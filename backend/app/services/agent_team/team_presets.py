"""
Team Presets — Sprint 194 (GAP-02).

5 named team configurations representing common SDLC team compositions.
Each preset maps to a subset of the 12 SDLC roles and their delegation chains.
Presets are code-defined constants (no DB table needed).

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

from app.services.agent_team.agent_seed_service import AgentSeedService

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
        """Seed agent definitions for a preset's roles.

        Args:
            preset_name: One of the 5 preset names.
            project_id: Target project UUID.
            team_id: Optional team binding.

        Returns:
            Dict with preset name, roles seeded, and count.

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

        logger.info(
            "Applied preset '%s' to project %s: %d/%d roles seeded",
            preset_name,
            project_id,
            len(preset_agents),
            len(preset.roles),
        )

        return {
            "preset": preset_name,
            "project_id": str(project_id),
            "roles_seeded": [d.sdlc_role for d in preset_agents],
            "roles_expected": list(preset.roles),
            "delegation_chain": [list(pair) for pair in preset.delegation_chain],
            "count": len(preset_agents),
        }
