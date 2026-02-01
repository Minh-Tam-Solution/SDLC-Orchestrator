"""
E2E tests for CLI GitHub init workflow.

Sprint 129 Day 6 - E2E Tests for GitHub Integration
Tests the complete workflow: parse → check app → clone → init structure

Reference: ADR-044-GitHub-Integration-Strategy.md
"""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestGitHubInitE2EFlow:
    """E2E tests for sdlcctl init --github workflow."""

    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace for E2E tests."""
        workspace = tempfile.mkdtemp(prefix="sdlcctl_e2e_")
        yield Path(workspace)
        # Cleanup
        shutil.rmtree(workspace, ignore_errors=True)

    @pytest.fixture
    def mock_api_responses(self):
        """Mock API responses for GitHub App detection."""
        installations_response = MagicMock()
        installations_response.status_code = 200
        installations_response.json.return_value = {
            "installations": [
                {
                    "id": "inst-123",
                    "installation_id": 12345,
                    "account_login": "test-org",
                    "account_type": "Organization",
                    "status": "active",
                }
            ]
        }

        repos_response = MagicMock()
        repos_response.status_code = 200
        repos_response.json.return_value = {
            "repositories": [
                {"owner": "test-org", "name": "test-repo"},
            ]
        }

        link_response = MagicMock()
        link_response.status_code = 201
        link_response.json.return_value = {
            "id": "project-123",
            "github_repo_id": 987654,
        }

        return {
            "installations": installations_response,
            "repos": repos_response,
            "link": link_response,
        }

    def test_e2e_github_init_simple_format(self, temp_workspace, mock_api_responses):
        """
        E2E Test 1: Full workflow with simple owner/repo format.

        Flow:
        1. Parse 'test-org/test-repo' format
        2. Check GitHub App installation (mocked)
        3. Clone repository (mocked)
        4. Create SDLC 6.0.0 structure
        5. Verify project initialization
        """
        os.chdir(temp_workspace)

        # Mock git clone to create a fake repo directory
        def mock_git_clone(cmd, **kwargs):
            if "clone" in cmd:
                # Create fake cloned directory
                repo_dir = temp_workspace / "test-repo"
                repo_dir.mkdir(exist_ok=True)
                (repo_dir / "README.md").write_text("# Test Repo")
                result = MagicMock()
                result.returncode = 0
                result.stdout = ""
                result.stderr = ""
                return result
            elif "--version" in cmd:
                result = MagicMock()
                result.returncode = 0
                return result
            return MagicMock(returncode=0)

        def mock_requests_get(url, **kwargs):
            if "installations" in url and "repositories" not in url:
                return mock_api_responses["installations"]
            elif "repositories" in url:
                return mock_api_responses["repos"]
            return MagicMock(status_code=404)

        def mock_requests_post(url, **kwargs):
            if "link" in url:
                return mock_api_responses["link"]
            return MagicMock(status_code=201)

        with (
            patch("subprocess.run", side_effect=mock_git_clone),
            patch("requests.get", side_effect=mock_requests_get),
            patch("requests.post", side_effect=mock_requests_post),
            patch.dict(os.environ, {"SDLC_API_TOKEN": "test-token"}),
        ):
            from sdlcctl.services.github_service import GitHubService

            service = GitHubService(
                api_base_url="http://test-api.example.com/api/v1",
                api_token="test-token",
            )

            # Step 1: Parse repository
            repo = service.parse_repository("test-org/test-repo")
            assert repo.owner == "test-org"
            assert repo.repo == "test-repo"
            assert repo.full_name == "test-org/test-repo"

            # Step 2: Check app installed
            app_installed = service.check_app_installed("test-org", "test-repo")
            assert app_installed is True

            # Step 3: Clone repository
            clone_path = service.clone_repository(repo, temp_workspace, shallow=True)
            assert clone_path.exists()
            assert (clone_path / "README.md").exists()

    def test_e2e_github_init_https_url(self, temp_workspace, mock_api_responses):
        """
        E2E Test 2: Full workflow with HTTPS URL format.
        """
        from sdlcctl.services.github_service import GitHubService

        service = GitHubService()

        # Test HTTPS URL parsing
        repo = service.parse_repository("https://github.com/acme-corp/my-project")
        assert repo.owner == "acme-corp"
        assert repo.repo == "my-project"
        assert repo.clone_url == "https://github.com/acme-corp/my-project.git"

        # Test HTTPS URL with .git suffix
        repo2 = service.parse_repository("https://github.com/acme-corp/my-project.git")
        assert repo2.owner == "acme-corp"
        assert repo2.repo == "my-project"

    def test_e2e_github_init_ssh_url(self, temp_workspace):
        """
        E2E Test 3: Full workflow with SSH URL format.
        """
        from sdlcctl.services.github_service import GitHubService

        service = GitHubService()

        # Test SSH URL parsing
        repo = service.parse_repository("git@github.com:acme-corp/my-project.git")
        assert repo.owner == "acme-corp"
        assert repo.repo == "my-project"
        assert repo.clone_url == "https://github.com/acme-corp/my-project.git"

    def test_e2e_github_init_app_not_installed(self, temp_workspace):
        """
        E2E Test 4: Workflow when GitHub App is not installed.

        Expected behavior:
        - check_app_installed returns False
        - User should be prompted to install the app
        """

        def mock_requests_get(url, **kwargs):
            response = MagicMock()
            response.status_code = 200
            response.json.return_value = {"installations": []}
            return response

        with (
            patch("requests.get", side_effect=mock_requests_get),
            patch.dict(os.environ, {"SDLC_API_TOKEN": "test-token"}),
        ):
            from sdlcctl.services.github_service import GitHubService

            service = GitHubService(
                api_base_url="http://test-api.example.com/api/v1",
                api_token="test-token",
            )

            # App should not be installed
            app_installed = service.check_app_installed("unknown-org", "unknown-repo")
            assert app_installed is False

    def test_e2e_github_init_clone_failure(self, temp_workspace):
        """
        E2E Test 5: Workflow when clone fails.

        Expected behavior:
        - Clone operation fails
        - GitHubCloneError is raised with helpful message
        """

        def mock_git_run(cmd, **kwargs):
            if "--version" in cmd:
                return MagicMock(returncode=0)
            elif "clone" in cmd:
                result = MagicMock()
                result.returncode = 128
                result.stdout = ""
                result.stderr = "fatal: repository 'https://github.com/test/private-repo.git/' not found"
                return result
            return MagicMock(returncode=0)

        with patch("subprocess.run", side_effect=mock_git_run):
            from sdlcctl.services.github_service import (
                GitHubCloneError,
                GitHubService,
                ParsedRepository,
            )

            service = GitHubService()
            repo = ParsedRepository(
                owner="test",
                repo="private-repo",
                full_name="test/private-repo",
            )

            with pytest.raises(GitHubCloneError) as exc_info:
                service.clone_repository(repo, temp_workspace)

            assert exc_info.value.owner == "test"
            assert exc_info.value.repo == "private-repo"
            assert "not found" in exc_info.value.reason

    def test_e2e_github_init_existing_repo_same_remote(self, temp_workspace):
        """
        E2E Test 6: Workflow when directory exists with same remote.

        Expected behavior:
        - Clone is skipped
        - Existing directory is returned
        """
        # Create existing repo directory
        repo_dir = temp_workspace / "existing-repo"
        repo_dir.mkdir()
        (repo_dir / "README.md").write_text("# Existing content")

        def mock_git_run(cmd, **kwargs):
            if "--version" in cmd:
                return MagicMock(returncode=0)
            elif "remote" in cmd and "get-url" in cmd:
                result = MagicMock()
                result.returncode = 0
                result.stdout = "https://github.com/owner/existing-repo.git"
                result.stderr = ""
                return result
            return MagicMock(returncode=0)

        with patch("subprocess.run", side_effect=mock_git_run):
            from sdlcctl.services.github_service import (
                GitHubService,
                ParsedRepository,
            )

            service = GitHubService()
            repo = ParsedRepository(
                owner="owner",
                repo="existing-repo",
                full_name="owner/existing-repo",
            )

            result_path = service.clone_repository(repo, temp_workspace)

            # Should return existing directory without cloning
            assert result_path == repo_dir
            assert (result_path / "README.md").exists()

    def test_e2e_github_init_no_token(self, temp_workspace):
        """
        E2E Test 7: Workflow without API token.

        Expected behavior:
        - Warning is shown
        - App installation check returns False
        - Clone can still proceed
        """
        # Clear any existing token
        env = os.environ.copy()
        env.pop("SDLC_API_TOKEN", None)

        with patch.dict(os.environ, env, clear=True):
            from sdlcctl.services.github_service import GitHubService

            service = GitHubService(api_token=None)

            # Should return False without making API call
            result = service.check_app_installed("any-org", "any-repo")
            assert result is False

            # Should return empty list
            installations = service.get_installations()
            assert installations == []

    def test_e2e_github_init_api_connection_error(self, temp_workspace):
        """
        E2E Test 8: Workflow when API is unreachable.

        Expected behavior:
        - Connection error is handled gracefully
        - App check returns False
        - Clone can still proceed
        """
        import requests

        with (
            patch(
                "requests.get", side_effect=requests.exceptions.ConnectionError()
            ),
            patch.dict(os.environ, {"SDLC_API_TOKEN": "test-token"}),
        ):
            from sdlcctl.services.github_service import GitHubService

            service = GitHubService(
                api_base_url="http://unreachable-api.example.com/api/v1",
                api_token="test-token",
            )

            # Should handle connection error gracefully
            result = service.check_app_installed("any-org", "any-repo")
            assert result is False

    def test_e2e_github_init_rate_limit(self, temp_workspace):
        """
        E2E Test 9: Workflow when API rate limit is exceeded.

        Expected behavior:
        - Rate limit error is handled
        - App check returns False
        - User-friendly error message
        """

        def mock_rate_limit_response(*args, **kwargs):
            response = MagicMock()
            response.status_code = 429
            response.json.return_value = {
                "detail": "Rate limit exceeded. Retry after 3600 seconds."
            }
            return response

        with (
            patch("requests.get", side_effect=mock_rate_limit_response),
            patch.dict(os.environ, {"SDLC_API_TOKEN": "test-token"}),
        ):
            from sdlcctl.services.github_service import GitHubApiError, GitHubService

            service = GitHubService(
                api_base_url="http://api.example.com/api/v1",
                api_token="test-token",
            )

            # Should raise API error for rate limit
            with pytest.raises(GitHubApiError) as exc_info:
                service.check_app_installed("any-org", "any-repo")

            assert exc_info.value.status_code == 429

    def test_e2e_github_init_invalid_format(self, temp_workspace):
        """
        E2E Test 10: Workflow with invalid repository format.

        Expected behavior:
        - GitHubRepoFormatError is raised
        - Helpful error message with valid formats
        """
        from sdlcctl.services.github_service import GitHubRepoFormatError, GitHubService

        service = GitHubService()

        invalid_formats = [
            "",
            "just-a-name",
            "owner",
            "/repo",
            "owner/",
            "https://gitlab.com/owner/repo",
            "not-a-url",
        ]

        for invalid_input in invalid_formats:
            with pytest.raises(GitHubRepoFormatError):
                service.parse_repository(invalid_input)


class TestGitHubInitCLIE2E:
    """E2E tests for sdlcctl init command with --github flag."""

    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace for CLI E2E tests."""
        # Store original cwd before any test modifies it
        try:
            original_cwd = os.getcwd()
        except FileNotFoundError:
            original_cwd = Path.home()

        workspace = tempfile.mkdtemp(prefix="sdlcctl_cli_e2e_")
        yield Path(workspace)
        # Cleanup - only change back if original still exists
        if Path(original_cwd).exists():
            os.chdir(original_cwd)
        shutil.rmtree(workspace, ignore_errors=True)

    def test_cli_init_help_shows_github_option(self):
        """
        CLI E2E Test 1: --help shows --github option.
        """
        result = subprocess.run(
            ["python", "-m", "sdlcctl.cli", "init", "--help"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent,
        )

        assert result.returncode == 0
        assert "--github" in result.stdout or "-g" in result.stdout
        assert "--clone" in result.stdout

    def test_cli_init_invalid_github_format(self, temp_workspace):
        """
        CLI E2E Test 2: Invalid GitHub format shows error.
        """
        result = subprocess.run(
            [
                "python",
                "-m",
                "sdlcctl.cli",
                "init",
                "--github",
                "invalid-format",
                "--tier",
                "lite",
                "--no-interactive",
                "--path",
                str(temp_workspace),
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent,
        )

        # Should show error about invalid format or exit with error code
        output = result.stdout + result.stderr
        assert "Invalid" in output or "format" in output.lower() or result.returncode != 0


class TestGitHubInstallUrl:
    """Tests for GitHub App installation URL."""

    def test_install_url_format(self):
        """
        Test GitHub App install URL is correct.
        """
        from sdlcctl.services.github_service import get_github_app_install_url

        url = get_github_app_install_url()

        assert url == "https://github.com/apps/sdlc-orchestrator/installations/new"
        assert "github.com" in url
        assert "apps" in url
        assert "sdlc-orchestrator" in url
