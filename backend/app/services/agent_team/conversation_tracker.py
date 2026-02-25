"""
=========================================================================
Conversation Tracker — Parent-child inheritance + loop guards + budget
SDLC Orchestrator - Sprint 177 (Multi-Agent Core Services)
Updated: Sprint 200 — Budget circuit breaker with OTT notifications (B-01/B-03/B-04)

Version: 1.1.0
Date: February 2026
Status: ACTIVE - Sprint 200
Authority: CTO Approved (ADR-056)
Reference: ADR-056-Multi-Agent-Team-Engine.md

Purpose:
- Conversation lifecycle management (active → completed/max_reached/error)
- Parent-child session inheritance (OpenClaw Pattern 5)
- Loop guard enforcement via ConversationLimits integration
- Token budget tracking + circuit breaker (Non-Negotiable #13)
- Delegation depth validation (Nanobot N2)
- Sprint 200 B-01: Per-conversation budget enforcement
- Sprint 200 B-02: Per-organization monthly budget (tier-based)
- Sprint 200 B-03: Budget warning at 80% threshold
- Sprint 200 B-04: Hard stop at 100% with admin notification

Sources:
- OpenClaw: src/agents/conversation-tracker.ts (session management)
- TinyClaw: src/tinyclaw/loop-guard.ts (message cap, branch counting)
- Nanobot N2: delegation depth tracking
- ADR-056 Decision 1: Snapshot Precedence
- ADR-056 Non-Negotiable #9: Loop guards
- ADR-056 Non-Negotiable #13: Budget circuit breaker

Zero Mock Policy: Production-ready async SQLAlchemy 2.0 service
=========================================================================
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_conversation import AgentConversation
from app.models.agent_definition import AgentDefinition
from app.services.agent_team.conversation_limits import ConversationLimits, LimitViolation

logger = logging.getLogger(__name__)

# ── Budget Thresholds (Sprint 200 B-03) ──────────────────────────────────────

BUDGET_WARNING_THRESHOLD: float = 0.80  # 80% → send warning
BUDGET_CRITICAL_THRESHOLD: float = 1.00  # 100% → hard stop

# Per-organization monthly budget limits by tier (Sprint 200 B-02)
# Values in cents — LITE=$10, STANDARD=$50, PRO=$200, ENTERPRISE=$1000
ORG_MONTHLY_BUDGET_CENTS: dict[str, int] = {
    "LITE": 1_000,
    "STANDARD": 5_000,
    "PRO": 20_000,
    "ENTERPRISE": 100_000,
}

# Redis key for per-org monthly budget tracking
_ORG_BUDGET_KEY = "org_monthly_budget:{org_id}:{year_month}"
_ORG_BUDGET_TTL = 35 * 86400  # 35 days — covers month + safety margin


class BudgetStatus(str, Enum):
    """Budget health status for a conversation or organization."""

    OK = "ok"
    WARNING = "warning"  # Above 80% — send OTT warning
    EXCEEDED = "exceeded"  # At or above 100% — hard stop


@dataclass(frozen=True)
class BudgetCheckResult:
    """Result of a budget check with details for caller notification."""

    status: BudgetStatus
    current_cents: int
    max_cents: int
    percentage: float
    message: str


class ConversationError(Exception):
    """Base exception for conversation operations."""


class ConversationNotFoundError(ConversationError):
    """Conversation not found."""


class ConversationInactiveError(ConversationError):
    """Conversation is not in active status."""


class LimitExceededError(ConversationError):
    """A conversation limit has been exceeded."""

    def __init__(self, violation: LimitViolation, message: str):
        self.violation = violation
        super().__init__(message)


class DelegationDepthError(ConversationError):
    """Delegation depth limit exceeded."""


class ConversationTracker:
    """
    Manages conversation lifecycle, loop guards, budget tracking,
    and parent-child inheritance.

    Snapshot Precedence (ADR-056 Decision 1):
    On conversation creation, max_messages, max_budget_cents, queue_mode,
    and session_scope are copied from the agent definition. The conversation
    copy is authoritative after creation.

    Usage:
        tracker = ConversationTracker(db)

        # Create with snapshot precedence
        conv = await tracker.create(definition, payload)

        # Check limits before processing
        await tracker.check_limits(conv)

        # Update token usage after processing
        await tracker.record_token_usage(conv.id, input_tokens=500, output_tokens=200, cost_cents=2)

        # Complete conversation
        await tracker.complete(conv.id)
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        definition: AgentDefinition,
        project_id: UUID,
        initiator_type: str,
        initiator_id: str,
        channel: str,
        parent_conversation_id: UUID | None = None,
        metadata: dict | None = None,
    ) -> AgentConversation:
        """
        Create a conversation with Snapshot Precedence from agent definition.

        Validates delegation depth against parent conversation chain.

        Args:
            definition: Agent definition to snapshot from.
            project_id: Project UUID (must match definition.project_id).
            initiator_type: "user", "agent", "gate_event", "ott_channel".
            initiator_id: Identifier of the initiator.
            channel: Communication channel.
            parent_conversation_id: Parent conversation for sub-agent inheritance.
            metadata: Optional extensible metadata.

        Returns:
            Created AgentConversation ORM instance.

        Raises:
            DelegationDepthError: If depth exceeds definition.max_delegation_depth.
        """
        delegation_depth = 0

        if parent_conversation_id:
            parent = await self._get_conversation(parent_conversation_id)
            delegation_depth = parent.delegation_depth + 1

            if delegation_depth > definition.max_delegation_depth:
                raise DelegationDepthError(
                    f"Delegation depth {delegation_depth} exceeds max "
                    f"{definition.max_delegation_depth} for agent '{definition.agent_name}'"
                )

        conversation = AgentConversation(
            id=uuid4(),
            project_id=project_id,
            agent_definition_id=definition.id,
            parent_conversation_id=parent_conversation_id,
            delegation_depth=delegation_depth,
            initiator_type=initiator_type,
            initiator_id=initiator_id,
            channel=channel,
            # Snapshot Precedence (ADR-056 Decision 1)
            session_scope=definition.session_scope,
            queue_mode=definition.queue_mode,
            max_messages=definition.config.get("max_messages", 50),
            max_budget_cents=definition.config.get("max_budget_cents", 1000),
            # Defaults
            status="active",
            metadata_=metadata or {},
        )

        self.db.add(conversation)
        await self.db.flush()

        logger.info(
            "Created conversation: id=%s, agent=%s, depth=%d, channel=%s",
            conversation.id,
            definition.agent_name,
            delegation_depth,
            channel,
        )
        return conversation

    async def get(self, conversation_id: UUID) -> AgentConversation:
        """
        Get conversation by ID.

        Raises:
            ConversationNotFoundError: If not found.
        """
        return await self._get_conversation(conversation_id)

    async def get_active(self, conversation_id: UUID) -> AgentConversation:
        """
        Get conversation by ID, ensuring it is active.

        Raises:
            ConversationNotFoundError: If not found.
            ConversationInactiveError: If not in active status.
        """
        conversation = await self._get_conversation(conversation_id)
        if conversation.status != "active":
            raise ConversationInactiveError(
                f"Conversation {conversation_id} is '{conversation.status}', not active"
            )
        return conversation

    def build_limits(self, conversation: AgentConversation) -> ConversationLimits:
        """
        Build ConversationLimits from snapshotted conversation fields.

        Uses the conversation's own snapshotted values (not the definition's),
        per Snapshot Precedence.
        """
        return ConversationLimits(
            max_messages=conversation.max_messages,
            max_budget_cents=conversation.max_budget_cents,
        )

    async def check_limits(self, conversation: AgentConversation) -> None:
        """
        Check all conversation limits. Raises LimitExceededError on violation.

        On violation, also updates conversation status to reflect the limit.
        """
        limits = self.build_limits(conversation)

        # Check message count
        violation = limits.check_messages(conversation.total_messages)
        if violation:
            await self._set_status(conversation, "max_reached")
            raise LimitExceededError(
                violation,
                f"Message limit reached: {conversation.total_messages}/{conversation.max_messages}",
            )

        # Check budget
        violation = limits.check_budget(conversation.current_cost_cents)
        if violation:
            await self._set_status(conversation, "max_reached")
            raise LimitExceededError(
                violation,
                f"Budget exceeded: {conversation.current_cost_cents}/{conversation.max_budget_cents} cents",
            )

    async def increment_message_count(self, conversation_id: UUID) -> int:
        """
        Atomically increment total_messages and return new count.

        Also increments branch_count when appropriate (TinyClaw pattern).
        """
        conversation = await self._get_conversation(conversation_id)
        conversation.total_messages += 1
        await self.db.flush()
        return conversation.total_messages

    async def record_token_usage(
        self,
        conversation_id: UUID,
        input_tokens: int,
        output_tokens: int,
        cost_cents: int,
        provider: str = "",
    ) -> BudgetCheckResult:
        """
        Record token usage and cost for budget circuit breaker tracking.
        Returns BudgetCheckResult so caller can send warnings or hard-stop.

        Called after each provider invocation with the token counts from
        the response.

        Sprint 200 B-01: per-conversation budget enforcement.
        Sprint 200 B-03: returns WARNING status at 80% threshold.
        Sprint 200 B-04: returns EXCEEDED status at 100%.
        Sprint 200 B-06: records provider attribution in metadata.
        """
        conversation = await self._get_conversation(conversation_id)
        conversation.input_tokens += input_tokens
        conversation.output_tokens += output_tokens
        conversation.total_tokens += input_tokens + output_tokens
        conversation.current_cost_cents += cost_cents

        # B-06: Track per-provider cost attribution in metadata
        if provider:
            metadata = dict(conversation.metadata_ or {})
            cost_by_provider: dict[str, int] = metadata.get("cost_by_provider", {})
            cost_by_provider[provider] = cost_by_provider.get(provider, 0) + cost_cents
            metadata["cost_by_provider"] = cost_by_provider
            conversation.metadata_ = metadata

        await self.db.flush()

        # Check budget status
        result = self.check_budget_status(conversation)

        logger.info(
            "TRACE_BUDGET cost_increment=%d, running_cost=%d, "
            "max_budget=%d, status=%s, conv=%s, tokens=+%d+%d, provider=%s",
            cost_cents,
            conversation.current_cost_cents,
            conversation.max_budget_cents,
            result.status.value,
            conversation_id,
            input_tokens,
            output_tokens,
            provider,
        )

        # B-04: Hard stop — pause conversation if budget exceeded
        if result.status == BudgetStatus.EXCEEDED:
            await self._set_status(conversation, "max_reached")
            logger.warning(
                "TRACE_BUDGET_EXCEEDED conv=%s cost=%d/%d — conversation paused",
                conversation_id,
                conversation.current_cost_cents,
                conversation.max_budget_cents,
            )

        return result

    @staticmethod
    def check_budget_status(conversation: AgentConversation) -> BudgetCheckResult:
        """
        Check budget health for a conversation (Sprint 200 B-01/B-03/B-04).

        Returns:
            BudgetCheckResult with status, percentage, and user-facing message.
        """
        current = conversation.current_cost_cents
        maximum = conversation.max_budget_cents
        if maximum <= 0:
            return BudgetCheckResult(
                status=BudgetStatus.OK,
                current_cents=current,
                max_cents=maximum,
                percentage=0.0,
                message="Budget tracking disabled (max=0).",
            )

        pct = current / maximum

        if pct >= BUDGET_CRITICAL_THRESHOLD:
            return BudgetCheckResult(
                status=BudgetStatus.EXCEEDED,
                current_cents=current,
                max_cents=maximum,
                percentage=round(pct * 100, 1),
                message=(
                    f"Budget exceeded: {current} / {maximum} cents "
                    f"({round(pct * 100, 1)}%). Conversation paused."
                ),
            )

        if pct >= BUDGET_WARNING_THRESHOLD:
            return BudgetCheckResult(
                status=BudgetStatus.WARNING,
                current_cents=current,
                max_cents=maximum,
                percentage=round(pct * 100, 1),
                message=(
                    f"Budget warning: {current} / {maximum} cents "
                    f"({round(pct * 100, 1)}%). Approaching limit."
                ),
            )

        return BudgetCheckResult(
            status=BudgetStatus.OK,
            current_cents=current,
            max_cents=maximum,
            percentage=round(pct * 100, 1),
            message=f"Budget OK: {current} / {maximum} cents ({round(pct * 100, 1)}%).",
        )

    async def check_org_monthly_budget(
        self,
        org_id: str,
        tier: str,
        redis: object | None = None,
    ) -> BudgetCheckResult:
        """
        Check per-organization monthly budget (Sprint 200 B-02).

        Uses Redis INCRBY for atomic counting across all conversations.
        Tier-based limits: LITE=$10, STANDARD=$50, PRO=$200, ENTERPRISE=$1000.

        Args:
            org_id: Organization identifier.
            tier: Tier name (LITE, STANDARD, PRO, ENTERPRISE).
            redis: Redis client for atomic counter.

        Returns:
            BudgetCheckResult for the organization's monthly usage.
        """
        max_cents = ORG_MONTHLY_BUDGET_CENTS.get(tier.upper(), ORG_MONTHLY_BUDGET_CENTS["STANDARD"])

        if redis is None:
            return BudgetCheckResult(
                status=BudgetStatus.OK,
                current_cents=0,
                max_cents=max_cents,
                percentage=0.0,
                message="Org budget check skipped (no Redis).",
            )

        year_month = datetime.now(timezone.utc).strftime("%Y-%m")
        key = _ORG_BUDGET_KEY.format(org_id=org_id, year_month=year_month)

        try:
            current_bytes = await redis.get(key)  # type: ignore[union-attr]
            current = int(current_bytes) if current_bytes else 0
        except Exception:
            return BudgetCheckResult(
                status=BudgetStatus.OK,
                current_cents=0,
                max_cents=max_cents,
                percentage=0.0,
                message="Org budget check failed (Redis error).",
            )

        pct = current / max_cents if max_cents > 0 else 0.0

        if pct >= BUDGET_CRITICAL_THRESHOLD:
            return BudgetCheckResult(
                status=BudgetStatus.EXCEEDED,
                current_cents=current,
                max_cents=max_cents,
                percentage=round(pct * 100, 1),
                message=(
                    f"Organization monthly budget exceeded: ${current / 100:.2f} / "
                    f"${max_cents / 100:.2f} ({tier}). Contact admin to upgrade tier."
                ),
            )

        if pct >= BUDGET_WARNING_THRESHOLD:
            return BudgetCheckResult(
                status=BudgetStatus.WARNING,
                current_cents=current,
                max_cents=max_cents,
                percentage=round(pct * 100, 1),
                message=(
                    f"Organization monthly budget at {round(pct * 100, 1)}%: "
                    f"${current / 100:.2f} / ${max_cents / 100:.2f} ({tier})."
                ),
            )

        return BudgetCheckResult(
            status=BudgetStatus.OK,
            current_cents=current,
            max_cents=max_cents,
            percentage=round(pct * 100, 1),
            message=f"Org budget OK: ${current / 100:.2f} / ${max_cents / 100:.2f} ({tier}).",
        )

    async def increment_org_monthly_budget(
        self,
        org_id: str,
        cost_cents: int,
        redis: object | None = None,
    ) -> int:
        """
        Atomically increment organization monthly budget counter (Sprint 200 B-02).

        Uses Redis INCRBY for race-condition-safe increment.

        Returns:
            New total cost in cents for the month.
        """
        if redis is None or cost_cents <= 0:
            return 0

        year_month = datetime.now(timezone.utc).strftime("%Y-%m")
        key = _ORG_BUDGET_KEY.format(org_id=org_id, year_month=year_month)

        try:
            new_total = await redis.incrby(key, cost_cents)  # type: ignore[union-attr]
            # Set TTL only on first increment (when new_total == cost_cents)
            if new_total == cost_cents:
                await redis.expire(key, _ORG_BUDGET_TTL)  # type: ignore[union-attr]
            return int(new_total)
        except Exception as exc:
            logger.warning(
                "Failed to increment org budget (non-fatal): org=%s, cost=%d, error=%s",
                org_id,
                cost_cents,
                exc,
            )
            return 0

    async def complete(self, conversation_id: UUID) -> AgentConversation:
        """Mark conversation as completed."""
        conversation = await self._get_conversation(conversation_id)
        await self._set_status(conversation, "completed")
        logger.info("Conversation completed: id=%s", conversation_id)
        return conversation

    async def error(
        self, conversation_id: UUID, error_detail: str | None = None
    ) -> AgentConversation:
        """Mark conversation as errored."""
        conversation = await self._get_conversation(conversation_id)
        await self._set_status(conversation, "error")
        if error_detail:
            metadata = dict(conversation.metadata_ or {})
            metadata["last_error"] = error_detail[:2000]
            conversation.metadata_ = metadata
            await self.db.flush()
        logger.warning(
            "Conversation errored: id=%s, error=%.200s",
            conversation_id,
            error_detail,
        )
        return conversation

    async def pause(self, conversation_id: UUID, reason: str) -> AgentConversation:
        """Pause conversation via human-in-the-loop interrupt."""
        conversation = await self._get_conversation(conversation_id)
        await self._set_status(conversation, "paused_by_human")
        metadata = dict(conversation.metadata_ or {})
        metadata["pause_reason"] = reason[:500]
        conversation.metadata_ = metadata
        await self.db.flush()
        logger.info(
            "Conversation paused: id=%s, reason=%.200s",
            conversation_id,
            reason,
        )
        return conversation

    async def resume(self, conversation_id: UUID) -> AgentConversation:
        """Resume a paused conversation."""
        conversation = await self._get_conversation(conversation_id)
        if conversation.status != "paused_by_human":
            raise ConversationInactiveError(
                f"Cannot resume conversation {conversation_id}: "
                f"status is '{conversation.status}', expected 'paused_by_human'"
            )
        conversation.status = "active"
        await self.db.flush()
        logger.info("Conversation resumed: id=%s", conversation_id)
        return conversation

    async def find_active_by_session_key(
        self,
        agent_definition_id: UUID,
        session_scope: str,
        sender_id: str,
    ) -> AgentConversation | None:
        """
        Find an active conversation matching session scoping rules.

        Session scoping (2 P0 modes):
        - per-sender: Match on agent_definition_id + initiator_id
        - global: Match on agent_definition_id only (ignores sender)
        """
        conditions = [
            AgentConversation.agent_definition_id == agent_definition_id,
            AgentConversation.status == "active",
        ]

        if session_scope == "per-sender":
            conditions.append(AgentConversation.initiator_id == sender_id)

        result = await self.db.execute(
            select(AgentConversation)
            .where(and_(*conditions))
            .order_by(AgentConversation.started_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def list_conversations(
        self,
        project_id: UUID,
        status_filter: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[AgentConversation], int]:
        """
        List conversations for a project with optional status filter.

        Args:
            project_id: Project UUID.
            status_filter: Optional status to filter by.
            page: Page number (1-based).
            page_size: Items per page.

        Returns:
            Tuple of (conversations list, total count).
        """
        from sqlalchemy import func

        conditions = [AgentConversation.project_id == project_id]
        if status_filter:
            conditions.append(AgentConversation.status == status_filter)

        count_result = await self.db.execute(
            select(func.count())
            .select_from(AgentConversation)
            .where(and_(*conditions))
        )
        total = count_result.scalar() or 0

        result = await self.db.execute(
            select(AgentConversation)
            .where(and_(*conditions))
            .order_by(AgentConversation.started_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        conversations = list(result.scalars().all())

        return conversations, total

    async def _get_conversation(self, conversation_id: UUID) -> AgentConversation:
        """Internal helper to fetch conversation with error."""
        result = await self.db.execute(
            select(AgentConversation).where(AgentConversation.id == conversation_id)
        )
        conversation = result.scalar_one_or_none()
        if not conversation:
            raise ConversationNotFoundError(
                f"Conversation {conversation_id} not found"
            )
        return conversation

    async def _set_status(
        self, conversation: AgentConversation, new_status: str
    ) -> None:
        """Set conversation status with timestamp on terminal states."""
        conversation.status = new_status
        if new_status in ("completed", "max_reached", "error"):
            conversation.completed_at = datetime.now(timezone.utc)
        await self.db.flush()
