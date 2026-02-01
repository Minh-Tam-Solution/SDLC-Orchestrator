"""
Unit tests for SpecFrontmatterValidator.

Tests YAML frontmatter validation for SDLC 6.0.0 specifications.
Part of Sprint 125 - Multi-Frontend Alignment.
"""

import tempfile
from pathlib import Path

import pytest

from sdlcctl.validation.validators.spec_frontmatter import SpecFrontmatterValidator


class TestSpecFrontmatterValidator:
    """Test suite for SpecFrontmatterValidator."""

    @pytest.fixture
    def temp_docs_dir(self):
        """Create a temporary docs directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            docs_root = Path(tmpdir)
            specs_dir = docs_root / "02-design" / "14-Technical-Specs"
            specs_dir.mkdir(parents=True)
            yield docs_root

    @pytest.fixture
    def validator(self, temp_docs_dir):
        """Create validator instance."""
        return SpecFrontmatterValidator(temp_docs_dir)

    def test_validator_attributes(self, validator):
        """Test validator has required attributes."""
        assert validator.VALIDATOR_ID == "spec-frontmatter"
        assert validator.VALIDATOR_NAME == "Specification Frontmatter Validator"
        assert "YAML frontmatter" in validator.VALIDATOR_DESCRIPTION

    def test_valid_frontmatter_passes(self, temp_docs_dir, validator):
        """Test that valid frontmatter passes validation."""
        spec_content = '''---
spec_id: SPEC-0001
title: "Test Specification Title"
version: "1.0.0"
status: APPROVED
tier:
  - LITE
  - STANDARD
  - PROFESSIONAL
  - ENTERPRISE
owner: "Test Owner"
last_updated: "2026-01-30"
---

# SPEC-0001: Test Specification

Content here.
'''
        spec_file = temp_docs_dir / "02-design" / "14-Technical-Specs" / "SPEC-0001-Test.md"
        spec_file.write_text(spec_content, encoding="utf-8")

        violations = validator.validate()
        assert len(violations) == 0, f"Expected no violations, got: {violations}"

    def test_missing_frontmatter_block_fails(self, temp_docs_dir, validator):
        """Test that missing frontmatter block creates SPC-004 violation."""
        spec_content = '''# SPEC-0002: Missing Frontmatter

This spec has no YAML frontmatter.
'''
        spec_file = temp_docs_dir / "02-design" / "14-Technical-Specs" / "SPEC-0002-NoFrontmatter.md"
        spec_file.write_text(spec_content, encoding="utf-8")

        violations = validator.validate()
        assert len(violations) == 1
        assert violations[0].rule_id == "SPC-004"
        assert "Missing YAML frontmatter" in violations[0].message

    def test_missing_required_fields_fails(self, temp_docs_dir, validator):
        """Test that missing required fields creates SPC-001 violation."""
        spec_content = '''---
spec_id: SPEC-0003
title: "Incomplete Spec"
---

# SPEC-0003: Incomplete

Missing required fields.
'''
        spec_file = temp_docs_dir / "02-design" / "14-Technical-Specs" / "SPEC-0003-Incomplete.md"
        spec_file.write_text(spec_content, encoding="utf-8")

        violations = validator.validate()
        # Should have violation for missing fields
        assert len(violations) >= 1
        missing_violation = next(
            (v for v in violations if v.rule_id in ("SPC-001", "SPC-002")), None
        )
        assert missing_violation is not None

    def test_invalid_spec_id_format_fails(self, temp_docs_dir, validator):
        """Test that invalid spec_id format creates SPC-002 violation."""
        spec_content = '''---
spec_id: INVALID-ID
title: "Invalid Spec ID"
version: "1.0.0"
status: APPROVED
tier:
  - LITE
owner: "Test"
last_updated: "2026-01-30"
---

# Invalid Spec
'''
        spec_file = temp_docs_dir / "02-design" / "14-Technical-Specs" / "SPEC-0004-InvalidID.md"
        spec_file.write_text(spec_content, encoding="utf-8")

        violations = validator.validate()
        assert len(violations) >= 1
        format_violation = next(
            (v for v in violations if "spec_id" in str(v.context) or "spec_id" in v.message.lower()),
            None
        )
        assert format_violation is not None

    def test_invalid_version_format_fails(self, temp_docs_dir, validator):
        """Test that invalid version format creates SPC-002 violation."""
        spec_content = '''---
spec_id: SPEC-0005
title: "Invalid Version"
version: "v1.0"
status: APPROVED
tier:
  - LITE
owner: "Test"
last_updated: "2026-01-30"
---

# Invalid Version
'''
        spec_file = temp_docs_dir / "02-design" / "14-Technical-Specs" / "SPEC-0005-BadVersion.md"
        spec_file.write_text(spec_content, encoding="utf-8")

        violations = validator.validate()
        assert len(violations) >= 1

    def test_invalid_status_value_fails(self, temp_docs_dir, validator):
        """Test that invalid status value creates SPC-002 violation."""
        spec_content = '''---
spec_id: SPEC-0006
title: "Invalid Status"
version: "1.0.0"
status: INVALID_STATUS
tier:
  - LITE
owner: "Test"
last_updated: "2026-01-30"
---

# Invalid Status
'''
        spec_file = temp_docs_dir / "02-design" / "14-Technical-Specs" / "SPEC-0006-BadStatus.md"
        spec_file.write_text(spec_content, encoding="utf-8")

        violations = validator.validate()
        assert len(violations) >= 1

    def test_invalid_tier_value_fails(self, temp_docs_dir, validator):
        """Test that invalid tier value creates SPC-002 violation."""
        spec_content = '''---
spec_id: SPEC-0007
title: "Invalid Tier"
version: "1.0.0"
status: APPROVED
tier:
  - INVALID_TIER
owner: "Test"
last_updated: "2026-01-30"
---

# Invalid Tier
'''
        spec_file = temp_docs_dir / "02-design" / "14-Technical-Specs" / "SPEC-0007-BadTier.md"
        spec_file.write_text(spec_content, encoding="utf-8")

        violations = validator.validate()
        assert len(violations) >= 1

    def test_invalid_date_format_fails(self, temp_docs_dir, validator):
        """Test that invalid date format creates SPC-002 violation."""
        spec_content = '''---
spec_id: SPEC-0008
title: "Invalid Date"
version: "1.0.0"
status: APPROVED
tier:
  - LITE
owner: "Test"
last_updated: "30-01-2026"
---

# Invalid Date
'''
        spec_file = temp_docs_dir / "02-design" / "14-Technical-Specs" / "SPEC-0008-BadDate.md"
        spec_file.write_text(spec_content, encoding="utf-8")

        violations = validator.validate()
        assert len(violations) >= 1

    def test_valid_with_optional_fields_passes(self, temp_docs_dir, validator):
        """Test that valid frontmatter with optional fields passes."""
        spec_content = '''---
spec_id: SPEC-0009
title: "Full Specification"
version: "2.1.0"
status: ACTIVE
tier:
  - PROFESSIONAL
  - ENTERPRISE
pillar:
  - "Pillar 7 - Quality Assurance"
owner: "Backend Team"
last_updated: "2026-01-30"
tags:
  - specification
  - validation
related_adrs:
  - ADR-001-Architecture
related_specs:
  - SPEC-0001
  - SPEC-0002
author: "Jane Developer"
created: "2025-12-01"
epic: "EP-06-Codegen"
sprint: 125
---

# SPEC-0009: Full Specification

Complete spec with all fields.
'''
        spec_file = temp_docs_dir / "02-design" / "14-Technical-Specs" / "SPEC-0009-Full.md"
        spec_file.write_text(spec_content, encoding="utf-8")

        violations = validator.validate()
        assert len(violations) == 0, f"Expected no violations, got: {violations}"

    def test_single_tier_string_passes(self, temp_docs_dir, validator):
        """Test that single tier as string (not array) passes."""
        spec_content = '''---
spec_id: SPEC-0010
title: "Single Tier Spec"
version: "1.0.0"
status: DRAFT
tier: LITE
owner: "Test"
last_updated: "2026-01-30"
---

# Single Tier
'''
        spec_file = temp_docs_dir / "02-design" / "14-Technical-Specs" / "SPEC-0010-SingleTier.md"
        spec_file.write_text(spec_content, encoding="utf-8")

        violations = validator.validate()
        assert len(violations) == 0, f"Expected no violations, got: {violations}"

    def test_skips_legacy_folder(self, temp_docs_dir, validator):
        """Test that files in 99-legacy folder are skipped."""
        legacy_dir = temp_docs_dir / "99-legacy"
        legacy_dir.mkdir(parents=True)

        spec_content = '''---
spec_id: INVALID
---

# Legacy spec (should be skipped)
'''
        spec_file = legacy_dir / "SPEC-0099-Legacy.md"
        spec_file.write_text(spec_content, encoding="utf-8")

        violations = validator.validate()
        # Should have no violations because legacy files are skipped
        legacy_violations = [v for v in violations if "99-legacy" in str(v.file_path)]
        assert len(legacy_violations) == 0

    def test_empty_docs_dir_returns_empty(self, temp_docs_dir, validator):
        """Test that empty docs directory returns no violations."""
        violations = validator.validate()
        assert len(violations) == 0

    def test_generates_frontmatter_template(self, validator):
        """Test frontmatter template generation."""
        test_file = Path("/test/SPEC-0123-MySpec.md")
        template = validator._generate_frontmatter_template(test_file)

        assert "spec_id: SPEC-0123" in template
        assert "title:" in template
        assert "version:" in template
        assert "status: DRAFT" in template
        assert "tier:" in template
        assert "owner:" in template
        assert "last_updated:" in template

    def test_field_suggestions(self, validator):
        """Test field suggestion generation."""
        suggestion = validator._get_field_suggestion("spec_id", {})
        assert "SPEC-" in suggestion

        suggestion = validator._get_field_suggestion("version", {})
        assert "1.0.0" in suggestion

        suggestion = validator._get_field_suggestion("status", {})
        assert "DRAFT" in suggestion or "APPROVED" in suggestion


class TestSpecFrontmatterValidatorWithSpecificPaths:
    """Test validator with specific file paths."""

    @pytest.fixture
    def temp_docs_dir(self):
        """Create a temporary docs directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            docs_root = Path(tmpdir)
            specs_dir = docs_root / "specs"
            specs_dir.mkdir(parents=True)
            yield docs_root

    def test_validate_specific_paths(self, temp_docs_dir):
        """Test validation of specific file paths."""
        validator = SpecFrontmatterValidator(temp_docs_dir)

        # Create two spec files - one valid, one invalid
        valid_content = '''---
spec_id: SPEC-0001
title: "Valid Spec"
version: "1.0.0"
status: APPROVED
tier:
  - LITE
owner: "Test"
last_updated: "2026-01-30"
---

# Valid
'''
        invalid_content = '''---
spec_id: BAD
---

# Invalid
'''
        valid_file = temp_docs_dir / "specs" / "SPEC-0001-Valid.md"
        invalid_file = temp_docs_dir / "specs" / "SPEC-0002-Invalid.md"

        valid_file.write_text(valid_content, encoding="utf-8")
        invalid_file.write_text(invalid_content, encoding="utf-8")

        # Validate only the valid file
        violations = validator.validate(paths=[valid_file])
        assert len(violations) == 0

        # Validate only the invalid file
        violations = validator.validate(paths=[invalid_file])
        assert len(violations) >= 1
