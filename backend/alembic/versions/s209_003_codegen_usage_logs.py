"""s209_003_codegen_usage_logs — Add codegen_usage_logs table

Missing migration for CodegenUsageLog model (Sprint 48 EP-06).
Tracks AI code generation requests for cost management and analytics.

Revision ID: s209_003
Revises: s209_002
Create Date: 2026-02-27
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = "s209_003"
down_revision = "s209_002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "codegen_usage_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("request_id", sa.String(64), nullable=False, unique=True, index=True),
        sa.Column("provider", sa.String(50), nullable=False, index=True),
        sa.Column("model", sa.String(100), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending", index=True),
        sa.Column("language", sa.String(50), nullable=False, server_default="python"),
        sa.Column("framework", sa.String(50), nullable=False, server_default="fastapi"),
        sa.Column("target_module", sa.String(100), nullable=True),
        sa.Column("blueprint_name", sa.String(200), nullable=True),
        sa.Column("blueprint_hash", sa.String(64), nullable=True),
        sa.Column("blueprint_size_bytes", sa.Integer, nullable=True),
        sa.Column("prompt_tokens", sa.Integer, server_default="0"),
        sa.Column("completion_tokens", sa.Integer, server_default="0"),
        sa.Column("total_tokens", sa.Integer, server_default="0"),
        sa.Column("estimated_cost_usd", sa.Numeric(10, 6), server_default="0"),
        sa.Column("actual_cost_usd", sa.Numeric(10, 6), server_default="0"),
        sa.Column("generation_time_ms", sa.Integer, nullable=True),
        sa.Column("queue_wait_ms", sa.Integer, nullable=True),
        sa.Column("files_generated", sa.Integer, server_default="0"),
        sa.Column("total_lines_generated", sa.Integer, server_default="0"),
        sa.Column("output_size_bytes", sa.Integer, server_default="0"),
        sa.Column("quality_gate_status", sa.String(20), nullable=True),
        sa.Column("quality_errors", sa.Integer, server_default="0"),
        sa.Column("quality_warnings", sa.Integer, server_default="0"),
        sa.Column("quality_blocked", sa.Boolean, server_default="false"),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("error_type", sa.String(100), nullable=True),
        sa.Column("extra_metadata", JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now(), index=True),
        sa.Column("completed_at", sa.DateTime, nullable=True),
    )
    op.create_index("ix_codegen_usage_logs_user_date", "codegen_usage_logs", ["user_id", "created_at"])
    op.create_index("ix_codegen_usage_logs_project_date", "codegen_usage_logs", ["project_id", "created_at"])
    op.create_index("ix_codegen_usage_logs_provider_date", "codegen_usage_logs", ["provider", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_codegen_usage_logs_provider_date", table_name="codegen_usage_logs")
    op.drop_index("ix_codegen_usage_logs_project_date", table_name="codegen_usage_logs")
    op.drop_index("ix_codegen_usage_logs_user_date", table_name="codegen_usage_logs")
    op.drop_table("codegen_usage_logs")
