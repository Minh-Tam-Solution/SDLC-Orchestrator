"""
Unit tests for Sprint 199 Track B — Evidence Upload via OTT.

Tests:
    - File attachment detection in ai_response_handler (B-01 routing)
    - Gate UUID extraction from captions
    - Evidence type inference from captions/filenames
    - File size validation (B-04: max 10MB)
    - Telegram file download (B-01)
    - MinIO upload flow
    - GateEvidence DB insert (B-02)
    - Confirmation reply formatting (B-03)
    - Full handle_evidence_upload flow

Sprint 199 — Track B: Evidence Upload via OTT
"""

from __future__ import annotations

import hashlib
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.agent_bridge.evidence_upload_handler import (
    _extract_gate_id,
    _format_error,
    _format_evidence_confirmation,
    _infer_evidence_type,
    handle_evidence_upload,
)


# ──────────────────────────────────────────────────────────────────────────────
# Gate UUID Extraction
# ──────────────────────────────────────────────────────────────────────────────


class TestGateUUIDExtraction:
    """Test gate_id extraction from Telegram captions."""

    def test_extract_from_standard_format(self):
        text = "evidence for gate 550e8400-e29b-41d4-a716-446655440000"
        assert _extract_gate_id(text) == "550e8400-e29b-41d4-a716-446655440000"

    def test_extract_with_gate_id_equals(self):
        text = "upload gate_id=550e8400-e29b-41d4-a716-446655440000 test"
        assert _extract_gate_id(text) == "550e8400-e29b-41d4-a716-446655440000"

    def test_extract_with_gate_id_colon(self):
        text = "gate_id: 550e8400-e29b-41d4-a716-446655440000"
        assert _extract_gate_id(text) == "550e8400-e29b-41d4-a716-446655440000"

    def test_no_gate_id_returns_none(self):
        assert _extract_gate_id("just some text") is None

    def test_empty_string(self):
        assert _extract_gate_id("") is None

    def test_partial_uuid_not_matched(self):
        assert _extract_gate_id("gate 12345") is None

    def test_case_insensitive(self):
        text = "Gate 550E8400-E29B-41D4-A716-446655440000"
        assert _extract_gate_id(text) == "550E8400-E29B-41D4-A716-446655440000"


# ──────────────────────────────────────────────────────────────────────────────
# Evidence Type Inference
# ──────────────────────────────────────────────────────────────────────────────


class TestEvidenceTypeInference:
    """Test evidence type inference from captions and filenames."""

    def test_test_keyword_english(self):
        assert _infer_evidence_type("test results", "report.pdf") == "test_report"

    def test_test_keyword_vietnamese(self):
        assert _infer_evidence_type("ket qua kiem thu", "report.html") == "test_report"

    def test_design_keyword(self):
        assert _infer_evidence_type("design document", "arch.pdf") == "DESIGN_DOCUMENT"

    def test_review_keyword(self):
        assert _infer_evidence_type("code review", "pr.txt") == "CODE_REVIEW"

    def test_deployment_keyword(self):
        assert _infer_evidence_type("deployment proof", "deploy.log") == "DEPLOYMENT_PROOF"

    def test_compliance_keyword(self):
        assert _infer_evidence_type("compliance report", "audit.pdf") == "COMPLIANCE"

    def test_pdf_extension_default(self):
        assert _infer_evidence_type("some file", "report.pdf") == "DESIGN_DOCUMENT"

    def test_html_extension_default(self):
        assert _infer_evidence_type("results", "coverage.html") == "test_report"

    def test_image_extension_default(self):
        assert _infer_evidence_type("screenshot", "screen.png") == "DEPLOYMENT_PROOF"

    def test_unknown_defaults_to_other(self):
        assert _infer_evidence_type("some stuff", "data.bin") == "other"


# ──────────────────────────────────────────────────────────────────────────────
# Response Formatting
# ──────────────────────────────────────────────────────────────────────────────


class TestResponseFormatting:
    """Test evidence confirmation and error formatting (B-03)."""

    def test_confirmation_format(self):
        result = _format_evidence_confirmation(
            file_name="report.pdf",
            file_size=1024 * 500,  # 500 KB
            sha256_hash="a" * 64,
            evidence_type="test_report",
            gate_id="550e8400-e29b-41d4-a716-446655440000",
        )
        assert "report.pdf" in result
        assert "500.0 KB" in result
        assert "test_report" in result
        assert "550e8400" in result
        assert "aaaaaaaaaaaaaaaa..." in result  # sha256[:16]
        assert "ott" in result

    def test_confirmation_large_file_mb(self):
        result = _format_evidence_confirmation(
            file_name="large.zip",
            file_size=5 * 1024 * 1024,  # 5 MB
            sha256_hash="b" * 64,
            evidence_type="COMPLIANCE",
            gate_id="test-gate-id",
        )
        assert "5.0 MB" in result

    def test_error_format(self):
        result = _format_error("Something went wrong")
        assert "failed" in result.lower()
        assert "Something went wrong" in result


# ──────────────────────────────────────────────────────────────────────────────
# File Size Validation (B-04)
# ──────────────────────────────────────────────────────────────────────────────


class TestFileSizeValidation:
    """Test file size validation (B-04: max 10MB for OTT)."""

    @pytest.mark.asyncio
    async def test_file_too_large_rejected(self):
        """Files > 10MB should be rejected with error message."""
        raw_body = {
            "message": {
                "chat": {"id": 123},
                "from": {"id": 456},
                "document": {
                    "file_id": "abc123",
                    "file_name": "huge.zip",
                    "file_size": 15 * 1024 * 1024,  # 15MB
                    "mime_type": "application/zip",
                },
                "caption": "gate 550e8400-e29b-41d4-a716-446655440000",
            }
        }

        with patch(
            "app.services.agent_bridge.evidence_upload_handler._send_telegram_reply",
            new_callable=AsyncMock,
            return_value=True,
        ) as mock_reply:
            result = await handle_evidence_upload(raw_body, "test-token")

        assert result is False
        mock_reply.assert_called_once()
        call_text = mock_reply.call_args[0][2]
        assert "10 MB" in call_text

    @pytest.mark.asyncio
    async def test_file_within_limit_proceeds(self):
        """Files <= 10MB should proceed to download."""
        raw_body = {
            "message": {
                "chat": {"id": 123},
                "from": {"id": 456},
                "document": {
                    "file_id": "abc123",
                    "file_name": "report.pdf",
                    "file_size": 5 * 1024 * 1024,  # 5MB
                    "mime_type": "application/pdf",
                },
                "caption": "gate 550e8400-e29b-41d4-a716-446655440000",
            }
        }

        # File is within limit — will proceed to download (which we mock to fail)
        with patch(
            "app.services.agent_bridge.evidence_upload_handler._download_telegram_file",
            new_callable=AsyncMock,
            return_value=None,
        ), patch(
            "app.services.agent_bridge.evidence_upload_handler._send_telegram_reply",
            new_callable=AsyncMock,
            return_value=True,
        ) as mock_reply:
            result = await handle_evidence_upload(raw_body, "test-token")

        # Download failed, but we got past size validation
        assert result is False
        call_text = mock_reply.call_args[0][2]
        assert "download" in call_text.lower() or "tai" in call_text.lower()


# ──────────────────────────────────────────────────────────────────────────────
# Missing Gate ID
# ──────────────────────────────────────────────────────────────────────────────


class TestMissingGateID:
    """Test that missing gate_id in caption returns helpful error."""

    @pytest.mark.asyncio
    async def test_no_gate_id_in_caption(self):
        raw_body = {
            "message": {
                "chat": {"id": 123},
                "from": {"id": 456},
                "document": {
                    "file_id": "abc123",
                    "file_name": "report.pdf",
                    "file_size": 1024,
                    "mime_type": "application/pdf",
                },
                "caption": "just some evidence file",
            }
        }

        with patch(
            "app.services.agent_bridge.evidence_upload_handler._send_telegram_reply",
            new_callable=AsyncMock,
            return_value=True,
        ) as mock_reply:
            result = await handle_evidence_upload(raw_body, "test-token")

        assert result is False
        call_text = mock_reply.call_args[0][2]
        assert "gate ID" in call_text or "gate_id" in call_text.lower()

    @pytest.mark.asyncio
    async def test_no_caption_at_all(self):
        raw_body = {
            "message": {
                "chat": {"id": 123},
                "from": {"id": 456},
                "document": {
                    "file_id": "abc123",
                    "file_name": "report.pdf",
                    "file_size": 1024,
                    "mime_type": "application/pdf",
                },
            }
        }

        with patch(
            "app.services.agent_bridge.evidence_upload_handler._send_telegram_reply",
            new_callable=AsyncMock,
            return_value=True,
        ) as mock_reply:
            result = await handle_evidence_upload(raw_body, "test-token")

        assert result is False


# ──────────────────────────────────────────────────────────────────────────────
# Telegram File Download (B-01)
# ──────────────────────────────────────────────────────────────────────────────


class TestTelegramDownload:
    """Test Telegram Bot API file download (B-01)."""

    @pytest.mark.asyncio
    async def test_download_success(self):
        from app.services.agent_bridge.evidence_upload_handler import (
            _download_telegram_file,
        )

        mock_getfile_response = MagicMock()
        mock_getfile_response.status_code = 200
        mock_getfile_response.json.return_value = {
            "ok": True,
            "result": {"file_path": "documents/file_123.pdf"},
        }

        mock_download_response = MagicMock()
        mock_download_response.status_code = 200
        mock_download_response.content = b"file content bytes"

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_getfile_response
        mock_client.get.return_value = mock_download_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await _download_telegram_file("test-token", "file_id_123")

        assert result is not None
        file_bytes, file_path = result
        assert file_bytes == b"file content bytes"
        assert file_path == "documents/file_123.pdf"

    @pytest.mark.asyncio
    async def test_download_getfile_fails(self):
        from app.services.agent_bridge.evidence_upload_handler import (
            _download_telegram_file,
        )

        mock_response = MagicMock()
        mock_response.status_code = 400

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await _download_telegram_file("test-token", "file_id_123")

        assert result is None


# ──────────────────────────────────────────────────────────────────────────────
# Full Upload Flow (B-02)
# ──────────────────────────────────────────────────────────────────────────────


class TestFullUploadFlow:
    """Test complete evidence upload flow (B-02)."""

    @pytest.mark.asyncio
    async def test_successful_upload(self):
        """Full flow: download → upload to MinIO → DB insert → confirmation."""
        file_bytes = b"test evidence content"
        sha256 = hashlib.sha256(file_bytes).hexdigest()

        raw_body = {
            "message": {
                "chat": {"id": 123},
                "from": {"id": 456},
                "document": {
                    "file_id": "abc123",
                    "file_name": "test-report.html",
                    "file_size": len(file_bytes),
                    "mime_type": "text/html",
                },
                "caption": "test evidence for gate 550e8400-e29b-41d4-a716-446655440000",
            }
        }

        # Mock evidence model
        mock_evidence = MagicMock()
        mock_evidence.id = "evidence-uuid-123"

        # Mock DB session
        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        mock_session_cls = MagicMock()
        mock_session_cls.return_value.__aenter__ = AsyncMock(return_value=mock_db)
        mock_session_cls.return_value.__aexit__ = AsyncMock(return_value=None)

        with (
            patch(
                "app.services.agent_bridge.evidence_upload_handler._download_telegram_file",
                new_callable=AsyncMock,
                return_value=(file_bytes, "documents/test-report.html"),
            ),
            patch(
                "app.services.agent_bridge.evidence_upload_handler._upload_to_minio",
                new_callable=AsyncMock,
                return_value=sha256,
            ),
            patch(
                "app.services.agent_bridge.evidence_upload_handler._send_telegram_reply",
                new_callable=AsyncMock,
                return_value=True,
            ) as mock_reply,
            patch(
                "app.db.session.AsyncSessionLocal",
                mock_session_cls,
            ),
            patch(
                "app.models.gate_evidence.GateEvidence",
                return_value=mock_evidence,
            ),
        ):
            result = await handle_evidence_upload(raw_body, "test-token")

        assert result is True
        # Confirmation reply sent
        assert mock_reply.call_count >= 1
        confirmation_text = mock_reply.call_args[0][2]
        assert "test-report.html" in confirmation_text
        assert "test_report" in confirmation_text
        assert sha256[:16] in confirmation_text

    @pytest.mark.asyncio
    async def test_minio_upload_fails(self):
        """MinIO upload failure sends error reply."""
        file_bytes = b"test content"

        raw_body = {
            "message": {
                "chat": {"id": 123},
                "from": {"id": 456},
                "document": {
                    "file_id": "abc123",
                    "file_name": "report.pdf",
                    "file_size": len(file_bytes),
                    "mime_type": "application/pdf",
                },
                "caption": "gate 550e8400-e29b-41d4-a716-446655440000",
            }
        }

        with (
            patch(
                "app.services.agent_bridge.evidence_upload_handler._download_telegram_file",
                new_callable=AsyncMock,
                return_value=(file_bytes, "documents/report.pdf"),
            ),
            patch(
                "app.services.agent_bridge.evidence_upload_handler._upload_to_minio",
                new_callable=AsyncMock,
                return_value=None,  # Upload failed
            ),
            patch(
                "app.services.agent_bridge.evidence_upload_handler._send_telegram_reply",
                new_callable=AsyncMock,
                return_value=True,
            ) as mock_reply,
        ):
            result = await handle_evidence_upload(raw_body, "test-token")

        assert result is False
        call_text = mock_reply.call_args[0][2]
        assert "failed" in call_text.lower() or "that bai" in call_text.lower()


# ──────────────────────────────────────────────────────────────────────────────
# Photo Attachment Support
# ──────────────────────────────────────────────────────────────────────────────


class TestPhotoAttachment:
    """Test photo attachment handling (largest size selected)."""

    @pytest.mark.asyncio
    async def test_photo_uses_largest_size(self):
        """Telegram sends multiple photo sizes; we use the largest (last)."""
        raw_body = {
            "message": {
                "chat": {"id": 123},
                "from": {"id": 456},
                "photo": [
                    {"file_id": "small", "file_size": 1024, "width": 90, "height": 90},
                    {"file_id": "medium", "file_size": 5120, "width": 320, "height": 320},
                    {"file_id": "large", "file_size": 20480, "width": 800, "height": 800},
                ],
                "caption": "gate 550e8400-e29b-41d4-a716-446655440000",
            }
        }

        with (
            patch(
                "app.services.agent_bridge.evidence_upload_handler._download_telegram_file",
                new_callable=AsyncMock,
                return_value=None,
            ) as mock_download,
            patch(
                "app.services.agent_bridge.evidence_upload_handler._send_telegram_reply",
                new_callable=AsyncMock,
                return_value=True,
            ),
        ):
            await handle_evidence_upload(raw_body, "test-token")

        # Should use "large" file_id (last in array)
        mock_download.assert_called_once_with("test-token", "large")


# ──────────────────────────────────────────────────────────────────────────────
# AI Response Handler — File Attachment Routing
# ──────────────────────────────────────────────────────────────────────────────


class TestAIHandlerFileRouting:
    """Test that ai_response_handler routes file attachments to evidence handler."""

    @pytest.mark.asyncio
    async def test_document_routed_to_evidence_handler(self):
        """Messages with document attachment should route to evidence handler."""
        from app.services.agent_bridge.ai_response_handler import handle_ai_response

        raw_body = {
            "message": {
                "chat": {"id": 123},
                "from": {"id": 456},
                "document": {
                    "file_id": "abc123",
                    "file_name": "report.pdf",
                    "file_size": 1024,
                },
                "caption": "gate 550e8400-e29b-41d4-a716-446655440000",
            }
        }

        with patch(
            "app.services.agent_bridge.evidence_upload_handler.handle_evidence_upload",
            new_callable=AsyncMock,
            return_value=True,
        ) as mock_evidence:
            result = await handle_ai_response(raw_body, "test-token")

        assert result is True
        mock_evidence.assert_called_once_with(raw_body, "test-token")

    @pytest.mark.asyncio
    async def test_photo_routed_to_evidence_handler(self):
        """Messages with photo attachment should route to evidence handler."""
        from app.services.agent_bridge.ai_response_handler import handle_ai_response

        raw_body = {
            "message": {
                "chat": {"id": 123},
                "from": {"id": 456},
                "photo": [{"file_id": "photo123", "file_size": 2048}],
                "caption": "gate 550e8400-e29b-41d4-a716-446655440000",
            }
        }

        with patch(
            "app.services.agent_bridge.evidence_upload_handler.handle_evidence_upload",
            new_callable=AsyncMock,
            return_value=True,
        ) as mock_evidence:
            result = await handle_ai_response(raw_body, "test-token")

        assert result is True
        mock_evidence.assert_called_once()

    @pytest.mark.asyncio
    async def test_text_only_not_routed_to_evidence(self):
        """Plain text messages without attachments should NOT go to evidence handler."""
        from app.services.agent_bridge.ai_response_handler import handle_ai_response

        raw_body = {
            "message": {
                "chat": {"id": 123},
                "from": {"id": 456},
                "text": "hello world",
            }
        }

        mock_redis = AsyncMock()
        mock_redis.incr = AsyncMock(return_value=1)
        mock_redis.expire = AsyncMock()
        mock_redis.lrange = AsyncMock(return_value=[])
        mock_redis.lpush = AsyncMock()
        mock_redis.ltrim = AsyncMock()

        with (
            patch(
                "app.services.agent_bridge.evidence_upload_handler.handle_evidence_upload",
                new_callable=AsyncMock,
            ) as mock_evidence,
            patch(
                "app.services.agent_bridge.ai_response_handler.get_redis_client",
                new_callable=AsyncMock,
                return_value=mock_redis,
            ),
            patch(
                "app.services.agent_bridge.ai_response_handler.OllamaService",
            ) as mock_ollama_cls,
            patch(
                "app.services.agent_bridge.ai_response_handler.run_in_threadpool",
                new_callable=AsyncMock,
                return_value={"message": {"content": "AI reply"}},
            ),
            patch(
                "app.services.agent_bridge.ai_response_handler._send_telegram_reply",
                new_callable=AsyncMock,
                return_value=True,
            ),
        ):
            await handle_ai_response(raw_body, "test-token")

        # Evidence handler should NOT be called for text-only messages
        mock_evidence.assert_not_called()

    @pytest.mark.asyncio
    async def test_evidence_handler_failure_falls_through(self):
        """If evidence handler fails, caption should fall through to AI chat."""
        from app.services.agent_bridge.ai_response_handler import handle_ai_response

        raw_body = {
            "message": {
                "chat": {"id": 123},
                "from": {"id": 456},
                "document": {
                    "file_id": "abc123",
                    "file_name": "report.pdf",
                    "file_size": 1024,
                },
                "caption": "just a random file, no gate id",
            }
        }

        mock_redis = AsyncMock()
        mock_redis.incr = AsyncMock(return_value=1)
        mock_redis.expire = AsyncMock()
        mock_redis.lrange = AsyncMock(return_value=[])
        mock_redis.lpush = AsyncMock()
        mock_redis.ltrim = AsyncMock()

        with (
            patch(
                "app.services.agent_bridge.evidence_upload_handler.handle_evidence_upload",
                new_callable=AsyncMock,
                return_value=False,  # Handler couldn't process (no gate_id)
            ),
            patch(
                "app.services.agent_bridge.ai_response_handler.get_redis_client",
                new_callable=AsyncMock,
                return_value=mock_redis,
            ),
            patch(
                "app.services.agent_bridge.ai_response_handler.run_in_threadpool",
                new_callable=AsyncMock,
                return_value={"message": {"content": "AI reply about the file"}},
            ),
            patch(
                "app.services.agent_bridge.ai_response_handler._send_telegram_reply",
                new_callable=AsyncMock,
                return_value=True,
            ) as mock_reply,
        ):
            result = await handle_ai_response(raw_body, "test-token")

        # Falls through to AI chat with caption text
        assert result is True
