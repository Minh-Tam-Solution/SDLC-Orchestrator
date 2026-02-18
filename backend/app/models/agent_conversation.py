"""
=========================================================================
Agent Conversation Model - Multi-Agent Team Engine (ADR-056)
SDLC Orchestrator - Sprint 176 (Multi-Agent Foundation)

Version: 1.0.0
Date: 2026-02-18
Status: ACTIVE - Sprint 176
Authority: CTO Approved (ADR-056, EP-07)
Reference: ADR-056-Multi-Agent-Team-Engine.md

Purpose:
- Agent conversation lifecycle with snapshotted configuration
- Parent-child session inheritance (OpenClaw Pattern 5)
- Token budget tracking + circuit breaker (Non-Negotiable #13)
- Loop prevention (TinyClaw: 50-msg cap, branch counting)
- Delegation depth tracking (Nanobot N2)

4 Locked Decisions Applied:
  1. Snapshot Precedence — max_messages, max_budget_cents, queue_mode, session_scope
     snapshotted from definition on creation. Conversation copy is authoritative after.
  2. Lane Contract — conversations track token budget for circuit breaker
  3. Provider Profile Key — provider invocations tracked per conversation
  4. Canonical Protocol Owner — conversation schema owned by Orchestrator

14 Non-Negotiables:
  #9: Loop guards (max_messages=50 default)
  #11: Snapshot precedence enforced
  #13: Token budget circuit breaker (current_cost_cents vs max_budget_cents)
  #14: Human-in-the-loop interrupt (paused_by_human status)

Zero Mock Policy: Production-ready SQLAlchemy 2.0 model
=========================================================================
"""

from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import uuid4

from sqlalchemy import Integer, String, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.agent_definition import AgentDefinition
    from app.models.agent_message import AgentMessage


class AgentConversation(Base):
    """
    Agent conversation — a session between a user/agent/system and an AI agent.

    Snapshot Precedence (ADR-056 Decision 1):
    On creation, max_messages, max_budget_cents, queue_mode, and session_scope are
    copied from the agent_definition. After creation, the conversation copy is
    authoritative — changing the definition does NOT retroactively affect running
    conversations.

    Parent-child inheritance (OpenClaw Pattern 5):
    Subagent conversations link to parent via parent_conversation_id.
    delegation_depth tracks how deep in the chain this conversation is.
    """

    __tablename__ = "agent_conversations"

    # ── Primary Key ──────────────────────────────────────────────────────
    id: Mapped[uuid4] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        doc="Unique identifier for the conversation",
    )

    # ── Foreign Keys ─────────────────────────────────────────────────────
    project_id: Mapped[uuid4] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Project this conversation belongs to",
    )

    agent_definition_id: Mapped[uuid4] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agent_definitions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Agent definition that created this conversation",
    )

    parent_conversation_id: Mapped[Optional[uuid4]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agent_conversations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Parent conversation for subagent inheritance (OpenClaw Pattern 5)",
    )

    # ── Delegation Depth (Nanobot N2) ────────────────────────────────────
    delegation_depth: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        doc="Current depth in delegation chain. Root=0, first child=1, etc.",
    )

    # ── Initiator ────────────────────────────────────────────────────────
    initiator_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        doc="What started this conversation: user, agent, gate_event, ott_channel",
    )

    initiator_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="Identifier of the initiator (user UUID, agent ID, gate event ID)",
    )

    channel: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        doc="Communication channel: web, cli, extension, telegram, discord, etc.",
    )

    # ── Snapshotted Fields (ADR-056 Decision 1) ─────────────────────────
    session_scope: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        doc="Snapshotted from definition: per-sender, global",
    )

    queue_mode: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        doc="Snapshotted from definition: queue, steer, interrupt",
    )

    # ── Conversation Status ──────────────────────────────────────────────
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="active",
        doc="Lifecycle: active, completed, max_reached, paused_by_human, error",
    )

    # ── Loop Prevention (TinyClaw patterns) ──────────────────────────────
    total_messages: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        doc="Running message count (incremented per message)",
    )

    max_messages: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=50,
        doc="Snapshotted from definition. Max before auto-complete (Non-Negotiable #9)",
    )

    branch_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        doc="Number of conversation branches (TinyClaw pattern)",
    )

    # ── Token Budget (OpenClaw + Non-Negotiable #13) ─────────────────────
    input_tokens: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        doc="Cumulative input tokens consumed",
    )

    output_tokens: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        doc="Cumulative output tokens consumed",
    )

    total_tokens: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        doc="Cumulative total tokens (input + output)",
    )

    current_cost_cents: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        doc="Running cost in cents (for circuit breaker comparison)",
    )

    max_budget_cents: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1000,
        doc="Snapshotted from definition. Budget ceiling in cents ($10 default)",
    )

    # ── Metadata ─────────────────────────────────────────────────────────
    metadata_: Mapped[dict] = mapped_column(
        "metadata",
        JSONB,
        nullable=False,
        default=dict,
        doc="Extensible metadata (labels, tags, context)",
    )

    # ── Timestamps ───────────────────────────────────────────────────────
    started_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        doc="Conversation start timestamp",
    )

    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        doc="Conversation completion timestamp (NULL while active)",
    )

    # ── Relationships ────────────────────────────────────────────────────
    project: Mapped["Project"] = relationship(
        "Project",
        lazy="selectin",
    )

    agent_definition: Mapped["AgentDefinition"] = relationship(
        "AgentDefinition",
        back_populates="conversations",
        lazy="selectin",
    )

    parent_conversation: Mapped[Optional["AgentConversation"]] = relationship(
        "AgentConversation",
        remote_side="AgentConversation.id",
        lazy="selectin",
    )

    messages: Mapped[list["AgentMessage"]] = relationship(
        "AgentMessage",
        back_populates="conversation",
        lazy="selectin",
        order_by="AgentMessage.created_at",
    )

    def __repr__(self) -> str:
        return (
            f"<AgentConversation(id={self.id}, status={self.status!r}, "
            f"messages={self.total_messages}/{self.max_messages})>"
        )
