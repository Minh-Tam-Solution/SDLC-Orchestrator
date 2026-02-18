"""
=========================================================================
Agent Message Model - Multi-Agent Team Engine (ADR-056)
SDLC Orchestrator - Sprint 176 (Multi-Agent Foundation)

Version: 1.0.0
Date: 2026-02-18
Status: ACTIVE - Sprint 176
Authority: CTO Approved (ADR-056, EP-07)
Reference: ADR-056-Multi-Agent-Team-Engine.md

Purpose:
- Message storage with lane-based concurrency (ADR-056 Decision 2)
- Dead-letter queue with exponential backoff (30s, 60s, 120s)
- Idempotency via dedupe_key (INSERT ON CONFLICT DO NOTHING)
- Failover reason tracking (6 classified errors)
- Provider invocation tracing (correlation_id, latency_ms)

4 Locked Decisions Applied:
  2. Lane Contract — processing_lane, processing_status, SKIP LOCKED, dead-letter
  3. Provider Profile Key — provider_used + failover_reason per message
  4. Canonical Protocol Owner — message schema owned by Orchestrator

14 Non-Negotiables:
  #7: Lane-based queue (processing_lane for per-agent serialization)
  #10: Dead-letter queue (failed_count >= 3 → dead_letter status)
  #12: Identity masquerading audit (correlation_id for request tracing)

Zero Mock Policy: Production-ready SQLAlchemy 2.0 model
=========================================================================
"""

from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import uuid4

from sqlalchemy import Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from app.models.agent_conversation import AgentConversation
    from app.models.gate_evidence import GateEvidence


class AgentMessage(Base):
    """
    Agent message — individual message within a Multi-Agent conversation.

    Lane Contract (ADR-056 Decision 2):
    - processing_lane determines which queue lane processes this message
    - processing_status tracks the message through pending → processing → completed/failed
    - Dead-letter: failed_count >= 3 → processing_status = 'dead_letter'
    - Exponential backoff: next_retry_at = NOW() + (30 * 2^failed_count) seconds

    Idempotency:
    - dedupe_key with UNIQUE constraint prevents duplicate message processing
    - INSERT ... ON CONFLICT (dedupe_key) DO NOTHING

    Provider Tracing:
    - correlation_id links all events in a message lifecycle
    - provider_used, failover_reason, latency_ms track provider invocation
    """

    __tablename__ = "agent_messages"

    # ── Primary Key ──────────────────────────────────────────────────────
    id: Mapped[uuid4] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        doc="Unique identifier for the message",
    )

    # ── Foreign Keys ─────────────────────────────────────────────────────
    conversation_id: Mapped[uuid4] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agent_conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Conversation this message belongs to",
    )

    parent_message_id: Mapped[Optional[uuid4]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agent_messages.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Parent message for threading support",
    )

    evidence_id: Mapped[Optional[uuid4]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("gate_evidence.id", ondelete="SET NULL"),
        nullable=True,
        doc="Linked evidence artifact (if message produced evidence)",
    )

    # ── Sender / Recipient ───────────────────────────────────────────────
    sender_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        doc="Who sent: user, agent, system",
    )

    sender_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="Sender identifier (user UUID, agent name, 'system')",
    )

    recipient_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        doc="Recipient identifier (agent name, user UUID). NULL = broadcast.",
    )

    # ── Content ──────────────────────────────────────────────────────────
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Message content (text, markdown, structured data)",
    )

    mentions: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        doc='Parsed @agent mentions: ["coder", "reviewer"]',
    )

    message_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        doc="Type: request, response, mention, system, interrupt",
    )

    # ── Queue / Lane (ADR-056 Decision 2) ────────────────────────────────
    queue_mode: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="queue",
        doc="How this message was queued: queue, steer, interrupt",
    )

    processing_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        index=True,
        doc="Lane state: pending, processing, completed, failed, dead_letter",
    )

    processing_lane: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="main",
        index=True,
        doc="Lane name for concurrency control (e.g., 'agent:coder', 'cron:cleanup')",
    )

    # ── Idempotency ──────────────────────────────────────────────────────
    dedupe_key: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        unique=True,
        doc="Idempotency key. INSERT ON CONFLICT DO NOTHING.",
    )

    # ── Tracing (Non-Negotiable #12) ─────────────────────────────────────
    correlation_id: Mapped[uuid4] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        default=uuid4,
        index=True,
        doc="Request tracing ID linking all events in message lifecycle",
    )

    # ── Provider Metrics ─────────────────────────────────────────────────
    token_count: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        doc="Tokens consumed by this message (input + output)",
    )

    latency_ms: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        doc="Provider response latency in milliseconds",
    )

    provider_used: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        doc="Which provider handled this message (ollama, anthropic, openai)",
    )

    failover_reason: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        doc="If failover occurred: auth, format, rate_limit, billing, timeout, unknown",
    )

    # ── Dead-Letter Queue (Non-Negotiable #10) ───────────────────────────
    failed_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        doc="Poison message tracking. >= 3 → dead_letter status.",
    )

    last_error: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Last error message (for dead-letter inspection)",
    )

    next_retry_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        doc="Exponential backoff: NOW() + (30 * 2^failed_count) seconds",
    )

    # ── Timestamp ────────────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        doc="Message creation timestamp",
    )

    # ── Relationships ────────────────────────────────────────────────────
    conversation: Mapped["AgentConversation"] = relationship(
        "AgentConversation",
        back_populates="messages",
        lazy="selectin",
    )

    parent_message: Mapped[Optional["AgentMessage"]] = relationship(
        "AgentMessage",
        remote_side="AgentMessage.id",
        lazy="selectin",
    )

    evidence: Mapped[Optional["GateEvidence"]] = relationship(
        "GateEvidence",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return (
            f"<AgentMessage(id={self.id}, type={self.message_type!r}, "
            f"status={self.processing_status!r}, lane={self.processing_lane!r})>"
        )
