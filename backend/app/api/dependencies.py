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

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

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
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Get current authenticated user from JWT token OR API key.

    Headers:
        Authorization: Bearer <access_token_or_api_key>

    Supports two authentication methods:
        1. JWT token: Standard access tokens (starts with 'ey...')
        2. API key: Personal access tokens (starts with 'sdlc_live_')

    Returns:
        User: Current authenticated user

    Raises:
        HTTPException(401): If token/key is invalid or user not found
        HTTPException(401): If token/key is expired
        HTTPException(401): If user account is deleted

    Usage:
        @router.get("/me")
        async def get_me(current_user: User = Depends(get_current_user)):
            return {"user_id": current_user.id, "email": current_user.email}

    Security Flow:
        1. Extract token from Authorization header
        2. Check if it's an API key (starts with 'sdlc_live_')
           - If yes: Validate API key via hash lookup
           - If no: Decode and validate JWT token
        3. Fetch user from database
        4. Verify user exists and is not deleted
        5. Return User object
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = credentials.credentials

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
                return {"message": f"Hello {user.name}"}
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
