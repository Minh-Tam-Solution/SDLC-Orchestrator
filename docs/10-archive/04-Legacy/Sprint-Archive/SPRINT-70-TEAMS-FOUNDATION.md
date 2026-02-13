# Sprint 70: Teams Foundation - Models & Migration

**Sprint ID:** S70  
**Status:** ✅ COMPLETE  
**Duration:** 5 days (Jan 20-24, 2026)  
**Goal:** Create database schema and SQLAlchemy models for Organizations, Teams, TeamMembers  
**Completion Rate:** 100% (27/27 SP)  
**CTO Approval:** 9.2/10

---

## 🎯 Why Teams is THE Core Feature

> **"Built BY AI+Human Teams FOR AI+Human Teams"** - SDLC 5.1.2

### SDLC Orchestrator = Nhạc Trưởng (Conductor)

```
Without Platform (Single Developer):
  Human ──► AI Agent ──► SDLC Framework ──► Code
  (Chỉ cần nhắc AI đọc SDLC-Enterprise-Framework là đủ)

With Platform (Enterprise Teams):
  ┌─────────────────────────────────────────────────┐
  │            SDLC ORCHESTRATOR PLATFORM           │
  │                                                 │
  │  Team A ──┐                                     │
  │           │      BriefingScript (Intent)        │
  │  Team B ──┼────► MentorScript (Standards)       │
  │           │      MRP/VCR (Evidence/Approval)    │
  │  AI Agent─┘      Quality Gates (Governance)     │
  │                                                 │
  │  = COORDINATED GOVERNANCE + AUDIT TRAIL        │
  └─────────────────────────────────────────────────┘
```

### Team Collaboration per SDLC 5.1.2

| Concept | SDLC Framework | Orchestrator Implementation |
|---------|----------------|----------------------------|
| **SE4H** | Agent Coach (Human) | Team Owner/Admin roles |
| **SE4A** | Agent Executor (AI) | TeamMember with "ai_agent" type |
| **BriefingScript** | Intent specification | Project.briefs |
| **MentorScript** | Standards/patterns | Team.settings.mentor_scripts |
| **MRP** | Merge evidence | Gate.evidence |
| **VCR** | Approval record | Gate.approvals |
| **CRP** | Escalation | Gate.escalations |

---

## 📋 Sprint Overview

| Attribute | Value |
|-----------|-------|
| Sprint Number | 70 |
| Start Date | January 20, 2026 (Monday) |
| End Date | January 24, 2026 (Friday) |
| Working Days | 5 |
| Story Points | 24 (+3 for E2E Bug Fixes) |
| Team Capacity | Backend Dev (5d), Frontend Dev (0.5d), Tech Lead (1d) |

---

## 🎯 Sprint Goal

> Establish the database foundation for Teams feature by creating Organizations, Teams, and TeamMembers tables with proper relationships to existing Users and Projects tables.

---

## 📊 Sprint Backlog

### Epic: ADR-028 Teams Feature Implementation

#### Story 1: Database Migration (8 SP)
**As a** developer  
**I want** Organizations, Teams, and TeamMembers tables  
**So that** I can store team hierarchies and memberships

| Task ID | Task | Owner | Est | Status |
|---------|------|-------|-----|--------|
| S70-T01 | Create `organizations` table migration | Backend Dev | 2h | ✅ |
| S70-T02 | Create `teams` table migration | Backend Dev | 2h | ✅ |
| S70-T03 | Create `team_members` table migration | Backend Dev | 2h | ✅ |
| S70-T04 | Add `organization_id` FK to `users` table | Backend Dev | 1h | ✅ |
| S70-T05 | Add `team_id` FK to `projects` table | Backend Dev | 1h | ✅ |
| S70-T06 | Create indexes for performance | Backend Dev | 1h | ✅ |
| S70-T07 | Test migration up/down | Backend Dev | 1h | ✅ |

**Acceptance Criteria:**
- [x] `alembic upgrade head` succeeds without errors
- [x] `alembic downgrade -1` succeeds without errors
- [x] All tables created with correct columns and constraints
- [x] Foreign keys properly reference parent tables
- [x] Indexes created on frequently queried columns

---

#### Story 2: SQLAlchemy Models (8 SP)
**As a** developer  
**I want** SQLAlchemy ORM models for teams  
**So that** I can query and manipulate team data

| Task ID | Task | Owner | Est | Status |
|---------|------|-------|-----|--------|
| S70-T08 | Create `Organization` model | Backend Dev | 3h | ✅ |
| S70-T09 | Create `Team` model | Backend Dev | 3h | ✅ |
| S70-T10 | Create `TeamMember` model | Backend Dev | 2h | ✅ |
| S70-T11 | Update `User` model with org relationship | Backend Dev | 1h | ✅ |
| S70-T12 | Update `Project` model with team relationship | Backend Dev | 1h | ✅ |
| S70-T13 | Update `models/__init__.py` exports | Backend Dev | 0.5h | ✅ |
| S70-T14 | Add model docstrings | Backend Dev | 0.5h | ✅ |

**Acceptance Criteria:**
- [x] All models inherit from Base correctly
- [x] Relationships defined with back_populates
- [x] Type hints on all mapped columns
- [x] Unique constraints on (org_id, slug) for teams
- [x] Cascade delete configured correctly

---

#### Story 3: Pydantic Schemas (3 SP)
**As a** developer  
**I want** Pydantic schemas for API validation  
**So that** request/response data is properly typed

| Task ID | Task | Owner | Est | Status |
|---------|------|-------|-----|--------|
| S70-T15 | Create `OrganizationCreate/Update/Response` | Backend Dev | 2h | ⏳ |
| S70-T15 | Create `OrganizationCreate/Update/Response` | Backend Dev | 2h | ✅ |
| S70-T16 | Create `TeamCreate/Update/Response` | Backend Dev | 2h | ✅ |
| S70-T17 | Create `TeamMemberAdd/Response` | Backend Dev | 1h | ✅ |
| S70-T18 | Create `TeamStatistics` schema | Backend Dev | 1h | ✅ |

**Acceptance Criteria:**
- [x] All schemas match OpenAPI spec in `openapi.yaml`
- [x] Proper validation rules (min/max length, patterns)
- [x] Examples included for documentation
- [x] ConfigDict with from_attributes=True

---

#### Story 4: Unit Tests (2 SP)
**As a** developer  
**I want** unit tests for team models  
**So that** I can verify models work correctly

| Task ID | Task | Owner | Est | Status |
|---------|------|-------|-----|--------|
| S70-T19 | Test Organization CRUD | Backend Dev | 1.5h | ✅ |
| S70-T20 | Test Team CRUD | Backend Dev | 1.5h | ✅ |
| S70-T21 | Test TeamMember operations | Backend Dev | 1h | ✅ |
| S70-T22 | Test relationships and cascades | Backend Dev | 1h | ✅ |
| S70-T23 | Test constraint violations | Backend Dev | 1h | ✅ |

**Acceptance Criteria:**
- [x] 20+ unit tests passing
- [x] Test coverage ≥ 90% for new models
- [x] Edge cases covered (duplicates, nulls, cascades)

---

### Epic: E2E Bug Fixes (Non-Teams)

#### Story 5: BUG #2 - User name Field Fix (1 SP) 🐛
**Bug Reference:** E2E Test Report - BUG #2  
**Issue:** Design Doc specifies `full_name` but database has `name`  
**Impact:** API responses use `name` but design says `full_name`

| Task ID | Task | Owner | Est | Status |
|---------|------|-------|-----|--------|
| S70-T24 | Add migration to rename `name` → `full_name` | Backend Dev | 1h | ✅ |
| S70-T25 | Update User model with `full_name` field | Backend Dev | 0.5h | ✅ |
| S70-T26 | Update UserResponse schema with `full_name` | Backend Dev | 0.5h | ✅ |
| S70-T27 | Update frontend to use `full_name` | Frontend Dev | 1h | ✅ |
| S70-T28 | Test name field displays correctly | QA | 0.5h | ✅ |

**Acceptance Criteria:**
- [x] Database column is `full_name`
- [x] API returns `full_name` in user responses
- [x] Frontend displays full_name correctly
- [x] No breaking changes for existing users

---

#### Story 6: BUG #8 - User Role Field Missing (2 SP) 🐛
**Bug Reference:** E2E Test Report - BUG #8  
**Issue:** Design Doc specifies user `role` enum (ceo, cto, pm, dev, etc.) but database has no role column  
**Impact:** RBAC may not work as designed

| Task ID | Task | Owner | Est | Status |
|---------|------|-------|-----|--------|
| S70-T29 | Add migration for `role` column to users | Backend Dev | 1h | ✅ |
| S70-T30 | Update User model with `role` field | Backend Dev | 0.5h | ✅ |
| S70-T31 | Create RoleEnum (ceo, cto, pm, dev, qa, etc.) | Backend Dev | 0.5h | ✅ |
| S70-T32 | Update UserResponse/UserCreate schemas | Backend Dev | 0.5h | ✅ |
| S70-T33 | Add role selector to user profile/settings | Frontend Dev | 1.5h | ✅ |
| S70-T34 | Backfill existing users with default role | Backend Dev | 0.5h | ✅ |
| S70-T35 | Test RBAC with role field | QA | 1h | ✅ |

**Acceptance Criteria:**
- [x] `role` column exists in users table
- [x] RoleEnum: `ceo`, `cto`, `cpo`, `cio`, `cfo`, `em`, `tl`, `pm`, `dev`, `qa`, `devops`, `security`, `ba`, `designer`
- [x] Default role = `dev` for existing users
- [x] User can update their role in settings
- [x] Role displayed in user profile

---

## 📁 Files to Create/Modify

### New Files
```
backend/
├── alembic/versions/
│   └── 2026_01_20_s70_add_organizations_teams.py
├── app/models/
│   ├── organization.py
│   ├── team.py
│   └── team_member.py
├── app/schemas/
│   ├── organization.py
│   └── team.py
└── tests/unit/
    └── test_team_models.py
```

### Modified Files
```
backend/app/models/
├── __init__.py          # Export new models
├── user.py              # Add organization_id FK
└── project.py           # Add team_id FK
```

---

## 🗄️ Database Schema

### organizations
```sql
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    plan VARCHAR(50) DEFAULT 'free',      -- free, starter, pro, enterprise
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_organizations_slug ON organizations(slug);
```

### teams
```sql
CREATE TABLE teams (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) NOT NULL,
    description TEXT,
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(organization_id, slug)
);

CREATE INDEX idx_teams_organization ON teams(organization_id);
CREATE INDEX idx_teams_slug ON teams(organization_id, slug);
```

### team_members
```sql
CREATE TABLE team_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL DEFAULT 'member',  -- owner, admin, member
    joined_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(team_id, user_id)
);

CREATE INDEX idx_team_members_team ON team_members(team_id);
CREATE INDEX idx_team_members_user ON team_members(user_id);
```

### Alterations
```sql
-- Add organization_id to users (nullable for migration)
ALTER TABLE users ADD COLUMN organization_id UUID REFERENCES organizations(id);
CREATE INDEX idx_users_organization ON users(organization_id);

-- Add team_id to projects (nullable for migration)
ALTER TABLE projects ADD COLUMN team_id UUID REFERENCES teams(id);
CREATE INDEX idx_projects_team ON projects(team_id);
```

---

## 📝 Model Specifications

### Organization Model
```python
# backend/app/models/organization.py
from sqlalchemy import String, TIMESTAMP, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid import uuid4
from datetime import datetime

from app.db.base_class import Base

class Organization(Base):
    __tablename__ = "organizations"
    
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    plan: Mapped[str] = mapped_column(String(50), default="free")
    settings: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=func.now(), onupdate=func.now()
    )
    
    # Relationships
    teams: Mapped[list["Team"]] = relationship(
        "Team", back_populates="organization", cascade="all, delete-orphan"
    )
    users: Mapped[list["User"]] = relationship(
        "User", back_populates="organization"
    )
    
    def __repr__(self) -> str:
        return f"<Organization {self.slug}>"
```

### Team Model
```python
# backend/app/models/team.py
from sqlalchemy import String, Text, ForeignKey, TIMESTAMP, func, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid import uuid4, UUID as PyUUID
from datetime import datetime

from app.db.base_class import Base

class Team(Base):
    __tablename__ = "teams"
    __table_args__ = (
        UniqueConstraint("organization_id", "slug", name="uq_team_org_slug"),
    )
    
    id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid4
    )
    organization_id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    settings: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=func.now(), onupdate=func.now()
    )
    
    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization", back_populates="teams"
    )
    members: Mapped[list["TeamMember"]] = relationship(
        "TeamMember", back_populates="team", cascade="all, delete-orphan"
    )
    projects: Mapped[list["Project"]] = relationship(
        "Project", back_populates="team"
    )
    
    def __repr__(self) -> str:
        return f"<Team {self.slug}>"
```

### TeamMember Model
```python
# backend/app/models/team_member.py
from sqlalchemy import String, ForeignKey, TIMESTAMP, func, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid import uuid4, UUID as PyUUID
from datetime import datetime

from app.db.base_class import Base

class TeamMember(Base):
    __tablename__ = "team_members"
    __table_args__ = (
        UniqueConstraint("team_id", "user_id", name="uq_team_member"),
    )
    
    id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid4
    )
    team_id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teams.id", ondelete="CASCADE"),
        nullable=False
    )
    user_id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    role: Mapped[str] = mapped_column(
        String(50), 
        nullable=False, 
        default="member"
    )  # owner, admin, member
    joined_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=func.now()
    )
    
    # Relationships
    team: Mapped["Team"] = relationship("Team", back_populates="members")
    user: Mapped["User"] = relationship("User", back_populates="team_memberships")
    
    def __repr__(self) -> str:
        return f"<TeamMember team={self.team_id} user={self.user_id}>"
```

---

## ✅ Definition of Done

### Code Complete
- [ ] All migration files created and tested
- [ ] All 3 new model files created
- [ ] User and Project models updated with FKs
- [ ] All Pydantic schemas created
- [ ] `__init__.py` exports updated

### Tests
- [ ] `pytest backend/tests/unit/test_team_models.py` passes
- [ ] 20+ unit tests implemented
- [ ] No regression in existing tests (`pytest backend/tests/`)
- [ ] Coverage ≥ 90% for new code

### Documentation
- [ ] Model docstrings complete
- [ ] Schema examples included
- [ ] Migration notes documented

### Review
- [ ] Code review approved by Tech Lead
- [ ] PR merged to main branch
- [ ] Migration applied to staging

---

## 🚨 Risks & Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Migration breaks existing data | High | Low | Nullable FKs, staged migration |
| Model relationships incorrect | Medium | Medium | Thorough unit tests |
| Performance issues with joins | Medium | Low | Proper indexing |

---

## 📅 Daily Schedule

### Day 1 (Mon, Jan 20)
- [ ] Morning: Create migration file (S70-T01 to T03)
- [ ] Afternoon: Add FK columns (S70-T04 to T05)
- [ ] EOD: Test migration locally

### Day 2 (Tue, Jan 21)
- [ ] Morning: Create Organization model (S70-T08)
- [ ] Afternoon: Create Team model (S70-T09)
- [ ] EOD: Basic relationship testing

### Day 3 (Wed, Jan 22)
- [ ] Morning: Create TeamMember model (S70-T10)
- [ ] Afternoon: Update User/Project models (S70-T11, T12)
- [ ] EOD: All models complete

### Day 4 (Thu, Jan 23)
- [ ] Morning: Create Pydantic schemas (S70-T15 to T18)
- [ ] Afternoon: Write unit tests (S70-T19 to T23)
- [ ] EOD: All tests passing

### Day 5 (Fri, Jan 24)
- [ ] Morning: Final testing and edge cases
- [ ] Afternoon: Code review with Tech Lead
- [ ] EOD: PR merged, Sprint 70 complete

---

## 📈 Sprint Metrics

| Metric | Target | Actual |
|--------|--------|--------|
| Story Points Completed | 21 | TBD |
| Tasks Completed | 23/23 | TBD |
| Unit Tests Added | 20+ | TBD |
| Code Coverage | ≥90% | TBD |
| Bugs Found | 0 | TBD |

---

## 🔗 References

- [ADR-028: Teams Feature Remediation Plan](../../06-deploy/TEAMS-FEATURE-REMEDIATION-PLAN.md)
- [OpenAPI Spec - Teams](../../02-design/04-API-Design/openapi.yaml) (lines 695-770)
- [Database Schema Design](../../02-design/03-Database-Schema/database-schema.md)
- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/)
