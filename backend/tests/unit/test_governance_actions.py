"""
Unit Tests — Sprint 199 Track A: Chat Governance Actions.

Tests the full governance action pipeline:
    1. Governance intent detection (A-04)
    2. Governance action handler (A-01, A-02)
    3. Magic Link verification endpoint (A-05)
    4. Response formatting (A-06)

All external dependencies mocked:
    - GateService (DB queries)
    - MagicLinkService (Redis token storage)
    - Telegram Bot API (httpx.AsyncClient)
    - Ollama (LLM function calling)

Sprint 199 — Track A: Gate Actions via Chat
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Optional
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest

# ──────────────────────────────────────────────────────────────────────────────
# Test: Governance Intent Detection (A-04)
# ──────────────────────────────────────────────────────────────────────────────


class TestGovernanceIntentDetection:
    """Test _is_governance_intent() keyword matching."""

    def test_gate_status_english(self) -> None:
        from app.services.agent_bridge.ai_response_handler import _is_governance_intent
        assert _is_governance_intent("gate status for project 5") is True

    def test_gate_status_vietnamese(self) -> None:
        from app.services.agent_bridge.ai_response_handler import _is_governance_intent
        assert _is_governance_intent("trạng thái gate của dự án 5") is True

    def test_approve_english(self) -> None:
        from app.services.agent_bridge.ai_response_handler import _is_governance_intent
        assert _is_governance_intent("approve gate G2") is True

    def test_approve_vietnamese(self) -> None:
        from app.services.agent_bridge.ai_response_handler import _is_governance_intent
        assert _is_governance_intent("duyệt gate G3") is True

    def test_create_project_english(self) -> None:
        from app.services.agent_bridge.ai_response_handler import _is_governance_intent
        assert _is_governance_intent("create project MyApp") is True

    def test_create_project_vietnamese(self) -> None:
        from app.services.agent_bridge.ai_response_handler import _is_governance_intent
        assert _is_governance_intent("tạo dự án mới") is True

    def test_submit_evidence(self) -> None:
        from app.services.agent_bridge.ai_response_handler import _is_governance_intent
        assert _is_governance_intent("submit evidence for gate G1") is True

    def test_export_audit(self) -> None:
        from app.services.agent_bridge.ai_response_handler import _is_governance_intent
        assert _is_governance_intent("export audit for project 3") is True

    def test_update_sprint(self) -> None:
        from app.services.agent_bridge.ai_response_handler import _is_governance_intent
        assert _is_governance_intent("cập nhật sprint hiện tại") is True

    def test_free_text_not_governance(self) -> None:
        from app.services.agent_bridge.ai_response_handler import _is_governance_intent
        assert _is_governance_intent("hello, how are you?") is False

    def test_general_question_not_governance(self) -> None:
        from app.services.agent_bridge.ai_response_handler import _is_governance_intent
        assert _is_governance_intent("what is SDLC framework?") is False

    def test_case_insensitive(self) -> None:
        from app.services.agent_bridge.ai_response_handler import _is_governance_intent
        assert _is_governance_intent("GATE STATUS for project 5") is True

    def test_empty_string(self) -> None:
        from app.services.agent_bridge.ai_response_handler import _is_governance_intent
        assert _is_governance_intent("") is False

    def test_just_approve_keyword(self) -> None:
        """Single keyword 'approve' should match."""
        from app.services.agent_bridge.ai_response_handler import _is_governance_intent
        assert _is_governance_intent("approve") is True


# ──────────────────────────────────────────────────────────────────────────────
# Test: Response Formatting (A-06)
# ──────────────────────────────────────────────────────────────────────────────


class TestResponseFormatting:
    """Test bilingual response formatters."""

    def _make_gate(self, **kwargs: Any) -> MagicMock:
        """Create a mock gate object."""
        gate = MagicMock()
        gate.gate_type = kwargs.get("gate_type", "G2_DESIGN_READY")
        gate.gate_name = kwargs.get("gate_name", "Design Ready")
        gate.gate_code = kwargs.get("gate_code", "G2")
        gate.status = kwargs.get("status", "SUBMITTED")
        gate.project_id = kwargs.get("project_id", uuid4())
        gate.evaluated_at = kwargs.get("evaluated_at", None)
        gate.created_at = kwargs.get("created_at", "2026-02-20")
        gate.exit_criteria = kwargs.get("exit_criteria", [])
        gate.id = kwargs.get("id", uuid4())
        return gate

    def test_format_gate_status(self) -> None:
        from app.services.agent_bridge.governance_action_handler import _format_gate_status
        gate = self._make_gate(status="EVALUATED")
        result = _format_gate_status(gate)
        assert "Gate Status" in result
        assert "EVALUATED" in result
        assert "Design Ready" in result

    def test_format_gate_status_with_exit_criteria(self) -> None:
        from app.services.agent_bridge.governance_action_handler import _format_gate_status
        gate = self._make_gate(
            exit_criteria=[
                {"id": "c1", "passed": True},
                {"id": "c2", "passed": True},
                {"id": "c3", "passed": None},
            ],
        )
        result = _format_gate_status(gate)
        assert "2/3 passed" in result

    def test_format_gate_approval_link(self) -> None:
        from app.services.agent_bridge.governance_action_handler import _format_gate_approval_link
        gate = self._make_gate(gate_type="G3_SHIP_READY", gate_name="Ship Ready")
        result = _format_gate_approval_link(gate, "https://example.com/verify?token=abc123", 300)
        assert "https://example.com/verify?token=abc123" in result
        assert "5" in result  # 300/60 = 5 minutes
        assert "Ship Ready" in result

    def test_format_gate_approved_direct(self) -> None:
        from app.services.agent_bridge.governance_action_handler import _format_gate_approved_direct
        gate = self._make_gate()
        result = _format_gate_approved_direct(gate)
        assert "APPROVED" in result
        assert "Design Ready" in result

    def test_format_gate_rejected(self) -> None:
        from app.services.agent_bridge.governance_action_handler import _format_gate_rejected
        gate = self._make_gate()
        result = _format_gate_rejected(gate)
        assert "REJECTED" in result

    def test_format_error(self) -> None:
        from app.services.agent_bridge.governance_action_handler import _format_error
        result = _format_error("Something went wrong")
        assert "Something went wrong" in result
        assert "Error" in result or "Lỗi" in result


# ──────────────────────────────────────────────────────────────────────────────
# Test: Governance Action Handler — Gate Status (A-01)
# ──────────────────────────────────────────────────────────────────────────────


class TestGateStatusExecution:
    """Test _execute_gate_status command handler."""

    @pytest.fixture
    def mock_gate(self) -> MagicMock:
        gate = MagicMock()
        gate.id = uuid4()
        gate.gate_type = "G2_DESIGN_READY"
        gate.gate_name = "Design Ready"
        gate.gate_code = "G2"
        gate.status = "EVALUATED"
        gate.project_id = uuid4()
        gate.evaluated_at = "2026-02-24T10:00:00"
        gate.created_at = "2026-02-20T08:00:00"
        gate.exit_criteria = []
        return gate

    @pytest.mark.asyncio
    async def test_gate_status_by_gate_id(self, mock_gate: MagicMock) -> None:
        from app.services.agent_bridge.governance_action_handler import _execute_gate_status

        with (
            patch("app.services.agent_bridge.governance_action_handler.AsyncSessionLocal") as mock_session_cls,
            patch("app.services.agent_bridge.governance_action_handler._send_telegram_reply", new_callable=AsyncMock) as mock_reply,
            patch("app.services.gate_service.GateService") as mock_gate_svc_cls,
        ):
            mock_session = AsyncMock()
            mock_session_cls.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            mock_gate_svc = MagicMock()
            mock_gate_svc.get_gate_by_id = AsyncMock(return_value=mock_gate)
            mock_gate_svc_cls.return_value = mock_gate_svc

            mock_reply.return_value = True

            result = await _execute_gate_status(
                tool_args={"gate_id": str(mock_gate.id)},
                bot_token="test-token",
                chat_id=123456,
                user_id="user-123",
            )

            assert result is True
            mock_reply.assert_called_once()
            reply_text = mock_reply.call_args[0][2]
            assert "EVALUATED" in reply_text
            assert "Design Ready" in reply_text

    @pytest.mark.asyncio
    async def test_gate_status_not_found(self) -> None:
        from app.services.agent_bridge.governance_action_handler import _execute_gate_status

        with (
            patch("app.services.agent_bridge.governance_action_handler.AsyncSessionLocal") as mock_session_cls,
            patch("app.services.agent_bridge.governance_action_handler._send_telegram_reply", new_callable=AsyncMock) as mock_reply,
            patch("app.services.gate_service.GateService") as mock_gate_svc_cls,
        ):
            mock_session = AsyncMock()
            mock_session_cls.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            mock_gate_svc = MagicMock()
            mock_gate_svc.get_gate_by_id = AsyncMock(return_value=None)
            mock_gate_svc_cls.return_value = mock_gate_svc

            mock_reply.return_value = True

            result = await _execute_gate_status(
                tool_args={"gate_id": str(uuid4())},
                bot_token="test-token",
                chat_id=123456,
                user_id="user-123",
            )

            assert result is False
            mock_reply.assert_called_once()
            reply_text = mock_reply.call_args[0][2]
            assert "not found" in reply_text.lower() or "Error" in reply_text

    @pytest.mark.asyncio
    async def test_gate_status_invalid_uuid(self) -> None:
        from app.services.agent_bridge.governance_action_handler import _execute_gate_status

        with patch("app.services.agent_bridge.governance_action_handler._send_telegram_reply", new_callable=AsyncMock) as mock_reply:
            mock_reply.return_value = True

            result = await _execute_gate_status(
                tool_args={"gate_id": "not-a-uuid"},
                bot_token="test-token",
                chat_id=123456,
                user_id="user-123",
            )

        assert result is False
        mock_reply.assert_called_once()
        reply_text = mock_reply.call_args[0][2]
        assert "Invalid" in reply_text or "invalid" in reply_text.lower()

    @pytest.mark.asyncio
    async def test_gate_status_no_params(self) -> None:
        from app.services.agent_bridge.governance_action_handler import _execute_gate_status

        with patch("app.services.agent_bridge.governance_action_handler._send_telegram_reply", new_callable=AsyncMock) as mock_reply:
            mock_reply.return_value = True

            result = await _execute_gate_status(
                tool_args={},
                bot_token="test-token",
                chat_id=123456,
                user_id="user-123",
            )

        assert result is False
        mock_reply.assert_called_once()
        reply_text = mock_reply.call_args[0][2]
        assert "gate_id" in reply_text.lower() or "project_id" in reply_text.lower()


# ──────────────────────────────────────────────────────────────────────────────
# Test: Governance Action Handler — Dispatch (execute_governance_action)
# ──────────────────────────────────────────────────────────────────────────────


class TestExecuteGovernanceAction:
    """Test main dispatch function."""

    @pytest.mark.asyncio
    async def test_no_tool_call_sends_response_text(self) -> None:
        from app.services.agent_bridge.governance_action_handler import execute_governance_action
        from app.services.agent_team.chat_command_router import ChatCommandResult

        result = ChatCommandResult(response_text="I didn't understand.")

        with patch("app.services.agent_bridge.governance_action_handler._send_telegram_reply", new_callable=AsyncMock) as mock_reply:
            mock_reply.return_value = True

            handled = await execute_governance_action(
                result=result,
                bot_token="test-token",
                chat_id=123456,
                user_id="user-123",
            )

        assert handled is True
        mock_reply.assert_called_once()
        assert "I didn't understand." in mock_reply.call_args[0][2]

    @pytest.mark.asyncio
    async def test_error_result_sends_error(self) -> None:
        from app.services.agent_bridge.governance_action_handler import execute_governance_action
        from app.services.agent_team.chat_command_router import ChatCommandResult

        result = ChatCommandResult(error="AI service unavailable")

        with patch("app.services.agent_bridge.governance_action_handler._send_telegram_reply", new_callable=AsyncMock) as mock_reply:
            mock_reply.return_value = True

            handled = await execute_governance_action(
                result=result,
                bot_token="test-token",
                chat_id=123456,
                user_id="user-123",
            )

        assert handled is True
        mock_reply.assert_called_once()
        assert "AI service unavailable" in mock_reply.call_args[0][2]

    @pytest.mark.asyncio
    async def test_unknown_tool_sends_error(self) -> None:
        from app.services.agent_bridge.governance_action_handler import execute_governance_action
        from app.services.agent_team.chat_command_router import ChatCommandResult

        result = ChatCommandResult(
            tool_name="nonexistent_tool",
            tool_args={"foo": "bar"},
        )

        with patch("app.services.agent_bridge.governance_action_handler._send_telegram_reply", new_callable=AsyncMock) as mock_reply:
            mock_reply.return_value = True

            handled = await execute_governance_action(
                result=result,
                bot_token="test-token",
                chat_id=123456,
                user_id="user-123",
            )

        assert handled is False
        mock_reply.assert_called_once()
        assert "Unknown" in mock_reply.call_args[0][2] or "unknown" in mock_reply.call_args[0][2].lower()

    @pytest.mark.asyncio
    async def test_gate_status_tool_dispatched(self) -> None:
        from app.services.agent_bridge.governance_action_handler import execute_governance_action
        from app.services.agent_team.chat_command_router import ChatCommandResult

        gate_id = str(uuid4())
        result = ChatCommandResult(
            tool_name="get_gate_status",
            tool_args={"gate_id": gate_id},
        )

        with patch("app.services.agent_bridge.governance_action_handler._execute_gate_status", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = True

            handled = await execute_governance_action(
                result=result,
                bot_token="test-token",
                chat_id=123456,
                user_id="user-123",
            )

        assert handled is True
        mock_exec.assert_called_once_with(
            {"gate_id": gate_id}, "test-token", 123456, "user-123",
            channel="telegram",
        )

    @pytest.mark.asyncio
    async def test_request_approval_tool_dispatched(self) -> None:
        from app.services.agent_bridge.governance_action_handler import execute_governance_action
        from app.services.agent_team.chat_command_router import ChatCommandResult

        gate_id = str(uuid4())
        result = ChatCommandResult(
            tool_name="request_approval",
            tool_args={"gate_id": gate_id, "action": "approve"},
        )

        with patch("app.services.agent_bridge.governance_action_handler._execute_request_approval", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = True

            handled = await execute_governance_action(
                result=result,
                bot_token="test-token",
                chat_id=123456,
                user_id="user-123",
            )

        assert handled is True
        mock_exec.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_project_returns_placeholder(self) -> None:
        from app.services.agent_bridge.governance_action_handler import execute_governance_action
        from app.services.agent_team.chat_command_router import ChatCommandResult

        result = ChatCommandResult(
            tool_name="create_project",
            tool_args={"name": "TestProject"},
        )

        with patch("app.services.agent_bridge.governance_action_handler._send_telegram_reply", new_callable=AsyncMock) as mock_reply:
            mock_reply.return_value = True

            handled = await execute_governance_action(
                result=result,
                bot_token="test-token",
                chat_id=123456,
                user_id="user-123",
            )

        assert handled is True
        reply_text = mock_reply.call_args[0][2]
        assert "TestProject" in reply_text


# ──────────────────────────────────────────────────────────────────────────────
# Test: Magic Link Verification Endpoint (A-05)
# ──────────────────────────────────────────────────────────────────────────────


class TestMagicLinkVerification:
    """Test GET /api/v1/magic-link/verify endpoint."""

    @pytest.mark.asyncio
    async def test_valid_token_approves_gate(self) -> None:
        """Valid token should consume token and approve gate."""
        from app.services.agent_team.magic_link_service import MagicLinkPayload

        gate_id = uuid4()
        user_id = uuid4()
        mock_payload = MagicLinkPayload(
            gate_id=str(gate_id),
            action="approve",
            user_id=str(user_id),
            idempotency_key="test-key-123",
        )

        mock_gate = MagicMock()
        mock_gate.id = gate_id
        mock_gate.gate_type = "G2_DESIGN_READY"
        mock_gate.gate_name = "Design Ready"
        mock_gate.gate_code = "G2"
        mock_gate.status = "APPROVED"

        with (
            patch("app.api.routes.magic_link.MagicLinkService") as mock_ml_cls,
            patch("app.api.routes.magic_link.GateService") as mock_gate_cls,
        ):
            mock_ml_instance = MagicMock()
            mock_ml_instance.validate_and_consume = AsyncMock(return_value=mock_payload)
            mock_ml_cls.return_value = mock_ml_instance

            mock_gate_svc = MagicMock()
            mock_gate_svc.get_gate_by_id = AsyncMock(return_value=mock_gate)
            mock_gate_svc.approve_gate = AsyncMock(return_value=mock_gate)
            mock_gate_cls.return_value = mock_gate_svc

            from app.api.routes.magic_link import verify_magic_link
            mock_db = AsyncMock()
            token = "a" * 64

            response = await verify_magic_link(
                token=token,
                user_id=str(user_id),
                db=mock_db,
            )

            assert response.status_code == 200
            body = json.loads(response.body)
            assert body["status"] == "success"
            assert body["action"] == "APPROVED"
            assert body["gate_id"] == str(gate_id)

    @pytest.mark.asyncio
    async def test_expired_token_returns_410(self) -> None:
        """Expired/used token should return 410 Gone."""
        from app.services.agent_team.magic_link_service import MagicLinkExpiredError
        from fastapi import HTTPException

        with patch("app.api.routes.magic_link.MagicLinkService") as mock_ml_cls:
            mock_ml_instance = MagicMock()
            mock_ml_instance.validate_and_consume = AsyncMock(
                side_effect=MagicLinkExpiredError("expired"),
            )
            mock_ml_cls.return_value = mock_ml_instance

            from app.api.routes.magic_link import verify_magic_link
            mock_db = AsyncMock()
            token = "b" * 64

            with pytest.raises(HTTPException) as exc_info:
                await verify_magic_link(
                    token=token,
                    user_id="user-123",
                    db=mock_db,
                )
            assert exc_info.value.status_code == 410

    @pytest.mark.asyncio
    async def test_invalid_token_returns_400(self) -> None:
        """Invalid token signature should return 400."""
        from app.services.agent_team.magic_link_service import MagicLinkInvalidError
        from fastapi import HTTPException

        with patch("app.api.routes.magic_link.MagicLinkService") as mock_ml_cls:
            mock_ml_instance = MagicMock()
            mock_ml_instance.validate_and_consume = AsyncMock(
                side_effect=MagicLinkInvalidError("invalid"),
            )
            mock_ml_cls.return_value = mock_ml_instance

            from app.api.routes.magic_link import verify_magic_link
            mock_db = AsyncMock()
            token = "c" * 64

            with pytest.raises(HTTPException) as exc_info:
                await verify_magic_link(
                    token=token,
                    user_id="user-123",
                    db=mock_db,
                )
            assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_user_mismatch_returns_403(self) -> None:
        """Token issued for different user should return 403."""
        from app.services.agent_team.magic_link_service import MagicLinkUserMismatchError
        from fastapi import HTTPException

        with patch("app.api.routes.magic_link.MagicLinkService") as mock_ml_cls:
            mock_ml_instance = MagicMock()
            mock_ml_instance.validate_and_consume = AsyncMock(
                side_effect=MagicLinkUserMismatchError("mismatch"),
            )
            mock_ml_cls.return_value = mock_ml_instance

            from app.api.routes.magic_link import verify_magic_link
            mock_db = AsyncMock()
            token = "d" * 64

            with pytest.raises(HTTPException) as exc_info:
                await verify_magic_link(
                    token=token,
                    user_id="wrong-user",
                    db=mock_db,
                )
            assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_reject_action(self) -> None:
        """Token with reject action should reject gate."""
        from app.services.agent_team.magic_link_service import MagicLinkPayload

        gate_id = uuid4()
        user_id = uuid4()
        mock_payload = MagicLinkPayload(
            gate_id=str(gate_id),
            action="reject",
            user_id=str(user_id),
            idempotency_key="test-key-456",
        )

        mock_gate = MagicMock()
        mock_gate.id = gate_id
        mock_gate.gate_type = "G1_CONSULTATION"
        mock_gate.gate_name = "Consultation"
        mock_gate.gate_code = "G1"
        mock_gate.status = "REJECTED"

        with (
            patch("app.api.routes.magic_link.MagicLinkService") as mock_ml_cls,
            patch("app.api.routes.magic_link.GateService") as mock_gate_cls,
        ):
            mock_ml_instance = MagicMock()
            mock_ml_instance.validate_and_consume = AsyncMock(return_value=mock_payload)
            mock_ml_cls.return_value = mock_ml_instance

            mock_gate_svc = MagicMock()
            mock_gate_svc.get_gate_by_id = AsyncMock(return_value=mock_gate)
            mock_gate_svc.reject_gate = AsyncMock(return_value=mock_gate)
            mock_gate_cls.return_value = mock_gate_svc

            from app.api.routes.magic_link import verify_magic_link
            mock_db = AsyncMock()
            token = "e" * 64

            response = await verify_magic_link(
                token=token,
                user_id=str(user_id),
                db=mock_db,
            )

            assert response.status_code == 200
            body = json.loads(response.body)
            assert body["action"] == "REJECTED"


# ──────────────────────────────────────────────────────────────────────────────
# Test: Telegram Reply Helper
# ──────────────────────────────────────────────────────────────────────────────


class TestTelegramReply:
    """Test _send_telegram_reply in governance handler."""

    @pytest.mark.asyncio
    async def test_send_reply_success(self) -> None:
        from app.services.agent_bridge.governance_action_handler import _send_telegram_reply
        import httpx

        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch("app.services.agent_bridge.governance_action_handler.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await _send_telegram_reply("test-token", 123456, "Hello!")

        assert result is True

    @pytest.mark.asyncio
    async def test_send_reply_no_token(self) -> None:
        from app.services.agent_bridge.governance_action_handler import _send_telegram_reply
        result = await _send_telegram_reply("", 123456, "Hello!")
        assert result is False

    @pytest.mark.asyncio
    async def test_send_reply_truncates_long_message(self) -> None:
        from app.services.agent_bridge.governance_action_handler import _send_telegram_reply
        import httpx

        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch("app.services.agent_bridge.governance_action_handler.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            long_msg = "A" * 5000
            result = await _send_telegram_reply("test-token", 123456, long_msg)

        assert result is True
        # Verify the message was truncated to 4000 chars
        call_args = mock_client.post.call_args
        sent_text = call_args.kwargs.get("json", {}).get("text", "")
        assert len(sent_text) <= 4000
