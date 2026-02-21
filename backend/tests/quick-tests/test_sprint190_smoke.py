"""
Sprint 190 Smoke Tests — Post-Cleanup Verification

Updated Sprint 191: Removed deprecated route stub tests (deprecated_routes.py
deleted — 1-sprint 410 grace period expired). Tests now verify:
1. App imports cleanly (no broken dependencies)
2. Active routes (gates, evidence, OTT) still registered

Sprint: 190 — Conversation-First Cleanup (updated Sprint 191)
Framework: SDLC 6.1.0

NOTE: Uses import-based verification (no TestClient) to avoid
lifespan event issues with Redis/DB in quick-test environment.
"""

class TestSprint190AppImport:
    """Verify the app imports cleanly after cleanup."""

    def test_app_module_importable(self):
        """app.main should import without errors after Sprint 190 cleanup."""
        from app.main import app
        assert app is not None

    def test_app_has_routes(self):
        """App should have routes registered after cleanup."""
        from app.main import app
        routes = [r for r in app.routes if hasattr(r, "path")]
        assert len(routes) > 100, (
            f"Expected >100 routes after cleanup, got {len(routes)}"
        )


# Sprint 191: TestSprint190DeprecatedRouteStub removed.
# deprecated_routes.py was deleted (1-sprint 410 grace period expired).
# Deprecated endpoints now return FastAPI default 404.


class TestSprint190ActiveRoutes:
    """Verify active routes are still registered after cleanup."""

    def test_core_admin_routes_registered(self):
        """Core admin routes must survive cleanup."""
        from app.main import app
        registered_paths = [
            r.path for r in app.routes if hasattr(r, "path")
        ]

        core_prefixes = [
            "/api/v1/gates",
            "/api/v1/evidence",
            "/api/v1/projects",
            "/api/v1/teams",
            "/api/v1/auth",
        ]

        for prefix in core_prefixes:
            assert any(prefix in p for p in registered_paths), (
                f"Core admin route '{prefix}' missing after cleanup"
            )

    def test_enterprise_routes_registered(self):
        """Enterprise routes (Sprint 183-188) must survive cleanup."""
        from app.main import app
        registered_paths = [
            r.path for r in app.routes if hasattr(r, "path")
        ]

        enterprise_prefixes = [
            "/api/v1/enterprise/sso",
            "/api/v1/jira",
            "/api/v1/enterprise/audit",
            "/api/v1/data-residency",
        ]

        for prefix in enterprise_prefixes:
            assert any(prefix in p for p in registered_paths), (
                f"Enterprise route '{prefix}' missing after cleanup"
            )

    def test_sprint189_routes_registered(self):
        """Sprint 189 routes (OTT channels, agent-team) must survive cleanup."""
        from app.main import app
        registered_paths = [
            r.path for r in app.routes if hasattr(r, "path")
        ]

        sprint189_prefixes = [
            "/api/v1/channels",
            "/api/v1/agent-team",
        ]

        for prefix in sprint189_prefixes:
            assert any(prefix in p for p in registered_paths), (
                f"Sprint 189 route '{prefix}' missing after cleanup"
            )

    def test_analytics_v2_survives_v1_deletion(self):
        """analytics_v2 routes must survive v1 deletion."""
        from app.main import app
        registered_paths = [
            r.path for r in app.routes if hasattr(r, "path")
        ]
        assert any("/api/v1/analytics" in p for p in registered_paths)

    def test_context_authority_v2_survives_v1_deletion(self):
        """context_authority_v2 routes must survive v1 route deletion."""
        from app.main import app
        registered_paths = [
            r.path for r in app.routes if hasattr(r, "path")
        ]
        assert any("/api/v1/context-authority" in p for p in registered_paths)
