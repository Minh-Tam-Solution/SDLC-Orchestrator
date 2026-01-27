"""
=========================================================================
Teams API Routes - Team Management Endpoints
SDLC Orchestrator - Sprint 71 (Teams Backend API)

Version: 1.0.0
Date: January 27, 2026
Status: ACTIVE - Sprint 71 Implementation
Authority: Backend Lead + CTO Approved
Reference: ADR-028-Teams-Feature-Architecture
Reference: Teams-API-Specification.md

API Endpoints (10 total):
- POST   /teams                    - Create team
- GET    /teams                    - List teams
- GET    /teams/{team_id}          - Get team details
- PATCH  /teams/{team_id}          - Update team
- DELETE /teams/{team_id}          - Delete team
- GET    /teams/{team_id}/stats    - Team statistics
- POST   /teams/{team_id}/members  - Add member
- DELETE /teams/{team_id}/members/{user_id} - Remove member
- PATCH  /teams/{team_id}/members/{user_id} - Update member role
- GET    /teams/{team_id}/members  - List members

SDLC 5.1.2 SASE Compliance:
- Owner/Admin = SE4H (Agent Coach) - VCR authority
- Member = SE4H/SE4A - Implementation work
- ai_agent = SE4A (Agent Executor) - Autonomous tasks

Zero Mock Policy: Production-ready API routes
=========================================================================
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.team_member import TeamMember
from app.models.user import User
from app.schemas.team import (
    TeamCreate,
    TeamListResponse,
    TeamMemberAdd,
    TeamMemberListResponse,
    TeamMemberResponse,
    TeamMemberUpdate,
    TeamResponse,
    TeamRole,
    TeamSettings,
    TeamStatistics,
    TeamUpdate,
    MemberType,
)
from app.services.teams_service import (
    CannotRemoveLastOwnerError,
    InvalidRoleError,
    MemberNotFoundError,
    PermissionDeniedError,
    TeamNotFoundError,
    TeamSlugExistsError,
    TeamsService,
    UserAlreadyMemberError,
    UserNotFoundByEmailError,
)


router = APIRouter(prefix="/teams", tags=["teams"])


# =========================================================================
# Helper Functions
# =========================================================================

def team_to_response(team, members_count: int = 0, projects_count: int = 0) -> TeamResponse:
    """Convert Team model to TeamResponse schema."""
    # Count members by type
    human_count = 0
    ai_count = 0
    if hasattr(team, 'members') and team.members:
        for m in team.members:
            if m.deleted_at is None:
                if m.member_type == "human":
                    human_count += 1
                else:
                    ai_count += 1
        members_count = human_count + ai_count
    
    # Count projects
    if hasattr(team, 'projects') and team.projects:
        projects_count = sum(1 for p in team.projects if p.deleted_at is None)

    return TeamResponse(
        id=team.id,
        organization_id=team.organization_id,
        name=team.name,
        slug=team.slug,
        description=team.description,
        settings=team.settings or {},
        members_count=members_count,
        human_members_count=human_count,
        ai_agents_count=ai_count,
        projects_count=projects_count,
        created_at=team.created_at,
        updated_at=team.updated_at
    )


def member_to_response(member) -> TeamMemberResponse:
    """Convert TeamMember model to TeamMemberResponse schema."""
    user = member.user if hasattr(member, 'user') and member.user else None
    
    return TeamMemberResponse(
        id=member.id,
        team_id=member.team_id,
        user_id=member.user_id,
        role=TeamRole(member.role),
        member_type=MemberType(member.member_type),
        sase_role=member.get_sase_role() if hasattr(member, 'get_sase_role') else "SE4H_Member",
        joined_at=member.joined_at or member.created_at,
        created_at=member.created_at,
        updated_at=member.updated_at,
        user_email=user.email if user else None,
        user_name=user.full_name if user else None,
        user_avatar_url=user.avatar_url if user else None
    )


# =========================================================================
# Team CRUD Endpoints (S71-T16 to T20)
# =========================================================================

@router.post(
    "",
    response_model=TeamResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Team",
    description="Create a new team. The creator becomes the team owner (SE4H Coach)."
)
async def create_team(
    data: TeamCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new team within an organization.

    - **organization_id**: Parent organization UUID (required)
    - **name**: Team display name (2-255 chars)
    - **slug**: URL-safe identifier (unique per org)
    - **description**: Optional description
    - **settings**: Team settings including SASE config

    The authenticated user becomes the team owner with VCR authority.
    """
    service = TeamsService(db)
    
    try:
        team = await service.create_team(data, current_user.id)
        return team_to_response(team)
    except TeamSlugExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Team with slug '{e.slug}' already exists in this organization"
        )


@router.get(
    "",
    response_model=TeamListResponse,
    summary="List Teams",
    description="List teams the current user is a member of."
)
async def list_teams(
    organization_id: Optional[UUID] = Query(None, description="Filter by organization"),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(20, ge=1, le=100, description="Max results"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List teams where the current user is an active member.

    - **organization_id**: Optional filter by organization
    - **skip**: Pagination offset (default 0)
    - **limit**: Max results per page (1-100, default 20)

    Returns paginated list of teams with member counts.
    """
    service = TeamsService(db)
    
    teams = await service.list_teams(
        user_id=current_user.id,
        organization_id=organization_id,
        skip=skip,
        limit=limit
    )
    
    return TeamListResponse(
        items=[team_to_response(t) for t in teams],
        total=len(teams),  # For proper pagination, should query total count
        page=skip // limit + 1 if limit > 0 else 1,
        page_size=limit,
        has_next=len(teams) == limit
    )


@router.get(
    "/{team_id}",
    response_model=TeamResponse,
    summary="Get Team",
    description="Get team details by ID."
)
async def get_team(
    team_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed information about a specific team.

    Returns team details including:
    - Basic info (name, slug, description)
    - Settings (SASE config, notifications)
    - Member counts (total, human, AI)
    - Project count
    """
    service = TeamsService(db)
    
    team = await service.get_team(team_id)
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Team {team_id} not found"
        )
    
    # Check if user is a member
    is_member = await service.check_permission(team_id, current_user.id, "member")
    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this team"
        )
    
    return team_to_response(team)


@router.patch(
    "/{team_id}",
    response_model=TeamResponse,
    summary="Update Team",
    description="Update team details. Requires admin or owner role."
)
async def update_team(
    team_id: UUID,
    data: TeamUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update team details.

    Requires admin or owner role in the team.

    Updatable fields:
    - **name**: Team display name
    - **slug**: URL-safe identifier (must be unique in org)
    - **description**: Team description
    - **settings**: Team settings including SASE config
    """
    service = TeamsService(db)
    
    try:
        team = await service.update_team(team_id, data, current_user.id)
        return team_to_response(team)
    except TeamNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Team {team_id} not found"
        )
    except PermissionDeniedError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or owner role required to update team"
        )
    except TeamSlugExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Team with slug '{e.slug}' already exists in this organization"
        )


@router.delete(
    "/{team_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Team",
    description="Delete team (soft delete). Requires owner role."
)
async def delete_team(
    team_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a team (soft delete).

    Requires owner role in the team.

    Warning: This will remove all team members' access to the team.
    Projects associated with the team will have team_id set to NULL.
    """
    service = TeamsService(db)
    
    try:
        await service.delete_team(team_id, current_user.id)
    except TeamNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Team {team_id} not found"
        )
    except PermissionDeniedError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Owner role required to delete team"
        )


# =========================================================================
# Team Statistics Endpoint (S71-T21)
# =========================================================================

@router.get(
    "/{team_id}/stats",
    response_model=TeamStatistics,
    summary="Get Team Statistics",
    description="Get team metrics and statistics."
)
async def get_team_statistics(
    team_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed statistics for a team.

    Returns:
    - **total_members**: Total team members
    - **human_members**: SE4H members (humans)
    - **ai_agents**: SE4A members (AI agents)
    - **owners_count**: Number of owners
    - **admins_count**: Number of admins
    - **total_projects**: Total projects
    - **active_projects**: Active projects
    - **agentic_maturity**: SASE maturity level (L0-L3)
    """
    service = TeamsService(db)
    
    # Check if user is a member
    is_member = await service.check_permission(team_id, current_user.id, "member")
    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this team"
        )
    
    try:
        return await service.get_team_statistics(team_id)
    except TeamNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Team {team_id} not found"
        )


# =========================================================================
# Member Management Endpoints (S71-T22 to T25)
# =========================================================================

@router.post(
    "/{team_id}/members",
    response_model=TeamMemberResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add Team Member",
    description="Add a user to the team. Requires admin or owner role."
)
async def add_team_member(
    team_id: UUID,
    data: TeamMemberAdd,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Add a new member to the team.

    Requires admin or owner role.

    - **user_id**: UUID of user to add
    - **role**: Member role (owner, admin, member, ai_agent)
    - **member_type**: human or ai_agent

    SASE Compliance:
    - AI agents cannot be assigned owner or admin roles
    - Human members default to member_type='human'
    """
    # Always set team_id from URL path (Sprint 105 fix)
    data.team_id = team_id
    
    service = TeamsService(db)
    
    try:
        member = await service.add_member(data, current_user.id)
        # Sprint 105: Properly load user relationship to avoid lazy loading hang
        # Use selectinload query instead of refresh() which doesn't load relationships
        member = await db.scalar(
            select(TeamMember)
            .options(selectinload(TeamMember.user))
            .where(TeamMember.id == member.id)
        )
        return member_to_response(member)
    except PermissionDeniedError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or owner role required to add members"
        )
    except UserNotFoundByEmailError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with email '{e.email}' not found. Please check the email address."
        )
    except UserAlreadyMemberError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User is already a member of this team"
        )
    except InvalidRoleError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role '{e.role}' for member_type '{e.member_type}'. "
                   f"AI agents cannot be owner or admin per SASE framework."
        )


@router.get(
    "/{team_id}/members",
    response_model=TeamMemberListResponse,
    summary="List Team Members",
    description="List all members of a team."
)
async def list_team_members(
    team_id: UUID,
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(20, ge=1, le=100, description="Max results"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all members of a team.

    Returns member list with:
    - User info (email, name, avatar)
    - Role (owner, admin, member, ai_agent)
    - Member type (human, ai_agent)
    - SASE role designation (SE4H_Coach, SE4H_Member, SE4A_Executor)
    """
    service = TeamsService(db)
    
    # Check if user is a member
    is_member = await service.check_permission(team_id, current_user.id, "member")
    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this team"
        )
    
    team = await service.get_team(team_id)
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Team {team_id} not found"
        )
    
    # Get active members with pagination
    members = [m for m in team.members if m.deleted_at is None]
    total = len(members)
    paginated = members[skip:skip + limit]
    
    return TeamMemberListResponse(
        items=[member_to_response(m) for m in paginated],
        total=total,
        page=skip // limit + 1 if limit > 0 else 1,
        page_size=limit,
        has_next=skip + limit < total
    )


@router.patch(
    "/{team_id}/members/{user_id}",
    response_model=TeamMemberResponse,
    summary="Update Member Role",
    description="Update a member's role. Requires owner role."
)
async def update_member_role(
    team_id: UUID,
    user_id: UUID,
    data: TeamMemberUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a team member's role.

    Requires owner role.

    - **role**: New role (owner, admin, member, ai_agent)

    SASE Compliance:
    - Cannot change AI agent to owner or admin
    - Only owners can promote to owner
    """
    if not data.role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role is required"
        )
    
    service = TeamsService(db)
    
    try:
        member = await service.update_member_role(
            team_id, user_id, data.role.value, current_user.id
        )
        return member_to_response(member)
    except MemberNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} is not a member of team {team_id}"
        )
    except PermissionDeniedError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Owner role required to change member roles"
        )
    except InvalidRoleError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot assign role '{e.role}' to AI agent. "
                   f"AI agents cannot be owner or admin per SASE framework."
        )


@router.delete(
    "/{team_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove Team Member",
    description="Remove a member from the team. Requires admin or owner role."
)
async def remove_team_member(
    team_id: UUID,
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Remove a member from the team.

    Requires admin or owner role.

    - Admins can remove members but not owners
    - Owners can remove anyone except the last owner
    - Cannot remove the last owner from a team
    """
    service = TeamsService(db)
    
    try:
        await service.remove_member(team_id, user_id, current_user.id)
    except MemberNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} is not a member of team {team_id}"
        )
    except PermissionDeniedError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"{e.required_role.capitalize()} role required for this action"
        )
    except CannotRemoveLastOwnerError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove the last owner from a team. "
                   "Promote another member to owner first."
        )
