"""
Conversation loop guards — 6 limits enforced per ADR-056 Non-Negotiable #9.

Sources:
- TinyClaw: 50-message cap, branch counting
- OpenClaw: Token budget tracking, session scoping
- Nanobot N2: Delegation depth limit (max_delegation_depth)
- Expert Synthesis v2: 6-limit guard spec

Sprint 176-177 P0 implementation.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class LimitViolation(str, Enum):
    """Which limit was violated."""

    MAX_MESSAGES = "max_messages"
    MAX_TOKENS = "max_tokens"
    MAX_TOOL_CALLS = "max_tool_calls"
    TIMEOUT_MINUTES = "timeout_minutes"
    MAX_DIFF_SIZE = "max_diff_size"
    MAX_RETRIES_PER_STEP = "max_retries_per_step"
    MAX_DELEGATION_DEPTH = "max_delegation_depth"
    BUDGET_EXCEEDED = "budget_exceeded"


@dataclass(frozen=True)
class ConversationLimits:
    """
    6 loop guard limits + delegation depth + budget.

    All values are snapshotted from agent_definitions into agent_conversations
    on conversation creation (Snapshot Precedence — ADR-056 Decision 1).
    """

    max_messages: int = 50
    max_tokens: int = 100_000
    max_tool_calls: int = 20
    timeout_minutes: int = 30
    max_diff_size: int = 10_000
    max_retries_per_step: int = 3
    max_delegation_depth: int = 1
    max_budget_cents: int = 1000

    def check_messages(self, total_messages: int) -> LimitViolation | None:
        """Check if message count exceeds limit."""
        if total_messages >= self.max_messages:
            logger.warning(
                "Message limit reached: %d >= %d",
                total_messages,
                self.max_messages,
            )
            return LimitViolation.MAX_MESSAGES
        return None

    def check_tokens(self, total_tokens: int) -> LimitViolation | None:
        """Check if token count exceeds limit."""
        if total_tokens >= self.max_tokens:
            logger.warning(
                "Token limit reached: %d >= %d",
                total_tokens,
                self.max_tokens,
            )
            return LimitViolation.MAX_TOKENS
        return None

    def check_tool_calls(self, tool_call_count: int) -> LimitViolation | None:
        """Check if tool call count exceeds per-message limit."""
        if tool_call_count >= self.max_tool_calls:
            logger.warning(
                "Tool call limit reached: %d >= %d",
                tool_call_count,
                self.max_tool_calls,
            )
            return LimitViolation.MAX_TOOL_CALLS
        return None

    def check_diff_size(self, diff_lines: int) -> LimitViolation | None:
        """Check if code diff size exceeds limit."""
        if diff_lines >= self.max_diff_size:
            logger.warning(
                "Diff size limit reached: %d >= %d lines",
                diff_lines,
                self.max_diff_size,
            )
            return LimitViolation.MAX_DIFF_SIZE
        return None

    def check_retries(self, failed_count: int) -> LimitViolation | None:
        """Check if retry count exceeds per-step limit (dead-letter threshold)."""
        if failed_count >= self.max_retries_per_step:
            logger.warning(
                "Retry limit reached: %d >= %d (dead-letter)",
                failed_count,
                self.max_retries_per_step,
            )
            return LimitViolation.MAX_RETRIES_PER_STEP
        return None

    def check_delegation_depth(
        self, current_depth: int, agent_max_depth: int | None = None
    ) -> LimitViolation | None:
        """
        Check if delegation depth exceeds limit (Nanobot N2).

        Uses agent_max_depth if provided (from agent_definitions),
        otherwise falls back to self.max_delegation_depth (from conversation snapshot).
        """
        effective_max = (
            agent_max_depth if agent_max_depth is not None else self.max_delegation_depth
        )
        if current_depth >= effective_max:
            logger.warning(
                "Delegation depth limit reached: %d >= %d",
                current_depth,
                effective_max,
            )
            return LimitViolation.MAX_DELEGATION_DEPTH
        return None

    def check_budget(self, current_cost_cents: int) -> LimitViolation | None:
        """Check if budget has been exceeded (circuit breaker)."""
        if current_cost_cents >= self.max_budget_cents:
            logger.warning(
                "Budget exceeded: %d >= %d cents",
                current_cost_cents,
                self.max_budget_cents,
            )
            return LimitViolation.BUDGET_EXCEEDED
        return None

    def check_all(
        self,
        total_messages: int = 0,
        total_tokens: int = 0,
        tool_call_count: int = 0,
        diff_lines: int = 0,
        failed_count: int = 0,
        delegation_depth: int = 0,
        current_cost_cents: int = 0,
    ) -> LimitViolation | None:
        """
        Check all limits in priority order. Returns first violation found.

        Returns None if all checks pass.
        """
        checks = [
            self.check_budget(current_cost_cents),
            self.check_messages(total_messages),
            self.check_tokens(total_tokens),
            self.check_tool_calls(tool_call_count),
            self.check_retries(failed_count),
            self.check_diff_size(diff_lines),
            self.check_delegation_depth(delegation_depth),
        ]
        for violation in checks:
            if violation is not None:
                return violation
        return None
