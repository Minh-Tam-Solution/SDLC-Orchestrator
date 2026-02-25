"""
Evidence Upload Handler — OTT file attachment → Evidence Vault bridge.

Sprint 199 — Track B: Evidence Upload via OTT (B-01, B-02, B-03, B-04).

When a user sends a file attachment on Telegram with a caption referencing
a gate (e.g., "evidence for gate <uuid>"), this handler:

    1. Downloads the file via Telegram Bot API (getFile → download)
    2. Validates file size (max 10MB for OTT, B-04)
    3. Computes SHA256 hash for integrity
    4. Uploads to MinIO S3 (AGPL-safe, network-only via requests)
    5. Creates GateEvidence record in PostgreSQL
    6. Sends confirmation reply to Telegram (B-03)

Architecture (ADR-060): Lives in agent_bridge/ (channel abstraction layer).
Uses AsyncSessionLocal for standalone DB sessions in fire-and-forget context.
AGPL Containment: Direct HTTP to MinIO (same pattern as gates.py upload).
"""

from __future__ import annotations

import hashlib
import logging
import os
import re
import time
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

import httpx

from app.services.agent_team.output_scrubber import OutputScrubber

logger = logging.getLogger(__name__)

# Configuration
_MAX_FILE_SIZE_BYTES: int = 10 * 1024 * 1024  # 10MB limit for OTT uploads (B-04)
_TELEGRAM_DOWNLOAD_TIMEOUT: float = 30.0  # seconds
_MINIO_UPLOAD_TIMEOUT: float = 60.0  # seconds
_TELEGRAM_MSG_LIMIT: int = 4000  # Telegram message char limit

# MinIO configuration (network-only, AGPL-safe)
_MINIO_URL: str = os.getenv("MINIO_URL", "http://minio:9000")
_MINIO_BUCKET: str = os.getenv("MINIO_BUCKET", "sdlc-evidence")
_MINIO_ACCESS_KEY: str = os.getenv("MINIO_ACCESS_KEY", "")
_MINIO_SECRET_KEY: str = os.getenv("MINIO_SECRET_KEY", "")

_scrubber = OutputScrubber()

# Gate UUID extraction pattern — matches full UUID or short prefix
_GATE_UUID_PATTERN = re.compile(
    r"(?:gate\s+|gate_id\s*[=:]\s*)"
    r"([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})",
    re.IGNORECASE,
)

# Evidence type hints from caption text
_EVIDENCE_TYPE_KEYWORDS: dict[str, str] = {
    "test": "test_report",
    "kiểm thử": "test_report",
    "design": "DESIGN_DOCUMENT",
    "thiết kế": "DESIGN_DOCUMENT",
    "review": "CODE_REVIEW",
    "deployment": "DEPLOYMENT_PROOF",
    "triển khai": "DEPLOYMENT_PROOF",
    "compliance": "COMPLIANCE",
    "tuân thủ": "COMPLIANCE",
}


def _extract_gate_id(text: str) -> str | None:
    """Extract gate UUID from caption text."""
    match = _GATE_UUID_PATTERN.search(text)
    if match:
        return match.group(1)
    return None


def _infer_evidence_type(text: str, file_name: str) -> str:
    """Infer evidence type from caption text or file name."""
    combined = f"{text} {file_name}".lower()
    for keyword, ev_type in _EVIDENCE_TYPE_KEYWORDS.items():
        if keyword in combined:
            return ev_type
    # Default based on file extension
    if file_name.lower().endswith((".pdf", ".doc", ".docx", ".md")):
        return "DESIGN_DOCUMENT"
    if file_name.lower().endswith((".html", ".xml", ".json")):
        return "test_report"
    if file_name.lower().endswith((".png", ".jpg", ".jpeg", ".gif")):
        return "DEPLOYMENT_PROOF"
    return "other"


async def _send_telegram_reply(
    bot_token: str,
    chat_id: str | int,
    text: str,
) -> bool:
    """Send reply message to Telegram chat."""
    if not bot_token:
        return False
    try:
        clean_text, _ = _scrubber.scrub(text)
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"https://api.telegram.org/bot{bot_token}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": clean_text[:_TELEGRAM_MSG_LIMIT],
                },
            )
            return resp.status_code == 200
    except Exception as exc:
        logger.warning(
            "evidence_upload_handler: sendMessage error chat_id=%s error=%s",
            chat_id,
            str(exc),
        )
        return False


async def _download_telegram_file(
    bot_token: str,
    file_id: str,
) -> tuple[bytes, str] | None:
    """
    Download file from Telegram Bot API (B-01).

    Two-step process:
        1. getFile(file_id) → file_path
        2. Download from https://api.telegram.org/file/bot{token}/{file_path}

    Returns:
        Tuple of (file_bytes, file_path) or None on failure.
    """
    try:
        async with httpx.AsyncClient(timeout=_TELEGRAM_DOWNLOAD_TIMEOUT) as client:
            # Step 1: Get file path
            resp = await client.post(
                f"https://api.telegram.org/bot{bot_token}/getFile",
                json={"file_id": file_id},
            )
            if resp.status_code != 200:
                logger.warning(
                    "evidence_upload_handler: getFile failed status=%s",
                    resp.status_code,
                )
                return None

            data = resp.json()
            if not data.get("ok"):
                logger.warning("evidence_upload_handler: getFile not ok")
                return None

            file_path = data.get("result", {}).get("file_path", "")
            if not file_path:
                logger.warning("evidence_upload_handler: no file_path in response")
                return None

            # Step 2: Download file bytes
            download_resp = await client.get(
                f"https://api.telegram.org/file/bot{bot_token}/{file_path}",
            )
            if download_resp.status_code != 200:
                logger.warning(
                    "evidence_upload_handler: file download failed status=%s",
                    download_resp.status_code,
                )
                return None

            return download_resp.content, file_path

    except Exception as exc:
        logger.error(
            "evidence_upload_handler: download failed file_id=%s error=%s",
            file_id,
            str(exc),
        )
        return None


async def _upload_to_minio(
    file_bytes: bytes,
    s3_key: str,
    content_type: str,
) -> str | None:
    """
    Upload file bytes to MinIO via S3 API (AGPL-safe, network-only).

    Same pattern as gates.py evidence upload endpoint — direct HTTP PUT.

    Returns:
        SHA256 hex digest on success, None on failure.
    """
    sha256_hash = hashlib.sha256(file_bytes).hexdigest()

    try:
        # Use httpx for async upload (not sync requests)
        import base64
        import hmac as hmac_mod
        from datetime import datetime as dt

        # Simple unauthenticated PUT — matching existing dev/staging pattern
        # Production uses MINIO_ACCESS_KEY auth via boto3 in minio_service.py
        async with httpx.AsyncClient(timeout=_MINIO_UPLOAD_TIMEOUT) as client:
            resp = await client.put(
                f"{_MINIO_URL}/{_MINIO_BUCKET}/{s3_key}",
                content=file_bytes,
                headers={
                    "Content-Type": content_type,
                    "x-amz-meta-sha256": sha256_hash,
                    "x-amz-meta-source": "ott",
                },
            )
            if resp.status_code in (200, 201, 204):
                logger.info(
                    "evidence_upload_handler: uploaded s3://%s/%s sha256=%s",
                    _MINIO_BUCKET,
                    s3_key,
                    sha256_hash[:16],
                )
                return sha256_hash
            logger.warning(
                "evidence_upload_handler: MinIO upload failed status=%s body=%s",
                resp.status_code,
                resp.text[:200],
            )
            return None
    except Exception as exc:
        logger.error(
            "evidence_upload_handler: MinIO upload error s3_key=%s error=%s",
            s3_key,
            str(exc),
        )
        return None


def _format_evidence_confirmation(
    file_name: str,
    file_size: int,
    sha256_hash: str,
    evidence_type: str,
    gate_id: str,
) -> str:
    """Format bilingual confirmation reply (B-03)."""
    size_kb = file_size / 1024
    size_str = f"{size_kb:.1f} KB" if size_kb < 1024 else f"{size_kb / 1024:.1f} MB"

    return (
        "Evidence uploaded / Bang chung da tai len\n\n"
        f"File: {file_name}\n"
        f"Size: {size_str}\n"
        f"Type: {evidence_type}\n"
        f"Gate: {gate_id}\n"
        f"SHA256: {sha256_hash[:16]}...\n"
        f"Source: ott\n\n"
        "Evidence stored in Evidence Vault with integrity verification."
    )


def _format_error(message: str) -> str:
    """Format bilingual error reply."""
    return f"Evidence upload failed / Tai bang chung that bai\n\n{message}"


async def handle_evidence_upload(
    raw_body: dict[str, Any],
    bot_token: str,
) -> bool:
    """
    Process a Telegram file attachment and upload to Evidence Vault.

    This is the main entry point called from ai_response_handler.py when
    a message contains a file attachment (document or photo).

    Flow:
        1. Extract file_id + caption from Telegram payload
        2. Parse gate_id from caption (required)
        3. Validate file size (B-04: max 10MB)
        4. Download file via Bot API (B-01)
        5. Upload to MinIO S3 (AGPL-safe)
        6. Create GateEvidence record in DB (B-02)
        7. Send confirmation reply (B-03)

    Args:
        raw_body: Raw Telegram webhook update payload.
        bot_token: Telegram Bot API token.

    Returns:
        True if evidence was uploaded, False otherwise.
    """
    message: dict[str, Any] | None = raw_body.get("message")
    if not message:
        return False

    chat_id = message.get("chat", {}).get("id")
    if not chat_id:
        return False

    # Extract file info from document or photo
    document = message.get("document")
    photo_list = message.get("photo")

    file_id: str | None = None
    file_name: str = "attachment"
    file_size: int = 0
    content_type: str = "application/octet-stream"

    if document:
        file_id = document.get("file_id")
        file_name = document.get("file_name", "document")
        file_size = document.get("file_size", 0)
        content_type = document.get("mime_type", "application/octet-stream")
    elif photo_list and isinstance(photo_list, list) and len(photo_list) > 0:
        # Telegram sends multiple photo sizes; use largest (last)
        largest_photo = photo_list[-1]
        file_id = largest_photo.get("file_id")
        file_size = largest_photo.get("file_size", 0)
        file_name = "photo.jpg"
        content_type = "image/jpeg"

    if not file_id:
        return False

    caption: str = (message.get("caption") or message.get("text") or "").strip()
    sender_id = str(message.get("from", {}).get("id", ""))

    # B-04: File size validation (10MB limit)
    if file_size > _MAX_FILE_SIZE_BYTES:
        size_mb = file_size / (1024 * 1024)
        await _send_telegram_reply(
            bot_token,
            chat_id,
            _format_error(
                f"File qua lon: {size_mb:.1f} MB (toi da 10 MB).\n"
                f"File too large: {size_mb:.1f} MB (max 10 MB)."
            ),
        )
        logger.info(
            "evidence_upload_handler: file too large chat_id=%s size=%d",
            chat_id,
            file_size,
        )
        return False

    # Extract gate_id from caption (required for evidence binding)
    gate_id_str = _extract_gate_id(caption)
    if not gate_id_str:
        await _send_telegram_reply(
            bot_token,
            chat_id,
            _format_error(
                "Vui long chi dinh gate ID trong caption.\n"
                "Please specify gate ID in caption.\n\n"
                'Vi du / Example: "evidence for gate 550e8400-e29b-41d4-a716-446655440000"'
            ),
        )
        return False

    # Validate gate_id format
    try:
        gate_uuid = UUID(gate_id_str)
    except ValueError:
        await _send_telegram_reply(
            bot_token,
            chat_id,
            _format_error(f"Gate ID khong hop le / Invalid gate ID: {gate_id_str}"),
        )
        return False

    # Infer evidence type from caption/filename
    evidence_type = _infer_evidence_type(caption, file_name)

    # B-01: Download file from Telegram
    download_result = await _download_telegram_file(bot_token, file_id)
    if not download_result:
        await _send_telegram_reply(
            bot_token,
            chat_id,
            _format_error(
                "Khong the tai file tu Telegram. Vui long thu lai.\n"
                "Could not download file from Telegram. Please try again."
            ),
        )
        return False

    file_bytes, _file_path = download_result
    actual_size = len(file_bytes)

    # Double-check size after download (Telegram file_size can be approximate)
    if actual_size > _MAX_FILE_SIZE_BYTES:
        await _send_telegram_reply(
            bot_token,
            chat_id,
            _format_error(
                f"File qua lon sau khi tai: {actual_size / (1024 * 1024):.1f} MB (toi da 10 MB)."
            ),
        )
        return False

    # Upload to MinIO S3 (AGPL-safe, network-only)
    timestamp_suffix = int(time.time())
    s3_key = f"evidence/{gate_uuid}/{timestamp_suffix}_{file_name}"

    sha256_hash = await _upload_to_minio(file_bytes, s3_key, content_type)
    if not sha256_hash:
        await _send_telegram_reply(
            bot_token,
            chat_id,
            _format_error(
                "Luu tru file that bai. Vui long thu lai.\n"
                "File storage failed. Please try again."
            ),
        )
        return False

    # B-02: Create GateEvidence record in DB
    try:
        from app.db.session import AsyncSessionLocal
        from app.models.gate_evidence import GateEvidence

        async with AsyncSessionLocal() as db:
            evidence = GateEvidence(
                gate_id=gate_uuid,
                file_name=file_name,
                file_size=actual_size,
                file_type=content_type,
                evidence_type=evidence_type,
                s3_key=s3_key,
                s3_bucket=_MINIO_BUCKET,
                sha256_hash=sha256_hash,
                sha256_server=sha256_hash,
                source="ott",
                description=f"Uploaded via Telegram OTT by user {sender_id}",
                uploaded_at=datetime.now(timezone.utc),
            )
            db.add(evidence)
            await db.commit()
            await db.refresh(evidence)

            evidence_id = str(evidence.id)

        logger.info(
            "evidence_upload_handler: evidence created id=%s gate=%s sha256=%s",
            evidence_id,
            gate_uuid,
            sha256_hash[:16],
        )
    except Exception as exc:
        logger.error(
            "evidence_upload_handler: DB insert failed gate=%s error=%s",
            gate_uuid,
            str(exc),
        )
        # File is already in MinIO — log but still inform user
        await _send_telegram_reply(
            bot_token,
            chat_id,
            _format_error(
                "File da luu nhung khong tao duoc ban ghi. Lien he admin.\n"
                "File stored but record creation failed. Contact admin."
            ),
        )
        return False

    # B-03: Send confirmation reply
    confirmation = _format_evidence_confirmation(
        file_name=file_name,
        file_size=actual_size,
        sha256_hash=sha256_hash,
        evidence_type=evidence_type,
        gate_id=str(gate_uuid),
    )
    await _send_telegram_reply(bot_token, chat_id, confirmation)

    return True
