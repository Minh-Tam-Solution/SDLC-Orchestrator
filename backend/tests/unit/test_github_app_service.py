"""
=========================================================================
Unit Tests - GitHub App Service (Sprint 81)
SDLC Orchestrator - Stage 04 (BUILD)

Version: 1.0.0
Date: January 19, 2026
Status: ACTIVE - Sprint 81 Implementation
Authority: QA Lead + Backend Lead Approved
Reference: TDS-081-001 GitHub App Integration

Purpose:
- Test JWT generation for GitHub App
- Test Installation Token management
- Test token caching
- Test error handling

Unit Coverage: 10 test cases
=========================================================================
"""

import time
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch, AsyncMock
import pytest

from app.services.github_app_service import (
    GitHubAppService,
    GitHubAppNotConfiguredError,
    GitHubAppAuthError,
    GitHubAppInstallationError,
)


class TestGitHubAppServiceInit:
    """Test GitHubAppService initialization."""

    def test_init_with_no_config(self):
        """Test service initialization when not configured."""
        with patch("app.services.github_app_service.settings") as mock_settings:
            mock_settings.GITHUB_APP_ID = None
            mock_settings.GITHUB_APP_PRIVATE_KEY = None

            service = GitHubAppService()

            assert service.is_configured is False
            assert service.app_id is None

    def test_init_with_raw_pem_key(self):
        """Test service initialization with raw PEM private key."""
        test_key = """-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA0Z3VS5JJcds3xfn/yqWyK5p...
-----END RSA PRIVATE KEY-----"""

        with patch("app.services.github_app_service.settings") as mock_settings:
            mock_settings.GITHUB_APP_ID = "12345"
            mock_settings.GITHUB_APP_PRIVATE_KEY = test_key

            service = GitHubAppService()

            assert service.is_configured is True
            assert service.app_id == "12345"

    def test_init_with_base64_key(self):
        """Test service initialization with base64 encoded key."""
        import base64

        raw_key = "-----BEGIN RSA PRIVATE KEY-----\ntest\n-----END RSA PRIVATE KEY-----"
        encoded_key = base64.b64encode(raw_key.encode()).decode()

        with patch("app.services.github_app_service.settings") as mock_settings:
            mock_settings.GITHUB_APP_ID = "12345"
            mock_settings.GITHUB_APP_PRIVATE_KEY = encoded_key

            service = GitHubAppService()

            assert service.is_configured is True


class TestJWTGeneration:
    """Test JWT generation for GitHub App authentication."""

    def test_generate_jwt_not_configured(self):
        """Test JWT generation fails when not configured."""
        with patch("app.services.github_app_service.settings") as mock_settings:
            mock_settings.GITHUB_APP_ID = None
            mock_settings.GITHUB_APP_PRIVATE_KEY = None

            service = GitHubAppService()

            with pytest.raises(GitHubAppNotConfiguredError):
                service._generate_jwt()

    @patch("app.services.github_app_service.jwt.encode")
    def test_generate_jwt_success(self, mock_jwt_encode):
        """Test successful JWT generation."""
        mock_jwt_encode.return_value = "test_jwt_token"

        with patch("app.services.github_app_service.settings") as mock_settings:
            mock_settings.GITHUB_APP_ID = "12345"
            mock_settings.GITHUB_APP_PRIVATE_KEY = "-----BEGIN RSA PRIVATE KEY-----\ntest\n-----END RSA PRIVATE KEY-----"

            service = GitHubAppService()
            jwt_token = service._generate_jwt()

            assert jwt_token == "test_jwt_token"
            mock_jwt_encode.assert_called_once()

            # Verify JWT payload structure
            call_args = mock_jwt_encode.call_args
            payload = call_args[0][0]

            assert "iat" in payload
            assert "exp" in payload
            assert "iss" in payload
            assert payload["iss"] == "12345"


class TestInstallationToken:
    """Test Installation Token management."""

    @pytest.mark.asyncio
    async def test_get_installation_token_not_configured(self):
        """Test getting token fails when not configured."""
        with patch("app.services.github_app_service.settings") as mock_settings:
            mock_settings.GITHUB_APP_ID = None
            mock_settings.GITHUB_APP_PRIVATE_KEY = None

            service = GitHubAppService()

            with pytest.raises(GitHubAppNotConfiguredError):
                await service.get_installation_token(12345)

    @pytest.mark.asyncio
    @patch("app.services.github_app_service.requests.post")
    @patch("app.services.github_app_service.jwt.encode")
    async def test_get_installation_token_success(self, mock_jwt_encode, mock_post):
        """Test successful installation token retrieval."""
        mock_jwt_encode.return_value = "test_jwt"

        # Mock GitHub API response
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "token": "ghs_test_installation_token",
            "expires_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
        }
        mock_post.return_value = mock_response

        with patch("app.services.github_app_service.settings") as mock_settings:
            mock_settings.GITHUB_APP_ID = "12345"
            mock_settings.GITHUB_APP_PRIVATE_KEY = "-----BEGIN RSA PRIVATE KEY-----\ntest\n-----END RSA PRIVATE KEY-----"

            service = GitHubAppService()
            token = await service.get_installation_token(12345)

            assert token == "ghs_test_installation_token"
            mock_post.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.services.github_app_service.requests.post")
    @patch("app.services.github_app_service.jwt.encode")
    async def test_get_installation_token_cached(self, mock_jwt_encode, mock_post):
        """Test installation token is cached."""
        mock_jwt_encode.return_value = "test_jwt"

        # Mock GitHub API response
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "token": "ghs_cached_token",
            "expires_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
        }
        mock_post.return_value = mock_response

        with patch("app.services.github_app_service.settings") as mock_settings:
            mock_settings.GITHUB_APP_ID = "12345"
            mock_settings.GITHUB_APP_PRIVATE_KEY = "-----BEGIN RSA PRIVATE KEY-----\ntest\n-----END RSA PRIVATE KEY-----"

            service = GitHubAppService()

            # First call - should fetch from API
            token1 = await service.get_installation_token(12345)
            assert mock_post.call_count == 1

            # Second call - should use cache
            token2 = await service.get_installation_token(12345)
            assert mock_post.call_count == 1  # No additional API call

            assert token1 == token2

    @pytest.mark.asyncio
    @patch("app.services.github_app_service.requests.post")
    @patch("app.services.github_app_service.jwt.encode")
    async def test_get_installation_token_404(self, mock_jwt_encode, mock_post):
        """Test handling of installation not found."""
        mock_jwt_encode.return_value = "test_jwt"

        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_post.return_value = mock_response

        with patch("app.services.github_app_service.settings") as mock_settings:
            mock_settings.GITHUB_APP_ID = "12345"
            mock_settings.GITHUB_APP_PRIVATE_KEY = "-----BEGIN RSA PRIVATE KEY-----\ntest\n-----END RSA PRIVATE KEY-----"

            service = GitHubAppService()

            with pytest.raises(GitHubAppInstallationError) as exc_info:
                await service.get_installation_token(99999)

            assert "not found" in str(exc_info.value).lower()


class TestInstallationLookup:
    """Test installation ID lookup for repositories."""

    @pytest.mark.asyncio
    @patch("app.services.github_app_service.requests.get")
    @patch("app.services.github_app_service.jwt.encode")
    async def test_get_installation_for_repo_success(self, mock_jwt_encode, mock_get):
        """Test successful installation lookup."""
        mock_jwt_encode.return_value = "test_jwt"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": 12345}
        mock_get.return_value = mock_response

        with patch("app.services.github_app_service.settings") as mock_settings:
            mock_settings.GITHUB_APP_ID = "12345"
            mock_settings.GITHUB_APP_PRIVATE_KEY = "-----BEGIN RSA PRIVATE KEY-----\ntest\n-----END RSA PRIVATE KEY-----"

            service = GitHubAppService()
            installation_id = await service.get_installation_for_repo("owner", "repo")

            assert installation_id == 12345

    @pytest.mark.asyncio
    @patch("app.services.github_app_service.requests.get")
    @patch("app.services.github_app_service.jwt.encode")
    async def test_get_installation_for_repo_not_installed(self, mock_jwt_encode, mock_get):
        """Test when app is not installed on repo."""
        mock_jwt_encode.return_value = "test_jwt"

        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        with patch("app.services.github_app_service.settings") as mock_settings:
            mock_settings.GITHUB_APP_ID = "12345"
            mock_settings.GITHUB_APP_PRIVATE_KEY = "-----BEGIN RSA PRIVATE KEY-----\ntest\n-----END RSA PRIVATE KEY-----"

            service = GitHubAppService()
            installation_id = await service.get_installation_for_repo("owner", "repo")

            assert installation_id is None


class TestTokenCacheManagement:
    """Test token cache management."""

    def test_clear_token_cache_specific(self):
        """Test clearing cache for specific installation."""
        with patch("app.services.github_app_service.settings") as mock_settings:
            mock_settings.GITHUB_APP_ID = "12345"
            mock_settings.GITHUB_APP_PRIVATE_KEY = "-----BEGIN RSA PRIVATE KEY-----\ntest\n-----END RSA PRIVATE KEY-----"

            service = GitHubAppService()

            # Manually add to cache
            service._token_cache[12345] = ("token1", datetime.now(timezone.utc))
            service._token_cache[67890] = ("token2", datetime.now(timezone.utc))

            # Clear specific
            service.clear_token_cache(installation_id=12345)

            assert 12345 not in service._token_cache
            assert 67890 in service._token_cache

    def test_clear_token_cache_all(self):
        """Test clearing all cached tokens."""
        with patch("app.services.github_app_service.settings") as mock_settings:
            mock_settings.GITHUB_APP_ID = "12345"
            mock_settings.GITHUB_APP_PRIVATE_KEY = "-----BEGIN RSA PRIVATE KEY-----\ntest\n-----END RSA PRIVATE KEY-----"

            service = GitHubAppService()

            # Manually add to cache
            service._token_cache[12345] = ("token1", datetime.now(timezone.utc))
            service._token_cache[67890] = ("token2", datetime.now(timezone.utc))

            # Clear all
            service.clear_token_cache()

            assert len(service._token_cache) == 0
