"""
Usage Tracking Models - Sprint 24 Day 4

Track user activity and feature usage for pilot analytics:
- User sessions
- Page views
- Feature usage events
- API calls tracking
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    Boolean,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class EventType(str, Enum):
    """Types of usage events."""

    # Session events
    SESSION_START = "session_start"
    SESSION_END = "session_end"

    # Page views
    PAGE_VIEW = "page_view"

    # Feature usage
    FEATURE_USE = "feature_use"

    # Actions
    GATE_VIEW = "gate_view"
    GATE_EVALUATE = "gate_evaluate"
    EVIDENCE_UPLOAD = "evidence_upload"
    EVIDENCE_VIEW = "evidence_view"
    COMPLIANCE_SCAN = "compliance_scan"
    COMPLIANCE_VIEW = "compliance_view"
    PROJECT_VIEW = "project_view"
    PROJECT_CREATE = "project_create"
    DASHBOARD_VIEW = "dashboard_view"
    FEEDBACK_SUBMIT = "feedback_submit"

    # API events
    API_CALL = "api_call"

    # Errors
    ERROR = "error"


class UserSession(Base):
    """Track user sessions for analytics."""

    __tablename__ = "user_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    session_token = Column(String(255), nullable=False, unique=True, index=True)

    # Session info
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True, index=True)

    # Duration in seconds (calculated on end)
    duration_seconds = Column(Integer, nullable=True)

    # Device/browser info
    user_agent = Column(String(512), nullable=True)
    ip_address = Column(String(45), nullable=True)  # IPv6 max length
    device_type = Column(String(50), nullable=True)  # desktop, mobile, tablet
    browser = Column(String(100), nullable=True)
    os = Column(String(100), nullable=True)

    # Location (if available)
    country = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)

    # Metrics
    page_views_count = Column(Integer, default=0)
    events_count = Column(Integer, default=0)

    # Relationships
    user = relationship("User", back_populates="sessions")
    events = relationship("UsageEvent", back_populates="session", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<UserSession {self.id} user={self.user_id}>"


class UsageEvent(Base):
    """Track individual usage events."""

    __tablename__ = "usage_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("user_sessions.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # Event info
    event_type = Column(String(50), nullable=False, index=True)
    event_name = Column(String(100), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    # Context
    page_url = Column(String(512), nullable=True)
    referrer_url = Column(String(512), nullable=True)

    # Resource being accessed
    resource_type = Column(String(50), nullable=True)  # project, gate, evidence, etc
    resource_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    # Additional event data
    event_metadata = Column(JSONB, nullable=True)

    # Performance
    duration_ms = Column(Integer, nullable=True)  # How long the action took

    # Relationships
    user = relationship("User", back_populates="usage_events")
    session = relationship("UserSession", back_populates="events")

    def __repr__(self) -> str:
        return f"<UsageEvent {self.event_type}:{self.event_name}>"


class FeatureUsage(Base):
    """Aggregated feature usage statistics."""

    __tablename__ = "feature_usage"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # Time period
    date = Column(DateTime, nullable=False, index=True)  # Daily aggregation
    period_type = Column(String(20), default="daily")  # daily, weekly, monthly

    # Feature info
    feature_name = Column(String(100), nullable=False, index=True)
    feature_category = Column(String(50), nullable=True)

    # Metrics
    total_uses = Column(Integer, default=0)
    unique_users = Column(Integer, default=0)
    avg_duration_ms = Column(Integer, nullable=True)

    # Success/failure
    success_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)

    # Metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<FeatureUsage {self.feature_name} on {self.date}>"


class PilotMetrics(Base):
    """Track pilot program success metrics."""

    __tablename__ = "pilot_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # Time period
    date = Column(DateTime, nullable=False, index=True)
    period_type = Column(String(20), default="daily")

    # User metrics
    total_users = Column(Integer, default=0)
    active_users = Column(Integer, default=0)  # Users with activity today
    new_users = Column(Integer, default=0)

    # Engagement metrics
    total_sessions = Column(Integer, default=0)
    avg_session_duration = Column(Integer, default=0)  # seconds
    total_page_views = Column(Integer, default=0)

    # Feature adoption
    users_using_gates = Column(Integer, default=0)
    users_using_evidence = Column(Integer, default=0)
    users_using_compliance = Column(Integer, default=0)

    # Gate metrics
    gates_evaluated = Column(Integer, default=0)
    gates_passed = Column(Integer, default=0)
    gates_failed = Column(Integer, default=0)

    # Evidence metrics
    evidence_uploaded = Column(Integer, default=0)
    evidence_size_bytes = Column(Integer, default=0)

    # Compliance metrics
    compliance_scans = Column(Integer, default=0)
    avg_compliance_score = Column(Integer, nullable=True)

    # Feedback metrics
    feedback_submitted = Column(Integer, default=0)
    bugs_reported = Column(Integer, default=0)
    features_requested = Column(Integer, default=0)

    # Metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<PilotMetrics {self.date}>"
