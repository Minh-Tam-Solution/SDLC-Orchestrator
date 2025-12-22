"""
Unit tests for Sequential Numbering Validator.

Part of Sprint 44 - SDLC Structure Scanner Engine.
"""

from pathlib import Path

import pytest

from sdlcctl.validation.validators.sequential_numbering import (
    SequentialNumberingValidator,
)
from sdlcctl.validation import Severity


class TestSequentialNumberingValidator:
    """Test Sequential Numbering Validator."""

    def test_create_validator(self, tmp_path):
        """Test creating sequential numbering validator."""
        docs_root = tmp_path / "docs"
        docs_root.mkdir()

        validator = SequentialNumberingValidator(docs_root)

        assert validator.VALIDATOR_ID == "sequential-numbering"
        assert validator.VALIDATOR_NAME == "Sequential Numbering Validator"
        assert validator.docs_root == docs_root

    def test_validate_valid_numbering(self, tmp_path):
        """Test validating valid sequential numbering."""
        docs_root = tmp_path / "docs"
        docs_root.mkdir()

        stage = docs_root / "01-planning"
        stage.mkdir()

        # Create properly numbered subfolders
        (stage / "01-requirements").mkdir()
        (stage / "02-analysis").mkdir()
        (stage / "03-specification").mkdir()

        validator = SequentialNumberingValidator(docs_root)
        violations = validator.validate()

        # No violations for valid structure
        assert len(violations) == 0

    def test_num_001_duplicate_numbering(self, tmp_path):
        """Test NUM-001: Duplicate numbering."""
        docs_root = tmp_path / "docs"
        docs_root.mkdir()

        stage = docs_root / "01-planning"
        stage.mkdir()

        # Create duplicate numbers
        (stage / "01-requirements").mkdir()
        (stage / "01-analysis").mkdir()  # Duplicate 01
        (stage / "02-design").mkdir()
        (stage / "02-architecture").mkdir()  # Duplicate 02

        validator = SequentialNumberingValidator(docs_root)
        violations = validator.validate()

        num_001_violations = [v for v in violations if v.rule_id == "NUM-001"]

        # Should report 2 violations (one for each duplicate number)
        assert len(num_001_violations) == 2
        assert all(v.severity == Severity.ERROR for v in num_001_violations)
        assert all(not v.auto_fixable for v in num_001_violations)

    def test_num_001_context(self, tmp_path):
        """Test NUM-001 violation context."""
        docs_root = tmp_path / "docs"
        docs_root.mkdir()

        stage = docs_root / "01-planning"
        stage.mkdir()

        (stage / "01-doc1").mkdir()
        (stage / "01-doc2").mkdir()
        (stage / "01-doc3").mkdir()

        validator = SequentialNumberingValidator(docs_root)
        violations = validator.validate()

        num_001 = [v for v in violations if v.rule_id == "NUM-001"][0]

        assert "duplicate_number" in num_001.context
        assert "duplicate_count" in num_001.context
        assert num_001.context["duplicate_count"] == 3
        assert num_001.context["duplicate_number"] == "01"

    def test_num_002_sequence_gaps(self, tmp_path):
        """Test NUM-002: Non-sequential numbering (gaps)."""
        docs_root = tmp_path / "docs"
        docs_root.mkdir()

        stage = docs_root / "01-planning"
        stage.mkdir()

        # Create gaps in sequence
        (stage / "01-doc1").mkdir()
        (stage / "03-doc3").mkdir()  # Missing 02
        (stage / "05-doc5").mkdir()  # Missing 04

        validator = SequentialNumberingValidator(docs_root)
        violations = validator.validate()

        num_002_violations = [v for v in violations if v.rule_id == "NUM-002"]

        assert len(num_002_violations) == 1
        assert num_002_violations[0].severity == Severity.INFO
        assert num_002_violations[0].auto_fixable is True

    def test_num_002_missing_numbers(self, tmp_path):
        """Test NUM-002 identifies missing numbers."""
        docs_root = tmp_path / "docs"
        docs_root.mkdir()

        stage = docs_root / "01-planning"
        stage.mkdir()

        (stage / "01-doc").mkdir()
        (stage / "04-doc").mkdir()  # Missing 02, 03

        validator = SequentialNumberingValidator(docs_root)
        violations = validator.validate()

        num_002 = [v for v in violations if v.rule_id == "NUM-002"][0]

        assert "missing_numbers" in num_002.context
        missing = num_002.context["missing_numbers"]
        assert "02" in missing
        assert "03" in missing

    def test_num_002_no_gaps(self, tmp_path):
        """Test NUM-002 with no gaps."""
        docs_root = tmp_path / "docs"
        docs_root.mkdir()

        stage = docs_root / "01-planning"
        stage.mkdir()

        (stage / "01-doc").mkdir()
        (stage / "02-doc").mkdir()
        (stage / "03-doc").mkdir()

        validator = SequentialNumberingValidator(docs_root)
        violations = validator.validate()

        num_002_violations = [v for v in violations if v.rule_id == "NUM-002"]

        assert len(num_002_violations) == 0

    def test_num_003_invalid_format_single_digit(self, tmp_path):
        """Test NUM-003: Invalid format (single digit)."""
        docs_root = tmp_path / "docs"
        docs_root.mkdir()

        stage = docs_root / "01-planning"
        stage.mkdir()

        # Create single-digit prefixes
        (stage / "1-doc").mkdir()
        (stage / "2-doc").mkdir()

        validator = SequentialNumberingValidator(docs_root)
        violations = validator.validate()

        num_003_violations = [v for v in violations if v.rule_id == "NUM-003"]

        assert len(num_003_violations) == 2
        assert all(v.severity == Severity.WARNING for v in num_003_violations)
        assert all(v.auto_fixable for v in num_003_violations)

    def test_num_003_fix_suggestion(self, tmp_path):
        """Test NUM-003 fix suggestion."""
        docs_root = tmp_path / "docs"
        docs_root.mkdir()

        stage = docs_root / "01-planning"
        stage.mkdir()

        (stage / "1-doc").mkdir()

        validator = SequentialNumberingValidator(docs_root)
        violations = validator.validate()

        num_003 = [v for v in violations if v.rule_id == "NUM-003"][0]

        assert "01-doc" in num_003.fix_suggestion
        assert num_003.context["suggested_prefix"] == "01"

    def test_num_003_three_digit_prefix(self, tmp_path):
        """Test NUM-003 with 3-digit prefix."""
        docs_root = tmp_path / "docs"
        docs_root.mkdir()

        stage = docs_root / "01-planning"
        stage.mkdir()

        (stage / "001-doc").mkdir()

        validator = SequentialNumberingValidator(docs_root)
        violations = validator.validate()

        num_003 = [v for v in violations if v.rule_id == "NUM-003"][0]

        # Should suggest last 2 digits
        assert num_003.context["suggested_prefix"] == "01"

    def test_multiple_stages(self, tmp_path):
        """Test validation across multiple stages."""
        docs_root = tmp_path / "docs"
        docs_root.mkdir()

        # Stage 1 with duplicates
        stage1 = docs_root / "01-planning"
        stage1.mkdir()
        (stage1 / "01-doc1").mkdir()
        (stage1 / "01-doc2").mkdir()

        # Stage 2 with gaps
        stage2 = docs_root / "02-design"
        stage2.mkdir()
        (stage2 / "01-doc").mkdir()
        (stage2 / "03-doc").mkdir()

        validator = SequentialNumberingValidator(docs_root)
        violations = validator.validate()

        # Should have violations from both stages
        num_001 = [v for v in violations if v.rule_id == "NUM-001"]
        num_002 = [v for v in violations if v.rule_id == "NUM-002"]

        assert len(num_001) >= 1  # From stage1
        assert len(num_002) >= 1  # From stage2

    def test_skip_legacy_folders(self, tmp_path):
        """Test that 99-legacy folders are skipped."""
        docs_root = tmp_path / "docs"
        docs_root.mkdir()

        stage = docs_root / "01-planning"
        stage.mkdir()

        (stage / "99-legacy").mkdir()  # Should be skipped
        (stage / "01-doc").mkdir()

        validator = SequentialNumberingValidator(docs_root)
        violations = validator.validate()

        # 99-legacy should not cause violations
        assert len(violations) == 0

    def test_skip_hidden_items(self, tmp_path):
        """Test that hidden items are skipped."""
        docs_root = tmp_path / "docs"
        docs_root.mkdir()

        stage = docs_root / "01-planning"
        stage.mkdir()

        (stage / ".git").mkdir()  # Hidden folder
        (stage / "01-doc").mkdir()

        validator = SequentialNumberingValidator(docs_root)
        violations = validator.validate()

        # Hidden folders should not cause violations
        assert len(violations) == 0

    def test_mixed_files_and_folders(self, tmp_path):
        """Test validation with both files and folders."""
        docs_root = tmp_path / "docs"
        docs_root.mkdir()

        stage = docs_root / "01-planning"
        stage.mkdir()

        (stage / "01-requirements").mkdir()
        (stage / "02-analysis.md").write_text("# Analysis")
        (stage / "03-design").mkdir()

        validator = SequentialNumberingValidator(docs_root)
        violations = validator.validate()

        # No violations for valid structure
        assert len(violations) == 0

    def test_empty_stage(self, tmp_path):
        """Test validation with empty stage folder."""
        docs_root = tmp_path / "docs"
        docs_root.mkdir()

        stage = docs_root / "01-planning"
        stage.mkdir()

        validator = SequentialNumberingValidator(docs_root)
        violations = validator.validate()

        # No violations for empty stage
        assert len(violations) == 0

    def test_single_item_no_sequence_check(self, tmp_path):
        """Test that single item doesn't trigger sequence gap check."""
        docs_root = tmp_path / "docs"
        docs_root.mkdir()

        stage = docs_root / "01-planning"
        stage.mkdir()

        (stage / "05-doc").mkdir()  # Only one item, no gap check

        validator = SequentialNumberingValidator(docs_root)
        violations = validator.validate()

        num_002_violations = [v for v in violations if v.rule_id == "NUM-002"]

        # Should not report gaps for single item
        assert len(num_002_violations) == 0

    def test_docs_root_not_exists(self, tmp_path):
        """Test validation when docs_root doesn't exist."""
        docs_root = tmp_path / "nonexistent"

        validator = SequentialNumberingValidator(docs_root)
        violations = validator.validate()

        # Should return empty list, not crash
        assert violations == []

    def test_complex_scenario(self, tmp_path):
        """Test complex scenario with multiple violation types."""
        docs_root = tmp_path / "docs"
        docs_root.mkdir()

        stage = docs_root / "01-planning"
        stage.mkdir()

        # Mix of violations
        (stage / "01-doc1").mkdir()
        (stage / "01-doc2").mkdir()  # Duplicate (NUM-001)
        (stage / "2-doc").mkdir()  # Wrong format (NUM-003)
        (stage / "04-doc").mkdir()  # Gap: missing 03 (NUM-002)

        validator = SequentialNumberingValidator(docs_root)
        violations = validator.validate()

        # Should have all three types of violations
        num_001 = [v for v in violations if v.rule_id == "NUM-001"]
        num_002 = [v for v in violations if v.rule_id == "NUM-002"]
        num_003 = [v for v in violations if v.rule_id == "NUM-003"]

        assert len(num_001) >= 1
        assert len(num_002) >= 1
        assert len(num_003) >= 1
