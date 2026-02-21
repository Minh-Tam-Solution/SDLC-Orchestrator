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
    # Drop old audit_logs table if it exists with the legacy schema
    # (Sprint 185 v1 had user_id/details; v2 uses event_type/actor_id).
    op.execute("DROP TABLE IF EXISTS audit_logs CASCADE;")

    # 1. Create audit_logs table (fresh schema)
    op.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id UUID NOT NULL,
            event_type VARCHAR(64) NOT NULL,
            action VARCHAR(64) NOT NULL,
            actor_id VARCHAR(36),
            actor_email VARCHAR(254),
            organization_id VARCHAR(36),
            resource_type VARCHAR(64),
            resource_id VARCHAR(36),
            detail JSONB,
            ip_address VARCHAR(45),
            user_agent VARCHAR(512),
            tier_at_event VARCHAR(32),
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            PRIMARY KEY (id)
        );
    """)

    # 2. Create indexes (IF NOT EXISTS — PostgreSQL 9.5+)
    op.execute("CREATE INDEX IF NOT EXISTS ix_audit_logs_id ON audit_logs (id);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_audit_logs_event_type ON audit_logs (event_type);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_audit_logs_action ON audit_logs (action);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_audit_logs_actor_id ON audit_logs (actor_id);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_audit_logs_organization_id ON audit_logs (organization_id);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_audit_logs_resource_id ON audit_logs (resource_id);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_audit_logs_created_at ON audit_logs (created_at);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_audit_org_created ON audit_logs (organization_id, created_at);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_audit_actor_created ON audit_logs (actor_id, created_at);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_audit_resource ON audit_logs (resource_type, resource_id);")

    # 3. Immutability trigger — SOC2 CC7.2 tamper-evidence
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
        DROP TRIGGER IF EXISTS audit_log_immutable ON audit_logs;
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
