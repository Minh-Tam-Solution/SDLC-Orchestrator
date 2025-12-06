"""
Bug Triage API Routes - Sprint 24 Day 3

Endpoints for automated bug triage:
- Auto-triage feedback items
- Apply triage decisions
- Check SLA status
- Get triage statistics
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.models.feedback import PilotFeedback, FeedbackPriority, FeedbackStatus
from app.models.user import User
from app.services.triage_service import TriageService


router = APIRouter(prefix="/triage", tags=["Triage"])


class TriageRequest(BaseModel):
    """Request to analyze text for triage."""

    title: str
    description: str
    steps_to_reproduce: str | None = None
    actual_behavior: str | None = None


class TriageResponse(BaseModel):
    """Response from auto-triage analysis."""

    suggested_priority: str
    suggested_team: str
    suggested_assignee: str | None
    confidence: float
    keywords_matched: list[str]
    sla_response_hours: float
    sla_resolution_hours: float


class ApplyTriageRequest(BaseModel):
    """Request to apply triage decision."""

    priority: FeedbackPriority


class SLAStatusResponse(BaseModel):
    """SLA status for a feedback item."""

    status: str
    acknowledgment_breached: bool
    response_breached: bool
    resolution_breached: bool
    age_hours: float
    ack_sla_hours: float
    response_sla_hours: float
    resolution_sla_hours: float | None


class TriageStatsResponse(BaseModel):
    """Triage statistics response."""

    by_status: dict[str, int]
    by_priority: dict[str, int]
    untriaged_count: int
    total: int
    triage_rate: float


@router.post("/analyze", response_model=TriageResponse)
async def analyze_for_triage(
    request: TriageRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TriageResponse:
    """
    Analyze text to suggest triage priority and routing.

    This endpoint analyzes the provided text (title, description, etc.)
    and returns suggested priority, team assignment, and SLA information.

    Does not modify any data - use /triage/{id}/apply to apply decisions.
    """
    service = TriageService(db)

    # Create a temporary feedback-like object for analysis
    class TempFeedback:
        title = request.title
        description = request.description
        steps_to_reproduce = request.steps_to_reproduce
        actual_behavior = request.actual_behavior

    result = await service.auto_triage(TempFeedback())

    return TriageResponse(
        suggested_priority=result.suggested_priority.value,
        suggested_team=result.suggested_team,
        suggested_assignee=result.suggested_assignee,
        confidence=result.confidence,
        keywords_matched=result.keywords_matched,
        sla_response_hours=result.sla_response.total_seconds() / 3600,
        sla_resolution_hours=result.sla_resolution.total_seconds() / 3600,
    )


@router.post("/{feedback_id}/auto-triage", response_model=TriageResponse)
async def auto_triage_feedback(
    feedback_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TriageResponse:
    """
    Run auto-triage on an existing feedback item.

    Returns suggested triage without applying it.
    Use /triage/{id}/apply to apply the decision.
    """
    # Get feedback
    result = await db.execute(
        select(PilotFeedback).where(PilotFeedback.id == feedback_id)
    )
    feedback = result.scalar_one_or_none()

    if not feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feedback {feedback_id} not found",
        )

    service = TriageService(db)
    triage_result = await service.auto_triage(feedback)

    return TriageResponse(
        suggested_priority=triage_result.suggested_priority.value,
        suggested_team=triage_result.suggested_team,
        suggested_assignee=triage_result.suggested_assignee,
        confidence=triage_result.confidence,
        keywords_matched=triage_result.keywords_matched,
        sla_response_hours=triage_result.sla_response.total_seconds() / 3600,
        sla_resolution_hours=triage_result.sla_resolution.total_seconds() / 3600,
    )


@router.post("/{feedback_id}/apply")
async def apply_triage_decision(
    feedback_id: UUID,
    request: ApplyTriageRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Apply triage decision to a feedback item.

    Sets the priority and updates status to TRIAGED.
    Requires triage permissions (any authenticated user for pilot).
    """
    service = TriageService(db)

    try:
        feedback = await service.apply_triage(feedback_id, request.priority)
        return {
            "success": True,
            "feedback_id": str(feedback.id),
            "priority": feedback.priority.value,
            "status": feedback.status.value,
            "message": f"Feedback triaged as {request.priority.value}",
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get("/{feedback_id}/sla", response_model=SLAStatusResponse)
async def get_sla_status(
    feedback_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SLAStatusResponse:
    """
    Get SLA status for a feedback item.

    Returns whether SLAs are being met or breached.
    """
    # Get feedback
    result = await db.execute(
        select(PilotFeedback).where(PilotFeedback.id == feedback_id)
    )
    feedback = result.scalar_one_or_none()

    if not feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feedback {feedback_id} not found",
        )

    service = TriageService(db)
    sla_status = await service.get_sla_status(feedback)

    # Handle untriaged case
    if sla_status.get("status") == "not_triaged":
        return SLAStatusResponse(
            status="not_triaged",
            acknowledgment_breached=False,
            response_breached=False,
            resolution_breached=False,
            age_hours=0,
            ack_sla_hours=0,
            response_sla_hours=0,
            resolution_sla_hours=None,
        )

    return SLAStatusResponse(**sla_status)


@router.get("/stats", response_model=TriageStatsResponse)
async def get_triage_statistics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TriageStatsResponse:
    """
    Get overall triage statistics.

    Returns counts by status, priority, and triage rate.
    Used for the triage dashboard.
    """
    service = TriageService(db)
    stats = await service.get_triage_stats()

    return TriageStatsResponse(
        by_status=stats["by_status"],
        by_priority=stats["by_priority"],
        untriaged_count=stats["untriaged_count"],
        total=stats["total"],
        triage_rate=stats["triage_rate"],
    )


@router.get("/sla-breaches")
async def get_sla_breaches(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Get all feedback items with SLA breaches.

    Returns list of items that have breached their SLA.
    """
    service = TriageService(db)

    # Get all non-resolved feedback with priority
    result = await db.execute(
        select(PilotFeedback).where(
            PilotFeedback.priority.isnot(None),
            PilotFeedback.status.notin_([
                FeedbackStatus.RESOLVED,
                FeedbackStatus.CLOSED,
                FeedbackStatus.WONT_FIX,
            ])
        )
    )
    feedbacks = result.scalars().all()

    breaches = []
    for feedback in feedbacks:
        sla_status = await service.get_sla_status(feedback)
        if sla_status.get("status") == "breached":
            breaches.append({
                "feedback_id": str(feedback.id),
                "title": feedback.title,
                "priority": feedback.priority.value if feedback.priority else None,
                "status": feedback.status.value,
                "age_hours": sla_status.get("age_hours"),
                "acknowledgment_breached": sla_status.get("acknowledgment_breached"),
                "response_breached": sla_status.get("response_breached"),
                "resolution_breached": sla_status.get("resolution_breached"),
            })

    return {
        "total_breaches": len(breaches),
        "breaches": breaches,
    }
