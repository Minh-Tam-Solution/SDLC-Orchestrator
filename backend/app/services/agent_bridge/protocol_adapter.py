"""
Protocol adapter — canonical OrchestratorMessage type and channel dispatcher.

Responsibilities:
- Define OrchestratorMessage dataclass (6 fields, immutable after construction)
- Maintain CHANNEL_REGISTRY mapping channel names → normalizer callables
- Dispatch incoming payloads to the correct normalizer
- Apply input sanitization (ADR-058 Pattern C — 12 injection regex patterns)
- Enforce content length limit (4096 chars) with truncation marker

ADR-060 D-060-01: All OTT channels normalized to OrchestratorMessage before
entering the Multi-Agent Team Engine. Protocol is owned by Orchestrator;
TinySDLC and OTT channels are clients.

Sprint 181: telegram + zalo registered.
Sprint 182: teams registered.
Sprint 183: slack added.
"""

from __future__ import annotations

import dataclasses
import logging
from datetime import datetime
from typing import Callable

from app.services.agent_team.input_sanitizer import INJECTION_PATTERNS

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Content limits
# ──────────────────────────────────────────────────────────────────────────────

MAX_CONTENT_LENGTH: int = 4096
_TRUNCATION_MARKER: str = "[TRUNCATED]"


# ──────────────────────────────────────────────────────────────────────────────
# OrchestratorMessage — canonical inbound message type
# ──────────────────────────────────────────────────────────────────────────────

@dataclasses.dataclass(frozen=True)
class OrchestratorMessage:
    """
    Canonical message type for all OTT channel inputs.

    Immutable after construction (frozen=True). All normalizers produce
    an OrchestratorMessage; downstream consumers (message_queue, agent_invoker)
    depend only on this type — not on channel-specific formats.

    Fields:
        channel:        Channel identifier: "telegram" | "zalo" | "teams" | "slack"
        sender_id:      Channel-specific stable user identifier (not display name)
        content:        Sanitized, normalized text content (max 4096 chars)
        timestamp:      UTC datetime of message origin
        correlation_id: Unique trace ID: "{channel}_{message_id}"
        metadata:       Channel-specific extras (chat_id, tenant_id, etc.)
    """

    channel: str
    sender_id: str
    content: str
    timestamp: datetime
    correlation_id: str
    metadata: dict


# ──────────────────────────────────────────────────────────────────────────────
# Channel registry — maps channel name → normalizer callable
# ──────────────────────────────────────────────────────────────────────────────

NormalizerFn = Callable[[dict], OrchestratorMessage]

# Populated at module import time by normalizer modules.
# Sprint 181: telegram, zalo.  Sprint 182: teams added.  Sprint 183: slack.
_CHANNEL_REGISTRY: dict[str, NormalizerFn] = {}


def register_normalizer(channel: str, fn: NormalizerFn) -> None:
    """
    Register a normalizer function for a channel name.

    Called by each normalizer module at import time. Channel names are
    lowercase strings (e.g. "telegram", "zalo", "teams", "slack").
    """
    _CHANNEL_REGISTRY[channel] = fn
    logger.debug("agent_bridge: registered normalizer for channel '%s'", channel)


# ──────────────────────────────────────────────────────────────────────────────
# Sanitization helpers
# ──────────────────────────────────────────────────────────────────────────────

def _sanitize_content(text: str) -> str:
    """
    Validate and sanitize OTT content before storage in OrchestratorMessage.

    Steps:
    1. Raise ValueError on empty or whitespace-only text (PA-17)
    2. Truncate to MAX_CONTENT_LENGTH with TRUNCATION_MARKER (PA-18)
    3. Strip each of the 12 injection patterns (ADR-058 Pattern C, PA-12)

    Truncation runs before injection scanning to bound regex work to at most
    4096 chars. Injection patterns are then applied to the already-truncated
    text; the [TRUNCATED] marker is preserved at the end.

    Returns:
        Sanitized content string (max 4096 chars, injection patterns replaced
        with [BLOCKED:{pattern_name}] tokens).

    Raises:
        ValueError: if text is empty or whitespace-only.
    """
    if not text or not text.strip():
        raise ValueError("OTT content must not be empty")

    # Truncate first (PA-18): bound regex work to MAX_CONTENT_LENGTH chars
    if len(text) > MAX_CONTENT_LENGTH:
        cut = MAX_CONTENT_LENGTH - len(_TRUNCATION_MARKER)
        text = text[:cut] + _TRUNCATION_MARKER

    # Strip injection patterns (PA-12) — applied to already-truncated text
    for name, pattern in INJECTION_PATTERNS:
        text = pattern.sub(f"[BLOCKED:{name}]", text)

    return text


# ──────────────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────────────

def normalize(raw_payload: dict, channel: str) -> OrchestratorMessage:
    """
    Normalize a raw OTT webhook payload into an OrchestratorMessage.

    Pipeline:
    1. Look up channel in _CHANNEL_REGISTRY — ValueError on unknown channel
    2. Call the normalizer to produce a raw OrchestratorMessage
    3. Sanitize content (empty check, length truncation, injection strip)
    4. Return new OrchestratorMessage with sanitized content

    Args:
        raw_payload: Raw dict from the OTT webhook body.
        channel:     Channel identifier string (must be in _CHANNEL_REGISTRY).

    Returns:
        OrchestratorMessage with sanitized content.

    Raises:
        ValueError: Unknown channel, missing required fields, or empty content.
    """
    if channel not in _CHANNEL_REGISTRY:
        raise ValueError(f"unsupported channel: {channel!r}")

    normalizer = _CHANNEL_REGISTRY[channel]
    raw_msg: OrchestratorMessage = normalizer(raw_payload)

    sanitized_content = _sanitize_content(raw_msg.content)

    return dataclasses.replace(raw_msg, content=sanitized_content)


def route_to_normalizer(channel: str, payload: dict) -> OrchestratorMessage:
    """
    Route a payload to the appropriate normalizer with structured logging.

    Wraps normalize() with logging of channel, correlation_id, and
    content_length for observability. Raises ValueError on unknown channel
    so callers can convert to HTTP 400.

    Args:
        channel: Channel identifier string.
        payload: Raw dict from the OTT webhook body.

    Returns:
        OrchestratorMessage with sanitized content (identical to normalize()).

    Raises:
        ValueError: Unknown channel, missing required fields, or empty content.
    """
    msg = normalize(raw_payload=payload, channel=channel)
    logger.info(
        "agent_bridge: routed message channel=%s correlation_id=%s content_length=%d",
        msg.channel,
        msg.correlation_id,
        len(msg.content),
    )
    return msg


# ──────────────────────────────────────────────────────────────────────────────
# Register built-in normalizers at import time
# ──────────────────────────────────────────────────────────────────────────────

# Import triggers side-effect: each module calls register_normalizer()
from app.services.agent_bridge import telegram_normalizer as _tg    # noqa: E402, F401
from app.services.agent_bridge import zalo_normalizer as _za        # noqa: E402, F401
from app.services.agent_bridge import teams_normalizer as _teams    # noqa: E402, F401
from app.services.agent_bridge import slack_normalizer as _slack    # noqa: E402, F401
