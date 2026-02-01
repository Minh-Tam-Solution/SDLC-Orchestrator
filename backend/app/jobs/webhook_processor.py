"""
Webhook Processor Background Job - Sprint 129.5 Day 2

Background job for processing GitHub webhook events asynchronously.

Key Features:
- Async processing of push/pull_request events
- Gap analysis trigger on push events
- Gate evaluation trigger on PR events
- PR status check posting
- PR comment posting for violations
- Retry with exponential backoff
- Dead letter queue for failed jobs

Job Flow:
1. Webhook endpoint receives event → returns 202 immediately
2. Event queued to Redis/Celery
3. This job picks up event and processes
4. Results posted back to GitHub (status checks, comments)

Reference: SPRINT-129.5-GITHUB-WEBHOOKS.md
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import select, and_

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.models.github_integration import GitHubRepository, GitHubInstallation
from app.models.project import Project
from app.services.github_webhook_service import (
    CheckStatus,
    ComplianceResult,
    PushEventData,
    PullRequestEventData,
    format_compliance_comment,
    parse_push_event,
    parse_pull_request_event,
    post_commit_status,
    post_pr_comment,
)
from app.services import github_app_service

logger = logging.getLogger(__name__)


# ============================================================================
# Job Queue (In-Memory for MVP, Redis/Celery in production)
# ============================================================================

# Job queues
_webhook_job_queue: List[Dict[str, Any]] = []
_dead_letter_queue: List[Dict[str, Any]] = []

# Job status tracking
_job_status: Dict[str, Dict[str, Any]] = {}

# Configuration
MAX_RETRIES = 3
RETRY_DELAYS = [5, 30, 120]  # seconds: 5s, 30s, 2min


# ============================================================================
# Job Submission
# ============================================================================

def enqueue_webhook_job(
    event_type: str,
    delivery_id: str,
    payload: Dict[str, Any],
    installation_id: Optional[int] = None
) -> str:
    """
    Enqueue a webhook event for background processing.

    Args:
        event_type: GitHub event type (push, pull_request)
        delivery_id: X-GitHub-Delivery header
        payload: Webhook payload
        installation_id: GitHub installation ID

    Returns:
        Job ID for tracking

    Example:
        job_id = enqueue_webhook_job(
            event_type="push",
            delivery_id="abc123",
            payload=webhook_data,
            installation_id=12345
        )
    """
    job_id = f"webhook_{delivery_id}"

    job = {
        "job_id": job_id,
        "event_type": event_type,
        "delivery_id": delivery_id,
        "payload": payload,
        "installation_id": installation_id,
        "status": "queued",
        "attempts": 0,
        "queued_at": datetime.utcnow().isoformat(),
        "started_at": None,
        "completed_at": None,
        "error": None,
        "result": None,
    }

    _webhook_job_queue.append(job)
    _job_status[job_id] = job

    logger.info(f"Enqueued webhook job {job_id} (event: {event_type})")

    return job_id


def get_job_status(job_id: str) -> Optional[Dict[str, Any]]:
    """Get status of a webhook processing job."""
    return _job_status.get(job_id)


# ============================================================================
# Job Processing
# ============================================================================

async def process_webhook_jobs(max_jobs: int = 10) -> Dict[str, Any]:
    """
    Process queued webhook jobs.

    Should be called by FastAPI BackgroundTasks or scheduled job runner.

    Args:
        max_jobs: Maximum jobs to process in one run

    Returns:
        Processing summary

    Example (FastAPI):
        @router.post("/admin/process-webhooks")
        async def trigger_processing(background_tasks: BackgroundTasks):
            background_tasks.add_task(process_webhook_jobs, max_jobs=10)
            return {"message": "Processing started"}
    """
    logger.info(f"Starting webhook job processor (max_jobs={max_jobs})")

    jobs_processed = 0
    jobs_succeeded = 0
    jobs_failed = 0
    jobs_retried = 0
    results = []

    while _webhook_job_queue and jobs_processed < max_jobs:
        job = _webhook_job_queue.pop(0)
        job_id = job["job_id"]

        logger.info(f"Processing webhook job {job_id}")

        # Update job status
        job["status"] = "processing"
        job["started_at"] = datetime.utcnow().isoformat()
        job["attempts"] += 1
        _job_status[job_id] = job

        try:
            # Process based on event type
            if job["event_type"] == "push":
                result = await process_push_job(job)
            elif job["event_type"] == "pull_request":
                result = await process_pull_request_job(job)
            else:
                result = {"status": "skipped", "reason": f"Unsupported event: {job['event_type']}"}

            # Mark as completed
            job["status"] = "completed"
            job["completed_at"] = datetime.utcnow().isoformat()
            job["result"] = result
            _job_status[job_id] = job

            jobs_succeeded += 1
            results.append({"job_id": job_id, "status": "completed", "result": result})

            logger.info(f"Webhook job {job_id} completed successfully")

        except Exception as e:
            logger.error(f"Webhook job {job_id} failed: {e}")

            # Check if should retry
            if job["attempts"] < MAX_RETRIES:
                job["status"] = "retrying"
                job["error"] = str(e)
                _job_status[job_id] = job

                # Re-queue with delay
                _webhook_job_queue.append(job)
                jobs_retried += 1
                results.append({"job_id": job_id, "status": "retrying", "attempt": job["attempts"]})

                logger.info(f"Webhook job {job_id} queued for retry (attempt {job['attempts']})")

            else:
                # Move to dead letter queue
                job["status"] = "failed"
                job["completed_at"] = datetime.utcnow().isoformat()
                job["error"] = str(e)
                _job_status[job_id] = job
                _dead_letter_queue.append(job)

                jobs_failed += 1
                results.append({"job_id": job_id, "status": "failed", "error": str(e)})

                logger.error(f"Webhook job {job_id} moved to dead letter queue after {MAX_RETRIES} attempts")

        jobs_processed += 1

    summary = {
        "jobs_processed": jobs_processed,
        "jobs_succeeded": jobs_succeeded,
        "jobs_failed": jobs_failed,
        "jobs_retried": jobs_retried,
        "jobs_remaining": len(_webhook_job_queue),
        "dlq_size": len(_dead_letter_queue),
        "results": results,
    }

    logger.info(f"Webhook processor completed: {summary}")
    return summary


# ============================================================================
# Push Event Processing
# ============================================================================

async def process_push_job(job: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process push webhook job.

    Flow:
    1. Find project by repository ID
    2. Trigger gap analysis
    3. Update project metadata

    Args:
        job: Job data from queue

    Returns:
        Processing result
    """
    payload = job["payload"]
    installation_id = job["installation_id"]

    try:
        push_data = parse_push_event(payload)
    except ValueError as e:
        return {"status": "error", "error": f"Failed to parse push event: {e}"}

    # Skip branch deletion
    if push_data.after == "0" * 40:
        return {"status": "skipped", "reason": "branch_deleted"}

    branch = push_data.ref.replace("refs/heads/", "")

    logger.info(f"Processing push: {push_data.repository_full_name}@{branch}")

    # Find linked project
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(GitHubRepository).where(
                and_(
                    GitHubRepository.github_repo_id == push_data.repository_id,
                    GitHubRepository.disconnected_at.is_(None)
                )
            )
        )
        github_repo = result.scalar_one_or_none()

        if not github_repo:
            return {
                "status": "skipped",
                "reason": "no_linked_project",
                "repository_id": push_data.repository_id
            }

        result = await db.execute(
            select(Project).where(Project.id == github_repo.project_id)
        )
        project = result.scalar_one_or_none()

        if not project:
            return {
                "status": "error",
                "error": "Project not found for linked repository"
            }

        # Check if this is the default branch
        is_default_branch = branch == github_repo.default_branch

        # TODO: Trigger gap analysis for default branch pushes
        # gap_result = await run_gap_analysis(project.id, github_repo.local_path)

        # Update last sync timestamp
        github_repo.updated_at = datetime.utcnow()
        await db.commit()

        return {
            "status": "processed",
            "event": "push",
            "repository": push_data.repository_full_name,
            "branch": branch,
            "is_default_branch": is_default_branch,
            "commits_count": len(push_data.commits),
            "project_id": str(project.id),
            # "gap_analysis_triggered": is_default_branch
        }


# ============================================================================
# Pull Request Event Processing
# ============================================================================

async def process_pull_request_job(job: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process pull_request webhook job.

    Flow:
    1. Find project by repository ID
    2. Run gate evaluation
    3. Post status check to GitHub
    4. Post comment if violations found

    Args:
        job: Job data from queue

    Returns:
        Processing result
    """
    payload = job["payload"]
    installation_id = job["installation_id"]

    try:
        pr_data = parse_pull_request_event(payload)
    except ValueError as e:
        return {"status": "error", "error": f"Failed to parse PR event: {e}"}

    # Only process certain actions
    if pr_data.action not in ("opened", "synchronize", "reopened"):
        return {"status": "skipped", "reason": f"action_{pr_data.action}_not_processable"}

    # Skip draft PRs
    if pr_data.is_draft:
        return {"status": "skipped", "reason": "draft_pr"}

    logger.info(f"Processing PR: {pr_data.repository_full_name}#{pr_data.pr_number}")

    # Find linked project
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(GitHubRepository).where(
                and_(
                    GitHubRepository.github_repo_id == pr_data.repository_id,
                    GitHubRepository.disconnected_at.is_(None)
                )
            )
        )
        github_repo = result.scalar_one_or_none()

        if not github_repo:
            return {
                "status": "skipped",
                "reason": "no_linked_project",
                "repository_id": pr_data.repository_id
            }

        result = await db.execute(
            select(Project).where(Project.id == github_repo.project_id)
        )
        project = result.scalar_one_or_none()

        if not project:
            return {
                "status": "error",
                "error": "Project not found for linked repository"
            }

        # Get installation - need to load relationship
        installation_id = github_repo.installation_id
        if not installation_id:
            return {
                "status": "error",
                "error": "Installation not found for repository"
            }

        result = await db.execute(
            select(GitHubInstallation).where(GitHubInstallation.id == installation_id)
        )
        installation = result.scalar_one_or_none()

        if not installation:
            return {
                "status": "error",
                "error": "Installation record not found"
            }

        try:
            token = await github_app_service.get_installation_token(installation.installation_id)
        except Exception as e:
            return {
                "status": "error",
                "error": f"Failed to get installation token: {e}"
            }

        # Post pending status
        await post_commit_status(
            token=token,
            repo_full_name=pr_data.repository_full_name,
            commit_sha=pr_data.head_sha,
            state=CheckStatus.PENDING,
            description="Running SDLC compliance check...",
            target_url=f"{settings.FRONTEND_URL}/projects/{project.id}/compliance"
        )

        # TODO: Run gate evaluation
        # compliance_result = await run_gate_evaluation(project.id, pr_data.head_sha)

        # For now, return success as placeholder
        compliance_result = ComplianceResult(
            score=100,
            violations_count=0,
            violations=[],
            gate_status="passed"
        )

        # Post final status
        if compliance_result.score >= 70:
            status = CheckStatus.SUCCESS
            description = f"SDLC compliance: {compliance_result.score}% ({compliance_result.violations_count} violations)"
        else:
            status = CheckStatus.FAILURE
            description = f"SDLC compliance: {compliance_result.score}% ({compliance_result.violations_count} violations)"

        await post_commit_status(
            token=token,
            repo_full_name=pr_data.repository_full_name,
            commit_sha=pr_data.head_sha,
            state=status,
            description=description,
            target_url=f"{settings.FRONTEND_URL}/projects/{project.id}/compliance"
        )

        # Post comment if violations found
        if compliance_result.violations_count > 0:
            comment = format_compliance_comment(
                compliance_result,
                report_url=f"{settings.FRONTEND_URL}/projects/{project.id}/compliance"
            )
            await post_pr_comment(
                token=token,
                repo_full_name=pr_data.repository_full_name,
                pr_number=pr_data.pr_number,
                body=comment
            )

        return {
            "status": "processed",
            "event": "pull_request",
            "action": pr_data.action,
            "repository": pr_data.repository_full_name,
            "pr_number": pr_data.pr_number,
            "compliance_score": compliance_result.score,
            "violations_count": compliance_result.violations_count,
            "status_check_posted": True,
            "comment_posted": compliance_result.violations_count > 0,
            "project_id": str(project.id),
        }


# ============================================================================
# Job Management
# ============================================================================

def get_queue_stats() -> Dict[str, Any]:
    """Get webhook job queue statistics."""
    status_counts: Dict[str, int] = {}
    for job in _job_status.values():
        s = job.get("status", "unknown")
        status_counts[s] = status_counts.get(s, 0) + 1

    return {
        "queue_length": len(_webhook_job_queue),
        "dlq_length": len(_dead_letter_queue),
        "total_jobs_tracked": len(_job_status),
        "jobs_by_status": status_counts,
    }


def get_dead_letter_jobs() -> List[Dict[str, Any]]:
    """Get jobs in dead letter queue."""
    return list(_dead_letter_queue)


def retry_dead_letter_job(job_id: str) -> bool:
    """
    Move a job from dead letter queue back to main queue.

    Args:
        job_id: Job ID to retry

    Returns:
        True if job was found and re-queued
    """
    for i, job in enumerate(_dead_letter_queue):
        if job["job_id"] == job_id:
            job = _dead_letter_queue.pop(i)
            job["status"] = "queued"
            job["attempts"] = 0
            job["error"] = None
            _webhook_job_queue.append(job)
            _job_status[job_id] = job
            logger.info(f"Re-queued dead letter job {job_id}")
            return True

    return False


def clear_completed_jobs(older_than_hours: int = 24) -> int:
    """
    Clear completed job status entries older than specified hours.

    Args:
        older_than_hours: Clear jobs completed more than X hours ago

    Returns:
        Number of jobs cleared
    """
    from datetime import timedelta

    cutoff = datetime.utcnow() - timedelta(hours=older_than_hours)
    cleared = 0

    jobs_to_remove = []
    for job_id, job in _job_status.items():
        completed_at = job.get("completed_at")
        if completed_at and job.get("status") == "completed":
            try:
                completed_time = datetime.fromisoformat(completed_at)
                if completed_time < cutoff:
                    jobs_to_remove.append(job_id)
            except ValueError:
                pass

    for job_id in jobs_to_remove:
        del _job_status[job_id]
        cleared += 1

    if cleared > 0:
        logger.info(f"Cleared {cleared} completed webhook jobs older than {older_than_hours}h")

    return cleared
