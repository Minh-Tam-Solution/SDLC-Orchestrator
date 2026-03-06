"""
Team Presets — Sprint 194 (GAP-02), Sprint 216 (delegation persistence).

5 named team configurations representing common SDLC team compositions.
Each preset maps to a subset of the 12 SDLC roles and their delegation chains.
Presets are code-defined constants (no DB table needed).

Sprint 216 addition (ADR-069, FR-051):
- apply_preset() now persists delegation_chain to delegation_links table
- Sets teams.lead_agent_definition_id to first role in the chain
- Deactivates existing links NOT in the new preset

Usage:
    from app.services.agent_team.team_presets import TEAM_PRESETS, get_preset

    preset = get_preset("startup-2")
    for role in preset.roles:
        # seed agent definition per role ...
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import and_, select, update

from app.models.agent_definition import AgentDefinition
from app.models.delegation_link import DelegationLink
from app.models.team import Team
from app.services.agent_team.agent_seed_service import AgentSeedService
from app.services.agent_team.delegation_service import DelegationService

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TeamPresetConfig:
    """Immutable team preset configuration."""

    name: str
    description: str
    roles: tuple[str, ...]
    delegation_chain: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    default_queue_mode: str = "queue"

    def to_dict(self) -> dict:
        """Serialize to JSON-compatible dict."""
        return {
            "name": self.name,
            "description": self.description,
            "roles": list(self.roles),
            "delegation_chain": [list(pair) for pair in self.delegation_chain],
            "default_queue_mode": self.default_queue_mode,
            "role_count": len(self.roles),
        }


# =========================================================================
# 5 Named Team Presets (Sprint 194 GAP-02)
# =========================================================================

TEAM_PRESETS: dict[str, TeamPresetConfig] = {
    "solo-dev": TeamPresetConfig(
        name="solo-dev",
        description="Single developer working alone",
        roles=("coder",),
        delegation_chain=(),
    ),
    "startup-2": TeamPresetConfig(
        name="startup-2",
        description="Small team with code review",
        roles=("coder", "reviewer"),
        delegation_chain=(("coder", "reviewer"),),
    ),
    "enterprise-3": TeamPresetConfig(
        name="enterprise-3",
        description="Standard enterprise dev team",
        roles=("architect", "coder", "reviewer"),
        delegation_chain=(
            ("architect", "coder"),
            ("coder", "reviewer"),
        ),
    ),
    "review-pair": TeamPresetConfig(
        name="review-pair",
        description="Quality-focused review pair",
        roles=("reviewer", "tester"),
        delegation_chain=(("reviewer", "tester"),),
    ),
    "full-sprint": TeamPresetConfig(
        name="full-sprint",
        description="Full SDLC sprint team",
        roles=("pm", "architect", "coder", "reviewer", "tester", "devops"),
        delegation_chain=(
            ("pm", "architect"),
            ("pm", "coder"),
            ("architect", "coder"),
            ("coder", "reviewer"),
            ("coder", "tester"),
            ("devops", "coder"),
        ),
        default_queue_mode="queue",
    ),
}


def list_presets() -> list[dict]:
    """Return all team presets as serializable dicts."""
    return [preset.to_dict() for preset in TEAM_PRESETS.values()]


def get_preset(name: str) -> TeamPresetConfig | None:
    """Retrieve a single preset by name.

    Args:
        name: Preset identifier (e.g. "solo-dev", "startup-2").

    Returns:
        TeamPresetConfig if found, None otherwise.
    """
    return TEAM_PRESETS.get(name)


class TeamPresetService:
    """Applies a named team preset to a project by seeding the relevant roles."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def apply_preset(
        self,
        preset_name: str,
        project_id: UUID,
        *,
        team_id: UUID | None = None,
    ) -> dict:
        """Seed agent definitions for a preset's roles and persist delegation chain.

        Sprint 216 (ADR-069, FR-051):
        1. Seeds agent definitions for preset roles.
        2. Creates delegation_links for each pair in the delegation_chain.
        3. Sets teams.lead_agent_definition_id to the first role in the chain.
        4. Deactivates existing links NOT in the new preset.

        Args:
            preset_name: One of the 5 preset names.
            project_id: Target project UUID.
            team_id: Optional team binding.

        Returns:
            Dict with preset name, roles seeded, delegation links created, and count.

        Raises:
            ValueError: If preset_name is not a valid preset.
        """
        preset = get_preset(preset_name)
        if preset is None:
            raise ValueError(
                f"Unknown preset '{preset_name}'. "
                f"Available: {', '.join(TEAM_PRESETS.keys())}"
            )

        seed_svc = AgentSeedService(self.db)
        created = await seed_svc.seed_project_agents(
            project_id, team_id=team_id
        )

        # Filter to only the roles in the preset
        preset_roles = set(preset.roles)
        preset_agents = [d for d in created if d.sdlc_role in preset_roles]

        # Build role -> agent_id lookup
        role_to_agent: dict[str, AgentDefinition] = {}
        for agent_def in preset_agents:
            role_to_agent[agent_def.sdlc_role] = agent_def

        # Persist delegation chain to delegation_links (Sprint 216)
        delegation_svc = DelegationService(self.db)
        links_created = 0
        preset_pairs: set[tuple[UUID, UUID]] = set()

        for source_role, target_role in preset.delegation_chain:
            source = role_to_agent.get(source_role)
            target = role_to_agent.get(target_role)
            if source is None or target is None:
                logger.warning(
                    "Delegation chain pair skipped (missing agent): %s -> %s",
                    source_role, target_role,
                )
                continue

            preset_pairs.add((source.id, target.id))
            try:
                await delegation_svc.create_link(source.id, target.id)
                links_created += 1
            except Exception:
                # DuplicateLinkError is acceptable — link already exists
                logger.debug(
                    "Delegation link already exists: %s -> %s",
                    source_role, target_role,
                )

        # Deactivate links NOT in the preset (FR-051-09)
        if preset_agents and team_id is not None:
            agent_ids = [a.id for a in preset_agents]
            existing_links_result = await self.db.execute(
                select(DelegationLink).where(
                    and_(
                        DelegationLink.source_agent_id.in_(agent_ids),
                        DelegationLink.is_active.is_(True),
                    )
                )
            )
            for link in existing_links_result.scalars().all():
                pair = (link.source_agent_id, link.target_agent_id)
                if pair not in preset_pairs:
                    link.is_active = False
                    logger.info(
                        "Deactivated non-preset link: %s -> %s",
                        link.source_agent_id, link.target_agent_id,
                    )

        # Set lead_agent_definition_id on team (Sprint 216 Track B)
        lead_agent_id = None
        if team_id is not None and preset.roles:
            first_role = preset.roles[0]
            lead = role_to_agent.get(first_role)
            if lead is not None:
                lead_agent_id = lead.id
                await self.db.execute(
                    update(Team)
                    .where(Team.id == team_id)
                    .values(lead_agent_definition_id=lead.id)
                )
                logger.info(
                    "Set team %s lead to %s (%s)",
                    team_id, lead.agent_name, first_role,
                )

        await self.db.flush()

        logger.info(
            "Applied preset '%s' to project %s: %d/%d roles seeded, %d delegation links",
            preset_name,
            project_id,
            len(preset_agents),
            len(preset.roles),
            links_created,
        )

        return {
            "preset": preset_name,
            "project_id": str(project_id),
            "roles_seeded": [d.sdlc_role for d in preset_agents],
            "roles_expected": list(preset.roles),
            "delegation_chain": [list(pair) for pair in preset.delegation_chain],
            "links_created": links_created,
            "lead_agent_id": str(lead_agent_id) if lead_agent_id else None,
            "count": len(preset_agents),
        }
