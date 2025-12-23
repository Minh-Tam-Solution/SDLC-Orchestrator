"""
SAST Validator - Static Application Security Testing

SDLC Stage: 04 - BUILD
Sprint: 43 - Policy Guards & Evidence UI
Framework: SDLC 5.1.1
Epic: EP-02 AI Safety Layer v1

Purpose:
Validate code for security vulnerabilities using Semgrep.
Detects OWASP Top 10 issues and custom security rules.

Features:
- OWASP Top 10 detection
- Custom security rules per project
- Severity-based blocking (ERROR blocks merge)
- CWE/OWASP reference mapping
- AI-safety specific rules (prompt injection, data leakage)

Blocking: Yes (default) - security errors block merge
Timeout: 300 seconds (default)

Reference:
- OWASP Top 10: https://owasp.org/www-project-top-ten/
- CWE: https://cwe.mitre.org/
"""

import logging
import time
from typing import Any, Dict, List, Optional
from uuid import UUID

from ..semgrep_service import (
    SemgrepCategory,
    SemgrepFinding,
    SemgrepSeverity,
    get_semgrep_service,
)
from . import BaseValidator, ValidatorConfig, ValidatorResult, ValidatorStatus

logger = logging.getLogger(__name__)


class SASTValidator(BaseValidator):
    """
    SAST validator using Semgrep for security scanning.

    Integrates with ValidationPipeline to detect:
    - SQL Injection
    - XSS (Cross-Site Scripting)
    - Command Injection
    - Path Traversal
    - Hardcoded Secrets
    - Insecure Crypto
    - SSRF (Server-Side Request Forgery)
    - AI-specific vulnerabilities (prompt injection, model extraction)
    """

    name = "sast"
    description = "Static Application Security Testing (Semgrep)"
    default_blocking = True
    default_timeout_seconds = 300

    # File extensions to scan
    SCANNABLE_EXTENSIONS = {
        ".py",
        ".js",
        ".ts",
        ".tsx",
        ".jsx",
        ".java",
        ".go",
        ".rb",
        ".php",
        ".c",
        ".cpp",
        ".cs",
        ".yaml",
        ".yml",
        ".json",
    }

    # Critical categories that always block
    BLOCKING_CATEGORIES = {
        SemgrepCategory.INJECTION,
        SemgrepCategory.COMMAND_INJECTION,
        SemgrepCategory.SECRETS,
        SemgrepCategory.BROKEN_AUTH,
        SemgrepCategory.SSRF,
        SemgrepCategory.INSECURE_DESERIALIZATION,
    }

    def __init__(
        self,
        config: Optional[ValidatorConfig] = None,
        custom_rules_path: Optional[str] = None,
        additional_rulesets: Optional[List[str]] = None,
    ):
        """
        Initialize SAST validator.

        Args:
            config: Validator configuration
            custom_rules_path: Path to custom .semgrep.yml rules
            additional_rulesets: Additional Semgrep rulesets to use
        """
        super().__init__(config)
        self.custom_rules_path = custom_rules_path
        self.additional_rulesets = additional_rulesets or []

    async def validate(
        self,
        project_id: UUID,
        pr_number: str,
        files: List[str],
        diff: str,
    ) -> ValidatorResult:
        """
        Run SAST validation on changed files.

        Process:
        1. Filter to scannable files
        2. Run Semgrep scan
        3. Categorize findings by severity
        4. Determine blocking status

        Args:
            project_id: Project UUID
            pr_number: Pull request number
            files: List of changed file paths
            diff: Unified diff

        Returns:
            ValidatorResult with security findings
        """
        started_at = time.time()

        try:
            # Filter to scannable files
            scannable_files = [f for f in files if self._is_scannable(f)]

            if not scannable_files:
                duration_ms = int((time.time() - started_at) * 1000)
                return ValidatorResult(
                    validator_name=self.name,
                    status=ValidatorStatus.SKIPPED,
                    message="No scannable files found",
                    details={"files_checked": 0},
                    duration_ms=duration_ms,
                    blocking=False,
                )

            logger.info(
                f"SAST validation: scanning {len(scannable_files)} files for PR #{pr_number}"
            )

            # Get Semgrep service
            semgrep = get_semgrep_service(custom_rules_path=self.custom_rules_path)

            # Run scan
            scan_result = await semgrep.scan_files(
                files=scannable_files,
                additional_rules=self.additional_rulesets,
            )

            duration_ms = int((time.time() - started_at) * 1000)

            # Handle scan failure
            if not scan_result.success:
                return ValidatorResult(
                    validator_name=self.name,
                    status=ValidatorStatus.ERROR,
                    message=f"SAST scan failed: {scan_result.error_message}",
                    details={"error": scan_result.error_message},
                    duration_ms=duration_ms,
                    blocking=False,  # Don't block on scan errors
                )

            # Process findings
            findings = scan_result.findings
            critical_findings = self._get_critical_findings(findings)
            blocking_findings = self._get_blocking_findings(findings)

            # Build details
            details = self._build_details(
                findings=findings,
                scan_result=scan_result,
                files_scanned=len(scannable_files),
            )

            # Determine status and blocking
            if critical_findings:
                status = ValidatorStatus.FAILED
                message = (
                    f"Found {len(critical_findings)} critical security issues "
                    f"({scan_result.errors} errors, {scan_result.warnings} warnings)"
                )
                blocking = True
            elif blocking_findings:
                status = ValidatorStatus.FAILED
                message = f"Found {len(blocking_findings)} security issues requiring review"
                blocking = self.config.blocking
            elif scan_result.warnings > 0:
                status = ValidatorStatus.PASSED
                message = f"Passed with {scan_result.warnings} security warnings"
                blocking = False
            else:
                status = ValidatorStatus.PASSED
                message = "No security issues found"
                blocking = False

            return ValidatorResult(
                validator_name=self.name,
                status=status,
                message=message,
                details=details,
                duration_ms=duration_ms,
                blocking=blocking,
            )

        except Exception as e:
            logger.error(f"SAST validation error: {e}", exc_info=True)
            duration_ms = int((time.time() - started_at) * 1000)
            return ValidatorResult(
                validator_name=self.name,
                status=ValidatorStatus.ERROR,
                message=f"SAST validation error: {str(e)}",
                details={"error": str(e)},
                duration_ms=duration_ms,
                blocking=False,
            )

    def _is_scannable(self, path: str) -> bool:
        """Check if file should be scanned."""
        return any(path.endswith(ext) for ext in self.SCANNABLE_EXTENSIONS)

    def _get_critical_findings(
        self, findings: List[SemgrepFinding]
    ) -> List[SemgrepFinding]:
        """Get critical severity findings."""
        return [f for f in findings if f.severity == SemgrepSeverity.ERROR]

    def _get_blocking_findings(
        self, findings: List[SemgrepFinding]
    ) -> List[SemgrepFinding]:
        """Get findings that should block merge."""
        return [
            f
            for f in findings
            if f.severity == SemgrepSeverity.ERROR
            or f.category in self.BLOCKING_CATEGORIES
        ]

    def _build_details(
        self,
        findings: List[SemgrepFinding],
        scan_result: Any,
        files_scanned: int,
    ) -> Dict[str, Any]:
        """Build detailed output for validator result."""
        # Group by severity
        by_severity = {
            "critical": [],
            "warning": [],
            "info": [],
        }

        for finding in findings[:50]:  # Limit to 50 findings
            finding_dict = {
                "file": finding.file_path,
                "line": finding.start_line,
                "rule": finding.rule_id,
                "category": finding.category.value,
                "message": finding.message,
                "cwe": finding.cwe,
                "owasp": finding.owasp,
            }

            if finding.severity == SemgrepSeverity.ERROR:
                by_severity["critical"].append(finding_dict)
            elif finding.severity == SemgrepSeverity.WARNING:
                by_severity["warning"].append(finding_dict)
            else:
                by_severity["info"].append(finding_dict)

        # Group by category
        by_category: Dict[str, int] = {}
        for finding in findings:
            cat = finding.category.value
            by_category[cat] = by_category.get(cat, 0) + 1

        # Group by file
        by_file: Dict[str, int] = {}
        for finding in findings:
            by_file[finding.file_path] = by_file.get(finding.file_path, 0) + 1

        return {
            "files_scanned": files_scanned,
            "rules_run": scan_result.rules_run,
            "total_findings": len(findings),
            "critical_count": scan_result.errors,
            "warning_count": scan_result.warnings,
            "info_count": scan_result.infos,
            "findings_by_severity": by_severity,
            "findings_by_category": by_category,
            "findings_by_file": dict(sorted(by_file.items(), key=lambda x: -x[1])[:10]),
            "scan_duration_ms": scan_result.duration_ms,
        }


class AISecurityValidator(BaseValidator):
    """
    AI-specific security validator for detecting AI/ML vulnerabilities.

    Detects:
    - Prompt injection vulnerabilities
    - Model extraction attacks
    - Data leakage in prompts
    - Unsafe AI API usage
    - PII exposure in training data
    """

    name = "ai-security"
    description = "AI/ML Security Validation"
    default_blocking = True
    default_timeout_seconds = 180

    # AI-specific patterns to detect
    AI_SECURITY_PATTERNS = {
        "prompt_injection": {
            "patterns": [
                r"user_input.*format\(",  # User input in format string
                r"f['\"].*\{.*user",  # User input in f-string
                r"\.format\(.*request\.",  # Request data in format
                r"prompt.*\+.*input",  # String concat with input
            ],
            "severity": SemgrepSeverity.ERROR,
            "message": "Potential prompt injection vulnerability",
        },
        "data_leakage": {
            "patterns": [
                r"print\(.*api_key",  # Printing API keys
                r"logger.*password",  # Logging passwords
                r"response.*secret",  # Secrets in response
            ],
            "severity": SemgrepSeverity.ERROR,
            "message": "Potential data leakage",
        },
        "unsafe_model_load": {
            "patterns": [
                r"pickle\.load",  # Unsafe pickle
                r"torch\.load\(",  # Unsafe torch load
                r"joblib\.load\(",  # Unsafe joblib load
            ],
            "severity": SemgrepSeverity.WARNING,
            "message": "Potentially unsafe model deserialization",
        },
    }

    async def validate(
        self,
        project_id: UUID,
        pr_number: str,
        files: List[str],
        diff: str,
    ) -> ValidatorResult:
        """
        Run AI security validation.

        Args:
            project_id: Project UUID
            pr_number: Pull request number
            files: List of changed file paths
            diff: Unified diff

        Returns:
            ValidatorResult with AI security findings
        """
        started_at = time.time()

        try:
            # Get Semgrep service with AI security rules
            ai_rules_path = self._get_ai_rules_path()
            semgrep = get_semgrep_service(custom_rules_path=ai_rules_path)

            # Filter AI-related files
            ai_files = [f for f in files if self._is_ai_related(f)]

            if not ai_files:
                duration_ms = int((time.time() - started_at) * 1000)
                return ValidatorResult(
                    validator_name=self.name,
                    status=ValidatorStatus.SKIPPED,
                    message="No AI-related files found",
                    details={"files_checked": 0},
                    duration_ms=duration_ms,
                    blocking=False,
                )

            # Scan files
            scan_result = await semgrep.scan_files(files=ai_files)

            duration_ms = int((time.time() - started_at) * 1000)

            if not scan_result.success:
                return ValidatorResult(
                    validator_name=self.name,
                    status=ValidatorStatus.ERROR,
                    message=f"AI security scan failed: {scan_result.error_message}",
                    details={"error": scan_result.error_message},
                    duration_ms=duration_ms,
                    blocking=False,
                )

            # Check for AI-specific patterns in diff
            ai_issues = self._check_ai_patterns(diff)

            # Combine findings
            total_issues = scan_result.errors + len(
                [i for i in ai_issues if i["severity"] == "error"]
            )

            if total_issues > 0:
                status = ValidatorStatus.FAILED
                message = f"Found {total_issues} AI security issues"
                blocking = True
            elif scan_result.warnings > 0 or ai_issues:
                status = ValidatorStatus.PASSED
                message = f"Passed with {scan_result.warnings + len(ai_issues)} warnings"
                blocking = False
            else:
                status = ValidatorStatus.PASSED
                message = "No AI security issues found"
                blocking = False

            return ValidatorResult(
                validator_name=self.name,
                status=status,
                message=message,
                details={
                    "files_scanned": len(ai_files),
                    "semgrep_findings": scan_result.errors + scan_result.warnings,
                    "pattern_findings": len(ai_issues),
                    "ai_issues": ai_issues[:20],
                },
                duration_ms=duration_ms,
                blocking=blocking,
            )

        except Exception as e:
            logger.error(f"AI security validation error: {e}", exc_info=True)
            duration_ms = int((time.time() - started_at) * 1000)
            return ValidatorResult(
                validator_name=self.name,
                status=ValidatorStatus.ERROR,
                message=f"AI security validation error: {str(e)}",
                details={"error": str(e)},
                duration_ms=duration_ms,
                blocking=False,
            )

    def _is_ai_related(self, path: str) -> bool:
        """Check if file is AI/ML related."""
        ai_indicators = [
            "ai",
            "ml",
            "model",
            "prompt",
            "llm",
            "embedding",
            "inference",
            "train",
            "predict",
            "agent",
            "chain",
            "langchain",
            "openai",
            "anthropic",
            "ollama",
        ]
        path_lower = path.lower()
        return any(ind in path_lower for ind in ai_indicators)

    def _get_ai_rules_path(self) -> Optional[str]:
        """Get path to AI security rules."""
        import os

        rules_path = "backend/policy-packs/semgrep/ai-security.yml"
        if os.path.exists(rules_path):
            return rules_path
        return None

    def _check_ai_patterns(self, diff: str) -> List[Dict[str, Any]]:
        """Check diff for AI-specific security patterns."""
        import re

        issues = []

        for pattern_name, config in self.AI_SECURITY_PATTERNS.items():
            for pattern in config["patterns"]:
                matches = re.findall(pattern, diff, re.IGNORECASE)
                if matches:
                    issues.append(
                        {
                            "pattern": pattern_name,
                            "severity": (
                                "error"
                                if config["severity"] == SemgrepSeverity.ERROR
                                else "warning"
                            ),
                            "message": config["message"],
                            "matches": len(matches),
                        }
                    )

        return issues
