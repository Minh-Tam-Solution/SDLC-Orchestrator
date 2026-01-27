"""
=========================================================================
Governance Exception Model - Break Glass / Exceptions
SDLC Orchestrator - Sprint 108 (Governance Foundation)

Version: 1.0.0
Date: January 27, 2026
Status: ACTIVE - Sprint 108 Day 1
Authority: CTO + Backend Lead Approved
Framework: SDLC 5.3.0 Quality Assurance System

Purpose:
- Emergency bypass for P0/P1 incidents
- Break glass mechanism (24h auto-revert)
- Stage bypass requests
- Policy override tracking

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
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class GovernanceException(Base):
    """
    Break glass / exception requests for emergency bypass.

    Exception Types:
    - break_glass: Emergency production hotfix
    - stage_bypass: Skip stage for urgent work
    - policy_override: Override specific policy
    - emergency_hotfix: Critical bug fix

    Features:
    - 24h auto-revert for break glass
    - Post-incident review required
    - CTO/CEO approval workflow
    """

    __tablename__ = "governance_exceptions"

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

    # Exception Request
    exception_type = Column(String(100), nullable=False)
    severity = Column(String(50), nullable=False)  # P0 | P1 | P2
    reason = Column(Text, nullable=False)

    # Incident Details
    incident_ticket = Column(String(255), nullable=True)  # JIRA/Linear ticket ID
    rollback_plan = Column(Text, nullable=False)

    # Approval Workflow
    requested_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    requested_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    approved_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    approved_at = Column(DateTime(timezone=True), nullable=True)

    approval_status = Column(
        String(50),
        nullable=False,
        default="pending",
        index=True,
    )  # pending | approved | rejected | auto_reverted

    # Break Glass Specifics
    break_glass_activated = Column(Boolean, nullable=False, default=False)
    auto_revert_at = Column(DateTime(timezone=True), nullable=True, index=True)
    post_incident_review_completed = Column(Boolean, nullable=False, default=False)

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
    submission = relationship("GovernanceSubmission", back_populates="exception")
    project = relationship("Project")
    requested_by_user = relationship("User", foreign_keys=[requested_by])
    approved_by_user = relationship("User", foreign_keys=[approved_by])

    def __repr__(self) -> str:
        return f"GovernanceException(id={self.id}, type={self.exception_type})"
