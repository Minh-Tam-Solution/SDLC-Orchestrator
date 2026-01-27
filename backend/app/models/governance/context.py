"""
=========================================================================
Context Models - Context Authority and Snapshots
SDLC Orchestrator - Sprint 108 (Governance Foundation)

Version: 1.0.0
Date: January 27, 2026
Status: ACTIVE - Sprint 108 Day 1
Authority: CTO + Backend Lead Approved
Framework: SDLC 5.3.0 Quality Assurance System

Purpose:
- Context Authority: Validation results for context linkage
- Context Snapshot: Historical context state (ADRs, AGENTS.md)

Principle 3: NO CHANGE WITHOUT TRACEABILITY
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
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class ContextSnapshot(Base):
    """
    Historical context state for reproducible validation.

    Captures:
    - ADRs at a specific commit
    - AGENTS.md content
    - Design documents
    - Module registry
    """

    __tablename__ = "context_snapshots"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Project Context
    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    commit_sha = Column(String(40), nullable=False, index=True)

    # Snapshot Content
    adrs = Column(JSONB, nullable=False, default=list)
    agents_md_content = Column(Text, nullable=True)
    agents_md_hash = Column(String(64), nullable=True)
    design_docs = Column(JSONB, nullable=True)
    module_registry = Column(JSONB, nullable=True)

    # Snapshot Metadata
    snapshot_reason = Column(String(255), nullable=True)
    snapshot_size_bytes = Column(BigInteger, nullable=True)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )

    # Relationships
    project = relationship("Project")

    def __repr__(self) -> str:
        return f"ContextSnapshot(id={self.id}, commit={self.commit_sha[:8]})"


class ContextAuthority(Base):
    """
    Context linkage validation results.

    Validates:
    - ADR linkage: Every module must reference at least one ADR
    - Design doc reference: New features must have design document
    - AGENTS.md freshness: Should be updated within 7 days
    - Module annotation consistency: Header matches directory
    """

    __tablename__ = "context_authorities"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Foreign Keys
    submission_id = Column(
        UUID(as_uuid=True),
        ForeignKey("governance_submissions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Context Validation Results
    has_adr_linkage = Column(Boolean, nullable=False, default=False)
    linked_adrs = Column(JSONB, nullable=True)

    has_design_doc = Column(Boolean, nullable=False, default=False)
    linked_design_docs = Column(JSONB, nullable=True)

    agents_md_freshness_days = Column(Integer, nullable=True)
    agents_md_stale = Column(Boolean, nullable=False, default=False)

    module_annotation_consistent = Column(Boolean, nullable=False, default=True)
    module_annotation_issues = Column(JSONB, nullable=True)

    # Validation Status
    validation_status = Column(
        String(50),
        nullable=False,
        default="pending",
        index=True,
    )  # pending | passed | failed
    validation_errors = Column(JSONB, nullable=True)

    # Context Snapshot Reference
    context_snapshot_id = Column(
        UUID(as_uuid=True),
        ForeignKey("context_snapshots.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Performance
    validation_duration_ms = Column(Integer, nullable=True)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    submission = relationship("GovernanceSubmission", back_populates="context_authority")
    project = relationship("Project")
    context_snapshot = relationship("ContextSnapshot")

    def __repr__(self) -> str:
        return f"ContextAuthority(id={self.id}, status={self.validation_status})"
