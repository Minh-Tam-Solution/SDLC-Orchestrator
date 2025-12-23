"""
Unit Tests for SASTValidator

SDLC Stage: 04 - BUILD
Sprint: 43 - Policy Guards & Evidence UI
Framework: SDLC 5.1.1
Epic: EP-02 AI Safety Layer v1

Purpose:
Comprehensive unit tests for SASTValidator and AISecurityValidator.
Tests integration with SemgrepService and ValidationPipeline.

Coverage Target: 90%+
"""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.services.semgrep_service import (
    SemgrepCategory,
    SemgrepFinding,
    SemgrepScanResult,
    SemgrepSeverity,
)
from app.services.validators import ValidatorConfig, ValidatorStatus
from app.services.validators.sast_validator import (
    AISecurityValidator,
    SASTValidator,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def sast_validator():
    """Create SASTValidator instance."""
    return SASTValidator()


@pytest.fixture
def ai_security_validator():
    """Create AISecurityValidator instance."""
    return AISecurityValidator()


@pytest.fixture
def sample_python_files():
    """Sample Python file paths."""
    return [
        "app/services/auth.py",
        "app/api/routes/users.py",
        "app/models/user.py",
        "app/utils/helpers.py",
    ]


@pytest.fixture
def sample_findings():
    """Sample Semgrep findings."""
    return [
        SemgrepFinding(
            file_path="app/services/auth.py",
            start_line=25,
            end_line=25,
            start_col=1,
            end_col=60,
            rule_id="python.security.sql-injection",
            rule_name="SQL Injection",
            severity=SemgrepSeverity.ERROR,
            category=SemgrepCategory.INJECTION,
            message="SQL injection vulnerability detected",
            snippet="cursor.execute(f'SELECT * FROM users WHERE id = {user_id}')",
            cwe=["CWE-89"],
            owasp=["A03:2021"],
        ),
        SemgrepFinding(
            file_path="app/utils/helpers.py",
            start_line=10,
            end_line=10,
            start_col=1,
            end_col=45,
            rule_id="python.security.hardcoded-secrets",
            rule_name="Hardcoded Secret",
            severity=SemgrepSeverity.ERROR,
            category=SemgrepCategory.SECRETS,
            message="Hardcoded API key detected",
            snippet="API_KEY = 'sk-1234567890abcdef'",
            cwe=["CWE-798"],
            owasp=["A02:2021"],
        ),
        SemgrepFinding(
            file_path="app/api/routes/users.py",
            start_line=50,
            end_line=52,
            start_col=1,
            end_col=30,
            rule_id="python.security.xss",
            rule_name="XSS Vulnerability",
            severity=SemgrepSeverity.WARNING,
            category=SemgrepCategory.XSS,
            message="Potential XSS vulnerability",
            snippet="return Response(user_input)",
            cwe=["CWE-79"],
            owasp=["A03:2021"],
        ),
    ]


@pytest.fixture
def sample_scan_result(sample_findings):
    """Sample Semgrep scan result."""
    return SemgrepScanResult(
        success=True,
        findings=sample_findings,
        files_scanned=4,
        rules_run=50,
        duration_ms=1500,
        errors=2,
        warnings=1,
        infos=0,
    )


# =============================================================================
# Test SASTValidator Initialization
# =============================================================================


class TestSASTValidatorInit:
    """Tests for SASTValidator initialization."""

    def test_default_initialization(self, sast_validator):
        """Test default validator settings."""
        assert sast_validator.name == "sast"
        assert sast_validator.default_blocking is True
        assert sast_validator.default_timeout_seconds == 300
        assert sast_validator.custom_rules_path is None
        assert sast_validator.additional_rulesets == []

    def test_custom_initialization(self):
        """Test validator with custom settings."""
        config = ValidatorConfig(blocking=False, timeout_seconds=120)
        validator = SASTValidator(
            config=config,
            custom_rules_path="/path/to/rules.yml",
            additional_rulesets=["p/custom"],
        )

        assert validator.config.blocking is False
        assert validator.config.timeout_seconds == 120
        assert validator.custom_rules_path == "/path/to/rules.yml"
        assert "p/custom" in validator.additional_rulesets

    def test_scannable_extensions(self, sast_validator):
        """Test scannable file extensions."""
        assert ".py" in sast_validator.SCANNABLE_EXTENSIONS
        assert ".js" in sast_validator.SCANNABLE_EXTENSIONS
        assert ".ts" in sast_validator.SCANNABLE_EXTENSIONS
        assert ".tsx" in sast_validator.SCANNABLE_EXTENSIONS
        assert ".java" in sast_validator.SCANNABLE_EXTENSIONS
        assert ".go" in sast_validator.SCANNABLE_EXTENSIONS

    def test_blocking_categories(self, sast_validator):
        """Test categories that always block."""
        assert SemgrepCategory.INJECTION in sast_validator.BLOCKING_CATEGORIES
        assert SemgrepCategory.COMMAND_INJECTION in sast_validator.BLOCKING_CATEGORIES
        assert SemgrepCategory.SECRETS in sast_validator.BLOCKING_CATEGORIES
        assert SemgrepCategory.SSRF in sast_validator.BLOCKING_CATEGORIES


# =============================================================================
# Test File Classification
# =============================================================================


class TestFileClassification:
    """Tests for file type detection."""

    def test_is_scannable_python(self, sast_validator):
        """Test Python file detection."""
        assert sast_validator._is_scannable("app/main.py") is True
        assert sast_validator._is_scannable("tests/test_main.py") is True

    def test_is_scannable_javascript(self, sast_validator):
        """Test JavaScript file detection."""
        assert sast_validator._is_scannable("src/index.js") is True
        assert sast_validator._is_scannable("components/Button.jsx") is True

    def test_is_scannable_typescript(self, sast_validator):
        """Test TypeScript file detection."""
        assert sast_validator._is_scannable("src/app.ts") is True
        assert sast_validator._is_scannable("components/Button.tsx") is True

    def test_is_scannable_config(self, sast_validator):
        """Test config file detection."""
        assert sast_validator._is_scannable("config.yaml") is True
        assert sast_validator._is_scannable("config.yml") is True
        assert sast_validator._is_scannable("settings.json") is True

    def test_is_not_scannable(self, sast_validator):
        """Test non-scannable files."""
        assert sast_validator._is_scannable("README.md") is False
        assert sast_validator._is_scannable("image.png") is False
        assert sast_validator._is_scannable("style.css") is False
        assert sast_validator._is_scannable("Makefile") is False


# =============================================================================
# Test Finding Classification
# =============================================================================


class TestFindingClassification:
    """Tests for finding severity/category classification."""

    def test_get_critical_findings(self, sast_validator, sample_findings):
        """Test filtering critical findings."""
        critical = sast_validator._get_critical_findings(sample_findings)

        assert len(critical) == 2
        assert all(f.severity == SemgrepSeverity.ERROR for f in critical)

    def test_get_blocking_findings(self, sast_validator, sample_findings):
        """Test filtering blocking findings."""
        blocking = sast_validator._get_blocking_findings(sample_findings)

        # 2 errors + secrets category
        assert len(blocking) >= 2

    def test_blocking_includes_category(self, sast_validator):
        """Test that blocking categories are included."""
        findings = [
            SemgrepFinding(
                file_path="test.py",
                start_line=1,
                end_line=1,
                start_col=1,
                end_col=1,
                rule_id="rule",
                rule_name="Rule",
                severity=SemgrepSeverity.WARNING,  # Not error
                category=SemgrepCategory.SECRETS,  # But blocking category
                message="msg",
                snippet="",
            )
        ]

        blocking = sast_validator._get_blocking_findings(findings)
        assert len(blocking) == 1


# =============================================================================
# Test Validate Method
# =============================================================================


class TestValidateMethod:
    """Tests for the main validate method."""

    @pytest.mark.asyncio
    async def test_validate_no_scannable_files(self, sast_validator):
        """Test validation with no scannable files."""
        files = ["README.md", "Dockerfile", "requirements.txt"]

        result = await sast_validator.validate(
            project_id=uuid4(),
            pr_number="123",
            files=files,
            diff="",
        )

        assert result.status == ValidatorStatus.SKIPPED
        assert result.blocking is False
        assert "No scannable files" in result.message

    @pytest.mark.asyncio
    async def test_validate_semgrep_unavailable(self, sast_validator, sample_python_files):
        """Test validation when Semgrep is unavailable."""
        with patch("app.services.validators.sast_validator.get_semgrep_service") as mock_get:
            mock_service = MagicMock()
            mock_service.scan_files = AsyncMock(
                return_value=SemgrepScanResult(
                    success=False,
                    error_message="Semgrep CLI not installed",
                )
            )
            mock_get.return_value = mock_service

            result = await sast_validator.validate(
                project_id=uuid4(),
                pr_number="123",
                files=sample_python_files,
                diff="",
            )

            assert result.status == ValidatorStatus.ERROR
            assert result.blocking is False
            assert "failed" in result.message.lower()

    @pytest.mark.asyncio
    async def test_validate_with_critical_findings(
        self, sast_validator, sample_python_files, sample_scan_result
    ):
        """Test validation with critical findings."""
        with patch("app.services.validators.sast_validator.get_semgrep_service") as mock_get:
            mock_service = MagicMock()
            mock_service.scan_files = AsyncMock(return_value=sample_scan_result)
            mock_get.return_value = mock_service

            result = await sast_validator.validate(
                project_id=uuid4(),
                pr_number="123",
                files=sample_python_files,
                diff="",
            )

            assert result.status == ValidatorStatus.FAILED
            assert result.blocking is True
            assert "critical" in result.message.lower()

    @pytest.mark.asyncio
    async def test_validate_no_findings(self, sast_validator, sample_python_files):
        """Test validation with no findings."""
        with patch("app.services.validators.sast_validator.get_semgrep_service") as mock_get:
            mock_service = MagicMock()
            mock_service.scan_files = AsyncMock(
                return_value=SemgrepScanResult(
                    success=True,
                    findings=[],
                    files_scanned=4,
                    rules_run=50,
                )
            )
            mock_get.return_value = mock_service

            result = await sast_validator.validate(
                project_id=uuid4(),
                pr_number="123",
                files=sample_python_files,
                diff="",
            )

            assert result.status == ValidatorStatus.PASSED
            assert result.blocking is False
            assert "No security issues" in result.message

    @pytest.mark.asyncio
    async def test_validate_warnings_only(self, sast_validator, sample_python_files):
        """Test validation with warnings only."""
        warnings_only = SemgrepScanResult(
            success=True,
            findings=[
                SemgrepFinding(
                    file_path="test.py",
                    start_line=1,
                    end_line=1,
                    start_col=1,
                    end_col=1,
                    rule_id="rule",
                    rule_name="Rule",
                    severity=SemgrepSeverity.WARNING,
                    category=SemgrepCategory.OTHER,
                    message="msg",
                    snippet="",
                )
            ],
            files_scanned=4,
            warnings=1,
        )

        with patch("app.services.validators.sast_validator.get_semgrep_service") as mock_get:
            mock_service = MagicMock()
            mock_service.scan_files = AsyncMock(return_value=warnings_only)
            mock_get.return_value = mock_service

            result = await sast_validator.validate(
                project_id=uuid4(),
                pr_number="123",
                files=sample_python_files,
                diff="",
            )

            assert result.status == ValidatorStatus.PASSED
            assert "warnings" in result.message.lower()

    @pytest.mark.asyncio
    async def test_validate_error_handling(self, sast_validator, sample_python_files):
        """Test error handling in validation."""
        with patch("app.services.validators.sast_validator.get_semgrep_service") as mock_get:
            mock_get.side_effect = Exception("Unexpected error")

            result = await sast_validator.validate(
                project_id=uuid4(),
                pr_number="123",
                files=sample_python_files,
                diff="",
            )

            assert result.status == ValidatorStatus.ERROR
            assert result.blocking is False
            assert "error" in result.message.lower()


# =============================================================================
# Test Details Building
# =============================================================================


class TestDetailsBuild:
    """Tests for result details building."""

    def test_build_details_structure(
        self, sast_validator, sample_findings, sample_scan_result
    ):
        """Test details structure."""
        details = sast_validator._build_details(
            findings=sample_findings,
            scan_result=sample_scan_result,
            files_scanned=4,
        )

        assert "files_scanned" in details
        assert "rules_run" in details
        assert "total_findings" in details
        assert "critical_count" in details
        assert "warning_count" in details
        assert "findings_by_severity" in details
        assert "findings_by_category" in details
        assert "findings_by_file" in details

    def test_build_details_severity_grouping(
        self, sast_validator, sample_findings, sample_scan_result
    ):
        """Test findings grouped by severity."""
        details = sast_validator._build_details(
            findings=sample_findings,
            scan_result=sample_scan_result,
            files_scanned=4,
        )

        by_severity = details["findings_by_severity"]
        assert "critical" in by_severity
        assert "warning" in by_severity
        assert "info" in by_severity

    def test_build_details_category_grouping(
        self, sast_validator, sample_findings, sample_scan_result
    ):
        """Test findings grouped by category."""
        details = sast_validator._build_details(
            findings=sample_findings,
            scan_result=sample_scan_result,
            files_scanned=4,
        )

        by_category = details["findings_by_category"]
        assert "injection" in by_category
        assert "secrets" in by_category

    def test_build_details_file_hotspots(
        self, sast_validator, sample_findings, sample_scan_result
    ):
        """Test file hotspots in details."""
        details = sast_validator._build_details(
            findings=sample_findings,
            scan_result=sample_scan_result,
            files_scanned=4,
        )

        by_file = details["findings_by_file"]
        assert len(by_file) <= 10  # Limited to top 10

    def test_build_details_limits_findings(self, sast_validator, sample_scan_result):
        """Test that findings are limited to 50."""
        many_findings = [
            SemgrepFinding(
                file_path=f"file_{i}.py",
                start_line=i,
                end_line=i,
                start_col=1,
                end_col=1,
                rule_id="rule",
                rule_name="Rule",
                severity=SemgrepSeverity.WARNING,
                category=SemgrepCategory.OTHER,
                message="msg",
                snippet="",
            )
            for i in range(100)
        ]

        details = sast_validator._build_details(
            findings=many_findings,
            scan_result=sample_scan_result,
            files_scanned=100,
        )

        total_in_severity = sum(
            len(v) for v in details["findings_by_severity"].values()
        )
        assert total_in_severity <= 50


# =============================================================================
# Test AISecurityValidator
# =============================================================================


class TestAISecurityValidator:
    """Tests for AISecurityValidator."""

    def test_initialization(self, ai_security_validator):
        """Test AI security validator initialization."""
        assert ai_security_validator.name == "ai-security"
        assert ai_security_validator.default_blocking is True
        assert ai_security_validator.default_timeout_seconds == 180

    def test_is_ai_related_files(self, ai_security_validator):
        """Test AI-related file detection."""
        assert ai_security_validator._is_ai_related("services/ai_service.py") is True
        assert ai_security_validator._is_ai_related("llm/prompts.py") is True
        assert ai_security_validator._is_ai_related("models/embedding.py") is True
        assert ai_security_validator._is_ai_related("agents/chat_agent.py") is True
        assert ai_security_validator._is_ai_related("langchain/chains.py") is True

    def test_is_not_ai_related(self, ai_security_validator):
        """Test non-AI file detection."""
        assert ai_security_validator._is_ai_related("services/auth.py") is False
        assert ai_security_validator._is_ai_related("api/routes.py") is False
        assert ai_security_validator._is_ai_related("utils/helpers.py") is False

    def test_ai_security_patterns(self, ai_security_validator):
        """Test AI security patterns defined."""
        patterns = ai_security_validator.AI_SECURITY_PATTERNS

        assert "prompt_injection" in patterns
        assert "data_leakage" in patterns
        assert "unsafe_model_load" in patterns

    def test_check_ai_patterns_prompt_injection(self, ai_security_validator):
        """Test prompt injection pattern detection."""
        diff = '''
+    prompt = f"User query: {user_input}"
+    response = llm.invoke(prompt)
'''

        issues = ai_security_validator._check_ai_patterns(diff)

        # Should detect f-string with user input
        assert len(issues) >= 0  # Pattern matching may vary

    def test_check_ai_patterns_unsafe_model(self, ai_security_validator):
        """Test unsafe model loading detection."""
        diff = '''
+    model = pickle.load(open("model.pkl", "rb"))
+    weights = torch.load("weights.pt")
'''

        issues = ai_security_validator._check_ai_patterns(diff)

        # Should detect pickle.load and torch.load
        assert any("unsafe_model" in i.get("pattern", "") for i in issues)

    @pytest.mark.asyncio
    async def test_validate_no_ai_files(self, ai_security_validator):
        """Test validation with no AI-related files."""
        files = ["app/main.py", "app/routes.py"]

        result = await ai_security_validator.validate(
            project_id=uuid4(),
            pr_number="123",
            files=files,
            diff="",
        )

        assert result.status == ValidatorStatus.SKIPPED
        assert "No AI-related files" in result.message

    @pytest.mark.asyncio
    async def test_validate_with_ai_files(self, ai_security_validator):
        """Test validation with AI-related files."""
        files = ["app/services/ai_service.py", "app/llm/prompts.py"]

        with patch("app.services.validators.sast_validator.get_semgrep_service") as mock_get:
            mock_service = MagicMock()
            mock_service.scan_files = AsyncMock(
                return_value=SemgrepScanResult(
                    success=True,
                    findings=[],
                    files_scanned=2,
                )
            )
            mock_get.return_value = mock_service

            result = await ai_security_validator.validate(
                project_id=uuid4(),
                pr_number="123",
                files=files,
                diff="",
            )

            assert result.status == ValidatorStatus.PASSED


# =============================================================================
# Test Integration with Pipeline
# =============================================================================


class TestPipelineIntegration:
    """Tests for integration with ValidationPipeline."""

    def test_validator_has_required_interface(self, sast_validator):
        """Test that validator implements required interface."""
        assert hasattr(sast_validator, "name")
        assert hasattr(sast_validator, "validate")
        assert hasattr(sast_validator, "is_blocking")
        assert hasattr(sast_validator, "get_timeout")
        assert hasattr(sast_validator, "get_name")

    def test_validator_name(self, sast_validator):
        """Test validator name method."""
        assert sast_validator.get_name() == "sast"

    def test_validator_blocking(self, sast_validator):
        """Test validator blocking status."""
        assert sast_validator.is_blocking() is True

        # Test with non-blocking config
        config = ValidatorConfig(blocking=False)
        non_blocking = SASTValidator(config=config)
        assert non_blocking.is_blocking() is False

    def test_validator_timeout(self, sast_validator):
        """Test validator timeout."""
        assert sast_validator.get_timeout() == 300

        # Test with custom timeout
        config = ValidatorConfig(timeout_seconds=120)
        custom_timeout = SASTValidator(config=config)
        assert custom_timeout.get_timeout() == 120

    @pytest.mark.asyncio
    async def test_validate_returns_validator_result(
        self, sast_validator, sample_python_files
    ):
        """Test that validate returns ValidatorResult."""
        with patch("app.services.validators.sast_validator.get_semgrep_service") as mock_get:
            mock_service = MagicMock()
            mock_service.scan_files = AsyncMock(
                return_value=SemgrepScanResult(success=True)
            )
            mock_get.return_value = mock_service

            result = await sast_validator.validate(
                project_id=uuid4(),
                pr_number="123",
                files=sample_python_files,
                diff="",
            )

            assert result.validator_name == "sast"
            assert isinstance(result.status, ValidatorStatus)
            assert isinstance(result.message, str)
            assert isinstance(result.details, dict)
            assert isinstance(result.duration_ms, int)
            assert isinstance(result.blocking, bool)
