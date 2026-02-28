"""
Bug Triage Service - Sprint 24 Day 3

Provides automated bug triage functionality:
- Priority detection based on keywords
- Component routing
- SLA tracking
- Auto-assignment
"""

import re
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional
from uuid import UUID

from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.feedback import PilotFeedback, FeedbackPriority, FeedbackStatus


class TriageResult:
    """Result of automated triage."""

    def __init__(
        self,
        suggested_priority: FeedbackPriority,
        suggested_team: str,
        suggested_assignee: Optional[str],
        confidence: float,
        keywords_matched: list[str],
        sla_response: timedelta,
        sla_resolution: timedelta,
    ):
        self.suggested_priority = suggested_priority
        self.suggested_team = suggested_team
        self.suggested_assignee = suggested_assignee
        self.confidence = confidence
        self.keywords_matched = keywords_matched
        self.sla_response = sla_response
        self.sla_resolution = sla_resolution

    def to_dict(self) -> dict:
        return {
            "suggested_priority": self.suggested_priority.value,
            "suggested_team": self.suggested_team,
            "suggested_assignee": self.suggested_assignee,
            "confidence": self.confidence,
            "keywords_matched": self.keywords_matched,
            "sla_response_hours": self.sla_response.total_seconds() / 3600,
            "sla_resolution_hours": self.sla_resolution.total_seconds() / 3600,
        }


# Priority detection keywords
PRIORITY_KEYWORDS = {
    FeedbackPriority.P0_CRITICAL: [
        r"can't login",
        r"cannot login",
        r"data loss",
        r"lost data",
        r"security",
        r"vulnerability",
        r"crash",
        r"down",
        r"outage",
        r"500 error",
        r"database",
        r"corruption",
        r"breac[h]",
        r"exploit",
        r"urgent",
        r"emergency",
    ],
    FeedbackPriority.P1_HIGH: [
        r"broken",
        r"not working",
        r"doesn't work",
        r"failing",
        r"failed",
        r"error",
        r"timeout",
        r"slow",
        r"stuck",
        r"blocked",
        r"cannot access",
        r"401",
        r"403",
        r"404",
    ],
    FeedbackPriority.P2_MEDIUM: [
        r"incorrect",
        r"wrong",
        r"missing",
        r"display",
        r"format",
        r"alignment",
        r"layout",
        r"unexpected",
        r"inconsistent",
        r"confusing",
    ],
    FeedbackPriority.P3_LOW: [
        r"typo",
        r"suggestion",
        r"nice to have",
        r"minor",
        r"cosmetic",
        r"would be nice",
        r"improvement",
        r"enhancement",
        r"feature request",
    ],
}

# Component routing rules
COMPONENT_ROUTING = [
    {
        "pattern": r"gate|evaluation|policy|opa",
        "team": "gate-engine",
        "assignee": "backend-lead",
    },
    {
        "pattern": r"evidence|upload|vault|s3|minio|file",
        "team": "evidence-team",
        "assignee": "backend-lead",
    },
    {
        "pattern": r"dashboard|ui|button|page|component|react|frontend",
        "team": "frontend",
        "assignee": "frontend-lead",
    },
    {
        "pattern": r"login|auth|oauth|token|session|password|mfa",
        "team": "security",
        "assignee": "security-lead",
    },
    {
        "pattern": r"api|endpoint|request|response|rest",
        "team": "backend",
        "assignee": "backend-lead",
    },
    {
        "pattern": r"deploy|docker|kubernetes|infra|devops|ci|cd",
        "team": "devops",
        "assignee": "devops-lead",
    },
    {
        "pattern": r"compliance|scan|violation|score",
        "team": "compliance",
        "assignee": "backend-lead",
    },
]

# SLA definitions
SLA_DEFINITIONS = {
    FeedbackPriority.P0_CRITICAL: {
        "acknowledgment": timedelta(minutes=15),
        "first_response": timedelta(minutes=30),
        "resolution": timedelta(hours=4),
    },
    FeedbackPriority.P1_HIGH: {
        "acknowledgment": timedelta(hours=1),
        "first_response": timedelta(hours=2),
        "resolution": timedelta(hours=24),
    },
    FeedbackPriority.P2_MEDIUM: {
        "acknowledgment": timedelta(hours=4),
        "first_response": timedelta(hours=8),
        "resolution": timedelta(days=5),
    },
    FeedbackPriority.P3_LOW: {
        "acknowledgment": timedelta(hours=24),
        "first_response": timedelta(hours=48),
        "resolution": None,  # Backlog, no SLA
    },
}


class TriageService:
    """Service for automated bug triage."""

    def __init__(self, db: AsyncSession):
        self.db = db

    def analyze_text(self, text: str) -> tuple[FeedbackPriority, list[str], float]:
        """
        Analyze text to determine priority based on keywords.

        Args:
            text: Combined title and description text

        Returns:
            Tuple of (priority, matched_keywords, confidence)
        """
        text_lower = text.lower()
        matched_by_priority: dict[FeedbackPriority, list[str]] = {
            p: [] for p in FeedbackPriority
        }

        for priority, keywords in PRIORITY_KEYWORDS.items():
            for keyword in keywords:
                if re.search(keyword, text_lower):
                    matched_by_priority[priority].append(keyword)

        # Determine priority based on matches (highest priority wins)
        for priority in [
            FeedbackPriority.P0_CRITICAL,
            FeedbackPriority.P1_HIGH,
            FeedbackPriority.P2_MEDIUM,
            FeedbackPriority.P3_LOW,
        ]:
            if matched_by_priority[priority]:
                # Confidence based on number of matches
                match_count = len(matched_by_priority[priority])
                confidence = min(0.5 + (match_count * 0.1), 0.95)
                return priority, matched_by_priority[priority], confidence

        # Default to P2 if no keywords matched
        return FeedbackPriority.P2_MEDIUM, [], 0.3

    def determine_component(
        self, text: str
    ) -> tuple[str, Optional[str]]:
        """
        Determine which team/component should handle this bug.

        Args:
            text: Combined title and description text

        Returns:
            Tuple of (team, suggested_assignee)
        """
        text_lower = text.lower()

        for rule in COMPONENT_ROUTING:
            if re.search(rule["pattern"], text_lower):
                return rule["team"], rule["assignee"]

        # Default to general backend team
        return "backend", None

    def get_sla(
        self, priority: FeedbackPriority
    ) -> tuple[timedelta, Optional[timedelta]]:
        """
        Get SLA times for a given priority.

        Args:
            priority: The bug priority

        Returns:
            Tuple of (response_sla, resolution_sla)
        """
        sla = SLA_DEFINITIONS.get(priority, SLA_DEFINITIONS[FeedbackPriority.P2_MEDIUM])
        return sla["first_response"], sla["resolution"]

    async def auto_triage(self, feedback: PilotFeedback) -> TriageResult:
        """
        Perform automated triage on a feedback item.

        Args:
            feedback: The feedback item to triage

        Returns:
            TriageResult with suggested priority, team, and SLAs
        """
        # Combine title and description for analysis
        text = f"{feedback.title} {feedback.description}"
        if feedback.steps_to_reproduce:
            text += f" {feedback.steps_to_reproduce}"
        if feedback.actual_behavior:
            text += f" {feedback.actual_behavior}"

        # Analyze for priority
        priority, keywords, confidence = self.analyze_text(text)

        # Determine component/team
        team, assignee = self.determine_component(text)

        # Get SLAs
        response_sla, resolution_sla = self.get_sla(priority)

        return TriageResult(
            suggested_priority=priority,
            suggested_team=team,
            suggested_assignee=assignee,
            confidence=confidence,
            keywords_matched=keywords,
            sla_response=response_sla,
            sla_resolution=resolution_sla or timedelta(days=30),
        )

    async def apply_triage(
        self,
        feedback_id: UUID,
        priority: FeedbackPriority,
    ) -> PilotFeedback:
        """
        Apply triage decision to a feedback item.

        Args:
            feedback_id: ID of the feedback item
            priority: Priority to set

        Returns:
            Updated feedback item
        """
        result = await self.db.execute(
            select(PilotFeedback).where(PilotFeedback.id == feedback_id)
        )
        feedback = result.scalar_one_or_none()

        if not feedback:
            raise ValueError(f"Feedback {feedback_id} not found")

        feedback.priority = priority
        feedback.status = FeedbackStatus.TRIAGED
        feedback.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(feedback)

        return feedback

    async def get_sla_status(self, feedback: PilotFeedback) -> dict:
        """
        Check SLA status for a feedback item.

        Args:
            feedback: The feedback item

        Returns:
            Dict with SLA status information
        """
        if not feedback.priority:
            return {"status": "not_triaged", "breach": False}

        sla = SLA_DEFINITIONS.get(feedback.priority)
        if not sla:
            return {"status": "unknown", "breach": False}

        now = datetime.utcnow()
        age = now - feedback.created_at

        # Check acknowledgment SLA
        ack_sla = sla["acknowledgment"]
        ack_breached = (
            age > ack_sla and feedback.status == FeedbackStatus.NEW
        )

        # Check response SLA
        response_sla = sla["first_response"]
        response_breached = (
            age > response_sla
            and feedback.status in [FeedbackStatus.NEW, FeedbackStatus.TRIAGED]
        )

        # Check resolution SLA
        resolution_sla = sla["resolution"]
        resolution_breached = False
        if resolution_sla and feedback.status not in [
            FeedbackStatus.RESOLVED,
            FeedbackStatus.CLOSED,
            FeedbackStatus.WONT_FIX,
        ]:
            resolution_breached = age > resolution_sla

        return {
            "status": "ok" if not any([ack_breached, response_breached, resolution_breached]) else "breached",
            "acknowledgment_breached": ack_breached,
            "response_breached": response_breached,
            "resolution_breached": resolution_breached,
            "age_hours": age.total_seconds() / 3600,
            "ack_sla_hours": ack_sla.total_seconds() / 3600,
            "response_sla_hours": response_sla.total_seconds() / 3600,
            "resolution_sla_hours": resolution_sla.total_seconds() / 3600 if resolution_sla else None,
        }

    async def get_triage_stats(self) -> dict:
        """
        Get triage statistics for dashboard.

        Returns:
            Dict with triage statistics
        """
        # Count by status
        status_counts = await self.db.execute(
            select(
                PilotFeedback.status,
                func.count(PilotFeedback.id)
            ).group_by(PilotFeedback.status)
        )
        # row[0] may be a Python enum or a raw string from asyncpg — handle both
        status_stats = {
            (row[0].value if hasattr(row[0], "value") else row[0]): row[1]
            for row in status_counts.all()
        }

        # Count by priority
        priority_counts = await self.db.execute(
            select(
                PilotFeedback.priority,
                func.count(PilotFeedback.id)
            ).where(PilotFeedback.priority.isnot(None))
            .group_by(PilotFeedback.priority)
        )
        priority_stats = {
            (row[0].value if hasattr(row[0], "value") else row[0]): row[1]
            for row in priority_counts.all()
        }

        # Count untriaged (new + no priority)
        # Use text() to bypass SQLEnum bind processor entirely.
        # SQLEnum(FeedbackStatus) sends enum NAMES (e.g. "NEW") but the PostgreSQL
        # enum type was created with lowercase values ("new", "triaged", etc.).
        # PostgreSQL also has no implicit varchar→feedbackstatus operator, so
        # we cast explicitly: 'new'::feedbackstatus.
        untriaged_count = await self.db.execute(
            select(func.count(PilotFeedback.id)).where(
                text("pilot_feedback.status = 'new'::feedbackstatus"),
                PilotFeedback.priority.is_(None)
            )
        )
        untriaged = untriaged_count.scalar() or 0

        # Calculate SLA compliance
        total_with_priority = sum(priority_stats.values())

        return {
            "by_status": status_stats,
            "by_priority": priority_stats,
            "untriaged_count": untriaged,
            "total": total_with_priority + untriaged,
            "triage_rate": (total_with_priority / (total_with_priority + untriaged) * 100)
            if (total_with_priority + untriaged) > 0
            else 0,
        }


async def get_triage_service(db: AsyncSession) -> TriageService:
    """Factory function for TriageService."""
    return TriageService(db)
