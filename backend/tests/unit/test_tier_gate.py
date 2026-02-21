"""
test_tier_gate.py — Sprint 184-185 TG-01..41

Unit tests for TierGateMiddleware (pure ASGI, ADR-059 INV-03).

Test IDs: TG-01 to TG-41 (41 tests)

Coverage:
  TG-01..09  Tier level access control (LITE/STANDARD/PROFESSIONAL/ENTERPRISE)
  TG-10..12  402 response body schema
  TG-13..15  Pass-through scenarios (unauthenticated, GDPR, health)
  TG-16..17  ASGI architecture requirements
  TG-18..20  Prefix matching edge cases
  TG-21..22  Admin bypass header
  TG-23..25  Prefix matching semantics
  TG-26..27  Performance and completeness (TG-27: dynamic, no hardcoded count)
  TG-28..29  STANDARD tier routes
  TG-30..34  State resolution and response format
  TG-35..37  ENTERPRISE sub-routes
  TG-38..40  Edge cases and performance
  TG-41      CI route coverage — all FastAPI prefixes in ROUTE_TIER_TABLE (Sprint 185)

Framework: pytest + pytest-asyncio
"""

from __future__ import annotations

import json
import os
import time
import pytest

from starlette.types import ASGIApp, Receive, Scope, Send
from starlette.responses import Response

from app.middleware.tier_gate import (
    TierGateMiddleware,
    ROUTE_TIER_TABLE,
    TIER_NAMES,
    TIER_VALUES,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _dummy_app(scope: Scope, receive: Receive, send: Send) -> None:
    """Minimal ASGI app that returns 200 OK with 'PASS' body."""
    response = Response("PASS", status_code=200)
    await response(scope, receive, send)


def _make_scope(
    path: str,
    user_tier: str | None = None,
    method: str = "GET",
    scope_type: str = "http",
    headers: list[tuple[bytes, bytes]] | None = None,
) -> dict:
    """Build a minimal ASGI scope dict for testing."""
    state: dict = {}
    if user_tier is not None:
        state["user_tier"] = user_tier

    base_headers: list[tuple[bytes, bytes]] = headers or []

    scope: dict = {
        "type": scope_type,
        "method": method,
        "path": path,
        "query_string": b"",
        "headers": base_headers,
        "state": state,
        "client": ("127.0.0.1", 12345),
    }
    return scope


async def _call_middleware(
    path: str,
    user_tier: str | None = None,
    scope_type: str = "http",
    headers: list[tuple[bytes, bytes]] | None = None,
) -> tuple[int, dict]:
    """
    Run TierGateMiddleware against a mock request.

    Returns (status_code, response_body_dict).
    """
    middleware = TierGateMiddleware(_dummy_app)
    scope = _make_scope(path, user_tier=user_tier, scope_type=scope_type, headers=headers)

    # Capture the HTTP response
    received_status: list[int] = []
    received_body: list[bytes] = []

    async def _receive():
        return {"type": "http.disconnect"}

    async def _send(message):
        if message["type"] == "http.response.start":
            received_status.append(message["status"])
        elif message["type"] == "http.response.body":
            received_body.append(message.get("body", b""))

    await middleware(scope, _receive, _send)

    status = received_status[0] if received_status else 200
    body_bytes = b"".join(received_body)
    body = {}
    if body_bytes:
        try:
            body = json.loads(body_bytes)
        except json.JSONDecodeError:
            body = {"raw": body_bytes.decode()}
    return status, body


# ---------------------------------------------------------------------------
# TG-01..09: Tier level access control
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_tg_01_lite_user_accesses_auth_route():
    """TG-01: LITE user can access /api/v1/auth endpoints (tier=1)."""
    status, _ = await _call_middleware("/api/v1/auth/login", user_tier="LITE")
    assert status == 200


@pytest.mark.asyncio
async def test_tg_02_lite_user_accesses_projects():
    """TG-02: LITE user can access /api/v1/projects (tier=1)."""
    status, _ = await _call_middleware("/api/v1/projects", user_tier="LITE")
    assert status == 200


@pytest.mark.asyncio
async def test_tg_03_lite_user_blocked_agent_team():
    """TG-03: LITE user gets 402 on /api/v1/agent-team (needs PROFESSIONAL)."""
    status, body = await _call_middleware("/api/v1/agent-team/definitions", user_tier="LITE")
    assert status == 402
    assert body["required_tier"] == "PROFESSIONAL"


@pytest.mark.asyncio
async def test_tg_04_lite_user_blocked_enterprise_sso():
    """TG-04: LITE user gets 402 on /api/v1/enterprise/sso (needs ENTERPRISE)."""
    status, body = await _call_middleware("/api/v1/enterprise/sso/configure", user_tier="LITE")
    assert status == 402
    assert body["required_tier"] == "ENTERPRISE"


@pytest.mark.asyncio
async def test_tg_05_standard_user_accesses_teams():
    """TG-05: STANDARD user can access /api/v1/teams (tier=2)."""
    status, _ = await _call_middleware("/api/v1/teams", user_tier="STANDARD")
    assert status == 200


@pytest.mark.asyncio
async def test_tg_06_standard_user_blocked_agent_team():
    """TG-06: STANDARD user gets 402 on /api/v1/agent-team (needs PROFESSIONAL)."""
    status, body = await _call_middleware("/api/v1/agent-team/conversations", user_tier="STANDARD")
    assert status == 402
    assert body["required_tier"] == "PROFESSIONAL"


@pytest.mark.asyncio
async def test_tg_07_professional_user_accesses_agent_team():
    """TG-07: PROFESSIONAL user can access /api/v1/agent-team."""
    status, _ = await _call_middleware("/api/v1/agent-team/conversations", user_tier="PROFESSIONAL")
    assert status == 200


@pytest.mark.asyncio
async def test_tg_08_professional_user_blocked_enterprise_sso():
    """TG-08: PROFESSIONAL user gets 402 on /api/v1/enterprise/sso (needs ENTERPRISE)."""
    status, body = await _call_middleware("/api/v1/enterprise/sso/configure", user_tier="PROFESSIONAL")
    assert status == 402
    assert body["required_tier"] == "ENTERPRISE"


@pytest.mark.asyncio
async def test_tg_09_enterprise_user_accesses_all_routes():
    """TG-09: ENTERPRISE user can access all route tiers."""
    for path in [
        "/api/v1/auth/login",
        "/api/v1/teams",
        "/api/v1/agent-team/definitions",
        "/api/v1/enterprise/sso/configure",
        "/api/v1/nist/govern",
        "/api/v1/admin/users",
    ]:
        status, _ = await _call_middleware(path, user_tier="ENTERPRISE")
        assert status == 200, f"ENTERPRISE should access {path}, got {status}"


# ---------------------------------------------------------------------------
# TG-10..12: 402 response body schema
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_tg_10_402_body_has_required_tier():
    """TG-10: 402 response body includes required_tier field."""
    _, body = await _call_middleware("/api/v1/agent-team/messages", user_tier="LITE")
    assert "required_tier" in body
    assert body["required_tier"] == "PROFESSIONAL"


@pytest.mark.asyncio
async def test_tg_11_402_body_has_current_tier():
    """TG-11: 402 response body includes current_tier field."""
    _, body = await _call_middleware("/api/v1/agent-team/messages", user_tier="LITE")
    assert "current_tier" in body
    assert body["current_tier"] == "LITE"


@pytest.mark.asyncio
async def test_tg_12_402_body_has_upgrade_url():
    """TG-12: 402 response body includes upgrade_url."""
    _, body = await _call_middleware("/api/v1/enterprise/sso/configure", user_tier="LITE")
    assert "upgrade_url" in body
    assert body["upgrade_url"]  # non-empty string


# ---------------------------------------------------------------------------
# TG-13..15: Pass-through scenarios
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_tg_13_unauthenticated_lite_route_passes():
    """TG-13: TierGate passes unauthenticated requests on LITE routes (401 handled by auth)."""
    # No user_tier in scope state — defaults to LITE internally
    status, _ = await _call_middleware("/api/v1/auth/login", user_tier=None)
    assert status == 200


@pytest.mark.asyncio
async def test_tg_14_gdpr_accessible_by_lite():
    """TG-14: /api/v1/gdpr accessible by LITE users (privacy law — all tiers)."""
    status, _ = await _call_middleware("/api/v1/gdpr/consent", user_tier="LITE")
    assert status == 200


@pytest.mark.asyncio
async def test_tg_15_health_accessible_without_tier():
    """TG-15: /api/v1/health accessible by all (no tier restriction)."""
    status, _ = await _call_middleware("/api/v1/health", user_tier=None)
    assert status == 200


# ---------------------------------------------------------------------------
# TG-16..17: ASGI architecture requirements
# ---------------------------------------------------------------------------

def test_tg_16_middleware_is_pure_asgi():
    """TG-16: TierGateMiddleware is pure ASGI (no BaseHTTPMiddleware inheritance)."""
    from starlette.middleware.base import BaseHTTPMiddleware
    assert not issubclass(TierGateMiddleware, BaseHTTPMiddleware), (
        "TierGateMiddleware MUST NOT inherit from BaseHTTPMiddleware "
        "(causes FastAPI 0.100+ hang on unhandled exceptions)"
    )
    # Must implement __call__ directly
    assert callable(TierGateMiddleware.__call__)


@pytest.mark.asyncio
async def test_tg_17_non_http_scope_passes_through():
    """TG-17: TierGateMiddleware passes non-http scope (websocket) through unchanged."""
    called = []

    async def _capture_app(scope, receive, send):
        called.append(scope["type"])

    middleware = TierGateMiddleware(_capture_app)
    scope = {"type": "websocket", "path": "/ws/connect", "state": {}}

    await middleware(scope, None, None)
    assert called == ["websocket"]


# ---------------------------------------------------------------------------
# TG-18..20: Prefix matching edge cases
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_tg_18_nist_with_trailing_slash_is_enterprise():
    """TG-18: route /api/v1/nist/ (with trailing slash) correctly maps to ENTERPRISE."""
    status, body = await _call_middleware("/api/v1/nist/govern/policies", user_tier="LITE")
    assert status == 402
    assert body["required_tier"] == "ENTERPRISE"


@pytest.mark.asyncio
async def test_tg_19_enterprise_sso_deep_path_is_enterprise():
    """TG-19: route /api/v1/enterprise/sso/saml/callback maps to ENTERPRISE."""
    status, body = await _call_middleware("/api/v1/enterprise/sso/saml/callback", user_tier="PROFESSIONAL")
    assert status == 402
    assert body["required_tier"] == "ENTERPRISE"


@pytest.mark.asyncio
async def test_tg_20_unknown_route_passes_through():
    """TG-20: Unknown route (not in ROUTE_TIER_TABLE) passes through (no tier requirement)."""
    # A completely unknown prefix should not be blocked
    status, _ = await _call_middleware("/api/v1/unknown-endpoint/xyz", user_tier="LITE")
    assert status == 200


# ---------------------------------------------------------------------------
# TG-21..22: Admin bypass header
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_tg_21_admin_bypass_valid_secret_skips_tier_check(monkeypatch):
    """TG-21: Admin bypass header X-Admin-Override: {secret} skips tier check."""
    secret = "test-admin-secret-s184"
    monkeypatch.setenv("TIER_GATE_ADMIN_SECRET", secret)

    # Reload the module to pick up env var change
    import importlib
    import app.middleware.tier_gate as tg_mod
    importlib.reload(tg_mod)

    middleware = tg_mod.TierGateMiddleware(_dummy_app)
    scope = _make_scope(
        "/api/v1/enterprise/sso/configure",
        user_tier="LITE",
        headers=[(b"x-admin-override", secret.encode())],
    )
    # Must pass through (no 402) because bypass is active

    received_status: list[int] = []

    async def _send(message):
        if message["type"] == "http.response.start":
            received_status.append(message["status"])

    async def _receive():
        return {"type": "http.disconnect"}

    await middleware(scope, _receive, _send)
    assert received_status == [200]

    # Restore
    monkeypatch.delenv("TIER_GATE_ADMIN_SECRET", raising=False)
    importlib.reload(tg_mod)


@pytest.mark.asyncio
async def test_tg_22_admin_bypass_invalid_secret_still_returns_402(monkeypatch):
    """TG-22: Admin bypass requires valid secret (invalid secret still returns 402)."""
    monkeypatch.setenv("TIER_GATE_ADMIN_SECRET", "correct-secret")

    import importlib
    import app.middleware.tier_gate as tg_mod
    importlib.reload(tg_mod)

    middleware = tg_mod.TierGateMiddleware(_dummy_app)
    scope = _make_scope(
        "/api/v1/enterprise/sso/configure",
        user_tier="LITE",
        headers=[(b"x-admin-override", b"wrong-secret")],
    )

    received_status: list[int] = []

    async def _send(message):
        if message["type"] == "http.response.start":
            received_status.append(message["status"])

    async def _receive():
        return {"type": "http.disconnect"}

    await middleware(scope, _receive, _send)
    assert received_status == [402]

    monkeypatch.delenv("TIER_GATE_ADMIN_SECRET", raising=False)
    importlib.reload(tg_mod)


# ---------------------------------------------------------------------------
# TG-23..25: Prefix matching semantics
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_tg_23_prefix_matching_not_exact():
    """TG-23: Tier check uses prefix matching, not exact match."""
    # /api/v1/agent-team is PROFESSIONAL; any sub-path should also be PROFESSIONAL
    for sub_path in [
        "/api/v1/agent-team",
        "/api/v1/agent-team/",
        "/api/v1/agent-team/definitions",
        "/api/v1/agent-team/conversations/abc-123",
        "/api/v1/agent-team/conversations/abc/messages",
    ]:
        status, _ = await _call_middleware(sub_path, user_tier="PROFESSIONAL")
        assert status == 200, f"PROFESSIONAL should access {sub_path}"


@pytest.mark.asyncio
async def test_tg_24_jira_requires_professional():
    """TG-24: /api/v1/jira requires PROFESSIONAL tier."""
    # STANDARD blocked
    status, body = await _call_middleware("/api/v1/jira/projects", user_tier="STANDARD")
    assert status == 402
    assert body["required_tier"] == "PROFESSIONAL"
    # PROFESSIONAL passes
    status, _ = await _call_middleware("/api/v1/jira/sync", user_tier="PROFESSIONAL")
    assert status == 200


@pytest.mark.asyncio
async def test_tg_25_professional_user_accesses_channels():
    """TG-25: PROFESSIONAL user can access /api/v1/channels (OTT gateway, tier=STANDARD)."""
    # STANDARD user accesses channels
    status, _ = await _call_middleware("/api/v1/channels/telegram/webhook", user_tier="STANDARD")
    assert status == 200
    # PROFESSIONAL can too
    status, _ = await _call_middleware("/api/v1/channels/teams/webhook", user_tier="PROFESSIONAL")
    assert status == 200


# ---------------------------------------------------------------------------
# TG-26..27: Performance and completeness
# ---------------------------------------------------------------------------

def test_tg_26_tier_check_under_1ms():
    """TG-26: Performance: tier check adds <1ms overhead (pure dict lookup)."""
    middleware = TierGateMiddleware(_dummy_app)
    # Warm up
    for _ in range(10):
        middleware._get_required_tier("/api/v1/agent-team/messages")

    # Measure 1000 lookups
    start = time.perf_counter()
    for _ in range(1000):
        middleware._get_required_tier("/api/v1/agent-team/messages")
    elapsed_ms = (time.perf_counter() - start) * 1000

    # 1000 lookups in <100ms = <0.1ms each (well under 1ms budget)
    assert elapsed_ms < 100, f"1000 lookups took {elapsed_ms:.2f}ms (expected <100ms)"


def test_tg_27_route_tier_table_covers_expected_routes():
    """TG-27: ROUTE_TIER_TABLE is populated and covers all 4 tier levels.

    Sprint 185 CTO action item #3: removed hardcoded >= 79 in favour of a
    dynamic minimum (3 routes per tier) so the test does not need updating
    when new routes are added.  The precise coverage check is in TG-41.
    """
    actual_count = len(ROUTE_TIER_TABLE)
    assert actual_count > 0, "ROUTE_TIER_TABLE is empty"

    # All 4 tier levels must be represented
    tiers_present = set(ROUTE_TIER_TABLE.values())
    assert 1 in tiers_present, "No LITE routes in ROUTE_TIER_TABLE"
    assert 2 in tiers_present, "No STANDARD routes in ROUTE_TIER_TABLE"
    assert 3 in tiers_present, "No PROFESSIONAL routes in ROUTE_TIER_TABLE"
    assert 4 in tiers_present, "No ENTERPRISE routes in ROUTE_TIER_TABLE"

    # Sanity floor: at least 3 entries per tier avoids accidental wipeout
    min_expected = len(tiers_present) * 3
    assert actual_count >= min_expected, (
        f"ROUTE_TIER_TABLE only has {actual_count} entries — "
        f"expected at least {min_expected} (3 per tier minimum). "
        f"See TG-41 for full CI route-coverage check."
    )


# ---------------------------------------------------------------------------
# TG-28..29: STANDARD tier
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_tg_28_codegen_requires_standard():
    """TG-28: /api/v1/codegen requires STANDARD tier."""
    # LITE blocked
    status, body = await _call_middleware("/api/v1/codegen/generate", user_tier="LITE")
    assert status == 402
    assert body["required_tier"] == "STANDARD"
    # STANDARD passes
    status, _ = await _call_middleware("/api/v1/codegen/sessions", user_tier="STANDARD")
    assert status == 200


@pytest.mark.asyncio
async def test_tg_29_council_requires_standard():
    """TG-29: /api/v1/council requires STANDARD tier."""
    # LITE blocked
    status, body = await _call_middleware("/api/v1/council/decompose", user_tier="LITE")
    assert status == 402
    assert body["required_tier"] == "STANDARD"


# ---------------------------------------------------------------------------
# TG-30..34: State resolution and response format
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_tg_30_reads_user_tier_from_scope_state():
    """TG-30: TierGateMiddleware reads user_tier from scope["state"]."""
    # Inject user_tier directly into scope["state"]
    middleware = TierGateMiddleware(_dummy_app)

    # Test that PROFESSIONAL in scope["state"] allows agent-team
    scope = _make_scope("/api/v1/agent-team/messages", user_tier="PROFESSIONAL")
    assert scope["state"]["user_tier"] == "PROFESSIONAL"

    received_status: list[int] = []

    async def _send(message):
        if message["type"] == "http.response.start":
            received_status.append(message["status"])

    async def _receive():
        return {"type": "http.disconnect"}

    await middleware(scope, _receive, _send)
    assert received_status == [200]


@pytest.mark.asyncio
async def test_tg_31_lite_on_standard_route_message_mentions_standard():
    """TG-31: LITE user on STANDARD route gets message about STANDARD upgrade."""
    _, body = await _call_middleware("/api/v1/codegen/generate", user_tier="LITE")
    assert "STANDARD" in body.get("message", "") or body["required_tier"] == "STANDARD"


@pytest.mark.asyncio
async def test_tg_32_lite_on_enterprise_route_message_mentions_enterprise():
    """TG-32: LITE user on ENTERPRISE route gets message about ENTERPRISE upgrade."""
    _, body = await _call_middleware("/api/v1/enterprise/sso/configure", user_tier="LITE")
    assert "ENTERPRISE" in body.get("message", "") or body["required_tier"] == "ENTERPRISE"


@pytest.mark.asyncio
async def test_tg_33_402_response_is_json():
    """TG-33: 402 response is JSON (Content-Type: application/json)."""
    middleware = TierGateMiddleware(_dummy_app)
    scope = _make_scope("/api/v1/agent-team/messages", user_tier="LITE")

    response_headers: dict[bytes, bytes] = {}

    async def _send(message):
        if message["type"] == "http.response.start":
            for k, v in message.get("headers", []):
                response_headers[k.lower()] = v

    async def _receive():
        return {"type": "http.disconnect"}

    await middleware(scope, _receive, _send)

    content_type = response_headers.get(b"content-type", b"")
    assert b"application/json" in content_type


@pytest.mark.asyncio
async def test_tg_34_missing_scope_state_defaults_to_lite():
    """TG-34: TierGateMiddleware handles scope without state gracefully (defaults to LITE)."""
    middleware = TierGateMiddleware(_dummy_app)
    # scope with NO state key
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/api/v1/agent-team/messages",
        "query_string": b"",
        "headers": [],
        "client": ("127.0.0.1", 0),
        # No "state" key
    }

    received_status: list[int] = []
    received_body: list[bytes] = []

    async def _send(message):
        if message["type"] == "http.response.start":
            received_status.append(message["status"])
        elif message["type"] == "http.response.body":
            received_body.append(message.get("body", b""))

    async def _receive():
        return {"type": "http.disconnect"}

    await middleware(scope, _receive, _send)
    # No state → defaults to LITE → LITE can't access PROFESSIONAL route → 402
    assert received_status == [402]


# ---------------------------------------------------------------------------
# TG-35..37: ENTERPRISE sub-routes
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_tg_35_enterprise_compliance_requires_enterprise():
    """TG-35: /api/v1/enterprise/compliance requires ENTERPRISE."""
    status, body = await _call_middleware("/api/v1/enterprise/compliance/soc2", user_tier="PROFESSIONAL")
    assert status == 402
    assert body["required_tier"] == "ENTERPRISE"


@pytest.mark.asyncio
async def test_tg_36_enterprise_audit_requires_enterprise():
    """TG-36: /api/v1/enterprise/audit requires ENTERPRISE."""
    status, body = await _call_middleware("/api/v1/enterprise/audit/logs", user_tier="PROFESSIONAL")
    assert status == 402
    assert body["required_tier"] == "ENTERPRISE"


@pytest.mark.asyncio
async def test_tg_37_data_residency_requires_enterprise():
    """TG-37: /api/v1/data-residency requires ENTERPRISE."""
    status, body = await _call_middleware("/api/v1/data-residency/eu/config", user_tier="PROFESSIONAL")
    assert status == 402
    assert body["required_tier"] == "ENTERPRISE"


# ---------------------------------------------------------------------------
# TG-38..40: Edge cases
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_tg_38_templates_is_lite():
    """TG-38: /api/v1/templates is LITE (free, public endpoint — Sprint 181)."""
    status, _ = await _call_middleware("/api/v1/templates/sdlc-6.1.0", user_tier="LITE")
    assert status == 200
    # Also accessible without any tier set
    status, _ = await _call_middleware("/api/v1/templates", user_tier=None)
    assert status == 200


@pytest.mark.asyncio
async def test_tg_39_legacy_tier_names_supported():
    """TG-39: Legacy effective_tier values ('free', 'pro', 'enterprise') are mapped correctly."""
    # 'free' (legacy) → LITE (1): blocked on STANDARD routes
    status, body = await _call_middleware("/api/v1/teams", user_tier="free")
    assert status == 402

    # 'pro' (legacy) → PROFESSIONAL (3): allowed on PROFESSIONAL routes
    status, _ = await _call_middleware("/api/v1/agent-team/conversations", user_tier="pro")
    assert status == 200

    # 'enterprise' (legacy) → ENTERPRISE (4): allowed everywhere
    status, _ = await _call_middleware("/api/v1/enterprise/sso/configure", user_tier="enterprise")
    assert status == 200


@pytest.mark.asyncio
async def test_tg_40_tier_gate_performance_1000_requests():
    """TG-40: TierGateMiddleware performance test: 1000 req baseline (<500ms total)."""
    middleware = TierGateMiddleware(_dummy_app)

    # Mix of paths and tiers
    test_cases = [
        ("/api/v1/auth/login", "LITE"),
        ("/api/v1/agent-team/messages", "PROFESSIONAL"),
        ("/api/v1/enterprise/sso/configure", "ENTERPRISE"),
        ("/api/v1/codegen/generate", "STANDARD"),
        ("/api/v1/nist/govern/policies", "ENTERPRISE"),
    ] * 200  # 1000 total

    start = time.perf_counter()
    for path, tier in test_cases:
        scope = _make_scope(path, user_tier=tier)

        async def _noop_send(msg):
            pass

        async def _noop_receive():
            return {"type": "http.disconnect"}

        await middleware(scope, _noop_receive, _noop_send)

    elapsed_ms = (time.perf_counter() - start) * 1000
    # 1000 requests should complete in < 500ms (Python overhead)
    assert elapsed_ms < 500, f"1000 requests took {elapsed_ms:.2f}ms (expected <500ms)"


# ---------------------------------------------------------------------------
# Additional constant verification tests
# ---------------------------------------------------------------------------

def test_tier_names_constant():
    """Verify TIER_NAMES maps 1..4 correctly."""
    assert TIER_NAMES[1] == "LITE"
    assert TIER_NAMES[2] == "STANDARD"
    assert TIER_NAMES[3] == "PROFESSIONAL"
    assert TIER_NAMES[4] == "ENTERPRISE"


def test_tier_values_canonical_names():
    """Verify TIER_VALUES maps canonical names correctly."""
    assert TIER_VALUES["LITE"] == 1
    assert TIER_VALUES["STANDARD"] == 2
    assert TIER_VALUES["PROFESSIONAL"] == 3
    assert TIER_VALUES["ENTERPRISE"] == 4


def test_tier_values_legacy_names():
    """Verify TIER_VALUES maps legacy effective_tier names correctly."""
    assert TIER_VALUES["free"] == 1
    assert TIER_VALUES["starter"] == 2
    assert TIER_VALUES["founder"] == 2
    assert TIER_VALUES["pro"] == 3
    assert TIER_VALUES["enterprise"] == 4


# ---------------------------------------------------------------------------
# TG-41: CI route coverage check (CTO Sprint 185 action item #2)
# ---------------------------------------------------------------------------

def test_tg_41_all_fastapi_routes_in_tier_table():
    """TG-41 (CI coverage): every FastAPI route prefix registered in main.py
    must appear in ROUTE_TIER_TABLE.

    Fails fast when a developer adds a new router in main.py without adding a
    corresponding entry in tier_gate.ROUTE_TIER_TABLE.  This is the mandatory
    gate that prevents ungated routes from reaching production
    (CTO Sprint 185 action item #2).

    FastAPI meta-routes (/openapi.json, /redoc, /docs, /favicon.ico) are
    excluded because TierGateMiddleware already has a pass-through for paths
    that do not start with /api/v1/.
    """
    from app.main import app  # pragma: no cover

    # Collect all /api/v1/<module> prefixes from registered FastAPI routes
    registered_prefixes: set[str] = set()
    for route in app.routes:
        path: str = getattr(route, "path", "") or ""
        # Match any path of the form /api/v1/<module>/...
        stripped = path.lstrip("/")
        parts = stripped.split("/")
        if len(parts) >= 3 and parts[0] == "api" and parts[1] == "v1" and parts[2]:
            registered_prefixes.add(f"/api/v1/{parts[2]}")

    # Every registered prefix must have a tier entry
    ungated = registered_prefixes - set(ROUTE_TIER_TABLE.keys())
    assert not ungated, (
        f"Found {len(ungated)} FastAPI route prefix(es) NOT in ROUTE_TIER_TABLE.\n"
        f"Add the following to backend/app/middleware/tier_gate.py ROUTE_TIER_TABLE "
        f"before Sprint 186 (CTO mandatory, Sprint 185 review):\n"
        + "\n".join(f'    "{p}": <tier>,  # TODO: set correct tier' for p in sorted(ungated))
    )
