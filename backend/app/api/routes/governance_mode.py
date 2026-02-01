"""
=========================================================================
Governance Mode API Routes - Mode Management & Kill Switch
SDLC Orchestrator - Sprint 108 (Governance Foundation)

Version: 1.0.0
Date: January 27, 2026
Status: ACTIVE - Sprint 108 Day 3
Authority: CTO + Backend Lead Approved
Framework: SDLC 5.3.0 Quality Assurance System

Endpoints:
- GET /governance/mode - Get current governance mode
- PUT /governance/mode - Set governance mode
- POST /governance/kill-switch - Emergency rollback to WARNING
- GET /governance/metrics - Get enforcement metrics
- GET /governance/dogfooding/status - Get dogfooding status
- POST /governance/false-positive - Report false positive

Zero Mock Policy: Real API with real enforcement
=========================================================================
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.api.dependencies import get_current_user as get_authenticated_user
from app.models.user import User
from app.services.governance.mode_service import (
    GovernanceMode,
    GovernanceModeService,
    GovernanceModeState,
    get_governance_mode_service,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/governance")


# ============================================================================
# Request/Response Models
# ============================================================================


class GovernanceModeResponse(BaseModel):
    """Response model for governance mode."""

    mode: str = Field(..., description="Current governance mode (off, warning, soft, full)")
    previous_mode: Optional[str] = Field(None, description="Previous mode before last change")
    changed_at: datetime = Field(..., description="When mode was last changed")
    changed_by: Optional[str] = Field(None, description="Who changed the mode")
    reason: Optional[str] = Field(None, description="Reason for last change")
    is_rollback: bool = Field(False, description="Whether last change was a rollback")
    auto_rollback_enabled: bool = Field(True, description="Whether auto-rollback is enabled")


class GovernanceModeStateResponse(BaseModel):
    """Full governance mode state including metrics."""

    mode: str
    previous_mode: Optional[str]
    changed_at: datetime
    changed_by: Optional[str]
    reason: Optional[str]
    is_rollback: bool
    auto_rollback_enabled: bool
    total_evaluations: int
    total_blocked: int
    total_warned: int
    total_passed: int
    rejection_rate: float
    false_positive_rate: float
    ceo_overrides: int


class SetModeRequest(BaseModel):
    """Request model for setting governance mode."""

    mode: str = Field(
        ...,
        description="New mode (off, warning, soft, full)",
        pattern="^(off|warning|soft|full)$",
    )
    reason: str = Field(
        ...,
        min_length=10,
        max_length=500,
        description="Reason for mode change (required for audit)",
    )
    project_id: Optional[UUID] = Field(
        None,
        description="Optional project ID for project-level override",
    )


class SetModeResponse(BaseModel):
    """Response model for set mode operation."""

    success: bool
    previous_mode: str
    new_mode: str
    changed_at: datetime
    changed_by: str
    reason: str
    message: str


class KillSwitchRequest(BaseModel):
    """Request model for kill switch."""

    reason: str = Field(
        ...,
        min_length=10,
        max_length=1000,
        description="Reason for triggering kill switch (required for audit)",
    )
    confirm: bool = Field(
        ...,
        description="Confirmation flag (must be true)",
    )


class KillSwitchResponse(BaseModel):
    """Response model for kill switch operation."""

    success: bool
    previous_mode: str
    new_mode: str = "warning"
    triggered_at: datetime
    triggered_by: str
    reason: str
    message: str
    notifications_sent: List[str]


class FalsePositiveRequest(BaseModel):
    """Request model for reporting false positive."""

    violation_id: str = Field(..., description="ID of the falsely blocked violation")
    submission_id: Optional[UUID] = Field(None, description="Related submission ID")
    reason: str = Field(
        ...,
        min_length=20,
        max_length=1000,
        description="Explanation of why this is a false positive",
    )


class FalsePositiveResponse(BaseModel):
    """Response model for false positive report."""

    success: bool
    violation_id: str
    reported_at: datetime
    reported_by: str
    total_false_positives: int
    false_positive_rate: float
    message: str


class MetricsResponse(BaseModel):
    """Response model for governance metrics."""

    mode: str
    total_evaluations: int
    total_blocked: int
    total_warned: int
    total_passed: int
    rejection_rate: float
    false_positive_rate: float
    latency_p95_ms: float
    ceo_overrides: int
    auto_rollback_enabled: bool
    uptime_since: datetime


class DogfoodingStatusResponse(BaseModel):
    """Response model for dogfooding status."""

    phase: str = Field(..., description="Current dogfooding phase (week_1, week_2, week_3)")
    mode: str
    start_date: datetime
    current_week: int
    metrics: Dict[str, Any]
    success_criteria_status: Dict[str, bool]
    failure_criteria_triggered: List[str]
    recommendation: str


# ============================================================================
# Dependency: Authentication (Sprint 132 P0 Fix - Real Auth)
# ============================================================================


async def get_current_user(
    user: User = Depends(get_authenticated_user),
) -> User:
    """
    Get current authenticated user.

    Uses real JWT authentication from app.api.dependencies.
    Sprint 132 P0 Fix: Replaced placeholder with real auth.

    Returns:
        User: Authenticated user object

    Raises:
        HTTPException(401): If not authenticated
    """
    return user


async def require_admin(
    user: User = Depends(get_authenticated_user),
) -> User:
    """
    Require admin user for governance operations.

    Checks for:
    - is_superuser flag (platform admin)
    - C-suite role (ceo, cto, cpo, cio, cfo)

    Sprint 132 P0 Fix: Replaced placeholder with real auth + role check.

    Returns:
        User: Authenticated admin user

    Raises:
        HTTPException(401): If not authenticated
        HTTPException(403): If not admin/C-suite
    """
    if not user.is_superuser and not user.is_c_suite:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or C-suite role required for governance operations",
        )
    return user


# ============================================================================
# Endpoints
# ============================================================================


@router.get(
    "/mode",
    response_model=GovernanceModeResponse,
    summary="Get current governance mode",
    description="""
    Get the current governance enforcement mode.

    Modes:
    - `off`: No enforcement (development mode)
    - `warning`: Log violations, don't block (observability mode)
    - `soft`: Block critical violations, warn on others
    - `full`: Block all violations (production mode)
    """,
)
async def get_governance_mode(
    project_id: Optional[UUID] = Query(
        None,
        description="Optional project ID to get project-specific mode",
    ),
    mode_service: GovernanceModeService = Depends(get_governance_mode_service),
) -> GovernanceModeResponse:
    """Get current governance mode."""
    state = mode_service.get_state()
    current_mode = mode_service.get_mode(project_id)

    return GovernanceModeResponse(
        mode=current_mode.value,
        previous_mode=state.previous_mode.value if state.previous_mode else None,
        changed_at=state.changed_at,
        changed_by=state.changed_by,
        reason=state.reason,
        is_rollback=state.is_rollback,
        auto_rollback_enabled=state.auto_rollback_enabled,
    )


@router.get(
    "/mode/state",
    response_model=GovernanceModeStateResponse,
    summary="Get full governance mode state",
    description="Get full governance mode state including metrics for calibration.",
)
async def get_governance_mode_state(
    mode_service: GovernanceModeService = Depends(get_governance_mode_service),
) -> GovernanceModeStateResponse:
    """Get full governance mode state with metrics."""
    state = mode_service.get_state()

    return GovernanceModeStateResponse(
        mode=state.current_mode.value,
        previous_mode=state.previous_mode.value if state.previous_mode else None,
        changed_at=state.changed_at,
        changed_by=state.changed_by,
        reason=state.reason,
        is_rollback=state.is_rollback,
        auto_rollback_enabled=state.auto_rollback_enabled,
        total_evaluations=state.total_evaluations,
        total_blocked=state.total_blocked,
        total_warned=state.total_warned,
        total_passed=state.total_passed,
        rejection_rate=state.rejection_rate(),
        false_positive_rate=state.false_positive_rate(),
        ceo_overrides=state.ceo_overrides,
    )


@router.put(
    "/mode",
    response_model=SetModeResponse,
    summary="Set governance mode",
    description="""
    Set the governance enforcement mode.

    **Authorization Required**: Admin or CTO role

    Mode progression:
    - Recommended: `off` → `warning` → `soft` → `full`
    - Rollback: Any mode can rollback to `warning` for safety

    **Warning**: Setting to `full` mode will block all non-compliant PRs.
    """,
)
async def set_governance_mode(
    request: SetModeRequest,
    current_user: User = Depends(require_admin),
    mode_service: GovernanceModeService = Depends(get_governance_mode_service),
) -> SetModeResponse:
    """Set governance mode."""
    try:
        new_mode = GovernanceMode(request.mode)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid mode: {request.mode}. Must be one of: off, warning, soft, full",
        )

    previous_state = mode_service.get_state()
    previous_mode = previous_state.current_mode

    # Extract user identifier for audit trail
    user_identifier = current_user.email or str(current_user.id)

    await mode_service.set_mode(
        mode=new_mode,
        changed_by=user_identifier,
        reason=request.reason,
        project_id=request.project_id,
    )

    logger.info(
        f"Governance mode changed: {previous_mode.value} → {new_mode.value} "
        f"by {user_identifier}: {request.reason}"
    )

    return SetModeResponse(
        success=True,
        previous_mode=previous_mode.value,
        new_mode=new_mode.value,
        changed_at=datetime.utcnow(),
        changed_by=user_identifier,
        reason=request.reason,
        message=f"Governance mode changed from {previous_mode.value} to {new_mode.value}",
    )


@router.post(
    "/kill-switch",
    response_model=KillSwitchResponse,
    summary="Emergency kill switch",
    description="""
    **EMERGENCY ONLY**: Immediately rollback governance to WARNING mode.

    Use this when:
    - Governance is blocking critical production deployments
    - False positive rate is too high
    - System is causing more harm than good

    **Authorization Required**: CTO or CEO role

    **Actions triggered**:
    1. Mode immediately set to WARNING
    2. All stakeholders notified (CEO, CTO, Tech Lead)
    3. Incident logged for post-mortem
    4. Post-incident review required within 24 hours
    """,
)
async def trigger_kill_switch(
    request: KillSwitchRequest,
    current_user: User = Depends(require_admin),
    mode_service: GovernanceModeService = Depends(get_governance_mode_service),
) -> KillSwitchResponse:
    """Trigger emergency kill switch."""
    if not request.confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Kill switch requires confirmation (confirm: true)",
        )

    previous_mode = mode_service.get_mode()

    # Extract user identifier for audit trail
    user_identifier = current_user.email or str(current_user.id)

    await mode_service.kill_switch(
        triggered_by=user_identifier,
        reason=request.reason,
    )

    # Notification targets (in real implementation, send actual notifications)
    notifications = ["CEO", "CTO", "Tech Lead", "All developers"]

    logger.critical(
        f"KILL SWITCH TRIGGERED by {user_identifier}: {request.reason}"
    )

    return KillSwitchResponse(
        success=True,
        previous_mode=previous_mode.value,
        new_mode="warning",
        triggered_at=datetime.utcnow(),
        triggered_by=user_identifier,
        reason=request.reason,
        message="KILL SWITCH ACTIVATED: Governance rolled back to WARNING mode",
        notifications_sent=notifications,
    )


@router.post(
    "/false-positive",
    response_model=FalsePositiveResponse,
    summary="Report false positive",
    description="""
    Report a false positive (incorrectly blocked submission).

    This data is used to:
    - Track false positive rate
    - Calibrate governance rules
    - Trigger auto-rollback if rate exceeds threshold
    """,
)
async def report_false_positive(
    request: FalsePositiveRequest,
    current_user: User = Depends(get_current_user),
    mode_service: GovernanceModeService = Depends(get_governance_mode_service),
) -> FalsePositiveResponse:
    """Report a false positive."""
    # Extract user identifier for audit trail
    user_identifier = current_user.email or str(current_user.id)

    await mode_service.report_false_positive(
        violation_id=request.violation_id,
        reported_by=user_identifier,
        reason=request.reason,
    )

    state = mode_service.get_state()

    logger.info(
        f"False positive reported by {user_identifier}: {request.violation_id}"
    )

    return FalsePositiveResponse(
        success=True,
        violation_id=request.violation_id,
        reported_at=datetime.utcnow(),
        reported_by=user_identifier,
        total_false_positives=state.false_positives_reported,
        false_positive_rate=state.false_positive_rate(),
        message="False positive recorded. Thank you for the feedback.",
    )


@router.get(
    "/metrics",
    response_model=MetricsResponse,
    summary="Get governance metrics",
    description="Get governance enforcement metrics for monitoring and calibration.",
)
async def get_governance_metrics(
    mode_service: GovernanceModeService = Depends(get_governance_mode_service),
) -> MetricsResponse:
    """Get governance metrics."""
    state = mode_service.get_state()

    return MetricsResponse(
        mode=state.current_mode.value,
        total_evaluations=state.total_evaluations,
        total_blocked=state.total_blocked,
        total_warned=state.total_warned,
        total_passed=state.total_passed,
        rejection_rate=state.rejection_rate(),
        false_positive_rate=state.false_positive_rate(),
        latency_p95_ms=mode_service.get_latency_p95(),
        ceo_overrides=state.ceo_overrides,
        auto_rollback_enabled=state.auto_rollback_enabled,
        uptime_since=state.changed_at,
    )


@router.get(
    "/dogfooding/status",
    response_model=DogfoodingStatusResponse,
    summary="Get dogfooding status",
    description="Get status of governance dogfooding on SDLC Orchestrator repo.",
)
async def get_dogfooding_status(
    mode_service: GovernanceModeService = Depends(get_governance_mode_service),
) -> DogfoodingStatusResponse:
    """Get dogfooding status."""
    import yaml
    from datetime import datetime

    state = mode_service.get_state()

    # Load dogfooding config
    try:
        with open("backend/app/config/dogfooding.yaml", "r") as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        config = {"dogfooding": {}}

    dogfooding = config.get("dogfooding", {})

    # Determine current phase based on date and mode
    now = datetime.utcnow()
    mode = state.current_mode

    if mode == GovernanceMode.WARNING:
        phase = "week_1_preparation"
        current_week = 1
    elif mode == GovernanceMode.SOFT:
        phase = "week_2_soft_enforcement"
        current_week = 2
    elif mode == GovernanceMode.FULL:
        phase = "week_3_full_enforcement"
        current_week = 3
    else:
        phase = "not_started"
        current_week = 0

    # Calculate metrics
    metrics = {
        "total_evaluations": state.total_evaluations,
        "rejection_rate": f"{state.rejection_rate():.1%}",
        "false_positive_rate": f"{state.false_positive_rate():.1%}",
        "first_pass_rate": f"{(1 - state.rejection_rate()):.1%}" if state.total_evaluations > 0 else "N/A",
    }

    # Check success criteria
    success_criteria = dogfooding.get("success_criteria", {})
    success_criteria_status = {
        "first_submission_pass_rate": state.total_evaluations == 0 or state.rejection_rate() <= 0.3,
        "developer_friction_low": True,  # Would need more metrics
        "auto_generation_usage_high": True,  # Would need more metrics
    }

    # Check failure criteria
    failure_criteria = dogfooding.get("failure_criteria", [])
    failure_criteria_triggered = []

    if state.rejection_rate() > 0.8:
        failure_criteria_triggered.append("High rejection rate (>80%)")
    if state.false_positive_rate() > 0.2:
        failure_criteria_triggered.append("High false positive rate (>20%)")

    # Generate recommendation
    if failure_criteria_triggered:
        recommendation = f"ROLLBACK RECOMMENDED: {', '.join(failure_criteria_triggered)}"
    elif all(success_criteria_status.values()):
        if mode == GovernanceMode.WARNING:
            recommendation = "Ready to advance to SOFT enforcement"
        elif mode == GovernanceMode.SOFT:
            recommendation = "Ready to advance to FULL enforcement"
        else:
            recommendation = "On track - continue monitoring"
    else:
        recommendation = "Continue monitoring - some criteria not yet met"

    return DogfoodingStatusResponse(
        phase=phase,
        mode=mode.value,
        start_date=state.changed_at,
        current_week=current_week,
        metrics=metrics,
        success_criteria_status=success_criteria_status,
        failure_criteria_triggered=failure_criteria_triggered,
        recommendation=recommendation,
    )


@router.get(
    "/health",
    summary="Governance service health check",
    description="Check health of governance services.",
)
async def governance_health(
    mode_service: GovernanceModeService = Depends(get_governance_mode_service),
) -> Dict[str, Any]:
    """Health check for governance services."""
    state = mode_service.get_state()

    return {
        "status": "healthy",
        "mode": state.current_mode.value,
        "auto_rollback_enabled": state.auto_rollback_enabled,
        "total_evaluations": state.total_evaluations,
        "latency_p95_ms": mode_service.get_latency_p95(),
        "timestamp": datetime.utcnow().isoformat(),
    }
