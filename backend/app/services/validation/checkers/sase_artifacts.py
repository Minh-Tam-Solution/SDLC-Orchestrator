"""
SASE Artifacts Checker - Sprint 123 (SPEC-0013)

Validates SDLC 6.0.0 SASE (Specification-Aware Software Engineering) artifacts:
1. CRP (Context & Requirements Protocol) present
2. MRP (Modification Request Protocol) present
3. VCR (Validation & Compliance Record) template present
"""

from uuid import UUID

from app.models.compliance_validation import ComplianceCategory, IssueSeverity
from app.services.validation.checkers.base import (
    BaseCategoryChecker,
    CategoryCheckResult,
    CheckIssue,
)


class SASEArtifactsChecker(BaseCategoryChecker):
    """SASE Artifacts Checker (10 points)."""

    category = ComplianceCategory.SASE_ARTIFACTS

    # SASE artifact paths
    SASE_ARTIFACTS = {
        "CRP": ["docs/templates/CRP-Template.md", "docs/09-govern/templates/CRP-Template.md"],
        "MRP": ["docs/templates/MRP-Template.md", "docs/09-govern/templates/MRP-Template.md"],
        "VCR": ["docs/templates/VCR-Template.md", "docs/09-govern/templates/VCR-Template.md"],
    }

    async def check(self, project_id: UUID) -> CategoryCheckResult:
        """Check SASE artifacts compliance."""
        issues: list[CheckIssue] = []
        passed_checks: list[str] = []
        checks_performed = 0

        for artifact_name, possible_paths in self.SASE_ARTIFACTS.items():
            checks_performed += 1
            found = False

            for path in possible_paths:
                exists = await self.file_service.file_exists(
                    project_id=project_id,
                    path=path,
                )
                if exists:
                    found = True
                    passed_checks.append(f"{artifact_name} template exists at {path}")
                    break

            if not found:
                issues.append(self._create_issue(
                    severity=IssueSeverity.INFO,
                    issue_code="MISSING_SASE_ARTIFACT",
                    message=f"Missing SASE artifact: {artifact_name} template",
                    file_path="docs/templates/",
                    fix_suggestion=f"Create {artifact_name}-Template.md in docs/templates/",
                    fix_command=f"sdlcctl init --sase-template {artifact_name.lower()}",
                    auto_fixable=True,
                ))

        # Check for SASE README
        checks_performed += 1
        sase_readme_paths = [
            "docs/templates/README.md",
            "docs/09-govern/templates/README.md",
        ]
        readme_found = False
        for path in sase_readme_paths:
            if await self.file_service.file_exists(project_id, path):
                readme_found = True
                passed_checks.append("SASE templates README exists")
                break

        if not readme_found:
            issues.append(self._create_issue(
                severity=IssueSeverity.INFO,
                issue_code="MISSING_SASE_README",
                message="Missing README for SASE templates documentation",
                file_path="docs/templates/",
                fix_suggestion="Add README.md explaining SASE artifact usage",
            ))

        return self._create_result(issues, passed_checks, checks_performed)
