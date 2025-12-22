"""
Unit tests for ViolationReport and ScanResult.

Part of Sprint 44 - SDLC Structure Scanner Engine.
"""

import json
from pathlib import Path

import pytest

from sdlcctl.validation import ViolationReport, Severity, ScanResult


class TestViolationReport:
    """Test ViolationReport dataclass."""

    def test_create_violation_report(self):
        """Test creating a basic violation report."""
        violation = ViolationReport(
            rule_id="STAGE-001",
            severity=Severity.ERROR,
            file_path=Path("/docs/1-planning"),
            message="Invalid stage folder naming",
        )

        assert violation.rule_id == "STAGE-001"
        assert violation.severity == Severity.ERROR
        assert violation.file_path == Path("/docs/1-planning")
        assert violation.message == "Invalid stage folder naming"
        assert violation.fix_suggestion is None
        assert violation.auto_fixable is False
        assert violation.context == {}

    def test_violation_with_fix_suggestion(self):
        """Test violation with fix suggestion."""
        violation = ViolationReport(
            rule_id="STAGE-001",
            severity=Severity.ERROR,
            file_path=Path("/docs/1-planning"),
            message="Invalid stage folder naming",
            fix_suggestion="Rename to '01-planning'",
            auto_fixable=True,
        )

        assert violation.fix_suggestion == "Rename to '01-planning'"
        assert violation.auto_fixable is True

    def test_violation_with_context(self):
        """Test violation with additional context."""
        violation = ViolationReport(
            rule_id="NUM-001",
            severity=Severity.WARNING,
            file_path=Path("/docs/01-planning"),
            message="Duplicate numbering detected",
            context={
                "duplicates": ["01-doc1.md", "01-doc2.md"],
                "suggested_next": "02",
            },
        )

        assert violation.context["duplicates"] == ["01-doc1.md", "01-doc2.md"]
        assert violation.context["suggested_next"] == "02"

    def test_violation_str_representation(self):
        """Test string representation of violation."""
        violation = ViolationReport(
            rule_id="STAGE-001",
            severity=Severity.ERROR,
            file_path=Path("/docs/1-planning"),
            message="Invalid stage folder naming",
        )

        str_repr = str(violation)
        assert "❌" in str_repr
        assert "ERROR" in str_repr
        assert "[STAGE-001]" in str_repr
        assert "Invalid stage folder naming" in str_repr

    def test_violation_str_with_suggestion(self):
        """Test string representation with fix suggestion."""
        violation = ViolationReport(
            rule_id="STAGE-001",
            severity=Severity.ERROR,
            file_path=Path("/docs/1-planning"),
            message="Invalid stage folder naming",
            fix_suggestion="Rename to '01-planning'",
            auto_fixable=True,
        )

        str_repr = str(violation)
        assert "💡 Suggestion: Rename to '01-planning'" in str_repr
        assert "🔧 Auto-fixable with --fix" in str_repr

    def test_violation_to_dict(self):
        """Test converting violation to dictionary."""
        violation = ViolationReport(
            rule_id="STAGE-001",
            severity=Severity.ERROR,
            file_path=Path("/docs/1-planning"),
            message="Invalid stage folder naming",
            fix_suggestion="Rename to '01-planning'",
            auto_fixable=True,
            context={"expected": "01-planning"},
        )

        data = violation.to_dict()

        assert data["rule_id"] == "STAGE-001"
        assert data["severity"] == "ERROR"
        assert data["file_path"] == "/docs/1-planning"
        assert data["message"] == "Invalid stage folder naming"
        assert data["fix_suggestion"] == "Rename to '01-planning'"
        assert data["auto_fixable"] is True
        assert data["context"] == {"expected": "01-planning"}

    def test_violation_from_dict(self):
        """Test creating violation from dictionary."""
        data = {
            "rule_id": "STAGE-001",
            "severity": "ERROR",
            "file_path": "/docs/1-planning",
            "message": "Invalid stage folder naming",
            "fix_suggestion": "Rename to '01-planning'",
            "auto_fixable": True,
            "context": {"expected": "01-planning"},
        }

        violation = ViolationReport.from_dict(data)

        assert violation.rule_id == "STAGE-001"
        assert violation.severity == Severity.ERROR
        assert violation.file_path == Path("/docs/1-planning")
        assert violation.fix_suggestion == "Rename to '01-planning'"
        assert violation.auto_fixable is True

    def test_severity_levels(self):
        """Test all severity levels."""
        error = ViolationReport(
            rule_id="TEST-001",
            severity=Severity.ERROR,
            file_path=Path("/test"),
            message="Test error",
        )
        assert error.severity == Severity.ERROR

        warning = ViolationReport(
            rule_id="TEST-002",
            severity=Severity.WARNING,
            file_path=Path("/test"),
            message="Test warning",
        )
        assert warning.severity == Severity.WARNING

        info = ViolationReport(
            rule_id="TEST-003",
            severity=Severity.INFO,
            file_path=Path("/test"),
            message="Test info",
        )
        assert info.severity == Severity.INFO


class TestScanResult:
    """Test ScanResult dataclass."""

    def test_create_empty_scan_result(self):
        """Test creating an empty scan result."""
        result = ScanResult(
            scan_path=Path("/docs"),
            violations=[],
            files_scanned=100,
            scan_time_ms=250.5,
        )

        assert result.scan_path == Path("/docs")
        assert result.violations == []
        assert result.files_scanned == 100
        assert result.scan_time_ms == 250.5
        assert result.scanner_version == "1.0.0"

    def test_scan_result_with_violations(self):
        """Test scan result with violations."""
        violations = [
            ViolationReport(
                rule_id="STAGE-001",
                severity=Severity.ERROR,
                file_path=Path("/docs/1-planning"),
                message="Invalid naming",
            ),
            ViolationReport(
                rule_id="NUM-001",
                severity=Severity.WARNING,
                file_path=Path("/docs/01-planning"),
                message="Duplicate numbering",
            ),
            ViolationReport(
                rule_id="NAME-001",
                severity=Severity.INFO,
                file_path=Path("/docs/README.md"),
                message="Consider kebab-case",
                auto_fixable=True,
            ),
        ]

        result = ScanResult(
            scan_path=Path("/docs"),
            violations=violations,
            files_scanned=100,
        )

        assert len(result.violations) == 3

    def test_error_count(self):
        """Test error count property."""
        violations = [
            ViolationReport(
                rule_id="TEST-001",
                severity=Severity.ERROR,
                file_path=Path("/test1"),
                message="Error 1",
            ),
            ViolationReport(
                rule_id="TEST-002",
                severity=Severity.ERROR,
                file_path=Path("/test2"),
                message="Error 2",
            ),
            ViolationReport(
                rule_id="TEST-003",
                severity=Severity.WARNING,
                file_path=Path("/test3"),
                message="Warning 1",
            ),
        ]

        result = ScanResult(scan_path=Path("/docs"), violations=violations)
        assert result.error_count == 2

    def test_warning_count(self):
        """Test warning count property."""
        violations = [
            ViolationReport(
                rule_id="TEST-001",
                severity=Severity.WARNING,
                file_path=Path("/test1"),
                message="Warning 1",
            ),
            ViolationReport(
                rule_id="TEST-002",
                severity=Severity.WARNING,
                file_path=Path("/test2"),
                message="Warning 2",
            ),
            ViolationReport(
                rule_id="TEST-003",
                severity=Severity.INFO,
                file_path=Path("/test3"),
                message="Info 1",
            ),
        ]

        result = ScanResult(scan_path=Path("/docs"), violations=violations)
        assert result.warning_count == 2

    def test_info_count(self):
        """Test info count property."""
        violations = [
            ViolationReport(
                rule_id="TEST-001",
                severity=Severity.INFO,
                file_path=Path("/test1"),
                message="Info 1",
            ),
            ViolationReport(
                rule_id="TEST-002",
                severity=Severity.ERROR,
                file_path=Path("/test2"),
                message="Error 1",
            ),
        ]

        result = ScanResult(scan_path=Path("/docs"), violations=violations)
        assert result.info_count == 1

    def test_auto_fixable_count(self):
        """Test auto-fixable count property."""
        violations = [
            ViolationReport(
                rule_id="TEST-001",
                severity=Severity.ERROR,
                file_path=Path("/test1"),
                message="Error 1",
                auto_fixable=True,
            ),
            ViolationReport(
                rule_id="TEST-002",
                severity=Severity.WARNING,
                file_path=Path("/test2"),
                message="Warning 1",
                auto_fixable=True,
            ),
            ViolationReport(
                rule_id="TEST-003",
                severity=Severity.INFO,
                file_path=Path("/test3"),
                message="Info 1",
                auto_fixable=False,
            ),
        ]

        result = ScanResult(scan_path=Path("/docs"), violations=violations)
        assert result.auto_fixable_count == 2

    def test_passed_property(self):
        """Test passed property."""
        # No errors = passed
        result1 = ScanResult(
            scan_path=Path("/docs"),
            violations=[
                ViolationReport(
                    rule_id="TEST-001",
                    severity=Severity.WARNING,
                    file_path=Path("/test"),
                    message="Warning",
                )
            ],
        )
        assert result1.passed is True

        # Has errors = not passed
        result2 = ScanResult(
            scan_path=Path("/docs"),
            violations=[
                ViolationReport(
                    rule_id="TEST-001",
                    severity=Severity.ERROR,
                    file_path=Path("/test"),
                    message="Error",
                )
            ],
        )
        assert result2.passed is False

    def test_get_violations_by_severity(self):
        """Test filtering violations by severity."""
        violations = [
            ViolationReport(
                rule_id="TEST-001",
                severity=Severity.ERROR,
                file_path=Path("/test1"),
                message="Error 1",
            ),
            ViolationReport(
                rule_id="TEST-002",
                severity=Severity.ERROR,
                file_path=Path("/test2"),
                message="Error 2",
            ),
            ViolationReport(
                rule_id="TEST-003",
                severity=Severity.WARNING,
                file_path=Path("/test3"),
                message="Warning 1",
            ),
        ]

        result = ScanResult(scan_path=Path("/docs"), violations=violations)

        errors = result.get_violations_by_severity(Severity.ERROR)
        assert len(errors) == 2
        assert all(v.severity == Severity.ERROR for v in errors)

        warnings = result.get_violations_by_severity(Severity.WARNING)
        assert len(warnings) == 1

    def test_get_violations_by_rule(self):
        """Test filtering violations by rule ID."""
        violations = [
            ViolationReport(
                rule_id="STAGE-001",
                severity=Severity.ERROR,
                file_path=Path("/test1"),
                message="Error 1",
            ),
            ViolationReport(
                rule_id="STAGE-001",
                severity=Severity.ERROR,
                file_path=Path("/test2"),
                message="Error 2",
            ),
            ViolationReport(
                rule_id="NUM-001",
                severity=Severity.WARNING,
                file_path=Path("/test3"),
                message="Warning 1",
            ),
        ]

        result = ScanResult(scan_path=Path("/docs"), violations=violations)

        stage_violations = result.get_violations_by_rule("STAGE-001")
        assert len(stage_violations) == 2
        assert all(v.rule_id == "STAGE-001" for v in stage_violations)

    def test_scan_result_to_dict(self):
        """Test converting scan result to dictionary."""
        violations = [
            ViolationReport(
                rule_id="TEST-001",
                severity=Severity.ERROR,
                file_path=Path("/test"),
                message="Test error",
            )
        ]

        result = ScanResult(
            scan_path=Path("/docs"),
            violations=violations,
            files_scanned=50,
            scan_time_ms=100.5,
        )

        data = result.to_dict()

        assert data["scan_path"] == "/docs"
        assert len(data["violations"]) == 1
        assert data["files_scanned"] == 50
        assert data["scan_time_ms"] == 100.5
        assert data["summary"]["total_violations"] == 1
        assert data["summary"]["errors"] == 1
        assert data["summary"]["passed"] is False

    def test_scan_result_from_dict(self):
        """Test creating scan result from dictionary."""
        data = {
            "scan_path": "/docs",
            "violations": [
                {
                    "rule_id": "TEST-001",
                    "severity": "ERROR",
                    "file_path": "/test",
                    "message": "Test error",
                    "fix_suggestion": None,
                    "auto_fixable": False,
                    "context": {},
                }
            ],
            "files_scanned": 50,
            "scan_time_ms": 100.5,
            "scanner_version": "1.0.0",
        }

        result = ScanResult.from_dict(data)

        assert result.scan_path == Path("/docs")
        assert len(result.violations) == 1
        assert result.files_scanned == 50
        assert result.scan_time_ms == 100.5

    def test_scan_result_str_representation(self):
        """Test string representation of scan result."""
        violations = [
            ViolationReport(
                rule_id="TEST-001",
                severity=Severity.ERROR,
                file_path=Path("/test"),
                message="Test error",
            )
        ]

        result = ScanResult(
            scan_path=Path("/docs"),
            violations=violations,
            files_scanned=100,
            scan_time_ms=250.5,
        )

        str_repr = str(result)
        assert "Scan Results" in str_repr
        assert "Files scanned: 100" in str_repr
        assert "250.50ms" in str_repr
        assert "Errors: 1" in str_repr

    def test_scan_result_str_no_violations(self):
        """Test string representation with no violations."""
        result = ScanResult(
            scan_path=Path("/docs"),
            violations=[],
            files_scanned=100,
        )

        str_repr = str(result)
        assert "✅ No violations found!" in str_repr
