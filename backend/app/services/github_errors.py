"""
GitHub Error Handling Module - Sprint 129 Day 4

Comprehensive error handling for GitHub API integration including:
- Custom exception classes for each error type
- Retry logic with exponential backoff
- Rate limit handling (5000 requests/hour)
- User-friendly error messages with suggested actions

Reference: ADR-044-GitHub-Integration-Strategy.md
Version: 1.0.0
Date: January 31, 2026
"""

import asyncio
import logging
import random
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, Optional, TypeVar, Union

from fastapi import HTTPException, status

logger = logging.getLogger(__name__)


# ============================================================================
# Error Codes
# ============================================================================

class GitHubErrorCode(str, Enum):
    """GitHub-specific error codes for structured error handling."""

    # Authentication errors (401)
    AUTH_FAILED = "github_auth_failed"
    TOKEN_EXPIRED = "github_token_expired"
    TOKEN_INVALID = "github_token_invalid"
    APP_NOT_CONFIGURED = "github_app_not_configured"

    # Authorization errors (403)
    ACCESS_DENIED = "github_access_denied"
    REPO_ACCESS_DENIED = "github_repo_access_denied"
    INSTALLATION_SUSPENDED = "github_installation_suspended"
    ABUSE_RATE_LIMIT = "github_abuse_rate_limit"

    # Not found errors (404)
    INSTALLATION_NOT_FOUND = "github_installation_not_found"
    REPO_NOT_FOUND = "github_repo_not_found"
    USER_NOT_FOUND = "github_user_not_found"

    # Rate limit errors (429)
    RATE_LIMIT_EXCEEDED = "github_rate_limit_exceeded"
    SECONDARY_RATE_LIMIT = "github_secondary_rate_limit"

    # Conflict errors (409)
    INSTALLATION_EXISTS = "github_installation_exists"
    REPO_ALREADY_LINKED = "github_repo_already_linked"
    PROJECT_ALREADY_LINKED = "github_project_already_linked"

    # Server errors (5xx)
    API_ERROR = "github_api_error"
    NETWORK_ERROR = "github_network_error"
    TIMEOUT = "github_timeout"
    CLONE_FAILED = "github_clone_failed"
    CLONE_TIMEOUT = "github_clone_timeout"

    # Validation errors
    INVALID_WEBHOOK_SIGNATURE = "github_invalid_webhook_signature"
    INVALID_PAYLOAD = "github_invalid_payload"


# ============================================================================
# Error Response Structure
# ============================================================================

@dataclass
class GitHubErrorResponse:
    """Structured error response for GitHub API errors."""

    code: GitHubErrorCode
    message: str
    status_code: int
    details: Optional[Dict[str, Any]] = None
    retry_after: Optional[int] = None  # Seconds to wait before retry
    suggestion: Optional[str] = None  # User action suggestion
    documentation_url: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for HTTPException detail."""
        result = {
            "error": self.code.value,
            "message": self.message,
        }
        if self.details:
            result["details"] = self.details
        if self.retry_after:
            result["retry_after"] = self.retry_after
        if self.suggestion:
            result["suggestion"] = self.suggestion
        if self.documentation_url:
            result["documentation_url"] = self.documentation_url
        return result

    def to_http_exception(self) -> HTTPException:
        """Convert to FastAPI HTTPException."""
        return HTTPException(
            status_code=self.status_code,
            detail=self.to_dict()
        )


# ============================================================================
# Custom Exceptions
# ============================================================================

class GitHubAPIError(Exception):
    """Base exception for GitHub API errors."""

    def __init__(
        self,
        code: GitHubErrorCode,
        message: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
        retry_after: Optional[int] = None,
        suggestion: Optional[str] = None
    ):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        self.retry_after = retry_after
        self.suggestion = suggestion

    @property
    def is_retryable(self) -> bool:
        """Check if this error is retryable."""
        retryable_codes = {
            GitHubErrorCode.NETWORK_ERROR,
            GitHubErrorCode.TIMEOUT,
            GitHubErrorCode.RATE_LIMIT_EXCEEDED,
            GitHubErrorCode.SECONDARY_RATE_LIMIT,
            GitHubErrorCode.API_ERROR,
            GitHubErrorCode.CLONE_TIMEOUT,
        }
        return self.code in retryable_codes or self.status_code >= 500

    @property
    def user_message(self) -> str:
        """Get user-friendly error message."""
        msg_info = get_user_friendly_message(self.code)
        return f"{msg_info['message']} {msg_info['action']}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = {
            "code": self.code.value,
            "message": self.message,
            "status_code": self.status_code,
            "is_retryable": self.is_retryable,
        }
        if self.details:
            result.update(self.details)
        if self.retry_after:
            result["retry_after"] = self.retry_after
        if self.suggestion:
            result["suggestion"] = self.suggestion
        return result

    def to_response(self) -> Dict[str, Any]:
        """Convert to API response format."""
        return {"error": self.to_dict()}

    def to_github_error_response(self) -> GitHubErrorResponse:
        """Convert to GitHubErrorResponse."""
        return GitHubErrorResponse(
            code=self.code,
            message=self.message,
            status_code=self.status_code,
            details=self.details,
            retry_after=self.retry_after,
            suggestion=self.suggestion
        )

    def to_http_exception(self) -> HTTPException:
        """Convert to FastAPI HTTPException."""
        return self.to_github_error_response().to_http_exception()


class GitHubAuthError(GitHubAPIError):
    """Authentication error (401)."""

    def __init__(
        self,
        message: str = "GitHub authentication failed",
        code: GitHubErrorCode = GitHubErrorCode.AUTH_FAILED,
        status_code: int = status.HTTP_401_UNAUTHORIZED,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            code=code,
            message=message,
            status_code=status_code,
            details=details,
            suggestion="Please re-authenticate with GitHub or check API credentials."
        )

    @property
    def user_message(self) -> str:
        """Get user-friendly message."""
        return "GitHub authentication failed. Please re-authorize the GitHub App."


class GitHubAccessDeniedError(GitHubAPIError):
    """Authorization error (403)."""

    def __init__(
        self,
        message: str = "Access denied to GitHub resource",
        code: GitHubErrorCode = GitHubErrorCode.REPO_ACCESS_DENIED,
        resource: Optional[str] = None,
        repo: Optional[str] = None,
        status_code: int = status.HTTP_403_FORBIDDEN,
        details: Optional[Dict[str, Any]] = None
    ):
        self.repo = repo or resource
        super().__init__(
            code=code,
            message=message,
            status_code=status_code,
            details=details or {"resource": self.repo} if self.repo else None,
            suggestion="Check if the GitHub App has required permissions for this repository."
        )

    @property
    def user_message(self) -> str:
        """Get user-friendly message including repo name."""
        if self.repo:
            return f"Access denied to repository {self.repo}. Please check repository permissions."
        return "Access denied to GitHub resource. Please check repository permissions."


class GitHubNotFoundError(GitHubAPIError):
    """Resource not found error (404)."""

    def __init__(
        self,
        message: str = "GitHub resource not found",
        code: GitHubErrorCode = GitHubErrorCode.REPO_NOT_FOUND,
        resource: Optional[str] = None,
        resource_id: Optional[str] = None,
        status_code: int = status.HTTP_404_NOT_FOUND,
        details: Optional[Dict[str, Any]] = None
    ):
        self.resource = resource
        self.resource_id = resource_id
        super().__init__(
            code=code,
            message=message,
            status_code=status_code,
            details=details or {"resource": resource, "resource_id": resource_id},
            suggestion="Verify the repository exists and the GitHub App is installed."
        )

    @property
    def user_message(self) -> str:
        """Get user-friendly message."""
        if self.resource == "repository":
            return f"Repository not found. It may have been deleted or made private."
        return f"GitHub {self.resource or 'resource'} not found. It may no longer exist."


class GitHubRateLimitError(GitHubAPIError):
    """Rate limit exceeded error (429)."""

    def __init__(
        self,
        message: str = "GitHub API rate limit exceeded",
        reset_at: Optional[datetime] = None,
        retry_after: Optional[int] = None,
        limit: Optional[int] = None,
        remaining: Optional[int] = None
    ):
        # Store as direct attributes for easy access
        self.reset_at = reset_at
        self.limit = limit
        self.remaining = remaining

        # Calculate retry_after if reset_at provided
        if reset_at and not retry_after:
            retry_after = max(1, int((reset_at - datetime.utcnow()).total_seconds()))

        # Calculate minutes for user message
        wait_minutes = (retry_after or 60) // 60 if (retry_after or 60) >= 60 else 1
        wait_text = f"{wait_minutes} minute(s)" if wait_minutes > 0 else f"{retry_after or 60} seconds"

        super().__init__(
            code=GitHubErrorCode.RATE_LIMIT_EXCEEDED,
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            details={
                "limit": limit,
                "remaining": remaining,
                "reset_at": reset_at.isoformat() if reset_at else None
            },
            retry_after=retry_after or 60,
            suggestion=f"Please wait {wait_text} before retrying."
        )

    @property
    def is_retryable(self) -> bool:
        """Rate limit errors are always retryable."""
        return True

    @property
    def user_message(self) -> str:
        """Get user-friendly message with wait time."""
        if self.retry_after:
            minutes = self.retry_after // 60
            if minutes >= 60:
                return f"GitHub API rate limit exceeded. Please wait {minutes // 60} hour(s) before trying again."
            elif minutes > 0:
                return f"GitHub API rate limit exceeded. Please wait {minutes} minute(s) before trying again."
            else:
                return f"GitHub API rate limit exceeded. Please wait {self.retry_after} seconds before trying again."
        return "GitHub API rate limit exceeded. Please wait before trying again."


class GitHubConflictError(GitHubAPIError):
    """Conflict error (409)."""

    def __init__(
        self,
        message: str = "Resource conflict",
        code: GitHubErrorCode = GitHubErrorCode.REPO_ALREADY_LINKED,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            code=code,
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            details=details,
            suggestion="The resource is already in use. Unlink it first if needed."
        )


class GitHubNetworkError(GitHubAPIError):
    """Network/connectivity error."""

    def __init__(
        self,
        message: str = "Failed to connect to GitHub API",
        original_error: Optional[Exception] = None
    ):
        super().__init__(
            code=GitHubErrorCode.NETWORK_ERROR,
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details={"original_error": str(original_error)} if original_error else None,
            retry_after=5,
            suggestion="Check your network connection and try again."
        )

    @property
    def is_retryable(self) -> bool:
        """Network errors are always retryable."""
        return True


class GitHubTimeoutError(GitHubAPIError):
    """Timeout error."""

    def __init__(
        self,
        message: str = "GitHub API request timed out",
        operation: Optional[str] = None,
        timeout: Optional[float] = None
    ):
        self.timeout = timeout
        super().__init__(
            code=GitHubErrorCode.TIMEOUT,
            message=message,
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            details={"operation": operation, "timeout": timeout} if operation or timeout else None,
            retry_after=10,
            suggestion="The operation is taking longer than expected. Please try again."
        )

    @property
    def is_retryable(self) -> bool:
        """Timeout errors are always retryable."""
        return True


class GitHubCloneError(GitHubAPIError):
    """Clone operation error."""

    def __init__(
        self,
        message: str = "Failed to clone repository",
        repo: Optional[str] = None,
        repo_name: Optional[str] = None,
        reason: Optional[str] = None,
        error_output: Optional[str] = None
    ):
        self.repo = repo or repo_name
        self.reason = reason or error_output
        super().__init__(
            code=GitHubErrorCode.CLONE_FAILED,
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details={
                "repository": self.repo,
                "reason": self.reason,
                "error": error_output
            } if self.repo or self.reason else None,
            suggestion="Check repository access permissions or try again later."
        )


class GitHubWebhookError(GitHubAPIError):
    """Webhook validation error."""

    def __init__(
        self,
        message: str = "Webhook validation failed",
        event_type: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.event_type = event_type
        super().__init__(
            code=GitHubErrorCode.INVALID_WEBHOOK_SIGNATURE,
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details or {"event_type": event_type} if event_type else None,
            suggestion="Check the webhook secret configuration."
        )


# ============================================================================
# Retry Logic with Exponential Backoff
# ============================================================================

T = TypeVar("T")


async def retry_with_backoff(
    func: Callable[..., T],
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retryable_exceptions: tuple = (GitHubNetworkError, GitHubTimeoutError, GitHubRateLimitError),
    on_retry: Optional[Callable[[Exception, int], None]] = None
) -> T:
    """
    Execute a function with exponential backoff retry logic.

    Args:
        func: Async function to execute
        max_retries: Maximum number of retry attempts (default: 3)
        base_delay: Initial delay in seconds (default: 1.0)
        max_delay: Maximum delay between retries (default: 60.0)
        exponential_base: Base for exponential backoff (default: 2.0)
        jitter: Add random jitter to prevent thundering herd (default: True)
        retryable_exceptions: Tuple of exception types to retry on
        on_retry: Optional callback on each retry (receives exception and attempt number)

    Returns:
        Result of the function call

    Raises:
        GitHubAPIError: If all retries are exhausted

    Example:
        >>> result = await retry_with_backoff(
        ...     lambda: get_installation_token(12345),
        ...     max_retries=3,
        ...     base_delay=1.0
        ... )
    """
    last_exception = None

    for attempt in range(max_retries + 1):
        try:
            if asyncio.iscoroutinefunction(func):
                return await func()
            else:
                return func()

        except retryable_exceptions as e:
            last_exception = e

            if attempt == max_retries:
                logger.warning(
                    f"All {max_retries + 1} attempts failed for {func.__name__ if hasattr(func, '__name__') else 'function'}"
                )
                raise

            # Calculate delay with exponential backoff
            delay = min(base_delay * (exponential_base ** attempt), max_delay)

            # Check if error has specific retry_after
            if hasattr(e, 'retry_after') and e.retry_after:
                delay = max(delay, e.retry_after)

            # Add jitter to prevent thundering herd
            if jitter:
                delay = delay * (0.5 + random.random())

            logger.info(
                f"Attempt {attempt + 1} failed with {type(e).__name__}: {e}. "
                f"Retrying in {delay:.2f}s..."
            )

            if on_retry:
                on_retry(e, attempt + 1)

            await asyncio.sleep(delay)

    # Should not reach here, but just in case
    if last_exception:
        raise last_exception


def with_retry(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    retryable_exceptions: tuple = (GitHubNetworkError, GitHubTimeoutError)
):
    """
    Decorator for adding retry logic to async functions.

    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay between retries
        retryable_exceptions: Tuple of exception types to retry on

    Example:
        >>> @with_retry(max_retries=3, base_delay=1.0)
        ... async def fetch_data():
        ...     return await api_call()
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            return await retry_with_backoff(
                lambda: func(*args, **kwargs),
                max_retries=max_retries,
                base_delay=base_delay,
                max_delay=max_delay,
                retryable_exceptions=retryable_exceptions
            )
        return wrapper
    return decorator


# ============================================================================
# Rate Limit Tracking
# ============================================================================

@dataclass
class RateLimitInfo:
    """Track GitHub API rate limit status."""

    limit: int = 5000  # Default for authenticated requests
    remaining: int = 5000
    reset_at: Optional[datetime] = None
    used: int = 0

    @classmethod
    def from_headers(cls, headers: Dict[str, str]) -> "RateLimitInfo":
        """Parse rate limit info from GitHub API response headers."""
        try:
            limit = int(headers.get("x-ratelimit-limit", 5000))
            remaining = int(headers.get("x-ratelimit-remaining", 5000))
            reset_timestamp = int(headers.get("x-ratelimit-reset", 0))
            used = int(headers.get("x-ratelimit-used", 0))

            reset_at = datetime.utcfromtimestamp(reset_timestamp) if reset_timestamp else None

            return cls(
                limit=limit,
                remaining=remaining,
                reset_at=reset_at,
                used=used
            )
        except (ValueError, TypeError) as e:
            logger.warning(f"Failed to parse rate limit headers: {e}")
            return cls()

    def is_near_limit(self, threshold: int = 100) -> bool:
        """Check if remaining requests is below threshold."""
        return self.remaining < threshold

    def seconds_until_reset(self) -> Optional[int]:
        """Get seconds until rate limit resets."""
        if not self.reset_at:
            return None
        delta = self.reset_at - datetime.utcnow()
        return max(0, int(delta.total_seconds()))


# Global rate limit tracker
_rate_limit_cache: Dict[str, RateLimitInfo] = {}


def update_rate_limit(endpoint_key: str, headers: Dict[str, str]) -> RateLimitInfo:
    """Update rate limit cache from response headers."""
    info = RateLimitInfo.from_headers(headers)
    _rate_limit_cache[endpoint_key] = info

    if info.is_near_limit():
        logger.warning(
            f"GitHub API rate limit low: {info.remaining}/{info.limit} "
            f"(resets in {info.seconds_until_reset()}s)"
        )

    return info


def get_rate_limit(endpoint_key: str = "default") -> Optional[RateLimitInfo]:
    """Get current rate limit info for an endpoint."""
    return _rate_limit_cache.get(endpoint_key)


def check_rate_limit(endpoint_key: str = "default") -> None:
    """
    Check if we should proceed with an API call based on rate limits.

    Raises:
        GitHubRateLimitError: If rate limit is exceeded or nearly exceeded
    """
    info = _rate_limit_cache.get(endpoint_key)
    if not info:
        return  # No cached info, proceed with request

    if info.remaining <= 0:
        raise GitHubRateLimitError(
            message="GitHub API rate limit exceeded",
            reset_at=info.reset_at,
            limit=info.limit,
            remaining=0
        )

    if info.is_near_limit(threshold=10):
        logger.warning(
            f"Very low rate limit remaining: {info.remaining}. "
            f"Consider waiting {info.seconds_until_reset()}s"
        )


# ============================================================================
# Error Response Helpers
# ============================================================================

def parse_github_error_response(response: Any) -> GitHubAPIError:
    """
    Parse GitHub API error response and return appropriate exception.

    Args:
        response: HTTP response object with status_code, json(), headers, text attributes

    Returns:
        Appropriate GitHubAPIError subclass
    """
    status_code = response.status_code

    # Try to parse JSON body
    try:
        response_body = response.json()
    except (ValueError, AttributeError):
        response_body = {"message": getattr(response, "text", "Unknown error")}

    message = response_body.get("message", "Unknown error")
    headers = getattr(response, "headers", {})

    # Handle rate limit errors
    if status_code == 429 or "rate limit" in message.lower():
        limit = int(headers.get("x-ratelimit-limit", 5000))
        remaining = int(headers.get("x-ratelimit-remaining", 0))
        reset_timestamp = int(headers.get("x-ratelimit-reset", 0))
        retry_after = int(headers.get("retry-after", 60))

        reset_at = datetime.utcfromtimestamp(reset_timestamp) if reset_timestamp else None

        return GitHubRateLimitError(
            message=message,
            reset_at=reset_at,
            retry_after=retry_after,
            limit=limit,
            remaining=remaining
        )

    # Handle authentication errors
    if status_code == 401:
        if "token" in message.lower():
            return GitHubAuthError(
                message=message,
                code=GitHubErrorCode.TOKEN_INVALID
            )
        return GitHubAuthError(message=message)

    # Handle authorization errors
    if status_code == 403:
        if "abuse" in message.lower() or "secondary rate limit" in message.lower():
            return GitHubRateLimitError(
                message="Secondary rate limit triggered (abuse detection)",
                retry_after=120  # GitHub recommends waiting 2 minutes
            )
        return GitHubAccessDeniedError(message=message)

    # Handle not found errors
    if status_code == 404:
        if "repository" in message.lower():
            return GitHubNotFoundError(
                message=message,
                code=GitHubErrorCode.REPO_NOT_FOUND
            )
        if "installation" in message.lower():
            return GitHubNotFoundError(
                message=message,
                code=GitHubErrorCode.INSTALLATION_NOT_FOUND
            )
        return GitHubNotFoundError(message=message)

    # Handle conflict errors
    if status_code == 409:
        return GitHubConflictError(message=message)

    # Handle server errors (retryable)
    if status_code >= 500:
        return GitHubAPIError(
            code=GitHubErrorCode.API_ERROR,
            message=message,
            status_code=status_code
        )

    # Default to generic API error
    return GitHubAPIError(
        code=GitHubErrorCode.API_ERROR,
        message=message,
        status_code=status_code
    )


# ============================================================================
# User-Friendly Error Messages
# ============================================================================

ERROR_MESSAGES: Dict[GitHubErrorCode, Dict[str, str]] = {
    GitHubErrorCode.AUTH_FAILED: {
        "title": "Authentication Failed",
        "message": "Could not authenticate with GitHub.",
        "action": "Please check your credentials or re-authenticate."
    },
    GitHubErrorCode.TOKEN_EXPIRED: {
        "title": "Token Expired",
        "message": "Your GitHub access token has expired.",
        "action": "Please re-authenticate with GitHub."
    },
    GitHubErrorCode.APP_NOT_CONFIGURED: {
        "title": "GitHub App Not Configured",
        "message": "The GitHub App is not properly configured on the server.",
        "action": "Please contact your administrator."
    },
    GitHubErrorCode.ACCESS_DENIED: {
        "title": "Access Denied",
        "message": "You don't have permission to access this resource.",
        "action": "Ask the repository owner to grant access."
    },
    GitHubErrorCode.REPO_ACCESS_DENIED: {
        "title": "Repository Access Denied",
        "message": "The GitHub App doesn't have access to this repository.",
        "action": "Install the GitHub App on this repository or request access."
    },
    GitHubErrorCode.INSTALLATION_NOT_FOUND: {
        "title": "Installation Not Found",
        "message": "GitHub App installation not found.",
        "action": "Please install the SDLC Orchestrator GitHub App."
    },
    GitHubErrorCode.REPO_NOT_FOUND: {
        "title": "Repository Not Found",
        "message": "The repository could not be found.",
        "action": "Verify the repository name and your access permissions."
    },
    GitHubErrorCode.RATE_LIMIT_EXCEEDED: {
        "title": "Rate Limit Exceeded",
        "message": "GitHub API rate limit has been exceeded.",
        "action": "Please wait a few minutes and try again."
    },
    GitHubErrorCode.REPO_ALREADY_LINKED: {
        "title": "Repository Already Linked",
        "message": "This repository is already linked to another project.",
        "action": "Unlink the repository from the other project first."
    },
    GitHubErrorCode.PROJECT_ALREADY_LINKED: {
        "title": "Project Already Linked",
        "message": "This project already has a linked repository.",
        "action": "Unlink the current repository first."
    },
    GitHubErrorCode.NETWORK_ERROR: {
        "title": "Network Error",
        "message": "Could not connect to GitHub.",
        "action": "Check your internet connection and try again."
    },
    GitHubErrorCode.TIMEOUT: {
        "title": "Request Timeout",
        "message": "The request to GitHub timed out.",
        "action": "Please try again. If the problem persists, the repository may be too large."
    },
    GitHubErrorCode.CLONE_FAILED: {
        "title": "Clone Failed",
        "message": "Failed to clone the repository.",
        "action": "Check repository access and try again."
    },
    GitHubErrorCode.CLONE_TIMEOUT: {
        "title": "Clone Timeout",
        "message": "Repository cloning timed out.",
        "action": "The repository may be too large. Try with a smaller repository."
    },
    GitHubErrorCode.INVALID_WEBHOOK_SIGNATURE: {
        "title": "Invalid Webhook",
        "message": "The webhook signature is invalid.",
        "action": "This may be a security issue. Contact your administrator."
    }
}


def get_user_friendly_message(code: GitHubErrorCode) -> Dict[str, str]:
    """Get user-friendly error message for a given error code."""
    return ERROR_MESSAGES.get(code, {
        "title": "GitHub Error",
        "message": "An unexpected error occurred with GitHub.",
        "action": "Please try again or contact support."
    })
