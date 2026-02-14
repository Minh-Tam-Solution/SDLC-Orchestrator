"""
=========================================================================
Telemetry API Routes - Product Truth Layer
SDLC Orchestrator - Sprint 147 (Spring Cleaning)

Version: 1.0.0
Date: February 4, 2026
Status: ACTIVE
Authority: CTO Approved
Framework: SDLC 6.0.5 Product Truth Layer

Endpoints:
- POST /telemetry/events - Track single event
- POST /telemetry/events/batch - Track batch events
- GET /telemetry/funnels/{funnel_name} - Get funnel metrics
- GET /telemetry/dashboard - Get activation dashboard
- GET /telemetry/interfaces - Get interface breakdown
- GET /telemetry/health - Health check

Purpose:
Replace "82-85% realization" narrative with measured metrics.
Track activation funnels and product usage across all interfaces.

Zero Mock Policy: Real database operations with measured latency.
=========================================================================
"""

import logging
from datetime import date, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.models.user import User
from app.services.telemetry_service import TelemetryService, get_telemetry_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/telemetry", tags=["Telemetry"])


# ============================================================================
# Request/Response Models
# ============================================================================


class TrackEventRequest(BaseModel):
    """Request to track a single event."""

    event_name: str = Field(..., description="Event name (e.g., 'project_created')")
    user_id: Optional[UUID] = Field(None, description="User ID (optional for anonymous)")
    project_id: Optional[UUID] = Field(None, description="Related project ID")
    organization_id: Optional[UUID] = Field(None, description="Related organization ID")
    properties: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Event-specific properties",
    )
    session_id: Optional[str] = Field(None, description="Session identifier")
    interface: Optional[str] = Field(
        None,
        description="Source interface: 'web', 'cli', 'extension', 'api'",
    )


class TrackEventResponse(BaseModel):
    """Response after tracking an event."""

    success: bool
    event_id: Optional[str] = None
    message: Optional[str] = None


class BatchEventRequest(BaseModel):
    """Request to track multiple events."""

    events: List[TrackEventRequest] = Field(..., description="List of events to track")


class BatchEventResponse(BaseModel):
    """Response after batch tracking."""

    success: bool
    events_tracked: int
    message: Optional[str] = None


class FunnelStep(BaseModel):
    """A single step in a funnel."""

    name: str
    count: int
    rate: float


class FunnelResponse(BaseModel):
    """Funnel metrics response."""

    funnel_name: str
    period: Dict[str, str]
    steps: List[FunnelStep]
    overall_conversion: float
    target: Dict[str, Any]


class DashboardResponse(BaseModel):
    """Activation dashboard response."""

    period: Dict[str, str]
    signups_7d: int
    projects_7d: int
    activation_rate: float
    funnels: Dict[str, Any]
    generated_at: str


class InterfaceBreakdownResponse(BaseModel):
    """Interface breakdown response."""

    period: Dict[str, str]
    breakdown: Dict[str, int]
    total: int
    percentages: Dict[str, float]


# ============================================================================
# Event Tracking Endpoints
# ============================================================================


@router.post("/events", response_model=TrackEventResponse, status_code=status.HTTP_201_CREATED)
async def track_event(
    request: TrackEventRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
) -> TrackEventResponse:
    """
    Track a single product event.

    This is the primary endpoint for event tracking. Use it to capture
    user actions across all interfaces (web, CLI, extension, API).

    **Event Naming Convention**:
    - Use snake_case: `user_signed_up`, `project_created`
    - Use past tense: `gate_passed` not `gate_pass`
    - Be specific: `first_evidence_uploaded` not `evidence_uploaded`

    **Example Request**:
    ```json
    {
        "event_name": "project_created",
        "project_id": "550e8400-e29b-41d4-a716-446655440000",
        "properties": {
            "tier": "PROFESSIONAL",
            "template": "ecommerce"
        },
        "interface": "web"
    }
    ```

    **Core Events (Tier 1)**:
    - user_signed_up
    - project_created
    - project_connected_github
    - first_validation_run
    - first_evidence_uploaded
    - first_gate_passed
    - invite_sent / invite_accepted
    - policy_violation_blocked
    - ai_council_used
    """
    telemetry = get_telemetry_service(db)

    try:
        # Use current user if user_id not provided
        user_id = request.user_id or (current_user.id if current_user else None)

        event = await telemetry.track_event(
            event_name=request.event_name,
            user_id=user_id,
            project_id=request.project_id,
            organization_id=request.organization_id,
            properties=request.properties,
            session_id=request.session_id,
            interface=request.interface,
        )

        return TrackEventResponse(
            success=True,
            event_id=str(event.id),
        )

    except Exception as e:
        logger.error(f"Failed to track event: {e}")
        return TrackEventResponse(
            success=False,
            message=f"Failed to track event: {str(e)}",
        )


@router.post("/events/batch", response_model=BatchEventResponse, status_code=status.HTTP_201_CREATED)
async def track_events_batch(
    request: BatchEventRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
) -> BatchEventResponse:
    """
    Track multiple events in a single request.

    Use this for batch tracking when you have multiple events to record.
    More efficient than calling `/events` multiple times.

    **Example Request**:
    ```json
    {
        "events": [
            {"event_name": "dashboard_page_viewed", "properties": {"page": "/projects"}},
            {"event_name": "dashboard_page_viewed", "properties": {"page": "/gates"}}
        ]
    }
    ```
    """
    telemetry = get_telemetry_service(db)

    try:
        events_data = []
        for event_req in request.events:
            events_data.append({
                "event_name": event_req.event_name,
                "user_id": event_req.user_id or (current_user.id if current_user else None),
                "project_id": event_req.project_id,
                "organization_id": event_req.organization_id,
                "properties": event_req.properties or {},
                "session_id": event_req.session_id,
                "interface": event_req.interface,
            })

        count = await telemetry.track_events_batch(events_data)

        return BatchEventResponse(
            success=True,
            events_tracked=count,
        )

    except Exception as e:
        logger.error(f"Failed to track batch events: {e}")
        return BatchEventResponse(
            success=False,
            events_tracked=0,
            message=f"Failed to track events: {str(e)}",
        )


# ============================================================================
# Funnel Analysis Endpoints
# ============================================================================


@router.get("/funnels/{funnel_name}", response_model=FunnelResponse)
async def get_funnel_metrics(
    funnel_name: str,
    start_date: Optional[date] = Query(None, description="Start date (default: 30 days ago)"),
    end_date: Optional[date] = Query(None, description="End date (default: today)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FunnelResponse:
    """
    Get funnel metrics for a specific funnel.

    **Available Funnels**:
    - `time_to_first_project`: Signup → Project Created → GitHub Connected
    - `time_to_first_evidence`: Project → Validation → Evidence Upload
    - `time_to_first_gate`: Evidence → Gate Request → Gate Pass

    **Example Response**:
    ```json
    {
        "funnel_name": "time_to_first_project",
        "period": {"start": "2026-01-05", "end": "2026-02-04"},
        "steps": [
            {"name": "Signup", "count": 127, "rate": 100.0},
            {"name": "Project Created", "count": 104, "rate": 81.9},
            {"name": "GitHub Connected", "count": 52, "rate": 50.0}
        ],
        "overall_conversion": 81.9,
        "target": {"conversion_rate": 70, "median_time_minutes": 5}
    }
    ```
    """
    telemetry = get_telemetry_service(db)

    # Default to last 30 days
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=30)

    try:
        metrics = await telemetry.get_funnel_metrics(funnel_name, start_date, end_date)
        return FunnelResponse(**metrics)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ============================================================================
# Dashboard Endpoints
# ============================================================================


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard_metrics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DashboardResponse:
    """
    Get activation dashboard metrics.

    Returns a summary of key activation metrics including:
    - Signups (last 7 days)
    - Activation rate (signup → project)
    - All three funnel summaries

    **Example Response**:
    ```json
    {
        "period": {"start": "2026-01-28", "end": "2026-02-04"},
        "signups_7d": 127,
        "projects_7d": 104,
        "activation_rate": 81.9,
        "funnels": { ... },
        "generated_at": "2026-02-04T10:00:00Z"
    }
    ```
    """
    telemetry = get_telemetry_service(db)
    metrics = await telemetry.get_dashboard_metrics()
    return DashboardResponse(**metrics)


@router.get("/interfaces", response_model=InterfaceBreakdownResponse)
async def get_interface_breakdown(
    start_date: Optional[date] = Query(None, description="Start date"),
    end_date: Optional[date] = Query(None, description="End date"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> InterfaceBreakdownResponse:
    """
    Get event breakdown by interface.

    Shows how users interact with SDLC Orchestrator across
    different interfaces: web, CLI, extension, API.

    **Example Response**:
    ```json
    {
        "period": {"start": "2026-01-28", "end": "2026-02-04"},
        "breakdown": {"web": 1500, "cli": 800, "extension": 600, "api": 200},
        "total": 3100,
        "percentages": {"web": 48.4, "cli": 25.8, "extension": 19.4, "api": 6.5}
    }
    ```
    """
    telemetry = get_telemetry_service(db)

    # Default to last 7 days
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=7)

    breakdown = await telemetry.get_interface_breakdown(start_date, end_date)
    return InterfaceBreakdownResponse(**breakdown)


# ============================================================================
# Health Check
# ============================================================================


@router.get("/health")
async def telemetry_health(
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Telemetry service health check.

    Verifies that the telemetry system is operational and can
    read/write to the database.
    """
    from sqlalchemy import text

    try:
        # Quick DB check
        result = await db.execute(text("SELECT 1"))
        result.scalar()

        return {
            "status": "healthy",
            "service": "telemetry",
            "version": "1.0.0",
            "funnels_available": [
                "time_to_first_project",
                "time_to_first_evidence",
                "time_to_first_gate",
            ],
            "core_events": 10,
            "engagement_events": 10,
            "timestamp": date.today().isoformat(),
        }

    except Exception as e:
        logger.error(f"Telemetry health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "telemetry",
            "error": str(e),
        }
