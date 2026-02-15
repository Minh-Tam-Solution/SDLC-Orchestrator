"""
=========================================================================
Gate Evidence Model - Evidence Vault (FR2)
SDLC Orchestrator - Stage 03 (BUILD)

Version: 1.0.0
Date: November 28, 2025
Status: ACTIVE - Week 3 Architecture Design
Authority: Backend Lead + CTO Approved
Foundation: Data Model v0.1 (9.8/10 quality), FR2 (Evidence Vault)
Framework: SDLC 4.9 Complete Lifecycle

Purpose:
- Evidence file management (S3/MinIO storage)
- SHA256 integrity verification (tamper detection)
- Evidence type classification (DESIGN, TEST, DEPLOYMENT, etc.)
- Audit trail for evidence uploads

Security Standards:
- SHA256 hashing for file integrity
- Tamper-proof audit trail (EvidenceIntegrityCheck)
- MinIO S3-compatible object storage (AGPL safe)
- Permanent evidence retention (soft delete only)

Zero Mock Policy: Real SQLAlchemy model with all fields
=========================================================================
"""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import BigInteger, Boolean, Column, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class GateEvidence(Base):
    """
    Gate Evidence model for evidence file management (FR2).

    Purpose:
        - Store evidence files (MinIO S3-compatible storage)
        - SHA256 integrity verification (tamper detection)
        - Permanent audit trail (evidence never deleted)
        - Support multiple evidence types (design docs, test results, code, etc.)

    Evidence Types:
        - DESIGN_DOCUMENT: Architecture diagrams, data models, API specs
        - TEST_RESULTS: Unit test, integration test, performance test results
        - CODE_REVIEW: Code review reports, static analysis results
        - DEPLOYMENT_PROOF: Deployment logs, production screenshots
        - DOCUMENTATION: README, user guides, technical docs
        - COMPLIANCE: Security scans, license audits, GDPR compliance

    Fields:
        - id: UUID primary key
        - gate_id: Foreign key to Gate
        - file_name: Original file name (e.g., "data-model-v0.1.md")
        - file_size: File size in bytes
        - file_type: MIME type (e.g., "text/markdown", "application/pdf")
        - evidence_type: Evidence category
        - s3_key: MinIO S3 object key (e.g., "evidence/gate-123/file-456.md")
        - s3_bucket: MinIO bucket name (e.g., "sdlc-evidence")
        - sha256_hash: SHA256 hash for integrity verification
        - description: Evidence description
        - uploaded_by: Foreign key to User (uploader)
        - uploaded_at: Upload timestamp
        - created_at: Record creation timestamp
        - deleted_at: Soft delete (evidence never hard-deleted)

    Relationships:
        - gate: Many-to-One with Gate model
        - uploader: Many-to-One with User model
        - integrity_checks: One-to-Many with EvidenceIntegrityCheck model

    Indexes:
        - gate_id (B-tree) - Fast gate evidence lookup
        - uploaded_by (B-tree) - Fast uploader lookup
        - sha256_hash (B-tree) - Fast hash lookup for deduplication
        - evidence_type (B-tree) - Evidence type filtering

    Usage Example:
        evidence = GateEvidence(
            gate_id=gate.id,
            file_name="data-model-v0.1.md",
            file_size=1400000,  # 1.4MB
            file_type="text/markdown",
            evidence_type="DESIGN_DOCUMENT",
            s3_key="evidence/gate-123/file-456.md",
            s3_bucket="sdlc-evidence",
            sha256_hash="abc123...",
            description="Data Model v0.1 - PostgreSQL schema design",
            uploaded_by=user.id
        )
    """

    __tablename__ = "gate_evidence"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)

    # Gate Relationship
    gate_id = Column(
        UUID(as_uuid=True),
        ForeignKey("gates.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # File Metadata
    file_name = Column(String(255), nullable=False)
    file_size = Column(BigInteger, nullable=False)  # Bytes
    file_type = Column(String(100), nullable=False)  # MIME type

    # Evidence Classification
    evidence_type = Column(
        String(50), nullable=False, index=True
    )  # 'DESIGN_DOCUMENT', 'TEST_RESULTS', etc.

    # S3 Storage (MinIO)
    s3_key = Column(String(512), nullable=False, unique=True)
    s3_bucket = Column(String(100), nullable=False, default="sdlc-evidence")

    # Integrity (Sprint 173 Evidence Contract — ADR-053)
    sha256_hash = Column(String(64), nullable=True, index=True)  # Client-side SHA256 (legacy alias)
    sha256_server = Column(String(64), nullable=True)  # Server re-computed SHA256

    # Evidence binding (Sprint 173)
    criteria_snapshot_id = Column(
        UUID(as_uuid=True), nullable=True, index=True
    )  # Binds to gate exit_criteria_version
    source = Column(
        String(20), nullable=False, default="web", index=True
    )  # 'cli', 'extension', 'web', 'other'

    # Description
    description = Column(Text, nullable=True)

    # Upload Tracking
    uploaded_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Audit Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    deleted_at = Column(DateTime, nullable=True)  # Soft delete only

    # Relationships
    gate = relationship("Gate", back_populates="evidence")
    uploader = relationship("User", back_populates="uploaded_evidence")
    integrity_checks = relationship(
        "EvidenceIntegrityCheck", back_populates="evidence", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<GateEvidence(id={self.id}, file_name={self.file_name}, gate_id={self.gate_id})>"

    @property
    def file_size_mb(self) -> float:
        """Get file size in megabytes"""
        return self.file_size / (1024 * 1024) if self.file_size else 0.0

    @property
    def s3_url(self) -> str:
        """Generate MinIO S3 URL (for internal access only)"""
        return f"s3://{self.s3_bucket}/{self.s3_key}"


class EvidenceIntegrityCheck(Base):
    """
    Evidence Integrity Check model for tamper detection.

    Purpose:
        - Periodic integrity verification (SHA256 hash check)
        - Tamper detection (hash mismatch = corrupted/modified file)
        - Audit trail for compliance

    Fields:
        - id: UUID primary key
        - evidence_id: Foreign key to GateEvidence
        - checked_at: Check timestamp
        - sha256_hash: Hash at check time
        - is_valid: Integrity check result (True = OK, False = tampered)
        - error_message: Error details if tampered
        - checked_by: System or user who triggered check
        - created_at: Record creation timestamp

    Relationships:
        - evidence: Many-to-One with GateEvidence model

    Indexes:
        - evidence_id (B-tree) - Fast evidence check lookup
        - checked_at (B-tree) - Recent checks queries
        - is_valid (B-tree) - Failed check filtering

    Usage Example:
        check = EvidenceIntegrityCheck(
            evidence_id=evidence.id,
            checked_at=datetime.utcnow(),
            sha256_hash=current_hash,
            is_valid=(current_hash == evidence.sha256_hash),
            checked_by='system-cron'
        )
    """

    __tablename__ = "evidence_integrity_checks"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)

    # Evidence Relationship
    evidence_id = Column(
        UUID(as_uuid=True),
        ForeignKey("gate_evidence.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Check Results
    checked_at = Column(DateTime, nullable=False, index=True)
    sha256_hash = Column(String(64), nullable=False)  # Hash at check time
    is_valid = Column(
        Boolean, nullable=False, index=True
    )  # True = OK, False = tampered

    # Error Details
    error_message = Column(Text, nullable=True)

    # Check Metadata
    checked_by = Column(String(100), nullable=False)  # 'system-cron', 'user-123', etc.

    # Audit Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    evidence = relationship("GateEvidence", back_populates="integrity_checks")

    def __repr__(self) -> str:
        return f"<EvidenceIntegrityCheck(evidence_id={self.evidence_id}, is_valid={self.is_valid})>"
