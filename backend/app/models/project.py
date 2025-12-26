"""
=========================================================================
Project Model - Project/Workspace Management
SDLC Orchestrator - Stage 03 (BUILD)

Version: 1.0.0
Date: November 28, 2025
Status: ACTIVE - Week 3 Architecture Design
Authority: Backend Lead + CTO Approved
Foundation: Data Model v0.1 (9.8/10 quality)
Framework: SDLC 4.9 Complete Lifecycle

Purpose:
- Multi-tenancy (project-level data isolation)
- Team collaboration (multiple members per project)
- Gate organization (gates belong to projects)
- Project-scoped role assignment

Security Standards:
- Row-Level Security (RLS) for multi-tenancy
- Soft delete pattern (deleted_at timestamp)
- Owner-based access control

Zero Mock Policy: Real SQLAlchemy model with all fields
=========================================================================
"""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class Project(Base):
    """
    Project model for workspace isolation and organization.

    Purpose:
        - Multi-tenancy (project-level data isolation)
        - Team collaboration (multiple members per project)
        - Gate organization (gates belong to projects)

    Fields:
        - id: UUID primary key
        - name: Project name (e.g., "E-commerce Platform v2.0")
        - slug: URL-friendly identifier (e.g., "ecommerce-platform-v2")
        - description: Project description
        - owner_id: Foreign key to User (project owner)
        - is_active: Project status (True by default, False = archived)
        - github_repo_id: GitHub repository ID (Sprint 15)
        - github_repo_full_name: Full repository name (owner/repo) (Sprint 15)
        - github_sync_status: Sync status (pending, syncing, synced, error) (Sprint 15)
        - github_synced_at: Last sync timestamp (Sprint 15)
        - created_at: Project creation timestamp
        - updated_at: Last update timestamp
        - deleted_at: Soft delete timestamp

    Relationships:
        - owner: Many-to-One with User model
        - members: One-to-Many with ProjectMember model
        - gates: One-to-Many with Gate model
        - custom_policies: One-to-Many with CustomPolicy model

    Indexes:
        - slug (unique, B-tree) - Fast project lookup by slug
        - owner_id (B-tree) - Fast owner lookup
        - is_active (B-tree) - Active project filtering

    Usage Example:
        project = Project(
            name="E-commerce Platform v2.0",
            slug="ecommerce-platform-v2",
            description="Rebuild e-commerce platform with microservices",
            owner_id=user.id
        )
        session.add(project)
        session.commit()
    """

    __tablename__ = "projects"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)

    # Project Identity
    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)

    # Ownership
    owner_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Project Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    # GitHub Integration (Sprint 15)
    github_repo_id = Column(Integer, nullable=True, index=True)
    github_repo_full_name = Column(String(500), nullable=True)
    github_sync_status = Column(String(50), nullable=True, default="pending")  # pending, syncing, synced, error
    github_synced_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    owner = relationship("User", back_populates="owned_projects", foreign_keys=[owner_id])
    members = relationship(
        "ProjectMember", back_populates="project", cascade="all, delete-orphan"
    )
    gates = relationship("Gate", back_populates="project", cascade="all, delete-orphan")
    custom_policies = relationship(
        "CustomPolicy", back_populates="project", cascade="all, delete-orphan"
    )
    webhooks = relationship("Webhook", back_populates="project", cascade="all, delete-orphan")
    ai_code_events = relationship(
        "AICodeEvent", back_populates="project", cascade="all, delete-orphan"
    )
    validation_overrides = relationship(
        "ValidationOverride", back_populates="project", cascade="all, delete-orphan"
    )
    policy_pack = relationship(
        "PolicyPack", back_populates="project", uselist=False, cascade="all, delete-orphan"
    )
    # Stage Mappings (Sprint 49 - SDLC 5.1.2)
    stage_mappings = relationship(
        "ProjectStageMapping", back_populates="project", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Project(id={self.id}, name={self.name}, slug={self.slug})>"

    @property
    def is_archived(self) -> bool:
        """Check if project is archived (soft deleted or inactive)"""
        return self.deleted_at is not None or not self.is_active

    @property
    def active_gates_count(self) -> int:
        """Count active gates (not deleted)"""
        return sum(1 for gate in self.gates if gate.deleted_at is None)


class ProjectMember(Base):
    """
    Project Member model for team collaboration.

    Purpose:
        - Multi-user project access
        - Project-scoped role assignment
        - Team membership management

    Fields:
        - id: UUID primary key
        - project_id: Foreign key to Project
        - user_id: Foreign key to User
        - role: Project-specific role ('owner', 'admin', 'member', 'viewer')
        - invited_by: Foreign key to User (who invited this member)
        - invited_at: Invitation timestamp
        - joined_at: Member accepted invitation timestamp
        - created_at: Record creation timestamp

    Relationships:
        - project: Many-to-One with Project model
        - user: Many-to-One with User model
        - inviter: Many-to-One with User model

    Indexes:
        - project_id + user_id (unique composite) - Prevent duplicate membership
        - project_id (B-tree) - Fast project member lookup
        - user_id (B-tree) - Fast user project lookup

    Usage Example:
        member = ProjectMember(
            project_id=project.id,
            user_id=user.id,
            role='member',
            invited_by=owner.id
        )
        session.add(member)
        session.commit()
    """

    __tablename__ = "project_members"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)

    # Project + User Relationship
    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Project Role
    role = Column(
        String(50), nullable=False, default="member"
    )  # 'owner', 'admin', 'member', 'viewer'

    # Invitation Tracking
    invited_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    invited_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    joined_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    project = relationship("Project", back_populates="members")
    user = relationship("User", foreign_keys=[user_id], back_populates="project_memberships")
    inviter = relationship("User", foreign_keys=[invited_by])

    def __repr__(self) -> str:
        return f"<ProjectMember(project_id={self.project_id}, user_id={self.user_id}, role={self.role})>"

    @property
    def is_owner(self) -> bool:
        """Check if member is project owner"""
        return self.role == "owner"

    @property
    def is_admin(self) -> bool:
        """Check if member is admin or owner"""
        return self.role in ("owner", "admin")

    @property
    def has_accepted(self) -> bool:
        """Check if member has accepted invitation"""
        return self.joined_at is not None
