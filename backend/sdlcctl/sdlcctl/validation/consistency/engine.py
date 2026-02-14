"""Consistency validation engine.

SDLC 6.0.5 - SPEC-0021 Stage Consistency Validation.
Orchestrates cross-stage consistency validation.
"""

import time
from pathlib import Path
from typing import Dict, List, Optional

from ..tier import Tier
from .checkers import (
    BaseConsistencyChecker,
    Stage01To02Checker,
    Stage01To04Checker,
    Stage02To03Checker,
    Stage03To04Checker,
)
from .models import ConsistencyConfig, ConsistencyResult, StageConsistencyResult


class ConsistencyEngine:
    """Orchestrates cross-stage consistency validation.

    Validates consistency between:
    - Stage 01 (Planning) ↔ Stage 02 (Design)
    - Stage 02 (Design) ↔ Stage 03 (Integrate)
    - Stage 03 (Integrate) ↔ Stage 04 (Build)
    - Stage 01 (Planning) ↔ Stage 04 (Build)

    Reference: SPEC-0021 Stage Consistency Validation
    """

    FRAMEWORK_VERSION = "6.0.5"

    def __init__(self, config: ConsistencyConfig):
        """Initialize consistency engine.

        Args:
            config: Consistency validation configuration
        """
        self.config = config
        self._checkers: Optional[List[BaseConsistencyChecker]] = None

    @property
    def checkers(self) -> List[BaseConsistencyChecker]:
        """Get list of checkers, initialized on first access."""
        if self._checkers is None:
            self._checkers = [
                Stage01To02Checker(self.config),
                Stage02To03Checker(self.config),
                Stage03To04Checker(self.config),
                Stage01To04Checker(self.config),
            ]
        return self._checkers

    def validate(self) -> ConsistencyResult:
        """Run all consistency checks.

        Returns:
            ConsistencyResult with all stage pair results and violations
        """
        start_time = time.time()

        # Validate configuration
        config_errors = self.config.validate()
        if config_errors:
            raise ValueError(f"Invalid configuration: {'; '.join(config_errors)}")

        # Run all checkers
        stage_pairs: Dict[str, StageConsistencyResult] = {}

        for checker in self.checkers:
            result = checker.check()
            stage_pairs[checker.pair_id] = result

        # Calculate execution time
        execution_time_seconds = time.time() - start_time

        # Determine project name from paths
        project_name = self._detect_project_name()

        return ConsistencyResult(
            project_name=project_name,
            tier=self.config.tier,
            framework_version=self.FRAMEWORK_VERSION,
            stage_pairs=stage_pairs,
            execution_time_seconds=execution_time_seconds,
        )

    def _detect_project_name(self) -> str:
        """Detect project name from paths."""
        # Try to find common parent directory
        paths = list(self.config.stage_paths.values())
        if not paths:
            return "Unknown"

        # Use first path's parent
        first_path = paths[0]
        if first_path.exists():
            # Go up to find project root (look for common markers)
            current = first_path
            for _ in range(5):  # Max 5 levels up
                if (current / ".git").exists() or (current / "pyproject.toml").exists():
                    return current.name
                current = current.parent

        return first_path.parts[-2] if len(first_path.parts) >= 2 else "Unknown"

    @classmethod
    def from_paths(
        cls,
        stage_01: Path,
        stage_02: Path,
        stage_03: Path,
        stage_04: Path,
        tier: Optional[Tier] = None,
        strict: bool = False,
        check_checksums: bool = False,
        checksums_path: Optional[Path] = None,
        verbose: bool = False,
    ) -> "ConsistencyEngine":
        """Create engine from stage paths.

        Args:
            stage_01: Path to Stage 01 (Planning) folder
            stage_02: Path to Stage 02 (Design) folder
            stage_03: Path to Stage 03 (Integrate) folder
            stage_04: Path to Stage 04 (Build) folder
            tier: Project tier (auto-detect if None)
            strict: Enable strict mode
            check_checksums: Enable artifact checksum verification
            checksums_path: Path to checksums file
            verbose: Enable verbose output

        Returns:
            Configured ConsistencyEngine instance
        """
        # Auto-detect tier if not provided
        if tier is None:
            tier = cls._detect_tier(stage_01, stage_02)

        config = ConsistencyConfig(
            tier=tier,
            stage_paths={
                "01": Path(stage_01).resolve(),
                "02": Path(stage_02).resolve(),
                "03": Path(stage_03).resolve(),
                "04": Path(stage_04).resolve(),
            },
            strict=strict,
            check_checksums=check_checksums,
            checksums_path=checksums_path,
            verbose=verbose,
        )

        return cls(config)

    @staticmethod
    def _detect_tier(stage_01: Path, stage_02: Path) -> Tier:
        """Auto-detect project tier based on artifact count.

        Heuristic:
        - <10 docs: LITE
        - 10-50 docs: STANDARD
        - 50-100 docs: PROFESSIONAL
        - >100 docs: ENTERPRISE
        """
        doc_count = 0

        for path in [stage_01, stage_02]:
            if path.exists():
                doc_count += len(list(path.rglob("*.md")))

        if doc_count < 10:
            return Tier.LITE
        elif doc_count < 50:
            return Tier.STANDARD
        elif doc_count < 100:
            return Tier.PROFESSIONAL
        else:
            return Tier.ENTERPRISE
