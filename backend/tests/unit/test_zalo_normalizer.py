"""
Unit tests for Zalo OA webhook normalizer — Sprint 192 (Signature Verification).

Test coverage:
  PA-60  _parse_zalo converts user_send_text into OrchestratorMessage
  PA-61  _parse_zalo rejects unsupported event types
  PA-62  _parse_zalo rejects missing message text
  PA-63  verify_signature returns True for valid Zalo OA signature
  PA-64  verify_signature returns False for tampered body
  PA-65  verify_signature returns False for wrong secret
  PA-66  verify_signature returns False for empty signature
  PA-67  verify_signature uses hmac.compare_digest (constant-time)
  PA-68  ott_gateway routes "zalo" channel to ZaloNormalizer
"""

from __future__ import annotations

import hashlib
from unittest.mock import patch

import pytest

from app.services.agent_bridge.zalo_normalizer import (
    _parse_zalo,
    verify_signature,
)
from app.services.agent_bridge.protocol_adapter import (
    _CHANNEL_REGISTRY,
)


# ──────────────────────────────────────────────────────────────────────────────
# Test fixtures
# ──────────────────────────────────────────────────────────────────────────────

_VALID_PAYLOAD: dict = {
    "eventName": "user_send_text",
    "appId": "12345678",
    "message": {"text": "gate status #42"},
    "sender": {"id": "zalo_user_001"},
    "recipient": {"id": "zalo_oa_001"},
    "timestamp": 1708000000000,
}


# ──────────────────────────────────────────────────────────────────────────────
# PA-60 to PA-62: Normalizer tests
# ──────────────────────────────────────────────────────────────────────────────


class TestParseZalo:
    """Tests for _parse_zalo normalizer function."""

    def test_pa60_valid_user_send_text(self) -> None:
        """PA-60: _parse_zalo converts user_send_text into OrchestratorMessage."""
        msg = _parse_zalo(_VALID_PAYLOAD)
        assert msg.channel == "zalo"
        assert msg.sender_id == "zalo_user_001"
        assert msg.content == "gate status #42"
        assert msg.correlation_id.startswith("zalo_")
        assert msg.metadata["event_name"] == "user_send_text"
        assert msg.metadata["recipient_id"] == "zalo_oa_001"

    def test_pa61_unsupported_event_type(self) -> None:
        """PA-61: _parse_zalo rejects unsupported event types."""
        payload = {**_VALID_PAYLOAD, "eventName": "user_send_image"}
        with pytest.raises(ValueError, match="unsupported zalo event"):
            _parse_zalo(payload)

    def test_pa62_missing_message_text(self) -> None:
        """PA-62: _parse_zalo rejects missing message text."""
        payload = {**_VALID_PAYLOAD, "message": {}}
        with pytest.raises(ValueError, match="missing message text"):
            _parse_zalo(payload)

    def test_pa62_missing_sender_uses_sentinel(self) -> None:
        """Sender without id uses 'zalo_unknown' sentinel."""
        payload = {**_VALID_PAYLOAD, "sender": {}}
        msg = _parse_zalo(payload)
        assert msg.sender_id == "zalo_unknown"


# ──────────────────────────────────────────────────────────────────────────────
# PA-63 to PA-67: Signature verification tests
# ──────────────────────────────────────────────────────────────────────────────


class TestVerifySignature:
    """Tests for Zalo OA SHA256 signature verification (Sprint 192)."""

    _BODY: bytes = b'{"eventName":"user_send_text","message":{"text":"hello"}}'
    _APP_ID: str = "12345678"
    _TIMESTAMP: str = "1708000000000"
    _SECRET: str = "zalo_oa_secret_key_test"

    @staticmethod
    def _make_sig(body: bytes, app_id: str, timestamp: str, secret: str) -> str:
        """Compute expected Zalo signature: sha256(appId + body + timestamp + secret)."""
        base_string = f"{app_id}{body.decode('utf-8')}{timestamp}{secret}"
        return hashlib.sha256(base_string.encode("utf-8")).hexdigest()

    def test_pa63_valid_signature_returns_true(self) -> None:
        """PA-63: verify_signature returns True for valid Zalo OA signature."""
        sig = self._make_sig(self._BODY, self._APP_ID, self._TIMESTAMP, self._SECRET)
        assert verify_signature(self._BODY, sig, self._APP_ID, self._TIMESTAMP, self._SECRET) is True

    def test_pa64_tampered_body_returns_false(self) -> None:
        """PA-64: verify_signature returns False for tampered body."""
        sig = self._make_sig(self._BODY, self._APP_ID, self._TIMESTAMP, self._SECRET)
        tampered = b'{"eventName":"user_send_text","message":{"text":"injected"}}'
        assert verify_signature(tampered, sig, self._APP_ID, self._TIMESTAMP, self._SECRET) is False

    def test_pa65_wrong_secret_returns_false(self) -> None:
        """PA-65: verify_signature returns False for wrong secret."""
        sig = self._make_sig(self._BODY, self._APP_ID, self._TIMESTAMP, self._SECRET)
        assert verify_signature(self._BODY, sig, self._APP_ID, self._TIMESTAMP, "wrong-secret") is False

    def test_pa66_empty_signature_returns_false(self) -> None:
        """PA-66: verify_signature returns False for empty signature."""
        assert verify_signature(self._BODY, "", self._APP_ID, self._TIMESTAMP, self._SECRET) is False

    def test_pa66_empty_secret_returns_false(self) -> None:
        """PA-66: verify_signature returns False for empty secret."""
        sig = self._make_sig(self._BODY, self._APP_ID, self._TIMESTAMP, self._SECRET)
        assert verify_signature(self._BODY, sig, self._APP_ID, self._TIMESTAMP, "") is False

    def test_pa66_empty_app_id_returns_false(self) -> None:
        """PA-66: verify_signature returns False for empty app_id."""
        sig = self._make_sig(self._BODY, self._APP_ID, self._TIMESTAMP, self._SECRET)
        assert verify_signature(self._BODY, sig, "", self._TIMESTAMP, self._SECRET) is False

    def test_pa67_constant_time_comparison(self) -> None:
        """PA-67: verify_signature uses hmac.compare_digest for constant-time comparison."""
        sig = self._make_sig(self._BODY, self._APP_ID, self._TIMESTAMP, self._SECRET)
        with patch("app.services.agent_bridge.zalo_normalizer.hmac.compare_digest") as mock_cd:
            mock_cd.return_value = True
            result = verify_signature(self._BODY, sig, self._APP_ID, self._TIMESTAMP, self._SECRET)
            assert mock_cd.called, "hmac.compare_digest must be used for timing-safe comparison"
            assert result is True

    def test_pa69_empty_timestamp_still_secure(self) -> None:
        """PA-69: verify_signature handles missing timestamp (empty string fallback).

        When Zalo sends a payload without a timestamp field, ott_gateway passes
        timestamp="" to verify_signature. The hash becomes sha256(appId + body + "" + secret).
        This is still secret-dependent and must reject mismatched signatures.
        """
        empty_ts = ""
        sig_with_empty_ts = self._make_sig(self._BODY, self._APP_ID, empty_ts, self._SECRET)
        # Valid: matching empty timestamp
        assert verify_signature(self._BODY, sig_with_empty_ts, self._APP_ID, empty_ts, self._SECRET) is True
        # Invalid: signature computed with real timestamp, verified with empty
        sig_with_real_ts = self._make_sig(self._BODY, self._APP_ID, self._TIMESTAMP, self._SECRET)
        assert verify_signature(self._BODY, sig_with_real_ts, self._APP_ID, empty_ts, self._SECRET) is False


# ──────────────────────────────────────────────────────────────────────────────
# PA-68: Channel registration
# ──────────────────────────────────────────────────────────────────────────────


class TestChannelRegistration:
    """Verify Zalo normalizer is registered in the channel dispatcher."""

    def test_pa68_zalo_registered(self) -> None:
        """PA-68: ott_gateway routes 'zalo' channel to ZaloNormalizer."""
        assert "zalo" in _CHANNEL_REGISTRY, "zalo must be registered in channel registry"
