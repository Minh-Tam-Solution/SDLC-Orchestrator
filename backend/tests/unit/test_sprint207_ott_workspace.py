"""
Unit Tests — Sprint 207: OTT Workspace Context Management

Covers workspace_service.py (Track A), governance dispatch (Track C),
and ai_response_handler workspace intercept.

FR-049, ADR-067: 15 test cases.
"""

import pytest
from dataclasses import dataclass
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4


# ─────────────────────────────────────────────────────────────────────────────
# D-01: workspace_service — WorkspaceContext + helpers
# ─────────────────────────────────────────────────────────────────────────────


def test_workspace_context_frozen():
    """WorkspaceContext is a frozen dataclass (D-067-02)."""
    from app.services.agent_bridge.workspace_service import WorkspaceContext

    ws = WorkspaceContext(
        project_id="abc-123",
        project_name="BFlow",
        tier="STANDARD",
        sdlc_stage="BUILD",
        set_at="2026-02-26T00:00:00Z",
        set_by="user-1",
    )
    assert ws.project_id == "abc-123"
    assert ws.project_name == "BFlow"
    with pytest.raises(AttributeError):
        ws.project_name = "Other"  # type: ignore[misc]


def test_is_uuid_valid():
    """is_uuid() accepts valid UUID strings."""
    from app.services.agent_bridge.workspace_service import is_uuid

    assert is_uuid(str(uuid4())) is True
    assert is_uuid("  " + str(uuid4()) + "  ") is True


def test_is_uuid_invalid():
    """is_uuid() rejects non-UUID strings."""
    from app.services.agent_bridge.workspace_service import is_uuid

    assert is_uuid("not-a-uuid") is False
    assert is_uuid("BFlow Platform") is False
    assert is_uuid("") is False


# ─────────────────────────────────────────────────────────────────────────────
# D-02: get_workspace — Redis HGETALL
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_workspace_returns_context():
    """get_workspace returns WorkspaceContext when Redis has data."""
    from app.services.agent_bridge.workspace_service import get_workspace

    mock_redis = AsyncMock()
    mock_redis.hgetall = AsyncMock(return_value={
        "project_id": str(uuid4()),
        "project_name": "BFlow",
        "tier": "STANDARD",
        "sdlc_stage": "BUILD",
        "set_at": "2026-02-26T00:00:00Z",
        "set_by": "user-1",
    })

    result = await get_workspace("telegram", "12345", mock_redis)
    assert result is not None
    assert result.project_name == "BFlow"
    assert result.tier == "STANDARD"


@pytest.mark.asyncio
async def test_get_workspace_returns_none_on_empty():
    """get_workspace returns None when no binding exists."""
    from app.services.agent_bridge.workspace_service import get_workspace

    mock_redis = AsyncMock()
    mock_redis.hgetall = AsyncMock(return_value={})

    result = await get_workspace("telegram", "12345", mock_redis)
    assert result is None


@pytest.mark.asyncio
async def test_get_workspace_returns_none_on_redis_error():
    """get_workspace returns None on Redis error (graceful degradation D-067-01)."""
    from app.services.agent_bridge.workspace_service import get_workspace

    mock_redis = AsyncMock()
    mock_redis.hgetall = AsyncMock(side_effect=ConnectionError("redis down"))

    result = await get_workspace("telegram", "12345", mock_redis)
    assert result is None


# ─────────────────────────────────────────────────────────────────────────────
# D-03: set_workspace — Redis HSET + TTL
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_set_workspace_stores_hash():
    """set_workspace writes Redis HASH with TTL (D-067-02)."""
    from app.services.agent_bridge.workspace_service import set_workspace

    mock_redis = AsyncMock()
    mock_redis.hset = AsyncMock()
    mock_redis.expire = AsyncMock()

    await set_workspace(
        "telegram", "12345",
        "proj-uuid", "BFlow", "STANDARD", "BUILD",
        "user-1", mock_redis,
    )

    mock_redis.hset.assert_called_once()
    call_args = mock_redis.hset.call_args
    assert call_args.kwargs["mapping"]["project_name"] == "BFlow"
    mock_redis.expire.assert_called_once()
    # TTL should be 7 days
    assert mock_redis.expire.call_args[0][1] == 604_800


# ─────────────────────────────────────────────────────────────────────────────
# D-04: clear_workspace
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_clear_workspace_deletes_key():
    """clear_workspace deletes the Redis key."""
    from app.services.agent_bridge.workspace_service import clear_workspace

    mock_redis = AsyncMock()
    mock_redis.delete = AsyncMock()

    await clear_workspace("telegram", "12345", mock_redis)
    mock_redis.delete.assert_called_once()


# ─────────────────────────────────────────────────────────────────────────────
# D-05: resolve_project_id — 4-level priority chain (D-067-04)
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_resolve_project_id_explicit_wins():
    """Priority 1: explicit project_id takes precedence over workspace."""
    from app.services.agent_bridge.workspace_service import resolve_project_id

    mock_redis = AsyncMock()
    resolved_id, ws_used = await resolve_project_id(
        explicit_id="explicit-uuid",
        channel="telegram",
        chat_id="12345",
        redis=mock_redis,
    )
    assert resolved_id == "explicit-uuid"
    assert ws_used is False
    # Redis should NOT be consulted when explicit_id is given
    mock_redis.hgetall.assert_not_called()


@pytest.mark.asyncio
async def test_resolve_project_id_workspace_fallback():
    """Priority 2: workspace project_id used when no explicit_id."""
    from app.services.agent_bridge.workspace_service import resolve_project_id

    ws_project_id = str(uuid4())
    mock_redis = AsyncMock()
    mock_redis.hgetall = AsyncMock(return_value={
        "project_id": ws_project_id,
        "project_name": "BFlow",
        "tier": "STANDARD",
        "sdlc_stage": "BUILD",
        "set_at": "2026-02-26T00:00:00Z",
        "set_by": "user-1",
    })

    resolved_id, ws_used = await resolve_project_id(
        explicit_id=None,
        channel="telegram",
        chat_id="12345",
        redis=mock_redis,
    )
    assert resolved_id == ws_project_id
    assert ws_used is True


@pytest.mark.asyncio
async def test_resolve_project_id_env_var_fallback():
    """Priority 3: OTT_DEFAULT_PROJECT_ID env var when no workspace."""
    from app.services.agent_bridge.workspace_service import resolve_project_id

    mock_redis = AsyncMock()
    mock_redis.hgetall = AsyncMock(return_value={})

    with patch.dict("os.environ", {"OTT_DEFAULT_PROJECT_ID": "default-uuid"}):
        resolved_id, ws_used = await resolve_project_id(
            explicit_id=None,
            channel="telegram",
            chat_id="12345",
            redis=mock_redis,
        )
    assert resolved_id == "default-uuid"
    assert ws_used is False


@pytest.mark.asyncio
async def test_resolve_project_id_none_when_all_fail():
    """Priority 4: returns (None, False) when all sources empty."""
    from app.services.agent_bridge.workspace_service import resolve_project_id

    mock_redis = AsyncMock()
    mock_redis.hgetall = AsyncMock(return_value={})

    with patch.dict("os.environ", {"OTT_DEFAULT_PROJECT_ID": ""}):
        resolved_id, ws_used = await resolve_project_id(
            explicit_id=None,
            channel="telegram",
            chat_id="12345",
            redis=mock_redis,
        )
    assert resolved_id is None
    assert ws_used is False


# ─────────────────────────────────────────────────────────────────────────────
# D-06: touch_workspace_ttl — non-critical
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_touch_workspace_ttl_resets_expiry():
    """touch_workspace_ttl calls expire with 7-day TTL."""
    from app.services.agent_bridge.workspace_service import touch_workspace_ttl

    mock_redis = AsyncMock()
    mock_redis.expire = AsyncMock()

    await touch_workspace_ttl("telegram", "12345", mock_redis)
    mock_redis.expire.assert_called_once()
    assert mock_redis.expire.call_args[0][1] == 604_800


@pytest.mark.asyncio
async def test_touch_workspace_ttl_swallows_error():
    """touch_workspace_ttl logs but doesn't raise on Redis failure."""
    from app.services.agent_bridge.workspace_service import touch_workspace_ttl

    mock_redis = AsyncMock()
    mock_redis.expire = AsyncMock(side_effect=ConnectionError("redis down"))

    # Should not raise
    await touch_workspace_ttl("telegram", "12345", mock_redis)


# ─────────────────────────────────────────────────────────────────────────────
# D-07: Telegram static replies — workspace commands in _COMMAND_REPLIES
# ─────────────────────────────────────────────────────────────────────────────


def test_telegram_responder_workspace_commands():
    """telegram_responder has all 4 workspace slash commands."""
    from app.services.agent_bridge.telegram_responder import _COMMAND_REPLIES

    for cmd in ("/workspace", "/workspace_set", "/workspace_list", "/workspace_clear"):
        assert cmd in _COMMAND_REPLIES, f"Missing {cmd} in _COMMAND_REPLIES"
        assert "Workspace" in _COMMAND_REPLIES[cmd]
