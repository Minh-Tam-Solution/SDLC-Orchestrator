"""
=========================================================================
MRP/VCR Schemas - SDLC Orchestrator
Sprint 152: MRP/VCR 5-Point Validation + Context Authority Integration

Version: 1.1.0
Date: February 3, 2026
Status: ACTIVE - Sprint 152 MRP Integration
Authority: Backend Lead + CTO Approved
Reference: docs/04-build/02-Sprint-Plans/CURRENT-SPRINT.md
Reference: SDLC 6.0.5 Framework - SASE Artifacts

Purpose:
- Define MRP (Merge Readiness Protocol) 5-point structure
- Define VCR (Verification Completion Report) schema
- Enable evidence validation and storage
- Integrate with Context Authority SSOT snapshots

MRP 5-Point Structure:
1. Test Evidence (coverage, pass/fail)
2. Lint Evidence (ruff, eslint)
3. Security Evidence (bandit, npm audit, grype)
4. Build Evidence (docker, package)
5. Conformance Evidence (pattern alignment, ADR)

Sprint 152 Additions:
- context_snapshot_id in ValidateMRPRequest and VCR
- context_validation_passed in MRPValidation
- Context Authority integration for SSOT validation

Zero Mock Policy: Production-ready Pydantic schemas
=========================================================================
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


# =========================================================================
# Enums
# =========================================================================

class MRPPointStatus(str, Enum):
    """Status for individual MRP evidence point."""
    PASSED = "PASSED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"      # Not required for tier
    NOT_AVAILABLE = "NOT_AVAILABLE"  # Required but not found
    IN_PROGRESS = "IN_PROGRESS"


class VCRVerdict(str, Enum):
    """Overall VCR verdict."""
    PASS = "PASS"
    FAIL = "FAIL"
    PENDING = "PENDING"
    BLOCKED = "BLOCKED"  # Blocked by CRP or other gate


class EvidenceSource(str, Enum):
    """Source of evidence collection."""
    GITHUB_ACTIONS = "GITHUB_ACTIONS"
    LOCAL_CLI = "LOCAL_CLI"
    JENKINS = "JENKINS"
    GITLAB_CI = "GITLAB_CI"
    MANUAL = "MANUAL"
    ORCHESTRATOR = "ORCHESTRATOR"


# =========================================================================
# Evidence Point Schemas
# =========================================================================

class BaseEvidencePoint(BaseModel):
    """Base schema for all evidence points."""
    status: MRPPointStatus = Field(
        ...,
        description="Pass/fail/skipped status for this evidence point",
    )
    message: str = Field(
        default="",
        description="Human-readable status message",
    )
    required: bool = Field(
        default=True,
        description="Whether this evidence point is required for the tier",
    )
    collected_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When evidence was collected",
    )
    source: EvidenceSource = Field(
        default=EvidenceSource.ORCHESTRATOR,
        description="Source of evidence collection",
    )
    details: dict = Field(
        default_factory=dict,
        description="Additional evidence details",
    )


class TestEvidence(BaseEvidencePoint):
    """Test evidence for MRP Point 1."""
    coverage: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Test coverage percentage",
    )
    total_tests: int = Field(
        default=0,
        ge=0,
        description="Total number of tests",
    )
    passed_tests: int = Field(
        default=0,
        ge=0,
        description="Number of passed tests",
    )
    failed_tests: int = Field(
        default=0,
        ge=0,
        description="Number of failed tests",
    )
    skipped_tests: int = Field(
        default=0,
        ge=0,
        description="Number of skipped tests",
    )
    execution_time_seconds: float = Field(
        default=0.0,
        ge=0.0,
        description="Test execution time in seconds",
    )
    unit_coverage: Optional[float] = Field(
        default=None,
        description="Unit test coverage if available",
    )
    integration_coverage: Optional[float] = Field(
        default=None,
        description="Integration test coverage if available",
    )


class LintEvidence(BaseEvidencePoint):
    """Lint evidence for MRP Point 2."""
    total_errors: int = Field(
        default=0,
        ge=0,
        description="Total lint errors",
    )
    total_warnings: int = Field(
        default=0,
        ge=0,
        description="Total lint warnings",
    )
    files_checked: int = Field(
        default=0,
        ge=0,
        description="Number of files checked",
    )
    linters_used: list[str] = Field(
        default_factory=list,
        description="List of linters used (e.g., ruff, eslint)",
    )
    errors_by_type: dict[str, int] = Field(
        default_factory=dict,
        description="Error counts by type/rule",
    )


class SecurityEvidence(BaseEvidencePoint):
    """Security evidence for MRP Point 3."""
    critical_vulnerabilities: int = Field(
        default=0,
        ge=0,
        description="Number of critical vulnerabilities",
    )
    high_vulnerabilities: int = Field(
        default=0,
        ge=0,
        description="Number of high vulnerabilities",
    )
    medium_vulnerabilities: int = Field(
        default=0,
        ge=0,
        description="Number of medium vulnerabilities",
    )
    low_vulnerabilities: int = Field(
        default=0,
        ge=0,
        description="Number of low vulnerabilities",
    )
    scanners_used: list[str] = Field(
        default_factory=list,
        description="List of scanners used (e.g., bandit, grype, npm audit)",
    )
    scan_time_seconds: float = Field(
        default=0.0,
        ge=0.0,
        description="Total scan time in seconds",
    )
    vulnerabilities_by_scanner: dict[str, dict] = Field(
        default_factory=dict,
        description="Vulnerability counts per scanner",
    )


class BuildEvidence(BaseEvidencePoint):
    """Build evidence for MRP Point 4."""
    build_success: bool = Field(
        default=False,
        description="Whether build completed successfully",
    )
    build_time_seconds: float = Field(
        default=0.0,
        ge=0.0,
        description="Build time in seconds",
    )
    build_warnings: int = Field(
        default=0,
        ge=0,
        description="Number of build warnings",
    )
    artifacts_generated: list[str] = Field(
        default_factory=list,
        description="List of generated artifacts",
    )
    docker_image_tag: Optional[str] = Field(
        default=None,
        description="Docker image tag if applicable",
    )
    docker_image_size_mb: Optional[float] = Field(
        default=None,
        description="Docker image size in MB",
    )


class ConformanceEvidence(BaseEvidencePoint):
    """Conformance evidence for MRP Point 5."""
    conformance_score: int = Field(
        default=0,
        ge=0,
        le=100,
        description="Conformance score (0-100)",
    )
    patterns_matched: int = Field(
        default=0,
        ge=0,
        description="Number of patterns matched",
    )
    patterns_violated: int = Field(
        default=0,
        ge=0,
        description="Number of patterns violated",
    )
    adrs_referenced: list[str] = Field(
        default_factory=list,
        description="List of ADRs referenced",
    )
    adr_alignment_passed: bool = Field(
        default=True,
        description="Whether ADR alignment check passed",
    )
    risk_analysis_score: Optional[int] = Field(
        default=None,
        description="Risk analysis score from Sprint 101",
    )
    deviations: list[str] = Field(
        default_factory=list,
        description="List of conformance deviations",
    )


# =========================================================================
# MRP Validation Schema
# =========================================================================

class MRPValidation(BaseModel):
    """
    Complete MRP (Merge Readiness Protocol) validation result.

    Contains all 5 evidence points with pass/fail status.
    """
    id: UUID = Field(
        default_factory=uuid4,
        description="Unique MRP validation ID",
    )
    project_id: UUID = Field(
        ...,
        description="Project UUID",
    )
    pr_id: str = Field(
        ...,
        description="Pull request ID or reference",
    )
    commit_sha: Optional[str] = Field(
        default=None,
        description="Git commit SHA",
    )

    # 5-Point Evidence
    test: TestEvidence = Field(
        default_factory=lambda: TestEvidence(status=MRPPointStatus.NOT_AVAILABLE),
        description="Point 1: Test evidence",
    )
    lint: LintEvidence = Field(
        default_factory=lambda: LintEvidence(status=MRPPointStatus.NOT_AVAILABLE),
        description="Point 2: Lint evidence",
    )
    security: SecurityEvidence = Field(
        default_factory=lambda: SecurityEvidence(status=MRPPointStatus.NOT_AVAILABLE),
        description="Point 3: Security evidence",
    )
    build: BuildEvidence = Field(
        default_factory=lambda: BuildEvidence(status=MRPPointStatus.NOT_AVAILABLE),
        description="Point 4: Build evidence",
    )
    conformance: ConformanceEvidence = Field(
        default_factory=lambda: ConformanceEvidence(status=MRPPointStatus.NOT_AVAILABLE),
        description="Point 5: Conformance evidence",
    )

    # Tier Info
    tier: str = Field(
        ...,
        description="Policy tier (LITE, STANDARD, PROFESSIONAL, ENTERPRISE)",
    )

    # Context Authority Integration (Sprint 152)
    context_snapshot_id: Optional[UUID] = Field(
        default=None,
        description="Context Authority snapshot ID for SSOT validation",
    )
    context_validation_passed: Optional[bool] = Field(
        default=None,
        description="Whether context validation passed (None if not performed)",
    )
    vibecoding_index: Optional[int] = Field(
        default=None,
        ge=0,
        le=100,
        description="Vibecoding index at time of validation (0-100)",
    )
    vibecoding_zone: Optional[str] = Field(
        default=None,
        description="Vibecoding zone: GREEN, YELLOW, ORANGE, RED",
    )

    # Overall Result
    overall_passed: bool = Field(
        default=False,
        description="Whether all required evidence points passed",
    )
    points_passed: int = Field(
        default=0,
        ge=0,
        le=5,
        description="Number of points passed (0-5)",
    )
    points_required: int = Field(
        default=0,
        ge=0,
        le=5,
        description="Number of points required for tier (0-5)",
    )

    # Timestamps
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When validation was performed",
    )
    validation_duration_ms: int = Field(
        default=0,
        ge=0,
        description="Total validation time in milliseconds",
    )
    model_config = ConfigDict(from_attributes=True)

    def get_summary(self) -> str:
        """Get human-readable summary of MRP validation."""
        return (
            f"MRP Validation: {self.points_passed}/{self.points_required} points passed "
            f"({'PASS' if self.overall_passed else 'FAIL'})"
        )


# =========================================================================
# VCR Schema
# =========================================================================

class VCR(BaseModel):
    """
    VCR (Verification Completion Report) schema.

    Aggregates MRP validation with tamper-evident storage.
    Required for PR merge in PROFESSIONAL and ENTERPRISE tiers.
    """
    id: UUID = Field(
        default_factory=uuid4,
        description="Unique VCR ID",
    )
    project_id: UUID = Field(
        ...,
        description="Project UUID",
    )
    pr_id: str = Field(
        ...,
        description="Pull request ID or reference",
    )
    commit_sha: Optional[str] = Field(
        default=None,
        description="Git commit SHA",
    )

    # MRP Validation
    mrp_validation: MRPValidation = Field(
        ...,
        description="Complete MRP validation result",
    )

    # Verdict
    verdict: VCRVerdict = Field(
        ...,
        description="Overall VCR verdict",
    )
    verdict_reason: str = Field(
        default="",
        description="Reason for verdict",
    )

    # Evidence Storage
    evidence_hash: Optional[str] = Field(
        default=None,
        description="SHA256 hash of stored evidence",
    )
    evidence_path: Optional[str] = Field(
        default=None,
        description="Path in Evidence Vault",
    )
    previous_hash: Optional[str] = Field(
        default=None,
        description="Previous VCR hash (hash chain)",
    )

    # Metadata
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When VCR was generated",
    )
    created_by: Optional[UUID] = Field(
        default=None,
        description="User who triggered VCR generation",
    )
    tier: str = Field(
        ...,
        description="Policy tier at time of VCR generation",
    )

    # CRP Reference (if applicable)
    crp_id: Optional[UUID] = Field(
        default=None,
        description="Associated CRP ID if high-risk change",
    )
    crp_approved: Optional[bool] = Field(
        default=None,
        description="Whether CRP was approved",
    )

    # Context Authority Integration (Sprint 152)
    context_snapshot_id: Optional[UUID] = Field(
        default=None,
        description="Context Authority snapshot ID for SSOT audit trail",
    )
    context_snapshot_hash: Optional[str] = Field(
        default=None,
        description="SHA256 hash of context snapshot for integrity verification",
    )
    model_config = ConfigDict(from_attributes=True)

    def is_merge_ready(self) -> bool:
        """Check if PR is merge-ready based on VCR."""
        return self.verdict == VCRVerdict.PASS


# =========================================================================
# Request/Response Schemas
# =========================================================================

class ValidateMRPRequest(BaseModel):
    """Request to validate MRP for a PR."""
    project_id: UUID = Field(
        ...,
        description="Project UUID",
    )
    pr_id: str = Field(
        ...,
        description="Pull request ID",
    )
    commit_sha: Optional[str] = Field(
        default=None,
        description="Specific commit SHA (optional)",
    )
    force_refresh: bool = Field(
        default=False,
        description="Force re-validation even if cached",
    )
    # Context Authority Integration (Sprint 152)
    context_snapshot_id: Optional[UUID] = Field(
        default=None,
        description="Context Authority snapshot ID to validate against",
    )
    include_context_validation: bool = Field(
        default=True,
        description="Whether to include Context Authority validation in MRP",
    )


class ValidateMRPResponse(BaseModel):
    """Response from MRP validation."""
    mrp_validation: MRPValidation = Field(
        ...,
        description="MRP validation result",
    )
    vcr: Optional[VCR] = Field(
        default=None,
        description="VCR if generated",
    )
    github_check_url: Optional[str] = Field(
        default=None,
        description="URL to GitHub check run",
    )
    # Context Authority Integration (Sprint 152)
    context_validation_message: Optional[str] = Field(
        default=None,
        description="Context Authority validation message",
    )
    context_overlay_applied: Optional[str] = Field(
        default=None,
        description="Name of context overlay that was applied",
    )


class VCRHistoryResponse(BaseModel):
    """Response for VCR history query."""
    vcrs: list[VCR] = Field(
        default_factory=list,
        description="List of VCRs",
    )
    total: int = Field(
        default=0,
        description="Total VCR count",
    )
    project_id: UUID = Field(
        ...,
        description="Project UUID",
    )
    pr_id: Optional[str] = Field(
        default=None,
        description="PR ID filter if applied",
    )


class TierComplianceReport(BaseModel):
    """Report on project's compliance with current tier requirements."""
    project_id: UUID = Field(
        ...,
        description="Project UUID",
    )
    current_tier: str = Field(
        ...,
        description="Current policy tier",
    )
    is_compliant: bool = Field(
        ...,
        description="Whether project meets tier requirements",
    )
    compliance_score: int = Field(
        default=0,
        ge=0,
        le=100,
        description="Compliance score (0-100)",
    )
    missing_requirements: list[str] = Field(
        default_factory=list,
        description="List of missing requirements",
    )
    recommendations: list[str] = Field(
        default_factory=list,
        description="Recommendations for improvement",
    )
    suggested_tier: Optional[str] = Field(
        default=None,
        description="Suggested tier based on current setup",
    )
    generated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When report was generated",
    )
