"""
Sprint Command Handler — Sprint 194 (ENR-01).

Handles the ``update_sprint`` chat command (slot 6 of 10 in command registry).
Fetches the current sprint from DB, generates CURRENT-SPRINT.md via
SprintFileService, pushes to GitHub, and returns a confirmation summary.

Usage (via OTT or CLI):
    /update_sprint --project_id <uuid>
    "cập nhật sprint cho dự án X"
"""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.project import Project
from app.models.sprint import Sprint
from app.services.github_service import GitHubService
from app.services.sprint_file_service import SprintFileService

logger = logging.getLogger(__name__)


async def handle_update_sprint(
    db: AsyncSession,
    project_id: UUID,
    github_service: GitHubService | None = None,
) -> dict[str, Any]:
    """Execute the update_sprint command.

    Fetches active sprint for the project, generates CURRENT-SPRINT.md,
    and pushes to GitHub (if configured).

    Args:
        db: Async database session.
        project_id: Target project UUID.
        github_service: Optional GitHubService (injected for testability).

    Returns:
        Dict with keys: status, sprint_name, content_length, commit_sha, message.
    """
    # 1. Look up project
    project_result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = project_result.scalar_one_or_none()
    if project is None:
        return {
            "status": "error",
            "message": f"Project {project_id} not found.",
        }

    # 2. Find active sprint for project
    sprint_result = await db.execute(
        select(Sprint)
        .where(
            Sprint.project_id == project_id,
            Sprint.status == "ACTIVE",
        )
        .options(selectinload(Sprint.backlog_items))
        .order_by(Sprint.created_at.desc())
        .limit(1)
    )
    sprint = sprint_result.scalar_one_or_none()
    if sprint is None:
        return {
            "status": "error",
            "message": f"No active sprint found for project {project_id}.",
        }

    # 3. Generate CURRENT-SPRINT.md
    if github_service is None:
        github_service = GitHubService()

    file_svc = SprintFileService(db, github_service)
    content = file_svc.generate_current_sprint_md(sprint, project)

    # 4. Push to GitHub (if project has repo configured)
    commit_sha = await file_svc.push_to_github(project, content)

    result: dict[str, Any] = {
        "status": "success",
        "sprint_name": sprint.name,
        "sprint_number": getattr(sprint, "sprint_number", None),
        "content_length": len(content),
        "commit_sha": commit_sha,
    }

    if commit_sha:
        result["message"] = (
            f"CURRENT-SPRINT.md updated for sprint '{sprint.name}' "
            f"and pushed to GitHub (commit: {commit_sha[:8]})."
        )
    else:
        result["message"] = (
            f"CURRENT-SPRINT.md generated for sprint '{sprint.name}' "
            f"({len(content)} chars). No GitHub repo configured — skipped push."
        )

    logger.info(
        "update_sprint: project=%s sprint=%s push=%s",
        project_id,
        sprint.name,
        "yes" if commit_sha else "no",
    )
    return result
