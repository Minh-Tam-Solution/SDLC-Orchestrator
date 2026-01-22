"""
Row-Level Security Context Middleware
Sprint 89: PostgreSQL RLS Policies

Sets database session variables for RLS enforcement:
- app.current_user_id: Current authenticated user
- app.current_org_id: User's organization (from first team membership)
- app.bypass_rls: True for platform admins

Usage:
    Include RLSContextMiddleware in FastAPI app startup.
    Alternatively, use set_rls_context() dependency in routes.

Reference: Expert Feedback Plan Section 3.1 (Multi-tenant RLS Implementation)
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.user import User

logger = logging.getLogger(__name__)


async def set_rls_context(
    db: AsyncSession,
    user_id: Optional[UUID] = None,
    org_id: Optional[UUID] = None,
    bypass_rls: bool = False,
) -> None:
    """
    Set RLS context variables for the current database session.

    This function must be called before any queries that need RLS enforcement.
    The context is transaction-scoped (true = local to transaction).

    Args:
        db: Async database session
        user_id: Current user's UUID (None for anonymous)
        org_id: User's organization UUID (None to auto-detect)
        bypass_rls: True to bypass RLS (for platform admins)

    Example:
        async with get_db() as db:
            await set_rls_context(db, user_id=current_user.id)
            # Now all queries respect RLS
            projects = await db.execute(select(Project))
    """
    try:
        # Convert to strings for PostgreSQL set_config
        user_str = str(user_id) if user_id else ""
        org_str = str(org_id) if org_id else ""
        bypass_str = "true" if bypass_rls else "false"

        # Use the helper function created in migration
        await db.execute(
            text("SELECT set_rls_context(:user_id::uuid, :org_id::uuid, :bypass::boolean)"),
            {
                "user_id": user_str if user_str else None,
                "org_id": org_str if org_str else None,
                "bypass": bypass_rls,
            }
        )

        logger.debug(
            f"RLS context set: user={user_str[:8] if user_str else 'none'}..., "
            f"org={org_str[:8] if org_str else 'none'}..., bypass={bypass_rls}"
        )

    except Exception as e:
        logger.warning(f"Failed to set RLS context: {e}")
        # Don't fail the request, just log the warning
        # Application-level filtering will still work


async def get_user_organization_id(db: AsyncSession, user_id: UUID) -> Optional[UUID]:
    """
    Get the user's primary organization ID.

    Queries team_members to find the user's organization.
    Returns the first organization found (users typically belong to one org).

    Args:
        db: Database session
        user_id: User's UUID

    Returns:
        Organization UUID or None if user has no team membership
    """
    try:
        result = await db.execute(
            text("""
                SELECT DISTINCT t.organization_id
                FROM team_members tm
                JOIN teams t ON tm.team_id = t.id
                WHERE tm.user_id = :user_id
                AND tm.deleted_at IS NULL
                LIMIT 1
            """),
            {"user_id": str(user_id)}
        )
        row = result.fetchone()
        return UUID(row[0]) if row else None

    except Exception as e:
        logger.warning(f"Failed to get user organization: {e}")
        return None


async def rls_context_dependency(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
) -> AsyncSession:
    """
    FastAPI dependency that sets RLS context for the current request.

    Use this dependency in route handlers that need RLS enforcement:

        @router.get("/projects")
        async def list_projects(db: AsyncSession = Depends(rls_context_dependency)):
            # RLS is already configured for this session
            return await db.execute(select(Project))

    Args:
        request: FastAPI request object
        db: Database session from get_db dependency
        current_user: Current authenticated user (or None)

    Returns:
        Database session with RLS context configured
    """
    if current_user:
        # Check if platform admin (bypass RLS)
        is_platform_admin = getattr(current_user, 'is_platform_admin', False)

        if is_platform_admin:
            # Platform admins bypass RLS but still need context for audit
            await set_rls_context(
                db,
                user_id=current_user.id,
                org_id=None,
                bypass_rls=True
            )
        else:
            # Regular users get organization-scoped RLS
            org_id = await get_user_organization_id(db, current_user.id)
            await set_rls_context(
                db,
                user_id=current_user.id,
                org_id=org_id,
                bypass_rls=False
            )
    else:
        # Anonymous users: no RLS context (all queries filtered out)
        await set_rls_context(db, user_id=None, org_id=None, bypass_rls=False)

    return db


class RLSContextManager:
    """
    Context manager for RLS-aware database operations.

    Useful for background tasks or services that don't go through FastAPI routes.

    Usage:
        async with RLSContextManager(db, user_id=user.id) as session:
            projects = await session.execute(select(Project))

    Args:
        db: Async database session
        user_id: User UUID for RLS context
        org_id: Organization UUID (optional, auto-detected)
        bypass_rls: Bypass RLS for admin operations
    """

    def __init__(
        self,
        db: AsyncSession,
        user_id: Optional[UUID] = None,
        org_id: Optional[UUID] = None,
        bypass_rls: bool = False,
    ):
        self.db = db
        self.user_id = user_id
        self.org_id = org_id
        self.bypass_rls = bypass_rls

    async def __aenter__(self) -> AsyncSession:
        # Auto-detect organization if not provided
        if self.user_id and not self.org_id and not self.bypass_rls:
            self.org_id = await get_user_organization_id(self.db, self.user_id)

        await set_rls_context(
            self.db,
            user_id=self.user_id,
            org_id=self.org_id,
            bypass_rls=self.bypass_rls
        )
        return self.db

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Clear RLS context
        await set_rls_context(self.db, user_id=None, org_id=None, bypass_rls=False)
        return False


# Utility function for background jobs
async def run_with_rls_bypass(db: AsyncSession, func, *args, **kwargs):
    """
    Run a function with RLS bypassed (for system operations).

    Use sparingly and only for legitimate admin/system tasks:
    - Migrations
    - Scheduled cleanup jobs
    - Analytics aggregation
    - Cross-tenant reporting

    Args:
        db: Database session
        func: Async function to execute
        *args, **kwargs: Arguments to pass to func

    Returns:
        Result of func execution

    Example:
        async def cleanup_expired_tokens(db):
            await db.execute(delete(Token).where(...))

        await run_with_rls_bypass(db, cleanup_expired_tokens, db)
    """
    try:
        await set_rls_context(db, bypass_rls=True)
        return await func(*args, **kwargs)
    finally:
        await set_rls_context(db, bypass_rls=False)
