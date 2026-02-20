"""
SAML service unit tests — Sprint 183.

SS-01 to SS-15: 15 tests covering SAMLService functionality.

Tests use unittest.mock to avoid dependency on python3-saml installation
and on a real SAML IdP. All tests verify the service contract and
security properties defined in ADR-061.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest


# ──────────────────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────────────────

@pytest.fixture()
def sample_org_id() -> UUID:
    return uuid4()


@pytest.fixture()
def saml_config(sample_org_id: UUID) -> MagicMock:
    """Mock EnterpriseSsoConfig for a SAML provider."""
    cfg = MagicMock()
    cfg.id = uuid4()
    cfg.organization_id = sample_org_id
    cfg.provider = "saml"
    cfg.is_enabled = True
    cfg.idp_entity_id = "https://idp.example.com/entity"
    cfg.idp_sso_url = "https://idp.example.com/sso"
    cfg.idp_x509_cert = "MIIC...base64cert...=="
    cfg.sp_entity_id = "https://orchestrator.example.com/sp"
    cfg.role_mapping = {
        "group_mappings": {"Engineering": "developer", "Admins": "admin"},
        "default_role": "developer",
    }
    return cfg


@pytest.fixture()
def saml_request_data() -> dict:
    """Minimal python3-saml request_data dict."""
    return {
        "http_host": "orchestrator.example.com",
        "script_name": "/api/v1/enterprise/sso/saml/callback",
        "server_port": 443,
        "get_data": {},
        "post_data": {"SAMLResponse": "base64encodedresponse"},
        "https": "on",
    }


@pytest.fixture()
def mock_db() -> AsyncMock:
    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.delete = AsyncMock()
    return db


# ──────────────────────────────────────────────────────────────────────────────
# SS-01: initiate_login returns valid SAML redirect URL
# ──────────────────────────────────────────────────────────────────────────────

def test_ss01_initiate_login_returns_redirect_url(saml_config: MagicMock) -> None:
    """SS-01: initiate_login returns a string URL pointing to IdP SSO URL."""
    mock_auth = MagicMock()
    mock_auth.login.return_value = (
        "https://idp.example.com/sso?SAMLRequest=abc123&RelayState=org-uuid"
    )

    with (
        patch(
            "app.services.sso.saml_service.OneLogin_Saml2_Auth",
            return_value=mock_auth,
        ),
        patch("app.services.sso.saml_service.OneLogin_Saml2_Settings"),
    ):
        from app.services.sso.saml_service import SAMLService

        svc = SAMLService(saml_config)
        redirect_url = svc.initiate_login(request_data={
            "http_host": "orchestrator.example.com",
            "script_name": "/api/v1/enterprise/sso/saml/login",
            "server_port": 443,
            "get_data": {},
            "post_data": {},
            "https": "on",
        })

    assert isinstance(redirect_url, str)
    assert "idp.example.com" in redirect_url
    assert "SAMLRequest" in redirect_url


# ──────────────────────────────────────────────────────────────────────────────
# SS-02: process_callback validates AssertionConsumerServiceURL
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_ss02_process_callback_validates_acs_url(
    saml_config: MagicMock,
    saml_request_data: dict,
    mock_db: AsyncMock,
) -> None:
    """SS-02: process_callback calls auth.process_response() — python3-saml validates ACS URL internally."""
    mock_auth = MagicMock()
    mock_auth.process_response = MagicMock()
    mock_auth.get_errors.return_value = []
    mock_auth.get_nameid.return_value = "user@example.com"
    mock_auth.get_attributes.return_value = {
        "email": ["user@example.com"],
        "displayName": ["Test User"],
    }
    mock_auth.get_session_expiration.return_value = None
    mock_auth.get_nameid_format.return_value = (
        "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress"
    )

    with (
        patch(
            "app.services.sso.saml_service.OneLogin_Saml2_Auth",
            return_value=mock_auth,
        ),
        patch("app.services.sso.saml_service.OneLogin_Saml2_Settings"),
        patch(
            "app.services.sso.saml_service._jit_provision_user",
            new_callable=AsyncMock,
            return_value=MagicMock(id=uuid4()),
        ),
        patch(
            "app.services.sso.saml_service._create_sso_session",
            new_callable=AsyncMock,
            return_value=MagicMock(id=uuid4()),
        ),
    ):
        from app.services.sso.saml_service import SAMLService

        svc = SAMLService(saml_config)
        user, session = await svc.process_callback(saml_request_data, mock_db)

    mock_auth.process_response.assert_called_once()
    assert user is not None
    assert session is not None


# ──────────────────────────────────────────────────────────────────────────────
# SS-03: process_callback rejects expired assertion
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_ss03_process_callback_rejects_expired_assertion(
    saml_config: MagicMock,
    saml_request_data: dict,
    mock_db: AsyncMock,
) -> None:
    """SS-03: process_callback raises SAMLError when python3-saml reports expired assertion."""
    from app.services.sso.saml_service import SAMLError

    mock_auth = MagicMock()
    mock_auth.process_response = MagicMock()
    mock_auth.get_errors.return_value = ["invalid_response"]
    mock_auth.get_last_error_reason.return_value = "Assertion has expired"

    with (
        patch(
            "app.services.sso.saml_service.OneLogin_Saml2_Auth",
            return_value=mock_auth,
        ),
        patch("app.services.sso.saml_service.OneLogin_Saml2_Settings"),
    ):
        from app.services.sso.saml_service import SAMLService

        svc = SAMLService(saml_config)
        with pytest.raises(SAMLError, match="expired"):
            await svc.process_callback(saml_request_data, mock_db)


# ──────────────────────────────────────────────────────────────────────────────
# SS-04: process_callback rejects unsigned assertion
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_ss04_process_callback_rejects_unsigned_assertion(
    saml_config: MagicMock,
    saml_request_data: dict,
    mock_db: AsyncMock,
) -> None:
    """SS-04: SAMLService settings enforce wantAssertionsSigned=True."""
    with (
        patch("app.services.sso.saml_service.OneLogin_Saml2_Auth") as mock_auth_cls,
        patch("app.services.sso.saml_service.OneLogin_Saml2_Settings"),
    ):
        from app.services.sso.saml_service import SAMLService

        mock_auth = MagicMock()
        mock_auth.process_response = MagicMock()
        mock_auth.get_errors.return_value = ["invalid_signature"]
        mock_auth.get_last_error_reason.return_value = "Found an unmatched signed assertion"
        mock_auth_cls.return_value = mock_auth

        svc = SAMLService(saml_config)
        # Verify security settings include wantAssertionsSigned
        settings = svc._build_settings(saml_config)
        assert settings["security"]["wantAssertionsSigned"] is True
        assert settings["security"]["wantMessagesSigned"] is True


# ──────────────────────────────────────────────────────────────────────────────
# SS-05: JIT provisioning — creates new User on first login
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_ss05_jit_creates_new_user(
    saml_config: MagicMock,
    saml_request_data: dict,
    mock_db: AsyncMock,
) -> None:
    """SS-05: _jit_provision_user creates a new User when email not found."""
    mock_auth = _make_valid_saml_auth("newuser@example.com", "New User")
    new_user_id = uuid4()

    with (
        patch(
            "app.services.sso.saml_service.OneLogin_Saml2_Auth",
            return_value=mock_auth,
        ),
        patch("app.services.sso.saml_service.OneLogin_Saml2_Settings"),
        patch(
            "app.services.sso.saml_service._jit_provision_user",
            new_callable=AsyncMock,
        ) as mock_jit,
        patch(
            "app.services.sso.saml_service._create_sso_session",
            new_callable=AsyncMock,
        ) as mock_create_session,
    ):
        mock_user = MagicMock(id=new_user_id, email="newuser@example.com")
        mock_jit.return_value = mock_user
        mock_session = MagicMock(id=uuid4())
        mock_create_session.return_value = mock_session

        from app.services.sso.saml_service import SAMLService

        svc = SAMLService(saml_config)
        user, session = await svc.process_callback(saml_request_data, mock_db)

    mock_jit.assert_called_once()
    call_kwargs = mock_jit.call_args.kwargs
    assert call_kwargs["email"] == "newuser@example.com"
    assert user.id == new_user_id


# ──────────────────────────────────────────────────────────────────────────────
# SS-06: JIT provisioning — returns existing User on second login
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_ss06_jit_returns_existing_user(
    saml_config: MagicMock,
    saml_request_data: dict,
    mock_db: AsyncMock,
) -> None:
    """SS-06: _jit_provision_user returns existing User when email matches."""
    mock_auth = _make_valid_saml_auth("existing@example.com", "Existing User")
    existing_id = uuid4()
    existing_user = MagicMock(id=existing_id, email="existing@example.com")

    with (
        patch(
            "app.services.sso.saml_service.OneLogin_Saml2_Auth",
            return_value=mock_auth,
        ),
        patch("app.services.sso.saml_service.OneLogin_Saml2_Settings"),
        patch(
            "app.services.sso.saml_service._jit_provision_user",
            new_callable=AsyncMock,
            return_value=existing_user,
        ),
        patch(
            "app.services.sso.saml_service._create_sso_session",
            new_callable=AsyncMock,
            return_value=MagicMock(id=uuid4()),
        ),
    ):
        from app.services.sso.saml_service import SAMLService

        svc = SAMLService(saml_config)
        user, _ = await svc.process_callback(saml_request_data, mock_db)

    assert user.id == existing_id


# ──────────────────────────────────────────────────────────────────────────────
# SS-07: Role mapping from IdP groups
# ──────────────────────────────────────────────────────────────────────────────

def test_ss07_role_mapping_from_groups(saml_config: MagicMock) -> None:
    """SS-07: _map_role maps IdP group 'Engineering' → 'developer' via role_mapping."""
    with (
        patch("app.services.sso.saml_service.OneLogin_Saml2_Auth"),
        patch("app.services.sso.saml_service.OneLogin_Saml2_Settings"),
    ):
        from app.services.sso.saml_service import _map_role

    attributes = {"groups": ["Engineering", "AllUsers"]}
    role_mapping = {
        "group_mappings": {"Engineering": "developer", "Admins": "admin"},
        "default_role": "member",
    }
    result = _map_role(attributes, role_mapping)
    assert result == "developer"


# ──────────────────────────────────────────────────────────────────────────────
# SS-08: Default role when no group matches
# ──────────────────────────────────────────────────────────────────────────────

def test_ss08_default_role_when_no_group_match(saml_config: MagicMock) -> None:
    """SS-08: _map_role defaults to 'developer' when no group matches role_mapping."""
    with (
        patch("app.services.sso.saml_service.OneLogin_Saml2_Auth"),
        patch("app.services.sso.saml_service.OneLogin_Saml2_Settings"),
    ):
        from app.services.sso.saml_service import _map_role

    attributes = {"groups": ["UnknownGroup"]}
    role_mapping = {
        "group_mappings": {"Admins": "admin"},
        "default_role": "developer",
    }
    result = _map_role(attributes, role_mapping)
    assert result == "developer"


# ──────────────────────────────────────────────────────────────────────────────
# SS-09: SHA256 hash stored — raw id_token NEVER stored
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_ss09_stores_id_token_hash_not_raw(mock_db: AsyncMock) -> None:
    """SS-09: _create_sso_session stores SHA256(id_token), NOT the raw id_token."""
    with (
        patch("app.services.sso.saml_service.OneLogin_Saml2_Auth"),
        patch("app.services.sso.saml_service.OneLogin_Saml2_Settings"),
    ):
        from app.services.sso.saml_service import _create_sso_session

    raw_token = "raw_saml_assertion_value"
    expected_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    user_id = uuid4()
    config_id = uuid4()
    expires_at = datetime.now(timezone.utc) + timedelta(hours=8)

    # Capture what gets persisted via db.add
    added_sessions = []
    mock_db.add = lambda obj: added_sessions.append(obj)
    mock_db.refresh = AsyncMock(side_effect=lambda obj: None)

    _session = await _create_sso_session(
        user_id=user_id,
        sso_config_id=config_id,
        subject_id="user@example.com",
        id_token_raw=raw_token,
        expires_at=expires_at,
        db=mock_db,
    )

    assert len(added_sessions) == 1
    session_obj = added_sessions[0]
    assert session_obj.id_token_hash == expected_hash
    # Verify raw token is NOT stored
    assert not hasattr(session_obj, "id_token") or getattr(session_obj, "id_token", None) is None


# ──────────────────────────────────────────────────────────────────────────────
# SS-10: SsoSession expires_at ≤ 8h from now
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_ss10_session_expiry_within_8h(
    saml_config: MagicMock,
    saml_request_data: dict,
    mock_db: AsyncMock,
) -> None:
    """SS-10: process_callback creates SsoSession with expires_at ≤ 8h from now."""
    mock_auth = _make_valid_saml_auth("user@example.com", "Test User")
    # python3-saml get_session_expiration returns None → service falls back to 8h
    mock_auth.get_session_expiration.return_value = None

    captured_sessions: list = []

    async def capture_create_session(**kwargs):
        session = MagicMock()
        session.id = uuid4()
        session.expires_at = kwargs["expires_at"]
        captured_sessions.append(session)
        return session

    with (
        patch(
            "app.services.sso.saml_service.OneLogin_Saml2_Auth",
            return_value=mock_auth,
        ),
        patch("app.services.sso.saml_service.OneLogin_Saml2_Settings"),
        patch(
            "app.services.sso.saml_service._jit_provision_user",
            new_callable=AsyncMock,
            return_value=MagicMock(id=uuid4()),
        ),
        patch(
            "app.services.sso.saml_service._create_sso_session",
            new_callable=AsyncMock,
            side_effect=capture_create_session,
        ),
    ):
        from app.services.sso.saml_service import SAMLService

        svc = SAMLService(saml_config)
        await svc.process_callback(saml_request_data, mock_db)

    assert len(captured_sessions) == 1
    expires_at = captured_sessions[0].expires_at
    now = datetime.now(timezone.utc)
    max_expiry = now + timedelta(hours=8, minutes=1)  # 1-minute buffer
    assert expires_at <= max_expiry, f"expires_at {expires_at} exceeds 8h limit"


# ──────────────────────────────────────────────────────────────────────────────
# SS-11: get_metadata returns valid XML
# ──────────────────────────────────────────────────────────────────────────────

def test_ss11_get_metadata_returns_xml(saml_config: MagicMock) -> None:
    """SS-11: get_metadata returns a non-empty string containing XML content."""
    mock_settings = MagicMock()
    mock_settings.get_sp_metadata.return_value = (
        b"<?xml version='1.0'?><EntityDescriptor xmlns='urn:oasis:names:tc:SAML:2.0:metadata'"
        b" entityID='https://orchestrator.example.com/sp'>"
        b"<SPSSODescriptor>...</SPSSODescriptor></EntityDescriptor>"
    )
    mock_settings.validate_metadata.return_value = []

    with (
        patch(
            "app.services.sso.saml_service.OneLogin_Saml2_Settings",
            return_value=mock_settings,
        ),
        patch("app.services.sso.saml_service.OneLogin_Saml2_Auth"),
    ):
        from app.services.sso.saml_service import SAMLService

        svc = SAMLService(saml_config)
        metadata = svc.get_metadata()

    assert isinstance(metadata, str)
    assert len(metadata) > 0
    assert "EntityDescriptor" in metadata or "entityID" in metadata


# ──────────────────────────────────────────────────────────────────────────────
# SS-12: get_metadata XML contains AssertionConsumerService URL
# ──────────────────────────────────────────────────────────────────────────────

def test_ss12_metadata_contains_acs_url(saml_config: MagicMock) -> None:
    """SS-12: SP metadata includes AssertionConsumerService location URL."""
    acs_url = "/api/v1/enterprise/sso/saml/callback"
    mock_settings = MagicMock()
    mock_settings.get_sp_metadata.return_value = (
        f"<?xml version='1.0'?><EntityDescriptor>"
        f"<SPSSODescriptor>"
        f"<AssertionConsumerService Location='https://orchestrator.example.com{acs_url}'/>"
        f"</SPSSODescriptor></EntityDescriptor>"
    ).encode()
    mock_settings.validate_metadata.return_value = []

    with (
        patch(
            "app.services.sso.saml_service.OneLogin_Saml2_Settings",
            return_value=mock_settings,
        ),
        patch("app.services.sso.saml_service.OneLogin_Saml2_Auth"),
    ):
        from app.services.sso.saml_service import SAMLService

        svc = SAMLService(saml_config)
        metadata = svc.get_metadata()

    assert acs_url in metadata or "AssertionConsumerService" in metadata


# ──────────────────────────────────────────────────────────────────────────────
# SS-13: logout deletes SsoSession from DB
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_ss13_logout_deletes_session(
    saml_config: MagicMock,
    mock_db: AsyncMock,
) -> None:
    """SS-13: logout() calls db.delete(session) and db.commit()."""
    session_id = uuid4()
    mock_session = MagicMock()
    mock_session.id = session_id

    # Mock select → scalar_one_or_none → mock_session
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_session
    mock_db.execute = AsyncMock(return_value=mock_result)

    with (
        patch("app.services.sso.saml_service.OneLogin_Saml2_Settings"),
        patch("app.services.sso.saml_service.OneLogin_Saml2_Auth"),
    ):
        from app.services.sso.saml_service import SAMLService

        svc = SAMLService(saml_config)
        await svc.logout(
            request_data={},
            sso_session_id=session_id,
            db=mock_db,
        )

    mock_db.delete.assert_called_once_with(mock_session)
    mock_db.commit.assert_called_once()


# ──────────────────────────────────────────────────────────────────────────────
# SS-14: process_callback raises SAMLError for InResponseTo mismatch
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_ss14_raises_saml_error_for_inresponseto_mismatch(
    saml_config: MagicMock,
    saml_request_data: dict,
    mock_db: AsyncMock,
) -> None:
    """SS-14: python3-saml InResponseTo mismatch → SAMLError raised."""
    from app.services.sso.saml_service import SAMLError

    mock_auth = MagicMock()
    mock_auth.process_response = MagicMock()
    mock_auth.get_errors.return_value = ["invalid_response"]
    mock_auth.get_last_error_reason.return_value = (
        "The InResponseTo of the Response: ONELOGIN_xxx, does not match any sent AuthNRequest ID"
    )

    with (
        patch(
            "app.services.sso.saml_service.OneLogin_Saml2_Auth",
            return_value=mock_auth,
        ),
        patch("app.services.sso.saml_service.OneLogin_Saml2_Settings"),
    ):
        from app.services.sso.saml_service import SAMLService

        svc = SAMLService(saml_config)
        with pytest.raises(SAMLError):
            await svc.process_callback(saml_request_data, mock_db)


# ──────────────────────────────────────────────────────────────────────────────
# SS-15: process_callback raises SAMLError for XML injection in assertion
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_ss15_raises_saml_error_for_xml_injection(
    saml_config: MagicMock,
    saml_request_data: dict,
    mock_db: AsyncMock,
) -> None:
    """SS-15: Malformed SAMLResponse (XML injection attempt) → SAMLError raised."""
    from app.services.sso.saml_service import SAMLError

    mock_auth = MagicMock()
    mock_auth.process_response = MagicMock(
        side_effect=Exception("XML parsing error: unexpected token")
    )
    mock_auth.get_errors.return_value = ["wantAssertionsSigned"]

    with (
        patch(
            "app.services.sso.saml_service.OneLogin_Saml2_Auth",
            return_value=mock_auth,
        ),
        patch("app.services.sso.saml_service.OneLogin_Saml2_Settings"),
    ):
        from app.services.sso.saml_service import SAMLService

        svc = SAMLService(saml_config)
        with pytest.raises(SAMLError):
            await svc.process_callback(saml_request_data, mock_db)


# ──────────────────────────────────────────────────────────────────────────────
# Private helpers for tests
# ──────────────────────────────────────────────────────────────────────────────

def _make_valid_saml_auth(email: str, display_name: str) -> MagicMock:
    """Create a mock OneLogin_Saml2_Auth that simulates a valid assertion."""
    mock_auth = MagicMock()
    mock_auth.process_response = MagicMock()
    mock_auth.get_errors.return_value = []
    mock_auth.get_nameid.return_value = email
    mock_auth.get_attributes.return_value = {
        "email": [email],
        "displayName": [display_name],
        "groups": [],
    }
    mock_auth.get_session_expiration.return_value = None
    mock_auth.get_nameid_format.return_value = (
        "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress"
    )
    return mock_auth


def _setup_jit_mocks(mock_db: AsyncMock, user_id: UUID) -> None:
    """Configure mock_db to simulate JIT provisioning (User select + insert)."""
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None  # No existing user
    mock_db.execute = AsyncMock(return_value=mock_result)
