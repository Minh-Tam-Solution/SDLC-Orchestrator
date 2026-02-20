"""
Unit tests for agent_bridge/teams_normalizer.py — Sprint 182.

Test IDs: PA-21 to PA-35 (see SPRINT-182 §Test Suite).

Coverage:
  PA-21  parse_activity extracts text content from Teams message activity
  PA-22  parse_activity maps from.aadObjectId → OrchestratorMessage.sender_id
  PA-23  parse_activity maps activity.id → OrchestratorMessage.correlation_id
  PA-24  parse_activity sets channel="teams"
  PA-25  parse_activity handles empty text (voice/card activities)
  PA-26  parse_activity extracts tenant_id from channelData.tenant.id
  PA-27  parse_activity handles conversationUpdate (member added/removed)
  PA-28  parse_activity rejects unknown activity type (raises ValueError)
  PA-29  verify_hmac returns True for valid Bot Framework signature
  PA-30  verify_hmac returns False for tampered body
  PA-31  verify_hmac returns False for wrong secret
  PA-32  verify_hmac uses constant-time comparison (hmac.compare_digest)
  PA-33  Adaptive Card response format: contentType application/vnd.microsoft.card.adaptive
  PA-34  ott_gateway.py routes "teams" channel to TeamsNormalizer
  PA-35  TeamsNormalizer rejects non-Teams channelId (e.g., "slack")
"""

from __future__ import annotations

import hashlib
import hmac
import importlib
from datetime import datetime
from unittest.mock import patch

import pytest

# Import normalizer (triggers register_normalizer side-effect for "teams")
from app.services.agent_bridge import teams_normalizer
from app.services.agent_bridge.teams_normalizer import (
    _TEAMS_CHANNEL_ID,
    _parse_teams,
    build_adaptive_card_response,
    verify_hmac,
)
from app.services.agent_bridge.protocol_adapter import (
    OrchestratorMessage,
    _CHANNEL_REGISTRY,
    normalize,
)


# ──────────────────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────────────────

TEAMS_MESSAGE_PAYLOAD: dict = {
    "type": "message",
    "id": "f:1826549975918235838",
    "channelId": "msteams",
    "timestamp": "2026-02-19T10:30:00.000Z",
    "from": {
        "id": "29:1abc",
        "aadObjectId": "aad-user-guid-001",
    },
    "conversation": {"id": "19:channel@thread.v2"},
    "channelData": {
        "tenant": {"id": "tenant-guid-abc"},
    },
    "text": "@reviewer approve sprint 182",
}

TEAMS_CONVERSATION_UPDATE_PAYLOAD: dict = {
    "type": "conversationUpdate",
    "id": "f:conv_update_001",
    "channelId": "msteams",
    "timestamp": "2026-02-19T10:31:00.000Z",
    "from": {
        "id": "29:1abc",
        "aadObjectId": "aad-user-guid-001",
    },
    "conversation": {"id": "19:channel@thread.v2"},
    "channelData": {
        "tenant": {"id": "tenant-guid-abc"},
        "eventType": "teamMemberAdded",
    },
    "membersAdded": [{"id": "29:1new-member", "aadObjectId": "aad-new-user-001"}],
}

TEAMS_INVOKE_PAYLOAD: dict = {
    "type": "invoke",
    "id": "f:invoke_001",
    "channelId": "msteams",
    "timestamp": "2026-02-19T10:32:00.000Z",
    "from": {
        "id": "29:1abc",
        "aadObjectId": "aad-user-guid-001",
    },
    "conversation": {"id": "19:channel@thread.v2"},
    "channelData": {
        "tenant": {"id": "tenant-guid-abc"},
    },
    "name": "adaptiveCard/action",
    # no "text" field — voice/card activities
}


# ──────────────────────────────────────────────────────────────────────────────
# PA-21 to PA-28: Activity parsing
# ──────────────────────────────────────────────────────────────────────────────

class TestTeamsActivityParsing:
    """Tests PA-21 to PA-28: Teams Bot Framework Activity → OrchestratorMessage."""

    def test_pa21_extract_text_content(self) -> None:
        """PA-21: parse_activity extracts text from Teams message activity."""
        msg = _parse_teams(TEAMS_MESSAGE_PAYLOAD)
        assert msg.content == "@reviewer approve sprint 182"

    def test_pa22_map_aad_object_id_to_sender_id(self) -> None:
        """PA-22: parse_activity maps from.aadObjectId → OrchestratorMessage.sender_id."""
        msg = _parse_teams(TEAMS_MESSAGE_PAYLOAD)
        assert msg.sender_id == "aad-user-guid-001"

    def test_pa23_map_activity_id_to_correlation_id(self) -> None:
        """PA-23: parse_activity maps activity.id → OrchestratorMessage.correlation_id."""
        msg = _parse_teams(TEAMS_MESSAGE_PAYLOAD)
        assert msg.correlation_id == "f:1826549975918235838"

    def test_pa24_channel_is_teams(self) -> None:
        """PA-24: parse_activity sets channel='teams'."""
        msg = _parse_teams(TEAMS_MESSAGE_PAYLOAD)
        assert msg.channel == "teams"

    def test_pa25_handles_empty_text_for_card_activities(self) -> None:
        """PA-25: parse_activity handles empty text for invoke/voice activities (no ValueError)."""
        # invoke payload has no "text" field
        msg = _parse_teams(TEAMS_INVOKE_PAYLOAD)
        # content should be "" (empty) not raising ValueError at this stage;
        # protocol_adapter.normalize() would raise ValueError — tested separately
        assert msg.content == ""
        assert msg.channel == "teams"

    def test_pa26_extracts_tenant_id_from_channel_data(self) -> None:
        """PA-26: parse_activity extracts tenant_id from channelData.tenant.id."""
        msg = _parse_teams(TEAMS_MESSAGE_PAYLOAD)
        assert msg.metadata["tenant_id"] == "tenant-guid-abc"

    def test_pa27_handles_conversation_update(self) -> None:
        """PA-27: parse_activity handles conversationUpdate (member added/removed)."""
        msg = _parse_teams(TEAMS_CONVERSATION_UPDATE_PAYLOAD)
        assert msg.channel == "teams"
        assert msg.metadata["activity_type"] == "conversationUpdate"
        assert msg.content == ""  # conversationUpdate has no text

    def test_pa28_rejects_unknown_activity_type(self) -> None:
        """PA-28: parse_activity rejects unknown activity type with ValueError."""
        payload = {**TEAMS_MESSAGE_PAYLOAD, "type": "unknownActivityType"}
        with pytest.raises(ValueError, match="unsupported activity type"):
            _parse_teams(payload)


# ──────────────────────────────────────────────────────────────────────────────
# PA-29 to PA-32: HMAC verification
# ──────────────────────────────────────────────────────────────────────────────

class TestVerifyHmac:
    """Tests PA-29 to PA-32: HMAC signature verification for Bot Framework."""

    _SECRET = "my-bot-framework-secret"
    _BODY = b'{"type":"message","text":"hello"}'

    @classmethod
    def _make_sig(cls, body: bytes, secret: str) -> str:
        """Helper: compute valid HMAC-SHA256 hex signature."""
        return hmac.new(
            key=secret.encode("utf-8"),
            msg=body,
            digestmod=hashlib.sha256,
        ).hexdigest()

    def test_pa29_valid_signature_returns_true(self) -> None:
        """PA-29: verify_hmac returns True for valid Bot Framework signature."""
        sig = self._make_sig(self._BODY, self._SECRET)
        assert verify_hmac(self._BODY, sig, self._SECRET) is True

    def test_pa30_tampered_body_returns_false(self) -> None:
        """PA-30: verify_hmac returns False for tampered body."""
        sig = self._make_sig(self._BODY, self._SECRET)
        tampered = b'{"type":"message","text":"tampered"}'
        assert verify_hmac(tampered, sig, self._SECRET) is False

    def test_pa31_wrong_secret_returns_false(self) -> None:
        """PA-31: verify_hmac returns False for wrong secret."""
        sig = self._make_sig(self._BODY, self._SECRET)
        assert verify_hmac(self._BODY, sig, "wrong-secret") is False

    def test_pa32_constant_time_comparison(self) -> None:
        """PA-32: verify_hmac uses hmac.compare_digest for constant-time comparison.

        Verifies the implementation is not vulnerable to timing oracle attacks.
        The test patches hmac.compare_digest to confirm it is called, which
        provides assurance that the timing-safe comparison path is exercised.
        """
        sig = self._make_sig(self._BODY, self._SECRET)
        with patch("app.services.agent_bridge.teams_normalizer.hmac.compare_digest") as mock_cd:
            mock_cd.return_value = True
            result = verify_hmac(self._BODY, sig, self._SECRET)
            assert mock_cd.called, "hmac.compare_digest must be used for timing-safe comparison"
            assert result is True


# ──────────────────────────────────────────────────────────────────────────────
# PA-33: Adaptive Card response format
# ──────────────────────────────────────────────────────────────────────────────

class TestAdaptiveCardResponse:
    """Test PA-33: Adaptive Card response structure."""

    def test_pa33_adaptive_card_content_type(self) -> None:
        """PA-33: build_adaptive_card_response has correct contentType for Teams."""
        response = build_adaptive_card_response("Agent output: sprint 182 approved")

        # Top-level structure
        assert response["type"] == "message"
        assert "attachments" in response
        assert len(response["attachments"]) == 1

        attachment = response["attachments"][0]
        assert attachment["contentType"] == "application/vnd.microsoft.card.adaptive"

        # Card body structure
        card = attachment["content"]
        assert card["type"] == "AdaptiveCard"
        assert card["version"] == "1.5"
        assert len(card["body"]) == 1
        text_block = card["body"][0]
        assert text_block["type"] == "TextBlock"
        assert text_block["text"] == "Agent output: sprint 182 approved"
        assert text_block["wrap"] is True


# ──────────────────────────────────────────────────────────────────────────────
# PA-34: OTT gateway routing
# ──────────────────────────────────────────────────────────────────────────────

class TestOttGatewayRouting:
    """Test PA-34: ott_gateway.py routes 'teams' channel to TeamsNormalizer."""

    def test_pa34_teams_channel_in_registry(self) -> None:
        """PA-34: 'teams' channel is registered in _CHANNEL_REGISTRY after import."""
        # Import of teams_normalizer (done at top of this file) triggers
        # register_normalizer("teams", _parse_teams). Verify registration.
        assert "teams" in _CHANNEL_REGISTRY, (
            "'teams' must be registered in _CHANNEL_REGISTRY via register_normalizer(); "
            "teams_normalizer.py module-level side-effect not executed"
        )

    def test_pa34_normalize_routes_teams_payload(self) -> None:
        """PA-34: normalize('teams', payload) dispatches to teams_normalizer._parse_teams."""
        # A message payload with text should normalize successfully
        msg = normalize(TEAMS_MESSAGE_PAYLOAD, "teams")
        assert isinstance(msg, OrchestratorMessage)
        assert msg.channel == "teams"
        assert msg.content == "@reviewer approve sprint 182"


# ──────────────────────────────────────────────────────────────────────────────
# PA-35: Non-Teams channelId rejection
# ──────────────────────────────────────────────────────────────────────────────

class TestTeamsChannelIdEnforcement:
    """Test PA-35: TeamsNormalizer rejects non-Teams channelId."""

    def test_pa35_rejects_slack_channel_id(self) -> None:
        """PA-35: _parse_teams raises ValueError when channelId is 'slack'."""
        payload = {**TEAMS_MESSAGE_PAYLOAD, "channelId": "slack"}
        with pytest.raises(ValueError, match="non-Teams channelId"):
            _parse_teams(payload)

    def test_pa35_rejects_directline_channel_id(self) -> None:
        """PA-35 (extended): _parse_teams raises ValueError for 'directline' channelId."""
        payload = {**TEAMS_MESSAGE_PAYLOAD, "channelId": "directline"}
        with pytest.raises(ValueError, match="non-Teams channelId"):
            _parse_teams(payload)

    def test_pa35_accepts_msteams_channel_id(self) -> None:
        """PA-35 (control): _parse_teams succeeds for correct 'msteams' channelId."""
        msg = _parse_teams(TEAMS_MESSAGE_PAYLOAD)
        assert msg.channel == "teams"
