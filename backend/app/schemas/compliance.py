"""
Compliance Validation Schemas - Sprint 123 (SPEC-0013)

Version: 1.0.0
Date: January 30, 2026
Status: ACTIVE - Sprint 123
Authority: CTO Approved (A+ Grade, 98/100)
Reference: SPEC-0013 Compliance Validation Service

Schemas for:
- Compliance Score API requests/responses
- Compliance Issue details
- Folder Collision detection
- Quick score lookup
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


# =============================================================================
# Enums (mirroring model enums for API layer)
# =============================================================================


class IssueSeverity(str, Enum):
    """Issue severity levels."""

    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class ComplianceCategory(str, Enum):
    """Compliance validation categories (10 categories × 10 points = 100 max)."""

    DOCUMENTATION_STRUCTURE = "documentation_structure"
    SPECIFICATIONS_MANAGEMENT = "specifications_management"
    CLAUDE_AGENTS_MD = "claude_agents_md"
    SASE_ARTIFACTS = "sase_artifacts"
    CODE_FILE_NAMING = "code_file_naming"
    MIGRATION_TRACKING = "migration_tracking"
    FRAMEWORK_ALIGNMENT = "framework_alignment"
    TEAM_ORGANIZATION = "team_organization"
    LEGACY_ARCHIVAL = "legacy_archival"
    GOVERNANCE_DOCUMENTATION = "governance_documentation"


# =============================================================================
# Compliance Issue Schemas
# =============================================================================


class ComplianceIssueBase(BaseModel):
    """Base schema for compliance issue."""

    category: ComplianceCategory
    severity: IssueSeverity
    issue_code: str = Field(..., max_length=50, description="Issue code: DUPLICATE_STAGE_FOLDER, etc.")
    message: str = Field(..., description="Human-readable issue message")
    file_path: Optional[str] = Field(None, max_length=500, description="Relative file path")
    line_number: Optional[int] = Field(None, ge=1, description="Line number if applicable")
    fix_suggestion: Optional[str] = Field(None, description="Suggested fix for the issue")
    fix_command: Optional[str] = Field(None, max_length=500, description="CLI command: sdlcctl fix --xxx")
    auto_fixable: bool = Field(False, description="Whether issue can be auto-fixed")


class ComplianceIssueResponse(ComplianceIssueBase):
    """Compliance issue response schema."""

    id: UUID
    score_id: UUID
    context: Optional[dict] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# Category Result Schemas
# =============================================================================


class CategoryResultResponse(BaseModel):
    """Result for single compliance category."""

    name: ComplianceCategory
    score: int = Field(..., ge=0, le=10, description="Category score (0-10)")
    max_score: int = Field(10, description="Maximum possible score")
    issues: list[ComplianceIssueBase] = Field(default_factory=list, description="Issues in this category")
    passed_checks: list[str] = Field(default_factory=list, description="Checks that passed")


class IssuesSummary(BaseModel):
    """Summary of all issues found."""

    total: int = Field(..., ge=0, description="Total issues count")
    critical: int = Field(..., ge=0, description="Critical issues count")
    warning: int = Field(..., ge=0, description="Warning issues count")
    info: int = Field(..., ge=0, description="Info issues count")


# =============================================================================
# Compliance Score Schemas
# =============================================================================


class ComplianceScoreRequest(BaseModel):
    """Request schema for compliance validation."""

    include_categories: Optional[list[ComplianceCategory]] = Field(
        None, description="Only check these categories (optional)"
    )
    exclude_categories: Optional[list[ComplianceCategory]] = Field(
        None, description="Skip these categories (optional)"
    )
    force_refresh: bool = Field(False, description="Bypass cache and recalculate")


class ComplianceScoreResponse(BaseModel):
    """Full compliance score response."""

    project_id: UUID
    overall_score: int = Field(..., ge=0, le=100, description="Overall compliance score (0-100)")
    categories: list[CategoryResultResponse] = Field(..., description="Category breakdown")
    summary: IssuesSummary = Field(..., description="Issues summary")
    recommendations: list[str] = Field(default_factory=list, description="Improvement recommendations")
    generated_at: datetime = Field(..., description="Score calculation timestamp")
    framework_version: str = Field("6.0.5", description="SDLC Framework version")
    validation_version: str = Field("1.0.0", description="Validator version")
    scan_duration_ms: Optional[int] = Field(None, description="Scan duration in milliseconds")
    files_scanned: Optional[int] = Field(None, description="Number of files scanned")
    is_cached: bool = Field(False, description="Whether result is from cache")

    model_config = ConfigDict(from_attributes=True)


class QuickScoreResponse(BaseModel):
    """Quick score response for badges/dashboards."""

    project_id: UUID
    score: int = Field(..., ge=0, le=100, description="Overall compliance score")
    last_calculated: datetime = Field(..., description="Last calculation timestamp")
    is_cached: bool = Field(True, description="Whether result is from cache")
    framework_version: str = Field("6.0.5", description="SDLC Framework version")

    model_config = ConfigDict(from_attributes=True)


class ComplianceHistoryItem(BaseModel):
    """Single item in compliance history."""

    id: UUID
    overall_score: int
    calculated_at: datetime
    issues_summary: IssuesSummary
    framework_version: str

    model_config = ConfigDict(from_attributes=True)


class ComplianceHistoryResponse(BaseModel):
    """Compliance score history for a project."""

    project_id: UUID
    history: list[ComplianceHistoryItem]
    total_count: int


# =============================================================================
# Folder Collision Schemas
# =============================================================================


class FolderCollision(BaseModel):
    """Single folder collision."""

    stage_prefix: str = Field(..., description="Stage prefix: 00, 01, 02, etc.")
    stage_name: str = Field(..., description="Stage name: discover, planning, design, etc.")
    folders: list[str] = Field(..., description="Conflicting folder names")
    severity: IssueSeverity = Field(IssueSeverity.CRITICAL, description="Collision severity")
    fix_suggestion: str = Field(..., description="Suggested fix command")


class DuplicateDetectionRequest(BaseModel):
    """Request schema for duplicate folder detection."""

    docs_path: str = Field("docs/", description="Path to docs folder")


class DuplicateDetectionResponse(BaseModel):
    """Duplicate folder detection response."""

    project_id: UUID
    valid: bool = Field(..., description="True if no collisions found")
    collisions: list[FolderCollision] = Field(default_factory=list, description="Detected collisions")
    gaps: list[str] = Field(default_factory=list, description="Missing stage folders")
    extras: list[str] = Field(default_factory=list, description="Non-standard folders")
    checked_at: datetime = Field(..., description="Check timestamp")
    docs_path: str = Field("docs/", description="Docs folder path checked")
    total_folders: Optional[int] = Field(None, description="Total folders scanned")

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# Batch Validation Schemas
# =============================================================================


class BatchValidationRequest(BaseModel):
    """Request for batch validation of multiple projects."""

    project_ids: list[UUID] = Field(..., min_length=1, max_length=50, description="Projects to validate")
    include_categories: Optional[list[ComplianceCategory]] = None
    force_refresh: bool = False


class BatchValidationResultItem(BaseModel):
    """Single result in batch validation."""

    project_id: UUID
    project_name: str
    overall_score: int
    critical_issues: int
    status: str = Field(..., description="success, error, skipped")
    error_message: Optional[str] = None


class BatchValidationResponse(BaseModel):
    """Batch validation response."""

    total_projects: int
    successful: int
    failed: int
    results: list[BatchValidationResultItem]
    started_at: datetime
    completed_at: datetime
    duration_ms: int


# =============================================================================
# Issue Code Reference
# =============================================================================

# Common issue codes for documentation and type hints
ISSUE_CODES = {
    # Documentation Structure (10 codes)
    "DUPLICATE_STAGE_FOLDER": "Multiple folders with same stage prefix",
    "MISSING_STAGE_FOLDER": "Required stage folder not found",
    "INVALID_STAGE_NUMBERING": "Stage folder numbering incorrect",
    "EXTRA_ROOT_FOLDER": "Non-standard folder in docs root",
    # Specifications Management (10 codes)
    "MISSING_YAML_FRONTMATTER": "Spec file missing YAML frontmatter",
    "INVALID_SPEC_ID": "SPEC-XXXX ID format invalid",
    "MISSING_SPEC_VERSION": "Spec missing version field",
    "MISSING_SPEC_STATUS": "Spec missing status field",
    "SPEC_WRONG_LOCATION": "Spec not in docs/02-design/14-Technical-Specs/",
    # CLAUDE.md / AGENTS.md (8 codes)
    "MISSING_CLAUDE_MD": "CLAUDE.md not found in project root",
    "MISSING_AGENTS_MD": "AGENTS.md not found in project root",
    "OUTDATED_FRAMEWORK_VERSION": "Framework version reference outdated",
    "MISSING_REQUIRED_SECTION": "Required section missing in CLAUDE.md",
    # Code File Naming (6 codes)
    "PYTHON_NOT_SNAKE_CASE": "Python file not snake_case",
    "TS_COMPONENT_NOT_PASCAL_CASE": "React component not PascalCase",
    "TS_FILE_NOT_CAMEL_CASE": "TypeScript file not camelCase",
    "FILE_NAME_TOO_LONG": "File name exceeds 50 characters",
    # Other categories (abbreviated)
    "MISSING_SASE_ARTIFACT": "Required SASE artifact not found",
    "MIGRATION_DEADLINE_EXCEEDED": "Migration deadline exceeded",
    "FRAMEWORK_MISMATCH": "Framework version mismatch",
    "MISSING_TEAM_HUB": "SDLC Compliance Hub folder not found",
    "IMPROPER_LEGACY_ARCHIVAL": "Legacy files not properly archived",
    "MISSING_CTO_APPROVAL": "CTO approval document not found",
}
