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

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.models.agent_conversation import AgentConversation
from app.models.agent_definition import AgentDefinition
from app.models.agent_message import AgentMessage
from app.models.sprint import Sprint
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
from app.services.agent_team.chat_command_router import (
    route_chat_command,
    ChatCommandResult,
)
from app.services.agent_team.history_compactor import HistoryCompactor
from app.services.agent_team.note_service import NoteService
from app.services.agent_team.escalation_service import EscalationService
from app.services.agent_team.query_classifier import classify, ClassificationResult
from app.services.ollama_service import OllamaError, get_ollama_service

logger = logging.getLogger(__name__)

# Sprint 204 (AD-3): LLM fallback prompt for ambiguous queries.
# Used by _llm_classify() when substring confidence < 0.6.
# Capped at 500 chars to bound LLM latency; qwen3:8b returns ~50 tokens.
_LLM_CLASSIFY_PROMPT = """\
Classify this user message into exactly one category.

Categories:
- code: Request to write, fix, generate, debug, or review code
- reasoning: Request requiring deep analysis, explanation, or multi-step thinking
- governance: Request for gate approval, evidence submission, sprint/audit management
- fast: Simple greeting, short acknowledgment, confirmation, or trivial query

Message: "{user_message}"

Respond with JSON only, no extra text: {{"hint": "category", "confidence": 0.0}}
confidence must be a float between 0.0 and 1.0."""


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
        self.redis = redis
        self.queue = MessageQueue(db, redis=redis)
        self.tracker = ConversationTracker(db)
        self.registry = AgentRegistry(db)
        self.mention_parser = MentionParser(db)
        self.evidence_collector = EvidenceCollector(db)
        # Sprint 179 — ADR-058 Pattern B
        self.compactor = HistoryCompactor(db)
        # Sprint 219 — P6 Agent Liveness
        from app.services.agent_team.heartbeat_service import HeartbeatService
        self.heartbeat = HeartbeatService(db, redis=redis)

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


            # Step 4.5 (Sprint 221 Track D): Consensus Interceptor
            # If the user directly calls `@vote`, bypass LLM and route to ConsensusService
            if message.content.strip().startswith("@vote"):
                import logging
                logger = logging.getLogger(__name__)
                logger.info(
                    "TRACE_ORCHESTRATOR: @vote intercepted — routing to consensus service, conv=%s",
                    conversation.id
                )
                return await self._handle_vote_command(
                    message=message,
                    conversation=conversation,
                    definition=definition
                )

            # Step 5: Build LLM context
            system_prompt, context_messages = await self._build_llm_context(
                definition=definition,
                conversation=conversation,
                current_message=message,
            )

            # Step 5.5 (Sprint 179 Pattern E / Sprint 204 Confidence Routing):
            # Classify message for model routing hint + confidence score.
            # classify() returns ClassificationResult; backward compat via
            # __bool__() (True iff hint is not None).
            # NOTE: governance pre-router interceptor (AD-2) added Day 2.
            classification: ClassificationResult = classify(
                DEFAULT_CLASSIFICATION_RULES, message.content
            )
            if classification:
                logger.debug(
                    "TRACE_ORCHESTRATOR: Query classified — hint=%s, "
                    "confidence=%.2f, method=%s, matches=%d, conv=%s",
                    classification.hint,
                    classification.confidence,
                    classification.method,
                    classification.matches,
                    conversation.id,
                )
            else:
                logger.debug(
                    "TRACE_ORCHESTRATOR: Query unclassified — "
                    "confidence=%.2f, conv=%s",
                    classification.confidence,
                    conversation.id,
                )

            # Step 5.6 (Sprint 204 AD-2): Governance pre-router interceptor.
            # If the message is classified as governance, dispatch directly to
            # the chat_command_router (LLM function calling) instead of the
            # generic LLM invocation path. This ensures governance commands
            # are handled by the bounded tool allowlist, not free-form LLM.
            if classification.hint == "governance":
                logger.info(
                    "TRACE_ORCHESTRATOR: Governance intercepted — "
                    "dispatching to chat_command_router, conv=%s, "
                    "confidence=%.2f",
                    conversation.id,
                    classification.confidence,
                )
                return await self._dispatch_governance_command(
                    message=message,
                    conversation=conversation,
                    definition=definition,
                )

            # Step 5.7 (Sprint 204 AD-3): LLM fallback for low-confidence queries.
            # When substring matching yields confidence < 0.6, delegate to
            # qwen3:8b for fast reclassification (1s timeout, non-fatal).
            # If LLM reclassifies as governance, re-run the governance intercept.
            # If LLM still yields confidence < 0.6 — Track B escalation (Day 5-6).
            if classification.confidence < 0.6:
                classification = await self._llm_classify(
                    content=message.content,
                    original=classification,
                )
                logger.debug(
                    "TRACE_ORCHESTRATOR: Post-LLM classification — "
                    "hint=%s, confidence=%.2f, method=%s, conv=%s",
                    classification.hint,
                    classification.confidence,
                    classification.method,
                    conversation.id,
                )
                if classification.hint == "governance":
                    logger.info(
                        "TRACE_ORCHESTRATOR: LLM reclassified as governance — "
                        "dispatching to chat_command_router, conv=%s",
                        conversation.id,
                    )
                    return await self._dispatch_governance_command(
                        message=message,
                        conversation=conversation,
                        definition=definition,
                    )

                # Track B (Sprint 204): LLM still low-confidence → human escalation.
                # Block on BLPOP until reviewer classifies via Magic Link or timeout.
                if classification.confidence < 0.6:
                    classification = await self._escalate_for_classification(
                        message=message,
                        conversation=conversation,
                        original=classification,
                    )
                    logger.info(
                        "TRACE_ORCHESTRATOR: Post-escalation classification — "
                        "hint=%s, confidence=%.2f, method=%s, conv=%s",
                        classification.hint,
                        classification.confidence,
                        classification.method,
                        conversation.id,
                    )

            # Step 6: Invoke provider chain
            invoker = self._build_invoker(definition, model_hint=classification.hint)
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

            # Sprint 219: Record heartbeat after successful agent turn
            await self.heartbeat.record_heartbeat(
                agent_id=conversation.agent_definition_id,
                conversation_id=conversation.id,
            )

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

            # Step 11: Append to sprint activity log (Sprint 194 ENR-02)
            if conversation.project_id:
                await self._log_sprint_activity(
                    conversation_id=conversation.id,
                    project_id=conversation.project_id,
                    summary=(
                        f"{definition.agent_name} responded "
                        f"({result.provider_used}, {result.latency_ms}ms)"
                    ),
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

        # Sprint 193 — Phase 3: Inject current sprint context into agent prompts
        sprint_context = await self._get_sprint_context(conversation.project_id)
        if sprint_context:
            system_prompt += f"\n\n## Current Sprint Context\n{sprint_context}"

        # Sprint 202 — Track B: Inject agent notes for cross-session memory
        try:
            note_svc = NoteService(self.db)
            notes_context = await note_svc.format_notes_for_context(
                agent_id=definition.id,
                max_notes=20,
            )
            if notes_context:
                system_prompt += f"\n\n## Agent Notes\n{notes_context}"
        except Exception as e:
            logger.warning(
                "TRACE_ORCHESTRATOR: Failed to load agent notes for %s: %s",
                definition.id,
                e,
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

    async def _get_sprint_context(self, project_id: UUID) -> str | None:
        """
        Get formatted sprint context for agent prompt injection.

        Sprint 193 — Phase 3: Agents must see sprint context so they can
        align their work with the current sprint goal, backlog priorities,
        and gate status.

        Args:
            project_id: UUID of the project

        Returns:
            Formatted sprint context string, or None if no active sprint
        """
        try:
            result = await self.db.execute(
                select(Sprint)
                .where(
                    Sprint.project_id == project_id,
                    Sprint.status == "active",
                )
                .order_by(Sprint.number.desc())
                .limit(1)
            )
            sprint = result.scalar_one_or_none()

            if not sprint:
                return None

            lines = [
                f"**Sprint {sprint.number}: {sprint.name}** | Status: {sprint.status.upper()}",
                "",
                f"Goal: {sprint.goal}",
            ]

            if sprint.start_date and sprint.end_date:
                from datetime import date as date_type

                today = date_type.today()
                days_remaining = (sprint.end_date - today).days
                if days_remaining >= 0:
                    lines.append(f"Days remaining: {days_remaining}")
                else:
                    lines.append(f"Sprint overdue by {abs(days_remaining)} days")

            g_sprint = getattr(sprint, "g_sprint_status", None)
            if g_sprint:
                lines.append(f"G-Sprint: {g_sprint}")

            return "\n".join(lines)

        except Exception as e:
            logger.warning("Failed to get sprint context for project %s: %s", project_id, e)
            return None

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

    # -----------------------------------------------------------------
    # Sprint 204 (AD-2): Governance Pre-Router Dispatch
    # -----------------------------------------------------------------


    # -----------------------------------------------------------------
    # Sprint 221 (Track D): Consensus Vote Interceptor
    # -----------------------------------------------------------------

    async def _handle_vote_command(
        self,
        message: AgentMessage,
        conversation: AgentConversation,
        definition: AgentDefinition
    ) -> ProcessingResult:
        '''
        Intercepts @vote messages and manually routes them through ConsensusService.
        '''
        from app.services.agent_team.consensus_service import ConsensusService
        service = ConsensusService(self.db)
        
        text = message.content.strip()
        parts = text.split(" ", 2)
        cmd = parts[1].lower() if len(parts) > 1 else ""
        args = parts[2] if len(parts) > 2 else ""

        reply_content = f"Unknown or missing vote subcommand: {cmd}. Supported: create, approve, reject, abstain, status, cancel"
        
        try:
            if cmd == "create":
                topic = args.strip().strip('"\'')
                if not topic:
                    reply_content = "Format: @vote create \"topic\""
                else:
                    session = await service.create_session(
                        conversation_id=conversation.id,
                        topic=topic,
                        created_by=definition.id,
                        quorum_type="majority",
                        required_voters=[definition.id] # Simplified for POC
                    )
                    reply_content = f"Consensus session created: {session.id}"
                    await self.queue.post_broadcast(
                        conversation_id=conversation.id,
                        content=reply_content,
                        sender_id="system",
                        sender_type="system",
                        metadata={"event_type": "consensus.created", "session_id": session.id, "topic": session.topic}
                    )
                    
            elif cmd in ["approve", "reject", "abstain"]:
                reasoning = args.strip()
                result = await service.cast_vote(
                    conversation_id=conversation.id,
                    voter_id=definition.id,
                    vote_value=cmd,
                    reasoning=reasoning
                )
                if result:
                    reply_content = f"Vote recorded: {cmd}. Session status: {result['status']}"
                    if result['status'] == "decided":
                        await self.queue.post_broadcast(
                            conversation_id=conversation.id,
                            content=f"Consensus reached: {result['result']['decision']}",
                            sender_id="system",
                            sender_type="system",
                            metadata={"event_type": "consensus.resolved", "session_id": result['id']}
                        )
                else:
                    reply_content = "No active session found or vote failed."
        except Exception as e:
            reply_content = f"Vote error: {str(e)}"

        # Send broadcast explicitly if not a simple reply
        # Actually completing the message generates the final reply, but let's push a system broadcast just in case
        await self.queue.post_broadcast(
            conversation_id=conversation.id,
            content=reply_content,
            sender_id="system",
            sender_type="system",
            metadata={"event_type": "consensus.reply"}
        )

        await self.queue.complete(
            message.id,
            output=reply_content,
            response_metadata={"intercepted": "consensus"}
        )
        return ProcessingResult(
            message_id=message.id,
            conversation_id=conversation.id,
            success=True,
            output=reply_content
        )

    async def _dispatch_governance_command(
        self,
        message: AgentMessage,
        conversation: AgentConversation,
        definition: AgentDefinition,
    ) -> ProcessingResult:
        """
        Dispatch a governance-classified message to the chat command router.

        Sprint 204 (AD-2): When ``classify()`` returns hint="governance",
        this method routes the message through ``route_chat_command()``
        (LLM function calling with bounded tool allowlist) instead of the
        generic LLM invocation path.

        The chat command router determines the specific governance action
        (approve gate, submit evidence, export audit, etc.) and returns
        a ``ChatCommandResult`` with the tool call or text response.

        Args:
            message: The incoming agent message.
            conversation: Active conversation.
            definition: Agent definition for context.

        Returns:
            ProcessingResult with governance routing outcome.
        """
        try:
            # Route through LLM function calling (chat_command_router)
            sender_id = message.sender_id or "unknown"
            cmd_result: ChatCommandResult = await route_chat_command(
                message=message.content,
                user_id=sender_id,
            )

            # Build response text from command result
            if cmd_result.is_error:
                response_text = (
                    f"Governance command error: {cmd_result.error}"
                )
            elif cmd_result.is_tool_call:
                response_text = (
                    f"[governance:{cmd_result.tool_name}] "
                    f"{cmd_result.response_text or 'Command dispatched.'}"
                )
            else:
                response_text = (
                    cmd_result.response_text
                    or "I understood your governance request but could not "
                    "determine the specific action. Please clarify."
                )

            # Complete the original message
            await self.queue.complete(
                message_id=message.id,
                provider_used="chat_command_router",
                token_count=0,
                latency_ms=0,
            )

            await self.tracker.increment_message_count(conversation.id)

            # Enqueue governance response
            response_msg = await self.queue.enqueue(
                conversation_id=conversation.id,
                content=response_text,
                sender_type="agent",
                sender_id=definition.agent_name,
                processing_lane=message.processing_lane,
                queue_mode=conversation.queue_mode,
                message_type="response",
                parent_message_id=message.id,
            )

            # Capture evidence
            on_behalf_of = f"{message.sender_type}:{message.sender_id}"
            evidence = await self.evidence_collector.capture_message(
                message=response_msg,
                agent_name=definition.agent_name,
                on_behalf_of=on_behalf_of,
            )

            # Sprint activity log
            if conversation.project_id:
                tool_label = cmd_result.tool_name or "governance"
                await self._log_sprint_activity(
                    conversation_id=conversation.id,
                    project_id=conversation.project_id,
                    summary=(
                        f"{definition.agent_name} handled governance "
                        f"command: {tool_label}"
                    ),
                )

            logger.info(
                "TRACE_ORCHESTRATOR: Governance command dispatched — "
                "msg=%s, tool=%s, is_error=%s, conv=%s",
                message.id,
                cmd_result.tool_name,
                cmd_result.is_error,
                conversation.id,
            )

            return ProcessingResult(
                message_id=message.id,
                conversation_id=conversation.id,
                success=not cmd_result.is_error,
                provider_used="chat_command_router",
                model_used="governance",
                response_message_id=response_msg.id,
                evidence_id=evidence.id if evidence else None,
                error=cmd_result.error,
            )

        except Exception as e:
            logger.error(
                "TRACE_ORCHESTRATOR: Governance dispatch failed — "
                "msg=%s, error=%s",
                message.id,
                e,
                exc_info=True,
            )
            # Fall through: mark message failed and return error result
            try:
                await self.queue.fail(
                    message.id,
                    error=f"Governance dispatch error: {str(e)[:500]}",
                )
            except Exception:
                logger.error(
                    "TRACE_ORCHESTRATOR: Failed to mark message as failed: %s",
                    message.id,
                    exc_info=True,
                )

            return ProcessingResult(
                message_id=message.id,
                conversation_id=conversation.id,
                success=False,
                error=f"Governance dispatch error: {str(e)[:500]}",
            )

    async def _escalate_for_classification(
        self,
        message: AgentMessage,
        conversation: AgentConversation,
        original: ClassificationResult,
    ) -> ClassificationResult:
        """
        Block on human classification for a low-confidence query (Sprint 204 Track B).

        When the LLM fallback still yields confidence < 0.6, this method delegates
        to ``EscalationService.escalate()`` which:
          1. Generates 4 Magic Link tokens (code / reasoning / governance / fast).
          2. Sends a Telegram notification to the configured reviewer.
          3. Blocks on Redis BLPOP ``escalation_result:{conversation_id}`` until
             the reviewer clicks a link or ``ESCALATION_TIMEOUT_SECONDS`` elapses.

        After escalation resolves, the caller (``_process()``) continues with the
        resolved ``ClassificationResult`` at Step 6 (provider invocation).

        Args:
            message: The incoming agent message (provides the query text).
            conversation: Active conversation (provides ``conversation_id``).
            original: Pre-escalation ``ClassificationResult`` — used as the
                      timeout fallback hint.

        Returns:
            ``ClassificationResult`` with method="human" (reviewer clicked) or
            method="timeout_fallback" (300 s elapsed, preserving original hint).
        """
        logger.info(
            "TRACE_ORCHESTRATOR: Escalating for human classification — "
            "conv=%s, original_hint=%s, confidence=%.2f",
            conversation.id,
            original.hint,
            original.confidence,
        )

        escalation_service = EscalationService()
        try:
            result = await escalation_service.escalate(
                conversation_id=str(conversation.id),
                query=message.content,
                original=original,
            )
        except Exception as exc:
            logger.error(
                "TRACE_ORCHESTRATOR: EscalationService failed — "
                "conv=%s, error=%s — using timeout_fallback",
                conversation.id,
                exc,
            )
            result = ClassificationResult(
                hint=original.hint,
                confidence=original.confidence,
                method="timeout_fallback",
                matches=original.matches,
            )

        if result.method == "timeout_fallback":
            logger.warning(
                "TRACE_ORCHESTRATOR: Classification escalation timed out — "
                "conv=%s, fallback_hint=%s (unconfirmed)",
                conversation.id,
                result.hint,
            )

        return result

    async def _llm_classify(
        self,
        content: str,
        original: ClassificationResult,
    ) -> ClassificationResult:
        """
        LLM-based fallback classifier for ambiguous messages.

        Sprint 204 (AD-3): When ``classify()`` returns confidence < 0.6,
        this method asks ``qwen3:8b`` to classify the message via a
        structured JSON prompt. qwen3:8b is the fastest available model
        (~60-80 tok/s) and is used exclusively for this classification
        task to bound latency.

        Timeout is 1.0 s (``asyncio.wait_for``). Ollama's ``generate()``
        is synchronous; it is wrapped with ``run_in_threadpool`` so it
        does not block the event loop.

        Non-fatal contract: any failure (timeout, parse error, invalid
        category, OllamaError) returns the original ``ClassificationResult``
        with ``method`` updated to ``"timeout_fallback"`` or
        ``"llm_failed"``. The caller proceeds with reduced confidence and
        may escalate to a human (Track B, Day 5-6).

        Args:
            content: Raw message text (truncated to 500 chars for the prompt).
            original: The ``ClassificationResult`` from substring matching.

        Returns:
            Updated ``ClassificationResult`` with ``method="llm"`` on
            success, ``method="timeout_fallback"`` on timeout, or
            ``method="llm_failed"`` on parse/network error. Confidence
            and hint are preserved from original on failure.
        """
        _VALID_HINTS = frozenset({"code", "reasoning", "governance", "fast"})
        prompt = _LLM_CLASSIFY_PROMPT.format(
            # Cap at 500 chars to bound token count; trailing context is
            # less discriminative than the opening intent.
            user_message=content[:500].replace('"', '\\"')
        )
        try:
            ollama = get_ollama_service()
            response = await asyncio.wait_for(
                run_in_threadpool(
                    ollama.generate,
                    prompt,       # positional: prompt
                    "qwen3:8b",   # positional: model (fastest)
                    None,         # system (none needed)
                    0.0,          # temperature — deterministic
                    64,           # max_tokens — JSON fits in <50 tokens
                ),
                timeout=1.0,
            )

            raw = response.response.strip()
            # Strip any markdown code fences Ollama might add
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
                raw = raw.strip()
            if raw.endswith("```"):
                raw = raw[: raw.rfind("```")].strip()

            data: dict = json.loads(raw)
            hint_raw = data.get("hint", "")
            hint: str | None = hint_raw if hint_raw in _VALID_HINTS else None
            confidence = float(data.get("confidence", 0.5))
            confidence = max(0.0, min(1.0, confidence))

            logger.debug(
                "TRACE_ORCHESTRATOR: _llm_classify result — "
                "hint=%s, confidence=%.2f, raw=%r",
                hint,
                confidence,
                raw[:120],
            )
            return ClassificationResult(
                hint=hint,
                confidence=confidence,
                method="llm",
                matches=0,
            )

        except asyncio.TimeoutError:
            logger.warning(
                "TRACE_ORCHESTRATOR: _llm_classify timed out (>1s) — "
                "falling back to original classification, original_hint=%s",
                original.hint,
            )
            return ClassificationResult(
                hint=original.hint,
                confidence=original.confidence,
                method="timeout_fallback",
                matches=original.matches,
            )

        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
            logger.warning(
                "TRACE_ORCHESTRATOR: _llm_classify parse error — "
                "%s: %s, original_hint=%s",
                type(exc).__name__,
                exc,
                original.hint,
            )
            return ClassificationResult(
                hint=original.hint,
                confidence=original.confidence,
                method="llm_failed",
                matches=original.matches,
            )

        except OllamaError as exc:
            logger.warning(
                "TRACE_ORCHESTRATOR: _llm_classify OllamaError — "
                "%s, original_hint=%s",
                exc,
                original.hint,
            )
            return ClassificationResult(
                hint=original.hint,
                confidence=original.confidence,
                method="llm_failed",
                matches=original.matches,
            )

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

    # -----------------------------------------------------------------
    # Sprint Activity Log (Sprint 194 ENR-02 — TinySDLC pattern)
    # -----------------------------------------------------------------

    async def _log_sprint_activity(
        self,
        conversation_id: UUID,
        project_id: UUID,
        summary: str,
    ) -> None:
        """Append conversation summary to the active sprint's activity log.

        Stores activities in ``Sprint.metadata_["activities"]`` JSONB field.
        Keeps the last 50 entries to prevent unbounded growth.

        Args:
            conversation_id: Conversation that triggered this activity.
            project_id: Project UUID to look up active sprint.
            summary: Human-readable 1-line summary.
        """
        try:
            result = await self.db.execute(
                select(Sprint)
                .where(
                    Sprint.project_id == project_id,
                    Sprint.status == "ACTIVE",
                )
                .order_by(Sprint.created_at.desc())
                .limit(1)
            )
            sprint = result.scalar_one_or_none()
            if sprint is None:
                return

            metadata = dict(sprint.metadata_) if sprint.metadata_ else {}
            activities: list = metadata.get("activities", [])
            activities.append({
                "conversation_id": str(conversation_id),
                "summary": summary,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
            # Keep last 50 activities to prevent unbounded growth
            metadata["activities"] = activities[-50:]
            sprint.metadata_ = metadata
            await self.db.flush()

            logger.debug(
                "TRACE_ORCHESTRATOR: Sprint activity logged — sprint=%s, conv=%s",
                sprint.id,
                conversation_id,
            )
        except Exception as e:
            # Non-critical: log warning but don't fail message processing
            logger.warning(
                "TRACE_ORCHESTRATOR: Failed to log sprint activity: %s", e
            )
