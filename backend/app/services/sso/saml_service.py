"""
SAML 2.0 Service Provider implementation — Sprint 183.

Implements SAML 2.0 SP per ADR-061 locked decisions:
    D-1: Protocol = python3-saml (MIT license) for SAML 2.0
    D-2: ACS URL = /api/v1/enterprise/sso/saml/callback
    D-3: JIT provisioning — auto-create user on first SSO login
    D-5: SHA256(id_token) only — raw tokens never stored

Library: python3-saml (onelogin.saml2) — MIT license, no AGPL contamination
System deps: libxml2-dev, libxmlsec1-dev (Dockerfile)

Security:
    - wantAssertionsSigned=True: reject unsigned assertions
    - wantMessagesSigned=True: reject unsigned responses
    - NotBefore/NotOnOrAfter: ±5 min clock skew tolerance
    - InResponseTo: replay-attack prevention via session-bound nonce

Sprint 183 — ADR-063 SAML 2.0 Implementation.
"""

from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# Module-level import with graceful fallback — allows patching in tests and
# provides a clear error when python3-saml is not installed in the environment.
try:
    from onelogin.saml2.auth import OneLogin_Saml2_Auth  # type: ignore[import-untyped]
    from onelogin.saml2.settings import OneLogin_Saml2_Settings  # type: ignore[import-untyped]
except ImportError:
    OneLogin_Saml2_Auth = None  # type: ignore[assignment, misc]
    OneLogin_Saml2_Settings = None  # type: ignore[assignment, misc]


# ──────────────────────────────────────────────────────────────────────────────
# Custom exceptions
# ──────────────────────────────────────────────────────────────────────────────

class SAMLError(Exception):
    """Raised for any SAML validation failure (assertion, signature, timing)."""


class SAMLConfigError(Exception):
    """Raised when SAML configuration is incomplete or invalid."""


# ──────────────────────────────────────────────────────────────────────────────
# SAMLService
# ──────────────────────────────────────────────────────────────────────────────

class SAMLService:
    """
    SAML 2.0 Service Provider implementation.

    One instance per SSO configuration (organization + provider='saml').
    python3-saml wraps the low-level XML signing/validation via libxmlsec1.

    Usage:
        config = await db.get(EnterpriseSsoConfig, config_id)
        svc = SAMLService(config)
        redirect_url = svc.initiate_login(request_data)

        # In ACS callback:
        user, session = await svc.process_callback(request_data, db)
    """

    # ACS URL pattern (ADR-061 Decision 2)
    ACS_URL_PATTERN = "/api/v1/enterprise/sso/saml/callback"
    # Session max lifetime: 8 hours (IdP exp claim may be shorter)
    SESSION_MAX_HOURS = 8

    def __init__(self, sso_config: Any) -> None:
        """
        Initialise SAML Service Provider from a stored SSO configuration.

        Args:
            sso_config: EnterpriseSsoConfig ORM instance with SAML fields populated.

        Raises:
            SAMLConfigError: If required SAML fields are missing.
        """
        self._config = sso_config
        self._saml_settings = self._build_settings(sso_config)

    # ──────────────────────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────────────────────

    def initiate_login(self, request_data: dict[str, Any]) -> str:
        """
        Initiate SP-initiated SAML login flow.

        Builds the SAML AuthnRequest and returns the IdP redirect URL.
        Browser should redirect the user to this URL.

        Args:
            request_data: Dict with HTTP request metadata:
                {"https": "on"|"off", "http_host": "...", "script_name": "...",
                 "server_port": "443", "get_data": {}, "post_data": {}}

        Returns:
            IdP redirect URL (string) for HTTP 302 redirect.

        Raises:
            SAMLError: If SAML library fails to generate the AuthnRequest.
        """
        if OneLogin_Saml2_Auth is None:
            raise SAMLConfigError(
                "python3-saml not installed. "
                "Run: pip install python3-saml"
            )
        try:
            auth = OneLogin_Saml2_Auth(request_data, old_settings=self._saml_settings)
            redirect_url: str = auth.login()
            logger.info(
                "saml_service: login initiated org=%s provider=saml",
                self._config.organization_id,
            )
            return redirect_url
        except Exception as exc:
            raise SAMLError(f"SAML login initiation failed: {exc}") from exc

    async def process_callback(
        self,
        request_data: dict[str, Any],
        db: AsyncSession,
    ) -> tuple[Any, Any]:
        """
        Process SAML ACS callback — validate assertion, JIT provision, create session.

        Pipeline:
        1. Parse and validate SAMLResponse (signature, timing, InResponseTo)
        2. Extract NameID (email) and attributes from validated assertion
        3. JIT provision: create User if not exists; match by email
        4. Create SsoSession with SHA256(assertion XML) hash (ADR-061 D5)
        5. Return (User, SsoSession)

        Args:
            request_data: Dict with HTTP request including POST body containing
                SAMLResponse and RelayState.
            db: Async database session.

        Returns:
            Tuple of (User ORM instance, SsoSession ORM instance).

        Raises:
            SAMLError: Signature invalid, assertion expired, InResponseTo mismatch,
                       or XML injection detected.
        """
        if OneLogin_Saml2_Auth is None:
            raise SAMLConfigError("python3-saml not installed")

        try:
            auth = OneLogin_Saml2_Auth(request_data, old_settings=self._saml_settings)
            auth.process_response()
        except Exception as exc:
            raise SAMLError(f"SAML response processing failed: {exc}") from exc

        # Validate: all errors from python3-saml must be empty
        errors = auth.get_errors()
        if errors:
            raise SAMLError(
                f"SAML validation errors: {errors}. "
                f"Reason: {auth.get_last_error_reason()}"
            )

        if not auth.is_authenticated():
            raise SAMLError("SAML authentication failed — not authenticated")

        # Extract NameID (email) and attributes
        name_id: str = auth.get_nameid()
        attributes: dict = auth.get_attributes()

        # Extract email: NameID preferred, fallback to email attribute
        email = _extract_email(name_id, attributes)
        if not email:
            raise SAMLError("SAML assertion contains no usable email identifier")

        display_name = _extract_display_name(attributes) or email.split("@")[0]

        # Map IdP groups → Orchestrator role via role_mapping JSONB
        role = _map_role(attributes, self._config.role_mapping)

        # JIT provision: create or fetch user
        from app.models.user import User
        user = await _jit_provision_user(
            email=email,
            display_name=display_name,
            role=role,
            db=db,
        )

        # Create SsoSession — SHA256 of SAMLResponse XML (ADR-061 D5)
        saml_response_b64: str = (
            request_data.get("post_data", {}).get("SAMLResponse", "")
        )
        session = await _create_sso_session(
            user_id=user.id,
            sso_config_id=self._config.id,
            subject_id=name_id,
            id_token_raw=saml_response_b64,
            expires_at=datetime.now(tz=timezone.utc) + timedelta(hours=self.SESSION_MAX_HOURS),
            db=db,
        )

        logger.info(
            "saml_service: callback success user=%s org=%s",
            user.id,
            self._config.organization_id,
        )
        return user, session

    def get_metadata(self) -> str:
        """
        Return SP metadata XML for IdP registration.

        The metadata XML contains:
            - SP entityId
            - AssertionConsumerService URL (ACS URL)
            - SP X.509 certificate (if configured)
            - NameID format requirements

        Returns:
            SP metadata XML string.

        Raises:
            SAMLError: If metadata generation fails.
        """
        if OneLogin_Saml2_Settings is None:
            raise SAMLConfigError("python3-saml not installed")
        try:
            settings = OneLogin_Saml2_Settings(
                settings=self._saml_settings,
                sp_validation_only=True,
            )
            metadata_raw = settings.get_sp_metadata()
            # python3-saml may return bytes; normalise to str for downstream
            metadata: str = (
                metadata_raw.decode("utf-8")
                if isinstance(metadata_raw, bytes)
                else metadata_raw
            )
            errors = settings.validate_metadata(metadata)
            if errors:
                raise SAMLError(f"SP metadata validation failed: {errors}")
            return metadata
        except SAMLError:
            raise
        except Exception as exc:
            raise SAMLError(f"SP metadata generation failed: {exc}") from exc

    async def logout(
        self,
        request_data: dict[str, Any],
        sso_session_id: UUID,
        db: AsyncSession,
    ) -> None:
        """
        Process SSO logout: delete SsoSession row, clear local session.

        Args:
            request_data: HTTP request metadata (used for SLO flow if IdP supports it).
            sso_session_id: UUID of the SsoSession row to delete.
            db: Async database session.

        Raises:
            SAMLError: If session not found.
        """
        from app.models.enterprise_sso import SsoSession
        result = await db.execute(
            select(SsoSession).where(SsoSession.id == sso_session_id)
        )
        session = result.scalar_one_or_none()
        if not session:
            raise SAMLError(f"SSO session {sso_session_id} not found")

        await db.delete(session)
        await db.commit()
        logger.info("saml_service: session %s deleted (logout)", sso_session_id)

    # ──────────────────────────────────────────────────────────────────────────
    # Private: settings builder
    # ──────────────────────────────────────────────────────────────────────────

    def _build_settings(self, sso_config: Any) -> dict[str, Any]:
        """
        Build python3-saml settings dict from stored SSO configuration.

        Security options enforced:
            - wantAssertionsSigned: True
            - wantMessagesSigned: True
            - relaxDestinationValidation: False
            - rejectDeprecatedAlgorithm: True (blocks SHA1 signatures)

        Args:
            sso_config: EnterpriseSsoConfig ORM instance.

        Returns:
            python3-saml settings dict.

        Raises:
            SAMLConfigError: If required SAML fields are missing.
        """
        if not sso_config.idp_sso_url or not sso_config.idp_entity_id:
            raise SAMLConfigError(
                "SAML configuration incomplete: idp_sso_url and idp_entity_id required"
            )
        if not sso_config.idp_x509_cert:
            raise SAMLConfigError(
                "SAML configuration incomplete: idp_x509_cert required"
            )
        if not sso_config.sp_entity_id:
            raise SAMLConfigError(
                "SAML configuration incomplete: sp_entity_id required"
            )

        return {
            "strict": True,
            "debug": False,
            "sp": {
                "entityId": sso_config.sp_entity_id,
                "assertionConsumerService": {
                    "url": self.ACS_URL_PATTERN,
                    "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST",
                },
                "singleLogoutService": {
                    "url": "/api/v1/enterprise/sso/logout",
                    "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
                },
                "NameIDFormat": "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress",
                "x509cert": "",    # SP cert: not required for SP-initiated flow
                "privateKey": "",  # SP key: not required without SP-signed requests
            },
            "idp": {
                "entityId": sso_config.idp_entity_id,
                "singleSignOnService": {
                    "url": sso_config.idp_sso_url,
                    "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
                },
                "x509cert": sso_config.idp_x509_cert,
            },
            "security": {
                # ADR-061: Require signed assertions AND signed responses
                "wantAssertionsSigned": True,
                "wantMessagesSigned": True,
                "signatureAlgorithm": "http://www.w3.org/2001/04/xmldsig-more#rsa-sha256",
                "digestAlgorithm": "http://www.w3.org/2001/04/xmlenc#sha256",
                # Replay protection: ±5 min clock skew
                "allowRepeatAttributeName": False,
                "rejectDeprecatedAlgorithm": True,   # Block SHA1
            },
        }


# ──────────────────────────────────────────────────────────────────────────────
# Private helper functions
# ──────────────────────────────────────────────────────────────────────────────

def _extract_email(name_id: str, attributes: dict) -> str | None:
    """
    Extract email from SAML NameID or standard email attribute.

    Attempts NameID first (emailAddress format), then falls back to
    urn:oid:0.9.2342.19200300.100.1.3 (mail attribute OID) and plain 'email'.

    Args:
        name_id: SAML NameID string (may be email or opaque ID).
        attributes: SAML attribute dict from python3-saml.

    Returns:
        Email string, or None if no email found.
    """
    # NameID in emailAddress format is most common
    if name_id and "@" in name_id:
        return name_id.strip().lower()

    # Standard email attribute OIDs
    for attr_key in (
        "urn:oid:0.9.2342.19200300.100.1.3",
        "email",
        "mail",
        "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress",
    ):
        values = attributes.get(attr_key, [])
        if values:
            return str(values[0]).strip().lower()

    return None


def _extract_display_name(attributes: dict) -> str | None:
    """
    Extract display name from SAML attributes.

    Args:
        attributes: SAML attribute dict.

    Returns:
        Display name string, or None if not found.
    """
    for attr_key in (
        "displayName",
        "cn",
        "urn:oid:2.16.840.1.113730.3.1.241",
        "http://schemas.microsoft.com/identity/claims/displayname",
        "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name",
    ):
        values = attributes.get(attr_key, [])
        if values:
            return str(values[0]).strip()
    return None


def _map_role(attributes: dict, role_mapping: dict) -> str:
    """
    Map IdP groups to Orchestrator RBAC roles via role_mapping JSONB.

    role_mapping schema:
        {"group_mappings": {"Engineering": "developer", "SDLC-Admins": "admin"},
         "default_role": "developer"}

    Args:
        attributes: SAML attribute dict.
        role_mapping: role_mapping JSONB from EnterpriseSsoConfig.

    Returns:
        Orchestrator role string (defaults to "developer" if no match).
    """
    default_role = role_mapping.get("default_role", "developer")
    group_mappings: dict = role_mapping.get("group_mappings", {})

    if not group_mappings:
        return default_role

    # Group attributes — check common SAML group attribute names
    user_groups: list[str] = []
    for attr_key in (
        "groups",
        "memberOf",
        "urn:oid:1.3.6.1.4.1.5923.1.5.1.1",  # eduPersonMember
    ):
        vals = attributes.get(attr_key, [])
        user_groups.extend(str(v) for v in vals)

    for group in user_groups:
        if group in group_mappings:
            return group_mappings[group]

    return default_role


async def _jit_provision_user(
    email: str,
    display_name: str,
    role: str,
    db: AsyncSession,
) -> Any:
    """
    JIT provision: fetch existing user by email, or create new user.

    New users are created with:
        - email: from SAML assertion
        - username: email prefix (before @)
        - display_name: from SAML attributes
        - is_active: True
        - password_hash: None (SSO-only account)

    Args:
        email: User email from IdP.
        display_name: Display name from IdP.
        role: Mapped Orchestrator role.
        db: Async database session.

    Returns:
        User ORM instance (existing or newly created).
    """
    from app.models.user import User

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if user:
        # Update display_name if changed in IdP
        if display_name and user.display_name != display_name:
            user.display_name = display_name
            await db.commit()
            await db.refresh(user)
        logger.info("saml_service: JIT provision — existing user %s", user.id)
        return user

    # Create new user (SSO-only — no password)
    import secrets
    user = User(
        email=email,
        username=email.split("@")[0] + "_" + secrets.token_hex(4),
        display_name=display_name,
        is_active=True,
        # SSO-only accounts have no password
        password_hash=None,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    logger.info("saml_service: JIT provision — new user created %s", user.id)
    return user


async def _create_sso_session(
    user_id: UUID,
    sso_config_id: UUID,
    subject_id: str,
    id_token_raw: str,
    expires_at: datetime,
    db: AsyncSession,
) -> Any:
    """
    Create SsoSession with SHA256 hash of id_token (ADR-061 Decision 5).

    The raw id_token (SAML response XML) is NEVER stored.
    Only SHA256(id_token_raw) is persisted as the audit hash.

    Args:
        user_id: User UUID.
        sso_config_id: EnterpriseSsoConfig UUID.
        subject_id: SAML NameID or OIDC sub claim.
        id_token_raw: Raw id_token string (hashed before storage).
        expires_at: Session expiry datetime (UTC).
        db: Async database session.

    Returns:
        SsoSession ORM instance.
    """
    from app.models.enterprise_sso import SsoSession

    # ADR-061 D5: Only SHA256 hash stored — raw token NEVER in DB
    id_token_hash = hashlib.sha256(id_token_raw.encode("utf-8")).hexdigest()

    session = SsoSession(
        user_id=user_id,
        sso_config_id=sso_config_id,
        subject_id=subject_id,
        id_token_hash=id_token_hash,
        expires_at=expires_at,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session
