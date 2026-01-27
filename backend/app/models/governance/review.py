"""
=========================================================================
Human Review Model - Human Review of AI Code
SDLC Orchestrator - Sprint 108 (Governance Foundation)

Version: 1.0.0
Date: January 27, 2026
Status: ACTIVE - Sprint 108 Day 1
Authority: CTO + Backend Lead Approved
Framework: SDLC 5.3.0 Quality Assurance System

Purpose:
- Track human review of AI-generated code
- Capture review quality metrics
- Link to AI attestations

Zero Mock Policy: Real SQLAlchemy model with all fields
=========================================================================
"""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class HumanReview(Base):
    """
    Human review of AI-generated code.

    Tracks:
    - Reviewer identity and role
    - Review duration
    - Issues found and fixed
    - Code quality rating (1-5)
    """

    __tablename__ = "human_reviews"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Foreign Keys
    attestation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("ai_attestations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    submission_id = Column(
        UUID(as_uuid=True),
        ForeignKey("governance_submissions.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Reviewer
    reviewed_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    reviewer_role = Column(String(50), nullable=False)  # developer | tech_lead | senior_dev | cto

    # Review Details
    review_duration_minutes = Column(Integer, nullable=False)
    review_notes = Column(Text, nullable=True)

    # Review Findings
    issues_found = Column(Integer, nullable=False, default=0)
    issues_fixed = Column(Integer, nullable=False, default=0)
    code_quality_rating = Column(Integer, nullable=True)  # 1-5 scale

    # Timestamps
    reviewed_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Relationships
    attestation = relationship("AIAttestation", back_populates="human_reviews")
    submission = relationship("GovernanceSubmission")
    reviewed_by_user = relationship("User", foreign_keys=[reviewed_by])

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "code_quality_rating IS NULL OR (code_quality_rating >= 1 AND code_quality_rating <= 5)",
            name="check_quality_rating_range",
        ),
    )

    def __repr__(self) -> str:
        return f"HumanReview(id={self.id}, rating={self.code_quality_rating})"
