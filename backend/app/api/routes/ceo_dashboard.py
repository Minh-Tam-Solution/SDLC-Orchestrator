"""
=========================================================================
CEO Dashboard API Routes - Executive Governance Intelligence
SDLC Orchestrator - Sprint 110 (CEO Dashboard & Observability)

Version: 1.0.0
Date: January 27, 2026
Status: ACTIVE - Sprint 110 Day 1
Authority: CTO + Backend Lead Approved
Framework: SDLC 5.3.0 Quality Assurance System

Endpoints:
- GET /ceo-dashboard/summary - Complete dashboard summary
- GET /ceo-dashboard/time-saved - Time saved metrics
- GET /ceo-dashboard/routing-breakdown - PR routing breakdown
- GET /ceo-dashboard/pending-decisions - Pending CEO decisions queue
- GET /ceo-dashboard/weekly-summary - Weekly governance summary
- GET /ceo-dashboard/trends/time-saved - Time saved trend (8 weeks)
- GET /ceo-dashboard/trends/vibecoding-index - Vibecoding index trend (7 days)
- GET /ceo-dashboard/top-rejections - Top rejection reasons
- GET /ceo-dashboard/overrides - CEO overrides this week
- POST /ceo-dashboard/decisions/{submission_id}/resolve - Resolve decision
- POST /ceo-dashboard/decisions/{submission_id}/override - Record override
- GET /ceo-dashboard/health - Dashboard health check

Zero Mock Policy: Real metrics aggregation
=========================================================================
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.services.governance.ceo_dashboard import (
    CEODashboardService,
    TimeRange,
    get_ceo_dashboard_service,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ceo-dashboard")


# ============================================================================
# Request/Response Models
# ============================================================================


class TimeSavedResponse(BaseModel):
    """Response model for time saved metrics."""

    baseline_hours: float
    actual_review_hours: float
    time_saved_hours: float
    time_saved_percent: float
    trend: str
    status: str
    target_week: int
    target_hours: float
    on_track: bool
    last_updated: datetime


class RoutingBreakdownResponse(BaseModel):
    """Response model for routing breakdown."""

    total_prs: int
    auto_approved: int
    tech_lead_review: int
    ceo_should_review: int
    ceo_must_review: int
    auto_approval_rate: float
    trend: str
    last_updated: datetime


class PendingDecisionResponse(BaseModel):
    """Response model for pending decision."""

    id: str
    pr_number: int
    pr_title: str
    project_name: str
    project_id: str
    vibecoding_index: float
    category: str
    routing: str
    top_contributors: List[Dict[str, Any]]
    suggested_focus: Optional[Dict[str, Any]]
    submitted_at: datetime
    waiting_hours: float
    submitter: str


class WeeklySummaryResponse(BaseModel):
    """Response model for weekly summary."""

    week_number: int
    week_start: datetime
    week_end: datetime
    compliance_pass_rate: float
    vibecoding_index_avg: float
    false_positive_rate: float
    developer_satisfaction_nps: Optional[float]
    time_saved_hours: float
    total_submissions: int
    total_rejections: int
    ceo_overrides: int
    status: str


class TopRejectionResponse(BaseModel):
    """Response model for top rejection reason."""

    reason: str
    count: int
    percentage: float
    trend: str
    actionable_fix: Optional[str]


class CEOOverrideResponse(BaseModel):
    """Response model for CEO override."""

    id: str
    pr_number: int
    pr_title: str
    project_name: str
    vibecoding_index: float
    original_routing: str
    override_type: str
    reason: Optional[str]
    override_at: datetime
    signal_breakdown: Dict[str, float]
    recommended_weight_adjustment: Optional[Dict[str, float]]


class SystemHealthResponse(BaseModel):
    """Response model for system health."""

    uptime_percent: float
    api_latency_p95_ms: float
    kill_switch_status: str
    overall_status: str
    alerts_active: int
    last_incident: Optional[datetime]


class DashboardSummaryResponse(BaseModel):
    """Complete CEO dashboard summary response."""

    executive_summary: Dict[str, Any]
    weekly_summary: Dict[str, Any]
    trends: Dict[str, Any]
    top_issues: Dict[str, Any]
    system_health: Dict[str, Any]
    pending_decisions: List[Dict[str, Any]]
    metadata: Dict[str, Any]


class ResolveDecisionRequest(BaseModel):
    """Request model for resolving a pending decision."""

    decision: str = Field(..., description="Decision: 'approved' or 'rejected'")
    reason: Optional[str] = Field(None, description="Reason for decision")


class RecordOverrideRequest(BaseModel):
    """Request model for recording a CEO override."""

    override_type: str = Field(..., description="Override type: 'agrees' or 'disagrees'")
    reason: Optional[str] = Field(None, description="Reason for override")
    pr_number: int = Field(..., description="PR number")
    pr_title: str = Field(..., description="PR title")
    project_name: str = Field(..., description="Project name")
    vibecoding_index: float = Field(..., description="Vibecoding index")
    original_routing: str = Field(..., description="Original routing decision")
    signal_breakdown: Optional[Dict[str, float]] = Field(
        None, description="Signal breakdown"
    )


class RecordSubmissionRequest(BaseModel):
    """Request model for recording a governance submission."""

    submission_id: str
    project_id: UUID
    vibecoding_index: float
    routing: str
    status: str
    pr_number: Optional[int] = None
    pr_title: Optional[str] = None
    project_name: Optional[str] = None
    submitter: Optional[str] = None
    rejection_reason: Optional[str] = None
    signal_breakdown: Optional[Dict[str, float]] = None
    top_contributors: Optional[List[Dict[str, Any]]] = None
    suggested_focus: Optional[Dict[str, Any]] = None


# ============================================================================
# Endpoints
# ============================================================================


@router.get(
    "/summary",
    response_model=DashboardSummaryResponse,
    summary="Get complete CEO dashboard summary",
    description="""
    Get complete CEO dashboard summary with all metrics.

    **Includes:**
    - Executive Summary (time saved, routing breakdown, pending count)
    - Weekly Summary (compliance rate, vibecoding avg, false positive rate)
    - Trends (time saved 8 weeks, vibecoding index 7 days)
    - Top Issues (rejection reasons, CEO overrides)
    - System Health (uptime, latency, kill switch status)
    - Pending Decisions queue (Orange/Red PRs)

    **Time Ranges:**
    - today: Today only
    - this_week: Current week (Monday-Sunday)
    - last_7_days: Rolling 7 days
    - last_30_days: Rolling 30 days

    **Target Metrics (per CEO-WORKFLOW-CONTRACT.md):**
    - Time Saved: 40h → 10h by Week 8
    - Auto-Approval Rate: 85% by Week 8
    - Vibecoding Index: <30 average
    - False Positive Rate: <10%
    """,
)
async def get_dashboard_summary(
    project_id: Optional[UUID] = Query(
        None,
        description="Filter by project ID (optional)",
    ),
    time_range: TimeRange = Query(
        TimeRange.THIS_WEEK,
        description="Time range for metrics",
    ),
    service: CEODashboardService = Depends(get_ceo_dashboard_service),
) -> DashboardSummaryResponse:
    """Get complete CEO dashboard summary."""
    try:
        summary = await service.get_dashboard_summary(
            project_id=project_id,
            time_range=time_range,
        )

        logger.info(
            f"CEO Dashboard summary: "
            f"time_saved={summary.time_saved.time_saved_hours:.1f}h, "
            f"pending={summary.pending_decisions_count}"
        )

        return DashboardSummaryResponse(**summary.to_dict())

    except Exception as e:
        logger.error(f"Failed to get dashboard summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get dashboard summary: {str(e)}",
        )


@router.get(
    "/time-saved",
    response_model=TimeSavedResponse,
    summary="Get CEO time saved metrics",
    description="""
    Get CEO time saved metrics vs baseline.

    **Calculation:**
    - Baseline: 40 hours/week (manual governance)
    - Actual: (ceo_should_review × 10min) + (ceo_must_review × 30min)
    - Time Saved: Baseline - Actual

    **Targets (per MONITORING-PLAN.md):**
    - Week 2: 30 hours (-25%)
    - Week 4: 20 hours (-50%)
    - Week 8: 10 hours (-75%)
    """,
)
async def get_time_saved(
    time_range: TimeRange = Query(
        TimeRange.THIS_WEEK,
        description="Time range for calculation",
    ),
    service: CEODashboardService = Depends(get_ceo_dashboard_service),
) -> TimeSavedResponse:
    """Get CEO time saved metrics."""
    try:
        time_saved = await service._calculate_time_saved(time_range)
        return TimeSavedResponse(**time_saved.to_dict())

    except Exception as e:
        logger.error(f"Failed to get time saved metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get time saved metrics: {str(e)}",
        )


@router.get(
    "/routing-breakdown",
    response_model=RoutingBreakdownResponse,
    summary="Get PR routing breakdown",
    description="""
    Get PR routing breakdown by vibecoding index category.

    **Categories:**
    - **Green (0-30)**: Auto-approve (no CEO time needed)
    - **Yellow (31-60)**: Tech Lead review (no CEO time needed)
    - **Orange (61-80)**: CEO should review (~10 min each)
    - **Red (81-100)**: CEO must review (~30 min each)

    **Target:** Auto-approval rate >85% by Week 8
    """,
)
async def get_routing_breakdown(
    project_id: Optional[UUID] = Query(
        None,
        description="Filter by project ID",
    ),
    time_range: TimeRange = Query(
        TimeRange.THIS_WEEK,
        description="Time range for breakdown",
    ),
    service: CEODashboardService = Depends(get_ceo_dashboard_service),
) -> RoutingBreakdownResponse:
    """Get PR routing breakdown."""
    try:
        breakdown = await service._get_routing_breakdown(time_range, project_id)
        return RoutingBreakdownResponse(**breakdown.to_dict())

    except Exception as e:
        logger.error(f"Failed to get routing breakdown: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get routing breakdown: {str(e)}",
        )


@router.get(
    "/pending-decisions",
    response_model=List[PendingDecisionResponse],
    summary="Get pending CEO decisions queue",
    description="""
    Get queue of pending CEO decisions (Orange and Red PRs).

    **Queue Priority:**
    1. Red PRs (index >80) - CEO must review
    2. Orange PRs (index 61-80) - CEO should review

    **Sorted by:** Vibecoding Index (descending), then waiting time

    Returns top 10 for dashboard. Use pagination for full queue.
    """,
)
async def get_pending_decisions(
    project_id: Optional[UUID] = Query(
        None,
        description="Filter by project ID",
    ),
    limit: int = Query(10, ge=1, le=50, description="Maximum decisions to return"),
    service: CEODashboardService = Depends(get_ceo_dashboard_service),
) -> List[PendingDecisionResponse]:
    """Get pending CEO decisions queue."""
    try:
        decisions = await service._get_pending_decisions(project_id)
        return [
            PendingDecisionResponse(**d.to_dict())
            for d in decisions[:limit]
        ]

    except Exception as e:
        logger.error(f"Failed to get pending decisions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get pending decisions: {str(e)}",
        )


@router.get(
    "/weekly-summary",
    response_model=WeeklySummaryResponse,
    summary="Get weekly governance summary",
    description="""
    Get governance summary for current week.

    **Metrics:**
    - Compliance pass rate (first submission success)
    - Vibecoding index average
    - False positive rate (CEO disagrees / total escalations)
    - Developer satisfaction NPS
    - Time saved hours
    - Total submissions and rejections
    - CEO overrides count

    **Health Status:**
    - Excellent: pass_rate ≥70%, index ≤30, false_positive ≤10%
    - Good: pass_rate ≥50%, index ≤60, false_positive ≤15%
    - Warning: pass_rate ≥30% OR index ≤80
    - Critical: Otherwise
    """,
)
async def get_weekly_summary(
    service: CEODashboardService = Depends(get_ceo_dashboard_service),
) -> WeeklySummaryResponse:
    """Get weekly governance summary."""
    try:
        summary = await service._get_weekly_summary()
        return WeeklySummaryResponse(**summary.to_dict())

    except Exception as e:
        logger.error(f"Failed to get weekly summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get weekly summary: {str(e)}",
        )


@router.get(
    "/trends/time-saved",
    summary="Get time saved trend (8 weeks)",
    description="""
    Get time saved trend data for last 8 weeks.

    **Data points:**
    - week: ISO week number
    - week_start: Week start date
    - time_saved_hours: Hours saved that week
    - baseline_hours: Baseline (40h)
    - target_hours: Target for that week

    Used for CEO Dashboard line chart.
    """,
)
async def get_time_saved_trend(
    service: CEODashboardService = Depends(get_ceo_dashboard_service),
) -> List[Dict[str, Any]]:
    """Get time saved trend for last 8 weeks."""
    try:
        trend = await service._get_time_saved_trend()
        return trend

    except Exception as e:
        logger.error(f"Failed to get time saved trend: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get time saved trend: {str(e)}",
        )


@router.get(
    "/trends/vibecoding-index",
    summary="Get vibecoding index trend (7 days)",
    description="""
    Get vibecoding index distribution for last 7 days.

    **Data points:**
    - date: Date string
    - day_name: Day of week
    - average_index: Average vibecoding index
    - count: Number of submissions
    - distribution: Count by index bucket (0-10, 11-20, etc.)

    Used for CEO Dashboard heatmap.
    """,
)
async def get_vibecoding_index_trend(
    project_id: Optional[UUID] = Query(
        None,
        description="Filter by project ID",
    ),
    service: CEODashboardService = Depends(get_ceo_dashboard_service),
) -> List[Dict[str, Any]]:
    """Get vibecoding index trend for last 7 days."""
    try:
        trend = await service._get_vibecoding_index_trend(project_id)
        return trend

    except Exception as e:
        logger.error(f"Failed to get vibecoding index trend: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get vibecoding index trend: {str(e)}",
        )


@router.get(
    "/top-rejections",
    response_model=List[TopRejectionResponse],
    summary="Get top rejection reasons",
    description="""
    Get top 5 rejection reasons with actionable fixes.

    **Each reason includes:**
    - reason: Rejection reason code
    - count: Number of rejections
    - percentage: Percentage of total rejections
    - trend: Trend direction (up/down/stable)
    - actionable_fix: CLI command or steps to fix

    **Common reasons:**
    - missing_ownership: No @owner annotation
    - missing_intent: No intent statement
    - orphan_code: No linked ADR
    - stage_violation: PR doesn't match current stage
    """,
)
async def get_top_rejections(
    project_id: Optional[UUID] = Query(
        None,
        description="Filter by project ID",
    ),
    time_range: TimeRange = Query(
        TimeRange.THIS_WEEK,
        description="Time range for analysis",
    ),
    service: CEODashboardService = Depends(get_ceo_dashboard_service),
) -> List[TopRejectionResponse]:
    """Get top rejection reasons."""
    try:
        rejections = await service._get_top_rejection_reasons(time_range, project_id)
        return [
            TopRejectionResponse(**r.to_dict())
            for r in rejections
        ]

    except Exception as e:
        logger.error(f"Failed to get top rejections: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get top rejections: {str(e)}",
        )


@router.get(
    "/overrides",
    response_model=List[CEOOverrideResponse],
    summary="Get CEO overrides this week",
    description="""
    Get CEO override records for calibration.

    **Override types:**
    - agrees: CEO confirms routing was correct
    - disagrees: CEO disagrees (false positive/negative)

    **Used for:**
    - Tracking false positive rate
    - Signal weight calibration
    - Identifying systematic biases

    **Recommendation:** If disagrees rate >10%, schedule calibration session.
    """,
)
async def get_ceo_overrides(
    service: CEODashboardService = Depends(get_ceo_dashboard_service),
) -> List[CEOOverrideResponse]:
    """Get CEO overrides this week."""
    try:
        overrides = await service._get_ceo_overrides_this_week()
        return [
            CEOOverrideResponse(**o.to_dict())
            for o in overrides
        ]

    except Exception as e:
        logger.error(f"Failed to get CEO overrides: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get CEO overrides: {str(e)}",
        )


@router.get(
    "/system-health",
    response_model=SystemHealthResponse,
    summary="Get system health snapshot",
    description="""
    Get system health snapshot for CEO quick glance.

    **Metrics:**
    - uptime_percent: System uptime (SLO: >99%)
    - api_latency_p95_ms: API latency P95 (SLO: <100ms)
    - kill_switch_status: Current mode (OFF/WARNING/SOFT/FULL)
    - overall_status: excellent/good/warning/critical
    - alerts_active: Number of active alerts
    - last_incident: Timestamp of last incident

    **Kill Switch Status:**
    - OFF: No enforcement (dev mode)
    - WARNING: Log violations only
    - SOFT: Block critical, warn others
    - FULL: Block all violations
    """,
)
async def get_system_health(
    service: CEODashboardService = Depends(get_ceo_dashboard_service),
) -> SystemHealthResponse:
    """Get system health snapshot."""
    try:
        health = await service._get_system_health()
        return SystemHealthResponse(**health.to_dict())

    except Exception as e:
        logger.error(f"Failed to get system health: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get system health: {str(e)}",
        )


@router.post(
    "/decisions/{submission_id}/resolve",
    summary="Resolve pending CEO decision",
    description="""
    Resolve a pending CEO decision.

    **Actions:**
    - Removes from pending queue
    - Updates submission status
    - Records for metrics

    **Decisions:**
    - approved: Approve the PR
    - rejected: Reject the PR
    """,
)
async def resolve_decision(
    submission_id: str,
    request: ResolveDecisionRequest,
    service: CEODashboardService = Depends(get_ceo_dashboard_service),
) -> Dict[str, Any]:
    """Resolve a pending CEO decision."""
    try:
        if request.decision not in ("approved", "rejected"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Decision must be 'approved' or 'rejected'",
            )

        await service.resolve_pending_decision(
            submission_id=submission_id,
            decision=request.decision,
            reason=request.reason,
        )

        logger.info(
            f"CEO resolved decision {submission_id}: {request.decision}"
        )

        return {
            "status": "success",
            "submission_id": submission_id,
            "decision": request.decision,
            "reason": request.reason,
            "resolved_at": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to resolve decision: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resolve decision: {str(e)}",
        )


@router.post(
    "/decisions/{submission_id}/override",
    summary="Record CEO override for calibration",
    description="""
    Record a CEO override for signal calibration.

    **Override Types:**
    - agrees: CEO confirms the routing was correct
    - disagrees: CEO disagrees with the routing (false positive/negative)

    **Calibration Impact:**
    - Tracks false positive rate
    - Generates weight adjustment recommendations
    - Feeds into weekly calibration session

    **Recommendation:**
    - If disagrees rate >10% → Trigger calibration session
    - If specific signal consistently wrong → Adjust weight
    """,
)
async def record_override(
    submission_id: str,
    request: RecordOverrideRequest,
    service: CEODashboardService = Depends(get_ceo_dashboard_service),
) -> Dict[str, Any]:
    """Record a CEO override for calibration."""
    try:
        if request.override_type not in ("agrees", "disagrees"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Override type must be 'agrees' or 'disagrees'",
            )

        await service.record_ceo_override(
            submission_id=submission_id,
            pr_number=request.pr_number,
            pr_title=request.pr_title,
            project_name=request.project_name,
            vibecoding_index=request.vibecoding_index,
            original_routing=request.original_routing,
            override_type=request.override_type,
            reason=request.reason,
            signal_breakdown=request.signal_breakdown,
        )

        logger.info(
            f"CEO override recorded: {submission_id}, type={request.override_type}"
        )

        return {
            "status": "success",
            "submission_id": submission_id,
            "override_type": request.override_type,
            "recorded_at": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to record override: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record override: {str(e)}",
        )


@router.post(
    "/submissions",
    summary="Record governance submission",
    description="""
    Record a governance submission for dashboard metrics.

    Called by governance validation endpoints to feed metrics.

    **Routing Categories:**
    - auto_approve: Green (index 0-30)
    - tech_lead_review: Yellow (index 31-60)
    - ceo_should_review: Orange (index 61-80)
    - ceo_must_review: Red (index 81-100)
    """,
)
async def record_submission(
    request: RecordSubmissionRequest,
    service: CEODashboardService = Depends(get_ceo_dashboard_service),
) -> Dict[str, Any]:
    """Record a governance submission."""
    try:
        await service.record_submission(
            submission_id=request.submission_id,
            project_id=request.project_id,
            vibecoding_index=request.vibecoding_index,
            routing=request.routing,
            status=request.status,
            pr_number=request.pr_number,
            pr_title=request.pr_title,
            project_name=request.project_name,
            submitter=request.submitter,
            rejection_reason=request.rejection_reason,
            signal_breakdown=request.signal_breakdown,
            top_contributors=request.top_contributors,
            suggested_focus=request.suggested_focus,
        )

        return {
            "status": "success",
            "submission_id": request.submission_id,
            "recorded_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to record submission: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record submission: {str(e)}",
        )


@router.get(
    "/health",
    summary="CEO Dashboard health check",
    description="Check health of CEO dashboard service.",
)
async def ceo_dashboard_health(
    service: CEODashboardService = Depends(get_ceo_dashboard_service),
) -> Dict[str, Any]:
    """Health check for CEO dashboard."""
    return {
        "status": "healthy",
        "service": "ceo_dashboard",
        "timestamp": datetime.utcnow().isoformat(),
        "metrics": {
            "submissions_tracked": len(service._submissions),
            "overrides_tracked": len(service._overrides),
            "pending_queue_size": len(service._pending_queue),
        },
    }
