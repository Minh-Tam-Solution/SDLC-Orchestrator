"""
Unit tests for GitHub error handling.

Sprint 129 Day 4 - Error Handling + Recovery
Tests 12 error scenarios for GitHub integration.

Reference: ADR-044-GitHub-Integration-Strategy.md
"""

import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from app.services.github_errors import (
    GitHubAPIError,
    GitHubAuthError,
    GitHubAccessDeniedError,
    GitHubNotFoundError,
    GitHubRateLimitError,
    GitHubNetworkError,
    GitHubTimeoutError,
    GitHubCloneError,
    GitHubWebhookError,
    GitHubErrorCode,
    retry_with_backoff,
    update_rate_limit,
    check_rate_limit,
    parse_github_error_response,
    _rate_limit_cache,
)


class TestGitHubErrorClasses:
    """Test 1-8: GitHub error class hierarchy and behavior."""

    def test_1_github_api_error_base(self):
        """Test 1: Base GitHubAPIError class properties."""
        error = GitHubAPIError(
            code=GitHubErrorCode.AUTH_FAILED,
            message="Authentication failed",
            status_code=401,
        )

        assert error.code == GitHubErrorCode.AUTH_FAILED
        assert error.message == "Authentication failed"
        assert error.status_code == 401
        assert error.is_retryable is False

    def test_2_github_auth_error(self):
        """Test 2: GitHubAuthError for authentication failures."""
        error = GitHubAuthError(
            message="JWT token expired",
            status_code=401,
        )

        assert error.code == GitHubErrorCode.AUTH_FAILED
        assert "JWT token expired" in str(error)
        assert error.is_retryable is False
        assert "re-authorize" in error.user_message.lower() or "GitHub App" in error.user_message

    def test_3_github_rate_limit_error_with_reset(self):
        """Test 3: GitHubRateLimitError with reset time calculation."""
        reset_at = datetime.utcnow() + timedelta(minutes=30)
        error = GitHubRateLimitError(
            message="Rate limit exceeded",
            reset_at=reset_at,
            retry_after=1800,
            limit=5000,
            remaining=0,
        )

        assert error.code == GitHubErrorCode.RATE_LIMIT_EXCEEDED
        assert error.is_retryable is True
        assert error.retry_after == 1800
        assert error.limit == 5000
        assert error.remaining == 0
        # Should mention wait time in user message
        assert "minute" in error.user_message.lower() or "30" in error.user_message

    def test_4_github_access_denied_error(self):
        """Test 4: GitHubAccessDeniedError for permission issues."""
        error = GitHubAccessDeniedError(
            message="Repository access denied",
            repo="owner/repo",
            status_code=403,
        )

        assert error.code == GitHubErrorCode.REPO_ACCESS_DENIED
        assert error.repo == "owner/repo"
        assert "owner/repo" in error.user_message

    def test_5_github_not_found_error(self):
        """Test 5: GitHubNotFoundError for missing resources."""
        error = GitHubNotFoundError(
            message="Repository not found",
            resource="repository",
            resource_id="owner/repo",
            status_code=404,
        )

        assert error.code == GitHubErrorCode.REPO_NOT_FOUND
        assert error.resource == "repository"
        assert error.resource_id == "owner/repo"

    def test_6_github_network_error_is_retryable(self):
        """Test 6: GitHubNetworkError is marked as retryable."""
        error = GitHubNetworkError(
            message="Connection refused to api.github.com",
        )

        assert error.code == GitHubErrorCode.NETWORK_ERROR
        assert error.is_retryable is True

    def test_7_github_timeout_error_is_retryable(self):
        """Test 7: GitHubTimeoutError is marked as retryable."""
        error = GitHubTimeoutError(
            message="Request timed out after 30s",
            timeout=30.0,
        )

        assert error.code == GitHubErrorCode.TIMEOUT
        assert error.is_retryable is True
        assert error.timeout == 30.0

    def test_8_github_clone_and_webhook_errors(self):
        """Test 8: GitHubCloneError and GitHubWebhookError."""
        clone_error = GitHubCloneError(
            message="Failed to clone repository",
            repo="owner/repo",
            reason="Permission denied",
        )
        assert clone_error.code == GitHubErrorCode.CLONE_FAILED
        assert clone_error.repo == "owner/repo"
        assert clone_error.reason == "Permission denied"

        webhook_error = GitHubWebhookError(
            message="Invalid webhook signature",
            event_type="push",
        )
        assert webhook_error.code == GitHubErrorCode.INVALID_WEBHOOK_SIGNATURE
        assert webhook_error.event_type == "push"


class TestRetryWithBackoff:
    """Test 9-10: Retry with exponential backoff functionality."""

    @pytest.mark.asyncio
    async def test_9_retry_success_and_failures(self):
        """Test 9: Retry succeeds after failures."""
        # Test success on first attempt
        mock_func1 = AsyncMock(return_value="success")
        result1 = await retry_with_backoff(mock_func1, max_retries=3)
        assert result1 == "success"
        assert mock_func1.call_count == 1

        # Test success after failures
        mock_func2 = AsyncMock(side_effect=[
            GitHubNetworkError("Connection failed"),
            GitHubNetworkError("Connection failed"),
            "success",
        ])

        result2 = await retry_with_backoff(
            mock_func2,
            max_retries=3,
            base_delay=0.01,
        )

        assert result2 == "success"
        assert mock_func2.call_count == 3

    @pytest.mark.asyncio
    async def test_10_retry_non_retryable_not_retried(self):
        """Test 10: Non-retryable errors are not retried."""
        mock_func = AsyncMock(side_effect=GitHubAuthError("Auth failed"))

        with pytest.raises(GitHubAuthError):
            await retry_with_backoff(
                mock_func,
                max_retries=3,
                base_delay=0.01,
            )

        # Should only be called once - auth errors are not retryable
        assert mock_func.call_count == 1


class TestRateLimitTracking:
    """Test 11: Rate limit cache and tracking functionality."""

    def setup_method(self):
        """Clear rate limit cache before each test."""
        _rate_limit_cache.clear()

    def test_11_rate_limit_tracking(self):
        """Test 11: Rate limit update and check functions."""
        # Test update from headers
        headers = {
            "x-ratelimit-limit": "5000",
            "x-ratelimit-remaining": "4999",
            "x-ratelimit-reset": str(int((datetime.utcnow() + timedelta(hours=1)).timestamp())),
        }

        update_rate_limit("test_key", headers)

        info = _rate_limit_cache.get("test_key")
        assert info is not None
        assert info.limit == 5000
        assert info.remaining == 4999

        # Test check when ok
        check_rate_limit("test_key")  # Should not raise

        # Test check when exhausted
        reset_at = datetime.utcnow() + timedelta(hours=1)
        from app.services.github_errors import RateLimitInfo
        _rate_limit_cache["exhausted_key"] = RateLimitInfo(
            limit=5000,
            remaining=0,
            reset_at=reset_at,
        )

        with pytest.raises(GitHubRateLimitError) as exc_info:
            check_rate_limit("exhausted_key")

        assert exc_info.value.remaining == 0
        assert exc_info.value.limit == 5000

        # Test unknown key passes
        check_rate_limit("unknown_key")  # Should not raise


class TestParseGitHubErrorResponse:
    """Test 12: Parsing GitHub API error responses."""

    def test_12_parse_error_responses(self):
        """Test 12: Parse various HTTP error responses."""
        # Test 401 unauthorized
        response_401 = MagicMock()
        response_401.status_code = 401
        response_401.json.return_value = {"message": "Bad credentials"}
        response_401.headers = {}

        error_401 = parse_github_error_response(response_401)
        assert isinstance(error_401, GitHubAuthError)
        assert error_401.code == GitHubErrorCode.AUTH_FAILED

        # Test 403 forbidden
        response_403 = MagicMock()
        response_403.status_code = 403
        response_403.json.return_value = {"message": "Resource not accessible"}
        response_403.headers = {}

        error_403 = parse_github_error_response(response_403)
        assert isinstance(error_403, GitHubAccessDeniedError)
        assert error_403.code == GitHubErrorCode.REPO_ACCESS_DENIED

        # Test 404 not found
        response_404 = MagicMock()
        response_404.status_code = 404
        response_404.json.return_value = {"message": "Not Found"}
        response_404.headers = {}

        error_404 = parse_github_error_response(response_404)
        assert isinstance(error_404, GitHubNotFoundError)
        assert error_404.code == GitHubErrorCode.REPO_NOT_FOUND

        # Test 429 rate limit
        reset_timestamp = int((datetime.utcnow() + timedelta(hours=1)).timestamp())
        response_429 = MagicMock()
        response_429.status_code = 429
        response_429.json.return_value = {"message": "API rate limit exceeded"}
        response_429.headers = {
            "x-ratelimit-limit": "5000",
            "x-ratelimit-remaining": "0",
            "x-ratelimit-reset": str(reset_timestamp),
            "retry-after": "3600",
        }

        error_429 = parse_github_error_response(response_429)
        assert isinstance(error_429, GitHubRateLimitError)
        assert error_429.code == GitHubErrorCode.RATE_LIMIT_EXCEEDED
        assert error_429.limit == 5000
        assert error_429.remaining == 0
        assert error_429.retry_after == 3600

        # Test 500 server error (retryable)
        response_500 = MagicMock()
        response_500.status_code = 500
        response_500.json.return_value = {"message": "Internal Server Error"}
        response_500.headers = {}

        error_500 = parse_github_error_response(response_500)
        assert isinstance(error_500, GitHubAPIError)
        assert error_500.is_retryable is True

        # Test invalid JSON response
        response_bad = MagicMock()
        response_bad.status_code = 500
        response_bad.json.side_effect = ValueError("Invalid JSON")
        response_bad.text = "Internal Server Error"
        response_bad.headers = {}

        error_bad = parse_github_error_response(response_bad)
        assert isinstance(error_bad, GitHubAPIError)
        assert "Internal Server Error" in error_bad.message


class TestErrorSerialization:
    """Additional tests for error serialization."""

    def test_error_to_dict(self):
        """Test error can be serialized to dictionary."""
        error = GitHubRateLimitError(
            message="Rate limit exceeded",
            reset_at=datetime(2026, 1, 31, 12, 0, 0),
            retry_after=3600,
            limit=5000,
            remaining=0,
        )

        error_dict = error.to_dict()

        assert error_dict["code"] == "github_rate_limit_exceeded"
        assert error_dict["message"] == "Rate limit exceeded"
        assert error_dict["retry_after"] == 3600
        assert error_dict["limit"] == 5000
        assert error_dict["remaining"] == 0
        assert "reset_at" in error_dict

    def test_error_to_response(self):
        """Test error can be converted to API response format."""
        error = GitHubAccessDeniedError(
            message="Access denied to repository",
            repo="owner/repo",
        )

        response = error.to_response()

        assert response["error"]["code"] == "github_repo_access_denied"
        assert "owner/repo" in response["error"]["message"] or "owner/repo" in str(response["error"].get("resource", ""))
        assert response["error"]["is_retryable"] is False


class TestErrorCodeMapping:
    """Test error code enumeration."""

    def test_all_error_codes_have_unique_values(self):
        """Test all error codes have unique values."""
        codes = [e.value for e in GitHubErrorCode]
        assert len(codes) == len(set(codes)), "Duplicate error code values found"

    def test_error_codes_are_strings(self):
        """Test error codes are string values for JSON serialization."""
        for code in GitHubErrorCode:
            assert isinstance(code.value, str)

    def test_common_error_codes_exist(self):
        """Test common error codes are defined."""
        expected_codes = [
            "github_auth_failed",
            "github_rate_limit_exceeded",
            "github_repo_access_denied",
            "github_repo_not_found",
            "github_clone_failed",
            "github_network_error",
            "github_timeout",
        ]

        actual_codes = [e.value for e in GitHubErrorCode]
        for expected in expected_codes:
            assert expected in actual_codes, f"Missing error code: {expected}"
