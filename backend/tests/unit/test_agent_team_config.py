"""
=========================================================================
Unit Tests - Agent Team Config (Sprint 177)
SDLC Orchestrator - Multi-Agent Team Engine

Version: 1.0.0
Date: February 2026
Status: ACTIVE - Sprint 177
Authority: CTO Approved (ADR-056)

Purpose:
- Test ROLE_MODEL_DEFAULTS coverage (12 roles)
- Test SE4H role detection and constraint overrides
- Test model defaults lookup per role

Zero Mock Policy: Pure logic tests, no DB needed
=========================================================================
"""

import pytest

from app.schemas.agent_team import SDLCRole, SE4H_ROLES, ROUTER_ROLES, SE4A_ROLES
from app.services.agent_team.config import (
    ROLE_MODEL_DEFAULTS,
    SE4H_CONSTRAINTS,
    get_model_defaults,
    is_se4h_role,
    get_se4h_overrides,
)


class TestRoleModelDefaults:
    """Tests for ROLE_MODEL_DEFAULTS configuration."""

    def test_all_12_roles_have_defaults(self):
        """Every SDLCRole value must have a model default entry."""
        for role in SDLCRole:
            assert role.value in ROLE_MODEL_DEFAULTS, (
                f"Role '{role.value}' missing from ROLE_MODEL_DEFAULTS"
            )
        assert len(ROLE_MODEL_DEFAULTS) == 12

    def test_each_default_has_provider_and_model(self):
        """Each entry must have 'provider' and 'model' keys."""
        for role_name, defaults in ROLE_MODEL_DEFAULTS.items():
            assert "provider" in defaults, f"Missing 'provider' for role '{role_name}'"
            assert "model" in defaults, f"Missing 'model' for role '{role_name}'"

    def test_se4a_roles_use_ollama(self):
        """SE4A roles should default to Ollama provider (cost optimization)."""
        se4a_values = {r.value for r in SE4A_ROLES}
        for role_name in se4a_values:
            assert ROLE_MODEL_DEFAULTS[role_name]["provider"] == "ollama", (
                f"SE4A role '{role_name}' should use ollama provider"
            )

    def test_se4h_roles_use_anthropic(self):
        """SE4H roles should default to Anthropic provider (best reasoning)."""
        se4h_values = {r.value for r in SE4H_ROLES}
        for role_name in se4h_values:
            assert ROLE_MODEL_DEFAULTS[role_name]["provider"] == "anthropic", (
                f"SE4H role '{role_name}' should use anthropic provider"
            )

    def test_assistant_uses_ollama(self):
        """Router role (assistant) should use Ollama (fast, cost-efficient)."""
        assert ROLE_MODEL_DEFAULTS["assistant"]["provider"] == "ollama"


class TestIsSe4hRole:
    """Tests for SE4H role detection."""

    def test_ceo_is_se4h(self):
        assert is_se4h_role(SDLCRole.CEO) is True

    def test_cpo_is_se4h(self):
        assert is_se4h_role(SDLCRole.CPO) is True

    def test_cto_is_se4h(self):
        assert is_se4h_role(SDLCRole.CTO) is True

    def test_coder_is_not_se4h(self):
        assert is_se4h_role(SDLCRole.CODER) is False

    def test_assistant_is_not_se4h(self):
        assert is_se4h_role(SDLCRole.ASSISTANT) is False

    def test_all_se4a_are_not_se4h(self):
        for role in SE4A_ROLES:
            assert is_se4h_role(role) is False, f"{role.value} should not be SE4H"


class TestGetSe4hOverrides:
    """Tests for SE4H constraint overrides."""

    def test_overrides_max_delegation_depth_zero(self):
        overrides = get_se4h_overrides()
        assert overrides["max_delegation_depth"] == 0

    def test_overrides_can_spawn_subagent_false(self):
        overrides = get_se4h_overrides()
        assert overrides["can_spawn_subagent"] is False

    def test_overrides_have_allowed_tools(self):
        overrides = get_se4h_overrides()
        assert "allowed_tools" in overrides
        assert isinstance(overrides["allowed_tools"], list)

    def test_overrides_have_denied_tools(self):
        overrides = get_se4h_overrides()
        assert "denied_tools" in overrides
        assert isinstance(overrides["denied_tools"], list)


class TestGetModelDefaults:
    """Tests for get_model_defaults helper (takes SDLCRole enum)."""

    def test_returns_defaults_for_valid_role(self):
        defaults = get_model_defaults(SDLCRole.CODER)
        assert defaults is not None
        assert "provider" in defaults
        assert "model" in defaults

    def test_returns_keyerror_for_unknown_role(self):
        """get_model_defaults raises KeyError for non-SDLCRole values."""
        # The function expects SDLCRole enum; passing a mock with unknown .value
        class FakeRole:
            value = "nonexistent"
        with pytest.raises(KeyError):
            get_model_defaults(FakeRole())

    def test_coder_defaults(self):
        defaults = get_model_defaults(SDLCRole.CODER)
        assert defaults["provider"] == "ollama"
        assert "coder" in defaults["model"].lower()

    def test_ceo_defaults(self):
        defaults = get_model_defaults(SDLCRole.CEO)
        assert defaults["provider"] == "anthropic"


class TestRoleClassification:
    """Tests for SASE role type classification sets."""

    def test_se4h_roles_count(self):
        assert len(SE4H_ROLES) == 3

    def test_router_roles_count(self):
        assert len(ROUTER_ROLES) == 1

    def test_se4a_roles_count(self):
        assert len(SE4A_ROLES) == 8

    def test_all_roles_classified(self):
        """Every role must be in exactly one classification set."""
        all_classified = SE4H_ROLES | ROUTER_ROLES | SE4A_ROLES
        assert all_classified == set(SDLCRole)

    def test_no_overlap(self):
        """Classification sets must be disjoint."""
        assert len(SE4H_ROLES & ROUTER_ROLES) == 0
        assert len(SE4H_ROLES & SE4A_ROLES) == 0
        assert len(ROUTER_ROLES & SE4A_ROLES) == 0
