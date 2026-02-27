"""
Unit tests for OTT Link Handler — ADR-068 OTT Identity Linking.

Sprint 209 — /link, /verify, /unlink command handlers.
Test IDs: E1-E6, E11-E12 (FR-050 acceptance criteria).

Coverage:
  E1   /link with valid email -> code generated, stored in Redis, email sent
  E2   /link with unknown email -> error reply, no Redis key created
  E3   /verify with correct code -> oauth_accounts upserted (GETDEL atomic single-use)
  E4   /verify with wrong code -> error reply, Redis key NOT deleted
  E5   /verify with expired code -> error reply
  E6   Double /verify -> second attempt fails (GETDEL single-use guarantee)
  E11  /unlink -> oauth_accounts deleted, cache cleared
  E12  /link rate limiting -> 6th attempt within 15 min blocked
  +    /whoami -> linked/unlinked/deleted-user/error scenarios

Zero Mock Policy: Real handler logic, mocked Redis + DB + email for isolation.
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.services.agent_bridge.ott_link_handler import (
    handle_link_command,
    handle_verify_command,
    handle_unlink_command,
    handle_whoami_command,
)


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────


@pytest.fixture()
def mock_redis() -> AsyncMock:
    """Comprehensive async Redis mock covering all methods used by handlers."""
    redis = AsyncMock()
    redis.incr.return_value = 1
    redis.expire.return_value = True
    redis.setex.return_value = True
    redis.get.return_value = None
    redis.getdel.return_value = None
    redis.delete.return_value = 1
    return redis


@pytest.fixture()
def mock_db() -> AsyncMock:
    """Async DB session mock with execute/commit/rollback/add."""
    db = AsyncMock()
    db.commit.return_value = None
    db.rollback.return_value = None
    db.add = MagicMock()
    return db


@pytest.fixture()
def mock_user() -> MagicMock:
    """A realistic User model mock for DB lookups."""
    user = MagicMock()
    user.id = uuid4()
    user.email = "dangtt1971@gmail.com"
    user.full_name = "Dang Tam"
    user.is_active = True
    return user


@pytest.fixture()
def mock_oauth_account() -> MagicMock:
    """A realistic OAuthAccount model mock."""
    account = MagicMock()
    account.id = uuid4()
    account.user_id = uuid4()
    account.provider = "telegram"
    account.provider_account_id = "123456789"
    account.access_token = ""
    return account


CHANNEL = "telegram"
SENDER_ID = "123456789"
VALID_EMAIL = "dangtt1971@gmail.com"


# ─────────────────────────────────────────────────────────────────────────────
# E1: /link with valid email -> code generated, stored in Redis, email sent
# ─────────────────────────────────────────────────────────────────────────────


class TestE1LinkValidEmail:
    """E1 — /link with valid email generates code, stores in Redis, sends email."""

    @pytest.mark.asyncio
    async def test_link_valid_email_success(
        self, mock_redis: AsyncMock, mock_db: AsyncMock, mock_user: MagicMock
    ) -> None:
        """E1a — happy path: user found, code stored, email sent, success reply."""
        # Arrange: DB returns the user
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = result_mock

        with patch(
            "app.services.email_service.send_email"
        ):
            reply = await handle_link_command(
                VALID_EMAIL, CHANNEL, SENDER_ID, mock_redis, mock_db
            )

        # Assert: success reply
        assert "Verification code sent" in reply
        assert VALID_EMAIL in reply
        assert "/verify" in reply

        # Assert: Redis setex was called with code_key and 300s TTL
        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args
        key = call_args[0][0]
        ttl = call_args[0][1]
        payload = json.loads(call_args[0][2])

        assert key == f"ott:link_code:{CHANNEL}:{SENDER_ID}"
        assert ttl == 300
        assert payload["email"] == VALID_EMAIL.lower()
        assert payload["user_id"] == str(mock_user.id)
        assert len(payload["code"]) == 6
        assert payload["code"].isdigit()

    @pytest.mark.asyncio
    async def test_link_valid_email_sends_email(
        self, mock_redis: AsyncMock, mock_db: AsyncMock, mock_user: MagicMock
    ) -> None:
        """E1b — email is sent with verification code via asyncio.to_thread."""
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = result_mock

        with patch(
            "app.services.agent_bridge.ott_link_handler.asyncio.to_thread",
            new_callable=AsyncMock,
        ) as patched_thread:
            reply = await handle_link_command(
                VALID_EMAIL, CHANNEL, SENDER_ID, mock_redis, mock_db
            )

        # Assert: to_thread called with send_email function
        patched_thread.assert_called_once()
        call_args = patched_thread.call_args[0]
        # First arg is the send_email function, then email, subject, html
        assert call_args[1] == VALID_EMAIL.lower()
        assert "Verification Code" in call_args[2]

    @pytest.mark.asyncio
    async def test_link_rate_counter_incremented(
        self, mock_redis: AsyncMock, mock_db: AsyncMock, mock_user: MagicMock
    ) -> None:
        """E1c — rate limit counter is incremented on valid request."""
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = result_mock

        with patch(
            "app.services.email_service.send_email"
        ):
            await handle_link_command(
                VALID_EMAIL, CHANNEL, SENDER_ID, mock_redis, mock_db
            )

        rate_key = f"ott:link_rate:{CHANNEL}:{SENDER_ID}"
        mock_redis.incr.assert_called_with(rate_key)


# ─────────────────────────────────────────────────────────────────────────────
# E2: /link with unknown email -> error reply, no Redis key created
# ─────────────────────────────────────────────────────────────────────────────


class TestE2LinkUnknownEmail:
    """E2 — /link with email not in system returns error, no code stored."""

    @pytest.mark.asyncio
    async def test_link_unknown_email_error(
        self, mock_redis: AsyncMock, mock_db: AsyncMock
    ) -> None:
        """E2a — unknown email returns 'not found' error reply."""
        # Arrange: DB returns None (no user)
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = result_mock

        reply = await handle_link_command(
            "unknown@nowhere.com", CHANNEL, SENDER_ID, mock_redis, mock_db
        )

        assert "Email not found" in reply
        assert "admin" in reply.lower() or "Contact" in reply

    @pytest.mark.asyncio
    async def test_link_unknown_email_no_redis_store(
        self, mock_redis: AsyncMock, mock_db: AsyncMock
    ) -> None:
        """E2b — no Redis setex call when email is unknown."""
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = result_mock

        await handle_link_command(
            "unknown@nowhere.com", CHANNEL, SENDER_ID, mock_redis, mock_db
        )

        mock_redis.setex.assert_not_called()

    @pytest.mark.asyncio
    async def test_link_invalid_email_format(
        self, mock_redis: AsyncMock, mock_db: AsyncMock
    ) -> None:
        """E2c — invalid email format returns error without DB query."""
        reply = await handle_link_command(
            "not-an-email", CHANNEL, SENDER_ID, mock_redis, mock_db
        )

        assert "Invalid email format" in reply
        mock_db.execute.assert_not_called()
        mock_redis.setex.assert_not_called()


# ─────────────────────────────────────────────────────────────────────────────
# E3: /verify with correct code -> oauth_accounts upserted
# ─────────────────────────────────────────────────────────────────────────────


class TestE3VerifyCorrectCode:
    """E3 — /verify with correct code upserts oauth_accounts row."""

    @pytest.mark.asyncio
    async def test_verify_correct_code_new_account(
        self, mock_redis: AsyncMock, mock_db: AsyncMock, mock_user: MagicMock
    ) -> None:
        """E3a — correct code with no existing oauth row creates new OAuthAccount."""
        user_id = str(mock_user.id)
        code = "847291"
        payload = json.dumps({
            "code": code,
            "user_id": user_id,
            "email": VALID_EMAIL,
        })
        mock_redis.get.return_value = payload
        mock_redis.getdel.return_value = payload

        # First execute: check existing OAuthAccount -> None
        # Second execute: fetch User for reply
        execute_results = [MagicMock(), MagicMock()]
        execute_results[0].scalar_one_or_none.return_value = None  # no existing link
        execute_results[1].scalar_one_or_none.return_value = mock_user  # user lookup
        mock_db.execute.side_effect = execute_results

        reply = await handle_verify_command(
            code, CHANNEL, SENDER_ID, mock_redis, mock_db
        )

        # Assert: success reply with user info
        assert "Account linked" in reply
        assert mock_user.full_name in reply
        assert mock_user.email in reply
        assert "governance commands" in reply

        # Assert: db.add called with new OAuthAccount
        mock_db.add.assert_called_once()
        added_obj = mock_db.add.call_args[0][0]
        assert added_obj.provider == CHANNEL
        assert added_obj.provider_account_id == SENDER_ID
        assert added_obj.access_token == ""  # ADR-068: empty token allowed
        assert added_obj.user_id == user_id

        # Assert: commit called
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_verify_correct_code_existing_account_updated(
        self, mock_redis: AsyncMock, mock_db: AsyncMock, mock_user: MagicMock, mock_oauth_account: MagicMock
    ) -> None:
        """E3b — correct code with existing oauth row updates user_id (D-068-03)."""
        user_id = str(mock_user.id)
        code = "123456"
        payload = json.dumps({
            "code": code,
            "user_id": user_id,
            "email": VALID_EMAIL,
        })
        mock_redis.get.return_value = payload
        mock_redis.getdel.return_value = payload

        # First execute: existing OAuthAccount found
        # Second execute: fetch User for reply
        execute_results = [MagicMock(), MagicMock()]
        execute_results[0].scalar_one_or_none.return_value = mock_oauth_account
        execute_results[1].scalar_one_or_none.return_value = mock_user
        mock_db.execute.side_effect = execute_results

        reply = await handle_verify_command(
            code, CHANNEL, SENDER_ID, mock_redis, mock_db
        )

        assert "Account linked" in reply

        # Assert: existing account updated, not a new one added
        mock_db.add.assert_not_called()
        assert mock_oauth_account.user_id == user_id
        assert mock_oauth_account.access_token == ""

    @pytest.mark.asyncio
    async def test_verify_clears_identity_cache(
        self, mock_redis: AsyncMock, mock_db: AsyncMock, mock_user: MagicMock
    ) -> None:
        """E3c — after successful verify, identity cache key is deleted."""
        user_id = str(mock_user.id)
        code = "999888"
        payload = json.dumps({
            "code": code,
            "user_id": user_id,
            "email": VALID_EMAIL,
        })
        mock_redis.get.return_value = payload
        mock_redis.getdel.return_value = payload

        execute_results = [MagicMock(), MagicMock()]
        execute_results[0].scalar_one_or_none.return_value = None
        execute_results[1].scalar_one_or_none.return_value = mock_user
        mock_db.execute.side_effect = execute_results

        await handle_verify_command(
            code, CHANNEL, SENDER_ID, mock_redis, mock_db
        )

        # Assert: code key consumed via GETDEL (FR-050-02 atomic single-use)
        code_key = f"ott:link_code:{CHANNEL}:{SENDER_ID}"
        mock_redis.getdel.assert_called_with(code_key)

        # Assert: identity cache key cleared via DELETE
        cache_key = f"ott:identity:{CHANNEL}:{SENDER_ID}"
        delete_calls = [c[0][0] for c in mock_redis.delete.call_args_list]
        assert cache_key in delete_calls


# ─────────────────────────────────────────────────────────────────────────────
# E4: /verify with wrong code -> error reply, Redis key NOT deleted
# ─────────────────────────────────────────────────────────────────────────────


class TestE4VerifyWrongCode:
    """E4 — /verify with incorrect code returns error, preserves Redis key."""

    @pytest.mark.asyncio
    async def test_verify_wrong_code_error(
        self, mock_redis: AsyncMock, mock_db: AsyncMock
    ) -> None:
        """E4a — wrong code returns 'wrong code' error."""
        payload = json.dumps({
            "code": "111111",
            "user_id": str(uuid4()),
            "email": VALID_EMAIL,
        })
        mock_redis.get.return_value = payload

        reply = await handle_verify_command(
            "999999", CHANNEL, SENDER_ID, mock_redis, mock_db
        )

        assert "Wrong verification code" in reply

    @pytest.mark.asyncio
    async def test_verify_wrong_code_key_not_deleted(
        self, mock_redis: AsyncMock, mock_db: AsyncMock
    ) -> None:
        """E4b — Redis code key is NOT deleted on wrong code (retry allowed)."""
        payload = json.dumps({
            "code": "111111",
            "user_id": str(uuid4()),
            "email": VALID_EMAIL,
        })
        mock_redis.get.return_value = payload

        await handle_verify_command(
            "999999", CHANNEL, SENDER_ID, mock_redis, mock_db
        )

        # Redis delete must NOT be called when code is wrong
        mock_redis.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_verify_wrong_code_no_db_write(
        self, mock_redis: AsyncMock, mock_db: AsyncMock
    ) -> None:
        """E4c — no DB operations on wrong code."""
        payload = json.dumps({
            "code": "111111",
            "user_id": str(uuid4()),
            "email": VALID_EMAIL,
        })
        mock_redis.get.return_value = payload

        await handle_verify_command(
            "999999", CHANNEL, SENDER_ID, mock_redis, mock_db
        )

        mock_db.execute.assert_not_called()
        mock_db.commit.assert_not_called()


# ─────────────────────────────────────────────────────────────────────────────
# E5: /verify with expired code -> error reply
# ─────────────────────────────────────────────────────────────────────────────


class TestE5VerifyExpiredCode:
    """E5 — /verify after code TTL expires returns expiration error."""

    @pytest.mark.asyncio
    async def test_verify_expired_code_error(
        self, mock_redis: AsyncMock, mock_db: AsyncMock
    ) -> None:
        """E5a — Redis returns None (TTL expired), error reply with re-link hint."""
        mock_redis.get.return_value = None

        reply = await handle_verify_command(
            "123456", CHANNEL, SENDER_ID, mock_redis, mock_db
        )

        assert "expired" in reply.lower()
        assert "/link" in reply

    @pytest.mark.asyncio
    async def test_verify_expired_no_db_operations(
        self, mock_redis: AsyncMock, mock_db: AsyncMock
    ) -> None:
        """E5b — no DB operations attempted when code is expired."""
        mock_redis.get.return_value = None

        await handle_verify_command(
            "123456", CHANNEL, SENDER_ID, mock_redis, mock_db
        )

        mock_db.execute.assert_not_called()
        mock_db.commit.assert_not_called()


# ─────────────────────────────────────────────────────────────────────────────
# E6: Double /verify -> second attempt fails (single-use deletion)
# ─────────────────────────────────────────────────────────────────────────────


class TestE6DoubleVerify:
    """E6 — second /verify fails because code key was deleted on first success."""

    @pytest.mark.asyncio
    async def test_double_verify_second_fails(
        self, mock_redis: AsyncMock, mock_db: AsyncMock, mock_user: MagicMock
    ) -> None:
        """E6 — first verify succeeds via GETDEL, second verify sees expired."""
        user_id = str(mock_user.id)
        code = "555666"
        payload = json.dumps({
            "code": code,
            "user_id": user_id,
            "email": VALID_EMAIL,
        })

        # First call: GET peeks at code, GETDEL consumes it
        # Second call: GET returns None (key was consumed by GETDEL)
        mock_redis.get.side_effect = [payload, None]
        mock_redis.getdel.return_value = payload  # First call consumes

        # DB mocks for first successful verify
        execute_results = [MagicMock(), MagicMock()]
        execute_results[0].scalar_one_or_none.return_value = None  # no existing link
        execute_results[1].scalar_one_or_none.return_value = mock_user
        mock_db.execute.side_effect = execute_results

        # First verify — success (code consumed via GETDEL)
        reply_1 = await handle_verify_command(
            code, CHANNEL, SENDER_ID, mock_redis, mock_db
        )
        assert "Account linked" in reply_1

        # Verify GETDEL was called on the code key (FR-050-02 atomic single-use)
        code_key = f"ott:link_code:{CHANNEL}:{SENDER_ID}"
        mock_redis.getdel.assert_called_with(code_key)

        # Second verify — fails because Redis GET returns None (key consumed)
        reply_2 = await handle_verify_command(
            code, CHANNEL, SENDER_ID, mock_redis, mock_db
        )
        assert "expired" in reply_2.lower()


# ─────────────────────────────────────────────────────────────────────────────
# E11: /unlink -> oauth_accounts deleted, cache cleared
# ─────────────────────────────────────────────────────────────────────────────


class TestE11Unlink:
    """E11 — /unlink removes oauth_accounts row and clears identity cache."""

    @pytest.mark.asyncio
    async def test_unlink_existing_account(
        self, mock_redis: AsyncMock, mock_db: AsyncMock, mock_oauth_account: MagicMock
    ) -> None:
        """E11a — unlink deletes linked account, clears cache, returns success."""
        # First execute: SELECT OAuthAccount -> found
        # Second execute: DELETE statement
        select_result = MagicMock()
        select_result.scalar_one_or_none.return_value = mock_oauth_account
        delete_result = MagicMock()
        mock_db.execute.side_effect = [select_result, delete_result]

        reply = await handle_unlink_command(
            CHANNEL, SENDER_ID, mock_redis, mock_db
        )

        assert "Account unlinked" in reply
        assert "/link" in reply

        # Assert: DB commit called (deletion committed)
        mock_db.commit.assert_called_once()

        # Assert: identity cache cleared
        cache_key = f"ott:identity:{CHANNEL}:{SENDER_ID}"
        delete_calls = [c[0][0] for c in mock_redis.delete.call_args_list]
        assert cache_key in delete_calls

    @pytest.mark.asyncio
    async def test_unlink_no_existing_account(
        self, mock_redis: AsyncMock, mock_db: AsyncMock
    ) -> None:
        """E11b — unlink with no linked account returns info message."""
        select_result = MagicMock()
        select_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = select_result

        reply = await handle_unlink_command(
            CHANNEL, SENDER_ID, mock_redis, mock_db
        )

        assert "No linked account" in reply
        assert "/link" in reply

        # Assert: no DELETE executed, no commit
        mock_db.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_unlink_db_error_rollback(
        self, mock_redis: AsyncMock, mock_db: AsyncMock, mock_oauth_account: MagicMock
    ) -> None:
        """E11c — DB error during unlink triggers rollback and error reply."""
        # SELECT succeeds, but then execute raises on DELETE
        select_result = MagicMock()
        select_result.scalar_one_or_none.return_value = mock_oauth_account
        mock_db.execute.side_effect = [select_result, RuntimeError("DB connection lost")]

        reply = await handle_unlink_command(
            CHANNEL, SENDER_ID, mock_redis, mock_db
        )

        assert "Failed to unlink" in reply
        mock_db.rollback.assert_called_once()


# ─────────────────────────────────────────────────────────────────────────────
# E12: /link rate limiting -> 6th attempt within 15 min blocked
# ─────────────────────────────────────────────────────────────────────────────


class TestE12RateLimiting:
    """E12 — /link rate limit: max 5 attempts per 15-min window."""

    @pytest.mark.asyncio
    async def test_sixth_attempt_blocked(
        self, mock_redis: AsyncMock, mock_db: AsyncMock
    ) -> None:
        """E12a — 6th /link attempt returns rate limit error."""
        # Arrange: Redis incr returns 6 (> _RATE_LIMIT_MAX of 5)
        mock_redis.incr.return_value = 6

        reply = await handle_link_command(
            VALID_EMAIL, CHANNEL, SENDER_ID, mock_redis, mock_db
        )

        assert "Too many link attempts" in reply
        assert "15 minutes" in reply

        # Assert: no DB lookup or Redis code storage
        mock_db.execute.assert_not_called()
        mock_redis.setex.assert_not_called()

    @pytest.mark.asyncio
    async def test_fifth_attempt_allowed(
        self, mock_redis: AsyncMock, mock_db: AsyncMock, mock_user: MagicMock
    ) -> None:
        """E12b — 5th attempt (exactly at limit) is still allowed."""
        mock_redis.incr.return_value = 5

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = result_mock

        with patch(
            "app.services.email_service.send_email"
        ):
            reply = await handle_link_command(
                VALID_EMAIL, CHANNEL, SENDER_ID, mock_redis, mock_db
            )

        # 5th attempt should succeed (limit is >5, not >=5)
        assert "Verification code sent" in reply

    @pytest.mark.asyncio
    async def test_first_attempt_sets_ttl(
        self, mock_redis: AsyncMock, mock_db: AsyncMock, mock_user: MagicMock
    ) -> None:
        """E12c — first attempt (incr returns 1) sets 15-min TTL on rate key."""
        mock_redis.incr.return_value = 1

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = result_mock

        with patch(
            "app.services.email_service.send_email"
        ):
            await handle_link_command(
                VALID_EMAIL, CHANNEL, SENDER_ID, mock_redis, mock_db
            )

        rate_key = f"ott:link_rate:{CHANNEL}:{SENDER_ID}"
        mock_redis.expire.assert_called_with(rate_key, 900)

    @pytest.mark.asyncio
    async def test_second_attempt_no_ttl_reset(
        self, mock_redis: AsyncMock, mock_db: AsyncMock, mock_user: MagicMock
    ) -> None:
        """E12d — second attempt (incr returns 2) does NOT reset TTL."""
        mock_redis.incr.return_value = 2

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = result_mock

        with patch(
            "app.services.email_service.send_email"
        ):
            await handle_link_command(
                VALID_EMAIL, CHANNEL, SENDER_ID, mock_redis, mock_db
            )

        # expire should NOT be called when count != 1
        mock_redis.expire.assert_not_called()


# ─────────────────────────────────────────────────────────────────────────────
# Edge cases — input validation
# ─────────────────────────────────────────────────────────────────────────────


class TestInputValidation:
    """Additional edge-case tests for input validation paths."""

    @pytest.mark.asyncio
    async def test_link_empty_email_shows_usage(
        self, mock_redis: AsyncMock, mock_db: AsyncMock
    ) -> None:
        """Empty /link args returns usage help."""
        reply = await handle_link_command(
            "", CHANNEL, SENDER_ID, mock_redis, mock_db
        )

        assert "Usage" in reply
        assert "/link" in reply

    @pytest.mark.asyncio
    async def test_verify_empty_code_shows_usage(
        self, mock_redis: AsyncMock, mock_db: AsyncMock
    ) -> None:
        """Empty /verify args returns usage help."""
        reply = await handle_verify_command(
            "", CHANNEL, SENDER_ID, mock_redis, mock_db
        )

        assert "Usage" in reply
        assert "/verify" in reply

    @pytest.mark.asyncio
    async def test_verify_non_digit_code_rejected(
        self, mock_redis: AsyncMock, mock_db: AsyncMock
    ) -> None:
        """Non-numeric /verify code returns usage error."""
        reply = await handle_verify_command(
            "abcdef", CHANNEL, SENDER_ID, mock_redis, mock_db
        )

        assert "Usage" in reply

    @pytest.mark.asyncio
    async def test_verify_five_digit_code_rejected(
        self, mock_redis: AsyncMock, mock_db: AsyncMock
    ) -> None:
        """5-digit code (too short) returns usage error."""
        reply = await handle_verify_command(
            "12345", CHANNEL, SENDER_ID, mock_redis, mock_db
        )

        assert "Usage" in reply

    @pytest.mark.asyncio
    async def test_verify_seven_digit_code_rejected(
        self, mock_redis: AsyncMock, mock_db: AsyncMock
    ) -> None:
        """7-digit code (too long) returns usage error."""
        reply = await handle_verify_command(
            "1234567", CHANNEL, SENDER_ID, mock_redis, mock_db
        )

        assert "Usage" in reply


# ─────────────────────────────────────────────────────────────────────────────
# /whoami — show current identity binding status
# ─────────────────────────────────────────────────────────────────────────────


class TestWhoami:
    """/whoami — displays linked identity or prompts user to link."""

    @pytest.mark.asyncio
    async def test_whoami_linked_user(
        self, mock_redis: AsyncMock, mock_db: AsyncMock, mock_user: MagicMock, mock_oauth_account: MagicMock
    ) -> None:
        """Linked user sees name, email, and user ID."""
        mock_oauth_account.user_id = mock_user.id

        # First execute: OAuthAccount found
        # Second execute: User found
        execute_results = [MagicMock(), MagicMock()]
        execute_results[0].scalar_one_or_none.return_value = mock_oauth_account
        execute_results[1].scalar_one_or_none.return_value = mock_user
        mock_db.execute.side_effect = execute_results

        reply = await handle_whoami_command(
            CHANNEL, SENDER_ID, mock_redis, mock_db
        )

        assert "Linked" in reply
        assert mock_user.full_name in reply
        assert mock_user.email in reply
        assert str(mock_user.id)[:8] in reply

    @pytest.mark.asyncio
    async def test_whoami_unlinked_user(
        self, mock_redis: AsyncMock, mock_db: AsyncMock
    ) -> None:
        """Unlinked user sees 'Not linked' and /link hint."""
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = result_mock

        reply = await handle_whoami_command(
            CHANNEL, SENDER_ID, mock_redis, mock_db
        )

        assert "Not linked" in reply
        assert "/link" in reply
        assert CHANNEL in reply
        assert SENDER_ID in reply

    @pytest.mark.asyncio
    async def test_whoami_linked_but_user_deleted(
        self, mock_redis: AsyncMock, mock_db: AsyncMock, mock_oauth_account: MagicMock
    ) -> None:
        """Linked account but user record deleted shows warning."""
        # First execute: OAuthAccount found
        # Second execute: User NOT found (deleted)
        execute_results = [MagicMock(), MagicMock()]
        execute_results[0].scalar_one_or_none.return_value = mock_oauth_account
        execute_results[1].scalar_one_or_none.return_value = None
        mock_db.execute.side_effect = execute_results

        reply = await handle_whoami_command(
            CHANNEL, SENDER_ID, mock_redis, mock_db
        )

        assert "user not found" in reply.lower()
        assert "/unlink" in reply

    @pytest.mark.asyncio
    async def test_whoami_db_error(
        self, mock_redis: AsyncMock, mock_db: AsyncMock
    ) -> None:
        """DB error returns generic error reply."""
        mock_db.execute.side_effect = RuntimeError("DB connection lost")

        reply = await handle_whoami_command(
            CHANNEL, SENDER_ID, mock_redis, mock_db
        )

        assert "Failed" in reply or "error" in reply.lower()
