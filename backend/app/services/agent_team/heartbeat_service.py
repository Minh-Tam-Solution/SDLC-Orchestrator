"""Heartbeat Service — Sprint 219 (P6 Agent Liveness).

Redis-based heartbeat tracking for multi-agent conversations.
Each agent records a heartbeat key with TTL; stale agents are
detected via MGET (single round-trip for batch check).

Recovery is idempotent — Redis dedup key prevents duplicate
recovery attempts within 5 minutes.

Key pattern: hb:{agent_id}:{conversation_id} → timestamp JSON
TTL: 60 seconds (configurable via HEARTBEAT_TTL_SECONDS)

References:
- ADR-072, Sprint 219 Track A
- CoPaw heartbeat pattern
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_conversation import AgentConversation
from app.models.agent_message import AgentMessage

logger = logging.getLogger(__name__)

# Defaults (overridable via constructor)
DEFAULT_TTL_SECONDS = 60
RECOVERY_DEDUP_TTL = 300  # 5 minutes — prevents duplicate recovery


def _hb_key(agent_id: UUID, conversation_id: UUID) -> str:
    """Redis key for heartbeat signal."""
    return f"hb:{agent_id}:{conversation_id}"


def _recovery_key(conversation_id: UUID) -> str:
    """Redis key for recovery dedup."""
    return f"hb:recovery:{conversation_id}"


class HeartbeatService:
    """Redis-based agent heartbeat tracking.

    Records, checks, and batch-queries agent liveness.
    Recovery inserts a system message and marks conversation as error,
    with Redis dedup to prevent repeated recovery for same conversation.
    """

    def __init__(
        self,
        db: AsyncSession,
        redis: object | None = None,
        ttl_seconds: int = DEFAULT_TTL_SECONDS,
    ):
        self.db = db
        self.redis = redis
        self.ttl_seconds = ttl_seconds

    async def record_heartbeat(
        self,
        agent_id: UUID,
        conversation_id: UUID,
    ) -> bool:
        """Record a heartbeat for an agent in a conversation.

        Sets a Redis key with TTL. Non-blocking — if Redis is
        unavailable, logs warning and returns False.

        Args:
            agent_id: Agent definition ID.
            conversation_id: Conversation ID.

        Returns:
            True if heartbeat recorded, False if Redis unavailable.
        """
        if self.redis is None:
            return False

        key = _hb_key(agent_id, conversation_id)
        payload = json.dumps({
            "agent_id": str(agent_id),
            "conversation_id": str(conversation_id),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        try:
            await self.redis.setex(key, self.ttl_seconds, payload)
            logger.debug(
                "TRACE_HEARTBEAT: recorded agent=%s conv=%s ttl=%ds",
                agent_id, conversation_id, self.ttl_seconds,
            )
            return True
        except Exception as e:
            logger.warning(
                "TRACE_HEARTBEAT: record failed (non-fatal): agent=%s, error=%s",
                agent_id, e,
            )
            return False

    async def check_liveness(
        self,
        agent_id: UUID,
        conversation_id: UUID,
    ) -> bool:
        """Check if an agent is alive (has unexpired heartbeat).

        Args:
            agent_id: Agent definition ID.
            conversation_id: Conversation ID.

        Returns:
            True if heartbeat exists and not expired, False otherwise.
        """
        if self.redis is None:
            return False

        key = _hb_key(agent_id, conversation_id)
        try:
            data = await self.redis.get(key)
            return data is not None
        except Exception as e:
            logger.warning(
                "TRACE_HEARTBEAT: liveness check failed: agent=%s, error=%s",
                agent_id, e,
            )
            return False

    async def get_stale_agents(
        self,
        agent_conversation_pairs: list[tuple[UUID, UUID]],
    ) -> list[tuple[UUID, UUID]]:
        """Batch-check which agents are stale (no heartbeat).

        Uses MGET for single Redis round-trip — no N+1.

        Args:
            agent_conversation_pairs: List of (agent_id, conversation_id) tuples.

        Returns:
            List of (agent_id, conversation_id) tuples with expired heartbeats.
        """
        if self.redis is None or not agent_conversation_pairs:
            return []

        keys = [
            _hb_key(agent_id, conv_id)
            for agent_id, conv_id in agent_conversation_pairs
        ]

        try:
            values = await self.redis.mget(keys)
            stale = []
            for i, val in enumerate(values):
                if val is None:
                    stale.append(agent_conversation_pairs[i])
            return stale
        except Exception as e:
            logger.warning(
                "TRACE_HEARTBEAT: batch check failed: error=%s", e,
            )
            return []

    async def recover_stale_conversation(
        self,
        conversation_id: UUID,
    ) -> bool:
        """Recover a stale conversation: mark error + insert system message.

        Idempotent — Redis dedup key prevents duplicate recovery for
        5 minutes. Three DB operations: UPDATE conversation status,
        INSERT system message, flush.

        Args:
            conversation_id: Conversation ID to recover.

        Returns:
            True if recovery performed, False if already recovered or skipped.
        """
        # Check Redis dedup key
        if self.redis is not None:
            dedup_key = _recovery_key(conversation_id)
            try:
                existing = await self.redis.get(dedup_key)
                if existing is not None:
                    logger.debug(
                        "TRACE_HEARTBEAT: recovery skipped (dedup): conv=%s",
                        conversation_id,
                    )
                    return False
            except Exception:
                pass  # Redis failure doesn't block recovery

        # 1. UPDATE conversation status to 'error'
        result = await self.db.execute(
            update(AgentConversation)
            .where(
                and_(
                    AgentConversation.id == conversation_id,
                    AgentConversation.status == "active",
                )
            )
            .values(
                status="error",
                completed_at=datetime.now(timezone.utc),
            )
        )

        if result.rowcount == 0:
            logger.debug(
                "TRACE_HEARTBEAT: recovery skipped (not active): conv=%s",
                conversation_id,
            )
            return False

        # 2. INSERT system message
        from uuid import uuid4 as _uuid4
        system_msg = AgentMessage(
            id=_uuid4(),
            conversation_id=conversation_id,
            sender_type="system",
            sender_id="heartbeat_monitor",
            recipient_id=None,
            content="Agent heartbeat expired. Conversation marked as error by liveness monitor.",
            mentions=[],
            metadata_={
                "recovery_reason": "heartbeat_expired",
                "recovered_at": datetime.now(timezone.utc).isoformat(),
            },
            message_type="system",
            queue_mode="queue",
            processing_status="completed",
            processing_lane="main",
            correlation_id=_uuid4(),
        )
        self.db.add(system_msg)
        await self.db.flush()

        # 3. Set Redis dedup key (5 min TTL)
        if self.redis is not None:
            dedup_key = _recovery_key(conversation_id)
            try:
                await self.redis.setex(dedup_key, RECOVERY_DEDUP_TTL, "1")
            except Exception:
                pass  # Non-fatal

        logger.info(
            "TRACE_HEARTBEAT: conversation recovered: conv=%s",
            conversation_id,
        )
        return True

    async def get_active_conversations(self) -> list[tuple[UUID, UUID]]:
        """Get all active conversations with their agent IDs.

        Returns:
            List of (agent_definition_id, conversation_id) tuples.
        """
        result = await self.db.execute(
            select(
                AgentConversation.agent_definition_id,
                AgentConversation.id,
            ).where(AgentConversation.status == "active")
        )
        return [(row[0], row[1]) for row in result.all()]
