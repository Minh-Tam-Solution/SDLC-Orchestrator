"""
=========================================================================
Quality Contract Model - Policy-as-Code Rules
SDLC Orchestrator - Sprint 108 (Governance Foundation)

Version: 1.0.0
Date: January 27, 2026
Status: ACTIVE - Sprint 108 Day 1
Authority: CTO + Backend Lead Approved
Framework: SDLC 5.3.0 Quality Assurance System

Purpose:
- Store YAML policy contracts
- Compile to OPA Rego for validation
- Version and deprecation tracking

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


class QualityContract(Base):
    """
    Policy-as-Code rules (YAML contracts compiled to OPA Rego).

    Categories:
    - architecture: Code structure rules
    - testing: Test coverage requirements
    - security: Security scan requirements
    - documentation: Documentation requirements
    - ai_governance: AI-generated code rules
    """

    __tablename__ = "quality_contracts"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Contract Metadata
    contract_name = Column(String(255), nullable=False, unique=True)
    contract_category = Column(String(100), nullable=False, index=True)
    contract_description = Column(Text, nullable=False)

    # Contract Content
    contract_yaml = Column(Text, nullable=False)
    contract_rego = Column(Text, nullable=True)  # Compiled OPA Rego

    # Versioning
    version = Column(String(50), nullable=False, default="1.0.0")
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    deprecated_at = Column(DateTime(timezone=True), nullable=True)

    # Ownership
    created_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    approved_by = Column(
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
    created_by_user = relationship("User", foreign_keys=[created_by])
    approved_by_user = relationship("User", foreign_keys=[approved_by])
    versions = relationship(
        "ContractVersion",
        back_populates="contract",
        cascade="all, delete-orphan",
    )
    violations = relationship(
        "ContractViolation",
        back_populates="contract",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"QualityContract(id={self.id}, name={self.contract_name})"
