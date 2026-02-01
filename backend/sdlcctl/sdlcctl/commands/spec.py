"""
SDLC Specification CLI Commands - Sprint 126 Enhancement.

Commands for validating, listing, initializing, and converting SDLC Framework 6.0.0 specifications.

Usage:
    sdlcctl spec validate [OPTIONS] [PATH]
    sdlcctl spec validate --fix [PATH]
    sdlcctl spec report [PATH]
    sdlcctl spec list [OPTIONS] [PATH]
    sdlcctl spec init [OPTIONS] [PATH]
    sdlcctl spec convert --from openspec [PATH]

Framework: SDLC 6.0.0 Specification Standard
Sprint: 126 - Implementation Alignment (Multi-Frontend)
Reference: SPEC-0002 Framework 6.0.0 Specification Standard

Changelog:
    - Sprint 119: Initial spec validate/report/list commands
    - Sprint 125: Added SpecFrontmatterValidator with JSON Schema
    - Sprint 126: Added spec init, spec convert, JSON Schema integration
"""

import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import typer
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm, Prompt
from rich.table import Table
from rich.tree import Tree

from ..validation.violation import ScanResult, Severity, ViolationReport

# Try to import jsonschema for schema-based validation
try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False

# Initialize Typer app for spec subcommand group
app = typer.Typer(
    name="spec",
    help="Specification validation and management commands",
    no_args_is_help=True,
)

console = Console()


# ============================================================================
# Validation Engine
# ============================================================================


class SpecificationValidator:
    """
    Specification validator for SDLC Framework 6.0.0.

    Validates:
    - YAML frontmatter (required fields, formats)
    - BDD requirements (GIVEN-WHEN-THEN format)
    - Tier-specific sections
    - Acceptance criteria tables
    - Cross-references

    Reference: SPEC-0002 Framework 6.0.0 Specification Standard
    """

    # Required YAML frontmatter fields (SPEC-0002 FR-008)
    REQUIRED_FIELDS = [
        "spec_id",
        "title",
        "version",
        "status",
        "tier",
        "owner",
        "last_updated",
    ]

    # Optional but recommended fields
    RECOMMENDED_FIELDS = [
        "pillar",
        "tags",
        "related_adrs",
        "related_specs",
    ]

    # Valid status values
    VALID_STATUSES = ["DRAFT", "REVIEW", "APPROVED", "ACTIVE", "DEPRECATED"]

    # Valid tier values
    VALID_TIERS = ["LITE", "STANDARD", "PROFESSIONAL", "ENTERPRISE"]

    # BDD keywords
    BDD_KEYWORDS = ["GIVEN", "WHEN", "THEN", "AND", "BUT"]

    # Spec ID pattern
    SPEC_ID_PATTERN = r"^SPEC-\d{4}$"

    # Version pattern (semantic versioning)
    VERSION_PATTERN = r"^\d+\.\d+\.\d+$"

    # Date pattern (YYYY-MM-DD)
    DATE_PATTERN = r"^\d{4}-\d{2}-\d{2}$"

    def __init__(self, path: Path, tier: Optional[str] = None, use_schema: bool = True):
        """
        Initialize specification validator.

        Args:
            path: Path to specification file or directory
            tier: Optional tier to validate against (LITE, STANDARD, PROFESSIONAL, ENTERPRISE)
            use_schema: Whether to use JSON Schema validation (Sprint 126 enhancement)
        """
        self.path = path
        self.tier = tier
        self.use_schema = use_schema and HAS_JSONSCHEMA
        self.violations: List[ViolationReport] = []
        self.files_scanned = 0
        self.start_time = 0.0
        self._schema: Optional[Dict[str, Any]] = None

    @property
    def schema(self) -> Optional[Dict[str, Any]]:
        """
        Load JSON schema for frontmatter validation (Sprint 126).

        Returns:
            JSON Schema dict or None if unavailable
        """
        if self._schema is None and self.use_schema:
            schema_path = Path(__file__).parent.parent / "schemas" / "spec-frontmatter-schema.json"
            if schema_path.exists():
                try:
                    with open(schema_path, "r", encoding="utf-8") as f:
                        self._schema = json.load(f)
                except Exception:
                    self._schema = {}
            else:
                self._schema = {}
        return self._schema

    def validate(self) -> ScanResult:
        """
        Validate specification(s).

        Returns:
            ScanResult with violations found
        """
        import re

        self.start_time = time.perf_counter()
        self.violations = []
        self.files_scanned = 0

        # Determine files to scan
        files_to_scan: List[Path] = []

        if self.path.is_file():
            if self.path.suffix.lower() == ".md":
                files_to_scan.append(self.path)
        elif self.path.is_dir():
            # Find all markdown files in directory
            files_to_scan = list(self.path.rglob("*.md"))
            # Filter to only SPEC-*.md files
            files_to_scan = [
                f for f in files_to_scan
                if f.name.startswith("SPEC-") and not f.name.startswith("SPEC-TEMPLATE")
            ]

        for file_path in files_to_scan:
            self._validate_file(file_path)
            self.files_scanned += 1

        scan_time_ms = (time.perf_counter() - self.start_time) * 1000

        return ScanResult(
            scan_path=self.path,
            violations=self.violations,
            files_scanned=self.files_scanned,
            scan_time_ms=scan_time_ms,
            scanner_version="1.0.0",
        )

    def _validate_file(self, file_path: Path) -> None:
        """
        Validate a single specification file.

        Args:
            file_path: Path to specification file
        """
        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception as e:
            self.violations.append(
                ViolationReport(
                    rule_id="SPEC-000",
                    severity=Severity.ERROR,
                    file_path=file_path,
                    message=f"Failed to read file: {e}",
                    auto_fixable=False,
                )
            )
            return

        # Validate YAML frontmatter
        self._validate_frontmatter(file_path, content)

        # Validate BDD format
        self._validate_bdd_format(file_path, content)

        # Validate tier-specific sections
        self._validate_tier_sections(file_path, content)

        # Validate acceptance criteria
        self._validate_acceptance_criteria(file_path, content)

        # Validate cross-references
        self._validate_cross_references(file_path, content)

    def _validate_frontmatter(self, file_path: Path, content: str) -> None:
        """
        Validate YAML frontmatter (SPEC-0002 FR-001, FR-008).

        Sprint 126: Now supports JSON Schema validation when jsonschema is available.

        Args:
            file_path: Path to specification file
            content: File content
        """
        # Check for YAML frontmatter
        # Pattern allows empty frontmatter (---\n---) by making \n before closing --- optional
        frontmatter_match = re.match(
            r"^---[ \t]*\n(.*?)(?:\n)?---[ \t]*\n",
            content,
            re.MULTILINE | re.DOTALL,
        )

        if not frontmatter_match:
            self.violations.append(
                ViolationReport(
                    rule_id="SPEC-001",
                    severity=Severity.ERROR,
                    file_path=file_path,
                    message="Missing YAML frontmatter (---)",
                    fix_suggestion="Add YAML frontmatter at the beginning of the file:\n---\nspec_id: SPEC-XXXX\ntitle: ...\nversion: \"1.0.0\"\nstatus: DRAFT\ntier:\n  - PROFESSIONAL\nowner: ...\nlast_updated: YYYY-MM-DD\n---",
                    auto_fixable=True,
                    context={"expected_format": "YAML frontmatter with required fields"},
                )
            )
            return

        frontmatter_text = frontmatter_match.group(1)

        # Parse YAML
        try:
            frontmatter = yaml.safe_load(frontmatter_text)
        except yaml.YAMLError as e:
            self.violations.append(
                ViolationReport(
                    rule_id="SPEC-002",
                    severity=Severity.ERROR,
                    file_path=file_path,
                    message=f"Invalid YAML frontmatter: {e}",
                    auto_fixable=False,
                    context={"yaml_error": str(e)},
                )
            )
            return

        if not isinstance(frontmatter, dict):
            self.violations.append(
                ViolationReport(
                    rule_id="SPEC-002",
                    severity=Severity.ERROR,
                    file_path=file_path,
                    message="YAML frontmatter must be a dictionary",
                    auto_fixable=False,
                )
            )
            return

        # Sprint 126: Use JSON Schema validation if available
        if self.use_schema and self.schema and HAS_JSONSCHEMA:
            self._validate_frontmatter_with_schema(file_path, frontmatter)
        else:
            self._validate_frontmatter_manually(file_path, frontmatter)

    def _validate_frontmatter_with_schema(
        self, file_path: Path, frontmatter: Dict[str, Any]
    ) -> None:
        """
        Validate frontmatter using JSON Schema (Sprint 126).

        Args:
            file_path: Path to specification file
            frontmatter: Parsed frontmatter dictionary
        """
        try:
            jsonschema.validate(frontmatter, self.schema)
        except jsonschema.ValidationError as e:
            # Extract field name from error path
            field_path = ".".join(str(p) for p in e.absolute_path) or "(root)"

            # Map schema errors to SPEC rule IDs
            rule_id = "SPEC-003"  # Default: missing required field
            if "pattern" in str(e.schema):
                rule_id = "SPEC-004"  # Pattern mismatch
            elif "enum" in str(e.schema):
                rule_id = "SPEC-006"  # Invalid enum value
            elif e.validator == "required":
                rule_id = "SPEC-003"  # Missing required field
            elif e.validator == "type":
                rule_id = "SPEC-007"  # Type mismatch

            self.violations.append(
                ViolationReport(
                    rule_id=rule_id,
                    severity=Severity.ERROR,
                    file_path=file_path,
                    message=f"Invalid frontmatter field '{field_path}': {e.message}",
                    fix_suggestion=self._get_field_suggestion(field_path, frontmatter),
                    auto_fixable=True,
                    context={
                        "field": field_path,
                        "error": e.message,
                        "current_value": frontmatter.get(field_path),
                    },
                )
            )
        except jsonschema.SchemaError as e:
            # Schema error - fall back to manual validation
            self._validate_frontmatter_manually(file_path, frontmatter)

        # Check recommended fields (not in schema, additional check)
        missing_recommended = []
        for field in self.RECOMMENDED_FIELDS:
            if field not in frontmatter:
                missing_recommended.append(field)

        if missing_recommended:
            self.violations.append(
                ViolationReport(
                    rule_id="SPEC-010",
                    severity=Severity.INFO,
                    file_path=file_path,
                    message=f"Missing recommended frontmatter fields: {', '.join(missing_recommended)}",
                    fix_suggestion=f"Consider adding: {', '.join(missing_recommended)}",
                    auto_fixable=False,
                    context={"missing_fields": missing_recommended},
                )
            )

    def _get_field_suggestion(self, field: str, frontmatter: Dict[str, Any]) -> str:
        """
        Get fix suggestion for a specific field (Sprint 126).

        Args:
            field: Field name
            frontmatter: Current frontmatter

        Returns:
            Fix suggestion string
        """
        suggestions = {
            "spec_id": "Use format: spec_id: SPEC-0001",
            "title": 'Add descriptive title: title: "My Specification Title"',
            "version": 'Use semantic versioning: version: "1.0.0"',
            "status": f"Use valid status: status: {'/'.join(sorted(self.VALID_STATUSES))}",
            "tier": "Specify applicable tiers:\ntier:\n  - LITE\n  - STANDARD\n  - PROFESSIONAL\n  - ENTERPRISE",
            "owner": 'Specify owner: owner: "Team/Person Name"',
            "last_updated": 'Use ISO date format: last_updated: "2026-01-30"',
            "pillar": 'Specify pillar: pillar: "Pillar 7 - Quality Assurance"',
            "tags": "Add categorization tags:\ntags:\n  - tag-name",
            "related_adrs": "Reference related ADRs:\nrelated_adrs:\n  - ADR-001-Description",
            "related_specs": "Reference related specs:\nrelated_specs:\n  - SPEC-0001",
        }
        return suggestions.get(field, f"Fix the '{field}' field according to SPEC-0002 standard")

    def _validate_frontmatter_manually(
        self, file_path: Path, frontmatter: Dict[str, Any]
    ) -> None:
        """
        Validate frontmatter manually (fallback when JSON Schema unavailable).

        Args:
            file_path: Path to specification file
            frontmatter: Parsed frontmatter dictionary
        """
        # Check required fields
        missing_fields = []
        for field in self.REQUIRED_FIELDS:
            if field not in frontmatter:
                missing_fields.append(field)

        if missing_fields:
            self.violations.append(
                ViolationReport(
                    rule_id="SPEC-003",
                    severity=Severity.ERROR,
                    file_path=file_path,
                    message=f"Missing required frontmatter fields: {', '.join(missing_fields)}",
                    fix_suggestion=f"Add missing fields: {', '.join(missing_fields)}",
                    auto_fixable=True,
                    context={"missing_fields": missing_fields},
                )
            )

        # Validate spec_id format
        spec_id = frontmatter.get("spec_id", "")
        if spec_id and not re.match(self.SPEC_ID_PATTERN, spec_id):
            self.violations.append(
                ViolationReport(
                    rule_id="SPEC-004",
                    severity=Severity.ERROR,
                    file_path=file_path,
                    message=f"Invalid spec_id format: '{spec_id}'. Expected SPEC-XXXX",
                    fix_suggestion="Use format: SPEC-0001, SPEC-0002, etc.",
                    auto_fixable=True,
                    context={"current_value": spec_id, "expected_pattern": "SPEC-XXXX"},
                )
            )

        # Validate version format (semantic versioning)
        version = str(frontmatter.get("version", ""))
        # Remove quotes if present
        version = version.strip('"').strip("'")
        if version and not re.match(self.VERSION_PATTERN, version):
            self.violations.append(
                ViolationReport(
                    rule_id="SPEC-005",
                    severity=Severity.WARNING,
                    file_path=file_path,
                    message=f"Invalid version format: '{version}'. Expected semantic versioning (X.Y.Z)",
                    fix_suggestion="Use semantic versioning: 1.0.0, 1.1.0, 2.0.0, etc.",
                    auto_fixable=True,
                    context={"current_value": version, "expected_pattern": "X.Y.Z"},
                )
            )

        # Validate status
        status = frontmatter.get("status", "")
        if status and status not in self.VALID_STATUSES:
            self.violations.append(
                ViolationReport(
                    rule_id="SPEC-006",
                    severity=Severity.ERROR,
                    file_path=file_path,
                    message=f"Invalid status: '{status}'. Expected one of: {', '.join(self.VALID_STATUSES)}",
                    fix_suggestion=f"Use one of: {', '.join(self.VALID_STATUSES)}",
                    auto_fixable=True,
                    context={"current_value": status, "valid_values": self.VALID_STATUSES},
                )
            )

        # Validate tier (must be array or single string)
        tier = frontmatter.get("tier", [])
        if tier:
            tiers_to_check = tier if isinstance(tier, list) else [tier]
            invalid_tiers = [t for t in tiers_to_check if t not in self.VALID_TIERS]
            if invalid_tiers:
                self.violations.append(
                    ViolationReport(
                        rule_id="SPEC-008",
                        severity=Severity.ERROR,
                        file_path=file_path,
                        message=f"Invalid tier values: {', '.join(invalid_tiers)}. Expected one of: {', '.join(self.VALID_TIERS)}",
                        fix_suggestion=f"Use valid tiers: {', '.join(self.VALID_TIERS)}",
                        auto_fixable=True,
                        context={"invalid_tiers": invalid_tiers, "valid_tiers": self.VALID_TIERS},
                    )
                )

        # Validate last_updated format
        last_updated = str(frontmatter.get("last_updated", ""))
        last_updated = last_updated.strip('"').strip("'")
        if last_updated and not re.match(self.DATE_PATTERN, last_updated):
            self.violations.append(
                ViolationReport(
                    rule_id="SPEC-009",
                    severity=Severity.WARNING,
                    file_path=file_path,
                    message=f"Invalid last_updated format: '{last_updated}'. Expected YYYY-MM-DD",
                    fix_suggestion="Use date format: 2026-01-29",
                    auto_fixable=True,
                    context={"current_value": last_updated, "expected_pattern": "YYYY-MM-DD"},
                )
            )

        # Check recommended fields
        missing_recommended = []
        for field in self.RECOMMENDED_FIELDS:
            if field not in frontmatter:
                missing_recommended.append(field)

        if missing_recommended:
            self.violations.append(
                ViolationReport(
                    rule_id="SPEC-010",
                    severity=Severity.INFO,
                    file_path=file_path,
                    message=f"Missing recommended frontmatter fields: {', '.join(missing_recommended)}",
                    fix_suggestion=f"Consider adding: {', '.join(missing_recommended)}",
                    auto_fixable=False,
                    context={"missing_fields": missing_recommended},
                )
            )

    def _validate_bdd_format(self, file_path: Path, content: str) -> None:
        """
        Validate BDD requirements format (SPEC-0002 FR-002).

        Args:
            file_path: Path to specification file
            content: File content
        """
        import re

        # Find Functional Requirements section
        fr_match = re.search(
            r"##\s*(Functional Requirements|FR-\d+:)",
            content,
            re.IGNORECASE,
        )

        if not fr_match:
            # No functional requirements section - not an error for all specs
            return

        # Extract requirements section
        fr_section_start = fr_match.start()
        # Find next major section (## not ### and not followed by FR-)
        # Use negative lookahead (?!#) to avoid matching ### headings
        next_section = re.search(
            r"\n##(?!#)\s*(?!FR-)",
            content[fr_section_start + 10:],
        )
        if next_section:
            fr_section_end = fr_section_start + 10 + next_section.start()
        else:
            fr_section_end = len(content)

        fr_section = content[fr_section_start:fr_section_end]

        # Find all FR- blocks using split approach for more reliable matching
        # Split on ### FR- pattern and process each block
        fr_pattern = r"###\s*(FR-\d+)"
        fr_headers = list(re.finditer(fr_pattern, fr_section))

        if not fr_headers:
            return

        for i, header_match in enumerate(fr_headers):
            # Extract block from this header to next header (or end of section)
            block_start = header_match.start()
            if i + 1 < len(fr_headers):
                block_end = fr_headers[i + 1].start()
            else:
                block_end = len(fr_section)

            fr_block = fr_section[block_start:block_end]
            fr_id = header_match.group(1)

            # Check for gherkin code block
            if "```gherkin" not in fr_block.lower():
                # Check for GIVEN-WHEN-THEN keywords
                has_given = re.search(r"\bGIVEN\b", fr_block, re.IGNORECASE)
                has_when = re.search(r"\bWHEN\b", fr_block, re.IGNORECASE)
                has_then = re.search(r"\bTHEN\b", fr_block, re.IGNORECASE)

                if not (has_given and has_when and has_then):
                    self.violations.append(
                        ViolationReport(
                            rule_id="SPEC-020",
                            severity=Severity.WARNING,
                            file_path=file_path,
                            message=f"{fr_id}: Missing BDD format (GIVEN-WHEN-THEN)",
                            fix_suggestion="Use BDD format:\n```gherkin\nGIVEN preconditions\nWHEN action\nTHEN expected result\n```",
                            auto_fixable=False,
                            context={"requirement_id": fr_id},
                        )
                    )

    def _validate_tier_sections(self, file_path: Path, content: str) -> None:
        """
        Validate tier-specific sections (SPEC-0002 FR-003).

        Args:
            file_path: Path to specification file
            content: File content
        """
        import re
        import yaml

        # Extract frontmatter to check tier
        frontmatter_match = re.match(
            r"^---[ \t]*\n(.*?)(?:\n)?---[ \t]*\n",
            content,
            re.MULTILINE | re.DOTALL,
        )

        if not frontmatter_match:
            return

        try:
            frontmatter = yaml.safe_load(frontmatter_match.group(1))
        except yaml.YAMLError:
            return

        if not isinstance(frontmatter, dict):
            return

        tiers = frontmatter.get("tier", [])
        if not isinstance(tiers, list):
            return

        # Only check for tier-specific sections if multiple tiers or PROFESSIONAL/ENTERPRISE
        requires_tier_sections = (
            len(tiers) > 1 or
            "PROFESSIONAL" in tiers or
            "ENTERPRISE" in tiers
        )

        if not requires_tier_sections:
            return

        # Check for tier-specific requirements section
        has_tier_section = re.search(
            r"##\s*Tier[-\s]Specific\s+Requirements",
            content,
            re.IGNORECASE,
        )

        if not has_tier_section:
            self.violations.append(
                ViolationReport(
                    rule_id="SPEC-030",
                    severity=Severity.WARNING,
                    file_path=file_path,
                    message="Missing 'Tier-Specific Requirements' section for multi-tier or PROFESSIONAL/ENTERPRISE spec",
                    fix_suggestion="Add section:\n## Tier-Specific Requirements\n\n### PROFESSIONAL Tier\n...\n\n### ENTERPRISE Tier\n...",
                    auto_fixable=True,
                    context={"tiers": tiers},
                )
            )

    def _validate_acceptance_criteria(self, file_path: Path, content: str) -> None:
        """
        Validate acceptance criteria table (SPEC-0002 FR-004).

        Args:
            file_path: Path to specification file
            content: File content
        """
        import re

        # Check for Acceptance Criteria section
        ac_match = re.search(
            r"##\s*Acceptance\s+Criteria",
            content,
            re.IGNORECASE,
        )

        if not ac_match:
            # Acceptance criteria section is required for PROFESSIONAL+ specs
            self.violations.append(
                ViolationReport(
                    rule_id="SPEC-040",
                    severity=Severity.WARNING,
                    file_path=file_path,
                    message="Missing 'Acceptance Criteria' section",
                    fix_suggestion="Add section:\n## Acceptance Criteria\n\n| ID | Criterion | Expected Result | Test Method | Priority |\n|----|-----------|-----------------|-------------|----------|\n| AC-001 | ... | ... | ... | P0 |",
                    auto_fixable=True,
                )
            )
            return

        # Extract acceptance criteria section
        ac_section_start = ac_match.start()
        next_section = re.search(
            r"\n##\s*(?!AC-)",
            content[ac_section_start + 10:],
        )
        if next_section:
            ac_section_end = ac_section_start + 10 + next_section.start()
        else:
            ac_section_end = len(content)

        ac_section = content[ac_section_start:ac_section_end]

        # Check for table
        table_match = re.search(r"\|.*\|", ac_section)
        if not table_match:
            self.violations.append(
                ViolationReport(
                    rule_id="SPEC-041",
                    severity=Severity.WARNING,
                    file_path=file_path,
                    message="Acceptance Criteria section missing table format",
                    fix_suggestion="Use table format:\n| ID | Criterion | Expected Result | Test Method | Priority |\n|----|-----------|-----------------|-------------|----------|",
                    auto_fixable=False,
                )
            )
            return

        # Count AC entries (rows with AC-XXX pattern)
        ac_entries = re.findall(r"AC-\d+", ac_section)
        if len(ac_entries) < 5:
            self.violations.append(
                ViolationReport(
                    rule_id="SPEC-042",
                    severity=Severity.WARNING,
                    file_path=file_path,
                    message=f"Acceptance Criteria section has {len(ac_entries)} entries. Minimum 5 required.",
                    fix_suggestion="Add more acceptance criteria (minimum 5)",
                    auto_fixable=False,
                    context={"current_count": len(ac_entries), "minimum_required": 5},
                )
            )

    def _validate_cross_references(self, file_path: Path, content: str) -> None:
        """
        Validate cross-references (SPEC-0002 FR-005).

        Args:
            file_path: Path to specification file
            content: File content
        """
        import re
        import yaml

        # Extract frontmatter
        frontmatter_match = re.match(
            r"^---[ \t]*\n(.*?)(?:\n)?---[ \t]*\n",
            content,
            re.MULTILINE | re.DOTALL,
        )

        if not frontmatter_match:
            return

        try:
            frontmatter = yaml.safe_load(frontmatter_match.group(1))
        except yaml.YAMLError:
            return

        if not isinstance(frontmatter, dict):
            return

        # Validate related_adrs format
        related_adrs = frontmatter.get("related_adrs", [])
        if related_adrs:
            if not isinstance(related_adrs, list):
                self.violations.append(
                    ViolationReport(
                        rule_id="SPEC-050",
                        severity=Severity.WARNING,
                        file_path=file_path,
                        message="related_adrs must be an array",
                        fix_suggestion="Use array format:\nrelated_adrs:\n  - ADR-001-Title\n  - ADR-002-Title",
                        auto_fixable=True,
                    )
                )
            else:
                # Check format: ADR-XXX or ADR-XXX-Title
                for adr in related_adrs:
                    if not re.match(r"^ADR-\d{3}(-[\w-]+)?$", str(adr)):
                        self.violations.append(
                            ViolationReport(
                                rule_id="SPEC-051",
                                severity=Severity.INFO,
                                file_path=file_path,
                                message=f"ADR reference format: '{adr}'. Recommended: ADR-XXX-Title",
                                fix_suggestion="Use format: ADR-041-Stage-Dependency-Matrix",
                                auto_fixable=False,
                                context={"current_value": str(adr)},
                            )
                        )

        # Validate related_specs format
        related_specs = frontmatter.get("related_specs", [])
        if related_specs:
            if not isinstance(related_specs, list):
                self.violations.append(
                    ViolationReport(
                        rule_id="SPEC-052",
                        severity=Severity.WARNING,
                        file_path=file_path,
                        message="related_specs must be an array",
                        fix_suggestion="Use array format:\nrelated_specs:\n  - SPEC-0001\n  - SPEC-0002",
                        auto_fixable=True,
                    )
                )
            else:
                # Check format: SPEC-XXXX
                for spec in related_specs:
                    if not re.match(r"^SPEC-\d{4}$", str(spec)):
                        self.violations.append(
                            ViolationReport(
                                rule_id="SPEC-053",
                                severity=Severity.INFO,
                                file_path=file_path,
                                message=f"Spec reference format: '{spec}'. Expected: SPEC-XXXX",
                                fix_suggestion="Use format: SPEC-0001, SPEC-0002",
                                auto_fixable=False,
                                context={"current_value": str(spec)},
                            )
                        )


# ============================================================================
# CLI Commands
# ============================================================================


@app.command("validate")
def validate(
    path: Path = typer.Argument(
        Path("."),
        help="Path to specification file or directory",
        exists=True,
    ),
    tier: Optional[str] = typer.Option(
        None,
        "--tier",
        "-t",
        help="Validate against specific tier (LITE, STANDARD, PROFESSIONAL, ENTERPRISE)",
    ),
    fix: bool = typer.Option(
        False,
        "--fix",
        "-f",
        help="Auto-fix fixable violations",
    ),
    output_format: str = typer.Option(
        "text",
        "--format",
        "-o",
        help="Output format: text, json, github",
    ),
    strict: bool = typer.Option(
        False,
        "--strict",
        "-s",
        help="Treat warnings as errors",
    ),
) -> None:
    """
    Validate SDLC Framework 6.0.0 specifications.

    Validates YAML frontmatter, BDD requirements format, tier-specific sections,
    acceptance criteria tables, and cross-references.

    Examples:
        sdlcctl spec validate docs/02-design/14-Technical-Specs/
        sdlcctl spec validate SPEC-0001-Anti-Vibecoding.md
        sdlcctl spec validate --tier ENTERPRISE --strict
        sdlcctl spec validate --fix --format json
    """
    # Validate tier if provided
    valid_tiers = ["LITE", "STANDARD", "PROFESSIONAL", "ENTERPRISE"]
    if tier and tier.upper() not in valid_tiers:
        console.print(f"[red]Error: Invalid tier '{tier}'. Valid: {', '.join(valid_tiers)}[/red]")
        raise typer.Exit(code=1)

    # Display header
    console.print()
    console.print(Panel(
        "[bold cyan]SDLC Specification Validator[/bold cyan]\n"
        "[dim]Framework 6.0.0 Specification Standard[/dim]",
        border_style="cyan",
    ))
    console.print()

    # Run validation with progress
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task("Validating specifications...", total=None)

        validator = SpecificationValidator(path, tier=tier.upper() if tier else None)
        result = validator.validate()

        progress.update(task, completed=True)

    # Handle --fix option
    if fix and result.auto_fixable_count > 0:
        console.print(f"[yellow]Auto-fix not yet implemented. {result.auto_fixable_count} violations can be auto-fixed.[/yellow]")
        console.print()

    # Output results
    if output_format == "json":
        _output_json(result)
    elif output_format == "github":
        _output_github(result)
    else:
        _output_text(result, strict)

    # Exit code
    if strict:
        exit_code = 0 if len(result.violations) == 0 else 1
    else:
        exit_code = 0 if result.error_count == 0 else 1

    raise typer.Exit(code=exit_code)


@app.command("report")
def report(
    path: Path = typer.Argument(
        Path("."),
        help="Path to specification file or directory",
        exists=True,
    ),
    output_format: str = typer.Option(
        "text",
        "--format",
        "-o",
        help="Output format: text, json, markdown",
    ),
    output_file: Optional[Path] = typer.Option(
        None,
        "--output",
        "-O",
        help="Write report to file instead of stdout",
    ),
) -> None:
    """
    Generate specification compliance report.

    Examples:
        sdlcctl spec report docs/02-design/14-Technical-Specs/
        sdlcctl spec report --format markdown --output report.md
    """
    # Run validation
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task("Analyzing specifications...", total=None)

        validator = SpecificationValidator(path)
        result = validator.validate()

        progress.update(task, completed=True)

    # Generate report
    if output_format == "json":
        report_content = json.dumps(result.to_dict(), indent=2)
    elif output_format == "markdown":
        report_content = _generate_markdown_report(result)
    else:
        report_content = _generate_text_report(result)

    # Output
    if output_file:
        output_file.write_text(report_content, encoding="utf-8")
        console.print(f"[green]Report written to: {output_file}[/green]")
    else:
        console.print(report_content)


@app.command("list")
def list_specs(
    path: Path = typer.Argument(
        Path("."),
        help="Path to search for specifications",
        exists=True,
    ),
    tier: Optional[str] = typer.Option(
        None,
        "--tier",
        "-t",
        help="Filter by tier",
    ),
    status: Optional[str] = typer.Option(
        None,
        "--status",
        "-s",
        help="Filter by status (DRAFT, REVIEW, APPROVED, ACTIVE, DEPRECATED)",
    ),
) -> None:
    """
    List all specifications in a directory.

    Examples:
        sdlcctl spec list docs/02-design/14-Technical-Specs/
        sdlcctl spec list --tier PROFESSIONAL
        sdlcctl spec list --status APPROVED
    """
    import re
    import yaml

    # Find all SPEC-*.md files
    if path.is_file():
        files = [path] if path.name.startswith("SPEC-") else []
    else:
        files = sorted(path.rglob("SPEC-*.md"))

    if not files:
        console.print("[yellow]No specifications found.[/yellow]")
        raise typer.Exit(code=0)

    # Parse specs
    specs = []
    for file_path in files:
        try:
            content = file_path.read_text(encoding="utf-8")
            frontmatter_match = re.match(
                r"^---[ \t]*\n(.*?)(?:\n)?---[ \t]*\n",
                content,
                re.MULTILINE | re.DOTALL,
            )
            if frontmatter_match:
                frontmatter = yaml.safe_load(frontmatter_match.group(1))
                if isinstance(frontmatter, dict):
                    specs.append({
                        "file": file_path,
                        "spec_id": frontmatter.get("spec_id", "Unknown"),
                        "title": frontmatter.get("title", "Unknown"),
                        "status": frontmatter.get("status", "Unknown"),
                        "tier": frontmatter.get("tier", []),
                        "last_updated": frontmatter.get("last_updated", "Unknown"),
                    })
        except Exception:
            continue

    # Filter by tier
    if tier:
        tier_upper = tier.upper()
        specs = [s for s in specs if tier_upper in s.get("tier", [])]

    # Filter by status
    if status:
        status_upper = status.upper()
        specs = [s for s in specs if s.get("status", "").upper() == status_upper]

    if not specs:
        console.print("[yellow]No specifications match the filters.[/yellow]")
        raise typer.Exit(code=0)

    # Display table
    table = Table(title="SDLC Specifications")
    table.add_column("Spec ID", style="cyan")
    table.add_column("Title", style="white")
    table.add_column("Status", style="green")
    table.add_column("Tier(s)", style="yellow")
    table.add_column("Last Updated", style="dim")

    for spec in specs:
        status_style = "green" if spec["status"] == "APPROVED" else "yellow"
        table.add_row(
            spec["spec_id"],
            spec["title"][:50] + "..." if len(spec["title"]) > 50 else spec["title"],
            f"[{status_style}]{spec['status']}[/{status_style}]",
            ", ".join(spec["tier"]) if isinstance(spec["tier"], list) else str(spec["tier"]),
            str(spec["last_updated"]),
        )

    console.print()
    console.print(table)
    console.print(f"\n[dim]Total: {len(specs)} specifications[/dim]")


@app.command("init")
def init_spec(
    path: Path = typer.Argument(
        Path("."),
        help="Directory where specification will be created",
    ),
    spec_id: Optional[str] = typer.Option(
        None,
        "--spec-id",
        "-i",
        help="Specification ID (e.g., SPEC-0001). Auto-generated if not provided.",
    ),
    title: Optional[str] = typer.Option(
        None,
        "--title",
        "-t",
        help="Specification title",
    ),
    tier: str = typer.Option(
        "PROFESSIONAL",
        "--tier",
        "-T",
        help="Target tier (LITE, STANDARD, PROFESSIONAL, ENTERPRISE)",
    ),
    stage: str = typer.Option(
        "02",
        "--stage",
        "-s",
        help="SDLC stage (00-09)",
    ),
    interactive: bool = typer.Option(
        True,
        "--interactive/--no-interactive",
        "-I/-N",
        help="Interactive mode prompts for values",
    ),
) -> None:
    """
    Initialize a new SDLC 6.0.0 specification file.

    Creates a specification file with proper YAML frontmatter template.

    Examples:
        sdlcctl spec init docs/02-design/14-Technical-Specs/
        sdlcctl spec init --spec-id SPEC-0042 --title "My Feature" --tier ENTERPRISE
        sdlcctl spec init --no-interactive --spec-id SPEC-0001 --title "API Gateway"
    """
    # Validate tier
    valid_tiers = ["LITE", "STANDARD", "PROFESSIONAL", "ENTERPRISE"]
    tier_upper = tier.upper()
    if tier_upper not in valid_tiers:
        console.print(f"[red]Error: Invalid tier '{tier}'. Valid: {', '.join(valid_tiers)}[/red]")
        raise typer.Exit(code=1)

    # Validate stage
    if not re.match(r"^(0[0-9]|10)$", stage):
        console.print(f"[red]Error: Invalid stage '{stage}'. Must be 00-10.[/red]")
        raise typer.Exit(code=1)

    # Interactive mode
    if interactive:
        if not spec_id:
            # Find next available spec ID
            existing_specs = list(path.rglob("SPEC-*.md")) if path.is_dir() else []
            existing_ids = []
            for f in existing_specs:
                match = re.search(r"SPEC-(\d{4})", f.name)
                if match:
                    existing_ids.append(int(match.group(1)))
            next_id = max(existing_ids) + 1 if existing_ids else 1
            default_id = f"SPEC-{next_id:04d}"
            spec_id = Prompt.ask("Specification ID", default=default_id)

        if not title:
            title = Prompt.ask("Specification title")

        tier_upper = Prompt.ask(
            "Target tier",
            choices=valid_tiers,
            default=tier_upper,
        )
    else:
        if not spec_id or not title:
            console.print("[red]Error: --spec-id and --title are required in non-interactive mode[/red]")
            raise typer.Exit(code=1)

    # Validate spec_id format
    if not re.match(r"^SPEC-\d{4}$", spec_id):
        console.print(f"[red]Error: Invalid spec_id format '{spec_id}'. Expected SPEC-XXXX[/red]")
        raise typer.Exit(code=1)

    # Generate filename
    title_slug = re.sub(r"[^a-zA-Z0-9]+", "-", title).strip("-")
    filename = f"{spec_id}-{title_slug}.md"

    # Determine output path
    if path.is_dir():
        output_path = path / filename
    else:
        output_path = path

    if output_path.exists():
        if not Confirm.ask(f"[yellow]File {output_path} already exists. Overwrite?[/yellow]"):
            console.print("[dim]Cancelled.[/dim]")
            raise typer.Exit(code=0)

    # Generate spec content
    today = datetime.now().strftime("%Y-%m-%d")
    spec_content = f'''---
spec_id: {spec_id}
title: "{title}"
version: "1.0.0"
status: DRAFT
tier:
  - {tier_upper}
owner: "<owner-name>"
last_updated: "{today}"
pillar:
  - "Pillar 7 - Quality Assurance"
tags:
  - specification
related_adrs: []
related_specs: []
author: "<author-name>"
created: "{today}"
---

# {spec_id}: {title}

## 1. Executive Summary

<!-- Brief overview of this specification (2-3 sentences) -->

## 2. Problem Statement

<!-- What problem does this specification address? -->

## 3. Scope

### 3.1 In Scope

-

### 3.2 Out of Scope

-

## 4. Functional Requirements

### FR-001: <Requirement Name>

**Description**: <Description>

**BDD Specification**:
```gherkin
GIVEN <precondition>
WHEN <action>
THEN <expected result>
```

**Acceptance Criteria**:
- [ ] AC-001: <Criterion>

### FR-002: <Requirement Name>

**Description**: <Description>

**BDD Specification**:
```gherkin
GIVEN <precondition>
WHEN <action>
THEN <expected result>
```

**Acceptance Criteria**:
- [ ] AC-002: <Criterion>

## 5. Non-Functional Requirements

### NFR-001: Performance

-

### NFR-002: Security

-

## 6. Tier-Specific Requirements

### {tier_upper} Tier

<!-- Requirements specific to this tier -->

## 7. Acceptance Criteria

| ID | Criterion | Expected Result | Test Method | Priority |
|----|-----------|-----------------|-------------|----------|
| AC-001 | | | | P0 |
| AC-002 | | | | P1 |
| AC-003 | | | | P1 |
| AC-004 | | | | P2 |
| AC-005 | | | | P2 |

## 8. Dependencies

### 8.1 Technical Dependencies

-

### 8.2 Related Specifications

-

## 9. Appendices

### A. Glossary

| Term | Definition |
|------|------------|
| | |

### B. References

- SDLC 6.0.0 Framework
- SPEC-0002 Specification Standard

---

**Document Status**: DRAFT
**Last Review**: {today}
**Next Review**: <date>
'''

    # Write file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(spec_content, encoding="utf-8")

    console.print(f"[green]✅ Created specification: {output_path}[/green]")
    console.print(f"[dim]   Spec ID: {spec_id}[/dim]")
    console.print(f"[dim]   Title: {title}[/dim]")
    console.print(f"[dim]   Tier: {tier_upper}[/dim]")
    console.print()
    console.print("[dim]Next steps:[/dim]")
    console.print("  1. Fill in the specification content")
    console.print("  2. Run: sdlcctl spec validate " + str(output_path))


@app.command("convert")
def convert_spec(
    path: Path = typer.Argument(
        Path("."),
        help="Path to OpenSpec proposals directory or file",
        exists=True,
    ),
    from_format: str = typer.Option(
        "openspec",
        "--from",
        "-f",
        help="Source format (currently only 'openspec' supported)",
    ),
    output_dir: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output directory for converted specs",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        "-d",
        help="Show what would be converted without writing files",
    ),
) -> None:
    """
    Convert specifications from other formats to SDLC 6.0.0.

    Currently supports converting from OpenSpec (.openspec/proposals/) format.

    Examples:
        sdlcctl spec convert --from openspec .openspec/proposals/
        sdlcctl spec convert --from openspec .openspec/proposals/ --output docs/02-design/14-Technical-Specs/
        sdlcctl spec convert --from openspec .openspec/proposals/ --dry-run
    """
    if from_format.lower() != "openspec":
        console.print(f"[red]Error: Unsupported format '{from_format}'. Currently only 'openspec' is supported.[/red]")
        raise typer.Exit(code=1)

    # Find OpenSpec proposal files
    if path.is_file():
        proposal_files = [path] if path.suffix in [".md", ".yaml", ".yml"] else []
    else:
        proposal_files = list(path.glob("*.md")) + list(path.glob("*.yaml")) + list(path.glob("*.yml"))

    if not proposal_files:
        console.print("[yellow]No OpenSpec proposal files found.[/yellow]")
        raise typer.Exit(code=0)

    console.print(f"[bold]Found {len(proposal_files)} OpenSpec proposal(s) to convert[/bold]")
    console.print()

    converted_count = 0
    failed_count = 0

    for proposal_file in proposal_files:
        try:
            # Read OpenSpec proposal
            content = proposal_file.read_text(encoding="utf-8")

            # Parse OpenSpec format
            openspec_data = _parse_openspec(content, proposal_file)

            if not openspec_data:
                console.print(f"[yellow]⚠️  Skipping {proposal_file.name}: Could not parse OpenSpec format[/yellow]")
                failed_count += 1
                continue

            # Generate SDLC 6.0.0 spec
            spec_id = openspec_data.get("spec_id", f"SPEC-{converted_count + 1:04d}")
            title = openspec_data.get("title", proposal_file.stem)
            spec_content = _generate_sdlc_spec_from_openspec(openspec_data)

            # Determine output path
            title_slug = re.sub(r"[^a-zA-Z0-9]+", "-", title).strip("-")
            output_filename = f"{spec_id}-{title_slug}.md"

            if output_dir:
                output_path = output_dir / output_filename
            else:
                output_path = proposal_file.parent / "converted" / output_filename

            if dry_run:
                console.print(f"[cyan]Would convert: {proposal_file.name} → {output_path}[/cyan]")
            else:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text(spec_content, encoding="utf-8")
                console.print(f"[green]✅ Converted: {proposal_file.name} → {output_path}[/green]")

            converted_count += 1

        except Exception as e:
            console.print(f"[red]❌ Failed to convert {proposal_file.name}: {e}[/red]")
            failed_count += 1

    console.print()
    console.print(f"[bold]Conversion complete:[/bold]")
    console.print(f"  ✅ Converted: {converted_count}")
    console.print(f"  ❌ Failed: {failed_count}")

    if not dry_run and converted_count > 0:
        console.print()
        console.print("[dim]Next steps:[/dim]")
        console.print("  1. Review converted specifications")
        console.print("  2. Run: sdlcctl spec validate <output-dir>")


def _parse_openspec(content: str, file_path: Path) -> Optional[Dict[str, Any]]:
    """
    Parse OpenSpec proposal format.

    Args:
        content: File content
        file_path: Source file path

    Returns:
        Parsed OpenSpec data or None if parsing fails
    """
    result: Dict[str, Any] = {}

    # Try YAML frontmatter first
    frontmatter_match = re.match(
        r"^---[ \t]*\n(.*?)(?:\n)?---[ \t]*\n(.*)",
        content,
        re.MULTILINE | re.DOTALL,
    )

    if frontmatter_match:
        try:
            frontmatter = yaml.safe_load(frontmatter_match.group(1))
            if isinstance(frontmatter, dict):
                result.update(frontmatter)
            result["body"] = frontmatter_match.group(2)
        except yaml.YAMLError:
            pass

    # Try to extract title from first H1
    title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    if title_match and "title" not in result:
        result["title"] = title_match.group(1).strip()

    # Try to extract ID from filename or title
    id_match = re.search(r"(\d{4})", file_path.stem)
    if id_match:
        result["spec_id"] = f"SPEC-{id_match.group(1)}"
    elif "spec_id" not in result:
        result["spec_id"] = "SPEC-0000"

    # Extract sections
    result["sections"] = _extract_sections(content)

    return result if result.get("title") or result.get("body") else None


def _extract_sections(content: str) -> Dict[str, str]:
    """Extract markdown sections from content."""
    sections = {}
    current_section = "intro"
    current_content = []

    for line in content.split("\n"):
        if line.startswith("## "):
            if current_content:
                sections[current_section] = "\n".join(current_content).strip()
            current_section = line[3:].strip().lower().replace(" ", "_")
            current_content = []
        else:
            current_content.append(line)

    if current_content:
        sections[current_section] = "\n".join(current_content).strip()

    return sections


def _generate_sdlc_spec_from_openspec(data: Dict[str, Any]) -> str:
    """
    Generate SDLC 6.0.0 specification from OpenSpec data.

    Args:
        data: Parsed OpenSpec data

    Returns:
        SDLC 6.0.0 compliant specification content
    """
    today = datetime.now().strftime("%Y-%m-%d")
    spec_id = data.get("spec_id", "SPEC-0000")
    title = data.get("title", "Untitled Specification")
    version = data.get("version", "1.0.0")
    status = data.get("status", "DRAFT")
    tier = data.get("tier", ["PROFESSIONAL"])
    if isinstance(tier, str):
        tier = [tier]
    owner = data.get("owner", "<owner-name>")
    sections = data.get("sections", {})
    body = data.get("body", "")

    # Build tier YAML
    tier_yaml = "\n".join(f"  - {t}" for t in tier)

    spec_content = f'''---
spec_id: {spec_id}
title: "{title}"
version: "{version}"
status: {status}
tier:
{tier_yaml}
owner: "{owner}"
last_updated: "{today}"
pillar:
  - "Pillar 7 - Quality Assurance"
tags:
  - specification
  - converted-from-openspec
related_adrs: []
related_specs: []
author: "<author-name>"
created: "{today}"
---

# {spec_id}: {title}

'''

    # Add body content or sections
    if body:
        spec_content += body
    elif sections:
        for section_name, section_content in sections.items():
            if section_name != "intro":
                spec_content += f"\n## {section_name.replace('_', ' ').title()}\n\n{section_content}\n"
            else:
                spec_content += f"{section_content}\n"

    # Add standard sections if missing
    if "acceptance_criteria" not in sections and "acceptance criteria" not in body.lower():
        spec_content += '''

## Acceptance Criteria

| ID | Criterion | Expected Result | Test Method | Priority |
|----|-----------|-----------------|-------------|----------|
| AC-001 | | | | P0 |
| AC-002 | | | | P1 |
| AC-003 | | | | P1 |
| AC-004 | | | | P2 |
| AC-005 | | | | P2 |
'''

    spec_content += f'''

---

**Document Status**: {status}
**Converted From**: OpenSpec
**Conversion Date**: {today}
'''

    return spec_content


# ============================================================================
# Output Formatters
# ============================================================================


def _output_text(result: ScanResult, strict: bool = False) -> None:
    """Output results in text format."""
    # Summary
    console.print(f"[bold]Scan Results for: {result.scan_path}[/bold]")
    console.print(f"Files scanned: {result.files_scanned}")
    console.print(f"Scan time: {result.scan_time_ms:.2f}ms")
    console.print()

    # Summary table
    summary_table = Table(title="Summary")
    summary_table.add_column("Severity", style="bold")
    summary_table.add_column("Count", justify="right")

    summary_table.add_row("❌ Errors", str(result.error_count), style="red" if result.error_count > 0 else "dim")
    summary_table.add_row("⚠️  Warnings", str(result.warning_count), style="yellow" if result.warning_count > 0 else "dim")
    summary_table.add_row("ℹ️  Info", str(result.info_count), style="blue" if result.info_count > 0 else "dim")
    summary_table.add_row("🔧 Auto-fixable", str(result.auto_fixable_count), style="cyan" if result.auto_fixable_count > 0 else "dim")

    console.print(summary_table)
    console.print()

    # Violations
    if result.violations:
        console.print("[bold]Violations:[/bold]")
        for v in result.violations:
            if v.severity == Severity.ERROR:
                icon = "❌"
                style = "red"
            elif v.severity == Severity.WARNING:
                icon = "⚠️"
                style = "yellow"
            else:
                icon = "ℹ️"
                style = "blue"

            console.print(f"  {icon} [{style}]{v.severity.value}[/{style}] [{v.rule_id}] {v.file_path.name}")
            console.print(f"      {v.message}")
            if v.fix_suggestion:
                console.print(f"      [dim]💡 {v.fix_suggestion.split(chr(10))[0]}[/dim]")
            console.print()
    else:
        console.print("[green]✅ No violations found![/green]")

    # Final status
    console.print()
    if result.passed:
        console.print("[green bold]✅ Specification validation PASSED[/green bold]")
    else:
        console.print("[red bold]❌ Specification validation FAILED[/red bold]")


def _output_json(result: ScanResult) -> None:
    """Output results in JSON format."""
    print(json.dumps(result.to_dict(), indent=2))


def _output_github(result: ScanResult) -> None:
    """Output results in GitHub Actions annotation format."""
    for v in result.violations:
        if v.severity == Severity.ERROR:
            level = "error"
        elif v.severity == Severity.WARNING:
            level = "warning"
        else:
            level = "notice"

        file_path = str(v.file_path)
        print(f"::{level} file={file_path}::[{v.rule_id}] {v.message}")


def _generate_text_report(result: ScanResult) -> str:
    """Generate text report."""
    lines = [
        "=" * 60,
        "SDLC Specification Compliance Report",
        "=" * 60,
        "",
        f"Scan Path: {result.scan_path}",
        f"Files Scanned: {result.files_scanned}",
        f"Scan Time: {result.scan_time_ms:.2f}ms",
        "",
        "Summary:",
        f"  Errors: {result.error_count}",
        f"  Warnings: {result.warning_count}",
        f"  Info: {result.info_count}",
        f"  Auto-fixable: {result.auto_fixable_count}",
        "",
        f"Status: {'PASSED' if result.passed else 'FAILED'}",
        "",
    ]

    if result.violations:
        lines.append("Violations:")
        lines.append("-" * 40)
        for v in result.violations:
            lines.append(f"  [{v.severity.value}] {v.rule_id}")
            lines.append(f"    File: {v.file_path}")
            lines.append(f"    Message: {v.message}")
            if v.fix_suggestion:
                lines.append(f"    Suggestion: {v.fix_suggestion.split(chr(10))[0]}")
            lines.append("")

    return "\n".join(lines)


def _generate_markdown_report(result: ScanResult) -> str:
    """Generate markdown report."""
    lines = [
        "# SDLC Specification Compliance Report",
        "",
        "## Summary",
        "",
        f"- **Scan Path**: `{result.scan_path}`",
        f"- **Files Scanned**: {result.files_scanned}",
        f"- **Scan Time**: {result.scan_time_ms:.2f}ms",
        f"- **Status**: {'✅ PASSED' if result.passed else '❌ FAILED'}",
        "",
        "### Violation Summary",
        "",
        "| Severity | Count |",
        "|----------|-------|",
        f"| ❌ Errors | {result.error_count} |",
        f"| ⚠️ Warnings | {result.warning_count} |",
        f"| ℹ️ Info | {result.info_count} |",
        f"| 🔧 Auto-fixable | {result.auto_fixable_count} |",
        "",
    ]

    if result.violations:
        lines.extend([
            "## Violations",
            "",
            "| Rule | Severity | File | Message |",
            "|------|----------|------|---------|",
        ])
        for v in result.violations:
            file_name = v.file_path.name
            message = v.message.replace("|", "\\|")
            lines.append(f"| {v.rule_id} | {v.severity.value} | `{file_name}` | {message} |")

    return "\n".join(lines)


# ============================================================================
# Entry Point
# ============================================================================

if __name__ == "__main__":
    app()
