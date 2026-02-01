"""
=========================================================================
GitHub Sync Background Jobs - Repository Synchronization Tasks
SDLC Orchestrator - Stage 03 (BUILD)

Version: 1.0.0
Date: November 28, 2025
Status: ACTIVE - Sprint 16 Day 4
Authority: Backend Lead + DevOps Lead Approved
Foundation: Sprint 15 GitHub Foundation, Sprint 16 Testing Plan
Framework: SDLC 4.9 Complete Lifecycle

Purpose:
- Background jobs for GitHub repository synchronization
- Webhook event processing (push, pull_request, issues)
- Scheduled polling for projects without webhooks
- Repository metadata refresh

Job Types:
1. schedule_project_sync: Queue sync for specific project
2. run_github_sync_job: Process queued sync jobs
3. process_webhook_event: Handle incoming webhook events
4. run_webhook_processing_job: Batch process webhook queue

Zero Mock Policy: Real GitHub API + database operations
=========================================================================
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import select, and_, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.models import Project, OAuthAccount
from app.services.github_service import GitHubAPIError, github_service
from app.services.project_sync_service import project_sync_service

logger = logging.getLogger(__name__)


# ============================================================================
# Job Queue (In-Memory for MVP, Redis in production)
# ============================================================================

# Simple in-memory queue for MVP
# In production, use Redis Queue or Celery
_sync_queue: list[dict[str, Any]] = []
_webhook_queue: list[dict[str, Any]] = []

# Job status tracking
_job_status: dict[str, dict[str, Any]] = {}


# ============================================================================
# Project Sync Jobs
# ============================================================================


async def schedule_project_sync(
    project_id: UUID,
    user_id: UUID,
    priority: str = "normal",
    force: bool = False,
) -> dict[str, Any]:
    """
    Schedule a project sync job for background execution.

    This function queues a sync job to be processed asynchronously,
    allowing the API to return immediately while sync runs in background.

    Args:
        project_id: UUID of project to sync
        user_id: UUID of user requesting sync
        priority: Job priority ("high", "normal", "low")
        force: Force sync even if recently synced

    Returns:
        Job info with job_id and status

    Example:
        job = await schedule_project_sync(
            project_id=project.id,
            user_id=current_user.id,
            priority="high"
        )
        print(f"Sync job {job['job_id']} queued")

    Usage in API:
        @router.post("/projects/{project_id}/sync")
        async def sync_project(
            project_id: UUID,
            background_tasks: BackgroundTasks,
            current_user: User = Depends(get_current_user)
        ):
            job = await schedule_project_sync(project_id, current_user.id)
            background_tasks.add_task(run_github_sync_job)
            return job
    """
    job_id = f"sync_{project_id}_{datetime.utcnow().timestamp()}"

    job = {
        "job_id": job_id,
        "type": "project_sync",
        "project_id": str(project_id),
        "user_id": str(user_id),
        "priority": priority,
        "force": force,
        "status": "queued",
        "queued_at": datetime.utcnow().isoformat(),
        "started_at": None,
        "completed_at": None,
        "error": None,
    }

    # Add to queue based on priority
    if priority == "high":
        _sync_queue.insert(0, job)
    else:
        _sync_queue.append(job)

    # Track job status
    _job_status[job_id] = job

    logger.info(f"Queued sync job {job_id} for project {project_id}")

    return {
        "job_id": job_id,
        "status": "queued",
        "project_id": str(project_id),
        "message": "Sync job queued for background processing",
    }


async def run_github_sync_job(max_jobs: int = 10) -> dict[str, Any]:
    """
    Process queued GitHub sync jobs.

    This function should be called by FastAPI BackgroundTasks or
    a scheduled job runner (APScheduler).

    Args:
        max_jobs: Maximum number of jobs to process in one run

    Returns:
        Summary of processed jobs

    Example (FastAPI BackgroundTasks):
        @router.post("/admin/run-sync")
        async def trigger_sync(background_tasks: BackgroundTasks):
            background_tasks.add_task(run_github_sync_job, max_jobs=5)
            return {"message": "Sync job started"}

    Example (Scheduled job):
        @scheduler.scheduled_job("interval", minutes=5)
        async def scheduled_sync():
            await run_github_sync_job(max_jobs=10)
    """
    logger.info(f"Starting sync job runner (max_jobs={max_jobs})")

    jobs_processed = 0
    jobs_succeeded = 0
    jobs_failed = 0
    results = []

    while _sync_queue and jobs_processed < max_jobs:
        job = _sync_queue.pop(0)
        job_id = job["job_id"]
        project_id = UUID(job["project_id"])
        user_id = UUID(job["user_id"])

        logger.info(f"Processing sync job {job_id}")

        # Update job status
        job["status"] = "running"
        job["started_at"] = datetime.utcnow().isoformat()
        _job_status[job_id] = job

        try:
            async with AsyncSessionLocal() as db:
                # Get OAuth account for user
                result = await db.execute(
                    select(OAuthAccount).where(
                        and_(
                            OAuthAccount.user_id == user_id,
                            OAuthAccount.provider == "github",
                        )
                    )
                )
                oauth_account = result.scalar_one_or_none()

                if not oauth_account:
                    raise ValueError(f"No GitHub connection for user {user_id}")

                # Get project
                result = await db.execute(
                    select(Project).where(Project.id == project_id)
                )
                project = result.scalar_one_or_none()

                if not project:
                    raise ValueError(f"Project {project_id} not found")

                if not project.github_repo_full_name:
                    raise ValueError(f"Project {project_id} has no GitHub repo linked")

                # Parse owner/repo from full_name
                owner, repo = project.github_repo_full_name.split("/", 1)

                # Run sync
                sync_result = await project_sync_service.sync_project(
                    project_id=project_id,
                    access_token=oauth_account.access_token,
                    owner=owner,
                    repo=repo,
                    db=db,
                    create_initial_gates=not job.get("force", False),
                )

                # Update job status
                job["status"] = "completed"
                job["completed_at"] = datetime.utcnow().isoformat()
                job["result"] = sync_result
                _job_status[job_id] = job

                jobs_succeeded += 1
                results.append({
                    "job_id": job_id,
                    "project_id": str(project_id),
                    "status": "completed",
                })

                logger.info(f"Sync job {job_id} completed successfully")

        except Exception as e:
            logger.error(f"Sync job {job_id} failed: {e}")

            job["status"] = "failed"
            job["completed_at"] = datetime.utcnow().isoformat()
            job["error"] = str(e)
            _job_status[job_id] = job

            jobs_failed += 1
            results.append({
                "job_id": job_id,
                "project_id": str(project_id),
                "status": "failed",
                "error": str(e),
            })

        jobs_processed += 1

    summary = {
        "jobs_processed": jobs_processed,
        "jobs_succeeded": jobs_succeeded,
        "jobs_failed": jobs_failed,
        "jobs_remaining": len(_sync_queue),
        "results": results,
    }

    logger.info(f"Sync job runner completed: {summary}")
    return summary


def get_sync_job_status(job_id: str) -> Optional[dict[str, Any]]:
    """
    Get status of a sync job.

    Args:
        job_id: Job ID returned from schedule_project_sync

    Returns:
        Job status dict or None if not found

    Example:
        status = get_sync_job_status("sync_abc123_1234567890")
        if status["status"] == "completed":
            print("Sync done!")
    """
    return _job_status.get(job_id)


def get_pending_sync_jobs() -> list[dict[str, Any]]:
    """
    Get list of pending sync jobs.

    Returns:
        List of queued job info
    """
    return [
        {
            "job_id": job["job_id"],
            "project_id": job["project_id"],
            "priority": job["priority"],
            "queued_at": job["queued_at"],
        }
        for job in _sync_queue
    ]


# ============================================================================
# Webhook Processing Jobs
# ============================================================================


async def process_webhook_event(
    event_type: str,
    payload: dict[str, Any],
    signature: str,
) -> dict[str, Any]:
    """
    Queue webhook event for background processing.

    This function validates the signature and queues the event
    for asynchronous processing.

    Args:
        event_type: GitHub event type (push, pull_request, etc.)
        payload: Webhook payload from GitHub
        signature: X-Hub-Signature-256 header value

    Returns:
        Processing result or queued status

    Example:
        result = await process_webhook_event(
            event_type="push",
            payload=request_body,
            signature=request.headers["X-Hub-Signature-256"]
        )
    """
    # Validate signature
    payload_bytes = str(payload).encode("utf-8")
    if not github_service.validate_webhook_signature(payload_bytes, signature):
        logger.warning("Invalid webhook signature")
        return {
            "received": False,
            "error": "Invalid signature",
        }

    # Extract repository info
    repo_info = payload.get("repository", {})
    repo_full_name = repo_info.get("full_name", "unknown")
    repo_id = repo_info.get("id")

    job_id = f"webhook_{repo_id}_{datetime.utcnow().timestamp()}"

    event = {
        "job_id": job_id,
        "type": "webhook",
        "event_type": event_type,
        "repository": repo_full_name,
        "repository_id": repo_id,
        "payload": payload,
        "status": "queued",
        "queued_at": datetime.utcnow().isoformat(),
    }

    _webhook_queue.append(event)
    _job_status[job_id] = event

    logger.info(f"Queued webhook event {job_id}: {event_type} for {repo_full_name}")

    return {
        "received": True,
        "job_id": job_id,
        "event_type": event_type,
        "repository": repo_full_name,
        "message": "Webhook queued for processing",
    }


async def run_webhook_processing_job(max_events: int = 50) -> dict[str, Any]:
    """
    Process queued webhook events.

    Handles different event types:
    - push: Update commit history, trigger sync if significant changes
    - pull_request: Create/update PR evidence, link to gates
    - issues: Create/update issue evidence
    - create/delete: Handle branch/tag events

    Args:
        max_events: Maximum events to process in one run

    Returns:
        Summary of processed events

    Example:
        @scheduler.scheduled_job("interval", seconds=30)
        async def process_webhooks():
            await run_webhook_processing_job(max_events=100)
    """
    logger.info(f"Starting webhook processor (max_events={max_events})")

    events_processed = 0
    events_succeeded = 0
    events_failed = 0
    results = []

    while _webhook_queue and events_processed < max_events:
        event = _webhook_queue.pop(0)
        job_id = event["job_id"]
        event_type = event["event_type"]
        payload = event["payload"]
        repo_id = event["repository_id"]

        logger.info(f"Processing webhook {job_id}: {event_type}")

        try:
            async with AsyncSessionLocal() as db:
                # Find project by GitHub repo ID
                result = await db.execute(
                    select(Project).where(
                        and_(
                            Project.github_repo_id == repo_id,
                            Project.deleted_at.is_(None),
                        )
                    )
                )
                project = result.scalar_one_or_none()

                if not project:
                    logger.info(f"No project found for repo {repo_id}, skipping")
                    event["status"] = "skipped"
                    event["message"] = "No linked project"
                    _job_status[job_id] = event
                    results.append({
                        "job_id": job_id,
                        "status": "skipped",
                        "reason": "No linked project",
                    })
                    events_processed += 1
                    continue

                # Process based on event type
                process_result = await _process_event_by_type(
                    project=project,
                    event_type=event_type,
                    payload=payload,
                    db=db,
                )

                event["status"] = "completed"
                event["completed_at"] = datetime.utcnow().isoformat()
                event["result"] = process_result
                _job_status[job_id] = event

                events_succeeded += 1
                results.append({
                    "job_id": job_id,
                    "status": "completed",
                    "result": process_result,
                })

                logger.info(f"Webhook {job_id} processed successfully")

        except Exception as e:
            logger.error(f"Webhook {job_id} processing failed: {e}")

            event["status"] = "failed"
            event["completed_at"] = datetime.utcnow().isoformat()
            event["error"] = str(e)
            _job_status[job_id] = event

            events_failed += 1
            results.append({
                "job_id": job_id,
                "status": "failed",
                "error": str(e),
            })

        events_processed += 1

    summary = {
        "events_processed": events_processed,
        "events_succeeded": events_succeeded,
        "events_failed": events_failed,
        "events_remaining": len(_webhook_queue),
        "results": results,
    }

    logger.info(f"Webhook processor completed: {summary}")
    return summary


async def _process_event_by_type(
    project: Project,
    event_type: str,
    payload: dict[str, Any],
    db: AsyncSession,
) -> dict[str, Any]:
    """
    Process webhook event based on type.

    Args:
        project: Project model instance
        event_type: GitHub event type
        payload: Webhook payload
        db: Database session

    Returns:
        Processing result
    """
    if event_type == "push":
        return await _handle_push_event(project, payload, db)
    elif event_type == "pull_request":
        return await _handle_pull_request_event(project, payload, db)
    elif event_type == "issues":
        return await _handle_issues_event(project, payload, db)
    elif event_type in ("create", "delete"):
        return await _handle_branch_event(project, event_type, payload, db)
    else:
        logger.info(f"Unhandled event type: {event_type}")
        return {"action": "ignored", "reason": f"Unhandled event type: {event_type}"}


async def _handle_push_event(
    project: Project,
    payload: dict[str, Any],
    db: AsyncSession,
) -> dict[str, Any]:
    """Handle push events - update sync timestamp, check for significant changes."""
    ref = payload.get("ref", "")
    commits = payload.get("commits", [])
    head_commit = payload.get("head_commit", {})

    # Update last activity timestamp
    project.github_synced_at = datetime.utcnow()
    await db.commit()

    # Check if this is a significant push (many commits, specific files)
    significant_files = [
        "requirements.txt", "pyproject.toml", "package.json",
        "Dockerfile", "docker-compose.yml",
        ".github/workflows",
    ]

    needs_full_sync = False
    for commit in commits:
        modified = commit.get("modified", []) + commit.get("added", [])
        if any(sf in f for f in modified for sf in significant_files):
            needs_full_sync = True
            break

    return {
        "action": "push_processed",
        "ref": ref,
        "commits_count": len(commits),
        "head_commit": head_commit.get("message", "")[:100],
        "needs_full_sync": needs_full_sync,
    }


async def _handle_pull_request_event(
    project: Project,
    payload: dict[str, Any],
    db: AsyncSession,
) -> dict[str, Any]:
    """Handle pull request events - could create evidence or update gate status."""
    action = payload.get("action")
    pr = payload.get("pull_request", {})
    pr_number = pr.get("number")
    pr_title = pr.get("title", "")
    pr_state = pr.get("state")

    # In production, would create/update evidence linked to appropriate gate
    # For MVP, just log and track

    return {
        "action": "pr_processed",
        "pr_action": action,
        "pr_number": pr_number,
        "pr_title": pr_title[:100],
        "pr_state": pr_state,
    }


async def _handle_issues_event(
    project: Project,
    payload: dict[str, Any],
    db: AsyncSession,
) -> dict[str, Any]:
    """Handle issues events - could sync to project management."""
    action = payload.get("action")
    issue = payload.get("issue", {})
    issue_number = issue.get("number")
    issue_title = issue.get("title", "")

    return {
        "action": "issue_processed",
        "issue_action": action,
        "issue_number": issue_number,
        "issue_title": issue_title[:100],
    }


async def _handle_branch_event(
    project: Project,
    event_type: str,
    payload: dict[str, Any],
    db: AsyncSession,
) -> dict[str, Any]:
    """Handle branch/tag create/delete events."""
    ref_type = payload.get("ref_type")  # branch or tag
    ref = payload.get("ref")  # branch/tag name

    return {
        "action": f"{ref_type}_{event_type}d",
        "ref_type": ref_type,
        "ref": ref,
    }


# ============================================================================
# Scheduled Sync (for projects without webhooks)
# ============================================================================


async def run_scheduled_sync_for_stale_projects(
    stale_hours: int = 24,
    max_projects: int = 10,
) -> dict[str, Any]:
    """
    Sync projects that haven't been synced recently.

    This is a fallback for projects that don't have webhooks configured.
    Should be run as a scheduled job (e.g., every 4 hours).

    Args:
        stale_hours: Hours since last sync to consider project stale
        max_projects: Maximum projects to sync per run

    Returns:
        Summary of scheduled syncs

    Example:
        @scheduler.scheduled_job("interval", hours=4)
        async def sync_stale_projects():
            await run_scheduled_sync_for_stale_projects(stale_hours=24)
    """
    logger.info(f"Checking for stale projects (older than {stale_hours}h)")

    stale_cutoff = datetime.utcnow() - timedelta(hours=stale_hours)
    jobs_queued = 0

    async with AsyncSessionLocal() as db:
        # Find projects that:
        # 1. Have GitHub repo linked
        # 2. Haven't been synced recently
        # 3. Are not currently syncing
        result = await db.execute(
            select(Project).where(
                and_(
                    Project.github_repo_id.isnot(None),
                    Project.deleted_at.is_(None),
                    Project.github_sync_status != "syncing",
                    (
                        (Project.github_synced_at.is_(None))
                        | (Project.github_synced_at < stale_cutoff)
                    ),
                )
            ).limit(max_projects)
        )
        stale_projects = result.scalars().all()

        for project in stale_projects:
            await schedule_project_sync(
                project_id=project.id,
                user_id=project.owner_id,
                priority="low",
            )
            jobs_queued += 1

    return {
        "stale_projects_found": len(stale_projects) if 'stale_projects' in locals() else 0,
        "jobs_queued": jobs_queued,
        "stale_threshold_hours": stale_hours,
    }


# ============================================================================
# Job Management
# ============================================================================


def clear_completed_jobs(older_than_hours: int = 24) -> int:
    """
    Clear completed job statuses older than specified hours.

    Args:
        older_than_hours: Clear jobs completed more than X hours ago

    Returns:
        Number of jobs cleared
    """
    cutoff = datetime.utcnow() - timedelta(hours=older_than_hours)
    cleared = 0

    jobs_to_remove = []
    for job_id, job in _job_status.items():
        completed_at = job.get("completed_at")
        if completed_at:
            completed_time = datetime.fromisoformat(completed_at)
            if completed_time < cutoff:
                jobs_to_remove.append(job_id)

    for job_id in jobs_to_remove:
        del _job_status[job_id]
        cleared += 1

    logger.info(f"Cleared {cleared} completed jobs older than {older_than_hours}h")
    return cleared


def get_job_queue_stats() -> dict[str, Any]:
    """
    Get statistics about job queues.

    Returns:
        Queue statistics
    """
    status_counts = {}
    for job in _job_status.values():
        status = job.get("status", "unknown")
        status_counts[status] = status_counts.get(status, 0) + 1

    return {
        "sync_queue_length": len(_sync_queue),
        "webhook_queue_length": len(_webhook_queue),
        "total_jobs_tracked": len(_job_status),
        "jobs_by_status": status_counts,
    }
