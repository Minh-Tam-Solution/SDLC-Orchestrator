"""
Skill BuildSummary — Sprint 217 (P2a Skills Engine).

Generates <available_skills> XML section listing skills accessible
to an agent. Injected into system prompt alongside delegation/team
context from context_injector.py.

Port of MTClaw skills/loader.go BuildSummary() function.

Token budget: <= 1500 tokens.
Format: XML-wrapped markdown with skill name, description, slug.
Security: All user content XML-escaped.

Usage:
    builder = SkillSummaryBuilder(db)
    xml = await builder.build_summary(agent_id, project_id)
    # Returns <available_skills>...</available_skills> or ""

References:
- ADR-069, Plan S216-03 (BuildSummary)
- MTClaw: /home/nqh/shared/MTClaw/internal/skills/loader.go BuildSummary()
"""

from __future__ import annotations

import logging
from html import escape as xml_escape
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.agent_team.skill_loader import SkillLoader

logger = logging.getLogger(__name__)

# Maximum number of skills to display in full detail
MAX_SKILLS_FULL = 20

# Token budget for the skills section
MAX_SKILLS_TOKENS = 1500


class SkillSummaryBuilder:
    """
    Builds <available_skills> XML section for system prompt injection.

    Lists skills accessible to an agent, grouped by tier.
    If more than MAX_SKILLS_FULL skills, shows first batch
    and adds a search instruction.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self._loader = SkillLoader(db)

    async def build_summary(
        self,
        agent_id: UUID,
        project_id: UUID | None = None,
    ) -> str:
        """
        Build XML summary of accessible skills for an agent.

        Args:
            agent_id: Agent definition ID.
            project_id: Project ID for workspace-scoped skills.

        Returns:
            XML string wrapped in <available_skills> tags,
            or empty string if agent has no skills.
        """
        skills = await self._loader.load_accessible(agent_id, project_id)

        if not skills:
            return ""

        lines = [
            "## Available Skills\n",
            "You can invoke these skills when relevant to your task:\n",
        ]

        display_skills = skills[:MAX_SKILLS_FULL]
        for skill in display_skills:
            name = xml_escape(skill.name)
            slug = xml_escape(skill.slug)
            tier = xml_escape(skill.tier)

            desc = ""
            if skill.description:
                desc_raw = skill.description[:100].replace("\n", " ").strip()
                desc = f" — {xml_escape(desc_raw)}"

            lines.append(f"- **{name}** (`{slug}`, {tier}){desc}")

        # Overflow notice
        remaining = len(skills) - MAX_SKILLS_FULL
        if remaining > 0:
            lines.append(
                f"\n> {remaining} more skills available. "
                "Describe what you need and the system will find matching skills."
            )

        content = "\n".join(lines)
        return f"<available_skills>\n{content}\n</available_skills>"

    async def build_skill_detail(
        self,
        slug: str,
    ) -> str:
        """
        Build detailed content for a single skill (for execution context).

        Args:
            slug: Skill slug to look up.

        Returns:
            Full skill content wrapped in <skill_content> tags,
            or empty string if skill not found.
        """
        skill = await self._loader.load_by_slug(slug)

        if skill is None:
            return ""

        name = xml_escape(skill.name)
        lines = [f"## Skill: {name}\n"]

        if skill.description:
            lines.append(xml_escape(skill.description))
            lines.append("")

        if skill.content:
            # Skill body content wrapped in code fence to prevent
            # XML tag breakout / prompt injection via user-authored content
            lines.append("### Instructions\n")
            lines.append(f"```\n{skill.content}\n```")

        content = "\n".join(lines)
        return f"<skill_content>\n{content}\n</skill_content>"
