"""
=========================================================================
Governance Rejection Model - Rejection Reasons and Feedback
SDLC Orchestrator - Sprint 108 (Governance Foundation)

Version: 1.0.0
Date: January 27, 2026
Status: ACTIVE - Sprint 108 Day 1
Authority: CTO + Backend Lead Approved
Framework: SDLC 5.3.0 Quality Assurance System

Purpose:
- Store rejection reasons with actionable feedback
- Link to feedback_templates.yaml
- Track resolution status

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


class GovernanceRejection(Base):
    """
    Store rejection reasons with actionable feedback.

    Provides:
    - Rejection category (compliance, quality, security, context)
    - Severity level (error, warning, info)
    - CLI commands for fixing issues
    - Documentation links
    """

    __tablename__ = "governance_rejections"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Foreign Key
    submission_id = Column(
        UUID(as_uuid=True),
        ForeignKey("governance_submissions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Rejection Details
    rejection_reason = Column(String(255), nullable=False)
    rejection_category = Column(String(100), nullable=False)
    severity = Column(String(50), nullable=False)  # error | warning | info

    # Feedback (from feedback_templates.yaml)
    feedback_template_id = Column(String(100), nullable=True)
    feedback_message = Column(Text, nullable=False)
    feedback_cli_command = Column(Text, nullable=True)
    documentation_link = Column(Text, nullable=True)

    # Resolution
    resolved = Column(Boolean, nullable=False, default=False, index=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolved_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
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
    submission = relationship("GovernanceSubmission", back_populates="rejections")
    resolved_by_user = relationship("User", foreign_keys=[resolved_by])

    def __repr__(self) -> str:
        return f"GovernanceRejection(id={self.id}, reason={self.rejection_reason})"
