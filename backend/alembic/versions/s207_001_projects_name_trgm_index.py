"""Sprint 207: pg_trgm GIN index on projects.name for workspace ILIKE search.

Day 1 blocker — must run before /workspace set <name> works.
ADR-067 D-067-02: ILIKE search degrades to sequential scan without this index.

Revision ID: s207_001
Revises: s206_001
Create Date: 2026-02-26
"""

from alembic import op

revision = "s207_001"
down_revision = "s206_001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.execute(
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_projects_name_trgm "
        "ON projects USING GIN (name gin_trgm_ops)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX CONCURRENTLY IF EXISTS idx_projects_name_trgm")
