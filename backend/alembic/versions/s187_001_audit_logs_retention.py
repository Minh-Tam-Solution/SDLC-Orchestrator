"""s187_001_audit_logs_retention — 90-day retention metadata + export function

Sprint 187 — G4 Production Validation (Gate G4-03 Audit Trail)

Purpose:
  Add retention metadata columns and a PostgreSQL export helper function to
  the audit_logs table created in s185_001.  The table itself remains
  append-only (immutability trigger from s185_001 is untouched).

Changes:
  1. Add nullable columns:
       - purge_eligible_at  TIMESTAMPTZ  — created_at + 90 days (retention floor)
       - legal_hold         BOOLEAN      — marks records exempt from archival (default FALSE)
  2. Backfill purge_eligible_at for existing rows (created_at + 90 days)
  3. Add index on purge_eligible_at for retention queries
  4. Create fn_export_audit_logs(start_date, end_date, p_org_id) — returns JSONB array
     of audit log rows in the date range (supports Art. 15/20 CSV export)
  5. Create fn_pseudonymize_audit_actor(actor_uuid) — replaces actor_id + actor_email
     with SHA-256 hash of the UUID (GDPR Art. 17 pseudonymization, preserves immutability)

G4 Acceptance Criteria:
  - G4-03: 90-day immutable log tested
  - AT-02: purge_eligible_at is correctly computed (created_at + interval '90 days')
  - AT-03: legal_hold flag prevents records from being included in purge candidates
  - AT-04: fn_export_audit_logs returns complete JSON for a given date range

Notes:
  - immutability trigger from s185_001 blocks UPDATE/DELETE on all columns
  - The new columns are nullable and have DEFAULT — they are safe to add to existing rows
  - purge_eligible_at backfill uses UPDATE which is ordinarily blocked by the trigger.
    We temporarily disable the trigger, run the backfill, then re-enable it.
    The trigger remains active post-migration for all future rows.
  - legal_hold and purge_eligible_at are never used to delete rows — they are advisory
    metadata for the archival/export pipeline.

Revision: s187001
Down: s186002
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


# ---------------------------------------------------------------------------
# Metadata
# ---------------------------------------------------------------------------

revision = "s187001"
down_revision = "s186002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # -------------------------------------------------------------------------
    # 1. Add retention metadata columns
    #    - purge_eligible_at: advisory timestamp (created_at + 90 days)
    #    - legal_hold: when TRUE the row is excluded from archival candidates
    # -------------------------------------------------------------------------
    op.add_column(
        "audit_logs",
        sa.Column(
            "purge_eligible_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="created_at + 90 days — row is eligible for archival/export after this date",
        ),
    )
    op.add_column(
        "audit_logs",
        sa.Column(
            "legal_hold",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("FALSE"),
            comment="TRUE = row must be retained beyond 90 days (regulatory / legal hold)",
        ),
    )

    # -------------------------------------------------------------------------
    # 2. Backfill purge_eligible_at for existing rows.
    #    The immutability trigger blocks UPDATE. We disable it temporarily,
    #    run the backfill for the new column only, then re-enable.
    # -------------------------------------------------------------------------
    op.execute(
        "ALTER TABLE audit_logs DISABLE TRIGGER audit_log_immutable;"
    )
    op.execute(
        """
        UPDATE audit_logs
        SET purge_eligible_at = created_at + INTERVAL '90 days'
        WHERE purge_eligible_at IS NULL;
        """
    )
    op.execute(
        "ALTER TABLE audit_logs ENABLE TRIGGER audit_log_immutable;"
    )

    # -------------------------------------------------------------------------
    # 3. Index on purge_eligible_at to support retention queries
    # -------------------------------------------------------------------------
    op.create_index(
        "ix_audit_purge_eligible_at",
        "audit_logs",
        ["purge_eligible_at"],
        postgresql_where=sa.text("legal_hold = FALSE"),
    )

    # -------------------------------------------------------------------------
    # 4. Export helper function — returns JSONB array for a date range + org
    #    Used by:
    #      - DPO dashboard (CSV export)
    #      - GDPR Art. 15/20 self-service
    #      - G4-03 "Export 30-day audit log as CSV → verify completeness"
    # -------------------------------------------------------------------------
    op.execute("""
        CREATE OR REPLACE FUNCTION fn_export_audit_logs(
            p_start  TIMESTAMPTZ,
            p_end    TIMESTAMPTZ,
            p_org_id TEXT DEFAULT NULL
        )
        RETURNS JSONB
        LANGUAGE plpgsql
        SECURITY DEFINER
        AS $$
        DECLARE
            v_result JSONB;
        BEGIN
            SELECT jsonb_agg(
                jsonb_build_object(
                    'id',               id,
                    'event_type',       event_type,
                    'action',           action,
                    'actor_id',         actor_id,
                    'actor_email',      actor_email,
                    'organization_id',  organization_id,
                    'resource_type',    resource_type,
                    'resource_id',      resource_id,
                    'detail',           detail,
                    'ip_address',       ip_address,
                    'tier_at_event',    tier_at_event,
                    'created_at',       created_at,
                    'purge_eligible_at', purge_eligible_at,
                    'legal_hold',       legal_hold
                )
                ORDER BY created_at ASC
            )
            INTO v_result
            FROM audit_logs
            WHERE created_at >= p_start
              AND created_at <  p_end
              AND (p_org_id IS NULL OR organization_id = p_org_id);

            RETURN COALESCE(v_result, '[]'::jsonb);
        END;
        $$;

        COMMENT ON FUNCTION fn_export_audit_logs IS
            'Return all audit log rows in [p_start, p_end) for the given org '
            '(NULL org = all orgs, requires superuser call). '
            'Used for GDPR Art. 15/20 export and G4-03 compliance validation.';

        -- F-04 fix: SECURITY DEFINER functions are PUBLIC-executable by default.
        -- Restrict to the application role only; PUBLIC must not call this directly.
        REVOKE EXECUTE ON FUNCTION fn_export_audit_logs(TIMESTAMPTZ, TIMESTAMPTZ, TEXT)
            FROM PUBLIC;
        GRANT  EXECUTE ON FUNCTION fn_export_audit_logs(TIMESTAMPTZ, TIMESTAMPTZ, TEXT)
            TO dpo_role;
    """)

    # -------------------------------------------------------------------------
    # 5. Pseudonymization helper — GDPR Art. 17 (right to erasure).
    #    Because audit_logs are immutable, we cannot DELETE rows.  Instead this
    #    function replaces actor_id + actor_email with a SHA-256 hash of the
    #    original actor UUID.  The row remains in the audit trail; PII is removed.
    #
    #    NOTE: This function intentionally bypasses the immutability trigger by
    #    temporarily disabling it (superuser action — requires DBA execution).
    #    It is NOT called automatically; it must be invoked by the DPO/DBA with
    #    explicit authorization after a verified GDPR erasure request.
    # -------------------------------------------------------------------------
    op.execute("""
        CREATE OR REPLACE FUNCTION fn_pseudonymize_audit_actor(p_actor_uuid UUID)
        RETURNS INTEGER
        LANGUAGE plpgsql
        SECURITY DEFINER
        AS $$
        DECLARE
            v_hash TEXT;
            v_count INTEGER;
        BEGIN
            -- SHA-256 of the actor UUID truncated to 36 chars (fits VARCHAR(36)).
            -- A 36-hex-char prefix of SHA-256 is still an irreversible one-way token.
            -- 'pseudonymized:' + 64-hex prefix = 78 chars — overflows VARCHAR(36); avoided here.
            v_hash := LEFT(encode(sha256(p_actor_uuid::TEXT::BYTEA), 'hex'), 36);

            ALTER TABLE audit_logs DISABLE TRIGGER audit_log_immutable;

            UPDATE audit_logs
            SET actor_id    = v_hash,
                actor_email = NULL,
                ip_address  = NULL
            WHERE actor_id = p_actor_uuid::TEXT;

            GET DIAGNOSTICS v_count = ROW_COUNT;

            ALTER TABLE audit_logs ENABLE TRIGGER audit_log_immutable;

            RETURN v_count;
        END;
        $$;

        COMMENT ON FUNCTION fn_pseudonymize_audit_actor IS
            'GDPR Art. 17 pseudonymization: replace actor_id + actor_email + ip_address '
            'with a one-way SHA-256 hash of the actor UUID. '
            'Requires DPO authorization and DBA execution. '
            'Returns the number of rows pseudonymized.';

        -- F-04 fix: restrict to dpo_role only — PUBLIC must not be able to invoke
        -- pseudonymization (it disables the immutability trigger internally).
        REVOKE EXECUTE ON FUNCTION fn_pseudonymize_audit_actor(UUID)
            FROM PUBLIC;
        GRANT  EXECUTE ON FUNCTION fn_pseudonymize_audit_actor(UUID)
            TO dpo_role;
    """)


def downgrade() -> None:
    # Drop functions
    op.execute("DROP FUNCTION IF EXISTS fn_pseudonymize_audit_actor(UUID);")
    op.execute(
        "DROP FUNCTION IF EXISTS fn_export_audit_logs(TIMESTAMPTZ, TIMESTAMPTZ, TEXT);"
    )

    # Drop retention index
    op.drop_index("ix_audit_purge_eligible_at", table_name="audit_logs")

    # Remove columns
    # Temporarily disable immutability trigger to allow DROP COLUMN backfill clean-up
    op.execute(
        "ALTER TABLE audit_logs DISABLE TRIGGER audit_log_immutable;"
    )
    op.drop_column("audit_logs", "legal_hold")
    op.drop_column("audit_logs", "purge_eligible_at")
    op.execute(
        "ALTER TABLE audit_logs ENABLE TRIGGER audit_log_immutable;"
    )
