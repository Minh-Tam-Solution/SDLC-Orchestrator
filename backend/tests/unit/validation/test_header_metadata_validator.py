"""Unit tests for Header Metadata Validator - Sprint 44 Day 4."""
from pathlib import Path
import pytest
from sdlcctl.validation.validators.header_metadata import HeaderMetadataValidator
from sdlcctl.validation import Severity

class TestHeaderMetadataValidator:
    """Test Header Metadata Validator."""
    
    def test_create_validator(self, tmp_path):
        docs = tmp_path / "docs"
        docs.mkdir()
        validator = HeaderMetadataValidator(docs)
        assert validator.VALIDATOR_ID == "header-metadata"
    
    def test_valid_yaml_frontmatter(self, tmp_path):
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "test.md").write_text("""---
Framework: SDLC 5.1.1
Sprint: 44
Epic: EP-04
---
# Content""")
        validator = HeaderMetadataValidator(docs)
        violations = validator.validate()
        assert len(violations) == 0
    
    def test_hdr_001_missing_fields(self, tmp_path):
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "test.md").write_text("# No headers")
        validator = HeaderMetadataValidator(docs)
        violations = validator.validate()
        hdr_001 = [v for v in violations if v.rule_id == "HDR-001"]
        assert len(hdr_001) >= 1
        assert hdr_001[0].severity == Severity.WARNING
        assert hdr_001[0].auto_fixable
    
    def test_hdr_002_invalid_format(self, tmp_path):
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "test.md").write_text("""---
Framework: InvalidFormat
Sprint: 44
Epic: EP-04
---
# Content""")
        validator = HeaderMetadataValidator(docs)
        violations = validator.validate()
        hdr_002 = [v for v in violations if v.rule_id == "HDR-002"]
        assert len(hdr_002) >= 1
    
    def test_parse_yaml_frontmatter(self, tmp_path):
        docs = tmp_path / "docs"
        docs.mkdir()
        validator = HeaderMetadataValidator(docs)
        content = """---
Framework: SDLC 5.1.1
Sprint: 44
---
# Content"""
        headers = validator._parse_yaml_frontmatter(content)
        assert headers["Framework"] == "SDLC 5.1.1"
        assert headers["Sprint"] == "44"
    
    def test_parse_markdown_headers(self, tmp_path):
        docs = tmp_path / "docs"
        docs.mkdir()
        validator = HeaderMetadataValidator(docs)
        content = """## Framework: SDLC 5.1.1
## Sprint: 44
# Content"""
        headers = validator._parse_markdown_headers(content)
        assert headers["Framework"] == "SDLC 5.1.1"
