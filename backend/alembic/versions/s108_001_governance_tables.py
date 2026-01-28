"""Sprint 108: Governance System - 14 Tables

Revision ID: s108_001_governance
Revises: s105_002_user_orgs
Create Date: 2026-01-27 10:00:00.000000

Sprint: 108 - Governance Foundation
Purpose: Create 14 governance tables for Anti-Vibecoding system

Tables Created:
1. governance_submissions - Central submission tracking
2. governance_rejections - Rejection reasons and feedback
3. evidence_vault_entries - Evidence metadata (MinIO S3)
4. governance_audit_log - Immutable audit trail (7-year retention)
5. ownership_registry - File ownership annotations
6. quality_contracts - Policy-as-code rules
7. context_snapshots - Historical context state
8. context_authorities - Context validation results
9. contract_versions - Policy versioning
10. contract_violations - Policy violation details
11. ai_attestations - AI-generated code attestations
12. human_reviews - Human review tracking
13. governance_exceptions - Break glass / exceptions
14. escalation_log - CEO escalation tracking

Performance Targets:
- Query by project_id: <50ms (P95)
- Query by status: <30ms (P95)
- All queries: <100ms (P95)

Retention:
- governance_audit_log: 7 years (NEVER delete)
- evidence_vault_entries: 7 years (HIPAA/SOC 2)
- Other tables: 2 years (archivable)
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "s108_001_governance"
down_revision = "s105_002_user_orgs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create 14 governance tables with indexes and constraints."""

    # 1. governance_submissions - Central submission tracking
    op.create_table(
        "governance_submissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("pr_number", sa.Integer(), nullable=True),
        sa.Column(
            "task_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("backlog_items.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("branch_name", sa.String(255), nullable=False),
        sa.Column("commit_sha", sa.String(40), nullable=False),
        sa.Column(
            "submitted_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "submitted_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("diff_summary", sa.Text(), nullable=True),
        sa.Column("files_changed", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("total_lines_added", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_lines_deleted", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("vibecoding_index", sa.Numeric(5, 2), nullable=True),
        sa.Column("routing", sa.String(50), nullable=True),
        sa.Column("passed_checks", postgresql.JSONB(), nullable=True),
        sa.Column("failed_checks", postgresql.JSONB(), nullable=True),
        sa.Column("validation_completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("signal_architectural_smell", sa.Numeric(5, 2), nullable=True),
        sa.Column("signal_abstraction_complexity", sa.Numeric(5, 2), nullable=True),
        sa.Column("signal_ai_dependency_ratio", sa.Numeric(5, 2), nullable=True),
        sa.Column("signal_change_surface_area", sa.Numeric(5, 2), nullable=True),
        sa.Column("signal_drift_velocity", sa.Numeric(5, 2), nullable=True),
        sa.Column("critical_path_override", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("critical_path_reason", sa.Text(), nullable=True),
        sa.Column("validation_duration_ms", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "vibecoding_index >= 0 AND vibecoding_index <= 100",
            name="check_vibecoding_index_range",
        ),
    )

    op.create_index("idx_submissions_project_id", "governance_submissions", ["project_id"])
    op.create_index("idx_submissions_status", "governance_submissions", ["status"])
    op.create_index(
        "idx_submissions_submitted_at", "governance_submissions", ["submitted_at"], postgresql_ops={"submitted_at": "DESC"}
    )
    op.create_index(
        "idx_submissions_vibecoding_index",
        "governance_submissions",
        ["vibecoding_index"],
        postgresql_where=sa.text("vibecoding_index IS NOT NULL"),
    )

    # 2. governance_rejections - Rejection reasons and feedback
    op.create_table(
        "governance_rejections",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "submission_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("governance_submissions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("rejection_reason", sa.String(255), nullable=False),
        sa.Column("rejection_category", sa.String(100), nullable=False),
        sa.Column("severity", sa.String(50), nullable=False),
        sa.Column("feedback_template_id", sa.String(100), nullable=True),
        sa.Column("feedback_message", sa.Text(), nullable=False),
        sa.Column("feedback_cli_command", sa.Text(), nullable=True),
        sa.Column("documentation_link", sa.Text(), nullable=True),
        sa.Column("resolved", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "resolved_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_index("idx_rejections_submission_id", "governance_rejections", ["submission_id"])
    op.create_index(
        "idx_rejections_resolved",
        "governance_rejections",
        ["resolved"],
        postgresql_where=sa.text("NOT resolved"),
    )

    # 3. evidence_vault_entries - Evidence metadata (MinIO S3)
    op.create_table(
        "evidence_vault_entries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "submission_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("governance_submissions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("evidence_type", sa.String(100), nullable=False),
        sa.Column("evidence_name", sa.String(255), nullable=False),
        sa.Column("evidence_description", sa.Text(), nullable=True),
        sa.Column("s3_bucket", sa.String(255), nullable=False),
        sa.Column("s3_key", sa.Text(), nullable=False),
        sa.Column("s3_url", sa.Text(), nullable=False),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("mime_type", sa.String(100), nullable=False),
        sa.Column("sha256_hash", sa.String(64), nullable=False),
        sa.Column("state", sa.String(50), nullable=False, server_default="uploaded"),
        sa.Column(
            "state_changed_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "uploaded_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "uploaded_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("s3_bucket", "s3_key", name="uq_evidence_s3_location"),
    )

    op.create_index("idx_evidence_submission_id", "evidence_vault_entries", ["submission_id"])
    op.create_index("idx_evidence_project_id", "evidence_vault_entries", ["project_id"])
    op.create_index("idx_evidence_type", "evidence_vault_entries", ["evidence_type"])
    op.create_index("idx_evidence_state", "evidence_vault_entries", ["state"])

    # 4. governance_audit_log - Immutable audit trail
    op.create_table(
        "governance_audit_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("user_email", sa.String(255), nullable=False),
        sa.Column("user_role", sa.String(50), nullable=True),
        sa.Column("ip_address", postgresql.INET(), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("action_category", sa.String(50), nullable=False),
        sa.Column("target_type", sa.String(100), nullable=True),
        sa.Column("target_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "submission_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("governance_submissions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("action_details", postgresql.JSONB(), nullable=True),
        sa.Column("outcome", sa.String(50), nullable=True),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_index("idx_audit_user_id", "governance_audit_log", ["user_id"])
    op.create_index(
        "idx_audit_timestamp", "governance_audit_log", ["timestamp"], postgresql_ops={"timestamp": "DESC"}
    )
    op.create_index("idx_audit_action", "governance_audit_log", ["action"])
    op.create_index("idx_audit_project_id", "governance_audit_log", ["project_id"])
    op.create_index("idx_audit_submission_id", "governance_audit_log", ["submission_id"])

    # Create immutability trigger for audit_log
    op.execute("""
        CREATE OR REPLACE FUNCTION prevent_audit_log_modification()
        RETURNS TRIGGER AS $$
        BEGIN
            RAISE EXCEPTION 'Audit log is immutable - UPDATE/DELETE forbidden';
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER governance_audit_log_immutable
            BEFORE UPDATE OR DELETE ON governance_audit_log
            FOR EACH ROW
            EXECUTE FUNCTION prevent_audit_log_modification();
    """)

    # 5. ownership_registry - File ownership annotations
    op.create_table(
        "ownership_registry",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("file_path", sa.Text(), nullable=False),
        sa.Column("file_hash", sa.String(64), nullable=True),
        sa.Column(
            "owner_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "owner_team_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("teams.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("ownership_source", sa.String(50), nullable=False),
        sa.Column("ownership_confidence", sa.Numeric(3, 2), nullable=True),
        sa.Column("module_name", sa.String(255), nullable=True),
        sa.Column("module_type", sa.String(100), nullable=True),
        sa.Column(
            "declared_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("last_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("project_id", "file_path", name="uq_ownership_project_file"),
    )

    op.create_index("idx_ownership_project_file", "ownership_registry", ["project_id", "file_path"])
    op.create_index("idx_ownership_owner_user", "ownership_registry", ["owner_user_id"])

    # 6. quality_contracts - Policy-as-code rules
    op.create_table(
        "quality_contracts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("contract_name", sa.String(255), nullable=False, unique=True),
        sa.Column("contract_category", sa.String(100), nullable=False),
        sa.Column("contract_description", sa.Text(), nullable=False),
        sa.Column("contract_yaml", sa.Text(), nullable=False),
        sa.Column("contract_rego", sa.Text(), nullable=True),
        sa.Column("version", sa.String(50), nullable=False, server_default="1.0.0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("deprecated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "approved_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_index(
        "idx_contracts_active",
        "quality_contracts",
        ["is_active"],
        postgresql_where=sa.text("is_active = true"),
    )
    op.create_index("idx_contracts_category", "quality_contracts", ["contract_category"])

    # 7. context_snapshots - Historical context state
    op.create_table(
        "context_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("commit_sha", sa.String(40), nullable=False),
        sa.Column("adrs", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("agents_md_content", sa.Text(), nullable=True),
        sa.Column("agents_md_hash", sa.String(64), nullable=True),
        sa.Column("design_docs", postgresql.JSONB(), nullable=True),
        sa.Column("module_registry", postgresql.JSONB(), nullable=True),
        sa.Column("snapshot_reason", sa.String(255), nullable=True),
        sa.Column("snapshot_size_bytes", sa.BigInteger(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_index("idx_snapshots_project_id", "context_snapshots", ["project_id"])
    op.create_index("idx_snapshots_commit_sha", "context_snapshots", ["commit_sha"])
    op.create_index(
        "idx_snapshots_created_at", "context_snapshots", ["created_at"], postgresql_ops={"created_at": "DESC"}
    )

    # 8. context_authorities - Context validation results
    op.create_table(
        "context_authorities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "submission_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("governance_submissions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("has_adr_linkage", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("linked_adrs", postgresql.JSONB(), nullable=True),
        sa.Column("has_design_doc", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("linked_design_docs", postgresql.JSONB(), nullable=True),
        sa.Column("agents_md_freshness_days", sa.Integer(), nullable=True),
        sa.Column("agents_md_stale", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("module_annotation_consistent", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("module_annotation_issues", postgresql.JSONB(), nullable=True),
        sa.Column("validation_status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("validation_errors", postgresql.JSONB(), nullable=True),
        sa.Column(
            "context_snapshot_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("context_snapshots.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("validation_duration_ms", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_index("idx_context_submission_id", "context_authorities", ["submission_id"])
    op.create_index("idx_context_project_id", "context_authorities", ["project_id"])
    op.create_index("idx_context_status", "context_authorities", ["validation_status"])

    # 9. contract_versions - Policy versioning
    op.create_table(
        "contract_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "contract_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("quality_contracts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("version", sa.String(50), nullable=False),
        sa.Column("version_description", sa.Text(), nullable=True),
        sa.Column("contract_yaml", sa.Text(), nullable=False),
        sa.Column("contract_rego", sa.Text(), nullable=True),
        sa.Column(
            "changed_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("change_reason", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("contract_id", "version", name="uq_contract_version"),
    )

    op.create_index("idx_contract_versions_contract_id", "contract_versions", ["contract_id"])
    op.create_index(
        "idx_contract_versions_created_at", "contract_versions", ["created_at"], postgresql_ops={"created_at": "DESC"}
    )

    # 10. contract_violations - Policy violation details
    op.create_table(
        "contract_violations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "submission_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("governance_submissions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "contract_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("quality_contracts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("violation_type", sa.String(255), nullable=False),
        sa.Column("violation_severity", sa.String(50), nullable=False),
        sa.Column("violation_message", sa.Text(), nullable=False),
        sa.Column("file_path", sa.Text(), nullable=True),
        sa.Column("line_number", sa.Integer(), nullable=True),
        sa.Column("resolved", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolution_notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_index("idx_violations_submission_id", "contract_violations", ["submission_id"])
    op.create_index("idx_violations_contract_id", "contract_violations", ["contract_id"])
    op.create_index(
        "idx_violations_resolved",
        "contract_violations",
        ["resolved"],
        postgresql_where=sa.text("NOT resolved"),
    )

    # 11. ai_attestations - AI-generated code attestations
    op.create_table(
        "ai_attestations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "submission_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("governance_submissions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("ai_provider", sa.String(100), nullable=False),
        sa.Column("model_version", sa.String(255), nullable=False),
        sa.Column("session_id", sa.String(255), nullable=True),
        sa.Column("prompt_hash", sa.String(64), nullable=True),
        sa.Column("ai_generated_files", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("total_ai_lines", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("review_time_minutes", sa.Integer(), nullable=False),
        sa.Column("minimum_review_time_minutes", sa.Integer(), nullable=False),
        sa.Column("review_sufficient", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("modifications_made", sa.Text(), nullable=True),
        sa.Column("understanding_confirmed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "attested_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "attested_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint("review_time_minutes >= 0", name="check_review_time_positive"),
    )

    op.create_index("idx_attestations_submission_id", "ai_attestations", ["submission_id"])
    op.create_index("idx_attestations_project_id", "ai_attestations", ["project_id"])
    op.create_index("idx_attestations_attested_by", "ai_attestations", ["attested_by"])

    # 12. human_reviews - Human review tracking
    op.create_table(
        "human_reviews",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "attestation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("ai_attestations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "submission_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("governance_submissions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "reviewed_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("reviewer_role", sa.String(50), nullable=False),
        sa.Column("review_duration_minutes", sa.Integer(), nullable=False),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column("issues_found", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("issues_fixed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("code_quality_rating", sa.Integer(), nullable=True),
        sa.Column(
            "reviewed_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "code_quality_rating IS NULL OR (code_quality_rating >= 1 AND code_quality_rating <= 5)",
            name="check_quality_rating_range",
        ),
    )

    op.create_index("idx_reviews_attestation_id", "human_reviews", ["attestation_id"])
    op.create_index("idx_reviews_reviewed_by", "human_reviews", ["reviewed_by"])

    # 13. governance_exceptions - Break glass / exceptions
    op.create_table(
        "governance_exceptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "submission_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("governance_submissions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("exception_type", sa.String(100), nullable=False),
        sa.Column("severity", sa.String(50), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("incident_ticket", sa.String(255), nullable=True),
        sa.Column("rollback_plan", sa.Text(), nullable=False),
        sa.Column(
            "requested_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "requested_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "approved_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approval_status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("break_glass_activated", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("auto_revert_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("post_incident_review_completed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_index("idx_exceptions_submission_id", "governance_exceptions", ["submission_id"])
    op.create_index("idx_exceptions_project_id", "governance_exceptions", ["project_id"])
    op.create_index("idx_exceptions_approval_status", "governance_exceptions", ["approval_status"])
    op.create_index(
        "idx_exceptions_auto_revert",
        "governance_exceptions",
        ["auto_revert_at"],
        postgresql_where=sa.text("auto_revert_at IS NOT NULL"),
    )

    # 14. escalation_log - CEO escalation tracking
    op.create_table(
        "escalation_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "submission_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("governance_submissions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("escalation_reason", sa.String(255), nullable=False),
        sa.Column("vibecoding_index", sa.Numeric(5, 2), nullable=True),
        sa.Column(
            "escalated_to",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "escalated_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "escalated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("ceo_decision", sa.String(50), nullable=True),
        sa.Column("ceo_decision_notes", sa.Text(), nullable=True),
        sa.Column("ceo_decision_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ceo_review_duration_minutes", sa.Integer(), nullable=True),
        sa.Column("ceo_agrees_with_index", sa.Boolean(), nullable=True),
        sa.Column("calibration_feedback", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_index("idx_escalation_submission_id", "escalation_log", ["submission_id"])
    op.create_index("idx_escalation_project_id", "escalation_log", ["project_id"])
    op.create_index("idx_escalation_to", "escalation_log", ["escalated_to"])
    op.create_index(
        "idx_escalation_decision",
        "escalation_log",
        ["ceo_decision"],
        postgresql_where=sa.text("ceo_decision IS NOT NULL"),
    )


def downgrade() -> None:
    """Drop all 14 governance tables in reverse order."""

    # Drop immutability trigger first
    op.execute("DROP TRIGGER IF EXISTS governance_audit_log_immutable ON governance_audit_log")
    op.execute("DROP FUNCTION IF EXISTS prevent_audit_log_modification()")

    # Drop tables in reverse dependency order
    op.drop_table("escalation_log")
    op.drop_table("governance_exceptions")
    op.drop_table("human_reviews")
    op.drop_table("ai_attestations")
    op.drop_table("contract_violations")
    op.drop_table("contract_versions")
    op.drop_table("context_authorities")
    op.drop_table("context_snapshots")
    op.drop_table("quality_contracts")
    op.drop_table("ownership_registry")
    op.drop_table("governance_audit_log")
    op.drop_table("evidence_vault_entries")
    op.drop_table("governance_rejections")
    op.drop_table("governance_submissions")
