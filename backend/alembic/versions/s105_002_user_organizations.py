"""Sprint 105: Add user_organizations join table for multi-org support

Revision ID: s105_002_user_orgs
Revises: s105_001_performance_indexes
Create Date: 2026-01-25

This migration adds support for users belonging to multiple organizations
(GitHub-style multi-org membership). The existing users.organization_id
is kept as the "default/currently selected" organization.

Schema:
    user_organizations (new join table):
        - user_id: FK to users.id
        - organization_id: FK to organizations.id
        - role: User's role in this organization (owner, admin, member)
        - joined_at: When user joined this organization
        - PRIMARY KEY: (user_id, organization_id)
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 's105_002_user_orgs'
down_revision = 's105_001_performance_indexes'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create user_organizations join table
    op.create_table(
        'user_organizations',
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role', sa.String(50), nullable=False, server_default='member'),
        sa.Column('joined_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id', 'organization_id'),
    )

    # Create indexes for fast lookups
    op.create_index('idx_user_orgs_user', 'user_organizations', ['user_id'])
    op.create_index('idx_user_orgs_org', 'user_organizations', ['organization_id'])

    # Migrate existing data: copy users.organization_id to user_organizations
    # This ensures existing users maintain their organization membership
    op.execute("""
        INSERT INTO user_organizations (user_id, organization_id, role, joined_at)
        SELECT id, organization_id, 'member', COALESCE(created_at, NOW())
        FROM users
        WHERE organization_id IS NOT NULL
        ON CONFLICT (user_id, organization_id) DO NOTHING
    """)


def downgrade() -> None:
    op.drop_index('idx_user_orgs_org', table_name='user_organizations')
    op.drop_index('idx_user_orgs_user', table_name='user_organizations')
    op.drop_table('user_organizations')
