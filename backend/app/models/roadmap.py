"""
=========================================================================
Roadmap Model - Strategic Planning (12-month vision)
SDLC Orchestrator - Sprint 74 (Planning Hierarchy)

Version: 1.0.0
Date: January 18, 2026
Status: ACTIVE - Sprint 74 Implementation
Authority: Backend Lead + CTO Approved
Framework: SDLC 5.1.3 Sprint Planning Governance
ADR: ADR-013 Planning Hierarchy

Purpose:
- Strategic 12-month planning with quarterly milestones
- Project vision and goals tracking
- Review cadence enforcement (Rule #10: Quarterly Re-Approval)
- Phase container for sprint grouping

Security Standards:
- Row-Level Security (project-scoped access)
- Audit trail (created_by, created_at, updated_at)

Zero Mock Policy: Real SQLAlchemy model with all fields
=========================================================================
"""

from datetime import datetime, date
from typing import Optional, List, TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import Column, Date, DateTime, ForeignKey, String, Text, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped

from app.db.base_class import Base

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.user import User
    from app.models.phase import Phase


class Roadmap(Base):
    """
    Roadmap model for strategic 12-month planning.

    Purpose:
        - Define project vision and long-term goals
        - Container for phases (4-8 week objectives)
        - Track review cadence per SDLC 5.1.3 Rule #10

    SDLC 5.1.3 Alignment:
        - Rule #10: Quarterly Roadmap Re-Approval
        - Rule #7: Sprint Goal Must Align with Roadmap Phase
        - Rule #5: Roadmap Changes Use Change Management

    Fields:
        - id: UUID primary key
        - project_id: Foreign key to Project
        - name: Roadmap name (e.g., "2026 Product Roadmap")
        - description: Detailed description
        - vision: Long-term vision statement
        - start_date: Roadmap start date
        - end_date: Roadmap end date (typically 12 months)
        - review_cadence: Review frequency (monthly, quarterly, yearly)
        - status: Roadmap status (draft, active, archived)
        - created_by: Foreign key to User (roadmap creator)

    Relationships:
        - project: Many-to-One with Project
        - creator: Many-to-One with User
        - phases: One-to-Many with Phase

    Indexes:
        - project_id (B-tree) - Fast project lookup
        - status (B-tree) - Active roadmap filtering

    Usage Example:
        roadmap = Roadmap(
            project_id=project.id,
            name="2026 Product Roadmap",
            vision="Build the #1 SDLC governance platform",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
            review_cadence="quarterly",
            created_by=user.id
        )
        session.add(roadmap)
        session.commit()
    """

    __tablename__ = "roadmaps"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)

    # Project Relationship
    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Roadmap Identity
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    vision = Column(Text, nullable=True, comment="Long-term vision statement")

    # Timeline
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)

    # Review Configuration (SDLC 5.1.3 Rule #10)
    review_cadence = Column(
        String(50),
        nullable=False,
        default="quarterly",
        comment="Review frequency: monthly, quarterly, yearly"
    )

    # Status
    status = Column(
        String(50),
        nullable=False,
        default="active",
        index=True,
        comment="Roadmap status: draft, active, archived"
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
    project: Mapped["Project"] = relationship("Project", backref="roadmaps")
    creator: Mapped[Optional["User"]] = relationship("User", foreign_keys=[created_by])
    phases: Mapped[List["Phase"]] = relationship(
        "Phase",
        back_populates="roadmap",
        cascade="all, delete-orphan",
        order_by="Phase.number"
    )

    # Unique constraint (project_id, name)
    __table_args__ = (
        Index("idx_roadmaps_project", "project_id"),
        Index("idx_roadmaps_status", "status"),
        {"comment": "SDLC 5.1.3 Strategic Planning - 12-month roadmaps"},
    )

    def __repr__(self) -> str:
        return f"<Roadmap(id={self.id}, name={self.name}, project_id={self.project_id})>"

    @property
    def is_active(self) -> bool:
        """Check if roadmap is active"""
        return self.status == "active"

    @property
    def duration_months(self) -> Optional[int]:
        """Calculate roadmap duration in months"""
        if self.start_date and self.end_date:
            delta = self.end_date - self.start_date
            return delta.days // 30
        return None

    @property
    def phases_count(self) -> int:
        """Count phases in roadmap"""
        return len(self.phases) if self.phases else 0

    @property
    def active_phases(self) -> List["Phase"]:
        """Get active phases"""
        return [p for p in self.phases if p.status == "active"]
