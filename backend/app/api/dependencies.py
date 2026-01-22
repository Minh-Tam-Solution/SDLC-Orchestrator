"""
=========================================================================
API Dependencies - FastAPI Dependency Injection
SDLC Orchestrator - Stage 03 (BUILD)

Version: 1.0.0
Date: November 28, 2025
Status: ACTIVE - Week 3 Day 3 API Implementation
Authority: Backend Lead + CTO Approved
Foundation: FastAPI Dependency Injection, JWT Authentication
Framework: SDLC 4.9 Complete Lifecycle

Purpose:
- JWT token authentication dependency
- Current user injection
- Role-based access control (RBAC) dependencies
- Database session dependency (already in db/session.py)

Dependencies:
- get_current_user: Extract user from JWT token
- get_current_active_user: Ensure user is active
- require_role: Check user has specific role (CTO, CPO, CEO, etc.)

Security:
- JWT validation (signature, expiry)
- User active status check
- Role permission enforcement

Zero Mock Policy: Production-ready authentication dependencies
=========================================================================
"""

from typing import List, Optional
from uuid import UUID

from fastapi import Cookie, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.cookies import ACCESS_TOKEN_COOKIE_NAME
from app.core.security import decode_token, hash_api_key
from app.db.session import get_db
from app.models.user import User, APIKey
from app.utils.redis import get_redis_client
from datetime import datetime


async def get_redis():
    """
    Get Redis client for dependency injection.

    Usage:
        @router.get("/data")
        async def get_data(redis = Depends(get_redis)):
            value = await redis.get("key")
            return {"value": value}

    Returns:
        Redis async client instance
    """
    return await get_redis_client()

# HTTP Bearer token scheme (Authorization: Bearer <token>)
security = HTTPBearer()


async def validate_api_key(api_key: str, db: AsyncSession) -> User:
    """
    Validate API key and return user.

    Args:
        api_key: Full API key (e.g., sdlc_live_abc123...)
        db: Database session

    Returns:
        User: User associated with the API key

    Raises:
        HTTPException(401): If API key is invalid, expired, or revoked

    Security:
        - Hash API key with SHA-256
        - Lookup in database by hash
        - Check expiry and active status
        - Update last_used_at timestamp
    """
    key_hash = hash_api_key(api_key)

    result = await db.execute(
        select(APIKey)
        .options(selectinload(APIKey.user).selectinload(User.roles))
        .where(APIKey.key_hash == key_hash, APIKey.is_active == True)
    )
    db_key = result.scalar_one_or_none()

    if not db_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check expiry
    if db_key.expires_at and db_key.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key expired",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Update last_used_at
    db_key.last_used_at = datetime.utcnow()
    await db.commit()

    return db_key.user


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: AsyncSession = Depends(get_db),
    access_token_cookie: Optional[str] = Cookie(None, alias=ACCESS_TOKEN_COOKIE_NAME),
) -> User:
    """
    Get current authenticated user from JWT token, API key, OR httpOnly cookie.

    Sprint 63 Dual Mode Authentication:
    - Supports BOTH cookie and header authentication (backward compatibility)
    - Cookie auth is preferred (more secure against XSS)
    - Header auth is fallback for legacy clients (Vite dashboard)

    Authentication Priority:
        1. httpOnly Cookie (sdlc_access_token) - Sprint 63 preferred method
        2. Authorization header (Bearer token) - Legacy method
        3. API key (sdlc_live_*) - Personal access tokens

    Returns:
        User: Current authenticated user

    Raises:
        HTTPException(401): If no valid auth found
        HTTPException(401): If token/key is invalid or expired
        HTTPException(401): If user account is deleted

    Usage:
        @router.get("/me")
        async def get_me(current_user: User = Depends(get_current_user)):
            return {"user_id": current_user.id, "email": current_user.email}

    Security Flow (Sprint 63):
        1. Try cookie first (sdlc_access_token)
        2. If no cookie, try Authorization header
        3. Validate token (JWT or API key)
        4. Fetch user from database
        5. Return User object
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token: Optional[str] = None

    # Priority 1: Try httpOnly cookie (Sprint 63 - preferred method)
    if access_token_cookie:
        token = access_token_cookie

    # Priority 2: Fallback to Authorization header (backward compatibility)
    elif credentials:
        token = credentials.credentials

    # No auth found
    if not token:
        raise credentials_exception

    # Check if it's an API key (starts with 'sdlc_live_')
    if token.startswith("sdlc_live_"):
        return await validate_api_key(token, db)

    # Otherwise, treat as JWT token
    try:
        payload = decode_token(token)

        # Extract user ID from token
        user_id: Optional[str] = payload.get("sub")
        if user_id is None:
            raise credentials_exception

        # Token type must be "access"
        token_type: Optional[str] = payload.get("type")
        if token_type != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type (expected 'access')",
                headers={"WWW-Authenticate": "Bearer"},
            )

    except JWTError:
        raise credentials_exception

    # Fetch user from database with eager-loaded relationships
    result = await db.execute(
        select(User)
        .options(selectinload(User.roles), selectinload(User.oauth_accounts))
        .where(User.id == UUID(user_id))
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get current active user (is_active = True).

    Returns:
        User: Current active user

    Raises:
        HTTPException(403): If user account is inactive

    Usage:
        @router.get("/protected")
        async def protected_route(user: User = Depends(get_current_active_user)):
            return {"message": "You have access!"}

    Security:
        - Ensures user account is active (is_active = True)
        - Inactive users cannot access protected routes
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    return current_user


def require_roles(allowed_roles: List[str]):
    """
    Dependency factory to require specific roles.

    Args:
        allowed_roles: List of allowed role names (e.g., ["CTO", "CPO", "CEO"])

    Returns:
        Dependency function that checks user roles

    Usage:
        @router.post("/gates/{gate_id}/approve")
        async def approve_gate(
            gate_id: UUID,
            user: User = Depends(require_roles(["CTO", "CPO", "CEO"])),
            db: AsyncSession = Depends(get_db)
        ):
            # Only CTO, CPO, or CEO can approve gates
            return {"message": "Gate approved!"}

    Security:
        - Checks user has at least one of the allowed roles
        - Returns 403 Forbidden if user lacks required role
    """

    async def check_roles(
        current_user: User = Depends(get_current_active_user),
    ) -> User:
        # Superusers bypass role checks (Sprint 69 fix)
        if current_user.is_superuser:
            return current_user

        # Get user's role names from relationships
        user_role_names = [role.display_name for role in current_user.roles]

        # Check if user has at least one allowed role
        has_role = any(role in allowed_roles for role in user_role_names)

        if not has_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {', '.join(allowed_roles)}",
            )

        return current_user

    return check_roles


# Alias for backward compatibility (singular form)
require_role = require_roles


def require_superuser(current_user: User = Depends(get_current_active_user)) -> User:
    """
    Dependency to require superuser access.

    Returns:
        User: Current superuser

    Raises:
        HTTPException(403): If user is not a superuser

    Usage:
        @router.delete("/users/{user_id}")
        async def delete_user(
            user_id: UUID,
            admin: User = Depends(require_superuser),
            db: AsyncSession = Depends(get_db)
        ):
            # Only superusers can delete users
            return {"message": "User deleted"}

    Security:
        - Checks user.is_superuser flag
        - Returns 403 Forbidden if user is not a superuser
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superuser access required",
        )

    return current_user


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """
    Get current user if token provided, otherwise None.

    Returns:
        User or None: Current user if authenticated, None otherwise

    Usage:
        @router.get("/public-or-private")
        async def mixed_route(user: Optional[User] = Depends(get_current_user_optional)):
            if user:
                return {"message": f"Hello {user.full_name}"}
            else:
                return {"message": "Hello Guest"}

    Security:
        - Optional authentication (doesn't raise 401 if no token)
        - Useful for routes with different behavior for authenticated/anonymous users
    """
    if not credentials:
        return None

    try:
        token = credentials.credentials
        payload = decode_token(token)
        user_id: Optional[str] = payload.get("sub")

        if user_id is None:
            return None

        result = await db.execute(
            select(User)
            .options(selectinload(User.roles), selectinload(User.oauth_accounts))
            .where(User.id == UUID(user_id))
        )
        user = result.scalar_one_or_none()

        if user:
            return user

    except JWTError:
        return None

    return None


# =========================================================================
# Rate Limiting Dependencies (Sprint 76 - P0 Fix)
# =========================================================================

import logging
import time

_rate_limit_logger = logging.getLogger(__name__)


class RateLimitExceeded(HTTPException):
    """Exception raised when rate limit is exceeded."""

    def __init__(self, limit: int, window: int, retry_after: int):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "rate_limit_exceeded",
                "message": f"Rate limit exceeded: {limit} requests per {window} seconds",
                "limit": limit,
                "window_seconds": window,
                "retry_after": retry_after,
            },
            headers={"Retry-After": str(retry_after)},
        )


def rate_limit(
    max_requests: int = 10,
    window_seconds: int = 60,
    key_prefix: str = "endpoint",
):
    """
    Rate limiter dependency factory for endpoint-specific limits.

    **Sprint 76 P0 Fix: DoS Protection for Analytics Endpoints**

    Creates a FastAPI dependency that enforces per-user rate limiting
    using Redis sliding window algorithm.

    Args:
        max_requests: Maximum requests allowed per window (default: 10)
        window_seconds: Time window in seconds (default: 60)
        key_prefix: Redis key prefix for this endpoint (default: "endpoint")

    Returns:
        Dependency function that checks rate limit

    Usage:
        @router.get("/compute-heavy")
        async def compute_heavy(
            _: None = Depends(rate_limit(max_requests=10, window_seconds=60)),
            user: User = Depends(get_current_user),
        ):
            # Rate limited to 10 req/min per user
            return expensive_computation()

    Security:
        - Per-user rate limiting (authenticated users)
        - Sliding window algorithm (smooth rate limiting)
        - Redis-backed for distributed deployments
        - Fail-open if Redis unavailable (logs warning)

    OWASP ASVS:
        - V11.1.7: DoS protection for compute-heavy operations
    """

    async def check_rate_limit(
        request: Request,
        current_user: User = Depends(get_current_user),
    ) -> None:
        """Check if user has exceeded rate limit for this endpoint."""
        try:
            redis = await get_redis_client()

            # Build rate limit key: prefix:user_id
            rate_key = f"ratelimit:{key_prefix}:user:{current_user.id}"

            # Get current timestamp
            now = int(time.time())

            # Remove old entries outside window
            cutoff = now - window_seconds
            await redis.zremrangebyscore(rate_key, 0, cutoff)

            # Count requests in window
            request_count = await redis.zcard(rate_key)

            if request_count >= max_requests:
                # Calculate retry-after (time until oldest entry expires)
                oldest = await redis.zrange(rate_key, 0, 0, withscores=True)
                if oldest:
                    oldest_ts = int(oldest[0][1])
                    retry_after = (oldest_ts + window_seconds) - now
                else:
                    retry_after = window_seconds

                _rate_limit_logger.warning(
                    f"Rate limit exceeded for user {current_user.id} on {key_prefix}: "
                    f"{request_count}/{max_requests} requests"
                )
                raise RateLimitExceeded(
                    limit=max_requests,
                    window=window_seconds,
                    retry_after=max(1, retry_after),
                )

            # Add current request timestamp
            await redis.zadd(rate_key, {f"{now}:{id(request)}": now})

            # Set TTL on key (window + buffer)
            await redis.expire(rate_key, window_seconds + 10)

        except RateLimitExceeded:
            # Re-raise rate limit exceptions
            raise
        except Exception as e:
            # Fail-open: log warning and allow request if Redis unavailable
            _rate_limit_logger.warning(
                f"Rate limit check failed (allowing request): {e}"
            )

    return check_rate_limit


# Pre-configured rate limiters for common use cases
def analytics_rate_limit():
    """
    Rate limiter for analytics endpoints (10 req/min per user).

    **Sprint 76 P0 Fix: CTO-mandated rate limiting for compute-heavy endpoints**

    Applies to:
    - GET /projects/{id}/velocity
    - GET /sprints/{id}/health
    - GET /sprints/{id}/suggestions
    - GET /sprints/{id}/analytics

    Returns:
        Dependency for 10 req/min rate limiting
    """
    return rate_limit(
        max_requests=10,
        window_seconds=60,
        key_prefix="analytics",
    )


# =========================================================================
# Sprint 88: Platform Admin Access Control
# =========================================================================


def require_customer_user(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    Dependency that ensures user is NOT a platform admin.

    **Sprint 88: Platform Admin Privacy Fix**

    Platform admins manage system operations but CANNOT access customer data.
    This dependency blocks platform admins from customer data endpoints.

    Args:
        current_user: Authenticated user from get_current_active_user

    Returns:
        User: User object if not platform admin

    Raises:
        HTTPException(403): If user is platform admin

    Usage:
        @router.get("/projects")
        async def list_projects(
            user: User = Depends(require_customer_user),
            db: AsyncSession = Depends(get_db)
        ):
            # user is guaranteed to NOT be platform admin
            projects = await get_user_projects(user.id, db)
            return projects

    Security:
        - Platform admins (is_platform_admin=True) get 403 Forbidden
        - Regular users and regular admins can access
        - Frontend already blocks UI, this is backend enforcement

    Reference:
        - Sprint 88 Day 4-5: Backend Migration
        - Migration: s88_001_add_is_platform_admin
        - ADR-030: Platform Admin Role Redesign
    """
    if current_user.is_platform_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Platform administrators cannot access customer data. "
                   "This is a privacy protection measure implemented in Sprint 88.",
        )
    return current_user


def get_user_organization_filter(
    current_user: User = Depends(get_current_active_user),
) -> Optional[UUID]:
    """
    Get organization filter based on user role.

    **Sprint 88: Platform Admin Privacy Fix**

    Determines which organizations a user can access based on their role.

    Args:
        current_user: Authenticated user

    Returns:
        None: If user is regular admin (can see all organizations)
        UUID: organization_id if user is regular user or platform admin

    Usage:
        @router.get("/projects")
        async def list_projects(
            org_filter: Optional[UUID] = Depends(get_user_organization_filter),
            db: AsyncSession = Depends(get_db)
        ):
            query = select(Project)
            if org_filter:
                query = query.where(Project.organization_id == org_filter)
            projects = await db.execute(query)
            return projects.scalars().all()

    Logic:
        - Regular admin (is_superuser=True, is_platform_admin=False): None (all orgs)
        - Platform admin (is_platform_admin=True): user.organization_id (own org only)
        - Regular user: user.organization_id (own org only)

    Security:
        - Platform admins isolated to their own organization
        - Regular admins can manage all organizations
        - Regular users only see their own organization
    """
    # Regular admin (non-platform): can see all organizations
    if current_user.is_superuser and not current_user.is_platform_admin:
        return None

    # Platform admin or regular user: only their organization
    return current_user.organization_id
