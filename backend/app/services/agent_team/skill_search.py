"""Skill Search — Sprint 218 (P3 Skills Completion).

Full-text search using tsvector GENERATED column on skill_definitions.
Grant management for per-agent skill access control.

Search: ts_rank() with plainto_tsquery('simple') — Vietnamese-safe,
no language-specific stemmer. Single SQL, no N+1.

Grants: workspace/project/personal tiers require explicit grant row.
Open tiers (global, builtin) are accessible without grants.

Port of MTClaw skills/search.go pattern.

References:
- ADR-070, Sprint 218 Track B/C
- skill_definitions.search_tsv GENERATED column (GIN index)
"""

from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy import and_, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.skill_agent_grant import SkillAgentGrant
from app.models.skill_definition import SkillDefinition

logger = logging.getLogger(__name__)

# Tiers that don't require explicit grants (open to all agents)
OPEN_TIERS = frozenset({"global", "builtin"})


class SkillSearch:
    """Full-text skill search with grant-based access control.

    Uses PostgreSQL tsvector for search ranking and skill_agent_grants
    table for per-agent access control on restricted tiers.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def search_skills(
        self,
        query: str,
        agent_id: UUID | None = None,
        project_id: UUID | None = None,
        limit: int = 10,
    ) -> list[dict]:
        """Search skills by text query using tsvector ranking.

        Single SQL query with ts_rank() — no N+1. Results include
        relevance score and grant status per skill.

        Args:
            query: Search text (e.g., "code review").
            agent_id: Optional agent ID for grant filtering.
            project_id: Optional project ID for scope filtering.
            limit: Max results (default 10, max 50).

        Returns:
            List of dicts with skill data + rank score + has_grant flag.
        """
        limit = min(max(limit, 1), 50)
        query = query.strip()
        if not query or len(query) > 200:
            return []

        # plainto_tsquery('simple', ...) — Vietnamese-safe, no stemmer
        tsquery = func.plainto_tsquery(text("'simple'"), query)
        rank = func.ts_rank(
            SkillDefinition.search_tsv,
            tsquery,
        ).label("rank")

        stmt = (
            select(SkillDefinition, rank)
            .where(
                and_(
                    SkillDefinition.is_active.is_(True),
                    SkillDefinition.search_tsv.op("@@")(tsquery),
                )
            )
            .order_by(rank.desc())
            .limit(limit)
        )

        # Optional project filter
        if project_id is not None:
            stmt = stmt.where(
                (SkillDefinition.project_id == project_id)
                | (SkillDefinition.project_id.is_(None))
            )

        result = await self.db.execute(stmt)
        rows = result.all()

        # Batch-check grants if agent_id provided
        granted_ids: set[UUID] = set()
        if agent_id is not None and rows:
            skill_ids = [row[0].id for row in rows]
            granted_ids = await self._get_granted_ids(agent_id, skill_ids)

        output = []
        for skill, score in rows:
            is_open = skill.tier in OPEN_TIERS
            has_grant = is_open or (skill.id in granted_ids)
            entry = skill.to_dict()
            entry["rank"] = float(score)
            entry["has_grant"] = has_grant
            output.append(entry)

        logger.debug(
            "search_skills: query=%r, results=%d, agent=%s",
            query, len(output), agent_id,
        )
        return output

    async def has_grant(
        self,
        agent_id: UUID,
        skill_id: UUID,
    ) -> bool:
        """Check if an agent has a grant for a specific skill.

        Open tiers (global/builtin) always return True.

        Args:
            agent_id: Agent definition ID.
            skill_id: Skill definition ID.

        Returns:
            True if agent can access the skill.
        """
        # Check if skill is in an open tier
        skill_result = await self.db.execute(
            select(SkillDefinition.tier).where(SkillDefinition.id == skill_id)
        )
        tier = skill_result.scalar_one_or_none()
        if tier is None:
            return False
        if tier in OPEN_TIERS:
            return True

        # Check for explicit grant
        grant_result = await self.db.execute(
            select(SkillAgentGrant.id).where(
                and_(
                    SkillAgentGrant.skill_definition_id == skill_id,
                    SkillAgentGrant.agent_definition_id == agent_id,
                )
            ).limit(1)
        )
        return grant_result.scalar_one_or_none() is not None

    async def grant_skill(
        self,
        skill_id: UUID,
        agent_id: UUID,
        granted_by: UUID | None = None,
    ) -> SkillAgentGrant | None:
        """Grant a skill to an agent. Idempotent (ON CONFLICT DO NOTHING).

        Args:
            skill_id: Skill definition ID.
            agent_id: Agent definition ID.
            granted_by: User ID who granted (optional).

        Returns:
            SkillAgentGrant if created, None if already exists.
        """
        # Check for existing grant (idempotent)
        existing = await self.db.execute(
            select(SkillAgentGrant).where(
                and_(
                    SkillAgentGrant.skill_definition_id == skill_id,
                    SkillAgentGrant.agent_definition_id == agent_id,
                )
            )
        )
        if existing.scalar_one_or_none() is not None:
            logger.debug(
                "Grant already exists: skill=%s, agent=%s", skill_id, agent_id,
            )
            return None

        grant = SkillAgentGrant(
            skill_definition_id=skill_id,
            agent_definition_id=agent_id,
            granted_by=granted_by,
        )
        self.db.add(grant)
        await self.db.flush()

        logger.info(
            "Skill granted: skill=%s, agent=%s, by=%s",
            skill_id, agent_id, granted_by,
        )
        return grant

    async def revoke_grant(
        self,
        skill_id: UUID,
        agent_id: UUID,
    ) -> bool:
        """Revoke a skill grant from an agent.

        Args:
            skill_id: Skill definition ID.
            agent_id: Agent definition ID.

        Returns:
            True if grant was revoked, False if not found.
        """
        result = await self.db.execute(
            select(SkillAgentGrant).where(
                and_(
                    SkillAgentGrant.skill_definition_id == skill_id,
                    SkillAgentGrant.agent_definition_id == agent_id,
                )
            )
        )
        grant = result.scalar_one_or_none()
        if grant is None:
            return False

        await self.db.delete(grant)
        await self.db.flush()

        logger.info(
            "Skill revoked: skill=%s, agent=%s", skill_id, agent_id,
        )
        return True

    async def list_grants(
        self,
        agent_id: UUID,
    ) -> list[SkillAgentGrant]:
        """List all skill grants for an agent.

        Args:
            agent_id: Agent definition ID.

        Returns:
            List of SkillAgentGrant objects with relationships loaded.
        """
        result = await self.db.execute(
            select(SkillAgentGrant).where(
                SkillAgentGrant.agent_definition_id == agent_id
            ).order_by(SkillAgentGrant.granted_at.desc())
        )
        return list(result.scalars().all())

    async def _get_granted_ids(
        self,
        agent_id: UUID,
        skill_ids: list[UUID],
    ) -> set[UUID]:
        """Batch-check which skill IDs the agent has grants for.

        Single query for all IDs — avoids N+1.
        """
        if not skill_ids:
            return set()

        result = await self.db.execute(
            select(SkillAgentGrant.skill_definition_id).where(
                and_(
                    SkillAgentGrant.agent_definition_id == agent_id,
                    SkillAgentGrant.skill_definition_id.in_(skill_ids),
                )
            )
        )
        return set(result.scalars().all())
