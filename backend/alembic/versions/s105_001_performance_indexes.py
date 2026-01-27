"""Sprint 105: Performance Indexes for Launch Readiness

Revision ID: s105_001_performance_indexes
Revises: s104_001_maturity_assessments
Create Date: 2026-01-24 10:00:00.000000

Performance optimization for production launch.
Only creates basic safe indexes.

Reference: docs/04-build/02-Sprint-Plans/SPRINT-105-DESIGN.md
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 's105_001_performance_indexes'
down_revision = 's104_001_maturity_assessments'
branch_labels = None
depends_on = None


def upgrade():
    # =========================================================================
    # Performance Indexes for Production Launch
    # Safe indexes only - columns verified to exist
    # =========================================================================

    # -------------------------------------------------------------------------
    # 1. User email lookup (already verified)
    # -------------------------------------------------------------------------
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_users_email_active
        ON users (email)
        WHERE deleted_at IS NULL AND is_active = TRUE;
    """)

    # -------------------------------------------------------------------------
    # 2. Gates by project (verified in schema)
    # -------------------------------------------------------------------------
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_gates_project_created
        ON gates (project_id, created_at DESC);
    """)

    # -------------------------------------------------------------------------
    # 3. Maturity Assessment Indexes (Sprint 104 table)
    # -------------------------------------------------------------------------
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_maturity_level
        ON maturity_assessments (level, assessed_at DESC);
    """)


def downgrade():
    op.execute("DROP INDEX IF EXISTS idx_maturity_level;")
    op.execute("DROP INDEX IF EXISTS idx_gates_project_created;")
    op.execute("DROP INDEX IF EXISTS idx_users_email_active;")
