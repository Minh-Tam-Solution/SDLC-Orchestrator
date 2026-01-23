"""
=========================================================================
PR Learning Model - Feedback Loop Closure (EP-11)
SDLC Orchestrator - Sprint 100 (Feedback Learning Service)

Version: 1.0.0
Date: January 23, 2026
Status: ACTIVE - Sprint 100 Implementation
Authority: Backend Lead + CTO Approved
Framework: SDLC 5.1.3 SASE Integration
Reference: docs/02-design/14-Technical-Specs/Feedback-Learning-Service-Design.md

Purpose:
- Store learnings extracted from PR review comments
- Enable continuous improvement of AI code generation
- Track learning application to CLAUDE.md and decomposition

Workflow:
1. PR merged with review comments
2. System extracts learnings automatically (AI-powered)
3. Monthly: Aggregate learnings → Update decomposition hints
4. Quarterly: Update CLAUDE.md with new patterns

Feedback Types:
- pattern_violation: Deviation from established patterns
- missing_requirement: Overlooked acceptance criteria
- edge_case: Unhandled edge case discovered in review
- performance: Performance concern or optimization
- security_issue: Security vulnerability or concern
- test_coverage: Missing or inadequate tests
- documentation: Documentation gaps or improvements
- refactoring: Code structure improvements

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


# Feedback type constants
FEEDBACK_TYPES = [
    "pattern_violation",
    "missing_requirement",
    "edge_case",
    "performance",
    "security_issue",
    "test_coverage",
    "documentation",
    "refactoring",
    "other",
]

# Severity levels
SEVERITY_LEVELS = ["low", "medium", "high", "critical"]

# Learning status
LEARNING_STATUS = ["extracted", "reviewed", "applied", "archived"]


class PRLearning(Base):
    """
    PR Learning model for feedback loop closure.

    Purpose:
        - Store learnings extracted from PR review comments
        - Track learning application to CLAUDE.md and decomposition
        - Enable AI-powered pattern extraction

    Attributes:
        id: Unique identifier (UUID v4)
        project_id: Associated project
        pr_number: GitHub PR number
        feedback_type: Category of feedback
        severity: Impact level
        review_comment: Original review comment
        corrected_approach: How to do it correctly
        pattern_extracted: Reusable pattern for future
        status: Processing status

    Relationships:
        project: Associated project
        reviewer: User who provided feedback
    """

    __tablename__ = "pr_learnings"

    # Primary Key
    id: Mapped[uuid4] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        comment="Unique learning ID (UUID v4)",
    )

    # Foreign Keys
    project_id: Mapped[uuid4] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Associated project ID",
    )

    reviewer_id: Mapped[Optional[uuid4]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="User who provided feedback (if internal)",
    )

    # PR Reference
    pr_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="GitHub PR number",
    )

    pr_title: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="PR title for context",
    )

    pr_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Full URL to the PR",
    )

    pr_merged_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When PR was merged",
    )

    # Learning Classification
    feedback_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Category: pattern_violation, missing_requirement, etc.",
    )

    severity: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default="medium",
        comment="Impact level: low, medium, high, critical",
    )

    # Learning Content
    original_code: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Original problematic code snippet",
    )

    original_spec_section: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Related spec/requirement section",
    )

    review_comment: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Original review comment text",
    )

    corrected_approach: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Explanation of correct approach",
    )

    pattern_extracted: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Reusable pattern for future generations",
    )

    # Context
    file_path: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="File path where issue occurred",
    )

    line_start: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Starting line number",
    )

    line_end: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Ending line number",
    )

    related_adr: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Related ADR reference (e.g., ADR-002)",
    )

    # Reviewer Information
    reviewer_github_login: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="GitHub username of reviewer",
    )

    # Processing Status
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default="extracted",
        index=True,
        comment="Status: extracted, reviewed, applied, archived",
    )

    applied_to_claude_md: Mapped[bool] = mapped_column(
        Boolean,
        server_default="false",
        comment="Whether applied to CLAUDE.md",
    )

    applied_to_decomposition: Mapped[bool] = mapped_column(
        Boolean,
        server_default="false",
        comment="Whether applied to decomposition hints",
    )

    applied_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When learning was applied",
    )

    # AI Processing
    ai_extracted: Mapped[bool] = mapped_column(
        Boolean,
        server_default="true",
        comment="AI extracted vs manual entry",
    )

    ai_confidence: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="AI confidence score (0.0-1.0)",
    )

    ai_model: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="AI model used for extraction",
    )

    extraction_metadata: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Additional extraction metadata",
    )

    # Tagging
    tags: Mapped[Optional[List[str]]] = mapped_column(
        JSONB,
        nullable=True,
        server_default="[]",
        comment="Tags for filtering and grouping",
    )

    related_learnings: Mapped[Optional[List[str]]] = mapped_column(
        JSONB,
        nullable=True,
        server_default="[]",
        comment="IDs of related learnings",
    )

    # Audit
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default="NOW()",
        comment="When learning was created",
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

    reviewer: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[reviewer_id],
        lazy="selectin",
    )

    # Table Arguments
    __table_args__ = (
        Index("idx_pr_learnings_project_feedback", "project_id", "feedback_type"),
        Index("idx_pr_learnings_project_created", "project_id", "created_at"),
        Index(
            "idx_pr_learnings_status_applied",
            "status",
            "applied_to_claude_md",
            "applied_to_decomposition",
        ),
        Index("idx_pr_learnings_pr_number", "project_id", "pr_number"),
        CheckConstraint(
            f"feedback_type IN {tuple(FEEDBACK_TYPES)}",
            name="pr_learnings_feedback_type_check",
        ),
        CheckConstraint(
            f"severity IN {tuple(SEVERITY_LEVELS)}",
            name="pr_learnings_severity_check",
        ),
        CheckConstraint(
            f"status IN {tuple(LEARNING_STATUS)}",
            name="pr_learnings_status_check",
        ),
        {"comment": "PR review learnings for AI improvement (EP-11)"},
    )

    def __repr__(self) -> str:
        return (
            f"PRLearning(id={self.id}, project_id={self.project_id}, "
            f"pr_number={self.pr_number}, type={self.feedback_type})"
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "project_id": str(self.project_id),
            "pr_number": self.pr_number,
            "pr_title": self.pr_title,
            "pr_url": self.pr_url,
            "pr_merged_at": (
                self.pr_merged_at.isoformat() if self.pr_merged_at else None
            ),
            "feedback_type": self.feedback_type,
            "severity": self.severity,
            "original_code": self.original_code,
            "original_spec_section": self.original_spec_section,
            "review_comment": self.review_comment,
            "corrected_approach": self.corrected_approach,
            "pattern_extracted": self.pattern_extracted,
            "file_path": self.file_path,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "related_adr": self.related_adr,
            "reviewer_id": str(self.reviewer_id) if self.reviewer_id else None,
            "reviewer_github_login": self.reviewer_github_login,
            "status": self.status,
            "applied_to_claude_md": self.applied_to_claude_md,
            "applied_to_decomposition": self.applied_to_decomposition,
            "applied_at": self.applied_at.isoformat() if self.applied_at else None,
            "ai_extracted": self.ai_extracted,
            "ai_confidence": self.ai_confidence,
            "ai_model": self.ai_model,
            "tags": self.tags or [],
            "related_learnings": self.related_learnings or [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @property
    def is_applied(self) -> bool:
        """Check if learning has been applied anywhere."""
        return self.applied_to_claude_md or self.applied_to_decomposition

    @property
    def is_high_priority(self) -> bool:
        """Check if learning is high priority based on severity."""
        return self.severity in ("high", "critical")
