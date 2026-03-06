"""
=========================================================================
Delegation Link Model — Sprint 216 (P1 Context Injection)
SDLC Orchestrator — ADR-069, FR-051

Version: 1.0.0
Date: 2026-03-04
Status: ACTIVE
Authority: CTO Approved (ADR-069, CTO Verdict 8.5/10)
Reference: ADR-069-MTClaw-Best-Practice-Adoption.md
Pattern Source: MTClaw agent_links.go

Purpose:
- Explicit delegation authorization between agent definitions
- Source agent can delegate to target agent via spawn/delegate tool
- Spawn tool guard checks this table before creating child conversations
- Context injector reads this table to build DELEGATION.md section

Constraints:
- UNIQUE(source_agent_id, target_agent_id, link_type) — no duplicate links
- CHECK: source_agent_id != target_agent_id — no self-delegation
- FK CASCADE: delete agent_definition → auto-delete delegation links
- Soft deactivation via is_active (not hard delete) for audit trail

Zero Mock Policy: Production-ready SQLAlchemy 2.0 model
=========================================================================
"""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class DelegationLink(Base):
    """
    Delegation link — explicit authorization for agent-to-agent delegation.

    Each row authorizes a source agent to delegate work to a target agent.
    The spawn tool guard checks this table before any delegation attempt.
    The context injector reads active links to build DELEGATION.md sections.

    Fields:
        id: UUID primary key
        source_agent_id: Agent that can delegate (FK agent_definitions)
        target_agent_id: Agent that receives delegation (FK agent_definitions)
        link_type: Type of link (default: 'can_delegate')
        is_active: Soft toggle (false = deactivated, not deleted)
        metadata_: Extensible JSONB for future use
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    __tablename__ = "delegation_links"

    # Primary Key
    id: Mapped[uuid4] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        doc="Unique identifier for the delegation link",
    )

    # Foreign Keys
    source_agent_id: Mapped[uuid4] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agent_definitions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Agent that can delegate (source of delegation)",
    )

    target_agent_id: Mapped[uuid4] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agent_definitions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Agent that receives delegation (target of delegation)",
    )

    # Link Configuration
    link_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="can_delegate",
        doc="Type of link: can_delegate (default), can_review, can_escalate",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        doc="Active toggle — false = deactivated (soft delete for audit)",
    )

    metadata_: Mapped[dict] = mapped_column(
        "metadata",
        JSONB,
        nullable=False,
        default=dict,
        doc="Extensible metadata (future: priority, conditions)",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        doc="Link creation timestamp",
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        doc="Last update timestamp (used in context cache key)",
    )

    # Relationships
    source_agent = relationship(
        "AgentDefinition",
        foreign_keys=[source_agent_id],
        lazy="selectin",
    )

    target_agent = relationship(
        "AgentDefinition",
        foreign_keys=[target_agent_id],
        lazy="selectin",
    )

    # Table Constraints
    __table_args__ = (
        UniqueConstraint(
            "source_agent_id", "target_agent_id", "link_type",
            name="uq_delegation_link_source_target_type",
        ),
        CheckConstraint(
            "source_agent_id != target_agent_id",
            name="ck_delegation_link_no_self",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<DelegationLink(id={self.id}, "
            f"source={self.source_agent_id}, target={self.target_agent_id}, "
            f"type={self.link_type!r}, active={self.is_active})>"
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        return {
            "id": str(self.id),
            "source_agent_id": str(self.source_agent_id),
            "target_agent_id": str(self.target_agent_id),
            "link_type": self.link_type,
            "is_active": self.is_active,
            "metadata": self.metadata_ or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
