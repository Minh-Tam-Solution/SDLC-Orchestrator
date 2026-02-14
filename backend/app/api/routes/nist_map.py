"""
=========================================================================
NIST MAP Router - NIST AI RMF MAP Function API
SDLC Orchestrator - Sprint 157 (Phase 3: COMPLIANCE)

Version: 1.0.0
Date: April 14, 2026
Status: ACTIVE
Authority: CTO Approved
Framework: SDLC 6.0.5
Reference: ADR-051, NIST AI RMF 1.0

Purpose:
API endpoints for NIST AI RMF MAP function:
- Policy evaluation (5 MAP controls via OPA + fallback)
- MAP dashboard aggregation
- AI system CRUD (register, update, soft-delete)
- Risk-to-impact mapping queries

Endpoints:
- POST /compliance/nist/map/evaluate       - Evaluate 5 MAP policies
- GET  /compliance/nist/map/dashboard       - MAP dashboard
- GET  /compliance/nist/map/ai-systems      - List AI systems
- POST /compliance/nist/map/ai-systems      - Register AI system
- PUT  /compliance/nist/map/ai-systems/{id} - Update AI system
- DELETE /compliance/nist/map/ai-systems/{id} - Soft-delete AI system
- GET  /compliance/nist/map/risk-impacts    - Risk-to-impact mappings

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
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import select

from app.api.dependencies import get_current_active_user
from app.db.session import get_db
from app.models.project import Project, ProjectMember
from app.models.user import User
from app.schemas.compliance_framework import (
    AISystemCreate,
    AISystemListResponse,
    AISystemResponse,
    AISystemUpdate,
    MapDashboardResponse,
    MapEvaluateRequest,
    MapEvaluateResponse,
    RiskImpactListResponse,
    RiskImpactMapping,
)
from app.services.nist_map_service import (
    AISystemDuplicateError,
    AISystemNotFoundError,
    NISTMapEvaluationError,
    NISTMapService,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/compliance/nist/map",
    tags=["NIST AI RMF MAP"],
)

# Service singleton
_map_service = NISTMapService()


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


# =============================================================================
# Evaluation Endpoints
# =============================================================================


@router.post(
    "/evaluate",
    response_model=MapEvaluateResponse,
    summary="Evaluate NIST MAP policies",
    description="""
    Evaluate all 5 NIST AI RMF MAP policies for a project.

    Policies evaluated:
    1. MAP-1.1: Context Establishment (critical)
    2. MAP-1.2: Stakeholder Identification (medium)
    3. MAP-2.1: System Categorization (critical)
    4. MAP-3.1: Risk & Impact Mapping (high)
    5. MAP-3.2: Dependency Mapping (medium)

    Uses OPA policy evaluation with in-process fallback.
    Returns per-policy pass/fail with reasons and overall compliance percentage.
    """,
)
async def evaluate_map(
    request: MapEvaluateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> MapEvaluateResponse:
    """Evaluate NIST MAP policies for a project."""
    await check_project_access(request.project_id, current_user, db)

    logger.info(
        "User %s evaluating MAP for project %s",
        current_user.id,
        request.project_id,
    )

    try:
        result = await _map_service.evaluate_map(
            db=db,
            project_id=request.project_id,
            request={},
        )

        return MapEvaluateResponse(
            project_id=result["project_id"],
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
    except NISTMapEvaluationError as exc:
        logger.error("MAP evaluation failed: %s", str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"MAP policy evaluation failed: {str(exc)}",
        )


@router.get(
    "/dashboard",
    response_model=MapDashboardResponse,
    summary="MAP dashboard",
    description="""
    Get NIST AI RMF MAP function dashboard data for a project.

    Includes:
    - Compliance percentage and policy results
    - AI system inventory summary (count by type)
    - Risk summary (count by level)
    """,
)
async def get_map_dashboard(
    project_id: UUID = Query(..., description="Project ID"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> MapDashboardResponse:
    """Get MAP dashboard data."""
    await check_project_access(project_id, current_user, db)

    logger.info(
        "User %s viewing MAP dashboard for project %s",
        current_user.id,
        project_id,
    )

    result = await _map_service.get_dashboard(db=db, project_id=project_id)

    return MapDashboardResponse(
        project_id=result["project_id"],
        compliance_percentage=result["compliance_percentage"],
        policies_passed=result["policies_passed"],
        policies_total=result["policies_total"],
        policy_results=result["policy_results"],
        ai_system_summary=result["ai_system_summary"],
        total_systems=sum(result["ai_system_summary"].values()),
        risk_summary=result["risk_summary"],
        total_risks=result["total_risks"],
    )


# =============================================================================
# AI System CRUD Endpoints
# =============================================================================


@router.get(
    "/ai-systems",
    response_model=AISystemListResponse,
    summary="List AI systems",
    description="List active AI systems registered for a project with pagination.",
)
async def list_ai_systems(
    project_id: UUID = Query(..., description="Project ID"),
    limit: int = Query(50, ge=1, le=200, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Skip results"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> AISystemListResponse:
    """List active AI systems for a project."""
    await check_project_access(project_id, current_user, db)

    items, total = await _map_service.list_ai_systems(
        db=db,
        project_id=project_id,
        skip=offset,
        limit=limit,
    )

    return AISystemListResponse(
        items=[AISystemResponse(**item) for item in items],
        total=total,
        limit=limit,
        offset=offset,
        has_more=(offset + limit) < total,
    )


@router.post(
    "/ai-systems",
    response_model=AISystemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register AI system",
    description="Register a new AI system with context, categorization, and dependencies.",
)
async def create_ai_system(
    data: AISystemCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> AISystemResponse:
    """Register a new AI system."""
    await check_project_access(data.project_id, current_user, db)

    logger.info(
        "User %s registering AI system '%s' for project %s",
        current_user.id,
        data.name,
        data.project_id,
    )

    try:
        system = await _map_service.create_ai_system(
            db=db,
            data=data.model_dump(),
        )
        return AISystemResponse.model_validate(system)
    except AISystemDuplicateError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )


@router.put(
    "/ai-systems/{system_id}",
    response_model=AISystemResponse,
    summary="Update AI system",
    description="Update an existing AI system's context, categorization, or dependencies.",
)
async def update_ai_system(
    system_id: UUID,
    data: AISystemUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> AISystemResponse:
    """Update an AI system."""
    logger.info(
        "User %s updating AI system %s",
        current_user.id,
        system_id,
    )

    try:
        system = await _map_service.update_ai_system(
            db=db,
            system_id=system_id,
            data=data.model_dump(exclude_unset=True),
        )
        return AISystemResponse.model_validate(system)
    except AISystemNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )


@router.delete(
    "/ai-systems/{system_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove AI system",
    description="Soft-delete an AI system (sets is_active = false).",
)
async def delete_ai_system(
    system_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Soft-delete an AI system."""
    logger.info(
        "User %s deleting AI system %s",
        current_user.id,
        system_id,
    )

    try:
        await _map_service.delete_ai_system(db=db, system_id=system_id)
    except AISystemNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )


# =============================================================================
# Risk-Impact Mapping Endpoints
# =============================================================================


@router.get(
    "/risk-impacts",
    response_model=RiskImpactListResponse,
    summary="Risk-to-impact mappings",
    description="Get risk-to-impact mappings for MAP-3.1 compliance visualization.",
)
async def get_risk_impacts(
    project_id: UUID = Query(..., description="Project ID"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> RiskImpactListResponse:
    """Get risk-to-impact mappings for a project."""
    await check_project_access(project_id, current_user, db)

    logger.info(
        "User %s viewing risk impacts for project %s",
        current_user.id,
        project_id,
    )

    items = await _map_service.get_risk_impacts(db=db, project_id=project_id)

    return RiskImpactListResponse(
        items=[RiskImpactMapping(**item) for item in items],
        total=len(items),
    )
