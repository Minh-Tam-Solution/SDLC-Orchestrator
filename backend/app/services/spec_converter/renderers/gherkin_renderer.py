"""
Gherkin Renderer
Sprint 154 Day 2 - TDD Phase 2 (GREEN)

Renders SpecIR to BDD/Gherkin format.

Output Format:
@tag1 @tag2
Feature: Feature Title
  As a user
  I want functionality
  So that benefit

  @priority-P0
  Scenario: Scenario Title
    Given precondition
    When action
    Then result

Architecture: ADR-050 Renderer Layer
"""

from typing import List

from ..models import SpecIR, SpecRequirement


class GherkinRenderer:
    """
    Render SpecIR to Gherkin/BDD format.

    Converts intermediate representation to standard Gherkin
    feature file format for use with Cucumber, Behave, etc.

    Example output:
        @authentication @security
        Feature: User Authentication
          Version: 1.0.0
          Status: DRAFT

          @P0
          Scenario: User Login
            Given a registered user with valid credentials
            When the user submits the login form
            Then the user is authenticated

    Architecture: ADR-050 Renderer Layer
    """

    async def render(self, ir: SpecIR) -> str:
        """
        Render SpecIR to Gherkin format.

        Args:
            ir: SpecIR intermediate representation

        Returns:
            Gherkin-formatted feature file content
        """
        lines: List[str] = []

        # Render tags
        if ir.tags:
            tag_line = " ".join(f"@{tag}" for tag in ir.tags)
            lines.append(tag_line)

        # Render Feature header
        lines.append(f"Feature: {ir.title}")

        # Render feature description
        lines.append(f"  Version: {ir.version}")
        lines.append(f"  Status: {ir.status}")
        if ir.spec_id:
            lines.append(f"  Spec ID: {ir.spec_id}")
        lines.append("")

        # Render scenarios from requirements
        for req in ir.requirements:
            scenario_lines = self._render_scenario(req)
            lines.extend(scenario_lines)
            lines.append("")

        return "\n".join(lines).rstrip() + "\n"

    def _render_scenario(self, req: SpecRequirement) -> List[str]:
        """Render a single requirement as a Gherkin scenario."""
        lines: List[str] = []

        # Priority tag
        if req.priority:
            lines.append(f"  @{req.priority}")

        # Scenario header
        lines.append(f"  Scenario: {req.title}")

        # Given steps
        given_parts = self._split_steps(req.given)
        if given_parts:
            lines.append(f"    Given {given_parts[0]}")
            for part in given_parts[1:]:
                lines.append(f"    And {part}")

        # When steps
        when_parts = self._split_steps(req.when)
        if when_parts:
            lines.append(f"    When {when_parts[0]}")
            for part in when_parts[1:]:
                lines.append(f"    And {part}")

        # Then steps
        then_parts = self._split_steps(req.then)
        if then_parts:
            lines.append(f"    Then {then_parts[0]}")
            for part in then_parts[1:]:
                lines.append(f"    And {part}")

        return lines

    def _split_steps(self, step_text: str) -> List[str]:
        """
        Split compound step text into individual steps.

        Handles:
        - Semicolon-separated steps: "step one; step two"
        - Newline-separated steps
        """
        if not step_text:
            return []

        # Split on semicolons or newlines
        parts = []
        for part in step_text.replace("\n", ";").split(";"):
            part = part.strip()
            if part:
                parts.append(part)

        return parts
