"""
OTT Gateway Admin API — Sprint 198 Track A + Sprint 199 Track C

Provides admin-only endpoints for monitoring OTT channels, viewing
conversations, and checking channel health. Data is sourced from
agent_conversations + agent_messages tables filtered by initiator_type='ott_channel'.

Security: requires is_superuser OR is_platform_admin (via require_superuser).
Tier gate: /api/v1/admin → ENTERPRISE (tier=4) in ROUTE_TIER_TABLE.

Endpoints:
    GET  /admin/ott-channels/stats              — Aggregate channel metrics
    GET  /admin/ott-channels/config              — Channel configuration (secrets masked)
    GET  /admin/ott-channels/{channel}/health     — Per-channel health check
    GET  /admin/ott-channels/{channel}/conversations — Paginated conversation list
    POST /admin/ott-channels/{channel}/test-webhook  — Test webhook pipeline (C-03)

ADR-060 D-060-01: All channels normalized to OrchestratorMessage.
Sprint 198: 4 endpoints (A-01, A-02, A-03, A-05). A-04 deferred per ADJ-01.
Sprint 199 C-03: Test-webhook endpoint for pipeline verification.
"""

from __future__ import annotations

import logging
import math
import os
import time
from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select, text
from sqlalchemy.exc import OperationalError as SQLAlchemyOperationalError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db, require_superuser
from app.models.agent_conversation import AgentConversation
from app.models.agent_message import AgentMessage
from app.models.user import User
from app.utils.redis import get_redis_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/ott-channels", tags=["OTT Gateway Admin"])

# Supported channels — mirrors ott_gateway.py SUPPORTED_CHANNELS
SUPPORTED_CHANNELS: frozenset[str] = frozenset({"telegram", "zalo", "teams", "slack"})

# Channel configuration: env var names for each channel
_CHANNEL_CONFIG: dict[str, dict[str, str]] = {
    "telegram": {
        "webhook_secret_env": "TELEGRAM_WEBHOOK_SECRET",
        "bot_token_env": "TELEGRAM_BOT_TOKEN",
        "tier": "STANDARD",
    },
    "zalo": {
        "webhook_secret_env": "ZALO_APP_SECRET",
        "app_id_env": "ZALO_APP_ID",
        "tier": "STANDARD",
    },
    "teams": {
        "webhook_secret_env": "TEAMS_APP_SECRET",
        "tier": "PROFESSIONAL",
    },
    "slack": {
        "webhook_secret_env": "SLACK_SIGNING_SECRET",
        "tier": "PROFESSIONAL",
    },
}


def _mask_secret(value: str) -> str:
    """Mask a secret for safe display: show first 4 and last 4 chars."""
    if not value:
        return ""
    if len(value) <= 8:
        return "****"
    return f"{value[:4]}...{value[-4:]}"


def _channel_status(channel: str) -> str:
    """Determine channel status based on env var configuration."""
    config = _CHANNEL_CONFIG.get(channel, {})
    secret_env = config.get("webhook_secret_env", "")
    secret_value = os.getenv(secret_env, "")

    # Telegram: consider "online" if bot token is set (active bidirectional)
    if channel == "telegram":
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        if bot_token:
            return "online"
        if secret_value:
            return "configured"
        return "offline"

    # Other channels: configured if secret is set
    if secret_value:
        return "configured"
    return "offline"


# ──────────────────────────────────────────────────────────────────────────────
# A-01: GET /admin/ott-channels/stats — Aggregate channel metrics
# ──────────────────────────────────────────────────────────────────────────────

@router.get(
    "/stats",
    summary="OTT channel aggregate statistics",
    response_description="Channel summary with conversation counts and message metrics",
)
async def get_channel_stats(
    admin: User = Depends(require_superuser),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Returns aggregate statistics across all OTT channels:
    - Per-channel conversation count, message count, status
    - Total active conversations
    - Dedup hit rate (from Redis)
    - Last 24h message volume
    """
    try:
        now = datetime.utcnow()
        last_24h = now - timedelta(hours=24)

        channels_stats: list[dict[str, Any]] = []

        for channel in sorted(SUPPORTED_CHANNELS):
            # Count conversations for this channel
            conv_count_q = select(func.count(AgentConversation.id)).where(
                AgentConversation.channel == channel,
                AgentConversation.initiator_type == "ott_channel",
            )
            conv_count_result = await db.execute(conv_count_q)
            conv_count = conv_count_result.scalar() or 0

            # Count active conversations
            active_count_q = select(func.count(AgentConversation.id)).where(
                AgentConversation.channel == channel,
                AgentConversation.initiator_type == "ott_channel",
                AgentConversation.status == "active",
            )
            active_result = await db.execute(active_count_q)
            active_count = active_result.scalar() or 0

            # Count messages in last 24h via join
            msg_24h_q = (
                select(func.count(AgentMessage.id))
                .join(AgentConversation, AgentMessage.conversation_id == AgentConversation.id)
                .where(
                    AgentConversation.channel == channel,
                    AgentConversation.initiator_type == "ott_channel",
                    AgentMessage.created_at >= last_24h,
                )
            )
            msg_24h_result = await db.execute(msg_24h_q)
            msg_24h = msg_24h_result.scalar() or 0

            # Total messages for this channel
            msg_total_q = (
                select(func.count(AgentMessage.id))
                .join(AgentConversation, AgentMessage.conversation_id == AgentConversation.id)
                .where(
                    AgentConversation.channel == channel,
                    AgentConversation.initiator_type == "ott_channel",
                )
            )
            msg_total_result = await db.execute(msg_total_q)
            msg_total = msg_total_result.scalar() or 0

            channels_stats.append({
                "channel": channel,
                "status": _channel_status(channel),
                "tier": _CHANNEL_CONFIG.get(channel, {}).get("tier", "UNKNOWN"),
                "conversations_total": conv_count,
                "conversations_active": active_count,
                "messages_total": msg_total,
                "messages_last_24h": msg_24h,
            })

        # Dedupe stats from Redis
        dedupe_stats: dict[str, int] = {"hits": 0, "keys_active": 0}
        try:
            redis = await get_redis_client()
            dedupe_keys = await redis.keys("webhook_dedupe:*")
            dedupe_stats["keys_active"] = len(dedupe_keys) if dedupe_keys else 0
        except Exception:
            pass  # Redis unavailable — non-fatal for stats

        return {
            "channels": channels_stats,
            "summary": {
                "total_channels": len(SUPPORTED_CHANNELS),
                "online_channels": sum(1 for c in channels_stats if c["status"] == "online"),
                "configured_channels": sum(1 for c in channels_stats if c["status"] in ("online", "configured")),
                "total_conversations": sum(c["conversations_total"] for c in channels_stats),
                "total_messages_24h": sum(c["messages_last_24h"] for c in channels_stats),
            },
            "dedupe": dedupe_stats,
            "generated_at": now.isoformat(),
        }
    except SQLAlchemyOperationalError as exc:
        logger.error("Database unavailable in get_channel_stats: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database temporarily unavailable",
            headers={"Retry-After": "30"},
        )


# ──────────────────────────────────────────────────────────────────────────────
# A-05: GET /admin/ott-channels/config — Channel configuration (secrets masked)
# ──────────────────────────────────────────────────────────────────────────────

@router.get(
    "/config",
    summary="OTT channel configuration",
    response_description="Channel configuration with secrets masked",
)
async def get_channel_config(
    admin: User = Depends(require_superuser),
) -> dict[str, Any]:
    """
    Returns configuration for all OTT channels with secrets masked.
    Useful for verifying which channels are properly configured.
    """
    hmac_enabled = os.getenv("OTT_HMAC_ENABLED", "false").lower() == "true"
    webhook_base = os.getenv(
        "OTT_WEBHOOK_BASE_URL",
        "https://sdlc.nhatquangholding.com/api/v1/channels",
    )

    channels_config: list[dict[str, Any]] = []

    for channel in sorted(SUPPORTED_CHANNELS):
        config = _CHANNEL_CONFIG.get(channel, {})
        secret_env = config.get("webhook_secret_env", "")
        secret_value = os.getenv(secret_env, "")

        channel_info: dict[str, Any] = {
            "channel": channel,
            "status": _channel_status(channel),
            "tier": config.get("tier", "UNKNOWN"),
            "webhook_url": f"{webhook_base}/{channel}/webhook",
            "hmac_enabled": hmac_enabled,
            "secret_configured": bool(secret_value),
            "secret_masked": _mask_secret(secret_value) if secret_value else None,
        }

        # Telegram-specific: bot token status
        if channel == "telegram":
            bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
            channel_info["bot_token_configured"] = bool(bot_token)
            channel_info["bot_token_masked"] = _mask_secret(bot_token) if bot_token else None

        # Zalo-specific: app ID
        if channel == "zalo":
            app_id = os.getenv("ZALO_APP_ID", "")
            channel_info["app_id_configured"] = bool(app_id)
            channel_info["app_id_masked"] = _mask_secret(app_id) if app_id else None

        channels_config.append(channel_info)

    return {
        "channels": channels_config,
        "global": {
            "hmac_enabled": hmac_enabled,
            "webhook_base_url": webhook_base,
            "dedupe_ttl_seconds": 3600,
        },
        "generated_at": datetime.utcnow().isoformat(),
    }


# ──────────────────────────────────────────────────────────────────────────────
# A-02: GET /admin/ott-channels/{channel}/health — Per-channel health check
# ──────────────────────────────────────────────────────────────────────────────

@router.get(
    "/{channel}/health",
    summary="Per-channel health check",
    response_description="Channel health with last webhook time and error metrics",
)
async def get_channel_health(
    channel: str,
    admin: User = Depends(require_superuser),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Returns health status for a specific OTT channel:
    - Last webhook received timestamp
    - Error count in last 24h
    - Average message latency
    - Conversation status breakdown
    """
    if channel not in SUPPORTED_CHANNELS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"unsupported channel: {channel!r}. Valid: {sorted(SUPPORTED_CHANNELS)}",
        )

    try:
        now = datetime.utcnow()
        last_24h = now - timedelta(hours=24)

        # Last message timestamp for this channel
        last_msg_q = (
            select(AgentMessage.created_at)
            .join(AgentConversation, AgentMessage.conversation_id == AgentConversation.id)
            .where(
                AgentConversation.channel == channel,
                AgentConversation.initiator_type == "ott_channel",
            )
            .order_by(AgentMessage.created_at.desc())
            .limit(1)
        )
        last_msg_result = await db.execute(last_msg_q)
        last_msg_row = last_msg_result.first()
        last_webhook_at = last_msg_row[0].isoformat() if last_msg_row else None

        # Error count (messages with processing_status='failed' or 'dead_letter')
        error_count_q = (
            select(func.count(AgentMessage.id))
            .join(AgentConversation, AgentMessage.conversation_id == AgentConversation.id)
            .where(
                AgentConversation.channel == channel,
                AgentConversation.initiator_type == "ott_channel",
                AgentMessage.created_at >= last_24h,
                AgentMessage.processing_status.in_(["failed", "dead_letter"]),
            )
        )
        error_result = await db.execute(error_count_q)
        error_count_24h = error_result.scalar() or 0

        # Average latency for messages with latency_ms recorded
        avg_latency_q = (
            select(func.avg(AgentMessage.latency_ms))
            .join(AgentConversation, AgentMessage.conversation_id == AgentConversation.id)
            .where(
                AgentConversation.channel == channel,
                AgentConversation.initiator_type == "ott_channel",
                AgentMessage.latency_ms.isnot(None),
                AgentMessage.created_at >= last_24h,
            )
        )
        avg_latency_result = await db.execute(avg_latency_q)
        avg_latency_ms = avg_latency_result.scalar()

        # Conversation status breakdown
        status_breakdown_q = (
            select(AgentConversation.status, func.count(AgentConversation.id))
            .where(
                AgentConversation.channel == channel,
                AgentConversation.initiator_type == "ott_channel",
            )
            .group_by(AgentConversation.status)
        )
        status_result = await db.execute(status_breakdown_q)
        status_breakdown = {row[0]: row[1] for row in status_result.all()}

        # Message volume in last 24h
        msg_24h_q = (
            select(func.count(AgentMessage.id))
            .join(AgentConversation, AgentMessage.conversation_id == AgentConversation.id)
            .where(
                AgentConversation.channel == channel,
                AgentConversation.initiator_type == "ott_channel",
                AgentMessage.created_at >= last_24h,
            )
        )
        msg_24h_result = await db.execute(msg_24h_q)
        messages_24h = msg_24h_result.scalar() or 0

        return {
            "channel": channel,
            "status": _channel_status(channel),
            "tier": _CHANNEL_CONFIG.get(channel, {}).get("tier", "UNKNOWN"),
            "health": {
                "last_webhook_at": last_webhook_at,
                "messages_24h": messages_24h,
                "errors_24h": error_count_24h,
                "avg_latency_ms": round(avg_latency_ms, 1) if avg_latency_ms else None,
            },
            "conversations": status_breakdown,
            "checked_at": now.isoformat(),
        }
    except SQLAlchemyOperationalError as exc:
        logger.error("Database unavailable in get_channel_health: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database temporarily unavailable",
            headers={"Retry-After": "30"},
        )


# ──────────────────────────────────────────────────────────────────────────────
# A-03: GET /admin/ott-channels/{channel}/conversations — Paginated list
# ──────────────────────────────────────────────────────────────────────────────

@router.get(
    "/{channel}/conversations",
    summary="Channel conversations (paginated)",
    response_description="Paginated list of conversations for a specific OTT channel",
)
async def get_channel_conversations(
    channel: str,
    admin: User = Depends(require_superuser),
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status_filter: str | None = Query(None, description="Filter by status: active, completed, error"),
) -> dict[str, Any]:
    """
    Returns paginated conversations for a specific OTT channel.
    Each conversation includes sender info, message count, and last message preview.
    """
    if channel not in SUPPORTED_CHANNELS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"unsupported channel: {channel!r}. Valid: {sorted(SUPPORTED_CHANNELS)}",
        )

    try:
        # Base query
        base_q = select(AgentConversation).where(
            AgentConversation.channel == channel,
            AgentConversation.initiator_type == "ott_channel",
        )

        count_q = select(func.count(AgentConversation.id)).where(
            AgentConversation.channel == channel,
            AgentConversation.initiator_type == "ott_channel",
        )

        if status_filter:
            base_q = base_q.where(AgentConversation.status == status_filter)
            count_q = count_q.where(AgentConversation.status == status_filter)

        # Total count
        count_result = await db.execute(count_q)
        total = count_result.scalar() or 0

        # Paginated results (newest first)
        offset = (page - 1) * page_size
        conversations_q = (
            base_q.order_by(AgentConversation.started_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        conversations_result = await db.execute(conversations_q)
        conversations = conversations_result.scalars().all()

        # Build response items with last message preview
        items: list[dict[str, Any]] = []
        for conv in conversations:
            # Get the last message for preview
            last_msg_q = (
                select(AgentMessage.content, AgentMessage.sender_type, AgentMessage.created_at)
                .where(AgentMessage.conversation_id == conv.id)
                .order_by(AgentMessage.created_at.desc())
                .limit(1)
            )
            last_msg_result = await db.execute(last_msg_q)
            last_msg = last_msg_result.first()

            items.append({
                "id": str(conv.id),
                "initiator_id": conv.initiator_id,
                "status": conv.status,
                "total_messages": conv.total_messages,
                "total_tokens": conv.total_tokens,
                "current_cost_cents": conv.current_cost_cents,
                "started_at": conv.started_at.isoformat(),
                "completed_at": conv.completed_at.isoformat() if conv.completed_at else None,
                "last_message": {
                    "content": last_msg[0][:200] if last_msg else None,  # Preview (200 chars max)
                    "sender_type": last_msg[1] if last_msg else None,
                    "created_at": last_msg[2].isoformat() if last_msg else None,
                } if last_msg else None,
            })

        pages = math.ceil(total / page_size) if total > 0 else 0

        return {
            "channel": channel,
            "items": items,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "pages": pages,
            },
        }
    except SQLAlchemyOperationalError as exc:
        logger.error("Database unavailable in get_channel_conversations: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database temporarily unavailable",
            headers={"Retry-After": "30"},
        )


# ──────────────────────────────────────────────────────────────────────────────
# C-03: POST /admin/ott-channels/{channel}/test-webhook — Pipeline test
# ──────────────────────────────────────────────────────────────────────────────

# Synthetic test payloads per channel (minimal valid structure)
_TEST_PAYLOADS: dict[str, dict[str, Any]] = {
    "telegram": {
        "update_id": 0,
        "message": {
            "message_id": 0,
            "from": {"id": 0, "is_bot": False, "first_name": "TestWebhook"},
            "chat": {"id": 0, "type": "private"},
            "date": 0,
            "text": "[test-webhook] Pipeline verification",
        },
    },
    "zalo": {
        "app_id": "test",
        "event_name": "user_send_text",
        "timestamp": "0",
        "sender": {"id": "0"},
        "message": {"text": "[test-webhook] Pipeline verification", "msg_id": "0"},
    },
    "teams": {
        "type": "message",
        "id": "test-0",
        "timestamp": "2026-01-01T00:00:00Z",
        "from": {"id": "test-user", "name": "TestWebhook"},
        "conversation": {"id": "test-conv"},
        "text": "[test-webhook] Pipeline verification",
    },
    "slack": {
        "event_id": "test-0",
        "type": "event_callback",
        "event": {
            "type": "message",
            "user": "U0TEST",
            "text": "[test-webhook] Pipeline verification",
            "ts": "0",
            "channel": "C0TEST",
        },
    },
}


@router.post(
    "/{channel}/test-webhook",
    summary="Test webhook pipeline",
    response_description="Pipeline test result with normalization status and timing",
)
async def test_webhook(
    channel: str,
    admin: User = Depends(require_superuser),
) -> dict[str, Any]:
    """
    Send a synthetic test payload through the channel normalizer pipeline
    to verify the webhook processing chain works end-to-end.

    Sprint 199 C-03 (deferred from Sprint 198 A-04).

    Does NOT deliver the message to agents — only tests normalization.
    The synthetic payload uses id=0 and [test-webhook] prefix to avoid
    confusion with real messages in logs.
    """
    if channel not in SUPPORTED_CHANNELS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"unsupported channel: {channel!r}. Valid: {sorted(SUPPORTED_CHANNELS)}",
        )

    test_payload = _TEST_PAYLOADS.get(channel)
    if not test_payload:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=f"test payload not available for channel: {channel}",
        )

    from app.services.agent_bridge import route_to_normalizer

    start_ns = time.monotonic_ns()
    try:
        normalized = route_to_normalizer(channel, test_payload)
        elapsed_ms = (time.monotonic_ns() - start_ns) / 1_000_000

        return {
            "channel": channel,
            "status": "ok",
            "normalization": {
                "success": True,
                "sender_id": normalized.sender_id,
                "content_length": len(normalized.content or ""),
                "correlation_id": normalized.correlation_id,
            },
            "pipeline": {
                "channel_status": _channel_status(channel),
                "hmac_enabled": os.getenv("OTT_HMAC_ENABLED", "false").lower() == "true",
            },
            "timing_ms": round(elapsed_ms, 2),
            "tested_at": datetime.utcnow().isoformat(),
        }
    except Exception as exc:
        elapsed_ms = (time.monotonic_ns() - start_ns) / 1_000_000
        logger.warning(
            "test_webhook: pipeline test failed channel=%s error=%s",
            channel,
            str(exc),
        )
        return {
            "channel": channel,
            "status": "error",
            "normalization": {
                "success": False,
                "error": str(exc),
            },
            "pipeline": {
                "channel_status": _channel_status(channel),
                "hmac_enabled": os.getenv("OTT_HMAC_ENABLED", "false").lower() == "true",
            },
            "timing_ms": round(elapsed_ms, 2),
            "tested_at": datetime.utcnow().isoformat(),
        }
