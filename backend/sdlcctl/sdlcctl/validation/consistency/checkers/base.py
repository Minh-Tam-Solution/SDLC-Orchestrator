"""Base class for stage consistency checkers.

SDLC 6.0.5 - SPEC-0021 Stage Consistency Validation.
"""

import re
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional, Set

import yaml

from ...tier import Tier
from ...violation import Severity
from ..models import (
    ConsistencyConfig,
    ConsistencyRule,
    ConsistencyStatus,
    ConsistencyViolation,
    StageConsistencyResult,
)


class BaseConsistencyChecker(ABC):
    """Abstract base class for stage-to-stage consistency checkers."""

    def __init__(self, config: ConsistencyConfig):
        """Initialize checker with configuration.

        Args:
            config: Consistency validation configuration
        """
        self.config = config
        self._rules: Optional[List[ConsistencyRule]] = None

    @property
    @abstractmethod
    def source_stage(self) -> str:
        """Return source stage ID, e.g., '01'."""
        ...

    @property
    @abstractmethod
    def target_stage(self) -> str:
        """Return target stage ID, e.g., '02'."""
        ...

    @property
    def pair_id(self) -> str:
        """Return checker ID, e.g., 'stage_01_02'."""
        return f"stage_{self.source_stage}_{self.target_stage}"

    @property
    def source_path(self) -> Optional[Path]:
        """Get source stage path."""
        return self.config.get_stage_path(self.source_stage)

    @property
    def target_path(self) -> Optional[Path]:
        """Get target stage path."""
        return self.config.get_stage_path(self.target_stage)

    @abstractmethod
    def get_rules(self) -> List[ConsistencyRule]:
        """Return rules for this checker."""
        ...

    @abstractmethod
    def _check_impl(self) -> List[ConsistencyViolation]:
        """Implement actual consistency checking logic.

        Returns:
            List of violations found
        """
        ...

    def check(self) -> StageConsistencyResult:
        """Perform consistency check between stages.

        Returns:
            StageConsistencyResult with violations and status
        """
        start_time = time.time()

        # Validate paths exist
        if not self.source_path or not self.source_path.exists():
            return StageConsistencyResult(
                source_stage=self.source_stage,
                target_stage=self.target_stage,
                status=ConsistencyStatus.ERROR,
                error_message=f"Source stage path does not exist: {self.source_path}",
                execution_time_ms=(time.time() - start_time) * 1000,
            )

        if not self.target_path or not self.target_path.exists():
            return StageConsistencyResult(
                source_stage=self.source_stage,
                target_stage=self.target_stage,
                status=ConsistencyStatus.ERROR,
                error_message=f"Target stage path does not exist: {self.target_path}",
                execution_time_ms=(time.time() - start_time) * 1000,
            )

        try:
            violations = self._check_impl()

            # Apply tier-specific severity
            violations = self._apply_tier_severity(violations)

            # Determine status
            has_errors = any(v.severity == Severity.ERROR for v in violations)
            status = (
                ConsistencyStatus.INCONSISTENT
                if has_errors
                else ConsistencyStatus.CONSISTENT
            )

            execution_time_ms = (time.time() - start_time) * 1000

            return StageConsistencyResult(
                source_stage=self.source_stage,
                target_stage=self.target_stage,
                status=status,
                violations=violations,
                artifacts_checked=self._count_artifacts(),
                execution_time_ms=execution_time_ms,
            )

        except Exception as e:
            return StageConsistencyResult(
                source_stage=self.source_stage,
                target_stage=self.target_stage,
                status=ConsistencyStatus.ERROR,
                error_message=str(e),
                execution_time_ms=(time.time() - start_time) * 1000,
            )

    def _apply_tier_severity(
        self, violations: List[ConsistencyViolation]
    ) -> List[ConsistencyViolation]:
        """Apply tier-specific severity to violations."""
        rules = {r.rule_id: r for r in self.get_rules()}

        for violation in violations:
            rule = rules.get(violation.rule_id)
            if rule:
                violation.severity = rule.get_severity(self.config.tier)

        return violations

    def _count_artifacts(self) -> int:
        """Count total artifacts checked in both stages."""
        count = 0

        if self.source_path and self.source_path.exists():
            count += len(list(self.source_path.rglob("*.md")))
            count += len(list(self.source_path.rglob("*.yaml")))
            count += len(list(self.source_path.rglob("*.yml")))
            count += len(list(self.source_path.rglob("*.json")))

        if self.target_path and self.target_path.exists():
            count += len(list(self.target_path.rglob("*.md")))
            count += len(list(self.target_path.rglob("*.yaml")))
            count += len(list(self.target_path.rglob("*.yml")))
            count += len(list(self.target_path.rglob("*.json")))
            count += len(list(self.target_path.rglob("*.py")))

        return count

    # =========================================================================
    # Helper methods for subclasses
    # =========================================================================

    def find_markdown_files(self, path: Path) -> List[Path]:
        """Find all markdown files in path."""
        if not path.exists():
            return []
        return list(path.rglob("*.md"))

    def find_yaml_files(self, path: Path) -> List[Path]:
        """Find all YAML files in path."""
        if not path.exists():
            return []
        files = list(path.rglob("*.yaml"))
        files.extend(path.rglob("*.yml"))
        return files

    def find_python_files(self, path: Path) -> List[Path]:
        """Find all Python files in path."""
        if not path.exists():
            return []
        return list(path.rglob("*.py"))

    def extract_frontmatter(self, file_path: Path) -> Optional[Dict]:
        """Extract YAML frontmatter from markdown file."""
        try:
            content = file_path.read_text(encoding="utf-8")
            if not content.startswith("---"):
                return None

            # Find end of frontmatter
            end_idx = content.find("---", 3)
            if end_idx == -1:
                return None

            frontmatter_str = content[3:end_idx].strip()
            return yaml.safe_load(frontmatter_str)
        except Exception:
            return None

    def extract_references(self, content: str) -> Set[str]:
        """Extract document references from content.

        Looks for patterns like:
        - [FR-001](../path/to/file.md)
        - See FR-001 for details
        - References: ADR-001, ADR-002
        """
        references = set()

        # Pattern: [ID](path) - markdown links
        link_pattern = r"\[([A-Z]+-\d+)[^\]]*\]"
        for match in re.finditer(link_pattern, content):
            references.add(match.group(1))

        # Pattern: ID standalone (e.g., FR-001, ADR-002)
        id_pattern = r"\b([A-Z]{2,5}-\d{3,4})\b"
        for match in re.finditer(id_pattern, content):
            references.add(match.group(1))

        return references

    def extract_api_endpoints(self, content: str) -> Set[str]:
        """Extract API endpoint definitions from content.

        Looks for patterns like:
        - GET /users/{id}
        - POST /api/v1/projects
        - @app.get("/health")
        """
        endpoints = set()

        # Pattern: HTTP method + path
        http_pattern = r"(GET|POST|PUT|DELETE|PATCH)\s+([/\w{}\-]+)"
        for match in re.finditer(http_pattern, content, re.IGNORECASE):
            method = match.group(1).upper()
            path = match.group(2)
            endpoints.add(f"{method} {path}")

        # Pattern: FastAPI decorators
        fastapi_pattern = r'@\w+\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']'
        for match in re.finditer(fastapi_pattern, content, re.IGNORECASE):
            method = match.group(1).upper()
            path = match.group(2)
            endpoints.add(f"{method} {path}")

        return endpoints

    def parse_openapi_spec(self, file_path: Path) -> Optional[Dict]:
        """Parse OpenAPI specification file."""
        try:
            content = file_path.read_text(encoding="utf-8")
            return yaml.safe_load(content)
        except Exception:
            return None

    def get_openapi_endpoints(self, spec: Dict) -> Set[str]:
        """Extract endpoints from OpenAPI specification."""
        endpoints = set()

        paths = spec.get("paths", {})
        for path, methods in paths.items():
            if isinstance(methods, dict):
                for method in methods.keys():
                    if method.upper() in ("GET", "POST", "PUT", "DELETE", "PATCH"):
                        endpoints.add(f"{method.upper()} {path}")

        return endpoints
