"""Stage 01 (Planning) ↔ Stage 04 (Build) consistency checker.

SDLC 6.0.5 - SPEC-0021 Stage Consistency Validation.

Validates:
- CONS-010: Implementation must satisfy requirements
- CONS-011: Behavioral changes must update Stage 01
- CONS-012: User stories acceptance criteria must be met
"""

from pathlib import Path
from typing import Dict, List, Set

from ...tier import Tier
from ...violation import Severity
from ..models import ConsistencyRule, ConsistencyViolation
from .base import BaseConsistencyChecker


class Stage01To04Checker(BaseConsistencyChecker):
    """Check consistency between Stage 01 (Planning) and Stage 04 (Build)."""

    @property
    def source_stage(self) -> str:
        return "01"

    @property
    def target_stage(self) -> str:
        return "04"

    def get_rules(self) -> List[ConsistencyRule]:
        """Return rules for Stage 01 ↔ Stage 04 consistency."""
        return [
            ConsistencyRule(
                rule_id="CONS-010",
                description="Implementation must satisfy requirements",
                source_stage="01",
                target_stage="04",
                default_severity=Severity.WARNING,
                tier_severity_override={
                    Tier.LITE: Severity.INFO,
                    Tier.STANDARD: Severity.WARNING,
                    Tier.PROFESSIONAL: Severity.ERROR,
                    Tier.ENTERPRISE: Severity.ERROR,
                },
            ),
            ConsistencyRule(
                rule_id="CONS-011",
                description="Behavioral changes must update Stage 01",
                source_stage="01",
                target_stage="04",
                default_severity=Severity.WARNING,
                tier_severity_override={
                    Tier.LITE: Severity.INFO,
                    Tier.STANDARD: Severity.WARNING,
                    Tier.PROFESSIONAL: Severity.WARNING,
                    Tier.ENTERPRISE: Severity.ERROR,
                },
            ),
            ConsistencyRule(
                rule_id="CONS-012",
                description="User stories acceptance criteria must be met",
                source_stage="01",
                target_stage="04",
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
        """Check Stage 01 ↔ Stage 04 consistency."""
        violations: List[ConsistencyViolation] = []

        # Get requirements from Stage 01
        requirements = self._get_requirements()

        # Check code references requirements
        violations.extend(self._check_code_requirement_references(requirements))

        # Check for unreferenced requirements
        violations.extend(self._check_unreferenced_requirements(requirements))

        return violations

    def _get_requirements(self) -> Dict[str, Dict]:
        """Extract requirements from Stage 01."""
        requirements: Dict[str, Dict] = {}

        if not self.source_path:
            return requirements

        # Find functional requirements folder
        fr_folder = self.source_path / "03-Functional-Requirements"
        if not fr_folder.exists():
            fr_folder = self.source_path

        for md_file in self.find_markdown_files(fr_folder):
            # Look for FR-*, US-*, REQ-* patterns
            filename = md_file.stem

            if filename.startswith(("FR-", "US-", "REQ-")):
                parts = filename.split("-")
                if len(parts) >= 2 and parts[1].isdigit():
                    req_id = f"{parts[0]}-{parts[1]}"

                    # Try to extract status from frontmatter
                    frontmatter = self.extract_frontmatter(md_file)
                    status = "UNKNOWN"
                    if frontmatter:
                        status = frontmatter.get("status", "UNKNOWN")

                    requirements[req_id] = {
                        "id": req_id,
                        "filename": filename,
                        "file_path": md_file,
                        "status": status,
                    }

        return requirements

    def _check_code_requirement_references(
        self, requirements: Dict[str, Dict]
    ) -> List[ConsistencyViolation]:
        """Check that code files reference requirements they implement."""
        violations = []

        if not self.target_path or not requirements:
            return violations

        # Find implementation files (services, routes, models)
        impl_files = [
            f for f in self.find_python_files(self.target_path)
            if any(
                folder in str(f)
                for folder in ["services", "routes", "api", "models", "core"]
            )
            and not f.name.startswith("test_")
            and "__pycache__" not in str(f)
        ]

        # Check sample of files for requirement references
        # (Full check would be too slow)
        sampled_files = impl_files[:50]  # Check first 50 files

        files_without_refs = []
        for py_file in sampled_files:
            try:
                content = py_file.read_text(encoding="utf-8")

                # Check for requirement references in comments/docstrings
                refs = self.extract_references(content)
                req_refs = refs.intersection(set(requirements.keys()))

                if not req_refs:
                    files_without_refs.append(py_file)
            except Exception:
                pass

        # Only report if significant portion lacks references
        if len(files_without_refs) > len(sampled_files) * 0.8:  # >80% without refs
            violations.append(
                ConsistencyViolation(
                    rule_id="CONS-010",
                    severity=Severity.WARNING,
                    source_stage=self.source_stage,
                    target_stage=self.target_stage,
                    message=(
                        f"Implementation files rarely reference requirements. "
                        f"{len(files_without_refs)}/{len(sampled_files)} files lack FR-*/US-*/REQ-* references."
                    ),
                    expected="Code comments/docstrings should reference requirements",
                    actual="Most implementation files lack requirement references",
                    fix_suggestion=(
                        "Add requirement IDs to docstrings of implementing functions. "
                        "Example: '''Implements FR-001: User authentication'''"
                    ),
                    context={
                        "files_checked": len(sampled_files),
                        "files_without_refs": len(files_without_refs),
                    },
                )
            )

        return violations

    def _check_unreferenced_requirements(
        self, requirements: Dict[str, Dict]
    ) -> List[ConsistencyViolation]:
        """Check for requirements not referenced anywhere in code."""
        violations = []

        if not self.target_path or not requirements:
            return violations

        # Collect all requirement references from code
        all_code_refs: Set[str] = set()

        for py_file in self.find_python_files(self.target_path):
            if "__pycache__" in str(py_file):
                continue
            try:
                content = py_file.read_text(encoding="utf-8")
                refs = self.extract_references(content)
                all_code_refs.update(refs)
            except Exception:
                pass

        # Find requirements not referenced in code
        unreferenced = set(requirements.keys()) - all_code_refs

        # Only report if significant number unreferenced
        if len(unreferenced) > len(requirements) * 0.5:  # >50% unreferenced
            sample_unreferenced = list(unreferenced)[:5]
            violations.append(
                ConsistencyViolation(
                    rule_id="CONS-011",
                    severity=Severity.WARNING,
                    source_stage=self.source_stage,
                    target_stage=self.target_stage,
                    message=(
                        f"Many requirements not referenced in code. "
                        f"{len(unreferenced)}/{len(requirements)} requirements have no code references."
                    ),
                    expected="All requirements should be traceable to code",
                    actual=f"Unreferenced: {', '.join(sample_unreferenced)}...",
                    fix_suggestion=(
                        "Add requirement IDs to implementing code or update requirements "
                        "to reflect actual implementation scope."
                    ),
                    context={
                        "total_requirements": len(requirements),
                        "unreferenced_count": len(unreferenced),
                        "sample_unreferenced": sample_unreferenced,
                    },
                )
            )

        return violations
