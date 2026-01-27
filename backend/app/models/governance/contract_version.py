"""
=========================================================================
Contract Version Model - Policy Contract Versioning
SDLC Orchestrator - Sprint 108 (Governance Foundation)

Version: 1.0.0
Date: January 27, 2026
Status: ACTIVE - Sprint 108 Day 1
Authority: CTO + Backend Lead Approved
Framework: SDLC 5.3.0 Quality Assurance System

Purpose:
- Track contract evolution over time
- Store historical versions of YAML/Rego

Zero Mock Policy: Real SQLAlchemy model with all fields
=========================================================================
"""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class ContractVersion(Base):
    """
    Policy contract versioning for audit trail.

    Tracks:
    - Version history (semantic versioning)
    - Content at each version
    - Who made the change and why
    """

    __tablename__ = "contract_versions"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Foreign Key
    contract_id = Column(
        UUID(as_uuid=True),
        ForeignKey("quality_contracts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Version Metadata
    version = Column(String(50), nullable=False)
    version_description = Column(Text, nullable=True)

    # Version Content
    contract_yaml = Column(Text, nullable=False)
    contract_rego = Column(Text, nullable=True)

    # Change Tracking
    changed_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    change_reason = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )

    # Relationships
    contract = relationship("QualityContract", back_populates="versions")
    changed_by_user = relationship("User", foreign_keys=[changed_by])

    # Constraints
    __table_args__ = (
        UniqueConstraint("contract_id", "version", name="uq_contract_version"),
    )

    def __repr__(self) -> str:
        return f"ContractVersion(id={self.id}, version={self.version})"
