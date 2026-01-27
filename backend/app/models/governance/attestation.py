"""
=========================================================================
AI Attestation Model - AI-Generated Code Attestations
SDLC Orchestrator - Sprint 108 (Governance Foundation)

Version: 1.0.0
Date: January 27, 2026
Status: ACTIVE - Sprint 108 Day 1
Authority: CTO + Backend Lead Approved
Framework: SDLC 5.3.0 Quality Assurance System

Purpose:
- Principle 4: NO AI OUTPUT WITHOUT EXPLAINABILITY
- Track AI session metadata
- Enforce minimum review time (2 sec/line)
- Validate human understanding

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
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class AIAttestation(Base):
    """
    AI-generated code attestations.

    Validates:
    - AI provider and model version
    - Generated lines count
    - Human review time (minimum: 2 sec/line)
    - Modifications made
    - Understanding confirmation
    """

    __tablename__ = "ai_attestations"

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

    # AI Session Metadata
    ai_provider = Column(String(100), nullable=False)  # ollama | claude | gpt-4o | deepcode
    model_version = Column(String(255), nullable=False)
    session_id = Column(String(255), nullable=True)
    prompt_hash = Column(String(64), nullable=True)

    # AI-Generated Content
    ai_generated_files = Column(JSONB, nullable=False, default=list)
    total_ai_lines = Column(Integer, nullable=False, default=0)

    # Human Review (MANDATORY)
    review_time_minutes = Column(Integer, nullable=False)
    minimum_review_time_minutes = Column(Integer, nullable=False)
    review_sufficient = Column(Boolean, nullable=False, default=False)

    modifications_made = Column(Text, nullable=True)
    understanding_confirmed = Column(Boolean, nullable=False, default=False)

    # Attestation
    attested_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    attested_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

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
    submission = relationship("GovernanceSubmission", back_populates="ai_attestation")
    project = relationship("Project")
    attested_by_user = relationship("User", foreign_keys=[attested_by])
    human_reviews = relationship(
        "HumanReview",
        back_populates="attestation",
        cascade="all, delete-orphan",
    )

    # Constraints
    __table_args__ = (
        CheckConstraint("review_time_minutes >= 0", name="check_review_time_positive"),
    )

    def __repr__(self) -> str:
        return f"AIAttestation(id={self.id}, provider={self.ai_provider})"
