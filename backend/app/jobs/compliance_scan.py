"""
=========================================================================
Compliance Scan Background Jobs - Scheduled & On-Demand Scanning
SDLC Orchestrator - Stage 03 (BUILD)

Version: 1.0.0
Date: December 2, 2025
Status: ACTIVE - Sprint 21 Day 2
Authority: Backend Lead + CTO Approved
Foundation: Sprint 21 Plan, ADR-007 Approved
Framework: SDLC 4.9.1 Complete Lifecycle

Purpose:
- Scheduled daily compliance scans (2:00 AM)
- On-demand scan job scheduling
- Batch processing for multiple projects
- Scan result notification triggers

Job Types:
1. schedule_compliance_scan: Queue scan for specific project
2. run_daily_compliance_scan: Daily scheduled scan for all projects
3. run_compliance_scan_job: Process queued scan jobs
4. process_scan_results: Handle scan results and notifications

Integration:
- APScheduler for job scheduling
- Notification service for alerting
- Redis for job queue (production)

Zero Mock Policy: Real compliance scanning + notifications
=========================================================================
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Optional
from uuid import UUID, uuid4

from sqlalchemy import select, and_, func, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.models.compliance_scan import (
    ComplianceScan,
    ScanJob,
    ScanJobStatus,
    TriggerType,
)
from app.models.project import Project
from app.services.compliance_scanner import ComplianceScanner

logger = logging.getLogger(__name__)


# ============================================================================
# Scan Configuration
# ============================================================================

SCAN_CONFIG = {
    "daily_scan_hour": 2,  # 2:00 AM
    "daily_scan_minute": 0,
    "max_concurrent_scans": 5,
    "scan_timeout_seconds": 300,  # 5 minutes per project
    "retry_attempts": 3,
    "retry_delay_seconds": 60,
}


# ============================================================================
# Scan Job Scheduling
# ============================================================================


async def schedule_compliance_scan(
    project_id: UUID,
    triggered_by: Optional[UUID] = None,
    trigger_type: TriggerType = TriggerType.MANUAL,
    priority: str = "normal",
    include_doc_code_sync: bool = True,
) -> dict[str, Any]:
    """
    Schedule a compliance scan job for background execution.

    This function creates a job in the database to be processed asynchronously,
    allowing the API to return immediately while scan runs in background.
    Jobs are persisted and survive server restarts.

    Args:
        project_id: UUID of project to scan
        triggered_by: UUID of user who triggered scan
        trigger_type: How the scan was triggered
        priority: Job priority ("high", "normal", "low")
        include_doc_code_sync: Whether to check doc-code drift

    Returns:
        Job info with job_id and status

    Example:
        job = await schedule_compliance_scan(
            project_id=project.id,
            triggered_by=current_user.id,
            priority="high"
        )
        print(f"Scan job {job['job_id']} queued")
    """
    async with AsyncSessionLocal() as db:
        # Create job in database
        job = ScanJob(
            project_id=project_id,
            triggered_by=triggered_by,
            trigger_type=trigger_type.value,
            priority=priority,
            include_doc_code_sync=include_doc_code_sync,
            status=ScanJobStatus.QUEUED.value,
            queued_at=datetime.utcnow(),
        )
        db.add(job)
        await db.commit()
        await db.refresh(job)

        logger.info(
            f"Compliance scan job {job.id} queued for project {project_id} "
            f"(priority={priority}, trigger={trigger_type.value})"
        )

        return {
            "job_id": str(job.id),
            "status": job.status,
            "message": f"Compliance scan job queued for project {project_id}",
            "queued_at": job.queued_at.isoformat(),
        }


async def get_scan_job_status(job_id: str) -> Optional[dict[str, Any]]:
    """
    Get status of a scan job from database.

    Args:
        job_id: UUID of the job

    Returns:
        Job status dict or None if not found
    """
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(ScanJob).where(ScanJob.id == UUID(job_id))
        )
        job = result.scalar_one_or_none()

        if not job:
            return None

        return {
            "job_id": str(job.id),
            "project_id": str(job.project_id),
            "triggered_by": str(job.triggered_by) if job.triggered_by else None,
            "trigger_type": job.trigger_type,
            "priority": job.priority,
            "include_doc_code_sync": job.include_doc_code_sync,
            "status": job.status,
            "queued_at": job.queued_at.isoformat() if job.queued_at else None,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "result": job.result,
            "error": job.error,
            "retry_count": job.retry_count,
        }


# ============================================================================
# Scan Job Processing
# ============================================================================


async def run_compliance_scan_job(job_id: UUID) -> dict[str, Any]:
    """
    Execute a single compliance scan job from database.

    Features:
    - Timeout handling (5 minutes per job)
    - Automatic retry on failure (up to max_retries)
    - Job state persistence to database
    - Race condition protection via database transactions

    Args:
        job_id: UUID of the job to execute

    Returns:
        Updated job status dict

    Raises:
        asyncio.TimeoutError: If scan exceeds timeout limit
    """
    logger.info(f"Starting compliance scan job {job_id}")
    timeout_seconds = SCAN_CONFIG["scan_timeout_seconds"]

    async with AsyncSessionLocal() as db:
        # Get job from database with FOR UPDATE lock to prevent race conditions
        result = await db.execute(
            select(ScanJob)
            .where(ScanJob.id == job_id)
            .with_for_update(skip_locked=True)
        )
        job = result.scalar_one_or_none()

        if not job:
            logger.error(f"Job {job_id} not found")
            return {"error": "Job not found"}

        if job.status != ScanJobStatus.QUEUED.value:
            logger.warning(f"Job {job_id} is not in queued state: {job.status}")
            return {"error": f"Job not in queued state: {job.status}"}

        # Update job to running
        job.status = ScanJobStatus.RUNNING.value
        job.started_at = datetime.utcnow()
        await db.commit()

        try:
            # Create scanner and run scan with timeout
            scanner = ComplianceScanner(db)

            # Wrap scan in timeout
            scan_result = await asyncio.wait_for(
                scanner.scan_project(
                    project_id=job.project_id,
                    triggered_by=job.triggered_by,
                    trigger_type=TriggerType(job.trigger_type),
                    include_doc_code_sync=job.include_doc_code_sync,
                ),
                timeout=timeout_seconds,
            )

            # Update job with results
            job.status = ScanJobStatus.COMPLETED.value
            job.completed_at = datetime.utcnow()
            job.result = {
                "compliance_score": scan_result.compliance_score,
                "violations_count": scan_result.violations_count,
                "warnings_count": scan_result.warnings_count,
                "is_compliant": scan_result.is_compliant,
                "duration_ms": scan_result.duration_ms,
            }
            await db.commit()

            logger.info(
                f"Compliance scan job {job_id} completed: "
                f"score={scan_result.compliance_score}, "
                f"violations={scan_result.violations_count}"
            )

            # Trigger notification if violations found
            if scan_result.violations_count > 0:
                await _trigger_violation_notification(
                    project_id=job.project_id,
                    scan_result=scan_result,
                    db=db,
                )

            return {
                "job_id": str(job.id),
                "status": job.status,
                "result": job.result,
            }

        except asyncio.TimeoutError:
            error_msg = f"Scan timed out after {timeout_seconds} seconds"
            logger.error(f"Compliance scan job {job_id} failed: {error_msg}")
            job.status = ScanJobStatus.FAILED.value
            job.completed_at = datetime.utcnow()
            job.error = error_msg
            job.retry_count += 1
            await db.commit()

            # Check if should retry
            if job.can_retry:
                logger.info(f"Job {job_id} will be retried ({job.retry_count}/{job.max_retries})")
                await _schedule_job_retry(job_id, job.retry_count)

            return {
                "job_id": str(job.id),
                "status": job.status,
                "error": error_msg,
                "will_retry": job.can_retry,
            }

        except Exception as e:
            logger.error(f"Compliance scan job {job_id} failed: {e}")
            job.status = ScanJobStatus.FAILED.value
            job.completed_at = datetime.utcnow()
            job.error = str(e)
            job.retry_count += 1
            await db.commit()

            # Check if should retry
            if job.can_retry:
                logger.info(f"Job {job_id} will be retried ({job.retry_count}/{job.max_retries})")
                await _schedule_job_retry(job_id, job.retry_count)

            return {
                "job_id": str(job.id),
                "status": job.status,
                "error": str(e),
                "will_retry": job.can_retry,
            }


async def _schedule_job_retry(job_id: UUID, retry_count: int) -> None:
    """
    Schedule a job for retry after delay.

    Uses exponential backoff: 60s, 120s, 240s for retries 1, 2, 3.

    Args:
        job_id: UUID of the job to retry
        retry_count: Current retry count
    """
    base_delay = SCAN_CONFIG["retry_delay_seconds"]
    delay_seconds = base_delay * (2 ** (retry_count - 1))  # Exponential backoff

    logger.info(f"Scheduling retry for job {job_id} in {delay_seconds} seconds")

    # Reset job to queued state after delay
    await asyncio.sleep(delay_seconds)

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(ScanJob).where(ScanJob.id == job_id)
        )
        job = result.scalar_one_or_none()

        if job and job.status == ScanJobStatus.FAILED.value:
            job.status = ScanJobStatus.QUEUED.value
            job.queued_at = datetime.utcnow()
            job.error = None
            await db.commit()
            logger.info(f"Job {job_id} re-queued for retry attempt {retry_count + 1}")


async def process_scan_queue(max_jobs: int = 10) -> list[dict[str, Any]]:
    """
    Process pending scan jobs from database queue.

    Args:
        max_jobs: Maximum number of jobs to process

    Returns:
        List of processed job results
    """
    results = []

    async with AsyncSessionLocal() as db:
        # Get queued jobs, ordered by priority (high first) and queued_at
        query = (
            select(ScanJob)
            .where(ScanJob.status == ScanJobStatus.QUEUED.value)
            .order_by(
                # High priority first using SQLAlchemy case()
                case(
                    (ScanJob.priority == "high", 1),
                    (ScanJob.priority == "normal", 2),
                    else_=3,
                ),
                ScanJob.queued_at.asc(),
            )
            .limit(max_jobs)
        )
        result = await db.execute(query)
        jobs = result.scalars().all()

        for job in jobs:
            job_result = await run_compliance_scan_job(job.id)
            results.append(job_result)

    logger.info(f"Processed {len(results)} compliance scan jobs")
    return results


# ============================================================================
# Daily Scheduled Scan
# ============================================================================


async def run_daily_compliance_scan() -> dict[str, Any]:
    """
    Run daily compliance scan for all active projects.

    This job runs at 2:00 AM daily and scans all active projects
    that haven't been scanned in the last 24 hours.

    Returns:
        Summary of daily scan run
    """
    logger.info("Starting daily compliance scan for all active projects")

    start_time = datetime.utcnow()
    projects_scanned = 0
    projects_skipped = 0
    total_violations = 0
    errors = []

    try:
        async with AsyncSessionLocal() as db:
            # Get all active projects
            result = await db.execute(
                select(Project).where(
                    Project.is_active == True,
                    Project.deleted_at.is_(None),
                )
            )
            projects = result.scalars().all()

            logger.info(f"Found {len(projects)} active projects to scan")

            for project in projects:
                try:
                    # Check if already scanned in last 24 hours
                    last_scan_result = await db.execute(
                        select(ComplianceScan)
                        .where(
                            ComplianceScan.project_id == project.id,
                            ComplianceScan.scanned_at > datetime.utcnow() - timedelta(hours=24),
                        )
                        .limit(1)
                    )
                    last_scan = last_scan_result.scalar_one_or_none()

                    if last_scan:
                        logger.debug(
                            f"Skipping project {project.id}: scanned within 24h"
                        )
                        projects_skipped += 1
                        continue

                    # Run scan
                    scanner = ComplianceScanner(db)
                    scan_result = await scanner.scan_project(
                        project_id=project.id,
                        triggered_by=None,
                        trigger_type=TriggerType.SCHEDULED,
                        include_doc_code_sync=False,  # Faster for scheduled scans
                    )

                    projects_scanned += 1
                    total_violations += scan_result.violations_count

                    # Trigger notification if violations found
                    if scan_result.violations_count > 0:
                        await _trigger_violation_notification(
                            project_id=project.id,
                            scan_result=scan_result,
                            db=db,
                        )

                    logger.info(
                        f"Scanned project {project.id}: "
                        f"score={scan_result.compliance_score}, "
                        f"violations={scan_result.violations_count}"
                    )

                except Exception as e:
                    logger.error(f"Error scanning project {project.id}: {e}")
                    errors.append({
                        "project_id": str(project.id),
                        "error": str(e),
                    })

    except Exception as e:
        logger.error(f"Daily compliance scan failed: {e}")
        return {
            "status": "failed",
            "error": str(e),
            "started_at": start_time.isoformat(),
            "completed_at": datetime.utcnow().isoformat(),
        }

    duration_seconds = (datetime.utcnow() - start_time).total_seconds()

    summary = {
        "status": "completed",
        "started_at": start_time.isoformat(),
        "completed_at": datetime.utcnow().isoformat(),
        "duration_seconds": int(duration_seconds),
        "projects_scanned": projects_scanned,
        "projects_skipped": projects_skipped,
        "total_violations": total_violations,
        "errors": errors,
    }

    logger.info(
        f"Daily compliance scan completed: "
        f"scanned={projects_scanned}, skipped={projects_skipped}, "
        f"violations={total_violations}, duration={duration_seconds:.1f}s"
    )

    return summary


# ============================================================================
# Notification Triggers
# ============================================================================


async def _trigger_violation_notification(
    project_id: UUID,
    scan_result: Any,
    db: AsyncSession,
) -> None:
    """
    Trigger notification for compliance violations.

    Args:
        project_id: UUID of the project
        scan_result: ComplianceScanResult with violations
        db: Database session
    """
    from app.models.user import User
    from app.models.project_member import ProjectMember
    from app.services.notification_service import create_notification_service

    # Get project details
    project_result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = project_result.scalar_one_or_none()

    if not project:
        logger.warning(f"Project {project_id} not found for notification")
        return

    # Count critical/high violations
    critical_high_violations = [
        v for v in scan_result.violations
        if v.severity in ("critical", "high")
    ]
    critical_count = len(critical_high_violations)

    if critical_count > 0:
        logger.info(
            f"Triggering notification for project {project.name}: "
            f"{critical_count} critical/high violations"
        )

        # Get project members to notify (owners and admins)
        members_result = await db.execute(
            select(User)
            .join(ProjectMember, ProjectMember.user_id == User.id)
            .where(
                ProjectMember.project_id == project_id,
                ProjectMember.role.in_(["owner", "admin", "manager"]),
                User.is_active == True,
            )
        )
        recipients = members_result.scalars().all()

        if not recipients:
            logger.warning(f"No recipients found for project {project.name}")
            return

        # Create notification service and send alerts
        notification_service = create_notification_service(db)
        await notification_service.send_violation_alert(
            project=project,
            violations=scan_result.violations,
            compliance_score=scan_result.compliance_score,
            recipients=list(recipients),
        )

        logger.info(
            f"Sent violation notifications to {len(recipients)} recipients "
            f"for project {project.name}"
        )


# ============================================================================
# APScheduler Job Registration
# ============================================================================


def register_scheduled_jobs(scheduler: Any) -> None:
    """
    Register compliance scan jobs with APScheduler.

    Registered Jobs:
    1. Daily compliance scan (2:00 AM)
    2. Process scan queue (every 5 minutes)
    3. Recover stuck jobs (every 15 minutes)
    4. Clear old completed jobs (daily at 3:00 AM)

    Args:
        scheduler: APScheduler instance

    Usage:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler

        scheduler = AsyncIOScheduler()
        register_scheduled_jobs(scheduler)
        scheduler.start()
    """
    from apscheduler.triggers.cron import CronTrigger

    # Daily compliance scan at 2:00 AM
    scheduler.add_job(
        run_daily_compliance_scan,
        CronTrigger(
            hour=SCAN_CONFIG["daily_scan_hour"],
            minute=SCAN_CONFIG["daily_scan_minute"],
        ),
        id="daily_compliance_scan",
        name="Daily Compliance Scan",
        replace_existing=True,
    )

    # Process scan queue every 5 minutes
    scheduler.add_job(
        process_scan_queue,
        "interval",
        minutes=5,
        id="process_scan_queue",
        name="Process Compliance Scan Queue",
        replace_existing=True,
    )

    # Recover stuck jobs every 15 minutes
    scheduler.add_job(
        recover_stuck_jobs,
        "interval",
        minutes=15,
        id="recover_stuck_jobs",
        name="Recover Stuck Jobs",
        replace_existing=True,
    )

    # Clear old completed jobs daily at 3:00 AM
    scheduler.add_job(
        clear_completed_jobs,
        CronTrigger(hour=3, minute=0),
        id="clear_completed_jobs",
        name="Clear Old Completed Jobs",
        replace_existing=True,
    )

    logger.info("Registered compliance scan scheduled jobs (4 jobs)")


# ============================================================================
# Utility Functions
# ============================================================================


async def get_queue_status() -> dict[str, Any]:
    """
    Get current status of the scan queue from database.

    Returns:
        Queue status including pending, running, and completed counts
    """
    async with AsyncSessionLocal() as db:
        # Count jobs by status
        counts = {}
        for status in ScanJobStatus:
            result = await db.execute(
                select(func.count(ScanJob.id)).where(
                    ScanJob.status == status.value
                )
            )
            counts[status.value] = result.scalar() or 0

        # Get total jobs
        total_result = await db.execute(select(func.count(ScanJob.id)))
        total = total_result.scalar() or 0

        return {
            "pending": counts.get(ScanJobStatus.QUEUED.value, 0),
            "running": counts.get(ScanJobStatus.RUNNING.value, 0),
            "completed": counts.get(ScanJobStatus.COMPLETED.value, 0),
            "failed": counts.get(ScanJobStatus.FAILED.value, 0),
            "cancelled": counts.get(ScanJobStatus.CANCELLED.value, 0),
            "total_jobs": total,
        }


async def clear_completed_jobs(older_than_hours: int = 24) -> int:
    """
    Clear completed jobs older than specified hours.

    Args:
        older_than_hours: Clear jobs older than this many hours

    Returns:
        Number of jobs cleared
    """
    cutoff = datetime.utcnow() - timedelta(hours=older_than_hours)

    async with AsyncSessionLocal() as db:
        # Delete old completed/failed jobs
        result = await db.execute(
            select(ScanJob).where(
                ScanJob.status.in_([
                    ScanJobStatus.COMPLETED.value,
                    ScanJobStatus.FAILED.value,
                    ScanJobStatus.CANCELLED.value,
                ]),
                ScanJob.completed_at < cutoff,
            )
        )
        old_jobs = result.scalars().all()

        count = len(old_jobs)
        for job in old_jobs:
            await db.delete(job)

        await db.commit()

    logger.info(f"Cleared {count} old compliance scan jobs")
    return count


async def recover_stuck_jobs(stuck_threshold_minutes: int = 10) -> int:
    """
    Recover jobs that are stuck in RUNNING state.

    Jobs that have been running longer than the threshold are considered stuck
    and will be reset to QUEUED state for retry.

    Args:
        stuck_threshold_minutes: Jobs running longer than this are considered stuck

    Returns:
        Number of jobs recovered
    """
    cutoff = datetime.utcnow() - timedelta(minutes=stuck_threshold_minutes)

    async with AsyncSessionLocal() as db:
        # Find stuck jobs
        result = await db.execute(
            select(ScanJob).where(
                ScanJob.status == ScanJobStatus.RUNNING.value,
                ScanJob.started_at < cutoff,
            )
        )
        stuck_jobs = result.scalars().all()

        count = 0
        for job in stuck_jobs:
            # Check if can retry
            if job.retry_count < job.max_retries:
                job.status = ScanJobStatus.QUEUED.value
                job.queued_at = datetime.utcnow()
                job.started_at = None
                job.retry_count += 1
                job.error = f"Job stuck in running state, recovered after {stuck_threshold_minutes} minutes"
                count += 1
                logger.info(f"Recovered stuck job {job.id} (retry {job.retry_count}/{job.max_retries})")
            else:
                # Max retries exceeded, mark as failed
                job.status = ScanJobStatus.FAILED.value
                job.completed_at = datetime.utcnow()
                job.error = f"Job stuck in running state, max retries ({job.max_retries}) exceeded"
                logger.warning(f"Job {job.id} failed after max retries")

        await db.commit()

    if count > 0:
        logger.info(f"Recovered {count} stuck compliance scan jobs")
    return count


async def cancel_job(job_id: UUID) -> dict[str, Any]:
    """
    Cancel a queued or running job.

    Args:
        job_id: UUID of the job to cancel

    Returns:
        Updated job status
    """
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(ScanJob).where(ScanJob.id == job_id)
        )
        job = result.scalar_one_or_none()

        if not job:
            return {"error": "Job not found"}

        if job.status in (
            ScanJobStatus.COMPLETED.value,
            ScanJobStatus.FAILED.value,
            ScanJobStatus.CANCELLED.value,
        ):
            return {"error": f"Cannot cancel job in {job.status} state"}

        job.status = ScanJobStatus.CANCELLED.value
        job.completed_at = datetime.utcnow()
        job.error = "Job cancelled by user"
        await db.commit()

        logger.info(f"Cancelled job {job_id}")

        return {
            "job_id": str(job.id),
            "status": job.status,
            "message": "Job cancelled successfully",
        }
