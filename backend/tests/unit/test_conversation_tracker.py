"""
=========================================================================
Unit Tests - Conversation Tracker (Sprint 177)
SDLC Orchestrator - Multi-Agent Team Engine

Version: 1.0.0
Date: February 2026
Status: ACTIVE - Sprint 177
Authority: CTO Approved (ADR-056)

Purpose:
- Test Snapshot Precedence (definition -> conversation copy)
- Test parent-child delegation depth validation
- Test loop guard enforcement (message count + budget)
- Test conversation lifecycle transitions (active -> completed/error/paused)
- Test session scoping lookup

Zero Mock Policy: Mocked AsyncSession for unit isolation
=========================================================================
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.services.agent_team.conversation_tracker import (
    ConversationTracker,
    ConversationNotFoundError,
    ConversationInactiveError,
    LimitExceededError,
    DelegationDepthError,
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
def tracker(mock_db):
    return ConversationTracker(mock_db)


def _make_definition(**overrides):
    """Create a mock AgentDefinition."""
    defn = MagicMock()
    defn.id = overrides.get("id", uuid4())
    defn.project_id = overrides.get("project_id", uuid4())
    defn.agent_name = overrides.get("agent_name", "coder-alpha")
    defn.session_scope = overrides.get("session_scope", "per-sender")
    defn.queue_mode = overrides.get("queue_mode", "queue")
    defn.max_delegation_depth = overrides.get("max_delegation_depth", 2)
    defn.config = overrides.get("config", {"max_messages": 50, "max_budget_cents": 1000})
    return defn


def _make_conversation(**overrides):
    """Create a mock AgentConversation."""
    conv = MagicMock()
    conv.id = overrides.get("id", uuid4())
    conv.project_id = overrides.get("project_id", uuid4())
    conv.agent_definition_id = overrides.get("agent_definition_id", uuid4())
    conv.parent_conversation_id = overrides.get("parent_conversation_id", None)
    conv.delegation_depth = overrides.get("delegation_depth", 0)
    conv.status = overrides.get("status", "active")
    conv.total_messages = overrides.get("total_messages", 5)
    conv.max_messages = overrides.get("max_messages", 50)
    conv.current_cost_cents = overrides.get("current_cost_cents", 100)
    conv.max_budget_cents = overrides.get("max_budget_cents", 1000)
    conv.input_tokens = overrides.get("input_tokens", 0)
    conv.output_tokens = overrides.get("output_tokens", 0)
    conv.total_tokens = overrides.get("total_tokens", 0)
    conv.metadata_ = overrides.get("metadata_", {})
    conv.completed_at = overrides.get("completed_at", None)
    return conv


def _setup_db_return(mock_db, obj):
    """Configure mock_db.execute to return obj via scalar_one_or_none."""
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = obj
    mock_db.execute.return_value = mock_result


# =========================================================================
# Create Tests
# =========================================================================


class TestCreate:
    """Tests for ConversationTracker.create."""

    @pytest.mark.asyncio
    async def test_create_snapshots_definition(self, tracker, mock_db):
        """Create copies session_scope, queue_mode, max_messages, max_budget_cents."""
        defn = _make_definition(
            session_scope="global",
            queue_mode="steer",
            config={"max_messages": 100, "max_budget_cents": 2000},
        )
        project_id = defn.project_id

        conv = await tracker.create(
            definition=defn,
            project_id=project_id,
            initiator_type="user",
            initiator_id="user-1",
            channel="web",
        )

        # Verify db.add was called with correct snapshot values
        mock_db.add.assert_called_once()
        added = mock_db.add.call_args[0][0]
        assert added.session_scope == "global"
        assert added.queue_mode == "steer"
        assert added.max_messages == 100
        assert added.max_budget_cents == 2000
        assert added.delegation_depth == 0
        assert added.status == "active"

    @pytest.mark.asyncio
    async def test_create_with_parent_sets_depth(self, tracker, mock_db):
        """Child conversation gets delegation_depth = parent + 1."""
        parent = _make_conversation(delegation_depth=1)
        _setup_db_return(mock_db, parent)

        defn = _make_definition(max_delegation_depth=5)

        conv = await tracker.create(
            definition=defn,
            project_id=defn.project_id,
            initiator_type="agent",
            initiator_id="coder-alpha",
            channel="web",
            parent_conversation_id=parent.id,
        )

        added = mock_db.add.call_args[0][0]
        assert added.delegation_depth == 2

    @pytest.mark.asyncio
    async def test_create_exceeds_delegation_depth_raises(self, tracker, mock_db):
        """Exceeding max_delegation_depth raises DelegationDepthError."""
        parent = _make_conversation(delegation_depth=2)
        _setup_db_return(mock_db, parent)

        defn = _make_definition(max_delegation_depth=2)

        with pytest.raises(DelegationDepthError):
            await tracker.create(
                definition=defn,
                project_id=defn.project_id,
                initiator_type="agent",
                initiator_id="sub-agent",
                channel="web",
                parent_conversation_id=parent.id,
            )


# =========================================================================
# Get Tests
# =========================================================================


class TestGet:
    """Tests for get and get_active."""

    @pytest.mark.asyncio
    async def test_get_not_found_raises(self, tracker, mock_db):
        _setup_db_return(mock_db, None)

        with pytest.raises(ConversationNotFoundError):
            await tracker.get(uuid4())

    @pytest.mark.asyncio
    async def test_get_returns_conversation(self, tracker, mock_db):
        conv = _make_conversation()
        _setup_db_return(mock_db, conv)

        result = await tracker.get(conv.id)
        assert result.id == conv.id

    @pytest.mark.asyncio
    async def test_get_active_inactive_raises(self, tracker, mock_db):
        conv = _make_conversation(status="completed")
        _setup_db_return(mock_db, conv)

        with pytest.raises(ConversationInactiveError):
            await tracker.get_active(conv.id)

    @pytest.mark.asyncio
    async def test_get_active_returns_active(self, tracker, mock_db):
        conv = _make_conversation(status="active")
        _setup_db_return(mock_db, conv)

        result = await tracker.get_active(conv.id)
        assert result.status == "active"


# =========================================================================
# Limit Check Tests
# =========================================================================


class TestCheckLimits:
    """Tests for loop guard enforcement."""

    @pytest.mark.asyncio
    async def test_check_limits_ok(self, tracker):
        """No exception when within limits."""
        conv = _make_conversation(total_messages=5, max_messages=50, current_cost_cents=10, max_budget_cents=1000)
        await tracker.check_limits(conv)  # Should not raise

    @pytest.mark.asyncio
    async def test_check_limits_message_exceeded(self, tracker, mock_db):
        """Exceeding max_messages raises LimitExceededError and sets status."""
        conv = _make_conversation(total_messages=50, max_messages=50)
        mock_db.flush = AsyncMock()

        with pytest.raises(LimitExceededError) as exc_info:
            await tracker.check_limits(conv)

        assert conv.status == "max_reached"
        assert "Message limit" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_check_limits_budget_exceeded(self, tracker, mock_db):
        """Exceeding max_budget_cents raises LimitExceededError."""
        conv = _make_conversation(
            total_messages=5, max_messages=50,
            current_cost_cents=1000, max_budget_cents=1000,
        )
        mock_db.flush = AsyncMock()

        with pytest.raises(LimitExceededError) as exc_info:
            await tracker.check_limits(conv)

        assert conv.status == "max_reached"
        assert "Budget" in str(exc_info.value)


# =========================================================================
# Token Usage Tests
# =========================================================================


class TestTokenUsage:
    """Tests for token and cost tracking."""

    @pytest.mark.asyncio
    async def test_increment_message_count(self, tracker, mock_db):
        conv = _make_conversation(total_messages=10)
        _setup_db_return(mock_db, conv)

        new_count = await tracker.increment_message_count(conv.id)
        assert new_count == 11
        assert conv.total_messages == 11

    @pytest.mark.asyncio
    async def test_record_token_usage(self, tracker, mock_db):
        conv = _make_conversation(
            input_tokens=100, output_tokens=50, total_tokens=150, current_cost_cents=5,
        )
        _setup_db_return(mock_db, conv)

        await tracker.record_token_usage(conv.id, input_tokens=200, output_tokens=100, cost_cents=3)

        assert conv.input_tokens == 300
        assert conv.output_tokens == 150
        assert conv.total_tokens == 450
        assert conv.current_cost_cents == 8


# =========================================================================
# Lifecycle Transition Tests
# =========================================================================


class TestLifecycleTransitions:
    """Tests for conversation status transitions."""

    @pytest.mark.asyncio
    async def test_complete(self, tracker, mock_db):
        conv = _make_conversation(status="active")
        _setup_db_return(mock_db, conv)

        result = await tracker.complete(conv.id)
        assert conv.status == "completed"
        assert conv.completed_at is not None

    @pytest.mark.asyncio
    async def test_error_with_detail(self, tracker, mock_db):
        conv = _make_conversation(status="active", metadata_={})
        _setup_db_return(mock_db, conv)

        result = await tracker.error(conv.id, error_detail="Provider timeout")
        assert conv.status == "error"
        assert conv.metadata_["last_error"] == "Provider timeout"

    @pytest.mark.asyncio
    async def test_error_truncates_detail(self, tracker, mock_db):
        conv = _make_conversation(status="active", metadata_={})
        _setup_db_return(mock_db, conv)

        long_error = "x" * 5000
        await tracker.error(conv.id, error_detail=long_error)
        assert len(conv.metadata_["last_error"]) == 2000

    @pytest.mark.asyncio
    async def test_pause(self, tracker, mock_db):
        conv = _make_conversation(status="active", metadata_={})
        _setup_db_return(mock_db, conv)

        result = await tracker.pause(conv.id, reason="CTO review needed")
        assert conv.status == "paused_by_human"
        assert conv.metadata_["pause_reason"] == "CTO review needed"

    @pytest.mark.asyncio
    async def test_resume_from_paused(self, tracker, mock_db):
        conv = _make_conversation(status="paused_by_human")
        _setup_db_return(mock_db, conv)

        result = await tracker.resume(conv.id)
        assert conv.status == "active"

    @pytest.mark.asyncio
    async def test_resume_from_active_raises(self, tracker, mock_db):
        """Only paused_by_human conversations can be resumed."""
        conv = _make_conversation(status="active")
        _setup_db_return(mock_db, conv)

        with pytest.raises(ConversationInactiveError):
            await tracker.resume(conv.id)


# =========================================================================
# Session Scoping Tests
# =========================================================================


class TestSessionScoping:
    """Tests for find_active_by_session_key."""

    @pytest.mark.asyncio
    async def test_find_active_returns_match(self, tracker, mock_db):
        conv = _make_conversation(status="active")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = conv
        mock_db.execute.return_value = mock_result

        result = await tracker.find_active_by_session_key(
            agent_definition_id=conv.agent_definition_id,
            session_scope="per-sender",
            sender_id="user-1",
        )
        assert result is not None

    @pytest.mark.asyncio
    async def test_find_active_returns_none(self, tracker, mock_db):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await tracker.find_active_by_session_key(
            agent_definition_id=uuid4(),
            session_scope="global",
            sender_id="user-1",
        )
        assert result is None
