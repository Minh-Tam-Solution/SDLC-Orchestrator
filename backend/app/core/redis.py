"""
Redis Client Configuration

Used for:
- Rate limiting (invitations, API calls)
- Session storage
- Token blacklist

Reference: Sprint 128 Infrastructure Setup
"""
import os
from typing import Optional

import redis

# Global Redis client instance
redis_client: Optional[redis.Redis] = None


def get_redis_client() -> Optional[redis.Redis]:
    """
    Get Redis client instance (singleton pattern).

    Returns:
        Redis client or None if connection fails
    """
    global redis_client

    if redis_client is None:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

        try:
            redis_client = redis.from_url(
                redis_url,
                max_connections=10,
                socket_timeout=5,
                decode_responses=True,
            )

            # Test connection
            redis_client.ping()

        except Exception as e:
            print(f"⚠️ Redis connection failed: {str(e)}")
            print("Rate limiting will be disabled (development only)")
            redis_client = None

    return redis_client


def close_redis_client():
    """Close Redis connection on app shutdown"""
    global redis_client
    if redis_client:
        redis_client.close()
        redis_client = None


# Initialize on import (optional, can be deferred to startup)
try:
    redis_client = get_redis_client()
except Exception:
    redis_client = None
