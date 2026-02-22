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
Reference: SDLC-Sprint-Planning-Governance.md (SDLC 6.1.1)

Endpoints:
- /roadmaps: Roadmap CRUD (strategic planning)
- /phases: Phase CRUD (4-8 week themes)
- /sprints: Sprint CRUD + G-Sprint/G-Sprint-Close gates
- /backlog: Backlog item CRUD (stories, tasks, bugs)

SDLC 6.1.1 Compliance:
- G-Sprint Gate validation before sprint start
- G-Sprint-Close Gate validation with 24h documentation deadline
- Immutable sprint numbering (Rule #1)
- Traceability chain enforcement
- Team role authorization for gate approval (SE4H Coach only)

Sprint 75 Enhancement:
- check_sprint_gate_authorization() - Team-based gate approval validation
- Only SE4H Coach (team owner/admin) can approve sprint gates
- AI agents (SE4A) cannot approve governance gates
- Human oversight enforcement for SDLC 6.1.1

Zero Mock Policy: Production-ready FastAPI routes
=========================================================================
"""

import logging
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
import sqlalchemy as sa
from sqlalchemy import func, select, Integer, cast
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.dependencies import get_current_user, analytics_rate_limit
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
from app.models.retro_action_item import RetroActionItem
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
from app.services.burndown_service import (
    BurndownService,
    get_burndown_service,
)
from app.services.forecast_service import (
    ForecastService,
    get_forecast_service,
)
from app.services.retrospective_service import (
    RetrospectiveService,
    get_retrospective_service,
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
    # Burndown (Sprint 77)
    BurndownChartResponse,
    BurndownPointResponse,
    # Forecast (Sprint 77)
    SprintForecastResponse,
    ForecastRiskResponse,
    # Retrospective (Sprint 77)
    SprintRetrospectiveResponse,
    RetroMetricsResponse,
    RetroInsightResponse,
    RetroActionResponse,
)
from app.schemas.retro_action_item import (
    RetroActionItemCreate,
    RetroActionItemUpdate,
    RetroActionItemResponse,
    RetroActionItemListResponse,
    RetroActionItemStats,
    RetroActionItemBulkCreate,
    RetroActionItemBulkStatusUpdate,
)
from app.schemas.sprint_dependency import (
    SprintDependencyCreate,
    SprintDependencyUpdate,
    SprintDependencyResponse,
    SprintDependencyListResponse,
    SprintDependencyWithDetails,
    DependencyGraph,
    DependencyAnalysis,
    SprintDependencyBulkResolve,
    SprintDependencyBulkResult,
)
from app.models.sprint_dependency import SprintDependency
from app.services.sprint_dependency_service import (
    SprintDependencyService,
    get_sprint_dependency_service,
)
from app.schemas.resource_allocation import (
    ResourceAllocationCreate,
    ResourceAllocationUpdate,
    ResourceAllocationResponse,
    ResourceAllocationListResponse,
    UserCapacity,
    TeamCapacity,
    SprintCapacity,
    ConflictCheckResult,
    ResourceHeatmap,
)
from app.models.resource_allocation import ResourceAllocation
from app.services.resource_allocation_service import (
    ResourceAllocationService,
    get_resource_allocation_service,
)
from app.schemas.sprint_template import (
    SprintTemplateCreate,
    SprintTemplateUpdate,
    SprintTemplateResponse,
    SprintTemplateListResponse,
    SprintTemplateWithDetails,
    ApplyTemplateRequest,
    ApplyTemplateResponse,
    TemplateSuggestionsResponse,
    SprintTemplateBulkDelete,
    SprintTemplateBulkResult,
)
from app.models.sprint_template import SprintTemplate
from app.services.sprint_template_service import (
    SprintTemplateService,
    get_sprint_template_service,
)


# =========================================================================
# Router Configuration
# =========================================================================

logger = logging.getLogger(__name__)

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

        # Sprint 88: Platform admins CANNOT access customer data
        is_regular_admin = user.is_superuser and not user.is_platform_admin
        if not member and not is_regular_admin:
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

    SDLC 6.1.1 Sprint Planning Governance (Sprint 75):
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

    # Sprint 88: Regular admins bypass (platform admins do not)
    is_regular_admin = user.is_superuser and not user.is_platform_admin
    if is_regular_admin:
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
    phase_status: Optional[str] = Query(None, description="Filter by status", alias="status"),
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
    if phase_status:
        query = query.where(Phase.status == phase_status)

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

    SDLC 6.1.1 Rule #1: Sprint numbers are immutable after creation.
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
            f"Sprint numbers are immutable per SDLC 6.1.1 Rule #1.",
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

    SDLC 6.1.1 Sprint Planning Governance (Sprint 75):
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

    # Sprint 193 Phase 4: Auto-verify checklist items with auto_verify=True
    # before finalization so automated results affect pass/fail outcome
    try:
        project_result = await db.execute(
            select(Project).where(Project.id == sprint.project_id)
        )
        project = project_result.scalar_one_or_none()
        if project:
            from app.services.github_service import github_service
            from app.services.sprint_verification_service import SprintVerificationService

            verification_svc = SprintVerificationService(
                db=db, github_service=github_service
            )
            await verification_svc.auto_evaluate_checklist_item(
                evaluation=evaluation,
                sprint=sprint,
                project=project,
            )
    except Exception:
        # Auto-verification is best-effort; manual checklist still works
        logger.warning(
            "Auto-verification failed for sprint %s gate %s",
            sprint_id, gate_type.value, exc_info=True,
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
    """Serialize gate evaluation to response dict.

    Sprint 193 fix: Template uses 'passed' field (True/False/None),
    not 'checked'. The serializer was reading the wrong field name,
    causing completion counts to always be 0.
    """
    passed_count = 0
    total = 0
    for category_items in evaluation.checklist.values():
        for item in category_items:
            total += 1
            if item.get("passed") is True:
                passed_count += 1

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
        "all_items_passed": passed_count == total and total > 0,
        "passed_count": passed_count,
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

    SDLC 6.1.1 GAP 2 Resolution (Sprint 76):
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

    SDLC 6.1.1 GAP 2 Resolution (Sprint 76):
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

    SDLC 6.1.1 GAP 2 Resolution (Sprint 76):
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
#
# P0 Fix: Rate limited to 10 req/min per user to prevent DoS attacks
# on compute-heavy analytics operations.
# Reference: Sprint 76 CTO Review - APPROVED with blocking condition
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
    _rate_limit: None = Depends(analytics_rate_limit()),
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
    _rate_limit: None = Depends(analytics_rate_limit()),
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
    _rate_limit: None = Depends(analytics_rate_limit()),
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
    _rate_limit: None = Depends(analytics_rate_limit()),
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


# =========================================================================
# Sprint Burndown Endpoints (Sprint 77 Day 2)
#
# Burndown chart data generation for sprint visualization
# Performance target: <100ms p95
# =========================================================================


@router.get(
    "/sprints/{sprint_id}/burndown",
    response_model=BurndownChartResponse,
    summary="Get sprint burndown chart data",
    tags=["Planning", "Analytics", "Sprint 77"],
)
async def get_sprint_burndown(
    sprint_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _rate_limit: None = Depends(analytics_rate_limit()),
) -> BurndownChartResponse:
    """
    Get burndown chart data for a sprint.

    **Sprint 77: Burndown Charts - Day 2 Implementation**

    Generates burndown chart data including:
    - Ideal burndown line (linear from total points to 0)
    - Actual burndown line (based on completed items)
    - Progress metrics (completion rate, days remaining)
    - On-track indicator (actual vs ideal comparison)

    Performance Budget:
    - Query time: <50ms
    - Calculation time: <20ms
    - Total response: <100ms p95

    Args:
        sprint_id: Sprint UUID

    Returns:
        BurndownChartResponse with ideal and actual burndown data

    Raises:
        404: Sprint not found
        400: Sprint has no start/end dates
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

    # Generate burndown data
    burndown_service = get_burndown_service(db)

    try:
        burndown = await burndown_service.get_burndown_data(sprint_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    return BurndownChartResponse(
        sprint_id=burndown.sprint_id,
        sprint_number=burndown.sprint_number,
        sprint_name=burndown.sprint_name,
        total_points=burndown.total_points,
        start_date=burndown.start_date,
        end_date=burndown.end_date,
        ideal=[
            BurndownPointResponse(
                point_date=p.date,
                points=p.points,
                point_type=p.type,
            )
            for p in burndown.ideal
        ],
        actual=[
            BurndownPointResponse(
                point_date=p.date,
                points=p.points,
                point_type=p.type,
            )
            for p in burndown.actual
        ],
        remaining_points=burndown.remaining_points,
        completion_rate=burndown.completion_rate,
        days_elapsed=burndown.days_elapsed,
        days_remaining=burndown.days_remaining,
        on_track=burndown.on_track,
    )


# =========================================================================
# Sprint Forecast Endpoints (Sprint 77 Day 3)
#
# Sprint completion prediction and risk analysis
# Performance target: <100ms p95
# =========================================================================


@router.get(
    "/sprints/{sprint_id}/forecast",
    response_model=SprintForecastResponse,
    summary="Get sprint completion forecast",
    tags=["Planning", "Analytics", "Sprint 77"],
)
async def get_sprint_forecast(
    sprint_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _rate_limit: None = Depends(analytics_rate_limit()),
) -> SprintForecastResponse:
    """
    Get sprint completion forecast with probability and risks.

    **Sprint 77: Sprint Forecasting - Day 3 Implementation**

    Predicts sprint completion probability based on:
    - Current vs required burn rate
    - Blocked items penalty (-5% each)
    - Incomplete P0 items penalty (-10% each)
    - Days remaining urgency factor

    Returns:
    - Completion probability (0-100%)
    - Predicted end date
    - On-track indicator
    - Identified risks with severity
    - AI-generated recommendations

    Performance Budget:
    - Query time: <50ms
    - Calculation time: <30ms
    - Total response: <100ms p95

    Args:
        sprint_id: Sprint UUID

    Returns:
        SprintForecastResponse with probability, risks, and recommendations

    Raises:
        404: Sprint not found
        400: Sprint has no start/end dates
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

    # Generate forecast
    forecast_service = get_forecast_service(db)

    try:
        forecast = await forecast_service.forecast_completion(sprint_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    return SprintForecastResponse(
        sprint_id=forecast.sprint_id,
        sprint_number=forecast.sprint_number,
        sprint_name=forecast.sprint_name,
        probability=forecast.probability,
        predicted_end_date=forecast.predicted_end_date,
        on_track=forecast.on_track,
        remaining_points=forecast.remaining_points,
        total_points=forecast.total_points,
        completed_points=forecast.completed_points,
        current_burn_rate=forecast.current_burn_rate,
        required_burn_rate=forecast.required_burn_rate,
        days_elapsed=forecast.days_elapsed,
        days_remaining=forecast.days_remaining,
        risks=[
            ForecastRiskResponse(
                risk_type=r.risk_type,
                severity=r.severity,
                message=r.message,
                recommendation=r.recommendation,
            )
            for r in forecast.risks
        ],
        recommendations=forecast.recommendations,
    )


# =========================================================================
# Sprint Retrospective Endpoints (Sprint 77 Day 4)
#
# Auto-generated sprint retrospective with insights and action items
# Performance target: <100ms p95
# =========================================================================


@router.get(
    "/sprints/{sprint_id}/retrospective",
    response_model=SprintRetrospectiveResponse,
    summary="Get auto-generated sprint retrospective",
    tags=["Planning", "Analytics", "Sprint 77"],
)
async def get_sprint_retrospective(
    sprint_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _rate_limit: None = Depends(analytics_rate_limit()),
) -> SprintRetrospectiveResponse:
    """
    Get auto-generated sprint retrospective.

    **Sprint 77: Retrospective Automation - Day 4 Implementation**

    Analyzes sprint performance and generates:
    - Metrics summary (completion rate, P0 status, blocked items)
    - "Went well" insights (positive patterns)
    - "Needs improvement" insights (areas for growth)
    - Action items (concrete next steps)
    - Executive summary

    Insight Categories:
    - delivery: Completion and delivery performance
    - priority: P0/P1 focus and completion
    - velocity: Velocity trends (improving/stable/declining)
    - planning: Sprint planning accuracy
    - scope: Scope changes and creep
    - blockers: Blocked items management

    Performance Budget:
    - Query time: <50ms
    - Analysis time: <30ms
    - Total response: <100ms p95

    Args:
        sprint_id: Sprint UUID

    Returns:
        SprintRetrospectiveResponse with metrics, insights, and actions

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

    # Generate retrospective
    retro_service = get_retrospective_service(db)

    try:
        retro = await retro_service.generate_retrospective(sprint_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    return SprintRetrospectiveResponse(
        sprint_id=retro.sprint_id,
        sprint_number=retro.sprint_number,
        sprint_name=retro.sprint_name,
        generated_at=retro.generated_at,
        metrics=RetroMetricsResponse(
            committed_points=retro.metrics.committed_points,
            completed_points=retro.metrics.completed_points,
            completion_rate=retro.metrics.completion_rate,
            p0_total=retro.metrics.p0_total,
            p0_completed=retro.metrics.p0_completed,
            p0_completion_rate=retro.metrics.p0_completion_rate,
            items_added_mid_sprint=retro.metrics.items_added_mid_sprint,
            blocked_items=retro.metrics.blocked_items,
            average_cycle_time_days=retro.metrics.average_cycle_time_days,
            velocity_trend=retro.metrics.velocity_trend,
        ),
        went_well=[
            RetroInsightResponse(
                category=i.category,
                insight_type=i.insight_type,
                title=i.title,
                description=i.description,
                impact=i.impact,
            )
            for i in retro.went_well
        ],
        needs_improvement=[
            RetroInsightResponse(
                category=i.category,
                insight_type=i.insight_type,
                title=i.title,
                description=i.description,
                impact=i.impact,
            )
            for i in retro.needs_improvement
        ],
        action_items=[
            RetroActionResponse(
                id=a.id,
                description=a.description,
                owner=a.owner,
                due_date=a.due_date,
                status=a.status,
                priority=a.priority,
            )
            for a in retro.action_items
        ],
        summary=retro.summary,
    )


# =========================================================================
# Retrospective Action Item Endpoints (Sprint 78 Day 1)
#
# CRUD operations for persistent action items from sprint retrospectives
# Supports cross-sprint tracking and assignment
# =========================================================================


def _serialize_retro_action_item(item: RetroActionItem) -> dict:
    """Serialize RetroActionItem to response dict."""
    return {
        "id": item.id,
        "sprint_id": item.sprint_id,
        "title": item.title,
        "description": item.description,
        "category": item.category,
        "priority": item.priority,
        "status": item.status,
        "assignee_id": item.assignee_id,
        "due_sprint_id": item.due_sprint_id,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
        "completed_at": item.completed_at,
    }


@router.post(
    "/sprints/{sprint_id}/action-items",
    status_code=status.HTTP_201_CREATED,
    response_model=RetroActionItemResponse,
    summary="Create action item from retrospective",
    tags=["Planning", "Retrospective", "Sprint 78"],
)
async def create_retro_action_item(
    sprint_id: UUID,
    data: RetroActionItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RetroActionItemResponse:
    """
    Create a new action item from sprint retrospective.

    **Sprint 78: Retrospective Enhancement - Day 1 Implementation**

    Action items track concrete next steps identified during sprint retrospectives.
    Supports:
    - Category classification (delivery, priority, velocity, etc.)
    - Priority levels (low, medium, high)
    - Assignment to team members
    - Cross-sprint tracking via due_sprint_id

    Args:
        sprint_id: Sprint UUID (source sprint)
        data: Action item data

    Returns:
        Created RetroActionItemResponse

    Raises:
        404: Sprint not found
        403: No write access to project
    """
    # Verify sprint exists
    result = await db.execute(
        select(Sprint).where(Sprint.id == sprint_id)
    )
    sprint = result.scalar_one_or_none()

    if not sprint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sprint {sprint_id} not found",
        )

    # Check project access
    await check_project_access(db, sprint.project_id, current_user, require_write=True)

    # Validate due_sprint belongs to same project if provided
    if data.due_sprint_id:
        due_sprint_result = await db.execute(
            select(Sprint).where(Sprint.id == data.due_sprint_id)
        )
        due_sprint = due_sprint_result.scalar_one_or_none()
        if not due_sprint or due_sprint.project_id != sprint.project_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Due sprint does not belong to this project",
            )

    # Create action item
    item = RetroActionItem(
        sprint_id=sprint_id,
        title=data.title,
        description=data.description,
        category=data.category,
        priority=data.priority,
        status="open",
        assignee_id=data.assignee_id,
        due_sprint_id=data.due_sprint_id,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)

    return _serialize_retro_action_item(item)


@router.get(
    "/sprints/{sprint_id}/action-items",
    response_model=RetroActionItemListResponse,
    summary="List action items for a sprint",
    tags=["Planning", "Retrospective", "Sprint 78"],
)
async def list_retro_action_items(
    sprint_id: UUID,
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    category: Optional[str] = Query(None, description="Filter by category"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    assignee_id: Optional[UUID] = Query(None, description="Filter by assignee"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RetroActionItemListResponse:
    """
    List action items for a sprint retrospective.

    **Sprint 78: Retrospective Enhancement - Day 1 Implementation**

    Supports filtering by:
    - status: open, in_progress, completed, cancelled
    - category: delivery, priority, velocity, planning, scope, blockers, team, general
    - priority: low, medium, high
    - assignee_id: User UUID

    Args:
        sprint_id: Sprint UUID
        Various filters

    Returns:
        Paginated list of action items
    """
    # Verify sprint exists
    result = await db.execute(
        select(Sprint).where(Sprint.id == sprint_id)
    )
    sprint = result.scalar_one_or_none()

    if not sprint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sprint {sprint_id} not found",
        )

    # Check project access
    await check_project_access(db, sprint.project_id, current_user)

    # Build query
    query = select(RetroActionItem).where(
        RetroActionItem.sprint_id == sprint_id,
        RetroActionItem.is_deleted == False,
    )

    if status_filter:
        query = query.where(RetroActionItem.status == status_filter)
    if category:
        query = query.where(RetroActionItem.category == category)
    if priority:
        query = query.where(RetroActionItem.priority == priority)
    if assignee_id:
        query = query.where(RetroActionItem.assignee_id == assignee_id)

    # Count total
    count_query = select(func.count(RetroActionItem.id)).where(
        RetroActionItem.sprint_id == sprint_id,
        RetroActionItem.is_deleted == False,
    )
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    # Get paginated results
    query = query.order_by(RetroActionItem.priority, RetroActionItem.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    items = result.scalars().all()

    return RetroActionItemListResponse(
        items=[_serialize_retro_action_item(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/action-items/{item_id}",
    response_model=RetroActionItemResponse,
    summary="Get a single action item",
    tags=["Planning", "Retrospective", "Sprint 78"],
)
async def get_retro_action_item(
    item_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RetroActionItemResponse:
    """Get a single action item by ID."""
    result = await db.execute(
        select(RetroActionItem)
        .options(selectinload(RetroActionItem.sprint))
        .where(
            RetroActionItem.id == item_id,
            RetroActionItem.is_deleted == False,
        )
    )
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Action item not found",
        )

    # Check project access
    await check_project_access(db, item.sprint.project_id, current_user)

    return _serialize_retro_action_item(item)


@router.put(
    "/action-items/{item_id}",
    response_model=RetroActionItemResponse,
    summary="Update an action item",
    tags=["Planning", "Retrospective", "Sprint 78"],
)
async def update_retro_action_item(
    item_id: UUID,
    data: RetroActionItemUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RetroActionItemResponse:
    """
    Update an action item.

    Status transitions:
    - open -> in_progress (when assigned)
    - in_progress -> completed (manual)
    - Any -> cancelled (manual)
    """
    result = await db.execute(
        select(RetroActionItem)
        .options(selectinload(RetroActionItem.sprint))
        .where(
            RetroActionItem.id == item_id,
            RetroActionItem.is_deleted == False,
        )
    )
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Action item not found",
        )

    # Check project access
    await check_project_access(db, item.sprint.project_id, current_user, require_write=True)

    # Update fields
    if data.title is not None:
        item.title = data.title
    if data.description is not None:
        item.description = data.description
    if data.category is not None:
        item.category = data.category
    if data.priority is not None:
        item.priority = data.priority
    if data.status is not None:
        item.status = data.status
        if data.status == "completed":
            item.completed_at = datetime.utcnow()
    if data.assignee_id is not None:
        item.assignee_id = data.assignee_id
        if item.status == "open":
            item.status = "in_progress"
    if data.due_sprint_id is not None:
        # Validate due_sprint belongs to same project
        due_sprint_result = await db.execute(
            select(Sprint).where(Sprint.id == data.due_sprint_id)
        )
        due_sprint = due_sprint_result.scalar_one_or_none()
        if not due_sprint or due_sprint.project_id != item.sprint.project_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Due sprint does not belong to this project",
            )
        item.due_sprint_id = data.due_sprint_id

    item.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(item)

    return _serialize_retro_action_item(item)


@router.delete(
    "/action-items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an action item",
    tags=["Planning", "Retrospective", "Sprint 78"],
)
async def delete_retro_action_item(
    item_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Soft delete an action item."""
    result = await db.execute(
        select(RetroActionItem)
        .options(selectinload(RetroActionItem.sprint))
        .where(
            RetroActionItem.id == item_id,
            RetroActionItem.is_deleted == False,
        )
    )
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Action item not found",
        )

    # Check project access
    await check_project_access(db, item.sprint.project_id, current_user, require_write=True)

    # Soft delete
    item.is_deleted = True
    item.updated_at = datetime.utcnow()
    await db.commit()


@router.post(
    "/sprints/{sprint_id}/action-items/bulk",
    status_code=status.HTTP_201_CREATED,
    summary="Bulk create action items",
    tags=["Planning", "Retrospective", "Sprint 78"],
)
async def bulk_create_retro_action_items(
    sprint_id: UUID,
    data: RetroActionItemBulkCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[RetroActionItemResponse]:
    """
    Bulk create action items from retrospective.

    Useful for importing action items generated by retrospective automation.
    """
    # Verify sprint exists
    result = await db.execute(
        select(Sprint).where(Sprint.id == sprint_id)
    )
    sprint = result.scalar_one_or_none()

    if not sprint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sprint {sprint_id} not found",
        )

    # Check project access
    await check_project_access(db, sprint.project_id, current_user, require_write=True)

    created_items = []
    for item_data in data.items:
        item = RetroActionItem(
            sprint_id=sprint_id,
            title=item_data.title,
            description=item_data.description,
            category=item_data.category,
            priority=item_data.priority,
            status="open",
        )
        db.add(item)
        created_items.append(item)

    await db.commit()
    for item in created_items:
        await db.refresh(item)

    return [_serialize_retro_action_item(item) for item in created_items]


@router.post(
    "/action-items/bulk/status",
    summary="Bulk update action item status",
    tags=["Planning", "Retrospective", "Sprint 78"],
)
async def bulk_update_retro_action_item_status(
    data: RetroActionItemBulkStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Bulk update status for multiple action items."""
    success_count = 0
    failure_count = 0
    errors = []

    for item_id in data.ids:
        try:
            result = await db.execute(
                select(RetroActionItem)
                .options(selectinload(RetroActionItem.sprint))
                .where(
                    RetroActionItem.id == item_id,
                    RetroActionItem.is_deleted == False,
                )
            )
            item = result.scalar_one_or_none()

            if not item:
                failure_count += 1
                errors.append({"item_id": str(item_id), "error": "Item not found"})
                continue

            await check_project_access(db, item.sprint.project_id, current_user, require_write=True)

            item.status = data.status
            if data.status == "completed":
                item.completed_at = datetime.utcnow()
            item.updated_at = datetime.utcnow()
            success_count += 1

        except HTTPException as e:
            failure_count += 1
            errors.append({"item_id": str(item_id), "error": e.detail})

    await db.commit()

    return {
        "success_count": success_count,
        "failure_count": failure_count,
        "errors": errors,
    }


@router.get(
    "/sprints/{sprint_id}/action-items/stats",
    response_model=RetroActionItemStats,
    summary="Get action items statistics",
    tags=["Planning", "Retrospective", "Sprint 78"],
)
async def get_retro_action_item_stats(
    sprint_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RetroActionItemStats:
    """
    Get statistics for action items in a sprint retrospective.

    Returns counts by status, category, and priority.
    """
    # Verify sprint exists
    result = await db.execute(
        select(Sprint).where(Sprint.id == sprint_id)
    )
    sprint = result.scalar_one_or_none()

    if not sprint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sprint {sprint_id} not found",
        )

    # Check project access
    await check_project_access(db, sprint.project_id, current_user)

    # Get status counts
    status_result = await db.execute(
        select(RetroActionItem.status, func.count(RetroActionItem.id))
        .where(
            RetroActionItem.sprint_id == sprint_id,
            RetroActionItem.is_deleted == False,
        )
        .group_by(RetroActionItem.status)
    )
    status_counts = {row[0]: row[1] for row in status_result}

    # Get category counts
    category_result = await db.execute(
        select(RetroActionItem.category, func.count(RetroActionItem.id))
        .where(
            RetroActionItem.sprint_id == sprint_id,
            RetroActionItem.is_deleted == False,
        )
        .group_by(RetroActionItem.category)
    )
    by_category = {row[0]: row[1] for row in category_result}

    # Get priority counts
    priority_result = await db.execute(
        select(RetroActionItem.priority, func.count(RetroActionItem.id))
        .where(
            RetroActionItem.sprint_id == sprint_id,
            RetroActionItem.is_deleted == False,
        )
        .group_by(RetroActionItem.priority)
    )
    by_priority = {row[0]: row[1] for row in priority_result}

    total = sum(status_counts.values())
    completed = status_counts.get("completed", 0)

    return RetroActionItemStats(
        total_items=total,
        open_items=status_counts.get("open", 0),
        in_progress_items=status_counts.get("in_progress", 0),
        completed_items=completed,
        cancelled_items=status_counts.get("cancelled", 0),
        completion_rate=round(completed / total * 100, 1) if total > 0 else 0.0,
        by_category=by_category,
        by_priority=by_priority,
    )


# =========================================================================
# Sprint Retrospective Comparison Endpoint (Sprint 78 Day 1)
#
# Compare retrospectives across multiple sprints
# =========================================================================


@router.get(
    "/projects/{project_id}/retrospective-comparison",
    summary="Compare retrospectives across sprints",
    tags=["Planning", "Retrospective", "Sprint 78"],
)
async def compare_sprint_retrospectives(
    project_id: UUID,
    sprint_ids: str = Query(..., description="Comma-separated sprint UUIDs (2-5 sprints)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _rate_limit: None = Depends(analytics_rate_limit()),
) -> dict:
    """
    Compare retrospectives across multiple sprints.

    **Sprint 78: Retrospective Enhancement - Day 1 Implementation**

    Compares key metrics across selected sprints:
    - Completion rates
    - P0 completion rates
    - Blocked item trends
    - Velocity trends
    - Action item completion rates

    Args:
        project_id: Project UUID
        sprint_ids: Comma-separated sprint UUIDs (2-5 sprints)

    Returns:
        Comparison data with metrics for each sprint
    """
    # Parse sprint IDs
    try:
        sprint_uuid_list = [UUID(sid.strip()) for sid in sprint_ids.split(",")]
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid sprint ID format. Use comma-separated UUIDs.",
        )

    if len(sprint_uuid_list) < 2 or len(sprint_uuid_list) > 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please provide 2-5 sprint IDs for comparison",
        )

    # Check project access
    await check_project_access(db, project_id, current_user)

    # Verify all sprints belong to the project
    sprints_result = await db.execute(
        select(Sprint).where(
            Sprint.id.in_(sprint_uuid_list),
            Sprint.project_id == project_id,
        ).order_by(Sprint.number)
    )
    sprints = sprints_result.scalars().all()

    if len(sprints) != len(sprint_uuid_list):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Some sprint IDs do not belong to this project",
        )

    # Generate comparison data
    retro_service = get_retrospective_service(db)
    comparison_data = []

    for sprint in sprints:
        try:
            retro = await retro_service.generate_retrospective(sprint.id)

            # Get action item stats
            action_stats_result = await db.execute(
                select(
                    func.count(RetroActionItem.id),
                    func.sum(sa.case((RetroActionItem.status == "completed", 1), else_=0)),
                )
                .where(
                    RetroActionItem.sprint_id == sprint.id,
                    RetroActionItem.is_deleted == False,
                )
            )
            action_stats = action_stats_result.one()

            comparison_data.append({
                "sprint_id": sprint.id,
                "sprint_number": sprint.number,
                "sprint_name": sprint.name,
                "metrics": {
                    "completion_rate": retro.metrics.completion_rate,
                    "p0_completion_rate": retro.metrics.p0_completion_rate,
                    "committed_points": retro.metrics.committed_points,
                    "completed_points": retro.metrics.completed_points,
                    "blocked_items": retro.metrics.blocked_items,
                    "items_added_mid_sprint": retro.metrics.items_added_mid_sprint,
                    "velocity_trend": retro.metrics.velocity_trend,
                },
                "action_items": {
                    "total": action_stats[0] or 0,
                    "completed": action_stats[1] or 0,
                    "completion_rate": round(
                        (action_stats[1] or 0) / (action_stats[0] or 1) * 100, 1
                    ) if action_stats[0] else 0.0,
                },
                "insights_count": {
                    "went_well": len(retro.went_well),
                    "needs_improvement": len(retro.needs_improvement),
                },
            })
        except ValueError:
            # Sprint may not have enough data
            comparison_data.append({
                "sprint_id": sprint.id,
                "sprint_number": sprint.number,
                "sprint_name": sprint.name,
                "error": "Insufficient data for retrospective",
            })

    # Calculate trends
    if len(comparison_data) >= 2:
        first = comparison_data[0]
        last = comparison_data[-1]

        if "metrics" in first and "metrics" in last:
            trends = {
                "completion_rate_change": round(
                    last["metrics"]["completion_rate"] - first["metrics"]["completion_rate"], 1
                ),
                "p0_completion_change": round(
                    last["metrics"]["p0_completion_rate"] - first["metrics"]["p0_completion_rate"], 1
                ),
                "blocked_items_change": (
                    last["metrics"]["blocked_items"] - first["metrics"]["blocked_items"]
                ),
            }
        else:
            trends = None
    else:
        trends = None

    return {
        "project_id": project_id,
        "sprint_count": len(sprints),
        "sprints": comparison_data,
        "trends": trends,
    }


# =========================================================================
# Sprint Dependency Endpoints (Sprint 78 Day 2)
#
# Cross-project sprint dependency management
# Supports circular dependency detection and graph visualization
# =========================================================================


def _serialize_dependency(dep: SprintDependency) -> dict:
    """Serialize SprintDependency to response dict."""
    return {
        "id": dep.id,
        "source_sprint_id": dep.source_sprint_id,
        "target_sprint_id": dep.target_sprint_id,
        "dependency_type": dep.dependency_type,
        "description": dep.description,
        "status": dep.status,
        "created_by_id": dep.created_by_id,
        "resolved_by_id": dep.resolved_by_id,
        "created_at": dep.created_at,
        "resolved_at": dep.resolved_at,
    }


def _serialize_dependency_with_details(dep: SprintDependency) -> dict:
    """Serialize SprintDependency with sprint and project details."""
    result = _serialize_dependency(dep)

    # Add source sprint details
    if dep.source_sprint:
        result["source_sprint_number"] = dep.source_sprint.number
        result["source_sprint_name"] = dep.source_sprint.name
        result["source_project_id"] = dep.source_sprint.project_id
        if dep.source_sprint.project:
            result["source_project_name"] = dep.source_sprint.project.name
        else:
            result["source_project_name"] = None
    else:
        result["source_sprint_number"] = None
        result["source_sprint_name"] = None
        result["source_project_id"] = None
        result["source_project_name"] = None

    # Add target sprint details
    if dep.target_sprint:
        result["target_sprint_number"] = dep.target_sprint.number
        result["target_sprint_name"] = dep.target_sprint.name
        result["target_project_id"] = dep.target_sprint.project_id
        if dep.target_sprint.project:
            result["target_project_name"] = dep.target_sprint.project.name
        else:
            result["target_project_name"] = None
    else:
        result["target_sprint_number"] = None
        result["target_sprint_name"] = None
        result["target_project_id"] = None
        result["target_project_name"] = None

    # Check if cross-project
    result["is_cross_project"] = dep.is_cross_project

    return result


@router.post(
    "/dependencies",
    status_code=status.HTTP_201_CREATED,
    response_model=SprintDependencyResponse,
    summary="Create sprint dependency",
    tags=["Planning", "Dependencies", "Sprint 78"],
)
async def create_sprint_dependency(
    data: SprintDependencyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SprintDependencyResponse:
    """
    Create a dependency between two sprints.

    **Sprint 78: Cross-Project Sprint Dependencies - Day 2 Implementation**

    Dependency types:
    - **blocks**: Source sprint is blocked until target completes (critical)
    - **requires**: Source requires deliverable from target
    - **related**: Sprints are related but not blocking

    Validation:
    - Both sprints must exist
    - No self-reference allowed
    - Circular dependencies are prevented

    Args:
        data: Dependency creation data

    Returns:
        Created SprintDependencyResponse

    Raises:
        400: Invalid dependency (circular, self-reference, duplicate)
        404: Sprint not found
    """
    service = get_sprint_dependency_service(db)

    try:
        dependency = await service.create_dependency(
            source_sprint_id=data.source_sprint_id,
            target_sprint_id=data.target_sprint_id,
            dependency_type=data.dependency_type,
            description=data.description,
            user_id=current_user.id,
        )
        return _serialize_dependency(dependency)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "/dependencies/{dependency_id}",
    response_model=SprintDependencyWithDetails,
    summary="Get a sprint dependency",
    tags=["Planning", "Dependencies", "Sprint 78"],
)
async def get_sprint_dependency(
    dependency_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SprintDependencyWithDetails:
    """Get a single dependency with sprint details."""
    service = get_sprint_dependency_service(db)
    dependency = await service.get_dependency(dependency_id)

    if not dependency:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dependency not found",
        )

    return _serialize_dependency_with_details(dependency)


@router.put(
    "/dependencies/{dependency_id}",
    response_model=SprintDependencyResponse,
    summary="Update a sprint dependency",
    tags=["Planning", "Dependencies", "Sprint 78"],
)
async def update_sprint_dependency(
    dependency_id: UUID,
    data: SprintDependencyUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SprintDependencyResponse:
    """Update a dependency's type, description, or status."""
    service = get_sprint_dependency_service(db)

    dependency = await service.update_dependency(
        dependency_id=dependency_id,
        dependency_type=data.dependency_type,
        description=data.description,
        status=data.status,
    )

    if not dependency:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dependency not found",
        )

    return _serialize_dependency(dependency)


@router.post(
    "/dependencies/{dependency_id}/resolve",
    response_model=SprintDependencyResponse,
    summary="Resolve a sprint dependency",
    tags=["Planning", "Dependencies", "Sprint 78"],
)
async def resolve_sprint_dependency(
    dependency_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SprintDependencyResponse:
    """Mark a dependency as resolved."""
    service = get_sprint_dependency_service(db)

    dependency = await service.resolve_dependency(
        dependency_id=dependency_id,
        user_id=current_user.id,
    )

    if not dependency:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dependency not found",
        )

    return _serialize_dependency(dependency)


@router.delete(
    "/dependencies/{dependency_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a sprint dependency",
    tags=["Planning", "Dependencies", "Sprint 78"],
)
async def delete_sprint_dependency(
    dependency_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Soft delete a dependency."""
    service = get_sprint_dependency_service(db)

    success = await service.delete_dependency(dependency_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dependency not found",
        )


@router.get(
    "/sprints/{sprint_id}/dependencies",
    response_model=SprintDependencyListResponse,
    summary="List dependencies for a sprint",
    tags=["Planning", "Dependencies", "Sprint 78"],
)
async def list_sprint_dependencies(
    sprint_id: UUID,
    direction: str = Query("both", description="Direction: incoming, outgoing, or both"),
    include_resolved: bool = Query(False, description="Include resolved/cancelled"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SprintDependencyListResponse:
    """
    List dependencies for a specific sprint.

    Direction:
    - **incoming**: Dependencies where this sprint is the target
    - **outgoing**: Dependencies where this sprint is the source
    - **both**: All dependencies involving this sprint
    """
    # Verify sprint exists
    result = await db.execute(
        select(Sprint).where(Sprint.id == sprint_id)
    )
    sprint = result.scalar_one_or_none()

    if not sprint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sprint {sprint_id} not found",
        )

    service = get_sprint_dependency_service(db)
    dependencies = await service.get_sprint_dependencies(
        sprint_id=sprint_id,
        direction=direction,
        include_resolved=include_resolved,
    )

    # Paginate
    total = len(dependencies)
    start = (page - 1) * page_size
    end = start + page_size
    paginated = dependencies[start:end]

    return SprintDependencyListResponse(
        items=[_serialize_dependency(d) for d in paginated],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/projects/{project_id}/dependency-graph",
    response_model=DependencyGraph,
    summary="Get dependency graph for a project",
    tags=["Planning", "Dependencies", "Sprint 78"],
)
async def get_project_dependency_graph(
    project_id: UUID,
    include_cross_project: bool = Query(True, description="Include cross-project deps"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DependencyGraph:
    """
    Get dependency graph for visualization.

    **Sprint 78: Cross-Project Sprint Dependencies - Day 2 Implementation**

    Returns a graph structure with:
    - **nodes**: Sprints with status and blocking info
    - **edges**: Dependencies with type and status

    Suitable for rendering with visualization libraries like ReactFlow or D3.
    """
    # Check project access
    await check_project_access(db, project_id, current_user)

    service = get_sprint_dependency_service(db)
    return await service.get_dependency_graph(
        project_id=project_id,
        include_cross_project=include_cross_project,
    )


@router.get(
    "/projects/{project_id}/dependency-analysis",
    response_model=DependencyAnalysis,
    summary="Analyze project dependencies",
    tags=["Planning", "Dependencies", "Sprint 78"],
)
async def analyze_project_dependencies(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DependencyAnalysis:
    """
    Analyze dependency structure for a project.

    Returns:
    - Dependency counts by type and status
    - Critical path through dependency chain
    - Risk indicators (high-dependency sprints)
    """
    # Check project access
    await check_project_access(db, project_id, current_user)

    service = get_sprint_dependency_service(db)
    return await service.analyze_dependencies(project_id)


@router.post(
    "/dependencies/bulk/resolve",
    response_model=SprintDependencyBulkResult,
    summary="Bulk resolve dependencies",
    tags=["Planning", "Dependencies", "Sprint 78"],
)
async def bulk_resolve_dependencies(
    data: SprintDependencyBulkResolve,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SprintDependencyBulkResult:
    """Bulk resolve multiple dependencies."""
    service = get_sprint_dependency_service(db)

    success_count = 0
    failure_count = 0
    errors = []

    for dep_id in data.ids:
        try:
            result = await service.resolve_dependency(dep_id, current_user.id)
            if result:
                success_count += 1
            else:
                failure_count += 1
                errors.append({"id": str(dep_id), "error": "Not found"})
        except Exception as e:
            failure_count += 1
            errors.append({"id": str(dep_id), "error": str(e)})

    return SprintDependencyBulkResult(
        success_count=success_count,
        failure_count=failure_count,
        errors=errors,
    )


@router.get(
    "/dependencies/check-circular",
    summary="Check for circular dependency",
    tags=["Planning", "Dependencies", "Sprint 78"],
)
async def check_circular_dependency(
    source_sprint_id: UUID = Query(..., description="Source sprint"),
    target_sprint_id: UUID = Query(..., description="Target sprint"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Check if adding a dependency would create a cycle.

    Use this endpoint before creating a dependency to validate.
    """
    service = get_sprint_dependency_service(db)

    has_cycle = await service.has_circular_dependency(
        source_id=source_sprint_id,
        target_id=target_sprint_id,
    )

    if has_cycle:
        cycle_path = await service.find_cycle_path(
            source_id=source_sprint_id,
            target_id=target_sprint_id,
        )
        return {
            "would_create_cycle": True,
            "cycle_path": [str(sid) for sid in (cycle_path or [])],
            "message": "Creating this dependency would form a circular dependency chain",
        }

    return {
        "would_create_cycle": False,
        "cycle_path": [],
        "message": "No circular dependency would be created",
    }


# =========================================================================
# Resource Allocation Endpoints (Sprint 78 Day 3)
#
# Team member allocation to sprints with capacity calculation,
# conflict detection, and resource heatmap visualization
# =========================================================================


def _serialize_allocation(alloc: ResourceAllocation) -> dict:
    """Serialize ResourceAllocation to response dict."""
    return {
        "id": alloc.id,
        "sprint_id": alloc.sprint_id,
        "user_id": alloc.user_id,
        "allocation_percentage": alloc.allocation_percentage,
        "role": alloc.role,
        "start_date": alloc.start_date,
        "end_date": alloc.end_date,
        "notes": alloc.notes,
        "created_by_id": alloc.created_by_id,
        "created_at": alloc.created_at,
        "updated_at": alloc.updated_at,
    }


def _serialize_allocation_with_details(alloc: ResourceAllocation) -> dict:
    """Serialize ResourceAllocation with user and sprint details."""
    result = _serialize_allocation(alloc)

    # Add user details
    if alloc.user:
        result["user_name"] = alloc.user.full_name or alloc.user.username
        result["user_email"] = alloc.user.email
    else:
        result["user_name"] = None
        result["user_email"] = None

    # Add sprint details
    if alloc.sprint:
        result["sprint_number"] = alloc.sprint.number
        result["sprint_name"] = alloc.sprint.name
        result["project_id"] = alloc.sprint.project_id
    else:
        result["sprint_number"] = None
        result["sprint_name"] = None
        result["project_id"] = None

    return result


@router.post(
    "/allocations",
    status_code=status.HTTP_201_CREATED,
    response_model=ResourceAllocationResponse,
    summary="Create resource allocation",
    tags=["Planning", "Resource Allocation", "Sprint 78"],
)
async def create_resource_allocation(
    data: ResourceAllocationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ResourceAllocationResponse:
    """
    Allocate a team member to a sprint.

    **Sprint 78: Resource Allocation Optimization - Day 3 Implementation**

    Allocation validation:
    - User must exist
    - Sprint must exist
    - No duplicate allocation (user to same sprint)
    - Allocation percentage between 1-100%
    - Dates must be within sprint range
    - Total allocation across sprints cannot exceed 100%

    Args:
        data: Allocation creation data

    Returns:
        Created ResourceAllocationResponse

    Raises:
        400: Validation error or conflict detected
        404: Sprint or user not found
    """
    service = get_resource_allocation_service(db)

    try:
        allocation = await service.create_allocation(
            sprint_id=data.sprint_id,
            user_id=data.user_id,
            allocation_percentage=data.allocation_percentage,
            role=data.role,
            start_date=data.start_date,
            end_date=data.end_date,
            notes=data.notes,
            created_by_id=current_user.id,
        )
        return _serialize_allocation(allocation)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "/allocations/{allocation_id}",
    response_model=ResourceAllocationResponse,
    summary="Get a resource allocation",
    tags=["Planning", "Resource Allocation", "Sprint 78"],
)
async def get_resource_allocation(
    allocation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ResourceAllocationResponse:
    """Get a single allocation with user and sprint details."""
    service = get_resource_allocation_service(db)
    allocation = await service.get_allocation(allocation_id)

    if not allocation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Allocation not found",
        )

    return _serialize_allocation_with_details(allocation)


@router.put(
    "/allocations/{allocation_id}",
    response_model=ResourceAllocationResponse,
    summary="Update a resource allocation",
    tags=["Planning", "Resource Allocation", "Sprint 78"],
)
async def update_resource_allocation(
    allocation_id: UUID,
    data: ResourceAllocationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ResourceAllocationResponse:
    """Update an allocation's percentage, role, or dates."""
    service = get_resource_allocation_service(db)

    try:
        allocation = await service.update_allocation(
            allocation_id=allocation_id,
            allocation_percentage=data.allocation_percentage,
            role=data.role,
            start_date=data.start_date,
            end_date=data.end_date,
            notes=data.notes,
        )

        if not allocation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Allocation not found",
            )

        return _serialize_allocation(allocation)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete(
    "/allocations/{allocation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a resource allocation",
    tags=["Planning", "Resource Allocation", "Sprint 78"],
)
async def delete_resource_allocation(
    allocation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Soft delete an allocation."""
    service = get_resource_allocation_service(db)

    success = await service.delete_allocation(allocation_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Allocation not found",
        )


@router.get(
    "/sprints/{sprint_id}/allocations",
    response_model=ResourceAllocationListResponse,
    summary="List allocations for a sprint",
    tags=["Planning", "Resource Allocation", "Sprint 78"],
)
async def list_sprint_allocations(
    sprint_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ResourceAllocationListResponse:
    """
    List all team member allocations for a sprint.

    Returns paginated list of allocations with user details.
    """
    # Verify sprint exists
    result = await db.execute(
        select(Sprint).where(Sprint.id == sprint_id)
    )
    sprint = result.scalar_one_or_none()

    if not sprint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sprint {sprint_id} not found",
        )

    service = get_resource_allocation_service(db)
    allocations = await service.get_sprint_allocations(sprint_id)

    # Paginate
    total = len(allocations)
    start = (page - 1) * page_size
    end = start + page_size
    paginated = allocations[start:end]

    return ResourceAllocationListResponse(
        items=[_serialize_allocation_with_details(a) for a in paginated],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/users/{user_id}/allocations",
    response_model=ResourceAllocationListResponse,
    summary="List allocations for a user",
    tags=["Planning", "Resource Allocation", "Sprint 78"],
)
async def list_user_allocations(
    user_id: UUID,
    start_date: Optional[str] = Query(None, description="Filter from date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Filter to date (YYYY-MM-DD)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ResourceAllocationListResponse:
    """
    List all sprint allocations for a user.

    Optionally filter by date range.
    """
    from datetime import datetime as dt

    # Parse dates
    parsed_start = None
    parsed_end = None
    if start_date:
        parsed_start = dt.strptime(start_date, "%Y-%m-%d").date()
    if end_date:
        parsed_end = dt.strptime(end_date, "%Y-%m-%d").date()

    service = get_resource_allocation_service(db)
    allocations = await service.get_user_allocations(
        user_id=user_id,
        start_date=parsed_start,
        end_date=parsed_end,
    )

    # Paginate
    total = len(allocations)
    start = (page - 1) * page_size
    end = start + page_size
    paginated = allocations[start:end]

    return ResourceAllocationListResponse(
        items=[_serialize_allocation_with_details(a) for a in paginated],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/users/{user_id}/capacity",
    response_model=UserCapacity,
    summary="Get user capacity",
    tags=["Planning", "Resource Allocation", "Sprint 78"],
)
async def get_user_capacity(
    user_id: UUID,
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserCapacity:
    """
    Calculate user capacity for a date range.

    **Sprint 78: Resource Allocation Optimization - Day 3 Implementation**

    Returns:
    - Total working days in period
    - Allocated days across sprints
    - Available days
    - Utilization rate (%)
    - List of allocations
    """
    from datetime import datetime as dt

    parsed_start = dt.strptime(start_date, "%Y-%m-%d").date()
    parsed_end = dt.strptime(end_date, "%Y-%m-%d").date()

    service = get_resource_allocation_service(db)

    try:
        return await service.calculate_user_capacity(
            user_id=user_id,
            start_date=parsed_start,
            end_date=parsed_end,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get(
    "/teams/{team_id}/capacity",
    response_model=TeamCapacity,
    summary="Get team capacity",
    tags=["Planning", "Resource Allocation", "Sprint 78"],
)
async def get_team_capacity(
    team_id: UUID,
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TeamCapacity:
    """
    Calculate team capacity for a date range.

    **Sprint 78: Resource Allocation Optimization - Day 3 Implementation**

    Returns:
    - Total capacity hours for team
    - Allocated hours
    - Available hours
    - Utilization rate (%)
    - Breakdown by member
    - Breakdown by role
    """
    from datetime import datetime as dt

    parsed_start = dt.strptime(start_date, "%Y-%m-%d").date()
    parsed_end = dt.strptime(end_date, "%Y-%m-%d").date()

    service = get_resource_allocation_service(db)

    try:
        return await service.calculate_team_capacity(
            team_id=team_id,
            start_date=parsed_start,
            end_date=parsed_end,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get(
    "/sprints/{sprint_id}/capacity",
    response_model=SprintCapacity,
    summary="Get sprint capacity",
    tags=["Planning", "Resource Allocation", "Sprint 78"],
)
async def get_sprint_capacity(
    sprint_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SprintCapacity:
    """
    Calculate capacity for a sprint.

    **Sprint 78: Resource Allocation Optimization - Day 3 Implementation**

    Returns:
    - Team size (allocated members)
    - Total capacity hours
    - Allocated hours
    - Available hours
    - Utilization rate (%)
    - Breakdown by role
    """
    service = get_resource_allocation_service(db)

    try:
        return await service.calculate_sprint_capacity(sprint_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post(
    "/allocations/check-conflicts",
    response_model=ConflictCheckResult,
    summary="Check allocation conflicts",
    tags=["Planning", "Resource Allocation", "Sprint 78"],
)
async def check_allocation_conflicts(
    user_id: UUID = Query(..., description="User to check"),
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
    allocation_percentage: int = Query(..., ge=1, le=100, description="Proposed allocation %"),
    exclude_sprint_id: Optional[UUID] = Query(None, description="Sprint to exclude (for updates)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ConflictCheckResult:
    """
    Check if an allocation would create conflicts.

    **Sprint 78: Resource Allocation Optimization - Day 3 Implementation**

    Use this endpoint before creating/updating an allocation to validate.

    Returns:
    - Whether conflicts exist
    - List of conflicts with details
    - Warnings for high utilization
    """
    from datetime import datetime as dt

    parsed_start = dt.strptime(start_date, "%Y-%m-%d").date()
    parsed_end = dt.strptime(end_date, "%Y-%m-%d").date()

    service = get_resource_allocation_service(db)

    return await service.detect_conflicts(
        user_id=user_id,
        start_date=parsed_start,
        end_date=parsed_end,
        new_percentage=allocation_percentage,
        exclude_sprint_id=exclude_sprint_id,
    )


@router.get(
    "/projects/{project_id}/resource-heatmap",
    response_model=ResourceHeatmap,
    summary="Get resource allocation heatmap",
    tags=["Planning", "Resource Allocation", "Sprint 78"],
)
async def get_project_resource_heatmap(
    project_id: UUID,
    sprint_ids: Optional[str] = Query(None, description="Comma-separated sprint IDs to include"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ResourceHeatmap:
    """
    Get resource allocation heatmap for visualization.

    **Sprint 78: Resource Allocation Optimization - Day 3 Implementation**

    Returns a heatmap structure with:
    - **users**: List of users with allocations
    - **sprints**: List of sprints
    - **cells**: Allocation data for each user-sprint combination

    Suitable for rendering with visualization libraries.

    Cell status values:
    - **available**: No allocation (0%)
    - **partial**: Partial allocation (1-99%)
    - **full**: Full allocation (100%)
    - **over_allocated**: Over-allocated (>100%)
    """
    # Check project access
    await check_project_access(db, project_id, current_user)

    # Parse sprint IDs if provided
    parsed_sprint_ids = None
    if sprint_ids:
        try:
            parsed_sprint_ids = [UUID(sid.strip()) for sid in sprint_ids.split(",")]
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid sprint ID format",
            )

    service = get_resource_allocation_service(db)
    return await service.generate_heatmap(
        project_id=project_id,
        sprint_ids=parsed_sprint_ids,
    )


# =========================================================================
# Sprint Template Endpoints (Sprint 78 Day 4)
#
# Reusable sprint configuration templates
# Standard, feature, bugfix, release template types
# =========================================================================


def _serialize_template(template: SprintTemplate) -> dict:
    """Serialize SprintTemplate to response dict."""
    return {
        "id": template.id,
        "name": template.name,
        "description": template.description,
        "template_type": template.template_type,
        "duration_days": template.duration_days,
        "default_capacity_points": template.default_capacity_points,
        "backlog_structure": template.backlog_structure,
        "gates_enabled": template.gates_enabled,
        "goal_template": template.goal_template,
        "team_id": template.team_id,
        "is_public": template.is_public,
        "is_default": template.is_default,
        "usage_count": template.usage_count,
        "created_by_id": template.created_by_id,
        "created_at": template.created_at,
        "updated_at": template.updated_at,
    }


def _serialize_template_with_details(template: SprintTemplate) -> dict:
    """Serialize SprintTemplate with additional details."""
    result = _serialize_template(template)

    # Add team name
    if template.team:
        result["team_name"] = template.team.name
    else:
        result["team_name"] = None

    # Add creator name
    if template.created_by:
        result["created_by_name"] = template.created_by.full_name or template.created_by.username
    else:
        result["created_by_name"] = None

    # Add computed fields
    result["backlog_item_count"] = template.backlog_item_count
    result["total_story_points"] = template.total_story_points

    return result


@router.post(
    "/templates",
    status_code=status.HTTP_201_CREATED,
    response_model=SprintTemplateResponse,
    summary="Create sprint template",
    tags=["Planning", "Templates", "Sprint 78"],
)
async def create_sprint_template(
    data: SprintTemplateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SprintTemplateResponse:
    """
    Create a new sprint template.

    **Sprint 78: Sprint Template Library - Day 4 Implementation**

    Template types:
    - **standard**: Standard 2-week sprint
    - **feature**: Feature-focused sprint
    - **bugfix**: Bug-fix focused sprint
    - **release**: Release preparation sprint
    - **custom**: Custom configuration

    Templates can include:
    - Default duration and capacity
    - Pre-defined backlog structure
    - Sprint goal template
    - Gate configuration

    Args:
        data: Template creation data

    Returns:
        Created SprintTemplateResponse
    """
    service = get_sprint_template_service(db)

    # Convert backlog structure to list of dicts
    backlog_structure = None
    if data.backlog_structure:
        backlog_structure = [item.model_dump() for item in data.backlog_structure]

    template = await service.create_template(
        name=data.name,
        description=data.description,
        template_type=data.template_type,
        duration_days=data.duration_days,
        default_capacity_points=data.default_capacity_points,
        gates_enabled=data.gates_enabled,
        goal_template=data.goal_template,
        team_id=data.team_id,
        is_public=data.is_public,
        is_default=data.is_default,
        backlog_structure=backlog_structure,
        created_by_id=current_user.id,
    )

    return _serialize_template(template)


@router.get(
    "/templates/{template_id}",
    response_model=SprintTemplateWithDetails,
    summary="Get a sprint template",
    tags=["Planning", "Templates", "Sprint 78"],
)
async def get_sprint_template(
    template_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SprintTemplateWithDetails:
    """Get a single template with details."""
    service = get_sprint_template_service(db)
    template = await service.get_template(template_id)

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found",
        )

    return _serialize_template_with_details(template)


@router.put(
    "/templates/{template_id}",
    response_model=SprintTemplateResponse,
    summary="Update a sprint template",
    tags=["Planning", "Templates", "Sprint 78"],
)
async def update_sprint_template(
    template_id: UUID,
    data: SprintTemplateUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SprintTemplateResponse:
    """Update a template's configuration."""
    service = get_sprint_template_service(db)

    # Convert backlog structure if provided
    backlog_structure = None
    if data.backlog_structure is not None:
        backlog_structure = [item.model_dump() for item in data.backlog_structure]

    template = await service.update_template(
        template_id=template_id,
        name=data.name,
        description=data.description,
        template_type=data.template_type,
        duration_days=data.duration_days,
        default_capacity_points=data.default_capacity_points,
        gates_enabled=data.gates_enabled,
        goal_template=data.goal_template,
        is_public=data.is_public,
        is_default=data.is_default,
        backlog_structure=backlog_structure,
    )

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found",
        )

    return _serialize_template(template)


@router.delete(
    "/templates/{template_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a sprint template",
    tags=["Planning", "Templates", "Sprint 78"],
)
async def delete_sprint_template(
    template_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Soft delete a template."""
    service = get_sprint_template_service(db)

    success = await service.delete_template(template_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found",
        )


@router.get(
    "/templates",
    response_model=SprintTemplateListResponse,
    summary="List sprint templates",
    tags=["Planning", "Templates", "Sprint 78"],
)
async def list_sprint_templates(
    team_id: Optional[UUID] = Query(None, description="Filter by team"),
    template_type: Optional[str] = Query(None, description="Filter by type"),
    include_public: bool = Query(True, description="Include public templates"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SprintTemplateListResponse:
    """
    List available sprint templates.

    **Sprint 78: Sprint Template Library - Day 4 Implementation**

    Filters:
    - **team_id**: Team-specific templates
    - **template_type**: Filter by type (standard, feature, bugfix, release, custom)
    - **include_public**: Include public templates (default: true)

    Returns paginated list sorted by:
    1. Default templates first
    2. Usage count (popularity)
    """
    service = get_sprint_template_service(db)
    templates, total = await service.list_templates(
        team_id=team_id,
        template_type=template_type,
        include_public=include_public,
        page=page,
        page_size=page_size,
    )

    return SprintTemplateListResponse(
        items=[_serialize_template(t) for t in templates],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post(
    "/templates/{template_id}/apply",
    response_model=ApplyTemplateResponse,
    summary="Apply template to create sprint",
    tags=["Planning", "Templates", "Sprint 78"],
)
async def apply_sprint_template(
    template_id: UUID,
    data: ApplyTemplateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApplyTemplateResponse:
    """
    Create a new sprint from a template.

    **Sprint 78: Sprint Template Library - Day 4 Implementation**

    Copies from template:
    - Duration configuration
    - Capacity points
    - Gate settings
    - Backlog structure (if include_backlog=true)

    Can override:
    - Sprint name
    - Goal
    - Team size

    Args:
        template_id: Template to apply
        data: Apply template request

    Returns:
        ApplyTemplateResponse with created sprint info

    Raises:
        400: Validation error
        404: Template or project not found
    """
    # Check project access
    await check_project_access(db, data.project_id, current_user)

    service = get_sprint_template_service(db)

    try:
        result = await service.apply_template(
            template_id=template_id,
            project_id=data.project_id,
            start_date=data.start_date,
            phase_id=data.phase_id,
            sprint_name=data.sprint_name,
            goal=data.goal,
            team_size=data.team_size,
            include_backlog=data.include_backlog,
            created_by_id=current_user.id,
        )
        return result

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "/projects/{project_id}/template-suggestions",
    response_model=TemplateSuggestionsResponse,
    summary="Get template suggestions for project",
    tags=["Planning", "Templates", "Sprint 78"],
)
async def get_template_suggestions(
    project_id: UUID,
    team_id: Optional[UUID] = Query(None, description="Team for filtering"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TemplateSuggestionsResponse:
    """
    Get template suggestions based on project context.

    **Sprint 78: Sprint Template Library - Day 4 Implementation**

    Analyzes:
    - Recent sprint patterns
    - Project characteristics
    - Template popularity

    Returns top 5 suggestions with match scores.
    """
    # Check project access
    await check_project_access(db, project_id, current_user)

    service = get_sprint_template_service(db)
    suggestions = await service.suggest_templates(
        project_id=project_id,
        team_id=team_id,
    )

    return TemplateSuggestionsResponse(
        suggestions=suggestions,
        project_context={"project_id": str(project_id)},
    )


@router.get(
    "/templates/default",
    response_model=SprintTemplateResponse,
    summary="Get default template",
    tags=["Planning", "Templates", "Sprint 78"],
)
async def get_default_template(
    team_id: Optional[UUID] = Query(None, description="Team for filtering"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SprintTemplateResponse:
    """
    Get the default template for a team or organization.

    Returns team-specific default if available, otherwise public default.
    """
    service = get_sprint_template_service(db)
    template = await service.get_default_template(team_id=team_id)

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No default template found",
        )

    return _serialize_template(template)


@router.post(
    "/templates/bulk/delete",
    response_model=SprintTemplateBulkResult,
    summary="Bulk delete templates",
    tags=["Planning", "Templates", "Sprint 78"],
)
async def bulk_delete_templates(
    data: SprintTemplateBulkDelete,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SprintTemplateBulkResult:
    """Bulk delete multiple templates."""
    service = get_sprint_template_service(db)

    success_count = 0
    failure_count = 0
    errors = []

    for template_id in data.ids:
        try:
            result = await service.delete_template(template_id)
            if result:
                success_count += 1
            else:
                failure_count += 1
                errors.append({"id": str(template_id), "error": "Not found"})
        except Exception as e:
            failure_count += 1
            errors.append({"id": str(template_id), "error": str(e)})

    return SprintTemplateBulkResult(
        success_count=success_count,
        failure_count=failure_count,
        errors=errors,
    )