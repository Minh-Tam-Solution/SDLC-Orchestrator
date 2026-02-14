"""
=========================================================================
Product Event Model - Telemetry Foundation
SDLC Orchestrator - Sprint 147 (Spring Cleaning)

Version: 1.0.0
Date: February 4, 2026
Status: ACTIVE
Authority: CTO Approved
Framework: SDLC 6.0.5 Product Truth Layer

Purpose:
Track user behavior events for activation funnels and product metrics.
This replaces the legacy analytics tracking with a focused, measurable approach.

Core Events (Tier 1 - Sprint 147):
1. user_signed_up
2. project_created
3. project_connected_github
4. first_validation_run
5. first_evidence_uploaded
6. first_gate_passed
7. invite_sent
8. invite_accepted
9. policy_violation_blocked
10. ai_council_used

Engagement Events (Tier 2 - Sprint 148):
11-20. daily_active_user, gate_approval_requested, etc.
=========================================================================
"""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PgUUID
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class ProductEvent(Base):
    """
    Product event for telemetry tracking.

    Tracks user behavior events for:
    - Activation funnels (signup → project → evidence → gate)
    - Engagement metrics (DAU, feature usage)
    - Conversion analysis (cohort retention)

    Designed for high-volume writes with efficient funnel queries.
    """

    __tablename__ = "product_events"

    # Primary key
    id = Column(
        PgUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        doc="Unique event ID",
    )

    # Event identification
    event_name = Column(
        String(100),
        nullable=False,
        index=True,
        doc="Event name (e.g., 'user_signed_up', 'project_created')",
    )

    # Actor identification
    user_id = Column(
        PgUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="User who triggered the event (null for anonymous)",
    )

    # Context
    project_id = Column(
        PgUUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Related project (if applicable)",
    )

    organization_id = Column(
        PgUUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Related organization (if applicable)",
    )

    # Event properties (flexible JSON)
    properties = Column(
        JSONB,
        nullable=False,
        default=dict,
        doc="Event-specific properties (e.g., tier, method, duration)",
    )

    # Session tracking
    session_id = Column(
        String(100),
        nullable=True,
        index=True,
        doc="Session ID for grouping events",
    )

    # Interface tracking (Web, CLI, Extension, API)
    interface = Column(
        String(20),
        nullable=True,
        doc="Interface: 'web', 'cli', 'extension', 'api'",
    )

    # Timestamp
    timestamp = Column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
        index=True,
        doc="Event timestamp",
    )

    # Relationships
    user = relationship("User", back_populates="product_events", lazy="joined")

    # Indexes for funnel queries
    __table_args__ = (
        # Funnel query optimization: find all events for a user in order
        Index("idx_product_events_user_time", "user_id", "timestamp"),
        # Project activity queries
        Index("idx_product_events_project_time", "project_id", "timestamp"),
        # Event type + time for aggregate metrics
        Index("idx_product_events_name_time", "event_name", "timestamp"),
        # Combined index for funnel analysis
        Index(
            "idx_product_events_funnel",
            "user_id",
            "event_name",
            "timestamp",
        ),
        # Interface + time for breakdown
        Index("idx_product_events_interface_time", "interface", "timestamp"),
    )

    def __repr__(self) -> str:
        return f"<ProductEvent {self.event_name} user={self.user_id} at {self.timestamp}>"

    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        return {
            "id": str(self.id),
            "event_name": self.event_name,
            "user_id": str(self.user_id) if self.user_id else None,
            "project_id": str(self.project_id) if self.project_id else None,
            "organization_id": str(self.organization_id) if self.organization_id else None,
            "properties": self.properties,
            "session_id": self.session_id,
            "interface": self.interface,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }


# Event name constants for type safety
class EventNames:
    """Standard event names for product telemetry."""

    # Tier 1: Activation Events (Sprint 147)
    USER_SIGNED_UP = "user_signed_up"
    PROJECT_CREATED = "project_created"
    PROJECT_CONNECTED_GITHUB = "project_connected_github"
    FIRST_VALIDATION_RUN = "first_validation_run"
    FIRST_EVIDENCE_UPLOADED = "first_evidence_uploaded"
    FIRST_GATE_PASSED = "first_gate_passed"
    INVITE_SENT = "invite_sent"
    INVITE_ACCEPTED = "invite_accepted"
    POLICY_VIOLATION_BLOCKED = "policy_violation_blocked"
    AI_COUNCIL_USED = "ai_council_used"

    # Tier 2: Engagement Events (Sprint 148)
    DAILY_ACTIVE_USER = "daily_active_user"
    GATE_APPROVAL_REQUESTED = "gate_approval_requested"
    EVIDENCE_VIEWED = "evidence_viewed"
    DASHBOARD_PAGE_VIEWED = "dashboard_page_viewed"
    CLI_COMMAND_EXECUTED = "cli_command_executed"
    EXTENSION_COMMAND_EXECUTED = "extension_command_executed"
    SPEC_VALIDATED = "spec_validated"
    REPORT_GENERATED = "report_generated"
    POLICY_PACK_APPLIED = "policy_pack_applied"
    VIBECODING_SCORE_CHANGED = "vibecoding_score_changed"

    # Tier 3: Deprecation Monitoring (Sprint 150)
    DEPRECATED_ENDPOINT_CALLED = "deprecated_endpoint_called"
