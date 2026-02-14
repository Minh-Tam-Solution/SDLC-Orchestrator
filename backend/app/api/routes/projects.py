"""
File: backend/app/api/routes/projects.py
Version: 1.1.0
Status: ACTIVE - STAGE 03 (BUILD)
Date: 2026-02-01
Authority: Backend Lead + CTO Approved
Foundation: SDLC 6.0.5 Complete Lifecycle, Zero Mock Policy

Description:
Projects API routes for SDLC Orchestrator.
Provides CRUD operations for projects.
Sprint 136: Added project context update endpoint (SSOT principle).
"""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select, func, case, literal_column
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID
import re

from app.db.session import get_db
from app.models.project import Project, ProjectMember
from app.models.gate import Gate
from app.models.policy_pack import PolicyPack
from app.models.agents_md import ContextOverlay
from app.api.dependencies import get_current_user
from app.models.user import User
from app.services.cache_service import (
    cache_service,
    invalidate_projects_cache,
    CACHE_TTL_SHORT,
    PROJECTS_CACHE,
)
from app.services.settings_service import SettingsService
from app.services.gate_auto_creation_service import create_default_gates
from app.services.project_metadata_service import project_metadata_service

router = APIRouter(prefix="/projects", tags=["projects"])


class ProjectCreate(BaseModel):
    """Schema for creating a new project"""
    name: str = Field(..., min_length=1, max_length=255, description="Project name")
    description: Optional[str] = Field(None, max_length=2000, description="Project description")
    policy_pack: Optional[str] = Field(
        "standard",
        description="Governance tier: lite, standard, professional, enterprise"
    )
    team_id: Optional[str] = Field(None, description="Team ID to assign project to (Sprint 73)")
    skip_auto_creation: bool = Field(
        False,
        description="Skip auto-creation of default gates (BUG #7 fix - Sprint 73)"
    )
    github_repo_id: Optional[int] = Field(None, description="GitHub repository ID if importing from GitHub")
    github_repo_full_name: Optional[str] = Field(None, description="GitHub repository full name (owner/repo)")


class ProjectUpdate(BaseModel):
    """Schema for updating a project"""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Project name")
    description: Optional[str] = Field(None, max_length=2000, description="Project description")


class ProjectContextUpdate(BaseModel):
    """
    Schema for updating project context (stage, gate, sprint).
    
    Sprint 136 - SSOT Principle:
    - Database is the Single Source of Truth
    - Extension/Dashboard READ from database
    - Admin UI/CLI WRITE to database via this endpoint
    """
    stage: Optional[str] = Field(
        None,
        description="Current SDLC stage: FOUNDATION, PLANNING, DESIGN, INTEGRATE, BUILD, TEST, DEPLOY, OPERATE, GOVERN, ARCHIVE"
    )
    gate: Optional[str] = Field(
        None,
        description="Current/last passed gate: G0.1, G0.2, G1, G2, G3, G4, G5, G6, G7, G8, G9"
    )
    sprint_number: Optional[int] = Field(
        None,
        ge=1,
        description="Current sprint number (e.g., 136)"
    )
    sprint_goal: Optional[str] = Field(
        None,
        max_length=500,
        description="Current sprint goal"
    )
    strict_mode: Optional[bool] = Field(
        None,
        description="Post-G3 strict mode (bug fixes only)"
    )


class ProjectContextResponse(BaseModel):
    """Response schema for project context"""
    project_id: str
    stage: Optional[str]
    gate: Optional[str]
    sprint_number: Optional[int]
    sprint_goal: Optional[str]
    strict_mode: bool
    updated_at: str


def slugify(text: str) -> str:
    """Convert text to URL-friendly slug"""
    # Convert to lowercase and replace spaces with hyphens
    slug = text.lower().strip()
    # Remove special characters except hyphens and alphanumeric
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    # Replace spaces with hyphens
    slug = re.sub(r'[\s_]+', '-', slug)
    # Remove consecutive hyphens
    slug = re.sub(r'-+', '-', slug)
    # Remove leading/trailing hyphens
    slug = slug.strip('-')
    return slug


# Tier to display name mapping
TIER_NAMES = {
    "lite": "Lite",
    "standard": "Standard",
    "professional": "Professional",
    "enterprise": "Enterprise",
}

# Default validators per tier
TIER_VALIDATORS = {
    "lite": [
        {"name": "lint", "enabled": True, "blocking": False, "config": {}},
    ],
    "standard": [
        {"name": "lint", "enabled": True, "blocking": True, "config": {}},
        {"name": "security", "enabled": True, "blocking": True, "config": {}},
    ],
    "professional": [
        {"name": "lint", "enabled": True, "blocking": True, "config": {}},
        {"name": "security", "enabled": True, "blocking": True, "config": {}},
        {"name": "context", "enabled": True, "blocking": True, "config": {}},
        {"name": "test", "enabled": True, "blocking": True, "config": {}},
    ],
    "enterprise": [
        {"name": "lint", "enabled": True, "blocking": True, "config": {}},
        {"name": "security", "enabled": True, "blocking": True, "config": {}},
        {"name": "context", "enabled": True, "blocking": True, "config": {}},
        {"name": "test", "enabled": True, "blocking": True, "config": {}},
        {"name": "architecture", "enabled": True, "blocking": True, "config": {}},
    ],
}

# Coverage thresholds per tier
TIER_COVERAGE = {
    "lite": 0,
    "standard": 60,
    "professional": 80,
    "enterprise": 95,
}


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_project(
    data: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new project with optional policy pack configuration.

    The current user becomes the project owner.

    Args:
        data: ProjectCreate schema with name, description, policy_pack, and optional GitHub fields

    Returns:
        Created project with ID, slug, and policy pack tier

    ADR-027 Phase 2:
        Enforces max_projects_per_user limit from system settings.
    """
    # ADR-027 Phase 2: Check max_projects_per_user limit
    settings_service = SettingsService(db)
    max_projects = await settings_service.get_max_projects_per_user()

    # Count user's owned projects
    owned_count_result = await db.execute(
        select(func.count(Project.id)).where(
            Project.owner_id == current_user.id,
            Project.deleted_at.is_(None),
        )
    )
    owned_count = owned_count_result.scalar() or 0

    if owned_count >= max_projects:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Project limit reached. You own {owned_count} projects (max: {max_projects}). "
            f"Delete existing projects or contact admin to increase limit.",
        )

    # Validate tier
    tier = (data.policy_pack or "standard").lower()
    if tier not in TIER_NAMES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid policy_pack: {tier}. Must be one of: lite, standard, professional, enterprise",
        )

    # Generate unique slug
    base_slug = slugify(data.name)
    slug = base_slug
    counter = 1

    # Check for slug uniqueness
    while True:
        result = await db.execute(
            select(Project).where(Project.slug == slug)
        )
        existing = result.scalar_one_or_none()
        if not existing:
            break
        slug = f"{base_slug}-{counter}"
        counter += 1

    # Create project with optional GitHub fields and team assignment (Sprint 73)
    project = Project(
        name=data.name,
        slug=slug,
        description=data.description,
        owner_id=current_user.id,
        is_active=True,
        team_id=UUID(data.team_id) if data.team_id else None,  # Sprint 73 - Teams Integration
        github_repo_id=data.github_repo_id,
        github_repo_full_name=data.github_repo_full_name,
        github_sync_status="synced" if data.github_repo_id else None,
        github_synced_at=datetime.utcnow() if data.github_repo_id else None,
    )
    db.add(project)
    await db.flush()  # Get the project ID

    # Create PolicyPack for the project
    policy_pack = PolicyPack(
        project_id=project.id,
        name=f"{TIER_NAMES[tier]} Policy Pack",
        description=f"Auto-configured {TIER_NAMES[tier]} tier policy pack for {data.name}",
        tier=tier,
        validators=TIER_VALIDATORS.get(tier, []),
        coverage_threshold=TIER_COVERAGE.get(tier, 60),
        coverage_blocking=(tier in ["professional", "enterprise"]),
        forbidden_imports=["minio", "grafana_sdk"] if tier != "lite" else [],
        required_patterns=[],
        created_by=current_user.id,
    )
    db.add(policy_pack)

    # Add owner as project member with 'owner' role
    member = ProjectMember(
        project_id=project.id,
        user_id=current_user.id,
        role="owner",
        joined_at=datetime.utcnow(),
    )
    db.add(member)

    # BUG #7 Fix (Sprint 73): Auto-create default gates for new project
    # Create 5 default gates: Planning, Design, Code Review, Test, Deploy
    auto_created_gates = await create_default_gates(
        db=db,
        project_id=project.id,
        created_by=current_user.id,
        skip_auto_creation=data.skip_auto_creation,
        team_id=project.team_id,
    )

    await db.commit()
    await db.refresh(project)

    # Invalidate projects cache
    await invalidate_projects_cache()

    return {
        "id": str(project.id),
        "name": project.name,
        "slug": project.slug,
        "description": project.description,
        "owner_id": str(project.owner_id),
        "is_active": project.is_active,
        "policy_pack": tier,
        "team_id": str(project.team_id) if project.team_id else None,  # Sprint 73
        "gates_created": len(auto_created_gates),  # BUG #7 fix - Sprint 73
        "github_repo_id": project.github_repo_id,
        "github_repo_full_name": project.github_repo_full_name,
        "created_at": project.created_at.isoformat() if project.created_at else None,
        "updated_at": project.updated_at.isoformat() if project.updated_at else None,
    }


@router.get("")
async def list_projects(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100,
):
    """
    List all projects with gate status summary.

    Sprint 23 Day 2 Optimization:
    - Changed from N+1 queries to single query with subqueries
    - Performance improvement: ~200ms -> ~50ms (75% faster)
    - Added Redis caching (60s TTL) for further optimization
    """
    # Check cache first
    cache_key = cache_service._make_key(
        f"{PROJECTS_CACHE}:list",
        user_id=str(current_user.id),
        skip=skip,
        limit=limit,
    )
    cached_result = await cache_service.get(cache_key)
    if cached_result is not None:
        return cached_result

    # Subquery for gate statistics per project
    gate_stats_subq = (
        select(
            Gate.project_id,
            func.count(Gate.id).label("total_gates"),
            func.sum(case((Gate.status == "APPROVED", 1), else_=0)).label("approved"),
            func.sum(case((Gate.status == "REJECTED", 1), else_=0)).label("rejected"),
            func.max(Gate.stage).label("max_stage"),
        )
        .where(Gate.deleted_at.is_(None))
        .group_by(Gate.project_id)
        .subquery()
    )

    # Sprint 88: Platform admins CANNOT access customer data
    # Build organization filter query
    query = (
        select(
            Project,
            func.coalesce(gate_stats_subq.c.total_gates, 0).label("total_gates"),
            func.coalesce(gate_stats_subq.c.approved, 0).label("approved"),
            func.coalesce(gate_stats_subq.c.rejected, 0).label("rejected"),
            func.coalesce(gate_stats_subq.c.max_stage, "00").label("max_stage"),
        )
        .outerjoin(gate_stats_subq, Project.id == gate_stats_subq.c.project_id)
        .where(Project.deleted_at.is_(None))
    )

    # Regular admin (non-platform): can see all projects
    is_regular_admin = current_user.is_superuser and not current_user.is_platform_admin
    if not is_regular_admin:
        # Platform admin or regular user: only projects from their organization
        # Filter through owner's organization_id
        query = query.join(User, Project.owner_id == User.id).where(
            User.organization_id == current_user.organization_id
        )

    # Execute query with ordering and pagination
    result = await db.execute(
        query.order_by(Project.updated_at.desc())
        .offset(skip)
        .limit(limit)
    )
    rows = result.all()

    project_list = []
    for row in rows:
        project = row[0]
        total_gates = row[1]
        approved = row[2]
        rejected = row[3]
        max_stage = row[4]

        # Determine overall status
        if rejected > 0:
            gate_status = "failed"
        elif total_gates - approved - rejected > 0:
            gate_status = "pending"
        elif approved > 0:
            gate_status = "passed"
        else:
            gate_status = "not_started"

        # Calculate progress (approved gates / total stages)
        # SDLC 4.9 has 10 stages (00-09), each with at least 1 gate
        progress = min(100, round((approved / 10) * 100)) if total_gates > 0 else 0

        project_list.append({
            "id": str(project.id),
            "name": project.name,
            "description": project.description or "",
            "current_stage": max_stage,
            "gate_status": gate_status,
            "progress": progress,
            "created_at": project.created_at.isoformat() if project.created_at else None,
            "updated_at": project.updated_at.isoformat() if project.updated_at else None,
        })

    # Cache result for 60 seconds
    await cache_service.set(cache_key, project_list, CACHE_TTL_SHORT)

    return project_list


@router.get("/{project_id}")
async def get_project(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get a single project by ID.
    """
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

    # Get gates for this project
    gates_result = await db.execute(
        select(Gate)
        .where(Gate.project_id == project_id, Gate.deleted_at.is_(None))
        .order_by(Gate.stage, Gate.created_at)
    )
    gates = gates_result.scalars().all()

    # Sprint 136: Read current_stage from ContextOverlay (SSOT) if exists
    # Fallback to calculating from gates if no context overlay
    context_result = await db.execute(
        select(ContextOverlay)
        .where(ContextOverlay.project_id == project_id)
        .order_by(ContextOverlay.generated_at.desc())
        .limit(1)
    )
    context_overlay = context_result.scalar_one_or_none()

    if context_overlay and context_overlay.stage_name:
        current_stage = context_overlay.stage_name
    else:
        # Fallback: Calculate from highest gate stage
        current_stage = max((gate.stage for gate in gates), default="00")

    return {
        "id": str(project.id),
        "name": project.name,
        "description": project.description,
        "current_stage": current_stage,
        "created_at": project.created_at.isoformat() if project.created_at else None,
        "updated_at": project.updated_at.isoformat() if project.updated_at else None,
        "gates": [
            {
                "id": str(gate.id),
                "gate_name": gate.gate_name,
                "gate_type": gate.gate_type,
                "stage": gate.stage,
                "status": gate.status,
                "description": gate.description,
                "created_at": gate.created_at.isoformat() if gate.created_at else None,
            }
            for gate in gates
        ],
    }


@router.put("/{project_id}")
async def update_project(
    project_id: UUID,
    data: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update a project.

    Only project owners and admins can update projects.
    """
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

    # Check if user has permission (owner or admin)
    member_result = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == current_user.id,
            ProjectMember.role.in_(["owner", "admin"]),
        )
    )
    member = member_result.scalar_one_or_none()

    # Sprint 88: Platform admins CANNOT access customer data
    is_regular_admin = current_user.is_superuser and not current_user.is_platform_admin
    if not member and not is_regular_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this project",
        )

    # Update fields
    if data.name is not None:
        project.name = data.name
    if data.description is not None:
        project.description = data.description

    await db.commit()
    await db.refresh(project)

    # Invalidate projects cache
    await invalidate_projects_cache()

    return {
        "id": str(project.id),
        "name": project.name,
        "slug": project.slug,
        "description": project.description,
        "owner_id": str(project.owner_id),
        "is_active": project.is_active,
        "created_at": project.created_at.isoformat() if project.created_at else None,
        "updated_at": project.updated_at.isoformat() if project.updated_at else None,
    }


@router.put(
    "/{project_id}/context",
    response_model=ProjectContextResponse,
    summary="Update project context (stage, gate, sprint)",
    description="""
    Update the current SDLC context for a project.
    
    **SSOT Principle (Sprint 136)**:
    - Database is the Single Source of Truth
    - Extension/Dashboard READ from this data
    - Admin UI/CLI WRITE via this endpoint
    
    **Valid Stages**: FOUNDATION, PLANNING, DESIGN, INTEGRATE, BUILD, TEST, DEPLOY, OPERATE, GOVERN, ARCHIVE
    **Valid Gates**: G0.1, G0.2, G1, G2, G3, G4, G5, G6, G7, G8, G9
    """,
)
async def update_project_context(
    project_id: UUID,
    data: ProjectContextUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update project SDLC context (stage, gate, sprint).
    
    Sprint 136 - SSOT Design Principle:
    - Database as Single Source of Truth
    - NOT local files → sync → backend (wrong direction)
    - Correct: Admin UI/CLI → API → Database → Extension/Dashboard
    
    Only project owners and admins can update context.
    """
    # Validate stage value
    valid_stages = [
        "FOUNDATION", "PLANNING", "DESIGN", "INTEGRATE", "BUILD",
        "TEST", "DEPLOY", "OPERATE", "GOVERN", "ARCHIVE"
    ]
    if data.stage and data.stage.upper() not in valid_stages:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid stage. Must be one of: {', '.join(valid_stages)}"
        )
    
    # Validate gate value
    valid_gates = ["G0.1", "G0.2", "G1", "G2", "G3", "G4", "G5", "G6", "G7", "G8", "G9"]
    if data.gate and data.gate.upper() not in [g.upper() for g in valid_gates]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid gate. Must be one of: {', '.join(valid_gates)}"
        )
    
    # Get project
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

    # Check permission (owner, admin, or regular superuser)
    member_result = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == current_user.id,
            ProjectMember.role.in_(["owner", "admin"]),
        )
    )
    member = member_result.scalar_one_or_none()

    is_regular_admin = current_user.is_superuser and not current_user.is_platform_admin
    if not member and not is_regular_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this project's context",
        )

    # Get or create context overlay for this project
    overlay_result = await db.execute(
        select(ContextOverlay)
        .where(ContextOverlay.project_id == project_id)
        .order_by(ContextOverlay.generated_at.desc())
        .limit(1)
    )
    existing_overlay = overlay_result.scalar_one_or_none()
    
    # Create new context overlay (audit trail)
    from uuid import uuid4
    new_overlay = ContextOverlay(
        id=uuid4(),
        project_id=project_id,
        stage_name=data.stage.upper() if data.stage else (existing_overlay.stage_name if existing_overlay else None),
        gate_status=data.gate if data.gate else (existing_overlay.gate_status if existing_overlay else None),
        sprint_number=data.sprint_number if data.sprint_number is not None else (existing_overlay.sprint_number if existing_overlay else None),
        sprint_goal=data.sprint_goal if data.sprint_goal is not None else (existing_overlay.sprint_goal if existing_overlay else None),
        strict_mode=data.strict_mode if data.strict_mode is not None else (existing_overlay.strict_mode if existing_overlay else False),
        constraints=[],
        generated_at=datetime.utcnow(),
        trigger_type="api",
        trigger_ref=f"PUT /projects/{project_id}/context by {current_user.email}",
    )
    
    db.add(new_overlay)
    await db.commit()
    await db.refresh(new_overlay)
    
    # Invalidate cache
    await invalidate_projects_cache()
    
    return ProjectContextResponse(
        project_id=str(project_id),
        stage=new_overlay.stage_name,
        gate=new_overlay.gate_status,
        sprint_number=new_overlay.sprint_number,
        sprint_goal=new_overlay.sprint_goal,
        strict_mode=new_overlay.strict_mode,
        updated_at=new_overlay.generated_at.isoformat(),
    )


@router.get(
    "/{project_id}/context",
    response_model=ProjectContextResponse,
    summary="Get project context (stage, gate, sprint)",
    description="Get the current SDLC context for a project (SSOT read endpoint).",
)
async def get_project_context(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get project SDLC context (stage, gate, sprint).
    
    SSOT Read Endpoint - Extension and Dashboard use this.
    """
    # Get project
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

    # Check membership
    member_result = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == current_user.id,
        )
    )
    member = member_result.scalar_one_or_none()

    is_regular_admin = current_user.is_superuser and not current_user.is_platform_admin
    if not member and not is_regular_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view this project's context",
        )

    # Get latest context overlay
    overlay_result = await db.execute(
        select(ContextOverlay)
        .where(ContextOverlay.project_id == project_id)
        .order_by(ContextOverlay.generated_at.desc())
        .limit(1)
    )
    overlay = overlay_result.scalar_one_or_none()
    
    if not overlay:
        # Return default context if no overlay exists
        return ProjectContextResponse(
            project_id=str(project_id),
            stage="FOUNDATION",
            gate="G0.1",
            sprint_number=None,
            sprint_goal=None,
            strict_mode=False,
            updated_at=project.created_at.isoformat() if project.created_at else datetime.utcnow().isoformat(),
        )
    
    return ProjectContextResponse(
        project_id=str(project_id),
        stage=overlay.stage_name,
        gate=overlay.gate_status,
        sprint_number=overlay.sprint_number,
        sprint_goal=overlay.sprint_goal,
        strict_mode=overlay.strict_mode,
        updated_at=overlay.generated_at.isoformat() if overlay.generated_at else datetime.utcnow().isoformat(),
    )


@router.post(
    "/{project_id}/sync",
    summary="Sync project metadata from repository files",
    description="""
    Sync project metadata from repository files to database.

    **Sprint 172 - Project Metadata Auto-Sync**:
    - Parses .sdlc-config.json, AGENTS.md, CLAUDE.md, README.md
    - Updates database with synced metadata
    - 5-min cache to prevent excessive file I/O
    - <200ms p95 latency target

    **ADR-029 Compliance**: Static AGENTS.md + Dynamic Overlay pattern

    **Sources**:
    - .sdlc-config.json: project.id, name, tier
    - AGENTS.md (lines 20-30): current_sprint, sprint_status, sprint_description
    - CLAUDE.md (lines 1-15): framework_version, gate_status
    - README.md: description (first paragraph)
    - Git metadata: last_commit_date, last_commit_sha
    """,
)
async def sync_project_metadata(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Sync project metadata from repository files.

    Sprint 172 Day 1 Task 1.2 - API Endpoint

    Flow:
    1. Check permissions (project member only)
    2. Check 5-min cache (Redis) - skip if recently synced
    3. Call ProjectMetadataService.sync_project_metadata()
    4. Update database with extracted metadata
    5. Set cache (5-min TTL)
    6. Return updated project

    Performance: <200ms p95 (cache miss), <50ms (cache hit)
    """
    # 1. Check project exists
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

    # 2. Check permissions (project member only)
    member_result = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == current_user.id,
        )
    )
    member = member_result.scalar_one_or_none()

    # Sprint 88: Platform admins CANNOT access customer data
    is_regular_admin = current_user.is_superuser and not current_user.is_platform_admin
    if not member and not is_regular_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to sync this project",
        )

    # 3. Check 5-min cache (Redis) - skip sync if recently synced
    cache_key = cache_service._make_key(f"{PROJECTS_CACHE}:sync", project_id=str(project_id))
    cached_result = await cache_service.get(cache_key)
    if cached_result is not None:
        # Return cached project data (skip file parsing)
        return cached_result

    # 4. Get repository path from project
    # For SDLC-Orchestrator: /home/nqh/shared/SDLC-Orchestrator
    # For other projects: /home/nqh/shared/{project.slug}
    if str(project.id) == "c0000000-0000-0000-0000-000000000003":
        repo_path = "/home/nqh/shared/SDLC-Orchestrator"
    else:
        repo_path = f"/home/nqh/shared/{project.slug}"

    # 5. Call ProjectMetadataService to parse files
    try:
        metadata = await project_metadata_service.sync_project_metadata(
            project_id=project_id,
            repo_path=repo_path,
        )
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repository not found: {str(e)}",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid repository: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync metadata: {str(e)}",
        )

    # 6. Update database with synced metadata
    if metadata.name:
        project.name = metadata.name
    if metadata.description:
        project.description = metadata.description

    project.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(project)

    # 7. Build response
    response = {
        "id": str(project.id),
        "name": project.name,
        "slug": project.slug,
        "description": project.description,
        "owner_id": str(project.owner_id),
        "is_active": project.is_active,
        "created_at": project.created_at.isoformat() if project.created_at else None,
        "updated_at": project.updated_at.isoformat() if project.updated_at else None,
        # Include synced metadata
        "metadata": {
            "tier": metadata.tier,
            "current_sprint": metadata.current_sprint,
            "sprint_status": metadata.sprint_status,
            "sprint_description": metadata.sprint_description,
            "framework_version": metadata.framework_version,
            "gate_status": metadata.gate_status,
            "last_commit_date": metadata.last_commit_date,
            "last_commit_sha": metadata.last_commit_sha,
        },
    }

    # 8. Set cache (5-min TTL = 300 seconds)
    await cache_service.set(cache_key, response, ttl=300)

    # 9. Invalidate projects cache to refresh list
    await invalidate_projects_cache()

    return response


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete a project (soft delete).

    Only project owners can delete projects.
    """
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

    # Sprint 88: Platform admins CANNOT access customer data
    # Check if user is owner or regular admin (not platform admin)
    is_regular_admin = current_user.is_superuser and not current_user.is_platform_admin
    if project.owner_id != current_user.id and not is_regular_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only project owners can delete projects",
        )

    # Soft delete
    project.deleted_at = datetime.utcnow()
    project.is_active = False
    await db.commit()

    # Invalidate projects cache
    await invalidate_projects_cache()

    return None


# =========================================================================
# SDLC 5.0.0 Project Initialization (Sprint 32)
# =========================================================================


class SDLCTier(str):
    """SDLC tier enumeration."""

    LITE = "LITE"
    STANDARD = "STANDARD"
    PROFESSIONAL = "PROFESSIONAL"
    ENTERPRISE = "ENTERPRISE"


class ProjectInitRequest(BaseModel):
    """Request to initialize a new SDLC project from VS Code Extension."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Project name",
    )
    tier: str = Field(
        default="STANDARD",
        description="SDLC tier: LITE, STANDARD, PROFESSIONAL, ENTERPRISE",
    )
    source: str = Field(
        default="vscode",
        description="Source of initialization: vscode, web, cli",
    )
    description: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Project description",
    )


class SDLCConfigResponse(BaseModel):
    """SDLC configuration for .sdlc-config.json."""

    schema_url: str = Field(alias="$schema")
    version: str
    project: dict
    sdlc: dict
    server: dict
    gates: dict

    class Config:
        populate_by_name = True


class ProjectInitResponse(BaseModel):
    """Response from project initialization."""

    project_id: str
    name: str
    slug: str
    tier: str
    config: dict
    message: str


# SDLC 5.0.0 Stage Definitions (Contract-First Order)
# Folder names use SHORT format: XX-name (e.g., 00-foundation)
SDLC_STAGES = {
    "00": {"name": "foundation", "folder": "00-foundation"},
    "01": {"name": "planning", "folder": "01-planning"},
    "02": {"name": "design", "folder": "02-design"},
    "03": {"name": "integration", "folder": "03-integration"},
    "04": {"name": "build", "folder": "src"},
    "05": {"name": "test", "folder": "tests"},
    "06": {"name": "deploy", "folder": "infrastructure"},
    "07": {"name": "operate", "folder": "07-operate"},
    "08": {"name": "collaborate", "folder": "08-collaborate"},
    "09": {"name": "govern", "folder": "09-govern"},
}

TIER_REQUIRED_STAGES = {
    "LITE": ["00", "01", "04", "05", "06"],
    "STANDARD": ["00", "01", "02", "03", "04", "05", "06", "07"],
    "PROFESSIONAL": ["00", "01", "02", "03", "04", "05", "06", "07", "08"],
    "ENTERPRISE": ["00", "01", "02", "03", "04", "05", "06", "07", "08", "09"],
}


def build_stage_mapping(tier: str) -> dict:
    """Build stage mapping for .sdlc-config.json based on tier."""
    required_stages = TIER_REQUIRED_STAGES.get(tier, TIER_REQUIRED_STAGES["STANDARD"])
    mapping = {}

    for stage_id in required_stages:
        stage_info = SDLC_STAGES.get(stage_id, {})
        stage_name = stage_info.get("name", "unknown")
        folder = stage_info.get("folder", f"{stage_id}-Unknown")

        # Code folders don't have docs/ prefix
        if stage_id in ["04", "05", "06"]:
            mapping[f"{stage_id}-{stage_name}"] = folder
        else:
            mapping[f"{stage_id}-{stage_name}"] = f"docs/{folder}"

    return mapping


@router.post(
    "/init",
    response_model=ProjectInitResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Initialize SDLC project",
    description=(
        "Initialize a new SDLC 5.0.0 project. Creates project in database "
        "and returns configuration for .sdlc-config.json."
    ),
)
async def init_project(
    data: ProjectInitRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectInitResponse:
    """
    Initialize a new SDLC 5.0.0 project.

    Used by:
    - VS Code Extension /init command
    - Web Dashboard project creation
    - CLI sdlcctl init command

    Flow:
    1. Check max_projects_per_user limit (ADR-027 Phase 2)
    2. Create project in database
    3. Add user as project owner
    4. Generate .sdlc-config.json content
    5. Return project ID and configuration

    Args:
        data: Project initialization request
        current_user: Authenticated user

    Returns:
        ProjectInitResponse with project_id and config
    """
    # ADR-027 Phase 2: Check max_projects_per_user limit
    settings_service = SettingsService(db)
    max_projects = await settings_service.get_max_projects_per_user()

    owned_count_result = await db.execute(
        select(func.count(Project.id)).where(
            Project.owner_id == current_user.id,
            Project.deleted_at.is_(None),
        )
    )
    owned_count = owned_count_result.scalar() or 0

    if owned_count >= max_projects:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Project limit reached. You own {owned_count} projects (max: {max_projects}). "
            f"Delete existing projects or contact admin to increase limit.",
        )

    # Validate tier
    valid_tiers = ["LITE", "STANDARD", "PROFESSIONAL", "ENTERPRISE"]
    tier = data.tier.upper()
    if tier not in valid_tiers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid tier: {data.tier}. Must be one of: {valid_tiers}",
        )

    # Generate unique slug
    base_slug = slugify(data.name)
    slug = base_slug
    counter = 1

    while True:
        result = await db.execute(select(Project).where(Project.slug == slug))
        existing = result.scalar_one_or_none()
        if not existing:
            break
        slug = f"{base_slug}-{counter}"
        counter += 1

    # Create project
    project = Project(
        name=data.name,
        slug=slug,
        description=data.description or f"SDLC 5.0.0 {tier} project initialized from {data.source}",
        owner_id=current_user.id,
        is_active=True,
    )
    db.add(project)
    await db.flush()

    # Add owner as project member
    member = ProjectMember(
        project_id=project.id,
        user_id=current_user.id,
        role="owner",
        joined_at=datetime.utcnow(),
    )
    db.add(member)
    await db.commit()
    await db.refresh(project)

    # Invalidate cache
    await invalidate_projects_cache()

    # Build .sdlc-config.json content
    stage_mapping = build_stage_mapping(tier)

    config = {
        "$schema": "https://sdlc-orchestrator.io/schemas/config-v1.json",
        "version": "1.0.0",
        "project": {
            "id": str(project.id),
            "name": project.name,
            "slug": project.slug,
        },
        "sdlc": {
            "frameworkVersion": "5.0.0",
            "tier": tier,
            "stages": stage_mapping,
        },
        "server": {
            "url": "https://sdlc.mtsolution.com.vn",
            "connected": True,
        },
        "gates": {
            "current": "G0.1",
            "passed": [],
        },
    }

    return ProjectInitResponse(
        project_id=str(project.id),
        name=project.name,
        slug=project.slug,
        tier=tier,
        config=config,
        message=f"Project '{project.name}' initialized successfully with SDLC 5.0.0 {tier} tier",
    )


class MigrateStagesRequest(BaseModel):
    """Request to migrate project stages to SDLC 5.0.0."""

    old_stage_mapping: Optional[dict] = Field(
        default=None,
        description="Current stage mapping (if known)",
    )
    target_tier: str = Field(
        default="STANDARD",
        description="Target SDLC tier after migration",
    )


class MigrateStagesResponse(BaseModel):
    """Response from stage migration."""

    project_id: str
    old_mapping: dict
    new_mapping: dict
    changes: list
    config: dict


# Old SDLC 4.x stage mapping (before restructure)
OLD_STAGE_MAPPING = {
    "00": "WHY",
    "01": "WHAT",
    "02": "HOW",
    "03": "BUILD",
    "04": "TEST",
    "05": "DEPLOY",
    "06": "OPERATE",
    "07": "INTEGRATE",  # This moves to 03 in 5.0.0
    "08": "COLLABORATE",
    "09": "GOVERN",
}


@router.post(
    "/{project_id}/migrate-stages",
    response_model=MigrateStagesResponse,
    summary="Migrate project stages to SDLC 5.0.0",
    description=(
        "Migrate project from old stage structure to SDLC 5.0.0. "
        "Moves INTEGRATE from stage 07 to stage 03."
    ),
)
async def migrate_stages(
    project_id: UUID,
    data: MigrateStagesRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MigrateStagesResponse:
    """
    Migrate project stages to SDLC 5.0.0 structure.

    Key change in SDLC 5.0.0:
    - INTEGRATE moved from Stage 07 to Stage 03 (Contract-First)
    - Stages 03-06 shifted by +1

    Args:
        project_id: UUID of project to migrate
        data: Migration request with target tier
        current_user: Authenticated user

    Returns:
        MigrateStagesResponse with old/new mappings and changes
    """
    # Check project exists and user has access
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

    # Check permission
    member_result = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == current_user.id,
            ProjectMember.role.in_(["owner", "admin"]),
        )
    )
    member = member_result.scalar_one_or_none()

    # Sprint 88: Platform admins CANNOT access customer data
    is_regular_admin = current_user.is_superuser and not current_user.is_platform_admin
    if not member and not is_regular_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only project owners/admins can migrate stages",
        )

    # Validate tier
    tier = data.target_tier.upper()
    if tier not in TIER_REQUIRED_STAGES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid tier: {data.target_tier}",
        )

    # Determine old mapping
    old_mapping = data.old_stage_mapping or {
        f"{k}-{v.lower()}": f"docs/{k}-{v}"
        for k, v in OLD_STAGE_MAPPING.items()
    }

    # Generate new mapping
    new_mapping = build_stage_mapping(tier)

    # Calculate changes
    changes = []

    # Key change: INTEGRATE moves from 07 to 03
    if "07-integrate" in str(old_mapping).lower():
        changes.append({
            "type": "move",
            "from": "07-integrate → docs/07-Integration-Hub",
            "to": "03-integration → docs/03-Integration-API",
            "reason": "SDLC 5.0.0 Contract-First: API design before implementation",
        })

    # Stages 03-06 shift
    stage_shifts = [
        ("03-build", "04-build", "Shifted due to INTEGRATE move"),
        ("04-test", "05-test", "Shifted due to INTEGRATE move"),
        ("05-deploy", "06-deploy", "Shifted due to INTEGRATE move"),
        ("06-operate", "07-operate", "Shifted due to INTEGRATE move"),
    ]

    for old_stage, new_stage, reason in stage_shifts:
        if old_stage in str(old_mapping).lower():
            changes.append({
                "type": "rename",
                "from": old_stage,
                "to": new_stage,
                "reason": reason,
            })

    # Build new config
    config = {
        "$schema": "https://sdlc-orchestrator.io/schemas/config-v1.json",
        "version": "1.0.0",
        "project": {
            "id": str(project.id),
            "name": project.name,
            "slug": project.slug,
        },
        "sdlc": {
            "frameworkVersion": "5.0.0",
            "tier": tier,
            "stages": new_mapping,
            "migrated_from": "4.x",
            "migrated_at": datetime.utcnow().isoformat(),
        },
        "server": {
            "url": "https://sdlc.mtsolution.com.vn",
            "connected": True,
        },
        "gates": {
            "current": "G0.1",
            "passed": [],
        },
    }

    return MigrateStagesResponse(
        project_id=str(project.id),
        old_mapping=old_mapping,
        new_mapping=new_mapping,
        changes=changes,
        config=config,
    )
