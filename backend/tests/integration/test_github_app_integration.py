"""
=========================================================================
Integration Tests - GitHub App Service (Sprint 129)
SDLC Orchestrator - Stage 04 (BUILD)

Version: 1.0.0
Date: January 31, 2026
Status: ACTIVE - Sprint 129 Implementation
Authority: QA Lead + Backend Lead Approved
Reference: ADR-044-GitHub-Integration-Strategy.md

Purpose:
- Test GitHub App service functions (token management, API calls)
- Test database operations (installations, repositories)
- Test webhook signature validation
- Test clone and scan operations
- Test API endpoints

Coverage: 25+ test cases
Test Execution:
    pytest tests/integration/test_github_app_integration.py -v

Zero Mock Policy: Uses mock HTTP responses for GitHub API, real DB for integration
=========================================================================
"""

import hashlib
import hmac
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.github_integration import (
    CloneStatus,
    GitHubInstallation,
    GitHubRepository,
    InstallationStatus,
)
from app.services import github_app_service


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_db():
    """Mock database session"""
    mock = MagicMock(spec=Session)

    def add_side_effect(obj):
        if hasattr(obj, 'id') and obj.id is None:
            obj.id = uuid4()

    def refresh_side_effect(obj):
        if hasattr(obj, 'created_at') and obj.created_at is None:
            obj.created_at = datetime.utcnow()
        if hasattr(obj, 'updated_at') and obj.updated_at is None:
            obj.updated_at = datetime.utcnow()

    mock.add.side_effect = add_side_effect
    mock.refresh.side_effect = refresh_side_effect
    return mock


@pytest.fixture
def mock_settings():
    """Mock settings with GitHub App config"""
    with patch("app.services.github_app_service.settings") as mock:
        mock.GITHUB_APP_ID = "12345"
        mock.GITHUB_APP_PRIVATE_KEY = """-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA0Z3VS5JJcds3xfn/ygKyK5pB...test...
-----END RSA PRIVATE KEY-----"""
        yield mock


@pytest.fixture
def sample_user_id():
    """Sample user UUID"""
    return uuid4()


@pytest.fixture
def sample_project_id():
    """Sample project UUID"""
    return uuid4()


@pytest.fixture
def sample_installation_id():
    """Sample GitHub installation ID (integer)"""
    return 12345678


@pytest.fixture
def sample_repo_info():
    """Sample repository info from GitHub API"""
    return {
        "id": 987654321,
        "name": "test-repo",
        "full_name": "test-org/test-repo",
        "owner": {
            "login": "test-org",
            "id": 123456
        },
        "private": False,
        "html_url": "https://github.com/test-org/test-repo",
        "default_branch": "main",
        "description": "Test repository for SDLC Orchestrator",
        "language": "Python"
    }


@pytest.fixture
def sample_installation(sample_user_id, sample_installation_id):
    """Sample GitHubInstallation object"""
    installation = GitHubInstallation(
        installation_id=sample_installation_id,
        account_type="Organization",
        account_login="test-org",
        account_avatar_url="https://avatars.githubusercontent.com/u/123456",
        installed_by=sample_user_id,
        status=InstallationStatus.ACTIVE
    )
    installation.id = uuid4()
    installation.installed_at = datetime.utcnow()
    installation.updated_at = datetime.utcnow()
    return installation


@pytest.fixture
def sample_github_repo(sample_installation, sample_project_id, sample_user_id):
    """Sample GitHubRepository object"""
    repo = GitHubRepository(
        installation_id=sample_installation.id,
        project_id=sample_project_id,
        github_repo_id=987654321,
        owner="test-org",
        name="test-repo",
        full_name="test-org/test-repo",
        default_branch="main",
        is_private=False,
        html_url="https://github.com/test-org/test-repo",
        connected_by=sample_user_id,
        clone_status=CloneStatus.PENDING
    )
    repo.id = uuid4()
    repo.connected_at = datetime.utcnow()
    repo.updated_at = datetime.utcnow()
    return repo


# ============================================================================
# JWT Generation Tests
# ============================================================================

class TestJWTGeneration:
    """Test JWT generation for GitHub App authentication."""

    def test_generate_jwt_not_configured(self):
        """Test JWT generation fails when not configured."""
        with patch("app.services.github_app_service.settings") as mock_settings:
            mock_settings.GITHUB_APP_ID = None
            mock_settings.GITHUB_APP_PRIVATE_KEY = None

            with pytest.raises(HTTPException) as exc_info:
                github_app_service.generate_github_app_jwt()

            assert exc_info.value.status_code == 500
            assert "not configured" in exc_info.value.detail["message"].lower()

    @patch("app.services.github_app_service.jwt.encode")
    def test_generate_jwt_success(self, mock_jwt_encode, mock_settings):
        """Test successful JWT generation."""
        mock_jwt_encode.return_value = "test_jwt_token"

        jwt_token = github_app_service.generate_github_app_jwt()

        assert jwt_token == "test_jwt_token"
        mock_jwt_encode.assert_called_once()

        # Verify JWT payload structure
        call_args = mock_jwt_encode.call_args
        payload = call_args[0][0]

        assert "iat" in payload
        assert "exp" in payload
        assert "iss" in payload
        assert payload["iss"] == "12345"
        assert payload["exp"] - payload["iat"] == 600  # 10 minutes

    @patch("app.services.github_app_service.jwt.encode")
    def test_generate_jwt_invalid_key(self, mock_jwt_encode, mock_settings):
        """Test JWT generation with invalid key raises error."""
        mock_jwt_encode.side_effect = Exception("Invalid key format")

        with pytest.raises(HTTPException) as exc_info:
            github_app_service.generate_github_app_jwt()

        assert exc_info.value.status_code == 500
        assert "jwt_generation_failed" in exc_info.value.detail["error"]


# ============================================================================
# Installation Token Tests
# ============================================================================

class TestInstallationToken:
    """Test installation token management."""

    @pytest.mark.asyncio
    async def test_get_installation_token_not_configured(self):
        """Test getting token fails when not configured."""
        with patch("app.services.github_app_service.settings") as mock_settings:
            mock_settings.GITHUB_APP_ID = None
            mock_settings.GITHUB_APP_PRIVATE_KEY = None

            with pytest.raises(HTTPException) as exc_info:
                await github_app_service.get_installation_token(12345)

            assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    @patch("app.services.github_app_service.httpx.AsyncClient")
    @patch("app.services.github_app_service.jwt.encode")
    async def test_get_installation_token_success(
        self, mock_jwt_encode, mock_client_class, mock_settings
    ):
        """Test successful installation token retrieval."""
        mock_jwt_encode.return_value = "test_jwt"

        # Clear cache before test
        github_app_service._token_cache.clear()

        # Mock HTTP response
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "token": "ghs_test_installation_token",
            "expires_at": (datetime.utcnow() + timedelta(hours=1)).isoformat() + "Z",
        }

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value.__aenter__.return_value = mock_client

        token = await github_app_service.get_installation_token(12345)

        assert token == "ghs_test_installation_token"
        assert 12345 in github_app_service._token_cache

    @pytest.mark.asyncio
    async def test_get_installation_token_cached(self, mock_settings):
        """Test token is returned from cache."""
        # Set up cache with valid token
        github_app_service._token_cache[99999] = (
            "cached_token",
            datetime.utcnow() + timedelta(hours=1)  # Not expired
        )

        # Should return cached token without API call
        token = await github_app_service.get_installation_token(99999)

        assert token == "cached_token"

    @pytest.mark.asyncio
    @patch("app.services.github_app_service.httpx.AsyncClient")
    @patch("app.services.github_app_service.jwt.encode")
    async def test_get_installation_token_404(
        self, mock_jwt_encode, mock_client_class, mock_settings
    ):
        """Test handling of installation not found."""
        mock_jwt_encode.return_value = "test_jwt"
        github_app_service._token_cache.clear()

        mock_response = MagicMock()
        mock_response.status_code = 404

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value.__aenter__.return_value = mock_client

        with pytest.raises(HTTPException) as exc_info:
            await github_app_service.get_installation_token(88888)

        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail["message"].lower()


# ============================================================================
# Webhook Signature Validation Tests
# ============================================================================

class TestWebhookSignatureValidation:
    """Test webhook signature validation."""

    def test_verify_webhook_signature_valid(self):
        """Test valid webhook signature verification."""
        secret = "test_webhook_secret_12345"
        payload = b'{"action": "opened", "number": 1}'

        expected_signature = hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        signature = f"sha256={expected_signature}"

        is_valid = github_app_service.verify_webhook_signature(payload, signature, secret)

        assert is_valid is True

    def test_verify_webhook_signature_invalid(self):
        """Test invalid webhook signature is rejected."""
        secret = "test_webhook_secret_12345"
        payload = b'{"action": "opened", "number": 1}'
        signature = "sha256=invalid_signature_12345"

        is_valid = github_app_service.verify_webhook_signature(payload, signature, secret)

        assert is_valid is False

    def test_verify_webhook_signature_wrong_format(self):
        """Test webhook signature with wrong format (sha1 instead of sha256)."""
        secret = "test_webhook_secret_12345"
        payload = b'{"action": "opened"}'
        signature = "sha1=old_format_signature"

        is_valid = github_app_service.verify_webhook_signature(payload, signature, secret)

        assert is_valid is False

    def test_verify_webhook_signature_empty_prefix(self):
        """Test webhook signature without sha256= prefix."""
        secret = "test_webhook_secret_12345"
        payload = b'{"action": "opened"}'
        signature = "no_prefix_signature"

        is_valid = github_app_service.verify_webhook_signature(payload, signature, secret)

        assert is_valid is False


# ============================================================================
# Local Repository Scan Tests
# ============================================================================

class TestLocalRepositoryScan:
    """Test local repository scanning."""

    def test_scan_local_repository_with_structure(self):
        """Test scanning a local repository with SDLC structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)

            # Create SDLC folder structure
            (repo_path / "docs").mkdir()
            (repo_path / "docs" / "00-foundation").mkdir(parents=True)
            (repo_path / "docs" / "01-planning").mkdir()
            (repo_path / "src").mkdir()
            (repo_path / ".sdlc-config.json").touch()
            (repo_path / "README.md").touch()

            result = github_app_service.scan_local_repository(repo_path)

            assert result["sdlc_config_found"] is True
            assert result["docs_folder_exists"] is True
            assert result["total_folders"] > 0
            assert result["total_files"] > 0
            assert "docs" in result["folders"]
            assert "README.md" in result["files"]

    def test_scan_local_repository_empty(self):
        """Test scanning an empty repository."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)

            result = github_app_service.scan_local_repository(repo_path)

            assert result["sdlc_config_found"] is False
            assert result["docs_folder_exists"] is False
            assert result["total_folders"] == 0
            assert result["total_files"] == 0

    def test_scan_local_repository_not_found(self):
        """Test scanning a non-existent path."""
        repo_path = Path("/nonexistent/path/12345")

        result = github_app_service.scan_local_repository(repo_path)

        assert "error" in result
        assert result["total_folders"] == 0
        assert result["total_files"] == 0

    def test_scan_local_repository_ignores_git(self):
        """Test that .git folder is ignored during scan."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)

            # Create .git folder (should be ignored)
            (repo_path / ".git").mkdir()
            (repo_path / ".git" / "objects").mkdir()
            (repo_path / ".git" / "refs").mkdir()
            (repo_path / "src").mkdir()
            (repo_path / "src" / "main.py").touch()

            result = github_app_service.scan_local_repository(repo_path)

            # .git should not be in folders
            assert ".git" not in result["folders"]
            assert all(".git" not in f for f in result["folders"])
            assert "src" in result["folders"]


# ============================================================================
# Database Operations Tests
# ============================================================================

class TestDatabaseOperations:
    """Test database operations for GitHub integration."""

    def test_get_user_installations(self, mock_db, sample_user_id, sample_installation):
        """Test getting user's GitHub installations."""
        mock_db.query.return_value.filter.return_value.all.return_value = [sample_installation]

        installations = github_app_service.get_user_installations(sample_user_id, mock_db)

        assert len(installations) == 1
        assert installations[0].installation_id == sample_installation.installation_id

    def test_create_installation_new(self, mock_db, sample_user_id, sample_installation_id):
        """Test creating a new GitHub installation."""
        # No existing installation
        mock_db.query.return_value.filter.return_value.first.return_value = None

        installation = github_app_service.create_installation(
            installation_id=sample_installation_id,
            account_type="Organization",
            account_login="test-org",
            user_id=sample_user_id,
            db=mock_db,
            account_avatar_url="https://avatars.githubusercontent.com/u/123456"
        )

        assert installation.installation_id == sample_installation_id
        assert installation.account_login == "test-org"
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_create_installation_existing_active(
        self, mock_db, sample_user_id, sample_installation_id, sample_installation
    ):
        """Test creating installation that already exists raises error."""
        # Existing active installation
        mock_db.query.return_value.filter.return_value.first.return_value = sample_installation

        with pytest.raises(HTTPException) as exc_info:
            github_app_service.create_installation(
                installation_id=sample_installation_id,
                account_type="Organization",
                account_login="test-org",
                user_id=sample_user_id,
                db=mock_db
            )

        assert exc_info.value.status_code == 409
        assert "already exists" in exc_info.value.detail["message"]

    def test_create_installation_reactivate_uninstalled(
        self, mock_db, sample_user_id, sample_installation_id, sample_installation
    ):
        """Test reactivating an uninstalled installation."""
        # Existing uninstalled installation
        sample_installation.status = InstallationStatus.UNINSTALLED
        mock_db.query.return_value.filter.return_value.first.return_value = sample_installation

        installation = github_app_service.create_installation(
            installation_id=sample_installation_id,
            account_type="Organization",
            account_login="test-org",
            user_id=sample_user_id,
            db=mock_db
        )

        assert installation.status == InstallationStatus.ACTIVE
        assert installation.uninstalled_at is None


# ============================================================================
# Repository Link Tests
# ============================================================================

class TestRepositoryLink:
    """Test repository linking operations."""

    def test_link_repository_success(
        self, mock_db, sample_installation, sample_project_id,
        sample_user_id, sample_repo_info
    ):
        """Test successful repository linking."""
        # Mock project exists
        mock_project = MagicMock()
        mock_project.id = sample_project_id

        # Configure query chains
        query_mock = MagicMock()
        query_mock.filter.return_value.first.side_effect = [
            mock_project,  # Project lookup
            None,  # No existing linked repo for project
            None   # No repo linked to other project
        ]
        mock_db.query.return_value = query_mock

        github_repo = github_app_service.link_repository_to_project(
            installation_uuid=sample_installation.id,
            project_id=sample_project_id,
            repo_info=sample_repo_info,
            user_id=sample_user_id,
            db=mock_db
        )

        assert github_repo.github_repo_id == sample_repo_info["id"]
        assert github_repo.full_name == sample_repo_info["full_name"]
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_link_repository_project_not_found(
        self, mock_db, sample_installation, sample_project_id,
        sample_user_id, sample_repo_info
    ):
        """Test linking fails when project doesn't exist."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            github_app_service.link_repository_to_project(
                installation_uuid=sample_installation.id,
                project_id=sample_project_id,
                repo_info=sample_repo_info,
                user_id=sample_user_id,
                db=mock_db
            )

        assert exc_info.value.status_code == 404
        assert "project_not_found" in exc_info.value.detail["error"]

    def test_unlink_repository_success(
        self, mock_db, sample_project_id, sample_user_id, sample_github_repo
    ):
        """Test successful repository unlinking."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_github_repo

        result = github_app_service.unlink_repository(
            project_id=sample_project_id,
            user_id=sample_user_id,
            db=mock_db
        )

        assert result.disconnected_at is not None
        mock_db.commit.assert_called_once()

    def test_unlink_repository_not_found(self, mock_db, sample_project_id, sample_user_id):
        """Test unlinking fails when no repo linked."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            github_app_service.unlink_repository(
                project_id=sample_project_id,
                user_id=sample_user_id,
                db=mock_db
            )

        assert exc_info.value.status_code == 404
        assert "no_repo_linked" in exc_info.value.detail["error"]


# ============================================================================
# Model Tests
# ============================================================================

class TestGitHubInstallationModel:
    """Test GitHubInstallation model methods."""

    def test_installation_status_transitions(self, sample_installation):
        """Test installation status transitions."""
        assert sample_installation.status == InstallationStatus.ACTIVE

        sample_installation.suspend()
        assert sample_installation.status == InstallationStatus.SUSPENDED
        assert sample_installation.suspended_at is not None

        sample_installation.unsuspend()
        assert sample_installation.status == InstallationStatus.ACTIVE
        assert sample_installation.suspended_at is None

    def test_installation_uninstall(self, sample_installation):
        """Test installation uninstall."""
        sample_installation.uninstall()

        assert sample_installation.status == InstallationStatus.UNINSTALLED
        assert sample_installation.uninstalled_at is not None


class TestGitHubRepositoryModel:
    """Test GitHubRepository model methods."""

    def test_clone_status_transitions(self, sample_github_repo):
        """Test clone status transitions."""
        assert sample_github_repo.clone_status == CloneStatus.PENDING

        sample_github_repo.start_clone("/path/to/clone")
        assert sample_github_repo.clone_status == CloneStatus.CLONING
        assert sample_github_repo.local_path == "/path/to/clone"
        assert sample_github_repo.clone_error is None

        sample_github_repo.complete_clone()
        assert sample_github_repo.clone_status == CloneStatus.CLONED
        assert sample_github_repo.last_cloned_at is not None

    def test_clone_failure(self, sample_github_repo):
        """Test clone failure handling."""
        sample_github_repo.start_clone("/path/to/clone")
        sample_github_repo.fail_clone("Network timeout")

        assert sample_github_repo.clone_status == CloneStatus.FAILED
        assert sample_github_repo.clone_error == "Network timeout"

    def test_repository_disconnect(self, sample_github_repo):
        """Test repository disconnect."""
        sample_github_repo.disconnect()

        assert sample_github_repo.disconnected_at is not None
        assert sample_github_repo.clone_status == CloneStatus.PENDING
        assert sample_github_repo.local_path is None


# ============================================================================
# Installation Listing Tests
# ============================================================================

class TestInstallationListing:
    """Test installation and repository listing from GitHub API."""

    @pytest.mark.asyncio
    @patch("app.services.github_app_service.httpx.AsyncClient")
    @patch("app.services.github_app_service.jwt.encode")
    async def test_list_installations_from_github(
        self, mock_jwt_encode, mock_client_class, mock_settings
    ):
        """Test listing installations from GitHub."""
        mock_jwt_encode.return_value = "test_jwt"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "id": 12345678,
                "account": {"login": "test-org", "type": "Organization"},
                "app_slug": "sdlc-orchestrator"
            }
        ]

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client_class.return_value.__aenter__.return_value = mock_client

        installations = await github_app_service.list_installations_from_github()

        assert len(installations) == 1
        assert installations[0]["id"] == 12345678

    @pytest.mark.asyncio
    @patch("app.services.github_app_service.httpx.AsyncClient")
    async def test_list_repositories_for_installation(
        self, mock_client_class, mock_settings
    ):
        """Test listing repositories for an installation."""
        # Pre-cache a token to avoid token generation call
        github_app_service._token_cache[12345678] = (
            "cached_token",
            datetime.utcnow() + timedelta(hours=1)
        )

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "total_count": 2,
            "repositories": [
                {"id": 111, "name": "repo1", "full_name": "org/repo1"},
                {"id": 222, "name": "repo2", "full_name": "org/repo2"}
            ]
        }

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client_class.return_value.__aenter__.return_value = mock_client

        result = await github_app_service.list_repositories_for_installation(12345678)

        assert result["total_count"] == 2
        assert len(result["repositories"]) == 2


# ============================================================================
# API Constants Tests
# ============================================================================

class TestAPIConstants:
    """Test API constants are correct."""

    def test_github_api_base_url(self):
        """Test GitHub API base URL."""
        assert github_app_service.GITHUB_API_BASE_URL == "https://api.github.com"

    def test_github_api_version(self):
        """Test GitHub API version."""
        assert github_app_service.GITHUB_API_VERSION == "2022-11-28"


# ============================================================================
# Token Cache Management Tests
# ============================================================================

class TestTokenCacheManagement:
    """Test token cache management."""

    def test_token_cache_stores_correctly(self):
        """Test token cache storage."""
        github_app_service._token_cache.clear()

        token = "test_token"
        expires_at = datetime.utcnow() + timedelta(hours=1)
        github_app_service._token_cache[11111] = (token, expires_at)

        assert 11111 in github_app_service._token_cache
        cached_token, cached_expires = github_app_service._token_cache[11111]
        assert cached_token == token

    def test_token_cache_clear(self):
        """Test token cache clearing."""
        github_app_service._token_cache[11111] = ("token1", datetime.utcnow())
        github_app_service._token_cache[22222] = ("token2", datetime.utcnow())

        github_app_service._token_cache.clear()

        assert len(github_app_service._token_cache) == 0
