"""
Usage Analytics API Routes - Sprint 24 Day 4

Endpoints for tracking and reporting user activity:
- Session management
- Event tracking
- Usage analytics
- Pilot metrics
"""

from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.models.user import User
from app.models.usage_tracking import EventType
from app.services.usage_tracking_service import UsageTrackingService


router = APIRouter(prefix="/analytics", tags=["Analytics"])


# ============================================================================
# Request/Response Models
# ============================================================================


class StartSessionRequest(BaseModel):
    """Request to start a new session."""

    pass  # User agent and IP from request headers


class SessionResponse(BaseModel):
    """Session information response."""

    id: str
    session_token: str
    started_at: datetime
    ended_at: Optional[datetime]
    is_active: bool
    duration_seconds: Optional[int]
    device_type: Optional[str]
    browser: Optional[str]
    os: Optional[str]
    page_views_count: int
    events_count: int


class TrackEventRequest(BaseModel):
    """Request to track an event."""

    event_type: str
    event_name: str
    session_token: Optional[str] = None
    page_url: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    metadata: Optional[dict] = None
    duration_ms: Optional[int] = None


class TrackPageViewRequest(BaseModel):
    """Request to track a page view."""

    page_url: str
    session_token: Optional[str] = None
    referrer_url: Optional[str] = None


class TrackFeatureRequest(BaseModel):
    """Request to track feature usage."""

    feature_name: str
    session_token: Optional[str] = None
    success: bool = True
    duration_ms: Optional[int] = None
    metadata: Optional[dict] = None


class EventResponse(BaseModel):
    """Event tracking response."""

    id: str
    event_type: str
    event_name: str
    timestamp: datetime


class EngagementSummary(BaseModel):
    """Engagement summary response."""

    today_active_users: int
    week_active_users: int
    today_sessions: int
    avg_session_duration_seconds: int
    top_features: list[dict]


class PilotMetricsResponse(BaseModel):
    """Pilot metrics response."""

    date: datetime
    total_users: int
    active_users: int
    total_sessions: int
    avg_session_duration: int
    total_page_views: int
    users_using_gates: int
    users_using_evidence: int
    users_using_compliance: int
    gates_evaluated: int
    evidence_uploaded: int
    compliance_scans: int
    feedback_submitted: int
    bugs_reported: int
    features_requested: int


class UserActivityResponse(BaseModel):
    """User activity response."""

    events: list[dict]
    total_count: int


# ============================================================================
# Session Endpoints
# ============================================================================


@router.post("/sessions/start", response_model=SessionResponse)
async def start_session(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SessionResponse:
    """
    Start a new user session.

    Automatically captures user agent and IP address from request.
    Returns session token for subsequent event tracking.
    """
    service = UsageTrackingService(db)

    user_agent = request.headers.get("user-agent")
    ip_address = request.client.host if request.client else None

    session = await service.start_session(
        user_id=current_user.id,
        user_agent=user_agent,
        ip_address=ip_address,
    )

    return SessionResponse(
        id=str(session.id),
        session_token=session.session_token,
        started_at=session.started_at,
        ended_at=session.ended_at,
        is_active=session.is_active,
        duration_seconds=session.duration_seconds,
        device_type=session.device_type,
        browser=session.browser,
        os=session.os,
        page_views_count=session.page_views_count or 0,
        events_count=session.events_count or 0,
    )


@router.post("/sessions/{session_id}/end", response_model=SessionResponse)
async def end_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SessionResponse:
    """
    End a user session.

    Calculates total session duration and marks session as inactive.
    """
    service = UsageTrackingService(db)

    session = await service.end_session(session_id)

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )

    return SessionResponse(
        id=str(session.id),
        session_token=session.session_token,
        started_at=session.started_at,
        ended_at=session.ended_at,
        is_active=session.is_active,
        duration_seconds=session.duration_seconds,
        device_type=session.device_type,
        browser=session.browser,
        os=session.os,
        page_views_count=session.page_views_count or 0,
        events_count=session.events_count or 0,
    )


@router.get("/sessions/active", response_model=Optional[SessionResponse])
async def get_active_session(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Optional[SessionResponse]:
    """Get the current active session for the authenticated user."""
    service = UsageTrackingService(db)

    session = await service.get_active_session(current_user.id)

    if not session:
        return None

    return SessionResponse(
        id=str(session.id),
        session_token=session.session_token,
        started_at=session.started_at,
        ended_at=session.ended_at,
        is_active=session.is_active,
        duration_seconds=session.duration_seconds,
        device_type=session.device_type,
        browser=session.browser,
        os=session.os,
        page_views_count=session.page_views_count or 0,
        events_count=session.events_count or 0,
    )


# ============================================================================
# Event Tracking Endpoints
# ============================================================================


@router.post("/events", response_model=EventResponse)
async def track_event(
    request: TrackEventRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EventResponse:
    """
    Track a usage event.

    Generic event tracking for any type of user activity.
    For specific events, use dedicated endpoints (page views, features).
    """
    service = UsageTrackingService(db)

    # Get session ID from token if provided
    session_id = None
    if request.session_token:
        session = await service.get_active_session(current_user.id)
        if session and session.session_token == request.session_token:
            session_id = session.id

    resource_id = UUID(request.resource_id) if request.resource_id else None

    event = await service.track_event(
        user_id=current_user.id,
        session_id=session_id,
        event_type=request.event_type,
        event_name=request.event_name,
        page_url=request.page_url,
        resource_type=request.resource_type,
        resource_id=resource_id,
        metadata=request.metadata,
        duration_ms=request.duration_ms,
    )

    return EventResponse(
        id=str(event.id),
        event_type=event.event_type,
        event_name=event.event_name,
        timestamp=event.timestamp,
    )


@router.post("/events/page-view", response_model=EventResponse)
async def track_page_view(
    request: TrackPageViewRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EventResponse:
    """Track a page view event."""
    service = UsageTrackingService(db)

    # Get session ID from token if provided
    session_id = None
    if request.session_token:
        session = await service.get_active_session(current_user.id)
        if session and session.session_token == request.session_token:
            session_id = session.id

    event = await service.track_page_view(
        user_id=current_user.id,
        session_id=session_id,
        page_url=request.page_url,
        referrer_url=request.referrer_url,
    )

    return EventResponse(
        id=str(event.id),
        event_type=event.event_type,
        event_name=event.event_name,
        timestamp=event.timestamp,
    )


@router.post("/events/feature", response_model=EventResponse)
async def track_feature_use(
    request: TrackFeatureRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EventResponse:
    """Track feature usage event."""
    service = UsageTrackingService(db)

    # Get session ID from token if provided
    session_id = None
    if request.session_token:
        session = await service.get_active_session(current_user.id)
        if session and session.session_token == request.session_token:
            session_id = session.id

    event = await service.track_feature_use(
        user_id=current_user.id,
        session_id=session_id,
        feature_name=request.feature_name,
        success=request.success,
        duration_ms=request.duration_ms,
        metadata=request.metadata,
    )

    return EventResponse(
        id=str(event.id),
        event_type=event.event_type,
        event_name=event.event_name,
        timestamp=event.timestamp,
    )


# ============================================================================
# Analytics Endpoints
# ============================================================================


@router.get("/my-activity", response_model=UserActivityResponse)
async def get_my_activity(
    days: int = 7,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserActivityResponse:
    """
    Get the current user's recent activity.

    Returns events from the last N days (default 7).
    """
    service = UsageTrackingService(db)

    start_date = datetime.utcnow() - timedelta(days=days)

    events = await service.get_user_activity(
        user_id=current_user.id,
        start_date=start_date,
        limit=limit,
    )

    return UserActivityResponse(
        events=[
            {
                "id": str(e.id),
                "event_type": e.event_type,
                "event_name": e.event_name,
                "timestamp": e.timestamp.isoformat(),
                "page_url": e.page_url,
                "resource_type": e.resource_type,
                "resource_id": str(e.resource_id) if e.resource_id else None,
            }
            for e in events
        ],
        total_count=len(events),
    )


@router.get("/engagement", response_model=EngagementSummary)
async def get_engagement_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EngagementSummary:
    """
    Get engagement summary for dashboard.

    Returns today's and this week's metrics.
    """
    service = UsageTrackingService(db)

    summary = await service.get_engagement_summary()

    return EngagementSummary(**summary)


@router.get("/features", response_model=dict)
async def get_feature_usage(
    days: int = 7,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Get feature usage statistics.

    Returns aggregated feature usage for the last N days.
    """
    service = UsageTrackingService(db)

    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    stats = await service.get_feature_usage_stats(start_date, end_date)

    return {
        "period_days": days,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "features": stats,
    }


@router.get("/pilot-metrics", response_model=list[PilotMetricsResponse])
async def get_pilot_metrics(
    days: int = 7,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[PilotMetricsResponse]:
    """
    Get pilot program metrics for dashboard.

    Returns daily metrics for the last N days.
    """
    service = UsageTrackingService(db)

    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    metrics = await service.get_pilot_metrics_range(start_date, end_date)

    return [
        PilotMetricsResponse(
            date=m.date,
            total_users=m.total_users,
            active_users=m.active_users,
            total_sessions=m.total_sessions,
            avg_session_duration=m.avg_session_duration,
            total_page_views=m.total_page_views,
            users_using_gates=m.users_using_gates,
            users_using_evidence=m.users_using_evidence,
            users_using_compliance=m.users_using_compliance,
            gates_evaluated=m.gates_evaluated,
            evidence_uploaded=m.evidence_uploaded,
            compliance_scans=m.compliance_scans,
            feedback_submitted=m.feedback_submitted,
            bugs_reported=m.bugs_reported,
            features_requested=m.features_requested,
        )
        for m in metrics
    ]


@router.post("/pilot-metrics/calculate")
async def calculate_today_metrics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Manually trigger pilot metrics calculation for today.

    This is typically done by a scheduled job, but can be triggered manually.
    """
    service = UsageTrackingService(db)

    metrics = await service.calculate_pilot_metrics(datetime.utcnow())

    return {
        "success": True,
        "date": metrics.date.isoformat(),
        "active_users": metrics.active_users,
        "total_sessions": metrics.total_sessions,
        "message": "Pilot metrics calculated successfully",
    }
