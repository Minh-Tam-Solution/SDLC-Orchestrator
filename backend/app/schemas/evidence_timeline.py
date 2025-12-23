"""
Evidence Timeline Schemas - AI Code Event Display

SDLC Stage: 04 - BUILD
Sprint: 43 - Policy Guards & Evidence UI
Framework: SDLC 5.1.1
Epic: EP-02 AI Safety Layer v1

Purpose:
Pydantic schemas for Evidence Timeline API endpoints.
Provides data models for AI code event display and filtering.

Features:
- Timeline event representation
- Filtering and pagination
- Stats aggregation
- Override request/approval flow
- Export formats
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# =============================================================================
# Enums
# =============================================================================


class AIToolType(str, Enum):
    """Supported AI coding tools."""

    CURSOR = "cursor"
    COPILOT = "copilot"
    CLAUDE = "claude"
    CHATGPT = "chatgpt"
    WINDSURF = "windsurf"
    CODY = "cody"
    TABNINE = "tabnine"
    OTHER = "other"
    MANUAL = "manual"


class ValidationStatus(str, Enum):
    """Validation pipeline status."""

    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    OVERRIDDEN = "overridden"
    ERROR = "error"


class OverrideStatus(str, Enum):
    """Override request status."""

    NONE = "none"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class OverrideType(str, Enum):
    """Types of override requests."""

    FALSE_POSITIVE = "false_positive"
    APPROVED_RISK = "approved_risk"
    EMERGENCY = "emergency"


class ValidatorName(str, Enum):
    """Validator types in the pipeline."""

    LINT = "lint"
    TESTS = "tests"
    COVERAGE = "coverage"
    SAST = "sast"
    POLICY_GUARDS = "policy_guards"
    AI_SECURITY = "ai_security"


# =============================================================================
# Validator Result
# =============================================================================


class ValidatorResultSummary(BaseModel):
    """Summary of a single validator result."""

    name: ValidatorName
    status: str = Field(..., description="passed, failed, skipped, error")
    duration_ms: int = Field(default=0, description="Execution time in ms")
    message: Optional[str] = Field(default=None, description="Result message")
    details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional details",
    )
    blocking: bool = Field(default=True, description="Whether this blocks merge")


# =============================================================================
# Evidence Event
# =============================================================================


class EvidenceEventBase(BaseModel):
    """Base model for evidence events."""

    # PR/Commit info
    pr_number: str = Field(..., description="PR number")
    pr_title: str = Field(..., description="PR title")
    pr_author: str = Field(..., description="PR author username")
    commit_sha: Optional[str] = Field(default=None, description="Commit SHA")
    branch_name: Optional[str] = Field(default=None, description="Branch name")

    # AI Detection
    ai_tool: AIToolType = Field(..., description="Detected AI tool")
    ai_model: Optional[str] = Field(default=None, description="AI model version")
    confidence_score: int = Field(..., ge=0, le=100, description="Detection confidence")
    detection_method: str = Field(
        default="metadata",
        description="Detection method used",
    )

    # Validation
    validation_status: ValidationStatus
    validation_duration_ms: int = Field(default=0, description="Total validation time")

    # Files
    files_changed: int = Field(default=0, description="Number of files changed")
    lines_added: int = Field(default=0, description="Lines added")
    lines_deleted: int = Field(default=0, description="Lines deleted")


class EvidenceEventSummary(EvidenceEventBase):
    """Event summary for timeline list view."""

    id: UUID
    project_id: UUID
    created_at: datetime

    # Validators summary (pass/fail counts)
    validators_passed: int = 0
    validators_failed: int = 0
    validators_total: int = 0

    # Override info
    override_status: OverrideStatus = OverrideStatus.NONE
    override_requested_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class EvidenceEventDetail(EvidenceEventSummary):
    """Full event detail with validation results."""

    # Validation results
    validator_results: List[ValidatorResultSummary] = Field(
        default_factory=list,
        description="Individual validator results",
    )

    # Evidence data
    detection_evidence: Dict[str, Any] = Field(
        default_factory=dict,
        description="Detection evidence details",
    )

    # Override history
    override_history: List["OverrideRecord"] = Field(
        default_factory=list,
        description="Override request history",
    )

    # GitHub integration
    github_check_run_id: Optional[str] = None
    github_pr_url: Optional[str] = None

    model_config = {"from_attributes": True}


# =============================================================================
# Override Records
# =============================================================================


class OverrideRecord(BaseModel):
    """Record of an override request/decision."""

    id: UUID
    event_id: UUID

    # Request
    override_type: OverrideType
    reason: str
    requested_by_id: UUID
    requested_by_name: str
    requested_at: datetime

    # Resolution
    status: OverrideStatus
    resolved_by_id: Optional[UUID] = None
    resolved_by_name: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolution_comment: Optional[str] = None

    model_config = {"from_attributes": True}


class OverrideRequest(BaseModel):
    """Request to create an override."""

    override_type: OverrideType
    reason: str = Field(
        ...,
        min_length=50,
        max_length=2000,
        description="Justification for override",
    )

    model_config = {"json_schema_extra": {"examples": [
        {
            "override_type": "approved_risk",
            "reason": "The failing tests are for a feature that is not yet deployed. This PR only updates the payment service which has separate tests. Coverage will be improved in follow-up PR #235.",
        }
    ]}}


class OverrideApproval(BaseModel):
    """Approval for an override request."""

    comment: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Approval comment",
    )


class OverrideRejection(BaseModel):
    """Rejection for an override request."""

    reason: str = Field(
        ...,
        min_length=10,
        max_length=500,
        description="Rejection reason",
    )


# =============================================================================
# Filters and Pagination
# =============================================================================


class EvidenceFilters(BaseModel):
    """Filters for evidence timeline."""

    date_start: Optional[datetime] = None
    date_end: Optional[datetime] = None
    ai_tool: Optional[AIToolType] = None
    confidence_min: int = Field(default=0, ge=0, le=100)
    confidence_max: int = Field(default=100, ge=0, le=100)
    validation_status: Optional[ValidationStatus] = None
    override_status: Optional[OverrideStatus] = None
    pr_author: Optional[str] = None
    search: Optional[str] = Field(
        default=None,
        description="Search in PR title/number",
    )


class PaginationParams(BaseModel):
    """Pagination parameters."""

    page: int = Field(default=1, ge=1)
    limit: int = Field(default=20, ge=1, le=100)


# =============================================================================
# Response Models
# =============================================================================


class EvidenceTimelineStats(BaseModel):
    """Statistics for the timeline header."""

    total_events: int = 0
    ai_detected: int = 0
    pass_rate: float = Field(default=0.0, description="Percentage 0-100")
    override_rate: float = Field(default=0.0, description="Percentage 0-100")

    # By tool breakdown
    by_tool: Dict[str, int] = Field(
        default_factory=dict,
        description="Count by AI tool",
    )

    # By status breakdown
    by_status: Dict[str, int] = Field(
        default_factory=dict,
        description="Count by validation status",
    )


class EvidenceTimelineResponse(BaseModel):
    """Response for timeline list endpoint."""

    events: List[EvidenceEventSummary]
    stats: EvidenceTimelineStats
    total: int
    page: int
    pages: int
    has_next: bool


class OverrideQueueItem(BaseModel):
    """Item in the override approval queue."""

    id: UUID
    event_id: UUID

    # PR info
    pr_number: str
    pr_title: str
    project_name: str
    project_id: UUID

    # Request details
    override_type: OverrideType
    reason: str
    requested_by_name: str
    requested_at: datetime

    # Validation failures
    failed_validators: List[str] = Field(default_factory=list)
    ai_tool: AIToolType
    confidence_score: int

    model_config = {"from_attributes": True}


class OverrideQueueResponse(BaseModel):
    """Response for override queue endpoint."""

    pending: List[OverrideQueueItem]
    recent_decisions: List[OverrideRecord]
    total_pending: int


# =============================================================================
# Export
# =============================================================================


class ExportFormat(str, Enum):
    """Export file formats."""

    CSV = "csv"
    JSON = "json"


class ExportRequest(BaseModel):
    """Request for evidence export."""

    format: ExportFormat = ExportFormat.CSV
    date_start: Optional[datetime] = None
    date_end: Optional[datetime] = None
    include_details: bool = Field(
        default=False,
        description="Include validator details",
    )


class ExportResponse(BaseModel):
    """Response for export endpoint."""

    download_url: str
    format: ExportFormat
    events_count: int
    expires_at: datetime
