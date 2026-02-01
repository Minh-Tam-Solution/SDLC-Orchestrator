"""GitHub Integration - Sprint 129

Revision ID: s129_001
Revises: s128_001
Create Date: 2026-01-31 15:00:00.000000

Changes:
- Create github_installations table (GitHub App installations)
- Create github_repositories table (project-repo links)
- Create enums for installation_status and clone_status
- Add indexes for performance (installation_id lookup, project lookup)

Security:
- Installation tokens are NOT stored (generated on-demand via JWT)
- Multi-tenant isolation via installation_id scoping
- Audit trail (connected_by, connected_at, installed_by)

Reference: ADR-044-GitHub-Integration-Strategy.md
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 's129_001'
down_revision = 's128_001'
branch_labels = None
depends_on = None


def upgrade():
    """Create GitHub integration tables and related objects"""

    # Create installation_status enum (checkfirst=True to avoid duplicate error)
    installation_status = postgresql.ENUM(
        'active',
        'suspended',
        'uninstalled',
        name='github_installation_status',
        create_type=False
    )
    installation_status.create(op.get_bind(), checkfirst=True)

    # Create clone_status enum (checkfirst=True to avoid duplicate error)
    clone_status = postgresql.ENUM(
        'pending',
        'cloning',
        'cloned',
        'failed',
        name='github_clone_status',
        create_type=False
    )
    clone_status.create(op.get_bind(), checkfirst=True)

    # Create github_installations table
    op.create_table(
        'github_installations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('installation_id', sa.BigInteger, nullable=False, unique=True, comment='GitHub App installation ID'),
        sa.Column('account_type', sa.String(20), nullable=False, comment='user or organization'),
        sa.Column('account_login', sa.String(255), nullable=False, comment='GitHub username or org name'),
        sa.Column('account_avatar_url', sa.String(500), nullable=True, comment='GitHub avatar URL'),

        # User who installed the GitHub App
        sa.Column('installed_by', postgresql.UUID(as_uuid=True), nullable=False),

        # Status tracking
        sa.Column('status', installation_status, nullable=False, server_default='active'),

        # Timestamps
        sa.Column('installed_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('uninstalled_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('suspended_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),

        # Foreign keys
        sa.ForeignKeyConstraint(['installed_by'], ['users.id']),

        # Constraints
        sa.CheckConstraint("account_type IN ('user', 'organization')", name='valid_account_type'),

        comment='GitHub App installations tracking (ADR-044)'
    )

    # Create index for installation_id lookup (most common query)
    op.create_index(
        'idx_github_installation_id',
        'github_installations',
        ['installation_id']
    )

    # Create index for user lookup (list user's installations)
    op.create_index(
        'idx_github_installation_user',
        'github_installations',
        ['installed_by']
    )

    # Create index for active installations
    op.create_index(
        'idx_github_installation_active',
        'github_installations',
        ['status'],
        postgresql_where=sa.text("status = 'active'")
    )

    # Create github_repositories table (project-repo links)
    op.create_table(
        'github_repositories',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('installation_id', postgresql.UUID(as_uuid=True), nullable=False, comment='FK to github_installations'),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False, comment='FK to projects'),

        # GitHub repository info
        sa.Column('github_repo_id', sa.BigInteger, nullable=False, comment='GitHub internal repo ID'),
        sa.Column('owner', sa.String(255), nullable=False, comment='Repo owner (user/org)'),
        sa.Column('name', sa.String(255), nullable=False, comment='Repo name'),
        sa.Column('full_name', sa.String(512), nullable=False, comment='owner/name'),
        sa.Column('default_branch', sa.String(100), nullable=False, server_default='main'),
        sa.Column('is_private', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('html_url', sa.String(500), nullable=True, comment='GitHub web URL'),

        # Clone tracking
        sa.Column('local_path', sa.Text, nullable=True, comment='Path to local clone'),
        sa.Column('last_cloned_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('clone_status', clone_status, nullable=False, server_default='pending'),
        sa.Column('clone_error', sa.Text, nullable=True, comment='Last clone error message'),

        # Audit trail
        sa.Column('connected_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('connected_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('disconnected_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),

        # Foreign keys
        sa.ForeignKeyConstraint(['installation_id'], ['github_installations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['connected_by'], ['users.id']),

        comment='Project-GitHub repository links (ADR-044)'
    )

    # Create unique index for github_repo_id (one repo = one project)
    op.create_index(
        'idx_github_repo_id_unique',
        'github_repositories',
        ['github_repo_id'],
        unique=True
    )

    # Create unique index for project_id (one project = one repo)
    op.create_index(
        'idx_github_repo_project_unique',
        'github_repositories',
        ['project_id'],
        unique=True
    )

    # Create index for installation lookup
    op.create_index(
        'idx_github_repo_installation',
        'github_repositories',
        ['installation_id']
    )

    # Create index for full_name search
    op.create_index(
        'idx_github_repo_full_name',
        'github_repositories',
        ['full_name']
    )


def downgrade():
    """Drop GitHub integration tables and related objects"""

    # Drop indexes first
    op.drop_index('idx_github_repo_full_name', table_name='github_repositories')
    op.drop_index('idx_github_repo_installation', table_name='github_repositories')
    op.drop_index('idx_github_repo_project_unique', table_name='github_repositories')
    op.drop_index('idx_github_repo_id_unique', table_name='github_repositories')

    # Drop github_repositories table
    op.drop_table('github_repositories')

    # Drop github_installations indexes
    op.drop_index('idx_github_installation_active', table_name='github_installations')
    op.drop_index('idx_github_installation_user', table_name='github_installations')
    op.drop_index('idx_github_installation_id', table_name='github_installations')

    # Drop github_installations table
    op.drop_table('github_installations')

    # Drop enums
    op.execute('DROP TYPE github_clone_status')
    op.execute('DROP TYPE github_installation_status')
