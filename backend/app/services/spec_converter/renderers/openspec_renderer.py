"""
OpenSpec Renderer
Sprint 154 Day 2 - TDD Phase 2 (GREEN)

Renders SpecIR to OpenSpec YAML format (SDLC 6.0.5 Section 8).

Output Format:
---
spec_id: SPEC-XXX
title: Specification Title
version: 1.0.0
status: DRAFT
tier: [ALL]
owner: owner@example.com
last_updated: 2026-02-04
tags: [tag1, tag2]
related_adrs: [ADR-001]
related_specs: [SPEC-002]
---

# Requirements

## REQ-001: Requirement Title [P0] [ALL]

**GIVEN** precondition
**WHEN** action
**THEN** result

**User Story:** As a user...

---

## Acceptance Criteria

| ID | Scenario | Given | When | Then | Tier | Testable |
|---|---|---|---|---|---|---|
| AC-001 | ... | ... | ... | ... | ALL | ✅ |

Architecture: ADR-050 Renderer Layer
"""

from typing import List
import yaml

from ..models import SpecIR, SpecRequirement, AcceptanceCriterion


class OpenSpecRenderer:
    """
    Render SpecIR to OpenSpec YAML format.

    Produces SDLC 6.0.5 Section 8 compliant specification
    with YAML frontmatter and markdown body.

    Example output:
        ---
        spec_id: SPEC-001
        title: User Authentication
        ...
        ---

        # Requirements

        ## REQ-001: User Login [P0] [ALL]
        ...

    Architecture: ADR-050 Renderer Layer
    """

    async def render(self, ir: SpecIR) -> str:
        """
        Render SpecIR to OpenSpec format.

        Args:
            ir: SpecIR intermediate representation

        Returns:
            OpenSpec-formatted markdown with YAML frontmatter
        """
        lines: List[str] = []

        # Render YAML frontmatter
        frontmatter = self._build_frontmatter(ir)
        lines.append("---")
        lines.append(yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True, sort_keys=False).rstrip())
        lines.append("---")
        lines.append("")

        # Render Requirements section
        lines.append("# Requirements")
        lines.append("")

        if ir.requirements:
            for req in ir.requirements:
                req_lines = self._render_requirement(req)
                lines.extend(req_lines)
                lines.append("")
        else:
            lines.append("_No requirements defined._")
            lines.append("")

        # Render Acceptance Criteria section
        if ir.acceptance_criteria:
            lines.append("---")
            lines.append("")
            lines.append("## Acceptance Criteria")
            lines.append("")
            ac_table = self._render_acceptance_criteria_table(ir.acceptance_criteria)
            lines.extend(ac_table)
            lines.append("")

        return "\n".join(lines)

    def _build_frontmatter(self, ir: SpecIR) -> dict:
        """Build YAML frontmatter dictionary."""
        frontmatter = {
            "spec_id": ir.spec_id,
            "title": ir.title,
            "version": ir.version,
            "status": ir.status,
            "tier": ir.tier,
            "owner": ir.owner,
            "last_updated": ir.last_updated,
        }

        # Only include non-empty lists
        if ir.tags:
            frontmatter["tags"] = ir.tags
        else:
            frontmatter["tags"] = []

        if ir.related_adrs:
            frontmatter["related_adrs"] = ir.related_adrs
        else:
            frontmatter["related_adrs"] = []

        if ir.related_specs:
            frontmatter["related_specs"] = ir.related_specs
        else:
            frontmatter["related_specs"] = []

        return frontmatter

    def _render_requirement(self, req: SpecRequirement) -> List[str]:
        """Render a single requirement in BDD format."""
        lines: List[str] = []

        # Requirement header with ID, title, priority, and tier
        tier_str = ", ".join(req.tier) if req.tier else "ALL"
        lines.append(f"## {req.id}: {req.title} [{req.priority}] [{tier_str}]")
        lines.append("")

        # BDD format
        if req.given:
            lines.append(f"**GIVEN** {req.given}")
        if req.when:
            lines.append(f"**WHEN** {req.when}")
        if req.then:
            lines.append(f"**THEN** {req.then}")

        # User story if present
        if req.user_story:
            lines.append("")
            lines.append(f"**User Story:** {req.user_story}")

        # Acceptance criteria for this requirement
        if req.acceptance_criteria:
            lines.append("")
            lines.append("**Acceptance Criteria:**")
            for ac in req.acceptance_criteria:
                lines.append(f"- {ac}")

        return lines

    def _render_acceptance_criteria_table(
        self, criteria: List[AcceptanceCriterion]
    ) -> List[str]:
        """Render acceptance criteria as markdown table."""
        lines: List[str] = []

        # Table header
        lines.append("| ID | Scenario | Given | When | Then | Tier | Testable |")
        lines.append("|---|---|---|---|---|---|---|")

        # Table rows
        for ac in criteria:
            tier_str = ", ".join(ac.tier) if ac.tier else "ALL"
            testable_str = "✅" if ac.testable else "❌"
            lines.append(
                f"| {ac.id} | {ac.scenario} | {ac.given} | {ac.when} | {ac.then} | {tier_str} | {testable_str} |"
            )

        return lines
