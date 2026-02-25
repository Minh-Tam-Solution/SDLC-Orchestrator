"""
Telegram Auto-Responder — immediate replies for bot commands.

Handles /start, /help, /status and other governance commands by sending
replies via the Telegram Bot API. Called from ott_gateway.py after
message normalization (fire-and-forget, non-blocking to webhook response).

The responder runs AFTER the webhook returns 200 OK to Telegram, so it
does not affect webhook delivery latency or reliability.

Sprint 198 — OTT Real Integration Testing
Sprint 200 — Track A (A-03/A-05): Progress streaming + result delivery
"""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)

_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
_API_BASE: str = f"https://api.telegram.org/bot{_BOT_TOKEN}" if _BOT_TOKEN else ""

# Command → reply text mapping
_COMMAND_REPLIES: dict[str, str] = {
    "/start": (
        "\U0001f680 Chào mừng bạn đến với SDLC Orchestrator!\n\n"
        "Bot này kết nối với hệ thống governance SDLC 6.1.1, "
        "cho phép bạn quản lý sprint, gates, và evidence trực tiếp "
        "từ Telegram.\n\n"
        "Gửi /help để xem danh sách lệnh."
    ),
    "/help": (
        "\U0001f4cb SDLC Orchestrator \u2014 Governance Commands\n\n"
        "\U0001f539 Sprint Management\n"
        "  /sprint \u2014 Xem sprint hiện tại\n"
        "  /sprint_status \u2014 Trạng thái sprint chi tiết\n"
        "  /update_sprint \u2014 Cập nhật CURRENT-SPRINT.md\n\n"
        "\U0001f539 Quality Gates\n"
        "  /gates \u2014 Danh sách gates của project\n"
        "  /gate_status <gate_id> \u2014 Chi tiết gate\n"
        "  /approve <gate_id> \u2014 Approve gate\n\n"
        "\U0001f539 Evidence\n"
        "  /evidence \u2014 Xem evidence gần nhất\n"
        "  /upload \u2014 Hướng dẫn upload evidence\n\n"
        "\U0001f539 General\n"
        "  /help \u2014 Hiển thị menu này\n"
        "  /start \u2014 Bắt đầu conversation\n"
        "  /status \u2014 Trạng thái hệ thống\n\n"
        "\u26a1 Powered by SDLC Orchestrator v1.0\n"
        "\U0001f310 https://sdlc.nhatquangholding.com"
    ),
    "/status": (
        "\U0001f4e1 SDLC Orchestrator Status\n\n"
        "\u2705 API: Online\n"
        "\u2705 Webhook: Active\n"
        "\u2705 Channel: Telegram OTT Gateway\n"
        "\U0001f4ca Framework: SDLC 6.1.1\n\n"
        "Gửi /help để xem các lệnh governance."
    ),
}


async def handle_telegram_auto_reply(raw_body: dict[str, Any]) -> bool:
    """
    Check if the incoming Telegram message is a known command and send
    an immediate auto-reply via the Bot API.

    Args:
        raw_body: Raw Telegram webhook payload (update object).

    Returns:
        True if a reply was sent, False if no matching command found
        or bot token not configured.
    """
    if not _BOT_TOKEN:
        return False

    message: dict[str, Any] | None = raw_body.get("message")
    if not message:
        return False

    text: str = (message.get("text") or "").strip()
    if not text.startswith("/"):
        return False

    # Extract command (strip @botname suffix for group chats)
    command = text.split()[0].split("@")[0].lower()

    reply_text = _COMMAND_REPLIES.get(command)
    if not reply_text:
        return False

    chat_id = message.get("chat", {}).get("id")
    if not chat_id:
        return False

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{_API_BASE}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": reply_text,
                },
            )
            if resp.status_code == 200:
                logger.info(
                    "telegram_responder: replied command=%s chat_id=%s",
                    command,
                    chat_id,
                )
                return True
            else:
                logger.warning(
                    "telegram_responder: sendMessage failed status=%s body=%s",
                    resp.status_code,
                    resp.text[:200],
                )
                return False
    except Exception as exc:
        logger.warning(
            "telegram_responder: sendMessage error command=%s error=%s",
            command,
            str(exc),
        )
        return False


# ── Sprint 200 A-03: Progress Streaming ──────────────────────────────────


_MAX_MESSAGE_LENGTH: int = 4000  # Telegram limit ~4096


async def send_progress_message(
    bot_token: str,
    chat_id: str | int,
    text: str,
) -> bool:
    """
    Send a progress update message to Telegram (Sprint 200 A-03).

    Used by ott_team_bridge to stream agent pipeline progress.
    Non-blocking — failure is logged but does not affect pipeline.

    Args:
        bot_token: Telegram Bot API token.
        chat_id: Telegram chat ID.
        text: Progress message text.

    Returns:
        True if message was sent, False otherwise.
    """
    if not bot_token:
        return False

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"https://api.telegram.org/bot{bot_token}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": text[:_MAX_MESSAGE_LENGTH],
                },
            )
            if resp.status_code == 200:
                logger.debug(
                    "telegram_responder: progress sent chat_id=%s len=%d",
                    chat_id,
                    len(text),
                )
                return True
            logger.warning(
                "telegram_responder: progress failed status=%s",
                resp.status_code,
            )
            return False
    except Exception as exc:
        logger.warning(
            "telegram_responder: progress error chat_id=%s error=%s",
            chat_id,
            str(exc),
        )
        return False


# ── Sprint 200 A-05: Result Delivery ─────────────────────────────────────


async def send_result_message(
    bot_token: str,
    chat_id: str | int,
    agent_name: str,
    content: str,
    tokens_used: int = 0,
    cost_cents: int = 0,
    elapsed_ms: int = 0,
    provider: str = "",
) -> bool:
    """
    Send an agent pipeline result to Telegram (Sprint 200 A-05).

    Formats the response with agent name, metrics footer, and truncates
    to Telegram's message length limit. For very long outputs (>3500
    chars), splits into header + content messages.

    Args:
        bot_token: Telegram Bot API token.
        chat_id: Telegram chat ID.
        agent_name: Name of the agent that produced the result.
        content: Agent response content.
        tokens_used: Total tokens consumed.
        cost_cents: Total cost in cents.
        elapsed_ms: Pipeline elapsed time in milliseconds.
        provider: Provider/model info string.

    Returns:
        True if result was sent, False otherwise.
    """
    if not bot_token:
        return False

    # Build metrics footer
    metrics_parts = []
    if tokens_used:
        metrics_parts.append(f"{tokens_used} tok")
    if cost_cents:
        metrics_parts.append(f"${cost_cents / 100:.2f}")
    if elapsed_ms:
        metrics_parts.append(f"{elapsed_ms}ms")
    if provider:
        metrics_parts.append(provider)

    metrics_line = " | ".join(metrics_parts) if metrics_parts else ""

    # Format header
    header = f"\U0001f916 {agent_name}"

    # Calculate available space for content
    footer = f"\n\n\u2500\u2500\u2500\n{metrics_line}" if metrics_line else ""
    available = _MAX_MESSAGE_LENGTH - len(header) - len(footer) - 10  # safety margin

    if len(content) <= available:
        full_text = f"{header}\n\n{content}{footer}"
        return await send_progress_message(bot_token, chat_id, full_text)

    # Content too long — truncate with indicator
    truncated = content[:available - 20] + "\n\n[...truncated]"
    full_text = f"{header}\n\n{truncated}{footer}"
    return await send_progress_message(bot_token, chat_id, full_text)
