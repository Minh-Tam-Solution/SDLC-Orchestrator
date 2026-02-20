"""
=========================================================================
Unit Tests - Agent Registry (Sprint 177)
SDLC Orchestrator - Multi-Agent Team Engine

Version: 1.0.0
Date: February 2026
Status: ACTIVE - Sprint 177
Authority: CTO Approved (ADR-056 §12.5)

Purpose:
- Test agent definition CRUD with project-scoped uniqueness
- Test SE4H behavioral constraint auto-enforcement
- Test session scoping resolution (per-sender vs global)
- Test list with pagination and filters
- Test partial update with SE4H re-enforcement

Zero Mock Policy: Mocked AsyncSession for unit isolation
=========================================================================
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.schemas.agent_team import (
    AgentDefinitionCreate,
    AgentDefinitionUpdate,
    SDLCRole,
    QueueMode,
    SessionScope,
)
from app.services.agent_team.agent_registry import (
    AgentRegistry,
    AgentNotFoundError,
    AgentDuplicateError,
    AgentInactiveError,
)


# =========================================================================
# Fixtures
# =========================================================================


@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    return db


@pytest.fixture
def registry(mock_db):
    return AgentRegistry(mock_db)


def _make_definition(**overrides):
    """Create a mock AgentDefinition ORM object."""
    defn = MagicMock()
    defn.id = overrides.get("id", uuid4())
    defn.project_id = overrides.get("project_id", uuid4())
    defn.team_id = overrides.get("team_id", None)
    defn.agent_name = overrides.get("agent_name", "coder-alpha")
    defn.sdlc_role = overrides.get("sdlc_role", "coder")
    defn.provider = overrides.get("provider", "ollama")
    defn.model = overrides.get("model", "qwen3-coder:30b")
    defn.is_active = overrides.get("is_active", True)
    defn.max_delegation_depth = overrides.get("max_delegation_depth", 2)
    defn.can_spawn_subagent = overrides.get("can_spawn_subagent", False)
    defn.allowed_tools = overrides.get("allowed_tools", ["*"])
    defn.denied_tools = overrides.get("denied_tools", [])
    defn.session_scope = overrides.get("session_scope", "per-sender")
    defn.created_at = overrides.get("created_at", None)
    return defn


def _make_create_payload(**overrides) -> AgentDefinitionCreate:
    """Create a valid AgentDefinitionCreate payload."""
    return AgentDefinitionCreate(
        project_id=overrides.get("project_id", uuid4()),
        agent_name=overrides.get("agent_name", "coder-alpha"),
        sdlc_role=overrides.get("sdlc_role", SDLCRole.CODER),
        provider=overrides.get("provider", "ollama"),
        model=overrides.get("model", "qwen3-coder:30b"),
        **{k: v for k, v in overrides.items() if k not in (
            "project_id", "agent_name", "sdlc_role", "provider", "model"
        )},
    )


def _setup_db_return(mock_db, obj):
    """Configure mock_db.execute to return obj."""
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = obj
    mock_db.execute.return_value = mock_result


# =========================================================================
# Create Tests
# =========================================================================


class TestCreate:
    """Tests for AgentRegistry.create."""

    @pytest.mark.asyncio
    async def test_create_agent_definition(self, registry, mock_db):
        """Happy path: creates definition and adds to DB."""
        # No duplicate exists
        _setup_db_return(mock_db, None)

        payload = _make_create_payload()
        result = await registry.create(payload)

        mock_db.add.assert_called_once()
        added = mock_db.add.call_args[0][0]
        assert added.agent_name == "coder-alpha"
        assert added.sdlc_role == "coder"
        assert added.is_active is True

    @pytest.mark.asyncio
    async def test_create_se4h_role_enforces_constraints(self, registry, mock_db):
        """SE4H roles (ceo/cpo/cto) get max_delegation_depth=0 and restricted tools."""
        _setup_db_return(mock_db, None)

        payload = _make_create_payload(
            agent_name="cto-coach",
            sdlc_role=SDLCRole.CTO,
            provider="anthropic",
            model="claude-opus-4-6",
            max_delegation_depth=5,  # Should be overridden to 0
            can_spawn_subagent=True,  # Should be overridden to False
        )
        result = await registry.create(payload)

        added = mock_db.add.call_args[0][0]
        assert added.max_delegation_depth == 0
        assert added.can_spawn_subagent is False

    @pytest.mark.asyncio
    async def test_create_duplicate_name_raises(self, registry, mock_db):
        """Duplicate agent name in same project raises AgentDuplicateError."""
        existing = _make_definition()
        _setup_db_return(mock_db, existing)

        payload = _make_create_payload()
        with pytest.raises(AgentDuplicateError):
            await registry.create(payload)


# =========================================================================
# Get Tests
# =========================================================================


class TestGet:
    """Tests for agent definition lookup."""

    @pytest.mark.asyncio
    async def test_get_returns_definition(self, registry, mock_db):
        defn = _make_definition()
        _setup_db_return(mock_db, defn)

        result = await registry.get(defn.id)
        assert result.id == defn.id

    @pytest.mark.asyncio
    async def test_get_not_found_raises(self, registry, mock_db):
        _setup_db_return(mock_db, None)

        with pytest.raises(AgentNotFoundError):
            await registry.get(uuid4())

    @pytest.mark.asyncio
    async def test_get_active_inactive_raises(self, registry, mock_db):
        defn = _make_definition(is_active=False)
        _setup_db_return(mock_db, defn)

        with pytest.raises(AgentInactiveError):
            await registry.get_active(defn.id)

    @pytest.mark.asyncio
    async def test_get_by_name(self, registry, mock_db):
        defn = _make_definition(agent_name="reviewer-beta")
        _setup_db_return(mock_db, defn)

        result = await registry.get_by_name(defn.project_id, "reviewer-beta")
        assert result is not None
        assert result.agent_name == "reviewer-beta"

    @pytest.mark.asyncio
    async def test_get_by_name_not_found(self, registry, mock_db):
        _setup_db_return(mock_db, None)

        result = await registry.get_by_name(uuid4(), "nonexistent")
        assert result is None


# =========================================================================
# Find by Role Tests
# =========================================================================


class TestFindByRole:
    """Tests for role-based lookup (used by @mention routing)."""

    @pytest.mark.asyncio
    async def test_find_by_role(self, registry, mock_db):
        agents = [_make_definition(sdlc_role="coder") for _ in range(3)]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = agents
        mock_db.execute.return_value = mock_result

        result = await registry.find_by_role(uuid4(), SDLCRole.CODER)
        assert len(result) == 3


# =========================================================================
# List Tests
# =========================================================================


class TestListDefinitions:
    """Tests for paginated listing."""

    @pytest.mark.asyncio
    async def test_list_definitions_pagination(self, registry, mock_db):
        """Returns definitions with total count."""
        definitions = [_make_definition() for _ in range(5)]

        # Mock count query
        count_result = MagicMock()
        count_result.scalar.return_value = 15

        # Mock fetch query
        fetch_result = MagicMock()
        fetch_result.scalars.return_value.all.return_value = definitions

        mock_db.execute.side_effect = [count_result, fetch_result]

        defs, total = await registry.list_definitions(uuid4(), page=1, page_size=5)
        assert len(defs) == 5
        assert total == 15

    @pytest.mark.asyncio
    async def test_list_definitions_with_role_filter(self, registry, mock_db):
        """Filtering by role works."""
        definitions = [_make_definition(sdlc_role="coder")]

        count_result = MagicMock()
        count_result.scalar.return_value = 1

        fetch_result = MagicMock()
        fetch_result.scalars.return_value.all.return_value = definitions

        mock_db.execute.side_effect = [count_result, fetch_result]

        defs, total = await registry.list_definitions(uuid4(), sdlc_role="coder")
        assert total == 1


# =========================================================================
# Update Tests
# =========================================================================


class TestUpdate:
    """Tests for partial update."""

    @pytest.mark.asyncio
    async def test_update_partial(self, registry, mock_db):
        """Only updates provided fields."""
        defn = _make_definition(agent_name="old-name")
        _setup_db_return(mock_db, defn)

        payload = AgentDefinitionUpdate(agent_name="new-name")

        # For name uniqueness check (no conflict)
        mock_db.execute.side_effect = [
            # First call: get definition
            MagicMock(scalar_one_or_none=MagicMock(return_value=defn)),
            # Second call: name uniqueness check
            MagicMock(scalar_one_or_none=MagicMock(return_value=None)),
        ]

        result = await registry.update(defn.id, payload)
        assert defn.agent_name == "new-name"

    @pytest.mark.asyncio
    async def test_update_name_uniqueness_check(self, registry, mock_db):
        """Changing name to an existing name raises AgentDuplicateError."""
        defn = _make_definition(agent_name="old-name")
        existing = _make_definition(agent_name="taken-name")

        mock_db.execute.side_effect = [
            MagicMock(scalar_one_or_none=MagicMock(return_value=defn)),
            MagicMock(scalar_one_or_none=MagicMock(return_value=existing)),
        ]

        payload = AgentDefinitionUpdate(agent_name="taken-name")
        with pytest.raises(AgentDuplicateError):
            await registry.update(defn.id, payload)

    @pytest.mark.asyncio
    async def test_update_to_se4h_role_enforces(self, registry, mock_db):
        """Changing role to SE4H re-applies behavioral constraints."""
        defn = _make_definition(
            sdlc_role="coder",
            max_delegation_depth=5,
            can_spawn_subagent=True,
        )

        mock_db.execute.side_effect = [
            MagicMock(scalar_one_or_none=MagicMock(return_value=defn)),
        ]

        payload = AgentDefinitionUpdate(sdlc_role=SDLCRole.CEO)
        result = await registry.update(defn.id, payload)

        assert defn.max_delegation_depth == 0
        assert defn.can_spawn_subagent is False


# =========================================================================
# Deactivate Tests
# =========================================================================


class TestDeactivate:
    """Tests for soft-deactivation."""

    @pytest.mark.asyncio
    async def test_deactivate(self, registry, mock_db):
        defn = _make_definition(is_active=True)
        _setup_db_return(mock_db, defn)

        result = await registry.deactivate(defn.id)
        assert defn.is_active is False


# =========================================================================
# Session Key Tests
# =========================================================================


class TestResolveSessionKey:
    """Tests for session key resolution."""

    @pytest.mark.asyncio
    async def test_per_sender_key(self, registry):
        defn = _make_definition(session_scope="per-sender")
        key = await registry.resolve_session_key(defn, "user-1")
        assert str(defn.id) in key
        assert "user-1" in key

    @pytest.mark.asyncio
    async def test_global_key(self, registry):
        defn = _make_definition(session_scope="global")
        key = await registry.resolve_session_key(defn, "user-1")
        assert str(defn.id) in key
        assert "global" in key
        assert "user-1" not in key
