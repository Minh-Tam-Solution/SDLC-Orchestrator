"""
User Story Parser
Sprint 154 - Spec Standard Completion

Parses User Stories to SpecIR with AI-assisted BDD conversion.

Supports:
- Standard "As a... I want... So that..." format
- "In order to... As a... I want..." variant
- Multiple user stories
- Acceptance criteria extraction

Format: User Stories → BDD SpecIR
Architecture: ADR-050 Parser Layer
"""

import re
from datetime import datetime
from typing import Any

from ..models import AcceptanceCriterion, SpecIR, SpecRequirement


class UserStoryParser:
    """
    Parse User Stories to SpecIR.

    Converts user story format to BDD GIVEN-WHEN-THEN structure:
    - "As a [actor]" → GIVEN a [actor]
    - "I want [action]" → WHEN they [action]
    - "So that [outcome]" → THEN [outcome]

    Example input:
        As a registered user
        I want to reset my password
        So that I can regain access to my account

    Architecture: ADR-050 Parser Layer
    """

    # Regex patterns for user story extraction
    STANDARD_PATTERN = re.compile(
        r"As\s+an?\s+(.+?)(?:,\s*|\s+)I\s+want\s+(?:to\s+)?(.+?)(?:\s+so\s+that\s+(.+))?$",
        re.IGNORECASE | re.DOTALL,
    )

    # Alternative format: "In order to... As a... I want..."
    ALTERNATIVE_PATTERN = re.compile(
        r"In\s+order\s+to\s+(.+?)\s+As\s+an?\s+(.+?)(?:,\s*|\s+)I\s+want\s+(?:to\s+)?(.+)$",
        re.IGNORECASE | re.DOTALL,
    )

    # Pattern for numbered user stories
    NUMBERED_STORY_PATTERN = re.compile(
        r"(?:User\s+Story\s+\d+:|Story\s+\d+:|\d+\.)\s*(.+?)(?=(?:User\s+Story\s+\d+:|Story\s+\d+:|\d+\.)|$)",
        re.IGNORECASE | re.DOTALL,
    )

    # Acceptance criteria pattern
    AC_PATTERN = re.compile(
        r"Acceptance\s+Criteria:?\s*\n((?:[-•*]\s*.+\n?)+)", re.IGNORECASE
    )
    AC_ITEM_PATTERN = re.compile(r"[-•*]\s*(.+)")

    async def parse(self, content: str) -> SpecIR:
        """
        Parse User Story content to SpecIR.

        Args:
            content: User story text in standard or alternative format

        Returns:
            SpecIR with extracted requirements

        Raises:
            ValueError: If content is empty
        """
        if not content or not content.strip():
            raise ValueError("Empty content provided")

        content = content.strip()

        # Check for multiple numbered stories
        numbered_matches = list(self.NUMBERED_STORY_PATTERN.finditer(content))
        if numbered_matches and len(numbered_matches) > 1:
            requirements = []
            for i, match in enumerate(numbered_matches, 1):
                story_text = match.group(1).strip()
                req = self._parse_single_story(story_text, f"REQ-{str(i).zfill(3)}")
                if req:
                    requirements.append(req)
        else:
            # Single story or unstructured
            req = self._parse_single_story(content, "REQ-001")
            requirements = [req] if req else []

        # Generate title from first requirement or content
        title = self._generate_title(content, requirements)

        return SpecIR(
            spec_id=self._generate_spec_id(content),
            title=title,
            version="1.0.0",
            status="DRAFT",
            tier=["ALL"],
            owner="",
            last_updated=datetime.utcnow().isoformat(),
            tags=["user-story"],
            related_adrs=[],
            related_specs=[],
            requirements=requirements,
            acceptance_criteria=[],
        )

    def _parse_single_story(
        self, content: str, req_id: str
    ) -> SpecRequirement | None:
        """Parse a single user story to a requirement."""
        content = content.strip()

        # Extract acceptance criteria first
        acceptance_criteria: list[str] = []
        ac_match = self.AC_PATTERN.search(content)
        if ac_match:
            ac_text = ac_match.group(1)
            acceptance_criteria = [
                m.group(1).strip()
                for m in self.AC_ITEM_PATTERN.finditer(ac_text)
            ]
            # Remove AC from content for cleaner parsing
            content = content[: ac_match.start()].strip()

        # Try alternative format first (In order to...)
        alt_match = self.ALTERNATIVE_PATTERN.search(content)
        if alt_match:
            outcome = alt_match.group(1).strip()
            actor = alt_match.group(2).strip()
            action = alt_match.group(3).strip()

            return self._build_requirement(
                req_id=req_id,
                actor=actor,
                action=action,
                outcome=outcome,
                original_story=content,
                acceptance_criteria=acceptance_criteria,
            )

        # Try standard format (As a... I want... So that...)
        std_match = self.STANDARD_PATTERN.search(content)
        if std_match:
            actor = std_match.group(1).strip()
            action = std_match.group(2).strip()
            outcome = std_match.group(3).strip() if std_match.group(3) else ""

            return self._build_requirement(
                req_id=req_id,
                actor=actor,
                action=action,
                outcome=outcome,
                original_story=content,
                acceptance_criteria=acceptance_criteria,
            )

        # Fallback: try to extract any meaningful content
        if "As a" in content or "As an" in content:
            # Partial match - extract what we can
            actor_match = re.search(r"As\s+an?\s+([^,\n]+)", content, re.IGNORECASE)
            action_match = re.search(
                r"I\s+want\s+(?:to\s+)?([^,\n]+)", content, re.IGNORECASE
            )

            if actor_match:
                actor = actor_match.group(1).strip()
                action = action_match.group(1).strip() if action_match else ""

                return self._build_requirement(
                    req_id=req_id,
                    actor=actor,
                    action=action,
                    outcome="",
                    original_story=content,
                    acceptance_criteria=acceptance_criteria,
                )

        # Cannot parse - return None (caller handles this)
        return None

    def _build_requirement(
        self,
        req_id: str,
        actor: str,
        action: str,
        outcome: str,
        original_story: str,
        acceptance_criteria: list[str],
    ) -> SpecRequirement:
        """Build a SpecRequirement from parsed components."""
        # Clean up action - remove trailing "so that" if present
        action = re.sub(r"\s*so\s+that.*$", "", action, flags=re.IGNORECASE).strip()

        # Build GIVEN clause
        given = f"a {actor}" if not actor.lower().startswith("a ") else actor

        # Build WHEN clause
        when = action
        if not any(
            action.lower().startswith(v)
            for v in ["they", "the user", "i", "we", "he", "she"]
        ):
            when = f"they {action}"

        # Build THEN clause
        then = outcome if outcome else ""
        if acceptance_criteria and not then:
            # Use acceptance criteria for THEN if no "so that" provided
            then = "; ".join(acceptance_criteria[:2])  # Use first 2 criteria

        # Generate title from action
        title = self._extract_title_from_action(action, actor)

        return SpecRequirement(
            id=req_id,
            title=title,
            priority="P1",
            tier=["ALL"],
            given=given,
            when=when,
            then=then,
            user_story=original_story,
            acceptance_criteria=acceptance_criteria,
        )

    def _extract_title_from_action(self, action: str, actor: str) -> str:
        """Extract a concise title from the action."""
        # Clean up action for title
        title = action.strip()

        # Remove common prefixes
        title = re.sub(r"^(?:to\s+)?", "", title, flags=re.IGNORECASE)

        # Capitalize first letter
        if title:
            title = title[0].upper() + title[1:]

        # Truncate if too long
        if len(title) > 60:
            title = title[:57] + "..."

        return title if title else f"{actor} Feature"

    def _generate_title(
        self, content: str, requirements: list[SpecRequirement]
    ) -> str:
        """Generate a title for the specification."""
        if requirements:
            # Use first requirement title
            return requirements[0].title

        # Extract from content
        lines = content.strip().split("\n")
        for line in lines:
            line = line.strip()
            if line and len(line) > 5:
                # Clean up and use as title
                title = re.sub(r"^(?:As\s+an?\s+|I\s+want\s+)", "", line, flags=re.IGNORECASE)
                if len(title) > 60:
                    title = title[:57] + "..."
                return title

        return "User Story Specification"

    def _generate_spec_id(self, content: str) -> str:
        """Generate spec_id from content hash."""
        import hashlib

        content_hash = hashlib.sha256(content.encode()).hexdigest()[:6].upper()
        return f"SPEC-US-{content_hash}"
