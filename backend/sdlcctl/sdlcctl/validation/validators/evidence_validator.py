"""
Implementation Evidence Validator

Validates that spec evidence files match actual implementation on disk.
Detects context drift between design (SPEC/ADR) and implementation (code files).

Part of SPEC-0016: Implementation Evidence Validation
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import jsonschema
from jsonschema import ValidationError as JSONSchemaValidationError

from ..base_validator import BaseValidator
from ..violation import ViolationReport, Severity

logger = logging.getLogger(__name__)


class EvidenceValidator(BaseValidator):
    """
    Validates implementation evidence files against JSON schema and file existence.

    Evidence files prove that a SPEC or ADR has been implemented across all interfaces:
    - Backend (API routes, services, models, tests)
    - Frontend (components, pages, hooks, tests)
    - Extension (commands, services, views)
    - CLI (commands, services, tests)

    Detects context drift when:
    - Evidence file references non-existent files
    - Evidence file is missing for a SPEC/ADR
    - Implementation is incomplete (missing required files)
    """

    VALIDATOR_NAME = "Implementation Evidence Validator"
    VALIDATOR_ID = "evidence"

    def __init__(self, project_root: Path):
        """
        Initialize evidence validator.

        Args:
            project_root: Root directory of SDLC project
        """
        super().__init__(project_root)
        self.project_root = project_root  # Store for use in validation methods
        self.schema_path = project_root / "backend/sdlcctl/sdlcctl/schemas/spec-evidence-schema.json"
        self.schema: Optional[Dict[str, Any]] = None
        self._load_schema()

    def _load_schema(self) -> None:
        """Load JSON schema for evidence files."""
        try:
            if self.schema_path.exists():
                with open(self.schema_path, 'r', encoding='utf-8') as f:
                    self.schema = json.load(f)
                logger.debug(f"Loaded evidence schema from {self.schema_path}")
            else:
                logger.warning(f"Evidence schema not found at {self.schema_path}")
                self.schema = None
        except Exception as e:
            logger.error(f"Failed to load evidence schema: {e}")
            self.schema = None

    def validate(self) -> List[ViolationReport]:
        """
        Validate all evidence files in the project.

        Returns:
            List of violations found
        """
        violations: List[ViolationReport] = []

        # Find all evidence files (docs/**/*-evidence.json)
        evidence_pattern = "docs/**/*-evidence.json"
        evidence_files = list(self.project_root.glob(evidence_pattern))

        if not evidence_files:
            violations.append(
                ViolationReport(
                    rule_id="EVIDENCE-001",
                    severity=Severity.WARNING,
                    message="No evidence files found in project",
                    file_path="docs/",
                    fix_suggestion="Create evidence files for implemented specs using: sdlcctl evidence create SPEC-00XX"
                )
            )
            return violations

        logger.info(f"Found {len(evidence_files)} evidence files to validate")

        # Validate each evidence file
        for evidence_file in evidence_files:
            violations.extend(self._validate_evidence_file(evidence_file))

        # Check for SPECs/ADRs without evidence files
        violations.extend(self._check_missing_evidence())

        return violations

    def _validate_evidence_file(self, evidence_file: Path) -> List[ViolationReport]:
        """
        Validate a single evidence file.

        Args:
            evidence_file: Path to evidence JSON file

        Returns:
            List of violations found
        """
        violations: List[ViolationReport] = []
        relative_path = evidence_file.relative_to(self.project_root)

        try:
            # Load JSON file
            with open(evidence_file, 'r', encoding='utf-8') as f:
                evidence_data = json.load(f)

            # Validate against JSON schema
            schema_violations = self._validate_schema(evidence_data, relative_path)
            violations.extend(schema_violations)

            # Validate file existence
            file_violations = self._validate_file_existence(evidence_data, relative_path)
            violations.extend(file_violations)

            # Validate test coverage (backend, frontend, extension must have tests)
            test_violations = self._validate_test_coverage(evidence_data, relative_path)
            violations.extend(test_violations)

        except json.JSONDecodeError as e:
            violations.append(
                ViolationReport(
                    rule_id="EVIDENCE-002",
                    severity=Severity.ERROR,
                    message=f"Invalid JSON in evidence file: {e.msg}",
                    file_path=str(relative_path),
                    line_number=e.lineno,
                    fix_suggestion="Fix JSON syntax errors"
                )
            )
        except Exception as e:
            violations.append(
                ViolationReport(
                    rule_id="EVIDENCE-003",
                    severity=Severity.ERROR,
                    message=f"Failed to validate evidence file: {str(e)}",
                    file_path=str(relative_path),
                    fix_suggestion="Check file format and permissions"
                )
            )

        return violations

    def _validate_schema(
        self,
        evidence_data: Dict[str, Any],
        relative_path: Path
    ) -> List[ViolationReport]:
        """
        Validate evidence data against JSON schema.

        Args:
            evidence_data: Parsed evidence JSON
            relative_path: Relative path to evidence file

        Returns:
            List of schema violations
        """
        violations: List[ViolationReport] = []

        if not self.schema:
            violations.append(
                ViolationReport(
                    rule_id="EVIDENCE-004",
                    severity=Severity.WARNING,
                    message="Evidence schema not loaded, skipping validation",
                    file_path=str(relative_path),
                    fix_suggestion="Ensure spec-evidence-schema.json exists"
                )
            )
            return violations

        try:
            jsonschema.validate(instance=evidence_data, schema=self.schema)
        except JSONSchemaValidationError as e:
            violations.append(
                ViolationReport(
                    rule_id="EVIDENCE-005",
                    severity=Severity.ERROR,
                    message=f"Schema validation failed: {e.message}",
                    file_path=str(relative_path),
                    fix_suggestion=f"Fix schema violation: {e.json_path}"
                )
            )

        return violations

    def _validate_file_existence(
        self,
        evidence_data: Dict[str, Any],
        relative_path: Path
    ) -> List[ViolationReport]:
        """
        Validate that all files referenced in evidence exist on disk.

        Args:
            evidence_data: Parsed evidence JSON
            relative_path: Relative path to evidence file

        Returns:
            List of file existence violations
        """
        violations: List[ViolationReport] = []
        spec_id = evidence_data.get("spec_id", "Unknown")
        interfaces = evidence_data.get("interfaces", {})

        # Track all referenced files for summary
        missing_files: List[str] = []

        # Check backend files
        backend = interfaces.get("backend", {})
        for category in ["api_routes", "services", "models", "schemas", "tests", "migrations"]:
            files = backend.get(category, [])
            for file_path in files:
                if not self._file_exists(file_path):
                    missing_files.append(file_path)
                    violations.append(
                        ViolationReport(
                            rule_id="EVIDENCE-006",
                            severity=Severity.ERROR,
                            message=f"Backend {category} file not found: {file_path}",
                            file_path=str(relative_path),
                            fix_suggestion=f"Implement {file_path} or remove from evidence"
                        )
                    )

        # Check frontend files
        frontend = interfaces.get("frontend", {})
        for category in ["components", "pages", "hooks", "api_client", "tests"]:
            files = frontend.get(category, [])
            for file_path in files:
                if not self._file_exists(file_path):
                    missing_files.append(file_path)
                    violations.append(
                        ViolationReport(
                            rule_id="EVIDENCE-007",
                            severity=Severity.ERROR,
                            message=f"Frontend {category} file not found: {file_path}",
                            file_path=str(relative_path),
                            fix_suggestion=f"Implement {file_path} or remove from evidence"
                        )
                    )

        # Check extension files
        extension = interfaces.get("extension", {})
        for category in ["commands", "services", "views", "package_json", "tests"]:
            files = extension.get(category, [])
            for file_path in files:
                if not self._file_exists(file_path):
                    missing_files.append(file_path)
                    violations.append(
                        ViolationReport(
                            rule_id="EVIDENCE-008",
                            severity=Severity.ERROR,
                            message=f"Extension {category} file not found: {file_path}",
                            file_path=str(relative_path),
                            fix_suggestion=f"Implement {file_path} or remove from evidence"
                        )
                    )

        # Check CLI files
        cli = interfaces.get("cli", {})
        for category in ["commands", "services", "tests"]:
            files = cli.get(category, [])
            for file_path in files:
                if not self._file_exists(file_path):
                    missing_files.append(file_path)
                    violations.append(
                        ViolationReport(
                            rule_id="EVIDENCE-009",
                            severity=Severity.ERROR,
                            message=f"CLI {category} file not found: {file_path}",
                            file_path=str(relative_path),
                            fix_suggestion=f"Implement {file_path} or remove from evidence"
                        )
                    )

        # Update validation metadata if missing files found
        if missing_files:
            self._update_validation_metadata(
                evidence_data,
                relative_path,
                status="partial",
                missing_files=missing_files
            )

        return violations

    def _validate_test_coverage(
        self,
        evidence_data: Dict[str, Any],
        relative_path: Path
    ) -> List[ViolationReport]:
        """
        Validate that required interfaces have test coverage.

        Args:
            evidence_data: Parsed evidence JSON
            relative_path: Relative path to evidence file

        Returns:
            List of test coverage violations
        """
        violations: List[ViolationReport] = []
        spec_id = evidence_data.get("spec_id", "Unknown")
        interfaces = evidence_data.get("interfaces", {})

        # Backend tests are MANDATORY (per schema required field)
        backend = interfaces.get("backend", {})
        if backend and not backend.get("tests"):
            violations.append(
                ViolationReport(
                    rule_id="EVIDENCE-010",
                    severity=Severity.ERROR,
                    message=f"{spec_id}: Backend implementation missing tests (MANDATORY)",
                    file_path=str(relative_path),
                    fix_suggestion="Add backend/tests/**/*.py files with pytest coverage"
                )
            )

        # Frontend tests recommended but not mandatory
        frontend = interfaces.get("frontend", {})
        if frontend and not frontend.get("tests"):
            violations.append(
                ViolationReport(
                    rule_id="EVIDENCE-011",
                    severity=Severity.WARNING,
                    message=f"{spec_id}: Frontend implementation missing tests (RECOMMENDED)",
                    file_path=str(relative_path),
                    fix_suggestion="Add frontend tests with Vitest + React Testing Library"
                )
            )

        # Extension tests recommended but not mandatory
        extension = interfaces.get("extension", {})
        if extension and not extension.get("tests"):
            violations.append(
                ViolationReport(
                    rule_id="EVIDENCE-012",
                    severity=Severity.WARNING,
                    message=f"{spec_id}: Extension implementation missing tests (RECOMMENDED)",
                    file_path=str(relative_path),
                    fix_suggestion="Add extension tests in vscode-extension/src/test/"
                )
            )

        # CLI tests recommended but not mandatory
        cli = interfaces.get("cli", {})
        if cli and not cli.get("tests"):
            violations.append(
                ViolationReport(
                    rule_id="EVIDENCE-013",
                    severity=Severity.WARNING,
                    message=f"{spec_id}: CLI implementation missing tests (RECOMMENDED)",
                    file_path=str(relative_path),
                    fix_suggestion="Add CLI tests in backend/sdlcctl/tests/"
                )
            )

        return violations

    def _check_missing_evidence(self) -> List[ViolationReport]:
        """
        Check for SPEC and ADR files without corresponding evidence files.

        Returns:
            List of violations for missing evidence
        """
        violations: List[ViolationReport] = []

        # Find all SPEC and ADR files
        spec_pattern = "docs/02-design/14-Technical-Specs/SPEC-*.md"
        adr_pattern = "docs/02-design/01-ADRs/ADR-*.md"

        spec_files = list(self.project_root.glob(spec_pattern))
        adr_files = list(self.project_root.glob(adr_pattern))

        all_design_docs = spec_files + adr_files

        # Check each design doc for evidence file
        for doc_file in all_design_docs:
            evidence_file = doc_file.with_suffix('.md').parent / f"{doc_file.stem}-evidence.json"

            if not evidence_file.exists():
                violations.append(
                    ViolationReport(
                        rule_id="EVIDENCE-014",
                        severity=Severity.WARNING,
                        message=f"Missing evidence file for {doc_file.name}",
                        file_path=str(doc_file.relative_to(self.project_root)),
                        fix_suggestion=f"Create {evidence_file.name} using: sdlcctl evidence create {doc_file.stem}"
                    )
                )

        return violations

    def _file_exists(self, file_path: str) -> bool:
        """
        Check if a file exists relative to project root.

        Args:
            file_path: Relative path to file (e.g., "backend/app/api/routes/invitations.py")

        Returns:
            True if file exists, False otherwise
        """
        full_path = self.project_root / file_path
        return full_path.exists()

    def _update_validation_metadata(
        self,
        evidence_data: Dict[str, Any],
        relative_path: Path,
        status: str,
        missing_files: Optional[List[str]] = None,
        warnings: Optional[List[str]] = None
    ) -> None:
        """
        Update validation metadata in evidence file.

        Args:
            evidence_data: Parsed evidence JSON
            relative_path: Relative path to evidence file
            status: Validation status (complete, partial, missing)
            missing_files: List of missing files
            warnings: List of warnings
        """
        validation = evidence_data.get("validation", {})
        validation["last_checked"] = datetime.utcnow().isoformat() + "Z"
        validation["checker_version"] = "1.0.0"  # TODO: Get from package version
        validation["status"] = status

        if missing_files:
            validation["missing_files"] = missing_files

        if warnings:
            validation["warnings"] = warnings

        evidence_data["validation"] = validation

        # Write updated evidence back to file
        try:
            full_path = self.project_root / relative_path
            with open(full_path, 'w', encoding='utf-8') as f:
                json.dump(evidence_data, f, indent=2, ensure_ascii=False)
                f.write('\n')  # Add trailing newline
            logger.debug(f"Updated validation metadata in {relative_path}")
        except Exception as e:
            logger.error(f"Failed to update validation metadata: {e}")


def validate_evidence(project_root: Path) -> Tuple[List[ViolationReport], Dict[str, Any]]:
    """
    Validate all evidence files in a project.

    Args:
        project_root: Root directory of SDLC project

    Returns:
        Tuple of (violations, summary_stats)
    """
    validator = EvidenceValidator(project_root)
    violations = validator.validate()

    # Calculate summary statistics
    total_violations = len(violations)
    errors = [v for v in violations if v.severity == "error"]
    warnings = [v for v in violations if v.severity == "warning"]

    # Count violations by rule
    violations_by_rule: Dict[str, int] = {}
    for violation in violations:
        violations_by_rule[violation.rule_id] = violations_by_rule.get(violation.rule_id, 0) + 1

    summary = {
        "total_violations": total_violations,
        "errors": len(errors),
        "warnings": len(warnings),
        "violations_by_rule": violations_by_rule,
    }

    return violations, summary
