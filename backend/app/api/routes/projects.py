"""
File: backend/app/api/routes/projects.py
Version: 1.0.0
Status: ACTIVE - STAGE 03 (BUILD)
Date: 2025-11-27
Authority: Backend Lead + CTO Approved
Foundation: SDLC 4.9 Complete Lifecycle, Zero Mock Policy

Description:
Projects API routes for SDLC Orchestrator.
Provides CRUD operations for projects.
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
from app.api.dependencies import get_current_user
from app.models.user import User
from app.services.cache_service import (
    cache_service,
    invalidate_projects_cache,
    CACHE_TTL_SHORT,
    PROJECTS_CACHE,
)

router = APIRouter(prefix="/projects", tags=["projects"])


class ProjectCreate(BaseModel):
    """Schema for creating a new project"""
    name: str = Field(..., min_length=1, max_length=255, description="Project name")
    description: Optional[str] = Field(None, max_length=2000, description="Project description")


class ProjectUpdate(BaseModel):
    """Schema for updating a project"""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Project name")
    description: Optional[str] = Field(None, max_length=2000, description="Project description")


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


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_project(
    data: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new project.

    The current user becomes the project owner.
    """
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

    # Create project
    project = Project(
        name=data.name,
        slug=slug,
        description=data.description,
        owner_id=current_user.id,
        is_active=True,
    )
    db.add(project)
    await db.flush()  # Get the project ID

    # Add owner as project member with 'owner' role
    member = ProjectMember(
        project_id=project.id,
        user_id=current_user.id,
        role="owner",
        joined_at=datetime.utcnow(),
    )
    db.add(member)
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

    # Main query with LEFT JOIN to gate stats
    result = await db.execute(
        select(
            Project,
            func.coalesce(gate_stats_subq.c.total_gates, 0).label("total_gates"),
            func.coalesce(gate_stats_subq.c.approved, 0).label("approved"),
            func.coalesce(gate_stats_subq.c.rejected, 0).label("rejected"),
            func.coalesce(gate_stats_subq.c.max_stage, "00").label("max_stage"),
        )
        .outerjoin(gate_stats_subq, Project.id == gate_stats_subq.c.project_id)
        .where(Project.deleted_at.is_(None))
        .order_by(Project.updated_at.desc())
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

    # Calculate current stage from highest gate stage
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

    if not member and not current_user.is_superuser:
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

    # Check if user is owner or superuser
    if project.owner_id != current_user.id and not current_user.is_superuser:
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
