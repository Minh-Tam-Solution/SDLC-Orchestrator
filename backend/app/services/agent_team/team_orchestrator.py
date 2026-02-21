"""
=========================================================================
Team Orchestrator — Central processing loop for Multi-Agent Team Engine
SDLC Orchestrator - Sprint 178 (Team Orchestrator + Evidence + Traces)

Version: 1.0.0
Date: 2026-02-18
Status: ACTIVE - Sprint 178
Authority: CTO Approved (ADR-056, EP-07)
Reference: ADR-056-Multi-Agent-Team-Engine.md
Reference: EP-07-Multi-Agent-Team-Engine.md

Purpose:
- Central coordination of message processing across all services
- Lane-based message claim → invoke → complete → evidence cycle
- Queue mode routing: queue (FIFO), steer (out-of-order), interrupt (pause)
- Integrates: MessageQueue + ConversationTracker + AgentRegistry +
  AgentInvoker + MentionParser + EvidenceCollector

Processing Flow (process_next):
  1. Claim next pending message from lane (SKIP LOCKED)
  2. Load conversation (check active + not paused_by_human)
  3. Check limits (message count + budget)
  4. Load agent definition from conversation's agent_definition_id
  5. Parse @mentions in message content
  6. Build LLM context (system prompt + conversation history)
  7. Build provider chain (from definition config)
  8. Invoke provider (with failover)
  9. Record response: complete message, record tokens, enqueue response
  10. Capture evidence (if agent output)
  11. Route @mentions (enqueue messages to mentioned agents)
  12. Return ProcessingResult

Queue Modes:
  - queue: Default FIFO processing via process_next(lane)
  - steer: Out-of-order processing via process_message(message_id)
  - interrupt: Conversation paused — orchestrator skips these messages

Zero Mock Policy: Production-ready orchestration with real service calls.
=========================================================================
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_conversation import AgentConversation
from app.models.agent_definition import AgentDefinition
from app.models.agent_message import AgentMessage
from app.services.agent_team.agent_invoker import (
    AgentInvoker,
    InvocationResult,
    ProviderConfig,
    AllProvidersFailedError,
)
from app.services.agent_team.agent_registry import AgentRegistry, AgentNotFoundError
from app.services.agent_team.conversation_tracker import (
    ConversationTracker,
    ConversationInactiveError,
    LimitExceededError,
)
from app.services.agent_team.evidence_collector import EvidenceCollector
from app.services.agent_team.mention_parser import MentionParser, MentionRouteResult
from app.services.agent_team.message_queue import MessageQueue
from app.services.agent_team.config import (
    ROLE_MODEL_DEFAULTS,
    DEFAULT_CLASSIFICATION_RULES,
    MODEL_ROUTE_HINTS,
)
from app.services.agent_team.history_compactor import HistoryCompactor
from app.services.agent_team.query_classifier import classify

logger = logging.getLogger(__name__)


@dataclass
class ProcessingResult:
    """Result of processing a single message through the orchestrator."""

    message_id: UUID
    conversation_id: UUID
    success: bool
    provider_used: str | None = None
    model_used: str | None = None
    response_message_id: UUID | None = None
    evidence_id: UUID | None = None
    mentions_routed: list[str] = field(default_factory=list)
    tokens_used: int = 0
    cost_cents: int = 0
    latency_ms: int = 0
    error: str | None = None
    skipped_reason: str | None = None


class TeamOrchestratorError(Exception):
    """Base error for team orchestrator operations."""


class TeamOrchestrator:
    """
    Central coordinator for the Multi-Agent Team Engine.

    Ties together all Sprint 176-177 services into a cohesive processing
    loop that handles message claiming, provider invocation, evidence
    capture, and mention routing.

    Usage:
        orchestrator = TeamOrchestrator(db, redis=redis_client)

        # FIFO processing — called by background worker per lane
        result = await orchestrator.process_next("agent:coder")

        # Out-of-order processing — steer mode
        result = await orchestrator.process_message(message_id)
    """

    # System prompt template
    SYSTEM_PROMPT_TEMPLATE = (
        "You are {agent_name}, a {sdlc_role} agent in the SDLC Orchestrator.\n"
        "{system_prompt}\n\n"
        "Session scope: {session_scope}. "
        "You are in conversation {conversation_id}."
    )

    # Max conversation history messages to include in LLM context
    MAX_CONTEXT_MESSAGES = 20

    def __init__(
        self,
        db: AsyncSession,
        redis: object | None = None,
    ) -> None:
        self.db = db
        self.queue = MessageQueue(db, redis=redis)
        self.tracker = ConversationTracker(db)
        self.registry = AgentRegistry(db)
        self.mention_parser = MentionParser(db)
        self.evidence_collector = EvidenceCollector(db)
        # Sprint 179 — ADR-058 Pattern B
        self.compactor = HistoryCompactor(db)

    async def process_next(self, lane: str) -> ProcessingResult | None:
        """
        Process the next pending message from a lane (FIFO queue mode).

        This is the primary entry point for background workers.

        Args:
            lane: Processing lane name (e.g., "agent:coder", "agent:reviewer").

        Returns:
            ProcessingResult if a message was processed, None if lane is empty.
        """
        message = await self.queue.claim_next(lane)
        if message is None:
            return None

        logger.info(
            "TRACE_ORCHESTRATOR: Processing claimed message: id=%s, lane=%s",
            message.id,
            lane,
        )

        return await self._process(message)

    async def process_message(self, message_id: UUID) -> ProcessingResult:
        """
        Process a specific message by ID (steer mode for out-of-order).

        Used when queue_mode='steer' allows processing messages out of
        FIFO order, e.g., for priority human-in-the-loop messages.

        Args:
            message_id: The UUID of the message to process.

        Returns:
            ProcessingResult with processing outcome.

        Raises:
            TeamOrchestratorError: If message not found.
        """
        result = await self.db.execute(
            select(AgentMessage).where(AgentMessage.id == message_id)
        )
        message = result.scalar_one_or_none()

        if message is None:
            raise TeamOrchestratorError(f"Message {message_id} not found")

        # Mark as processing
        message.processing_status = "processing"
        await self.db.flush()

        logger.info(
            "TRACE_ORCHESTRATOR: Processing steered message: id=%s, conversation=%s",
            message.id,
            message.conversation_id,
        )

        return await self._process(message)

    async def _process(self, message: AgentMessage) -> ProcessingResult:
        """
        Core processing pipeline for a single message.

        Note: This method does NOT call db.commit(). Caller is responsible
        for commit/rollback (typically the API route or background worker).

        Steps:
        1. Load conversation (check active, not interrupted)
        2. Check limits (message count + budget)
        3. Load agent definition
        4. Parse @mentions
        5. Build LLM context
        6. Invoke provider chain
        7. Record result (complete/fail)
        8. Capture evidence
        9. Route @mentions
        """
        try:
            # Step 1: Load conversation
            conversation = await self._load_conversation(message.conversation_id)
            if conversation is None:
                return ProcessingResult(
                    message_id=message.id,
                    conversation_id=message.conversation_id,
                    success=False,
                    skipped_reason="conversation_not_found",
                )

            # Check for interrupt mode
            if conversation.status == "paused_by_human":
                logger.info(
                    "TRACE_ORCHESTRATOR: Skipping paused conversation: id=%s",
                    conversation.id,
                )
                # Re-queue the message (put back to pending)
                message.processing_status = "pending"
                await self.db.flush()
                return ProcessingResult(
                    message_id=message.id,
                    conversation_id=conversation.id,
                    success=False,
                    skipped_reason="conversation_paused",
                )

            # Step 2: Check limits
            try:
                await self.tracker.check_limits(conversation)
            except LimitExceededError as e:
                await self.queue.fail(
                    message.id,
                    error=str(e),
                    failover_reason=None,
                )
                return ProcessingResult(
                    message_id=message.id,
                    conversation_id=conversation.id,
                    success=False,
                    error=str(e),
                    skipped_reason="limit_exceeded",
                )

            # Step 2.5 (Pattern B): History compaction if near limit
            compaction_summary = await self.compactor.maybe_compact(
                conversation=conversation,
                agent_invoker=None,  # No invoker at this point; fallback truncation used
            )
            if compaction_summary:
                logger.info(
                    "TRACE_ORCHESTRATOR: History compacted for conv=%s, "
                    "summary_len=%d chars",
                    conversation.id,
                    len(compaction_summary),
                )

            # Step 3: Load agent definition
            definition = await self._load_definition(conversation.agent_definition_id)
            if definition is None:
                await self.queue.fail(
                    message.id,
                    error="Agent definition not found or inactive",
                )
                return ProcessingResult(
                    message_id=message.id,
                    conversation_id=conversation.id,
                    success=False,
                    error="agent_definition_not_found",
                )

            # Step 4: Parse @mentions
            mention_result = await self.mention_parser.parse_and_route(
                content=message.content,
                project_id=conversation.project_id,
            )

            # Step 5: Build LLM context
            system_prompt, context_messages = await self._build_llm_context(
                definition=definition,
                conversation=conversation,
                current_message=message,
            )

            # Step 5.5 (Pattern E): Classify message for model routing hint
            model_hint = classify(DEFAULT_CLASSIFICATION_RULES, message.content)
            if model_hint:
                logger.debug(
                    "TRACE_ORCHESTRATOR: Query classified — hint=%s, conv=%s",
                    model_hint,
                    conversation.id,
                )

            # Step 6: Invoke provider chain
            invoker = self._build_invoker(definition, model_hint=model_hint)
            try:
                result = await invoker.invoke(
                    messages=context_messages,
                    system_prompt=system_prompt,
                )
            except AllProvidersFailedError as e:
                await self.queue.fail(
                    message.id,
                    error=str(e),
                    failover_reason="all_providers_failed",
                )
                return ProcessingResult(
                    message_id=message.id,
                    conversation_id=conversation.id,
                    success=False,
                    error=str(e),
                )

            # Step 7: Record result
            total_tokens = result.input_tokens + result.output_tokens

            await self.queue.complete(
                message_id=message.id,
                provider_used=result.provider_used,
                token_count=total_tokens,
                latency_ms=result.latency_ms,
            )

            await self.tracker.record_token_usage(
                conversation_id=conversation.id,
                input_tokens=result.input_tokens,
                output_tokens=result.output_tokens,
                cost_cents=result.cost_cents,
            )

            await self.tracker.increment_message_count(conversation.id)

            # Step 8: Enqueue response message
            response_msg = await self.queue.enqueue(
                conversation_id=conversation.id,
                content=result.content,
                sender_type="agent",
                sender_id=definition.agent_name,
                processing_lane=message.processing_lane,
                queue_mode=conversation.queue_mode,
                message_type="response",
                parent_message_id=message.id,
            )

            # Step 9: Capture evidence (agent output → GateEvidence)
            on_behalf_of = f"{message.sender_type}:{message.sender_id}"
            evidence = await self.evidence_collector.capture_message(
                message=response_msg,
                agent_name=definition.agent_name,
                on_behalf_of=on_behalf_of,
            )

            # Step 10: Route @mentions (enqueue messages to mentioned agents)
            mentions_routed = await self._route_mentions(
                mention_result=mention_result,
                conversation=conversation,
                response_content=result.content,
                source_agent=definition.agent_name,
                parent_message_id=response_msg.id,
            )

            logger.info(
                "TRACE_ORCHESTRATOR: Message processed successfully: "
                "msg=%s, provider=%s, tokens=%d, cost=%d cents, "
                "evidence=%s, mentions_routed=%d",
                message.id,
                result.provider_used,
                total_tokens,
                result.cost_cents,
                evidence.id if evidence else None,
                len(mentions_routed),
            )

            return ProcessingResult(
                message_id=message.id,
                conversation_id=conversation.id,
                success=True,
                provider_used=result.provider_used,
                model_used=result.model_used,
                response_message_id=response_msg.id,
                evidence_id=evidence.id if evidence else None,
                mentions_routed=mentions_routed,
                tokens_used=total_tokens,
                cost_cents=result.cost_cents,
                latency_ms=result.latency_ms,
            )

        except Exception as e:
            logger.error(
                "TRACE_ORCHESTRATOR: Unexpected error processing message %s: %s",
                message.id,
                e,
                exc_info=True,
            )
            try:
                await self.queue.fail(
                    message.id,
                    error=f"Orchestrator error: {str(e)[:1000]}",
                )
            except Exception:
                logger.error(
                    "TRACE_ORCHESTRATOR: Failed to mark message as failed: %s",
                    message.id,
                    exc_info=True,
                )

            return ProcessingResult(
                message_id=message.id,
                conversation_id=message.conversation_id,
                success=False,
                error=str(e),
            )

    async def _load_conversation(
        self, conversation_id: UUID
    ) -> AgentConversation | None:
        """Load conversation, returning None if not found."""
        try:
            return await self.tracker.get(conversation_id)
        except Exception:
            logger.warning(
                "TRACE_ORCHESTRATOR: Conversation not found: %s",
                conversation_id,
            )
            return None

    async def _load_definition(
        self, definition_id: UUID
    ) -> AgentDefinition | None:
        """Load active agent definition, returning None if not found/inactive."""
        try:
            return await self.registry.get_active(definition_id)
        except AgentNotFoundError:
            return None

    async def _build_llm_context(
        self,
        definition: AgentDefinition,
        conversation: AgentConversation,
        current_message: AgentMessage,
    ) -> tuple[str, list[dict[str, str]]]:
        """
        Build the system prompt and conversation history for LLM invocation.

        Returns:
            Tuple of (system_prompt, messages) where messages is a list of
            {"role": "user"|"assistant", "content": "..."} dicts.
        """
        # Build system prompt
        system_prompt = self.SYSTEM_PROMPT_TEMPLATE.format(
            agent_name=definition.agent_name,
            sdlc_role=definition.sdlc_role,
            system_prompt=definition.system_prompt or "",
            session_scope=conversation.session_scope,
            conversation_id=conversation.id,
        )

        # Sprint 179 — ADR-058 Pattern B: inject compaction summary if present
        meta = conversation.metadata_ or {}
        compaction_summary: str | None = meta.get("compaction_summary")
        if compaction_summary:
            system_prompt = (
                f"[Conversation summary so far]:\n{compaction_summary}\n\n"
                f"[Current session continues below]\n\n"
                + system_prompt
            )

        # Fetch recent conversation history
        history_result = await self.db.execute(
            select(AgentMessage)
            .where(AgentMessage.conversation_id == conversation.id)
            .where(AgentMessage.id != current_message.id)
            .where(AgentMessage.processing_status == "completed")
            .order_by(AgentMessage.created_at.desc())
            .limit(self.MAX_CONTEXT_MESSAGES)
        )
        history_msgs = list(reversed(history_result.scalars().all()))

        # Build messages list
        context_messages: list[dict[str, str]] = []

        for msg in history_msgs:
            role = "assistant" if msg.sender_type == "agent" else "user"
            context_messages.append({"role": role, "content": msg.content})

        # Add current message
        context_messages.append({
            "role": "user",
            "content": current_message.content,
        })

        return system_prompt, context_messages

    def _build_invoker(
        self,
        definition: AgentDefinition,
        model_hint: str | None = None,
    ) -> AgentInvoker:
        """
        Build an AgentInvoker with the provider chain from definition config.

        Uses ROLE_MODEL_DEFAULTS for the definition's SDLC role, then
        overrides with any explicit config.

        Sprint 179 (Pattern E): If ``model_hint`` is provided and matches an
        entry in MODEL_ROUTE_HINTS, the primary model is overridden with the
        hint's model (role-specific key first, fallback to ``"*"``).

        Args:
            definition: Agent definition with config and SDLC role.
            model_hint: Optional routing hint from query_classifier.classify().
        """
        config = definition.config or {}
        role_defaults = ROLE_MODEL_DEFAULTS.get(definition.sdlc_role, {})

        # Primary provider from config or role defaults
        primary_provider = config.get("provider", role_defaults.get("provider", "ollama"))
        primary_model = config.get("model", role_defaults.get("model", "qwen3-coder:30b"))
        timeout = config.get("timeout_seconds", role_defaults.get("timeout_seconds", 30))

        # Sprint 179 — ADR-058 Pattern E: apply model hint override
        if model_hint and model_hint in MODEL_ROUTE_HINTS:
            hint_routes = MODEL_ROUTE_HINTS[model_hint]
            # Role-specific override first, then wildcard
            route = hint_routes.get(definition.sdlc_role) or hint_routes.get("*")
            if route:
                primary_provider, primary_model = route
                logger.debug(
                    "TRACE_ORCHESTRATOR: Model hint override — hint=%s, "
                    "provider=%s, model=%s",
                    model_hint,
                    primary_provider,
                    primary_model,
                )

        chain = [
            ProviderConfig(
                provider=primary_provider,
                model=primary_model,
                timeout_seconds=timeout,
            ),
        ]

        # Add Anthropic fallback if primary is not already Anthropic
        if primary_provider != "anthropic":
            chain.append(
                ProviderConfig(
                    provider="anthropic",
                    model="claude-sonnet-4-5",
                    timeout_seconds=45,
                ),
            )

        return AgentInvoker(provider_chain=chain)

    async def _route_mentions(
        self,
        mention_result: MentionRouteResult,
        conversation: AgentConversation,
        response_content: str,
        source_agent: str,
        parent_message_id: UUID,
    ) -> list[str]:
        """
        Route @mentions by enqueuing messages to mentioned agents' lanes.

        For each resolved @mention target:
        1. Determine the target agent's processing lane
        2. Enqueue a new 'mention' type message addressed to that agent
        3. Include the source agent's response as content

        Args:
            mention_result: MentionRouteResult from MentionParser.
            conversation: Current conversation.
            response_content: The agent's response to forward.
            source_agent: Name of the agent that generated the response.
            parent_message_id: Parent message for threading.

        Returns:
            List of agent names that were successfully routed to.
        """
        routed: list[str] = []

        if not mention_result.has_mentions:
            return routed

        for agent in mention_result.resolved_agents:
            target_lane = f"agent:{agent.agent_name}"

            try:
                await self.queue.enqueue(
                    conversation_id=conversation.id,
                    content=f"@{source_agent} mentioned you:\n\n{response_content}",
                    sender_type="agent",
                    sender_id=source_agent,
                    processing_lane=target_lane,
                    queue_mode=conversation.queue_mode,
                    message_type="mention",
                    recipient_id=agent.agent_name,
                    mentions=[agent.agent_name],
                    parent_message_id=parent_message_id,
                )
                routed.append(agent.agent_name)
                logger.debug(
                    "TRACE_ORCHESTRATOR: Routed mention to %s (lane=%s)",
                    agent.agent_name,
                    target_lane,
                )
            except Exception as e:
                logger.warning(
                    "TRACE_ORCHESTRATOR: Failed to route mention to %s: %s",
                    agent.agent_name,
                    e,
                )

        if mention_result.unresolved:
            logger.warning(
                "TRACE_ORCHESTRATOR: Unresolved mentions: %s",
                mention_result.unresolved,
            )

        return routed
