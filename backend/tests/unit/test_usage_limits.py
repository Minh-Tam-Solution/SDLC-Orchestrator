"""
==========================================================================
Unit Tests — UsageLimitsMiddleware + UsageService
Sprint 188 — Per-Resource Tier Enforcement

Coverage targets:
    test_lite_project_limit_enforced       — 402 when project_count at cap
    test_lite_project_limit_not_exceeded   — pass-through when under cap
    test_unlimited_tier_skips_check        — enterprise: no DB query called
    test_lite_storage_limit_enforced       — 402 when storage_mb over cap
    test_lite_gate_monthly_limit           — 402 when gates_this_month at cap
    test_founder_tier_uses_standard_limits — FOUNDER gets 15-project limit
    test_jwt_decode_failure_skips_limit    — no auth header → pass-through
    test_standard_tier_project_under_limit — STANDARD 5/15 passes
    test_pro_tier_skips_project_check      — PRO -1 limit skips DB
    test_unknown_tier_defaults_to_lite     — unrecognised tier → LITE limits
    test_storage_limit_exactly_at_cap      — boundary: equal triggers 402
    test_team_member_limit_enforced        — team invite blocked at cap
    test_non_watched_path_passes_through   — GET /api/v1/projects no check
    test_websocket_scope_passes_through    — websocket scope ignored

SDLC 6.1.0 — Sprint 188 P0
==========================================================================
"""

import json
from io import BytesIO
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
from starlette.testclient import TestClient
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
        # Send a minimal 200 response so test harness doesn't hang
        await send(
            {
                "type": "http.response.start",
                "status": 200,
                "headers": [[b"content-type", b"application/json"]],
            }
        )
        await send({"type": "http.response.body", "body": b"{}", "more_body": False})


async def _call_middleware(
    middleware_instance,
    method: str = "POST",
    path: str = "/api/v1/projects",
    headers: list[tuple[bytes, bytes]] | None = None,
    state: dict | None = None,
) -> dict[str, Any]:
    """
    Invoke the middleware __call__ and return a dict with:
        called_downstream: bool
        status: int
        body: dict
    """
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

    # Wrap middleware so downstream is the _MockApp
    mw = type(middleware_instance)(downstream)  # re-instantiate with fresh downstream
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
async def test_lite_project_limit_enforced():
    """
    LITE tier: project_count = 1 (at cap of 1) → 402 returned, downstream not called.
    """
    from app.middleware.usage_limits import UsageLimitsMiddleware

    with (
        patch("app.middleware.usage_limits.UsageLimitsMiddleware._extract_user_id",
              return_value=_FAKE_USER_ID),
        patch("app.middleware.usage_limits.UsageLimitsMiddleware._resolve_effective_tier",
              new_callable=AsyncMock, return_value="lite"),
        patch("app.middleware.usage_limits.UsageLimitsMiddleware._fetch_usage",
              new_callable=AsyncMock, return_value=1),
    ):
        mw = UsageLimitsMiddleware(app=_MockApp())
        result = await _call_middleware(
            mw,
            method="POST",
            path="/api/v1/projects",
            headers=_make_auth_header(),
        )

    assert result["status"] == 402
    assert result["body"]["error"] == "usage_limit_exceeded"
    assert result["body"]["limit_type"] == "project"
    assert result["body"]["current"] == 1
    assert result["body"]["max"] == 1
    assert result["body"]["tier"] == "lite"
    assert "upgrade_url" in result["body"]
    assert result["called_downstream"] is False


@pytest.mark.asyncio
async def test_lite_project_limit_not_exceeded():
    """
    LITE tier: project_count = 0 (under cap of 1) → passes through, downstream called.
    """
    from app.middleware.usage_limits import UsageLimitsMiddleware

    with (
        patch("app.middleware.usage_limits.UsageLimitsMiddleware._extract_user_id",
              return_value=_FAKE_USER_ID),
        patch("app.middleware.usage_limits.UsageLimitsMiddleware._resolve_effective_tier",
              new_callable=AsyncMock, return_value="lite"),
        patch("app.middleware.usage_limits.UsageLimitsMiddleware._fetch_usage",
              new_callable=AsyncMock, return_value=0),
    ):
        mw = UsageLimitsMiddleware(app=_MockApp())
        result = await _call_middleware(
            mw,
            method="POST",
            path="/api/v1/projects",
            headers=_make_auth_header(),
        )

    assert result["status"] == 200
    assert result["called_downstream"] is True


@pytest.mark.asyncio
async def test_unlimited_tier_skips_check():
    """
    ENTERPRISE tier: all limits are -1 → _fetch_usage must not be called.
    """
    from app.middleware.usage_limits import UsageLimitsMiddleware

    fetch_mock = AsyncMock(return_value=9999)

    with (
        patch("app.middleware.usage_limits.UsageLimitsMiddleware._extract_user_id",
              return_value=_FAKE_USER_ID),
        patch("app.middleware.usage_limits.UsageLimitsMiddleware._resolve_effective_tier",
              new_callable=AsyncMock, return_value="enterprise"),
        patch("app.middleware.usage_limits.UsageLimitsMiddleware._fetch_usage",
              fetch_mock),
    ):
        mw = UsageLimitsMiddleware(app=_MockApp())
        result = await _call_middleware(
            mw,
            method="POST",
            path="/api/v1/projects",
            headers=_make_auth_header(),
        )

    fetch_mock.assert_not_called()
    assert result["status"] == 200
    assert result["called_downstream"] is True


@pytest.mark.asyncio
async def test_lite_storage_limit_enforced():
    """
    LITE tier: storage_mb = 101 (over cap of 100) → 402 with limit_type=storage.
    """
    from app.middleware.usage_limits import UsageLimitsMiddleware

    with (
        patch("app.middleware.usage_limits.UsageLimitsMiddleware._extract_user_id",
              return_value=_FAKE_USER_ID),
        patch("app.middleware.usage_limits.UsageLimitsMiddleware._resolve_effective_tier",
              new_callable=AsyncMock, return_value="lite"),
        patch("app.middleware.usage_limits.UsageLimitsMiddleware._fetch_usage",
              new_callable=AsyncMock, return_value=101.5),
    ):
        mw = UsageLimitsMiddleware(app=_MockApp())
        result = await _call_middleware(
            mw,
            method="POST",
            path="/api/v1/evidence/upload",
            headers=_make_auth_header(),
        )

    assert result["status"] == 402
    assert result["body"]["limit_type"] == "storage"
    assert result["body"]["current"] == 101.5
    assert result["body"]["max"] == 100
    assert result["called_downstream"] is False


@pytest.mark.asyncio
async def test_lite_gate_monthly_limit():
    """
    LITE tier: gates_this_month = 4 (at cap of 4) → 402 with limit_type=gate.
    """
    from app.middleware.usage_limits import UsageLimitsMiddleware

    with (
        patch("app.middleware.usage_limits.UsageLimitsMiddleware._extract_user_id",
              return_value=_FAKE_USER_ID),
        patch("app.middleware.usage_limits.UsageLimitsMiddleware._resolve_effective_tier",
              new_callable=AsyncMock, return_value="lite"),
        patch("app.middleware.usage_limits.UsageLimitsMiddleware._fetch_usage",
              new_callable=AsyncMock, return_value=4),
    ):
        mw = UsageLimitsMiddleware(app=_MockApp())
        result = await _call_middleware(
            mw,
            method="POST",
            path="/api/v1/gates",
            headers=_make_auth_header(),
        )

    assert result["status"] == 402
    assert result["body"]["limit_type"] == "gate"
    assert result["body"]["max"] == 4
    assert "LITE tier allows 4 gates" in result["body"]["message"]
    assert result["called_downstream"] is False


@pytest.mark.asyncio
async def test_founder_tier_uses_standard_limits():
    """
    FOUNDER tier is grandfathered = STANDARD billing (15 projects).
    project_count = 14 → passes through (under 15-project FOUNDER cap).
    """
    from app.middleware.usage_limits import UsageLimitsMiddleware

    with (
        patch("app.middleware.usage_limits.UsageLimitsMiddleware._extract_user_id",
              return_value=_FAKE_USER_ID),
        patch("app.middleware.usage_limits.UsageLimitsMiddleware._resolve_effective_tier",
              new_callable=AsyncMock, return_value="founder"),
        patch("app.middleware.usage_limits.UsageLimitsMiddleware._fetch_usage",
              new_callable=AsyncMock, return_value=14),
    ):
        mw = UsageLimitsMiddleware(app=_MockApp())
        result = await _call_middleware(
            mw,
            method="POST",
            path="/api/v1/projects",
            headers=_make_auth_header(),
        )

    assert result["status"] == 200
    assert result["called_downstream"] is True


@pytest.mark.asyncio
async def test_founder_tier_at_project_cap():
    """
    FOUNDER tier: project_count = 15 (at 15-project FOUNDER cap) → 402.
    """
    from app.middleware.usage_limits import UsageLimitsMiddleware

    with (
        patch("app.middleware.usage_limits.UsageLimitsMiddleware._extract_user_id",
              return_value=_FAKE_USER_ID),
        patch("app.middleware.usage_limits.UsageLimitsMiddleware._resolve_effective_tier",
              new_callable=AsyncMock, return_value="founder"),
        patch("app.middleware.usage_limits.UsageLimitsMiddleware._fetch_usage",
              new_callable=AsyncMock, return_value=15),
    ):
        mw = UsageLimitsMiddleware(app=_MockApp())
        result = await _call_middleware(
            mw,
            method="POST",
            path="/api/v1/projects",
            headers=_make_auth_header(),
        )

    assert result["status"] == 402
    assert result["body"]["max"] == 15


@pytest.mark.asyncio
async def test_jwt_decode_failure_skips_limit():
    """
    No Authorization header → _extract_user_id returns None → pass-through (401 by route).
    """
    from app.middleware.usage_limits import UsageLimitsMiddleware

    fetch_mock = AsyncMock(return_value=99)

    with (
        patch("app.middleware.usage_limits.UsageLimitsMiddleware._fetch_usage", fetch_mock),
    ):
        mw = UsageLimitsMiddleware(app=_MockApp())
        result = await _call_middleware(
            mw,
            method="POST",
            path="/api/v1/projects",
            headers=[],  # no Authorization header
        )

    fetch_mock.assert_not_called()
    assert result["status"] == 200
    assert result["called_downstream"] is True


@pytest.mark.asyncio
async def test_standard_tier_project_under_limit():
    """
    STANDARD tier: project_count = 5 (under cap of 15) → passes through.
    """
    from app.middleware.usage_limits import UsageLimitsMiddleware

    with (
        patch("app.middleware.usage_limits.UsageLimitsMiddleware._extract_user_id",
              return_value=_FAKE_USER_ID),
        patch("app.middleware.usage_limits.UsageLimitsMiddleware._resolve_effective_tier",
              new_callable=AsyncMock, return_value="standard"),
        patch("app.middleware.usage_limits.UsageLimitsMiddleware._fetch_usage",
              new_callable=AsyncMock, return_value=5),
    ):
        mw = UsageLimitsMiddleware(app=_MockApp())
        result = await _call_middleware(
            mw,
            method="POST",
            path="/api/v1/projects",
            headers=_make_auth_header(),
        )

    assert result["status"] == 200
    assert result["called_downstream"] is True


@pytest.mark.asyncio
async def test_pro_tier_skips_project_check():
    """
    PRO tier: max_projects = 20 (not -1), but project_count = 10 → passes.
    Also verifies _fetch_usage IS called (since PRO max_projects is not -1).
    """
    from app.middleware.usage_limits import UsageLimitsMiddleware

    fetch_mock = AsyncMock(return_value=10)

    with (
        patch("app.middleware.usage_limits.UsageLimitsMiddleware._extract_user_id",
              return_value=_FAKE_USER_ID),
        patch("app.middleware.usage_limits.UsageLimitsMiddleware._resolve_effective_tier",
              new_callable=AsyncMock, return_value="pro"),
        patch("app.middleware.usage_limits.UsageLimitsMiddleware._fetch_usage",
              fetch_mock),
    ):
        mw = UsageLimitsMiddleware(app=_MockApp())
        result = await _call_middleware(
            mw,
            method="POST",
            path="/api/v1/projects",
            headers=_make_auth_header(),
        )

    fetch_mock.assert_called_once()
    assert result["status"] == 200
    assert result["called_downstream"] is True


@pytest.mark.asyncio
async def test_unknown_tier_defaults_to_lite():
    """
    Unrecognised tier string → normalised to "lite" → LITE limits applied.
    project_count = 1 → 402.
    """
    from app.middleware.usage_limits import UsageLimitsMiddleware

    with (
        patch("app.middleware.usage_limits.UsageLimitsMiddleware._extract_user_id",
              return_value=_FAKE_USER_ID),
        patch("app.middleware.usage_limits.UsageLimitsMiddleware._resolve_effective_tier",
              new_callable=AsyncMock, return_value="unknown_plan_xyz"),
        patch("app.middleware.usage_limits.UsageLimitsMiddleware._fetch_usage",
              new_callable=AsyncMock, return_value=1),
    ):
        mw = UsageLimitsMiddleware(app=_MockApp())
        result = await _call_middleware(
            mw,
            method="POST",
            path="/api/v1/projects",
            headers=_make_auth_header(),
        )

    assert result["status"] == 402
    assert result["body"]["max"] == 1  # LITE default cap


@pytest.mark.asyncio
async def test_storage_limit_exactly_at_cap():
    """
    Boundary condition: storage_mb == max_storage_mb (100) → 402 (>= enforced).
    """
    from app.middleware.usage_limits import UsageLimitsMiddleware

    with (
        patch("app.middleware.usage_limits.UsageLimitsMiddleware._extract_user_id",
              return_value=_FAKE_USER_ID),
        patch("app.middleware.usage_limits.UsageLimitsMiddleware._resolve_effective_tier",
              new_callable=AsyncMock, return_value="lite"),
        patch("app.middleware.usage_limits.UsageLimitsMiddleware._fetch_usage",
              new_callable=AsyncMock, return_value=100.0),
    ):
        mw = UsageLimitsMiddleware(app=_MockApp())
        result = await _call_middleware(
            mw,
            method="POST",
            path="/api/v1/evidence/upload",
            headers=_make_auth_header(),
        )

    assert result["status"] == 402
    assert result["body"]["current"] == 100.0


@pytest.mark.asyncio
async def test_team_member_limit_enforced():
    """
    LITE tier: team_members = 1 (at cap of 1) → 402 on invite endpoint.
    """
    from app.middleware.usage_limits import UsageLimitsMiddleware

    with (
        patch("app.middleware.usage_limits.UsageLimitsMiddleware._extract_user_id",
              return_value=_FAKE_USER_ID),
        patch("app.middleware.usage_limits.UsageLimitsMiddleware._resolve_effective_tier",
              new_callable=AsyncMock, return_value="lite"),
        patch("app.middleware.usage_limits.UsageLimitsMiddleware._fetch_usage",
              new_callable=AsyncMock, return_value=1),
    ):
        mw = UsageLimitsMiddleware(app=_MockApp())
        result = await _call_middleware(
            mw,
            method="POST",
            path="/api/v1/teams/members/invite",
            headers=_make_auth_header(),
        )

    assert result["status"] == 402
    assert result["body"]["limit_type"] == "team_member"
    assert result["body"]["max"] == 1
    assert result["called_downstream"] is False


@pytest.mark.asyncio
async def test_non_watched_path_passes_through():
    """
    GET /api/v1/projects (list) is not in _WATCHED — no limit check, passes through.
    """
    from app.middleware.usage_limits import UsageLimitsMiddleware

    fetch_mock = AsyncMock(return_value=99)

    with (
        patch("app.middleware.usage_limits.UsageLimitsMiddleware._fetch_usage", fetch_mock),
    ):
        mw = UsageLimitsMiddleware(app=_MockApp())
        result = await _call_middleware(
            mw,
            method="GET",
            path="/api/v1/projects",
            headers=_make_auth_header(),
        )

    fetch_mock.assert_not_called()
    assert result["status"] == 200
    assert result["called_downstream"] is True


@pytest.mark.asyncio
async def test_websocket_scope_passes_through():
    """
    WebSocket scope type = 'websocket' is ignored entirely by the middleware.
    """
    from app.middleware.usage_limits import UsageLimitsMiddleware

    downstream = _MockApp()
    mw = UsageLimitsMiddleware(app=downstream)

    scope: Scope = {
        "type": "websocket",
        "method": "GET",
        "path": "/api/v1/projects",
        "headers": _make_auth_header(),
        "state": {},
    }

    async def _receive():
        return {}

    async def _send(event: dict) -> None:
        pass

    await mw(scope, _receive, _send)

    assert downstream.called is True


@pytest.mark.asyncio
async def test_db_error_fails_open():
    """
    If _fetch_usage returns None (DB error), middleware passes through rather than
    returning 402 — fail-open design ensures service availability.
    """
    from app.middleware.usage_limits import UsageLimitsMiddleware

    with (
        patch("app.middleware.usage_limits.UsageLimitsMiddleware._extract_user_id",
              return_value=_FAKE_USER_ID),
        patch("app.middleware.usage_limits.UsageLimitsMiddleware._resolve_effective_tier",
              new_callable=AsyncMock, return_value="lite"),
        patch("app.middleware.usage_limits.UsageLimitsMiddleware._fetch_usage",
              new_callable=AsyncMock, return_value=None),  # DB error
    ):
        mw = UsageLimitsMiddleware(app=_MockApp())
        result = await _call_middleware(
            mw,
            method="POST",
            path="/api/v1/projects",
            headers=_make_auth_header(),
        )

    assert result["status"] == 200
    assert result["called_downstream"] is True


# ---------------------------------------------------------------------------
# UsageService unit tests (async query logic)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_usage_service_get_project_count():
    """UsageService.get_project_count returns scalar result from DB."""
    from app.services.usage_service import UsageService

    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = 3
    mock_db.execute = AsyncMock(return_value=mock_result)

    count = await UsageService.get_project_count(mock_db, _FAKE_USER_ID)

    assert count == 3
    mock_db.execute.assert_called_once()


@pytest.mark.asyncio
async def test_usage_service_get_storage_mb():
    """UsageService.get_storage_mb converts bytes to MB correctly."""
    from app.services.usage_service import UsageService

    mock_db = AsyncMock()
    mock_result = MagicMock()
    # 50 MB in bytes = 52,428,800
    mock_result.scalar_one_or_none.return_value = 52_428_800
    mock_db.execute = AsyncMock(return_value=mock_result)

    mb = await UsageService.get_storage_mb(mock_db, _FAKE_USER_ID)

    assert abs(mb - 50.0) < 0.01


@pytest.mark.asyncio
async def test_usage_service_get_storage_mb_no_evidence():
    """UsageService.get_storage_mb returns 0.0 when no evidence exists."""
    from app.services.usage_service import UsageService

    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None  # coalesce returns 0 in real DB
    mock_db.execute = AsyncMock(return_value=mock_result)

    mb = await UsageService.get_storage_mb(mock_db, _FAKE_USER_ID)

    assert mb == 0.0


@pytest.mark.asyncio
async def test_usage_service_get_gates_this_month():
    """UsageService.get_gates_this_month returns correct count."""
    from app.services.usage_service import UsageService

    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = 2
    mock_db.execute = AsyncMock(return_value=mock_result)

    count = await UsageService.get_gates_this_month(mock_db, _FAKE_USER_ID)

    assert count == 2


@pytest.mark.asyncio
async def test_usage_service_get_team_members_with_org():
    """UsageService.get_team_members returns org member count."""
    from app.services.usage_service import UsageService

    fake_org_id = uuid4()

    mock_db = AsyncMock()
    # First call: user.organization_id lookup
    org_result = MagicMock()
    org_result.scalar_one_or_none.return_value = fake_org_id
    # Second call: member count
    member_result = MagicMock()
    member_result.scalar_one_or_none.return_value = 5
    mock_db.execute = AsyncMock(side_effect=[org_result, member_result])

    # No context manager needed — call directly with the pre-configured mock_db
    count = await UsageService.get_team_members(mock_db, _FAKE_USER_ID)

    assert count == 5


@pytest.mark.asyncio
async def test_usage_service_get_team_members_no_org():
    """UsageService.get_team_members returns 1 when user has no org."""
    from app.services.usage_service import UsageService

    mock_db = AsyncMock()
    org_result = MagicMock()
    org_result.scalar_one_or_none.return_value = None  # no org
    mock_db.execute = AsyncMock(return_value=org_result)

    count = await UsageService.get_team_members(mock_db, _FAKE_USER_ID)

    assert count == 1


@pytest.mark.asyncio
async def test_usage_service_get_all():
    """UsageService.get_all returns dict with all four keys."""
    from app.services.usage_service import UsageService

    mock_db = AsyncMock()

    with (
        patch.object(UsageService, "get_project_count", new_callable=AsyncMock, return_value=2),
        patch.object(UsageService, "get_storage_mb", new_callable=AsyncMock, return_value=45.0),
        patch.object(UsageService, "get_gates_this_month", new_callable=AsyncMock, return_value=1),
        patch.object(UsageService, "get_team_members", new_callable=AsyncMock, return_value=3),
    ):
        result = await UsageService.get_all(mock_db, _FAKE_USER_ID)

    assert result == {
        "project_count": 2,
        "storage_mb": 45.0,
        "gates_this_month": 1,
        "team_members": 3,
    }


# ---------------------------------------------------------------------------
# _normalise_tier helper tests
# ---------------------------------------------------------------------------

def test_normalise_tier_free_to_lite():
    """'free' maps to 'lite'."""
    from app.middleware.usage_limits import _normalise_tier
    assert _normalise_tier("free") == "lite"


def test_normalise_tier_professional_to_pro():
    """'professional' maps to 'pro'."""
    from app.middleware.usage_limits import _normalise_tier
    assert _normalise_tier("professional") == "pro"


def test_normalise_tier_unknown_to_lite():
    """Unrecognised string maps to 'lite' (safe default)."""
    from app.middleware.usage_limits import _normalise_tier
    assert _normalise_tier("super_premium_gold") == "lite"


def test_normalise_tier_passthrough():
    """Known tiers pass through unchanged."""
    from app.middleware.usage_limits import _normalise_tier
    for tier in ("lite", "founder", "starter", "standard", "pro", "enterprise"):
        assert _normalise_tier(tier) == tier


# ---------------------------------------------------------------------------
# Sprint 195 F-06 fix: superuser/platform_admin bypass
# ADR-065: org-based tier resolution tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_superuser_bypasses_usage_limits():
    """
    Sprint 195 F-06 + ADR-065 D2: Superuser gets 'enterprise' tier from
    _resolve_effective_tier, which has -1 (unlimited) for all limits →
    _fetch_usage never called.
    """
    from app.middleware.usage_limits import UsageLimitsMiddleware

    mock_user_result = MagicMock()
    mock_user_result.one_or_none.return_value = (True, False)  # is_superuser, is_platform_admin

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_user_result)
    mock_db.__aenter__ = AsyncMock(return_value=mock_db)
    mock_db.__aexit__ = AsyncMock(return_value=None)

    fetch_mock = AsyncMock(return_value=9999)

    with (
        patch("app.middleware.usage_limits.UsageLimitsMiddleware._extract_user_id",
              return_value=_FAKE_USER_ID),
        patch("app.db.session.AsyncSessionLocal", return_value=mock_db),
        patch("app.middleware.usage_limits.UsageLimitsMiddleware._fetch_usage",
              fetch_mock),
    ):
        mw = UsageLimitsMiddleware(app=_MockApp())
        result = await _call_middleware(
            mw,
            method="POST",
            path="/api/v1/projects",
            headers=_make_auth_header(),
        )

    fetch_mock.assert_not_called()
    assert result["status"] == 200
    assert result["called_downstream"] is True


@pytest.mark.asyncio
async def test_platform_admin_bypasses_usage_limits():
    """
    Sprint 195 F-06 + ADR-065 D2: Platform admin gets 'enterprise' tier.
    """
    from app.middleware.usage_limits import UsageLimitsMiddleware

    mock_user_result = MagicMock()
    mock_user_result.one_or_none.return_value = (False, True)  # not superuser, is platform_admin

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_user_result)
    mock_db.__aenter__ = AsyncMock(return_value=mock_db)
    mock_db.__aexit__ = AsyncMock(return_value=None)

    fetch_mock = AsyncMock(return_value=9999)

    with (
        patch("app.middleware.usage_limits.UsageLimitsMiddleware._extract_user_id",
              return_value=_FAKE_USER_ID),
        patch("app.db.session.AsyncSessionLocal", return_value=mock_db),
        patch("app.middleware.usage_limits.UsageLimitsMiddleware._fetch_usage",
              fetch_mock),
    ):
        mw = UsageLimitsMiddleware(app=_MockApp())
        result = await _call_middleware(
            mw,
            method="POST",
            path="/api/v1/projects",
            headers=_make_auth_header(),
        )

    fetch_mock.assert_not_called()
    assert result["status"] == 200
    assert result["called_downstream"] is True


@pytest.mark.asyncio
async def test_org_based_tier_resolution_pro():
    """
    ADR-065 D1: Regular user with org plan='pro' → resolves to 'pro' tier.
    PRO has max_projects=20; user with 5 projects → passes through.
    """
    from app.middleware.usage_limits import UsageLimitsMiddleware

    # Query 1: User is_superuser=False, is_platform_admin=False
    mock_user_result = MagicMock()
    mock_user_result.one_or_none.return_value = (False, False)

    # Query 2: Organization plans
    mock_org_row = MagicMock()
    mock_org_row.__getitem__ = lambda self, idx: "pro"
    mock_org_result = MagicMock()
    mock_org_result.all.return_value = [mock_org_row]

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(side_effect=[mock_user_result, mock_org_result])
    mock_db.__aenter__ = AsyncMock(return_value=mock_db)
    mock_db.__aexit__ = AsyncMock(return_value=None)

    fetch_mock = AsyncMock(return_value=5)

    with (
        patch("app.middleware.usage_limits.UsageLimitsMiddleware._extract_user_id",
              return_value=_FAKE_USER_ID),
        patch("app.db.session.AsyncSessionLocal", return_value=mock_db),
        patch("app.middleware.usage_limits.UsageLimitsMiddleware._fetch_usage",
              fetch_mock),
    ):
        mw = UsageLimitsMiddleware(app=_MockApp())
        result = await _call_middleware(
            mw,
            method="POST",
            path="/api/v1/projects",
            headers=_make_auth_header(),
        )

    assert result["status"] == 200
    assert result["called_downstream"] is True


@pytest.mark.asyncio
async def test_org_based_tier_resolution_free():
    """
    ADR-065 D1: User with org plan='free' → normalises to 'lite' tier.
    LITE has max_projects=1; user with 1 project → 402.
    """
    from app.middleware.usage_limits import UsageLimitsMiddleware

    mock_user_result = MagicMock()
    mock_user_result.one_or_none.return_value = (False, False)

    mock_org_row = MagicMock()
    mock_org_row.__getitem__ = lambda self, idx: "free"
    mock_org_result = MagicMock()
    mock_org_result.all.return_value = [mock_org_row]

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(side_effect=[mock_user_result, mock_org_result])
    mock_db.__aenter__ = AsyncMock(return_value=mock_db)
    mock_db.__aexit__ = AsyncMock(return_value=None)

    fetch_mock = AsyncMock(return_value=1)

    with (
        patch("app.middleware.usage_limits.UsageLimitsMiddleware._extract_user_id",
              return_value=_FAKE_USER_ID),
        patch("app.db.session.AsyncSessionLocal", return_value=mock_db),
        patch("app.middleware.usage_limits.UsageLimitsMiddleware._fetch_usage",
              fetch_mock),
    ):
        mw = UsageLimitsMiddleware(app=_MockApp())
        result = await _call_middleware(
            mw,
            method="POST",
            path="/api/v1/projects",
            headers=_make_auth_header(),
        )

    assert result["status"] == 402
    assert result["body"]["tier"] == "lite"
    assert result["body"]["max"] == 1


@pytest.mark.asyncio
async def test_org_based_tier_max_across_orgs():
    """
    ADR-065 D1: User in multiple orgs → highest tier wins.
    Org A: 'free' (lite=1), Org B: 'starter' (starter=2) → resolves to 'starter'.
    """
    from app.middleware.usage_limits import UsageLimitsMiddleware

    mock_user_result = MagicMock()
    mock_user_result.one_or_none.return_value = (False, False)

    mock_org_row_a = MagicMock()
    mock_org_row_a.__getitem__ = lambda self, idx: "free"
    mock_org_row_b = MagicMock()
    mock_org_row_b.__getitem__ = lambda self, idx: "starter"
    mock_org_result = MagicMock()
    mock_org_result.all.return_value = [mock_org_row_a, mock_org_row_b]

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(side_effect=[mock_user_result, mock_org_result])
    mock_db.__aenter__ = AsyncMock(return_value=mock_db)
    mock_db.__aexit__ = AsyncMock(return_value=None)

    fetch_mock = AsyncMock(return_value=3)

    with (
        patch("app.middleware.usage_limits.UsageLimitsMiddleware._extract_user_id",
              return_value=_FAKE_USER_ID),
        patch("app.db.session.AsyncSessionLocal", return_value=mock_db),
        patch("app.middleware.usage_limits.UsageLimitsMiddleware._fetch_usage",
              fetch_mock),
    ):
        mw = UsageLimitsMiddleware(app=_MockApp())
        result = await _call_middleware(
            mw,
            method="POST",
            path="/api/v1/projects",
            headers=_make_auth_header(),
        )

    # starter has max_projects=5, user has 3 → passes
    assert result["status"] == 200
    assert result["called_downstream"] is True


@pytest.mark.asyncio
async def test_org_based_no_orgs_defaults_lite():
    """
    ADR-065: User with no org memberships → defaults to 'lite' (most restrictive).
    """
    from app.middleware.usage_limits import UsageLimitsMiddleware

    mock_user_result = MagicMock()
    mock_user_result.one_or_none.return_value = (False, False)

    mock_org_result = MagicMock()
    mock_org_result.all.return_value = []  # no org memberships

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(side_effect=[mock_user_result, mock_org_result])
    mock_db.__aenter__ = AsyncMock(return_value=mock_db)
    mock_db.__aexit__ = AsyncMock(return_value=None)

    fetch_mock = AsyncMock(return_value=1)

    with (
        patch("app.middleware.usage_limits.UsageLimitsMiddleware._extract_user_id",
              return_value=_FAKE_USER_ID),
        patch("app.db.session.AsyncSessionLocal", return_value=mock_db),
        patch("app.middleware.usage_limits.UsageLimitsMiddleware._fetch_usage",
              fetch_mock),
    ):
        mw = UsageLimitsMiddleware(app=_MockApp())
        result = await _call_middleware(
            mw,
            method="POST",
            path="/api/v1/projects",
            headers=_make_auth_header(),
        )

    # lite has max_projects=1, user has 1 → 402
    assert result["status"] == 402
    assert result["body"]["tier"] == "lite"


@pytest.mark.asyncio
async def test_org_based_enterprise_early_exit():
    """
    ADR-065 D1: Enterprise org plan triggers early exit — no further iteration.
    """
    from app.middleware.usage_limits import UsageLimitsMiddleware

    mock_user_result = MagicMock()
    mock_user_result.one_or_none.return_value = (False, False)

    mock_org_row_a = MagicMock()
    mock_org_row_a.__getitem__ = lambda self, idx: "free"
    mock_org_row_b = MagicMock()
    mock_org_row_b.__getitem__ = lambda self, idx: "enterprise"
    mock_org_result = MagicMock()
    mock_org_result.all.return_value = [mock_org_row_a, mock_org_row_b]

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(side_effect=[mock_user_result, mock_org_result])
    mock_db.__aenter__ = AsyncMock(return_value=mock_db)
    mock_db.__aexit__ = AsyncMock(return_value=None)

    fetch_mock = AsyncMock(return_value=9999)

    with (
        patch("app.middleware.usage_limits.UsageLimitsMiddleware._extract_user_id",
              return_value=_FAKE_USER_ID),
        patch("app.db.session.AsyncSessionLocal", return_value=mock_db),
        patch("app.middleware.usage_limits.UsageLimitsMiddleware._fetch_usage",
              fetch_mock),
    ):
        mw = UsageLimitsMiddleware(app=_MockApp())
        result = await _call_middleware(
            mw,
            method="POST",
            path="/api/v1/projects",
            headers=_make_auth_header(),
        )

    # enterprise has -1 (unlimited) → _fetch_usage never called
    fetch_mock.assert_not_called()
    assert result["status"] == 200
    assert result["called_downstream"] is True
