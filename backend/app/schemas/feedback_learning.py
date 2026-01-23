"""
=========================================================================
Feedback Learning Schemas - Pydantic Models for EP-11 API Validation
SDLC Orchestrator - Sprint 100 (Feedback Learning Service)

Version: 1.0.0
Date: January 23, 2026
Status: ACTIVE - Sprint 100 Implementation
Authority: Backend Lead + CTO Approved
Reference: docs/02-design/14-Technical-Specs/Feedback-Learning-Service-Design.md

Purpose:
- API request/response validation for PR Learnings
- Decomposition Hints CRUD operations
- Learning Aggregation workflows
- GitHub webhook payload validation

EP-11 Feedback Loop:
1. PR merged → Extract learnings from review comments
2. Monthly → Aggregate learnings → Generate hints
3. Quarterly → Synthesize → CLAUDE.md suggestions
4. Track effectiveness → Close feedback loop

Zero Mock Policy: Production-ready Pydantic v2 models
=========================================================================
"""

from datetime import date, datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


# =========================================================================
# Enums
# =========================================================================


class FeedbackType(str, Enum):
    """PR review feedback type classification."""

    PATTERN_VIOLATION = "pattern_violation"
    MISSING_REQUIREMENT = "missing_requirement"
    EDGE_CASE = "edge_case"
    PERFORMANCE = "performance"
    SECURITY_ISSUE = "security_issue"
    TEST_COVERAGE = "test_coverage"
    DOCUMENTATION = "documentation"
    REFACTORING = "refactoring"
    OTHER = "other"


class Severity(str, Enum):
    """Feedback severity level."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class LearningStatus(str, Enum):
    """PR learning processing status."""

    EXTRACTED = "extracted"  # Just extracted from PR
    REVIEWED = "reviewed"  # Human reviewed
    APPLIED = "applied"  # Applied to hints/CLAUDE.md
    ARCHIVED = "archived"  # No longer active


class HintType(str, Enum):
    """Decomposition hint type."""

    PATTERN = "pattern"  # Reusable pattern to follow
    ANTIPATTERN = "antipattern"  # Common mistake to avoid
    CONVENTION = "convention"  # Naming/structure convention
    CHECKLIST = "checklist"  # Items to verify
    DEPENDENCY = "dependency"  # Hidden dependencies


class HintCategory(str, Enum):
    """Decomposition hint domain category."""

    SECURITY = "security"
    TESTING = "testing"
    ARCHITECTURE = "architecture"
    NAMING = "naming"
    ERROR_HANDLING = "error_handling"
    PERFORMANCE = "performance"
    DOCUMENTATION = "documentation"
    ACCESSIBILITY = "accessibility"
    API_DESIGN = "api_design"
    DATABASE = "database"
    FRONTEND = "frontend"
    BACKEND = "backend"
    DEVOPS = "devops"
    OTHER = "other"


class HintStatus(str, Enum):
    """Decomposition hint lifecycle status."""

    ACTIVE = "active"  # Currently in use
    DEPRECATED = "deprecated"  # Superseded
    MERGED = "merged"  # Merged into another hint
    ARCHIVED = "archived"  # No longer relevant


class AggregationPeriod(str, Enum):
    """Learning aggregation period type."""

    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"


class AggregationStatus(str, Enum):
    """Learning aggregation processing status."""

    PENDING = "pending"  # Awaiting processing
    PROCESSED = "processed"  # Suggestions generated
    APPLIED = "applied"  # Suggestions applied
    REJECTED = "rejected"  # Suggestions rejected


class HintUsageOutcome(str, Enum):
    """Outcome of using a hint in decomposition."""

    PREVENTED_ERROR = "prevented_error"  # Hint prevented an error
    NO_EFFECT = "no_effect"  # No measurable effect
    FALSE_POSITIVE = "false_positive"  # Hint was not applicable


# =========================================================================
# PR Learning Schemas
# =========================================================================


class PRLearningBase(BaseModel):
    """Base schema for PR Learning with common fields."""

    pr_number: int = Field(..., ge=1, description="GitHub PR number")
    pr_title: Optional[str] = Field(None, max_length=255, description="PR title")
    pr_url: Optional[str] = Field(None, max_length=500, description="Full PR URL")
    feedback_type: FeedbackType = Field(..., description="Category of feedback")
    severity: Severity = Field(Severity.MEDIUM, description="Impact level")
    review_comment: str = Field(..., min_length=10, description="Original review comment")
    corrected_approach: Optional[str] = Field(None, description="Correct approach")
    pattern_extracted: Optional[str] = Field(None, description="Reusable pattern")
    file_path: Optional[str] = Field(None, max_length=500, description="File path")
    line_start: Optional[int] = Field(None, ge=1, description="Starting line")
    line_end: Optional[int] = Field(None, ge=1, description="Ending line")
    related_adr: Optional[str] = Field(None, max_length=100, description="Related ADR")
    tags: Optional[list[str]] = Field(default_factory=list, description="Tags")

    model_config = ConfigDict(use_enum_values=True)


class PRLearningCreate(PRLearningBase):
    """Schema for creating a new PR learning (manual entry)."""

    original_code: Optional[str] = Field(None, description="Problematic code snippet")
    original_spec_section: Optional[str] = Field(None, description="Related spec section")
    reviewer_github_login: Optional[str] = Field(
        None, max_length=100, description="GitHub reviewer username"
    )


class PRLearningExtract(BaseModel):
    """Schema for extracting learning from PR comment (AI-powered)."""

    pr_number: int = Field(..., ge=1, description="GitHub PR number")
    pr_title: str = Field(..., max_length=255, description="PR title")
    pr_url: str = Field(..., max_length=500, description="Full PR URL")
    comment_id: int = Field(..., ge=1, description="GitHub comment ID")
    comment_body: str = Field(..., min_length=10, description="Comment text")
    file_path: Optional[str] = Field(None, description="File being reviewed")
    diff_hunk: Optional[str] = Field(None, description="Code diff context")
    reviewer_github_login: str = Field(..., description="Reviewer username")


class PRLearningUpdate(BaseModel):
    """Schema for updating a PR learning."""

    feedback_type: Optional[FeedbackType] = None
    severity: Optional[Severity] = None
    corrected_approach: Optional[str] = None
    pattern_extracted: Optional[str] = None
    status: Optional[LearningStatus] = None
    tags: Optional[list[str]] = None

    model_config = ConfigDict(use_enum_values=True)


class PRLearningResponse(PRLearningBase):
    """Schema for PR learning API response."""

    id: UUID
    project_id: UUID
    pr_merged_at: Optional[datetime] = None
    original_code: Optional[str] = None
    original_spec_section: Optional[str] = None
    reviewer_id: Optional[UUID] = None
    reviewer_github_login: Optional[str] = None
    status: LearningStatus
    applied_to_claude_md: bool
    applied_to_decomposition: bool
    applied_at: Optional[datetime] = None
    ai_extracted: bool
    ai_confidence: Optional[float] = None
    ai_model: Optional[str] = None
    related_learnings: Optional[list[str]] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PRLearningListResponse(BaseModel):
    """Schema for paginated PR learning list."""

    items: list[PRLearningResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


class PRLearningStats(BaseModel):
    """Schema for PR learning statistics."""

    total_learnings: int
    by_feedback_type: dict[str, int]
    by_severity: dict[str, int]
    by_status: dict[str, int]
    applied_count: int
    pending_count: int
    period_start: Optional[date] = None
    period_end: Optional[date] = None


# =========================================================================
# Decomposition Hint Schemas
# =========================================================================


class DecompositionHintBase(BaseModel):
    """Base schema for Decomposition Hint with common fields."""

    hint_type: HintType = Field(..., description="Type of hint")
    category: HintCategory = Field(..., description="Domain category")
    subcategory: Optional[str] = Field(None, max_length=50, description="Subcategory")
    title: str = Field(..., min_length=5, max_length=255, description="Short title")
    description: str = Field(..., min_length=20, description="Full description")
    example_good: Optional[str] = Field(None, description="Good example")
    example_bad: Optional[str] = Field(None, description="Bad example")
    rationale: Optional[str] = Field(None, description="Why this matters")
    applies_to: list[str] = Field(
        default_factory=lambda: ["all"],
        description="Applies to: frontend, backend, api, database, all",
    )
    languages: list[str] = Field(
        default_factory=lambda: ["all"],
        description="Languages: python, typescript, all",
    )
    frameworks: list[str] = Field(
        default_factory=lambda: ["all"],
        description="Frameworks: react, fastapi, all",
    )
    tags: Optional[list[str]] = Field(default_factory=list, description="Tags")
    related_adrs: Optional[list[str]] = Field(
        default_factory=list, description="Related ADRs"
    )

    model_config = ConfigDict(use_enum_values=True)


class DecompositionHintCreate(DecompositionHintBase):
    """Schema for creating a decomposition hint (manual)."""

    source_learning_id: Optional[UUID] = Field(
        None, description="Source learning that generated hint"
    )
    confidence: float = Field(0.8, ge=0.0, le=1.0, description="Confidence score")


class DecompositionHintUpdate(BaseModel):
    """Schema for updating a decomposition hint."""

    hint_type: Optional[HintType] = None
    category: Optional[HintCategory] = None
    subcategory: Optional[str] = None
    title: Optional[str] = Field(None, min_length=5, max_length=255)
    description: Optional[str] = Field(None, min_length=20)
    example_good: Optional[str] = None
    example_bad: Optional[str] = None
    rationale: Optional[str] = None
    applies_to: Optional[list[str]] = None
    languages: Optional[list[str]] = None
    frameworks: Optional[list[str]] = None
    status: Optional[HintStatus] = None
    deprecated_reason: Optional[str] = None
    tags: Optional[list[str]] = None
    related_adrs: Optional[list[str]] = None

    model_config = ConfigDict(use_enum_values=True)


class DecompositionHintResponse(DecompositionHintBase):
    """Schema for decomposition hint API response."""

    id: UUID
    project_id: UUID
    source_learning_id: Optional[UUID] = None
    aggregation_id: Optional[UUID] = None
    merged_into_id: Optional[UUID] = None
    confidence: float
    usage_count: int
    effectiveness_score: Optional[float] = None
    prevented_errors: int
    last_used_at: Optional[datetime] = None
    status: HintStatus
    deprecated_reason: Optional[str] = None
    ai_generated: bool
    ai_model: Optional[str] = None
    human_verified: bool
    verified_by: Optional[UUID] = None
    verified_at: Optional[datetime] = None
    created_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DecompositionHintListResponse(BaseModel):
    """Schema for paginated decomposition hint list."""

    items: list[DecompositionHintResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


class DecompositionHintStats(BaseModel):
    """Schema for decomposition hint statistics."""

    total_hints: int
    active_hints: int
    by_type: dict[str, int]
    by_category: dict[str, int]
    total_usage: int
    total_prevented_errors: int
    average_effectiveness: Optional[float] = None
    human_verified_count: int


# =========================================================================
# Hint Usage Schemas
# =========================================================================


class HintUsageCreate(BaseModel):
    """Schema for recording hint usage."""

    hint_id: UUID = Field(..., description="Hint that was used")
    decomposition_session_id: Optional[UUID] = Field(
        None, description="Decomposition session"
    )
    task_description: Optional[str] = Field(None, description="Task being decomposed")
    plan_generated: Optional[str] = Field(None, description="Generated plan excerpt")


class HintUsageFeedback(BaseModel):
    """Schema for providing feedback on hint usage."""

    outcome: HintUsageOutcome = Field(..., description="Result of using hint")
    pr_id: Optional[int] = Field(None, description="Linked PR number")
    feedback: Optional[str] = Field(None, description="Human feedback")

    model_config = ConfigDict(use_enum_values=True)


class HintUsageResponse(BaseModel):
    """Schema for hint usage API response."""

    id: UUID
    hint_id: UUID
    project_id: UUID
    used_by: Optional[UUID] = None
    decomposition_session_id: Optional[UUID] = None
    task_description: Optional[str] = None
    outcome: Optional[str] = None
    pr_id: Optional[int] = None
    error_prevented: bool
    feedback: Optional[str] = None
    used_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =========================================================================
# Learning Aggregation Schemas
# =========================================================================


class LearningAggregationBase(BaseModel):
    """Base schema for Learning Aggregation."""

    period_type: AggregationPeriod = Field(..., description="Aggregation period")
    period_start: date = Field(..., description="Period start date")
    period_end: date = Field(..., description="Period end date")

    model_config = ConfigDict(use_enum_values=True)

    @field_validator("period_end")
    @classmethod
    def validate_period_end(cls, v: date, info) -> date:
        """Ensure period_end is after period_start."""
        if "period_start" in info.data and v <= info.data["period_start"]:
            raise ValueError("period_end must be after period_start")
        return v


class LearningAggregationCreate(LearningAggregationBase):
    """Schema for triggering a learning aggregation."""

    pass


class LearningAggregationResponse(LearningAggregationBase):
    """Schema for learning aggregation API response."""

    id: UUID
    project_id: UUID
    total_learnings: int
    by_feedback_type: dict[str, int]
    by_severity: dict[str, int]
    top_patterns: list[dict[str, Any]]
    top_files: list[dict[str, Any]]
    claude_md_suggestions: Optional[list[dict[str, Any]]] = None
    decomposition_hints: Optional[list[dict[str, Any]]] = None
    adr_recommendations: Optional[list[dict[str, Any]]] = None
    status: AggregationStatus
    processed_at: Optional[datetime] = None
    applied_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    processed_by: Optional[UUID] = None
    ai_model: Optional[str] = None
    ai_processing_time_ms: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LearningAggregationListResponse(BaseModel):
    """Schema for paginated aggregation list."""

    items: list[LearningAggregationResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


class AggregationApplyRequest(BaseModel):
    """Schema for applying aggregation suggestions."""

    apply_claude_md: bool = Field(True, description="Apply CLAUDE.md suggestions")
    apply_hints: bool = Field(True, description="Apply decomposition hints")
    apply_adrs: bool = Field(False, description="Apply ADR recommendations")
    reviewer_notes: Optional[str] = Field(None, description="Reviewer notes")


class AggregationRejectRequest(BaseModel):
    """Schema for rejecting aggregation suggestions."""

    reason: str = Field(..., min_length=10, description="Rejection reason")


# =========================================================================
# GitHub Webhook Schemas
# =========================================================================


class GitHubReviewCommentWebhook(BaseModel):
    """Schema for GitHub pull_request_review_comment webhook payload."""

    action: str = Field(..., description="Webhook action")
    comment: dict[str, Any] = Field(..., description="Comment data")
    pull_request: dict[str, Any] = Field(..., description="PR data")
    repository: dict[str, Any] = Field(..., description="Repository data")
    sender: dict[str, Any] = Field(..., description="User who triggered")


class GitHubPullRequestWebhook(BaseModel):
    """Schema for GitHub pull_request webhook payload (for PR merged)."""

    action: str = Field(..., description="Webhook action: closed, merged")
    pull_request: dict[str, Any] = Field(..., description="PR data")
    repository: dict[str, Any] = Field(..., description="Repository data")
    sender: dict[str, Any] = Field(..., description="User who triggered")


# =========================================================================
# Query/Filter Schemas
# =========================================================================


class LearningFilterParams(BaseModel):
    """Schema for filtering PR learnings."""

    feedback_type: Optional[FeedbackType] = None
    severity: Optional[Severity] = None
    status: Optional[LearningStatus] = None
    ai_extracted: Optional[bool] = None
    applied_to_claude_md: Optional[bool] = None
    applied_to_decomposition: Optional[bool] = None
    pr_number: Optional[int] = None
    from_date: Optional[date] = None
    to_date: Optional[date] = None
    search: Optional[str] = Field(None, description="Search in comments and patterns")

    model_config = ConfigDict(use_enum_values=True)


class HintFilterParams(BaseModel):
    """Schema for filtering decomposition hints."""

    hint_type: Optional[HintType] = None
    category: Optional[HintCategory] = None
    status: Optional[HintStatus] = None
    ai_generated: Optional[bool] = None
    human_verified: Optional[bool] = None
    min_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    min_effectiveness: Optional[float] = Field(None, ge=0.0, le=1.0)
    applies_to: Optional[str] = None  # Single value to filter
    language: Optional[str] = None  # Single value to filter
    framework: Optional[str] = None  # Single value to filter
    search: Optional[str] = Field(None, description="Search in title/description")

    model_config = ConfigDict(use_enum_values=True)


class AggregationFilterParams(BaseModel):
    """Schema for filtering learning aggregations."""

    period_type: Optional[AggregationPeriod] = None
    status: Optional[AggregationStatus] = None
    has_suggestions: Optional[bool] = None
    from_date: Optional[date] = None
    to_date: Optional[date] = None

    model_config = ConfigDict(use_enum_values=True)


# =========================================================================
# Bulk Operation Schemas
# =========================================================================


class BulkLearningStatusUpdate(BaseModel):
    """Schema for bulk updating learning status."""

    learning_ids: list[UUID] = Field(..., min_length=1, description="Learning IDs")
    status: LearningStatus = Field(..., description="New status")

    model_config = ConfigDict(use_enum_values=True)


class BulkHintStatusUpdate(BaseModel):
    """Schema for bulk updating hint status."""

    hint_ids: list[UUID] = Field(..., min_length=1, description="Hint IDs")
    status: HintStatus = Field(..., description="New status")
    deprecated_reason: Optional[str] = Field(
        None, description="Reason (if deprecating)"
    )

    model_config = ConfigDict(use_enum_values=True)


# =========================================================================
# Analysis & Report Schemas
# =========================================================================


class LearningAnalysisRequest(BaseModel):
    """Schema for requesting learning analysis."""

    period_type: AggregationPeriod = Field(
        AggregationPeriod.MONTHLY, description="Analysis period"
    )
    include_suggestions: bool = Field(True, description="Generate suggestions")

    model_config = ConfigDict(use_enum_values=True)


class LearningAnalysisResponse(BaseModel):
    """Schema for learning analysis results."""

    project_id: UUID
    period_type: str
    period_start: date
    period_end: date
    total_learnings: int
    stats: PRLearningStats
    trends: dict[str, Any]  # Week-over-week or month-over-month trends
    top_issues: list[dict[str, Any]]  # Most common issues
    improvement_suggestions: list[str]  # AI-generated suggestions
    analysis_model: str
    analysis_time_ms: int


class CLAUDEMdSuggestion(BaseModel):
    """Schema for CLAUDE.md update suggestion."""

    section: str = Field(..., description="Section to update")
    content: str = Field(..., description="Suggested content")
    reason: str = Field(..., description="Why this should be added")
    source_learnings: list[UUID] = Field(..., description="Source learning IDs")
    priority: str = Field(..., description="Priority: high, medium, low")


class CLAUDEMdUpdateRequest(BaseModel):
    """Schema for applying CLAUDE.md suggestions."""

    suggestions_to_apply: list[UUID] = Field(
        ..., description="Suggestion IDs to apply"
    )
    custom_edits: Optional[dict[str, str]] = Field(
        None, description="Custom edits per section"
    )
    commit_message: Optional[str] = Field(None, description="Custom commit message")
