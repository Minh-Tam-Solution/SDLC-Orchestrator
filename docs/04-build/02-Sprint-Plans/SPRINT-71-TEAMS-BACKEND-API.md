# Sprint 71: Teams Backend API

**Sprint ID:** S71  
**Status:** ⏳ QUEUED  
**Duration:** 5 days (Jan 27-31, 2026)  
**Goal:** Implement all Teams and Organizations API endpoints per OpenAPI spec

**Dependency:** Sprint 70 (Models & Migration) must be complete

---

## 🎯 Orchestrator Philosophy: SE4H + SE4A Roles

Per SDLC 5.1.2 Agentic Core Principles, Teams API must support:

### Team Roles → SASE Mapping

| Team Role | SASE Role | Permissions | Use Case |
|-----------|-----------|-------------|----------|
| **owner** | SE4H (Agent Coach) | Full control, VCR authority | Define BriefingScript, approve MRP |
| **admin** | SE4H (Agent Coach) | Manage members, update settings | MentorScript maintenance |
| **member** | SE4A (Agent Executor) or SE4H | Execute tasks, create MRP | Implementation work |
| **ai_agent** | SE4A (Agent Executor) | Read-only BRS, create MRP/CRP | Autonomous execution |

### Team Settings → SASE Artifacts

```yaml
Team.settings:
  mentor_scripts:          # MentorScript references
    - /docs/02-design/MTS-001-Backend-Standards.yaml
  briefing_templates:      # BriefingScript templates
    - /docs/01-planning/BRS-Template.yaml
  agentic_maturity: L1     # L0-L3 per SDLC 5.1.2
  crp_threshold: 0.7       # CRP required if confidence < 70%
  auto_approve_mrp: false  # Human VCR required
```

### API Design Alignment with SASE

| Endpoint | SASE Discipline | Purpose |
|----------|-----------------|---------|
| `POST /teams` | BriefingEng | Create team with initial brief |
| `POST /teams/{id}/members` | ATIE | Add human or AI agent |
| `GET /teams/{id}/statistics` | ATME | Monitor team performance |
| `PATCH /teams/{id}/settings` | AGE | Governance configuration |

---

## 📋 Sprint Overview

| Attribute | Value |
|-----------|-------|
| Sprint Number | 71 |
| Start Date | January 27, 2026 (Monday) |
| End Date | January 31, 2026 (Friday) |
| Working Days | 5 |
| Story Points | 29 (+3 for SE4A AI Agent Support) |
| Team Capacity | Backend Dev (5d), Tech Lead (1d) |

---

## 🎯 Sprint Goal

> Implement complete Teams and Organizations REST API with proper authorization, enabling team CRUD operations, member management, and team statistics.

---

## 📊 Sprint Backlog

### Epic: ADR-028 Teams Feature Implementation

#### Story 1: TeamsService (8 SP)
**As a** developer  
**I want** a service layer for team operations  
**So that** business logic is separated from routes

| Task ID | Task | Owner | Est | Status |
|---------|------|-------|-----|--------|
| S71-T01 | Implement `create_team()` | Backend Dev | 2h | ⏳ |
| S71-T02 | Implement `get_team()` with eager loading | Backend Dev | 1h | ⏳ |
| S71-T03 | Implement `list_teams()` with pagination | Backend Dev | 2h | ⏳ |
| S71-T04 | Implement `update_team()` | Backend Dev | 1h | ⏳ |
| S71-T05 | Implement `delete_team()` | Backend Dev | 1h | ⏳ |
| S71-T06 | Implement `add_member()` | Backend Dev | 2h | ⏳ |
| S71-T07 | Implement `remove_member()` | Backend Dev | 2h | ⏳ |
| S71-T08 | Implement `update_member_role()` | Backend Dev | 1h | ⏳ |
| S71-T09 | Implement `get_team_statistics()` | Backend Dev | 2h | ⏳ |
| S71-T10 | Implement permission checks | Backend Dev | 2h | ⏳ |

**Acceptance Criteria:**
- [ ] All service methods implemented with async/await
- [ ] Proper error handling (404, 403, 409)
- [ ] Permission validation (owner/admin/member)
- [ ] Cannot remove last owner from team
- [ ] Statistics include member count, project count, gate metrics

---

#### Story 2: OrganizationsService (4 SP)
**As a** developer  
**I want** a service layer for organization operations  
**So that** org management is consistent

| Task ID | Task | Owner | Est | Status |
|---------|------|-------|-----|--------|
| S71-T11 | Implement `create_organization()` | Backend Dev | 2h | ⏳ |
| S71-T12 | Implement `get_organization()` | Backend Dev | 1h | ⏳ |
| S71-T13 | Implement `list_organizations()` | Backend Dev | 1h | ⏳ |
| S71-T14 | Implement `update_organization()` | Backend Dev | 1h | ⏳ |
| S71-T15 | Implement `get_organization_statistics()` | Backend Dev | 2h | ⏳ |

**Acceptance Criteria:**
- [ ] Organization created with creator as admin
- [ ] Slug uniqueness enforced
- [ ] Plan levels supported (free, starter, pro, enterprise)
- [ ] Statistics include team count, user count, usage metrics

---

#### Story 3: Teams API Routes (8 SP)
**As an** API consumer  
**I want** REST endpoints for team management  
**So that** I can manage teams via HTTP

| Task ID | Task | Owner | Est | Status |
|---------|------|-------|-----|--------|
| S71-T16 | `GET /api/v1/teams` - List teams | Backend Dev | 1h | ⏳ |
| S71-T17 | `POST /api/v1/teams` - Create team | Backend Dev | 1.5h | ⏳ |
| S71-T18 | `GET /api/v1/teams/{id}` - Get team | Backend Dev | 1h | ⏳ |
| S71-T19 | `PATCH /api/v1/teams/{id}` - Update team | Backend Dev | 1h | ⏳ |
| S71-T20 | `DELETE /api/v1/teams/{id}` - Delete team | Backend Dev | 1h | ⏳ |
| S71-T21 | `GET /api/v1/teams/{id}/members` - List members | Backend Dev | 1h | ⏳ |
| S71-T22 | `POST /api/v1/teams/{id}/members` - Add member | Backend Dev | 1.5h | ⏳ |
| S71-T23 | `DELETE /api/v1/teams/{id}/members/{uid}` - Remove | Backend Dev | 1h | ⏳ |
| S71-T24 | `PATCH /api/v1/teams/{id}/members/{uid}` - Role | Backend Dev | 1h | ⏳ |
| S71-T25 | `GET /api/v1/teams/{id}/statistics` - Stats | Backend Dev | 1h | ⏳ |

**Acceptance Criteria:**
- [ ] All 10 endpoints return correct status codes
- [ ] Response format matches OpenAPI spec
- [ ] Pagination on list endpoints (skip, limit)
- [ ] Proper authentication required
- [ ] Authorization checked per endpoint

---

#### Story 4: Organizations API Routes (3 SP)
**As an** API consumer  
**I want** REST endpoints for organization management  
**So that** I can manage orgs via HTTP

| Task ID | Task | Owner | Est | Status |
|---------|------|-------|-----|--------|
| S71-T26 | `GET /api/v1/organizations` - List orgs | Backend Dev | 1h | ⏳ |
| S71-T27 | `POST /api/v1/organizations` - Create org | Backend Dev | 1.5h | ⏳ |
| S71-T28 | `GET /api/v1/organizations/{id}` - Get org | Backend Dev | 1h | ⏳ |
| S71-T29 | `PATCH /api/v1/organizations/{id}` - Update org | Backend Dev | 1h | ⏳ |

**Acceptance Criteria:**
- [ ] All 4 endpoints functional
- [ ] User can only see orgs they belong to
- [ ] Only org admins can update org settings

---

#### Story 5: AI Agent Support - SE4A Integration (3 SP) ⭐ CTO R1
**As a** team orchestrator
**I want** to add AI agents as team members
**So that** SE4A agents can participate in SASE workflows

| Task ID | Task | Owner | Est | Status |
|---------|------|-------|-----|--------|
| S71-T30 | Add `ai_agent` to role constraint | Backend Dev | 1h | ⏳ |
| S71-T31 | Add `member_type` column (human/ai_agent) | Backend Dev | 1h | ⏳ |
| S71-T32 | Update TeamMember model with member_type | Backend Dev | 1h | ⏳ |
| S71-T33 | Create Alembic migration for new fields | Backend Dev | 1h | ⏳ |
| S71-T34 | Update schemas for AI agent support | Backend Dev | 1h | ⏳ |
| S71-T35 | Add AI agent validation rules | Backend Dev | 2h | ⏳ |

**Acceptance Criteria:**
- [ ] `ai_agent` role can be assigned to team members
- [ ] `member_type` distinguishes human from AI agent
- [ ] AI agents have read-only BRS, can create MRP/CRP
- [ ] AI agents cannot be team owners
- [ ] API validates member_type on add_member

**SASE Compliance:**
```yaml
# AI Agent constraints per SDLC 5.1.2
ai_agent_rules:
  allowed_roles: [ai_agent, member]  # NOT owner/admin
  capabilities:
    - read_briefing_script
    - create_mrp
    - create_crp
    - execute_tasks
  prohibited:
    - approve_mrp (VCR)
    - change_roles
    - delete_team
```

---

#### Story 6: Integration Tests (3 SP)
**As a** developer
**I want** integration tests for Teams API
**So that** I can verify API behavior

| Task ID | Task | Owner | Est | Status |
|---------|------|-------|-----|--------|
| S71-T36 | Test team CRUD endpoints | Backend Dev | 2h | ⏳ |
| S71-T37 | Test member management | Backend Dev | 2h | ⏳ |
| S71-T38 | Test permission scenarios | Backend Dev | 2h | ⏳ |
| S71-T39 | Test organization endpoints | Backend Dev | 1h | ⏳ |
| S71-T40 | Test error cases (404, 403, 409) | Backend Dev | 1h | ⏳ |
| S71-T41 | Test AI agent member type | Backend Dev | 1h | ⏳ |

**Acceptance Criteria:**
- [ ] 35+ integration tests passing
- [ ] All happy paths covered
- [ ] All error scenarios covered
- [ ] Permission matrix fully tested
- [ ] AI agent constraints verified

---

## 📁 Files to Create/Modify

### New Files
```
backend/app/
├── services/
│   ├── teams_service.py           # ~400 lines
│   └── organizations_service.py   # ~250 lines
├── api/routes/
│   ├── teams.py                   # ~450 lines
│   └── organizations.py           # ~200 lines
└── tests/integration/
    └── test_teams_api.py          # ~600 lines
```

### Modified Files
```
backend/app/api/routes/__init__.py    # Add routers
backend/app/main.py                   # Include routers
```

---

## 🔌 API Specification

### Teams Endpoints

#### GET /api/v1/teams
List teams user has access to.

```yaml
parameters:
  - name: organization_id
    in: query
    schema: { type: string, format: uuid }
  - name: skip
    in: query
    schema: { type: integer, default: 0 }
  - name: limit
    in: query
    schema: { type: integer, default: 20, max: 100 }
responses:
  200:
    content:
      application/json:
        schema:
          type: array
          items: { $ref: '#/components/schemas/TeamResponse' }
```

#### POST /api/v1/teams
Create new team (user becomes owner).

```yaml
requestBody:
  content:
    application/json:
      schema:
        type: object
        required: [name, slug, organization_id]
        properties:
          name: { type: string, maxLength: 255 }
          slug: { type: string, pattern: '^[a-z0-9-]+$', maxLength: 100 }
          organization_id: { type: string, format: uuid }
          description: { type: string }
responses:
  201:
    content:
      application/json:
        schema: { $ref: '#/components/schemas/TeamResponse' }
  409:
    description: Team slug already exists in organization
```

#### GET /api/v1/teams/{team_id}
Get team details with members.

```yaml
parameters:
  - name: team_id
    in: path
    required: true
    schema: { type: string, format: uuid }
responses:
  200:
    content:
      application/json:
        schema: { $ref: '#/components/schemas/TeamDetailResponse' }
  404:
    description: Team not found
```

#### PATCH /api/v1/teams/{team_id}
Update team (admin/owner only).

```yaml
requestBody:
  content:
    application/json:
      schema:
        type: object
        properties:
          name: { type: string }
          description: { type: string }
          settings: { type: object }
responses:
  200:
    content:
      application/json:
        schema: { $ref: '#/components/schemas/TeamResponse' }
  403:
    description: Not authorized to update team
```

#### DELETE /api/v1/teams/{team_id}
Delete team (owner only).

```yaml
responses:
  204:
    description: Team deleted
  403:
    description: Not authorized to delete team
```

#### POST /api/v1/teams/{team_id}/members
Add member to team (admin/owner only).

```yaml
requestBody:
  content:
    application/json:
      schema:
        type: object
        required: [user_id]
        properties:
          user_id: { type: string, format: uuid }
          role: { type: string, enum: [member, admin], default: member }
responses:
  201:
    content:
      application/json:
        schema: { $ref: '#/components/schemas/TeamMemberResponse' }
  409:
    description: User already a member
```

#### DELETE /api/v1/teams/{team_id}/members/{user_id}
Remove member from team.

```yaml
responses:
  204:
    description: Member removed
  400:
    description: Cannot remove last owner
```

#### PATCH /api/v1/teams/{team_id}/members/{user_id}
Update member role (owner only).

```yaml
requestBody:
  content:
    application/json:
      schema:
        type: object
        required: [role]
        properties:
          role: { type: string, enum: [owner, admin, member] }
responses:
  200:
    content:
      application/json:
        schema: { $ref: '#/components/schemas/TeamMemberResponse' }
```

#### GET /api/v1/teams/{team_id}/statistics
Get team metrics.

```yaml
responses:
  200:
    content:
      application/json:
        schema:
          type: object
          properties:
            member_count: { type: integer }
            project_count: { type: integer }
            active_gates: { type: integer }
            compliance_score: { type: number }
            created_at: { type: string, format: date-time }
```

---

## 🔐 Permission Matrix

| Action | Owner | Admin | Member | Non-Member |
|--------|-------|-------|--------|------------|
| View team | ✅ | ✅ | ✅ | ❌ |
| Update team | ✅ | ✅ | ❌ | ❌ |
| Delete team | ✅ | ❌ | ❌ | ❌ |
| View members | ✅ | ✅ | ✅ | ❌ |
| Add member | ✅ | ✅ | ❌ | ❌ |
| Remove member | ✅ | ✅* | ❌ | ❌ |
| Change role | ✅ | ❌ | ❌ | ❌ |
| View statistics | ✅ | ✅ | ✅ | ❌ |

*Admin can remove members but not owners

---

## 📝 Service Implementation

### TeamsService
```python
# backend/app/services/teams_service.py
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Team, TeamMember, Project, User
from app.schemas.team import TeamCreate, TeamUpdate, TeamMemberAdd

class TeamsService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_team(
        self,
        data: TeamCreate,
        owner_id: UUID
    ) -> Team:
        """Create team and add owner as first member."""
        # Check slug uniqueness within org
        existing = await self.db.scalar(
            select(Team).where(
                Team.organization_id == data.organization_id,
                Team.slug == data.slug
            )
        )
        if existing:
            raise TeamSlugExistsError(data.slug)
        
        # Create team
        team = Team(
            organization_id=data.organization_id,
            name=data.name,
            slug=data.slug,
            description=data.description
        )
        self.db.add(team)
        await self.db.flush()
        
        # Add owner
        member = TeamMember(
            team_id=team.id,
            user_id=owner_id,
            role="owner"
        )
        self.db.add(member)
        await self.db.commit()
        await self.db.refresh(team)
        
        return team
    
    async def get_team(self, team_id: UUID) -> Team | None:
        """Get team with members and projects loaded."""
        return await self.db.scalar(
            select(Team)
            .options(
                selectinload(Team.members).selectinload(TeamMember.user),
                selectinload(Team.projects)
            )
            .where(Team.id == team_id)
        )
    
    async def list_teams(
        self,
        user_id: UUID,
        organization_id: UUID | None = None,
        skip: int = 0,
        limit: int = 20
    ) -> list[Team]:
        """List teams user is a member of."""
        query = (
            select(Team)
            .join(TeamMember)
            .where(TeamMember.user_id == user_id)
        )
        
        if organization_id:
            query = query.where(Team.organization_id == organization_id)
        
        query = query.offset(skip).limit(limit)
        result = await self.db.scalars(query)
        return list(result.all())
    
    async def add_member(
        self,
        team_id: UUID,
        user_id: UUID,
        role: str = "member"
    ) -> TeamMember:
        """Add user to team with specified role."""
        # Check if already member
        existing = await self.db.scalar(
            select(TeamMember).where(
                TeamMember.team_id == team_id,
                TeamMember.user_id == user_id
            )
        )
        if existing:
            raise UserAlreadyMemberError(user_id)
        
        member = TeamMember(
            team_id=team_id,
            user_id=user_id,
            role=role
        )
        self.db.add(member)
        await self.db.commit()
        await self.db.refresh(member)
        
        return member
    
    async def remove_member(
        self,
        team_id: UUID,
        user_id: UUID
    ) -> bool:
        """Remove user from team (cannot remove last owner)."""
        member = await self.db.scalar(
            select(TeamMember).where(
                TeamMember.team_id == team_id,
                TeamMember.user_id == user_id
            )
        )
        if not member:
            raise MemberNotFoundError(user_id)
        
        # Check if last owner
        if member.role == "owner":
            owner_count = await self.db.scalar(
                select(func.count())
                .select_from(TeamMember)
                .where(
                    TeamMember.team_id == team_id,
                    TeamMember.role == "owner"
                )
            )
            if owner_count <= 1:
                raise CannotRemoveLastOwnerError()
        
        await self.db.delete(member)
        await self.db.commit()
        return True
    
    async def get_team_statistics(self, team_id: UUID) -> dict:
        """Get team metrics: members, projects, gates, compliance."""
        team = await self.get_team(team_id)
        if not team:
            raise TeamNotFoundError(team_id)
        
        project_count = await self.db.scalar(
            select(func.count())
            .select_from(Project)
            .where(Project.team_id == team_id)
        )
        
        return {
            "member_count": len(team.members),
            "project_count": project_count,
            "active_gates": 0,  # TODO: implement
            "compliance_score": 0.0,  # TODO: implement
            "created_at": team.created_at
        }
    
    async def check_permission(
        self,
        team_id: UUID,
        user_id: UUID,
        required_role: str = "member"
    ) -> bool:
        """Check if user has required role in team."""
        member = await self.db.scalar(
            select(TeamMember).where(
                TeamMember.team_id == team_id,
                TeamMember.user_id == user_id
            )
        )
        if not member:
            return False
        
        role_hierarchy = {"owner": 3, "admin": 2, "member": 1}
        return role_hierarchy.get(member.role, 0) >= role_hierarchy.get(required_role, 0)
```

---

## ✅ Definition of Done

### Code Complete
- [ ] TeamsService with all methods
- [ ] OrganizationsService with all methods
- [ ] Teams routes (10 endpoints)
- [ ] Organizations routes (4 endpoints)
- [ ] Routers registered in main.py

### Tests
- [ ] 30+ integration tests passing
- [ ] Permission matrix fully tested
- [ ] Error scenarios covered
- [ ] No regression in existing tests

### Documentation
- [ ] OpenAPI spec matches implementation
- [ ] Docstrings on all methods
- [ ] Error codes documented

### Review
- [ ] Code review approved
- [ ] PR merged to main
- [ ] Staging deployment verified

---

## 📅 Daily Schedule

### Day 1 (Mon, Jan 27)
- [ ] Morning: TeamsService CRUD (S71-T01 to T05)
- [ ] Afternoon: Member operations (S71-T06 to T09)
- [ ] EOD: TeamsService complete

### Day 2 (Tue, Jan 28)
- [ ] Morning: Permission checks (S71-T10)
- [ ] Afternoon: OrganizationsService (S71-T11 to T15)
- [ ] EOD: All services complete

### Day 3 (Wed, Jan 29)
- [ ] Morning: Teams routes (S71-T16 to T20)
- [ ] Afternoon: Member routes (S71-T21 to T25)
- [ ] EOD: Teams API complete

### Day 4 (Thu, Jan 30)
- [ ] Morning: Organizations routes (S71-T26 to T29)
- [ ] Afternoon: Integration tests (S71-T30 to T32)
- [ ] EOD: 20+ tests passing

### Day 5 (Fri, Jan 31)
- [ ] Morning: Complete tests (S71-T33 to T34)
- [ ] Afternoon: Code review, documentation
- [ ] EOD: PR merged, Sprint 71 complete

---

## 🔗 References

- [Sprint 70: Teams Foundation](./SPRINT-70-TEAMS-FOUNDATION.md)
- [OpenAPI Spec - Teams](../../02-design/04-API-Design/openapi.yaml)
- [ADR-028: Teams Feature](../../06-deploy/TEAMS-FEATURE-REMEDIATION-PLAN.md)
