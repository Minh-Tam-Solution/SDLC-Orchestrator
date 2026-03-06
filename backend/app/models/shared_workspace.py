"""
=========================================================================
Shared Workspace Item Model — Sprint 219 (P5 Shared Workspace Foundation)
SDLC Orchestrator — ADR-069/ADR-072

Version: 1.0.0
Date: 2026-03-04
Status: ACTIVE — Sprint 219
Authority: CTO Approved (PDR-001, ADR-072)
Reference: CoPaw ReMe pattern (shared memory)

Purpose:
- Conversation-scoped shared workspace for cross-agent collaboration
- Optimistic concurrency via version column (UPDATE WHERE version=expected)
- Soft delete via version=-1 (preserves audit trail)
- 6 item types: text, code, diff, json, markdown, binary_ref
- 3 conflict resolution strategies: last_write_wins, retry_3x, escalate_to_lead

Scoping: workspace dies with conversation (short-lived team tasks).
Parent-child isolation: children READ parent workspace, WRITE only to own.

Zero Mock Policy: Production-ready SQLAlchemy 2.0 model
=========================================================================
"""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


# Valid item types
WORKSPACE_ITEM_TYPES = ("text", "code", "diff", "json", "markdown", "binary_ref")

# Valid conflict resolution strategies
CONFLICT_STRATEGIES = ("last_write_wins", "retry_3x", "escalate_to_lead")


class SharedWorkspaceItem(Base):
    """
    Shared workspace item — conversation-scoped key-value store
    for cross-agent collaboration.

    Each item has a key (unique per conversation), content, version,
    and conflict resolution strategy. Soft delete sets version=-1.

    Port of CoPaw ReMe shared memory pattern.
    """

    __tablename__ = "shared_workspace_items"

    # ── Primary Key ──────────────────────────────────────────────────────
    id: Mapped[uuid4] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        doc="Unique identifier for the workspace item",
    )

    # ── Foreign Keys ─────────────────────────────────────────────────────
    conversation_id: Mapped[uuid4] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agent_conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Conversation this workspace item belongs to",
    )

    created_by: Mapped[Optional[uuid4]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agent_definitions.id", ondelete="SET NULL"),
        nullable=True,
        doc="Agent that created this item",
    )

    updated_by: Mapped[Optional[uuid4]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agent_definitions.id", ondelete="SET NULL"),
        nullable=True,
        doc="Agent that last updated this item",
    )

    # ── Key / Value ──────────────────────────────────────────────────────
    item_key: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        doc="Workspace key (e.g., 'coder/main.py', 'reviewer/feedback')",
    )

    item_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="text",
        doc="Content type: text|code|diff|json|markdown|binary_ref",
    )

    content: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Item content (text/code/json/markdown) or S3 key for binary_ref",
    )

    # ── Versioning (Optimistic Concurrency) ──────────────────────────────
    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        doc="Version counter. Incremented on update. -1 = soft deleted.",
    )

    # ── Conflict Resolution ──────────────────────────────────────────────
    conflict_resolution: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="last_write_wins",
        doc="Strategy: last_write_wins|retry_3x|escalate_to_lead",
    )

    # ── Timestamps ───────────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
        nullable=False,
        doc="Creation timestamp",
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
        nullable=False,
        doc="Last update timestamp",
    )

    # ── Relationships ────────────────────────────────────────────────────
    conversation = relationship(
        "AgentConversation",
        foreign_keys=[conversation_id],
        lazy="selectin",
    )

    # ── Constraints ──────────────────────────────────────────────────────
    __table_args__ = (
        CheckConstraint(
            "item_type IN ('text', 'code', 'diff', 'json', 'markdown', 'binary_ref')",
            name="ck_workspace_item_type",
        ),
        CheckConstraint(
            "conflict_resolution IN ('last_write_wins', 'retry_3x', 'escalate_to_lead')",
            name="ck_workspace_conflict_resolution",
        ),
    )

    def to_dict(self) -> dict:
        """Serialize to JSON-compatible dict."""
        return {
            "id": str(self.id),
            "conversation_id": str(self.conversation_id),
            "created_by": str(self.created_by) if self.created_by else None,
            "updated_by": str(self.updated_by) if self.updated_by else None,
            "item_key": self.item_key,
            "item_type": self.item_type,
            "content": self.content,
            "version": self.version,
            "conflict_resolution": self.conflict_resolution,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return (
            f"<SharedWorkspaceItem(id={self.id}, key={self.item_key!r}, "
            f"version={self.version}, type={self.item_type!r})>"
        )
