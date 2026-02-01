"""
Team Invitation Model

Security-focused invitation system with hash-based tokens (ADR-043).

Features:
- SHA256 token hashing (no raw tokens stored)
- One-time use (status change prevents replay)
- 7-day expiry (configurable)
- Rate limiting support (resend_count)
- Full audit trail (who invited whom, when, from where)

Reference: ADR-043-Team-Invitation-System-Architecture.md
"""
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy import (
    Column,
    String,
    Integer,
    Text,
    DateTime,
    ForeignKey,
    CheckConstraint,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, INET
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base_class import Base


class InvitationStatus:
    """Invitation status enum"""
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class TeamInvitation(Base):
    """
    Team invitation with hash-based token security.

    Security features:
    - Token stored as SHA256 hash (invitation_token_hash)
    - One-time use enforcement (status check)
    - Constant-time comparison (hmac.compare_digest)
    - Audit trail (IP, user agent, timestamps)

    Rate limiting:
    - resend_count tracked in DB
    - Limit enforced in application layer (configurable)
    - No DB CHECK constraint for flexibility
    """
    __tablename__ = "team_invitations"

    id = Column(PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())

    # Invitation details
    team_id = Column(PGUUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    invited_email = Column(String(255), nullable=False, index=True)
    invitation_token_hash = Column(
        String(64),
        nullable=False,
        unique=True,
        index=True,
        comment="SHA256 hash of invitation token (never store raw token)"
    )
    role = Column(String(20), nullable=False, default="member")
    status = Column(String(20), nullable=False, default=InvitationStatus.PENDING, index=True)

    # User relationships
    invited_by = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)
    accepted_at = Column(DateTime, nullable=True)
    declined_at = Column(DateTime, nullable=True)

    # Rate limiting (enforced in application)
    resend_count = Column(Integer, nullable=False, default=0)
    last_resent_at = Column(DateTime, nullable=True)

    # Audit trail
    ip_address = Column(INET, nullable=True)
    user_agent = Column(Text, nullable=True)

    # Relationships
    team = relationship("Team", back_populates="invitations", lazy="joined")
    inviter = relationship("User", foreign_keys=[invited_by], lazy="joined")

    # Constraints
    __table_args__ = (
        CheckConstraint("expires_at > created_at", name="valid_expiry"),
        # Partial unique index for pending invitations
        Index(
            "idx_unique_pending_invitation",
            "team_id",
            "invited_email",
            unique=True,
            postgresql_where=(status == InvitationStatus.PENDING)
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<TeamInvitation(id={self.id}, "
            f"team_id={self.team_id}, "
            f"email={self.invited_email}, "
            f"status={self.status})>"
        )

    @property
    def is_expired(self) -> bool:
        """Check if invitation has expired"""
        return datetime.utcnow() > self.expires_at

    @property
    def is_pending(self) -> bool:
        """Check if invitation is pending"""
        return self.status == InvitationStatus.PENDING and not self.is_expired

    @property
    def is_accepted(self) -> bool:
        """Check if invitation was accepted"""
        return self.status == InvitationStatus.ACCEPTED

    @property
    def is_declined(self) -> bool:
        """Check if invitation was declined"""
        return self.status == InvitationStatus.DECLINED

    @property
    def can_resend(self) -> bool:
        """
        Check if invitation can be resent.

        Rules:
        - Status must be pending or expired
        - Not exceeded max resends limit (default: 3)
        - Cooldown period elapsed (default: 5 minutes)
        """
        # Default limits (can be overridden by settings)
        max_resends = 3
        cooldown_minutes = 5

        if self.status not in [InvitationStatus.PENDING, InvitationStatus.EXPIRED]:
            return False

        if self.resend_count >= max_resends:
            return False

        if self.last_resent_at:
            cooldown = timedelta(minutes=cooldown_minutes)
            if datetime.utcnow() - self.last_resent_at < cooldown:
                return False

        return True

    def accept(self, user_id: UUID) -> None:
        """
        Accept invitation (one-time use).

        Args:
            user_id: User who accepted the invitation

        Raises:
            ValueError: If invitation cannot be accepted
        """
        if not self.is_pending:
            raise ValueError(f"Invitation cannot be accepted (status: {self.status})")

        self.status = InvitationStatus.ACCEPTED
        self.accepted_at = datetime.utcnow()

    def decline(self) -> None:
        """
        Decline invitation.

        Raises:
            ValueError: If invitation cannot be declined
        """
        if not self.is_pending:
            raise ValueError(f"Invitation cannot be declined (status: {self.status})")

        self.status = InvitationStatus.DECLINED
        self.declined_at = datetime.utcnow()

    def cancel(self) -> None:
        """
        Cancel invitation (admin action).

        Raises:
            ValueError: If invitation cannot be cancelled
        """
        if self.status != InvitationStatus.PENDING:
            raise ValueError(f"Invitation cannot be cancelled (status: {self.status})")

        self.status = InvitationStatus.CANCELLED

    def mark_expired(self) -> None:
        """Mark invitation as expired (background job)"""
        if self.status == InvitationStatus.PENDING and self.is_expired:
            self.status = InvitationStatus.EXPIRED

    def increment_resend_count(self) -> None:
        """
        Increment resend counter (before sending email).

        Raises:
            ValueError: If cannot resend
        """
        if not self.can_resend:
            raise ValueError(
                f"Cannot resend invitation (count: {self.resend_count}, "
                f"status: {self.status})"
            )

        self.resend_count += 1
        self.last_resent_at = datetime.utcnow()
