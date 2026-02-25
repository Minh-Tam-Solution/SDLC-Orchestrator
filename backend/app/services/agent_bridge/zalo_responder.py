"""
Zalo OA Responder — Sprint 200 C-01/C-04.

Sends messages back to Zalo OA users via the Zalo Open API.
Handles auto-replies, progress streaming, and result delivery
with Zalo-specific formatting (plain text, no Markdown).

Architecture:
    ott_gateway.py → _zalo_dispatch() (fire-and-forget)
        → zalo_responder.handle_zalo_auto_reply()    — /commands
        → ai_response_handler.handle_ai_response()   — free-text AI

Zalo API:
    POST https://openapi.zalo.me/v3.0/oa/message/cs
    Headers: { access_token: <token> }
    Body: { recipient: {user_id}, message: {text} }

Sprint 200 — Track C: Cross-Channel Agent Parity
ADR-060: Channel-agnostic OrchestratorMessage
"""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

_ZALO_OA_ACCESS_TOKEN: str = os.getenv("ZALO_OA_ACCESS_TOKEN", "")

# Zalo message send endpoint (Customer Service API — 48h window)
_ZALO_SEND_URL = "https://openapi.zalo.me/v3.0/oa/message/cs"

# Zalo text limit (~2000 chars per message)
_ZALO_MAX_TEXT_LEN = 2000

# Command auto-replies (Sprint 200 C-01)
_COMMAND_REPLIES: dict[str, str] = {
    "/start": (
        "Xin chao! SDLC Orchestrator san sang.\n\n"
        "Gui tin nhan de bat dau hoi thoai voi AI.\n"
        "Dung 'generate code' de goi agent team.\n"
        "Dung 'stop' de dung agent."
    ),
    "/help": (
        "Cac lenh co san:\n"
        "- /start — Bat dau\n"
        "- /help — Tro giup\n"
        "- /status — Trang thai ket noi\n"
        "- generate code <mo ta> — Goi agent team\n"
        "- gate status — Xem trang thai gate\n"
        "- approve gate — Duyet gate\n"
        "- stop — Dung agent dang chay"
    ),
    "/status": (
        "Zalo OA Gateway: Online\n"
        "Tinh nang: AI Chat, Agent Team, Gate Actions\n"
        "Framework: SDLC 6.1.1"
    ),
}


async def _send_zalo_message(
    user_id: str,
    text: str,
) -> bool:
    """
    Send a text message to a Zalo user via the OA Customer Service API.

    Zalo requires an OAuth 2.0 access token (not a simple bot token).
    The CS API has a 48-hour response window after user's last message.

    Returns True if sent successfully, False on error.
    """
    if not _ZALO_OA_ACCESS_TOKEN:
        logger.warning("zalo_responder: ZALO_OA_ACCESS_TOKEN not configured")
        return False

    if not user_id:
        return False

    # Truncate to Zalo limit
    if len(text) > _ZALO_MAX_TEXT_LEN:
        text = text[: _ZALO_MAX_TEXT_LEN - 20] + "\n\n[TRUNCATED]"

    import httpx

    payload = {
        "recipient": {"user_id": user_id},
        "message": {"text": text},
    }

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                _ZALO_SEND_URL,
                json=payload,
                headers={"access_token": _ZALO_OA_ACCESS_TOKEN},
            )

        if resp.status_code == 200:
            data = resp.json()
            if data.get("error") == 0:
                return True
            logger.warning(
                "zalo_responder: API error code=%s msg=%s",
                data.get("error"),
                data.get("message"),
            )
            return False

        logger.warning(
            "zalo_responder: HTTP %d from Zalo API", resp.status_code
        )
        return False

    except Exception as exc:
        logger.warning(
            "zalo_responder: send failed user_id=%s error=%s",
            user_id,
            str(exc),
        )
        return False


async def handle_zalo_auto_reply(raw_body: dict[str, Any]) -> bool:
    """
    Check if incoming Zalo message is a known /command and send auto-reply.

    Called from ott_gateway.py fire-and-forget after returning 200 to Zalo.
    Non-blocking — failure doesn't affect webhook acknowledgment.

    Returns True if a command was handled, False otherwise.
    """
    event_name = raw_body.get("event_name", "")
    if event_name != "user_send_text":
        return False

    message = raw_body.get("message", {})
    text = message.get("text", "").strip()
    sender = raw_body.get("sender", {})
    user_id = sender.get("id", "")

    if not text or not user_id:
        return False

    # Check for /command
    cmd = text.split()[0].lower() if text.startswith("/") else None
    if cmd and cmd in _COMMAND_REPLIES:
        return await _send_zalo_message(user_id, _COMMAND_REPLIES[cmd])

    return False


async def send_progress_message(
    user_id: str,
    text: str,
) -> bool:
    """
    Send a progress update to Zalo user (Sprint 200 C-01).

    Plain text only — Zalo OA does not support Markdown.
    """
    return await _send_zalo_message(user_id, text)


async def send_result_message(
    user_id: str,
    agent_name: str,
    content: str,
    tokens_used: int = 0,
    cost_cents: int = 0,
    elapsed_ms: int = 0,
    provider: str = "",
) -> bool:
    """
    Send an agent pipeline result to Zalo user (Sprint 200 C-01/C-04).

    Formatted as plain text (Zalo doesn't support Markdown):
        [Agent: coder]
        <content>

        --- Metrics ---
        Tokens: 1,234 | Cost: $0.02 | Time: 3,456ms | Provider: ollama
    """
    # Build plain-text formatted result (C-04: Zalo = plain text)
    header = f"[Agent: {agent_name}]"

    footer_parts: list[str] = []
    if tokens_used:
        footer_parts.append(f"Tokens: {tokens_used:,}")
    if cost_cents:
        footer_parts.append(f"Cost: ${cost_cents / 100:.2f}")
    if elapsed_ms:
        footer_parts.append(f"Time: {elapsed_ms:,}ms")
    if provider:
        footer_parts.append(f"Provider: {provider}")

    footer = " | ".join(footer_parts) if footer_parts else ""

    # Assemble message
    parts = [header, "", content]
    if footer:
        parts.extend(["", "--- Metrics ---", footer])

    full_text = "\n".join(parts)
    return await _send_zalo_message(user_id, full_text)
