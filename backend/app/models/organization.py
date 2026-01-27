"""
=========================================================================
Organization Model - Multi-Tenant Root Entity
SDLC Orchestrator - Sprint 70 (Teams Foundation)

Version: 1.0.0
Date: January 20, 2026
Status: ACTIVE - Sprint 70 Implementation
Authority: Backend Lead + CTO Approved
Reference: ADR-028-Teams-Feature-Architecture
Reference: Teams-Data-Model-Specification.md

Purpose:
- Multi-tenant root entity for billing and compliance
- Contains teams and users
- Organization-wide settings and policy defaults

SDLC 5.1.3 Alignment (ADR-029):
- Organizations coordinate AI+Human teams
- Settings support AGENTS.md and SASE artifacts (CRP, MRP, VCR)
- Plan tiers map to SDLC 4-Tier Classification
- Note: BRS/MTS/LPS deprecated in favor of industry-standard AGENTS.md

Zero Mock Policy: Production-ready SQLAlchemy 2.0 model
=========================================================================
"""

from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import uuid4

from sqlalchemy import String, Text, CheckConstraint, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from app.models.team import Team
    from app.models.user import User


class UserOrganization(Base):
    """
    Join table for many-to-many relationship between users and organizations.

    Sprint 105: Enables GitHub-style multi-organization membership.
    A user can belong to multiple organizations with different roles in each.

    Fields:
        user_id: FK to users.id
        organization_id: FK to organizations.id
        role: User's role in this org (owner, admin, member)
        joined_at: When user joined this organization
    """

    __tablename__ = "user_organizations"

    user_id: Mapped[uuid4] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        doc="User ID"
    )
    organization_id: Mapped[uuid4] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        doc="Organization ID"
    )
    role: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="member",
        doc="User's role in this organization: owner, admin, member"
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        doc="When user joined this organization"
    )

    def __repr__(self) -> str:
        return f"<UserOrganization(user={self.user_id}, org={self.organization_id}, role={self.role})>"


class Organization(Base):
    """
    Organization model - multi-tenant root entity.

    Represents a company or organization that contains teams and users.
    All billing, compliance, and governance is scoped at the organization level.

    SDLC 5.1.2 Alignment:
        - Organization = Billing/Compliance unit
        - Teams = Collaboration units within org
        - Settings support SASE configuration

    Fields:
        id: UUID primary key
        name: Display name (e.g., "Acme Corporation")
        slug: URL-safe unique identifier (e.g., "acme-corp")
        plan: Subscription plan (free, starter, pro, enterprise)
        settings: Organization-wide settings (JSONB)
        created_at: Creation timestamp
        updated_at: Last update timestamp
        deleted_at: Soft delete timestamp (NULL = active)

    Relationships:
        teams: One-to-Many with Team model
        users: One-to-Many with User model

    Indexes:
        - slug (unique) - Fast org lookup by slug
        - plan - Plan-based queries
        - created_at - Recent orgs

    Settings JSONB Schema:
        {
            "default_policy_pack": "string | null",
            "require_mfa": "boolean (default: false)",
            "allowed_domains": ["string"] (email domains),
            "max_teams": "number (default: unlimited)",
            "max_projects_per_team": "number (default: unlimited)",
            "branding": {
                "logo_url": "string | null",
                "primary_color": "string (hex)"
            },
            "sase_config": {
                "agentic_maturity": "L0|L1|L2|L3",
                "mentor_scripts": ["string"],
                "briefing_templates": ["string"]
            }
        }
    """

    __tablename__ = "organizations"

    # Primary Key
    id: Mapped[uuid4] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        index=True,
        doc="Unique identifier for the organization"
    )

    # Core Fields
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Display name of the organization (e.g., 'Acme Corp')"
    )
    slug: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
        doc="URL-safe unique identifier (e.g., 'acme-corp')"
    )

    # Plan & Billing
    plan: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="free",
        index=True,
        doc="Subscription plan: free, starter, pro, enterprise"
    )

    # Settings (JSONB for flexibility)
    settings: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        doc="Organization-wide settings including SASE config"
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
    teams: Mapped[list["Team"]] = relationship(
        "Team",
        back_populates="organization",
        cascade="all, delete-orphan",
        doc="Teams belonging to this organization"
    )
    users: Mapped[list["User"]] = relationship(
        "User",
        back_populates="organization",
        doc="Users belonging to this organization"
    )

    # Table constraints
    __table_args__ = (
        CheckConstraint(
            "plan IN ('free', 'starter', 'pro', 'enterprise')",
            name="organizations_plan_check"
        ),
    )

    def __repr__(self) -> str:
        return f"<Organization(id={self.id}, slug={self.slug}, plan={self.plan})>"

    # ==================== Properties ====================

    @property
    def is_enterprise(self) -> bool:
        """Check if organization has enterprise plan."""
        return self.plan == "enterprise"

    @property
    def is_paid(self) -> bool:
        """Check if organization has a paid plan."""
        return self.plan in ("starter", "pro", "enterprise")

    @property
    def teams_count(self) -> int:
        """Get count of teams (excluding deleted)."""
        return sum(1 for t in self.teams if t.deleted_at is None)

    @property
    def users_count(self) -> int:
        """Get count of users (excluding deleted)."""
        return sum(1 for u in self.users if u.deleted_at is None)

    @property
    def require_mfa(self) -> bool:
        """Check if MFA is required for this organization."""
        return self.settings.get("require_mfa", False)

    @property
    def allowed_email_domains(self) -> list[str]:
        """Get list of allowed email domains for signup."""
        return self.settings.get("allowed_domains", [])

    @property
    def agentic_maturity(self) -> str:
        """Get SASE agentic maturity level (L0-L3)."""
        sase = self.settings.get("sase_config", {})
        return sase.get("agentic_maturity", "L0")

    # ==================== Validation Methods ====================

    def can_create_team(self) -> bool:
        """Check if organization can create more teams based on plan limits."""
        max_teams = self.settings.get("max_teams")
        if max_teams is None:
            return True  # Unlimited
        return self.teams_count < max_teams

    def is_email_allowed(self, email: str) -> bool:
        """Check if email domain is allowed for this organization."""
        domains = self.allowed_email_domains
        if not domains:
            return True  # No domain restrictions
        email_domain = email.split("@")[-1].lower()
        return email_domain in [d.lower() for d in domains]
