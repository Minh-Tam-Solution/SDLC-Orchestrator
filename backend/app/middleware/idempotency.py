"""
=========================================================================
Idempotency Middleware - Redis-Based Response Replay
SDLC Orchestrator - Sprint 173 (Governance Loop)

Version: 1.0.0
Date: February 15, 2026
Status: ACTIVE - Sprint 173 Implementation
Authority: CTO + Architect + SDLC Expert — All Approved v4 FINAL
Reference: ADR-053-Governance-Loop-State-Machine.md

Purpose:
- Prevent duplicate mutations on gate governance endpoints
- Redis-backed response storage (TTL 24h)
- User-scoped keys to prevent cross-user collision
- Graceful degradation when Redis is unavailable

Key Pattern:
    idempotency:{user_id}:{endpoint}:{gate_id}:{idempotency_key}

Endpoints Supporting Idempotency:
    POST /gates/{id}/evaluate
    POST /gates/{id}/submit
    POST /gates/{id}/approve
    POST /gates/{id}/reject
    POST /gates/{id}/evidence

Zero Mock Policy: Real Redis operations
=========================================================================
"""

import json
import logging
from typing import Any, Callable, Dict, Optional
from uuid import UUID

from fastapi import Request, Response
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)

# TTL for idempotency keys (24 hours)
IDEMPOTENCY_TTL = 86400

# Header name for idempotency key
IDEMPOTENCY_HEADER = "X-Idempotency-Key"


def _build_idempotency_key(
    user_id: UUID,
    endpoint: str,
    gate_id: str,
    idempotency_key: str,
) -> str:
    """Build Redis key for idempotency storage."""
    return f"idempotency:{user_id}:{endpoint}:{gate_id}:{idempotency_key}"


async def check_idempotency(
    request: Request,
    user_id: UUID,
    gate_id: str,
    endpoint: str,
) -> Optional[Dict[str, Any]]:
    """
    Check if this request has been processed before.

    Args:
        request: FastAPI request object
        user_id: Current user UUID
        gate_id: Gate UUID from path
        endpoint: Endpoint name (evaluate, submit, approve, reject, evidence)

    Returns:
        Stored response dict if duplicate, None if first request
    """
    idempotency_key = request.headers.get(IDEMPOTENCY_HEADER)
    if not idempotency_key:
        return None

    try:
        from app.utils.redis import get_redis_client
        redis = await get_redis_client()

        key = _build_idempotency_key(user_id, endpoint, gate_id, idempotency_key)
        stored = await redis.get(key)

        if stored:
            logger.info(
                f"Idempotent request detected: {endpoint} gate={gate_id} "
                f"key={idempotency_key} user={user_id}"
            )
            return json.loads(stored)

    except Exception as e:
        # Graceful degradation: if Redis is down, proceed normally
        logger.warning(f"Redis idempotency check failed (proceeding normally): {e}")

    return None


async def store_idempotency(
    request: Request,
    user_id: UUID,
    gate_id: str,
    endpoint: str,
    response_data: Dict[str, Any],
) -> None:
    """
    Store response for idempotency replay.

    Args:
        request: FastAPI request object
        user_id: Current user UUID
        gate_id: Gate UUID from path
        endpoint: Endpoint name
        response_data: Response body to store for replay
    """
    idempotency_key = request.headers.get(IDEMPOTENCY_HEADER)
    if not idempotency_key:
        return

    try:
        from app.utils.redis import get_redis_client
        redis = await get_redis_client()

        key = _build_idempotency_key(user_id, endpoint, gate_id, idempotency_key)

        # Serialize UUIDs and datetimes to strings for JSON storage
        serializable = _make_serializable(response_data)
        await redis.setex(key, IDEMPOTENCY_TTL, json.dumps(serializable))

        logger.debug(
            f"Idempotency response stored: {endpoint} gate={gate_id} "
            f"key={idempotency_key} TTL={IDEMPOTENCY_TTL}s"
        )

    except Exception as e:
        # Graceful degradation: if Redis is down, don't block the response
        logger.warning(f"Redis idempotency store failed (non-blocking): {e}")


def _make_serializable(obj: Any) -> Any:
    """Convert UUIDs, datetimes, and other non-serializable types to strings."""
    if isinstance(obj, dict):
        return {k: _make_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_make_serializable(item) for item in obj]
    elif isinstance(obj, UUID):
        return str(obj)
    elif hasattr(obj, "isoformat"):
        return obj.isoformat()
    elif isinstance(obj, set):
        return list(obj)
    return obj
