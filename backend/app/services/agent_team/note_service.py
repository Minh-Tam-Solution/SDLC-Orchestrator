"""
=========================================================================
Note Service — Agent Structured Memory CRUD (Sprint 202)
SDLC Orchestrator - Sprint 202 (Context Engineering Depth)

Version: 1.0.0
Date: 2026-04-21
Status: ACTIVE - Sprint 202
Authority: CTO Approved (Anthropic Best Practices Gap 1 — P1)
Reference: Anthropic "Building Effective AI Agents" Ch 8 (Context Engineering)

Purpose:
- CRUD operations for agent_notes table
- save_note: UPSERT pattern (INSERT ON CONFLICT UPDATE)
- recall_note: Retrieve single note by key
- list_notes: Retrieve all notes for an agent (for context injection)
- prune_notes: Enforce max 50 notes per agent (oldest pruned)
- format_notes_for_context: Format notes as markdown for system prompt injection

Design Decisions:
- UPSERT via PostgreSQL INSERT ON CONFLICT DO UPDATE
- Max 50 notes per agent (configurable via MAX_NOTES_PER_AGENT)
- Pruning deletes oldest notes beyond the limit
- format_notes_for_context returns compact markdown for prompt injection
- All operations are async (matches TeamOrchestrator DB session pattern)

Zero Mock Policy: Production-ready async SQLAlchemy service.
=========================================================================
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_note import AgentNote

logger = logging.getLogger(__name__)

# Maximum notes per agent — oldest beyond this limit are pruned
MAX_NOTES_PER_AGENT = 50

# Valid note types
VALID_NOTE_TYPES = {"decision", "commitment", "context", "preference"}


class NoteServiceError(Exception):
    """Base error for note service operations."""


class NoteService:
    """CRUD service for agent structured notes (cross-session memory).

    Provides save/recall/list/prune operations for the agent_notes table.
    Used by TeamOrchestrator to inject notes into _build_llm_context()
    and by agents via save_note/recall_note tool calls.

    Usage:
        note_svc = NoteService(db)
        await note_svc.save_note(
            agent_id=uuid4(),
            key="sprint_goal",
            value="Build eval framework",
            note_type="context",
        )
        note = await note_svc.recall_note(agent_id=agent_uuid, key="sprint_goal")
        # note.value == "Build eval framework"
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def save_note(
        self,
        agent_id: UUID,
        key: str,
        value: str,
        note_type: str = "context",
        conversation_id: Optional[UUID] = None,
    ) -> AgentNote:
        """Save or update a note for an agent (UPSERT pattern).

        If a note with the same (agent_id, key) exists, updates the value
        and updated_at timestamp. Otherwise creates a new note.

        Args:
            agent_id: Agent definition ID.
            key: Note key (max 100 chars).
            value: Note value (max 500 chars).
            note_type: Classification (decision|commitment|context|preference).
            conversation_id: Optional conversation binding (NULL = global).

        Returns:
            The saved or updated AgentNote.

        Raises:
            NoteServiceError: If validation fails.
        """
        if not key or len(key) > 100:
            raise NoteServiceError(f"Key must be 1-100 chars, got: {len(key) if key else 0}")

        if not value or len(value) > 500:
            raise NoteServiceError(f"Value must be 1-500 chars, got: {len(value) if value else 0}")

        if note_type not in VALID_NOTE_TYPES:
            raise NoteServiceError(
                f"Invalid note_type '{note_type}'. Must be one of: {VALID_NOTE_TYPES}"
            )

        now = datetime.now(timezone.utc)

        stmt = pg_insert(AgentNote).values(
            agent_id=agent_id,
            key=key,
            value=value,
            note_type=note_type,
            conversation_id=conversation_id,
            created_at=now,
            updated_at=now,
        ).on_conflict_do_update(
            constraint="uq_agent_notes_agent_key",
            set_={
                "value": value,
                "note_type": note_type,
                "conversation_id": conversation_id,
                "updated_at": now,
            },
        ).returning(AgentNote)

        result = await self.db.execute(stmt)
        note = result.scalar_one()
        await self.db.flush()

        # Prune if over limit
        await self._prune_if_needed(agent_id)

        logger.info(
            "TRACE_NOTES: save_note agent_id=%s, key=%s, type=%s",
            agent_id,
            key,
            note_type,
        )

        return note

    async def recall_note(
        self,
        agent_id: UUID,
        key: str,
    ) -> Optional[AgentNote]:
        """Retrieve a single note by key for an agent.

        Args:
            agent_id: Agent definition ID.
            key: Note key to look up.

        Returns:
            AgentNote if found, None otherwise.
        """
        result = await self.db.execute(
            select(AgentNote).where(
                AgentNote.agent_id == agent_id,
                AgentNote.key == key,
            )
        )
        return result.scalar_one_or_none()

    async def list_notes(
        self,
        agent_id: UUID,
        note_type: Optional[str] = None,
        limit: int = MAX_NOTES_PER_AGENT,
    ) -> list[AgentNote]:
        """List all notes for an agent, optionally filtered by type.

        Args:
            agent_id: Agent definition ID.
            note_type: Optional filter by note type.
            limit: Max notes to return (default: MAX_NOTES_PER_AGENT).

        Returns:
            List of AgentNote objects, ordered by updated_at descending.
        """
        query = (
            select(AgentNote)
            .where(AgentNote.agent_id == agent_id)
            .order_by(AgentNote.updated_at.desc())
            .limit(limit)
        )
        if note_type and note_type in VALID_NOTE_TYPES:
            query = query.where(AgentNote.note_type == note_type)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def delete_note(
        self,
        agent_id: UUID,
        key: str,
    ) -> bool:
        """Delete a single note by key.

        Returns:
            True if a note was deleted, False if not found.
        """
        result = await self.db.execute(
            delete(AgentNote).where(
                AgentNote.agent_id == agent_id,
                AgentNote.key == key,
            )
        )
        await self.db.flush()
        deleted = result.rowcount > 0

        if deleted:
            logger.info(
                "TRACE_NOTES: delete_note agent_id=%s, key=%s",
                agent_id,
                key,
            )

        return deleted

    async def count_notes(self, agent_id: UUID) -> int:
        """Count total notes for an agent."""
        result = await self.db.execute(
            select(func.count(AgentNote.id)).where(
                AgentNote.agent_id == agent_id,
            )
        )
        return result.scalar_one()

    async def format_notes_for_context(
        self,
        agent_id: UUID,
        max_notes: int = 20,
    ) -> Optional[str]:
        """Format agent notes as markdown for system prompt injection.

        Returns a compact markdown section or None if no notes exist.
        Notes are ordered by type priority (decision > commitment > context > preference)
        then by updated_at descending.

        Args:
            agent_id: Agent definition ID.
            max_notes: Maximum notes to include (default 20 for prompt brevity).

        Returns:
            Markdown string for system prompt, or None if no notes.
        """
        notes = await self.list_notes(agent_id, limit=max_notes)
        if not notes:
            return None

        # Group by type for organized display
        type_order = ["decision", "commitment", "context", "preference"]
        grouped: dict[str, list[AgentNote]] = {t: [] for t in type_order}
        for note in notes:
            bucket = grouped.get(note.note_type, grouped["context"])
            bucket.append(note)

        lines: list[str] = []
        for note_type in type_order:
            type_notes = grouped[note_type]
            if not type_notes:
                continue
            lines.append(f"**{note_type.title()}s**:")
            for n in type_notes:
                lines.append(f"- {n.key}: {n.value}")

        if not lines:
            return None

        return "\n".join(lines)

    async def _prune_if_needed(self, agent_id: UUID) -> int:
        """Prune oldest notes if agent exceeds MAX_NOTES_PER_AGENT.

        Deletes the oldest notes (by created_at) that exceed the limit.

        Returns:
            Number of notes pruned.
        """
        count = await self.count_notes(agent_id)
        if count <= MAX_NOTES_PER_AGENT:
            return 0

        excess = count - MAX_NOTES_PER_AGENT

        # Find IDs of oldest notes to delete
        oldest_query = (
            select(AgentNote.id)
            .where(AgentNote.agent_id == agent_id)
            .order_by(AgentNote.created_at.asc())
            .limit(excess)
        )
        oldest_result = await self.db.execute(oldest_query)
        ids_to_delete = [row[0] for row in oldest_result.all()]

        if ids_to_delete:
            await self.db.execute(
                delete(AgentNote).where(AgentNote.id.in_(ids_to_delete))
            )
            await self.db.flush()

            logger.info(
                "TRACE_NOTES: Pruned %d notes for agent_id=%s (was %d, max %d)",
                len(ids_to_delete),
                agent_id,
                count,
                MAX_NOTES_PER_AGENT,
            )

        return len(ids_to_delete)
