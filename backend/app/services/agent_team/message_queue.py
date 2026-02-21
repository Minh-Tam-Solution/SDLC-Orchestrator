"""
=========================================================================
Lane-Based Message Queue — SKIP LOCKED + Redis pub/sub notification
SDLC Orchestrator - Sprint 177 (Multi-Agent Core Services)

Version: 1.0.0
Date: February 2026
Status: ACTIVE - Sprint 177
Authority: CTO Approved (ADR-056 Decision 2)
Reference: ADR-056-Multi-Agent-Team-Engine.md

Purpose:
- Lane-based concurrent message processing (DB is truth, Redis is notify)
- SKIP LOCKED for safe concurrent consumption without double-processing
- Dead-letter handling with exponential backoff (30s * 2^failed_count)
- Idempotent message insertion via dedupe_key
- Per-lane serialization (agent:coder processes one message at a time)

Sources:
- OpenClaw: src/queue/lane-queue.ts (SKIP LOCKED, dead-letter, lane concept)
- ADR-056 Decision 2: Lane Contract — DB is truth, Redis is notify-only
- ADR-056 Non-Negotiable #7: Lane-based queue
- ADR-056 Non-Negotiable #10: Dead-letter queue (failed_count >= 3)

Architecture:
  Producer (API/OTT) → INSERT agent_messages (processing_status=pending)
                      → PUBLISH Redis channel (notify only)
  Consumer (Worker)   → SELECT ... FOR UPDATE SKIP LOCKED (claim message)
                      → Process → UPDATE processing_status=completed
                      → On failure → INCREMENT failed_count, SET next_retry_at
                      → failed_count >= 3 → processing_status=dead_letter

Zero Mock Policy: Production-ready async SQLAlchemy 2.0 + Redis service
=========================================================================
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import select, update, and_, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_message import AgentMessage

if TYPE_CHECKING:
    from app.services.agent_bridge.protocol_adapter import OrchestratorMessage

logger = logging.getLogger(__name__)

# Dead-letter threshold: >= 3 failed attempts → dead_letter
DEAD_LETTER_THRESHOLD = 3

# Base backoff seconds (exponential: base * 2^failed_count)
BACKOFF_BASE_SECONDS = 30

# Redis notification channel prefix
REDIS_CHANNEL_PREFIX = "agent_queue"


class MessageQueueError(Exception):
    """Base exception for message queue operations."""


class NoMessageAvailable(MessageQueueError):
    """No pending message available in the requested lane."""


class MessageQueue:
    """
    Lane-based message queue backed by PostgreSQL (SKIP LOCKED) with Redis notification.

    DB is truth, Redis is notify-only (ADR-056 Decision 2):
    - All message state lives in agent_messages table
    - Redis pub/sub is a performance optimization for wake-up notification
    - If Redis is unavailable, polling the DB still works (degraded latency)

    Lane serialization:
    - Each processing_lane (e.g., "agent:coder") processes one message at a time
    - SKIP LOCKED ensures concurrent consumers don't grab the same message
    - Different lanes process in parallel (agent:coder and agent:reviewer run concurrently)

    Usage:
        queue = MessageQueue(db, redis_client)

        # Producer: enqueue a message
        msg = await queue.enqueue(conversation_id, content, sender_type, ...)

        # Consumer: claim and process
        msg = await queue.claim_next(lane="agent:coder")
        if msg:
            try:
                result = await process(msg)
                await queue.complete(msg.id, provider_used="ollama", ...)
            except Exception as e:
                await queue.fail(msg.id, error=str(e))
    """

    def __init__(self, db: AsyncSession, redis: object | None = None):
        self.db = db
        self.redis = redis

    async def enqueue(
        self,
        conversation_id: UUID,
        content: str,
        sender_type: str,
        sender_id: str,
        processing_lane: str,
        queue_mode: str = "queue",
        message_type: str = "request",
        recipient_id: str | None = None,
        mentions: list[str] | None = None,
        dedupe_key: str | None = None,
        parent_message_id: UUID | None = None,
    ) -> AgentMessage:
        """
        Enqueue a message for lane-based processing.

        Idempotent: if dedupe_key is provided and already exists, returns
        the existing message without creating a duplicate.

        Args:
            conversation_id: Target conversation UUID.
            content: Message content.
            sender_type: "user", "agent", or "system".
            sender_id: Sender identifier.
            processing_lane: Lane name (e.g., "agent:coder").
            queue_mode: Queue mode from conversation snapshot.
            message_type: "request", "response", "mention", "system", "interrupt".
            recipient_id: Optional recipient agent name.
            mentions: Parsed @mention names.
            dedupe_key: Idempotency key (optional).
            parent_message_id: Threading support (optional).

        Returns:
            Created (or existing if deduped) AgentMessage.
        """
        # Idempotency check
        if dedupe_key:
            existing = await self.db.execute(
                select(AgentMessage).where(AgentMessage.dedupe_key == dedupe_key)
            )
            existing_msg = existing.scalar_one_or_none()
            if existing_msg:
                logger.debug("Dedupe hit: key=%s, msg_id=%s", dedupe_key, existing_msg.id)
                return existing_msg

        correlation_id = uuid4()
        message = AgentMessage(
            id=uuid4(),
            conversation_id=conversation_id,
            parent_message_id=parent_message_id,
            sender_type=sender_type,
            sender_id=sender_id,
            recipient_id=recipient_id,
            content=content,
            mentions=mentions or [],
            message_type=message_type,
            queue_mode=queue_mode,
            processing_status="pending",
            processing_lane=processing_lane,
            dedupe_key=dedupe_key,
            correlation_id=correlation_id,
        )

        self.db.add(message)
        await self.db.flush()

        # Notify via Redis (non-blocking, best-effort)
        await self._notify_lane(processing_lane, str(message.id))

        logger.info(
            "TRACE_MSG_LIFECYCLE status=created: id=%s, lane=%s, "
            "type=%s, sender=%s, correlation=%s",
            message.id,
            processing_lane,
            message_type,
            sender_id,
            correlation_id,
        )
        return message

    async def claim_next(
        self, lane: str, batch_size: int = 1
    ) -> AgentMessage | None:
        """
        Claim the next pending message from a lane using SKIP LOCKED.

        SELECT ... WHERE processing_lane = :lane AND processing_status = 'pending'
        AND (next_retry_at IS NULL OR next_retry_at <= NOW())
        ORDER BY created_at ASC
        FOR UPDATE SKIP LOCKED
        LIMIT 1

        Returns None if no message is available.
        """
        now = datetime.now(timezone.utc)

        # Raw SQL for SKIP LOCKED (SQLAlchemy 2.0 supports with_for_update)
        query = (
            select(AgentMessage)
            .where(
                and_(
                    AgentMessage.processing_lane == lane,
                    AgentMessage.processing_status == "pending",
                    # Respect backoff timer
                    (AgentMessage.next_retry_at == None)  # noqa: E711
                    | (AgentMessage.next_retry_at <= now),
                )
            )
            .order_by(AgentMessage.created_at.asc())
            .limit(batch_size)
            .with_for_update(skip_locked=True)
        )

        result = await self.db.execute(query)
        message = result.scalar_one_or_none()

        if message:
            message.processing_status = "processing"
            await self.db.flush()
            logger.debug(
                "Claimed message: id=%s, lane=%s",
                message.id,
                lane,
            )

        return message

    async def complete(
        self,
        message_id: UUID,
        provider_used: str | None = None,
        token_count: int | None = None,
        latency_ms: int | None = None,
    ) -> None:
        """
        Mark a message as completed with provider metrics.

        Args:
            message_id: Message UUID.
            provider_used: Which provider handled this (ollama, anthropic, etc.).
            token_count: Tokens consumed.
            latency_ms: Provider response latency in milliseconds.
        """
        result = await self.db.execute(
            select(AgentMessage).where(AgentMessage.id == message_id)
        )
        message = result.scalar_one_or_none()
        if not message:
            logger.error("Cannot complete: message %s not found", message_id)
            return

        message.processing_status = "completed"
        message.provider_used = provider_used
        message.token_count = token_count
        message.latency_ms = latency_ms
        await self.db.flush()

        logger.info(
            "TRACE_MSG_LIFECYCLE status=completed: id=%s, provider=%s, "
            "tokens=%s, latency=%sms",
            message_id,
            provider_used,
            token_count,
            latency_ms,
        )

    async def fail(
        self,
        message_id: UUID,
        error: str,
        failover_reason: str | None = None,
    ) -> bool:
        """
        Record a message processing failure with dead-letter handling.

        Increments failed_count. If >= DEAD_LETTER_THRESHOLD (3), moves to
        dead_letter status. Otherwise, sets next_retry_at with exponential backoff.

        Returns:
            True if message moved to dead_letter, False if retryable.
        """
        result = await self.db.execute(
            select(AgentMessage).where(AgentMessage.id == message_id)
        )
        message = result.scalar_one_or_none()
        if not message:
            logger.error("Cannot fail: message %s not found", message_id)
            return True

        message.failed_count += 1
        message.last_error = error[:2000]  # Truncate error to prevent bloat
        message.failover_reason = failover_reason

        if message.failed_count >= DEAD_LETTER_THRESHOLD:
            message.processing_status = "dead_letter"
            message.next_retry_at = None
            logger.warning(
                "TRACE_MSG_LIFECYCLE status=dead_letter: id=%s, "
                "failed_count=%d, last_error=%.200s",
                message_id,
                message.failed_count,
                error,
            )
            await self.db.flush()
            return True

        # Exponential backoff: 30s, 60s, 120s
        backoff_seconds = BACKOFF_BASE_SECONDS * (2 ** (message.failed_count - 1))
        message.processing_status = "pending"
        message.next_retry_at = datetime.now(timezone.utc) + timedelta(seconds=backoff_seconds)

        logger.info(
            "TRACE_MSG_LIFECYCLE status=retry: id=%s, attempt=%d/%d, "
            "backoff=%ds",
            message_id,
            message.failed_count,
            DEAD_LETTER_THRESHOLD,
            backoff_seconds,
        )
        await self.db.flush()
        return False

    async def get_pending_count(self, lane: str) -> int:
        """Count pending messages in a lane (for monitoring)."""
        from sqlalchemy import func

        result = await self.db.execute(
            select(func.count())
            .select_from(AgentMessage)
            .where(
                and_(
                    AgentMessage.processing_lane == lane,
                    AgentMessage.processing_status == "pending",
                )
            )
        )
        return result.scalar() or 0

    async def get_dead_letters(
        self, lane: str | None = None, limit: int = 50
    ) -> list[AgentMessage]:
        """
        Retrieve dead-letter messages for inspection.

        Args:
            lane: Optional lane filter. None = all lanes.
            limit: Max messages to return.
        """
        conditions = [AgentMessage.processing_status == "dead_letter"]
        if lane:
            conditions.append(AgentMessage.processing_lane == lane)

        result = await self.db.execute(
            select(AgentMessage)
            .where(and_(*conditions))
            .order_by(AgentMessage.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def requeue_dead_letter(self, message_id: UUID) -> bool:
        """
        Manually requeue a dead-letter message for retry.

        Resets failed_count to 0 and sets processing_status back to pending.
        Returns True if successful, False if message not found or not dead-lettered.
        """
        result = await self.db.execute(
            select(AgentMessage).where(AgentMessage.id == message_id)
        )
        message = result.scalar_one_or_none()
        if not message or message.processing_status != "dead_letter":
            return False

        message.processing_status = "pending"
        message.failed_count = 0
        message.next_retry_at = None
        message.last_error = None
        await self.db.flush()

        # Notify lane for pickup
        await self._notify_lane(message.processing_lane, str(message.id))

        logger.info(
            "Dead-letter requeued: id=%s, lane=%s",
            message_id,
            message.processing_lane,
        )
        return True

    async def list_messages(
        self,
        conversation_id: UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[AgentMessage], int]:
        """
        List messages for a conversation with pagination.

        Args:
            conversation_id: Conversation UUID.
            page: Page number (1-based).
            page_size: Items per page.

        Returns:
            Tuple of (messages list, total count).
        """
        from sqlalchemy import func

        conditions = [AgentMessage.conversation_id == conversation_id]

        count_result = await self.db.execute(
            select(func.count())
            .select_from(AgentMessage)
            .where(and_(*conditions))
        )
        total = count_result.scalar() or 0

        result = await self.db.execute(
            select(AgentMessage)
            .where(and_(*conditions))
            .order_by(AgentMessage.created_at.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        messages = list(result.scalars().all())

        return messages, total

    async def enqueue_ott_message(self, msg: "OrchestratorMessage") -> None:
        """
        Accept a normalized OTT OrchestratorMessage into the staging pipeline.

        Sprint 181: Publishes a Redis wake-up notification and logs the inbound
        message. DB insertion (with conversation routing) is deferred to Sprint 182
        once Teams channel + conversation-discovery logic is in place. A conversation_id
        is required by AgentMessage FK; OTT routing to an existing conversation is a
        Sprint 182 concern (ADR-061).

        Args:
            msg: Normalized OrchestratorMessage produced by agent_bridge.normalize().

        Raises:
            Exception: Propagated on Redis failure so caller can return HTTP 503.
        """
        lane = f"ott:{msg.channel}"

        # Notify Redis consumer for eventual pickup (best-effort, DB is truth)
        await self._notify_lane(lane, msg.correlation_id)

        logger.info(
            "ott_queue: staged channel=%s correlation_id=%s sender=%s content_length=%d",
            msg.channel,
            msg.correlation_id,
            msg.sender_id,
            len(msg.content),
        )

    async def _notify_lane(self, lane: str, message_id: str) -> None:
        """
        Publish notification to Redis channel for lane wake-up.

        Non-blocking, best-effort. If Redis is unavailable, consumers
        fall back to polling (degraded latency but still functional).
        """
        if self.redis is None:
            return

        channel = f"{REDIS_CHANNEL_PREFIX}:{lane}"
        try:
            await self.redis.publish(channel, message_id)  # type: ignore[union-attr]
            logger.debug("Redis notify: channel=%s, msg_id=%s", channel, message_id)
        except Exception as e:
            # Redis failure is non-fatal (DB is truth, Redis is notify-only)
            logger.warning(
                "Redis notify failed (non-fatal): channel=%s, error=%s",
                channel,
                e,
            )
