"""
=========================================================================
NIST MANAGE Router - NIST AI RMF MANAGE Function API
SDLC Orchestrator - Sprint 158 (Phase 3: COMPLIANCE)

Version: 1.0.0
Date: April 21, 2026
Status: ACTIVE
Authority: CTO Approved
Framework: SDLC 6.0.5
Reference: ADR-051, NIST AI RMF 1.0

Purpose:
API endpoints for NIST AI RMF MANAGE function:
- Policy evaluation (5 MANAGE controls via OPA + fallback)
- MANAGE dashboard aggregation
- Risk response CRUD (create, list, update)
- Incident CRUD (report, list, update)

Endpoints:
- POST /compliance/nist/manage/evaluate                - Evaluate 5 MANAGE policies
- GET  /compliance/nist/manage/dashboard               - MANAGE dashboard
- GET  /compliance/nist/manage/risk-responses           - List risk responses
- POST /compliance/nist/manage/risk-responses           - Create risk response
- PUT  /compliance/nist/manage/risk-responses/{id}      - Update risk response
- GET  /compliance/nist/manage/incidents                - List incidents
- POST /compliance/nist/manage/incidents                - Report incident
- PUT  /compliance/nist/manage/incidents/{id}           - Update incident

Security:
- Authentication required (JWT)
- Project membership required (CTO Condition #3)

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
from app.models.nist_manage import ManageIncident, ManageRiskResponse
from app.models.project import Project, ProjectMember
from app.models.user import User
from app.schemas.compliance_framework import (
    IncidentCreate,
    IncidentListResponse,
    IncidentResponse,
    IncidentUpdate,
    ManageDashboardResponse,
    ManageEvaluateRequest,
    ManageEvaluateResponse,
    RiskResponseCreate,
    RiskResponseListResponse,
    RiskResponseResponse,
    RiskResponseUpdate,
)
from app.services.nist_manage_service import (
    IncidentNotFoundError,
    NISTManageEvaluationError,
    NISTManageService,
    RiskResponseNotFoundError,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/compliance/nist/manage",
    tags=["NIST AI RMF MANAGE"],
)

# Service singleton
_manage_service = NISTManageService()


# =============================================================================
# Authorization Helper (CTO Condition #3 - CRITICAL)
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


# =============================================================================
# Evaluation Endpoints
# =============================================================================


@router.post(
    "/evaluate",
    response_model=ManageEvaluateResponse,
    summary="Evaluate NIST MANAGE policies",
    description="""
    Evaluate all 5 NIST AI RMF MANAGE policies for a project.

    Policies evaluated:
    1. MANAGE-1.1: Risk Response Planning (critical)
    2. MANAGE-2.1: Resource Allocation (high)
    3. MANAGE-2.4: System Deactivation Criteria (critical)
    4. MANAGE-3.1: Third-Party Monitoring (high)
    5. MANAGE-4.1: Post-Deployment Monitoring (medium)

    Uses OPA policy evaluation with in-process fallback.
    Returns per-policy pass/fail with reasons and overall compliance percentage.
    """,
)
async def evaluate_manage(
    request: ManageEvaluateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ManageEvaluateResponse:
    """Evaluate NIST MANAGE policies for a project."""
    await check_project_access(request.project_id, current_user, db)

    logger.info(
        "User %s evaluating MANAGE for project %s",
        current_user.id,
        request.project_id,
    )

    try:
        result = await _manage_service.evaluate_manage(
            project_id=request.project_id,
            db=db,
        )

        return ManageEvaluateResponse(
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
    except NISTManageEvaluationError as exc:
        logger.error("MANAGE evaluation failed: %s", str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"MANAGE policy evaluation failed: {str(exc)}",
        )


@router.get(
    "/dashboard",
    response_model=ManageDashboardResponse,
    summary="MANAGE dashboard",
    description="""
    Get NIST AI RMF MANAGE function dashboard data for a project.

    Includes:
    - Compliance percentage and policy results
    - Total risk responses and completed count
    - Total incidents, open incidents, and critical incidents
    - Deactivation criteria presence flag
    """,
)
async def get_manage_dashboard(
    project_id: UUID = Query(..., description="Project ID"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ManageDashboardResponse:
    """Get MANAGE dashboard data."""
    await check_project_access(project_id, current_user, db)

    logger.info(
        "User %s viewing MANAGE dashboard for project %s",
        current_user.id,
        project_id,
    )

    result = await _manage_service.get_dashboard(
        project_id=project_id,
        db=db,
    )

    return ManageDashboardResponse(
        project_id=result["project_id"]
        if isinstance(result["project_id"], UUID)
        else UUID(result["project_id"]),
        compliance_percentage=result["compliance_percentage"],
        policies_passed=result["policies_passed"],
        policies_total=result["policies_total"],
        policy_results=result["policy_results"],
        total_risk_responses=result["total_risk_responses"],
        completed_responses=result["completed_responses"],
        total_incidents=result["total_incidents"],
        open_incidents=result["open_incidents"],
        critical_incidents=result["critical_incidents"],
        has_deactivation_criteria=result["has_deactivation_criteria"],
    )


# =============================================================================
# Risk Response Endpoints
# =============================================================================


@router.get(
    "/risk-responses",
    response_model=RiskResponseListResponse,
    summary="List risk responses",
    description="List risk response plans for a project with optional status filter and pagination.",
)
async def list_risk_responses(
    project_id: UUID = Query(..., description="Project ID"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    limit: int = Query(50, ge=1, le=200, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Skip results"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> RiskResponseListResponse:
    """List risk responses for a project."""
    await check_project_access(project_id, current_user, db)

    items, total = await _manage_service.list_risk_responses(
        project_id=project_id,
        status_filter=status_filter,
        limit=limit,
        offset=offset,
        db=db,
    )

    return RiskResponseListResponse(
        items=[RiskResponseResponse.model_validate(r) for r in items],
        total=total,
        limit=limit,
        offset=offset,
        has_more=(offset + limit) < total,
    )


@router.post(
    "/risk-responses",
    response_model=RiskResponseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create risk response",
    description="Create a new risk response plan linked to an existing risk register entry.",
)
async def create_risk_response(
    data: RiskResponseCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> RiskResponseResponse:
    """Create a risk response plan."""
    await check_project_access(data.project_id, current_user, db)

    logger.info(
        "User %s creating risk response for risk %s in project %s",
        current_user.id,
        data.risk_id,
        data.project_id,
    )

    try:
        response = await _manage_service.create_risk_response(
            data=data.model_dump(mode="json"),
            user_id=current_user.id,
            db=db,
        )
        return RiskResponseResponse.model_validate(response)
    except RiskResponseNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )


@router.put(
    "/risk-responses/{response_id}",
    response_model=RiskResponseResponse,
    summary="Update risk response",
    description="Update an existing risk response plan. Only provided fields are updated.",
)
async def update_risk_response(
    response_id: UUID,
    data: RiskResponseUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> RiskResponseResponse:
    """Update a risk response plan."""
    # Resolve response -> project_id for access check
    result = await db.execute(
        select(ManageRiskResponse).where(ManageRiskResponse.id == response_id)
    )
    risk_response = result.scalar_one_or_none()

    if not risk_response:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Risk response not found: {response_id}",
        )

    await check_project_access(risk_response.project_id, current_user, db)

    logger.info(
        "User %s updating risk response %s",
        current_user.id,
        response_id,
    )

    try:
        updated = await _manage_service.update_risk_response(
            response_id=response_id,
            data=data.model_dump(exclude_unset=True, mode="json"),
            db=db,
        )
        return RiskResponseResponse.model_validate(updated)
    except RiskResponseNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )


# =============================================================================
# Incident Endpoints
# =============================================================================


@router.get(
    "/incidents",
    response_model=IncidentListResponse,
    summary="List incidents",
    description="List AI system incidents for a project with optional filters and pagination.",
)
async def list_incidents(
    project_id: UUID = Query(..., description="Project ID"),
    ai_system_id: Optional[UUID] = Query(None, description="Filter by AI system"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    limit: int = Query(50, ge=1, le=200, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Skip results"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> IncidentListResponse:
    """List AI system incidents."""
    await check_project_access(project_id, current_user, db)

    items, total = await _manage_service.list_incidents(
        project_id=project_id,
        ai_system_id=ai_system_id,
        status_filter=status_filter,
        limit=limit,
        offset=offset,
        db=db,
    )

    return IncidentListResponse(
        items=[IncidentResponse.model_validate(i) for i in items],
        total=total,
        limit=limit,
        offset=offset,
        has_more=(offset + limit) < total,
    )


@router.post(
    "/incidents",
    response_model=IncidentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Report incident",
    description="Report a new AI system incident with severity, type, and occurrence timestamp.",
)
async def create_incident(
    data: IncidentCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> IncidentResponse:
    """Report an AI system incident."""
    await check_project_access(data.project_id, current_user, db)

    logger.info(
        "User %s reporting incident '%s' for system %s in project %s",
        current_user.id,
        data.title,
        data.ai_system_id,
        data.project_id,
    )

    try:
        incident = await _manage_service.create_incident(
            data=data.model_dump(mode="json"),
            user_id=current_user.id,
            db=db,
        )
        return IncidentResponse.model_validate(incident)
    except IncidentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )


@router.put(
    "/incidents/{incident_id}",
    response_model=IncidentResponse,
    summary="Update incident",
    description="Update an existing incident. Supports status transitions, resolution, and root cause analysis.",
)
async def update_incident(
    incident_id: UUID,
    data: IncidentUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> IncidentResponse:
    """Update an AI system incident."""
    # Resolve incident -> project_id for access check
    result = await db.execute(
        select(ManageIncident).where(ManageIncident.id == incident_id)
    )
    incident = result.scalar_one_or_none()

    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident not found: {incident_id}",
        )

    await check_project_access(incident.project_id, current_user, db)

    logger.info(
        "User %s updating incident %s",
        current_user.id,
        incident_id,
    )

    try:
        updated = await _manage_service.update_incident(
            incident_id=incident_id,
            data=data.model_dump(exclude_unset=True, mode="json"),
            db=db,
        )
        return IncidentResponse.model_validate(updated)
    except IncidentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
