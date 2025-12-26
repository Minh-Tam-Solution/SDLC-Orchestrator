"""
Add soft delete support to users table.

Revision ID: n9i0j1k2l3m4
Revises: m8h9i0j1k2l3
Create Date: 2025-12-17

SDLC 5.1.1 Compliance:
- Sprint 40: Admin Panel Full CRUD Users (CTO Approved Dec 17, 2025)
- Soft delete pattern: deleted_at timestamp for audit trail
- deleted_by FK for accountability (who performed the deletion)
- Supports GDPR compliance (right to be forgotten with audit trail)

Security:
- Soft delete preserves audit trail (cannot hard delete users)
- deleted_by tracks admin accountability
- Indexed for query performance (filter active users)
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'n9i0j1k2l3m4'
down_revision = 'm8h9i0j1k2l3'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add soft delete columns to users table."""

    # 1. Add deleted_at timestamp column (nullable, indexed)
    op.add_column(
        'users',
        sa.Column('deleted_at', sa.DateTime(), nullable=True)
    )

    # 2. Add deleted_by foreign key to track who performed the deletion
    op.add_column(
        'users',
        sa.Column('deleted_by', sa.UUID(), nullable=True)
    )

    # 3. Create foreign key constraint: deleted_by -> users.id
    op.create_foreign_key(
        'fk_users_deleted_by',
        'users',
        'users',
        ['deleted_by'],
        ['id'],
        ondelete='SET NULL'  # If admin is deleted, preserve the record
    )

    # 4. Create index on deleted_at for filtering active users
    # Query pattern: WHERE deleted_at IS NULL (active users)
    op.create_index(
        'ix_users_deleted_at',
        'users',
        ['deleted_at']
    )

    # 5. Create composite index for active user queries (is_active + deleted_at)
    # Query pattern: WHERE is_active = true AND deleted_at IS NULL
    op.create_index(
        'ix_users_active_not_deleted',
        'users',
        ['is_active', 'deleted_at']
    )


def downgrade() -> None:
    """Remove soft delete columns from users table."""

    # Drop indexes first
    op.drop_index('ix_users_active_not_deleted', table_name='users')
    op.drop_index('ix_users_deleted_at', table_name='users')

    # Drop foreign key constraint
    op.drop_constraint('fk_users_deleted_by', 'users', type_='foreignkey')

    # Drop columns
    op.drop_column('users', 'deleted_by')
    op.drop_column('users', 'deleted_at')
