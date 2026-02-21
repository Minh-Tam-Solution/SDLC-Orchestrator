"""
Unit tests for HistoryCompactor — ADR-058 Pattern B.

Sprint 179 — ZeroClaw Security Hardening.
Test IDs: HC-01 to HC-10 (see FR-044 §3).

Coverage:
  HC-01  should_compact() returns False below 80% threshold
  HC-02  should_compact() returns True at 80% threshold
  HC-03  Stale-guard: skip compaction if delta < STALE_GUARD_DELTA
  HC-04  maybe_compact() returns None if threshold not reached
  HC-05  maybe_compact() fires LLM summarize when invoker provided
  HC-06  LLM failure falls back to deterministic truncation (no exception)
  HC-07  Summary stored in metadata_ with correct keys
  HC-08  maybe_compact() returns None when not enough history (≤ KEEP_RECENT)
  HC-09  _fallback_truncate() respects MAX_SUMMARY_CHARS
  HC-10  _messages_to_text() maps sender_type to role correctly
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.services.agent_team.history_compactor import (
    COMPACTION_THRESHOLD_RATIO,
    KEEP_RECENT,
    MAX_SUMMARY_CHARS,
    STALE_GUARD_DELTA,
    HistoryCompactor,
)


# ── Helpers ──────────────────────────────────────────────────────────────────

def _make_conversation(
    total_messages: int = 0,
    max_messages: int = 50,
    metadata: dict[str, Any] | None = None,
) -> MagicMock:
    conv = MagicMock()
    conv.id = uuid4()
    conv.total_messages = total_messages
    conv.max_messages = max_messages
    conv.metadata_ = metadata or {}
    return conv


def _make_message(sender_type: str = "user", content: str = "hello") -> MagicMock:
    msg = MagicMock()
    msg.id = uuid4()
    msg.sender_type = sender_type
    msg.content = content
    msg.processing_status = "completed"
    msg.created_at = datetime.now(timezone.utc)
    return msg


def _make_db_with_messages(messages: list[MagicMock]) -> AsyncMock:
    """Return a mock AsyncSession whose execute() yields the given messages."""
    db = AsyncMock()
    result = MagicMock()
    result.scalars.return_value.all.return_value = messages
    db.execute.return_value = result
    db.flush = AsyncMock()
    return db


# ── HC-01: should_compact() below threshold ──────────────────────────────────

class TestShouldCompactBelowThreshold:
    def test_below_threshold_returns_false(self) -> None:
        """HC-01 — 10% utilization → should_compact() is False."""
        db = AsyncMock()
        compactor = HistoryCompactor(db=db)
        conv = _make_conversation(total_messages=5, max_messages=50)
        assert compactor.should_compact(conv) is False

    def test_just_below_threshold_returns_false(self) -> None:
        """HC-01b — 79% utilization → False."""
        db = AsyncMock()
        compactor = HistoryCompactor(db=db)
        # 80% of 50 = 40; 39 < 40 → False
        conv = _make_conversation(total_messages=39, max_messages=50)
        assert compactor.should_compact(conv) is False


# ── HC-02: should_compact() at threshold ─────────────────────────────────────

class TestShouldCompactAtThreshold:
    def test_at_threshold_returns_true(self) -> None:
        """HC-02a — exactly at 80% → should_compact() is True."""
        db = AsyncMock()
        compactor = HistoryCompactor(db=db)
        # 80% of 50 = 40 → True (last_compacted_messages = 0, delta = 40)
        conv = _make_conversation(total_messages=40, max_messages=50)
        assert compactor.should_compact(conv) is True

    def test_above_threshold_returns_true(self) -> None:
        """HC-02b — 90% utilization → True."""
        db = AsyncMock()
        compactor = HistoryCompactor(db=db)
        conv = _make_conversation(total_messages=45, max_messages=50)
        assert compactor.should_compact(conv) is True


# ── HC-03: Stale-guard ───────────────────────────────────────────────────────

class TestStaleGuard:
    def test_stale_guard_skips_when_delta_small(self) -> None:
        """HC-03a — already compacted recently (delta < STALE_GUARD_DELTA) → False."""
        db = AsyncMock()
        compactor = HistoryCompactor(db=db)
        # total=42, last_compacted=40, delta=2 < STALE_GUARD_DELTA(5)
        conv = _make_conversation(
            total_messages=42,
            max_messages=50,
            metadata={"last_compacted_messages": 40},
        )
        assert compactor.should_compact(conv) is False

    def test_stale_guard_fires_when_delta_sufficient(self) -> None:
        """HC-03b — delta >= STALE_GUARD_DELTA → True."""
        db = AsyncMock()
        compactor = HistoryCompactor(db=db)
        # total=46, last_compacted=40, delta=6 >= 5 → True
        conv = _make_conversation(
            total_messages=46,
            max_messages=50,
            metadata={"last_compacted_messages": 40},
        )
        assert compactor.should_compact(conv) is True


# ── HC-04: maybe_compact() no-op below threshold ─────────────────────────────

class TestMaybeCompactNoOp:
    @pytest.mark.asyncio
    async def test_returns_none_below_threshold(self) -> None:
        """HC-04 — threshold not reached → maybe_compact() returns None."""
        db = AsyncMock()
        compactor = HistoryCompactor(db=db)
        conv = _make_conversation(total_messages=5, max_messages=50)
        result = await compactor.maybe_compact(conv, agent_invoker=None)
        assert result is None
        # DB execute should NOT be called
        db.execute.assert_not_called()


# ── HC-05: maybe_compact() LLM summarize ─────────────────────────────────────

class TestMaybeCompactLLMSummarize:
    @pytest.mark.asyncio
    async def test_uses_invoker_when_provided(self) -> None:
        """HC-05 — LLM summarizer invoked when agent_invoker is provided."""
        messages = [_make_message("user", f"msg {i}") for i in range(30)]
        db = _make_db_with_messages(messages)
        compactor = HistoryCompactor(db=db)

        # Conversation is over threshold
        conv = _make_conversation(total_messages=42, max_messages=50)

        # Mock agent_invoker with async invoke()
        mock_result = MagicMock()
        mock_result.content = "This is the LLM-generated summary."
        mock_invoker = MagicMock()
        mock_invoker.invoke = AsyncMock(return_value=mock_result)

        summary = await compactor.maybe_compact(conv, agent_invoker=mock_invoker)

        assert summary is not None
        assert "LLM-generated summary" in summary
        mock_invoker.invoke.assert_awaited_once()


# ── HC-06: LLM failure → fallback truncation ─────────────────────────────────

class TestLLMFailureFallback:
    @pytest.mark.asyncio
    async def test_llm_exception_falls_back_to_truncation(self) -> None:
        """HC-06 — LLM invoke raises → fallback truncation used, no exception."""
        messages = [_make_message("user", f"msg {i}") for i in range(30)]
        db = _make_db_with_messages(messages)
        compactor = HistoryCompactor(db=db)
        conv = _make_conversation(total_messages=42, max_messages=50)

        # Mock invoker that raises
        mock_invoker = MagicMock()
        mock_invoker.invoke = AsyncMock(side_effect=RuntimeError("LLM unavailable"))

        # Should NOT raise — fallback used
        summary = await compactor.maybe_compact(conv, agent_invoker=mock_invoker)
        assert summary is not None
        # Deterministic truncation result is non-empty
        assert len(summary) > 0

    @pytest.mark.asyncio
    async def test_no_invoker_uses_fallback(self) -> None:
        """HC-06b — invoker=None → fallback truncation used directly."""
        messages = [_make_message("user", f"content of message {i}") for i in range(30)]
        db = _make_db_with_messages(messages)
        compactor = HistoryCompactor(db=db)
        conv = _make_conversation(total_messages=42, max_messages=50)

        summary = await compactor.maybe_compact(conv, agent_invoker=None)
        assert summary is not None
        assert len(summary) > 0


# ── HC-07: Summary stored in metadata_ ───────────────────────────────────────

class TestSummaryPersisted:
    @pytest.mark.asyncio
    async def test_compaction_summary_stored_in_metadata(self) -> None:
        """HC-07 — summary stored in conversation.metadata_['compaction_summary']."""
        messages = [_make_message("user", f"msg {i}") for i in range(30)]
        db = _make_db_with_messages(messages)
        compactor = HistoryCompactor(db=db)
        conv = _make_conversation(total_messages=42, max_messages=50)

        await compactor.maybe_compact(conv, agent_invoker=None)

        meta = conv.metadata_
        assert "compaction_summary" in meta
        assert "last_compacted_messages" in meta
        assert "last_compacted_at" in meta
        assert meta["last_compacted_messages"] == conv.total_messages
        db.flush.assert_awaited()

    @pytest.mark.asyncio
    async def test_last_compacted_at_is_iso_timestamp(self) -> None:
        """HC-07b — last_compacted_at is a parseable ISO 8601 timestamp."""
        messages = [_make_message("user", f"msg {i}") for i in range(30)]
        db = _make_db_with_messages(messages)
        compactor = HistoryCompactor(db=db)
        conv = _make_conversation(total_messages=42, max_messages=50)

        await compactor.maybe_compact(conv, agent_invoker=None)

        ts = conv.metadata_["last_compacted_at"]
        # Should be parseable
        parsed = datetime.fromisoformat(ts)
        assert parsed is not None


# ── HC-08: Returns None when not enough history ───────────────────────────────

class TestNotEnoughHistory:
    @pytest.mark.asyncio
    async def test_returns_none_when_history_le_keep_recent(self) -> None:
        """HC-08 — ≤ KEEP_RECENT completed messages → nothing to summarize → None."""
        messages = [_make_message("user", f"msg {i}") for i in range(KEEP_RECENT)]
        db = _make_db_with_messages(messages)
        compactor = HistoryCompactor(db=db)
        # Conversation IS over threshold
        conv = _make_conversation(total_messages=42, max_messages=50)

        result = await compactor.maybe_compact(conv, agent_invoker=None)
        # Even if threshold is reached, no older msgs to summarize
        assert result is None


# ── HC-09: _fallback_truncate() respects limit ────────────────────────────────

class TestFallbackTruncate:
    def test_short_text_unchanged(self) -> None:
        """HC-09a — text shorter than MAX_SUMMARY_CHARS returned unchanged."""
        db = AsyncMock()
        compactor = HistoryCompactor(db=db)
        text = "short text"
        result = compactor._fallback_truncate(text)
        assert result == text

    def test_long_text_truncated(self) -> None:
        """HC-09b — text longer than MAX_SUMMARY_CHARS is truncated."""
        db = AsyncMock()
        compactor = HistoryCompactor(db=db)
        long_text = "x" * (MAX_SUMMARY_CHARS + 500)
        result = compactor._fallback_truncate(long_text)
        assert len(result) <= MAX_SUMMARY_CHARS
        assert "[...truncated]" in result

    def test_truncated_result_within_limit(self) -> None:
        """HC-09c — result length never exceeds MAX_SUMMARY_CHARS."""
        db = AsyncMock()
        compactor = HistoryCompactor(db=db)
        text = "a" * MAX_SUMMARY_CHARS * 3
        result = compactor._fallback_truncate(text)
        assert len(result) <= MAX_SUMMARY_CHARS


# ── HC-10: _messages_to_text() role mapping ───────────────────────────────────

class TestMessagesToText:
    def test_agent_sender_maps_to_assistant(self) -> None:
        """HC-10a — sender_type='agent' maps to 'assistant:' prefix."""
        db = AsyncMock()
        compactor = HistoryCompactor(db=db)
        msg = _make_message(sender_type="agent", content="I completed the task.")
        result = compactor._messages_to_text([msg])
        assert result.startswith("assistant:")

    def test_user_sender_maps_to_user(self) -> None:
        """HC-10b — sender_type='user' maps to 'user:' prefix."""
        db = AsyncMock()
        compactor = HistoryCompactor(db=db)
        msg = _make_message(sender_type="user", content="Please fix the bug.")
        result = compactor._messages_to_text([msg])
        assert result.startswith("user:")

    def test_mixed_messages_ordered(self) -> None:
        """HC-10c — multiple messages maintain insertion order."""
        db = AsyncMock()
        compactor = HistoryCompactor(db=db)
        msgs = [
            _make_message("user", "first"),
            _make_message("agent", "second"),
            _make_message("user", "third"),
        ]
        result = compactor._messages_to_text(msgs)
        lines = result.split("\n")
        assert lines[0].startswith("user:")
        assert lines[1].startswith("assistant:")
        assert lines[2].startswith("user:")
        assert "first" in lines[0]
        assert "second" in lines[1]
        assert "third" in lines[2]
