"""Add SDLC 5.0.0 validation tables

Revision ID: j5e6f7g8h9i0
Revises: i4d5e6f7g8h9
Create Date: 2025-12-05 14:00:00.000000

Sprint 30 Day 3: Web API Endpoint for SDLC Structure Validation
Authority: Backend Lead + CTO Approved
Framework: SDLC 5.0.0

Changes:
- Add sdlc_validations table for validation history
- Add sdlc_validation_issues table for detailed issues
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


# revision identifiers, used by Alembic.
revision: str = 'j5e6f7g8h9i0'
down_revision: Union[str, None] = 'i4d5e6f7g8h9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create SDLC validation tables."""
    conn = op.get_bind()

    # Create enums using raw SQL with IF NOT EXISTS
    conn.execute(sa.text("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'sdlctier') THEN
                CREATE TYPE sdlctier AS ENUM ('lite', 'standard', 'professional', 'enterprise');
            END IF;
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'validationtrigger') THEN
                CREATE TYPE validationtrigger AS ENUM ('manual', 'api', 'webhook', 'cicd', 'precommit', 'scheduled');
            END IF;
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'issueseverity') THEN
                CREATE TYPE issueseverity AS ENUM ('error', 'warning', 'info');
            END IF;
        END$$;
    """))

    # Create sdlc_validations table
    conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS sdlc_validations (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            validated_by UUID REFERENCES users(id) ON DELETE SET NULL,
            trigger_type VARCHAR(50) NOT NULL DEFAULT 'api',
            tier VARCHAR(20) NOT NULL DEFAULT 'standard',
            tier_detected BOOLEAN NOT NULL DEFAULT FALSE,
            is_compliant BOOLEAN NOT NULL DEFAULT FALSE,
            compliance_score INTEGER NOT NULL DEFAULT 0,
            stages_found INTEGER NOT NULL DEFAULT 0,
            stages_required INTEGER NOT NULL DEFAULT 0,
            stages_detail JSONB NOT NULL DEFAULT '[]',
            stages_missing JSONB NOT NULL DEFAULT '[]',
            p0_status JSONB DEFAULT '{}',
            error_count INTEGER NOT NULL DEFAULT 0,
            warning_count INTEGER NOT NULL DEFAULT 0,
            issues JSONB NOT NULL DEFAULT '[]',
            validation_time_ms FLOAT,
            validated_at TIMESTAMP NOT NULL DEFAULT NOW(),
            docs_root VARCHAR(500) NOT NULL DEFAULT 'docs',
            config_file VARCHAR(500),
            strict_mode BOOLEAN NOT NULL DEFAULT FALSE,
            result_hash VARCHAR(64),
            git_commit VARCHAR(40),
            git_branch VARCHAR(255),
            created_at TIMESTAMP NOT NULL DEFAULT NOW()
        );
    """))

    # Create sdlc_validation_issues table
    conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS sdlc_validation_issues (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            validation_id UUID NOT NULL REFERENCES sdlc_validations(id) ON DELETE CASCADE,
            project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            severity VARCHAR(20) NOT NULL DEFAULT 'warning',
            code VARCHAR(100) NOT NULL,
            message TEXT NOT NULL,
            location VARCHAR(1000),
            suggestion TEXT,
            created_at TIMESTAMP NOT NULL DEFAULT NOW()
        );
    """))

    # Create indexes for performance
    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS idx_sdlc_validations_project_id ON sdlc_validations(project_id);
        CREATE INDEX IF NOT EXISTS idx_sdlc_validations_validated_at ON sdlc_validations(validated_at DESC);
        CREATE INDEX IF NOT EXISTS idx_sdlc_validations_compliance_score ON sdlc_validations(compliance_score);
        CREATE INDEX IF NOT EXISTS idx_sdlc_validations_tier ON sdlc_validations(tier);
        CREATE INDEX IF NOT EXISTS idx_sdlc_validations_is_compliant ON sdlc_validations(is_compliant);
        CREATE INDEX IF NOT EXISTS idx_sdlc_validations_validated_by ON sdlc_validations(validated_by);

        CREATE INDEX IF NOT EXISTS idx_sdlc_validation_issues_validation_id ON sdlc_validation_issues(validation_id);
        CREATE INDEX IF NOT EXISTS idx_sdlc_validation_issues_project_id ON sdlc_validation_issues(project_id);
        CREATE INDEX IF NOT EXISTS idx_sdlc_validation_issues_severity ON sdlc_validation_issues(severity);
        CREATE INDEX IF NOT EXISTS idx_sdlc_validation_issues_code ON sdlc_validation_issues(code);
    """))

    # Add comments
    conn.execute(sa.text("""
        COMMENT ON TABLE sdlc_validations IS 'SDLC 5.0.0 folder structure validation history';
        COMMENT ON COLUMN sdlc_validations.tier IS 'Project tier: lite, standard, professional, enterprise';
        COMMENT ON COLUMN sdlc_validations.tier_detected IS 'True if tier was auto-detected';
        COMMENT ON COLUMN sdlc_validations.p0_status IS 'P0 artifact status for professional/enterprise tiers';
        COMMENT ON COLUMN sdlc_validations.result_hash IS 'SHA256 hash for result integrity';

        COMMENT ON TABLE sdlc_validation_issues IS 'Individual SDLC validation issues';
        COMMENT ON COLUMN sdlc_validation_issues.code IS 'Issue code (e.g., MISSING_STAGE, P0_NOT_FOUND)';
    """))


def downgrade() -> None:
    """Drop SDLC validation tables."""
    conn = op.get_bind()

    # Drop tables
    conn.execute(sa.text("DROP TABLE IF EXISTS sdlc_validation_issues CASCADE;"))
    conn.execute(sa.text("DROP TABLE IF EXISTS sdlc_validations CASCADE;"))

    # Drop enums
    conn.execute(sa.text("""
        DROP TYPE IF EXISTS issueseverity CASCADE;
        DROP TYPE IF EXISTS validationtrigger CASCADE;
        DROP TYPE IF EXISTS sdlctier CASCADE;
    """))
