"""
=========================================================================
Gate Model - Quality Gate Management (FR1)
SDLC Orchestrator - Stage 03 (BUILD)

Version: 1.1.0
Date: 2025-12-16
Status: ACTIVE - STAGE 03 (BUILD)
Authority: Backend Lead + CTO Approved
Foundation: Data Model v0.1 (9.8/10 quality), FR1 (Quality Gate Management)
Framework: SDLC 5.1.3 Complete Lifecycle

Purpose:
- Quality gate creation and lifecycle management
- Multi-approver workflow (CTO, CPO, CEO)
- Stage progression tracking (WHY → WHAT → BUILD...G9)
- Policy evaluation results storage

Design References:
- Data Model: docs/01-planning/03-Data-Model/Database-Schema.md
- Data Dictionary: docs/01-planning/03-Data-Model/Data-Dictionary.md
- FR1: docs/01-planning/01-Requirements/Functional-Requirements-Document.md

Gate Status Values (UPPERCASE - Source of Truth, Sprint 173 ADR-053):
- DRAFT: Gate created, no evaluation yet
- EVALUATED: Exit criteria evaluated against evidence
- EVALUATED_STALE: Evaluation invalidated by new evidence upload
- SUBMITTED: Submitted for approval review (was PENDING_APPROVAL)
- APPROVED: Passed all criteria
- REJECTED: Did not meet criteria (re-evaluate allowed)
- ARCHIVED: No longer active (lifecycle, not governance state)

SDLC 5.1.3 Gates:
- G0.1: Foundation Ready (WHY stage)
- G0.2: Solution Diversity (WHY stage)
- G1: Design Ready (WHAT stage)
- G2: Ship Ready (HOW stage)
- G3-G9: BUILD through GOVERN stages

Performance: Indexed for <200ms query response (p95)
Zero Mock Policy: Real SQLAlchemy model with all fields

Changelog:
- v1.1.0 (2025-12-16): Add Design References, document status values
- v1.0.0 (2025-11-28): Initial implementation
=========================================================================
"""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class Gate(Base):
    """
    Gate model for SDLC quality gates (G0, G1, G2...G9).

    Purpose (FR1):
        - Quality gate creation and lifecycle management
        - Multi-approver workflow (CTO, CPO, CEO)
        - Stage progression tracking (WHY → WHAT → BUILD...)
        - Policy evaluation results storage

    SDLC 4.9 Gates:
        - G0.1: Foundation Ready (WHY stage)
        - G0.2: Solution Diversity (WHY stage)
        - G1: Design Ready (WHAT stage)
        - G2: Ship Ready (HOW stage)
        - G3: Build Complete (BUILD stage)
        - G4: Test Complete (TEST stage)
        - G5: Deploy Ready (DEPLOY stage)
        - G6: Operate Ready (OPERATE stage)
        - G7: Integration Complete (INTEGRATE stage)
        - G8: Collaboration Ready (COLLABORATE stage)
        - G9: Governance Complete (GOVERN stage)

    Fields:
        - id: UUID primary key
        - gate_name: Human-readable name (e.g., "Q4 2025 E-commerce Platform - G1")
        - gate_type: SDLC 4.9 gate type (e.g., 'G1_DESIGN_READY')
        - stage: Current SDLC stage ('WHY', 'WHAT', 'BUILD', etc.)
        - project_id: Foreign key to Project
        - created_by: Foreign key to User (gate creator)
        - status: Gate status ('DRAFT', 'PENDING_APPROVAL', 'APPROVED', 'REJECTED', 'ARCHIVED')
        - exit_criteria: JSONB array of exit criteria
        - description: Gate description
        - approved_at: Approval timestamp
        - rejected_at: Rejection timestamp
        - archived_at: Archive timestamp
        - created_at: Gate creation timestamp
        - updated_at: Last update timestamp
        - deleted_at: Soft delete timestamp

    Relationships:
        - project: Many-to-One with Project model
        - creator: Many-to-One with User model
        - approvals: One-to-Many with GateApproval model
        - evidence: One-to-Many with GateEvidence model
        - policy_evaluations: One-to-Many with PolicyEvaluation model
        - stage_transitions: One-to-Many with StageTransition model

    Indexes:
        - project_id (B-tree) - Fast project gate lookup
        - created_by (B-tree) - Fast creator lookup
        - status (B-tree) - Active gate filtering
        - gate_type (B-tree) - Gate type filtering
        - created_at (B-tree) - Recent gates queries

    Usage Example:
        gate = Gate(
            gate_name="E-commerce Platform v2.0 - G1 Design Ready",
            gate_type="G1_DESIGN_READY",
            stage="WHAT",
            project_id=project.id,
            created_by=user.id,
            status="DRAFT",
            exit_criteria=[
                {"id": "FRD_COMPLETE", "description": "Functional Requirements Document complete"},
                {"id": "DATA_MODEL", "description": "Data Model v0.1 designed"}
            ]
        )
    """

    __tablename__ = "gates"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)

    # Gate Identity
    gate_name = Column(String(255), nullable=False)
    gate_type = Column(
        String(50), nullable=False, index=True
    )  # 'G1_DESIGN_READY', 'G2_SHIP_READY', etc.
    stage = Column(
        String(20), nullable=False, index=True
    )  # 'WHY', 'WHAT', 'BUILD', 'TEST', etc.

    # Project Relationship
    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Creator
    created_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Gate Status (Sprint 173 State Machine — ADR-053)
    # Valid: DRAFT, EVALUATED, EVALUATED_STALE, SUBMITTED, APPROVED, REJECTED, ARCHIVED
    status = Column(
        String(20),
        nullable=False,
        default="DRAFT",
        index=True,
    )

    # Exit Criteria (JSONB)
    exit_criteria = Column(
        JSONB, nullable=False, default=list
    )  # [{"id": "...", "description": "...", "met": false}]

    # Sprint 173: Exit criteria version for evidence snapshot binding
    exit_criteria_version = Column(
        UUID(as_uuid=True), default=uuid4, nullable=True
    )

    # Description
    description = Column(Text, nullable=True)

    # Status Timestamps
    evaluated_at = Column(DateTime, nullable=True)  # Sprint 173: Last evaluation timestamp
    approved_at = Column(DateTime, nullable=True)
    rejected_at = Column(DateTime, nullable=True)
    archived_at = Column(DateTime, nullable=True)

    # Audit Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    project = relationship("Project", back_populates="gates")
    creator = relationship("User", back_populates="created_gates")
    approvals = relationship(
        "GateApproval", back_populates="gate", cascade="all, delete-orphan"
    )
    evidence = relationship(
        "GateEvidence", back_populates="gate", cascade="all, delete-orphan"
    )
    policy_evaluations = relationship(
        "PolicyEvaluation", back_populates="gate", cascade="all, delete-orphan"
    )
    stage_transitions = relationship(
        "StageTransition", back_populates="gate", cascade="all, delete-orphan"
    )
    ai_requests = relationship("AIRequest", back_populates="gate")
    ai_evidence_drafts = relationship(
        "AIEvidenceDraft", back_populates="gate", cascade="all, delete-orphan"
    )
    # Tier-Based Gate Approval (Sprint 161 - Phase 4 AUTHORIZATION)
    decisions = relationship(
        "GateDecision", back_populates="gate", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Gate(id={self.id}, gate_name={self.gate_name}, status={self.status})>"

    @property
    def is_approved(self) -> bool:
        """Check if gate is approved."""
        return self.status == "APPROVED"

    @property
    def is_pending(self) -> bool:
        """Check if gate is pending approval (SUBMITTED status, Sprint 173)."""
        return self.status == "SUBMITTED"

    @property
    def is_draft(self) -> bool:
        """Check if gate is still in draft."""
        return self.status == "DRAFT"

    @property
    def is_evaluated(self) -> bool:
        """Check if gate has been evaluated (Sprint 173)."""
        return self.status == "EVALUATED"

    @property
    def is_evaluated_stale(self) -> bool:
        """Check if evaluation is stale due to new evidence (Sprint 173)."""
        return self.status == "EVALUATED_STALE"

    @property
    def is_rejected(self) -> bool:
        """Check if gate was rejected (re-evaluate allowed, Sprint 173)."""
        return self.status == "REJECTED"

    @property
    def all_criteria_met(self) -> bool:
        """Check if all exit criteria are met"""
        if not self.exit_criteria:
            return False
        return all(criterion.get("met", False) for criterion in self.exit_criteria)

    @property
    def criteria_met_count(self) -> int:
        """Count how many criteria are met"""
        if not self.exit_criteria:
            return 0
        return sum(1 for criterion in self.exit_criteria if criterion.get("met", False))

    @property
    def criteria_total_count(self) -> int:
        """Total number of exit criteria"""
        return len(self.exit_criteria) if self.exit_criteria else 0
