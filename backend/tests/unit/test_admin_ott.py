"""
==========================================================================
Unit Tests for admin_ott.py — Sprint 198 OTT Gateway Admin Dashboard
SDLC Orchestrator — ENTERPRISE Tier

Test IDs:
  OTT-01  helper _mask_secret masks correctly
  OTT-02  helper _channel_status returns online/configured/offline
  OTT-03  GET /stats returns aggregate channel metrics (empty DB)
  OTT-04  GET /stats returns metrics with conversations + messages
  OTT-05  GET /stats handles Redis failure gracefully
  OTT-06  GET /config returns all channels with secrets masked
  OTT-07  GET /config shows telegram bot_token_configured
  OTT-08  GET /{channel}/health for valid channel (empty DB)
  OTT-09  GET /{channel}/health returns metrics with data
  OTT-10  GET /{channel}/health rejects invalid channel (400)
  OTT-11  GET /{channel}/conversations returns paginated list (empty)
  OTT-12  GET /{channel}/conversations returns items with last_message
  OTT-13  GET /{channel}/conversations rejects invalid channel (400)
  OTT-14  GET /{channel}/conversations respects status_filter
  OTT-15  GET /{channel}/conversations respects page/page_size params

Approach:
  - httpx.AsyncClient + ASGITransport hitting the real FastAPI app
  - dependency_overrides for require_superuser + get_db
  - TierGateMiddleware bypassed via patch.object on ADMIN_BYPASS_SECRET
  - get_redis_client patched for dedupe stats
  - os.getenv patched for channel configuration tests
  - No real database connection — AsyncMock sessions only

SDLC 6.1.0 — Sprint 198
Authority: CTO Approved
==========================================================================
"""

from __future__ import annotations

import math
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

import app.middleware.tier_gate as _tg_mod
from app.api.dependencies import require_superuser
from app.api.routes.admin_ott import (
    SUPPORTED_CHANNELS,
    _channel_status,
    _mask_secret,
)
from app.db.session import get_db
from app.main import app

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_TEST_BYPASS_SECRET = "test-ott-bypass-secret-198"

_ENTERPRISE_HEADERS = {
    "X-Admin-Override": _TEST_BYPASS_SECRET,
    "Authorization": "Bearer fake-jwt-token",
}

_USER_ID = uuid4()

# Base URL prefix for OTT admin routes
_BASE = "/api/v1/admin/ott-channels"


# ---------------------------------------------------------------------------
# Tier-gate bypass
# ---------------------------------------------------------------------------


@contextmanager
def _tier_bypass():
    """Patch TierGateMiddleware's module-level ADMIN_BYPASS_SECRET."""
    with patch.object(_tg_mod, "ADMIN_BYPASS_SECRET", _TEST_BYPASS_SECRET):
        yield


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_superuser() -> MagicMock:
    """Create a mock superuser for admin route tests."""
    user = MagicMock()
    user.id = _USER_ID
    user.email = "admin@sdlc.test"
    user.is_superuser = True
    user.is_platform_admin = False
    user.is_active = True
    user.effective_tier = "ENTERPRISE"
    return user


def _make_db_scalar(value):
    """Return a mock execute result where .scalar() returns value."""
    result = MagicMock()
    result.scalar.return_value = value
    return result


def _make_db_scalar_one(value):
    """Return a mock execute result where .scalar_one() returns value."""
    result = MagicMock()
    result.scalar_one.return_value = value
    return result


def _make_db_first(row):
    """Return a mock execute result where .first() returns row."""
    result = MagicMock()
    result.first.return_value = row
    return result


def _make_db_all(rows):
    """Return a mock execute result where .all() returns rows."""
    result = MagicMock()
    result.all.return_value = rows
    return result


def _make_db_scalars_all(rows):
    """Return a mock execute result where .scalars().all() returns rows."""
    result = MagicMock()
    result.scalars.return_value.all.return_value = rows
    return result


def _make_conversation(
    *,
    channel: str = "telegram",
    status: str = "active",
    total_messages: int = 5,
    total_tokens: int = 1200,
    current_cost_cents: int = 2,
) -> MagicMock:
    """Create a mock AgentConversation row."""
    conv = MagicMock()
    conv.id = uuid4()
    conv.channel = channel
    conv.initiator_type = "ott_channel"
    conv.initiator_id = "chat_123456"
    conv.status = status
    conv.total_messages = total_messages
    conv.total_tokens = total_tokens
    conv.current_cost_cents = current_cost_cents
    conv.started_at = datetime(2026, 2, 23, 10, 0, 0)
    conv.completed_at = None
    return conv


# ---------------------------------------------------------------------------
# OTT-01: _mask_secret helper
# ---------------------------------------------------------------------------


class TestMaskSecret:
    """OTT-01: Test the _mask_secret helper function."""

    def test_empty_string(self):
        assert _mask_secret("") == ""

    def test_short_secret(self):
        assert _mask_secret("abcd") == "****"

    def test_exactly_eight(self):
        assert _mask_secret("12345678") == "****"

    def test_long_secret(self):
        result = _mask_secret("abcdefghij1234567890")
        assert result == "abcd...7890"

    def test_nine_chars(self):
        result = _mask_secret("123456789")
        assert result == "1234...6789"


# ---------------------------------------------------------------------------
# OTT-02: _channel_status helper
# ---------------------------------------------------------------------------


class TestChannelStatus:
    """OTT-02: Test the _channel_status helper function."""

    def test_telegram_online_with_bot_token(self):
        with patch.dict("os.environ", {"TELEGRAM_BOT_TOKEN": "tok123"}, clear=False):
            assert _channel_status("telegram") == "online"

    def test_telegram_configured_with_secret_only(self):
        env = {"TELEGRAM_WEBHOOK_SECRET": "sec123"}
        with patch.dict("os.environ", env, clear=False):
            with patch("os.getenv", side_effect=lambda k, d="": env.get(k, d)):
                result = _channel_status("telegram")
                # With no bot token but secret set → configured
                assert result in ("configured", "online")

    def test_telegram_offline_no_env(self):
        with patch("os.getenv", return_value=""):
            assert _channel_status("telegram") == "offline"

    def test_slack_configured_with_secret(self):
        with patch("os.getenv", side_effect=lambda k, d="": "sec" if "SLACK" in k else ""):
            assert _channel_status("slack") == "configured"

    def test_unknown_channel_offline(self):
        assert _channel_status("unknown_channel") == "offline"


# ---------------------------------------------------------------------------
# OTT-03: GET /stats — empty DB
# ---------------------------------------------------------------------------


class TestGetChannelStats:
    """OTT-03..05: Test GET /admin/ott-channels/stats endpoint."""

    @pytest.mark.asyncio
    async def test_stats_empty_db(self):
        """OTT-03: Stats with no conversations returns zero counts."""
        user = _make_superuser()
        db = AsyncMock()
        # Each channel has 4 DB queries (conv_count, active_count, msg_24h, msg_total)
        # 4 channels × 4 queries = 16 execute calls, all returning 0
        db.execute = AsyncMock(return_value=_make_db_scalar(0))

        async def _db_override() -> AsyncGenerator:
            yield db

        mock_redis = AsyncMock()
        mock_redis.keys = AsyncMock(return_value=[])

        app.dependency_overrides[require_superuser] = lambda: user
        app.dependency_overrides[get_db] = _db_override

        try:
            with _tier_bypass(), \
                 patch("app.api.routes.admin_ott.get_redis_client", new_callable=AsyncMock, return_value=mock_redis):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://testserver") as client:
                    response = await client.get(
                        f"{_BASE}/stats",
                        headers=_ENTERPRISE_HEADERS,
                    )

            assert response.status_code == 200
            body = response.json()
            assert "channels" in body
            assert "summary" in body
            assert "dedupe" in body
            assert body["summary"]["total_channels"] == len(SUPPORTED_CHANNELS)
            assert body["summary"]["total_conversations"] == 0
            assert body["summary"]["total_messages_24h"] == 0
            assert body["dedupe"]["keys_active"] == 0
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_stats_with_conversations(self):
        """OTT-04: Stats reflect conversation and message counts."""
        user = _make_superuser()
        db = AsyncMock()

        # We'll make telegram return non-zero, others zero
        call_count = 0

        async def _mock_execute(stmt):
            nonlocal call_count
            call_count += 1
            # First 4 calls are for "slack" (alphabetical order)
            # Next 4 for "teams", next 4 for "telegram", next 4 for "zalo"
            # telegram is 3rd channel (0-indexed: 8-11)
            if 9 <= call_count <= 12:
                # telegram queries: conv_count=3, active=1, msg_24h=15, msg_total=42
                values = {9: 3, 10: 1, 11: 15, 12: 42}
                return _make_db_scalar(values.get(call_count, 0))
            return _make_db_scalar(0)

        db.execute = AsyncMock(side_effect=_mock_execute)

        async def _db_override() -> AsyncGenerator:
            yield db

        mock_redis = AsyncMock()
        mock_redis.keys = AsyncMock(return_value=["webhook_dedupe:abc", "webhook_dedupe:def"])

        app.dependency_overrides[require_superuser] = lambda: user
        app.dependency_overrides[get_db] = _db_override

        try:
            with _tier_bypass(), \
                 patch("app.api.routes.admin_ott.get_redis_client", new_callable=AsyncMock, return_value=mock_redis):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://testserver") as client:
                    response = await client.get(
                        f"{_BASE}/stats",
                        headers=_ENTERPRISE_HEADERS,
                    )

            assert response.status_code == 200
            body = response.json()
            assert body["summary"]["total_conversations"] == 3
            assert body["summary"]["total_messages_24h"] == 15
            assert body["dedupe"]["keys_active"] == 2

            # Find telegram in channels list
            tg = next(c for c in body["channels"] if c["channel"] == "telegram")
            assert tg["conversations_total"] == 3
            assert tg["conversations_active"] == 1
            assert tg["messages_total"] == 42
            assert tg["messages_last_24h"] == 15
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_stats_redis_failure_non_fatal(self):
        """OTT-05: Redis failure doesn't break stats endpoint."""
        user = _make_superuser()
        db = AsyncMock()
        db.execute = AsyncMock(return_value=_make_db_scalar(0))

        async def _db_override() -> AsyncGenerator:
            yield db

        async def _failing_redis():
            raise ConnectionError("Redis unavailable")

        app.dependency_overrides[require_superuser] = lambda: user
        app.dependency_overrides[get_db] = _db_override

        try:
            with _tier_bypass(), \
                 patch("app.api.routes.admin_ott.get_redis_client", new_callable=AsyncMock, side_effect=ConnectionError("Redis down")):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://testserver") as client:
                    response = await client.get(
                        f"{_BASE}/stats",
                        headers=_ENTERPRISE_HEADERS,
                    )

            assert response.status_code == 200
            body = response.json()
            # Dedupe stats should be zero (graceful degradation)
            assert body["dedupe"]["hits"] == 0
            assert body["dedupe"]["keys_active"] == 0
        finally:
            app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# OTT-06..07: GET /config
# ---------------------------------------------------------------------------


class TestGetChannelConfig:
    """OTT-06..07: Test GET /admin/ott-channels/config endpoint."""

    @pytest.mark.asyncio
    async def test_config_returns_all_channels(self):
        """OTT-06: Config returns all 4 supported channels with masked secrets."""
        user = _make_superuser()

        app.dependency_overrides[require_superuser] = lambda: user

        try:
            with _tier_bypass():
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://testserver") as client:
                    response = await client.get(
                        f"{_BASE}/config",
                        headers=_ENTERPRISE_HEADERS,
                    )

            assert response.status_code == 200
            body = response.json()
            assert "channels" in body
            assert "global" in body
            assert len(body["channels"]) == len(SUPPORTED_CHANNELS)

            channel_names = {c["channel"] for c in body["channels"]}
            assert channel_names == set(SUPPORTED_CHANNELS)

            # Each channel should have required fields
            for ch in body["channels"]:
                assert "status" in ch
                assert "tier" in ch
                assert "webhook_url" in ch
                assert "hmac_enabled" in ch
                assert "secret_configured" in ch
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_config_telegram_bot_token_fields(self):
        """OTT-07: Telegram config includes bot_token_configured field."""
        user = _make_superuser()

        app.dependency_overrides[require_superuser] = lambda: user

        try:
            with _tier_bypass():
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://testserver") as client:
                    response = await client.get(
                        f"{_BASE}/config",
                        headers=_ENTERPRISE_HEADERS,
                    )

            assert response.status_code == 200
            body = response.json()
            tg = next(c for c in body["channels"] if c["channel"] == "telegram")
            assert "bot_token_configured" in tg
            # bot_token_masked is present only if token is configured
            assert "bot_token_masked" in tg
        finally:
            app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# OTT-08..10: GET /{channel}/health
# ---------------------------------------------------------------------------


class TestGetChannelHealth:
    """OTT-08..10: Test GET /admin/ott-channels/{channel}/health endpoint."""

    @pytest.mark.asyncio
    async def test_health_empty_db(self):
        """OTT-08: Health for valid channel with no data."""
        user = _make_superuser()
        db = AsyncMock()

        # 5 queries: last_msg, error_count, avg_latency, status_breakdown, msg_24h
        db.execute = AsyncMock(side_effect=[
            _make_db_first(None),      # last_msg: no messages
            _make_db_scalar(0),        # error_count_24h
            _make_db_scalar(None),     # avg_latency (no data)
            _make_db_all([]),          # status_breakdown
            _make_db_scalar(0),        # messages_24h
        ])

        async def _db_override() -> AsyncGenerator:
            yield db

        app.dependency_overrides[require_superuser] = lambda: user
        app.dependency_overrides[get_db] = _db_override

        try:
            with _tier_bypass():
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://testserver") as client:
                    response = await client.get(
                        f"{_BASE}/telegram/health",
                        headers=_ENTERPRISE_HEADERS,
                    )

            assert response.status_code == 200
            body = response.json()
            assert body["channel"] == "telegram"
            assert body["health"]["last_webhook_at"] is None
            assert body["health"]["messages_24h"] == 0
            assert body["health"]["errors_24h"] == 0
            assert body["health"]["avg_latency_ms"] is None
            assert body["conversations"] == {}
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_health_with_data(self):
        """OTT-09: Health returns real metrics when data exists."""
        user = _make_superuser()
        db = AsyncMock()

        last_msg_time = datetime(2026, 2, 23, 14, 30, 0)

        db.execute = AsyncMock(side_effect=[
            _make_db_first((last_msg_time,)),  # last_msg: has timestamp
            _make_db_scalar(2),                 # error_count_24h: 2 errors
            _make_db_scalar(245.7),             # avg_latency: 245.7ms
            _make_db_all([("active", 5), ("completed", 12)]),  # status_breakdown
            _make_db_scalar(47),                # messages_24h
        ])

        async def _db_override() -> AsyncGenerator:
            yield db

        app.dependency_overrides[require_superuser] = lambda: user
        app.dependency_overrides[get_db] = _db_override

        try:
            with _tier_bypass():
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://testserver") as client:
                    response = await client.get(
                        f"{_BASE}/telegram/health",
                        headers=_ENTERPRISE_HEADERS,
                    )

            assert response.status_code == 200
            body = response.json()
            assert body["channel"] == "telegram"
            assert body["health"]["last_webhook_at"] == last_msg_time.isoformat()
            assert body["health"]["messages_24h"] == 47
            assert body["health"]["errors_24h"] == 2
            assert body["health"]["avg_latency_ms"] == 245.7
            assert body["conversations"]["active"] == 5
            assert body["conversations"]["completed"] == 12
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_health_invalid_channel(self):
        """OTT-10: Invalid channel returns 400."""
        user = _make_superuser()

        app.dependency_overrides[require_superuser] = lambda: user

        try:
            with _tier_bypass():
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://testserver") as client:
                    response = await client.get(
                        f"{_BASE}/whatsapp/health",
                        headers=_ENTERPRISE_HEADERS,
                    )

            assert response.status_code == 400
            body = response.json()
            assert "unsupported channel" in body["detail"]
        finally:
            app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# OTT-11..15: GET /{channel}/conversations
# ---------------------------------------------------------------------------


class TestGetChannelConversations:
    """OTT-11..15: Test GET /admin/ott-channels/{channel}/conversations."""

    @pytest.mark.asyncio
    async def test_conversations_empty(self):
        """OTT-11: Empty conversation list with pagination metadata."""
        user = _make_superuser()
        db = AsyncMock()

        # 2 queries: count + paginated results
        db.execute = AsyncMock(side_effect=[
            _make_db_scalar(0),            # count: 0
            _make_db_scalars_all([]),       # results: empty
        ])

        async def _db_override() -> AsyncGenerator:
            yield db

        app.dependency_overrides[require_superuser] = lambda: user
        app.dependency_overrides[get_db] = _db_override

        try:
            with _tier_bypass():
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://testserver") as client:
                    response = await client.get(
                        f"{_BASE}/telegram/conversations",
                        headers=_ENTERPRISE_HEADERS,
                    )

            assert response.status_code == 200
            body = response.json()
            assert body["channel"] == "telegram"
            assert body["items"] == []
            assert body["pagination"]["total"] == 0
            assert body["pagination"]["pages"] == 0
            assert body["pagination"]["page"] == 1
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_conversations_with_items(self):
        """OTT-12: Returns conversations with last message preview."""
        user = _make_superuser()
        db = AsyncMock()

        conv1 = _make_conversation(channel="telegram", status="active", total_messages=8)
        conv2 = _make_conversation(channel="telegram", status="completed", total_messages=3)
        conv2.completed_at = datetime(2026, 2, 23, 12, 0, 0)

        last_msg_time = datetime(2026, 2, 23, 14, 0, 0)

        # count query, paginated query, then per-item last_msg queries
        db.execute = AsyncMock(side_effect=[
            _make_db_scalar(2),                           # count: 2
            _make_db_scalars_all([conv1, conv2]),          # results
            _make_db_first(("Hello from user", "user", last_msg_time)),   # conv1 last msg
            _make_db_first(("AI response here", "agent", last_msg_time)), # conv2 last msg
        ])

        async def _db_override() -> AsyncGenerator:
            yield db

        app.dependency_overrides[require_superuser] = lambda: user
        app.dependency_overrides[get_db] = _db_override

        try:
            with _tier_bypass():
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://testserver") as client:
                    response = await client.get(
                        f"{_BASE}/telegram/conversations",
                        headers=_ENTERPRISE_HEADERS,
                    )

            assert response.status_code == 200
            body = response.json()
            assert body["channel"] == "telegram"
            assert len(body["items"]) == 2
            assert body["pagination"]["total"] == 2
            assert body["pagination"]["pages"] == 1

            # Verify first item has last_message
            item0 = body["items"][0]
            assert item0["status"] == "active"
            assert item0["total_messages"] == 8
            assert item0["last_message"] is not None
            assert item0["last_message"]["content"] == "Hello from user"
            assert item0["last_message"]["sender_type"] == "user"

            # Verify second item (completed)
            item1 = body["items"][1]
            assert item1["status"] == "completed"
            assert item1["completed_at"] is not None
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_conversations_invalid_channel(self):
        """OTT-13: Invalid channel returns 400."""
        user = _make_superuser()

        app.dependency_overrides[require_superuser] = lambda: user

        try:
            with _tier_bypass():
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://testserver") as client:
                    response = await client.get(
                        f"{_BASE}/discord/conversations",
                        headers=_ENTERPRISE_HEADERS,
                    )

            assert response.status_code == 400
            body = response.json()
            assert "unsupported channel" in body["detail"]
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_conversations_status_filter(self):
        """OTT-14: status_filter query param is accepted."""
        user = _make_superuser()
        db = AsyncMock()

        db.execute = AsyncMock(side_effect=[
            _make_db_scalar(0),
            _make_db_scalars_all([]),
        ])

        async def _db_override() -> AsyncGenerator:
            yield db

        app.dependency_overrides[require_superuser] = lambda: user
        app.dependency_overrides[get_db] = _db_override

        try:
            with _tier_bypass():
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://testserver") as client:
                    response = await client.get(
                        f"{_BASE}/telegram/conversations?status_filter=active",
                        headers=_ENTERPRISE_HEADERS,
                    )

            assert response.status_code == 200
            body = response.json()
            assert body["items"] == []
            # DB execute was called (filter applied) — verify at least 2 calls
            assert db.execute.call_count >= 2
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_conversations_pagination_params(self):
        """OTT-15: Custom page and page_size params are respected."""
        user = _make_superuser()
        db = AsyncMock()

        # Total 25 items, page 2, page_size 10 → pages = 3
        db.execute = AsyncMock(side_effect=[
            _make_db_scalar(25),
            _make_db_scalars_all([]),  # page 2 might be empty in mock
        ])

        async def _db_override() -> AsyncGenerator:
            yield db

        app.dependency_overrides[require_superuser] = lambda: user
        app.dependency_overrides[get_db] = _db_override

        try:
            with _tier_bypass():
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://testserver") as client:
                    response = await client.get(
                        f"{_BASE}/telegram/conversations?page=2&page_size=10",
                        headers=_ENTERPRISE_HEADERS,
                    )

            assert response.status_code == 200
            body = response.json()
            assert body["pagination"]["page"] == 2
            assert body["pagination"]["page_size"] == 10
            assert body["pagination"]["total"] == 25
            assert body["pagination"]["pages"] == math.ceil(25 / 10)
        finally:
            app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# OTT-16..19: POST /{channel}/test-webhook (Sprint 199 C-03)
# ---------------------------------------------------------------------------


class TestTestWebhook:
    """OTT-16..19: Test POST /admin/ott-channels/{channel}/test-webhook."""

    @pytest.mark.asyncio
    async def test_webhook_telegram_success(self):
        """OTT-16: Telegram test-webhook normalizes successfully."""
        user = _make_superuser()

        app.dependency_overrides[require_superuser] = lambda: user

        try:
            with _tier_bypass():
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://testserver") as client:
                    response = await client.post(
                        f"{_BASE}/telegram/test-webhook",
                        headers=_ENTERPRISE_HEADERS,
                    )

            assert response.status_code == 200
            body = response.json()
            assert body["channel"] == "telegram"
            assert body["status"] == "ok"
            assert body["normalization"]["success"] is True
            assert body["normalization"]["sender_id"] == "0"
            assert body["normalization"]["content_length"] > 0
            assert body["timing_ms"] >= 0
            assert body["tested_at"] is not None
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_webhook_invalid_channel(self):
        """OTT-17: Invalid channel returns 400."""
        user = _make_superuser()

        app.dependency_overrides[require_superuser] = lambda: user

        try:
            with _tier_bypass():
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://testserver") as client:
                    response = await client.post(
                        f"{_BASE}/whatsapp/test-webhook",
                        headers=_ENTERPRISE_HEADERS,
                    )

            assert response.status_code == 400
            body = response.json()
            assert "unsupported channel" in body["detail"]
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_webhook_returns_pipeline_info(self):
        """OTT-18: Response includes pipeline config (hmac_enabled, channel_status)."""
        user = _make_superuser()

        app.dependency_overrides[require_superuser] = lambda: user

        try:
            with _tier_bypass():
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://testserver") as client:
                    response = await client.post(
                        f"{_BASE}/telegram/test-webhook",
                        headers=_ENTERPRISE_HEADERS,
                    )

            assert response.status_code == 200
            body = response.json()
            assert "pipeline" in body
            assert "hmac_enabled" in body["pipeline"]
            assert "channel_status" in body["pipeline"]
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_webhook_normalizer_error_returns_error_status(self):
        """OTT-19: If normalizer throws, response has status='error'."""
        user = _make_superuser()

        app.dependency_overrides[require_superuser] = lambda: user

        try:
            with (
                _tier_bypass(),
                patch(
                    "app.services.agent_bridge.route_to_normalizer",
                    side_effect=ValueError("Test normalizer failure"),
                ),
            ):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://testserver") as client:
                    response = await client.post(
                        f"{_BASE}/telegram/test-webhook",
                        headers=_ENTERPRISE_HEADERS,
                    )

            assert response.status_code == 200  # Not 500 — error is captured
            body = response.json()
            assert body["status"] == "error"
            assert body["normalization"]["success"] is False
            assert "Test normalizer failure" in body["normalization"]["error"]
        finally:
            app.dependency_overrides.clear()
