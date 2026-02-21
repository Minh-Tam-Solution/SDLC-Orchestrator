"""
Zalo OA (Official Account) webhook → OrchestratorMessage normalizer.

Handles 'user_send_text' event type only. All other eventNames raise ValueError.

Field mappings:
    channel         → "zalo" (constant)
    sender_id       → sender.id
    content         → message.text (required; ValueError if absent)
    timestamp       → datetime.utcfromtimestamp(timestamp / 1000)  # ms → s
    correlation_id  → f"zalo_{timestamp}_{sender.id}"
    metadata        → {event_name, recipient_id}

Signature verification (Sprint 192 — CTO P0-1):
    Zalo OA uses plain SHA256 (NOT HMAC-SHA256). The signature is sent in
    the ``X-ZEvent-Signature`` header and computed as:
        mac = sha256(app_id + body_string + timestamp + oa_secret_key)
    where app_id and timestamp come from the parsed JSON body.
    No replay protection — Zalo does not provide a separate timestamp header
    (documented limitation; CTO acknowledged).

Sprint 181 — ADR-060 D-060-02: Zalo registered as STANDARD tier channel (Vietnam pilot).
"""

from __future__ import annotations

import hashlib
import hmac
import logging
from datetime import datetime, timezone

from app.services.agent_bridge.protocol_adapter import OrchestratorMessage, register_normalizer

logger = logging.getLogger(__name__)

_SUPPORTED_EVENTS = {"user_send_text"}


# ──────────────────────────────────────────────────────────────────────────────
# Signature verification (Sprint 192)
# ──────────────────────────────────────────────────────────────────────────────

def verify_signature(
    body: bytes,
    signature: str,
    app_id: str,
    timestamp: str,
    oa_secret_key: str,
) -> bool:
    """
    Verify a Zalo OA webhook signature (X-ZEvent-Signature header).

    Zalo uses plain SHA256 of the concatenation:
        sha256(app_id + body_utf8 + timestamp + oa_secret_key)

    No replay protection is available because Zalo OA does not provide a
    separate timestamp header — the timestamp is embedded in the JSON body
    and is already part of the signed data, preventing tampering but not
    replay.

    Args:
        body:           Raw request body bytes as received.
        signature:      Hex-encoded SHA256 from X-ZEvent-Signature header.
        app_id:         Zalo application ID (from parsed body or config).
        timestamp:      Timestamp string from the parsed body.
        oa_secret_key:  OA secret key from Zalo Developer console.

    Returns:
        True if the computed hash matches the provided signature.
        False if any input is missing or the signature does not match.
    """
    if not signature or not oa_secret_key or not app_id:
        return False

    body_str = body.decode("utf-8", errors="replace")
    base_string = f"{app_id}{body_str}{timestamp}{oa_secret_key}"
    expected = hashlib.sha256(base_string.encode("utf-8")).hexdigest()

    # hmac.compare_digest for constant-time comparison (PA-40 timing oracle)
    return hmac.compare_digest(expected, signature.lower())


def _parse_zalo(payload: dict) -> OrchestratorMessage:
    """
    Parse a Zalo OA webhook payload into a raw OrchestratorMessage.

    Content sanitization is applied by protocol_adapter.normalize() after
    this function returns.

    Args:
        payload: Raw dict from Zalo OA Webhook.

    Returns:
        Raw OrchestratorMessage (content not yet sanitized).

    Raises:
        ValueError: Unsupported eventName or missing message.text.
    """
    event_name: str = payload.get("eventName", "")
    if event_name not in _SUPPORTED_EVENTS:
        raise ValueError(f"unsupported zalo event: {event_name!r}")

    message: dict = payload.get("message", {})
    text: str | None = message.get("text")
    if text is None:
        raise ValueError("zalo payload missing message text")

    sender: dict = payload.get("sender", {})
    # Sprint 191: Named sentinel instead of empty string (matches Telegram "channel_post" pattern)
    sender_id: str = sender.get("id") or "zalo_unknown"
    recipient: dict = payload.get("recipient", {})

    # Zalo timestamps are in milliseconds — convert to seconds
    ts_ms: int = payload.get("timestamp", 0)
    timestamp = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc)

    return OrchestratorMessage(
        channel="zalo",
        sender_id=sender_id,
        content=text,  # raw; sanitized by protocol_adapter.normalize()
        timestamp=timestamp,
        correlation_id=f"zalo_{ts_ms}_{sender_id}",
        metadata={
            "event_name": event_name,
            "recipient_id": recipient.get("id"),
        },
    )


# Register with the channel dispatcher at import time
register_normalizer("zalo", _parse_zalo)
