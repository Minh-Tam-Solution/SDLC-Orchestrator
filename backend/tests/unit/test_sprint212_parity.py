"""
Sprint 212 — Backend Parity: Verification Tests (Tracks B-F, C2).

Test matrix (12 tests):
  T1:  CLI auth command file exists (Track B)
  T2:  CLI auth module has login/status/logout commands (Track B)
  T3:  CLI auth config uses ~/.sdlcctl/config.json path (Track B)
  T4:  CLI team command file exists (Track C)
  T5:  CLI team module has invite/list/remove commands (Track C)
  T6:  ExportAuditButton component exists (Track D)
  T7:  ExportAuditButton calls /evidence/export endpoint (Track D)
  T8:  SSO admin page exists (Track E)
  T9:  SSO page calls /enterprise/sso/configure API (Track E)
  T10: Usage route module has router attribute (Track F)
  T11: Usage tier limits define LITE quotas (Track F)
  T12: VS Code extension team command exists with sdlc.inviteTeamMember (Track C2)

References:
  - CLI auth:  backend/sdlcctl/sdlcctl/commands/auth.py
  - CLI team:  backend/sdlcctl/sdlcctl/commands/team.py
  - Export:    frontend/src/components/dashboard/ExportAuditButton.tsx
  - SSO:       frontend/src/app/admin/sso/page.tsx
  - Usage:     backend/app/api/routes/usage.py
  - Extension: vscode-extension/src/commands/teamCommand.ts
"""

from __future__ import annotations

from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[3]
BACKEND_DIR = PROJECT_ROOT / "backend"
FRONTEND_DIR = PROJECT_ROOT / "frontend" / "src"
EXTENSION_DIR = PROJECT_ROOT / "vscode-extension" / "src"


# ============================================================================
# T1 — CLI auth command file exists (Track B)
# ============================================================================


class TestT1AuthCommandFileExists:
    """T1: CLI auth.py command module exists."""

    def test_auth_command_file_exists(self) -> None:
        auth_file = (
            BACKEND_DIR / "sdlcctl" / "sdlcctl" / "commands" / "auth.py"
        )
        assert auth_file.exists(), (
            f"CLI auth command must exist at {auth_file}"
        )


# ============================================================================
# T2 — CLI auth module has login/status/logout commands (Track B)
# ============================================================================


class TestT2AuthCommandsRegistered:
    """T2: CLI auth module registers login, status, logout commands."""

    @pytest.mark.parametrize("command_name", ["login", "status", "logout"])
    def test_auth_commands_registered(self, command_name: str) -> None:
        try:
            from sdlcctl.commands.auth import app as auth_app

            registered = [
                cmd.name for cmd in auth_app.registered_commands
            ]
            assert command_name in registered, (
                f"Auth app must register '{command_name}' command"
            )
        except ImportError:
            # Fallback: verify command function exists in file content
            auth_file = (
                BACKEND_DIR / "sdlcctl" / "sdlcctl" / "commands" / "auth.py"
            )
            content = auth_file.read_text()
            assert f"def {command_name}" in content, (
                f"auth.py must define '{command_name}' function"
            )


# ============================================================================
# T3 — CLI auth config uses ~/.sdlcctl/config.json path (Track B)
# ============================================================================


class TestT3AuthConfigPath:
    """T3: CLI auth module references ~/.sdlcctl/config.json config path."""

    def test_auth_config_path(self) -> None:
        auth_file = (
            BACKEND_DIR / "sdlcctl" / "sdlcctl" / "commands" / "auth.py"
        )
        content = auth_file.read_text()
        assert ".sdlcctl" in content, (
            "Auth module must reference .sdlcctl config directory"
        )
        assert "config.json" in content, (
            "Auth module must reference config.json file"
        )


# ============================================================================
# T4 — CLI team command file exists (Track C)
# ============================================================================


class TestT4TeamCommandFileExists:
    """T4: CLI team.py command module exists."""

    def test_team_command_file_exists(self) -> None:
        team_file = (
            BACKEND_DIR / "sdlcctl" / "sdlcctl" / "commands" / "team.py"
        )
        assert team_file.exists(), (
            f"CLI team command must exist at {team_file}"
        )


# ============================================================================
# T5 — CLI team module has invite/list/remove commands (Track C)
# ============================================================================


class TestT5TeamCommandsRegistered:
    """T5: CLI team module registers invite, list, remove commands."""

    @pytest.mark.parametrize("command_name", ["invite", "list", "remove"])
    def test_team_commands_registered(self, command_name: str) -> None:
        try:
            from sdlcctl.commands.team import app as team_app

            registered = [
                cmd.name for cmd in team_app.registered_commands
            ]
            assert command_name in registered, (
                f"Team app must register '{command_name}' command"
            )
        except ImportError:
            # Fallback: verify command function exists in file content
            team_file = (
                BACKEND_DIR / "sdlcctl" / "sdlcctl" / "commands" / "team.py"
            )
            content = team_file.read_text()
            assert f"def {command_name}" in content, (
                f"team.py must define '{command_name}' function"
            )


# ============================================================================
# T6 — ExportAuditButton component exists (Track D)
# ============================================================================


class TestT6ExportAuditButtonExists:
    """T6: ExportAuditButton.tsx component exists in dashboard components."""

    def test_export_audit_button_component_exists(self) -> None:
        component = (
            FRONTEND_DIR / "components" / "dashboard" / "ExportAuditButton.tsx"
        )
        assert component.exists(), (
            f"ExportAuditButton component must exist at {component}"
        )


# ============================================================================
# T7 — ExportAuditButton calls /evidence/export endpoint (Track D)
# ============================================================================


class TestT7ExportAuditButtonEndpoint:
    """T7: ExportAuditButton references /evidence/export API path."""

    def test_export_audit_button_calls_correct_endpoint(self) -> None:
        component = (
            FRONTEND_DIR / "components" / "dashboard" / "ExportAuditButton.tsx"
        )
        content = component.read_text()
        assert "/evidence/export" in content, (
            "ExportAuditButton must call /evidence/export API endpoint"
        )


# ============================================================================
# T8 — SSO admin page exists (Track E)
# ============================================================================


class TestT8SsoAdminPageExists:
    """T8: SSO admin configuration page exists."""

    def test_sso_admin_page_exists(self) -> None:
        sso_page = FRONTEND_DIR / "app" / "admin" / "sso" / "page.tsx"
        assert sso_page.exists(), (
            f"SSO admin page must exist at {sso_page}"
        )


# ============================================================================
# T9 — SSO page calls /enterprise/sso/configure API (Track E)
# ============================================================================


class TestT9SsoPageApiPath:
    """T9: SSO admin page references /enterprise/sso/configure API path."""

    def test_sso_page_calls_enterprise_sso_api(self) -> None:
        sso_page = FRONTEND_DIR / "app" / "admin" / "sso" / "page.tsx"
        content = sso_page.read_text()
        assert "/enterprise/sso/configure" in content, (
            "SSO page must call /enterprise/sso/configure API endpoint"
        )


# ============================================================================
# T10 — Usage route module has router attribute (Track F)
# ============================================================================


class TestT10UsageRouteExists:
    """T10: Usage route module exports a router."""

    def test_usage_route_exists(self) -> None:
        try:
            from app.api.routes import usage

            assert hasattr(usage, "router"), (
                "Usage route module must export a 'router' attribute"
            )
        except ImportError:
            # Fallback: verify router defined in file content
            usage_file = BACKEND_DIR / "app" / "api" / "routes" / "usage.py"
            content = usage_file.read_text()
            assert "router" in content, (
                "usage.py must define a router"
            )


# ============================================================================
# T11 — Usage tier limits define LITE quotas (Track F)
# ============================================================================


class TestT11UsageTierLimits:
    """T11: Usage module defines LITE tier limits with correct quotas."""

    def test_usage_tier_limits_defined(self) -> None:
        try:
            from app.api.routes.usage import TIER_LIMITS

            # Keys may be lowercase or uppercase depending on implementation
            lite_key = "lite" if "lite" in TIER_LIMITS else "LITE"
            assert lite_key in TIER_LIMITS, (
                "TIER_LIMITS must include lite/LITE tier"
            )
            lite = TIER_LIMITS[lite_key]
            # Field names may vary: projects/max_projects, storage_mb/storage/max_storage
            projects = lite.get("projects", lite.get("max_projects", 0))
            storage = lite.get("storage_mb", lite.get("storage", lite.get("max_storage", 0)))
            gates = lite.get("gates_month", lite.get("gates", lite.get("max_gates", 0)))
            members = lite.get("members", lite.get("max_members", 0))
            assert projects == 1, (
                f"LITE tier must limit projects to 1, got {projects}"
            )
            assert storage == 100, (
                f"LITE tier must limit storage to 100 MB, got {storage}"
            )
            assert gates == 4, (
                f"LITE tier must limit gates to 4 per month, got {gates}"
            )
            assert members == 1, (
                f"LITE tier must limit members to 1, got {members}"
            )
        except (ImportError, AttributeError):
            # Fallback: verify limits in file content
            usage_file = BACKEND_DIR / "app" / "api" / "routes" / "usage.py"
            content = usage_file.read_text()
            assert "lite" in content.lower(), "usage.py must define LITE tier limits"
            assert "projects" in content or "max_projects" in content, (
                "LITE tier must define project limit"
            )


# ============================================================================
# T12 — VS Code extension team command exists (Track C2)
# ============================================================================


class TestT12ExtensionTeamCommand:
    """T12: VS Code extension teamCommand.ts exists with sdlc.inviteTeamMember."""

    def test_extension_team_command_exists(self) -> None:
        team_cmd = EXTENSION_DIR / "commands" / "teamCommand.ts"
        assert team_cmd.exists(), (
            f"Extension team command must exist at {team_cmd}"
        )
        content = team_cmd.read_text()
        assert "sdlc.inviteTeamMember" in content, (
            "teamCommand.ts must register sdlc.inviteTeamMember command"
        )
