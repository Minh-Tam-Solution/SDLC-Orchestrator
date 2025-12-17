"""
File: backend/app/api/routes/dashboard.py
Version: 1.1.0
Status: ACTIVE - STAGE 03 (BUILD)
Date: 2025-12-16
Authority: Backend Lead + CTO Approved
Foundation: SDLC 5.1.1 Complete Lifecycle, Zero Mock Policy

Description:
Dashboard API routes for SDLC Orchestrator.
Provides statistics and recent activity data.

Design References:
- Data Model: docs/01-planning/03-Data-Model/Database-Schema.md
- Gate Model: backend/app/models/gate.py (source of truth for status values)
- Gate Status: DRAFT | PENDING_APPROVAL | IN_PROGRESS | APPROVED | REJECTED | ARCHIVED

Changelog:
- v1.1.0 (2025-12-16): Normalize status values to UPPERCASE per gate.py model
- v1.0.0 (2025-11-27): Initial implementation
"""

from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.project import Project
from app.models.gate import Gate
from app.api.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats")
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get dashboard statistics.

    Returns:
        - total_projects: Total number of projects
        - active_gates: Gates with pending status
        - pending_approvals: Gates awaiting approval
        - pass_rate: Percentage of approved gates
    """
    # Total projects
    total_projects_result = await db.execute(
        select(func.count(Project.id)).where(Project.deleted_at.is_(None))
    )
    total_projects = total_projects_result.scalar() or 0

    # Active gates (PENDING, PENDING_APPROVAL, IN_PROGRESS)
    # Note: All status values are normalized to UPPERCASE in database
    active_gates_result = await db.execute(
        select(func.count(Gate.id)).where(
            Gate.deleted_at.is_(None),
            Gate.status.in_(["PENDING", "PENDING_APPROVAL", "IN_PROGRESS"]),
        )
    )
    active_gates = active_gates_result.scalar() or 0

    # Pending approvals (PENDING_APPROVAL only)
    pending_approvals_result = await db.execute(
        select(func.count(Gate.id)).where(
            Gate.deleted_at.is_(None),
            Gate.status == "PENDING_APPROVAL",
        )
    )
    pending_approvals = pending_approvals_result.scalar() or 0

    # Calculate pass rate (APPROVED / (APPROVED + REJECTED))
    total_gates_result = await db.execute(
        select(func.count(Gate.id)).where(
            Gate.deleted_at.is_(None),
            Gate.status.in_(["APPROVED", "REJECTED"]),
        )
    )
    total_evaluated = total_gates_result.scalar() or 0

    approved_gates_result = await db.execute(
        select(func.count(Gate.id)).where(
            Gate.deleted_at.is_(None),
            Gate.status == "APPROVED",
        )
    )
    approved_gates = approved_gates_result.scalar() or 0

    pass_rate = round((approved_gates / total_evaluated * 100) if total_evaluated > 0 else 0)

    return {
        "total_projects": total_projects,
        "active_gates": active_gates,
        "pending_approvals": pending_approvals,
        "pass_rate": pass_rate,
    }


@router.get("/recent-gates")
async def get_recent_gates(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = 5,
):
    """
    Get recent gate activity.

    Returns list of recent gates with project info.
    """
    result = await db.execute(
        select(Gate, Project)
        .join(Project, Gate.project_id == Project.id)
        .where(Gate.deleted_at.is_(None))
        .order_by(Gate.updated_at.desc())
        .limit(limit)
    )
    rows = result.all()

    gates = []
    for gate, project in rows:
        # Map status to frontend format
        status_map = {
            "APPROVED": "passed",
            "REJECTED": "failed",
            "PENDING": "pending",
            "PENDING_APPROVAL": "pending",
            "IN_PROGRESS": "pending",
        }
        gates.append({
            "id": str(gate.id),
            "gate_name": gate.gate_name,
            "project_name": project.name,
            "status": status_map.get(gate.status, "pending"),
            "updated_at": gate.updated_at.isoformat() if gate.updated_at else None,
        })

    return gates
