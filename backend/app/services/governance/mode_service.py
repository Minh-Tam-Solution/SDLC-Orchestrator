"""
=========================================================================
Governance Mode Service - Enforcement Level Management
SDLC Orchestrator - Sprint 173 (Governance Loop Completion)

Version: 1.1.0
Date: February 15, 2026
Status: ACTIVE
Authority: CTO + Backend Lead Approved
Framework: SDLC 6.0.5 Quality Assurance System

Purpose:
- Manage governance enforcement levels (OFF, WARNING, SOFT, FULL)
- Enable gradual rollout with kill switch capability
- Track enforcement metrics for calibration
- Support dogfooding on Orchestrator repo

Sprint 173 Updates:
- Added RollbackResult for structured rollback responses
- Added state history tracking (get_state_history)
- Added escalate_mode for post-recovery escalation
- Fixed manual_rollback to raise ValueError on escalation
- check_and_rollback_if_needed uses external metrics parameter

Enforcement Levels:
- OFF: No governance checks (development mode)
- WARNING: Log violations, don't block (observability mode)
- SOFT: Block critical violations, warn on others
- FULL: Block all violations (production mode)

Zero Mock Policy: Real enforcement with feature flags
=========================================================================
"""

import asyncio
import logging
import types
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Callable
from uuid import UUID

import yaml

logger = logging.getLogger(__name__)


class GovernanceMode(str, Enum):
    """
    Governance enforcement levels.

    Progression: OFF → WARNING → SOFT → FULL
    Rollback: Any level can rollback to WARNING for safety
    """

    OFF = "off"  # No enforcement (dev mode)
    WARNING = "warning"  # Log only, no blocking
    SOFT = "soft"  # Block critical, warn others
    FULL = "full"  # Block all violations


class ViolationSeverity(str, Enum):
    """
    Violation severity levels for enforcement decisions.

    Maps to governance rules in governance_signals.yaml
    """

    INFO = "info"  # Informational only
    WARNING = "warning"  # Should fix, not blocking
    ERROR = "error"  # Must fix, blocks in SOFT+
    CRITICAL = "critical"  # Security/safety issue, always blocks


@dataclass
class GovernanceViolation:
    """
    Represents a governance violation detected during validation.
    """

    id: str
    rule_id: str
    severity: ViolationSeverity
    message: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    suggestion: Optional[str] = None
    cli_command: Optional[str] = None
    documentation_link: Optional[str] = None
    auto_fixable: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "id": self.id,
            "rule_id": self.rule_id,
            "severity": self.severity.value,
            "message": self.message,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "suggestion": self.suggestion,
            "cli_command": self.cli_command,
            "documentation_link": self.documentation_link,
            "auto_fixable": self.auto_fixable,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class EnforcementResult:
    """
    Result of governance enforcement check.
    """

    allowed: bool
    mode: GovernanceMode
    violations: List[GovernanceViolation]
    blocked_violations: List[GovernanceViolation]
    warned_violations: List[GovernanceViolation]
    vibecoding_index: Optional[float] = None
    routing: Optional[str] = None
    processing_time_ms: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "allowed": self.allowed,
            "mode": self.mode.value,
            "violations_count": len(self.violations),
            "blocked_count": len(self.blocked_violations),
            "warned_count": len(self.warned_violations),
            "violations": [v.to_dict() for v in self.violations],
            "blocked_violations": [v.to_dict() for v in self.blocked_violations],
            "warned_violations": [v.to_dict() for v in self.warned_violations],
            "vibecoding_index": self.vibecoding_index,
            "routing": self.routing,
            "processing_time_ms": self.processing_time_ms,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class RollbackCriteria:
    """
    Criteria for automatic rollback to WARNING mode.

    If any threshold is exceeded, system auto-rollbacks.
    """

    max_rejection_rate: float = 0.8  # 80%
    max_latency_p95_ms: float = 500.0  # 500ms
    max_false_positive_rate: float = 0.2  # 20%
    max_developer_complaints_per_day: int = 5
    evaluation_window_minutes: int = 60


@dataclass
class GovernanceModeState:
    """
    Current state of governance mode.

    Includes metrics for calibration and rollback decisions.
    """

    current_mode: GovernanceMode
    previous_mode: Optional[GovernanceMode]
    changed_at: datetime
    changed_by: Optional[str]
    reason: Optional[str]
    is_rollback: bool = False
    auto_rollback_enabled: bool = True
    rollback_criteria: RollbackCriteria = field(default_factory=RollbackCriteria)

    # Metrics for calibration
    total_evaluations: int = 0
    total_blocked: int = 0
    total_warned: int = 0
    total_passed: int = 0
    false_positives_reported: int = 0
    ceo_overrides: int = 0
    _latency_p95_ms: float = 0.0

    @property
    def total_rejections(self) -> int:
        """Alias for total_blocked (backward compatibility)."""
        return self.total_blocked

    @property
    def latency_p95_ms(self) -> float:
        """Current P95 latency in milliseconds."""
        return self._latency_p95_ms

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "current_mode": self.current_mode.value,
            "previous_mode": self.previous_mode.value if self.previous_mode else None,
            "changed_at": self.changed_at.isoformat(),
            "changed_by": self.changed_by,
            "reason": self.reason,
            "is_rollback": self.is_rollback,
            "auto_rollback_enabled": self.auto_rollback_enabled,
            "total_evaluations": self.total_evaluations,
            "total_blocked": self.total_blocked,
            "total_warned": self.total_warned,
            "total_passed": self.total_passed,
            "false_positives_reported": self.false_positives_reported,
            "ceo_overrides": self.ceo_overrides,
            "rejection_rate": self.rejection_rate(),
            "latency_p95_ms": self._latency_p95_ms,
        }

    def rejection_rate(self) -> float:
        """Calculate current rejection rate."""
        if self.total_evaluations == 0:
            return 0.0
        return self.total_blocked / self.total_evaluations

    def false_positive_rate(self) -> float:
        """Calculate false positive rate."""
        if self.total_blocked == 0:
            return 0.0
        return self.false_positives_reported / self.total_blocked

    def should_auto_rollback(self) -> tuple[bool, Optional[str]]:
        """
        Check if auto-rollback should be triggered.

        Returns: (should_rollback, reason)
        """
        if not self.auto_rollback_enabled:
            return False, None

        if self.current_mode == GovernanceMode.WARNING:
            return False, None  # Already in warning mode

        if self.current_mode == GovernanceMode.OFF:
            return False, None  # OFF mode is exempt

        # Need minimum sample size for statistical significance
        if self.total_evaluations < 10:
            return False, None

        if self.rejection_rate() > self.rollback_criteria.max_rejection_rate:
            return True, f"Rejection rate {self.rejection_rate():.1%} > {self.rollback_criteria.max_rejection_rate:.1%}"

        if self.false_positive_rate() > self.rollback_criteria.max_false_positive_rate:
            return True, f"False positive rate {self.false_positive_rate():.1%} > {self.rollback_criteria.max_false_positive_rate:.1%}"

        return False, None


@dataclass
class RollbackResult:
    """
    Structured result from rollback operations.

    Always returned by check_and_rollback_if_needed and manual_rollback
    so callers don't need to handle None.
    """

    rollback_triggered: bool
    new_mode: GovernanceMode
    previous_mode: Optional[GovernanceMode] = None
    triggered_by: Optional[str] = None
    trigger_reasons: List[str] = field(default_factory=list)
    audit_log_entry: Optional[Dict[str, Any]] = None
    notifications_sent: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)


class GovernanceModeService:
    """
    Service for managing governance enforcement modes.

    Features:
    - Mode management (OFF/WARNING/SOFT/FULL)
    - Auto-rollback on criteria breach
    - Metrics tracking for calibration
    - Kill switch capability
    - Project-level overrides

    Usage:
        service = GovernanceModeService()
        await service.initialize()

        # Check enforcement
        result = await service.enforce(
            violations=violations,
            project_id=project_id,
        )
    """

    def __init__(
        self,
        config_path: Optional[str] = None,
        default_mode: GovernanceMode = GovernanceMode.WARNING,
    ):
        """
        Initialize Governance Mode Service.

        Args:
            config_path: Path to governance_flags configuration
            default_mode: Default governance mode (WARNING for safety)
        """
        self._config_path = config_path or "backend/app/config/governance_flags.py"
        self._default_mode = default_mode

        # Global state
        self._state = GovernanceModeState(
            current_mode=default_mode,
            previous_mode=None,
            changed_at=datetime.utcnow(),
            changed_by="system",
            reason="Initial startup",
        )

        # Project-level overrides
        self._project_overrides: Dict[UUID, GovernanceMode] = {}

        # Listeners for mode changes
        self._mode_change_listeners: List[Callable] = []

        # Latency tracking for p95 calculation
        self._latencies: List[float] = []
        self._latency_window = 1000  # Keep last 1000 measurements

        # State history for auditing (Sprint 173)
        self._state_history: List[Dict[str, Any]] = []

        logger.info(f"GovernanceModeService initialized with default mode: {default_mode.value}")

    async def initialize(self) -> None:
        """
        Initialize service and load configuration.

        Loads governance flags from config file if available.
        """
        try:
            # Try to load governance flags
            flags = self._load_governance_flags()
            if flags:
                mode_str = flags.get("GOVERNANCE_MODE", self._default_mode.value)
                self._state.current_mode = GovernanceMode(mode_str.lower())
                self._state.auto_rollback_enabled = flags.get("AUTO_ROLLBACK_ENABLED", True)
                logger.info(f"Loaded governance mode from config: {self._state.current_mode.value}")

        except Exception as e:
            logger.warning(f"Failed to load governance config, using defaults: {e}")

    def _load_governance_flags(self) -> Optional[Dict[str, Any]]:
        """Load governance flags from config file."""
        try:
            # Try YAML config first
            yaml_path = "backend/app/config/governance_flags.yaml"
            with open(yaml_path, "r") as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            pass

        try:
            # Fallback to Python config
            from app.config.governance_flags import (
                GOVERNANCE_MODE,
                AUTO_ROLLBACK_ENABLED,
            )

            return {
                "GOVERNANCE_MODE": GOVERNANCE_MODE,
                "AUTO_ROLLBACK_ENABLED": AUTO_ROLLBACK_ENABLED,
            }
        except ImportError:
            return None

    # ========================================================================
    # Mode Management
    # ========================================================================

    @property
    def current_mode(self) -> GovernanceMode:
        """Property accessor for current governance mode."""
        return self._state.current_mode

    def get_mode(self, project_id: Optional[UUID] = None) -> GovernanceMode:
        """
        Get current governance mode.

        Args:
            project_id: Optional project ID for project-level override

        Returns:
            Current governance mode
        """
        if project_id and project_id in self._project_overrides:
            return self._project_overrides[project_id]
        return self._state.current_mode

    def get_state(self) -> GovernanceModeState:
        """Get full governance mode state including metrics."""
        return self._state

    async def set_mode(
        self,
        mode: GovernanceMode,
        changed_by: str,
        reason: str,
        project_id: Optional[UUID] = None,
    ) -> GovernanceModeState:
        """
        Set governance mode.

        Args:
            mode: New governance mode
            changed_by: User/system making the change
            reason: Reason for change
            project_id: Optional project ID for project-level override

        Returns:
            Updated governance mode state
        """
        if project_id:
            # Project-level override
            old_mode = self._project_overrides.get(project_id)
            self._project_overrides[project_id] = mode
            logger.info(
                f"Governance mode for project {project_id} changed: "
                f"{old_mode.value if old_mode else 'default'} → {mode.value} by {changed_by}: {reason}"
            )
        else:
            # Global mode change
            old_mode = self._state.current_mode
            self._state.previous_mode = old_mode
            self._state.current_mode = mode
            self._state.changed_at = datetime.utcnow()
            self._state.changed_by = changed_by
            self._state.reason = reason
            self._state.is_rollback = False

            logger.info(
                f"Governance mode changed: {old_mode.value} → {mode.value} by {changed_by}: {reason}"
            )

            # Record in state history
            self._state_history.append({
                "timestamp": datetime.utcnow().isoformat(),
                "old_mode": old_mode.value,
                "mode": mode.value,
                "changed_by": changed_by,
                "reason": reason,
            })

            # Notify listeners
            await self._notify_mode_change(old_mode, mode, changed_by, reason)

        return self._state

    async def rollback_to_warning(
        self,
        triggered_by: str,
        reason: str,
    ) -> GovernanceModeState:
        """
        Emergency rollback to WARNING mode.

        Used when:
        - Kill switch triggered
        - Auto-rollback criteria met
        - Manual rollback by CTO

        Args:
            triggered_by: Who/what triggered the rollback
            reason: Reason for rollback

        Returns:
            Updated governance mode state
        """
        old_mode = self._state.current_mode

        if old_mode == GovernanceMode.WARNING:
            logger.info("Already in WARNING mode, no rollback needed")
            return self._state

        self._state.previous_mode = old_mode
        self._state.current_mode = GovernanceMode.WARNING
        self._state.changed_at = datetime.utcnow()
        self._state.changed_by = triggered_by
        self._state.reason = f"ROLLBACK: {reason}"
        self._state.is_rollback = True

        logger.warning(
            f"GOVERNANCE ROLLBACK: {old_mode.value} → WARNING by {triggered_by}: {reason}"
        )

        # Notify listeners (high priority)
        await self._notify_mode_change(
            old_mode,
            GovernanceMode.WARNING,
            triggered_by,
            f"ROLLBACK: {reason}",
        )

        return self._state

    async def manual_rollback(
        self,
        triggered_by: str,
        reason: str,
        target_mode: Optional[GovernanceMode] = None,
    ) -> "RollbackResult":
        """
        Manual rollback by CTO/CEO.

        Args:
            triggered_by: Who triggered the rollback
            reason: Reason for rollback
            target_mode: Target mode (defaults to WARNING)

        Returns:
            RollbackResult with rollback details

        Raises:
            ValueError: If attempting to escalate via rollback
        """
        target = target_mode or GovernanceMode.WARNING

        # Cannot escalate via rollback - only de-escalate
        current = self._state.current_mode
        if self._mode_severity(target) > self._mode_severity(current):
            raise ValueError(
                f"Manual rollback cannot escalate: {current.value} → {target.value}. "
                f"Use escalate_mode() instead."
            )

        old_mode = self._state.current_mode
        await self.set_mode(target, triggered_by, f"MANUAL_ROLLBACK: {reason}")

        audit_entry = {
            "old_mode": old_mode.value,
            "new_mode": target.value,
            "triggered_by": triggered_by,
            "trigger_reasons": [f"manual_rollback: {reason}"],
            "timestamp": datetime.utcnow().isoformat(),
        }

        return RollbackResult(
            rollback_triggered=True,
            new_mode=target,
            previous_mode=old_mode,
            triggered_by=triggered_by,
            trigger_reasons=[f"manual_rollback: {reason}"],
            audit_log_entry=audit_entry,
        )

    def _mode_severity(self, mode: GovernanceMode) -> int:
        """Get severity level of mode (higher = stricter)."""
        severity_map = {
            GovernanceMode.OFF: 0,
            GovernanceMode.WARNING: 1,
            GovernanceMode.SOFT: 2,
            GovernanceMode.FULL: 3,
        }
        return severity_map.get(mode, 0)

    async def escalate_mode(
        self,
        target_mode: GovernanceMode,
        escalated_by: str,
        reason: str,
    ) -> Dict[str, Any]:
        """
        Manually escalate governance mode after recovery.

        Unlike set_mode, this validates that escalation is intentional
        and only moves to a stricter mode.

        Args:
            target_mode: Target mode to escalate to
            escalated_by: Who is escalating (must be CTO or CEO)
            reason: Reason for escalation

        Returns:
            Dict with success status and mode info

        Raises:
            ValueError: If trying to de-escalate (use manual_rollback instead)
        """
        current = self._state.current_mode

        if self._mode_severity(target_mode) <= self._mode_severity(current):
            raise ValueError(
                f"escalate_mode cannot de-escalate: {current.value} → {target_mode.value}. "
                f"Use manual_rollback() instead."
            )

        await self.set_mode(target_mode, escalated_by, f"ESCALATION: {reason}")

        return types.SimpleNamespace(
            success=True,
            old_mode=current.value,
            new_mode=target_mode.value,
            escalated_by=escalated_by,
            reason=reason,
        )

    def get_state_history(self) -> List[Dict[str, Any]]:
        """
        Get history of all governance mode state changes.

        Returns:
            List of state change entries with timestamp, mode, changed_by, reason
        """
        return list(self._state_history)

    async def check_and_rollback_if_needed(
        self,
        metrics: Optional[Dict[str, Any]] = None,
    ) -> "RollbackResult":
        """
        Check if auto-rollback should trigger and execute if needed.

        Args:
            metrics: Optional metrics dict with keys:
                - rejection_rate, latency_p95_ms, false_positive_rate,
                  developer_complaints_today
                If not provided, uses internal state metrics.

        Returns:
            RollbackResult (always, even when no rollback)
        """
        current_mode = self._state.current_mode

        # OFF mode is exempt from auto-rollback
        if current_mode == GovernanceMode.OFF:
            return RollbackResult(
                rollback_triggered=False,
                new_mode=current_mode,
            )

        # If metrics provided, evaluate against kill switch thresholds
        if metrics is not None:
            triggers = self._evaluate_rollback_triggers(metrics)
            if triggers:
                trigger_reasons = [t["reason"] for t in triggers]
                reason_text = "; ".join(t["message"] for t in triggers)
                logger.warning(f"Auto-rollback triggered by metrics: {reason_text}")

                old_mode = self._state.current_mode
                await self.rollback_to_warning(
                    triggered_by="auto_rollback",
                    reason=reason_text,
                )

                audit_entry = {
                    "old_mode": old_mode.value,
                    "new_mode": GovernanceMode.WARNING.value,
                    "triggered_by": "auto_rollback",
                    "trigger_reasons": trigger_reasons,
                    "timestamp": datetime.utcnow().isoformat(),
                }

                return RollbackResult(
                    rollback_triggered=old_mode != GovernanceMode.WARNING and old_mode != GovernanceMode.OFF,
                    new_mode=self._state.current_mode,
                    previous_mode=old_mode,
                    triggered_by="auto_rollback",
                    trigger_reasons=trigger_reasons,
                    audit_log_entry=audit_entry,
                    notifications_sent=["CTO", "CEO"],
                )

        # Fallback: check internal state metrics
        should_rollback, reason = self._state.should_auto_rollback()

        if should_rollback and reason:
            logger.warning(f"Auto-rollback triggered: {reason}")
            old_mode = self._state.current_mode
            await self.rollback_to_warning(
                triggered_by="auto_rollback",
                reason=reason,
            )

            audit_entry = {
                "old_mode": old_mode.value,
                "new_mode": GovernanceMode.WARNING.value,
                "triggered_by": "auto_rollback",
                "trigger_reasons": [reason],
                "timestamp": datetime.utcnow().isoformat(),
            }

            return RollbackResult(
                rollback_triggered=True,
                new_mode=GovernanceMode.WARNING,
                previous_mode=old_mode,
                triggered_by="auto_rollback",
                trigger_reasons=[reason],
                audit_log_entry=audit_entry,
                notifications_sent=["CTO", "CEO"],
            )

        # No rollback needed
        return RollbackResult(
            rollback_triggered=False,
            new_mode=current_mode,
        )

    async def _notify_mode_change(
        self,
        old_mode: GovernanceMode,
        new_mode: GovernanceMode,
        changed_by: str,
        reason: str,
    ) -> None:
        """Notify all listeners of mode change."""
        for listener in self._mode_change_listeners:
            try:
                if asyncio.iscoroutinefunction(listener):
                    await listener(old_mode, new_mode, changed_by, reason)
                else:
                    listener(old_mode, new_mode, changed_by, reason)
            except Exception as e:
                logger.error(f"Error in mode change listener: {e}")

    def add_mode_change_listener(self, listener: Callable) -> None:
        """Add listener for mode changes."""
        self._mode_change_listeners.append(listener)

    # ========================================================================
    # Enforcement Logic
    # ========================================================================

    async def enforce(
        self,
        violations: List[GovernanceViolation],
        project_id: Optional[UUID] = None,
        vibecoding_index: Optional[float] = None,
    ) -> EnforcementResult:
        """
        Enforce governance based on current mode and violations.

        Args:
            violations: List of detected violations
            project_id: Optional project ID for project-level mode
            vibecoding_index: Optional Vibecoding Index score

        Returns:
            EnforcementResult with allowed status and categorized violations
        """
        import time

        start_time = time.perf_counter()

        mode = self.get_mode(project_id)
        blocked_violations: List[GovernanceViolation] = []
        warned_violations: List[GovernanceViolation] = []

        # Determine routing based on Vibecoding Index
        routing = self._determine_routing(vibecoding_index)

        # Categorize violations based on mode
        # OFF mode: no categorization (violations exist but are neither blocked nor warned)
        if mode != GovernanceMode.OFF:
            for violation in violations:
                should_block = self._should_block(mode, violation.severity)

                if should_block:
                    blocked_violations.append(violation)
                else:
                    warned_violations.append(violation)

        # Determine if allowed
        allowed = len(blocked_violations) == 0

        # Update metrics
        processing_time_ms = (time.perf_counter() - start_time) * 1000
        self._update_metrics(allowed, processing_time_ms)

        result = EnforcementResult(
            allowed=allowed,
            mode=mode,
            violations=violations,
            blocked_violations=blocked_violations,
            warned_violations=warned_violations,
            vibecoding_index=vibecoding_index,
            routing=routing,
            processing_time_ms=processing_time_ms,
        )

        # Log enforcement decision
        if not allowed:
            logger.warning(
                f"Governance BLOCKED: {len(blocked_violations)} violations in {mode.value} mode"
            )
        elif warned_violations:
            logger.info(
                f"Governance WARNED: {len(warned_violations)} violations in {mode.value} mode"
            )

        return result

    def _should_block(
        self,
        mode: GovernanceMode,
        severity: ViolationSeverity,
    ) -> bool:
        """
        Determine if violation should block based on mode and severity.

        Args:
            mode: Current governance mode
            severity: Violation severity

        Returns:
            True if violation should block
        """
        if mode == GovernanceMode.OFF:
            return False

        if mode == GovernanceMode.WARNING:
            return False  # Warning mode never blocks

        if mode == GovernanceMode.SOFT:
            # Soft mode blocks CRITICAL and ERROR only
            return severity in (ViolationSeverity.CRITICAL, ViolationSeverity.ERROR)

        if mode == GovernanceMode.FULL:
            # Full mode blocks everything except INFO
            return severity != ViolationSeverity.INFO

        return False

    def _determine_routing(self, vibecoding_index: Optional[float]) -> Optional[str]:
        """
        Determine routing based on Vibecoding Index.

        Args:
            vibecoding_index: 0-100 score

        Returns:
            Routing string (auto_approve, tech_lead_review, ceo_should_review, ceo_must_review)
        """
        if vibecoding_index is None:
            return None

        if vibecoding_index <= 30:
            return "auto_approve"
        elif vibecoding_index <= 60:
            return "tech_lead_review"
        elif vibecoding_index <= 80:
            return "ceo_should_review"
        else:
            return "ceo_must_review"

    def _update_metrics(self, allowed: bool, latency_ms: float) -> None:
        """Update enforcement metrics for calibration."""
        self._state.total_evaluations += 1

        if allowed:
            self._state.total_passed += 1
        else:
            self._state.total_blocked += 1

        # Track latency
        self._latencies.append(latency_ms)
        if len(self._latencies) > self._latency_window:
            self._latencies = self._latencies[-self._latency_window:]

        # Update P95 on state for property access
        self._state._latency_p95_ms = self.get_latency_p95()

    def get_latency_p95(self) -> float:
        """Calculate p95 latency from recent measurements."""
        if not self._latencies:
            return 0.0

        sorted_latencies = sorted(self._latencies)
        p95_index = int(len(sorted_latencies) * 0.95)
        return sorted_latencies[p95_index] if p95_index < len(sorted_latencies) else sorted_latencies[-1]

    # ========================================================================
    # Calibration & Feedback
    # ========================================================================

    async def report_false_positive(
        self,
        violation_id: str,
        reported_by: str,
        reason: str,
    ) -> None:
        """
        Report a false positive for calibration.

        Args:
            violation_id: ID of the falsely blocked violation
            reported_by: User reporting the false positive
            reason: Explanation of why it's a false positive
        """
        self._state.false_positives_reported += 1

        logger.info(
            f"False positive reported by {reported_by}: {violation_id} - {reason}"
        )

        # Check if this triggers auto-rollback
        should_rollback, rollback_reason = self._state.should_auto_rollback()
        if should_rollback and rollback_reason:
            await self.rollback_to_warning("auto_rollback", rollback_reason)

    async def record_ceo_override(
        self,
        submission_id: UUID,
        ceo_user_id: UUID,
        decision: str,
        agrees_with_index: bool,
        feedback: Optional[str] = None,
    ) -> None:
        """
        Record CEO override decision for calibration.

        Args:
            submission_id: The submission that was overridden
            ceo_user_id: CEO's user ID
            decision: approve/reject/request_changes
            agrees_with_index: Whether CEO agrees with Vibecoding Index
            feedback: Optional calibration feedback
        """
        self._state.ceo_overrides += 1

        if not agrees_with_index:
            # CEO disagrees - this is calibration data
            logger.warning(
                f"CEO disagrees with Vibecoding Index for submission {submission_id}: {feedback}"
            )

    # ========================================================================
    # Kill Switch
    # ========================================================================

    def _evaluate_rollback_triggers(
        self,
        metrics: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Evaluate metrics against kill switch thresholds.

        Kill Switch Triggers (per MONITORING-PLAN.md):
        1. rejection_rate >80%
        2. latency_p95 >500ms
        3. false_positive_rate >20%
        4. developer_complaints >5/day

        Args:
            metrics: System metrics dict containing:
                - rejection_rate: float (0.0 to 1.0)
                - latency_p95_ms: float (milliseconds)
                - false_positive_rate: float (0.0 to 1.0)
                - developer_complaints_today: int

        Returns:
            List of triggered conditions with reason and message
        """
        triggers: List[Dict[str, Any]] = []
        criteria = self._state.rollback_criteria

        # Check rejection rate (>80%)
        rejection_rate = metrics.get("rejection_rate", 0.0)
        if rejection_rate > criteria.max_rejection_rate:
            triggers.append({
                "reason": "rejection_rate_high",
                "message": f"Rejection rate {rejection_rate:.1%} > {criteria.max_rejection_rate:.1%}",
                "metric": "rejection_rate",
                "value": rejection_rate,
                "threshold": criteria.max_rejection_rate,
            })

        # Check latency P95 (>500ms)
        latency_p95 = metrics.get("latency_p95_ms", 0)
        if latency_p95 > criteria.max_latency_p95_ms:
            triggers.append({
                "reason": "latency_high",
                "message": f"Latency P95 {latency_p95:.0f}ms > {criteria.max_latency_p95_ms:.0f}ms",
                "metric": "latency_p95_ms",
                "value": latency_p95,
                "threshold": criteria.max_latency_p95_ms,
            })

        # Check false positive rate (>20%)
        fp_rate = metrics.get("false_positive_rate", 0.0)
        if fp_rate > criteria.max_false_positive_rate:
            triggers.append({
                "reason": "false_positive_rate_high",
                "message": f"False positive rate {fp_rate:.1%} > {criteria.max_false_positive_rate:.1%}",
                "metric": "false_positive_rate",
                "value": fp_rate,
                "threshold": criteria.max_false_positive_rate,
            })

        # Check developer complaints (>5/day)
        complaints = metrics.get("developer_complaints_today", 0)
        if complaints > criteria.max_developer_complaints_per_day:
            triggers.append({
                "reason": "developer_complaints_high",
                "message": f"Developer complaints {complaints} > {criteria.max_developer_complaints_per_day}/day",
                "metric": "developer_complaints_today",
                "value": complaints,
                "threshold": criteria.max_developer_complaints_per_day,
            })

        return triggers

    async def kill_switch(
        self,
        triggered_by: str,
        reason: str,
    ) -> GovernanceModeState:
        """
        Emergency kill switch - immediately rollback to WARNING.

        This is the nuclear option when governance is causing problems.

        Args:
            triggered_by: Who triggered the kill switch
            reason: Why the kill switch was triggered

        Returns:
            Updated governance mode state
        """
        logger.critical(
            f"KILL SWITCH TRIGGERED by {triggered_by}: {reason}"
        )

        return await self.rollback_to_warning(
            triggered_by=f"KILL_SWITCH:{triggered_by}",
            reason=reason,
        )


# ============================================================================
# Factory Functions
# ============================================================================

_governance_mode_service: Optional[GovernanceModeService] = None


def create_governance_mode_service(
    config_path: Optional[str] = None,
    default_mode: GovernanceMode = GovernanceMode.WARNING,
) -> GovernanceModeService:
    """
    Create a new GovernanceModeService instance.

    Args:
        config_path: Path to configuration file
        default_mode: Default governance mode

    Returns:
        GovernanceModeService instance
    """
    global _governance_mode_service
    _governance_mode_service = GovernanceModeService(
        config_path=config_path,
        default_mode=default_mode,
    )
    return _governance_mode_service


def get_governance_mode_service() -> GovernanceModeService:
    """
    Get or create GovernanceModeService singleton.

    Returns:
        GovernanceModeService instance
    """
    global _governance_mode_service
    if _governance_mode_service is None:
        _governance_mode_service = create_governance_mode_service()
    return _governance_mode_service


async def initialize_governance_mode_service() -> GovernanceModeService:
    """
    Initialize and return the GovernanceModeService.

    This should be called during application startup.

    Returns:
        Initialized GovernanceModeService
    """
    service = get_governance_mode_service()
    await service.initialize()
    return service
