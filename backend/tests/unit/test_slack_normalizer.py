"""
Slack normalizer unit tests — PA-36 to PA-50.

Tests cover:
    PA-36: verify_signature returns True for valid HMAC
    PA-37: verify_signature returns False for invalid HMAC
    PA-38: verify_signature returns False for replayed timestamps (>5min old)
    PA-39: verify_signature returns False when secret or signature is empty
    PA-40: verify_signature uses hmac.compare_digest (timing-safe)
    PA-41: _parse_slack handles app_mention event → OrchestratorMessage
    PA-42: _parse_slack handles message event → OrchestratorMessage
    PA-43: _parse_slack raises SlackUrlVerificationError for url_verification
    PA-44: _parse_slack raises ValueError for unsupported payload/event types
    PA-45: sender_id maps to event["user"]
    PA-46: correlation_id = "slack_" + event_id
    PA-47: channel field is always "slack"
    PA-48: timestamp parsed from payload["event_time"] (Unix epoch)
    PA-49: metadata contains team_id, channel_id, event_type
    PA-50: build_block_kit_response returns proper Block Kit format

All tests use only stdlib mocks — no real Slack API, no network I/O.

Sprint 183 — OTT Slack Normalizer
"""

import hashlib
import hmac
import time
from datetime import timezone
from unittest.mock import patch

import pytest

from app.services.agent_bridge.slack_normalizer import (
    SlackUrlVerificationError,
    _REPLAY_PROTECTION_WINDOW_SECONDS,
    _SLACK_SIG_VERSION,
    _SUPPORTED_EVENT_TYPES,
    _parse_slack,
    build_block_kit_response,
    verify_signature,
)


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _make_signature(body: bytes, timestamp: str, secret: str) -> str:
    """Compute a valid Slack HMAC-SHA256 signature for test fixtures."""
    base = f"v0:{timestamp}:{body.decode('utf-8')}"
    hex_digest = hmac.new(
        key=secret.encode("utf-8"),
        msg=base.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()
    return f"v0={hex_digest}"


def _event_callback_payload(
    event_type: str = "app_mention",
    user: str = "U123ABC",
    text: str = "Hello <@UBOT>",
    event_id: str = "Ev0TEST123",
    event_time: int = 1700000000,
    team_id: str = "T0TEAM01",
    channel: str = "C0CHAN01",
) -> dict:
    """Build a minimal valid Slack event_callback payload."""
    return {
        "type": "event_callback",
        "event": {
            "type": event_type,
            "user": user,
            "text": text,
            "channel": channel,
            "event_ts": "1700000000.000001",
        },
        "event_id": event_id,
        "event_time": event_time,
        "team_id": team_id,
        "api_app_id": "A0APP01",
    }


# ──────────────────────────────────────────────────────────────────────────────
# PA-36: valid HMAC → True
# ──────────────────────────────────────────────────────────────────────────────

def test_pa36_verify_signature_valid_hmac_returns_true():
    """PA-36: verify_signature returns True for a correctly computed signature."""
    secret = "test_signing_secret"
    body = b'{"type":"event_callback"}'
    ts = str(int(time.time()))
    sig = _make_signature(body, ts, secret)

    assert verify_signature(body, ts, sig, secret) is True


# ──────────────────────────────────────────────────────────────────────────────
# PA-37: tampered signature → False
# ──────────────────────────────────────────────────────────────────────────────

def test_pa37_verify_signature_invalid_hmac_returns_false():
    """PA-37: verify_signature returns False for a tampered/incorrect signature."""
    secret = "test_signing_secret"
    body = b'{"type":"event_callback"}'
    ts = str(int(time.time()))
    bad_sig = "v0=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"

    assert verify_signature(body, ts, bad_sig, secret) is False


# ──────────────────────────────────────────────────────────────────────────────
# PA-38: replayed timestamp → False
# ──────────────────────────────────────────────────────────────────────────────

def test_pa38_verify_signature_replayed_timestamp_returns_false():
    """PA-38: verify_signature returns False for timestamps older than 5 minutes."""
    secret = "test_signing_secret"
    body = b'{"type":"event_callback"}'
    # Use a timestamp 6 minutes in the past
    stale_ts = str(int(time.time()) - _REPLAY_PROTECTION_WINDOW_SECONDS - 60)
    sig = _make_signature(body, stale_ts, secret)

    assert verify_signature(body, stale_ts, sig, secret) is False


# ──────────────────────────────────────────────────────────────────────────────
# PA-39: missing credentials → False
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "body, timestamp, signature, secret",
    [
        (b"", str(int(time.time())), "v0=abc", "secret"),    # empty body
        (b"payload", str(int(time.time())), "", "secret"),   # empty signature
        (b"payload", str(int(time.time())), "v0=abc", ""),   # empty secret
        (b"payload", "", "v0=abc", "secret"),                # empty timestamp
    ],
)
def test_pa39_verify_signature_missing_params_returns_false(body, timestamp, signature, secret):
    """PA-39: verify_signature returns False when any required param is empty/absent."""
    assert verify_signature(body, timestamp, signature, secret) is False


# ──────────────────────────────────────────────────────────────────────────────
# PA-40: constant-time comparison
# ──────────────────────────────────────────────────────────────────────────────

def test_pa40_verify_signature_uses_compare_digest():
    """PA-40: verify_signature uses hmac.compare_digest for timing-safe comparison."""
    secret = "test_signing_secret"
    body = b'{"type":"event_callback"}'
    ts = str(int(time.time()))
    sig = _make_signature(body, ts, secret)

    with patch("app.services.agent_bridge.slack_normalizer.hmac.compare_digest") as mock_cd:
        mock_cd.return_value = True
        result = verify_signature(body, ts, sig, secret)
        assert mock_cd.called
        assert result is True


# ──────────────────────────────────────────────────────────────────────────────
# PA-41: app_mention event → OrchestratorMessage
# ──────────────────────────────────────────────────────────────────────────────

def test_pa41_parse_slack_app_mention_returns_orchestrator_message():
    """PA-41: _parse_slack converts app_mention event into a valid OrchestratorMessage."""
    payload = _event_callback_payload(
        event_type="app_mention",
        text="<@UBOT> please summarize sprint 183",
    )

    msg = _parse_slack(payload)

    assert msg.channel == "slack"
    assert msg.content == "<@UBOT> please summarize sprint 183"
    assert msg.metadata["event_type"] == "app_mention"


# ──────────────────────────────────────────────────────────────────────────────
# PA-42: message event → OrchestratorMessage
# ──────────────────────────────────────────────────────────────────────────────

def test_pa42_parse_slack_message_event_returns_orchestrator_message():
    """PA-42: _parse_slack converts a plain message event into a valid OrchestratorMessage."""
    payload = _event_callback_payload(
        event_type="message",
        text="run the tests",
    )

    msg = _parse_slack(payload)

    assert msg.channel == "slack"
    assert msg.content == "run the tests"
    assert msg.metadata["event_type"] == "message"


# ──────────────────────────────────────────────────────────────────────────────
# PA-43: url_verification → SlackUrlVerificationError
# ──────────────────────────────────────────────────────────────────────────────

def test_pa43_parse_slack_url_verification_raises_error():
    """PA-43: _parse_slack raises SlackUrlVerificationError with challenge for url_verification."""
    challenge_value = "3eZbrw1aBm2rZgRNFdxV2595E9CY3gmdALWMmHkvFXO7"
    payload = {
        "token": "deprecated_token",
        "challenge": challenge_value,
        "type": "url_verification",
    }

    with pytest.raises(SlackUrlVerificationError) as exc_info:
        _parse_slack(payload)

    assert exc_info.value.challenge == challenge_value


def test_pa43b_url_verification_missing_challenge_raises_value_error():
    """PA-43b: url_verification payload without challenge raises ValueError."""
    payload = {"type": "url_verification"}

    with pytest.raises(ValueError, match="missing challenge"):
        _parse_slack(payload)


# ──────────────────────────────────────────────────────────────────────────────
# PA-44: unsupported payload/event types → ValueError
# ──────────────────────────────────────────────────────────────────────────────

def test_pa44_parse_slack_unsupported_payload_type_raises_value_error():
    """PA-44: _parse_slack raises ValueError for unrecognized top-level payload types."""
    payload = {"type": "unknown_event_type", "event": {}}

    with pytest.raises(ValueError, match="unsupported payload type"):
        _parse_slack(payload)


def test_pa44b_parse_slack_unsupported_inner_event_type_raises_value_error():
    """PA-44b: _parse_slack raises ValueError for unsupported inner event types."""
    payload = {
        "type": "event_callback",
        "event": {"type": "reaction_added", "user": "U123", "text": ""},
        "event_id": "Ev001",
        "event_time": 1700000000,
        "team_id": "T0TEAM01",
    }

    with pytest.raises(ValueError, match="unsupported event type"):
        _parse_slack(payload)


# ──────────────────────────────────────────────────────────────────────────────
# PA-45: sender_id maps to event["user"]
# ──────────────────────────────────────────────────────────────────────────────

def test_pa45_sender_id_maps_to_event_user():
    """PA-45: sender_id in OrchestratorMessage is taken from event['user']."""
    payload = _event_callback_payload(user="UABC12345")
    msg = _parse_slack(payload)
    assert msg.sender_id == "UABC12345"


# ──────────────────────────────────────────────────────────────────────────────
# PA-46: correlation_id = "slack_" + event_id
# ──────────────────────────────────────────────────────────────────────────────

def test_pa46_correlation_id_prefixed_with_slack():
    """PA-46: correlation_id is 'slack_' + event_id from payload."""
    payload = _event_callback_payload(event_id="Ev0SPRINT183")
    msg = _parse_slack(payload)
    assert msg.correlation_id == "slack_Ev0SPRINT183"


# ──────────────────────────────────────────────────────────────────────────────
# PA-47: channel field is "slack"
# ──────────────────────────────────────────────────────────────────────────────

def test_pa47_channel_is_always_slack():
    """PA-47: OrchestratorMessage.channel is always 'slack' for Slack payloads."""
    payload = _event_callback_payload()
    msg = _parse_slack(payload)
    assert msg.channel == "slack"


# ──────────────────────────────────────────────────────────────────────────────
# PA-48: timestamp from event_time (Unix epoch)
# ──────────────────────────────────────────────────────────────────────────────

def test_pa48_timestamp_parsed_from_event_time():
    """PA-48: OrchestratorMessage.timestamp is a UTC datetime from payload['event_time']."""
    from datetime import datetime

    event_time_unix = 1700000000
    payload = _event_callback_payload(event_time=event_time_unix)
    msg = _parse_slack(payload)

    expected_dt = datetime.fromtimestamp(event_time_unix, tz=timezone.utc)
    assert msg.timestamp == expected_dt
    assert msg.timestamp.tzinfo == timezone.utc


def test_pa48b_timestamp_fallback_on_invalid_event_time():
    """PA-48b: Falls back to current UTC time when event_time is absent/invalid."""
    payload = _event_callback_payload()
    payload.pop("event_time")

    msg = _parse_slack(payload)

    # Just verify it's a UTC-aware datetime (exact time not testable)
    assert msg.timestamp.tzinfo == timezone.utc


# ──────────────────────────────────────────────────────────────────────────────
# PA-49: metadata contains team_id, channel_id, event_type
# ──────────────────────────────────────────────────────────────────────────────

def test_pa49_metadata_contains_required_fields():
    """PA-49: metadata dict contains team_id, channel_id, and event_type."""
    payload = _event_callback_payload(
        team_id="T0SDLC183",
        channel="C0EVIDENCE",
        event_type="app_mention",
    )
    msg = _parse_slack(payload)

    assert msg.metadata["team_id"] == "T0SDLC183"
    assert msg.metadata["channel_id"] == "C0EVIDENCE"
    assert msg.metadata["event_type"] == "app_mention"


# ──────────────────────────────────────────────────────────────────────────────
# PA-50: build_block_kit_response format
# ──────────────────────────────────────────────────────────────────────────────

def test_pa50_build_block_kit_response_returns_valid_format():
    """PA-50: build_block_kit_response returns a properly structured Block Kit message."""
    content = "Sprint 183 evidence collection complete. SOC2_CONTROL type added."
    result = build_block_kit_response(content)

    # Must have top-level "blocks" list
    assert "blocks" in result
    assert isinstance(result["blocks"], list)
    assert len(result["blocks"]) >= 1

    # First block must be a "section" with mrkdwn text
    block = result["blocks"][0]
    assert block["type"] == "section"
    assert block["text"]["type"] == "mrkdwn"
    assert block["text"]["text"] == content

    # Must have fallback "text" for notifications
    assert "text" in result
    assert result["text"] == content


def test_pa50b_build_block_kit_response_supports_mrkdwn_formatting():
    """PA-50b: Block Kit response preserves Slack mrkdwn formatting markers."""
    content = "*bold* _italic_ `code` <http://example.com|link>"
    result = build_block_kit_response(content)

    assert result["blocks"][0]["text"]["text"] == content
