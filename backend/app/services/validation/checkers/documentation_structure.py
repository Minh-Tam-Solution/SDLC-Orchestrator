"""
Documentation Structure Checker - Sprint 123 (SPEC-0013)

Validates SDLC 6.0.5 documentation folder structure:
1. Stage folders exist (00-10)
2. No duplicate stage prefixes
3. Proper folder naming
4. No extra root folders (except allowed: specs, templates)
"""

from typing import Optional
from uuid import UUID

from app.models.compliance_validation import ComplianceCategory, IssueSeverity
from app.services.validation.checkers.base import (
    BaseCategoryChecker,
    CategoryCheckResult,
    CheckIssue,
)


class DocumentationStructureChecker(BaseCategoryChecker):
    """
    Documentation Structure Checker (10 points).

    Validates:
    1. Required stage folders exist (00-09, 10 optional)
    2. No duplicate stage prefixes (e.g., 04-X + 04-Y)
    3. Proper folder naming convention (XX-name)
    4. No non-standard root folders
    """

    category = ComplianceCategory.DOCUMENTATION_STRUCTURE

    # SDLC 6.0.5 stage definitions
    REQUIRED_STAGES = [
        ("00", "discover"),
        ("01", "planning"),
        ("02", "design"),
        ("03", "integrate"),
        ("04", "build"),
        ("05", "test"),
        ("06", "deploy"),
        ("07", "operate"),
        ("08", "collaborate"),
        ("09", "govern"),
    ]
    OPTIONAL_STAGES = [
        ("10", "archive"),
    ]

    # Allowed non-stage folders in docs/
    ALLOWED_EXTRAS = {"specs", "templates", ".git", ".github", "README.md"}

    async def check(self, project_id: UUID) -> CategoryCheckResult:
        """
        Check documentation structure compliance.

        Checks:
        1. Stage folders exist (10 required, 1 optional)
        2. No duplicate prefixes
        3. No extra root folders
        4. Proper naming convention

        Args:
            project_id: Project UUID

        Returns:
            CategoryCheckResult with score and issues
        """
        issues: list[CheckIssue] = []
        passed_checks: list[str] = []
        checks_performed = 0

        # Get docs folder contents
        docs_folders = await self.file_service.list_directories(
            project_id=project_id,
            path="docs/",
        )

        # Check 1: Required stage folders exist
        for prefix, stage_name in self.REQUIRED_STAGES:
            checks_performed += 1
            matching = [f for f in docs_folders if f.startswith(f"{prefix}-")]

            if len(matching) == 1:
                passed_checks.append(f"Stage {prefix}-{stage_name} exists")
            elif len(matching) == 0:
                issues.append(self._create_issue(
                    severity=IssueSeverity.WARNING,
                    issue_code="MISSING_STAGE_FOLDER",
                    message=f"Missing stage folder: {prefix}-{stage_name}",
                    file_path="docs/",
                    fix_suggestion=f"Create folder: mkdir -p docs/{prefix}-{stage_name}",
                    fix_command=f"sdlcctl init --stage {prefix}-{stage_name}",
                    auto_fixable=True,
                ))
            else:
                # Duplicate detected - critical issue
                issues.append(self._create_issue(
                    severity=IssueSeverity.CRITICAL,
                    issue_code="DUPLICATE_STAGE_FOLDER",
                    message=f"Duplicate stage folder detected: {', '.join(matching)}",
                    file_path="docs/",
                    fix_suggestion=f"Archive duplicates: mv docs/{matching[1]} docs/10-archive/duplicate-folders/",
                    fix_command="sdlcctl fix --duplicates",
                    auto_fixable=False,
                    context={"stage_prefix": prefix, "folders": matching},
                ))

        # Check 2: Optional stage 10-archive
        checks_performed += 1
        archive_folders = [f for f in docs_folders if f.startswith("10-")]
        if len(archive_folders) <= 1:
            passed_checks.append("Stage 10-archive (optional) valid")
        else:
            issues.append(self._create_issue(
                severity=IssueSeverity.WARNING,
                issue_code="DUPLICATE_STAGE_FOLDER",
                message=f"Multiple archive folders: {', '.join(archive_folders)}",
                file_path="docs/",
                fix_suggestion="Merge archive folders into single 10-archive/",
            ))

        # Check 3: No invalid stage prefixes
        checks_performed += 1
        valid_prefixes = {s[0] for s in self.REQUIRED_STAGES + self.OPTIONAL_STAGES}
        invalid_numbered = []

        for folder in docs_folders:
            if "-" in folder:
                prefix = folder.split("-")[0]
                if prefix.isdigit() and prefix not in valid_prefixes:
                    invalid_numbered.append(folder)

        if not invalid_numbered:
            passed_checks.append("No invalid stage prefixes")
        else:
            for folder in invalid_numbered:
                issues.append(self._create_issue(
                    severity=IssueSeverity.WARNING,
                    issue_code="INVALID_STAGE_NUMBERING",
                    message=f"Invalid stage numbering: {folder}",
                    file_path=f"docs/{folder}",
                    fix_suggestion=f"Move to archive: mv docs/{folder} docs/10-archive/",
                ))

        # Check 4: No extra root folders (except allowed)
        checks_performed += 1
        stage_prefixes = {s[0] for s in self.REQUIRED_STAGES + self.OPTIONAL_STAGES}
        extra_folders = []

        for folder in docs_folders:
            # Skip if it's a stage folder
            if "-" in folder:
                prefix = folder.split("-")[0]
                if prefix in stage_prefixes:
                    continue

            # Check if allowed
            if folder.lower() not in {a.lower() for a in self.ALLOWED_EXTRAS}:
                extra_folders.append(folder)

        if not extra_folders:
            passed_checks.append("No non-standard root folders")
        else:
            for folder in extra_folders:
                issues.append(self._create_issue(
                    severity=IssueSeverity.INFO,
                    issue_code="EXTRA_ROOT_FOLDER",
                    message=f"Non-standard folder in docs/: {folder}",
                    file_path=f"docs/{folder}",
                    fix_suggestion=f"Move to appropriate stage or archive",
                ))

        # Check 5: Folder naming convention (XX-description)
        checks_performed += 1
        invalid_naming = []
        for folder in docs_folders:
            # Skip allowed extras
            if folder.lower() in {a.lower() for a in self.ALLOWED_EXTRAS}:
                continue
            # Check format: XX-name
            if "-" not in folder or not folder.split("-")[0].isdigit():
                if folder not in extra_folders:  # Don't double-report
                    invalid_naming.append(folder)

        if not invalid_naming:
            passed_checks.append("All stage folders follow naming convention")
        else:
            for folder in invalid_naming:
                issues.append(self._create_issue(
                    severity=IssueSeverity.INFO,
                    issue_code="INVALID_FOLDER_NAMING",
                    message=f"Folder doesn't follow XX-name convention: {folder}",
                    file_path=f"docs/{folder}",
                ))

        return self._create_result(
            issues=issues,
            passed_checks=passed_checks,
            checks_performed=checks_performed,
        )
