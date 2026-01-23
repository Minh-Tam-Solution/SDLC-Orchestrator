"""
=========================================================================
Planning Sub-agent Schemas - Pydantic Models for Agentic Planning
SDLC Orchestrator - Sprint 98 (Planning Sub-agent Implementation Part 1)

Version: 1.0.0
Date: January 22, 2026
Status: ACTIVE - Sprint 98 Implementation
Authority: Backend Lead + CTO Approved
Reference: ADR-034-Planning-Subagent-Orchestration
Reference: SDLC 5.2.0 AI Agent Best Practices (Planning Mode)

Purpose:
- API request/response validation for Planning Orchestrator
- Pattern extraction schemas (Agentic Grep)
- ADR and Test pattern scanner schemas
- Conformance check and plan generation schemas

Key Insight (Expert Workflow):
- "Agentic grep > RAG for context retrieval"
- MANDATORY Planning Mode for changes >15 LOC
- Prevents architectural drift

Zero Mock Policy: Production-ready Pydantic v2 models
=========================================================================
"""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


# =========================================================================
# Enums
# =========================================================================

class ExploreAgentType(str, Enum):
    """Type of explore sub-agent."""
    SIMILAR_IMPLEMENTATIONS = "similar_implementations"  # Find similar code
    ADR_PATTERNS = "adr_patterns"  # Find related ADRs
    TEST_PATTERNS = "test_patterns"  # Find test patterns
    CODE_CONVENTIONS = "code_conventions"  # Find coding conventions


class PatternCategory(str, Enum):
    """Category of extracted pattern."""
    ARCHITECTURE = "architecture"  # System design patterns
    CODE_STYLE = "code_style"  # Naming, formatting
    ERROR_HANDLING = "error_handling"  # Exception patterns
    TESTING = "testing"  # Test patterns
    SECURITY = "security"  # Security patterns
    PERFORMANCE = "performance"  # Performance patterns
    API_DESIGN = "api_design"  # API conventions
    DATABASE = "database"  # DB patterns
    DOCUMENTATION = "documentation"  # Doc patterns


class ConformanceLevel(str, Enum):
    """Conformance check result level."""
    EXCELLENT = "excellent"  # 90-100: Fully aligned
    GOOD = "good"  # 70-89: Minor deviations
    FAIR = "fair"  # 50-69: Some deviations
    POOR = "poor"  # 0-49: Major deviations


class PlanningStatus(str, Enum):
    """Status of planning request."""
    PENDING = "pending"  # Waiting to start
    EXPLORING = "exploring"  # Sub-agents running
    SYNTHESIZING = "synthesizing"  # Merging patterns
    GENERATING = "generating"  # Creating plan
    AWAITING_APPROVAL = "awaiting_approval"  # Human approval needed
    APPROVED = "approved"  # Plan approved
    REJECTED = "rejected"  # Plan rejected
    EXECUTING = "executing"  # Implementation in progress
    COMPLETED = "completed"  # Done
    FAILED = "failed"  # Error occurred


# =========================================================================
# Pattern Extraction Schemas
# =========================================================================

class ExtractedPattern(BaseModel):
    """
    Single extracted pattern from codebase.

    Represents a convention, pattern, or practice found in existing code.
    """
    id: str = Field(..., description="Unique pattern identifier")
    category: PatternCategory = Field(..., description="Pattern category")
    name: str = Field(..., min_length=3, max_length=200, description="Pattern name")
    description: str = Field(..., max_length=2000, description="Pattern description")
    source_file: str = Field(..., description="File where pattern was found")
    source_line: Optional[int] = Field(None, description="Line number in source")
    code_snippet: Optional[str] = Field(
        None,
        max_length=5000,
        description="Code example of the pattern"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score (0-1)"
    )
    occurrences: int = Field(
        1,
        ge=1,
        description="Number of times pattern found"
    )
    related_files: list[str] = Field(
        default_factory=list,
        description="Other files using this pattern"
    )

    model_config = ConfigDict(from_attributes=True)


class PatternSummary(BaseModel):
    """
    Summary of all patterns extracted by sub-agents.

    Aggregated view of patterns for plan generation.
    """
    patterns: list[ExtractedPattern] = Field(
        default_factory=list,
        description="All extracted patterns"
    )
    total_files_scanned: int = Field(0, description="Files scanned")
    total_patterns_found: int = Field(0, description="Patterns found")
    categories: dict[str, int] = Field(
        default_factory=dict,
        description="Pattern count by category"
    )
    top_patterns: list[str] = Field(
        default_factory=list,
        max_length=10,
        description="Top patterns by occurrences"
    )
    conventions_detected: dict[str, str] = Field(
        default_factory=dict,
        description="Detected conventions (key: type, value: convention)"
    )

    model_config = ConfigDict(from_attributes=True)


# =========================================================================
# Explore Sub-agent Schemas
# =========================================================================

class ExploreAgentConfig(BaseModel):
    """Configuration for an explore sub-agent."""
    agent_type: ExploreAgentType = Field(..., description="Agent type")
    search_depth: int = Field(3, ge=1, le=10, description="Search depth")
    max_files: int = Field(100, ge=10, le=1000, description="Max files to scan")
    timeout_seconds: int = Field(60, ge=10, le=300, description="Timeout")
    include_patterns: list[str] = Field(
        default_factory=lambda: ["*.py", "*.ts", "*.tsx", "*.md"],
        description="Glob patterns to include"
    )
    exclude_patterns: list[str] = Field(
        default_factory=lambda: ["node_modules/*", "*.pyc", "__pycache__/*", ".git/*"],
        description="Glob patterns to exclude"
    )

    model_config = ConfigDict(from_attributes=True)


class ExploreResult(BaseModel):
    """
    Result from a single explore sub-agent.

    Each sub-agent returns its findings independently.
    """
    agent_type: ExploreAgentType = Field(..., description="Agent type")
    status: str = Field("completed", description="Execution status")
    patterns: list[ExtractedPattern] = Field(
        default_factory=list,
        description="Patterns found"
    )
    files_searched: int = Field(0, description="Files searched")
    files_relevant: int = Field(0, description="Relevant files found")
    execution_time_ms: int = Field(0, description="Execution time in ms")
    search_queries: list[str] = Field(
        default_factory=list,
        description="Search queries used"
    )
    errors: list[str] = Field(
        default_factory=list,
        description="Any errors encountered"
    )

    model_config = ConfigDict(from_attributes=True)


# =========================================================================
# ADR Scanner Schemas
# =========================================================================

class ADRReference(BaseModel):
    """Reference to an Architecture Decision Record."""
    id: str = Field(..., description="ADR ID (e.g., ADR-034)")
    title: str = Field(..., description="ADR title")
    status: str = Field(..., description="ADR status (accepted, deprecated, etc)")
    file_path: str = Field(..., description="Path to ADR file")
    summary: str = Field(..., max_length=1000, description="ADR summary")
    decision: str = Field(..., max_length=2000, description="The decision made")
    consequences: list[str] = Field(
        default_factory=list,
        description="Consequences of the decision"
    )
    relevance_score: float = Field(
        0.0,
        ge=0.0,
        le=1.0,
        description="Relevance to current task"
    )

    model_config = ConfigDict(from_attributes=True)


class ADRScanResult(BaseModel):
    """Result from ADR scanner."""
    related_adrs: list[ADRReference] = Field(
        default_factory=list,
        description="Related ADRs found"
    )
    total_adrs_scanned: int = Field(0, description="Total ADRs scanned")
    conventions_from_adrs: dict[str, str] = Field(
        default_factory=dict,
        description="Conventions extracted from ADRs"
    )
    required_patterns: list[str] = Field(
        default_factory=list,
        description="Patterns required by ADRs"
    )

    model_config = ConfigDict(from_attributes=True)


# =========================================================================
# Test Pattern Schemas
# =========================================================================

class TestPattern(BaseModel):
    """Test pattern extracted from existing tests."""
    name: str = Field(..., description="Pattern name")
    pattern_type: str = Field(
        ...,
        description="Type: unit, integration, e2e, fixture, mock"
    )
    description: str = Field(..., max_length=1000, description="Description")
    example_file: str = Field(..., description="Example test file")
    code_example: Optional[str] = Field(
        None,
        max_length=3000,
        description="Code example"
    )
    frameworks_used: list[str] = Field(
        default_factory=list,
        description="Test frameworks (pytest, vitest, etc)"
    )

    model_config = ConfigDict(from_attributes=True)


class TestPatternResult(BaseModel):
    """Result from test pattern scanner."""
    patterns: list[TestPattern] = Field(
        default_factory=list,
        description="Test patterns found"
    )
    test_files_scanned: int = Field(0, description="Test files scanned")
    coverage_conventions: dict[str, Any] = Field(
        default_factory=dict,
        description="Coverage conventions detected"
    )
    test_structure: dict[str, str] = Field(
        default_factory=dict,
        description="Test directory structure conventions"
    )

    model_config = ConfigDict(from_attributes=True)


# =========================================================================
# Implementation Plan Schemas
# =========================================================================

class ImplementationStep(BaseModel):
    """Single step in the implementation plan."""
    order: int = Field(..., ge=1, description="Step order")
    title: str = Field(..., min_length=5, max_length=200, description="Step title")
    description: str = Field(..., max_length=2000, description="Detailed description")
    files_to_create: list[str] = Field(
        default_factory=list,
        description="New files to create"
    )
    files_to_modify: list[str] = Field(
        default_factory=list,
        description="Existing files to modify"
    )
    patterns_to_follow: list[str] = Field(
        default_factory=list,
        description="Patterns to follow (by ID)"
    )
    estimated_loc: int = Field(
        0,
        ge=0,
        description="Estimated lines of code"
    )
    estimated_hours: float = Field(
        0.0,
        ge=0.0,
        description="Estimated hours"
    )
    dependencies: list[int] = Field(
        default_factory=list,
        description="Dependent step orders"
    )
    tests_required: list[str] = Field(
        default_factory=list,
        description="Tests to write"
    )

    model_config = ConfigDict(from_attributes=True)


class ImplementationPlan(BaseModel):
    """
    Complete implementation plan generated from patterns.

    This is what the human reviews and approves.
    """
    id: UUID = Field(..., description="Plan UUID")
    task: str = Field(..., description="Original task description")
    summary: str = Field(..., max_length=2000, description="Plan summary")
    steps: list[ImplementationStep] = Field(
        default_factory=list,
        description="Implementation steps"
    )
    total_estimated_loc: int = Field(0, description="Total estimated LOC")
    total_estimated_hours: float = Field(0.0, description="Total estimated hours")
    files_to_create: list[str] = Field(
        default_factory=list,
        description="All new files"
    )
    files_to_modify: list[str] = Field(
        default_factory=list,
        description="All files to modify"
    )
    patterns_applied: list[str] = Field(
        default_factory=list,
        description="Patterns applied (by name)"
    )
    adrs_referenced: list[str] = Field(
        default_factory=list,
        description="ADRs referenced"
    )
    new_patterns_introduced: list[str] = Field(
        default_factory=list,
        description="New patterns (may need ADR)"
    )
    risks: list[str] = Field(
        default_factory=list,
        description="Identified risks"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Creation timestamp"
    )

    model_config = ConfigDict(from_attributes=True)


# =========================================================================
# Conformance Check Schemas
# =========================================================================

class ConformanceDeviation(BaseModel):
    """Single deviation from established patterns."""
    pattern_id: str = Field(..., description="Pattern ID that was violated")
    pattern_name: str = Field(..., description="Pattern name")
    description: str = Field(..., description="What deviated")
    severity: str = Field(
        "medium",
        description="Severity: low, medium, high"
    )
    file_path: Optional[str] = Field(None, description="File with deviation")
    line_number: Optional[int] = Field(None, description="Line number")
    suggestion: str = Field(..., description="How to fix")

    model_config = ConfigDict(from_attributes=True)


class ConformanceResult(BaseModel):
    """
    Result of conformance check against patterns.

    Used for plan validation and CI/CD gate.
    """
    score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Conformance score (0-100)"
    )
    level: ConformanceLevel = Field(..., description="Conformance level")
    deviations: list[ConformanceDeviation] = Field(
        default_factory=list,
        description="List of deviations"
    )
    recommendations: list[str] = Field(
        default_factory=list,
        description="Recommendations for improvement"
    )
    requires_adr: bool = Field(
        False,
        description="True if new pattern needs ADR"
    )
    new_patterns_detected: list[str] = Field(
        default_factory=list,
        description="New patterns that may need documentation"
    )
    checked_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Check timestamp"
    )

    model_config = ConfigDict(from_attributes=True)


# =========================================================================
# Planning Request/Response Schemas
# =========================================================================

class PlanningRequest(BaseModel):
    """
    Request to start planning mode.

    Used by `sdlcctl plan` command and API.
    """
    task: str = Field(
        ...,
        min_length=10,
        max_length=2000,
        description="Task description (e.g., 'Add OAuth2 authentication')"
    )
    project_path: str = Field(
        ".",
        description="Project root path"
    )
    depth: int = Field(
        3,
        ge=1,
        le=10,
        description="Search depth for pattern extraction"
    )
    auto_approve: bool = Field(
        False,
        description="Skip human approval (not recommended)"
    )
    include_tests: bool = Field(
        True,
        description="Include test patterns in analysis"
    )
    include_adrs: bool = Field(
        True,
        description="Include ADR analysis"
    )
    custom_patterns: list[str] = Field(
        default_factory=list,
        description="Additional patterns to look for"
    )
    exclude_paths: list[str] = Field(
        default_factory=list,
        description="Paths to exclude from search"
    )

    @field_validator("task")
    @classmethod
    def validate_task(cls, v: str) -> str:
        """Ensure task is meaningful."""
        if len(v.split()) < 3:
            raise ValueError("Task description too short. Please provide more detail.")
        return v.strip()

    model_config = ConfigDict(from_attributes=True)


class PlanningResult(BaseModel):
    """
    Complete result of planning mode.

    Returned to user for review and approval.
    """
    id: UUID = Field(..., description="Planning session UUID")
    task: str = Field(..., description="Original task")
    status: PlanningStatus = Field(..., description="Current status")

    # Exploration results
    explore_results: list[ExploreResult] = Field(
        default_factory=list,
        description="Results from all sub-agents"
    )
    patterns: PatternSummary = Field(
        default_factory=PatternSummary,
        description="Synthesized patterns"
    )
    adr_scan: Optional[ADRScanResult] = Field(
        None,
        description="ADR scan results"
    )
    test_patterns: Optional[TestPatternResult] = Field(
        None,
        description="Test pattern results"
    )

    # Generated plan
    plan: Optional[ImplementationPlan] = Field(
        None,
        description="Generated implementation plan"
    )

    # Conformance
    conformance: Optional[ConformanceResult] = Field(
        None,
        description="Conformance check result"
    )

    # Metadata
    requires_approval: bool = Field(
        True,
        description="Whether human approval is needed"
    )
    execution_time_ms: int = Field(0, description="Total execution time")
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Creation timestamp"
    )
    approved_at: Optional[datetime] = Field(None, description="Approval timestamp")
    approved_by: Optional[UUID] = Field(None, description="Approver UUID")
    rejection_reason: Optional[str] = Field(None, description="If rejected, why")

    model_config = ConfigDict(from_attributes=True)


class PlanApprovalRequest(BaseModel):
    """Request to approve or reject a plan."""
    planning_id: UUID = Field(..., description="Planning session UUID")
    approved: bool = Field(..., description="True to approve, False to reject")
    notes: Optional[str] = Field(
        None,
        max_length=2000,
        description="Approval/rejection notes"
    )
    modifications: Optional[dict[str, Any]] = Field(
        None,
        description="Modifications to apply before approval"
    )

    model_config = ConfigDict(from_attributes=True)


class PlanApprovalResponse(BaseModel):
    """Response after plan approval/rejection."""
    planning_id: UUID = Field(..., description="Planning session UUID")
    status: PlanningStatus = Field(..., description="New status")
    message: str = Field(..., description="Result message")
    next_steps: list[str] = Field(
        default_factory=list,
        description="Next steps for implementation"
    )

    model_config = ConfigDict(from_attributes=True)


# =========================================================================
# CLI Output Schemas
# =========================================================================

class PlanningCLIOutput(BaseModel):
    """
    Formatted output for CLI display.

    Used by `sdlcctl plan` to display results.
    """
    task: str = Field(..., description="Task description")
    status: str = Field(..., description="Status indicator")

    # Summary
    patterns_found: int = Field(0, description="Number of patterns found")
    adrs_referenced: int = Field(0, description="Number of ADRs referenced")
    test_patterns: int = Field(0, description="Number of test patterns")

    # Plan summary
    steps_count: int = Field(0, description="Number of implementation steps")
    estimated_loc: int = Field(0, description="Estimated lines of code")
    estimated_hours: float = Field(0.0, description="Estimated hours")
    files_to_create: list[str] = Field(default_factory=list)
    files_to_modify: list[str] = Field(default_factory=list)

    # Conformance
    conformance_score: int = Field(0, description="Conformance score")
    conformance_level: str = Field("unknown", description="Conformance level")
    deviations_count: int = Field(0, description="Number of deviations")

    # Warnings/Recommendations
    warnings: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


# =========================================================================
# GitHub Check Schemas (for CI/CD integration)
# =========================================================================

class ConformanceCheckRequest(BaseModel):
    """Request for CI/CD conformance check."""
    pr_diff_url: str = Field(..., description="GitHub PR diff URL")
    project_path: str = Field(".", description="Project root path")
    fail_threshold: int = Field(
        70,
        ge=0,
        le=100,
        description="Minimum score to pass"
    )

    model_config = ConfigDict(from_attributes=True)


class ConformanceCheckResponse(BaseModel):
    """Response for CI/CD conformance check."""
    passed: bool = Field(..., description="Whether check passed")
    score: int = Field(..., ge=0, le=100, description="Conformance score")
    threshold: int = Field(..., description="Required threshold")
    deviations: list[ConformanceDeviation] = Field(
        default_factory=list,
        description="Deviations found"
    )
    summary: str = Field(..., description="Human-readable summary")
    details_url: Optional[str] = Field(
        None,
        description="URL to detailed report"
    )

    model_config = ConfigDict(from_attributes=True)
