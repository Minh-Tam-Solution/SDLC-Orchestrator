"""
=========================================================================
GitHub Integration Models - Sprint 129
SDLC Orchestrator - Stage 04 (BUILD)

Version: 1.0.0
Date: January 31, 2026
Status: ACTIVE
Authority: Backend Lead + CTO Approved
Reference: ADR-044-GitHub-Integration-Strategy.md
Framework: SDLC 5.3.0

Purpose:
- GitHub App installation tracking
- Project-repository linking
- Clone status management
- Multi-tenant isolation via installation_id

Security Standards:
- Installation tokens NOT stored (JWT on-demand)
- Multi-tenant isolation via installation scoping
- Audit trail (who connected, when)

Zero Mock Policy: Real SQLAlchemy models with all fields
=========================================================================
"""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    String,
    Text,
    CheckConstraint,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class InstallationStatus:
    """GitHub App installation status enum"""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    UNINSTALLED = "uninstalled"


class CloneStatus:
    """Repository clone status enum"""
    PENDING = "pending"
    CLONING = "cloning"
    CLONED = "cloned"
    FAILED = "failed"


class GitHubInstallation(Base):
    """
    GitHub App installation tracking.

    Purpose:
        - Track GitHub App installations across users/organizations
        - Multi-tenant isolation (each team has separate installations)
        - Support webhook events (installation created/deleted/suspended)

    Fields:
        - id: UUID primary key (internal)
        - installation_id: GitHub's installation ID (external, unique)
        - account_type: 'user' or 'organization'
        - account_login: GitHub username or org name
        - account_avatar_url: GitHub avatar URL
        - installed_by: User who installed the app
        - status: active, suspended, uninstalled
        - installed_at, uninstalled_at, suspended_at: timestamps

    Relationships:
        - installer: User who installed the GitHub App
        - repositories: One-to-Many with GitHubRepository

    Usage Example:
        installation = GitHubInstallation(
            installation_id=12345678,
            account_type='organization',
            account_login='acme-corp',
            installed_by=user.id
        )
        session.add(installation)
        session.commit()
    """

    __tablename__ = "github_installations"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)

    # GitHub Installation Identity
    installation_id = Column(
        BigInteger,
        nullable=False,
        unique=True,
        index=True,
        comment="GitHub App installation ID"
    )
    account_type = Column(
        String(20),
        nullable=False,
        comment="user or organization"
    )
    account_login = Column(
        String(255),
        nullable=False,
        comment="GitHub username or org name"
    )
    account_avatar_url = Column(
        String(500),
        nullable=True,
        comment="GitHub avatar URL"
    )

    # Ownership
    installed_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    # Status
    status = Column(
        String(20),
        nullable=False,
        default=InstallationStatus.ACTIVE,
        index=True
    )

    # Timestamps
    installed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    uninstalled_at = Column(DateTime, nullable=True)
    suspended_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    installer = relationship("User", foreign_keys=[installed_by], lazy="joined")
    repositories = relationship(
        "GitHubRepository",
        back_populates="installation",
        cascade="all, delete-orphan"
    )

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "account_type IN ('user', 'organization')",
            name="valid_account_type"
        ),
        Index(
            "idx_github_installation_active",
            "status",
            postgresql_where="status = 'active'"
        ),
    )

    def __repr__(self) -> str:
        return f"<GitHubInstallation(id={self.id}, installation_id={self.installation_id}, account={self.account_login})>"

    @property
    def is_active(self) -> bool:
        """Check if installation is active"""
        return self.status == InstallationStatus.ACTIVE

    @property
    def is_organization(self) -> bool:
        """Check if installation is for an organization"""
        return self.account_type == "organization"

    def suspend(self) -> None:
        """Mark installation as suspended"""
        self.status = InstallationStatus.SUSPENDED
        self.suspended_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def unsuspend(self) -> None:
        """Reactivate suspended installation"""
        self.status = InstallationStatus.ACTIVE
        self.suspended_at = None
        self.updated_at = datetime.utcnow()

    def uninstall(self) -> None:
        """Mark installation as uninstalled"""
        self.status = InstallationStatus.UNINSTALLED
        self.uninstalled_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()


class GitHubRepository(Base):
    """
    Project-GitHub repository link.

    Purpose:
        - Link SDLC Orchestrator projects to GitHub repositories
        - Track clone status for gap analysis
        - One project = one repo (unique constraint)

    Fields:
        - id: UUID primary key
        - installation_id: FK to GitHubInstallation
        - project_id: FK to Project
        - github_repo_id: GitHub's internal repo ID
        - owner, name, full_name: Repository identity
        - default_branch: Default branch name
        - is_private: Private repository flag
        - html_url: GitHub web URL
        - local_path: Path to local clone
        - clone_status: pending, cloning, cloned, failed
        - clone_error: Last clone error message
        - connected_at, connected_by: Audit trail

    Relationships:
        - installation: Many-to-One with GitHubInstallation
        - project: Many-to-One with Project
        - connector: User who connected the repo

    Usage Example:
        github_repo = GitHubRepository(
            installation_id=installation.id,
            project_id=project.id,
            github_repo_id=987654321,
            owner='acme-corp',
            name='my-project',
            full_name='acme-corp/my-project',
            connected_by=user.id
        )
        session.add(github_repo)
        session.commit()
    """

    __tablename__ = "github_repositories"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)

    # Installation + Project links
    installation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("github_installations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,  # One project = one repo
        index=True
    )

    # GitHub Repository Identity
    github_repo_id = Column(
        BigInteger,
        nullable=False,
        unique=True,  # One repo can only be linked once
        index=True,
        comment="GitHub internal repo ID"
    )
    owner = Column(String(255), nullable=False, comment="Repo owner (user/org)")
    name = Column(String(255), nullable=False, comment="Repo name")
    full_name = Column(String(512), nullable=False, index=True, comment="owner/name")
    default_branch = Column(String(100), nullable=False, default="main")
    is_private = Column(Boolean, nullable=False, default=False)
    html_url = Column(String(500), nullable=True, comment="GitHub web URL")

    # Clone Tracking
    local_path = Column(Text, nullable=True, comment="Path to local clone")
    last_cloned_at = Column(DateTime, nullable=True)
    clone_status = Column(
        String(20),
        nullable=False,
        default=CloneStatus.PENDING,
        index=True
    )
    clone_error = Column(Text, nullable=True, comment="Last clone error message")

    # Audit Trail
    connected_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    connected_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False
    )
    disconnected_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    installation = relationship("GitHubInstallation", back_populates="repositories", lazy="joined")
    project = relationship("Project", back_populates="github_repository", lazy="joined")
    connector = relationship("User", foreign_keys=[connected_by], lazy="joined")

    def __repr__(self) -> str:
        return f"<GitHubRepository(id={self.id}, full_name={self.full_name}, project_id={self.project_id})>"

    @property
    def is_cloned(self) -> bool:
        """Check if repository is successfully cloned"""
        return self.clone_status == CloneStatus.CLONED

    @property
    def is_connected(self) -> bool:
        """Check if repository is still connected (not disconnected)"""
        return self.disconnected_at is None

    def start_clone(self, local_path: str) -> None:
        """Mark clone as started"""
        self.clone_status = CloneStatus.CLONING
        self.local_path = local_path
        self.clone_error = None
        self.updated_at = datetime.utcnow()

    def complete_clone(self) -> None:
        """Mark clone as completed successfully"""
        self.clone_status = CloneStatus.CLONED
        self.last_cloned_at = datetime.utcnow()
        self.clone_error = None
        self.updated_at = datetime.utcnow()

    def fail_clone(self, error_message: str) -> None:
        """Mark clone as failed with error message"""
        self.clone_status = CloneStatus.FAILED
        self.clone_error = error_message
        self.updated_at = datetime.utcnow()

    def disconnect(self) -> None:
        """Disconnect repository from project"""
        self.disconnected_at = datetime.utcnow()
        self.clone_status = CloneStatus.PENDING
        self.local_path = None
        self.updated_at = datetime.utcnow()

    def reset_clone_status(self) -> None:
        """Reset clone status to pending (for re-clone)"""
        self.clone_status = CloneStatus.PENDING
        self.clone_error = None
        self.updated_at = datetime.utcnow()
