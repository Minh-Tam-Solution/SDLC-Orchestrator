"""
=========================================================================
Compliance Framework Schemas
SDLC Orchestrator - Sprint 156 (Phase 3: COMPLIANCE)

Version: 1.0.0
Date: April 7, 2026
Status: ACTIVE
Authority: CTO Approved
Framework: SDLC 6.0.5
Reference: ADR-051

Purpose:
Pydantic schemas for compliance framework API request/response validation.
Covers frameworks, controls, assessments, risk register, and RACI matrix.

Note: This is separate from schemas/compliance.py (Sprint 123 SPEC-0013
compliance validation). That file handles SDLC folder structure validation.
This file handles regulatory compliance (NIST, EU AI Act, ISO 42001).

Zero Mock Policy: Production-ready implementation
=========================================================================
"""

from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


# =============================================================================
# Enums (Pydantic versions matching SQLAlchemy enums)
# =============================================================================


class AssessmentStatus(str, Enum):
    """Compliance assessment status."""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    NOT_APPLICABLE = "not_applicable"


class ControlSeverity(str, Enum):
    """Control severity level."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RiskLikelihood(str, Enum):
    """Risk likelihood scale (1-5)."""

    RARE = "rare"
    UNLIKELY = "unlikely"
    POSSIBLE = "possible"
    LIKELY = "likely"
    ALMOST_CERTAIN = "almost_certain"


class RiskImpact(str, Enum):
    """Risk impact scale (1-5)."""

    NEGLIGIBLE = "negligible"
    MINOR = "minor"
    MODERATE = "moderate"
    MAJOR = "major"
    CATASTROPHIC = "catastrophic"


class RiskStatus(str, Enum):
    """Risk management lifecycle status."""

    IDENTIFIED = "identified"
    MITIGATING = "mitigating"
    MITIGATED = "mitigated"
    ACCEPTED = "accepted"
    CLOSED = "closed"


# Numeric values for risk score calculation
LIKELIHOOD_VALUES = {
    RiskLikelihood.RARE: 1,
    RiskLikelihood.UNLIKELY: 2,
    RiskLikelihood.POSSIBLE: 3,
    RiskLikelihood.LIKELY: 4,
    RiskLikelihood.ALMOST_CERTAIN: 5,
}

IMPACT_VALUES = {
    RiskImpact.NEGLIGIBLE: 1,
    RiskImpact.MINOR: 2,
    RiskImpact.MODERATE: 3,
    RiskImpact.MAJOR: 4,
    RiskImpact.CATASTROPHIC: 5,
}


# =============================================================================
# Evidence Required Schema (JSONB structure)
# =============================================================================


class EvidenceRequirement(BaseModel):
    """Schema for a single evidence requirement in compliance controls."""

    type: str = Field(
        ...,
        description="Evidence type: document, attestation, report, screenshot, test_result, audit_log",
    )
    description: str = Field(..., description="Human-readable evidence description")
    required: bool = Field(True, description="Whether this evidence is mandatory")
    accepted_formats: List[str] = Field(
        default_factory=list,
        description="Accepted file formats (pdf, md, docx, csv, json, etc.)",
    )

    @field_validator("type")
    @classmethod
    def validate_evidence_type(cls, v: str) -> str:
        """Validate evidence type is one of the allowed values."""
        allowed = {"document", "attestation", "report", "screenshot", "test_result", "audit_log"}
        if v not in allowed:
            raise ValueError(f"Evidence type must be one of: {', '.join(sorted(allowed))}")
        return v


# =============================================================================
# Request Schemas
# =============================================================================


class AssessmentCreate(BaseModel):
    """Schema for creating a compliance assessment."""

    project_id: UUID = Field(..., description="Project being assessed")
    control_id: UUID = Field(..., description="Control being assessed")
    status: AssessmentStatus = Field(
        AssessmentStatus.NOT_STARTED, description="Assessment status"
    )
    evidence_ids: List[UUID] = Field(
        default_factory=list, description="Evidence Vault IDs"
    )
    notes: Optional[str] = Field(None, max_length=5000, description="Assessment notes")


class AssessmentUpdate(BaseModel):
    """Schema for updating a compliance assessment."""

    status: Optional[AssessmentStatus] = Field(None, description="New status")
    evidence_ids: Optional[List[UUID]] = Field(None, description="Updated evidence IDs")
    notes: Optional[str] = Field(None, max_length=5000, description="Updated notes")


class RiskCreate(BaseModel):
    """Schema for creating a risk register entry."""

    project_id: UUID = Field(..., description="Associated project")
    framework_id: UUID = Field(..., description="Associated compliance framework")
    risk_code: str = Field(
        ..., max_length=50, description="Risk identifier (e.g., RISK-001)"
    )
    title: str = Field(..., max_length=300, description="Risk title")
    description: Optional[str] = Field(None, description="Detailed risk description")
    likelihood: RiskLikelihood = Field(
        RiskLikelihood.POSSIBLE, description="Risk likelihood"
    )
    impact: RiskImpact = Field(RiskImpact.MODERATE, description="Risk impact")
    category: str = Field(
        ...,
        max_length=100,
        description="Risk category (safety, fairness, privacy, security, reliability)",
    )
    mitigation_strategy: Optional[str] = Field(
        None, description="Mitigation strategy"
    )
    responsible_id: Optional[UUID] = Field(
        None, description="Person responsible for mitigation"
    )
    target_date: Optional[date] = Field(
        None, description="Target date for mitigation"
    )

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        """Validate risk category."""
        allowed = {"safety", "fairness", "privacy", "security", "reliability", "transparency", "accountability"}
        v_lower = v.lower().strip()
        if v_lower not in allowed:
            raise ValueError(f"Category must be one of: {', '.join(sorted(allowed))}")
        return v_lower


class RiskUpdate(BaseModel):
    """Schema for updating a risk register entry."""

    title: Optional[str] = Field(None, max_length=300)
    description: Optional[str] = None
    likelihood: Optional[RiskLikelihood] = None
    impact: Optional[RiskImpact] = None
    category: Optional[str] = Field(None, max_length=100)
    mitigation_strategy: Optional[str] = None
    responsible_id: Optional[UUID] = None
    status: Optional[RiskStatus] = None
    target_date: Optional[date] = None


class RACICreate(BaseModel):
    """Schema for creating/updating a RACI entry."""

    project_id: UUID = Field(..., description="Associated project")
    control_id: UUID = Field(..., description="Associated control")
    responsible_id: Optional[UUID] = Field(None, description="Responsible (R)")
    accountable_id: Optional[UUID] = Field(None, description="Accountable (A)")
    consulted_ids: List[UUID] = Field(
        default_factory=list, description="Consulted (C)"
    )
    informed_ids: List[UUID] = Field(
        default_factory=list, description="Informed (I)"
    )


class GovernEvaluateRequest(BaseModel):
    """Request for evaluating NIST GOVERN policies via OPA."""

    project_id: UUID = Field(..., description="Project to evaluate")
    ai_systems: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="AI systems [{name, owner, type}]",
    )
    team_training: Optional[Dict[str, Any]] = Field(
        None,
        description="Team training data {total_members, trained_members, completion_pct}",
    )
    legal_review: Optional[Dict[str, Any]] = Field(
        None,
        description="Legal review data {approved, reviewer, date}",
    )
    third_party_apis: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Third-party API data [{name, sla_documented, privacy_agreement}]",
    )
    incident_postmortems: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Incident postmortems [{incident_date, postmortem_date, process_updated}]",
    )


# =============================================================================
# Response Schemas
# =============================================================================


class UserSummary(BaseModel):
    """Brief user info for compliance responses."""

    id: UUID
    name: str
    email: str

    model_config = ConfigDict(from_attributes=True)


class FrameworkResponse(BaseModel):
    """Compliance framework response."""

    id: UUID
    code: str
    name: str
    version: str
    description: Optional[str]
    total_controls: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FrameworkListResponse(BaseModel):
    """List of compliance frameworks."""

    items: List[FrameworkResponse]
    total: int


class ControlResponse(BaseModel):
    """Compliance control response."""

    id: UUID
    framework_id: UUID
    control_code: str
    category: str
    title: str
    description: Optional[str]
    severity: str
    gate_mapping: Optional[str]
    evidence_required: List[Dict[str, Any]]
    opa_policy_code: Optional[str]
    sort_order: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AssessmentResponse(BaseModel):
    """Compliance assessment response."""

    id: UUID
    project_id: UUID
    control_id: UUID
    status: str
    evidence_ids: List[UUID]
    assessor_id: Optional[UUID]
    notes: Optional[str]
    auto_evaluated: bool
    opa_result: Optional[Dict[str, Any]]
    assessed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    control: Optional[ControlResponse] = None
    assessor: Optional[UserSummary] = None

    model_config = ConfigDict(from_attributes=True)


class AssessmentListResponse(BaseModel):
    """Paginated assessment list."""

    items: List[AssessmentResponse]
    total: int
    limit: int
    offset: int
    has_more: bool


class RiskResponse(BaseModel):
    """Risk register entry response."""

    id: UUID
    project_id: UUID
    framework_id: UUID
    risk_code: str
    title: str
    description: Optional[str]
    likelihood: str
    impact: str
    risk_score: int
    risk_level: str = Field(default="medium", description="Computed risk level")
    category: str
    mitigation_strategy: Optional[str]
    responsible_id: Optional[UUID]
    status: str
    target_date: Optional[date]
    created_at: datetime
    updated_at: datetime

    responsible: Optional[UserSummary] = None

    model_config = ConfigDict(from_attributes=True)


class RiskListResponse(BaseModel):
    """Paginated risk register list."""

    items: List[RiskResponse]
    total: int
    limit: int
    offset: int
    has_more: bool


class RACIResponse(BaseModel):
    """RACI matrix entry response."""

    id: UUID
    project_id: UUID
    control_id: UUID
    responsible_id: Optional[UUID]
    accountable_id: Optional[UUID]
    consulted_ids: List[UUID]
    informed_ids: List[UUID]
    created_at: datetime
    updated_at: datetime

    control: Optional[ControlResponse] = None
    responsible: Optional[UserSummary] = None
    accountable: Optional[UserSummary] = None

    model_config = ConfigDict(from_attributes=True)


class RACIListResponse(BaseModel):
    """List of RACI entries for a project."""

    items: List[RACIResponse]
    total: int


# =============================================================================
# GOVERN Dashboard Response
# =============================================================================


class PolicyEvaluationResult(BaseModel):
    """Result from a single OPA policy evaluation."""

    control_code: str
    title: str
    allowed: bool
    reason: str
    severity: str
    details: Dict[str, Any] = Field(default_factory=dict)


class GovernEvaluateResponse(BaseModel):
    """Response from NIST GOVERN evaluation."""

    project_id: UUID
    framework_code: str = "NIST_AI_RMF"
    function: str = "GOVERN"
    overall_compliant: bool
    policies_passed: int
    policies_total: int
    compliance_percentage: float
    results: List[PolicyEvaluationResult]
    evaluated_at: datetime


class GovernDashboardResponse(BaseModel):
    """GOVERN function dashboard data."""

    project_id: UUID
    compliance_percentage: float = Field(0.0, description="Overall GOVERN compliance %")
    policies_passed: int = Field(0, description="Number of passing policies")
    policies_total: int = Field(0, description="Total GOVERN policies")
    policy_results: List[PolicyEvaluationResult] = Field(
        default_factory=list, description="Individual policy results"
    )
    risk_summary: Dict[str, int] = Field(
        default_factory=dict,
        description="Risk count by level {critical, high, medium, low}",
    )
    total_risks: int = Field(0, description="Total risk entries")
    raci_coverage: float = Field(
        0.0, description="% of controls with RACI assignments"
    )
    training_completion: Optional[float] = Field(
        None, description="Team training completion %"
    )


# =============================================================================
# MAP Enums & Schemas (Sprint 157)
# =============================================================================


class AISystemType(str, Enum):
    """AI system type classification."""

    NLP = "nlp"
    VISION = "vision"
    RECOMMENDATION = "recommendation"
    DECISION = "decision"
    GENERATIVE = "generative"


class AIRiskLevel(str, Enum):
    """AI system risk level (EU AI Act taxonomy)."""

    MINIMAL = "minimal"
    LIMITED = "limited"
    HIGH = "high"
    UNACCEPTABLE = "unacceptable"


class MetricType(str, Enum):
    """Performance metric type classification."""

    ACCURACY = "accuracy"
    PRECISION = "precision"
    RECALL = "recall"
    F1_SCORE = "f1_score"
    LATENCY_P95 = "latency_p95"
    BIAS_SCORE = "bias_score"
    DISPARITY_INDEX = "disparity_index"
    CUSTOM = "custom"


# =============================================================================
# MAP Request Schemas
# =============================================================================


class AISystemCreate(BaseModel):
    """Schema for creating an AI system."""

    project_id: UUID = Field(..., description="Associated project")
    name: str = Field(..., max_length=200, description="AI system name")
    description: Optional[str] = Field(None, description="System description")
    system_type: AISystemType = Field(..., description="System type")
    risk_level: AIRiskLevel = Field(AIRiskLevel.HIGH, description="Risk level")
    purpose: Optional[str] = Field(None, description="MAP-1.1: Intended purpose")
    scope: Optional[str] = Field(None, description="MAP-1.1: Deployment scope")
    stakeholders: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="MAP-1.2: [{role, name, impact_type}]",
    )
    dependencies: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="MAP-3.2: [{name, type, version, provider}]",
    )
    categorization: Optional[Dict[str, Any]] = Field(
        None,
        description="MAP-2.1: {risk_tier, data_sensitivity, autonomy_level, reversibility}",
    )
    owner_id: Optional[UUID] = Field(None, description="System owner")


class AISystemUpdate(BaseModel):
    """Schema for updating an AI system."""

    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    system_type: Optional[AISystemType] = None
    risk_level: Optional[AIRiskLevel] = None
    purpose: Optional[str] = None
    scope: Optional[str] = None
    stakeholders: Optional[List[Dict[str, Any]]] = None
    dependencies: Optional[List[Dict[str, Any]]] = None
    categorization: Optional[Dict[str, Any]] = None
    owner_id: Optional[UUID] = None


class MapEvaluateRequest(BaseModel):
    """Request for evaluating NIST MAP policies via OPA."""

    project_id: UUID = Field(..., description="Project to evaluate")


class AISystemResponse(BaseModel):
    """AI system response."""

    id: UUID
    project_id: UUID
    name: str
    description: Optional[str]
    system_type: str
    risk_level: str
    purpose: Optional[str]
    scope: Optional[str]
    stakeholders: List[Dict[str, Any]]
    dependencies: List[Dict[str, Any]]
    categorization: Optional[Dict[str, Any]]
    owner_id: Optional[UUID]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AISystemListResponse(BaseModel):
    """Paginated AI system list."""

    items: List[AISystemResponse]
    total: int
    limit: int
    offset: int
    has_more: bool


class MapEvaluateResponse(BaseModel):
    """Response from NIST MAP evaluation."""

    project_id: UUID
    framework_code: str = "NIST_AI_RMF"
    function: str = "MAP"
    overall_compliant: bool
    policies_passed: int
    policies_total: int
    compliance_percentage: float
    results: List[PolicyEvaluationResult]
    evaluated_at: datetime


class MapDashboardResponse(BaseModel):
    """MAP function dashboard data."""

    project_id: UUID
    compliance_percentage: float = Field(0.0, description="Overall MAP compliance %")
    policies_passed: int = Field(0, description="Number of passing policies")
    policies_total: int = Field(0, description="Total MAP policies")
    policy_results: List[PolicyEvaluationResult] = Field(
        default_factory=list, description="Individual policy results"
    )
    ai_system_summary: Dict[str, int] = Field(
        default_factory=dict,
        description="AI system count by type {nlp, vision, ...}",
    )
    total_systems: int = Field(0, description="Total active AI systems")
    risk_summary: Dict[str, int] = Field(
        default_factory=dict,
        description="Risk count by level {critical, high, medium, low}",
    )
    total_risks: int = Field(0, description="Total risk entries")


class RiskImpactMapping(BaseModel):
    """Risk-to-impact mapping for MAP-3.1."""

    risk_id: UUID
    risk_code: str
    title: str
    category: str
    impact_areas: List[str] = Field(default_factory=list)
    affected_stakeholders: List[str] = Field(default_factory=list)
    risk_score: int


class RiskImpactListResponse(BaseModel):
    """List of risk-to-impact mappings."""

    items: List[RiskImpactMapping]
    total: int


# =============================================================================
# MEASURE Request Schemas
# =============================================================================


class MetricCreate(BaseModel):
    """Schema for creating a performance metric."""

    project_id: UUID = Field(..., description="Associated project")
    ai_system_id: UUID = Field(..., description="Associated AI system")
    metric_type: MetricType = Field(..., description="Metric type")
    metric_name: str = Field(..., max_length=200, description="Display name")
    metric_value: float = Field(..., description="Measured value")
    threshold_min: Optional[float] = Field(None, description="Lower bound")
    threshold_max: Optional[float] = Field(None, description="Upper bound")
    unit: Optional[str] = Field(None, max_length=50, description="Unit: %, ms, ratio")
    demographic_group: Optional[str] = Field(
        None, max_length=100, description="Demographic group: gender:female"
    )
    tags: List[str] = Field(
        default_factory=list, description='Tags: ["bias","fairness"]'
    )
    measured_at: datetime = Field(..., description="When measurement was taken")
    notes: Optional[str] = Field(None, description="Notes about this measurement")


class MetricBatchCreate(BaseModel):
    """Schema for batch creating performance metrics."""

    project_id: UUID = Field(..., description="Associated project")
    metrics: List[MetricCreate] = Field(..., min_length=1, description="Metrics to create")


class MeasureEvaluateRequest(BaseModel):
    """Request for evaluating NIST MEASURE policies via OPA."""

    project_id: UUID = Field(..., description="Project to evaluate")


class MetricResponse(BaseModel):
    """Performance metric response."""

    id: UUID
    project_id: UUID
    ai_system_id: UUID
    metric_type: str
    metric_name: str
    metric_value: float
    threshold_min: Optional[float]
    threshold_max: Optional[float]
    is_within_threshold: bool
    unit: Optional[str]
    demographic_group: Optional[str]
    tags: List[str]
    measured_at: datetime
    measured_by_id: Optional[UUID]
    notes: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MetricListResponse(BaseModel):
    """Paginated metric list."""

    items: List[MetricResponse]
    total: int
    limit: int
    offset: int
    has_more: bool


class MetricTrendPoint(BaseModel):
    """Single point in a metric trend."""

    measured_at: datetime
    metric_value: float
    is_within_threshold: bool


class MetricTrendResponse(BaseModel):
    """Metric trend data over time."""

    ai_system_id: UUID
    metric_type: str
    data_points: List[MetricTrendPoint]
    total_points: int


class BiasGroupSummary(BaseModel):
    """Bias summary for a demographic group."""

    demographic_group: str
    avg_score: float
    min_score: float
    max_score: float
    count: int


class BiasSystemSummary(BaseModel):
    """Bias summary per AI system."""

    ai_system_id: UUID
    ai_system_name: str
    groups: List[BiasGroupSummary]
    disparity_ratio: Optional[float] = Field(
        None, description="Max/min ratio across groups"
    )
    is_compliant: bool = Field(True, description="Disparity ≤ 1.25")


class BiasSummaryResponse(BaseModel):
    """Overall bias summary for a project."""

    project_id: UUID
    systems: List[BiasSystemSummary]
    total_bias_metrics: int
    compliant_systems: int
    non_compliant_systems: int


class MeasureEvaluateResponse(BaseModel):
    """Response from NIST MEASURE evaluation."""

    project_id: UUID
    framework_code: str = "NIST_AI_RMF"
    function: str = "MEASURE"
    overall_compliant: bool
    policies_passed: int
    policies_total: int
    compliance_percentage: float
    results: List[PolicyEvaluationResult]
    evaluated_at: datetime


class MeasureDashboardResponse(BaseModel):
    """MEASURE function dashboard data."""

    project_id: UUID
    compliance_percentage: float = Field(0.0, description="Overall MEASURE compliance %")
    policies_passed: int = Field(0, description="Number of passing policies")
    policies_total: int = Field(0, description="Total MEASURE policies")
    policy_results: List[PolicyEvaluationResult] = Field(
        default_factory=list, description="Individual policy results"
    )
    total_metrics: int = Field(0, description="Total recorded metrics")
    within_threshold: int = Field(0, description="Metrics within threshold")
    bias_groups_count: int = Field(0, description="Distinct demographic groups measured")
    disparity_summary: Dict[str, Any] = Field(
        default_factory=dict,
        description="Disparity analysis summary",
    )


# =============================================================================
# NIST MANAGE Schemas (Sprint 158)
# =============================================================================


class ManageResponseType(str, Enum):
    """Risk response type per ISO 31000."""

    MITIGATE = "mitigate"
    ACCEPT = "accept"
    TRANSFER = "transfer"
    AVOID = "avoid"


class ManageResponseStatus(str, Enum):
    """Risk response status."""

    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    DEFERRED = "deferred"


class ManageResponsePriority(str, Enum):
    """Risk response priority."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ManageIncidentSeverity(str, Enum):
    """Incident severity level."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ManageIncidentType(str, Enum):
    """AI system incident type."""

    PERFORMANCE_DEGRADATION = "performance_degradation"
    BIAS_DETECTED = "bias_detected"
    SECURITY_BREACH = "security_breach"
    AVAILABILITY = "availability"
    DATA_QUALITY = "data_quality"
    COMPLIANCE_VIOLATION = "compliance_violation"


class ManageIncidentStatus(str, Enum):
    """Incident lifecycle status."""

    OPEN = "open"
    INVESTIGATING = "investigating"
    MITIGATING = "mitigating"
    RESOLVED = "resolved"
    CLOSED = "closed"


# -- Deactivation Criteria (CTO Condition #5) --


class DeactivationCriteria(BaseModel):
    """Pydantic schema for MANAGE-2.4 deactivation criteria JSONB validation."""

    conditions: List[str] = Field(
        ...,
        min_length=1,
        description="Conditions triggering deactivation, e.g. ['bias_score > 0.3', 'for 7 days']",
    )
    threshold: Optional[float] = Field(
        None, description="Numeric threshold value"
    )
    action: str = Field(
        ...,
        description="Action to take: deactivate, alert, review",
    )

    @field_validator("action")
    @classmethod
    def validate_action(cls, v: str) -> str:
        allowed = {"deactivate", "alert", "review"}
        if v not in allowed:
            raise ValueError(f"action must be one of {allowed}")
        return v


# -- Risk Response Schemas --


class ResourceAllocation(BaseModel):
    """Single resource allocation entry."""

    type: str = Field(..., description="Resource type: budget, personnel, tool")
    description: str = Field(..., description="Resource description")
    budget: float = Field(0.0, ge=0, description="Budget amount")


class RiskResponseCreate(BaseModel):
    """Schema for creating a risk response."""

    project_id: UUID
    risk_id: UUID
    response_type: ManageResponseType
    description: str = Field(..., min_length=1, max_length=2000)
    assigned_to: Optional[str] = Field(None, max_length=200)
    priority: ManageResponsePriority = ManageResponsePriority.MEDIUM
    due_date: Optional[date] = None
    resources_allocated: List[ResourceAllocation] = Field(default_factory=list)
    deactivation_criteria: Optional[DeactivationCriteria] = None
    notes: Optional[str] = None


class RiskResponseUpdate(BaseModel):
    """Schema for updating a risk response."""

    response_type: Optional[ManageResponseType] = None
    description: Optional[str] = Field(None, min_length=1, max_length=2000)
    assigned_to: Optional[str] = Field(None, max_length=200)
    priority: Optional[ManageResponsePriority] = None
    status: Optional[ManageResponseStatus] = None
    due_date: Optional[date] = None
    resources_allocated: Optional[List[ResourceAllocation]] = None
    deactivation_criteria: Optional[DeactivationCriteria] = None
    notes: Optional[str] = None


class RiskResponseResponse(BaseModel):
    """Risk response API response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    risk_id: UUID
    response_type: str
    description: str
    assigned_to: Optional[str] = None
    priority: str
    status: str
    due_date: Optional[date] = None
    resources_allocated: List[Dict[str, Any]] = Field(default_factory=list)
    deactivation_criteria: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class RiskResponseListResponse(BaseModel):
    """Paginated risk response list."""

    items: List[RiskResponseResponse]
    total: int
    limit: int
    offset: int
    has_more: bool


# -- Incident Schemas --


class IncidentCreate(BaseModel):
    """Schema for reporting an incident."""

    project_id: UUID
    ai_system_id: UUID
    risk_id: Optional[UUID] = None
    title: str = Field(..., min_length=1, max_length=300)
    description: Optional[str] = None
    severity: ManageIncidentSeverity
    incident_type: ManageIncidentType
    reported_by: Optional[str] = Field(None, max_length=200)
    assigned_to: Optional[str] = Field(None, max_length=200)
    occurred_at: datetime


class IncidentUpdate(BaseModel):
    """Schema for updating an incident."""

    title: Optional[str] = Field(None, min_length=1, max_length=300)
    description: Optional[str] = None
    severity: Optional[ManageIncidentSeverity] = None
    status: Optional[ManageIncidentStatus] = None
    assigned_to: Optional[str] = Field(None, max_length=200)
    resolution: Optional[str] = None
    root_cause: Optional[str] = None
    resolved_at: Optional[datetime] = None


class IncidentResponse(BaseModel):
    """Incident API response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    ai_system_id: UUID
    risk_id: Optional[UUID] = None
    title: str
    description: Optional[str] = None
    severity: str
    incident_type: str
    status: str
    reported_by: Optional[str] = None
    assigned_to: Optional[str] = None
    resolution: Optional[str] = None
    root_cause: Optional[str] = None
    occurred_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class IncidentListResponse(BaseModel):
    """Paginated incident list."""

    items: List[IncidentResponse]
    total: int
    limit: int
    offset: int
    has_more: bool


# -- MANAGE Evaluation Schemas --


class ManageEvaluateRequest(BaseModel):
    """Request to evaluate NIST MANAGE policies."""

    project_id: UUID


class ManageEvaluateResponse(BaseModel):
    """Response from NIST MANAGE evaluation."""

    project_id: UUID
    framework_code: str = "NIST_AI_RMF"
    function: str = "MANAGE"
    overall_compliant: bool
    policies_passed: int
    policies_total: int
    compliance_percentage: float
    results: List[PolicyEvaluationResult]
    evaluated_at: datetime


class ManageDashboardResponse(BaseModel):
    """MANAGE function dashboard data."""

    project_id: UUID
    compliance_percentage: float = Field(0.0, description="Overall MANAGE compliance %")
    policies_passed: int = Field(0, description="Number of passing policies")
    policies_total: int = Field(0, description="Total MANAGE policies")
    policy_results: List[PolicyEvaluationResult] = Field(
        default_factory=list, description="Individual policy results"
    )
    total_risk_responses: int = Field(0, description="Total risk responses")
    completed_responses: int = Field(0, description="Completed risk responses")
    total_incidents: int = Field(0, description="Total incidents")
    open_incidents: int = Field(0, description="Open incidents")
    critical_incidents: int = Field(0, description="Unresolved critical incidents")
    has_deactivation_criteria: bool = Field(
        False, description="Whether any response has deactivation criteria"
    )
