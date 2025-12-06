"""
File: backend/app/models/feedback.py
Version: 1.0.0
Status: ACTIVE - STAGE 03 (BUILD)
Date: 2025-12-03
Authority: Backend Lead + CTO Approved
Foundation: SDLC 4.9 Complete Lifecycle, Zero Mock Policy

Description:
SQLAlchemy models for pilot feedback collection system.
Supports bug reports, feature requests, and general feedback.

Sprint 24 Day 2: Pilot Onboarding Guide
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import (
    Column,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class FeedbackType(str, Enum):
    """Types of feedback submissions."""
    BUG = "bug"
    FEATURE_REQUEST = "feature_request"
    IMPROVEMENT = "improvement"
    QUESTION = "question"
    OTHER = "other"


class FeedbackPriority(str, Enum):
    """Priority levels for feedback."""
    P0_CRITICAL = "p0_critical"
    P1_HIGH = "p1_high"
    P2_MEDIUM = "p2_medium"
    P3_LOW = "p3_low"


class FeedbackStatus(str, Enum):
    """Status of feedback submission."""
    NEW = "new"
    TRIAGED = "triaged"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"
    WONT_FIX = "wont_fix"


class PilotFeedback(Base):
    """
    Pilot feedback submission model.

    Attributes:
        id: Unique identifier
        user_id: User who submitted feedback
        type: Type of feedback (bug, feature, etc.)
        priority: Priority level
        status: Current status
        title: Short summary
        description: Detailed description
        steps_to_reproduce: For bugs - reproduction steps
        expected_behavior: For bugs - what should happen
        actual_behavior: For bugs - what actually happens
        browser: Browser information
        os: Operating system
        screenshot_url: URL to attached screenshot
        page_url: URL where issue occurred
        created_at: Submission timestamp
        updated_at: Last update timestamp
        resolved_at: Resolution timestamp
        resolved_by: User who resolved
        resolution_notes: Notes about resolution
    """

    __tablename__ = "pilot_feedback"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    type = Column(
        SQLEnum(FeedbackType),
        nullable=False,
        default=FeedbackType.OTHER,
        index=True,
    )
    priority = Column(
        SQLEnum(FeedbackPriority),
        nullable=True,
        index=True,
    )
    status = Column(
        SQLEnum(FeedbackStatus),
        nullable=False,
        default=FeedbackStatus.NEW,
        index=True,
    )
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    steps_to_reproduce = Column(Text, nullable=True)
    expected_behavior = Column(Text, nullable=True)
    actual_behavior = Column(Text, nullable=True)
    browser = Column(String(100), nullable=True)
    os = Column(String(100), nullable=True)
    screenshot_url = Column(String(512), nullable=True)
    page_url = Column(String(512), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    resolution_notes = Column(Text, nullable=True)

    # Relationships
    user = relationship("User", foreign_keys=[user_id], backref="feedback_submitted")
    resolver = relationship("User", foreign_keys=[resolved_by])

    def __repr__(self) -> str:
        return f"<PilotFeedback {self.id}: {self.title[:30]}...>"


class FeedbackComment(Base):
    """
    Comments on feedback submissions.

    Allows team members to discuss and collaborate on feedback items.
    """

    __tablename__ = "feedback_comments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    feedback_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pilot_feedback.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    feedback = relationship("PilotFeedback", backref="comments")
    user = relationship("User")

    def __repr__(self) -> str:
        return f"<FeedbackComment {self.id} on {self.feedback_id}>"
