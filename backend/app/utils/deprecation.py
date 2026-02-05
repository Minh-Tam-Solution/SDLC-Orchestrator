"""
=========================================================================
API Deprecation Utilities - Sunset Headers & Migration Support
SDLC Orchestrator - Sprint 147 (Spring Cleaning)

Version: 1.1.0
Date: February 25, 2026
Status: ACTIVE
Authority: CTO Approved
Framework: SDLC 6.0.3 API Deprecation Policy

Features:
- Sunset headers (RFC 8594)
- Deprecation warning headers
- Usage logging for migration tracking
- Compatibility layer support
- Telemetry tracking for deprecation monitoring (Sprint 150)

Deprecation Policy:
- Public API: 180 days notice
- Internal API: 30 days notice
=========================================================================
"""

import asyncio
import functools
import logging
from datetime import datetime, date
from typing import Any, Callable, Dict, Optional, TypeVar
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)

# Background task queue for telemetry (non-blocking)
_telemetry_queue: asyncio.Queue = asyncio.Queue(maxsize=1000)

# Type variable for generic decorator
F = TypeVar("F", bound=Callable)


async def _track_deprecation_telemetry(
    endpoint_path: str,
    removal_date: str,
    successor_version: str,
    client_info: str,
    user_id: Optional[str] = None,
) -> None:
    """
    Track deprecated endpoint usage via telemetry service.

    This function is designed to be called in a non-blocking manner
    to avoid impacting API latency.
    """
    try:
        from app.db.session import async_session
        from app.services.telemetry_service import TelemetryService
        from uuid import UUID

        async with async_session() as db:
            telemetry = TelemetryService(db)
            await telemetry.track_event(
                event_name="deprecated_endpoint_called",
                user_id=UUID(user_id) if user_id else None,
                properties={
                    "endpoint": endpoint_path,
                    "removal_date": removal_date,
                    "successor_version": successor_version,
                    "client_info": client_info,
                    "days_until_sunset": days_until_sunset(removal_date),
                },
                interface="api",
            )
    except Exception as e:
        # Telemetry should never break the main flow
        logger.warning(f"Failed to track deprecation telemetry: {e}")


def deprecated_endpoint(
    removal_date: str,
    successor_version: str,
    migration_guide: Optional[str] = None,
    reason: str = "This endpoint is deprecated",
) -> Callable[[F], F]:
    """
    Decorator to mark an API endpoint as deprecated.

    Adds RFC 8594 compliant headers:
    - Deprecation: true
    - Sunset: {removal_date}
    - Link: <{successor}>; rel="successor-version"

    Args:
        removal_date: Date when endpoint will be removed (YYYY-MM-DD)
        successor_version: Path to the replacement endpoint
        migration_guide: Optional URL to migration documentation
        reason: Human-readable deprecation reason

    Example:
        @router.get("/v1/endpoint")
        @deprecated_endpoint(
            removal_date="2026-08-03",
            successor_version="/v2/endpoint",
            reason="Use V2 for gate-aware validation"
        )
        async def old_endpoint(...):
            ...
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Find response object in kwargs or create new context
            response: Optional[Response] = kwargs.get("response")
            request: Optional[Request] = None

            # Extract request from args/kwargs for logging
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            if not request:
                request = kwargs.get("request")

            # Call the original function
            result = await func(*args, **kwargs)

            # Log deprecation usage
            endpoint_path = func.__name__
            client_info = "unknown"
            if request:
                endpoint_path = str(request.url.path)
                client_info = request.headers.get("User-Agent", "unknown")[:50]

            logger.warning(
                f"DEPRECATED_ENDPOINT_CALLED: {endpoint_path} | "
                f"removal={removal_date} | successor={successor_version} | "
                f"client={client_info}"
            )

            # Track telemetry in background (non-blocking)
            try:
                # Extract user_id from request state if available
                user_id_str = None
                if request and hasattr(request, "state") and hasattr(request.state, "user"):
                    user = request.state.user
                    if hasattr(user, "id"):
                        user_id_str = str(user.id)

                # Create background task for telemetry (fire-and-forget)
                asyncio.create_task(
                    _track_deprecation_telemetry(
                        endpoint_path=endpoint_path,
                        removal_date=removal_date,
                        successor_version=successor_version,
                        client_info=client_info,
                        user_id=user_id_str,
                    )
                )
            except Exception as e:
                # Telemetry should never break the main flow
                logger.debug(f"Could not create telemetry task: {e}")

            # If response is a Response object (from returning directly),
            # we can add headers. For Pydantic models, headers are set at route level.
            if isinstance(result, Response):
                result.headers["Deprecation"] = "true"
                result.headers["Sunset"] = removal_date
                result.headers["Link"] = f'<{successor_version}>; rel="successor-version"'
                if migration_guide:
                    result.headers["X-Migration-Guide"] = migration_guide
                result.headers["X-Deprecation-Reason"] = reason

            return result

        # Add deprecation metadata to function for documentation
        wrapper._deprecated = True
        wrapper._deprecation_info = {
            "removal_date": removal_date,
            "successor_version": successor_version,
            "migration_guide": migration_guide,
            "reason": reason,
        }

        return wrapper  # type: ignore

    return decorator


def add_deprecation_headers(
    response: Response,
    removal_date: str,
    successor_version: str,
    migration_guide: Optional[str] = None,
    reason: str = "This endpoint is deprecated",
) -> None:
    """
    Manually add deprecation headers to a response.

    Use this when the @deprecated_endpoint decorator cannot be used
    (e.g., when response object is available after function execution).

    Args:
        response: FastAPI/Starlette Response object
        removal_date: Date when endpoint will be removed (YYYY-MM-DD)
        successor_version: Path to the replacement endpoint
        migration_guide: Optional URL to migration documentation
        reason: Human-readable deprecation reason
    """
    response.headers["Deprecation"] = "true"
    response.headers["Sunset"] = removal_date
    response.headers["Link"] = f'<{successor_version}>; rel="successor-version"'
    if migration_guide:
        response.headers["X-Migration-Guide"] = migration_guide
    response.headers["X-Deprecation-Reason"] = reason


def is_sunset_passed(removal_date: str) -> bool:
    """
    Check if the sunset date has passed.

    Args:
        removal_date: Date string in YYYY-MM-DD format

    Returns:
        True if current date is past removal date
    """
    try:
        sunset = datetime.strptime(removal_date, "%Y-%m-%d").date()
        return date.today() > sunset
    except ValueError:
        logger.error(f"Invalid removal_date format: {removal_date}")
        return False


def days_until_sunset(removal_date: str) -> int:
    """
    Calculate days until sunset.

    Args:
        removal_date: Date string in YYYY-MM-DD format

    Returns:
        Number of days until sunset (negative if passed)
    """
    try:
        sunset = datetime.strptime(removal_date, "%Y-%m-%d").date()
        return (sunset - date.today()).days
    except ValueError:
        logger.error(f"Invalid removal_date format: {removal_date}")
        return 0


# Constants for Sprint 147 deprecation
CONTEXT_AUTHORITY_V1_SUNSET = "2026-03-06"  # 30 days for internal API
ANALYTICS_V1_SUNSET = "2026-03-06"  # 30 days for internal API
