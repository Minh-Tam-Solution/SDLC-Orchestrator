"""Team Invitation System - Sprint 128

Revision ID: s128_001
Revises: s123_001
Create Date: 2026-01-30 14:00:00.000000

Changes:
- Create team_invitations table with hash-based tokens
- Create invitation_status enum
- Add indexes for performance (hash lookup, email search, expiry)
- Add audit trail fields (ip_address, user_agent)

Security:
- Token stored as SHA256 hash (never raw token)
- Unique constraint on pending invitations per team+email
- Rate limiting enforced in application layer (no DB CHECK constraint)

Reference: ADR-043-Team-Invitation-System-Architecture.md
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 's128_001'
down_revision = 's123_001_compliance_validation'
branch_labels = None
depends_on = None


def upgrade():
    """Create team_invitations table and related objects"""

    # Create invitation_status enum (checkfirst=True to avoid duplicate error)
    invitation_status = postgresql.ENUM(
        'pending',
        'accepted',
        'declined',
        'expired',
        'cancelled',
        name='invitation_status',
        create_type=False
    )
    invitation_status.create(op.get_bind(), checkfirst=True)

    # Create team_invitations table
    op.create_table(
        'team_invitations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('team_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('invited_email', sa.String(255), nullable=False),
        sa.Column('invitation_token_hash', sa.String(64), nullable=False, unique=True, comment='SHA256 hash of invitation token'),
        sa.Column('role', sa.String(20), nullable=False, server_default='member'),
        sa.Column('status', invitation_status, nullable=False, server_default='pending'),
        sa.Column('invited_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('expires_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('accepted_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('declined_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),

        # Rate limiting (enforced in application, NOT DB constraint for flexibility)
        sa.Column('resend_count', sa.Integer, nullable=False, server_default='0', comment='Number of times invitation was resent'),
        sa.Column('last_resent_at', sa.TIMESTAMP(timezone=True), nullable=True),

        # Audit trail
        sa.Column('ip_address', postgresql.INET, nullable=True, comment='IP address of inviter'),
        sa.Column('user_agent', sa.Text, nullable=True, comment='User agent of inviter'),

        # Foreign keys
        sa.ForeignKeyConstraint(['team_id'], ['teams.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['invited_by'], ['users.id']),

        # Constraints
        sa.CheckConstraint('expires_at > created_at', name='valid_expiry'),

        comment='Team invitation system with hash-based tokens (ADR-043)'
    )

    # Create unique partial index for pending invitations
    # Allows multiple invitations to same email if previous ones are not pending
    op.execute("""
        CREATE UNIQUE INDEX idx_unique_pending_invitation
        ON team_invitations(team_id, invited_email)
        WHERE status = 'pending'
    """)

    # Create index for token hash lookup (most common query)
    op.create_index(
        'idx_invitation_hash',
        'team_invitations',
        ['invitation_token_hash'],
        postgresql_where=sa.text("status = 'pending'")
    )

    # Create index for email lookup (admin searches invitations by email)
    op.create_index(
        'idx_invitation_email',
        'team_invitations',
        ['team_id', 'invited_email']
    )

    # Create index for expiry cleanup (background job)
    op.create_index(
        'idx_invitation_expiry',
        'team_invitations',
        ['expires_at'],
        postgresql_where=sa.text("status = 'pending'")
    )

    # Create index for invited_by (audit queries)
    op.create_index(
        'idx_invitation_invited_by',
        'team_invitations',
        ['invited_by']
    )


def downgrade():
    """Drop team_invitations table and related objects"""

    # Drop indexes first
    op.drop_index('idx_invitation_invited_by', table_name='team_invitations')
    op.drop_index('idx_invitation_expiry', table_name='team_invitations')
    op.drop_index('idx_invitation_email', table_name='team_invitations')
    op.drop_index('idx_invitation_hash', table_name='team_invitations')
    op.execute('DROP INDEX IF EXISTS idx_unique_pending_invitation')

    # Drop table
    op.drop_table('team_invitations')

    # Drop enum
    op.execute('DROP TYPE invitation_status')
