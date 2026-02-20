"""Sprint 182: enterprise_sso_configs + sso_sessions tables

Revision ID: s182_001
Revises: s181_001
Create Date: 2026-02-19 00:00:00.000000

CONTEXT:
- Sprint 182 "Enterprise SSO Design + Teams Channel" — ADR-061
- Adds two tables for ENTERPRISE-tier SSO configuration and session tracking
- enterprise_sso_configs: stores SAML 2.0 / Azure AD IdP configuration per organization
- sso_sessions: stores active SSO session metadata (subject, expiry, id_token_hash only)

SECURITY:
- id_token_hash stores SHA256(id_token) ONLY — raw tokens never persisted (ADR-061 Decision 5)
- ENTERPRISE-only tables; LITE/STANDARD tiers have no access (ADR-059 tier gate)
- uq_sso_config_org_provider ensures one SSO config per (org, provider) pair

SAFETY:
- Upgrade: CREATE TABLE (additive-only; no existing tables modified)
- Downgrade: DROP TABLE (safe while no dependent rows exist)
- All FKs reference existing tables (organizations, users)

CTO REVIEW:
- ADR-061 approved February 19, 2026
- 5 locked decisions: protocol (SAML + Azure AD), ACS URL, JIT, SCIM deferred, token security
- Reference: ADR-061-Enterprise-SSO.md
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers
revision = "s182_001"
down_revision = "s181_001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create enterprise_sso_configs and sso_sessions tables."""

    # ──────────────────────────────────────────────────────────────────────
    # Table: enterprise_sso_configs (13 columns)
    # ──────────────────────────────────────────────────────────────────────
    op.create_table(
        "enterprise_sso_configs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        # Protocol: 'saml' | 'azure_ad'
        sa.Column("provider", sa.String(20), nullable=False),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default="false"),
        # SAML 2.0 fields (nullable — populated only when provider='saml')
        sa.Column("idp_entity_id", sa.Text(), nullable=True),
        sa.Column("idp_sso_url", sa.Text(), nullable=True),
        sa.Column("idp_x509_cert", sa.Text(), nullable=True),
        sa.Column("sp_entity_id", sa.Text(), nullable=True),
        # Azure AD fields (nullable — populated only when provider='azure_ad')
        sa.Column("tenant_id", sa.String(36), nullable=True),
        sa.Column("client_id", sa.String(36), nullable=True),
        # Role mapping: IdP groups → Orchestrator RBAC roles (JSON object)
        # Example: {"group_mappings": {"SDLC-Admins": "admin"}, "default_role": "member"}
        sa.Column(
            "role_mapping",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        # Audit timestamps
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        # One SSO config per (organization, provider) pair
        sa.UniqueConstraint(
            "organization_id",
            "provider",
            name="uq_sso_config_org_provider",
        ),
    )

    # Index: fast lookup by organization
    op.create_index(
        "idx_sso_config_org",
        "enterprise_sso_configs",
        ["organization_id"],
    )

    # ──────────────────────────────────────────────────────────────────────
    # Table: sso_sessions (7 columns)
    # Security: only id_token_hash (SHA256) stored — never raw id_token
    # ──────────────────────────────────────────────────────────────────────
    op.create_table(
        "sso_sessions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "sso_config_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("enterprise_sso_configs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        # SAML NameID or OIDC sub claim — used as lookup key for JIT provisioning
        sa.Column("subject_id", sa.String(255), nullable=False),
        # SHA256(id_token) — 64-char hex string. Raw id_token is NEVER stored (ADR-061 D5)
        sa.Column("id_token_hash", sa.String(64), nullable=False),
        # Session expiry (from IdP token exp claim)
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )

    # Index: lookup sessions by user
    op.create_index(
        "idx_sso_sessions_user",
        "sso_sessions",
        ["user_id"],
    )
    # Index: eviction queries (expired session cleanup)
    op.create_index(
        "idx_sso_sessions_expiry",
        "sso_sessions",
        ["expires_at"],
    )
    # Index: JIT provisioning lookup — find existing subject within a config
    op.create_index(
        "idx_sso_sessions_subject",
        "sso_sessions",
        ["sso_config_id", "subject_id"],
    )


def downgrade() -> None:
    """Drop sso_sessions and enterprise_sso_configs tables.

    Order matters: sso_sessions has FK → enterprise_sso_configs, so
    sso_sessions must be dropped first.
    """
    # Drop indices first (implicit on DROP TABLE in PG, but explicit for clarity)
    op.drop_index("idx_sso_sessions_subject", table_name="sso_sessions")
    op.drop_index("idx_sso_sessions_expiry", table_name="sso_sessions")
    op.drop_index("idx_sso_sessions_user", table_name="sso_sessions")
    op.drop_table("sso_sessions")

    op.drop_index("idx_sso_config_org", table_name="enterprise_sso_configs")
    op.drop_table("enterprise_sso_configs")
