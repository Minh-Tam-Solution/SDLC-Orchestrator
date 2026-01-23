"""
=========================================================================
Learning Aggregation Model - Periodic Pattern Synthesis (EP-11)
SDLC Orchestrator - Sprint 100 (Feedback Learning Service)

Version: 1.0.0
Date: January 23, 2026
Status: ACTIVE - Sprint 100 Implementation
Authority: Backend Lead + CTO Approved
Framework: SDLC 5.1.3 SASE Integration
Reference: docs/02-design/14-Technical-Specs/Feedback-Learning-Service-Design.md

Purpose:
- Store monthly/quarterly aggregations of PR learnings
- Generate pattern updates for CLAUDE.md
- Create decomposition hints from aggregated learnings

Aggregation Workflow:
1. Monthly job: Aggregate learnings → Generate hints
2. Quarterly job: Synthesize → CLAUDE.md suggestions
3. Human review: Apply approved changes
4. Track effectiveness of applied changes

Zero Mock Policy: Real SQLAlchemy model with all fields
=========================================================================
"""

from datetime import datetime, date
from typing import Optional, List, Any, TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import (
    DateTime,
    Date,
    ForeignKey,
    Integer,
    String,
    Index,
    CheckConstraint,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.db.base_class import Base

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.user import User


# Period types
PERIOD_TYPES = ["weekly", "monthly", "quarterly"]

# Aggregation status
AGGREGATION_STATUS = ["pending", "processed", "applied", "rejected"]


class LearningAggregation(Base):
    """
    Learning Aggregation model for periodic pattern synthesis.

    Purpose:
        - Store monthly/quarterly aggregations of PR learnings
        - Generate pattern updates for CLAUDE.md
        - Create decomposition hints from aggregated learnings

    Attributes:
        id: Unique identifier (UUID v4)
        project_id: Associated project
        period_type: Type of period (monthly, quarterly)
        period_start: Start date of the period
        period_end: End date of the period
        total_learnings: Number of learnings in period
        by_feedback_type: Breakdown by feedback type
        top_patterns: Most common patterns identified

    Relationships:
        project: Associated project
        processed_by: User who processed the aggregation
    """

    __tablename__ = "learning_aggregations"

    # Primary Key
    id: Mapped[uuid4] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        comment="Unique aggregation ID (UUID v4)",
    )

    # Foreign Keys
    project_id: Mapped[uuid4] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Associated project ID",
    )

    processed_by: Mapped[Optional[uuid4]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="User who processed/reviewed the aggregation",
    )

    # Aggregation Period
    period_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Period type: weekly, monthly, quarterly",
    )

    period_start: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Start date of the period",
    )

    period_end: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="End date of the period",
    )

    # Statistics
    total_learnings: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default="0",
        comment="Total number of learnings in period",
    )

    by_feedback_type: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        server_default="{}",
        comment='Breakdown: {"pattern_violation": 5, "edge_case": 3, ...}',
    )

    by_severity: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        server_default="{}",
        comment='Breakdown: {"critical": 1, "high": 5, "medium": 10, ...}',
    )

    top_patterns: Mapped[List[dict]] = mapped_column(
        JSONB,
        nullable=False,
        server_default="[]",
        comment="Most common patterns identified",
    )

    top_files: Mapped[List[dict]] = mapped_column(
        JSONB,
        nullable=False,
        server_default="[]",
        comment="Files with most learnings",
    )

    # Generated Updates
    claude_md_suggestions: Mapped[Optional[List[dict]]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Suggested additions to CLAUDE.md",
    )

    decomposition_hints: Mapped[Optional[List[dict]]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Generated decomposition hints",
    )

    adr_recommendations: Mapped[Optional[List[dict]]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Recommended ADR updates or creations",
    )

    # Processing
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default="pending",
        comment="Status: pending, processed, applied, rejected",
    )

    processed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When aggregation was processed",
    )

    applied_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When suggestions were applied",
    )

    rejection_reason: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Reason for rejection (if applicable)",
    )

    # AI Processing
    ai_model: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="AI model used for synthesis",
    )

    ai_processing_time_ms: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Time taken for AI synthesis (ms)",
    )

    # Audit
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default="NOW()",
        comment="When aggregation was created",
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default="NOW()",
        onupdate=datetime.utcnow,
        comment="Last update timestamp",
    )

    # Relationships
    project: Mapped["Project"] = relationship(
        "Project",
        lazy="selectin",
    )

    processor: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[processed_by],
        lazy="selectin",
    )

    # Table Arguments
    __table_args__ = (
        Index(
            "idx_learning_aggregations_project_period",
            "project_id",
            "period_type",
            "period_start",
        ),
        UniqueConstraint(
            "project_id",
            "period_type",
            "period_start",
            name="learning_aggregations_unique_period",
        ),
        CheckConstraint(
            f"period_type IN {tuple(PERIOD_TYPES)}",
            name="learning_aggregations_period_type_check",
        ),
        CheckConstraint(
            f"status IN {tuple(AGGREGATION_STATUS)}",
            name="learning_aggregations_status_check",
        ),
        {"comment": "Monthly/quarterly aggregations of PR learnings (EP-11)"},
    )

    def __repr__(self) -> str:
        return (
            f"LearningAggregation(id={self.id}, project_id={self.project_id}, "
            f"period={self.period_type}, start={self.period_start})"
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "project_id": str(self.project_id),
            "period_type": self.period_type,
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "total_learnings": self.total_learnings,
            "by_feedback_type": self.by_feedback_type,
            "by_severity": self.by_severity,
            "top_patterns": self.top_patterns,
            "top_files": self.top_files,
            "claude_md_suggestions": self.claude_md_suggestions,
            "decomposition_hints": self.decomposition_hints,
            "adr_recommendations": self.adr_recommendations,
            "status": self.status,
            "processed_at": (
                self.processed_at.isoformat() if self.processed_at else None
            ),
            "applied_at": self.applied_at.isoformat() if self.applied_at else None,
            "rejection_reason": self.rejection_reason,
            "processed_by": str(self.processed_by) if self.processed_by else None,
            "ai_model": self.ai_model,
            "ai_processing_time_ms": self.ai_processing_time_ms,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def to_summary_dict(self) -> dict[str, Any]:
        """Convert to summary dictionary for list views."""
        return {
            "id": str(self.id),
            "project_id": str(self.project_id),
            "period_type": self.period_type,
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "total_learnings": self.total_learnings,
            "status": self.status,
            "has_suggestions": bool(
                self.claude_md_suggestions or self.decomposition_hints
            ),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @property
    def is_pending(self) -> bool:
        """Check if aggregation is pending processing."""
        return self.status == "pending"

    @property
    def is_applied(self) -> bool:
        """Check if aggregation suggestions have been applied."""
        return self.status == "applied"

    @property
    def has_suggestions(self) -> bool:
        """Check if aggregation has generated suggestions."""
        return bool(
            self.claude_md_suggestions
            or self.decomposition_hints
            or self.adr_recommendations
        )

    @property
    def suggestion_count(self) -> int:
        """Count total number of suggestions."""
        count = 0
        if self.claude_md_suggestions:
            count += len(self.claude_md_suggestions)
        if self.decomposition_hints:
            count += len(self.decomposition_hints)
        if self.adr_recommendations:
            count += len(self.adr_recommendations)
        return count
