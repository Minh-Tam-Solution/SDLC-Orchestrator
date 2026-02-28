"""s209_004_add_sast_tables — Add sast_scans and sast_findings tables

Missing migration for SASTScan and SASTFinding models (Sprint 69 CTO Go-Live).
Tables required by /api/v1/sast/ endpoints which return HTTP 500 without them.

Revision ID: s209_004
Revises: s209_003
Create Date: 2026-02-28
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import ENUM as PGEnum

# revision identifiers
revision = "s209_004"
down_revision = "s209_003"
branch_labels = None
depends_on = None

# Enum types with create_type=False so SQLAlchemy does NOT auto-issue
# CREATE TYPE during table creation — we manage the type lifecycle ourselves
# using DO ... EXCEPTION blocks to be idempotent.
_scan_status = PGEnum(
    "pending", "running", "completed", "failed", "cancelled",
    name="sastscanstatus", create_type=False
)
_scan_type = PGEnum(
    "full", "quick", "pr", "incremental",
    name="sastscantype", create_type=False
)
_severity = PGEnum(
    "critical", "high", "medium", "low", "info",
    name="sastseverity", create_type=False
)


def upgrade() -> None:
    # ------------------------------------------------------------------
    # Enum types — PostgreSQL does not support CREATE TYPE IF NOT EXISTS.
    # Use DO ... EXCEPTION so re-running is safe.
    # ------------------------------------------------------------------
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE sastscanstatus AS ENUM
                ('pending', 'running', 'completed', 'failed', 'cancelled');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE sastscantype AS ENUM
                ('full', 'quick', 'pr', 'incremental');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE sastseverity AS ENUM
                ('critical', 'high', 'medium', 'low', 'info');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$
    """)

    # ------------------------------------------------------------------
    # sast_scans
    # ------------------------------------------------------------------
    op.create_table(
        "sast_scans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "triggered_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        sa.Column("scan_type", _scan_type, nullable=False, server_default="full"),
        sa.Column("status", _scan_status, nullable=False, server_default="pending", index=True),
        sa.Column("branch", sa.String(255), nullable=True),
        sa.Column("commit_sha", sa.String(64), nullable=True),
        sa.Column("total_findings", sa.Integer, nullable=False, server_default="0"),
        sa.Column("critical_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("high_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("medium_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("low_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("info_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("files_scanned", sa.Integer, nullable=False, server_default="0"),
        sa.Column("rules_run", sa.Integer, nullable=False, server_default="0"),
        sa.Column("scan_duration_ms", sa.Integer, nullable=True),
        sa.Column("blocks_merge", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("findings", postgresql.JSONB, nullable=True),
        sa.Column("by_category", postgresql.JSONB, nullable=True),
        sa.Column("top_affected_files", postgresql.JSONB, nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("started_at", sa.DateTime, nullable=True),
        sa.Column("completed_at", sa.DateTime, nullable=True, index=True),
        sa.Column(
            "created_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )
    op.create_index("ix_sast_scans_id", "sast_scans", ["id"])

    # ------------------------------------------------------------------
    # sast_findings
    # ------------------------------------------------------------------
    op.create_table(
        "sast_findings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "scan_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sast_scans.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("rule_id", sa.String(255), nullable=False, index=True),
        sa.Column("rule_name", sa.String(500), nullable=True),
        sa.Column("severity", _severity, nullable=False, server_default="medium", index=True),
        sa.Column("category", sa.String(100), nullable=True, index=True),
        sa.Column("file_path", sa.String(1000), nullable=False, index=True),
        sa.Column("start_line", sa.Integer, nullable=False),
        sa.Column("end_line", sa.Integer, nullable=True),
        sa.Column("start_col", sa.Integer, nullable=True),
        sa.Column("end_col", sa.Integer, nullable=True),
        sa.Column("message", sa.Text, nullable=False),
        sa.Column("snippet", sa.Text, nullable=True),
        sa.Column("fix_suggestion", sa.Text, nullable=True),
        sa.Column("cwe", postgresql.JSONB, nullable=True),
        sa.Column("owasp", postgresql.JSONB, nullable=True),
        sa.Column("references", postgresql.JSONB, nullable=True),
        sa.Column("confidence", sa.String(50), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="open", index=True),
        sa.Column("fixed_at", sa.DateTime, nullable=True),
        sa.Column(
            "fixed_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )
    op.create_index("ix_sast_findings_id", "sast_findings", ["id"])


def downgrade() -> None:
    op.drop_table("sast_findings")
    op.drop_table("sast_scans")
    op.execute("DROP TYPE IF EXISTS sastseverity")
    op.execute("DROP TYPE IF EXISTS sastscantype")
    op.execute("DROP TYPE IF EXISTS sastscanstatus")
