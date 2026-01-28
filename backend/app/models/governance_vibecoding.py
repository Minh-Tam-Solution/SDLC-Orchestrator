"""
SQLAlchemy models for Sprint 118 Governance System v2.0

PART 2: VIBECODING SYSTEM (7 models)
- VibecodingSignal
- VibecodingIndexHistory
- ProgressiveRoutingRule
- KillSwitchTrigger
- KillSwitchEvent
- TierSpecificRequirement
- SpecValidationResult

References:
- D1: docs/02-design/02-System-Architecture/Database-Schema-Governance-v2.md
- Migration: backend/alembic/versions/s118_001_governance_v2_tables.py
- SPEC-0001: Anti-Vibecoding Quality Assurance System
"""
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    DateTime,
    Text,
    ForeignKey,
    Index,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base_class import Base


class VibecodingSignal(Base):
    """
    Individual signal measurements for vibecoding index.

    5 Signals (SPEC-0001):
    1. Intent Clarity (30% weight) - 0-100 scale
    2. Code Ownership (25% weight) - 0-100 scale
    3. Context Completeness (20% weight) - 0-100 scale
    4. AI Attestation (15% weight) - boolean → 0 or 100
    5. Rejection Rate (10% weight) - 0.0-1.0 → 0-100 scale

    Time-series data for historical analysis and trending.
    """
    __tablename__ = "vibecoding_signals"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    project_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Project this signal belongs to",
    )
    submission_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="Unique submission identifier (PR number, commit SHA, etc.)",
    )
    signal_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Signal type: intent_clarity, code_ownership, context_completeness, ai_attestation, rejection_rate",
    )
    signal_value: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Signal value (0-100 scale)",
    )
    signal_weight: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Weight in index calculation (0.0-1.0)",
    )
    evidence: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Evidence supporting this signal value",
    )
    measured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
        comment="Signal measurement timestamp",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Relationships
    project = relationship("Project", back_populates="vibecoding_signals")

    # Composite index for signal aggregation
    __table_args__ = (
        Index("idx_vibecoding_signals_submission_type", "submission_id", "signal_type"),
        # Time-series index for historical analysis (BRIN for timestamp columns)
        Index("idx_vibecoding_signals_measured_at_brin", "measured_at", postgresql_using="brin"),
    )

    def __repr__(self) -> str:
        return f"<VibecodingSignal(submission_id='{self.submission_id}', type='{self.signal_type}', value={self.signal_value})>"


class VibecodingIndexHistory(Base):
    """
    Historical record of vibecoding index calculations.

    Immutable audit trail - index calculations are never updated.
    Each submission gets one index calculation entry.

    Index Formula (SPEC-0001):
    index = (
        (100 - intent_clarity) * 0.30 +
        (100 - code_ownership) * 0.25 +
        (100 - context_completeness) * 0.20 +
        (0 if ai_attestation else 100) * 0.15 +
        (rejection_rate * 100) * 0.10
    )

    Zones:
    - GREEN (0-20): AUTO_MERGE
    - YELLOW (20-40): HUMAN_REVIEW (4h SLA)
    - ORANGE (40-60): SENIOR_REVIEW (2h SLA)
    - RED (60-100): BLOCK (1h SLA, council review)
    """
    __tablename__ = "vibecoding_index_history"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    project_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Project this index belongs to",
    )
    submission_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="Unique submission identifier",
    )
    index_score: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Calculated vibecoding index (0-100)",
    )
    zone: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        comment="Zone: GREEN, YELLOW, ORANGE, RED",
    )
    routing_decision: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Routing decision: AUTO_MERGE, HUMAN_REVIEW, SENIOR_REVIEW, BLOCK",
    )
    signal_breakdown: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        comment="Breakdown of 5 signals and their contributions",
    )
    calculated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
        comment="Index calculation timestamp",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Relationships
    project = relationship("Project", back_populates="vibecoding_index_history")

    # Time-series index for trend analysis (BRIN for timestamp)
    __table_args__ = (
        Index("idx_vibecoding_index_history_calculated_at_brin", "calculated_at", postgresql_using="brin"),
        Index("idx_vibecoding_index_history_project_zone", "project_id", "zone", "calculated_at"),
    )

    def __repr__(self) -> str:
        return f"<VibecodingIndexHistory(submission_id='{self.submission_id}', score={self.index_score}, zone='{self.zone}')>"


class ProgressiveRoutingRule(Base):
    """
    Configurable routing rules for vibecoding zones.

    Default Rules (seeded in migration):
    - GREEN (0-20): AUTO_MERGE, no SLA
    - YELLOW (20-40): HUMAN_REVIEW, 4h SLA, escalate to senior
    - ORANGE (40-60): SENIOR_REVIEW, 2h SLA, escalate to council
    - RED (60-100): BLOCK, 1h SLA, escalate to CTO

    Configurable per organization for different risk tolerance.
    """
    __tablename__ = "progressive_routing_rules"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    zone: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        unique=True,
        comment="Zone: GREEN, YELLOW, ORANGE, RED",
    )
    threshold_min: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Minimum index score for this zone (inclusive)",
    )
    threshold_max: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Maximum index score for this zone (exclusive)",
    )
    routing_action: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Action: AUTO_MERGE, HUMAN_REVIEW, SENIOR_REVIEW, BLOCK",
    )
    sla_minutes: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="SLA for review in minutes (NULL = no SLA)",
    )
    escalation_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="false",
        comment="Whether to escalate if SLA breached",
    )
    escalation_target: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Escalation target: senior_review, council, cto",
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Human-readable zone description",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    def __repr__(self) -> str:
        return f"<ProgressiveRoutingRule(zone='{self.zone}', action='{self.routing_action}', sla={self.sla_minutes}min)>"


class KillSwitchTrigger(Base):
    """
    Kill switch trigger conditions configuration.

    Default Triggers (seeded in migration):
    1. rejection_rate_high: >80% in 30min → rollback_to_warning (critical)
    2. latency_high: >500ms p95 in 15min → alert_cto (major)
    3. security_cves: >=5 critical CVEs in 1min → block_all_merges (critical)

    Configurable per organization for different operational thresholds.
    """
    __tablename__ = "kill_switch_triggers"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    trigger_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        comment="Trigger identifier: rejection_rate_high, latency_high, security_cves",
    )
    metric_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Metric to monitor: rejection_rate, api_latency_p95, critical_cves_count",
    )
    threshold_value: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Threshold value to trigger kill switch",
    )
    threshold_operator: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        comment="Comparison operator: >, <, >=, <=, ==",
    )
    window_minutes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Time window for metric evaluation (minutes)",
    )
    action: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Action to take: rollback_to_warning, block_all_merges, alert_cto",
    )
    severity: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Severity: critical, major, minor",
    )
    enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="true",
        comment="Whether this trigger is active",
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Human-readable trigger description",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    events = relationship("KillSwitchEvent", back_populates="trigger", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<KillSwitchTrigger(name='{self.trigger_name}', metric='{self.metric_name}', threshold={self.threshold_value})>"


class KillSwitchEvent(Base):
    """
    Historical record of kill switch activations.

    Immutable audit trail - events are never updated.
    Tracks trigger activation, action taken, and resolution.

    SLA for resolution:
    - critical: 1 hour
    - major: 4 hours
    - minor: 24 hours
    """
    __tablename__ = "kill_switch_events"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    trigger_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("kill_switch_triggers.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Trigger that caused this event",
    )
    triggered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
        comment="Kill switch activation timestamp",
    )
    metric_value: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Metric value that triggered kill switch",
    )
    threshold_breached: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Threshold that was breached",
    )
    action_taken: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Action executed: rollback_to_warning, block_all_merges, alert_cto",
    )
    severity: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Severity: critical, major, minor",
    )
    notified_users: Mapped[Optional[list]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Array of user IDs notified",
    )
    resolution_notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Human-entered resolution notes",
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        comment="Event resolution timestamp",
    )
    resolved_by_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="User who resolved this event",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Relationships
    trigger = relationship("KillSwitchTrigger", back_populates="events")
    resolved_by = relationship("User")

    # Time-series index for event analysis (BRIN for timestamp)
    __table_args__ = (
        Index("idx_kill_switch_events_triggered_at_brin", "triggered_at", postgresql_using="brin"),
    )

    def __repr__(self) -> str:
        return f"<KillSwitchEvent(trigger_id={self.trigger_id}, severity='{self.severity}', resolved={self.resolved_at is not None})>"


class TierSpecificRequirement(Base):
    """
    Tier-specific requirement variations (LITE/STANDARD/PRO/ENTERPRISE).

    4-Tier Classification (SDLC Framework 5.3.0):
    - LITE: Minimal requirements (startups, prototypes)
    - STANDARD: Normal requirements (SME, standard projects)
    - PROFESSIONAL: Enhanced requirements (mid-sized companies)
    - ENTERPRISE: Full requirements (large enterprises, regulated industries)

    Examples:
    - evidence_vault_required: LITE=false, STANDARD=true, PRO=true, ENTERPRISE=true
    - mfa_required: LITE=false, STANDARD=false, PRO=true, ENTERPRISE=true
    - audit_retention_days: LITE=30, STANDARD=90, PRO=365, ENTERPRISE=2555 (7 years)
    """
    __tablename__ = "tier_specific_requirements"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    requirement_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Requirement identifier (e.g., evidence_vault_required)",
    )
    tier: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        comment="Tier: LITE, STANDARD, PROFESSIONAL, ENTERPRISE",
    )
    is_required: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        comment="Whether requirement is mandatory for this tier",
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Requirement description",
    )
    validation_rule: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="OPA policy or validation logic",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Unique constraint: One requirement per tier
    __table_args__ = (
        UniqueConstraint("requirement_name", "tier", name="idx_tier_specific_requirements_name_tier_unique"),
    )

    def __repr__(self) -> str:
        return f"<TierSpecificRequirement(name='{self.requirement_name}', tier='{self.tier}', required={self.is_required})>"


class SpecValidationResult(Base):
    """
    Validation results for specifications.

    Validation Types:
    - frontmatter: YAML frontmatter compliance (SPEC-0002)
    - requirements: Functional requirements completeness
    - acceptance_criteria: Acceptance criteria testability
    - cross_references: Cross-reference integrity

    Tracks errors (blocking) and warnings (non-blocking).
    """
    __tablename__ = "spec_validation_results"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    spec_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("governance_specifications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Specification being validated",
    )
    validation_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Type: frontmatter, requirements, acceptance_criteria, cross_references",
    )
    is_valid: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        index=True,
        comment="Overall validation result",
    )
    errors: Mapped[Optional[list]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Array of validation errors",
    )
    warnings: Mapped[Optional[list]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Array of validation warnings",
    )
    validated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
        comment="Validation timestamp",
    )
    validator_version: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="Version of validator used",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Relationships
    specification = relationship("GovernanceSpecification", back_populates="validation_results")

    # Time-series index for validation history (BRIN for timestamp)
    __table_args__ = (
        Index("idx_spec_validation_results_validated_at_brin", "validated_at", postgresql_using="brin"),
    )

    def __repr__(self) -> str:
        return f"<SpecValidationResult(spec_id={self.spec_id}, type='{self.validation_type}', valid={self.is_valid})>"
