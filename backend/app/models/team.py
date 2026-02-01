"""
=========================================================================
Team Model - Collaboration Unit
SDLC Orchestrator - Sprint 70 (Teams Foundation)

Version: 1.0.0
Date: January 20, 2026
Status: ACTIVE - Sprint 70 Implementation
Authority: Backend Lead + CTO Approved
Reference: ADR-028-Teams-Feature-Architecture
Reference: Teams-Data-Model-Specification.md

Purpose:
- Collaboration unit within an organization
- Groups users and projects for team governance
- Supports SASE workflow configuration

SDLC 5.1.3 Alignment (ADR-029):
- Teams coordinate SE4H (Agent Coach) and SE4A (Agent Executor)
- Settings store AGENTS.md configuration and SASE artifacts (CRP, MRP, VCR)
- Agentic maturity level (L0-L3) for team autonomy
- Note: BRS/MTS/LPS deprecated in favor of industry-standard AGENTS.md

Zero Mock Policy: Production-ready SQLAlchemy 2.0 model
=========================================================================
"""

from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import uuid4

from sqlalchemy import String, Text, ForeignKey, UniqueConstraint, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.team_member import TeamMember
    from app.models.project import Project


class Team(Base):
    """
    Team model - collaboration unit within an organization.

    Teams group users and projects together for collaboration and governance.
    Each team has owners, admins, and members (including AI agents per SASE).

    SDLC 5.1.2 Alignment:
        - owner = SE4H (Agent Coach) with VCR authority
        - admin = SE4H (Agent Coach) for member/settings management
        - member = SE4H/SE4A for implementation work
        - ai_agent = SE4A (Agent Executor) for autonomous tasks

    Fields:
        id: UUID primary key
        organization_id: Parent organization
        name: Display name (e.g., "Backend Team")
        slug: URL-safe identifier (unique per organization)
        description: Team description
        settings: Team-specific settings (JSONB)
        created_at: Creation timestamp
        updated_at: Last update timestamp
        deleted_at: Soft delete timestamp (NULL = active)

    Relationships:
        organization: Many-to-One with Organization
        members: One-to-Many with TeamMember (junction table)
        projects: One-to-Many with Project

    Indexes:
        - organization_id - Fast org team lookup
        - (organization_id, slug) unique - Slug unique per org
        - created_at - Recent teams

    Settings JSONB Schema:
        {
            "default_gate_approvers": ["uuid"],
            "notification_channel": "slack|email|webhook",
            "webhook_url": "string | null",
            "auto_assign_projects": "boolean (default: false)",
            "mentor_scripts": ["string"],
            "briefing_templates": ["string"],
            "agentic_maturity": "L0|L1|L2|L3",
            "crp_threshold": "number (0-1, default: 0.7)",
            "auto_approve_mrp": "boolean (default: false)"
        }
    """

    __tablename__ = "teams"

    # Primary Key
    id: Mapped[uuid4] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        index=True,
        doc="Unique identifier for the team"
    )

    # Foreign Key
    organization_id: Mapped[uuid4] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Parent organization"
    )

    # Core Fields
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Display name of the team (e.g., 'Backend Team')"
    )
    slug: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        doc="URL-safe identifier (unique per organization)"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Team description"
    )

    # Settings (JSONB for flexibility)
    settings: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        doc="Team-specific settings including SASE config"
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        index=True,
        doc="Record creation timestamp"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        doc="Last update timestamp"
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        index=True,
        doc="Soft delete timestamp (NULL = active)"
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization",
        back_populates="teams",
        doc="Parent organization"
    )
    members: Mapped[list["TeamMember"]] = relationship(
        "TeamMember",
        back_populates="team",
        cascade="all, delete-orphan",
        doc="Team membership records"
    )
    projects: Mapped[list["Project"]] = relationship(
        "Project",
        back_populates="team",
        doc="Projects belonging to this team"
    )
    invitations: Mapped[list["TeamInvitation"]] = relationship(
        "TeamInvitation",
        back_populates="team",
        cascade="all, delete-orphan",
        doc="Pending and historical team invitations"
    )

    # Table constraints
    __table_args__ = (
        UniqueConstraint(
            "organization_id", "slug",
            name="teams_org_slug_unique"
        ),
    )

    def __repr__(self) -> str:
        return f"<Team(id={self.id}, slug={self.slug}, org={self.organization_id})>"

    # ==================== Properties ====================

    @property
    def members_count(self) -> int:
        """Get count of members (excluding deleted)."""
        return sum(1 for m in self.members if m.deleted_at is None)

    @property
    def human_members_count(self) -> int:
        """Get count of human members (SE4H)."""
        return sum(
            1 for m in self.members
            if m.deleted_at is None and m.member_type == "human"
        )

    @property
    def ai_agents_count(self) -> int:
        """Get count of AI agent members (SE4A)."""
        return sum(
            1 for m in self.members
            if m.deleted_at is None and m.member_type == "ai_agent"
        )

    @property
    def projects_count(self) -> int:
        """Get count of projects (excluding deleted)."""
        return sum(1 for p in self.projects if p.deleted_at is None)

    @property
    def owners(self) -> list["TeamMember"]:
        """Get list of team owners."""
        return [m for m in self.members if m.role == "owner" and m.deleted_at is None]

    @property
    def admins(self) -> list["TeamMember"]:
        """Get list of team admins."""
        return [m for m in self.members if m.role == "admin" and m.deleted_at is None]

    @property
    def agentic_maturity(self) -> str:
        """Get SASE agentic maturity level (L0-L3)."""
        return self.settings.get("agentic_maturity", "L0")

    @property
    def crp_threshold(self) -> float:
        """Get CRP threshold (confidence below this triggers consultation)."""
        return self.settings.get("crp_threshold", 0.7)

    @property
    def auto_approve_mrp(self) -> bool:
        """Check if MRP auto-approval is enabled (no human VCR required)."""
        return self.settings.get("auto_approve_mrp", False)

    @property
    def agents_md_config(self) -> dict:
        """Get AGENTS.md configuration for this team.

        Note: Replaces deprecated MentorScript/BriefingScript per ADR-029.
        AGENTS.md is the industry-standard format for AI coding agents.
        """
        return self.settings.get("agents_md", {})

    @property
    def mentor_scripts(self) -> list[str]:
        """Get list of MentorScript references.

        DEPRECATED: Use agents_md_config instead per ADR-029.
        Retained for backwards compatibility with Sprint 78 pilot data.
        """
        return self.settings.get("mentor_scripts", [])

    @property
    def briefing_templates(self) -> list[str]:
        """Get list of BriefingScript template references.

        DEPRECATED: Use agents_md_config instead per ADR-029.
        Retained for backwards compatibility with Sprint 78 pilot data.
        """
        return self.settings.get("briefing_templates", [])

    # ==================== Query Methods ====================

    def get_member_by_user_id(self, user_id: uuid4) -> Optional["TeamMember"]:
        """Get membership record for a user."""
        for member in self.members:
            if member.user_id == user_id and member.deleted_at is None:
                return member
        return None

    def is_member(self, user_id: uuid4) -> bool:
        """Check if user is a team member."""
        return self.get_member_by_user_id(user_id) is not None

    def is_owner(self, user_id: uuid4) -> bool:
        """Check if user is a team owner."""
        member = self.get_member_by_user_id(user_id)
        return member is not None and member.role == "owner"

    def is_admin_or_owner(self, user_id: uuid4) -> bool:
        """Check if user is admin or owner."""
        member = self.get_member_by_user_id(user_id)
        return member is not None and member.role in ("owner", "admin")

    def can_approve_mrp(self, user_id: uuid4) -> bool:
        """Check if user can approve MRP (VCR authority)."""
        # Only human owners/admins can approve MRP (SE4H Coach role)
        member = self.get_member_by_user_id(user_id)
        if member is None:
            return False
        return (
            member.member_type == "human" and
            member.role in ("owner", "admin")
        )
