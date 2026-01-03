"""
Subscription & Payment Models - SDLC Orchestrator

Version: 1.0.0
Date: December 27, 2025
Status: Sprint 58 - Registration + VNPay
Authority: Backend Lead + CTO Approved
Foundation: Plan v2.2 Section 4 & 7.3

Purpose:
- Subscription management (free, founder, standard, enterprise)
- Payment history with VNPay integration
- Idempotent payment processing per plan v2.2 Section 7.3

Tables:
- subscriptions: User subscription plans
- payment_history: VNPay payment records with idempotency
"""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4
import enum

from sqlalchemy import (
    Column,
    String,
    ForeignKey,
    Enum,
    Numeric,
    DateTime,
    Text,
    CheckConstraint,
    Index,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class SubscriptionPlan(str, enum.Enum):
    """
    Subscription plan tiers per Plan v2.2 Section 2.1.

    Pricing:
    - FREE: 0 VND, 1 project, 5 gates
    - FOUNDER: 2.5M VND/team/month (~$99)
    - STANDARD: $30/user/month (manual billing in V1)
    - ENTERPRISE: Custom pricing
    """

    FREE = "free"
    FOUNDER = "founder"
    STANDARD = "standard"
    ENTERPRISE = "enterprise"


class SubscriptionStatus(str, enum.Enum):
    """Subscription status."""

    ACTIVE = "active"
    CANCELED = "canceled"
    PAST_DUE = "past_due"


class PaymentStatus(str, enum.Enum):
    """
    Payment status with terminal state semantics.

    Per Plan v2.2 Section 7.3.1:
    - pending → completed: Only once, never reverse
    - pending → failed: Only once, never reverse
    - completed/failed: Terminal states (immutable)
    """

    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class Subscription(Base):
    """
    User subscription model.

    One user can have one active subscription.
    Default is FREE plan.

    Attributes:
        id: Primary key
        user_id: Foreign key to users
        plan: Subscription plan (free, founder, standard, enterprise)
        status: Subscription status (active, canceled, past_due)
        current_period_start: Start of current billing period
        current_period_end: End of current billing period
        vnpay_subscription_id: VNPay subscription identifier (if applicable)
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    __tablename__ = "subscriptions"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        comment="Subscription ID",
    )

    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
        comment="User ID (one subscription per user)",
    )

    plan: Mapped[str] = mapped_column(
        Enum(SubscriptionPlan, name="subscription_plan_enum", create_constraint=True),
        nullable=False,
        default=SubscriptionPlan.FREE,
        comment="Subscription plan tier",
    )

    status: Mapped[str] = mapped_column(
        Enum(SubscriptionStatus, name="subscription_status_enum", create_constraint=True),
        nullable=False,
        default=SubscriptionStatus.ACTIVE,
        comment="Subscription status",
    )

    current_period_start: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Start of current billing period",
    )

    current_period_end: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="End of current billing period",
    )

    vnpay_subscription_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="VNPay subscription identifier",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Creation timestamp",
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="Last update timestamp",
    )

    # Relationships
    user = relationship("User", back_populates="subscription")
    payments = relationship("PaymentHistory", back_populates="subscription")

    __table_args__ = (
        Index("ix_subscriptions_user_plan", "user_id", "plan"),
        {"comment": "User subscriptions - one per user"},
    )

    def __repr__(self) -> str:
        return f"Subscription(id={self.id}, user_id={self.user_id}, plan={self.plan})"


class PaymentHistory(Base):
    """
    VNPay payment history with idempotency.

    Per Plan v2.2 Section 7.3.2:
    - vnp_txn_ref is idempotency key (UNIQUE)
    - Terminal states (completed/failed) are immutable
    - processed_at is set when reaching terminal state

    Attributes:
        id: Primary key
        user_id: Foreign key to users
        subscription_id: Foreign key to subscriptions
        vnp_txn_ref: VNPay transaction reference (our order ID, idempotency key)
        vnp_transaction_no: VNPay's transaction ID
        amount: Payment amount in VND
        currency: Currency code (VND)
        plan: Plan being purchased
        status: Payment status (pending, completed, failed)
        processed_at: Timestamp when terminal state reached
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    __tablename__ = "payment_history"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        comment="Payment ID",
    )

    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="User ID",
    )

    subscription_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("subscriptions.id", ondelete="SET NULL"),
        nullable=True,
        comment="Subscription ID (set when payment completes)",
    )

    # VNPay identifiers (idempotency keys)
    vnp_txn_ref: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
        comment="VNPay transaction reference (our order ID, idempotency key)",
    )

    vnp_transaction_no: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="VNPay's transaction ID (set by VNPay IPN)",
    )

    # Payment details
    amount: Mapped[float] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        comment="Payment amount",
    )

    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="VND",
        comment="Currency code",
    )

    plan: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Plan being purchased (founder, standard)",
    )

    # State machine
    status: Mapped[str] = mapped_column(
        Enum(PaymentStatus, name="payment_status_enum", create_constraint=True),
        nullable=False,
        default=PaymentStatus.PENDING,
        comment="Payment status (terminal states: completed, failed)",
    )

    processed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp when terminal state reached (NULL until processed)",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Creation timestamp",
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="Last update timestamp",
    )

    # Additional metadata
    vnpay_response_code: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
        comment="VNPay response code (00 = success)",
    )

    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Error message if payment failed",
    )

    # Relationships
    user = relationship("User", back_populates="payments")
    subscription = relationship("Subscription", back_populates="payments")

    __table_args__ = (
        Index("ix_payment_history_user_status", "user_id", "status"),
        Index("ix_payment_history_vnp_txn_ref", "vnp_txn_ref"),
        CheckConstraint(
            "status IN ('pending', 'completed', 'failed')",
            name="valid_payment_status",
        ),
        {"comment": "VNPay payment history with idempotency support"},
    )

    def __repr__(self) -> str:
        return f"PaymentHistory(id={self.id}, vnp_txn_ref={self.vnp_txn_ref}, status={self.status})"

    def is_terminal(self) -> bool:
        """Check if payment is in terminal state."""
        return self.status in (PaymentStatus.COMPLETED, PaymentStatus.FAILED)

    def can_transition_to(self, new_status: PaymentStatus) -> bool:
        """
        Check if status transition is valid.

        Valid transitions:
        - pending → completed
        - pending → failed

        Invalid (no-op):
        - completed → anything
        - failed → anything
        """
        if self.is_terminal():
            return False
        return new_status in (PaymentStatus.COMPLETED, PaymentStatus.FAILED)
