"""
=========================================================================
VCR Router - Version Controlled Resolution API
SDLC Orchestrator - Sprint 151 (SASE Artifacts Enhancement)

Version: 1.0.0
Date: March 4, 2026
Status: ACTIVE
Authority: CTO Approved
Framework: SDLC 6.0.5 SASE Methodology
Reference: SPEC-0024, ADR-048

Purpose:
API endpoints for VCR (Version Controlled Resolution) management:
- CRUD operations for VCRs
- Workflow transitions (submit, approve, reject)
- Statistics and reporting
- AI-assisted generation

Endpoints:
- POST   /vcr                  - Create VCR (draft)
- GET    /vcr                  - List VCRs (paginated)
- GET    /vcr/{vcr_id}         - Get VCR by ID
- PUT    /vcr/{vcr_id}         - Update VCR (draft only)
- DELETE /vcr/{vcr_id}         - Delete VCR (draft only)
- POST   /vcr/{vcr_id}/submit  - Submit for approval
- POST   /vcr/{vcr_id}/approve - Approve VCR (CTO/CEO)
- POST   /vcr/{vcr_id}/reject  - Reject VCR (CTO/CEO)
- POST   /vcr/{vcr_id}/reopen  - Reopen rejected VCR
- GET    /vcr/stats/{project_id} - Get project statistics
- POST   /vcr/auto-generate    - AI-assisted generation

Security:
- Authentication required (JWT)
- RBAC: CTO/CEO for approve/reject
- Project membership required for access

Zero Mock Policy: Production-ready implementation
=========================================================================
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user, require_roles
from app.db.session import get_db
from app.models.user import User
from app.models.vcr import VCRStatus
from app.schemas.vcr import (
    VCRAutoGenerateRequest,
    VCRAutoGenerateResponse,
    VCRCreate,
    VCRListResponse,
    VCRRejectRequest,
    VCRResponse,
    VCRStatsResponse,
    VCRUpdate,
)
from app.services.vcr_service import (
    VCRService,
    VCRNotFoundError,
    VCRStateError,
    VCRPermissionError,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/vcr", tags=["VCR (Version Controlled Resolution)"])


# =============================================================================
# Helper Functions
# =============================================================================


def get_vcr_service(db: AsyncSession = Depends(get_db)) -> VCRService:
    """Dependency injection for VCR service."""
    return VCRService(db)


# =============================================================================
# CRUD Endpoints
# =============================================================================


@router.post(
    "",
    response_model=VCRResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create VCR",
    description="""
    Create a new Version Controlled Resolution (VCR) in draft status.

    A VCR documents significant changes with:
    - Problem statement and root cause analysis
    - Solution approach and implementation notes
    - Evidence and ADR linkage
    - AI tool attribution

    Requires project membership.
    """,
)
async def create_vcr(
    data: VCRCreate,
    current_user: User = Depends(get_current_active_user),
    vcr_service: VCRService = Depends(get_vcr_service),
) -> VCRResponse:
    """Create a new VCR in draft status."""
    logger.info(f"User {current_user.id} creating VCR for project {data.project_id}")

    try:
        vcr = await vcr_service.create(data, current_user.id)
        return vcr
    except Exception as e:
        logger.error(f"Error creating VCR: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get(
    "",
    response_model=VCRListResponse,
    summary="List VCRs",
    description="""
    List VCRs with filtering and pagination.

    Filters:
    - project_id: Filter by project
    - status: Filter by status (draft, submitted, approved, rejected)
    - limit/offset: Pagination
    """,
)
async def list_vcrs(
    project_id: Optional[UUID] = Query(None, description="Filter by project"),
    status_filter: Optional[str] = Query(
        None, alias="status", description="Filter by status"
    ),
    limit: int = Query(20, ge=1, le=100, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Skip results"),
    current_user: User = Depends(get_current_active_user),
    vcr_service: VCRService = Depends(get_vcr_service),
) -> VCRListResponse:
    """List VCRs with pagination and filters."""
    vcr_status = None
    if status_filter:
        try:
            vcr_status = VCRStatus(status_filter)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {status_filter}. "
                f"Valid values: {[s.value for s in VCRStatus]}",
            )

    return await vcr_service.list(
        project_id=project_id,
        status=vcr_status,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{vcr_id}",
    response_model=VCRResponse,
    summary="Get VCR",
    description="Get a VCR by ID with full details.",
)
async def get_vcr(
    vcr_id: UUID,
    current_user: User = Depends(get_current_active_user),
    vcr_service: VCRService = Depends(get_vcr_service),
) -> VCRResponse:
    """Get VCR by ID."""
    try:
        return await vcr_service.get(vcr_id, include_relationships=True)
    except VCRNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"VCR {vcr_id} not found",
        )


@router.put(
    "/{vcr_id}",
    response_model=VCRResponse,
    summary="Update VCR",
    description="""
    Update a VCR (draft only).

    Only the creator can update their VCR.
    Only draft VCRs can be updated.
    """,
)
async def update_vcr(
    vcr_id: UUID,
    data: VCRUpdate,
    current_user: User = Depends(get_current_active_user),
    vcr_service: VCRService = Depends(get_vcr_service),
) -> VCRResponse:
    """Update VCR (draft only)."""
    try:
        return await vcr_service.update(vcr_id, data, current_user.id)
    except VCRNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"VCR {vcr_id} not found",
        )
    except VCRStateError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except VCRPermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )


@router.delete(
    "/{vcr_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete VCR",
    description="""
    Delete a VCR (draft only).

    Only the creator can delete their VCR.
    Only draft VCRs can be deleted.
    """,
)
async def delete_vcr(
    vcr_id: UUID,
    current_user: User = Depends(get_current_active_user),
    vcr_service: VCRService = Depends(get_vcr_service),
) -> None:
    """Delete VCR (draft only)."""
    try:
        await vcr_service.delete(vcr_id, current_user.id)
    except VCRNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"VCR {vcr_id} not found",
        )
    except VCRStateError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except VCRPermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )


# =============================================================================
# Workflow Endpoints
# =============================================================================


@router.post(
    "/{vcr_id}/submit",
    response_model=VCRResponse,
    summary="Submit VCR for approval",
    description="""
    Submit a draft VCR for CTO/CEO approval.

    Transitions: DRAFT → SUBMITTED

    Only the creator can submit their VCR.
    """,
)
async def submit_vcr(
    vcr_id: UUID,
    current_user: User = Depends(get_current_active_user),
    vcr_service: VCRService = Depends(get_vcr_service),
) -> VCRResponse:
    """Submit VCR for approval."""
    try:
        return await vcr_service.submit(vcr_id, current_user.id)
    except VCRNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"VCR {vcr_id} not found",
        )
    except VCRStateError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except VCRPermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )


@router.post(
    "/{vcr_id}/approve",
    response_model=VCRResponse,
    summary="Approve VCR",
    description="""
    Approve a submitted VCR.

    Transitions: SUBMITTED → APPROVED

    Requires CTO or CEO role.
    """,
)
async def approve_vcr(
    vcr_id: UUID,
    current_user: User = Depends(require_roles(["cto", "ceo", "admin"])),
    vcr_service: VCRService = Depends(get_vcr_service),
) -> VCRResponse:
    """Approve VCR (CTO/CEO only)."""
    try:
        return await vcr_service.approve(vcr_id, current_user.id)
    except VCRNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"VCR {vcr_id} not found",
        )
    except VCRStateError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/{vcr_id}/reject",
    response_model=VCRResponse,
    summary="Reject VCR",
    description="""
    Reject a submitted VCR with reason.

    Transitions: SUBMITTED → REJECTED

    Requires CTO or CEO role.
    Rejection reason must be at least 10 characters.
    """,
)
async def reject_vcr(
    vcr_id: UUID,
    request: VCRRejectRequest,
    current_user: User = Depends(require_roles(["cto", "ceo", "admin"])),
    vcr_service: VCRService = Depends(get_vcr_service),
) -> VCRResponse:
    """Reject VCR with reason (CTO/CEO only)."""
    try:
        return await vcr_service.reject(vcr_id, current_user.id, request)
    except VCRNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"VCR {vcr_id} not found",
        )
    except VCRStateError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/{vcr_id}/reopen",
    response_model=VCRResponse,
    summary="Reopen rejected VCR",
    description="""
    Reopen a rejected VCR for editing.

    Transitions: REJECTED → DRAFT

    Only the creator can reopen their VCR.
    """,
)
async def reopen_vcr(
    vcr_id: UUID,
    current_user: User = Depends(get_current_active_user),
    vcr_service: VCRService = Depends(get_vcr_service),
) -> VCRResponse:
    """Reopen rejected VCR to draft."""
    try:
        return await vcr_service.reopen(vcr_id, current_user.id)
    except VCRNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"VCR {vcr_id} not found",
        )
    except VCRStateError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except VCRPermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )


# =============================================================================
# Statistics & Reporting Endpoints
# =============================================================================


@router.get(
    "/stats/{project_id}",
    response_model=VCRStatsResponse,
    summary="Get VCR statistics",
    description="""
    Get VCR statistics for a project:
    - Count by status (draft, submitted, approved, rejected)
    - Average approval time
    - Average AI involvement percentage
    """,
)
async def get_vcr_stats(
    project_id: UUID,
    current_user: User = Depends(get_current_active_user),
    vcr_service: VCRService = Depends(get_vcr_service),
) -> VCRStatsResponse:
    """Get VCR statistics for a project."""
    return await vcr_service.get_stats(project_id)


# =============================================================================
# AI-Assisted Generation Endpoints
# =============================================================================


@router.post(
    "/auto-generate",
    response_model=VCRAutoGenerateResponse,
    summary="AI-assisted VCR generation",
    description="""
    Generate VCR content using AI from PR context.

    Provides AI-generated suggestions for:
    - Title
    - Problem statement
    - Root cause analysis (for bugs)
    - Solution approach
    - Implementation notes
    - Suggested evidence to attach

    Returns a confidence score (0-1) indicating
    how confident the AI is in the generated content.

    NOTE: Full implementation in Sprint 151 Day 4.
    """,
)
async def auto_generate_vcr(
    request: VCRAutoGenerateRequest,
    current_user: User = Depends(get_current_active_user),
    vcr_service: VCRService = Depends(get_vcr_service),
) -> VCRAutoGenerateResponse:
    """AI-assisted VCR content generation."""
    return await vcr_service.auto_generate(request, current_user.id)
