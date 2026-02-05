"""
=========================================================================
Compliance Framework Router - Shared Compliance API
SDLC Orchestrator - Sprint 156 (Phase 3: COMPLIANCE)

Version: 1.0.0
Date: April 7, 2026
Status: ACTIVE
Authority: CTO Approved
Framework: SDLC 6.0.4
Reference: ADR-051

Purpose:
Shared API endpoints for compliance framework management:
- List all compliance frameworks (NIST, EU AI Act, ISO 42001)
- Get framework details with control count
- List per-project assessments with filters

These endpoints serve all 3 compliance frameworks. Framework-specific
endpoints (NIST GOVERN, EU AI Act, ISO 42001) are in separate routers.

Endpoints:
- GET  /compliance/frameworks              - List frameworks
- GET  /compliance/frameworks/{code}       - Get framework by code
- GET  /compliance/projects/{pid}/assessments - List project assessments

Security:
- Authentication required (JWT)
- Project membership required for assessment access

Zero Mock Policy: Production-ready implementation
=========================================================================
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user
from app.db.session import get_db
from app.models.compliance import (
    ComplianceAssessment,
    ComplianceControl,
    ComplianceFramework,
)
from app.models.user import User
from app.schemas.compliance_framework import (
    AssessmentListResponse,
    AssessmentResponse,
    ControlResponse,
    FrameworkListResponse,
    FrameworkResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/compliance",
    tags=["Compliance Framework"],
)


# =============================================================================
# Helper Functions
# =============================================================================


async def check_project_access(
    project_id: UUID, user: User, db: AsyncSession
) -> None:
    """Check if user has access to project. Raises 403 if not."""
    from app.models.project import Project

    query = select(Project).where(Project.id == project_id)
    result = await db.execute(query)
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    # Check if user owns project or is a member
    if project.owner_id != user.id:
        # TODO: Check project membership when teams are implemented
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this project"
        )


# =============================================================================
# Framework Endpoints
# =============================================================================


@router.get(
    "/frameworks",
    response_model=FrameworkListResponse,
    summary="List compliance frameworks",
    description="""
    List all compliance frameworks registered in the system.

    Returns frameworks with metadata including:
    - Framework code (NIST_AI_RMF, EU_AI_ACT, ISO_42001)
    - Version and description
    - Total control count
    - Active status

    By default, only active frameworks are returned.
    """,
)
async def list_frameworks(
    active_only: bool = Query(True, description="Only return active frameworks"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> FrameworkListResponse:
    """List all compliance frameworks."""
    logger.info(f"User {current_user.id} listing compliance frameworks (active_only={active_only})")

    query = select(ComplianceFramework)
    if active_only:
        query = query.where(ComplianceFramework.is_active == True)
    query = query.order_by(ComplianceFramework.code)

    result = await db.execute(query)
    frameworks = result.scalars().all()

    return FrameworkListResponse(
        items=[FrameworkResponse.model_validate(f) for f in frameworks],
        total=len(frameworks),
    )


@router.get(
    "/frameworks/{code}",
    response_model=FrameworkResponse,
    summary="Get compliance framework",
    description="""
    Get a compliance framework by its code.

    Valid codes: NIST_AI_RMF, EU_AI_ACT, ISO_42001

    Returns framework details including control count.
    """,
)
async def get_framework(
    code: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> FrameworkResponse:
    """Get compliance framework by code."""
    code_upper = code.upper().strip()

    query = select(ComplianceFramework).where(
        ComplianceFramework.code == code_upper
    )
    result = await db.execute(query)
    framework = result.scalar_one_or_none()

    if not framework:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Compliance framework '{code_upper}' not found. "
            f"Valid codes: NIST_AI_RMF, EU_AI_ACT, ISO_42001",
        )

    return FrameworkResponse.model_validate(framework)


# =============================================================================
# Assessment Endpoints
# =============================================================================


@router.get(
    "/projects/{project_id}/assessments",
    response_model=AssessmentListResponse,
    summary="List project assessments",
    description="""
    List compliance assessments for a project.

    Filters:
    - framework_code: Filter by framework (NIST_AI_RMF, EU_AI_ACT, ISO_42001)
    - status: Filter by status (not_started, in_progress, compliant, non_compliant, not_applicable)
    - limit/offset: Pagination
    """,
)
async def list_project_assessments(
    project_id: UUID,
    framework_code: Optional[str] = Query(None, description="Filter by framework code"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    limit: int = Query(50, ge=1, le=200, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Skip results"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> AssessmentListResponse:
    """List compliance assessments for a project."""
    # Authorization: Check project access
    await check_project_access(project_id, current_user, db)

    logger.info(f"User {current_user.id} listing assessments for project {project_id}")

    # Build base query with join to control and framework
    query = (
        select(ComplianceAssessment)
        .where(ComplianceAssessment.project_id == project_id)
    )

    # Apply framework filter via control→framework join
    if framework_code:
        framework_code_upper = framework_code.upper().strip()
        query = query.join(
            ComplianceControl,
            ComplianceAssessment.control_id == ComplianceControl.id,
        ).join(
            ComplianceFramework,
            ComplianceControl.framework_id == ComplianceFramework.id,
        ).where(
            ComplianceFramework.code == framework_code_upper
        )

    # Apply status filter
    if status_filter:
        query = query.where(ComplianceAssessment.status == status_filter)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply pagination
    query = query.order_by(ComplianceAssessment.created_at.desc())
    query = query.limit(limit).offset(offset)

    result = await db.execute(query)
    assessments = result.scalars().all()

    return AssessmentListResponse(
        items=[AssessmentResponse.model_validate(a) for a in assessments],
        total=total,
        limit=limit,
        offset=offset,
        has_more=(offset + limit) < total,
    )
