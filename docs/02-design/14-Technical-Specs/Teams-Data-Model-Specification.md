# Teams Data Model Specification
## Database Schema for Organizations, Teams, and Team Members

**Version**: 1.0.0
**Date**: January 17, 2026
**Status**: APPROVED
**Author**: Backend Lead
**Reference**: ADR-028-Teams-Feature-Architecture
**Sprint**: Sprint 70 (Jan 20 - Feb 3, 2026)

---

## 1. Overview

This specification defines the database schema for multi-tenant team management in SDLC Orchestrator. It introduces 3 new tables and modifies 2 existing tables.

### Tables Summary

| Table | Type | Purpose |
|-------|------|---------|
| `organizations` | NEW | Multi-tenant root, billing entity |
| `teams` | NEW | Collaboration unit within organization |
| `team_members` | NEW | User-Team many-to-many relationship |
| `users` | MODIFIED | Add `organization_id` FK |
| `projects` | MODIFIED | Add `team_id` FK |

---

## 2. Table Definitions

### 2.1 organizations

Root entity for multi-tenancy. Every user and team belongs to exactly one organization.

```sql
CREATE TABLE organizations (
    -- Primary Key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Core Fields
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) NOT NULL,

    -- Plan & Billing
    plan VARCHAR(50) NOT NULL DEFAULT 'free',

    -- Settings (JSONB for flexibility)
    settings JSONB NOT NULL DEFAULT '{}',

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    -- Constraints
    CONSTRAINT organizations_slug_unique UNIQUE (slug),
    CONSTRAINT organizations_plan_check CHECK (plan IN ('free', 'pro', 'enterprise'))
);

-- Indexes
CREATE INDEX idx_organizations_slug ON organizations(slug);
CREATE INDEX idx_organizations_plan ON organizations(plan);
CREATE INDEX idx_organizations_created_at ON organizations(created_at DESC);
```

#### Field Definitions

| Field | Type | Nullable | Default | Description |
|-------|------|----------|---------|-------------|
| `id` | UUID | NO | gen_random_uuid() | Primary key |
| `name` | VARCHAR(255) | NO | - | Display name (e.g., "Acme Corp") |
| `slug` | VARCHAR(100) | NO | - | URL-safe identifier (e.g., "acme-corp") |
| `plan` | VARCHAR(50) | NO | 'free' | Subscription plan |
| `settings` | JSONB | NO | '{}' | Organization-wide settings |
| `created_at` | TIMESTAMPTZ | NO | NOW() | Creation timestamp |
| `updated_at` | TIMESTAMPTZ | NO | NOW() | Last update timestamp |

#### Settings JSONB Schema

```json
{
  "default_policy_pack": "string | null",
  "require_mfa": "boolean (default: false)",
  "allowed_domains": "string[] (email domains)",
  "max_teams": "number (default: unlimited)",
  "max_projects_per_team": "number (default: unlimited)",
  "branding": {
    "logo_url": "string | null",
    "primary_color": "string (hex)"
  }
}
```

### 2.2 teams

Collaboration unit within an organization. Groups users and projects.

```sql
CREATE TABLE teams (
    -- Primary Key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Foreign Key
    organization_id UUID NOT NULL,

    -- Core Fields
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) NOT NULL,
    description TEXT,

    -- Settings (JSONB for flexibility)
    settings JSONB NOT NULL DEFAULT '{}',

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    -- Constraints
    CONSTRAINT teams_organization_fk
        FOREIGN KEY (organization_id)
        REFERENCES organizations(id)
        ON DELETE CASCADE,
    CONSTRAINT teams_org_slug_unique
        UNIQUE (organization_id, slug)
);

-- Indexes
CREATE INDEX idx_teams_organization_id ON teams(organization_id);
CREATE INDEX idx_teams_slug ON teams(slug);
CREATE INDEX idx_teams_created_at ON teams(created_at DESC);
```

#### Field Definitions

| Field | Type | Nullable | Default | Description |
|-------|------|----------|---------|-------------|
| `id` | UUID | NO | gen_random_uuid() | Primary key |
| `organization_id` | UUID | NO | - | Parent organization |
| `name` | VARCHAR(255) | NO | - | Display name (e.g., "Backend Team") |
| `slug` | VARCHAR(100) | NO | - | URL-safe identifier (unique per org) |
| `description` | TEXT | YES | NULL | Team description |
| `settings` | JSONB | NO | '{}' | Team-specific settings |
| `created_at` | TIMESTAMPTZ | NO | NOW() | Creation timestamp |
| `updated_at` | TIMESTAMPTZ | NO | NOW() | Last update timestamp |

#### Settings JSONB Schema

```json
{
  "default_gate_approvers": "UUID[] (user IDs)",
  "notification_channel": "string (slack/email/webhook)",
  "webhook_url": "string | null",
  "auto_assign_projects": "boolean (default: false)"
}
```

### 2.3 team_members

Junction table for User-Team many-to-many relationship with role and member type.

```sql
CREATE TABLE team_members (
    -- Primary Key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Foreign Keys
    team_id UUID NOT NULL,
    user_id UUID NOT NULL,

    -- Role and Member Type (SE4H/SE4A support per CTO R1/R2)
    role VARCHAR(50) NOT NULL DEFAULT 'member',
    member_type VARCHAR(20) NOT NULL DEFAULT 'human',

    -- Timestamps
    joined_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    -- Constraints
    CONSTRAINT team_members_team_fk
        FOREIGN KEY (team_id)
        REFERENCES teams(id)
        ON DELETE CASCADE,
    CONSTRAINT team_members_user_fk
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE,
    CONSTRAINT team_members_unique
        UNIQUE (team_id, user_id),
    CONSTRAINT team_members_role_check
        CHECK (role IN ('owner', 'admin', 'member', 'ai_agent')),
    CONSTRAINT team_members_member_type_check
        CHECK (member_type IN ('human', 'ai_agent')),
    CONSTRAINT team_members_ai_agent_role_check
        CHECK (NOT (member_type = 'ai_agent' AND role IN ('owner', 'admin')))
);

-- Indexes
CREATE INDEX idx_team_members_team_id ON team_members(team_id);
CREATE INDEX idx_team_members_user_id ON team_members(user_id);
CREATE INDEX idx_team_members_role ON team_members(role);
CREATE INDEX idx_team_members_member_type ON team_members(member_type);
```

#### Field Definitions

| Field | Type | Nullable | Default | Description |
|-------|------|----------|---------|-------------|
| `id` | UUID | NO | gen_random_uuid() | Primary key |
| `team_id` | UUID | NO | - | Team reference |
| `user_id` | UUID | NO | - | User reference |
| `role` | VARCHAR(50) | NO | 'member' | Member role in team |
| `member_type` | VARCHAR(20) | NO | 'human' | SE4H (human) or SE4A (ai_agent) |
| `joined_at` | TIMESTAMPTZ | NO | NOW() | When user joined team |

#### Role Definitions (SASE Aligned - CTO R1)

| Role | SASE Role | Member Type | Description | Permissions |
|------|-----------|-------------|-------------|-------------|
| `owner` | SE4H (Agent Coach) | human | Team creator, VCR authority | Full control, delete team, transfer ownership, approve MRP |
| `admin` | SE4H (Agent Coach) | human | Team administrator | Manage members, settings, MentorScript maintenance |
| `member` | SE4H/SE4A | human | Regular team member | View team, contribute to projects, create MRP |
| `ai_agent` | SE4A (Agent Executor) | ai_agent | AI agent executor | Read-only BRS, create MRP/CRP, execute tasks |

#### Member Type Definitions (CTO R2)

| Member Type | Description | Allowed Roles | Constraints |
|-------------|-------------|---------------|-------------|
| `human` | Human team member | owner, admin, member | Full role access |
| `ai_agent` | AI agent (SE4A) | member, ai_agent | Cannot be owner/admin per SASE principles |

---

## 3. Schema Modifications

### 3.1 users Table Modification

Add `organization_id` foreign key to existing users table.

```sql
-- Add column (nullable first for migration)
ALTER TABLE users
ADD COLUMN organization_id UUID;

-- Add foreign key constraint
ALTER TABLE users
ADD CONSTRAINT users_organization_fk
    FOREIGN KEY (organization_id)
    REFERENCES organizations(id);

-- Add index
CREATE INDEX idx_users_organization_id ON users(organization_id);

-- After data migration, make NOT NULL
-- ALTER TABLE users ALTER COLUMN organization_id SET NOT NULL;
```

### 3.2 projects Table Modification

Add `team_id` foreign key to existing projects table.

```sql
-- Add column (nullable first for migration)
ALTER TABLE projects
ADD COLUMN team_id UUID;

-- Add foreign key constraint
ALTER TABLE projects
ADD CONSTRAINT projects_team_fk
    FOREIGN KEY (team_id)
    REFERENCES teams(id);

-- Add index
CREATE INDEX idx_projects_team_id ON projects(team_id);

-- After data migration, make NOT NULL
-- ALTER TABLE projects ALTER COLUMN team_id SET NOT NULL;
```

---

## 4. SQLAlchemy Models

### 4.1 Organization Model

```python
# backend/app/models/organization.py
from uuid import UUID, uuid4
from datetime import datetime
from sqlalchemy import String, Text, CheckConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

class Organization(Base):
    """
    Organization model - multi-tenant root entity.

    Represents a company or organization that contains teams and users.
    All billing and compliance is scoped at the organization level.
    """
    __tablename__ = "organizations"

    # Primary Key
    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
        doc="Unique identifier for the organization"
    )

    # Core Fields
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Display name of the organization"
    )
    slug: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
        doc="URL-safe identifier (unique globally)"
    )

    # Plan & Billing
    plan: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="free",
        doc="Subscription plan: free, pro, enterprise"
    )

    # Settings
    settings: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        doc="Organization-wide settings (JSONB)"
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=datetime.utcnow,
        doc="When organization was created"
    )
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        doc="When organization was last updated"
    )

    # Relationships
    teams: Mapped[list["Team"]] = relationship(
        "Team",
        back_populates="organization",
        cascade="all, delete-orphan",
        doc="Teams belonging to this organization"
    )
    users: Mapped[list["User"]] = relationship(
        "User",
        back_populates="organization",
        doc="Users belonging to this organization"
    )

    # Table constraints
    __table_args__ = (
        CheckConstraint(
            "plan IN ('free', 'pro', 'enterprise')",
            name="organizations_plan_check"
        ),
    )

    def __repr__(self) -> str:
        return f"<Organization(id={self.id}, name={self.name}, plan={self.plan})>"
```

### 4.2 Team Model

```python
# backend/app/models/team.py
from uuid import UUID, uuid4
from datetime import datetime
from sqlalchemy import String, Text, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

class Team(Base):
    """
    Team model - collaboration unit within an organization.

    Teams group users and projects together for collaboration.
    Each team has owners, admins, and members with different permissions.
    """
    __tablename__ = "teams"

    # Primary Key
    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
        doc="Unique identifier for the team"
    )

    # Foreign Key
    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Parent organization"
    )

    # Core Fields
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Display name of the team"
    )
    slug: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        doc="URL-safe identifier (unique per organization)"
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Team description"
    )

    # Settings
    settings: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        doc="Team-specific settings (JSONB)"
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=datetime.utcnow,
        doc="When team was created"
    )
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        doc="When team was last updated"
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization",
        back_populates="teams",
        doc="Parent organization"
    )
    members: Mapped[list["TeamMember"]] = relationship(
        "TeamMember",
        back_populates="team",
        cascade="all, delete-orphan",
        doc="Team membership records"
    )
    projects: Mapped[list["Project"]] = relationship(
        "Project",
        back_populates="team",
        doc="Projects belonging to this team"
    )

    # Table constraints
    __table_args__ = (
        UniqueConstraint(
            "organization_id", "slug",
            name="teams_org_slug_unique"
        ),
    )

    def __repr__(self) -> str:
        return f"<Team(id={self.id}, name={self.name}, org={self.organization_id})>"
```

### 4.3 TeamMember Model

```python
# backend/app/models/team_member.py
from uuid import UUID, uuid4
from datetime import datetime
from sqlalchemy import String, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

class TeamMember(Base):
    """
    TeamMember model - junction table for User-Team relationship.

    Represents a user's membership in a team with a specific role and member type.

    Roles (per SASE alignment):
      - owner: SE4H Coach with full VCR authority
      - admin: SE4H Coach for member/settings management
      - member: SE4H/SE4A for implementation work
      - ai_agent: SE4A Executor for autonomous tasks

    Member Types:
      - human: Human team member (can be any role)
      - ai_agent: AI agent (restricted to member/ai_agent roles per SASE)
    """
    __tablename__ = "team_members"

    # Primary Key
    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
        doc="Unique identifier for the membership"
    )

    # Foreign Keys
    team_id: Mapped[UUID] = mapped_column(
        ForeignKey("teams.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Team reference"
    )
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="User reference"
    )

    # Role and Member Type (CTO R1/R2 - SASE Alignment)
    role: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="member",
        index=True,
        doc="Member role: owner, admin, member, ai_agent"
    )
    member_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="human",
        index=True,
        doc="Member type: human (SE4H) or ai_agent (SE4A)"
    )

    # Timestamps
    joined_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=datetime.utcnow,
        doc="When user joined the team"
    )

    # Relationships
    team: Mapped["Team"] = relationship(
        "Team",
        back_populates="members",
        doc="Parent team"
    )
    user: Mapped["User"] = relationship(
        "User",
        back_populates="team_memberships",
        doc="Member user"
    )

    # Table constraints (SASE compliant)
    __table_args__ = (
        UniqueConstraint(
            "team_id", "user_id",
            name="team_members_unique"
        ),
        CheckConstraint(
            "role IN ('owner', 'admin', 'member', 'ai_agent')",
            name="team_members_role_check"
        ),
        CheckConstraint(
            "member_type IN ('human', 'ai_agent')",
            name="team_members_member_type_check"
        ),
        # SASE Principle: AI agents cannot be owners/admins (per SDLC 5.1.2)
        CheckConstraint(
            "NOT (member_type = 'ai_agent' AND role IN ('owner', 'admin'))",
            name="team_members_ai_agent_role_check"
        ),
    )

    @property
    def is_ai_agent(self) -> bool:
        """Check if this member is an AI agent (SE4A)."""
        return self.member_type == "ai_agent"

    @property
    def is_coach(self) -> bool:
        """Check if this member has SE4H (Coach) authority."""
        return self.role in ("owner", "admin") and self.member_type == "human"

    def __repr__(self) -> str:
        return f"<TeamMember(team={self.team_id}, user={self.user_id}, role={self.role}, type={self.member_type})>"
```

---

## 5. Alembic Migration

### Migration File: `s70_add_organizations_teams.py`

```python
"""Add organizations, teams, team_members tables

Revision ID: s70_add_orgs_teams
Revises: [previous_revision]
Create Date: 2026-01-17

Sprint 70 - Teams Feature Foundation
Reference: ADR-028-Teams-Feature-Architecture
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 's70_add_orgs_teams'
down_revision = '[previous_revision]'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Create organizations table
    op.create_table(
        'organizations',
        sa.Column('id', sa.UUID(), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(100), nullable=False),
        sa.Column('plan', sa.String(50), nullable=False, server_default='free'),
        sa.Column('settings', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug', name='organizations_slug_unique'),
        sa.CheckConstraint("plan IN ('free', 'pro', 'enterprise')", name='organizations_plan_check')
    )
    op.create_index('idx_organizations_slug', 'organizations', ['slug'])
    op.create_index('idx_organizations_plan', 'organizations', ['plan'])
    op.create_index('idx_organizations_created_at', 'organizations', ['created_at'])

    # 2. Create teams table
    op.create_table(
        'teams',
        sa.Column('id', sa.UUID(), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('settings', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE', name='teams_organization_fk'),
        sa.UniqueConstraint('organization_id', 'slug', name='teams_org_slug_unique')
    )
    op.create_index('idx_teams_organization_id', 'teams', ['organization_id'])
    op.create_index('idx_teams_slug', 'teams', ['slug'])
    op.create_index('idx_teams_created_at', 'teams', ['created_at'])

    # 3. Create team_members table (with CTO R1/R2 - AI Agent Support)
    op.create_table(
        'team_members',
        sa.Column('id', sa.UUID(), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('team_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('role', sa.String(50), nullable=False, server_default='member'),
        sa.Column('member_type', sa.String(20), nullable=False, server_default='human'),
        sa.Column('joined_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['team_id'], ['teams.id'], ondelete='CASCADE', name='team_members_team_fk'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE', name='team_members_user_fk'),
        sa.UniqueConstraint('team_id', 'user_id', name='team_members_unique'),
        sa.CheckConstraint("role IN ('owner', 'admin', 'member', 'ai_agent')", name='team_members_role_check'),
        sa.CheckConstraint("member_type IN ('human', 'ai_agent')", name='team_members_member_type_check'),
        sa.CheckConstraint("NOT (member_type = 'ai_agent' AND role IN ('owner', 'admin'))", name='team_members_ai_agent_role_check')
    )
    op.create_index('idx_team_members_team_id', 'team_members', ['team_id'])
    op.create_index('idx_team_members_user_id', 'team_members', ['user_id'])
    op.create_index('idx_team_members_role', 'team_members', ['role'])
    op.create_index('idx_team_members_member_type', 'team_members', ['member_type'])

    # 4. Add organization_id to users (nullable for migration)
    op.add_column('users', sa.Column('organization_id', sa.UUID(), nullable=True))
    op.create_foreign_key(
        'users_organization_fk',
        'users', 'organizations',
        ['organization_id'], ['id']
    )
    op.create_index('idx_users_organization_id', 'users', ['organization_id'])

    # 5. Add team_id to projects (nullable for migration)
    op.add_column('projects', sa.Column('team_id', sa.UUID(), nullable=True))
    op.create_foreign_key(
        'projects_team_fk',
        'projects', 'teams',
        ['team_id'], ['id']
    )
    op.create_index('idx_projects_team_id', 'projects', ['team_id'])


def downgrade() -> None:
    # Remove FKs and columns from existing tables
    op.drop_constraint('projects_team_fk', 'projects', type_='foreignkey')
    op.drop_index('idx_projects_team_id', 'projects')
    op.drop_column('projects', 'team_id')

    op.drop_constraint('users_organization_fk', 'users', type_='foreignkey')
    op.drop_index('idx_users_organization_id', 'users')
    op.drop_column('users', 'organization_id')

    # Drop new tables
    op.drop_table('team_members')
    op.drop_table('teams')
    op.drop_table('organizations')
```

---

## 6. Data Migration Script

### Migrate Existing Data

```python
"""Migrate existing users and projects to default organization

Revision ID: s70_migrate_data
Revises: s70_add_orgs_teams
Create Date: 2026-01-17
"""
from alembic import op
from sqlalchemy import text

revision = 's70_migrate_data'
down_revision = 's70_add_orgs_teams'
branch_labels = None
depends_on = None

DEFAULT_ORG_ID = '00000000-0000-0000-0000-000000000001'
DEFAULT_TEAM_ID = '00000000-0000-0000-0000-000000000002'


def upgrade() -> None:
    conn = op.get_bind()

    # 1. Create default organization
    conn.execute(text("""
        INSERT INTO organizations (id, name, slug, plan, settings)
        VALUES (:id, 'Default Organization', 'default', 'free', '{}')
        ON CONFLICT (slug) DO NOTHING
    """), {'id': DEFAULT_ORG_ID})

    # 2. Create default team
    conn.execute(text("""
        INSERT INTO teams (id, organization_id, name, slug, description, settings)
        VALUES (:id, :org_id, 'Unassigned', 'unassigned', 'Default team for migrated projects', '{}')
        ON CONFLICT (organization_id, slug) DO NOTHING
    """), {'id': DEFAULT_TEAM_ID, 'org_id': DEFAULT_ORG_ID})

    # 3. Migrate users to default organization
    conn.execute(text("""
        UPDATE users
        SET organization_id = :org_id
        WHERE organization_id IS NULL
    """), {'org_id': DEFAULT_ORG_ID})

    # 4. Add all users as members of default team
    conn.execute(text("""
        INSERT INTO team_members (team_id, user_id, role)
        SELECT :team_id, id, 'member'
        FROM users
        WHERE id NOT IN (
            SELECT user_id FROM team_members WHERE team_id = :team_id
        )
    """), {'team_id': DEFAULT_TEAM_ID})

    # 5. Migrate projects to default team
    conn.execute(text("""
        UPDATE projects
        SET team_id = :team_id
        WHERE team_id IS NULL
    """), {'team_id': DEFAULT_TEAM_ID})

    # 6. Make columns NOT NULL
    op.alter_column('users', 'organization_id', nullable=False)
    op.alter_column('projects', 'team_id', nullable=False)


def downgrade() -> None:
    # Make columns nullable again
    op.alter_column('users', 'organization_id', nullable=True)
    op.alter_column('projects', 'team_id', nullable=True)

    # Remove data migration (optional, keeps data)
    pass
```

---

## 7. Pydantic Schemas

### Request/Response Schemas

```python
# backend/app/schemas/team.py
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

# ============== Organization Schemas ==============

class OrganizationBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=100, pattern=r'^[a-z0-9-]+$')

class OrganizationCreate(OrganizationBase):
    plan: str = Field(default="free", pattern=r'^(free|pro|enterprise)$')

class OrganizationUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    plan: str | None = Field(None, pattern=r'^(free|pro|enterprise)$')
    settings: dict | None = None

class OrganizationResponse(OrganizationBase):
    id: UUID
    plan: str
    settings: dict
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# ============== Team Schemas ==============

class TeamBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=100, pattern=r'^[a-z0-9-]+$')
    description: str | None = None

class TeamCreate(TeamBase):
    organization_id: UUID

class TeamUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    settings: dict | None = None

class TeamResponse(TeamBase):
    id: UUID
    organization_id: UUID
    settings: dict
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class TeamDetailResponse(TeamResponse):
    members_count: int
    projects_count: int
    members: list["TeamMemberResponse"] | None = None

# ============== TeamMember Schemas (CTO R1/R2 - AI Agent Support) ==============

class TeamMemberBase(BaseModel):
    role: str = Field(default="member", pattern=r'^(owner|admin|member|ai_agent)$')
    member_type: str = Field(default="human", pattern=r'^(human|ai_agent)$')

class TeamMemberAdd(TeamMemberBase):
    user_id: UUID

    @model_validator(mode='after')
    def validate_ai_agent_role(self) -> 'TeamMemberAdd':
        """SASE Principle: AI agents cannot be owners/admins."""
        if self.member_type == 'ai_agent' and self.role in ('owner', 'admin'):
            raise ValueError('AI agents cannot have owner or admin roles per SASE principles')
        return self

class TeamMemberRoleUpdate(BaseModel):
    role: str = Field(..., pattern=r'^(owner|admin|member|ai_agent)$')

class TeamMemberResponse(TeamMemberBase):
    id: UUID
    team_id: UUID
    user_id: UUID
    joined_at: datetime
    user: "UserBasicResponse | None" = None
    is_ai_agent: bool = False  # Computed from member_type
    is_coach: bool = False     # SE4H authority (human owner/admin)

    model_config = ConfigDict(from_attributes=True)

# ============== Statistics Schema ==============

class TeamStatistics(BaseModel):
    team_id: UUID
    members_count: int
    projects_count: int
    gates_total: int
    gates_passed: int
    gates_failed: int
    compliance_rate: float  # 0.0 - 1.0

# Forward reference updates
TeamDetailResponse.model_rebuild()
TeamMemberResponse.model_rebuild()
```

---

## 8. Validation Rules

### Organization Validation

| Field | Rule | Error Message |
|-------|------|---------------|
| `name` | 1-255 chars | "Name must be 1-255 characters" |
| `slug` | lowercase, alphanumeric, hyphens only | "Slug must contain only lowercase letters, numbers, and hyphens" |
| `slug` | globally unique | "Organization slug already exists" |
| `plan` | in ('free', 'pro', 'enterprise') | "Invalid plan" |

### Team Validation

| Field | Rule | Error Message |
|-------|------|---------------|
| `name` | 1-255 chars | "Name must be 1-255 characters" |
| `slug` | lowercase, alphanumeric, hyphens only | "Slug must contain only lowercase letters, numbers, and hyphens" |
| `slug` | unique per organization | "Team slug already exists in this organization" |
| `organization_id` | must exist | "Organization not found" |

### TeamMember Validation (Updated for CTO R1/R2)

| Field | Rule | Error Message |
|-------|------|---------------|
| `team_id` | must exist | "Team not found" |
| `user_id` | must exist | "User not found" |
| `user_id` | same organization | "User must belong to the same organization" |
| `role` | in ('owner', 'admin', 'member', 'ai_agent') | "Invalid role" |
| `member_type` | in ('human', 'ai_agent') | "Invalid member type" |
| `ai_agent` + `role` | AI agents cannot be owner/admin | "AI agents cannot have owner or admin roles per SASE principles" |
| unique | one membership per user per team | "User is already a member of this team" |

---

## 9. Success Criteria

- [ ] All 3 new tables created successfully
- [ ] Indexes created for all foreign keys
- [ ] Existing users migrated to default organization
- [ ] Existing projects assigned to default team
- [ ] `organization_id` NOT NULL on users
- [ ] `team_id` NOT NULL on projects
- [ ] SQLAlchemy models pass type checking (mypy)
- [ ] Unit tests for model relationships pass
- [ ] **CTO R1**: `ai_agent` role constraint works correctly
- [ ] **CTO R2**: `member_type` column with human/ai_agent values
- [ ] **SASE Compliance**: AI agents cannot be assigned owner/admin roles

---

## Document Control

| Field | Value |
|-------|-------|
| **Version** | 1.0.0 |
| **Date** | January 17, 2026 |
| **Author** | Backend Lead |
| **Reviewer** | CTO |
| **Status** | APPROVED |
