"""
=========================================================================
Teams Service - Business Logic for Team Operations
SDLC Orchestrator - Sprint 71 (Teams Backend API)

Version: 1.0.0
Date: January 27, 2026
Status: ACTIVE - Sprint 71 Implementation
Authority: Backend Lead + CTO Approved
Reference: ADR-028-Teams-Feature-Architecture
Reference: SPRINT-71-TEAMS-BACKEND-API.md

Purpose:
- Service layer for team CRUD operations
- Member management with permission validation
- Team statistics and metrics
- SASE-compliant role management

SDLC 5.1.2 SASE Compliance:
- Owner/Admin = SE4H (Agent Coach) - VCR authority
- Member = SE4H/SE4A - Implementation work
- ai_agent = SE4A (Agent Executor) - Autonomous tasks

Zero Mock Policy: Production-ready service with async/await
=========================================================================
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.organization import Organization
from app.models.project import Project
from app.models.team import Team
from app.models.team_member import TeamMember
from app.models.user import User
from app.schemas.team import (
    TeamCreate,
    TeamMemberAdd,
    TeamStatistics,
    TeamUpdate,
)


# =========================================================================
# Custom Exceptions
# =========================================================================

class TeamsServiceError(Exception):
    """Base exception for TeamsService errors."""
    pass


class TeamNotFoundError(TeamsServiceError):
    """Team not found."""
    def __init__(self, team_id: UUID):
        self.team_id = team_id
        super().__init__(f"Team {team_id} not found")


class TeamSlugExistsError(TeamsServiceError):
    """Team slug already exists in organization."""
    def __init__(self, slug: str, organization_id: UUID):
        self.slug = slug
        self.organization_id = organization_id
        super().__init__(
            f"Team with slug '{slug}' already exists in organization {organization_id}"
        )


class UserAlreadyMemberError(TeamsServiceError):
    """User is already a team member."""
    def __init__(self, user_id: UUID, team_id: UUID):
        self.user_id = user_id
        self.team_id = team_id
        super().__init__(f"User {user_id} is already a member of team {team_id}")


class MemberNotFoundError(TeamsServiceError):
    """Team member not found."""
    def __init__(self, user_id: UUID, team_id: UUID):
        self.user_id = user_id
        self.team_id = team_id
        super().__init__(f"User {user_id} is not a member of team {team_id}")


class CannotRemoveLastOwnerError(TeamsServiceError):
    """Cannot remove the last owner from a team."""
    def __init__(self):
        super().__init__("Cannot remove the last owner from team")


class PermissionDeniedError(TeamsServiceError):
    """User does not have required permission."""
    def __init__(self, action: str, required_role: str):
        self.action = action
        self.required_role = required_role
        super().__init__(
            f"Permission denied: '{action}' requires '{required_role}' role"
        )


class InvalidRoleError(TeamsServiceError):
    """Invalid role for member type."""
    def __init__(self, role: str, member_type: str):
        self.role = role
        self.member_type = member_type
        super().__init__(
            f"Invalid role '{role}' for member_type '{member_type}' "
            f"(AI agents cannot be owner/admin per SASE)"
        )


class UserNotFoundByEmailError(TeamsServiceError):
    """User not found by email address."""
    def __init__(self, email: str):
        self.email = email
        super().__init__(f"User with email '{email}' not found")


# =========================================================================
# TeamsService
# =========================================================================

class TeamsService:
    """
    Service layer for team operations.

    Provides business logic for:
    - Team CRUD operations
    - Member management with SASE compliance
    - Permission validation
    - Team statistics and metrics

    All methods are async and use SQLAlchemy AsyncSession.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize TeamsService.

        Args:
            db: Async database session
        """
        self.db = db

    # =========================================================================
    # Team CRUD Operations (S71-T01 to T05)
    # =========================================================================

    async def create_team(
        self,
        data: TeamCreate,
        owner_id: UUID
    ) -> Team:
        """
        Create new team with owner as first member.

        Args:
            data: Team creation data
            owner_id: UUID of user who will be team owner

        Returns:
            Created Team object

        Raises:
            TeamSlugExistsError: If slug already exists in organization

        SASE Compliance:
            - Creator becomes owner (SE4H Agent Coach)
            - Owner has VCR authority for team
        """
        # Check slug uniqueness within organization
        existing = await self.db.scalar(
            select(Team).where(
                Team.organization_id == data.organization_id,
                Team.slug == data.slug,
                Team.deleted_at.is_(None)
            )
        )
        if existing:
            raise TeamSlugExistsError(data.slug, data.organization_id)

        # Create team
        team = Team(
            organization_id=data.organization_id,
            name=data.name,
            slug=data.slug,
            description=data.description,
            settings=data.settings.model_dump() if data.settings else {}
        )
        self.db.add(team)
        await self.db.flush()

        # Add owner as first member (SE4H Coach)
        member = TeamMember(
            team_id=team.id,
            user_id=owner_id,
            role="owner",
            member_type="human"
        )
        self.db.add(member)
        await self.db.commit()
        await self.db.refresh(team)

        return team

    async def get_team(self, team_id: UUID) -> Optional[Team]:
        """
        Get team by ID with members and projects loaded.

        Args:
            team_id: Team UUID

        Returns:
            Team object if found, None otherwise

        Note:
            Uses eager loading for members and projects to avoid N+1 queries.
            Sprint 105: Filter out soft-deleted members at database level.
        """
        return await self.db.scalar(
            select(Team)
            .options(
                # Sprint 105: Only load active members (exclude soft-deleted)
                selectinload(
                    Team.members.and_(TeamMember.deleted_at.is_(None))
                ).selectinload(TeamMember.user),
                selectinload(Team.projects),
                selectinload(Team.organization)
            )
            .where(
                Team.id == team_id,
                Team.deleted_at.is_(None)
            )
        )

    async def list_teams(
        self,
        user_id: UUID,
        organization_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 20
    ) -> list[Team]:
        """
        List teams user is a member of.

        Args:
            user_id: User UUID
            organization_id: Optional filter by organization
            skip: Pagination offset
            limit: Max results (default 20, max 100)

        Returns:
            List of Team objects

        Note:
            Only returns teams where user is an active member.
        """
        query = (
            select(Team)
            .join(TeamMember)
            .where(
                TeamMember.user_id == user_id,
                TeamMember.deleted_at.is_(None),
                Team.deleted_at.is_(None)
            )
            .options(
                # Sprint 105: Only load active members (exclude soft-deleted)
                selectinload(Team.members.and_(TeamMember.deleted_at.is_(None))),
                selectinload(Team.projects)
            )
        )

        if organization_id:
            query = query.where(Team.organization_id == organization_id)

        query = query.offset(skip).limit(min(limit, 100))
        result = await self.db.scalars(query)
        return list(result.unique().all())

    async def update_team(
        self,
        team_id: UUID,
        data: TeamUpdate,
        user_id: UUID
    ) -> Team:
        """
        Update team details (admin/owner only).

        Args:
            team_id: Team UUID
            data: Update data
            user_id: User making the update

        Returns:
            Updated Team object

        Raises:
            TeamNotFoundError: If team not found
            PermissionDeniedError: If user is not admin/owner
        """
        # Get team
        team = await self.get_team(team_id)
        if not team:
            raise TeamNotFoundError(team_id)

        # Check permission
        if not await self.check_permission(team_id, user_id, "admin"):
            raise PermissionDeniedError("update_team", "admin")

        # Update fields
        if data.name is not None:
            team.name = data.name
        if data.slug is not None:
            # Check slug uniqueness
            existing = await self.db.scalar(
                select(Team).where(
                    Team.organization_id == team.organization_id,
                    Team.slug == data.slug,
                    Team.id != team_id,
                    Team.deleted_at.is_(None)
                )
            )
            if existing:
                raise TeamSlugExistsError(data.slug, team.organization_id)
            team.slug = data.slug
        if data.description is not None:
            team.description = data.description
        if data.settings is not None:
            team.settings = data.settings.model_dump()

        team.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(team)

        return team

    async def delete_team(
        self,
        team_id: UUID,
        user_id: UUID
    ) -> bool:
        """
        Delete team (soft delete, owner only).

        Args:
            team_id: Team UUID
            user_id: User requesting deletion

        Returns:
            True if deleted

        Raises:
            TeamNotFoundError: If team not found
            PermissionDeniedError: If user is not owner
        """
        # Get team
        team = await self.get_team(team_id)
        if not team:
            raise TeamNotFoundError(team_id)

        # Check permission (owner only)
        if not await self.check_permission(team_id, user_id, "owner"):
            raise PermissionDeniedError("delete_team", "owner")

        # Soft delete
        team.deleted_at = datetime.utcnow()
        await self.db.commit()

        return True

    # =========================================================================
    # Member Management (S71-T06 to T08)
    # =========================================================================

    async def add_member(
        self,
        data: TeamMemberAdd,
        requester_id: UUID
    ) -> TeamMember:
        """
        Add user to team with specified role.

        Args:
            data: Member add data (team_id, user_id/email, role, member_type)
            requester_id: User adding the member

        Returns:
            Created TeamMember object

        Raises:
            TeamNotFoundError: If team not found
            UserAlreadyMemberError: If user is already a member
            PermissionDeniedError: If requester is not admin/owner
            InvalidRoleError: If AI agent assigned owner/admin role
            UserNotFoundByEmailError: If email provided but user not found

        SASE Compliance:
            - Validates AI agents cannot be owner/admin (CTO R1/R2)
            - Human members default to member_type='human'

        Sprint 105 Enhancement:
            - Accepts user_id (UUID) OR email (string)
            - If email provided, looks up user by email
        """
        # Check permission
        if not await self.check_permission(data.team_id, requester_id, "admin"):
            raise PermissionDeniedError("add_member", "admin")

        # Sprint 105: Resolve user_id from email if email provided
        user_id = data.user_id
        if not user_id and data.email:
            # Lookup user by email
            user = await self.db.scalar(
                select(User).where(
                    func.lower(User.email) == func.lower(data.email.strip()),
                    User.deleted_at.is_(None)
                )
            )
            if not user:
                raise UserNotFoundByEmailError(data.email)
            user_id = user.id

        # Check if already an ACTIVE member
        existing = await self.db.scalar(
            select(TeamMember).where(
                TeamMember.team_id == data.team_id,
                TeamMember.user_id == user_id,
                TeamMember.deleted_at.is_(None)
            )
        )
        if existing:
            raise UserAlreadyMemberError(user_id, data.team_id)

        # Sprint 105: Clean up any soft-deleted records (hard delete policy)
        # This handles the case where a member was previously soft-deleted
        soft_deleted = await self.db.scalar(
            select(TeamMember).where(
                TeamMember.team_id == data.team_id,
                TeamMember.user_id == user_id,
                TeamMember.deleted_at.isnot(None)
            )
        )
        if soft_deleted:
            await self.db.delete(soft_deleted)
            await self.db.flush()

        # SASE Validation: AI agents cannot be owner/admin
        if data.member_type == "ai_agent" and data.role in ("owner", "admin"):
            raise InvalidRoleError(data.role, data.member_type)

        # Create member
        member = TeamMember(
            team_id=data.team_id,
            user_id=user_id,
            role=data.role,
            member_type=data.member_type
        )
        self.db.add(member)

        try:
            await self.db.commit()
        except IntegrityError as e:
            await self.db.rollback()
            # Handle unique constraint violation (team_members_unique)
            if "team_members_unique" in str(e):
                raise UserAlreadyMemberError(user_id, data.team_id)
            # Re-raise other integrity errors
            raise

        await self.db.refresh(member)

        return member

    async def remove_member(
        self,
        team_id: UUID,
        user_id: UUID,
        requester_id: UUID
    ) -> bool:
        """
        Remove user from team.

        Args:
            team_id: Team UUID
            user_id: User to remove
            requester_id: User requesting removal

        Returns:
            True if removed

        Raises:
            MemberNotFoundError: If member not found
            CannotRemoveLastOwnerError: If trying to remove last owner
            PermissionDeniedError: If requester is not admin/owner

        Note:
            Admins can remove members but not owners.
            Owners can remove anyone except last owner.
        """
        # Check permission
        if not await self.check_permission(team_id, requester_id, "admin"):
            raise PermissionDeniedError("remove_member", "admin")

        # Get member
        member = await self.db.scalar(
            select(TeamMember).where(
                TeamMember.team_id == team_id,
                TeamMember.user_id == user_id,
                TeamMember.deleted_at.is_(None)
            )
        )
        if not member:
            raise MemberNotFoundError(user_id, team_id)

        # Check if last owner
        if member.role == "owner":
            owner_count = await self.db.scalar(
                select(func.count())
                .select_from(TeamMember)
                .where(
                    TeamMember.team_id == team_id,
                    TeamMember.role == "owner",
                    TeamMember.deleted_at.is_(None)
                )
            )
            if owner_count <= 1:
                raise CannotRemoveLastOwnerError()

            # Check if requester is owner (only owner can remove owner)
            if not await self.check_permission(team_id, requester_id, "owner"):
                raise PermissionDeniedError("remove_owner", "owner")

        # Hard delete - team member removal is permanent (not soft delete)
        # Only user deletion uses soft delete, team membership is hard deleted
        await self.db.delete(member)
        await self.db.commit()

        return True

    async def update_member_role(
        self,
        team_id: UUID,
        user_id: UUID,
        new_role: str,
        requester_id: UUID
    ) -> TeamMember:
        """
        Update member role (admin or owner).

        Args:
            team_id: Team UUID
            user_id: User whose role to update
            new_role: New role (owner, admin, member, ai_agent)
            requester_id: User requesting update

        Returns:
            Updated TeamMember object

        Raises:
            MemberNotFoundError: If member not found
            PermissionDeniedError: If requester lacks permission
            InvalidRoleError: If AI agent assigned owner/admin role

        Permission Logic (Sprint 152):
            - Admin can change roles to: member, admin
            - Only Owner can promote to owner
            - Cannot demote the last owner
        """
        # Check if requester is at least admin
        is_admin = await self.check_permission(team_id, requester_id, "admin")
        is_owner = await self.check_permission(team_id, requester_id, "owner")

        if not is_admin:
            raise PermissionDeniedError("update_member_role", "admin")

        # Only owner can promote to owner
        if new_role == "owner" and not is_owner:
            raise PermissionDeniedError("promote_to_owner", "owner")

        # Get member with user eagerly loaded (needed for member_to_response)
        member = await self.db.scalar(
            select(TeamMember)
            .options(selectinload(TeamMember.user))
            .where(
                TeamMember.team_id == team_id,
                TeamMember.user_id == user_id,
                TeamMember.deleted_at.is_(None)
            )
        )
        if not member:
            raise MemberNotFoundError(user_id, team_id)

        # SASE Validation: AI agents cannot be owner/admin
        if member.member_type == "ai_agent" and new_role in ("owner", "admin"):
            raise InvalidRoleError(new_role, member.member_type)

        # Prevent demoting the last owner
        if member.role == "owner" and new_role != "owner":
            owner_count = await self.db.scalar(
                select(func.count())
                .select_from(TeamMember)
                .where(
                    TeamMember.team_id == team_id,
                    TeamMember.role == "owner",
                    TeamMember.deleted_at.is_(None)
                )
            )
            if owner_count <= 1:
                raise PermissionDeniedError("demote_last_owner", "owner")

        # Update role
        member.role = new_role
        member.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(member, attribute_names=["user"])

        return member

    # =========================================================================
    # Statistics & Metrics (S71-T09)
    # =========================================================================

    async def get_team_statistics(self, team_id: UUID) -> TeamStatistics:
        """
        Get team metrics and statistics.

        Args:
            team_id: Team UUID

        Returns:
            TeamStatistics object

        Raises:
            TeamNotFoundError: If team not found

        Statistics include:
            - Total members, human members, AI agents
            - Owner/admin counts
            - Total projects, active projects
            - Agentic maturity level (from team settings)
        """
        team = await self.get_team(team_id)
        if not team:
            raise TeamNotFoundError(team_id)

        # Count members by type - filter out soft-deleted members (Sprint 105 fix)
        members = [m for m in team.members if m.deleted_at is None]
        total_members = len(members)
        human_members = sum(1 for m in members if m.member_type == "human")
        ai_agents = sum(1 for m in members if m.member_type == "ai_agent")
        owners_count = sum(1 for m in members if m.role == "owner")
        admins_count = sum(1 for m in members if m.role == "admin")

        # Count projects
        project_count = await self.db.scalar(
            select(func.count())
            .select_from(Project)
            .where(
                Project.team_id == team_id,
                Project.deleted_at.is_(None)
            )
        )

        active_projects = await self.db.scalar(
            select(func.count())
            .select_from(Project)
            .where(
                Project.team_id == team_id,
                Project.is_active == True,
                Project.deleted_at.is_(None)
            )
        )

        # Get agentic maturity from team settings
        agentic_maturity = team.settings.get("agentic_maturity", "L0")

        return TeamStatistics(
            team_id=team.id,
            team_name=team.name,
            total_members=total_members,
            human_members=human_members,
            ai_agents=ai_agents,
            owners_count=owners_count,
            admins_count=admins_count,
            total_projects=project_count or 0,
            active_projects=active_projects or 0,
            agentic_maturity=agentic_maturity
        )

    # =========================================================================
    # Permission Checks (S71-T10)
    # =========================================================================

    async def check_permission(
        self,
        team_id: UUID,
        user_id: UUID,
        required_role: str = "member"
    ) -> bool:
        """
        Check if user has required role in team.

        Args:
            team_id: Team UUID
            user_id: User UUID
            required_role: Required role (owner, admin, member)

        Returns:
            True if user has required role or higher

        Role Hierarchy:
            owner (3) > admin (2) > member (1) >= ai_agent (1)

        SASE Note:
            ai_agent role is equivalent to member in hierarchy
            but has different permissions for VCR/MRP approval
        """
        member = await self.db.scalar(
            select(TeamMember).where(
                TeamMember.team_id == team_id,
                TeamMember.user_id == user_id,
                TeamMember.deleted_at.is_(None)
            )
        )
        if not member:
            return False

        # Role hierarchy
        role_hierarchy = {
            "owner": 3,
            "admin": 2,
            "member": 1,
            "ai_agent": 1
        }

        user_level = role_hierarchy.get(member.role, 0)
        required_level = role_hierarchy.get(required_role, 0)

        return user_level >= required_level

    async def get_member_role(
        self,
        team_id: UUID,
        user_id: UUID
    ) -> Optional[str]:
        """
        Get user's role in team.

        Args:
            team_id: Team UUID
            user_id: User UUID

        Returns:
            Role string if member, None if not a member
        """
        member = await self.db.scalar(
            select(TeamMember).where(
                TeamMember.team_id == team_id,
                TeamMember.user_id == user_id,
                TeamMember.deleted_at.is_(None)
            )
        )
        return member.role if member else None
