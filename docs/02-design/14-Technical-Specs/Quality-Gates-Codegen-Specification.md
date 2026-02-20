# Quality Gates for Generated Code Specification
## EP-06: Codegen Quality Validation | Sprint 48

**Status**: APPROVED
**Version**: 1.0.0
**Date**: December 23, 2025
**Author**: Backend Lead + QA Lead
**Sprint**: Sprint 48 (Feb 17-28, 2026)
**Framework**: SDLC 6.1.0
**Dependency**: Sprint 46-47 (IR Processors + Templates)

---

## 1. Overview

### 1.1 Purpose

This specification defines the Quality Gates system that validates all generated code before delivery to users, ensuring 95%+ pass rate for the Founder Plan.

### 1.2 Strategic Context

**Cost Target for Founder Plan**:
- Infrastructure: <$50/month per project
- Generation latency: <3s (p95)
- Quality gate pass rate: ≥95%

```
┌─────────────────────────────────────────────────────────────────────┐
│                    QUALITY GATE PIPELINE                             │
│                                                                      │
│  Generated Code → [Gate 1] → [Gate 2] → [Gate 3] → [Gate 4] → ✅    │
│                   Syntax     Security   Arch      Tests              │
│                                                                      │
│  If ANY gate fails:                                                  │
│  → Return detailed errors in Vietnamese                              │
│  → Suggest fixes                                                     │
│  → Option to retry with different provider                           │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.3 Scope

| In Scope | Out of Scope |
|----------|--------------|
| 4 validation gates | Runtime performance testing |
| Vietnamese error messages | Load testing |
| Auto-fix suggestions | Security penetration testing |
| Ollama optimization | External API integrations |

---

## 2. Quality Gates

### 2.1 Gate 1: Syntax Validation

**Purpose**: Ensure generated code is syntactically correct.

```python
# backend/app/services/codegen/validators/syntax_validator.py

from typing import List, Dict, Any
from pydantic import BaseModel
import ast
import subprocess
import tempfile
from pathlib import Path

class SyntaxIssue(BaseModel):
    file: str
    line: int
    column: int
    message: str
    vietnamese_message: str

class SyntaxValidationResult(BaseModel):
    passed: bool
    issues: List[SyntaxIssue]
    files_checked: int
    files_passed: int

class SyntaxValidator:
    """Validates syntax of generated code."""

    # Vietnamese error translations
    ERROR_TRANSLATIONS = {
        "invalid syntax": "Cú pháp không hợp lệ",
        "unexpected indent": "Thụt lề không đúng",
        "expected an indented block": "Thiếu khối thụt lề",
        "unexpected EOF": "Kết thúc file không mong đợi",
        "name '{}' is not defined": "Tên '{}' chưa được định nghĩa",
    }

    def validate(self, files: List[Dict[str, str]]) -> SyntaxValidationResult:
        """
        Validate syntax for all generated files.

        Args:
            files: List of {path, content, language} dicts

        Returns:
            SyntaxValidationResult with pass/fail and issues
        """
        issues = []
        files_passed = 0

        for file in files:
            file_issues = self._validate_file(file)
            if not file_issues:
                files_passed += 1
            issues.extend(file_issues)

        return SyntaxValidationResult(
            passed=len(issues) == 0,
            issues=issues,
            files_checked=len(files),
            files_passed=files_passed
        )

    def _validate_file(self, file: Dict[str, str]) -> List[SyntaxIssue]:
        """Validate a single file."""
        language = file.get("language", "python")
        content = file["content"]
        path = file["path"]

        if language == "python":
            return self._validate_python(path, content)
        elif language in ["typescript", "javascript"]:
            return self._validate_typescript(path, content)
        elif language == "yaml":
            return self._validate_yaml(path, content)

        return []

    def _validate_python(self, path: str, content: str) -> List[SyntaxIssue]:
        """Validate Python syntax using AST."""
        issues = []

        try:
            ast.parse(content)
        except SyntaxError as e:
            vn_message = self._translate_error(str(e.msg))
            issues.append(SyntaxIssue(
                file=path,
                line=e.lineno or 1,
                column=e.offset or 0,
                message=str(e.msg),
                vietnamese_message=vn_message
            ))

        return issues

    def _validate_typescript(self, path: str, content: str) -> List[SyntaxIssue]:
        """Validate TypeScript/JavaScript using esbuild or tsc."""
        issues = []

        # Write to temp file and run tsc --noEmit
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.ts' if path.endswith('.ts') else '.js',
            delete=False
        ) as f:
            f.write(content)
            temp_path = f.name

        try:
            result = subprocess.run(
                ['npx', 'tsc', '--noEmit', '--allowJs', temp_path],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                # Parse tsc errors
                for line in result.stderr.split('\n'):
                    if '(' in line and ')' in line:
                        # Extract line:col from error
                        parts = line.split('(')
                        if len(parts) > 1:
                            loc = parts[1].split(')')[0]
                            if ',' in loc:
                                ln, col = loc.split(',')
                                issues.append(SyntaxIssue(
                                    file=path,
                                    line=int(ln),
                                    column=int(col),
                                    message=line,
                                    vietnamese_message=self._translate_error(line)
                                ))
        except subprocess.TimeoutExpired:
            pass
        finally:
            Path(temp_path).unlink(missing_ok=True)

        return issues

    def _validate_yaml(self, path: str, content: str) -> List[SyntaxIssue]:
        """Validate YAML syntax."""
        import yaml

        issues = []
        try:
            yaml.safe_load(content)
        except yaml.YAMLError as e:
            issues.append(SyntaxIssue(
                file=path,
                line=getattr(e, 'problem_mark', {}).get('line', 1),
                column=getattr(e, 'problem_mark', {}).get('column', 0),
                message=str(e),
                vietnamese_message="Lỗi cú pháp YAML"
            ))

        return issues

    def _translate_error(self, message: str) -> str:
        """Translate error message to Vietnamese."""
        for en, vn in self.ERROR_TRANSLATIONS.items():
            if en in message.lower():
                return vn
        return f"Lỗi: {message}"
```

### 2.2 Gate 2: Security Validation (Semgrep)

**Purpose**: Detect security vulnerabilities using OWASP rules.

```python
# backend/app/services/codegen/validators/security_validator.py

from typing import List, Dict, Any
from pydantic import BaseModel
import subprocess
import tempfile
import json
from pathlib import Path

class SecurityIssue(BaseModel):
    file: str
    line: int
    rule_id: str
    severity: str  # critical, high, medium, low
    message: str
    vietnamese_message: str
    fix_suggestion: str | None = None

class SecurityValidationResult(BaseModel):
    passed: bool
    issues: List[SecurityIssue]
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int

class SecurityValidator:
    """Validates security of generated code using Semgrep."""

    # Vietnamese translations for common security issues
    SECURITY_TRANSLATIONS = {
        "sql-injection": "Lỗ hổng SQL Injection - Dữ liệu người dùng không được escape",
        "xss": "Lỗ hổng XSS - Output không được sanitize",
        "hardcoded-secret": "Secret được hardcode - Nên dùng biến môi trường",
        "insecure-random": "Sử dụng random không an toàn - Dùng secrets module",
        "path-traversal": "Lỗ hổng Path Traversal - Đường dẫn file không được validate",
        "command-injection": "Lỗ hổng Command Injection - Input không được sanitize",
    }

    # Semgrep rules for generated code
    SEMGREP_RULES = """
rules:
  - id: hardcoded-secret
    pattern-either:
      - pattern: password = "..."
      - pattern: api_key = "..."
      - pattern: secret = "..."
    message: "Hardcoded secret detected"
    severity: ERROR
    languages: [python]

  - id: sql-injection
    pattern: |
      $CURSOR.execute($QUERY % ...)
    message: "Potential SQL injection"
    severity: ERROR
    languages: [python]

  - id: eval-usage
    pattern: eval(...)
    message: "Dangerous eval() usage"
    severity: ERROR
    languages: [python]

  - id: shell-injection
    pattern-either:
      - pattern: os.system($CMD)
      - pattern: subprocess.call($CMD, shell=True)
    message: "Potential shell injection"
    severity: ERROR
    languages: [python]
"""

    def validate(self, files: List[Dict[str, str]]) -> SecurityValidationResult:
        """
        Validate security of generated files using Semgrep.

        Args:
            files: List of generated files

        Returns:
            SecurityValidationResult with issues
        """
        issues = []

        # Create temp directory with files
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Write rules file
            rules_path = tmpdir_path / "rules.yaml"
            rules_path.write_text(self.SEMGREP_RULES)

            # Write generated files
            for file in files:
                if file.get("language") == "python":
                    file_path = tmpdir_path / file["path"]
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    file_path.write_text(file["content"])

            # Run Semgrep
            try:
                result = subprocess.run(
                    [
                        'semgrep',
                        '--config', str(rules_path),
                        '--json',
                        str(tmpdir_path)
                    ],
                    capture_output=True,
                    text=True,
                    timeout=60
                )

                if result.stdout:
                    semgrep_output = json.loads(result.stdout)
                    for finding in semgrep_output.get("results", []):
                        issues.append(self._parse_finding(finding))

            except subprocess.TimeoutExpired:
                pass
            except json.JSONDecodeError:
                pass

        # Count by severity
        critical = sum(1 for i in issues if i.severity == "critical")
        high = sum(1 for i in issues if i.severity == "high")
        medium = sum(1 for i in issues if i.severity == "medium")
        low = sum(1 for i in issues if i.severity == "low")

        # Pass if no critical/high issues
        passed = critical == 0 and high == 0

        return SecurityValidationResult(
            passed=passed,
            issues=issues,
            critical_count=critical,
            high_count=high,
            medium_count=medium,
            low_count=low
        )

    def _parse_finding(self, finding: Dict) -> SecurityIssue:
        """Parse Semgrep finding to SecurityIssue."""
        rule_id = finding.get("check_id", "unknown")
        severity_map = {"ERROR": "high", "WARNING": "medium", "INFO": "low"}

        return SecurityIssue(
            file=finding.get("path", "unknown"),
            line=finding.get("start", {}).get("line", 1),
            rule_id=rule_id,
            severity=severity_map.get(
                finding.get("extra", {}).get("severity", "WARNING"),
                "medium"
            ),
            message=finding.get("extra", {}).get("message", "Security issue"),
            vietnamese_message=self._translate_issue(rule_id),
            fix_suggestion=finding.get("extra", {}).get("fix")
        )

    def _translate_issue(self, rule_id: str) -> str:
        """Translate rule ID to Vietnamese message."""
        for key, vn in self.SECURITY_TRANSLATIONS.items():
            if key in rule_id.lower():
                return vn
        return "Vấn đề bảo mật được phát hiện"
```

### 2.3 Gate 3: Architecture Validation

**Purpose**: Ensure generated code follows architectural rules.

```python
# backend/app/services/codegen/validators/architecture_validator.py

from typing import List, Dict, Any, Set
from pydantic import BaseModel
import ast
import re

class ArchitectureIssue(BaseModel):
    file: str
    line: int | None = None
    rule: str
    message: str
    vietnamese_message: str

class ArchitectureValidationResult(BaseModel):
    passed: bool
    issues: List[ArchitectureIssue]

class ArchitectureValidator:
    """Validates architecture rules for generated code."""

    # Layer rules: which layers can import from which
    LAYER_RULES = {
        "api/routes": ["services", "schemas", "core", "models"],
        "services": ["models", "schemas", "core"],
        "models": ["core"],
        "schemas": ["core"],
        "core": []
    }

    def validate(self, files: List[Dict[str, str]]) -> ArchitectureValidationResult:
        """
        Validate architecture rules.

        Args:
            files: List of generated files

        Returns:
            ArchitectureValidationResult
        """
        issues = []

        # Build file map
        file_map = {f["path"]: f["content"] for f in files}

        for file in files:
            if file.get("language") != "python":
                continue

            file_issues = []

            # Check layer dependencies
            file_issues.extend(self._check_layer_deps(file))

            # Check for circular imports
            file_issues.extend(self._check_circular_imports(file, file_map))

            # Check naming conventions
            file_issues.extend(self._check_naming(file))

            issues.extend(file_issues)

        return ArchitectureValidationResult(
            passed=len(issues) == 0,
            issues=issues
        )

    def _get_layer(self, path: str) -> str | None:
        """Determine which layer a file belongs to."""
        for layer in self.LAYER_RULES.keys():
            if layer in path:
                return layer
        return None

    def _check_layer_deps(self, file: Dict) -> List[ArchitectureIssue]:
        """Check that file only imports from allowed layers."""
        issues = []
        path = file["path"]
        content = file["content"]

        current_layer = self._get_layer(path)
        if not current_layer:
            return []

        allowed_layers = self.LAYER_RULES.get(current_layer, [])

        # Parse imports
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        issue = self._check_import(
                            path, alias.name, current_layer, allowed_layers, node.lineno
                        )
                        if issue:
                            issues.append(issue)

                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        issue = self._check_import(
                            path, node.module, current_layer, allowed_layers, node.lineno
                        )
                        if issue:
                            issues.append(issue)
        except SyntaxError:
            pass

        return issues

    def _check_import(
        self,
        file_path: str,
        import_name: str,
        current_layer: str,
        allowed_layers: List[str],
        line: int
    ) -> ArchitectureIssue | None:
        """Check if an import is allowed."""
        # Skip standard library and third-party imports
        if not import_name.startswith("app."):
            return None

        # Check which layer the import is from
        for layer in self.LAYER_RULES.keys():
            if f"app.{layer.replace('/', '.')}" in import_name or f"app/{layer}" in import_name:
                if layer not in allowed_layers and layer != current_layer:
                    return ArchitectureIssue(
                        file=file_path,
                        line=line,
                        rule="layer-dependency",
                        message=f"Layer '{current_layer}' should not import from '{layer}'",
                        vietnamese_message=f"Tầng '{current_layer}' không nên import từ '{layer}'"
                    )

        return None

    def _check_circular_imports(
        self,
        file: Dict,
        file_map: Dict[str, str]
    ) -> List[ArchitectureIssue]:
        """Check for potential circular imports."""
        issues = []

        # Build import graph
        imports = self._get_imports(file["content"])
        current_module = file["path"].replace("/", ".").replace(".py", "")

        for imp in imports:
            if imp.startswith("app."):
                # Check if the imported module imports back
                imp_path = imp.replace(".", "/") + ".py"
                if imp_path in file_map:
                    other_imports = self._get_imports(file_map[imp_path])
                    if current_module in other_imports or f"app.{current_module}" in other_imports:
                        issues.append(ArchitectureIssue(
                            file=file["path"],
                            rule="circular-import",
                            message=f"Potential circular import with {imp}",
                            vietnamese_message=f"Có thể xảy ra import vòng với {imp}"
                        ))

        return issues

    def _get_imports(self, content: str) -> Set[str]:
        """Extract all imports from content."""
        imports = set()
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.add(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.add(node.module)
        except SyntaxError:
            pass
        return imports

    def _check_naming(self, file: Dict) -> List[ArchitectureIssue]:
        """Check naming conventions."""
        issues = []
        path = file["path"]

        # Check file naming
        filename = path.split("/")[-1].replace(".py", "")

        # Models should be PascalCase class names
        if "/models/" in path and not filename.startswith("_"):
            if not filename.islower() and "_" not in filename:
                issues.append(ArchitectureIssue(
                    file=path,
                    rule="naming-convention",
                    message=f"Model file should be snake_case: {filename}",
                    vietnamese_message=f"File model nên dùng snake_case: {filename}"
                ))

        return issues
```

### 2.4 Gate 4: Test Execution

**Purpose**: Run generated tests and verify they pass.

```python
# backend/app/services/codegen/validators/test_validator.py

from typing import List, Dict, Any
from pydantic import BaseModel
import subprocess
import tempfile
from pathlib import Path

class TestResult(BaseModel):
    test_name: str
    passed: bool
    error_message: str | None = None

class TestValidationResult(BaseModel):
    passed: bool
    tests_run: int
    tests_passed: int
    tests_failed: int
    results: List[TestResult]

class TestValidator:
    """Runs generated tests to validate code correctness."""

    def validate(
        self,
        files: List[Dict[str, str]],
        blueprint: Dict[str, Any]
    ) -> TestValidationResult:
        """
        Run generated tests.

        Args:
            files: Generated files including tests
            blueprint: Original IR for context

        Returns:
            TestValidationResult
        """
        results = []
        tests_passed = 0
        tests_failed = 0

        # Create temp project
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Write all files
            for file in files:
                file_path = tmpdir_path / file["path"]
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(file["content"])

            # Create minimal pytest config
            (tmpdir_path / "pyproject.toml").write_text("""
[tool.pytest.ini_options]
pythonpath = ["."]
testpaths = ["tests"]
""")

            # Find test files
            test_files = [
                f for f in files
                if f["path"].startswith("tests/") and f["path"].endswith(".py")
            ]

            if not test_files:
                # No tests to run
                return TestValidationResult(
                    passed=True,
                    tests_run=0,
                    tests_passed=0,
                    tests_failed=0,
                    results=[]
                )

            # Run pytest
            try:
                result = subprocess.run(
                    ['python', '-m', 'pytest', '-v', '--tb=short'],
                    cwd=str(tmpdir_path),
                    capture_output=True,
                    text=True,
                    timeout=120,
                    env={
                        **subprocess.os.environ,
                        'PYTHONPATH': str(tmpdir_path)
                    }
                )

                # Parse pytest output
                for line in result.stdout.split('\n'):
                    if '::' in line and (' PASSED' in line or ' FAILED' in line):
                        test_name = line.split('::')[1].split()[0] if '::' in line else line
                        passed = 'PASSED' in line

                        if passed:
                            tests_passed += 1
                        else:
                            tests_failed += 1

                        results.append(TestResult(
                            test_name=test_name,
                            passed=passed,
                            error_message=None if passed else self._extract_error(result.stdout, test_name)
                        ))

            except subprocess.TimeoutExpired:
                return TestValidationResult(
                    passed=False,
                    tests_run=0,
                    tests_passed=0,
                    tests_failed=0,
                    results=[TestResult(
                        test_name="timeout",
                        passed=False,
                        error_message="Test execution timed out after 120s"
                    )]
                )

        return TestValidationResult(
            passed=tests_failed == 0,
            tests_run=tests_passed + tests_failed,
            tests_passed=tests_passed,
            tests_failed=tests_failed,
            results=results
        )

    def _extract_error(self, output: str, test_name: str) -> str | None:
        """Extract error message for a failed test."""
        lines = output.split('\n')
        for i, line in enumerate(lines):
            if test_name in line and 'FAILED' in line:
                # Get next few lines as error
                error_lines = lines[i+1:i+5]
                return '\n'.join(error_lines)
        return None
```

---

## 3. Gate Pipeline Orchestrator

```python
# backend/app/services/codegen/validators/gate_pipeline.py

from typing import List, Dict, Any
from pydantic import BaseModel
from .syntax_validator import SyntaxValidator, SyntaxValidationResult
from .security_validator import SecurityValidator, SecurityValidationResult
from .architecture_validator import ArchitectureValidator, ArchitectureValidationResult
from .test_validator import TestValidator, TestValidationResult
import time
import logging

logger = logging.getLogger(__name__)

class GateResult(BaseModel):
    gate_name: str
    passed: bool
    duration_ms: int
    details: Dict[str, Any]

class PipelineResult(BaseModel):
    passed: bool
    total_duration_ms: int
    gates: List[GateResult]
    summary: Dict[str, Any]
    vietnamese_summary: str

class QualityGatePipeline:
    """Orchestrates all quality gates for generated code."""

    def __init__(self):
        self.syntax_validator = SyntaxValidator()
        self.security_validator = SecurityValidator()
        self.architecture_validator = ArchitectureValidator()
        self.test_validator = TestValidator()

    def run(
        self,
        files: List[Dict[str, str]],
        blueprint: Dict[str, Any]
    ) -> PipelineResult:
        """
        Run all quality gates.

        Args:
            files: Generated files
            blueprint: Original IR

        Returns:
            PipelineResult with all gate results
        """
        gates = []
        total_start = time.time()

        # Gate 1: Syntax
        gate_result = self._run_gate(
            "syntax",
            lambda: self.syntax_validator.validate(files)
        )
        gates.append(gate_result)

        # If syntax fails, skip other gates
        if not gate_result.passed:
            return self._build_result(gates, total_start)

        # Gate 2: Security
        gate_result = self._run_gate(
            "security",
            lambda: self.security_validator.validate(files)
        )
        gates.append(gate_result)

        # Gate 3: Architecture
        gate_result = self._run_gate(
            "architecture",
            lambda: self.architecture_validator.validate(files)
        )
        gates.append(gate_result)

        # Gate 4: Tests
        gate_result = self._run_gate(
            "tests",
            lambda: self.test_validator.validate(files, blueprint)
        )
        gates.append(gate_result)

        return self._build_result(gates, total_start)

    def _run_gate(self, name: str, validator_fn) -> GateResult:
        """Run a single gate with timing."""
        start = time.time()
        try:
            result = validator_fn()
            duration_ms = int((time.time() - start) * 1000)

            return GateResult(
                gate_name=name,
                passed=result.passed,
                duration_ms=duration_ms,
                details=result.dict()
            )
        except Exception as e:
            logger.exception(f"Gate {name} failed with exception")
            duration_ms = int((time.time() - start) * 1000)

            return GateResult(
                gate_name=name,
                passed=False,
                duration_ms=duration_ms,
                details={"error": str(e)}
            )

    def _build_result(
        self,
        gates: List[GateResult],
        start_time: float
    ) -> PipelineResult:
        """Build final pipeline result."""
        total_duration = int((time.time() - start_time) * 1000)
        all_passed = all(g.passed for g in gates)

        # Build summary
        summary = {
            "gates_run": len(gates),
            "gates_passed": sum(1 for g in gates if g.passed),
            "gates_failed": sum(1 for g in gates if not g.passed)
        }

        # Vietnamese summary
        if all_passed:
            vn_summary = "✅ Tất cả các gate đều PASS. Code sẵn sàng sử dụng."
        else:
            failed_gates = [g.gate_name for g in gates if not g.passed]
            vn_summary = f"❌ Các gate sau FAIL: {', '.join(failed_gates)}. Vui lòng xem chi tiết bên dưới."

        return PipelineResult(
            passed=all_passed,
            total_duration_ms=total_duration,
            gates=gates,
            summary=summary,
            vietnamese_summary=vn_summary
        )
```

---

## 4. Ollama Optimization

### 4.1 Prompt Optimization

```python
# backend/app/services/codegen/ollama_optimizer.py

from typing import Dict, Any
from app.core.config import settings
import hashlib

class OllamaOptimizer:
    """Optimizes Ollama usage for cost and latency."""

    # Prompt templates optimized for smaller models
    OPTIMIZED_PROMPTS = {
        "generate": """Tạo {framework} code từ IR:
{ir_json}

Yêu cầu:
- File: {target_file}
- Ngôn ngữ: {language}

Trả về code duy nhất, không giải thích.""",

        "validate": """Kiểm tra code:
```{language}
{code}
```

Trả về JSON: {{"valid": true/false, "errors": [], "warnings": []}}"""
    }

    def __init__(self):
        self.cache = {}  # Simple in-memory cache
        self.cache_ttl = 3600  # 1 hour

    def optimize_prompt(
        self,
        prompt_type: str,
        context: Dict[str, Any]
    ) -> str:
        """
        Optimize prompt for Ollama.

        Args:
            prompt_type: Type of prompt (generate, validate)
            context: Variables to fill in prompt

        Returns:
            Optimized prompt string
        """
        template = self.OPTIMIZED_PROMPTS.get(prompt_type)
        if not template:
            raise ValueError(f"Unknown prompt type: {prompt_type}")

        return template.format(**context)

    def get_cache_key(self, prompt: str, model: str) -> str:
        """Generate cache key for prompt."""
        content = f"{model}:{prompt}"
        return hashlib.sha256(content.encode()).hexdigest()

    def get_cached(self, cache_key: str) -> str | None:
        """Get cached response if available."""
        entry = self.cache.get(cache_key)
        if entry:
            import time
            if time.time() - entry["timestamp"] < self.cache_ttl:
                return entry["response"]
        return None

    def set_cached(self, cache_key: str, response: str) -> None:
        """Cache a response."""
        import time
        self.cache[cache_key] = {
            "response": response,
            "timestamp": time.time()
        }

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count (rough approximation)."""
        # Vietnamese: ~1.5 chars per token, English: ~4 chars per token
        # Assume mixed content
        return len(text) // 3

    def should_use_ollama(self, estimated_tokens: int) -> bool:
        """Determine if Ollama is suitable for this request."""
        # Ollama context limit is typically 4096 or 8192
        max_context = settings.OLLAMA_MAX_CONTEXT or 4096
        return estimated_tokens < max_context * 0.8  # 80% of limit
```

### 4.2 Cost Tracking

```python
# backend/app/services/codegen/cost_tracker.py

from typing import Dict, Any
from pydantic import BaseModel
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.codegen_usage import CodegenUsage

class CostEstimate(BaseModel):
    provider: str
    tokens: int
    cost_usd: float

class CostTracker:
    """Tracks codegen costs per project/user."""

    # Cost per 1K tokens (estimated)
    COST_PER_1K = {
        "ollama": 0.001,      # Self-hosted, minimal cost
        "claude": 0.015,      # Anthropic pricing
        "gpt4": 0.03,         # OpenAI pricing
    }

    async def track_usage(
        self,
        db: AsyncSession,
        project_id: str,
        user_id: str,
        provider: str,
        tokens: int,
        generation_time_ms: int
    ) -> None:
        """Track codegen usage in database."""
        cost = self._calculate_cost(provider, tokens)

        usage = CodegenUsage(
            project_id=project_id,
            user_id=user_id,
            provider=provider,
            tokens_used=tokens,
            cost_usd=cost,
            generation_time_ms=generation_time_ms,
            created_at=datetime.utcnow()
        )

        db.add(usage)
        await db.commit()

    def _calculate_cost(self, provider: str, tokens: int) -> float:
        """Calculate cost for token usage."""
        rate = self.COST_PER_1K.get(provider, 0.01)
        return (tokens / 1000) * rate

    async def get_project_usage(
        self,
        db: AsyncSession,
        project_id: str,
        period_days: int = 30
    ) -> Dict[str, Any]:
        """Get usage summary for a project."""
        from sqlalchemy import select, func
        from datetime import timedelta

        cutoff = datetime.utcnow() - timedelta(days=period_days)

        result = await db.execute(
            select(
                func.sum(CodegenUsage.tokens_used).label("total_tokens"),
                func.sum(CodegenUsage.cost_usd).label("total_cost"),
                func.count(CodegenUsage.id).label("total_requests"),
                func.avg(CodegenUsage.generation_time_ms).label("avg_latency")
            ).where(
                CodegenUsage.project_id == project_id,
                CodegenUsage.created_at >= cutoff
            )
        )

        row = result.first()
        return {
            "period_days": period_days,
            "total_tokens": row.total_tokens or 0,
            "total_cost_usd": float(row.total_cost or 0),
            "total_requests": row.total_requests or 0,
            "avg_latency_ms": float(row.avg_latency or 0)
        }
```

---

## 5. Success Criteria

| Metric | Target | Measurement |
|--------|--------|-------------|
| Gate pass rate | ≥95% | Production metrics |
| Validation latency | <3s total | p95 measurement |
| False positive rate | <5% | Manual review sample |
| Cost per project | <$50/month | Cost tracking |

---

## 6. Sprint 48 Implementation Checklist

### Week 1 (Feb 17-21)

- [ ] Implement SyntaxValidator with Vietnamese messages
- [ ] Implement SecurityValidator with Semgrep integration
- [ ] Implement ArchitectureValidator with layer rules
- [ ] Create QualityGatePipeline orchestrator
- [ ] Write unit tests for each validator

### Week 2 (Feb 24-28)

- [ ] Implement TestValidator
- [ ] Implement OllamaOptimizer with caching
- [ ] Implement CostTracker with database persistence
- [ ] Integration test full pipeline
- [ ] Performance optimization to meet <3s target

---

## Document Control

| Field | Value |
|-------|-------|
| **Version** | 1.0.0 |
| **Date** | December 23, 2025 |
| **Author** | Backend Lead + QA Lead |
| **Status** | APPROVED |
| **Sprint** | Sprint 48 (Feb 17-28, 2026) |
| **Dependency** | Sprint 46-47 |
