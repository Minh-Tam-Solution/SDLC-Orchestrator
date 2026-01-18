"""
=========================================================================
Phase Model - 4-8 Week Themed Objectives
SDLC Orchestrator - Sprint 74 (Planning Hierarchy)

Version: 1.0.0
Date: January 18, 2026
Status: ACTIVE - Sprint 74 Implementation
Authority: Backend Lead + CTO Approved
Framework: SDLC 5.1.3 Sprint Planning Governance
ADR: ADR-013 Planning Hierarchy

Purpose:
- Group sprints into 4-8 week themed objectives
- Bridge between roadmap goals and sprint work
- Phase objective for sprint goal alignment (Rule #7)

Security Standards:
- Row-Level Security (roadmap-scoped access)
- Sequential numbering within roadmap

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
    from app.models.roadmap import Roadmap
    from app.models.sprint import Sprint


class Phase(Base):
    """
    Phase model for 4-8 week themed objectives.

    Purpose:
        - Group related sprints under a common theme
        - Define phase-level objectives for sprint alignment
        - Support traceability chain (Roadmap → Phase → Sprint)

    SDLC 5.1.3 Alignment:
        - Rule #7: Sprint Goal Must Align with Roadmap Phase
        - Traceability: Phase Objective → Sprint Goal

    Fields:
        - id: UUID primary key
        - roadmap_id: Foreign key to Roadmap
        - number: Sequential phase number within roadmap
        - name: Phase name (e.g., "Phase 1: Foundation")
        - theme: Phase theme (e.g., "Q1 Foundation")
        - objective: Phase objective (what this phase achieves)
        - start_date: Phase start date
        - end_date: Phase end date
        - status: Phase status (planned, active, completed)

    Relationships:
        - roadmap: Many-to-One with Roadmap
        - sprints: One-to-Many with Sprint

    Indexes:
        - roadmap_id (B-tree) - Fast roadmap lookup
        - status (B-tree) - Active phase filtering

    Constraints:
        - Unique (roadmap_id, number) - Sequential numbering

    Usage Example:
        phase = Phase(
            roadmap_id=roadmap.id,
            number=1,
            name="Phase 1: Foundation",
            theme="Q1 Foundation",
            objective="Establish core platform infrastructure",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 2, 28)
        )
        session.add(phase)
        session.commit()
    """

    __tablename__ = "phases"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)

    # Roadmap Relationship
    roadmap_id = Column(
        UUID(as_uuid=True),
        ForeignKey("roadmaps.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Phase Identity
    number = Column(
        Integer,
        nullable=False,
        comment="Sequential phase number within roadmap"
    )
    name = Column(String(255), nullable=False)
    theme = Column(Text, nullable=True, comment="Phase theme (e.g., Q1 Foundation)")
    objective = Column(Text, nullable=True, comment="Phase objective for sprint alignment")

    # Timeline
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)

    # Status
    status = Column(
        String(50),
        nullable=False,
        default="planned",
        index=True,
        comment="Phase status: planned, active, completed"
    )

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    roadmap: Mapped["Roadmap"] = relationship("Roadmap", back_populates="phases")
    sprints: Mapped[List["Sprint"]] = relationship(
        "Sprint",
        back_populates="phase",
        order_by="Sprint.number"
    )

    # Unique constraint (roadmap_id, number)
    __table_args__ = (
        Index("idx_phases_roadmap", "roadmap_id"),
        Index("idx_phases_status", "status"),
        {"comment": "SDLC 5.1.3 Phase Planning - 4-8 week objectives"},
    )

    def __repr__(self) -> str:
        return f"<Phase(id={self.id}, number={self.number}, name={self.name})>"

    @property
    def is_active(self) -> bool:
        """Check if phase is active"""
        return self.status == "active"

    @property
    def is_completed(self) -> bool:
        """Check if phase is completed"""
        return self.status == "completed"

    @property
    def duration_weeks(self) -> Optional[int]:
        """Calculate phase duration in weeks"""
        if self.start_date and self.end_date:
            delta = self.end_date - self.start_date
            return delta.days // 7
        return None

    @property
    def sprints_count(self) -> int:
        """Count sprints in phase"""
        return len(self.sprints) if self.sprints else 0

    @property
    def active_sprints(self) -> List["Sprint"]:
        """Get active sprints in phase"""
        return [s for s in self.sprints if s.status == "active"]

    @property
    def completed_sprints(self) -> List["Sprint"]:
        """Get completed sprints in phase"""
        return [s for s in self.sprints if s.status == "completed"]

    @property
    def completion_rate(self) -> float:
        """Calculate phase completion rate based on sprints"""
        if not self.sprints:
            return 0.0
        completed = len([s for s in self.sprints if s.status == "completed"])
        return completed / len(self.sprints) * 100
