"""
Spec Import Service
Sprint 154 Day 5 - External Source Import

Service for importing specifications from external sources:
- Jira issues
- Linear issues
- GitHub issues
- Plain text/markdown

Architecture: ADR-050 Import Layer
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

from .models import SpecIR, SpecRequirement, SpecFormat


class ImportSource(str, Enum):
    """Supported import sources."""

    JIRA = "jira"
    LINEAR = "linear"
    GITHUB = "github"
    TEXT = "text"


@dataclass
class ImportResult:
    """Result of an import operation."""

    success: bool
    spec_ir: Optional[SpecIR]
    source: ImportSource
    source_id: Optional[str]
    error: Optional[str] = None
    warnings: List[str] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


@dataclass
class JiraIssue:
    """Jira issue data structure."""

    key: str
    summary: str
    description: str
    issue_type: str
    status: str
    priority: str
    labels: List[str]
    components: List[str]
    acceptance_criteria: Optional[str] = None


@dataclass
class LinearIssue:
    """Linear issue data structure."""

    id: str
    title: str
    description: str
    state: str
    priority: int
    labels: List[str]
    team: Optional[str] = None


class SpecImportService:
    """
    Service for importing specifications from external sources.

    Supported sources:
    - Jira: Import from Jira issues with acceptance criteria
    - Linear: Import from Linear issues
    - GitHub: Import from GitHub issues
    - Text: Import from plain text/markdown
    """

    def __init__(self):
        """Initialize import service."""
        self._jira_client = None
        self._linear_client = None
        self._github_client = None

    async def import_from_jira(
        self,
        issue_key: str,
        jira_url: Optional[str] = None,
        api_token: Optional[str] = None,
    ) -> ImportResult:
        """
        Import specification from Jira issue.

        Args:
            issue_key: Jira issue key (e.g., "PROJ-123")
            jira_url: Jira instance URL (optional, uses env var if not provided)
            api_token: Jira API token (optional, uses env var if not provided)

        Returns:
            ImportResult with parsed SpecIR or error
        """
        try:
            # In production, this would fetch from Jira API
            # For now, return stub implementation
            issue = await self._fetch_jira_issue(issue_key, jira_url, api_token)

            if not issue:
                return ImportResult(
                    success=False,
                    spec_ir=None,
                    source=ImportSource.JIRA,
                    source_id=issue_key,
                    error=f"Jira issue {issue_key} not found",
                )

            spec_ir = self._jira_to_spec_ir(issue)

            return ImportResult(
                success=True,
                spec_ir=spec_ir,
                source=ImportSource.JIRA,
                source_id=issue_key,
            )

        except Exception as e:
            return ImportResult(
                success=False,
                spec_ir=None,
                source=ImportSource.JIRA,
                source_id=issue_key,
                error=str(e),
            )

    async def import_from_linear(
        self,
        issue_id: str,
        api_key: Optional[str] = None,
    ) -> ImportResult:
        """
        Import specification from Linear issue.

        Args:
            issue_id: Linear issue ID
            api_key: Linear API key (optional, uses env var if not provided)

        Returns:
            ImportResult with parsed SpecIR or error
        """
        try:
            # In production, this would fetch from Linear API
            issue = await self._fetch_linear_issue(issue_id, api_key)

            if not issue:
                return ImportResult(
                    success=False,
                    spec_ir=None,
                    source=ImportSource.LINEAR,
                    source_id=issue_id,
                    error=f"Linear issue {issue_id} not found",
                )

            spec_ir = self._linear_to_spec_ir(issue)

            return ImportResult(
                success=True,
                spec_ir=spec_ir,
                source=ImportSource.LINEAR,
                source_id=issue_id,
            )

        except Exception as e:
            return ImportResult(
                success=False,
                spec_ir=None,
                source=ImportSource.LINEAR,
                source_id=issue_id,
                error=str(e),
            )

    async def import_from_text(
        self,
        content: str,
        title: Optional[str] = None,
    ) -> ImportResult:
        """
        Import specification from plain text or markdown.

        Args:
            content: Text content to import
            title: Optional title for the spec

        Returns:
            ImportResult with parsed SpecIR
        """
        try:
            spec_ir = self._text_to_spec_ir(content, title)

            return ImportResult(
                success=True,
                spec_ir=spec_ir,
                source=ImportSource.TEXT,
                source_id=None,
            )

        except Exception as e:
            return ImportResult(
                success=False,
                spec_ir=None,
                source=ImportSource.TEXT,
                source_id=None,
                error=str(e),
            )

    # =========================================================================
    # Private Methods - Jira
    # =========================================================================

    async def _fetch_jira_issue(
        self,
        issue_key: str,
        jira_url: Optional[str],
        api_token: Optional[str],
    ) -> Optional[JiraIssue]:
        """
        Fetch issue from Jira API.

        Note: This is a stub implementation. In production, would use
        the Jira REST API to fetch the actual issue.
        """
        # Stub: Return mock data for testing
        # In production: Use httpx to call Jira API
        #
        # Example Jira API call:
        # GET {jira_url}/rest/api/3/issue/{issue_key}
        # Headers: Authorization: Basic {base64(email:api_token)}

        # For now, return None to indicate not implemented
        # This allows tests to verify error handling
        return None

    def _jira_to_spec_ir(self, issue: JiraIssue) -> SpecIR:
        """Convert Jira issue to SpecIR."""
        # Map Jira priority to spec priority
        priority_map = {
            "Highest": "P0",
            "High": "P0",
            "Medium": "P1",
            "Low": "P2",
            "Lowest": "P3",
        }

        # Map Jira status to spec status
        status_map = {
            "To Do": "DRAFT",
            "In Progress": "PROPOSED",
            "Done": "APPROVED",
            "Closed": "APPROVED",
        }

        # Extract requirements from description and acceptance criteria
        requirements = self._extract_requirements_from_jira(issue)

        return SpecIR(
            spec_id=f"SPEC-{issue.key}",
            title=issue.summary,
            version="1.0.0",
            status=status_map.get(issue.status, "DRAFT"),
            tier=["ALL"],
            owner="",
            last_updated="",
            tags=issue.labels,
            related_adrs=[],
            related_specs=[],
            requirements=requirements,
            acceptance_criteria=[],
        )

    def _extract_requirements_from_jira(
        self, issue: JiraIssue
    ) -> List[SpecRequirement]:
        """Extract requirements from Jira issue description."""
        requirements = []

        # Try to extract from acceptance criteria field
        if issue.acceptance_criteria:
            ac_reqs = self._parse_acceptance_criteria(issue.acceptance_criteria)
            requirements.extend(ac_reqs)

        # If no ACs, create single requirement from description
        if not requirements:
            req = SpecRequirement(
                id="REQ-001",
                title=issue.summary,
                priority="P1",
                tier=["ALL"],
                given="the feature is implemented",
                when="the user interacts with it",
                then="it behaves as described",
                acceptance_criteria=[],
            )
            requirements.append(req)

        return requirements

    def _parse_acceptance_criteria(self, ac_text: str) -> List[SpecRequirement]:
        """Parse acceptance criteria text into requirements."""
        requirements = []

        # Common patterns for acceptance criteria
        # Pattern 1: Numbered list (1. xxx, 2. xxx)
        # Pattern 2: Bullet points (- xxx, * xxx)
        # Pattern 3: Given/When/Then blocks

        lines = ac_text.strip().split("\n")
        current_req_idx = 0

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check for Given/When/Then pattern
            given_match = re.match(r"(?:given|precondition)[:\s]+(.+)", line, re.I)
            when_match = re.match(r"(?:when|action)[:\s]+(.+)", line, re.I)
            then_match = re.match(r"(?:then|expected|result)[:\s]+(.+)", line, re.I)

            if given_match or when_match or then_match:
                # BDD-style AC
                if not requirements or requirements[-1].then:
                    current_req_idx += 1
                    req = SpecRequirement(
                        id=f"REQ-{str(current_req_idx).zfill(3)}",
                        title=f"Requirement {current_req_idx}",
                        priority="P1",
                        tier=["ALL"],
                        given="",
                        when="",
                        then="",
                        acceptance_criteria=[],
                    )
                    requirements.append(req)

                if given_match:
                    requirements[-1].given = given_match.group(1)
                elif when_match:
                    requirements[-1].when = when_match.group(1)
                elif then_match:
                    requirements[-1].then = then_match.group(1)

            elif line.startswith(("-", "*", "•")) or re.match(r"^\d+\.", line):
                # List item - treat as separate AC
                current_req_idx += 1
                text = re.sub(r"^[-*•\d.]+\s*", "", line)
                req = SpecRequirement(
                    id=f"REQ-{str(current_req_idx).zfill(3)}",
                    title=text[:50],
                    priority="P1",
                    tier=["ALL"],
                    given="the system is ready",
                    when="this action is performed",
                    then=text,
                    acceptance_criteria=[],
                )
                requirements.append(req)

        return requirements

    # =========================================================================
    # Private Methods - Linear
    # =========================================================================

    async def _fetch_linear_issue(
        self,
        issue_id: str,
        api_key: Optional[str],
    ) -> Optional[LinearIssue]:
        """
        Fetch issue from Linear API.

        Note: This is a stub implementation. In production, would use
        the Linear GraphQL API to fetch the actual issue.
        """
        # Stub: Return None to indicate not implemented
        # In production: Use httpx to call Linear GraphQL API
        #
        # Example Linear API call:
        # POST https://api.linear.app/graphql
        # Headers: Authorization: {api_key}
        # Body: { query: "{ issue(id: \"...\") { ... } }" }

        return None

    def _linear_to_spec_ir(self, issue: LinearIssue) -> SpecIR:
        """Convert Linear issue to SpecIR."""
        # Map Linear priority (0-4) to spec priority
        priority_map = {
            0: "P3",  # No priority
            1: "P0",  # Urgent
            2: "P0",  # High
            3: "P1",  # Medium
            4: "P2",  # Low
        }

        # Map Linear state to spec status
        status_map = {
            "backlog": "DRAFT",
            "todo": "DRAFT",
            "in_progress": "PROPOSED",
            "done": "APPROVED",
            "canceled": "DEPRECATED",
        }

        requirements = self._extract_requirements_from_linear(issue)

        return SpecIR(
            spec_id=f"SPEC-LIN-{issue.id[:8]}",
            title=issue.title,
            version="1.0.0",
            status=status_map.get(issue.state.lower(), "DRAFT"),
            tier=["ALL"],
            owner="",
            last_updated="",
            tags=issue.labels,
            related_adrs=[],
            related_specs=[],
            requirements=requirements,
            acceptance_criteria=[],
        )

    def _extract_requirements_from_linear(
        self, issue: LinearIssue
    ) -> List[SpecRequirement]:
        """Extract requirements from Linear issue description."""
        if not issue.description:
            return [
                SpecRequirement(
                    id="REQ-001",
                    title=issue.title,
                    priority="P1",
                    tier=["ALL"],
                    given="the feature is implemented",
                    when="the user interacts with it",
                    then="it behaves as described",
                    acceptance_criteria=[],
                )
            ]

        return self._parse_acceptance_criteria(issue.description)

    # =========================================================================
    # Private Methods - Text
    # =========================================================================

    def _text_to_spec_ir(self, content: str, title: Optional[str]) -> SpecIR:
        """Convert plain text to SpecIR."""
        # Try to detect format first
        detected_format = self._detect_text_format(content)

        if detected_format == "user_story":
            return self._user_story_to_spec_ir(content, title)
        elif detected_format == "bdd":
            return self._bdd_to_spec_ir(content, title)
        else:
            return self._plain_text_to_spec_ir(content, title)

    def _detect_text_format(self, content: str) -> str:
        """Detect the format of text content."""
        content_lower = content.lower()

        if "as a " in content_lower and " i want " in content_lower:
            return "user_story"
        elif "feature:" in content_lower or "scenario:" in content_lower:
            return "bdd"
        elif "given " in content_lower and "when " in content_lower:
            return "bdd"
        else:
            return "plain"

    def _user_story_to_spec_ir(self, content: str, title: Optional[str]) -> SpecIR:
        """Convert user story to SpecIR."""
        # Parse user story format: As a [role], I want [feature] so that [benefit]
        pattern = r"as a ([^,]+),?\s*i want ([^,]+?)(?:,?\s*so that (.+))?"
        match = re.search(pattern, content, re.I | re.DOTALL)

        if match:
            role = match.group(1).strip()
            feature = match.group(2).strip()
            benefit = match.group(3).strip() if match.group(3) else "I can achieve my goal"

            spec_title = title or f"User Story: {feature[:50]}"

            return SpecIR(
                spec_id=f"SPEC-{abs(hash(content)) % 10000:04d}",
                title=spec_title,
                version="1.0.0",
                status="DRAFT",
                tier=["ALL"],
                owner="",
                last_updated="",
                tags=["user-story", "imported"],
                related_adrs=[],
                related_specs=[],
                requirements=[
                    SpecRequirement(
                        id="REQ-001",
                        title=feature[:50],
                        priority="P1",
                        tier=["ALL"],
                        given=f"I am a {role}",
                        when=f"I {feature}",
                        then=benefit,
                        user_story=content,
                        acceptance_criteria=[],
                    )
                ],
                acceptance_criteria=[],
            )

        # Fallback to plain text
        return self._plain_text_to_spec_ir(content, title)

    def _bdd_to_spec_ir(self, content: str, title: Optional[str]) -> SpecIR:
        """Convert BDD/Gherkin content to SpecIR."""
        # This is a simplified parser - the full parser is in parsers.py
        # Just extract basic structure for import purposes

        requirements = []
        req_idx = 0

        # Extract feature title
        feature_match = re.search(r"feature:\s*(.+)", content, re.I)
        spec_title = title or (feature_match.group(1).strip() if feature_match else "Imported BDD Spec")

        # Extract scenarios
        scenario_pattern = r"scenario:\s*(.+?)(?=scenario:|$)"
        scenarios = re.findall(scenario_pattern, content, re.I | re.DOTALL)

        for scenario_text in scenarios:
            req_idx += 1
            lines = scenario_text.strip().split("\n")
            scenario_title = lines[0].strip() if lines else f"Scenario {req_idx}"

            given = when = then = ""
            for line in lines[1:]:
                line = line.strip()
                if line.lower().startswith("given "):
                    given = line[6:].strip()
                elif line.lower().startswith("when "):
                    when = line[5:].strip()
                elif line.lower().startswith("then "):
                    then = line[5:].strip()

            requirements.append(
                SpecRequirement(
                    id=f"REQ-{str(req_idx).zfill(3)}",
                    title=scenario_title[:50],
                    priority="P1",
                    tier=["ALL"],
                    given=given or "precondition",
                    when=when or "action",
                    then=then or "result",
                    acceptance_criteria=[],
                )
            )

        if not requirements:
            requirements.append(
                SpecRequirement(
                    id="REQ-001",
                    title="Imported Requirement",
                    priority="P1",
                    tier=["ALL"],
                    given="precondition",
                    when="action",
                    then="result",
                    acceptance_criteria=[],
                )
            )

        return SpecIR(
            spec_id=f"SPEC-{abs(hash(content)) % 10000:04d}",
            title=spec_title,
            version="1.0.0",
            status="DRAFT",
            tier=["ALL"],
            owner="",
            last_updated="",
            tags=["bdd", "imported"],
            related_adrs=[],
            related_specs=[],
            requirements=requirements,
            acceptance_criteria=[],
        )

    def _plain_text_to_spec_ir(self, content: str, title: Optional[str]) -> SpecIR:
        """Convert plain text to SpecIR."""
        # Extract first line as title if not provided
        lines = content.strip().split("\n")
        spec_title = title or lines[0][:50] if lines else "Imported Specification"

        return SpecIR(
            spec_id=f"SPEC-{abs(hash(content)) % 10000:04d}",
            title=spec_title,
            version="1.0.0",
            status="DRAFT",
            tier=["ALL"],
            owner="",
            last_updated="",
            tags=["imported"],
            related_adrs=[],
            related_specs=[],
            requirements=[
                SpecRequirement(
                    id="REQ-001",
                    title=spec_title,
                    priority="P1",
                    tier=["ALL"],
                    given="the feature is implemented",
                    when="the user interacts with it",
                    then=content[:200] if len(content) > 200 else content,
                    acceptance_criteria=[],
                )
            ],
            acceptance_criteria=[],
        )


# Export service instance
import_service = SpecImportService()
