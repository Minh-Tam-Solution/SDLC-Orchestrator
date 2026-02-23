"""
Pilot Tracking Models - Sprint 49.

Track pilot program participants and TTFV (Time To First Value) metrics:
- PilotParticipant: Individual pilot user profile
- PilotSession: End-to-end onboarding journey with TTFV tracking
- PilotFeedback: Post-generation satisfaction survey

SDLC Stage: 04 - BUILD
Sprint: 49 - EP-06 Pilot Execution + Metrics Hardening
Framework: SDLC 5.1.3

Success Metrics (CEO Approved):
- 10 Vietnamese SME founders
- TTFV < 30 minutes
- Satisfaction score 8/10
- Quality gate pass rate 95%+
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
    Float,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class PilotStatus(str, Enum):
    """Pilot participant status."""

    INVITED = "invited"  # Sent invitation
    REGISTERED = "registered"  # Created account
    ONBOARDING = "onboarding"  # In onboarding flow
    ACTIVE = "active"  # Completed first generation
    CHURNED = "churned"  # Dropped off
    COMPLETED = "completed"  # Finished pilot program


class PilotDomain(str, Enum):
    """Vietnamese SME domains for pilot."""

    FNB = "fnb"  # Food & Beverage (Nhà hàng, Quán ăn)
    HOSPITALITY = "hospitality"  # Hotel/Homestay (Khách sạn)
    RETAIL = "retail"  # Retail shop (Cửa hàng bán lẻ)
    ECOMMERCE = "ecommerce"  # E-commerce (Thương mại điện tử)
    HRM = "hrm"  # HR Management (Quản lý nhân sự)
    CRM = "crm"  # CRM (Quản lý quan hệ khách hàng)


class OnboardingStage(str, Enum):
    """Stages in the onboarding funnel."""

    STARTED = "started"  # Clicked "Create App"
    DOMAIN_SELECTED = "domain_selected"  # Selected business domain
    APP_NAMED = "app_named"  # Entered app name
    FEATURES_SELECTED = "features_selected"  # Selected modules/features
    SCALE_SELECTED = "scale_selected"  # Selected business scale
    BLUEPRINT_GENERATED = "blueprint_generated"  # IR generated
    CODE_GENERATING = "code_generating"  # Waiting for code generation
    CODE_GENERATED = "code_generated"  # Code generation complete
    QUALITY_GATE_PASSED = "quality_gate_passed"  # Passed quality checks
    DEPLOYED = "deployed"  # App deployed (optional)
    COMPLETED = "completed"  # TTFV achieved


class PilotParticipant(Base):
    """
    Pilot program participant.

    Tracks Vietnamese SME founders in the EP-06 pilot program.
    Target: 10 participants across F&B, Hospitality, Retail domains.
    """

    __tablename__ = "pilot_participants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # Participant info
    status = Column(String(20), nullable=False, default=PilotStatus.INVITED.value, index=True)
    domain = Column(String(20), nullable=True, index=True)  # F&B, Hospitality, Retail
    company_name = Column(String(255), nullable=True)
    company_size = Column(String(20), nullable=True)  # micro, small, medium

    # Recruitment tracking
    invited_at = Column(DateTime, nullable=True)
    registered_at = Column(DateTime, nullable=True)
    first_login_at = Column(DateTime, nullable=True)
    activated_at = Column(DateTime, nullable=True)  # First successful generation

    # Pilot metrics
    total_sessions = Column(Integer, default=0)
    total_generations = Column(Integer, default=0)
    successful_generations = Column(Integer, default=0)
    quality_gate_passes = Column(Integer, default=0)
    quality_gate_failures = Column(Integer, default=0)

    # TTFV metrics (aggregated)
    best_ttfv_seconds = Column(Integer, nullable=True)  # Best TTFV achieved
    avg_ttfv_seconds = Column(Integer, nullable=True)  # Average TTFV

    # Satisfaction
    latest_satisfaction_score = Column(Integer, nullable=True)  # 1-10
    would_recommend = Column(Boolean, nullable=True)  # NPS indicator

    # Metadata
    referral_source = Column(String(100), nullable=True)  # How they joined
    notes = Column(Text, nullable=True)  # Admin notes
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="pilot_participant")
    sessions = relationship("PilotSession", back_populates="participant", cascade="all, delete-orphan")
    satisfaction_surveys = relationship("PilotSatisfactionSurvey", back_populates="participant", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("ix_pilot_participant_status_domain", "status", "domain"),
    )

    def __repr__(self) -> str:
        return f"<PilotParticipant {self.id} status={self.status}>"


class PilotSession(Base):
    """
    Individual pilot session tracking TTFV.

    Tracks the complete journey from "Create App" to "Working App".
    TTFV = Time from session start to quality_gate_passed_at.
    """

    __tablename__ = "pilot_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    participant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pilot_participants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    onboarding_session_id = Column(String(36), nullable=True, index=True)  # Links to OnboardingSession

    # Session lifecycle
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    completed_at = Column(DateTime, nullable=True)
    abandoned_at = Column(DateTime, nullable=True)

    # Current stage tracking
    current_stage = Column(String(30), nullable=False, default=OnboardingStage.STARTED.value)
    stage_history = Column(JSONB, nullable=True)  # [{stage, timestamp, duration_ms}]

    # Stage timestamps (for detailed funnel analysis)
    domain_selected_at = Column(DateTime, nullable=True)
    app_named_at = Column(DateTime, nullable=True)
    features_selected_at = Column(DateTime, nullable=True)
    scale_selected_at = Column(DateTime, nullable=True)
    blueprint_generated_at = Column(DateTime, nullable=True)
    code_generation_started_at = Column(DateTime, nullable=True)
    code_generation_completed_at = Column(DateTime, nullable=True)
    quality_gate_passed_at = Column(DateTime, nullable=True)
    deployed_at = Column(DateTime, nullable=True)

    # TTFV calculation (primary Sprint 49 metric)
    ttfv_seconds = Column(Integer, nullable=True)  # Total time start → quality_gate_passed
    ttfv_target_met = Column(Boolean, nullable=True)  # < 30 minutes = True

    # Generation details
    domain = Column(String(20), nullable=True)
    app_name = Column(String(100), nullable=True)
    selected_features = Column(JSONB, nullable=True)  # List of selected features
    scale = Column(String(20), nullable=True)

    # Code generation metrics
    generation_provider = Column(String(20), nullable=True)  # ollama, claude, etc
    generation_time_ms = Column(Integer, nullable=True)
    tokens_used = Column(Integer, nullable=True)
    files_generated = Column(Integer, nullable=True)
    lines_of_code = Column(Integer, nullable=True)

    # Quality gate results
    quality_gate_passed = Column(Boolean, nullable=True)
    quality_gate_score = Column(Float, nullable=True)  # 0-100
    quality_gate_details = Column(JSONB, nullable=True)

    # Error tracking
    errors = Column(JSONB, nullable=True)  # List of errors encountered
    error_count = Column(Integer, default=0)

    # User context
    user_agent = Column(String(512), nullable=True)
    ip_address = Column(String(45), nullable=True)

    # Metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    participant = relationship("PilotParticipant", back_populates="sessions")

    # Indexes
    __table_args__ = (
        Index("ix_pilot_session_participant_started", "participant_id", "started_at"),
        Index("ix_pilot_session_ttfv", "ttfv_seconds", "ttfv_target_met"),
    )

    def __repr__(self) -> str:
        return f"<PilotSession {self.id} stage={self.current_stage}>"

    def calculate_ttfv(self) -> Optional[int]:
        """Calculate TTFV in seconds if quality gate passed."""
        if self.started_at and self.quality_gate_passed_at:
            delta = self.quality_gate_passed_at - self.started_at
            return int(delta.total_seconds())
        return None

    def update_ttfv(self) -> None:
        """Update TTFV fields based on current timestamps."""
        ttfv = self.calculate_ttfv()
        if ttfv is not None:
            self.ttfv_seconds = ttfv
            self.ttfv_target_met = ttfv <= 1800  # 30 minutes = 1800 seconds


class PilotSatisfactionSurvey(Base):
    """
    Pilot satisfaction survey.

    Collected after code generation to measure satisfaction.
    Target: 8/10 average satisfaction score.

    Note: Different from PilotFeedback (bug reports) in feedback.py.
    This is specifically for TTFV satisfaction measurement.
    """

    __tablename__ = "pilot_satisfaction_surveys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    participant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pilot_participants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pilot_sessions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Core satisfaction metrics
    overall_score = Column(Integer, nullable=False)  # 1-10
    would_recommend = Column(Boolean, nullable=True)  # NPS indicator
    ease_of_use_score = Column(Integer, nullable=True)  # 1-10
    code_quality_score = Column(Integer, nullable=True)  # 1-10
    speed_score = Column(Integer, nullable=True)  # 1-10

    # Qualitative feedback
    what_went_well = Column(Text, nullable=True)
    what_needs_improvement = Column(Text, nullable=True)
    feature_requests = Column(Text, nullable=True)
    bugs_reported = Column(Text, nullable=True)

    # Structured feedback
    pain_points = Column(JSONB, nullable=True)  # List of pain points
    favorite_features = Column(JSONB, nullable=True)  # List of favorite features
    missing_features = Column(JSONB, nullable=True)  # List of missing features

    # Context
    feedback_context = Column(String(50), nullable=True)  # post_generation, weekly, exit
    submitted_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    # Metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    participant = relationship("PilotParticipant", back_populates="satisfaction_surveys")

    # Indexes
    __table_args__ = (
        Index("ix_pilot_feedback_participant_submitted", "participant_id", "submitted_at"),
        Index("ix_pilot_feedback_score", "overall_score"),
    )

    def __repr__(self) -> str:
        return f"<PilotFeedback {self.id} score={self.overall_score}>"


class PilotDailyMetrics(Base):
    """
    Daily aggregated pilot metrics for Sprint 49 KPI tracking.

    Aggregates all pilot sessions for a given day.
    Used for dashboard and CEO reporting.
    """

    __tablename__ = "pilot_daily_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    date = Column(DateTime, nullable=False, unique=True, index=True)

    # Participant metrics
    total_participants = Column(Integer, default=0)
    active_participants = Column(Integer, default=0)  # Had activity today
    new_participants = Column(Integer, default=0)

    # Session metrics
    total_sessions = Column(Integer, default=0)
    completed_sessions = Column(Integer, default=0)
    abandoned_sessions = Column(Integer, default=0)

    # TTFV metrics (Sprint 49 primary KPI)
    ttfv_p50_seconds = Column(Integer, nullable=True)  # Median TTFV
    ttfv_p90_seconds = Column(Integer, nullable=True)  # 90th percentile TTFV
    ttfv_avg_seconds = Column(Integer, nullable=True)  # Average TTFV
    ttfv_min_seconds = Column(Integer, nullable=True)  # Best TTFV
    ttfv_target_met_count = Column(Integer, default=0)  # Sessions meeting <30min target
    ttfv_target_met_percent = Column(Float, nullable=True)

    # Generation metrics
    total_generations = Column(Integer, default=0)
    successful_generations = Column(Integer, default=0)
    failed_generations = Column(Integer, default=0)
    generation_success_rate = Column(Float, nullable=True)

    # Quality gate metrics
    quality_gates_evaluated = Column(Integer, default=0)
    quality_gates_passed = Column(Integer, default=0)
    quality_gate_pass_rate = Column(Float, nullable=True)  # Target: 95%+

    # Satisfaction metrics
    feedback_count = Column(Integer, default=0)
    avg_satisfaction_score = Column(Float, nullable=True)  # Target: 8/10
    would_recommend_count = Column(Integer, default=0)
    would_recommend_percent = Column(Float, nullable=True)

    # Cost metrics
    total_tokens_used = Column(Integer, default=0)
    estimated_cost_usd = Column(Float, nullable=True)

    # Domain breakdown
    fnb_sessions = Column(Integer, default=0)
    hospitality_sessions = Column(Integer, default=0)
    retail_sessions = Column(Integer, default=0)

    # Metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<PilotDailyMetrics {self.date}>"
