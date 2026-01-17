# Teams API Specification
## REST API Endpoints for Organizations, Teams, and Members

**Version**: 1.0.0
**Date**: January 17, 2026
**Status**: APPROVED
**Author**: Backend Lead
**Reference**: ADR-028-Teams-Feature-Architecture
**Sprint**: Sprint 71 (Feb 3 - Feb 17, 2026)

---

## 1. Overview

This specification defines the REST API endpoints for team management in SDLC Orchestrator. It covers Organizations, Teams, and Team Members APIs.

### Endpoint Summary

| Group | Endpoints | Auth Required |
|-------|-----------|---------------|
| Organizations | 3 | Yes |
| Teams | 5 | Yes |
| Team Members | 4 | Yes |
| **Total** | **12** | |

### Base URL

```
Production: https://api.sdlc.nhatquangholding.com/api/v1
Development: http://localhost:8000/api/v1
```

---

## 2. Organizations API

### 2.1 Create Organization

Creates a new organization. Typically called during user signup.

```http
POST /organizations
```

**Request Body:**

```json
{
  "name": "Acme Corporation",
  "slug": "acme-corp",
  "plan": "free"
}
```

**Response (201 Created):**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Acme Corporation",
  "slug": "acme-corp",
  "plan": "free",
  "settings": {},
  "created_at": "2026-01-17T10:30:00Z",
  "updated_at": "2026-01-17T10:30:00Z"
}
```

**Error Responses:**

| Status | Condition | Body |
|--------|-----------|------|
| 400 | Invalid request | `{"detail": "Slug must contain only lowercase letters, numbers, and hyphens"}` |
| 409 | Slug exists | `{"detail": "Organization slug already exists"}` |

**Authorization:** Authenticated user. User becomes organization owner.

---

### 2.2 Get Organization

Returns organization details.

```http
GET /organizations/{organization_id}
```

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `organization_id` | UUID | Organization ID |

**Response (200 OK):**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Acme Corporation",
  "slug": "acme-corp",
  "plan": "pro",
  "settings": {
    "require_mfa": true,
    "allowed_domains": ["acme.com"]
  },
  "created_at": "2026-01-17T10:30:00Z",
  "updated_at": "2026-01-17T10:30:00Z",
  "teams_count": 5,
  "users_count": 25
}
```

**Error Responses:**

| Status | Condition | Body |
|--------|-----------|------|
| 403 | Not a member | `{"detail": "Access denied"}` |
| 404 | Not found | `{"detail": "Organization not found"}` |

**Authorization:** User must belong to the organization.

---

### 2.3 Update Organization

Updates organization details.

```http
PATCH /organizations/{organization_id}
```

**Request Body:**

```json
{
  "name": "Acme Corp International",
  "plan": "enterprise",
  "settings": {
    "require_mfa": true,
    "allowed_domains": ["acme.com", "acme.io"]
  }
}
```

**Response (200 OK):**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Acme Corp International",
  "slug": "acme-corp",
  "plan": "enterprise",
  "settings": {
    "require_mfa": true,
    "allowed_domains": ["acme.com", "acme.io"]
  },
  "created_at": "2026-01-17T10:30:00Z",
  "updated_at": "2026-01-18T14:20:00Z"
}
```

**Error Responses:**

| Status | Condition | Body |
|--------|-----------|------|
| 400 | Invalid request | `{"detail": "Invalid plan"}` |
| 403 | Not owner | `{"detail": "Only organization owner can update"}` |
| 404 | Not found | `{"detail": "Organization not found"}` |

**Authorization:** Organization owner only.

---

## 3. Teams API

### 3.1 List Teams

Returns teams the current user has access to.

```http
GET /teams
```

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `organization_id` | UUID | - | Filter by organization (optional) |
| `skip` | int | 0 | Pagination offset |
| `limit` | int | 20 | Pagination limit (max 100) |

**Response (200 OK):**

```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "organization_id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Backend Team",
      "slug": "backend",
      "description": "Backend development team",
      "settings": {},
      "created_at": "2026-01-17T10:30:00Z",
      "updated_at": "2026-01-17T10:30:00Z",
      "members_count": 5,
      "projects_count": 3
    }
  ],
  "total": 1,
  "skip": 0,
  "limit": 20
}
```

**Authorization:** Returns only teams where user is a member.

---

### 3.2 Create Team

Creates a new team. Creator becomes owner.

```http
POST /teams
```

**Request Body:**

```json
{
  "organization_id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Frontend Team",
  "slug": "frontend",
  "description": "Frontend development team"
}
```

**Response (201 Created):**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440002",
  "organization_id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Frontend Team",
  "slug": "frontend",
  "description": "Frontend development team",
  "settings": {},
  "created_at": "2026-01-17T11:00:00Z",
  "updated_at": "2026-01-17T11:00:00Z",
  "members_count": 1,
  "projects_count": 0
}
```

**Error Responses:**

| Status | Condition | Body |
|--------|-----------|------|
| 400 | Invalid request | `{"detail": "Slug must contain only lowercase letters, numbers, and hyphens"}` |
| 403 | Not org member | `{"detail": "Must be organization member to create team"}` |
| 409 | Slug exists | `{"detail": "Team slug already exists in this organization"}` |

**Authorization:** User must belong to the organization.

**Side Effects:** Creator is added as team owner automatically.

---

### 3.3 Get Team

Returns team details with members and projects.

```http
GET /teams/{team_id}
```

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `team_id` | UUID | Team ID |

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `include_members` | bool | false | Include member list |
| `include_projects` | bool | false | Include project list |

**Response (200 OK):**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "organization_id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Backend Team",
  "slug": "backend",
  "description": "Backend development team",
  "settings": {
    "notification_channel": "slack",
    "webhook_url": "https://hooks.slack.com/..."
  },
  "created_at": "2026-01-17T10:30:00Z",
  "updated_at": "2026-01-17T10:30:00Z",
  "members_count": 5,
  "projects_count": 3,
  "members": [
    {
      "id": "mem-uuid-1",
      "user_id": "user-uuid-1",
      "role": "owner",
      "joined_at": "2026-01-17T10:30:00Z",
      "user": {
        "id": "user-uuid-1",
        "email": "john@acme.com",
        "full_name": "John Doe"
      }
    }
  ],
  "projects": [
    {
      "id": "proj-uuid-1",
      "name": "API Gateway",
      "status": "active"
    }
  ]
}
```

**Error Responses:**

| Status | Condition | Body |
|--------|-----------|------|
| 403 | Not a member | `{"detail": "Access denied"}` |
| 404 | Not found | `{"detail": "Team not found"}` |

**Authorization:** User must be a team member.

---

### 3.4 Update Team

Updates team details.

```http
PATCH /teams/{team_id}
```

**Request Body:**

```json
{
  "name": "Backend Engineering",
  "description": "Core backend services team",
  "settings": {
    "notification_channel": "email"
  }
}
```

**Response (200 OK):**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "organization_id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Backend Engineering",
  "slug": "backend",
  "description": "Core backend services team",
  "settings": {
    "notification_channel": "email"
  },
  "created_at": "2026-01-17T10:30:00Z",
  "updated_at": "2026-01-18T09:00:00Z"
}
```

**Error Responses:**

| Status | Condition | Body |
|--------|-----------|------|
| 400 | Invalid request | `{"detail": "Invalid settings format"}` |
| 403 | Not admin+ | `{"detail": "Admin or owner required"}` |
| 404 | Not found | `{"detail": "Team not found"}` |

**Authorization:** Team admin or owner.

---

### 3.5 Delete Team

Deletes a team and all memberships. Projects are NOT deleted (orphaned to org default team).

```http
DELETE /teams/{team_id}
```

**Response (204 No Content):**

No body.

**Error Responses:**

| Status | Condition | Body |
|--------|-----------|------|
| 403 | Not owner | `{"detail": "Only team owner can delete"}` |
| 404 | Not found | `{"detail": "Team not found"}` |
| 409 | Has projects | `{"detail": "Cannot delete team with active projects. Reassign projects first."}` |

**Authorization:** Team owner only.

**Side Effects:**
- All team memberships deleted (CASCADE)
- Projects reassigned to organization's default team

---

## 4. Team Members API

### 4.1 List Team Members

Returns all members of a team.

```http
GET /teams/{team_id}/members
```

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `role` | string | - | Filter by role (owner/admin/member/ai_agent) |
| `member_type` | string | - | Filter by member type (human/ai_agent) |
| `skip` | int | 0 | Pagination offset |
| `limit` | int | 50 | Pagination limit (max 100) |

**Response (200 OK):**

```json
{
  "items": [
    {
      "id": "mem-uuid-1",
      "team_id": "550e8400-e29b-41d4-a716-446655440001",
      "user_id": "user-uuid-1",
      "role": "owner",
      "member_type": "human",
      "is_coach": true,
      "is_ai_agent": false,
      "joined_at": "2026-01-17T10:30:00Z",
      "user": {
        "id": "user-uuid-1",
        "email": "john@acme.com",
        "full_name": "John Doe",
        "avatar_url": null
      }
    },
    {
      "id": "mem-uuid-2",
      "team_id": "550e8400-e29b-41d4-a716-446655440001",
      "user_id": "user-uuid-2",
      "role": "member",
      "member_type": "human",
      "is_coach": false,
      "is_ai_agent": false,
      "joined_at": "2026-01-18T14:00:00Z",
      "user": {
        "id": "user-uuid-2",
        "email": "jane@acme.com",
        "full_name": "Jane Smith",
        "avatar_url": "https://..."
      }
    },
    {
      "id": "mem-uuid-3",
      "team_id": "550e8400-e29b-41d4-a716-446655440001",
      "user_id": "agent-uuid-1",
      "role": "ai_agent",
      "member_type": "ai_agent",
      "is_coach": false,
      "is_ai_agent": true,
      "joined_at": "2026-01-19T09:00:00Z",
      "user": {
        "id": "agent-uuid-1",
        "email": "claude-agent@sdlc.ai",
        "full_name": "Claude Code Agent"
      }
    }
  ],
  "total": 3,
  "skip": 0,
  "limit": 50
}
```

**Authorization:** Team member (any role).

---

### 4.2 Add Team Member

Adds a user (human or AI agent) to a team.

```http
POST /teams/{team_id}/members
```

**Request Body (Human):**

```json
{
  "user_id": "user-uuid-3",
  "role": "member",
  "member_type": "human"
}
```

**Request Body (AI Agent - CTO R1/R2):**

```json
{
  "user_id": "agent-uuid-1",
  "role": "ai_agent",
  "member_type": "ai_agent"
}
```

**Response (201 Created):**

```json
{
  "id": "mem-uuid-3",
  "team_id": "550e8400-e29b-41d4-a716-446655440001",
  "user_id": "user-uuid-3",
  "role": "member",
  "member_type": "human",
  "is_coach": false,
  "is_ai_agent": false,
  "joined_at": "2026-01-19T10:00:00Z",
  "user": {
    "id": "user-uuid-3",
    "email": "bob@acme.com",
    "full_name": "Bob Wilson"
  }
}
```

**Error Responses:**

| Status | Condition | Body |
|--------|-----------|------|
| 400 | Invalid role | `{"detail": "Role must be owner, admin, member, or ai_agent"}` |
| 400 | Invalid member_type | `{"detail": "Member type must be human or ai_agent"}` |
| 400 | AI agent as owner/admin | `{"detail": "AI agents cannot have owner or admin roles per SASE principles"}` |
| 403 | Not admin+ | `{"detail": "Admin or owner required to add members"}` |
| 404 | User not found | `{"detail": "User not found"}` |
| 409 | Already member | `{"detail": "User is already a member of this team"}` |
| 422 | Different org | `{"detail": "User must belong to the same organization"}` |

**Authorization:** Team admin or owner.

**Validation:**
- User must belong to the same organization as the team
- **SASE Compliance**: AI agents (member_type=ai_agent) cannot be assigned owner or admin roles

---

### 4.3 Update Member Role

Changes a member's role in the team.

```http
PATCH /teams/{team_id}/members/{user_id}
```

**Request Body:**

```json
{
  "role": "admin"
}
```

**Response (200 OK):**

```json
{
  "id": "mem-uuid-2",
  "team_id": "550e8400-e29b-41d4-a716-446655440001",
  "user_id": "user-uuid-2",
  "role": "admin",
  "member_type": "human",
  "is_coach": true,
  "is_ai_agent": false,
  "joined_at": "2026-01-18T14:00:00Z"
}
```

**Error Responses:**

| Status | Condition | Body |
|--------|-----------|------|
| 400 | Invalid role | `{"detail": "Role must be owner, admin, member, or ai_agent"}` |
| 400 | AI agent to owner/admin | `{"detail": "AI agents cannot have owner or admin roles per SASE principles"}` |
| 403 | Not owner | `{"detail": "Only team owner can change roles"}` |
| 404 | Not found | `{"detail": "Member not found"}` |
| 422 | Self-demote | `{"detail": "Cannot demote yourself. Transfer ownership first."}` |

**Authorization:** Team owner only.

**Special Rules:**
- Owner cannot demote themselves (must transfer ownership first)
- Promoting to owner transfers ownership (previous owner becomes admin)
- **SASE Compliance**: AI agents cannot be promoted to owner or admin roles

---

### 4.4 Remove Team Member

Removes a user from the team.

```http
DELETE /teams/{team_id}/members/{user_id}
```

**Response (204 No Content):**

No body.

**Error Responses:**

| Status | Condition | Body |
|--------|-----------|------|
| 403 | Not admin+ | `{"detail": "Admin or owner required to remove members"}` |
| 403 | Remove owner | `{"detail": "Cannot remove team owner. Transfer ownership first."}` |
| 404 | Not found | `{"detail": "Member not found"}` |

**Authorization:** Team admin or owner. Self-removal allowed.

**Special Rules:**
- Cannot remove the team owner
- Members can remove themselves (leave team)

---

## 5. Team Statistics API

### 5.1 Get Team Statistics

Returns aggregated metrics for a team.

```http
GET /teams/{team_id}/statistics
```

**Response (200 OK):**

```json
{
  "team_id": "550e8400-e29b-41d4-a716-446655440001",
  "members_count": 5,
  "projects_count": 3,
  "gates_total": 45,
  "gates_passed": 38,
  "gates_failed": 5,
  "gates_pending": 2,
  "compliance_rate": 0.84,
  "evidence_count": 156,
  "last_activity": "2026-01-19T14:30:00Z"
}
```

**Authorization:** Team member (any role).

---

## 6. Service Implementation

### TeamsService Class

```python
# backend/app/services/teams_service.py
from uuid import UUID
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.models import Organization, Team, TeamMember, User, Project
from app.schemas.team import TeamCreate, TeamUpdate, TeamMemberAdd
from app.core.exceptions import NotFoundError, ForbiddenError, ConflictError
import logging

logger = logging.getLogger(__name__)


class TeamsService:
    """
    Service layer for team management operations.

    Handles all business logic for organizations, teams, and members.
    Enforces authorization rules and data integrity.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    # ==================== Organization Methods ====================

    async def create_organization(
        self,
        name: str,
        slug: str,
        owner_id: UUID,
        plan: str = "free"
    ) -> Organization:
        """
        Create a new organization with the user as owner.

        Args:
            name: Organization display name
            slug: URL-safe unique identifier
            owner_id: User ID who will own this organization
            plan: Subscription plan (free/pro/enterprise)

        Returns:
            Created Organization

        Raises:
            ConflictError: Slug already exists
        """
        # Check slug uniqueness
        existing = await self.db.execute(
            select(Organization).where(Organization.slug == slug)
        )
        if existing.scalar_one_or_none():
            raise ConflictError("Organization slug already exists")

        org = Organization(name=name, slug=slug, plan=plan)
        self.db.add(org)
        await self.db.flush()

        # Update user's organization_id
        user = await self.db.get(User, owner_id)
        if user:
            user.organization_id = org.id

        await self.db.commit()
        await self.db.refresh(org)

        logger.info(f"Created organization: {org.id} ({org.slug})")
        return org

    async def get_organization(self, org_id: UUID) -> Optional[Organization]:
        """Get organization by ID."""
        return await self.db.get(Organization, org_id)

    async def update_organization(
        self,
        org_id: UUID,
        user_id: UUID,
        data: dict
    ) -> Organization:
        """
        Update organization details.

        Args:
            org_id: Organization ID
            user_id: User performing the update (must be owner)
            data: Fields to update

        Returns:
            Updated Organization

        Raises:
            NotFoundError: Organization not found
            ForbiddenError: User is not organization owner
        """
        org = await self.get_organization(org_id)
        if not org:
            raise NotFoundError("Organization not found")

        # Authorization: Check if user is org owner (first user with this org_id)
        # In production, you'd have an explicit owner field
        user = await self.db.get(User, user_id)
        if not user or user.organization_id != org_id:
            raise ForbiddenError("Only organization owner can update")

        # Update fields
        for key, value in data.items():
            if hasattr(org, key) and value is not None:
                setattr(org, key, value)

        await self.db.commit()
        await self.db.refresh(org)
        return org

    # ==================== Team Methods ====================

    async def list_teams(
        self,
        user_id: UUID,
        organization_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 20
    ) -> tuple[list[Team], int]:
        """
        List teams the user is a member of.

        Args:
            user_id: Current user ID
            organization_id: Filter by organization (optional)
            skip: Pagination offset
            limit: Pagination limit

        Returns:
            Tuple of (teams list, total count)
        """
        # Base query: teams where user is member
        query = (
            select(Team)
            .join(TeamMember)
            .where(TeamMember.user_id == user_id)
        )

        if organization_id:
            query = query.where(Team.organization_id == organization_id)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        # Get paginated results
        query = query.offset(skip).limit(limit).order_by(Team.created_at.desc())
        result = await self.db.execute(query)
        teams = list(result.scalars().all())

        return teams, total

    async def create_team(
        self,
        organization_id: UUID,
        name: str,
        slug: str,
        owner_id: UUID,
        description: Optional[str] = None
    ) -> Team:
        """
        Create a new team with the user as owner.

        Args:
            organization_id: Parent organization ID
            name: Team display name
            slug: URL-safe identifier (unique per org)
            owner_id: User ID who will own this team
            description: Optional team description

        Returns:
            Created Team

        Raises:
            NotFoundError: Organization not found
            ForbiddenError: User not in organization
            ConflictError: Slug already exists in organization
        """
        # Verify organization exists
        org = await self.get_organization(organization_id)
        if not org:
            raise NotFoundError("Organization not found")

        # Verify user belongs to organization
        user = await self.db.get(User, owner_id)
        if not user or user.organization_id != organization_id:
            raise ForbiddenError("Must be organization member to create team")

        # Check slug uniqueness within organization
        existing = await self.db.execute(
            select(Team).where(
                Team.organization_id == organization_id,
                Team.slug == slug
            )
        )
        if existing.scalar_one_or_none():
            raise ConflictError("Team slug already exists in this organization")

        # Create team
        team = Team(
            organization_id=organization_id,
            name=name,
            slug=slug,
            description=description
        )
        self.db.add(team)
        await self.db.flush()

        # Add creator as owner
        member = TeamMember(
            team_id=team.id,
            user_id=owner_id,
            role="owner"
        )
        self.db.add(member)

        await self.db.commit()
        await self.db.refresh(team)

        logger.info(f"Created team: {team.id} ({team.slug}) in org {organization_id}")
        return team

    async def get_team(
        self,
        team_id: UUID,
        include_members: bool = False,
        include_projects: bool = False
    ) -> Optional[Team]:
        """
        Get team by ID with optional eager loading.

        Args:
            team_id: Team ID
            include_members: Load members relationship
            include_projects: Load projects relationship

        Returns:
            Team or None
        """
        query = select(Team).where(Team.id == team_id)

        if include_members:
            query = query.options(
                selectinload(Team.members).selectinload(TeamMember.user)
            )
        if include_projects:
            query = query.options(selectinload(Team.projects))

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def update_team(
        self,
        team_id: UUID,
        user_id: UUID,
        data: dict
    ) -> Team:
        """
        Update team details.

        Args:
            team_id: Team ID
            user_id: User performing the update
            data: Fields to update

        Returns:
            Updated Team

        Raises:
            NotFoundError: Team not found
            ForbiddenError: User is not admin or owner
        """
        team = await self.get_team(team_id)
        if not team:
            raise NotFoundError("Team not found")

        # Authorization: Check if user is admin or owner
        await self._require_team_role(team_id, user_id, ["admin", "owner"])

        # Update fields
        for key, value in data.items():
            if hasattr(team, key) and value is not None:
                setattr(team, key, value)

        await self.db.commit()
        await self.db.refresh(team)
        return team

    async def delete_team(self, team_id: UUID, user_id: UUID) -> bool:
        """
        Delete a team.

        Args:
            team_id: Team ID
            user_id: User performing the deletion (must be owner)

        Returns:
            True if deleted

        Raises:
            NotFoundError: Team not found
            ForbiddenError: User is not owner
            ConflictError: Team has active projects
        """
        team = await self.get_team(team_id, include_projects=True)
        if not team:
            raise NotFoundError("Team not found")

        # Authorization: Only owner can delete
        await self._require_team_role(team_id, user_id, ["owner"])

        # Check for active projects
        if team.projects:
            raise ConflictError(
                "Cannot delete team with active projects. Reassign projects first."
            )

        await self.db.delete(team)
        await self.db.commit()

        logger.info(f"Deleted team: {team_id}")
        return True

    # ==================== Team Member Methods ====================

    async def list_members(
        self,
        team_id: UUID,
        role: Optional[str] = None,
        skip: int = 0,
        limit: int = 50
    ) -> tuple[list[TeamMember], int]:
        """
        List team members with pagination.

        Args:
            team_id: Team ID
            role: Filter by role (optional)
            skip: Pagination offset
            limit: Pagination limit

        Returns:
            Tuple of (members list, total count)
        """
        query = (
            select(TeamMember)
            .where(TeamMember.team_id == team_id)
            .options(selectinload(TeamMember.user))
        )

        if role:
            query = query.where(TeamMember.role == role)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        # Get paginated results
        query = query.offset(skip).limit(limit).order_by(TeamMember.joined_at)
        result = await self.db.execute(query)
        members = list(result.scalars().all())

        return members, total

    async def add_member(
        self,
        team_id: UUID,
        user_id: UUID,
        added_by: UUID,
        role: str = "member"
    ) -> TeamMember:
        """
        Add a user to a team.

        Args:
            team_id: Team ID
            user_id: User to add
            added_by: User performing the action
            role: Role to assign (default: member)

        Returns:
            Created TeamMember

        Raises:
            NotFoundError: Team or user not found
            ForbiddenError: Actor not admin/owner
            ConflictError: User already a member
            ValueError: User not in same organization
        """
        team = await self.get_team(team_id)
        if not team:
            raise NotFoundError("Team not found")

        # Authorization: Admin or owner required
        await self._require_team_role(team_id, added_by, ["admin", "owner"])

        # Get user to add
        user = await self.db.get(User, user_id)
        if not user:
            raise NotFoundError("User not found")

        # Verify same organization
        if user.organization_id != team.organization_id:
            raise ValueError("User must belong to the same organization")

        # Check not already a member
        existing = await self.db.execute(
            select(TeamMember).where(
                TeamMember.team_id == team_id,
                TeamMember.user_id == user_id
            )
        )
        if existing.scalar_one_or_none():
            raise ConflictError("User is already a member of this team")

        # Create membership
        member = TeamMember(team_id=team_id, user_id=user_id, role=role)
        self.db.add(member)
        await self.db.commit()
        await self.db.refresh(member)

        logger.info(f"Added member {user_id} to team {team_id} as {role}")
        return member

    async def update_member_role(
        self,
        team_id: UUID,
        user_id: UUID,
        updated_by: UUID,
        new_role: str
    ) -> TeamMember:
        """
        Update a member's role in the team.

        Args:
            team_id: Team ID
            user_id: Member user ID
            updated_by: User performing the action (must be owner)
            new_role: New role to assign

        Returns:
            Updated TeamMember

        Raises:
            NotFoundError: Member not found
            ForbiddenError: Actor not owner
            ValueError: Cannot demote self
        """
        # Authorization: Only owner can change roles
        await self._require_team_role(team_id, updated_by, ["owner"])

        # Get membership
        result = await self.db.execute(
            select(TeamMember).where(
                TeamMember.team_id == team_id,
                TeamMember.user_id == user_id
            )
        )
        member = result.scalar_one_or_none()
        if not member:
            raise NotFoundError("Member not found")

        # Cannot demote self
        if user_id == updated_by and new_role != "owner":
            raise ValueError("Cannot demote yourself. Transfer ownership first.")

        # If promoting to owner, demote current owner
        if new_role == "owner" and member.role != "owner":
            current_owner = await self.db.execute(
                select(TeamMember).where(
                    TeamMember.team_id == team_id,
                    TeamMember.role == "owner"
                )
            )
            current = current_owner.scalar_one_or_none()
            if current:
                current.role = "admin"

        member.role = new_role
        await self.db.commit()
        await self.db.refresh(member)

        logger.info(f"Updated member {user_id} role to {new_role} in team {team_id}")
        return member

    async def remove_member(
        self,
        team_id: UUID,
        user_id: UUID,
        removed_by: UUID
    ) -> bool:
        """
        Remove a user from a team.

        Args:
            team_id: Team ID
            user_id: User to remove
            removed_by: User performing the action

        Returns:
            True if removed

        Raises:
            NotFoundError: Member not found
            ForbiddenError: Cannot remove owner, or actor not authorized
        """
        # Get membership
        result = await self.db.execute(
            select(TeamMember).where(
                TeamMember.team_id == team_id,
                TeamMember.user_id == user_id
            )
        )
        member = result.scalar_one_or_none()
        if not member:
            raise NotFoundError("Member not found")

        # Cannot remove owner
        if member.role == "owner":
            raise ForbiddenError(
                "Cannot remove team owner. Transfer ownership first."
            )

        # Authorization: Admin/owner can remove others, anyone can remove self
        if user_id != removed_by:
            await self._require_team_role(team_id, removed_by, ["admin", "owner"])

        await self.db.delete(member)
        await self.db.commit()

        logger.info(f"Removed member {user_id} from team {team_id}")
        return True

    # ==================== Helper Methods ====================

    async def _require_team_role(
        self,
        team_id: UUID,
        user_id: UUID,
        allowed_roles: list[str]
    ) -> TeamMember:
        """
        Check if user has required role in team.

        Args:
            team_id: Team ID
            user_id: User ID
            allowed_roles: List of allowed roles

        Returns:
            TeamMember record

        Raises:
            ForbiddenError: User doesn't have required role
        """
        result = await self.db.execute(
            select(TeamMember).where(
                TeamMember.team_id == team_id,
                TeamMember.user_id == user_id
            )
        )
        member = result.scalar_one_or_none()

        if not member or member.role not in allowed_roles:
            raise ForbiddenError(
                f"{' or '.join(allowed_roles).title()} required"
            )

        return member

    async def is_team_member(
        self,
        team_id: UUID,
        user_id: UUID
    ) -> bool:
        """Check if user is a member of the team."""
        result = await self.db.execute(
            select(TeamMember.id).where(
                TeamMember.team_id == team_id,
                TeamMember.user_id == user_id
            )
        )
        return result.scalar_one_or_none() is not None

    async def get_team_statistics(self, team_id: UUID) -> dict:
        """
        Get aggregated statistics for a team.

        Args:
            team_id: Team ID

        Returns:
            Statistics dictionary
        """
        team = await self.get_team(team_id)
        if not team:
            raise NotFoundError("Team not found")

        # Count members
        members_count = (await self.db.execute(
            select(func.count()).where(TeamMember.team_id == team_id)
        )).scalar() or 0

        # Count projects
        projects_count = (await self.db.execute(
            select(func.count()).where(Project.team_id == team_id)
        )).scalar() or 0

        # Gate statistics (simplified - expand as needed)
        # This would join with gates table through projects

        return {
            "team_id": team_id,
            "members_count": members_count,
            "projects_count": projects_count,
            "gates_total": 0,  # Implement with actual query
            "gates_passed": 0,
            "gates_failed": 0,
            "gates_pending": 0,
            "compliance_rate": 0.0,
            "evidence_count": 0,
            "last_activity": None
        }
```

---

## 7. API Routes Implementation

```python
# backend/app/api/routes/teams.py
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_current_active_user
from app.models import User
from app.services.teams_service import TeamsService
from app.schemas.team import (
    TeamCreate, TeamUpdate, TeamResponse, TeamDetailResponse,
    TeamMemberAdd, TeamMemberResponse, TeamMemberRoleUpdate,
    TeamStatistics
)
from app.core.exceptions import NotFoundError, ForbiddenError, ConflictError

router = APIRouter(prefix="/teams", tags=["teams"])


def get_teams_service(db: AsyncSession = Depends(get_db)) -> TeamsService:
    return TeamsService(db)


# ==================== Teams Endpoints ====================

@router.get("/", response_model=dict)
async def list_teams(
    organization_id: UUID | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    service: TeamsService = Depends(get_teams_service)
):
    """List teams user has access to."""
    teams, total = await service.list_teams(
        user_id=current_user.id,
        organization_id=organization_id,
        skip=skip,
        limit=limit
    )
    return {
        "items": [TeamResponse.model_validate(t) for t in teams],
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.post("/", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
async def create_team(
    team_data: TeamCreate,
    current_user: User = Depends(get_current_active_user),
    service: TeamsService = Depends(get_teams_service)
):
    """Create new team (user becomes owner)."""
    try:
        team = await service.create_team(
            organization_id=team_data.organization_id,
            name=team_data.name,
            slug=team_data.slug,
            owner_id=current_user.id,
            description=team_data.description
        )
        return TeamResponse.model_validate(team)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ForbiddenError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("/{team_id}", response_model=TeamDetailResponse)
async def get_team(
    team_id: UUID,
    include_members: bool = Query(False),
    include_projects: bool = Query(False),
    current_user: User = Depends(get_current_active_user),
    service: TeamsService = Depends(get_teams_service)
):
    """Get team details with members and projects."""
    # Check membership
    if not await service.is_team_member(team_id, current_user.id):
        raise HTTPException(status_code=403, detail="Access denied")

    team = await service.get_team(
        team_id,
        include_members=include_members,
        include_projects=include_projects
    )
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    return TeamDetailResponse.model_validate(team)


@router.patch("/{team_id}", response_model=TeamResponse)
async def update_team(
    team_id: UUID,
    team_data: TeamUpdate,
    current_user: User = Depends(get_current_active_user),
    service: TeamsService = Depends(get_teams_service)
):
    """Update team (admin/owner only)."""
    try:
        team = await service.update_team(
            team_id=team_id,
            user_id=current_user.id,
            data=team_data.model_dump(exclude_unset=True)
        )
        return TeamResponse.model_validate(team)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ForbiddenError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.delete("/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_team(
    team_id: UUID,
    current_user: User = Depends(get_current_active_user),
    service: TeamsService = Depends(get_teams_service)
):
    """Delete team (owner only)."""
    try:
        await service.delete_team(team_id=team_id, user_id=current_user.id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ForbiddenError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))


# ==================== Team Members Endpoints ====================

@router.get("/{team_id}/members", response_model=dict)
async def list_team_members(
    team_id: UUID,
    role: str | None = Query(None, pattern=r'^(owner|admin|member)$'),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    service: TeamsService = Depends(get_teams_service)
):
    """List team members."""
    if not await service.is_team_member(team_id, current_user.id):
        raise HTTPException(status_code=403, detail="Access denied")

    members, total = await service.list_members(
        team_id=team_id,
        role=role,
        skip=skip,
        limit=limit
    )
    return {
        "items": [TeamMemberResponse.model_validate(m) for m in members],
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.post("/{team_id}/members", response_model=TeamMemberResponse, status_code=status.HTTP_201_CREATED)
async def add_team_member(
    team_id: UUID,
    member_data: TeamMemberAdd,
    current_user: User = Depends(get_current_active_user),
    service: TeamsService = Depends(get_teams_service)
):
    """Add member to team (admin/owner only)."""
    try:
        member = await service.add_member(
            team_id=team_id,
            user_id=member_data.user_id,
            added_by=current_user.id,
            role=member_data.role
        )
        return TeamMemberResponse.model_validate(member)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ForbiddenError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.patch("/{team_id}/members/{user_id}", response_model=TeamMemberResponse)
async def update_team_member_role(
    team_id: UUID,
    user_id: UUID,
    role_data: TeamMemberRoleUpdate,
    current_user: User = Depends(get_current_active_user),
    service: TeamsService = Depends(get_teams_service)
):
    """Update member role (owner only)."""
    try:
        member = await service.update_member_role(
            team_id=team_id,
            user_id=user_id,
            updated_by=current_user.id,
            new_role=role_data.role
        )
        return TeamMemberResponse.model_validate(member)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ForbiddenError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.delete("/{team_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_team_member(
    team_id: UUID,
    user_id: UUID,
    current_user: User = Depends(get_current_active_user),
    service: TeamsService = Depends(get_teams_service)
):
    """Remove member from team (admin/owner only, can't remove owner)."""
    try:
        await service.remove_member(
            team_id=team_id,
            user_id=user_id,
            removed_by=current_user.id
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ForbiddenError as e:
        raise HTTPException(status_code=403, detail=str(e))


# ==================== Statistics Endpoint ====================

@router.get("/{team_id}/statistics", response_model=TeamStatistics)
async def get_team_statistics(
    team_id: UUID,
    current_user: User = Depends(get_current_active_user),
    service: TeamsService = Depends(get_teams_service)
):
    """Get team metrics and compliance summary."""
    if not await service.is_team_member(team_id, current_user.id):
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        stats = await service.get_team_statistics(team_id)
        return TeamStatistics(**stats)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
```

---

## 8. Testing Requirements

### Unit Tests

| Test Case | Description |
|-----------|-------------|
| `test_create_team_success` | Create team with valid data |
| `test_create_team_duplicate_slug` | Reject duplicate slug in org |
| `test_create_team_not_org_member` | Reject if user not in org |
| `test_add_member_success` | Add member with valid role |
| `test_add_member_duplicate` | Reject if already member |
| `test_add_member_wrong_org` | Reject if user in different org |
| `test_remove_owner_fails` | Cannot remove team owner |
| `test_update_role_owner_only` | Only owner can change roles |
| `test_delete_team_with_projects` | Reject if team has projects |

### AI Agent Tests (CTO R1/R2)

| Test Case | Description |
|-----------|-------------|
| `test_add_ai_agent_success` | Add AI agent with ai_agent role |
| `test_add_ai_agent_as_owner_fails` | Reject AI agent with owner role |
| `test_add_ai_agent_as_admin_fails` | Reject AI agent with admin role |
| `test_promote_ai_agent_to_admin_fails` | Cannot promote AI agent to admin |
| `test_filter_members_by_member_type` | Filter human/ai_agent members |
| `test_ai_agent_member_type_response` | Response includes is_ai_agent, is_coach flags |

### Integration Tests

| Test Case | Description |
|-----------|-------------|
| `test_full_team_lifecycle` | Create → Add members → Update → Delete |
| `test_team_project_integration` | Create team → Create project in team |
| `test_authorization_matrix` | Verify all role permissions |
| `test_pagination` | Verify pagination works correctly |
| `test_ai_agent_sase_workflow` | AI agent can read BRS, create MRP/CRP |

---

## 9. Success Criteria

- [ ] All 12 endpoints return expected responses
- [ ] Authorization rules enforced correctly
- [ ] Pagination works for list endpoints
- [ ] Error responses match specification
- [ ] 30+ unit tests passing
- [ ] Integration tests passing
- [ ] OpenAPI spec generated correctly
- [ ] **CTO R1**: `ai_agent` role supported in add/update member
- [ ] **CTO R2**: `member_type` field (human/ai_agent) in responses
- [ ] **SASE Compliance**: AI agents blocked from owner/admin roles

---

## Document Control

| Field | Value |
|-------|-------|
| **Version** | 1.0.0 |
| **Date** | January 17, 2026 |
| **Author** | Backend Lead |
| **Reviewer** | CTO |
| **Status** | APPROVED |
