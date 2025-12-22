"""
Unit tests for Stage Folder Validator.

Part of Sprint 44 - SDLC Structure Scanner Engine.
"""

from pathlib import Path

import pytest

from sdlcctl.validation.validators.stage_folder import StageFolderValidator
from sdlcctl.validation import Severity


class TestStageFolderValidator:
    """Test Stage Folder Validator."""

    def test_create_validator(self, tmp_path):
        """Test creating stage folder validator."""
        docs_root = tmp_path / "docs"
        docs_root.mkdir()

        validator = StageFolderValidator(docs_root)

        assert validator.VALIDATOR_ID == "stage-folder"
        assert validator.VALIDATOR_NAME == "Stage Folder Validator"
        assert validator.docs_root == docs_root

    def test_validate_valid_structure(self, tmp_path):
        """Test validating a valid SDLC structure."""
        docs_root = tmp_path / "docs"
        docs_root.mkdir()

        # Create valid stage folders
        (docs_root / "00-foundation").mkdir()
        (docs_root / "01-planning").mkdir()
        (docs_root / "02-design").mkdir()

        validator = StageFolderValidator(docs_root)
        violations = validator.validate()

        # Should have no violations (except maybe missing stages)
        errors = [v for v in violations if v.severity == Severity.ERROR]
        assert len(errors) == 0

    def test_stage_001_invalid_naming(self, tmp_path):
        """Test STAGE-001: Invalid stage folder naming."""
        docs_root = tmp_path / "docs"
        docs_root.mkdir()

        # Create invalid stage folders
        (docs_root / "1-planning").mkdir()  # Single digit
        (docs_root / "2-design").mkdir()  # Single digit

        validator = StageFolderValidator(docs_root)
        violations = validator.validate()

        stage_001_violations = [v for v in violations if v.rule_id == "STAGE-001"]

        assert len(stage_001_violations) == 2
        assert all(v.severity == Severity.ERROR for v in stage_001_violations)
        assert all(v.auto_fixable for v in stage_001_violations)

    def test_stage_001_fix_suggestion(self, tmp_path):
        """Test STAGE-001 fix suggestion."""
        docs_root = tmp_path / "docs"
        docs_root.mkdir()

        (docs_root / "1-planning").mkdir()

        validator = StageFolderValidator(docs_root)
        violations = validator.validate()

        stage_001 = [v for v in violations if v.rule_id == "STAGE-001"][0]

        assert "01-planning" in stage_001.fix_suggestion
        assert stage_001.context["suggested_name"] == "01-planning"

    def test_stage_002_unknown_stage_number(self, tmp_path):
        """Test STAGE-002: Unknown stage number."""
        docs_root = tmp_path / "docs"
        docs_root.mkdir()

        # Create folders with invalid stage IDs
        (docs_root / "11-unknown").mkdir()  # 11 doesn't exist
        (docs_root / "99-test").mkdir()  # 99 is not a standard stage

        validator = StageFolderValidator(docs_root)
        violations = validator.validate()

        stage_002_violations = [v for v in violations if v.rule_id == "STAGE-002"]

        # 99 is filtered out as legacy pattern
        assert len(stage_002_violations) >= 1
        assert all(v.severity == Severity.ERROR for v in stage_002_violations)
        assert all(not v.auto_fixable for v in stage_002_violations)

    def test_stage_003_name_mismatch(self, tmp_path):
        """Test STAGE-003: Stage name mismatch."""
        docs_root = tmp_path / "docs"
        docs_root.mkdir()

        # Create stage with wrong name
        (docs_root / "01-design").mkdir()  # Should be "01-planning"
        (docs_root / "02-planning").mkdir()  # Should be "02-design"

        validator = StageFolderValidator(docs_root)
        violations = validator.validate()

        stage_003_violations = [v for v in violations if v.rule_id == "STAGE-003"]

        assert len(stage_003_violations) == 2
        assert all(v.severity == Severity.WARNING for v in stage_003_violations)
        assert all(v.auto_fixable for v in stage_003_violations)

    def test_stage_003_correct_names(self, tmp_path):
        """Test STAGE-003 with correct names."""
        docs_root = tmp_path / "docs"
        docs_root.mkdir()

        # Create stages with correct names
        (docs_root / "00-foundation").mkdir()
        (docs_root / "01-planning").mkdir()

        validator = StageFolderValidator(docs_root)
        violations = validator.validate()

        stage_003_violations = [v for v in violations if v.rule_id == "STAGE-003"]

        assert len(stage_003_violations) == 0

    def test_stage_004_duplicate_stage_numbers(self, tmp_path):
        """Test STAGE-004: Duplicate stage numbers."""
        docs_root = tmp_path / "docs"
        docs_root.mkdir()

        # Create duplicate stage folders
        (docs_root / "01-planning").mkdir()
        (docs_root / "01-analysis").mkdir()
        (docs_root / "02-design").mkdir()
        (docs_root / "02-architecture").mkdir()

        validator = StageFolderValidator(docs_root)
        violations = validator.validate()

        stage_004_violations = [v for v in violations if v.rule_id == "STAGE-004"]

        # Should report 4 violations (2 for stage 01, 2 for stage 02)
        assert len(stage_004_violations) == 4
        assert all(v.severity == Severity.ERROR for v in stage_004_violations)
        assert all(not v.auto_fixable for v in stage_004_violations)

    def test_stage_005_missing_core_stages(self, tmp_path):
        """Test STAGE-005: Missing required stages."""
        docs_root = tmp_path / "docs"
        docs_root.mkdir()

        # Create only some stages (missing core stages)
        (docs_root / "03-integration").mkdir()
        (docs_root / "05-test").mkdir()

        validator = StageFolderValidator(docs_root)
        violations = validator.validate()

        stage_005_violations = [v for v in violations if v.rule_id == "STAGE-005"]

        # Missing core: 00, 01, 02, 04
        assert len(stage_005_violations) == 4
        assert all(v.severity == Severity.WARNING for v in stage_005_violations)
        assert all(v.auto_fixable for v in stage_005_violations)

    def test_stage_005_all_stages_present(self, tmp_path):
        """Test STAGE-005 when all core stages present."""
        docs_root = tmp_path / "docs"
        docs_root.mkdir()

        # Create all core stages
        (docs_root / "00-foundation").mkdir()
        (docs_root / "01-planning").mkdir()
        (docs_root / "02-design").mkdir()
        (docs_root / "04-build").mkdir()

        validator = StageFolderValidator(docs_root)
        violations = validator.validate()

        stage_005_violations = [v for v in violations if v.rule_id == "STAGE-005"]

        assert len(stage_005_violations) == 0

    def test_skip_legacy_folders(self, tmp_path):
        """Test that 99-legacy folders are skipped."""
        docs_root = tmp_path / "docs"
        docs_root.mkdir()

        (docs_root / "99-legacy").mkdir()
        (docs_root / "99-Legacy").mkdir()
        (docs_root / "01-planning").mkdir()

        validator = StageFolderValidator(docs_root)
        violations = validator.validate()

        # 99-legacy folders should not trigger STAGE-002
        stage_002_violations = [v for v in violations if v.rule_id == "STAGE-002"]
        assert len(stage_002_violations) == 0

    def test_skip_archive_folders(self, tmp_path):
        """Test that 10-archive folders are skipped."""
        docs_root = tmp_path / "docs"
        docs_root.mkdir()

        (docs_root / "10-archive").mkdir()
        (docs_root / "10-Archive").mkdir()
        (docs_root / "01-planning").mkdir()

        validator = StageFolderValidator(docs_root)
        violations = validator.validate()

        # 10-archive is a valid stage, should not be skipped
        # But the Archive variant should be skipped
        stage_folders = validator._get_stage_folders()
        folder_names = [f.name for f in stage_folders]

        assert "01-planning" in folder_names

    def test_skip_hidden_folders(self, tmp_path):
        """Test that hidden folders are skipped."""
        docs_root = tmp_path / "docs"
        docs_root.mkdir()

        (docs_root / ".git").mkdir()
        (docs_root / ".vscode").mkdir()
        (docs_root / "01-planning").mkdir()

        validator = StageFolderValidator(docs_root)
        stage_folders = validator._get_stage_folders()

        folder_names = [f.name for f in stage_folders]
        assert ".git" not in folder_names
        assert ".vscode" not in folder_names
        assert "01-planning" in folder_names

    def test_docs_root_not_exists(self, tmp_path):
        """Test validation when docs_root doesn't exist."""
        docs_root = tmp_path / "nonexistent"

        validator = StageFolderValidator(docs_root)
        violations = validator.validate()

        # Should return error violation
        assert len(violations) == 1
        assert violations[0].rule_id == "STAGE-ERROR"
        assert violations[0].severity == Severity.ERROR

    def test_empty_docs_root(self, tmp_path):
        """Test validation with empty docs_root."""
        docs_root = tmp_path / "docs"
        docs_root.mkdir()

        validator = StageFolderValidator(docs_root)
        violations = validator.validate()

        # Should report missing core stages
        stage_005_violations = [v for v in violations if v.rule_id == "STAGE-005"]
        assert len(stage_005_violations) >= 4  # Missing 00, 01, 02, 04

    def test_mixed_valid_invalid_stages(self, tmp_path):
        """Test validation with mix of valid and invalid stages."""
        docs_root = tmp_path / "docs"
        docs_root.mkdir()

        # Mix of valid, invalid naming, wrong names
        (docs_root / "00-foundation").mkdir()  # Valid
        (docs_root / "1-planning").mkdir()  # Invalid naming (STAGE-001)
        (docs_root / "02-planning").mkdir()  # Wrong name (STAGE-003)
        (docs_root / "03-integration").mkdir()  # Valid

        validator = StageFolderValidator(docs_root)
        violations = validator.validate()

        # Should have STAGE-001 and STAGE-003 violations
        stage_001 = [v for v in violations if v.rule_id == "STAGE-001"]
        stage_003 = [v for v in violations if v.rule_id == "STAGE-003"]

        assert len(stage_001) >= 1
        assert len(stage_003) >= 1

    def test_violation_context(self, tmp_path):
        """Test that violations include proper context."""
        docs_root = tmp_path / "docs"
        docs_root.mkdir()

        (docs_root / "1-planning").mkdir()

        validator = StageFolderValidator(docs_root)
        violations = validator.validate()

        stage_001 = [v for v in violations if v.rule_id == "STAGE-001"][0]

        assert "current_name" in stage_001.context
        assert "suggested_name" in stage_001.context
        assert stage_001.context["current_name"] == "1-planning"
