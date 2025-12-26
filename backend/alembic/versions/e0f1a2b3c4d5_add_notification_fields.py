"""Add notification enhancement fields

Revision ID: e0f1a2b3c4d5
Revises: d9e0f1a2b3c4
Create Date: 2025-12-02 10:00:00.000000

Sprint 22 Day 1: Notification Service Enhancement
Authority: Backend Lead + CTO Approved

Changes:
- Add priority column to notifications
- Add project_id foreign key to notifications
- Add metadata JSONB column to notifications
- Add is_read boolean column to notifications
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'e0f1a2b3c4d5'
down_revision: Union[str, None] = 'd9e0f1a2b3c4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add priority column
    op.add_column(
        'notifications',
        sa.Column('priority', sa.String(length=20), nullable=True, server_default='medium')
    )

    # Add project_id foreign key
    op.add_column(
        'notifications',
        sa.Column('project_id', sa.UUID(), nullable=True)
    )
    op.create_foreign_key(
        'fk_notifications_project_id',
        'notifications',
        'projects',
        ['project_id'],
        ['id'],
        ondelete='CASCADE'
    )
    op.create_index(
        op.f('ix_notifications_project_id'),
        'notifications',
        ['project_id'],
        unique=False
    )

    # Add extra_data JSONB column (Note: 'metadata' is reserved in SQLAlchemy)
    op.add_column(
        'notifications',
        sa.Column('extra_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default='{}')
    )

    # Add is_read boolean column
    op.add_column(
        'notifications',
        sa.Column('is_read', sa.Boolean(), nullable=True, server_default='false')
    )
    op.create_index(
        op.f('ix_notifications_is_read'),
        'notifications',
        ['is_read'],
        unique=False
    )

    # Set NOT NULL after adding with defaults
    op.alter_column('notifications', 'priority', nullable=False)
    op.alter_column('notifications', 'is_read', nullable=False)


def downgrade() -> None:
    # Remove is_read column and index
    op.drop_index(op.f('ix_notifications_is_read'), table_name='notifications')
    op.drop_column('notifications', 'is_read')

    # Remove extra_data column
    op.drop_column('notifications', 'extra_data')

    # Remove project_id foreign key and index
    op.drop_index(op.f('ix_notifications_project_id'), table_name='notifications')
    op.drop_constraint('fk_notifications_project_id', 'notifications', type_='foreignkey')
    op.drop_column('notifications', 'project_id')

    # Remove priority column
    op.drop_column('notifications', 'priority')
