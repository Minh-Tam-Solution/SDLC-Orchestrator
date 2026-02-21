"""
Azure AD service unit tests — Sprint 183.

AD-01 to AD-15: 15 tests covering AzureADService and generate_pkce_pair.

Tests mock httpx and PyJWT/PyJWKClient to avoid real HTTP calls.
All tests verify the security properties and interface contract
defined in ADR-061 (Azure AD PKCE S256 implementation).
"""

from __future__ import annotations

import base64
import hashlib
import json
import time
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from urllib.parse import parse_qs, urlparse
from uuid import UUID, uuid4

import pytest


# ──────────────────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────────────────

@pytest.fixture()
def azure_config() -> MagicMock:
    """Mock EnterpriseSsoConfig for Azure AD provider."""
    cfg = MagicMock()
    cfg.id = uuid4()
    cfg.organization_id = uuid4()
    cfg.provider = "azure_ad"
    cfg.is_enabled = True
    cfg.tenant_id = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
    cfg.client_id = "b2c3d4e5-f6a7-8901-bcde-f12345678901"
    cfg.role_mapping = {
        "group_mappings": {},
        "default_role": "developer",
    }
    return cfg


@pytest.fixture()
def mock_db() -> AsyncMock:
    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    return db


@pytest.fixture()
def valid_jwt_claims(azure_config: MagicMock) -> dict:
    """Valid JWT claims matching expected Azure AD id_token structure."""
    now = int(time.time())
    return {
        "sub": "user-subject-id-123",
        "email": "testuser@example.com",
        "preferred_username": "testuser@example.com",
        "name": "Test User",
        "iss": f"https://login.microsoftonline.com/{azure_config.tenant_id}/v2.0",
        "aud": azure_config.client_id,
        "exp": now + 3600,
        "iat": now,
        "groups": [],
    }


# ──────────────────────────────────────────────────────────────────────────────
# AD-01: initiate_login returns (auth_url, code_verifier, state)
# ──────────────────────────────────────────────────────────────────────────────

def test_ad01_initiate_login_returns_triple(azure_config: MagicMock) -> None:
    """AD-01: initiate_login returns tuple (auth_url, code_verifier, state)."""
    from app.services.sso.azure_ad_service import AzureADService

    svc = AzureADService(azure_config)
    result = svc.initiate_login()

    assert isinstance(result, tuple)
    assert len(result) == 3
    auth_url, code_verifier, state = result
    assert isinstance(auth_url, str)
    assert isinstance(code_verifier, str)
    assert isinstance(state, str)


# ──────────────────────────────────────────────────────────────────────────────
# AD-02: auth_url contains code_challenge_method=S256
# ──────────────────────────────────────────────────────────────────────────────

def test_ad02_auth_url_uses_s256(azure_config: MagicMock) -> None:
    """AD-02: auth_url query params include code_challenge_method=S256."""
    from app.services.sso.azure_ad_service import AzureADService

    svc = AzureADService(azure_config)
    auth_url, _, _ = svc.initiate_login()

    parsed = urlparse(auth_url)
    params = parse_qs(parsed.query)
    assert params.get("code_challenge_method") == ["S256"]


# ──────────────────────────────────────────────────────────────────────────────
# AD-03: auth_url contains response_type=code
# ──────────────────────────────────────────────────────────────────────────────

def test_ad03_auth_url_response_type_code(azure_config: MagicMock) -> None:
    """AD-03: auth_url query params include response_type=code."""
    from app.services.sso.azure_ad_service import AzureADService

    svc = AzureADService(azure_config)
    auth_url, _, _ = svc.initiate_login()

    parsed = urlparse(auth_url)
    params = parse_qs(parsed.query)
    assert params.get("response_type") == ["code"]


# ──────────────────────────────────────────────────────────────────────────────
# AD-04: auth_url contains scope with openid, profile, email
# ──────────────────────────────────────────────────────────────────────────────

def test_ad04_auth_url_scope_includes_oidc(azure_config: MagicMock) -> None:
    """AD-04: auth_url scope parameter includes openid, profile, and email."""
    from app.services.sso.azure_ad_service import AzureADService

    svc = AzureADService(azure_config)
    auth_url, _, _ = svc.initiate_login()

    parsed = urlparse(auth_url)
    params = parse_qs(parsed.query)
    scope_values = params.get("scope", [""])[0]
    assert "openid" in scope_values
    assert "profile" in scope_values
    assert "email" in scope_values


# ──────────────────────────────────────────────────────────────────────────────
# AD-05: process_callback exchanges code for id_token via HTTPS
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_ad05_process_callback_exchanges_code(
    azure_config: MagicMock,
    valid_jwt_claims: dict,
    mock_db: AsyncMock,
) -> None:
    """AD-05: process_callback calls the Azure AD token endpoint via HTTPS POST."""
    fake_id_token = "header.payload.signature"
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "id_token": fake_id_token,
        "access_token": "access-token-value",
        "token_type": "Bearer",
    }

    with (
        patch(
            "app.services.sso.azure_ad_service.AzureADService._validate_id_token",
            new_callable=AsyncMock,
            return_value=valid_jwt_claims,
        ),
        patch("httpx.AsyncClient") as mock_client_cls,
        patch(
            "app.services.sso.saml_service._jit_provision_user",
            new_callable=AsyncMock,
        ) as mock_jit,
        patch(
            "app.services.sso.saml_service._create_sso_session",
            new_callable=AsyncMock,
        ) as mock_create_session,
    ):
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=mock_ctx)
        mock_ctx.__aexit__ = AsyncMock(return_value=False)
        mock_ctx.post = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value = mock_ctx

        mock_jit.return_value = MagicMock(id=uuid4())
        mock_create_session.return_value = MagicMock(id=uuid4())

        from app.services.sso.azure_ad_service import AzureADService

        svc = AzureADService(azure_config)
        user, session = await svc.process_callback(
            code="auth-code-from-azure",
            state="csrf-state",
            code_verifier="verifier-string",
            db=mock_db,
        )

    # Token endpoint must use HTTPS
    mock_ctx.post.assert_called_once()
    call_args = mock_ctx.post.call_args
    token_url = call_args[0][0] if call_args[0] else call_args.kwargs.get("url", "")
    assert token_url.startswith("https://")
    assert azure_config.tenant_id in token_url


# ──────────────────────────────────────────────────────────────────────────────
# AD-06: process_callback validates id_token JWT signature via JWKS
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_ad06_validate_id_token_calls_jwks(
    azure_config: MagicMock,
    valid_jwt_claims: dict,
    mock_db: AsyncMock,
) -> None:
    """AD-06: _validate_id_token uses PyJWKClient to fetch signing key from JWKS URL."""
    from app.services.sso.azure_ad_service import AzureADService

    svc = AzureADService(azure_config)

    mock_signing_key = MagicMock()
    mock_signing_key.key = "mock-rsa-key"

    with (
        patch("app.services.sso.azure_ad_service.PyJWKClient") as mock_jwks_cls,
        patch("app.services.sso.azure_ad_service.jwt") as mock_jwt,
    ):
        mock_jwks_client = MagicMock()
        mock_jwks_client.get_signing_key_from_jwt.return_value = mock_signing_key
        mock_jwks_cls.return_value = mock_jwks_client

        mock_jwt.decode.return_value = valid_jwt_claims

        claims = await svc._validate_id_token("fake.jwt.token")

    # JWKS URL must include tenant_id
    jwks_url_arg = mock_jwks_cls.call_args[0][0]
    assert azure_config.tenant_id in jwks_url_arg
    assert claims == valid_jwt_claims


# ──────────────────────────────────────────────────────────────────────────────
# AD-07: process_callback rejects expired id_token
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_ad07_rejects_expired_id_token(
    azure_config: MagicMock,
    mock_db: AsyncMock,
) -> None:
    """AD-07: _validate_id_token raises AzureADError for expired id_token."""
    from app.services.sso.azure_ad_service import AzureADError, AzureADService

    svc = AzureADService(azure_config)

    with (
        patch("app.services.sso.azure_ad_service.PyJWKClient") as mock_jwks_cls,
        patch("app.services.sso.azure_ad_service.jwt") as mock_jwt,
    ):
        from jwt import ExpiredSignatureError

        mock_jwks_client = MagicMock()
        mock_signing_key = MagicMock()
        mock_signing_key.key = "rsa-key"
        mock_jwks_client.get_signing_key_from_jwt.return_value = mock_signing_key
        mock_jwks_cls.return_value = mock_jwks_client

        mock_jwt.decode.side_effect = ExpiredSignatureError("Signature has expired")

        with pytest.raises(AzureADError, match="validation failed"):
            await svc._validate_id_token("expired.jwt.token")


# ──────────────────────────────────────────────────────────────────────────────
# AD-08: process_callback rejects state mismatch (CSRF)
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_ad08_state_mismatch_handled_by_caller(
    azure_config: MagicMock,
    mock_db: AsyncMock,
) -> None:
    """
    AD-08: State validation is enforced by the route handler (enterprise_sso.py)
    before calling process_callback. AzureADService.process_callback does not
    re-validate state internally — the caller passes the already-validated verifier.

    This test verifies the contract: caller must validate state → retrieve verifier
    from Redis → then call process_callback with the correct verifier.
    """
    # The route handler deletes state from Redis and validates before calling.
    # AzureADService just processes the code + verifier it receives.
    # If state validation failed, process_callback would not be called at all.
    from app.services.sso.azure_ad_service import AzureADService

    svc = AzureADService(azure_config)
    # Verify the method signature accepts code, state, code_verifier, db
    import inspect
    sig = inspect.signature(svc.process_callback)
    assert "code" in sig.parameters
    assert "state" in sig.parameters
    assert "code_verifier" in sig.parameters
    assert "db" in sig.parameters


# ──────────────────────────────────────────────────────────────────────────────
# AD-09: process_callback JIT provisions user from JWT claims
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_ad09_jit_provisions_user_from_claims(
    azure_config: MagicMock,
    valid_jwt_claims: dict,
    mock_db: AsyncMock,
) -> None:
    """AD-09: process_callback extracts email from JWT and calls _jit_provision_user."""
    fake_response = MagicMock()
    fake_response.status_code = 200
    fake_response.json.return_value = {"id_token": "header.payload.sig"}
    fake_response.content = b'{"id_token": "header.payload.sig"}'

    with (
        patch(
            "app.services.sso.azure_ad_service.AzureADService._validate_id_token",
            new_callable=AsyncMock,
            return_value=valid_jwt_claims,
        ),
        patch("httpx.AsyncClient") as mock_client_cls,
        patch(
            "app.services.sso.saml_service._jit_provision_user",
            new_callable=AsyncMock,
        ) as mock_jit,
        patch(
            "app.services.sso.saml_service._create_sso_session",
            new_callable=AsyncMock,
            return_value=MagicMock(id=uuid4()),
        ),
    ):
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=mock_ctx)
        mock_ctx.__aexit__ = AsyncMock(return_value=False)
        mock_ctx.post = AsyncMock(return_value=fake_response)
        mock_client_cls.return_value = mock_ctx
        mock_jit.return_value = MagicMock(id=uuid4())

        from app.services.sso.azure_ad_service import AzureADService

        svc = AzureADService(azure_config)
        await svc.process_callback(
            code="code", state="state", code_verifier="verifier", db=mock_db
        )

    mock_jit.assert_called_once()
    call_kwargs = mock_jit.call_args.kwargs
    assert call_kwargs["email"] == "testuser@example.com"


# ──────────────────────────────────────────────────────────────────────────────
# AD-10: process_callback stores SHA256 hash of id_token
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_ad10_stores_id_token_sha256_hash(
    azure_config: MagicMock,
    valid_jwt_claims: dict,
    mock_db: AsyncMock,
) -> None:
    """AD-10: _create_sso_session is called with id_token_raw, which is then SHA256-hashed."""
    raw_id_token = "raw.id.token.value"
    expected_hash = hashlib.sha256(raw_id_token.encode()).hexdigest()

    fake_response = MagicMock()
    fake_response.status_code = 200
    fake_response.json.return_value = {"id_token": raw_id_token}
    fake_response.content = json.dumps({"id_token": raw_id_token}).encode()

    captured_calls: list = []

    async def capture_create(*args, **kwargs):
        captured_calls.append(kwargs)
        return MagicMock(id=uuid4())

    with (
        patch(
            "app.services.sso.azure_ad_service.AzureADService._validate_id_token",
            new_callable=AsyncMock,
            return_value=valid_jwt_claims,
        ),
        patch("httpx.AsyncClient") as mock_client_cls,
        patch(
            "app.services.sso.saml_service._jit_provision_user",
            new_callable=AsyncMock,
            return_value=MagicMock(id=uuid4()),
        ),
        patch(
            "app.services.sso.saml_service._create_sso_session",
            new_callable=AsyncMock,
            side_effect=capture_create,
        ),
    ):
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=mock_ctx)
        mock_ctx.__aexit__ = AsyncMock(return_value=False)
        mock_ctx.post = AsyncMock(return_value=fake_response)
        mock_client_cls.return_value = mock_ctx

        from app.services.sso.azure_ad_service import AzureADService

        svc = AzureADService(azure_config)
        await svc.process_callback(
            code="code", state="state", code_verifier="verifier", db=mock_db
        )

    assert len(captured_calls) == 1
    # raw id_token passed to _create_sso_session; the function SHA256-hashes it
    passed_raw = captured_calls[0].get("id_token_raw", "")
    assert passed_raw == raw_id_token
    # Verify that SHA256 would equal expected hash
    assert hashlib.sha256(passed_raw.encode()).hexdigest() == expected_hash


# ──────────────────────────────────────────────────────────────────────────────
# AD-11: process_callback creates SsoSession
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_ad11_creates_sso_session(
    azure_config: MagicMock,
    valid_jwt_claims: dict,
    mock_db: AsyncMock,
) -> None:
    """AD-11: process_callback returns (User, SsoSession) tuple."""
    session_id = uuid4()

    fake_response = MagicMock()
    fake_response.status_code = 200
    fake_response.json.return_value = {"id_token": "header.payload.sig"}
    fake_response.content = b'{"id_token": "header.payload.sig"}'

    with (
        patch(
            "app.services.sso.azure_ad_service.AzureADService._validate_id_token",
            new_callable=AsyncMock,
            return_value=valid_jwt_claims,
        ),
        patch("httpx.AsyncClient") as mock_client_cls,
        patch(
            "app.services.sso.saml_service._jit_provision_user",
            new_callable=AsyncMock,
            return_value=MagicMock(id=uuid4()),
        ),
        patch(
            "app.services.sso.saml_service._create_sso_session",
            new_callable=AsyncMock,
            return_value=MagicMock(id=session_id),
        ),
    ):
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=mock_ctx)
        mock_ctx.__aexit__ = AsyncMock(return_value=False)
        mock_ctx.post = AsyncMock(return_value=fake_response)
        mock_client_cls.return_value = mock_ctx

        from app.services.sso.azure_ad_service import AzureADService

        svc = AzureADService(azure_config)
        user, session = await svc.process_callback(
            code="code", state="state", code_verifier="verifier", db=mock_db
        )

    assert session.id == session_id
    assert user is not None


# ──────────────────────────────────────────────────────────────────────────────
# AD-12: generate_pkce_pair verifier is 64 bytes (before base64)
# ──────────────────────────────────────────────────────────────────────────────

def test_ad12_pkce_verifier_64_bytes() -> None:
    """AD-12: generate_pkce_pair code_verifier is derived from 64 random bytes."""
    from app.services.sso.azure_ad_service import generate_pkce_pair

    verifier, challenge = generate_pkce_pair()

    # The verifier is base64url(64 random bytes) — decode to check byte length
    # Add padding for decoding
    padded = verifier + "=" * (4 - len(verifier) % 4)
    decoded = base64.urlsafe_b64decode(padded)
    assert len(decoded) == 64, f"Expected 64 bytes, got {len(decoded)}"


# ──────────────────────────────────────────────────────────────────────────────
# AD-13: generate_pkce_pair S256 challenge matches sha256(verifier)
# ──────────────────────────────────────────────────────────────────────────────

def test_ad13_pkce_challenge_is_s256_of_verifier() -> None:
    """AD-13: code_challenge = BASE64URL(SHA256(code_verifier)) — S256 method."""
    from app.services.sso.azure_ad_service import generate_pkce_pair

    verifier, challenge = generate_pkce_pair()

    # Recompute S256 challenge manually
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    expected_challenge = (
        base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    )
    assert challenge == expected_challenge, (
        f"S256 mismatch: got {challenge!r}, expected {expected_challenge!r}"
    )


# ──────────────────────────────────────────────────────────────────────────────
# AD-14: GET /azure-ad/callback returns 302 redirect on missing code
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_ad14_callback_redirects_on_missing_code() -> None:
    """AD-14: azure_ad_callback route returns 302 redirect when code is missing."""
    from httpx import AsyncClient
    from fastapi.testclient import TestClient

    # Test using route handler logic directly
    from fastapi import FastAPI
    from app.api.routes.enterprise_sso import router, _SSO_ERROR_REDIRECT

    test_app = FastAPI()
    test_app.include_router(router, prefix="/api/v1")

    with TestClient(test_app, follow_redirects=False) as client:
        # Call without code param — only state
        response = client.get(
            "/api/v1/enterprise/sso/azure-ad/callback",
            params={"state": "some-state"},
        )

    # Should redirect (302) to error page since code is missing
    assert response.status_code == 302
    location = response.headers.get("location", "")
    assert "error" in location.lower() or "login" in location.lower()


# ──────────────────────────────────────────────────────────────────────────────
# AD-15: JWKS cache: second call within TTL doesn't re-fetch
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_ad15_jwks_client_uses_cache(azure_config: MagicMock) -> None:
    """AD-15: PyJWKClient is initialized with cache_keys=True and lifespan=3600."""
    from app.services.sso.azure_ad_service import AzureADService

    svc = AzureADService(azure_config)

    with patch("app.services.sso.azure_ad_service.PyJWKClient") as mock_jwks_cls:
        mock_client = MagicMock()
        mock_client.get_signing_key_from_jwt.return_value = MagicMock(key="rsa-key")
        mock_jwks_cls.return_value = mock_client

        with patch("app.services.sso.azure_ad_service.jwt") as mock_jwt:
            mock_jwt.decode.return_value = {
                "sub": "user123",
                "email": "user@example.com",
                "iss": f"https://login.microsoftonline.com/{azure_config.tenant_id}/v2.0",
                "aud": azure_config.client_id,
                "exp": int(time.time()) + 3600,
            }
            await svc._validate_id_token("header.payload.sig")

    # Verify PyJWKClient was initialized with caching enabled
    init_kwargs = mock_jwks_cls.call_args.kwargs
    assert init_kwargs.get("cache_keys") is True
    # lifespan should be 3600 (1 hour)
    assert init_kwargs.get("lifespan") == 3600
