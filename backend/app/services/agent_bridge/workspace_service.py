"""
OTT Workspace Context Service — Redis CRUD for chat workspace bindings.

Sprint 207 — FR-049, ADR-067
Stores active project binding per (channel, chat_id) in a Redis HASH
with 7-day TTL. Governance commands auto-inject project_id from workspace.

Architecture (D-067-01):
    Redis = UX convenience cache.  PostgreSQL = control plane truth.
    Workspace NEVER caches permissions, gate status, or approval history.
    Every governance command re-verifies permissions against PostgreSQL.

Key format (D-067-02):
    ott:workspace:{channel}:{chat_id}  → HASH (7-day TTL)

Fields:
    project_id, project_name, tier, sdlc_stage, set_at, set_by
"""

from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

logger = logging.getLogger(__name__)

_WORKSPACE_KEY = "ott:workspace:{channel}:{chat_id}"
_WORKSPACE_TTL = 604_800  # 7 days in seconds


@dataclass(frozen=True)
class WorkspaceContext:
    """Active workspace binding for an OTT chat session (D-067-02)."""

    project_id: str
    project_name: str
    tier: str
    sdlc_stage: str
    set_at: str
    set_by: str


def _key(channel: str, chat_id: str | int) -> str:
    """Build Redis key from channel + chat_id."""
    return _WORKSPACE_KEY.format(channel=channel, chat_id=chat_id)


async def get_workspace(
    channel: str,
    chat_id: str | int,
    redis: Any,
) -> WorkspaceContext | None:
    """
    Read active workspace for a chat session.

    Returns None on any Redis error (graceful degradation per D-067-01).
    Caller falls through to OTT_DEFAULT_PROJECT_ID env var.
    """
    try:
        data: dict[str, str] = await redis.hgetall(_key(channel, chat_id))
        if not data:
            return None
        return WorkspaceContext(**data)
    except Exception:
        logger.warning(
            "workspace_service: Redis read failed channel=%s chat_id=%s",
            channel, chat_id, exc_info=True,
        )
        return None


async def set_workspace(
    channel: str,
    chat_id: str | int,
    project_id: str,
    project_name: str,
    tier: str,
    sdlc_stage: str,
    sender_id: str,
    redis: Any,
) -> None:
    """
    Set active workspace for a chat session.

    Raises on Redis failure — caller should display user-visible error
    per D-067-01 SET failure contract.
    """
    key = _key(channel, chat_id)
    mapping = {
        "project_id": str(project_id),
        "project_name": project_name,
        "tier": tier,
        "sdlc_stage": sdlc_stage,
        "set_at": datetime.now(timezone.utc).isoformat(),
        "set_by": str(sender_id),
    }
    await redis.hset(key, mapping=mapping)
    await redis.expire(key, _WORKSPACE_TTL)


async def clear_workspace(
    channel: str,
    chat_id: str | int,
    redis: Any,
) -> None:
    """
    Delete workspace binding for a chat session.

    Raises on Redis failure — caller should display user-visible error.
    """
    await redis.delete(_key(channel, chat_id))


async def touch_workspace_ttl(
    channel: str,
    chat_id: str | int,
    redis: Any,
) -> None:
    """
    Reset TTL on workspace key after successful governance command (D-067-02).

    Only called when workspace-injected project_id was used successfully.
    NOT called on explicit project_id, failure, or /workspace set.
    """
    try:
        await redis.expire(_key(channel, chat_id), _WORKSPACE_TTL)
    except Exception:
        logger.warning(
            "workspace_service: TTL touch failed channel=%s chat_id=%s",
            channel, chat_id, exc_info=True,
        )


_UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


def is_uuid(value: str) -> bool:
    """Check if a string looks like a UUID (36-char hyphenated hex)."""
    return bool(_UUID_RE.match(value.strip()))


async def resolve_project_by_name(
    name: str,
    user_id: str,
    db: Any,
) -> dict[str, Any]:
    """
    Search projects by name (ILIKE) with membership check.

    Returns:
        {"exact": Project | None, "matches": list[Project]}
        - exact: single match (workspace will be set)
        - matches: 2-5 results for disambiguation (workspace NOT set)

    Requires pg_trgm GIN index on projects.name (Alembic s207_001).
    """
    from sqlalchemy import select, func
    from app.models.project import Project, ProjectMember

    # Validate user_id is UUID to prevent injection
    try:
        UUID(user_id)
    except (ValueError, AttributeError):
        return {"exact": None, "matches": []}

    # Query projects where user is a member, name matches ILIKE
    stmt = (
        select(Project)
        .join(ProjectMember, ProjectMember.project_id == Project.id)
        .where(
            ProjectMember.user_id == user_id,
            Project.is_active.is_(True),
            Project.name.ilike(f"%{name}%"),
        )
        .order_by(func.length(Project.name))
        .limit(6)
    )
    result = await db.execute(stmt)
    projects = list(result.scalars().all())

    if len(projects) == 1:
        return {"exact": projects[0], "matches": projects}

    # Check for exact case-insensitive match among results
    exact = None
    for p in projects:
        if p.name.lower() == name.lower():
            exact = p
            break

    if exact:
        return {"exact": exact, "matches": [exact]}

    return {"exact": None, "matches": projects[:5]}


async def resolve_project_id(
    explicit_id: str | None,
    channel: str,
    chat_id: str | int,
    redis: Any,
) -> tuple[str | None, bool]:
    """
    Resolve project_id via 4-level priority chain (D-067-04).

    Returns:
        (project_id, workspace_used) — workspace_used=True means TTL should
        be reset on successful execution.

    Priority:
        1. Explicit from message
        2. Active workspace (Redis)
        3. OTT_DEFAULT_PROJECT_ID env var
        4. None (error)
    """
    # Priority 1: explicit from message
    if explicit_id:
        return explicit_id, False

    # Priority 2: workspace from Redis
    workspace = await get_workspace(channel, chat_id, redis)
    if workspace:
        return workspace.project_id, True

    # Priority 3: env var default
    default = os.getenv("OTT_DEFAULT_PROJECT_ID", "")
    if default:
        return default, False

    # Priority 4: error
    return None, False
