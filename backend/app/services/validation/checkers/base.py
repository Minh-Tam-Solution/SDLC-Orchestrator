"""
Base Category Checker - Sprint 123 (SPEC-0013)

Abstract base class for all compliance category checkers.
Each checker validates one category (max 10 points).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.compliance_validation import ComplianceCategory, IssueSeverity


@dataclass
class CheckIssue:
    """Single compliance issue found during check."""

    category: ComplianceCategory
    severity: IssueSeverity
    issue_code: str
    message: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    fix_suggestion: Optional[str] = None
    fix_command: Optional[str] = None
    auto_fixable: bool = False
    context: Optional[dict] = None


@dataclass
class CategoryCheckResult:
    """Result from checking a single category."""

    category: ComplianceCategory
    score: int  # 0-10
    max_score: int = 10
    issues: list[CheckIssue] = field(default_factory=list)
    passed_checks: list[str] = field(default_factory=list)
    checks_performed: int = 0

    @property
    def has_critical_issues(self) -> bool:
        """Check if there are any critical issues."""
        return any(i.severity == IssueSeverity.CRITICAL for i in self.issues)

    @property
    def critical_count(self) -> int:
        """Count critical issues."""
        return sum(1 for i in self.issues if i.severity == IssueSeverity.CRITICAL)

    @property
    def warning_count(self) -> int:
        """Count warning issues."""
        return sum(1 for i in self.issues if i.severity == IssueSeverity.WARNING)

    @property
    def info_count(self) -> int:
        """Count info issues."""
        return sum(1 for i in self.issues if i.severity == IssueSeverity.INFO)


class BaseCategoryChecker(ABC):
    """
    Base class for compliance category checkers.

    Each checker validates one category (max 10 points).
    Subclasses implement the `check` method with specific validation logic.

    Usage:
        class DocumentationStructureChecker(BaseCategoryChecker):
            category = ComplianceCategory.DOCUMENTATION_STRUCTURE

            async def check(self, project_id: UUID) -> CategoryCheckResult:
                # Validation logic
                pass

    Scoring Algorithm:
        1. Run all checks for the category
        2. Calculate base score: (passed_checks / total_checks) * 10
        3. Apply critical penalty: if critical_failures > 0, score *= 0.5
        4. Return score clamped to 0-10
    """

    category: ComplianceCategory
    max_score: int = 10

    def __init__(self, db: AsyncSession, file_service):
        """
        Initialize checker with database session and file service.

        Args:
            db: Async database session
            file_service: Service for file operations (list, read, etc.)
        """
        self.db = db
        self.file_service = file_service

    @abstractmethod
    async def check(self, project_id: UUID) -> CategoryCheckResult:
        """
        Run all checks for this category.

        Args:
            project_id: Project UUID to validate

        Returns:
            CategoryCheckResult with score, issues, and passed checks
        """
        pass

    def _calculate_score(
        self,
        passed: int,
        total: int,
        critical_failures: int = 0,
    ) -> int:
        """
        Calculate category score based on passed/total checks.

        Args:
            passed: Number of checks that passed
            total: Total number of checks performed
            critical_failures: Number of critical failures (causes 50% penalty)

        Returns:
            Score from 0-10
        """
        if total == 0:
            return self.max_score

        base_score = int((passed / total) * self.max_score)

        # Critical failures reduce score by 50%
        if critical_failures > 0:
            base_score = int(base_score * 0.5)

        return max(0, min(self.max_score, base_score))

    def _create_issue(
        self,
        severity: IssueSeverity,
        issue_code: str,
        message: str,
        file_path: Optional[str] = None,
        line_number: Optional[int] = None,
        fix_suggestion: Optional[str] = None,
        fix_command: Optional[str] = None,
        auto_fixable: bool = False,
        context: Optional[dict] = None,
    ) -> CheckIssue:
        """
        Create a standardized issue for this category.

        Args:
            severity: Issue severity (critical, warning, info)
            issue_code: Unique code for the issue type
            message: Human-readable message
            file_path: Optional file path where issue found
            line_number: Optional line number
            fix_suggestion: Optional fix suggestion
            fix_command: Optional CLI command to fix
            auto_fixable: Whether issue can be auto-fixed
            context: Optional additional context

        Returns:
            CheckIssue instance
        """
        return CheckIssue(
            category=self.category,
            severity=severity,
            issue_code=issue_code,
            message=message,
            file_path=file_path,
            line_number=line_number,
            fix_suggestion=fix_suggestion,
            fix_command=fix_command,
            auto_fixable=auto_fixable,
            context=context,
        )

    def _create_result(
        self,
        issues: list[CheckIssue],
        passed_checks: list[str],
        checks_performed: int,
    ) -> CategoryCheckResult:
        """
        Create a standardized result for this category.

        Args:
            issues: List of issues found
            passed_checks: List of check names that passed
            checks_performed: Total checks performed

        Returns:
            CategoryCheckResult with calculated score
        """
        critical_count = sum(1 for i in issues if i.severity == IssueSeverity.CRITICAL)
        passed_count = len(passed_checks)

        score = self._calculate_score(
            passed=passed_count,
            total=checks_performed,
            critical_failures=critical_count,
        )

        return CategoryCheckResult(
            category=self.category,
            score=score,
            max_score=self.max_score,
            issues=issues,
            passed_checks=passed_checks,
            checks_performed=checks_performed,
        )
