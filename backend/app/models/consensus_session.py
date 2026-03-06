"""ConsensusSession + ConsensusVote models — Sprint 221 (P2 Group Consensus).

Two tables for multi-agent group voting:
- consensus_sessions: voting session lifecycle (open -> voting -> decided/timeout/cancelled)
- consensus_votes: individual agent votes with DB-enforced double-vote prevention

INVARIANT: Consensus is advisory — CANNOT bypass EP-07 gates.
3 agents voting 'approve' on G3-gated task still needs human approval if G3 policy requires it.

References:
- ADR-070 (CoPaw/AgentScope Pattern Adoption), Sprint 221 Plan
- CTO F3: @vote command syntax documented before implementation
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base

# ── Constants ─────────────────────────────────────────────────────────────────

QUORUM_TYPES = ("majority", "unanimous", "threshold")
SESSION_STATUSES = ("open", "voting", "decided", "timeout", "cancelled")
VOTE_CHOICES = ("approve", "reject", "abstain")


class ConsensusSession(Base):
    """Voting session for multi-agent group consensus.

    Lifecycle: open -> voting (first vote) -> decided (quorum) | timeout | cancelled.
    Result stored in JSONB with decision, vote counts, and deciding vote reference.
    """

    __tablename__ = "consensus_sessions"

    id: Mapped[uuid4] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        doc="Unique identifier for the consensus session",
    )
    conversation_id: Mapped[uuid4] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agent_conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Conversation this session belongs to",
    )
    created_by: Mapped[uuid4] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agent_definitions.id", ondelete="CASCADE"),
        nullable=False,
        doc="Agent that initiated the vote",
    )
    topic: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        doc="Vote topic description",
    )
    quorum_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="majority",
        server_default="majority",
        doc="Quorum rule: majority|unanimous|threshold",
    )
    required_voters: Mapped[Any] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default=text("'[]'::jsonb"),
        doc="List of agent_definition IDs required to vote",
    )
    threshold_pct: Mapped[Optional[float]] = mapped_column(
        Numeric(3, 2),
        nullable=True,
        default=0.67,
        server_default="0.67",
        doc="Required percentage for threshold quorum type (0.00-1.00)",
    )
    timeout_seconds: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=300,
        server_default="300",
        doc="Seconds before session auto-times out",
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="open",
        server_default="open",
        doc="Session status: open|voting|decided|timeout|cancelled",
    )
    result: Mapped[Optional[Any]] = mapped_column(
        JSONB,
        nullable=True,
        default=None,
        doc="Quorum result: {decision, approve_count, reject_count, abstain_count}",
    )
    decided_by_vote_id: Mapped[Optional[uuid4]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        default=None,
        doc="Vote that triggered quorum (compare-and-swap guard)",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
        nullable=False,
    )
    closed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    # Relationships
    votes: Mapped[list["ConsensusVote"]] = relationship(
        "ConsensusVote",
        back_populates="session",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    conversation = relationship(
        "AgentConversation",
        foreign_keys=[conversation_id],
        lazy="selectin",
    )
    creator = relationship(
        "AgentDefinition",
        foreign_keys=[created_by],
        lazy="selectin",
    )

    __table_args__ = (
        CheckConstraint(
            "quorum_type IN ('majority', 'unanimous', 'threshold')",
            name="ck_consensus_sessions_quorum_type",
        ),
        CheckConstraint(
            "status IN ('open', 'voting', 'decided', 'timeout', 'cancelled')",
            name="ck_consensus_sessions_status",
        ),
    )

    def to_dict(self) -> dict:
        """Serialize to JSON-compatible dict."""
        return {
            "id": str(self.id),
            "conversation_id": str(self.conversation_id),
            "created_by": str(self.created_by),
            "topic": self.topic,
            "quorum_type": self.quorum_type,
            "required_voters": self.required_voters,
            "threshold_pct": float(self.threshold_pct) if self.threshold_pct else None,
            "timeout_seconds": self.timeout_seconds,
            "status": self.status,
            "result": self.result,
            "decided_by_vote_id": (
                str(self.decided_by_vote_id) if self.decided_by_vote_id else None
            ),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "closed_at": self.closed_at.isoformat() if self.closed_at else None,
        }

    def __repr__(self) -> str:
        return (
            f"<ConsensusSession(id={self.id}, topic={self.topic!r}, "
            f"status={self.status!r}, quorum={self.quorum_type!r})>"
        )


class ConsensusVote(Base):
    """Individual agent vote in a consensus session.

    DB-enforced uniqueness: UNIQUE(session_id, voter_agent_id) prevents double-vote.
    """

    __tablename__ = "consensus_votes"

    id: Mapped[uuid4] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        doc="Unique identifier for the vote",
    )
    session_id: Mapped[uuid4] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("consensus_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Consensus session this vote belongs to",
    )
    voter_agent_id: Mapped[uuid4] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agent_definitions.id", ondelete="CASCADE"),
        nullable=False,
        doc="Agent casting this vote",
    )
    vote: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        doc="Vote choice: approve|reject|abstain",
    )
    reasoning: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        default=None,
        doc="Agent's reasoning for their vote",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
        nullable=False,
    )

    # Relationships
    session: Mapped["ConsensusSession"] = relationship(
        "ConsensusSession",
        back_populates="votes",
        lazy="selectin",
    )
    voter = relationship(
        "AgentDefinition",
        foreign_keys=[voter_agent_id],
        lazy="selectin",
    )

    __table_args__ = (
        UniqueConstraint(
            "session_id",
            "voter_agent_id",
            name="uq_consensus_votes_session_voter",
        ),
        CheckConstraint(
            "vote IN ('approve', 'reject', 'abstain')",
            name="ck_consensus_votes_vote",
        ),
    )

    def to_dict(self) -> dict:
        """Serialize to JSON-compatible dict."""
        return {
            "id": str(self.id),
            "session_id": str(self.session_id),
            "voter_agent_id": str(self.voter_agent_id),
            "vote": self.vote,
            "reasoning": self.reasoning,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        return (
            f"<ConsensusVote(id={self.id}, session={self.session_id}, "
            f"voter={self.voter_agent_id}, vote={self.vote!r})>"
        )
