"""
=========================================================================
EventBus - Pub/Sub Infrastructure for Lifecycle Events
SDLC Orchestrator - Sprint 83 (Dynamic Context & Analytics)

Version: 1.0.0
Date: January 19, 2026
Status: ACTIVE - Sprint 83 (Pre-Launch Hardening)
Authority: CTO Approved
Framework: SDLC 5.1.3 P7 (Documentation Permanence)

Purpose:
- Decouple event producers from consumers
- Enable dynamic AGENTS.md updates on lifecycle changes
- Support async event handlers for non-blocking operations

Design:
- Type-safe event subscription (by event class)
- Async handlers for I/O operations (GitHub API, file writes)
- Sync handlers for quick in-process updates
- Error isolation (one handler failure doesn't affect others)

TRUE MOAT: This enables "Dynamic AGENTS.md" - the key differentiator
=========================================================================
"""

import asyncio
import logging
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import (
    Any,
    Callable,
    Coroutine,
    Dict,
    List,
    Optional,
    Protocol,
    Type,
    TypeVar,
    Union,
)
from uuid import UUID, uuid4

logger = logging.getLogger(__name__)


# Type definitions
T = TypeVar("T", bound="LifecycleEvent")
SyncHandler = Callable[[Any], None]
AsyncHandler = Callable[[Any], Coroutine[Any, Any, None]]
EventHandler = Union[SyncHandler, AsyncHandler]


class LifecycleEvent(Protocol):
    """Protocol for lifecycle events."""

    event_id: UUID
    timestamp: datetime
    source: str


@dataclass
class EventSubscription:
    """
    Represents a subscription to an event type.

    Attributes:
        handler: The callback function (sync or async)
        is_async: Whether the handler is async
        priority: Higher priority handlers execute first (default 0)
        subscriber_id: Unique ID for this subscription
    """

    handler: EventHandler
    is_async: bool
    priority: int
    subscriber_id: UUID

    def __lt__(self, other: "EventSubscription") -> bool:
        """Sort by priority (descending - higher first)."""
        return self.priority > other.priority


@dataclass
class EventResult:
    """
    Result of publishing an event.

    Attributes:
        event_id: The published event's ID
        event_type: Class name of the event
        handlers_called: Number of handlers invoked
        handlers_succeeded: Number of handlers that completed without error
        handlers_failed: Number of handlers that raised exceptions
        errors: List of (subscriber_id, error_message) tuples
        duration_ms: Total time to process all handlers
    """

    event_id: UUID
    event_type: str
    handlers_called: int
    handlers_succeeded: int
    handlers_failed: int
    errors: List[tuple[UUID, str]]
    duration_ms: float


class EventBus:
    """
    Pub/Sub EventBus for SDLC Orchestrator lifecycle events.

    Features:
    - Type-safe subscriptions (subscribe by event class)
    - Async and sync handler support
    - Priority-based handler ordering
    - Error isolation (failures don't cascade)
    - Event history for debugging

    Usage:
        event_bus = EventBus()

        # Subscribe to events
        event_bus.subscribe(GateStatusChanged, handle_gate_change)
        event_bus.subscribe(SprintChanged, handle_sprint_change, priority=10)

        # Publish events
        await event_bus.publish(GateStatusChanged(
            project_id=project_id,
            new_status=GateStatus.G2_PASSED,
            ...
        ))

    Sprint 83 Implementation:
    - DynamicContextService subscribes to lifecycle events
    - On event, AGENTS.md is regenerated with new context
    - Changes are pushed to GitHub via PR or direct commit
    """

    def __init__(self, max_history: int = 1000):
        """
        Initialize EventBus.

        Args:
            max_history: Maximum number of events to keep in history
        """
        self._subscriptions: Dict[Type, List[EventSubscription]] = defaultdict(list)
        self._history: List[tuple[datetime, Any, EventResult]] = []
        self._max_history = max_history
        self._is_running = True
        logger.info("EventBus initialized (max_history=%d)", max_history)

    def subscribe(
        self,
        event_type: Type[T],
        handler: EventHandler,
        priority: int = 0,
    ) -> UUID:
        """
        Subscribe a handler to an event type.

        Args:
            event_type: The event class to subscribe to
            handler: Callback function (sync or async)
            priority: Higher priority handlers execute first (default 0)

        Returns:
            UUID: Subscription ID (use for unsubscribe)

        Example:
            sub_id = event_bus.subscribe(GateStatusChanged, my_handler, priority=10)
        """
        subscriber_id = uuid4()
        is_async = asyncio.iscoroutinefunction(handler)

        subscription = EventSubscription(
            handler=handler,
            is_async=is_async,
            priority=priority,
            subscriber_id=subscriber_id,
        )

        self._subscriptions[event_type].append(subscription)
        # Keep sorted by priority (descending)
        self._subscriptions[event_type].sort()

        logger.debug(
            "Subscribed handler to %s (id=%s, async=%s, priority=%d)",
            event_type.__name__,
            subscriber_id,
            is_async,
            priority,
        )

        return subscriber_id

    def unsubscribe(self, event_type: Type[T], subscriber_id: UUID) -> bool:
        """
        Unsubscribe a handler from an event type.

        Args:
            event_type: The event class
            subscriber_id: The subscription ID from subscribe()

        Returns:
            bool: True if unsubscribed, False if not found
        """
        subscriptions = self._subscriptions.get(event_type, [])
        original_count = len(subscriptions)

        self._subscriptions[event_type] = [
            s for s in subscriptions if s.subscriber_id != subscriber_id
        ]

        removed = len(self._subscriptions[event_type]) < original_count

        if removed:
            logger.debug(
                "Unsubscribed handler from %s (id=%s)",
                event_type.__name__,
                subscriber_id,
            )

        return removed

    def unsubscribe_all(self, event_type: Type[T]) -> int:
        """
        Unsubscribe all handlers from an event type.

        Args:
            event_type: The event class

        Returns:
            int: Number of handlers unsubscribed
        """
        count = len(self._subscriptions.get(event_type, []))
        self._subscriptions[event_type] = []
        logger.debug("Unsubscribed all handlers from %s (count=%d)", event_type.__name__, count)
        return count

    async def publish(self, event: T) -> EventResult:
        """
        Publish an event to all subscribers.

        Args:
            event: The event instance to publish

        Returns:
            EventResult: Summary of handler execution

        Note:
            - Handlers are called in priority order (highest first)
            - Errors in one handler don't affect others
            - Both sync and async handlers are supported
        """
        if not self._is_running:
            logger.warning("EventBus is stopped, ignoring event: %s", type(event).__name__)
            return EventResult(
                event_id=getattr(event, "event_id", uuid4()),
                event_type=type(event).__name__,
                handlers_called=0,
                handlers_succeeded=0,
                handlers_failed=0,
                errors=[],
                duration_ms=0.0,
            )

        event_type = type(event)
        event_id = getattr(event, "event_id", uuid4())
        subscriptions = self._subscriptions.get(event_type, [])

        start_time = datetime.now(timezone.utc)
        handlers_succeeded = 0
        handlers_failed = 0
        errors: List[tuple[UUID, str]] = []

        logger.info(
            "Publishing event %s (id=%s, handlers=%d)",
            event_type.__name__,
            event_id,
            len(subscriptions),
        )

        for subscription in subscriptions:
            try:
                if subscription.is_async:
                    await subscription.handler(event)
                else:
                    subscription.handler(event)
                handlers_succeeded += 1
            except Exception as e:
                handlers_failed += 1
                error_msg = f"{type(e).__name__}: {str(e)}"
                errors.append((subscription.subscriber_id, error_msg))
                logger.error(
                    "Handler %s failed for event %s: %s",
                    subscription.subscriber_id,
                    event_type.__name__,
                    error_msg,
                    exc_info=True,
                )

        end_time = datetime.now(timezone.utc)
        duration_ms = (end_time - start_time).total_seconds() * 1000

        result = EventResult(
            event_id=event_id,
            event_type=event_type.__name__,
            handlers_called=len(subscriptions),
            handlers_succeeded=handlers_succeeded,
            handlers_failed=handlers_failed,
            errors=errors,
            duration_ms=duration_ms,
        )

        # Add to history
        self._add_to_history(start_time, event, result)

        logger.info(
            "Event %s published (id=%s, succeeded=%d, failed=%d, duration=%.2fms)",
            event_type.__name__,
            event_id,
            handlers_succeeded,
            handlers_failed,
            duration_ms,
        )

        return result

    def publish_sync(self, event: T) -> EventResult:
        """
        Publish an event synchronously (for non-async contexts).

        Args:
            event: The event instance to publish

        Returns:
            EventResult: Summary of handler execution

        Note:
            - Only sync handlers will be called
            - Async handlers will be skipped with a warning
        """
        if not self._is_running:
            logger.warning("EventBus is stopped, ignoring event: %s", type(event).__name__)
            return EventResult(
                event_id=getattr(event, "event_id", uuid4()),
                event_type=type(event).__name__,
                handlers_called=0,
                handlers_succeeded=0,
                handlers_failed=0,
                errors=[],
                duration_ms=0.0,
            )

        event_type = type(event)
        event_id = getattr(event, "event_id", uuid4())
        subscriptions = self._subscriptions.get(event_type, [])

        start_time = datetime.now(timezone.utc)
        handlers_succeeded = 0
        handlers_failed = 0
        handlers_skipped = 0
        errors: List[tuple[UUID, str]] = []

        for subscription in subscriptions:
            if subscription.is_async:
                handlers_skipped += 1
                logger.warning(
                    "Skipping async handler %s in sync publish",
                    subscription.subscriber_id,
                )
                continue

            try:
                subscription.handler(event)
                handlers_succeeded += 1
            except Exception as e:
                handlers_failed += 1
                error_msg = f"{type(e).__name__}: {str(e)}"
                errors.append((subscription.subscriber_id, error_msg))
                logger.error(
                    "Handler %s failed for event %s: %s",
                    subscription.subscriber_id,
                    event_type.__name__,
                    error_msg,
                )

        end_time = datetime.now(timezone.utc)
        duration_ms = (end_time - start_time).total_seconds() * 1000

        result = EventResult(
            event_id=event_id,
            event_type=event_type.__name__,
            handlers_called=len(subscriptions) - handlers_skipped,
            handlers_succeeded=handlers_succeeded,
            handlers_failed=handlers_failed,
            errors=errors,
            duration_ms=duration_ms,
        )

        self._add_to_history(start_time, event, result)

        return result

    def _add_to_history(self, timestamp: datetime, event: Any, result: EventResult) -> None:
        """Add event to history, maintaining max size."""
        self._history.append((timestamp, event, result))
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history :]

    def get_history(
        self,
        event_type: Optional[Type[T]] = None,
        limit: int = 100,
    ) -> List[tuple[datetime, Any, EventResult]]:
        """
        Get event history.

        Args:
            event_type: Filter by event type (optional)
            limit: Maximum entries to return

        Returns:
            List of (timestamp, event, result) tuples
        """
        history = self._history
        if event_type:
            history = [h for h in history if isinstance(h[1], event_type)]
        return history[-limit:]

    def get_subscriber_count(self, event_type: Type[T]) -> int:
        """Get number of subscribers for an event type."""
        return len(self._subscriptions.get(event_type, []))

    def get_all_event_types(self) -> List[Type]:
        """Get all event types with subscribers."""
        return [t for t, subs in self._subscriptions.items() if subs]

    def stop(self) -> None:
        """Stop the event bus (new events will be ignored)."""
        self._is_running = False
        logger.info("EventBus stopped")

    def start(self) -> None:
        """Start the event bus (resume processing events)."""
        self._is_running = True
        logger.info("EventBus started")

    def clear_history(self) -> None:
        """Clear event history."""
        self._history = []
        logger.debug("EventBus history cleared")


# Global EventBus instance (singleton pattern)
_event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """
    Get the global EventBus instance.

    Returns:
        EventBus: The singleton EventBus instance

    Usage:
        from app.events import get_event_bus

        event_bus = get_event_bus()
        await event_bus.publish(MyEvent(...))
    """
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus


def reset_event_bus() -> None:
    """Reset the global EventBus (for testing)."""
    global _event_bus
    _event_bus = None
