"""
=========================================================================
Planning Hierarchy API Routes - SDLC Orchestrator
Sprint 74: Planning Hierarchy Implementation
Sprint 75: Team Role Authorization for Gate Approval

Version: 1.1.0
Date: January 18, 2026
Status: ACTIVE - Sprint 75 Enhancement
Authority: Backend Lead + CTO Approved
Reference: ADR-013-Planning-Hierarchy
Reference: SDLC-Sprint-Planning-Governance.md (SDLC 5.1.3)

Endpoints:
- /roadmaps: Roadmap CRUD (strategic planning)
- /phases: Phase CRUD (4-8 week themes)
- /sprints: Sprint CRUD + G-Sprint/G-Sprint-Close gates
- /backlog: Backlog item CRUD (stories, tasks, bugs)

SDLC 5.1.3 Compliance:
- G-Sprint Gate validation before sprint start
- G-Sprint-Close Gate validation with 24h documentation deadline
- Immutable sprint numbering (Rule #1)
- Traceability chain enforcement
- Team role authorization for gate approval (SE4H Coach only)

Sprint 75 Enhancement:
- check_sprint_gate_authorization() - Team-based gate approval validation
- Only SE4H Coach (team owner/admin) can approve sprint gates
- AI agents (SE4A) cannot approve governance gates
- Human oversight enforcement for SDLC 5.1.3

Zero Mock Policy: Production-ready FastAPI routes
=========================================================================
"""

from datetime import datetime, timedelta
from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
import sqlalchemy as sa
from sqlalchemy import func, select, Integer, cast
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.backlog_item import BacklogItem
from app.models.phase import Phase
from app.models.project import Project, ProjectMember
from app.models.roadmap import Roadmap
from app.models.sprint import Sprint
from app.models.sprint_gate_evaluation import (
    SprintGateEvaluation,
    G_SPRINT_CHECKLIST_TEMPLATE,
    G_SPRINT_CLOSE_CHECKLIST_TEMPLATE,
)
from app.models.team import Team
from app.models.team_member import TeamMember
from app.models.user import User
from app.services.backlog_service import (
    BacklogService,
    AssigneeNotTeamMemberError,
)
from app.services.sprint_assistant import (
    SprintAssistantService,
    get_sprint_assistant_service,
)
from app.schemas.planning import (
    # Roadmap
    RoadmapCreate,
    RoadmapUpdate,
    RoadmapResponse,
    RoadmapListResponse,
    # Phase
    PhaseCreate,
    PhaseUpdate,
    PhaseResponse,
    PhaseListResponse,
    # Sprint
    SprintCreate,
    SprintUpdate,
    SprintResponse,
    SprintListResponse,
    # Gate Evaluation
    GateEvaluationCreate,
    GateEvaluationUpdate,
    GateEvaluationSubmit,
    GateEvaluationResponse,
    GateType,
    GateStatus,
    # Backlog
    BacklogItemCreate,
    BacklogItemUpdate,
    BacklogItemResponse,
    BacklogItemListResponse,
    Priority,
    # Bulk Operations
    BulkMoveToSprint,
    BulkUpdatePriority,
    BulkOperationResult,
    # Dashboard
    PlanningDashboard,
    RoadmapHierarchy,
    PhaseSummary,
    SprintSummary,
    # Analytics (Sprint 76)
    VelocityMetricsResponse,
    SprintHealthResponse,
    PrioritySuggestionResponse,
    SprintSuggestionsResponse,
    SprintAnalyticsResponse,
)


# =========================================================================
# Router Configuration
# =========================================================================

router = APIRouter(prefix="/planning", tags=["Planning Hierarchy"])


# =========================================================================
# Helper Functions
# =========================================================================


async def check_project_access(
    db: AsyncSession,
    project_id: UUID,
    user: User,
    require_write: bool = False,
) -> Project:
    """Check if user has access to the project."""
    result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.deleted_at.is_(None),
        )
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    if require_write:
        member_result = await db.execute(
            select(ProjectMember).where(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == user.id,
                ProjectMember.role.in_(["owner", "admin", "developer"]),
            )
        )
        member = member_result.scalar_one_or_none()

        if not member and not user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to modify this project",
            )

    return project


async def check_sprint_gate_authorization(
    db: AsyncSession,
    sprint: Sprint,
    user: User,
) -> None:
    """
    Check if user can approve sprint gates (G-Sprint/G-Sprint-Close).

    SDLC 5.1.3 Sprint Planning Governance (Sprint 75):
    - If project has team: user must be team owner/admin (SE4H Coach)
    - If project has no team: user must be project owner
    - AI agents (SE4A) cannot approve gates

    Args:
        db: Database session
        sprint: Sprint to check authorization for
        user: Current user

    Raises:
        HTTPException: 403 if user is not authorized
    """
    # Get project with team relation
    project_result = await db.execute(
        select(Project)
        .options(selectinload(Project.team).selectinload(Team.members))
        .where(Project.id == sprint.project_id)
    )
    project = project_result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    # Superuser bypass
    if user.is_superuser:
        return

    # If project has team, check team role authorization
    if project.team:
        team_member = None
        for member in project.team.members:
            if member.user_id == user.id and member.deleted_at is None:
                team_member = member
                break

        if not team_member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a member of the project team",
            )

        if not team_member.can_approve_sprint_gate:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{team_member.role}' cannot approve sprint gates. "
                       f"Only team owner/admin (SE4H Coach) can approve.",
            )
        return

    # Fallback: project without team - check project owner
    if project.owner_id == user.id:
        return

    # Check if user is project admin
    member_result = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project.id,
            ProjectMember.user_id == user.id,
            ProjectMember.role.in_(["owner", "admin"]),
        )
    )
    member = member_result.scalar_one_or_none()

    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only project owner/admin can approve gates for projects without team",
        )


def serialize_roadmap(roadmap: Roadmap, phases_count: int = 0) -> dict:
    """Serialize roadmap to response dict."""
    return {
        "id": roadmap.id,
        "project_id": roadmap.project_id,
        "name": roadmap.name,
        "description": roadmap.description,
        "vision": roadmap.vision,
        "start_date": roadmap.start_date,
        "end_date": roadmap.end_date,
        "review_cadence": roadmap.review_cadence,
        "status": roadmap.status,
        "phases_count": phases_count,
        "created_by": roadmap.created_by,
        "created_at": roadmap.created_at,
        "updated_at": roadmap.updated_at,
    }


def serialize_phase(phase: Phase, sprints_count: int = 0) -> dict:
    """Serialize phase to response dict."""
    return {
        "id": phase.id,
        "roadmap_id": phase.roadmap_id,
        "number": phase.number,
        "name": phase.name,
        "theme": phase.theme,
        "objective": phase.objective,
        "start_date": phase.start_date,
        "end_date": phase.end_date,
        "status": phase.status,
        "sprints_count": sprints_count,
        "created_at": phase.created_at,
        "updated_at": phase.updated_at,
    }


def serialize_sprint(sprint: Sprint, backlog_count: int = 0) -> dict:
    """Serialize sprint to response dict."""
    return {
        "id": sprint.id,
        "project_id": sprint.project_id,
        "phase_id": sprint.phase_id,
        "number": sprint.number,
        "name": sprint.name,
        "goal": sprint.goal,
        "status": sprint.status,
        "start_date": sprint.start_date,
        "end_date": sprint.end_date,
        "capacity_points": sprint.capacity_points,
        "team_size": sprint.team_size,
        "velocity_target": sprint.velocity_target,
        "g_sprint_status": sprint.g_sprint_status,
        "g_sprint_approved_by": sprint.g_sprint_approved_by,
        "g_sprint_approved_at": sprint.g_sprint_approved_at,
        "g_sprint_close_status": sprint.g_sprint_close_status,
        "g_sprint_close_approved_by": sprint.g_sprint_close_approved_by,
        "g_sprint_close_approved_at": sprint.g_sprint_close_approved_at,
        "documentation_deadline": sprint.documentation_deadline,
        "backlog_items_count": backlog_count,
        "can_start": sprint.can_start,
        "can_close": sprint.can_close,
        "documentation_overdue": sprint.documentation_overdue,
        "created_by": sprint.created_by,
        "created_at": sprint.created_at,
        "updated_at": sprint.updated_at,
    }


def serialize_backlog_item(item: BacklogItem, subtasks_count: int = 0) -> dict:
    """Serialize backlog item to response dict."""
    return {
        "id": item.id,
        "project_id": item.project_id,
        "sprint_id": item.sprint_id,
        "parent_id": item.parent_id,
        "type": item.type,
        "title": item.title,
        "description": item.description,
        "acceptance_criteria": item.acceptance_criteria,
        "priority": item.priority,
        "story_points": item.story_points,
        "status": item.status,
        "assignee_id": item.assignee_id,
        "labels": item.labels or [],
        "subtasks_count": subtasks_count,
        "created_by": item.created_by,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
    }


# =========================================================================
# Roadmap Endpoints
# =========================================================================


@router.post("/roadmaps", status_code=status.HTTP_201_CREATED)
async def create_roadmap(
    data: RoadmapCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RoadmapResponse:
    """
    Create a new roadmap for a project.

    Roadmaps represent strategic 12-month planning with quarterly review cadence.
    """
    await check_project_access(db, data.project_id, current_user, require_write=True)

    # Check for duplicate name within project
    existing = await db.execute(
        select(Roadmap).where(
            Roadmap.project_id == data.project_id,
            Roadmap.name == data.name,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Roadmap with name '{data.name}' already exists in this project",
        )

    roadmap = Roadmap(
        project_id=data.project_id,
        name=data.name,
        description=data.description,
        vision=data.vision,
        start_date=data.start_date,
        end_date=data.end_date,
        review_cadence=data.review_cadence.value,
        status="active",
        created_by=current_user.id,
    )
    db.add(roadmap)
    await db.commit()
    await db.refresh(roadmap)

    return serialize_roadmap(roadmap)


@router.get("/roadmaps")
async def list_roadmaps(
    project_id: UUID = Query(..., description="Project UUID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RoadmapListResponse:
    """List roadmaps for a project."""
    await check_project_access(db, project_id, current_user)

    query = select(Roadmap).where(Roadmap.project_id == project_id)
    if status:
        query = query.where(Roadmap.status == status)

    # Count total
    count_result = await db.execute(
        select(func.count(Roadmap.id)).where(Roadmap.project_id == project_id)
    )
    total = count_result.scalar() or 0

    # Get paginated results with phase counts
    query = query.order_by(Roadmap.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    roadmaps = result.scalars().all()

    items = []
    for roadmap in roadmaps:
        # Count phases
        phases_count_result = await db.execute(
            select(func.count(Phase.id)).where(Phase.roadmap_id == roadmap.id)
        )
        phases_count = phases_count_result.scalar() or 0
        items.append(serialize_roadmap(roadmap, phases_count))

    return RoadmapListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        has_next=(page * page_size) < total,
    )


@router.get("/roadmaps/{roadmap_id}")
async def get_roadmap(
    roadmap_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RoadmapResponse:
    """Get a single roadmap by ID."""
    result = await db.execute(
        select(Roadmap).where(Roadmap.id == roadmap_id)
    )
    roadmap = result.scalar_one_or_none()

    if not roadmap:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Roadmap not found",
        )

    await check_project_access(db, roadmap.project_id, current_user)

    phases_count_result = await db.execute(
        select(func.count(Phase.id)).where(Phase.roadmap_id == roadmap.id)
    )
    phases_count = phases_count_result.scalar() or 0

    return serialize_roadmap(roadmap, phases_count)


@router.put("/roadmaps/{roadmap_id}")
async def update_roadmap(
    roadmap_id: UUID,
    data: RoadmapUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RoadmapResponse:
    """Update a roadmap."""
    result = await db.execute(
        select(Roadmap).where(Roadmap.id == roadmap_id)
    )
    roadmap = result.scalar_one_or_none()

    if not roadmap:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Roadmap not found",
        )

    await check_project_access(db, roadmap.project_id, current_user, require_write=True)

    # Update fields
    if data.name is not None:
        roadmap.name = data.name
    if data.description is not None:
        roadmap.description = data.description
    if data.vision is not None:
        roadmap.vision = data.vision
    if data.start_date is not None:
        roadmap.start_date = data.start_date
    if data.end_date is not None:
        roadmap.end_date = data.end_date
    if data.review_cadence is not None:
        roadmap.review_cadence = data.review_cadence.value
    if data.status is not None:
        roadmap.status = data.status.value

    roadmap.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(roadmap)

    phases_count_result = await db.execute(
        select(func.count(Phase.id)).where(Phase.roadmap_id == roadmap.id)
    )
    phases_count = phases_count_result.scalar() or 0

    return serialize_roadmap(roadmap, phases_count)


@router.delete("/roadmaps/{roadmap_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_roadmap(
    roadmap_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a roadmap (cascades to phases)."""
    result = await db.execute(
        select(Roadmap).where(Roadmap.id == roadmap_id)
    )
    roadmap = result.scalar_one_or_none()

    if not roadmap:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Roadmap not found",
        )

    await check_project_access(db, roadmap.project_id, current_user, require_write=True)

    await db.delete(roadmap)
    await db.commit()


# =========================================================================
# Phase Endpoints
# =========================================================================


@router.post("/phases", status_code=status.HTTP_201_CREATED)
async def create_phase(
    data: PhaseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PhaseResponse:
    """Create a new phase within a roadmap."""
    # Check roadmap exists
    roadmap_result = await db.execute(
        select(Roadmap).where(Roadmap.id == data.roadmap_id)
    )
    roadmap = roadmap_result.scalar_one_or_none()

    if not roadmap:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Roadmap not found",
        )

    await check_project_access(db, roadmap.project_id, current_user, require_write=True)

    # Check for duplicate phase number
    existing = await db.execute(
        select(Phase).where(
            Phase.roadmap_id == data.roadmap_id,
            Phase.number == data.number,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Phase {data.number} already exists in this roadmap",
        )

    phase = Phase(
        roadmap_id=data.roadmap_id,
        number=data.number,
        name=data.name,
        theme=data.theme,
        objective=data.objective,
        start_date=data.start_date,
        end_date=data.end_date,
        status="planned",
    )
    db.add(phase)
    await db.commit()
    await db.refresh(phase)

    return serialize_phase(phase)


@router.get("/phases")
async def list_phases(
    roadmap_id: UUID = Query(..., description="Roadmap UUID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PhaseListResponse:
    """List phases for a roadmap."""
    # Check roadmap exists
    roadmap_result = await db.execute(
        select(Roadmap).where(Roadmap.id == roadmap_id)
    )
    roadmap = roadmap_result.scalar_one_or_none()

    if not roadmap:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Roadmap not found",
        )

    await check_project_access(db, roadmap.project_id, current_user)

    query = select(Phase).where(Phase.roadmap_id == roadmap_id)
    if status:
        query = query.where(Phase.status == status)

    # Count total
    count_result = await db.execute(
        select(func.count(Phase.id)).where(Phase.roadmap_id == roadmap_id)
    )
    total = count_result.scalar() or 0

    # Get paginated results
    query = query.order_by(Phase.number)
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    phases = result.scalars().all()

    items = []
    for phase in phases:
        sprints_count_result = await db.execute(
            select(func.count(Sprint.id)).where(Sprint.phase_id == phase.id)
        )
        sprints_count = sprints_count_result.scalar() or 0
        items.append(serialize_phase(phase, sprints_count))

    return PhaseListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        has_next=(page * page_size) < total,
    )


@router.get("/phases/{phase_id}")
async def get_phase(
    phase_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PhaseResponse:
    """Get a single phase by ID."""
    result = await db.execute(
        select(Phase).options(selectinload(Phase.roadmap)).where(Phase.id == phase_id)
    )
    phase = result.scalar_one_or_none()

    if not phase:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Phase not found",
        )

    await check_project_access(db, phase.roadmap.project_id, current_user)

    sprints_count_result = await db.execute(
        select(func.count(Sprint.id)).where(Sprint.phase_id == phase.id)
    )
    sprints_count = sprints_count_result.scalar() or 0

    return serialize_phase(phase, sprints_count)


@router.put("/phases/{phase_id}")
async def update_phase(
    phase_id: UUID,
    data: PhaseUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PhaseResponse:
    """Update a phase."""
    result = await db.execute(
        select(Phase).options(selectinload(Phase.roadmap)).where(Phase.id == phase_id)
    )
    phase = result.scalar_one_or_none()

    if not phase:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Phase not found",
        )

    await check_project_access(db, phase.roadmap.project_id, current_user, require_write=True)

    if data.name is not None:
        phase.name = data.name
    if data.theme is not None:
        phase.theme = data.theme
    if data.objective is not None:
        phase.objective = data.objective
    if data.start_date is not None:
        phase.start_date = data.start_date
    if data.end_date is not None:
        phase.end_date = data.end_date
    if data.status is not None:
        phase.status = data.status.value

    phase.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(phase)

    sprints_count_result = await db.execute(
        select(func.count(Sprint.id)).where(Sprint.phase_id == phase.id)
    )
    sprints_count = sprints_count_result.scalar() or 0

    return serialize_phase(phase, sprints_count)


@router.delete("/phases/{phase_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_phase(
    phase_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a phase."""
    result = await db.execute(
        select(Phase).options(selectinload(Phase.roadmap)).where(Phase.id == phase_id)
    )
    phase = result.scalar_one_or_none()

    if not phase:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Phase not found",
        )

    await check_project_access(db, phase.roadmap.project_id, current_user, require_write=True)

    await db.delete(phase)
    await db.commit()


# =========================================================================
# Sprint Endpoints
# =========================================================================


@router.post("/sprints", status_code=status.HTTP_201_CREATED)
async def create_sprint(
    data: SprintCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SprintResponse:
    """
    Create a new sprint.

    SDLC 5.1.3 Rule #1: Sprint numbers are immutable after creation.
    """
    await check_project_access(db, data.project_id, current_user, require_write=True)

    # Check for duplicate sprint number in project (Rule #1: Immutable)
    existing = await db.execute(
        select(Sprint).where(
            Sprint.project_id == data.project_id,
            Sprint.number == data.number,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Sprint {data.number} already exists in this project. "
            f"Sprint numbers are immutable per SDLC 5.1.3 Rule #1.",
        )

    # Validate phase belongs to project if provided
    if data.phase_id:
        phase_result = await db.execute(
            select(Phase).options(selectinload(Phase.roadmap)).where(Phase.id == data.phase_id)
        )
        phase = phase_result.scalar_one_or_none()
        if not phase or phase.roadmap.project_id != data.project_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phase does not belong to this project",
            )

    sprint = Sprint(
        project_id=data.project_id,
        phase_id=data.phase_id,
        number=data.number,
        name=data.name,
        goal=data.goal,
        status="planning",
        start_date=data.start_date,
        end_date=data.end_date,
        capacity_points=data.capacity_points,
        team_size=data.team_size,
        velocity_target=data.velocity_target,
        g_sprint_status="pending",
        g_sprint_close_status="pending",
        created_by=current_user.id,
    )
    db.add(sprint)
    await db.commit()
    await db.refresh(sprint)

    return serialize_sprint(sprint)


@router.get("/sprints")
async def list_sprints(
    project_id: UUID = Query(..., description="Project UUID"),
    phase_id: Optional[UUID] = Query(None, description="Filter by phase"),
    status: Optional[str] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SprintListResponse:
    """List sprints for a project."""
    await check_project_access(db, project_id, current_user)

    query = select(Sprint).where(Sprint.project_id == project_id)
    if phase_id:
        query = query.where(Sprint.phase_id == phase_id)
    if status:
        query = query.where(Sprint.status == status)

    # Count total
    count_query = select(func.count(Sprint.id)).where(Sprint.project_id == project_id)
    if phase_id:
        count_query = count_query.where(Sprint.phase_id == phase_id)
    if status:
        count_query = count_query.where(Sprint.status == status)
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    # Get paginated results
    query = query.order_by(Sprint.number.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    sprints = result.scalars().all()

    items = []
    for sprint in sprints:
        backlog_count_result = await db.execute(
            select(func.count(BacklogItem.id)).where(BacklogItem.sprint_id == sprint.id)
        )
        backlog_count = backlog_count_result.scalar() or 0
        items.append(serialize_sprint(sprint, backlog_count))

    return SprintListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        has_next=(page * page_size) < total,
    )


@router.get("/sprints/{sprint_id}")
async def get_sprint(
    sprint_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SprintResponse:
    """Get a single sprint by ID."""
    result = await db.execute(
        select(Sprint).where(Sprint.id == sprint_id)
    )
    sprint = result.scalar_one_or_none()

    if not sprint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sprint not found",
        )

    await check_project_access(db, sprint.project_id, current_user)

    backlog_count_result = await db.execute(
        select(func.count(BacklogItem.id)).where(BacklogItem.sprint_id == sprint.id)
    )
    backlog_count = backlog_count_result.scalar() or 0

    return serialize_sprint(sprint, backlog_count)


@router.put("/sprints/{sprint_id}")
async def update_sprint(
    sprint_id: UUID,
    data: SprintUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SprintResponse:
    """
    Update a sprint.

    Note: Sprint number cannot be changed (Rule #1: Immutable).
    """
    result = await db.execute(
        select(Sprint).where(Sprint.id == sprint_id)
    )
    sprint = result.scalar_one_or_none()

    if not sprint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sprint not found",
        )

    await check_project_access(db, sprint.project_id, current_user, require_write=True)

    if data.phase_id is not None:
        sprint.phase_id = data.phase_id
    if data.name is not None:
        sprint.name = data.name
    if data.goal is not None:
        sprint.goal = data.goal
    if data.start_date is not None:
        sprint.start_date = data.start_date
    if data.end_date is not None:
        sprint.end_date = data.end_date
        # Set documentation deadline (Rule #2: 24h after end_date)
        sprint.documentation_deadline = datetime.combine(
            data.end_date, datetime.min.time()
        ) + timedelta(hours=24)
    if data.capacity_points is not None:
        sprint.capacity_points = data.capacity_points
    if data.team_size is not None:
        sprint.team_size = data.team_size
    if data.velocity_target is not None:
        sprint.velocity_target = data.velocity_target
    if data.status is not None:
        sprint.status = data.status.value

    sprint.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(sprint)

    backlog_count_result = await db.execute(
        select(func.count(BacklogItem.id)).where(BacklogItem.sprint_id == sprint.id)
    )
    backlog_count = backlog_count_result.scalar() or 0

    return serialize_sprint(sprint, backlog_count)


@router.delete("/sprints/{sprint_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sprint(
    sprint_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete a sprint.

    Warning: Deleting a sprint moves all backlog items back to the product backlog.
    """
    result = await db.execute(
        select(Sprint).where(Sprint.id == sprint_id)
    )
    sprint = result.scalar_one_or_none()

    if not sprint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sprint not found",
        )

    await check_project_access(db, sprint.project_id, current_user, require_write=True)

    # Move backlog items to product backlog (sprint_id = NULL)
    await db.execute(
        BacklogItem.__table__.update()
        .where(BacklogItem.sprint_id == sprint_id)
        .values(sprint_id=None, updated_at=datetime.utcnow())
    )

    await db.delete(sprint)
    await db.commit()


# =========================================================================
# Sprint Gate Evaluation Endpoints (G-Sprint / G-Sprint-Close)
# =========================================================================


@router.post("/sprints/{sprint_id}/gates", status_code=status.HTTP_201_CREATED)
async def create_gate_evaluation(
    sprint_id: UUID,
    data: GateEvaluationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> GateEvaluationResponse:
    """
    Create a gate evaluation for a sprint.

    Gate types:
    - g_sprint: Sprint Planning Gate (before sprint starts)
    - g_sprint_close: Sprint Completion Gate (before sprint closes)
    """
    result = await db.execute(
        select(Sprint).where(Sprint.id == sprint_id)
    )
    sprint = result.scalar_one_or_none()

    if not sprint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sprint not found",
        )

    await check_project_access(db, sprint.project_id, current_user, require_write=True)

    # Check if evaluation already exists
    existing = await db.execute(
        select(SprintGateEvaluation).where(
            SprintGateEvaluation.sprint_id == sprint_id,
            SprintGateEvaluation.gate_type == data.gate_type.value,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Gate evaluation for {data.gate_type.value} already exists",
        )

    # Create evaluation with appropriate template
    if data.gate_type == GateType.G_SPRINT:
        evaluation = SprintGateEvaluation.create_g_sprint_evaluation(sprint_id)
    else:
        evaluation = SprintGateEvaluation.create_g_sprint_close_evaluation(sprint_id)

    db.add(evaluation)
    await db.commit()
    await db.refresh(evaluation)

    return _serialize_gate_evaluation(evaluation)


@router.get("/sprints/{sprint_id}/gates")
async def list_gate_evaluations(
    sprint_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[GateEvaluationResponse]:
    """List all gate evaluations for a sprint."""
    result = await db.execute(
        select(Sprint).where(Sprint.id == sprint_id)
    )
    sprint = result.scalar_one_or_none()

    if not sprint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sprint not found",
        )

    await check_project_access(db, sprint.project_id, current_user)

    evals_result = await db.execute(
        select(SprintGateEvaluation).where(SprintGateEvaluation.sprint_id == sprint_id)
    )
    evaluations = evals_result.scalars().all()

    return [_serialize_gate_evaluation(e) for e in evaluations]


@router.get("/sprints/{sprint_id}/gates/{gate_type}")
async def get_gate_evaluation(
    sprint_id: UUID,
    gate_type: GateType,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> GateEvaluationResponse:
    """Get a specific gate evaluation."""
    result = await db.execute(
        select(Sprint).where(Sprint.id == sprint_id)
    )
    sprint = result.scalar_one_or_none()

    if not sprint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sprint not found",
        )

    await check_project_access(db, sprint.project_id, current_user)

    eval_result = await db.execute(
        select(SprintGateEvaluation).where(
            SprintGateEvaluation.sprint_id == sprint_id,
            SprintGateEvaluation.gate_type == gate_type.value,
        )
    )
    evaluation = eval_result.scalar_one_or_none()

    if not evaluation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Gate evaluation for {gate_type.value} not found",
        )

    return _serialize_gate_evaluation(evaluation)


@router.put("/sprints/{sprint_id}/gates/{gate_type}")
async def update_gate_evaluation(
    sprint_id: UUID,
    gate_type: GateType,
    data: GateEvaluationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> GateEvaluationResponse:
    """Update gate evaluation checklist items."""
    result = await db.execute(
        select(Sprint).where(Sprint.id == sprint_id)
    )
    sprint = result.scalar_one_or_none()

    if not sprint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sprint not found",
        )

    await check_project_access(db, sprint.project_id, current_user, require_write=True)

    eval_result = await db.execute(
        select(SprintGateEvaluation).where(
            SprintGateEvaluation.sprint_id == sprint_id,
            SprintGateEvaluation.gate_type == gate_type.value,
        )
    )
    evaluation = eval_result.scalar_one_or_none()

    if not evaluation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Gate evaluation for {gate_type.value} not found",
        )

    if evaluation.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update a finalized gate evaluation",
        )

    evaluation.checklist = data.checklist
    if data.notes is not None:
        evaluation.notes = data.notes

    await db.commit()
    await db.refresh(evaluation)

    return _serialize_gate_evaluation(evaluation)


@router.post("/sprints/{sprint_id}/gates/{gate_type}/submit")
async def submit_gate_evaluation(
    sprint_id: UUID,
    gate_type: GateType,
    data: GateEvaluationSubmit,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> GateEvaluationResponse:
    """
    Submit gate evaluation for approval.

    SDLC 5.1.3 Sprint Planning Governance (Sprint 75):
    - Only team owner/admin (SE4H Coach) can approve sprint gates
    - AI agents (SE4A) cannot approve gates
    - This enforces human oversight for sprint governance

    The gate passes only if all checklist items are checked.
    This also updates the sprint's gate status.
    """
    result = await db.execute(
        select(Sprint).where(Sprint.id == sprint_id)
    )
    sprint = result.scalar_one_or_none()

    if not sprint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sprint not found",
        )

    # Sprint 75: Team role authorization for gate approval
    # Only SE4H Coach (team owner/admin) can approve sprint gates
    await check_sprint_gate_authorization(db, sprint, current_user)

    eval_result = await db.execute(
        select(SprintGateEvaluation).where(
            SprintGateEvaluation.sprint_id == sprint_id,
            SprintGateEvaluation.gate_type == gate_type.value,
        )
    )
    evaluation = eval_result.scalar_one_or_none()

    if not evaluation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Gate evaluation for {gate_type.value} not found",
        )

    if evaluation.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Gate evaluation already submitted",
        )

    # Finalize evaluation
    if data.notes:
        evaluation.notes = data.notes
    evaluation.finalize_evaluation(current_user.id)

    # Update sprint gate status
    if gate_type == GateType.G_SPRINT:
        sprint.g_sprint_status = evaluation.status
        sprint.g_sprint_approved_by = current_user.id if evaluation.status == "passed" else None
        sprint.g_sprint_approved_at = datetime.utcnow() if evaluation.status == "passed" else None
    else:
        sprint.g_sprint_close_status = evaluation.status
        sprint.g_sprint_close_approved_by = current_user.id if evaluation.status == "passed" else None
        sprint.g_sprint_close_approved_at = datetime.utcnow() if evaluation.status == "passed" else None

    await db.commit()
    await db.refresh(evaluation)

    return _serialize_gate_evaluation(evaluation)


def _serialize_gate_evaluation(evaluation: SprintGateEvaluation) -> dict:
    """Serialize gate evaluation to response dict."""
    checked = 0
    total = 0
    for category_items in evaluation.checklist.values():
        for item in category_items:
            total += 1
            if item.get("checked", False):
                checked += 1

    return {
        "id": evaluation.id,
        "sprint_id": evaluation.sprint_id,
        "gate_type": evaluation.gate_type,
        "status": evaluation.status,
        "checklist": evaluation.checklist,
        "notes": evaluation.notes,
        "evaluated_by": evaluation.evaluated_by,
        "evaluated_at": evaluation.evaluated_at,
        "created_at": evaluation.created_at,
        "all_items_checked": checked == total and total > 0,
        "checked_count": checked,
        "total_count": total,
    }


# =========================================================================
# Backlog Item Endpoints
# =========================================================================


@router.post("/backlog", status_code=status.HTTP_201_CREATED)
async def create_backlog_item(
    data: BacklogItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BacklogItemResponse:
    """
    Create a new backlog item (story, task, bug, spike).

    SDLC 5.1.3 GAP 2 Resolution (Sprint 76):
    - If assignee_id is provided, validates that assignee is a team member
    - Projects without teams allow any assignee (backward compatibility)
    """
    await check_project_access(db, data.project_id, current_user, require_write=True)

    # Validate sprint belongs to project if provided
    if data.sprint_id:
        sprint_result = await db.execute(
            select(Sprint).where(Sprint.id == data.sprint_id)
        )
        sprint = sprint_result.scalar_one_or_none()
        if not sprint or sprint.project_id != data.project_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Sprint does not belong to this project",
            )

    # Validate parent item belongs to same project if provided
    if data.parent_id:
        parent_result = await db.execute(
            select(BacklogItem).where(BacklogItem.id == data.parent_id)
        )
        parent = parent_result.scalar_one_or_none()
        if not parent or parent.project_id != data.project_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Parent item does not belong to this project",
            )

    # GAP 2 Resolution: Validate assignee is team member
    if data.assignee_id:
        backlog_service = BacklogService(db)
        try:
            await backlog_service.validate_assignee_membership(
                sprint_id=data.sprint_id,
                project_id=data.project_id,
                assignee_id=data.assignee_id,
            )
        except AssigneeNotTeamMemberError as e:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(e),
            )

    item = BacklogItem(
        project_id=data.project_id,
        sprint_id=data.sprint_id,
        parent_id=data.parent_id,
        type=data.type.value,
        title=data.title,
        description=data.description,
        acceptance_criteria=data.acceptance_criteria,
        priority=data.priority.value,
        story_points=data.story_points,
        status="todo",
        assignee_id=data.assignee_id,
        labels=data.labels,
        created_by=current_user.id,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)

    return serialize_backlog_item(item)


@router.get("/backlog/assignees/{project_id}")
async def get_valid_assignees(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    """
    Get list of valid assignees for backlog items in a project.

    SDLC 5.1.3 GAP 2 Resolution (Sprint 76):
    - Returns only team members who can be assigned to backlog items
    - Used by frontend to populate assignee dropdown
    - If project has no team, returns empty list (allow any assignee)

    Returns:
        List of dicts with user info:
        [
            {
                "user_id": UUID,
                "full_name": str,
                "email": str,
                "role": str,
                "member_type": str
            }
        ]
    """
    await check_project_access(db, project_id, current_user)

    # Get project with team
    project_result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.deleted_at.is_(None),
        )
    )
    project = project_result.scalar_one_or_none()

    if not project or not project.team_id:
        return []

    # Get team members with user info
    members_result = await db.execute(
        select(TeamMember, User)
        .join(User, TeamMember.user_id == User.id)
        .where(
            TeamMember.team_id == project.team_id,
            TeamMember.deleted_at.is_(None),
        )
        .order_by(User.full_name)
    )
    members = members_result.all()

    return [
        {
            "user_id": member.user_id,
            "full_name": user.full_name or user.username,
            "email": user.email,
            "role": member.role,
            "member_type": member.member_type,
        }
        for member, user in members
    ]


@router.get("/backlog")
async def list_backlog_items(
    project_id: UUID = Query(..., description="Project UUID"),
    sprint_id: Optional[UUID] = Query(None, description="Filter by sprint (null = product backlog)"),
    type: Optional[str] = Query(None, description="Filter by type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    assignee_id: Optional[UUID] = Query(None, description="Filter by assignee"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BacklogItemListResponse:
    """List backlog items with filtering and pagination."""
    await check_project_access(db, project_id, current_user)

    query = select(BacklogItem).where(BacklogItem.project_id == project_id)

    # Apply filters
    if sprint_id is not None:
        query = query.where(BacklogItem.sprint_id == sprint_id)
    if type:
        query = query.where(BacklogItem.type == type)
    if status:
        query = query.where(BacklogItem.status == status)
    if priority:
        query = query.where(BacklogItem.priority == priority)
    if assignee_id:
        query = query.where(BacklogItem.assignee_id == assignee_id)

    # Count total
    count_query = select(func.count(BacklogItem.id)).where(BacklogItem.project_id == project_id)
    if sprint_id is not None:
        count_query = count_query.where(BacklogItem.sprint_id == sprint_id)
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    # Get priority counts
    priority_counts = await db.execute(
        select(
            BacklogItem.priority,
            func.count(BacklogItem.id),
        )
        .where(BacklogItem.project_id == project_id)
        .group_by(BacklogItem.priority)
    )
    p0_count = p1_count = p2_count = 0
    for row in priority_counts:
        if row[0] == "P0":
            p0_count = row[1]
        elif row[0] == "P1":
            p1_count = row[1]
        elif row[0] == "P2":
            p2_count = row[1]

    # Get total points
    points_result = await db.execute(
        select(func.sum(BacklogItem.story_points)).where(
            BacklogItem.project_id == project_id,
            BacklogItem.sprint_id == sprint_id if sprint_id else True,
        )
    )
    total_points = points_result.scalar() or 0

    # Get paginated results
    query = query.order_by(
        BacklogItem.priority,  # P0 first
        BacklogItem.created_at.desc(),
    )
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    items = result.scalars().all()

    serialized_items = []
    for item in items:
        subtasks_count_result = await db.execute(
            select(func.count(BacklogItem.id)).where(BacklogItem.parent_id == item.id)
        )
        subtasks_count = subtasks_count_result.scalar() or 0
        serialized_items.append(serialize_backlog_item(item, subtasks_count))

    return BacklogItemListResponse(
        items=serialized_items,
        total=total,
        page=page,
        page_size=page_size,
        has_next=(page * page_size) < total,
        total_points=total_points,
        p0_count=p0_count,
        p1_count=p1_count,
        p2_count=p2_count,
    )


@router.get("/backlog/{item_id}")
async def get_backlog_item(
    item_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BacklogItemResponse:
    """Get a single backlog item by ID."""
    result = await db.execute(
        select(BacklogItem).where(BacklogItem.id == item_id)
    )
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Backlog item not found",
        )

    await check_project_access(db, item.project_id, current_user)

    subtasks_count_result = await db.execute(
        select(func.count(BacklogItem.id)).where(BacklogItem.parent_id == item.id)
    )
    subtasks_count = subtasks_count_result.scalar() or 0

    return serialize_backlog_item(item, subtasks_count)


@router.put("/backlog/{item_id}")
async def update_backlog_item(
    item_id: UUID,
    data: BacklogItemUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BacklogItemResponse:
    """
    Update a backlog item.

    SDLC 5.1.3 GAP 2 Resolution (Sprint 76):
    - If assignee_id is being updated, validates that new assignee is a team member
    - Projects without teams allow any assignee (backward compatibility)
    """
    result = await db.execute(
        select(BacklogItem).where(BacklogItem.id == item_id)
    )
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Backlog item not found",
        )

    await check_project_access(db, item.project_id, current_user, require_write=True)

    # GAP 2 Resolution: Validate new assignee is team member
    if data.assignee_id is not None and data.assignee_id != item.assignee_id:
        backlog_service = BacklogService(db)
        try:
            await backlog_service.validate_assignee_membership(
                sprint_id=data.sprint_id if data.sprint_id is not None else item.sprint_id,
                project_id=item.project_id,
                assignee_id=data.assignee_id,
            )
        except AssigneeNotTeamMemberError as e:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(e),
            )

    if data.sprint_id is not None:
        item.sprint_id = data.sprint_id
    if data.parent_id is not None:
        item.parent_id = data.parent_id
    if data.type is not None:
        item.type = data.type.value
    if data.title is not None:
        item.title = data.title
    if data.description is not None:
        item.description = data.description
    if data.acceptance_criteria is not None:
        item.acceptance_criteria = data.acceptance_criteria
    if data.priority is not None:
        item.priority = data.priority.value
    if data.story_points is not None:
        item.story_points = data.story_points
    if data.status is not None:
        item.status = data.status.value
    if data.assignee_id is not None:
        item.assignee_id = data.assignee_id
    if data.labels is not None:
        item.labels = data.labels

    item.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(item)

    subtasks_count_result = await db.execute(
        select(func.count(BacklogItem.id)).where(BacklogItem.parent_id == item.id)
    )
    subtasks_count = subtasks_count_result.scalar() or 0

    return serialize_backlog_item(item, subtasks_count)


@router.delete("/backlog/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_backlog_item(
    item_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a backlog item."""
    result = await db.execute(
        select(BacklogItem).where(BacklogItem.id == item_id)
    )
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Backlog item not found",
        )

    await check_project_access(db, item.project_id, current_user, require_write=True)

    await db.delete(item)
    await db.commit()


# =========================================================================
# Bulk Operations
# =========================================================================


@router.post("/backlog/bulk/move-to-sprint")
async def bulk_move_to_sprint(
    data: BulkMoveToSprint,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BulkOperationResult:
    """Bulk move backlog items to a sprint (or back to product backlog)."""
    success_count = 0
    failure_count = 0
    errors = []

    for item_id in data.item_ids:
        try:
            result = await db.execute(
                select(BacklogItem).where(BacklogItem.id == item_id)
            )
            item = result.scalar_one_or_none()

            if not item:
                failure_count += 1
                errors.append({"item_id": str(item_id), "error": "Item not found"})
                continue

            await check_project_access(db, item.project_id, current_user, require_write=True)

            item.sprint_id = data.sprint_id
            item.updated_at = datetime.utcnow()
            success_count += 1

        except HTTPException as e:
            failure_count += 1
            errors.append({"item_id": str(item_id), "error": e.detail})

    await db.commit()

    return BulkOperationResult(
        success_count=success_count,
        failure_count=failure_count,
        errors=errors,
    )


@router.post("/backlog/bulk/update-priority")
async def bulk_update_priority(
    data: BulkUpdatePriority,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BulkOperationResult:
    """Bulk update priority for backlog items."""
    success_count = 0
    failure_count = 0
    errors = []

    for item_id in data.item_ids:
        try:
            result = await db.execute(
                select(BacklogItem).where(BacklogItem.id == item_id)
            )
            item = result.scalar_one_or_none()

            if not item:
                failure_count += 1
                errors.append({"item_id": str(item_id), "error": "Item not found"})
                continue

            await check_project_access(db, item.project_id, current_user, require_write=True)

            item.priority = data.priority.value
            item.updated_at = datetime.utcnow()
            success_count += 1

        except HTTPException as e:
            failure_count += 1
            errors.append({"item_id": str(item_id), "error": e.detail})

    await db.commit()

    return BulkOperationResult(
        success_count=success_count,
        failure_count=failure_count,
        errors=errors,
    )


# =========================================================================
# Planning Dashboard
# =========================================================================


@router.get("/dashboard/{project_id}")
async def get_planning_dashboard(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PlanningDashboard:
    """
    Get planning hierarchy dashboard data for a project.

    Returns:
    - All roadmaps with phases and sprints
    - Active roadmap and current sprint
    - Backlog statistics
    """
    await check_project_access(db, project_id, current_user)

    # Get all roadmaps
    roadmaps_result = await db.execute(
        select(Roadmap).where(Roadmap.project_id == project_id).order_by(Roadmap.created_at.desc())
    )
    roadmaps = roadmaps_result.scalars().all()

    roadmap_hierarchies = []
    active_roadmap = None
    current_sprint = None

    for roadmap in roadmaps:
        # Get phases for roadmap
        phases_result = await db.execute(
            select(Phase).where(Phase.roadmap_id == roadmap.id).order_by(Phase.number)
        )
        phases = phases_result.scalars().all()

        phase_summaries = []
        total_sprints = 0

        for phase in phases:
            # Get sprints for phase
            sprints_result = await db.execute(
                select(Sprint).where(Sprint.phase_id == phase.id).order_by(Sprint.number)
            )
            sprints = sprints_result.scalars().all()

            sprint_summaries = []
            for sprint in sprints:
                # Get backlog stats for sprint
                backlog_result = await db.execute(
                    select(
                        func.count(BacklogItem.id),
                        func.coalesce(func.sum(BacklogItem.story_points), 0),
                    ).where(BacklogItem.sprint_id == sprint.id)
                )
                backlog_row = backlog_result.one()

                sprint_summary = SprintSummary(
                    id=sprint.id,
                    number=sprint.number,
                    name=sprint.name,
                    status=sprint.status,
                    g_sprint_status=sprint.g_sprint_status,
                    g_sprint_close_status=sprint.g_sprint_close_status,
                    backlog_items_count=backlog_row[0],
                    total_points=backlog_row[1],
                    start_date=sprint.start_date,
                    end_date=sprint.end_date,
                )
                sprint_summaries.append(sprint_summary)

                # Track current sprint (active)
                if sprint.status == "active" and current_sprint is None:
                    backlog_count_result = await db.execute(
                        select(func.count(BacklogItem.id)).where(BacklogItem.sprint_id == sprint.id)
                    )
                    backlog_count = backlog_count_result.scalar() or 0
                    current_sprint = serialize_sprint(sprint, backlog_count)

                total_sprints += 1

            phase_summaries.append(PhaseSummary(
                id=phase.id,
                number=phase.number,
                name=phase.name,
                status=phase.status,
                sprints_count=len(sprints),
                sprints=sprint_summaries,
            ))

        # Find active sprint for this roadmap
        active_sprint_summary = None
        for ps in phase_summaries:
            for ss in ps.sprints:
                if ss.status == "active":
                    active_sprint_summary = ss
                    break

        hierarchy = RoadmapHierarchy(
            id=roadmap.id,
            name=roadmap.name,
            status=roadmap.status,
            vision=roadmap.vision,
            start_date=roadmap.start_date,
            end_date=roadmap.end_date,
            phases=phase_summaries,
            total_sprints=total_sprints,
            active_sprint=active_sprint_summary,
        )
        roadmap_hierarchies.append(hierarchy)

        if roadmap.status == "active" and active_roadmap is None:
            active_roadmap = hierarchy

    # Get backlog stats for project
    backlog_stats_result = await db.execute(
        select(
            func.count(BacklogItem.id),
            func.sum(cast(BacklogItem.sprint_id.isnot(None), Integer)),
            func.sum(cast(BacklogItem.sprint_id.is_(None), Integer)),
        ).where(BacklogItem.project_id == project_id)
    )

    stats_row = backlog_stats_result.one()

    priority_stats_result = await db.execute(
        select(BacklogItem.priority, func.count(BacklogItem.id))
        .where(BacklogItem.project_id == project_id)
        .group_by(BacklogItem.priority)
    )
    p0_count = p1_count = p2_count = 0
    for row in priority_stats_result:
        if row[0] == "P0":
            p0_count = row[1]
        elif row[0] == "P1":
            p1_count = row[1]
        elif row[0] == "P2":
            p2_count = row[1]

    return PlanningDashboard(
        project_id=project_id,
        roadmaps=roadmap_hierarchies,
        active_roadmap=active_roadmap,
        current_sprint=current_sprint,
        backlog_stats={
            "total": stats_row[0] or 0,
            "in_sprint": stats_row[1] or 0,
            "in_backlog": stats_row[2] or 0,
            "p0_count": p0_count,
            "p1_count": p1_count,
            "p2_count": p2_count,
        },
    )


# =========================================================================
# Sprint Analytics Endpoints (Sprint 76 Day 5)
# =========================================================================

@router.get(
    "/projects/{project_id}/velocity",
    response_model=VelocityMetricsResponse,
    summary="Get project velocity metrics",
    tags=["Planning", "Analytics"],
)
async def get_project_velocity(
    project_id: UUID,
    sprint_count: int = Query(default=5, ge=1, le=20, description="Number of sprints to analyze"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> VelocityMetricsResponse:
    """
    Get velocity metrics for a project from historical sprint data.

    **Sprint 76: AI Sprint Assistant - Velocity Calculation**

    Calculates:
    - Average velocity (story points per sprint)
    - Velocity trend (increasing/decreasing/stable)
    - Confidence score based on data availability
    - History of recent sprint velocities

    Args:
        project_id: Project UUID
        sprint_count: Number of completed sprints to analyze (default: 5)

    Returns:
        VelocityMetricsResponse with velocity metrics

    Raises:
        404: Project not found or no access
    """
    # Verify project access
    await check_project_access(db, project_id, current_user)

    # Calculate velocity
    assistant = get_sprint_assistant_service(db)
    velocity = await assistant.calculate_velocity(project_id, sprint_count)

    return VelocityMetricsResponse(
        average=velocity.average,
        trend=velocity.trend,
        confidence=velocity.confidence,
        history=velocity.history,
        sprint_count=velocity.sprint_count,
        project_id=project_id,
    )


@router.get(
    "/sprints/{sprint_id}/health",
    response_model=SprintHealthResponse,
    summary="Get sprint health indicators",
    tags=["Planning", "Analytics"],
)
async def get_sprint_health(
    sprint_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SprintHealthResponse:
    """
    Get health indicators for a sprint.

    **Sprint 76: AI Sprint Assistant - Health Assessment**

    Calculates:
    - Completion rate (story points done / total)
    - Blocked item count
    - Risk level (low/medium/high based on progress vs time)
    - Days remaining in sprint
    - Expected completion based on time elapsed

    Args:
        sprint_id: Sprint UUID

    Returns:
        SprintHealthResponse with health indicators

    Raises:
        404: Sprint not found
    """
    # Verify sprint exists and user has access
    result = await db.execute(
        select(Sprint)
        .options(selectinload(Sprint.project))
        .where(Sprint.id == sprint_id)
    )
    sprint = result.scalar_one_or_none()

    if not sprint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sprint {sprint_id} not found",
        )

    # Check project access
    await check_project_access(db, sprint.project_id, current_user)

    # Calculate health
    assistant = get_sprint_assistant_service(db)
    health = await assistant.get_sprint_health(sprint_id)

    return SprintHealthResponse(
        sprint_id=sprint_id,
        completion_rate=health.completion_rate,
        completed_points=health.completed_points,
        total_points=health.total_points,
        blocked_count=health.blocked_count,
        risk_level=health.risk_level,
        days_remaining=health.days_remaining,
        days_elapsed=health.days_elapsed,
        expected_completion=health.expected_completion,
    )


@router.get(
    "/sprints/{sprint_id}/suggestions",
    response_model=SprintSuggestionsResponse,
    summary="Get AI prioritization suggestions",
    tags=["Planning", "Analytics", "AI"],
)
async def get_sprint_suggestions(
    sprint_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SprintSuggestionsResponse:
    """
    Get AI-powered prioritization suggestions for a sprint.

    **Sprint 76: AI Sprint Assistant - Recommendations**

    Analyzes sprint backlog and generates suggestions:
    - start_p0: P0 items not yet started (critical)
    - unassigned_priority: Unassigned P0/P1 items
    - overloaded: Sprint capacity exceeds velocity
    - blocked: Items requiring unblocking
    - p2_at_risk: Low-priority items at risk
    - underloaded: Capacity opportunity

    Args:
        sprint_id: Sprint UUID

    Returns:
        SprintSuggestionsResponse with AI suggestions

    Raises:
        404: Sprint not found
    """
    # Verify sprint exists
    result = await db.execute(
        select(Sprint)
        .options(selectinload(Sprint.project))
        .where(Sprint.id == sprint_id)
    )
    sprint = result.scalar_one_or_none()

    if not sprint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sprint {sprint_id} not found",
        )

    await check_project_access(db, sprint.project_id, current_user)

    # Generate suggestions
    assistant = get_sprint_assistant_service(db)
    suggestions = await assistant.suggest_priorities(sprint_id)

    return SprintSuggestionsResponse(
        sprint_id=sprint_id,
        suggestions=[
            PrioritySuggestionResponse(
                type=s.type,
                message=s.message,
                severity=s.severity,
                items=s.items,
                action=s.action,
            )
            for s in suggestions
        ],
        suggestion_count=len(suggestions),
    )


@router.get(
    "/sprints/{sprint_id}/analytics",
    response_model=SprintAnalyticsResponse,
    summary="Get comprehensive sprint analytics",
    tags=["Planning", "Analytics", "AI"],
)
async def get_sprint_analytics(
    sprint_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SprintAnalyticsResponse:
    """
    Get comprehensive analytics for a sprint.

    **Sprint 76: AI Sprint Assistant - Full Analytics**

    Combines velocity, health, and suggestions into a single response
    with an AI-generated summary of sprint status.

    Args:
        sprint_id: Sprint UUID

    Returns:
        SprintAnalyticsResponse with full analytics

    Raises:
        404: Sprint not found
    """
    # Verify sprint exists
    result = await db.execute(
        select(Sprint)
        .options(selectinload(Sprint.project))
        .where(Sprint.id == sprint_id)
    )
    sprint = result.scalar_one_or_none()

    if not sprint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sprint {sprint_id} not found",
        )

    await check_project_access(db, sprint.project_id, current_user)

    # Get comprehensive analytics
    assistant = get_sprint_assistant_service(db)
    analytics = await assistant.get_sprint_analytics(sprint_id)

    return SprintAnalyticsResponse(
        sprint_id=analytics.sprint_id,
        sprint_number=analytics.sprint_number,
        sprint_name=analytics.sprint_name,
        health=SprintHealthResponse(
            sprint_id=sprint_id,
            completion_rate=analytics.health.completion_rate,
            completed_points=analytics.health.completed_points,
            total_points=analytics.health.total_points,
            blocked_count=analytics.health.blocked_count,
            risk_level=analytics.health.risk_level,
            days_remaining=analytics.health.days_remaining,
            days_elapsed=analytics.health.days_elapsed,
            expected_completion=analytics.health.expected_completion,
        ),
        velocity=VelocityMetricsResponse(
            average=analytics.velocity.average,
            trend=analytics.velocity.trend,
            confidence=analytics.velocity.confidence,
            history=analytics.velocity.history,
            sprint_count=analytics.velocity.sprint_count,
            project_id=sprint.project_id,
        ),
        suggestions=[
            PrioritySuggestionResponse(
                type=s.type,
                message=s.message,
                severity=s.severity,
                items=s.items,
                action=s.action,
            )
            for s in analytics.suggestions
        ],
        summary=analytics.summary,
    )
