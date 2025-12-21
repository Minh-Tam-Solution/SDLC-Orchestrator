"""
Circuit Breaker Pattern - AI Detection Resilience

SDLC Stage: 04 - BUILD
Sprint: 42 - AI Detection & Validation Pipeline
Framework: SDLC 5.1.1
CTO P2: Circuit Breaker for External Tools

Purpose:
Implement circuit breaker pattern to handle failures gracefully
when external services (GitHub API, future AI APIs) are unavailable.

States:
- CLOSED: Normal operation, requests pass through
- OPEN: Circuit tripped, requests fail fast
- HALF_OPEN: Testing if service recovered

Configuration:
- FAILURE_THRESHOLD: Number of failures before opening circuit (default: 5)
- RECOVERY_TIMEOUT: Seconds before attempting recovery (default: 30)
- SUCCESS_THRESHOLD: Successes needed to close circuit (default: 3)

Usage:
    from app.services.ai_detection.circuit_breaker import circuit_breaker

    @circuit_breaker.protected
    async def call_external_api():
        return await external_api.fetch()

    # Or use as context manager
    async with circuit_breaker:
        result = await external_api.fetch()
"""

import asyncio
import logging
import os
import time
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)


class CircuitState(str, Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing fast
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""

    # Number of failures before opening circuit
    failure_threshold: int = field(
        default_factory=lambda: int(
            os.getenv("CIRCUIT_BREAKER_FAILURE_THRESHOLD", "5")
        )
    )

    # Seconds before attempting recovery
    recovery_timeout: float = field(
        default_factory=lambda: float(
            os.getenv("CIRCUIT_BREAKER_RECOVERY_TIMEOUT", "30.0")
        )
    )

    # Successes needed to close circuit from half-open
    success_threshold: int = field(
        default_factory=lambda: int(
            os.getenv("CIRCUIT_BREAKER_SUCCESS_THRESHOLD", "3")
        )
    )

    # Enable/disable circuit breaker
    enabled: bool = field(
        default_factory=lambda: os.getenv("CIRCUIT_BREAKER_ENABLED", "true").lower()
        == "true"
    )


@dataclass
class CircuitBreakerStats:
    """Statistics for circuit breaker monitoring."""

    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: Optional[float] = None
    last_state_change: float = field(default_factory=time.time)
    total_requests: int = 0
    total_failures: int = 0
    total_successes: int = 0
    total_rejections: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for monitoring."""
        return {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": self.last_failure_time,
            "last_state_change": self.last_state_change,
            "total_requests": self.total_requests,
            "total_failures": self.total_failures,
            "total_successes": self.total_successes,
            "total_rejections": self.total_rejections,
            "uptime_seconds": time.time() - self.last_state_change,
        }


class CircuitBreakerError(Exception):
    """Raised when circuit is open and request is rejected."""

    def __init__(self, message: str, stats: CircuitBreakerStats):
        super().__init__(message)
        self.stats = stats


class CircuitBreaker:
    """
    Circuit breaker implementation for resilient external API calls.

    Usage:
        breaker = CircuitBreaker(name="github_api")

        @breaker.protected
        async def fetch_pr_data(pr_id: str):
            return await github_api.get_pr(pr_id)

        # Or use decorator with custom error handler
        @breaker.protected(fallback=lambda: {"error": "service unavailable"})
        async def fetch_with_fallback():
            return await external_service.fetch()
    """

    def __init__(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None,
    ):
        """
        Initialize circuit breaker.

        Args:
            name: Identifier for this circuit breaker (for logging/metrics)
            config: Optional configuration override
        """
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.stats = CircuitBreakerStats()
        self._lock = asyncio.Lock()

    @property
    def state(self) -> CircuitState:
        """Get current circuit state."""
        return self.stats.state

    @property
    def is_closed(self) -> bool:
        """Check if circuit is closed (normal operation)."""
        return self.stats.state == CircuitState.CLOSED

    @property
    def is_open(self) -> bool:
        """Check if circuit is open (failing fast)."""
        return self.stats.state == CircuitState.OPEN

    async def _should_attempt_recovery(self) -> bool:
        """Check if enough time has passed to attempt recovery."""
        if self.stats.state != CircuitState.OPEN:
            return False

        if self.stats.last_failure_time is None:
            return True

        elapsed = time.time() - self.stats.last_failure_time
        return elapsed >= self.config.recovery_timeout

    async def _transition_to(self, new_state: CircuitState) -> None:
        """Transition to a new state with logging."""
        old_state = self.stats.state
        self.stats.state = new_state
        self.stats.last_state_change = time.time()

        if new_state == CircuitState.CLOSED:
            self.stats.failure_count = 0
            self.stats.success_count = 0
        elif new_state == CircuitState.HALF_OPEN:
            self.stats.success_count = 0

        logger.info(
            f"Circuit breaker '{self.name}' state change: {old_state.value} -> {new_state.value}",
            extra={
                "circuit_breaker": self.name,
                "old_state": old_state.value,
                "new_state": new_state.value,
                "stats": self.stats.to_dict(),
            },
        )

    async def record_success(self) -> None:
        """Record a successful call."""
        async with self._lock:
            self.stats.total_successes += 1
            self.stats.success_count += 1

            if self.stats.state == CircuitState.HALF_OPEN:
                if self.stats.success_count >= self.config.success_threshold:
                    await self._transition_to(CircuitState.CLOSED)

    async def record_failure(self, error: Exception) -> None:
        """Record a failed call."""
        async with self._lock:
            self.stats.total_failures += 1
            self.stats.failure_count += 1
            self.stats.last_failure_time = time.time()

            logger.warning(
                f"Circuit breaker '{self.name}' recorded failure: {error}",
                extra={
                    "circuit_breaker": self.name,
                    "error": str(error),
                    "failure_count": self.stats.failure_count,
                },
            )

            if self.stats.state == CircuitState.HALF_OPEN:
                # Any failure in half-open goes back to open
                await self._transition_to(CircuitState.OPEN)
            elif self.stats.state == CircuitState.CLOSED:
                if self.stats.failure_count >= self.config.failure_threshold:
                    await self._transition_to(CircuitState.OPEN)

    async def can_execute(self) -> bool:
        """Check if a request can be executed."""
        if not self.config.enabled:
            return True

        async with self._lock:
            self.stats.total_requests += 1

            if self.stats.state == CircuitState.CLOSED:
                return True

            if self.stats.state == CircuitState.OPEN:
                if await self._should_attempt_recovery():
                    await self._transition_to(CircuitState.HALF_OPEN)
                    return True
                else:
                    self.stats.total_rejections += 1
                    return False

            # HALF_OPEN: allow request through for testing
            return True

    async def execute(
        self,
        func: Callable,
        *args,
        fallback: Optional[Callable] = None,
        **kwargs,
    ) -> Any:
        """
        Execute a function with circuit breaker protection.

        Args:
            func: Async function to execute
            *args: Function arguments
            fallback: Optional fallback function if circuit is open
            **kwargs: Function keyword arguments

        Returns:
            Function result or fallback result

        Raises:
            CircuitBreakerError: If circuit is open and no fallback provided
        """
        if not await self.can_execute():
            if fallback:
                logger.info(
                    f"Circuit breaker '{self.name}' using fallback",
                    extra={"circuit_breaker": self.name},
                )
                if asyncio.iscoroutinefunction(fallback):
                    return await fallback()
                return fallback()

            raise CircuitBreakerError(
                f"Circuit breaker '{self.name}' is OPEN - request rejected",
                self.stats,
            )

        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            await self.record_success()
            return result

        except Exception as e:
            await self.record_failure(e)
            raise

    def protected(
        self,
        fallback: Optional[Callable] = None,
    ) -> Callable:
        """
        Decorator to protect a function with circuit breaker.

        Args:
            fallback: Optional fallback function

        Returns:
            Decorated function

        Usage:
            @circuit_breaker.protected
            async def my_function():
                pass

            @circuit_breaker.protected(fallback=lambda: "default")
            async def my_function_with_fallback():
                pass
        """

        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                return await self.execute(func, *args, fallback=fallback, **kwargs)

            return wrapper

        return decorator

    async def __aenter__(self):
        """Async context manager entry."""
        if not await self.can_execute():
            raise CircuitBreakerError(
                f"Circuit breaker '{self.name}' is OPEN",
                self.stats,
            )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if exc_type is None:
            await self.record_success()
        else:
            await self.record_failure(exc_val)
        return False

    def get_stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics."""
        return {
            "name": self.name,
            "config": {
                "failure_threshold": self.config.failure_threshold,
                "recovery_timeout": self.config.recovery_timeout,
                "success_threshold": self.config.success_threshold,
                "enabled": self.config.enabled,
            },
            "stats": self.stats.to_dict(),
        }

    async def reset(self) -> None:
        """Reset circuit breaker to initial state."""
        async with self._lock:
            self.stats = CircuitBreakerStats()
            logger.info(
                f"Circuit breaker '{self.name}' reset",
                extra={"circuit_breaker": self.name},
            )


# Pre-configured circuit breakers for common services
github_api_breaker = CircuitBreaker(name="github_api")
external_ai_breaker = CircuitBreaker(name="external_ai")


def get_all_circuit_breaker_stats() -> Dict[str, Any]:
    """Get statistics for all circuit breakers."""
    return {
        "github_api": github_api_breaker.get_stats(),
        "external_ai": external_ai_breaker.get_stats(),
    }
