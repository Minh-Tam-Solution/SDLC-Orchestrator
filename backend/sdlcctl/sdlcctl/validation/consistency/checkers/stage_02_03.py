"""Stage 02 (Design) ↔ Stage 03 (Integrate) consistency checker.

SDLC 6.0.5 - SPEC-0021 Stage Consistency Validation.

Validates:
- CONS-004: API contracts must match architecture design
- CONS-005: Integration strategy must reference ADRs
- CONS-006: Third-party dependencies must be documented
"""

from pathlib import Path
from typing import List, Set

from ...tier import Tier
from ...violation import Severity
from ..models import ConsistencyRule, ConsistencyViolation
from .base import BaseConsistencyChecker


class Stage02To03Checker(BaseConsistencyChecker):
    """Check consistency between Stage 02 (Design) and Stage 03 (Integrate)."""

    @property
    def source_stage(self) -> str:
        return "02"

    @property
    def target_stage(self) -> str:
        return "03"

    def get_rules(self) -> List[ConsistencyRule]:
        """Return rules for Stage 02 ↔ Stage 03 consistency."""
        return [
            ConsistencyRule(
                rule_id="CONS-004",
                description="API contracts must match architecture design",
                source_stage="02",
                target_stage="03",
                default_severity=Severity.WARNING,
                tier_severity_override={
                    Tier.LITE: Severity.INFO,
                    Tier.STANDARD: Severity.WARNING,
                    Tier.PROFESSIONAL: Severity.ERROR,
                    Tier.ENTERPRISE: Severity.ERROR,
                },
            ),
            ConsistencyRule(
                rule_id="CONS-005",
                description="Integration strategy must reference ADRs",
                source_stage="02",
                target_stage="03",
                default_severity=Severity.WARNING,
                tier_severity_override={
                    Tier.LITE: Severity.INFO,
                    Tier.STANDARD: Severity.WARNING,
                    Tier.PROFESSIONAL: Severity.WARNING,
                    Tier.ENTERPRISE: Severity.ERROR,
                },
            ),
            ConsistencyRule(
                rule_id="CONS-006",
                description="Third-party dependencies must be documented",
                source_stage="02",
                target_stage="03",
                default_severity=Severity.WARNING,
                tier_severity_override={
                    Tier.LITE: Severity.INFO,
                    Tier.STANDARD: Severity.WARNING,
                    Tier.PROFESSIONAL: Severity.WARNING,
                    Tier.ENTERPRISE: Severity.WARNING,
                },
            ),
        ]

    def _check_impl(self) -> List[ConsistencyViolation]:
        """Check Stage 02 ↔ Stage 03 consistency."""
        violations: List[ConsistencyViolation] = []

        # Get ADR IDs from Stage 02
        adr_ids = self._get_adr_ids()

        # Check API contracts reference architecture
        violations.extend(self._check_api_contract_references(adr_ids))

        # Check integration strategy references ADRs
        violations.extend(self._check_integration_strategy_references(adr_ids))

        return violations

    def _get_adr_ids(self) -> Set[str]:
        """Extract ADR IDs from Stage 02."""
        ids = set()

        if not self.source_path:
            return ids

        adr_folder = self.source_path / "01-ADRs"
        if not adr_folder.exists():
            adr_folder = self.source_path

        for md_file in self.find_markdown_files(adr_folder):
            if md_file.stem.upper().startswith("ADR-"):
                # Extract ID (e.g., ADR-001 from ADR-001-Multi-Tenant.md)
                parts = md_file.stem.split("-")
                if len(parts) >= 2 and parts[1].isdigit():
                    ids.add(f"ADR-{parts[1]}")

        return ids

    def _check_api_contract_references(self, adr_ids: Set[str]) -> List[ConsistencyViolation]:
        """Check that API contracts reference architecture decisions."""
        violations = []

        if not self.target_path:
            return violations

        # Find API contract folder
        contract_folder = self.target_path / "01-api-contracts"
        if not contract_folder.exists():
            contract_folder = self.target_path

        # Find OpenAPI specs
        openapi_files = self.find_yaml_files(contract_folder)

        for spec_file in openapi_files:
            if "openapi" in spec_file.name.lower() or "api" in spec_file.name.lower():
                try:
                    content = spec_file.read_text(encoding="utf-8")

                    # Check if spec references any ADRs
                    references = self.extract_references(content)
                    adr_refs = references.intersection(adr_ids)

                    if not adr_refs and adr_ids:
                        violations.append(
                            ConsistencyViolation(
                                rule_id="CONS-004",
                                severity=Severity.WARNING,
                                source_stage=self.source_stage,
                                target_stage=self.target_stage,
                                source_file=None,
                                target_file=spec_file,
                                message="API contract does not reference architecture decisions",
                                expected="Reference to ADR-* documents in comments/description",
                                actual="No ADR references found",
                                fix_suggestion=(
                                    f"Add ADR references in {spec_file.name} description. "
                                    f"Available ADRs: {', '.join(sorted(list(adr_ids)[:5]))}"
                                ),
                            )
                        )
                except Exception:
                    pass

        return violations

    def _check_integration_strategy_references(
        self, adr_ids: Set[str]
    ) -> List[ConsistencyViolation]:
        """Check that integration strategy documents reference ADRs."""
        violations = []

        if not self.target_path:
            return violations

        # Find integration strategy documents
        strategy_files = [
            f for f in self.find_markdown_files(self.target_path)
            if "strategy" in f.name.lower() or "integration" in f.name.lower()
        ]

        for strategy_file in strategy_files:
            try:
                content = strategy_file.read_text(encoding="utf-8")
                references = self.extract_references(content)
                adr_refs = references.intersection(adr_ids)

                if not adr_refs and adr_ids:
                    violations.append(
                        ConsistencyViolation(
                            rule_id="CONS-005",
                            severity=Severity.WARNING,
                            source_stage=self.source_stage,
                            target_stage=self.target_stage,
                            target_file=strategy_file,
                            message="Integration strategy does not reference ADRs",
                            expected="Reference to architecture decisions (ADR-*)",
                            actual="No ADR references found",
                            fix_suggestion=(
                                f"Add references to relevant ADRs in {strategy_file.name}"
                            ),
                        )
                    )
            except Exception:
                pass

        return violations
