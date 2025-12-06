"""
File: backend/app/services/cache_service.py
Version: 1.0.0
Status: ACTIVE - STAGE 03 (BUILD)
Date: 2025-12-03
Authority: Backend Lead + CTO Approved
Foundation: SDLC 4.9 Complete Lifecycle, Zero Mock Policy

Description:
Cache service for API responses using Redis.
Provides cache decorators and utilities for performance optimization.

Sprint 23 Day 2: Performance Optimization
- Redis caching for frequent queries
- Configurable TTL per cache key pattern
- Automatic cache invalidation on write operations
"""

import hashlib
import json
import logging
from functools import wraps
from typing import Any, Callable, Optional, TypeVar
from uuid import UUID

from app.utils.redis import get_redis_client

logger = logging.getLogger(__name__)

# Type variable for generic return type
T = TypeVar("T")

# Default TTL values (in seconds)
CACHE_TTL_SHORT = 60  # 1 minute - for frequently changing data
CACHE_TTL_MEDIUM = 300  # 5 minutes - for moderately stable data
CACHE_TTL_LONG = 900  # 15 minutes - for stable data

# Cache key prefixes
CACHE_PREFIX = "sdlc:cache:"
PROJECTS_CACHE = "projects"
GATES_CACHE = "gates"
POLICIES_CACHE = "policies"
EVIDENCE_CACHE = "evidence"
USERS_CACHE = "users"


class CacheService:
    """
    Redis-based caching service for API responses.

    Features:
    - Automatic serialization/deserialization of JSON data
    - Configurable TTL per cache key
    - Pattern-based cache invalidation
    - UUID serialization support

    Usage:
        cache = CacheService()
        await cache.get("projects:list:user123")
        await cache.set("projects:list:user123", data, ttl=300)
        await cache.invalidate_pattern("projects:*")
    """

    @staticmethod
    def _serialize(value: Any) -> str:
        """Serialize value to JSON string with UUID support."""
        def json_encoder(obj):
            if isinstance(obj, UUID):
                return str(obj)
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

        return json.dumps(value, default=json_encoder)

    @staticmethod
    def _deserialize(value: str) -> Any:
        """Deserialize JSON string to Python object."""
        if value is None:
            return None
        return json.loads(value)

    @staticmethod
    def _make_key(prefix: str, *args, **kwargs) -> str:
        """
        Generate cache key from prefix and arguments.

        Args:
            prefix: Cache key prefix (e.g., "projects:list")
            *args: Positional arguments to include in key
            **kwargs: Keyword arguments to include in key

        Returns:
            Cache key string
        """
        key_parts = [CACHE_PREFIX, prefix]

        # Add positional args
        for arg in args:
            if arg is not None:
                key_parts.append(str(arg))

        # Add sorted kwargs for deterministic keys
        for k, v in sorted(kwargs.items()):
            if v is not None:
                key_parts.append(f"{k}={v}")

        return ":".join(key_parts)

    async def get(self, key: str) -> Optional[Any]:
        """
        Get cached value by key.

        Args:
            key: Full cache key

        Returns:
            Cached value or None if not found/expired
        """
        try:
            redis = await get_redis_client()
            value = await redis.get(key)
            if value:
                logger.debug(f"Cache HIT: {key}")
                return self._deserialize(value)
            logger.debug(f"Cache MISS: {key}")
            return None
        except Exception as e:
            logger.warning(f"Cache get error for {key}: {e}")
            return None

    async def set(
        self, key: str, value: Any, ttl: int = CACHE_TTL_MEDIUM
    ) -> bool:
        """
        Set cached value with TTL.

        Args:
            key: Full cache key
            value: Value to cache (must be JSON serializable)
            ttl: Time-to-live in seconds

        Returns:
            True if successful, False otherwise
        """
        try:
            redis = await get_redis_client()
            serialized = self._serialize(value)
            await redis.setex(key, ttl, serialized)
            logger.debug(f"Cache SET: {key} (TTL: {ttl}s)")
            return True
        except Exception as e:
            logger.warning(f"Cache set error for {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """
        Delete cached value by key.

        Args:
            key: Full cache key

        Returns:
            True if deleted, False otherwise
        """
        try:
            redis = await get_redis_client()
            result = await redis.delete(key)
            logger.debug(f"Cache DELETE: {key} (deleted: {result})")
            return result > 0
        except Exception as e:
            logger.warning(f"Cache delete error for {key}: {e}")
            return False

    async def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate all cache keys matching pattern.

        Args:
            pattern: Key pattern with wildcards (e.g., "projects:*")

        Returns:
            Number of keys deleted
        """
        try:
            redis = await get_redis_client()
            full_pattern = f"{CACHE_PREFIX}{pattern}"
            keys = []

            # Use SCAN for large keyspaces (non-blocking)
            async for key in redis.scan_iter(match=full_pattern, count=100):
                keys.append(key)

            if keys:
                deleted = await redis.delete(*keys)
                logger.info(f"Cache INVALIDATE: {pattern} ({deleted} keys)")
                return deleted
            return 0
        except Exception as e:
            logger.warning(f"Cache invalidate error for {pattern}: {e}")
            return 0


# Global cache instance
cache_service = CacheService()


def cached(
    prefix: str,
    ttl: int = CACHE_TTL_MEDIUM,
    key_builder: Optional[Callable[..., str]] = None,
):
    """
    Decorator for caching async function results.

    Args:
        prefix: Cache key prefix
        ttl: Time-to-live in seconds
        key_builder: Optional function to build cache key from args

    Usage:
        @cached("projects:list", ttl=300)
        async def list_projects(user_id: str, skip: int, limit: int):
            ...

        @cached("project:detail", key_builder=lambda project_id, **_: str(project_id))
        async def get_project(project_id: UUID):
            ...
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            # Build cache key
            if key_builder:
                key_suffix = key_builder(*args, **kwargs)
                cache_key = cache_service._make_key(prefix, key_suffix)
            else:
                # Generate key from function args
                key_hash = hashlib.md5(
                    f"{args}{sorted(kwargs.items())}".encode()
                ).hexdigest()[:12]
                cache_key = cache_service._make_key(prefix, key_hash)

            # Try to get from cache
            cached_value = await cache_service.get(cache_key)
            if cached_value is not None:
                return cached_value

            # Execute function and cache result
            result = await func(*args, **kwargs)
            await cache_service.set(cache_key, result, ttl)
            return result

        return wrapper
    return decorator


async def invalidate_projects_cache():
    """Invalidate all project-related caches."""
    await cache_service.invalidate_pattern(f"{PROJECTS_CACHE}:*")


async def invalidate_gates_cache(project_id: Optional[UUID] = None):
    """Invalidate gate caches, optionally for specific project."""
    if project_id:
        await cache_service.invalidate_pattern(f"{GATES_CACHE}:{project_id}:*")
    else:
        await cache_service.invalidate_pattern(f"{GATES_CACHE}:*")


async def invalidate_policies_cache():
    """Invalidate all policy caches."""
    await cache_service.invalidate_pattern(f"{POLICIES_CACHE}:*")


async def invalidate_evidence_cache(gate_id: Optional[UUID] = None):
    """Invalidate evidence caches, optionally for specific gate."""
    if gate_id:
        await cache_service.invalidate_pattern(f"{EVIDENCE_CACHE}:{gate_id}:*")
    else:
        await cache_service.invalidate_pattern(f"{EVIDENCE_CACHE}:*")


# Sprint 31 Day 2: Additional cache helpers for Gate G3 performance
COMPLIANCE_CACHE = "compliance"
VALIDATION_CACHE = "validation"


async def invalidate_compliance_cache(project_id: Optional[UUID] = None):
    """Invalidate compliance scan caches."""
    if project_id:
        await cache_service.invalidate_pattern(f"{COMPLIANCE_CACHE}:{project_id}:*")
    else:
        await cache_service.invalidate_pattern(f"{COMPLIANCE_CACHE}:*")


async def invalidate_validation_cache(project_id: Optional[UUID] = None):
    """Invalidate SDLC validation caches."""
    if project_id:
        await cache_service.invalidate_pattern(f"{VALIDATION_CACHE}:{project_id}:*")
    else:
        await cache_service.invalidate_pattern(f"{VALIDATION_CACHE}:*")
