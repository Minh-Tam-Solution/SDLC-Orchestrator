"""
=========================================================================
SDLC 5.0.0 Structure Validation Router
SDLC Orchestrator - Stage 03 (BUILD)

Version: 1.0.0
Date: December 5, 2025
Status: ACTIVE - Sprint 30 Day 3
Authority: Backend Lead + CTO Approved
Framework: SDLC 5.0.0 Complete Lifecycle

Purpose:
- Validate project documentation structure against SDLC 5.0.0 standards
- Store validation history for compliance tracking
- Provide compliance dashboard data

Endpoints:
- POST /projects/{id}/validate-structure - Validate SDLC structure
- GET /projects/{id}/validation-history - Get validation history
- GET /projects/{id}/compliance-summary - Get compliance summary

Security:
- Authentication required (JWT)
- Project membership required for access
- Rate limiting: 10 validations/minute per project

Zero Mock Policy: Production-ready SDLC structure validation
=========================================================================
"""

import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user
from app.db.session import get_db
from app.models.project import Project, ProjectMember
from app.models.user import User
from app.models.sdlc_validation import SDLCValidation, SDLCValidationIssue

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projects", tags=["SDLC Structure"])


# =========================================================================
# Pydantic Schemas
# =========================================================================


class SDLCTier(str):
    """SDLC tier enumeration."""
    LITE = "lite"
    STANDARD = "standard"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class ValidateStructureRequest(BaseModel):
    """Request to validate SDLC 5.0.0 structure."""

    tier: Optional[str] = Field(
        None,
        description="Override auto-detected tier: lite, standard, professional, enterprise",
    )
    docs_root: str = Field(
        default="docs",
        description="Documentation folder path relative to project root",
    )
    strict_mode: bool = Field(
        default=False,
        description="Fail on warnings in addition to errors",
    )
    include_p0: bool = Field(
        default=True,
        description="Include P0 artifact validation",
    )


class StageInfo(BaseModel):
    """Information about a detected stage."""

    stage_id: str
    stage_name: str
    folder_name: str
    file_count: int
    has_readme: bool


class P0ArtifactInfo(BaseModel):
    """Information about a P0 artifact."""

    artifact_id: str
    name: str
    stage_id: str
    found: bool
    path: Optional[str] = None
    file_size_bytes: int = 0
    has_content: bool = False


class ValidationIssue(BaseModel):
    """A validation issue (error, warning, or info)."""

    code: str
    severity: str  # error, warning, info
    message: str
    path: Optional[str] = None
    stage_id: Optional[str] = None
    fix_suggestion: Optional[str] = None


class ValidateStructureResponse(BaseModel):
    """Response from SDLC structure validation."""

    id: UUID
    project_id: UUID
    valid: bool = Field(alias="is_compliant")
    score: int = Field(ge=0, le=100, alias="compliance_score")
    tier: str
    team_size: Optional[int] = None

    # Stage information
    stages_found: List[StageInfo]
    stages_missing: List[str]
    stages_required: int

    # P0 artifact information
    p0_status: dict
    p0_artifacts: Optional[List[P0ArtifactInfo]] = None

    # Issues
    errors: int = Field(alias="error_count")
    warnings: int = Field(alias="warning_count")
    issues: List[ValidationIssue]

    # Metadata
    validated_at: datetime
    validation_time_ms: float

    class Config:
        from_attributes = True
        populate_by_name = True


class ValidationHistoryItem(BaseModel):
    """Summary of a past validation."""

    id: UUID
    valid: bool
    score: int
    tier: str
    stages_found: int
    stages_required: int
    errors: int
    warnings: int
    validated_at: datetime


class ComplianceSummary(BaseModel):
    """Compliance summary for a project."""

    project_id: UUID
    project_name: str
    tier: str
    current_score: int
    is_compliant: bool
    last_validated: Optional[datetime] = None
    validation_count: int
    score_trend: List[dict]  # [{date, score}]
    compliance_history: List[dict]  # [{date, compliant}]


# =========================================================================
# In-memory rate limiter (use Redis in production)
# =========================================================================

_rate_limit_cache: dict = {}


def check_rate_limit(project_id: UUID, max_requests: int = 10, window_seconds: int = 60) -> bool:
    """
    Check if project has exceeded rate limit.

    Returns True if rate limited, False if allowed.
    """
    key = str(project_id)
    now = datetime.utcnow()
    window_start = now - timedelta(seconds=window_seconds)

    if key not in _rate_limit_cache:
        _rate_limit_cache[key] = []

    # Clean old entries
    _rate_limit_cache[key] = [
        ts for ts in _rate_limit_cache[key] if ts > window_start
    ]

    # Check limit
    if len(_rate_limit_cache[key]) >= max_requests:
        return True

    # Add current request
    _rate_limit_cache[key].append(now)
    return False


# =========================================================================
# Helper Functions
# =========================================================================


async def check_project_access(
    project_id: UUID, user: User, db: AsyncSession
) -> Project:
    """Check if user has access to the project."""
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


def run_sdlc_validation(
    project_root: Path,
    docs_root: str = "docs",
    tier: Optional[str] = None,
    team_size: Optional[int] = None,
) -> dict:
    """
    Run SDLC 5.0.0 structure validation.

    This uses the sdlcctl validation engine.

    Args:
        project_root: Root directory of the project
        docs_root: Documentation folder name
        tier: Optional tier override
        team_size: Optional team size for tier detection

    Returns:
        Validation result dictionary
    """
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "sdlcctl"))

    try:
        from sdlcctl.validation.engine import SDLCValidator
        from sdlcctl.validation.tier import Tier

        # Parse tier
        project_tier = None
        if tier:
            try:
                project_tier = Tier(tier.lower())
            except ValueError:
                pass

        # Create validator
        validator = SDLCValidator(
            project_root=project_root,
            docs_root=docs_root,
            tier=project_tier,
            team_size=team_size,
        )

        # Run validation
        result = validator.validate()

        # Convert to dictionary
        return result.to_dict()

    except ImportError as e:
        logger.error(f"sdlcctl module not available: {e}")
        # Zero Mock Policy: Fail loudly instead of returning mock data
        raise HTTPException(
            status_code=503,
            detail={
                "error": "SDLC Validator Unavailable",
                "message": "The sdlcctl validation module is not installed or not accessible.",
                "code": "SDLC_VALIDATOR_UNAVAILABLE",
                "suggestion": "Ensure sdlcctl is installed: pip install -e ./sdlcctl",
            }
        )


def _create_fallback_result(
    project_root: Path,
    docs_root: str,
    tier: Optional[str],
) -> dict:
    """Create fallback result when sdlcctl is not available."""
    docs_path = project_root / docs_root

    # Check if docs folder exists
    if not docs_path.exists():
        return {
            "is_compliant": False,
            "compliance_score": 0,
            "tier": tier or "professional",
            "validation_time_ms": 0,
            "error_count": 1,
            "warning_count": 0,
            "summary": {
                "stages_found": 0,
                "stages_missing": 10,
                "p0_artifacts_found": 0,
                "p0_artifacts_missing": 15,
                "errors": 1,
                "warnings": 0,
                "info": 0,
            },
            "issues": [
                {
                    "code": "SDLC-001",
                    "severity": "error",
                    "message": f"Documentation folder not found: {docs_root}",
                    "path": str(docs_path),
                    "stage_id": None,
                    "fix_suggestion": f"mkdir -p {docs_root}",
                }
            ],
            "scan_result": {
                "stages_found": {},
                "stages_missing": ["00", "01", "02", "03", "04", "05", "06", "07", "08", "09"],
                "total_files": 0,
            },
            "p0_result": {
                "artifacts_checked": 15,
                "artifacts_found": 0,
                "artifacts_missing": 15,
                "coverage_percent": 0,
                "is_compliant": False,
                "results": {},
            },
            "tier_requirements": {
                "required_stages": ["00", "01", "02", "03", "04", "05", "06", "07", "08", "09"],
                "min_stages": 10,
                "p0_required": True,
            },
        }

    # Count stages
    stages_found = {}
    for stage_dir in docs_path.iterdir():
        if stage_dir.is_dir() and stage_dir.name[:2].isdigit():
            stage_id = stage_dir.name[:2]
            file_count = sum(1 for _ in stage_dir.rglob("*") if _.is_file())
            has_readme = (stage_dir / "README.md").exists()
            stages_found[stage_id] = {
                "folder_name": stage_dir.name,
                "file_count": file_count,
                "has_readme": has_readme,
            }

    stages_required = ["00", "01", "02", "03", "04", "05", "06", "07", "08", "09"]
    stages_missing = [s for s in stages_required if s not in stages_found]

    score = int((len(stages_found) / len(stages_required)) * 100) if stages_required else 100
    is_compliant = len(stages_missing) == 0

    return {
        "is_compliant": is_compliant,
        "compliance_score": score,
        "tier": tier or "professional",
        "validation_time_ms": 0,
        "error_count": len(stages_missing),
        "warning_count": 0,
        "summary": {
            "stages_found": len(stages_found),
            "stages_missing": len(stages_missing),
            "p0_artifacts_found": 0,
            "p0_artifacts_missing": 0,
            "errors": len(stages_missing),
            "warnings": 0,
            "info": 0,
        },
        "issues": [
            {
                "code": "SDLC-002",
                "severity": "error",
                "message": f"Required stage missing: {s}",
                "path": None,
                "stage_id": s,
                "fix_suggestion": f"sdlcctl fix --tier {tier or 'professional'}",
            }
            for s in stages_missing
        ],
        "scan_result": {
            "stages_found": stages_found,
            "stages_missing": stages_missing,
            "total_files": sum(s["file_count"] for s in stages_found.values()),
        },
        "p0_result": {
            "artifacts_checked": 0,
            "artifacts_found": 0,
            "artifacts_missing": 0,
            "coverage_percent": 0,
            "is_compliant": True,
            "results": {},
        },
        "tier_requirements": {
            "required_stages": stages_required,
            "min_stages": len(stages_required),
            "p0_required": True,
        },
    }


# =========================================================================
# Endpoints
# =========================================================================


@router.post(
    "/{project_id}/validate-structure",
    response_model=ValidateStructureResponse,
    status_code=status.HTTP_200_OK,
    summary="Validate SDLC 5.0.0 structure",
    description="Validate project documentation structure against SDLC 5.0.0 standards.",
    responses={
        200: {"description": "Validation completed"},
        429: {"description": "Rate limit exceeded"},
        404: {"description": "Project not found"},
        403: {"description": "Access denied"},
    },
)
async def validate_structure(
    project_id: UUID,
    request: ValidateStructureRequest = ValidateStructureRequest(),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ValidateStructureResponse:
    """
    Validate SDLC 5.0.0 structure for a project.

    This endpoint:
    1. Validates project access
    2. Checks rate limit (10/minute per project)
    3. Runs SDLC 5.0.0 structure validation
    4. Stores result in validation history
    5. Returns detailed validation result

    Args:
        project_id: UUID of project to validate
        request: Validation configuration options
        current_user: Authenticated user
        db: Database session

    Returns:
        ValidateStructureResponse with detailed validation result
    """
    # Check project access
    project = await check_project_access(project_id, current_user, db)

    # Check rate limit
    if check_rate_limit(project_id, max_requests=10, window_seconds=60):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Max 10 validations per minute per project.",
        )

    logger.info(
        f"Validating SDLC structure for project {project_id} by user {current_user.id}"
    )

    start_time = time.time()

    # Determine project root
    # In production, this would be fetched from project settings or repository
    # For now, use a default path or environment variable
    import os
    project_root = Path(os.environ.get("PROJECT_ROOT", "."))

    # If project has github_repo, could clone/checkout the repo
    # For now, assume local validation

    # Run validation
    try:
        result = run_sdlc_validation(
            project_root=project_root,
            docs_root=request.docs_root,
            tier=request.tier,
            team_size=project.team_size if hasattr(project, "team_size") else None,
        )
    except Exception as e:
        logger.error(f"SDLC validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Validation failed: {str(e)}",
        )

    validation_time_ms = (time.time() - start_time) * 1000

    # Build response
    scan_result = result.get("scan_result", {})
    p0_result = result.get("p0_result", {})
    tier_req = result.get("tier_requirements", {})

    # Convert stages_found to list of StageInfo
    stages_found_list = []
    stages_found_dict = scan_result.get("stages_found", {})

    # Stage names mapping
    stage_names = {
        "00": "Project Foundation",
        "01": "Planning & Analysis",
        "02": "Design & Architecture",
        "03": "Development & Implementation",
        "04": "Testing & QA",
        "05": "Deployment & Release",
        "06": "Operations & Monitoring",
        "07": "Integration Hub",
        "08": "Team Management",
        "09": "Executive Reports",
        "10": "Archive",
    }

    for stage_id, stage_data in stages_found_dict.items():
        if isinstance(stage_data, dict):
            stages_found_list.append(
                StageInfo(
                    stage_id=stage_id,
                    stage_name=stage_names.get(stage_id, f"Stage {stage_id}"),
                    folder_name=stage_data.get("folder_name", f"{stage_id}-Unknown"),
                    file_count=stage_data.get("file_count", 0),
                    has_readme=stage_data.get("has_readme", False),
                )
            )

    # Convert issues
    issues_list = []
    for issue in result.get("issues", []):
        issues_list.append(
            ValidationIssue(
                code=issue.get("code", "SDLC-000"),
                severity=issue.get("severity", "info"),
                message=issue.get("message", ""),
                path=issue.get("path"),
                stage_id=issue.get("stage_id"),
                fix_suggestion=issue.get("fix_suggestion"),
            )
        )

    # Store validation result in database
    import hashlib
    import json
    result_json = json.dumps(result, sort_keys=True, default=str)
    result_hash = hashlib.sha256(result_json.encode()).hexdigest()

    validation = SDLCValidation(
        project_id=project_id,
        validated_by=current_user.id,
        trigger_type="api",
        tier=result.get("tier", "professional"),
        tier_detected=request.tier is None,
        is_compliant=result.get("is_compliant", False),
        compliance_score=result.get("compliance_score", 0),
        stages_found=len(stages_found_dict),
        stages_required=len(tier_req.get("required_stages", [])),
        stages_detail=[s.model_dump() for s in stages_found_list],
        stages_missing=scan_result.get("stages_missing", []),
        p0_status={
            "total": p0_result.get("artifacts_checked", 0),
            "found": p0_result.get("artifacts_found", 0),
            "missing": p0_result.get("artifacts_missing", 0),
            "coverage": p0_result.get("coverage_percent", 0),
        },
        error_count=result.get("error_count", 0),
        warning_count=result.get("warning_count", 0),
        issues=[i.model_dump() for i in issues_list],
        validation_time_ms=validation_time_ms,
        docs_root=request.docs_root,
        strict_mode=request.strict_mode,
        result_hash=result_hash,
    )

    db.add(validation)
    await db.commit()
    await db.refresh(validation)

    logger.info(
        f"Validation result for project {project_id}: "
        f"score={result.get('compliance_score', 0)}, "
        f"compliant={result.get('is_compliant', False)}, "
        f"validation_id={validation.id}"
    )

    return ValidateStructureResponse(
        id=validation.id,
        project_id=project_id,
        is_compliant=result.get("is_compliant", False),
        compliance_score=result.get("compliance_score", 0),
        tier=result.get("tier", "professional"),
        team_size=getattr(project, "team_size", None),
        stages_found=stages_found_list,
        stages_missing=scan_result.get("stages_missing", []),
        stages_required=len(tier_req.get("required_stages", [])),
        p0_status={
            "total": p0_result.get("artifacts_checked", 0),
            "found": p0_result.get("artifacts_found", 0),
            "missing": p0_result.get("artifacts_missing", 0),
            "coverage": p0_result.get("coverage_percent", 0),
        },
        p0_artifacts=None,  # Could expand this with detailed P0 info
        error_count=result.get("error_count", 0),
        warning_count=result.get("warning_count", 0),
        issues=issues_list,
        validated_at=datetime.utcnow(),
        validation_time_ms=validation_time_ms,
    )


@router.get(
    "/{project_id}/validation-history",
    response_model=List[ValidationHistoryItem],
    summary="Get validation history",
    description="Get SDLC structure validation history for a project.",
)
async def get_validation_history(
    project_id: UUID,
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> List[ValidationHistoryItem]:
    """
    Get validation history for a project (last 30 days).

    Args:
        project_id: UUID of the project
        limit: Maximum number of results
        offset: Number of results to skip
        current_user: Authenticated user
        db: Database session

    Returns:
        List of validation history items
    """
    # Check project access
    await check_project_access(project_id, current_user, db)

    logger.info(f"Getting validation history for project {project_id}")

    # Query validation history from database
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)

    result = await db.execute(
        select(SDLCValidation)
        .where(
            SDLCValidation.project_id == project_id,
            SDLCValidation.validated_at >= thirty_days_ago,
        )
        .order_by(desc(SDLCValidation.validated_at))
        .offset(offset)
        .limit(limit)
    )
    validations = result.scalars().all()

    return [
        ValidationHistoryItem(
            id=v.id,
            valid=v.is_compliant,
            score=v.compliance_score,
            tier=v.tier,
            stages_found=v.stages_found,
            stages_required=v.stages_required,
            errors=v.error_count,
            warnings=v.warning_count,
            validated_at=v.validated_at,
        )
        for v in validations
    ]


@router.get(
    "/{project_id}/compliance-summary",
    response_model=ComplianceSummary,
    summary="Get compliance summary",
    description="Get SDLC compliance summary for a project.",
)
async def get_compliance_summary(
    project_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ComplianceSummary:
    """
    Get compliance summary for a project.

    Args:
        project_id: UUID of the project
        current_user: Authenticated user
        db: Database session

    Returns:
        Compliance summary with trend data
    """
    # Check project access
    project = await check_project_access(project_id, current_user, db)

    logger.info(f"Getting compliance summary for project {project_id}")

    # Get latest validation
    latest_result = await db.execute(
        select(SDLCValidation)
        .where(SDLCValidation.project_id == project_id)
        .order_by(desc(SDLCValidation.validated_at))
        .limit(1)
    )
    latest = latest_result.scalar_one_or_none()

    # Get validation count
    count_result = await db.execute(
        select(func.count(SDLCValidation.id))
        .where(SDLCValidation.project_id == project_id)
    )
    validation_count = count_result.scalar() or 0

    # Get trend data (last 30 days, daily aggregation)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)

    trend_result = await db.execute(
        select(
            func.date(SDLCValidation.validated_at).label("date"),
            func.max(SDLCValidation.compliance_score).label("score"),
        )
        .where(
            SDLCValidation.project_id == project_id,
            SDLCValidation.validated_at >= thirty_days_ago,
        )
        .group_by(func.date(SDLCValidation.validated_at))
        .order_by(func.date(SDLCValidation.validated_at))
    )
    trend_rows = trend_result.all()

    score_trend = [
        {"date": str(row.date), "score": row.score}
        for row in trend_rows
    ]

    # Get compliance history
    history_result = await db.execute(
        select(
            func.date(SDLCValidation.validated_at).label("date"),
            func.bool_or(SDLCValidation.is_compliant).label("compliant"),
        )
        .where(
            SDLCValidation.project_id == project_id,
            SDLCValidation.validated_at >= thirty_days_ago,
        )
        .group_by(func.date(SDLCValidation.validated_at))
        .order_by(func.date(SDLCValidation.validated_at))
    )
    history_rows = history_result.all()

    compliance_history = [
        {"date": str(row.date), "compliant": row.compliant}
        for row in history_rows
    ]

    return ComplianceSummary(
        project_id=project_id,
        project_name=project.name,
        tier=latest.tier if latest else "professional",
        current_score=latest.compliance_score if latest else 0,
        is_compliant=latest.is_compliant if latest else False,
        last_validated=latest.validated_at if latest else None,
        validation_count=validation_count,
        score_trend=score_trend,
        compliance_history=compliance_history,
    )
