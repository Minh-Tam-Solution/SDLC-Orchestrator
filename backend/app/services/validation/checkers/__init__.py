"""
Compliance Category Checkers - Sprint 123 (SPEC-0013)

10 category checkers, each validating specific compliance aspects.
Each category is worth 10 points, totaling 100 maximum.

Categories:
1. documentation_structure: Stage folders (00-10), no duplicates
2. specifications_management: YAML frontmatter, SPEC-XXXX numbering
3. claude_agents_md: Version headers, required sections
4. sase_artifacts: CRP, MRP, VCR templates present
5. code_file_naming: snake_case (Python), camelCase/PascalCase (TS)
6. migration_tracking: Progress percentage, deadline compliance
7. framework_alignment: 7-Pillar + Section 7 compliance
8. team_organization: SDLC Compliance Hub, roles defined
9. legacy_archival: Proper 99-legacy/ or 10-Archive/ usage
10. governance_documentation: CEO/CTO approvals, ADRs
"""

from app.services.validation.checkers.base import BaseCategoryChecker
from app.services.validation.checkers.documentation_structure import DocumentationStructureChecker
from app.services.validation.checkers.specifications_management import SpecificationsManagementChecker
from app.services.validation.checkers.claude_agents_md import ClaudeAgentsMdChecker
from app.services.validation.checkers.sase_artifacts import SASEArtifactsChecker
from app.services.validation.checkers.code_file_naming import CodeFileNamingChecker
from app.services.validation.checkers.migration_tracking import MigrationTrackingChecker
from app.services.validation.checkers.framework_alignment import FrameworkAlignmentChecker
from app.services.validation.checkers.team_organization import TeamOrganizationChecker
from app.services.validation.checkers.legacy_archival import LegacyArchivalChecker
from app.services.validation.checkers.governance_documentation import GovernanceDocumentationChecker

from app.models.compliance_validation import ComplianceCategory

# Registry of category checkers
CATEGORY_CHECKERS: dict[ComplianceCategory, type[BaseCategoryChecker]] = {
    ComplianceCategory.DOCUMENTATION_STRUCTURE: DocumentationStructureChecker,
    ComplianceCategory.SPECIFICATIONS_MANAGEMENT: SpecificationsManagementChecker,
    ComplianceCategory.CLAUDE_AGENTS_MD: ClaudeAgentsMdChecker,
    ComplianceCategory.SASE_ARTIFACTS: SASEArtifactsChecker,
    ComplianceCategory.CODE_FILE_NAMING: CodeFileNamingChecker,
    ComplianceCategory.MIGRATION_TRACKING: MigrationTrackingChecker,
    ComplianceCategory.FRAMEWORK_ALIGNMENT: FrameworkAlignmentChecker,
    ComplianceCategory.TEAM_ORGANIZATION: TeamOrganizationChecker,
    ComplianceCategory.LEGACY_ARCHIVAL: LegacyArchivalChecker,
    ComplianceCategory.GOVERNANCE_DOCUMENTATION: GovernanceDocumentationChecker,
}

__all__ = [
    "BaseCategoryChecker",
    "DocumentationStructureChecker",
    "SpecificationsManagementChecker",
    "ClaudeAgentsMdChecker",
    "SASEArtifactsChecker",
    "CodeFileNamingChecker",
    "MigrationTrackingChecker",
    "FrameworkAlignmentChecker",
    "TeamOrganizationChecker",
    "LegacyArchivalChecker",
    "GovernanceDocumentationChecker",
    "CATEGORY_CHECKERS",
]
