"""
=========================================================================
Mention Parser — @mention routing for Multi-Agent conversations
SDLC Orchestrator - Sprint 177 (Multi-Agent Core Services)

Version: 1.0.0
Date: February 2026
Status: ACTIVE - Sprint 177
Authority: CTO Approved (ADR-056)
Reference: ADR-056-Multi-Agent-Team-Engine.md

Purpose:
- Parse @agent mentions from message content (TinyClaw pattern)
- Resolve mentions to agent definitions within project scope
- Support role-based mentions (@coder, @reviewer) and name-based (@coder-alpha)
- Return routed targets for message delivery

Sources:
- TinyClaw: src/tinyclaw/mention-parser.ts (@mention routing)
- ADR-056 Section 10.2: @Mention Routing
- OpenClaw: src/agents/agent-router.ts (agent resolution)

Zero Mock Policy: Production-ready async service
=========================================================================
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_definition import AgentDefinition
from app.schemas.agent_team import SDLCRole

logger = logging.getLogger(__name__)

# @mention regex: matches @word patterns, excluding email-like patterns
_MENTION_PATTERN = re.compile(
    r"(?<!\S)@([a-zA-Z][a-zA-Z0-9_-]{0,49})(?!\S)",
)

# Valid SDLC role values for role-based mention resolution
_ROLE_VALUES: frozenset[str] = frozenset(r.value for r in SDLCRole)


@dataclass(frozen=True)
class ParsedMention:
    """A single parsed @mention from message content."""

    raw: str
    name: str
    is_role_mention: bool


@dataclass
class MentionRouteResult:
    """Result of mention routing — resolved agent targets."""

    mentions: list[ParsedMention] = field(default_factory=list)
    resolved_agents: list[AgentDefinition] = field(default_factory=list)
    unresolved: list[str] = field(default_factory=list)

    @property
    def has_mentions(self) -> bool:
        return len(self.mentions) > 0

    @property
    def mention_names(self) -> list[str]:
        return [m.name for m in self.mentions]


class MentionParser:
    """
    Parses @mentions from message content and resolves them to agent definitions.

    Two resolution modes:
    1. **Role-based**: @coder, @reviewer → all active agents with that SDLC role
    2. **Name-based**: @coder-alpha → specific agent by name

    Role-based mentions are checked first (exact match against SDLCRole enum values).
    If no role match, falls back to name-based lookup.

    Usage:
        parser = MentionParser(db)
        result = await parser.parse_and_route(project_id, "Hey @coder please review this")
        for agent in result.resolved_agents:
            # route message to agent
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def extract_mentions(content: str) -> list[ParsedMention]:
        """
        Extract @mentions from message content.

        Returns list of ParsedMention with is_role_mention flag set
        based on whether the mention matches an SDLCRole value.
        """
        mentions: list[ParsedMention] = []
        seen: set[str] = set()

        for match in _MENTION_PATTERN.finditer(content):
            name = match.group(1).lower()
            if name in seen:
                continue
            seen.add(name)

            is_role = name in _ROLE_VALUES
            mentions.append(
                ParsedMention(raw=match.group(0), name=name, is_role_mention=is_role)
            )

        return mentions

    async def resolve_mentions(
        self, project_id: UUID, mentions: list[ParsedMention]
    ) -> MentionRouteResult:
        """
        Resolve parsed mentions to agent definitions within project scope.

        Role mentions resolve to all active agents with that role.
        Name mentions resolve to the specific named agent.
        """
        result = MentionRouteResult(mentions=mentions)
        resolved_ids: set[UUID] = set()

        for mention in mentions:
            if mention.is_role_mention:
                agents = await self._resolve_by_role(project_id, mention.name)
            else:
                agents = await self._resolve_by_name(project_id, mention.name)

            if agents:
                for agent in agents:
                    if agent.id not in resolved_ids:
                        result.resolved_agents.append(agent)
                        resolved_ids.add(agent.id)
            else:
                result.unresolved.append(mention.name)
                logger.warning(
                    "Unresolved mention @%s in project %s",
                    mention.name,
                    project_id,
                )

        return result

    async def parse_and_route(
        self, project_id: UUID, content: str
    ) -> MentionRouteResult:
        """
        Parse message content for @mentions and resolve to agent targets.

        Convenience method combining extract_mentions + resolve_mentions.
        """
        mentions = self.extract_mentions(content)
        if not mentions:
            return MentionRouteResult()

        return await self.resolve_mentions(project_id, mentions)

    async def _resolve_by_role(
        self, project_id: UUID, role_value: str
    ) -> list[AgentDefinition]:
        """Find all active agents with matching SDLC role in project."""
        result = await self.db.execute(
            select(AgentDefinition).where(
                and_(
                    AgentDefinition.project_id == project_id,
                    AgentDefinition.sdlc_role == role_value,
                    AgentDefinition.is_active == True,  # noqa: E712
                )
            )
        )
        agents = list(result.scalars().all())
        if agents:
            logger.debug(
                "Role mention @%s resolved to %d agent(s) in project %s",
                role_value,
                len(agents),
                project_id,
            )
        return agents

    async def _resolve_by_name(
        self, project_id: UUID, agent_name: str
    ) -> list[AgentDefinition]:
        """Find agent by exact name in project."""
        result = await self.db.execute(
            select(AgentDefinition).where(
                and_(
                    AgentDefinition.project_id == project_id,
                    AgentDefinition.agent_name == agent_name,
                    AgentDefinition.is_active == True,  # noqa: E712
                )
            )
        )
        agent = result.scalar_one_or_none()
        return [agent] if agent else []
