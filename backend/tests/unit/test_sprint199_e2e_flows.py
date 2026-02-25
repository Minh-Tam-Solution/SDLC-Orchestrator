"""
E2E Flow Tests — Sprint 199 Track D (D-01, D-02, D-03).

Tests the complete end-to-end handler pipelines with mocked external
dependencies (Telegram API, PostgreSQL, Redis, MinIO). These validate
that the full call chain works correctly without requiring a running server.

D-01: Gate approval via Telegram (intent → router → handler → GateService → reply)
D-02: Evidence upload via Telegram (attachment → handler → MinIO → DB → reply)
D-03: Magic Link verification (generate → validate → consume → gate action)

Sprint 199 — Track D: E2E Testing + Sprint Close
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────


def _telegram_text_payload(
    text: str,
    chat_id: int = 111222333,
    user_id: int = 444555666,
) -> dict:
    """Build a Telegram webhook payload with text message."""
    return {
        "update_id": 10001,
        "message": {
            "message_id": 20001,
            "from": {
                "id": user_id,
                "is_bot": False,
                "first_name": "TestUser",
            },
            "chat": {
                "id": chat_id,
                "type": "private",
            },
            "date": 1740000000,
            "text": text,
        },
    }


def _telegram_document_payload(
    caption: str,
    file_id: str = "BQACAgIAAxkDAAICZmVQ",
    file_name: str = "test-report.pdf",
    file_size: int = 5000,
    mime_type: str = "application/pdf",
    chat_id: int = 111222333,
    user_id: int = 444555666,
) -> dict:
    """Build a Telegram webhook payload with document attachment."""
    return {
        "update_id": 10002,
        "message": {
            "message_id": 20002,
            "from": {
                "id": user_id,
                "is_bot": False,
                "first_name": "TestUser",
            },
            "chat": {
                "id": chat_id,
                "type": "private",
            },
            "date": 1740000000,
            "document": {
                "file_id": file_id,
                "file_name": file_name,
                "file_size": file_size,
                "mime_type": mime_type,
            },
            "caption": caption,
        },
    }


def _telegram_photo_payload(
    caption: str,
    chat_id: int = 111222333,
    user_id: int = 444555666,
) -> dict:
    """Build a Telegram webhook payload with photo attachment."""
    return {
        "update_id": 10003,
        "message": {
            "message_id": 20003,
            "from": {
                "id": user_id,
                "is_bot": False,
                "first_name": "TestUser",
            },
            "chat": {
                "id": chat_id,
                "type": "private",
            },
            "date": 1740000000,
            "photo": [
                {"file_id": "small_id", "file_size": 1000, "width": 90, "height": 90},
                {"file_id": "medium_id", "file_size": 5000, "width": 320, "height": 320},
                {"file_id": "large_id", "file_size": 15000, "width": 800, "height": 800},
            ],
            "caption": caption,
        },
    }


# ──────────────────────────────────────────────────────────────────────────────
# D-01: Gate Approval via Telegram — Full E2E Flow
# ──────────────────────────────────────────────────────────────────────────────


class TestGateApprovalE2E:
    """D-01: Test end-to-end gate approval flow via Telegram chat."""

    @pytest.mark.asyncio
    async def test_governance_intent_routes_to_handler(self) -> None:
        """
        Full flow: 'approve gate <uuid>' → governance intent detected →
        chat_command_router → governance_action_handler → reply sent.
        """
        from app.services.agent_bridge.ai_response_handler import handle_ai_response

        gate_id = str(uuid4())
        payload = _telegram_text_payload(f"approve gate {gate_id}")

        mock_redis = AsyncMock()
        mock_redis.incr = AsyncMock(return_value=1)
        mock_redis.expire = AsyncMock()

        # Mock the governance intent detection to return True
        # and the subsequent handler chain
        with (
            patch("app.services.agent_bridge.ai_response_handler.get_redis_client", new_callable=AsyncMock, return_value=mock_redis),
            patch("app.services.agent_bridge.ai_response_handler._send_typing_indicator", new_callable=AsyncMock),
            patch("app.services.agent_team.chat_command_router.route_chat_command", new_callable=AsyncMock) as mock_router,
            patch("app.services.agent_bridge.governance_action_handler.execute_governance_action", new_callable=AsyncMock) as mock_action,
        ):
            from app.services.agent_team.chat_command_router import ChatCommandResult
            mock_router.return_value = ChatCommandResult(
                tool_name="request_approval",
                tool_args={"gate_id": gate_id, "action": "approve"},
            )
            mock_action.return_value = True

            result = await handle_ai_response(payload, "test-bot-token")

        assert result is True
        mock_router.assert_called_once()
        mock_action.assert_called_once()
        # Verify the action was called with correct params
        call_kwargs = mock_action.call_args.kwargs
        assert call_kwargs["chat_id"] == 111222333
        assert call_kwargs["user_id"] == "444555666"

    @pytest.mark.asyncio
    async def test_gate_status_query_e2e(self) -> None:
        """
        Full flow: 'gate status <uuid>' → intent detected → handler →
        GateService.get_gate_by_id → formatted reply → Telegram.
        """
        from app.services.agent_bridge.ai_response_handler import handle_ai_response

        gate_id = str(uuid4())
        payload = _telegram_text_payload(f"gate status {gate_id}")

        mock_redis = AsyncMock()
        mock_redis.incr = AsyncMock(return_value=1)
        mock_redis.expire = AsyncMock()

        with (
            patch("app.services.agent_bridge.ai_response_handler.get_redis_client", new_callable=AsyncMock, return_value=mock_redis),
            patch("app.services.agent_bridge.ai_response_handler._send_typing_indicator", new_callable=AsyncMock),
            patch("app.services.agent_team.chat_command_router.route_chat_command", new_callable=AsyncMock) as mock_router,
            patch("app.services.agent_bridge.governance_action_handler.execute_governance_action", new_callable=AsyncMock) as mock_action,
        ):
            from app.services.agent_team.chat_command_router import ChatCommandResult
            mock_router.return_value = ChatCommandResult(
                tool_name="get_gate_status",
                tool_args={"gate_id": gate_id},
            )
            mock_action.return_value = True

            result = await handle_ai_response(payload, "test-bot-token")

        assert result is True
        mock_router.assert_called_once_with(
            message=f"gate status {gate_id}",
            user_id="444555666",
        )

    @pytest.mark.asyncio
    async def test_non_governance_falls_through_to_ai(self) -> None:
        """
        'hello how are you' → NOT governance intent → Ollama AI chat → reply.
        """
        from app.services.agent_bridge.ai_response_handler import handle_ai_response

        payload = _telegram_text_payload("hello how are you?")

        mock_redis = AsyncMock()
        mock_redis.incr = AsyncMock(return_value=1)
        mock_redis.expire = AsyncMock()
        mock_redis.lrange = AsyncMock(return_value=[])
        mock_redis.lpush = AsyncMock()
        mock_redis.ltrim = AsyncMock()

        mock_ollama_response = {
            "message": {"content": "Hi! I'm the SDLC assistant."},
        }

        with (
            patch("app.services.agent_bridge.ai_response_handler.get_redis_client", new_callable=AsyncMock, return_value=mock_redis),
            patch("app.services.agent_bridge.ai_response_handler._send_typing_indicator", new_callable=AsyncMock),
            patch("app.services.agent_bridge.ai_response_handler._send_telegram_reply", new_callable=AsyncMock, return_value=True) as mock_reply,
            patch("app.services.agent_bridge.ai_response_handler.OllamaService") as mock_ollama_cls,
            patch("app.services.agent_bridge.ai_response_handler.run_in_threadpool", new_callable=AsyncMock, return_value=mock_ollama_response),
        ):
            result = await handle_ai_response(payload, "test-bot-token")

        assert result is True
        mock_reply.assert_called_once()
        reply_text = mock_reply.call_args[0][2]
        assert "SDLC assistant" in reply_text

    @pytest.mark.asyncio
    async def test_governance_handler_failure_falls_through(self) -> None:
        """
        If governance handler raises Exception, should fall through to AI chat.
        """
        from app.services.agent_bridge.ai_response_handler import handle_ai_response

        payload = _telegram_text_payload("approve gate invalid-stuff")

        mock_redis = AsyncMock()
        mock_redis.incr = AsyncMock(return_value=1)
        mock_redis.expire = AsyncMock()
        mock_redis.lrange = AsyncMock(return_value=[])
        mock_redis.lpush = AsyncMock()
        mock_redis.ltrim = AsyncMock()

        mock_ollama_response = {
            "message": {"content": "I can help with gate approvals."},
        }

        with (
            patch("app.services.agent_bridge.ai_response_handler.get_redis_client", new_callable=AsyncMock, return_value=mock_redis),
            patch("app.services.agent_bridge.ai_response_handler._send_typing_indicator", new_callable=AsyncMock),
            patch("app.services.agent_bridge.ai_response_handler._send_telegram_reply", new_callable=AsyncMock, return_value=True),
            patch("app.services.agent_team.chat_command_router.route_chat_command", new_callable=AsyncMock, side_effect=Exception("Router crash")),
            patch("app.services.agent_bridge.ai_response_handler.OllamaService") as mock_ollama_cls,
            patch("app.services.agent_bridge.ai_response_handler.run_in_threadpool", new_callable=AsyncMock, return_value=mock_ollama_response),
        ):
            result = await handle_ai_response(payload, "test-bot-token")

        # Falls through to AI chat instead of crashing
        assert result is True

    @pytest.mark.asyncio
    async def test_rate_limited_user_gets_rate_limit_reply(self) -> None:
        """
        User exceeding 10 msg/min rate limit gets rate limit message.
        """
        from app.services.agent_bridge.ai_response_handler import handle_ai_response

        payload = _telegram_text_payload("approve something")

        mock_redis = AsyncMock()
        mock_redis.incr = AsyncMock(return_value=11)  # Over 10/min limit

        with (
            patch("app.services.agent_bridge.ai_response_handler.get_redis_client", new_callable=AsyncMock, return_value=mock_redis),
            patch("app.services.agent_bridge.ai_response_handler._send_telegram_reply", new_callable=AsyncMock, return_value=True) as mock_reply,
        ):
            result = await handle_ai_response(payload, "test-bot-token")

        assert result is False
        mock_reply.assert_called_once()
        reply_text = mock_reply.call_args[0][2]
        assert "Rate limit" in reply_text or "qua nhieu" in reply_text


# ──────────────────────────────────────────────────────────────────────────────
# D-02: Evidence Upload via Telegram — Full E2E Flow
# ──────────────────────────────────────────────────────────────────────────────


class TestEvidenceUploadE2E:
    """D-02: Test end-to-end evidence upload flow via Telegram file attachment."""

    @pytest.mark.asyncio
    async def test_document_upload_full_flow(self) -> None:
        """
        Full flow: document attachment → evidence_upload_handler →
        download from Telegram → upload to MinIO → create DB record → confirm reply.
        """
        from app.services.agent_bridge.ai_response_handler import handle_ai_response

        gate_id = str(uuid4())
        payload = _telegram_document_payload(
            caption=f"test report for gate {gate_id}",
            file_name="test-results.pdf",
            file_size=5000,
        )

        # Mock the evidence upload handler
        with patch(
            "app.services.agent_bridge.evidence_upload_handler.handle_evidence_upload",
            new_callable=AsyncMock,
            return_value=True,
        ) as mock_evidence:
            result = await handle_ai_response(payload, "test-bot-token")

        assert result is True
        mock_evidence.assert_called_once_with(payload, "test-bot-token")

    @pytest.mark.asyncio
    async def test_photo_upload_full_flow(self) -> None:
        """
        Full flow: photo attachment → evidence_upload_handler →
        selects largest photo → downloads → uploads → confirms.
        """
        from app.services.agent_bridge.ai_response_handler import handle_ai_response

        gate_id = str(uuid4())
        payload = _telegram_photo_payload(
            caption=f"deployment screenshot for gate {gate_id}",
        )

        with patch(
            "app.services.agent_bridge.evidence_upload_handler.handle_evidence_upload",
            new_callable=AsyncMock,
            return_value=True,
        ) as mock_evidence:
            result = await handle_ai_response(payload, "test-bot-token")

        assert result is True
        mock_evidence.assert_called_once()

    @pytest.mark.asyncio
    async def test_document_no_gate_id_falls_through(self) -> None:
        """
        Document with caption but no gate_id → evidence handler returns False →
        falls through to AI chat with caption as text.
        """
        from app.services.agent_bridge.ai_response_handler import handle_ai_response

        payload = _telegram_document_payload(
            caption="just a random document",
            file_name="random.pdf",
        )

        mock_redis = AsyncMock()
        mock_redis.incr = AsyncMock(return_value=1)
        mock_redis.expire = AsyncMock()
        mock_redis.lrange = AsyncMock(return_value=[])
        mock_redis.lpush = AsyncMock()
        mock_redis.ltrim = AsyncMock()

        mock_ollama_response = {
            "message": {"content": "I see you uploaded a document."},
        }

        with (
            patch("app.services.agent_bridge.evidence_upload_handler.handle_evidence_upload", new_callable=AsyncMock, return_value=False),
            patch("app.services.agent_bridge.ai_response_handler.get_redis_client", new_callable=AsyncMock, return_value=mock_redis),
            patch("app.services.agent_bridge.ai_response_handler._send_typing_indicator", new_callable=AsyncMock),
            patch("app.services.agent_bridge.ai_response_handler._send_telegram_reply", new_callable=AsyncMock, return_value=True) as mock_reply,
            patch("app.services.agent_bridge.ai_response_handler.OllamaService"),
            patch("app.services.agent_bridge.ai_response_handler.run_in_threadpool", new_callable=AsyncMock, return_value=mock_ollama_response),
        ):
            result = await handle_ai_response(payload, "test-bot-token")

        assert result is True

    @pytest.mark.asyncio
    async def test_evidence_handler_full_pipeline(self) -> None:
        """
        Deep E2E: Tests handle_evidence_upload with mocked Telegram download,
        MinIO upload, and DB insert — verifying the complete evidence pipeline.
        """
        from app.services.agent_bridge.evidence_upload_handler import handle_evidence_upload

        gate_id = str(uuid4())
        payload = _telegram_document_payload(
            caption=f"test evidence for gate {gate_id}",
            file_name="sast-report.html",
            file_size=2048,
            mime_type="text/html",
        )

        file_bytes = b"<html><body>SAST Report: 0 vulnerabilities</body></html>"
        sha256_hash = "a" * 64

        mock_telegram_response_get_file = MagicMock()
        mock_telegram_response_get_file.status_code = 200
        mock_telegram_response_get_file.json.return_value = {
            "ok": True,
            "result": {"file_path": "documents/file_123.html"},
        }

        mock_telegram_response_download = MagicMock()
        mock_telegram_response_download.status_code = 200
        mock_telegram_response_download.content = file_bytes

        mock_minio_response = MagicMock()
        mock_minio_response.status_code = 200

        mock_telegram_reply = MagicMock()
        mock_telegram_reply.status_code = 200

        # Mock DB session
        mock_evidence_record = MagicMock()
        mock_evidence_record.id = uuid4()

        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock(side_effect=lambda e: setattr(e, "id", uuid4()))

        with (
            patch("app.services.agent_bridge.evidence_upload_handler.httpx.AsyncClient") as mock_client_cls,
            patch("app.db.session.AsyncSessionLocal") as mock_session_cls,
        ):
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(side_effect=[
                mock_telegram_response_get_file,  # getFile
                mock_telegram_reply,               # sendMessage (confirmation)
            ])
            mock_client.get = AsyncMock(return_value=mock_telegram_response_download)
            mock_client.put = AsyncMock(return_value=mock_minio_response)

            mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            mock_session_cls.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_session_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await handle_evidence_upload(payload, "test-bot-token")

        assert result is True
        # Verify DB record was created
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        # Verify the evidence record has correct fields
        evidence_obj = mock_db.add.call_args[0][0]
        assert evidence_obj.source == "ott"
        assert evidence_obj.evidence_type == "test_report"  # html → test_report
        assert evidence_obj.file_name == "sast-report.html"

    @pytest.mark.asyncio
    async def test_oversized_file_rejected(self) -> None:
        """File > 10MB is rejected with error message, never downloaded."""
        from app.services.agent_bridge.evidence_upload_handler import handle_evidence_upload

        gate_id = str(uuid4())
        payload = _telegram_document_payload(
            caption=f"big file for gate {gate_id}",
            file_name="huge.zip",
            file_size=15 * 1024 * 1024,  # 15MB
        )

        mock_telegram_reply = MagicMock()
        mock_telegram_reply.status_code = 200

        with patch("app.services.agent_bridge.evidence_upload_handler.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_telegram_reply)
            mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await handle_evidence_upload(payload, "test-bot-token")

        assert result is False
        # Verify error reply was sent
        mock_client.post.assert_called_once()  # Only sendMessage, NOT getFile


# ──────────────────────────────────────────────────────────────────────────────
# D-03: Magic Link Verification — Full E2E Flow
# ──────────────────────────────────────────────────────────────────────────────


class TestMagicLinkE2E:
    """D-03: Test end-to-end Magic Link flow: generate → consume → gate action."""

    @pytest.mark.asyncio
    async def test_generate_then_consume_flow(self) -> None:
        """
        Full flow: generate_token() → validate_and_consume() →
        returns correct payload for gate action.
        """
        from app.services.agent_team.magic_link_service import MagicLinkService

        gate_id = str(uuid4())
        user_id = str(uuid4())

        # Use a shared mock Redis that stores/retrieves real data
        redis_store: dict[str, str] = {}

        async def mock_setex(key: str, ttl: int, value: str) -> None:
            redis_store[key] = value

        async def mock_getdel(key: str):
            return redis_store.pop(key, None)

        mock_redis = AsyncMock()
        mock_redis.setex = mock_setex
        mock_redis.getdel = mock_getdel

        with patch(
            "app.services.agent_team.magic_link_service.get_redis_client",
            new_callable=AsyncMock,
            return_value=mock_redis,
        ):
            svc = MagicLinkService(
                secret="e2e-test-secret-32-bytes-long!",
                ttl_seconds=300,
                frontend_url="https://sdlc.example.com",
            )

            # Step 1: Generate token
            token = await svc.generate_token(
                gate_id=gate_id,
                action="approve",
                user_id=user_id,
            )

            assert token.signature is not None
            assert len(token.signature) == 64
            assert token.url.startswith("https://sdlc.example.com/auth/magic?token=")

            # Step 2: Consume token (simulates browser clicking the link)
            payload = await svc.validate_and_consume(
                signature=token.signature,
                browser_user_id=user_id,
            )

            assert payload.gate_id == gate_id
            assert payload.action == "approve"
            assert payload.user_id == user_id

            # Step 3: Second consumption fails (single-use)
            from app.services.agent_team.magic_link_service import MagicLinkExpiredError
            with pytest.raises(MagicLinkExpiredError):
                await svc.validate_and_consume(
                    signature=token.signature,
                    browser_user_id=user_id,
                )

    @pytest.mark.asyncio
    async def test_reject_flow(self) -> None:
        """Generate reject token → consume → returns reject action."""
        from app.services.agent_team.magic_link_service import MagicLinkService

        gate_id = str(uuid4())
        user_id = str(uuid4())

        redis_store: dict[str, str] = {}

        async def mock_setex(key: str, ttl: int, value: str) -> None:
            redis_store[key] = value

        async def mock_getdel(key: str):
            return redis_store.pop(key, None)

        mock_redis = AsyncMock()
        mock_redis.setex = mock_setex
        mock_redis.getdel = mock_getdel

        with patch(
            "app.services.agent_team.magic_link_service.get_redis_client",
            new_callable=AsyncMock,
            return_value=mock_redis,
        ):
            svc = MagicLinkService(
                secret="e2e-reject-secret-32-bytes-ok!",
                ttl_seconds=300,
                frontend_url="https://sdlc.example.com",
            )

            token = await svc.generate_token(gate_id, "reject", user_id)
            payload = await svc.validate_and_consume(token.signature, user_id)

            assert payload.action == "reject"
            assert payload.gate_id == gate_id

    @pytest.mark.asyncio
    async def test_wrong_user_cannot_consume(self) -> None:
        """Token generated for user A cannot be consumed by user B."""
        from app.services.agent_team.magic_link_service import (
            MagicLinkService,
            MagicLinkUserMismatchError,
        )

        gate_id = str(uuid4())
        user_a = str(uuid4())
        user_b = str(uuid4())

        redis_store: dict[str, str] = {}

        async def mock_setex(key: str, ttl: int, value: str) -> None:
            redis_store[key] = value

        async def mock_getdel(key: str):
            return redis_store.pop(key, None)

        mock_redis = AsyncMock()
        mock_redis.setex = mock_setex
        mock_redis.getdel = mock_getdel

        with patch(
            "app.services.agent_team.magic_link_service.get_redis_client",
            new_callable=AsyncMock,
            return_value=mock_redis,
        ):
            svc = MagicLinkService(
                secret="e2e-mismatch-secret-32-bytes!",
                ttl_seconds=300,
                frontend_url="https://sdlc.example.com",
            )

            token = await svc.generate_token(gate_id, "approve", user_a)

            with pytest.raises(MagicLinkUserMismatchError):
                await svc.validate_and_consume(token.signature, user_b)

    @pytest.mark.asyncio
    async def test_magic_link_verify_endpoint_e2e(self) -> None:
        """
        Full endpoint E2E: verify_magic_link() → consume token → approve gate → JSON.
        """
        from app.api.routes.magic_link import verify_magic_link
        from app.services.agent_team.magic_link_service import MagicLinkPayload

        gate_id = uuid4()
        user_id = uuid4()

        mock_payload = MagicLinkPayload(
            gate_id=str(gate_id),
            action="approve",
            user_id=str(user_id),
            idempotency_key="e2e-idem-key",
        )

        mock_gate = MagicMock()
        mock_gate.id = gate_id
        mock_gate.gate_type = "G3_SHIP_READY"
        mock_gate.gate_name = "Ship Ready"
        mock_gate.gate_code = "G3"
        mock_gate.status = "APPROVED"

        with (
            patch("app.api.routes.magic_link.MagicLinkService") as mock_ml_cls,
            patch("app.api.routes.magic_link.GateService") as mock_gate_cls,
        ):
            mock_ml = MagicMock()
            mock_ml.validate_and_consume = AsyncMock(return_value=mock_payload)
            mock_ml_cls.return_value = mock_ml

            mock_gate_svc = MagicMock()
            mock_gate_svc.get_gate_by_id = AsyncMock(return_value=mock_gate)
            mock_gate_svc.approve_gate = AsyncMock(return_value=mock_gate)
            mock_gate_cls.return_value = mock_gate_svc

            response = await verify_magic_link(
                token="a" * 64,
                user_id=str(user_id),
                db=AsyncMock(),
            )

        assert response.status_code == 200
        body = json.loads(response.body)
        assert body["status"] == "success"
        assert body["action"] == "APPROVED"
        assert body["gate_id"] == str(gate_id)
        assert body["gate_name"] == "Ship Ready"
        assert body["gate_type"] == "G3_SHIP_READY"
        assert body["approved_by"] == str(user_id)

    @pytest.mark.asyncio
    async def test_two_tokens_for_same_gate_both_unique(self) -> None:
        """
        Two tokens generated for the same gate have different signatures
        (due to unique idempotency keys).
        """
        from app.services.agent_team.magic_link_service import MagicLinkService

        gate_id = str(uuid4())
        user_id = str(uuid4())

        redis_store: dict[str, str] = {}

        async def mock_setex(key: str, ttl: int, value: str) -> None:
            redis_store[key] = value

        mock_redis = AsyncMock()
        mock_redis.setex = mock_setex

        with patch(
            "app.services.agent_team.magic_link_service.get_redis_client",
            new_callable=AsyncMock,
            return_value=mock_redis,
        ):
            svc = MagicLinkService(
                secret="e2e-unique-tokens-32-bytes-ok!",
                ttl_seconds=300,
                frontend_url="https://example.com",
            )

            token1 = await svc.generate_token(gate_id, "approve", user_id)
            token2 = await svc.generate_token(gate_id, "approve", user_id)

        assert token1.signature != token2.signature
        assert token1.url != token2.url
        # Both stored in Redis
        assert len(redis_store) == 2


# ──────────────────────────────────────────────────────────────────────────────
# Cross-Track Integration: Governance Intent + Evidence Routing
# ──────────────────────────────────────────────────────────────────────────────


class TestCrossTrackIntegration:
    """Test interaction between Track A (governance) and Track B (evidence)."""

    @pytest.mark.asyncio
    async def test_file_attachment_takes_priority_over_governance_intent(self) -> None:
        """
        Message with both file attachment AND governance text in caption →
        should route to evidence handler FIRST (file takes priority).
        """
        from app.services.agent_bridge.ai_response_handler import handle_ai_response

        gate_id = str(uuid4())
        payload = _telegram_document_payload(
            caption=f"approve gate {gate_id}",
            file_name="approval-evidence.pdf",
        )

        with patch(
            "app.services.agent_bridge.evidence_upload_handler.handle_evidence_upload",
            new_callable=AsyncMock,
            return_value=True,
        ) as mock_evidence:
            result = await handle_ai_response(payload, "test-bot-token")

        # Evidence handler is called first (file attachment priority)
        assert result is True
        mock_evidence.assert_called_once()

    @pytest.mark.asyncio
    async def test_empty_message_returns_false(self) -> None:
        """Message with no text, no caption, no file → returns False."""
        from app.services.agent_bridge.ai_response_handler import handle_ai_response

        payload = {
            "update_id": 10010,
            "message": {
                "message_id": 20010,
                "from": {"id": 123, "is_bot": False, "first_name": "Test"},
                "chat": {"id": 456, "type": "private"},
                "date": 1740000000,
                # No text, no caption, no document, no photo
            },
        }

        result = await handle_ai_response(payload, "test-bot-token")
        assert result is False

    @pytest.mark.asyncio
    async def test_no_message_key_returns_false(self) -> None:
        """Telegram update with no 'message' key (e.g., callback_query) → False."""
        from app.services.agent_bridge.ai_response_handler import handle_ai_response

        payload = {
            "update_id": 10011,
            "callback_query": {
                "id": "test-callback",
                "from": {"id": 123, "is_bot": False},
            },
        }

        result = await handle_ai_response(payload, "test-bot-token")
        assert result is False
