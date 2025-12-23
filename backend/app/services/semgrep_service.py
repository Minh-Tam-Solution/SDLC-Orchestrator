"""
Semgrep Service - Static Application Security Testing

SDLC Stage: 04 - BUILD
Sprint: 43 - Policy Guards & Evidence UI
Framework: SDLC 5.1.1
Epic: EP-02 AI Safety Layer v1

Purpose:
Async wrapper for Semgrep CLI providing SAST capabilities.
Detects security vulnerabilities using rule-based pattern matching.

Features:
- Async subprocess execution for non-blocking scans
- Custom rule support (built-in + project-specific)
- OWASP Top 10 detection
- SARIF output parsing for standardized results
- Caching for rule validation
- Timeout and error handling

Architecture:
- Uses subprocess to call semgrep CLI (no SDK dependency)
- Parses SARIF JSON output for structured results
- Supports parallel file scanning
- Integrates with ValidationPipeline via SASTValidator

Reference:
- Semgrep CLI: https://semgrep.dev/docs/cli-reference
- SARIF Format: https://docs.oasis-open.org/sarif/sarif/v2.1.0/sarif-v2.1.0.html
"""

import asyncio
import json
import logging
import os
import tempfile
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class SemgrepSeverity(str, Enum):
    """Semgrep finding severity levels."""

    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"


class SemgrepCategory(str, Enum):
    """OWASP Top 10 + security categories."""

    INJECTION = "injection"
    BROKEN_AUTH = "broken-authentication"
    SENSITIVE_DATA = "sensitive-data-exposure"
    XXE = "xxe"
    BROKEN_ACCESS = "broken-access-control"
    SECURITY_MISCONFIG = "security-misconfiguration"
    XSS = "xss"
    INSECURE_DESERIALIZATION = "insecure-deserialization"
    VULNERABLE_COMPONENTS = "vulnerable-components"
    INSUFFICIENT_LOGGING = "insufficient-logging"
    SECRETS = "secrets"
    CRYPTO = "cryptography"
    PATH_TRAVERSAL = "path-traversal"
    COMMAND_INJECTION = "command-injection"
    SSRF = "ssrf"
    OTHER = "other"


@dataclass
class SemgrepFinding:
    """Single security finding from Semgrep scan."""

    # Location
    file_path: str
    start_line: int
    end_line: int
    start_col: int
    end_col: int

    # Rule info
    rule_id: str
    rule_name: str
    severity: SemgrepSeverity
    category: SemgrepCategory

    # Details
    message: str
    snippet: str
    fix_suggestion: Optional[str] = None

    # Metadata
    cwe: List[str] = field(default_factory=list)
    owasp: List[str] = field(default_factory=list)
    references: List[str] = field(default_factory=list)

    # Confidence
    confidence: str = "high"  # high, medium, low

    def to_dict(self) -> dict:
        """Convert to dict for JSON serialization."""
        return {
            "file_path": self.file_path,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "start_col": self.start_col,
            "end_col": self.end_col,
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "severity": self.severity.value,
            "category": self.category.value,
            "message": self.message,
            "snippet": self.snippet,
            "fix_suggestion": self.fix_suggestion,
            "cwe": self.cwe,
            "owasp": self.owasp,
            "references": self.references,
            "confidence": self.confidence,
        }


@dataclass
class SemgrepScanResult:
    """Complete result from a Semgrep scan."""

    # Status
    success: bool
    error_message: Optional[str] = None

    # Findings
    findings: List[SemgrepFinding] = field(default_factory=list)

    # Statistics
    files_scanned: int = 0
    rules_run: int = 0
    duration_ms: int = 0

    # Summary by severity
    errors: int = 0
    warnings: int = 0
    infos: int = 0

    def to_dict(self) -> dict:
        """Convert to dict for JSON serialization."""
        return {
            "success": self.success,
            "error_message": self.error_message,
            "findings": [f.to_dict() for f in self.findings],
            "files_scanned": self.files_scanned,
            "rules_run": self.rules_run,
            "duration_ms": self.duration_ms,
            "errors": self.errors,
            "warnings": self.warnings,
            "infos": self.infos,
        }


class SemgrepService:
    """
    Async Semgrep service for SAST scanning.

    Features:
    - Custom rule support
    - OWASP Top 10 detection
    - Parallel scanning
    - SARIF output parsing
    """

    # Default rulesets (can be customized)
    DEFAULT_RULESETS = [
        "p/python",
        "p/security-audit",
        "p/owasp-top-ten",
        "p/secrets",
    ]

    # Timeout for scan (seconds)
    DEFAULT_TIMEOUT = 300  # 5 minutes

    # Max files per scan
    MAX_FILES_PER_SCAN = 100

    def __init__(
        self,
        custom_rules_path: Optional[str] = None,
        rulesets: Optional[List[str]] = None,
        timeout_seconds: int = DEFAULT_TIMEOUT,
    ):
        """
        Initialize Semgrep service.

        Args:
            custom_rules_path: Path to custom .semgrep.yml rules
            rulesets: List of Semgrep rulesets to use
            timeout_seconds: Scan timeout in seconds
        """
        self.custom_rules_path = custom_rules_path
        self.rulesets = rulesets or self.DEFAULT_RULESETS
        self.timeout_seconds = timeout_seconds
        self._semgrep_available: Optional[bool] = None

    async def check_availability(self) -> bool:
        """
        Check if Semgrep CLI is available.

        Returns:
            True if semgrep is installed and accessible
        """
        if self._semgrep_available is not None:
            return self._semgrep_available

        try:
            process = await asyncio.create_subprocess_shell(
                "semgrep --version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await asyncio.wait_for(process.communicate(), timeout=10)

            self._semgrep_available = process.returncode == 0
            if self._semgrep_available:
                version = stdout.decode().strip()
                logger.info(f"Semgrep available: {version}")
            else:
                logger.warning("Semgrep not available")

            return self._semgrep_available

        except (asyncio.TimeoutError, FileNotFoundError):
            self._semgrep_available = False
            logger.warning("Semgrep CLI not installed")
            return False

    async def scan_files(
        self,
        files: List[str],
        project_root: Optional[str] = None,
        additional_rules: Optional[List[str]] = None,
    ) -> SemgrepScanResult:
        """
        Scan specific files for security issues.

        Args:
            files: List of file paths to scan
            project_root: Project root directory (for context)
            additional_rules: Additional ruleset paths

        Returns:
            SemgrepScanResult with findings
        """
        start_time = time.time()

        # Check availability
        if not await self.check_availability():
            return SemgrepScanResult(
                success=False,
                error_message="Semgrep CLI not installed",
                duration_ms=int((time.time() - start_time) * 1000),
            )

        # Filter to existing files
        existing_files = [f for f in files if os.path.exists(f)]
        if not existing_files:
            return SemgrepScanResult(
                success=True,
                files_scanned=0,
                duration_ms=int((time.time() - start_time) * 1000),
            )

        # Limit files
        scan_files = existing_files[: self.MAX_FILES_PER_SCAN]

        try:
            # Build command
            cmd = await self._build_scan_command(
                scan_files, project_root, additional_rules
            )

            logger.info(f"Running Semgrep scan on {len(scan_files)} files")

            # Execute scan
            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=self.timeout_seconds
            )

            # Parse SARIF output
            result = self._parse_sarif_output(stdout.decode())
            result.files_scanned = len(scan_files)
            result.duration_ms = int((time.time() - start_time) * 1000)

            # Log summary
            logger.info(
                f"Semgrep scan complete: {len(result.findings)} findings "
                f"({result.errors} errors, {result.warnings} warnings, {result.infos} info)"
            )

            return result

        except asyncio.TimeoutError:
            logger.error(f"Semgrep scan timed out after {self.timeout_seconds}s")
            return SemgrepScanResult(
                success=False,
                error_message=f"Scan timed out after {self.timeout_seconds} seconds",
                files_scanned=len(scan_files),
                duration_ms=int((time.time() - start_time) * 1000),
            )

        except Exception as e:
            logger.error(f"Semgrep scan error: {e}", exc_info=True)
            return SemgrepScanResult(
                success=False,
                error_message=str(e),
                files_scanned=len(scan_files),
                duration_ms=int((time.time() - start_time) * 1000),
            )

    async def scan_directory(
        self,
        directory: str,
        exclude_patterns: Optional[List[str]] = None,
    ) -> SemgrepScanResult:
        """
        Scan entire directory for security issues.

        Args:
            directory: Directory path to scan
            exclude_patterns: Glob patterns to exclude

        Returns:
            SemgrepScanResult with findings
        """
        start_time = time.time()

        if not os.path.isdir(directory):
            return SemgrepScanResult(
                success=False,
                error_message=f"Directory not found: {directory}",
                duration_ms=int((time.time() - start_time) * 1000),
            )

        if not await self.check_availability():
            return SemgrepScanResult(
                success=False,
                error_message="Semgrep CLI not installed",
                duration_ms=int((time.time() - start_time) * 1000),
            )

        try:
            # Build command for directory scan
            cmd_parts = ["semgrep", "--sarif", "--quiet"]

            # Add rulesets
            for ruleset in self.rulesets:
                cmd_parts.extend(["--config", ruleset])

            # Add custom rules if available
            if self.custom_rules_path and os.path.exists(self.custom_rules_path):
                cmd_parts.extend(["--config", self.custom_rules_path])

            # Add exclusions
            default_excludes = [
                "node_modules",
                ".git",
                "__pycache__",
                "*.min.js",
                "dist",
                "build",
                ".venv",
                "venv",
            ]
            for pattern in default_excludes + (exclude_patterns or []):
                cmd_parts.extend(["--exclude", pattern])

            # Add directory
            cmd_parts.append(directory)

            cmd = " ".join(cmd_parts)
            logger.info(f"Running Semgrep directory scan: {directory}")

            # Execute
            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=self.timeout_seconds
            )

            # Parse output
            result = self._parse_sarif_output(stdout.decode())
            result.duration_ms = int((time.time() - start_time) * 1000)

            return result

        except asyncio.TimeoutError:
            return SemgrepScanResult(
                success=False,
                error_message=f"Directory scan timed out after {self.timeout_seconds}s",
                duration_ms=int((time.time() - start_time) * 1000),
            )

        except Exception as e:
            logger.error(f"Semgrep directory scan error: {e}", exc_info=True)
            return SemgrepScanResult(
                success=False,
                error_message=str(e),
                duration_ms=int((time.time() - start_time) * 1000),
            )

    async def scan_code_snippet(
        self,
        code: str,
        language: str,
        rules: Optional[List[str]] = None,
    ) -> SemgrepScanResult:
        """
        Scan a code snippet for security issues.

        Args:
            code: Source code to scan
            language: Programming language (python, javascript, etc)
            rules: Specific rules to apply

        Returns:
            SemgrepScanResult with findings
        """
        start_time = time.time()

        if not await self.check_availability():
            return SemgrepScanResult(
                success=False,
                error_message="Semgrep CLI not installed",
                duration_ms=int((time.time() - start_time) * 1000),
            )

        # Language to extension mapping
        lang_ext = {
            "python": ".py",
            "javascript": ".js",
            "typescript": ".ts",
            "java": ".java",
            "go": ".go",
            "ruby": ".rb",
            "php": ".php",
            "c": ".c",
            "cpp": ".cpp",
            "csharp": ".cs",
        }

        ext = lang_ext.get(language.lower(), ".txt")

        try:
            # Create temp file with code
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=ext, delete=False
            ) as temp_file:
                temp_file.write(code)
                temp_path = temp_file.name

            try:
                result = await self.scan_files([temp_path], additional_rules=rules)
                result.files_scanned = 1
                return result
            finally:
                # Cleanup temp file
                os.unlink(temp_path)

        except Exception as e:
            logger.error(f"Semgrep snippet scan error: {e}", exc_info=True)
            return SemgrepScanResult(
                success=False,
                error_message=str(e),
                duration_ms=int((time.time() - start_time) * 1000),
            )

    async def _build_scan_command(
        self,
        files: List[str],
        project_root: Optional[str],
        additional_rules: Optional[List[str]],
    ) -> str:
        """Build semgrep command with all options."""
        cmd_parts = ["semgrep", "--sarif", "--quiet"]

        # Add rulesets
        for ruleset in self.rulesets:
            cmd_parts.extend(["--config", ruleset])

        # Add custom rules
        if self.custom_rules_path and os.path.exists(self.custom_rules_path):
            cmd_parts.extend(["--config", self.custom_rules_path])

        # Add additional rules
        if additional_rules:
            for rule in additional_rules:
                cmd_parts.extend(["--config", rule])

        # Add files (quoted for safety)
        for f in files:
            cmd_parts.append(f'"{f}"')

        return " ".join(cmd_parts)

    def _parse_sarif_output(self, output: str) -> SemgrepScanResult:
        """
        Parse SARIF JSON output from Semgrep.

        Args:
            output: SARIF JSON string

        Returns:
            SemgrepScanResult with parsed findings
        """
        if not output.strip():
            return SemgrepScanResult(success=True)

        try:
            sarif = json.loads(output)
        except json.JSONDecodeError as e:
            return SemgrepScanResult(
                success=False, error_message=f"Failed to parse SARIF output: {e}"
            )

        findings: List[SemgrepFinding] = []
        rules_map: Dict[str, Any] = {}

        # Extract rules from run
        runs = sarif.get("runs", [])
        for run in runs:
            # Build rules map
            for rule in run.get("tool", {}).get("driver", {}).get("rules", []):
                rules_map[rule.get("id", "")] = rule

            # Parse results
            for result in run.get("results", []):
                finding = self._parse_sarif_result(result, rules_map)
                if finding:
                    findings.append(finding)

        # Count by severity
        errors = sum(1 for f in findings if f.severity == SemgrepSeverity.ERROR)
        warnings = sum(1 for f in findings if f.severity == SemgrepSeverity.WARNING)
        infos = sum(1 for f in findings if f.severity == SemgrepSeverity.INFO)

        return SemgrepScanResult(
            success=True,
            findings=findings,
            rules_run=len(rules_map),
            errors=errors,
            warnings=warnings,
            infos=infos,
        )

    def _parse_sarif_result(
        self, result: Dict[str, Any], rules_map: Dict[str, Any]
    ) -> Optional[SemgrepFinding]:
        """Parse single SARIF result into SemgrepFinding."""
        try:
            rule_id = result.get("ruleId", "unknown")
            rule = rules_map.get(rule_id, {})

            # Get location
            locations = result.get("locations", [])
            if not locations:
                return None

            location = locations[0].get("physicalLocation", {})
            artifact = location.get("artifactLocation", {})
            region = location.get("region", {})

            file_path = artifact.get("uri", "")
            start_line = region.get("startLine", 1)
            end_line = region.get("endLine", start_line)
            start_col = region.get("startColumn", 1)
            end_col = region.get("endColumn", 1)
            snippet = region.get("snippet", {}).get("text", "")

            # Get severity
            level = result.get("level", "warning").upper()
            if level == "ERROR":
                severity = SemgrepSeverity.ERROR
            elif level == "WARNING":
                severity = SemgrepSeverity.WARNING
            else:
                severity = SemgrepSeverity.INFO

            # Get category from rule metadata
            properties = rule.get("properties", {})
            category_str = properties.get("category", "other").lower()
            category = self._map_category(category_str)

            # Get message
            message_obj = result.get("message", {})
            message = message_obj.get("text", rule.get("shortDescription", {}).get("text", ""))

            # Get CWE and OWASP
            cwe = properties.get("cwe", [])
            if isinstance(cwe, str):
                cwe = [cwe]
            owasp = properties.get("owasp", [])
            if isinstance(owasp, str):
                owasp = [owasp]

            # Get references
            references = rule.get("helpUri", [])
            if isinstance(references, str):
                references = [references]

            # Get fix suggestion
            fixes = result.get("fixes", [])
            fix_suggestion = None
            if fixes:
                fix_changes = fixes[0].get("changes", [])
                if fix_changes:
                    fix_suggestion = fix_changes[0].get("insertedContent", {}).get(
                        "text"
                    )

            return SemgrepFinding(
                file_path=file_path,
                start_line=start_line,
                end_line=end_line,
                start_col=start_col,
                end_col=end_col,
                rule_id=rule_id,
                rule_name=rule.get("name", rule_id),
                severity=severity,
                category=category,
                message=message,
                snippet=snippet,
                fix_suggestion=fix_suggestion,
                cwe=cwe,
                owasp=owasp,
                references=references,
                confidence=properties.get("confidence", "high"),
            )

        except Exception as e:
            logger.warning(f"Failed to parse SARIF result: {e}")
            return None

    def _map_category(self, category_str: str) -> SemgrepCategory:
        """Map Semgrep category string to enum."""
        category_mapping = {
            "injection": SemgrepCategory.INJECTION,
            "sql-injection": SemgrepCategory.INJECTION,
            "command-injection": SemgrepCategory.COMMAND_INJECTION,
            "xss": SemgrepCategory.XSS,
            "cross-site-scripting": SemgrepCategory.XSS,
            "ssrf": SemgrepCategory.SSRF,
            "server-side-request-forgery": SemgrepCategory.SSRF,
            "path-traversal": SemgrepCategory.PATH_TRAVERSAL,
            "directory-traversal": SemgrepCategory.PATH_TRAVERSAL,
            "secrets": SemgrepCategory.SECRETS,
            "hardcoded-secrets": SemgrepCategory.SECRETS,
            "crypto": SemgrepCategory.CRYPTO,
            "cryptography": SemgrepCategory.CRYPTO,
            "authentication": SemgrepCategory.BROKEN_AUTH,
            "auth": SemgrepCategory.BROKEN_AUTH,
            "authorization": SemgrepCategory.BROKEN_ACCESS,
            "access-control": SemgrepCategory.BROKEN_ACCESS,
            "sensitive-data": SemgrepCategory.SENSITIVE_DATA,
            "xxe": SemgrepCategory.XXE,
            "deserialization": SemgrepCategory.INSECURE_DESERIALIZATION,
            "security-misconfiguration": SemgrepCategory.SECURITY_MISCONFIG,
            "misconfiguration": SemgrepCategory.SECURITY_MISCONFIG,
            "logging": SemgrepCategory.INSUFFICIENT_LOGGING,
            "vulnerable-components": SemgrepCategory.VULNERABLE_COMPONENTS,
            "dependency": SemgrepCategory.VULNERABLE_COMPONENTS,
        }

        for key, value in category_mapping.items():
            if key in category_str.lower():
                return value

        return SemgrepCategory.OTHER


# Global service instance
_semgrep_service: Optional[SemgrepService] = None


def get_semgrep_service(
    custom_rules_path: Optional[str] = None,
    rulesets: Optional[List[str]] = None,
) -> SemgrepService:
    """
    Get or create Semgrep service instance.

    Args:
        custom_rules_path: Path to custom rules (optional)
        rulesets: List of rulesets to use (optional)

    Returns:
        SemgrepService instance
    """
    global _semgrep_service

    if _semgrep_service is None:
        # Check for custom rules in project
        project_rules = Path("backend/.semgrep.yml")
        if project_rules.exists():
            custom_rules_path = str(project_rules)

        _semgrep_service = SemgrepService(
            custom_rules_path=custom_rules_path,
            rulesets=rulesets,
        )

    return _semgrep_service
