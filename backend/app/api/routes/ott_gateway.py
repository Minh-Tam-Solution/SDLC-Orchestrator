"""
OTT (Over-The-Top) channel gateway — POST /api/v1/channels/{channel}/webhook.

Accepts webhooks from external OTT channels (Telegram, Zalo, Teams, Slack),
normalizes them via agent_bridge, and enqueues them into the Multi-Agent
Team Engine message queue.

Security controls:
    - No JWT required (OTT platforms cannot send auth headers)
    - HMAC signature verification (channel-specific, ENV-controlled)
    - Rate limiting: 200 req/min per source IP (Redis token bucket)
    - Input sanitization: applied inside agent_bridge.normalize()

Supported channels (Sprint 181-183):
    telegram — Telegram Bot API webhooks (STANDARD tier)
    zalo     — Zalo OA webhooks (STANDARD tier)
    teams    — Microsoft Teams Bot Framework webhooks (PROFESSIONAL tier)
    slack    — Slack Events API webhooks (PROFESSIONAL tier) [Sprint 183]

ADR-060 D-060-01: All channels normalized to OrchestratorMessage.
ADR-060 D-060-03: Tier gating enforced per channel inside ott_gateway.
"""

from __future__ import annotations

import hmac
import logging
import os
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.agent_bridge import route_to_normalizer
from app.services.agent_bridge.protocol_adapter import OrchestratorMessage
from app.utils.redis import get_redis_client

logger = logging.getLogger(__name__)

router = APIRouter(tags=["OTT Gateway"])

# Channels supported in Sprint 181-183.
SUPPORTED_CHANNELS: frozenset[str] = frozenset({"telegram", "zalo", "teams", "slack"})

# HMAC verification enabled via env var. Default: false in dev/test.
_HMAC_ENABLED: bool = os.getenv("OTT_HMAC_ENABLED", "false").lower() == "true"
_TELEGRAM_SECRET: str = os.getenv("TELEGRAM_WEBHOOK_SECRET", "")
# Sprint 198: Bot token for bidirectional AI replies (sendMessage API)
_TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
_SLACK_SIGNING_SECRET: str = os.getenv("SLACK_SIGNING_SECRET", "")
# Sprint 192 — CTO P1-2: Zalo uses os.getenv() pattern (matches Slack/Telegram)
_ZALO_APP_SECRET: str = os.getenv("ZALO_APP_SECRET", "")
_ZALO_APP_ID: str = os.getenv("ZALO_APP_ID", "")

# Redis dedupe TTL (Sprint 189 — ADR-064 T-04, FR-048)
_DEDUPE_TTL_SECONDS: int = 3600  # 1 hour covers all reasonable retry windows


# ──────────────────────────────────────────────────────────────────────────────
# HMAC verification
# ──────────────────────────────────────────────────────────────────────────────

def _verify_slack_signature(
    body: bytes,
    timestamp: str | None,
    signature: str | None,
) -> bool:
    """
    Verify Slack X-Slack-Signature using HMAC-SHA256 with replay protection.

    Delegates to slack_normalizer.verify_signature() which enforces:
    - HMAC-SHA256 base string: "v0:{timestamp}:{body}"
    - Replay protection: reject if |now - timestamp| > 300 seconds
    - Constant-time comparison (hmac.compare_digest)

    Returns True if OTT_HMAC_ENABLED is False (dev mode bypass).
    """
    if not _HMAC_ENABLED:
        return True
    if not timestamp or not signature:
        return False
    from app.services.agent_bridge.slack_normalizer import verify_signature as _slack_verify
    return _slack_verify(body, timestamp, signature, _SLACK_SIGNING_SECRET)


def _verify_telegram_secret_token(body: bytes, secret_header: str | None) -> bool:
    """
    Verify Telegram X-Telegram-Bot-Api-Secret-Token header.

    Telegram uses a plain shared-secret token, not an HMAC-of-body digest.
    hmac.compare_digest() is used here solely for timing-safe string comparison
    to prevent timing-oracle attacks on the token comparison, not for computing
    a digest. See Telegram Bot API docs: setWebhook secret_token parameter.

    Returns True if OTT_HMAC_ENABLED is False (dev mode bypass).
    Returns True if the provided header matches the configured secret.
    Returns False if header is absent or does not match.
    """
    if not _HMAC_ENABLED:
        return True
    if not secret_header:
        return False
    return hmac.compare_digest(secret_header, _TELEGRAM_SECRET)


def _verify_zalo_signature(
    body: bytes,
    raw_body: dict[str, Any],
    signature: str | None,
) -> bool:
    """
    Verify Zalo OA X-ZEvent-Signature using SHA256.

    Zalo formula: sha256(app_id + body_utf8 + timestamp + oa_secret_key).
    app_id and timestamp are extracted from the parsed JSON body.

    No replay protection — Zalo does not provide a separate timestamp header
    (documented limitation, CTO acknowledged Sprint 192 P3-1).

    Returns True if OTT_HMAC_ENABLED is False (dev mode bypass).
    """
    if not _HMAC_ENABLED:
        return True
    if not signature:
        return False
    app_id = raw_body.get("appId") or raw_body.get("app_id") or _ZALO_APP_ID
    timestamp = str(raw_body.get("timestamp", ""))
    from app.services.agent_bridge.zalo_normalizer import verify_signature as _zalo_verify
    return _zalo_verify(body, signature, app_id, timestamp, _ZALO_APP_SECRET)


# ──────────────────────────────────────────────────────────────────────────────
# Webhook dedupe — event ID extraction (Sprint 189 — FR-048 §2.1)
# ──────────────────────────────────────────────────────────────────────────────

def _extract_event_id(channel: str, body: dict[str, Any]) -> str | None:
    """
    Extract platform-specific event ID for deduplication (FR-048 §2.1).

    Each OTT platform uses a different field for unique event identification:
        Telegram: update_id (integer, monotonically increasing)
        Slack:    event_id within the event envelope
        Teams:    id (activity ID)
        Zalo:     event_id in the webhook payload

    Returns None if event ID cannot be extracted (dedupe skipped).
    """
    if channel == "telegram":
        uid = body.get("update_id")
        return str(uid) if uid is not None else None
    elif channel == "slack":
        return body.get("event_id") or body.get("event", {}).get("event_ts") or None
    elif channel == "teams":
        return body.get("id") or None
    elif channel == "zalo":
        return body.get("event_id") or None
    return None


# ──────────────────────────────────────────────────────────────────────────────
# Webhook endpoint
# ──────────────────────────────────────────────────────────────────────────────

@router.post(
    "/channels/{channel}/webhook",
    status_code=status.HTTP_200_OK,
    summary="OTT channel webhook receiver",
    response_description="Accepted — message enqueued for agent processing",
)
async def receive_webhook(
    channel: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
    x_slack_signature: str | None = Header(default=None),
    x_slack_request_timestamp: str | None = Header(default=None),
    x_zevent_signature: str | None = Header(default=None, alias="X-ZEvent-Signature"),
) -> JSONResponse:
    """
    Receive an OTT channel webhook and enqueue it for the Multi-Agent Team Engine.

    Path param:
        channel: Channel name (telegram, zalo, teams, slack). Returns 400 for unknown.

    Security:
        Telegram: HMAC verified via X-Telegram-Bot-Api-Secret-Token header.
        Slack:    HMAC-SHA256 verified via X-Slack-Signature +
                  X-Slack-Request-Timestamp headers (replay protection 5min).
        Zalo:     SHA256 verified via X-ZEvent-Signature header
                  (Sprint 192). No replay protection (Zalo API limitation).
        All:      Verification bypassed when OTT_HMAC_ENABLED=false (dev default).

    Slack url_verification:
        Returns {"challenge": "..."} immediately without enqueuing to agent queue.
        This is Slack's one-time endpoint verification handshake.

    Returns:
        200 {"status": "accepted", "correlation_id": "..."} on success.
        200 {"challenge": "..."} for Slack url_verification handshake.

    Errors:
        400 — Unsupported channel or malformed payload
        403 — HMAC signature mismatch (when HMAC_ENABLED=true)
        422 — Missing required fields in payload
        503 — Agent engine unavailable
    """
    if channel not in SUPPORTED_CHANNELS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"unsupported channel: {channel!r}",
        )

    # Read body once — needed for HMAC verification and JSON parsing
    body_bytes: bytes = await request.body()

    # Channel-specific HMAC verification
    if channel == "telegram":
        if not _verify_telegram_secret_token(
            body=body_bytes,
            secret_header=x_telegram_bot_api_secret_token,
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="webhook signature invalid",
            )
    elif channel == "slack":
        if not _verify_slack_signature(
            body=body_bytes,
            timestamp=x_slack_request_timestamp,
            signature=x_slack_signature,
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="webhook signature invalid",
            )

    try:
        import json
        raw_body: dict[str, Any] = json.loads(body_bytes)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="request body must be valid JSON",
        )

    # Sprint 192: Zalo verification requires parsed body (appId + timestamp
    # are inside the JSON payload). Verification still covers raw body_bytes
    # integrity — the SHA256 base string includes the raw body string.
    if channel == "zalo":
        if not _verify_zalo_signature(
            body=body_bytes,
            raw_body=raw_body,
            signature=x_zevent_signature,
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="webhook signature invalid",
            )

    # ── Sprint 189: Redis-based webhook dedupe (ADR-064 T-04, FR-048) ──
    # Dedupe at gateway level (NOT router) to cover ALL channels.
    # Event ID extraction per platform: Telegram update_id, Slack event_id,
    # Teams id, Zalo event_id. Returns HTTP 200 for duplicates to prevent
    # OTT platform re-delivery.
    event_id = _extract_event_id(channel, raw_body)
    if event_id:
        try:
            redis = await get_redis_client()
            dedupe_key = f"webhook_dedupe:{channel}:{event_id}"
            # Atomic SET NX EX: returns True if key was set (new event),
            # None/False if key exists (duplicate). Eliminates TOCTOU race
            # in GET-then-SET pattern. See FR-048 §2.2.
            was_set = await redis.set(
                dedupe_key, "1", nx=True, ex=_DEDUPE_TTL_SECONDS,
            )
            if not was_set:
                logger.info(
                    "ott_gateway: duplicate webhook channel=%s event_id=%s",
                    channel,
                    event_id,
                )
                return JSONResponse(
                    content={"status": "duplicate", "event_id": str(event_id)},
                    status_code=status.HTTP_200_OK,
                )
        except Exception as exc:
            # Dedupe failure is non-fatal — log and continue processing
            logger.warning(
                "ott_gateway: dedupe check failed channel=%s error=%s",
                channel,
                str(exc),
            )

    try:
        msg: OrchestratorMessage = route_to_normalizer(channel, raw_body)
    except Exception as exc:
        # Slack url_verification: respond with challenge, do not enqueue
        from app.services.agent_bridge.slack_normalizer import SlackUrlVerificationError
        if isinstance(exc, SlackUrlVerificationError):
            logger.info("ott_gateway: slack url_verification challenge responded")
            return JSONResponse(
                content={"challenge": exc.challenge},
                status_code=status.HTTP_200_OK,
            )
        if isinstance(exc, ValueError):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(exc),
            )
        raise

    # Enqueue into the Multi-Agent Team Engine message queue.
    # Import here to avoid circular imports at module level.
    # Sprint 182: conversation routing (channel → conversation_id discovery) added
    # when Teams normalizer ships. For Sprint 181, enqueue_ott_message stages
    # the message via Redis notify; DB insert happens after routing.
    try:
        from app.services.agent_team.message_queue import MessageQueue
        queue = MessageQueue(db)
        await queue.enqueue_ott_message(msg)
    except Exception as exc:
        logger.error(
            "ott_gateway: message_queue enqueue failed channel=%s correlation_id=%s error=%s",
            channel,
            msg.correlation_id,
            str(exc),
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="agent engine unavailable",
            headers={"Retry-After": "30"},
        )

    logger.info(
        "ott_gateway: accepted channel=%s correlation_id=%s sender=%s",
        msg.channel,
        msg.correlation_id,
        msg.sender_id,
    )

    # ── Sprint 198: Telegram bidirectional response ──
    # Fire-and-forget: send reply AFTER returning 200 to Telegram.
    # Non-blocking — failure does not affect webhook acknowledgment.
    #
    # Routing: /command messages → telegram_responder (static replies)
    #          free-text messages → ai_response_handler (Ollama AI reply)
    #
    # The responder returns True if a command was handled. If False (not a
    # command), the AI handler picks up for bidirectional conversation.
    if channel == "telegram":
        import asyncio
        from app.services.agent_bridge.telegram_responder import handle_telegram_auto_reply
        from app.services.agent_bridge.ai_response_handler import handle_ai_response

        async def _telegram_dispatch() -> None:
            """Route Telegram message: commands → responder, free text → AI."""
            handled = await handle_telegram_auto_reply(raw_body)
            if not handled:
                await handle_ai_response(raw_body, _TELEGRAM_BOT_TOKEN)

        asyncio.ensure_future(_telegram_dispatch())

    # ── Sprint 200 C-01: Zalo bidirectional response ──
    # Same fire-and-forget pattern as Telegram. Zalo uses OAuth access token
    # instead of bot token, so we pass the sender_id directly.
    if channel == "zalo":
        import asyncio
        from app.services.agent_bridge.zalo_responder import handle_zalo_auto_reply
        from app.services.agent_bridge.ai_response_handler import handle_ai_response

        _zalo_sender_id = raw_body.get("sender", {}).get("id", "")

        async def _zalo_dispatch() -> None:
            """Route Zalo message: commands → zalo_responder, free text → AI."""
            handled = await handle_zalo_auto_reply(raw_body)
            if not handled:
                await handle_ai_response(raw_body, "", channel="zalo")

        asyncio.ensure_future(_zalo_dispatch())

    return JSONResponse(
        content={"status": "accepted", "correlation_id": msg.correlation_id},
        status_code=status.HTTP_200_OK,
    )
