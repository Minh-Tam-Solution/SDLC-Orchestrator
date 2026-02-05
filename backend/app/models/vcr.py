"""
=========================================================================
VCR (Version Controlled Resolution) Model
SDLC Orchestrator - Sprint 151 (SASE Artifacts Enhancement)

Version: 1.0.0
Date: March 4, 2026
Status: ACTIVE
Authority: CTO Approved
Framework: SDLC 6.0.3 SASE Methodology

Purpose:
VCR captures post-merge documentation for significant changes.
Links PR metadata with evidence, ADRs, and AI tool attribution.

Workflow:
1. Developer creates PR → passes gates (or has override)
2. Developer creates VCR with problem/solution documentation
3. VCR submitted for CTO/CEO approval
4. Approved VCR → PR merged, evidence stored
5. Rejected VCR → Request changes

SASE Integration:
- VCR is one of 6 SASE artifacts (BRS, LPS, MTS, CRP, MRP, VCR)
- Links to Evidence Vault for immutable audit trail
- Tracks AI tool involvement for governance
=========================================================================
"""

from datetime import datetime
from enum import Enum as PyEnum
from typing import List, Optional
from uuid import uuid4

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID as PgUUID
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class VCRStatus(str, PyEnum):
    """VCR lifecycle status."""

    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"


class VersionControlledResolution(Base):
    """
    Version Controlled Resolution (VCR) model.

    Captures post-merge documentation for significant changes with:
    - Problem statement and root cause analysis
    - Solution approach and implementation notes
    - Evidence and ADR linkage
    - AI tool attribution
    - Approval workflow
    """

    __tablename__ = "version_controlled_resolutions"

    # Primary key
    id = Column(
        PgUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        doc="Unique VCR identifier",
    )

    # Foreign keys
    project_id = Column(
        PgUUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Associated project",
    )

    pr_number = Column(
        Integer,
        nullable=True,
        doc="GitHub PR number (if applicable)",
    )

    pr_url = Column(
        String(500),
        nullable=True,
        doc="Full PR URL",
    )

    # VCR Content
    title = Column(
        String(255),
        nullable=False,
        doc="VCR title (concise summary)",
    )

    problem_statement = Column(
        Text,
        nullable=False,
        doc="What problem was being solved?",
    )

    root_cause_analysis = Column(
        Text,
        nullable=True,
        doc="Root cause analysis (for bug fixes)",
    )

    solution_approach = Column(
        Text,
        nullable=False,
        doc="How was the problem solved?",
    )

    implementation_notes = Column(
        Text,
        nullable=True,
        doc="Implementation details, caveats, trade-offs",
    )

    # Linkage
    evidence_ids = Column(
        ARRAY(PgUUID(as_uuid=True)),
        nullable=True,
        default=list,
        doc="Linked evidence IDs from Evidence Vault",
    )

    adr_ids = Column(
        ARRAY(PgUUID(as_uuid=True)),
        nullable=True,
        default=list,
        doc="Linked ADR IDs",
    )

    # AI Involvement
    ai_generated_percentage = Column(
        Float,
        nullable=True,
        default=0.0,
        doc="Percentage of code that was AI-generated (0.0 - 1.0)",
    )

    ai_tools_used = Column(
        ARRAY(String),
        nullable=True,
        default=list,
        doc="AI tools used (e.g., ['Cursor', 'Copilot', 'Claude'])",
    )

    ai_generation_details = Column(
        JSONB,
        nullable=True,
        default=dict,
        doc="Detailed AI generation metadata",
    )

    # Workflow
    status = Column(
        Enum(VCRStatus),
        nullable=False,
        default=VCRStatus.DRAFT,
        index=True,
        doc="VCR lifecycle status",
    )

    created_by_id = Column(
        PgUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        doc="User who created the VCR",
    )

    approved_by_id = Column(
        PgUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        doc="User who approved the VCR (CTO/CEO)",
    )

    rejection_reason = Column(
        Text,
        nullable=True,
        doc="Reason for rejection (if rejected)",
    )

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        doc="VCR creation timestamp",
    )

    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        doc="Last update timestamp",
    )

    submitted_at = Column(
        DateTime(timezone=True),
        nullable=True,
        doc="Submission timestamp",
    )

    approved_at = Column(
        DateTime(timezone=True),
        nullable=True,
        doc="Approval timestamp",
    )

    # Relationships
    project = relationship("Project", back_populates="vcrs", lazy="joined")
    created_by = relationship(
        "User",
        foreign_keys=[created_by_id],
        lazy="joined",
    )
    approved_by = relationship(
        "User",
        foreign_keys=[approved_by_id],
        lazy="joined",
    )

    def __repr__(self) -> str:
        return f"<VCR {self.title[:30]}... status={self.status}>"

    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        return {
            "id": str(self.id),
            "project_id": str(self.project_id),
            "pr_number": self.pr_number,
            "pr_url": self.pr_url,
            "title": self.title,
            "problem_statement": self.problem_statement,
            "root_cause_analysis": self.root_cause_analysis,
            "solution_approach": self.solution_approach,
            "implementation_notes": self.implementation_notes,
            "evidence_ids": [str(eid) for eid in (self.evidence_ids or [])],
            "adr_ids": [str(aid) for aid in (self.adr_ids or [])],
            "ai_generated_percentage": self.ai_generated_percentage,
            "ai_tools_used": self.ai_tools_used or [],
            "ai_generation_details": self.ai_generation_details or {},
            "status": self.status.value if self.status else None,
            "created_by_id": str(self.created_by_id) if self.created_by_id else None,
            "approved_by_id": str(self.approved_by_id) if self.approved_by_id else None,
            "rejection_reason": self.rejection_reason,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "submitted_at": self.submitted_at.isoformat() if self.submitted_at else None,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
        }
