"""
=========================================================================
Redis Connection Utility
SDLC Orchestrator - Week 5 Day 1 (P1 Features)

Purpose:
- Redis connection management for rate limiting and caching
- Singleton pattern for connection reuse
- Async support for FastAPI
=========================================================================
"""

import logging
from typing import Optional

import redis.asyncio as aioredis
from redis.asyncio import Redis

from app.core.config import settings

logger = logging.getLogger(__name__)

# Global Redis connection pool (singleton)
_redis_client: Optional[Redis] = None


async def get_redis_client() -> Redis:
    """
    Get or create Redis client (singleton pattern).

    Returns:
        Redis async client instance

    Example:
        redis = await get_redis_client()
        await redis.set("key", "value")
        value = await redis.get("key")
    """
    global _redis_client

    if _redis_client is None:
        _redis_client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            max_connections=100,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
        )
        logger.info(f"Redis client initialized: {settings.REDIS_URL}")

    # Test connection
    try:
        await _redis_client.ping()
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")
        raise

    return _redis_client


async def close_redis_client():
    """Close Redis connection pool."""
    global _redis_client

    if _redis_client:
        await _redis_client.close()
        _redis_client = None
        logger.info("Redis client closed")

