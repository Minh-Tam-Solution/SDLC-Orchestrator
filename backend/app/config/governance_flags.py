"""
Governance Feature Flags Configuration

Feature flags for controlling governance enforcement levels and emergency controls.

Version: 1.0.0
Last Updated: January 27, 2026
Authority: Plan PRE-PHASE 0 - Kill Switch Configuration

GOVERNANCE MODES:
  OFF: Governance disabled (development only)
  WARNING: Log violations, don't block (observation mode)
  SOFT: Block critical violations, warn on others
  FULL: Block all violations (production mode)

KILL SWITCH:
  Auto-rollback if governance causes problems (rejection rate >80%, latency >500ms)
"""

from enum import Enum
from typing import Dict, Any, List
from dataclasses import dataclass


class GovernanceMode(str, Enum):
    """Governance enforcement levels"""

    OFF = "OFF"
    """Governance disabled. For local development only."""

    WARNING = "WARNING"
    """Log violations, don't block. For observation and tuning."""

    SOFT = "SOFT"
    """Block critical violations (missing ownership, missing intent, index >80).
    Warn on medium violations (index 60-80, test coverage <80%)."""

    FULL = "FULL"
    """Block all violations. Production mode after Week 5 validation."""


@dataclass
class FeatureFlag:
    """Feature flag definition"""

    name: str
    default: Any
    description: str
    options: List[Any] = None
    requires_approval_from: List[str] = None


# ═══════════════════════════════════════════════════════════════
# PRIMARY FLAGS
# ═══════════════════════════════════════════════════════════════

GOVERNANCE_MODE = FeatureFlag(
    name="governance.enforcement_mode",
    default=GovernanceMode.WARNING,
    description="Governance enforcement level (OFF/WARNING/SOFT/FULL)",
    options=[
        GovernanceMode.OFF,
        GovernanceMode.WARNING,
        GovernanceMode.SOFT,
        GovernanceMode.FULL,
    ],
)

GOVERNANCE_BYPASS = FeatureFlag(
    name="governance.emergency_bypass",
    default=False,
    description="Emergency bypass for production hotfixes (Break Glass)",
    requires_approval_from=["CTO", "CEO"],
)

# ═══════════════════════════════════════════════════════════════
# AUTO-GENERATION FLAGS
# ═══════════════════════════════════════════════════════════════

AUTO_GENERATION_ENABLED = FeatureFlag(
    name="governance.auto_generation.enabled",
    default=True,
    description="Enable auto-generation (intent, ownership, context, attestation)",
)

AUTO_GENERATION_LLM_PROVIDER = FeatureFlag(
    name="governance.auto_generation.llm_provider",
    default="ollama",
    description="Primary LLM provider (ollama/claude/rule-based)",
    options=["ollama", "claude", "rule-based"],
)

AUTO_GENERATION_FALLBACK_ENABLED = FeatureFlag(
    name="governance.auto_generation.fallback_enabled",
    default=True,
    description="Enable fallback chain (LLM → Template → Placeholder)",
)

AUTO_GENERATION_MAX_LATENCY = FeatureFlag(
    name="governance.auto_generation.max_latency_ms",
    default=10000,
    description="Max LLM latency before fallback (milliseconds)",
)

# ═══════════════════════════════════════════════════════════════
# VIBECODING INDEX FLAGS
# ═══════════════════════════════════════════════════════════════

VIBECODING_INDEX_ENABLED = FeatureFlag(
    name="governance.vibecoding_index.enabled",
    default=True,
    description="Enable Vibecoding Index calculation",
)

VIBECODING_INDEX_CRITICAL_PATH_OVERRIDE = FeatureFlag(
    name="governance.vibecoding_index.critical_path_override",
    default=True,
    description="Auto-boost index to 80 for security/payment/infra files",
)

VIBECODING_INDEX_GREEN_THRESHOLD = FeatureFlag(
    name="governance.vibecoding_index.green_threshold",
    default=30,
    description="Max index for Green (auto-approve)",
)

VIBECODING_INDEX_ORANGE_THRESHOLD = FeatureFlag(
    name="governance.vibecoding_index.orange_threshold",
    default=60,
    description="Min index for Orange (CEO should review)",
)

VIBECODING_INDEX_RED_THRESHOLD = FeatureFlag(
    name="governance.vibecoding_index.red_threshold",
    default=80,
    description="Min index for Red (CEO must review)",
)

# ═══════════════════════════════════════════════════════════════
# STAGE GATING FLAGS
# ═══════════════════════════════════════════════════════════════

STAGE_GATING_ENABLED = FeatureFlag(
    name="governance.stage_gating.enabled",
    default=True,
    description="Enable stage-aware PR gating (prevent working ahead of design)",
)

STAGE_GATING_STRICT_MODE = FeatureFlag(
    name="governance.stage_gating.strict_mode",
    default=False,
    description="Strict mode: No exceptions for stage violations",
)

# ═══════════════════════════════════════════════════════════════
# CONTEXT AUTHORITY FLAGS
# ═══════════════════════════════════════════════════════════════

CONTEXT_AUTHORITY_ENABLED = FeatureFlag(
    name="governance.context_authority.enabled",
    default=True,
    description="Enable Context Authority Engine (orphan code detection)",
)

CONTEXT_AUTHORITY_ADR_LINKAGE_REQUIRED = FeatureFlag(
    name="governance.context_authority.adr_linkage_required",
    default=True,
    description="Require ADR linkage for all modules",
)

CONTEXT_AUTHORITY_AGENTS_MD_FRESHNESS_DAYS = FeatureFlag(
    name="governance.context_authority.agents_md_freshness_days",
    default=7,
    description="Max age for AGENTS.md before warning (days)",
)

# ═══════════════════════════════════════════════════════════════
# KILL SWITCH CONFIGURATION
# ═══════════════════════════════════════════════════════════════

KILL_SWITCH_ENABLED = FeatureFlag(
    name="governance.kill_switch.enabled",
    default=True,
    description="Enable automatic rollback if governance causes problems",
)


@dataclass
class KillSwitchCriteria:
    """Kill switch auto-rollback criteria"""

    rejection_rate_threshold: float = 0.8  # 80%
    latency_p95_threshold_ms: int = 500  # 500ms
    false_positive_rate_threshold: float = 0.2  # 20%
    developer_complaints_per_day: int = 5  # 5/day

    rollback_to: GovernanceMode = GovernanceMode.WARNING
    notify: List[str] = None

    def __post_init__(self):
        if self.notify is None:
            self.notify = ["CTO", "CEO", "Tech Lead"]


KILL_SWITCH_CRITERIA = KillSwitchCriteria()

# ═══════════════════════════════════════════════════════════════
# DOGFOODING FLAGS (Orchestrator Repo Self-Application)
# ═══════════════════════════════════════════════════════════════

DOGFOODING_ENABLED = FeatureFlag(
    name="governance.dogfooding.enabled",
    default=False,
    description="Apply governance to Orchestrator repo itself",
)

DOGFOODING_STRICT_MODE = FeatureFlag(
    name="governance.dogfooding.strict_mode",
    default=False,
    description="No exceptions for Orchestrator team (treat like customer)",
)

# ═══════════════════════════════════════════════════════════════
# PHASE CONTROL FLAGS (PRE-PHASE 0 → WEEK 5)
# ═══════════════════════════════════════════════════════════════


class Phase(str, Enum):
    """Implementation phases"""

    PRE_PHASE_0 = "PRE_PHASE_0"  # Signatures + calibration
    PHASE_0 = "PHASE_0"  # 48-hour deliverables
    WEEK_1 = "WEEK_1"  # Foundation + Auto-Gen Layer
    WEEK_2 = "WEEK_2"  # Context Authority + Evidence + Signals
    WEEK_3 = "WEEK_3"  # Stage Gating + Actor Governance + Feedback
    WEEK_4 = "WEEK_4"  # Quality Contract + CEO Dashboard + Integration
    WEEK_5 = "WEEK_5"  # Rollout + Measurement + Optimization
    WEEK_6_PLUS = "WEEK_6_PLUS"  # Full Enforcement + Customer Rollout


CURRENT_PHASE = FeatureFlag(
    name="governance.current_phase",
    default=Phase.PRE_PHASE_0,
    description="Current implementation phase (controls feature availability)",
    options=[phase for phase in Phase],
)

# ═══════════════════════════════════════════════════════════════
# MONITORING FLAGS
# ═══════════════════════════════════════════════════════════════

MONITORING_ENABLED = FeatureFlag(
    name="governance.monitoring.enabled",
    default=True,
    description="Enable Prometheus metrics collection",
)

MONITORING_METRICS_INTERVAL_SECONDS = FeatureFlag(
    name="governance.monitoring.metrics_interval_seconds",
    default=60,
    description="Metrics collection interval (seconds)",
)

# ═══════════════════════════════════════════════════════════════
# CEO DASHBOARD FLAGS
# ═══════════════════════════════════════════════════════════════

CEO_DASHBOARD_ENABLED = FeatureFlag(
    name="governance.ceo_dashboard.enabled",
    default=False,  # Enable in Week 4
    description="Enable CEO Dashboard (Time Saved, Vibecoding Index, etc.)",
)

CEO_DASHBOARD_REAL_TIME_UPDATES = FeatureFlag(
    name="governance.ceo_dashboard.real_time_updates",
    default=True,
    description="Enable WebSocket real-time updates",
)

# ═══════════════════════════════════════════════════════════════
# FEATURE AVAILABILITY BY PHASE
# ═══════════════════════════════════════════════════════════════

PHASE_FEATURE_AVAILABILITY: Dict[Phase, Dict[str, bool]] = {
    Phase.PRE_PHASE_0: {
        # Only infrastructure setup, no enforcement
        "governance_enforcement": False,
        "auto_generation": False,
        "vibecoding_index": False,
        "stage_gating": False,
        "context_authority": False,
        "ceo_dashboard": False,
    },
    Phase.PHASE_0: {
        # 48-hour deliverables, design phase
        "governance_enforcement": False,
        "auto_generation": False,
        "vibecoding_index": False,
        "stage_gating": False,
        "context_authority": False,
        "ceo_dashboard": False,
    },
    Phase.WEEK_1: {
        # Auto-Generation Layer + Dogfooding prep
        "governance_enforcement": False,  # WARNING mode only
        "auto_generation": True,
        "vibecoding_index": False,
        "stage_gating": False,
        "context_authority": False,
        "ceo_dashboard": False,
    },
    Phase.WEEK_2: {
        # Context Authority + Evidence Validator + Signals
        "governance_enforcement": False,  # WARNING mode only
        "auto_generation": True,
        "vibecoding_index": True,
        "stage_gating": False,
        "context_authority": True,
        "ceo_dashboard": False,
    },
    Phase.WEEK_3: {
        # Stage Gating + Feedback Loop + Dogfooding SOFT
        "governance_enforcement": True,  # SOFT mode for dogfooding
        "auto_generation": True,
        "vibecoding_index": True,
        "stage_gating": True,
        "context_authority": True,
        "ceo_dashboard": False,
    },
    Phase.WEEK_4: {
        # Quality Contract + CEO Dashboard + Integration
        "governance_enforcement": True,  # FULL mode for dogfooding
        "auto_generation": True,
        "vibecoding_index": True,
        "stage_gating": True,
        "context_authority": True,
        "ceo_dashboard": True,
    },
    Phase.WEEK_5: {
        # Rollout + Measurement (WARNING mode for production)
        "governance_enforcement": False,  # WARNING mode for customers
        "auto_generation": True,
        "vibecoding_index": True,
        "stage_gating": True,
        "context_authority": True,
        "ceo_dashboard": True,
    },
    Phase.WEEK_6_PLUS: {
        # Full Enforcement + Customer Rollout
        "governance_enforcement": True,  # FULL mode for customers
        "auto_generation": True,
        "vibecoding_index": True,
        "stage_gating": True,
        "context_authority": True,
        "ceo_dashboard": True,
    },
}


# ═══════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════


def is_feature_available(feature_name: str, current_phase: Phase = None) -> bool:
    """
    Check if a feature is available in the current phase.

    Args:
        feature_name: Feature name (e.g., "auto_generation")
        current_phase: Current phase (defaults to CURRENT_PHASE.default)

    Returns:
        True if feature is available, False otherwise
    """
    if current_phase is None:
        current_phase = CURRENT_PHASE.default

    phase_features = PHASE_FEATURE_AVAILABILITY.get(current_phase, {})
    return phase_features.get(feature_name, False)


def get_governance_mode(current_phase: Phase = None) -> GovernanceMode:
    """
    Get recommended governance mode for current phase.

    Args:
        current_phase: Current phase (defaults to CURRENT_PHASE.default)

    Returns:
        Recommended GovernanceMode
    """
    if current_phase is None:
        current_phase = CURRENT_PHASE.default

    phase_mode_map = {
        Phase.PRE_PHASE_0: GovernanceMode.OFF,
        Phase.PHASE_0: GovernanceMode.OFF,
        Phase.WEEK_1: GovernanceMode.WARNING,
        Phase.WEEK_2: GovernanceMode.WARNING,
        Phase.WEEK_3: GovernanceMode.SOFT,  # Dogfooding
        Phase.WEEK_4: GovernanceMode.FULL,  # Dogfooding
        Phase.WEEK_5: GovernanceMode.WARNING,  # Customer rollout
        Phase.WEEK_6_PLUS: GovernanceMode.FULL,  # Production
    }

    return phase_mode_map.get(current_phase, GovernanceMode.WARNING)


def should_trigger_kill_switch(
    rejection_rate: float,
    latency_p95_ms: int,
    false_positive_rate: float,
    developer_complaints_per_day: int,
) -> tuple[bool, str]:
    """
    Check if kill switch criteria are met.

    Args:
        rejection_rate: PR rejection rate (0.0 to 1.0)
        latency_p95_ms: P95 latency in milliseconds
        false_positive_rate: False positive rate (0.0 to 1.0)
        developer_complaints_per_day: Number of complaints per day

    Returns:
        (should_trigger, reason) tuple
    """
    criteria = KILL_SWITCH_CRITERIA

    if rejection_rate > criteria.rejection_rate_threshold:
        return (
            True,
            f"Rejection rate {rejection_rate:.1%} exceeds threshold "
            f"{criteria.rejection_rate_threshold:.1%}",
        )

    if latency_p95_ms > criteria.latency_p95_threshold_ms:
        return (
            True,
            f"Latency P95 {latency_p95_ms}ms exceeds threshold "
            f"{criteria.latency_p95_threshold_ms}ms",
        )

    if false_positive_rate > criteria.false_positive_rate_threshold:
        return (
            True,
            f"False positive rate {false_positive_rate:.1%} exceeds threshold "
            f"{criteria.false_positive_rate_threshold:.1%}",
        )

    if developer_complaints_per_day > criteria.developer_complaints_per_day:
        return (
            True,
            f"Developer complaints {developer_complaints_per_day}/day exceeds threshold "
            f"{criteria.developer_complaints_per_day}/day",
        )

    return (False, "All criteria within acceptable range")


# ═══════════════════════════════════════════════════════════════
# ALL FLAGS REGISTRY
# ═══════════════════════════════════════════════════════════════

ALL_FLAGS: Dict[str, FeatureFlag] = {
    # Primary
    "GOVERNANCE_MODE": GOVERNANCE_MODE,
    "GOVERNANCE_BYPASS": GOVERNANCE_BYPASS,
    # Auto-Generation
    "AUTO_GENERATION_ENABLED": AUTO_GENERATION_ENABLED,
    "AUTO_GENERATION_LLM_PROVIDER": AUTO_GENERATION_LLM_PROVIDER,
    "AUTO_GENERATION_FALLBACK_ENABLED": AUTO_GENERATION_FALLBACK_ENABLED,
    "AUTO_GENERATION_MAX_LATENCY": AUTO_GENERATION_MAX_LATENCY,
    # Vibecoding Index
    "VIBECODING_INDEX_ENABLED": VIBECODING_INDEX_ENABLED,
    "VIBECODING_INDEX_CRITICAL_PATH_OVERRIDE": VIBECODING_INDEX_CRITICAL_PATH_OVERRIDE,
    "VIBECODING_INDEX_GREEN_THRESHOLD": VIBECODING_INDEX_GREEN_THRESHOLD,
    "VIBECODING_INDEX_ORANGE_THRESHOLD": VIBECODING_INDEX_ORANGE_THRESHOLD,
    "VIBECODING_INDEX_RED_THRESHOLD": VIBECODING_INDEX_RED_THRESHOLD,
    # Stage Gating
    "STAGE_GATING_ENABLED": STAGE_GATING_ENABLED,
    "STAGE_GATING_STRICT_MODE": STAGE_GATING_STRICT_MODE,
    # Context Authority
    "CONTEXT_AUTHORITY_ENABLED": CONTEXT_AUTHORITY_ENABLED,
    "CONTEXT_AUTHORITY_ADR_LINKAGE_REQUIRED": CONTEXT_AUTHORITY_ADR_LINKAGE_REQUIRED,
    "CONTEXT_AUTHORITY_AGENTS_MD_FRESHNESS_DAYS": CONTEXT_AUTHORITY_AGENTS_MD_FRESHNESS_DAYS,
    # Kill Switch
    "KILL_SWITCH_ENABLED": KILL_SWITCH_ENABLED,
    # Dogfooding
    "DOGFOODING_ENABLED": DOGFOODING_ENABLED,
    "DOGFOODING_STRICT_MODE": DOGFOODING_STRICT_MODE,
    # Phase Control
    "CURRENT_PHASE": CURRENT_PHASE,
    # Monitoring
    "MONITORING_ENABLED": MONITORING_ENABLED,
    "MONITORING_METRICS_INTERVAL_SECONDS": MONITORING_METRICS_INTERVAL_SECONDS,
    # CEO Dashboard
    "CEO_DASHBOARD_ENABLED": CEO_DASHBOARD_ENABLED,
    "CEO_DASHBOARD_REAL_TIME_UPDATES": CEO_DASHBOARD_REAL_TIME_UPDATES,
}


if __name__ == "__main__":
    # Print current configuration for debugging
    print("=" * 70)
    print("GOVERNANCE FEATURE FLAGS CONFIGURATION")
    print("=" * 70)
    print(f"\nCurrent Phase: {CURRENT_PHASE.default}")
    print(f"Governance Mode: {get_governance_mode()}")
    print(f"\nFeature Availability:")
    for feature_name in [
        "auto_generation",
        "vibecoding_index",
        "stage_gating",
        "context_authority",
        "ceo_dashboard",
    ]:
        available = is_feature_available(feature_name)
        status = "✅ ENABLED" if available else "⏳ DISABLED"
        print(f"  {feature_name}: {status}")

    print(f"\nKill Switch Criteria:")
    print(f"  Rejection Rate: >{KILL_SWITCH_CRITERIA.rejection_rate_threshold:.0%}")
    print(
        f"  Latency P95: >{KILL_SWITCH_CRITERIA.latency_p95_threshold_ms}ms"
    )
    print(
        f"  False Positive Rate: >{KILL_SWITCH_CRITERIA.false_positive_rate_threshold:.0%}"
    )
    print(
        f"  Developer Complaints: >{KILL_SWITCH_CRITERIA.developer_complaints_per_day}/day"
    )
    print("=" * 70)
