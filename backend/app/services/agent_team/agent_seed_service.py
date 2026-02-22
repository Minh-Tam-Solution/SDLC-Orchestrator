"""
Agent Seed Service — Sprint 194 (GAP-01).

Seeds 12 default AgentDefinition records for a project, one per SDLC role.
Uses ROLE_MODEL_DEFAULTS from config.py for provider/model assignments.

Usage:
    svc = AgentSeedService(db)
    created = await svc.seed_project_agents(project_id)
"""

import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_definition import AgentDefinition
from app.services.agent_team.config import ROLE_MODEL_DEFAULTS

logger = logging.getLogger(__name__)

# System prompt templates per SDLC role (concise, role-focused).
_ROLE_PROMPTS: dict[str, str] = {
    "researcher": (
        "You are an SDLC Researcher agent. Gather requirements, analyse market data, "
        "and produce evidence-backed findings. Output structured summaries."
    ),
    "pm": (
        "You are an SDLC Project Manager agent. Decompose user stories into tasks, "
        "track sprint progress, and ensure traceability from requirements to delivery."
    ),
    "pjm": (
        "You are an SDLC Program Manager agent. Coordinate cross-team dependencies, "
        "manage roadmap milestones, and report escalation risks."
    ),
    "architect": (
        "You are an SDLC Architect agent. Design system architecture, review ADRs, "
        "validate non-functional requirements, and enforce design principles."
    ),
    "coder": (
        "You are an SDLC Coder agent. Write production-ready code following Zero Mock "
        "Policy. Include type hints, error handling, and docstrings. Run linting before output."
    ),
    "reviewer": (
        "You are an SDLC Code Reviewer agent. Review code for correctness, security, "
        "performance, and SDLC compliance. Provide actionable feedback with line references."
    ),
    "tester": (
        "You are an SDLC Tester agent. Write unit, integration, and E2E tests. "
        "Target 95%+ coverage. Follow Arrange-Act-Assert pattern."
    ),
    "devops": (
        "You are an SDLC DevOps agent. Manage CI/CD pipelines, Docker configurations, "
        "infrastructure-as-code, and deployment procedures."
    ),
    "ceo": (
        "You are an SDLC CEO Coach. Provide strategic guidance on product-market fit, "
        "business priorities, and investment decisions. Read-only analysis."
    ),
    "cpo": (
        "You are an SDLC CPO Coach. Advise on product strategy, user experience, "
        "feature prioritisation, and customer feedback analysis. Read-only analysis."
    ),
    "cto": (
        "You are an SDLC CTO Coach. Review architecture decisions, technology choices, "
        "security posture, and engineering quality. Read-only analysis."
    ),
    "assistant": (
        "You are an SDLC Router assistant. Help users find the right agent or workflow "
        "for their task. Provide navigation and quick answers."
    ),
}

# Default max_tokens per role category.
_ROLE_MAX_TOKENS: dict[str, int] = {
    "researcher": 8192,
    "pm": 4096,
    "pjm": 4096,
    "architect": 8192,
    "coder": 16384,
    "reviewer": 8192,
    "tester": 8192,
    "devops": 4096,
    "ceo": 4096,
    "cpo": 4096,
    "cto": 4096,
    "assistant": 2048,
}


class AgentSeedService:
    """Seeds default agent definitions for a project."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def seed_project_agents(
        self,
        project_id: UUID,
        *,
        team_id: UUID | None = None,
        skip_existing: bool = True,
    ) -> list[AgentDefinition]:
        """
        Create 12 default AgentDefinition records for the given project.

        Args:
            project_id: Target project UUID.
            team_id: Optional team binding.
            skip_existing: If True, skip roles that already have a definition.

        Returns:
            List of newly created AgentDefinition records.
        """
        existing_roles: set[str] = set()
        if skip_existing:
            result = await self.db.execute(
                select(AgentDefinition.sdlc_role).where(
                    AgentDefinition.project_id == project_id,
                    AgentDefinition.is_active.is_(True),
                )
            )
            existing_roles = {row[0] for row in result.all()}

        created: list[AgentDefinition] = []

        for role, model_cfg in ROLE_MODEL_DEFAULTS.items():
            if role in existing_roles:
                logger.debug("Skipping role %s — already exists for project %s", role, project_id)
                continue

            definition = AgentDefinition(
                project_id=project_id,
                team_id=team_id,
                agent_name=role,
                sdlc_role=role,
                provider=model_cfg["provider"],
                model=model_cfg["model"],
                system_prompt=_ROLE_PROMPTS.get(role, ""),
                max_tokens=_ROLE_MAX_TOKENS.get(role, 4096),
                temperature=0.3 if role in ("coder", "reviewer", "tester") else 0.7,
                queue_mode="queue",
                session_scope="per-sender",
                max_delegation_depth=0 if role in ("ceo", "cpo", "cto") else 1,
                can_spawn_subagent=role not in ("ceo", "cpo", "cto", "assistant"),
                allowed_tools=["read_file", "search", "analyze"] if role in ("ceo", "cpo", "cto") else ["*"],
                denied_tools=(
                    ["write_file", "execute_command", "spawn_agent", "send_message", "approve_gate"]
                    if role in ("ceo", "cpo", "cto")
                    else []
                ),
                allowed_paths=[],
                is_active=True,
                config={},
            )
            self.db.add(definition)
            created.append(definition)

        if created:
            await self.db.flush()
            logger.info(
                "Seeded %d agent definitions for project %s (roles: %s)",
                len(created),
                project_id,
                ", ".join(d.sdlc_role for d in created),
            )

        return created
