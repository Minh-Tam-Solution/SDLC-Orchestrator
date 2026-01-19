"""
=========================================================================
Lifecycle Events - SDLC Orchestrator Event Definitions
Sprint 83 - Dynamic Context Injector

Version: 1.0.0
Date: January 19, 2026
Status: ACTIVE - Sprint 83 (Dynamic Context & Analytics)
Authority: CTO Approved
Framework: SDLC 5.1.3 P7 (Documentation Permanence)

Purpose:
- Define strongly-typed lifecycle events
- Enable event-driven AGENTS.md updates
- Support analytics and audit trail

Event Types:
- GateStatusChanged: Gate passed/failed/pending
- SprintChanged: Sprint started/closed
- ConstraintDetected: Security/compliance constraint found
- AgentsMdUpdated: AGENTS.md regenerated and pushed
- EvidenceUploaded: New evidence added to vault
- SecurityScanCompleted: SAST/DAST scan finished

TRUE MOAT: Events trigger dynamic AGENTS.md updates
=========================================================================
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4


class GateStatus(str, Enum):
    """Gate status values."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    PASSED = "passed"
    FAILED = "failed"
    BLOCKED = "blocked"
    BYPASSED = "bypassed"


class SprintStatus(str, Enum):
    """Sprint status values."""

    PLANNING = "planning"
    ACTIVE = "active"
    REVIEW = "review"
    CLOSED = "closed"


class ConstraintSeverity(str, Enum):
    """Constraint severity levels."""

    CRITICAL = "critical"  # Block merge immediately
    HIGH = "high"  # Block merge, requires fix
    MEDIUM = "medium"  # Warning, should fix
    LOW = "low"  # Info, optional fix
    INFO = "info"  # Informational only


class ConstraintType(str, Enum):
    """Constraint type categories."""

    SECURITY = "security"  # CVE, vulnerability
    COMPLIANCE = "compliance"  # GDPR, SOC2, HIPAA
    QUALITY = "quality"  # Code quality, coverage
    ARCHITECTURE = "architecture"  # Design constraints
    DEPENDENCY = "dependency"  # License, version
    PERFORMANCE = "performance"  # Latency, memory


class ScanType(str, Enum):
    """Security scan types."""

    SAST = "sast"  # Static analysis (Semgrep)
    DAST = "dast"  # Dynamic analysis
    SCA = "sca"  # Software composition (Grype)
    SECRET = "secret"  # Secret scanning
    LICENSE = "license"  # License compliance


# =========================================================================
# Base Event
# =========================================================================


@dataclass
class LifecycleEvent:
    """
    Base class for all lifecycle events.

    All events include:
    - event_id: Unique identifier
    - timestamp: When the event occurred
    - source: What triggered the event
    - correlation_id: For tracing related events
    """

    event_id: UUID = field(default_factory=uuid4)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    source: str = "sdlc-orchestrator"
    correlation_id: Optional[UUID] = None


# =========================================================================
# Gate Events
# =========================================================================


@dataclass
class GateStatusChanged(LifecycleEvent):
    """
    Event fired when a gate status changes.

    Used by DynamicContextService to update AGENTS.md:
    - Gate passed → Update "Current Stage" section
    - Gate failed → Add constraints to "DO NOT" section
    - Gate bypassed → Add audit note

    Example:
        event = GateStatusChanged(
            project_id=project_id,
            gate_id="G2",
            new_status=GateStatus.PASSED,
            previous_status=GateStatus.IN_PROGRESS,
            changed_by=user_id,
        )
        await event_bus.publish(event)
    """

    project_id: UUID = field(default_factory=uuid4)
    gate_id: str = ""
    gate_name: str = ""
    new_status: GateStatus = GateStatus.PENDING
    previous_status: Optional[GateStatus] = None
    changed_by: UUID = field(default_factory=uuid4)
    reason: str = ""
    evidence_ids: List[UUID] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Set default source."""
        self.source = "gate-engine"


@dataclass
class GateEvaluationRequested(LifecycleEvent):
    """
    Event fired when gate evaluation is requested.

    Used for:
    - Triggering policy evaluation
    - Starting evidence collection
    - Initiating SAST scans
    """

    project_id: UUID = field(default_factory=uuid4)
    gate_id: str = ""
    requested_by: UUID = field(default_factory=uuid4)
    pr_number: Optional[int] = None
    commit_sha: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Set default source."""
        self.source = "gate-engine"


# =========================================================================
# Sprint Events
# =========================================================================


@dataclass
class SprintChanged(LifecycleEvent):
    """
    Event fired when sprint status changes.

    Used by DynamicContextService to update AGENTS.md:
    - Sprint started → Update "Current Sprint" section
    - Sprint closed → Archive sprint context

    Example:
        event = SprintChanged(
            project_id=project_id,
            sprint_id=sprint_id,
            sprint_name="Sprint 83",
            new_status=SprintStatus.ACTIVE,
            previous_status=SprintStatus.PLANNING,
        )
        await event_bus.publish(event)
    """

    project_id: UUID = field(default_factory=uuid4)
    sprint_id: UUID = field(default_factory=uuid4)
    sprint_name: str = ""
    sprint_number: int = 0
    new_status: SprintStatus = SprintStatus.PLANNING
    previous_status: Optional[SprintStatus] = None
    started_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    goals: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Set default source."""
        self.source = "sprint-manager"


# =========================================================================
# Constraint Events
# =========================================================================


@dataclass
class ConstraintDetected(LifecycleEvent):
    """
    Event fired when a constraint/issue is detected.

    Used by DynamicContextService to update AGENTS.md:
    - Critical constraint → Add to "BLOCKED" section
    - Security issue → Add to "DO NOT" section
    - Known issue → Add to "Known Issues" section

    Example:
        event = ConstraintDetected(
            project_id=project_id,
            constraint_type=ConstraintType.SECURITY,
            severity=ConstraintSeverity.CRITICAL,
            title="CVE-2024-12345 in lodash",
            description="Upgrade lodash to 4.17.21",
            affected_files=["package.json"],
        )
        await event_bus.publish(event)
    """

    project_id: UUID = field(default_factory=uuid4)
    constraint_id: UUID = field(default_factory=uuid4)
    constraint_type: ConstraintType = ConstraintType.SECURITY
    severity: ConstraintSeverity = ConstraintSeverity.MEDIUM
    title: str = ""
    description: str = ""
    affected_files: List[str] = field(default_factory=list)
    rule_id: Optional[str] = None  # e.g., Semgrep rule ID
    cve_id: Optional[str] = None  # e.g., CVE-2024-12345
    remediation: Optional[str] = None  # How to fix
    auto_fixable: bool = False
    blocking: bool = False  # Should this block merge?
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Set default source and blocking flag."""
        self.source = "constraint-detector"
        # Critical and high severity constraints block by default
        if self.severity in (ConstraintSeverity.CRITICAL, ConstraintSeverity.HIGH):
            self.blocking = True


@dataclass
class ConstraintResolved(LifecycleEvent):
    """
    Event fired when a constraint is resolved.

    Used to:
    - Remove constraint from AGENTS.md
    - Update gate status
    - Record remediation in audit trail
    """

    project_id: UUID = field(default_factory=uuid4)
    constraint_id: UUID = field(default_factory=uuid4)
    resolved_by: UUID = field(default_factory=uuid4)
    resolution: str = ""  # How it was fixed
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Set default source."""
        self.source = "constraint-detector"


# =========================================================================
# AGENTS.md Events
# =========================================================================


@dataclass
class AgentsMdUpdated(LifecycleEvent):
    """
    Event fired when AGENTS.md is updated.

    Used for:
    - Audit trail (who changed what when)
    - Analytics (update frequency)
    - Notifications (stakeholder alerts)

    Example:
        event = AgentsMdUpdated(
            project_id=project_id,
            repository_id=repo_id,
            trigger_event="GateStatusChanged",
            sections_updated=["Current Stage", "Constraints"],
            commit_sha="abc123",
        )
        await event_bus.publish(event)
    """

    project_id: UUID = field(default_factory=uuid4)
    repository_id: UUID = field(default_factory=uuid4)
    repository_full_name: str = ""  # e.g., "org/repo"
    trigger_event: str = ""  # What caused the update
    trigger_event_id: Optional[UUID] = None
    sections_updated: List[str] = field(default_factory=list)
    previous_hash: Optional[str] = None  # SHA256 of previous content
    new_hash: str = ""  # SHA256 of new content
    commit_sha: Optional[str] = None  # Git commit SHA
    pr_number: Optional[int] = None  # If via PR
    updated_by: UUID = field(default_factory=uuid4)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Set default source."""
        self.source = "dynamic-context-service"


@dataclass
class AgentsMdValidated(LifecycleEvent):
    """
    Event fired when AGENTS.md is validated.

    Used for:
    - Compliance checking
    - Structure enforcement
    - Quality metrics
    """

    project_id: UUID = field(default_factory=uuid4)
    repository_id: UUID = field(default_factory=uuid4)
    is_valid: bool = True
    validation_errors: List[str] = field(default_factory=list)
    validation_warnings: List[str] = field(default_factory=list)
    line_count: int = 0
    section_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Set default source."""
        self.source = "agents-md-validator"


# =========================================================================
# Evidence Events
# =========================================================================


@dataclass
class EvidenceUploaded(LifecycleEvent):
    """
    Event fired when evidence is uploaded to vault.

    Used for:
    - Triggering gate evaluation
    - Updating manifest hash chain
    - Analytics (evidence volume)
    """

    project_id: UUID = field(default_factory=uuid4)
    evidence_id: UUID = field(default_factory=uuid4)
    gate_id: str = ""
    file_name: str = ""
    file_path: str = ""  # S3 path
    sha256_hash: str = ""
    size_bytes: int = 0
    content_type: str = ""
    uploaded_by: UUID = field(default_factory=uuid4)
    manifest_id: Optional[UUID] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Set default source."""
        self.source = "evidence-vault"


@dataclass
class EvidenceDeleted(LifecycleEvent):
    """
    Event fired when evidence is deleted (soft delete).

    Used for:
    - Audit trail
    - GDPR compliance tracking
    """

    project_id: UUID = field(default_factory=uuid4)
    evidence_id: UUID = field(default_factory=uuid4)
    deleted_by: UUID = field(default_factory=uuid4)
    reason: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Set default source."""
        self.source = "evidence-vault"


# =========================================================================
# Security Scan Events
# =========================================================================


@dataclass
class SecurityScanCompleted(LifecycleEvent):
    """
    Event fired when a security scan completes.

    Used by DynamicContextService to:
    - Update AGENTS.md with findings
    - Block merge if critical issues found
    - Add remediation guidance

    Example:
        event = SecurityScanCompleted(
            project_id=project_id,
            scan_type=ScanType.SAST,
            scanner="semgrep",
            findings_critical=0,
            findings_high=2,
            findings_medium=5,
        )
        await event_bus.publish(event)
    """

    project_id: UUID = field(default_factory=uuid4)
    scan_id: UUID = field(default_factory=uuid4)
    scan_type: ScanType = ScanType.SAST
    scanner: str = ""  # e.g., "semgrep", "grype"
    scan_duration_ms: int = 0
    files_scanned: int = 0
    findings_critical: int = 0
    findings_high: int = 0
    findings_medium: int = 0
    findings_low: int = 0
    findings_info: int = 0
    passed: bool = True  # Did scan pass policy threshold?
    commit_sha: Optional[str] = None
    pr_number: Optional[int] = None
    report_path: Optional[str] = None  # Path to detailed report
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Set default source and passed flag."""
        self.source = "security-scanner"
        # Fail if any critical or high findings
        if self.findings_critical > 0 or self.findings_high > 0:
            self.passed = False


# =========================================================================
# Policy Events
# =========================================================================


@dataclass
class PolicyEvaluated(LifecycleEvent):
    """
    Event fired when OPA policy is evaluated.

    Used for:
    - Gate status updates
    - Policy analytics
    - Compliance reporting
    """

    project_id: UUID = field(default_factory=uuid4)
    policy_pack: str = ""  # e.g., "sdlc-standard"
    rules_evaluated: int = 0
    rules_passed: int = 0
    rules_failed: int = 0
    rules_skipped: int = 0
    passed: bool = True
    failed_rules: List[str] = field(default_factory=list)
    evaluation_duration_ms: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Set default source."""
        self.source = "policy-engine"


# =========================================================================
# Event Registry (for discovery)
# =========================================================================

EVENT_REGISTRY = {
    # Gate Events
    "GateStatusChanged": GateStatusChanged,
    "GateEvaluationRequested": GateEvaluationRequested,
    # Sprint Events
    "SprintChanged": SprintChanged,
    # Constraint Events
    "ConstraintDetected": ConstraintDetected,
    "ConstraintResolved": ConstraintResolved,
    # AGENTS.md Events
    "AgentsMdUpdated": AgentsMdUpdated,
    "AgentsMdValidated": AgentsMdValidated,
    # Evidence Events
    "EvidenceUploaded": EvidenceUploaded,
    "EvidenceDeleted": EvidenceDeleted,
    # Security Events
    "SecurityScanCompleted": SecurityScanCompleted,
    # Policy Events
    "PolicyEvaluated": PolicyEvaluated,
}


def get_event_class(event_name: str) -> Optional[type]:
    """Get event class by name."""
    return EVENT_REGISTRY.get(event_name)


def get_all_event_types() -> List[str]:
    """Get all registered event type names."""
    return list(EVENT_REGISTRY.keys())
