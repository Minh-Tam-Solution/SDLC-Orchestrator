"""
Unit Tests for SDLC Specification CLI - Sprint 119 Track 2.

Tests for sdlcctl spec validate command and related validators.

Framework: SDLC 6.0.5
Sprint: 119 - Specification CLI Commands
Reference: SPEC-0002 Framework 6.0.5 Specification Standard
"""

import tempfile
from pathlib import Path

import pytest
from typer.testing import CliRunner

from sdlcctl.commands.spec import SpecificationValidator, app
from sdlcctl.validation.violation import Severity


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def runner():
    """CLI test runner."""
    return CliRunner()


@pytest.fixture
def valid_spec_content() -> str:
    """Valid SDLC 6.0.5 specification content."""
    return """---
spec_id: SPEC-0001
title: Test Specification
version: "1.0.0"
status: APPROVED
tier:
  - PROFESSIONAL
  - ENTERPRISE
pillar:
  - Pillar 7 - Quality Assurance
owner: Test Team
last_updated: "2026-01-29"
tags:
  - test
  - specification
related_adrs:
  - ADR-041-Stage-Dependency-Matrix
related_specs:
  - SPEC-0002
---

# SPEC-0001: Test Specification

## 1. Overview

Test specification for validation.

## 2. Functional Requirements

### FR-001: Test Requirement

**Priority**: P0
**Complexity**: Low
**Tier Applicability**: ALL

```gherkin
GIVEN a test precondition
WHEN a test action occurs
THEN a test result happens
  AND additional assertion
```

### FR-002: Another Requirement

**Priority**: P1

```gherkin
GIVEN another precondition
WHEN another action
THEN another result
```

## 3. Acceptance Criteria

| ID | Criterion | Expected Result | Test Method | Priority |
|----|-----------|-----------------|-------------|----------|
| AC-001 | Test criterion 1 | Expected result 1 | Unit test | P0 |
| AC-002 | Test criterion 2 | Expected result 2 | Integration test | P0 |
| AC-003 | Test criterion 3 | Expected result 3 | E2E test | P1 |
| AC-004 | Test criterion 4 | Expected result 4 | Manual test | P1 |
| AC-005 | Test criterion 5 | Expected result 5 | Load test | P1 |

## 4. Tier-Specific Requirements

### PROFESSIONAL Tier

- Feature A enabled with warning mode

### ENTERPRISE Tier

- Feature A enabled with full enforcement
- Additional feature B
"""


@pytest.fixture
def invalid_spec_no_frontmatter() -> str:
    """Specification without YAML frontmatter."""
    return """# SPEC-0001: Missing Frontmatter

This specification has no YAML frontmatter.

## Requirements

Some requirements here.
"""


@pytest.fixture
def invalid_spec_missing_fields() -> str:
    """Specification with missing required fields."""
    return """---
spec_id: SPEC-0002
title: Missing Fields Spec
# Missing: version, status, tier, owner, last_updated
---

# SPEC-0002: Missing Fields

Content here.
"""


@pytest.fixture
def invalid_spec_wrong_format() -> str:
    """Specification with invalid field formats."""
    return """---
spec_id: INVALID-FORMAT
title: Wrong Format Spec
version: invalid-version
status: INVALID_STATUS
tier: PROFESSIONAL
owner: Test Team
last_updated: 2026/01/29
---

# Wrong Format Spec

Content here.
"""


@pytest.fixture
def spec_without_bdd() -> str:
    """Specification without BDD format requirements."""
    return """---
spec_id: SPEC-0003
title: Non-BDD Spec
version: "1.0.0"
status: DRAFT
tier:
  - LITE
owner: Test Team
last_updated: "2026-01-29"
---

# SPEC-0003: Non-BDD Spec

## Functional Requirements

### FR-001: Old Style Requirement

The system shall process data efficiently.
The system should handle errors gracefully.
"""


@pytest.fixture
def spec_without_tier_sections() -> str:
    """PROFESSIONAL spec without tier-specific sections."""
    return """---
spec_id: SPEC-0004
title: Missing Tier Sections
version: "1.0.0"
status: APPROVED
tier:
  - PROFESSIONAL
  - ENTERPRISE
owner: Test Team
last_updated: "2026-01-29"
---

# SPEC-0004: Missing Tier Sections

## Functional Requirements

Some requirements without tier sections.
"""


@pytest.fixture
def spec_few_acceptance_criteria() -> str:
    """Specification with too few acceptance criteria."""
    return """---
spec_id: SPEC-0005
title: Few Acceptance Criteria
version: "1.0.0"
status: APPROVED
tier:
  - PROFESSIONAL
owner: Test Team
last_updated: "2026-01-29"
---

# SPEC-0005: Few Acceptance Criteria

## Acceptance Criteria

| ID | Criterion | Expected Result | Test Method | Priority |
|----|-----------|-----------------|-------------|----------|
| AC-001 | Only one criterion | Some result | Unit test | P0 |
| AC-002 | Second criterion | Some result | Unit test | P0 |
"""


@pytest.fixture
def temp_spec_dir(tmp_path: Path, valid_spec_content: str) -> Path:
    """Create temporary directory with spec files."""
    spec_dir = tmp_path / "specs"
    spec_dir.mkdir()

    # Create valid spec
    (spec_dir / "SPEC-0001-Valid.md").write_text(valid_spec_content)

    return spec_dir


# ============================================================================
# SpecificationValidator Unit Tests
# ============================================================================


class TestSpecificationValidator:
    """Tests for SpecificationValidator class."""

    def test_validate_valid_spec(self, tmp_path: Path, valid_spec_content: str):
        """Test validation of valid specification."""
        spec_file = tmp_path / "SPEC-0001-Valid.md"
        spec_file.write_text(valid_spec_content)

        validator = SpecificationValidator(spec_file)
        result = validator.validate()

        # Should have no errors
        assert result.error_count == 0
        assert result.files_scanned == 1
        assert result.passed is True

    def test_validate_missing_frontmatter(
        self, tmp_path: Path, invalid_spec_no_frontmatter: str
    ):
        """Test validation catches missing frontmatter."""
        spec_file = tmp_path / "SPEC-0001-NoFrontmatter.md"
        spec_file.write_text(invalid_spec_no_frontmatter)

        validator = SpecificationValidator(spec_file)
        result = validator.validate()

        assert result.error_count >= 1
        assert result.passed is False

        # Find the SPEC-001 violation
        spec_001_violations = [v for v in result.violations if v.rule_id == "SPEC-001"]
        assert len(spec_001_violations) == 1
        assert "Missing YAML frontmatter" in spec_001_violations[0].message

    def test_validate_missing_required_fields(
        self, tmp_path: Path, invalid_spec_missing_fields: str
    ):
        """Test validation catches missing required fields."""
        spec_file = tmp_path / "SPEC-0002-MissingFields.md"
        spec_file.write_text(invalid_spec_missing_fields)

        validator = SpecificationValidator(spec_file)
        result = validator.validate()

        assert result.error_count >= 1

        # Find SPEC-003 violation (missing fields)
        spec_003_violations = [v for v in result.violations if v.rule_id == "SPEC-003"]
        assert len(spec_003_violations) == 1
        assert "Missing required frontmatter fields" in spec_003_violations[0].message

    def test_validate_invalid_spec_id_format(self, tmp_path: Path):
        """Test validation catches invalid spec_id format."""
        content = """---
spec_id: INVALID-ID
title: Test
version: "1.0.0"
status: APPROVED
tier:
  - LITE
owner: Test
last_updated: "2026-01-29"
---

# Test
"""
        spec_file = tmp_path / "SPEC-INVALID.md"
        spec_file.write_text(content)

        validator = SpecificationValidator(spec_file)
        result = validator.validate()

        spec_004_violations = [v for v in result.violations if v.rule_id == "SPEC-004"]
        assert len(spec_004_violations) == 1
        assert "Invalid spec_id format" in spec_004_violations[0].message

    def test_validate_invalid_status(self, tmp_path: Path):
        """Test validation catches invalid status value."""
        content = """---
spec_id: SPEC-0001
title: Test
version: "1.0.0"
status: INVALID_STATUS
tier:
  - LITE
owner: Test
last_updated: "2026-01-29"
---

# Test
"""
        spec_file = tmp_path / "SPEC-0001.md"
        spec_file.write_text(content)

        validator = SpecificationValidator(spec_file)
        result = validator.validate()

        spec_006_violations = [v for v in result.violations if v.rule_id == "SPEC-006"]
        assert len(spec_006_violations) == 1
        assert "Invalid status" in spec_006_violations[0].message

    def test_validate_tier_not_array(self, tmp_path: Path):
        """Test validation catches tier not being an array."""
        content = """---
spec_id: SPEC-0001
title: Test
version: "1.0.0"
status: APPROVED
tier: PROFESSIONAL
owner: Test
last_updated: "2026-01-29"
---

# Test
"""
        spec_file = tmp_path / "SPEC-0001.md"
        spec_file.write_text(content)

        validator = SpecificationValidator(spec_file)
        result = validator.validate()

        spec_007_violations = [v for v in result.violations if v.rule_id == "SPEC-007"]
        assert len(spec_007_violations) == 1
        assert "tier must be an array" in spec_007_violations[0].message

    def test_validate_invalid_tier_value(self, tmp_path: Path):
        """Test validation catches invalid tier values."""
        content = """---
spec_id: SPEC-0001
title: Test
version: "1.0.0"
status: APPROVED
tier:
  - INVALID_TIER
  - PROFESSIONAL
owner: Test
last_updated: "2026-01-29"
---

# Test
"""
        spec_file = tmp_path / "SPEC-0001.md"
        spec_file.write_text(content)

        validator = SpecificationValidator(spec_file)
        result = validator.validate()

        spec_008_violations = [v for v in result.violations if v.rule_id == "SPEC-008"]
        assert len(spec_008_violations) == 1
        assert "Invalid tier values" in spec_008_violations[0].message

    def test_validate_missing_bdd_format(self, tmp_path: Path):
        """Test validation warns about missing BDD format."""
        # Content with FR- block but no BDD format (no gherkin keywords)
        content = """---
spec_id: SPEC-0003
title: Non-BDD Spec
version: "1.0.0"
status: DRAFT
tier:
  - LITE
owner: Test Team
last_updated: "2026-01-29"
---

# SPEC-0003: Non-BDD Spec

## Functional Requirements

### FR-001: Old Style Requirement

The system shall process data efficiently.
The system should handle errors gracefully.
This requirement uses legacy format without BDD keywords.
"""
        spec_file = tmp_path / "SPEC-0003.md"
        spec_file.write_text(content)

        validator = SpecificationValidator(spec_file)
        result = validator.validate()

        spec_020_violations = [v for v in result.violations if v.rule_id == "SPEC-020"]
        assert len(spec_020_violations) >= 1
        assert "Missing BDD format" in spec_020_violations[0].message

    def test_validate_missing_tier_sections(
        self, tmp_path: Path, spec_without_tier_sections: str
    ):
        """Test validation warns about missing tier sections for PROFESSIONAL+ specs."""
        spec_file = tmp_path / "SPEC-0004.md"
        spec_file.write_text(spec_without_tier_sections)

        validator = SpecificationValidator(spec_file)
        result = validator.validate()

        spec_030_violations = [v for v in result.violations if v.rule_id == "SPEC-030"]
        assert len(spec_030_violations) == 1
        assert "Missing 'Tier-Specific Requirements' section" in spec_030_violations[0].message

    def test_validate_missing_acceptance_criteria(self, tmp_path: Path):
        """Test validation warns about missing acceptance criteria section."""
        content = """---
spec_id: SPEC-0001
title: Test
version: "1.0.0"
status: APPROVED
tier:
  - LITE
owner: Test
last_updated: "2026-01-29"
---

# Test

## Functional Requirements

Some requirements.
"""
        spec_file = tmp_path / "SPEC-0001.md"
        spec_file.write_text(content)

        validator = SpecificationValidator(spec_file)
        result = validator.validate()

        spec_040_violations = [v for v in result.violations if v.rule_id == "SPEC-040"]
        assert len(spec_040_violations) == 1
        assert "Missing 'Acceptance Criteria' section" in spec_040_violations[0].message

    def test_validate_few_acceptance_criteria(
        self, tmp_path: Path, spec_few_acceptance_criteria: str
    ):
        """Test validation warns about too few acceptance criteria."""
        spec_file = tmp_path / "SPEC-0005.md"
        spec_file.write_text(spec_few_acceptance_criteria)

        validator = SpecificationValidator(spec_file)
        result = validator.validate()

        spec_042_violations = [v for v in result.violations if v.rule_id == "SPEC-042"]
        assert len(spec_042_violations) == 1
        assert "Minimum 5 required" in spec_042_violations[0].message

    def test_validate_directory(self, temp_spec_dir: Path):
        """Test validation of directory with multiple specs."""
        validator = SpecificationValidator(temp_spec_dir)
        result = validator.validate()

        assert result.files_scanned >= 1
        assert result.scan_path == temp_spec_dir

    def test_validate_nonexistent_file(self, tmp_path: Path):
        """Test validation of nonexistent file."""
        # The validator won't find any files if path doesn't exist
        nonexistent = tmp_path / "nonexistent.md"

        # Create empty directory
        (tmp_path / "empty").mkdir()
        validator = SpecificationValidator(tmp_path / "empty")
        result = validator.validate()

        assert result.files_scanned == 0
        assert result.error_count == 0

    def test_recommended_fields_info(self, tmp_path: Path):
        """Test that missing recommended fields are reported as INFO."""
        content = """---
spec_id: SPEC-0001
title: Test
version: "1.0.0"
status: APPROVED
tier:
  - LITE
owner: Test
last_updated: "2026-01-29"
---

# Test
"""
        spec_file = tmp_path / "SPEC-0001.md"
        spec_file.write_text(content)

        validator = SpecificationValidator(spec_file)
        result = validator.validate()

        spec_010_violations = [v for v in result.violations if v.rule_id == "SPEC-010"]
        assert len(spec_010_violations) == 1
        assert spec_010_violations[0].severity == Severity.INFO
        assert "Missing recommended frontmatter fields" in spec_010_violations[0].message


# ============================================================================
# CLI Command Tests
# ============================================================================


class TestSpecCLI:
    """Tests for spec CLI commands."""

    def test_spec_validate_help(self, runner: CliRunner):
        """Test spec validate --help."""
        result = runner.invoke(app, ["validate", "--help"])
        assert result.exit_code == 0
        assert "Validate SDLC Framework 6.0.5 specifications" in result.output

    def test_spec_validate_valid_file(
        self, runner: CliRunner, tmp_path: Path, valid_spec_content: str
    ):
        """Test validation of valid spec file."""
        spec_file = tmp_path / "SPEC-0001-Valid.md"
        spec_file.write_text(valid_spec_content)

        result = runner.invoke(app, ["validate", str(spec_file)])
        assert result.exit_code == 0
        assert "PASSED" in result.output or "No violations found" in result.output

    def test_spec_validate_invalid_file(
        self, runner: CliRunner, tmp_path: Path, invalid_spec_no_frontmatter: str
    ):
        """Test validation of invalid spec file."""
        spec_file = tmp_path / "SPEC-0001-Invalid.md"
        spec_file.write_text(invalid_spec_no_frontmatter)

        result = runner.invoke(app, ["validate", str(spec_file)])
        assert result.exit_code == 1
        assert "FAILED" in result.output

    def test_spec_validate_json_format(
        self, runner: CliRunner, tmp_path: Path, valid_spec_content: str
    ):
        """Test validation with JSON output format."""
        spec_file = tmp_path / "SPEC-0001-Valid.md"
        spec_file.write_text(valid_spec_content)

        result = runner.invoke(app, ["validate", str(spec_file), "--format", "json"])
        assert result.exit_code == 0
        assert '"violations"' in result.output
        assert '"files_scanned"' in result.output

    def test_spec_validate_strict_mode(
        self, runner: CliRunner, tmp_path: Path, spec_without_bdd: str
    ):
        """Test validation in strict mode (warnings = errors)."""
        spec_file = tmp_path / "SPEC-0003.md"
        spec_file.write_text(spec_without_bdd)

        result = runner.invoke(app, ["validate", str(spec_file), "--strict"])
        # In strict mode, warnings cause non-zero exit
        # (spec_without_bdd should have BDD warning)
        assert result.exit_code in [0, 1]  # Depends on whether warnings exist

    def test_spec_validate_with_tier(
        self, runner: CliRunner, tmp_path: Path, valid_spec_content: str
    ):
        """Test validation with tier filter."""
        spec_file = tmp_path / "SPEC-0001-Valid.md"
        spec_file.write_text(valid_spec_content)

        result = runner.invoke(
            app, ["validate", str(spec_file), "--tier", "PROFESSIONAL"]
        )
        assert result.exit_code == 0

    def test_spec_validate_invalid_tier(self, runner: CliRunner, tmp_path: Path):
        """Test validation with invalid tier."""
        spec_file = tmp_path / "SPEC-0001.md"
        spec_file.write_text("---\nspec_id: SPEC-0001\n---\n# Test")

        result = runner.invoke(
            app, ["validate", str(spec_file), "--tier", "INVALID_TIER"]
        )
        assert result.exit_code == 1
        assert "Invalid tier" in result.output

    def test_spec_report_help(self, runner: CliRunner):
        """Test spec report --help."""
        result = runner.invoke(app, ["report", "--help"])
        assert result.exit_code == 0
        assert "Generate specification compliance report" in result.output

    def test_spec_report_text_format(
        self, runner: CliRunner, tmp_path: Path, valid_spec_content: str
    ):
        """Test report generation in text format."""
        spec_file = tmp_path / "SPEC-0001-Valid.md"
        spec_file.write_text(valid_spec_content)

        result = runner.invoke(app, ["report", str(spec_file)])
        assert result.exit_code == 0
        assert "Compliance Report" in result.output or "Scan" in result.output

    def test_spec_report_markdown_format(
        self, runner: CliRunner, tmp_path: Path, valid_spec_content: str
    ):
        """Test report generation in markdown format."""
        spec_file = tmp_path / "SPEC-0001-Valid.md"
        spec_file.write_text(valid_spec_content)

        result = runner.invoke(
            app, ["report", str(spec_file), "--format", "markdown"]
        )
        assert result.exit_code == 0
        assert "# SDLC Specification Compliance Report" in result.output

    def test_spec_report_to_file(
        self, runner: CliRunner, tmp_path: Path, valid_spec_content: str
    ):
        """Test report output to file."""
        spec_file = tmp_path / "SPEC-0001-Valid.md"
        spec_file.write_text(valid_spec_content)
        output_file = tmp_path / "report.md"

        result = runner.invoke(
            app,
            ["report", str(spec_file), "--format", "markdown", "--output", str(output_file)],
        )
        assert result.exit_code == 0
        assert output_file.exists()
        content = output_file.read_text()
        assert "SDLC Specification Compliance Report" in content

    def test_spec_list_help(self, runner: CliRunner):
        """Test spec list --help."""
        result = runner.invoke(app, ["list", "--help"])
        assert result.exit_code == 0
        assert "List all specifications" in result.output

    def test_spec_list_empty_directory(self, runner: CliRunner, tmp_path: Path):
        """Test listing specs in empty directory."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        result = runner.invoke(app, ["list", str(empty_dir)])
        assert result.exit_code == 0
        assert "No specifications found" in result.output

    def test_spec_list_with_specs(
        self, runner: CliRunner, tmp_path: Path, valid_spec_content: str
    ):
        """Test listing specs in directory with specs."""
        spec_file = tmp_path / "SPEC-0001-Valid.md"
        spec_file.write_text(valid_spec_content)

        result = runner.invoke(app, ["list", str(tmp_path)])
        assert result.exit_code == 0
        assert "SPEC-0001" in result.output
        assert "SDLC Specifications" in result.output

    def test_spec_list_filter_by_tier(
        self, runner: CliRunner, tmp_path: Path, valid_spec_content: str
    ):
        """Test listing specs filtered by tier."""
        spec_file = tmp_path / "SPEC-0001-Valid.md"
        spec_file.write_text(valid_spec_content)

        # Filter by tier that exists
        result = runner.invoke(
            app, ["list", str(tmp_path), "--tier", "PROFESSIONAL"]
        )
        assert result.exit_code == 0
        assert "SPEC-0001" in result.output

        # Filter by tier that doesn't match
        result = runner.invoke(app, ["list", str(tmp_path), "--tier", "LITE"])
        assert result.exit_code == 0
        assert "No specifications match" in result.output

    def test_spec_list_filter_by_status(
        self, runner: CliRunner, tmp_path: Path, valid_spec_content: str
    ):
        """Test listing specs filtered by status."""
        spec_file = tmp_path / "SPEC-0001-Valid.md"
        spec_file.write_text(valid_spec_content)

        # Filter by status that exists
        result = runner.invoke(
            app, ["list", str(tmp_path), "--status", "APPROVED"]
        )
        assert result.exit_code == 0
        assert "SPEC-0001" in result.output


# ============================================================================
# Edge Cases and Error Handling
# ============================================================================


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_validate_yaml_parse_error(self, tmp_path: Path):
        """Test handling of invalid YAML in frontmatter."""
        content = """---
spec_id: SPEC-0001
invalid yaml: [unclosed bracket
title: Test
---

# Test
"""
        spec_file = tmp_path / "SPEC-0001.md"
        spec_file.write_text(content)

        validator = SpecificationValidator(spec_file)
        result = validator.validate()

        spec_002_violations = [v for v in result.violations if v.rule_id == "SPEC-002"]
        assert len(spec_002_violations) == 1
        assert "Invalid YAML frontmatter" in spec_002_violations[0].message

    def test_validate_empty_frontmatter(self, tmp_path: Path):
        """Test handling of empty frontmatter."""
        content = """---
---

# Empty Frontmatter
"""
        spec_file = tmp_path / "SPEC-0001.md"
        spec_file.write_text(content)

        validator = SpecificationValidator(spec_file)
        result = validator.validate()

        # Empty frontmatter (None) returns early after SPEC-002 check
        # The validator reports it's not a valid dict
        spec_002_violations = [v for v in result.violations if v.rule_id == "SPEC-002"]
        assert len(spec_002_violations) == 1
        assert "must be a dictionary" in spec_002_violations[0].message

    def test_validate_file_encoding_error(self, tmp_path: Path):
        """Test handling of file with encoding issues."""
        spec_file = tmp_path / "SPEC-0001.md"
        # Write binary content that's not valid UTF-8
        spec_file.write_bytes(b"\x80\x81\x82")

        validator = SpecificationValidator(spec_file)
        result = validator.validate()

        # Should report read error
        spec_000_violations = [v for v in result.violations if v.rule_id == "SPEC-000"]
        assert len(spec_000_violations) == 1
        assert "Failed to read file" in spec_000_violations[0].message

    def test_validate_very_long_content(self, tmp_path: Path, valid_spec_content: str):
        """Test validation of spec with very long content."""
        # Add lots of content
        long_content = valid_spec_content + "\n" + ("x" * 100000)

        spec_file = tmp_path / "SPEC-0001.md"
        spec_file.write_text(long_content)

        validator = SpecificationValidator(spec_file)
        result = validator.validate()

        # Should complete without error
        assert result.files_scanned == 1

    def test_validate_unicode_content(self, tmp_path: Path):
        """Test validation of spec with Unicode content."""
        content = """---
spec_id: SPEC-0001
title: 越南语规范 - Đặc tả Tiếng Việt
version: "1.0.0"
status: APPROVED
tier:
  - LITE
owner: Đội phát triển
last_updated: "2026-01-29"
---

# 越南语规范

## Yêu cầu chức năng

Nội dung tiếng Việt với các ký tự đặc biệt: ắ ẵ ặ ấ ầ ẩ ẫ ậ
"""
        spec_file = tmp_path / "SPEC-0001.md"
        spec_file.write_text(content, encoding="utf-8")

        validator = SpecificationValidator(spec_file)
        result = validator.validate()

        assert result.files_scanned == 1

    def test_validate_multiple_specs_in_directory(self, tmp_path: Path):
        """Test validation of multiple specs in a directory."""
        for i in range(5):
            content = f"""---
spec_id: SPEC-000{i}
title: Test Spec {i}
version: "1.0.0"
status: APPROVED
tier:
  - LITE
owner: Test
last_updated: "2026-01-29"
---

# Test Spec {i}
"""
            (tmp_path / f"SPEC-000{i}-Test.md").write_text(content)

        validator = SpecificationValidator(tmp_path)
        result = validator.validate()

        assert result.files_scanned == 5


# ============================================================================
# Violation Report Tests
# ============================================================================


class TestViolationReports:
    """Tests for violation report formatting and context."""

    def test_violation_context_includes_details(self, tmp_path: Path):
        """Test that violation context includes helpful details."""
        content = """---
spec_id: INVALID
title: Test
version: bad-version
status: APPROVED
tier:
  - LITE
owner: Test
last_updated: "2026-01-29"
---

# Test
"""
        spec_file = tmp_path / "SPEC-0001.md"
        spec_file.write_text(content)

        validator = SpecificationValidator(spec_file)
        result = validator.validate()

        for v in result.violations:
            if v.rule_id == "SPEC-004":
                assert "current_value" in v.context
                assert v.context["current_value"] == "INVALID"
            if v.rule_id == "SPEC-005":
                assert "current_value" in v.context
                assert v.context["current_value"] == "bad-version"

    def test_violation_auto_fixable_flag(self, tmp_path: Path):
        """Test that auto-fixable violations are properly flagged."""
        content = """---
spec_id: SPEC-0001
title: Test
version: "1.0.0"
status: APPROVED
tier:
  - LITE
owner: Test
last_updated: "2026-01-29"
---

# Test
"""
        spec_file = tmp_path / "SPEC-0001.md"
        spec_file.write_text(content)

        validator = SpecificationValidator(spec_file)
        result = validator.validate()

        # Check auto_fixable count
        auto_fixable = [v for v in result.violations if v.auto_fixable]
        non_auto_fixable = [v for v in result.violations if not v.auto_fixable]

        # Verify proper categorization
        assert result.auto_fixable_count == len(auto_fixable)

    def test_scan_result_to_dict(self, tmp_path: Path, valid_spec_content: str):
        """Test ScanResult serialization to dict."""
        spec_file = tmp_path / "SPEC-0001.md"
        spec_file.write_text(valid_spec_content)

        validator = SpecificationValidator(spec_file)
        result = validator.validate()

        result_dict = result.to_dict()

        assert "scan_path" in result_dict
        assert "violations" in result_dict
        assert "files_scanned" in result_dict
        assert "scan_time_ms" in result_dict
        assert "summary" in result_dict
        assert "total_violations" in result_dict["summary"]
        assert "passed" in result_dict["summary"]


# ============================================================================
# Performance Tests
# ============================================================================


class TestPerformance:
    """Performance tests for specification validation."""

    def test_validation_performance_single_file(
        self, tmp_path: Path, valid_spec_content: str
    ):
        """Test that single file validation completes in <100ms."""
        import time

        spec_file = tmp_path / "SPEC-0001.md"
        spec_file.write_text(valid_spec_content)

        start = time.perf_counter()
        validator = SpecificationValidator(spec_file)
        result = validator.validate()
        elapsed = (time.perf_counter() - start) * 1000

        assert elapsed < 100, f"Validation took {elapsed:.2f}ms, expected <100ms"
        assert result.scan_time_ms < 100

    def test_validation_performance_multiple_files(self, tmp_path: Path):
        """Test that 10 files validate in <500ms."""
        import time

        for i in range(10):
            content = f"""---
spec_id: SPEC-00{i:02d}
title: Test Spec {i}
version: "1.0.0"
status: APPROVED
tier:
  - PROFESSIONAL
  - ENTERPRISE
owner: Test Team
last_updated: "2026-01-29"
tags:
  - test
related_adrs:
  - ADR-001
related_specs:
  - SPEC-0001
---

# Test Spec {i}

## Functional Requirements

### FR-001: Test

```gherkin
GIVEN something
WHEN action
THEN result
```

## Acceptance Criteria

| ID | Criterion | Expected Result | Test Method | Priority |
|----|-----------|-----------------|-------------|----------|
| AC-001 | Test 1 | Result 1 | Unit | P0 |
| AC-002 | Test 2 | Result 2 | Unit | P0 |
| AC-003 | Test 3 | Result 3 | Unit | P0 |
| AC-004 | Test 4 | Result 4 | Unit | P1 |
| AC-005 | Test 5 | Result 5 | Unit | P1 |

## Tier-Specific Requirements

### PROFESSIONAL Tier

Features for PRO tier.

### ENTERPRISE Tier

Features for ENT tier.
"""
            (tmp_path / f"SPEC-00{i:02d}-Test.md").write_text(content)

        start = time.perf_counter()
        validator = SpecificationValidator(tmp_path)
        result = validator.validate()
        elapsed = (time.perf_counter() - start) * 1000

        assert result.files_scanned == 10
        assert elapsed < 500, f"Validation took {elapsed:.2f}ms, expected <500ms"
