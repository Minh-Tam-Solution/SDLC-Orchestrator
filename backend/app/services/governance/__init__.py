"""
=========================================================================
Governance Services - Complete Governance System
SDLC Orchestrator - Sprint 110 (CEO Dashboard & Observability)

Version: 1.7.0
Date: January 27, 2026
Status: ACTIVE - Sprint 110 Day 5
Authority: CTO + Backend Lead Approved
Framework: SDLC 5.3.0 Quality Assurance System

Services:
- AutoGenerationService: 4 generators for compliance artifacts
- GovernanceModeService: Enforcement mode management (OFF/WARNING/SOFT/FULL)
- GovernanceSignalsEngine: Vibecoding Index calculation (5 signals)
- StageGatingService: Stage-aware PR validation (11 SDLC stages)
- ContextAuthorityEngineV1: ADR & context linkage validation (metadata only)
- CEODashboardService: Executive governance intelligence & metrics
- PrometheusMetricsCollector: 45 Prometheus metrics for observability
- GrafanaDashboardService: 3 Grafana dashboards (CEO, Tech, Ops)
- FeedbackService: Actionable error messages (planned)

Zero Mock Policy: Real implementations only
=========================================================================
"""

from app.services.governance.auto_generator import (
    AutoGenerationService,
    IntentGenerator,
    OwnershipGenerator,
    ContextAttachmentGenerator,
    AttestationGenerator,
    GenerationResult,
    FallbackLevel,
    create_auto_generation_service,
    get_auto_generation_service,
)

from app.services.governance.mode_service import (
    GovernanceMode,
    GovernanceModeService,
    GovernanceModeState,
    GovernanceViolation,
    ViolationSeverity,
    EnforcementResult,
    RollbackCriteria,
    create_governance_mode_service,
    get_governance_mode_service,
    initialize_governance_mode_service,
)

from app.services.governance.signals_engine import (
    GovernanceSignalsEngine,
    CodeSubmission,
    ProjectContext,
    VibecodingIndex,
    SignalScore,
    SignalType,
    IndexCategory,
    RoutingDecision,
    CriticalPathMatch,
    create_signals_engine,
    get_signals_engine,
)

from app.services.governance.stage_gating import (
    StageGatingService,
    SDLCStage,
    ViolationType as StageViolationType,
    PRRequirement,
    StageRules,
    StageViolation,
    StageGatingResult,
    PullRequest,
    Project,
    DEFAULT_STAGE_RULES,
    create_stage_gating_service,
    get_stage_gating_service,
)

from app.services.governance.context_authority import (
    ContextAuthorityEngineV1,
    ContextViolationType,
    ViolationSeverity as ContextViolationSeverity,
    ADRStatus,
    ADR,
    DesignSpec,
    AgentsMdInfo,
    ModuleAnnotation,
    ContextViolation,
    ContextValidationResult,
    CodeSubmission as ContextCodeSubmission,
    create_context_authority_engine,
    get_context_authority_engine,
)

from app.services.governance.ceo_dashboard import (
    CEODashboardService,
    TimeRange,
    TrendDirection,
    HealthStatus,
    TimeSavedMetric,
    RoutingBreakdown,
    PendingDecision,
    WeeklySummary,
    TopRejectionReason,
    CEOOverride,
    SystemHealthSnapshot,
    CEODashboardSummary,
    create_ceo_dashboard_service,
    get_ceo_dashboard_service,
)

from app.services.governance.metrics_collector import (
    PrometheusMetricsCollector,
    MetricType,
    MetricDefinition,
    ALL_METRICS,
    GOVERNANCE_METRICS,
    PERFORMANCE_METRICS,
    BUSINESS_METRICS,
    DEVELOPER_EXPERIENCE_METRICS as DEVELOPER_METRICS,
    SYSTEM_HEALTH_METRICS as SYSTEM_METRICS,
    create_metrics_collector,
    get_metrics_collector,
)

from app.services.governance.grafana_dashboards import (
    GrafanaDashboardService,
    GrafanaDashboard,
    GrafanaPanel,
    DashboardType,
    PanelType,
    create_grafana_dashboard_service,
    get_grafana_dashboard_service,
)

__all__ = [
    # Auto-Generation Service
    "AutoGenerationService",
    # Individual Generators
    "IntentGenerator",
    "OwnershipGenerator",
    "ContextAttachmentGenerator",
    "AttestationGenerator",
    # Auto-Generation Data Classes
    "GenerationResult",
    "FallbackLevel",
    # Auto-Generation Factory Functions
    "create_auto_generation_service",
    "get_auto_generation_service",
    # Mode Service
    "GovernanceMode",
    "GovernanceModeService",
    "GovernanceModeState",
    "GovernanceViolation",
    "ViolationSeverity",
    "EnforcementResult",
    "RollbackCriteria",
    # Mode Service Factory Functions
    "create_governance_mode_service",
    "get_governance_mode_service",
    "initialize_governance_mode_service",
    # Signals Engine
    "GovernanceSignalsEngine",
    "CodeSubmission",
    "ProjectContext",
    "VibecodingIndex",
    "SignalScore",
    "SignalType",
    "IndexCategory",
    "RoutingDecision",
    "CriticalPathMatch",
    # Signals Engine Factory Functions
    "create_signals_engine",
    "get_signals_engine",
    # Stage Gating Service
    "StageGatingService",
    "SDLCStage",
    "StageViolationType",
    "PRRequirement",
    "StageRules",
    "StageViolation",
    "StageGatingResult",
    "PullRequest",
    "Project",
    "DEFAULT_STAGE_RULES",
    # Stage Gating Factory Functions
    "create_stage_gating_service",
    "get_stage_gating_service",
    # Context Authority Engine V1
    "ContextAuthorityEngineV1",
    "ContextViolationType",
    "ContextViolationSeverity",
    "ADRStatus",
    "ADR",
    "DesignSpec",
    "AgentsMdInfo",
    "ModuleAnnotation",
    "ContextViolation",
    "ContextValidationResult",
    "ContextCodeSubmission",
    # Context Authority Factory Functions
    "create_context_authority_engine",
    "get_context_authority_engine",
    # CEO Dashboard Service
    "CEODashboardService",
    "TimeRange",
    "TrendDirection",
    "HealthStatus",
    "TimeSavedMetric",
    "RoutingBreakdown",
    "PendingDecision",
    "WeeklySummary",
    "TopRejectionReason",
    "CEOOverride",
    "SystemHealthSnapshot",
    "CEODashboardSummary",
    # CEO Dashboard Factory Functions
    "create_ceo_dashboard_service",
    "get_ceo_dashboard_service",
    # Prometheus Metrics Collector
    "PrometheusMetricsCollector",
    "MetricType",
    "MetricDefinition",
    "ALL_METRICS",
    "GOVERNANCE_METRICS",
    "PERFORMANCE_METRICS",
    "BUSINESS_METRICS",
    "DEVELOPER_METRICS",
    "SYSTEM_METRICS",
    # Metrics Collector Factory Functions
    "create_metrics_collector",
    "get_metrics_collector",
    # Grafana Dashboard Service
    "GrafanaDashboardService",
    "GrafanaDashboard",
    "GrafanaPanel",
    "DashboardType",
    "PanelType",
    # Grafana Dashboard Factory Functions
    "create_grafana_dashboard_service",
    "get_grafana_dashboard_service",
]
