"""
Telegram Bot API webhook → OrchestratorMessage normalizer.

Handles Bot Framework update payloads (message, channel_post activity types).
HMAC signature verification is handled upstream in ott_gateway.py.

Field mappings:
    channel         → "telegram" (constant)
    sender_id       → message.from.id cast to str; "channel_post" if absent
    content         → message.text (required; ValueError if absent)
    timestamp       → datetime.utcfromtimestamp(message.date)
    correlation_id  → f"telegram_{message.message_id}"
    metadata        → {chat_id, chat_type, update_id}

Sprint 181 — ADR-060 D-060-02: Telegram registered as STANDARD tier channel.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from app.services.agent_bridge.protocol_adapter import OrchestratorMessage, register_normalizer

logger = logging.getLogger(__name__)


def _parse_telegram(payload: dict) -> OrchestratorMessage:
    """
    Parse a Telegram Bot API update payload into a raw OrchestratorMessage.

    Content sanitization is applied by protocol_adapter.normalize() after
    this function returns.

    Args:
        payload: Raw dict from Telegram Bot API webhook.

    Returns:
        Raw OrchestratorMessage (content not yet sanitized).

    Raises:
        ValueError: If 'message' key is absent or 'text' field is missing.
    """
    if "message" not in payload:
        raise ValueError("telegram payload missing message")

    message: dict = payload["message"]

    text: str | None = message.get("text")
    if text is None:
        raise ValueError("telegram message has no text")

    from_data: dict = message.get("from", {})
    sender_id: str = str(from_data["id"]) if "id" in from_data else "channel_post"

    update_id: int = payload.get("update_id", 0)
    message_id: int = message["message_id"]
    chat: dict = message.get("chat", {})

    timestamp = datetime.fromtimestamp(message["date"], tz=timezone.utc)

    return OrchestratorMessage(
        channel="telegram",
        sender_id=sender_id,
        content=text,  # raw; sanitized by protocol_adapter.normalize()
        timestamp=timestamp,
        correlation_id=f"telegram_{message_id}",
        metadata={
            "chat_id": chat.get("id"),
            "chat_type": chat.get("type"),
            "update_id": update_id,
        },
    )


# Register with the channel dispatcher at import time
register_normalizer("telegram", _parse_telegram)
