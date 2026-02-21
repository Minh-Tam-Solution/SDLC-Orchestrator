"""
Slack Events API → OrchestratorMessage normalizer.

Handles Slack Events API payloads received from Slack's Event Subscriptions:
    - event_callback:    User sends a message or mentions the bot (message, app_mention)
    - url_verification:  Slack's one-time endpoint verification handshake

HMAC-SHA256 signature verification (Slack Signing Secret, PA-43):
    base_string = f"v0:{timestamp}:{body}"
    signature   = "v0=" + hexdigest(HMAC-SHA256(signing_secret, base_string))

Replay protection (PA-38): reject if |now - timestamp| > 300 seconds.
Constant-time comparison (PA-40): hmac.compare_digest() prevents timing oracles.

Field mappings:
    channel         → "slack" (constant, enforced)
    sender_id       → event["user"] (Slack user ID, e.g. "U123456")
    content         → event["text"] (empty string for non-text event types)
    timestamp       → datetime.fromtimestamp(payload["event_time"], UTC)
    correlation_id  → "slack_" + payload["event_id"]
    metadata        → {team_id, channel_id, event_type}

Tier: PROFESSIONAL+ (ADR-059 BM-10: Slack is enterprise OTT channel)
Sprint 183 — ADR-060 D-060-01, ADR-060 D-060-03
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import time
from datetime import datetime, timezone
from typing import Any

from app.services.agent_bridge.protocol_adapter import OrchestratorMessage, register_normalizer

logger = logging.getLogger(__name__)

# Supported Slack event types within event_callback payloads (PA-44)
_SUPPORTED_EVENT_TYPES: frozenset[str] = frozenset({"message", "app_mention"})

# Replay protection window: 5 minutes (PA-38 — same window as Slack docs)
_REPLAY_PROTECTION_WINDOW_SECONDS: int = 300

# Slack signature version prefix (always "v0" per Slack API docs)
_SLACK_SIG_VERSION: str = "v0"


# ──────────────────────────────────────────────────────────────────────────────
# Slack URL verification exception
# ──────────────────────────────────────────────────────────────────────────────

class SlackUrlVerificationError(Exception):
    """
    Raised by _parse_slack when payload type is "url_verification".

    Callers (ott_gateway) catch this exception and respond with:
        {"challenge": exc.challenge}
    as required by the Slack Events API subscription handshake.

    Attributes:
        challenge: The challenge string from the Slack verification payload.
    """

    def __init__(self, challenge: str) -> None:
        super().__init__(f"slack url_verification challenge: {challenge}")
        self.challenge: str = challenge


# ──────────────────────────────────────────────────────────────────────────────
# Signature verification
# ──────────────────────────────────────────────────────────────────────────────

def verify_signature(
    body: bytes,
    timestamp: str,
    signature: str,
    signing_secret: str,
) -> bool:
    """
    Verify Slack's HMAC-SHA256 request signature with replay protection.

    Slack signing algorithm:
        base_string = f"v0:{timestamp}:{body.decode()}"
        expected    = "v0=" + HMAC-SHA256(signing_secret, base_string).hexdigest()

    Replay protection (PA-38):
        Reject if |now - int(timestamp)| > 300 seconds.
        This prevents replay of captured requests.

    Constant-time comparison (PA-40):
        hmac.compare_digest() prevents timing-oracle attacks.

    Args:
        body:           Raw request body bytes.
        timestamp:      X-Slack-Request-Timestamp header value (Unix epoch string).
        signature:      X-Slack-Signature header value ("v0=<hexdigest>").
        signing_secret: Slack app signing secret from environment config.

    Returns:
        True if the signature is valid and the request is within the replay window.
        False if timestamp, signature, or secret is absent/malformed, or if the
        replay window is exceeded, or if the HMAC does not match.
    """
    if not body or not timestamp or not signature or not signing_secret:
        return False

    # PA-38: Replay protection — reject stale requests
    try:
        request_ts = int(timestamp)
    except (ValueError, TypeError):
        return False

    if abs(time.time() - request_ts) > _REPLAY_PROTECTION_WINDOW_SECONDS:
        logger.warning(
            "slack_normalizer: rejected replayed request timestamp=%s age_seconds=%s",
            timestamp,
            abs(time.time() - request_ts),
        )
        return False

    # Compute expected signature: "v0=" + HMAC-SHA256(secret, "v0:{ts}:{body}")
    base_string = f"{_SLACK_SIG_VERSION}:{timestamp}:{body.decode('utf-8')}"
    expected_hex = hmac.new(
        key=signing_secret.encode("utf-8"),
        msg=base_string.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()
    expected_sig = f"{_SLACK_SIG_VERSION}={expected_hex}"

    # PA-40: Constant-time comparison to prevent timing oracle
    return hmac.compare_digest(expected_sig, signature)


# ──────────────────────────────────────────────────────────────────────────────
# Block Kit response builder
# ──────────────────────────────────────────────────────────────────────────────

def build_block_kit_response(content: str) -> dict[str, Any]:
    """
    Build a Slack Block Kit message payload for bot responses.

    Returns a single-block message with a mrkdwn-formatted section.
    Block Kit is the Slack-recommended way to format rich messages.

    Args:
        content: Text content to display. Supports Slack mrkdwn formatting.

    Returns:
        Dict formatted as a Slack Block Kit message payload suitable for
        posting via the Slack Web API (chat.postMessage).
    """
    return {
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": content,
                },
            }
        ],
        "text": content,  # Fallback text for notifications and accessibility
    }


# ──────────────────────────────────────────────────────────────────────────────
# Payload parser
# ──────────────────────────────────────────────────────────────────────────────

def _parse_slack(payload: dict[str, Any]) -> OrchestratorMessage:
    """
    Parse a Slack Events API payload into a raw OrchestratorMessage.

    Content sanitization is applied by protocol_adapter.normalize() after
    this function returns.

    Supported payload types:
        event_callback:   Routes to OrchestratorMessage (message or app_mention).
        url_verification: Raises SlackUrlVerificationError with challenge string.

    Args:
        payload: Raw dict from the Slack Events API webhook body.

    Returns:
        Raw OrchestratorMessage (content not yet sanitized by protocol_adapter).

    Raises:
        SlackUrlVerificationError: When payload type is "url_verification". Callers
                                   must catch this and respond with the challenge.
        ValueError: If payload type is not "event_callback" or "url_verification"
                    (PA-44), or if the inner event.type is not in
                    SUPPORTED_EVENT_TYPES.
    """
    payload_type: str = payload.get("type", "")

    # Handle Slack endpoint verification handshake (one-time, PA-43)
    if payload_type == "url_verification":
        challenge: str = payload.get("challenge", "")
        if not challenge:
            raise ValueError("slack_normalizer: url_verification missing challenge field")
        raise SlackUrlVerificationError(challenge)

    # PA-44: Reject unsupported payload types
    if payload_type != "event_callback":
        raise ValueError(
            f"slack_normalizer: unsupported payload type {payload_type!r}; "
            f"supported: 'event_callback', 'url_verification'"
        )

    event: dict = payload.get("event", {})
    event_type: str = event.get("type", "")

    # PA-44: Reject unsupported event types within event_callback
    if event_type not in _SUPPORTED_EVENT_TYPES:
        raise ValueError(
            f"slack_normalizer: unsupported event type {event_type!r}; "
            f"supported: {sorted(_SUPPORTED_EVENT_TYPES)}"
        )

    # PA-45: Map event.user → sender_id (Slack user ID is stable identifier)
    sender_id: str = event.get("user", "")

    # PA-49: Extract text content (app_mention text includes bot mention token)
    content: str = event.get("text") or ""

    # PA-46: correlation_id = "slack_" + event_id (unique per Slack event)
    event_id: str = payload.get("event_id", "")
    correlation_id: str = f"slack_{event_id}" if event_id else ""

    # PA-48: Parse event_time (Unix epoch integer from top-level payload)
    event_time: int | float = payload.get("event_time", 0)
    try:
        ts = datetime.fromtimestamp(float(event_time), tz=timezone.utc)
    except (ValueError, TypeError, OSError):
        ts = datetime.now(tz=timezone.utc)

    # PA-49: Extract team_id and channel_id for metadata
    team_id: str | None = payload.get("team_id")
    channel_id: str | None = event.get("channel")

    return OrchestratorMessage(
        channel="slack",
        sender_id=sender_id,
        content=content,
        timestamp=ts,
        correlation_id=correlation_id,
        metadata={
            "team_id": team_id,
            "channel_id": channel_id,
            "event_type": event_type,
        },
    )


# Register with the channel dispatcher at import time (PA-34)
register_normalizer("slack", _parse_slack)
