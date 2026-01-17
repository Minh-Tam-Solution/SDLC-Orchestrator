"""Sprint 70: Add organizations, teams, team_members tables

Revision ID: s70_teams_foundation
Revises: s71_fix_fallback_order
Create Date: 2026-01-20

Sprint 70 - Teams Feature Foundation
Reference: ADR-028-Teams-Feature-Architecture
Reference: Teams-Data-Model-Specification.md

This migration creates:
1. organizations table - Multi-tenant root entity
2. teams table - Collaboration unit within organization
3. team_members table - User-Team many-to-many with roles
4. Add organization_id FK to users table
5. Add team_id FK to projects table

SASE Alignment (CTO R1/R2):
- ai_agent role for SE4A (Agent Executor)
- member_type column (human/ai_agent)
- Constraint: AI agents cannot be owner/admin
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 's70_teams_foundation'
down_revision = 's71_fix_fallback_order'
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
        sa.Column('settings', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug', name='organizations_slug_unique'),
        sa.CheckConstraint("plan IN ('free', 'starter', 'pro', 'enterprise')", name='organizations_plan_check')
    )
    op.create_index('idx_organizations_slug', 'organizations', ['slug'])
    op.create_index('idx_organizations_plan', 'organizations', ['plan'])
    op.create_index('idx_organizations_created_at', 'organizations', [sa.text('created_at DESC')])

    # 2. Create teams table
    op.create_table(
        'teams',
        sa.Column('id', sa.UUID(), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('settings', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(
            ['organization_id'], ['organizations.id'],
            ondelete='CASCADE', name='teams_organization_fk'
        ),
        sa.UniqueConstraint('organization_id', 'slug', name='teams_org_slug_unique')
    )
    op.create_index('idx_teams_organization_id', 'teams', ['organization_id'])
    op.create_index('idx_teams_slug', 'teams', ['slug'])
    op.create_index('idx_teams_created_at', 'teams', [sa.text('created_at DESC')])

    # 3. Create team_members table (with CTO R1/R2 - AI Agent Support)
    op.create_table(
        'team_members',
        sa.Column('id', sa.UUID(), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('team_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('role', sa.String(50), nullable=False, server_default='member'),
        sa.Column('member_type', sa.String(20), nullable=False, server_default='human'),
        sa.Column('joined_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(
            ['team_id'], ['teams.id'],
            ondelete='CASCADE', name='team_members_team_fk'
        ),
        sa.ForeignKeyConstraint(
            ['user_id'], ['users.id'],
            ondelete='CASCADE', name='team_members_user_fk'
        ),
        sa.UniqueConstraint('team_id', 'user_id', name='team_members_unique'),
        # Role constraint: owner, admin, member, ai_agent
        sa.CheckConstraint(
            "role IN ('owner', 'admin', 'member', 'ai_agent')",
            name='team_members_role_check'
        ),
        # Member type constraint: human, ai_agent
        sa.CheckConstraint(
            "member_type IN ('human', 'ai_agent')",
            name='team_members_member_type_check'
        ),
        # SASE Principle: AI agents cannot be owners/admins (per SDLC 5.1.2)
        sa.CheckConstraint(
            "NOT (member_type = 'ai_agent' AND role IN ('owner', 'admin'))",
            name='team_members_ai_agent_role_check'
        )
    )
    op.create_index('idx_team_members_team_id', 'team_members', ['team_id'])
    op.create_index('idx_team_members_user_id', 'team_members', ['user_id'])
    op.create_index('idx_team_members_role', 'team_members', ['role'])
    op.create_index('idx_team_members_member_type', 'team_members', ['member_type'])

    # 4. Add organization_id to users table (nullable for migration)
    op.add_column('users', sa.Column('organization_id', sa.UUID(), nullable=True))
    op.create_foreign_key(
        'users_organization_fk',
        'users', 'organizations',
        ['organization_id'], ['id'],
        ondelete='SET NULL'
    )
    op.create_index('idx_users_organization_id', 'users', ['organization_id'])

    # 5. Add team_id to projects table (nullable for migration)
    op.add_column('projects', sa.Column('team_id', sa.UUID(), nullable=True))
    op.create_foreign_key(
        'projects_team_fk',
        'projects', 'teams',
        ['team_id'], ['id'],
        ondelete='SET NULL'
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

    # Drop new tables (in reverse order of dependencies)
    op.drop_table('team_members')
    op.drop_table('teams')
    op.drop_table('organizations')
