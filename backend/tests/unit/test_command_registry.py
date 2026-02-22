"""
Sprint 191 Acceptance Tests — Unified Command Registry

8 tests verifying the command registry, OTT/CLI parity, SASE adapter,
requirements split, and Vietnamese aliases.

Sprint: 191 — Unified Command Registry + Post-Cleanup Stabilization
Framework: SDLC 6.1.0
"""

import pytest
from pydantic import BaseModel


class TestRegistryRoundtrip:
    """Verify registry returns 6 commands with all required fields."""

    def test_get_commands_returns_six(self):
        """get_commands() must return exactly 6 governance commands."""
        from app.services.agent_team.command_registry import get_commands

        commands = get_commands()
        assert len(commands) == 6, f"Expected 6 commands, got {len(commands)}"

    def test_commands_have_required_fields(self):
        """Each CommandDef must have all required fields populated."""
        from app.services.agent_team.command_registry import get_commands

        for cmd in get_commands():
            assert cmd.name, "Command missing name"
            assert cmd.description, f"Command {cmd.name} missing description"
            assert cmd.params is not None, f"Command {cmd.name} missing params"
            assert issubclass(cmd.params, BaseModel), (
                f"Command {cmd.name} params must be a Pydantic BaseModel subclass"
            )
            assert cmd.permission, f"Command {cmd.name} missing permission"
            assert cmd.handler, f"Command {cmd.name} missing handler"
            assert cmd.cli_name, f"Command {cmd.name} missing cli_name"
            assert cmd.ott_description, f"Command {cmd.name} missing ott_description"
            assert len(cmd.ott_aliases) > 0, (
                f"Command {cmd.name} missing ott_aliases"
            )

    def test_get_command_by_name(self):
        """get_command() must return the correct CommandDef by name."""
        from app.services.agent_team.command_registry import get_command

        cmd = get_command("create_project")
        assert cmd is not None
        assert cmd.name == "create_project"

        missing = get_command("nonexistent_command")
        assert missing is None


class TestOllamaToolsGeneration:
    """Verify to_ollama_tools() produces valid JSON Schema."""

    def test_ollama_tools_count(self):
        """to_ollama_tools() must produce 6 tool definitions."""
        from app.services.agent_team.command_registry import to_ollama_tools

        tools = to_ollama_tools()
        assert len(tools) == 6, f"Expected 6 Ollama tools, got {len(tools)}"

    def test_ollama_tools_structure(self):
        """Each Ollama tool must have type, function.name, function.description, function.parameters."""
        from app.services.agent_team.command_registry import to_ollama_tools

        for tool in to_ollama_tools():
            assert tool["type"] == "function"
            fn = tool["function"]
            assert "name" in fn, "Tool missing function.name"
            assert "description" in fn, f"Tool {fn.get('name')} missing description"
            assert "parameters" in fn, f"Tool {fn.get('name')} missing parameters"
            params = fn["parameters"]
            assert params.get("type") == "object", (
                f"Tool {fn['name']} parameters.type must be 'object'"
            )
            assert "properties" in params, (
                f"Tool {fn['name']} parameters missing properties"
            )


class TestToolSchemasMapping:
    """Verify to_tool_schemas() maps ToolName to Pydantic models."""

    def test_tool_schemas_maps_all_names(self):
        """to_tool_schemas() must map each ToolName to the correct Pydantic model."""
        from app.services.agent_team.command_registry import (
            ToolName,
            to_tool_schemas,
        )

        schemas = to_tool_schemas()
        for tn in ToolName:
            assert tn.value in schemas, (
                f"ToolName {tn.value} not found in tool schemas"
            )
            assert issubclass(schemas[tn.value], BaseModel), (
                f"Schema for {tn.value} must be a Pydantic BaseModel subclass"
            )


class TestCLIParity:
    """Verify CLI governance commands import and use registry schemas."""

    def test_cli_governance_importable(self):
        """CLI governance module must be importable (requires sdlcctl install)."""
        try:
            from sdlcctl.commands.governance import app as governance_app
            assert governance_app is not None
        except ModuleNotFoundError:
            # sdlcctl is a separate installable package — skip if not installed
            pytest.skip("sdlcctl not installed in this environment")

    def test_registry_cli_names_defined(self):
        """Each registry command must have a cli_name for Typer generation."""
        from app.services.agent_team.command_registry import get_commands

        for cmd in get_commands():
            assert cmd.cli_name, f"Command {cmd.name} missing cli_name"
            assert "-" in cmd.cli_name or cmd.cli_name.isalpha(), (
                f"CLI name should be kebab-case: {cmd.cli_name}"
            )


class TestSASEAntiRegression:
    """Verify SASE adapter decoupling works."""

    def test_sase_adapter_importable(self):
        """sase_adapter must re-export create_sase_generation_service."""
        from app.services.sase_adapter import create_sase_generation_service

        assert callable(create_sase_generation_service)


class TestVietnameseAliases:
    """Verify registry includes Vietnamese aliases for each command."""

    def test_all_commands_have_vietnamese_alias(self):
        """Each command must have at least one Vietnamese OTT alias."""
        from app.services.agent_team.command_registry import get_commands

        vietnamese_keywords = ["tạo", "trạng", "nộp", "duyệt", "xuất", "cập nhật"]
        for cmd in get_commands():
            has_vn = any(
                any(kw in alias for kw in vietnamese_keywords)
                for alias in cmd.ott_aliases
            )
            assert has_vn, (
                f"Command {cmd.name} missing Vietnamese alias. "
                f"Aliases: {cmd.ott_aliases}"
            )


class TestMaxCommandsGuard:
    """Verify registry enforces max 10 commands."""

    def test_max_commands_constant(self):
        """MAX_COMMANDS must be 10 (Expert 9 correction)."""
        from app.services.agent_team.command_registry import MAX_COMMANDS

        assert MAX_COMMANDS == 10

    def test_current_count_within_limit(self):
        """Current command count must not exceed MAX_COMMANDS."""
        from app.services.agent_team.command_registry import (
            GOVERNANCE_COMMANDS,
            MAX_COMMANDS,
        )

        assert len(GOVERNANCE_COMMANDS) <= MAX_COMMANDS, (
            f"Registry has {len(GOVERNANCE_COMMANDS)} commands, "
            f"exceeds MAX_COMMANDS={MAX_COMMANDS}"
        )


class TestRequirementsSplit:
    """Verify requirements/core.txt is valid."""

    def test_core_requirements_exists(self):
        """requirements/core.txt must exist and be non-empty."""
        from pathlib import Path

        core_path = Path(__file__).resolve().parents[2] / "requirements" / "core.txt"
        assert core_path.exists(), f"core.txt not found at {core_path}"
        content = core_path.read_text()
        assert len(content) > 100, (
            f"core.txt too short ({len(content)} chars), expected >100"
        )

    def test_core_requirements_has_fastapi(self):
        """core.txt must include fastapi (core production dependency)."""
        from pathlib import Path

        core_path = Path(__file__).resolve().parents[2] / "requirements" / "core.txt"
        content = core_path.read_text()
        assert "fastapi" in content.lower(), "core.txt missing fastapi"

    def test_core_requirements_has_sqlalchemy(self):
        """core.txt must include SQLAlchemy (core production dependency)."""
        from pathlib import Path

        core_path = Path(__file__).resolve().parents[2] / "requirements" / "core.txt"
        content = core_path.read_text()
        assert "sqlalchemy" in content.lower(), "core.txt missing SQLAlchemy"
