"""
Dogfooding API Routes - Sprint 114 Track 2

Provides endpoints for monitoring WARNING mode dogfooding metrics
and Go/No-Go decision support.
"""

from datetime import date, datetime, timedelta
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.services.governance.mode_service import GovernanceModeService, GovernanceMode

router = APIRouter(prefix="/dogfooding", tags=["dogfooding"])


# ============================================================================
# Request/Response Models
# ============================================================================

class VibecodingDistribution(BaseModel):
    """Vibecoding index distribution across zones."""
    green: int = Field(description="PRs with index 0-30")
    yellow: int = Field(description="PRs with index 31-60")
    orange: int = Field(description="PRs with index 61-80")
    red: int = Field(description="PRs with index 81-100")


class DogfoodingMetricsResponse(BaseModel):
    """Sprint dogfooding metrics response."""
    sprint: str
    mode: str
    start_date: str
    end_date: str
    days_elapsed: int
    total_days: int

    # PR Metrics
    prs_evaluated: int
    prs_target: int

    # Vibecoding Index
    distribution: VibecodingDistribution
    average_index: float

    # Developer Friction
    avg_friction_minutes: float
    friction_target: float

    # Accuracy
    false_positive_rate: float
    false_positive_target: float

    # Team Satisfaction
    team_nps: Optional[float]
    nps_target: float

    # Go/No-Go
    go_no_go_ready: bool
    blockers: list[str]


class PRMetricResponse(BaseModel):
    """Individual PR governance metric."""
    pr_number: int
    title: str
    author: str
    vibecode_index: float
    zone: str
    friction_minutes: float
    auto_gen_used: bool
    timestamp: datetime


class PRMetricsListResponse(BaseModel):
    """List of PR metrics."""
    items: list[PRMetricResponse]
    total: int
    page: int
    page_size: int


class RecordPRMetricRequest(BaseModel):
    """Request to record a PR governance evaluation metric."""
    pr_number: int
    title: str
    author: str
    vibecode_index: float
    zone: str
    friction_minutes: float
    auto_gen_used: bool = False
    file_count: int = 0
    violations: list[str] = []


class GoNoGoDecisionResponse(BaseModel):
    """Go/No-Go decision for next sprint."""
    ready: bool
    checks: list[dict]
    recommendation: str
    blockers: list[str]
    next_sprint: str
    next_mode: str


# ============================================================================
# In-Memory Storage (Sprint 114 POC - Replace with DB in production)
# ============================================================================

# Sprint 114 configuration
SPRINT_114_CONFIG = {
    "sprint": "114",
    "mode": "WARNING",
    "start_date": "2026-02-03",
    "end_date": "2026-02-07",
    "total_days": 5,
    "prs_target": 15,
    "friction_target": 10.0,  # minutes
    "false_positive_target": 20.0,  # percent
    "nps_target": 50.0,
}

# In-memory PR metrics storage
_pr_metrics: list[dict] = []


def _calculate_days_elapsed() -> int:
    """Calculate days elapsed since sprint start."""
    start = datetime.strptime(SPRINT_114_CONFIG["start_date"], "%Y-%m-%d").date()
    today = date.today()
    if today < start:
        return 0
    elapsed = (today - start).days + 1
    return min(elapsed, SPRINT_114_CONFIG["total_days"])


def _calculate_distribution() -> VibecodingDistribution:
    """Calculate vibecoding index distribution from recorded PRs."""
    dist = {"green": 0, "yellow": 0, "orange": 0, "red": 0}
    for pr in _pr_metrics:
        zone = pr.get("zone", "green").lower()
        if zone in dist:
            dist[zone] += 1
    return VibecodingDistribution(**dist)


def _calculate_average_index() -> float:
    """Calculate average vibecoding index."""
    if not _pr_metrics:
        return 0.0
    return sum(pr.get("vibecode_index", 0) for pr in _pr_metrics) / len(_pr_metrics)


def _calculate_avg_friction() -> float:
    """Calculate average developer friction in minutes."""
    if not _pr_metrics:
        return 0.0
    return sum(pr.get("friction_minutes", 0) for pr in _pr_metrics) / len(_pr_metrics)


def _calculate_false_positive_rate() -> float:
    """Calculate false positive rate."""
    # TODO: Implement actual false positive tracking
    # For now, return 0 as no false positives reported yet
    return 0.0


def _get_blockers() -> list[str]:
    """Identify blockers for Go/No-Go decision."""
    blockers = []

    # Check PR count
    if len(_pr_metrics) < SPRINT_114_CONFIG["prs_target"]:
        blockers.append(
            f"Need {SPRINT_114_CONFIG['prs_target']}+ PRs evaluated "
            f"(currently: {len(_pr_metrics)})"
        )

    # Check average friction
    avg_friction = _calculate_avg_friction()
    if avg_friction > SPRINT_114_CONFIG["friction_target"]:
        blockers.append(
            f"Developer friction too high: {avg_friction:.1f} min "
            f"(target: <{SPRINT_114_CONFIG['friction_target']} min)"
        )

    # Check false positive rate
    fp_rate = _calculate_false_positive_rate()
    if fp_rate > SPRINT_114_CONFIG["false_positive_target"]:
        blockers.append(
            f"False positive rate too high: {fp_rate:.1f}% "
            f"(target: <{SPRINT_114_CONFIG['false_positive_target']}%)"
        )

    # Check NPS (placeholder - survey not implemented yet)
    blockers.append("Team NPS survey not completed")

    return blockers


# ============================================================================
# API Endpoints
# ============================================================================

@router.get("/metrics", response_model=DogfoodingMetricsResponse)
async def get_dogfooding_metrics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get Sprint 114 dogfooding metrics for WARNING mode observation.

    Returns aggregated metrics for Go/No-Go decision support.
    """
    distribution = _calculate_distribution()
    avg_index = _calculate_average_index()
    avg_friction = _calculate_avg_friction()
    fp_rate = _calculate_false_positive_rate()
    blockers = _get_blockers()

    return DogfoodingMetricsResponse(
        sprint=SPRINT_114_CONFIG["sprint"],
        mode=SPRINT_114_CONFIG["mode"],
        start_date=SPRINT_114_CONFIG["start_date"],
        end_date=SPRINT_114_CONFIG["end_date"],
        days_elapsed=_calculate_days_elapsed(),
        total_days=SPRINT_114_CONFIG["total_days"],
        prs_evaluated=len(_pr_metrics),
        prs_target=SPRINT_114_CONFIG["prs_target"],
        distribution=distribution,
        average_index=avg_index,
        avg_friction_minutes=avg_friction,
        friction_target=SPRINT_114_CONFIG["friction_target"],
        false_positive_rate=fp_rate,
        false_positive_target=SPRINT_114_CONFIG["false_positive_target"],
        team_nps=None,  # Survey not implemented yet
        nps_target=SPRINT_114_CONFIG["nps_target"],
        go_no_go_ready=len(blockers) == 0,
        blockers=blockers,
    )


@router.get("/prs", response_model=PRMetricsListResponse)
async def get_pr_metrics(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get list of PR governance evaluations.

    Paginated list of PRs evaluated during dogfooding period.
    """
    start = (page - 1) * page_size
    end = start + page_size

    items = [
        PRMetricResponse(
            pr_number=pr["pr_number"],
            title=pr["title"],
            author=pr["author"],
            vibecode_index=pr["vibecode_index"],
            zone=pr["zone"],
            friction_minutes=pr["friction_minutes"],
            auto_gen_used=pr.get("auto_gen_used", False),
            timestamp=pr.get("timestamp", datetime.utcnow()),
        )
        for pr in _pr_metrics[start:end]
    ]

    return PRMetricsListResponse(
        items=items,
        total=len(_pr_metrics),
        page=page,
        page_size=page_size,
    )


@router.post("/prs/record")
async def record_pr_metric(
    request: RecordPRMetricRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Record a PR governance evaluation metric.

    Called by GitHub Actions workflow after each PR evaluation.
    No authentication required for GitHub Actions webhook.
    """
    # Check if PR already recorded
    existing = next(
        (pr for pr in _pr_metrics if pr["pr_number"] == request.pr_number),
        None,
    )

    pr_data = {
        "pr_number": request.pr_number,
        "title": request.title,
        "author": request.author,
        "vibecode_index": request.vibecode_index,
        "zone": request.zone,
        "friction_minutes": request.friction_minutes,
        "auto_gen_used": request.auto_gen_used,
        "file_count": request.file_count,
        "violations": request.violations,
        "timestamp": datetime.utcnow(),
    }

    if existing:
        # Update existing record
        _pr_metrics.remove(existing)

    _pr_metrics.append(pr_data)

    return {
        "status": "recorded",
        "pr_number": request.pr_number,
        "total_prs": len(_pr_metrics),
    }


@router.get("/go-no-go", response_model=GoNoGoDecisionResponse)
async def get_go_no_go_decision(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get Go/No-Go decision for Sprint 115 (SOFT mode).

    Evaluates all criteria and provides recommendation.
    Requires CTO or CEO role.
    """
    if current_user.role not in ["cto", "ceo", "admin"]:
        raise HTTPException(
            status_code=403,
            detail="Go/No-Go decision requires CTO or CEO role",
        )

    blockers = _get_blockers()
    avg_friction = _calculate_avg_friction()
    fp_rate = _calculate_false_positive_rate()

    checks = [
        {
            "name": "PRs Evaluated",
            "current": len(_pr_metrics),
            "target": SPRINT_114_CONFIG["prs_target"],
            "passed": len(_pr_metrics) >= SPRINT_114_CONFIG["prs_target"],
        },
        {
            "name": "Developer Friction",
            "current": f"{avg_friction:.1f} min",
            "target": f"<{SPRINT_114_CONFIG['friction_target']} min",
            "passed": avg_friction <= SPRINT_114_CONFIG["friction_target"],
        },
        {
            "name": "False Positive Rate",
            "current": f"{fp_rate:.1f}%",
            "target": f"<{SPRINT_114_CONFIG['false_positive_target']}%",
            "passed": fp_rate <= SPRINT_114_CONFIG["false_positive_target"],
        },
        {
            "name": "Team NPS",
            "current": "N/A",
            "target": f">{SPRINT_114_CONFIG['nps_target']}",
            "passed": False,  # Survey not completed
        },
    ]

    ready = len(blockers) == 0
    recommendation = (
        "PROCEED to Sprint 115 (SOFT Enforcement)"
        if ready
        else "EXTEND WARNING mode - address blockers before enforcement"
    )

    return GoNoGoDecisionResponse(
        ready=ready,
        checks=checks,
        recommendation=recommendation,
        blockers=blockers,
        next_sprint="115",
        next_mode="SOFT" if ready else "WARNING",
    )


@router.get("/status")
async def get_dogfooding_status(
    db: AsyncSession = Depends(get_db),
):
    """
    Get current dogfooding status (public endpoint).

    Returns basic status information for monitoring.
    """
    return {
        "sprint": SPRINT_114_CONFIG["sprint"],
        "mode": SPRINT_114_CONFIG["mode"],
        "start_date": SPRINT_114_CONFIG["start_date"],
        "end_date": SPRINT_114_CONFIG["end_date"],
        "days_elapsed": _calculate_days_elapsed(),
        "prs_evaluated": len(_pr_metrics),
        "prs_target": SPRINT_114_CONFIG["prs_target"],
        "status": "active" if _calculate_days_elapsed() <= SPRINT_114_CONFIG["total_days"] else "completed",
    }


@router.post("/report-false-positive")
async def report_false_positive(
    pr_number: int,
    reason: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Report a false positive governance evaluation.

    Used by developers to flag incorrect violations for calibration.
    """
    # Find the PR metric
    pr = next(
        (pr for pr in _pr_metrics if pr["pr_number"] == pr_number),
        None,
    )

    if not pr:
        raise HTTPException(
            status_code=404,
            detail=f"PR #{pr_number} not found in dogfooding metrics",
        )

    # Record false positive
    if "false_positive_reports" not in pr:
        pr["false_positive_reports"] = []

    pr["false_positive_reports"].append({
        "reporter": current_user.username,
        "reason": reason,
        "timestamp": datetime.utcnow().isoformat(),
    })

    return {
        "status": "reported",
        "pr_number": pr_number,
        "message": "False positive report recorded. Thank you for helping calibrate the system.",
    }
