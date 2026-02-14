"""Unit tests for stage consistency validation.

SDLC 6.0.5 - SPEC-0021 Stage Consistency Validation.
Sprint 136 - Validate Consistency Command.
"""

import json
import tempfile
from pathlib import Path

import pytest

from sdlcctl.validation.consistency import (
    ConsistencyConfig,
    ConsistencyEngine,
    ConsistencyReportFormatter,
    ConsistencyResult,
)
from sdlcctl.validation.consistency.models import (
    ConsistencyStatus,
    ConsistencyViolation,
    StageConsistencyResult,
)
from sdlcctl.validation.tier import Tier
from sdlcctl.validation.violation import Severity


@pytest.fixture
def temp_project_structure():
    """Create a temporary project structure for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)

        # Create Stage 01 (Planning)
        stage_01 = root / "docs" / "01-planning"
        (stage_01 / "03-Functional-Requirements").mkdir(parents=True)

        # Create FR-001 file
        fr_001 = stage_01 / "03-Functional-Requirements" / "FR-001-Authentication.md"
        fr_001.write_text("""---
id: FR-001
status: APPROVED
---

# FR-001: User Authentication

## Requirements

Users must be able to authenticate via username/password.
""")

        # Create Stage 02 (Design)
        stage_02 = root / "docs" / "02-design"
        (stage_02 / "01-ADRs").mkdir(parents=True)

        # Create ADR that references FR-001
        adr_001 = stage_02 / "01-ADRs" / "ADR-001-Auth-Architecture.md"
        adr_001.write_text("""---
id: ADR-001
status: APPROVED
---

# ADR-001: Authentication Architecture

## Context

Based on FR-001 requirements, we need to design authentication.

## Decision

Use JWT tokens with refresh token rotation.
""")

        # Create ADR without references (will trigger violation)
        adr_002 = stage_02 / "01-ADRs" / "ADR-002-Database.md"
        adr_002.write_text("""---
id: ADR-002
status: APPROVED
---

# ADR-002: Database Architecture

## Decision

Use PostgreSQL.
""")

        # Create Stage 03 (Integrate)
        stage_03 = root / "docs" / "03-integrate"
        (stage_03 / "01-api-contracts").mkdir(parents=True)

        # Create OpenAPI spec
        openapi = stage_03 / "01-api-contracts" / "openapi.yaml"
        openapi.write_text("""openapi: 3.0.0
info:
  title: Test API
  version: 1.0.0
paths:
  /users:
    get:
      summary: List users
      responses:
        '200':
          description: OK
  /users/{id}:
    get:
      summary: Get user by ID
      responses:
        '200':
          description: OK
""")

        # Create Stage 04 (Build)
        stage_04 = root / "backend" / "app"
        (stage_04 / "api" / "routes").mkdir(parents=True)

        # Create route file
        users_route = stage_04 / "api" / "routes" / "users.py"
        users_route.write_text('''"""User routes.

Implements FR-001: User authentication.
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/users")
def list_users():
    """List all users."""
    return []


@router.get("/users/{id}")
def get_user(id: int):
    """Get user by ID."""
    return {"id": id}
''')

        yield {
            "root": root,
            "stage_01": stage_01,
            "stage_02": stage_02,
            "stage_03": stage_03,
            "stage_04": stage_04,
        }


class TestConsistencyConfig:
    """Tests for ConsistencyConfig."""

    def test_config_validation_valid(self, temp_project_structure):
        """Test valid config passes validation."""
        config = ConsistencyConfig(
            tier=Tier.STANDARD,
            stage_paths={
                "01": temp_project_structure["stage_01"],
                "02": temp_project_structure["stage_02"],
                "03": temp_project_structure["stage_03"],
                "04": temp_project_structure["stage_04"],
            },
        )

        errors = config.validate()
        assert errors == []

    def test_config_validation_missing_stage(self, temp_project_structure):
        """Test missing stage fails validation."""
        config = ConsistencyConfig(
            tier=Tier.STANDARD,
            stage_paths={
                "01": temp_project_structure["stage_01"],
                "02": temp_project_structure["stage_02"],
                # Missing 03 and 04
            },
        )

        errors = config.validate()
        assert len(errors) == 2
        assert "Stage 03" in errors[0]
        assert "Stage 04" in errors[1]

    def test_config_validation_nonexistent_path(self):
        """Test nonexistent path fails validation."""
        config = ConsistencyConfig(
            tier=Tier.STANDARD,
            stage_paths={
                "01": Path("/nonexistent/path"),
                "02": Path("/another/nonexistent"),
                "03": Path("/yet/another"),
                "04": Path("/last/one"),
            },
        )

        errors = config.validate()
        assert len(errors) == 4
        assert all("does not exist" in e for e in errors)


class TestConsistencyEngine:
    """Tests for ConsistencyEngine."""

    def test_engine_from_paths(self, temp_project_structure):
        """Test creating engine from paths."""
        engine = ConsistencyEngine.from_paths(
            stage_01=temp_project_structure["stage_01"],
            stage_02=temp_project_structure["stage_02"],
            stage_03=temp_project_structure["stage_03"],
            stage_04=temp_project_structure["stage_04"],
            tier=Tier.STANDARD,
        )

        assert engine is not None
        assert engine.config.tier == Tier.STANDARD
        assert len(engine.checkers) == 4

    def test_engine_auto_detect_tier(self, temp_project_structure):
        """Test tier auto-detection based on document count."""
        engine = ConsistencyEngine.from_paths(
            stage_01=temp_project_structure["stage_01"],
            stage_02=temp_project_structure["stage_02"],
            stage_03=temp_project_structure["stage_03"],
            stage_04=temp_project_structure["stage_04"],
            tier=None,  # Auto-detect
        )

        # With few documents, should detect as LITE
        assert engine.config.tier == Tier.LITE

    def test_engine_validate(self, temp_project_structure):
        """Test running validation."""
        engine = ConsistencyEngine.from_paths(
            stage_01=temp_project_structure["stage_01"],
            stage_02=temp_project_structure["stage_02"],
            stage_03=temp_project_structure["stage_03"],
            stage_04=temp_project_structure["stage_04"],
            tier=Tier.STANDARD,
        )

        result = engine.validate()

        assert isinstance(result, ConsistencyResult)
        assert result.tier == Tier.STANDARD
        assert result.framework_version == "6.0.5"
        assert len(result.stage_pairs) == 4
        assert "stage_01_02" in result.stage_pairs

    def test_engine_detect_violations(self, temp_project_structure):
        """Test that violations are detected."""
        engine = ConsistencyEngine.from_paths(
            stage_01=temp_project_structure["stage_01"],
            stage_02=temp_project_structure["stage_02"],
            stage_03=temp_project_structure["stage_03"],
            stage_04=temp_project_structure["stage_04"],
            tier=Tier.PROFESSIONAL,  # PRO tier makes CONS-001 an ERROR
        )

        result = engine.validate()

        # ADR-002 doesn't reference FR-001, should trigger CONS-001
        violations = result.all_violations
        cons_001_violations = [v for v in violations if v.rule_id == "CONS-001"]

        # Should have at least one violation for ADR-002
        assert len(cons_001_violations) > 0


class TestConsistencyResult:
    """Tests for ConsistencyResult model."""

    def test_result_passed_when_no_errors(self):
        """Test result shows passed when no errors."""
        result = ConsistencyResult(
            project_name="test",
            tier=Tier.STANDARD,
            framework_version="6.0.5",
            stage_pairs={
                "stage_01_02": StageConsistencyResult(
                    source_stage="01",
                    target_stage="02",
                    status=ConsistencyStatus.CONSISTENT,
                    violations=[],
                ),
            },
        )

        assert result.passed is True
        assert result.error_count == 0

    def test_result_failed_when_has_errors(self):
        """Test result shows failed when has errors."""
        result = ConsistencyResult(
            project_name="test",
            tier=Tier.PROFESSIONAL,
            framework_version="6.0.5",
            stage_pairs={
                "stage_01_02": StageConsistencyResult(
                    source_stage="01",
                    target_stage="02",
                    status=ConsistencyStatus.INCONSISTENT,
                    violations=[
                        ConsistencyViolation(
                            rule_id="CONS-001",
                            severity=Severity.ERROR,
                            source_stage="01",
                            target_stage="02",
                            message="Test violation",
                        ),
                    ],
                ),
            },
        )

        assert result.passed is False
        assert result.error_count == 1

    def test_result_to_dict(self):
        """Test JSON serialization."""
        result = ConsistencyResult(
            project_name="test",
            tier=Tier.STANDARD,
            framework_version="6.0.5",
            stage_pairs={},
            execution_time_seconds=1.5,
        )

        data = result.to_dict()

        assert data["project"] == "test"
        assert data["tier"] == "standard"
        assert data["framework_version"] == "6.0.5"
        assert "summary" in data


class TestConsistencyReportFormatter:
    """Tests for ConsistencyReportFormatter."""

    @pytest.fixture
    def sample_result(self):
        """Create a sample result for formatting tests."""
        return ConsistencyResult(
            project_name="test-project",
            tier=Tier.STANDARD,
            framework_version="6.0.5",
            stage_pairs={
                "stage_01_02": StageConsistencyResult(
                    source_stage="01",
                    target_stage="02",
                    status=ConsistencyStatus.CONSISTENT,
                    violations=[
                        ConsistencyViolation(
                            rule_id="CONS-001",
                            severity=Severity.WARNING,
                            source_stage="01",
                            target_stage="02",
                            message="Test warning",
                            fix_suggestion="Fix it",
                        ),
                    ],
                    artifacts_checked=10,
                ),
                "stage_02_03": StageConsistencyResult(
                    source_stage="02",
                    target_stage="03",
                    status=ConsistencyStatus.CONSISTENT,
                    violations=[],
                    artifacts_checked=5,
                ),
            },
            execution_time_seconds=0.5,
        )

    def test_format_text(self, sample_result):
        """Test text output format."""
        formatter = ConsistencyReportFormatter()
        output = formatter.format_text(sample_result)

        assert "Stage Consistency Validation Report" in output
        assert "test-project" in output
        assert "STANDARD" in output
        assert "CONS-001" in output
        assert "Fix it" in output

    def test_format_json(self, sample_result):
        """Test JSON output format."""
        formatter = ConsistencyReportFormatter()
        output = formatter.format_json(sample_result)

        data = json.loads(output)
        assert data["project"] == "test-project"
        assert data["tier"] == "standard"
        assert "violations" in data

    def test_format_github(self, sample_result):
        """Test GitHub Actions output format."""
        formatter = ConsistencyReportFormatter()
        output = formatter.format_github(sample_result)

        assert "::warning" in output
        assert "CONS-001" in output

    def test_format_summary(self, sample_result):
        """Test summary output format."""
        formatter = ConsistencyReportFormatter()
        output = formatter.format_summary(sample_result)

        assert "PASS" in output
        assert "Warnings: 1" in output
        assert "Errors: 0" in output


class TestTierSpecificSeverity:
    """Tests for tier-specific severity handling."""

    def test_lite_tier_makes_all_info(self, temp_project_structure):
        """Test LITE tier downgrades all violations to INFO."""
        engine = ConsistencyEngine.from_paths(
            stage_01=temp_project_structure["stage_01"],
            stage_02=temp_project_structure["stage_02"],
            stage_03=temp_project_structure["stage_03"],
            stage_04=temp_project_structure["stage_04"],
            tier=Tier.LITE,
        )

        result = engine.validate()

        for violation in result.all_violations:
            assert violation.severity == Severity.INFO

    def test_professional_tier_has_errors(self, temp_project_structure):
        """Test PROFESSIONAL tier has ERROR severity for critical rules."""
        engine = ConsistencyEngine.from_paths(
            stage_01=temp_project_structure["stage_01"],
            stage_02=temp_project_structure["stage_02"],
            stage_03=temp_project_structure["stage_03"],
            stage_04=temp_project_structure["stage_04"],
            tier=Tier.PROFESSIONAL,
        )

        result = engine.validate()

        # CONS-001 should be ERROR for PROFESSIONAL tier
        cons_001 = [v for v in result.all_violations if v.rule_id == "CONS-001"]
        if cons_001:
            assert cons_001[0].severity == Severity.ERROR
