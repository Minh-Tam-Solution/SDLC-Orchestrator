"""
=========================================================================
GitHub Service - Repository Integration (Sprint 15)
SDLC Orchestrator - Stage 03 (BUILD)

Version: 1.0.0
Date: November 28, 2025
Status: ACTIVE - Sprint 15 (GitHub Foundation)
Authority: Backend Lead + CTO Approved
Foundation: Sprint 15 Plan, User-Onboarding-Flow-Architecture.md
Framework: SDLC 4.9 Complete Lifecycle

Purpose:
- GitHub OAuth token management (store, refresh, validate)
- Repository listing and details (read-only access)
- Webhook event handling (push, pull_request, issues)
- Rate limiting awareness (5,000 requests/hour per token)

AGPL-Safe Implementation:
- Uses Python requests library (Apache 2.0 license)
- Network-only access via GitHub REST API
- No PyGithub SDK (avoid tight coupling)

Zero Mock Policy: 100% real implementation (requests + GitHub API)
=========================================================================
"""

import hashlib
import hmac
import logging
from datetime import datetime, timedelta
from typing import Any, Optional
from uuid import UUID

import requests
from requests.exceptions import RequestException, Timeout

from app.core.config import settings

logger = logging.getLogger(__name__)

# ============================================================================
# Constants
# ============================================================================

GITHUB_API_BASE_URL = "https://api.github.com"
GITHUB_OAUTH_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
GITHUB_OAUTH_TOKEN_URL = "https://github.com/login/oauth/access_token"

# Default scopes for repository access (read-only)
DEFAULT_SCOPES = ["read:user", "user:email", "repo"]

# Rate limiting
RATE_LIMIT_REQUESTS_PER_HOUR = 5000
RATE_LIMIT_REMAINING_THRESHOLD = 100  # Warn when below this


# ============================================================================
# Custom Exceptions
# ============================================================================


class GitHubServiceError(Exception):
    """Base exception for GitHub service errors."""

    pass


class GitHubAuthError(GitHubServiceError):
    """Exception raised when GitHub authentication fails."""

    pass


class GitHubRateLimitError(GitHubServiceError):
    """Exception raised when GitHub rate limit is exceeded."""

    pass


class GitHubAPIError(GitHubServiceError):
    """Exception raised when GitHub API call fails."""

    pass


# ============================================================================
# GitHub Service
# ============================================================================


class GitHubService:
    """
    GitHub service adapter using REST API.

    AGPL-Safe Implementation:
    - Uses Python requests library (Apache 2.0 license)
    - Network-only access via GitHub REST API
    - No code dependencies on PyGithub

    Usage:
        github = GitHubService()

        # Get OAuth authorization URL
        auth_url = github.get_authorization_url(state="random_state")

        # Exchange code for token
        token_data = github.exchange_code_for_token(code="...")

        # List repositories
        repos = github.list_repositories(access_token="...")

        # Validate webhook signature
        is_valid = github.validate_webhook_signature(payload, signature)
    """

    def __init__(self):
        """Initialize GitHub service with configuration."""
        self.client_id = settings.GITHUB_CLIENT_ID
        self.client_secret = settings.GITHUB_CLIENT_SECRET
        self.webhook_secret = getattr(settings, "GITHUB_WEBHOOK_SECRET", None)
        self.timeout = 30  # 30 seconds timeout
        self.base_url = GITHUB_API_BASE_URL

        logger.info("GitHub service initialized")

    # ============================================================================
    # OAuth Flow
    # ============================================================================

    def get_authorization_url(
        self,
        state: str,
        redirect_uri: Optional[str] = None,
        scopes: Optional[list[str]] = None,
    ) -> str:
        """
        Generate GitHub OAuth authorization URL.

        Args:
            state: Random state for CSRF protection
            redirect_uri: OAuth callback URL (optional)
            scopes: OAuth scopes (default: read:user, user:email, repo)

        Returns:
            GitHub authorization URL

        Example:
            auth_url = github.get_authorization_url(
                state="abc123",
                redirect_uri="https://app.example.com/auth/github/callback"
            )
            # Returns: https://github.com/login/oauth/authorize?client_id=...
        """
        if not self.client_id:
            raise GitHubAuthError("GitHub client ID not configured")

        scopes = scopes or DEFAULT_SCOPES
        scope_str = " ".join(scopes)

        params = {
            "client_id": self.client_id,
            "scope": scope_str,
            "state": state,
        }

        if redirect_uri:
            params["redirect_uri"] = redirect_uri

        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{GITHUB_OAUTH_AUTHORIZE_URL}?{query_string}"

    def exchange_code_for_token(
        self,
        code: str,
        redirect_uri: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Exchange OAuth authorization code for access token.

        Args:
            code: Authorization code from GitHub callback
            redirect_uri: OAuth callback URL (must match authorization request)

        Returns:
            Token data:
            {
                "access_token": "gho_...",
                "token_type": "bearer",
                "scope": "read:user,user:email,repo"
            }

        Raises:
            GitHubAuthError: If token exchange fails

        Example:
            token_data = github.exchange_code_for_token(code="abc123")
            access_token = token_data["access_token"]
        """
        if not self.client_id or not self.client_secret:
            raise GitHubAuthError("GitHub OAuth credentials not configured")

        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
        }

        if redirect_uri:
            payload["redirect_uri"] = redirect_uri

        try:
            response = requests.post(
                GITHUB_OAUTH_TOKEN_URL,
                data=payload,
                headers={"Accept": "application/json"},
                timeout=self.timeout,
            )

            if response.status_code != 200:
                logger.error(f"GitHub token exchange failed: {response.status_code}")
                raise GitHubAuthError(f"Token exchange failed: {response.text}")

            token_data = response.json()

            if "error" in token_data:
                error_msg = token_data.get("error_description", token_data["error"])
                logger.error(f"GitHub OAuth error: {error_msg}")
                raise GitHubAuthError(f"OAuth error: {error_msg}")

            logger.info("GitHub token exchange successful")
            return token_data

        except Timeout:
            logger.error("GitHub token exchange timeout")
            raise GitHubAuthError("Token exchange timed out")

        except RequestException as e:
            logger.error(f"GitHub token exchange request failed: {e}")
            raise GitHubAuthError(f"Token exchange request failed: {str(e)}")

    def validate_access_token(self, access_token: str) -> dict[str, Any]:
        """
        Validate access token and get current user info.

        Args:
            access_token: GitHub OAuth access token

        Returns:
            User info:
            {
                "id": 12345,
                "login": "username",
                "email": "user@example.com",
                "name": "User Name",
                "avatar_url": "https://..."
            }

        Raises:
            GitHubAuthError: If token is invalid

        Example:
            user_info = github.validate_access_token("gho_...")
            github_user_id = user_info["id"]
        """
        try:
            response = self._make_request(
                method="GET",
                endpoint="/user",
                access_token=access_token,
            )
            return response

        except GitHubAPIError as e:
            raise GitHubAuthError(f"Invalid access token: {str(e)}")

    # ============================================================================
    # Repository Operations
    # ============================================================================

    def list_repositories(
        self,
        access_token: str,
        visibility: str = "all",
        sort: str = "updated",
        direction: str = "desc",
        per_page: int = 100,
        page: int = 1,
    ) -> list[dict[str, Any]]:
        """
        List repositories for authenticated user.

        Args:
            access_token: GitHub OAuth access token
            visibility: Repository visibility ('all', 'public', 'private')
            sort: Sort field ('created', 'updated', 'pushed', 'full_name')
            direction: Sort direction ('asc', 'desc')
            per_page: Results per page (max 100)
            page: Page number

        Returns:
            List of repository objects:
            [
                {
                    "id": 12345,
                    "name": "repo-name",
                    "full_name": "owner/repo-name",
                    "description": "...",
                    "html_url": "https://github.com/...",
                    "language": "Python",
                    "default_branch": "main",
                    "private": false,
                    "fork": false,
                    "stargazers_count": 100,
                    "updated_at": "2025-01-01T00:00:00Z"
                }
            ]

        Example:
            repos = github.list_repositories(access_token="gho_...")
            for repo in repos:
                print(f"{repo['full_name']}: {repo['description']}")
        """
        params = {
            "visibility": visibility,
            "sort": sort,
            "direction": direction,
            "per_page": min(per_page, 100),
            "page": page,
        }

        return self._make_request(
            method="GET",
            endpoint="/user/repos",
            access_token=access_token,
            params=params,
        )

    def get_repository(
        self,
        access_token: str,
        owner: str,
        repo: str,
    ) -> dict[str, Any]:
        """
        Get repository details.

        Args:
            access_token: GitHub OAuth access token
            owner: Repository owner (username or organization)
            repo: Repository name

        Returns:
            Repository object with full details

        Raises:
            GitHubAPIError: If repository not found or access denied

        Example:
            repo = github.get_repository(
                access_token="gho_...",
                owner="anthropics",
                repo="claude-code"
            )
            print(f"Stars: {repo['stargazers_count']}")
        """
        return self._make_request(
            method="GET",
            endpoint=f"/repos/{owner}/{repo}",
            access_token=access_token,
        )

    def get_repository_contents(
        self,
        access_token: str,
        owner: str,
        repo: str,
        path: str = "",
        ref: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """
        Get repository contents (files and directories).

        Args:
            access_token: GitHub OAuth access token
            owner: Repository owner
            repo: Repository name
            path: Path within repository (default: root)
            ref: Branch/tag/commit reference (default: default branch)

        Returns:
            List of content items:
            [
                {
                    "name": "README.md",
                    "path": "README.md",
                    "type": "file",
                    "size": 1234,
                    "sha": "abc123..."
                }
            ]

        Example:
            contents = github.get_repository_contents(
                access_token="gho_...",
                owner="anthropics",
                repo="claude-code",
                path="src"
            )
        """
        params = {}
        if ref:
            params["ref"] = ref

        return self._make_request(
            method="GET",
            endpoint=f"/repos/{owner}/{repo}/contents/{path}",
            access_token=access_token,
            params=params if params else None,
        )

    def get_repository_languages(
        self,
        access_token: str,
        owner: str,
        repo: str,
    ) -> dict[str, int]:
        """
        Get repository language breakdown.

        Args:
            access_token: GitHub OAuth access token
            owner: Repository owner
            repo: Repository name

        Returns:
            Language breakdown (bytes per language):
            {
                "Python": 123456,
                "TypeScript": 78901,
                "JavaScript": 45678
            }

        Example:
            languages = github.get_repository_languages(...)
            primary_language = max(languages, key=languages.get)
        """
        return self._make_request(
            method="GET",
            endpoint=f"/repos/{owner}/{repo}/languages",
            access_token=access_token,
        )

    # ============================================================================
    # Webhook Handling
    # ============================================================================

    def validate_webhook_signature(
        self,
        payload: bytes,
        signature: str,
    ) -> bool:
        """
        Validate GitHub webhook signature (HMAC-SHA256).

        Args:
            payload: Raw request body (bytes)
            signature: X-Hub-Signature-256 header value

        Returns:
            True if signature is valid, False otherwise

        Example:
            is_valid = github.validate_webhook_signature(
                payload=request.body,
                signature=request.headers.get("X-Hub-Signature-256")
            )
            if not is_valid:
                raise HTTPException(status_code=401, detail="Invalid signature")
        """
        if not self.webhook_secret:
            logger.warning("Webhook secret not configured, skipping validation")
            return True  # Allow in development

        if not signature or not signature.startswith("sha256="):
            logger.warning("Invalid webhook signature format")
            return False

        expected_signature = hmac.new(
            key=self.webhook_secret.encode("utf-8"),
            msg=payload,
            digestmod=hashlib.sha256,
        ).hexdigest()

        expected_header = f"sha256={expected_signature}"
        return hmac.compare_digest(expected_header, signature)

    def parse_webhook_event(
        self,
        event_type: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Parse GitHub webhook event into normalized format.

        Args:
            event_type: X-GitHub-Event header value
            payload: Webhook JSON payload

        Returns:
            Normalized event data:
            {
                "event_type": "push",
                "repository": {"id": ..., "full_name": ...},
                "sender": {"id": ..., "login": ...},
                "action": "created",  # For PR/issue events
                "data": {...}  # Event-specific data
            }

        Example:
            event = github.parse_webhook_event(
                event_type="push",
                payload=request.json()
            )
        """
        repository = payload.get("repository", {})
        sender = payload.get("sender", {})

        normalized = {
            "event_type": event_type,
            "repository": {
                "id": repository.get("id"),
                "full_name": repository.get("full_name"),
                "name": repository.get("name"),
                "owner": repository.get("owner", {}).get("login"),
                "private": repository.get("private"),
            },
            "sender": {
                "id": sender.get("id"),
                "login": sender.get("login"),
            },
            "action": payload.get("action"),
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Add event-specific data
        if event_type == "push":
            normalized["data"] = {
                "ref": payload.get("ref"),
                "before": payload.get("before"),
                "after": payload.get("after"),
                "commits": len(payload.get("commits", [])),
                "head_commit": payload.get("head_commit", {}).get("message"),
            }

        elif event_type == "pull_request":
            pr = payload.get("pull_request", {})
            normalized["data"] = {
                "number": pr.get("number"),
                "title": pr.get("title"),
                "state": pr.get("state"),
                "merged": pr.get("merged"),
                "head_branch": pr.get("head", {}).get("ref"),
                "base_branch": pr.get("base", {}).get("ref"),
            }

        elif event_type == "issues":
            issue = payload.get("issue", {})
            normalized["data"] = {
                "number": issue.get("number"),
                "title": issue.get("title"),
                "state": issue.get("state"),
                "labels": [l.get("name") for l in issue.get("labels", [])],
            }

        elif event_type == "create" or event_type == "delete":
            normalized["data"] = {
                "ref": payload.get("ref"),
                "ref_type": payload.get("ref_type"),
            }

        else:
            normalized["data"] = {}

        return normalized

    # ============================================================================
    # Rate Limiting
    # ============================================================================

    # ============================================================================
    # Sprint 100 (EP-11): Pull Request Comments
    # ============================================================================

    def get_pull_request_comments(
        self,
        access_token: str,
        owner: str,
        repo: str,
        pr_number: int,
    ) -> list[dict[str, Any]]:
        """
        Get all review comments on a pull request.

        Sprint 100 EP-11: Fetch review comments for learning extraction.

        Args:
            access_token: GitHub OAuth access token
            owner: Repository owner
            repo: Repository name
            pr_number: Pull request number

        Returns:
            List of review comment objects:
            [
                {
                    "id": 12345,
                    "body": "This should use async/await...",
                    "path": "backend/app/services/example.py",
                    "line": 42,
                    "original_line": 40,
                    "diff_hunk": "@@ -39,7 +39,7 @@...",
                    "user": {"id": 123, "login": "reviewer"},
                    "created_at": "2025-01-01T00:00:00Z"
                }
            ]

        Example:
            comments = github.get_pull_request_comments(
                access_token="gho_...",
                owner="org",
                repo="project",
                pr_number=123
            )
        """
        return self._make_request(
            method="GET",
            endpoint=f"/repos/{owner}/{repo}/pulls/{pr_number}/comments",
            access_token=access_token,
        )

    def get_pull_request(
        self,
        access_token: str,
        owner: str,
        repo: str,
        pr_number: int,
    ) -> dict[str, Any]:
        """
        Get pull request details.

        Args:
            access_token: GitHub OAuth access token
            owner: Repository owner
            repo: Repository name
            pr_number: Pull request number

        Returns:
            Pull request object with full details

        Example:
            pr = github.get_pull_request(
                access_token="gho_...",
                owner="org",
                repo="project",
                pr_number=123
            )
        """
        return self._make_request(
            method="GET",
            endpoint=f"/repos/{owner}/{repo}/pulls/{pr_number}",
            access_token=access_token,
        )

    # ============================================================================
    # Rate Limiting
    # ============================================================================

    def get_rate_limit(self, access_token: str) -> dict[str, Any]:
        """
        Get current rate limit status.

        Args:
            access_token: GitHub OAuth access token

        Returns:
            Rate limit info:
            {
                "limit": 5000,
                "remaining": 4999,
                "reset": 1234567890,
                "used": 1
            }

        Example:
            rate = github.get_rate_limit(access_token="gho_...")
            if rate["remaining"] < 100:
                print("Warning: Rate limit running low")
        """
        return self._make_request(
            method="GET",
            endpoint="/rate_limit",
            access_token=access_token,
        )

    # ============================================================================
    # Private Methods
    # ============================================================================

    def _make_request(
        self,
        method: str,
        endpoint: str,
        access_token: str,
        params: Optional[dict] = None,
        data: Optional[dict] = None,
    ) -> Any:
        """
        Make authenticated request to GitHub API.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (e.g., /user/repos)
            access_token: GitHub OAuth access token
            params: Query parameters
            data: Request body (JSON)

        Returns:
            Response JSON data

        Raises:
            GitHubRateLimitError: If rate limit exceeded
            GitHubAPIError: If API call fails
        """
        url = f"{self.base_url}{endpoint}"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=data,
                timeout=self.timeout,
            )

            # Check rate limiting
            remaining = int(response.headers.get("X-RateLimit-Remaining", 5000))
            if remaining < RATE_LIMIT_REMAINING_THRESHOLD:
                reset_time = int(response.headers.get("X-RateLimit-Reset", 0))
                reset_dt = datetime.fromtimestamp(reset_time)
                logger.warning(
                    f"GitHub rate limit low: {remaining} remaining, "
                    f"resets at {reset_dt.isoformat()}"
                )

            if remaining == 0:
                reset_time = int(response.headers.get("X-RateLimit-Reset", 0))
                raise GitHubRateLimitError(
                    f"Rate limit exceeded. Resets at {datetime.fromtimestamp(reset_time)}"
                )

            # Handle errors
            if response.status_code == 401:
                raise GitHubAuthError("Invalid or expired access token")

            if response.status_code == 403:
                if remaining == 0:
                    raise GitHubRateLimitError("Rate limit exceeded")
                raise GitHubAPIError("Access forbidden")

            if response.status_code == 404:
                raise GitHubAPIError("Resource not found")

            if response.status_code >= 400:
                error_msg = response.json().get("message", response.text)
                raise GitHubAPIError(f"API error ({response.status_code}): {error_msg}")

            # Return JSON response
            if response.text:
                return response.json()
            return None

        except Timeout:
            logger.error(f"GitHub API timeout: {endpoint}")
            raise GitHubAPIError(f"Request to {endpoint} timed out")

        except RequestException as e:
            logger.error(f"GitHub API request failed: {endpoint}, Error: {e}")
            raise GitHubAPIError(f"Request failed: {str(e)}")


# ============================================================================
# Global GitHub Service Instance
# ============================================================================

# Singleton instance (initialized on first import)
github_service = GitHubService()
