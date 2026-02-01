"""
Integration tests for GitHub OAuth Device Flow.

Sprint 127 - Multi-Frontend Alignment Bug Fixes
Tests the newly added Device Flow endpoints for VS Code Extension.
"""

import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch, MagicMock

from app.main import app
from app.core.config import settings


class TestGitHubDeviceFlow:
    """Test GitHub OAuth Device Flow endpoints."""

    @pytest.mark.asyncio
    async def test_device_flow_initiation_success(self):
        """Test successful device flow initiation."""
        # Mock GitHub response
        mock_github_response = {
            "device_code": "3584d83530557fdd1f46af8289938c8ef79f9dc5",
            "user_code": "WDJB-MJHT",
            "verification_uri": "https://github.com/login/device",
            "expires_in": 900,
            "interval": 5,
        }

        with patch("app.services.oauth_service.httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_github_response
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post("/api/v1/auth/github/device")

                assert response.status_code == 200
                data = response.json()
                assert data["device_code"] == mock_github_response["device_code"]
                assert data["user_code"] == mock_github_response["user_code"]
                assert data["verification_uri"] == mock_github_response["verification_uri"]
                assert data["expires_in"] == 900
                assert data["interval"] == 5

    @pytest.mark.asyncio
    async def test_device_flow_initiation_github_error(self):
        """Test device flow initiation when GitHub returns error."""
        mock_github_response = {
            "error": "bad_verification_code",
            "error_description": "The device_code is invalid",
        }

        with patch("app.services.oauth_service.httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_github_response
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post("/api/v1/auth/github/device")

                assert response.status_code == 400
                assert "bad_verification_code" in response.text

    @pytest.mark.asyncio
    async def test_device_token_poll_authorization_pending(self):
        """Test polling when user hasn't authorized yet."""
        # Mock GitHub response (authorization pending)
        mock_github_response = {
            "error": "authorization_pending",
            "error_description": "The authorization request is still pending",
        }

        with patch("app.services.oauth_service.httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_github_response
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/auth/github/token",
                    json={"device_code": "test_device_code"},
                )

                assert response.status_code == 400
                data = response.json()
                assert data["error"] == "authorization_pending"

    @pytest.mark.asyncio
    async def test_device_token_poll_slow_down(self):
        """Test polling when rate limit exceeded."""
        mock_github_response = {
            "error": "slow_down",
            "error_description": "You are polling too quickly",
        }

        with patch("app.services.oauth_service.httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_github_response
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/auth/github/token",
                    json={"device_code": "test_device_code"},
                )

                assert response.status_code == 400
                data = response.json()
                assert data["error"] == "slow_down"

    @pytest.mark.asyncio
    async def test_device_token_poll_expired(self):
        """Test polling when device code expired."""
        mock_github_response = {
            "error": "expired_token",
            "error_description": "The device code has expired",
        }

        with patch("app.services.oauth_service.httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_github_response
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/auth/github/token",
                    json={"device_code": "test_device_code"},
                )

                assert response.status_code == 400
                data = response.json()
                assert data["error"] == "expired_token"

    @pytest.mark.asyncio
    async def test_device_token_poll_access_denied(self):
        """Test polling when user denied authorization."""
        mock_github_response = {
            "error": "access_denied",
            "error_description": "The user denied the authorization request",
        }

        with patch("app.services.oauth_service.httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_github_response
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/auth/github/token",
                    json={"device_code": "test_device_code"},
                )

                assert response.status_code == 400
                data = response.json()
                assert data["error"] == "access_denied"

    @pytest.mark.asyncio
    async def test_device_token_poll_missing_device_code(self):
        """Test polling without device_code."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/auth/github/token",
                json={},  # Missing device_code
            )

            assert response.status_code == 422  # Validation error

    @pytest.mark.skip(reason="Requires database and full OAuth flow mock")
    @pytest.mark.asyncio
    async def test_device_token_poll_success(self):
        """
        Test successful device token polling.

        This test requires:
        - Mocked GitHub token exchange (success)
        - Mocked GitHub user info retrieval
        - Database setup for user creation/linking
        - JWT token generation
        """
        # TODO: Implement when database fixtures are ready
        pass


class TestGitHubDeviceFlowConfiguration:
    """Test Device Flow configuration and error handling."""

    @pytest.mark.asyncio
    async def test_device_flow_without_github_config(self):
        """Test device flow when GitHub OAuth is not configured."""
        with patch.object(settings, "GITHUB_CLIENT_ID", None):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post("/api/v1/auth/github/device")

                assert response.status_code == 400
                assert "not configured" in response.text.lower()
