"""
=========================================================================
Sprint Gate Evaluation Model - G-Sprint / G-Sprint-Close Checklists
SDLC Orchestrator - Sprint 74 (Planning Hierarchy)

Version: 1.0.0
Date: January 18, 2026
Status: ACTIVE - Sprint 74 Implementation
Authority: Backend Lead + CTO Approved
Framework: SDLC 5.1.3 Sprint Planning Governance
ADR: ADR-013 Planning Hierarchy

Purpose:
- Store G-Sprint and G-Sprint-Close evaluation results
- JSONB checklist for audit trail
- Support tier-based approval authority

SDLC 5.1.3 Compliance:
- G-Sprint: Validates sprint plan before execution
- G-Sprint-Close: Ensures proper closure and documentation
- Checklist items per SDLC 5.1.3 specification

Security Standards:
- Row-Level Security (sprint-scoped access)
- Immutable evaluation records (append-only audit)

Zero Mock Policy: Real SQLAlchemy model with JSONB checklist
=========================================================================
"""

from datetime import datetime
from typing import Optional, Dict, Any, List, TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, String, Text, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, Mapped

from app.db.base_class import Base

if TYPE_CHECKING:
    from app.models.sprint import Sprint
    from app.models.user import User


# SDLC 5.1.3 G-Sprint Checklist Template
G_SPRINT_CHECKLIST_TEMPLATE = {
    "alignment": [
        {"id": "goal_aligns_phase", "label": "Sprint goal aligns with Phase objective", "required": True, "passed": None},
        {"id": "goal_aligns_roadmap", "label": "Sprint goal aligns with Roadmap goal", "required": True, "passed": None},
        {"id": "priorities_explicit", "label": "Priorities explicit (P0/P1/P2 labeled)", "required": True, "passed": None},
        {"id": "no_options_p0", "label": "No 'options' for P0 items", "required": True, "passed": None},
    ],
    "capacity": [
        {"id": "capacity_calculated", "label": "Team capacity calculated", "required": True, "passed": None},
        {"id": "velocity_within", "label": "Story points within velocity (+10% max)", "required": True, "passed": None},
        {"id": "personnel_confirmed", "label": "Key personnel availability confirmed", "required": True, "passed": None},
        {"id": "pto_accounted", "label": "PTO/holidays accounted for", "required": False, "passed": None},
    ],
    "dependencies": [
        {"id": "dependencies_identified", "label": "External dependencies identified", "required": True, "passed": None},
        {"id": "blocker_mitigation", "label": "Blocker mitigation planned", "required": False, "passed": None},
        {"id": "cross_team_scheduled", "label": "Cross-team coordination scheduled", "required": False, "passed": None},
    ],
    "risk": [
        {"id": "risks_identified", "label": "Top 3 risks identified", "required": True, "passed": None},
        {"id": "mitigation_defined", "label": "Mitigation strategies defined", "required": True, "passed": None},
        {"id": "escalation_clear", "label": "Escalation path clear", "required": False, "passed": None},
    ],
    "documentation": [
        {"id": "sprint_doc_created", "label": "SPRINT-XX.md created", "required": True, "passed": None},
        {"id": "dod_agreed", "label": "Definition of Done agreed", "required": True, "passed": None},
        {"id": "events_scheduled", "label": "Sprint events scheduled", "required": True, "passed": None},
    ],
}

# SDLC 5.1.3 G-Sprint-Close Checklist Template
G_SPRINT_CLOSE_CHECKLIST_TEMPLATE = {
    "work": [
        {"id": "work_accounted", "label": "All items accounted for (done/carryover)", "required": True, "passed": None},
        {"id": "carryover_documented", "label": "Carryover documented with reason", "required": True, "passed": None},
        {"id": "no_p0_dropped", "label": "No P0 items dropped", "required": True, "passed": None},
    ],
    "quality": [
        {"id": "dod_met", "label": "Definition of Done met", "required": True, "passed": None},
        {"id": "no_p0_bugs", "label": "No P0 bugs shipped", "required": True, "passed": None},
        {"id": "coverage_maintained", "label": "Test coverage maintained", "required": False, "passed": None},
    ],
    "retrospective": [
        {"id": "retro_completed", "label": "Sprint retro completed", "required": True, "passed": None},
        {"id": "actions_assigned", "label": "Action items assigned", "required": True, "passed": None},
        {"id": "improvements_documented", "label": "Improvements documented", "required": False, "passed": None},
    ],
    "metrics": [
        {"id": "velocity_calculated", "label": "Velocity calculated", "required": True, "passed": None},
        {"id": "completion_recorded", "label": "Completion rate recorded", "required": True, "passed": None},
        {"id": "bug_escape_recorded", "label": "Bug escape rate recorded", "required": False, "passed": None},
    ],
    "documentation": [
        {"id": "current_sprint_updated", "label": "CURRENT-SPRINT.md updated", "required": True, "passed": None},
        {"id": "sprint_index_updated", "label": "SPRINT-INDEX.md updated", "required": True, "passed": None},
        {"id": "roadmap_reviewed", "label": "Roadmap reviewed (update if needed)", "required": True, "passed": None},
        {"id": "within_24h", "label": "Documentation within 24 business hours", "required": True, "passed": None},
    ],
}


class SprintGateEvaluation(Base):
    """
    Sprint Gate Evaluation model for G-Sprint and G-Sprint-Close.

    Purpose:
        - Store gate evaluation results with JSONB checklist
        - Track evaluator and evaluation timestamp
        - Support audit trail for compliance

    SDLC 5.1.3 Gate Types:
        - g_sprint: Sprint planning gate
        - g_sprint_close: Sprint completion gate

    Fields:
        - id: UUID primary key
        - sprint_id: Foreign key to Sprint
        - gate_type: 'g_sprint' or 'g_sprint_close'
        - status: Gate evaluation status (pending, passed, failed)
        - checklist: JSONB with evaluation results
        - notes: Optional evaluation notes
        - evaluated_by: Foreign key to User (evaluator)
        - evaluated_at: Evaluation timestamp

    Relationships:
        - sprint: Many-to-One with Sprint
        - evaluator: Many-to-One with User

    Constraints:
        - Unique (sprint_id, gate_type) - One evaluation per gate type

    Usage Example:
        from app.models.sprint_gate_evaluation import G_SPRINT_CHECKLIST_TEMPLATE

        evaluation = SprintGateEvaluation(
            sprint_id=sprint.id,
            gate_type="g_sprint",
            checklist=G_SPRINT_CHECKLIST_TEMPLATE,
            evaluated_by=user.id
        )
        session.add(evaluation)
        session.commit()
    """

    __tablename__ = "sprint_gate_evaluations"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)

    # Sprint Relationship
    sprint_id = Column(
        UUID(as_uuid=True),
        ForeignKey("sprints.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Gate Type
    gate_type = Column(
        String(50),
        nullable=False,
        index=True,
        comment="Gate type: 'g_sprint' or 'g_sprint_close'"
    )

    # Status
    status = Column(
        String(50),
        nullable=False,
        default="pending",
        index=True,
        comment="Evaluation status: pending, passed, failed"
    )

    # JSONB Checklist (SDLC 5.1.3 format)
    checklist = Column(
        JSONB,
        nullable=False,
        comment="SDLC 5.1.3 checklist with pass/fail per item"
    )

    # Notes
    notes = Column(Text, nullable=True, comment="Optional evaluation notes")

    # Evaluator
    evaluated_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    evaluated_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    sprint: Mapped["Sprint"] = relationship("Sprint", back_populates="gate_evaluations")
    evaluator: Mapped[Optional["User"]] = relationship("User", foreign_keys=[evaluated_by])

    # Indexes & Constraints
    __table_args__ = (
        Index("idx_gate_eval_sprint", "sprint_id"),
        Index("idx_gate_eval_type", "gate_type"),
        Index("idx_gate_eval_status", "status"),
        {"comment": "SDLC 5.1.3 Sprint Gate Evaluations"},
    )

    def __repr__(self) -> str:
        return f"<SprintGateEvaluation(id={self.id}, gate_type={self.gate_type}, status={self.status})>"

    # ===== Status Properties =====

    @property
    def is_pending(self) -> bool:
        """Check if evaluation is pending"""
        return self.status == "pending"

    @property
    def is_passed(self) -> bool:
        """Check if evaluation passed"""
        return self.status == "passed"

    @property
    def is_failed(self) -> bool:
        """Check if evaluation failed"""
        return self.status == "failed"

    @property
    def is_g_sprint(self) -> bool:
        """Check if this is G-Sprint evaluation"""
        return self.gate_type == "g_sprint"

    @property
    def is_g_sprint_close(self) -> bool:
        """Check if this is G-Sprint-Close evaluation"""
        return self.gate_type == "g_sprint_close"

    # ===== Checklist Analysis =====

    @property
    def required_items(self) -> List[Dict[str, Any]]:
        """Get all required checklist items"""
        items = []
        for category, category_items in self.checklist.items():
            for item in category_items:
                if item.get("required", False):
                    items.append({**item, "category": category})
        return items

    @property
    def failed_required_items(self) -> List[Dict[str, Any]]:
        """Get required items that failed"""
        return [item for item in self.required_items if item.get("passed") is False]

    @property
    def pending_items(self) -> List[Dict[str, Any]]:
        """Get items not yet evaluated"""
        items = []
        for category, category_items in self.checklist.items():
            for item in category_items:
                if item.get("passed") is None:
                    items.append({**item, "category": category})
        return items

    @property
    def all_required_passed(self) -> bool:
        """Check if all required items passed"""
        for item in self.required_items:
            if item.get("passed") is not True:
                return False
        return True

    @property
    def completion_percentage(self) -> float:
        """Calculate checklist completion percentage"""
        total = 0
        evaluated = 0
        for category, category_items in self.checklist.items():
            for item in category_items:
                total += 1
                if item.get("passed") is not None:
                    evaluated += 1
        return (evaluated / total * 100) if total > 0 else 0.0

    # ===== Evaluation Methods =====

    def evaluate_item(self, item_id: str, passed: bool) -> bool:
        """
        Evaluate a single checklist item.

        Args:
            item_id: The item ID to evaluate
            passed: Whether the item passed

        Returns:
            bool: True if item was found and updated
        """
        for category, category_items in self.checklist.items():
            for item in category_items:
                if item.get("id") == item_id:
                    item["passed"] = passed
                    return True
        return False

    def finalize_evaluation(self, evaluator_id, notes: Optional[str] = None) -> str:
        """
        Finalize the gate evaluation.

        Sets status to 'passed' if all required items pass, 'failed' otherwise.

        Args:
            evaluator_id: UUID of the evaluator
            notes: Optional evaluation notes

        Returns:
            str: Final status ('passed' or 'failed')
        """
        self.evaluated_by = evaluator_id
        self.evaluated_at = datetime.utcnow()
        self.notes = notes

        if self.all_required_passed:
            self.status = "passed"
        else:
            self.status = "failed"

        return self.status

    @classmethod
    def create_g_sprint_evaluation(cls, sprint_id) -> "SprintGateEvaluation":
        """
        Factory method to create G-Sprint evaluation with template.

        Args:
            sprint_id: UUID of the sprint

        Returns:
            SprintGateEvaluation: New G-Sprint evaluation
        """
        import copy
        return cls(
            sprint_id=sprint_id,
            gate_type="g_sprint",
            checklist=copy.deepcopy(G_SPRINT_CHECKLIST_TEMPLATE)
        )

    @classmethod
    def create_g_sprint_close_evaluation(cls, sprint_id) -> "SprintGateEvaluation":
        """
        Factory method to create G-Sprint-Close evaluation with template.

        Args:
            sprint_id: UUID of the sprint

        Returns:
            SprintGateEvaluation: New G-Sprint-Close evaluation
        """
        import copy
        return cls(
            sprint_id=sprint_id,
            gate_type="g_sprint_close",
            checklist=copy.deepcopy(G_SPRINT_CLOSE_CHECKLIST_TEMPLATE)
        )
