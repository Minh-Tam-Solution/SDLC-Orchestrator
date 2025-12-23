"""
Unit tests for Cross-Reference Validator.

Part of Sprint 44 - SDLC Structure Scanner Engine.
"""

from pathlib import Path

import pytest

from sdlcctl.validation.validators.cross_reference import CrossReferenceValidator
from sdlcctl.validation import Severity


class TestCrossReferenceValidator:
    """Test Cross-Reference Validator."""

    def test_create_validator(self, tmp_path):
        """Test creating cross-reference validator."""
        docs_root = tmp_path / "docs"
        docs_root.mkdir()

        validator = CrossReferenceValidator(docs_root)

        assert validator.VALIDATOR_ID == "cross-reference"
        assert validator.VALIDATOR_NAME == "Cross-Reference Validator"
        assert validator.docs_root == docs_root

    def test_valid_structure_no_violations(self, tmp_path):
        """Test valid structure with proper cross-references."""
        docs_root = tmp_path / "docs"
        docs_root.mkdir()

        # Create stage folders
        stage1 = docs_root / "01-planning"
        stage1.mkdir()

        # Create files with valid references
        doc1 = stage1 / "overview.md"
        doc2 = stage1 / "details.md"

        doc1.write_text(
            "# Overview\n\n"
            "[See details](./details.md)\n"
        )
        doc2.write_text("# Details\n\nSome content")

        validator = CrossReferenceValidator(docs_root)
        violations = validator.validate()

        # Should have SCANNER-001 health report only
        scanner_violations = [v for v in violations if v.rule_id == "SCANNER-001"]
        assert len(scanner_violations) == 1
        assert scanner_violations[0].context["health_status"] == "HEALTHY"

        # No broken links or orphaned files
        ref_001 = [v for v in violations if v.rule_id == "REF-001"]
        ref_002 = [v for v in violations if v.rule_id == "REF-002"]
        assert len(ref_001) == 0
        assert len(ref_002) == 0

    def test_ref_001_broken_link(self, tmp_path):
        """Test REF-001: Broken link detection."""
        docs_root = tmp_path / "docs"
        docs_root.mkdir()

        stage = docs_root / "01-planning"
        stage.mkdir()

        # Create file with broken link
        doc = stage / "overview.md"
        doc.write_text(
            "# Overview\n\n"
            "[Broken link](./non-existent-file.md)\n"
            "[Another broken](../02-design/missing.md)\n"
        )

        validator = CrossReferenceValidator(docs_root)
        violations = validator.validate()

        ref_001 = [v for v in violations if v.rule_id == "REF-001"]
        assert len(ref_001) == 2
        assert all(v.severity == Severity.ERROR for v in ref_001)
        assert all(not v.auto_fixable for v in ref_001)

        # Check first violation
        assert "non-existent-file.md" in ref_001[0].message
        assert "line_number" in ref_001[0].context

    def test_ref_001_relative_path_resolution(self, tmp_path):
        """Test REF-001: Relative path resolution."""
        docs_root = tmp_path / "docs"
        docs_root.mkdir()

        stage1 = docs_root / "01-planning"
        stage2 = docs_root / "02-design"
        stage1.mkdir()
        stage2.mkdir()

        # Create files
        doc1 = stage1 / "overview.md"
        doc2 = stage2 / "architecture.md"

        # Valid relative link
        doc1.write_text(
            "# Overview\n\n"
            "[Architecture](../02-design/architecture.md)\n"
        )
        doc2.write_text("# Architecture")

        validator = CrossReferenceValidator(docs_root)
        violations = validator.validate()

        # No broken links
        ref_001 = [v for v in violations if v.rule_id == "REF-001"]
        assert len(ref_001) == 0

    def test_ref_001_skip_external_links(self, tmp_path):
        """Test REF-001: Skip external links (http, https, mailto)."""
        docs_root = tmp_path / "docs"
        docs_root.mkdir()

        stage = docs_root / "01-planning"
        stage.mkdir()

        doc = stage / "overview.md"
        doc.write_text(
            "# Overview\n\n"
            "[External](https://example.com)\n"
            "[Email](mailto:test@example.com)\n"
            "[FTP](ftp://ftp.example.com)\n"
        )

        validator = CrossReferenceValidator(docs_root)
        violations = validator.validate()

        # External links should not trigger violations
        ref_001 = [v for v in violations if v.rule_id == "REF-001"]
        assert len(ref_001) == 0

    def test_ref_001_skip_anchor_only_links(self, tmp_path):
        """Test REF-001: Skip anchor-only links (#section)."""
        docs_root = tmp_path / "docs"
        docs_root.mkdir()

        stage = docs_root / "01-planning"
        stage.mkdir()

        doc = stage / "overview.md"
        doc.write_text(
            "# Overview\n\n"
            "[Section 1](#section-1)\n"
            "[Section 2](#another-section)\n"
        )

        validator = CrossReferenceValidator(docs_root)
        violations = validator.validate()

        # Anchor-only links should not trigger violations
        ref_001 = [v for v in violations if v.rule_id == "REF-001"]
        assert len(ref_001) == 0

    def test_ref_001_handle_anchors_in_links(self, tmp_path):
        """Test REF-001: Handle links with anchors (file.md#section)."""
        docs_root = tmp_path / "docs"
        docs_root.mkdir()

        stage = docs_root / "01-planning"
        stage.mkdir()

        doc1 = stage / "overview.md"
        doc2 = stage / "details.md"

        # Link with anchor
        doc1.write_text(
            "# Overview\n\n"
            "[Details section](./details.md#implementation)\n"
        )
        doc2.write_text("# Details\n\n## Implementation")

        validator = CrossReferenceValidator(docs_root)
        violations = validator.validate()

        # Should validate file exists (ignore anchor)
        ref_001 = [v for v in violations if v.rule_id == "REF-001"]
        assert len(ref_001) == 0

    def test_ref_002_orphaned_file(self, tmp_path):
        """Test REF-002: Orphaned file detection."""
        docs_root = tmp_path / "docs"
        docs_root.mkdir()

        stage = docs_root / "01-planning"
        stage.mkdir()

        # Create orphaned file (not referenced)
        orphaned = stage / "orphaned.md"
        orphaned.write_text("# Orphaned\n\nNot referenced anywhere")

        # Create referenced file
        doc = stage / "overview.md"
        doc.write_text("# Overview")  # No links

        validator = CrossReferenceValidator(docs_root)
        violations = validator.validate()

        ref_002 = [v for v in violations if v.rule_id == "REF-002"]
        assert len(ref_002) == 2  # Both files are orphaned
        assert all(v.severity == Severity.WARNING for v in ref_002)
        assert all(not v.auto_fixable for v in ref_002)

        # Check context
        assert "file_path" in ref_002[0].context
        assert "file_size_bytes" in ref_002[0].context

    def test_ref_002_skip_readme_files(self, tmp_path):
        """Test REF-002: Skip README.md and index.md files."""
        docs_root = tmp_path / "docs"
        docs_root.mkdir()

        stage = docs_root / "01-planning"
        stage.mkdir()

        # Create README and index (should not be flagged as orphaned)
        (stage / "README.md").write_text("# README")
        (stage / "index.md").write_text("# Index")
        (docs_root / "README.md").write_text("# Root README")

        validator = CrossReferenceValidator(docs_root)
        violations = validator.validate()

        ref_002 = [v for v in violations if v.rule_id == "REF-002"]
        # README.md and index.md should not be flagged
        orphaned_names = [v.file_path.name for v in ref_002]
        assert "README.md" not in orphaned_names
        assert "readme.md" not in orphaned_names
        assert "index.md" not in orphaned_names
        assert "INDEX.md" not in orphaned_names

    def test_ref_002_only_markdown_files(self, tmp_path):
        """Test REF-002: Only flag orphaned markdown/text files."""
        docs_root = tmp_path / "docs"
        docs_root.mkdir()

        stage = docs_root / "01-planning"
        stage.mkdir()

        # Create various file types
        (stage / "orphaned.md").write_text("# Orphaned MD")
        (stage / "orphaned.txt").write_text("Orphaned TXT")
        (stage / "image.png").write_bytes(b"fake image")
        (stage / "script.py").write_text("print('hello')")

        validator = CrossReferenceValidator(docs_root)
        violations = validator.validate()

        ref_002 = [v for v in violations if v.rule_id == "REF-002"]
        orphaned_extensions = {v.file_path.suffix for v in ref_002}

        # Only .md and .txt should be flagged
        assert ".md" in orphaned_extensions
        assert ".txt" in orphaned_extensions
        assert ".png" not in orphaned_extensions
        assert ".py" not in orphaned_extensions

    def test_scanner_001_health_metrics(self, tmp_path):
        """Test SCANNER-001: Structure health metrics."""
        docs_root = tmp_path / "docs"
        docs_root.mkdir()

        stage = docs_root / "01-planning"
        stage.mkdir()

        # Create structure with some issues
        doc1 = stage / "overview.md"
        doc2 = stage / "details.md"
        orphaned = stage / "orphaned.md"

        doc1.write_text(
            "# Overview\n\n"
            "[Details](./details.md)\n"
            "[Broken](./missing.md)\n"
        )
        doc2.write_text("# Details")
        orphaned.write_text("# Orphaned")

        validator = CrossReferenceValidator(docs_root)
        violations = validator.validate()

        scanner_001 = [v for v in violations if v.rule_id == "SCANNER-001"]
        assert len(scanner_001) == 1

        health = scanner_001[0]
        assert "health_status" in health.context
        assert "total_files" in health.context
        assert "broken_links" in health.context
        assert "orphaned_files" in health.context
        assert "reference_density" in health.context

        # Check metrics
        assert health.context["total_files"] == 3
        assert health.context["broken_links"] == 1
        assert health.context["orphaned_files"] >= 1

    def test_scanner_001_healthy_status(self, tmp_path):
        """Test SCANNER-001: HEALTHY status for good structure."""
        docs_root = tmp_path / "docs"
        docs_root.mkdir()

        stage = docs_root / "01-planning"
        stage.mkdir()

        # Create healthy structure
        doc1 = stage / "overview.md"
        doc2 = stage / "details.md"

        doc1.write_text(
            "# Overview\n\n"
            "[Details](./details.md)\n"
        )
        doc2.write_text(
            "# Details\n\n"
            "[Overview](./overview.md)\n"
        )

        validator = CrossReferenceValidator(docs_root)
        violations = validator.validate()

        scanner_001 = [v for v in violations if v.rule_id == "SCANNER-001"]
        assert len(scanner_001) == 1
        assert scanner_001[0].context["health_status"] == "HEALTHY"
        assert scanner_001[0].context["broken_links"] == 0
        assert scanner_001[0].context["orphaned_files"] == 0

    def test_scanner_001_unhealthy_status(self, tmp_path):
        """Test SCANNER-001: UNHEALTHY status for problematic structure."""
        docs_root = tmp_path / "docs"
        docs_root.mkdir()

        stage = docs_root / "01-planning"
        stage.mkdir()

        # Create structure with many issues
        doc1 = stage / "overview.md"

        # Many broken links (>10%)
        broken_links = "\n".join([f"[Broken {i}](./missing{i}.md)" for i in range(10)])
        doc1.write_text(f"# Overview\n\n{broken_links}\n")

        # Many orphaned files (>20%)
        for i in range(15):
            (stage / f"orphaned{i}.md").write_text(f"# Orphaned {i}")

        validator = CrossReferenceValidator(docs_root)
        violations = validator.validate()

        scanner_001 = [v for v in violations if v.rule_id == "SCANNER-001"]
        assert len(scanner_001) == 1
        assert scanner_001[0].context["health_status"] in ["UNHEALTHY", "NEEDS ATTENTION"]
        assert scanner_001[0].severity in [Severity.WARNING, Severity.INFO]

    def test_skip_hidden_files(self, tmp_path):
        """Test that hidden files are skipped during scanning."""
        docs_root = tmp_path / "docs"
        docs_root.mkdir()

        stage = docs_root / "01-planning"
        stage.mkdir()

        # Create hidden file
        (stage / ".hidden.md").write_text("# Hidden")

        # Create git folder
        git_folder = stage / ".git"
        git_folder.mkdir()
        (git_folder / "config").write_text("git config")

        # Create normal file
        (stage / "normal.md").write_text("# Normal")

        validator = CrossReferenceValidator(docs_root)
        violations = validator.validate()

        scanner_001 = [v for v in violations if v.rule_id == "SCANNER-001"]
        assert len(scanner_001) == 1

        # Should only count normal file
        assert scanner_001[0].context["total_files"] == 1
        assert scanner_001[0].context["scannable_files"] == 1

    def test_skip_node_modules(self, tmp_path):
        """Test that node_modules is skipped during scanning."""
        docs_root = tmp_path / "docs"
        docs_root.mkdir()

        stage = docs_root / "01-planning"
        stage.mkdir()

        # Create node_modules
        node_modules = stage / "node_modules"
        node_modules.mkdir()
        (node_modules / "package.md").write_text("# Package")

        # Create normal file
        (stage / "normal.md").write_text("# Normal")

        validator = CrossReferenceValidator(docs_root)
        violations = validator.validate()

        scanner_001 = [v for v in violations if v.rule_id == "SCANNER-001"]
        assert len(scanner_001) == 1

        # Should only count normal file (skip node_modules)
        assert scanner_001[0].context["total_files"] == 1

    def test_docs_root_not_exists(self, tmp_path):
        """Test validation when docs_root doesn't exist."""
        docs_root = tmp_path / "nonexistent"

        validator = CrossReferenceValidator(docs_root)
        violations = validator.validate()

        # Should return error violation
        assert len(violations) == 1
        assert violations[0].rule_id == "SCANNER-ERROR"
        assert violations[0].severity == Severity.ERROR

    def test_complex_reference_graph(self, tmp_path):
        """Test complex cross-reference graph."""
        docs_root = tmp_path / "docs"
        docs_root.mkdir()

        stage1 = docs_root / "01-planning"
        stage2 = docs_root / "02-design"
        stage1.mkdir()
        stage2.mkdir()

        # Create complex reference graph
        doc1 = stage1 / "overview.md"
        doc2 = stage1 / "requirements.md"
        doc3 = stage2 / "architecture.md"
        doc4 = stage2 / "api-spec.md"

        doc1.write_text(
            "# Overview\n\n"
            "[Requirements](./requirements.md)\n"
            "[Architecture](../02-design/architecture.md)\n"
        )
        doc2.write_text(
            "# Requirements\n\n"
            "[API Spec](../02-design/api-spec.md)\n"
        )
        doc3.write_text(
            "# Architecture\n\n"
            "[Overview](../01-planning/overview.md)\n"
            "[API Spec](./api-spec.md)\n"
        )
        doc4.write_text("# API Spec")

        validator = CrossReferenceValidator(docs_root)
        violations = validator.validate()

        # No broken links
        ref_001 = [v for v in violations if v.rule_id == "REF-001"]
        assert len(ref_001) == 0

        # No orphaned files (all are cross-referenced)
        ref_002 = [v for v in violations if v.rule_id == "REF-002"]
        assert len(ref_002) == 0

        # Healthy structure
        scanner_001 = [v for v in violations if v.rule_id == "SCANNER-001"]
        assert len(scanner_001) == 1
        assert scanner_001[0].context["health_status"] == "HEALTHY"

    def test_unicode_handling(self, tmp_path):
        """Test handling of Unicode file names and content."""
        docs_root = tmp_path / "docs"
        docs_root.mkdir()

        stage = docs_root / "01-planning"
        stage.mkdir()

        # Create files with Unicode
        doc1 = stage / "overview.md"
        doc2 = stage / "tiếng-việt.md"

        doc1.write_text(
            "# Overview\n\n"
            "[Tiếng Việt](./tiếng-việt.md)\n",
            encoding='utf-8'
        )
        doc2.write_text("# Tiếng Việt\n\nNội dung tiếng Việt", encoding='utf-8')

        validator = CrossReferenceValidator(docs_root)
        violations = validator.validate()

        # Should handle Unicode correctly
        ref_001 = [v for v in violations if v.rule_id == "REF-001"]
        assert len(ref_001) == 0
