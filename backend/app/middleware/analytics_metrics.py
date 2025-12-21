"""
Analytics Prometheus Metrics - Sprint 41

SDLC Stage: 04 - BUILD
Sprint: 41 - AI Safety Foundation
Framework: SDLC 5.1.1

Purpose:
Expose Prometheus metrics for analytics service monitoring:
1. Circuit breaker state and failures (CTO Condition #2)
2. Event tracking success/failure rates
3. Batch processing performance
4. Retention cleanup metrics

CTO Recommendation: Add circuit breaker monitoring
Reference: CTO Code Review - Sprint 41 Analytics Implementation

Usage:
```python
# In analytics_service.py
from app.middleware.analytics_metrics import (
    analytics_circuit_breaker_state,
    analytics_circuit_breaker_failures_total,
    analytics_events_tracked_total,
)

# Record metrics
analytics_circuit_breaker_state.set(1)  # 0=closed, 1=open, 2=half_open
analytics_circuit_breaker_failures_total.inc()
analytics_events_tracked_total.labels(provider="mixpanel", status="success").inc()
```

Grafana Dashboard:
- Circuit breaker status (single stat)
- Circuit breaker failures over time (graph)
- Event tracking success rate (graph)
- Retention cleanup duration (histogram)

Alerts:
- Circuit breaker open for >10 minutes → PagerDuty
- Event tracking failure rate >5% → Slack
- Retention cleanup duration >5 minutes → Email
"""

from prometheus_client import Counter, Gauge, Histogram


# ============================================================================
# Circuit Breaker Metrics (CTO Condition #2)
# ============================================================================

analytics_circuit_breaker_state = Gauge(
    "analytics_circuit_breaker_state",
    "Analytics circuit breaker state (0=closed, 1=open, 2=half_open)",
    [],
)

analytics_circuit_breaker_failures_total = Counter(
    "analytics_circuit_breaker_failures_total",
    "Total number of analytics circuit breaker failures",
    [],
)

analytics_circuit_breaker_transitions_total = Counter(
    "analytics_circuit_breaker_transitions_total",
    "Total number of circuit breaker state transitions",
    ["from_state", "to_state"],
)

analytics_circuit_breaker_time_open_seconds = Counter(
    "analytics_circuit_breaker_time_open_seconds",
    "Total time circuit breaker has been open (seconds)",
    [],
)


# ============================================================================
# Event Tracking Metrics
# ============================================================================

analytics_events_tracked_total = Counter(
    "analytics_events_tracked_total",
    "Total number of analytics events tracked",
    ["provider", "status"],  # provider: mixpanel|postgresql, status: success|failure
)

analytics_events_batch_size = Histogram(
    "analytics_events_batch_size",
    "Number of events in batch tracking requests",
    [],
    buckets=(1, 5, 10, 25, 50, 100),
)

analytics_event_track_duration_seconds = Histogram(
    "analytics_event_track_duration_seconds",
    "Duration of event tracking operations (seconds)",
    ["provider"],
    buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 2.0),
)


# ============================================================================
# Retention Cleanup Metrics (CTO Condition #3)
# ============================================================================

analytics_retention_cleanup_duration_seconds = Histogram(
    "analytics_retention_cleanup_duration_seconds",
    "Duration of analytics retention cleanup (seconds)",
    [],
    buckets=(1, 5, 10, 30, 60, 120, 300, 600),  # 1s to 10 minutes
)

analytics_retention_cleanup_records_deleted_total = Counter(
    "analytics_retention_cleanup_records_deleted_total",
    "Total number of records deleted by retention cleanup",
    ["table"],  # table: analytics_events|ai_code_events
)

analytics_retention_cleanup_failures_total = Counter(
    "analytics_retention_cleanup_failures_total",
    "Total number of retention cleanup failures",
    ["error_type"],
)

analytics_retention_events_older_than_policy = Gauge(
    "analytics_retention_events_older_than_policy",
    "Number of events older than retention policy (should be cleaned)",
    ["table"],
)


# ============================================================================
# DAU/MAU Metrics
# ============================================================================

analytics_daily_active_users = Gauge(
    "analytics_daily_active_users",
    "Daily Active Users (DAU) count",
    [],
)

analytics_weekly_active_users = Gauge(
    "analytics_weekly_active_users",
    "Weekly Active Users (WAU) count",
    [],
)

analytics_monthly_active_users = Gauge(
    "analytics_monthly_active_users",
    "Monthly Active Users (MAU) count",
    [],
)


# ============================================================================
# AI Safety Metrics
# ============================================================================

analytics_ai_safety_validations_total = Counter(
    "analytics_ai_safety_validations_total",
    "Total number of AI Safety Layer validations",
    ["result", "ai_tool"],  # result: passed|failed|warning
)

analytics_ai_safety_validation_duration_ms = Histogram(
    "analytics_ai_safety_validation_duration_ms",
    "AI Safety Layer validation duration (milliseconds)",
    ["ai_tool"],
    buckets=(100, 500, 1000, 2000, 5000, 10000),
)

analytics_ai_safety_violations_total = Counter(
    "analytics_ai_safety_violations_total",
    "Total number of AI Safety policy violations",
    ["violation_type"],
)


# ============================================================================
# Helper Functions
# ============================================================================


def record_circuit_breaker_state(state_enum):
    """
    Record circuit breaker state change.

    Args:
        state_enum: CircuitState enum value (CLOSED/OPEN/HALF_OPEN)

    Example:
        from app.services.analytics_service import CircuitState
        record_circuit_breaker_state(CircuitState.OPEN)
    """
    state_mapping = {
        "closed": 0,
        "open": 1,
        "half_open": 2,
    }
    analytics_circuit_breaker_state.set(state_mapping.get(state_enum.value, 0))


def record_circuit_breaker_transition(from_state, to_state):
    """
    Record circuit breaker state transition.

    Args:
        from_state: Previous circuit state
        to_state: New circuit state

    Example:
        record_circuit_breaker_transition("closed", "open")
    """
    analytics_circuit_breaker_transitions_total.labels(
        from_state=from_state.value, to_state=to_state.value
    ).inc()


def record_event_tracked(provider: str, success: bool, duration_seconds: float = None):
    """
    Record event tracking attempt.

    Args:
        provider: "mixpanel" or "postgresql"
        success: True if event successfully tracked
        duration_seconds: Optional duration of tracking operation

    Example:
        record_event_tracked("mixpanel", True, 0.123)
    """
    status = "success" if success else "failure"
    analytics_events_tracked_total.labels(provider=provider, status=status).inc()

    if duration_seconds is not None:
        analytics_event_track_duration_seconds.labels(provider=provider).observe(
            duration_seconds
        )


def record_retention_cleanup(
    table: str, deleted_count: int, duration_seconds: float, error: str = None
):
    """
    Record retention cleanup execution.

    Args:
        table: Table name ("analytics_events" or "ai_code_events")
        deleted_count: Number of records deleted
        duration_seconds: Cleanup duration in seconds
        error: Optional error message if cleanup failed

    Example:
        record_retention_cleanup("analytics_events", 12500, 3.2)
    """
    if error:
        analytics_retention_cleanup_failures_total.labels(error_type=error).inc()
    else:
        analytics_retention_cleanup_records_deleted_total.labels(table=table).inc(
            deleted_count
        )

    analytics_retention_cleanup_duration_seconds.observe(duration_seconds)
