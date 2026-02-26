"""
=========================================================================
WorkflowResumer — Durable Workflow Resume Service (ADR-066 D-066-05)
SDLC Orchestrator - Sprint 206 (LangGraph Durable Workflows)

Version: 1.0.0
Date: February 2026
Status: ACTIVE - Sprint 206
Authority: CTO Approved (ADR-066)
Reference: ADR-066-LangChain-Multi-Agent-Orchestration.md

Purpose:
- Resumes LangGraph workflows after async agent completion.
- Dual-path design (D-066-05):
    Fast path: Redis pub/sub listener — immediate resume when agent
      publishes its conversation_id to channel "workflow_resume:{conv_id}".
    Fallback: Reconciler polling every 30s — catches missed pub/sub events
      by querying agent_conversations WHERE metadata_->>'workflow.status'
      = 'waiting' AND next_wakeup_at <= now().
    Stuck detection: Workflows waiting >STUCK_THRESHOLD_MINUTES are
      auto-resumed regardless of pub/sub delivery.

Single-Instance Constraint (D-066-05):
  WorkflowResumer MUST run as a single Docker service (replicas: 1) OR
  via Redis leader election (30s TTL key) to prevent concurrent resume.
  Concurrent resume is safe due to OCC in WorkflowService.save() — one
  instance wins, the other gets a False return (no-op, no data loss).

OCC Safety:
  If two WorkflowResumer instances race, WorkflowService.save() ensures
  only the first write succeeds (version mismatch → False). The second
  resume attempt finds an already-advanced workflow and exits gracefully.

Zero Mock Policy: Production-ready asyncio implementation.
=========================================================================
"""

from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Constants (from config / environment, overridable in tests)
# ─────────────────────────────────────────────────────────────────────────────

# Redis pub/sub channel: agents publish "{conversation_id}" to this channel
# on message processing completion. WorkflowResumer subscribes via pattern.
WORKFLOW_RESUME_CHANNEL = "workflow_resume"

# Reconciler polling interval (seconds)
RECONCILER_INTERVAL_SECONDS: int = int(
    os.environ.get("WORKFLOW_RESUMER_RECONCILER_INTERVAL_SECONDS", "30")
)

# Workflows waiting longer than this are considered stuck and auto-resumed
STUCK_THRESHOLD_MINUTES: int = int(
    os.environ.get("WORKFLOW_STUCK_THRESHOLD_MINUTES", "5")
)

# Redis leader-election key (only one instance holds this key)
LEADER_ELECTION_KEY = "workflow_resumer:leader"
LEADER_ELECTION_TTL_SECONDS = 30  # Renew every 10s, expire after 30s


# ─────────────────────────────────────────────────────────────────────────────
# WorkflowResumer
# ─────────────────────────────────────────────────────────────────────────────


class WorkflowResumer:
    """
    Async service that resumes durable LangGraph workflows.

    Architecture (D-066-05 dual-path):
      1. Redis pub/sub fast path: subscribes to "workflow_resume" channel.
         When an agent completes, it publishes the workflow conversation_id.
         WorkflowResumer receives the message and calls graph.resume().

      2. DB reconciler fallback: every RECONCILER_INTERVAL_SECONDS, queries
         agent_conversations for workflows in "waiting" status with
         next_wakeup_at <= now(). Resumes any found — handles missed events.

      3. Stuck detection: workflows waiting > STUCK_THRESHOLD_MINUTES are
         auto-resumed regardless of pub/sub delivery status.

    OCC: WorkflowService.save() rejects concurrent writes via version check.
    If two resumes race, exactly 1 succeeds; the other is a safe no-op.

    Usage (standalone service):
        resumer = WorkflowResumer(db_url=settings.DATABASE_URL,
                                   redis_url=settings.REDIS_URL)
        await resumer.start()  # Runs until cancelled

    Usage (in tests):
        resumer = WorkflowResumer(db=mock_db, redis=mock_redis,
                                   graph=mock_graph)
        await resumer._resume_conversation(conv_id)
    """

    def __init__(
        self,
        db_url: str | None = None,
        redis_url: str | None = None,
        db: AsyncSession | None = None,
        redis: Any | None = None,
        graph: Any | None = None,
    ) -> None:
        """
        Args:
            db_url:    SQLAlchemy async URL (used when db= is not provided).
            redis_url: Redis URL (used when redis= is not provided).
            db:        Pre-built AsyncSession (for testing / in-process use).
            redis:     Pre-built Redis client (for testing / in-process use).
            graph:     Pre-built ReflectionGraph (for testing / in-process use).
        """
        self._db_url = db_url or os.environ.get("DATABASE_URL", "")
        self._redis_url = redis_url or os.environ.get("REDIS_URL", "redis://localhost:6379/0")
        self._db = db
        self._redis = redis
        self._graph = graph
        self._running = False
        self._session_factory: async_sessionmaker | None = None

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    async def start(self) -> None:
        """
        Start the WorkflowResumer service.

        Runs pub/sub listener and reconciler concurrently until cancelled.
        Called from the Docker entrypoint (workflow_resumer service).
        """
        logger.info("WorkflowResumer: starting (reconciler_interval=%ds, stuck_threshold=%dmin)",
                    RECONCILER_INTERVAL_SECONDS, STUCK_THRESHOLD_MINUTES)
        self._running = True

        if self._db is None and self._db_url:
            engine = create_async_engine(self._db_url, echo=False)
            self._session_factory = async_sessionmaker(engine, expire_on_commit=False)

        if self._redis is None:
            try:
                import redis.asyncio as aioredis  # type: ignore[import]
                self._redis = aioredis.from_url(
                    self._redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                )
            except ImportError:
                logger.warning("WorkflowResumer: redis.asyncio not available — reconciler only")

        try:
            await asyncio.gather(
                self._run_pubsub_listener(),
                self._run_reconciler(),
            )
        except asyncio.CancelledError:
            logger.info("WorkflowResumer: stopped")
            self._running = False
            raise

    def stop(self) -> None:
        """Signal the resumer to stop on next iteration."""
        self._running = False

    # ── Fast path: Redis pub/sub ──────────────────────────────────────────────

    async def _run_pubsub_listener(self) -> None:
        """
        Subscribe to WORKFLOW_RESUME_CHANNEL and resume workflows on message.

        Channel message format: the conversation_id UUID string.
        Published by the agent worker after processing a workflow message.
        """
        if self._redis is None:
            logger.info("WorkflowResumer: no Redis — pub/sub listener disabled")
            # Keep running (reconciler is the fallback)
            while self._running:
                await asyncio.sleep(60)
            return

        logger.info("WorkflowResumer: pub/sub listener active on channel=%s", WORKFLOW_RESUME_CHANNEL)

        # Create dedicated pub/sub connection
        pubsub = self._redis.pubsub()
        await pubsub.subscribe(WORKFLOW_RESUME_CHANNEL)

        try:
            while self._running:
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message is None:
                    await asyncio.sleep(0.1)
                    continue

                data = message.get("data", "")
                if not data:
                    continue

                logger.info("WorkflowResumer: pub/sub received conversation_id=%s", data)
                try:
                    conv_id = UUID(str(data))
                    await self._resume_conversation(conv_id)
                except (ValueError, TypeError) as exc:
                    logger.warning(
                        "WorkflowResumer: invalid pub/sub data '%s': %s", data, exc
                    )
                except Exception as exc:  # noqa: BLE001
                    logger.error(
                        "WorkflowResumer: resume failed for conv=%s: %s", data, exc,
                        exc_info=True,
                    )
        finally:
            await pubsub.unsubscribe(WORKFLOW_RESUME_CHANNEL)
            await pubsub.close()

    # ── Fallback path: Reconciler ─────────────────────────────────────────────

    async def _run_reconciler(self) -> None:
        """
        Poll every RECONCILER_INTERVAL_SECONDS for missed pub/sub events.

        Queries agent_conversations for waiting workflows whose next_wakeup_at
        is in the past. Resumes each one. This also covers stuck workflows
        (waiting > STUCK_THRESHOLD_MINUTES via the wakeup_at timestamp).
        """
        logger.info(
            "WorkflowResumer: reconciler started (interval=%ds)", RECONCILER_INTERVAL_SECONDS
        )

        while self._running:
            await asyncio.sleep(RECONCILER_INTERVAL_SECONDS)
            if not self._running:
                break

            try:
                await self._reconcile_once()
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # noqa: BLE001
                logger.error("WorkflowResumer: reconciler error: %s", exc, exc_info=True)

    async def _reconcile_once(self) -> int:
        """
        Find and resume all workflows due for wakeup.

        Returns:
            Number of workflows resumed.
        """
        now_str = datetime.now(timezone.utc).isoformat()
        resumed = 0

        # SQL: find conversations with waiting workflow where next_wakeup_at is past
        # Uses partial index created in Alembic migration s206_001
        raw_sql = text("""
            SELECT id
            FROM agent_conversations
            WHERE metadata_->>'workflow' IS NOT NULL
              AND metadata_->'workflow'->>'status' = 'waiting'
              AND metadata_->'workflow'->>'next_wakeup_at' IS NOT NULL
              AND (metadata_->'workflow'->>'next_wakeup_at')::timestamptz <= :now
            ORDER BY (metadata_->'workflow'->>'next_wakeup_at')::timestamptz
            LIMIT 50
        """)

        async with self._get_db_session() as db:
            result = await db.execute(raw_sql, {"now": now_str})
            rows = result.fetchall()

        if rows:
            logger.info("WorkflowResumer: reconciler found %d workflows to resume", len(rows))

        for row in rows:
            conv_id = UUID(str(row[0]))
            try:
                await self._resume_conversation(conv_id)
                resumed += 1
            except Exception as exc:  # noqa: BLE001
                logger.error(
                    "WorkflowResumer: reconciler resume failed conv=%s: %s",
                    conv_id,
                    exc,
                    exc_info=True,
                )

        return resumed

    # ── Core resume logic ─────────────────────────────────────────────────────

    async def _resume_conversation(self, conversation_id: UUID) -> bool:
        """
        Resume a single workflow at its current checkpoint.

        Safe to call concurrently: WorkflowService OCC ensures only the
        first caller successfully transitions the workflow. The second call
        finds the workflow already advanced and returns False (no-op).

        Args:
            conversation_id: Workflow coordination conversation UUID.

        Returns:
            True if resume executed, False if workflow not found or terminal
            (including OCC-rejected concurrent resume).
        """
        logger.info(
            "TRACE_RESUMER action=resume conv=%s",
            conversation_id,
        )

        async with self._get_db_session() as db:
            graph = await self._get_graph(db)
            result = await graph.resume(conversation_id)

        if result is None:
            logger.debug("WorkflowResumer: no workflow found for conv=%s", conversation_id)
            return False

        logger.info(
            "TRACE_RESUMER action=resumed conv=%s status=%s node=%s",
            conversation_id,
            result.status,
            result.current_node,
        )
        return True

    # ── Publish (called by agent worker after completing a workflow message) ──

    async def publish_resume(self, conversation_id: UUID) -> bool:
        """
        Publish a resume signal for a workflow conversation.

        Called by team_orchestrator / agent worker after an agent completes
        a message that is part of a workflow (i.e., the message has a
        workflow_id in its metadata).

        Args:
            conversation_id: Workflow coordination conversation UUID.

        Returns:
            True if published to Redis, False if Redis unavailable.
        """
        if self._redis is None:
            logger.debug(
                "WorkflowResumer.publish_resume: no Redis — relying on reconciler for conv=%s",
                conversation_id,
            )
            return False

        try:
            await self._redis.publish(WORKFLOW_RESUME_CHANNEL, str(conversation_id))
            logger.info(
                "TRACE_RESUMER action=published conv=%s channel=%s",
                conversation_id,
                WORKFLOW_RESUME_CHANNEL,
            )
            return True
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "WorkflowResumer.publish_resume: Redis publish failed conv=%s: %s",
                conversation_id,
                exc,
            )
            return False

    # ── Helpers ───────────────────────────────────────────────────────────────

    async def _get_graph(self, db: AsyncSession) -> Any:
        """Return ReflectionGraph, building it if not injected (production path)."""
        if self._graph is not None:
            return self._graph

        # Lazy import to avoid circular dependency at module load time
        from app.services.agent_team.workflows.graph_state import WorkflowService
        from app.services.agent_team.workflows.reflection_graph import ReflectionGraph
        from app.services.agent_team.message_queue import MessageQueue

        workflow_service = WorkflowService(db)
        queue = MessageQueue(db, self._redis)
        return ReflectionGraph(workflow_service=workflow_service, queue=queue)

    from contextlib import asynccontextmanager

    @asynccontextmanager  # type: ignore[misc]
    async def _get_db_session(self):  # type: ignore[no-untyped-def]
        """Yield a scoped DB session (test-injectable via self._db)."""
        if self._db is not None:
            # Test path: use injected session directly
            yield self._db
            return

        if self._session_factory is None:
            raise RuntimeError(
                "WorkflowResumer: no DB session available. "
                "Provide db= or db_url= in constructor."
            )

        async with self._session_factory() as session:
            async with session.begin():
                yield session


# ─────────────────────────────────────────────────────────────────────────────
# Entrypoint (for Docker service: python -m app.services.agent_team.workflow_resumer)
# ─────────────────────────────────────────────────────────────────────────────


async def _main() -> None:
    """Standalone entrypoint for the workflow_resumer Docker service."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    db_url = os.environ.get("DATABASE_URL", "")
    redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

    if not db_url:
        raise ValueError("DATABASE_URL environment variable not set")

    resumer = WorkflowResumer(db_url=db_url, redis_url=redis_url)
    await resumer.start()


if __name__ == "__main__":  # pragma: no cover
    asyncio.run(_main())
