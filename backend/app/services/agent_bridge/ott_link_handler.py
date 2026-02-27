"""
OTT Link Handler — /link, /verify, /unlink command handlers.

Sprint 209 — ADR-068 OTT Identity Linking.
Email verification flow: user sends /link <email> → 6-digit code → /verify <code>.

Architecture:
    Lives in agent_bridge/ (channel abstraction layer).
    Reuses oauth_accounts table (same table as GitHub/Google OAuth, different provider).
    Redis stores verification codes with 5-min TTL.
    Email sent via asyncio.to_thread (P0-3: send_email is sync, blocks event loop).

Redis keys (ADR-067 convention):
    ott:link_code:{channel}:{sender_id}  → JSON{code, user_id, email}  (5-min TTL)
    ott:link_rate:{channel}:{sender_id}  → int counter                 (15-min TTL)
    ott:identity:{channel}:{sender_id}   → User UUID string            (60-min TTL)
"""

from __future__ import annotations

import asyncio
import json
import logging
import random
import re
from typing import Any
from uuid import uuid4

from sqlalchemy import select, delete

logger = logging.getLogger(__name__)

_CODE_TTL = 300  # 5 minutes
_RATE_LIMIT_MAX = 5
_RATE_LIMIT_WINDOW = 900  # 15 minutes
_EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


async def handle_link_command(
    args_text: str,
    channel: str,
    sender_id: str,
    redis: Any,
    db: Any,
) -> str:
    """
    Handle /link <email> — initiate account linking.

    Args:
        args_text: Email address (stripped from /link prefix).
        channel: OTT channel ('telegram', 'zalo').
        sender_id: External sender ID.
        redis: Redis client.
        db: AsyncSession for user lookup.

    Returns:
        Reply message string for the user.
    """
    email = args_text.strip()

    # No argument → usage help
    if not email:
        return (
            "ℹ️ Usage: /link <your-sdlc-email>\n"
            "Example: /link dangtt1971@gmail.com\n"
            "This links your Telegram account to your SDLC Orchestrator user."
        )

    # Validate email format
    if not _EMAIL_RE.match(email):
        return "❌ Invalid email format. Usage: /link your-email@example.com"

    # Rate limit check (CTO M2: max 5 per 15 min)
    rate_key = f"ott:link_rate:{channel}:{sender_id}"
    try:
        count = await redis.incr(rate_key)
        if count == 1:
            await redis.expire(rate_key, _RATE_LIMIT_WINDOW)
        if count > _RATE_LIMIT_MAX:
            return "⚠️ Too many link attempts. Try again in 15 minutes."
    except Exception as exc:
        logger.warning("ott_link: rate limit check failed: %s", exc)

    # Look up user by email (case-insensitive)
    try:
        from app.models.user import User
        stmt = select(User).where(
            User.email == email.lower().strip(),
            User.is_active.is_(True),
        )
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
    except Exception as exc:
        logger.error("ott_link: user lookup failed email=%s error=%s", email, exc)
        return "❌ Service error. Please try again later."

    if not user:
        return (
            "❌ Email not found in SDLC Orchestrator.\n"
            "Contact your admin to create an account first."
        )

    # Generate 6-digit code
    code = str(random.randint(100000, 999999))

    # Store in Redis
    code_key = f"ott:link_code:{channel}:{sender_id}"
    payload = json.dumps({
        "code": code,
        "user_id": str(user.id),
        "email": email.lower().strip(),
    })
    try:
        await redis.setex(code_key, _CODE_TTL, payload)
    except Exception as exc:
        logger.error("ott_link: Redis store failed: %s", exc)
        return "❌ Service temporarily unavailable. Please try again."

    # Send email (P0-3: wrap sync send_email in asyncio.to_thread)
    try:
        from app.services.email_service import send_email

        subject = "SDLC Orchestrator — Verification Code"
        html_content = (
            f"<h2>Your Verification Code</h2>"
            f"<p>Use this code to link your {channel.title()} account:</p>"
            f"<h1 style='font-size:36px;letter-spacing:8px;color:#2563eb'>{code}</h1>"
            f"<p>This code expires in 5 minutes.</p>"
            f"<p>If you did not request this, please ignore this email.</p>"
        )
        await asyncio.to_thread(send_email, email.lower().strip(), subject, html_content)
    except Exception as exc:
        logger.error("ott_link: email send failed email=%s error=%s", email, exc)
        return (
            "⚠️ Verification code generated but email delivery failed.\n"
            "Contact admin or try again later."
        )

    return (
        f"📧 Verification code sent to {email}\n"
        f"Reply /verify <code> within 5 minutes."
    )


async def handle_verify_command(
    args_text: str,
    channel: str,
    sender_id: str,
    redis: Any,
    db: Any,
) -> str:
    """
    Handle /verify <code> — complete account linking.

    Uses Redis GETDEL for atomic read+delete (FR-050-02 single-use guarantee).
    Wrong code falls back to GET (non-destructive) to allow retry.

    Args:
        args_text: 6-digit code.
        channel: OTT channel.
        sender_id: External sender ID.
        redis: Redis client.
        db: AsyncSession for oauth_accounts upsert.

    Returns:
        Reply message string.
    """
    code_input = args_text.strip()

    if not code_input or not code_input.isdigit() or len(code_input) != 6:
        return "❌ Usage: /verify <6-digit-code>\nExample: /verify 847291"

    # Read pending code — first peek (non-destructive) to validate code
    code_key = f"ott:link_code:{channel}:{sender_id}"
    try:
        raw = await redis.get(code_key)
    except Exception as exc:
        logger.error("ott_verify: Redis read failed: %s", exc)
        return "❌ Service temporarily unavailable. Please try again."

    if not raw:
        return "❌ Verification code expired. Send /link <email> to get a new code."

    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return "❌ Verification code expired. Send /link <email> to get a new code."

    stored_code = data.get("code", "")
    user_id = data.get("user_id", "")
    email = data.get("email", "")

    # Validate code — wrong code does NOT consume the key (user can retry)
    if code_input != stored_code:
        return "❌ Wrong verification code. Check your email and try again."

    # Code matches — atomic GETDEL for single-use guarantee (FR-050-02)
    # GETDEL ensures no race condition: if two requests arrive simultaneously,
    # only one gets the data, the other sees None → "expired" response.
    try:
        consumed = await redis.getdel(code_key)
        if not consumed:
            # Another request consumed the key between GET and GETDEL
            return "❌ Verification code expired. Send /link <email> to get a new code."
    except AttributeError:
        # Redis <6.2 fallback: DELETE (not atomic but functional)
        try:
            await redis.delete(code_key)
        except Exception:
            pass
    except Exception:
        # Best-effort delete on Redis error
        try:
            await redis.delete(code_key)
        except Exception:
            pass

    # Upsert oauth_accounts (D-068-03: ON CONFLICT update user_id)
    try:
        from app.models.user import OAuthAccount, User

        # Check for existing row
        stmt = select(OAuthAccount).where(
            OAuthAccount.provider == channel,
            OAuthAccount.provider_account_id == sender_id,
        )
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            existing.user_id = user_id
            existing.access_token = ""
        else:
            new_account = OAuthAccount(
                id=uuid4(),
                user_id=user_id,
                provider=channel,
                provider_account_id=sender_id,
                access_token="",
            )
            db.add(new_account)

        await db.commit()

        # Clear identity cache so next message uses new mapping
        cache_key = f"ott:identity:{channel}:{sender_id}"
        try:
            await redis.delete(cache_key)
        except Exception:
            pass

        # Fetch user info for reply
        user_stmt = select(User).where(User.id == user_id)
        user_result = await db.execute(user_stmt)
        user = user_result.scalar_one_or_none()
        full_name = user.full_name if user and user.full_name else "User"
        user_email = user.email if user else email

        logger.info(
            "ott_verify: linked %s:%s → %s (%s)",
            channel, sender_id, user_id, user_email,
        )

        return (
            f"✅ Account linked!\n"
            f"Name: {full_name}\n"
            f"Email: {user_email}\n"
            f"You can now use all governance commands."
        )

    except Exception as exc:
        logger.error(
            "ott_verify: upsert failed %s:%s error=%s",
            channel, sender_id, exc,
        )
        await db.rollback()
        return "❌ Failed to link account. Please try again."


async def handle_unlink_command(
    channel: str,
    sender_id: str,
    redis: Any,
    db: Any,
) -> str:
    """
    Handle /unlink — remove account linking.

    Args:
        channel: OTT channel.
        sender_id: External sender ID.
        redis: Redis client.
        db: AsyncSession for oauth_accounts delete.

    Returns:
        Reply message string.
    """
    try:
        from app.models.user import OAuthAccount

        # Check if linked
        stmt = select(OAuthAccount).where(
            OAuthAccount.provider == channel,
            OAuthAccount.provider_account_id == sender_id,
        )
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()

        if not existing:
            return (
                "ℹ️ No linked account found.\n"
                "Use /link <email> to connect your Telegram."
            )

        # Delete the link
        del_stmt = delete(OAuthAccount).where(
            OAuthAccount.provider == channel,
            OAuthAccount.provider_account_id == sender_id,
        )
        await db.execute(del_stmt)
        await db.commit()

        # Clear identity cache
        cache_key = f"ott:identity:{channel}:{sender_id}"
        try:
            await redis.delete(cache_key)
        except Exception:
            pass

        logger.info("ott_unlink: removed %s:%s", channel, sender_id)

        return (
            "✅ Account unlinked.\n"
            "Use /link <email> to reconnect."
        )

    except Exception as exc:
        logger.error(
            "ott_unlink: failed %s:%s error=%s",
            channel, sender_id, exc,
        )
        await db.rollback()
        return "❌ Failed to unlink account. Please try again."


async def handle_whoami_command(
    channel: str,
    sender_id: str,
    redis: Any,
    db: Any,
) -> str:
    """
    Handle /whoami — show current identity binding status.

    Displays: linked user info (name, email, role) or unlinked status.
    Team Collaboration Flow Section 7.3 requirement.

    Args:
        channel: OTT channel ('telegram', 'zalo').
        sender_id: External sender ID.
        redis: Redis client.
        db: AsyncSession for user lookup.

    Returns:
        Reply message string with identity status.
    """
    try:
        from app.models.user import OAuthAccount, User

        # Look up existing link
        stmt = select(OAuthAccount).where(
            OAuthAccount.provider == channel,
            OAuthAccount.provider_account_id == sender_id,
        )
        result = await db.execute(stmt)
        account = result.scalar_one_or_none()

        if not account:
            return (
                f"ℹ️ Identity: Not linked\n"
                f"Channel: {channel}\n"
                f"Sender ID: {sender_id}\n"
                f"\nUse /link <email> to connect your SDLC account."
            )

        # Fetch user details
        user_stmt = select(User).where(User.id == account.user_id)
        user_result = await db.execute(user_stmt)
        user = user_result.scalar_one_or_none()

        if not user:
            return (
                f"⚠️ Identity: Linked but user not found\n"
                f"User ID: {account.user_id}\n"
                f"This may indicate a deleted account. Use /unlink then /link <email>."
            )

        full_name = user.full_name if user.full_name else user.username or "N/A"
        return (
            f"✅ Identity: Linked\n"
            f"Name: {full_name}\n"
            f"Email: {user.email}\n"
            f"User ID: {str(user.id)[:8]}...\n"
            f"Channel: {channel}\n"
            f"Sender ID: {sender_id}"
        )

    except Exception as exc:
        logger.error(
            "ott_whoami: failed %s:%s error=%s",
            channel, sender_id, exc,
        )
        return "❌ Failed to check identity. Please try again."
