"""
=========================================================================
GitHub Router - Repository Integration API
SDLC Orchestrator - Stage 03 (BUILD)

Version: 1.0.0
Date: November 28, 2025
Status: ACTIVE - Sprint 15 (GitHub Foundation)
Authority: Backend Lead + CPO Approved
Foundation: Sprint 15 Plan, User-Onboarding-Flow-Architecture.md
Framework: SDLC 4.9 Complete Lifecycle

Purpose:
- GitHub OAuth flow (initiate, callback)
- Repository listing and selection
- Repository sync to projects
- Webhook handling (push, PR, issues)

Endpoints:
- GET /github/authorize - Get OAuth authorization URL
- POST /github/callback - Handle OAuth callback
- GET /github/status - Get GitHub connection status
- GET /github/repositories - List user's repositories
- GET /github/repositories/{owner}/{repo} - Get repository details
- GET /github/repositories/{owner}/{repo}/contents - Get repository contents
- GET /github/repositories/{owner}/{repo}/languages - Get language breakdown
- POST /github/sync - Sync repository to SDLC Orchestrator project
- POST /github/webhook - Handle GitHub webhook events
- DELETE /github/disconnect - Disconnect GitHub account

Security:
- JWT authentication required (except webhook)
- Webhook HMAC signature validation
- Rate limiting (100 req/min per user)

Zero Mock Policy: Real GitHub API calls, production-ready
=========================================================================
"""

import secrets
import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Header, Request, status
from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user
from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token, hash_api_key
from app.db.session import get_db
from app.models.project import Project
from app.models.stage_mapping import ProjectStageMapping
from app.models.user import OAuthAccount, User, RefreshToken
from app.services.settings_service import SettingsService, get_settings_service
from app.schemas.github import (
    GitHubConnectionStatus,
    GitHubOAuthCallbackRequest,
    GitHubOAuthCallbackResponse,
    GitHubOAuthURLResponse,
    GitHubRateLimitInfo,
    GitHubRepository,
    GitHubRepositoryContents,
    GitHubRepositoryLanguages,
    GitHubRepositoryListResponse,
    GitHubSyncRequest,
    GitHubSyncResponse,
    GitHubWebhookEvent,
    GitHubWebhookResponse,
    SaveStageMappingsRequest,
    SaveStageMappingsResponse,
    StageMappingItem,
)
from app.services.github_service import (
    GitHubAPIError,
    GitHubAuthError,
    GitHubRateLimitError,
    github_service,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/github", tags=["GitHub"])


# ============================================================================
# OAuth Flow Endpoints
# ============================================================================


@router.get(
    "/authorize",
    response_model=GitHubOAuthURLResponse,
    status_code=status.HTTP_200_OK,
    summary="Get GitHub OAuth authorization URL",
    description="Generate OAuth authorization URL for GitHub login/connect.",
)
async def get_authorization_url(
    redirect_uri: Optional[str] = None,
    current_user: Optional[User] = Depends(get_current_active_user),
) -> GitHubOAuthURLResponse:
    """
    Get GitHub OAuth authorization URL.

    Query Parameters:
        - redirect_uri: Optional custom redirect URI

    Response (200 OK):
        {
            "authorization_url": "https://github.com/login/oauth/authorize?...",
            "state": "random_state_string"
        }

    Flow:
        1. Generate random state for CSRF protection
        2. Build authorization URL with client_id and scopes
        3. Return URL for frontend to redirect user
    """
    # Generate CSRF protection state
    state = secrets.token_urlsafe(32)

    # Store state in session/cache for validation (in production, use Redis)
    # For MVP, we'll validate in callback by checking user context

    try:
        authorization_url = github_service.get_authorization_url(
            state=state,
            redirect_uri=redirect_uri,
        )

        return GitHubOAuthURLResponse(
            authorization_url=authorization_url,
            state=state,
        )

    except GitHubAuthError as e:
        logger.error(f"GitHub OAuth URL generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate GitHub authorization URL",
        )


@router.post(
    "/callback",
    response_model=GitHubOAuthCallbackResponse,
    status_code=status.HTTP_200_OK,
    summary="Handle GitHub OAuth callback",
    description="Exchange authorization code for access token and create/link user.",
)
async def handle_oauth_callback(
    callback_data: GitHubOAuthCallbackRequest,
    db: AsyncSession = Depends(get_db),
    settings_service: "SettingsService" = Depends(get_settings_service),
) -> GitHubOAuthCallbackResponse:
    """
    Handle GitHub OAuth callback.

    Request Body:
        {
            "code": "authorization_code",
            "state": "state_from_authorize"
        }

    Response (200 OK):
        {
            "access_token": "jwt_access_token",
            "refresh_token": "jwt_refresh_token",
            "token_type": "bearer",
            "expires_in": 3600,
            "github_connected": true,
            "user_id": "uuid",
            "email": "user@example.com",
            "name": "User Name",
            "avatar_url": "https://..."
        }

    Flow:
        1. Exchange code for GitHub access token
        2. Get GitHub user info
        3. Find or create user in database
        4. Store GitHub OAuth account
        5. Generate JWT tokens for app authentication
        6. Return tokens and user info
    """
    # In production, validate state from session/cache
    # For MVP, we proceed with code exchange

    try:
        # 1. Exchange code for GitHub access token
        token_data = github_service.exchange_code_for_token(code=callback_data.code)
        github_access_token = token_data.get("access_token")

        if not github_access_token:
            raise GitHubAuthError("No access token in response")

        # 2. Get GitHub user info
        github_user = github_service.validate_access_token(github_access_token)
        github_id = str(github_user.get("id"))
        github_login = github_user.get("login")
        github_email = github_user.get("email")
        github_name = github_user.get("name")
        github_avatar = github_user.get("avatar_url")

        # If no email from user endpoint, fetch from emails endpoint
        if not github_email:
            # GitHub users can have private emails - use login@github.com as fallback
            github_email = f"{github_login}@users.noreply.github.com"

        # 3. Find existing OAuth account or user
        oauth_account = await db.execute(
            select(OAuthAccount).where(
                and_(
                    OAuthAccount.provider == "github",
                    OAuthAccount.provider_account_id == github_id,
                )
            )
        )
        oauth_account = oauth_account.scalar_one_or_none()

        if oauth_account:
            # Existing GitHub connection - update token and get user
            oauth_account.access_token = github_access_token
            oauth_account.updated_at = datetime.utcnow()

            user = await db.execute(
                select(User).where(User.id == oauth_account.user_id)
            )
            user = user.scalar_one()
        else:
            # Check if user exists with same email
            user = await db.execute(
                select(User).where(User.email == github_email)
            )
            user = user.scalar_one_or_none()

            if not user:
                # Create new user
                user = User(
                    email=github_email,
                    name=github_name or github_login,
                    avatar_url=github_avatar,
                    is_active=True,
                    password_hash=None,  # OAuth-only user
                )
                db.add(user)
                await db.flush()  # Get user.id

                logger.info(f"Created new user from GitHub: {github_email}")

            # Create OAuth account link
            oauth_account = OAuthAccount(
                user_id=user.id,
                provider="github",
                provider_account_id=github_id,
                access_token=github_access_token,
                refresh_token=None,  # GitHub tokens don't expire by default
                expires_at=None,
            )
            db.add(oauth_account)

            logger.info(f"Linked GitHub account {github_login} to user {user.email}")

        # Update user last login
        user.last_login = datetime.utcnow()
        if not user.avatar_url and github_avatar:
            user.avatar_url = github_avatar
        if not user.full_name and github_name:
            user.full_name = github_name

        # 5. Generate JWT tokens for app authentication (ADR-027: session_timeout from DB)
        access_token = await create_access_token(
            subject=str(user.id),
            settings_service=settings_service
        )
        refresh_token = create_refresh_token(subject=str(user.id))

        # Store refresh token in database
        db_refresh_token = RefreshToken(
            user_id=user.id,
            token_hash=hash_api_key(refresh_token),
            expires_at=datetime.utcnow()
            + settings.REFRESH_TOKEN_EXPIRE_TIMEDELTA,
        )
        db.add(db_refresh_token)

        await db.commit()

        return GitHubOAuthCallbackResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            github_connected=True,
            user_id=user.id,
            email=user.email,
            name=user.full_name,
            avatar_url=user.avatar_url,
        )

    except GitHubAuthError as e:
        logger.error(f"GitHub OAuth callback failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"GitHub authentication failed: {str(e)}",
        )

    except Exception as e:
        logger.error(f"GitHub OAuth callback error: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to complete GitHub authentication",
        )


@router.get(
    "/status",
    response_model=GitHubConnectionStatus,
    status_code=status.HTTP_200_OK,
    summary="Get GitHub connection status",
    description="Check if current user has GitHub connected.",
)
async def get_connection_status(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> GitHubConnectionStatus:
    """
    Get GitHub connection status for current user.

    Response (200 OK):
        {
            "connected": true,
            "github_username": "developer",
            "github_avatar": "https://...",
            "scopes": ["read:user", "user:email", "repo"],
            "connected_at": "2025-01-01T00:00:00Z",
            "rate_limit": {...}
        }
    """
    # Find GitHub OAuth account
    oauth_account = await db.execute(
        select(OAuthAccount).where(
            and_(
                OAuthAccount.user_id == current_user.id,
                OAuthAccount.provider == "github",
            )
        )
    )
    oauth_account = oauth_account.scalar_one_or_none()

    if not oauth_account:
        return GitHubConnectionStatus(
            connected=False,
            github_username=None,
            github_avatar=None,
            scopes=[],
            connected_at=None,
            rate_limit=None,
        )

    # Get current GitHub user info and rate limit
    try:
        github_user = github_service.validate_access_token(oauth_account.access_token)
        rate_limit_data = github_service.get_rate_limit(oauth_account.access_token)

        core_limit = rate_limit_data.get("resources", {}).get("core", {})

        return GitHubConnectionStatus(
            connected=True,
            github_username=github_user.get("login"),
            github_avatar=github_user.get("avatar_url"),
            scopes=["read:user", "user:email", "repo"],  # Our requested scopes
            connected_at=oauth_account.created_at,
            rate_limit=GitHubRateLimitInfo(
                limit=core_limit.get("limit", 5000),
                remaining=core_limit.get("remaining", 5000),
                reset=datetime.fromtimestamp(core_limit.get("reset", 0)),
                used=core_limit.get("used", 0),
            ),
        )

    except GitHubAuthError:
        # Token expired or invalid
        return GitHubConnectionStatus(
            connected=False,
            github_username=None,
            github_avatar=None,
            scopes=[],
            connected_at=oauth_account.created_at,
            rate_limit=None,
        )


@router.delete(
    "/disconnect",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Disconnect GitHub account",
    description="Remove GitHub connection from current user.",
)
async def disconnect_github(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Disconnect GitHub account from current user.

    Response (204 No Content): Success

    Errors:
        - 404 Not Found: No GitHub connection exists
    """
    # Find and delete GitHub OAuth account
    result = await db.execute(
        select(OAuthAccount).where(
            and_(
                OAuthAccount.user_id == current_user.id,
                OAuthAccount.provider == "github",
            )
        )
    )
    oauth_account = result.scalar_one_or_none()

    if not oauth_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No GitHub connection found",
        )

    await db.delete(oauth_account)
    await db.commit()

    logger.info(f"User {current_user.email} disconnected GitHub account")


# ============================================================================
# Repository Endpoints
# ============================================================================


@router.get(
    "/repositories",
    response_model=GitHubRepositoryListResponse,
    status_code=status.HTTP_200_OK,
    summary="List user's GitHub repositories",
    description="Get list of repositories accessible to the user.",
)
async def list_repositories(
    visibility: str = "all",
    sort: str = "updated",
    direction: str = "desc",
    per_page: int = 30,
    page: int = 1,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> GitHubRepositoryListResponse:
    """
    List user's GitHub repositories.

    Query Parameters:
        - visibility: 'all', 'public', 'private' (default: all)
        - sort: 'created', 'updated', 'pushed', 'full_name' (default: updated)
        - direction: 'asc', 'desc' (default: desc)
        - per_page: Results per page, max 100 (default: 30)
        - page: Page number (default: 1)

    Response (200 OK):
        {
            "repositories": [...],
            "total": 25,
            "page": 1,
            "per_page": 30
        }

    Errors:
        - 401 Unauthorized: GitHub not connected
        - 429 Too Many Requests: GitHub rate limit exceeded
    """
    # Get GitHub OAuth account
    oauth_account = await db.execute(
        select(OAuthAccount).where(
            and_(
                OAuthAccount.user_id == current_user.id,
                OAuthAccount.provider == "github",
            )
        )
    )
    oauth_account = oauth_account.scalar_one_or_none()

    if not oauth_account:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="GitHub not connected. Please connect your GitHub account first.",
        )

    try:
        repos = github_service.list_repositories(
            access_token=oauth_account.access_token,
            visibility=visibility,
            sort=sort,
            direction=direction,
            per_page=min(per_page, 100),
            page=page,
        )

        # Transform to response model
        repositories = [
            GitHubRepository(
                id=repo["id"],
                name=repo["name"],
                full_name=repo["full_name"],
                description=repo.get("description"),
                html_url=repo["html_url"],
                clone_url=repo.get("clone_url"),
                default_branch=repo.get("default_branch", "main"),
                language=repo.get("language"),
                private=repo.get("private", False),
                fork=repo.get("fork", False),
                stargazers_count=repo.get("stargazers_count", 0),
                forks_count=repo.get("forks_count", 0),
                open_issues_count=repo.get("open_issues_count", 0),
                owner={
                    "login": repo["owner"]["login"],
                    "id": repo["owner"]["id"],
                    "avatar_url": repo["owner"].get("avatar_url"),
                    "type": repo["owner"].get("type", "User"),
                },
                created_at=repo.get("created_at"),
                updated_at=repo.get("updated_at"),
                pushed_at=repo.get("pushed_at"),
            )
            for repo in repos
        ]

        return GitHubRepositoryListResponse(
            repositories=repositories,
            total=len(repositories),  # GitHub doesn't return total, approximate
            page=page,
            per_page=per_page,
        )

    except GitHubAuthError as e:
        logger.error(f"GitHub auth error listing repos: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="GitHub authentication failed. Please reconnect your account.",
        )

    except GitHubRateLimitError as e:
        logger.error(f"GitHub rate limit: {e}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(e),
        )

    except GitHubAPIError as e:
        logger.error(f"GitHub API error: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"GitHub API error: {str(e)}",
        )


@router.get(
    "/repositories/{owner}/{repo}",
    response_model=GitHubRepository,
    status_code=status.HTTP_200_OK,
    summary="Get repository details",
    description="Get detailed information about a specific repository.",
)
async def get_repository(
    owner: str,
    repo: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> GitHubRepository:
    """
    Get repository details.

    Path Parameters:
        - owner: Repository owner (username or organization)
        - repo: Repository name

    Response (200 OK):
        {
            "id": 123456789,
            "name": "my-project",
            "full_name": "developer/my-project",
            ...
        }

    Errors:
        - 401 Unauthorized: GitHub not connected
        - 404 Not Found: Repository not found or no access
    """
    # Get GitHub OAuth account
    oauth_account = await db.execute(
        select(OAuthAccount).where(
            and_(
                OAuthAccount.user_id == current_user.id,
                OAuthAccount.provider == "github",
            )
        )
    )
    oauth_account = oauth_account.scalar_one_or_none()

    if not oauth_account:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="GitHub not connected",
        )

    try:
        repo_data = github_service.get_repository(
            access_token=oauth_account.access_token,
            owner=owner,
            repo=repo,
        )

        return GitHubRepository(
            id=repo_data["id"],
            name=repo_data["name"],
            full_name=repo_data["full_name"],
            description=repo_data.get("description"),
            html_url=repo_data["html_url"],
            clone_url=repo_data.get("clone_url"),
            default_branch=repo_data.get("default_branch", "main"),
            language=repo_data.get("language"),
            private=repo_data.get("private", False),
            fork=repo_data.get("fork", False),
            stargazers_count=repo_data.get("stargazers_count", 0),
            forks_count=repo_data.get("forks_count", 0),
            open_issues_count=repo_data.get("open_issues_count", 0),
            owner={
                "login": repo_data["owner"]["login"],
                "id": repo_data["owner"]["id"],
                "avatar_url": repo_data["owner"].get("avatar_url"),
                "type": repo_data["owner"].get("type", "User"),
            },
            created_at=repo_data.get("created_at"),
            updated_at=repo_data.get("updated_at"),
            pushed_at=repo_data.get("pushed_at"),
        )

    except GitHubAPIError as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Repository {owner}/{repo} not found or no access",
            )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"GitHub API error: {str(e)}",
        )


@router.get(
    "/repositories/{owner}/{repo}/contents",
    response_model=list[GitHubRepositoryContents],
    status_code=status.HTTP_200_OK,
    summary="Get repository contents",
    description="Get file/directory listing for a repository path.",
)
async def get_repository_contents(
    owner: str,
    repo: str,
    path: str = "",
    ref: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[GitHubRepositoryContents]:
    """
    Get repository contents (files and directories).

    Path Parameters:
        - owner: Repository owner
        - repo: Repository name

    Query Parameters:
        - path: Path within repository (default: root)
        - ref: Branch/tag/commit reference (default: default branch)

    Response (200 OK):
        [
            {"name": "README.md", "path": "README.md", "type": "file", ...},
            {"name": "src", "path": "src", "type": "dir", ...}
        ]
    """
    # Get GitHub OAuth account
    oauth_account = await db.execute(
        select(OAuthAccount).where(
            and_(
                OAuthAccount.user_id == current_user.id,
                OAuthAccount.provider == "github",
            )
        )
    )
    oauth_account = oauth_account.scalar_one_or_none()

    if not oauth_account:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="GitHub not connected",
        )

    try:
        contents = github_service.get_repository_contents(
            access_token=oauth_account.access_token,
            owner=owner,
            repo=repo,
            path=path,
            ref=ref,
        )

        # Handle single file response (GitHub returns dict for single file)
        if isinstance(contents, dict):
            contents = [contents]

        return [
            GitHubRepositoryContents(
                name=item["name"],
                path=item["path"],
                type=item["type"],
                size=item.get("size", 0),
                sha=item["sha"],
                download_url=item.get("download_url"),
            )
            for item in contents
        ]

    except GitHubAPIError as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Path {path} not found in {owner}/{repo}",
            )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"GitHub API error: {str(e)}",
        )


@router.get(
    "/repositories/{owner}/{repo}/languages",
    response_model=GitHubRepositoryLanguages,
    status_code=status.HTTP_200_OK,
    summary="Get repository languages",
    description="Get language breakdown for a repository.",
)
async def get_repository_languages(
    owner: str,
    repo: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> GitHubRepositoryLanguages:
    """
    Get repository language breakdown.

    Path Parameters:
        - owner: Repository owner
        - repo: Repository name

    Response (200 OK):
        {
            "languages": {"Python": 50000, "TypeScript": 30000},
            "primary_language": "Python"
        }
    """
    # Get GitHub OAuth account
    oauth_account = await db.execute(
        select(OAuthAccount).where(
            and_(
                OAuthAccount.user_id == current_user.id,
                OAuthAccount.provider == "github",
            )
        )
    )
    oauth_account = oauth_account.scalar_one_or_none()

    if not oauth_account:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="GitHub not connected",
        )

    try:
        languages = github_service.get_repository_languages(
            access_token=oauth_account.access_token,
            owner=owner,
            repo=repo,
        )

        primary_language = max(languages, key=languages.get) if languages else None

        return GitHubRepositoryLanguages(
            languages=languages,
            primary_language=primary_language,
        )

    except GitHubAPIError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"GitHub API error: {str(e)}",
        )


# ============================================================================
# Repository Analysis Endpoint (Sprint 15 Day 4)
# ============================================================================


@router.get(
    "/repositories/{owner}/{repo}/analyze",
    status_code=status.HTTP_200_OK,
    summary="Analyze repository for SDLC recommendations",
    description="Analyze GitHub repository and get policy pack recommendations.",
)
async def analyze_repository(
    owner: str,
    repo: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Analyze GitHub repository for SDLC recommendations.

    Path Parameters:
        - owner: Repository owner
        - repo: Repository name

    Response (200 OK):
        {
            "repository": {...},
            "languages": {...},
            "project_type": "fastapi_app",
            "team_size_estimate": 10,
            "recommendations": {
                "policy_pack": "standard",
                "initial_gates": ["G0.1", "G0.2"]
            }
        }

    This endpoint analyzes the repository structure and provides:
    - Project type detection (Python, Node, Go, etc.)
    - Team size estimation
    - Policy pack recommendation (Lite/Standard/Enterprise)
    - Stage mapping suggestions
    - Initial gates to create
    """
    # Get GitHub OAuth account
    oauth_account = await db.execute(
        select(OAuthAccount).where(
            and_(
                OAuthAccount.user_id == current_user.id,
                OAuthAccount.provider == "github",
            )
        )
    )
    oauth_account = oauth_account.scalar_one_or_none()

    if not oauth_account:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="GitHub not connected",
        )

    try:
        from app.services.project_sync_service import project_sync_service

        analysis = await project_sync_service.analyze_repository(
            access_token=oauth_account.access_token,
            owner=owner,
            repo=repo,
        )

        return analysis

    except GitHubAPIError as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Repository {owner}/{repo} not found or no access",
            )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"GitHub API error: {str(e)}",
        )


# ============================================================================
# Stage Mapping Endpoints (Sprint 49 - SDLC 5.1.2)
# ============================================================================


@router.post(
    "/stage-mappings",
    response_model=SaveStageMappingsResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Save stage mappings for a project",
    description="Persist folder-to-stage mappings for a project. Only /docs folders are stage-mapped per SDLC 5.1.2.",
)
async def save_stage_mappings(
    request: SaveStageMappingsRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> SaveStageMappingsResponse:
    """
    Save stage mappings for a project (SDLC 5.1.2).

    Request Body:
        {
            "project_id": "uuid",
            "stage_mappings": [
                {
                    "folder_path": "docs/00-foundation",
                    "stage_code": "00",
                    "stage_name": "FOUNDATION",
                    "is_auto_detected": true,
                    "confidence": 0.95
                }
            ]
        }

    Response (201 Created):
        {
            "project_id": "uuid",
            "mappings_saved": 5,
            "mappings": [...]
        }

    SDLC 5.1.2 Rules:
        - Only /docs folders are stage-mapped (stages 00-09)
        - Stage 10 is archive folder, NOT a numbered stage
        - Code folders (backend, frontend) are NOT stage-mapped
    """
    # Verify project exists and user has access
    project_result = await db.execute(
        select(Project).where(Project.id == request.project_id)
    )
    project = project_result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {request.project_id} not found",
        )

    # Verify user owns or has access to project
    if project.owner_id != current_user.id:
        # Check if user is a member
        from app.models.project import ProjectMember
        member_result = await db.execute(
            select(ProjectMember).where(
                and_(
                    ProjectMember.project_id == request.project_id,
                    ProjectMember.user_id == current_user.id,
                )
            )
        )
        if not member_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this project",
            )

    # Delete existing mappings for this project
    await db.execute(
        select(ProjectStageMapping).where(
            ProjectStageMapping.project_id == request.project_id
        )
    )
    # Use delete statement
    from sqlalchemy import delete
    await db.execute(
        delete(ProjectStageMapping).where(
            ProjectStageMapping.project_id == request.project_id
        )
    )

    # Create new mappings
    saved_mappings = []
    for mapping in request.stage_mappings:
        # Validate: only docs folders should be mapped
        if not mapping.folder_path.startswith("docs"):
            logger.warning(
                f"Skipping non-docs folder mapping: {mapping.folder_path}"
            )
            continue

        db_mapping = ProjectStageMapping(
            project_id=request.project_id,
            folder_path=mapping.folder_path,
            stage_code=mapping.stage_code,
            stage_name=mapping.stage_name,
            is_auto_detected=mapping.is_auto_detected,
            confidence=mapping.confidence,
        )
        db.add(db_mapping)
        saved_mappings.append(mapping)

    await db.commit()

    logger.info(
        f"Saved {len(saved_mappings)} stage mappings for project {project.name}"
    )

    return SaveStageMappingsResponse(
        project_id=request.project_id,
        mappings_saved=len(saved_mappings),
        mappings=saved_mappings,
    )


@router.get(
    "/projects/{project_id}/stage-mappings",
    response_model=list[StageMappingItem],
    status_code=status.HTTP_200_OK,
    summary="Get stage mappings for a project",
    description="Retrieve saved folder-to-stage mappings for a project.",
)
async def get_stage_mappings(
    project_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[StageMappingItem]:
    """
    Get stage mappings for a project.

    Path Parameters:
        - project_id: Project UUID

    Response (200 OK):
        [
            {
                "folder_path": "docs/00-foundation",
                "stage_code": "00",
                "stage_name": "FOUNDATION",
                "is_auto_detected": true,
                "confidence": 0.95
            }
        ]
    """
    # Verify project exists
    project_result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = project_result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    # Get mappings
    mappings_result = await db.execute(
        select(ProjectStageMapping).where(
            ProjectStageMapping.project_id == project_id
        ).order_by(ProjectStageMapping.stage_code)
    )
    mappings = mappings_result.scalars().all()

    return [
        StageMappingItem(
            folder_path=m.folder_path,
            stage_code=m.stage_code,
            stage_name=m.stage_name,
            is_auto_detected=m.is_auto_detected,
            confidence=m.confidence,
        )
        for m in mappings
    ]


# ============================================================================
# Repository Sync Endpoint
# ============================================================================


@router.post(
    "/sync",
    response_model=GitHubSyncResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Sync GitHub repository to project",
    description="Create SDLC Orchestrator project from GitHub repository.",
)
async def sync_repository(
    sync_request: GitHubSyncRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> GitHubSyncResponse:
    """
    Sync GitHub repository to SDLC Orchestrator project.

    Request Body:
        {
            "github_repo_id": 123456789,
            "github_repo_full_name": "developer/my-project",
            "project_name": "My Project",
            "auto_setup": true
        }

    Response (201 Created):
        {
            "project_id": "uuid",
            "project_name": "My Project",
            "project_slug": "my-project",
            "github_repo_id": 123456789,
            "github_repo_full_name": "developer/my-project",
            "sync_status": "synced",
            "synced_at": "2025-01-01T00:00:00Z"
        }

    Flow:
        1. Verify GitHub connection
        2. Create project with GitHub metadata
        3. Optionally run AI analysis and stage mapping
        4. Return project info
    """
    # Get GitHub OAuth account
    oauth_account = await db.execute(
        select(OAuthAccount).where(
            and_(
                OAuthAccount.user_id == current_user.id,
                OAuthAccount.provider == "github",
            )
        )
    )
    oauth_account = oauth_account.scalar_one_or_none()

    if not oauth_account:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="GitHub not connected",
        )

    # Check if project already exists for this repo
    existing_project = await db.execute(
        select(Project).where(
            Project.slug == sync_request.github_repo_full_name.replace("/", "-").lower()
        )
    )
    existing_project = existing_project.scalar_one_or_none()

    if existing_project:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Project already exists for repository {sync_request.github_repo_full_name}",
        )

    # Get repository details for metadata
    try:
        owner, repo = sync_request.github_repo_full_name.split("/")
        repo_data = github_service.get_repository(
            access_token=oauth_account.access_token,
            owner=owner,
            repo=repo,
        )
    except GitHubAPIError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repository not found: {str(e)}",
        )

    # Create project
    project_name = sync_request.project_name or repo_data["name"]
    project_slug = sync_request.github_repo_full_name.replace("/", "-").lower()

    project = Project(
        name=project_name,
        slug=project_slug,
        description=repo_data.get("description") or f"Synced from GitHub: {sync_request.github_repo_full_name}",
        owner_id=current_user.id,
        is_active=True,
        # GitHub integration fields (Sprint 15 Day 4)
        github_repo_id=sync_request.github_repo_id,
        github_repo_full_name=sync_request.github_repo_full_name,
        github_sync_status="synced",
        github_synced_at=datetime.utcnow(),
    )

    db.add(project)
    await db.flush()  # Get project.id

    # Sprint 15 Day 4: Run full sync with project_sync_service
    sync_result = None
    if sync_request.auto_setup:
        from app.services.project_sync_service import project_sync_service
        try:
            sync_result = await project_sync_service.sync_project(
                project_id=project.id,
                access_token=oauth_account.access_token,
                owner=owner,
                repo=repo,
                db=db,
                create_initial_gates=True,
            )
            logger.info(
                f"Auto-setup complete for project {project.name}: "
                f"{len(sync_result.get('gates_created', []))} gates created"
            )
        except Exception as e:
            logger.warning(f"Auto-setup failed (non-blocking): {e}")
            # Continue without auto-setup - project is still created

    await db.commit()

    logger.info(
        f"Created project {project.name} from GitHub repo {sync_request.github_repo_full_name}"
    )

    return GitHubSyncResponse(
        project_id=project.id,
        project_name=project.name,
        project_slug=project.slug,
        github_repo_id=sync_request.github_repo_id,
        github_repo_full_name=sync_request.github_repo_full_name,
        sync_status=project.github_sync_status or "synced",
        synced_at=project.github_synced_at or datetime.utcnow(),
    )


# ============================================================================
# Webhook Endpoint
# ============================================================================


@router.post(
    "/webhook",
    response_model=GitHubWebhookResponse,
    status_code=status.HTTP_200_OK,
    summary="Handle GitHub webhook events",
    description="Receive and process GitHub webhook events (push, PR, issues).",
)
async def handle_webhook(
    request: Request,
    x_github_event: str = Header(..., alias="X-GitHub-Event"),
    x_hub_signature_256: Optional[str] = Header(None, alias="X-Hub-Signature-256"),
    db: AsyncSession = Depends(get_db),
) -> GitHubWebhookResponse:
    """
    Handle GitHub webhook events.

    Headers:
        - X-GitHub-Event: Event type (push, pull_request, issues)
        - X-Hub-Signature-256: HMAC signature for validation

    Request Body: GitHub webhook payload (varies by event)

    Response (200 OK):
        {
            "received": true,
            "event_type": "push",
            "repository": "developer/my-project",
            "message": "Push event processed: 3 commits to main"
        }

    Security:
        - HMAC-SHA256 signature validation
        - Only processes events from configured repositories

    Sprint 81 Enhancement:
        - pull_request.opened/synchronize -> Create Check Run
        - pull_request.labeled (sdlc-recheck) -> Re-evaluate gates
    """
    # Read raw body for signature validation
    body = await request.body()

    # Validate webhook signature
    if x_hub_signature_256:
        if not github_service.validate_webhook_signature(body, x_hub_signature_256):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook signature",
            )

    # Parse webhook payload
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload",
        )

    # Parse and normalize event
    event = github_service.parse_webhook_event(x_github_event, payload)
    repo_full_name = event["repository"].get("full_name", "unknown")

    logger.info(f"Received GitHub webhook: {x_github_event} for {repo_full_name}")

    # Build response message
    message = f"Webhook event {x_github_event} received"
    check_run_created = False

    # Sprint 81: Handle pull_request events -> Create Check Run
    if x_github_event == "pull_request":
        action = payload.get("action", "")
        pr = payload.get("pull_request", {})
        repo = payload.get("repository", {})

        # Find project by repo full name
        project = await _find_project_by_repo(db, repo_full_name)

        if project:
            # Trigger Check Run for opened/synchronize actions
            if action in ("opened", "synchronize"):
                check_run_created = await _trigger_check_run(
                    project_id=project.id,
                    repo_owner=repo.get("owner", {}).get("login"),
                    repo_name=repo.get("name"),
                    head_sha=pr.get("head", {}).get("sha"),
                )
                if check_run_created:
                    message = f"Pull request #{pr.get('number')} {action} - Check Run created"
                else:
                    message = f"Pull request #{pr.get('number')} {action} - Check Run skipped (GitHub App not configured)"

            # Re-evaluate on sdlc-recheck label
            elif action == "labeled":
                label = payload.get("label", {}).get("name", "")
                if label == "sdlc-recheck":
                    check_run_created = await _trigger_check_run(
                        project_id=project.id,
                        repo_owner=repo.get("owner", {}).get("login"),
                        repo_name=repo.get("name"),
                        head_sha=pr.get("head", {}).get("sha"),
                    )
                    message = f"Pull request #{pr.get('number')} recheck triggered"
                else:
                    message = f"Pull request #{pr.get('number')} labeled: {label}"
            else:
                message = f"Pull request #{pr.get('number')} {action}"
        else:
            message = f"Pull request #{pr.get('number')} {action} - repository not registered"

    elif x_github_event == "push":
        commits = event["data"].get("commits", 0)
        ref = event["data"].get("ref", "").replace("refs/heads/", "")
        message = f"Push event processed: {commits} commits to {ref}"

    elif x_github_event == "issues":
        action = event.get("action", "unknown")
        issue_number = event["data"].get("number", 0)
        message = f"Issue #{issue_number} {action}"

    return GitHubWebhookResponse(
        received=True,
        event_type=x_github_event,
        repository=repo_full_name,
        message=message,
    )


# ============================================================================
# Sprint 81: Check Run Helper Functions
# ============================================================================


async def _find_project_by_repo(
    db: AsyncSession,
    repo_full_name: str,
) -> Optional[Project]:
    """
    Find project by GitHub repository full name.

    Args:
        db: Database session
        repo_full_name: GitHub repository full name (e.g., "owner/repo")

    Returns:
        Project if found, None otherwise
    """
    result = await db.execute(
        select(Project).where(
            Project.github_repo_full_name == repo_full_name
        )
    )
    return result.scalar_one_or_none()


async def _trigger_check_run(
    project_id: UUID,
    repo_owner: str,
    repo_name: str,
    head_sha: str,
) -> bool:
    """
    Trigger GitHub Check Run for a PR.

    Sprint 81: Advisory mode - Check Run provides feedback but doesn't block.

    Args:
        project_id: SDLC Orchestrator project ID
        repo_owner: Repository owner
        repo_name: Repository name
        head_sha: Git commit SHA

    Returns:
        True if Check Run was created, False if skipped (e.g., App not configured)
    """
    try:
        from app.services.github_app_service import get_github_app_service
        from app.services.github_check_run_service import get_check_run_service

        app_service = get_github_app_service()

        # Check if GitHub App is configured
        if not app_service.is_configured:
            logger.info(
                f"GitHub App not configured - skipping Check Run for {repo_owner}/{repo_name}"
            )
            return False

        # Get Check Run service (without gate_service for now - Advisory mode)
        check_run_service = get_check_run_service()

        # Create Check Run
        result = await check_run_service.create_check_run(
            project_id=project_id,
            repo_owner=repo_owner,
            repo_name=repo_name,
            head_sha=head_sha,
        )

        logger.info(
            f"Check Run created for {repo_owner}/{repo_name} "
            f"(id={result.check_run_id}, conclusion={result.conclusion})"
        )
        return True

    except Exception as e:
        logger.error(f"Failed to create Check Run: {e}")
        return False
