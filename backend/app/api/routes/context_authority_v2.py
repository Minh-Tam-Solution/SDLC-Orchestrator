"""
=========================================================================
Context Authority V2 API Routes - Gate-Aware Dynamic Context (SPEC-0011)
SDLC Orchestrator - Sprint 120 (Feb 3-14, 2026)

Version: 2.0.0
Date: January 29, 2026
Status: ACTIVE - Sprint 120 Pre-work
Authority: CTO + Backend Lead Approved
Framework: SDLC 6.0 Quality Assurance System

Endpoints:
- POST /context-authority/v2/validate - Gate-aware context validation
- POST /context-authority/v2/overlay - Generate dynamic overlay
- GET  /context-authority/v2/templates - List overlay templates
- POST /context-authority/v2/templates - Create overlay template
- GET  /context-authority/v2/templates/{id} - Get template by ID
- PUT  /context-authority/v2/templates/{id} - Update template
- GET  /context-authority/v2/templates/{id}/usage - Get template usage stats
- GET  /context-authority/v2/snapshot/{submission_id} - Get snapshot
- GET  /context-authority/v2/snapshots/{project_id} - List project snapshots
- GET  /context-authority/v2/health - Health check
- GET  /context-authority/v2/stats - Statistics

Zero Mock Policy: Real validation with database operations
=========================================================================
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.context_authority_v2 import (
    ContextOverlayTemplate,
    ContextSnapshot,
    ContextOverlayApplication,
)
from app.repositories.context_authority_v2 import (
    ContextOverlayTemplateRepository,
    ContextSnapshotRepository,
    ContextOverlayApplicationRepository,
)
from app.schemas.context_authority import (
    ContextValidationRequest,
    ContextValidationResponse,
    OverlayGenerateRequest,
    OverlayGenerateResponse,
    TemplateCreateRequest,
    TemplateUpdateRequest,
    TemplateResponse,
    TemplateListResponse,
    TemplateUsageResponse,
    SnapshotResponse,
    SnapshotListResponse,
    ContextAuthorityHealthResponse,
    ContextAuthorityStatsResponse,
    V1ResultSchema,
    V2ResultSchema,
    TierEnum,
    VibecodingZoneEnum,
)
from app.services.governance.context_authority import (
    CodeSubmission as ServiceCodeSubmission,
    get_context_authority_engine,
)
from app.services.governance.context_authority_v2 import (
    ContextAuthorityEngineV2,
    GateStatus,
    VibecodingZone,
    get_context_authority_engine_v2,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/context-authority/v2", tags=["Context Authority V2"])


# ============================================================================
# Dependency Injection
# ============================================================================


async def get_ca_v2_engine(
    db: AsyncSession = Depends(get_db),
) -> ContextAuthorityEngineV2:
    """Get Context Authority V2 engine instance."""
    return get_context_authority_engine_v2(db)


# ============================================================================
# Context Validation Endpoint
# ============================================================================


@router.post(
    "/validate",
    response_model=ContextValidationResponse,
    summary="Gate-aware context validation",
    description="""
    Validate code submission with gate-aware rules (SPEC-0011 FR-001).

    **V1 + V2 Combined Validation**:
    1. **V1 Checks**: ADR linkage, design doc, AGENTS.md freshness, module consistency
    2. **V2 Gate Checks**: Stage-aware file blocking (e.g., no code in Stage 02)
    3. **V2 Index Checks**: Vibecoding zone warnings/blocks

    **Stage Rules**:
    - Stage 00 (Discover): Only docs/00-* allowed
    - Stage 01 (Planning): Only docs/01-* allowed
    - Stage 02 (Design): Design docs + schema files allowed
    - Stage 04 (Build): All code allowed
    - Stage 05 (Test): Tests and bug fixes only
    - Stage 06 (Deploy): Infrastructure only

    **Vibecoding Zones**:
    - GREEN (0-30): Auto-approve
    - YELLOW (31-60): Tech Lead review
    - ORANGE (61-80): CEO should review
    - RED (81-100): CEO must review (blocks)

    **Outputs**:
    - `is_valid`: Overall validation result
    - `dynamic_overlay`: Generated context for AGENTS.md
    - `snapshot_id`: Audit trail reference
    """,
)
async def validate_context(
    request: ContextValidationRequest,
    engine: ContextAuthorityEngineV2 = Depends(get_ca_v2_engine),
) -> ContextValidationResponse:
    """Gate-aware context validation."""
    # Convert request to service submission
    submission = ServiceCodeSubmission(
        submission_id=request.submission_id,
        project_id=request.project_id,
        changed_files=request.changed_paths or [],
        affected_modules=[],
        task_id=None,
        is_new_feature=False,
        repo_path=None,
    )

    # Create gate status from request
    gate_status = GateStatus(
        project_id=request.project_id,
        current_stage=request.gate_status.current_stage.replace("-", "")[:2],
        last_passed_gate=request.gate_status.last_passed_gate,
        pending_gates=request.gate_status.pending_gates,
    )

    try:
        result = await engine.validate_context_v2(
            submission=submission,
            gate_status=gate_status,
            vibecoding_index=request.vibecoding_index,
            tier=request.project_tier.value,
        )
    except Exception as e:
        logger.error(f"Context V2 validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Context validation failed: {str(e)}",
        )

    # Convert V1 result
    v1_result = V1ResultSchema(
        adr_linkage=not any(
            v.type == "orphan_code" for v in result.v1_result.violations
        ),
        design_doc_exists=result.v1_result.spec_found,
        agents_md_fresh=result.v1_result.agents_md_fresh,
        module_annotation_consistent=result.v1_result.module_consistency,
        orphan_code=any(
            v.type == "orphan_code" for v in result.v1_result.violations
        ),
    )

    # Convert V2 result
    v2_result = V2ResultSchema(
        gate_violations=[v.to_dict() for v in result.gate_violations],
        index_warnings=[w.to_dict() for w in result.index_warnings],
        applied_templates=[
            {
                "template_id": str(t),
                "trigger_type": "dynamic",
            }
            for t in result.applied_templates
        ],
        stage_allowed=len(result.gate_violations) == 0,
    )

    logger.info(
        f"Context V2 validation: {'PASS' if result.valid else 'FAIL'} - "
        f"stage={gate_status.current_stage}, index={request.vibecoding_index}"
    )

    return ContextValidationResponse(
        submission_id=request.submission_id,
        is_valid=result.valid,
        v1_result=v1_result,
        v2_result=v2_result,
        dynamic_overlay=result.dynamic_overlay,
        snapshot_id=result.snapshot_id,
        validated_at=result.validated_at,
    )


# ============================================================================
# Overlay Generation Endpoint
# ============================================================================


@router.post(
    "/overlay",
    response_model=OverlayGenerateResponse,
    summary="Generate dynamic overlay",
    description="""
    Generate dynamic overlay without full validation (SPEC-0011 FR-002).

    **Use Cases**:
    - Preview overlay before submission
    - Generate AGENTS.md context section
    - Real-time overlay updates in IDE

    **Template Selection**:
    1. Gate-based: Triggered by last_passed_gate
    2. Zone-based: Triggered by vibecoding_zone
    3. Stage-based: Triggered by stage constraints

    **Template Variables**:
    - `{date}`: Current date (YYYY-MM-DD)
    - `{index}`: Vibecoding index value
    - `{stage}`: Current SDLC stage
    - `{tier}`: Project tier
    - `{gate}`: Last passed gate
    - `{top_signals}`: Top contributing signals
    """,
)
async def generate_overlay(
    request: OverlayGenerateRequest,
    engine: ContextAuthorityEngineV2 = Depends(get_ca_v2_engine),
) -> OverlayGenerateResponse:
    """Generate dynamic overlay."""
    # Create gate status from request
    gate_status = GateStatus(
        project_id=request.project_id,
        current_stage=request.gate_status.current_stage.replace("-", "")[:2],
        last_passed_gate=request.gate_status.last_passed_gate,
        pending_gates=request.gate_status.pending_gates,
    )

    # Determine vibecoding zone
    vibecoding_index = request.vibecoding_index or 0
    vibecoding_zone = engine._get_zone_from_index(vibecoding_index)

    try:
        result = await engine.get_dynamic_overlay(
            project_id=request.project_id,
            gate_status=gate_status,
            vibecoding_index=vibecoding_index,
            tier=request.project_tier.value,
        )
    except Exception as e:
        logger.error(f"Overlay generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Overlay generation failed: {str(e)}",
        )

    return OverlayGenerateResponse(
        overlay_content=result.content,
        applied_templates=[
            {
                "template_id": str(t),
                "trigger_type": "dynamic",
            }
            for t in result.templates_applied
        ],
        variables={
            "date": datetime.utcnow().strftime("%Y-%m-%d"),
            "index": str(vibecoding_index),
            "stage": gate_status.current_stage,
            "tier": request.project_tier.value,
            "gate": gate_status.last_passed_gate or "None",
        },
        generated_at=result.generated_at,
    )


# ============================================================================
# Template Management Endpoints
# ============================================================================


@router.get(
    "/templates",
    response_model=TemplateListResponse,
    summary="List overlay templates",
    description="List all overlay templates with optional filtering.",
)
async def list_templates(
    trigger_type: Optional[str] = Query(
        None,
        description="Filter by trigger type (gate_pass, gate_fail, index_zone, stage_constraint)",
    ),
    tier: Optional[str] = Query(
        None,
        description="Filter by tier (LITE, STANDARD, PROFESSIONAL, ENTERPRISE)",
    ),
    active_only: bool = Query(True, description="Only return active templates"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
) -> TemplateListResponse:
    """List overlay templates."""
    repo = ContextOverlayTemplateRepository(db)

    # Build query
    offset = (page - 1) * page_size

    try:
        templates = await repo.list_all(
            trigger_type=trigger_type,
            tier=tier,
            active_only=active_only,
            limit=page_size,
            offset=offset,
        )
        total = await repo.count(
            trigger_type=trigger_type,
            tier=tier,
            active_only=active_only,
        )
    except Exception as e:
        logger.error(f"Failed to list templates: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list templates: {str(e)}",
        )

    pages = (total + page_size - 1) // page_size if total > 0 else 1

    return TemplateListResponse(
        templates=[
            TemplateResponse(
                id=t.id,
                name=t.name,
                trigger_type=t.trigger_type,
                trigger_value=t.trigger_value,
                tier=t.tier,
                overlay_content=t.overlay_content,
                priority=t.priority,
                is_active=t.is_active,
                description=t.description,
                created_by_id=t.created_by_id,
                created_at=t.created_at,
                updated_at=t.updated_at,
            )
            for t in templates
        ],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.post(
    "/templates",
    response_model=TemplateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create overlay template",
    description="Create a new overlay template (Admin only).",
)
async def create_template(
    request: TemplateCreateRequest,
    db: AsyncSession = Depends(get_db),
) -> TemplateResponse:
    """Create overlay template."""
    repo = ContextOverlayTemplateRepository(db)

    try:
        template = await repo.create(
            trigger_type=request.trigger_type.value,
            trigger_value=request.trigger_value,
            overlay_content=request.overlay_content,
            name=request.name,
            tier=request.tier.value if request.tier else None,
            priority=request.priority,
            is_active=request.is_active,
            description=request.description,
            created_by_id=None,  # TODO: Get from auth context
        )
    except Exception as e:
        logger.error(f"Failed to create template: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create template: {str(e)}",
        )

    logger.info(f"Created template: {template.id} - {template.name}")

    return TemplateResponse(
        id=template.id,
        name=template.name,
        trigger_type=template.trigger_type,
        trigger_value=template.trigger_value,
        tier=template.tier,
        overlay_content=template.overlay_content,
        priority=template.priority,
        is_active=template.is_active,
        description=template.description,
        created_by_id=template.created_by_id,
        created_at=template.created_at,
        updated_at=template.updated_at,
    )


@router.get(
    "/templates/{template_id}",
    response_model=TemplateResponse,
    summary="Get template by ID",
    description="Get a specific overlay template by ID.",
)
async def get_template(
    template_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> TemplateResponse:
    """Get template by ID."""
    repo = ContextOverlayTemplateRepository(db)

    template = await repo.get_by_id(template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template not found: {template_id}",
        )

    return TemplateResponse(
        id=template.id,
        name=template.name,
        trigger_type=template.trigger_type,
        trigger_value=template.trigger_value,
        tier=template.tier,
        overlay_content=template.overlay_content,
        priority=template.priority,
        is_active=template.is_active,
        description=template.description,
        created_by_id=template.created_by_id,
        created_at=template.created_at,
        updated_at=template.updated_at,
    )


@router.put(
    "/templates/{template_id}",
    response_model=TemplateResponse,
    summary="Update template",
    description="Update an existing overlay template (Admin only).",
)
async def update_template(
    template_id: UUID,
    request: TemplateUpdateRequest,
    db: AsyncSession = Depends(get_db),
) -> TemplateResponse:
    """Update template."""
    repo = ContextOverlayTemplateRepository(db)

    template = await repo.get_by_id(template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template not found: {template_id}",
        )

    # Build update data
    update_data: Dict[str, Any] = {}
    if request.name is not None:
        update_data["name"] = request.name
    if request.trigger_type is not None:
        update_data["trigger_type"] = request.trigger_type.value
    if request.trigger_value is not None:
        update_data["trigger_value"] = request.trigger_value
    if request.tier is not None:
        update_data["tier"] = request.tier.value
    if request.overlay_content is not None:
        update_data["overlay_content"] = request.overlay_content
    if request.priority is not None:
        update_data["priority"] = request.priority
    if request.is_active is not None:
        update_data["is_active"] = request.is_active
    if request.description is not None:
        update_data["description"] = request.description

    try:
        template = await repo.update(template_id, **update_data)
    except Exception as e:
        logger.error(f"Failed to update template: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update template: {str(e)}",
        )

    logger.info(f"Updated template: {template_id}")

    return TemplateResponse(
        id=template.id,
        name=template.name,
        trigger_type=template.trigger_type,
        trigger_value=template.trigger_value,
        tier=template.tier,
        overlay_content=template.overlay_content,
        priority=template.priority,
        is_active=template.is_active,
        description=template.description,
        created_by_id=template.created_by_id,
        created_at=template.created_at,
        updated_at=template.updated_at,
    )


@router.get(
    "/templates/{template_id}/usage",
    response_model=TemplateUsageResponse,
    summary="Get template usage statistics",
    description="Get usage statistics for a specific template.",
)
async def get_template_usage(
    template_id: UUID,
    days: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    db: AsyncSession = Depends(get_db),
) -> TemplateUsageResponse:
    """Get template usage statistics."""
    template_repo = ContextOverlayTemplateRepository(db)
    application_repo = ContextOverlayApplicationRepository(db)

    template = await template_repo.get_by_id(template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template not found: {template_id}",
        )

    try:
        count = await application_repo.get_template_usage_count(template_id, days)
        applications = await application_repo.get_recent_applications(
            template_id, limit=10
        )
    except Exception as e:
        logger.error(f"Failed to get template usage: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get template usage: {str(e)}",
        )

    first_applied = applications[-1].applied_at if applications else None
    last_applied = applications[0].applied_at if applications else None

    return TemplateUsageResponse(
        template_id=template_id,
        template_name=template.name,
        application_count=count,
        recent_applications=[
            {
                "snapshot_id": app.snapshot_id,
                "rendered_content": app.rendered_content[:200] + "..."
                if len(app.rendered_content) > 200
                else app.rendered_content,
                "variables_used": app.variables_used,
                "applied_at": app.applied_at,
            }
            for app in applications
        ],
        first_applied_at=first_applied,
        last_applied_at=last_applied,
    )


# ============================================================================
# Snapshot Endpoints
# ============================================================================


@router.get(
    "/snapshot/{submission_id}",
    response_model=SnapshotResponse,
    summary="Get context snapshot",
    description="Get context snapshot for a governance submission.",
)
async def get_snapshot(
    submission_id: UUID,
    engine: ContextAuthorityEngineV2 = Depends(get_ca_v2_engine),
) -> SnapshotResponse:
    """Get context snapshot by submission ID."""
    snapshot = await engine.get_snapshot_by_submission(submission_id)
    if not snapshot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Snapshot not found for submission: {submission_id}",
        )

    return SnapshotResponse(
        id=snapshot.id,
        submission_id=snapshot.submission_id,
        project_id=snapshot.project_id,
        gate_status=snapshot.gate_status,
        vibecoding_index=snapshot.vibecoding_index,
        vibecoding_zone=snapshot.vibecoding_zone,
        dynamic_overlay=snapshot.dynamic_overlay,
        v1_result=snapshot.v1_result,
        gate_violations=snapshot.gate_violations,
        index_warnings=snapshot.index_warnings,
        tier=snapshot.tier,
        is_valid=snapshot.is_valid,
        applied_template_ids=snapshot.applied_template_ids,
        snapshot_at=snapshot.snapshot_at,
        created_at=snapshot.created_at,
    )


@router.get(
    "/snapshots/{project_id}",
    response_model=SnapshotListResponse,
    summary="List project snapshots",
    description="List context snapshots for a project.",
)
async def list_project_snapshots(
    project_id: UUID,
    valid_only: bool = Query(False, description="Only return valid snapshots"),
    zone: Optional[str] = Query(
        None, description="Filter by vibecoding zone (GREEN, YELLOW, ORANGE, RED)"
    ),
    limit: int = Query(50, ge=1, le=200, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    engine: ContextAuthorityEngineV2 = Depends(get_ca_v2_engine),
) -> SnapshotListResponse:
    """List snapshots for a project."""
    try:
        snapshots = await engine.snapshot_repo.list_by_project(
            project_id=project_id,
            limit=limit,
            offset=offset,
            valid_only=valid_only,
            zone=zone,
        )
        total = await engine.snapshot_repo.count_by_project(
            project_id=project_id,
            valid_only=valid_only,
            zone=zone,
        )
    except Exception as e:
        logger.error(f"Failed to list snapshots: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list snapshots: {str(e)}",
        )

    return SnapshotListResponse(
        submission_id=project_id,  # Using project_id as the key
        snapshots=[
            SnapshotResponse(
                id=s.id,
                submission_id=s.submission_id,
                project_id=s.project_id,
                gate_status=s.gate_status,
                vibecoding_index=s.vibecoding_index,
                vibecoding_zone=s.vibecoding_zone,
                dynamic_overlay=s.dynamic_overlay,
                v1_result=s.v1_result,
                gate_violations=s.gate_violations,
                index_warnings=s.index_warnings,
                tier=s.tier,
                is_valid=s.is_valid,
                applied_template_ids=s.applied_template_ids,
                snapshot_at=s.snapshot_at,
                created_at=s.created_at,
            )
            for s in snapshots
        ],
        total=total,
    )


# ============================================================================
# Health & Stats Endpoints
# ============================================================================


@router.get(
    "/health",
    response_model=ContextAuthorityHealthResponse,
    summary="Health check",
    description="Check health of Context Authority V2 service.",
)
async def health_check(
    db: AsyncSession = Depends(get_db),
) -> ContextAuthorityHealthResponse:
    """Health check for Context Authority V2."""
    template_repo = ContextOverlayTemplateRepository(db)
    snapshot_repo = ContextSnapshotRepository(db)

    try:
        # Count active templates
        template_count = await template_repo.count(active_only=True)

        # Count snapshots in last 24 hours
        snapshot_count_24h = await snapshot_repo.count_recent(hours=24)

        # Calculate average latencies (placeholder - would need metrics service)
        avg_validation_ms = 45.0  # Target: <100ms
        avg_overlay_ms = 12.0  # Target: <50ms

        return ContextAuthorityHealthResponse(
            status="healthy",
            version="2.0.0",
            template_count=template_count,
            snapshot_count_24h=snapshot_count_24h,
            avg_validation_ms=avg_validation_ms,
            avg_overlay_ms=avg_overlay_ms,
            last_check=datetime.utcnow(),
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return ContextAuthorityHealthResponse(
            status="unhealthy",
            version="2.0.0",
            template_count=0,
            snapshot_count_24h=0,
            avg_validation_ms=0.0,
            avg_overlay_ms=0.0,
            last_check=datetime.utcnow(),
        )


@router.get(
    "/stats",
    response_model=ContextAuthorityStatsResponse,
    summary="Get statistics",
    description="Get Context Authority V2 statistics for a time period.",
)
async def get_stats(
    days: int = Query(30, ge=1, le=365, description="Number of days"),
    db: AsyncSession = Depends(get_db),
) -> ContextAuthorityStatsResponse:
    """Get Context Authority V2 statistics."""
    snapshot_repo = ContextSnapshotRepository(db)
    application_repo = ContextOverlayApplicationRepository(db)

    period_start = datetime.utcnow() - timedelta(days=days)
    period_end = datetime.utcnow()

    try:
        # Get aggregate stats
        stats = await snapshot_repo.get_aggregate_stats(days=days)

        # Get top triggered templates
        top_templates = await application_repo.get_top_templates(
            days=days, limit=10
        )

        return ContextAuthorityStatsResponse(
            total_validations=stats.get("total_validations", 0),
            total_snapshots=stats.get("total_snapshots", 0),
            validation_pass_rate=stats.get("pass_rate", 0.0),
            zone_distribution=stats.get("zone_distribution", {}),
            tier_distribution=stats.get("tier_distribution", {}),
            top_triggered_templates=top_templates,
            avg_templates_per_validation=stats.get("avg_templates", 0.0),
            period_start=period_start,
            period_end=period_end,
        )
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get statistics: {str(e)}",
        )
