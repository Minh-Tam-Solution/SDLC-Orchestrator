"""
Azure AD OAuth 2.0 PKCE service — Sprint 183.

Implements Azure AD OIDC via Authorization Code Flow with PKCE S256 per
ADR-061 locked decisions:
    D-1: Protocol = msal (MIT license) + PKCE S256
    D-2: Callback URL = /api/v1/enterprise/sso/azure-ad/callback
    D-3: JIT provisioning from JWT claims
    D-5: SHA256(id_token) only — raw id_token never stored

Library: msal (MIT license), httpx (BSD-3), PyJWT (MIT)

PKCE S256 flow:
    1. generate code_verifier (64 bytes), compute code_challenge = base64url(sha256(verifier))
    2. Redirect user to Azure AD with code_challenge + state (32-byte random)
    3. Azure AD redirects back with code
    4. Exchange code + code_verifier for id_token
    5. Validate JWT via JWKS (cached 1h)
    6. JIT provision user; create SsoSession

Sprint 183 — ADR-064 Azure AD Implementation.
"""

from __future__ import annotations

import base64
import hashlib
import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# Module-level PyJWT import — allows test patching at module level.
# PyJWT (MIT license) is always installed alongside the backend; this try/except
# is defensive for environments where it might be absent.
try:
    import jwt  # type: ignore[import-untyped]
    from jwt import PyJWKClient, PyJWTError  # type: ignore[import-untyped]
except ImportError:
    jwt = None  # type: ignore[assignment]
    PyJWKClient = None  # type: ignore[assignment, misc]
    PyJWTError = Exception  # type: ignore[assignment, misc]


# Azure AD OIDC discovery endpoint pattern
_AZURE_AUTHORITY_BASE = "https://login.microsoftonline.com"
_AZURE_JWKS_URL_PATTERN = (
    "https://login.microsoftonline.com/{tenant_id}/discovery/v2.0/keys"
)
_AZURE_TOKEN_URL_PATTERN = (
    "https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
)
_AZURE_AUTH_URL_PATTERN = (
    "https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/authorize"
)

# JWKS cache TTL: 1 hour (Azure AD rotates keys weekly, but cache to avoid latency)
_JWKS_CACHE_TTL_SECONDS = 3600
# State token TTL: 5 minutes (prevents CSRF window exploitation)
_STATE_TTL_SECONDS = 300
# Token max age: 1 hour for id_tokens (Azure AD default)
_SESSION_MAX_HOURS = 8


# ──────────────────────────────────────────────────────────────────────────────
# Custom exceptions
# ──────────────────────────────────────────────────────────────────────────────

class AzureADError(Exception):
    """Raised for Azure AD authentication failures."""


class AzureADConfigError(Exception):
    """Raised when Azure AD configuration is incomplete."""


# ──────────────────────────────────────────────────────────────────────────────
# PKCE utilities
# ──────────────────────────────────────────────────────────────────────────────

def generate_pkce_pair() -> tuple[str, str]:
    """
    Generate PKCE code_verifier and S256 code_challenge pair.

    RFC 7636 S256 method:
        code_challenge = BASE64URL(SHA256(ASCII(code_verifier)))

    Args: none

    Returns:
        Tuple of (code_verifier, code_challenge) — both URL-safe base64 strings.
        code_verifier: 64 bytes of random data (URL-safe base64, ~86 chars)
        code_challenge: SHA256 of verifier, base64url-encoded (43 chars)
    """
    # 64 random bytes → URL-safe base64 without padding (~86 chars)
    code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(64)).rstrip(b"=").decode()
    # S256: SHA256 of verifier → base64url
    code_challenge = (
        base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode("ascii")).digest()
        )
        .rstrip(b"=")
        .decode()
    )
    return code_verifier, code_challenge


# ──────────────────────────────────────────────────────────────────────────────
# AzureADService
# ──────────────────────────────────────────────────────────────────────────────

class AzureADService:
    """
    Azure AD OIDC Authorization Code + PKCE S256 service.

    One instance per SSO configuration (organization + provider='azure_ad').

    Usage:
        config = await db.get(EnterpriseSsoConfig, config_id)
        svc = AzureADService(config)

        # Step 1: initiate login
        auth_url, code_verifier, state = svc.initiate_login()
        # Store code_verifier + state in Redis with 5-min TTL
        # Redirect user to auth_url

        # Step 2: process callback
        user, session = await svc.process_callback(code, state, code_verifier, db)
    """

    # Scopes required for OIDC user info
    SCOPES = ["openid", "profile", "email"]

    def __init__(self, sso_config: Any) -> None:
        """
        Initialise Azure AD service from stored SSO configuration.

        Args:
            sso_config: EnterpriseSsoConfig ORM instance with Azure AD fields.

        Raises:
            AzureADConfigError: If tenant_id or client_id are missing.
        """
        if not sso_config.tenant_id or not sso_config.client_id:
            raise AzureADConfigError(
                "Azure AD configuration incomplete: tenant_id and client_id required"
            )

        self._config = sso_config
        self._tenant_id: str = sso_config.tenant_id
        self._client_id: str = sso_config.client_id
        # In-memory JWKS cache: {"keys": [...], "cached_at": datetime}
        self._jwks_cache: dict[str, Any] = {}

    # ──────────────────────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────────────────────

    def initiate_login(
        self, redirect_uri: str | None = None
    ) -> tuple[str, str, str]:
        """
        Initiate Azure AD PKCE login flow.

        Generates a PKCE code_verifier, S256 code_challenge, and CSRF state token.
        Caller must store (code_verifier, state, redirect_uri) in Redis with 5-min TTL
        and redirect the user to the returned auth_url.

        Args:
            redirect_uri: Absolute callback URL registered in the Azure AD app.
                          Must match the redirect_uri used in process_callback.
                          Example: "https://app.example.com/api/v1/enterprise/sso/azure-ad/callback"
                          If None, falls back to the relative path (dev/test only).

        Returns:
            Tuple of (auth_url, code_verifier, state):
                auth_url:       Azure AD authorization URL with code_challenge
                code_verifier:  PKCE verifier to pass to process_callback
                state:          CSRF state token (32 bytes, URL-safe base64)

        Raises:
            AzureADConfigError: If tenant_id or client_id are missing.
        """
        code_verifier, code_challenge = generate_pkce_pair()
        state = secrets.token_urlsafe(32)

        auth_url = self._build_auth_url(code_challenge, state, redirect_uri=redirect_uri)

        logger.info(
            "azure_ad_service: login initiated org=%s tenant=%s",
            self._config.organization_id,
            self._tenant_id,
        )
        return auth_url, code_verifier, state

    async def process_callback(
        self,
        code: str,
        state: str,
        code_verifier: str,
        db: AsyncSession,
        redirect_uri: str | None = None,
    ) -> tuple[Any, Any]:
        """
        Process Azure AD callback — exchange code, validate JWT, JIT provision.

        Pipeline:
        1. Validate state (caller must verify against stored state before calling)
        2. Exchange authorization code + code_verifier for id_token via token endpoint
        3. Validate id_token JWT signature via JWKS (cached 1h)
        4. Validate JWT claims: iss, aud, exp
        5. JIT provision user from JWT claims (email, name)
        6. Create SsoSession with SHA256(id_token) (ADR-061 D5)

        Args:
            code:           Authorization code from Azure AD callback.
            state:          CSRF state token (caller validates before calling).
            code_verifier:  PKCE verifier (must match code_challenge from initiate_login).
            db:             Async database session.
            redirect_uri:   Absolute callback URL — must match the URI used in initiate_login
                            and the Azure AD app registration. If None, falls back to relative
                            path (dev/test only).

        Returns:
            Tuple of (User ORM instance, SsoSession ORM instance).

        Raises:
            AzureADError: Token exchange failed, JWT invalid, or state mismatch.
        """
        # Exchange code for id_token — redirect_uri must match authorization request exactly
        token_response = await self._exchange_code_for_token(
            code, code_verifier, redirect_uri=redirect_uri
        )

        id_token: str = token_response.get("id_token", "")
        if not id_token:
            raise AzureADError("Azure AD token response missing id_token")

        # Validate JWT
        claims = await self._validate_id_token(id_token)

        # Extract user info from claims
        email = claims.get("email") or claims.get("preferred_username", "")
        if not email or "@" not in email:
            raise AzureADError("Azure AD id_token missing valid email claim")

        display_name = claims.get("name") or email.split("@")[0]
        subject_id = claims.get("sub", "")

        # Map role from groups claim (if present)
        groups: list[str] = claims.get("groups", [])
        role = _map_azure_role(groups, self._config.role_mapping)

        # JIT provision
        from app.services.sso.saml_service import _jit_provision_user
        user = await _jit_provision_user(
            email=email.lower(),
            display_name=display_name,
            role=role,
            db=db,
        )

        # Compute session expiry from JWT exp claim
        exp_timestamp: int = claims.get("exp", 0)
        if exp_timestamp:
            expires_at = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
        else:
            expires_at = datetime.now(tz=timezone.utc) + timedelta(hours=_SESSION_MAX_HOURS)

        # Create SsoSession (SHA256 of id_token — raw token NEVER stored)
        from app.services.sso.saml_service import _create_sso_session
        session = await _create_sso_session(
            user_id=user.id,
            sso_config_id=self._config.id,
            subject_id=subject_id,
            id_token_raw=id_token,
            expires_at=expires_at,
            db=db,
        )

        logger.info(
            "azure_ad_service: callback success user=%s org=%s",
            user.id,
            self._config.organization_id,
        )
        return user, session

    # ──────────────────────────────────────────────────────────────────────────
    # Private: token exchange
    # ──────────────────────────────────────────────────────────────────────────

    async def _exchange_code_for_token(
        self,
        code: str,
        code_verifier: str,
        redirect_uri: str | None = None,
    ) -> dict[str, Any]:
        """
        Exchange authorization code + PKCE verifier for token response.

        Makes a HTTPS POST to the Azure AD token endpoint.
        No client_secret — PKCE is the proof of possession.

        Args:
            code:           Authorization code from callback query parameter.
            code_verifier:  PKCE verifier matching the code_challenge used at login.
            redirect_uri:   Absolute callback URL — must exactly match the URI used in
                            the authorization request and the Azure AD app registration.
                            If None, falls back to relative path (dev/test only).

        Returns:
            Token response dict containing id_token, access_token, refresh_token.

        Raises:
            AzureADError: If token endpoint returns an error.
        """
        import httpx

        token_url = _AZURE_TOKEN_URL_PATTERN.format(tenant_id=self._tenant_id)

        # redirect_uri must exactly match the authorization request URI and app registration.
        # Absolute URI is required by Azure AD (AADSTS50011 if relative or mismatched).
        _redirect_uri = redirect_uri or "/api/v1/enterprise/sso/azure-ad/callback"

        payload = {
            "client_id": self._client_id,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": _redirect_uri,
            "code_verifier": code_verifier,
            "scope": " ".join(self.SCOPES),
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(token_url, data=payload)

            if response.status_code != 200:
                error_data = response.json() if response.content else {}
                raise AzureADError(
                    f"Azure AD token exchange failed: "
                    f"HTTP {response.status_code} — "
                    f"{error_data.get('error_description', error_data)}"
                )

            return response.json()

        except httpx.RequestError as exc:
            raise AzureADError(
                f"Azure AD token exchange network error: {exc}"
            ) from exc

    async def _validate_id_token(self, id_token: str) -> dict[str, Any]:
        """
        Validate Azure AD id_token JWT: fetch JWKS, verify signature, check claims.

        JWKS are cached for 1 hour (Azure AD rotates signing keys weekly).

        Validates:
            - Signature via JWKS from Azure AD discovery endpoint
            - Issuer (iss): must match https://login.microsoftonline.com/{tenant_id}/v2.0
            - Audience (aud): must match client_id
            - Expiry (exp): must be in the future

        Args:
            id_token: JWT id_token string from Azure AD token response.

        Returns:
            Validated JWT claims dict.

        Raises:
            AzureADError: Signature invalid, expired, or claims mismatch.
        """
        if jwt is None or PyJWKClient is None:
            raise AzureADError(
                "PyJWT not installed. Run: pip install PyJWT[cryptography]"
            )

        jwks_url = _AZURE_JWKS_URL_PATTERN.format(tenant_id=self._tenant_id)
        expected_issuer = (
            f"https://login.microsoftonline.com/{self._tenant_id}/v2.0"
        )

        try:
            # PyJWKClient handles JWKS caching internally (fetches from URL)
            jwks_client = PyJWKClient(
                jwks_url,
                cache_keys=True,
                lifespan=_JWKS_CACHE_TTL_SECONDS,
            )
            signing_key = jwks_client.get_signing_key_from_jwt(id_token)

            claims: dict = jwt.decode(
                id_token,
                signing_key.key,
                algorithms=["RS256"],
                audience=self._client_id,
                issuer=expected_issuer,
                options={
                    "verify_exp": True,
                    "verify_iss": True,
                    "verify_aud": True,
                    "require": ["sub", "exp", "iss", "aud"],
                },
            )
            return claims

        except PyJWTError as exc:
            raise AzureADError(f"Azure AD id_token validation failed: {exc}") from exc
        except Exception as exc:
            raise AzureADError(
                f"Azure AD JWKS fetch or token validation error: {exc}"
            ) from exc

    def _build_auth_url(
        self,
        code_challenge: str,
        state: str,
        redirect_uri: str | None = None,
    ) -> str:
        """
        Build Azure AD authorization URL with PKCE S256 and CSRF state.

        Args:
            code_challenge: PKCE S256 code challenge (base64url-encoded SHA256 of verifier).
            state:          CSRF state token (32-byte URL-safe base64).
            redirect_uri:   Absolute callback URL registered in Azure AD app.
                            Must be absolute (e.g. "https://host/api/v1/.../azure-ad/callback").
                            Azure AD rejects relative URIs (AADSTS50011: redirect_uri mismatch).
                            If None, falls back to relative path (dev/test only).

        Returns:
            Full authorization URL for browser redirect.
        """
        from urllib.parse import urlencode

        # Absolute URI required by Azure AD — relative path causes AADSTS50011.
        _redirect_uri = redirect_uri or "/api/v1/enterprise/sso/azure-ad/callback"

        params = {
            "client_id": self._client_id,
            "response_type": "code",
            "redirect_uri": _redirect_uri,
            "scope": " ".join(self.SCOPES),
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
            "response_mode": "query",
        }
        base_url = _AZURE_AUTH_URL_PATTERN.format(tenant_id=self._tenant_id)
        return f"{base_url}?{urlencode(params)}"


# ──────────────────────────────────────────────────────────────────────────────
# Private helper
# ──────────────────────────────────────────────────────────────────────────────

def _map_azure_role(groups: list[str], role_mapping: dict) -> str:
    """
    Map Azure AD groups to Orchestrator role via role_mapping JSONB.

    Args:
        groups:       List of Azure AD group object IDs from JWT groups claim.
        role_mapping: role_mapping JSONB from EnterpriseSsoConfig.

    Returns:
        Orchestrator role string.
    """
    default_role = role_mapping.get("default_role", "developer")
    group_mappings: dict = role_mapping.get("group_mappings", {})

    for group in groups:
        if group in group_mappings:
            return group_mappings[group]

    return default_role
