"""
=========================================================================
Agent Note Model — Structured Agent Memory (Sprint 202, ADR-058 Pattern B ext.)
SDLC Orchestrator - Sprint 202 (Context Engineering Depth)

Version: 1.0.0
Date: 2026-04-21
Status: ACTIVE - Sprint 202
Authority: CTO Approved (Anthropic Best Practices Gap 1 — P1)
Reference: Anthropic "Building Effective AI Agents" Ch 8 (Context Engineering)

Purpose:
- Persistent key-value notes that survive context resets and session expiry
- Agents can save decisions, commitments, and context via save_note tool
- Notes injected into _build_llm_context() for cross-session memory
- UPSERT pattern: one value per key per agent (UNIQUE agent_id + key)
- Max 50 notes per agent (oldest auto-pruned by note_service)

Note Types:
- decision: Architecture/design decisions made during conversation
- commitment: Promises or action items the agent committed to
- context: Background information relevant to ongoing work
- preference: User or project preferences discovered during interaction

Design Decisions:
- agent_id FK to agent_definitions (NOT conversation-scoped by default)
- conversation_id nullable — global notes (NULL) or conversation-scoped
- UNIQUE(agent_id, key) enables upsert without duplicates
- VARCHAR(500) value limit prevents context overflow (50 notes × 500 chars max)

Zero Mock Policy: Production-ready SQLAlchemy 2.0 model.
=========================================================================
"""

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional
from uuid import UUID as PyUUID, uuid4

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base

if TYPE_CHECKING:
    from app.models.agent_definition import AgentDefinition
    from app.models.agent_conversation import AgentConversation


class AgentNote(Base):
    """Persistent structured note for cross-session agent memory.

    Enables agents to save key-value notes that survive context resets,
    session expiry, and history compaction. Notes are loaded into
    _build_llm_context() as the ## Agent Notes section.

    Attributes:
        id: UUID primary key.
        agent_id: FK to agent_definitions (UUID) — which agent owns this note.
        conversation_id: Optional FK (UUID) — NULL means global note.
        key: Note key (max 100 chars, unique per agent).
        value: Note value (max 500 chars to prevent context overflow).
        note_type: Classification — decision|commitment|context|preference.
        created_at: When the note was first created.
        updated_at: When the note was last updated (upsert timestamp).
    """

    __tablename__ = "agent_notes"
    __table_args__ = (
        UniqueConstraint("agent_id", "key", name="uq_agent_notes_agent_key"),
        Index("idx_agent_notes_agent_id", "agent_id"),
        Index("idx_agent_notes_conversation", "conversation_id"),
    )

    id: Mapped[uuid4] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4,
    )
    agent_id: Mapped[uuid4] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agent_definitions.id", ondelete="CASCADE"),
        nullable=False,
    )
    conversation_id: Mapped[Optional[uuid4]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agent_conversations.id", ondelete="SET NULL"),
        nullable=True,
    )
    key: Mapped[str] = mapped_column(String(100), nullable=False)
    value: Mapped[str] = mapped_column(String(500), nullable=False)
    note_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="context",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
