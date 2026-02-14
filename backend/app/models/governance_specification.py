"""
SQLAlchemy models for Sprint 118 Governance System v2.0

PART 1: SPECIFICATION MANAGEMENT (7 models)
- GovernanceSpecification
- SpecVersion
- SpecFrontmatterMetadata
- SpecFunctionalRequirement
- SpecAcceptanceCriterion
- SpecImplementationPhase
- SpecCrossReference

References:
- D1: docs/02-design/02-System-Architecture/Database-Schema-Governance-v2.md
- Migration: backend/alembic/versions/s118_001_governance_v2_tables.py
- SPEC-0002: Specification Standard (Framework 6.0.5)
"""
from datetime import datetime
from typing import Optional, List
from uuid import UUID, uuid4

from sqlalchemy import (
    Column,
    String,
    Integer,
    Boolean,
    DateTime,
    Text,
    ForeignKey,
    Index,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base_class import Base


class GovernanceSpecification(Base):
    """
    Master table for all SDLC specifications (ADRs, specs, policies).

    SPEC-0002 Compliance:
    - YAML frontmatter in separate table (spec_frontmatter_metadata)
    - Version history tracked (spec_versions)
    - SHA256 content hashing for change detection

    Tier Classification:
    - LITE: Minimal requirements
    - STANDARD: Normal requirements
    - PROFESSIONAL: Enhanced requirements
    - ENTERPRISE: Full requirements
    """
    __tablename__ = "governance_specifications"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        comment="Specification UUID",
    )
    project_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Project owning this specification",
    )
    spec_number: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        comment="Specification identifier (e.g., SPEC-0001, ADR-041)",
    )
    spec_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Type: technical_spec, adr, policy, requirement, design_doc",
    )
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Human-readable specification title",
    )
    file_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        unique=True,
        comment="Relative path from project root (e.g., docs/02-design/14-Technical-Specs/SPEC-0001.md)",
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default="draft",
        index=True,
        comment="Status: draft, review, approved, deprecated",
    )
    tier: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default="STANDARD",
        index=True,
        comment="Tier: LITE, STANDARD, PROFESSIONAL, ENTERPRISE",
    )
    version: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default="1.0.0",
        comment="Semantic version (e.g., 1.0.0, 2.1.0)",
    )
    content_hash: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        comment="SHA256 hash of specification content for change detection",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
        comment="Specification creation timestamp",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        index=True,
        comment="Last modification timestamp",
    )
    created_by_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="User who created this specification",
    )
    approved_by_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="User who approved this specification",
    )
    approved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Approval timestamp",
    )

    # Relationships
    project = relationship("Project", back_populates="governance_specifications")
    created_by = relationship("User", foreign_keys=[created_by_id])
    approved_by = relationship("User", foreign_keys=[approved_by_id])

    versions = relationship("SpecVersion", back_populates="specification", cascade="all, delete-orphan")
    frontmatter = relationship("SpecFrontmatterMetadata", back_populates="specification", uselist=False, cascade="all, delete-orphan")
    functional_requirements = relationship("SpecFunctionalRequirement", back_populates="specification", cascade="all, delete-orphan")
    acceptance_criteria = relationship("SpecAcceptanceCriterion", back_populates="specification", cascade="all, delete-orphan")
    implementation_phases = relationship("SpecImplementationPhase", back_populates="specification", cascade="all, delete-orphan")
    source_cross_references = relationship("SpecCrossReference", foreign_keys="SpecCrossReference.source_spec_id", back_populates="source_specification", cascade="all, delete-orphan")
    target_cross_references = relationship("SpecCrossReference", foreign_keys="SpecCrossReference.target_spec_id", back_populates="target_specification")
    validation_results = relationship("SpecValidationResult", back_populates="specification", cascade="all, delete-orphan")

    # Composite index
    __table_args__ = (
        Index("idx_governance_specifications_project_type_status", "project_id", "spec_type", "status"),
    )

    def __repr__(self) -> str:
        return f"<GovernanceSpecification(spec_number='{self.spec_number}', title='{self.title}', status='{self.status}')>"


class SpecVersion(Base):
    """
    Version history tracking for specifications.

    Immutable audit trail - versions are never updated, only created.
    Enables rollback to previous specification versions.
    """
    __tablename__ = "spec_versions"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    spec_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("governance_specifications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Reference to parent specification",
    )
    version: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Version number (e.g., 1.0.0, 2.1.0)",
    )
    content_snapshot: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Full content snapshot at this version",
    )
    content_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="SHA256 hash of content_snapshot",
    )
    change_summary: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Human-readable summary of changes from previous version",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
        comment="Version creation timestamp",
    )
    created_by_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="User who created this version",
    )

    # Relationships
    specification = relationship("GovernanceSpecification", back_populates="versions")
    created_by = relationship("User")

    # Unique constraint: One version per spec
    __table_args__ = (
        UniqueConstraint("spec_id", "version", name="idx_spec_versions_spec_version_unique"),
    )

    def __repr__(self) -> str:
        return f"<SpecVersion(spec_id={self.spec_id}, version='{self.version}')>"


class SpecFrontmatterMetadata(Base):
    """
    YAML frontmatter metadata (SPEC-0002 compliance).

    Framework 6.0.5 requires:
    - authors (MANDATORY)
    - reviewers, stakeholders (RECOMMENDED)
    - tags, dependencies, supersedes (OPTIONAL)

    One-to-one relationship with GovernanceSpecification.
    """
    __tablename__ = "spec_frontmatter_metadata"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    spec_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("governance_specifications.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        comment="One-to-one relationship with specification",
    )
    authors: Mapped[Optional[list]] = mapped_column(
        JSONB,
        nullable=True,
        comment='Array of author names/emails (MANDATORY per SPEC-0002)',
    )
    reviewers: Mapped[Optional[list]] = mapped_column(
        JSONB,
        nullable=True,
        comment='Array of reviewer names/emails',
    )
    stakeholders: Mapped[Optional[list]] = mapped_column(
        JSONB,
        nullable=True,
        comment='Array of stakeholder names/roles',
    )
    tags: Mapped[Optional[list]] = mapped_column(
        JSONB,
        nullable=True,
        comment='Array of classification tags',
    )
    dependencies: Mapped[Optional[list]] = mapped_column(
        JSONB,
        nullable=True,
        comment='Array of dependent spec numbers (e.g., ["SPEC-0001", "ADR-041"])',
    )
    supersedes: Mapped[Optional[list]] = mapped_column(
        JSONB,
        nullable=True,
        comment='Array of superseded spec numbers',
    )
    related_specs: Mapped[Optional[list]] = mapped_column(
        JSONB,
        nullable=True,
        comment='Array of related spec numbers',
    )
    custom_fields: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment='Additional custom YAML fields',
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    specification = relationship("GovernanceSpecification", back_populates="frontmatter")

    # GIN indexes for JSONB array searches
    __table_args__ = (
        Index("idx_spec_frontmatter_tags_gin", "tags", postgresql_using="gin"),
        Index("idx_spec_frontmatter_dependencies_gin", "dependencies", postgresql_using="gin"),
    )

    def __repr__(self) -> str:
        return f"<SpecFrontmatterMetadata(spec_id={self.spec_id}, authors={self.authors})>"


class SpecFunctionalRequirement(Base):
    """
    Functional requirements extracted from specifications.

    Supports:
    - FR (Functional Requirements)
    - NFR (Non-Functional Requirements)
    - Security, Performance, Scalability requirements
    """
    __tablename__ = "spec_functional_requirements"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    spec_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("governance_specifications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Parent specification",
    )
    requirement_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Requirement identifier (e.g., FR-001, NFR-005)",
    )
    requirement_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        comment="Type: functional, non_functional, security, performance",
    )
    priority: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default="MEDIUM",
        index=True,
        comment="Priority: CRITICAL, HIGH, MEDIUM, LOW",
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Full requirement description",
    )
    acceptance_criteria: Mapped[Optional[list]] = mapped_column(
        JSONB,
        nullable=True,
        comment='Array of acceptance criteria',
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default="pending",
        index=True,
        comment="Status: pending, in_progress, completed, deferred",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    specification = relationship("GovernanceSpecification", back_populates="functional_requirements")

    # Composite index
    __table_args__ = (
        Index("idx_spec_functional_requirements_spec_type_priority", "spec_id", "requirement_type", "priority"),
    )

    def __repr__(self) -> str:
        return f"<SpecFunctionalRequirement(requirement_id='{self.requirement_id}', type='{self.requirement_type}', priority='{self.priority}')>"


class SpecAcceptanceCriterion(Base):
    """
    Detailed acceptance criteria for specifications.

    Testable conditions that must be met for specification approval.
    Tracks validation status and evidence links.
    """
    __tablename__ = "spec_acceptance_criteria"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    spec_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("governance_specifications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Parent specification",
    )
    criterion_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Criterion identifier (e.g., AC-001)",
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Detailed acceptance criterion",
    )
    validation_method: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="How to validate: unit_test, integration_test, manual_review, performance_test",
    )
    is_met: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="false",
        index=True,
        comment="Whether criterion is currently met",
    )
    validated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When criterion was validated",
    )
    validated_by_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="User who validated this criterion",
    )
    evidence_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Link to validation evidence (test report, PR, etc.)",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    specification = relationship("GovernanceSpecification", back_populates="acceptance_criteria")
    validated_by = relationship("User")

    def __repr__(self) -> str:
        return f"<SpecAcceptanceCriterion(criterion_id='{self.criterion_id}', is_met={self.is_met})>"


class SpecImplementationPhase(Base):
    """
    Implementation phases breakdown from specifications.

    Maps to D5 planning (Implementation-Phases-Governance-v2.md).
    Tracks phase dependencies, deliverables, and status.
    """
    __tablename__ = "spec_implementation_phases"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    spec_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("governance_specifications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Parent specification",
    )
    phase_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Phase sequence number (1, 2, 3...)",
    )
    phase_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Phase name (e.g., Database Migration, API Implementation)",
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Detailed phase description",
    )
    estimated_duration_days: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Estimated duration in days",
    )
    dependencies: Mapped[Optional[list]] = mapped_column(
        JSONB,
        nullable=True,
        comment='Array of prerequisite phase numbers',
    )
    deliverables: Mapped[Optional[list]] = mapped_column(
        JSONB,
        nullable=True,
        comment='Array of deliverable descriptions',
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default="not_started",
        index=True,
        comment="Status: not_started, in_progress, completed, blocked",
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Phase start timestamp",
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Phase completion timestamp",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    specification = relationship("GovernanceSpecification", back_populates="implementation_phases")

    # Unique constraint: One phase number per spec
    __table_args__ = (
        UniqueConstraint("spec_id", "phase_number", name="idx_spec_implementation_phases_spec_phase_unique"),
    )

    def __repr__(self) -> str:
        return f"<SpecImplementationPhase(phase_number={self.phase_number}, phase_name='{self.phase_name}', status='{self.status}')>"


class SpecCrossReference(Base):
    """
    Cross-reference links between specifications.

    Creates graph structure for specification relationships:
    - depends_on: This spec requires another spec
    - supersedes: This spec replaces another spec
    - related_to: This spec is related to another spec
    - implements: This spec implements another spec
    - references: This spec mentions another spec
    """
    __tablename__ = "spec_cross_references"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    source_spec_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("governance_specifications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Source specification (from)",
    )
    target_spec_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("governance_specifications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Target specification (to)",
    )
    reference_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Type: depends_on, supersedes, related_to, implements, references",
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Optional description of relationship",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Relationships
    source_specification = relationship("GovernanceSpecification", foreign_keys=[source_spec_id], back_populates="source_cross_references")
    target_specification = relationship("GovernanceSpecification", foreign_keys=[target_spec_id], back_populates="target_cross_references")

    # Composite index for graph queries
    __table_args__ = (
        Index("idx_spec_cross_references_source_target", "source_spec_id", "target_spec_id", "reference_type"),
    )

    def __repr__(self) -> str:
        return f"<SpecCrossReference(source={self.source_spec_id}, target={self.target_spec_id}, type='{self.reference_type}')>"
