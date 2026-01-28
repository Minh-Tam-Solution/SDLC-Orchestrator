"""
VibecodingService - Core business logic for Anti-Vibecoding Quality Assurance System

SPEC-0001: Anti-Vibecoding Quality Assurance System
- 5-signal vibecoding index calculation
- Progressive routing (GREEN/YELLOW/ORANGE/RED)
- Kill switch monitoring
- Historical trend analysis

Sprint: 118 (Jan 28 - Feb 7, 2026)
Phase: Phase 2 Part 2 - Service Classes
Authority: CTO + CEO Approved
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.governance_vibecoding import (
    VibecodingSignal,
    VibecodingIndexHistory,
    ProgressiveRoutingRule,
    KillSwitchTrigger,
    KillSwitchEvent,
)
from app.models.project import Project


class VibecodingIndexCalculationError(Exception):
    """Raised when vibecoding index calculation fails."""
    pass


class KillSwitchTriggeredError(Exception):
    """Raised when a kill switch is triggered."""
    pass


class VibecodingService:
    """
    Service for Anti-Vibecoding Quality Assurance System.

    Core Responsibilities:
    1. Calculate vibecoding index from 5 signals
    2. Determine routing zone and action
    3. Monitor kill switch triggers
    4. Store and query index history

    SPEC-0001 Implementation:
    - 5 Signals with weighted formula
    - 4 Progressive routing zones
    - 3 Kill switch triggers
    - Immutable audit trail
    """

    # Signal weights (SPEC-0001)
    SIGNAL_WEIGHTS = {
        "intent_clarity": 0.30,        # 30% - How clear is the intent?
        "code_ownership": 0.25,        # 25% - Who owns this code?
        "context_completeness": 0.20,  # 20% - Is context sufficient?
        "ai_attestation": 0.15,        # 15% - Is AI-generated code attested?
        "rejection_rate": 0.10,        # 10% - Historical rejection rate
    }

    # Zone thresholds (default, overridable by ProgressiveRoutingRule)
    ZONE_THRESHOLDS = {
        "GREEN": (0, 20),      # 0-19: AUTO_MERGE
        "YELLOW": (20, 40),    # 20-39: HUMAN_REVIEW
        "ORANGE": (40, 60),    # 40-59: SENIOR_REVIEW
        "RED": (60, 100),      # 60-100: BLOCK
    }

    def __init__(self, db: AsyncSession):
        """
        Initialize VibecodingService.

        Args:
            db: Async database session
        """
        self.db = db

    async def calculate_index(
        self,
        project_id: UUID,
        submission_id: str,
        intent_clarity: int,
        code_ownership: int,
        context_completeness: int,
        ai_attestation: bool,
        rejection_rate: float,
        evidence: Optional[Dict] = None,
    ) -> Dict:
        """
        Calculate vibecoding index from 5 signals.

        SPEC-0001 Formula:
        index = (
            (100 - intent_clarity) * 0.30 +
            (100 - code_ownership) * 0.25 +
            (100 - context_completeness) * 0.20 +
            (0 if ai_attestation else 100) * 0.15 +
            (rejection_rate * 100) * 0.10
        )

        Args:
            project_id: Project UUID
            submission_id: Unique submission identifier (PR number, commit SHA)
            intent_clarity: Intent clarity score (0-100, higher is better)
            code_ownership: Code ownership score (0-100, higher is better)
            context_completeness: Context completeness score (0-100, higher is better)
            ai_attestation: Whether AI-generated code is attested (True/False)
            rejection_rate: Historical rejection rate (0.0-1.0)
            evidence: Optional evidence supporting signal values

        Returns:
            Dict with keys:
            - index_score: Calculated index (0-100)
            - zone: Zone (GREEN/YELLOW/ORANGE/RED)
            - routing_decision: Routing action (AUTO_MERGE/HUMAN_REVIEW/SENIOR_REVIEW/BLOCK)
            - signal_breakdown: Breakdown of 5 signals
            - sla_minutes: SLA for review (if applicable)
            - escalation_enabled: Whether escalation is enabled

        Raises:
            VibecodingIndexCalculationError: If calculation fails
            ValueError: If signal values are out of range
        """
        # Validate signal values
        self._validate_signals(
            intent_clarity,
            code_ownership,
            context_completeness,
            ai_attestation,
            rejection_rate,
        )

        # Calculate weighted index
        intent_score = (100 - intent_clarity) * self.SIGNAL_WEIGHTS["intent_clarity"]
        ownership_score = (100 - code_ownership) * self.SIGNAL_WEIGHTS["code_ownership"]
        context_score = (100 - context_completeness) * self.SIGNAL_WEIGHTS["context_completeness"]
        attestation_score = (0 if ai_attestation else 100) * self.SIGNAL_WEIGHTS["ai_attestation"]
        rejection_score = (rejection_rate * 100) * self.SIGNAL_WEIGHTS["rejection_rate"]

        index_score = int(
            intent_score + ownership_score + context_score + attestation_score + rejection_score
        )

        # Clamp to 0-100 range (defensive programming)
        index_score = max(0, min(100, index_score))

        # Store individual signals
        await self._store_signals(
            project_id=project_id,
            submission_id=submission_id,
            signals={
                "intent_clarity": intent_clarity,
                "code_ownership": code_ownership,
                "context_completeness": context_completeness,
                "ai_attestation": 100 if ai_attestation else 0,  # Convert bool to 0-100
                "rejection_rate": int(rejection_rate * 100),
            },
            evidence=evidence,
        )

        # Determine zone and routing
        zone, routing_decision, sla_minutes, escalation_enabled, escalation_target = (
            await self._determine_routing(index_score)
        )

        # Build signal breakdown
        signal_breakdown = {
            "intent_clarity": {
                "value": intent_clarity,
                "weight": self.SIGNAL_WEIGHTS["intent_clarity"],
                "contribution": intent_score,
            },
            "code_ownership": {
                "value": code_ownership,
                "weight": self.SIGNAL_WEIGHTS["code_ownership"],
                "contribution": ownership_score,
            },
            "context_completeness": {
                "value": context_completeness,
                "weight": self.SIGNAL_WEIGHTS["context_completeness"],
                "contribution": context_score,
            },
            "ai_attestation": {
                "value": ai_attestation,
                "weight": self.SIGNAL_WEIGHTS["ai_attestation"],
                "contribution": attestation_score,
            },
            "rejection_rate": {
                "value": rejection_rate,
                "weight": self.SIGNAL_WEIGHTS["rejection_rate"],
                "contribution": rejection_score,
            },
        }

        # Store index history (immutable audit trail)
        index_history = VibecodingIndexHistory(
            project_id=project_id,
            submission_id=submission_id,
            index_score=index_score,
            zone=zone,
            routing_decision=routing_decision,
            signal_breakdown=signal_breakdown,
        )
        self.db.add(index_history)
        await self.db.commit()
        await self.db.refresh(index_history)

        # Check kill switch triggers
        await self._check_kill_switch_triggers(project_id, index_score)

        return {
            "index_score": index_score,
            "zone": zone,
            "routing_decision": routing_decision,
            "signal_breakdown": signal_breakdown,
            "sla_minutes": sla_minutes,
            "escalation_enabled": escalation_enabled,
            "escalation_target": escalation_target,
            "history_id": str(index_history.id),
            "calculated_at": index_history.calculated_at.isoformat(),
        }

    async def get_index_history(
        self,
        project_id: UUID,
        submission_id: Optional[str] = None,
        zone: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[VibecodingIndexHistory]:
        """
        Get vibecoding index history with optional filters.

        Args:
            project_id: Project UUID
            submission_id: Optional submission filter
            zone: Optional zone filter (GREEN/YELLOW/ORANGE/RED)
            start_date: Optional start date filter
            end_date: Optional end date filter
            limit: Maximum number of records to return

        Returns:
            List of VibecodingIndexHistory records
        """
        query = select(VibecodingIndexHistory).where(
            VibecodingIndexHistory.project_id == project_id
        )

        if submission_id:
            query = query.where(VibecodingIndexHistory.submission_id == submission_id)

        if zone:
            query = query.where(VibecodingIndexHistory.zone == zone)

        if start_date:
            query = query.where(VibecodingIndexHistory.calculated_at >= start_date)

        if end_date:
            query = query.where(VibecodingIndexHistory.calculated_at <= end_date)

        query = query.order_by(VibecodingIndexHistory.calculated_at.desc()).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_zone_statistics(
        self,
        project_id: UUID,
        days: int = 30,
    ) -> Dict[str, int]:
        """
        Get zone distribution statistics for a project.

        Args:
            project_id: Project UUID
            days: Number of days to analyze (default: 30)

        Returns:
            Dict with zone counts:
            {
                "GREEN": 45,
                "YELLOW": 30,
                "ORANGE": 15,
                "RED": 10,
                "total": 100
            }
        """
        start_date = datetime.utcnow() - timedelta(days=days)

        query = (
            select(
                VibecodingIndexHistory.zone,
                func.count(VibecodingIndexHistory.id).label("count"),
            )
            .where(
                and_(
                    VibecodingIndexHistory.project_id == project_id,
                    VibecodingIndexHistory.calculated_at >= start_date,
                )
            )
            .group_by(VibecodingIndexHistory.zone)
        )

        result = await self.db.execute(query)
        zone_counts = {row.zone: row.count for row in result}

        # Ensure all zones present (even with 0 count)
        statistics = {
            "GREEN": zone_counts.get("GREEN", 0),
            "YELLOW": zone_counts.get("YELLOW", 0),
            "ORANGE": zone_counts.get("ORANGE", 0),
            "RED": zone_counts.get("RED", 0),
        }
        statistics["total"] = sum(statistics.values())

        return statistics

    async def get_trend_analysis(
        self,
        project_id: UUID,
        days: int = 30,
    ) -> Dict:
        """
        Get trend analysis for vibecoding index over time.

        Args:
            project_id: Project UUID
            days: Number of days to analyze (default: 30)

        Returns:
            Dict with trend metrics:
            {
                "average_index": 35.5,
                "median_index": 32.0,
                "trend_direction": "improving",  # improving, stable, degrading
                "zone_distribution": {...},
                "daily_averages": [...]
            }
        """
        start_date = datetime.utcnow() - timedelta(days=days)

        query = select(VibecodingIndexHistory).where(
            and_(
                VibecodingIndexHistory.project_id == project_id,
                VibecodingIndexHistory.calculated_at >= start_date,
            )
        ).order_by(VibecodingIndexHistory.calculated_at)

        result = await self.db.execute(query)
        records = list(result.scalars().all())

        if not records:
            return {
                "average_index": 0.0,
                "median_index": 0.0,
                "trend_direction": "unknown",
                "zone_distribution": await self.get_zone_statistics(project_id, days),
                "daily_averages": [],
            }

        # Calculate average and median
        scores = [r.index_score for r in records]
        average_index = sum(scores) / len(scores)
        sorted_scores = sorted(scores)
        median_index = sorted_scores[len(sorted_scores) // 2]

        # Determine trend (compare first half vs second half)
        mid_point = len(scores) // 2
        first_half_avg = sum(scores[:mid_point]) / mid_point if mid_point > 0 else 0
        second_half_avg = sum(scores[mid_point:]) / (len(scores) - mid_point) if len(scores) > mid_point else 0

        if second_half_avg < first_half_avg - 5:
            trend_direction = "improving"  # Lower index is better
        elif second_half_avg > first_half_avg + 5:
            trend_direction = "degrading"
        else:
            trend_direction = "stable"

        # Get zone distribution
        zone_distribution = await self.get_zone_statistics(project_id, days)

        return {
            "average_index": round(average_index, 2),
            "median_index": round(median_index, 2),
            "trend_direction": trend_direction,
            "zone_distribution": zone_distribution,
            "record_count": len(records),
            "date_range": {
                "start": start_date.isoformat(),
                "end": datetime.utcnow().isoformat(),
            },
        }

    async def check_kill_switch_status(
        self,
        project_id: UUID,
    ) -> Dict:
        """
        Check current kill switch status for a project.

        Returns:
            Dict with kill switch status:
            {
                "active_triggers": [...],
                "recent_events": [...],
                "health_status": "healthy"  # healthy, warning, critical
            }
        """
        # Get enabled triggers
        query = select(KillSwitchTrigger).where(
            KillSwitchTrigger.enabled == True  # noqa: E712
        )
        result = await self.db.execute(query)
        triggers = list(result.scalars().all())

        # Get recent events (last 24 hours)
        start_date = datetime.utcnow() - timedelta(hours=24)
        events_query = (
            select(KillSwitchEvent)
            .where(KillSwitchEvent.triggered_at >= start_date)
            .order_by(KillSwitchEvent.triggered_at.desc())
            .limit(10)
        )
        events_result = await self.db.execute(events_query)
        recent_events = list(events_result.scalars().all())

        # Determine health status
        unresolved_critical = [
            e for e in recent_events
            if e.severity == "critical" and e.resolved_at is None
        ]

        if unresolved_critical:
            health_status = "critical"
        elif len([e for e in recent_events if e.resolved_at is None]) > 0:
            health_status = "warning"
        else:
            health_status = "healthy"

        return {
            "active_triggers": [
                {
                    "id": str(t.id),
                    "name": t.trigger_name,
                    "metric": t.metric_name,
                    "threshold": t.threshold_value,
                    "operator": t.threshold_operator,
                    "window_minutes": t.window_minutes,
                    "action": t.action,
                    "severity": t.severity,
                }
                for t in triggers
            ],
            "recent_events": [
                {
                    "id": str(e.id),
                    "triggered_at": e.triggered_at.isoformat(),
                    "metric_value": e.metric_value,
                    "action_taken": e.action_taken,
                    "severity": e.severity,
                    "resolved": e.resolved_at is not None,
                    "resolved_at": e.resolved_at.isoformat() if e.resolved_at else None,
                }
                for e in recent_events
            ],
            "health_status": health_status,
            "unresolved_count": len([e for e in recent_events if e.resolved_at is None]),
        }

    # Private helper methods

    def _validate_signals(
        self,
        intent_clarity: int,
        code_ownership: int,
        context_completeness: int,
        ai_attestation: bool,
        rejection_rate: float,
    ):
        """Validate signal values are within acceptable ranges."""
        if not (0 <= intent_clarity <= 100):
            raise ValueError(f"intent_clarity must be 0-100, got {intent_clarity}")

        if not (0 <= code_ownership <= 100):
            raise ValueError(f"code_ownership must be 0-100, got {code_ownership}")

        if not (0 <= context_completeness <= 100):
            raise ValueError(f"context_completeness must be 0-100, got {context_completeness}")

        if not isinstance(ai_attestation, bool):
            raise ValueError(f"ai_attestation must be boolean, got {type(ai_attestation)}")

        if not (0.0 <= rejection_rate <= 1.0):
            raise ValueError(f"rejection_rate must be 0.0-1.0, got {rejection_rate}")

    async def _store_signals(
        self,
        project_id: UUID,
        submission_id: str,
        signals: Dict[str, int],
        evidence: Optional[Dict] = None,
    ):
        """Store individual signal measurements."""
        for signal_type, signal_value in signals.items():
            signal = VibecodingSignal(
                project_id=project_id,
                submission_id=submission_id,
                signal_type=signal_type,
                signal_value=signal_value,
                signal_weight=self.SIGNAL_WEIGHTS.get(signal_type, 0.0),
                evidence=evidence,
            )
            self.db.add(signal)

        await self.db.commit()

    async def _determine_routing(
        self,
        index_score: int,
    ) -> Tuple[str, str, Optional[int], bool, Optional[str]]:
        """
        Determine routing zone and action based on index score.

        Returns:
            Tuple of (zone, routing_decision, sla_minutes, escalation_enabled, escalation_target)
        """
        # Get routing rules from database (allows configuration)
        query = select(ProgressiveRoutingRule).order_by(
            ProgressiveRoutingRule.threshold_min
        )
        result = await self.db.execute(query)
        rules = list(result.scalars().all())

        # Find matching rule
        for rule in rules:
            if rule.threshold_min <= index_score < rule.threshold_max:
                return (
                    rule.zone,
                    rule.routing_action,
                    rule.sla_minutes,
                    rule.escalation_enabled,
                    rule.escalation_target,
                )

        # Fallback to default (RED zone if no rule matches)
        return ("RED", "BLOCK", 60, True, "cto")

    async def _check_kill_switch_triggers(
        self,
        project_id: UUID,
        current_index: int,
    ):
        """Check if any kill switch triggers should be activated."""
        # This is a placeholder for kill switch monitoring
        # In production, this would:
        # 1. Query recent metrics (rejection rate, latency, CVEs)
        # 2. Compare against trigger thresholds
        # 3. Create KillSwitchEvent if triggered
        # 4. Execute configured action (rollback, block, alert)

        # For now, we'll implement basic rejection rate check
        # as an example of kill switch logic

        # Get rejection rate for last 30 minutes
        start_time = datetime.utcnow() - timedelta(minutes=30)
        query = select(VibecodingIndexHistory).where(
            and_(
                VibecodingIndexHistory.project_id == project_id,
                VibecodingIndexHistory.calculated_at >= start_time,
            )
        )
        result = await self.db.execute(query)
        recent_history = list(result.scalars().all())

        if len(recent_history) >= 10:  # Need minimum sample size
            red_zone_count = len([h for h in recent_history if h.zone == "RED"])
            rejection_rate = red_zone_count / len(recent_history)

            # Check if rejection rate trigger threshold breached (>80%)
            if rejection_rate > 0.80:
                # Get trigger configuration
                trigger_query = select(KillSwitchTrigger).where(
                    and_(
                        KillSwitchTrigger.trigger_name == "rejection_rate_high",
                        KillSwitchTrigger.enabled == True,  # noqa: E712
                    )
                )
                trigger_result = await self.db.execute(trigger_query)
                trigger = trigger_result.scalar_one_or_none()

                if trigger:
                    # Create kill switch event
                    event = KillSwitchEvent(
                        trigger_id=trigger.id,
                        metric_value=rejection_rate,
                        threshold_breached=trigger.threshold_value,
                        action_taken=trigger.action,
                        severity=trigger.severity,
                    )
                    self.db.add(event)
                    await self.db.commit()

                    # Raise exception to halt processing
                    raise KillSwitchTriggeredError(
                        f"Kill switch triggered: {trigger.trigger_name} "
                        f"(rejection rate {rejection_rate:.1%} > {trigger.threshold_value:.1%})"
                    )
