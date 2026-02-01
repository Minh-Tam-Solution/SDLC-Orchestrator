"""
GitHub Integration Schemas - Sprint 129

Pydantic schemas for GitHub API request/response validation.

Reference: ADR-044-GitHub-Integration-Strategy.md
"""
from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl


# ============================================================================
# Request Schemas
# ============================================================================

class GitHubLinkRequest(BaseModel):
    """Request schema for linking a GitHub repository to a project"""

    installation_id: UUID = Field(
        ...,
        description="Our GitHubInstallation UUID (not GitHub's installation_id)"
    )
    owner: str = Field(
        ...,
        description="Repository owner (user or organization)",
        example="acme-corp"
    )
    repo: str = Field(
        ...,
        description="Repository name",
        example="my-project"
    )


class GitHubCloneRequest(BaseModel):
    """Request schema for triggering a repository clone"""

    shallow: bool = Field(
        default=True,
        description="Use shallow clone (depth=1)"
    )
    force: bool = Field(
        default=False,
        description="Force re-clone even if already cloned"
    )


# ============================================================================
# Response Schemas
# ============================================================================

class GitHubInstallationResponse(BaseModel):
    """Response schema for GitHub App installation"""

    id: UUID = Field(..., description="Internal UUID")
    installation_id: int = Field(..., description="GitHub's installation ID")
    account_type: str = Field(..., description="'user' or 'organization'")
    account_login: str = Field(..., description="GitHub username or org name")
    account_avatar_url: Optional[str] = Field(None, description="Avatar URL")
    status: str = Field(..., description="Installation status (active, suspended, uninstalled)")
    installed_at: datetime
    repositories_count: Optional[int] = Field(None, description="Number of repos accessible")

    class Config:
        from_attributes = True


class GitHubInstallationsListResponse(BaseModel):
    """Response schema for listing user's GitHub installations"""

    installations: List[GitHubInstallationResponse]
    total_count: int


class GitHubRepoInfo(BaseModel):
    """Schema for repository info from GitHub API"""

    id: int = Field(..., description="GitHub's internal repo ID")
    name: str = Field(..., description="Repository name")
    full_name: str = Field(..., description="owner/name")
    owner: str = Field(..., description="Repository owner")
    description: Optional[str] = None
    private: bool = Field(default=False)
    default_branch: str = Field(default="main")
    html_url: str
    clone_url: Optional[str] = None
    size: Optional[int] = Field(None, description="Repository size in KB")
    language: Optional[str] = Field(None, description="Primary language")
    updated_at: Optional[datetime] = None


class GitHubRepositoriesListResponse(BaseModel):
    """Response schema for listing repositories in an installation"""

    repositories: List[GitHubRepoInfo]
    total_count: int
    page: int
    per_page: int
    has_more: bool


class GitHubRepositoryResponse(BaseModel):
    """Response schema for a linked GitHub repository"""

    id: UUID = Field(..., description="Internal UUID")
    installation_id: UUID = Field(..., description="Installation UUID")
    project_id: UUID = Field(..., description="Project UUID")
    github_repo_id: int = Field(..., description="GitHub's repo ID")
    owner: str
    name: str
    full_name: str
    default_branch: str
    is_private: bool
    html_url: Optional[str]

    # Clone status
    local_path: Optional[str]
    last_cloned_at: Optional[datetime]
    clone_status: str = Field(..., description="pending, cloning, cloned, failed")
    clone_error: Optional[str]

    # Audit
    connected_at: datetime
    connected_by: UUID

    class Config:
        from_attributes = True


class GitHubLinkResponse(BaseModel):
    """Response schema for linking/unlinking a repository"""

    message: str
    repository: GitHubRepositoryResponse


class GitHubCloneStatusResponse(BaseModel):
    """Response schema for clone status update"""

    message: str
    clone_status: str
    local_path: Optional[str]
    last_cloned_at: Optional[datetime]


class GitHubScanResult(BaseModel):
    """Response schema for local repository scan"""

    folders: List[str]
    files: List[str]
    total_folders: int
    total_files: int
    sdlc_config_found: bool
    docs_folder_exists: bool
    error: Optional[str] = None


# ============================================================================
# Webhook Schemas
# ============================================================================

class GitHubWebhookInstallation(BaseModel):
    """Schema for installation event webhook payload"""

    action: str = Field(..., description="created, deleted, suspend, unsuspend")
    installation: dict
    sender: dict


class GitHubWebhookPush(BaseModel):
    """Schema for push event webhook payload"""

    ref: str
    before: str
    after: str
    repository: dict
    pusher: dict
    commits: List[dict]


class GitHubWebhookPullRequest(BaseModel):
    """Schema for pull_request event webhook payload"""

    action: str
    number: int
    pull_request: dict
    repository: dict
    sender: dict
