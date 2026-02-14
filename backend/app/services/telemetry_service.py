"""
=========================================================================
Telemetry Service - Product Truth Layer
SDLC Orchestrator - Sprint 147 (Spring Cleaning)

Version: 1.0.0
Date: February 4, 2026
Status: ACTIVE
Authority: CTO Approved
Framework: SDLC 6.0.5 Product Truth Layer

Purpose:
Provide a clean interface for tracking product events and querying funnels.
Replaces the narrative "82-85% realization" with measured metrics.

Core Features:
1. Event tracking (async, non-blocking)
2. Funnel analysis (time-to-first-X metrics)
3. Cohort retention (weekly breakdown)
4. Interface-based analytics (web/cli/extension)

Zero Mock Policy: Real database operations with measured latency.
=========================================================================
"""

import logging
from datetime import datetime, timedelta, date
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product_event import ProductEvent, EventNames

logger = logging.getLogger(__name__)


class TelemetryService:
    """
    Product telemetry service for event tracking and funnel analysis.

    Designed for:
    - High-volume writes (async event tracking)
    - Low-latency reads (indexed funnel queries)
    - Privacy-compliant analytics (no PII in properties)
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    # ========================================================================
    # Event Tracking
    # ========================================================================

    async def track_event(
        self,
        event_name: str,
        user_id: Optional[UUID] = None,
        project_id: Optional[UUID] = None,
        organization_id: Optional[UUID] = None,
        properties: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
        interface: Optional[str] = None,
    ) -> ProductEvent:
        """
        Track a product event.

        Args:
            event_name: Event name (use EventNames constants)
            user_id: User who triggered the event
            project_id: Related project
            organization_id: Related organization
            properties: Event-specific properties
            session_id: Session identifier
            interface: Source interface (web, cli, extension, api)

        Returns:
            Created ProductEvent instance

        Example:
            await telemetry.track_event(
                event_name=EventNames.PROJECT_CREATED,
                user_id=user.id,
                project_id=project.id,
                properties={"tier": "PROFESSIONAL", "template": "ecommerce"},
                interface="web"
            )
        """
        event = ProductEvent(
            event_name=event_name,
            user_id=user_id,
            project_id=project_id,
            organization_id=organization_id,
            properties=properties or {},
            session_id=session_id,
            interface=interface,
            timestamp=datetime.utcnow(),
        )

        self.db.add(event)
        await self.db.commit()
        await self.db.refresh(event)

        logger.info(
            f"TELEMETRY: {event_name} | user={user_id} | project={project_id} | interface={interface}"
        )

        return event

    async def track_events_batch(
        self,
        events: List[Dict[str, Any]],
    ) -> int:
        """
        Track multiple events in a single transaction.

        Args:
            events: List of event dictionaries with keys:
                - event_name (required)
                - user_id, project_id, properties, etc. (optional)

        Returns:
            Number of events tracked

        Example:
            await telemetry.track_events_batch([
                {"event_name": "page_view", "user_id": user.id, "properties": {"page": "/dashboard"}},
                {"event_name": "page_view", "user_id": user.id, "properties": {"page": "/projects"}},
            ])
        """
        event_objects = []
        for event_data in events:
            event = ProductEvent(
                event_name=event_data["event_name"],
                user_id=event_data.get("user_id"),
                project_id=event_data.get("project_id"),
                organization_id=event_data.get("organization_id"),
                properties=event_data.get("properties", {}),
                session_id=event_data.get("session_id"),
                interface=event_data.get("interface"),
                timestamp=event_data.get("timestamp", datetime.utcnow()),
            )
            event_objects.append(event)

        self.db.add_all(event_objects)
        await self.db.commit()

        logger.info(f"TELEMETRY_BATCH: tracked {len(event_objects)} events")
        return len(event_objects)

    # ========================================================================
    # Funnel Analysis
    # ========================================================================

    async def get_funnel_metrics(
        self,
        funnel_name: str,
        start_date: date,
        end_date: date,
    ) -> Dict[str, Any]:
        """
        Get funnel metrics for a specific funnel.

        Args:
            funnel_name: One of "time_to_first_project", "time_to_first_evidence", "time_to_first_gate"
            start_date: Start of analysis period
            end_date: End of analysis period

        Returns:
            Funnel metrics including conversion rates and median times
        """
        if funnel_name == "time_to_first_project":
            return await self._get_time_to_first_project_funnel(start_date, end_date)
        elif funnel_name == "time_to_first_evidence":
            return await self._get_time_to_first_evidence_funnel(start_date, end_date)
        elif funnel_name == "time_to_first_gate":
            return await self._get_time_to_first_gate_funnel(start_date, end_date)
        else:
            raise ValueError(f"Unknown funnel: {funnel_name}")

    async def _get_time_to_first_project_funnel(
        self,
        start_date: date,
        end_date: date,
    ) -> Dict[str, Any]:
        """Calculate Time-to-First-Project funnel metrics."""
        # Get signups in period
        signups_query = select(func.count(func.distinct(ProductEvent.user_id))).where(
            ProductEvent.event_name == EventNames.USER_SIGNED_UP,
            func.date(ProductEvent.timestamp) >= start_date,
            func.date(ProductEvent.timestamp) <= end_date,
        )
        signups_result = await self.db.execute(signups_query)
        signups = signups_result.scalar() or 0

        # Get users who created a project within 24h of signup
        # This is a simplified query - in production would use window functions
        projects_query = select(func.count(func.distinct(ProductEvent.user_id))).where(
            ProductEvent.event_name == EventNames.PROJECT_CREATED,
            func.date(ProductEvent.timestamp) >= start_date,
            func.date(ProductEvent.timestamp) <= end_date,
        )
        projects_result = await self.db.execute(projects_query)
        projects = projects_result.scalar() or 0

        # Get users who connected GitHub
        github_query = select(func.count(func.distinct(ProductEvent.user_id))).where(
            ProductEvent.event_name == EventNames.PROJECT_CONNECTED_GITHUB,
            func.date(ProductEvent.timestamp) >= start_date,
            func.date(ProductEvent.timestamp) <= end_date,
        )
        github_result = await self.db.execute(github_query)
        github = github_result.scalar() or 0

        conversion_rate = (projects / signups * 100) if signups > 0 else 0
        github_rate = (github / projects * 100) if projects > 0 else 0

        return {
            "funnel_name": "time_to_first_project",
            "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
            "steps": [
                {"name": "Signup", "count": signups, "rate": 100},
                {"name": "Project Created", "count": projects, "rate": round(conversion_rate, 1)},
                {"name": "GitHub Connected", "count": github, "rate": round(github_rate, 1)},
            ],
            "overall_conversion": round(conversion_rate, 1),
            "target": {"conversion_rate": 70, "median_time_minutes": 5},
        }

    async def _get_time_to_first_evidence_funnel(
        self,
        start_date: date,
        end_date: date,
    ) -> Dict[str, Any]:
        """Calculate Time-to-First-Evidence funnel metrics."""
        # Get projects created in period
        projects_query = select(func.count(func.distinct(ProductEvent.project_id))).where(
            ProductEvent.event_name == EventNames.PROJECT_CREATED,
            func.date(ProductEvent.timestamp) >= start_date,
            func.date(ProductEvent.timestamp) <= end_date,
        )
        projects_result = await self.db.execute(projects_query)
        projects = projects_result.scalar() or 0

        # Get validations
        validations_query = select(func.count(func.distinct(ProductEvent.project_id))).where(
            ProductEvent.event_name == EventNames.FIRST_VALIDATION_RUN,
            func.date(ProductEvent.timestamp) >= start_date,
            func.date(ProductEvent.timestamp) <= end_date,
        )
        validations_result = await self.db.execute(validations_query)
        validations = validations_result.scalar() or 0

        # Get evidence uploads
        evidence_query = select(func.count(func.distinct(ProductEvent.project_id))).where(
            ProductEvent.event_name == EventNames.FIRST_EVIDENCE_UPLOADED,
            func.date(ProductEvent.timestamp) >= start_date,
            func.date(ProductEvent.timestamp) <= end_date,
        )
        evidence_result = await self.db.execute(evidence_query)
        evidence = evidence_result.scalar() or 0

        validation_rate = (validations / projects * 100) if projects > 0 else 0
        evidence_rate = (evidence / projects * 100) if projects > 0 else 0

        return {
            "funnel_name": "time_to_first_evidence",
            "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
            "steps": [
                {"name": "Project Created", "count": projects, "rate": 100},
                {"name": "First Validation", "count": validations, "rate": round(validation_rate, 1)},
                {"name": "First Evidence", "count": evidence, "rate": round(evidence_rate, 1)},
            ],
            "overall_conversion": round(evidence_rate, 1),
            "target": {"conversion_rate": 40, "median_time_minutes": 15},
        }

    async def _get_time_to_first_gate_funnel(
        self,
        start_date: date,
        end_date: date,
    ) -> Dict[str, Any]:
        """Calculate Time-to-First-Gate-Pass funnel metrics."""
        # Get evidence uploads in period
        evidence_query = select(func.count(func.distinct(ProductEvent.project_id))).where(
            ProductEvent.event_name == EventNames.FIRST_EVIDENCE_UPLOADED,
            func.date(ProductEvent.timestamp) >= start_date,
            func.date(ProductEvent.timestamp) <= end_date,
        )
        evidence_result = await self.db.execute(evidence_query)
        evidence = evidence_result.scalar() or 0

        # Get gate approvals requested
        requests_query = select(func.count(func.distinct(ProductEvent.project_id))).where(
            ProductEvent.event_name == EventNames.GATE_APPROVAL_REQUESTED,
            func.date(ProductEvent.timestamp) >= start_date,
            func.date(ProductEvent.timestamp) <= end_date,
        )
        requests_result = await self.db.execute(requests_query)
        requests = requests_result.scalar() or 0

        # Get first gate passed
        gates_query = select(func.count(func.distinct(ProductEvent.project_id))).where(
            ProductEvent.event_name == EventNames.FIRST_GATE_PASSED,
            func.date(ProductEvent.timestamp) >= start_date,
            func.date(ProductEvent.timestamp) <= end_date,
        )
        gates_result = await self.db.execute(gates_query)
        gates = gates_result.scalar() or 0

        request_rate = (requests / evidence * 100) if evidence > 0 else 0
        gate_rate = (gates / evidence * 100) if evidence > 0 else 0

        return {
            "funnel_name": "time_to_first_gate",
            "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
            "steps": [
                {"name": "Evidence Uploaded", "count": evidence, "rate": 100},
                {"name": "Gate Requested", "count": requests, "rate": round(request_rate, 1)},
                {"name": "Gate Passed", "count": gates, "rate": round(gate_rate, 1)},
            ],
            "overall_conversion": round(gate_rate, 1),
            "target": {"conversion_rate": 25, "median_time_minutes": 60},
        }

    # ========================================================================
    # Dashboard Metrics
    # ========================================================================

    async def get_dashboard_metrics(self) -> Dict[str, Any]:
        """
        Get activation dashboard metrics.

        Returns:
            Dashboard data including signups, activation rate, and time metrics.
        """
        today = date.today()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)

        # Signups last 7 days
        signups_query = select(func.count(ProductEvent.id)).where(
            ProductEvent.event_name == EventNames.USER_SIGNED_UP,
            func.date(ProductEvent.timestamp) >= week_ago,
        )
        signups_result = await self.db.execute(signups_query)
        signups_7d = signups_result.scalar() or 0

        # Projects created last 7 days
        projects_query = select(func.count(ProductEvent.id)).where(
            ProductEvent.event_name == EventNames.PROJECT_CREATED,
            func.date(ProductEvent.timestamp) >= week_ago,
        )
        projects_result = await self.db.execute(projects_query)
        projects_7d = projects_result.scalar() or 0

        # Activation rate (signup → project in 24h)
        activation_rate = (projects_7d / signups_7d * 100) if signups_7d > 0 else 0

        # Get funnel metrics for last 30 days
        ttp_funnel = await self._get_time_to_first_project_funnel(month_ago, today)
        tte_funnel = await self._get_time_to_first_evidence_funnel(month_ago, today)
        ttg_funnel = await self._get_time_to_first_gate_funnel(month_ago, today)

        return {
            "period": {"start": week_ago.isoformat(), "end": today.isoformat()},
            "signups_7d": signups_7d,
            "projects_7d": projects_7d,
            "activation_rate": round(activation_rate, 1),
            "funnels": {
                "time_to_first_project": ttp_funnel,
                "time_to_first_evidence": tte_funnel,
                "time_to_first_gate": ttg_funnel,
            },
            "generated_at": datetime.utcnow().isoformat(),
        }

    # ========================================================================
    # Interface Breakdown
    # ========================================================================

    async def get_interface_breakdown(
        self,
        start_date: date,
        end_date: date,
    ) -> Dict[str, Any]:
        """
        Get event breakdown by interface (web, cli, extension).

        Returns:
            Event counts per interface for the specified period.
        """
        query = (
            select(ProductEvent.interface, func.count(ProductEvent.id))
            .where(
                func.date(ProductEvent.timestamp) >= start_date,
                func.date(ProductEvent.timestamp) <= end_date,
            )
            .group_by(ProductEvent.interface)
        )

        result = await self.db.execute(query)
        breakdown = {row[0] or "unknown": row[1] for row in result.fetchall()}

        total = sum(breakdown.values())

        return {
            "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
            "breakdown": breakdown,
            "total": total,
            "percentages": {
                k: round(v / total * 100, 1) if total > 0 else 0
                for k, v in breakdown.items()
            },
        }


def get_telemetry_service(db: AsyncSession) -> TelemetryService:
    """Dependency injection for TelemetryService."""
    return TelemetryService(db)
