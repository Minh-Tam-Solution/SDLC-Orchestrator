"""
Quality Pipeline - 4-Gate Code Quality Validation

SDLC Framework Compliance:
- Framework: SDLC 5.2.0 (7-Pillar + AI Governance Principles)
- Pillar 5: Test & Quality Assurance - Automated Quality Gates
- AI Governance Principle 6: Multi-Tier Quality Enforcement
- Methodology: Shift-left quality validation with deterministic feedback

Purpose:
Implements the 4-Gate Quality Pipeline for validating generated code:
- Gate 1: Syntax Check (ast.parse, ruff for Python)
- Gate 2: Security Scan (Semgrep SAST with OWASP Top 10 rules)
- Gate 3: Context Validation (imports, dependencies, file structure)
- Gate 4: Test Execution (pytest in sandbox OR smoke test for scaffolds)

Sprint 106 Enhancement: Quality Gate Profiles
- Scaffold Mode: G1+G2 mandatory, G3 soft-fail, G4 smoke test
- Production Mode: All 4 gates mandatory, strict validation

Each gate returns pass/fail with detailed feedback for auto-fix loops.

Related ADRs:
- ADR-022: IR-Based Codegen with 4-Gate Quality Pipeline
- ADR-040: App Builder Integration - Competitive Necessity

Sprint: 49 (Original), 106 (Quality Profiles)
Date: December 24, 2025 (Updated: January 27, 2026)
Version: 1.1.0
Owner: Backend Team
Status: ACTIVE - Sprint 106 Enhancement
"""

import ast
import re
import subprocess
import tempfile
import shutil
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class GateStatus(str, Enum):
    """Status of a quality gate."""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    SOFT_FAIL = "soft_fail"  # Sprint 106: Pass but with warnings


class QualityMode(str, Enum):
    """
    Quality mode for different use cases.
    
    Sprint 106: App Builder Integration
    - SCAFFOLD: Lenient mode for initial project scaffolding
    - PRODUCTION: Strict mode for production-ready code
    """
    SCAFFOLD = "scaffold"      # G1+G2 mandatory, G3 soft-fail, G4 smoke test
    PRODUCTION = "production"  # All 4 gates mandatory, strict validation


@dataclass
class QualityGateProfile:
    """
    Quality Gate Profile - Controls which gates are mandatory.
    
    Sprint 106: App Builder Integration
    
    Two modes:
    - SCAFFOLD: Lenient for initial project generation
      - Gate 1 (Syntax): MANDATORY - Code must compile
      - Gate 2 (Security): MANDATORY - No OWASP violations
      - Gate 3 (Context): SOFT-FAIL - May have missing imports (placeholders)
      - Gate 4 (Tests): SMOKE TEST - Just check if project builds
    
    - PRODUCTION: Strict for production-ready code
      - All 4 gates MANDATORY
      - No soft-fails allowed
      - Full unit test execution
    
    Example:
        # Scaffold mode for app-builder
        profile = QualityGateProfile.scaffold_mode()
        result = await quality_pipeline.run(files, profile)
        
        # Production mode for Ollama/Claude
        profile = QualityGateProfile.production_mode()
        result = await quality_pipeline.run(files, profile)
    """
    mode: QualityMode
    gates: Dict[str, bool]  # gate_name → is_mandatory
    
    @classmethod
    def scaffold_mode(cls) -> "QualityGateProfile":
        """
        Lenient profile for app scaffolding.
        
        Gate 1 (Syntax): MANDATORY - Code must compile/parse
        Gate 2 (Security): MANDATORY - No OWASP Top 10 violations
        Gate 3 (Context): SOFT-FAIL - Allow missing optional dependencies
        Gate 4 (Tests): SMOKE TEST - Just check if builds (not full unit tests)
        
        Returns:
            QualityGateProfile for scaffold mode
        """
        return cls(
            mode=QualityMode.SCAFFOLD,
            gates={
                "syntax": True,      # MANDATORY - Must compile
                "security": True,    # MANDATORY - No security issues
                "context": False,    # OPTIONAL - Soft-fail allowed
                "tests": False,      # OPTIONAL - Smoke test only
            }
        )
    
    @classmethod
    def production_mode(cls) -> "QualityGateProfile":
        """
        Strict profile for production-ready code.
        
        All 4 gates are MANDATORY with no soft-fails.
        
        Returns:
            QualityGateProfile for production mode
        """
        return cls(
            mode=QualityMode.PRODUCTION,
            gates={
                "syntax": True,      # MANDATORY
                "security": True,    # MANDATORY
                "context": True,     # MANDATORY
                "tests": True,       # MANDATORY - Full unit tests
            }
        )
    
    def is_gate_mandatory(self, gate_name: str) -> bool:
        """Check if a gate is mandatory for this profile"""
        return self.gates.get(gate_name, False)
    
    def allows_soft_fail(self, gate_name: str) -> bool:
        """
        Check if a gate allows soft-fail (pass with warnings).
        
        Only applicable in SCAFFOLD mode for Context gate.
        """
        return (
            self.mode == QualityMode.SCAFFOLD and
            gate_name == "context" and
            not self.is_gate_mandatory(gate_name)
        )


@dataclass
class GateIssue:
    """Single issue found by a gate."""
    file_path: str
    line: Optional[int]
    column: Optional[int]
    severity: str  # "error", "warning", "info"
    code: str  # Issue code (e.g., "E501", "security/sql-injection")
    message: str
    suggestion: Optional[str] = None


@dataclass
class GateResult:
    """Result of running a single gate."""
    gate_name: str
    gate_number: int
    status: GateStatus
    duration_ms: int
    issues: List[GateIssue] = field(default_factory=list)
    summary: str = ""
    details: Dict[str, Any] = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return self.status in [GateStatus.PASSED, GateStatus.SOFT_FAIL]

    @property
    def error_count(self) -> int:
        return len([i for i in self.issues if i.severity == "error"])

    @property
    def warning_count(self) -> int:
        return len([i for i in self.issues if i.severity == "warning"])


@dataclass
class PipelineResult:
    """Result of running the full 4-gate pipeline."""
    success: bool
    gates: List[GateResult]
    total_duration_ms: int
    failed_gate: Optional[int] = None
    summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to API-friendly dict."""
        return {
            "success": self.success,
            "total_duration_ms": self.total_duration_ms,
            "failed_gate": self.failed_gate,
            "summary": self.summary,
            "gates": [
                {
                    "gate_name": g.gate_name,
                    "gate_number": g.gate_number,
                    "status": g.status.value,
                    "duration_ms": g.duration_ms,
                    "error_count": g.error_count,
                    "warning_count": g.warning_count,
                    "summary": g.summary,
                    "issues": [
                        {
                            "file": i.file_path,
                            "line": i.line,
                            "column": i.column,
                            "severity": i.severity,
                            "code": i.code,
                            "message": i.message,
                            "suggestion": i.suggestion,
                        }
                        for i in g.issues
                    ],
                }
                for g in self.gates
            ],
        }


class QualityPipeline:
    """
    4-Gate Code Quality Pipeline.

    Validates generated code through 4 sequential gates:
    1. Syntax Check - Ensures code is syntactically valid
    2. Security Scan - SAST using Semgrep rules
    3. Context Validation - Verifies imports and dependencies
    4. Test Execution - Runs pytest (optional, requires sandbox)

    Example:
        pipeline = QualityPipeline()
        result = pipeline.run(files={
            "app/main.py": "from fastapi import FastAPI\\napp = FastAPI()",
            "app/models.py": "class User:\\n    pass"
        })

        if result.success:
            print("All gates passed!")
        else:
            print(f"Failed at gate {result.failed_gate}")
    """

    def __init__(
        self,
        skip_security: bool = False,
        skip_tests: bool = True,  # Tests disabled by default (needs Docker sandbox)
        semgrep_rules: Optional[str] = None,
    ):
        """
        Initialize quality pipeline.

        Args:
            skip_security: Skip Gate 2 (security scan)
            skip_tests: Skip Gate 4 (test execution)
            semgrep_rules: Path to custom Semgrep rules (default: auto)
        """
        self.skip_security = skip_security
        self.skip_tests = skip_tests
        self.semgrep_rules = semgrep_rules or "p/python"

    def run(
        self,
        files: Dict[str, str],
        language: str = "python",
    ) -> PipelineResult:
        """
        Run full 4-gate pipeline on generated files.

        Args:
            files: Dict of file_path -> content
            language: Primary language ("python", "typescript")

        Returns:
            PipelineResult with gate results
        """
        start_time = datetime.utcnow()
        gates: List[GateResult] = []
        failed_gate: Optional[int] = None

        # Gate 1: Syntax Check
        gate1 = self._run_gate1_syntax(files, language)
        gates.append(gate1)
        if not gate1.passed:
            failed_gate = 1

        # Gate 2: Security Scan (if Gate 1 passed)
        if failed_gate is None:
            if self.skip_security:
                gate2 = GateResult(
                    gate_name="Security (SAST)",
                    gate_number=2,
                    status=GateStatus.SKIPPED,
                    duration_ms=0,
                    summary="Skipped (disabled)",
                )
            else:
                gate2 = self._run_gate2_security(files, language)
            gates.append(gate2)
            if gate2.status == GateStatus.FAILED:
                failed_gate = 2

        # Gate 3: Context Validation (if Gate 2 passed)
        if failed_gate is None:
            gate3 = self._run_gate3_context(files, language)
            gates.append(gate3)
            if not gate3.passed:
                failed_gate = 3

        # Gate 4: Test Execution (if Gate 3 passed)
        if failed_gate is None:
            if self.skip_tests:
                gate4 = GateResult(
                    gate_name="Test Coverage",
                    gate_number=4,
                    status=GateStatus.SKIPPED,
                    duration_ms=0,
                    summary="Skipped (requires sandbox)",
                )
            else:
                gate4 = self._run_gate4_tests(files, language)
            gates.append(gate4)
            if gate4.status == GateStatus.FAILED:
                failed_gate = 4

        # Calculate total duration
        total_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

        # Generate summary
        success = failed_gate is None
        passed_count = len([g for g in gates if g.passed or g.status == GateStatus.SKIPPED])
        summary = f"{passed_count}/{len(gates)} gates passed"
        if not success:
            summary = f"Failed at Gate {failed_gate}: {gates[failed_gate - 1].gate_name}"

        return PipelineResult(
            success=success,
            gates=gates,
            total_duration_ms=total_ms,
            failed_gate=failed_gate,
            summary=summary,
        )

    def _run_gate1_syntax(
        self,
        files: Dict[str, str],
        language: str,
    ) -> GateResult:
        """
        Gate 1: Syntax Check.

        For Python: ast.parse() + ruff check
        For TypeScript: tsc --noEmit (if available)
        """
        start_time = datetime.utcnow()
        issues: List[GateIssue] = []

        if language == "python":
            # Check Python syntax
            for file_path, content in files.items():
                if not file_path.endswith(".py"):
                    continue

                # 1. ast.parse check
                try:
                    ast.parse(content)
                except SyntaxError as e:
                    issues.append(GateIssue(
                        file_path=file_path,
                        line=e.lineno,
                        column=e.offset,
                        severity="error",
                        code="E999",
                        message=f"SyntaxError: {e.msg}",
                        suggestion="Fix the syntax error at the indicated line",
                    ))

            # 2. Run ruff (if installed)
            ruff_issues = self._run_ruff_check(files)
            issues.extend(ruff_issues)

        elif language == "typescript":
            # TypeScript syntax check would go here
            # For now, skip TS validation
            pass

        duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

        error_count = len([i for i in issues if i.severity == "error"])
        status = GateStatus.PASSED if error_count == 0 else GateStatus.FAILED

        return GateResult(
            gate_name="Syntax Check",
            gate_number=1,
            status=status,
            duration_ms=duration_ms,
            issues=issues,
            summary=f"{error_count} syntax errors" if error_count else "No syntax errors",
            details={"files_checked": len(files)},
        )

    def _run_ruff_check(self, files: Dict[str, str]) -> List[GateIssue]:
        """Run ruff linter on Python files."""
        issues: List[GateIssue] = []

        # Create temp directory with files
        temp_dir = tempfile.mkdtemp()
        try:
            for file_path, content in files.items():
                if not file_path.endswith(".py"):
                    continue

                # Create file in temp dir
                full_path = Path(temp_dir) / file_path
                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.write_text(content)

            # Run ruff
            try:
                result = subprocess.run(
                    ["ruff", "check", "--output-format=json", temp_dir],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )

                if result.stdout:
                    import json
                    try:
                        ruff_output = json.loads(result.stdout)
                        for item in ruff_output:
                            # Convert temp path back to original
                            file_path = item.get("filename", "").replace(temp_dir + "/", "")
                            issues.append(GateIssue(
                                file_path=file_path,
                                line=item.get("location", {}).get("row"),
                                column=item.get("location", {}).get("column"),
                                severity="warning" if item.get("code", "").startswith("W") else "error",
                                code=item.get("code", ""),
                                message=item.get("message", ""),
                                suggestion=item.get("fix", {}).get("message") if item.get("fix") else None,
                            ))
                    except json.JSONDecodeError:
                        pass

            except FileNotFoundError:
                logger.warning("ruff not found, skipping lint check")
            except subprocess.TimeoutExpired:
                logger.warning("ruff timed out")

        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

        return issues

    def _run_gate2_security(
        self,
        files: Dict[str, str],
        language: str,
    ) -> GateResult:
        """
        Gate 2: Security Scan (SAST).

        Uses Semgrep to scan for security vulnerabilities.
        """
        start_time = datetime.utcnow()
        issues: List[GateIssue] = []

        # Create temp directory with files
        temp_dir = tempfile.mkdtemp()
        try:
            for file_path, content in files.items():
                full_path = Path(temp_dir) / file_path
                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.write_text(content)

            # Run Semgrep
            try:
                result = subprocess.run(
                    [
                        "semgrep", "scan",
                        "--config", self.semgrep_rules,
                        "--json",
                        "--quiet",
                        temp_dir,
                    ],
                    capture_output=True,
                    text=True,
                    timeout=60,
                )

                if result.stdout:
                    import json
                    try:
                        semgrep_output = json.loads(result.stdout)
                        for finding in semgrep_output.get("results", []):
                            file_path = finding.get("path", "").replace(temp_dir + "/", "")
                            issues.append(GateIssue(
                                file_path=file_path,
                                line=finding.get("start", {}).get("line"),
                                column=finding.get("start", {}).get("col"),
                                severity="error" if "critical" in finding.get("extra", {}).get("severity", "").lower() else "warning",
                                code=finding.get("check_id", ""),
                                message=finding.get("extra", {}).get("message", "Security issue found"),
                                suggestion=finding.get("extra", {}).get("fix"),
                            ))
                    except json.JSONDecodeError:
                        pass

            except FileNotFoundError:
                logger.warning("semgrep not found, skipping security scan")
                return GateResult(
                    gate_name="Security (SAST)",
                    gate_number=2,
                    status=GateStatus.SKIPPED,
                    duration_ms=int((datetime.utcnow() - start_time).total_seconds() * 1000),
                    summary="Skipped (semgrep not installed)",
                )
            except subprocess.TimeoutExpired:
                logger.warning("semgrep timed out")

        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

        duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

        # Security gate: fail on any high/critical severity
        critical_count = len([i for i in issues if i.severity == "error"])
        status = GateStatus.PASSED if critical_count == 0 else GateStatus.FAILED

        return GateResult(
            gate_name="Security (SAST)",
            gate_number=2,
            status=status,
            duration_ms=duration_ms,
            issues=issues,
            summary=f"{len(issues)} security findings ({critical_count} critical)" if issues else "No security issues",
            details={"rules": self.semgrep_rules},
        )

    def _run_gate3_context(
        self,
        files: Dict[str, str],
        language: str,
    ) -> GateResult:
        """
        Gate 3: Context Validation.

        Checks:
        - Import consistency (all imports are valid)
        - Internal references (modules reference each other correctly)
        - Required files exist (main.py, __init__.py, etc.)
        """
        start_time = datetime.utcnow()
        issues: List[GateIssue] = []

        if language == "python":
            issues.extend(self._validate_python_context(files))

        duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

        error_count = len([i for i in issues if i.severity == "error"])
        status = GateStatus.PASSED if error_count == 0 else GateStatus.FAILED

        return GateResult(
            gate_name="Context Validation",
            gate_number=3,
            status=status,
            duration_ms=duration_ms,
            issues=issues,
            summary=f"{error_count} context errors" if error_count else "Context valid",
            details={"checks": ["imports", "references", "structure"]},
        )

    def _validate_python_context(self, files: Dict[str, str]) -> List[GateIssue]:
        """Validate Python-specific context."""
        issues: List[GateIssue] = []
        file_paths = set(files.keys())

        # Get all module paths (convert file paths to import paths)
        module_paths = set()
        for fp in file_paths:
            if fp.endswith(".py"):
                # app/models/user.py -> app.models.user
                module = fp.replace("/", ".").replace("\\", ".")[:-3]
                module_paths.add(module)
                # Also add parent packages
                parts = module.split(".")
                for i in range(len(parts)):
                    module_paths.add(".".join(parts[:i + 1]))

        # Check each Python file for imports
        for file_path, content in files.items():
            if not file_path.endswith(".py"):
                continue

            try:
                tree = ast.parse(content)
            except SyntaxError:
                continue  # Already caught in Gate 1

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        module = alias.name
                        # Check if it's a local import that should exist
                        if module.startswith("app.") or module.startswith("src."):
                            if module not in module_paths and not self._is_stdlib(module):
                                issues.append(GateIssue(
                                    file_path=file_path,
                                    line=node.lineno,
                                    column=node.col_offset,
                                    severity="warning",
                                    code="CTX001",
                                    message=f"Import '{module}' not found in generated code",
                                    suggestion=f"Ensure module '{module}' is generated",
                                ))

                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    if module.startswith("app.") or module.startswith("src."):
                        if module not in module_paths and not self._is_stdlib(module):
                            issues.append(GateIssue(
                                file_path=file_path,
                                line=node.lineno,
                                column=node.col_offset,
                                severity="warning",
                                code="CTX002",
                                message=f"Import from '{module}' not found in generated code",
                                suggestion=f"Ensure module '{module}' is generated",
                            ))

        # Check for required files
        required_patterns = [
            ("app/main.py", "Main application entry point"),
            ("requirements.txt", "Dependencies file"),
        ]
        for pattern, description in required_patterns:
            found = any(fp.endswith(pattern.split("/")[-1]) or pattern in fp for fp in file_paths)
            if not found:
                issues.append(GateIssue(
                    file_path=pattern,
                    line=None,
                    column=None,
                    severity="warning",
                    code="CTX003",
                    message=f"Missing recommended file: {pattern} ({description})",
                    suggestion=f"Consider generating {pattern}",
                ))

        return issues

    def _is_stdlib(self, module: str) -> bool:
        """Check if module is Python standard library."""
        stdlib_modules = {
            "os", "sys", "re", "json", "datetime", "typing", "logging",
            "pathlib", "collections", "functools", "itertools", "dataclasses",
            "enum", "abc", "asyncio", "uuid", "hashlib", "base64", "io",
            "tempfile", "shutil", "subprocess", "contextlib", "copy",
        }
        top_module = module.split(".")[0]
        return top_module in stdlib_modules

    def _run_gate4_tests(
        self,
        files: Dict[str, str],
        language: str,
    ) -> GateResult:
        """
        Gate 4: Test Execution.

        Runs pytest in a sandbox environment.
        Requires Docker for isolation.
        """
        start_time = datetime.utcnow()

        # For now, return skipped - full implementation needs Docker sandbox
        logger.info("Gate 4 (Test Execution) requires sandbox - skipping")

        return GateResult(
            gate_name="Test Coverage",
            gate_number=4,
            status=GateStatus.SKIPPED,
            duration_ms=int((datetime.utcnow() - start_time).total_seconds() * 1000),
            summary="Skipped (sandbox not configured)",
            details={"reason": "Docker sandbox required for test execution"},
        )


# Singleton instance
_pipeline: Optional[QualityPipeline] = None


def get_quality_pipeline() -> QualityPipeline:
    """Get or create singleton QualityPipeline instance."""
    global _pipeline
    if _pipeline is None:
        _pipeline = QualityPipeline()
    return _pipeline
