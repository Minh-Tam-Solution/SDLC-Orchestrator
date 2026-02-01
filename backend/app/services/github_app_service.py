"""
GitHub App Service - Sprint 129 (Day 4 Enhanced)

Business logic for GitHub App authentication, repository management, and cloning.

Key Features:
- JWT generation for GitHub App authentication (10-min expiry)
- Installation token retrieval with auto-refresh (1-hour TTL)
- Token caching (refresh 5min before expiry)
- Installation and repository listing
- Shallow clone for gap analysis
- Multi-tenant isolation via installation_id
- Retry with exponential backoff (Sprint 129 Day 4)
- Rate limit handling (5000 requests/hour)
- User-friendly error messages

Security:
- Tokens NOT stored in database (generated on-demand)
- Installation tokens cached in memory only
- Clone uses installation token (not user credentials)
- Webhook signature validation (HMAC-SHA256)

Reference: ADR-044-GitHub-Integration-Strategy.md
"""

import hashlib
import hmac
import logging
import subprocess
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from uuid import UUID

import httpx
import jwt
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.github_integration import (
    GitHubInstallation,
    GitHubRepository,
    InstallationStatus,
    CloneStatus,
)
from app.models.project import Project
from app.services.github_errors import (
    GitHubAPIError,
    GitHubAuthError,
    GitHubAccessDeniedError,
    GitHubNotFoundError,
    GitHubRateLimitError,
    GitHubNetworkError,
    GitHubTimeoutError,
    GitHubCloneError,
    GitHubErrorCode,
    retry_with_backoff,
    update_rate_limit,
    check_rate_limit,
    parse_github_error_response,
)

logger = logging.getLogger(__name__)


# ============================================================================
# GitHub API Constants
# ============================================================================

GITHUB_API_BASE_URL = "https://api.github.com"
GITHUB_API_VERSION = "2022-11-28"


# ============================================================================
# Token Cache (In-Memory)
# ============================================================================

# Cache format: {installation_id: (token, expires_at)}
_token_cache: Dict[int, Tuple[str, datetime]] = {}


# ============================================================================
# JWT Generation
# ============================================================================

def generate_github_app_jwt() -> str:
    """
    Generate JWT for GitHub App authentication.

    The JWT is used to authenticate as the GitHub App itself,
    which is then exchanged for an installation access token.

    Returns:
        JWT token string (valid for 10 minutes)

    Raises:
        HTTPException(500): If GitHub App is not configured
        HTTPException(500): If private key is invalid

    Example:
        >>> jwt_token = generate_github_app_jwt()
        >>> # Use jwt_token to request installation access token
    """
    if not settings.GITHUB_APP_ID or not settings.GITHUB_APP_PRIVATE_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "github_app_not_configured",
                "message": "GitHub App credentials not configured. Set GITHUB_APP_ID and GITHUB_APP_PRIVATE_KEY."
            }
        )

    now = int(time.time())

    payload = {
        "iat": now,
        "exp": now + 600,  # 10 minutes
        "iss": settings.GITHUB_APP_ID
    }

    try:
        # Handle base64-encoded or raw PEM key
        private_key = settings.GITHUB_APP_PRIVATE_KEY
        if not private_key.startswith("-----BEGIN"):
            import base64
            private_key = base64.b64decode(private_key).decode("utf-8")

        token = jwt.encode(payload, private_key, algorithm="RS256")
        return token
    except Exception as e:
        logger.error(f"Failed to generate GitHub App JWT: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "jwt_generation_failed",
                "message": "Failed to generate GitHub App JWT. Check private key configuration."
            }
        )


# ============================================================================
# Installation Token Management
# ============================================================================

async def get_installation_token(installation_id: int, retry: bool = True) -> str:
    """
    Get installation access token with auto-refresh and retry logic.

    Tokens are cached and automatically refreshed 5 minutes before expiry.
    GitHub installation tokens have a 1-hour TTL.

    Args:
        installation_id: GitHub App installation ID
        retry: Whether to retry on transient failures (default: True)

    Returns:
        Installation access token string

    Raises:
        GitHubNotFoundError: If installation not found
        GitHubAuthError: If authentication fails
        GitHubRateLimitError: If rate limit exceeded
        GitHubNetworkError: If network error occurs

    Example:
        >>> token = await get_installation_token(12345678)
        >>> # Use token to make GitHub API requests
    """
    global _token_cache

    # Check cache
    if installation_id in _token_cache:
        token, expires_at = _token_cache[installation_id]

        # Refresh if expiring in <5 minutes
        if datetime.utcnow() < expires_at - timedelta(minutes=5):
            logger.debug(f"Using cached token for installation {installation_id}")
            return token
        else:
            logger.info(f"Token expiring soon for installation {installation_id}, refreshing...")

    async def _fetch_token() -> str:
        """Internal function for token fetch with retry support."""
        jwt_token = generate_github_app_jwt()

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{GITHUB_API_BASE_URL}/app/installations/{installation_id}/access_tokens",
                    headers={
                        "Authorization": f"Bearer {jwt_token}",
                        "Accept": "application/vnd.github+json",
                        "X-GitHub-Api-Version": GITHUB_API_VERSION
                    },
                    timeout=30.0
                )

                # Update rate limit info
                update_rate_limit(f"installation_{installation_id}", dict(response.headers))

                # Handle error responses
                if response.status_code == 404:
                    raise GitHubNotFoundError(
                        message=f"GitHub App installation {installation_id} not found. "
                                "Please install the SDLC Orchestrator GitHub App.",
                        code=GitHubErrorCode.INSTALLATION_NOT_FOUND
                    )

                if response.status_code == 401:
                    raise GitHubAuthError(
                        message="GitHub App authentication failed. Check credentials.",
                        code=GitHubErrorCode.AUTH_FAILED
                    )

                if response.status_code == 403:
                    raise GitHubAccessDeniedError(
                        message="GitHub App access denied. The installation may be suspended.",
                        code=GitHubErrorCode.INSTALLATION_SUSPENDED
                    )

                if response.status_code == 429:
                    # Parse rate limit info from response
                    data = response.json()
                    raise GitHubRateLimitError(
                        message=data.get("message", "Rate limit exceeded"),
                        retry_after=int(response.headers.get("retry-after", 60))
                    )

                response.raise_for_status()

                data = response.json()
                token = data["token"]
                expires_at = datetime.fromisoformat(data["expires_at"].replace("Z", "+00:00"))

                # Cache token
                _token_cache[installation_id] = (token, expires_at)

                logger.info(f"Refreshed token for installation {installation_id}, expires at {expires_at}")

                return token

        except httpx.TimeoutException as e:
            logger.error(f"Timeout getting installation token: {e}")
            raise GitHubTimeoutError(
                message="GitHub API request timed out",
                operation="get_installation_token"
            )
        except httpx.RequestError as e:
            logger.error(f"Network error getting installation token: {e}")
            raise GitHubNetworkError(
                message="Failed to connect to GitHub API. Check network connection.",
                original_error=e
            )
        except (GitHubAPIError, HTTPException):
            raise
        except httpx.HTTPStatusError as e:
            logger.error(f"GitHub API error for installation {installation_id}: {e}")
            error = parse_github_error_response(
                e.response.status_code,
                e.response.json() if e.response.content else {}
            )
            raise error

    # Execute with or without retry
    if retry:
        return await retry_with_backoff(
            _fetch_token,
            max_retries=3,
            base_delay=1.0,
            max_delay=30.0,
            retryable_exceptions=(GitHubNetworkError, GitHubTimeoutError, GitHubRateLimitError)
        )
    else:
        return await _fetch_token()


# ============================================================================
# Installation Management
# ============================================================================

async def list_installations_from_github() -> List[Dict[str, Any]]:
    """
    List all GitHub App installations.

    Requires GitHub App JWT authentication.

    Returns:
        List of installation dictionaries from GitHub API

    Raises:
        HTTPException(502): If GitHub API fails
    """
    jwt_token = generate_github_app_jwt()

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{GITHUB_API_BASE_URL}/app/installations",
                headers={
                    "Authorization": f"Bearer {jwt_token}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": GITHUB_API_VERSION
                },
                timeout=30.0
            )

            response.raise_for_status()
            return response.json()

    except httpx.HTTPStatusError as e:
        logger.error(f"Failed to list installations: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "error": "github_api_error",
                "message": f"Failed to list GitHub App installations: {e.response.status_code}"
            }
        )


async def list_repositories_for_installation(
    installation_id: int,
    page: int = 1,
    per_page: int = 100,
    retry: bool = True
) -> Dict[str, Any]:
    """
    List repositories accessible to a GitHub App installation.

    Args:
        installation_id: GitHub App installation ID
        page: Page number (default: 1)
        per_page: Results per page (default: 100, max: 100)
        retry: Whether to retry on transient failures (default: True)

    Returns:
        Dictionary with 'total_count' and 'repositories' list

    Raises:
        GitHubAuthError: If installation token is invalid
        GitHubRateLimitError: If rate limit exceeded
        GitHubNetworkError: If network error occurs
    """
    async def _list_repos() -> Dict[str, Any]:
        token = await get_installation_token(installation_id)

        try:
            # Check rate limit before making request
            check_rate_limit(f"repos_{installation_id}")

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{GITHUB_API_BASE_URL}/installation/repositories",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Accept": "application/vnd.github+json",
                        "X-GitHub-Api-Version": GITHUB_API_VERSION
                    },
                    params={"page": page, "per_page": min(per_page, 100)},
                    timeout=30.0
                )

                # Update rate limit info
                update_rate_limit(f"repos_{installation_id}", dict(response.headers))

                if response.status_code == 401:
                    # Token may have been revoked, clear cache
                    _token_cache.pop(installation_id, None)
                    raise GitHubAuthError(
                        message="Installation access token is invalid or revoked. Please reconnect.",
                        code=GitHubErrorCode.TOKEN_INVALID
                    )

                if response.status_code == 403:
                    raise GitHubAccessDeniedError(
                        message="Access denied. The GitHub App may need additional permissions."
                    )

                if response.status_code == 429:
                    data = response.json()
                    raise GitHubRateLimitError(
                        message=data.get("message", "Rate limit exceeded"),
                        retry_after=int(response.headers.get("retry-after", 60))
                    )

                response.raise_for_status()
                return response.json()

        except httpx.TimeoutException as e:
            logger.error(f"Timeout listing repositories: {e}")
            raise GitHubTimeoutError(
                message="Request timed out while listing repositories",
                operation="list_repositories"
            )
        except httpx.RequestError as e:
            logger.error(f"Network error listing repositories for installation {installation_id}: {e}")
            raise GitHubNetworkError(
                message="Failed to connect to GitHub API",
                original_error=e
            )
        except (GitHubAPIError, HTTPException):
            raise
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to list repositories for installation {installation_id}: {e}")
            error = parse_github_error_response(
                e.response.status_code,
                e.response.json() if e.response.content else {}
            )
            raise error

    if retry:
        return await retry_with_backoff(
            _list_repos,
            max_retries=3,
            base_delay=1.0,
            max_delay=30.0,
            retryable_exceptions=(GitHubNetworkError, GitHubTimeoutError, GitHubRateLimitError)
        )
    else:
        return await _list_repos()


async def get_repository_info(
    installation_id: int,
    owner: str,
    repo: str,
    retry: bool = True
) -> Dict[str, Any]:
    """
    Get detailed information about a repository.

    Args:
        installation_id: GitHub App installation ID
        owner: Repository owner (user or org)
        repo: Repository name
        retry: Whether to retry on transient failures (default: True)

    Returns:
        Repository information dictionary

    Raises:
        GitHubNotFoundError: If repository not found
        GitHubAccessDeniedError: If no access to repository
        GitHubRateLimitError: If rate limit exceeded
    """
    async def _get_repo() -> Dict[str, Any]:
        token = await get_installation_token(installation_id)

        try:
            check_rate_limit(f"repo_{owner}_{repo}")

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{GITHUB_API_BASE_URL}/repos/{owner}/{repo}",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Accept": "application/vnd.github+json",
                        "X-GitHub-Api-Version": GITHUB_API_VERSION
                    },
                    timeout=30.0
                )

                update_rate_limit(f"repo_{owner}_{repo}", dict(response.headers))

                if response.status_code == 404:
                    raise GitHubNotFoundError(
                        message=f"Repository {owner}/{repo} not found or not accessible. "
                                "Verify the repository exists and the GitHub App is installed.",
                        code=GitHubErrorCode.REPO_NOT_FOUND,
                        resource=f"{owner}/{repo}"
                    )

                if response.status_code == 403:
                    raise GitHubAccessDeniedError(
                        message=f"No access to repository {owner}/{repo}. "
                                "Please grant the GitHub App access to this repository.",
                        code=GitHubErrorCode.REPO_ACCESS_DENIED,
                        resource=f"{owner}/{repo}"
                    )

                if response.status_code == 429:
                    data = response.json()
                    raise GitHubRateLimitError(
                        message=data.get("message", "Rate limit exceeded"),
                        retry_after=int(response.headers.get("retry-after", 60))
                    )

                response.raise_for_status()
                return response.json()

        except httpx.TimeoutException as e:
            logger.error(f"Timeout getting repository info: {e}")
            raise GitHubTimeoutError(
                message=f"Request timed out while getting {owner}/{repo} info",
                operation="get_repository_info"
            )
        except httpx.RequestError as e:
            logger.error(f"Network error getting repository {owner}/{repo}: {e}")
            raise GitHubNetworkError(
                message="Failed to connect to GitHub API",
                original_error=e
            )
        except (GitHubAPIError, HTTPException):
            raise
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to get repository {owner}/{repo}: {e}")
            error = parse_github_error_response(
                e.response.status_code,
                e.response.json() if e.response.content else {}
            )
            raise error

    if retry:
        return await retry_with_backoff(
            _get_repo,
            max_retries=3,
            base_delay=1.0,
            max_delay=30.0,
            retryable_exceptions=(GitHubNetworkError, GitHubTimeoutError, GitHubRateLimitError)
        )
    else:
        return await _get_repo()


# ============================================================================
# Clone Management
# ============================================================================

async def clone_repository(
    installation_id: int,
    owner: str,
    repo: str,
    target_dir: Path,
    shallow: bool = True,
    timeout_seconds: int = 300,
    max_retries: int = 2
) -> Path:
    """
    Clone a GitHub repository using installation token with retry support.

    Uses shallow clone (--depth=1) by default to minimize bandwidth.

    Args:
        installation_id: GitHub App installation ID
        owner: Repository owner
        repo: Repository name
        target_dir: Target directory for clone
        shallow: Use shallow clone (default: True)
        timeout_seconds: Clone timeout in seconds (default: 300 = 5 minutes)
        max_retries: Number of retry attempts (default: 2)

    Returns:
        Path to cloned repository

    Raises:
        GitHubCloneError: If clone fails
        GitHubTimeoutError: If clone times out
        GitHubAuthError: If authentication fails
    """
    import shutil

    last_error = None

    for attempt in range(max_retries + 1):
        try:
            token = await get_installation_token(installation_id)

            # Build clone URL with installation token
            clone_url = f"https://x-access-token:{token}@github.com/{owner}/{repo}.git"

            # Build git command
            cmd = ["git", "clone"]
            if shallow:
                cmd.extend(["--depth=1", "--single-branch", "--no-tags"])
            cmd.extend([clone_url, str(target_dir)])

            # Create parent directory if needed
            target_dir.parent.mkdir(parents=True, exist_ok=True)

            # Clean up any failed previous attempt
            if target_dir.exists():
                shutil.rmtree(target_dir)

            # Run git clone
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                timeout=timeout_seconds,
                text=True
            )

            logger.info(f"Successfully cloned {owner}/{repo} to {target_dir}")
            return target_dir

        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.strip() if e.stderr else "Unknown error"
            # Clean up token from error message
            error_msg = error_msg.replace(token, "[TOKEN]")

            logger.error(f"Clone attempt {attempt + 1} failed for {owner}/{repo}: {error_msg}")

            # Check for specific error types
            if "Authentication failed" in error_msg or "could not read Username" in error_msg:
                # Clear token cache and retry with fresh token
                _token_cache.pop(installation_id, None)
                last_error = GitHubAuthError(
                    message="Git authentication failed. Token may have expired.",
                    code=GitHubErrorCode.TOKEN_EXPIRED
                )
            elif "Repository not found" in error_msg:
                raise GitHubNotFoundError(
                    message=f"Repository {owner}/{repo} not found or no access.",
                    code=GitHubErrorCode.REPO_NOT_FOUND,
                    resource=f"{owner}/{repo}"
                )
            elif "Permission denied" in error_msg or "access denied" in error_msg.lower():
                raise GitHubAccessDeniedError(
                    message=f"Permission denied for repository {owner}/{repo}.",
                    code=GitHubErrorCode.REPO_ACCESS_DENIED,
                    resource=f"{owner}/{repo}"
                )
            else:
                last_error = GitHubCloneError(
                    message=f"Failed to clone repository: {error_msg}",
                    repo_name=f"{owner}/{repo}",
                    error_output=error_msg
                )

            # Retry if we have attempts left
            if attempt < max_retries:
                import asyncio
                delay = 2 ** attempt  # Exponential backoff: 1s, 2s
                logger.info(f"Retrying clone in {delay}s...")
                await asyncio.sleep(delay)
            else:
                raise last_error

        except subprocess.TimeoutExpired:
            logger.error(f"Clone timed out for {owner}/{repo} (attempt {attempt + 1})")

            # Clean up partial clone
            if target_dir.exists():
                shutil.rmtree(target_dir)

            last_error = GitHubTimeoutError(
                message=f"Repository clone timed out after {timeout_seconds}s. "
                        "The repository may be too large for shallow clone.",
                operation=f"clone_{owner}/{repo}"
            )

            if attempt < max_retries:
                # For timeout, try with longer timeout on retry
                timeout_seconds = int(timeout_seconds * 1.5)
                logger.info(f"Retrying with {timeout_seconds}s timeout...")
            else:
                raise last_error

    # Should not reach here
    if last_error:
        raise last_error
    raise GitHubCloneError(message="Clone failed unexpectedly")


def scan_local_repository(repo_path: Path) -> Dict[str, Any]:
    """
    Scan local repository structure for gap analysis.

    Does NOT use GitHub API - scans local filesystem directly.

    Args:
        repo_path: Path to cloned repository

    Returns:
        Dictionary with folder structure info:
        - folders: List of folder paths (relative to repo root)
        - files: List of file paths
        - total_folders: Count of folders
        - total_files: Count of files
        - sdlc_config_found: Whether .sdlc-config.json exists
        - docs_folder_exists: Whether docs/ folder exists
    """
    folders = []
    files = []

    if not repo_path.exists():
        return {
            "folders": [],
            "files": [],
            "total_folders": 0,
            "total_files": 0,
            "sdlc_config_found": False,
            "docs_folder_exists": False,
            "error": f"Path not found: {repo_path}"
        }

    for item in repo_path.rglob("*"):
        # Skip .git directory
        if ".git" in item.parts:
            continue

        relative_path = str(item.relative_to(repo_path))

        if item.is_dir():
            folders.append(relative_path)
        elif item.is_file():
            files.append(relative_path)

    return {
        "folders": sorted(folders),
        "files": sorted(files),
        "total_folders": len(folders),
        "total_files": len(files),
        "sdlc_config_found": (repo_path / ".sdlc-config.json").exists(),
        "docs_folder_exists": (repo_path / "docs").exists()
    }


# ============================================================================
# Webhook Signature Validation
# ============================================================================

def verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    """
    Verify GitHub webhook signature (HMAC-SHA256).

    Args:
        payload: Raw webhook payload bytes
        signature: X-Hub-Signature-256 header value
        secret: Webhook secret

    Returns:
        True if signature is valid, False otherwise

    Example:
        >>> payload = b'{"action": "created"}'
        >>> signature = "sha256=abc123..."
        >>> verify_webhook_signature(payload, signature, "my-secret")
        True
    """
    if not signature.startswith("sha256="):
        return False

    expected_signature = "sha256=" + hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(signature, expected_signature)


# ============================================================================
# Database Operations
# ============================================================================

def get_user_installations(user_id: UUID, db: Session) -> List[GitHubInstallation]:
    """
    Get all active GitHub installations for a user.

    Args:
        user_id: User UUID
        db: Database session

    Returns:
        List of GitHubInstallation objects
    """
    return db.query(GitHubInstallation).filter(
        GitHubInstallation.installed_by == user_id,
        GitHubInstallation.status == InstallationStatus.ACTIVE
    ).all()


def create_installation(
    installation_id: int,
    account_type: str,
    account_login: str,
    user_id: UUID,
    db: Session,
    account_avatar_url: Optional[str] = None
) -> GitHubInstallation:
    """
    Create a new GitHub installation record.

    Args:
        installation_id: GitHub's installation ID
        account_type: 'user' or 'organization'
        account_login: GitHub username or org name
        user_id: User who installed the app
        db: Database session
        account_avatar_url: Optional avatar URL

    Returns:
        Created GitHubInstallation object

    Raises:
        HTTPException(409): If installation already exists
    """
    # Check if installation already exists
    existing = db.query(GitHubInstallation).filter(
        GitHubInstallation.installation_id == installation_id
    ).first()

    if existing:
        if existing.status == InstallationStatus.UNINSTALLED:
            # Reactivate uninstalled installation
            existing.status = InstallationStatus.ACTIVE
            existing.uninstalled_at = None
            existing.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(existing)
            return existing
        else:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": "installation_exists",
                    "message": f"Installation {installation_id} already exists"
                }
            )

    installation = GitHubInstallation(
        installation_id=installation_id,
        account_type=account_type,
        account_login=account_login,
        account_avatar_url=account_avatar_url,
        installed_by=user_id
    )

    db.add(installation)
    db.commit()
    db.refresh(installation)

    logger.info(f"Created GitHub installation {installation_id} for user {user_id}")
    return installation


def link_repository_to_project(
    installation_uuid: UUID,
    project_id: UUID,
    repo_info: Dict[str, Any],
    user_id: UUID,
    db: Session
) -> GitHubRepository:
    """
    Link a GitHub repository to a project.

    Args:
        installation_uuid: Our GitHubInstallation.id (UUID)
        project_id: Project UUID
        repo_info: Repository info from GitHub API
        user_id: User who connected the repo
        db: Database session

    Returns:
        Created GitHubRepository object

    Raises:
        HTTPException(404): If project not found
        HTTPException(409): If repo already linked
    """
    # Verify project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "project_not_found",
                "message": f"Project {project_id} not found"
            }
        )

    # Check if project already has a repo linked
    existing = db.query(GitHubRepository).filter(
        GitHubRepository.project_id == project_id,
        GitHubRepository.disconnected_at.is_(None)
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "project_already_linked",
                "message": f"Project already linked to repository {existing.full_name}"
            }
        )

    # Check if repo is already linked to another project
    repo_linked = db.query(GitHubRepository).filter(
        GitHubRepository.github_repo_id == repo_info["id"],
        GitHubRepository.disconnected_at.is_(None)
    ).first()

    if repo_linked:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "repo_already_linked",
                "message": f"Repository already linked to another project"
            }
        )

    github_repo = GitHubRepository(
        installation_id=installation_uuid,
        project_id=project_id,
        github_repo_id=repo_info["id"],
        owner=repo_info["owner"]["login"],
        name=repo_info["name"],
        full_name=repo_info["full_name"],
        default_branch=repo_info.get("default_branch", "main"),
        is_private=repo_info.get("private", False),
        html_url=repo_info.get("html_url"),
        connected_by=user_id
    )

    db.add(github_repo)
    db.commit()
    db.refresh(github_repo)

    logger.info(f"Linked repo {repo_info['full_name']} to project {project_id}")
    return github_repo


def unlink_repository(project_id: UUID, user_id: UUID, db: Session) -> GitHubRepository:
    """
    Unlink a GitHub repository from a project.

    Args:
        project_id: Project UUID
        user_id: User performing the action (for audit)
        db: Database session

    Returns:
        Updated GitHubRepository object

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

    github_repo.disconnect()
    db.commit()
    db.refresh(github_repo)

    logger.info(f"Unlinked repo {github_repo.full_name} from project {project_id}")
    return github_repo


def update_clone_status(
    github_repo_id: UUID,
    status: str,
    db: Session,
    local_path: Optional[str] = None,
    error_message: Optional[str] = None
) -> GitHubRepository:
    """
    Update clone status for a GitHub repository.

    Args:
        github_repo_id: GitHubRepository UUID
        status: New clone status (pending, cloning, cloned, failed)
        db: Database session
        local_path: Path to local clone (for 'cloned' status)
        error_message: Error message (for 'failed' status)

    Returns:
        Updated GitHubRepository object
    """
    github_repo = db.query(GitHubRepository).filter(
        GitHubRepository.id == github_repo_id
    ).first()

    if not github_repo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "github_repo_not_found",
                "message": f"GitHub repository record {github_repo_id} not found"
            }
        )

    if status == CloneStatus.CLONING:
        github_repo.start_clone(local_path or "")
    elif status == CloneStatus.CLONED:
        github_repo.complete_clone()
        if local_path:
            github_repo.local_path = local_path
    elif status == CloneStatus.FAILED:
        github_repo.fail_clone(error_message or "Unknown error")
    elif status == CloneStatus.PENDING:
        github_repo.reset_clone_status()

    db.commit()
    db.refresh(github_repo)

    return github_repo


# ==============================================================================
# Class-Based Service Wrapper (Test Compatibility - Sprint 129 Day 7)
# ==============================================================================


class GitHubAppError(Exception):
    """Base exception for GitHub App errors"""
    pass


class GitHubAppNotConfiguredError(GitHubAppError):
    """Raised when GitHub App credentials are not configured"""
    pass


class GitHubAppAuthError(GitHubAppError):
    """Raised when GitHub App authentication fails"""
    pass


class GitHubAppInstallationError(GitHubAppError):
    """Raised when GitHub App installation operations fail"""
    pass


class GitHubAppService:
    """
    Class-based wrapper for GitHub App service functions.
    
    Provides backward compatibility for tests that expect a service class.
    All methods delegate to module-level functions.
    
    Usage:
        service = GitHubAppService()
        jwt_token = service.generate_jwt()
        installation_token = await service.get_installation_token(installation_id)
    """
    
    def __init__(self):
        """Initialize GitHub App Service (validates configuration)"""
        if not settings.GITHUB_APP_ID or not settings.GITHUB_APP_PRIVATE_KEY:
            raise GitHubAppNotConfiguredError(
                "GitHub App credentials not configured. Set GITHUB_APP_ID and GITHUB_APP_PRIVATE_KEY."
            )
    
    def generate_jwt(self) -> str:
        """Generate JWT for GitHub App authentication"""
        return generate_jwt()
    
    async def get_installation_token(
        self,
        installation_id: int,
        force_refresh: bool = False
    ) -> str:
        """Get installation token (with caching)"""
        return await get_installation_token(installation_id, force_refresh)
    
    async def list_installations(self, user_access_token: str) -> List[Dict[str, Any]]:
        """List all GitHub App installations for authenticated user"""
        return await list_installations(user_access_token)
    
    async def list_installation_repositories(
        self,
        installation_id: int
    ) -> List[Dict[str, Any]]:
        """List repositories for a specific installation"""
        return await list_installation_repositories(installation_id)
    
    async def clone_repository(
        self,
        full_name: str,
        installation_id: int,
        local_path: str
    ) -> Tuple[bool, Optional[str]]:
        """Clone repository using installation token"""
        return await clone_repository(full_name, installation_id, local_path)
    
    async def scan_repository_structure(
        self,
        local_path: str
    ) -> Dict[str, Any]:
        """Scan local repository structure"""
        return await scan_repository_structure(local_path)
    
    def link_repository_to_project(
        self,
        project_id: UUID,
        github_repo_id: UUID,
        db: Session
    ) -> GitHubRepository:
        """Link GitHub repository to project"""
        return link_repository_to_project(project_id, github_repo_id, db)
    
    def unlink_repository_from_project(
        self,
        project_id: UUID,
        db: Session
    ) -> GitHubRepository:
        """Unlink GitHub repository from project"""
        return unlink_repository_from_project(project_id, db)


# ==============================================================================
# Service Factory Function (Dependency Injection - Sprint 129 Day 7)
# ==============================================================================


def get_github_app_service() -> GitHubAppService:
    """
    Factory function for GitHubAppService (dependency injection).
    
    Returns:
        Initialized GitHubAppService instance
        
    Raises:
        GitHubAppNotConfiguredError: If GitHub App credentials missing
    """
    return GitHubAppService()
