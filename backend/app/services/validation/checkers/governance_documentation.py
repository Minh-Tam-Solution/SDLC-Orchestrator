"""
Governance Documentation Checker - Sprint 123 (SPEC-0013)

Validates governance documentation (CEO/CTO approvals, ADRs).
"""

from uuid import UUID

from app.models.compliance_validation import ComplianceCategory, IssueSeverity
from app.services.validation.checkers.base import (
    BaseCategoryChecker,
    CategoryCheckResult,
    CheckIssue,
)


class GovernanceDocumentationChecker(BaseCategoryChecker):
    """Governance Documentation Checker (10 points)."""

    category = ComplianceCategory.GOVERNANCE_DOCUMENTATION

    ADR_PATHS = [
        "docs/02-design/01-ADRs/",
        "docs/02-design/03-ADRs/",
    ]

    async def check(self, project_id: UUID) -> CategoryCheckResult:
        """Check governance documentation compliance."""
        issues: list[CheckIssue] = []
        passed_checks: list[str] = []
        checks_performed = 0

        # Check for ADR folder
        checks_performed += 1
        adr_folder = None

        for path in self.ADR_PATHS:
            if await self.file_service.directory_exists(project_id, path):
                adr_folder = path
                break

        if adr_folder:
            passed_checks.append(f"ADR folder exists: {adr_folder}")

            # Count ADRs
            checks_performed += 1
            adrs = await self.file_service.find_files(
                project_id=project_id,
                pattern=f"{adr_folder}ADR-*.md",
            )

            if adrs and len(adrs) >= 1:
                passed_checks.append(f"ADRs documented: {len(adrs)} ADRs")
            else:
                issues.append(self._create_issue(
                    severity=IssueSeverity.INFO,
                    issue_code="NO_ADRS_FOUND",
                    message="No ADR documents found",
                    file_path=adr_folder,
                    fix_suggestion="Document architectural decisions as ADR-XXX-title.md",
                ))
        else:
            issues.append(self._create_issue(
                severity=IssueSeverity.WARNING,
                issue_code="MISSING_ADR_FOLDER",
                message="ADR folder not found (docs/02-design/01-ADRs/)",
                file_path="docs/02-design/",
                fix_suggestion="Create ADR folder for architecture decisions",
            ))

        # Check for governance folder (09-govern)
        checks_performed += 1
        govern_exists = await self.file_service.directory_exists(
            project_id, "docs/09-govern/"
        )

        if govern_exists:
            passed_checks.append("Governance folder (09-govern) exists")

            # Check for CTO reports
            checks_performed += 1
            cto_reports = await self.file_service.find_files(
                project_id=project_id,
                pattern="docs/09-govern/**/*CTO*.md",
            )
            if cto_reports:
                passed_checks.append(f"CTO reports found: {len(cto_reports)}")
            # Not critical if missing
        else:
            issues.append(self._create_issue(
                severity=IssueSeverity.INFO,
                issue_code="MISSING_GOVERN_FOLDER",
                message="Governance folder (09-govern) not found",
                file_path="docs/",
            ))

        # Check for PROJECT-KICKOFF.md (CEO/CTO approval)
        checks_performed += 1
        kickoff_paths = [
            "PROJECT-KICKOFF.md",
            "docs/00-discover/PROJECT-KICKOFF.md",
        ]
        kickoff_found = False

        for path in kickoff_paths:
            if await self.file_service.file_exists(project_id, path):
                kickoff_found = True
                passed_checks.append(f"Project kickoff document exists: {path}")
                break

        if not kickoff_found:
            issues.append(self._create_issue(
                severity=IssueSeverity.INFO,
                issue_code="MISSING_PROJECT_KICKOFF",
                message="PROJECT-KICKOFF.md not found",
                file_path="./",
                fix_suggestion="Document CEO/CTO project approval in PROJECT-KICKOFF.md",
            ))

        return self._create_result(issues, passed_checks, checks_performed)
