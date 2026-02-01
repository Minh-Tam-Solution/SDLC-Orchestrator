"""
Specifications Management Checker - Sprint 123 (SPEC-0013)

Validates SDLC 6.0.0 specification management:
1. Specs in correct location (docs/02-design/14-Technical-Specs/)
2. YAML frontmatter present and valid
3. SPEC-XXXX ID format
4. Required fields present (status, version, author)
"""

import re
from typing import Optional
from uuid import UUID

from app.models.compliance_validation import ComplianceCategory, IssueSeverity
from app.services.validation.checkers.base import (
    BaseCategoryChecker,
    CategoryCheckResult,
    CheckIssue,
)


class SpecificationsManagementChecker(BaseCategoryChecker):
    """
    Specifications Management Checker (10 points).

    Validates:
    1. Specs location (docs/02-design/14-Technical-Specs/)
    2. YAML frontmatter structure
    3. SPEC-XXXX numbering format
    4. Required metadata fields
    """

    category = ComplianceCategory.SPECIFICATIONS_MANAGEMENT

    SPECS_PATH = "docs/02-design/14-Technical-Specs/"
    SPEC_ID_PATTERN = re.compile(r"^SPEC-\d{4}$")
    REQUIRED_FRONTMATTER = ["spec_id", "title", "version", "status"]
    VALID_STATUSES = ["DRAFT", "REVIEW", "APPROVED", "CTO_APPROVED", "DEPRECATED"]

    async def check(self, project_id: UUID) -> CategoryCheckResult:
        """
        Check specifications management compliance.

        Args:
            project_id: Project UUID

        Returns:
            CategoryCheckResult with score and issues
        """
        issues: list[CheckIssue] = []
        passed_checks: list[str] = []
        checks_performed = 0

        # Get all spec files
        spec_files = await self.file_service.list_files(
            project_id=project_id,
            path=self.SPECS_PATH,
            pattern="*.md",
        )

        if not spec_files:
            # No specs found - might be intentional for small projects
            checks_performed = 1
            issues.append(self._create_issue(
                severity=IssueSeverity.INFO,
                issue_code="NO_SPECS_FOUND",
                message=f"No specification files found in {self.SPECS_PATH}",
                file_path=self.SPECS_PATH,
                fix_suggestion="Create specs using: sdlcctl spec create --name my-feature",
            ))
            return self._create_result(issues, passed_checks, checks_performed)

        # Check each spec file
        for spec_file in spec_files:
            checks_performed += 1
            file_path = f"{self.SPECS_PATH}{spec_file}"

            # Read file content
            content = await self.file_service.read_file(
                project_id=project_id,
                path=file_path,
            )

            if not content:
                issues.append(self._create_issue(
                    severity=IssueSeverity.WARNING,
                    issue_code="SPEC_UNREADABLE",
                    message=f"Cannot read spec file: {spec_file}",
                    file_path=file_path,
                ))
                continue

            # Check YAML frontmatter
            frontmatter = self._extract_frontmatter(content)
            if frontmatter is None:
                issues.append(self._create_issue(
                    severity=IssueSeverity.WARNING,
                    issue_code="MISSING_YAML_FRONTMATTER",
                    message=f"Missing YAML frontmatter in spec: {spec_file}",
                    file_path=file_path,
                    fix_suggestion="Add YAML frontmatter between --- markers at file start",
                    fix_command=f"sdlcctl spec fix --frontmatter {file_path}",
                    auto_fixable=True,
                ))
                continue

            # Validate required fields
            missing_fields = [
                f for f in self.REQUIRED_FRONTMATTER
                if f not in frontmatter
            ]

            if missing_fields:
                issues.append(self._create_issue(
                    severity=IssueSeverity.WARNING,
                    issue_code="MISSING_FRONTMATTER_FIELDS",
                    message=f"Missing fields in {spec_file}: {', '.join(missing_fields)}",
                    file_path=file_path,
                    fix_suggestion=f"Add missing fields: {', '.join(missing_fields)}",
                    context={"missing_fields": missing_fields},
                ))
            else:
                # Validate spec_id format
                spec_id = frontmatter.get("spec_id", "")
                if not self.SPEC_ID_PATTERN.match(spec_id):
                    issues.append(self._create_issue(
                        severity=IssueSeverity.WARNING,
                        issue_code="INVALID_SPEC_ID",
                        message=f"Invalid spec_id format in {spec_file}: {spec_id}",
                        file_path=file_path,
                        fix_suggestion="Use format: SPEC-XXXX (e.g., SPEC-0013)",
                    ))
                else:
                    passed_checks.append(f"Spec {spec_id} has valid frontmatter")

                # Validate status
                status = frontmatter.get("status", "")
                if status not in self.VALID_STATUSES:
                    issues.append(self._create_issue(
                        severity=IssueSeverity.INFO,
                        issue_code="INVALID_SPEC_STATUS",
                        message=f"Unknown status in {spec_file}: {status}",
                        file_path=file_path,
                        fix_suggestion=f"Use valid status: {', '.join(self.VALID_STATUSES)}",
                    ))

        # Check for specs outside designated folder
        checks_performed += 1
        other_specs = await self.file_service.find_files(
            project_id=project_id,
            pattern="**/SPEC-*.md",
            exclude_path=self.SPECS_PATH,
        )

        if not other_specs:
            passed_checks.append("All specs in correct location")
        else:
            for spec in other_specs:
                issues.append(self._create_issue(
                    severity=IssueSeverity.WARNING,
                    issue_code="SPEC_WRONG_LOCATION",
                    message=f"Spec found outside designated folder: {spec}",
                    file_path=spec,
                    fix_suggestion=f"Move to: {self.SPECS_PATH}",
                    fix_command=f"mv {spec} {self.SPECS_PATH}",
                    auto_fixable=True,
                ))

        return self._create_result(
            issues=issues,
            passed_checks=passed_checks,
            checks_performed=checks_performed,
        )

    def _extract_frontmatter(self, content: str) -> Optional[dict]:
        """Extract YAML frontmatter from markdown content."""
        if not content.startswith("---"):
            return None

        parts = content.split("---", 2)
        if len(parts) < 3:
            return None

        try:
            import yaml
            return yaml.safe_load(parts[1])
        except Exception:
            return None
