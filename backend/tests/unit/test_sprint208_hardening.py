"""
Sprint 208 — Pre-Release Hardening Tests.

Tests cover:
  E1: ROUTE_TIER_TABLE contains /api/v1/magic-link (tier 2)
  E2: ROUTE_TIER_TABLE contains /api/v1/workflows (tier 3)
  E3: billing/ directory deleted
  E4: infrastructure/__init__.py deleted
  E5: browser_agent_service.py deleted
  E6: _execute_create_project exists and is async
  E7: _execute_submit_evidence exists and is async
  E8: _execute_update_sprint exists and is async

Zero Mock Policy: Structural assertions on real production code.
"""

import asyncio
import os
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# E1/E2: Tier gate route coverage (TG-41 fix)
# ---------------------------------------------------------------------------


class TestTierGateRoutes:
    """Verify Sprint 208 route additions to ROUTE_TIER_TABLE."""

    def test_e1_magic_link_route_standard_tier(self):
        """E1: /api/v1/magic-link must be in ROUTE_TIER_TABLE at tier 2 (STANDARD)."""
        from app.middleware.tier_gate import ROUTE_TIER_TABLE

        assert "/api/v1/magic-link" in ROUTE_TIER_TABLE, (
            "TG-41: /api/v1/magic-link missing from ROUTE_TIER_TABLE"
        )
        assert ROUTE_TIER_TABLE["/api/v1/magic-link"] == 2, (
            "TG-41: /api/v1/magic-link must be tier 2 (STANDARD)"
        )

    def test_e2_workflows_route_professional_tier(self):
        """E2: /api/v1/workflows must be in ROUTE_TIER_TABLE at tier 3 (PROFESSIONAL)."""
        from app.middleware.tier_gate import ROUTE_TIER_TABLE

        assert "/api/v1/workflows" in ROUTE_TIER_TABLE, (
            "TG-41: /api/v1/workflows missing from ROUTE_TIER_TABLE"
        )
        assert ROUTE_TIER_TABLE["/api/v1/workflows"] == 3, (
            "TG-41: /api/v1/workflows must be tier 3 (PROFESSIONAL)"
        )


# ---------------------------------------------------------------------------
# E3/E4/E5: Dead code deletion verification
# ---------------------------------------------------------------------------


class TestDeadCodeDeletion:
    """Verify Sprint 208 dead code cleanup."""

    BACKEND_SERVICES = Path(__file__).resolve().parents[2] / "app" / "services"

    def test_e3_billing_directory_deleted(self):
        """E3: billing/ directory must not exist (empty, no .py files)."""
        billing_dir = self.BACKEND_SERVICES / "billing"
        if billing_dir.exists():
            py_files = list(billing_dir.glob("*.py"))
            assert len(py_files) == 0, (
                f"billing/ still contains Python files: {py_files}"
            )

    def test_e4_infrastructure_init_deleted(self):
        """E4: infrastructure/__init__.py must not exist (broken import)."""
        infra_init = self.BACKEND_SERVICES / "infrastructure" / "__init__.py"
        assert not infra_init.exists(), (
            "infrastructure/__init__.py still exists — broken MinioService import"
        )

    def test_e5_browser_agent_service_deleted(self):
        """E5: browser_agent_service.py must not exist (0 references)."""
        browser_svc = self.BACKEND_SERVICES / "browser_agent_service.py"
        assert not browser_svc.exists(), (
            "browser_agent_service.py still exists — 0 references in codebase"
        )


# ---------------------------------------------------------------------------
# E6/E7/E8: Stub command implementations exist
# ---------------------------------------------------------------------------


class TestStubCommandImplementations:
    """Verify Sprint 208 stub commands replaced with real implementations."""

    def test_e6_execute_create_project_exists(self):
        """E6: _execute_create_project must exist as async function."""
        from app.services.agent_bridge.governance_action_handler import (
            _execute_create_project,
        )
        assert asyncio.iscoroutinefunction(_execute_create_project), (
            "_execute_create_project must be an async function"
        )

    def test_e7_execute_submit_evidence_exists(self):
        """E7: _execute_submit_evidence must exist as async function."""
        from app.services.agent_bridge.governance_action_handler import (
            _execute_submit_evidence,
        )
        assert asyncio.iscoroutinefunction(_execute_submit_evidence), (
            "_execute_submit_evidence must be an async function"
        )

    def test_e8_execute_update_sprint_exists(self):
        """E8: _execute_update_sprint must exist as async function."""
        from app.services.agent_bridge.governance_action_handler import (
            _execute_update_sprint,
        )
        assert asyncio.iscoroutinefunction(_execute_update_sprint), (
            "_execute_update_sprint must be an async function"
        )
