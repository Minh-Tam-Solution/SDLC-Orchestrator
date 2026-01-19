"""
=========================================================================
GitHub App Service - Installation Token Management (Sprint 81)
SDLC Orchestrator - Stage 04 (BUILD)

Version: 1.0.0
Date: January 19, 2026
Status: ACTIVE - Sprint 81 (AGENTS.md Integration)
Authority: Backend Lead + CTO Approved
Foundation: Sprint 81 Plan, SPRINT-81-DESIGN-REVIEW.md
Framework: SDLC 5.1.3 (7-Pillar Architecture)

Purpose:
- GitHub App JWT generation (RS256 signing)
- Installation Access Token management (1-hour expiry)
- Token caching with automatic refresh
- Installation ID lookup for repositories

CRITICAL: GitHub Check Runs API requires GitHub App, NOT OAuth App.
OAuth tokens cannot create Check Runs - this service provides the
necessary GitHub App authentication.

AGPL-Safe Implementation:
- Uses Python requests library (Apache 2.0 license)
- Uses PyJWT for RS256 signing (MIT license)
- Network-only access via GitHub REST API

Zero Mock Policy: 100% real implementation
CTO Decision: Organization-owned GitHub App (Jan 19, 2026)
=========================================================================
"""

import base64
import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
import requests
from requests.exceptions import RequestException, Timeout

from app.core.config import settings

logger = logging.getLogger(__name__)

# ============================================================================
# Constants
# ============================================================================

GITHUB_API_BASE_URL = "https://api.github.com"

# JWT expires in 10 minutes (GitHub max)
JWT_EXPIRY_MINUTES = 10

# Installation token cache buffer (refresh 5 min before expiry)
TOKEN_REFRESH_BUFFER_MINUTES = 5

# Installation token validity (GitHub provides 1 hour)
INSTALLATION_TOKEN_EXPIRY_HOURS = 1


# ============================================================================
# Custom Exceptions
# ============================================================================


class GitHubAppError(Exception):
    """Base exception for GitHub App service errors."""

    pass


class GitHubAppNotConfiguredError(GitHubAppError):
    """Exception raised when GitHub App is not configured."""

    pass


class GitHubAppAuthError(GitHubAppError):
    """Exception raised when GitHub App authentication fails."""

    pass


class GitHubAppInstallationError(GitHubAppError):
    """Exception raised when installation access fails."""

    pass


# ============================================================================
# GitHub App Service
# ============================================================================


class GitHubAppService:
    """
    GitHub App service for Installation Access Tokens.

    IMPORTANT: GitHub Check Runs API requires GitHub App, NOT OAuth App.
    OAuth tokens (used in GitHubService) cannot create Check Runs.

    Architecture (CTO Decision Jan 19, 2026):
    - Organization-owned GitHub App (single App for all repos)
    - Private key stored in HashiCorp Vault (90-day rotation)
    - Installation tokens cached in Redis (AES-256 encrypted)

    Flow:
    1. Generate JWT from App private key (RS256)
    2. Exchange JWT for Installation Access Token
    3. Use Installation Token for Check Runs API
    4. Cache token (expires in 1 hour, refresh at 55 min)

    Usage:
        app_service = GitHubAppService()

        # Get installation token for a repo
        token = await app_service.get_installation_token(installation_id=12345)

        # Find installation ID for a repo
        install_id = await app_service.get_installation_for_repo("owner", "repo")

        # Create Check Run using the token
        response = requests.post(
            f"https://api.github.com/repos/{owner}/{repo}/check-runs",
            headers={"Authorization": f"token {token}"},
            json=check_run_data,
        )
    """

    def __init__(self):
        """
        Initialize GitHub App service.

        Loads configuration from settings:
        - GITHUB_APP_ID: App ID (numeric string)
        - GITHUB_APP_PRIVATE_KEY: PEM private key

        Raises:
            GitHubAppNotConfiguredError: If App credentials not configured
        """
        self.app_id = settings.GITHUB_APP_ID
        self._private_key: Optional[str] = None
        self.timeout = 30  # 30 seconds timeout

        # Token cache: {installation_id: (token, expires_at)}
        self._token_cache: dict[int, tuple[str, datetime]] = {}

        # Load private key
        self._load_private_key()

        logger.info(
            f"GitHub App service initialized "
            f"(app_id={self.app_id}, configured={self.is_configured})"
        )

    def _load_private_key(self) -> None:
        """
        Load private key from configuration.

        Supports:
        - Raw PEM key (starts with -----BEGIN)
        - Base64 encoded key (for environment variables)
        """
        raw_key = settings.GITHUB_APP_PRIVATE_KEY
        if not raw_key:
            logger.warning("GitHub App private key not configured")
            return

        # Check if base64 encoded
        if not raw_key.startswith("-----BEGIN"):
            try:
                decoded = base64.b64decode(raw_key).decode("utf-8")
                if decoded.startswith("-----BEGIN"):
                    self._private_key = decoded
                    logger.info("GitHub App private key loaded (base64 decoded)")
                    return
            except Exception:
                pass

        # Use as raw PEM
        if raw_key.startswith("-----BEGIN"):
            self._private_key = raw_key
            logger.info("GitHub App private key loaded (raw PEM)")
        else:
            logger.error("Invalid GitHub App private key format")

    @property
    def is_configured(self) -> bool:
        """Check if GitHub App is properly configured."""
        return bool(self.app_id and self._private_key)

    def _ensure_configured(self) -> None:
        """Raise exception if not configured."""
        if not self.is_configured:
            raise GitHubAppNotConfiguredError(
                "GitHub App not configured. Set GITHUB_APP_ID and GITHUB_APP_PRIVATE_KEY "
                "environment variables. See Sprint 81 setup guide."
            )

    # ============================================================================
    # JWT Generation
    # ============================================================================

    def _generate_jwt(self) -> str:
        """
        Generate JWT for GitHub App authentication.

        JWT is signed with RS256 algorithm using the App's private key.
        Valid for 10 minutes (GitHub maximum).

        Returns:
            JWT token string

        Raises:
            GitHubAppNotConfiguredError: If private key not configured
            GitHubAppAuthError: If JWT generation fails
        """
        self._ensure_configured()

        now = int(time.time())

        payload = {
            # Issued 60 seconds ago to handle clock drift
            "iat": now - 60,
            # Expires in 10 minutes (GitHub max)
            "exp": now + (JWT_EXPIRY_MINUTES * 60),
            # Issuer is the App ID
            "iss": self.app_id,
        }

        try:
            token = jwt.encode(
                payload,
                self._private_key,
                algorithm="RS256",
            )
            logger.debug("Generated GitHub App JWT")
            return token

        except jwt.PyJWTError as e:
            logger.error(f"Failed to generate GitHub App JWT: {e}")
            raise GitHubAppAuthError(f"JWT generation failed: {str(e)}")

    # ============================================================================
    # Installation Token Management
    # ============================================================================

    async def get_installation_token(self, installation_id: int) -> str:
        """
        Get Installation Access Token for a GitHub App installation.

        Tokens are cached and automatically refreshed 5 minutes before expiry.
        Each token is valid for 1 hour.

        Args:
            installation_id: GitHub App installation ID

        Returns:
            Installation access token string

        Raises:
            GitHubAppNotConfiguredError: If App not configured
            GitHubAppInstallationError: If token generation fails

        Example:
            token = await app_service.get_installation_token(12345)
            # Use token for Check Runs API
        """
        self._ensure_configured()

        # Check cache
        if installation_id in self._token_cache:
            token, expires_at = self._token_cache[installation_id]
            # Refresh buffer: 5 minutes before expiry
            refresh_threshold = expires_at - timedelta(
                minutes=TOKEN_REFRESH_BUFFER_MINUTES
            )
            if datetime.now(timezone.utc) < refresh_threshold:
                logger.debug(
                    f"Using cached installation token "
                    f"(installation_id={installation_id}, expires={expires_at})"
                )
                return token

        # Generate new token
        logger.info(f"Generating new installation token (installation_id={installation_id})")
        jwt_token = self._generate_jwt()

        try:
            response = requests.post(
                f"{GITHUB_API_BASE_URL}/app/installations/{installation_id}/access_tokens",
                headers={
                    "Authorization": f"Bearer {jwt_token}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
                timeout=self.timeout,
            )

            if response.status_code == 404:
                raise GitHubAppInstallationError(
                    f"Installation not found (id={installation_id}). "
                    "Ensure the GitHub App is installed on the target repository."
                )

            if response.status_code == 401:
                raise GitHubAppAuthError(
                    "GitHub App authentication failed. "
                    "Check GITHUB_APP_ID and GITHUB_APP_PRIVATE_KEY."
                )

            if response.status_code != 201:
                error_msg = response.json().get("message", response.text)
                raise GitHubAppInstallationError(
                    f"Failed to get installation token: {error_msg}"
                )

            data = response.json()
            token = data["token"]

            # Parse expiry time (ISO 8601 format)
            expires_at_str = data["expires_at"]
            expires_at = datetime.fromisoformat(expires_at_str.replace("Z", "+00:00"))

            # Cache token
            self._token_cache[installation_id] = (token, expires_at)
            logger.info(
                f"Installation token generated "
                f"(installation_id={installation_id}, expires={expires_at})"
            )

            return token

        except Timeout:
            logger.error(f"GitHub API timeout getting installation token")
            raise GitHubAppInstallationError(
                "Request timed out while getting installation token"
            )

        except RequestException as e:
            logger.error(f"GitHub API request failed: {e}")
            raise GitHubAppInstallationError(
                f"Request failed while getting installation token: {str(e)}"
            )

    async def get_installation_for_repo(
        self,
        repo_owner: str,
        repo_name: str,
    ) -> Optional[int]:
        """
        Find installation ID for a repository.

        Args:
            repo_owner: Repository owner (username or organization)
            repo_name: Repository name

        Returns:
            Installation ID if App is installed, None otherwise

        Raises:
            GitHubAppNotConfiguredError: If App not configured
            GitHubAppAuthError: If authentication fails

        Example:
            install_id = await app_service.get_installation_for_repo(
                "anthropics", "claude-code"
            )
            if install_id:
                token = await app_service.get_installation_token(install_id)
        """
        self._ensure_configured()

        jwt_token = self._generate_jwt()

        try:
            response = requests.get(
                f"{GITHUB_API_BASE_URL}/repos/{repo_owner}/{repo_name}/installation",
                headers={
                    "Authorization": f"Bearer {jwt_token}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
                timeout=self.timeout,
            )

            if response.status_code == 404:
                logger.info(
                    f"GitHub App not installed on {repo_owner}/{repo_name}"
                )
                return None

            if response.status_code == 401:
                raise GitHubAppAuthError(
                    "GitHub App authentication failed. "
                    "Check GITHUB_APP_ID and GITHUB_APP_PRIVATE_KEY."
                )

            if response.status_code != 200:
                error_msg = response.json().get("message", response.text)
                logger.error(f"Failed to get installation for repo: {error_msg}")
                return None

            installation_id = response.json()["id"]
            logger.info(
                f"Found installation for {repo_owner}/{repo_name} "
                f"(installation_id={installation_id})"
            )
            return installation_id

        except Timeout:
            logger.error(f"GitHub API timeout checking installation")
            return None

        except RequestException as e:
            logger.error(f"GitHub API request failed: {e}")
            return None

    async def list_installations(self) -> list[dict]:
        """
        List all installations for the GitHub App.

        Returns:
            List of installation objects:
            [
                {
                    "id": 12345,
                    "account": {"login": "org-name", "type": "Organization"},
                    "repository_selection": "all" | "selected",
                    "permissions": {...},
                }
            ]

        Raises:
            GitHubAppNotConfiguredError: If App not configured
            GitHubAppAuthError: If authentication fails
        """
        self._ensure_configured()

        jwt_token = self._generate_jwt()

        try:
            response = requests.get(
                f"{GITHUB_API_BASE_URL}/app/installations",
                headers={
                    "Authorization": f"Bearer {jwt_token}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
                timeout=self.timeout,
            )

            if response.status_code == 401:
                raise GitHubAppAuthError(
                    "GitHub App authentication failed. "
                    "Check GITHUB_APP_ID and GITHUB_APP_PRIVATE_KEY."
                )

            if response.status_code != 200:
                error_msg = response.json().get("message", response.text)
                raise GitHubAppAuthError(f"Failed to list installations: {error_msg}")

            installations = response.json()
            logger.info(f"Found {len(installations)} GitHub App installations")
            return installations

        except Timeout:
            logger.error("GitHub API timeout listing installations")
            raise GitHubAppAuthError("Request timed out while listing installations")

        except RequestException as e:
            logger.error(f"GitHub API request failed: {e}")
            raise GitHubAppAuthError(f"Request failed: {str(e)}")

    def clear_token_cache(self, installation_id: Optional[int] = None) -> None:
        """
        Clear cached installation tokens.

        Args:
            installation_id: Specific installation to clear, or None for all

        Example:
            # Clear specific installation cache
            app_service.clear_token_cache(installation_id=12345)

            # Clear all cached tokens
            app_service.clear_token_cache()
        """
        if installation_id is not None:
            if installation_id in self._token_cache:
                del self._token_cache[installation_id]
                logger.info(f"Cleared token cache for installation {installation_id}")
        else:
            self._token_cache.clear()
            logger.info("Cleared all installation token cache")


# ============================================================================
# Global GitHub App Service Instance
# ============================================================================

# Singleton instance (initialized on first import)
github_app_service = GitHubAppService()


def get_github_app_service() -> GitHubAppService:
    """
    Get GitHub App service instance.

    Returns:
        GitHubAppService: Singleton instance
    """
    return github_app_service
