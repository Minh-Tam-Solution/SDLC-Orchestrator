"""
SQLAlchemy Models - SDLC Orchestrator

Version: 1.0.0
Date: November 28, 2025
Status: ACTIVE - Week 3 Architecture Design
Authority: Backend Lead + CTO Approved
Foundation: Data Model v0.1 (21 tables, 9.8/10 quality)
Framework: SDLC 4.9 Complete Lifecycle

Database: PostgreSQL 15.5+
ORM: SQLAlchemy 2.0+
Migrations: Alembic

Quality Standards:
- Zero Mock Policy enforced (production-ready code only)
- Type hints (Python 3.11+)
- Docstrings (Google style)
- Zero N+1 queries (eager loading where needed)
"""

from app.db.base_class import Base

# Import models that are referenced by Project relationships FIRST
# (These are needed before Project is imported to resolve forward references)
from app.models.compliance_validation import (
    ComplianceScore,
    ComplianceIssue,
    FolderCollisionCheck,
    ComplianceCategory,
    IssueSeverity,
)

# Policy Pack (needed by Project relationship)
from app.models.policy_pack import PolicyPack

# Core Entities (6 models)
from app.models.user import User, Role, OAuthAccount, APIKey, RefreshToken
from app.models.project import Project, ProjectMember

# Project Function Role (depends on Project - Sprint 161)
from app.models.project_function_role import ProjectFunctionRole
from app.models.gate import Gate

# Gate Management (FR1) - 2 models
from app.models.gate_approval import GateApproval
from app.models.policy import PolicyEvaluation

# Evidence Vault (FR2) - 2 models
from app.models.gate_evidence import GateEvidence, EvidenceIntegrityCheck

# AI Engine (FR3) - 4 models
from app.models.ai_engine import AIProvider, AIRequest, AIUsageLog, AIEvidenceDraft

# Policy Library (FR5) - 3 models
from app.models.policy import Policy, CustomPolicy, PolicyTest

# Supporting - 5 models
from app.models.support import StageTransition, Webhook, AuditLog, Notification, SystemSetting

# Compliance Scanning (Sprint 21) - 3 models
from app.models.compliance_scan import ComplianceScan, ComplianceViolation, ScanJob

# Usage Tracking (Sprint 24) - 4 models
from app.models.usage_tracking import UserSession, UsageEvent, FeatureUsage, PilotMetrics

# Feedback (Sprint 24) - 2 models
from app.models.feedback import PilotFeedback, FeedbackComment

# SDLC Validation (Sprint 30) - 2 models
from app.models.sdlc_validation import SDLCValidation, SDLCValidationIssue

# Analytics (Sprint 41) - 2 models
from app.models.analytics import AnalyticsEvent, AICodeEvent

# Override / VCR Flow (Sprint 43) - 2 models
from app.models.override import ValidationOverride, OverrideAuditLog

# Codegen Usage Tracking (Sprint 48) - 4 models
from app.models.codegen_usage import (
    CodegenUsageLog,
    CodegenDailySummary,
    CodegenMonthlyCost,
    CodegenProviderHealth,
)

# Pilot Tracking (Sprint 49) - 4 models
from app.models.pilot_tracking import (
    PilotParticipant,
    PilotSession,
    PilotSatisfactionSurvey,
    PilotDailyMetrics,
)

# Stage Mapping (Sprint 49 - SDLC 5.1.2) - 1 model
from app.models.stage_mapping import ProjectStageMapping

# Subscription & Payment (Sprint 58) - 2 models
from app.models.subscription import (
    Subscription,
    PaymentHistory,
    SubscriptionPlan,
    SubscriptionStatus,
    PaymentStatus,
)

# SAST Scanning (Sprint 69) - 2 models
from app.models.sast_scan import SASTScan, SASTFinding

# Council Sessions (Sprint 69) - 1 model
from app.models.council_session import CouncilSession

# Teams Foundation (Sprint 70) - 3 models
from app.models.organization import Organization
from app.models.team import Team  # Must be before TeamInvitation (relationship dependency)
from app.models.team_invitation import TeamInvitation, InvitationStatus  # Sprint 128
from app.models.organization_invitation import OrganizationInvitation, OrgInvitationStatus  # Sprint 146
from app.models.team_member import TeamMember

# GitHub Integration (Sprint 129) - 2 models
from app.models.github_integration import (
    GitHubInstallation,
    GitHubRepository,
    InstallationStatus,
    CloneStatus,
)

# Planning Hierarchy (Sprint 74) - 5 models
from app.models.roadmap import Roadmap
from app.models.phase import Phase
from app.models.sprint import Sprint
from app.models.sprint_gate_evaluation import SprintGateEvaluation, G_SPRINT_CHECKLIST_TEMPLATE, G_SPRINT_CLOSE_CHECKLIST_TEMPLATE
from app.models.backlog_item import BacklogItem

# Retrospective Enhancement (Sprint 78) - 1 model
from app.models.retro_action_item import RetroActionItem

# Cross-Project Dependencies (Sprint 78) - 1 model
from app.models.sprint_dependency import SprintDependency

# Resource Allocation (Sprint 78) - 1 model
from app.models.resource_allocation import ResourceAllocation

# Sprint Templates (Sprint 78) - 1 model
from app.models.sprint_template import SprintTemplate

# AGENTS.md Integration (Sprint 80) - 2 models
from app.models.agents_md import AgentsMdFile, ContextOverlay

# Evidence Manifest Hash Chain (Sprint 82) - 2 models
from app.models.evidence_manifest import EvidenceManifest, EvidenceManifestVerification

# Feedback Learning (Sprint 100 - EP-11) - 4 models
from app.models.pr_learning import PRLearning
from app.models.decomposition_hint import DecompositionHint, HintUsageLog
from app.models.learning_aggregation import LearningAggregation

# Governance System (Sprint 108) - 14 models
from app.models.governance import (
    GovernanceSubmission,
    GovernanceRejection,
    EvidenceVaultEntry,
    GovernanceAuditLog,
    OwnershipRegistry,
    QualityContract,
    ContextAuthority,
    GovernanceContextSnapshot,
    ContractVersion,
    ContractViolation,
    AIAttestation,
    HumanReview,
    GovernanceException,
    EscalationLog,
)

# Governance System v2.0 (Sprint 118) - 14 models (SPEC-0001 + SPEC-0002)
# PART 1: Specification Management (7 models)
from app.models.governance_specification import (
    GovernanceSpecification,
    SpecVersion,
    SpecFrontmatterMetadata,
    SpecFunctionalRequirement,
    SpecAcceptanceCriterion,
    SpecImplementationPhase,
    SpecCrossReference,
)
# PART 2: Vibecoding System (7 models)
from app.models.governance_vibecoding import (
    VibecodingSignal,
    VibecodingIndexHistory,
    ProgressiveRoutingRule,
    KillSwitchTrigger,
    KillSwitchEvent,
    TierSpecificRequirement,
    SpecValidationResult,
)

# Consultation Request (Sprint 101) - 1 model
from app.models.consultation_request import ConsultationRequest

# Framework Version (Sprint 101) - 1 model
from app.models.framework_version import FrameworkVersion

# Agentic Maturity (Sprint 104) - 1 model
from app.models.agentic_maturity import AgenticMaturityAssessment

# Context Authority V2 (Sprint 120 - SPEC-0011) - 3 models
from app.models.context_authority_v2 import (
    ContextOverlayTemplate,
    ContextSnapshot as ContextSnapshotV2,
    ContextOverlayApplication,
)

# Product Telemetry (Sprint 147 - Product Truth Layer) - 1 model + constants
from app.models.product_event import ProductEvent, EventNames

# VCR - Version Controlled Resolution (Sprint 151 - SASE Artifacts) - 1 model + enum
from app.models.vcr import VersionControlledResolution, VCRStatus

# Compliance Framework (Sprint 156 - Phase 3 COMPLIANCE) - 5 models + 5 enums
from app.models.compliance import (
    ComplianceFramework,
    ComplianceControl,
    ComplianceAssessment,
    ComplianceRiskRegister,
    ComplianceRACI,
    AssessmentStatus as ComplianceAssessmentStatus,
    ControlSeverity,
    RiskLikelihood,
    RiskImpact,
    RiskStatus,
)

# NIST MAP & MEASURE (Sprint 157 - Phase 3 COMPLIANCE) - 2 models + 3 enums
from app.models.nist_map_measure import (
    AISystem,
    PerformanceMetric,
    AISystemType,
    AIRiskLevel,
    MetricType,
)

# NIST MANAGE (Sprint 158 - Phase 3 COMPLIANCE) - 2 models + 6 enums
from app.models.nist_manage import (
    ManageRiskResponse,
    ManageIncident,
    ResponseType,
    ResponseStatus,
    ResponsePriority,
    IncidentSeverity,
    IncidentType,
    IncidentStatus,
)

# Tier-Based Gate Approval (Sprint 161 - Phase 4 AUTHORIZATION) - GateDecision model
# Note: ProjectFunctionRole imported earlier (before Project) to resolve relationship
from app.models.gate_decision import GateDecision

# Note: ComplianceScore, ComplianceIssue, FolderCollisionCheck imported earlier
# (before Project) to resolve forward references

__all__ = [
    # Base
    "Base",
    # Policy Pack (needed by Project)
    "PolicyPack",
    # Core Entities (6)
    "User",
    "Role",
    "OAuthAccount",
    "APIKey",
    "RefreshToken",
    "Project",
    "ProjectMember",
    "Gate",
    # Gate Management (2)
    "GateApproval",
    "PolicyEvaluation",
    # Evidence Vault (2)
    "GateEvidence",
    "EvidenceIntegrityCheck",
    # AI Engine (4)
    "AIProvider",
    "AIRequest",
    "AIUsageLog",
    "AIEvidenceDraft",
    # Policy Library (3)
    "Policy",
    "CustomPolicy",
    "PolicyTest",
    # Supporting (5)
    "StageTransition",
    "Webhook",
    "AuditLog",
    "Notification",
    "SystemSetting",
    # Compliance Scanning (3)
    "ComplianceScan",
    "ComplianceViolation",
    "ScanJob",
    # Usage Tracking (4)
    "UserSession",
    "UsageEvent",
    "FeatureUsage",
    "PilotMetrics",
    # Feedback (2)
    "PilotFeedback",
    "FeedbackComment",
    # SDLC Validation (2)
    "SDLCValidation",
    "SDLCValidationIssue",
    # Analytics (2)
    "AnalyticsEvent",
    "AICodeEvent",
    # Override / VCR Flow (2)
    "ValidationOverride",
    "OverrideAuditLog",
    # Codegen Usage Tracking (4)
    "CodegenUsageLog",
    "CodegenDailySummary",
    "CodegenMonthlyCost",
    "CodegenProviderHealth",
    # Pilot Tracking (4)
    "PilotParticipant",
    "PilotSession",
    "PilotSatisfactionSurvey",
    "PilotDailyMetrics",
    # Stage Mapping (1)
    "ProjectStageMapping",
    # Subscription & Payment (2)
    "Subscription",
    "PaymentHistory",
    "SubscriptionPlan",
    "SubscriptionStatus",
    "PaymentStatus",
    # SAST Scanning (2)
    "SASTScan",
    "SASTFinding",
    # Council Sessions (1)
    "CouncilSession",
    # Teams Foundation (3)
    "Organization",
    "Team",
    "TeamMember",
    # Team & Org Invitations - Sprint 128, 146 (2 models + 2 enums)
    "TeamInvitation",
    "InvitationStatus",
    "OrganizationInvitation",
    "OrgInvitationStatus",
    # Planning Hierarchy - Sprint 74 (5 models + 2 templates)
    "Roadmap",
    "Phase",
    "Sprint",
    "SprintGateEvaluation",
    "G_SPRINT_CHECKLIST_TEMPLATE",
    "G_SPRINT_CLOSE_CHECKLIST_TEMPLATE",
    "BacklogItem",
    # Retrospective Enhancement - Sprint 78 (1 model)
    "RetroActionItem",
    # Cross-Project Dependencies - Sprint 78 (1 model)
    "SprintDependency",
    # Resource Allocation - Sprint 78 (1 model)
    "ResourceAllocation",
    # Sprint Templates - Sprint 78 (1 model)
    "SprintTemplate",
    # AGENTS.md Integration - Sprint 80 (2 models)
    "AgentsMdFile",
    "ContextOverlay",
    # Evidence Manifest Hash Chain - Sprint 82 (2 models)
    "EvidenceManifest",
    "EvidenceManifestVerification",
    # Feedback Learning - Sprint 100 EP-11 (4 models)
    "PRLearning",
    "DecompositionHint",
    "HintUsageLog",
    "LearningAggregation",
    # Governance System - Sprint 108 (14 models)
    "GovernanceSubmission",
    "GovernanceRejection",
    "EvidenceVaultEntry",
    "GovernanceAuditLog",
    "OwnershipRegistry",
    "QualityContract",
    "ContextAuthority",
    "GovernanceContextSnapshot",
    "ContractVersion",
    "ContractViolation",
    "AIAttestation",
    "HumanReview",
    "GovernanceException",
    "EscalationLog",
    # Consultation Request - Sprint 101 (1 model)
    "ConsultationRequest",
    # Framework Version - Sprint 101 (1 model)
    "FrameworkVersion",
    # Agentic Maturity - Sprint 104 (1 model)
    "AgenticMaturityAssessment",
    # Context Authority V2 - Sprint 120 SPEC-0011 (3 models)
    "ContextOverlayTemplate",
    "ContextSnapshotV2",
    "ContextOverlayApplication",
    # Compliance Validation - Sprint 123 SPEC-0013 (3 models + 2 enums)
    "ComplianceScore",
    "ComplianceIssue",
    "FolderCollisionCheck",
    "ComplianceCategory",
    "IssueSeverity",
    # GitHub Integration - Sprint 129 ADR-044 (2 models + 2 enums)
    "GitHubInstallation",
    "GitHubRepository",
    "InstallationStatus",
    "CloneStatus",
    # Product Telemetry - Sprint 147 Product Truth Layer (1 model + constants)
    "ProductEvent",
    "EventNames",
    # VCR - Sprint 151 SASE Artifacts (1 model + enum)
    "VersionControlledResolution",
    "VCRStatus",
    # Compliance Framework - Sprint 156 Phase 3 (5 models + 5 enums)
    "ComplianceFramework",
    "ComplianceControl",
    "ComplianceAssessment",
    "ComplianceRiskRegister",
    "ComplianceRACI",
    "ComplianceAssessmentStatus",
    "ControlSeverity",
    "RiskLikelihood",
    "RiskImpact",
    "RiskStatus",
    # NIST MAP & MEASURE - Sprint 157 Phase 3 (2 models + 3 enums)
    "AISystem",
    "PerformanceMetric",
    "AISystemType",
    "AIRiskLevel",
    "MetricType",
    # NIST MANAGE - Sprint 158 Phase 3 (2 models + 6 enums)
    "ManageRiskResponse",
    "ManageIncident",
    "ResponseType",
    "ResponseStatus",
    "ResponsePriority",
    "IncidentSeverity",
    "IncidentType",
    "IncidentStatus",
    # Tier-Based Gate Approval - Sprint 161 Phase 4 (2 models)
    "ProjectFunctionRole",
    "GateDecision",
]
