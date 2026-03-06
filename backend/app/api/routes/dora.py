"""
DORA Metrics Aggregation API — Sprint 211 Track C
SDLC Orchestrator

Derives the four DORA metrics from quality-gate lifecycle data:
  - Deployment Frequency  (APPROVED gates / week)
  - Lead Time for Changes (created_at → updated_at for APPROVED)
  - Mean Time to Restore  (REJECTED updated_at → next APPROVED updated_at)
  - Change Failure Rate   (REJECTED / (APPROVED + REJECTED))

Rating bands follow the 2023 State of DevOps Report thresholds.
"""

import re
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.gate import Gate
from app.models.user import User

router = APIRouter(prefix="/dora", tags=["DORA Metrics"])

_PERIOD_RE = re.compile(r"^(\d+)d$")
_ALLOWED_DAYS = {7, 30, 90}


def _parse_period(raw: str) -> int:
    m = _PERIOD_RE.match(raw)
    if not m or int(m.group(1)) not in _ALLOWED_DAYS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid period '{raw}'. Accepted values: 7d, 30d, 90d",
        )
    return int(m.group(1))


def _rate_df(per_week: float) -> str:
    if per_week >= 7:
        return "Elite"
    if per_week >= 1:
        return "High"
    if per_week >= 0.25:
        return "Medium"
    return "Low"


def _rate_lt(hours: float) -> str:
    if hours < 1:
        return "Elite"
    if hours < 24:
        return "High"
    if hours < 168:
        return "Medium"
    return "Low"


def _rate_mttr(hours: float) -> str:
    if hours < 1:
        return "Elite"
    if hours < 24:
        return "High"
    if hours < 168:
        return "Medium"
    return "Low"


def _rate_cfr(pct: float) -> str:
    if pct < 0.05:
        return "Elite"
    if pct < 0.15:
        return "High"
    if pct < 0.30:
        return "Medium"
    return "Low"


@router.get("/metrics")
async def get_dora_metrics(
    project_id: UUID = Query(..., description="Project UUID"),
    period: str = Query("30d", description="Time period: 7d, 30d, or 90d"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Return aggregated DORA metrics derived from gate lifecycle data."""

    days = _parse_period(period)
    cutoff = datetime.utcnow() - timedelta(days=days)

    # Fetch APPROVED + REJECTED gates in the period
    result = await db.execute(
        select(Gate)
        .where(
            and_(
                Gate.project_id == project_id,
                Gate.status.in_(["APPROVED", "REJECTED"]),
                Gate.updated_at >= cutoff,
                Gate.deleted_at.is_(None),
            )
        )
        .order_by(Gate.updated_at.asc())
    )
    gates = result.scalars().all()

    approved = [g for g in gates if g.status == "APPROVED"]
    rejected = [g for g in gates if g.status == "REJECTED"]

    total_weeks = max(days / 7, 1)

    # --- Deployment Frequency ---
    df_value = round(len(approved) / total_weeks, 2)

    # --- Lead Time (hours) ---
    lead_times: list[float] = []
    for g in approved:
        if g.created_at and g.updated_at:
            delta = (g.updated_at - g.created_at).total_seconds() / 3600
            lead_times.append(delta)
    lt_value = round(sum(lead_times) / len(lead_times), 1) if lead_times else 0.0

    # --- MTTR (hours) ---
    # For each REJECTED gate, find the next APPROVED gate on the same project
    mttr_values: list[float] = []
    for rg in rejected:
        next_approved = next(
            (ag for ag in approved if ag.updated_at and rg.updated_at and ag.updated_at > rg.updated_at),
            None,
        )
        if next_approved and next_approved.updated_at and rg.updated_at:
            delta = (next_approved.updated_at - rg.updated_at).total_seconds() / 3600
            mttr_values.append(delta)
    mttr_value = round(sum(mttr_values) / len(mttr_values), 1) if mttr_values else 0.0

    # --- Change Failure Rate ---
    total_decisions = len(approved) + len(rejected)
    cfr_value = round(len(rejected) / total_decisions, 4) if total_decisions else 0.0

    # --- Daily trend ---
    trend: list[dict[str, Any]] = []
    for offset in range(days):
        day_start = (datetime.utcnow() - timedelta(days=days - offset)).replace(
            hour=0, minute=0, second=0, microsecond=0,
        )
        day_end = day_start + timedelta(days=1)
        day_approved = [g for g in approved if day_start <= g.updated_at < day_end]
        day_rejected = [g for g in rejected if day_start <= g.updated_at < day_end]

        day_lt_list = [
            (g.updated_at - g.created_at).total_seconds() / 3600
            for g in day_approved
            if g.created_at and g.updated_at
        ]
        day_total = len(day_approved) + len(day_rejected)
        trend.append({
            "date": day_start.strftime("%Y-%m-%d"),
            "deployment_frequency": round(len(day_approved) * 7, 2),
            "lead_time_hours": round(sum(day_lt_list) / len(day_lt_list), 1) if day_lt_list else 0.0,
            "mttr_hours": 0.0,
            "change_failure_rate": round(len(day_rejected) / day_total, 4) if day_total else 0.0,
        })

    return {
        "project_id": str(project_id),
        "period_days": days,
        "metrics": {
            "deployment_frequency": {"value": df_value, "unit": "per_week", "rating": _rate_df(df_value)},
            "lead_time_hours": {"value": lt_value, "unit": "hours", "rating": _rate_lt(lt_value)},
            "mttr_hours": {"value": mttr_value, "unit": "hours", "rating": _rate_mttr(mttr_value)},
            "change_failure_rate": {"value": cfr_value, "unit": "percentage", "rating": _rate_cfr(cfr_value)},
        },
        "trend": trend,
    }
