"""
File: backend/app/middleware/cache_headers.py
Version: 1.0.0
Status: ACTIVE - STAGE 03 (BUILD)
Date: 2025-12-03
Authority: Backend Lead + CTO Approved
Foundation: SDLC 4.9 Complete Lifecycle, Zero Mock Policy

Description:
HTTP Cache Headers Middleware for API responses.
Adds Cache-Control, ETag, and Vary headers to optimize client-side caching.

Sprint 23 Day 4: API Response Optimization
- Cache-Control headers for different endpoint types
- ETag support for conditional requests (304 Not Modified)
- Vary header for proper cache key differentiation
"""

import hashlib
import logging
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse

logger = logging.getLogger(__name__)

# Cache configuration per endpoint pattern
# Sprint 31 Day 2: Enhanced caching for Gate G3 performance targets
CACHE_CONFIG = {
    # Static-like endpoints (rarely change)
    "/api/v1/policies": {"max_age": 300, "stale_while_revalidate": 60},  # 5 min
    "/api/docs": {"max_age": 3600, "stale_while_revalidate": 300},  # 1 hour
    "/api/openapi.json": {"max_age": 3600, "stale_while_revalidate": 300},
    "/health": {"max_age": 10, "stale_while_revalidate": 5},  # 10 sec

    # Dynamic endpoints (short cache) - Optimized for Gate G3
    "/api/v1/projects": {"max_age": 60, "stale_while_revalidate": 30},  # 1 min (increased from 30s)
    "/api/v1/gates": {"max_age": 60, "stale_while_revalidate": 30},  # 1 min (increased from 30s)
    "/api/v1/dashboard": {"max_age": 60, "stale_while_revalidate": 30},  # 1 min
    "/api/v1/compliance": {"max_age": 120, "stale_while_revalidate": 60},  # 2 min (increased)
    "/api/v1/evidence": {"max_age": 60, "stale_while_revalidate": 30},  # 1 min (new)

    # SDLC Validation endpoints - Sprint 31
    "/api/v1/sdlc": {"max_age": 120, "stale_while_revalidate": 60},  # 2 min

    # Analytics endpoints (can be cached longer)
    "/api/v1/analytics": {"max_age": 300, "stale_while_revalidate": 120},  # 5 min

    # User-specific endpoints (no cache)
    "/api/v1/auth": {"max_age": 0, "private": True},
    "/api/v1/notifications": {"max_age": 0, "private": True},
    "/api/v1/council": {"max_age": 0, "private": True},  # AI Council (real-time)
}

# Endpoints that should never be cached
NO_CACHE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
NO_CACHE_PATHS = {"/api/v1/auth/login", "/api/v1/auth/logout", "/api/v1/auth/refresh"}


class CacheHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add HTTP caching headers to API responses.

    Features:
    - Cache-Control header with max-age and stale-while-revalidate
    - ETag header for conditional requests (If-None-Match)
    - Vary header for proper cache key differentiation
    - Private cache for user-specific endpoints
    - No-cache for mutation endpoints (POST, PUT, DELETE)

    Usage:
        app.add_middleware(CacheHeadersMiddleware)
    """

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> StarletteResponse:
        # Skip caching for mutation methods
        if request.method in NO_CACHE_METHODS:
            response = await call_next(request)
            response.headers["Cache-Control"] = "no-store"
            return response

        # Skip caching for specific paths
        path = request.url.path
        if path in NO_CACHE_PATHS:
            response = await call_next(request)
            response.headers["Cache-Control"] = "no-store"
            return response

        # Get response
        response = await call_next(request)

        # Only cache successful responses
        if response.status_code != 200:
            return response

        # Find matching cache config
        cache_config = self._get_cache_config(path)

        if cache_config:
            # Build Cache-Control header
            directives = []

            if cache_config.get("private"):
                directives.append("private")
            else:
                directives.append("public")

            max_age = cache_config.get("max_age", 0)
            if max_age > 0:
                directives.append(f"max-age={max_age}")

                # Add stale-while-revalidate for better UX
                swr = cache_config.get("stale_while_revalidate", 0)
                if swr > 0:
                    directives.append(f"stale-while-revalidate={swr}")
            else:
                directives.append("no-cache")

            response.headers["Cache-Control"] = ", ".join(directives)

            # Add Vary header for proper cache differentiation
            response.headers["Vary"] = "Authorization, Accept-Encoding"

        return response

    def _get_cache_config(self, path: str) -> dict | None:
        """
        Find cache configuration for the given path.

        Matches exact paths first, then prefix matches.
        """
        # Exact match
        if path in CACHE_CONFIG:
            return CACHE_CONFIG[path]

        # Prefix match (for paths like /api/v1/projects/123)
        for config_path, config in CACHE_CONFIG.items():
            if path.startswith(config_path):
                return config

        return None


class ETagMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add ETag headers and handle conditional requests.

    Features:
    - Generates ETag from response content hash
    - Handles If-None-Match header for 304 Not Modified responses
    - Reduces bandwidth for unchanged resources

    Note: This middleware should be added after CacheHeadersMiddleware
    for optimal performance (304 responses don't need cache headers).
    """

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> StarletteResponse:
        # Skip for mutation methods
        if request.method in NO_CACHE_METHODS:
            return await call_next(request)

        # Get response
        response = await call_next(request)

        # Only add ETag for successful GET responses
        if request.method != "GET" or response.status_code != 200:
            return response

        # Read response body to generate ETag
        body = b""
        async for chunk in response.body_iterator:
            body += chunk

        # Generate ETag from content hash
        etag = f'"{hashlib.md5(body).hexdigest()}"'

        # Check If-None-Match header
        if_none_match = request.headers.get("If-None-Match")
        if if_none_match and if_none_match == etag:
            # Return 304 Not Modified
            return Response(
                status_code=304,
                headers={
                    "ETag": etag,
                    "Cache-Control": response.headers.get("Cache-Control", ""),
                },
            )

        # Create new response with ETag
        return Response(
            content=body,
            status_code=response.status_code,
            headers={
                **dict(response.headers),
                "ETag": etag,
            },
            media_type=response.media_type,
        )
