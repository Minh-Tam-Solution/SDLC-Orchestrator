"""Sprint 105: Performance Indexes for Launch Readiness

Revision ID: s105_001_performance_indexes
Revises: s104_001_maturity_assessments
Create Date: 2026-01-24 10:00:00.000000

Performance optimization for production launch:
- Optimize PR queries (project + status)
- Optimize Evidence Vault queries (project + type)
- Optimize Learning queries (project + date)
- Optimize Consultation queries (status + date)
- Optimize Maturity queries (project + date)

Target: p95 latency <2s under 1000 concurrent users

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
    #
    # These indexes optimize the most common query patterns:
    # - PR listing by project and status
    # - Evidence retrieval by project and type
    # - Learning aggregation by project and date
    # - Consultation status filtering
    # - Maturity assessment history
    # =========================================================================

    # -------------------------------------------------------------------------
    # 1. Pull Request Indexes
    # Optimize: GET /api/v1/projects/{id}/prs?status=open
    # -------------------------------------------------------------------------
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_prs_project_status
        ON pull_requests (project_id, status)
        WHERE deleted_at IS NULL;
    """)

    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_prs_created_at
        ON pull_requests (created_at DESC)
        WHERE deleted_at IS NULL;
    """)

    # -------------------------------------------------------------------------
    # 2. Evidence Vault Indexes
    # Optimize: GET /api/v1/evidence/projects/{id}?type=VCR
    # -------------------------------------------------------------------------
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_evidence_project_type
        ON evidence (project_id, evidence_type)
        WHERE deleted_at IS NULL;
    """)

    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_evidence_created_at
        ON evidence (created_at DESC)
        WHERE deleted_at IS NULL;
    """)

    # -------------------------------------------------------------------------
    # 3. PR Learnings Indexes (Sprint 100)
    # Optimize: Monthly aggregation, hint generation
    # -------------------------------------------------------------------------
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_learnings_project_created
        ON pr_learnings (project_id, created_at DESC);
    """)

    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_learnings_category
        ON pr_learnings (category, created_at DESC);
    """)

    # -------------------------------------------------------------------------
    # 4. Consultation Requests Indexes (Sprint 101)
    # Optimize: CRP dashboard, pending consultations list
    # -------------------------------------------------------------------------
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_consultations_status
        ON consultation_requests (status, created_at DESC);
    """)

    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_consultations_project
        ON consultation_requests (project_id, status);
    """)

    # -------------------------------------------------------------------------
    # 5. Risk Analysis Indexes (Sprint 101)
    # Optimize: Risk analysis by project and risk level
    # -------------------------------------------------------------------------
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_risk_analysis_project
        ON risk_analyses (project_id, created_at DESC);
    """)

    # -------------------------------------------------------------------------
    # 6. MRP Validation Indexes (Sprint 102)
    # Optimize: MRP validation history by project
    # -------------------------------------------------------------------------
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_mrp_project_created
        ON mrp_validations (project_id, created_at DESC);
    """)

    # -------------------------------------------------------------------------
    # 7. Maturity Assessment Indexes (Sprint 104)
    # Already created in s104 migration, but add level index
    # -------------------------------------------------------------------------
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_maturity_level
        ON maturity_assessments (level, assessed_at DESC);
    """)

    # -------------------------------------------------------------------------
    # 8. Framework Version Indexes (Sprint 103)
    # Already has basic indexes, add version index
    # -------------------------------------------------------------------------
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_framework_version
        ON framework_versions (version, applied_at DESC);
    """)

    # -------------------------------------------------------------------------
    # 9. Project Query Optimization
    # Optimize: Project listing with filters
    # -------------------------------------------------------------------------
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_projects_owner_active
        ON projects (owner_id, is_active)
        WHERE deleted_at IS NULL;
    """)

    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_projects_tier
        ON projects (tier, created_at DESC)
        WHERE deleted_at IS NULL;
    """)

    # -------------------------------------------------------------------------
    # 10. User Query Optimization
    # Optimize: User lookup by email
    # -------------------------------------------------------------------------
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_email_lower
        ON users (LOWER(email))
        WHERE deleted_at IS NULL AND is_active = TRUE;
    """)

    # Add table comments
    op.execute("""
        COMMENT ON INDEX idx_prs_project_status IS
        'Sprint 105: Optimize PR listing by project and status';

        COMMENT ON INDEX idx_evidence_project_type IS
        'Sprint 105: Optimize Evidence Vault queries';

        COMMENT ON INDEX idx_learnings_project_created IS
        'Sprint 105: Optimize learning aggregation';

        COMMENT ON INDEX idx_consultations_status IS
        'Sprint 105: Optimize CRP dashboard queries';
    """)


def downgrade():
    # Drop indexes in reverse order
    op.execute("DROP INDEX IF EXISTS idx_users_email_lower;")
    op.execute("DROP INDEX IF EXISTS idx_projects_tier;")
    op.execute("DROP INDEX IF EXISTS idx_projects_owner_active;")
    op.execute("DROP INDEX IF EXISTS idx_framework_version;")
    op.execute("DROP INDEX IF EXISTS idx_maturity_level;")
    op.execute("DROP INDEX IF EXISTS idx_mrp_project_created;")
    op.execute("DROP INDEX IF EXISTS idx_risk_analysis_project;")
    op.execute("DROP INDEX IF EXISTS idx_consultations_project;")
    op.execute("DROP INDEX IF EXISTS idx_consultations_status;")
    op.execute("DROP INDEX IF EXISTS idx_learnings_category;")
    op.execute("DROP INDEX IF EXISTS idx_learnings_project_created;")
    op.execute("DROP INDEX IF EXISTS idx_evidence_created_at;")
    op.execute("DROP INDEX IF EXISTS idx_evidence_project_type;")
    op.execute("DROP INDEX IF EXISTS idx_prs_created_at;")
    op.execute("DROP INDEX IF EXISTS idx_prs_project_status;")
