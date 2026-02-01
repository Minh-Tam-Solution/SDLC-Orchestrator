"""
GitHub Service for CLI.

Sprint 129 Day 5 - CLI GitHub Integration
Provides GitHub App installation detection, repository validation,
and clone functionality for the sdlcctl CLI.

Reference: ADR-044-GitHub-Integration-Strategy.md
"""

import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import requests
from rich.console import Console

console = Console()

# GitHub repository format regex: owner/repo
GITHUB_REPO_PATTERN = re.compile(
    r"^(?P<owner>[a-zA-Z0-9](?:[a-zA-Z0-9]|-(?=[a-zA-Z0-9])){0,38})"
    r"/"
    r"(?P<repo>[a-zA-Z0-9._-]{1,100})$"
)

# Alternative patterns for full URLs
GITHUB_URL_PATTERNS = [
    # https://github.com/owner/repo
    re.compile(
        r"^https?://github\.com/"
        r"(?P<owner>[a-zA-Z0-9](?:[a-zA-Z0-9]|-(?=[a-zA-Z0-9])){0,38})"
        r"/"
        r"(?P<repo>[a-zA-Z0-9._-]{1,100})(?:\.git)?/?$"
    ),
    # git@github.com:owner/repo.git
    re.compile(
        r"^git@github\.com:"
        r"(?P<owner>[a-zA-Z0-9](?:[a-zA-Z0-9]|-(?=[a-zA-Z0-9])){0,38})"
        r"/"
        r"(?P<repo>[a-zA-Z0-9._-]{1,100})(?:\.git)?$"
    ),
]


class GitHubServiceError(Exception):
    """Base error for GitHub service operations."""

    def __init__(self, message: str, code: str = "GITHUB_ERROR"):
        self.message = message
        self.code = code
        super().__init__(message)


class GitHubRepoFormatError(GitHubServiceError):
    """Invalid repository format."""

    def __init__(self, repo_input: str):
        super().__init__(
            f"Invalid GitHub repository format: '{repo_input}'. "
            f"Expected format: 'owner/repo' or 'https://github.com/owner/repo'",
            code="INVALID_REPO_FORMAT",
        )


class GitHubAppNotInstalledError(GitHubServiceError):
    """GitHub App not installed on the repository."""

    def __init__(self, owner: str, repo: str):
        self.owner = owner
        self.repo = repo
        super().__init__(
            f"SDLC Orchestrator GitHub App is not installed on {owner}/{repo}. "
            f"Please install it at: https://github.com/apps/sdlc-orchestrator/installations/new",
            code="APP_NOT_INSTALLED",
        )


class GitHubCloneError(GitHubServiceError):
    """Repository clone failed."""

    def __init__(self, owner: str, repo: str, reason: str):
        self.owner = owner
        self.repo = repo
        self.reason = reason
        super().__init__(
            f"Failed to clone {owner}/{repo}: {reason}",
            code="CLONE_FAILED",
        )


class GitHubApiError(GitHubServiceError):
    """GitHub API error."""

    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        super().__init__(
            f"GitHub API error ({status_code}): {message}",
            code="API_ERROR",
        )


@dataclass
class ParsedRepository:
    """Parsed GitHub repository information."""

    owner: str
    repo: str
    full_name: str

    @property
    def clone_url(self) -> str:
        """Get HTTPS clone URL."""
        return f"https://github.com/{self.owner}/{self.repo}.git"

    @property
    def html_url(self) -> str:
        """Get repository HTML URL."""
        return f"https://github.com/{self.owner}/{self.repo}"


@dataclass
class GitHubInstallation:
    """GitHub App installation information."""

    id: str
    installation_id: int
    account_login: str
    account_type: str
    status: str


class GitHubService:
    """
    GitHub service for CLI operations.

    Provides:
    - Repository format validation
    - GitHub App installation detection
    - Repository cloning
    - API integration with SDLC Orchestrator backend

    Usage:
        service = GitHubService(api_base_url="http://localhost:8000/api/v1")
        repo = service.parse_repository("owner/repo")
        if service.check_app_installed(repo.owner, repo.repo):
            service.clone_repository(repo, Path("./my-project"))
    """

    def __init__(
        self,
        api_base_url: Optional[str] = None,
        api_token: Optional[str] = None,
    ):
        """
        Initialize GitHub service.

        Args:
            api_base_url: SDLC Orchestrator API base URL.
                          Falls back to SDLC_API_URL env var or default.
            api_token: Authentication token for API.
                       Falls back to SDLC_API_TOKEN env var.
        """
        self.api_base_url = (
            api_base_url
            or os.environ.get("SDLC_API_URL", "http://localhost:8000/api/v1")
        ).rstrip("/")

        self.api_token = api_token or os.environ.get("SDLC_API_TOKEN")

    def parse_repository(self, repo_input: str) -> ParsedRepository:
        """
        Parse and validate GitHub repository input.

        Accepts formats:
        - owner/repo
        - https://github.com/owner/repo
        - https://github.com/owner/repo.git
        - git@github.com:owner/repo.git

        Args:
            repo_input: Repository identifier in any supported format.

        Returns:
            ParsedRepository with owner, repo, and URLs.

        Raises:
            GitHubRepoFormatError: If the format is invalid.
        """
        repo_input = repo_input.strip()

        # Try simple format first (owner/repo)
        match = GITHUB_REPO_PATTERN.match(repo_input)
        if match:
            owner = match.group("owner")
            repo = match.group("repo")
            return ParsedRepository(
                owner=owner,
                repo=repo,
                full_name=f"{owner}/{repo}",
            )

        # Try URL patterns
        for pattern in GITHUB_URL_PATTERNS:
            match = pattern.match(repo_input)
            if match:
                owner = match.group("owner")
                repo = match.group("repo")
                # Remove .git suffix if present
                if repo.endswith(".git"):
                    repo = repo[:-4]
                return ParsedRepository(
                    owner=owner,
                    repo=repo,
                    full_name=f"{owner}/{repo}",
                )

        raise GitHubRepoFormatError(repo_input)

    def check_app_installed(self, owner: str, repo: str) -> bool:
        """
        Check if SDLC Orchestrator GitHub App is installed on the repository.

        Args:
            owner: Repository owner (user or organization).
            repo: Repository name.

        Returns:
            True if installed and accessible, False otherwise.

        Raises:
            GitHubApiError: If API call fails for unexpected reason.
        """
        if not self.api_token:
            console.print(
                "[yellow]Warning:[/yellow] No API token configured. "
                "Cannot verify GitHub App installation."
            )
            return False

        try:
            headers = {"Authorization": f"Bearer {self.api_token}"}
            response = requests.get(
                f"{self.api_base_url}/github/installations",
                headers=headers,
                timeout=30,
            )

            if response.status_code == 401:
                console.print(
                    "[yellow]Warning:[/yellow] Invalid API token. "
                    "Cannot verify GitHub App installation."
                )
                return False

            if response.status_code != 200:
                raise GitHubApiError(
                    response.status_code,
                    response.json().get("detail", "Unknown error"),
                )

            data = response.json()
            installations = data.get("installations", [])

            # Check if any installation grants access to this repo
            for installation in installations:
                if installation.get("account_login", "").lower() == owner.lower():
                    # Found installation for this owner
                    # Now check if repo is accessible
                    return self._check_repo_accessible(
                        installation.get("id"), owner, repo
                    )

            return False

        except requests.exceptions.ConnectionError:
            console.print(
                f"[yellow]Warning:[/yellow] Cannot connect to API at {self.api_base_url}. "
                "Skipping installation check."
            )
            return False
        except requests.exceptions.Timeout:
            console.print(
                "[yellow]Warning:[/yellow] API request timed out. "
                "Skipping installation check."
            )
            return False

    def _check_repo_accessible(
        self, installation_id: str, owner: str, repo: str
    ) -> bool:
        """Check if a specific repo is accessible via installation."""
        try:
            headers = {"Authorization": f"Bearer {self.api_token}"}
            response = requests.get(
                f"{self.api_base_url}/github/installations/{installation_id}/repositories",
                headers=headers,
                timeout=30,
            )

            if response.status_code != 200:
                return False

            data = response.json()
            repositories = data.get("repositories", [])

            for repository in repositories:
                if (
                    repository.get("owner", "").lower() == owner.lower()
                    and repository.get("name", "").lower() == repo.lower()
                ):
                    return True

            return False

        except Exception:
            return False

    def get_installations(self) -> list[GitHubInstallation]:
        """
        Get list of GitHub App installations for the current user.

        Returns:
            List of GitHubInstallation objects.

        Raises:
            GitHubApiError: If API call fails.
        """
        if not self.api_token:
            return []

        try:
            headers = {"Authorization": f"Bearer {self.api_token}"}
            response = requests.get(
                f"{self.api_base_url}/github/installations",
                headers=headers,
                timeout=30,
            )

            if response.status_code != 200:
                raise GitHubApiError(
                    response.status_code,
                    response.json().get("detail", "Unknown error"),
                )

            data = response.json()
            return [
                GitHubInstallation(
                    id=inst.get("id"),
                    installation_id=inst.get("installation_id"),
                    account_login=inst.get("account_login"),
                    account_type=inst.get("account_type"),
                    status=inst.get("status"),
                )
                for inst in data.get("installations", [])
            ]

        except requests.exceptions.RequestException as e:
            console.print(f"[yellow]Warning:[/yellow] Failed to get installations: {e}")
            return []

    def clone_repository(
        self,
        repo: ParsedRepository,
        target_path: Path,
        shallow: bool = True,
    ) -> Path:
        """
        Clone a GitHub repository to the target path.

        Args:
            repo: Parsed repository information.
            target_path: Target directory for clone.
            shallow: If True, perform shallow clone (--depth 1).

        Returns:
            Path to the cloned repository.

        Raises:
            GitHubCloneError: If clone operation fails.
        """
        # Check if git is available
        if not self._is_git_available():
            raise GitHubCloneError(
                repo.owner,
                repo.repo,
                "Git is not installed or not in PATH",
            )

        # Determine clone directory
        clone_dir = target_path / repo.repo
        if clone_dir.exists():
            # Check if it's already a git repo with same remote
            if self._is_same_remote(clone_dir, repo):
                console.print(
                    f"[dim]Repository already cloned at {clone_dir}[/dim]"
                )
                return clone_dir
            else:
                raise GitHubCloneError(
                    repo.owner,
                    repo.repo,
                    f"Directory {clone_dir} already exists and is not the same repository",
                )

        # Build clone command
        cmd = ["git", "clone"]
        if shallow:
            cmd.extend(["--depth", "1"])
        cmd.extend([repo.clone_url, str(clone_dir)])

        try:
            console.print(f"[dim]Cloning {repo.full_name}...[/dim]")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )

            if result.returncode != 0:
                error_msg = result.stderr.strip() or result.stdout.strip()
                raise GitHubCloneError(repo.owner, repo.repo, error_msg)

            console.print(f"[green]✓[/green] Cloned to {clone_dir}")
            return clone_dir

        except subprocess.TimeoutExpired:
            raise GitHubCloneError(
                repo.owner, repo.repo, "Clone operation timed out"
            )
        except FileNotFoundError:
            raise GitHubCloneError(
                repo.owner, repo.repo, "Git executable not found"
            )

    def _is_git_available(self) -> bool:
        """Check if git is available in PATH."""
        try:
            result = subprocess.run(
                ["git", "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def _is_same_remote(self, repo_path: Path, repo: ParsedRepository) -> bool:
        """Check if existing repo has the same remote URL."""
        try:
            result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode != 0:
                return False

            remote_url = result.stdout.strip()
            # Parse the remote URL and compare
            try:
                parsed = self.parse_repository(remote_url)
                return (
                    parsed.owner.lower() == repo.owner.lower()
                    and parsed.repo.lower() == repo.repo.lower()
                )
            except GitHubRepoFormatError:
                return False

        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def link_repository_to_project(
        self,
        project_id: str,
        installation_id: str,
        repo: ParsedRepository,
    ) -> bool:
        """
        Link a GitHub repository to an SDLC Orchestrator project.

        Args:
            project_id: UUID of the project.
            installation_id: GitHub App installation ID.
            repo: Parsed repository information.

        Returns:
            True if linked successfully.

        Raises:
            GitHubApiError: If API call fails.
        """
        if not self.api_token:
            console.print(
                "[yellow]Warning:[/yellow] No API token. "
                "Cannot link repository to project."
            )
            return False

        try:
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json",
            }
            response = requests.post(
                f"{self.api_base_url}/github/projects/{project_id}/link",
                json={
                    "installation_id": installation_id,
                    "owner": repo.owner,
                    "repo": repo.repo,
                },
                headers=headers,
                timeout=30,
            )

            if response.status_code not in (200, 201):
                error_detail = response.json().get("detail", "Unknown error")
                console.print(
                    f"[yellow]Warning:[/yellow] Failed to link repository: {error_detail}"
                )
                return False

            return True

        except requests.exceptions.RequestException as e:
            console.print(f"[yellow]Warning:[/yellow] Failed to link repository: {e}")
            return False


def get_github_app_install_url() -> str:
    """Get the URL to install the SDLC Orchestrator GitHub App."""
    return "https://github.com/apps/sdlc-orchestrator/installations/new"
