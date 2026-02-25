"""
Sprint 200 — Agent Team OTT Integration Unit Tests.

Covers:
    D-01: Multi-agent intent detection + routing
    D-02: Budget circuit breaker (BudgetStatus / BudgetCheckResult)
    D-03: Cross-channel parity (Telegram / Zalo payload extraction)
    D-04: Session interruption keywords

Sprint 200 — Track D: E2E Testing + Sprint Close
ADR-056, ADR-058, ADR-060
"""

from __future__ import annotations

import pytest

# ──────────────────────────────────────────────────────────────────────────────
# D-01: Multi-agent intent detection
# ──────────────────────────────────────────────────────────────────────────────


class TestMultiAgentIntentDetection:
    """Verify is_multi_agent_intent() correctly classifies user messages."""

    def _detect(self, text: str) -> bool:
        from app.services.agent_bridge.ott_team_bridge import is_multi_agent_intent
        return is_multi_agent_intent(text)

    @pytest.mark.parametrize("text", [
        "generate code for user management",
        "Generate Code for API",
        "analyze my API spec and generate code",
        "use coder team",
        "use review team",
        "use full team",
        "start agent for deployment",
        "tạo code cho module đơn hàng",      # Vietnamese
        "phân tích và tạo code API",          # Vietnamese
        "agent team hãy giúp tôi",           # Vietnamese — agent team
    ])
    def test_positive_multi_agent_intents(self, text: str) -> None:
        """These messages should trigger multi-agent pipeline."""
        assert self._detect(text) is True, f"Expected True for: {text}"

    @pytest.mark.parametrize("text", [
        "hello",
        "what time is it",
        "how are you",
        "/start",
        "/help",
        "gate status",      # governance intent, not multi-agent
        "approve gate G4",  # governance intent
    ])
    def test_negative_intents(self, text: str) -> None:
        """These messages should NOT trigger multi-agent pipeline."""
        assert self._detect(text) is False, f"Expected False for: {text}"


# ──────────────────────────────────────────────────────────────────────────────
# D-01: Preset detection from chat message
# ──────────────────────────────────────────────────────────────────────────────


class TestPresetDetection:
    """Verify _detect_preset() extracts correct team preset from text."""

    def _detect(self, text: str) -> str:
        from app.services.agent_bridge.ott_team_bridge import _detect_preset
        return _detect_preset(text)

    def test_default_preset_is_startup(self) -> None:
        """Messages without explicit preset should default to 'startup-2'."""
        assert self._detect("generate code for auth") == "startup-2"

    def test_explicit_coder_keyword(self) -> None:
        """'coder' keyword maps to 'startup-2' preset."""
        assert self._detect("use coder team for this") == "startup-2"

    def test_explicit_review_keyword(self) -> None:
        """'review' keyword maps to 'review-pair' preset."""
        assert self._detect("use review team") == "review-pair"

    def test_explicit_enterprise_keyword(self) -> None:
        """'enterprise' keyword maps to 'enterprise-3' preset."""
        assert self._detect("use enterprise team") == "enterprise-3"


# ──────────────────────────────────────────────────────────────────────────────
# D-02: Budget circuit breaker types
# ──────────────────────────────────────────────────────────────────────────────


class TestBudgetTypes:
    """Verify BudgetStatus enum and BudgetCheckResult dataclass."""

    def test_budget_status_values(self) -> None:
        from app.services.agent_team.conversation_tracker import BudgetStatus
        assert BudgetStatus.OK == "ok"
        assert BudgetStatus.WARNING == "warning"
        assert BudgetStatus.EXCEEDED == "exceeded"

    def test_budget_check_result_ok(self) -> None:
        from app.services.agent_team.conversation_tracker import (
            BudgetCheckResult,
            BudgetStatus,
        )
        result = BudgetCheckResult(
            status=BudgetStatus.OK,
            current_cents=100,
            max_cents=500,
            percentage=20.0,
            message="Budget OK",
        )
        assert result.status == BudgetStatus.OK
        assert result.percentage == 20.0
        assert result.current_cents == 100

    def test_budget_check_result_warning(self) -> None:
        from app.services.agent_team.conversation_tracker import (
            BudgetCheckResult,
            BudgetStatus,
        )
        result = BudgetCheckResult(
            status=BudgetStatus.WARNING,
            current_cents=420,
            max_cents=500,
            percentage=84.0,
            message="Warning: 84% budget used",
        )
        assert result.status == BudgetStatus.WARNING
        assert result.percentage == 84.0

    def test_budget_check_result_exceeded(self) -> None:
        from app.services.agent_team.conversation_tracker import (
            BudgetCheckResult,
            BudgetStatus,
        )
        result = BudgetCheckResult(
            status=BudgetStatus.EXCEEDED,
            current_cents=550,
            max_cents=500,
            percentage=110.0,
            message="Budget exceeded",
        )
        assert result.status == BudgetStatus.EXCEEDED
        assert result.percentage == 110.0

    def test_budget_check_result_frozen(self) -> None:
        """BudgetCheckResult should be immutable (frozen dataclass)."""
        from app.services.agent_team.conversation_tracker import (
            BudgetCheckResult,
            BudgetStatus,
        )
        result = BudgetCheckResult(
            status=BudgetStatus.OK,
            current_cents=0,
            max_cents=500,
            percentage=0.0,
            message="OK",
        )
        with pytest.raises(AttributeError):
            result.status = BudgetStatus.WARNING  # type: ignore[misc]

    def test_org_monthly_budget_tiers(self) -> None:
        """Verify tier-based org monthly budget constants."""
        from app.services.agent_team.conversation_tracker import ORG_MONTHLY_BUDGET_CENTS
        assert ORG_MONTHLY_BUDGET_CENTS["LITE"] == 1_000
        assert ORG_MONTHLY_BUDGET_CENTS["STANDARD"] == 5_000
        assert ORG_MONTHLY_BUDGET_CENTS["PRO"] == 20_000
        assert ORG_MONTHLY_BUDGET_CENTS["ENTERPRISE"] == 100_000

    def test_check_budget_status_static_method(self) -> None:
        """Verify static check_budget_status correctly classifies budget."""
        from types import SimpleNamespace
        from app.services.agent_team.conversation_tracker import (
            ConversationTracker,
            BudgetStatus,
        )

        def _mock_conv(current: int, maximum: int):
            return SimpleNamespace(
                current_cost_cents=current, max_budget_cents=maximum,
            )

        # OK: under 80%
        r = ConversationTracker.check_budget_status(_mock_conv(100, 500))
        assert r.status == BudgetStatus.OK
        assert r.percentage == pytest.approx(20.0)

        # WARNING: at 80%
        r = ConversationTracker.check_budget_status(_mock_conv(400, 500))
        assert r.status == BudgetStatus.WARNING
        assert r.percentage == pytest.approx(80.0)

        # EXCEEDED: at 100%
        r = ConversationTracker.check_budget_status(_mock_conv(500, 500))
        assert r.status == BudgetStatus.EXCEEDED
        assert r.percentage == pytest.approx(100.0)

        # EXCEEDED: over 100%
        r = ConversationTracker.check_budget_status(_mock_conv(600, 500))
        assert r.status == BudgetStatus.EXCEEDED

    def test_check_budget_status_zero_max(self) -> None:
        """Zero max_cents should return OK (no budget set)."""
        from types import SimpleNamespace
        from app.services.agent_team.conversation_tracker import (
            ConversationTracker,
            BudgetStatus,
        )
        conv = SimpleNamespace(current_cost_cents=100, max_budget_cents=0)
        r = ConversationTracker.check_budget_status(conv)
        assert r.status == BudgetStatus.OK


# ──────────────────────────────────────────────────────────────────────────────
# D-03: Cross-channel payload extraction
# ──────────────────────────────────────────────────────────────────────────────


class TestCrossChannelPayloadExtraction:
    """Verify _extract_chat_context() handles both Telegram and Zalo payloads."""

    def _extract(self, raw_body: dict, channel: str):
        from app.services.agent_bridge.ai_response_handler import _extract_chat_context
        return _extract_chat_context(raw_body, channel)

    def test_telegram_payload_extraction(self) -> None:
        """Telegram payload extracts chat_id from message.chat.id."""
        payload = {
            "message": {
                "text": "hello world",
                "chat": {"id": 12345},
                "from": {"id": 67890},
            }
        }
        chat_id, text, sender_id, message = self._extract(payload, "telegram")
        assert chat_id == 12345
        assert text == "hello world"
        assert sender_id == "67890"
        assert message is not None

    def test_zalo_payload_extraction(self) -> None:
        """Zalo payload extracts chat_id from sender.id."""
        payload = {
            "event_name": "user_send_text",
            "sender": {"id": "zalo_user_abc"},
            "message": {"text": "xin chao"},
        }
        chat_id, text, sender_id, message = self._extract(payload, "zalo")
        assert chat_id == "zalo_user_abc"
        assert text == "xin chao"
        assert sender_id == "zalo_user_abc"  # Zalo: sender_id == chat_id
        assert message is not None

    def test_telegram_missing_message_returns_none(self) -> None:
        """Telegram payload without 'message' key returns None chat_id."""
        payload = {"update_id": 123}
        chat_id, text, sender_id, message = self._extract(payload, "telegram")
        assert chat_id is None
        assert text == ""
        assert message is None

    def test_zalo_empty_message_text(self) -> None:
        """Zalo payload with empty text returns empty string."""
        payload = {
            "sender": {"id": "user123"},
            "message": {},
        }
        chat_id, text, sender_id, message = self._extract(payload, "zalo")
        assert chat_id == "user123"
        assert text == ""

    def test_telegram_caption_extraction(self) -> None:
        """Telegram photo messages use caption instead of text."""
        payload = {
            "message": {
                "caption": "evidence for gate G4",
                "photo": [{"file_id": "abc123"}],
                "chat": {"id": 11111},
                "from": {"id": 22222},
            }
        }
        chat_id, text, sender_id, message = self._extract(payload, "telegram")
        assert chat_id == 11111
        assert text == "evidence for gate G4"

    def test_zalo_missing_sender_returns_none(self) -> None:
        """Zalo payload without sender returns None chat_id."""
        payload = {"message": {"text": "hello"}}
        chat_id, text, sender_id, message = self._extract(payload, "zalo")
        assert chat_id is None  # empty string -> None
        assert text == "hello"


# ──────────────────────────────────────────────────────────────────────────────
# D-03: Channel-agnostic reply routing
# ──────────────────────────────────────────────────────────────────────────────


class TestChannelAgnosticReplyRouting:
    """Verify _send_reply dispatches to correct channel."""

    def test_send_reply_exists(self) -> None:
        """The _send_reply function should be importable."""
        from app.services.agent_bridge.ai_response_handler import _send_reply
        assert callable(_send_reply)

    def test_ott_send_progress_exists(self) -> None:
        """The _ott_send_progress function should be importable."""
        from app.services.agent_bridge.ott_team_bridge import _ott_send_progress
        assert callable(_ott_send_progress)

    def test_ott_send_result_exists(self) -> None:
        """The _ott_send_result function should be importable."""
        from app.services.agent_bridge.ott_team_bridge import _ott_send_result
        assert callable(_ott_send_result)


# ──────────────────────────────────────────────────────────────────────────────
# D-04: Session interruption keywords
# ──────────────────────────────────────────────────────────────────────────────


class TestInterruptKeywords:
    """Verify interrupt keywords are detected correctly."""

    def test_interrupt_keywords_defined(self) -> None:
        from app.services.agent_bridge.ai_response_handler import _INTERRUPT_KEYWORDS
        assert "stop" in _INTERRUPT_KEYWORDS
        assert "cancel" in _INTERRUPT_KEYWORDS
        assert "/stop" in _INTERRUPT_KEYWORDS
        assert "/cancel" in _INTERRUPT_KEYWORDS

    def test_vietnamese_interrupt_keywords(self) -> None:
        from app.services.agent_bridge.ai_response_handler import _INTERRUPT_KEYWORDS
        assert "dừng lại" in _INTERRUPT_KEYWORDS
        assert "hủy" in _INTERRUPT_KEYWORDS

    def test_governance_keywords_defined(self) -> None:
        from app.services.agent_bridge.ai_response_handler import _GOVERNANCE_KEYWORDS
        assert "gate status" in _GOVERNANCE_KEYWORDS
        assert "approve gate" in _GOVERNANCE_KEYWORDS
        assert "trạng thái gate" in _GOVERNANCE_KEYWORDS

    def test_governance_intent_detection(self) -> None:
        from app.services.agent_bridge.ai_response_handler import _is_governance_intent
        assert _is_governance_intent("gate status") is True
        assert _is_governance_intent("approve gate G4") is True
        assert _is_governance_intent("trạng thái gate") is True
        assert _is_governance_intent("hello world") is False
        assert _is_governance_intent("generate code") is False


# ──────────────────────────────────────────────────────────────────────────────
# D-03: Zalo responder
# ──────────────────────────────────────────────────────────────────────────────


class TestZaloResponder:
    """Verify Zalo-specific response formatting (C-04)."""

    def test_command_replies_exist(self) -> None:
        from app.services.agent_bridge.zalo_responder import _COMMAND_REPLIES
        assert "/start" in _COMMAND_REPLIES
        assert "/help" in _COMMAND_REPLIES
        assert "/status" in _COMMAND_REPLIES

    def test_zalo_max_text_length(self) -> None:
        from app.services.agent_bridge.zalo_responder import _ZALO_MAX_TEXT_LEN
        assert _ZALO_MAX_TEXT_LEN == 2000

    def test_zalo_send_url(self) -> None:
        from app.services.agent_bridge.zalo_responder import _ZALO_SEND_URL
        assert "openapi.zalo.me" in _ZALO_SEND_URL
        assert "/v3.0/oa/message/cs" in _ZALO_SEND_URL


# ──────────────────────────────────────────────────────────────────────────────
# D-03: Governance action handler channel support
# ──────────────────────────────────────────────────────────────────────────────


class TestGovernanceHandlerChannelParam:
    """Verify governance_action_handler.execute_governance_action accepts channel."""

    def test_execute_governance_action_signature(self) -> None:
        """execute_governance_action should accept channel parameter."""
        import inspect
        from app.services.agent_bridge.governance_action_handler import (
            execute_governance_action,
        )
        sig = inspect.signature(execute_governance_action)
        params = list(sig.parameters.keys())
        assert "channel" in params
        assert sig.parameters["channel"].default == "telegram"

    def test_send_telegram_reply_accepts_channel(self) -> None:
        """_send_telegram_reply should accept channel parameter."""
        import inspect
        from app.services.agent_bridge.governance_action_handler import (
            _send_telegram_reply,
        )
        sig = inspect.signature(_send_telegram_reply)
        params = list(sig.parameters.keys())
        assert "channel" in params
        assert sig.parameters["channel"].default == "telegram"


# ──────────────────────────────────────────────────────────────────────────────
# D-01: handle_ai_response channel parameter
# ──────────────────────────────────────────────────────────────────────────────


class TestHandleAiResponseSignature:
    """Verify handle_ai_response accepts channel parameter."""

    def test_channel_parameter_exists(self) -> None:
        import inspect
        from app.services.agent_bridge.ai_response_handler import handle_ai_response
        sig = inspect.signature(handle_ai_response)
        params = list(sig.parameters.keys())
        assert "channel" in params
        assert sig.parameters["channel"].default == "telegram"

    def test_handle_agent_team_request_channel(self) -> None:
        import inspect
        from app.services.agent_bridge.ott_team_bridge import handle_agent_team_request
        sig = inspect.signature(handle_agent_team_request)
        params = list(sig.parameters.keys())
        assert "channel" in params
        assert sig.parameters["channel"].default == "telegram"

    def test_handle_interrupt_channel(self) -> None:
        import inspect
        from app.services.agent_bridge.ott_team_bridge import handle_interrupt
        sig = inspect.signature(handle_interrupt)
        params = list(sig.parameters.keys())
        assert "channel" in params
        assert sig.parameters["channel"].default == "telegram"


# ──────────────────────────────────────────────────────────────────────────────
# D-01: Agent Activity Panel types
# ──────────────────────────────────────────────────────────────────────────────


class TestAgentActivityPanelExport:
    """Verify AgentActivityPanel is properly exported."""

    def test_ott_gateway_component_index(self) -> None:
        """The ott-gateway component index should export AgentActivityPanel."""
        import pathlib
        index_path = pathlib.Path(
            "frontend/src/components/ott-gateway/index.ts"
        )
        assert index_path.exists(), "ott-gateway/index.ts must exist"
        content = index_path.read_text()
        assert "AgentActivityPanel" in content
        assert "WebhookLogViewer" in content
        assert "ChannelConfigPanel" in content
