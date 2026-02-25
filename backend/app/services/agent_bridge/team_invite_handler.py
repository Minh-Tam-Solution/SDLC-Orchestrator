"""
Team Invite Handler — Invite team members via OTT chat.

Sprint 201 Track A (A-05): Team invitation through OTT channels
(Telegram / Zalo).

Architecture:
    User: "invite dev@example.com to my team"
      │
      ├─ chat_command_router.py  → tool_call: invite_member(team_id=..., email=...)
      │
      ├─ governance_action_handler.py  → dispatch to this handler
      │
      ├─ team_invite_handler.py  ← THIS FILE
      │   ├─ invitation_service.send_invitation()
      │   ├─ Rate limit checks (team + email)
      │   └─ Format bilingual confirmation
      │
      └─ _send_reply()  → Telegram / Zalo

Security:
- Rate limiting: 50 invitations/hour per team, 3/day per email
- SHA256 token hashing (raw tokens never stored)
- Audit trail: IP, user agent, timestamps

DB Session: Creates standalone AsyncSession via AsyncSessionLocal
(fire-and-forget, runs AFTER webhook 200 response).

Sprint 201 — Track A: Self-Governance Setup
"""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from app.db.session import AsyncSessionLocal

logger = logging.getLogger(__name__)


async def handle_invite_member(
    tool_args: dict[str, Any],
    bot_token: str,
    chat_id: str | int,
    user_id: str,
    channel: str = "telegram",
) -> bool:
    """
    Invite a new team member via email from OTT chat.

    Flow:
        1. Validate team_id and email
        2. Check rate limits (team + email)
        3. Send invitation via invitation_service
        4. Send confirmation reply to OTT chat

    Args:
        tool_args: Validated parameters {"team_id": UUID, "email": str, "role": str}
        bot_token: Telegram Bot API token (empty for Zalo)
        chat_id: OTT chat/user ID for reply
        user_id: Authenticated user ID
        channel: OTT channel ("telegram" or "zalo")

    Returns:
        True if invitation sent and reply delivered, False on error
    """
    from app.services.agent_bridge.governance_action_handler import (
        _send_telegram_reply,
        _format_error,
    )

    team_id_str = str(tool_args.get("team_id", ""))
    email = str(tool_args.get("email", "")).strip().lower()
    role = str(tool_args.get("role", "member")).strip().lower()

    # Validate team_id
    try:
        team_id = UUID(team_id_str)
    except ValueError:
        await _send_telegram_reply(
            bot_token, chat_id,
            _format_error(f"Invalid team ID: {team_id_str}"),
            channel=channel,
        )
        return False

    # Validate email format (basic check)
    if "@" not in email or "." not in email.split("@")[-1]:
        await _send_telegram_reply(
            bot_token, chat_id,
            _format_error(
                f"Email không hợp lệ: {email}\n"
                f"Invalid email address: {email}"
            ),
            channel=channel,
        )
        return False

    # Validate role
    allowed_roles = ("member", "admin")
    if role not in allowed_roles:
        role = "member"

    async with AsyncSessionLocal() as db:
        from fastapi import HTTPException
        from app.schemas.invitation import InvitationCreate
        from app.services.invitation_service import send_invitation

        invitation_data = InvitationCreate(email=email, role=role)

        try:
            response, raw_token = await send_invitation(
                team_id=team_id,
                data=invitation_data,
                invited_by_user_id=UUID(user_id),
                db=db,
            )
        except HTTPException as exc:
            detail = exc.detail
            if isinstance(detail, dict):
                message = detail.get("message", str(detail))
            else:
                message = str(detail)

            error_text = {
                404: f"Team không tồn tại: {team_id_str}\nTeam not found.",
                409: f"Đã có lời mời đang chờ cho {email}.\n"
                     f"Pending invitation already exists for {email}.",
                429: f"Vượt giới hạn gửi lời mời.\n"
                     f"Invitation rate limit exceeded.",
            }.get(exc.status_code, message)

            await _send_telegram_reply(
                bot_token, chat_id,
                _format_error(error_text),
                channel=channel,
            )
            return False

        logger.info(
            "team_invite_handler: invitation sent team=%s email=%s role=%s user=%s",
            team_id,
            email,
            role,
            user_id,
        )

        reply = (
            f"\U0001f4e8 Invitation Sent / Đã gửi lời mời\n"
            f"\n"
            f"\U0001f4e7 Email: {email}\n"
            f"\U0001f465 Team: {team_id_str[:8]}...\n"
            f"\U0001f464 Role: {role}\n"
            f"\U0001f4ca Status: PENDING\n"
            f"\u23f0 Expires: {response.expires_at:%Y-%m-%d}\n"
            f"\n"
            f"Lời mời đã được gửi. Người nhận sẽ nhận email xác nhận.\n"
            f"Invitation sent. The recipient will receive a confirmation email."
        )

        return await _send_telegram_reply(
            bot_token, chat_id, reply, channel=channel,
        )
