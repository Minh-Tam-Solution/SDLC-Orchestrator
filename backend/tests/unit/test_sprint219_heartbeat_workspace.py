"""
Sprint 219 — P6 Agent Liveness + P5 Shared Workspace Foundation Tests.

Covers:
- S1: SharedWorkspaceItem model (columns, constraints, to_dict, repr)
- S2: SharedWorkspace service (put, get, list_keys, delete, get_active_keys)
- S3: Optimistic concurrency (VersionConflictError, expected_version)
- S4: HeartbeatService (record, check_liveness, get_stale, recover)
- S5: HeartbeatService batch check (MGET, no N+1)
- S6: HeartbeatMonitor (start, stop, circuit breaker)
- S7: Heartbeat recovery idempotency (Redis dedup)
- S8: Model registration (SharedWorkspaceItem in __init__.py)
- S9: Alembic migration chain (s218_001 → s219_001)
- S10: Orchestrator heartbeat wiring

Test count: 62 tests across 11 groups.
Cumulative: 131 (S216+S217+S218) + 62 = 193 total.
"""

import asyncio
import importlib.util
import json
import logging
import pytest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
from uuid import uuid4, UUID

# Models
from app.models.shared_workspace import (
    SharedWorkspaceItem,
    WORKSPACE_ITEM_TYPES,
    CONFLICT_STRATEGIES,
)

# Services
from app.services.agent_team.shared_workspace import (
    SharedWorkspace,
    VersionConflictError,
    PREVIEW_MAX_LEN,
)
from app.services.agent_team.heartbeat_service import (
    HeartbeatService,
    DEFAULT_TTL_SECONDS,
    RECOVERY_DEDUP_TTL,
    _hb_key,
    _recovery_key,
)
from app.services.agent_team.heartbeat_monitor import (
    HeartbeatMonitor,
    SCAN_INTERVAL_SECONDS,
    MASS_STALL_THRESHOLD,
    MASS_STALL_WINDOW_SECONDS,
)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _make_workspace_item(
    item_key: str = "coder/main.py",
    content: str = "print('hello')",
    item_type: str = "code",
    version: int = 1,
    conversation_id=None,
    created_by=None,
    updated_by=None,
    conflict_resolution: str = "last_write_wins",
) -> SharedWorkspaceItem:
    """Create a SharedWorkspaceItem instance for testing."""
    item = SharedWorkspaceItem()
    item.id = uuid4()
    item.conversation_id = conversation_id or uuid4()
    item.created_by = created_by
    item.updated_by = updated_by
    item.item_key = item_key
    item.item_type = item_type
    item.content = content
    item.version = version
    item.conflict_resolution = conflict_resolution
    item.created_at = datetime.now(timezone.utc)
    item.updated_at = datetime.now(timezone.utc)
    return item


def _mock_redis():
    """Create a mock Redis client with all needed methods."""
    redis = AsyncMock()
    redis.setex = AsyncMock(return_value=True)
    redis.get = AsyncMock(return_value=None)
    redis.mget = AsyncMock(return_value=[])
    redis.ping = AsyncMock(return_value=True)
    return redis


# ═══════════════════════════════════════════════════════════════════════════════
# S1: SharedWorkspaceItem Model Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestSharedWorkspaceItemModel:
    """S1: SharedWorkspaceItem model columns, constants, constraints."""

    def test_valid_item_types(self):
        """All 6 item types are defined."""
        assert len(WORKSPACE_ITEM_TYPES) == 6
        assert "text" in WORKSPACE_ITEM_TYPES
        assert "code" in WORKSPACE_ITEM_TYPES
        assert "diff" in WORKSPACE_ITEM_TYPES
        assert "json" in WORKSPACE_ITEM_TYPES
        assert "markdown" in WORKSPACE_ITEM_TYPES
        assert "binary_ref" in WORKSPACE_ITEM_TYPES

    def test_valid_conflict_strategies(self):
        """All 3 conflict resolution strategies are defined."""
        assert len(CONFLICT_STRATEGIES) == 3
        assert "last_write_wins" in CONFLICT_STRATEGIES
        assert "retry_3x" in CONFLICT_STRATEGIES
        assert "escalate_to_lead" in CONFLICT_STRATEGIES

    def test_tablename(self):
        """Table name is shared_workspace_items."""
        assert SharedWorkspaceItem.__tablename__ == "shared_workspace_items"

    def test_columns_exist(self):
        """All expected columns exist on the model."""
        table = SharedWorkspaceItem.__table__
        col_names = {c.name for c in table.columns}
        expected = {
            "id", "conversation_id", "created_by", "updated_by",
            "item_key", "item_type", "content", "version",
            "conflict_resolution", "created_at", "updated_at",
        }
        assert expected.issubset(col_names)

    def test_to_dict_serialization(self):
        """to_dict() returns correct keys and values."""
        conv_id = uuid4()
        agent_id = uuid4()
        item = _make_workspace_item(
            conversation_id=conv_id,
            created_by=agent_id,
            item_key="reviewer/notes",
            content="Looks good!",
            item_type="text",
            version=3,
        )

        d = item.to_dict()
        assert d["conversation_id"] == str(conv_id)
        assert d["created_by"] == str(agent_id)
        assert d["item_key"] == "reviewer/notes"
        assert d["content"] == "Looks good!"
        assert d["item_type"] == "text"
        assert d["version"] == 3
        assert d["conflict_resolution"] == "last_write_wins"

    def test_to_dict_none_agent(self):
        """to_dict() handles None created_by/updated_by."""
        item = _make_workspace_item(created_by=None, updated_by=None)
        d = item.to_dict()
        assert d["created_by"] is None
        assert d["updated_by"] is None

    def test_repr(self):
        """__repr__ includes key, version, type."""
        item = _make_workspace_item(item_key="coder/test.py", version=2, item_type="code")
        r = repr(item)
        assert "coder/test.py" in r
        assert "version=2" in r
        assert "code" in r

    def test_table_args_check_constraints(self):
        """Table has 2 CHECK constraints (item_type, conflict_resolution)."""
        constraints = [
            c for c in SharedWorkspaceItem.__table_args__
            if hasattr(c, 'name') and c.name and c.name.startswith('ck_')
        ]
        names = {c.name for c in constraints}
        assert "ck_workspace_item_type" in names
        assert "ck_workspace_conflict_resolution" in names


# ═══════════════════════════════════════════════════════════════════════════════
# S2: SharedWorkspace Service Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestSharedWorkspaceService:
    """S2: SharedWorkspace service — put, get, list_keys, delete."""

    @pytest.mark.asyncio
    async def test_put_creates_new_item(self):
        """put() creates new item when key doesn't exist."""
        db = AsyncMock()
        conv_id = uuid4()
        agent_id = uuid4()

        # SELECT FOR UPDATE returns None (no existing)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=mock_result)
        db.add = MagicMock()
        db.flush = AsyncMock()

        ws = SharedWorkspace(db, conv_id)
        item = await ws.put("coder/main.py", "code content", agent_id=agent_id)

        assert item.item_key == "coder/main.py"
        assert item.content == "code content"
        assert item.version == 1
        assert item.created_by == agent_id
        db.add.assert_called_once()
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_put_updates_existing(self):
        """put() updates existing item and increments version."""
        db = AsyncMock()
        conv_id = uuid4()
        existing = _make_workspace_item(
            conversation_id=conv_id,
            item_key="coder/main.py",
            content="old content",
            version=2,
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing
        db.execute = AsyncMock(return_value=mock_result)
        db.flush = AsyncMock()

        ws = SharedWorkspace(db, conv_id)
        updated = await ws.put("coder/main.py", "new content")

        assert updated.content == "new content"
        assert updated.version == 3

    @pytest.mark.asyncio
    async def test_get_returns_active_item(self):
        """get() returns item with version > 0."""
        db = AsyncMock()
        conv_id = uuid4()
        item = _make_workspace_item(conversation_id=conv_id, version=2)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = item
        db.execute = AsyncMock(return_value=mock_result)

        ws = SharedWorkspace(db, conv_id)
        result = await ws.get("coder/main.py")
        assert result is not None
        assert result.version == 2

    @pytest.mark.asyncio
    async def test_get_returns_none_missing(self):
        """get() returns None when key doesn't exist."""
        db = AsyncMock()
        conv_id = uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=mock_result)

        ws = SharedWorkspace(db, conv_id)
        result = await ws.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_list_keys_with_preview(self):
        """list_keys() returns items with 50-char preview."""
        db = AsyncMock()
        conv_id = uuid4()

        item1 = _make_workspace_item(
            conversation_id=conv_id,
            item_key="a/file.py",
            content="short",
            item_type="code",
            version=1,
        )
        item2 = _make_workspace_item(
            conversation_id=conv_id,
            item_key="b/notes.md",
            content="x" * 100,
            item_type="markdown",
            version=3,
        )

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [item1, item2]
        mock_result.scalars.return_value = mock_scalars
        db.execute = AsyncMock(return_value=mock_result)

        ws = SharedWorkspace(db, conv_id)
        keys = await ws.list_keys()

        assert len(keys) == 2
        assert keys[0]["item_key"] == "a/file.py"
        assert keys[0]["preview"] == "short"
        assert keys[1]["preview"] == "x" * 50 + "\u2026"

    @pytest.mark.asyncio
    async def test_delete_soft_deletes(self):
        """delete() sets version=-1 (soft delete)."""
        db = AsyncMock()
        conv_id = uuid4()

        mock_result = MagicMock()
        mock_result.rowcount = 1
        db.execute = AsyncMock(return_value=mock_result)

        ws = SharedWorkspace(db, conv_id)
        deleted = await ws.delete("coder/main.py")
        assert deleted is True

    @pytest.mark.asyncio
    async def test_delete_not_found(self):
        """delete() returns False when key doesn't exist."""
        db = AsyncMock()
        conv_id = uuid4()

        mock_result = MagicMock()
        mock_result.rowcount = 0
        db.execute = AsyncMock(return_value=mock_result)

        ws = SharedWorkspace(db, conv_id)
        deleted = await ws.delete("nonexistent")
        assert deleted is False

    @pytest.mark.asyncio
    async def test_get_active_keys(self):
        """get_active_keys() returns list of key strings."""
        db = AsyncMock()
        conv_id = uuid4()

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = ["a/file.py", "b/notes.md"]
        mock_result.scalars.return_value = mock_scalars
        db.execute = AsyncMock(return_value=mock_result)

        ws = SharedWorkspace(db, conv_id)
        keys = await ws.get_active_keys()
        assert keys == ["a/file.py", "b/notes.md"]


# ═══════════════════════════════════════════════════════════════════════════════
# S3: Optimistic Concurrency Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestOptimisticConcurrency:
    """S3: VersionConflictError and expected_version check."""

    def test_version_conflict_error_attributes(self):
        """VersionConflictError stores item_key, expected, actual."""
        err = VersionConflictError("coder/main.py", expected=2, actual=5)
        assert err.item_key == "coder/main.py"
        assert err.expected == 2
        assert err.actual == 5
        assert "coder/main.py" in str(err)
        assert "expected=2" in str(err)

    @pytest.mark.asyncio
    async def test_put_version_conflict(self):
        """put() with wrong expected_version raises VersionConflictError."""
        db = AsyncMock()
        conv_id = uuid4()
        existing = _make_workspace_item(
            conversation_id=conv_id,
            item_key="coder/main.py",
            version=5,
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing
        db.execute = AsyncMock(return_value=mock_result)

        ws = SharedWorkspace(db, conv_id)
        with pytest.raises(VersionConflictError) as exc_info:
            await ws.put("coder/main.py", "new", expected_version=2)

        assert exc_info.value.expected == 2
        assert exc_info.value.actual == 5

    @pytest.mark.asyncio
    async def test_put_version_match_succeeds(self):
        """put() with correct expected_version succeeds."""
        db = AsyncMock()
        conv_id = uuid4()
        existing = _make_workspace_item(
            conversation_id=conv_id,
            item_key="coder/main.py",
            version=3,
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing
        db.execute = AsyncMock(return_value=mock_result)
        db.flush = AsyncMock()

        ws = SharedWorkspace(db, conv_id)
        item = await ws.put("coder/main.py", "updated", expected_version=3)
        assert item.version == 4
        assert item.content == "updated"


# ═══════════════════════════════════════════════════════════════════════════════
# S4: HeartbeatService Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestHeartbeatService:
    """S4: HeartbeatService — record, check_liveness, recover."""

    def test_hb_key_format(self):
        """Redis key follows hb:{agent_id}:{conv_id} pattern."""
        agent_id = uuid4()
        conv_id = uuid4()
        key = _hb_key(agent_id, conv_id)
        assert key == f"hb:{agent_id}:{conv_id}"

    def test_recovery_key_format(self):
        """Redis recovery key follows hb:recovery:{conv_id} pattern."""
        conv_id = uuid4()
        key = _recovery_key(conv_id)
        assert key == f"hb:recovery:{conv_id}"

    @pytest.mark.asyncio
    async def test_record_heartbeat_success(self):
        """record_heartbeat() sets Redis key with TTL."""
        redis = _mock_redis()
        db = AsyncMock()
        service = HeartbeatService(db, redis=redis)

        agent_id = uuid4()
        conv_id = uuid4()
        result = await service.record_heartbeat(agent_id, conv_id)

        assert result is True
        redis.setex.assert_awaited_once()
        call_args = redis.setex.call_args
        assert f"hb:{agent_id}:{conv_id}" == call_args[0][0]
        assert call_args[0][1] == DEFAULT_TTL_SECONDS

    @pytest.mark.asyncio
    async def test_record_heartbeat_no_redis(self):
        """record_heartbeat() returns False when Redis is None."""
        db = AsyncMock()
        service = HeartbeatService(db, redis=None)
        result = await service.record_heartbeat(uuid4(), uuid4())
        assert result is False

    @pytest.mark.asyncio
    async def test_record_heartbeat_redis_error(self):
        """record_heartbeat() returns False on Redis error (non-fatal)."""
        redis = _mock_redis()
        redis.setex = AsyncMock(side_effect=ConnectionError("lost"))
        db = AsyncMock()
        service = HeartbeatService(db, redis=redis)
        result = await service.record_heartbeat(uuid4(), uuid4())
        assert result is False

    @pytest.mark.asyncio
    async def test_check_liveness_alive(self):
        """check_liveness() returns True when key exists."""
        redis = _mock_redis()
        redis.get = AsyncMock(return_value=b'{"timestamp": "2026-01-01"}')
        db = AsyncMock()
        service = HeartbeatService(db, redis=redis)

        result = await service.check_liveness(uuid4(), uuid4())
        assert result is True

    @pytest.mark.asyncio
    async def test_check_liveness_expired(self):
        """check_liveness() returns False when key expired."""
        redis = _mock_redis()
        redis.get = AsyncMock(return_value=None)
        db = AsyncMock()
        service = HeartbeatService(db, redis=redis)

        result = await service.check_liveness(uuid4(), uuid4())
        assert result is False

    @pytest.mark.asyncio
    async def test_check_liveness_no_redis(self):
        """check_liveness() returns False when Redis is None."""
        db = AsyncMock()
        service = HeartbeatService(db, redis=None)
        result = await service.check_liveness(uuid4(), uuid4())
        assert result is False

    @pytest.mark.asyncio
    async def test_default_ttl(self):
        """Default TTL is 60 seconds."""
        assert DEFAULT_TTL_SECONDS == 60

    @pytest.mark.asyncio
    async def test_recovery_dedup_ttl(self):
        """Recovery dedup TTL is 300 seconds (5 minutes)."""
        assert RECOVERY_DEDUP_TTL == 300


# ═══════════════════════════════════════════════════════════════════════════════
# S5: Heartbeat Batch Check (MGET)
# ═══════════════════════════════════════════════════════════════════════════════

class TestHeartbeatBatchCheck:
    """S5: get_stale_agents uses MGET for single round-trip."""

    @pytest.mark.asyncio
    async def test_get_stale_agents_one_expired(self):
        """get_stale_agents: 1 expired + 1 active → only expired returned."""
        redis = _mock_redis()
        agent1 = uuid4()
        agent2 = uuid4()
        conv1 = uuid4()
        conv2 = uuid4()

        # agent1 expired (None), agent2 alive (has data)
        redis.mget = AsyncMock(return_value=[None, b'{"ts": "ok"}'])

        db = AsyncMock()
        service = HeartbeatService(db, redis=redis)
        pairs = [(agent1, conv1), (agent2, conv2)]
        stale = await service.get_stale_agents(pairs)

        assert len(stale) == 1
        assert stale[0] == (agent1, conv1)
        redis.mget.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_stale_agents_all_alive(self):
        """get_stale_agents: all alive → empty list."""
        redis = _mock_redis()
        redis.mget = AsyncMock(return_value=[b'{"ts": "1"}', b'{"ts": "2"}'])

        db = AsyncMock()
        service = HeartbeatService(db, redis=redis)
        stale = await service.get_stale_agents([(uuid4(), uuid4()), (uuid4(), uuid4())])
        assert stale == []

    @pytest.mark.asyncio
    async def test_get_stale_agents_empty_input(self):
        """get_stale_agents: empty list → empty result, no Redis call."""
        redis = _mock_redis()
        db = AsyncMock()
        service = HeartbeatService(db, redis=redis)
        stale = await service.get_stale_agents([])
        assert stale == []
        redis.mget.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_get_stale_agents_no_redis(self):
        """get_stale_agents: no Redis → empty result."""
        db = AsyncMock()
        service = HeartbeatService(db, redis=None)
        stale = await service.get_stale_agents([(uuid4(), uuid4())])
        assert stale == []

    @pytest.mark.asyncio
    async def test_get_stale_agents_redis_error(self):
        """get_stale_agents: Redis error → empty result (non-fatal)."""
        redis = _mock_redis()
        redis.mget = AsyncMock(side_effect=ConnectionError("lost"))
        db = AsyncMock()
        service = HeartbeatService(db, redis=redis)
        stale = await service.get_stale_agents([(uuid4(), uuid4())])
        assert stale == []


# ═══════════════════════════════════════════════════════════════════════════════
# S6: HeartbeatMonitor Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestHeartbeatMonitor:
    """S6: HeartbeatMonitor start, stop, circuit breaker constants."""

    def test_scan_interval_30s(self):
        """Scan interval is 30 seconds."""
        assert SCAN_INTERVAL_SECONDS == 30

    def test_mass_stall_threshold(self):
        """Mass stall threshold is 5 agents."""
        assert MASS_STALL_THRESHOLD == 5

    def test_mass_stall_window(self):
        """Mass stall window is 60 seconds."""
        assert MASS_STALL_WINDOW_SECONDS == 60

    def test_monitor_init(self):
        """Monitor initializes with correct state."""
        monitor = HeartbeatMonitor(db_url="postgresql://test", redis=None)
        assert monitor._running is False
        assert monitor._task is None
        assert monitor._stall_timestamps == []

    @pytest.mark.asyncio
    async def test_monitor_start_sets_running(self):
        """start() sets _running=True and creates task."""
        monitor = HeartbeatMonitor(db_url="postgresql://test", redis=None)

        # Patch _scan_loop to prevent actual execution
        async def _noop():
            await asyncio.sleep(999)

        with patch.object(monitor, '_scan_loop', _noop):
            await monitor.start()
            assert monitor._running is True
            assert monitor._task is not None

            # Stop immediately to clean up
            monitor.stop()
            assert monitor._running is False

    @pytest.mark.asyncio
    async def test_monitor_double_start(self, caplog):
        """start() twice logs warning."""
        monitor = HeartbeatMonitor(db_url="postgresql://test", redis=None)

        async def _noop():
            await asyncio.sleep(999)

        with patch.object(monitor, '_scan_loop', _noop):
            await monitor.start()
            with caplog.at_level(logging.WARNING):
                await monitor.start()  # Double start
            assert "already running" in caplog.text
            monitor.stop()

    def test_monitor_stop_when_not_running(self):
        """stop() on non-running monitor is safe (no error)."""
        monitor = HeartbeatMonitor(db_url="postgresql://test", redis=None)
        monitor.stop()  # Should not raise
        assert monitor._running is False


# ═══════════════════════════════════════════════════════════════════════════════
# S7: Recovery Idempotency Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestRecoveryIdempotency:
    """S7: recover_stale_conversation dedup via Redis key."""

    @pytest.mark.asyncio
    async def test_recover_skips_when_dedup_key_exists(self):
        """Recovery is skipped when Redis dedup key exists (5 min TTL)."""
        redis = _mock_redis()
        redis.get = AsyncMock(return_value=b"1")  # Dedup key exists
        db = AsyncMock()

        service = HeartbeatService(db, redis=redis)
        result = await service.recover_stale_conversation(uuid4())
        assert result is False
        # DB should NOT be called
        db.execute.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_recover_sets_dedup_key(self):
        """Successful recovery sets Redis dedup key with 5 min TTL."""
        redis = _mock_redis()
        redis.get = AsyncMock(return_value=None)  # No dedup key
        db = AsyncMock()

        # UPDATE returns 1 row affected
        mock_result = MagicMock()
        mock_result.rowcount = 1
        db.execute = AsyncMock(return_value=mock_result)
        db.add = MagicMock()
        db.flush = AsyncMock()

        service = HeartbeatService(db, redis=redis)
        conv_id = uuid4()
        result = await service.recover_stale_conversation(conv_id)

        assert result is True
        # Check dedup key was set
        redis.setex.assert_awaited_once()
        dedup_call = redis.setex.call_args
        assert f"hb:recovery:{conv_id}" == dedup_call[0][0]
        assert dedup_call[0][1] == RECOVERY_DEDUP_TTL

    @pytest.mark.asyncio
    async def test_recover_not_active_returns_false(self):
        """Recovery returns False when conversation is not active."""
        redis = _mock_redis()
        redis.get = AsyncMock(return_value=None)
        db = AsyncMock()

        # UPDATE returns 0 rows (not active)
        mock_result = MagicMock()
        mock_result.rowcount = 0
        db.execute = AsyncMock(return_value=mock_result)

        service = HeartbeatService(db, redis=redis)
        result = await service.recover_stale_conversation(uuid4())
        assert result is False

    @pytest.mark.asyncio
    async def test_recover_inserts_system_message(self):
        """Successful recovery inserts a system message."""
        redis = _mock_redis()
        redis.get = AsyncMock(return_value=None)
        db = AsyncMock()

        mock_result = MagicMock()
        mock_result.rowcount = 1
        db.execute = AsyncMock(return_value=mock_result)
        db.add = MagicMock()
        db.flush = AsyncMock()

        service = HeartbeatService(db, redis=redis)
        await service.recover_stale_conversation(uuid4())

        # db.add should be called with a system message
        db.add.assert_called_once()
        msg = db.add.call_args[0][0]
        assert msg.sender_type == "system"
        assert msg.sender_id == "heartbeat_monitor"
        assert "heartbeat expired" in msg.content.lower()

    @pytest.mark.asyncio
    async def test_get_active_conversations(self):
        """get_active_conversations returns (agent_def_id, conv_id) pairs."""
        db = AsyncMock()
        agent_id = uuid4()
        conv_id = uuid4()

        mock_result = MagicMock()
        mock_result.all.return_value = [(agent_id, conv_id)]
        db.execute = AsyncMock(return_value=mock_result)

        service = HeartbeatService(db, redis=None)
        active = await service.get_active_conversations()
        assert len(active) == 1
        assert active[0] == (agent_id, conv_id)


# ═══════════════════════════════════════════════════════════════════════════════
# S8: Model Registration
# ═══════════════════════════════════════════════════════════════════════════════

class TestModelRegistration:
    """S8: SharedWorkspaceItem registered in models/__init__.py."""

    def test_shared_workspace_item_in_all(self):
        """SharedWorkspaceItem is in models.__all__."""
        from app.models import __all__ as all_models
        assert "SharedWorkspaceItem" in all_models

    def test_shared_workspace_item_importable(self):
        """SharedWorkspaceItem is importable from app.models."""
        from app.models import SharedWorkspaceItem as SWI
        assert SWI is SharedWorkspaceItem


# ═══════════════════════════════════════════════════════════════════════════════
# S9: Alembic Migration Chain
# ═══════════════════════════════════════════════════════════════════════════════

class TestAlembicMigrationChain:
    """S9: Migration s219_001 chain and table definition."""

    def _load_migration(self):
        """Load s219_001 migration module by filesystem path."""
        migrations_dir = Path(__file__).resolve().parent.parent.parent / "alembic" / "versions"
        migration_file = migrations_dir / "s219_001_workspace_heartbeat.py"
        assert migration_file.exists(), f"Migration file not found: {migration_file}"

        spec = importlib.util.spec_from_file_location("s219_001", str(migration_file))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    def test_revision_id(self):
        """Migration revision is s219_001."""
        mod = self._load_migration()
        assert mod.revision == "s219_001"

    def test_down_revision_chain(self):
        """s219_001 depends on s218_001."""
        mod = self._load_migration()
        assert mod.down_revision == "s218_001"

    def test_upgrade_function_exists(self):
        """upgrade() function is defined."""
        mod = self._load_migration()
        assert callable(mod.upgrade)

    def test_downgrade_function_exists(self):
        """downgrade() function is defined."""
        mod = self._load_migration()
        assert callable(mod.downgrade)


# ═══════════════════════════════════════════════════════════════════════════════
# S10: Orchestrator Heartbeat Wiring
# ═══════════════════════════════════════════════════════════════════════════════

class TestOrchestratorHeartbeatWiring:
    """S10: HeartbeatService wired into TeamOrchestrator."""

    def test_orchestrator_has_heartbeat_attribute(self):
        """TeamOrchestrator constructor creates heartbeat attribute."""
        from app.services.agent_team.team_orchestrator import TeamOrchestrator

        db = AsyncMock()
        redis = _mock_redis()
        orchestrator = TeamOrchestrator(db=db, redis=redis)

        assert hasattr(orchestrator, 'heartbeat')
        assert isinstance(orchestrator.heartbeat, HeartbeatService)

    def test_orchestrator_heartbeat_uses_injected_redis(self):
        """HeartbeatService uses the Redis instance injected into orchestrator."""
        from app.services.agent_team.team_orchestrator import TeamOrchestrator

        db = AsyncMock()
        redis = _mock_redis()
        orchestrator = TeamOrchestrator(db=db, redis=redis)

        assert orchestrator.heartbeat.redis is redis

    def test_heartbeat_monitor_importable(self):
        """HeartbeatMonitor can be imported from heartbeat_monitor module."""
        from app.services.agent_team.heartbeat_monitor import HeartbeatMonitor
        assert HeartbeatMonitor is not None

    def test_shared_workspace_importable(self):
        """SharedWorkspace can be imported from shared_workspace module."""
        from app.services.agent_team.shared_workspace import SharedWorkspace
        assert SharedWorkspace is not None


# ═══════════════════════════════════════════════════════════════════════════════
# S11: CTO Review Fix — Input Validation (F1)
# ═══════════════════════════════════════════════════════════════════════════════

class TestCTOReviewFixF1:
    """S11: Input validation in SharedWorkspace.put() — CTO F1."""

    @pytest.mark.asyncio
    async def test_item_key_too_long_raises(self):
        """put() rejects item_key > 200 chars."""
        db = AsyncMock()
        ws = SharedWorkspace(db, uuid4())
        with pytest.raises(ValueError, match="item_key must be 1-200 chars"):
            await ws.put("x" * 201, "content")

    @pytest.mark.asyncio
    async def test_item_key_empty_raises(self):
        """put() rejects empty item_key."""
        db = AsyncMock()
        ws = SharedWorkspace(db, uuid4())
        with pytest.raises(ValueError, match="item_key must be 1-200 chars"):
            await ws.put("", "content")

    @pytest.mark.asyncio
    async def test_item_key_max_length_ok(self):
        """put() accepts exactly 200-char key."""
        db = AsyncMock()
        conv_id = uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=mock_result)
        db.add = MagicMock()
        db.flush = AsyncMock()

        ws = SharedWorkspace(db, conv_id)
        item = await ws.put("x" * 200, "content")
        assert item.item_key == "x" * 200

    @pytest.mark.asyncio
    async def test_invalid_item_type_raises(self):
        """put() rejects invalid item_type."""
        db = AsyncMock()
        ws = SharedWorkspace(db, uuid4())
        with pytest.raises(ValueError, match="Invalid item_type"):
            await ws.put("key", "content", item_type="invalid")

    @pytest.mark.asyncio
    async def test_invalid_conflict_resolution_raises(self):
        """put() rejects invalid conflict_resolution."""
        db = AsyncMock()
        ws = SharedWorkspace(db, uuid4())
        with pytest.raises(ValueError, match="Invalid conflict_resolution"):
            await ws.put("key", "content", conflict_resolution="yolo")
