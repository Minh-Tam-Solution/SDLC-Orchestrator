"""
=========================================================================
Unit Tests - Team Orchestrator (Sprint 178)
SDLC Orchestrator - Multi-Agent Team Engine

Version: 1.0.0
Date: February 2026
Status: ACTIVE - Sprint 178
Authority: CTO Approved (ADR-056, EP-07)

Purpose:
- Test process_next FIFO flow (claim → invoke → complete → evidence)
- Test conversation status checks (paused_by_human skip)
- Test limit exceeded handling (LimitExceededError → fail)
- Test provider failure handling (AllProvidersFailedError → fail)
- Test @mention routing (resolved agents → enqueue to target lanes)
- Test budget tracking (token usage recorded on conversation)
- Test evidence capture (agent response → GateEvidence)
- Test unexpected error handling (catch-all → queue.fail)
- Test steer mode (process_message by ID)

Test Pattern: Mock all sub-services (AgentInvoker, DB session)
per CTO implementation note #4.

Zero Mock Policy: Mocked sub-services for unit isolation
=========================================================================
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
from uuid import uuid4, UUID
from dataclasses import dataclass, field

from app.services.agent_team.team_orchestrator import (
    TeamOrchestrator,
    TeamOrchestratorError,
    ProcessingResult,
)
from app.services.agent_team.agent_invoker import (
    InvocationResult,
    AllProvidersFailedError,
)
from app.services.agent_team.conversation_tracker import LimitExceededError
from app.services.agent_team.conversation_limits import LimitViolation


# =========================================================================
# Fixtures
# =========================================================================


@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.execute = AsyncMock()
    return db


def _make_message(**overrides) -> MagicMock:
    """Create a mock AgentMessage."""
    msg = MagicMock()
    msg.id = overrides.pop("id", uuid4())
    msg.conversation_id = overrides.pop("conversation_id", uuid4())
    msg.content = overrides.pop("content", "Write a hello world function")
    msg.sender_type = overrides.pop("sender_type", "user")
    msg.sender_id = overrides.pop("sender_id", "alice")
    msg.processing_lane = overrides.pop("processing_lane", "agent:coder")
    msg.processing_status = overrides.pop("processing_status", "processing")
    msg.message_type = overrides.pop("message_type", "request")
    msg.correlation_id = overrides.pop("correlation_id", uuid4())
    msg.evidence_id = None
    for k, v in overrides.items():
        setattr(msg, k, v)
    return msg


def _make_conversation(**overrides) -> MagicMock:
    """Create a mock AgentConversation."""
    conv = MagicMock()
    conv.id = overrides.pop("id", uuid4())
    conv.project_id = overrides.pop("project_id", uuid4())
    conv.agent_definition_id = overrides.pop("agent_definition_id", uuid4())
    conv.status = overrides.pop("status", "active")
    conv.session_scope = overrides.pop("session_scope", "per_sender")
    conv.queue_mode = overrides.pop("queue_mode", "queue")
    conv.total_messages = overrides.pop("total_messages", 5)
    conv.total_input_tokens = overrides.pop("total_input_tokens", 1000)
    conv.total_output_tokens = overrides.pop("total_output_tokens", 500)
    conv.total_cost_cents = overrides.pop("total_cost_cents", 10)
    for k, v in overrides.items():
        setattr(conv, k, v)
    return conv


def _make_definition(**overrides) -> MagicMock:
    """Create a mock AgentDefinition."""
    defn = MagicMock()
    defn.id = overrides.pop("id", uuid4())
    defn.agent_name = overrides.pop("agent_name", "coder-alpha")
    defn.sdlc_role = overrides.pop("sdlc_role", "coder")
    defn.system_prompt = overrides.pop("system_prompt", "You are a code generator.")
    defn.provider = overrides.pop("provider", "ollama")
    defn.model = overrides.pop("model", "qwen3-coder:30b")
    defn.config = overrides.pop("config", None)
    defn.is_active = overrides.pop("is_active", True)
    for k, v in overrides.items():
        setattr(defn, k, v)
    return defn


def _make_invocation_result(**overrides) -> InvocationResult:
    """Create an InvocationResult."""
    return InvocationResult(
        success=overrides.get("success", True),
        content=overrides.get("content", "def hello():\n    print('hello')"),
        provider_used=overrides.get("provider_used", "ollama"),
        model_used=overrides.get("model_used", "qwen3-coder:30b"),
        input_tokens=overrides.get("input_tokens", 100),
        output_tokens=overrides.get("output_tokens", 50),
        latency_ms=overrides.get("latency_ms", 500),
        cost_cents=overrides.get("cost_cents", 0),
    )


def _make_mention_result(has_mentions=False, resolved=None, unresolved=None):
    """Create a mock MentionRouteResult."""
    result = MagicMock()
    result.has_mentions = has_mentions
    result.resolved_agents = resolved or []
    result.unresolved = unresolved or []
    return result


def _make_orchestrator_with_mocks(mock_db):
    """
    Create a TeamOrchestrator with all sub-services mocked.

    Returns (orchestrator, mocks_dict) for test assertions.
    """
    orchestrator = TeamOrchestrator(mock_db, redis=None)

    # Mock sub-services
    orchestrator.queue = AsyncMock()
    orchestrator.tracker = AsyncMock()
    orchestrator.registry = AsyncMock()
    orchestrator.mention_parser = AsyncMock()
    orchestrator.evidence_collector = AsyncMock()

    return orchestrator


# =========================================================================
# TestProcessNext — FIFO processing (5 tests)
# =========================================================================


class TestProcessNext:
    """Tests for process_next: the main FIFO entry point."""

    @pytest.mark.asyncio
    async def test_empty_lane_returns_none(self, mock_db):
        """When no messages are pending, process_next returns None."""
        orch = _make_orchestrator_with_mocks(mock_db)
        orch.queue.claim_next = AsyncMock(return_value=None)

        result = await orch.process_next("agent:coder")

        assert result is None
        orch.queue.claim_next.assert_awaited_once_with("agent:coder")

    @pytest.mark.asyncio
    async def test_fifo_success_flow(self, mock_db):
        """Full FIFO success: claim → invoke → complete → evidence → result."""
        orch = _make_orchestrator_with_mocks(mock_db)

        msg = _make_message()
        conv = _make_conversation(id=msg.conversation_id)
        defn = _make_definition(id=conv.agent_definition_id)
        inv_result = _make_invocation_result()
        response_msg = _make_message(sender_type="agent", sender_id="coder-alpha")
        evidence = MagicMock()
        evidence.id = uuid4()

        # Wire up mocks
        orch.queue.claim_next = AsyncMock(return_value=msg)
        orch.tracker.get = AsyncMock(return_value=conv)
        orch.tracker.check_limits = AsyncMock()
        orch.tracker.record_token_usage = AsyncMock()
        orch.tracker.increment_message_count = AsyncMock()
        orch.registry.get_active = AsyncMock(return_value=defn)
        orch.mention_parser.parse_and_route = AsyncMock(
            return_value=_make_mention_result(has_mentions=False)
        )
        orch.queue.enqueue = AsyncMock(return_value=response_msg)
        orch.queue.complete = AsyncMock()
        orch.evidence_collector.capture_message = AsyncMock(return_value=evidence)

        # Mock history query
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result

        with patch.object(orch, "_build_invoker") as mock_build:
            mock_invoker = AsyncMock()
            mock_invoker.invoke = AsyncMock(return_value=inv_result)
            mock_build.return_value = mock_invoker

            result = await orch.process_next("agent:coder")

        assert result is not None
        assert result.success is True
        assert result.provider_used == "ollama"
        assert result.tokens_used == 150  # 100 + 50
        orch.queue.complete.assert_awaited_once()
        orch.tracker.record_token_usage.assert_awaited_once()
        orch.tracker.increment_message_count.assert_awaited_once()
        orch.evidence_collector.capture_message.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_paused_conversation_skips(self, mock_db):
        """Paused conversation should skip processing and re-queue message."""
        orch = _make_orchestrator_with_mocks(mock_db)

        msg = _make_message()
        conv = _make_conversation(
            id=msg.conversation_id,
            status="paused_by_human",
        )

        orch.queue.claim_next = AsyncMock(return_value=msg)
        orch.tracker.get = AsyncMock(return_value=conv)

        result = await orch.process_next("agent:coder")

        assert result is not None
        assert result.success is False
        assert result.skipped_reason == "conversation_paused"
        # Message should be set back to pending
        assert msg.processing_status == "pending"

    @pytest.mark.asyncio
    async def test_limit_exceeded_fails_message(self, mock_db):
        """LimitExceededError should cause queue.fail and return error result."""
        orch = _make_orchestrator_with_mocks(mock_db)

        msg = _make_message()
        conv = _make_conversation(id=msg.conversation_id)

        orch.queue.claim_next = AsyncMock(return_value=msg)
        orch.tracker.get = AsyncMock(return_value=conv)
        orch.tracker.check_limits = AsyncMock(
            side_effect=LimitExceededError(
                LimitViolation.MAX_MESSAGES, "Max messages exceeded: 100/100"
            )
        )

        result = await orch.process_next("agent:coder")

        assert result is not None
        assert result.success is False
        assert result.skipped_reason == "limit_exceeded"
        assert "Max messages" in result.error
        orch.queue.fail.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_provider_failure_fails_message(self, mock_db):
        """AllProvidersFailedError should cause queue.fail."""
        orch = _make_orchestrator_with_mocks(mock_db)

        msg = _make_message()
        conv = _make_conversation(id=msg.conversation_id)
        defn = _make_definition(id=conv.agent_definition_id)

        orch.queue.claim_next = AsyncMock(return_value=msg)
        orch.tracker.get = AsyncMock(return_value=conv)
        orch.tracker.check_limits = AsyncMock()
        orch.registry.get_active = AsyncMock(return_value=defn)
        orch.mention_parser.parse_and_route = AsyncMock(
            return_value=_make_mention_result()
        )

        # Mock history query
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result

        with patch.object(orch, "_build_invoker") as mock_build:
            mock_invoker = AsyncMock()
            mock_invoker.invoke = AsyncMock(
                side_effect=AllProvidersFailedError([
                    ("ollama", MagicMock(value="timeout"), "Connection timeout"),
                ])
            )
            mock_build.return_value = mock_invoker

            result = await orch.process_next("agent:coder")

        assert result is not None
        assert result.success is False
        assert "All providers failed" in result.error
        orch.queue.fail.assert_awaited_once()


# =========================================================================
# TestMentionRouting — @mention → enqueue to target lane (3 tests)
# =========================================================================


class TestMentionRouting:
    """Tests for @mention routing within _process."""

    @pytest.mark.asyncio
    async def test_mention_routes_to_target_lane(self, mock_db):
        """Resolved @mention should enqueue message to target agent's lane."""
        orch = _make_orchestrator_with_mocks(mock_db)

        msg = _make_message(content="@reviewer please check this")
        conv = _make_conversation(id=msg.conversation_id)
        defn = _make_definition(id=conv.agent_definition_id)
        inv_result = _make_invocation_result()
        response_msg = _make_message(sender_type="agent")
        evidence = MagicMock()
        evidence.id = uuid4()

        reviewer_agent = MagicMock()
        reviewer_agent.agent_name = "reviewer-beta"

        orch.queue.claim_next = AsyncMock(return_value=msg)
        orch.tracker.get = AsyncMock(return_value=conv)
        orch.tracker.check_limits = AsyncMock()
        orch.tracker.record_token_usage = AsyncMock()
        orch.tracker.increment_message_count = AsyncMock()
        orch.registry.get_active = AsyncMock(return_value=defn)
        orch.mention_parser.parse_and_route = AsyncMock(
            return_value=_make_mention_result(
                has_mentions=True,
                resolved=[reviewer_agent],
            )
        )
        orch.queue.enqueue = AsyncMock(return_value=response_msg)
        orch.queue.complete = AsyncMock()
        orch.evidence_collector.capture_message = AsyncMock(return_value=evidence)

        # Mock history
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result

        with patch.object(orch, "_build_invoker") as mock_build:
            mock_invoker = AsyncMock()
            mock_invoker.invoke = AsyncMock(return_value=inv_result)
            mock_build.return_value = mock_invoker

            result = await orch.process_next("agent:coder")

        assert result.success is True
        assert "reviewer-beta" in result.mentions_routed
        # enqueue called at least twice: response + mention
        assert orch.queue.enqueue.await_count >= 2

    @pytest.mark.asyncio
    async def test_no_mentions_skips_routing(self, mock_db):
        """When no @mentions, mentions_routed should be empty."""
        orch = _make_orchestrator_with_mocks(mock_db)

        msg = _make_message(content="Just a normal message")
        conv = _make_conversation(id=msg.conversation_id)
        defn = _make_definition(id=conv.agent_definition_id)
        inv_result = _make_invocation_result()
        response_msg = _make_message(sender_type="agent")

        orch.queue.claim_next = AsyncMock(return_value=msg)
        orch.tracker.get = AsyncMock(return_value=conv)
        orch.tracker.check_limits = AsyncMock()
        orch.tracker.record_token_usage = AsyncMock()
        orch.tracker.increment_message_count = AsyncMock()
        orch.registry.get_active = AsyncMock(return_value=defn)
        orch.mention_parser.parse_and_route = AsyncMock(
            return_value=_make_mention_result(has_mentions=False)
        )
        orch.queue.enqueue = AsyncMock(return_value=response_msg)
        orch.queue.complete = AsyncMock()
        orch.evidence_collector.capture_message = AsyncMock(return_value=None)

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result

        with patch.object(orch, "_build_invoker") as mock_build:
            mock_invoker = AsyncMock()
            mock_invoker.invoke = AsyncMock(return_value=inv_result)
            mock_build.return_value = mock_invoker

            result = await orch.process_next("agent:coder")

        assert result.success is True
        assert result.mentions_routed == []

    @pytest.mark.asyncio
    async def test_multiple_mentions_all_routed(self, mock_db):
        """Multiple resolved @mentions should all be routed."""
        orch = _make_orchestrator_with_mocks(mock_db)

        msg = _make_message(content="@reviewer @tester check this")
        conv = _make_conversation(id=msg.conversation_id)
        defn = _make_definition(id=conv.agent_definition_id)
        inv_result = _make_invocation_result()
        response_msg = _make_message(sender_type="agent")
        evidence = MagicMock()
        evidence.id = uuid4()

        reviewer = MagicMock()
        reviewer.agent_name = "reviewer"
        tester = MagicMock()
        tester.agent_name = "tester"

        orch.queue.claim_next = AsyncMock(return_value=msg)
        orch.tracker.get = AsyncMock(return_value=conv)
        orch.tracker.check_limits = AsyncMock()
        orch.tracker.record_token_usage = AsyncMock()
        orch.tracker.increment_message_count = AsyncMock()
        orch.registry.get_active = AsyncMock(return_value=defn)
        orch.mention_parser.parse_and_route = AsyncMock(
            return_value=_make_mention_result(
                has_mentions=True,
                resolved=[reviewer, tester],
            )
        )
        orch.queue.enqueue = AsyncMock(return_value=response_msg)
        orch.queue.complete = AsyncMock()
        orch.evidence_collector.capture_message = AsyncMock(return_value=evidence)

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result

        with patch.object(orch, "_build_invoker") as mock_build:
            mock_invoker = AsyncMock()
            mock_invoker.invoke = AsyncMock(return_value=inv_result)
            mock_build.return_value = mock_invoker

            result = await orch.process_next("agent:coder")

        assert result.success is True
        assert len(result.mentions_routed) == 2
        assert "reviewer" in result.mentions_routed
        assert "tester" in result.mentions_routed


# =========================================================================
# TestBudgetTracking — Token usage + evidence (3 tests)
# =========================================================================


class TestBudgetTracking:
    """Tests for token usage recording and evidence capture."""

    @pytest.mark.asyncio
    async def test_token_usage_recorded(self, mock_db):
        """record_token_usage should be called with correct token counts."""
        orch = _make_orchestrator_with_mocks(mock_db)

        msg = _make_message()
        conv = _make_conversation(id=msg.conversation_id)
        defn = _make_definition(id=conv.agent_definition_id)
        inv_result = _make_invocation_result(input_tokens=200, output_tokens=300, cost_cents=5)
        response_msg = _make_message(sender_type="agent")

        orch.queue.claim_next = AsyncMock(return_value=msg)
        orch.tracker.get = AsyncMock(return_value=conv)
        orch.tracker.check_limits = AsyncMock()
        orch.tracker.record_token_usage = AsyncMock()
        orch.tracker.increment_message_count = AsyncMock()
        orch.registry.get_active = AsyncMock(return_value=defn)
        orch.mention_parser.parse_and_route = AsyncMock(
            return_value=_make_mention_result()
        )
        orch.queue.enqueue = AsyncMock(return_value=response_msg)
        orch.queue.complete = AsyncMock()
        orch.evidence_collector.capture_message = AsyncMock(return_value=None)

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result

        with patch.object(orch, "_build_invoker") as mock_build:
            mock_invoker = AsyncMock()
            mock_invoker.invoke = AsyncMock(return_value=inv_result)
            mock_build.return_value = mock_invoker

            result = await orch.process_next("agent:coder")

        assert result.tokens_used == 500  # 200 + 300
        assert result.cost_cents == 5
        orch.tracker.record_token_usage.assert_awaited_once_with(
            conversation_id=conv.id,
            input_tokens=200,
            output_tokens=300,
            cost_cents=5,
        )

    @pytest.mark.asyncio
    async def test_message_count_incremented(self, mock_db):
        """increment_message_count should be called after successful invoke."""
        orch = _make_orchestrator_with_mocks(mock_db)

        msg = _make_message()
        conv = _make_conversation(id=msg.conversation_id)
        defn = _make_definition(id=conv.agent_definition_id)
        inv_result = _make_invocation_result()
        response_msg = _make_message(sender_type="agent")

        orch.queue.claim_next = AsyncMock(return_value=msg)
        orch.tracker.get = AsyncMock(return_value=conv)
        orch.tracker.check_limits = AsyncMock()
        orch.tracker.record_token_usage = AsyncMock()
        orch.tracker.increment_message_count = AsyncMock()
        orch.registry.get_active = AsyncMock(return_value=defn)
        orch.mention_parser.parse_and_route = AsyncMock(
            return_value=_make_mention_result()
        )
        orch.queue.enqueue = AsyncMock(return_value=response_msg)
        orch.queue.complete = AsyncMock()
        orch.evidence_collector.capture_message = AsyncMock(return_value=None)

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result

        with patch.object(orch, "_build_invoker") as mock_build:
            mock_invoker = AsyncMock()
            mock_invoker.invoke = AsyncMock(return_value=inv_result)
            mock_build.return_value = mock_invoker

            await orch.process_next("agent:coder")

        orch.tracker.increment_message_count.assert_awaited_once_with(conv.id)

    @pytest.mark.asyncio
    async def test_evidence_captured_for_agent_response(self, mock_db):
        """Evidence collector should be called with response message."""
        orch = _make_orchestrator_with_mocks(mock_db)

        msg = _make_message(sender_type="user", sender_id="alice")
        conv = _make_conversation(id=msg.conversation_id)
        defn = _make_definition(id=conv.agent_definition_id, agent_name="coder-alpha")
        inv_result = _make_invocation_result()
        response_msg = _make_message(sender_type="agent", sender_id="coder-alpha")
        evidence = MagicMock()
        evidence.id = uuid4()

        orch.queue.claim_next = AsyncMock(return_value=msg)
        orch.tracker.get = AsyncMock(return_value=conv)
        orch.tracker.check_limits = AsyncMock()
        orch.tracker.record_token_usage = AsyncMock()
        orch.tracker.increment_message_count = AsyncMock()
        orch.registry.get_active = AsyncMock(return_value=defn)
        orch.mention_parser.parse_and_route = AsyncMock(
            return_value=_make_mention_result()
        )
        orch.queue.enqueue = AsyncMock(return_value=response_msg)
        orch.queue.complete = AsyncMock()
        orch.evidence_collector.capture_message = AsyncMock(return_value=evidence)

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result

        with patch.object(orch, "_build_invoker") as mock_build:
            mock_invoker = AsyncMock()
            mock_invoker.invoke = AsyncMock(return_value=inv_result)
            mock_build.return_value = mock_invoker

            result = await orch.process_next("agent:coder")

        assert result.evidence_id == evidence.id
        orch.evidence_collector.capture_message.assert_awaited_once_with(
            message=response_msg,
            agent_name="coder-alpha",
            on_behalf_of="user:alice",
        )


# =========================================================================
# TestDeadLetterHandling — Error → queue.fail (2 tests)
# =========================================================================


class TestDeadLetterHandling:
    """Tests for error handling and dead-letter scenarios."""

    @pytest.mark.asyncio
    async def test_provider_failure_calls_queue_fail(self, mock_db):
        """AllProvidersFailedError should call queue.fail with reason."""
        orch = _make_orchestrator_with_mocks(mock_db)

        msg = _make_message()
        conv = _make_conversation(id=msg.conversation_id)
        defn = _make_definition(id=conv.agent_definition_id)

        orch.queue.claim_next = AsyncMock(return_value=msg)
        orch.tracker.get = AsyncMock(return_value=conv)
        orch.tracker.check_limits = AsyncMock()
        orch.registry.get_active = AsyncMock(return_value=defn)
        orch.mention_parser.parse_and_route = AsyncMock(
            return_value=_make_mention_result()
        )

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result

        with patch.object(orch, "_build_invoker") as mock_build:
            mock_invoker = AsyncMock()
            mock_invoker.invoke = AsyncMock(
                side_effect=AllProvidersFailedError([
                    ("ollama", MagicMock(value="timeout"), "timeout"),
                ])
            )
            mock_build.return_value = mock_invoker

            result = await orch.process_next("agent:coder")

        assert result.success is False
        orch.queue.fail.assert_awaited_once()
        call_kwargs = orch.queue.fail.call_args
        assert call_kwargs[1].get("failover_reason") == "all_providers_failed" or \
               (len(call_kwargs[0]) >= 1 and call_kwargs[0][0] == msg.id)

    @pytest.mark.asyncio
    async def test_unexpected_exception_catches_and_fails(self, mock_db):
        """Unexpected exceptions should be caught, logged, and queue.fail called."""
        orch = _make_orchestrator_with_mocks(mock_db)

        msg = _make_message()
        conv = _make_conversation(id=msg.conversation_id)

        orch.queue.claim_next = AsyncMock(return_value=msg)
        orch.tracker.get = AsyncMock(return_value=conv)
        # check_limits raises unexpected error
        orch.tracker.check_limits = AsyncMock(
            side_effect=RuntimeError("Unexpected DB error")
        )

        result = await orch.process_next("agent:coder")

        assert result.success is False
        assert "Unexpected DB error" in result.error
        orch.queue.fail.assert_awaited_once()


# =========================================================================
# TestMessageContext — LLM context building (2 tests)
# =========================================================================


class TestMessageContext:
    """Tests for _build_llm_context and process_message (steer)."""

    @pytest.mark.asyncio
    async def test_steer_mode_process_by_id(self, mock_db):
        """process_message should process a specific message by ID."""
        orch = _make_orchestrator_with_mocks(mock_db)

        msg = _make_message()
        conv = _make_conversation(id=msg.conversation_id)
        defn = _make_definition(id=conv.agent_definition_id)
        inv_result = _make_invocation_result()
        response_msg = _make_message(sender_type="agent")

        # Mock DB execute for process_message lookup
        mock_result_msg = MagicMock()
        mock_result_msg.scalar_one_or_none.return_value = msg

        # Mock DB execute for history query
        mock_result_history = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result_history.scalars.return_value = mock_scalars

        mock_db.execute = AsyncMock(
            side_effect=[mock_result_msg, mock_result_history]
        )

        orch.tracker.get = AsyncMock(return_value=conv)
        orch.tracker.check_limits = AsyncMock()
        orch.tracker.record_token_usage = AsyncMock()
        orch.tracker.increment_message_count = AsyncMock()
        orch.registry.get_active = AsyncMock(return_value=defn)
        orch.mention_parser.parse_and_route = AsyncMock(
            return_value=_make_mention_result()
        )
        orch.queue.enqueue = AsyncMock(return_value=response_msg)
        orch.queue.complete = AsyncMock()
        orch.evidence_collector.capture_message = AsyncMock(return_value=None)

        with patch.object(orch, "_build_invoker") as mock_build:
            mock_invoker = AsyncMock()
            mock_invoker.invoke = AsyncMock(return_value=inv_result)
            mock_build.return_value = mock_invoker

            result = await orch.process_message(msg.id)

        assert result.success is True
        assert msg.processing_status == "processing"

    @pytest.mark.asyncio
    async def test_steer_mode_not_found_raises(self, mock_db):
        """process_message with invalid ID should raise TeamOrchestratorError."""
        orch = _make_orchestrator_with_mocks(mock_db)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        with pytest.raises(TeamOrchestratorError, match="not found"):
            await orch.process_message(uuid4())


# =========================================================================
# TestBuildInvoker — Provider chain construction (2 tests)
# =========================================================================


class TestBuildInvoker:
    """Tests for _build_invoker method."""

    def test_ollama_primary_gets_anthropic_fallback(self, mock_db):
        """Ollama primary should get anthropic as fallback in chain."""
        orch = _make_orchestrator_with_mocks(mock_db)
        defn = _make_definition(sdlc_role="coder", config=None)

        invoker = orch._build_invoker(defn)

        assert len(invoker.provider_chain) == 2
        assert invoker.provider_chain[0].provider == "ollama"
        assert invoker.provider_chain[1].provider == "anthropic"

    def test_anthropic_primary_no_duplicate_fallback(self, mock_db):
        """If primary is already anthropic, no duplicate anthropic in chain."""
        orch = _make_orchestrator_with_mocks(mock_db)
        defn = _make_definition(
            sdlc_role="ceo",
            config={"provider": "anthropic", "model": "claude-sonnet-4-5"},
        )

        invoker = orch._build_invoker(defn)

        assert len(invoker.provider_chain) == 1
        assert invoker.provider_chain[0].provider == "anthropic"


# =========================================================================
# TestProcessingResult — Dataclass structure (1 test)
# =========================================================================


class TestProcessingResult:
    """Tests for ProcessingResult dataclass."""

    def test_processing_result_defaults(self):
        """ProcessingResult should have sensible defaults."""
        result = ProcessingResult(
            message_id=uuid4(),
            conversation_id=uuid4(),
            success=True,
        )
        assert result.provider_used is None
        assert result.mentions_routed == []
        assert result.tokens_used == 0
        assert result.cost_cents == 0
        assert result.error is None
        assert result.skipped_reason is None
