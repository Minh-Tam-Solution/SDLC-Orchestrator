"""
=========================================================================
Planning Hierarchy Schemas - Pydantic Models for API Validation
SDLC Orchestrator - Sprint 74 (Planning Hierarchy)

Version: 1.0.0
Date: January 18, 2026
Status: ACTIVE - Sprint 74 Implementation
Authority: Backend Lead + CTO Approved
Reference: ADR-013-Planning-Hierarchy
Reference: SDLC-Sprint-Planning-Governance.md (SDLC 5.1.3)

Purpose:
- API request/response validation for Roadmaps, Phases, Sprints, BacklogItems
- G-Sprint/G-Sprint-Close gate evaluation schemas
- Sprint governance checklist validation

SDLC 5.1.3 Alignment:
- G-Sprint Gate (Sprint Planning validation)
- G-Sprint-Close Gate (Sprint Completion validation)
- 10 Golden Rules enforcement
- Traceability chain: Roadmap → Phase → Sprint → Backlog

Zero Mock Policy: Production-ready Pydantic v2 models
=========================================================================
"""

from datetime import date, datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


# =========================================================================
# Enums
# =========================================================================

class RoadmapStatus(str, Enum):
    """Roadmap lifecycle status."""
    DRAFT = "draft"           # Being prepared
    ACTIVE = "active"         # Current roadmap
    ARCHIVED = "archived"     # Historical

class ReviewCadence(str, Enum):
    """Roadmap review cadence (Rule #10: Quarterly Re-Approval)."""
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"   # Default per SDLC 5.1.3
    YEARLY = "yearly"

class PhaseStatus(str, Enum):
    """Phase lifecycle status."""
    PLANNED = "planned"       # Not yet started
    ACTIVE = "active"         # Currently in progress
    COMPLETED = "completed"   # Done

class SprintStatus(str, Enum):
    """Sprint lifecycle status."""
    PLANNING = "planning"     # Preparing sprint
    ACTIVE = "active"         # Sprint in progress
    COMPLETED = "completed"   # Sprint done
    CANCELLED = "cancelled"   # Sprint cancelled

class GateStatus(str, Enum):
    """Sprint gate evaluation status."""
    PENDING = "pending"       # Not yet evaluated
    PASSED = "passed"         # Gate passed
    FAILED = "failed"         # Gate failed

class GateType(str, Enum):
    """Sprint governance gate types (separate track from G0-G3)."""
    G_SPRINT = "g_sprint"             # Sprint Planning Gate
    G_SPRINT_CLOSE = "g_sprint_close" # Sprint Completion Gate

class BacklogItemType(str, Enum):
    """Backlog item type classification."""
    STORY = "story"           # User story
    TASK = "task"             # Technical task
    BUG = "bug"               # Bug fix
    SPIKE = "spike"           # Research/investigation

class BacklogItemStatus(str, Enum):
    """Backlog item workflow status."""
    TODO = "todo"             # Not started
    IN_PROGRESS = "in_progress"  # Being worked on
    REVIEW = "review"         # In review
    DONE = "done"             # Completed
    BLOCKED = "blocked"       # Blocked by dependency

class Priority(str, Enum):
    """Priority classification per SDLC 5.1.3 Rule #8."""
    P0 = "P0"                 # Must have (required for sprint goal)
    P1 = "P1"                 # Should have (high value)
    P2 = "P2"                 # Could have (nice to have)


# =========================================================================
# Roadmap Schemas
# =========================================================================

class RoadmapCreate(BaseModel):
    """Schema for creating a new roadmap."""
    project_id: UUID = Field(..., description="Parent project UUID")
    name: str = Field(
        ...,
        min_length=2,
        max_length=255,
        description="Roadmap name (e.g., '2026 Roadmap')",
        examples=["2026 Product Roadmap"]
    )
    description: Optional[str] = Field(
        None,
        max_length=2000,
        description="Detailed roadmap description"
    )
    vision: Optional[str] = Field(
        None,
        max_length=2000,
        description="Strategic vision for this roadmap"
    )
    start_date: Optional[date] = Field(
        None,
        description="Roadmap start date"
    )
    end_date: Optional[date] = Field(
        None,
        description="Roadmap end date"
    )
    review_cadence: ReviewCadence = Field(
        ReviewCadence.QUARTERLY,
        description="Review cadence per Rule #10 (Quarterly Re-Approval)"
    )

    @model_validator(mode="after")
    def validate_dates(self) -> "RoadmapCreate":
        """Validate that end_date is after start_date."""
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError("end_date must be after start_date")
        return self

    model_config = ConfigDict(from_attributes=True)


class RoadmapUpdate(BaseModel):
    """Schema for updating a roadmap."""
    name: Optional[str] = Field(
        None,
        min_length=2,
        max_length=255,
        description="Roadmap name"
    )
    description: Optional[str] = Field(
        None,
        max_length=2000,
        description="Detailed roadmap description"
    )
    vision: Optional[str] = Field(
        None,
        max_length=2000,
        description="Strategic vision"
    )
    start_date: Optional[date] = Field(
        None,
        description="Roadmap start date"
    )
    end_date: Optional[date] = Field(
        None,
        description="Roadmap end date"
    )
    review_cadence: Optional[ReviewCadence] = Field(
        None,
        description="Review cadence"
    )
    status: Optional[RoadmapStatus] = Field(
        None,
        description="Roadmap status"
    )

    model_config = ConfigDict(from_attributes=True)


class RoadmapResponse(BaseModel):
    """Schema for roadmap response."""
    id: UUID = Field(..., description="Roadmap UUID")
    project_id: UUID = Field(..., description="Parent project UUID")
    name: str = Field(..., description="Roadmap name")
    description: Optional[str] = Field(None, description="Description")
    vision: Optional[str] = Field(None, description="Strategic vision")
    start_date: Optional[date] = Field(None, description="Start date")
    end_date: Optional[date] = Field(None, description="End date")
    review_cadence: str = Field(..., description="Review cadence")
    status: str = Field(..., description="Roadmap status")
    phases_count: int = Field(0, description="Number of phases")
    created_by: Optional[UUID] = Field(None, description="Creator UUID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True)


class RoadmapListResponse(BaseModel):
    """Schema for paginated roadmap list."""
    items: list[RoadmapResponse] = Field(default_factory=list)
    total: int = Field(0, ge=0)
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
    has_next: bool = Field(False)

    model_config = ConfigDict(from_attributes=True)


# =========================================================================
# Phase Schemas
# =========================================================================

class PhaseCreate(BaseModel):
    """Schema for creating a new phase."""
    roadmap_id: UUID = Field(..., description="Parent roadmap UUID")
    number: int = Field(
        ...,
        ge=1,
        description="Phase number (sequential within roadmap)"
    )
    name: str = Field(
        ...,
        min_length=2,
        max_length=255,
        description="Phase name (e.g., 'Q1 Foundation')",
        examples=["Q1 2026: Core Infrastructure"]
    )
    theme: Optional[str] = Field(
        None,
        max_length=500,
        description="Phase theme (e.g., 'Foundation', 'Scale')"
    )
    objective: Optional[str] = Field(
        None,
        max_length=2000,
        description="Phase objective/goal"
    )
    start_date: Optional[date] = Field(
        None,
        description="Phase start date"
    )
    end_date: Optional[date] = Field(
        None,
        description="Phase end date"
    )

    @model_validator(mode="after")
    def validate_dates(self) -> "PhaseCreate":
        """Validate that end_date is after start_date."""
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError("end_date must be after start_date")
        return self

    model_config = ConfigDict(from_attributes=True)


class PhaseUpdate(BaseModel):
    """Schema for updating a phase."""
    name: Optional[str] = Field(
        None,
        min_length=2,
        max_length=255,
        description="Phase name"
    )
    theme: Optional[str] = Field(
        None,
        max_length=500,
        description="Phase theme"
    )
    objective: Optional[str] = Field(
        None,
        max_length=2000,
        description="Phase objective"
    )
    start_date: Optional[date] = Field(
        None,
        description="Phase start date"
    )
    end_date: Optional[date] = Field(
        None,
        description="Phase end date"
    )
    status: Optional[PhaseStatus] = Field(
        None,
        description="Phase status"
    )

    model_config = ConfigDict(from_attributes=True)


class PhaseResponse(BaseModel):
    """Schema for phase response."""
    id: UUID = Field(..., description="Phase UUID")
    roadmap_id: UUID = Field(..., description="Parent roadmap UUID")
    number: int = Field(..., description="Phase number")
    name: str = Field(..., description="Phase name")
    theme: Optional[str] = Field(None, description="Phase theme")
    objective: Optional[str] = Field(None, description="Phase objective")
    start_date: Optional[date] = Field(None, description="Start date")
    end_date: Optional[date] = Field(None, description="End date")
    status: str = Field(..., description="Phase status")
    sprints_count: int = Field(0, description="Number of sprints")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True)


class PhaseListResponse(BaseModel):
    """Schema for paginated phase list."""
    items: list[PhaseResponse] = Field(default_factory=list)
    total: int = Field(0, ge=0)
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
    has_next: bool = Field(False)

    model_config = ConfigDict(from_attributes=True)


# =========================================================================
# Sprint Schemas
# =========================================================================

class SprintCreate(BaseModel):
    """Schema for creating a new sprint."""
    project_id: UUID = Field(..., description="Project UUID (required)")
    phase_id: Optional[UUID] = Field(
        None,
        description="Parent phase UUID (optional, can be standalone)"
    )
    number: int = Field(
        ...,
        ge=1,
        description="Sprint number (Rule #1: Immutable)"
    )
    name: str = Field(
        ...,
        min_length=2,
        max_length=255,
        description="Sprint name (e.g., 'Sprint 74: Planning Hierarchy')",
        examples=["Sprint 74: Planning Hierarchy Implementation"]
    )
    goal: str = Field(
        ...,
        min_length=10,
        max_length=500,
        description="Sprint goal - single sentence (Rule #7)",
        examples=["Implement complete Planning Hierarchy with G-Sprint governance gates"]
    )
    start_date: Optional[date] = Field(
        None,
        description="Sprint start date"
    )
    end_date: Optional[date] = Field(
        None,
        description="Sprint end date"
    )
    capacity_points: Optional[int] = Field(
        None,
        ge=1,
        le=200,
        description="Team capacity in story points"
    )
    team_size: Optional[int] = Field(
        None,
        ge=1,
        le=20,
        description="Number of team members"
    )
    velocity_target: Optional[int] = Field(
        None,
        ge=1,
        le=200,
        description="Target velocity in story points"
    )

    @model_validator(mode="after")
    def validate_dates(self) -> "SprintCreate":
        """Validate that end_date is after start_date."""
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError("end_date must be after start_date")
        return self

    model_config = ConfigDict(from_attributes=True)


class SprintUpdate(BaseModel):
    """Schema for updating a sprint (name/goal cannot change after start)."""
    phase_id: Optional[UUID] = Field(
        None,
        description="Parent phase UUID"
    )
    name: Optional[str] = Field(
        None,
        min_length=2,
        max_length=255,
        description="Sprint name"
    )
    goal: Optional[str] = Field(
        None,
        min_length=10,
        max_length=500,
        description="Sprint goal"
    )
    start_date: Optional[date] = Field(
        None,
        description="Sprint start date"
    )
    end_date: Optional[date] = Field(
        None,
        description="Sprint end date"
    )
    capacity_points: Optional[int] = Field(
        None,
        ge=1,
        le=200,
        description="Team capacity"
    )
    team_size: Optional[int] = Field(
        None,
        ge=1,
        le=20,
        description="Team size"
    )
    velocity_target: Optional[int] = Field(
        None,
        ge=1,
        le=200,
        description="Target velocity"
    )
    status: Optional[SprintStatus] = Field(
        None,
        description="Sprint status"
    )

    model_config = ConfigDict(from_attributes=True)


class SprintGateInfo(BaseModel):
    """Embedded gate information in sprint response."""
    status: GateStatus = Field(..., description="Gate status")
    approved_by: Optional[UUID] = Field(None, description="Approver UUID")
    approved_at: Optional[datetime] = Field(None, description="Approval timestamp")

    model_config = ConfigDict(from_attributes=True)


class SprintResponse(BaseModel):
    """Schema for sprint response."""
    id: UUID = Field(..., description="Sprint UUID")
    project_id: UUID = Field(..., description="Project UUID")
    phase_id: Optional[UUID] = Field(None, description="Parent phase UUID")
    number: int = Field(..., description="Sprint number (immutable)")
    name: str = Field(..., description="Sprint name")
    goal: str = Field(..., description="Sprint goal")
    status: str = Field(..., description="Sprint status")
    start_date: Optional[date] = Field(None, description="Start date")
    end_date: Optional[date] = Field(None, description="End date")
    capacity_points: Optional[int] = Field(None, description="Capacity")
    team_size: Optional[int] = Field(None, description="Team size")
    velocity_target: Optional[int] = Field(None, description="Target velocity")

    # Gate status
    g_sprint_status: str = Field("pending", description="G-Sprint gate status")
    g_sprint_approved_by: Optional[UUID] = Field(None, description="G-Sprint approver")
    g_sprint_approved_at: Optional[datetime] = Field(None, description="G-Sprint approval time")
    g_sprint_close_status: str = Field("pending", description="G-Sprint-Close status")
    g_sprint_close_approved_by: Optional[UUID] = Field(None, description="G-Sprint-Close approver")
    g_sprint_close_approved_at: Optional[datetime] = Field(None, description="G-Sprint-Close approval time")
    documentation_deadline: Optional[datetime] = Field(None, description="24h documentation deadline")

    # Computed
    backlog_items_count: int = Field(0, description="Number of backlog items")
    can_start: bool = Field(False, description="Can sprint start (G-Sprint passed)")
    can_close: bool = Field(False, description="Can sprint close")
    documentation_overdue: bool = Field(False, description="Is documentation overdue")

    created_by: Optional[UUID] = Field(None, description="Creator UUID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True)


class SprintListResponse(BaseModel):
    """Schema for paginated sprint list."""
    items: list[SprintResponse] = Field(default_factory=list)
    total: int = Field(0, ge=0)
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
    has_next: bool = Field(False)

    model_config = ConfigDict(from_attributes=True)


# =========================================================================
# Sprint Gate Evaluation Schemas
# =========================================================================

class ChecklistItem(BaseModel):
    """Individual checklist item for gate evaluation."""
    id: str = Field(..., description="Unique item ID within category")
    label: str = Field(..., description="Display label")
    checked: bool = Field(False, description="Whether item is checked")
    notes: Optional[str] = Field(None, max_length=500, description="Optional notes")

    model_config = ConfigDict(from_attributes=True)


class ChecklistCategory(BaseModel):
    """Category of checklist items."""
    name: str = Field(..., description="Category name")
    items: list[ChecklistItem] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class GateEvaluationCreate(BaseModel):
    """Schema for creating a gate evaluation (auto-creates from template)."""
    sprint_id: UUID = Field(..., description="Sprint UUID")
    gate_type: GateType = Field(..., description="Gate type (g_sprint or g_sprint_close)")

    model_config = ConfigDict(from_attributes=True)


class GateEvaluationUpdate(BaseModel):
    """Schema for updating a gate evaluation (checklist items)."""
    checklist: dict[str, list[dict[str, Any]]] = Field(
        ...,
        description="Updated checklist with checked items"
    )
    notes: Optional[str] = Field(
        None,
        max_length=2000,
        description="Evaluation notes"
    )

    model_config = ConfigDict(from_attributes=True)


class GateEvaluationSubmit(BaseModel):
    """Schema for submitting a gate evaluation for approval."""
    notes: Optional[str] = Field(
        None,
        max_length=2000,
        description="Final evaluation notes"
    )

    model_config = ConfigDict(from_attributes=True)


class GateEvaluationResponse(BaseModel):
    """Schema for gate evaluation response."""
    id: UUID = Field(..., description="Evaluation UUID")
    sprint_id: UUID = Field(..., description="Sprint UUID")
    gate_type: str = Field(..., description="Gate type")
    status: str = Field(..., description="Evaluation status")
    checklist: dict[str, list[dict[str, Any]]] = Field(
        default_factory=dict,
        description="Checklist with items"
    )
    notes: Optional[str] = Field(None, description="Evaluation notes")
    evaluated_by: Optional[UUID] = Field(None, description="Evaluator UUID")
    evaluated_at: Optional[datetime] = Field(None, description="Evaluation timestamp")
    created_at: datetime = Field(..., description="Creation timestamp")

    # Computed
    all_items_checked: bool = Field(False, description="All checklist items passed")
    checked_count: int = Field(0, description="Number of checked items")
    total_count: int = Field(0, description="Total number of items")

    model_config = ConfigDict(from_attributes=True)


# =========================================================================
# Backlog Item Schemas
# =========================================================================

class BacklogItemCreate(BaseModel):
    """Schema for creating a backlog item."""
    project_id: UUID = Field(..., description="Project UUID (required)")
    sprint_id: Optional[UUID] = Field(
        None,
        description="Sprint UUID (null = product backlog)"
    )
    parent_id: Optional[UUID] = Field(
        None,
        description="Parent item UUID (for subtasks)"
    )
    type: BacklogItemType = Field(
        ...,
        description="Item type (story, task, bug, spike)"
    )
    title: str = Field(
        ...,
        min_length=5,
        max_length=500,
        description="Item title",
        examples=["As a user, I want to view my sprint backlog"]
    )
    description: Optional[str] = Field(
        None,
        max_length=5000,
        description="Detailed description"
    )
    acceptance_criteria: Optional[str] = Field(
        None,
        max_length=5000,
        description="Acceptance criteria for stories"
    )
    priority: Priority = Field(
        Priority.P2,
        description="Priority (P0=must, P1=should, P2=could)"
    )
    story_points: Optional[int] = Field(
        None,
        ge=1,
        le=21,
        description="Story points estimate (1-21)"
    )
    assignee_id: Optional[UUID] = Field(
        None,
        description="Assigned user UUID"
    )
    labels: list[str] = Field(
        default_factory=list,
        max_length=10,
        description="Labels/tags"
    )

    @field_validator("labels")
    @classmethod
    def validate_labels(cls, v: list[str]) -> list[str]:
        """Validate label format."""
        if v:
            for label in v:
                if len(label) > 50:
                    raise ValueError(f"Label '{label[:20]}...' exceeds 50 characters")
        return v

    model_config = ConfigDict(from_attributes=True)


class BacklogItemUpdate(BaseModel):
    """Schema for updating a backlog item."""
    sprint_id: Optional[UUID] = Field(
        None,
        description="Sprint UUID (set to move to sprint)"
    )
    parent_id: Optional[UUID] = Field(
        None,
        description="Parent item UUID"
    )
    type: Optional[BacklogItemType] = Field(
        None,
        description="Item type"
    )
    title: Optional[str] = Field(
        None,
        min_length=5,
        max_length=500,
        description="Item title"
    )
    description: Optional[str] = Field(
        None,
        max_length=5000,
        description="Detailed description"
    )
    acceptance_criteria: Optional[str] = Field(
        None,
        max_length=5000,
        description="Acceptance criteria"
    )
    priority: Optional[Priority] = Field(
        None,
        description="Priority"
    )
    story_points: Optional[int] = Field(
        None,
        ge=1,
        le=21,
        description="Story points"
    )
    status: Optional[BacklogItemStatus] = Field(
        None,
        description="Item status"
    )
    assignee_id: Optional[UUID] = Field(
        None,
        description="Assigned user UUID"
    )
    labels: Optional[list[str]] = Field(
        None,
        max_length=10,
        description="Labels/tags"
    )

    model_config = ConfigDict(from_attributes=True)


class BacklogItemResponse(BaseModel):
    """Schema for backlog item response."""
    id: UUID = Field(..., description="Item UUID")
    project_id: UUID = Field(..., description="Project UUID")
    sprint_id: Optional[UUID] = Field(None, description="Sprint UUID")
    parent_id: Optional[UUID] = Field(None, description="Parent item UUID")
    type: str = Field(..., description="Item type")
    title: str = Field(..., description="Item title")
    description: Optional[str] = Field(None, description="Description")
    acceptance_criteria: Optional[str] = Field(None, description="Acceptance criteria")
    priority: str = Field(..., description="Priority")
    story_points: Optional[int] = Field(None, description="Story points")
    status: str = Field(..., description="Item status")
    assignee_id: Optional[UUID] = Field(None, description="Assignee UUID")
    labels: list[str] = Field(default_factory=list, description="Labels")
    subtasks_count: int = Field(0, description="Number of subtasks")
    created_by: Optional[UUID] = Field(None, description="Creator UUID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True)


class BacklogItemListResponse(BaseModel):
    """Schema for paginated backlog item list."""
    items: list[BacklogItemResponse] = Field(default_factory=list)
    total: int = Field(0, ge=0)
    page: int = Field(1, ge=1)
    page_size: int = Field(50, ge=1, le=200)
    has_next: bool = Field(False)

    # Summary stats
    total_points: int = Field(0, description="Total story points")
    p0_count: int = Field(0, description="P0 items count")
    p1_count: int = Field(0, description="P1 items count")
    p2_count: int = Field(0, description="P2 items count")

    model_config = ConfigDict(from_attributes=True)


# =========================================================================
# Planning Hierarchy Overview Schemas
# =========================================================================

class SprintSummary(BaseModel):
    """Summary sprint info for hierarchy view."""
    id: UUID
    number: int
    name: str
    status: str
    g_sprint_status: str
    g_sprint_close_status: str
    backlog_items_count: int
    total_points: int
    start_date: Optional[date]
    end_date: Optional[date]

    model_config = ConfigDict(from_attributes=True)


class PhaseSummary(BaseModel):
    """Summary phase info for hierarchy view."""
    id: UUID
    number: int
    name: str
    status: str
    sprints_count: int
    sprints: list[SprintSummary] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class RoadmapHierarchy(BaseModel):
    """Full roadmap hierarchy for dashboard view."""
    id: UUID
    name: str
    status: str
    vision: Optional[str]
    start_date: Optional[date]
    end_date: Optional[date]
    phases: list[PhaseSummary] = Field(default_factory=list)
    total_sprints: int = Field(0)
    active_sprint: Optional[SprintSummary] = Field(None)

    model_config = ConfigDict(from_attributes=True)


class PlanningDashboard(BaseModel):
    """Planning hierarchy dashboard data."""
    project_id: UUID
    roadmaps: list[RoadmapHierarchy] = Field(default_factory=list)
    active_roadmap: Optional[RoadmapHierarchy] = Field(None)
    current_sprint: Optional[SprintResponse] = Field(None)
    backlog_stats: dict[str, int] = Field(
        default_factory=lambda: {
            "total": 0,
            "in_sprint": 0,
            "in_backlog": 0,
            "p0_count": 0,
            "p1_count": 0,
            "p2_count": 0,
        }
    )

    model_config = ConfigDict(from_attributes=True)


# =========================================================================
# Bulk Operation Schemas
# =========================================================================

class BulkMoveToSprint(BaseModel):
    """Schema for bulk moving items to a sprint."""
    item_ids: list[UUID] = Field(
        ...,
        min_length=1,
        max_length=50,
        description="List of backlog item UUIDs to move"
    )
    sprint_id: Optional[UUID] = Field(
        None,
        description="Target sprint UUID (null = move to backlog)"
    )

    model_config = ConfigDict(from_attributes=True)


class BulkUpdatePriority(BaseModel):
    """Schema for bulk priority update."""
    item_ids: list[UUID] = Field(
        ...,
        min_length=1,
        max_length=50,
        description="List of backlog item UUIDs"
    )
    priority: Priority = Field(
        ...,
        description="New priority for all items"
    )

    model_config = ConfigDict(from_attributes=True)


class BulkOperationResult(BaseModel):
    """Schema for bulk operation result."""
    success_count: int = Field(0, description="Number of successful operations")
    failure_count: int = Field(0, description="Number of failed operations")
    errors: list[dict] = Field(
        default_factory=list,
        description="List of errors with details"
    )

    model_config = ConfigDict(from_attributes=True)


# =========================================================================
# Sprint Analytics Schemas (Sprint 76 Day 5)
# =========================================================================

class VelocityMetricsResponse(BaseModel):
    """
    Velocity metrics from historical sprint data.

    Sprint 76: AI Sprint Assistant - Velocity calculation
    """
    average: float = Field(
        default=0.0,
        description="Average velocity in story points"
    )
    trend: str = Field(
        default="unknown",
        description="Trend: increasing, decreasing, stable, unknown"
    )
    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Confidence score (0-1) based on data availability"
    )
    history: list[int] = Field(
        default_factory=list,
        description="Velocity history from recent sprints"
    )
    sprint_count: int = Field(
        default=0,
        description="Number of sprints analyzed"
    )
    project_id: UUID = Field(description="Project UUID")

    model_config = ConfigDict(from_attributes=True)


class SprintHealthResponse(BaseModel):
    """
    Sprint health indicators.

    Sprint 76: AI Sprint Assistant - Health assessment
    """
    sprint_id: UUID = Field(description="Sprint UUID")
    completion_rate: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Completion percentage (0-100)"
    )
    completed_points: int = Field(default=0, description="Story points completed")
    total_points: int = Field(default=0, description="Total story points")
    blocked_count: int = Field(default=0, description="Number of blocked items")
    risk_level: str = Field(
        default="low",
        description="Risk level: low, medium, high"
    )
    days_remaining: int = Field(default=0, description="Days until sprint end")
    days_elapsed: int = Field(default=0, description="Days since sprint start")
    expected_completion: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Expected completion based on time elapsed"
    )

    model_config = ConfigDict(from_attributes=True)


class PrioritySuggestionResponse(BaseModel):
    """
    AI-powered prioritization suggestion.

    Sprint 76: AI Sprint Assistant - Backlog recommendations
    """
    type: str = Field(description="Suggestion type identifier")
    message: str = Field(description="Human-readable suggestion message")
    severity: str = Field(
        default="info",
        description="Severity: info, warning, error"
    )
    items: list[UUID] = Field(
        default_factory=list,
        description="Related backlog item UUIDs"
    )
    action: Optional[str] = Field(
        default=None,
        description="Recommended action"
    )

    model_config = ConfigDict(from_attributes=True)


class SprintSuggestionsResponse(BaseModel):
    """
    Sprint prioritization suggestions response.

    Sprint 76: AI Sprint Assistant - Recommendations
    """
    sprint_id: UUID = Field(description="Sprint UUID")
    suggestions: list[PrioritySuggestionResponse] = Field(
        default_factory=list,
        description="List of AI-generated suggestions"
    )
    suggestion_count: int = Field(
        default=0,
        description="Total number of suggestions"
    )

    model_config = ConfigDict(from_attributes=True)


class SprintAnalyticsResponse(BaseModel):
    """
    Comprehensive sprint analytics.

    Sprint 76: AI Sprint Assistant - Full analytics
    """
    sprint_id: UUID
    sprint_number: int
    sprint_name: str
    health: SprintHealthResponse
    velocity: VelocityMetricsResponse
    suggestions: list[PrioritySuggestionResponse]
    summary: str = Field(description="AI-generated status summary")

    model_config = ConfigDict(from_attributes=True)
