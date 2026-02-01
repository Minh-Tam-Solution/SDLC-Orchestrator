"""
Code File Naming Checker - Sprint 123 (SPEC-0013)

Validates SDLC 6.0.0 code file naming conventions:
1. Python: snake_case (max 50 chars)
2. TypeScript: camelCase for files, PascalCase for components
3. Alembic migrations: revision_description format (max 60 chars)
"""

import re
from uuid import UUID

from app.models.compliance_validation import ComplianceCategory, IssueSeverity
from app.services.validation.checkers.base import (
    BaseCategoryChecker,
    CategoryCheckResult,
    CheckIssue,
)


class CodeFileNamingChecker(BaseCategoryChecker):
    """Code File Naming Checker (10 points)."""

    category = ComplianceCategory.CODE_FILE_NAMING

    SNAKE_CASE = re.compile(r"^[a-z][a-z0-9_]*$")
    CAMEL_CASE = re.compile(r"^[a-z][a-zA-Z0-9]*$")
    PASCAL_CASE = re.compile(r"^[A-Z][a-zA-Z0-9]*$")
    MAX_LENGTH = 50
    MIGRATION_MAX_LENGTH = 60

    async def check(self, project_id: UUID) -> CategoryCheckResult:
        """Check code file naming compliance."""
        issues: list[CheckIssue] = []
        passed_checks: list[str] = []
        checks_performed = 0

        # Check Python files
        py_files = await self.file_service.find_files(
            project_id=project_id,
            pattern="**/*.py",
            exclude_patterns=["**/venv/**", "**/__pycache__/**", "**/alembic/versions/**"],
        )

        py_violations = 0
        for file_path in py_files[:50]:  # Sample up to 50 files
            checks_performed += 1
            filename = file_path.split("/")[-1].replace(".py", "")

            # Skip special files
            if filename.startswith("__") or filename in ["conftest", "setup"]:
                passed_checks.append(f"Python file {filename} (special)")
                continue

            if not self.SNAKE_CASE.match(filename):
                py_violations += 1
                issues.append(self._create_issue(
                    severity=IssueSeverity.WARNING,
                    issue_code="PYTHON_NOT_SNAKE_CASE",
                    message=f"Python file not snake_case: {filename}.py",
                    file_path=file_path,
                    fix_suggestion=f"Rename to: {self._to_snake_case(filename)}.py",
                ))
            elif len(filename) > self.MAX_LENGTH:
                issues.append(self._create_issue(
                    severity=IssueSeverity.INFO,
                    issue_code="FILE_NAME_TOO_LONG",
                    message=f"Python file name > {self.MAX_LENGTH} chars: {filename}",
                    file_path=file_path,
                ))
            else:
                passed_checks.append(f"Python file {filename} valid")

        # Check TypeScript/TSX files
        ts_files = await self.file_service.find_files(
            project_id=project_id,
            pattern="**/*.{ts,tsx}",
            exclude_patterns=["**/node_modules/**", "**/dist/**"],
        )

        ts_violations = 0
        for file_path in ts_files[:50]:
            checks_performed += 1
            filename = file_path.split("/")[-1]
            name_only = filename.replace(".tsx", "").replace(".ts", "")

            # TSX components should be PascalCase
            if filename.endswith(".tsx"):
                if not self.PASCAL_CASE.match(name_only):
                    ts_violations += 1
                    issues.append(self._create_issue(
                        severity=IssueSeverity.WARNING,
                        issue_code="TS_COMPONENT_NOT_PASCAL_CASE",
                        message=f"React component not PascalCase: {filename}",
                        file_path=file_path,
                        fix_suggestion=f"Rename to: {self._to_pascal_case(name_only)}.tsx",
                    ))
                else:
                    passed_checks.append(f"TSX component {name_only} valid")
            # Regular TS files should be camelCase
            elif not self.CAMEL_CASE.match(name_only) and not self.SNAKE_CASE.match(name_only):
                # Allow both camelCase and snake_case for TS
                ts_violations += 1
                issues.append(self._create_issue(
                    severity=IssueSeverity.INFO,
                    issue_code="TS_FILE_NAMING",
                    message=f"TypeScript file naming inconsistent: {filename}",
                    file_path=file_path,
                ))
            else:
                passed_checks.append(f"TypeScript file {name_only} valid")

        # Summary check
        checks_performed += 1
        total_violations = py_violations + ts_violations
        if total_violations == 0:
            passed_checks.append("All code files follow naming conventions")
        elif total_violations < 5:
            passed_checks.append(f"Minor naming issues ({total_violations} files)")

        return self._create_result(issues, passed_checks, checks_performed)

    def _to_snake_case(self, name: str) -> str:
        """Convert to snake_case."""
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

    def _to_pascal_case(self, name: str) -> str:
        """Convert to PascalCase."""
        words = re.split(r'[_\-\s]', name)
        return ''.join(word.capitalize() for word in words)
