"""
=========================================================================
Enforcement Strategy - Unified Governance Enforcement (Strategy Pattern)
SDLC Orchestrator - Sprint 173 (Governance Loop Completion)

Version: 1.0.0
Date: February 15, 2026
Status: ACTIVE
Authority: CTO + Backend Lead Approved
Framework: SDLC 6.0.5 Quality Assurance System

Sprint 173 Consolidation:
- Merged SoftModeEnforcer + FullModeEnforcer into Strategy pattern
- Pure decision engines (no side effects in decide methods)
- soft_mode_enforcer.py and full_mode_enforcer.py are facades for 1 sprint

Enforcement Strategies:
- SoftEnforcement: Block CRITICAL only, warn ORANGE, auto-approve GREEN
- FullEnforcement: Strict zone-based approval (Tech Lead / CEO / CTO+CEO)

Zero Mock Policy: Real enforcement with configurable rules
=========================================================================
"""

import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from fnmatch import fnmatch
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import yaml

from app.services.governance.signals_engine import (
    CodeSubmission,
    IndexCategory,
    RoutingDecision,
    SignalType,
    VibecodingIndex,
)

logger = logging.getLogger(__name__)


# ============================================================================
# Enums
# ============================================================================


class EnforcementAction(str, Enum):
    """Enforcement actions."""

    BLOCKED = "blocked"
    WARNED = "warned"
    APPROVED = "approved"
    AUTO_APPROVED = "auto_approved"


class ExemptionType(str, Enum):
    """Types of exemptions that can be applied."""

    DEPENDENCY_UPDATE = "dependency_update_exemption"
    DOCUMENTATION_SAFE = "documentation_safe_pattern"
    TEST_ONLY = "test_only_pattern"


class OverrideAuthority(str, Enum):
    """Authorities that can override blocks."""

    CTO = "CTO"
    CEO = "CEO"
    SECURITY_LEAD = "Security Lead"


class ApprovalRequirement(str, Enum):
    """Approval requirements for FULL mode."""

    NONE = "none"
    TECH_LEAD = "tech_lead"
    CEO = "ceo"
    CTO_CEO = "cto_ceo"


class ApprovalStatus(str, Enum):
    """Status of approval request."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    ESCALATED = "escalated"


# ============================================================================
# Data Classes
# ============================================================================


@dataclass
class ExemptionResult:
    """Result of exemption rule evaluation."""

    applied: bool
    exemption_type: Optional[ExemptionType] = None
    message: str = ""
    adjustments: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BlockRuleResult:
    """Result of block rule evaluation."""

    rule_name: str
    triggered: bool
    message: str = ""
    override_allowed: bool = False
    override_requires: List[str] = field(default_factory=list)


@dataclass
class WarnRuleResult:
    """Result of warn rule evaluation."""

    rule_name: str
    triggered: bool
    message: str = ""


@dataclass
class EnforcementResult:
    """
    Complete enforcement decision for a PR.

    This is the main output of enforcement strategies.
    """

    action: EnforcementAction
    vibecoding_index: VibecodingIndex
    exemptions_applied: List[ExemptionResult] = field(default_factory=list)
    block_rules_triggered: List[BlockRuleResult] = field(default_factory=list)
    warn_rules_triggered: List[WarnRuleResult] = field(default_factory=list)
    can_merge: bool = True
    requires_override: bool = False
    override_authority: List[str] = field(default_factory=list)
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    evaluated_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "enforcement": {
                "action": self.action.value,
                "can_merge": self.can_merge,
                "requires_override": self.requires_override,
                "override_authority": self.override_authority,
                "message": self.message,
            },
            "vibecoding_index": self.vibecoding_index.to_dict(),
            "exemptions": [
                {
                    "applied": e.applied,
                    "type": e.exemption_type.value if e.exemption_type else None,
                    "message": e.message,
                    "adjustments": e.adjustments,
                }
                for e in self.exemptions_applied
                if e.applied
            ],
            "block_rules": [
                {
                    "rule": r.rule_name,
                    "triggered": r.triggered,
                    "message": r.message,
                    "override_allowed": r.override_allowed,
                    "override_requires": r.override_requires,
                }
                for r in self.block_rules_triggered
                if r.triggered
            ],
            "warnings": [
                {"rule": w.rule_name, "message": w.message}
                for w in self.warn_rules_triggered
                if w.triggered
            ],
            "evaluated_at": self.evaluated_at.isoformat(),
        }

    @property
    def blocked(self) -> bool:
        """Whether the PR is blocked."""
        return self.action == EnforcementAction.BLOCKED

    @property
    def warned(self) -> bool:
        """Whether the PR has warnings."""
        return self.action == EnforcementAction.WARNED

    @property
    def block_reasons(self) -> List[str]:
        """List of reasons for blocking."""
        return [r.message for r in self.block_rules_triggered if r.triggered and r.message]

    @property
    def warn_reasons(self) -> List[str]:
        """List of warning reasons."""
        return [w.message for w in self.warn_rules_triggered if w.triggered and w.message]

    @property
    def exemptions_applied_list(self) -> List[str]:
        """List of applied exemption names."""
        return [
            e.exemption_type.value for e in self.exemptions_applied
            if e.applied and e.exemption_type
        ]


@dataclass
class ApprovalRequest:
    """Request for approval in FULL mode."""

    id: str
    pr_number: int
    zone: IndexCategory
    vibecoding_index: float
    required_approvers: List[str]
    requested_at: datetime
    timeout_hours: int
    status: ApprovalStatus = ApprovalStatus.PENDING
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None


@dataclass
class CEOTimeEntry:
    """Track CEO time spent on governance activities."""

    id: str
    activity_type: str
    pr_number: Optional[int]
    duration_minutes: float
    category: str
    recorded_at: datetime
    notes: Optional[str] = None


@dataclass
class FullModeEnforcementResult(EnforcementResult):
    """Extended enforcement result for FULL mode."""

    approval_required: bool = False
    approval_type: ApprovalRequirement = ApprovalRequirement.NONE
    approval_request: Optional[ApprovalRequest] = None
    ceo_review_required: bool = False
    estimated_review_time_minutes: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        base_dict = super().to_dict()
        base_dict.update({
            "full_mode": {
                "approval_required": self.approval_required,
                "approval_type": self.approval_type.value,
                "ceo_review_required": self.ceo_review_required,
                "estimated_review_time_minutes": self.estimated_review_time_minutes,
            }
        })
        return base_dict


# ============================================================================
# Abstract Strategy
# ============================================================================


class EnforcementStrategy(ABC):
    """
    Pure decision engine for governance enforcement.

    Subclasses implement SOFT or FULL enforcement logic without side effects.
    Side effects (approval workflows, persistence, notifications) are handled
    by the GovernanceModeService that delegates to these strategies.
    """

    @abstractmethod
    def decide(
        self,
        vibecoding_index: VibecodingIndex,
        submission: CodeSubmission,
        has_ownership: bool = True,
        has_intent: bool = True,
        security_scan_critical: int = 0,
        has_adr_linkage: bool = True,
        test_coverage: float = 80.0,
    ) -> EnforcementResult:
        """Make enforcement decision (pure function, no side effects)."""
        ...

    @abstractmethod
    def check_exemptions(
        self,
        submission: CodeSubmission,
    ) -> List[ExemptionResult]:
        """Evaluate exemption rules for a submission."""
        ...


# ============================================================================
# Shared Logic Mixin
# ============================================================================


class _ExemptionEvaluator:
    """
    Shared exemption evaluation logic used by both strategies.

    Extracted to avoid duplication between Soft and Full enforcement.
    """

    def __init__(self, config: Dict[str, Any]):
        self._config = config
        self._dependency_files: Set[str] = set(
            config.get("exemptions", {})
            .get("dependency_update_exemption", {})
            .get("trigger_files", [])
        )
        self._doc_patterns: List[str] = (
            config.get("exemptions", {})
            .get("documentation_safe_pattern", {})
            .get("trigger_paths", [])
        )
        self._test_patterns: List[str] = (
            config.get("exemptions", {})
            .get("test_only_pattern", {})
            .get("trigger_paths", [])
        )

    def evaluate_exemptions(
        self, submission: CodeSubmission
    ) -> List[ExemptionResult]:
        """Evaluate all exemption rules for a submission."""
        return [
            self._check_dependency_exemption(submission),
            self._check_documentation_exemption(submission),
            self._check_test_only_exemption(submission),
        ]

    def _check_dependency_exemption(
        self, submission: CodeSubmission
    ) -> ExemptionResult:
        """Check if dependency update exemption applies."""
        exemption_config = self._config.get("exemptions", {}).get(
            "dependency_update_exemption", {}
        )

        if not exemption_config.get("enabled", False):
            return ExemptionResult(applied=False)

        changed_basenames = [Path(f).name for f in submission.changed_files]
        all_dependency_files = all(
            basename in self._dependency_files for basename in changed_basenames
        )

        if not all_dependency_files:
            return ExemptionResult(applied=False)

        non_lock_lines = submission.added_lines
        for f in submission.changed_files:
            if "lock" in f.lower():
                continue

        max_lines = exemption_config.get("conditions", {}).get("max_non_lock_lines", 50)
        if non_lock_lines > max_lines:
            return ExemptionResult(
                applied=False,
                message=f"Too many non-lock lines ({non_lock_lines} > {max_lines})",
            )

        effect = exemption_config.get("effect", {})
        return ExemptionResult(
            applied=True,
            exemption_type=ExemptionType.DEPENDENCY_UPDATE,
            message=effect.get("auto_message", "Dependency update exemption applied"),
            adjustments={
                "drift_velocity_multiplier": effect.get("drift_velocity_multiplier", 0.5),
                "max_index_cap": effect.get("max_index_cap", 40),
            },
        )

    def _check_documentation_exemption(
        self, submission: CodeSubmission
    ) -> ExemptionResult:
        """Check if documentation safe pattern applies."""
        exemption_config = self._config.get("exemptions", {}).get(
            "documentation_safe_pattern", {}
        )

        if not exemption_config.get("enabled", False):
            return ExemptionResult(applied=False)

        all_docs = all(
            self._matches_patterns(f, self._doc_patterns)
            for f in submission.changed_files
        )

        if not all_docs:
            return ExemptionResult(applied=False)

        effect = exemption_config.get("effect", {})
        return ExemptionResult(
            applied=True,
            exemption_type=ExemptionType.DOCUMENTATION_SAFE,
            message=effect.get("auto_message", "Documentation-only PR - auto-approved"),
            adjustments={
                "force_zone": effect.get("force_zone", "green"),
                "auto_approve": effect.get("auto_approve", True),
                "max_index_required": exemption_config.get("conditions", {}).get("max_index", 25),
            },
        )

    def _check_test_only_exemption(
        self, submission: CodeSubmission
    ) -> ExemptionResult:
        """Check if test-only pattern applies."""
        exemption_config = self._config.get("exemptions", {}).get(
            "test_only_pattern", {}
        )

        if not exemption_config.get("enabled", False):
            return ExemptionResult(applied=False)

        all_tests = all(
            self._matches_patterns(f, self._test_patterns)
            for f in submission.changed_files
        )

        if not all_tests:
            return ExemptionResult(applied=False)

        effect = exemption_config.get("effect", {})
        return ExemptionResult(
            applied=True,
            exemption_type=ExemptionType.TEST_ONLY,
            message=effect.get("auto_message", "Test-only PR - reduced scrutiny applied"),
            adjustments={
                "abstraction_complexity_multiplier": effect.get(
                    "abstraction_complexity_multiplier", 0.5
                ),
                "ai_dependency_multiplier": effect.get("ai_dependency_multiplier", 0.7),
                "max_index_required": exemption_config.get("conditions", {}).get("max_index", 50),
            },
        )

    @staticmethod
    def _matches_patterns(file_path: str, patterns: List[str]) -> bool:
        """Check if file path matches any of the glob patterns."""
        for pattern in patterns:
            if fnmatch(file_path, pattern):
                return True
            if fnmatch(Path(file_path).name, pattern):
                return True
        return False


def _apply_exemption_adjustments(
    index: VibecodingIndex,
    exemptions: List[ExemptionResult],
) -> VibecodingIndex:
    """Apply exemption adjustments to the Vibecoding Index."""
    adjusted_score = index.score

    for exemption in exemptions:
        if not exemption.applied:
            continue

        adjustments = exemption.adjustments

        if "max_index_cap" in adjustments:
            cap = adjustments["max_index_cap"]
            if adjusted_score > cap:
                adjusted_score = cap
                logger.info(f"Index capped to {cap} by {exemption.exemption_type}")

        if adjustments.get("force_zone") == "green":
            max_index_required = adjustments.get("max_index_required", 25)
            if index.score <= max_index_required:
                adjusted_score = min(adjusted_score, 25)
                logger.info(
                    f"Index forced to green zone by {exemption.exemption_type}"
                )

    if adjusted_score <= 30:
        category = IndexCategory.GREEN
        routing = RoutingDecision.AUTO_APPROVE
    elif adjusted_score <= 60:
        category = IndexCategory.YELLOW
        routing = RoutingDecision.TECH_LEAD_REVIEW
    elif adjusted_score <= 80:
        category = IndexCategory.ORANGE
        routing = RoutingDecision.CEO_SHOULD_REVIEW
    else:
        category = IndexCategory.RED
        routing = RoutingDecision.CEO_MUST_REVIEW

    return VibecodingIndex(
        score=adjusted_score,
        category=category,
        routing=routing,
        signals=index.signals,
        critical_override=index.critical_override,
        critical_matches=index.critical_matches,
        original_score=index.score,
        suggested_focus=index.suggested_focus,
        flags=index.flags + [
            f"exemption_adjusted:{e.exemption_type.value}"
            for e in exemptions if e.applied
        ],
    )


# ============================================================================
# SOFT Enforcement Strategy
# ============================================================================


class SoftEnforcement(EnforcementStrategy):
    """
    SOFT mode enforcement strategy.

    Rules:
    - RED (81-100): BLOCKED (CTO override required)
    - ORANGE (61-80): WARNED (CEO review recommended)
    - YELLOW (31-60): PASSED (Tech Lead review suggested)
    - GREEN (0-30): AUTO-APPROVED
    """

    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self._evaluator = _ExemptionEvaluator(self.config)

    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """Load governance configuration."""
        if config_path:
            path = Path(config_path)
        else:
            path = Path(__file__).parent.parent.parent / "config" / "governance_soft_mode.yaml"

        if path.exists():
            with open(path) as f:
                return yaml.safe_load(f)
        else:
            logger.warning(f"Config not found at {path}, using defaults")
            return self._default_config()

    def _default_config(self) -> Dict[str, Any]:
        """Return default configuration."""
        return {
            "governance": {"mode": "soft"},
            "signal_weights": {
                "architectural_smell": 0.25,
                "abstraction_complexity": 0.15,
                "ai_dependency_ratio": 0.20,
                "change_surface_area": 0.25,
                "drift_velocity": 0.15,
            },
            "exemptions": {
                "dependency_update_exemption": {
                    "enabled": True,
                    "trigger_files": [
                        "package.json",
                        "package-lock.json",
                        "requirements.txt",
                        "poetry.lock",
                    ],
                },
                "documentation_safe_pattern": {
                    "enabled": True,
                    "trigger_paths": ["docs/**", "*.md"],
                },
                "test_only_pattern": {
                    "enabled": True,
                    "trigger_paths": ["tests/**", "**/test_*.py"],
                },
            },
        }

    def get_adjusted_weights(self) -> Dict[SignalType, float]:
        """Get signal weights adjusted for SOFT mode."""
        weights_config = self.config.get("signal_weights", {})
        return {
            SignalType.ARCHITECTURAL_SMELL: weights_config.get("architectural_smell", 0.25),
            SignalType.ABSTRACTION_COMPLEXITY: weights_config.get("abstraction_complexity", 0.15),
            SignalType.AI_DEPENDENCY_RATIO: weights_config.get("ai_dependency_ratio", 0.20),
            SignalType.CHANGE_SURFACE_AREA: weights_config.get("change_surface_area", 0.25),
            SignalType.DRIFT_VELOCITY: weights_config.get("drift_velocity", 0.15),
        }

    def check_exemptions(
        self, submission: CodeSubmission
    ) -> List[ExemptionResult]:
        """Evaluate all exemption rules for a submission."""
        return self._evaluator.evaluate_exemptions(submission)

    def decide(
        self,
        vibecoding_index: VibecodingIndex,
        submission: CodeSubmission,
        has_ownership: bool = True,
        has_intent: bool = True,
        security_scan_critical: int = 0,
        has_adr_linkage: bool = True,
        test_coverage: float = 80.0,
    ) -> EnforcementResult:
        """
        SOFT mode enforcement decision.

        Args:
            vibecoding_index: Calculated Vibecoding Index
            submission: Code submission details
            has_ownership: Whether PR has @owner annotation
            has_intent: Whether PR has intent statement
            security_scan_critical: Number of critical security issues
            has_adr_linkage: Whether new features have ADR linkage
            test_coverage: Test coverage percentage

        Returns:
            EnforcementResult with action, rules triggered, and merge decision
        """
        exemptions = self.check_exemptions(submission)
        applied_exemptions = [e for e in exemptions if e.applied]

        adjusted_index = _apply_exemption_adjustments(
            vibecoding_index, applied_exemptions
        )

        block_results = self._evaluate_block_rules(
            adjusted_index, has_ownership, has_intent, security_scan_critical,
        )
        triggered_blocks = [b for b in block_results if b.triggered]

        warn_results = self._evaluate_warn_rules(
            adjusted_index, has_adr_linkage, submission.is_new_feature, test_coverage,
        )
        triggered_warns = [w for w in warn_results if w.triggered]

        action, can_merge, requires_override, override_authority, message = (
            self._determine_action(
                adjusted_index, triggered_blocks, triggered_warns, applied_exemptions
            )
        )

        return EnforcementResult(
            action=action,
            vibecoding_index=adjusted_index,
            exemptions_applied=exemptions,
            block_rules_triggered=block_results,
            warn_rules_triggered=warn_results,
            can_merge=can_merge,
            requires_override=requires_override,
            override_authority=override_authority,
            message=message,
            details={
                "original_index": vibecoding_index.score,
                "adjusted_index": adjusted_index.score,
                "exemptions_count": len(applied_exemptions),
                "blocks_count": len(triggered_blocks),
                "warns_count": len(triggered_warns),
            },
        )

    def _evaluate_block_rules(
        self,
        index: VibecodingIndex,
        has_ownership: bool,
        has_intent: bool,
        security_critical: int,
    ) -> List[BlockRuleResult]:
        """Evaluate block rules."""
        results = []

        results.append(
            BlockRuleResult(
                rule_name="vibecoding_index_red",
                triggered=index.score >= 81,
                message=f"PR blocked: Vibecoding Index {index.score:.1f} exceeds threshold (81)"
                if index.score >= 81
                else "",
                override_allowed=True,
                override_requires=["CTO"],
            )
        )

        results.append(
            BlockRuleResult(
                rule_name="missing_ownership",
                triggered=not has_ownership,
                message="PR blocked: Missing @owner annotation",
                override_allowed=False,
                override_requires=[],
            )
        )

        results.append(
            BlockRuleResult(
                rule_name="missing_intent",
                triggered=not has_intent,
                message="PR blocked: Missing intent statement",
                override_allowed=False,
                override_requires=[],
            )
        )

        results.append(
            BlockRuleResult(
                rule_name="security_scan_fail",
                triggered=security_critical > 0,
                message=f"PR blocked: {security_critical} critical security vulnerabilities detected",
                override_allowed=True,
                override_requires=["CTO", "Security Lead"],
            )
        )

        return results

    def _evaluate_warn_rules(
        self,
        index: VibecodingIndex,
        has_adr_linkage: bool,
        is_new_feature: bool,
        test_coverage: float,
    ) -> List[WarnRuleResult]:
        """Evaluate warn rules."""
        results = []

        results.append(
            WarnRuleResult(
                rule_name="vibecoding_index_orange",
                triggered=61 <= index.score <= 80,
                message=f"Warning: Vibecoding Index {index.score:.1f} in orange zone. CEO review recommended.",
            )
        )

        results.append(
            WarnRuleResult(
                rule_name="missing_adr_linkage",
                triggered=is_new_feature and not has_adr_linkage,
                message="Warning: New feature without ADR linkage",
            )
        )

        results.append(
            WarnRuleResult(
                rule_name="low_test_coverage",
                triggered=test_coverage < 80,
                message=f"Warning: Test coverage {test_coverage:.1f}% below 80% target",
            )
        )

        return results

    # Backward-compatible aliases (old SoftModeEnforcer used these names)
    enforce = decide
    evaluate_exemptions = check_exemptions

    def _determine_action(
        self,
        index: VibecodingIndex,
        blocks: List[BlockRuleResult],
        warns: List[WarnRuleResult],
        exemptions: List[ExemptionResult],
    ) -> tuple:
        """Determine final enforcement action."""
        non_overridable = [b for b in blocks if not b.override_allowed]
        if non_overridable:
            return (
                EnforcementAction.BLOCKED, False, False, [],
                non_overridable[0].message,
            )

        overridable = [b for b in blocks if b.override_allowed]
        if overridable:
            all_authorities: List[str] = []
            for b in overridable:
                all_authorities.extend(b.override_requires)
            unique_authorities = list(set(all_authorities))
            return (
                EnforcementAction.BLOCKED, False, True, unique_authorities,
                overridable[0].message,
            )

        for e in exemptions:
            if e.adjustments.get("auto_approve"):
                return (
                    EnforcementAction.AUTO_APPROVED, True, False, [],
                    e.message,
                )

        if warns:
            warning_messages = [w.message for w in warns]
            return (
                EnforcementAction.WARNED, True, False, [],
                "; ".join(warning_messages),
            )

        if index.category == IndexCategory.GREEN:
            return (
                EnforcementAction.AUTO_APPROVED, True, False, [],
                f"Auto-approved: Vibecoding Index {index.score:.1f} in green zone",
            )

        if index.category == IndexCategory.YELLOW:
            return (
                EnforcementAction.APPROVED, True, False, [],
                f"Approved: Vibecoding Index {index.score:.1f} in yellow zone. Tech Lead review suggested.",
            )

        return (
            EnforcementAction.APPROVED, True, False, [],
            f"Approved: Vibecoding Index {index.score:.1f}",
        )


# ============================================================================
# FULL Enforcement Strategy
# ============================================================================


class FullEnforcement(EnforcementStrategy):
    """
    FULL mode enforcement strategy.

    Stricter than SOFT:
    - GREEN (0-30): AUTO-APPROVED (no review)
    - YELLOW (31-60): REQUIRES Tech Lead approval
    - ORANGE (61-80): REQUIRES CEO approval
    - RED (81-100): BLOCKED (CTO+CEO override required)

    Also integrates CEO time tracking for measuring governance impact.
    """

    def __init__(self, config_path: Optional[str] = None):
        # Use SoftEnforcement internally for shared logic
        self._soft = SoftEnforcement(config_path)
        self.full_config = self._load_full_config(config_path)

        # Approval tracking
        self._pending_approvals: Dict[str, ApprovalRequest] = {}

        # CEO time tracking
        self._ceo_time_entries: List[CEOTimeEntry] = []
        self._ceo_time_baseline = self.full_config.get(
            "ceo_time_tracking", {}
        ).get("baseline_hours_per_week", 40)
        self._ceo_time_target = self.full_config.get(
            "ceo_time_tracking", {}
        ).get("target_hours_per_week", 10)

    def _load_full_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load FULL mode configuration."""
        default_path = Path(__file__).parent.parent.parent / "config" / "governance_full_mode.yaml"
        path = Path(config_path) if config_path else default_path

        try:
            with open(path, "r") as f:
                config = yaml.safe_load(f)
                logger.info(f"Loaded FULL mode config from {path}")
                return config
        except FileNotFoundError:
            logger.warning(f"FULL mode config not found at {path}, using defaults")
            return self._get_default_full_config()

    def _get_default_full_config(self) -> Dict[str, Any]:
        """Get default FULL mode configuration."""
        return {
            "mode": "full",
            "zone_thresholds": {
                "green": {"min": 0, "max": 30, "action": "auto_approve"},
                "yellow": {"min": 31, "max": 60, "action": "require_approval", "review": "tech_lead"},
                "orange": {"min": 61, "max": 80, "action": "require_approval", "review": "ceo"},
                "red": {"min": 81, "max": 100, "action": "blocked", "review": "cto_ceo"},
            },
            "approval_rules": {
                "yellow_zone_tech_lead": {
                    "enabled": True, "zone": "yellow",
                    "requires": ["Tech Lead"], "timeout_hours": 24,
                },
                "orange_zone_ceo": {
                    "enabled": True, "zone": "orange",
                    "requires": ["CEO"], "timeout_hours": 48,
                },
            },
            "ceo_time_tracking": {
                "enabled": True,
                "baseline_hours_per_week": 40,
                "target_hours_per_week": 10,
            },
            "kill_switch": {
                "rejection_rate": {"threshold": 0.5},
                "false_positive_rate": {"threshold": 0.15},
            },
        }

    def check_exemptions(
        self, submission: CodeSubmission
    ) -> List[ExemptionResult]:
        """Evaluate exemptions (delegates to soft strategy)."""
        return self._soft.check_exemptions(submission)

    def decide(
        self,
        vibecoding_index: VibecodingIndex,
        submission: CodeSubmission,
        has_ownership: bool = True,
        has_intent: bool = True,
        security_scan_critical: int = 0,
        has_adr_linkage: bool = True,
        test_coverage: float = 80.0,
    ) -> EnforcementResult:
        """FULL mode enforcement decision (without coverage_delta)."""
        return self.decide_full(
            vibecoding_index=vibecoding_index,
            submission=submission,
            has_ownership=has_ownership,
            has_intent=has_intent,
            security_scan_critical=security_scan_critical,
            has_adr_linkage=has_adr_linkage,
            test_coverage=test_coverage,
            coverage_delta=0.0,
        )

    def decide_full(
        self,
        vibecoding_index: VibecodingIndex,
        submission: CodeSubmission,
        has_ownership: bool = True,
        has_intent: bool = True,
        security_scan_critical: int = 0,
        has_adr_linkage: bool = True,
        test_coverage: float = 80.0,
        coverage_delta: float = 0.0,
    ) -> FullModeEnforcementResult:
        """
        FULL mode enforcement with approval requirements.

        Args:
            vibecoding_index: Calculated Vibecoding Index
            submission: Code submission details
            has_ownership: Whether PR has @owner annotation
            has_intent: Whether PR has intent statement
            security_scan_critical: Number of critical security issues
            has_adr_linkage: Whether new features have ADR linkage
            test_coverage: Test coverage percentage
            coverage_delta: Change in test coverage (negative = drop)

        Returns:
            FullModeEnforcementResult with action, approvals, and CEO time estimate
        """
        soft_result = self._soft.decide(
            vibecoding_index=vibecoding_index,
            submission=submission,
            has_ownership=has_ownership,
            has_intent=has_intent,
            security_scan_critical=security_scan_critical,
            has_adr_linkage=has_adr_linkage,
            test_coverage=test_coverage,
        )

        coverage_block = self._check_coverage_drop(coverage_delta)
        if coverage_block.triggered:
            soft_result.block_rules_triggered.append(coverage_block)

        adjusted_index = soft_result.vibecoding_index
        approval_required = False
        approval_type = ApprovalRequirement.NONE
        ceo_review_required = False
        estimated_review_time = 0.0

        if adjusted_index.category == IndexCategory.YELLOW:
            approval_required = True
            approval_type = ApprovalRequirement.TECH_LEAD
            estimated_review_time = 15.0

        elif adjusted_index.category == IndexCategory.ORANGE:
            approval_required = True
            approval_type = ApprovalRequirement.CEO
            ceo_review_required = True
            estimated_review_time = 30.0

        elif adjusted_index.category == IndexCategory.RED:
            approval_required = True
            approval_type = ApprovalRequirement.CTO_CEO
            ceo_review_required = True
            estimated_review_time = 60.0

        action, can_merge, message = self._determine_full_mode_action(
            soft_result, approval_required, approval_type, coverage_block
        )

        approval_request = None
        if approval_required and action != EnforcementAction.BLOCKED:
            approval_request = self._create_approval_request(
                pr_number=getattr(submission, 'pr_number', 0),
                zone=adjusted_index.category,
                vibecoding_index=adjusted_index.score,
                approval_type=approval_type,
            )

        return FullModeEnforcementResult(
            action=action,
            vibecoding_index=adjusted_index,
            exemptions_applied=soft_result.exemptions_applied,
            block_rules_triggered=soft_result.block_rules_triggered,
            warn_rules_triggered=soft_result.warn_rules_triggered,
            can_merge=can_merge,
            requires_override=soft_result.requires_override,
            override_authority=soft_result.override_authority,
            message=message,
            details=soft_result.details,
            approval_required=approval_required,
            approval_type=approval_type,
            approval_request=approval_request,
            ceo_review_required=ceo_review_required,
            estimated_review_time_minutes=estimated_review_time,
        )

    # Backward-compatible aliases (old FullModeEnforcer used these names)
    enforce = decide
    enforce_full = decide_full

    def _check_coverage_drop(self, coverage_delta: float) -> BlockRuleResult:
        """Check if coverage dropped below threshold."""
        threshold = self.full_config.get("block_rules", {}).get(
            "coverage_drop", {}
        ).get("threshold", -5)

        triggered = coverage_delta < threshold

        return BlockRuleResult(
            rule_name="coverage_drop",
            triggered=triggered,
            message=f"PR blocked: Test coverage dropped by {abs(coverage_delta):.1f}% (threshold: {abs(threshold)}%)"
            if triggered else "",
            override_allowed=True,
            override_requires=["Tech Lead"],
        )

    def _determine_full_mode_action(
        self,
        soft_result: EnforcementResult,
        approval_required: bool,
        approval_type: ApprovalRequirement,
        coverage_block: BlockRuleResult,
    ) -> tuple:
        """Determine final action for FULL mode."""
        all_blocks = [
            b for b in soft_result.block_rules_triggered if b.triggered
        ]
        if coverage_block.triggered:
            all_blocks.append(coverage_block)

        if all_blocks:
            return (EnforcementAction.BLOCKED, False, all_blocks[0].message)

        if approval_required:
            if approval_type == ApprovalRequirement.TECH_LEAD:
                return (
                    EnforcementAction.WARNED, False,
                    "Requires Tech Lead approval (Vibecoding Index in yellow zone)",
                )
            elif approval_type == ApprovalRequirement.CEO:
                return (
                    EnforcementAction.WARNED, False,
                    "Requires CEO approval (Vibecoding Index in orange zone)",
                )
            elif approval_type == ApprovalRequirement.CTO_CEO:
                return (
                    EnforcementAction.BLOCKED, False,
                    "Requires CTO+CEO override (Vibecoding Index in red zone)",
                )

        return (
            EnforcementAction.AUTO_APPROVED, True,
            f"Auto-approved: Vibecoding Index {soft_result.vibecoding_index.score:.1f} in green zone",
        )

    def _create_approval_request(
        self,
        pr_number: int,
        zone: IndexCategory,
        vibecoding_index: float,
        approval_type: ApprovalRequirement,
    ) -> ApprovalRequest:
        """Create an approval request for tracking."""
        timeout_hours = 24 if approval_type == ApprovalRequirement.TECH_LEAD else 48
        approvers = {
            ApprovalRequirement.TECH_LEAD: ["Tech Lead"],
            ApprovalRequirement.CEO: ["CEO"],
            ApprovalRequirement.CTO_CEO: ["CTO", "CEO"],
        }.get(approval_type, [])

        request = ApprovalRequest(
            id=str(uuid.uuid4())[:8],
            pr_number=pr_number,
            zone=zone,
            vibecoding_index=vibecoding_index,
            required_approvers=approvers,
            requested_at=datetime.utcnow(),
            timeout_hours=timeout_hours,
        )

        self._pending_approvals[request.id] = request
        logger.info(
            f"Created approval request {request.id} for PR #{pr_number}: "
            f"requires {approvers}"
        )
        return request

    # ========================================================================
    # Approval Management
    # ========================================================================

    def approve(
        self,
        request_id: str,
        approved_by: str,
        approver_role: str,
    ) -> bool:
        """Approve a pending request."""
        request = self._pending_approvals.get(request_id)
        if not request:
            logger.warning(f"Approval request {request_id} not found")
            return False

        if request.status != ApprovalStatus.PENDING:
            logger.warning(f"Approval request {request_id} not pending: {request.status}")
            return False

        if approver_role not in request.required_approvers:
            logger.warning(
                f"Approver {approved_by} ({approver_role}) not authorized. "
                f"Required: {request.required_approvers}"
            )
            return False

        request.status = ApprovalStatus.APPROVED
        request.approved_by = approved_by
        request.approved_at = datetime.utcnow()

        logger.info(
            f"Approval request {request_id} approved by {approved_by} ({approver_role})"
        )

        if approver_role == "CEO":
            self._record_ceo_time(
                activity_type="pr_approval",
                pr_number=request.pr_number,
                duration_minutes=30.0,
                category="governance",
            )

        return True

    def reject(
        self,
        request_id: str,
        rejected_by: str,
        reason: str,
    ) -> bool:
        """Reject a pending request."""
        request = self._pending_approvals.get(request_id)
        if not request:
            logger.warning(f"Approval request {request_id} not found")
            return False

        request.status = ApprovalStatus.REJECTED
        request.rejection_reason = reason

        logger.info(
            f"Approval request {request_id} rejected by {rejected_by}: {reason}"
        )
        return True

    def get_pending_approvals(
        self,
        approver_role: Optional[str] = None,
    ) -> List[ApprovalRequest]:
        """Get pending approval requests."""
        pending = [
            r for r in self._pending_approvals.values()
            if r.status == ApprovalStatus.PENDING
        ]

        if approver_role:
            pending = [
                r for r in pending
                if approver_role in r.required_approvers
            ]

        return pending

    # ========================================================================
    # CEO Time Tracking
    # ========================================================================

    def _record_ceo_time(
        self,
        activity_type: str,
        pr_number: Optional[int],
        duration_minutes: float,
        category: str,
        notes: Optional[str] = None,
    ) -> CEOTimeEntry:
        """Record CEO time entry."""
        entry = CEOTimeEntry(
            id=str(uuid.uuid4())[:8],
            activity_type=activity_type,
            pr_number=pr_number,
            duration_minutes=duration_minutes,
            category=category,
            recorded_at=datetime.utcnow(),
            notes=notes,
        )

        self._ceo_time_entries.append(entry)
        logger.info(f"CEO time recorded: {duration_minutes:.1f} min for {activity_type}")
        return entry

    def get_ceo_time_summary(self, days: int = 7) -> Dict[str, Any]:
        """Get CEO time summary for the last N days."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        recent_entries = [
            e for e in self._ceo_time_entries
            if e.recorded_at >= cutoff
        ]

        total_minutes = sum(e.duration_minutes for e in recent_entries)
        total_hours = total_minutes / 60

        breakdown: Dict[str, float] = {}
        for entry in recent_entries:
            cat = entry.category
            breakdown[cat] = breakdown.get(cat, 0) + entry.duration_minutes

        baseline_hours = self._ceo_time_baseline * (days / 7)
        savings_hours = baseline_hours - total_hours
        savings_percent = (savings_hours / baseline_hours * 100) if baseline_hours > 0 else 0

        return {
            "period_days": days,
            "total_hours": round(total_hours, 2),
            "baseline_hours": round(baseline_hours, 2),
            "target_hours": round(self._ceo_time_target * (days / 7), 2),
            "savings_hours": round(max(0, savings_hours), 2),
            "savings_percent": round(max(0, savings_percent), 1),
            "on_target": total_hours <= self._ceo_time_target * (days / 7),
            "breakdown_minutes": breakdown,
            "entry_count": len(recent_entries),
        }

    def record_manual_ceo_time(
        self,
        activity_type: str,
        duration_minutes: float,
        pr_number: Optional[int] = None,
        notes: Optional[str] = None,
    ) -> CEOTimeEntry:
        """Manually record CEO time."""
        category = self._categorize_activity(activity_type)
        return self._record_ceo_time(
            activity_type=activity_type,
            pr_number=pr_number,
            duration_minutes=duration_minutes,
            category=category,
            notes=notes,
        )

    @staticmethod
    def _categorize_activity(activity_type: str) -> str:
        """Categorize activity type for reporting."""
        categories = {
            "pr_review": "code_review",
            "pr_approval": "governance",
            "override_approval": "governance",
            "architecture_review": "design",
            "security_review": "security",
            "planning": "planning",
            "meeting": "meeting",
        }
        return categories.get(activity_type, "other")

    def check_kill_switch(self) -> Optional[Dict[str, Any]]:
        """Check if FULL mode should trigger kill switch."""
        kill_config = self.full_config.get("kill_switch", {})

        total = len(self._pending_approvals) + 1
        blocked = sum(
            1 for r in self._pending_approvals.values()
            if r.status == ApprovalStatus.REJECTED
        )
        rejection_rate = blocked / total

        threshold = kill_config.get("criteria", {}).get(
            "rejection_rate", {}
        ).get("threshold", 0.5)
        if rejection_rate > threshold:
            return {
                "trigger": "rejection_rate",
                "current": rejection_rate,
                "threshold": threshold,
                "action": "rollback_to_soft",
                "message": f"Rejection rate {rejection_rate:.1%} > {threshold:.1%}",
            }

        return None


# ============================================================================
# Factory Functions
# ============================================================================


_soft_enforcement: Optional[SoftEnforcement] = None
_full_enforcement: Optional[FullEnforcement] = None


def create_soft_enforcement(config_path: Optional[str] = None) -> SoftEnforcement:
    """Create a SoftEnforcement strategy instance."""
    global _soft_enforcement
    _soft_enforcement = SoftEnforcement(config_path)
    return _soft_enforcement


def get_soft_enforcement() -> SoftEnforcement:
    """Get or create SoftEnforcement singleton."""
    global _soft_enforcement
    if _soft_enforcement is None:
        _soft_enforcement = SoftEnforcement()
    return _soft_enforcement


def create_full_enforcement(config_path: Optional[str] = None) -> FullEnforcement:
    """Create a FullEnforcement strategy instance."""
    global _full_enforcement
    _full_enforcement = FullEnforcement(config_path)
    return _full_enforcement


def get_full_enforcement() -> FullEnforcement:
    """Get or create FullEnforcement singleton."""
    global _full_enforcement
    if _full_enforcement is None:
        _full_enforcement = FullEnforcement()
    return _full_enforcement
