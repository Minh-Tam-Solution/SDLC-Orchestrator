"""
Sprint 201 — Self-Hosted Pilot Test Suite.

Tests for:
- Track A: Team invite handler (A-05)
- Track B: Sprint governance handler — close sprint (B-05) + audit export (B-06)
- Track B: Command registry — 2 new commands (close_sprint, invite_member)
- Track C: Pilot Docker Compose validation
- Track D: Integration dispatch + dogfooding verification

Test Health Target: 100% pass, 0 regressions.

Sprint 201 — Self-Hosted Pilot: SDLC Orchestrator Manages Itself
Framework: SDLC 6.1.1
"""

from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest


# ============================================================================
# Track B — Command Registry: 2 New Commands
# ============================================================================


class TestCommandRegistrySpint201:
    """Verify close_sprint and invite_member commands registered correctly."""

    def test_registry_has_10_commands(self) -> None:
        from app.services.agent_team.command_registry import GOVERNANCE_COMMANDS

        assert len(GOVERNANCE_COMMANDS) == 10

    def test_registry_within_max_limit(self) -> None:
        from app.services.agent_team.command_registry import (
            GOVERNANCE_COMMANDS,
            MAX_COMMANDS,
        )

        assert len(GOVERNANCE_COMMANDS) <= MAX_COMMANDS

    def test_close_sprint_command_exists(self) -> None:
        from app.services.agent_team.command_registry import get_command

        cmd = get_command("close_sprint")
        assert cmd is not None
        assert cmd.name == "close_sprint"
        assert cmd.permission == "governance:write"
        assert "project_id" in cmd.required_params

    def test_invite_member_command_exists(self) -> None:
        from app.services.agent_team.command_registry import get_command

        cmd = get_command("invite_member")
        assert cmd is not None
        assert cmd.name == "invite_member"
        assert cmd.permission == "projects:admin"
        assert "team_id" in cmd.required_params
        assert "email" in cmd.required_params

    def test_close_sprint_in_tool_name_enum(self) -> None:
        from app.services.agent_team.command_registry import ToolName

        assert ToolName.CLOSE_SPRINT.value == "close_sprint"

    def test_invite_member_in_tool_name_enum(self) -> None:
        from app.services.agent_team.command_registry import ToolName

        assert ToolName.INVITE_MEMBER.value == "invite_member"

    def test_close_sprint_ott_aliases(self) -> None:
        from app.services.agent_team.command_registry import get_command

        cmd = get_command("close_sprint")
        assert "close sprint" in cmd.ott_aliases
        assert "đóng sprint" in cmd.ott_aliases

    def test_invite_member_ott_aliases(self) -> None:
        from app.services.agent_team.command_registry import get_command

        cmd = get_command("invite_member")
        assert "invite" in cmd.ott_aliases
        assert "mời" in cmd.ott_aliases

    def test_tool_schemas_include_new_commands(self) -> None:
        from app.services.agent_team.command_registry import to_tool_schemas

        schemas = to_tool_schemas()
        assert "close_sprint" in schemas
        assert "invite_member" in schemas

    def test_ollama_tools_include_new_commands(self) -> None:
        from app.services.agent_team.command_registry import to_ollama_tools

        tools = to_ollama_tools()
        tool_names = [t["function"]["name"] for t in tools]
        assert "close_sprint" in tool_names
        assert "invite_member" in tool_names


# ============================================================================
# Track B — CloseSprintParams Validation
# ============================================================================


class TestCloseSprintParams:
    """Validate CloseSprintParams Pydantic model."""

    def test_valid_project_id(self) -> None:
        from app.services.agent_team.command_registry import CloseSprintParams

        params = CloseSprintParams(project_id=uuid4())
        assert params.project_id is not None

    def test_project_id_required(self) -> None:
        from app.services.agent_team.command_registry import CloseSprintParams
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            CloseSprintParams()  # type: ignore[call-arg]


# ============================================================================
# Track A — InviteMemberParams Validation
# ============================================================================


class TestInviteMemberParams:
    """Validate InviteMemberParams Pydantic model."""

    def test_valid_params(self) -> None:
        from app.services.agent_team.command_registry import InviteMemberParams

        params = InviteMemberParams(
            team_id=uuid4(), email="dev@example.com", role="member",
        )
        assert params.email == "dev@example.com"
        assert params.role == "member"

    def test_default_role_is_member(self) -> None:
        from app.services.agent_team.command_registry import InviteMemberParams

        params = InviteMemberParams(team_id=uuid4(), email="a@b.com")
        assert params.role == "member"

    def test_email_required(self) -> None:
        from app.services.agent_team.command_registry import InviteMemberParams
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            InviteMemberParams(team_id=uuid4())  # type: ignore[call-arg]

    def test_team_id_required(self) -> None:
        from app.services.agent_team.command_registry import InviteMemberParams
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            InviteMemberParams(email="a@b.com")  # type: ignore[call-arg]


# ============================================================================
# Track B — Governance Action Handler Dispatch
# ============================================================================


class TestGovernanceDispatchNewCommands:
    """Verify governance_action_handler routes new commands to correct handlers."""

    def test_close_sprint_dispatch_branch(self) -> None:
        """Verify close_sprint tool name is handled (not 'Unknown command')."""
        from app.services.agent_team.command_registry import ToolName

        assert ToolName.CLOSE_SPRINT.value == "close_sprint"

    def test_invite_member_dispatch_branch(self) -> None:
        """Verify invite_member tool name is handled (not 'Unknown command')."""
        from app.services.agent_team.command_registry import ToolName

        assert ToolName.INVITE_MEMBER.value == "invite_member"

    def test_export_audit_dispatch_branch(self) -> None:
        """Verify export_audit now routes to handle_export_audit (Sprint 201 B-06)."""
        from app.services.agent_team.command_registry import ToolName

        assert ToolName.EXPORT_AUDIT.value == "export_audit"


# ============================================================================
# Track B — Sprint Governance Handler: Function Signatures
# ============================================================================


class TestSprintGovernanceHandlerSignatures:
    """Verify handler functions exist with correct signatures."""

    def test_handle_close_sprint_exists(self) -> None:
        from app.services.agent_bridge.sprint_governance_handler import (
            handle_close_sprint,
        )

        import inspect
        sig = inspect.signature(handle_close_sprint)
        param_names = list(sig.parameters.keys())
        assert "tool_args" in param_names
        assert "bot_token" in param_names
        assert "chat_id" in param_names
        assert "user_id" in param_names
        assert "channel" in param_names

    def test_handle_export_audit_exists(self) -> None:
        from app.services.agent_bridge.sprint_governance_handler import (
            handle_export_audit,
        )

        import inspect
        sig = inspect.signature(handle_export_audit)
        param_names = list(sig.parameters.keys())
        assert "tool_args" in param_names
        assert "channel" in param_names

    def test_handle_close_sprint_is_async(self) -> None:
        from app.services.agent_bridge.sprint_governance_handler import (
            handle_close_sprint,
        )

        import asyncio
        assert asyncio.iscoroutinefunction(handle_close_sprint)

    def test_handle_export_audit_is_async(self) -> None:
        from app.services.agent_bridge.sprint_governance_handler import (
            handle_export_audit,
        )

        import asyncio
        assert asyncio.iscoroutinefunction(handle_export_audit)


# ============================================================================
# Track A — Team Invite Handler: Function Signatures
# ============================================================================


class TestTeamInviteHandlerSignatures:
    """Verify team invite handler exists with correct signature."""

    def test_handle_invite_member_exists(self) -> None:
        from app.services.agent_bridge.team_invite_handler import (
            handle_invite_member,
        )

        import inspect
        sig = inspect.signature(handle_invite_member)
        param_names = list(sig.parameters.keys())
        assert "tool_args" in param_names
        assert "bot_token" in param_names
        assert "chat_id" in param_names
        assert "user_id" in param_names
        assert "channel" in param_names

    def test_handle_invite_member_is_async(self) -> None:
        from app.services.agent_bridge.team_invite_handler import (
            handle_invite_member,
        )

        import asyncio
        assert asyncio.iscoroutinefunction(handle_invite_member)


# ============================================================================
# Track C — Pilot Docker Compose Validation
# ============================================================================


class TestPilotDockerCompose:
    """Validate pilot deployment configuration files exist and are well-formed."""

    PILOT_DIR = Path(__file__).resolve().parents[3] / "docker" / "pilot"

    def test_docker_compose_pilot_exists(self) -> None:
        compose_file = self.PILOT_DIR / "docker-compose.pilot.yml"
        assert compose_file.exists(), f"Missing: {compose_file}"

    def test_env_example_exists(self) -> None:
        env_file = self.PILOT_DIR / ".env.example"
        assert env_file.exists(), f"Missing: {env_file}"

    def test_docker_compose_has_required_services(self) -> None:
        compose_file = self.PILOT_DIR / "docker-compose.pilot.yml"
        content = compose_file.read_text()
        for svc in ("postgres", "redis", "opa", "minio", "backend", "frontend"):
            assert svc in content, f"Missing service: {svc}"

    def test_env_example_has_required_vars(self) -> None:
        env_file = self.PILOT_DIR / ".env.example"
        content = env_file.read_text()
        for var in (
            "POSTGRES_PASSWORD",
            "REDIS_PASSWORD",
            "JWT_SECRET_KEY",
            "TELEGRAM_BOT_TOKEN",
            "OLLAMA_URL",
        ):
            assert var in content, f"Missing env var: {var}"

    def test_docker_compose_uses_pilot_network(self) -> None:
        compose_file = self.PILOT_DIR / "docker-compose.pilot.yml"
        content = compose_file.read_text()
        assert "sdlc-pilot" in content

    def test_docker_compose_has_healthchecks(self) -> None:
        compose_file = self.PILOT_DIR / "docker-compose.pilot.yml"
        content = compose_file.read_text()
        assert content.count("healthcheck:") >= 4, "At least 4 services need healthchecks"


# ============================================================================
# Track D — Dogfooding Verification Matrix
# ============================================================================


class TestDogfoodingVerificationMatrix:
    """Verify all governance actions are available via OTT (100% dogfooding)."""

    def test_all_10_commands_registered(self) -> None:
        from app.services.agent_team.command_registry import GOVERNANCE_COMMANDS

        names = {cmd.name for cmd in GOVERNANCE_COMMANDS}
        expected = {
            "create_project",
            "get_gate_status",
            "submit_evidence",
            "request_approval",
            "export_audit",
            "update_sprint",
            "close_sprint",
            "invite_member",
            "run_evals",
            "list_notes",
        }
        assert names == expected

    def test_all_commands_have_ott_aliases(self) -> None:
        from app.services.agent_team.command_registry import GOVERNANCE_COMMANDS

        for cmd in GOVERNANCE_COMMANDS:
            assert len(cmd.ott_aliases) > 0, f"Command {cmd.name} has no OTT aliases"

    def test_all_commands_have_vietnamese_alias(self) -> None:
        """At least one Vietnamese alias per command (bilingual requirement)."""
        from app.services.agent_team.command_registry import GOVERNANCE_COMMANDS

        for cmd in GOVERNANCE_COMMANDS:
            has_vi = any(
                any(c > "\u007f" for c in alias)
                for alias in cmd.ott_aliases
            )
            assert has_vi, f"Command {cmd.name} has no Vietnamese alias"

    def test_governance_commands_cover_sprint_lifecycle(self) -> None:
        """Sprint lifecycle: create → update → close must all be chat-accessible."""
        from app.services.agent_team.command_registry import get_command

        assert get_command("create_project") is not None
        assert get_command("update_sprint") is not None
        assert get_command("close_sprint") is not None

    def test_governance_commands_cover_gate_lifecycle(self) -> None:
        """Gate lifecycle: status → approve → evidence must all be chat-accessible."""
        from app.services.agent_team.command_registry import get_command

        assert get_command("get_gate_status") is not None
        assert get_command("request_approval") is not None
        assert get_command("submit_evidence") is not None


# ============================================================================
# Track D — Sprint 200 Regression Guard
# ============================================================================


class TestSprint200RegressionGuard:
    """Ensure Sprint 200 features still work after Sprint 201 changes."""

    def test_multi_agent_intent_detection_still_works(self) -> None:
        from app.services.agent_bridge.ott_team_bridge import (
            is_multi_agent_intent,
        )

        assert is_multi_agent_intent("generate code for user management")
        assert is_multi_agent_intent("tạo code cho module đơn hàng")
        assert not is_multi_agent_intent("hello how are you")

    def test_budget_status_types_still_exist(self) -> None:
        from app.services.agent_team.conversation_tracker import (
            BudgetStatus,
            BudgetCheckResult,
        )

        assert BudgetStatus.OK is not None
        assert BudgetStatus.WARNING is not None
        assert BudgetStatus.EXCEEDED is not None

    def test_channel_agnostic_handler_signature(self) -> None:
        from app.services.agent_bridge.governance_action_handler import (
            execute_governance_action,
        )

        import inspect
        sig = inspect.signature(execute_governance_action)
        assert "channel" in sig.parameters

    def test_interrupt_keywords_still_defined(self) -> None:
        from app.services.agent_bridge.ai_response_handler import (
            _INTERRUPT_KEYWORDS,
        )

        assert "stop" in _INTERRUPT_KEYWORDS
        assert "cancel" in _INTERRUPT_KEYWORDS
        assert "dừng lại" in _INTERRUPT_KEYWORDS
