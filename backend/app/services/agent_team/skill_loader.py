"""
Skill Loader — Sprint 217 (P2a Skills Engine).

Loads skills from 5 tiers in priority order.
Higher-priority tier overrides lower for the same slug.

5-Tier Priority (highest → lowest):
  1. workspace       — project-specific overrides
  2. project_agent   — agent-specific skills in project
  3. personal_agent  — agent's personal library
  4. global          — available to all agents
  5. builtin         — system defaults

Port of MTClaw skills/loader.go (361 LOC).

Usage:
    loader = SkillLoader(db)
    skills = await loader.load_accessible(agent_id, project_id)
    # Returns deduplicated list, highest-priority tier wins per slug

References:
- ADR-069, Plan S216 (Skills Engine P2a)
- MTClaw: /home/nqh/shared/MTClaw/internal/skills/loader.go
"""

from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy import and_, exists, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.skill_agent_grant import SkillAgentGrant
from app.models.skill_definition import (
    SkillDefinition,
    SKILL_TIER_PRIORITY,
    SKILL_TIERS,
)

# Tiers that don't require explicit grants (open to all agents)
OPEN_TIERS = frozenset({"global", "builtin"})

logger = logging.getLogger(__name__)


class SkillLoader:
    """
    Loads skills accessible to an agent, applying 5-tier hierarchy.

    Skills are deduplicated by slug — highest-priority tier wins.
    Visibility filtering:
    - public: accessible to any agent
    - internal: accessible to agents in the same project
    - private: accessible only to the owning agent
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def load_accessible(
        self,
        agent_id: UUID,
        project_id: UUID | None = None,
    ) -> list[SkillDefinition]:
        """
        Load all skills accessible to an agent, deduplicated by slug.

        Queries all 5 tiers and merges results with priority ordering.
        Highest-tier skill wins for each slug.

        Sprint 218: Restricted tiers (workspace, project_agent, personal_agent)
        require an explicit grant row in skill_agent_grants.
        Open tiers (global, builtin) remain accessible without grants.

        Args:
            agent_id: Agent definition ID.
            project_id: Project ID for workspace/project_agent scoping.

        Returns:
            List of SkillDefinition objects, one per unique slug,
            ordered by tier priority (highest first).
        """
        # Subquery: does this agent have a grant for a given skill?
        grant_exists = exists(
            select(SkillAgentGrant.id).where(
                and_(
                    SkillAgentGrant.skill_definition_id == SkillDefinition.id,
                    SkillAgentGrant.agent_definition_id == agent_id,
                )
            )
        )

        conditions = [SkillDefinition.is_active.is_(True)]

        # Build tier-specific OR conditions
        tier_conditions = []

        # Tier 5: builtin — always available (open tier, no grant needed)
        tier_conditions.append(SkillDefinition.tier == "builtin")

        # Tier 4: global — always available, public only (open tier, no grant needed)
        tier_conditions.append(
            and_(
                SkillDefinition.tier == "global",
                SkillDefinition.visibility == "public",
            )
        )

        # Tier 3: personal_agent — owned by this agent OR has grant
        tier_conditions.append(
            and_(
                SkillDefinition.tier == "personal_agent",
                or_(
                    SkillDefinition.agent_definition_id == agent_id,
                    grant_exists,
                ),
            )
        )

        if project_id is not None:
            # Tier 2: project_agent — in this project, (for this agent or public) AND has grant
            tier_conditions.append(
                and_(
                    SkillDefinition.tier == "project_agent",
                    SkillDefinition.project_id == project_id,
                    or_(
                        SkillDefinition.agent_definition_id == agent_id,
                        SkillDefinition.visibility.in_(["public", "internal"]),
                    ),
                    grant_exists,
                )
            )

            # Tier 1: workspace — project-level, public/internal AND has grant
            tier_conditions.append(
                and_(
                    SkillDefinition.tier == "workspace",
                    SkillDefinition.project_id == project_id,
                    SkillDefinition.visibility.in_(["public", "internal"]),
                    grant_exists,
                )
            )

        conditions.append(or_(*tier_conditions))

        result = await self.db.execute(
            select(SkillDefinition).where(and_(*conditions))
        )
        all_skills = list(result.scalars().all())

        # Deduplicate by slug — highest-priority tier wins
        return self._deduplicate_by_tier(all_skills)

    async def load_by_tier(
        self,
        tier: str,
        project_id: UUID | None = None,
        agent_id: UUID | None = None,
    ) -> list[SkillDefinition]:
        """
        Load skills from a specific tier.

        Sprint 218 (CTO F1): Restricted tiers (workspace, project_agent,
        personal_agent) require an explicit grant when agent_id is provided.
        Open tiers (global, builtin) bypass grant checks.

        Args:
            tier: One of the 5 tier names.
            project_id: Filter by project (for workspace/project_agent).
            agent_id: Filter by agent (for personal_agent/project_agent).

        Returns:
            List of SkillDefinition objects from the specified tier.

        Raises:
            ValueError: If tier is not a valid tier name.
        """
        if tier not in SKILL_TIERS:
            raise ValueError(
                f"Invalid tier '{tier}'. Valid: {', '.join(SKILL_TIERS)}"
            )

        conditions = [
            SkillDefinition.is_active.is_(True),
            SkillDefinition.tier == tier,
        ]

        if project_id is not None:
            conditions.append(SkillDefinition.project_id == project_id)

        if agent_id is not None:
            conditions.append(SkillDefinition.agent_definition_id == agent_id)

        # Grant check for restricted tiers (CTO F1 — access control)
        if agent_id is not None and tier not in OPEN_TIERS:
            grant_exists = exists(
                select(SkillAgentGrant.id).where(
                    and_(
                        SkillAgentGrant.skill_definition_id == SkillDefinition.id,
                        SkillAgentGrant.agent_definition_id == agent_id,
                    )
                )
            )
            conditions.append(grant_exists)

        result = await self.db.execute(
            select(SkillDefinition).where(and_(*conditions))
        )
        return list(result.scalars().all())

    async def load_by_slug(self, slug: str) -> SkillDefinition | None:
        """
        Load a single skill by slug.

        Args:
            slug: Unique skill identifier.

        Returns:
            SkillDefinition if found and active, None otherwise.
        """
        result = await self.db.execute(
            select(SkillDefinition).where(
                and_(
                    SkillDefinition.slug == slug,
                    SkillDefinition.is_active.is_(True),
                )
            )
        )
        return result.scalar_one_or_none()

    def _deduplicate_by_tier(
        self,
        skills: list[SkillDefinition],
    ) -> list[SkillDefinition]:
        """
        Deduplicate skills by slug — highest-priority tier wins.

        Args:
            skills: All matching skills (may have duplicate slugs).

        Returns:
            Deduplicated list, sorted by tier priority then name.
        """
        slug_map: dict[str, SkillDefinition] = {}

        for skill in skills:
            existing = slug_map.get(skill.slug)
            if existing is None:
                slug_map[skill.slug] = skill
            else:
                # Higher priority = lower index in SKILL_TIER_PRIORITY
                existing_priority = SKILL_TIER_PRIORITY.get(existing.tier, 99)
                new_priority = SKILL_TIER_PRIORITY.get(skill.tier, 99)
                if new_priority < existing_priority:
                    slug_map[skill.slug] = skill

        # Sort by tier priority (highest first), then name
        result = sorted(
            slug_map.values(),
            key=lambda s: (SKILL_TIER_PRIORITY.get(s.tier, 99), s.name),
        )

        logger.debug(
            "Deduplicated %d skills → %d unique slugs",
            len(skills),
            len(result),
        )
        return result


class SkillFrontmatterParser:
    """
    Simple YAML-like frontmatter parser for SKILL.md files.

    Parses content between --- delimiters:
    ---
    name: Code Review
    description: Standard code review checklist
    tier: workspace
    tags: review, quality
    ---
    Actual skill content here...

    Port of MTClaw skills/loader.go parseFrontmatter().
    """

    @staticmethod
    def parse(raw_content: str) -> tuple[dict, str]:
        """
        Parse frontmatter and body from raw SKILL.md content.

        Args:
            raw_content: Full file content with --- delimiters.

        Returns:
            Tuple of (frontmatter_dict, body_content).
            If no frontmatter found, returns ({}, full_content).
        """
        if not raw_content.startswith("---"):
            return {}, raw_content

        # Find closing ---
        end_idx = raw_content.find("---", 3)
        if end_idx == -1:
            return {}, raw_content

        frontmatter_str = raw_content[3:end_idx].strip()
        body = raw_content[end_idx + 3:].strip()

        # Parse simple key: value pairs
        metadata: dict = {}
        for line in frontmatter_str.split("\n"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if ":" not in line:
                continue
            key, _, value = line.partition(":")
            key = key.strip()
            value = value.strip()
            # Handle comma-separated values as lists
            if "," in value:
                metadata[key] = [v.strip() for v in value.split(",") if v.strip()]
            else:
                metadata[key] = value

        return metadata, body
