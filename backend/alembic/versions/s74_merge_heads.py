"""Merge Sprint 70 BUG8 and Sprint 73 migration heads

Revision ID: s74_merge_heads
Revises: s70_bug8_user_role, s73_teams_data_migration
Create Date: 2026-01-18 09:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 's74_merge_heads'
down_revision = ('s70_bug8_user_role', 's73_teams_data_migration')
branch_labels = None
depends_on = None


def upgrade():
    # This is a merge migration - no schema changes
    pass


def downgrade():
    # This is a merge migration - no schema changes
    pass
