"""
Project Function Role Model - Sprint 161

Functional role assignment for approval authority.

Separates access control (project_members.role: owner/admin/member/viewer)
from approval authority (functional_role: PM/CTO/CEO/QA_LEAD/COMPLIANCE_OFFICER).

Key Insight (Enterprise Architect Review):
- Access control ≠ Approval authority
- Same user can be "member" in Project A but assigned "PM" functional role
- Solves: "PM/CTO/CEO roles don't have data source per project"

Example:
    User Alice:
    - project_members: Project A → role='member' (access control)
    - project_function_roles: Project A → functional_role='PM' (approval authority)
    - Result: Alice can view/edit (member) AND approve gates (PM)

Reference: ADR-052 Tier-Based Gate Approval Architecture
"""
from sqlalchemy import Column, String, ForeignKey, TIMESTAMP, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.db.base_class import Base


class ProjectFunctionRole(Base):
    """
    Functional role assignment for approval authority.

    Attributes:
        id: Primary key (UUID)
        project_id: Project this role assignment belongs to
        user_id: User assigned the functional role
        functional_role: Functional role (PM/CTO/CEO/QA_LEAD/COMPLIANCE_OFFICER)
        assigned_at: Timestamp when role was assigned
        assigned_by: User who assigned this role (can be NULL for system-assigned)

    Relationships:
        project: Project this role belongs to
        user: User with this functional role
        assigner: User who assigned this role

    Constraints:
        - One user can have multiple functional roles per project
        - Unique constraint: (project_id, user_id, functional_role)

    Examples:
        >>> # Assign PM role to user in Project A
        >>> role = ProjectFunctionRole(
        ...     project_id=project_a_id,
        ...     user_id=alice_id,
        ...     functional_role='PM',
        ...     assigned_by=admin_id
        ... )

        >>> # User can have multiple roles
        >>> role2 = ProjectFunctionRole(
        ...     project_id=project_a_id,
        ...     user_id=alice_id,
        ...     functional_role='QA_LEAD',
        ...     assigned_by=admin_id
        ... )
    """

    __tablename__ = "project_function_roles"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign keys
    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    # Functional role (ENUM: PM, CTO, CEO, QA_LEAD, COMPLIANCE_OFFICER)
    functional_role = Column(String(50), nullable=False)

    # Audit
    assigned_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    assigned_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    # Relationships
    project = relationship("Project", back_populates="function_roles")
    user = relationship("User", foreign_keys=[user_id])
    assigner = relationship("User", foreign_keys=[assigned_by])

    # Constraints
    __table_args__ = (
        UniqueConstraint(
            "project_id",
            "user_id",
            "functional_role",
            name="uq_project_user_function"
        ),
    )

    def to_dict(self):
        """
        Serialize to dictionary.

        Returns:
            dict: JSON-serializable representation

        Example:
            >>> role.to_dict()
            {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "project_id": "789e4567-e89b-12d3-a456-426614174000",
                "user_id": "456e4567-e89b-12d3-a456-426614174000",
                "functional_role": "PM",
                "assigned_at": "2026-02-06T09:00:00",
                "assigned_by": "321e4567-e89b-12d3-a456-426614174000"
            }
        """
        return {
            "id": str(self.id),
            "project_id": str(self.project_id),
            "user_id": str(self.user_id),
            "functional_role": self.functional_role,
            "assigned_at": self.assigned_at.isoformat() if self.assigned_at else None,
            "assigned_by": str(self.assigned_by) if self.assigned_by else None,
        }

    def __repr__(self):
        """String representation for debugging."""
        return (
            f"<ProjectFunctionRole("
            f"id={self.id}, "
            f"project_id={self.project_id}, "
            f"user_id={self.user_id}, "
            f"functional_role={self.functional_role}"
            f")>"
        )
