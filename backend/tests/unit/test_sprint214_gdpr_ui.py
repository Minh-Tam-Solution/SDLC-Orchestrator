"""
=========================================================================
Sprint 214 — GDPR/Data Residency UI + Compliance Dashboard + Extension Commands
Test Suite

Validates:
  A) GDPR + Data Residency frontend files exist with correct content
  B) Compliance dashboard enablement (sidebar, overview page, FF_COMPLIANCE)
  C) Extension exportAudit + closeSprint commands registered
  D) Combined Sprint 209-214 regression (file existence)

SDLC 6.1.1 — Sprint 214 Track D
Authority: CTO Approved
Zero Mock Policy: 100% file-based validation
=========================================================================
"""

from __future__ import annotations

import os
import re

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))


def _read(path: str) -> str:
    """Read a file relative to project root, return empty string if missing."""
    full = os.path.join(ROOT, path)
    if not os.path.isfile(full):
        return ""
    with open(full, encoding="utf-8") as f:
        return f.read()


def _exists(path: str) -> bool:
    return os.path.isfile(os.path.join(ROOT, path))


# =========================================================================
# Track A — GDPR + Data Residency frontend pages + hooks
# =========================================================================

class TestTrackA_GdprFrontend:
    """Validate GDPR and Data Residency frontend files."""

    def test_use_gdpr_hook_exists(self):
        assert _exists("frontend/src/hooks/useGdpr.ts")

    def test_use_gdpr_hook_has_key_factory(self):
        content = _read("frontend/src/hooks/useGdpr.ts")
        assert "gdprKeys" in content
        assert "dsarList" in content
        assert "exportSummary" in content
        assert "consents" in content

    def test_use_gdpr_hook_has_mutations(self):
        content = _read("frontend/src/hooks/useGdpr.ts")
        assert "useCreateDsar" in content
        assert "useRecordConsent" in content
        assert "useFullDataExport" in content

    def test_use_data_residency_hook_exists(self):
        assert _exists("frontend/src/hooks/useDataResidency.ts")

    def test_use_data_residency_hook_has_key_factory(self):
        content = _read("frontend/src/hooks/useDataResidency.ts")
        assert "dataResidencyKeys" in content
        assert "regions" in content
        assert "projectRegion" in content

    def test_use_data_residency_hook_has_mutation(self):
        content = _read("frontend/src/hooks/useDataResidency.ts")
        assert "useUpdateProjectRegion" in content

    def test_gdpr_page_exists(self):
        assert _exists("frontend/src/app/app/gdpr/page.tsx")

    def test_gdpr_page_has_locked_feature(self):
        content = _read("frontend/src/app/app/gdpr/page.tsx")
        assert "LockedFeature" in content
        assert 'requiredTier="ENTERPRISE"' in content

    def test_gdpr_page_has_dsar_section(self):
        content = _read("frontend/src/app/app/gdpr/page.tsx")
        assert "DSARSection" in content or "useDsarList" in content

    def test_gdpr_page_has_consent_section(self):
        content = _read("frontend/src/app/app/gdpr/page.tsx")
        assert "ConsentSection" in content or "useActiveConsents" in content

    def test_data_residency_page_exists(self):
        assert _exists("frontend/src/app/app/data-residency/page.tsx")

    def test_data_residency_page_has_locked_feature(self):
        content = _read("frontend/src/app/app/data-residency/page.tsx")
        assert "LockedFeature" in content
        assert 'requiredTier="ENTERPRISE"' in content

    def test_data_residency_page_has_region_selector(self):
        content = _read("frontend/src/app/app/data-residency/page.tsx")
        assert "useAvailableRegions" in content
        assert "useProjectRegion" in content


# =========================================================================
# Track B — Compliance Dashboard Enablement
# =========================================================================

class TestTrackB_ComplianceDashboard:
    """Validate compliance dashboard enablement."""

    def test_ff_compliance_true_in_env_example(self):
        content = _read("frontend/.env.example")
        # Should be true (Sprint 214 enablement)
        assert re.search(r"NEXT_PUBLIC_FF_COMPLIANCE\s*=\s*true", content), (
            "FF_COMPLIANCE should be true in .env.example"
        )

    def test_sidebar_has_gdpr_nav_item(self):
        content = _read("frontend/src/components/dashboard/Sidebar.tsx")
        assert "/app/gdpr" in content, "Sidebar should have GDPR nav item"

    def test_sidebar_has_data_residency_nav_item(self):
        content = _read("frontend/src/components/dashboard/Sidebar.tsx")
        assert "/app/data-residency" in content, "Sidebar should have Data Residency nav item"

    def test_sidebar_has_compliance_nav_item(self):
        content = _read("frontend/src/components/dashboard/Sidebar.tsx")
        assert "/app/compliance" in content, "Sidebar should have Compliance overview nav item"

    def test_compliance_overview_has_gdpr_card(self):
        content = _read("frontend/src/app/app/compliance/page.tsx")
        assert "GDPR" in content
        assert "/app/gdpr" in content

    def test_compliance_overview_has_data_residency_card(self):
        content = _read("frontend/src/app/app/compliance/page.tsx")
        assert "Data Residency" in content
        assert "/app/data-residency" in content

    def test_compliance_overview_no_dead_nist_link(self):
        content = _read("frontend/src/app/app/compliance/page.tsx")
        # NIST AI RMF was removed Sprint 190 — should not appear
        assert "NIST_AI_RMF" not in content, "Dead NIST AI RMF reference should be removed"


# =========================================================================
# Track C — Extension Commands
# =========================================================================

class TestTrackC_ExtensionCommands:
    """Validate extension exportAudit and closeSprint commands."""

    def test_export_audit_command_exists(self):
        assert _exists("vscode-extension/src/commands/exportAuditCommand.ts")

    def test_export_audit_command_has_register(self):
        content = _read("vscode-extension/src/commands/exportAuditCommand.ts")
        assert "registerExportAuditCommand" in content
        assert "sdlc.exportAudit" in content

    def test_export_audit_handles_binary(self):
        content = _read("vscode-extension/src/commands/exportAuditCommand.ts")
        # Should use exportAudit from apiClient (which returns ArrayBuffer)
        assert "exportAudit" in content

    def test_close_sprint_command_exists(self):
        assert _exists("vscode-extension/src/commands/closeSprintCommand.ts")

    def test_close_sprint_command_has_register(self):
        content = _read("vscode-extension/src/commands/closeSprintCommand.ts")
        assert "registerCloseSprintCommand" in content
        assert "sdlc.closeSprint" in content

    def test_close_sprint_triggers_gate_refresh(self):
        content = _read("vscode-extension/src/commands/closeSprintCommand.ts")
        assert "refreshGates" in content

    def test_api_client_has_export_audit_method(self):
        content = _read("vscode-extension/src/services/apiClient.ts")
        assert "exportAudit(" in content
        assert "arrayBuffer" in content

    def test_api_client_has_get_project_sprints(self):
        content = _read("vscode-extension/src/services/apiClient.ts")
        assert "getProjectSprints(" in content

    def test_api_client_has_close_sprint_gate(self):
        content = _read("vscode-extension/src/services/apiClient.ts")
        assert "closeSprintGate(" in content

    def test_extension_registers_export_audit(self):
        content = _read("vscode-extension/src/extension.ts")
        assert "registerExportAuditCommand" in content

    def test_extension_registers_close_sprint(self):
        content = _read("vscode-extension/src/extension.ts")
        assert "registerCloseSprintCommand" in content


# =========================================================================
# Track D — Combined Sprint 209-214 Regression
# =========================================================================

class TestTrackD_Regression:
    """Verify key files from Sprint 209-214 still exist."""

    # Sprint 210 — P0 enterprise critical fixes
    def test_sprint210_test_exists(self):
        assert _exists("backend/tests/unit/test_sprint210_p0_fixes.py")

    # Sprint 211 — ENT feature parity
    def test_sprint211_test_exists(self):
        assert _exists("backend/tests/unit/test_sprint211_ent_features.py")

    # Sprint 211 — Audit export backend
    def test_audit_export_route_exists(self):
        assert _exists("backend/app/api/routes/audit_export.py")

    # Sprint 212 — Cross-interface parity
    def test_sprint212_test_exists(self):
        assert _exists("backend/tests/unit/test_sprint212_parity.py")

    # Sprint 213 — Frontend tests + Extension gate command
    def test_sprint213_test_exists(self):
        assert _exists("backend/tests/unit/test_sprint213_ext_gate.py")

    def test_sprint213_create_gate_command_exists(self):
        assert _exists("vscode-extension/src/commands/createGateCommand.ts")

    # Sprint 213 — Frontend hook tests
    def test_sprint213_hook_tests_exist(self):
        hooks_dir = os.path.join(ROOT, "frontend/src/__tests__/hooks")
        assert os.path.isdir(hooks_dir), "Hook tests directory should exist"
        hook_files = [f for f in os.listdir(hooks_dir) if f.endswith(".test.ts") or f.endswith(".test.tsx")]
        assert len(hook_files) >= 8, f"Expected 8+ hook test files, found {len(hook_files)}"

    # Sprint 213 — Frontend component tests
    def test_sprint213_component_tests_exist(self):
        comp_dir = os.path.join(ROOT, "frontend/src/__tests__/components")
        assert os.path.isdir(comp_dir), "Component tests directory should exist"
        comp_files = [f for f in os.listdir(comp_dir) if f.endswith(".test.tsx")]
        assert len(comp_files) >= 5, f"Expected 5+ component test files, found {len(comp_files)}"

    # Sprint 214 plan document
    def test_sprint214_plan_exists(self):
        assert _exists("docs/04-build/02-Sprint-Plans/SPRINT-214-GDPR-UI-COMPLIANCE-EXTENSION.md")
