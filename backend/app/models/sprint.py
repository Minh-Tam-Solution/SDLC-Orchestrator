"""
=========================================================================
Sprint Model - 5-10 Day Delivery Cycles with Governance Gates
SDLC Orchestrator - Sprint 74 (Planning Hierarchy)

Version: 1.0.0
Date: January 18, 2026
Status: ACTIVE - Sprint 74 Implementation
Authority: Backend Lead + CTO Approved
Framework: SDLC 5.1.3 Sprint Planning Governance
ADR: ADR-013 Planning Hierarchy

Purpose:
- Track sprint planning and execution
- Enforce G-Sprint and G-Sprint-Close governance gates
- Support immutable sprint numbering (Rule #1)
- Enforce 24h documentation deadline (Rule #2)

SDLC 5.1.3 Compliance:
- Rule #1: Sprint Numbers Are Immutable
- Rule #2: Post-Sprint Documentation Within 24 Business Hours
- Rule #3: Sprint Planning Requires Approval
- Rule #8: Strategic Priorities Explicit
- Rule #9: Documentation Freeze = Sprint Freeze

Security Standards:
- Row-Level Security (project-scoped access)
- Audit trail for gate approvals

Zero Mock Policy: Real SQLAlchemy model with all fields
=========================================================================
"""

from datetime import datetime, date
from typing import Optional, List, TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String, Text, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped

from app.db.base_class import Base

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.phase import Phase
    from app.models.user import User
    from app.models.sprint_gate_evaluation import SprintGateEvaluation
    from app.models.backlog_item import BacklogItem


class Sprint(Base):
    """
    Sprint model for 5-10 day delivery cycles with SDLC 5.1.3 governance.

    Purpose:
        - Track sprint planning, execution, and closure
        - Enforce G-Sprint gate before sprint start
        - Enforce G-Sprint-Close gate for documentation
        - Support traceability (Sprint → Phase → Roadmap)

    SDLC 5.1.3 Governance Gates:
        - G-Sprint: Validates sprint plan before execution
        - G-Sprint-Close: Ensures proper closure and documentation

    Fields:
        - id: UUID primary key
        - phase_id: Optional foreign key to Phase
        - project_id: Foreign key to Project
        - number: Immutable sprint number (Rule #1)
        - name: Sprint name (e.g., "Sprint 74: Planning Hierarchy")
        - goal: Single sentence sprint goal (Rule #7)
        - status: Sprint status (planning, active, completed, cancelled)
        - start_date, end_date: Sprint timeline
        - capacity_points: Story points capacity
        - team_size, velocity_target: Team metrics
        - G-Sprint fields: Approval status, approver, timestamp
        - G-Sprint-Close fields: Closure status, approver, timestamp
        - documentation_deadline: 24h deadline for docs (Rule #2)

    Relationships:
        - project: Many-to-One with Project
        - phase: Many-to-One with Phase (optional)
        - creator: Many-to-One with User
        - gate_evaluations: One-to-Many with SprintGateEvaluation
        - backlog_items: One-to-Many with BacklogItem

    Constraints:
        - Unique (project_id, number) - Immutable sprint numbers

    Usage Example:
        sprint = Sprint(
            project_id=project.id,
            phase_id=phase.id,
            number=74,
            name="Sprint 74: Planning Hierarchy",
            goal="Implement complete Planning Hierarchy with governance gates",
            start_date=date(2026, 2, 3),
            end_date=date(2026, 2, 14),
            capacity_points=55
        )
        session.add(sprint)
        session.commit()
    """

    __tablename__ = "sprints"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)

    # Project & Phase Relationship
    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    phase_id = Column(
        UUID(as_uuid=True),
        ForeignKey("phases.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Optional phase (NULL for standalone sprints)"
    )

    # Sprint Identity (Rule #1: Immutable)
    number = Column(
        Integer,
        nullable=False,
        comment="Immutable sprint number (SDLC 5.1.3 Rule #1)"
    )
    name = Column(String(255), nullable=False)
    goal = Column(
        Text,
        nullable=False,
        comment="Single sentence sprint goal (SDLC 5.1.3 Rule #7)"
    )

    # Status
    status = Column(
        String(50),
        nullable=False,
        default="planning",
        index=True,
        comment="Sprint status: planning, active, completed, cancelled"
    )

    # Timeline
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)

    # Capacity & Velocity
    capacity_points = Column(Integer, nullable=True, comment="Story points capacity")
    team_size = Column(Integer, nullable=True)
    velocity_target = Column(Integer, nullable=True, comment="Target velocity")

    # ===== G-Sprint Gate (Sprint Planning) =====
    g_sprint_status = Column(
        String(50),
        nullable=False,
        default="pending",
        index=True,
        comment="G-Sprint gate status: pending, passed, failed"
    )
    g_sprint_approved_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    g_sprint_approved_at = Column(DateTime, nullable=True)

    # ===== G-Sprint-Close Gate (Sprint Completion) =====
    g_sprint_close_status = Column(
        String(50),
        nullable=False,
        default="pending",
        index=True,
        comment="G-Sprint-Close gate status: pending, passed, failed"
    )
    g_sprint_close_approved_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    g_sprint_close_approved_at = Column(DateTime, nullable=True)

    # Documentation Deadline (Rule #2: 24h business hours)
    documentation_deadline = Column(
        DateTime,
        nullable=True,
        comment="24 business hours deadline from end_date (SDLC 5.1.3 Rule #2)"
    )

    # Audit
    created_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    project: Mapped["Project"] = relationship("Project", backref="sprints")
    phase: Mapped[Optional["Phase"]] = relationship("Phase", back_populates="sprints")
    creator: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[created_by], backref="created_sprints"
    )
    g_sprint_approver: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[g_sprint_approved_by]
    )
    g_sprint_close_approver: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[g_sprint_close_approved_by]
    )
    gate_evaluations: Mapped[List["SprintGateEvaluation"]] = relationship(
        "SprintGateEvaluation",
        back_populates="sprint",
        cascade="all, delete-orphan"
    )
    backlog_items: Mapped[List["BacklogItem"]] = relationship(
        "BacklogItem",
        back_populates="sprint",
        order_by="BacklogItem.priority"
    )

    # Indexes & Constraints
    __table_args__ = (
        Index("idx_sprints_project", "project_id"),
        Index("idx_sprints_phase", "phase_id"),
        Index("idx_sprints_status", "status"),
        Index("idx_sprints_g_sprint_status", "g_sprint_status"),
        Index("idx_sprints_g_sprint_close_status", "g_sprint_close_status"),
        {"comment": "SDLC 5.1.3 Sprint with Governance Gates"},
    )

    def __repr__(self) -> str:
        return f"<Sprint(id={self.id}, number={self.number}, name={self.name})>"

    # ===== Status Properties =====

    @property
    def is_planning(self) -> bool:
        """Check if sprint is in planning status"""
        return self.status == "planning"

    @property
    def is_active(self) -> bool:
        """Check if sprint is active"""
        return self.status == "active"

    @property
    def is_completed(self) -> bool:
        """Check if sprint is completed"""
        return self.status == "completed"

    @property
    def is_cancelled(self) -> bool:
        """Check if sprint is cancelled (Rule #1: Keep number)"""
        return self.status == "cancelled"

    # ===== Gate Properties =====

    @property
    def can_start(self) -> bool:
        """Check if sprint can start (G-Sprint must pass)"""
        return self.g_sprint_status == "passed" and self.status == "planning"

    @property
    def can_close(self) -> bool:
        """Check if sprint can close (must be active)"""
        return self.status == "active"

    @property
    def g_sprint_passed(self) -> bool:
        """Check if G-Sprint gate passed"""
        return self.g_sprint_status == "passed"

    @property
    def g_sprint_close_passed(self) -> bool:
        """Check if G-Sprint-Close gate passed"""
        return self.g_sprint_close_status == "passed"

    @property
    def documentation_overdue(self) -> bool:
        """Check if documentation deadline is overdue (Rule #9)"""
        if not self.documentation_deadline:
            return False
        return datetime.utcnow() > self.documentation_deadline and self.g_sprint_close_status != "passed"

    # ===== Timeline Properties =====

    @property
    def duration_days(self) -> Optional[int]:
        """Calculate sprint duration in days"""
        if self.start_date and self.end_date:
            delta = self.end_date - self.start_date
            return delta.days + 1  # Include end date
        return None

    # ===== Backlog Properties =====

    @property
    def total_story_points(self) -> int:
        """Sum of story points for all backlog items"""
        if not self.backlog_items:
            return 0
        return sum(item.story_points or 0 for item in self.backlog_items)

    @property
    def completed_story_points(self) -> int:
        """Sum of story points for completed items"""
        if not self.backlog_items:
            return 0
        return sum(
            item.story_points or 0
            for item in self.backlog_items
            if item.status == "done"
        )

    @property
    def p0_items(self) -> List["BacklogItem"]:
        """Get P0 priority items"""
        return [item for item in self.backlog_items if item.priority == "P0"]

    @property
    def p1_items(self) -> List["BacklogItem"]:
        """Get P1 priority items"""
        return [item for item in self.backlog_items if item.priority == "P1"]

    @property
    def completion_rate(self) -> float:
        """Calculate sprint completion rate"""
        if not self.backlog_items:
            return 0.0
        done = len([item for item in self.backlog_items if item.status == "done"])
        return done / len(self.backlog_items) * 100

    # ===== Traceability =====

    @property
    def phase_objective(self) -> Optional[str]:
        """Get parent phase objective for traceability"""
        return self.phase.objective if self.phase else None

    @property
    def roadmap_goal(self) -> Optional[str]:
        """Get roadmap vision for traceability"""
        if self.phase and self.phase.roadmap:
            return self.phase.roadmap.vision
        return None
