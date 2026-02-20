"""
Jira Connection model — Sprint 184 (Enterprise Integrations, PROFESSIONAL+ Tier)
Stores per-organization Jira Cloud API credentials (encrypted at-rest).
"""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from cryptography.fernet import Fernet
from sqlalchemy import Column, DateTime, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.core.config import settings
from app.db.base_class import Base


class JiraConnection(Base):
    """
    Per-organization Jira Cloud API connection credentials.

    Stores encrypted API token (Fernet AES-128-CBC) so raw tokens
    are never stored in plaintext (OWASP ASVS V3.4 — credential storage).

    Fields:
        id           : UUID primary key
        organization_id: Organization UUID (FK reference — string for portability)
        jira_base_url: Jira Cloud workspace URL (e.g., https://acme.atlassian.net)
        jira_email   : Atlassian account email for Basic Auth
        api_token_enc: Fernet-encrypted Jira API token
        created_at   : Creation timestamp
        updated_at   : Last update timestamp

    Indexes:
        ix_jira_conn_org: unique per organization (one connection per org)
    """

    __tablename__ = "jira_connections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    organization_id = Column(String(36), nullable=False, unique=True, index=True)
    jira_base_url = Column(String(512), nullable=False)   # e.g., https://acme.atlassian.net
    jira_email = Column(String(254), nullable=False)
    api_token_enc = Column(Text, nullable=False)           # Fernet-encrypted API token
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_jira_conn_org", "organization_id", unique=True),
    )

    # -------------------------------------------------------------------------
    # Encryption helpers
    # -------------------------------------------------------------------------

    @classmethod
    def _fernet(cls) -> Fernet:
        """Return Fernet instance keyed by settings.FERNET_KEY (or SECRET_KEY padded)."""
        key = getattr(settings, "FERNET_KEY", None)
        if not key:
            # Derive 32-byte Fernet key from SECRET_KEY (first 32 bytes, base64-padded)
            import base64
            raw = settings.SECRET_KEY.encode()[:32].ljust(32, b"\x00")
            key = base64.urlsafe_b64encode(raw)
        return Fernet(key)

    @classmethod
    def encrypt_token(cls, plain_token: str) -> str:
        """Encrypt a plain API token. Returns base64 Fernet ciphertext."""
        return cls._fernet().encrypt(plain_token.encode()).decode()

    @classmethod
    def decrypt_token(cls, encrypted: str) -> str:
        """Decrypt a Fernet-encrypted API token back to plaintext."""
        return cls._fernet().decrypt(encrypted.encode()).decode()

    def get_plain_token(self) -> str:
        """Convenience: decrypt and return the stored API token."""
        return self.decrypt_token(self.api_token_enc)

    def __repr__(self) -> str:
        return f"<JiraConnection(org={self.organization_id}, url={self.jira_base_url})>"
