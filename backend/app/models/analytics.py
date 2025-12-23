"""
Analytics Database Models

SDLC Stage: 04 - BUILD
Sprint: 41 - AI Safety Foundation
Epic: EP-01/EP-02
Status: IMPLEMENTED
Framework: SDLC 5.1.1

Purpose:
Store product telemetry events locally for audit trail and offline analysis.
Complements Mixpanel with 90-day retention for GDPR compliance.

Tables:
1. analytics_events - All product events (user actions, AI validations, gates)
2. ai_code_events - AI-generated code detection and safety checks (future Sprint 42)

Retention Policy:
- analytics_events: 90 days (GDPR compliance)
- ai_code_events: 2 years (security audit requirement)
"""

from datetime import datetime
from uuid import UUID, uuid4
from sqlalchemy import Column, String, Integer, DateTime, JSON, ForeignKey, Index, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class AnalyticsEvent(Base):
    """
    Product analytics events table.

    Tracks all user interactions, AI Safety events, and gate evaluations.
    Used for funnel analysis, retention metrics, and product analytics.

    Schema Evolution:
    - v1.0: Initial schema (Sprint 41)
    - v1.1: Add session_id, device_type (Sprint 42)
    - v1.2: Add ai_tool_version for versioning tracking (Sprint 43)

    Indexes:
    - user_id + created_at: User timeline queries
    - event_name + created_at: Event-specific aggregations
    - created_at: Cleanup queries (delete old events)

    Partitioning:
    - Consider monthly partitions if >10M events/month (Sprint 45+)
    """

    __tablename__ = "analytics_events"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    event_name = Column(String(100), nullable=False, index=True)
    properties = Column(JSON, nullable=True)  # Event metadata (max 100KB)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    # Relationships
    user = relationship("User", back_populates="analytics_events")

    # Indexes for performance
    __table_args__ = (
        Index("ix_analytics_user_created", "user_id", "created_at"),
        Index("ix_analytics_event_created", "event_name", "created_at"),
    )

    def __repr__(self):
        return f"<AnalyticsEvent {self.event_name} by user {self.user_id}>"


class AICodeEvent(Base):
    """
    AI-generated code detection and safety events.

    Tracks every PR/commit for AI tool usage, validates against SDLC policies,
    and stores violation details for security audits.

    Use Cases:
    1. AI Safety Layer validation (EP-02)
    2. Design Partner feedback collection (EP-03)
    3. Security audit trail (OWASP ASVS L2 requirement)

    Schema:
    - pr_id: Pull request ID (GitHub PR number or internal UUID)
    - commit_sha: Git commit hash (40 chars)
    - ai_tool_detected: AI tool name (claude, cursor, copilot, windsurf, etc)
    - confidence_score: Detection confidence (0.0-1.0, ML model output)
    - validation_result: SDLC policy validation result (passed/failed/warning)
    - violations: List of policy violations (YAML array)
    - duration_ms: Validation duration in milliseconds

    Retention: 2 years (security audit requirement)
    """

    __tablename__ = "ai_code_events"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    project_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # PR/Commit identification
    pr_id = Column(String(100), nullable=True, index=True)  # GitHub PR number or UUID
    commit_sha = Column(String(40), nullable=True, index=True)  # Git commit hash
    branch_name = Column(String(255), nullable=True)

    # AI Detection
    ai_tool_detected = Column(String(50), nullable=True, index=True)  # claude, cursor, copilot
    confidence_score = Column(Integer, nullable=True)  # 0-100 (ML model confidence)
    detection_method = Column(String(50), nullable=True)  # pattern, ml, comment, metadata

    # SDLC Validation
    validation_result = Column(String(20), nullable=False, index=True)  # passed, failed, warning
    violations = Column(JSON, nullable=True)  # Array of violation objects
    policy_pack_id = Column(String(100), nullable=True)  # OPA policy pack used

    # Performance metrics
    duration_ms = Column(Integer, nullable=True)  # Validation duration
    files_scanned = Column(Integer, nullable=True)  # Number of files scanned
    lines_changed = Column(Integer, nullable=True)  # Lines added + deleted

    # Audit trail
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    validated_by_user_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="ai_code_events")
    project = relationship("Project", back_populates="ai_code_events")
    validated_by = relationship("User", foreign_keys=[validated_by_user_id])
    overrides = relationship("ValidationOverride", back_populates="event", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("ix_ai_code_project_created", "project_id", "created_at"),
        Index("ix_ai_code_tool_result", "ai_tool_detected", "validation_result"),
        Index("ix_ai_code_pr_commit", "pr_id", "commit_sha"),
    )

    def __repr__(self):
        return f"<AICodeEvent PR-{self.pr_id} tool={self.ai_tool_detected} result={self.validation_result}>"
