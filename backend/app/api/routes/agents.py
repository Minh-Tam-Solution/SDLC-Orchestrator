"""
=========================================================================
AGENTS.md API Routes
SDLC Orchestrator - Sprint 80 (AGENTS.md Integration)

Version: 1.0.0
Date: January 19, 2026
Status: ACTIVE - Sprint 80 Implementation
Authority: Backend Lead + CTO Approved
Reference: ADR-029-AGENTS-MD-Integration-Strategy
Reference: TDS-080-001 AGENTS.md Technical Design

Purpose:
- API endpoints for AGENTS.md generation and management
- Context overlay delivery via API
- Validation and linting endpoints
- History and audit trail

Endpoints (7 total):
- POST /agents-md/generate - Generate AGENTS.md
- GET /agents-md/{project_id} - Get latest AGENTS.md
- POST /agents-md/validate - Validate AGENTS.md content
- POST /agents-md/lint - Lint and fix AGENTS.md
- GET /agents-md/{project_id}/history - Get generation history
- GET /context/{project_id} - Get dynamic context overlay
- GET /context/{project_id}/history - Get overlay history

Zero Mock Policy: Production-ready endpoint implementation
=========================================================================
"""

import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.services.agents_md_service import (
    AgentsMdService,
    AgentsMdConfig,
    AgentsMdResult,
)
from app.services.context_overlay_service import (
    ContextOverlayService,
    ContextOverlay,
)
from app.services.agents_md_validator import AgentsMdValidator
from app.services.file_analyzer import FileAnalyzer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents-md", tags=["AGENTS.md"])


# ============================================================================
# Request/Response Schemas
# ============================================================================


class GenerateRequest(BaseModel):
    """Request to generate AGENTS.md."""

    project_id: UUID = Field(..., description="Project UUID")
    project_path: Optional[str] = Field(
        None,
        description="Path to project root for file analysis (optional)",
    )
    include_quick_start: bool = Field(True, description="Include Quick Start section")
    include_architecture: bool = Field(True, description="Include Architecture section")
    include_current_stage: bool = Field(True, description="Include Current Stage section")
    include_conventions: bool = Field(True, description="Include Conventions section")
    include_security: bool = Field(True, description="Include Security section")
    include_git_workflow: bool = Field(True, description="Include Git Workflow section")
    include_do_not: bool = Field(True, description="Include DO NOT section")
    max_lines: int = Field(150, ge=50, le=200, description="Maximum lines (50-200)")
    custom_quick_start: Optional[str] = Field(None, description="Custom Quick Start content")
    custom_architecture: Optional[str] = Field(None, description="Custom Architecture content")
    custom_conventions: Optional[str] = Field(None, description="Custom Conventions content")
    custom_do_not: Optional[List[str]] = Field(None, description="Custom DO NOT rules")


class GenerateResponse(BaseModel):
    """Response from AGENTS.md generation."""

    id: Optional[str] = Field(None, description="Generation record ID")
    content: str = Field(..., description="Generated AGENTS.md content")
    content_hash: str = Field(..., description="SHA256 hash of content")
    line_count: int = Field(..., description="Number of lines")
    sections: List[str] = Field(..., description="Included sections")
    generated_at: str = Field(..., description="Generation timestamp")
    generator_version: str = Field(..., description="Generator version")
    validation_status: str = Field(..., description="Validation status")
    validation_errors: List[dict] = Field(default=[], description="Validation errors")
    validation_warnings: List[dict] = Field(default=[], description="Validation warnings")


class ValidateRequest(BaseModel):
    """Request to validate AGENTS.md content."""

    content: str = Field(..., description="AGENTS.md content to validate")


class ValidateResponse(BaseModel):
    """Response from AGENTS.md validation."""

    valid: bool = Field(..., description="Whether content is valid")
    errors: List[dict] = Field(default=[], description="Validation errors")
    warnings: List[dict] = Field(default=[], description="Validation warnings")
    line_count: int = Field(..., description="Number of lines")
    over_limit: bool = Field(..., description="Whether line count exceeds limit")


class LintRequest(BaseModel):
    """Request to lint and fix AGENTS.md content."""

    content: str = Field(..., description="AGENTS.md content to lint")


class LintResponse(BaseModel):
    """Response from AGENTS.md linting."""

    original_content: str = Field(..., description="Original content")
    fixed_content: str = Field(..., description="Fixed content")
    changes: List[str] = Field(default=[], description="Changes made")
    valid: bool = Field(..., description="Whether fixed content is valid")


class HistoryItem(BaseModel):
    """History item for AGENTS.md or context overlay."""

    id: str = Field(..., description="Record ID")
    generated_at: str = Field(..., description="Generation timestamp")
    line_count: Optional[int] = Field(None, description="Line count (AGENTS.md)")
    sections: Optional[List[str]] = Field(None, description="Sections (AGENTS.md)")
    validation_status: Optional[str] = Field(None, description="Validation status")
    trigger_type: Optional[str] = Field(None, description="Trigger type (overlay)")
    trigger_ref: Optional[str] = Field(None, description="Trigger reference (overlay)")


class ContextOverlayResponse(BaseModel):
    """Response for context overlay."""

    id: Optional[str] = Field(None, description="Overlay record ID")
    project_id: str = Field(..., description="Project UUID")
    generated_at: str = Field(..., description="Generation timestamp")
    stage_name: Optional[str] = Field(None, description="Current SDLC stage")
    gate_status: Optional[str] = Field(None, description="Latest gate status")
    sprint: Optional[dict] = Field(None, description="Active sprint context")
    constraints: List[dict] = Field(default=[], description="Active constraints")
    strict_mode: bool = Field(..., description="Whether strict mode is active")
    formatted: dict = Field(..., description="Formatted outputs for different channels")


# ============================================================================
# AGENTS.md Endpoints
# ============================================================================


class AgentsMdRepoItem(BaseModel):
    """Single repository in AGENTS.md list."""

    id: str = Field(..., description="Project UUID")
    project_name: str = Field(..., description="Project name")
    github_repo_full_name: Optional[str] = Field(None, description="GitHub repo (owner/name)")
    has_agents_md: bool = Field(..., description="Whether AGENTS.md exists")
    is_outdated: bool = Field(False, description="Whether AGENTS.md is outdated")
    validation_status: str = Field("unknown", description="Validation status (valid/invalid/unknown)")
    last_generated_at: Optional[str] = Field(None, description="Last generation timestamp ISO")
    line_count: Optional[int] = Field(None, description="Number of lines")
    generator_version: Optional[str] = Field(None, description="Generator version")


class AgentsMdReposResponse(BaseModel):
    """Response for /repos endpoint."""

    total: int = Field(..., description="Total number of repositories")
    repos: List[AgentsMdRepoItem] = Field(..., description="List of repositories")


@router.get(
    "/repos",
    response_model=AgentsMdReposResponse,
    summary="List all repositories with AGENTS.md status",
    description="Get list of all accessible projects with their AGENTS.md status.",
)
async def list_agents_md_repos(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(None, description="Filter by status: valid/invalid/missing"),
    project_id: Optional[UUID] = Query(None, description="Filter by specific project"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AgentsMdReposResponse:
    """
    List all repositories with AGENTS.md status.

    Returns paginated list of projects with:
    - AGENTS.md existence status
    - Validation status
    - Last generation timestamp
    - Line count

    Args:
        page: Page number (1-indexed)
        page_size: Items per page (1-100)
        status: Filter by status
        project_id: Filter by specific project
        current_user: Authenticated user

    Returns:
        AgentsMdReposResponse with list of repos
    """
    from sqlalchemy import select, func
    from sqlalchemy.orm import selectinload
    from app.models.project import Project
    from app.models.agents_md import AgentsMdFile

    # Sprint 88: Platform admins CANNOT access customer data
    # Build query for projects user has access to
    query = select(Project).where(Project.deleted_at.is_(None))

    # Filter by user's organization (platform admins only see their org)
    # Regular admins see all, platform admins + regular users see only their org
    is_regular_admin = current_user.is_superuser and not current_user.is_platform_admin
    if not is_regular_admin:
        query = query.where(Project.organization_id == current_user.organization_id)

    # Filter by specific project if provided
    if project_id:
        query = query.where(Project.id == project_id)

    # Execute query to get projects
    result = await db.execute(query.offset((page - 1) * page_size).limit(page_size))
    projects = result.scalars().all()

    # Get total count
    count_query = select(func.count()).select_from(Project).where(Project.deleted_at.is_(None))
    if not is_regular_admin:
        count_query = count_query.where(Project.organization_id == current_user.organization_id)
    if project_id:
        count_query = count_query.where(Project.id == project_id)
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # For each project, get latest AGENTS.md record
    repos = []
    for project in projects:
        # Get latest AGENTS.md record for this project
        record_query = (
            select(AgentsMdFile)
            .where(AgentsMdFile.project_id == project.id)
            .order_by(AgentsMdFile.generated_at.desc())
            .limit(1)
        )
        record_result = await db.execute(record_query)
        record = record_result.scalar_one_or_none()

        # Build repo item
        has_agents_md = record is not None
        validation_status = record.validation_status if record else "unknown"

        # Apply status filter
        if status == "valid" and validation_status != "valid":
            continue
        elif status == "invalid" and validation_status != "invalid":
            continue
        elif status == "missing" and has_agents_md:
            continue

        repos.append(
            AgentsMdRepoItem(
                id=str(project.id),
                project_name=project.name,
                github_repo_full_name=project.github_repo_full_name,
                has_agents_md=has_agents_md,
                is_outdated=False,  # TODO: Implement outdated detection logic
                validation_status=validation_status,
                last_generated_at=record.generated_at.isoformat() if record else None,
                line_count=record.line_count if record else None,
                generator_version=record.generator_version if record else None,
            )
        )

    return AgentsMdReposResponse(total=total, repos=repos)


@router.post(
    "/generate",
    response_model=GenerateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate AGENTS.md",
    description="Generate AGENTS.md from project configuration analysis.",
)
async def generate_agents_md(
    data: GenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> GenerateResponse:
    """
    Generate AGENTS.md for a project.

    Analyzes project structure and generates AGENTS.md content with:
    - Quick Start commands (from docker-compose, package.json)
    - Architecture overview (from project structure)
    - Current Stage (static note about dynamic delivery)
    - Conventions (from linter configs)
    - Security rules (OWASP, AGPL containment)
    - Git Workflow (branch naming, commit format)
    - DO NOT rules (Zero Mock Policy, etc.)

    Args:
        data: Generation configuration
        current_user: Authenticated user

    Returns:
        GenerateResponse with content and metadata
    """
    try:
        # Build config
        config = AgentsMdConfig(
            include_quick_start=data.include_quick_start,
            include_architecture=data.include_architecture,
            include_current_stage=data.include_current_stage,
            include_conventions=data.include_conventions,
            include_security=data.include_security,
            include_git_workflow=data.include_git_workflow,
            include_do_not=data.include_do_not,
            max_lines=data.max_lines,
            custom_quick_start=data.custom_quick_start,
            custom_architecture=data.custom_architecture,
            custom_conventions=data.custom_conventions,
            custom_do_not=data.custom_do_not,
        )

        # Create service and generate
        file_analyzer = FileAnalyzer(data.project_path) if data.project_path else None
        service = AgentsMdService(db, file_analyzer=file_analyzer)

        result = await service.generate(
            project_id=data.project_id,
            config=config,
            user_id=current_user.id,
            project_path=data.project_path,
        )

        logger.info(
            f"Generated AGENTS.md for project {data.project_id}: "
            f"{result.line_count} lines, {len(result.sections)} sections"
        )

        return GenerateResponse(
            id=str(result.id) if result.id else None,
            content=result.content,
            content_hash=result.content_hash,
            line_count=result.line_count,
            sections=result.sections,
            generated_at=result.generated_at.isoformat(),
            generator_version=result.generator_version,
            validation_status=result.validation_status,
            validation_errors=result.validation_errors,
            validation_warnings=result.validation_warnings,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Failed to generate AGENTS.md: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Generation failed: {str(e)}",
        )


@router.get(
    "/{project_id}",
    response_model=GenerateResponse,
    summary="Get latest AGENTS.md",
    description="Get the latest generated AGENTS.md for a project.",
)
async def get_latest_agents_md(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> GenerateResponse:
    """
    Get the latest AGENTS.md for a project.

    Args:
        project_id: Project UUID
        current_user: Authenticated user

    Returns:
        GenerateResponse with latest content

    Raises:
        404 if no AGENTS.md found for project
    """
    service = AgentsMdService(db)
    record = await service.get_latest(project_id)

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No AGENTS.md found for project {project_id}. Generate one first.",
        )

    return GenerateResponse(
        id=str(record.id),
        content=record.content,
        content_hash=record.content_hash,
        line_count=record.line_count,
        sections=record.sections,
        generated_at=record.generated_at.isoformat(),
        generator_version=record.generator_version,
        validation_status=record.validation_status,
        validation_errors=record.validation_errors or [],
        validation_warnings=record.validation_warnings or [],
    )


@router.post(
    "/validate",
    response_model=ValidateResponse,
    summary="Validate AGENTS.md",
    description="Validate AGENTS.md content for secrets, structure, and line limits.",
)
async def validate_agents_md(
    data: ValidateRequest,
    current_user: User = Depends(get_current_user),
) -> ValidateResponse:
    """
    Validate AGENTS.md content.

    Checks:
    - No secrets (API keys, tokens, passwords)
    - Line limit (≤150 recommended, ≤200 max)
    - Required sections
    - Markdown structure

    Args:
        data: Content to validate
        current_user: Authenticated user

    Returns:
        ValidateResponse with validation results
    """
    validator = AgentsMdValidator()
    result = validator.validate(data.content)

    line_count = data.content.count('\n') + 1
    over_limit = line_count > 150

    return ValidateResponse(
        valid=result.valid,
        errors=[e.dict() for e in result.errors],
        warnings=[w.dict() for w in result.warnings],
        line_count=line_count,
        over_limit=over_limit,
    )


@router.post(
    "/lint",
    response_model=LintResponse,
    summary="Lint AGENTS.md",
    description="Lint and auto-fix AGENTS.md content.",
)
async def lint_agents_md(
    data: LintRequest,
    current_user: User = Depends(get_current_user),
) -> LintResponse:
    """
    Lint and fix AGENTS.md content.

    Fixes:
    - Trailing whitespace
    - Multiple blank lines
    - Missing headers
    - Markdown formatting

    Args:
        data: Content to lint
        current_user: Authenticated user

    Returns:
        LintResponse with fixed content and changes
    """
    validator = AgentsMdValidator()
    fixed_content, changes = validator.lint(data.content)

    # Validate fixed content
    validation = validator.validate(fixed_content)

    return LintResponse(
        original_content=data.content,
        fixed_content=fixed_content,
        changes=changes,
        valid=validation.valid,
    )


@router.get(
    "/{project_id}/history",
    response_model=List[HistoryItem],
    summary="Get AGENTS.md history",
    description="Get generation history for a project.",
)
async def get_agents_md_history(
    project_id: UUID,
    limit: int = Query(10, ge=1, le=100, description="Maximum items to return"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[HistoryItem]:
    """
    Get AGENTS.md generation history for a project.

    Args:
        project_id: Project UUID
        limit: Maximum items to return (1-100)
        current_user: Authenticated user

    Returns:
        List of history items
    """
    service = AgentsMdService(db)
    records = await service.get_history(project_id, limit=limit)

    return [
        HistoryItem(
            id=str(record.id),
            generated_at=record.generated_at.isoformat(),
            line_count=record.line_count,
            sections=record.sections,
            validation_status=record.validation_status,
        )
        for record in records
    ]


# ============================================================================
# Context Overlay Endpoints
# ============================================================================


context_router = APIRouter(prefix="/context", tags=["Context Overlay"])


@context_router.get(
    "/{project_id}",
    response_model=ContextOverlayResponse,
    summary="Get context overlay",
    description="Get dynamic context overlay for a project.",
)
async def get_context_overlay(
    project_id: UUID,
    format: str = Query(
        "all",
        description="Output format: all, pr_comment, cli, check_run, vscode, json",
    ),
    trigger_type: str = Query("api", description="Trigger type for audit"),
    trigger_ref: Optional[str] = Query(None, description="Trigger reference"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ContextOverlayResponse:
    """
    Get dynamic context overlay for a project.

    Returns current:
    - SDLC stage and gate status
    - Active sprint context (goal, velocity, days remaining)
    - Active constraints (strict mode, security reviews, AGPL)

    Formatted for:
    - PR comments (visible to Cursor, Copilot)
    - CLI output (terminal display)
    - GitHub Check Run output
    - VS Code Extension panel
    - JSON (API consumers)

    Args:
        project_id: Project UUID
        format: Output format preference
        trigger_type: What triggered this overlay (for audit)
        trigger_ref: Reference for trigger (PR number, etc.)
        current_user: Authenticated user

    Returns:
        ContextOverlayResponse with formatted outputs
    """
    try:
        service = ContextOverlayService(db)

        overlay = await service.get_overlay(
            project_id=project_id,
            trigger_type=trigger_type,
            trigger_ref=trigger_ref,
            save_to_db=True,
        )

        # Generate formatted outputs
        formatted = {}

        if format in ["all", "pr_comment"]:
            formatted["pr_comment"] = service.format_pr_comment(overlay)

        if format in ["all", "cli"]:
            formatted["cli"] = service.format_cli_output(overlay)

        if format in ["all", "check_run"]:
            formatted["check_run"] = service.format_check_run_output(overlay)

        if format in ["all", "vscode"]:
            formatted["vscode"] = service.format_vscode_panel(overlay)

        if format in ["all", "json"]:
            formatted["json"] = service.format_json(overlay)

        logger.info(
            f"Generated context overlay for project {project_id}: "
            f"stage={overlay.stage_name}, strict={overlay.strict_mode}"
        )

        return ContextOverlayResponse(
            id=str(overlay.id) if overlay.id else None,
            project_id=str(overlay.project_id),
            generated_at=overlay.generated_at.isoformat(),
            stage_name=overlay.stage_name,
            gate_status=overlay.gate_status,
            sprint=overlay.sprint.dict() if overlay.sprint else None,
            constraints=[c.dict() for c in overlay.constraints],
            strict_mode=overlay.strict_mode,
            formatted=formatted,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Failed to get context overlay: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get context: {str(e)}",
        )


@context_router.get(
    "/{project_id}/history",
    response_model=List[HistoryItem],
    summary="Get context overlay history",
    description="Get context overlay delivery history for a project.",
)
async def get_context_history(
    project_id: UUID,
    limit: int = Query(10, ge=1, le=100, description="Maximum items to return"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[HistoryItem]:
    """
    Get context overlay history for a project.

    Args:
        project_id: Project UUID
        limit: Maximum items to return (1-100)
        current_user: Authenticated user

    Returns:
        List of history items
    """
    service = ContextOverlayService(db)
    records = await service.get_history(project_id, limit=limit)

    return [
        HistoryItem(
            id=str(record.id),
            generated_at=record.generated_at.isoformat(),
            trigger_type=record.trigger_type,
            trigger_ref=record.trigger_ref,
        )
        for record in records
    ]


# Register context router under main router
router.include_router(context_router)
