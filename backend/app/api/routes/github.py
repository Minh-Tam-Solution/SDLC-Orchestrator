"""
GitHub Integration API Endpoints - Sprint 129

RESTful API for GitHub App integration with clone-local strategy.

Key Features:
- List user's GitHub App installations
- List repositories for an installation
- Link/unlink repositories to projects
- Trigger repository clone
- Webhook handling (installation events)

Security:
- All endpoints require authentication (except webhooks)
- Webhook signature validation (HMAC-SHA256)
- Installation tokens not stored (generated on-demand)
- Multi-tenant isolation via installation_id

Reference: ADR-044-GitHub-Integration-Strategy.md
API Spec: docs/01-planning/05-API-Design/API-Specification.md
"""
import logging
from pathlib import Path
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.core.config import settings
from app.models.user import User
from app.models.github_integration import (
    GitHubInstallation,
    GitHubRepository,
    CloneStatus,
)
from app.schemas.github import (
    GitHubLinkRequest,
    GitHubCloneRequest,
    GitHubInstallationResponse,
    GitHubInstallationsListResponse,
    GitHubRepoInfo,
    GitHubRepositoriesListResponse,
    GitHubRepositoryResponse,
    GitHubLinkResponse,
    GitHubCloneStatusResponse,
    GitHubScanResult,
)
from app.services import github_app_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/github", tags=["github"])


# ============================================================================
# Installation Endpoints (Authenticated)
# ============================================================================

@router.get(
    "/installations",
    response_model=GitHubInstallationsListResponse,
    summary="List user's GitHub installations",
    description="""
    List all active GitHub App installations for the current user.

    Returns installations where the user installed the GitHub App.
    Each installation provides access to repositories in that user/org.

    **Note**: To get repositories for an installation, use
    GET /github/installations/{installation_id}/repositories
    """,
)
async def list_installations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> GitHubInstallationsListResponse:
    """
    List user's GitHub App installations.

    Args:
        current_user: Authenticated user
        db: Database session

    Returns:
        List of GitHubInstallation objects
    """
    installations = github_app_service.get_user_installations(current_user.id, db)

    return GitHubInstallationsListResponse(
        installations=[
            GitHubInstallationResponse(
                id=inst.id,
                installation_id=inst.installation_id,
                account_type=inst.account_type,
                account_login=inst.account_login,
                account_avatar_url=inst.account_avatar_url,
                status=inst.status,
                installed_at=inst.installed_at,
                repositories_count=len(inst.repositories) if inst.repositories else 0
            )
            for inst in installations
        ],
        total_count=len(installations)
    )


@router.get(
    "/installations/{installation_id}/repositories",
    response_model=GitHubRepositoriesListResponse,
    summary="List repositories for installation",
    description="""
    List repositories accessible to a GitHub App installation.

    Requires the installation to be owned by the current user.
    Results are paginated (default: 100 per page, max: 100).

    **Note**: This fetches fresh data from GitHub API, not cached.
    """,
)
async def list_installation_repositories(
    installation_id: UUID,
    page: int = 1,
    per_page: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> GitHubRepositoriesListResponse:
    """
    List repositories for a GitHub installation.

    Args:
        installation_id: Our GitHubInstallation UUID
        page: Page number (default: 1)
        per_page: Results per page (default: 100)
        current_user: Authenticated user
        db: Database session

    Returns:
        List of repository info from GitHub API

    Raises:
        HTTPException(403): If user doesn't own the installation
        HTTPException(404): If installation not found
    """
    # Get installation from database
    installation = db.query(GitHubInstallation).filter(
        GitHubInstallation.id == installation_id
    ).first()

    if not installation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "installation_not_found",
                "message": f"Installation {installation_id} not found"
            }
        )

    # Check ownership
    if installation.installed_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "not_installation_owner",
                "message": "You do not own this GitHub installation"
            }
        )

    # Fetch repositories from GitHub API
    data = await github_app_service.list_repositories_for_installation(
        installation.installation_id,  # GitHub's installation ID
        page=page,
        per_page=per_page
    )

    repositories = [
        GitHubRepoInfo(
            id=repo["id"],
            name=repo["name"],
            full_name=repo["full_name"],
            owner=repo["owner"]["login"],
            description=repo.get("description"),
            private=repo.get("private", False),
            default_branch=repo.get("default_branch", "main"),
            html_url=repo["html_url"],
            clone_url=repo.get("clone_url"),
            size=repo.get("size"),
            language=repo.get("language"),
            updated_at=repo.get("updated_at")
        )
        for repo in data.get("repositories", [])
    ]

    total_count = data.get("total_count", len(repositories))
    has_more = page * per_page < total_count

    return GitHubRepositoriesListResponse(
        repositories=repositories,
        total_count=total_count,
        page=page,
        per_page=per_page,
        has_more=has_more
    )


# ============================================================================
# Project-Repository Linking Endpoints
# ============================================================================

@router.post(
    "/projects/{project_id}/link",
    response_model=GitHubLinkResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Link GitHub repository to project",
    description="""
    Link a GitHub repository to an SDLC Orchestrator project.

    **Rules**:
    - One project can only be linked to one repository
    - One repository can only be linked to one project
    - User must own the installation

    **After linking**:
    - Use POST /projects/{project_id}/clone to clone the repository
    - Use GET /projects/{project_id}/scan to scan the cloned repository
    """,
)
async def link_repository(
    project_id: UUID,
    data: GitHubLinkRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> GitHubLinkResponse:
    """
    Link a GitHub repository to a project.

    Args:
        project_id: Project UUID
        data: Link request with installation_id, owner, repo
        current_user: Authenticated user
        db: Database session

    Returns:
        GitHubLinkResponse with linked repository info

    Raises:
        HTTPException(404): If project or installation not found
        HTTPException(403): If user doesn't own installation
        HTTPException(409): If project or repo already linked
    """
    # Verify installation ownership
    installation = db.query(GitHubInstallation).filter(
        GitHubInstallation.id == data.installation_id
    ).first()

    if not installation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "installation_not_found",
                "message": f"Installation {data.installation_id} not found"
            }
        )

    if installation.installed_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "not_installation_owner",
                "message": "You do not own this GitHub installation"
            }
        )

    # Get repository info from GitHub
    repo_info = await github_app_service.get_repository_info(
        installation.installation_id,
        data.owner,
        data.repo
    )

    # Link repository to project
    github_repo = github_app_service.link_repository_to_project(
        installation_uuid=installation.id,
        project_id=project_id,
        repo_info=repo_info,
        user_id=current_user.id,
        db=db
    )

    return GitHubLinkResponse(
        message=f"Successfully linked {data.owner}/{data.repo} to project",
        repository=GitHubRepositoryResponse(
            id=github_repo.id,
            installation_id=github_repo.installation_id,
            project_id=github_repo.project_id,
            github_repo_id=github_repo.github_repo_id,
            owner=github_repo.owner,
            name=github_repo.name,
            full_name=github_repo.full_name,
            default_branch=github_repo.default_branch,
            is_private=github_repo.is_private,
            html_url=github_repo.html_url,
            local_path=github_repo.local_path,
            last_cloned_at=github_repo.last_cloned_at,
            clone_status=github_repo.clone_status,
            clone_error=github_repo.clone_error,
            connected_at=github_repo.connected_at,
            connected_by=github_repo.connected_by
        )
    )


@router.delete(
    "/projects/{project_id}/unlink",
    response_model=GitHubLinkResponse,
    summary="Unlink GitHub repository from project",
    description="""
    Unlink a GitHub repository from a project.

    This does NOT delete the repository from GitHub.
    The local clone is also preserved (can be deleted manually).
    """,
)
async def unlink_repository(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> GitHubLinkResponse:
    """
    Unlink a GitHub repository from a project.

    Args:
        project_id: Project UUID
        current_user: Authenticated user
        db: Database session

    Returns:
        GitHubLinkResponse with unlinked repository info

    Raises:
        HTTPException(404): If no repository linked
    """
    github_repo = github_app_service.unlink_repository(
        project_id=project_id,
        user_id=current_user.id,
        db=db
    )

    return GitHubLinkResponse(
        message=f"Successfully unlinked {github_repo.full_name} from project",
        repository=GitHubRepositoryResponse(
            id=github_repo.id,
            installation_id=github_repo.installation_id,
            project_id=github_repo.project_id,
            github_repo_id=github_repo.github_repo_id,
            owner=github_repo.owner,
            name=github_repo.name,
            full_name=github_repo.full_name,
            default_branch=github_repo.default_branch,
            is_private=github_repo.is_private,
            html_url=github_repo.html_url,
            local_path=github_repo.local_path,
            last_cloned_at=github_repo.last_cloned_at,
            clone_status=github_repo.clone_status,
            clone_error=github_repo.clone_error,
            connected_at=github_repo.connected_at,
            connected_by=github_repo.connected_by
        )
    )


@router.get(
    "/projects/{project_id}/repository",
    response_model=GitHubRepositoryResponse,
    summary="Get linked repository for project",
    description="Get the GitHub repository linked to a project.",
)
async def get_project_repository(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> GitHubRepositoryResponse:
    """
    Get the GitHub repository linked to a project.

    Args:
        project_id: Project UUID
        current_user: Authenticated user
        db: Database session

    Returns:
        GitHubRepositoryResponse

    Raises:
        HTTPException(404): If no repository linked
    """
    github_repo = db.query(GitHubRepository).filter(
        GitHubRepository.project_id == project_id,
        GitHubRepository.disconnected_at.is_(None)
    ).first()

    if not github_repo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "no_repo_linked",
                "message": f"No repository linked to project {project_id}"
            }
        )

    return GitHubRepositoryResponse(
        id=github_repo.id,
        installation_id=github_repo.installation_id,
        project_id=github_repo.project_id,
        github_repo_id=github_repo.github_repo_id,
        owner=github_repo.owner,
        name=github_repo.name,
        full_name=github_repo.full_name,
        default_branch=github_repo.default_branch,
        is_private=github_repo.is_private,
        html_url=github_repo.html_url,
        local_path=github_repo.local_path,
        last_cloned_at=github_repo.last_cloned_at,
        clone_status=github_repo.clone_status,
        clone_error=github_repo.clone_error,
        connected_at=github_repo.connected_at,
        connected_by=github_repo.connected_by
    )


# ============================================================================
# Clone & Scan Endpoints
# ============================================================================

@router.post(
    "/projects/{project_id}/clone",
    response_model=GitHubCloneStatusResponse,
    summary="Clone linked repository",
    description="""
    Clone the linked GitHub repository to local storage.

    Uses shallow clone (--depth=1) by default for faster cloning.
    After clone, use GET /projects/{project_id}/scan for gap analysis.

    **Clone Status Flow**:
    pending → cloning → cloned (or failed)
    """,
)
async def clone_repository(
    project_id: UUID,
    data: GitHubCloneRequest = GitHubCloneRequest(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> GitHubCloneStatusResponse:
    """
    Clone the linked GitHub repository.

    Args:
        project_id: Project UUID
        data: Clone options (shallow, force)
        current_user: Authenticated user
        db: Database session

    Returns:
        GitHubCloneStatusResponse with clone status

    Raises:
        HTTPException(404): If no repository linked
        HTTPException(409): If already cloned (unless force=True)
    """
    # Get linked repository
    github_repo = db.query(GitHubRepository).filter(
        GitHubRepository.project_id == project_id,
        GitHubRepository.disconnected_at.is_(None)
    ).first()

    if not github_repo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "no_repo_linked",
                "message": f"No repository linked to project {project_id}"
            }
        )

    # Check if already cloned
    if github_repo.clone_status == CloneStatus.CLONED and not data.force:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "already_cloned",
                "message": "Repository already cloned. Use force=true to re-clone."
            }
        )

    # Get installation
    installation = github_repo.installation
    if not installation:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "installation_not_found",
                "message": "GitHub installation not found for repository"
            }
        )

    # Define target directory
    target_dir = Path(f"/var/sdlc/repos/{project_id}")

    # Update status to cloning
    github_repo.start_clone(str(target_dir))
    db.commit()

    try:
        # Clone repository
        await github_app_service.clone_repository(
            installation_id=installation.installation_id,
            owner=github_repo.owner,
            repo=github_repo.name,
            target_dir=target_dir,
            shallow=data.shallow
        )

        # Update status to cloned
        github_repo.complete_clone()
        github_repo.local_path = str(target_dir)
        db.commit()

        return GitHubCloneStatusResponse(
            message=f"Successfully cloned {github_repo.full_name}",
            clone_status=github_repo.clone_status,
            local_path=github_repo.local_path,
            last_cloned_at=github_repo.last_cloned_at
        )

    except HTTPException as e:
        # Update status to failed
        github_repo.fail_clone(str(e.detail.get("message", "Unknown error")))
        db.commit()
        raise


@router.get(
    "/projects/{project_id}/scan",
    response_model=GitHubScanResult,
    summary="Scan cloned repository",
    description="""
    Scan the cloned repository structure for gap analysis.

    Returns folder/file structure to determine SDLC compliance.
    Repository must be cloned first (clone_status = 'cloned').
    """,
)
async def scan_repository(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> GitHubScanResult:
    """
    Scan the cloned repository structure.

    Args:
        project_id: Project UUID
        current_user: Authenticated user
        db: Database session

    Returns:
        GitHubScanResult with folder/file structure

    Raises:
        HTTPException(404): If no repository linked
        HTTPException(400): If repository not cloned
    """
    # Get linked repository
    github_repo = db.query(GitHubRepository).filter(
        GitHubRepository.project_id == project_id,
        GitHubRepository.disconnected_at.is_(None)
    ).first()

    if not github_repo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "no_repo_linked",
                "message": f"No repository linked to project {project_id}"
            }
        )

    if github_repo.clone_status != CloneStatus.CLONED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "not_cloned",
                "message": f"Repository not cloned. Current status: {github_repo.clone_status}"
            }
        )

    if not github_repo.local_path:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "local_path_missing",
                "message": "Repository local path not set"
            }
        )

    # Scan local repository
    result = github_app_service.scan_local_repository(Path(github_repo.local_path))

    return GitHubScanResult(**result)


# ============================================================================
# Webhook Endpoints (Unauthenticated, Signature Verified)
# ============================================================================

@router.post(
    "/webhooks",
    summary="GitHub webhook handler",
    description="""
    Handle GitHub webhook events (Sprint 129.5).

    **Supported Events**:
    - installation: App install/uninstall/suspend/unsuspend
    - push: Code pushed → triggers gap analysis
    - pull_request: PR opened/sync/closed → triggers gate evaluation
    - ping: Webhook configuration test

    **Security**:
    - Webhook signature validation (HMAC-SHA256)
    - X-Hub-Signature-256 header required
    - Idempotency via X-GitHub-Delivery header

    **Processing**:
    - Webhook returns 202 Accepted immediately
    - Actual processing happens in background job
    - Use X-GitHub-Delivery to track status
    """,
    status_code=status.HTTP_202_ACCEPTED,
)
async def handle_webhook(
    request: Request,
    x_github_event: Optional[str] = Header(None, alias="X-GitHub-Event"),
    x_hub_signature_256: Optional[str] = Header(None, alias="X-Hub-Signature-256"),
    x_github_delivery: Optional[str] = Header(None, alias="X-GitHub-Delivery"),
    db: Session = Depends(get_db),
):
    """
    Handle GitHub webhook events (Sprint 129.5 implementation).

    Args:
        request: FastAPI request
        x_github_event: GitHub event type header
        x_hub_signature_256: Webhook signature header
        x_github_delivery: Unique delivery ID (for idempotency)
        db: Database session

    Returns:
        Status response with delivery_id

    Raises:
        HTTPException(401): If signature invalid or missing
        HTTPException(500): If webhook not configured
    """
    from app.services.github_webhook_service import (
        verify_webhook_signature,
        process_webhook,
    )

    # Get webhook secret
    webhook_secret = settings.GITHUB_APP_WEBHOOK_SECRET
    if not webhook_secret:
        logger.warning("GitHub webhook secret not configured")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "webhook_not_configured", "message": "GITHUB_APP_WEBHOOK_SECRET not set"}
        )

    # Get raw payload
    payload_bytes = await request.body()

    # Verify signature (required)
    if not x_hub_signature_256:
        logger.warning(f"Webhook missing signature header (delivery: {x_github_delivery})")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "signature_missing", "message": "X-Hub-Signature-256 header required"}
        )

    if not verify_webhook_signature(payload_bytes, x_hub_signature_256, webhook_secret):
        logger.warning(f"Webhook signature invalid (delivery: {x_github_delivery})")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "signature_invalid", "message": "Webhook signature verification failed"}
        )

    # Parse payload
    data = await request.json()

    # Generate delivery ID if not provided (for testing)
    delivery_id = x_github_delivery or f"local_{hash(payload_bytes) % 10**10}"

    # Process webhook (with idempotency check)
    result = await process_webhook(
        event_type=x_github_event or "unknown",
        delivery_id=delivery_id,
        payload=data,
        db_session=db
    )

    # Add delivery_id to response for tracking
    result["delivery_id"] = delivery_id

    return result


# Installation event handling moved to github_webhook_service.py (Sprint 129.5)


# ============================================================================
# Webhook Admin Endpoints (Authenticated, Admin Only)
# ============================================================================

@router.get(
    "/webhooks/stats",
    summary="Get webhook job queue statistics",
    description="""
    Get statistics about webhook job queues.

    **Statistics Include**:
    - Queue length (pending jobs)
    - Dead letter queue (DLQ) length
    - Jobs by status (queued, processing, completed, failed)
    - Total jobs tracked

    **Access**: Requires admin authentication
    """,
)
async def get_webhook_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get webhook job queue statistics.

    Args:
        current_user: Authenticated user (must be admin)
        db: Database session

    Returns:
        Queue statistics

    Raises:
        HTTPException(403): If user is not admin
    """
    from app.jobs.webhook_processor import get_queue_stats

    # Check admin access
    if not current_user.is_admin and not current_user.role in ("owner", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    stats = get_queue_stats()
    return {
        "status": "ok",
        "stats": stats
    }


@router.get(
    "/webhooks/dlq",
    summary="Get dead letter queue jobs",
    description="""
    Get jobs in the dead letter queue (failed after max retries).

    **Dead Letter Queue (DLQ)**:
    - Contains jobs that failed after 3 retry attempts
    - Jobs can be manually retried via POST /webhooks/dlq/{job_id}/retry
    - Monitor DLQ size for potential issues

    **Access**: Requires admin authentication
    """,
)
async def get_dlq_jobs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get dead letter queue jobs.

    Args:
        current_user: Authenticated user (must be admin)
        db: Database session

    Returns:
        List of failed jobs

    Raises:
        HTTPException(403): If user is not admin
    """
    from app.jobs.webhook_processor import get_dead_letter_jobs

    # Check admin access
    if not current_user.is_admin and not current_user.role in ("owner", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    jobs = get_dead_letter_jobs()
    return {
        "status": "ok",
        "dlq_size": len(jobs),
        "jobs": jobs
    }


@router.post(
    "/webhooks/dlq/{job_id}/retry",
    summary="Retry a dead letter queue job",
    description="""
    Retry a job from the dead letter queue.

    **Retry Behavior**:
    - Moves job from DLQ back to main queue
    - Resets retry count to 0
    - Job will be processed with next batch

    **Access**: Requires admin authentication
    """,
)
async def retry_dlq_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retry a dead letter queue job.

    Args:
        job_id: Job ID to retry
        current_user: Authenticated user (must be admin)
        db: Database session

    Returns:
        Retry result

    Raises:
        HTTPException(403): If user is not admin
        HTTPException(404): If job not found in DLQ
    """
    from app.jobs.webhook_processor import retry_dead_letter_job

    # Check admin access
    if not current_user.is_admin and not current_user.role in ("owner", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    success = retry_dead_letter_job(job_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "job_not_found", "message": f"Job {job_id} not found in DLQ"}
        )

    return {
        "status": "ok",
        "message": f"Job {job_id} re-queued for processing",
        "job_id": job_id
    }


@router.post(
    "/webhooks/process",
    summary="Trigger webhook job processing",
    description="""
    Manually trigger processing of queued webhook jobs.

    **Processing Behavior**:
    - Processes up to `max_jobs` queued webhooks
    - Returns processing summary
    - Should be called by scheduler or admin

    **Access**: Requires admin authentication
    """,
)
async def trigger_webhook_processing(
    max_jobs: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Manually trigger webhook job processing.

    Args:
        max_jobs: Maximum jobs to process (default: 10)
        current_user: Authenticated user (must be admin)
        db: Database session

    Returns:
        Processing summary

    Raises:
        HTTPException(403): If user is not admin
    """
    from app.jobs.webhook_processor import process_webhook_jobs

    # Check admin access
    if not current_user.is_admin and not current_user.role in ("owner", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    summary = await process_webhook_jobs(max_jobs=max_jobs)

    return {
        "status": "ok",
        "summary": summary
    }


@router.get(
    "/webhooks/jobs/{job_id}",
    summary="Get webhook job status",
    description="""
    Get status of a specific webhook job.

    **Job Status**:
    - queued: Waiting to be processed
    - processing: Currently being processed
    - completed: Successfully processed
    - retrying: Failed, queued for retry
    - failed: Failed after max retries (in DLQ)

    **Access**: Requires authentication
    """,
)
async def get_webhook_job_status(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get webhook job status.

    Args:
        job_id: Job ID (from webhook delivery_id)
        current_user: Authenticated user
        db: Database session

    Returns:
        Job status or 404

    Raises:
        HTTPException(404): If job not found
    """
    from app.jobs.webhook_processor import get_job_status

    job = get_job_status(job_id)

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "job_not_found", "message": f"Job {job_id} not found"}
        )

    return {
        "status": "ok",
        "job": job
    }
