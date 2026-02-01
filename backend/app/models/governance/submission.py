"""
=========================================================================
Governance Submission Model - Central Submission Tracking
SDLC Orchestrator - Sprint 108 (Governance Foundation)

Version: 1.0.0
Date: January 27, 2026
Status: ACTIVE - Sprint 108 Day 1
Authority: CTO + Backend Lead Approved
Framework: SDLC 5.3.0 Quality Assurance System

Purpose:
- Track all code submissions for governance validation
- Store Vibecoding Index (0-100)
- Route submissions based on index (Green/Yellow/Orange/Red)
- Link to validation results and evidence

Performance Targets:
- Query by project_id: <50ms (P95)
- Query by status: <30ms (P95)
- Query by vibecoding_index: <20ms (P95)

Retention: 2 years (archivable to cold storage)
Zero Mock Policy: Real SQLAlchemy model with all fields
=========================================================================
"""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class GovernanceSubmission(Base):
    """
    Central table for all code submissions requiring governance validation.

    Stores:
    - Submission metadata (PR, commit, branch)
    - Vibecoding Index (0-100)
    - Routing decision (auto_approve, tech_lead, ceo_should, ceo_must)
    - Validation results

    Indexes:
    - project_id: Fast project lookup
    - status: Active/pending filtering
    - submitted_at: Chronological queries
    - vibecoding_index: Score-based routing
    """

    __tablename__ = "governance_submissions"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Submission Metadata
    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    pr_number = Column(Integer, nullable=True)
    task_id = Column(
        UUID(as_uuid=True),
        ForeignKey("backlog_items.id", ondelete="SET NULL"),
        nullable=True,
    )
    branch_name = Column(String(255), nullable=False)
    commit_sha = Column(String(40), nullable=False)

    # Submitter Info
    submitted_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    submitted_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Submission Content
    diff_summary = Column(Text, nullable=True)
    files_changed = Column(JSONB, nullable=False, default=list)
    total_lines_added = Column(Integer, nullable=False, default=0)
    total_lines_deleted = Column(Integer, nullable=False, default=0)

    # Governance Status
    status = Column(
        String(50),
        nullable=False,
        default="pending",
        index=True,
    )  # pending | validating | passed | failed | escalated

    vibecoding_index = Column(
        Numeric(5, 2),
        nullable=True,
        index=True,
    )  # 0.00 to 100.00

    routing = Column(
        String(50),
        nullable=True,
    )  # auto_approve | tech_lead_review | ceo_should_review | ceo_must_review

    # Validation Results
    passed_checks = Column(JSONB, nullable=True)
    failed_checks = Column(JSONB, nullable=True)
    validation_completed_at = Column(DateTime(timezone=True), nullable=True)

    # Signal Scores (5 signals)
    signal_architectural_smell = Column(Numeric(5, 2), nullable=True)
    signal_abstraction_complexity = Column(Numeric(5, 2), nullable=True)
    signal_ai_dependency_ratio = Column(Numeric(5, 2), nullable=True)
    signal_change_surface_area = Column(Numeric(5, 2), nullable=True)
    signal_drift_velocity = Column(Numeric(5, 2), nullable=True)

    # MAX CRITICALITY Override
    critical_path_override = Column(Boolean, nullable=False, default=False)
    critical_path_reason = Column(Text, nullable=True)

    # Performance Tracking
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
    project = relationship("Project", back_populates="governance_submissions")
    submitted_by_user = relationship("User", foreign_keys=[submitted_by])
    rejections = relationship(
        "GovernanceRejection",
        back_populates="submission",
        cascade="all, delete-orphan",
    )
    evidence_entries = relationship(
        "EvidenceVaultEntry",
        back_populates="submission",
        cascade="all, delete-orphan",
    )
    context_authority = relationship(
        "ContextAuthority",
        back_populates="submission",
        uselist=False,
        cascade="all, delete-orphan",
    )
    ai_attestation = relationship(
        "AIAttestation",
        back_populates="submission",
        uselist=False,
        cascade="all, delete-orphan",
    )
    contract_violations = relationship(
        "ContractViolation",
        back_populates="submission",
        cascade="all, delete-orphan",
    )
    exception = relationship(
        "GovernanceException",
        back_populates="submission",
        uselist=False,
        cascade="all, delete-orphan",
    )
    escalations = relationship(
        "EscalationLog",
        back_populates="submission",
        cascade="all, delete-orphan",
    )
    # Context Snapshots (Sprint 120 - Context Authority V2)
    context_snapshots = relationship(
        "ContextSnapshot",
        back_populates="submission",
        cascade="all, delete-orphan",
    )

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "vibecoding_index >= 0 AND vibecoding_index <= 100",
            name="check_vibecoding_index_range",
        ),
    )

    def __repr__(self) -> str:
        return f"GovernanceSubmission(id={self.id}, status={self.status}, index={self.vibecoding_index})"
