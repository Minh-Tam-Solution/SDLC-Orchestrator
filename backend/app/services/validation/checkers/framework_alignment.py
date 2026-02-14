"""
Framework Alignment Checker - Sprint 123 (SPEC-0013)

Validates SDLC 6.0.5 7-Pillar Architecture alignment.
"""

from uuid import UUID

from app.models.compliance_validation import ComplianceCategory, IssueSeverity
from app.services.validation.checkers.base import (
    BaseCategoryChecker,
    CategoryCheckResult,
    CheckIssue,
)


class FrameworkAlignmentChecker(BaseCategoryChecker):
    """Framework Alignment Checker (10 points)."""

    category = ComplianceCategory.FRAMEWORK_ALIGNMENT

    # SDLC 6.0.5 7-Pillar requirements
    PILLARS = [
        ("Pillar 1", "Foundation Governance", ["CLAUDE.md", "AGENTS.md"]),
        ("Pillar 2", "Sprint Planning", ["docs/04-build/02-Sprint-Plans/"]),
        ("Pillar 3", "Quality Assurance", ["docs/05-test/"]),
        ("Pillar 4", "Deployment", ["docs/06-deploy/"]),
        ("Pillar 5", "Operations", ["docs/07-operate/"]),
        ("Pillar 6", "Collaboration", ["docs/08-collaborate/"]),
        ("Pillar 7", "Governance", ["docs/09-govern/"]),
    ]

    async def check(self, project_id: UUID) -> CategoryCheckResult:
        """Check framework alignment compliance."""
        issues: list[CheckIssue] = []
        passed_checks: list[str] = []
        checks_performed = 0

        for pillar_name, description, paths in self.PILLARS:
            checks_performed += 1
            pillar_satisfied = False

            for path in paths:
                if path.endswith("/"):
                    exists = await self.file_service.directory_exists(project_id, path)
                else:
                    exists = await self.file_service.file_exists(project_id, path)

                if exists:
                    pillar_satisfied = True
                    break

            if pillar_satisfied:
                passed_checks.append(f"{pillar_name}: {description}")
            else:
                issues.append(self._create_issue(
                    severity=IssueSeverity.INFO,
                    issue_code="PILLAR_NOT_SATISFIED",
                    message=f"{pillar_name} ({description}) not fully satisfied",
                    file_path=paths[0],
                    fix_suggestion=f"Create required structure for {pillar_name}",
                ))

        # Check Section 7 (Quality Assurance System)
        checks_performed += 1
        qa_indicators = [
            "docs/02-design/14-Technical-Specs/SPEC-0001-Anti-Vibecoding.md",
            "docs/02-design/14-Technical-Specs/",
        ]
        qa_found = False
        for path in qa_indicators:
            if await self.file_service.file_exists(project_id, path) or \
               await self.file_service.directory_exists(project_id, path):
                qa_found = True
                break

        if qa_found:
            passed_checks.append("Section 7: Quality Assurance System")
        else:
            issues.append(self._create_issue(
                severity=IssueSeverity.INFO,
                issue_code="SECTION7_NOT_FOUND",
                message="Section 7 (Quality Assurance System) not detected",
                file_path="docs/02-design/14-Technical-Specs/",
            ))

        return self._create_result(issues, passed_checks, checks_performed)
