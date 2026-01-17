"""
=========================================================================
Organizations API Routes - Organization Management Endpoints
SDLC Orchestrator - Sprint 71 (Teams Backend API)

Version: 1.0.0
Date: January 27, 2026
Status: ACTIVE - Sprint 71 Implementation
Authority: Backend Lead + CTO Approved
Reference: ADR-028-Teams-Feature-Architecture
Reference: Teams-API-Specification.md

API Endpoints (4 total):
- POST   /organizations              - Create organization
- GET    /organizations              - List organizations
- GET    /organizations/{org_id}     - Get organization details
- PATCH  /organizations/{org_id}     - Update organization
- GET    /organizations/{org_id}/stats - Organization statistics

Multi-Tenancy:
- Organizations are the root entity for multi-tenancy
- Users belong to one organization
- Teams belong to organizations

Zero Mock Policy: Production-ready API routes
=========================================================================
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.team import (
    OrganizationCreate,
    OrganizationListResponse,
    OrganizationResponse,
    OrganizationUpdate,
)
from app.services.organizations_service import (
    OrganizationNotFoundError,
    OrganizationSlugExistsError,
    OrganizationsService,
    UserNotInOrganizationError,
)


router = APIRouter(prefix="/organizations", tags=["organizations"])


# =========================================================================
# Helper Functions
# =========================================================================

def org_to_response(org, teams_count: int = 0, users_count: int = 0) -> OrganizationResponse:
    """Convert Organization model to OrganizationResponse schema."""
    # Count teams and users from relationships if loaded
    if hasattr(org, 'teams') and org.teams:
        teams_count = sum(1 for t in org.teams if t.deleted_at is None)
    if hasattr(org, 'users') and org.users:
        users_count = sum(1 for u in org.users if u.deleted_at is None)

    return OrganizationResponse(
        id=org.id,
        name=org.name,
        slug=org.slug,
        plan=org.plan,
        settings=org.settings or {},
        teams_count=teams_count,
        users_count=users_count,
        created_at=org.created_at,
        updated_at=org.updated_at
    )


# =========================================================================
# Organization CRUD Endpoints (S71-T26 to T29)
# =========================================================================

@router.post(
    "",
    response_model=OrganizationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Organization",
    description="Create a new organization. The creator is automatically assigned to it."
)
async def create_organization(
    data: OrganizationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new organization.

    - **name**: Organization display name (2-255 chars)
    - **slug**: URL-safe identifier (globally unique)
    - **plan**: Subscription plan (free, starter, pro, enterprise)
    - **settings**: Organization settings including SASE config

    The authenticated user is automatically assigned to the new organization.
    """
    service = OrganizationsService(db)
    
    try:
        org = await service.create_organization(data, current_user.id)
        return org_to_response(org)
    except OrganizationSlugExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Organization with slug '{e.slug}' already exists"
        )


@router.get(
    "",
    response_model=OrganizationListResponse,
    summary="List Organizations",
    description="List organizations. Regular users see only their own organization."
)
async def list_organizations(
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(20, ge=1, le=100, description="Max results"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List organizations.

    For regular users: Returns only the organization they belong to.
    For superusers: Returns all organizations (for admin purposes).

    - **skip**: Pagination offset (default 0)
    - **limit**: Max results per page (1-100, default 20)
    """
    service = OrganizationsService(db)
    
    # Non-superusers only see their organization
    user_filter = None if current_user.is_superuser else current_user.id
    
    orgs = await service.list_organizations(
        user_id=user_filter,
        skip=skip,
        limit=limit
    )
    
    return OrganizationListResponse(
        items=[org_to_response(o) for o in orgs],
        total=len(orgs),
        page=skip // limit + 1 if limit > 0 else 1,
        page_size=limit,
        has_next=len(orgs) == limit
    )


@router.get(
    "/{org_id}",
    response_model=OrganizationResponse,
    summary="Get Organization",
    description="Get organization details by ID."
)
async def get_organization(
    org_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed information about a specific organization.

    Returns organization details including:
    - Basic info (name, slug, plan)
    - Settings (MFA requirement, allowed domains, SASE config)
    - Team count
    - User count
    """
    service = OrganizationsService(db)
    
    org = await service.get_organization(org_id)
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Organization {org_id} not found"
        )
    
    # Check access: user must belong to org or be superuser
    if not current_user.is_superuser and current_user.organization_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this organization"
        )
    
    return org_to_response(org)


@router.patch(
    "/{org_id}",
    response_model=OrganizationResponse,
    summary="Update Organization",
    description="Update organization details. User must be a member."
)
async def update_organization(
    org_id: UUID,
    data: OrganizationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update organization details.

    User must be a member of the organization.

    Updatable fields:
    - **name**: Organization display name
    - **slug**: URL-safe identifier (must be globally unique)
    - **plan**: Subscription plan
    - **settings**: Organization settings
    """
    service = OrganizationsService(db)
    
    try:
        org = await service.update_organization(org_id, data, current_user.id)
        return org_to_response(org)
    except OrganizationNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Organization {org_id} not found"
        )
    except UserNotInOrganizationError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this organization"
        )
    except OrganizationSlugExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Organization with slug '{e.slug}' already exists"
        )


# =========================================================================
# Organization Statistics Endpoint
# =========================================================================

@router.get(
    "/{org_id}/stats",
    summary="Get Organization Statistics",
    description="Get organization metrics and statistics."
)
async def get_organization_statistics(
    org_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed statistics for an organization.

    Returns:
    - **plan**: Subscription plan
    - **teams_count**: Total teams
    - **users_count**: Total users
    - **agentic_maturity**: SASE maturity level
    - **require_mfa**: MFA requirement status
    - **allowed_domains**: Email domain restrictions
    """
    service = OrganizationsService(db)
    
    # Check access
    if not current_user.is_superuser and current_user.organization_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this organization"
        )
    
    try:
        return await service.get_organization_statistics(org_id)
    except OrganizationNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Organization {org_id} not found"
        )
