"""Unit tests for Naming Convention Validator - Sprint 44 Day 4."""
from pathlib import Path
import pytest
from sdlcctl.validation.validators.naming_convention import NamingConventionValidator
from sdlcctl.validation import Severity

class TestNamingConventionValidator:
    """Test Naming Convention Validator."""
    
    def test_create_validator(self, tmp_path):
        docs_root = tmp_path / "docs"
        docs_root.mkdir()
        validator = NamingConventionValidator(docs_root)
        assert validator.VALIDATOR_ID == "naming-convention"
    
    def test_valid_kebab_case(self, tmp_path):
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "user-guide.md").write_text("# Guide")
        (docs / "api-reference.md").write_text("# API")
        validator = NamingConventionValidator(docs)
        violations = validator.validate()
        assert len(violations) == 0
    
    def test_name_001_spaces(self, tmp_path):
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "User Guide.md").write_text("# Guide")
        validator = NamingConventionValidator(docs)
        violations = validator.validate()
        name_001 = [v for v in violations if v.rule_id == "NAME-001"]
        assert len(name_001) == 1
        assert name_001[0].severity == Severity.WARNING
        assert name_001[0].auto_fixable
        assert "user-guide.md" in name_001[0].fix_suggestion
    
    def test_name_001_underscores(self, tmp_path):
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "user_guide.md").write_text("# Guide")
        validator = NamingConventionValidator(docs)
        violations = validator.validate()
        name_001 = [v for v in violations if v.rule_id == "NAME-001"]
        assert len(name_001) >= 1
    
    def test_name_002_uppercase(self, tmp_path):
        """README.md is exempt from naming validation as a conventional entrypoint."""
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "README.md").write_text("# README")
        validator = NamingConventionValidator(docs)
        violations = validator.validate()
        # README.md is intentionally exempt from validation
        assert len(violations) == 0
    
    def test_name_002_camelcase(self, tmp_path):
        """CamelCase names are caught as NAME-001 (invalid chars) since uppercase is invalid."""
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "userGuide.md").write_text("# Guide")
        validator = NamingConventionValidator(docs)
        violations = validator.validate()
        # CamelCase is caught as invalid chars (NAME-001) because uppercase is invalid
        name_001 = [v for v in violations if v.rule_id == "NAME-001"]
        assert len(name_001) >= 1
    
    def test_numbering_prefix_ignored(self, tmp_path):
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "01-user-guide.md").write_text("# Guide")
        validator = NamingConventionValidator(docs)
        violations = validator.validate()
        assert len(violations) == 0
    
    def test_kebab_case_conversion(self, tmp_path):
        docs = tmp_path / "docs"
        docs.mkdir()
        validator = NamingConventionValidator(docs)
        assert validator._to_kebab_case("User Guide") == "user-guide"
        assert validator._to_kebab_case("userGuide") == "user-guide"
        assert validator._to_kebab_case("user_guide") == "user-guide"
        assert validator._to_kebab_case("USER_GUIDE") == "user-guide"
