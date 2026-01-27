"""
=========================================================================
Rate Limiting Middleware - Redis-Based
SDLC Orchestrator - Week 5 Day 1 (P1 Features)

Purpose:
- Per-user rate limiting: 100 requests/minute
- Per-IP rate limiting: 1000 requests/hour
- Redis-backed sliding window algorithm
- OWASP ASVS Level 2 compliance (V11: Business Logic)

Requirements:
- 100 req/min per authenticated user
- 1000 req/hour per IP address
- Graceful degradation (fail-open if Redis unavailable)
=========================================================================
"""

import logging
import time
from typing import Callable, Optional

from fastapi import Request, status
from fastapi.responses import JSONResponse
from jose import JWTError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.security import decode_token
from app.utils.redis import get_redis_client

logger = logging.getLogger(__name__)

# Rate limit configuration
USER_RATE_LIMIT = 100  # requests per minute per user
IP_RATE_LIMIT = 1000  # requests per hour per IP
USER_WINDOW = 60  # seconds
IP_WINDOW = 3600  # seconds (1 hour)


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware using Redis sliding window.

    Algorithm:
    1. Check user rate limit (if authenticated): 100 req/min
    2. Check IP rate limit: 1000 req/hour
    3. If limit exceeded, return 429 Too Many Requests
    4. Fail-open if Redis unavailable (log warning, allow request)

    Usage:
        app.add_middleware(RateLimiterMiddleware)
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.redis_available = True

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive)

        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/health/ready", "/"]:
            await self.app(scope, receive, send)
            return

        try:
            # Get rate limit identifiers
            user_id = self._get_user_id(request)
            ip_address = self._get_ip_address(request)

            # Check user rate limit (if authenticated)
            if user_id:
                if await self._check_rate_limit(
                    identifier=f"user:{user_id}",
                    limit=USER_RATE_LIMIT,
                    window=USER_WINDOW,
                ):
                    await self._rate_limit_response(send, "user")
                    return

            # Check IP rate limit
            if await self._check_rate_limit(
                identifier=f"ip:{ip_address}",
                limit=IP_RATE_LIMIT,
                window=IP_WINDOW,
            ):
                await self._rate_limit_response(send, "ip")
                return

            # Rate limit passed, continue request
            await self.app(scope, receive, send)

        except Exception as e:
            # Fail-open: if Redis unavailable, allow request (log warning)
            logger.warning(f"Rate limit check failed (allowing request): {e}")
            self.redis_available = False
            await self.app(scope, receive, send)

    def _get_user_id(self, request: Request) -> Optional[str]:
        """
        Extract user ID from JWT token (header or cookie).

        Sprint 105: Support both Authorization header and httpOnly cookies.

        Args:
            request: FastAPI request object

        Returns:
            User ID string or None if not authenticated
        """
        token = None

        # Priority 1: Check httpOnly cookie (Sprint 63 preferred method)
        from app.core.cookies import ACCESS_TOKEN_COOKIE_NAME
        cookie_token = request.cookies.get(ACCESS_TOKEN_COOKIE_NAME)
        if cookie_token:
            token = cookie_token

        # Priority 2: Check Authorization header for JWT token
        if not token:
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]

        if token:
            try:
                # Decode JWT token to extract user_id
                payload = decode_token(token)
                
                # Extract user ID from token (sub claim)
                user_id = payload.get("sub")
                token_type = payload.get("type")
                
                # Only use access tokens for rate limiting
                if user_id and token_type == "access":
                    return str(user_id)
                    
            except JWTError:
                # Invalid or expired token - treat as unauthenticated (will use IP rate limiting)
                logger.debug("Invalid JWT token in rate limiter (treating as unauthenticated)")
                return None
            except Exception as e:
                # Other errors - log and treat as unauthenticated
                logger.debug(f"Failed to extract user_id from token: {e}")
                return None

        return None

    def _get_ip_address(self, request: Request) -> str:
        """
        Extract client IP address from request.

        Handles proxies/load balancers (X-Forwarded-For header).

        Args:
            request: FastAPI request object

        Returns:
            IP address string
        """
        # Check X-Forwarded-For header (from proxies/load balancers)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take first IP (original client)
            return forwarded_for.split(",")[0].strip()

        # Check X-Real-IP header (from nginx)
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()

        # Fallback to direct client IP
        client_host = request.client.host if request.client else "unknown"
        return client_host

    async def _check_rate_limit(
        self, identifier: str, limit: int, window: int
    ) -> bool:
        """
        Check if rate limit exceeded using Redis sliding window.

        Algorithm:
        1. Get current request count from Redis (key: identifier, sorted set)
        2. Remove old entries (outside window)
        3. Count remaining entries
        4. If count >= limit, return True (rate limit exceeded)
        5. Add current timestamp to sorted set
        6. Set TTL on key (window + 1 second)

        Args:
            identifier: Rate limit identifier (e.g., "user:123" or "ip:1.2.3.4")
            limit: Maximum requests allowed
            window: Time window in seconds

        Returns:
            True if rate limit exceeded, False otherwise
        """
        try:
            redis = await get_redis_client()

            # Get current timestamp
            now = int(time.time())

            # Redis key for this identifier
            key = f"ratelimit:{identifier}"

            # Remove entries outside time window (older than now - window)
            cutoff = now - window
            await redis.zremrangebyscore(key, 0, cutoff)

            # Count current requests in window
            count = await redis.zcard(key)

            # Check if limit exceeded
            if count >= limit:
                logger.warning(
                    f"Rate limit exceeded: {identifier} ({count}/{limit} requests)"
                )
                return True

            # Add current request timestamp
            await redis.zadd(key, {str(now): now})

            # Set TTL on key (window + 1 second for safety)
            await redis.expire(key, window + 1)

            return False

        except Exception as e:
            # Fail-open: if Redis unavailable, log warning and allow request
            logger.warning(f"Rate limit check failed (Redis error): {e}")
            return False

    async def _rate_limit_response(self, send: Callable, limit_type: str):
        """
        Send 429 Too Many Requests response.

        Args:
            send: ASGI send callable
            limit_type: Type of rate limit ("user" or "ip")
        """
        response = JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "error": "rate_limit_exceeded",
                "message": f"{limit_type.title()} rate limit exceeded",
                "retry_after": USER_WINDOW if limit_type == "user" else IP_WINDOW,
            },
        )

        await response(scope=None, receive=None, send=send)

