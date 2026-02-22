"""
Unit Tests for AgentSeedService — Sprint 194 (GAP-01).

Tests:
- Seeds 12 agent definitions for a project
- Skips existing roles when skip_existing=True
- Applies correct model/provider from ROLE_MODEL_DEFAULTS
- SE4H roles get restricted permissions
- Coder/reviewer/tester get low temperature
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.services.agent_team.agent_seed_service import AgentSeedService
from app.services.agent_team.config import ROLE_MODEL_DEFAULTS


@pytest.fixture
def db():
    """Create a mock async DB session."""
    mock_db = AsyncMock()
    # Mock execute().all() for existing roles query
    mock_result = MagicMock()
    mock_result.all.return_value = []
    mock_db.execute.return_value = mock_result
    return mock_db


class TestAgentSeedService:
    """Test AgentSeedService.seed_project_agents()."""

    @pytest.mark.asyncio
    async def test_seeds_all_12_roles(self, db):
        """Creates 12 agent definitions when project has none."""
        svc = AgentSeedService(db)
        project_id = uuid4()

        created = await svc.seed_project_agents(project_id)

        assert len(created) == 12
        roles = {d.sdlc_role for d in created}
        expected_roles = set(ROLE_MODEL_DEFAULTS.keys())
        assert roles == expected_roles

    @pytest.mark.asyncio
    async def test_uses_correct_provider_model(self, db):
        """Each definition matches ROLE_MODEL_DEFAULTS config."""
        svc = AgentSeedService(db)
        created = await svc.seed_project_agents(uuid4())

        for defn in created:
            expected = ROLE_MODEL_DEFAULTS[defn.sdlc_role]
            assert defn.provider == expected["provider"]
            assert defn.model == expected["model"]

    @pytest.mark.asyncio
    async def test_se4h_roles_restricted(self, db):
        """SE4H roles (ceo, cpo, cto) get restricted permissions."""
        svc = AgentSeedService(db)
        created = await svc.seed_project_agents(uuid4())

        se4h_roles = {"ceo", "cpo", "cto"}
        for defn in created:
            if defn.sdlc_role in se4h_roles:
                assert defn.max_delegation_depth == 0
                assert defn.can_spawn_subagent is False
                assert "write_file" in defn.denied_tools
                assert defn.allowed_tools == ["read_file", "search", "analyze"]

    @pytest.mark.asyncio
    async def test_coder_low_temperature(self, db):
        """Coder/reviewer/tester get temperature 0.3."""
        svc = AgentSeedService(db)
        created = await svc.seed_project_agents(uuid4())

        low_temp_roles = {"coder", "reviewer", "tester"}
        for defn in created:
            if defn.sdlc_role in low_temp_roles:
                assert defn.temperature == 0.3
            else:
                assert defn.temperature == 0.7

    @pytest.mark.asyncio
    async def test_skips_existing_roles(self, db):
        """Skips roles that already have an active definition."""
        # Simulate "coder" and "reviewer" already exist
        mock_result = MagicMock()
        mock_result.all.return_value = [("coder",), ("reviewer",)]
        db.execute.return_value = mock_result

        svc = AgentSeedService(db)
        created = await svc.seed_project_agents(uuid4())

        assert len(created) == 10
        roles = {d.sdlc_role for d in created}
        assert "coder" not in roles
        assert "reviewer" not in roles

    @pytest.mark.asyncio
    async def test_skip_existing_false_seeds_all(self, db):
        """When skip_existing=False, seeds all 12 even if some exist."""
        # Simulate "coder" already exists
        mock_result = MagicMock()
        mock_result.all.return_value = [("coder",)]
        db.execute.return_value = mock_result

        svc = AgentSeedService(db)
        created = await svc.seed_project_agents(uuid4(), skip_existing=False)

        assert len(created) == 12

    @pytest.mark.asyncio
    async def test_binds_project_and_team(self, db):
        """All definitions reference the given project_id and team_id."""
        project_id = uuid4()
        team_id = uuid4()

        svc = AgentSeedService(db)
        created = await svc.seed_project_agents(project_id, team_id=team_id)

        for defn in created:
            assert defn.project_id == project_id
            assert defn.team_id == team_id

    @pytest.mark.asyncio
    async def test_all_definitions_active(self, db):
        """All seeded definitions are active."""
        svc = AgentSeedService(db)
        created = await svc.seed_project_agents(uuid4())

        for defn in created:
            assert defn.is_active is True

    @pytest.mark.asyncio
    async def test_coder_max_tokens_16384(self, db):
        """Coder gets highest max_tokens (16384) for code generation."""
        svc = AgentSeedService(db)
        created = await svc.seed_project_agents(uuid4())

        coder = next(d for d in created if d.sdlc_role == "coder")
        assert coder.max_tokens == 16384

    @pytest.mark.asyncio
    async def test_flush_called_when_created(self, db):
        """Calls db.flush() after adding definitions."""
        svc = AgentSeedService(db)
        await svc.seed_project_agents(uuid4())

        db.flush.assert_awaited_once()
