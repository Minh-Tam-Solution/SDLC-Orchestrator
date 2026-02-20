"""
Microsoft Teams Bot Framework Activity → OrchestratorMessage normalizer.

Handles Bot Framework Activity payloads received from Microsoft Teams:
    - message:            User sends a text message (most common)
    - invoke:             Adaptive Card action submit or other invoke
    - conversationUpdate: Member added/removed from conversation

HMAC verification is separate from Teams Bot Framework JWT auth. The
verify_hmac() helper validates a shared-secret HMAC-SHA256 signature
appended to Bot Framework requests in some configurations.

Field mappings:
    channel         → "teams" (constant, enforced)
    sender_id       → activity["from"]["aadObjectId"] (Azure AD object ID)
    content         → activity["text"] (empty string for non-text activity types)
    timestamp       → activity["timestamp"] (ISO 8601 string → datetime UTC)
    correlation_id  → activity["id"] (Bot Framework activity ID)
    metadata        → {conversation_id, tenant_id, activity_type}

Tier: PROFESSIONAL+ (ADR-059 BM-10: Teams is enterprise OTT channel)
Sprint 182 — ADR-060 D-060-01, ADR-060 D-060-03
"""

from __future__ import annotations

import hashlib
import hmac
import logging
from datetime import datetime, timezone
from typing import Any

from app.services.agent_bridge.protocol_adapter import OrchestratorMessage, register_normalizer

logger = logging.getLogger(__name__)

# Supported Bot Framework activity types (PA-28: others → ValueError)
_SUPPORTED_ACTIVITY_TYPES: frozenset[str] = frozenset(
    {"message", "invoke", "conversationUpdate"}
)

# Teams channel ID as set by Bot Framework (PA-35)
_TEAMS_CHANNEL_ID: str = "msteams"


# ──────────────────────────────────────────────────────────────────────────────
# HMAC verification
# ──────────────────────────────────────────────────────────────────────────────

def verify_hmac(request_body: bytes, signature: str, secret: str) -> bool:
    """
    Verify a Bot Framework HMAC-SHA256 request signature.

    Computes HMAC-SHA256 of `request_body` with `secret` and compares the
    result against `signature` using hmac.compare_digest() to prevent
    timing-oracle attacks (constant-time comparison, PA-32).

    Args:
        request_body: Raw request body bytes as received from Teams.
        signature:    Hex-encoded HMAC-SHA256 signature from the request header.
        secret:       Shared HMAC secret configured in the Bot registration.

    Returns:
        True if the computed HMAC matches the provided signature.
        False if the signature is absent, malformed, or does not match.
    """
    if not signature or not secret:
        return False

    expected = hmac.new(
        key=secret.encode("utf-8"),
        msg=request_body,
        digestmod=hashlib.sha256,
    ).hexdigest()

    # compare_digest provides constant-time comparison (PA-32)
    return hmac.compare_digest(expected, signature.lower())


# ──────────────────────────────────────────────────────────────────────────────
# Adaptive Card response builder
# ──────────────────────────────────────────────────────────────────────────────

def build_adaptive_card_response(content: str) -> dict[str, Any]:
    """
    Build a Teams Adaptive Card response message.

    Returns a Bot Framework message payload with a single TextBlock card
    targeting Adaptive Cards schema v1.5 (widely supported by Teams desktop
    and mobile clients per Sprint 182 risk assessment).

    Args:
        content: Text content to display in the card body.

    Returns:
        Dict formatted as a Bot Framework message with Adaptive Card attachment.
    """
    return {
        "type": "message",
        "attachments": [
            {
                "contentType": "application/vnd.microsoft.card.adaptive",
                "content": {
                    "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                    "type": "AdaptiveCard",
                    "version": "1.5",
                    "body": [
                        {
                            "type": "TextBlock",
                            "text": content,
                            "wrap": True,
                        }
                    ],
                },
            }
        ],
    }


# ──────────────────────────────────────────────────────────────────────────────
# Activity parser
# ──────────────────────────────────────────────────────────────────────────────

def _parse_teams(payload: dict[str, Any]) -> OrchestratorMessage:
    """
    Parse a Microsoft Teams Bot Framework Activity into a raw OrchestratorMessage.

    Content sanitization is applied by protocol_adapter.normalize() after
    this function returns.

    Args:
        payload: Raw dict from the Teams Bot Framework webhook body.

    Returns:
        Raw OrchestratorMessage (content not yet sanitized by protocol_adapter).

    Raises:
        ValueError: If channelId is not "msteams" (PA-35), or if activity
                    type is not in SUPPORTED_ACTIVITY_TYPES (PA-28).
    """
    # PA-35: Reject payloads not originating from Teams
    channel_id: str = payload.get("channelId", "")
    if channel_id != _TEAMS_CHANNEL_ID:
        raise ValueError(
            f"teams_normalizer: rejecting non-Teams channelId {channel_id!r}; "
            f"expected {_TEAMS_CHANNEL_ID!r}"
        )

    # PA-28: Reject unsupported activity types
    activity_type: str = payload.get("type", "")
    if activity_type not in _SUPPORTED_ACTIVITY_TYPES:
        raise ValueError(
            f"teams_normalizer: unsupported activity type {activity_type!r}; "
            f"supported: {sorted(_SUPPORTED_ACTIVITY_TYPES)}"
        )

    # PA-22: Map from.aadObjectId → sender_id (Azure AD object ID is the stable identifier)
    from_data: dict = payload.get("from", {})
    sender_id: str = from_data.get("aadObjectId") or from_data.get("id", "")

    # PA-21, PA-25: Extract text content.
    # message activities have text; invoke and conversationUpdate may have no text.
    content: str = payload.get("text") or ""

    # PA-23: Map activity.id → correlation_id (Bot Framework assigns unique ID per activity)
    correlation_id: str = payload.get("id", "")

    # PA-24: Parse timestamp (ISO 8601 string → UTC datetime)
    timestamp_str: str = payload.get("timestamp", "")
    try:
        # Bot Framework timestamps: "2026-02-19T10:30:00.000Z"
        ts = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        ts = datetime.now(tz=timezone.utc)

    # PA-26: Extract tenant_id from channelData.tenant.id
    channel_data: dict = payload.get("channelData", {})
    tenant_id: str | None = channel_data.get("tenant", {}).get("id")

    # PA-27: Extract conversation ID for routing (Teams conversation thread)
    conversation: dict = payload.get("conversation", {})
    conversation_id: str | None = conversation.get("id")

    return OrchestratorMessage(
        channel="teams",
        sender_id=sender_id,
        content=content,
        timestamp=ts,
        correlation_id=correlation_id,
        metadata={
            "conversation_id": conversation_id,
            "tenant_id": tenant_id,
            "activity_type": activity_type,
        },
    )


# Register with the channel dispatcher at import time (PA-34)
register_normalizer("teams", _parse_teams)
