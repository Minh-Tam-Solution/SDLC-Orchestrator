"""
==========================================================================
Unit Tests — ConversationFirstGuard Middleware (Sprint 195 F-02 P0 Fix)
SDLC Orchestrator — Admin-Only Write Path Enforcement

Coverage targets:
    test_cfg_01_get_request_passes_through       — GET always allowed
    test_cfg_02_head_request_passes_through      — HEAD always allowed
    test_cfg_03_post_non_admin_path_passes       — POST on non-gated path OK
    test_cfg_04_superuser_passes_write_on_admin_path — superuser POST /teams OK
    test_cfg_05_platform_admin_passes_write      — platform_admin POST /admin OK
    test_cfg_06_org_admin_passes_write           — org admin POST /projects OK
    test_cfg_07_org_owner_passes_write           — org owner POST /gates OK
    test_cfg_08_regular_member_blocked_403       — member POST /teams → 403
    test_cfg_09_unauthenticated_fails_open       — no JWT → pass-through
    test_cfg_10_scope_state_admin_role           — scope state shortcut works
    test_cfg_11_scope_state_member_role_blocked  — scope state member → 403
    test_cfg_12_db_error_fails_open              — DB exception → pass-through
    test_cfg_13_disabled_env_var                 — CONVERSATION_FIRST_GUARD=false → off
    test_cfg_14_websocket_passes_through         — non-http scope ignored
    test_cfg_15_403_response_body_schema         — 403 has correct JSON body
    test_cfg_16_all_write_methods_blocked        — POST/PUT/PATCH/DELETE all blocked
    test_cfg_17_multiple_org_roles_admin_in_any  — admin in any org → pass
    test_cfg_18_user_not_found_fails_open        — user UUID not in DB → pass

Framework: pytest + pytest-asyncio
Sprint: 195 — Track A P0 Fix
==========================================================================
"""

import json
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from starlette.types import ASGIApp, Receive, Scope, Send


# ---------------------------------------------------------------------------
# Helpers — minimal ASGI test infrastructure
# ---------------------------------------------------------------------------

class _MockApp:
    """Downstream ASGI app that records whether it was called."""

    def __init__(self) -> None:
        self.called = False
        self.last_scope: Scope | None = None

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        self.called = True
        self.last_scope = scope
        await send({
            "type": "http.response.start",
            "status": 200,
            "headers": [[b"content-type", b"application/json"]],
        })
        await send({"type": "http.response.body", "body": b"{}", "more_body": False})


async def _call_middleware(
    middleware_instance,
    method: str = "POST",
    path: str = "/api/v1/teams",
    headers: list[tuple[bytes, bytes]] | None = None,
    state: dict | None = None,
) -> dict[str, Any]:
    """Invoke middleware and return {called_downstream, status, body}."""
    downstream = _MockApp()

    scope: Scope = {
        "type": "http",
        "method": method,
        "path": path,
        "headers": headers or [],
        "state": state or {},
    }

    captured: list[dict] = []

    async def mock_receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def mock_send(event: dict) -> None:
        captured.append(event)

    mw = type(middleware_instance)(downstream)
    await mw(scope, mock_receive, mock_send)

    status = 200
    body: dict = {}
    for event in captured:
        if event.get("type") == "http.response.start":
            status = event["status"]
        if event.get("type") == "http.response.body":
            raw = event.get("body", b"{}")
            try:
                body = json.loads(raw)
            except Exception:
                body = {}

    return {
        "called_downstream": downstream.called,
        "status": status,
        "body": body,
    }


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_FAKE_USER_ID = uuid4()
_FAKE_TOKEN = "eyJ.fake.token"


def _make_auth_header(token: str = _FAKE_TOKEN) -> list[tuple[bytes, bytes]]:
    return [(b"authorization", f"Bearer {token}".encode())]


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_cfg_01_get_request_passes_through():
    """CFG-01: GET requests always pass through (read-only dashboard access)."""
    from app.middleware.conversation_first_guard import ConversationFirstGuard

    mw = ConversationFirstGuard(app=_MockApp())
    result = await _call_middleware(mw, method="GET", path="/api/v1/teams")

    assert result["status"] == 200
    assert result["called_downstream"] is True


@pytest.mark.asyncio
async def test_cfg_02_head_request_passes_through():
    """CFG-02: HEAD requests always pass through."""
    from app.middleware.conversation_first_guard import ConversationFirstGuard

    mw = ConversationFirstGuard(app=_MockApp())
    result = await _call_middleware(mw, method="HEAD", path="/api/v1/admin/users")

    assert result["status"] == 200
    assert result["called_downstream"] is True


@pytest.mark.asyncio
async def test_cfg_03_post_non_admin_path_passes():
    """CFG-03: POST on a non-admin-gated path passes through for any user."""
    from app.middleware.conversation_first_guard import ConversationFirstGuard

    mw = ConversationFirstGuard(app=_MockApp())
    result = await _call_middleware(
        mw, method="POST", path="/api/v1/codegen/generate",
        headers=_make_auth_header(),
    )

    assert result["status"] == 200
    assert result["called_downstream"] is True


@pytest.mark.asyncio
async def test_cfg_04_superuser_passes_write_on_admin_path():
    """CFG-04: Superuser can POST on admin-gated paths (Sprint 195 F-02 fix)."""
    from app.middleware.conversation_first_guard import ConversationFirstGuard

    # Mock: _extract_user_id returns a valid UUID
    # Mock: DB returns is_superuser=True, is_platform_admin=False
    mock_user_result = MagicMock()
    mock_user_result.one_or_none.return_value = (True, False)  # is_superuser, is_platform_admin

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_user_result)
    mock_db.__aenter__ = AsyncMock(return_value=mock_db)
    mock_db.__aexit__ = AsyncMock(return_value=None)

    with (
        patch("app.middleware.conversation_first_guard.ConversationFirstGuard._extract_user_id",
              return_value=_FAKE_USER_ID),
        patch("app.db.session.AsyncSessionLocal", return_value=mock_db),
    ):
        mw = ConversationFirstGuard(app=_MockApp())
        result = await _call_middleware(
            mw, method="POST", path="/api/v1/teams",
            headers=_make_auth_header(),
        )

    assert result["status"] == 200
    assert result["called_downstream"] is True


@pytest.mark.asyncio
async def test_cfg_05_platform_admin_passes_write():
    """CFG-05: Platform admin can POST on admin-gated paths."""
    from app.middleware.conversation_first_guard import ConversationFirstGuard

    mock_user_result = MagicMock()
    mock_user_result.one_or_none.return_value = (False, True)  # not superuser, is platform_admin

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_user_result)
    mock_db.__aenter__ = AsyncMock(return_value=mock_db)
    mock_db.__aexit__ = AsyncMock(return_value=None)

    with (
        patch("app.middleware.conversation_first_guard.ConversationFirstGuard._extract_user_id",
              return_value=_FAKE_USER_ID),
        patch("app.db.session.AsyncSessionLocal", return_value=mock_db),
    ):
        mw = ConversationFirstGuard(app=_MockApp())
        result = await _call_middleware(
            mw, method="POST", path="/api/v1/admin/users",
            headers=_make_auth_header(),
        )

    assert result["status"] == 200
    assert result["called_downstream"] is True


@pytest.mark.asyncio
async def test_cfg_06_org_admin_passes_write():
    """CFG-06: User with 'admin' org role can POST on admin-gated paths."""
    from app.middleware.conversation_first_guard import ConversationFirstGuard

    # DB: user is not superuser/platform_admin
    mock_user_result = MagicMock()
    mock_user_result.one_or_none.return_value = (False, False)

    # DB: org role = 'admin'
    mock_org_result = MagicMock()
    mock_org_result.all.return_value = [("admin",)]

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(side_effect=[mock_user_result, mock_org_result])
    mock_db.__aenter__ = AsyncMock(return_value=mock_db)
    mock_db.__aexit__ = AsyncMock(return_value=None)

    with (
        patch("app.middleware.conversation_first_guard.ConversationFirstGuard._extract_user_id",
              return_value=_FAKE_USER_ID),
        patch("app.db.session.AsyncSessionLocal", return_value=mock_db),
    ):
        mw = ConversationFirstGuard(app=_MockApp())
        result = await _call_middleware(
            mw, method="POST", path="/api/v1/projects",
            headers=_make_auth_header(),
        )

    assert result["status"] == 200
    assert result["called_downstream"] is True


@pytest.mark.asyncio
async def test_cfg_07_org_owner_passes_write():
    """CFG-07: User with 'owner' org role can POST on admin-gated paths."""
    from app.middleware.conversation_first_guard import ConversationFirstGuard

    mock_user_result = MagicMock()
    mock_user_result.one_or_none.return_value = (False, False)

    mock_org_result = MagicMock()
    mock_org_result.all.return_value = [("owner",)]

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(side_effect=[mock_user_result, mock_org_result])
    mock_db.__aenter__ = AsyncMock(return_value=mock_db)
    mock_db.__aexit__ = AsyncMock(return_value=None)

    with (
        patch("app.middleware.conversation_first_guard.ConversationFirstGuard._extract_user_id",
              return_value=_FAKE_USER_ID),
        patch("app.db.session.AsyncSessionLocal", return_value=mock_db),
    ):
        mw = ConversationFirstGuard(app=_MockApp())
        result = await _call_middleware(
            mw, method="PUT", path="/api/v1/gates/abc123",
            headers=_make_auth_header(),
        )

    assert result["status"] == 200
    assert result["called_downstream"] is True


@pytest.mark.asyncio
async def test_cfg_08_regular_member_blocked_403():
    """CFG-08: Regular member gets 403 on write to admin-gated path (Sprint 195 P0 fix)."""
    from app.middleware.conversation_first_guard import ConversationFirstGuard

    # Not superuser, not platform_admin
    mock_user_result = MagicMock()
    mock_user_result.one_or_none.return_value = (False, False)

    # Org role = 'member' (not in ADMIN_ROLES)
    mock_org_result = MagicMock()
    mock_org_result.all.return_value = [("member",)]

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(side_effect=[mock_user_result, mock_org_result])
    mock_db.__aenter__ = AsyncMock(return_value=mock_db)
    mock_db.__aexit__ = AsyncMock(return_value=None)

    with (
        patch("app.middleware.conversation_first_guard.ConversationFirstGuard._extract_user_id",
              return_value=_FAKE_USER_ID),
        patch("app.db.session.AsyncSessionLocal", return_value=mock_db),
    ):
        mw = ConversationFirstGuard(app=_MockApp())
        result = await _call_middleware(
            mw, method="POST", path="/api/v1/teams",
            headers=_make_auth_header(),
        )

    assert result["status"] == 403
    assert result["body"]["error"] == "conversation_first_guard"
    assert "OTT" in result["body"]["detail"] or "CLI" in result["body"]["detail"]
    assert result["called_downstream"] is False


@pytest.mark.asyncio
async def test_cfg_09_unauthenticated_fails_open():
    """CFG-09: No JWT token → fail-open (pass-through, route returns 401)."""
    from app.middleware.conversation_first_guard import ConversationFirstGuard

    mw = ConversationFirstGuard(app=_MockApp())
    result = await _call_middleware(
        mw, method="POST", path="/api/v1/teams",
        headers=[],  # no Authorization header
    )

    assert result["status"] == 200
    assert result["called_downstream"] is True


@pytest.mark.asyncio
async def test_cfg_10_scope_state_admin_role():
    """CFG-10: scope['state']['user_role']='admin' bypasses DB lookup (fast path)."""
    from app.middleware.conversation_first_guard import ConversationFirstGuard

    mw = ConversationFirstGuard(app=_MockApp())
    result = await _call_middleware(
        mw, method="POST", path="/api/v1/teams",
        state={"user_role": "admin"},
    )

    assert result["status"] == 200
    assert result["called_downstream"] is True


@pytest.mark.asyncio
async def test_cfg_11_scope_state_member_role_blocked():
    """CFG-11: scope['state']['user_role']='member' → 403."""
    from app.middleware.conversation_first_guard import ConversationFirstGuard

    mw = ConversationFirstGuard(app=_MockApp())
    result = await _call_middleware(
        mw, method="POST", path="/api/v1/teams",
        state={"user_role": "member"},
    )

    assert result["status"] == 403
    assert result["called_downstream"] is False


@pytest.mark.asyncio
async def test_cfg_12_db_error_fails_open():
    """CFG-12: DB exception during role lookup → fail-open (pass-through)."""
    from app.middleware.conversation_first_guard import ConversationFirstGuard

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(side_effect=Exception("DB connection refused"))
    mock_db.__aenter__ = AsyncMock(return_value=mock_db)
    mock_db.__aexit__ = AsyncMock(return_value=None)

    with (
        patch("app.middleware.conversation_first_guard.ConversationFirstGuard._extract_user_id",
              return_value=_FAKE_USER_ID),
        patch("app.db.session.AsyncSessionLocal", return_value=mock_db),
    ):
        mw = ConversationFirstGuard(app=_MockApp())
        result = await _call_middleware(
            mw, method="POST", path="/api/v1/teams",
            headers=_make_auth_header(),
        )

    assert result["status"] == 200
    assert result["called_downstream"] is True


@pytest.mark.asyncio
async def test_cfg_13_disabled_env_var(monkeypatch):
    """CFG-13: CONVERSATION_FIRST_GUARD=false disables middleware entirely."""
    monkeypatch.setenv("CONVERSATION_FIRST_GUARD", "false")

    import importlib
    import app.middleware.conversation_first_guard as cfg_mod
    importlib.reload(cfg_mod)

    mw = cfg_mod.ConversationFirstGuard(app=_MockApp())
    result = await _call_middleware(
        mw, method="POST", path="/api/v1/teams",
    )

    assert result["status"] == 200
    assert result["called_downstream"] is True

    # Restore
    monkeypatch.delenv("CONVERSATION_FIRST_GUARD", raising=False)
    importlib.reload(cfg_mod)


@pytest.mark.asyncio
async def test_cfg_14_websocket_passes_through():
    """CFG-14: WebSocket scope type is ignored entirely."""
    from app.middleware.conversation_first_guard import ConversationFirstGuard

    downstream = _MockApp()
    mw = ConversationFirstGuard(app=downstream)

    scope: Scope = {
        "type": "websocket",
        "method": "GET",
        "path": "/api/v1/teams",
        "headers": [],
        "state": {},
    }

    async def _receive():
        return {}

    async def _send(event: dict) -> None:
        pass

    await mw(scope, _receive, _send)
    assert downstream.called is True


@pytest.mark.asyncio
async def test_cfg_15_403_response_body_schema():
    """CFG-15: 403 response has correct JSON schema with alternatives."""
    from app.middleware.conversation_first_guard import ConversationFirstGuard

    mock_user_result = MagicMock()
    mock_user_result.one_or_none.return_value = (False, False)

    mock_org_result = MagicMock()
    mock_org_result.all.return_value = [("viewer",)]

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(side_effect=[mock_user_result, mock_org_result])
    mock_db.__aenter__ = AsyncMock(return_value=mock_db)
    mock_db.__aexit__ = AsyncMock(return_value=None)

    with (
        patch("app.middleware.conversation_first_guard.ConversationFirstGuard._extract_user_id",
              return_value=_FAKE_USER_ID),
        patch("app.db.session.AsyncSessionLocal", return_value=mock_db),
    ):
        mw = ConversationFirstGuard(app=_MockApp())
        result = await _call_middleware(
            mw, method="DELETE", path="/api/v1/evidence/abc123",
            headers=_make_auth_header(),
        )

    assert result["status"] == 403
    body = result["body"]
    assert "detail" in body
    assert "error" in body
    assert body["error"] == "conversation_first_guard"
    assert "alternatives" in body
    assert "ott" in body["alternatives"]
    assert "cli" in body["alternatives"]


@pytest.mark.asyncio
async def test_cfg_16_all_write_methods_blocked():
    """CFG-16: All write methods (POST/PUT/PATCH/DELETE) are blocked for non-admin."""
    from app.middleware.conversation_first_guard import ConversationFirstGuard

    for method in ("POST", "PUT", "PATCH", "DELETE"):
        mock_user_result = MagicMock()
        mock_user_result.one_or_none.return_value = (False, False)

        mock_org_result = MagicMock()
        mock_org_result.all.return_value = [("member",)]

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(side_effect=[mock_user_result, mock_org_result])
        mock_db.__aenter__ = AsyncMock(return_value=mock_db)
        mock_db.__aexit__ = AsyncMock(return_value=None)

        with (
            patch("app.middleware.conversation_first_guard.ConversationFirstGuard._extract_user_id",
                  return_value=_FAKE_USER_ID),
            patch("app.db.session.AsyncSessionLocal", return_value=mock_db),
        ):
            mw = ConversationFirstGuard(app=_MockApp())
            result = await _call_middleware(
                mw, method=method, path="/api/v1/projects",
                headers=_make_auth_header(),
            )

        assert result["status"] == 403, f"{method} should be blocked for non-admin"


@pytest.mark.asyncio
async def test_cfg_17_multiple_org_roles_admin_in_any():
    """CFG-17: User with admin role in any org passes through."""
    from app.middleware.conversation_first_guard import ConversationFirstGuard

    mock_user_result = MagicMock()
    mock_user_result.one_or_none.return_value = (False, False)

    # Member in one org, admin in another
    mock_org_result = MagicMock()
    mock_org_result.all.return_value = [("member",), ("admin",)]

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(side_effect=[mock_user_result, mock_org_result])
    mock_db.__aenter__ = AsyncMock(return_value=mock_db)
    mock_db.__aexit__ = AsyncMock(return_value=None)

    with (
        patch("app.middleware.conversation_first_guard.ConversationFirstGuard._extract_user_id",
              return_value=_FAKE_USER_ID),
        patch("app.db.session.AsyncSessionLocal", return_value=mock_db),
    ):
        mw = ConversationFirstGuard(app=_MockApp())
        result = await _call_middleware(
            mw, method="POST", path="/api/v1/teams",
            headers=_make_auth_header(),
        )

    assert result["status"] == 200
    assert result["called_downstream"] is True


@pytest.mark.asyncio
async def test_cfg_18_user_not_found_fails_open():
    """CFG-18: User UUID not found in DB → fail-open (pass-through)."""
    from app.middleware.conversation_first_guard import ConversationFirstGuard

    mock_user_result = MagicMock()
    mock_user_result.one_or_none.return_value = None  # user not found

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_user_result)
    mock_db.__aenter__ = AsyncMock(return_value=mock_db)
    mock_db.__aexit__ = AsyncMock(return_value=None)

    with (
        patch("app.middleware.conversation_first_guard.ConversationFirstGuard._extract_user_id",
              return_value=_FAKE_USER_ID),
        patch("app.db.session.AsyncSessionLocal", return_value=mock_db),
    ):
        mw = ConversationFirstGuard(app=_MockApp())
        result = await _call_middleware(
            mw, method="POST", path="/api/v1/teams",
            headers=_make_auth_header(),
        )

    assert result["status"] == 200
    assert result["called_downstream"] is True


# ---------------------------------------------------------------------------
# Architecture test — pure ASGI, no BaseHTTPMiddleware
# ---------------------------------------------------------------------------

def test_cfg_architecture_pure_asgi():
    """ConversationFirstGuard must be pure ASGI (not BaseHTTPMiddleware)."""
    from starlette.middleware.base import BaseHTTPMiddleware
    from app.middleware.conversation_first_guard import ConversationFirstGuard

    assert not issubclass(ConversationFirstGuard, BaseHTTPMiddleware), (
        "ConversationFirstGuard MUST NOT inherit from BaseHTTPMiddleware "
        "(causes FastAPI 0.100+ hang on unhandled exceptions)"
    )
    assert callable(ConversationFirstGuard.__call__)
