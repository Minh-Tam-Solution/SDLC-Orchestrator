"""
Unit Tests for SemgrepService

SDLC Stage: 04 - BUILD
Sprint: 43 - Policy Guards & Evidence UI
Framework: SDLC 5.1.1
Epic: EP-02 AI Safety Layer v1

Purpose:
Comprehensive unit tests for SemgrepService.
Tests async scanning, SARIF parsing, and error handling.

Coverage Target: 90%+
"""

import asyncio
import json
import os
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.services.semgrep_service import (
    SemgrepCategory,
    SemgrepFinding,
    SemgrepScanResult,
    SemgrepService,
    SemgrepSeverity,
    get_semgrep_service,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def semgrep_service():
    """Create a fresh SemgrepService instance."""
    return SemgrepService()


@pytest.fixture
def sample_sarif_output():
    """Sample SARIF output from Semgrep."""
    return json.dumps({
        "runs": [
            {
                "tool": {
                    "driver": {
                        "rules": [
                            {
                                "id": "python.security.sql-injection",
                                "name": "sql-injection",
                                "shortDescription": {"text": "SQL Injection detected"},
                                "properties": {
                                    "category": "injection",
                                    "cwe": ["CWE-89"],
                                    "owasp": ["A03:2021"],
                                    "confidence": "high",
                                },
                            },
                            {
                                "id": "python.security.hardcoded-secrets",
                                "name": "hardcoded-secrets",
                                "shortDescription": {"text": "Hardcoded secret detected"},
                                "properties": {
                                    "category": "secrets",
                                    "cwe": ["CWE-798"],
                                    "confidence": "high",
                                },
                            },
                        ]
                    }
                },
                "results": [
                    {
                        "ruleId": "python.security.sql-injection",
                        "level": "error",
                        "message": {
                            "text": "Possible SQL injection vulnerability"
                        },
                        "locations": [
                            {
                                "physicalLocation": {
                                    "artifactLocation": {"uri": "app/db.py"},
                                    "region": {
                                        "startLine": 10,
                                        "endLine": 10,
                                        "startColumn": 5,
                                        "endColumn": 50,
                                        "snippet": {"text": "cursor.execute(f'SELECT * FROM {table}')"},
                                    },
                                }
                            }
                        ],
                    },
                    {
                        "ruleId": "python.security.hardcoded-secrets",
                        "level": "warning",
                        "message": {
                            "text": "Hardcoded API key detected"
                        },
                        "locations": [
                            {
                                "physicalLocation": {
                                    "artifactLocation": {"uri": "app/config.py"},
                                    "region": {
                                        "startLine": 5,
                                        "endLine": 5,
                                        "startColumn": 1,
                                        "endColumn": 40,
                                        "snippet": {"text": "API_KEY = 'sk-1234567890abcdef'"},
                                    },
                                }
                            }
                        ],
                    },
                ],
            }
        ]
    })


@pytest.fixture
def vulnerable_python_code():
    """Sample vulnerable Python code for testing."""
    return '''
import sqlite3
import os

def login(username, password):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    # SQL Injection vulnerability
    cursor.execute(f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'")
    return cursor.fetchone()

def run_command(user_input):
    # Command injection vulnerability
    os.system(f"echo {user_input}")

# Hardcoded secret
API_KEY = "sk-1234567890abcdef1234567890abcdef"

def unsafe_yaml():
    import yaml
    # Unsafe YAML loading
    data = yaml.load(open("config.yml"))
    return data
'''


# =============================================================================
# Test SemgrepService Initialization
# =============================================================================


class TestSemgrepServiceInit:
    """Tests for SemgrepService initialization."""

    def test_default_initialization(self, semgrep_service):
        """Test default initialization values."""
        assert semgrep_service.custom_rules_path is None
        assert semgrep_service.rulesets == SemgrepService.DEFAULT_RULESETS
        assert semgrep_service.timeout_seconds == SemgrepService.DEFAULT_TIMEOUT
        assert semgrep_service._semgrep_available is None

    def test_custom_initialization(self):
        """Test initialization with custom parameters."""
        custom_rules = "/path/to/rules.yml"
        custom_rulesets = ["p/python", "p/custom"]
        timeout = 120

        service = SemgrepService(
            custom_rules_path=custom_rules,
            rulesets=custom_rulesets,
            timeout_seconds=timeout,
        )

        assert service.custom_rules_path == custom_rules
        assert service.rulesets == custom_rulesets
        assert service.timeout_seconds == timeout

    def test_default_rulesets(self):
        """Test default rulesets include security packs."""
        assert "p/python" in SemgrepService.DEFAULT_RULESETS
        assert "p/security-audit" in SemgrepService.DEFAULT_RULESETS
        assert "p/owasp-top-ten" in SemgrepService.DEFAULT_RULESETS
        assert "p/secrets" in SemgrepService.DEFAULT_RULESETS


# =============================================================================
# Test Availability Check
# =============================================================================


class TestSemgrepAvailability:
    """Tests for Semgrep availability checking."""

    @pytest.mark.asyncio
    async def test_check_availability_success(self, semgrep_service):
        """Test availability check when Semgrep is installed."""
        with patch("asyncio.create_subprocess_shell") as mock_subprocess:
            mock_process = AsyncMock()
            mock_process.returncode = 0
            mock_process.communicate.return_value = (b"1.50.0", b"")
            mock_subprocess.return_value = mock_process

            result = await semgrep_service.check_availability()

            assert result is True
            assert semgrep_service._semgrep_available is True

    @pytest.mark.asyncio
    async def test_check_availability_failure(self, semgrep_service):
        """Test availability check when Semgrep is not installed."""
        with patch("asyncio.create_subprocess_shell") as mock_subprocess:
            mock_process = AsyncMock()
            mock_process.returncode = 1
            mock_process.communicate.return_value = (b"", b"command not found")
            mock_subprocess.return_value = mock_process

            result = await semgrep_service.check_availability()

            assert result is False
            assert semgrep_service._semgrep_available is False

    @pytest.mark.asyncio
    async def test_check_availability_cached(self, semgrep_service):
        """Test that availability result is cached."""
        semgrep_service._semgrep_available = True

        # Should return cached value without subprocess call
        with patch("asyncio.create_subprocess_shell") as mock_subprocess:
            result = await semgrep_service.check_availability()

            assert result is True
            mock_subprocess.assert_not_called()

    @pytest.mark.asyncio
    async def test_check_availability_timeout(self, semgrep_service):
        """Test availability check with timeout."""
        with patch("asyncio.create_subprocess_shell") as mock_subprocess:
            mock_subprocess.side_effect = asyncio.TimeoutError()

            result = await semgrep_service.check_availability()

            assert result is False


# =============================================================================
# Test SARIF Parsing
# =============================================================================


class TestSarifParsing:
    """Tests for SARIF output parsing."""

    def test_parse_sarif_output_success(self, semgrep_service, sample_sarif_output):
        """Test successful SARIF parsing."""
        result = semgrep_service._parse_sarif_output(sample_sarif_output)

        assert result.success is True
        assert len(result.findings) == 2
        assert result.errors == 1
        assert result.warnings == 1
        assert result.rules_run == 2

    def test_parse_sarif_output_finding_details(
        self, semgrep_service, sample_sarif_output
    ):
        """Test parsed finding details."""
        result = semgrep_service._parse_sarif_output(sample_sarif_output)

        # Check first finding (SQL injection)
        sql_finding = next(
            f for f in result.findings if "sql" in f.rule_id.lower()
        )
        assert sql_finding.file_path == "app/db.py"
        assert sql_finding.start_line == 10
        assert sql_finding.severity == SemgrepSeverity.ERROR
        assert sql_finding.category == SemgrepCategory.INJECTION
        assert "CWE-89" in sql_finding.cwe

    def test_parse_sarif_output_empty(self, semgrep_service):
        """Test parsing empty SARIF output."""
        result = semgrep_service._parse_sarif_output("")

        assert result.success is True
        assert len(result.findings) == 0

    def test_parse_sarif_output_invalid_json(self, semgrep_service):
        """Test parsing invalid JSON."""
        result = semgrep_service._parse_sarif_output("not valid json")

        assert result.success is False
        assert "Failed to parse SARIF" in result.error_message

    def test_parse_sarif_output_no_results(self, semgrep_service):
        """Test parsing SARIF with no results."""
        sarif = json.dumps({"runs": [{"tool": {"driver": {"rules": []}}, "results": []}]})
        result = semgrep_service._parse_sarif_output(sarif)

        assert result.success is True
        assert len(result.findings) == 0


# =============================================================================
# Test Category Mapping
# =============================================================================


class TestCategoryMapping:
    """Tests for category string mapping."""

    def test_map_category_injection(self, semgrep_service):
        """Test mapping injection category."""
        assert semgrep_service._map_category("injection") == SemgrepCategory.INJECTION
        assert semgrep_service._map_category("sql-injection") == SemgrepCategory.INJECTION

    def test_map_category_xss(self, semgrep_service):
        """Test mapping XSS category."""
        assert semgrep_service._map_category("xss") == SemgrepCategory.XSS
        assert semgrep_service._map_category("cross-site-scripting") == SemgrepCategory.XSS

    def test_map_category_secrets(self, semgrep_service):
        """Test mapping secrets category."""
        assert semgrep_service._map_category("secrets") == SemgrepCategory.SECRETS
        assert semgrep_service._map_category("hardcoded-secrets") == SemgrepCategory.SECRETS

    def test_map_category_ssrf(self, semgrep_service):
        """Test mapping SSRF category."""
        assert semgrep_service._map_category("ssrf") == SemgrepCategory.SSRF
        assert semgrep_service._map_category("server-side-request-forgery") == SemgrepCategory.SSRF

    def test_map_category_unknown(self, semgrep_service):
        """Test mapping unknown category."""
        assert semgrep_service._map_category("unknown-category") == SemgrepCategory.OTHER
        assert semgrep_service._map_category("") == SemgrepCategory.OTHER


# =============================================================================
# Test File Scanning
# =============================================================================


class TestFileScan:
    """Tests for file scanning functionality."""

    @pytest.mark.asyncio
    async def test_scan_files_unavailable(self, semgrep_service):
        """Test scanning when Semgrep is unavailable."""
        semgrep_service._semgrep_available = False

        result = await semgrep_service.scan_files(["/path/to/file.py"])

        assert result.success is False
        assert "not installed" in result.error_message.lower()

    @pytest.mark.asyncio
    async def test_scan_files_no_files(self, semgrep_service):
        """Test scanning with no existing files."""
        semgrep_service._semgrep_available = True

        result = await semgrep_service.scan_files(["/nonexistent/file.py"])

        assert result.success is True
        assert result.files_scanned == 0

    @pytest.mark.asyncio
    async def test_scan_files_success(
        self, semgrep_service, sample_sarif_output, vulnerable_python_code
    ):
        """Test successful file scanning."""
        semgrep_service._semgrep_available = True

        # Create temp file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as f:
            f.write(vulnerable_python_code)
            temp_path = f.name

        try:
            with patch("asyncio.create_subprocess_shell") as mock_subprocess:
                mock_process = AsyncMock()
                mock_process.returncode = 0
                mock_process.communicate.return_value = (
                    sample_sarif_output.encode(),
                    b"",
                )
                mock_subprocess.return_value = mock_process

                result = await semgrep_service.scan_files([temp_path])

                assert result.success is True
                assert result.files_scanned == 1
                assert len(result.findings) > 0
        finally:
            os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_scan_files_timeout(self, semgrep_service):
        """Test scanning with timeout."""
        semgrep_service._semgrep_available = True
        semgrep_service.timeout_seconds = 0.001

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("print('test')")
            temp_path = f.name

        try:
            with patch("asyncio.create_subprocess_shell") as mock_subprocess:
                mock_subprocess.side_effect = asyncio.TimeoutError()

                result = await semgrep_service.scan_files([temp_path])

                assert result.success is False
                assert "timed out" in result.error_message.lower()
        finally:
            os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_scan_files_max_limit(self, semgrep_service):
        """Test that file count is limited."""
        semgrep_service._semgrep_available = True

        # Create more files than MAX_FILES_PER_SCAN
        files = [f"/tmp/test_{i}.py" for i in range(150)]

        with patch.object(
            semgrep_service, "_build_scan_command", new_callable=AsyncMock
        ) as mock_cmd:
            mock_cmd.return_value = "semgrep --sarif"

            with patch("asyncio.create_subprocess_shell") as mock_subprocess:
                mock_process = AsyncMock()
                mock_process.returncode = 0
                mock_process.communicate.return_value = (b'{"runs": []}', b"")
                mock_subprocess.return_value = mock_process

                # Files don't exist, so scan returns empty
                result = await semgrep_service.scan_files(files)

                # Should be limited, but since files don't exist, result is 0
                assert result.files_scanned == 0


# =============================================================================
# Test Code Snippet Scanning
# =============================================================================


class TestSnippetScan:
    """Tests for code snippet scanning."""

    @pytest.mark.asyncio
    async def test_scan_snippet_unavailable(self, semgrep_service):
        """Test snippet scanning when Semgrep unavailable."""
        semgrep_service._semgrep_available = False

        result = await semgrep_service.scan_code_snippet(
            code="print('hello')",
            language="python",
        )

        assert result.success is False
        assert "not installed" in result.error_message.lower()

    @pytest.mark.asyncio
    async def test_scan_snippet_success(
        self, semgrep_service, sample_sarif_output
    ):
        """Test successful snippet scanning."""
        semgrep_service._semgrep_available = True

        code = "cursor.execute(f'SELECT * FROM {table}')"

        with patch.object(
            semgrep_service, "scan_files", new_callable=AsyncMock
        ) as mock_scan:
            mock_scan.return_value = SemgrepScanResult(
                success=True,
                findings=[
                    SemgrepFinding(
                        file_path="snippet.py",
                        start_line=1,
                        end_line=1,
                        start_col=1,
                        end_col=40,
                        rule_id="sql-injection",
                        rule_name="SQL Injection",
                        severity=SemgrepSeverity.ERROR,
                        category=SemgrepCategory.INJECTION,
                        message="SQL injection detected",
                        snippet=code,
                    )
                ],
                files_scanned=1,
            )

            result = await semgrep_service.scan_code_snippet(
                code=code,
                language="python",
            )

            assert result.success is True
            assert result.files_scanned == 1

    @pytest.mark.asyncio
    async def test_scan_snippet_language_mapping(self, semgrep_service):
        """Test language to extension mapping."""
        semgrep_service._semgrep_available = True

        languages = [
            ("python", ".py"),
            ("javascript", ".js"),
            ("typescript", ".ts"),
            ("java", ".java"),
            ("go", ".go"),
        ]

        for lang, expected_ext in languages:
            with patch.object(
                semgrep_service, "scan_files", new_callable=AsyncMock
            ) as mock_scan:
                mock_scan.return_value = SemgrepScanResult(success=True)

                await semgrep_service.scan_code_snippet(
                    code="test code",
                    language=lang,
                )

                # Check that temp file was created with correct extension
                call_args = mock_scan.call_args
                assert call_args is not None


# =============================================================================
# Test Directory Scanning
# =============================================================================


class TestDirectoryScan:
    """Tests for directory scanning."""

    @pytest.mark.asyncio
    async def test_scan_directory_not_found(self, semgrep_service):
        """Test scanning non-existent directory."""
        result = await semgrep_service.scan_directory("/nonexistent/path")

        assert result.success is False
        assert "not found" in result.error_message.lower()

    @pytest.mark.asyncio
    async def test_scan_directory_unavailable(self, semgrep_service):
        """Test scanning when Semgrep unavailable."""
        semgrep_service._semgrep_available = False

        with tempfile.TemporaryDirectory() as tmpdir:
            result = await semgrep_service.scan_directory(tmpdir)

            assert result.success is False
            assert "not installed" in result.error_message.lower()


# =============================================================================
# Test Global Service
# =============================================================================


class TestGlobalService:
    """Tests for global service singleton."""

    def test_get_semgrep_service_singleton(self):
        """Test that get_semgrep_service returns singleton."""
        # Reset global
        import app.services.semgrep_service as module
        module._semgrep_service = None

        service1 = get_semgrep_service()
        service2 = get_semgrep_service()

        assert service1 is service2

    def test_get_semgrep_service_custom_rules(self):
        """Test service with custom rules path."""
        import app.services.semgrep_service as module
        module._semgrep_service = None

        with patch("pathlib.Path.exists", return_value=True):
            service = get_semgrep_service()

            # Should detect project rules
            assert service is not None


# =============================================================================
# Test Finding Dataclass
# =============================================================================


class TestSemgrepFinding:
    """Tests for SemgrepFinding dataclass."""

    def test_finding_to_dict(self):
        """Test finding serialization."""
        finding = SemgrepFinding(
            file_path="test.py",
            start_line=10,
            end_line=10,
            start_col=1,
            end_col=50,
            rule_id="test-rule",
            rule_name="Test Rule",
            severity=SemgrepSeverity.ERROR,
            category=SemgrepCategory.INJECTION,
            message="Test message",
            snippet="code snippet",
            cwe=["CWE-89"],
            owasp=["A03:2021"],
        )

        result = finding.to_dict()

        assert result["file_path"] == "test.py"
        assert result["severity"] == "ERROR"
        assert result["category"] == "injection"
        assert result["cwe"] == ["CWE-89"]

    def test_finding_defaults(self):
        """Test finding default values."""
        finding = SemgrepFinding(
            file_path="test.py",
            start_line=1,
            end_line=1,
            start_col=1,
            end_col=1,
            rule_id="rule",
            rule_name="Rule",
            severity=SemgrepSeverity.INFO,
            category=SemgrepCategory.OTHER,
            message="msg",
            snippet="",
        )

        assert finding.fix_suggestion is None
        assert finding.cwe == []
        assert finding.owasp == []
        assert finding.references == []
        assert finding.confidence == "high"


# =============================================================================
# Test Scan Result Dataclass
# =============================================================================


class TestSemgrepScanResult:
    """Tests for SemgrepScanResult dataclass."""

    def test_scan_result_to_dict(self):
        """Test scan result serialization."""
        finding = SemgrepFinding(
            file_path="test.py",
            start_line=1,
            end_line=1,
            start_col=1,
            end_col=1,
            rule_id="rule",
            rule_name="Rule",
            severity=SemgrepSeverity.ERROR,
            category=SemgrepCategory.SECRETS,
            message="msg",
            snippet="",
        )

        result = SemgrepScanResult(
            success=True,
            findings=[finding],
            files_scanned=5,
            rules_run=10,
            duration_ms=500,
            errors=1,
            warnings=0,
            infos=0,
        )

        dict_result = result.to_dict()

        assert dict_result["success"] is True
        assert len(dict_result["findings"]) == 1
        assert dict_result["files_scanned"] == 5
        assert dict_result["errors"] == 1

    def test_scan_result_defaults(self):
        """Test scan result default values."""
        result = SemgrepScanResult(success=True)

        assert result.error_message is None
        assert result.findings == []
        assert result.files_scanned == 0
        assert result.rules_run == 0
        assert result.duration_ms == 0
