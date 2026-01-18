"""
=========================================================================
Backlog Item Model - User Stories, Tasks, Bugs with Priorities
SDLC Orchestrator - Sprint 74 (Planning Hierarchy)

Version: 1.0.0
Date: January 18, 2026
Status: ACTIVE - Sprint 74 Implementation
Authority: Backend Lead + CTO Approved
Framework: SDLC 5.1.3 Sprint Planning Governance
ADR: ADR-013 Planning Hierarchy

Purpose:
- Track user stories, tasks, bugs, and spikes
- Support P0/P1/P2 priority classification (Rule #8)
- Enable backlog management and sprint planning
- Support subtask hierarchy (parent-child)

SDLC 5.1.3 Compliance:
- Rule #8: Strategic Priorities Explicit (P0/P1/P2)
- G-Sprint-Close: All items accounted for

Security Standards:
- Row-Level Security (project-scoped access)
- Audit trail (created_by, created_at, updated_at)

Zero Mock Policy: Real SQLAlchemy model with all fields
=========================================================================
"""

from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, Mapped

from app.db.base_class import Base

if TYPE_CHECKING:
    from app.models.sprint import Sprint
    from app.models.project import Project
    from app.models.user import User


class BacklogItem(Base):
    """
    Backlog Item model for user stories, tasks, bugs, and spikes.

    Purpose:
        - Manage product backlog and sprint backlog
        - Track item priority, status, and assignments
        - Support parent-child relationship for subtasks

    SDLC 5.1.3 Compliance:
        - Rule #8: Strategic Priorities Explicit (P0, P1, P2)
        - G-Sprint-Close: All items must be accounted for (done/carryover)

    Item Types:
        - story: User story (epic-level work)
        - task: Implementation task
        - bug: Bug fix
        - spike: Research/exploration

    Priority Levels (Rule #8):
        - P0: CORE / Must Have (cannot defer without CEO approval)
        - P1: Important / Should Have (can defer with CTO approval)
        - P2: Nice-to-Have / Could Have (can defer freely)

    Status Flow:
        todo → in_progress → review → done
        todo → blocked → in_progress (unblocked)

    Fields:
        - id: UUID primary key
        - sprint_id: Optional foreign key to Sprint (NULL = product backlog)
        - project_id: Foreign key to Project
        - type: Item type (story, task, bug, spike)
        - title: Item title
        - description: Detailed description
        - acceptance_criteria: Definition of done for this item
        - priority: P0, P1, P2 (Rule #8)
        - story_points: Effort estimation
        - status: Item status (todo, in_progress, review, done, blocked)
        - assignee_id: Assigned user
        - parent_id: Parent item (for subtasks)
        - labels: JSONB array of labels

    Relationships:
        - sprint: Many-to-One with Sprint (optional)
        - project: Many-to-One with Project
        - assignee: Many-to-One with User
        - creator: Many-to-One with User
        - parent: Self-referential for subtasks
        - children: Subtasks

    Usage Example:
        item = BacklogItem(
            project_id=project.id,
            sprint_id=sprint.id,
            type="story",
            title="Implement G-Sprint gate evaluation",
            description="Create API endpoint for G-Sprint checklist evaluation",
            priority="P0",
            story_points=5,
            assignee_id=developer.id
        )
        session.add(item)
        session.commit()
    """

    __tablename__ = "backlog_items"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)

    # Sprint & Project Relationship
    sprint_id = Column(
        UUID(as_uuid=True),
        ForeignKey("sprints.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Sprint assignment (NULL = product backlog)"
    )
    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Item Identity
    type = Column(
        String(50),
        nullable=False,
        index=True,
        comment="Item type: story, task, bug, spike"
    )
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    acceptance_criteria = Column(Text, nullable=True, comment="Definition of done")

    # Priority (SDLC 5.1.3 Rule #8)
    priority = Column(
        String(10),
        nullable=False,
        default="P2",
        index=True,
        comment="Priority: P0 (must), P1 (should), P2 (could)"
    )

    # Estimation
    story_points = Column(Integer, nullable=True, comment="Effort in story points")

    # Status
    status = Column(
        String(50),
        nullable=False,
        default="todo",
        index=True,
        comment="Status: todo, in_progress, review, done, blocked"
    )

    # Assignment
    assignee_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Hierarchy (subtasks)
    parent_id = Column(
        UUID(as_uuid=True),
        ForeignKey("backlog_items.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Parent item for subtasks"
    )

    # Labels
    labels = Column(
        JSONB,
        nullable=False,
        default=[],
        comment="Array of labels for categorization"
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
    sprint: Mapped[Optional["Sprint"]] = relationship("Sprint", back_populates="backlog_items")
    project: Mapped["Project"] = relationship("Project", backref="backlog_items")
    assignee: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[assignee_id], backref="assigned_items"
    )
    creator: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[created_by], backref="created_items"
    )
    parent: Mapped[Optional["BacklogItem"]] = relationship(
        "BacklogItem",
        remote_side=[id],
        backref="children",
        foreign_keys=[parent_id]
    )

    # Indexes
    __table_args__ = (
        Index("idx_backlog_sprint", "sprint_id"),
        Index("idx_backlog_project", "project_id"),
        Index("idx_backlog_status", "status"),
        Index("idx_backlog_assignee", "assignee_id"),
        Index("idx_backlog_priority", "priority"),
        Index("idx_backlog_type", "type"),
        Index("idx_backlog_parent", "parent_id"),
        {"comment": "SDLC 5.1.3 Backlog Items with P0/P1/P2 priorities"},
    )

    def __repr__(self) -> str:
        return f"<BacklogItem(id={self.id}, type={self.type}, title={self.title[:30]}...)>"

    # ===== Type Properties =====

    @property
    def is_story(self) -> bool:
        """Check if item is a user story"""
        return self.type == "story"

    @property
    def is_task(self) -> bool:
        """Check if item is a task"""
        return self.type == "task"

    @property
    def is_bug(self) -> bool:
        """Check if item is a bug"""
        return self.type == "bug"

    @property
    def is_spike(self) -> bool:
        """Check if item is a spike"""
        return self.type == "spike"

    # ===== Priority Properties (Rule #8) =====

    @property
    def is_p0(self) -> bool:
        """Check if item is P0 (must have)"""
        return self.priority == "P0"

    @property
    def is_p1(self) -> bool:
        """Check if item is P1 (should have)"""
        return self.priority == "P1"

    @property
    def is_p2(self) -> bool:
        """Check if item is P2 (could have)"""
        return self.priority == "P2"

    @property
    def is_critical(self) -> bool:
        """Check if item is critical (P0 or P1)"""
        return self.priority in ("P0", "P1")

    # ===== Status Properties =====

    @property
    def is_todo(self) -> bool:
        """Check if item is in todo status"""
        return self.status == "todo"

    @property
    def is_in_progress(self) -> bool:
        """Check if item is in progress"""
        return self.status == "in_progress"

    @property
    def is_review(self) -> bool:
        """Check if item is in review"""
        return self.status == "review"

    @property
    def is_done(self) -> bool:
        """Check if item is done"""
        return self.status == "done"

    @property
    def is_blocked(self) -> bool:
        """Check if item is blocked"""
        return self.status == "blocked"

    @property
    def is_in_sprint(self) -> bool:
        """Check if item is assigned to a sprint"""
        return self.sprint_id is not None

    @property
    def is_in_backlog(self) -> bool:
        """Check if item is in product backlog (no sprint)"""
        return self.sprint_id is None

    # ===== Hierarchy Properties =====

    @property
    def has_parent(self) -> bool:
        """Check if item has a parent (is subtask)"""
        return self.parent_id is not None

    @property
    def has_children(self) -> bool:
        """Check if item has subtasks"""
        return len(self.children) > 0 if self.children else False

    @property
    def children_count(self) -> int:
        """Count subtasks"""
        return len(self.children) if self.children else 0

    @property
    def completed_children_count(self) -> int:
        """Count completed subtasks"""
        if not self.children:
            return 0
        return len([c for c in self.children if c.status == "done"])

    @property
    def children_completion_rate(self) -> float:
        """Calculate subtask completion rate"""
        if not self.children:
            return 0.0
        done = len([c for c in self.children if c.status == "done"])
        return done / len(self.children) * 100

    # ===== Status Transitions =====

    def start(self) -> bool:
        """Move item to in_progress status"""
        if self.status in ("todo", "blocked"):
            self.status = "in_progress"
            return True
        return False

    def review(self) -> bool:
        """Move item to review status"""
        if self.status == "in_progress":
            self.status = "review"
            return True
        return False

    def complete(self) -> bool:
        """Move item to done status"""
        if self.status in ("in_progress", "review"):
            self.status = "done"
            return True
        return False

    def block(self) -> bool:
        """Move item to blocked status"""
        if self.status in ("todo", "in_progress"):
            self.status = "blocked"
            return True
        return False

    def unblock(self) -> bool:
        """Move item back to previous status (in_progress)"""
        if self.status == "blocked":
            self.status = "in_progress"
            return True
        return False

    def move_to_sprint(self, sprint_id) -> None:
        """Assign item to a sprint"""
        self.sprint_id = sprint_id

    def move_to_backlog(self) -> None:
        """Move item back to product backlog"""
        self.sprint_id = None
