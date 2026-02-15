"""
=========================================================================
Isolated Unit Tests for GovernanceModeService
SDLC Orchestrator - Sprint 108

These tests run WITHOUT the full app context for faster feedback.
Run: cd backend && python3 -m pytest tests/unit/services/governance/test_mode_service_isolated.py -v
=========================================================================
"""

import sys
import os
from pathlib import Path

# Add backend/app to path for isolated testing
backend_path = Path(__file__).parent.parent.parent.parent.parent / "app"
sys.path.insert(0, str(backend_path.parent))

import pytest
import asyncio
from uuid import uuid4
from datetime import datetime

# Import the service module
from app.services.governance.mode_service import (
    GovernanceMode,
    GovernanceModeService,
    GovernanceViolation,
    ViolationSeverity,
    EnforcementResult,
    GovernanceModeState,
    RollbackCriteria,
    create_governance_mode_service,
    get_governance_mode_service,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mode_service() -> GovernanceModeService:
    """Create fresh GovernanceModeService for each test."""
    return GovernanceModeService(default_mode=GovernanceMode.WARNING)


@pytest.fixture
def sample_violation() -> GovernanceViolation:
    """Create sample violation for testing."""
    return GovernanceViolation(
        id="v-001",
        rule_id="ownership_required",
        severity=ViolationSeverity.ERROR,
        message="File missing @owner annotation",
        file_path="backend/app/services/example.py",
        line_number=1,
        suggestion="Add @owner annotation to file header",
        cli_command="sdlcctl add-ownership --file example.py",
    )


@pytest.fixture
def critical_violation() -> GovernanceViolation:
    """Create critical violation for testing."""
    return GovernanceViolation(
        id="v-002",
        rule_id="security_vulnerability",
        severity=ViolationSeverity.CRITICAL,
        message="SQL injection vulnerability detected",
        file_path="backend/app/api/users.py",
        line_number=42,
        suggestion="Use parameterized queries",
    )


# ============================================================================
# Test Suite 1: Mode Management
# ============================================================================

class TestModeManagement:
    """Test governance mode get/set operations."""

    def test_mode_001_default_mode_is_warning(self, mode_service: GovernanceModeService):
        """Default mode should be WARNING for safety."""
        assert mode_service.get_mode() == GovernanceMode.WARNING

    def test_mode_002_custom_default_mode(self):
        """Service should accept custom default mode."""
        service = GovernanceModeService(default_mode=GovernanceMode.OFF)
        assert service.get_mode() == GovernanceMode.OFF

    @pytest.mark.asyncio
    async def test_mode_003_set_mode_global(self, mode_service: GovernanceModeService):
        """Should set global governance mode."""
        await mode_service.set_mode(
            mode=GovernanceMode.SOFT,
            changed_by="cto",
            reason="Enable soft enforcement",
        )
        assert mode_service.get_mode() == GovernanceMode.SOFT

    @pytest.mark.asyncio
    async def test_mode_004_set_mode_tracks_history(self, mode_service: GovernanceModeService):
        """Mode change should track previous mode."""
        await mode_service.set_mode(
            mode=GovernanceMode.SOFT,
            changed_by="cto",
            reason="Test",
        )
        state = mode_service.get_state()
        assert state.previous_mode == GovernanceMode.WARNING
        assert state.current_mode == GovernanceMode.SOFT
        assert state.changed_by == "cto"

    @pytest.mark.asyncio
    async def test_mode_005_project_override(self, mode_service: GovernanceModeService):
        """Project-level override should take precedence."""
        project_id = uuid4()

        # Set global mode to WARNING
        await mode_service.set_mode(
            mode=GovernanceMode.WARNING,
            changed_by="system",
            reason="Global default",
        )

        # Set project override to FULL
        await mode_service.set_mode(
            mode=GovernanceMode.FULL,
            changed_by="project_owner",
            reason="Enable full mode for this project",
            project_id=project_id,
        )

        # Global should be WARNING
        assert mode_service.get_mode() == GovernanceMode.WARNING
        # Project should be FULL
        assert mode_service.get_mode(project_id=project_id) == GovernanceMode.FULL


# ============================================================================
# Test Suite 2: Enforcement Logic
# ============================================================================

class TestEnforcementLogic:
    """Test enforcement behavior in different modes."""

    @pytest.mark.asyncio
    async def test_enforce_001_off_mode_allows_all(
        self,
        sample_violation: GovernanceViolation,
    ):
        """OFF mode should allow all violations without categorization."""
        service = GovernanceModeService(default_mode=GovernanceMode.OFF)
        result = await service.enforce(violations=[sample_violation])

        assert result.allowed is True
        assert len(result.blocked_violations) == 0
        assert len(result.warned_violations) == 0

    @pytest.mark.asyncio
    async def test_enforce_002_warning_mode_allows_all(
        self,
        mode_service: GovernanceModeService,
        sample_violation: GovernanceViolation,
        critical_violation: GovernanceViolation,
    ):
        """WARNING mode should allow all, even critical violations."""
        result = await mode_service.enforce(
            violations=[sample_violation, critical_violation]
        )

        assert result.allowed is True
        assert len(result.blocked_violations) == 0
        assert len(result.warned_violations) == 2

    @pytest.mark.asyncio
    async def test_enforce_003_soft_mode_blocks_critical(
        self,
        critical_violation: GovernanceViolation,
    ):
        """SOFT mode should block CRITICAL violations."""
        service = GovernanceModeService(default_mode=GovernanceMode.SOFT)
        result = await service.enforce(violations=[critical_violation])

        assert result.allowed is False
        assert len(result.blocked_violations) == 1
        assert result.blocked_violations[0].severity == ViolationSeverity.CRITICAL

    @pytest.mark.asyncio
    async def test_enforce_004_soft_mode_blocks_error(
        self,
        sample_violation: GovernanceViolation,
    ):
        """SOFT mode should block ERROR violations."""
        service = GovernanceModeService(default_mode=GovernanceMode.SOFT)
        result = await service.enforce(violations=[sample_violation])

        assert result.allowed is False
        assert len(result.blocked_violations) == 1

    @pytest.mark.asyncio
    async def test_enforce_005_soft_mode_warns_warning_severity(self):
        """SOFT mode should warn (not block) WARNING severity."""
        service = GovernanceModeService(default_mode=GovernanceMode.SOFT)
        violation = GovernanceViolation(
            id="v-003",
            rule_id="naming_convention",
            severity=ViolationSeverity.WARNING,
            message="Variable naming doesn't match convention",
        )
        result = await service.enforce(violations=[violation])

        assert result.allowed is True
        assert len(result.blocked_violations) == 0
        assert len(result.warned_violations) == 1

    @pytest.mark.asyncio
    async def test_enforce_006_full_mode_blocks_warning_severity(self):
        """FULL mode should block WARNING severity."""
        service = GovernanceModeService(default_mode=GovernanceMode.FULL)
        violation = GovernanceViolation(
            id="v-004",
            rule_id="naming_convention",
            severity=ViolationSeverity.WARNING,
            message="Variable naming doesn't match convention",
        )
        result = await service.enforce(violations=[violation])

        assert result.allowed is False
        assert len(result.blocked_violations) == 1

    @pytest.mark.asyncio
    async def test_enforce_007_full_mode_allows_info(self):
        """FULL mode should allow INFO severity."""
        service = GovernanceModeService(default_mode=GovernanceMode.FULL)
        violation = GovernanceViolation(
            id="v-005",
            rule_id="style_suggestion",
            severity=ViolationSeverity.INFO,
            message="Consider using list comprehension",
        )
        result = await service.enforce(violations=[violation])

        assert result.allowed is True
        assert len(result.blocked_violations) == 0
        assert len(result.warned_violations) == 1

    @pytest.mark.asyncio
    async def test_enforce_008_empty_violations_allowed(
        self,
        mode_service: GovernanceModeService,
    ):
        """No violations should always be allowed."""
        result = await mode_service.enforce(violations=[])
        assert result.allowed is True
        assert len(result.violations) == 0


# ============================================================================
# Test Suite 3: Vibecoding Index Routing
# ============================================================================

class TestVibecodingRouting:
    """Test Vibecoding Index to routing conversion."""

    @pytest.mark.asyncio
    async def test_routing_001_green_auto_approve(
        self,
        mode_service: GovernanceModeService,
    ):
        """Index 0-30 should route to auto_approve."""
        result = await mode_service.enforce(violations=[], vibecoding_index=25.0)
        assert result.routing == "auto_approve"

    @pytest.mark.asyncio
    async def test_routing_002_yellow_tech_lead(
        self,
        mode_service: GovernanceModeService,
    ):
        """Index 31-60 should route to tech_lead_review."""
        result = await mode_service.enforce(violations=[], vibecoding_index=45.0)
        assert result.routing == "tech_lead_review"

    @pytest.mark.asyncio
    async def test_routing_003_orange_ceo_optional(
        self,
        mode_service: GovernanceModeService,
    ):
        """Index 61-80 should route to ceo_should_review."""
        result = await mode_service.enforce(violations=[], vibecoding_index=70.0)
        assert result.routing == "ceo_should_review"

    @pytest.mark.asyncio
    async def test_routing_004_red_ceo_mandatory(
        self,
        mode_service: GovernanceModeService,
    ):
        """Index 81-100 should route to ceo_must_review."""
        result = await mode_service.enforce(violations=[], vibecoding_index=85.0)
        assert result.routing == "ceo_must_review"

    @pytest.mark.asyncio
    async def test_routing_005_boundary_30(
        self,
        mode_service: GovernanceModeService,
    ):
        """Index exactly 30 should be auto_approve."""
        result = await mode_service.enforce(violations=[], vibecoding_index=30.0)
        assert result.routing == "auto_approve"

    @pytest.mark.asyncio
    async def test_routing_006_boundary_60(
        self,
        mode_service: GovernanceModeService,
    ):
        """Index exactly 60 should be tech_lead_review."""
        result = await mode_service.enforce(violations=[], vibecoding_index=60.0)
        assert result.routing == "tech_lead_review"


# ============================================================================
# Test Suite 4: Rollback & Kill Switch
# ============================================================================

class TestRollbackAndKillSwitch:
    """Test rollback and kill switch functionality."""

    @pytest.mark.asyncio
    async def test_rollback_001_to_warning(self):
        """Rollback should set mode to WARNING."""
        service = GovernanceModeService(default_mode=GovernanceMode.FULL)
        await service.rollback_to_warning(
            triggered_by="cto",
            reason="Emergency rollback",
        )
        assert service.get_mode() == GovernanceMode.WARNING

    @pytest.mark.asyncio
    async def test_rollback_002_tracks_previous(self):
        """Rollback should track previous mode."""
        service = GovernanceModeService(default_mode=GovernanceMode.FULL)
        await service.rollback_to_warning(
            triggered_by="auto_rollback",
            reason="High rejection rate",
        )
        state = service.get_state()
        assert state.previous_mode == GovernanceMode.FULL
        assert state.is_rollback is True

    @pytest.mark.asyncio
    async def test_rollback_003_already_warning(self):
        """Rollback from WARNING should be no-op."""
        service = GovernanceModeService(default_mode=GovernanceMode.WARNING)
        state_before = service.get_state()
        await service.rollback_to_warning(
            triggered_by="system",
            reason="Test",
        )
        state_after = service.get_state()
        assert state_after.current_mode == GovernanceMode.WARNING
        assert state_after.is_rollback is False  # Should not mark as rollback

    @pytest.mark.asyncio
    async def test_kill_switch_001_triggers_rollback(self):
        """Kill switch should trigger rollback to WARNING."""
        service = GovernanceModeService(default_mode=GovernanceMode.FULL)
        await service.kill_switch(
            triggered_by="cto",
            reason="Production incident",
        )
        assert service.get_mode() == GovernanceMode.WARNING
        state = service.get_state()
        assert "KILL_SWITCH" in state.changed_by


# ============================================================================
# Test Suite 5: Metrics & Auto-Rollback
# ============================================================================

class TestMetricsAndAutoRollback:
    """Test metrics tracking and auto-rollback criteria."""

    @pytest.mark.asyncio
    async def test_metrics_001_tracks_evaluations(
        self,
        mode_service: GovernanceModeService,
    ):
        """Service should track total evaluations."""
        await mode_service.enforce(violations=[])
        await mode_service.enforce(violations=[])
        await mode_service.enforce(violations=[])

        state = mode_service.get_state()
        assert state.total_evaluations == 3

    @pytest.mark.asyncio
    async def test_metrics_002_tracks_blocked(self):
        """Service should track blocked count."""
        service = GovernanceModeService(default_mode=GovernanceMode.FULL)
        # Disable auto-rollback to test blocking metrics accurately
        service._state.auto_rollback_enabled = False
        violation = GovernanceViolation(
            id="v-001",
            rule_id="test",
            severity=ViolationSeverity.WARNING,
            message="Test",
        )
        await service.enforce(violations=[violation])
        await service.enforce(violations=[violation])

        state = service.get_state()
        assert state.total_blocked == 2

    @pytest.mark.asyncio
    async def test_metrics_003_rejection_rate(self):
        """Service should calculate rejection rate."""
        service = GovernanceModeService(default_mode=GovernanceMode.FULL)
        # Disable auto-rollback to test rejection rate calculation accurately
        service._state.auto_rollback_enabled = False
        violation = GovernanceViolation(
            id="v-001",
            rule_id="test",
            severity=ViolationSeverity.WARNING,
            message="Test",
        )

        # 2 blocked, 2 passed = 50% rejection rate
        await service.enforce(violations=[violation])
        await service.enforce(violations=[violation])
        await service.enforce(violations=[])
        await service.enforce(violations=[])

        state = service.get_state()
        assert state.rejection_rate() == 0.5

    @pytest.mark.asyncio
    async def test_metrics_004_auto_rollback_on_high_rejection(self):
        """Auto-rollback should trigger on >80% rejection rate via check_and_rollback_if_needed."""
        service = GovernanceModeService(default_mode=GovernanceMode.FULL)
        service._state.auto_rollback_enabled = True

        violation = GovernanceViolation(
            id="v-001",
            rule_id="test",
            severity=ViolationSeverity.WARNING,
            message="Test",
        )

        # Simulate 9 blocked, 1 passed = 90% rejection rate
        for _ in range(9):
            service._state.total_evaluations += 1
            service._state.total_blocked += 1

        # One more enforcement to push evaluations to 10 (minimum sample size)
        await service.enforce(violations=[violation])

        # Explicitly trigger rollback check (enforce is pure — no side effects)
        result = await service.check_and_rollback_if_needed()

        # Should have rolled back to WARNING
        assert result.rollback_triggered is True
        assert service.get_mode() == GovernanceMode.WARNING

    @pytest.mark.asyncio
    async def test_metrics_005_false_positive_tracking(self):
        """Service should track false positives."""
        service = GovernanceModeService(default_mode=GovernanceMode.FULL)
        await service.report_false_positive(
            violation_id="v-001",
            reported_by="developer",
            reason="This is not a real violation",
        )
        state = service.get_state()
        assert state.false_positives_reported == 1


# ============================================================================
# Test Suite 6: Mode Change Listeners
# ============================================================================

class TestModeChangeListeners:
    """Test mode change notification system."""

    @pytest.mark.asyncio
    async def test_listener_001_sync_listener(
        self,
        mode_service: GovernanceModeService,
    ):
        """Sync listener should be called on mode change."""
        listener_called = []

        def listener(old_mode, new_mode, changed_by, reason):
            listener_called.append((old_mode, new_mode, changed_by))

        mode_service.add_mode_change_listener(listener)
        await mode_service.set_mode(
            mode=GovernanceMode.SOFT,
            changed_by="cto",
            reason="Test",
        )

        assert len(listener_called) == 1
        assert listener_called[0] == (GovernanceMode.WARNING, GovernanceMode.SOFT, "cto")

    @pytest.mark.asyncio
    async def test_listener_002_async_listener(
        self,
        mode_service: GovernanceModeService,
    ):
        """Async listener should be called on mode change."""
        listener_called = []

        async def async_listener(old_mode, new_mode, changed_by, reason):
            await asyncio.sleep(0.001)  # Simulate async work
            listener_called.append((old_mode, new_mode))

        mode_service.add_mode_change_listener(async_listener)
        await mode_service.set_mode(
            mode=GovernanceMode.FULL,
            changed_by="system",
            reason="Test",
        )

        assert len(listener_called) == 1


# ============================================================================
# Test Suite 7: Data Structures
# ============================================================================

class TestDataStructures:
    """Test data structure serialization."""

    def test_violation_to_dict(self, sample_violation: GovernanceViolation):
        """Violation should serialize to dict correctly."""
        d = sample_violation.to_dict()
        assert d["id"] == "v-001"
        assert d["severity"] == "error"
        assert d["file_path"] == "backend/app/services/example.py"
        assert "created_at" in d

    @pytest.mark.asyncio
    async def test_enforcement_result_to_dict(
        self,
        mode_service: GovernanceModeService,
        sample_violation: GovernanceViolation,
    ):
        """EnforcementResult should serialize correctly."""
        result = await mode_service.enforce(
            violations=[sample_violation],
            vibecoding_index=45.0,
        )
        d = result.to_dict()
        assert d["allowed"] is True
        assert d["mode"] == "warning"
        assert d["violations_count"] == 1
        assert d["vibecoding_index"] == 45.0
        assert d["routing"] == "tech_lead_review"


# ============================================================================
# Main - Run tests if executed directly
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
