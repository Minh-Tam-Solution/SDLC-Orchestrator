"""
Legacy Archival Checker - Sprint 123 (SPEC-0013)

Validates proper legacy file archival.
"""

from uuid import UUID

from app.models.compliance_validation import ComplianceCategory, IssueSeverity
from app.services.validation.checkers.base import (
    BaseCategoryChecker,
    CategoryCheckResult,
    CheckIssue,
)


class LegacyArchivalChecker(BaseCategoryChecker):
    """Legacy Archival Checker (10 points)."""

    category = ComplianceCategory.LEGACY_ARCHIVAL

    LEGACY_PATTERNS = ["99-legacy", "99-Legacy", "_legacy", "old_", "deprecated_"]
    ARCHIVE_PATHS = ["docs/10-archive/", "docs/10-Archive/"]

    async def check(self, project_id: UUID) -> CategoryCheckResult:
        """Check legacy archival compliance."""
        issues: list[CheckIssue] = []
        passed_checks: list[str] = []
        checks_performed = 0

        # Check for legacy folders in wrong locations
        checks_performed += 1
        docs_folders = await self.file_service.list_directories(project_id, "docs/")

        legacy_in_wrong_place = []
        for folder in docs_folders:
            folder_lower = folder.lower()
            if any(pat.lower() in folder_lower for pat in self.LEGACY_PATTERNS):
                if not folder.startswith("10-"):
                    legacy_in_wrong_place.append(folder)

        if not legacy_in_wrong_place:
            passed_checks.append("No legacy folders in wrong location")
        else:
            for folder in legacy_in_wrong_place:
                issues.append(self._create_issue(
                    severity=IssueSeverity.WARNING,
                    issue_code="IMPROPER_LEGACY_ARCHIVAL",
                    message=f"Legacy folder not in 10-archive: {folder}",
                    file_path=f"docs/{folder}",
                    fix_suggestion=f"Move to: docs/10-archive/{folder}",
                    fix_command=f"mv docs/{folder} docs/10-archive/",
                    auto_fixable=True,
                ))

        # Check archive folder structure
        checks_performed += 1
        archive_exists = False
        archive_path = None

        for path in self.ARCHIVE_PATHS:
            if await self.file_service.directory_exists(project_id, path):
                archive_exists = True
                archive_path = path
                break

        if archive_exists:
            passed_checks.append(f"Archive folder exists: {archive_path}")

            # Check archive has README
            checks_performed += 1
            readme_exists = await self.file_service.file_exists(
                project_id,
                f"{archive_path}README.md"
            )
            if readme_exists:
                passed_checks.append("Archive README exists")
            else:
                issues.append(self._create_issue(
                    severity=IssueSeverity.INFO,
                    issue_code="MISSING_ARCHIVE_README",
                    message="Archive folder missing README.md",
                    file_path=archive_path,
                    fix_suggestion="Add README.md explaining archive contents",
                ))
        else:
            # Archive folder not existing is fine if no legacy content
            if not legacy_in_wrong_place:
                passed_checks.append("No archive needed (no legacy content)")
            else:
                issues.append(self._create_issue(
                    severity=IssueSeverity.INFO,
                    issue_code="MISSING_ARCHIVE_FOLDER",
                    message="Archive folder (10-archive) not found",
                    file_path="docs/",
                    fix_suggestion="Create docs/10-archive/ for legacy content",
                ))

        return self._create_result(issues, passed_checks, checks_performed)
