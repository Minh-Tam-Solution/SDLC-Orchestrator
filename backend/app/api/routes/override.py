"""
Override API Router - VCR (Version Controlled Resolution) Workflow

SDLC Stage: 04 - BUILD
Sprint: 43 - Policy Guards & Evidence UI
Framework: SDLC 5.1.1
Epic: EP-02 AI Safety Layer v1

Purpose:
API endpoints for the Override workflow:
- Create override requests
- Admin queue management
- Approve/reject overrides
- Override statistics

API Endpoints (9):
1. POST /overrides/request - Create override request
2. GET /overrides/{id} - Get override details
3. GET /overrides/event/{event_id} - Get overrides for event
4. POST /overrides/{id}/approve - Approve override (admin)
5. POST /overrides/{id}/reject - Reject override (admin)
6. POST /overrides/{id}/cancel - Cancel override (requester)
7. GET /admin/override-queue - Get pending queue
8. GET /admin/override-stats - Get override statistics
9. GET /projects/{id}/overrides - Get project overrides

Zero Mock Policy: 100% COMPLIANCE (all real implementations)
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user, require_role
from app.db.session import get_db
from app.models.override import OverrideStatus, OverrideType
from app.models.user import User
from app.services.override_service import (
    OverrideNotFoundError,
    OverridePermissionError,
    OverrideService,
    OverrideValidationError,
    get_override_service,
)

router = APIRouter()


# =============================================================================
# Request/Response Schemas
# =============================================================================


class OverrideRequestCreate(BaseModel):
    """Request to create an override."""

    event_id: UUID = Field(..., description="AI code event ID")
    override_type: OverrideType = Field(..., description="Type of override")
    reason: str = Field(
        ...,
        min_length=50,
        max_length=2000,
        description="Justification for override",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "event_id": "123e4567-e89b-12d3-a456-426614174000",
                    "override_type": "false_positive",
                    "reason": "This is a false positive. The detected pattern is in a test file which is excluded from production deployment. The pattern was flagged due to test data containing mock API keys.",
                }
            ]
        }
    }


class OverrideApprovalRequest(BaseModel):
    """Request to approve an override."""

    comment: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Optional approval comment",
    )


class OverrideRejectionRequest(BaseModel):
    """Request to reject an override."""

    reason: str = Field(
        ...,
        min_length=10,
        max_length=500,
        description="Rejection reason",
    )


class OverrideResponse(BaseModel):
    """Override response model."""

    id: UUID
    event_id: UUID
    project_id: UUID
    override_type: str
    reason: str
    status: str
    requested_by_id: Optional[UUID]
    requested_by_name: Optional[str]
    requested_at: datetime
    resolved_by_id: Optional[UUID]
    resolved_by_name: Optional[str]
    resolved_at: Optional[datetime]
    resolution_comment: Optional[str]
    pr_number: Optional[str]
    pr_title: Optional[str]
    failed_validators: Optional[list[str]]
    expires_at: Optional[datetime]
    is_expired: bool
    post_merge_review_required: bool
    created_at: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_with_names(cls, override, requested_by=None, resolved_by=None):
        """Create response from ORM object with user names."""
        import json

        failed_validators = None
        if override.failed_validators:
            try:
                failed_validators = json.loads(override.failed_validators)
            except (json.JSONDecodeError, TypeError):
                failed_validators = []

        return cls(
            id=override.id,
            event_id=override.event_id,
            project_id=override.project_id,
            override_type=override.override_type.value if override.override_type else None,
            reason=override.reason,
            status=override.status.value if override.status else None,
            requested_by_id=override.requested_by_id,
            requested_by_name=requested_by.name if requested_by else None,
            requested_at=override.requested_at,
            resolved_by_id=override.resolved_by_id,
            resolved_by_name=resolved_by.name if resolved_by else None,
            resolved_at=override.resolved_at,
            resolution_comment=override.resolution_comment,
            pr_number=override.pr_number,
            pr_title=override.pr_title,
            failed_validators=failed_validators,
            expires_at=override.expires_at,
            is_expired=override.is_expired or False,
            post_merge_review_required=override.post_merge_review_required or False,
            created_at=override.created_at,
        )


class OverrideQueueResponse(BaseModel):
    """Response for override queue."""

    pending: list[OverrideResponse]
    recent_decisions: list[OverrideResponse]
    total_pending: int


class OverrideStatsResponse(BaseModel):
    """Response for override statistics."""

    total: int
    by_status: dict[str, int]
    by_type: dict[str, int]
    approval_rate: float
    pending: int
    days: int


# =============================================================================
# Override Request Endpoints
# =============================================================================


@router.post(
    "/overrides/request",
    response_model=OverrideResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create override request",
    description="""
    Create a new override request for a failed validation event.

    **Request Body**:
    - event_id: ID of the AI code event (must be failed/warning)
    - override_type: Type of override (false_positive, approved_risk, emergency)
    - reason: Detailed justification (min 50 chars)

    **Business Rules**:
    - Event must have failed or warning validation status
    - Only one pending override per event allowed
    - Emergency overrides require post-merge review

    **Response** (201 Created):
    - Created override record with PENDING status
    """,
)
async def create_override_request(
    request_data: OverrideRequestCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new override request."""
    service = get_override_service(db)

    # Get client info for audit
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    try:
        override = await service.create_override_request(
            event_id=request_data.event_id,
            override_type=request_data.override_type,
            reason=request_data.reason,
            requested_by=current_user,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        return OverrideResponse.from_orm_with_names(
            override,
            requested_by=current_user,
        )

    except OverrideNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except OverrideValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "/overrides/{override_id}",
    response_model=OverrideResponse,
    summary="Get override details",
    description="Get detailed information about an override request.",
)
async def get_override(
    override_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get override details by ID."""
    service = get_override_service(db)

    override = await service.get_override(override_id)
    if not override:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Override with ID {override_id} not found",
        )

    return OverrideResponse.from_orm_with_names(
        override,
        requested_by=override.requested_by,
        resolved_by=override.resolved_by,
    )


@router.get(
    "/overrides/event/{event_id}",
    response_model=list[OverrideResponse],
    summary="Get overrides for event",
    description="Get all override requests for a specific AI code event.",
)
async def get_overrides_for_event(
    event_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get all overrides for an event."""
    service = get_override_service(db)

    overrides = await service.get_overrides_for_event(event_id)

    return [
        OverrideResponse.from_orm_with_names(
            o,
            requested_by=o.requested_by if hasattr(o, 'requested_by') else None,
            resolved_by=o.resolved_by if hasattr(o, 'resolved_by') else None,
        )
        for o in overrides
    ]


# =============================================================================
# Approve/Reject Endpoints
# =============================================================================


@router.post(
    "/overrides/{override_id}/approve",
    response_model=OverrideResponse,
    summary="Approve override",
    description="""
    Approve a pending override request.

    **Access Control**:
    - Requires ADMIN, MANAGER, or SECURITY role

    **Side Effects**:
    - Updates AICodeEvent.validation_result to 'overridden'
    - Creates audit log entry

    **Request Body**:
    - comment: Optional approval comment
    """,
)
async def approve_override(
    override_id: UUID,
    approval: OverrideApprovalRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager", "security", "cto", "ceo"])),
):
    """Approve a pending override request."""
    service = get_override_service(db)

    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    try:
        override = await service.approve_override(
            override_id=override_id,
            approver=current_user,
            comment=approval.comment,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        return OverrideResponse.from_orm_with_names(
            override,
            requested_by=override.requested_by,
            resolved_by=current_user,
        )

    except OverrideNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except OverridePermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )
    except OverrideValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/overrides/{override_id}/reject",
    response_model=OverrideResponse,
    summary="Reject override",
    description="""
    Reject a pending override request.

    **Access Control**:
    - Requires ADMIN, MANAGER, or SECURITY role

    **Request Body**:
    - reason: Required rejection reason (min 10 chars)
    """,
)
async def reject_override(
    override_id: UUID,
    rejection: OverrideRejectionRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager", "security", "cto", "ceo"])),
):
    """Reject a pending override request."""
    service = get_override_service(db)

    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    try:
        override = await service.reject_override(
            override_id=override_id,
            rejector=current_user,
            reason=rejection.reason,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        return OverrideResponse.from_orm_with_names(
            override,
            requested_by=override.requested_by,
            resolved_by=current_user,
        )

    except OverrideNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except OverridePermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )
    except OverrideValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/overrides/{override_id}/cancel",
    response_model=OverrideResponse,
    summary="Cancel override",
    description="""
    Cancel a pending override request.

    **Access Control**:
    - Requester can cancel their own request
    - Admins can cancel any request
    """,
)
async def cancel_override(
    override_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Cancel a pending override request."""
    service = get_override_service(db)

    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    try:
        override = await service.cancel_override(
            override_id=override_id,
            user=current_user,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        return OverrideResponse.from_orm_with_names(
            override,
            requested_by=override.requested_by,
        )

    except OverrideNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except OverridePermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )
    except OverrideValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# =============================================================================
# Admin Queue Endpoints
# =============================================================================


@router.get(
    "/admin/override-queue",
    response_model=OverrideQueueResponse,
    summary="Get override approval queue",
    description="""
    Get list of pending override requests for admin approval.

    **Access Control**:
    - Requires ADMIN, MANAGER, or SECURITY role

    **Query Parameters**:
    - project_id: Filter by project (optional)
    - limit: Max pending items (default: 50)

    **Response**:
    - pending: List of pending override requests
    - recent_decisions: Recent approvals/rejections for reference
    - total_pending: Total count of pending requests
    """,
)
async def get_override_queue(
    project_id: Optional[UUID] = Query(None, description="Filter by project"),
    limit: int = Query(50, ge=1, le=100, description="Max pending items"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager", "security", "cto", "ceo"])),
):
    """Get pending override requests for admin approval."""
    service = get_override_service(db)

    # Get pending queue
    pending_overrides, total_pending = await service.get_pending_queue(
        project_id=project_id,
        limit=limit,
    )

    # Get recent decisions
    recent_decisions = await service.get_recent_decisions(
        project_id=project_id,
        limit=10,
    )

    return OverrideQueueResponse(
        pending=[
            OverrideResponse.from_orm_with_names(
                o,
                requested_by=o.requested_by if hasattr(o, 'requested_by') else None,
            )
            for o in pending_overrides
        ],
        recent_decisions=[
            OverrideResponse.from_orm_with_names(
                o,
                requested_by=o.requested_by if hasattr(o, 'requested_by') else None,
                resolved_by=o.resolved_by if hasattr(o, 'resolved_by') else None,
            )
            for o in recent_decisions
        ],
        total_pending=total_pending,
    )


@router.get(
    "/admin/override-stats",
    response_model=OverrideStatsResponse,
    summary="Get override statistics",
    description="""
    Get override statistics for dashboard.

    **Access Control**:
    - Requires ADMIN, MANAGER, or SECURITY role

    **Query Parameters**:
    - project_id: Filter by project (optional)
    - days: Number of days to include (default: 30)
    """,
)
async def get_override_stats(
    project_id: Optional[UUID] = Query(None, description="Filter by project"),
    days: int = Query(30, ge=1, le=365, description="Days to include"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager", "security", "cto", "ceo"])),
):
    """Get override statistics."""
    service = get_override_service(db)

    stats = await service.get_override_stats(
        project_id=project_id,
        days=days,
    )

    return OverrideStatsResponse(**stats)


# =============================================================================
# Project-scoped Endpoints
# =============================================================================


@router.get(
    "/projects/{project_id}/overrides",
    response_model=list[OverrideResponse],
    summary="Get project overrides",
    description="Get all override requests for a project.",
)
async def get_project_overrides(
    project_id: UUID,
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    limit: int = Query(50, ge=1, le=100, description="Max items"),
    offset: int = Query(0, ge=0, description="Offset"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get all overrides for a project."""
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    from app.models.override import ValidationOverride

    query = (
        select(ValidationOverride)
        .options(
            selectinload(ValidationOverride.requested_by),
            selectinload(ValidationOverride.resolved_by),
        )
        .where(ValidationOverride.project_id == project_id)
    )

    if status_filter:
        try:
            status_enum = OverrideStatus(status_filter)
            query = query.where(ValidationOverride.status == status_enum)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {status_filter}",
            )

    query = query.order_by(ValidationOverride.created_at.desc())
    query = query.offset(offset).limit(limit)

    result = await db.execute(query)
    overrides = result.scalars().all()

    return [
        OverrideResponse.from_orm_with_names(
            o,
            requested_by=o.requested_by,
            resolved_by=o.resolved_by,
        )
        for o in overrides
    ]
