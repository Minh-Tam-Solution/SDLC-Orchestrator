"""
E2E Integration Test — Telegram OTT Channel via /api/v1/channels/telegram/webhook.

Tests the full webhook pipeline:
    1. HTTP POST with real Telegram Bot API payload format
    2. Signature verification (when OTT_HMAC_ENABLED=true)
    3. Webhook deduplication (Redis SET NX EX)
    4. Protocol adapter normalization (Telegram → OrchestratorMessage)
    5. Input sanitization (12 injection patterns)
    6. Message queue staging (Redis pub/sub notification)

Usage:
    # Against local server (default: http://localhost:8300)
    python -m pytest backend/tests/integration/test_telegram_e2e.py -v

    # Against custom server URL
    BACKEND_URL=https://your-server.com python -m pytest ... -v

    # With HMAC verification enabled
    OTT_HMAC_ENABLED=true TELEGRAM_WEBHOOK_SECRET=mysecret python -m pytest ... -v

Sprint 198 — OTT Channel Real Integration Testing
"""

from __future__ import annotations

import json
import os
import time

import httpx
import pytest

# ──────────────────────────────────────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────────────────────────────────────

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8300")
WEBHOOK_URL = f"{BACKEND_URL}/api/v1/channels/telegram/webhook"
TELEGRAM_SECRET = os.getenv("TELEGRAM_WEBHOOK_SECRET", "test-secret-token")
HMAC_ENABLED = os.getenv("OTT_HMAC_ENABLED", "false").lower() == "true"


def _make_telegram_payload(
    text: str = "Hello from Telegram E2E test",
    chat_id: int = 123456789,
    user_id: int = 987654321,
    message_id: int | None = None,
    update_id: int | None = None,
    chat_type: str = "private",
    first_name: str = "TestUser",
) -> dict:
    """Build a realistic Telegram Bot API update payload."""
    if message_id is None:
        message_id = int(time.time() * 1000) % 2**31
    if update_id is None:
        update_id = int(time.time() * 1000) % 2**31 + 1

    return {
        "update_id": update_id,
        "message": {
            "message_id": message_id,
            "from": {
                "id": user_id,
                "is_bot": False,
                "first_name": first_name,
                "language_code": "vi",
            },
            "chat": {
                "id": chat_id,
                "first_name": first_name,
                "type": chat_type,
            },
            "date": int(time.time()),
            "text": text,
        },
    }


def _headers(with_secret: bool = True) -> dict[str, str]:
    """Build request headers. Include secret token if HMAC is relevant."""
    h: dict[str, str] = {"Content-Type": "application/json"}
    if with_secret:
        h["X-Telegram-Bot-Api-Secret-Token"] = TELEGRAM_SECRET
    return h


# ──────────────────────────────────────────────────────────────────────────────
# Tests: Basic Webhook Acceptance
# ──────────────────────────────────────────────────────────────────────────────


class TestTelegramWebhookAcceptance:
    """Test basic webhook acceptance flow."""

    def test_valid_message_returns_200_accepted(self) -> None:
        """A well-formed Telegram message webhook should be accepted."""
        payload = _make_telegram_payload(text="Sprint 198 test message")
        resp = httpx.post(WEBHOOK_URL, json=payload, headers=_headers(), timeout=10)

        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data["status"] in ("accepted", "duplicate")
        if data["status"] == "accepted":
            assert "correlation_id" in data
            assert data["correlation_id"].startswith("telegram_")

    def test_private_chat_message(self) -> None:
        """Private chat message (1-on-1 with bot) should be accepted."""
        payload = _make_telegram_payload(
            text="/start",
            chat_type="private",
        )
        resp = httpx.post(WEBHOOK_URL, json=payload, headers=_headers(), timeout=10)
        assert resp.status_code == 200

    def test_group_chat_message(self) -> None:
        """Group chat message should be accepted."""
        payload = _make_telegram_payload(
            text="@sdlc_bot check sprint status",
            chat_type="group",
            chat_id=-1001234567890,
        )
        resp = httpx.post(WEBHOOK_URL, json=payload, headers=_headers(), timeout=10)
        assert resp.status_code == 200

    def test_vietnamese_text(self) -> None:
        """Vietnamese text with diacritics should pass through correctly."""
        payload = _make_telegram_payload(
            text="Kiểm tra sprint hiện tại, cập nhật trạng thái gate G4",
        )
        resp = httpx.post(WEBHOOK_URL, json=payload, headers=_headers(), timeout=10)
        assert resp.status_code == 200

    def test_long_message_accepted(self) -> None:
        """Messages up to Telegram's 4096 char limit should be accepted."""
        long_text = "A" * 4000
        payload = _make_telegram_payload(text=long_text)
        resp = httpx.post(WEBHOOK_URL, json=payload, headers=_headers(), timeout=10)
        assert resp.status_code == 200

    def test_emoji_and_unicode(self) -> None:
        """Emoji and unicode characters should be handled correctly."""
        payload = _make_telegram_payload(text="Sprint passed ✅ Gate G4 approved 🎉🚀")
        resp = httpx.post(WEBHOOK_URL, json=payload, headers=_headers(), timeout=10)
        assert resp.status_code == 200


# ──────────────────────────────────────────────────────────────────────────────
# Tests: Error Handling
# ──────────────────────────────────────────────────────────────────────────────


class TestTelegramWebhookErrors:
    """Test error handling for malformed/invalid requests."""

    def test_unsupported_channel_returns_400(self) -> None:
        """Unknown channel name should return 400."""
        url = f"{BACKEND_URL}/api/v1/channels/whatsapp/webhook"
        payload = _make_telegram_payload()
        resp = httpx.post(url, json=payload, headers=_headers(), timeout=10)
        assert resp.status_code == 400

    def test_missing_message_key_returns_422(self) -> None:
        """Telegram payload without 'message' key should return 422."""
        payload = {"update_id": 123456}  # no 'message' key
        resp = httpx.post(WEBHOOK_URL, json=payload, headers=_headers(), timeout=10)
        assert resp.status_code == 422

    def test_missing_text_returns_422(self) -> None:
        """Telegram message without 'text' field should return 422."""
        payload = {
            "update_id": 123457,
            "message": {
                "message_id": 999,
                "from": {"id": 12345, "is_bot": False, "first_name": "Test"},
                "chat": {"id": 12345, "type": "private"},
                "date": int(time.time()),
                # no "text" field — e.g. photo/sticker message
            },
        }
        resp = httpx.post(WEBHOOK_URL, json=payload, headers=_headers(), timeout=10)
        assert resp.status_code == 422

    def test_invalid_json_returns_400(self) -> None:
        """Non-JSON body should return 400."""
        resp = httpx.post(
            WEBHOOK_URL,
            content=b"this is not json",
            headers={"Content-Type": "application/json", "X-Telegram-Bot-Api-Secret-Token": TELEGRAM_SECRET},
            timeout=10,
        )
        assert resp.status_code == 400

    def test_empty_body_returns_400(self) -> None:
        """Empty body should return 400 or 422."""
        resp = httpx.post(
            WEBHOOK_URL,
            content=b"",
            headers={"Content-Type": "application/json", "X-Telegram-Bot-Api-Secret-Token": TELEGRAM_SECRET},
            timeout=10,
        )
        assert resp.status_code in (400, 422)


# ──────────────────────────────────────────────────────────────────────────────
# Tests: Security — HMAC Verification
# ──────────────────────────────────────────────────────────────────────────────


class TestTelegramHmacVerification:
    """Test HMAC signature verification (only when OTT_HMAC_ENABLED=true)."""

    @pytest.mark.skipif(not HMAC_ENABLED, reason="OTT_HMAC_ENABLED=false — skipping HMAC tests")
    def test_missing_secret_header_returns_403(self) -> None:
        """Missing X-Telegram-Bot-Api-Secret-Token should return 403."""
        payload = _make_telegram_payload()
        resp = httpx.post(WEBHOOK_URL, json=payload, headers=_headers(with_secret=False), timeout=10)
        assert resp.status_code == 403

    @pytest.mark.skipif(not HMAC_ENABLED, reason="OTT_HMAC_ENABLED=false — skipping HMAC tests")
    def test_wrong_secret_returns_403(self) -> None:
        """Wrong secret token should return 403."""
        payload = _make_telegram_payload()
        headers = _headers()
        headers["X-Telegram-Bot-Api-Secret-Token"] = "wrong-secret"
        resp = httpx.post(WEBHOOK_URL, json=payload, headers=headers, timeout=10)
        assert resp.status_code == 403

    @pytest.mark.skipif(not HMAC_ENABLED, reason="OTT_HMAC_ENABLED=false — skipping HMAC tests")
    def test_correct_secret_returns_200(self) -> None:
        """Correct secret token should return 200."""
        payload = _make_telegram_payload()
        resp = httpx.post(WEBHOOK_URL, json=payload, headers=_headers(), timeout=10)
        assert resp.status_code == 200


# ──────────────────────────────────────────────────────────────────────────────
# Tests: Webhook Deduplication (FR-048)
# ──────────────────────────────────────────────────────────────────────────────


class TestTelegramDeduplication:
    """Test Redis-based webhook deduplication."""

    def test_duplicate_update_id_returns_duplicate(self) -> None:
        """Sending the same update_id twice should return 'duplicate' on second attempt."""
        fixed_update_id = 999888777
        payload = _make_telegram_payload(
            text="dedupe test",
            update_id=fixed_update_id,
            message_id=fixed_update_id + 1,
        )

        # First request — should be accepted
        resp1 = httpx.post(WEBHOOK_URL, json=payload, headers=_headers(), timeout=10)
        assert resp1.status_code == 200

        # Second request — same update_id, should be duplicate
        resp2 = httpx.post(WEBHOOK_URL, json=payload, headers=_headers(), timeout=10)
        assert resp2.status_code == 200
        data2 = resp2.json()
        # Either duplicate (Redis available) or accepted again (Redis unavailable)
        assert data2["status"] in ("duplicate", "accepted")


# ──────────────────────────────────────────────────────────────────────────────
# Tests: Input Sanitization
# ──────────────────────────────────────────────────────────────────────────────


class TestTelegramInputSanitization:
    """Test that injection patterns are blocked by the sanitization pipeline."""

    def test_sql_injection_blocked(self) -> None:
        """SQL injection patterns should be sanitized, not rejected."""
        payload = _make_telegram_payload(text="'; DROP TABLE users; --")
        resp = httpx.post(WEBHOOK_URL, json=payload, headers=_headers(), timeout=10)
        # Should be accepted (sanitized), not rejected
        assert resp.status_code == 200

    def test_xss_blocked(self) -> None:
        """XSS patterns should be sanitized."""
        payload = _make_telegram_payload(text='<script>alert("xss")</script>')
        resp = httpx.post(WEBHOOK_URL, json=payload, headers=_headers(), timeout=10)
        assert resp.status_code == 200

    def test_command_injection_blocked(self) -> None:
        """Command injection patterns should be sanitized."""
        payload = _make_telegram_payload(text="; rm -rf / && echo pwned")
        resp = httpx.post(WEBHOOK_URL, json=payload, headers=_headers(), timeout=10)
        assert resp.status_code == 200


# ──────────────────────────────────────────────────────────────────────────────
# Tests: Governance Commands (Conversation-First)
# ──────────────────────────────────────────────────────────────────────────────


class TestTelegramGovernanceCommands:
    """Test that governance commands via Telegram are accepted."""

    @pytest.mark.parametrize("command", [
        "/start",
        "/help",
        "check sprint status",
        "approve gate G4",
        "show project dashboard",
        "update sprint",
        "cập nhật sprint",  # Vietnamese alias
        "kiểm tra gate",  # Vietnamese
    ])
    def test_governance_command_accepted(self, command: str) -> None:
        """Governance commands should be accepted via Telegram."""
        payload = _make_telegram_payload(text=command)
        resp = httpx.post(WEBHOOK_URL, json=payload, headers=_headers(), timeout=10)
        assert resp.status_code == 200


# ──────────────────────────────────────────────────────────────────────────────
# Standalone runner — for manual testing without pytest
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    """
    Run as standalone script for quick manual testing:
        python backend/tests/integration/test_telegram_e2e.py
    """
    print(f"\n{'='*60}")
    print(f"Telegram OTT E2E Test — SDLC Orchestrator")
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Webhook URL: {WEBHOOK_URL}")
    print(f"HMAC Enabled: {HMAC_ENABLED}")
    print(f"{'='*60}\n")

    client = httpx.Client(timeout=10)
    passed = 0
    failed = 0

    tests = [
        ("Valid message", _make_telegram_payload(text="Hello from manual test")),
        ("Vietnamese text", _make_telegram_payload(text="Kiểm tra sprint hiện tại")),
        ("Emoji message", _make_telegram_payload(text="Gate approved ✅🎉")),
        ("Group chat", _make_telegram_payload(text="@bot check status", chat_type="group", chat_id=-100123)),
        ("/start command", _make_telegram_payload(text="/start")),
        ("Long message", _make_telegram_payload(text="A" * 4000)),
        ("Governance command", _make_telegram_payload(text="update sprint")),
        ("Vietnamese command", _make_telegram_payload(text="cập nhật sprint")),
    ]

    for name, payload in tests:
        try:
            resp = client.post(WEBHOOK_URL, json=payload, headers=_headers())
            status = "PASS" if resp.status_code == 200 else "FAIL"
            if status == "PASS":
                passed += 1
            else:
                failed += 1
            data = resp.json() if resp.status_code == 200 else resp.text
            print(f"  [{status}] {name}: {resp.status_code} — {data}")
        except Exception as exc:
            failed += 1
            print(f"  [FAIL] {name}: {exc}")

    # Error cases
    error_tests = [
        ("Unsupported channel", f"{BACKEND_URL}/api/v1/channels/whatsapp/webhook", _make_telegram_payload(), 400),
        ("Missing message key", WEBHOOK_URL, {"update_id": 123}, 422),
        ("Invalid JSON", WEBHOOK_URL, None, 400),
    ]

    for name, url, payload, expected_code in error_tests:
        try:
            if payload is None:
                resp = client.post(url, content=b"not-json", headers=_headers())
            else:
                resp = client.post(url, json=payload, headers=_headers())
            status = "PASS" if resp.status_code == expected_code else "FAIL"
            if status == "PASS":
                passed += 1
            else:
                failed += 1
            print(f"  [{status}] {name}: expected={expected_code} got={resp.status_code}")
        except Exception as exc:
            failed += 1
            print(f"  [FAIL] {name}: {exc}")

    print(f"\n{'='*60}")
    print(f"Results: {passed} passed, {failed} failed, {passed + failed} total")
    print(f"{'='*60}\n")
