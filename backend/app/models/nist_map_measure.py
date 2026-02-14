"""
=========================================================================
NIST AI RMF MAP & MEASURE Models
SDLC Orchestrator - Sprint 157 (Phase 3: COMPLIANCE)

Version: 1.0.0
Date: April 14, 2026
Status: ACTIVE
Authority: CTO Approved
Framework: SDLC 6.0.5
Reference: ADR-051, NIST AI RMF 1.0 Sections MAP & MEASURE

Purpose:
Models for NIST MAP (context & categorization) and MEASURE (metrics &
bias detection) functions:
- ai_systems: AI system inventory with context, stakeholders, dependencies
- performance_metrics: Time-series metrics for performance and bias tracking

Tables:
- ai_systems: MAP context & categorization (JSONB for flexible data)
- performance_metrics: MEASURE time-series with thresholds and demographics

Zero Mock Policy: Production-ready implementation
=========================================================================
"""

from datetime import datetime
from enum import Enum as PyEnum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PgUUID
from sqlalchemy.orm import relationship

from app.db.base_class import Base


# =============================================================================
# Enums
# =============================================================================


class AISystemType(str, PyEnum):
    """AI system type classification."""

    NLP = "nlp"
    VISION = "vision"
    RECOMMENDATION = "recommendation"
    DECISION = "decision"
    GENERATIVE = "generative"


class AIRiskLevel(str, PyEnum):
    """AI system risk level (EU AI Act taxonomy)."""

    MINIMAL = "minimal"
    LIMITED = "limited"
    HIGH = "high"
    UNACCEPTABLE = "unacceptable"


class MetricType(str, PyEnum):
    """Performance metric type classification."""

    ACCURACY = "accuracy"
    PRECISION = "precision"
    RECALL = "recall"
    F1_SCORE = "f1_score"
    LATENCY_P95 = "latency_p95"
    BIAS_SCORE = "bias_score"
    DISPARITY_INDEX = "disparity_index"
    CUSTOM = "custom"


# =============================================================================
# Models
# =============================================================================


class AISystem(Base):
    """
    AI system inventory for NIST MAP function.

    Tracks AI systems with their context, categorization, stakeholders,
    and dependencies. Supports MAP-1.1 (context), MAP-1.2 (stakeholders),
    MAP-2.1 (categorization), and MAP-3.2 (dependencies).
    """

    __tablename__ = "ai_systems"

    id = Column(
        PgUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        doc="Unique AI system identifier",
    )

    project_id = Column(
        PgUUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Associated project",
    )

    name = Column(
        String(200),
        nullable=False,
        doc="AI system name (unique per project)",
    )

    description = Column(
        Text,
        nullable=True,
        doc="AI system description and purpose",
    )

    system_type = Column(
        String(50),
        nullable=False,
        doc="System type: nlp, vision, recommendation, decision, generative",
    )

    risk_level = Column(
        String(20),
        nullable=False,
        default=AIRiskLevel.HIGH.value,
        doc="Risk level: minimal, limited, high, unacceptable",
    )

    purpose = Column(
        Text,
        nullable=True,
        doc="MAP-1.1: Intended purpose of the AI system",
    )

    scope = Column(
        Text,
        nullable=True,
        doc="MAP-1.1: Deployment scope and operational environment",
    )

    stakeholders = Column(
        JSONB,
        nullable=False,
        default=list,
        server_default="[]",
        doc="MAP-1.2: [{role, name, impact_type}]",
    )

    dependencies = Column(
        JSONB,
        nullable=False,
        default=list,
        server_default="[]",
        doc="MAP-3.2: [{name, type, version, provider}]",
    )

    categorization = Column(
        JSONB,
        nullable=True,
        doc="MAP-2.1: {risk_tier, data_sensitivity, autonomy_level, reversibility}",
    )

    owner_id = Column(
        PgUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        doc="System owner for accountability",
    )

    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        doc="Whether the AI system is currently active",
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        doc="Creation timestamp",
    )

    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        doc="Last update timestamp",
    )

    # Relationships
    project = relationship("Project", lazy="joined")
    owner = relationship("User", lazy="joined")
    metrics = relationship(
        "PerformanceMetric",
        back_populates="ai_system",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    __table_args__ = (
        {"comment": "AI systems for NIST MAP context & categorization"},
    )

    def __repr__(self) -> str:
        return f"<AISystem {self.name} type={self.system_type} risk={self.risk_level}>"

    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        return {
            "id": str(self.id),
            "project_id": str(self.project_id),
            "name": self.name,
            "description": self.description,
            "system_type": self.system_type,
            "risk_level": self.risk_level,
            "purpose": self.purpose,
            "scope": self.scope,
            "stakeholders": self.stakeholders or [],
            "dependencies": self.dependencies or [],
            "categorization": self.categorization,
            "owner_id": str(self.owner_id) if self.owner_id else None,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class PerformanceMetric(Base):
    """
    Performance metrics for NIST MEASURE function.

    Time-series metrics supporting:
    - MEASURE-1.1: Performance thresholds and monitoring
    - MEASURE-2.1: Bias detection across demographic groups
    - MEASURE-2.2: Disparity analysis (4/5ths rule)
    - MEASURE-3.1: Metric trending over time
    """

    __tablename__ = "performance_metrics"

    id = Column(
        PgUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        doc="Unique metric identifier",
    )

    project_id = Column(
        PgUUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Associated project",
    )

    ai_system_id = Column(
        PgUUID(as_uuid=True),
        ForeignKey("ai_systems.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Associated AI system",
    )

    metric_type = Column(
        String(50),
        nullable=False,
        doc="Metric type: accuracy, precision, recall, f1_score, latency_p95, bias_score, disparity_index, custom",
    )

    metric_name = Column(
        String(200),
        nullable=False,
        doc="Display name for the metric",
    )

    metric_value = Column(
        Float,
        nullable=False,
        doc="Measured value",
    )

    threshold_min = Column(
        Float,
        nullable=True,
        doc="Minimum acceptable value",
    )

    threshold_max = Column(
        Float,
        nullable=True,
        doc="Maximum acceptable value",
    )

    is_within_threshold = Column(
        Boolean,
        nullable=False,
        default=True,
        doc="Whether value is within threshold bounds",
    )

    unit = Column(
        String(50),
        nullable=True,
        doc="Unit of measurement: %, ms, ratio",
    )

    demographic_group = Column(
        String(100),
        nullable=True,
        doc="MEASURE-2.x demographic group: gender:female, age:18-25",
    )

    tags = Column(
        JSONB,
        nullable=False,
        default=list,
        server_default="[]",
        doc='Metric tags: ["bias","fairness"], ["performance"]',
    )

    measured_at = Column(
        DateTime(timezone=True),
        nullable=False,
        doc="When the measurement was taken",
    )

    measured_by_id = Column(
        PgUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        doc="User who recorded the metric",
    )

    notes = Column(
        Text,
        nullable=True,
        doc="Notes about this measurement",
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        doc="Creation timestamp",
    )

    # Relationships
    project = relationship("Project", lazy="joined")
    ai_system = relationship(
        "AISystem",
        back_populates="metrics",
        lazy="joined",
    )
    measured_by = relationship("User", lazy="joined")

    __table_args__ = (
        {"comment": "Performance metrics for NIST MEASURE function"},
    )

    def __repr__(self) -> str:
        return f"<PerformanceMetric {self.metric_name}={self.metric_value} type={self.metric_type}>"

    def compute_threshold_status(self) -> bool:
        """Compute whether the metric value is within threshold bounds."""
        if self.threshold_min is not None and self.metric_value < self.threshold_min:
            return False
        if self.threshold_max is not None and self.metric_value > self.threshold_max:
            return False
        return True

    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        return {
            "id": str(self.id),
            "project_id": str(self.project_id),
            "ai_system_id": str(self.ai_system_id),
            "metric_type": self.metric_type,
            "metric_name": self.metric_name,
            "metric_value": self.metric_value,
            "threshold_min": self.threshold_min,
            "threshold_max": self.threshold_max,
            "is_within_threshold": self.is_within_threshold,
            "unit": self.unit,
            "demographic_group": self.demographic_group,
            "tags": self.tags or [],
            "measured_at": self.measured_at.isoformat() if self.measured_at else None,
            "measured_by_id": str(self.measured_by_id) if self.measured_by_id else None,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
