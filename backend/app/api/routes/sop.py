"""
=========================================================================
SOP Generator API Routes - Phase 2-Pilot (SE 3.0 Track 1)
SDLC Orchestrator - SASE Level 1 Integration

Version: 1.0.0
Date: December 23, 2025
Status: ACTIVE - Phase 2-Pilot Week 1
Authority: CTO Approved (BRS-PILOT-001)
Foundation: SE 3.0 SASE Integration, Phase 1-Spec (v5.1.0-agentic-spec-alpha)
Framework: SDLC 5.1.0 Complete Lifecycle

Endpoints:
- POST /api/sop/generate - Generate SOP from workflow description (FR1)
- GET /api/sop/types - List supported SOP types (FR3)
- GET /api/sop/{sop_id} - Get SOP details
- GET /api/sop/{sop_id}/mrp - Get MRP evidence (FR6)
- POST /api/sop/{sop_id}/vcr - Submit VCR decision (FR7)

BRS Reference: BRS-PILOT-001-NQH-Bot-SOP-Generator.yaml
=========================================================================
"""

import logging
from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.services.sop_generator_service import (
    GeneratedSOP,
    MRPEvidence,
    SOPGenerationRequest,
    SOPStatus,
    SOPType,
    get_sop_generator_service,
    SOPGeneratorService,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sop", tags=["SOP Generator"])


# ============================================================================
# Request/Response Models
# ============================================================================


class SOPTypeResponse(BaseModel):
    """SOP type information."""

    type: str
    name: str
    description: str
    typical_sections: list[str]


class GenerateSOPRequest(BaseModel):
    """Request to generate an SOP (FR1)."""

    sop_type: str = Field(..., description="Type of SOP: deployment, incident, change, backup, security")
    workflow_description: str = Field(
        ...,
        min_length=50,
        max_length=5000,
        description="Description of the workflow to create SOP for",
    )
    additional_context: Optional[str] = Field(
        None,
        max_length=2000,
        description="Additional context or requirements",
    )
    project_id: Optional[str] = Field(None, description="Associated project ID")

    class Config:
        json_schema_extra = {
            "example": {
                "sop_type": "deployment",
                "workflow_description": "Deploy the SDLC Orchestrator application to production environment. The application is containerized with Docker and deployed to Kubernetes cluster. Deployment should include database migrations, configuration updates, and health checks.",
                "additional_context": "Ensure zero-downtime deployment. Rollback if health checks fail.",
                "project_id": "PRJ-001",
            }
        }


class GeneratedSOPResponse(BaseModel):
    """Response containing generated SOP and MRP evidence."""

    # SOP details
    sop_id: str
    sop_type: str
    title: str
    version: str
    status: str
    created_at: str

    # Content sections (FR2)
    purpose: str
    scope: str
    procedure: str
    roles: str
    quality_criteria: str

    # Full markdown
    markdown_content: str

    # Evidence (FR5)
    sha256_hash: str

    # Generation metrics
    generation_time_ms: float
    ai_model: str

    # MRP reference (FR6)
    mrp_id: str
    completeness_score: float


class MRPResponse(BaseModel):
    """MRP evidence response (FR6)."""

    mrp_id: str
    brs_id: str
    sop_id: str
    created_at: str

    # SOP evidence
    sop_type: str
    template_used: str

    # Generation metrics
    generation_time_ms: float
    ai_model: str
    ai_provider: str

    # Quality metrics
    sections_present: int
    sections_required: int
    completeness_score: float

    # Integrity
    sha256_hash: str

    # Status
    status: str


class VCRDecision(str, Enum):
    """VCR decision options (FR7)."""

    APPROVED = "approved"
    REJECTED = "rejected"
    REVISION_REQUIRED = "revision_required"


class VCRRequest(BaseModel):
    """VCR decision request (FR7)."""

    decision: VCRDecision
    reviewer: str = Field(..., description="Name of the reviewer")
    comments: Optional[str] = Field(None, description="Review comments")
    quality_rating: Optional[int] = Field(
        None,
        ge=1,
        le=5,
        description="Quality rating 1-5 (NFR2: target ≥4)",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "decision": "approved",
                "reviewer": "Tech Lead",
                "comments": "SOP is complete and follows ISO 9001 format",
                "quality_rating": 4,
            }
        }


class VCRResponse(BaseModel):
    """VCR decision response (FR7)."""

    vcr_id: str
    sop_id: str
    mrp_id: str
    decision: str
    reviewer: str
    reviewed_at: str
    comments: Optional[str]
    quality_rating: Optional[int]
    status: str


# ============================================================================
# In-Memory Storage (for pilot - replace with database in production)
# ============================================================================

# Store generated SOPs and MRPs (pilot only - use database in production)
_sop_store: dict[str, GeneratedSOP] = {}
_mrp_store: dict[str, MRPEvidence] = {}
_vcr_store: dict[str, dict[str, Any]] = {}


# ============================================================================
# API Endpoints
# ============================================================================


# NOTE: Health endpoint MUST be defined before /{sop_id} to avoid route conflict
@router.get(
    "/health",
    summary="SOP Generator health check",
    description="Check if SOP Generator service is healthy",
)
async def health_check(
    service: SOPGeneratorService = Depends(get_sop_generator_service),
) -> dict[str, Any]:
    """
    Health check for SOP Generator.

    Returns:
        Health status including Ollama connectivity
    """
    try:
        import requests

        # Check Ollama connectivity
        response = requests.get(
            f"{service.ollama_base_url}/api/tags",
            timeout=5,
        )
        ollama_status = "healthy" if response.status_code == 200 else "unhealthy"
        ollama_models = response.json().get("models", []) if response.ok else []
    except Exception as e:
        ollama_status = f"error: {str(e)}"
        ollama_models = []

    return {
        "status": "healthy",
        "service": "sop_generator",
        "version": "1.0.0",
        "ollama": {
            "status": ollama_status,
            "url": service.ollama_base_url,
            "model": service.ollama_model,
            "available_models": [m.get("name") for m in ollama_models],
        },
        "sase_level": "Level 1 (BRS + MRP + VCR)",
        "brs_reference": "BRS-PILOT-001",
    }


@router.get(
    "/types",
    response_model=list[SOPTypeResponse],
    summary="List supported SOP types",
    description="Get list of all supported SOP types (FR3: 5 types)",
)
async def get_sop_types(
    service: SOPGeneratorService = Depends(get_sop_generator_service),
) -> list[SOPTypeResponse]:
    """
    List all supported SOP types (FR3).

    Returns:
        List of 5 SOP types: deployment, incident, change, backup, security
    """
    types = service.get_supported_types()
    return [SOPTypeResponse(**t) for t in types]


@router.post(
    "/generate",
    response_model=GeneratedSOPResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate SOP from workflow description",
    description="""
    Generate a Standard Operating Procedure (SOP) using AI (FR1).

    This endpoint:
    1. Takes a workflow description and SOP type
    2. Generates complete SOP with 5 mandatory sections (FR2)
    3. Creates MRP evidence automatically (FR6)
    4. Returns SOP ready for VCR approval (FR7)

    Performance: Target <30 seconds generation time (NFR1)
    """,
)
async def generate_sop(
    request: GenerateSOPRequest,
    service: SOPGeneratorService = Depends(get_sop_generator_service),
) -> GeneratedSOPResponse:
    """
    Generate SOP from workflow description (FR1).

    Args:
        request: SOP generation request with workflow description

    Returns:
        Generated SOP with MRP evidence

    Raises:
        HTTPException: If generation fails or invalid SOP type
    """
    # Validate SOP type
    try:
        sop_type = SOPType(request.sop_type.lower())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid SOP type: {request.sop_type}. "
            f"Valid types: deployment, incident, change, backup, security",
        )

    # Create generation request
    gen_request = SOPGenerationRequest(
        sop_type=sop_type,
        workflow_description=request.workflow_description,
        additional_context=request.additional_context,
        project_id=request.project_id,
    )

    try:
        # Generate SOP (FR1) and MRP (FR6)
        sop, mrp = await service.generate_sop(gen_request)

        # Store for retrieval (pilot uses in-memory, production uses DB)
        _sop_store[sop.sop_id] = sop
        _mrp_store[mrp.mrp_id] = mrp

        logger.info(
            f"SOP generated: id={sop.sop_id}, type={sop_type.value}, "
            f"time={sop.generation_time_ms:.0f}ms, "
            f"completeness={mrp.completeness_score:.1f}%"
        )

        return GeneratedSOPResponse(
            sop_id=sop.sop_id,
            sop_type=sop.sop_type.value,
            title=sop.title,
            version=sop.version,
            status=sop.status.value,
            created_at=sop.created_at.isoformat(),
            purpose=sop.purpose,
            scope=sop.scope,
            procedure=sop.procedure,
            roles=sop.roles,
            quality_criteria=sop.quality_criteria,
            markdown_content=sop.markdown_content,
            sha256_hash=sop.sha256_hash,
            generation_time_ms=sop.generation_time_ms,
            ai_model=sop.ai_model,
            mrp_id=mrp.mrp_id,
            completeness_score=mrp.completeness_score,
        )

    except Exception as e:
        logger.error(f"SOP generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"SOP generation failed: {str(e)}",
        )


class SOPListItem(BaseModel):
    """SOP list item for history view."""

    sop_id: str
    sop_type: str
    title: str
    status: str
    created_at: str
    completeness_score: float
    has_vcr: bool


class SOPListResponse(BaseModel):
    """Response for SOP list endpoint."""

    items: list[SOPListItem]
    total: int
    page: int
    page_size: int


@router.get(
    "/list",
    response_model=SOPListResponse,
    summary="List generated SOPs",
    description="Get paginated list of generated SOPs for history view (M4)",
)
async def list_sops(
    page: int = 1,
    page_size: int = 20,
    sop_type: Optional[str] = None,
    status: Optional[str] = None,
) -> SOPListResponse:
    """
    List generated SOPs with pagination and filtering (M4 History).

    Args:
        page: Page number (1-indexed)
        page_size: Items per page (max 100)
        sop_type: Filter by SOP type
        status: Filter by status

    Returns:
        Paginated list of SOPs
    """
    # Apply filters
    filtered_sops = list(_sop_store.values())

    if sop_type:
        filtered_sops = [s for s in filtered_sops if s.sop_type.value == sop_type.lower()]

    if status:
        filtered_sops = [s for s in filtered_sops if s.status.value == status.lower()]

    # Sort by created_at descending
    filtered_sops.sort(key=lambda s: s.created_at, reverse=True)

    # Pagination
    total = len(filtered_sops)
    page_size = min(page_size, 100)
    start = (page - 1) * page_size
    end = start + page_size
    page_items = filtered_sops[start:end]

    # Build response items
    items = []
    for sop in page_items:
        mrp = next(
            (m for m in _mrp_store.values() if m.sop_id == sop.sop_id),
            None,
        )
        vcr = next(
            (v for v in _vcr_store.values() if v["sop_id"] == sop.sop_id),
            None,
        )

        items.append(
            SOPListItem(
                sop_id=sop.sop_id,
                sop_type=sop.sop_type.value,
                title=sop.title,
                status=sop.status.value,
                created_at=sop.created_at.isoformat(),
                completeness_score=mrp.completeness_score if mrp else 0.0,
                has_vcr=vcr is not None,
            )
        )

    return SOPListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{sop_id}",
    response_model=GeneratedSOPResponse,
    summary="Get SOP details",
    description="Retrieve a generated SOP by ID",
)
async def get_sop(sop_id: str) -> GeneratedSOPResponse:
    """
    Get SOP details by ID.

    Args:
        sop_id: SOP identifier

    Returns:
        SOP details

    Raises:
        HTTPException: If SOP not found
    """
    if sop_id not in _sop_store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"SOP not found: {sop_id}",
        )

    sop = _sop_store[sop_id]

    # Find associated MRP
    mrp = next(
        (m for m in _mrp_store.values() if m.sop_id == sop_id),
        None,
    )

    return GeneratedSOPResponse(
        sop_id=sop.sop_id,
        sop_type=sop.sop_type.value,
        title=sop.title,
        version=sop.version,
        status=sop.status.value,
        created_at=sop.created_at.isoformat(),
        purpose=sop.purpose,
        scope=sop.scope,
        procedure=sop.procedure,
        roles=sop.roles,
        quality_criteria=sop.quality_criteria,
        markdown_content=sop.markdown_content,
        sha256_hash=sop.sha256_hash,
        generation_time_ms=sop.generation_time_ms,
        ai_model=sop.ai_model,
        mrp_id=mrp.mrp_id if mrp else "",
        completeness_score=mrp.completeness_score if mrp else 0.0,
    )


@router.get(
    "/{sop_id}/mrp",
    response_model=MRPResponse,
    summary="Get MRP evidence for SOP",
    description="Retrieve Merge-Readiness Pack evidence for a generated SOP (FR6)",
)
async def get_sop_mrp(sop_id: str) -> MRPResponse:
    """
    Get MRP evidence for SOP (FR6).

    Args:
        sop_id: SOP identifier

    Returns:
        MRP evidence

    Raises:
        HTTPException: If SOP or MRP not found
    """
    if sop_id not in _sop_store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"SOP not found: {sop_id}",
        )

    mrp = next(
        (m for m in _mrp_store.values() if m.sop_id == sop_id),
        None,
    )

    if not mrp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"MRP not found for SOP: {sop_id}",
        )

    return MRPResponse(
        mrp_id=mrp.mrp_id,
        brs_id=mrp.brs_id,
        sop_id=mrp.sop_id,
        created_at=mrp.created_at.isoformat(),
        sop_type=mrp.sop_type,
        template_used=mrp.template_used,
        generation_time_ms=mrp.generation_time_ms,
        ai_model=mrp.ai_model,
        ai_provider=mrp.ai_provider,
        sections_present=mrp.sections_present,
        sections_required=mrp.sections_required,
        completeness_score=mrp.completeness_score,
        sha256_hash=mrp.sha256_hash,
        status=mrp.status,
    )


@router.post(
    "/{sop_id}/vcr",
    response_model=VCRResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit VCR decision for SOP",
    description="""
    Submit Version Controlled Resolution (VCR) decision for SOP approval (FR7).

    Decision options:
    - approved: SOP is approved for use
    - rejected: SOP is rejected (needs new generation)
    - revision_required: SOP needs modifications

    Quality rating (1-5) is optional but recommended (NFR2: target ≥4)
    """,
)
async def submit_vcr(
    sop_id: str,
    request: VCRRequest,
) -> VCRResponse:
    """
    Submit VCR decision for SOP (FR7).

    Args:
        sop_id: SOP identifier
        request: VCR decision

    Returns:
        VCR decision record

    Raises:
        HTTPException: If SOP not found
    """
    if sop_id not in _sop_store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"SOP not found: {sop_id}",
        )

    sop = _sop_store[sop_id]

    # Find associated MRP
    mrp = next(
        (m for m in _mrp_store.values() if m.sop_id == sop_id),
        None,
    )

    # Generate VCR ID
    vcr_id = f"VCR-PILOT-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

    # Update SOP status based on decision
    if request.decision == VCRDecision.APPROVED:
        sop.status = SOPStatus.APPROVED
    elif request.decision == VCRDecision.REJECTED:
        sop.status = SOPStatus.REJECTED
    elif request.decision == VCRDecision.REVISION_REQUIRED:
        sop.status = SOPStatus.REVISION_REQUIRED

    # Update MRP status
    if mrp:
        mrp.status = request.decision.value

    # Store VCR
    vcr = {
        "vcr_id": vcr_id,
        "sop_id": sop_id,
        "mrp_id": mrp.mrp_id if mrp else "",
        "decision": request.decision.value,
        "reviewer": request.reviewer,
        "reviewed_at": datetime.utcnow().isoformat(),
        "comments": request.comments,
        "quality_rating": request.quality_rating,
        "status": "completed",
    }
    _vcr_store[vcr_id] = vcr

    logger.info(
        f"VCR submitted: vcr_id={vcr_id}, sop_id={sop_id}, "
        f"decision={request.decision.value}, reviewer={request.reviewer}"
    )

    return VCRResponse(**vcr)


@router.get(
    "/{sop_id}/vcr",
    response_model=VCRResponse,
    summary="Get VCR decision for SOP",
    description="Retrieve Version Controlled Resolution decision for SOP (FR7)",
)
async def get_sop_vcr(sop_id: str) -> VCRResponse:
    """
    Get VCR decision for SOP (FR7).

    Args:
        sop_id: SOP identifier

    Returns:
        VCR decision record

    Raises:
        HTTPException: If SOP or VCR not found
    """
    if sop_id not in _sop_store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"SOP not found: {sop_id}",
        )

    vcr = next(
        (v for v in _vcr_store.values() if v["sop_id"] == sop_id),
        None,
    )

    if not vcr:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"VCR not found for SOP: {sop_id}",
        )

    return VCRResponse(**vcr)


# Health endpoint moved to top of file to avoid route conflict with /{sop_id}
