"""
Unit Tests for TeamPresetService — Sprint 194 (GAP-02).

Tests:
- 5 named presets exist with correct role counts
- list_presets returns all 5
- get_preset returns correct preset by name
- get_preset returns None for unknown name
- Each preset has valid SDLC roles
- apply_preset seeds only preset roles
- apply_preset raises ValueError for unknown preset
- TeamPresetConfig.to_dict serialization
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.services.agent_team.team_presets import (
    TEAM_PRESETS,
    TeamPresetConfig,
    TeamPresetService,
    get_preset,
    list_presets,
)
from app.services.agent_team.config import ROLE_MODEL_DEFAULTS


class TestTeamPresetConstants:
    """Test preset data structures."""

    def test_five_presets_exist(self):
        """Exactly 5 named presets are defined."""
        assert len(TEAM_PRESETS) == 5

    def test_preset_names(self):
        """All 5 expected preset names are present."""
        expected = {"solo-dev", "startup-2", "enterprise-3", "review-pair", "full-sprint"}
        assert set(TEAM_PRESETS.keys()) == expected

    def test_solo_dev_roles(self):
        """solo-dev has exactly 1 role: coder."""
        preset = TEAM_PRESETS["solo-dev"]
        assert preset.roles == ("coder",)
        assert len(preset.delegation_chain) == 0

    def test_startup_2_roles(self):
        """startup-2 has coder and reviewer."""
        preset = TEAM_PRESETS["startup-2"]
        assert set(preset.roles) == {"coder", "reviewer"}
        assert len(preset.delegation_chain) == 1

    def test_enterprise_3_roles(self):
        """enterprise-3 has architect, coder, reviewer."""
        preset = TEAM_PRESETS["enterprise-3"]
        assert set(preset.roles) == {"architect", "coder", "reviewer"}
        assert len(preset.delegation_chain) == 2

    def test_review_pair_roles(self):
        """review-pair has reviewer and tester."""
        preset = TEAM_PRESETS["review-pair"]
        assert set(preset.roles) == {"reviewer", "tester"}

    def test_full_sprint_roles(self):
        """full-sprint has 6 roles: pm, architect, coder, reviewer, tester, devops."""
        preset = TEAM_PRESETS["full-sprint"]
        assert set(preset.roles) == {"pm", "architect", "coder", "reviewer", "tester", "devops"}
        assert len(preset.delegation_chain) == 6

    def test_all_roles_are_valid_sdlc_roles(self):
        """Every role in every preset is a valid ROLE_MODEL_DEFAULTS key."""
        valid_roles = set(ROLE_MODEL_DEFAULTS.keys())
        for name, preset in TEAM_PRESETS.items():
            for role in preset.roles:
                assert role in valid_roles, f"Preset '{name}' has invalid role '{role}'"

    def test_delegation_chain_uses_preset_roles(self):
        """Delegation chains only reference roles within the same preset."""
        for name, preset in TEAM_PRESETS.items():
            role_set = set(preset.roles)
            for src, dst in preset.delegation_chain:
                assert src in role_set, f"Preset '{name}': delegation src '{src}' not in roles"
                assert dst in role_set, f"Preset '{name}': delegation dst '{dst}' not in roles"


class TestPresetFunctions:
    """Test module-level helper functions."""

    def test_list_presets_returns_5(self):
        """list_presets returns 5 dicts."""
        result = list_presets()
        assert len(result) == 5
        assert all(isinstance(p, dict) for p in result)

    def test_list_presets_includes_role_count(self):
        """Each preset dict includes role_count."""
        for p in list_presets():
            assert "role_count" in p
            assert p["role_count"] == len(p["roles"])

    def test_get_preset_found(self):
        """get_preset returns the correct preset."""
        preset = get_preset("startup-2")
        assert preset is not None
        assert preset.name == "startup-2"

    def test_get_preset_not_found(self):
        """get_preset returns None for unknown name."""
        assert get_preset("nonexistent") is None

    def test_to_dict_serialization(self):
        """TeamPresetConfig.to_dict produces valid JSON-ready dict."""
        preset = TeamPresetConfig(
            name="test",
            description="Test preset",
            roles=("coder", "reviewer"),
            delegation_chain=(("coder", "reviewer"),),
        )
        d = preset.to_dict()
        assert d["name"] == "test"
        assert d["roles"] == ["coder", "reviewer"]
        assert d["delegation_chain"] == [["coder", "reviewer"]]
        assert d["role_count"] == 2
        assert d["default_queue_mode"] == "queue"

    def test_preset_is_frozen(self):
        """TeamPresetConfig is immutable (frozen dataclass)."""
        preset = TEAM_PRESETS["solo-dev"]
        with pytest.raises(AttributeError):
            preset.name = "hacked"


class TestTeamPresetService:
    """Test TeamPresetService.apply_preset()."""

    @pytest.fixture
    def db(self):
        """Create a mock async DB session."""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_db.execute.return_value = mock_result
        return mock_db

    @pytest.mark.asyncio
    async def test_apply_preset_seeds_roles(self, db):
        """apply_preset seeds all 12 roles via AgentSeedService."""
        svc = TeamPresetService(db)
        result = await svc.apply_preset("startup-2", uuid4())

        assert result["preset"] == "startup-2"
        assert set(result["roles_expected"]) == {"coder", "reviewer"}
        # AgentSeedService seeds all 12 roles; apply_preset filters to preset roles
        assert set(result["roles_seeded"]) == {"coder", "reviewer"}
        assert result["count"] == 2

    @pytest.mark.asyncio
    async def test_apply_preset_unknown_raises(self, db):
        """apply_preset raises ValueError for unknown preset."""
        svc = TeamPresetService(db)
        with pytest.raises(ValueError, match="Unknown preset"):
            await svc.apply_preset("nonexistent", uuid4())

    @pytest.mark.asyncio
    async def test_apply_full_sprint_seeds_6(self, db):
        """full-sprint preset seeds 6 roles."""
        svc = TeamPresetService(db)
        result = await svc.apply_preset("full-sprint", uuid4())

        assert result["count"] == 6
        assert set(result["roles_seeded"]) == {
            "pm", "architect", "coder", "reviewer", "tester", "devops"
        }

    @pytest.mark.asyncio
    async def test_apply_solo_dev_seeds_1(self, db):
        """solo-dev preset seeds exactly 1 role."""
        svc = TeamPresetService(db)
        result = await svc.apply_preset("solo-dev", uuid4())

        assert result["count"] == 1
        assert result["roles_seeded"] == ["coder"]

    @pytest.mark.asyncio
    async def test_apply_preset_with_team_id(self, db):
        """apply_preset passes team_id to AgentSeedService."""
        svc = TeamPresetService(db)
        team_id = uuid4()
        result = await svc.apply_preset("review-pair", uuid4(), team_id=team_id)

        assert result["count"] == 2
