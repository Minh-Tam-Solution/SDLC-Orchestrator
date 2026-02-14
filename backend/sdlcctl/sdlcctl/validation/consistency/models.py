"""Data models for stage consistency validation.

SDLC 6.0.5 - SPEC-0021 Stage Consistency Validation.
Sprint 136 - Validate Consistency Command.
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..tier import Tier
from ..violation import Severity


class ConsistencyStatus(Enum):
    """Status of consistency check between stage pairs."""

    CONSISTENT = "CONSISTENT"
    INCONSISTENT = "INCONSISTENT"
    SKIPPED = "SKIPPED"
    ERROR = "ERROR"


@dataclass
class ConsistencyRule:
    """Definition of a consistency rule."""

    rule_id: str
    description: str
    source_stage: str
    target_stage: str
    default_severity: Severity
    tier_severity_override: Dict[Tier, Severity] = field(default_factory=dict)
    auto_fixable: bool = False

    def get_severity(self, tier: Tier) -> Severity:
        """Get severity for specific tier."""
        return self.tier_severity_override.get(tier, self.default_severity)


@dataclass
class ConsistencyViolation:
    """A single consistency violation."""

    rule_id: str
    severity: Severity
    source_stage: str
    target_stage: str
    source_file: Optional[Path] = None
    target_file: Optional[Path] = None
    line_number: Optional[int] = None
    message: str = ""
    expected: Optional[str] = None
    actual: Optional[str] = None
    fix_suggestion: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "rule_id": self.rule_id,
            "severity": self.severity.value,
            "source_stage": self.source_stage,
            "target_stage": self.target_stage,
            "source_file": str(self.source_file) if self.source_file else None,
            "target_file": str(self.target_file) if self.target_file else None,
            "line_number": self.line_number,
            "message": self.message,
            "expected": self.expected,
            "actual": self.actual,
            "fix_suggestion": self.fix_suggestion,
            "context": self.context,
        }


@dataclass
class StageConsistencyResult:
    """Result of consistency check between a pair of stages."""

    source_stage: str
    target_stage: str
    status: ConsistencyStatus
    violations: List[ConsistencyViolation] = field(default_factory=list)
    artifacts_checked: int = 0
    execution_time_ms: float = 0.0
    error_message: Optional[str] = None

    @property
    def pair_id(self) -> str:
        """Return pair ID, e.g., 'stage_01_02'."""
        return f"stage_{self.source_stage}_{self.target_stage}"

    @property
    def passed(self) -> bool:
        """Check if this stage pair passed consistency check."""
        return self.status == ConsistencyStatus.CONSISTENT

    @property
    def error_count(self) -> int:
        """Count of error-level violations."""
        return sum(1 for v in self.violations if v.severity == Severity.ERROR)

    @property
    def warning_count(self) -> int:
        """Count of warning-level violations."""
        return sum(1 for v in self.violations if v.severity == Severity.WARNING)

    @property
    def info_count(self) -> int:
        """Count of info-level violations."""
        return sum(1 for v in self.violations if v.severity == Severity.INFO)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "source_stage": self.source_stage,
            "target_stage": self.target_stage,
            "status": self.status.value,
            "violations_count": len(self.violations),
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "info_count": self.info_count,
            "artifacts_checked": self.artifacts_checked,
            "execution_time_ms": self.execution_time_ms,
            "error_message": self.error_message,
        }


@dataclass
class ConsistencyConfig:
    """Configuration for consistency validation."""

    tier: Tier
    stage_paths: Dict[str, Path]
    strict: bool = False
    check_checksums: bool = False
    checksums_path: Optional[Path] = None
    verbose: bool = False

    def get_stage_path(self, stage_id: str) -> Optional[Path]:
        """Get path for a specific stage."""
        return self.stage_paths.get(stage_id)

    def validate(self) -> List[str]:
        """Validate configuration and return list of errors."""
        errors = []

        required_stages = ["01", "02", "03", "04"]
        for stage_id in required_stages:
            path = self.stage_paths.get(stage_id)
            if path is None:
                errors.append(f"Stage {stage_id} path is required")
            elif not path.exists():
                errors.append(f"Stage {stage_id} path does not exist: {path}")

        if self.check_checksums and self.checksums_path:
            if not self.checksums_path.exists():
                errors.append(f"Checksums file does not exist: {self.checksums_path}")

        return errors


@dataclass
class ConsistencyResult:
    """Complete result of consistency validation."""

    project_name: str
    tier: Tier
    framework_version: str
    stage_pairs: Dict[str, StageConsistencyResult]
    execution_time_seconds: float = 0.0

    @property
    def passed(self) -> bool:
        """Check if all stage pairs passed."""
        return all(r.passed for r in self.stage_pairs.values())

    @property
    def all_violations(self) -> List[ConsistencyViolation]:
        """Get all violations from all stage pairs."""
        violations = []
        for result in self.stage_pairs.values():
            violations.extend(result.violations)
        return violations

    @property
    def total_violations(self) -> int:
        """Count total violations."""
        return sum(len(r.violations) for r in self.stage_pairs.values())

    @property
    def error_count(self) -> int:
        """Count of error-level violations."""
        return sum(r.error_count for r in self.stage_pairs.values())

    @property
    def warning_count(self) -> int:
        """Count of warning-level violations."""
        return sum(r.warning_count for r in self.stage_pairs.values())

    @property
    def info_count(self) -> int:
        """Count of info-level violations."""
        return sum(r.info_count for r in self.stage_pairs.values())

    @property
    def overall_consistency_percent(self) -> float:
        """Calculate overall consistency percentage."""
        total_artifacts = sum(r.artifacts_checked for r in self.stage_pairs.values())
        if total_artifacts == 0:
            return 100.0

        total_errors = self.error_count
        if total_errors == 0:
            return 100.0

        # Simple calculation: (artifacts - errors) / artifacts * 100
        return max(0.0, (total_artifacts - total_errors) / total_artifacts * 100)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "schema_version": "1.0.0",
            "project": self.project_name,
            "tier": self.tier.value,
            "framework_version": self.framework_version,
            "consistency_checks": {
                pair_id: result.to_dict()
                for pair_id, result in self.stage_pairs.items()
            },
            "violations": [v.to_dict() for v in self.all_violations],
            "summary": {
                "total_violations": self.total_violations,
                "errors": self.error_count,
                "warnings": self.warning_count,
                "info": self.info_count,
                "overall_consistency_percent": round(self.overall_consistency_percent, 2),
                "execution_time_seconds": round(self.execution_time_seconds, 2),
                "passed": self.passed,
            },
        }
