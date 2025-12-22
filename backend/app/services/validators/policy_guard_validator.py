"""
Policy Guard Validator - OPA Policy Enforcement

SDLC Stage: 04 - BUILD
Sprint: 43 - Policy Guards & Evidence UI
Framework: SDLC 5.1.1 (10-Stage Lifecycle, 4-Tier Classification)
Epic: EP-02 AI Safety Layer v1

Purpose:
Validator that enforces OPA policies on AI-generated code.
Integrates with ValidationPipeline for automated policy checks.

Features:
- Policy-as-Code enforcement via OPA
- Parallel policy evaluation
- Severity-based blocking
- Detailed violation reporting

Architecture:
- Uses OPAPolicyService for OPA communication
- Uses PolicyPackService for policy configuration
- Extends BaseValidator for pipeline integration

Reference:
- docs/02-design/14-Technical-Specs/Policy-Guards-Design.md
- docs/04-build/05-SASE-Artifacts/BRS-2026-003-POLICY-GUARDS.yaml

Version: 1.0.0
Updated: December 2025
"""

import logging
import re
import time
from typing import Any, Dict, List, Optional
from uuid import UUID

from . import BaseValidator, ValidatorConfig, ValidatorResult, ValidatorStatus

logger = logging.getLogger(__name__)


class PolicyGuardValidator(BaseValidator):
    """
    Validator that enforces OPA policies on AI-generated code.

    This validator:
    1. Gets policy pack configuration for the project
    2. Prepares input data (files, diff, imports, layers)
    3. Evaluates all enabled policies via OPA
    4. Aggregates results and returns pass/fail

    Blocking Behavior:
    - CRITICAL/HIGH severity violations always block
    - MEDIUM severity respects policy.blocking flag
    - LOW/INFO never blocks (warnings only)

    Usage:
        validator = PolicyGuardValidator()
        result = await validator.validate(
            project_id=uuid,
            pr_number="123",
            files=["app/main.py", "app/api/routes.py"],
            diff="...",
        )
    """

    name = "policy_guards"
    description = "OPA Policy-as-Code enforcement"
    default_blocking = True
    default_timeout_seconds = 30  # 30 seconds max for all policies

    # Language detection
    LANGUAGE_EXTENSIONS = {
        ".py": "python",
        ".pyi": "python",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".js": "javascript",
        ".jsx": "javascript",
        ".go": "go",
        ".rs": "rust",
        ".java": "java",
        ".kt": "kotlin",
        ".rb": "ruby",
    }

    def __init__(
        self,
        config: Optional[ValidatorConfig] = None,
        opa_service: Optional[Any] = None,
        policy_pack_service: Optional[Any] = None,
    ):
        """
        Initialize Policy Guard Validator.

        Args:
            config: Validator configuration
            opa_service: OPAPolicyService instance (optional, lazy loaded)
            policy_pack_service: PolicyPackService instance (optional, lazy loaded)
        """
        super().__init__(config)
        self._opa_service = opa_service
        self._policy_pack_service = policy_pack_service

    @property
    def opa_service(self):
        """Lazy load OPA service."""
        if self._opa_service is None:
            from app.services.opa_policy_service import get_opa_policy_service
            self._opa_service = get_opa_policy_service()
        return self._opa_service

    @property
    def policy_pack_service(self):
        """Lazy load Policy Pack service."""
        if self._policy_pack_service is None:
            from app.services.policy_pack_service import get_policy_pack_service
            self._policy_pack_service = get_policy_pack_service()
        return self._policy_pack_service

    async def validate(
        self,
        project_id: UUID,
        pr_number: str,
        files: List[str],
        diff: str,
    ) -> ValidatorResult:
        """
        Run policy validation on PR files.

        Args:
            project_id: Project UUID
            pr_number: Pull request number
            files: List of changed file paths
            diff: Unified diff of changes

        Returns:
            ValidatorResult with policy evaluation status
        """
        start_time = time.time()

        try:
            # Get policy pack for project
            policy_pack = await self._get_policy_pack(project_id)

            if policy_pack is None:
                duration_ms = int((time.time() - start_time) * 1000)
                return ValidatorResult(
                    validator_name=self.name,
                    status=ValidatorStatus.SKIPPED,
                    message="No policy pack configured for project",
                    details={"reason": "no_policy_pack"},
                    duration_ms=duration_ms,
                    blocking=False,
                )

            # Check if policy_guards validator is enabled
            if not self._is_validator_enabled(policy_pack):
                duration_ms = int((time.time() - start_time) * 1000)
                return ValidatorResult(
                    validator_name=self.name,
                    status=ValidatorStatus.SKIPPED,
                    message="Policy guards disabled in pack configuration",
                    details={"reason": "validator_disabled"},
                    duration_ms=duration_ms,
                    blocking=False,
                )

            # Get policies from pack
            policies = await self._get_policies(policy_pack)

            if not policies:
                duration_ms = int((time.time() - start_time) * 1000)
                return ValidatorResult(
                    validator_name=self.name,
                    status=ValidatorStatus.SKIPPED,
                    message="No policies configured in pack",
                    details={"reason": "no_policies"},
                    duration_ms=duration_ms,
                    blocking=False,
                )

            # Prepare input for OPA
            file_contents = await self._get_file_contents(project_id, files)
            input_data = self._prepare_input(file_contents, diff, policy_pack)

            # Evaluate all policies
            results = await self.opa_service.evaluate_policies(policies, input_data)

            # Aggregate results
            return self._aggregate_results(results, start_time)

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            logger.error(f"Policy validation error: {e}", exc_info=True)

            return ValidatorResult(
                validator_name=self.name,
                status=ValidatorStatus.ERROR,
                message=f"Policy validation error: {str(e)}",
                details={"error": str(e)},
                duration_ms=duration_ms,
                blocking=False,  # Fail open
            )

    async def _get_policy_pack(self, project_id: UUID) -> Optional[Any]:
        """Get policy pack for project."""
        try:
            return await self.policy_pack_service.get_by_project(project_id)
        except Exception as e:
            logger.warning(f"Failed to get policy pack: {e}")
            return None

    def _is_validator_enabled(self, policy_pack: Any) -> bool:
        """Check if policy_guards validator is enabled in pack."""
        if not hasattr(policy_pack, "validators"):
            return True  # Default enabled

        for validator in policy_pack.validators:
            if validator.get("name") == "policy_guards":
                return validator.get("enabled", True)

        return True  # Default enabled if not explicitly configured

    async def _get_policies(self, policy_pack: Any) -> List[Any]:
        """Get policies from pack."""
        if hasattr(policy_pack, "policies"):
            return policy_pack.policies
        return []

    async def _get_file_contents(
        self,
        project_id: UUID,
        file_paths: List[str],
    ) -> List[Dict[str, Any]]:
        """
        Get file contents for policy evaluation.

        Note: In production, this would fetch from GitHub or local git.
        For now, returns file metadata only.
        """
        files = []
        for path in file_paths:
            files.append({
                "path": path,
                "content": "",  # TODO: Fetch actual content
                "language": self._detect_language(path),
                "imports": [],  # TODO: Parse imports
                "layer": self._detect_layer(path),
            })
        return files

    def _prepare_input(
        self,
        files: List[Dict[str, Any]],
        diff: str,
        policy_pack: Any,
    ) -> Dict[str, Any]:
        """
        Prepare input data for OPA evaluation.

        Input structure:
        {
            "files": [
                {
                    "path": "app/main.py",
                    "content": "...",
                    "language": "python",
                    "imports": ["fastapi", "app.services"],
                    "layer": "presentation"
                }
            ],
            "diff": "...",
            "config": {
                "forbidden_imports": ["minio", "grafana_sdk"],
                "required_patterns": ["from app.core.logging import"],
                "coverage_threshold": 80
            }
        }
        """
        # Parse imports from file content
        for file_data in files:
            if file_data.get("content"):
                file_data["imports"] = self._extract_imports(
                    file_data["content"],
                    file_data.get("language", "unknown"),
                )

        return {
            "files": files,
            "diff": diff,
            "config": {
                "forbidden_imports": getattr(policy_pack, "forbidden_imports", []),
                "required_patterns": getattr(policy_pack, "required_patterns", []),
                "coverage_threshold": getattr(policy_pack, "coverage_threshold", 80),
            },
        }

    def _detect_language(self, path: str) -> str:
        """Detect programming language from file extension."""
        for ext, lang in self.LANGUAGE_EXTENSIONS.items():
            if path.endswith(ext):
                return lang
        return "unknown"

    def _detect_layer(self, path: str) -> str:
        """
        Detect architectural layer from file path.

        Layers (4-layer architecture):
        - presentation: API routes, controllers
        - business: Services, use cases
        - data: Repositories, database access
        - domain: Models, schemas, entities
        """
        path_lower = path.lower()

        if "/api/" in path_lower or "/routes/" in path_lower or "/controllers/" in path_lower:
            return "presentation"
        elif "/services/" in path_lower or "/usecases/" in path_lower:
            return "business"
        elif "/repositories/" in path_lower or "/db/" in path_lower or "/database/" in path_lower:
            return "data"
        elif "/schemas/" in path_lower or "/models/" in path_lower or "/entities/" in path_lower:
            return "domain"

        return "unknown"

    def _extract_imports(self, content: str, language: str) -> List[str]:
        """Extract import statements from code."""
        imports = []

        if language == "python":
            # Python: import X, from X import Y
            imports.extend(re.findall(r"^import\s+(\S+)", content, re.MULTILINE))
            imports.extend(re.findall(r"^from\s+(\S+)\s+import", content, re.MULTILINE))

        elif language in ("typescript", "javascript"):
            # JS/TS: import ... from 'X', require('X')
            imports.extend(re.findall(r"import\s+.*?from\s+['\"]([^'\"]+)['\"]", content))
            imports.extend(re.findall(r"require\(['\"]([^'\"]+)['\"]\)", content))

        elif language == "go":
            # Go: import "X", import ( "X" )
            imports.extend(re.findall(r'import\s+"([^"]+)"', content))
            imports.extend(re.findall(r'import\s+\(\s*(?:[^)]*?"([^"]+)"[^)]*?\s*)+\)', content, re.DOTALL))

        return imports

    def _aggregate_results(
        self,
        results: List[Any],
        start_time: float,
    ) -> ValidatorResult:
        """Aggregate policy results into ValidatorResult."""
        duration_ms = int((time.time() - start_time) * 1000)

        if not results:
            return ValidatorResult(
                validator_name=self.name,
                status=ValidatorStatus.PASSED,
                message="No policies evaluated",
                details={"total_policies": 0},
                duration_ms=duration_ms,
                blocking=False,
            )

        # Categorize results
        passed = [r for r in results if r.passed]
        failed = [r for r in results if not r.passed]
        blocking_failures = [r for r in failed if r.blocking]
        warnings = [r for r in failed if not r.blocking]

        # Build details
        details = {
            "total_policies": len(results),
            "passed_count": len(passed),
            "failed_count": len(failed),
            "blocking_count": len(blocking_failures),
            "warning_count": len(warnings),
            "policies": [
                {
                    "policy_id": r.policy_id,
                    "policy_name": r.policy_name,
                    "passed": r.passed,
                    "severity": r.severity.value if hasattr(r.severity, "value") else r.severity,
                    "blocking": r.blocking,
                    "message": r.message,
                    "evaluation_time_ms": r.evaluation_time_ms,
                }
                for r in results
            ],
        }

        # Add violation details for failures
        if blocking_failures:
            details["blocking_violations"] = [
                {
                    "policy_id": f.policy_id,
                    "policy_name": f.policy_name,
                    "severity": f.severity.value if hasattr(f.severity, "value") else f.severity,
                    "message": f.message,
                    "violations": f.violations,
                }
                for f in blocking_failures
            ]

        if warnings:
            details["warnings"] = [
                {
                    "policy_id": w.policy_id,
                    "policy_name": w.policy_name,
                    "severity": w.severity.value if hasattr(w.severity, "value") else w.severity,
                    "message": w.message,
                }
                for w in warnings
            ]

        # Determine status
        if blocking_failures:
            return ValidatorResult(
                validator_name=self.name,
                status=ValidatorStatus.FAILED,
                message=f"{len(blocking_failures)} blocking policy violation(s)",
                details=details,
                duration_ms=duration_ms,
                blocking=True,
            )

        if warnings:
            return ValidatorResult(
                validator_name=self.name,
                status=ValidatorStatus.PASSED,
                message=f"Passed with {len(warnings)} warning(s)",
                details=details,
                duration_ms=duration_ms,
                blocking=False,
            )

        return ValidatorResult(
            validator_name=self.name,
            status=ValidatorStatus.PASSED,
            message=f"All {len(results)} policies passed",
            details=details,
            duration_ms=duration_ms,
            blocking=False,
        )
