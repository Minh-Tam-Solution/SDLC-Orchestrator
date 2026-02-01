"""
=========================================================================
Compliance Validation Router - Sprint 123 (SPEC-0013)
SDLC Orchestrator - Stage 04 (BUILD)

Version: 1.0.0
Date: January 30, 2026
Status: ACTIVE - Sprint 123
Authority: CTO Approved (A+ Grade, 98/100)
Reference: SPEC-0013 Compliance Validation Service

Purpose:
- Calculate SDLC 6.0.0 compliance scores (10 categories × 10 points)
- Detect stage folder collisions (duplicate prefixes)
- Quick score lookup for dashboards/badges
- Score history for trend analysis

Endpoints:
- POST /projects/{project_id}/validate/compliance - Full compliance validation
- GET /projects/{project_id}/compliance/score - Quick score lookup (cached)
- POST /projects/{project_id}/validate/duplicates - Detect folder collisions
- GET /projects/{project_id}/compliance/history - Score history

Security:
- Authentication required (JWT)
- Project membership required for access

Zero Mock Policy: Production-ready compliance validation
=========================================================================
"""

import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user
from app.db.session import get_db
from app.models.project import Project, ProjectMember
from app.models.user import User
from app.models.compliance_validation import (
    ComplianceScore as ComplianceScoreModel,
    ComplianceCategory,
)
from app.schemas.compliance import (
    ComplianceScoreRequest,
    ComplianceScoreResponse,
    QuickScoreResponse,
    DuplicateDetectionRequest,
    DuplicateDetectionResponse,
    ComplianceHistoryResponse,
    ComplianceHistoryItem,
    IssuesSummary,
)
from app.services.validation.compliance_scorer import ComplianceScorerService
from app.services.validation.duplicate_detector import DuplicateFolderDetector

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projects", tags=["Compliance Validation"])


# =============================================================================
# Helper Functions
# =============================================================================


async def check_project_access(
    project_id: UUID, user: User, db: AsyncSession
) -> Project:
    """
    Check if user has access to the project.

    Args:
        project_id: UUID of the project
        user: Current user
        db: Database session

    Returns:
        Project if access granted

    Raises:
        HTTPException: If project not found or access denied
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

    # Check if user is owner
    if project.owner_id == user.id:
        return project

    # Superusers bypass membership check
    if user.is_superuser:
        return project

    # Check if user is member
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


def get_file_service():
    """Get file service for validation operations."""
    from app.services.file_service import FileService
    return FileService()


# =============================================================================
# Endpoints
# =============================================================================


@router.post(
    "/{project_id}/validate/compliance",
    response_model=ComplianceScoreResponse,
    status_code=status.HTTP_200_OK,
    summary="Calculate compliance score",
    description="Calculate SDLC 6.0.0 compliance score for a project. "
                "10 categories × 10 points = 100 maximum score.",
)
async def validate_compliance(
    project_id: UUID,
    request: ComplianceScoreRequest = ComplianceScoreRequest(),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ComplianceScoreResponse:
    """
    Calculate full compliance score for a project.

    This endpoint:
    1. Validates project access
    2. Runs 10 category checkers concurrently
    3. Calculates overall score (0-100)
    4. Caches result for 1 hour
    5. Returns detailed breakdown with recommendations

    Categories:
    1. documentation_structure (10 pts) - Stage folders, no duplicates
    2. specifications_management (10 pts) - YAML frontmatter, SPEC-XXXX
    3. claude_agents_md (10 pts) - Version headers, required sections
    4. sase_artifacts (10 pts) - CRP, MRP, VCR templates
    5. code_file_naming (10 pts) - snake_case, PascalCase conventions
    6. migration_tracking (10 pts) - Progress, deadline compliance
    7. framework_alignment (10 pts) - 7-Pillar + Section 7
    8. team_organization (10 pts) - SDLC Compliance Hub
    9. legacy_archival (10 pts) - Proper 99-legacy usage
    10. governance_documentation (10 pts) - ADRs, approvals

    Args:
        project_id: UUID of project to validate
        request: Validation options (include/exclude categories, force_refresh)
        current_user: Authenticated user
        db: Database session

    Returns:
        ComplianceScoreResponse with overall score and category breakdown
    """
    # Check project access
    await check_project_access(project_id, current_user, db)

    logger.info(
        f"Calculating compliance score for project {project_id} "
        f"by user {current_user.id}"
    )

    # Get file service for validation operations
    file_service = get_file_service()

    # Create scorer and calculate
    scorer = ComplianceScorerService(db, file_service)

    try:
        # Convert request categories to model enums if provided
        include_categories = None
        exclude_categories = None

        if request.include_categories:
            include_categories = [
                ComplianceCategory(c.value) for c in request.include_categories
            ]

        if request.exclude_categories:
            exclude_categories = [
                ComplianceCategory(c.value) for c in request.exclude_categories
            ]

        result = await scorer.calculate_score(
            project_id=project_id,
            user_id=current_user.id,
            include_categories=include_categories,
            exclude_categories=exclude_categories,
            force_refresh=request.force_refresh,
        )

        logger.info(
            f"Compliance score calculated for project {project_id}: "
            f"score={result.overall_score}/100, "
            f"issues={result.summary.total}"
        )

        return result

    except Exception as e:
        logger.error(
            f"Compliance validation failed for project {project_id}: {e}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Compliance validation failed: {str(e)}",
        )


@router.get(
    "/{project_id}/compliance/score",
    response_model=QuickScoreResponse,
    summary="Get quick compliance score",
    description="Get cached compliance score for badges and dashboards. "
                "Returns None if never calculated.",
)
async def get_quick_score(
    project_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> QuickScoreResponse:
    """
    Get quick compliance score (cached lookup only).

    This endpoint is optimized for dashboards and badges.
    Returns the most recent cached score without recalculating.

    Args:
        project_id: UUID of the project
        current_user: Authenticated user
        db: Database session

    Returns:
        QuickScoreResponse with score and last calculation time

    Raises:
        HTTPException(404): If no score has been calculated yet
    """
    # Check project access
    await check_project_access(project_id, current_user, db)

    # Get file service
    file_service = get_file_service()

    # Get quick score
    scorer = ComplianceScorerService(db, file_service)
    result = await scorer.get_quick_score(project_id)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No compliance score found. Run validation first: "
                   f"POST /api/v1/projects/{project_id}/validate/compliance",
        )

    return result


@router.post(
    "/{project_id}/validate/duplicates",
    response_model=DuplicateDetectionResponse,
    status_code=status.HTTP_200_OK,
    summary="Detect duplicate stage folders",
    description="Detect stage folder collisions in docs/ directory. "
                "Reports duplicates, missing stages, and extra folders.",
)
async def validate_duplicates(
    project_id: UUID,
    request: DuplicateDetectionRequest = DuplicateDetectionRequest(),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> DuplicateDetectionResponse:
    """
    Detect duplicate stage folders in project docs.

    Stage folders should follow SDLC 6.0.0 numbering (00-10).
    This endpoint detects:
    - Collisions: Multiple folders with same prefix (e.g., 04-Dev + 04-Test)
    - Gaps: Missing required stage folders (00-09 required)
    - Extras: Non-standard folders in docs root

    Args:
        project_id: UUID of the project
        request: Detection options (docs_path)
        current_user: Authenticated user
        db: Database session

    Returns:
        DuplicateDetectionResponse with collisions, gaps, extras

    Example:
        POST /api/v1/projects/{id}/validate/duplicates
        {"docs_path": "docs/"}

        Response:
        {
            "valid": false,
            "collisions": [{
                "stage_prefix": "04",
                "stage_name": "build",
                "folders": ["04-Development", "04-Testing"],
                "severity": "critical",
                "fix_suggestion": "mkdir -p docs/10-archive/..."
            }],
            "gaps": ["03-integrate"],
            "extras": ["99-legacy"]
        }
    """
    # Check project access
    await check_project_access(project_id, current_user, db)

    logger.info(
        f"Detecting duplicate folders for project {project_id} "
        f"by user {current_user.id}"
    )

    # Get file service
    file_service = get_file_service()

    # Create detector and run
    detector = DuplicateFolderDetector(db, file_service)

    try:
        result = await detector.detect(
            project_id=project_id,
            user_id=current_user.id,
            docs_path=request.docs_path,
        )

        if not result.valid:
            logger.warning(
                f"Duplicate folders detected for project {project_id}: "
                f"{len(result.collisions)} collision(s)"
            )
        else:
            logger.info(
                f"No duplicate folders found for project {project_id}"
            )

        return result

    except Exception as e:
        logger.error(
            f"Duplicate detection failed for project {project_id}: {e}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Duplicate detection failed: {str(e)}",
        )


@router.get(
    "/{project_id}/compliance/history",
    response_model=ComplianceHistoryResponse,
    summary="Get compliance score history",
    description="Get historical compliance scores for trend analysis.",
)
async def get_compliance_history(
    project_id: UUID,
    limit: int = Query(default=10, ge=1, le=100, description="Max results"),
    offset: int = Query(default=0, ge=0, description="Skip results"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ComplianceHistoryResponse:
    """
    Get compliance score history for a project.

    Returns historical scores sorted by calculation time (newest first).
    Useful for tracking compliance improvement over time.

    Args:
        project_id: UUID of the project
        limit: Maximum number of results (default 10)
        offset: Number of results to skip (pagination)
        current_user: Authenticated user
        db: Database session

    Returns:
        ComplianceHistoryResponse with list of historical scores
    """
    # Check project access
    await check_project_access(project_id, current_user, db)

    # Count total records
    count_stmt = (
        select(func.count())
        .select_from(ComplianceScoreModel)
        .where(ComplianceScoreModel.project_id == project_id)
    )
    count_result = await db.execute(count_stmt)
    total_count = count_result.scalar_one()

    # Get history
    stmt = (
        select(ComplianceScoreModel)
        .where(ComplianceScoreModel.project_id == project_id)
        .order_by(desc(ComplianceScoreModel.calculated_at))
        .offset(offset)
        .limit(limit)
    )

    result = await db.execute(stmt)
    scores = result.scalars().all()

    history = [
        ComplianceHistoryItem(
            id=score.id,
            overall_score=score.overall_score,
            calculated_at=score.calculated_at,
            issues_summary=IssuesSummary(**score.issues_summary),
            framework_version=score.framework_version,
        )
        for score in scores
    ]

    return ComplianceHistoryResponse(
        project_id=project_id,
        history=history,
        total_count=total_count,
    )


@router.get(
    "/{project_id}/compliance/last-check",
    response_model=Optional[DuplicateDetectionResponse],
    summary="Get last folder collision check",
    description="Get the most recent folder collision check result.",
)
async def get_last_collision_check(
    project_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Optional[DuplicateDetectionResponse]:
    """
    Get the most recent folder collision check for a project.

    Args:
        project_id: UUID of the project
        current_user: Authenticated user
        db: Database session

    Returns:
        Most recent DuplicateDetectionResponse or None if never checked
    """
    # Check project access
    await check_project_access(project_id, current_user, db)

    # Get file service
    file_service = get_file_service()

    # Get last check
    detector = DuplicateFolderDetector(db, file_service)
    result = await detector.get_last_check(project_id)

    if not result:
        return None

    return result
