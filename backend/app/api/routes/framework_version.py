"""
=========================================================================
Framework Version API Routes - SDLC Orchestrator
Sprint 103: Context <60 Lines + Framework Version Tracking

Version: 1.0.0
Date: January 23, 2026
Status: ACTIVE - Sprint 103 Implementation
Authority: Backend Lead + CTO Approved
Reference: docs/04-build/02-Sprint-Plans/SPRINT-103-DESIGN.md

Endpoints:
- GET /framework-version/{project_id}: Get current Framework version
- GET /framework-version/{project_id}/history: Get version history
- POST /framework-version/{project_id}: Record new version
- GET /framework-version/{project_id}/drift: Check version drift
- GET /framework-version/{project_id}/compliance: Get compliance summary

SDLC 5.2.0 Compliance:
- Framework version tracking for audit compliance
- Version drift detection for upgrade planning

Zero Mock Policy: Production-ready FastAPI routes
=========================================================================
"""

import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.project import Project, ProjectMember
from app.models.user import User
from app.services.framework_version_service import (
    CURRENT_FRAMEWORK_VERSION,
    FrameworkVersionService,
    create_framework_version_service,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/framework-version", tags=["Framework Version"])


# =============================================================================
# Request/Response Models
# =============================================================================


class FrameworkVersionResponse(BaseModel):
    """Response for Framework version."""
    id: UUID
    project_id: UUID
    version: str
    major: int
    minor: int
    patch: int
    release_notes: Optional[str] = None
    applied_at: datetime
    applied_by: Optional[UUID] = None

    class Config:
        from_attributes = True


class FrameworkVersionHistoryResponse(BaseModel):
    """Response for version history."""
    project_id: UUID
    versions: list[FrameworkVersionResponse]
    total: int


class RecordVersionRequest(BaseModel):
    """Request to record new Framework version."""
    version: str = Field(
        ...,
        description="Semantic version string (e.g., 5.2.0)",
        pattern=r'^\d+\.\d+\.\d+$',
    )
    release_notes: Optional[str] = Field(
        default=None,
        description="Optional notes about this version application",
    )


class VersionDriftResponse(BaseModel):
    """Response for version drift check."""
    project_id: UUID
    current_version: Optional[str]
    latest_version: str
    has_drift: bool
    severity: str = Field(..., description="none | info | warning | critical")
    major_drift: bool
    minor_drift: bool
    patch_drift: bool
    message: str


class ComplianceSummaryResponse(BaseModel):
    """Response for Framework compliance summary."""
    project_id: UUID
    current_version: Optional[str]
    current_applied_at: Optional[datetime]
    latest_framework_version: str
    drift: dict
    version_count: int
    versions: list[dict]


# =============================================================================
# Helper Functions
# =============================================================================


async def check_project_access(
    project_id: UUID,
    user: dict,
    db: AsyncSession,
) -> Project:
    """Check if user has access to project."""
    user_id = user.id if hasattr(user, "id") else UUID(user.get("sub"))

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

    # Check if user is owner
    if project.owner_id == user_id:
        return project

    # Check if user is member
    membership_result = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
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
# Endpoints
# =============================================================================


@router.get(
    "/{project_id}",
    response_model=FrameworkVersionResponse,
    summary="Get current Framework version",
    description="Get the current (latest) Framework version for a project.",
)
async def get_current_version(
    project_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FrameworkVersionResponse:
    """
    Get current Framework version for a project.

    Args:
        project_id: Project UUID
        current_user: Authenticated user
        db: Database session

    Returns:
        Current FrameworkVersion
    """
    await check_project_access(project_id, current_user, db)

    service = create_framework_version_service(db)
    version = await service.get_current_framework_version(project_id)

    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No Framework version recorded for this project",
        )

    return FrameworkVersionResponse.model_validate(version)


@router.get(
    "/{project_id}/history",
    response_model=FrameworkVersionHistoryResponse,
    summary="Get version history",
    description="Get Framework version history for a project.",
)
async def get_version_history(
    project_id: UUID,
    limit: int = Query(default=50, ge=1, le=100, description="Max results"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FrameworkVersionHistoryResponse:
    """
    Get Framework version history for a project.

    Args:
        project_id: Project UUID
        limit: Max results to return
        current_user: Authenticated user
        db: Database session

    Returns:
        List of FrameworkVersion records
    """
    await check_project_access(project_id, current_user, db)

    service = create_framework_version_service(db)
    versions = await service.get_version_history(project_id, limit=limit)

    return FrameworkVersionHistoryResponse(
        project_id=project_id,
        versions=[FrameworkVersionResponse.model_validate(v) for v in versions],
        total=len(versions),
    )


@router.post(
    "/{project_id}",
    response_model=FrameworkVersionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record new Framework version",
    description="Record a new Framework version for a project (e.g., after migration).",
)
async def record_version(
    project_id: UUID,
    body: RecordVersionRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FrameworkVersionResponse:
    """
    Record new Framework version for a project.

    Args:
        project_id: Project UUID
        body: Version information
        current_user: Authenticated user
        db: Database session

    Returns:
        Newly recorded FrameworkVersion
    """
    await check_project_access(project_id, current_user, db)

    user_id = None
    if hasattr(current_user, "id"):
        user_id = current_user.id
    elif current_user.get("sub"):
        try:
            user_id = UUID(current_user.get("sub"))
        except ValueError:
            pass

    service = create_framework_version_service(db)

    try:
        version = await service.record_framework_version(
            project_id=project_id,
            version=body.version,
            applied_by=user_id,
            release_notes=body.release_notes,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    return FrameworkVersionResponse.model_validate(version)


@router.get(
    "/{project_id}/drift",
    response_model=VersionDriftResponse,
    summary="Check version drift",
    description="Check if project is behind the latest Framework version.",
)
async def check_version_drift(
    project_id: UUID,
    latest_version: str = Query(
        default=CURRENT_FRAMEWORK_VERSION,
        description="Latest Framework version to compare against",
    ),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> VersionDriftResponse:
    """
    Check if project is behind latest Framework version.

    Args:
        project_id: Project UUID
        latest_version: Latest Framework version to compare against
        current_user: Authenticated user
        db: Database session

    Returns:
        VersionDrift analysis
    """
    await check_project_access(project_id, current_user, db)

    service = create_framework_version_service(db)
    drift = await service.detect_version_drift(project_id, latest_version)

    return VersionDriftResponse(
        project_id=project_id,
        current_version=drift.current,
        latest_version=drift.latest,
        has_drift=drift.drift,
        severity=drift.severity,
        major_drift=drift.major_drift,
        minor_drift=drift.minor_drift,
        patch_drift=drift.patch_drift,
        message=drift.message,
    )


@router.get(
    "/{project_id}/compliance",
    response_model=ComplianceSummaryResponse,
    summary="Get compliance summary",
    description="Get Framework compliance summary for a project.",
)
async def get_compliance_summary(
    project_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ComplianceSummaryResponse:
    """
    Get Framework compliance summary for a project.

    Args:
        project_id: Project UUID
        current_user: Authenticated user
        db: Database session

    Returns:
        Compliance summary with drift analysis
    """
    await check_project_access(project_id, current_user, db)

    service = create_framework_version_service(db)
    summary = await service.get_compliance_summary(project_id)

    return ComplianceSummaryResponse(
        project_id=UUID(summary["project_id"]),
        current_version=summary["current_version"],
        current_applied_at=summary["current_applied_at"],
        latest_framework_version=summary["latest_framework_version"],
        drift=summary["drift"],
        version_count=summary["version_count"],
        versions=summary["versions"],
    )


# =============================================================================
# Health Check
# =============================================================================


@router.get(
    "/health",
    summary="Health check",
    description="Check Framework version service health.",
)
async def health_check() -> dict:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "framework-version",
        "version": "1.0.0",
        "current_framework_version": CURRENT_FRAMEWORK_VERSION,
    }
