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
        - framework_version: SDLC Framework version for compliance (Sprint 101)
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

    # Team (Sprint 70 - Teams Foundation)
    team_id = Column(
        UUID(as_uuid=True),
        ForeignKey("teams.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Parent team (NULL during migration or for standalone projects)"
    )

    # Project Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    # GitHub Integration (Sprint 15)
    github_repo_id = Column(Integer, nullable=True, index=True)
    github_repo_full_name = Column(String(500), nullable=True)
    github_sync_status = Column(String(50), nullable=True, default="pending")  # pending, syncing, synced, error
    github_synced_at = Column(DateTime, nullable=True)

    # Framework Version Tracking (Sprint 101 - SDLC 5.2.0 Compliance)
    # Tracks which SDLC Framework version this project was created/updated against
    framework_version = Column(
        String(20),
        nullable=False,
        default="5.2.0",
        server_default="5.2.0",
        comment="SDLC Framework version (e.g., 5.2.0) for compliance audits"
    )

    # Policy Pack Tier (Sprint 102 - 4-Tier Enforcement)
    # Determines policy enforcement level for the project
    policy_pack_tier = Column(
        String(20),
        nullable=False,
        default="PROFESSIONAL",
        server_default="PROFESSIONAL",
        comment="Policy tier: LITE, STANDARD, PROFESSIONAL, ENTERPRISE"
    )

    # EU AI Act Classification (Sprint 160 - EU AI Act Compliance)
    eu_ai_act_risk_level = Column(
        String(20),
        nullable=True,
        index=True,
        comment="EU AI Act risk classification: prohibited, high_risk, limited_risk, minimal_risk"
    )
    eu_ai_act_classified_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp of EU AI Act classification"
    )
    eu_ai_act_classified_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="User who performed EU AI Act classification"
    )

    # Data Residency (Sprint 186, ADR-063)
    # Storage-level region routing for MinIO/S3 buckets.
    # Valid values: 'VN' (Asia Pacific / default), 'EU' (Frankfurt, GDPR), 'US' (future).
    # DB remains single-region; only MinIO bucket selection is region-aware.
    data_region = Column(
        String(10),
        nullable=False,
        default="VN",
        server_default="VN",
        index=True,
        comment="MinIO/S3 storage region for this project: VN | EU | US",
    )

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    owner = relationship("User", back_populates="owned_projects", foreign_keys=[owner_id])
    eu_ai_act_classifier = relationship("User", foreign_keys=[eu_ai_act_classified_by])
    team = relationship("Team", back_populates="projects")  # Sprint 70 - Teams Foundation
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
    # SAST Scans (Sprint 69 - CTO Go-Live)
    sast_scans = relationship(
        "SASTScan", back_populates="project", cascade="all, delete-orphan"
    )
    # AGENTS.md Integration (Sprint 80)
    agents_md_files = relationship(
        "AgentsMdFile", back_populates="project", cascade="all, delete-orphan"
    )
    # Dynamic Context Overlays (Sprint 83)
    context_overlays = relationship(
        "ContextOverlay", back_populates="project", cascade="all, delete-orphan"
    )
    # Evidence Manifests (Sprint 83)
    evidence_manifests = relationship(
        "EvidenceManifest", back_populates="project", cascade="all, delete-orphan"
    )
    # Framework Version History (Sprint 103)
    framework_versions = relationship(
        "FrameworkVersion", back_populates="project", cascade="all, delete-orphan"
    )
    # Maturity Assessments (Sprint 104)
    maturity_assessments = relationship(
        "AgenticMaturityAssessment", back_populates="project", cascade="all, delete-orphan"
    )
    # Governance Submissions (Sprint 120 - Context Authority V2)
    governance_submissions = relationship(
        "GovernanceSubmission", back_populates="project", cascade="all, delete-orphan"
    )
    # Context Snapshots (Sprint 120 - Context Authority V2)
    context_snapshots = relationship(
        "ContextSnapshot", back_populates="project", cascade="all, delete-orphan"
    )
    # Governance Specifications (Sprint 118 - SPEC-0001 + SPEC-0002)
    governance_specifications = relationship(
        "GovernanceSpecification", back_populates="project", cascade="all, delete-orphan"
    )
    # Vibecoding Signals (Sprint 118 - Anti-Vibecoding Governance)
    vibecoding_signals = relationship(
        "VibecodingSignal", back_populates="project", cascade="all, delete-orphan"
    )
    # Vibecoding Index History (Sprint 118 - Anti-Vibecoding Governance)
    vibecoding_index_history = relationship(
        "VibecodingIndexHistory", back_populates="project", cascade="all, delete-orphan"
    )
    # Compliance Validation (Sprint 123 - SPEC-0013)
    compliance_scores = relationship(
        "ComplianceScore", back_populates="project", cascade="all, delete-orphan"
    )
    folder_collision_checks = relationship(
        "FolderCollisionCheck", back_populates="project", cascade="all, delete-orphan"
    )
    # GitHub Integration (Sprint 129 - ADR-044)
    github_repository = relationship(
        "GitHubRepository", back_populates="project", uselist=False, cascade="all, delete-orphan"
    )
    # VCR - Version Controlled Resolution (Sprint 151 - SASE Artifacts)
    vcrs = relationship(
        "VersionControlledResolution", back_populates="project", cascade="all, delete-orphan"
    )
    # Tier-Based Gate Approval (Sprint 161 - Phase 4 AUTHORIZATION)
    function_roles = relationship(
        "ProjectFunctionRole", back_populates="project", cascade="all, delete-orphan"
    )
    # Multi-Agent Team Engine (Sprint 176 - ADR-056)
    agent_definitions = relationship(
        "AgentDefinition", back_populates="project", cascade="all, delete-orphan"
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
