"""Sprint 160: stub migration (file was lost, DB already applied)

Revision ID: s160_001
Revises: s159_001
Create Date: 2026-02-06 08:00:00.000000
"""
from alembic import op

revision = 's160_001'
down_revision = 's159_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass  # Already applied in DB — stub only to repair revision chain


def downgrade() -> None:
    pass
