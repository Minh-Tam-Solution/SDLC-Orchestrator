"""s184_001_jira_connections — create jira_connections table

Revision ID: s184001
Revises: s183002
Create Date: 2026-02-19

Sprint 184 — Jira integration credentials storage
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "s184001"
down_revision = "s183_002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "jira_connections",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("organization_id", sa.String(36), nullable=False),
        sa.Column("jira_base_url", sa.String(512), nullable=False),
        sa.Column("jira_email", sa.String(254), nullable=False),
        sa.Column("api_token_enc", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_jira_conn_org", "jira_connections", ["organization_id"], unique=True)
    op.create_index(
        op.f("ix_jira_connections_id"), "jira_connections", ["id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_jira_connections_id"), table_name="jira_connections")
    op.drop_index("ix_jira_conn_org", table_name="jira_connections")
    op.drop_table("jira_connections")
