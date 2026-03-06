"""
Sprint 213 — Frontend Test Coverage Push + Extension Gate Create
Backend parity tests for Track C (Extension gate create) + Track A/B file existence.

Tests:
  T1-T2: Extension createGateCommand file + sdlc.createGate content
  T3-T4: apiClient.ts has createGate method + POST /api/v1/gates
  T5-T12: Frontend test file existence checks (8 hook + 6 component test files)
  T13: Sprint 213 plan document exists

@sprint 213
@framework SDLC 6.1.1
"""

import os
import pytest

# ─── Paths ────────────────────────────────────────────────────────
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
EXT = os.path.join(ROOT, "vscode-extension", "src")
FE_TESTS = os.path.join(ROOT, "frontend", "src", "__tests__")
DOCS = os.path.join(ROOT, "docs", "04-build", "02-Sprint-Plans")


# ─── Track C: Extension Gate Create ──────────────────────────────

class TestExtensionGateCreate:
    """T1-T4: Extension gate create command parity."""

    def test_create_gate_command_file_exists(self):
        """T1: createGateCommand.ts exists in extension commands."""
        path = os.path.join(EXT, "commands", "createGateCommand.ts")
        assert os.path.isfile(path), f"Missing: {path}"

    def test_create_gate_command_has_sdlc_create_gate(self):
        """T2: createGateCommand.ts registers sdlc.createGate."""
        path = os.path.join(EXT, "commands", "createGateCommand.ts")
        content = open(path).read()
        assert "sdlc.createGate" in content, "Command ID 'sdlc.createGate' not found"

    def test_api_client_has_create_gate_method(self):
        """T3: apiClient.ts exports createGate method."""
        path = os.path.join(EXT, "services", "apiClient.ts")
        content = open(path).read()
        assert "createGate" in content, "createGate method not found in apiClient.ts"

    def test_api_client_posts_to_gates_endpoint(self):
        """T4: createGate calls POST /api/v1/gates."""
        path = os.path.join(EXT, "services", "apiClient.ts")
        content = open(path).read()
        assert "/api/v1/gates" in content, "POST /api/v1/gates endpoint not found"


# ─── Track A: Hook Test Files ────────────────────────────────────

class TestHookTestFiles:
    """T5-T8: Frontend hook test files exist."""

    @pytest.mark.parametrize("hook_name", [
        "useAuth",
        "useProjects",
        "useGates",
        "useEvidence",
        "useTeams",
        "useUserTier",
        "useCodegen",
        "useKillSwitch",
    ])
    def test_hook_test_file_exists(self, hook_name: str):
        """T5-T12: Hook test file exists for each critical hook."""
        path = os.path.join(FE_TESTS, "hooks", f"{hook_name}.test.ts")
        # Some hooks use .tsx extension
        path_tsx = os.path.join(FE_TESTS, "hooks", f"{hook_name}.test.tsx")
        assert os.path.isfile(path) or os.path.isfile(path_tsx), (
            f"Missing hook test: {hook_name}.test.ts(x)"
        )


# ─── Track B: Component Test Files ──────────────────────────────

class TestComponentTestFiles:
    """T9-T14: Frontend component test files exist."""

    @pytest.mark.parametrize("component_name", [
        "UsageWidget",
        "ExportAuditButton",
        "Header",
        "AuthGuard",
        "TierBadge",
        "NotificationCenter",
    ])
    def test_component_test_file_exists(self, component_name: str):
        """T9-T14: Component test file exists for each critical component."""
        path = os.path.join(FE_TESTS, "components", f"{component_name}.test.tsx")
        assert os.path.isfile(path), f"Missing component test: {component_name}.test.tsx"


# ─── Sprint 213 Meta ─────────────────────────────────────────────

class TestSprint213Meta:
    """Sprint 213 plan document and extension registration."""

    def test_sprint_213_plan_exists(self):
        """T15: Sprint 213 plan document exists."""
        path = os.path.join(DOCS, "SPRINT-213-FRONTEND-TEST-PUSH-EXTENSION-GATE.md")
        assert os.path.isfile(path), f"Missing: {path}"

    def test_extension_registers_create_gate(self):
        """T16: extension.ts imports and registers createGateCommand."""
        path = os.path.join(EXT, "extension.ts")
        content = open(path).read()
        assert "createGateCommand" in content, (
            "createGateCommand not imported in extension.ts"
        )
