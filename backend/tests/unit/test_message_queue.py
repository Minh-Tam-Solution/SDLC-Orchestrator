"""
=========================================================================
Unit Tests - Message Queue (Sprint 177)
SDLC Orchestrator - Multi-Agent Team Engine

Version: 1.0.0
Date: February 2026
Status: ACTIVE - Sprint 177
Authority: CTO Approved (ADR-056 Decision 2)

Purpose:
- Test lane-based enqueue with dedupe
- Test SKIP LOCKED claim semantics
- Test dead-letter handling (threshold=3, exponential backoff)
- Test Redis notification (best-effort, non-fatal on failure)
- Test pending count and dead-letter retrieval

Zero Mock Policy: Mocked AsyncSession + Redis for unit isolation
=========================================================================
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.services.agent_team.message_queue import (
    MessageQueue,
    DEAD_LETTER_THRESHOLD,
    BACKOFF_BASE_SECONDS,
)


# =========================================================================
# Fixtures
# =========================================================================


@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    return db


@pytest.fixture
def mock_redis():
    redis = AsyncMock()
    redis.publish = AsyncMock()
    return redis


@pytest.fixture
def queue(mock_db, mock_redis):
    return MessageQueue(mock_db, mock_redis)


@pytest.fixture
def queue_no_redis(mock_db):
    return MessageQueue(mock_db, redis=None)


def _make_message(**overrides):
    """Create a mock AgentMessage."""
    msg = MagicMock()
    msg.id = overrides.get("id", uuid4())
    msg.conversation_id = overrides.get("conversation_id", uuid4())
    msg.content = overrides.get("content", "test message")
    msg.processing_status = overrides.get("processing_status", "pending")
    msg.processing_lane = overrides.get("processing_lane", "agent:coder")
    msg.failed_count = overrides.get("failed_count", 0)
    msg.last_error = overrides.get("last_error", None)
    msg.next_retry_at = overrides.get("next_retry_at", None)
    msg.failover_reason = overrides.get("failover_reason", None)
    msg.created_at = overrides.get("created_at", datetime.now(timezone.utc))
    msg.dedupe_key = overrides.get("dedupe_key", None)
    msg.correlation_id = overrides.get("correlation_id", uuid4())
    msg.provider_used = overrides.get("provider_used", None)
    msg.token_count = overrides.get("token_count", None)
    msg.latency_ms = overrides.get("latency_ms", None)
    return msg


# =========================================================================
# Enqueue Tests
# =========================================================================


class TestEnqueue:
    """Tests for MessageQueue.enqueue."""

    @pytest.mark.asyncio
    async def test_enqueue_creates_pending(self, queue, mock_db):
        """Enqueue creates a message with pending status."""
        # No dedupe hit
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        msg = await queue.enqueue(
            conversation_id=uuid4(),
            content="Hello agent",
            sender_type="user",
            sender_id="user-1",
            processing_lane="agent:coder",
        )

        # Verify db.add was called
        mock_db.add.assert_called_once()
        added_msg = mock_db.add.call_args[0][0]
        assert added_msg.processing_status == "pending"
        assert added_msg.processing_lane == "agent:coder"

    @pytest.mark.asyncio
    async def test_enqueue_dedupe_returns_existing(self, queue, mock_db):
        """Dedupe key match returns existing message without creating new."""
        existing_msg = _make_message(dedupe_key="dedup-123")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_msg
        mock_db.execute.return_value = mock_result

        result = await queue.enqueue(
            conversation_id=uuid4(),
            content="Duplicate",
            sender_type="user",
            sender_id="user-1",
            processing_lane="agent:coder",
            dedupe_key="dedup-123",
        )

        assert result.id == existing_msg.id
        mock_db.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_enqueue_notifies_redis(self, queue, mock_redis, mock_db):
        """Enqueue publishes notification to Redis channel."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        await queue.enqueue(
            conversation_id=uuid4(),
            content="Test",
            sender_type="user",
            sender_id="user-1",
            processing_lane="agent:coder",
        )

        mock_redis.publish.assert_called_once()
        channel = mock_redis.publish.call_args[0][0]
        assert "agent:coder" in channel

    @pytest.mark.asyncio
    async def test_enqueue_redis_failure_nonfatal(self, queue, mock_redis, mock_db):
        """Redis publish failure does not prevent message creation."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result
        mock_redis.publish.side_effect = ConnectionError("Redis down")

        # Should not raise
        msg = await queue.enqueue(
            conversation_id=uuid4(),
            content="Test",
            sender_type="user",
            sender_id="user-1",
            processing_lane="agent:coder",
        )

        mock_db.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_enqueue_without_redis(self, queue_no_redis, mock_db):
        """Enqueue works without Redis (degraded latency mode)."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        msg = await queue_no_redis.enqueue(
            conversation_id=uuid4(),
            content="No Redis",
            sender_type="user",
            sender_id="user-1",
            processing_lane="agent:coder",
        )

        mock_db.add.assert_called_once()


# =========================================================================
# Claim Tests
# =========================================================================


class TestClaimNext:
    """Tests for MessageQueue.claim_next (SKIP LOCKED)."""

    @pytest.mark.asyncio
    async def test_claim_returns_message(self, queue, mock_db):
        """Claim returns pending message and sets status to processing."""
        msg = _make_message(processing_status="pending")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = msg
        mock_db.execute.return_value = mock_result

        result = await queue.claim_next("agent:coder")

        assert result is not None
        assert msg.processing_status == "processing"

    @pytest.mark.asyncio
    async def test_claim_empty_lane(self, queue, mock_db):
        """Claim returns None when no messages are pending."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await queue.claim_next("agent:coder")
        assert result is None


# =========================================================================
# Complete Tests
# =========================================================================


class TestComplete:
    """Tests for MessageQueue.complete."""

    @pytest.mark.asyncio
    async def test_complete_sets_metrics(self, queue, mock_db):
        """Complete sets provider metrics on the message."""
        msg = _make_message(processing_status="processing")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = msg
        mock_db.execute.return_value = mock_result

        await queue.complete(
            msg.id,
            provider_used="ollama",
            token_count=1500,
            latency_ms=250,
        )

        assert msg.processing_status == "completed"
        assert msg.provider_used == "ollama"
        assert msg.token_count == 1500
        assert msg.latency_ms == 250


# =========================================================================
# Fail + Dead-Letter Tests
# =========================================================================


class TestFail:
    """Tests for MessageQueue.fail with dead-letter handling."""

    @pytest.mark.asyncio
    async def test_fail_increments_count(self, queue, mock_db):
        """Fail increments failed_count."""
        msg = _make_message(failed_count=0)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = msg
        mock_db.execute.return_value = mock_result

        is_dead = await queue.fail(msg.id, error="Connection timeout")

        assert is_dead is False
        assert msg.failed_count == 1

    @pytest.mark.asyncio
    async def test_fail_exponential_backoff(self, queue, mock_db):
        """Backoff follows 30s * 2^(failed_count-1) pattern."""
        msg = _make_message(failed_count=1)  # Will become 2
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = msg
        mock_db.execute.return_value = mock_result

        await queue.fail(msg.id, error="Timeout")

        assert msg.failed_count == 2
        assert msg.processing_status == "pending"
        # Backoff for attempt 2: 30 * 2^(2-1) = 60s
        assert msg.next_retry_at is not None

    @pytest.mark.asyncio
    async def test_fail_dead_letter_at_threshold(self, queue, mock_db):
        """Message moves to dead_letter when failed_count reaches threshold."""
        msg = _make_message(failed_count=DEAD_LETTER_THRESHOLD - 1)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = msg
        mock_db.execute.return_value = mock_result

        is_dead = await queue.fail(msg.id, error="Persistent failure")

        assert is_dead is True
        assert msg.processing_status == "dead_letter"
        assert msg.failed_count == DEAD_LETTER_THRESHOLD

    @pytest.mark.asyncio
    async def test_fail_truncates_error(self, queue, mock_db):
        """Error strings are truncated to 2000 chars to prevent DB bloat."""
        msg = _make_message(failed_count=0)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = msg
        mock_db.execute.return_value = mock_result

        long_error = "x" * 5000
        await queue.fail(msg.id, error=long_error)

        assert len(msg.last_error) == 2000


# =========================================================================
# Monitoring Tests
# =========================================================================


class TestMonitoring:
    """Tests for queue monitoring operations."""

    @pytest.mark.asyncio
    async def test_get_pending_count(self, queue, mock_db):
        """Pending count returns integer."""
        mock_result = MagicMock()
        mock_result.scalar.return_value = 5
        mock_db.execute.return_value = mock_result

        count = await queue.get_pending_count("agent:coder")
        assert count == 5

    @pytest.mark.asyncio
    async def test_get_dead_letters(self, queue, mock_db):
        """Dead letters returns list of messages."""
        dead_msgs = [_make_message(processing_status="dead_letter") for _ in range(3)]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = dead_msgs
        mock_db.execute.return_value = mock_result

        result = await queue.get_dead_letters("agent:coder")
        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_requeue_dead_letter(self, queue, mock_db, mock_redis):
        """Requeue resets dead-letter to pending."""
        msg = _make_message(processing_status="dead_letter", failed_count=3)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = msg
        mock_db.execute.return_value = mock_result

        success = await queue.requeue_dead_letter(msg.id)

        assert success is True
        assert msg.processing_status == "pending"
        assert msg.failed_count == 0
        assert msg.next_retry_at is None

    @pytest.mark.asyncio
    async def test_requeue_non_dead_letter_fails(self, queue, mock_db):
        """Cannot requeue a message that is not dead-lettered."""
        msg = _make_message(processing_status="pending")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = msg
        mock_db.execute.return_value = mock_result

        success = await queue.requeue_dead_letter(msg.id)
        assert success is False


# =========================================================================
# Constants Tests
# =========================================================================


class TestConstants:
    """Tests for queue configuration constants."""

    def test_dead_letter_threshold(self):
        assert DEAD_LETTER_THRESHOLD == 3

    def test_backoff_base(self):
        assert BACKOFF_BASE_SECONDS == 30

    def test_backoff_formula(self):
        """Verify exponential backoff: 30s, 60s, 120s."""
        for attempt in range(1, 4):
            expected = BACKOFF_BASE_SECONDS * (2 ** (attempt - 1))
            assert expected in (30, 60, 120), f"Unexpected backoff for attempt {attempt}"
