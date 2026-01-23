"""
=========================================================================
Decomposition Hint Model - AI Planning Improvement (EP-11)
SDLC Orchestrator - Sprint 100 (Feedback Learning Service)

Version: 1.0.0
Date: January 23, 2026
Status: ACTIVE - Sprint 100 Implementation
Authority: Backend Lead + CTO Approved
Framework: SDLC 5.1.3 SASE Integration
Reference: docs/02-design/14-Technical-Specs/Feedback-Learning-Service-Design.md

Purpose:
- Store extracted patterns from PR learnings
- Guide AI task decomposition to avoid common mistakes
- Track hint effectiveness for continuous improvement

Hint Types:
- pattern: Reusable code pattern to follow
- antipattern: Common mistake to avoid
- convention: Team/project naming/structure convention
- checklist: Items to verify before completion
- dependency: Hidden dependencies to consider

Workflow:
1. Extract hints from pr_learnings (monthly aggregation)
2. AI references hints during task decomposition
3. Hints improve quality of generated plans
4. Feedback loop closes when hint prevents future errors

Zero Mock Policy: Real SQLAlchemy model with all fields
=========================================================================
"""

from datetime import datetime
from typing import Optional, List, Any, TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    Index,
    CheckConstraint,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.db.base_class import Base

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.user import User
    from app.models.pr_learning import PRLearning
    from app.models.learning_aggregation import LearningAggregation


# Hint type constants
HINT_TYPES = ["pattern", "antipattern", "convention", "checklist", "dependency"]

# Hint categories
HINT_CATEGORIES = [
    "security",
    "testing",
    "architecture",
    "naming",
    "error_handling",
    "performance",
    "documentation",
    "accessibility",
    "api_design",
    "database",
    "frontend",
    "backend",
    "devops",
    "other",
]

# Hint status
HINT_STATUS = ["active", "deprecated", "merged", "archived"]


class DecompositionHint(Base):
    """
    Decomposition Hint model for AI planning improvement.

    Purpose:
        - Store extracted patterns from PR learnings
        - Guide AI task decomposition to avoid common mistakes
        - Track hint effectiveness for continuous improvement

    Attributes:
        id: Unique identifier (UUID v4)
        project_id: Associated project
        hint_type: Type of hint (pattern, antipattern, etc.)
        category: Domain category (security, testing, etc.)
        title: Short descriptive title
        description: Full description of the hint
        example_good: Example of correct implementation
        example_bad: Example of what to avoid
        confidence: AI confidence in hint accuracy

    Relationships:
        project: Associated project
        source_learning: Original PR learning that generated hint
    """

    __tablename__ = "decomposition_hints"

    # Primary Key
    id: Mapped[uuid4] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        comment="Unique hint ID (UUID v4)",
    )

    # Foreign Keys
    project_id: Mapped[uuid4] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Associated project ID",
    )

    source_learning_id: Mapped[Optional[uuid4]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("pr_learnings.id", ondelete="SET NULL"),
        nullable=True,
        comment="Original PR learning that generated hint",
    )

    aggregation_id: Mapped[Optional[uuid4]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("learning_aggregations.id", ondelete="SET NULL"),
        nullable=True,
        comment="Aggregation that created this hint",
    )

    merged_into_id: Mapped[Optional[uuid4]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("decomposition_hints.id", ondelete="SET NULL"),
        nullable=True,
        comment="Hint this was merged into (if deprecated)",
    )

    verified_by: Mapped[Optional[uuid4]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="User who verified the hint",
    )

    created_by: Mapped[Optional[uuid4]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="User who created (or approved) the hint",
    )

    # Hint Classification
    hint_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        index=True,
        comment="Type: pattern, antipattern, convention, checklist, dependency",
    )

    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Domain: security, testing, architecture, etc.",
    )

    subcategory: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="More specific category within domain",
    )

    # Hint Content
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Short descriptive title",
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Full description of the hint",
    )

    example_good: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Example of correct implementation",
    )

    example_bad: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Example of what to avoid",
    )

    rationale: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Why this hint matters",
    )

    # Applicability
    applies_to: Mapped[List[str]] = mapped_column(
        JSONB,
        nullable=False,
        server_default='["all"]',
        comment='Applies to: ["frontend", "backend", "api", "database", "all"]',
    )

    languages: Mapped[List[str]] = mapped_column(
        JSONB,
        nullable=False,
        server_default='["all"]',
        comment='Languages: ["python", "typescript", "all"]',
    )

    frameworks: Mapped[List[str]] = mapped_column(
        JSONB,
        nullable=False,
        server_default='["all"]',
        comment='Frameworks: ["react", "fastapi", "all"]',
    )

    # Quality Metrics
    confidence: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        server_default="0.8",
        comment="AI confidence in hint accuracy (0.0-1.0)",
    )

    usage_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default="0",
        comment="How many times used in decomposition",
    )

    effectiveness_score: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Computed: prevented_errors / usage_count",
    )

    prevented_errors: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default="0",
        comment="Number of errors prevented by this hint",
    )

    last_used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Last time hint was used",
    )

    # Status
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default="active",
        index=True,
        comment="Status: active, deprecated, merged, archived",
    )

    deprecated_reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Reason for deprecation (if applicable)",
    )

    # AI Processing
    ai_generated: Mapped[bool] = mapped_column(
        Boolean,
        server_default="true",
        comment="AI generated vs manual creation",
    )

    ai_model: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="AI model used for generation",
    )

    human_verified: Mapped[bool] = mapped_column(
        Boolean,
        server_default="false",
        comment="Whether verified by a human",
    )

    verified_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When hint was verified",
    )

    # Tagging
    tags: Mapped[Optional[List[str]]] = mapped_column(
        JSONB,
        nullable=True,
        server_default="[]",
        comment="Tags for filtering and grouping",
    )

    related_adrs: Mapped[Optional[List[str]]] = mapped_column(
        JSONB,
        nullable=True,
        server_default="[]",
        comment='Related ADR references: ["ADR-002", "ADR-007"]',
    )

    # Audit
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default="NOW()",
        comment="When hint was created",
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

    source_learning: Mapped[Optional["PRLearning"]] = relationship(
        "PRLearning",
        foreign_keys=[source_learning_id],
        lazy="selectin",
    )

    merged_into: Mapped[Optional["DecompositionHint"]] = relationship(
        "DecompositionHint",
        foreign_keys=[merged_into_id],
        remote_side="DecompositionHint.id",
        lazy="selectin",
    )

    verified_by_user: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[verified_by],
        lazy="selectin",
    )

    created_by_user: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[created_by],
        lazy="selectin",
    )

    # Table Arguments
    __table_args__ = (
        Index("idx_decomposition_hints_project_type", "project_id", "hint_type"),
        Index("idx_decomposition_hints_project_category", "project_id", "category"),
        Index(
            "idx_decomposition_hints_active",
            "project_id",
            "status",
            postgresql_where="status = 'active'",
        ),
        Index(
            "idx_decomposition_hints_effectiveness",
            "project_id",
            "effectiveness_score",
            postgresql_where="effectiveness_score IS NOT NULL",
        ),
        CheckConstraint(
            f"hint_type IN {tuple(HINT_TYPES)}",
            name="decomposition_hints_type_check",
        ),
        CheckConstraint(
            f"status IN {tuple(HINT_STATUS)}",
            name="decomposition_hints_status_check",
        ),
        CheckConstraint(
            "confidence >= 0 AND confidence <= 1",
            name="decomposition_hints_confidence_check",
        ),
        {"comment": "AI decomposition hints for planning improvement (EP-11)"},
    )

    def __repr__(self) -> str:
        return (
            f"DecompositionHint(id={self.id}, project_id={self.project_id}, "
            f"type={self.hint_type}, category={self.category})"
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "project_id": str(self.project_id),
            "hint_type": self.hint_type,
            "category": self.category,
            "subcategory": self.subcategory,
            "title": self.title,
            "description": self.description,
            "example_good": self.example_good,
            "example_bad": self.example_bad,
            "rationale": self.rationale,
            "applies_to": self.applies_to,
            "languages": self.languages,
            "frameworks": self.frameworks,
            "confidence": self.confidence,
            "usage_count": self.usage_count,
            "effectiveness_score": self.effectiveness_score,
            "prevented_errors": self.prevented_errors,
            "last_used_at": (
                self.last_used_at.isoformat() if self.last_used_at else None
            ),
            "status": self.status,
            "deprecated_reason": self.deprecated_reason,
            "ai_generated": self.ai_generated,
            "ai_model": self.ai_model,
            "human_verified": self.human_verified,
            "verified_at": self.verified_at.isoformat() if self.verified_at else None,
            "tags": self.tags or [],
            "related_adrs": self.related_adrs or [],
            "source_learning_id": (
                str(self.source_learning_id) if self.source_learning_id else None
            ),
            "merged_into_id": (
                str(self.merged_into_id) if self.merged_into_id else None
            ),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @property
    def is_active(self) -> bool:
        """Check if hint is active."""
        return self.status == "active"

    @property
    def is_effective(self) -> bool:
        """Check if hint has proven effective (>50% error prevention rate)."""
        if self.usage_count < 3:  # Need minimum sample
            return False
        return (
            self.effectiveness_score is not None and self.effectiveness_score > 0.5
        )

    def record_usage(self, prevented_error: bool = False) -> None:
        """Record hint usage and update effectiveness score."""
        self.usage_count += 1
        self.last_used_at = datetime.utcnow()

        if prevented_error:
            self.prevented_errors += 1

        # Update effectiveness score
        if self.usage_count > 0:
            self.effectiveness_score = self.prevented_errors / self.usage_count


class HintUsageLog(Base):
    """
    Hint Usage Log model for effectiveness tracking.

    Purpose:
        - Track when hints are used during task decomposition
        - Enable effectiveness scoring for hints
        - Provide feedback loop data

    Attributes:
        id: Unique identifier (UUID v4)
        hint_id: Associated hint
        project_id: Project where used
        outcome: Result of using the hint
        error_prevented: Whether hint prevented an error
    """

    __tablename__ = "hint_usage_logs"

    # Primary Key
    id: Mapped[uuid4] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        comment="Unique log ID (UUID v4)",
    )

    # Foreign Keys
    hint_id: Mapped[uuid4] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("decomposition_hints.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Associated hint ID",
    )

    project_id: Mapped[uuid4] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Project where hint was used",
    )

    used_by: Mapped[Optional[uuid4]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="User who triggered the decomposition",
    )

    # Context
    decomposition_session_id: Mapped[Optional[uuid4]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="Decomposition session ID (if tracked)",
    )

    task_description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Task being decomposed",
    )

    plan_generated: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Generated plan (or relevant excerpt)",
    )

    # Outcome
    outcome: Mapped[Optional[str]] = mapped_column(
        String(30),
        nullable=True,
        comment="Outcome: prevented_error, no_effect, false_positive",
    )

    pr_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Linked PR number (if applicable)",
    )

    error_prevented: Mapped[bool] = mapped_column(
        Boolean,
        server_default="false",
        comment="Whether hint prevented an error",
    )

    feedback: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Human feedback on hint usefulness",
    )

    # Audit
    used_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default="NOW()",
        comment="When hint was used",
    )

    # Relationships
    hint: Mapped["DecompositionHint"] = relationship(
        "DecompositionHint",
        lazy="selectin",
    )

    project: Mapped["Project"] = relationship(
        "Project",
        lazy="selectin",
    )

    user: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[used_by],
        lazy="selectin",
    )

    # Table Arguments
    __table_args__ = (
        Index("idx_hint_usage_logs_hint_outcome", "hint_id", "outcome"),
        {"comment": "Track hint usage for effectiveness scoring (EP-11)"},
    )

    def __repr__(self) -> str:
        return (
            f"HintUsageLog(id={self.id}, hint_id={self.hint_id}, "
            f"outcome={self.outcome}, prevented={self.error_prevented})"
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "hint_id": str(self.hint_id),
            "project_id": str(self.project_id),
            "used_by": str(self.used_by) if self.used_by else None,
            "decomposition_session_id": (
                str(self.decomposition_session_id)
                if self.decomposition_session_id
                else None
            ),
            "task_description": self.task_description,
            "outcome": self.outcome,
            "pr_id": self.pr_id,
            "error_prevented": self.error_prevented,
            "feedback": self.feedback,
            "used_at": self.used_at.isoformat() if self.used_at else None,
        }
