"""
Delegation Service — Sprint 216 (P1 Context Injection).

Manages delegation links between agent definitions.
Port of MTClaw agent_links.go pattern.

Methods:
- can_delegate(source_id, target_id) — check if active link exists
- get_targets(agent_id) — list active delegation targets
- get_sources(agent_id) — list agents that can delegate TO this agent
- create_link(source_id, target_id, link_type) — insert with duplicate check
- deactivate_link(source_id, target_id) — soft delete (is_active=False)
- get_max_updated_at(agent_id) — for context cache key freshness

References:
- ADR-069, FR-051, Sprint 216 Track A
- MTClaw: /home/nqh/shared/MTClaw/internal/store/pg/agent_links.go
"""

from __future__ import annotations

import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy import and_, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.delegation_link import DelegationLink

logger = logging.getLogger(__name__)


class DuplicateLinkError(Exception):
    """Raised when a delegation link already exists."""


class SelfDelegationError(Exception):
    """Raised when source_agent_id == target_agent_id."""


class DelegationService:
    """
    CRUD + query operations for delegation_links table.

    All queries filter on is_active=True by default.
    Deactivation is preferred over hard deletion for audit compliance.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def can_delegate(
        self,
        source_id: UUID,
        target_id: UUID,
        link_type: str = "can_delegate",
    ) -> bool:
        """
        Check if an active delegation link exists from source to target.

        Args:
            source_id: Source agent definition ID.
            target_id: Target agent definition ID.
            link_type: Link type to check (default: can_delegate).

        Returns:
            True if an active link exists, False otherwise.
        """
        stmt = select(func.count()).select_from(DelegationLink).where(
            and_(
                DelegationLink.source_agent_id == source_id,
                DelegationLink.target_agent_id == target_id,
                DelegationLink.link_type == link_type,
                DelegationLink.is_active.is_(True),
            )
        )
        result = await self.db.execute(stmt)
        count = result.scalar_one()
        return count > 0

    async def get_targets(
        self,
        agent_id: UUID,
        link_type: str = "can_delegate",
    ) -> list[DelegationLink]:
        """
        Get all active delegation targets for an agent.

        Used by context injector to build DELEGATION.md section.

        Args:
            agent_id: Source agent definition ID.
            link_type: Filter by link type.

        Returns:
            List of DelegationLink rows with target_agent eagerly loaded.
        """
        stmt = (
            select(DelegationLink)
            .where(
                and_(
                    DelegationLink.source_agent_id == agent_id,
                    DelegationLink.link_type == link_type,
                    DelegationLink.is_active.is_(True),
                )
            )
            .order_by(DelegationLink.created_at)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_sources(
        self,
        agent_id: UUID,
        link_type: str = "can_delegate",
    ) -> list[DelegationLink]:
        """
        Get all agents that can delegate TO this agent.

        Args:
            agent_id: Target agent definition ID.
            link_type: Filter by link type.

        Returns:
            List of DelegationLink rows with source_agent eagerly loaded.
        """
        stmt = (
            select(DelegationLink)
            .where(
                and_(
                    DelegationLink.target_agent_id == agent_id,
                    DelegationLink.link_type == link_type,
                    DelegationLink.is_active.is_(True),
                )
            )
            .order_by(DelegationLink.created_at)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create_link(
        self,
        source_id: UUID,
        target_id: UUID,
        link_type: str = "can_delegate",
        metadata: dict | None = None,
    ) -> DelegationLink:
        """
        Create a new delegation link.

        If a deactivated link already exists for the same (source, target, type),
        reactivates it instead of creating a duplicate.

        Args:
            source_id: Source agent definition ID.
            target_id: Target agent definition ID.
            link_type: Link type (default: can_delegate).
            metadata: Optional metadata dict.

        Returns:
            Created or reactivated DelegationLink.

        Raises:
            SelfDelegationError: If source_id == target_id.
            DuplicateLinkError: If an active link already exists.
        """
        if source_id == target_id:
            raise SelfDelegationError(
                f"Cannot create self-delegation link: agent {source_id}"
            )

        # Check for existing link (active or inactive)
        stmt = select(DelegationLink).where(
            and_(
                DelegationLink.source_agent_id == source_id,
                DelegationLink.target_agent_id == target_id,
                DelegationLink.link_type == link_type,
            )
        )
        result = await self.db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing is not None:
            if existing.is_active:
                raise DuplicateLinkError(
                    f"Active delegation link already exists: "
                    f"{source_id} -> {target_id} ({link_type})"
                )
            # Reactivate deactivated link
            existing.is_active = True
            existing.updated_at = datetime.utcnow()
            if metadata is not None:
                existing.metadata_ = metadata
            await self.db.flush()
            logger.info(
                "Reactivated delegation link: %s -> %s (%s)",
                source_id, target_id, link_type,
            )
            return existing

        link = DelegationLink(
            source_agent_id=source_id,
            target_agent_id=target_id,
            link_type=link_type,
            metadata_=metadata or {},
        )
        self.db.add(link)

        try:
            await self.db.flush()
        except IntegrityError as exc:
            await self.db.rollback()
            raise DuplicateLinkError(
                f"Delegation link constraint violation: {exc}"
            ) from exc

        logger.info(
            "Created delegation link: %s -> %s (%s)",
            source_id, target_id, link_type,
        )
        return link

    async def deactivate_link(
        self,
        source_id: UUID,
        target_id: UUID,
        link_type: str = "can_delegate",
    ) -> bool:
        """
        Soft-delete a delegation link by setting is_active=False.

        Args:
            source_id: Source agent definition ID.
            target_id: Target agent definition ID.
            link_type: Link type.

        Returns:
            True if a link was deactivated, False if no active link found.
        """
        stmt = (
            update(DelegationLink)
            .where(
                and_(
                    DelegationLink.source_agent_id == source_id,
                    DelegationLink.target_agent_id == target_id,
                    DelegationLink.link_type == link_type,
                    DelegationLink.is_active.is_(True),
                )
            )
            .values(is_active=False, updated_at=datetime.utcnow())
        )
        result = await self.db.execute(stmt)
        deactivated = result.rowcount > 0

        if deactivated:
            logger.info(
                "Deactivated delegation link: %s -> %s (%s)",
                source_id, target_id, link_type,
            )
        return deactivated

    async def get_max_updated_at(self, agent_id: UUID) -> datetime | None:
        """
        Get the most recent updated_at for any delegation link involving this agent.

        Used as part of the context injection cache key:
        ctx:{agent_id}:{team_id}:{max_updated_at}

        Args:
            agent_id: Agent definition ID (as source).

        Returns:
            Max updated_at datetime, or None if no links exist.
        """
        stmt = select(func.max(DelegationLink.updated_at)).where(
            DelegationLink.source_agent_id == agent_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_target_count(self, agent_id: UUID) -> int:
        """
        Count active delegation targets for an agent.

        Used by AVAILABILITY.md builder to decide whether to emit negative context.

        Args:
            agent_id: Source agent definition ID.

        Returns:
            Count of active delegation targets.
        """
        stmt = select(func.count()).select_from(DelegationLink).where(
            and_(
                DelegationLink.source_agent_id == agent_id,
                DelegationLink.is_active.is_(True),
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one()
