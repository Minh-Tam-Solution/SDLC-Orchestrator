"""
Override Schemas - VCR (Version Controlled Resolution) Flow

SDLC Stage: 04 - BUILD
Sprint: 43 - Policy Guards & Evidence UI
Framework: SDLC 5.1.1
Epic: EP-02 AI Safety Layer v1

Purpose:
Pydantic schemas for Override API endpoints.
Provides request/response models for VCR override workflow.

Features:
- Override request creation with validation
- Approval/rejection flows with audit
- Admin queue management
- Statistics and reporting
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# =============================================================================
# Enums
# =============================================================================


class OverrideType(str, Enum):
    """Types of override requests."""

    FALSE_POSITIVE = "false_positive"
    APPROVED_RISK = "approved_risk"
    EMERGENCY = "emergency"


class OverrideStatus(str, Enum):
    """Override request status."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class OverrideAuditAction(str, Enum):
    """Audit log action types."""

    REQUEST_CREATED = "request_created"
    REQUEST_UPDATED = "request_updated"
    REQUEST_CANCELLED = "request_cancelled"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    ESCALATED = "escalated"
    COMMENT_ADDED = "comment_added"


# =============================================================================
# Request Schemas
# =============================================================================


class OverrideRequestCreate(BaseModel):
    """Request to create an override."""

    event_id: UUID = Field(..., description="AI code event ID")
    override_type: OverrideType = Field(..., description="Type of override")
    reason: str = Field(
        ...,
        min_length=50,
        max_length=2000,
        description="Justification for override (min 50 chars)",
    )

    @field_validator("reason")
    @classmethod
    def validate_reason(cls, v: str) -> str:
        """Ensure reason is meaningful."""
        if not v.strip():
            raise ValueError("Reason cannot be empty or whitespace only")
        return v.strip()

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "event_id": "550e8400-e29b-41d4-a716-446655440000",
                    "override_type": "approved_risk",
                    "reason": "The failing SAST check is a false positive. The SQL query uses parameterized queries via SQLAlchemy ORM which prevents SQL injection. Verified by security team review.",
                }
            ]
        }
    }


class OverrideApprovalRequest(BaseModel):
    """Request to approve an override."""

    comment: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Approval comment (optional)",
    )


class OverrideRejectionRequest(BaseModel):
    """Request to reject an override."""

    reason: str = Field(
        ...,
        min_length=10,
        max_length=500,
        description="Rejection reason",
    )


class OverrideCancellationRequest(BaseModel):
    """Request to cancel an override."""

    reason: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Cancellation reason (optional)",
    )


# =============================================================================
# Response Schemas
# =============================================================================


class UserBrief(BaseModel):
    """Brief user info for responses."""

    id: UUID
    username: str
    display_name: Optional[str] = None

    model_config = {"from_attributes": True}


class OverrideAuditLogResponse(BaseModel):
    """Audit log entry response."""

    id: UUID
    action: OverrideAuditAction
    action_by: Optional[UserBrief] = None
    action_at: datetime
    previous_status: Optional[OverrideStatus] = None
    new_status: Optional[OverrideStatus] = None
    comment: Optional[str] = None
    ip_address: Optional[str] = None

    model_config = {"from_attributes": True}


class OverrideResponse(BaseModel):
    """Full override response with details."""

    id: UUID
    event_id: UUID
    project_id: UUID
    override_type: OverrideType
    reason: str
    status: OverrideStatus

    # Requester
    requested_by: Optional[UserBrief] = None
    requested_at: datetime

    # Resolution
    resolved_by: Optional[UserBrief] = None
    resolved_at: Optional[datetime] = None
    resolution_comment: Optional[str] = None

    # PR info (denormalized)
    pr_number: Optional[str] = None
    pr_title: Optional[str] = None
    failed_validators: List[str] = Field(default_factory=list)

    # Expiry
    expires_at: Optional[datetime] = None
    is_expired: bool = False

    # Emergency override
    post_merge_review_required: bool = False
    post_merge_review_completed: bool = False
    post_merge_reviewed_at: Optional[datetime] = None

    # Timestamps
    created_at: datetime
    updated_at: datetime

    # Audit trail
    audit_logs: List[OverrideAuditLogResponse] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class OverrideSummary(BaseModel):
    """Brief override info for lists."""

    id: UUID
    event_id: UUID
    project_id: UUID
    override_type: OverrideType
    status: OverrideStatus
    pr_number: Optional[str] = None
    pr_title: Optional[str] = None
    requested_by_name: Optional[str] = None
    requested_at: datetime
    resolved_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# =============================================================================
# Queue Schemas
# =============================================================================


class OverrideQueueItem(BaseModel):
    """Item in the override approval queue."""

    id: UUID
    event_id: UUID
    project_id: UUID
    project_name: str

    # Request details
    override_type: OverrideType
    reason: str
    status: OverrideStatus

    # PR info
    pr_number: Optional[str] = None
    pr_title: Optional[str] = None

    # Requester
    requested_by_name: str
    requested_at: datetime

    # Validation info
    failed_validators: List[str] = Field(default_factory=list)
    ai_tool: Optional[str] = None
    confidence_score: Optional[int] = None

    # Expiry
    expires_at: Optional[datetime] = None
    hours_until_expiry: Optional[int] = None

    model_config = {"from_attributes": True}


class RecentDecision(BaseModel):
    """Recent override decision for queue history."""

    id: UUID
    event_id: UUID
    project_name: str
    override_type: OverrideType
    status: OverrideStatus
    pr_number: Optional[str] = None
    requested_by_name: str
    resolved_by_name: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolution_comment: Optional[str] = None

    model_config = {"from_attributes": True}


class OverrideQueueResponse(BaseModel):
    """Response for admin override queue endpoint."""

    pending: List[OverrideQueueItem] = Field(default_factory=list)
    recent_decisions: List[RecentDecision] = Field(default_factory=list)
    total_pending: int = 0


# =============================================================================
# Statistics Schemas
# =============================================================================


class OverrideStats(BaseModel):
    """Override statistics for a project or global."""

    total_requests: int = 0
    pending_count: int = 0
    approved_count: int = 0
    rejected_count: int = 0
    expired_count: int = 0
    cancelled_count: int = 0

    # Rates
    approval_rate: float = Field(default=0.0, description="Percentage 0-100")
    rejection_rate: float = Field(default=0.0, description="Percentage 0-100")

    # Timing
    avg_resolution_hours: float = Field(
        default=0.0,
        description="Average time to resolve in hours",
    )

    # By type breakdown
    by_type: Dict[str, int] = Field(
        default_factory=dict,
        description="Count by override type",
    )

    # Emergency override tracking
    emergency_total: int = 0
    emergency_pending_review: int = 0


class OverrideStatsResponse(BaseModel):
    """Response for override statistics endpoint."""

    stats: OverrideStats
    period_days: int = 30
    generated_at: datetime


# =============================================================================
# List/Filter Schemas
# =============================================================================


class OverrideListFilters(BaseModel):
    """Filters for override list."""

    status: Optional[OverrideStatus] = None
    override_type: Optional[OverrideType] = None
    requested_by_id: Optional[UUID] = None
    date_start: Optional[datetime] = None
    date_end: Optional[datetime] = None
    pr_number: Optional[str] = None


class OverrideListResponse(BaseModel):
    """Paginated response for override list."""

    overrides: List[OverrideSummary] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    pages: int = 1
    has_next: bool = False
