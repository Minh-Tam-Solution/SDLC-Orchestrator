"""
Team Organization Checker - Sprint 123 (SPEC-0013)

Validates team structure and SDLC Compliance Hub.
"""

from uuid import UUID

from app.models.compliance_validation import ComplianceCategory, IssueSeverity
from app.services.validation.checkers.base import (
    BaseCategoryChecker,
    CategoryCheckResult,
    CheckIssue,
)


class TeamOrganizationChecker(BaseCategoryChecker):
    """Team Organization Checker (10 points)."""

    category = ComplianceCategory.TEAM_ORGANIZATION

    COMPLIANCE_HUB_PATHS = [
        "docs/08-collaborate/01-SDLC-Compliance/",
        "docs/08-Team-Management/01-SDLC-Compliance/",
        "docs/08-collaborate/02-SDLC-Compliance/",
    ]

    async def check(self, project_id: UUID) -> CategoryCheckResult:
        """Check team organization compliance."""
        issues: list[CheckIssue] = []
        passed_checks: list[str] = []
        checks_performed = 0

        # Check for SDLC Compliance Hub
        checks_performed += 1
        hub_found = False
        hub_path = None

        for path in self.COMPLIANCE_HUB_PATHS:
            if await self.file_service.directory_exists(project_id, path):
                hub_found = True
                hub_path = path
                break

        if hub_found:
            passed_checks.append(f"SDLC Compliance Hub exists at {hub_path}")

            # Check for common hub files
            hub_files = [
                "MIGRATION-STATUS.md",
                "PM-PJM-REVIEW*.md",
                "GATE-READINESS*.md",
            ]

            for pattern in hub_files:
                checks_performed += 1
                files = await self.file_service.find_files(
                    project_id=project_id,
                    pattern=f"{hub_path}{pattern}",
                )
                if files:
                    passed_checks.append(f"Hub file: {pattern}")
                # Not critical if missing
        else:
            issues.append(self._create_issue(
                severity=IssueSeverity.INFO,
                issue_code="MISSING_TEAM_HUB",
                message="SDLC Compliance Hub folder not found",
                file_path="docs/08-collaborate/01-SDLC-Compliance/",
                fix_suggestion="Create SDLC Compliance Hub for team coordination",
                fix_command="sdlcctl init --compliance-hub",
                auto_fixable=True,
            ))

        # Check for team documentation
        checks_performed += 1
        team_docs = [
            "docs/08-collaborate/",
            "docs/08-Team-Management/",
        ]
        team_folder = None
        for path in team_docs:
            if await self.file_service.directory_exists(project_id, path):
                team_folder = path
                break

        if team_folder:
            passed_checks.append(f"Team folder exists: {team_folder}")
        else:
            issues.append(self._create_issue(
                severity=IssueSeverity.WARNING,
                issue_code="MISSING_TEAM_FOLDER",
                message="Team management folder (08-collaborate) not found",
                file_path="docs/",
                fix_suggestion="Create docs/08-collaborate/ for team documentation",
            ))

        return self._create_result(issues, passed_checks, checks_performed)
