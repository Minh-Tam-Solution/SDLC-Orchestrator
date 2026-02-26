"""
=========================================================================
WorkflowMetadata + WorkflowService — Durable Workflow State in JSONB
SDLC Orchestrator - Sprint 206 (LangGraph Durable Workflows)

Version: 1.0.0
Date: February 2026
Status: ACTIVE - Sprint 206
Authority: CTO Approved (ADR-066)
Reference: ADR-066-LangChain-Multi-Agent-Orchestration.md

Purpose:
- WorkflowMetadata: Pydantic v2 model for workflow checkpoint state.
  Stored in agent_conversations.metadata_["workflow"] JSONB column.
- WorkflowService: Read/write WorkflowMetadata with OCC (Optimistic
  Concurrency Control) — version field compare-and-swap on every save.

ADR-066 Locked Decisions Applied:
  D-066-02: Workflow state in agent_conversations.metadata_ JSONB.
    - WorkflowMetadata schema with version field for OCC.
    - 64KB max size validation before every write.
    - Partial index: (status, next_wakeup_at) WHERE workflow_id IS NOT NULL
  D-066-06: Idempotency keys in WorkflowMetadata.idempotency_keys dict.

OCC Pattern:
  caller loads metadata (reads version=N)
  caller updates fields
  caller calls save(expected_version=N)
  → DB has version=N → save succeeds, DB version becomes N+1
  → DB has version!=N → save fails (False) — concurrent update detected

Zero Mock Policy: Production-ready Pydantic v2 + async SQLAlchemy 2.0
=========================================================================
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Literal, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_conversation import AgentConversation

logger = logging.getLogger(__name__)

# JSONB key for workflow metadata within agent_conversations.metadata_
_WORKFLOW_KEY = "workflow"

# 64KB max for JSONB workflow state (D-066-02)
_MAX_JSONB_BYTES = 65_536


# ── Exceptions ───────────────────────────────────────────────────────────────


class WorkflowConcurrencyError(Exception):
    """OCC version mismatch: another process updated the workflow state."""


class WorkflowNotFoundError(Exception):
    """No workflow metadata found in conversation, or conversation not found."""


# ── WorkflowMetadata (D-066-02 schema) ────────────────────────────────────────


class WorkflowMetadata(BaseModel):
    """
    Durable checkpoint for a LangGraph workflow stored in agent_conversations.metadata_.

    OCC: version is incremented on every successful save. Before saving,
    the caller must provide the version they read (expected_version).
    If the DB version != expected_version, the save is rejected.

    Attributes:
        workflow_schema_version: Schema version for forward compatibility.
        workflow_id: Unique identifier for this workflow run.
        workflow_type: Type of workflow — currently only "reflection".
        status: Current lifecycle state.
        current_node: Next node WorkflowResumer should execute on resume.
        iteration: How many Coder→Reviewer cycles have completed.
        next_wakeup_at: When reconciler should retry (None = ASAP on pub/sub).
        idempotency_keys: {step_id: node_name} for D-066-06 step deduplication.
        version: OCC version, incremented atomically on every write.
        state: Arbitrary workflow-specific payload (store pointers, not blobs).
    """

    workflow_schema_version: str = "1.0.0"
    workflow_id: UUID = Field(default_factory=uuid4)
    workflow_type: Literal["reflection"] = "reflection"
    status: Literal["waiting", "running", "completed", "failed"] = "running"
    current_node: str
    iteration: int = 0
    next_wakeup_at: Optional[datetime] = None
    idempotency_keys: dict[str, str] = Field(default_factory=dict)
    version: int = 0  # OCC: starts at 0, caller expected_version=0 on first save
    state: dict[str, Any] = Field(default_factory=dict)

    @field_validator("iteration")
    @classmethod
    def iteration_non_negative(cls, v: int) -> int:
        if v < 0:
            raise ValueError("iteration must be >= 0")
        return v

    @field_validator("version")
    @classmethod
    def version_non_negative(cls, v: int) -> int:
        if v < 0:
            raise ValueError("version must be >= 0")
        return v

    def serialized_size(self) -> int:
        """Return UTF-8 byte size of JSON serialization (64KB limit check)."""
        return len(json.dumps(self.model_dump(mode="json")).encode("utf-8"))

    def is_terminal(self) -> bool:
        """Return True if this workflow has reached a terminal state."""
        return self.status in ("completed", "failed")

    def is_step_done(self, step_id: str) -> bool:
        """Return True if step_id is already in idempotency_keys (D-066-06)."""
        return step_id in self.idempotency_keys

    model_config = {"json_encoders": {UUID: str, datetime: lambda v: v.isoformat()}}


# ── WorkflowService ───────────────────────────────────────────────────────────


class WorkflowService:
    """
    Read/write WorkflowMetadata from agent_conversations.metadata_ JSONB.

    Uses Optimistic Concurrency Control (OCC): callers read the current
    version, modify fields, then call save(expected_version=<read version>).
    If the DB version has changed since the read, save() returns False.

    Usage:
        svc = WorkflowService(db)

        # Start a new workflow
        meta = await svc.start_workflow(conv_id, initial_node="enqueue_coder",
                                         initial_state={"task": "...", "max_iterations": 3})

        # Load checkpoint
        meta = await svc.load(conv_id)

        # Transition to next node
        meta = await svc.transition(conv_id, next_node="score_output", new_status="running",
                                     state_updates={"coder_output": "..."})
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def load(self, conversation_id: UUID) -> Optional[WorkflowMetadata]:
        """
        Load WorkflowMetadata from conversation metadata_.

        Returns None if conversation has no workflow or conversation not found.
        Logs a warning on parse failure (does not raise).
        """
        result = await self.db.execute(
            select(AgentConversation).where(AgentConversation.id == conversation_id)
        )
        conversation = result.scalar_one_or_none()
        if not conversation:
            return None

        wf_raw = (conversation.metadata_ or {}).get(_WORKFLOW_KEY)
        if not wf_raw:
            return None

        try:
            return WorkflowMetadata.model_validate(wf_raw)
        except Exception as exc:
            logger.warning(
                "WorkflowService.load: parse error conv=%s: %s", conversation_id, exc
            )
            return None

    async def save(
        self,
        conversation_id: UUID,
        workflow_meta: WorkflowMetadata,
        expected_version: int,
    ) -> bool:
        """
        Persist WorkflowMetadata with OCC version check.

        Increments workflow_meta.version before writing. If the DB has a
        different version than expected_version, does NOT write and returns False.

        Args:
            conversation_id: Target conversation UUID.
            workflow_meta: Updated WorkflowMetadata to persist.
            expected_version: Version the caller observed before this call.

        Returns:
            True if saved, False if OCC conflict (another write occurred).

        Raises:
            WorkflowConcurrencyError: If conversation not found.
        """
        result = await self.db.execute(
            select(AgentConversation).where(AgentConversation.id == conversation_id)
        )
        conversation = result.scalar_one_or_none()
        if not conversation:
            raise WorkflowConcurrencyError(
                f"Conversation {conversation_id} not found — cannot save workflow state"
            )

        metadata = dict(conversation.metadata_ or {})
        existing = metadata.get(_WORKFLOW_KEY, {})
        current_version = existing.get("version", -1) if isinstance(existing, dict) else -1

        # First-time save: expected_version=0 and no existing entry
        if expected_version == 0 and not existing:
            current_version = 0  # treat as matching

        if current_version != expected_version:
            logger.warning(
                "WorkflowService OCC conflict: conv=%s expected_v=%d db_v=%d",
                conversation_id,
                expected_version,
                current_version,
            )
            return False

        # Increment version for next writer
        updated = workflow_meta.model_copy(update={"version": expected_version + 1})

        # Validate 64KB limit (D-066-02)
        size = updated.serialized_size()
        if size > _MAX_JSONB_BYTES:
            logger.error(
                "WorkflowService: JSONB size %d exceeds 64KB limit for conv=%s — "
                "store pointers not payloads in state dict",
                size,
                conversation_id,
            )
            raise WorkflowConcurrencyError(
                f"Workflow state too large ({size}B > {_MAX_JSONB_BYTES}B limit). "
                "Store message_id / evidence_id pointers, not full payloads."
            )

        metadata[_WORKFLOW_KEY] = updated.model_dump(mode="json")
        conversation.metadata_ = metadata
        await self.db.flush()

        logger.debug(
            "WorkflowService.save: conv=%s node=%s status=%s v=%d→%d",
            conversation_id,
            updated.current_node,
            updated.status,
            expected_version,
            updated.version,
        )
        return True

    async def start_workflow(
        self,
        conversation_id: UUID,
        initial_node: str,
        initial_state: dict[str, Any] | None = None,
    ) -> WorkflowMetadata:
        """
        Create and persist a new workflow. Raises if workflow already exists.

        Args:
            conversation_id: Target conversation UUID.
            initial_node: First node to execute (e.g. "enqueue_coder").
            initial_state: Initial state dict — use pointers not payloads.

        Returns:
            Created WorkflowMetadata (version=1 after save).

        Raises:
            WorkflowConcurrencyError: If workflow already exists or conversation missing.
        """
        # Check for existing workflow
        existing = await self.load(conversation_id)
        if existing is not None:
            raise WorkflowConcurrencyError(
                f"Workflow already exists for conv={conversation_id} "
                f"(status={existing.status}). Use resume() instead."
            )

        meta = WorkflowMetadata(
            current_node=initial_node,
            status="running",
            state=initial_state or {},
        )

        saved = await self.save(conversation_id, meta, expected_version=0)
        if not saved:
            raise WorkflowConcurrencyError(
                f"start_workflow OCC conflict on conv={conversation_id}"
            )

        # Return the version-1 copy
        return meta.model_copy(update={"version": 1})

    async def transition(
        self,
        conversation_id: UUID,
        next_node: str,
        new_status: Literal["waiting", "running", "completed", "failed"],
        state_updates: dict[str, Any] | None = None,
        idempotency_key: str | None = None,
        next_wakeup_at: Optional[datetime] = None,
        increment_iteration: bool = False,
    ) -> WorkflowMetadata:
        """
        Atomically transition workflow to next_node with OCC retry.

        Retries up to 3 times on OCC conflict (each conflict means another
        process updated the state — reload and re-apply transition).

        Args:
            conversation_id: Target conversation UUID.
            next_node: Node name after transition.
            new_status: New workflow status.
            state_updates: Dict merged into WorkflowMetadata.state.
            idempotency_key: If provided, added to idempotency_keys.
            next_wakeup_at: Scheduled wakeup time for reconciler.
            increment_iteration: If True, iteration += 1.

        Returns:
            Updated WorkflowMetadata (after successful save).

        Raises:
            WorkflowNotFoundError: If conversation/workflow not found.
            WorkflowConcurrencyError: If all 3 OCC retries fail.
        """
        last_exc: Optional[Exception] = None

        for attempt in range(3):
            meta = await self.load(conversation_id)
            if meta is None:
                raise WorkflowNotFoundError(
                    f"No workflow metadata for conv={conversation_id}"
                )

            new_idempotency_keys = dict(meta.idempotency_keys)
            if idempotency_key:
                new_idempotency_keys[idempotency_key] = next_node

            new_state = dict(meta.state)
            if state_updates:
                new_state.update(state_updates)

            updated = meta.model_copy(
                update={
                    "current_node": next_node,
                    "status": new_status,
                    "next_wakeup_at": next_wakeup_at,
                    "idempotency_keys": new_idempotency_keys,
                    "state": new_state,
                    "iteration": meta.iteration + (1 if increment_iteration else 0),
                }
            )

            if await self.save(conversation_id, updated, expected_version=meta.version):
                return updated.model_copy(update={"version": meta.version + 1})

            logger.debug(
                "WorkflowService.transition OCC retry: attempt=%d conv=%s",
                attempt + 1,
                conversation_id,
            )
            last_exc = WorkflowConcurrencyError(
                f"OCC retry {attempt + 1}/3 failed for conv={conversation_id}"
            )

        raise WorkflowConcurrencyError(
            f"WorkflowService.transition failed after 3 retries: conv={conversation_id}"
        ) from last_exc
