"""Stage 01 (Planning) ↔ Stage 02 (Design) consistency checker.

SDLC 6.0.5 - SPEC-0021 Stage Consistency Validation.

Validates:
- CONS-001: ADRs must reference Stage 01 requirements
- CONS-002: Design documents must cite specification IDs
- CONS-003: Architecture decisions must trace to user stories
"""

from pathlib import Path
from typing import List

from ...tier import Tier
from ...violation import Severity
from ..models import ConsistencyRule, ConsistencyViolation
from .base import BaseConsistencyChecker


class Stage01To02Checker(BaseConsistencyChecker):
    """Check consistency between Stage 01 (Planning) and Stage 02 (Design)."""

    @property
    def source_stage(self) -> str:
        return "01"

    @property
    def target_stage(self) -> str:
        return "02"

    def get_rules(self) -> List[ConsistencyRule]:
        """Return rules for Stage 01 ↔ Stage 02 consistency."""
        return [
            ConsistencyRule(
                rule_id="CONS-001",
                description="ADRs must reference Stage 01 requirements",
                source_stage="01",
                target_stage="02",
                default_severity=Severity.WARNING,
                tier_severity_override={
                    Tier.LITE: Severity.INFO,
                    Tier.STANDARD: Severity.WARNING,
                    Tier.PROFESSIONAL: Severity.ERROR,
                    Tier.ENTERPRISE: Severity.ERROR,
                },
            ),
            ConsistencyRule(
                rule_id="CONS-002",
                description="Design documents must cite specification IDs",
                source_stage="01",
                target_stage="02",
                default_severity=Severity.WARNING,
                tier_severity_override={
                    Tier.LITE: Severity.INFO,
                    Tier.STANDARD: Severity.WARNING,
                    Tier.PROFESSIONAL: Severity.WARNING,
                    Tier.ENTERPRISE: Severity.ERROR,
                },
            ),
            ConsistencyRule(
                rule_id="CONS-003",
                description="Architecture decisions must trace to user stories",
                source_stage="01",
                target_stage="02",
                default_severity=Severity.INFO,
                tier_severity_override={
                    Tier.LITE: Severity.INFO,
                    Tier.STANDARD: Severity.INFO,
                    Tier.PROFESSIONAL: Severity.WARNING,
                    Tier.ENTERPRISE: Severity.WARNING,
                },
            ),
        ]

    def _check_impl(self) -> List[ConsistencyViolation]:
        """Check Stage 01 ↔ Stage 02 consistency."""
        violations: List[ConsistencyViolation] = []

        # Get Stage 01 requirement IDs
        stage_01_ids = self._get_stage_01_document_ids()

        # Check ADRs reference requirements
        violations.extend(self._check_adr_references(stage_01_ids))

        # Check design documents cite specifications
        violations.extend(self._check_design_citations(stage_01_ids))

        return violations

    def _get_stage_01_document_ids(self) -> set[str]:
        """Extract document IDs from Stage 01 files."""
        ids = set()

        if not self.source_path:
            return ids

        # Look for FR-*, US-*, SPEC-* patterns in filenames and content
        for md_file in self.find_markdown_files(self.source_path):
            # Extract from filename (e.g., FR-001-Authentication.md)
            filename = md_file.stem
            if filename.startswith(("FR-", "US-", "SPEC-", "REQ-")):
                # Extract ID portion
                parts = filename.split("-")
                if len(parts) >= 2 and parts[1].isdigit():
                    ids.add(f"{parts[0]}-{parts[1]}")

            # Extract from frontmatter
            frontmatter = self.extract_frontmatter(md_file)
            if frontmatter:
                doc_id = frontmatter.get("id") or frontmatter.get("document_id")
                if doc_id and isinstance(doc_id, str):
                    ids.add(doc_id)

        return ids

    def _check_adr_references(self, stage_01_ids: set[str]) -> List[ConsistencyViolation]:
        """Check that ADRs reference Stage 01 requirements."""
        violations = []

        if not self.target_path:
            return violations

        # Find ADR folder
        adr_folder = self.target_path / "01-ADRs"
        if not adr_folder.exists():
            adr_folder = self.target_path  # Fallback to root

        adr_files = [
            f for f in self.find_markdown_files(adr_folder)
            if f.stem.upper().startswith("ADR-")
        ]

        for adr_file in adr_files:
            try:
                content = adr_file.read_text(encoding="utf-8")
                references = self.extract_references(content)

                # Check if ADR references any Stage 01 document
                stage_01_refs = references.intersection(stage_01_ids)

                if not stage_01_refs and stage_01_ids:
                    violations.append(
                        ConsistencyViolation(
                            rule_id="CONS-001",
                            severity=Severity.WARNING,  # Will be overridden by tier
                            source_stage=self.source_stage,
                            target_stage=self.target_stage,
                            target_file=adr_file,
                            message=f"ADR does not reference any Stage 01 requirements",
                            expected="Reference to FR-*, US-*, SPEC-*, or REQ-* documents",
                            actual="No Stage 01 references found",
                            fix_suggestion=(
                                f"Add references to Stage 01 requirements in {adr_file.name}. "
                                f"Available IDs: {', '.join(sorted(list(stage_01_ids)[:5]))}"
                            ),
                        )
                    )
            except Exception:
                pass  # Skip files that can't be read

        return violations

    def _check_design_citations(self, stage_01_ids: set[str]) -> List[ConsistencyViolation]:
        """Check that design documents cite specification IDs."""
        violations = []

        if not self.target_path:
            return violations

        # Find design documents (excluding ADRs)
        design_files = [
            f for f in self.find_markdown_files(self.target_path)
            if not f.stem.upper().startswith("ADR-")
            and "System-Architecture" in f.name or "Design" in f.name
        ]

        for design_file in design_files:
            try:
                content = design_file.read_text(encoding="utf-8")
                references = self.extract_references(content)

                # Check if design doc references SPEC-* documents
                spec_refs = [ref for ref in references if ref.startswith("SPEC-")]

                if not spec_refs:
                    violations.append(
                        ConsistencyViolation(
                            rule_id="CONS-002",
                            severity=Severity.WARNING,
                            source_stage=self.source_stage,
                            target_stage=self.target_stage,
                            target_file=design_file,
                            message="Design document does not cite any specification IDs",
                            expected="Reference to SPEC-* documents",
                            actual="No specification references found",
                            fix_suggestion=(
                                f"Add references to related specifications in {design_file.name}"
                            ),
                        )
                    )
            except Exception:
                pass

        return violations
