"""
=========================================================================
Risk Analysis Schemas - Risk Factor Detection for Planning Trigger
SDLC Orchestrator - Sprint 101 (Risk-Based Planning Trigger)

Version: 1.0.0
Date: January 23, 2026
Status: ACTIVE - Sprint 101 Implementation
Authority: Backend Lead + CTO Approved
Reference: docs/04-build/02-Sprint-Plans/SPRINT-101-DESIGN.md
Reference: SDLC 5.2.0 Planning Mode Principle (7 Mandatory Risk Factors)

Purpose:
- Define schemas for risk factor detection
- Replace >15 LOC heuristic with evidence-based risk analysis
- Enable intelligent planning trigger decisions

7 Mandatory Risk Factors (SDLC 5.2.0):
1. Data schema changes (migrations, models)
2. API contracts (endpoints, breaking changes)
3. Authentication / Authorization
4. Cross-service boundaries (microservices)
5. Concurrency / race conditions
6. Security-sensitive code (payment, PII)
7. Public API interfaces

Zero Mock Policy: Production-ready Pydantic v2 models
=========================================================================
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# =========================================================================
# Enums
# =========================================================================


class RiskFactor(str, Enum):
    """
    7 Mandatory Risk Factors (SDLC Framework 5.2.0).

    Any presence of these factors in a diff SHOULD trigger planning mode.
    """

    DATA_SCHEMA = "data_schema"  # Migrations, model changes, DB schema
    API_CONTRACT = "api_contract"  # API routes, breaking changes, OpenAPI
    AUTH = "auth"  # Authentication, authorization, RBAC
    CROSS_SERVICE = "cross_service"  # Service boundaries, IPC, messaging
    CONCURRENCY = "concurrency"  # Race conditions, locks, async patterns
    SECURITY = "security"  # Payment, PII, encryption, secrets
    PUBLIC_API = "public_api"  # External-facing APIs, SDKs


class RiskLevel(str, Enum):
    """Risk level based on score calculation."""

    MINIMAL = "minimal"  # 0-20: No planning needed
    LOW = "low"  # 21-40: Planning recommended
    MEDIUM = "medium"  # 41-60: Planning strongly recommended
    HIGH = "high"  # 61-80: Planning required
    CRITICAL = "critical"  # 81-100: Planning + CRP required


class PlanningDecision(str, Enum):
    """Decision on whether planning mode is required."""

    NOT_REQUIRED = "not_required"  # Skip planning, proceed
    RECOMMENDED = "recommended"  # Planning suggested but optional
    REQUIRED = "required"  # Planning mandatory before proceeding
    REQUIRES_CRP = "requires_crp"  # High-risk, needs human consultation


# =========================================================================
# Request Schemas
# =========================================================================


class RiskAnalysisContext(BaseModel):
    """Context for risk analysis providing additional project/change information."""

    stage: Optional[str] = Field(
        default=None,
        description="Current SDLC stage (00-discover, 04-build, etc.)",
    )
    has_tests: Optional[bool] = Field(
        default=None,
        description="Whether the change includes tests",
    )
    project_tier: Optional[str] = Field(
        default=None,
        description="Project tier (LITE, STANDARD, PROFESSIONAL, ENTERPRISE)",
    )
    maturity_level: Optional[str] = Field(
        default=None,
        description="Agentic maturity level (L0, L1, L2, L3)",
    )


class RiskAnalysisRequest(BaseModel):
    """
    Request to analyze a diff for risk factors.

    The diff can be a git diff, PR diff, or staged changes.
    Context provides additional information about the project/change.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    diff: str = Field(
        ...,
        min_length=1,
        max_length=500000,  # 500KB max diff size
        description="Git diff or PR diff content to analyze",
    )
    context: Optional[dict] = Field(
        default=None,
        description="Additional context (project_id, file_types, author, etc.)",
    )
    project_id: Optional[UUID] = Field(
        default=None,
        description="Project ID for project-specific risk thresholds",
    )


# =========================================================================
# Detection Results
# =========================================================================


class RiskFactorDetection(BaseModel):
    """Single detected risk factor with evidence."""

    factor: RiskFactor = Field(..., description="Type of risk factor detected")
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Detection confidence (0.0-1.0)",
    )
    evidence: list[str] = Field(
        default_factory=list,
        description="Lines/patterns that triggered detection",
    )
    file_paths: list[str] = Field(
        default_factory=list,
        description="Files containing the risk factor",
    )
    severity: str = Field(
        default="medium",
        description="Severity: low, medium, high, critical",
    )
    recommendation: str = Field(
        default="",
        description="Specific recommendation for this risk factor",
    )


class LOCAnalysis(BaseModel):
    """Lines of Code analysis from diff."""

    total_lines: int = Field(..., ge=0, description="Total lines in diff")
    added_lines: int = Field(..., ge=0, description="Lines added (+)")
    removed_lines: int = Field(..., ge=0, description="Lines removed (-)")
    modified_files: int = Field(..., ge=0, description="Number of files changed")
    file_types: dict[str, int] = Field(
        default_factory=dict,
        description="Line count by file extension",
    )


# =========================================================================
# Response Schemas
# =========================================================================


class RiskAnalysis(BaseModel):
    """
    Complete risk analysis result.

    Combines 7 risk factors, LOC analysis, and planning decision.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    # Analysis ID
    id: UUID = Field(..., description="Unique analysis ID")

    # Risk Factors (7 mandatory checks)
    risk_factors: list[RiskFactorDetection] = Field(
        default_factory=list,
        description="Detected risk factors with evidence",
    )
    risk_factor_count: int = Field(
        default=0,
        description="Number of distinct risk factors detected",
    )

    # Risk Score
    risk_score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Overall risk score (0-100)",
    )
    risk_level: RiskLevel = Field(
        ...,
        description="Categorized risk level",
    )

    # LOC Analysis
    loc_analysis: LOCAnalysis = Field(
        ...,
        description="Lines of code analysis",
    )

    # Planning Decision
    should_plan: bool = Field(
        ...,
        description="Whether planning mode is recommended",
    )
    planning_decision: PlanningDecision = Field(
        ...,
        description="Specific planning recommendation",
    )

    # Recommendations
    recommendations: list[str] = Field(
        default_factory=list,
        description="Actionable recommendations based on analysis",
    )

    # Metadata
    analyzed_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When analysis was performed",
    )
    analyzer_version: str = Field(
        default="1.0.0",
        description="Version of risk analyzer",
    )


class ShouldPlanResponse(BaseModel):
    """
    Quick response for planning trigger check.

    Used by API endpoint: GET /api/v1/planning/should-plan
    """

    should_plan: bool = Field(
        ...,
        description="Whether planning mode is recommended",
    )
    reason: str = Field(
        ...,
        description="Human-readable reason for decision",
    )
    risk_score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Quick risk score",
    )
    risk_factors: list[RiskFactor] = Field(
        default_factory=list,
        description="List of detected risk factors",
    )
    planning_decision: PlanningDecision = Field(
        ...,
        description="Specific planning recommendation",
    )
    full_analysis: Optional[RiskAnalysis] = Field(
        default=None,
        description="Full analysis (if requested)",
    )
