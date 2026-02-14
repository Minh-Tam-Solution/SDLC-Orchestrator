"""
=========================================================================
Context Authority API Routes V1 - DEPRECATED
SDLC Orchestrator - Sprint 147 (Spring Cleaning)

Version: 1.1.0
Date: February 4, 2026
Status: DEPRECATED - Use /context-authority/v2 instead
Sunset Date: March 6, 2026 (30 days)
Authority: CTO Approved
Framework: SDLC 6.0.5 API Deprecation Policy

DEPRECATION NOTICE:
All V1 endpoints in this file are deprecated and will be removed on
March 6, 2026. Please migrate to the V2 API at /context-authority/v2.

Migration Guide:
- POST /validate → POST /v2/validate (gate-aware validation)
- GET /adrs → Use V2 snapshot/overlay system
- Other endpoints → See /docs/migration/context-authority-v2.md

Deprecated Endpoints:
- POST /context-authority/validate
- GET /context-authority/adrs
- GET /context-authority/adrs/{adr_id}
- POST /context-authority/check-adr-linkage
- POST /context-authority/check-spec
- GET /context-authority/agents-md
- GET /context-authority/health

Zero Mock Policy: Real validation with file checks
=========================================================================
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel, Field

from app.utils.deprecation import (
    add_deprecation_headers,
    CONTEXT_AUTHORITY_V1_SUNSET,
)

from app.services.governance.context_authority import (
    ContextAuthorityEngineV1,
    ContextValidationResult,
    ContextViolationType,
    ViolationSeverity,
    ADR,
    ADRStatus,
    CodeSubmission as ServiceCodeSubmission,
    get_context_authority_engine,
)

logger = logging.getLogger(__name__)

# V1 Router - DEPRECATED (Sunset: March 6, 2026)
router = APIRouter(
    prefix="/context-authority",
    tags=["Context Authority V1 (DEPRECATED)"],
    deprecated=True,
)

# Deprecation constants
V1_SUNSET = CONTEXT_AUTHORITY_V1_SUNSET
V1_SUCCESSOR = "/context-authority/v2"
V1_MIGRATION_GUIDE = "/docs/migration/context-authority-v2.md"


# ============================================================================
# Request/Response Models
# ============================================================================


class ContextValidationRequest(BaseModel):
    """Request model for context validation."""

    submission_id: UUID = Field(..., description="Unique submission ID")
    project_id: UUID = Field(..., description="Project ID")
    changed_files: List[str] = Field(..., min_length=1, description="Changed file paths")
    affected_modules: List[str] = Field(
        default_factory=list,
        description="Affected module names",
    )
    task_id: Optional[str] = Field(None, description="Task ID (e.g., TASK-123)")
    is_new_feature: bool = Field(False, description="Whether this is a new feature")
    repo_path: Optional[str] = Field(None, description="Repository root path (optional)")


class ViolationResponse(BaseModel):
    """Response model for a violation."""

    type: str
    severity: str
    message: str
    file_path: Optional[str]
    module: Optional[str]
    fix: Optional[str]
    cli_command: Optional[str]
    related_adr: Optional[str]


class ContextValidationResponse(BaseModel):
    """Response model for context validation."""

    valid: bool = Field(..., description="Whether context is valid")
    violations_count: int = Field(..., description="Number of errors")
    warnings_count: int = Field(..., description="Number of warnings")
    violations: List[ViolationResponse]
    warnings: List[ViolationResponse]
    adr_count: int = Field(..., description="Total ADRs in repository")
    linked_adrs: List[str] = Field(..., description="ADRs linked to submission")
    spec_found: bool = Field(..., description="Whether design spec was found")
    agents_md_fresh: bool = Field(..., description="Whether AGENTS.md is fresh")
    module_consistency: bool = Field(..., description="Whether modules are consistent")
    validated_at: datetime


class ADRResponse(BaseModel):
    """Response model for an ADR."""

    id: str
    title: str
    status: str
    file_path: str
    modules: List[str]
    tags: List[str]


class ADRListResponse(BaseModel):
    """Response model for ADR list."""

    total: int
    adrs: List[ADRResponse]
    statuses: Dict[str, int]


class ADRLinkageRequest(BaseModel):
    """Request model for checking ADR linkage."""

    modules: List[str] = Field(..., min_length=1, description="Modules to check")
    changed_files: List[str] = Field(
        default_factory=list,
        description="Optional changed files for annotation extraction",
    )
    repo_path: Optional[str] = Field(None, description="Repository root path")


class ADRLinkageResponse(BaseModel):
    """Response model for ADR linkage check."""

    modules_checked: int
    modules_linked: int
    modules_orphaned: int
    linkage: Dict[str, List[str]]  # module -> [adr_ids]
    orphan_modules: List[str]
    deprecated_links: List[Dict[str, str]]


class SpecCheckRequest(BaseModel):
    """Request model for design spec check."""

    task_id: str = Field(..., description="Task ID (e.g., TASK-123)")
    repo_path: Optional[str] = Field(None, description="Repository root path")


class SpecCheckResponse(BaseModel):
    """Response model for design spec check."""

    task_id: str
    spec_found: bool
    spec_path: Optional[str]
    is_empty: bool
    word_count: int
    message: str


class AgentsMdResponse(BaseModel):
    """Response model for AGENTS.md status."""

    exists: bool
    file_path: str
    last_modified: Optional[datetime]
    age_days: int
    is_stale: bool
    staleness_threshold_days: int
    line_count: int
    message: str


# ============================================================================
# Endpoints
# ============================================================================


@router.post(
    "/validate",
    response_model=ContextValidationResponse,
    summary="[DEPRECATED] Validate code context linkage",
    deprecated=True,
    description="""
    **⚠️ DEPRECATED**: This endpoint will be removed on March 6, 2026.
    Use `POST /context-authority/v2/validate` instead for gate-aware validation.

    Validate that code submission has proper context linkage.

    Performs 4 checks:
    1. **ADR Linkage**: Every module must reference at least one ADR
    2. **Design Doc Reference**: New features must have spec files
    3. **AGENTS.md Freshness**: Context file should be updated within 7 days
    4. **Module Annotation Consistency**: @module header must match directory

    **Philosophy**: "Orphan Code = Rejected Code"

    **V1 Scope** (Metadata Only):
    - File existence checks
    - Pattern matching for annotations
    - Simple text search in ADR content

    **Migration**: The V2 API adds gate-aware context overlays and dynamic AGENTS.md updates.
    """,
)
async def validate_context(
    request: ContextValidationRequest,
    response: Response,
    engine: ContextAuthorityEngineV1 = Depends(get_context_authority_engine),
) -> ContextValidationResponse:
    """Validate code context linkage."""
    # Convert request to service submission
    submission = ServiceCodeSubmission(
        submission_id=request.submission_id,
        project_id=request.project_id,
        changed_files=request.changed_files,
        affected_modules=request.affected_modules,
        task_id=request.task_id,
        is_new_feature=request.is_new_feature,
        repo_path=request.repo_path,
    )

    # Validate context
    try:
        result = await engine.validate_context(submission)
    except Exception as e:
        logger.error(f"Context validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Context validation failed: {str(e)}",
        )

    logger.info(
        f"Context validation: {'PASS' if result.valid else 'FAIL'} - "
        f"{len(result.violations)} errors, {len(result.warnings)} warnings"
    )

    # Add deprecation headers (Sprint 147)
    add_deprecation_headers(
        response=response,
        removal_date=V1_SUNSET,
        successor_version=f"{V1_SUCCESSOR}/validate",
        migration_guide=V1_MIGRATION_GUIDE,
        reason="Use V2 for gate-aware context validation",
    )

    return ContextValidationResponse(
        valid=result.valid,
        violations_count=len(result.violations),
        warnings_count=len(result.warnings),
        violations=[
            ViolationResponse(
                type=v.type.value,
                severity=v.severity.value,
                message=v.message,
                file_path=v.file_path,
                module=v.module,
                fix=v.fix,
                cli_command=v.cli_command,
                related_adr=v.related_adr,
            )
            for v in result.violations
        ],
        warnings=[
            ViolationResponse(
                type=w.type.value,
                severity=w.severity.value,
                message=w.message,
                file_path=w.file_path,
                module=w.module,
                fix=w.fix,
                cli_command=w.cli_command,
                related_adr=w.related_adr,
            )
            for w in result.warnings
        ],
        adr_count=result.adr_count,
        linked_adrs=result.linked_adrs,
        spec_found=result.spec_found,
        agents_md_fresh=result.agents_md_fresh,
        module_consistency=result.module_consistency,
        validated_at=result.validated_at,
    )


@router.get(
    "/adrs",
    response_model=ADRListResponse,
    summary="[DEPRECATED] List all ADRs",
    deprecated=True,
    description="""
    **⚠️ DEPRECATED**: This endpoint will be removed on March 6, 2026.
    Use the V2 snapshot/overlay system for ADR management.

    Get list of all ADRs in the repository with their status.
    """,
)
async def list_adrs(
    response: Response,
    status_filter: Optional[str] = Query(
        None,
        description="Filter by status (proposed, accepted, deprecated, superseded)",
    ),
    engine: ContextAuthorityEngineV1 = Depends(get_context_authority_engine),
) -> ADRListResponse:
    """List all ADRs."""
    # Get ADR cache
    all_adrs = list(engine._adr_cache.values())

    # Filter by status if specified
    if status_filter:
        try:
            filter_status = ADRStatus(status_filter.lower())
            all_adrs = [a for a in all_adrs if a.status == filter_status]
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {status_filter}. Must be one of: proposed, accepted, deprecated, superseded",
            )

    # Calculate status distribution
    status_counts: Dict[str, int] = {}
    for adr in engine._adr_cache.values():
        status_name = adr.status.value
        status_counts[status_name] = status_counts.get(status_name, 0) + 1

    # Add deprecation headers (Sprint 147)
    add_deprecation_headers(
        response=response,
        removal_date=V1_SUNSET,
        successor_version=f"{V1_SUCCESSOR}/templates",
        migration_guide=V1_MIGRATION_GUIDE,
        reason="Use V2 overlay templates for ADR management",
    )

    return ADRListResponse(
        total=len(all_adrs),
        adrs=[
            ADRResponse(
                id=adr.id,
                title=adr.title,
                status=adr.status.value,
                file_path=adr.file_path,
                modules=adr.modules,
                tags=adr.tags,
            )
            for adr in sorted(all_adrs, key=lambda a: a.id)
        ],
        statuses=status_counts,
    )


@router.get(
    "/adrs/{adr_id}",
    response_model=ADRResponse,
    summary="[DEPRECATED] Get specific ADR",
    deprecated=True,
    description="""
    **⚠️ DEPRECATED**: This endpoint will be removed on March 6, 2026.
    Use V2 snapshot/overlay system for ADR management.

    Get details of a specific ADR by ID.
    """,
)
async def get_adr(
    adr_id: str,
    response: Response,
    engine: ContextAuthorityEngineV1 = Depends(get_context_authority_engine),
) -> ADRResponse:
    """Get specific ADR."""
    adr_id_upper = adr_id.upper()

    if adr_id_upper not in engine._adr_cache:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ADR not found: {adr_id}",
        )

    adr = engine._adr_cache[adr_id_upper]

    # Add deprecation headers (Sprint 147)
    add_deprecation_headers(
        response=response,
        removal_date=V1_SUNSET,
        successor_version=f"{V1_SUCCESSOR}/templates",
        migration_guide=V1_MIGRATION_GUIDE,
        reason="Use V2 overlay templates for ADR management",
    )

    return ADRResponse(
        id=adr.id,
        title=adr.title,
        status=adr.status.value,
        file_path=adr.file_path,
        modules=adr.modules,
        tags=adr.tags,
    )


@router.post(
    "/check-adr-linkage",
    response_model=ADRLinkageResponse,
    summary="[DEPRECATED] Check ADR linkage for modules",
    deprecated=True,
    description="""
    **⚠️ DEPRECATED**: This endpoint will be removed on March 6, 2026.
    Use `POST /context-authority/v2/validate` for comprehensive validation.

    Check if modules have proper ADR linkage.
    """,
)
async def check_adr_linkage(
    request: ADRLinkageRequest,
    response: Response,
    engine: ContextAuthorityEngineV1 = Depends(get_context_authority_engine),
) -> ADRLinkageResponse:
    """Check ADR linkage for modules."""
    repo_path = request.repo_path or engine._get_default_repo_path()

    linkage: Dict[str, List[str]] = {}
    orphan_modules: List[str] = []
    deprecated_links: List[Dict[str, str]] = []

    for module in request.modules:
        module_adrs = await engine._find_adrs_for_module(
            module,
            request.changed_files,
            repo_path,
        )

        linkage[module] = module_adrs

        if not module_adrs:
            orphan_modules.append(module)
        else:
            # Check for deprecated ADRs
            for adr_id in module_adrs:
                if adr_id in engine._adr_cache:
                    adr = engine._adr_cache[adr_id]
                    if adr.status == ADRStatus.DEPRECATED:
                        deprecated_links.append({
                            "module": module,
                            "adr_id": adr_id,
                            "adr_title": adr.title,
                        })

    # Add deprecation headers (Sprint 147)
    add_deprecation_headers(
        response=response,
        removal_date=V1_SUNSET,
        successor_version=f"{V1_SUCCESSOR}/validate",
        migration_guide=V1_MIGRATION_GUIDE,
        reason="Use V2 validate for comprehensive linkage checks",
    )

    return ADRLinkageResponse(
        modules_checked=len(request.modules),
        modules_linked=len(request.modules) - len(orphan_modules),
        modules_orphaned=len(orphan_modules),
        linkage=linkage,
        orphan_modules=orphan_modules,
        deprecated_links=deprecated_links,
    )


@router.post(
    "/check-spec",
    response_model=SpecCheckResponse,
    summary="[DEPRECATED] Check design spec existence",
    deprecated=True,
    description="""
    **⚠️ DEPRECATED**: This endpoint will be removed on March 6, 2026.
    Use `POST /context-authority/v2/validate` for spec checking.

    Check if a design specification document exists for a task.
    """,
)
async def check_spec(
    request: SpecCheckRequest,
    response: Response,
    engine: ContextAuthorityEngineV1 = Depends(get_context_authority_engine),
) -> SpecCheckResponse:
    """Check design spec existence."""
    repo_path = request.repo_path or engine._get_default_repo_path()

    # Look for spec file
    spec_patterns = [
        f"{request.task_id}-spec.md",
        f"{request.task_id.lower()}-spec.md",
        f"{request.task_id.replace('-', '_')}-spec.md",
    ]

    spec_dir = Path(repo_path) / engine.spec_path
    spec_found = False
    spec_path: Optional[str] = None
    is_empty = False
    word_count = 0

    if spec_dir.exists():
        for pattern in spec_patterns:
            spec_file = spec_dir / pattern
            if spec_file.exists():
                spec_found = True
                spec_path = str(spec_file)
                content = spec_file.read_text()
                word_count = len(content.split())
                is_empty = word_count < 50  # Less than 50 words = effectively empty
                break

    if spec_found:
        if is_empty:
            message = f"Spec exists but is effectively empty ({word_count} words)"
        else:
            message = f"Spec found with {word_count} words"
    else:
        message = f"No spec found for {request.task_id}"

    # Add deprecation headers (Sprint 147)
    add_deprecation_headers(
        response=response,
        removal_date=V1_SUNSET,
        successor_version=f"{V1_SUCCESSOR}/validate",
        migration_guide=V1_MIGRATION_GUIDE,
        reason="Use V2 validate for spec checking",
    )

    return SpecCheckResponse(
        task_id=request.task_id,
        spec_found=spec_found,
        spec_path=spec_path,
        is_empty=is_empty,
        word_count=word_count,
        message=message,
    )


@router.get(
    "/agents-md",
    response_model=AgentsMdResponse,
    summary="[DEPRECATED] Get AGENTS.md status",
    deprecated=True,
    description="""
    **⚠️ DEPRECATED**: This endpoint will be removed on March 6, 2026.
    Use `POST /context-authority/v2/overlay` for dynamic AGENTS.md management.

    Get the status and freshness of the AGENTS.md context file.
    """,
)
async def get_agents_md_status(
    response: Response,
    repo_path: Optional[str] = Query(None, description="Repository root path"),
    engine: ContextAuthorityEngineV1 = Depends(get_context_authority_engine),
) -> AgentsMdResponse:
    """Get AGENTS.md status."""
    # Add deprecation headers (Sprint 147)
    add_deprecation_headers(
        response=response,
        removal_date=V1_SUNSET,
        successor_version=f"{V1_SUCCESSOR}/overlay",
        migration_guide=V1_MIGRATION_GUIDE,
        reason="Use V2 overlay for dynamic AGENTS.md management",
    )

    repo_path = repo_path or engine._get_default_repo_path()
    agents_file = Path(repo_path) / engine.agents_md_path

    if not agents_file.exists():
        return AgentsMdResponse(
            exists=False,
            file_path=str(agents_file),
            last_modified=None,
            age_days=0,
            is_stale=True,
            staleness_threshold_days=engine.staleness_days,
            line_count=0,
            message="AGENTS.md not found",
        )

    stat = agents_file.stat()
    last_modified = datetime.fromtimestamp(stat.st_mtime)
    age_days = (datetime.now() - last_modified).days
    is_stale = age_days > engine.staleness_days

    # Count lines
    line_count = len(agents_file.read_text().split("\n"))

    if is_stale:
        message = f"AGENTS.md is stale ({age_days} days old, threshold: {engine.staleness_days})"
    else:
        message = f"AGENTS.md is fresh ({age_days} days old)"

    return AgentsMdResponse(
        exists=True,
        file_path=str(agents_file),
        last_modified=last_modified,
        age_days=age_days,
        is_stale=is_stale,
        staleness_threshold_days=engine.staleness_days,
        line_count=line_count,
        message=message,
    )


@router.get(
    "/health",
    summary="[DEPRECATED] Context authority health check",
    deprecated=True,
    description="""
    **⚠️ DEPRECATED**: This endpoint will be removed on March 6, 2026.
    Use `GET /context-authority/v2/health` instead.

    Check health of context authority service.
    """,
)
async def context_authority_health(
    response: Response,
    engine: ContextAuthorityEngineV1 = Depends(get_context_authority_engine),
) -> Dict[str, Any]:
    """Health check for context authority."""
    # Add deprecation headers (Sprint 147)
    add_deprecation_headers(
        response=response,
        removal_date=V1_SUNSET,
        successor_version=f"{V1_SUCCESSOR}/health",
        migration_guide=V1_MIGRATION_GUIDE,
        reason="Use V2 health check endpoint",
    )

    return {
        "status": "healthy",
        "service": "context_authority_v1",
        "deprecated": True,
        "deprecation_notice": f"This V1 endpoint will be removed on {V1_SUNSET}. Use /context-authority/v2/health",
        "adr_count": len(engine._adr_cache),
        "adr_path": engine.adr_path,
        "spec_path": engine.spec_path,
        "agents_md_path": engine.agents_md_path,
        "staleness_threshold_days": engine.staleness_days,
        "timestamp": datetime.utcnow().isoformat(),
    }
