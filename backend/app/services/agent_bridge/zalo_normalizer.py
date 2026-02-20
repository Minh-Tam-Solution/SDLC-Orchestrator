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

Sprint 181 — ADR-060 D-060-02: Zalo registered as STANDARD tier channel (Vietnam pilot).
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from app.services.agent_bridge.protocol_adapter import OrchestratorMessage, register_normalizer

logger = logging.getLogger(__name__)

_SUPPORTED_EVENTS = {"user_send_text"}


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
    sender_id: str = sender.get("id", "")
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
