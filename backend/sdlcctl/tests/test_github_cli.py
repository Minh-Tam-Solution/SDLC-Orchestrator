"""
Unit tests for CLI GitHub integration.

Sprint 129 Day 5 - CLI GitHub Integration Tests
Tests 8 scenarios for GitHub CLI functionality.

Reference: ADR-044-GitHub-Integration-Strategy.md
"""

import subprocess
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from sdlcctl.services.github_service import (
    GitHubService,
    GitHubRepoFormatError,
    GitHubAppNotInstalledError,
    GitHubCloneError,
    GitHubApiError,
    ParsedRepository,
    GITHUB_REPO_PATTERN,
    get_github_app_install_url,
)


class TestRepositoryParsing:
    """Test 1-3: Repository format parsing and validation."""

    def test_1_parse_owner_repo_format(self):
        """Test 1: Parse simple owner/repo format."""
        service = GitHubService()

        # Valid formats
        repo = service.parse_repository("owner/repo")
        assert repo.owner == "owner"
        assert repo.repo == "repo"
        assert repo.full_name == "owner/repo"
        assert repo.clone_url == "https://github.com/owner/repo.git"
        assert repo.html_url == "https://github.com/owner/repo"

        # Organization names with hyphens
        repo2 = service.parse_repository("my-org/my-project")
        assert repo2.owner == "my-org"
        assert repo2.repo == "my-project"
        assert repo2.full_name == "my-org/my-project"

        # Numbers in name
        repo3 = service.parse_repository("user123/repo456")
        assert repo3.owner == "user123"
        assert repo3.repo == "repo456"

    def test_2_parse_github_url_formats(self):
        """Test 2: Parse various GitHub URL formats."""
        service = GitHubService()

        # HTTPS URL
        repo1 = service.parse_repository("https://github.com/owner/repo")
        assert repo1.owner == "owner"
        assert repo1.repo == "repo"
        assert repo1.full_name == "owner/repo"

        # HTTPS URL with .git
        repo2 = service.parse_repository("https://github.com/owner/repo.git")
        assert repo2.owner == "owner"
        assert repo2.repo == "repo"

        # HTTP URL (should upgrade to HTTPS in clone_url)
        repo3 = service.parse_repository("http://github.com/acme-corp/project")
        assert repo3.owner == "acme-corp"
        assert repo3.repo == "project"
        assert repo3.clone_url == "https://github.com/acme-corp/project.git"

        # SSH URL
        repo4 = service.parse_repository("git@github.com:owner/repo.git")
        assert repo4.owner == "owner"
        assert repo4.repo == "repo"

        # Trailing slash
        repo5 = service.parse_repository("https://github.com/owner/repo/")
        assert repo5.owner == "owner"
        assert repo5.repo == "repo"

    def test_3_invalid_repo_format_raises_error(self):
        """Test 3: Invalid repository formats raise GitHubRepoFormatError."""
        service = GitHubService()

        invalid_inputs = [
            "",  # Empty string
            "just-a-name",  # No owner
            "owner",  # No repo
            "/repo",  # Missing owner
            "owner/",  # Missing repo
            "https://gitlab.com/owner/repo",  # Wrong host
            "not-a-url",  # Invalid format
            "owner/repo/extra",  # Too many parts in simple format
            "-invalid/repo",  # Owner starts with hyphen
            "owner/a" * 100,  # Repo name too long
        ]

        for invalid_input in invalid_inputs:
            with pytest.raises(GitHubRepoFormatError):
                service.parse_repository(invalid_input)


class TestGitHubAppInstallation:
    """Test 4-5: GitHub App installation detection."""

    def test_4_check_app_installed_with_valid_token(self):
        """Test 4: Check app installation with valid API token."""
        service = GitHubService(
            api_base_url="http://test-api.example.com/api/v1",
            api_token="test-token-123",
        )

        # Mock successful API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "installations": [
                {
                    "id": "inst-123",
                    "installation_id": 12345,
                    "account_login": "acme-corp",
                    "account_type": "Organization",
                    "status": "active",
                }
            ]
        }

        mock_repo_response = MagicMock()
        mock_repo_response.status_code = 200
        mock_repo_response.json.return_value = {
            "repositories": [
                {"owner": "acme-corp", "name": "my-project"},
                {"owner": "acme-corp", "name": "other-project"},
            ]
        }

        with patch("requests.get") as mock_get:
            # First call for installations, second for repositories
            mock_get.side_effect = [mock_response, mock_repo_response]

            result = service.check_app_installed("acme-corp", "my-project")
            assert result is True

    def test_5_check_app_not_installed(self):
        """Test 5: Returns False when app is not installed."""
        service = GitHubService(
            api_base_url="http://test-api.example.com/api/v1",
            api_token="test-token-123",
        )

        # Mock response with no installations
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"installations": []}

        with patch("requests.get", return_value=mock_response):
            result = service.check_app_installed("unknown-org", "repo")
            assert result is False

        # Mock response with different org
        mock_response2 = MagicMock()
        mock_response2.status_code = 200
        mock_response2.json.return_value = {
            "installations": [
                {
                    "id": "inst-123",
                    "installation_id": 12345,
                    "account_login": "other-org",
                    "account_type": "Organization",
                    "status": "active",
                }
            ]
        }

        with patch("requests.get", return_value=mock_response2):
            result = service.check_app_installed("acme-corp", "repo")
            assert result is False


class TestRepositoryCloning:
    """Test 6-7: Repository cloning functionality."""

    def test_6_clone_repository_success(self):
        """Test 6: Successfully clone a repository."""
        service = GitHubService()

        with tempfile.TemporaryDirectory() as tmpdir:
            target_path = Path(tmpdir)
            repo = ParsedRepository(
                owner="owner",
                repo="test-repo",
                full_name="owner/test-repo",
            )

            # Mock git available check and successful clone
            mock_git_version = MagicMock()
            mock_git_version.returncode = 0

            mock_clone_result = MagicMock()
            mock_clone_result.returncode = 0
            mock_clone_result.stdout = ""
            mock_clone_result.stderr = ""

            clone_cmd_captured = []

            def mock_run_side_effect(cmd, **kwargs):
                if cmd[1] == "--version":
                    return mock_git_version
                clone_cmd_captured.append(cmd)
                return mock_clone_result

            with patch("subprocess.run", side_effect=mock_run_side_effect):
                result_path = service.clone_repository(repo, target_path, shallow=True)

                # Verify clone command was called correctly
                assert len(clone_cmd_captured) == 1
                clone_cmd = clone_cmd_captured[0]
                assert "git" in clone_cmd
                assert "clone" in clone_cmd
                assert "--depth" in clone_cmd
                assert "1" in clone_cmd
                assert repo.clone_url in clone_cmd

                assert result_path == target_path / "test-repo"

    def test_7_clone_repository_failure(self):
        """Test 7: Clone failure raises GitHubCloneError."""
        service = GitHubService()

        with tempfile.TemporaryDirectory() as tmpdir:
            target_path = Path(tmpdir)
            repo = ParsedRepository(
                owner="owner",
                repo="private-repo",
                full_name="owner/private-repo",
            )

            # Mock git available check to return True
            # Then mock failed git clone
            mock_git_version = MagicMock()
            mock_git_version.returncode = 0

            mock_clone_result = MagicMock()
            mock_clone_result.returncode = 128
            mock_clone_result.stdout = ""
            mock_clone_result.stderr = "fatal: repository not found"

            def mock_run_side_effect(cmd, **kwargs):
                if cmd[1] == "--version":
                    return mock_git_version
                return mock_clone_result

            with patch("subprocess.run", side_effect=mock_run_side_effect):
                with pytest.raises(GitHubCloneError) as exc_info:
                    service.clone_repository(repo, target_path)

                assert exc_info.value.owner == "owner"
                assert exc_info.value.repo == "private-repo"
                assert "not found" in exc_info.value.reason


class TestGetInstallUrl:
    """Test 8: GitHub App installation URL."""

    def test_8_get_github_app_install_url(self):
        """Test 8: Get correct GitHub App installation URL."""
        url = get_github_app_install_url()

        assert "github.com" in url
        assert "apps" in url
        assert "sdlc-orchestrator" in url
        assert "installations/new" in url
        assert url == "https://github.com/apps/sdlc-orchestrator/installations/new"


class TestGitHubServiceEdgeCases:
    """Additional edge case tests for robustness."""

    def test_service_without_token(self):
        """Test service behavior without API token."""
        service = GitHubService(api_token=None)

        # Should return False (can't verify without token)
        result = service.check_app_installed("owner", "repo")
        assert result is False

        # Should return empty list
        installations = service.get_installations()
        assert installations == []

    def test_service_connection_error_handling(self):
        """Test service handles connection errors gracefully."""
        import requests

        service = GitHubService(
            api_base_url="http://nonexistent.example.com/api/v1",
            api_token="test-token",
        )

        with patch("requests.get", side_effect=requests.exceptions.ConnectionError):
            result = service.check_app_installed("owner", "repo")
            assert result is False

    def test_service_timeout_handling(self):
        """Test service handles timeout errors gracefully."""
        import requests

        service = GitHubService(
            api_base_url="http://slow-api.example.com/api/v1",
            api_token="test-token",
        )

        with patch("requests.get", side_effect=requests.exceptions.Timeout):
            result = service.check_app_installed("owner", "repo")
            assert result is False

    def test_git_not_available(self):
        """Test clone fails gracefully when git is not available."""
        service = GitHubService()

        with tempfile.TemporaryDirectory() as tmpdir:
            repo = ParsedRepository(
                owner="owner",
                repo="repo",
                full_name="owner/repo",
            )

            # Mock git not being available
            with patch.object(service, "_is_git_available", return_value=False):
                with pytest.raises(GitHubCloneError) as exc_info:
                    service.clone_repository(repo, Path(tmpdir))

                assert "not installed" in exc_info.value.reason.lower()

    def test_existing_repo_same_remote(self):
        """Test existing directory with same remote skips clone."""
        service = GitHubService()

        with tempfile.TemporaryDirectory() as tmpdir:
            target_path = Path(tmpdir)
            repo = ParsedRepository(
                owner="owner",
                repo="existing-repo",
                full_name="owner/existing-repo",
            )

            # Create existing directory
            repo_dir = target_path / "existing-repo"
            repo_dir.mkdir()
            (repo_dir / "README.md").write_text("# Existing content")

            # Mock _is_same_remote to return True
            with patch.object(service, "_is_same_remote", return_value=True):
                result = service.clone_repository(repo, target_path)
                assert result == repo_dir

    def test_existing_repo_different_remote(self):
        """Test existing directory with different remote raises error."""
        service = GitHubService()

        with tempfile.TemporaryDirectory() as tmpdir:
            target_path = Path(tmpdir)
            repo = ParsedRepository(
                owner="owner",
                repo="conflicting-repo",
                full_name="owner/conflicting-repo",
            )

            # Create existing directory
            repo_dir = target_path / "conflicting-repo"
            repo_dir.mkdir()
            (repo_dir / "README.md").write_text("# Different content")

            # Mock _is_same_remote to return False
            with patch.object(service, "_is_same_remote", return_value=False):
                with pytest.raises(GitHubCloneError) as exc_info:
                    service.clone_repository(repo, target_path)

                assert "already exists" in exc_info.value.reason
                assert "not the same" in exc_info.value.reason


class TestParsedRepository:
    """Tests for ParsedRepository dataclass."""

    def test_parsed_repository_properties(self):
        """Test ParsedRepository computed properties."""
        repo = ParsedRepository(
            owner="acme-corp",
            repo="sdlc-orchestrator",
            full_name="acme-corp/sdlc-orchestrator",
        )

        assert repo.clone_url == "https://github.com/acme-corp/sdlc-orchestrator.git"
        assert repo.html_url == "https://github.com/acme-corp/sdlc-orchestrator"

    def test_parsed_repository_with_special_chars(self):
        """Test repository names with special characters."""
        repo = ParsedRepository(
            owner="my-org",
            repo="my_project.v2",
            full_name="my-org/my_project.v2",
        )

        assert repo.clone_url == "https://github.com/my-org/my_project.v2.git"
        assert repo.html_url == "https://github.com/my-org/my_project.v2"
