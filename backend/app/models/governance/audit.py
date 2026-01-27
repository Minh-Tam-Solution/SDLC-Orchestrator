"""
=========================================================================
Governance Audit Log Model - Immutable Audit Trail
SDLC Orchestrator - Sprint 108 (Governance Foundation)

Version: 1.0.0
Date: January 27, 2026
Status: ACTIVE - Sprint 108 Day 1
Authority: CTO + Backend Lead Approved
Framework: SDLC 5.3.0 Quality Assurance System

Purpose:
- Immutable audit trail for all governance actions
- HIPAA/SOC 2 compliance (7-year retention)
- Who did what when tracking

Performance Target: <50ms (P95) for audit queries
Retention: 7 years (NEVER delete, archivable after 1 year)
Zero Mock Policy: Real SQLAlchemy model with all fields

IMPORTANT: This table is IMMUTABLE - UPDATE/DELETE are prevented by trigger
=========================================================================
"""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class GovernanceAuditLog(Base):
    """
    Immutable audit trail for all governance actions.

    Action Categories:
    - governance: submit_pr, approve_gate, reject_gate
    - security: break_glass
    - exception: override_decision
    - calibration: ceo_calibration

    IMMUTABLE: UPDATE/DELETE forbidden via PostgreSQL trigger
    """

    __tablename__ = "governance_audit_log"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Actor
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    user_email = Column(String(255), nullable=False)
    user_role = Column(String(50), nullable=True)
    ip_address = Column(INET, nullable=True)

    # Action
    action = Column(String(100), nullable=False, index=True)
    action_category = Column(String(50), nullable=False)

    # Target
    target_type = Column(String(100), nullable=True)
    target_id = Column(UUID(as_uuid=True), nullable=True)

    # Context
    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    submission_id = Column(
        UUID(as_uuid=True),
        ForeignKey("governance_submissions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Details
    action_details = Column(JSONB, nullable=True)
    outcome = Column(String(50), nullable=True)  # success | failure | pending

    # Timestamp (IMMUTABLE - never updated)
    timestamp = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    project = relationship("Project")
    submission = relationship("GovernanceSubmission")

    def __repr__(self) -> str:
        return f"GovernanceAuditLog(id={self.id}, action={self.action})"
