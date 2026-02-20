"""
Enterprise SSO Pydantic schemas — Sprint 183.

Request/response models for:
    - SSO configuration (create, read)
    - SSO login initiation
    - SSO session management

ADR-061: ACS URL pattern = /api/v1/enterprise/sso/{provider}/callback
ADR-061 Decision 5: id_token never returned in response — only session metadata.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# ──────────────────────────────────────────────────────────────────────────────
# SSO Configuration schemas
# ──────────────────────────────────────────────────────────────────────────────

class SsoConfigCreate(BaseModel):
    """Create or replace SSO configuration for an organization."""

    organization_id: UUID = Field(..., description="Organization UUID")
    provider: Literal["saml", "azure_ad"] = Field(
        ..., description="SSO provider: 'saml' or 'azure_ad'"
    )
    is_enabled: bool = Field(default=True, description="Activate SSO immediately")

    # SAML fields (required when provider='saml')
    idp_entity_id: Optional[str] = Field(
        None, description="SAML: IdP entity ID URL"
    )
    idp_sso_url: Optional[str] = Field(
        None, description="SAML: IdP Single Sign-On URL (redirect binding)"
    )
    idp_x509_cert: Optional[str] = Field(
        None, description="SAML: IdP public X.509 certificate (PEM)"
    )
    sp_entity_id: Optional[str] = Field(
        None, description="SAML: Service Provider entity ID URL"
    )

    # Azure AD fields (required when provider='azure_ad')
    tenant_id: Optional[str] = Field(
        None, max_length=36, description="Azure AD: tenant GUID"
    )
    client_id: Optional[str] = Field(
        None, max_length=36, description="Azure AD: app registration client ID"
    )

    # Role mapping
    role_mapping: dict = Field(
        default_factory=dict,
        description=(
            "IdP group → Orchestrator role mapping. "
            "Example: {\"group_mappings\": {\"SDLC-Admins\": \"admin\"}, "
            "\"default_role\": \"developer\"}"
        ),
    )

    @field_validator("idp_sso_url", "idp_entity_id", "sp_entity_id")
    @classmethod
    def validate_url_field(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.startswith(("http://", "https://")):
            raise ValueError("URL fields must start with http:// or https://")
        return v


class SsoConfigResponse(BaseModel):
    """SSO configuration read response (no sensitive fields)."""

    id: UUID
    organization_id: UUID
    provider: str
    is_enabled: bool
    sp_entity_id: Optional[str]
    idp_entity_id: Optional[str]
    # idp_sso_url returned for admin visibility (not sensitive)
    idp_sso_url: Optional[str]
    # idp_x509_cert: omitted from response (long PEM, not useful for display)
    tenant_id: Optional[str]
    client_id: Optional[str]
    role_mapping: dict
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ──────────────────────────────────────────────────────────────────────────────
# Login / callback schemas
# ──────────────────────────────────────────────────────────────────────────────

class SsoLoginInitiateRequest(BaseModel):
    """Request body for SSO login initiation."""

    organization_id: UUID = Field(..., description="Organization UUID")


class SsoLoginResponse(BaseModel):
    """Response for SSO login initiation — redirect URL for browser."""

    redirect_url: str = Field(..., description="IdP redirect URL for browser")
    provider: str = Field(..., description="SSO provider identifier")
    # Azure AD only: state token to validate in callback
    state: Optional[str] = Field(
        None, description="CSRF state token (Azure AD only)"
    )


class SsoSessionResponse(BaseModel):
    """Active SSO session metadata (no raw tokens, ADR-061 D5)."""

    session_id: UUID = Field(..., description="SSO session UUID")
    user_id: UUID = Field(..., description="Authenticated user UUID")
    provider: str = Field(..., description="SSO provider used")
    subject_id: str = Field(..., description="IdP subject identifier (NameID/sub)")
    expires_at: datetime = Field(..., description="Session expiry (UTC)")
    created_at: datetime = Field(..., description="Login timestamp (UTC)")


class SsoLogoutRequest(BaseModel):
    """Request body for SSO logout."""

    session_id: UUID = Field(..., description="SSO session UUID to invalidate")


# ──────────────────────────────────────────────────────────────────────────────
# Internal JIT provisioning result
# ──────────────────────────────────────────────────────────────────────────────

class JitProvisionResult(BaseModel):
    """Result of JIT (Just-in-Time) user provisioning."""

    user_id: UUID
    email: str
    display_name: str
    role: str
    is_new_user: bool = Field(
        ..., description="True if user was created; False if existing user matched"
    )
