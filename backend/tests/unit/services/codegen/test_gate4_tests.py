"""
Tests for Gate 4: Test Execution (quality_pipeline._run_gate4_tests)

Sprint 196 — Track A-02
Validates:
- Pytest execution in temp sandbox
- Output parsing (PASSED / FAILED / ERROR counts)
- Timeout handling (60s)
- Graceful skip when pytest unavailable
- No-test-files scenario → PASSED
- Non-Python language → SKIPPED
"""

import subprocess
from unittest.mock import patch, MagicMock

import pytest

from app.services.codegen.quality_pipeline import (
    QualityPipeline,
    GateStatus,
)


@pytest.fixture
def pipeline() -> QualityPipeline:
    """Pipeline with tests enabled."""
    return QualityPipeline(skip_tests=False)


# ---------------------------------------------------------------------------
# G4-01: No test files → PASSED (nothing to validate)
# ---------------------------------------------------------------------------
class TestGate4NoTestFiles:
    def test_no_test_files_returns_passed(self, pipeline: QualityPipeline):
        """If generated code has no test files, Gate 4 returns PASSED."""
        files = {
            "main.py": "print('hello')\n",
            "utils.py": "def add(a, b): return a + b\n",
        }
        result = pipeline._run_gate4_tests(files, "python")

        assert result.status == GateStatus.PASSED
        assert result.gate_number == 4
        assert result.details["test_files"] == 0
        assert "no test files" in result.summary.lower()


# ---------------------------------------------------------------------------
# G4-02: Passing tests → PASSED
# ---------------------------------------------------------------------------
class TestGate4PassingTests:
    def test_all_tests_pass(self, pipeline: QualityPipeline):
        """Gate 4 returns PASSED when all pytest tests pass."""
        files = {
            "calculator.py": "def add(a, b): return a + b\n",
            "test_calculator.py": (
                "from calculator import add\n"
                "\n"
                "def test_add():\n"
                "    assert add(1, 2) == 3\n"
                "\n"
                "def test_add_negative():\n"
                "    assert add(-1, 1) == 0\n"
            ),
        }
        result = pipeline._run_gate4_tests(files, "python")

        assert result.status == GateStatus.PASSED
        assert result.gate_number == 4
        assert result.details["tests_passed"] >= 2
        assert result.details["tests_failed"] == 0
        assert result.details["test_files"] == 1


# ---------------------------------------------------------------------------
# G4-03: Failing tests → FAILED with issues
# ---------------------------------------------------------------------------
class TestGate4FailingTests:
    def test_failing_test_returns_failed(self, pipeline: QualityPipeline):
        """Gate 4 returns FAILED when any test fails."""
        files = {
            "calculator.py": "def add(a, b): return a + b\n",
            "test_calculator.py": (
                "from calculator import add\n"
                "\n"
                "def test_add_correct():\n"
                "    assert add(1, 2) == 3\n"
                "\n"
                "def test_add_wrong():\n"
                "    assert add(1, 2) == 999  # deliberately wrong\n"
            ),
        }
        result = pipeline._run_gate4_tests(files, "python")

        assert result.status == GateStatus.FAILED
        assert result.gate_number == 4
        assert result.details["tests_failed"] >= 1
        assert len(result.issues) >= 1
        assert result.issues[0].severity == "error"
        assert result.issues[0].code == "gate4/test_failed"


# ---------------------------------------------------------------------------
# G4-04: Non-Python language → SKIPPED
# ---------------------------------------------------------------------------
class TestGate4NonPython:
    def test_typescript_skipped(self, pipeline: QualityPipeline):
        """Gate 4 skips non-Python languages."""
        files = {"index.ts": "console.log('hi');\n"}
        result = pipeline._run_gate4_tests(files, "typescript")

        assert result.status == GateStatus.SKIPPED
        assert "typescript" in result.summary.lower()

    def test_javascript_skipped(self, pipeline: QualityPipeline):
        files = {"index.js": "console.log('hi');\n"}
        result = pipeline._run_gate4_tests(files, "javascript")

        assert result.status == GateStatus.SKIPPED


# ---------------------------------------------------------------------------
# G4-05: Timeout handling
# ---------------------------------------------------------------------------
class TestGate4Timeout:
    @patch("app.services.codegen.quality_pipeline.subprocess.run")
    def test_timeout_returns_failed(self, mock_run, pipeline: QualityPipeline):
        """Gate 4 returns FAILED (not SKIPPED) on timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired(
            cmd=["python", "-m", "pytest"], timeout=60
        )
        files = {
            "test_slow.py": "def test_slow():\n    import time; time.sleep(999)\n",
        }
        result = pipeline._run_gate4_tests(files, "python")

        assert result.status == GateStatus.FAILED
        assert "timeout" in result.summary.lower()
        assert result.issues[0].code == "gate4/timeout"


# ---------------------------------------------------------------------------
# G4-06: pytest binary not found → SKIPPED
# ---------------------------------------------------------------------------
class TestGate4NoPytest:
    @patch("app.services.codegen.quality_pipeline.subprocess.run")
    def test_no_pytest_returns_skipped(self, mock_run, pipeline: QualityPipeline):
        """Gate 4 returns SKIPPED if pytest binary is not available."""
        mock_run.side_effect = FileNotFoundError("pytest not found")
        files = {
            "test_basic.py": "def test_true():\n    assert True\n",
        }
        result = pipeline._run_gate4_tests(files, "python")

        assert result.status == GateStatus.SKIPPED
        assert "not available" in result.summary.lower()


# ---------------------------------------------------------------------------
# G4-07: Output parser — verbose mode
# ---------------------------------------------------------------------------
class TestGate4OutputParser:
    def test_parse_passed_lines(self):
        stdout = (
            "test_foo.py::test_bar PASSED\n"
            "test_foo.py::test_baz PASSED\n"
            "2 passed in 0.01s\n"
        )
        issues, passed, failed = QualityPipeline._parse_pytest_output(stdout, "")
        assert passed == 2
        assert failed == 0
        assert issues == []

    def test_parse_failed_lines(self):
        stdout = (
            "test_foo.py::test_ok PASSED\n"
            "test_foo.py::test_bad FAILED\n"
            "1 passed, 1 failed in 0.02s\n"
        )
        issues, passed, failed = QualityPipeline._parse_pytest_output(stdout, "")
        assert passed == 1
        assert failed == 1
        assert len(issues) == 1
        assert issues[0].code == "gate4/test_failed"

    def test_parse_summary_only_fallback(self):
        """If no :: lines, parse from summary."""
        stdout = "===== 5 passed, 2 failed in 0.5s =====\n"
        issues, passed, failed = QualityPipeline._parse_pytest_output(stdout, "")
        assert passed == 5
        assert failed == 2
        assert len(issues) == 1  # one aggregated issue

    def test_parse_error_lines(self):
        stdout = "test_bad.py::test_import ERROR\n"
        issues, passed, failed = QualityPipeline._parse_pytest_output(stdout, "")
        assert failed == 1
        assert issues[0].code == "gate4/test_error"


# ---------------------------------------------------------------------------
# G4-08: Sandbox cleanup (temp dir removed after run)
# ---------------------------------------------------------------------------
class TestGate4Cleanup:
    @patch("app.services.codegen.quality_pipeline.shutil.rmtree")
    def test_temp_dir_cleaned_up_on_success(self, mock_rmtree, pipeline: QualityPipeline):
        """Temp directory is always cleaned up, even on success."""
        files = {"main.py": "print(1)\n"}  # no test files → quick PASSED
        pipeline._run_gate4_tests(files, "python")
        mock_rmtree.assert_called_once()

    @patch("app.services.codegen.quality_pipeline.subprocess.run")
    @patch("app.services.codegen.quality_pipeline.shutil.rmtree")
    def test_temp_dir_cleaned_up_on_timeout(self, mock_rmtree, mock_run, pipeline: QualityPipeline):
        """Temp directory is cleaned up even on timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired(cmd=[], timeout=60)
        files = {"test_x.py": "def test_a(): pass\n"}
        pipeline._run_gate4_tests(files, "python")
        mock_rmtree.assert_called_once()


# ---------------------------------------------------------------------------
# G4-09: Tests in subdirectory
# ---------------------------------------------------------------------------
class TestGate4SubdirTests:
    def test_tests_in_tests_subdir(self, pipeline: QualityPipeline):
        """Gate 4 discovers tests in tests/ subdirectory."""
        files = {
            "app.py": "def greet(name): return f'Hello {name}'\n",
            "tests/test_app.py": (
                "import sys, os\n"
                "sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))\n"
                "from app import greet\n"
                "\n"
                "def test_greet():\n"
                "    assert greet('World') == 'Hello World'\n"
            ),
        }
        result = pipeline._run_gate4_tests(files, "python")

        assert result.status == GateStatus.PASSED
        assert result.details["test_files"] == 1
        assert result.details["tests_passed"] >= 1
