"""
Override Database Models - VCR (Version Controlled Resolution)

SDLC Stage: 04 - BUILD
Sprint: 43 - Policy Guards & Evidence UI
Framework: SDLC 5.1.1
Epic: EP-02 AI Safety Layer v1

Purpose:
Database models for the VCR Override Flow.
Tracks override requests, approvals, and audit trail.

Tables:
1. validation_overrides - Override requests and resolutions
2. override_audit_logs - Immutable audit trail for compliance

VCR Flow:
1. Developer requests override (failed validation)
2. Request enters admin queue (PENDING)
3. Admin/Manager reviews and approves/rejects
4. If approved, validation_result updated to 'overridden'
5. All actions logged in audit trail

Retention Policy:
- validation_overrides: 2 years (security audit requirement)
- override_audit_logs: 5 years (compliance requirement)
"""

from datetime import datetime
from enum import Enum as PyEnum
from uuid import uuid4

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    Text,
    Boolean,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class OverrideType(str, PyEnum):
    """Types of override requests."""

    FALSE_POSITIVE = "false_positive"  # Detection was incorrect
    APPROVED_RISK = "approved_risk"    # Risk reviewed and accepted
    EMERGENCY = "emergency"            # Critical hotfix bypass


class OverrideStatus(str, PyEnum):
    """Override request status."""

    PENDING = "pending"      # Awaiting review
    APPROVED = "approved"    # Override granted
    REJECTED = "rejected"    # Override denied
    EXPIRED = "expired"      # Request expired (7 days)
    CANCELLED = "cancelled"  # Requester cancelled


class OverrideAuditAction(str, PyEnum):
    """Audit log action types."""

    REQUEST_CREATED = "request_created"
    REQUEST_UPDATED = "request_updated"
    REQUEST_CANCELLED = "request_cancelled"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    ESCALATED = "escalated"
    COMMENT_ADDED = "comment_added"


class ValidationOverride(Base):
    """
    Override request for failed validations.

    Lifecycle:
    1. Created when developer requests override on failed event
    2. Status: PENDING → (APPROVED | REJECTED | EXPIRED | CANCELLED)
    3. If APPROVED, linked AICodeEvent.validation_result → 'overridden'

    Business Rules:
    - Only ADMIN, MANAGER, SECURITY_LEAD can approve
    - EMERGENCY overrides require post-merge review within 24h
    - Requests expire after 7 days if not actioned
    - Reason must be ≥50 characters

    Indexes:
    - event_id: Lookup by AI code event
    - status + created_at: Admin queue filtering
    - requested_by_id: User's override history
    - project_id + status: Project-level metrics
    """

    __tablename__ = "validation_overrides"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Link to AI Code Event
    event_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("ai_code_events.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Project context (denormalized for faster queries)
    project_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Request details
    override_type = Column(
        Enum(OverrideType),
        nullable=False,
        index=True,
    )
    reason = Column(
        Text,
        nullable=False,
    )
    status = Column(
        Enum(OverrideStatus),
        nullable=False,
        default=OverrideStatus.PENDING,
        index=True,
    )

    # Requester
    requested_by_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    requested_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    # Resolution
    resolved_by_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    resolved_at = Column(DateTime, nullable=True)
    resolution_comment = Column(Text, nullable=True)

    # Metadata
    pr_number = Column(String(100), nullable=True)  # Denormalized for queue display
    pr_title = Column(String(500), nullable=True)   # Denormalized for queue display
    failed_validators = Column(Text, nullable=True)  # JSON array of failed validator names

    # Expiry tracking
    expires_at = Column(DateTime, nullable=True)  # 7 days from created_at
    is_expired = Column(Boolean, default=False)

    # Emergency override tracking
    post_merge_review_required = Column(Boolean, default=False)
    post_merge_review_completed = Column(Boolean, default=False)
    post_merge_reviewed_by_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    post_merge_reviewed_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    event = relationship("AICodeEvent", back_populates="overrides")
    project = relationship("Project", back_populates="validation_overrides")
    requested_by = relationship("User", foreign_keys=[requested_by_id], back_populates="override_requests")
    resolved_by = relationship("User", foreign_keys=[resolved_by_id])
    post_merge_reviewed_by = relationship("User", foreign_keys=[post_merge_reviewed_by_id])
    audit_logs = relationship("OverrideAuditLog", back_populates="override", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("ix_override_status_created", "status", "created_at"),
        Index("ix_override_project_status", "project_id", "status"),
        Index("ix_override_type_status", "override_type", "status"),
        Index("ix_override_expires", "expires_at", "is_expired"),
    )

    def __repr__(self):
        return f"<ValidationOverride {self.id} event={self.event_id} status={self.status}>"


class OverrideAuditLog(Base):
    """
    Immutable audit trail for override actions.

    Purpose:
    - Compliance requirement (SOC 2, HIPAA)
    - Security audit trail
    - Incident investigation

    Design:
    - Append-only (no updates, no deletes)
    - Captures full state at action time
    - IP address and user agent for forensics

    Retention: 5 years (compliance requirement)
    """

    __tablename__ = "override_audit_logs"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Link to override
    override_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("validation_overrides.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Action details
    action = Column(
        Enum(OverrideAuditAction),
        nullable=False,
        index=True,
    )
    action_by_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    action_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        index=True,
    )

    # State snapshot
    previous_status = Column(Enum(OverrideStatus), nullable=True)
    new_status = Column(Enum(OverrideStatus), nullable=True)
    comment = Column(Text, nullable=True)

    # Forensics
    ip_address = Column(String(45), nullable=True)  # IPv6 max length
    user_agent = Column(String(500), nullable=True)

    # Metadata
    metadata_json = Column("metadata", Text, nullable=True)  # JSON for additional context

    # Relationships
    override = relationship("ValidationOverride", back_populates="audit_logs")
    action_by = relationship("User")

    # Indexes
    __table_args__ = (
        Index("ix_audit_override_action", "override_id", "action"),
        Index("ix_audit_action_at", "action_at"),
    )

    def __repr__(self):
        return f"<OverrideAuditLog {self.action} on {self.override_id}>"
