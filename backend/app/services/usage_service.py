"""
==========================================================================
UsageService — Sprint 188 Per-User Resource Usage Queries
SDLC Orchestrator — Tier Enforcement Layer

Purpose:
- Compute current resource consumption for a user across 4 dimensions:
    1. project_count   — active projects owned by user
    2. storage_mb      — total evidence file size (bytes → MB)
    3. gates_this_month — gates created since first day of current UTC month
    4. team_members    — members in user's primary organization

Architecture:
- Stateless service: all methods are pure async queries, no side-effects
- Uses AsyncSession directly (called from ASGI middleware, not FastAPI deps)
- Soft-deleted rows (deleted_at IS NOT NULL) are excluded from all counts
- All queries indexed: owner_id, gate.created_by, evidence.uploaded_by,
  user_organizations.user_id — p95 <10ms each

Zero Mock Policy: real SQLAlchemy 2.0 async queries throughout.
SDLC 6.1.0 — Sprint 188 P0 Deliverable
Authority: CTO + Backend Lead Approved
==========================================================================
"""

import logging
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.gate import Gate
from app.models.gate_evidence import GateEvidence
from app.models.organization import UserOrganization
from app.models.project import Project

logger = logging.getLogger(__name__)


class UsageService:
    """
    Per-user resource usage calculator for Sprint 188 tier enforcement.

    All methods accept an AsyncSession and user_id (UUID).
    They return integer / float counts — the caller decides whether
    the value exceeds a tier limit.

    Performance targets (indexed queries):
        - project_count:      <5ms
        - storage_mb:         <10ms
        - gates_this_month:   <5ms
        - team_members:       <5ms
    """

    # ------------------------------------------------------------------
    # Public async query methods
    # ------------------------------------------------------------------

    @staticmethod
    async def get_project_count(db: AsyncSession, user_id: UUID) -> int:
        """
        Count active projects owned by the user.

        Excludes soft-deleted (deleted_at IS NOT NULL) and inactive projects.

        Args:
            db:      Open AsyncSession
            user_id: UUID of the authenticated user

        Returns:
            Integer count of active owned projects.
        """
        result = await db.execute(
            select(func.count())
            .select_from(Project)
            .where(
                Project.owner_id == user_id,
                Project.deleted_at.is_(None),
                Project.is_active.is_(True),
            )
        )
        count: int = result.scalar_one_or_none() or 0
        logger.debug("UsageService.get_project_count user=%s count=%d", user_id, count)
        return count

    @staticmethod
    async def get_storage_mb(db: AsyncSession, user_id: UUID) -> float:
        """
        Calculate total evidence storage consumed by the user's projects in MB.

        Strategy:
        - Join GateEvidence → Gate → Project on owner_id = user_id
        - SUM file_size (bytes) across all non-deleted evidence rows
        - Convert to MB (divide by 1,048,576)

        Args:
            db:      Open AsyncSession
            user_id: UUID of the authenticated user

        Returns:
            Total storage in megabytes (float, 0.0 if no evidence).
        """
        # GateEvidence has no direct user FK — it belongs to a Gate which belongs to a Project
        # whose owner_id is the user.  We join through both tables.
        result = await db.execute(
            select(func.coalesce(func.sum(GateEvidence.file_size), 0))
            .select_from(GateEvidence)
            .join(Gate, Gate.id == GateEvidence.gate_id)
            .join(Project, Project.id == Gate.project_id)
            .where(
                Project.owner_id == user_id,
                GateEvidence.deleted_at.is_(None),
                Gate.deleted_at.is_(None),
                Project.deleted_at.is_(None),
            )
        )
        total_bytes: int = result.scalar_one_or_none() or 0
        storage_mb = total_bytes / 1_048_576
        logger.debug(
            "UsageService.get_storage_mb user=%s bytes=%d mb=%.3f",
            user_id, total_bytes, storage_mb,
        )
        return storage_mb

    @staticmethod
    async def get_gates_this_month(db: AsyncSession, user_id: UUID) -> int:
        """
        Count gates created by the user since the first day of the current UTC month.

        LITE tier has a hard monthly gate limit (default: 4/month).
        The window resets at 00:00:00 UTC on the first of each calendar month.

        Args:
            db:      Open AsyncSession
            user_id: UUID of the authenticated user

        Returns:
            Integer count of gates created this calendar month.
        """
        now_utc = datetime.now(timezone.utc)
        # First moment of the current month in UTC — must be timezone-aware to compare
        # safely against TIMESTAMPTZ columns in PostgreSQL (naive datetime vs TIMESTAMPTZ
        # raises ProgrammingError in asyncpg/psycopg3).
        month_start = datetime(now_utc.year, now_utc.month, 1, tzinfo=timezone.utc)

        result = await db.execute(
            select(func.count())
            .select_from(Gate)
            .where(
                Gate.created_by == user_id,
                Gate.deleted_at.is_(None),
                Gate.created_at >= month_start,
            )
        )
        count: int = result.scalar_one_or_none() or 0
        logger.debug(
            "UsageService.get_gates_this_month user=%s month_start=%s count=%d",
            user_id, month_start.isoformat(), count,
        )
        return count

    @staticmethod
    async def get_team_members(db: AsyncSession, user_id: UUID) -> int:
        """
        Count members in the user's primary organization.

        "Primary organization" = the organization linked via users.organization_id.
        We count distinct user_ids in user_organizations for that org.

        If the user has no primary organization, returns 1 (only the user themselves),
        since a solo user still occupies one team-member slot.

        Args:
            db:      Open AsyncSession
            user_id: UUID of the authenticated user

        Returns:
            Integer count of organization members (minimum 1).
        """
        from app.models.user import User  # local import avoids circular dependency

        # Step 1: resolve user's primary organization_id
        user_result = await db.execute(
            select(User.organization_id).where(User.id == user_id)
        )
        org_id = user_result.scalar_one_or_none()

        if org_id is None:
            # No org — user is solo; count as 1
            logger.debug(
                "UsageService.get_team_members user=%s no_org → returning 1", user_id
            )
            return 1

        # Step 2: count members in that org via user_organizations join table
        result = await db.execute(
            select(func.count())
            .select_from(UserOrganization)
            .where(UserOrganization.organization_id == org_id)
        )
        count: int = result.scalar_one_or_none() or 1
        logger.debug(
            "UsageService.get_team_members user=%s org=%s count=%d",
            user_id, org_id, count,
        )
        return count

    @staticmethod
    async def get_all(db: AsyncSession, user_id: UUID) -> dict[str, int | float]:
        """
        Fetch all four usage dimensions in a single call (sequential queries).

        Returns a dict with keys:
            project_count, storage_mb, gates_this_month, team_members

        Args:
            db:      Open AsyncSession
            user_id: UUID of the authenticated user

        Returns:
            Dict[str, int | float] with all four usage metrics.
        """
        return {
            "project_count": await UsageService.get_project_count(db, user_id),
            "storage_mb": await UsageService.get_storage_mb(db, user_id),
            "gates_this_month": await UsageService.get_gates_this_month(db, user_id),
            "team_members": await UsageService.get_team_members(db, user_id),
        }
