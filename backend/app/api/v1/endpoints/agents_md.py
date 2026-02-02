"""
=========================================================================
AGENTS.md API Endpoints - Multi-Repo Management
SDLC Orchestrator - Sprint 83 (Dynamic Context & Analytics)

Version: 1.0.0
Date: January 19, 2026
Status: ACTIVE - Sprint 83 (Pre-Launch Hardening)
Authority: Backend Lead + CTO Approved
Framework: SDLC 5.1.3 P7 (Documentation Permanence)

Purpose:
- Multi-repo AGENTS.md status overview
- Bulk regeneration operations
- Diff view between versions
- Dynamic context status

API Endpoints:
- GET /agents-md/repos - List repos with AGENTS.md status
- GET /agents-md/{repo_id} - Get repo AGENTS.md details
- POST /agents-md/{repo_id}/regenerate - Regenerate AGENTS.md
- POST /agents-md/bulk/regenerate - Bulk regenerate
- GET /agents-md/{repo_id}/diff - Get diff between versions
- GET /agents-md/{repo_id}/context - Get dynamic context

Zero Mock Policy: Production-ready API implementation
=========================================================================
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db, get_current_user
from app.models.agents_md import AgentsMdFile
from app.models.project import Project
from app.models.user import User
from app.services.dynamic_context_service import (
    DynamicContextService,
    DynamicContext,
    get_event_bus,
)
from app.events.lifecycle_events import GateStatus, SprintStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents-md", tags=["AGENTS.md"])


# ============================================================================
# Request/Response Models
# ============================================================================


class RepoStatus(BaseModel):
    """Repository AGENTS.md status."""

    id: UUID
    name: str
    owner: str
    full_name: str
    stage_name: str
    gate_status: str
    strict_mode: bool
    agents_md_version: Optional[str] = None
    agents_md_hash: Optional[str] = None
    last_updated: Optional[datetime] = None
    constraints_count: int = 0
    blocking_constraints: int = 0
    update_count: int = 0

    class Config:
        from_attributes = True


class RepoListResponse(BaseModel):
    """List repos response."""

    items: List[RepoStatus]
    total: int
    page: int = 1
    page_size: int = 50


class RepoDetailResponse(BaseModel):
    """Repo detail response."""

    repo: RepoStatus
    agents_md_content: Optional[str] = None
    dynamic_context: Optional[dict] = None
    recent_updates: List[dict] = []


class RegenerateRequest(BaseModel):
    """Regenerate request."""

    force: bool = False
    reason: Optional[str] = None


class BulkRegenerateRequest(BaseModel):
    """Bulk regenerate request."""

    repo_ids: List[UUID]
    force: bool = False


class BulkRegenerateResult(BaseModel):
    """Bulk regenerate result item."""

    repo_id: UUID
    status: str  # "success", "failed", "skipped"
    message: str
    new_hash: Optional[str] = None


class BulkRegenerateResponse(BaseModel):
    """Bulk regenerate response."""

    results: List[BulkRegenerateResult]
    total: int
    succeeded: int
    failed: int


class DiffResponse(BaseModel):
    """Diff response."""

    repo_id: UUID
    current_version: str
    current_hash: str
    previous_version: Optional[str] = None
    previous_hash: Optional[str] = None
    diff: str
    changed_at: Optional[datetime] = None
    change_trigger: Optional[str] = None


class DynamicContextResponse(BaseModel):
    """Dynamic context response."""

    repo_id: UUID
    current_gate: str
    gate_status: str
    current_sprint: Optional[str] = None
    sprint_number: Optional[int] = None
    sprint_status: Optional[str] = None
    sprint_goals: List[str] = []
    active_constraints: List[dict] = []
    blocking_constraints: List[dict] = []
    last_scan_passed: bool = True
    last_updated: datetime
    update_count: int


# ============================================================================
# Dependencies
# ============================================================================


async def get_dynamic_context_service(
    db: AsyncSession = Depends(get_db),
) -> DynamicContextService:
    """Get DynamicContextService instance."""
    # In production, this would be a singleton service
    # For now, create instance per request
    return DynamicContextService(db=db)


# ============================================================================
# Endpoints
# ============================================================================


@router.get("/repos", response_model=RepoListResponse)
async def list_repos(
    organization_id: Optional[UUID] = Query(None, description="Filter by organization"),
    stage_filter: Optional[str] = Query(None, description="Filter by stage name"),
    strict_mode_only: bool = Query(False, description="Only show repos in strict mode"),
    has_constraints: Optional[bool] = Query(None, description="Filter by constraint status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    context_service: DynamicContextService = Depends(get_dynamic_context_service),
) -> RepoListResponse:
    """
    List all repositories with AGENTS.md status.

    Returns summary of each repo's:
    - Current SDLC stage and gate status
    - AGENTS.md version and last update
    - Active constraints count
    - Strict mode status
    """
    # Build query for projects with GitHub repos
    query = (
        select(Project)
        .where(Project.github_repo.isnot(None))
        .where(Project.is_active == True)
    )

    if organization_id:
        query = query.where(Project.organization_id == organization_id)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply pagination
    query = query.offset((page - 1) * page_size).limit(page_size)

    # Execute query
    result = await db.execute(query)
    projects = result.scalars().all()

    # Build response
    items = []
    for project in projects:
        # Get dynamic context if available
        context = context_service.get_context(project.id)

        # Get latest AGENTS.md file
        agents_result = await db.execute(
            select(AgentsMdFile)
            .where(AgentsMdFile.project_id == project.id)
            .order_by(AgentsMdFile.generated_at.desc())
            .limit(1)
        )
        agents_md = agents_result.scalar_one_or_none()

        # Calculate status
        gate_status = context.gate_status.value if context else "pending"
        stage_name = _gate_to_stage(context.current_gate if context else "G0")
        strict_mode = context.gate_status in (GateStatus.BLOCKED,) if context else False

        # Apply filters
        if stage_filter and stage_name.lower() != stage_filter.lower():
            continue
        if strict_mode_only and not strict_mode:
            continue

        constraints_count = len(context.active_constraints) if context else 0
        blocking_count = len(context.blocking_constraints) if context else 0

        if has_constraints is not None:
            if has_constraints and constraints_count == 0:
                continue
            if not has_constraints and constraints_count > 0:
                continue

        repo_status = RepoStatus(
            id=project.id,
            name=project.github_repo or project.name,
            owner=project.github_owner or "",
            full_name=f"{project.github_owner}/{project.github_repo}" if project.github_owner else project.name,
            stage_name=stage_name,
            gate_status=gate_status,
            strict_mode=strict_mode,
            agents_md_version=agents_md.generator_version if agents_md else None,
            agents_md_hash=agents_md.content_hash[:8] if agents_md else None,
            last_updated=agents_md.generated_at if agents_md else None,
            constraints_count=constraints_count,
            blocking_constraints=blocking_count,
            update_count=context.update_count if context else 0,
        )
        items.append(repo_status)

    return RepoListResponse(
        items=items,
        total=len(items),
        page=page,
        page_size=page_size,
    )


@router.get("/{repo_id}", response_model=RepoDetailResponse)
async def get_repo_detail(
    repo_id: UUID,
    include_content: bool = Query(True, description="Include AGENTS.md content"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    context_service: DynamicContextService = Depends(get_dynamic_context_service),
) -> RepoDetailResponse:
    """
    Get detailed AGENTS.md information for a repository.

    Includes:
    - Full AGENTS.md content
    - Dynamic context state
    - Recent update history
    """
    # Get project
    result = await db.execute(
        select(Project).where(Project.id == repo_id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repository not found: {repo_id}",
        )

    # Get context
    context = context_service.get_context(repo_id)

    # Get latest AGENTS.md
    agents_result = await db.execute(
        select(AgentsMdFile)
        .where(AgentsMdFile.project_id == repo_id)
        .order_by(AgentsMdFile.generated_at.desc())
        .limit(1)
    )
    agents_md = agents_result.scalar_one_or_none()

    # Get recent updates
    history_result = await db.execute(
        select(AgentsMdFile)
        .where(AgentsMdFile.project_id == repo_id)
        .order_by(AgentsMdFile.generated_at.desc())
        .limit(10)
    )
    recent_files = history_result.scalars().all()

    recent_updates = [
        {
            "id": str(f.id),
            "version": f.generator_version,
            "hash": f.content_hash[:8],
            "generated_at": f.generated_at.isoformat() if f.generated_at else None,
            "line_count": f.line_count,
        }
        for f in recent_files
    ]

    # Build repo status
    gate_status = context.gate_status.value if context else "pending"
    stage_name = _gate_to_stage(context.current_gate if context else "G0")

    repo_status = RepoStatus(
        id=project.id,
        name=project.github_repo or project.name,
        owner=project.github_owner or "",
        full_name=f"{project.github_owner}/{project.github_repo}" if project.github_owner else project.name,
        stage_name=stage_name,
        gate_status=gate_status,
        strict_mode=False,
        agents_md_version=agents_md.generator_version if agents_md else None,
        agents_md_hash=agents_md.content_hash[:8] if agents_md else None,
        last_updated=agents_md.generated_at if agents_md else None,
        constraints_count=len(context.active_constraints) if context else 0,
        blocking_constraints=len(context.blocking_constraints) if context else 0,
        update_count=context.update_count if context else 0,
    )

    # Build dynamic context dict
    dynamic_context = None
    if context:
        dynamic_context = {
            "current_gate": context.current_gate,
            "gate_status": context.gate_status.value,
            "current_sprint": context.current_sprint,
            "sprint_number": context.sprint_number,
            "sprint_status": context.sprint_status.value if context.sprint_status else None,
            "sprint_goals": context.sprint_goals,
            "active_constraints": context.active_constraints,
            "blocking_constraints": context.blocking_constraints,
            "last_scan_passed": context.last_scan_passed,
            "last_updated": context.last_updated.isoformat(),
            "update_count": context.update_count,
        }

    return RepoDetailResponse(
        repo=repo_status,
        agents_md_content=agents_md.content if agents_md and include_content else None,
        dynamic_context=dynamic_context,
        recent_updates=recent_updates,
    )


@router.post("/{repo_id}/regenerate")
async def regenerate_agents_md(
    repo_id: UUID,
    request: RegenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    context_service: DynamicContextService = Depends(get_dynamic_context_service),
) -> dict:
    """
    Regenerate AGENTS.md for a repository.

    Forces immediate regeneration and push to GitHub.
    """
    # Get project
    result = await db.execute(
        select(Project).where(Project.id == repo_id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repository not found: {repo_id}",
        )

    # Force update
    reason = request.reason or f"Manual regeneration by {current_user.username}"
    content = await context_service.force_update(repo_id, reason)

    logger.info(
        "AGENTS.md regenerated: repo=%s user=%s reason=%s",
        repo_id,
        current_user.id,
        reason,
    )

    return {
        "status": "success",
        "repo_id": str(repo_id),
        "message": f"AGENTS.md regenerated for {project.name}",
        "content_preview": content[:500] if content else None,
    }


@router.post("/bulk/regenerate", response_model=BulkRegenerateResponse)
async def bulk_regenerate(
    request: BulkRegenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    context_service: DynamicContextService = Depends(get_dynamic_context_service),
) -> BulkRegenerateResponse:
    """
    Regenerate AGENTS.md for multiple repositories.

    Processes each repo and returns results.
    """
    results = []
    succeeded = 0
    failed = 0

    for repo_id in request.repo_ids:
        try:
            # Get project
            result = await db.execute(
                select(Project).where(Project.id == repo_id)
            )
            project = result.scalar_one_or_none()

            if not project:
                results.append(BulkRegenerateResult(
                    repo_id=repo_id,
                    status="failed",
                    message=f"Repository not found: {repo_id}",
                ))
                failed += 1
                continue

            # Force update
            reason = f"Bulk regeneration by {current_user.username}"
            content = await context_service.force_update(repo_id, reason)

            # Get new hash
            import hashlib
            new_hash = hashlib.sha256(content.encode()).hexdigest()[:8] if content else None

            results.append(BulkRegenerateResult(
                repo_id=repo_id,
                status="success",
                message=f"Regenerated for {project.name}",
                new_hash=new_hash,
            ))
            succeeded += 1

        except Exception as e:
            logger.error("Failed to regenerate %s: %s", repo_id, e)
            results.append(BulkRegenerateResult(
                repo_id=repo_id,
                status="failed",
                message=str(e),
            ))
            failed += 1

    return BulkRegenerateResponse(
        results=results,
        total=len(request.repo_ids),
        succeeded=succeeded,
        failed=failed,
    )


@router.get("/{repo_id}/diff", response_model=DiffResponse)
async def get_diff(
    repo_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DiffResponse:
    """
    Get diff between current and previous AGENTS.md versions.

    Returns unified diff format.
    """
    # Get latest 2 versions
    result = await db.execute(
        select(AgentsMdFile)
        .where(AgentsMdFile.project_id == repo_id)
        .order_by(AgentsMdFile.generated_at.desc())
        .limit(2)
    )
    versions = result.scalars().all()

    if not versions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No AGENTS.md versions found for: {repo_id}",
        )

    current = versions[0]
    previous = versions[1] if len(versions) > 1 else None

    # Generate diff
    import difflib

    current_lines = current.content.splitlines(keepends=True)
    previous_lines = previous.content.splitlines(keepends=True) if previous else []

    diff_lines = difflib.unified_diff(
        previous_lines,
        current_lines,
        fromfile="AGENTS.md (previous)",
        tofile="AGENTS.md (current)",
        lineterm="",
    )
    diff = "".join(diff_lines)

    return DiffResponse(
        repo_id=repo_id,
        current_version=current.content,
        current_hash=current.content_hash,
        previous_version=previous.content if previous else None,
        previous_hash=previous.content_hash if previous else None,
        diff=diff,
        changed_at=current.generated_at,
        change_trigger=None,  # Would come from audit log
    )


@router.get("/{repo_id}/context", response_model=DynamicContextResponse)
async def get_dynamic_context(
    repo_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    context_service: DynamicContextService = Depends(get_dynamic_context_service),
) -> DynamicContextResponse:
    """
    Get current dynamic context for a repository.

    Returns live context state including:
    - Current gate and sprint
    - Active constraints
    - Security scan status
    """
    # Get or create context
    context = context_service._get_or_create_context(repo_id)

    return DynamicContextResponse(
        repo_id=repo_id,
        current_gate=context.current_gate,
        gate_status=context.gate_status.value,
        current_sprint=context.current_sprint or None,
        sprint_number=context.sprint_number or None,
        sprint_status=context.sprint_status.value if context.sprint_status else None,
        sprint_goals=context.sprint_goals,
        active_constraints=context.active_constraints,
        blocking_constraints=context.blocking_constraints,
        last_scan_passed=context.last_scan_passed,
        last_updated=context.last_updated,
        update_count=context.update_count,
    )


# ============================================================================
# Helper Functions
# ============================================================================


def _gate_to_stage(gate_name: str) -> str:
    """Map gate name to SDLC stage."""
    mapping = {
        "G0": "DISCOVER",
        "G0.1": "DISCOVER",
        "G0.2": "DESIGN",
        "G1": "BUILD",
        "G2": "INTEGRATE",
        "G3": "TEST",
        "G4": "VALIDATE",
        "G5": "RELEASE",
    }
    return mapping.get(gate_name, "DISCOVER")
