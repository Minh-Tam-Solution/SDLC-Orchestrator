"""
=========================================================================
Escalation Log Model - CEO Escalation Tracking
SDLC Orchestrator - Sprint 108 (Governance Foundation)

Version: 1.0.0
Date: January 27, 2026
Status: ACTIVE - Sprint 108 Day 1
Authority: CTO + Backend Lead Approved
Framework: SDLC 5.3.0 Quality Assurance System

Purpose:
- Track Red/Orange PR escalations to CEO
- Store CEO decisions and review time
- Enable calibration feedback for index tuning

Zero Mock Policy: Real SQLAlchemy model with all fields
=========================================================================
"""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class EscalationLog(Base):
    """
    Red/Orange PR escalations to CEO.

    Escalation Reasons:
    - vibecoding_index_red: Index > 80
    - vibecoding_index_orange: Index 61-80
    - critical_path: Security/payment/auth changes
    - exception_request: Break glass request
    - ceo_override_requested: Manual escalation

    CEO Decision:
    - approve: PR can merge
    - reject: PR must be reworked
    - request_changes: Minor fixes needed
    - escalate_further: Needs more review
    """

    __tablename__ = "escalation_log"

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

    # Escalation Details
    escalation_reason = Column(String(255), nullable=False)
    vibecoding_index = Column(Numeric(5, 2), nullable=True)

    escalated_to = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    escalated_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    escalated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # CEO Decision
    ceo_decision = Column(
        String(50),
        nullable=True,
        index=True,
    )  # approve | reject | request_changes | escalate_further
    ceo_decision_notes = Column(Text, nullable=True)
    ceo_decision_at = Column(DateTime(timezone=True), nullable=True)
    ceo_review_duration_minutes = Column(Integer, nullable=True)

    # Feedback to System (Calibration)
    ceo_agrees_with_index = Column(Boolean, nullable=True)
    calibration_feedback = Column(Text, nullable=True)

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
    submission = relationship("GovernanceSubmission", back_populates="escalations")
    project = relationship("Project")
    escalated_to_user = relationship("User", foreign_keys=[escalated_to])
    escalated_by_user = relationship("User", foreign_keys=[escalated_by])

    def __repr__(self) -> str:
        return f"EscalationLog(id={self.id}, decision={self.ceo_decision})"
