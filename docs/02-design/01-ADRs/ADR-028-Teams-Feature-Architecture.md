# ADR-028: Teams Feature Architecture
## Multi-Tenant Organization & Team Management

**Status**: APPROVED
**Date**: January 17, 2026
**Decision Makers**: CTO, CEO
**Stage**: Stage 02 (HOW - Design & Architecture)
**Framework**: SDLC 6.1.0
**Sprint**: Sprint 70 (Jan 20 - Feb 3, 2026)
**Priority**: P0 - BLOCKS PLATFORM VALUE PROPOSITION

---

## Context

### Problem Statement

SDLC Orchestrator currently lacks multi-tenant team management - the **CORE value proposition** for enterprise customers. Without Teams:

- Individual developers can achieve the same outcome with AI + SDLC Framework directly
- No governance layer exists for team collaboration
- No audit trail for team-based decisions
- Platform cannot justify enterprise pricing

### Business Impact

| Metric | Without Teams | With Teams |
|--------|---------------|------------|
| Value Proposition | None (single dev can use AI + SDLC Framework) | Enterprise governance |
| Target Market | 0 customers | 100+ enterprise teams |
| Competitive Position | AI wrapper | Unique orchestration platform |
| Mission Alignment | Individual tool | "100 teams by MVP" achievable |

### Current State

**Exists (Design Only)**:
- OpenAPI Spec: Team endpoints defined
- DB Schema: Team tables designed
- ProjectMember model: Partial team concept

**Completely Missing**:
- Organization model and API
- Team model and API
- TeamMember model and API
- Frontend pages and hooks
- Integration with existing features

---

## Decision

We will implement a **3-layer multi-tenant architecture**:

```
┌─────────────────────────────────────────────────────────────┐
│  LAYER 1: ORGANIZATION (Billing & Compliance Root)          │
│  - Single organization per customer account                 │
│  - Plan management (free/pro/enterprise)                    │
│  - Organization-wide settings and policies                  │
├─────────────────────────────────────────────────────────────┤
│  LAYER 2: TEAM (Collaboration Unit)                         │
│  - Multiple teams per organization                          │
│  - Team-specific settings and permissions                   │
│  - Cross-functional project grouping                        │
├─────────────────────────────────────────────────────────────┤
│  LAYER 3: PROJECT (Work Container)                          │
│  - Projects belong to teams (required)                      │
│  - Team members inherit project access                      │
│  - Gates scoped to project within team context              │
└─────────────────────────────────────────────────────────────┘
```

### Key Design Decisions

1. **Organization is Required**
   - Every user belongs to exactly one organization
   - New users create organization on first login OR join via invite
   - Solo users get a "Personal" organization automatically

2. **Team Membership Model**
   - 3-tier roles: `owner`, `admin`, `member`
   - Owner can do everything including delete team
   - Admin can manage members and settings
   - Member can view and contribute to projects

3. **Project-Team Relationship**
   - Projects MUST belong to a team (required FK)
   - Team members automatically have access to team projects
   - Project-level permissions can restrict further

4. **Backward Compatibility**
   - Existing users migrated to "Default Organization"
   - Existing projects assigned to "Unassigned Team"
   - V1 API continues to work (team context optional)
   - V2 API requires team context

---

## Rationale

### Why 3-Layer Instead of 2-Layer?

| Approach | Pros | Cons | Decision |
|----------|------|------|----------|
| **User → Team → Project** | Simple | No billing isolation, no org-wide policies | ❌ Rejected |
| **User → Org → Project** | Clear billing | No team collaboration | ❌ Rejected |
| **User → Org → Team → Project** | Full flexibility, clear boundaries | More complexity | ✅ Selected |

### Why Required Team for Projects?

Projects without teams create governance gaps:
- No clear ownership escalation path
- Gate approvals lack team context
- Cross-project reporting impossible
- Dashboard metrics meaningless

### Why Not ProjectMember Expansion?

The existing `project_members` table handles project-level access but:
- Cannot express team-wide permissions
- No inheritance mechanism
- No organization context
- Requires duplicate entries per project

---

## Architecture Design

### Entity Relationships

```
organizations
├── id (PK)
├── name: VARCHAR(255) NOT NULL
├── slug: VARCHAR(100) UNIQUE NOT NULL
├── plan: VARCHAR(50) DEFAULT 'free'  -- free, pro, enterprise
├── settings: JSONB DEFAULT '{}'
├── created_at, updated_at
│
├── users[] (1:N via organization_id FK)
└── teams[] (1:N via organization_id FK)

teams
├── id (PK)
├── organization_id (FK → organizations.id) NOT NULL
├── name: VARCHAR(255) NOT NULL
├── slug: VARCHAR(100) NOT NULL
├── description: TEXT
├── settings: JSONB DEFAULT '{}'
├── created_at, updated_at
├── UNIQUE(organization_id, slug)
│
├── members[] (1:N via team_members)
└── projects[] (1:N via team_id FK)

team_members
├── id (PK)
├── team_id (FK → teams.id) NOT NULL ON DELETE CASCADE
├── user_id (FK → users.id) NOT NULL ON DELETE CASCADE
├── role: VARCHAR(50) NOT NULL DEFAULT 'member'  -- owner, admin, member
├── joined_at: TIMESTAMP DEFAULT NOW()
├── UNIQUE(team_id, user_id)
```

### Authorization Matrix

| Action | Owner | Admin | Member |
|--------|-------|-------|--------|
| View team | ✅ | ✅ | ✅ |
| View members | ✅ | ✅ | ✅ |
| View projects | ✅ | ✅ | ✅ |
| Create project | ✅ | ✅ | ❌ |
| Add member | ✅ | ✅ | ❌ |
| Remove member | ✅ | ✅ | ❌ |
| Change member role | ✅ | ❌ | ❌ |
| Update team settings | ✅ | ✅ | ❌ |
| Delete team | ✅ | ❌ | ❌ |
| Transfer ownership | ✅ | ❌ | ❌ |

### API Endpoints

```yaml
# Organization Management
POST   /organizations              # Create organization (on signup)
GET    /organizations/{id}         # Get organization details
PATCH  /organizations/{id}         # Update organization (owner only)

# Team Management
GET    /teams                      # List user's teams
POST   /teams                      # Create team (becomes owner)
GET    /teams/{id}                 # Get team with members/projects
PATCH  /teams/{id}                 # Update team (admin+)
DELETE /teams/{id}                 # Delete team (owner only)

# Team Membership
GET    /teams/{id}/members         # List team members
POST   /teams/{id}/members         # Add member (admin+)
PATCH  /teams/{id}/members/{uid}   # Update role (owner only)
DELETE /teams/{id}/members/{uid}   # Remove member (admin+)

# Team Statistics
GET    /teams/{id}/statistics      # Projects, gates, compliance metrics
```

### Frontend Routes

```
/app/teams                         # Teams list (grid view)
/app/teams/new                     # Create team wizard
/app/teams/[id]                    # Team dashboard
/app/teams/[id]/members            # Member management
/app/teams/[id]/projects           # Team projects list
/app/teams/[id]/settings           # Team settings
```

---

## Migration Strategy

### Phase 1: Schema Migration (Non-breaking)

```sql
-- Add columns as NULLABLE first
ALTER TABLE users ADD COLUMN organization_id UUID;
ALTER TABLE projects ADD COLUMN team_id UUID;

-- Create new tables
CREATE TABLE organizations (...);
CREATE TABLE teams (...);
CREATE TABLE team_members (...);

-- Add foreign keys
ALTER TABLE users
  ADD CONSTRAINT fk_users_org
  FOREIGN KEY (organization_id) REFERENCES organizations(id);

ALTER TABLE projects
  ADD CONSTRAINT fk_projects_team
  FOREIGN KEY (team_id) REFERENCES teams(id);
```

### Phase 2: Data Migration

```sql
-- Create default organization for existing users
INSERT INTO organizations (id, name, slug, plan)
VALUES ('default-org-uuid', 'Default Organization', 'default', 'free');

-- Migrate existing users
UPDATE users SET organization_id = 'default-org-uuid' WHERE organization_id IS NULL;

-- Create default team
INSERT INTO teams (id, organization_id, name, slug)
VALUES ('default-team-uuid', 'default-org-uuid', 'Unassigned', 'unassigned');

-- Migrate existing projects
UPDATE projects SET team_id = 'default-team-uuid' WHERE team_id IS NULL;

-- Add owners for all users in default team
INSERT INTO team_members (team_id, user_id, role)
SELECT 'default-team-uuid', id, 'member' FROM users;
```

### Phase 3: Constraint Enforcement

```sql
-- Make columns NOT NULL after migration
ALTER TABLE users ALTER COLUMN organization_id SET NOT NULL;
ALTER TABLE projects ALTER COLUMN team_id SET NOT NULL;
```

---

## Performance Considerations

### Indexes

```sql
-- Team lookups
CREATE INDEX idx_teams_org ON teams(organization_id);
CREATE INDEX idx_team_members_team ON team_members(team_id);
CREATE INDEX idx_team_members_user ON team_members(user_id);

-- Project scoping
CREATE INDEX idx_projects_team ON projects(team_id);

-- User org lookup
CREATE INDEX idx_users_org ON users(organization_id);
```

### Caching Strategy

```yaml
Redis Keys:
  team:{id}:members      # List of member UUIDs (TTL: 5min)
  user:{id}:teams        # List of team UUIDs (TTL: 5min)
  team:{id}:projects     # List of project UUIDs (TTL: 5min)

Invalidation:
  - On member add/remove: Invalidate team:{id}:members, user:{id}:teams
  - On project create: Invalidate team:{id}:projects
```

---

## Consequences

### Positive

1. **Clear Value Proposition**: Platform enables team governance (not just individual tracking)
2. **Enterprise Ready**: Multi-tenant structure supports billing isolation
3. **Audit Trail**: Team context for all gate decisions and approvals
4. **Scalable**: Organization → Team → Project hierarchy supports growth
5. **Backward Compatible**: Existing users/projects migrated gracefully

### Negative

1. **Complexity**: 3-layer model more complex than single-tenant
2. **Migration Risk**: Existing data must be migrated carefully
3. **API Changes**: New endpoints, optional team context in existing endpoints
4. **Frontend Scope**: New pages and components required

### Neutral

1. **Database Growth**: 3 new tables (~100 rows initially)
2. **Query Complexity**: JOINs required for team-scoped queries
3. **Testing**: New test suites for team authorization

---

## Implementation Plan

### Sprint 70 (Week 1-2): Foundation
- [x] ADR-028 approved
- [ ] Database migration script
- [ ] Organization, Team, TeamMember models
- [ ] Update User and Project models with FKs

### Sprint 71 (Week 3-4): Backend API
- [ ] Organizations API (3 endpoints)
- [ ] Teams API (5 endpoints)
- [ ] Team Members API (4 endpoints)
- [ ] Teams Service with authorization
- [ ] API tests (30+ tests)

### Sprint 72 (Week 5-6): Frontend
- [ ] useTeams hook
- [ ] Teams list page
- [ ] Team detail page
- [ ] Member management page
- [ ] Team settings page

### Sprint 73 (Week 7-8): Integration
- [ ] Project creation with team selector
- [ ] Dashboard team-scoped metrics
- [ ] Gate approvals with team context
- [ ] E2E tests (10+ scenarios)

---

## Success Criteria

### Phase 1 (Sprint 70)
- [ ] `alembic upgrade head` succeeds
- [ ] All 3 new tables exist in database
- [ ] Existing data migrated to default org/team
- [ ] No breaking changes to existing API

### Phase 2 (Sprint 71)
- [ ] 12 API endpoints return 200
- [ ] Authorization matrix enforced
- [ ] 30+ unit/integration tests passing

### Phase 3 (Sprint 72)
- [ ] Teams list page renders
- [ ] Create team flow works E2E
- [ ] Team dashboard shows correct data

### Phase 4 (Sprint 73)
- [ ] E2E: Create org → Create team → Add member → Create project → Gate approval
- [ ] Zero Mock Policy satisfied
- [ ] Code coverage ≥ 80%

---

## References

- [TEAMS-FEATURE-REMEDIATION-PLAN.md](../../06-deploy/TEAMS-FEATURE-REMEDIATION-PLAN.md) - Original analysis
- [Data-Model-ERD.md](../../01-planning/04-Data-Model/Data-Model-ERD.md) - Database schema
- [OpenAPI Spec](../../01-planning/05-API-Design/) - API contract
- [ADR-002: Authentication Model](./ADR-002-Authentication-Model.md) - Auth patterns

---

## Document Control

| Field | Value |
|-------|-------|
| **Version** | 1.0.0 |
| **Date** | January 17, 2026 |
| **Author** | Architect + Backend Lead |
| **Status** | APPROVED |
| **CTO Approval** | ✅ Jan 17, 2026 |
