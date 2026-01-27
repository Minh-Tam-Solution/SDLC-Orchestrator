"""
=========================================================================
Organizations Service - Business Logic for Organization Operations
SDLC Orchestrator - Sprint 71 (Teams Backend API)

Version: 1.0.0
Date: January 27, 2026
Status: ACTIVE - Sprint 71 Implementation
Authority: Backend Lead + CTO Approved
Reference: ADR-028-Teams-Feature-Architecture

Purpose:
- Service layer for organization CRUD operations
- User assignment to organizations
- Organization statistics and metrics
- Multi-tenant root entity management

Zero Mock Policy: Production-ready service with async/await
=========================================================================
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.organization import Organization, UserOrganization
from app.models.team import Team
from app.models.user import User
from app.schemas.team import OrganizationCreate, OrganizationUpdate


# =========================================================================
# Custom Exceptions
# =========================================================================

class OrganizationsServiceError(Exception):
    """Base exception for OrganizationsService errors."""
    pass


class OrganizationNotFoundError(OrganizationsServiceError):
    """Organization not found."""
    def __init__(self, org_id: UUID):
        self.org_id = org_id
        super().__init__(f"Organization {org_id} not found")


class OrganizationSlugExistsError(OrganizationsServiceError):
    """Organization slug already exists."""
    def __init__(self, slug: str):
        self.slug = slug
        super().__init__(f"Organization with slug '{slug}' already exists")


class UserNotInOrganizationError(OrganizationsServiceError):
    """User is not a member of the organization."""
    def __init__(self, user_id: UUID, org_id: UUID):
        self.user_id = user_id
        self.org_id = org_id
        super().__init__(
            f"User {user_id} is not a member of organization {org_id}"
        )


# =========================================================================
# OrganizationsService
# =========================================================================

class OrganizationsService:
    """
    Service layer for organization operations.

    Provides business logic for:
    - Organization CRUD operations
    - User assignment to organizations
    - Organization statistics and metrics

    All methods are async and use SQLAlchemy AsyncSession.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize OrganizationsService.

        Args:
            db: Async database session
        """
        self.db = db

    # =========================================================================
    # Organization CRUD Operations (S71-T11 to T14)
    # =========================================================================

    async def create_organization(
        self,
        data: OrganizationCreate,
        creator_id: UUID
    ) -> Organization:
        """
        Create new organization with creator as first member.

        Sprint 105 Update: Uses join table for multi-org support (GitHub-style).
        Creator is ADDED to the new org without being REMOVED from existing orgs.

        Args:
            data: Organization creation data
            creator_id: UUID of user creating the organization

        Returns:
            Created Organization object

        Raises:
            OrganizationSlugExistsError: If slug already exists

        Note:
            - Creator is added to user_organizations join table as 'owner'
            - If user has no current organization, sets as default
            - Existing org memberships are PRESERVED (not replaced)
        """
        # Check slug uniqueness
        existing = await self.db.scalar(
            select(Organization).where(
                Organization.slug == data.slug,
                Organization.deleted_at.is_(None)
            )
        )
        if existing:
            raise OrganizationSlugExistsError(data.slug)

        # Create organization
        org = Organization(
            name=data.name,
            slug=data.slug,
            plan=data.plan,
            settings=data.settings.model_dump() if data.settings else {}
        )
        self.db.add(org)
        await self.db.flush()

        # Sprint 105: Add creator to join table as owner (multi-org support)
        user_org = UserOrganization(
            user_id=creator_id,
            organization_id=org.id,
            role="owner",
            joined_at=datetime.utcnow()
        )
        self.db.add(user_org)

        # Only set as default org if user has no current organization
        creator = await self.db.get(User, creator_id)
        if creator and creator.organization_id is None:
            creator.organization_id = org.id

        await self.db.commit()
        await self.db.refresh(org)

        return org

    async def get_organization(self, org_id: UUID) -> Optional[Organization]:
        """
        Get organization by ID with teams and users loaded.

        Args:
            org_id: Organization UUID

        Returns:
            Organization object if found, None otherwise

        Note:
            Uses eager loading for teams and users to avoid N+1 queries.
        """
        return await self.db.scalar(
            select(Organization)
            .options(
                selectinload(Organization.teams),
                selectinload(Organization.users)
            )
            .where(
                Organization.id == org_id,
                Organization.deleted_at.is_(None)
            )
        )

    async def list_organizations(
        self,
        user_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 20
    ) -> list[Organization]:
        """
        List organizations with eager-loaded relationships.

        Sprint 105 Update: Uses user_organizations join table for multi-org support.

        Args:
            user_id: Optional filter by user membership
            skip: Pagination offset
            limit: Max results (default 20, max 100)

        Returns:
            List of Organization objects with teams/users loaded

        Note:
            If user_id provided, returns ALL orgs user belongs to (via join table).
            Otherwise returns all organizations (superuser only).
            Uses selectinload to avoid N+1 query issues.
        """
        query = (
            select(Organization)
            .options(
                selectinload(Organization.teams),
                selectinload(Organization.users)
            )
            .where(Organization.deleted_at.is_(None))
        )

        if user_id:
            # Sprint 105: Query via user_organizations join table (multi-org support)
            query = query.join(
                UserOrganization,
                Organization.id == UserOrganization.organization_id
            ).where(UserOrganization.user_id == user_id)

        query = query.offset(skip).limit(min(limit, 100))
        result = await self.db.scalars(query)
        return list(result.all())

    async def update_organization(
        self,
        org_id: UUID,
        data: OrganizationUpdate,
        user_id: UUID
    ) -> Organization:
        """
        Update organization details.

        Args:
            org_id: Organization UUID
            data: Update data
            user_id: User making the update

        Returns:
            Updated Organization object

        Raises:
            OrganizationNotFoundError: If organization not found
            UserNotInOrganizationError: If user not in organization

        Note:
            Only organization members can update it
        """
        # Get organization
        org = await self.get_organization(org_id)
        if not org:
            raise OrganizationNotFoundError(org_id)

        # Check if user is in organization
        user = await self.db.get(User, user_id)
        if not user or user.organization_id != org_id:
            raise UserNotInOrganizationError(user_id, org_id)

        # Update fields
        if data.name is not None:
            org.name = data.name
        if data.slug is not None:
            # Check slug uniqueness
            existing = await self.db.scalar(
                select(Organization).where(
                    Organization.slug == data.slug,
                    Organization.id != org_id,
                    Organization.deleted_at.is_(None)
                )
            )
            if existing:
                raise OrganizationSlugExistsError(data.slug)
            org.slug = data.slug
        if data.plan is not None:
            org.plan = data.plan
        if data.settings is not None:
            org.settings = data.settings.model_dump()

        org.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(org)

        return org

    # =========================================================================
    # Statistics & Metrics (S71-T15)
    # =========================================================================

    async def get_organization_statistics(self, org_id: UUID) -> dict:
        """
        Get organization metrics and statistics.

        Args:
            org_id: Organization UUID

        Returns:
            Dictionary with organization statistics

        Raises:
            OrganizationNotFoundError: If organization not found

        Statistics include:
            - Total teams
            - Total users
            - Plan level
            - SASE configuration status
        """
        org = await self.get_organization(org_id)
        if not org:
            raise OrganizationNotFoundError(org_id)

        # Count teams
        teams_count = await self.db.scalar(
            select(func.count())
            .select_from(Team)
            .where(
                Team.organization_id == org_id,
                Team.deleted_at.is_(None)
            )
        )

        # Count users
        users_count = await self.db.scalar(
            select(func.count())
            .select_from(User)
            .where(
                User.organization_id == org_id,
                User.deleted_at.is_(None)
            )
        )

        # Get SASE config from settings
        sase_config = org.settings.get("sase_config", {})
        agentic_maturity = sase_config.get("agentic_maturity", "L0")

        return {
            "organization_id": org.id,
            "organization_name": org.name,
            "plan": org.plan,
            "teams_count": teams_count or 0,
            "users_count": users_count or 0,
            "agentic_maturity": agentic_maturity,
            "require_mfa": org.settings.get("require_mfa", False),
            "allowed_domains": org.settings.get("allowed_domains", []),
            "created_at": org.created_at,
            "updated_at": org.updated_at
        }

    # =========================================================================
    # User Assignment
    # =========================================================================

    async def assign_user_to_organization(
        self,
        org_id: UUID,
        user_id: UUID
    ) -> User:
        """
        Assign user to organization.

        Args:
            org_id: Organization UUID
            user_id: User UUID

        Returns:
            Updated User object

        Raises:
            OrganizationNotFoundError: If organization not found

        Note:
            User can only belong to one organization at a time
        """
        # Check organization exists
        org = await self.get_organization(org_id)
        if not org:
            raise OrganizationNotFoundError(org_id)

        # Assign user
        user = await self.db.get(User, user_id)
        if user:
            user.organization_id = org_id
            await self.db.commit()
            await self.db.refresh(user)

        return user

    async def remove_user_from_organization(
        self,
        user_id: UUID
    ) -> User:
        """
        Remove user from their organization.

        Args:
            user_id: User UUID

        Returns:
            Updated User object

        Note:
            Sets user's organization_id to NULL
        """
        user = await self.db.get(User, user_id)
        if user:
            user.organization_id = None
            await self.db.commit()
            await self.db.refresh(user)

        return user

    # =========================================================================
    # Plan Management
    # =========================================================================

    async def upgrade_plan(
        self,
        org_id: UUID,
        new_plan: str
    ) -> Organization:
        """
        Upgrade organization plan.

        Args:
            org_id: Organization UUID
            new_plan: New plan level (free, starter, pro, enterprise)

        Returns:
            Updated Organization object

        Raises:
            OrganizationNotFoundError: If organization not found

        Note:
            Plan hierarchy: free < starter < pro < enterprise
        """
        org = await self.get_organization(org_id)
        if not org:
            raise OrganizationNotFoundError(org_id)

        org.plan = new_plan
        org.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(org)

        return org
