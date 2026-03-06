"""
Sprint 216 — P1 Context Injection + Delegation Links Tests.

Test coverage:
- D1: Delegation service (can_delegate, get_targets, create_link, deactivate_link)
- D2: Context injector (build_delegation_md, build_team_md, build_availability_md)
- D3: Spawn tool guard (authorized/unauthorized delegation)
- D4: FK cascade + preset persistence

References: FR-051 BDD scenarios, Sprint 216 Track D
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

# ─────────────────────────────────────────────────────────────────────────────
# D1: Delegation Service Tests
# ─────────────────────────────────────────────────────────────────────────────


class TestDelegationService:
    """Test delegation_service.py CRUD operations."""

    @pytest.fixture
    def mock_db(self):
        db = AsyncMock()
        db.execute = AsyncMock()
        db.flush = AsyncMock()
        db.add = MagicMock()
        db.rollback = AsyncMock()
        return db

    @pytest.fixture
    def service(self, mock_db):
        from app.services.agent_team.delegation_service import DelegationService
        return DelegationService(mock_db)

    @pytest.mark.asyncio
    async def test_can_delegate_returns_true_for_active_link(self, service, mock_db):
        """FR-051-02: Spawn tool allows delegation to linked target."""
        source_id = uuid4()
        target_id = uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 1
        mock_db.execute.return_value = mock_result

        result = await service.can_delegate(source_id, target_id)
        assert result is True

    @pytest.mark.asyncio
    async def test_can_delegate_returns_false_for_missing_link(self, service, mock_db):
        """FR-051-02: No active link → delegation denied."""
        source_id = uuid4()
        target_id = uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 0
        mock_db.execute.return_value = mock_result

        result = await service.can_delegate(source_id, target_id)
        assert result is False

    @pytest.mark.asyncio
    async def test_get_targets_returns_active_links(self, service, mock_db):
        """FR-051-03: get_targets returns correct agents, excludes inactive."""
        agent_id = uuid4()
        mock_link = MagicMock()
        mock_link.target_agent = MagicMock()
        mock_link.target_agent.agent_name = "coder"

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [mock_link]
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result

        targets = await service.get_targets(agent_id)
        assert len(targets) == 1
        assert targets[0].target_agent.agent_name == "coder"

    @pytest.mark.asyncio
    async def test_create_link_rejects_self_delegation(self, service):
        """FR-051-01: CHECK constraint — no self-delegation."""
        from app.services.agent_team.delegation_service import SelfDelegationError

        agent_id = uuid4()
        with pytest.raises(SelfDelegationError):
            await service.create_link(agent_id, agent_id)

    @pytest.mark.asyncio
    async def test_create_link_rejects_duplicate_active(self, service, mock_db):
        """FR-051-01: UNIQUE constraint prevents duplicate links."""
        from app.services.agent_team.delegation_service import DuplicateLinkError

        source_id = uuid4()
        target_id = uuid4()

        mock_existing = MagicMock()
        mock_existing.is_active = True
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_existing
        mock_db.execute.return_value = mock_result

        with pytest.raises(DuplicateLinkError):
            await service.create_link(source_id, target_id)

    @pytest.mark.asyncio
    async def test_create_link_reactivates_deactivated(self, service, mock_db):
        """Reactivate deactivated link instead of creating duplicate."""
        source_id = uuid4()
        target_id = uuid4()

        mock_existing = MagicMock()
        mock_existing.is_active = False
        mock_existing.updated_at = None
        mock_existing.metadata_ = {}
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_existing
        mock_db.execute.return_value = mock_result

        result = await service.create_link(source_id, target_id)
        assert result.is_active is True

    @pytest.mark.asyncio
    async def test_deactivate_link_soft_deletes(self, service, mock_db):
        """FR-051-01: Deactivate sets is_active=False, not hard delete."""
        source_id = uuid4()
        target_id = uuid4()

        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_db.execute.return_value = mock_result

        result = await service.deactivate_link(source_id, target_id)
        assert result is True

    @pytest.mark.asyncio
    async def test_deactivate_nonexistent_returns_false(self, service, mock_db):
        """Deactivate returns False when no active link found."""
        mock_result = MagicMock()
        mock_result.rowcount = 0
        mock_db.execute.return_value = mock_result

        result = await service.deactivate_link(uuid4(), uuid4())
        assert result is False

    @pytest.mark.asyncio
    async def test_get_target_count(self, service, mock_db):
        """get_target_count returns correct count of active targets."""
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 5
        mock_db.execute.return_value = mock_result

        count = await service.get_target_count(uuid4())
        assert count == 5

    @pytest.mark.asyncio
    async def test_get_max_updated_at(self, service, mock_db):
        """get_max_updated_at returns datetime for cache key."""
        ts = datetime(2026, 3, 4, 10, 0, 0)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = ts
        mock_db.execute.return_value = mock_result

        result = await service.get_max_updated_at(uuid4())
        assert result == ts


# ─────────────────────────────────────────────────────────────────────────────
# D2: Context Injector Tests
# ─────────────────────────────────────────────────────────────────────────────


class TestContextInjector:
    """Test context_injector.py — 3 builders + inject entrypoint."""

    @pytest.fixture
    def mock_db(self):
        db = AsyncMock()
        db.execute = AsyncMock()
        return db

    @pytest.fixture
    def injector(self, mock_db):
        from app.services.agent_team.context_injector import ContextInjector
        return ContextInjector(mock_db)

    @pytest.mark.asyncio
    async def test_build_delegation_md_with_targets(self, injector):
        """FR-051-03: DELEGATION.md with <=15 targets — correct XML output."""
        agent_id = uuid4()

        mock_target = MagicMock()
        mock_target.agent_name = "coder-alpha"
        mock_target.sdlc_role = "coder"
        mock_target.system_prompt = "Generates production-ready Python code"

        mock_link = MagicMock()
        mock_link.target_agent = mock_target

        with patch.object(
            injector._delegation_service, "get_targets",
            return_value=[mock_link]
        ):
            result = await injector.build_delegation_md(agent_id)

        assert "<delegation>" in result
        assert "</delegation>" in result
        assert "@coder-alpha" in result
        assert "role: coder" in result

    @pytest.mark.asyncio
    async def test_build_delegation_md_overflow(self, injector):
        """FR-051-03: >15 targets — truncated with search instruction."""
        agent_id = uuid4()

        # Create 20 mock links
        links = []
        for i in range(20):
            mock_target = MagicMock()
            mock_target.agent_name = f"agent-{i}"
            mock_target.sdlc_role = "coder"
            mock_target.system_prompt = f"Agent {i} desc"
            mock_link = MagicMock()
            mock_link.target_agent = mock_target
            links.append(mock_link)

        with patch.object(
            injector._delegation_service, "get_targets",
            return_value=links
        ):
            result = await injector.build_delegation_md(agent_id)

        assert "5 more targets not shown" in result
        assert "@search" in result
        # Should show first 15
        assert "@agent-14" in result
        # Should NOT show 16th
        assert "@agent-15" not in result

    @pytest.mark.asyncio
    async def test_build_delegation_md_empty(self, injector):
        """DELEGATION.md is empty string when agent has 0 targets."""
        with patch.object(
            injector._delegation_service, "get_targets",
            return_value=[]
        ):
            result = await injector.build_delegation_md(uuid4())

        assert result == ""

    @pytest.mark.asyncio
    async def test_build_team_md_lead_variant(self, injector, mock_db):
        """FR-051-04: TEAM.md for lead includes full roster."""
        agent_id = uuid4()
        team_id = uuid4()

        mock_team = MagicMock()
        mock_team.name = "backend-team"
        mock_team.lead_agent_definition_id = agent_id

        mock_agent = MagicMock()
        mock_agent.id = agent_id
        mock_agent.agent_name = "lead-agent"
        mock_agent.sdlc_role = "architect"

        mock_member = MagicMock()
        mock_member.id = uuid4()
        mock_member.agent_name = "coder-alpha"
        mock_member.sdlc_role = "coder"

        # First call: team query
        team_result = MagicMock()
        team_result.scalar_one_or_none.return_value = mock_team

        # Second call: agent query
        agent_result = MagicMock()
        agent_result.scalar_one_or_none.return_value = mock_agent

        # Third call: team members query
        members_scalars = MagicMock()
        members_scalars.all.return_value = [mock_agent, mock_member]
        members_result = MagicMock()
        members_result.scalars.return_value = members_scalars

        mock_db.execute.side_effect = [team_result, agent_result, members_result]

        result = await injector.build_team_md(agent_id, team_id)

        assert "<team>" in result
        assert "Team Context (Lead)" in result
        assert "backend-team" in result
        assert "@coder-alpha" in result

    @pytest.mark.asyncio
    async def test_build_team_md_member_variant(self, injector, mock_db):
        """FR-051-04: TEAM.md for member includes lead reference."""
        agent_id = uuid4()
        lead_id = uuid4()
        team_id = uuid4()

        mock_team = MagicMock()
        mock_team.name = "backend-team"
        mock_team.lead_agent_definition_id = lead_id  # Different from agent_id

        mock_agent = MagicMock()
        mock_agent.id = agent_id
        mock_agent.agent_name = "coder"
        mock_agent.sdlc_role = "coder"

        mock_lead = MagicMock()
        mock_lead.id = lead_id
        mock_lead.agent_name = "lead-bot"

        members_scalars = MagicMock()
        members_scalars.all.return_value = [mock_agent]
        members_result = MagicMock()
        members_result.scalars.return_value = members_scalars

        team_result = MagicMock()
        team_result.scalar_one_or_none.return_value = mock_team
        agent_result = MagicMock()
        agent_result.scalar_one_or_none.return_value = mock_agent
        # 4th call: lead agent async lookup (F1 fix)
        lead_result = MagicMock()
        lead_result.scalar_one_or_none.return_value = mock_lead

        mock_db.execute.side_effect = [team_result, agent_result, members_result, lead_result]

        result = await injector.build_team_md(agent_id, team_id)

        assert "<team>" in result
        assert "Team Context (Member)" in result
        assert "backend-team" in result
        assert "@lead-bot" in result
        assert "Escalate blockers" in result

    @pytest.mark.asyncio
    async def test_build_team_md_no_team(self, injector):
        """TEAM.md is empty when team_id is None."""
        result = await injector.build_team_md(uuid4(), None)
        assert result == ""

    @pytest.mark.asyncio
    async def test_build_availability_md_no_targets(self, injector):
        """FR-051-05: AVAILABILITY.md with 0 targets — negative context."""
        with patch.object(
            injector._delegation_service, "get_target_count",
            return_value=0
        ):
            result = await injector.build_availability_md(uuid4())

        assert "<availability>" in result
        assert "no delegation targets" in result
        assert "Do NOT attempt" in result

    @pytest.mark.asyncio
    async def test_build_availability_md_with_targets(self, injector):
        """FR-051-05: AVAILABILITY.md is empty when agent has targets."""
        with patch.object(
            injector._delegation_service, "get_target_count",
            return_value=3
        ):
            result = await injector.build_availability_md(uuid4())

        assert result == ""

    @pytest.mark.asyncio
    async def test_build_delegation_md_xml_escapes_user_content(self, injector):
        """FR-051: Agent description with <script> is XML-escaped."""
        agent_id = uuid4()

        mock_target = MagicMock()
        mock_target.agent_name = "evil<script>agent"
        mock_target.sdlc_role = "coder"
        mock_target.system_prompt = '<script>alert("xss")</script>'

        mock_link = MagicMock()
        mock_link.target_agent = mock_target

        with patch.object(
            injector._delegation_service, "get_targets",
            return_value=[mock_link]
        ):
            result = await injector.build_delegation_md(agent_id)

        assert "<script>" not in result
        assert "&lt;script&gt;" in result

    @pytest.mark.asyncio
    async def test_inject_context_appends_all_sections(self, injector):
        """FR-051-06: inject_context appends DELEGATION + TEAM + AVAILABILITY."""
        agent_id = uuid4()
        base_prompt = "You are an AI assistant."

        with patch.object(injector, "build_delegation_md", return_value="<delegation>test</delegation>"), \
             patch.object(injector, "build_team_md", return_value="<team>test</team>"), \
             patch.object(injector, "build_availability_md", return_value=""), \
             patch.object(injector, "build_skills_md", return_value=""):
            result = await injector.inject_context(agent_id, uuid4(), base_prompt)

        assert result.startswith(base_prompt)
        assert "<system_context>" in result
        assert "<delegation>" in result
        assert "<team>" in result

    @pytest.mark.asyncio
    async def test_inject_context_no_sections(self, injector):
        """inject_context returns unchanged prompt when no sections generated."""
        base_prompt = "You are an AI assistant."

        with patch.object(injector, "build_delegation_md", return_value=""), \
             patch.object(injector, "build_team_md", return_value=""), \
             patch.object(injector, "build_availability_md", return_value=""), \
             patch.object(injector, "build_skills_md", return_value=""):
            result = await injector.inject_context(uuid4(), None, base_prompt)

        assert result == base_prompt


# ─────────────────────────────────────────────────────────────────────────────
# D3: Spawn Tool Guard Tests
# ─────────────────────────────────────────────────────────────────────────────


class TestSpawnToolGuard:
    """Test spawn tool delegation guard (tool_context.py additions)."""

    @pytest.mark.asyncio
    async def test_authorized_delegation_passes(self):
        """FR-051-02: Authorized delegation — spawn allowed."""
        from app.services.agent_team.tool_context import check_delegation_authorized

        mock_db = AsyncMock()
        source_id = uuid4()
        target_id = uuid4()

        with patch(
            "app.services.agent_team.delegation_service.DelegationService"
        ) as MockSvc:
            mock_svc = MockSvc.return_value
            mock_svc.can_delegate = AsyncMock(return_value=True)

            # Should not raise
            await check_delegation_authorized(source_id, target_id, mock_db)

    @pytest.mark.asyncio
    async def test_unauthorized_delegation_raises(self):
        """FR-051-02: Unauthorized delegation — DelegationDenied raised."""
        from app.services.agent_team.tool_context import (
            DelegationDenied,
            check_delegation_authorized,
        )

        mock_db = AsyncMock()
        source_id = uuid4()
        target_id = uuid4()

        with patch(
            "app.services.agent_team.delegation_service.DelegationService"
        ) as MockSvc:
            mock_svc = MockSvc.return_value
            mock_svc.can_delegate = AsyncMock(return_value=False)
            mock_svc.get_targets = AsyncMock(return_value=[])

            with pytest.raises(DelegationDenied, match="no delegation targets"):
                await check_delegation_authorized(source_id, target_id, mock_db)

    @pytest.mark.asyncio
    async def test_unauthorized_delegation_lists_available_targets(self):
        """FR-051-02: Rejection error lists available target names."""
        from app.services.agent_team.tool_context import (
            DelegationDenied,
            check_delegation_authorized,
        )

        mock_db = AsyncMock()

        with patch(
            "app.services.agent_team.delegation_service.DelegationService"
        ) as MockSvc:
            mock_svc = MockSvc.return_value
            mock_svc.can_delegate = AsyncMock(return_value=False)

            mock_target = MagicMock()
            mock_target.target_agent = MagicMock()
            mock_target.target_agent.agent_name = "coder"
            mock_svc.get_targets = AsyncMock(return_value=[mock_target])

            with pytest.raises(DelegationDenied, match="Available targets: coder"):
                await check_delegation_authorized(uuid4(), uuid4(), mock_db)

    def test_delegation_denied_is_permission_denied_subclass(self):
        """DelegationDenied inherits from ToolPermissionDenied."""
        from app.services.agent_team.tool_context import (
            DelegationDenied,
            ToolPermissionDenied,
        )

        assert issubclass(DelegationDenied, ToolPermissionDenied)


# ─────────────────────────────────────────────────────────────────────────────
# D4: Model + Preset Persistence Tests
# ─────────────────────────────────────────────────────────────────────────────


class TestDelegationLinkModel:
    """Test delegation_link.py model structure."""

    def test_model_tablename(self):
        from app.models.delegation_link import DelegationLink
        assert DelegationLink.__tablename__ == "delegation_links"

    def test_model_to_dict(self):
        from app.models.delegation_link import DelegationLink
        link = DelegationLink(
            source_agent_id=uuid4(),
            target_agent_id=uuid4(),
            link_type="can_delegate",
            is_active=True,
            metadata_={},
            created_at=datetime(2026, 3, 4),
            updated_at=datetime(2026, 3, 4),
        )
        d = link.to_dict()
        assert d["link_type"] == "can_delegate"
        assert d["is_active"] is True
        assert "source_agent_id" in d
        assert "target_agent_id" in d

    def test_model_has_check_constraint(self):
        """No self-delegation CHECK constraint exists."""
        from app.models.delegation_link import DelegationLink
        constraints = DelegationLink.__table_args__
        check_names = [c.name for c in constraints if hasattr(c, "name")]
        assert "ck_delegation_link_no_self" in check_names

    def test_model_has_unique_constraint(self):
        """UNIQUE(source, target, link_type) constraint exists."""
        from app.models.delegation_link import DelegationLink
        constraints = DelegationLink.__table_args__
        uq_names = [c.name for c in constraints if hasattr(c, "name")]
        assert "uq_delegation_link_source_target_type" in uq_names


class TestTeamLeadColumn:
    """Test teams.lead_agent_definition_id column (Sprint 216 Track B)."""

    def test_team_model_has_lead_column(self):
        from app.models.team import Team
        assert hasattr(Team, "lead_agent_definition_id")

    def test_team_model_has_lead_relationship(self):
        from app.models.team import Team
        assert hasattr(Team, "lead_agent")


class TestTeamPresetDelegation:
    """Test team_presets.py delegation chain persistence."""

    def test_presets_have_delegation_chains(self):
        from app.services.agent_team.team_presets import TEAM_PRESETS
        # full-sprint preset should have delegation chain
        full_sprint = TEAM_PRESETS["full-sprint"]
        assert len(full_sprint.delegation_chain) > 0
        assert ("pm", "architect") in full_sprint.delegation_chain

    def test_solo_dev_has_no_chain(self):
        from app.services.agent_team.team_presets import TEAM_PRESETS
        solo = TEAM_PRESETS["solo-dev"]
        assert len(solo.delegation_chain) == 0

    def test_preset_to_dict_includes_chain(self):
        from app.services.agent_team.team_presets import TEAM_PRESETS
        d = TEAM_PRESETS["enterprise-3"].to_dict()
        assert "delegation_chain" in d
        assert len(d["delegation_chain"]) == 2


# ─────────────────────────────────────────────────────────────────────────────
# Model Registration Test
# ─────────────────────────────────────────────────────────────────────────────


class TestModelRegistration:
    """Verify DelegationLink is properly registered."""

    def test_delegation_link_in_models_init(self):
        from app.models import DelegationLink
        assert DelegationLink.__tablename__ == "delegation_links"

    def test_delegation_link_in_all_exports(self):
        import app.models as models
        assert "DelegationLink" in models.__all__
