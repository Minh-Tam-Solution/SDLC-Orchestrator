"""Sprint 123: Compliance Validation Service (SPEC-0013)

Revision ID: s123_001_compliance_validation
Revises: s120_001_context_authority_v2
Create Date: 2026-01-30 10:00:00.000000

Creates tables for Compliance Validation Service (SPEC-0013):
1. compliance_scores - SDLC 6.0.5 compliance scoring results
2. compliance_issues - Individual compliance issues found
3. folder_collision_checks - Stage folder collision detection results

Reference:
- SPEC-0013: Compliance Validation Service
- Sprint 123 Plan: SPRINT-123-COMPLIANCE-VALIDATION.md
- Source: PM/PJM Review of NQH-Bot + BFlow SDLC 6.0.5 Migrations
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 's123_001_compliance_validation'
down_revision = 's120_001_context_authority_v2'
branch_labels = None
depends_on = None


def upgrade():
    # =========================================================================
    # Table 1: compliance_scores
    # SDLC 6.0.5 compliance scoring with 10-category breakdown
    # =========================================================================
    op.create_table(
        'compliance_scores',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()'),
                  comment='Unique identifier for compliance score'),
        sa.Column('project_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('projects.id', ondelete='CASCADE'),
                  nullable=False, index=True,
                  comment='Project this score belongs to'),
        sa.Column('overall_score', sa.Integer(), nullable=False,
                  comment='Overall compliance score (0-100)'),
        sa.Column('category_scores', postgresql.JSONB(), nullable=False,
                  comment='Score breakdown: {"documentation_structure": 8, "specifications": 10, ...}'),
        sa.Column('issues_summary', postgresql.JSONB(), nullable=False,
                  comment='Issues count: {"total": 5, "critical": 1, "warning": 3, "info": 1}'),
        sa.Column('recommendations', postgresql.JSONB(), nullable=True,
                  comment='Array of recommendation strings'),
        sa.Column('calculated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now(),
                  comment='Score calculation timestamp'),
        sa.Column('calculated_by_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='SET NULL'),
                  nullable=True,
                  comment='User who triggered the calculation'),
        sa.Column('validation_version', sa.String(20), nullable=False,
                  server_default='1.0.0',
                  comment='Validator version used'),
        sa.Column('framework_version', sa.String(20), nullable=False,
                  server_default='6.0.5',
                  comment='SDLC Framework version validated against'),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True,
                  comment='Cache expiration timestamp'),
        sa.Column('scan_duration_ms', sa.Integer(), nullable=True,
                  comment='Scan duration in milliseconds'),
        sa.Column('files_scanned', sa.Integer(), nullable=True,
                  comment='Number of files scanned'),
        # Audit columns
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now(), onupdate=sa.func.now()),
        # Check constraints
        sa.CheckConstraint(
            'overall_score >= 0 AND overall_score <= 100',
            name='ck_compliance_scores_valid_score'
        ),
    )

    # Index for project-based queries (most recent first)
    op.create_index(
        'idx_compliance_scores_project_calculated',
        'compliance_scores',
        ['project_id', 'calculated_at'],
        postgresql_ops={'calculated_at': 'DESC'}
    )

    # Index for cache lookup (active scores)
    # Note: Cannot use NOW() in partial index as it's not IMMUTABLE
    # Filter expires_at > NOW() in application layer instead
    op.create_index(
        'idx_compliance_scores_active_cache',
        'compliance_scores',
        ['project_id', 'expires_at'],
        postgresql_where=sa.text('expires_at IS NOT NULL')
    )

    # BRIN index for time-series queries
    op.execute("""
        CREATE INDEX idx_compliance_scores_calculated_brin
        ON compliance_scores USING brin (calculated_at);
    """)

    # =========================================================================
    # Table 2: compliance_issues
    # Individual compliance issues with severity and fix suggestions
    # =========================================================================
    op.create_table(
        'compliance_issues',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()'),
                  comment='Unique identifier for issue'),
        sa.Column('score_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('compliance_scores.id', ondelete='CASCADE'),
                  nullable=False, index=True,
                  comment='Parent compliance score'),
        sa.Column('category', sa.String(50), nullable=False, index=True,
                  comment='Category: documentation_structure, specifications, etc.'),
        sa.Column('severity', sa.String(20), nullable=False, index=True,
                  comment='Severity: critical, warning, info'),
        sa.Column('issue_code', sa.String(50), nullable=False, index=True,
                  comment='Issue code: DUPLICATE_STAGE_FOLDER, MISSING_YAML_FRONTMATTER, etc.'),
        sa.Column('message', sa.Text(), nullable=False,
                  comment='Human-readable issue message'),
        sa.Column('file_path', sa.String(500), nullable=True,
                  comment='Relative file path where issue found'),
        sa.Column('line_number', sa.Integer(), nullable=True,
                  comment='Line number if applicable'),
        sa.Column('fix_suggestion', sa.Text(), nullable=True,
                  comment='Suggested fix for the issue'),
        sa.Column('fix_command', sa.String(500), nullable=True,
                  comment='CLI command to fix: sdlcctl fix --xxx'),
        sa.Column('auto_fixable', sa.Boolean(), nullable=False,
                  server_default='false',
                  comment='Whether issue can be auto-fixed'),
        sa.Column('context', postgresql.JSONB(), nullable=True,
                  comment='Additional context for the issue'),
        # Audit columns
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        # Check constraints
        sa.CheckConstraint(
            "severity IN ('critical', 'warning', 'info')",
            name='ck_compliance_issues_valid_severity'
        ),
        sa.CheckConstraint(
            """category IN (
                'documentation_structure',
                'specifications_management',
                'claude_agents_md',
                'sase_artifacts',
                'code_file_naming',
                'migration_tracking',
                'framework_alignment',
                'team_organization',
                'legacy_archival',
                'governance_documentation'
            )""",
            name='ck_compliance_issues_valid_category'
        ),
    )

    # Composite index for filtering by score + severity
    op.create_index(
        'idx_compliance_issues_score_severity',
        'compliance_issues',
        ['score_id', 'severity']
    )

    # Index for issue code analysis
    op.create_index(
        'idx_compliance_issues_code_count',
        'compliance_issues',
        ['issue_code', 'created_at']
    )

    # =========================================================================
    # Table 3: folder_collision_checks
    # Stage folder collision detection results (quick lookups)
    # =========================================================================
    op.create_table(
        'folder_collision_checks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()'),
                  comment='Unique identifier for collision check'),
        sa.Column('project_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('projects.id', ondelete='CASCADE'),
                  nullable=False, index=True,
                  comment='Project this check belongs to'),
        sa.Column('checked_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now(),
                  comment='Check timestamp'),
        sa.Column('docs_path', sa.String(500), nullable=False,
                  server_default='docs/',
                  comment='Docs folder path checked'),
        sa.Column('valid', sa.Boolean(), nullable=False, index=True,
                  comment='True if no collisions found'),
        sa.Column('collisions', postgresql.JSONB(), nullable=True,
                  comment='Array of collisions: [{stage_prefix, folders, severity}]'),
        sa.Column('gaps', postgresql.JSONB(), nullable=True,
                  comment='Array of missing stage folders'),
        sa.Column('extras', postgresql.JSONB(), nullable=True,
                  comment='Array of non-standard folders'),
        sa.Column('total_folders', sa.Integer(), nullable=True,
                  comment='Total folders scanned'),
        sa.Column('checked_by_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='SET NULL'),
                  nullable=True,
                  comment='User who triggered the check'),
        # Audit columns
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
    )

    # Index for project-based queries (most recent first)
    op.create_index(
        'idx_folder_collision_checks_project_time',
        'folder_collision_checks',
        ['project_id', 'checked_at'],
        postgresql_ops={'checked_at': 'DESC'}
    )

    # Index for finding invalid projects
    op.create_index(
        'idx_folder_collision_checks_invalid',
        'folder_collision_checks',
        ['valid', 'checked_at'],
        postgresql_where=sa.text('valid = false')
    )

    # =========================================================================
    # Issue Code Reference Table (for analytics and documentation)
    # =========================================================================
    op.execute("""
        COMMENT ON TABLE compliance_scores IS
        'SDLC 6.0.5 compliance scoring results. 10 categories × 10 points = 100 max score. '
        'Source: SPEC-0013 Compliance Validation Service (Sprint 123)';

        COMMENT ON TABLE compliance_issues IS
        'Individual compliance issues found during validation. '
        'Categories: documentation_structure, specifications_management, claude_agents_md, '
        'sase_artifacts, code_file_naming, migration_tracking, framework_alignment, '
        'team_organization, legacy_archival, governance_documentation. '
        'Source: SPEC-0013 Compliance Validation Service (Sprint 123)';

        COMMENT ON TABLE folder_collision_checks IS
        'Stage folder collision detection results. Validates that each stage prefix (00-10) '
        'has exactly one folder. Detects collisions (04-Development + 04-Testing), gaps '
        '(missing stages), and extras (non-standard folders). '
        'Source: SPEC-0013 Compliance Validation Service (Sprint 123)';
    """)


def downgrade():
    # Drop tables in reverse order (respecting FKs)
    op.drop_table('folder_collision_checks')
    op.drop_table('compliance_issues')
    op.drop_table('compliance_scores')
