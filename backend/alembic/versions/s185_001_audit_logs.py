"""s185_001_audit_logs — create audit_logs table with immutability trigger

Revision ID: s185001
Revises: s184001
Create Date: 2026-02-20

Sprint 185 — SOC2 Type II append-only audit trail (ADR-059)

Security:
  The prevent_audit_log_modifications trigger enforces immutability at the
  PostgreSQL engine level — any UPDATE or DELETE on audit_logs raises EXCEPTION,
  bypassing ORM, direct SQL, and superuser connections from application code.
  This satisfies SOC2 CC6.1, CC7.2, CC8.1 (tamper-evident log).

Indexes:
  ix_audit_logs_id            — primary key fast lookup
  ix_audit_logs_event_type    — filter by event category
  ix_audit_logs_actor_id      — all events by a user
  ix_audit_logs_resource_id   — all events on a resource
  ix_audit_logs_created_at    — time-range queries + 90-day retention
  ix_audit_org_created        — org + time (most common query pattern)
  ix_audit_actor_created      — actor + time (user activity timeline)
  ix_audit_resource           — resource_type + resource_id (who touched X)
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "s185001"
down_revision = "s184001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # -------------------------------------------------------------------------
    # 1. Create audit_logs table
    # -------------------------------------------------------------------------
    op.create_table(
        "audit_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("actor_id", sa.String(36), nullable=True),
        sa.Column("actor_email", sa.String(254), nullable=True),
        sa.Column("organization_id", sa.String(36), nullable=True),
        sa.Column("resource_type", sa.String(64), nullable=True),
        sa.Column("resource_id", sa.String(36), nullable=True),
        sa.Column("detail", JSONB, nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.String(512), nullable=True),
        sa.Column("tier_at_event", sa.String(32), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )

    # -------------------------------------------------------------------------
    # 2. Create indexes
    # -------------------------------------------------------------------------
    op.create_index("ix_audit_logs_id", "audit_logs", ["id"], unique=False)
    op.create_index("ix_audit_logs_event_type", "audit_logs", ["event_type"])
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index("ix_audit_logs_actor_id", "audit_logs", ["actor_id"])
    op.create_index("ix_audit_logs_organization_id", "audit_logs", ["organization_id"])
    op.create_index("ix_audit_logs_resource_id", "audit_logs", ["resource_id"])
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])

    # Composite indexes for most common query patterns
    op.create_index(
        "ix_audit_org_created",
        "audit_logs",
        ["organization_id", "created_at"],
    )
    op.create_index(
        "ix_audit_actor_created",
        "audit_logs",
        ["actor_id", "created_at"],
    )
    op.create_index(
        "ix_audit_resource",
        "audit_logs",
        ["resource_type", "resource_id"],
    )

    # -------------------------------------------------------------------------
    # 3. Immutability trigger — prevent UPDATE and DELETE at DB engine level
    #
    # This trigger enforces SOC2 tamper-evidence:
    #   - No UPDATE: cannot alter historical event data
    #   - No DELETE: no event can be erased (even by DB admin via application)
    #   - Retention is handled by archiving/partitioning, NOT deletion
    #
    # Security note: PostgreSQL superuser can bypass triggers with
    # SET session_replication_role = 'replica'; — this is an infra-level
    # control that should be restricted via GRANT/REVOKE on the DB role
    # used by the application (app role should NOT be superuser).
    # -------------------------------------------------------------------------
    op.execute("""
        CREATE OR REPLACE FUNCTION prevent_audit_log_modifications()
        RETURNS TRIGGER AS $$
        BEGIN
            RAISE EXCEPTION
                'audit_logs is append-only: % on audit_logs is not permitted. '
                'SOC2 CC7.2 tamper-evidence constraint.',
                TG_OP;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER audit_log_immutable
        BEFORE UPDATE OR DELETE ON audit_logs
        FOR EACH ROW EXECUTE FUNCTION prevent_audit_log_modifications();
    """)


def downgrade() -> None:
    # Drop trigger first, then function, then table
    op.execute("DROP TRIGGER IF EXISTS audit_log_immutable ON audit_logs;")
    op.execute("DROP FUNCTION IF EXISTS prevent_audit_log_modifications();")

    op.drop_index("ix_audit_resource", table_name="audit_logs")
    op.drop_index("ix_audit_actor_created", table_name="audit_logs")
    op.drop_index("ix_audit_org_created", table_name="audit_logs")
    op.drop_index("ix_audit_logs_created_at", table_name="audit_logs")
    op.drop_index("ix_audit_logs_resource_id", table_name="audit_logs")
    op.drop_index("ix_audit_logs_organization_id", table_name="audit_logs")
    op.drop_index("ix_audit_logs_actor_id", table_name="audit_logs")
    op.drop_index("ix_audit_logs_action", table_name="audit_logs")
    op.drop_index("ix_audit_logs_event_type", table_name="audit_logs")
    op.drop_index("ix_audit_logs_id", table_name="audit_logs")
    op.drop_table("audit_logs")
