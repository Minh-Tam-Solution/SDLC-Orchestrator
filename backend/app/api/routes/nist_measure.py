"""
=========================================================================
NIST MEASURE Router - NIST AI RMF MEASURE Function API
SDLC Orchestrator - Sprint 157 (Phase 3: COMPLIANCE)

Version: 1.0.0
Date: April 14, 2026
Status: ACTIVE
Authority: CTO Approved
Framework: SDLC 6.0.5
Reference: ADR-051, NIST AI RMF 1.0

Purpose:
API endpoints for NIST AI RMF MEASURE function:
- Policy evaluation (4 MEASURE controls via OPA + fallback)
- MEASURE dashboard aggregation
- Performance metrics CRUD (single + batch)
- Metric trend queries (30-day window)
- Bias/disparity summary

Endpoints:
- POST /compliance/nist/measure/evaluate      - Evaluate 4 MEASURE policies
- GET  /compliance/nist/measure/dashboard      - MEASURE dashboard
- GET  /compliance/nist/measure/metrics        - List metrics
- POST /compliance/nist/measure/metrics        - Record single metric
- POST /compliance/nist/measure/metrics/batch  - Record batch metrics
- GET  /compliance/nist/measure/metrics/trend  - Metric trend data
- GET  /compliance/nist/measure/bias-summary   - Bias/disparity summary

Security:
- Authentication required (JWT)
- Project membership required

Zero Mock Policy: Production-ready implementation
=========================================================================
"""

import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user
from app.db.session import get_db
from app.models.nist_map_measure import AISystem
from app.models.project import Project, ProjectMember
from app.models.user import User
from app.schemas.compliance_framework import (
    BiasSummaryResponse,
    MeasureDashboardResponse,
    MeasureEvaluateRequest,
    MeasureEvaluateResponse,
    MetricBatchCreate,
    MetricCreate,
    MetricListResponse,
    MetricResponse,
    MetricTrendResponse,
)
from app.services.nist_measure_service import (
    MetricNotFoundError,
    NISTMeasureEvaluationError,
    NISTMeasureService,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/compliance/nist/measure",
    tags=["NIST AI RMF MEASURE"],
)

# Service singleton
_measure_service = NISTMeasureService()


# =============================================================================
# Authorization Helper
# =============================================================================


async def check_project_access(
    project_id: UUID, user: User, db: AsyncSession
) -> Project:
    """
    Check if user has access to the project.

    Args:
        project_id: UUID of the project.
        user: Current authenticated user.
        db: Database session.

    Returns:
        Project if access granted.

    Raises:
        HTTPException: 404 if project not found, 403 if access denied.
    """
    result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.deleted_at.is_(None),
        )
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project not found: {project_id}",
        )

    if project.owner_id == user.id:
        return project

    membership_result = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user.id,
        )
    )
    membership = membership_result.scalar_one_or_none()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. You are not a member of this project.",
        )

    return project


async def check_ai_system_access(
    ai_system_id: UUID, user: User, db: AsyncSession
) -> AISystem:
    """
    Resolve AI system and check project access.

    Args:
        ai_system_id: UUID of the AI system.
        user: Current authenticated user.
        db: Database session.

    Returns:
        AISystem if access granted.

    Raises:
        HTTPException: 404 if system not found, 403 if access denied.
    """
    result = await db.execute(
        select(AISystem).where(AISystem.id == ai_system_id, AISystem.is_active.is_(True))
    )
    system = result.scalar_one_or_none()

    if not system:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"AI system not found: {ai_system_id}",
        )

    await check_project_access(system.project_id, user, db)
    return system


# =============================================================================
# Evaluation Endpoints
# =============================================================================


@router.post(
    "/evaluate",
    response_model=MeasureEvaluateResponse,
    summary="Evaluate NIST MEASURE policies",
    description="""
    Evaluate all 4 NIST AI RMF MEASURE policies for a project.

    Policies evaluated:
    1. MEASURE-1.1: Performance Thresholds (high)
    2. MEASURE-2.1: Bias Detection (critical)
    3. MEASURE-2.2: Disparity Analysis (critical)
    4. MEASURE-3.1: Metric Trending (medium)

    Uses OPA policy evaluation with in-process fallback.
    Returns per-policy pass/fail with reasons and overall compliance percentage.
    """,
)
async def evaluate_measure(
    request: MeasureEvaluateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> MeasureEvaluateResponse:
    """Evaluate NIST MEASURE policies for a project."""
    await check_project_access(request.project_id, current_user, db)

    logger.info(
        "User %s evaluating MEASURE for project %s",
        current_user.id,
        request.project_id,
    )

    try:
        result = await _measure_service.evaluate_measure(
            project_id=request.project_id,
            db=db,
        )

        return MeasureEvaluateResponse(
            project_id=result["project_id"]
            if isinstance(result["project_id"], UUID)
            else UUID(result["project_id"]),
            framework_code=result["framework_code"],
            function=result["function"],
            overall_compliant=result["overall_compliant"],
            policies_passed=result["policies_passed"],
            policies_total=result["policies_total"],
            compliance_percentage=result["compliance_percentage"],
            results=result["results"],
            evaluated_at=datetime.fromisoformat(result["evaluated_at"])
            if isinstance(result["evaluated_at"], str)
            else result["evaluated_at"],
        )
    except NISTMeasureEvaluationError as exc:
        logger.error("MEASURE evaluation failed: %s", str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"MEASURE policy evaluation failed: {str(exc)}",
        )


@router.get(
    "/dashboard",
    response_model=MeasureDashboardResponse,
    summary="MEASURE dashboard",
    description="""
    Get NIST AI RMF MEASURE function dashboard data for a project.

    Includes:
    - Compliance percentage and policy results
    - Total metrics and within-threshold count
    - Bias demographic group count
    - Disparity summary
    """,
)
async def get_measure_dashboard(
    project_id: UUID = Query(..., description="Project ID"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> MeasureDashboardResponse:
    """Get MEASURE dashboard data."""
    await check_project_access(project_id, current_user, db)

    logger.info(
        "User %s viewing MEASURE dashboard for project %s",
        current_user.id,
        project_id,
    )

    result = await _measure_service.get_dashboard(
        project_id=project_id,
        db=db,
    )

    return MeasureDashboardResponse(
        project_id=result["project_id"]
        if isinstance(result["project_id"], UUID)
        else UUID(result["project_id"]),
        compliance_percentage=result["compliance_percentage"],
        policies_passed=result["policies_passed"],
        policies_total=result["policies_total"],
        policy_results=result["policy_results"],
        total_metrics=result["total_metrics"],
        within_threshold=result["within_threshold"],
        bias_groups_count=result["bias_groups_count"],
        disparity_summary=result["disparity_summary"],
    )


# =============================================================================
# Metrics CRUD Endpoints
# =============================================================================


@router.get(
    "/metrics",
    response_model=MetricListResponse,
    summary="List metrics",
    description="List performance metrics with optional filters and pagination.",
)
async def list_metrics(
    project_id: UUID = Query(..., description="Project ID"),
    ai_system_id: Optional[UUID] = Query(None, description="Filter by AI system"),
    metric_type: Optional[str] = Query(None, description="Filter by metric type"),
    limit: int = Query(50, ge=1, le=200, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Skip results"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> MetricListResponse:
    """List performance metrics."""
    await check_project_access(project_id, current_user, db)

    items, total = await _measure_service.list_metrics(
        project_id=project_id,
        ai_system_id=ai_system_id,
        metric_type=metric_type,
        limit=limit,
        offset=offset,
        db=db,
    )

    return MetricListResponse(
        items=[MetricResponse.model_validate(m) for m in items],
        total=total,
        limit=limit,
        offset=offset,
        has_more=(offset + limit) < total,
    )


@router.post(
    "/metrics",
    response_model=MetricResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record metric",
    description="Record a single performance metric measurement.",
)
async def create_metric(
    data: MetricCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> MetricResponse:
    """Record a single metric."""
    await check_project_access(data.project_id, current_user, db)

    logger.info(
        "User %s recording metric '%s' for system %s",
        current_user.id,
        data.metric_name,
        data.ai_system_id,
    )

    try:
        metric = await _measure_service.create_metric(
            data=data.model_dump(),
            user_id=current_user.id,
            db=db,
        )
        return MetricResponse.model_validate(metric)
    except MetricNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )


@router.post(
    "/metrics/batch",
    response_model=list[MetricResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Record batch metrics",
    description="Record multiple performance metrics in a single request.",
)
async def create_metrics_batch(
    data: MetricBatchCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[MetricResponse]:
    """Record batch metrics."""
    await check_project_access(data.project_id, current_user, db)

    logger.info(
        "User %s batch recording %d metrics for project %s",
        current_user.id,
        len(data.metrics),
        data.project_id,
    )

    try:
        metrics_data = [m.model_dump() for m in data.metrics]
        created = await _measure_service.create_metrics_batch(
            project_id=data.project_id,
            metrics_data=metrics_data,
            user_id=current_user.id,
            db=db,
        )
        return [MetricResponse.model_validate(m) for m in created]
    except MetricNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )


# =============================================================================
# Trend & Bias Endpoints
# =============================================================================


@router.get(
    "/metrics/trend",
    response_model=MetricTrendResponse,
    summary="Metric trend data",
    description="Get metric trend data points over a configurable time window.",
)
async def get_metric_trend(
    ai_system_id: UUID = Query(..., description="AI system ID"),
    metric_type: str = Query(..., description="Metric type to trend"),
    days: int = Query(30, ge=1, le=365, description="Lookback period in days"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> MetricTrendResponse:
    """Get metric trend data."""
    await check_ai_system_access(ai_system_id, current_user, db)

    logger.info(
        "User %s viewing trend for system %s metric %s (%d days)",
        current_user.id,
        ai_system_id,
        metric_type,
        days,
    )

    data_points = await _measure_service.get_metric_trend(
        ai_system_id=ai_system_id,
        metric_type=metric_type,
        days=days,
        db=db,
    )

    return MetricTrendResponse(
        ai_system_id=ai_system_id,
        metric_type=metric_type,
        data_points=data_points,
        total_points=len(data_points),
    )


@router.get(
    "/bias-summary",
    response_model=BiasSummaryResponse,
    summary="Bias/disparity summary",
    description="Get bias and disparity analysis summary across AI systems and demographic groups.",
)
async def get_bias_summary(
    project_id: UUID = Query(..., description="Project ID"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> BiasSummaryResponse:
    """Get bias/disparity summary."""
    await check_project_access(project_id, current_user, db)

    logger.info(
        "User %s viewing bias summary for project %s",
        current_user.id,
        project_id,
    )

    result = await _measure_service.get_bias_summary(
        project_id=project_id,
        db=db,
    )

    return BiasSummaryResponse(
        project_id=result["project_id"]
        if isinstance(result["project_id"], UUID)
        else UUID(result["project_id"]),
        systems=result["systems"],
        total_bias_metrics=result["total_bias_metrics"],
        compliant_systems=result["compliant_systems"],
        non_compliant_systems=result["non_compliant_systems"],
    )
