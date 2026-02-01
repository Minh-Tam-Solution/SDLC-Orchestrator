"""
Migration Tracking Checker - Sprint 123 (SPEC-0013)

Validates migration status and deadline compliance.
"""

from datetime import datetime
from uuid import UUID

from app.models.compliance_validation import ComplianceCategory, IssueSeverity
from app.services.validation.checkers.base import (
    BaseCategoryChecker,
    CategoryCheckResult,
    CheckIssue,
)


class MigrationTrackingChecker(BaseCategoryChecker):
    """Migration Tracking Checker (10 points)."""

    category = ComplianceCategory.MIGRATION_TRACKING

    MIGRATION_FILES = [
        "docs/08-collaborate/01-SDLC-Compliance/MIGRATION-STATUS.md",
        "docs/08-Team-Management/01-SDLC-Compliance/MIGRATION-STATUS.md",
    ]

    async def check(self, project_id: UUID) -> CategoryCheckResult:
        """Check migration tracking compliance."""
        issues: list[CheckIssue] = []
        passed_checks: list[str] = []
        checks_performed = 0

        # Check for migration tracking file
        checks_performed += 1
        migration_file = None

        for path in self.MIGRATION_FILES:
            if await self.file_service.file_exists(project_id, path):
                migration_file = path
                break

        if migration_file:
            passed_checks.append("Migration tracking file exists")

            # Read and analyze content
            content = await self.file_service.read_file(project_id, migration_file)
            if content:
                # Check for progress percentage
                checks_performed += 1
                import re
                progress_match = re.search(r"(\d+)\s*[%/]", content)
                if progress_match:
                    progress = int(progress_match.group(1))
                    if progress >= 100:
                        passed_checks.append(f"Migration complete ({progress}%)")
                    elif progress >= 80:
                        passed_checks.append(f"Migration nearly complete ({progress}%)")
                    else:
                        issues.append(self._create_issue(
                            severity=IssueSeverity.INFO,
                            issue_code="MIGRATION_IN_PROGRESS",
                            message=f"Migration in progress: {progress}%",
                            file_path=migration_file,
                        ))
                else:
                    issues.append(self._create_issue(
                        severity=IssueSeverity.INFO,
                        issue_code="MISSING_PROGRESS",
                        message="Migration progress percentage not found",
                        file_path=migration_file,
                        fix_suggestion="Add progress indicator (e.g., 'Progress: 85%')",
                    ))

                # Check for deadline
                checks_performed += 1
                deadline_match = re.search(
                    r"[Dd]eadline[:\s]+(\d{4}-\d{2}-\d{2})",
                    content
                )
                if deadline_match:
                    deadline_str = deadline_match.group(1)
                    try:
                        deadline = datetime.strptime(deadline_str, "%Y-%m-%d")
                        if datetime.now() > deadline:
                            issues.append(self._create_issue(
                                severity=IssueSeverity.WARNING,
                                issue_code="MIGRATION_DEADLINE_EXCEEDED",
                                message=f"Migration deadline exceeded: {deadline_str}",
                                file_path=migration_file,
                            ))
                        else:
                            passed_checks.append(f"Deadline on track ({deadline_str})")
                    except ValueError:
                        pass
                else:
                    issues.append(self._create_issue(
                        severity=IssueSeverity.INFO,
                        issue_code="MISSING_DEADLINE",
                        message="Migration deadline not specified",
                        file_path=migration_file,
                    ))
        else:
            # No migration file - might be intentional
            issues.append(self._create_issue(
                severity=IssueSeverity.INFO,
                issue_code="NO_MIGRATION_TRACKING",
                message="No migration tracking file found",
                file_path="docs/08-collaborate/01-SDLC-Compliance/",
                fix_suggestion="Create MIGRATION-STATUS.md if migration is in progress",
            ))

        # Even without file, award base points if not actively migrating
        if not migration_file and checks_performed == 1:
            passed_checks.append("No active migration (or already complete)")

        return self._create_result(issues, passed_checks, checks_performed)
