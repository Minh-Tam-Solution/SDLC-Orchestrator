"""
Usage Limits Dashboard API — Sprint 212 Track F
SDLC Orchestrator - Stage 04 (BUILD -> DEPLOY)

Returns current resource usage vs tier limits for the authenticated user.

Metrics:
  - projects: count of user's projects (via project_members join)
  - storage_mb: sum of evidence file sizes across user's projects
  - gates_this_month: gates created in the current calendar month
  - members: unique team members across user's projects

Tier limits (ADR-059):
  LITE(1,100,4,1) STANDARD(10,1000,50,10)
  PROFESSIONAL(50,10000,500,50) ENTERPRISE(9999,100000,9999,9999)
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user
from app.db.session import get_db
from app.models.gate import Gate
from app.models.gate_evidence import GateEvidence
from app.models.project import ProjectMember
from app.models.user import User

router = APIRouter(prefix="/usage", tags=["Usage"])

# ── Tier limits (projects, storage_mb, gates/month, members) ──

TIER_LIMITS: dict[str, dict[str, int | float]] = {
    "lite":         {"projects": 1,    "storage_mb": 100,    "gates_month": 4,    "members": 1},
    "free":         {"projects": 1,    "storage_mb": 100,    "gates_month": 4,    "members": 1},
    "standard":     {"projects": 10,   "storage_mb": 1000,   "gates_month": 50,   "members": 10},
    "starter":      {"projects": 10,   "storage_mb": 1000,   "gates_month": 50,   "members": 10},
    "founder":      {"projects": 10,   "storage_mb": 1000,   "gates_month": 50,   "members": 10},
    "professional": {"projects": 50,   "storage_mb": 10000,  "gates_month": 500,  "members": 50},
    "pro":          {"projects": 50,   "storage_mb": 10000,  "gates_month": 500,  "members": 50},
    "enterprise":   {"projects": 9999, "storage_mb": 100000, "gates_month": 9999, "members": 9999},
}


# ── Response schema ──

class UsageBucket(BaseModel):
    current: float = Field(..., description="Current usage value")
    limit: float = Field(..., description="Tier limit")
    percent: float = Field(..., description="Usage percentage (0-100)")


class UsageStatsResponse(BaseModel):
    tier: str = Field(..., description="Effective subscription tier")
    usage: dict[str, UsageBucket] = Field(
        ..., description="Per-resource usage buckets"
    )


# ── Endpoint ──

@router.get(
    "/stats",
    response_model=UsageStatsResponse,
    summary="Current usage vs tier limits",
    description=(
        "Returns per-resource usage counters and the authenticated user's "
        "tier limits. Useful for dashboard quota bars and upgrade CTAs."
    ),
)
async def get_usage_stats(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> UsageStatsResponse:
    """
    Return current resource consumption against tier limits.

    Queries:
      1. projects  — COUNT of projects the user is a member of
      2. storage   — SUM(file_size) of evidence in those projects (bytes → MB)
      3. gates     — COUNT of gates created this calendar month
      4. members   — COUNT(DISTINCT user_id) across user's projects

    Args:
        current_user: Authenticated active user.
        db: Async database session.

    Returns:
        UsageStatsResponse with tier name and four usage buckets.
    """
    user_id = current_user.id
    tier = current_user.effective_tier
    limits = TIER_LIMITS.get(tier, TIER_LIMITS["lite"])

    # Sub-query: project IDs the user belongs to
    user_project_ids = (
        select(ProjectMember.project_id)
        .where(ProjectMember.user_id == user_id)
        .scalar_subquery()
    )

    # 1. Project count
    proj_result = await db.execute(
        select(func.count(distinct(ProjectMember.project_id)))
        .where(ProjectMember.user_id == user_id)
    )
    project_count: int = proj_result.scalar_one() or 0

    # 2. Storage (bytes → MB) from gate_evidence via gates in user's projects
    storage_result = await db.execute(
        select(func.coalesce(func.sum(GateEvidence.file_size), 0))
        .join(Gate, GateEvidence.gate_id == Gate.id)
        .where(
            Gate.project_id.in_(user_project_ids),
            GateEvidence.deleted_at.is_(None),
        )
    )
    storage_bytes: int = storage_result.scalar_one() or 0
    storage_mb = round(storage_bytes / (1024 * 1024), 1)

    # 3. Gates created this calendar month in user's projects
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    gates_result = await db.execute(
        select(func.count(Gate.id))
        .where(
            Gate.project_id.in_(user_project_ids),
            Gate.created_at >= month_start,
            Gate.deleted_at.is_(None),
        )
    )
    gates_count: int = gates_result.scalar_one() or 0

    # 4. Unique members across user's projects
    members_result = await db.execute(
        select(func.count(distinct(ProjectMember.user_id)))
        .where(ProjectMember.project_id.in_(user_project_ids))
    )
    member_count: int = members_result.scalar_one() or 0

    def _bucket(current: float, limit: float) -> UsageBucket:
        pct = round((current / limit) * 100, 1) if limit > 0 else 0.0
        return UsageBucket(current=current, limit=limit, percent=pct)

    return UsageStatsResponse(
        tier=tier,
        usage={
            "projects": _bucket(project_count, limits["projects"]),
            "storage_mb": _bucket(storage_mb, limits["storage_mb"]),
            "gates_this_month": _bucket(gates_count, limits["gates_month"]),
            "members": _bucket(member_count, limits["members"]),
        },
    )
