"""
CLAUDE.md / AGENTS.md Checker - Sprint 123 (SPEC-0013)

Validates AI context files:
1. CLAUDE.md exists in project root
2. AGENTS.md exists (optional but recommended)
3. Framework version reference is current
4. Required sections present
"""

import re
from uuid import UUID

from app.models.compliance_validation import ComplianceCategory, IssueSeverity
from app.services.validation.checkers.base import (
    BaseCategoryChecker,
    CategoryCheckResult,
    CheckIssue,
)


class ClaudeAgentsMdChecker(BaseCategoryChecker):
    """
    CLAUDE.md / AGENTS.md Checker (10 points).

    Validates:
    1. CLAUDE.md exists
    2. AGENTS.md exists (recommended)
    3. Framework version current (6.0.5)
    4. Required sections present
    """

    category = ComplianceCategory.CLAUDE_AGENTS_MD

    REQUIRED_FILES = ["CLAUDE.md"]
    RECOMMENDED_FILES = ["AGENTS.md"]
    CURRENT_FRAMEWORK = "6.0.5"
    REQUIRED_SECTIONS = [
        "PROJECT OVERVIEW",
        "YOUR ROLE",
        "FRAMEWORK",
    ]

    async def check(self, project_id: UUID) -> CategoryCheckResult:
        """Check CLAUDE.md and AGENTS.md compliance."""
        issues: list[CheckIssue] = []
        passed_checks: list[str] = []
        checks_performed = 0

        # Check 1: CLAUDE.md exists
        checks_performed += 1
        claude_md = await self.file_service.file_exists(
            project_id=project_id,
            path="CLAUDE.md",
        )

        if claude_md:
            passed_checks.append("CLAUDE.md exists")

            # Check content
            content = await self.file_service.read_file(
                project_id=project_id,
                path="CLAUDE.md",
            )

            if content:
                # Check framework version
                checks_performed += 1
                version_match = re.search(r"(?:Framework|SDLC)[:\s]+(\d+\.\d+\.\d+)", content)
                if version_match:
                    version = version_match.group(1)
                    if version >= self.CURRENT_FRAMEWORK:
                        passed_checks.append(f"Framework version current ({version})")
                    else:
                        issues.append(self._create_issue(
                            severity=IssueSeverity.WARNING,
                            issue_code="OUTDATED_FRAMEWORK_VERSION",
                            message=f"CLAUDE.md references outdated framework: {version}",
                            file_path="CLAUDE.md",
                            fix_suggestion=f"Update to SDLC {self.CURRENT_FRAMEWORK}",
                            context={"current": version, "required": self.CURRENT_FRAMEWORK},
                        ))
                else:
                    issues.append(self._create_issue(
                        severity=IssueSeverity.INFO,
                        issue_code="MISSING_FRAMEWORK_VERSION",
                        message="CLAUDE.md missing framework version reference",
                        file_path="CLAUDE.md",
                    ))

                # Check required sections
                for section in self.REQUIRED_SECTIONS:
                    checks_performed += 1
                    if section.upper() in content.upper():
                        passed_checks.append(f"Section '{section}' present")
                    else:
                        issues.append(self._create_issue(
                            severity=IssueSeverity.INFO,
                            issue_code="MISSING_REQUIRED_SECTION",
                            message=f"CLAUDE.md missing section: {section}",
                            file_path="CLAUDE.md",
                            fix_suggestion=f"Add section: ## {section}",
                        ))
        else:
            issues.append(self._create_issue(
                severity=IssueSeverity.CRITICAL,
                issue_code="MISSING_CLAUDE_MD",
                message="CLAUDE.md not found in project root",
                file_path="./",
                fix_suggestion="Create CLAUDE.md with project context for AI assistants",
                fix_command="sdlcctl init --claude-md",
                auto_fixable=True,
            ))

        # Check 2: AGENTS.md exists (recommended)
        checks_performed += 1
        agents_md = await self.file_service.file_exists(
            project_id=project_id,
            path="AGENTS.md",
        )

        if agents_md:
            passed_checks.append("AGENTS.md exists")

            # Check for framework version in AGENTS.md too
            content = await self.file_service.read_file(
                project_id=project_id,
                path="AGENTS.md",
            )
            if content:
                checks_performed += 1
                version_match = re.search(r"(?:Framework|SDLC)[:\s]+(\d+\.\d+\.\d+)", content)
                if version_match:
                    version = version_match.group(1)
                    if version < self.CURRENT_FRAMEWORK:
                        issues.append(self._create_issue(
                            severity=IssueSeverity.WARNING,
                            issue_code="OUTDATED_FRAMEWORK_VERSION",
                            message=f"AGENTS.md references outdated framework: {version}",
                            file_path="AGENTS.md",
                            fix_suggestion=f"Update to SDLC {self.CURRENT_FRAMEWORK}",
                        ))
                    else:
                        passed_checks.append("AGENTS.md framework version current")
        else:
            issues.append(self._create_issue(
                severity=IssueSeverity.INFO,
                issue_code="MISSING_AGENTS_MD",
                message="AGENTS.md not found (recommended for industry standard)",
                file_path="./",
                fix_suggestion="Create AGENTS.md following industry standard format",
            ))

        return self._create_result(
            issues=issues,
            passed_checks=passed_checks,
            checks_performed=checks_performed,
        )
