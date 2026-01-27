"""
=========================================================================
Evidence Vault Entry Model - Evidence Metadata Storage
SDLC Orchestrator - Sprint 108 (Governance Foundation)

Version: 1.0.0
Date: January 27, 2026
Status: ACTIVE - Sprint 108 Day 1
Authority: CTO + Backend Lead Approved
Framework: SDLC 5.3.0 Quality Assurance System

Purpose:
- Metadata for evidence artifacts stored in MinIO S3
- SHA256 integrity verification
- 8-state lifecycle tracking

Retention: 7 years (HIPAA/SOC 2 compliance)
Zero Mock Policy: Real SQLAlchemy model with all fields
=========================================================================
"""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import (
    BigInteger,
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


class EvidenceVaultEntry(Base):
    """
    Metadata for evidence artifacts stored in MinIO S3.

    Evidence Types:
    - intent_statement
    - ownership_declaration
    - adr_linkage
    - test_coverage_report
    - security_scan_report
    - ai_attestation

    Lifecycle States:
    - uploaded
    - validating
    - validated
    - rejected
    - archived
    - deleted
    """

    __tablename__ = "evidence_vault_entries"

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

    # Evidence Metadata
    evidence_type = Column(String(100), nullable=False, index=True)
    evidence_name = Column(String(255), nullable=False)
    evidence_description = Column(Text, nullable=True)

    # Storage Location (MinIO S3)
    s3_bucket = Column(String(255), nullable=False)
    s3_key = Column(Text, nullable=False)
    s3_url = Column(Text, nullable=False)

    # File Metadata
    file_size_bytes = Column(BigInteger, nullable=False)
    mime_type = Column(String(100), nullable=False)
    sha256_hash = Column(String(64), nullable=False)  # Integrity verification

    # Evidence Lifecycle (8 states)
    state = Column(String(50), nullable=False, default="uploaded", index=True)
    state_changed_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Access Control
    uploaded_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    uploaded_at = Column(
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
    submission = relationship("GovernanceSubmission", back_populates="evidence_entries")
    project = relationship("Project")
    uploaded_by_user = relationship("User", foreign_keys=[uploaded_by])

    # Constraints
    __table_args__ = (
        UniqueConstraint("s3_bucket", "s3_key", name="uq_evidence_s3_location"),
    )

    def __repr__(self) -> str:
        return f"EvidenceVaultEntry(id={self.id}, type={self.evidence_type})"
