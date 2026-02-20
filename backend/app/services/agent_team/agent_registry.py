"""
=========================================================================
Agent Registry — Agent Definition CRUD + Session Scoping + SE4H Constraints
SDLC Orchestrator - Sprint 177 (Multi-Agent Core Services)

Version: 1.0.0
Date: February 2026
Status: ACTIVE - Sprint 177
Authority: CTO Approved (ADR-056 §12.5)
Reference: ADR-056-Multi-Agent-Team-Engine.md

Purpose:
- Agent definition CRUD with project-scoped uniqueness
- Session scoping enforcement (per-sender vs global, 2 P0 modes)
- SE4H behavioral constraint auto-enforcement
- Active agent lookup by role for @mention routing

Sources:
- OpenClaw: src/agents/agent-registry.ts (agent lookup, session scoping)
- ADR-056 Decision 1: Snapshot Precedence
- ADR-056 §12.5: SASE 12-Role Classification
- config.py: ROLE_MODEL_DEFAULTS, SE4H_CONSTRAINTS

Zero Mock Policy: Production-ready async SQLAlchemy 2.0 service
=========================================================================
"""

from __future__ import annotations

import logging
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_conversation import AgentConversation
from app.models.agent_definition import AgentDefinition
from app.schemas.agent_team import (
    AgentDefinitionCreate,
    AgentDefinitionUpdate,
    AgentDefinitionResponse,
    SDLCRole,
    SE4H_ROLES,
)
from app.services.agent_team.config import is_se4h_role, get_se4h_overrides

logger = logging.getLogger(__name__)


class AgentRegistryError(Exception):
    """Base exception for agent registry operations."""


class AgentNotFoundError(AgentRegistryError):
    """Agent definition not found."""


class AgentDuplicateError(AgentRegistryError):
    """Agent name already exists in this project."""


class AgentInactiveError(AgentRegistryError):
    """Agent definition is inactive."""


class AgentRegistry:
    """
    Agent definition CRUD service with session scoping and SE4H enforcement.

    Responsibilities:
    - Create/read/update agent definitions within project scope
    - Enforce unique agent names per project
    - Auto-apply SE4H behavioral constraints (ADR-056 §12.5.4)
    - Lookup agents by role for @mention routing
    - Resolve session scope for conversation creation

    Usage:
        registry = AgentRegistry(db)
        definition = await registry.create(payload)
        agent = await registry.get_by_name(project_id, "coder-alpha")
        agents = await registry.find_by_role(project_id, SDLCRole.CODER)
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, payload: AgentDefinitionCreate) -> AgentDefinition:
        """
        Create an agent definition with SE4H constraint enforcement.

        SE4H roles (ceo, cpo, cto) automatically receive:
        - max_delegation_depth=0 (cannot spawn sub-agents)
        - can_spawn_subagent=False
        - Restricted tool permissions (read-only)

        Args:
            payload: Agent definition creation payload.

        Returns:
            Created AgentDefinition ORM instance.

        Raises:
            AgentDuplicateError: If agent name already exists in project.
        """
        await self._check_name_uniqueness(payload.project_id, payload.agent_name)

        # Build kwargs from payload
        create_kwargs = {
            "id": uuid4(),
            "project_id": payload.project_id,
            "team_id": payload.team_id,
            "agent_name": payload.agent_name,
            "sdlc_role": payload.sdlc_role.value,
            "provider": payload.provider,
            "model": payload.model,
            "system_prompt": payload.system_prompt,
            "working_directory": payload.working_directory,
            "max_tokens": payload.max_tokens,
            "temperature": payload.temperature,
            "queue_mode": payload.queue_mode.value,
            "session_scope": payload.session_scope.value,
            "max_delegation_depth": payload.max_delegation_depth,
            "allowed_tools": payload.allowed_tools,
            "denied_tools": payload.denied_tools,
            "can_spawn_subagent": payload.can_spawn_subagent,
            "allowed_paths": payload.allowed_paths,
            "reflect_frequency": payload.reflect_frequency,
            "is_active": True,
            "config": payload.config,
        }

        # SE4H constraint enforcement (ADR-056 §12.5.4)
        if is_se4h_role(payload.sdlc_role):
            se4h_overrides = get_se4h_overrides()
            create_kwargs["max_delegation_depth"] = se4h_overrides["max_delegation_depth"]
            create_kwargs["can_spawn_subagent"] = se4h_overrides["can_spawn_subagent"]
            create_kwargs["allowed_tools"] = se4h_overrides["allowed_tools"]
            create_kwargs["denied_tools"] = se4h_overrides["denied_tools"]
            logger.info(
                "SE4H constraints applied for role=%s: max_delegation_depth=0, read-only tools",
                payload.sdlc_role.value,
            )

        definition = AgentDefinition(**create_kwargs)
        self.db.add(definition)
        await self.db.flush()

        logger.info(
            "Created agent definition: id=%s, name=%s, role=%s, project=%s",
            definition.id,
            definition.agent_name,
            definition.sdlc_role,
            definition.project_id,
        )
        return definition

    async def get(self, definition_id: UUID) -> AgentDefinition:
        """
        Get agent definition by ID.

        Raises:
            AgentNotFoundError: If definition not found.
        """
        result = await self.db.execute(
            select(AgentDefinition).where(AgentDefinition.id == definition_id)
        )
        definition = result.scalar_one_or_none()
        if not definition:
            raise AgentNotFoundError(f"Agent definition {definition_id} not found")
        return definition

    async def get_active(self, definition_id: UUID) -> AgentDefinition:
        """
        Get agent definition by ID, ensuring it is active.

        Raises:
            AgentNotFoundError: If definition not found.
            AgentInactiveError: If definition is inactive.
        """
        definition = await self.get(definition_id)
        if not definition.is_active:
            raise AgentInactiveError(
                f"Agent definition {definition_id} ({definition.agent_name}) is inactive"
            )
        return definition

    async def get_by_name(
        self, project_id: UUID, agent_name: str
    ) -> AgentDefinition | None:
        """
        Lookup agent definition by name within project scope.

        Returns None if not found (does not raise).
        """
        result = await self.db.execute(
            select(AgentDefinition).where(
                and_(
                    AgentDefinition.project_id == project_id,
                    AgentDefinition.agent_name == agent_name,
                    AgentDefinition.is_active == True,  # noqa: E712
                )
            )
        )
        return result.scalar_one_or_none()

    async def find_by_role(
        self, project_id: UUID, role: SDLCRole, active_only: bool = True
    ) -> list[AgentDefinition]:
        """
        Find all agent definitions with a given SDLC role in a project.

        Used by @mention routing to resolve role-based mentions
        (e.g., @coder routes to all agents with sdlc_role=coder).
        """
        conditions = [
            AgentDefinition.project_id == project_id,
            AgentDefinition.sdlc_role == role.value,
        ]
        if active_only:
            conditions.append(AgentDefinition.is_active == True)  # noqa: E712

        result = await self.db.execute(
            select(AgentDefinition).where(and_(*conditions))
        )
        return list(result.scalars().all())

    async def list_definitions(
        self,
        project_id: UUID,
        sdlc_role: str | None = None,
        is_active: bool | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[AgentDefinition], int]:
        """
        List agent definitions with filters and pagination.

        Returns:
            (definitions, total_count)
        """
        conditions = [AgentDefinition.project_id == project_id]
        if sdlc_role:
            conditions.append(AgentDefinition.sdlc_role == sdlc_role)
        if is_active is not None:
            conditions.append(AgentDefinition.is_active == is_active)

        # Count
        count_query = (
            select(func.count())
            .select_from(AgentDefinition)
            .where(and_(*conditions))
        )
        total = (await self.db.execute(count_query)).scalar() or 0

        # Fetch page
        query = (
            select(AgentDefinition)
            .where(and_(*conditions))
            .order_by(AgentDefinition.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self.db.execute(query)
        definitions = list(result.scalars().all())

        return definitions, total

    async def update(
        self, definition_id: UUID, payload: AgentDefinitionUpdate
    ) -> AgentDefinition:
        """
        Partially update an agent definition.

        NOTE: Changes do NOT affect running conversations (Snapshot Precedence).
        SE4H constraints are re-enforced if sdlc_role is changed to an SE4H role.

        Raises:
            AgentNotFoundError: If definition not found.
            AgentDuplicateError: If new name conflicts with existing.
        """
        definition = await self.get(definition_id)

        update_data = payload.model_dump(exclude_unset=True)

        # Check name uniqueness if name is being changed
        new_name = update_data.get("agent_name")
        if new_name and new_name != definition.agent_name:
            await self._check_name_uniqueness(definition.project_id, new_name)

        # Determine effective role after update
        new_role = update_data.get("sdlc_role")
        effective_role = new_role if new_role else SDLCRole(definition.sdlc_role)

        # Apply fields
        for field_name, value in update_data.items():
            if field_name in ("sdlc_role", "queue_mode", "session_scope") and value is not None:
                setattr(definition, field_name, value.value)
            else:
                setattr(definition, field_name, value)

        # Re-enforce SE4H constraints if role changed to SE4H
        if isinstance(effective_role, SDLCRole) and is_se4h_role(effective_role):
            se4h_overrides = get_se4h_overrides()
            definition.max_delegation_depth = se4h_overrides["max_delegation_depth"]
            definition.can_spawn_subagent = se4h_overrides["can_spawn_subagent"]
            definition.allowed_tools = se4h_overrides["allowed_tools"]
            definition.denied_tools = se4h_overrides["denied_tools"]
            logger.info(
                "SE4H constraints re-enforced after update: id=%s, role=%s",
                definition_id,
                effective_role.value if isinstance(effective_role, SDLCRole) else effective_role,
            )

        await self.db.flush()
        logger.info("Updated agent definition: id=%s", definition_id)
        return definition

    async def has_active_conversations(self, definition_id: UUID) -> int:
        """
        Count active conversations for an agent definition.

        Returns:
            Number of conversations with status='active'.
        """
        result = await self.db.execute(
            select(func.count())
            .select_from(AgentConversation)
            .where(
                and_(
                    AgentConversation.agent_definition_id == definition_id,
                    AgentConversation.status == "active",
                )
            )
        )
        return result.scalar() or 0

    async def deactivate(self, definition_id: UUID) -> AgentDefinition:
        """
        Soft-deactivate an agent definition.

        Raises:
            AgentNotFoundError: If definition not found.
        """
        definition = await self.get(definition_id)
        definition.is_active = False
        await self.db.flush()
        logger.info("Deactivated agent definition: id=%s", definition_id)
        return definition

    async def resolve_session_key(
        self, definition: AgentDefinition, sender_id: str
    ) -> str:
        """
        Resolve session key for conversation lookup based on session_scope.

        Session scoping (2 P0 modes per ADR-056):
        - per-sender: Each user gets isolated session → key = {agent_id}:{sender_id}
        - global: Single session across all senders → key = {agent_id}:global

        Returns:
            Session key string for conversation deduplication.
        """
        if definition.session_scope == "global":
            return f"{definition.id}:global"
        return f"{definition.id}:{sender_id}"

    async def _check_name_uniqueness(
        self, project_id: UUID, agent_name: str
    ) -> None:
        """
        Check that agent name is unique within project scope.

        Raises:
            AgentDuplicateError: If name already exists.
        """
        existing = await self.db.execute(
            select(AgentDefinition).where(
                and_(
                    AgentDefinition.project_id == project_id,
                    AgentDefinition.agent_name == agent_name,
                )
            )
        )
        if existing.scalar_one_or_none():
            raise AgentDuplicateError(
                f"Agent '{agent_name}' already exists in project {project_id}"
            )
