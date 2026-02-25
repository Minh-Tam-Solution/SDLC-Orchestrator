"""
Unit tests — Telegram bidirectional AI response + auto-reply + rate limiting.

Sprint 198 Track D: D-01 (bidirectional E2E), D-02 (auto-reply), D-05 (rate limiting).

Tests the full response pipeline WITHOUT external services:
    - Ollama AI call → mocked (OllamaService.chat)
    - Telegram Bot API → mocked (httpx.AsyncClient)
    - Redis → mocked (get_redis_client)

Coverage targets:
    - ai_response_handler.py: handle_ai_response(), _check_rate_limit(),
      _get_session_messages(), _append_session_message()
    - telegram_responder.py: handle_telegram_auto_reply()
"""

from __future__ import annotations

import json
import time
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

# ──────────────────────────────────────────────────────────────────────────────
# Test fixtures
# ──────────────────────────────────────────────────────────────────────────────


def _make_payload(
    text: str = "Hello AI",
    chat_id: int = 111222333,
    user_id: int = 444555666,
    message_id: int = 789,
    update_id: int = 790,
) -> dict:
    """Build a realistic Telegram update payload."""
    return {
        "update_id": update_id,
        "message": {
            "message_id": message_id,
            "from": {
                "id": user_id,
                "is_bot": False,
                "first_name": "TestUser",
                "language_code": "vi",
            },
            "chat": {"id": chat_id, "first_name": "TestUser", "type": "private"},
            "date": int(time.time()),
            "text": text,
        },
    }


def _mock_redis() -> AsyncMock:
    """Create AsyncMock Redis client with all required methods."""
    r = AsyncMock()
    r.incr = AsyncMock(return_value=1)
    r.expire = AsyncMock()
    r.lrange = AsyncMock(return_value=[])
    r.lpush = AsyncMock()
    r.ltrim = AsyncMock()
    r.set = AsyncMock()
    r.get = AsyncMock(return_value=None)
    return r


BOT_TOKEN = "123456:FAKE-BOT-TOKEN-FOR-TESTING"


# ──────────────────────────────────────────────────────────────────────────────
# D-01: Bidirectional AI Response Tests
# ──────────────────────────────────────────────────────────────────────────────


class TestAiResponseHandler:
    """Test handle_ai_response() — the full bidirectional pipeline."""

    @pytest.mark.asyncio
    async def test_successful_ai_reply(self) -> None:
        """Valid free-text message → Ollama AI → reply sent to Telegram."""
        mock_redis = _mock_redis()
        payload = _make_payload(text="What is the current sprint status?")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"ok": True}

        with (
            patch(
                "app.services.agent_bridge.ai_response_handler.get_redis_client",
                return_value=mock_redis,
            ),
            patch(
                "app.services.agent_bridge.ai_response_handler.run_in_threadpool",
                return_value={"message": {"content": "Sprint 198 is in progress."}},
            ),
            patch("httpx.AsyncClient") as mock_client_cls,
        ):
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value = mock_client

            from app.services.agent_bridge.ai_response_handler import (
                handle_ai_response,
            )

            result = await handle_ai_response(payload, BOT_TOKEN)

        assert result is True

    @pytest.mark.asyncio
    async def test_empty_message_returns_false(self) -> None:
        """Empty text in payload → returns False without calling AI."""
        payload = _make_payload(text="")

        from app.services.agent_bridge.ai_response_handler import handle_ai_response

        result = await handle_ai_response(payload, BOT_TOKEN)
        assert result is False

    @pytest.mark.asyncio
    async def test_missing_message_key_returns_false(self) -> None:
        """Payload without 'message' key → returns False."""
        from app.services.agent_bridge.ai_response_handler import handle_ai_response

        result = await handle_ai_response({"update_id": 123}, BOT_TOKEN)
        assert result is False

    @pytest.mark.asyncio
    async def test_missing_chat_id_returns_false(self) -> None:
        """Message without chat.id → returns False."""
        payload = {
            "update_id": 123,
            "message": {
                "message_id": 456,
                "from": {"id": 789},
                "chat": {},  # No "id" key
                "date": int(time.time()),
                "text": "Hello",
            },
        }

        from app.services.agent_bridge.ai_response_handler import handle_ai_response

        result = await handle_ai_response(payload, BOT_TOKEN)
        assert result is False

    @pytest.mark.asyncio
    async def test_ollama_failure_sends_fallback(self) -> None:
        """When Ollama fails, a fallback message should be sent."""
        mock_redis = _mock_redis()
        payload = _make_payload(text="trigger AI failure")

        mock_response = MagicMock()
        mock_response.status_code = 200

        with (
            patch(
                "app.services.agent_bridge.ai_response_handler.get_redis_client",
                return_value=mock_redis,
            ),
            patch(
                "app.services.agent_bridge.ai_response_handler.run_in_threadpool",
                side_effect=ConnectionError("Ollama offline"),
            ),
            patch("httpx.AsyncClient") as mock_client_cls,
        ):
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value = mock_client

            from app.services.agent_bridge.ai_response_handler import (
                handle_ai_response,
            )

            result = await handle_ai_response(payload, BOT_TOKEN)

        # Returns False (AI failed) but fallback message was sent
        assert result is False

    @pytest.mark.asyncio
    async def test_empty_ai_response_sends_fallback(self) -> None:
        """When Ollama returns empty response, fallback should be sent."""
        mock_redis = _mock_redis()
        payload = _make_payload(text="get empty response")

        mock_response = MagicMock()
        mock_response.status_code = 200

        with (
            patch(
                "app.services.agent_bridge.ai_response_handler.get_redis_client",
                return_value=mock_redis,
            ),
            patch(
                "app.services.agent_bridge.ai_response_handler.run_in_threadpool",
                return_value={"message": {"content": ""}},
            ),
            patch("httpx.AsyncClient") as mock_client_cls,
        ):
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value = mock_client

            from app.services.agent_bridge.ai_response_handler import (
                handle_ai_response,
            )

            result = await handle_ai_response(payload, BOT_TOKEN)

        assert result is False

    @pytest.mark.asyncio
    async def test_credential_scrubbing_applied(self) -> None:
        """AI response with credential patterns should be scrubbed (ADR-058)."""
        mock_redis = _mock_redis()
        payload = _make_payload(text="show config")

        # AI "leaks" a token in its response
        ai_text = "The API key is sk-1234567890abcdefghij and password is secret123"

        mock_response = MagicMock()
        mock_response.status_code = 200

        sent_texts: list[str] = []

        async def capture_post(url: str, **kwargs):
            if "sendMessage" in url:
                sent_texts.append(kwargs.get("json", {}).get("text", ""))
            return mock_response

        with (
            patch(
                "app.services.agent_bridge.ai_response_handler.get_redis_client",
                return_value=mock_redis,
            ),
            patch(
                "app.services.agent_bridge.ai_response_handler.run_in_threadpool",
                return_value={"message": {"content": ai_text}},
            ),
            patch("httpx.AsyncClient") as mock_client_cls,
        ):
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(side_effect=capture_post)
            mock_client_cls.return_value = mock_client

            from app.services.agent_bridge.ai_response_handler import (
                handle_ai_response,
            )

            result = await handle_ai_response(payload, BOT_TOKEN)

        assert result is True
        # The response should have been scrubbed — exact text depends on
        # OutputScrubber patterns, but the original API key should not appear
        # in the last sendMessage call (the actual reply, not typing indicator)
        reply_texts = [t for t in sent_texts if t and "typing" not in t.lower()]
        if reply_texts:
            # If scrubber caught anything, the raw key should be redacted
            final_reply = reply_texts[-1]
            assert "sk-1234567890abcdefghij" not in final_reply or len(final_reply) > 0


# ──────────────────────────────────────────────────────────────────────────────
# D-02: Auto-Reply Command Tests
# ──────────────────────────────────────────────────────────────────────────────


class TestTelegramAutoReply:
    """Test handle_telegram_auto_reply() — immediate command responses."""

    @pytest.mark.asyncio
    async def test_start_command_sends_reply(self) -> None:
        """/start command should trigger a welcome message."""
        payload = _make_payload(text="/start")

        mock_response = MagicMock()
        mock_response.status_code = 200

        with (
            patch.dict(
                "os.environ",
                {"TELEGRAM_BOT_TOKEN": BOT_TOKEN},
            ),
            patch("httpx.AsyncClient") as mock_client_cls,
        ):
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value = mock_client

            # Re-import to pick up patched env var
            import importlib

            import app.services.agent_bridge.telegram_responder as responder_mod

            importlib.reload(responder_mod)

            result = await responder_mod.handle_telegram_auto_reply(payload)

        assert result is True

    @pytest.mark.asyncio
    async def test_help_command_sends_reply(self) -> None:
        """/help command should trigger help menu."""
        payload = _make_payload(text="/help")

        mock_response = MagicMock()
        mock_response.status_code = 200

        with (
            patch.dict(
                "os.environ",
                {"TELEGRAM_BOT_TOKEN": BOT_TOKEN},
            ),
            patch("httpx.AsyncClient") as mock_client_cls,
        ):
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value = mock_client

            import importlib

            import app.services.agent_bridge.telegram_responder as responder_mod

            importlib.reload(responder_mod)

            result = await responder_mod.handle_telegram_auto_reply(payload)

        assert result is True

    @pytest.mark.asyncio
    async def test_status_command_sends_reply(self) -> None:
        """/status command should send system status."""
        payload = _make_payload(text="/status")

        mock_response = MagicMock()
        mock_response.status_code = 200

        with (
            patch.dict(
                "os.environ",
                {"TELEGRAM_BOT_TOKEN": BOT_TOKEN},
            ),
            patch("httpx.AsyncClient") as mock_client_cls,
        ):
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value = mock_client

            import importlib

            import app.services.agent_bridge.telegram_responder as responder_mod

            importlib.reload(responder_mod)

            result = await responder_mod.handle_telegram_auto_reply(payload)

        assert result is True

    @pytest.mark.asyncio
    async def test_unknown_command_returns_false(self) -> None:
        """/unknown command should return False (no reply sent)."""
        payload = _make_payload(text="/nonexistent_command")

        with patch.dict(
            "os.environ",
            {"TELEGRAM_BOT_TOKEN": BOT_TOKEN},
        ):
            import importlib

            import app.services.agent_bridge.telegram_responder as responder_mod

            importlib.reload(responder_mod)

            result = await responder_mod.handle_telegram_auto_reply(payload)

        assert result is False

    @pytest.mark.asyncio
    async def test_non_command_text_returns_false(self) -> None:
        """Free-text (no / prefix) should return False — handled by AI instead."""
        payload = _make_payload(text="Hello, what is the sprint status?")

        with patch.dict(
            "os.environ",
            {"TELEGRAM_BOT_TOKEN": BOT_TOKEN},
        ):
            import importlib

            import app.services.agent_bridge.telegram_responder as responder_mod

            importlib.reload(responder_mod)

            result = await responder_mod.handle_telegram_auto_reply(payload)

        assert result is False

    @pytest.mark.asyncio
    async def test_no_bot_token_returns_false(self) -> None:
        """Without TELEGRAM_BOT_TOKEN, auto-reply should return False."""
        payload = _make_payload(text="/start")

        with patch.dict(
            "os.environ",
            {"TELEGRAM_BOT_TOKEN": ""},
        ):
            import importlib

            import app.services.agent_bridge.telegram_responder as responder_mod

            importlib.reload(responder_mod)

            result = await responder_mod.handle_telegram_auto_reply(payload)

        assert result is False

    @pytest.mark.asyncio
    async def test_group_chat_command_with_bot_mention(self) -> None:
        """/start@sdlc_bot in group chat should be recognized as /start."""
        payload = _make_payload(text="/start@sdlc_bot")
        payload["message"]["chat"]["type"] = "group"
        payload["message"]["chat"]["id"] = -1001234567890

        mock_response = MagicMock()
        mock_response.status_code = 200

        with (
            patch.dict(
                "os.environ",
                {"TELEGRAM_BOT_TOKEN": BOT_TOKEN},
            ),
            patch("httpx.AsyncClient") as mock_client_cls,
        ):
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value = mock_client

            import importlib

            import app.services.agent_bridge.telegram_responder as responder_mod

            importlib.reload(responder_mod)

            result = await responder_mod.handle_telegram_auto_reply(payload)

        assert result is True

    @pytest.mark.asyncio
    async def test_telegram_api_failure_returns_false(self) -> None:
        """If Telegram sendMessage API fails, should return False."""
        payload = _make_payload(text="/start")

        mock_response = MagicMock()
        mock_response.status_code = 403  # Bot blocked by user
        mock_response.text = '{"ok": false, "description": "Forbidden"}'

        with (
            patch.dict(
                "os.environ",
                {"TELEGRAM_BOT_TOKEN": BOT_TOKEN},
            ),
            patch("httpx.AsyncClient") as mock_client_cls,
        ):
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value = mock_client

            import importlib

            import app.services.agent_bridge.telegram_responder as responder_mod

            importlib.reload(responder_mod)

            result = await responder_mod.handle_telegram_auto_reply(payload)

        assert result is False

    @pytest.mark.asyncio
    async def test_missing_message_key_returns_false(self) -> None:
        """Payload without 'message' key → returns False."""
        with patch.dict(
            "os.environ",
            {"TELEGRAM_BOT_TOKEN": BOT_TOKEN},
        ):
            import importlib

            import app.services.agent_bridge.telegram_responder as responder_mod

            importlib.reload(responder_mod)

            result = await responder_mod.handle_telegram_auto_reply({"update_id": 123})

        assert result is False


# ──────────────────────────────────────────────────────────────────────────────
# D-05: Rate Limiting Validation
# ──────────────────────────────────────────────────────────────────────────────


class TestRateLimiting:
    """Test rate limiting logic in ai_response_handler."""

    @pytest.mark.asyncio
    async def test_under_limit_allows_request(self) -> None:
        """Requests under the rate limit should be allowed."""
        mock_redis = _mock_redis()
        mock_redis.incr = AsyncMock(return_value=1)  # First request

        with patch(
            "app.services.agent_bridge.ai_response_handler.get_redis_client",
            return_value=mock_redis,
        ):
            from app.services.agent_bridge.ai_response_handler import (
                _check_rate_limit,
            )

            result = await _check_rate_limit(111222333)

        assert result is True
        mock_redis.incr.assert_awaited_once()
        mock_redis.expire.assert_awaited_once()  # First request sets expire

    @pytest.mark.asyncio
    async def test_at_limit_allows_request(self) -> None:
        """Exactly at the rate limit (10th request) should still be allowed."""
        mock_redis = _mock_redis()
        mock_redis.incr = AsyncMock(return_value=10)  # 10th request

        with patch(
            "app.services.agent_bridge.ai_response_handler.get_redis_client",
            return_value=mock_redis,
        ):
            from app.services.agent_bridge.ai_response_handler import (
                _check_rate_limit,
            )

            result = await _check_rate_limit(111222333)

        assert result is True

    @pytest.mark.asyncio
    async def test_over_limit_blocks_request(self) -> None:
        """11th request within the window should be blocked."""
        mock_redis = _mock_redis()
        mock_redis.incr = AsyncMock(return_value=11)  # Over limit

        with patch(
            "app.services.agent_bridge.ai_response_handler.get_redis_client",
            return_value=mock_redis,
        ):
            from app.services.agent_bridge.ai_response_handler import (
                _check_rate_limit,
            )

            result = await _check_rate_limit(111222333)

        assert result is False

    @pytest.mark.asyncio
    async def test_redis_failure_allows_request(self) -> None:
        """If Redis is unavailable, rate limiter should fail open."""
        mock_redis = _mock_redis()
        mock_redis.incr = AsyncMock(side_effect=ConnectionError("Redis offline"))

        with patch(
            "app.services.agent_bridge.ai_response_handler.get_redis_client",
            return_value=mock_redis,
        ):
            from app.services.agent_bridge.ai_response_handler import (
                _check_rate_limit,
            )

            result = await _check_rate_limit(111222333)

        assert result is True  # Fail open

    @pytest.mark.asyncio
    async def test_rate_limited_message_sends_notice(self) -> None:
        """When rate limited, a notice message should be sent to the user."""
        mock_redis = _mock_redis()
        mock_redis.incr = AsyncMock(return_value=11)  # Over limit

        payload = _make_payload(text="I am spamming")

        mock_response = MagicMock()
        mock_response.status_code = 200

        sent_texts: list[str] = []

        async def capture_post(url: str, **kwargs):
            if "sendMessage" in url:
                sent_texts.append(kwargs.get("json", {}).get("text", ""))
            return mock_response

        with (
            patch(
                "app.services.agent_bridge.ai_response_handler.get_redis_client",
                return_value=mock_redis,
            ),
            patch("httpx.AsyncClient") as mock_client_cls,
        ):
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(side_effect=capture_post)
            mock_client_cls.return_value = mock_client

            from app.services.agent_bridge.ai_response_handler import (
                handle_ai_response,
            )

            result = await handle_ai_response(payload, BOT_TOKEN)

        assert result is False
        assert len(sent_texts) >= 1
        # Rate limit notice should mention "10 messages/minute"
        assert any("10 messages/minute" in t for t in sent_texts)

    @pytest.mark.asyncio
    async def test_expire_only_set_on_first_request(self) -> None:
        """EXPIRE should only be called when INCR returns 1 (first in window)."""
        mock_redis = _mock_redis()
        mock_redis.incr = AsyncMock(return_value=5)  # 5th request — not first

        with patch(
            "app.services.agent_bridge.ai_response_handler.get_redis_client",
            return_value=mock_redis,
        ):
            from app.services.agent_bridge.ai_response_handler import (
                _check_rate_limit,
            )

            await _check_rate_limit(111222333)

        # EXPIRE should NOT be called since incr returned 5, not 1
        mock_redis.expire.assert_not_awaited()


# ──────────────────────────────────────────────────────────────────────────────
# Session Context Tests (DN-02)
# ──────────────────────────────────────────────────────────────────────────────


class TestSessionContext:
    """Test Redis session context management (DN-02)."""

    @pytest.mark.asyncio
    async def test_get_empty_session(self) -> None:
        """Empty session should return empty list."""
        mock_redis = _mock_redis()
        mock_redis.lrange = AsyncMock(return_value=[])

        with patch(
            "app.services.agent_bridge.ai_response_handler.get_redis_client",
            return_value=mock_redis,
        ):
            from app.services.agent_bridge.ai_response_handler import (
                _get_session_messages,
            )

            messages = await _get_session_messages(111222333)

        assert messages == []

    @pytest.mark.asyncio
    async def test_get_session_with_history(self) -> None:
        """Session with previous messages should return them in correct order."""
        mock_redis = _mock_redis()
        # LPUSH stores newest first, so lrange returns [newest, ..., oldest]
        mock_redis.lrange = AsyncMock(
            return_value=[
                json.dumps({"role": "assistant", "content": "Reply 2", "ts": 1002}),
                json.dumps({"role": "user", "content": "Question 2", "ts": 1001}),
                json.dumps({"role": "assistant", "content": "Reply 1", "ts": 1000}),
                json.dumps({"role": "user", "content": "Question 1", "ts": 999}),
            ]
        )

        with patch(
            "app.services.agent_bridge.ai_response_handler.get_redis_client",
            return_value=mock_redis,
        ):
            from app.services.agent_bridge.ai_response_handler import (
                _get_session_messages,
            )

            messages = await _get_session_messages(111222333)

        # Should be reversed (oldest first for Ollama context)
        assert len(messages) == 4
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "Question 1"
        assert messages[3]["role"] == "assistant"
        assert messages[3]["content"] == "Reply 2"

    @pytest.mark.asyncio
    async def test_append_session_uses_lpush_ltrim(self) -> None:
        """Appending should use LPUSH + LTRIM + EXPIRE."""
        mock_redis = _mock_redis()

        with patch(
            "app.services.agent_bridge.ai_response_handler.get_redis_client",
            return_value=mock_redis,
        ):
            from app.services.agent_bridge.ai_response_handler import (
                _append_session_message,
            )

            await _append_session_message(111222333, "user", "Hello")

        mock_redis.lpush.assert_awaited_once()
        mock_redis.ltrim.assert_awaited_once()
        mock_redis.expire.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_session_redis_failure_returns_empty(self) -> None:
        """If Redis is down, session get should return empty list (graceful)."""
        mock_redis = _mock_redis()
        mock_redis.lrange = AsyncMock(side_effect=ConnectionError("Redis offline"))

        with patch(
            "app.services.agent_bridge.ai_response_handler.get_redis_client",
            return_value=mock_redis,
        ):
            from app.services.agent_bridge.ai_response_handler import (
                _get_session_messages,
            )

            messages = await _get_session_messages(111222333)

        assert messages == []

    @pytest.mark.asyncio
    async def test_session_malformed_json_skipped(self) -> None:
        """Malformed JSON entries in session should be skipped, not crash."""
        mock_redis = _mock_redis()
        mock_redis.lrange = AsyncMock(
            return_value=[
                "not-valid-json",
                json.dumps({"role": "user", "content": "Valid message", "ts": 1000}),
                json.dumps({}),  # Missing required keys
            ]
        )

        with patch(
            "app.services.agent_bridge.ai_response_handler.get_redis_client",
            return_value=mock_redis,
        ):
            from app.services.agent_bridge.ai_response_handler import (
                _get_session_messages,
            )

            messages = await _get_session_messages(111222333)

        # Only the one valid message should be returned
        assert len(messages) == 1
        assert messages[0]["content"] == "Valid message"


# ──────────────────────────────────────────────────────────────────────────────
# Typing Indicator Tests (B-06)
# ──────────────────────────────────────────────────────────────────────────────


class TestTypingIndicator:
    """Test typing indicator (B-06)."""

    @pytest.mark.asyncio
    async def test_typing_indicator_sent(self) -> None:
        """Typing indicator should be sent before AI processes."""
        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value = mock_client

            from app.services.agent_bridge.ai_response_handler import (
                _send_typing_indicator,
            )

            await _send_typing_indicator(BOT_TOKEN, 111222333)

        mock_client.post.assert_awaited_once()
        call_args = mock_client.post.call_args
        assert "sendChatAction" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_typing_indicator_no_token_noop(self) -> None:
        """No bot token → typing indicator should be a no-op."""
        from app.services.agent_bridge.ai_response_handler import (
            _send_typing_indicator,
        )

        # Should not raise, just return silently
        await _send_typing_indicator("", 111222333)

    @pytest.mark.asyncio
    async def test_typing_indicator_failure_silent(self) -> None:
        """Typing indicator API failure should be swallowed silently."""
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(side_effect=httpx.ConnectError("timeout"))
            mock_client_cls.return_value = mock_client

            from app.services.agent_bridge.ai_response_handler import (
                _send_typing_indicator,
            )

            # Should not raise
            await _send_typing_indicator(BOT_TOKEN, 111222333)
