"""
=========================================================================
Contract Violation Model - Policy Violation Details
SDLC Orchestrator - Sprint 108 (Governance Foundation)

Version: 1.0.0
Date: January 27, 2026
Status: ACTIVE - Sprint 108 Day 1
Authority: CTO + Backend Lead Approved
Framework: SDLC 5.3.0 Quality Assurance System

Purpose:
- Track policy violations per submission
- Link to specific contracts
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
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class ContractViolation(Base):
    """
    Policy violation details linked to specific contracts.

    Tracks:
    - Violation type and severity
    - File location (path + line number)
    - Resolution status and notes
    """

    __tablename__ = "contract_violations"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Foreign Keys
    submission_id = Column(
        UUID(as_uuid=True),
        ForeignKey("governance_submissions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    contract_id = Column(
        UUID(as_uuid=True),
        ForeignKey("quality_contracts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Violation Details
    violation_type = Column(String(255), nullable=False)
    violation_severity = Column(String(50), nullable=False)  # error | warning | info
    violation_message = Column(Text, nullable=False)

    # Location
    file_path = Column(Text, nullable=True)
    line_number = Column(Integer, nullable=True)

    # Resolution
    resolved = Column(Boolean, nullable=False, default=False, index=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolution_notes = Column(Text, nullable=True)

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
    submission = relationship("GovernanceSubmission", back_populates="contract_violations")
    contract = relationship("QualityContract", back_populates="violations")

    def __repr__(self) -> str:
        return f"ContractViolation(id={self.id}, type={self.violation_type})"
