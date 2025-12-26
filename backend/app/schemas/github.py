"""
=========================================================================
GitHub Schemas - Request/Response Models for GitHub Integration
SDLC Orchestrator - Stage 03 (BUILD)

Version: 1.0.0
Date: November 28, 2025
Status: ACTIVE - Sprint 15 (GitHub Foundation)
Authority: Backend Lead + CPO Approved
Foundation: Sprint 15 Plan, User-Onboarding-Flow-Architecture.md
Framework: SDLC 4.9 Complete Lifecycle

Purpose:
- Pydantic models for GitHub API endpoints
- Request validation (OAuth, repository sync)
- Response serialization (repositories, webhook events)

Zero Mock Policy: Production-ready schemas with validation
=========================================================================
"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl


# ============================================================================
# OAuth Schemas
# ============================================================================


class GitHubOAuthURLResponse(BaseModel):
    """Response for GitHub OAuth authorization URL."""

    authorization_url: str = Field(..., description="GitHub OAuth authorization URL")
    state: str = Field(..., description="CSRF protection state parameter")

    class Config:
        json_schema_extra = {
            "example": {
                "authorization_url": "https://github.com/login/oauth/authorize?client_id=abc123&scope=read:user%20user:email%20repo&state=xyz789",
                "state": "xyz789",
            }
        }


class GitHubOAuthCallbackRequest(BaseModel):
    """Request for GitHub OAuth callback handling."""

    code: str = Field(..., description="OAuth authorization code from GitHub")
    state: str = Field(..., description="CSRF protection state parameter")

    class Config:
        json_schema_extra = {
            "example": {
                "code": "abc123def456",
                "state": "xyz789",
            }
        }


class GitHubOAuthCallbackResponse(BaseModel):
    """Response after successful GitHub OAuth callback."""

    access_token: str = Field(..., description="JWT access token for SDLC Orchestrator")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Access token expiry in seconds")
    github_connected: bool = Field(default=True, description="GitHub connection status")
    user_id: UUID = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    name: Optional[str] = Field(None, description="User display name")
    avatar_url: Optional[str] = Field(None, description="User avatar URL")

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 3600,
                "github_connected": True,
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "email": "developer@example.com",
                "name": "Developer Name",
                "avatar_url": "https://avatars.githubusercontent.com/u/12345",
            }
        }


# ============================================================================
# Repository Schemas
# ============================================================================


class GitHubRepositoryOwner(BaseModel):
    """GitHub repository owner info."""

    login: str = Field(..., description="Owner username")
    id: int = Field(..., description="Owner ID")
    avatar_url: Optional[str] = Field(None, description="Avatar URL")
    type: str = Field(default="User", description="Owner type (User or Organization)")


class GitHubRepository(BaseModel):
    """GitHub repository details."""

    id: int = Field(..., description="GitHub repository ID")
    name: str = Field(..., description="Repository name")
    full_name: str = Field(..., description="Full repository name (owner/repo)")
    description: Optional[str] = Field(None, description="Repository description")
    html_url: str = Field(..., description="GitHub URL")
    clone_url: Optional[str] = Field(None, description="Git clone URL")
    default_branch: str = Field(default="main", description="Default branch")
    language: Optional[str] = Field(None, description="Primary language")
    private: bool = Field(default=False, description="Is private repository")
    fork: bool = Field(default=False, description="Is forked repository")
    stargazers_count: int = Field(default=0, description="Star count")
    forks_count: int = Field(default=0, description="Fork count")
    open_issues_count: int = Field(default=0, description="Open issues count")
    owner: GitHubRepositoryOwner = Field(..., description="Repository owner")
    created_at: Optional[datetime] = Field(None, description="Created timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last updated timestamp")
    pushed_at: Optional[datetime] = Field(None, description="Last push timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "id": 123456789,
                "name": "my-project",
                "full_name": "developer/my-project",
                "description": "A sample project",
                "html_url": "https://github.com/developer/my-project",
                "clone_url": "https://github.com/developer/my-project.git",
                "default_branch": "main",
                "language": "Python",
                "private": False,
                "fork": False,
                "stargazers_count": 42,
                "forks_count": 10,
                "open_issues_count": 5,
                "owner": {
                    "login": "developer",
                    "id": 12345,
                    "avatar_url": "https://avatars.githubusercontent.com/u/12345",
                    "type": "User",
                },
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2025-01-01T00:00:00Z",
                "pushed_at": "2025-01-01T00:00:00Z",
            }
        }


class GitHubRepositoryListResponse(BaseModel):
    """Response for listing GitHub repositories."""

    repositories: list[GitHubRepository] = Field(
        ..., description="List of repositories"
    )
    total: int = Field(..., description="Total repository count")
    page: int = Field(default=1, description="Current page")
    per_page: int = Field(default=30, description="Items per page")

    class Config:
        json_schema_extra = {
            "example": {
                "repositories": [],
                "total": 25,
                "page": 1,
                "per_page": 30,
            }
        }


class GitHubRepositoryContents(BaseModel):
    """GitHub repository file/directory item."""

    name: str = Field(..., description="File/directory name")
    path: str = Field(..., description="Path within repository")
    type: str = Field(..., description="Type: 'file' or 'dir'")
    size: int = Field(default=0, description="File size in bytes")
    sha: str = Field(..., description="Git SHA hash")
    download_url: Optional[str] = Field(None, description="Raw file download URL")


class GitHubRepositoryLanguages(BaseModel):
    """GitHub repository language breakdown."""

    languages: dict[str, int] = Field(
        ..., description="Language breakdown (bytes per language)"
    )
    primary_language: Optional[str] = Field(None, description="Primary language")

    class Config:
        json_schema_extra = {
            "example": {
                "languages": {"Python": 50000, "TypeScript": 30000, "JavaScript": 10000},
                "primary_language": "Python",
            }
        }


# ============================================================================
# Repository Sync Schemas
# ============================================================================


class GitHubSyncRequest(BaseModel):
    """Request to sync GitHub repository to SDLC Orchestrator project."""

    github_repo_id: int = Field(..., description="GitHub repository ID")
    github_repo_full_name: str = Field(
        ..., description="Full repository name (owner/repo)"
    )
    project_name: Optional[str] = Field(
        None, description="Custom project name (default: repo name)"
    )
    auto_setup: bool = Field(
        default=True, description="Auto-run AI analysis and stage mapping"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "github_repo_id": 123456789,
                "github_repo_full_name": "developer/my-project",
                "project_name": "My Project",
                "auto_setup": True,
            }
        }


class GitHubSyncResponse(BaseModel):
    """Response after syncing GitHub repository."""

    project_id: UUID = Field(..., description="Created project ID")
    project_name: str = Field(..., description="Project name")
    project_slug: str = Field(..., description="Project slug")
    github_repo_id: int = Field(..., description="GitHub repository ID")
    github_repo_full_name: str = Field(..., description="Full repository name")
    sync_status: str = Field(
        default="synced", description="Sync status: synced, syncing, error"
    )
    synced_at: datetime = Field(..., description="Sync timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "project_id": "550e8400-e29b-41d4-a716-446655440000",
                "project_name": "My Project",
                "project_slug": "my-project",
                "github_repo_id": 123456789,
                "github_repo_full_name": "developer/my-project",
                "sync_status": "synced",
                "synced_at": "2025-01-01T00:00:00Z",
            }
        }


# ============================================================================
# Webhook Schemas
# ============================================================================


class GitHubWebhookEvent(BaseModel):
    """Normalized GitHub webhook event."""

    event_type: str = Field(
        ..., description="Event type: push, pull_request, issues, etc."
    )
    repository: dict[str, Any] = Field(..., description="Repository info")
    sender: dict[str, Any] = Field(..., description="Event sender info")
    action: Optional[str] = Field(None, description="Event action (for PR/issues)")
    timestamp: datetime = Field(..., description="Event timestamp")
    data: dict[str, Any] = Field(default_factory=dict, description="Event-specific data")

    class Config:
        json_schema_extra = {
            "example": {
                "event_type": "push",
                "repository": {
                    "id": 123456789,
                    "full_name": "developer/my-project",
                    "name": "my-project",
                    "owner": "developer",
                    "private": False,
                },
                "sender": {"id": 12345, "login": "developer"},
                "action": None,
                "timestamp": "2025-01-01T00:00:00Z",
                "data": {
                    "ref": "refs/heads/main",
                    "commits": 3,
                    "head_commit": "feat: Add new feature",
                },
            }
        }


class GitHubWebhookResponse(BaseModel):
    """Response after processing GitHub webhook."""

    received: bool = Field(default=True, description="Webhook received successfully")
    event_type: str = Field(..., description="Processed event type")
    repository: str = Field(..., description="Repository full name")
    message: str = Field(default="Webhook processed", description="Status message")

    class Config:
        json_schema_extra = {
            "example": {
                "received": True,
                "event_type": "push",
                "repository": "developer/my-project",
                "message": "Push event processed: 3 commits to main",
            }
        }


# ============================================================================
# Rate Limit Schemas
# ============================================================================


class GitHubRateLimitInfo(BaseModel):
    """GitHub API rate limit information."""

    limit: int = Field(..., description="Rate limit per hour")
    remaining: int = Field(..., description="Remaining requests")
    reset: datetime = Field(..., description="Rate limit reset time")
    used: int = Field(..., description="Requests used this hour")

    class Config:
        json_schema_extra = {
            "example": {
                "limit": 5000,
                "remaining": 4999,
                "reset": "2025-01-01T01:00:00Z",
                "used": 1,
            }
        }


# ============================================================================
# Connection Status Schemas
# ============================================================================


# ============================================================================
# Stage Mapping Schemas (Sprint 49 - SDLC 5.1.2)
# ============================================================================


class StageMappingItem(BaseModel):
    """Individual stage mapping for a folder."""

    folder_path: str = Field(..., description="Folder path relative to repo root")
    stage_code: str = Field(..., description="SDLC stage code: '00'-'09' or '10' for archive")
    stage_name: Optional[str] = Field(None, description="Human-readable stage name")
    is_auto_detected: bool = Field(default=True, description="Auto-detected or manually set")
    confidence: Optional[float] = Field(None, description="Detection confidence (0.0-1.0)")

    class Config:
        json_schema_extra = {
            "example": {
                "folder_path": "docs/00-foundation",
                "stage_code": "00",
                "stage_name": "FOUNDATION",
                "is_auto_detected": True,
                "confidence": 0.95,
            }
        }


class SaveStageMappingsRequest(BaseModel):
    """Request to save stage mappings for a project."""

    project_id: UUID = Field(..., description="Project ID to save mappings for")
    stage_mappings: list[StageMappingItem] = Field(
        ..., description="List of stage mappings to save"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "project_id": "550e8400-e29b-41d4-a716-446655440000",
                "stage_mappings": [
                    {
                        "folder_path": "docs/00-foundation",
                        "stage_code": "00",
                        "stage_name": "FOUNDATION",
                        "is_auto_detected": True,
                        "confidence": 0.95,
                    },
                    {
                        "folder_path": "docs/01-planning",
                        "stage_code": "01",
                        "stage_name": "PLANNING",
                        "is_auto_detected": True,
                        "confidence": 0.90,
                    },
                ],
            }
        }


class SaveStageMappingsResponse(BaseModel):
    """Response after saving stage mappings."""

    project_id: UUID = Field(..., description="Project ID")
    mappings_saved: int = Field(..., description="Number of mappings saved")
    mappings: list[StageMappingItem] = Field(..., description="Saved mappings")

    class Config:
        json_schema_extra = {
            "example": {
                "project_id": "550e8400-e29b-41d4-a716-446655440000",
                "mappings_saved": 5,
                "mappings": [],
            }
        }


class GitHubConnectionStatus(BaseModel):
    """GitHub connection status for current user."""

    connected: bool = Field(..., description="Is GitHub connected")
    github_username: Optional[str] = Field(None, description="GitHub username")
    github_avatar: Optional[str] = Field(None, description="GitHub avatar URL")
    scopes: list[str] = Field(default_factory=list, description="Granted OAuth scopes")
    connected_at: Optional[datetime] = Field(None, description="Connection timestamp")
    rate_limit: Optional[GitHubRateLimitInfo] = Field(
        None, description="Current rate limit status"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "connected": True,
                "github_username": "developer",
                "github_avatar": "https://avatars.githubusercontent.com/u/12345",
                "scopes": ["read:user", "user:email", "repo"],
                "connected_at": "2025-01-01T00:00:00Z",
                "rate_limit": {
                    "limit": 5000,
                    "remaining": 4999,
                    "reset": "2025-01-01T01:00:00Z",
                    "used": 1,
                },
            }
        }
