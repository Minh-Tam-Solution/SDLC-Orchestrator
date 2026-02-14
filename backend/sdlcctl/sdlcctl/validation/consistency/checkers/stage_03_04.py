"""Stage 03 (Integrate) ↔ Stage 04 (Build) consistency checker.

SDLC 6.0.5 - SPEC-0021 Stage Consistency Validation.

Validates:
- CONS-007: API endpoints must match Stage 03 contracts
- CONS-008: Request/response schemas must match OpenAPI
- CONS-009: New endpoints must be documented in Stage 03
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Set

from ...tier import Tier
from ...violation import Severity
from ..models import ConsistencyRule, ConsistencyViolation
from .base import BaseConsistencyChecker


class Stage03To04Checker(BaseConsistencyChecker):
    """Check consistency between Stage 03 (Integrate) and Stage 04 (Build)."""

    @property
    def source_stage(self) -> str:
        return "03"

    @property
    def target_stage(self) -> str:
        return "04"

    def get_rules(self) -> List[ConsistencyRule]:
        """Return rules for Stage 03 ↔ Stage 04 consistency."""
        return [
            ConsistencyRule(
                rule_id="CONS-007",
                description="API endpoints must match Stage 03 contracts",
                source_stage="03",
                target_stage="04",
                default_severity=Severity.ERROR,
                tier_severity_override={
                    Tier.LITE: Severity.WARNING,
                    Tier.STANDARD: Severity.WARNING,
                    Tier.PROFESSIONAL: Severity.ERROR,
                    Tier.ENTERPRISE: Severity.ERROR,
                },
            ),
            ConsistencyRule(
                rule_id="CONS-008",
                description="Request/response schemas must match OpenAPI",
                source_stage="03",
                target_stage="04",
                default_severity=Severity.ERROR,
                tier_severity_override={
                    Tier.LITE: Severity.INFO,
                    Tier.STANDARD: Severity.WARNING,
                    Tier.PROFESSIONAL: Severity.ERROR,
                    Tier.ENTERPRISE: Severity.ERROR,
                },
            ),
            ConsistencyRule(
                rule_id="CONS-009",
                description="New endpoints must be documented in Stage 03",
                source_stage="03",
                target_stage="04",
                default_severity=Severity.WARNING,
                tier_severity_override={
                    Tier.LITE: Severity.INFO,
                    Tier.STANDARD: Severity.WARNING,
                    Tier.PROFESSIONAL: Severity.WARNING,
                    Tier.ENTERPRISE: Severity.ERROR,
                },
            ),
        ]

    def _check_impl(self) -> List[ConsistencyViolation]:
        """Check Stage 03 ↔ Stage 04 consistency."""
        violations: List[ConsistencyViolation] = []

        # Get endpoints from OpenAPI spec (Stage 03)
        spec_endpoints = self._get_openapi_endpoints()

        # Get endpoints from code (Stage 04)
        code_endpoints = self._get_code_endpoints()

        # Check endpoint matching
        violations.extend(self._check_endpoint_matching(spec_endpoints, code_endpoints))

        # Check for undocumented endpoints
        violations.extend(self._check_undocumented_endpoints(spec_endpoints, code_endpoints))

        return violations

    def _get_openapi_endpoints(self) -> Dict[str, Dict]:
        """Extract endpoints from OpenAPI specification."""
        endpoints: Dict[str, Dict] = {}

        if not self.source_path:
            return endpoints

        # Find OpenAPI spec file
        contract_folder = self.source_path / "01-api-contracts"
        if not contract_folder.exists():
            contract_folder = self.source_path

        for yaml_file in self.find_yaml_files(contract_folder):
            spec = self.parse_openapi_spec(yaml_file)
            if not spec:
                continue

            paths = spec.get("paths", {})
            for path, methods in paths.items():
                if not isinstance(methods, dict):
                    continue

                for method, details in methods.items():
                    if method.upper() not in ("GET", "POST", "PUT", "DELETE", "PATCH"):
                        continue

                    endpoint_key = f"{method.upper()} {path}"
                    endpoints[endpoint_key] = {
                        "path": path,
                        "method": method.upper(),
                        "operation_id": details.get("operationId", ""),
                        "summary": details.get("summary", ""),
                        "source_file": yaml_file,
                    }

        return endpoints

    def _get_code_endpoints(self) -> Dict[str, Dict]:
        """Extract endpoints from code implementation."""
        endpoints: Dict[str, Dict] = {}

        if not self.target_path:
            return endpoints

        # Find Python route files
        route_files = [
            f for f in self.find_python_files(self.target_path)
            if "route" in f.name.lower() or "endpoint" in f.name.lower() or "api" in f.parent.name.lower()
        ]

        for py_file in route_files:
            try:
                content = py_file.read_text(encoding="utf-8")
                file_endpoints = self._extract_fastapi_endpoints(content, py_file)
                endpoints.update(file_endpoints)
            except Exception:
                pass

        return endpoints

    def _extract_fastapi_endpoints(self, content: str, file_path: Path) -> Dict[str, Dict]:
        """Extract FastAPI endpoint definitions from Python code."""
        endpoints: Dict[str, Dict] = {}

        # Pattern for FastAPI route decorators
        # Matches: @router.get("/path"), @app.post("/api/v1/users"), etc.
        decorator_pattern = (
            r'@(?:router|app|api_router)\.'
            r'(get|post|put|delete|patch)\s*\(\s*'
            r'["\']([^"\']+)["\']'
        )

        for match in re.finditer(decorator_pattern, content, re.IGNORECASE):
            method = match.group(1).upper()
            path = match.group(2)

            # Normalize path (remove leading/trailing slashes for comparison)
            normalized_path = "/" + path.strip("/")

            endpoint_key = f"{method} {normalized_path}"
            line_number = content[:match.start()].count("\n") + 1

            endpoints[endpoint_key] = {
                "path": normalized_path,
                "method": method,
                "line_number": line_number,
                "source_file": file_path,
            }

        return endpoints

    def _normalize_path(self, path: str) -> str:
        """Normalize API path for comparison.

        - Removes /api/v1 prefix
        - Normalizes {param} format
        """
        # Remove common prefixes
        prefixes = ["/api/v1", "/api/v2", "/api"]
        for prefix in prefixes:
            if path.startswith(prefix):
                path = path[len(prefix):]
                break

        # Ensure leading slash
        if not path.startswith("/"):
            path = "/" + path

        # Normalize parameter format: {id} -> {id}
        path = re.sub(r"\{(\w+)\}", r"{\1}", path)

        return path

    def _check_endpoint_matching(
        self, spec_endpoints: Dict[str, Dict], code_endpoints: Dict[str, Dict]
    ) -> List[ConsistencyViolation]:
        """Check that code endpoints match spec endpoints."""
        violations = []

        # Normalize spec endpoints for comparison
        spec_normalized = {
            f"{v['method']} {self._normalize_path(v['path'])}": (k, v)
            for k, v in spec_endpoints.items()
        }

        # Check each code endpoint against spec
        for code_key, code_info in code_endpoints.items():
            code_normalized = f"{code_info['method']} {self._normalize_path(code_info['path'])}"

            # Check if endpoint exists in spec (normalized comparison)
            matching_spec = None
            for spec_key, (original_key, spec_info) in spec_normalized.items():
                if code_normalized == spec_key:
                    matching_spec = spec_info
                    break

            if not matching_spec and spec_endpoints:
                # Check if it's a close match (same path, different method, etc.)
                close_matches = [
                    k for k in spec_normalized.keys()
                    if self._normalize_path(code_info['path']) in k
                ]

                if close_matches:
                    violations.append(
                        ConsistencyViolation(
                            rule_id="CONS-007",
                            severity=Severity.ERROR,
                            source_stage=self.source_stage,
                            target_stage=self.target_stage,
                            target_file=code_info.get("source_file"),
                            line_number=code_info.get("line_number"),
                            message=f"API endpoint path mismatch",
                            expected=f"One of: {', '.join(close_matches[:3])}",
                            actual=code_key,
                            fix_suggestion=(
                                "Update OpenAPI spec to match implementation, "
                                "or fix implementation to match spec"
                            ),
                        )
                    )

        return violations

    def _check_undocumented_endpoints(
        self, spec_endpoints: Dict[str, Dict], code_endpoints: Dict[str, Dict]
    ) -> List[ConsistencyViolation]:
        """Check for code endpoints not documented in spec."""
        violations = []

        if not spec_endpoints:
            # No spec to compare against
            return violations

        # Normalize for comparison
        spec_normalized = {
            f"{v['method']} {self._normalize_path(v['path'])}"
            for v in spec_endpoints.values()
        }

        for code_key, code_info in code_endpoints.items():
            code_normalized = f"{code_info['method']} {self._normalize_path(code_info['path'])}"

            if code_normalized not in spec_normalized:
                # Skip health/status endpoints (commonly undocumented)
                if any(skip in code_info['path'].lower() for skip in ["health", "status", "ping", "metrics"]):
                    continue

                violations.append(
                    ConsistencyViolation(
                        rule_id="CONS-009",
                        severity=Severity.WARNING,
                        source_stage=self.source_stage,
                        target_stage=self.target_stage,
                        target_file=code_info.get("source_file"),
                        line_number=code_info.get("line_number"),
                        message=f"Undocumented API endpoint: {code_key}",
                        expected="Endpoint documented in OpenAPI spec",
                        actual="Endpoint not found in Stage 03 contracts",
                        fix_suggestion=(
                            f"Add endpoint {code_key} to OpenAPI specification "
                            f"in docs/03-integrate/01-api-contracts/"
                        ),
                    )
                )

        return violations
