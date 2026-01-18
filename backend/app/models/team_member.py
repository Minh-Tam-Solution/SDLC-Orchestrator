"""
=========================================================================
TeamMember Model - User-Team Membership with SASE Roles
SDLC Orchestrator - Sprint 70 (Teams Foundation)

Version: 1.0.0
Date: January 20, 2026
Status: ACTIVE - Sprint 70 Implementation
Authority: Backend Lead + CTO Approved
Reference: ADR-028-Teams-Feature-Architecture
Reference: Teams-Data-Model-Specification.md

Purpose:
- Many-to-many relationship between users and teams
- Role-based access within teams (owner, admin, member, ai_agent)
- SASE member type tracking (human vs ai_agent)

SDLC 5.1.2 Alignment:
- CTO R1: ai_agent role for SE4A (Agent Executor)
- CTO R2: member_type column (human/ai_agent)
- SASE Constraint: AI agents cannot be owner/admin

Zero Mock Policy: Production-ready SQLAlchemy 2.0 model
=========================================================================
"""

from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import uuid4

from sqlalchemy import String, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from app.models.team import Team
    from app.models.user import User


class TeamMember(Base):
    """
    TeamMember model - junction table for User-Team many-to-many.

    Represents a user's membership in a team with specific role and type.
    Supports both human users (SE4H) and AI agents (SE4A) per SASE framework.

    SDLC 5.1.2 SASE Roles:
        - owner: SE4H with full VCR authority (create, delete team)
        - admin: SE4H for member/settings management
        - member: SE4H/SE4A for implementation work
        - ai_agent: SE4A (Agent Executor) for autonomous tasks

    SASE Constraint (CTO R1/R2):
        AI agents (member_type='ai_agent') cannot have owner/admin roles.
        This enforces human oversight for governance decisions.

    Fields:
        id: UUID primary key
        team_id: Parent team
        user_id: Member user (human or AI agent)
        role: Role in team (owner, admin, member, ai_agent)
        member_type: Type of member (human, ai_agent)
        joined_at: When the user joined the team
        created_at: Creation timestamp
        updated_at: Last update timestamp
        deleted_at: Soft delete timestamp (NULL = active)

    Relationships:
        team: Many-to-One with Team
        user: Many-to-One with User

    Indexes:
        - team_id - Fast team member lookup
        - user_id - Fast user team lookup
        - role - Role-based queries
        - member_type - Type-based queries
        - (team_id, user_id) unique - One membership per team

    Role Hierarchy:
        owner > admin > member >= ai_agent
        - owner: Full control (delete team, transfer ownership)
        - admin: Manage members, settings (cannot delete team)
        - member: Work on projects, submit evidence
        - ai_agent: Autonomous task execution (SE4A)
    """

    __tablename__ = "team_members"

    # Primary Key
    id: Mapped[uuid4] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        index=True,
        doc="Unique identifier for the membership"
    )

    # Foreign Keys
    team_id: Mapped[uuid4] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teams.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Parent team"
    )
    user_id: Mapped[uuid4] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Member user (human or AI agent)"
    )

    # Role & Type (CTO R1/R2)
    role: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="member",
        index=True,
        doc="Role in team: owner, admin, member, ai_agent"
    )
    member_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="human",
        index=True,
        doc="Type of member: human (SE4H), ai_agent (SE4A)"
    )

    # Timestamps
    joined_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=datetime.utcnow,
        doc="When the user joined the team"
    )

    # Relationships
    team: Mapped["Team"] = relationship(
        "Team",
        back_populates="members",
        doc="Parent team"
    )
    user: Mapped["User"] = relationship(
        "User",
        back_populates="team_memberships",
        doc="Member user"
    )

    # Table constraints (mirrors migration constraints)
    __table_args__ = (
        # Unique membership per team
        UniqueConstraint(
            "team_id", "user_id",
            name="team_members_unique"
        ),
        # Role constraint
        CheckConstraint(
            "role IN ('owner', 'admin', 'member', 'ai_agent')",
            name="team_members_role_check"
        ),
        # Member type constraint
        CheckConstraint(
            "member_type IN ('human', 'ai_agent')",
            name="team_members_member_type_check"
        ),
        # SASE Constraint: AI agents cannot be owners/admins
        CheckConstraint(
            "NOT (member_type = 'ai_agent' AND role IN ('owner', 'admin'))",
            name="team_members_ai_agent_role_check"
        ),
    )

    def __repr__(self) -> str:
        return f"<TeamMember(id={self.id}, team={self.team_id}, user={self.user_id}, role={self.role})>"

    # ==================== Properties ====================

    @property
    def is_owner(self) -> bool:
        """Check if member is team owner."""
        return self.role == "owner"

    @property
    def is_admin(self) -> bool:
        """Check if member is team admin."""
        return self.role == "admin"

    @property
    def is_admin_or_owner(self) -> bool:
        """Check if member is admin or owner."""
        return self.role in ("owner", "admin")

    @property
    def is_ai_agent(self) -> bool:
        """Check if member is an AI agent (SE4A)."""
        return self.member_type == "ai_agent"

    @property
    def is_human(self) -> bool:
        """Check if member is human (SE4H)."""
        return self.member_type == "human"

    @property
    def is_coach(self) -> bool:
        """Check if member is SE4H Coach (human owner/admin)."""
        return self.is_human and self.is_admin_or_owner

    @property
    def is_executor(self) -> bool:
        """Check if member is SE4A Executor (ai_agent role)."""
        return self.member_type == "ai_agent" and self.role == "ai_agent"

    @property
    def can_manage_members(self) -> bool:
        """Check if member can add/remove team members."""
        return self.is_admin_or_owner and self.is_human

    @property
    def can_approve_vcr(self) -> bool:
        """Check if member can approve VCR (Verification & Compliance Review)."""
        # Only human owners/admins can approve VCR per SASE
        return self.is_coach

    @property
    def can_modify_settings(self) -> bool:
        """Check if member can modify team settings."""
        return self.is_admin_or_owner and self.is_human

    @property
    def can_approve_sprint_gate(self) -> bool:
        """
        Check if member can approve Sprint Gates (G-Sprint/G-Sprint-Close).

        SDLC 5.1.3 Sprint Planning Governance:
        - Only human owners/admins (SE4H Coach) can approve sprint gates
        - AI agents cannot approve governance gates
        - This enforces human oversight for sprint governance

        Returns:
            True if member can approve sprint gates, False otherwise
        """
        return self.is_coach

    @property
    def can_create_sprint(self) -> bool:
        """
        Check if member can create new sprints.

        Any human member can create sprints, but only coaches can approve.
        """
        return self.is_human and self.deleted_at is None

    @property
    def can_manage_backlog(self) -> bool:
        """
        Check if member can manage backlog items (create, assign, prioritize).

        Any active team member (human or AI) can manage backlog.
        """
        return self.deleted_at is None

    # ==================== SASE Helper Methods ====================

    def can_perform_action(self, action: str) -> bool:
        """
        Check if member can perform a specific action.

        Args:
            action: Action to check (e.g., 'delete_team', 'add_member')

        Returns:
            True if member can perform action, False otherwise
        """
        # Define action permissions
        owner_only = {"delete_team", "transfer_ownership"}
        admin_actions = {
            "add_member", "remove_member", "modify_settings", "approve_vcr",
            "approve_g_sprint", "approve_g_sprint_close",  # Sprint 75: Sprint Gates
        }
        member_actions = {
            "submit_evidence", "view_projects", "comment",
            "create_sprint", "manage_backlog",  # Sprint 75: Planning
        }
        ai_agent_actions = {"execute_task", "generate_code", "run_tests"}

        if action in owner_only:
            return self.is_owner and self.is_human
        elif action in admin_actions:
            return self.is_coach
        elif action in member_actions:
            return self.deleted_at is None  # Any active member
        elif action in ai_agent_actions:
            return self.is_executor or (self.is_human and self.role == "member")
        else:
            return False

    def get_sase_role(self) -> str:
        """
        Get SASE framework role designation.

        Returns:
            'SE4H_Coach' for human owners/admins
            'SE4H_Member' for human members
            'SE4A_Executor' for AI agents
        """
        if self.is_ai_agent:
            return "SE4A_Executor"
        elif self.is_admin_or_owner:
            return "SE4H_Coach"
        else:
            return "SE4H_Member"
