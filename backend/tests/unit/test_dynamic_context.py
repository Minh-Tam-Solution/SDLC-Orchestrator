"""
=========================================================================
Unit Tests - DynamicContextService (Sprint 83)
SDLC Orchestrator - Stage 04 (BUILD)

Version: 1.0.0
Date: January 19, 2026
Status: ACTIVE - Sprint 83 (Dynamic Context & Analytics)
Authority: Backend Lead + CTO Approved
Foundation: Sprint 83 Plan - TRUE MOAT

Purpose:
- Test dynamic AGENTS.md generation
- Test event handler integration
- Test context accumulation
- Test constraint injection

Test Coverage:
1. Context creation and management
2. Gate change handling
3. Sprint change handling
4. Constraint detection and resolution
5. Security scan handling
6. Dynamic section generation
7. Debouncing

Zero Mock Policy: Real EventBus, real handlers, mocked DB
=========================================================================
"""

import asyncio
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.events.event_bus import EventBus, reset_event_bus
from app.events.lifecycle_events import (
    GateStatusChanged,
    SprintChanged,
    ConstraintDetected,
    ConstraintResolved,
    SecurityScanCompleted,
    AgentsMdUpdated,
    GateStatus,
    SprintStatus,
    ConstraintSeverity,
    ConstraintType,
    ScanType,
)
from app.services.dynamic_context_service import (
    DynamicContextService,
    DynamicContextConfig,
    DynamicContext,
    UpdateMode,
    create_dynamic_context_service,
)


# =========================================================================
# Fixtures
# =========================================================================


@pytest.fixture
def event_bus():
    """Create fresh EventBus for each test."""
    reset_event_bus()
    return EventBus(max_history=100)


@pytest.fixture
def mock_db():
    """Create mock database session."""
    db = AsyncMock()
    db.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None)))
    return db


@pytest.fixture
def config():
    """Create test configuration."""
    return DynamicContextConfig(
        update_mode=UpdateMode.DISABLED,  # Disable GitHub push for tests
        auto_update_on_gate_change=True,
        auto_update_on_sprint_change=True,
        auto_update_on_constraint=True,
        debounce_seconds=0.1,  # Fast debounce for tests
    )


@pytest.fixture
def service(mock_db, event_bus, config):
    """Create DynamicContextService with test config."""
    return DynamicContextService(
        db=mock_db,
        github_service=None,
        event_bus=event_bus,
        config=config,
    )


@pytest.fixture
def project_id():
    """Generate project UUID."""
    return uuid4()


# =========================================================================
# Context Management Tests
# =========================================================================


class TestContextManagement:
    """Tests for context creation and management."""

    def test_get_or_create_context_creates_new(self, service, project_id):
        """get_or_create_context creates new context."""
        context = service._get_or_create_context(project_id)

        assert context is not None
        assert isinstance(context, DynamicContext)
        assert context.current_gate == "G0"
        assert context.gate_status == GateStatus.PENDING

    def test_get_or_create_context_returns_existing(self, service, project_id):
        """get_or_create_context returns existing context."""
        context1 = service._get_or_create_context(project_id)
        context1.current_gate = "G2"

        context2 = service._get_or_create_context(project_id)

        assert context1 is context2
        assert context2.current_gate == "G2"

    def test_get_context_returns_none_if_missing(self, service):
        """get_context returns None if no context exists."""
        context = service.get_context(uuid4())
        assert context is None


# =========================================================================
# Gate Change Handler Tests
# =========================================================================


class TestGateChangeHandler:
    """Tests for gate status change handling."""

    @pytest.mark.asyncio
    async def test_gate_change_updates_context(self, service, event_bus, project_id):
        """Gate change event updates context."""
        await service.start()

        event = GateStatusChanged(
            project_id=project_id,
            gate_id="G2",
            gate_name="Design Ready",
            new_status=GateStatus.PASSED,
            previous_status=GateStatus.IN_PROGRESS,
            changed_by=uuid4(),
        )

        await event_bus.publish(event)
        await asyncio.sleep(0.05)  # Let handler execute

        context = service.get_context(project_id)
        assert context is not None
        assert context.current_gate == "G2"
        assert context.gate_status == GateStatus.PASSED
        assert context.gate_passed_at is not None

    @pytest.mark.asyncio
    async def test_gate_failed_updates_context(self, service, event_bus, project_id):
        """Gate failed event updates context without passed_at."""
        await service.start()

        event = GateStatusChanged(
            project_id=project_id,
            gate_id="G3",
            new_status=GateStatus.FAILED,
            previous_status=GateStatus.IN_PROGRESS,
            changed_by=uuid4(),
            reason="Tests failed",
        )

        await event_bus.publish(event)
        await asyncio.sleep(0.05)

        context = service.get_context(project_id)
        assert context.gate_status == GateStatus.FAILED
        assert context.gate_passed_at is None


# =========================================================================
# Sprint Change Handler Tests
# =========================================================================


class TestSprintChangeHandler:
    """Tests for sprint status change handling."""

    @pytest.mark.asyncio
    async def test_sprint_change_updates_context(self, service, event_bus, project_id):
        """Sprint change event updates context."""
        await service.start()

        event = SprintChanged(
            project_id=project_id,
            sprint_id=uuid4(),
            sprint_name="Sprint 83",
            sprint_number=83,
            new_status=SprintStatus.ACTIVE,
            previous_status=SprintStatus.PLANNING,
            goals=["Dynamic Context", "Analytics API"],
        )

        await event_bus.publish(event)
        await asyncio.sleep(0.05)

        context = service.get_context(project_id)
        assert context.current_sprint == "Sprint 83"
        assert context.sprint_number == 83
        assert context.sprint_status == SprintStatus.ACTIVE
        assert len(context.sprint_goals) == 2

    @pytest.mark.asyncio
    async def test_sprint_closed_updates_context(self, service, event_bus, project_id):
        """Sprint closed event updates context."""
        await service.start()

        event = SprintChanged(
            project_id=project_id,
            sprint_id=uuid4(),
            sprint_name="Sprint 82",
            sprint_number=82,
            new_status=SprintStatus.CLOSED,
            previous_status=SprintStatus.REVIEW,
        )

        await event_bus.publish(event)
        await asyncio.sleep(0.05)

        context = service.get_context(project_id)
        assert context.sprint_status == SprintStatus.CLOSED


# =========================================================================
# Constraint Handler Tests
# =========================================================================


class TestConstraintHandler:
    """Tests for constraint detection handling."""

    @pytest.mark.asyncio
    async def test_constraint_detected_adds_to_context(self, service, event_bus, project_id):
        """Constraint detected adds to active constraints."""
        await service.start()

        event = ConstraintDetected(
            project_id=project_id,
            constraint_type=ConstraintType.SECURITY,
            severity=ConstraintSeverity.HIGH,
            title="SQL Injection in auth.py",
            description="User input not sanitized",
            affected_files=["backend/auth.py"],
            blocking=True,
        )

        await event_bus.publish(event)
        await asyncio.sleep(0.05)

        context = service.get_context(project_id)
        assert len(context.active_constraints) == 1
        assert context.active_constraints[0]["title"] == "SQL Injection in auth.py"
        assert len(context.blocking_constraints) == 1

    @pytest.mark.asyncio
    async def test_low_severity_constraint_ignored(self, service, event_bus, project_id):
        """Low severity constraint below threshold is ignored."""
        await service.start()

        event = ConstraintDetected(
            project_id=project_id,
            constraint_type=ConstraintType.QUALITY,
            severity=ConstraintSeverity.INFO,  # Below MEDIUM threshold
            title="Missing docstring",
        )

        await event_bus.publish(event)
        await asyncio.sleep(0.05)

        context = service.get_context(project_id)
        # Should not be added (INFO is below MEDIUM threshold)
        assert context is None or len(context.active_constraints) == 0

    @pytest.mark.asyncio
    async def test_constraint_resolved_removes_from_context(self, service, event_bus, project_id):
        """Constraint resolved removes from context."""
        await service.start()

        constraint_id = uuid4()

        # First detect
        detect_event = ConstraintDetected(
            project_id=project_id,
            constraint_id=constraint_id,
            constraint_type=ConstraintType.SECURITY,
            severity=ConstraintSeverity.HIGH,
            title="CVE-2024-12345",
            blocking=True,
        )
        await event_bus.publish(detect_event)
        await asyncio.sleep(0.05)

        context = service.get_context(project_id)
        assert len(context.active_constraints) == 1
        assert len(context.blocking_constraints) == 1

        # Then resolve
        resolve_event = ConstraintResolved(
            project_id=project_id,
            constraint_id=constraint_id,
            resolved_by=uuid4(),
            resolution="Updated to patched version",
        )
        await event_bus.publish(resolve_event)
        await asyncio.sleep(0.05)

        # Should be removed
        assert len(context.active_constraints) == 0
        assert len(context.blocking_constraints) == 0

    @pytest.mark.asyncio
    async def test_max_constraints_limit(self, service, event_bus, project_id):
        """Max constraints limit is enforced."""
        service.config.max_constraints_in_context = 3
        await service.start()

        # Add 5 constraints
        for i in range(5):
            event = ConstraintDetected(
                project_id=project_id,
                constraint_type=ConstraintType.SECURITY,
                severity=ConstraintSeverity.MEDIUM,
                title=f"Constraint {i}",
            )
            await event_bus.publish(event)
            await asyncio.sleep(0.02)

        context = service.get_context(project_id)
        # Should only keep last 3
        assert len(context.active_constraints) <= 3


# =========================================================================
# Security Scan Handler Tests
# =========================================================================


class TestSecurityScanHandler:
    """Tests for security scan handling."""

    @pytest.mark.asyncio
    async def test_scan_passed_updates_context(self, service, event_bus, project_id):
        """Security scan passed updates context."""
        await service.start()

        event = SecurityScanCompleted(
            project_id=project_id,
            scan_type=ScanType.SAST,
            scanner="semgrep",
            passed=True,
            findings_critical=0,
            findings_high=0,
            findings_medium=2,
        )

        await event_bus.publish(event)
        await asyncio.sleep(0.05)

        context = service.get_context(project_id)
        assert context.last_scan_passed is True
        assert context.last_scan_findings["medium"] == 2

    @pytest.mark.asyncio
    async def test_scan_failed_updates_context(self, service, event_bus, project_id):
        """Security scan failed updates context and triggers update."""
        await service.start()

        event = SecurityScanCompleted(
            project_id=project_id,
            scan_type=ScanType.SAST,
            scanner="semgrep",
            passed=False,
            findings_critical=1,
            findings_high=3,
        )

        await event_bus.publish(event)
        await asyncio.sleep(0.15)  # Wait for debounce

        context = service.get_context(project_id)
        assert context.last_scan_passed is False
        assert context.last_scan_findings["critical"] == 1
        assert context.last_scan_findings["high"] == 3


# =========================================================================
# Dynamic Section Generation Tests
# =========================================================================


class TestDynamicSectionGeneration:
    """Tests for dynamic AGENTS.md section generation."""

    def test_generate_basic_section(self, service, project_id):
        """Generate basic dynamic section."""
        context = service._get_or_create_context(project_id)
        context.current_gate = "G2"
        context.gate_status = GateStatus.PASSED

        section = service._generate_dynamic_section(context)

        assert "## Current Stage" in section
        assert "G2" in section
        assert "PASSED" in section
        assert "✅" in section  # Passed icon

    def test_generate_with_sprint(self, service, project_id):
        """Generate section includes sprint info."""
        context = service._get_or_create_context(project_id)
        context.current_sprint = "Sprint 83"
        context.sprint_number = 83
        context.sprint_status = SprintStatus.ACTIVE
        context.sprint_goals = ["Dynamic Context", "Analytics"]

        section = service._generate_dynamic_section(context)

        assert "## Current Sprint" in section
        assert "Sprint 83" in section
        assert "ACTIVE" in section
        assert "Dynamic Context" in section

    def test_generate_with_blocking_constraints(self, service, project_id):
        """Generate section includes blocking constraints."""
        context = service._get_or_create_context(project_id)
        context.blocking_constraints = [
            {
                "title": "CVE-2024-12345",
                "severity": "CRITICAL",
                "remediation": "Update lodash",
            }
        ]

        section = service._generate_dynamic_section(context)

        assert "## ⛔ BLOCKED" in section
        assert "CVE-2024-12345" in section
        assert "Update lodash" in section

    def test_generate_with_known_issues(self, service, project_id):
        """Generate section includes known issues."""
        context = service._get_or_create_context(project_id)
        context.active_constraints = [
            {
                "title": "Missing tests",
                "severity": "medium",
                "affected_files": ["service.py"],
                "blocking": False,
            }
        ]

        section = service._generate_dynamic_section(context)

        assert "## ⚠️ Known Issues" in section
        assert "Missing tests" in section

    def test_generate_with_failed_scan(self, service, project_id):
        """Generate section includes security alert."""
        context = service._get_or_create_context(project_id)
        context.last_scan_passed = False
        context.last_scan_findings = {"critical": 2, "high": 5, "medium": 10}

        section = service._generate_dynamic_section(context)

        assert "## 🔴 Security Alert" in section
        assert "FAILED" in section
        assert "Critical: 2" in section

    def test_gate_status_icons(self, service):
        """Gate status icons are correct."""
        assert service._get_stage_icon(GateStatus.PASSED) == "✅"
        assert service._get_stage_icon(GateStatus.FAILED) == "❌"
        assert service._get_stage_icon(GateStatus.BLOCKED) == "⛔"
        assert service._get_stage_icon(GateStatus.IN_PROGRESS) == "🔄"
        assert service._get_stage_icon(GateStatus.PENDING) == "⏳"


# =========================================================================
# Debounce Tests
# =========================================================================


class TestDebouncing:
    """Tests for event debouncing."""

    @pytest.mark.asyncio
    async def test_rapid_events_debounced(self, service, event_bus, project_id):
        """Rapid events are debounced into single update."""
        service.config.debounce_seconds = 0.2
        update_count = []

        # Track updates
        original_execute = service._execute_update

        async def track_execute(*args, **kwargs):
            update_count.append(1)
            await original_execute(*args, **kwargs)

        service._execute_update = track_execute
        await service.start()

        # Fire 5 rapid events
        for i in range(5):
            event = GateStatusChanged(
                project_id=project_id,
                gate_id=f"G{i}",
                new_status=GateStatus.IN_PROGRESS,
                changed_by=uuid4(),
            )
            await event_bus.publish(event)
            await asyncio.sleep(0.01)  # Very small gap

        # Wait for debounce to complete
        await asyncio.sleep(0.3)

        # Should have only 1 update (debounced)
        assert len(update_count) == 1


# =========================================================================
# Service Lifecycle Tests
# =========================================================================


class TestServiceLifecycle:
    """Tests for service start/stop."""

    @pytest.mark.asyncio
    async def test_start_subscribes_to_events(self, service, event_bus):
        """Start subscribes to lifecycle events."""
        await service.start()

        assert event_bus.get_subscriber_count(GateStatusChanged) >= 1
        assert event_bus.get_subscriber_count(SprintChanged) >= 1
        assert event_bus.get_subscriber_count(ConstraintDetected) >= 1

    @pytest.mark.asyncio
    async def test_stop_clears_subscriptions(self, service, event_bus):
        """Stop clears subscriptions list."""
        await service.start()
        assert len(service._subscriptions) > 0

        await service.stop()
        assert len(service._subscriptions) == 0


# =========================================================================
# Force Update Tests
# =========================================================================


class TestForceUpdate:
    """Tests for manual force update."""

    @pytest.mark.asyncio
    async def test_force_update_generates_content(self, service, project_id):
        """Force update generates and returns content."""
        # Set up some context
        context = service._get_or_create_context(project_id)
        context.current_gate = "G3"
        context.gate_status = GateStatus.PASSED

        content = await service.force_update(project_id, "Manual test")

        assert "G3" in content
        assert "PASSED" in content


# =========================================================================
# Update Mode Tests
# =========================================================================


class TestUpdateModes:
    """Tests for different update modes."""

    @pytest.mark.asyncio
    async def test_disabled_mode_skips_updates(self, mock_db, event_bus):
        """Disabled mode skips scheduling updates."""
        config = DynamicContextConfig(update_mode=UpdateMode.DISABLED)
        service = DynamicContextService(
            db=mock_db,
            event_bus=event_bus,
            config=config,
        )

        project_id = uuid4()
        await service._schedule_update(project_id, "Test")

        # No pending updates
        assert project_id not in service._pending_updates
