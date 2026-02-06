"""
Gate Decision Model - Sprint 161

Event log for gate approval decisions.

Uses event log pattern (NOT state machine) for simpler coupling.
Chain logic derived from (chain_id, step_index).

Key Insight (Enterprise Architect Review):
- Event log > state machine (simpler, less coupling)
- Chain logic: same chain_id = related decisions (e.g., council review)
- step_index: 0=first approver, 1=second approver, etc.
- NO gate finalization in Sprint 161 (defer to Sprint 164)

Example (Council Review):
    Gate G5 on ENTERPRISE project requires CTO + CEO + COMPLIANCE_OFFICER:

    Decision 1:
        chain_id: abc-123
        step_index: 0
        required_roles: ['CTO']
        status: PENDING

    Decision 2:
        chain_id: abc-123  # Same chain!
        step_index: 1
        required_roles: ['CEO']
        status: PENDING

    Decision 3:
        chain_id: abc-123  # Same chain!
        step_index: 2
        required_roles: ['COMPLIANCE_OFFICER']
        status: PENDING

Reference: ADR-052 Tier-Based Gate Approval Architecture
"""
from sqlalchemy import Column, String, Integer, Text, ForeignKey, TIMESTAMP, ARRAY, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.db.base_class import Base


class GateDecision(Base):
    """
    Event log for gate approval decisions.

    Attributes:
        id: Primary key (UUID)
        gate_id: Gate this decision is for
        project_id: Project containing the gate
        action: Decision action (REQUEST/APPROVE/REJECT/ESCALATE/COMMENT)
        actor_id: User who made this decision
        chain_id: Groups related decisions (council review)
        step_index: Sequential step in approval chain (0-based)
        required_roles: Roles required at this step
        status: Decision status (PENDING/COMPLETED/CANCELLED)
        comments: Decision comments
        evidence_ids: List of evidence UUIDs supporting decision
        created_at: When decision was created
        expires_at: When decision expires (for timeout/escalation) - CTO v2.5
        completed_at: When decision was completed

    Relationships:
        gate: Gate this decision is for
        project: Project containing the gate
        actor: User who made this decision

    Constraints:
        - step_index >= 0
        - Unique constraint: (gate_id, chain_id, step_index)

    Examples:
        >>> # Self-approval (FREE tier)
        >>> decision = GateDecision(
        ...     gate_id=gate_id,
        ...     project_id=project_id,
        ...     action='APPROVE',
        ...     actor_id=user_id,
        ...     chain_id=uuid4(),
        ...     step_index=0,
        ...     required_roles=[],
        ...     status='COMPLETED'
        ... )

        >>> # Council review (ENTERPRISE tier) - 3 decisions
        >>> chain_id = uuid4()
        >>> d1 = GateDecision(chain_id=chain_id, step_index=0, required_roles=['CTO'])
        >>> d2 = GateDecision(chain_id=chain_id, step_index=1, required_roles=['CEO'])
        >>> d3 = GateDecision(chain_id=chain_id, step_index=2, required_roles=['CO'])
    """

    __tablename__ = "gate_decisions"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign keys
    gate_id = Column(
        UUID(as_uuid=True),
        ForeignKey("gates.id", ondelete="CASCADE"),
        nullable=False
    )
    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False
    )

    # Decision metadata
    action = Column(String(20), nullable=False)
    # Values: 'REQUEST', 'APPROVE', 'REJECT', 'ESCALATE', 'COMMENT'
    actor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Chain tracking
    chain_id = Column(UUID(as_uuid=True), nullable=False)
    step_index = Column(Integer, nullable=False, default=0)
    required_roles = Column(ARRAY(String), nullable=False)

    # Status
    status = Column(String(20), default="PENDING")
    # Values: 'PENDING', 'COMPLETED', 'CANCELLED'

    # Evidence
    comments = Column(Text)
    evidence_ids = Column(ARRAY(UUID(as_uuid=True)))

    # Audit timestamps
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    expires_at = Column(TIMESTAMP)  # CTO v2.5 adjustment #2
    completed_at = Column(TIMESTAMP)

    # Relationships
    gate = relationship("Gate", back_populates="decisions")
    project = relationship("Project")
    actor = relationship("User")

    # Constraints
    __table_args__ = (
        CheckConstraint("step_index >= 0", name="gate_decisions_step_index_positive"),
    )

    def to_dict(self):
        """
        Serialize to dictionary.

        Returns:
            dict: JSON-serializable representation

        Example:
            >>> decision.to_dict()
            {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "gate_id": "789e4567-e89b-12d3-a456-426614174000",
                "project_id": "456e4567-e89b-12d3-a456-426614174000",
                "action": "REQUEST",
                "actor_id": "321e4567-e89b-12d3-a456-426614174000",
                "chain_id": "abc-123-def-456",
                "step_index": 0,
                "required_roles": ["PM"],
                "status": "PENDING",
                "comments": "Requesting approval for G1",
                "evidence_ids": ["ev1", "ev2"],
                "created_at": "2026-02-06T09:00:00",
                "expires_at": "2026-02-08T09:00:00",
                "completed_at": None
            }
        """
        return {
            "id": str(self.id),
            "gate_id": str(self.gate_id),
            "project_id": str(self.project_id),
            "action": self.action,
            "actor_id": str(self.actor_id),
            "chain_id": str(self.chain_id),
            "step_index": self.step_index,
            "required_roles": self.required_roles,
            "status": self.status,
            "comments": self.comments,
            "evidence_ids": [str(eid) for eid in self.evidence_ids] if self.evidence_ids else [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }

    def __repr__(self):
        """String representation for debugging."""
        return (
            f"<GateDecision("
            f"id={self.id}, "
            f"gate_id={self.gate_id}, "
            f"action={self.action}, "
            f"chain_id={self.chain_id}, "
            f"step_index={self.step_index}, "
            f"status={self.status}"
            f")>"
        )
