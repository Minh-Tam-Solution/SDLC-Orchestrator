"""s186_002_gdpr_tables — GDPR data subject request + consent tables

Revision ID: s186002
Revises: s186001
Create Date: 2026-02-20

Sprint 186 — Multi-Region Data Residency + GDPR (ADR-063)
Authority: CTO Approved

Tables created:
  gdpr_dsar_requests  — Data Subject Access/Erasure Request (GDPR Art. 15/17)
  gdpr_consent_logs   — Processing consent audit trail (GDPR Art. 7)

State machine for dsar_requests:
  pending → processing → completed | rejected | partial

Indexes:
  ix_dsar_user_id      — all requests from a user
  ix_dsar_status       — filter by status (processing queue)
  ix_dsar_created_at   — time-range queries
  ix_consent_user_id   — consent history for a user
  ix_consent_purpose   — filter by processing purpose
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = "s186002"
down_revision = "s186001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # -------------------------------------------------------------------------
    # 1. gdpr_dsar_requests — Data Subject Access / Erasure Requests
    # -------------------------------------------------------------------------
    op.create_table(
        "gdpr_dsar_requests",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True),
        # Type: 'access' (Art.15 DSAR) or 'erasure' (Art.17 right-to-be-forgotten)
        sa.Column("request_type", sa.String(20), nullable=False),
        # Status state machine: pending → processing → completed | rejected | partial
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("requester_email", sa.String(254), nullable=False),  # May differ from user.email if submitted via form
        sa.Column("description", sa.Text, nullable=True),
        # DPO notes / rejection reason
        sa.Column("dpo_notes", sa.Text, nullable=True),
        # For erasure: path to the generated data export ZIP (stored in S3 for access requests)
        sa.Column("export_s3_key", sa.String(512), nullable=True),
        sa.Column("export_s3_bucket", sa.String(100), nullable=True),
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),  # GDPR 30-day deadline
        sa.Column("processed_by", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
    )

    op.create_check_constraint(
        "ck_dsar_request_type",
        "gdpr_dsar_requests",
        sa.text("request_type IN ('access', 'erasure', 'portability', 'rectification')"),
    )
    op.create_check_constraint(
        "ck_dsar_status",
        "gdpr_dsar_requests",
        sa.text("status IN ('pending', 'processing', 'completed', 'rejected', 'partial')"),
    )

    op.create_index("ix_dsar_status", "gdpr_dsar_requests", ["status"])
    op.create_index("ix_dsar_created_at", "gdpr_dsar_requests", ["created_at"])
    op.create_index("ix_dsar_requester_email", "gdpr_dsar_requests", ["requester_email"])

    # -------------------------------------------------------------------------
    # 2. gdpr_consent_logs — Processing consent records (GDPR Art. 7)
    # -------------------------------------------------------------------------
    op.create_table(
        "gdpr_consent_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        # Processing purpose: 'essential', 'analytics', 'marketing', 'ai_training'
        sa.Column("purpose", sa.String(50), nullable=False),
        sa.Column("granted", sa.Boolean, nullable=False),
        sa.Column("version", sa.String(20), nullable=False),   # Privacy policy version at consent time
        sa.Column("ip_address", sa.String(45), nullable=True), # IPv4 or IPv6
        sa.Column("user_agent", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        # When consent was withdrawn (null = still active)
        sa.Column("withdrawn_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_check_constraint(
        "ck_consent_purpose",
        "gdpr_consent_logs",
        sa.text("purpose IN ('essential', 'analytics', 'marketing', 'ai_training', 'third_party')"),
    )

    op.create_index("ix_consent_purpose", "gdpr_consent_logs", ["purpose"])
    op.create_index("ix_consent_created_at", "gdpr_consent_logs", ["created_at"])
    # Composite: most common query pattern (user + purpose + active)
    op.create_index(
        "ix_consent_user_purpose",
        "gdpr_consent_logs",
        ["user_id", "purpose", "withdrawn_at"],
    )


def downgrade() -> None:
    op.drop_table("gdpr_consent_logs")
    op.drop_table("gdpr_dsar_requests")
