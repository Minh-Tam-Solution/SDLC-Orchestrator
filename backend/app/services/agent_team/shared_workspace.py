"""Shared Workspace Service — Sprint 219 (P5 Shared Workspace Foundation).

Conversation-scoped key-value workspace for cross-agent collaboration.
Optimistic concurrency via version column (UPDATE WHERE version=expected).
Soft delete via version=-1 (preserves audit trail).

Parent-child isolation: children READ parent workspace via
parent_conversation_id chain. WRITE only to own conversation's workspace.

References:
- ADR-072, Sprint 219 Track B
- CoPaw ReMe shared memory pattern
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.shared_workspace import (
    SharedWorkspaceItem,
    WORKSPACE_ITEM_TYPES,
    CONFLICT_STRATEGIES,
)

logger = logging.getLogger(__name__)

# Preview truncation length for list_keys()
PREVIEW_MAX_LEN = 50


class VersionConflictError(Exception):
    """Raised when optimistic version check fails on update."""

    def __init__(self, item_key: str, expected: int, actual: int):
        self.item_key = item_key
        self.expected = expected
        self.actual = actual
        super().__init__(
            f"Version conflict on key '{item_key}': "
            f"expected={expected}, actual={actual}"
        )


class SharedWorkspace:
    """Conversation-scoped shared workspace with optimistic concurrency.

    All operations are scoped to a single conversation_id.
    Uses SELECT FOR UPDATE for serialization on writes.
    """

    def __init__(self, db: AsyncSession, conversation_id: UUID):
        self.db = db
        self.conversation_id = conversation_id

    async def put(
        self,
        item_key: str,
        content: str,
        agent_id: UUID | None = None,
        item_type: str = "text",
        expected_version: int | None = None,
        conflict_resolution: str = "last_write_wins",
    ) -> SharedWorkspaceItem:
        """Create or update a workspace item (upsert).

        Optimistic concurrency: if expected_version is provided,
        update only succeeds when current version matches.

        Args:
            item_key: Unique key within conversation (e.g., 'coder/main.py').
            content: Item content.
            agent_id: Agent performing the write.
            item_type: Content type (text|code|diff|json|markdown|binary_ref).
            expected_version: If set, requires version match (optimistic lock).
            conflict_resolution: Strategy on conflict.

        Returns:
            The created or updated SharedWorkspaceItem.

        Raises:
            ValueError: If item_key, item_type, or conflict_resolution is invalid.
            VersionConflictError: If expected_version doesn't match current.
        """
        # Input validation (CTO F1 — prevent raw DB errors)
        if not item_key or len(item_key) > 200:
            raise ValueError(f"item_key must be 1-200 chars, got {len(item_key) if item_key else 0}")
        if item_type not in WORKSPACE_ITEM_TYPES:
            raise ValueError(f"Invalid item_type: {item_type!r}")
        if conflict_resolution not in CONFLICT_STRATEGIES:
            raise ValueError(f"Invalid conflict_resolution: {conflict_resolution!r}")

        # Try to find existing active item (SELECT FOR UPDATE)
        result = await self.db.execute(
            select(SharedWorkspaceItem)
            .where(
                and_(
                    SharedWorkspaceItem.conversation_id == self.conversation_id,
                    SharedWorkspaceItem.item_key == item_key,
                    SharedWorkspaceItem.version > 0,
                )
            )
            .with_for_update()
        )
        existing = result.scalar_one_or_none()

        if existing is not None:
            # Update existing item
            if expected_version is not None and existing.version != expected_version:
                raise VersionConflictError(
                    item_key, expected_version, existing.version,
                )

            existing.content = content
            existing.version += 1
            existing.item_type = item_type
            existing.updated_by = agent_id
            existing.conflict_resolution = conflict_resolution
            existing.updated_at = datetime.now(timezone.utc)
            await self.db.flush()

            logger.debug(
                "TRACE_WORKSPACE: updated key=%r v=%d conv=%s",
                item_key, existing.version, self.conversation_id,
            )
            return existing

        # Insert new item
        from uuid import uuid4 as _uuid4
        item = SharedWorkspaceItem(
            id=_uuid4(),
            conversation_id=self.conversation_id,
            created_by=agent_id,
            updated_by=agent_id,
            item_key=item_key,
            item_type=item_type,
            content=content,
            version=1,
            conflict_resolution=conflict_resolution,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        self.db.add(item)
        await self.db.flush()

        logger.debug(
            "TRACE_WORKSPACE: created key=%r v=1 conv=%s",
            item_key, self.conversation_id,
        )
        return item

    async def get(self, item_key: str) -> SharedWorkspaceItem | None:
        """Get an active workspace item by key.

        Args:
            item_key: Workspace key.

        Returns:
            SharedWorkspaceItem if found and active (version > 0), None otherwise.
        """
        result = await self.db.execute(
            select(SharedWorkspaceItem).where(
                and_(
                    SharedWorkspaceItem.conversation_id == self.conversation_id,
                    SharedWorkspaceItem.item_key == item_key,
                    SharedWorkspaceItem.version > 0,
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_keys(self) -> list[dict]:
        """List all active workspace keys with 50-char content preview.

        Returns:
            List of dicts with item_key, item_type, version, preview, updated_by.
        """
        result = await self.db.execute(
            select(SharedWorkspaceItem).where(
                and_(
                    SharedWorkspaceItem.conversation_id == self.conversation_id,
                    SharedWorkspaceItem.version > 0,
                )
            ).order_by(SharedWorkspaceItem.item_key)
        )
        items = result.scalars().all()

        output = []
        for item in items:
            preview = ""
            if item.content:
                preview = item.content[:PREVIEW_MAX_LEN]
                if len(item.content) > PREVIEW_MAX_LEN:
                    preview += "\u2026"  # ellipsis
            output.append({
                "item_key": item.item_key,
                "item_type": item.item_type,
                "version": item.version,
                "preview": preview,
                "updated_by": str(item.updated_by) if item.updated_by else None,
            })

        return output

    async def delete(
        self,
        item_key: str,
        agent_id: UUID | None = None,
    ) -> bool:
        """Soft-delete a workspace item (set version=-1).

        Args:
            item_key: Workspace key to delete.
            agent_id: Agent performing the delete.

        Returns:
            True if item was deleted, False if not found.
        """
        result = await self.db.execute(
            update(SharedWorkspaceItem)
            .where(
                and_(
                    SharedWorkspaceItem.conversation_id == self.conversation_id,
                    SharedWorkspaceItem.item_key == item_key,
                    SharedWorkspaceItem.version > 0,
                )
            )
            .values(
                version=-1,
                updated_by=agent_id,
                updated_at=datetime.now(timezone.utc),
            )
        )
        deleted = result.rowcount > 0

        if deleted:
            logger.debug(
                "TRACE_WORKSPACE: soft-deleted key=%r conv=%s",
                item_key, self.conversation_id,
            )
        return deleted

    async def get_active_keys(self) -> list[str]:
        """Get list of active key names (version > 0).

        Returns:
            List of item_key strings.
        """
        result = await self.db.execute(
            select(SharedWorkspaceItem.item_key).where(
                and_(
                    SharedWorkspaceItem.conversation_id == self.conversation_id,
                    SharedWorkspaceItem.version > 0,
                )
            ).order_by(SharedWorkspaceItem.item_key)
        )
        return list(result.scalars().all())
