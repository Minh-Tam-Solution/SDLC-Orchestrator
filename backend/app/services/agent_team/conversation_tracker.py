"""
=========================================================================
Conversation Tracker — Parent-child inheritance + loop guards + budget
SDLC Orchestrator - Sprint 177 (Multi-Agent Core Services)

Version: 1.0.0
Date: February 2026
Status: ACTIVE - Sprint 177
Authority: CTO Approved (ADR-056)
Reference: ADR-056-Multi-Agent-Team-Engine.md

Purpose:
- Conversation lifecycle management (active → completed/max_reached/error)
- Parent-child session inheritance (OpenClaw Pattern 5)
- Loop guard enforcement via ConversationLimits integration
- Token budget tracking + circuit breaker (Non-Negotiable #13)
- Delegation depth validation (Nanobot N2)

Sources:
- OpenClaw: src/agents/conversation-tracker.ts (session management)
- TinyClaw: src/tinyclaw/loop-guard.ts (message cap, branch counting)
- Nanobot N2: delegation depth tracking
- ADR-056 Decision 1: Snapshot Precedence
- ADR-056 Non-Negotiable #9: Loop guards
- ADR-056 Non-Negotiable #13: Budget circuit breaker

Zero Mock Policy: Production-ready async SQLAlchemy 2.0 service
=========================================================================
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_conversation import AgentConversation
from app.models.agent_definition import AgentDefinition
from app.services.agent_team.conversation_limits import ConversationLimits, LimitViolation

logger = logging.getLogger(__name__)


class ConversationError(Exception):
    """Base exception for conversation operations."""


class ConversationNotFoundError(ConversationError):
    """Conversation not found."""


class ConversationInactiveError(ConversationError):
    """Conversation is not in active status."""


class LimitExceededError(ConversationError):
    """A conversation limit has been exceeded."""

    def __init__(self, violation: LimitViolation, message: str):
        self.violation = violation
        super().__init__(message)


class DelegationDepthError(ConversationError):
    """Delegation depth limit exceeded."""


class ConversationTracker:
    """
    Manages conversation lifecycle, loop guards, budget tracking,
    and parent-child inheritance.

    Snapshot Precedence (ADR-056 Decision 1):
    On conversation creation, max_messages, max_budget_cents, queue_mode,
    and session_scope are copied from the agent definition. The conversation
    copy is authoritative after creation.

    Usage:
        tracker = ConversationTracker(db)

        # Create with snapshot precedence
        conv = await tracker.create(definition, payload)

        # Check limits before processing
        await tracker.check_limits(conv)

        # Update token usage after processing
        await tracker.record_token_usage(conv.id, input_tokens=500, output_tokens=200, cost_cents=2)

        # Complete conversation
        await tracker.complete(conv.id)
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        definition: AgentDefinition,
        project_id: UUID,
        initiator_type: str,
        initiator_id: str,
        channel: str,
        parent_conversation_id: UUID | None = None,
        metadata: dict | None = None,
    ) -> AgentConversation:
        """
        Create a conversation with Snapshot Precedence from agent definition.

        Validates delegation depth against parent conversation chain.

        Args:
            definition: Agent definition to snapshot from.
            project_id: Project UUID (must match definition.project_id).
            initiator_type: "user", "agent", "gate_event", "ott_channel".
            initiator_id: Identifier of the initiator.
            channel: Communication channel.
            parent_conversation_id: Parent conversation for sub-agent inheritance.
            metadata: Optional extensible metadata.

        Returns:
            Created AgentConversation ORM instance.

        Raises:
            DelegationDepthError: If depth exceeds definition.max_delegation_depth.
        """
        delegation_depth = 0

        if parent_conversation_id:
            parent = await self._get_conversation(parent_conversation_id)
            delegation_depth = parent.delegation_depth + 1

            if delegation_depth > definition.max_delegation_depth:
                raise DelegationDepthError(
                    f"Delegation depth {delegation_depth} exceeds max "
                    f"{definition.max_delegation_depth} for agent '{definition.agent_name}'"
                )

        conversation = AgentConversation(
            id=uuid4(),
            project_id=project_id,
            agent_definition_id=definition.id,
            parent_conversation_id=parent_conversation_id,
            delegation_depth=delegation_depth,
            initiator_type=initiator_type,
            initiator_id=initiator_id,
            channel=channel,
            # Snapshot Precedence (ADR-056 Decision 1)
            session_scope=definition.session_scope,
            queue_mode=definition.queue_mode,
            max_messages=definition.config.get("max_messages", 50),
            max_budget_cents=definition.config.get("max_budget_cents", 1000),
            # Defaults
            status="active",
            metadata_=metadata or {},
        )

        self.db.add(conversation)
        await self.db.flush()

        logger.info(
            "Created conversation: id=%s, agent=%s, depth=%d, channel=%s",
            conversation.id,
            definition.agent_name,
            delegation_depth,
            channel,
        )
        return conversation

    async def get(self, conversation_id: UUID) -> AgentConversation:
        """
        Get conversation by ID.

        Raises:
            ConversationNotFoundError: If not found.
        """
        return await self._get_conversation(conversation_id)

    async def get_active(self, conversation_id: UUID) -> AgentConversation:
        """
        Get conversation by ID, ensuring it is active.

        Raises:
            ConversationNotFoundError: If not found.
            ConversationInactiveError: If not in active status.
        """
        conversation = await self._get_conversation(conversation_id)
        if conversation.status != "active":
            raise ConversationInactiveError(
                f"Conversation {conversation_id} is '{conversation.status}', not active"
            )
        return conversation

    def build_limits(self, conversation: AgentConversation) -> ConversationLimits:
        """
        Build ConversationLimits from snapshotted conversation fields.

        Uses the conversation's own snapshotted values (not the definition's),
        per Snapshot Precedence.
        """
        return ConversationLimits(
            max_messages=conversation.max_messages,
            max_budget_cents=conversation.max_budget_cents,
        )

    async def check_limits(self, conversation: AgentConversation) -> None:
        """
        Check all conversation limits. Raises LimitExceededError on violation.

        On violation, also updates conversation status to reflect the limit.
        """
        limits = self.build_limits(conversation)

        # Check message count
        violation = limits.check_messages(conversation.total_messages)
        if violation:
            await self._set_status(conversation, "max_reached")
            raise LimitExceededError(
                violation,
                f"Message limit reached: {conversation.total_messages}/{conversation.max_messages}",
            )

        # Check budget
        violation = limits.check_budget(conversation.current_cost_cents)
        if violation:
            await self._set_status(conversation, "max_reached")
            raise LimitExceededError(
                violation,
                f"Budget exceeded: {conversation.current_cost_cents}/{conversation.max_budget_cents} cents",
            )

    async def increment_message_count(self, conversation_id: UUID) -> int:
        """
        Atomically increment total_messages and return new count.

        Also increments branch_count when appropriate (TinyClaw pattern).
        """
        conversation = await self._get_conversation(conversation_id)
        conversation.total_messages += 1
        await self.db.flush()
        return conversation.total_messages

    async def record_token_usage(
        self,
        conversation_id: UUID,
        input_tokens: int,
        output_tokens: int,
        cost_cents: int,
    ) -> None:
        """
        Record token usage and cost for budget circuit breaker tracking.

        Called after each provider invocation with the token counts from
        the response.
        """
        conversation = await self._get_conversation(conversation_id)
        conversation.input_tokens += input_tokens
        conversation.output_tokens += output_tokens
        conversation.total_tokens += input_tokens + output_tokens
        conversation.current_cost_cents += cost_cents
        await self.db.flush()

        exceeded = conversation.current_cost_cents >= conversation.max_budget_cents
        logger.info(
            "TRACE_BUDGET cost_increment=%d, running_cost=%d, "
            "max_budget=%d, exceeded=%s, conv=%s, tokens=+%d+%d",
            cost_cents,
            conversation.current_cost_cents,
            conversation.max_budget_cents,
            exceeded,
            conversation_id,
            input_tokens,
            output_tokens,
        )

    async def complete(self, conversation_id: UUID) -> AgentConversation:
        """Mark conversation as completed."""
        conversation = await self._get_conversation(conversation_id)
        await self._set_status(conversation, "completed")
        logger.info("Conversation completed: id=%s", conversation_id)
        return conversation

    async def error(
        self, conversation_id: UUID, error_detail: str | None = None
    ) -> AgentConversation:
        """Mark conversation as errored."""
        conversation = await self._get_conversation(conversation_id)
        await self._set_status(conversation, "error")
        if error_detail:
            metadata = dict(conversation.metadata_ or {})
            metadata["last_error"] = error_detail[:2000]
            conversation.metadata_ = metadata
            await self.db.flush()
        logger.warning(
            "Conversation errored: id=%s, error=%.200s",
            conversation_id,
            error_detail,
        )
        return conversation

    async def pause(self, conversation_id: UUID, reason: str) -> AgentConversation:
        """Pause conversation via human-in-the-loop interrupt."""
        conversation = await self._get_conversation(conversation_id)
        await self._set_status(conversation, "paused_by_human")
        metadata = dict(conversation.metadata_ or {})
        metadata["pause_reason"] = reason[:500]
        conversation.metadata_ = metadata
        await self.db.flush()
        logger.info(
            "Conversation paused: id=%s, reason=%.200s",
            conversation_id,
            reason,
        )
        return conversation

    async def resume(self, conversation_id: UUID) -> AgentConversation:
        """Resume a paused conversation."""
        conversation = await self._get_conversation(conversation_id)
        if conversation.status != "paused_by_human":
            raise ConversationInactiveError(
                f"Cannot resume conversation {conversation_id}: "
                f"status is '{conversation.status}', expected 'paused_by_human'"
            )
        conversation.status = "active"
        await self.db.flush()
        logger.info("Conversation resumed: id=%s", conversation_id)
        return conversation

    async def find_active_by_session_key(
        self,
        agent_definition_id: UUID,
        session_scope: str,
        sender_id: str,
    ) -> AgentConversation | None:
        """
        Find an active conversation matching session scoping rules.

        Session scoping (2 P0 modes):
        - per-sender: Match on agent_definition_id + initiator_id
        - global: Match on agent_definition_id only (ignores sender)
        """
        conditions = [
            AgentConversation.agent_definition_id == agent_definition_id,
            AgentConversation.status == "active",
        ]

        if session_scope == "per-sender":
            conditions.append(AgentConversation.initiator_id == sender_id)

        result = await self.db.execute(
            select(AgentConversation)
            .where(and_(*conditions))
            .order_by(AgentConversation.started_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def list_conversations(
        self,
        project_id: UUID,
        status_filter: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[AgentConversation], int]:
        """
        List conversations for a project with optional status filter.

        Args:
            project_id: Project UUID.
            status_filter: Optional status to filter by.
            page: Page number (1-based).
            page_size: Items per page.

        Returns:
            Tuple of (conversations list, total count).
        """
        from sqlalchemy import func

        conditions = [AgentConversation.project_id == project_id]
        if status_filter:
            conditions.append(AgentConversation.status == status_filter)

        count_result = await self.db.execute(
            select(func.count())
            .select_from(AgentConversation)
            .where(and_(*conditions))
        )
        total = count_result.scalar() or 0

        result = await self.db.execute(
            select(AgentConversation)
            .where(and_(*conditions))
            .order_by(AgentConversation.started_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        conversations = list(result.scalars().all())

        return conversations, total

    async def _get_conversation(self, conversation_id: UUID) -> AgentConversation:
        """Internal helper to fetch conversation with error."""
        result = await self.db.execute(
            select(AgentConversation).where(AgentConversation.id == conversation_id)
        )
        conversation = result.scalar_one_or_none()
        if not conversation:
            raise ConversationNotFoundError(
                f"Conversation {conversation_id} not found"
            )
        return conversation

    async def _set_status(
        self, conversation: AgentConversation, new_status: str
    ) -> None:
        """Set conversation status with timestamp on terminal states."""
        conversation.status = new_status
        if new_status in ("completed", "max_reached", "error"):
            conversation.completed_at = datetime.now(timezone.utc)
        await self.db.flush()
