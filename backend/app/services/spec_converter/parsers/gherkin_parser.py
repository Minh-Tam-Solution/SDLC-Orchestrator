"""
Gherkin (BDD) Parser
Sprint 154 - Spec Standard Completion

Parses Gherkin feature files to SpecIR.

Supports:
- Feature extraction
- Scenario/Scenario Outline parsing
- Given/When/Then step extraction
- Tags extraction
- Background handling
- AND step continuation

Reference: https://cucumber.io/docs/gherkin/reference/
"""

import hashlib
import re
from datetime import datetime
from typing import Optional

from ..models import SpecIR, SpecRequirement


class GherkinParser:
    """
    Parse Gherkin (BDD) feature files to SpecIR.

    Example input:
        @auth @security
        Feature: User Login
          As a user, I want to login

          Scenario: Successful login
            Given a registered user
            When they enter valid credentials
            Then they are logged in

    Architecture: ADR-050 Parser Layer
    """

    # Regex patterns for Gherkin elements
    FEATURE_PATTERN = re.compile(r"^\s*Feature:\s*(.+)$", re.MULTILINE)
    SCENARIO_PATTERN = re.compile(
        r"^\s*Scenario(?:\s+Outline)?:\s*(.+)$", re.MULTILINE
    )
    TAG_PATTERN = re.compile(r"@(\w+)")
    BACKGROUND_PATTERN = re.compile(r"^\s*Background:\s*$", re.MULTILINE)

    STEP_PATTERNS = {
        "given": re.compile(r"^\s*Given\s+(.+)$", re.MULTILINE | re.IGNORECASE),
        "when": re.compile(r"^\s*When\s+(.+)$", re.MULTILINE | re.IGNORECASE),
        "then": re.compile(r"^\s*Then\s+(.+)$", re.MULTILINE | re.IGNORECASE),
        "and": re.compile(r"^\s*And\s+(.+)$", re.MULTILINE | re.IGNORECASE),
    }

    async def parse(self, content: str) -> SpecIR:
        """
        Parse Gherkin content to SpecIR.

        Args:
            content: Gherkin feature file content

        Returns:
            SpecIR with extracted requirements

        Raises:
            ValueError: If content is empty or invalid
        """
        if not content or not content.strip():
            raise ValueError("Empty content provided")

        # Extract feature name
        feature_name = self._extract_feature(content)
        if not feature_name:
            raise ValueError("No Feature found in content")

        # Extract scenarios
        scenarios = self._extract_scenarios(content)
        if not scenarios:
            raise ValueError("No Scenario found in content")

        # Extract tags
        tags = self._extract_tags(content)

        # Extract background (if any)
        background = self._extract_background(content)

        # Convert scenarios to requirements
        requirements = []
        for i, scenario in enumerate(scenarios):
            req = self._scenario_to_requirement(
                scenario=scenario,
                index=i,
                background=background,
            )
            requirements.append(req)

        # Generate spec_id from feature name
        spec_id = self._generate_spec_id(feature_name)

        return SpecIR(
            spec_id=spec_id,
            title=feature_name,
            last_updated=datetime.utcnow().isoformat(),
            tags=tags,
            requirements=requirements,
        )

    def _extract_feature(self, content: str) -> Optional[str]:
        """Extract feature name from content."""
        match = self.FEATURE_PATTERN.search(content)
        if match:
            return match.group(1).strip()
        return None

    def _extract_tags(self, content: str) -> list[str]:
        """Extract tags from content (e.g., @auth @security)."""
        # Get tags before Feature line
        feature_match = self.FEATURE_PATTERN.search(content)
        if feature_match:
            pre_feature = content[: feature_match.start()]
            tags = self.TAG_PATTERN.findall(pre_feature)
            return list(set(tags))
        return []

    def _extract_background(self, content: str) -> Optional[dict]:
        """Extract Background section if present."""
        match = self.BACKGROUND_PATTERN.search(content)
        if not match:
            return None

        # Find the end of background (next Scenario or end of feature)
        start = match.end()
        scenario_match = self.SCENARIO_PATTERN.search(content[start:])
        end = start + scenario_match.start() if scenario_match else len(content)

        background_content = content[start:end]
        steps = self._extract_steps(background_content)

        return steps

    def _extract_scenarios(self, content: str) -> list[dict]:
        """Extract all scenarios from content."""
        scenarios = []

        # Find all scenario matches
        scenario_matches = list(self.SCENARIO_PATTERN.finditer(content))

        for i, match in enumerate(scenario_matches):
            scenario_name = match.group(1).strip()

            # Determine scenario content bounds
            start = match.end()
            if i + 1 < len(scenario_matches):
                end = scenario_matches[i + 1].start()
            else:
                end = len(content)

            scenario_content = content[start:end]

            # Extract tags for this scenario
            tag_start = content.rfind("\n", 0, match.start())
            if tag_start == -1:
                tag_start = 0
            tag_region = content[tag_start : match.start()]
            scenario_tags = self.TAG_PATTERN.findall(tag_region)

            # Extract steps
            steps = self._extract_steps(scenario_content)

            scenarios.append(
                {
                    "name": scenario_name,
                    "tags": scenario_tags,
                    "steps": steps,
                    **steps,
                }
            )

        return scenarios

    def _extract_steps(self, content: str) -> dict:
        """
        Extract Given/When/Then steps from content.

        Handles AND continuation by appending to the previous step type.
        """
        result = {
            "given": "",
            "when": "",
            "then": "",
        }

        lines = content.split("\n")
        current_step_type = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check for step keywords
            if line.lower().startswith("given "):
                current_step_type = "given"
                step_text = line[6:].strip()
                result["given"] = self._append_step(result["given"], step_text)
            elif line.lower().startswith("when "):
                current_step_type = "when"
                step_text = line[5:].strip()
                result["when"] = self._append_step(result["when"], step_text)
            elif line.lower().startswith("then "):
                current_step_type = "then"
                step_text = line[5:].strip()
                result["then"] = self._append_step(result["then"], step_text)
            elif line.lower().startswith("and "):
                # AND continues the previous step type
                if current_step_type:
                    step_text = line[4:].strip()
                    result[current_step_type] = self._append_step(
                        result[current_step_type], step_text
                    )

        return result

    def _append_step(self, existing: str, new: str) -> str:
        """Append a step to existing text."""
        if existing:
            return f"{existing} and {new}"
        return new

    def _scenario_to_requirement(
        self,
        scenario: dict,
        index: int,
        background: Optional[dict] = None,
    ) -> SpecRequirement:
        """
        Convert a scenario to a SpecRequirement.

        Args:
            scenario: Scenario dict with name and steps
            index: Scenario index for ID generation
            background: Optional background steps to prepend

        Returns:
            SpecRequirement with BDD format
        """
        # Combine background with scenario given
        given = scenario.get("given", "")
        if background and background.get("given"):
            given = f"{background['given']} and {given}" if given else background["given"]

        return SpecRequirement(
            id=f"REQ-{index + 1:03d}",
            title=scenario["name"],
            given=given,
            when=scenario.get("when", ""),
            then=scenario.get("then", ""),
        )

    def _generate_spec_id(self, feature_name: str) -> str:
        """
        Generate deterministic spec_id from feature name.

        Uses hash to ensure consistency across runs.
        """
        # Create a hash of the feature name for uniqueness
        name_hash = hashlib.sha256(feature_name.encode()).hexdigest()[:6].upper()
        return f"SPEC-{name_hash}"
