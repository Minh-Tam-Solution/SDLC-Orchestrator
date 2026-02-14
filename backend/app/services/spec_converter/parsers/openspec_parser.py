"""
OpenSpec YAML Parser
Sprint 154 - Spec Standard Completion

Parses SDLC 6.0.5 specification format to SpecIR.

Supports:
- YAML frontmatter extraction
- BDD requirements (GIVEN-WHEN-THEN)
- Acceptance criteria tables
- Related ADRs/Specs references

Format: SDLC 6.0.5 Section 8 Unified Specification Standard
"""

import re
from datetime import datetime
from typing import Any, Optional

import yaml

from ..models import AcceptanceCriterion, SpecIR, SpecRequirement


class OpenSpecParser:
    """
    Parse OpenSpec YAML specifications to SpecIR.

    Example input:
        ---
        spec_id: SPEC-0001
        title: User Authentication
        status: DRAFT
        tier: [STANDARD, PROFESSIONAL]
        ...
        ---

        # SPEC-0001: User Authentication

        ## Requirements

        ### REQ-001: Login
        **GIVEN** a user
        **WHEN** they login
        **THEN** they are authenticated

    Architecture: ADR-050 Parser Layer
    """

    # Regex patterns
    FRONTMATTER_PATTERN = re.compile(r"^---\s*\n(.*?)\n---", re.DOTALL)
    # Match both ## and ### for requirement headers
    # Format: ## REQ-001: Title [P0] [TIER] or ### REQ-001: Title
    REQUIREMENT_HEADER_PATTERN = re.compile(
        r"^#{2,3}\s*(?:REQ-)?(\d+)[:.]?\s*(.+?)(?:\s+\[(P\d)\])?\s*(?:\[[^\]]+\])?$",
        re.MULTILINE,
    )
    PRIORITY_PATTERN = re.compile(r"\*\*Priority\*\*:\s*(P[0-3])", re.IGNORECASE)
    # Also match priority from header format [P0]
    HEADER_PRIORITY_PATTERN = re.compile(r"\[(P[0-3])\]", re.IGNORECASE)
    TIER_PATTERN = re.compile(r"\*\*Tier\*\*:\s*(.+)$", re.MULTILINE | re.IGNORECASE)
    GIVEN_PATTERN = re.compile(r"\*\*GIVEN\*\*\s+(.+?)(?=\*\*WHEN\*\*|$)", re.DOTALL)
    WHEN_PATTERN = re.compile(r"\*\*WHEN\*\*\s+(.+?)(?=\*\*THEN\*\*|$)", re.DOTALL)
    THEN_PATTERN = re.compile(r"\*\*THEN\*\*\s+(.+?)(?=\n\n|\*\*|$)", re.DOTALL)
    AC_TABLE_PATTERN = re.compile(
        r"\|\s*ID\s*\|\s*Scenario\s*\|.*?\n\|[-|]+\|\n((?:\|.*?\n)+)", re.IGNORECASE
    )

    async def parse(self, content: str) -> SpecIR:
        """
        Parse OpenSpec YAML content to SpecIR.

        Args:
            content: OpenSpec markdown content with YAML frontmatter

        Returns:
            SpecIR with extracted metadata and requirements

        Raises:
            ValueError: If content is empty
        """
        if not content or not content.strip():
            raise ValueError("Empty content provided")

        # Extract frontmatter
        frontmatter = self._extract_frontmatter(content)

        # Extract body (after frontmatter)
        body = self._extract_body(content)

        # Parse requirements from body
        requirements = self._extract_requirements(body)

        # Parse acceptance criteria from body
        acceptance_criteria = self._extract_acceptance_criteria(body)

        # Build SpecIR
        return SpecIR(
            spec_id=frontmatter.get("spec_id", self._generate_spec_id(content)),
            title=frontmatter.get("title", "Untitled Specification"),
            version=str(frontmatter.get("version", "1.0.0")),
            status=frontmatter.get("status", "DRAFT"),
            tier=self._normalize_tier(frontmatter.get("tier", [])),
            owner=frontmatter.get("owner", ""),
            last_updated=frontmatter.get(
                "last_updated", datetime.utcnow().isoformat()
            ),
            tags=frontmatter.get("tags", []),
            related_adrs=frontmatter.get("related_adrs", []),
            related_specs=frontmatter.get("related_specs", []),
            requirements=requirements,
            acceptance_criteria=acceptance_criteria,
        )

    def _extract_frontmatter(self, content: str) -> dict[str, Any]:
        """Extract YAML frontmatter from content."""
        match = self.FRONTMATTER_PATTERN.search(content)
        if match:
            try:
                return yaml.safe_load(match.group(1)) or {}
            except yaml.YAMLError:
                return {}
        return {}

    def _extract_body(self, content: str) -> str:
        """Extract body content after frontmatter."""
        match = self.FRONTMATTER_PATTERN.search(content)
        if match:
            return content[match.end() :].strip()
        return content.strip()

    def _normalize_tier(self, tier: Any) -> list[str]:
        """Normalize tier to list format."""
        if isinstance(tier, str):
            return [tier]
        if isinstance(tier, list):
            return tier
        return ["LITE", "STANDARD", "PROFESSIONAL", "ENTERPRISE"]

    def _extract_requirements(self, body: str) -> list[SpecRequirement]:
        """Extract requirements from markdown body."""
        requirements = []

        # Find all requirement headers
        headers = list(self.REQUIREMENT_HEADER_PATTERN.finditer(body))

        for i, header_match in enumerate(headers):
            req_num = header_match.group(1)
            req_title = header_match.group(2).strip()
            # Group 3 may contain priority from header [P0]
            header_priority = header_match.group(3) if header_match.lastindex >= 3 else None

            # Determine content bounds
            start = header_match.end()
            if i + 1 < len(headers):
                end = headers[i + 1].start()
            else:
                end = len(body)

            req_content = body[start:end]

            # Extract BDD clauses
            given = self._extract_clause(req_content, self.GIVEN_PATTERN)
            when = self._extract_clause(req_content, self.WHEN_PATTERN)
            then = self._extract_clause(req_content, self.THEN_PATTERN)

            # Extract priority - prefer header priority, then body, then default
            priority = "P1"
            if header_priority:
                priority = header_priority.upper()
            else:
                priority_match = self.PRIORITY_PATTERN.search(req_content)
                if priority_match:
                    priority = priority_match.group(1).upper()

            # Extract tier
            tier_match = self.TIER_PATTERN.search(req_content)
            tier = ["ALL"]
            if tier_match:
                tier_text = tier_match.group(1).strip()
                if "+" in tier_text:
                    # Handle STANDARD+ style
                    tier = [tier_text]
                else:
                    tier = [t.strip() for t in tier_text.split(",")]

            requirements.append(
                SpecRequirement(
                    id=f"REQ-{req_num.zfill(3)}",
                    title=req_title,
                    priority=priority,
                    tier=tier,
                    given=given,
                    when=when,
                    then=then,
                )
            )

        return requirements

    def _extract_clause(self, content: str, pattern: re.Pattern) -> str:
        """Extract a BDD clause from content."""
        match = pattern.search(content)
        if match:
            text = match.group(1).strip()
            # Clean up newlines and extra spaces
            text = re.sub(r"\s+", " ", text)
            return text
        return ""

    def _extract_acceptance_criteria(self, body: str) -> list[AcceptanceCriterion]:
        """Extract acceptance criteria from markdown tables."""
        criteria = []

        match = self.AC_TABLE_PATTERN.search(body)
        if match:
            table_rows = match.group(1)
            for row in table_rows.strip().split("\n"):
                cells = [c.strip() for c in row.split("|") if c.strip()]
                if len(cells) >= 2:
                    ac_id = cells[0]
                    scenario = cells[1]
                    tier = cells[2] if len(cells) > 2 else "ALL"
                    testable = (
                        cells[3].upper() in ("YES", "TRUE", "✅")
                        if len(cells) > 3
                        else True
                    )

                    criteria.append(
                        AcceptanceCriterion(
                            id=ac_id,
                            scenario=scenario,
                            tier=[tier] if isinstance(tier, str) else tier,
                            testable=testable,
                        )
                    )

        return criteria

    def _generate_spec_id(self, content: str) -> str:
        """Generate spec_id from content hash if not provided."""
        import hashlib

        content_hash = hashlib.sha256(content.encode()).hexdigest()[:6].upper()
        return f"SPEC-{content_hash}"
