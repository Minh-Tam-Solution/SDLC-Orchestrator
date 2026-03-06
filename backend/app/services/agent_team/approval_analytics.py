"""Approval Analytics Service — Sprint 220 (P4 Human-in-the-Loop).

Provides aggregate analytics on approval/rejection decisions:
- get_approval_rate(project_id, days) → ApprovalStats
- get_avg_response_time(project_id, days) → ResponseTimeStats (p50/p95)

Uses PERCENTILE_CONT for accurate percentile calculation (no in-memory approximation).
Scoped by project_id (via conversations → agent_definitions → project_id).

References:
- ADR-072, Sprint 220 Plan S220-04
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import and_, case, cast, func, literal_column, select, text, Float
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_conversation import AgentConversation
from app.models.agent_message import AgentMessage

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ApprovalStats:
    """Approval rate statistics for a project."""
    total: int
    approved: int
    rejected: int
    rate: float  # 0.0 to 1.0


@dataclass(frozen=True)
class ResponseTimeStats:
    """Response time percentiles (in seconds)."""
    p50: float | None
    p95: float | None
    count: int


class ApprovalAnalyticsService:
    """Aggregate analytics for approval/rejection decisions.

    All queries scoped by project_id via the conversation → agent_definition
    chain. Uses conversation.project_id for scoping.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_approval_rate(
        self,
        project_id: UUID,
        days: int = 30,
    ) -> ApprovalStats:
        """Get approval/rejection rate for a project within a time window.

        Scans agent_messages with approval_feedback metadata and
        counts approved vs rejected actions.

        Args:
            project_id: Project ID to scope the query.
            days: Number of days to look back (default 30).

        Returns:
            ApprovalStats with total, approved, rejected counts and rate.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        # Query messages with approval_feedback in metadata
        # Join through conversations to filter by project_id
        result = await self.db.execute(
            select(AgentMessage.metadata_)
            .join(
                AgentConversation,
                AgentMessage.conversation_id == AgentConversation.id,
            )
            .where(
                and_(
                    AgentConversation.project_id == project_id,
                    AgentMessage.message_type == "system",
                    AgentMessage.sender_id == "approval_feedback",
                    AgentMessage.created_at >= cutoff,
                )
            )
        )

        approved = 0
        rejected = 0

        for (meta,) in result.all():
            if not isinstance(meta, dict):
                continue
            feedback = meta.get("approval_feedback", {})
            action = feedback.get("action", "")
            if action == "approved":
                approved += 1
            elif action == "rejected":
                rejected += 1

        total = approved + rejected
        rate = approved / total if total > 0 else 0.0

        logger.debug(
            "TRACE_ANALYTICS: approval_rate project=%s days=%d → "
            "total=%d approved=%d rejected=%d rate=%.2f",
            project_id, days, total, approved, rejected, rate,
        )

        return ApprovalStats(
            total=total,
            approved=approved,
            rejected=rejected,
            rate=round(rate, 4),
        )

    async def get_avg_response_time(
        self,
        project_id: UUID,
        days: int = 30,
    ) -> ResponseTimeStats:
        """Get approval response time percentiles (p50/p95).

        Calculates time between conversation creation and the first
        approval_feedback message. Uses PERCENTILE_CONT for accurate
        percentile computation at the database level.

        Args:
            project_id: Project ID to scope the query.
            days: Number of days to look back (default 30).

        Returns:
            ResponseTimeStats with p50, p95 in seconds, and count.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        # Subquery: first feedback message per conversation
        first_feedback = (
            select(
                AgentMessage.conversation_id,
                func.min(AgentMessage.created_at).label("feedback_at"),
            )
            .join(
                AgentConversation,
                AgentMessage.conversation_id == AgentConversation.id,
            )
            .where(
                and_(
                    AgentConversation.project_id == project_id,
                    AgentMessage.message_type == "system",
                    AgentMessage.sender_id == "approval_feedback",
                    AgentMessage.created_at >= cutoff,
                )
            )
            .group_by(AgentMessage.conversation_id)
            .subquery("first_feedback")
        )

        # Join back to get conversation created_at and compute delta
        # EXTRACT(EPOCH FROM (feedback_at - conv.created_at))
        delta_expr = func.extract(
            "epoch",
            first_feedback.c.feedback_at - AgentConversation.created_at,
        )

        result = await self.db.execute(
            select(
                func.count().label("cnt"),
                func.percentile_cont(0.50).within_group(delta_expr).label("p50"),
                func.percentile_cont(0.95).within_group(delta_expr).label("p95"),
            )
            .select_from(first_feedback)
            .join(
                AgentConversation,
                first_feedback.c.conversation_id == AgentConversation.id,
            )
        )

        row = result.one()
        count = row.cnt or 0
        p50 = round(float(row.p50), 2) if row.p50 is not None else None
        p95 = round(float(row.p95), 2) if row.p95 is not None else None

        logger.debug(
            "TRACE_ANALYTICS: response_time project=%s days=%d → "
            "count=%d p50=%s p95=%s",
            project_id, days, count, p50, p95,
        )

        return ResponseTimeStats(p50=p50, p95=p95, count=count)
