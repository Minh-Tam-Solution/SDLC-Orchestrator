"""
Enterprise SSO SQLAlchemy models — Sprint 183.

Maps to tables created by s182_001_enterprise_sso.py migration:
    - enterprise_sso_configs  (13 columns, per ADR-061)
    - sso_sessions            (7 columns, SHA256 hash only, ADR-061 Decision 5)

Security:
    - id_token_hash: SHA256(id_token) ONLY — raw tokens never stored
    - ENTERPRISE tier only — enforced at route layer

Sprint 182: tables created.
Sprint 183: models + services implemented (ADR-063/ADR-064).
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base_class import Base


class EnterpriseSsoConfig(Base):
    """
    SSO configuration per organization per provider.

    One row per (organization_id, provider) pair (unique constraint).
    Stores SAML 2.0 IdP metadata OR Azure AD tenant/client credentials.

    Columns:
        id              — UUID PK (gen_random_uuid)
        organization_id — FK → organizations.id (CASCADE delete)
        provider        — 'saml' | 'azure_ad' (VARCHAR 20)
        is_enabled      — Whether SSO is currently active
        idp_entity_id   — SAML: IdP entity ID URL
        idp_sso_url     — SAML: IdP SSO URL (redirect binding)
        idp_x509_cert   — SAML: IdP public certificate (PEM)
        sp_entity_id    — SAML: Our SP entity ID URL
        tenant_id       — Azure AD: tenant GUID
        client_id       — Azure AD: app registration client ID
        role_mapping    — JSONB: IdP groups → Orchestrator roles
        created_at      — Creation timestamp
        updated_at      — Last update timestamp
    """

    __tablename__ = "enterprise_sso_configs"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
        nullable=False,
    )
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    provider: Mapped[str] = mapped_column(String(20), nullable=False)
    is_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false"
    )

    # SAML 2.0 fields (nullable when provider='azure_ad')
    idp_entity_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    idp_sso_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    idp_x509_cert: Mapped[str | None] = mapped_column(Text, nullable=True)
    sp_entity_id: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Azure AD fields (nullable when provider='saml')
    tenant_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    client_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    # Role mapping JSONB: {"group_mappings": {"Admins": "admin"}, "default_role": "developer"}
    role_mapping: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default="{}"
    )

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default=func.now(),
        onupdate=func.now(),
    )

    # Unique constraint: one SSO config per (org, provider) pair
    __table_args__ = (
        UniqueConstraint(
            "organization_id", "provider", name="uq_sso_config_org_provider"
        ),
    )

    # Relationships
    sso_sessions: Mapped[list["SsoSession"]] = relationship(
        "SsoSession", back_populates="sso_config", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"<EnterpriseSsoConfig id={self.id} org={self.organization_id}"
            f" provider={self.provider!r} enabled={self.is_enabled}>"
        )


class SsoSession(Base):
    """
    Active SSO session metadata.

    Security: id_token_hash stores SHA256(id_token) ONLY — raw tokens never
    stored in the database (ADR-061 Decision 5, OWASP ASVS V8.3).

    Columns:
        id              — UUID PK
        user_id         — FK → users.id (CASCADE delete)
        sso_config_id   — FK → enterprise_sso_configs.id (CASCADE delete)
        subject_id      — SAML NameID or OIDC sub claim (lookup key for JIT)
        id_token_hash   — SHA256(id_token) hex string, 64 chars
        expires_at      — Session expiry (from IdP token exp claim)
        created_at      — Login timestamp
    """

    __tablename__ = "sso_sessions"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
        nullable=False,
    )
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sso_config_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("enterprise_sso_configs.id", ondelete="CASCADE"),
        nullable=False,
    )
    # SAML NameID or OIDC sub claim — used as JIT provisioning lookup key
    subject_id: Mapped[str] = mapped_column(String(255), nullable=False)
    # SHA256(id_token) — 64-char hex. Raw token NEVER stored (ADR-061 D5)
    id_token_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    sso_config: Mapped["EnterpriseSsoConfig"] = relationship(
        "EnterpriseSsoConfig", back_populates="sso_sessions"
    )

    def __repr__(self) -> str:
        return (
            f"<SsoSession id={self.id} user={self.user_id}"
            f" config={self.sso_config_id} expires={self.expires_at}>"
        )
