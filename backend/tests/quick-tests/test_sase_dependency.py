"""
SASE Anti-Regression Test — Sprint 190

Verify that sase_generation_service.py remains importable after cleanup.
This is a blocker: vcr_service.py and crp_service.py depend on it.

Sprint: 190 — Conversation-First Cleanup
Framework: SDLC 6.1.0
"""

import pytest


class TestSaseDependencyIntact:
    """Ensure SASE generation service survives Sprint 190 cleanup."""

    def test_sase_generation_service_importable(self):
        """sase_generation_service must remain importable (vcr/crp dependency)."""
        from app.services.sase_generation_service import (
            create_sase_generation_service,
        )
        assert callable(create_sase_generation_service)

    def test_vcr_service_importable(self):
        """vcr_service must remain importable (uses sase_generation_service)."""
        from app.services.vcr_service import VCRService
        assert VCRService is not None

    def test_crp_service_importable(self):
        """crp_service must remain importable (uses sase_generation_service)."""
        from app.services.crp_service import CRPService
        assert CRPService is not None

    def test_context_authority_v2_importable(self):
        """context_authority_v2 must remain importable (uses v1 dependency)."""
        from app.api.routes.context_authority_v2 import router
        assert router is not None

    def test_analytics_v2_importable(self):
        """analytics_v2 must remain importable."""
        from app.api.routes.analytics_v2 import router
        assert router is not None
