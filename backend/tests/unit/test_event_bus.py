"""
=========================================================================
Unit Tests - EventBus (Sprint 83)
SDLC Orchestrator - Stage 04 (BUILD)

Version: 1.0.0
Date: January 19, 2026
Status: ACTIVE - Sprint 83 (Dynamic Context & Analytics)
Authority: Backend Lead + CTO Approved
Foundation: Sprint 83 Plan

Purpose:
- Test EventBus pub/sub functionality
- Test async and sync handler support
- Test priority ordering
- Test error isolation

Test Coverage:
1. Event subscription and unsubscription
2. Async handler execution
3. Sync handler execution
4. Priority ordering
5. Error isolation (one handler fails, others continue)
6. Event history

Zero Mock Policy: Real EventBus, real handlers
=========================================================================
"""

import asyncio
import pytest
from datetime import datetime, timezone
from uuid import uuid4

from app.events.event_bus import (
    EventBus,
    EventSubscription,
    EventResult,
    get_event_bus,
    reset_event_bus,
)
from app.events.lifecycle_events import (
    GateStatusChanged,
    SprintChanged,
    ConstraintDetected,
    GateStatus,
    SprintStatus,
    ConstraintSeverity,
    ConstraintType,
)


# =========================================================================
# Fixtures
# =========================================================================


@pytest.fixture
def event_bus():
    """Create fresh EventBus for each test."""
    return EventBus(max_history=100)


@pytest.fixture
def sample_gate_event():
    """Create sample GateStatusChanged event."""
    return GateStatusChanged(
        project_id=uuid4(),
        gate_id="G2",
        gate_name="Design Ready",
        new_status=GateStatus.PASSED,
        previous_status=GateStatus.IN_PROGRESS,
        changed_by=uuid4(),
        reason="All criteria met",
    )


@pytest.fixture
def sample_sprint_event():
    """Create sample SprintChanged event."""
    return SprintChanged(
        project_id=uuid4(),
        sprint_id=uuid4(),
        sprint_name="Sprint 83",
        sprint_number=83,
        new_status=SprintStatus.ACTIVE,
        previous_status=SprintStatus.PLANNING,
        goals=["Dynamic Context Injector", "Analytics API"],
    )


# =========================================================================
# Subscription Tests
# =========================================================================


class TestEventSubscription:
    """Tests for event subscription."""

    def test_subscribe_returns_uuid(self, event_bus):
        """Subscribe returns unique subscriber ID."""

        def handler(event):
            pass

        sub_id = event_bus.subscribe(GateStatusChanged, handler)
        assert sub_id is not None
        assert isinstance(sub_id, type(uuid4()))

    def test_subscribe_multiple_handlers(self, event_bus):
        """Multiple handlers can subscribe to same event type."""
        handlers_called = []

        def handler1(event):
            handlers_called.append("handler1")

        def handler2(event):
            handlers_called.append("handler2")

        event_bus.subscribe(GateStatusChanged, handler1)
        event_bus.subscribe(GateStatusChanged, handler2)

        assert event_bus.get_subscriber_count(GateStatusChanged) == 2

    def test_unsubscribe_removes_handler(self, event_bus):
        """Unsubscribe removes handler."""

        def handler(event):
            pass

        sub_id = event_bus.subscribe(GateStatusChanged, handler)
        assert event_bus.get_subscriber_count(GateStatusChanged) == 1

        removed = event_bus.unsubscribe(GateStatusChanged, sub_id)
        assert removed is True
        assert event_bus.get_subscriber_count(GateStatusChanged) == 0

    def test_unsubscribe_nonexistent_returns_false(self, event_bus):
        """Unsubscribe nonexistent returns False."""
        removed = event_bus.unsubscribe(GateStatusChanged, uuid4())
        assert removed is False

    def test_unsubscribe_all(self, event_bus):
        """Unsubscribe all handlers from event type."""

        def handler1(event):
            pass

        def handler2(event):
            pass

        event_bus.subscribe(GateStatusChanged, handler1)
        event_bus.subscribe(GateStatusChanged, handler2)
        assert event_bus.get_subscriber_count(GateStatusChanged) == 2

        count = event_bus.unsubscribe_all(GateStatusChanged)
        assert count == 2
        assert event_bus.get_subscriber_count(GateStatusChanged) == 0


# =========================================================================
# Async Handler Tests
# =========================================================================


class TestAsyncHandlers:
    """Tests for async handler execution."""

    @pytest.mark.asyncio
    async def test_async_handler_called(self, event_bus, sample_gate_event):
        """Async handler is called on publish."""
        handler_called = []

        async def async_handler(event):
            handler_called.append(event)

        event_bus.subscribe(GateStatusChanged, async_handler)
        result = await event_bus.publish(sample_gate_event)

        assert result.handlers_called == 1
        assert result.handlers_succeeded == 1
        assert result.handlers_failed == 0
        assert len(handler_called) == 1
        assert handler_called[0] == sample_gate_event

    @pytest.mark.asyncio
    async def test_multiple_async_handlers(self, event_bus, sample_gate_event):
        """Multiple async handlers are all called."""
        results = []

        async def handler1(event):
            await asyncio.sleep(0.01)
            results.append("h1")

        async def handler2(event):
            await asyncio.sleep(0.01)
            results.append("h2")

        event_bus.subscribe(GateStatusChanged, handler1)
        event_bus.subscribe(GateStatusChanged, handler2)

        result = await event_bus.publish(sample_gate_event)

        assert result.handlers_called == 2
        assert result.handlers_succeeded == 2
        assert len(results) == 2
        assert "h1" in results
        assert "h2" in results


# =========================================================================
# Sync Handler Tests
# =========================================================================


class TestSyncHandlers:
    """Tests for sync handler execution."""

    @pytest.mark.asyncio
    async def test_sync_handler_called(self, event_bus, sample_gate_event):
        """Sync handler is called on publish."""
        handler_called = []

        def sync_handler(event):
            handler_called.append(event)

        event_bus.subscribe(GateStatusChanged, sync_handler)
        result = await event_bus.publish(sample_gate_event)

        assert result.handlers_called == 1
        assert result.handlers_succeeded == 1
        assert len(handler_called) == 1

    def test_sync_publish(self, event_bus, sample_gate_event):
        """Sync publish calls sync handlers only."""
        sync_called = []
        async_called = []

        def sync_handler(event):
            sync_called.append(event)

        async def async_handler(event):
            async_called.append(event)

        event_bus.subscribe(GateStatusChanged, sync_handler)
        event_bus.subscribe(GateStatusChanged, async_handler)

        result = event_bus.publish_sync(sample_gate_event)

        assert result.handlers_called == 1  # Only sync
        assert len(sync_called) == 1
        assert len(async_called) == 0  # Async skipped


# =========================================================================
# Priority Tests
# =========================================================================


class TestPriorityOrdering:
    """Tests for handler priority ordering."""

    @pytest.mark.asyncio
    async def test_higher_priority_first(self, event_bus, sample_gate_event):
        """Higher priority handlers execute first."""
        order = []

        def low_handler(event):
            order.append("low")

        def high_handler(event):
            order.append("high")

        def medium_handler(event):
            order.append("medium")

        # Subscribe in random order with different priorities
        event_bus.subscribe(GateStatusChanged, low_handler, priority=1)
        event_bus.subscribe(GateStatusChanged, high_handler, priority=10)
        event_bus.subscribe(GateStatusChanged, medium_handler, priority=5)

        await event_bus.publish(sample_gate_event)

        # Should be: high (10), medium (5), low (1)
        assert order == ["high", "medium", "low"]

    @pytest.mark.asyncio
    async def test_same_priority_order_preserved(self, event_bus, sample_gate_event):
        """Same priority handlers maintain subscription order."""
        order = []

        def handler1(event):
            order.append("h1")

        def handler2(event):
            order.append("h2")

        event_bus.subscribe(GateStatusChanged, handler1, priority=5)
        event_bus.subscribe(GateStatusChanged, handler2, priority=5)

        await event_bus.publish(sample_gate_event)

        # Order should be preserved (h1 first since subscribed first)
        assert order == ["h1", "h2"]


# =========================================================================
# Error Isolation Tests
# =========================================================================


class TestErrorIsolation:
    """Tests for error isolation between handlers."""

    @pytest.mark.asyncio
    async def test_error_doesnt_stop_other_handlers(self, event_bus, sample_gate_event):
        """One handler error doesn't stop others."""
        results = []

        def good_handler1(event):
            results.append("good1")

        def bad_handler(event):
            raise ValueError("Intentional error")

        def good_handler2(event):
            results.append("good2")

        event_bus.subscribe(GateStatusChanged, good_handler1, priority=10)
        event_bus.subscribe(GateStatusChanged, bad_handler, priority=5)
        event_bus.subscribe(GateStatusChanged, good_handler2, priority=1)

        result = await event_bus.publish(sample_gate_event)

        assert result.handlers_called == 3
        assert result.handlers_succeeded == 2
        assert result.handlers_failed == 1
        assert len(result.errors) == 1
        assert "ValueError" in result.errors[0][1]

        # Good handlers still executed
        assert "good1" in results
        assert "good2" in results

    @pytest.mark.asyncio
    async def test_async_error_isolation(self, event_bus, sample_gate_event):
        """Async handler errors are isolated."""
        results = []

        async def good_handler(event):
            results.append("good")

        async def bad_handler(event):
            raise RuntimeError("Async error")

        event_bus.subscribe(GateStatusChanged, good_handler, priority=10)
        event_bus.subscribe(GateStatusChanged, bad_handler, priority=5)

        result = await event_bus.publish(sample_gate_event)

        assert result.handlers_succeeded == 1
        assert result.handlers_failed == 1
        assert "good" in results


# =========================================================================
# Event History Tests
# =========================================================================


class TestEventHistory:
    """Tests for event history tracking."""

    @pytest.mark.asyncio
    async def test_events_recorded_in_history(self, event_bus, sample_gate_event):
        """Published events are recorded in history."""

        def handler(event):
            pass

        event_bus.subscribe(GateStatusChanged, handler)
        await event_bus.publish(sample_gate_event)

        history = event_bus.get_history()
        assert len(history) == 1
        assert history[0][1] == sample_gate_event

    @pytest.mark.asyncio
    async def test_history_filter_by_type(self, event_bus, sample_gate_event, sample_sprint_event):
        """History can be filtered by event type."""

        def handler(event):
            pass

        event_bus.subscribe(GateStatusChanged, handler)
        event_bus.subscribe(SprintChanged, handler)

        await event_bus.publish(sample_gate_event)
        await event_bus.publish(sample_sprint_event)

        all_history = event_bus.get_history()
        assert len(all_history) == 2

        gate_history = event_bus.get_history(event_type=GateStatusChanged)
        assert len(gate_history) == 1

    @pytest.mark.asyncio
    async def test_history_respects_max_size(self, sample_gate_event):
        """History respects max_history limit."""
        small_bus = EventBus(max_history=3)

        def handler(event):
            pass

        small_bus.subscribe(GateStatusChanged, handler)

        # Publish 5 events
        for _ in range(5):
            await small_bus.publish(sample_gate_event)

        history = small_bus.get_history()
        assert len(history) == 3  # Only last 3 kept

    def test_clear_history(self, event_bus):
        """Clear history removes all entries."""
        event_bus._history = [("test", "event", "result")]
        assert len(event_bus.get_history()) == 1

        event_bus.clear_history()
        assert len(event_bus.get_history()) == 0


# =========================================================================
# Start/Stop Tests
# =========================================================================


class TestStartStop:
    """Tests for EventBus start/stop."""

    @pytest.mark.asyncio
    async def test_stopped_bus_ignores_events(self, event_bus, sample_gate_event):
        """Stopped bus ignores published events."""
        called = []

        def handler(event):
            called.append(event)

        event_bus.subscribe(GateStatusChanged, handler)
        event_bus.stop()

        result = await event_bus.publish(sample_gate_event)

        assert result.handlers_called == 0
        assert len(called) == 0

    @pytest.mark.asyncio
    async def test_restart_bus(self, event_bus, sample_gate_event):
        """Restarted bus processes events again."""
        called = []

        def handler(event):
            called.append(event)

        event_bus.subscribe(GateStatusChanged, handler)
        event_bus.stop()
        event_bus.start()

        result = await event_bus.publish(sample_gate_event)

        assert result.handlers_called == 1
        assert len(called) == 1


# =========================================================================
# Global EventBus Tests
# =========================================================================


class TestGlobalEventBus:
    """Tests for global EventBus singleton."""

    def test_get_event_bus_returns_singleton(self):
        """get_event_bus returns same instance."""
        reset_event_bus()
        bus1 = get_event_bus()
        bus2 = get_event_bus()
        assert bus1 is bus2

    def test_reset_event_bus(self):
        """reset_event_bus creates new instance."""
        bus1 = get_event_bus()
        reset_event_bus()
        bus2 = get_event_bus()
        assert bus1 is not bus2


# =========================================================================
# Event Types Tests
# =========================================================================


class TestEventTypes:
    """Tests for different event types."""

    @pytest.mark.asyncio
    async def test_gate_status_changed(self, event_bus):
        """GateStatusChanged event properties."""
        received = []

        def handler(event):
            received.append(event)

        event_bus.subscribe(GateStatusChanged, handler)

        event = GateStatusChanged(
            project_id=uuid4(),
            gate_id="G3",
            new_status=GateStatus.PASSED,
        )

        await event_bus.publish(event)

        assert len(received) == 1
        assert received[0].gate_id == "G3"
        assert received[0].new_status == GateStatus.PASSED
        assert received[0].source == "gate-engine"

    @pytest.mark.asyncio
    async def test_constraint_detected(self, event_bus):
        """ConstraintDetected event auto-sets blocking flag."""
        event_critical = ConstraintDetected(
            project_id=uuid4(),
            constraint_type=ConstraintType.SECURITY,
            severity=ConstraintSeverity.CRITICAL,
            title="CVE-2024-12345",
        )

        event_low = ConstraintDetected(
            project_id=uuid4(),
            constraint_type=ConstraintType.QUALITY,
            severity=ConstraintSeverity.LOW,
            title="Missing docstring",
        )

        # Critical should be blocking
        assert event_critical.blocking is True

        # Low should not be blocking
        assert event_low.blocking is False
