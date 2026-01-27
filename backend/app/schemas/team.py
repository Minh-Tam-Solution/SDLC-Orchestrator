"""
=========================================================================
Team Schemas - Pydantic Models for API Validation
SDLC Orchestrator - Sprint 70 (Teams Foundation)

Version: 1.0.0
Date: January 20, 2026
Status: ACTIVE - Sprint 70 Implementation
Authority: Backend Lead + CTO Approved
Reference: ADR-028-Teams-Feature-Architecture
Reference: Teams-Data-Model-Specification.md

Purpose:
- API request/response validation for Organizations, Teams, TeamMembers
- SASE-compliant role validation (ai_agent cannot be owner/admin)
- Type-safe data transfer between API and business logic

SDLC 5.1.2 Alignment:
- RoleEnum with ai_agent role for SE4A
- MemberTypeEnum with human/ai_agent types
- Settings schemas for SASE artifacts

Zero Mock Policy: Production-ready Pydantic v2 models
=========================================================================
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


# =========================================================================
# Enums
# =========================================================================

class OrganizationPlan(str, Enum):
    """Organization subscription plan."""
    FREE = "free"
    STARTER = "starter"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class TeamRole(str, Enum):
    """Team member role per SASE framework."""
    OWNER = "owner"       # SE4H with full VCR authority
    ADMIN = "admin"       # SE4H for member/settings management
    MEMBER = "member"     # SE4H/SE4A for implementation work
    AI_AGENT = "ai_agent" # SE4A (Agent Executor) for autonomous tasks


class MemberType(str, Enum):
    """Member type per SASE framework (CTO R2)."""
    HUMAN = "human"       # SE4H (Agent Coach or Member)
    AI_AGENT = "ai_agent" # SE4A (Agent Executor)


class AgenticMaturity(str, Enum):
    """SASE agentic maturity level."""
    L0 = "L0"  # Manual only
    L1 = "L1"  # AI-assisted
    L2 = "L2"  # AI-delegated
    L3 = "L3"  # AI-autonomous


# =========================================================================
# Organization Schemas
# =========================================================================

class OrganizationSettings(BaseModel):
    """Organization-wide settings including SASE config."""
    default_policy_pack: Optional[str] = Field(
        None,
        description="Default policy pack for new projects"
    )
    require_mfa: bool = Field(
        False,
        description="Require MFA for all organization members"
    )
    allowed_domains: list[str] = Field(
        default_factory=list,
        description="Allowed email domains for signup"
    )
    max_teams: Optional[int] = Field(
        None,
        ge=1,
        description="Maximum number of teams (NULL = unlimited)"
    )
    max_projects_per_team: Optional[int] = Field(
        None,
        ge=1,
        description="Maximum projects per team (NULL = unlimited)"
    )
    sase_config: Optional[dict] = Field(
        default_factory=dict,
        description="SASE configuration (agentic_maturity, mentor_scripts, etc.)"
    )

    model_config = ConfigDict(from_attributes=True)


class OrganizationCreate(BaseModel):
    """Schema for creating a new organization."""
    name: str = Field(
        ...,
        min_length=2,
        max_length=255,
        description="Display name of the organization",
        examples=["Acme Corporation"]
    )
    slug: str = Field(
        ...,
        min_length=2,
        max_length=100,
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
        description="URL-safe unique identifier",
        examples=["acme-corp"]
    )
    plan: OrganizationPlan = Field(
        OrganizationPlan.FREE,
        description="Subscription plan"
    )
    settings: Optional[OrganizationSettings] = Field(
        default_factory=OrganizationSettings,
        description="Organization-wide settings"
    )

    model_config = ConfigDict(from_attributes=True)


class OrganizationUpdate(BaseModel):
    """Schema for updating an organization."""
    name: Optional[str] = Field(
        None,
        min_length=2,
        max_length=255,
        description="Display name of the organization"
    )
    slug: Optional[str] = Field(
        None,
        min_length=2,
        max_length=100,
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
        description="URL-safe unique identifier"
    )
    plan: Optional[OrganizationPlan] = Field(
        None,
        description="Subscription plan"
    )
    settings: Optional[OrganizationSettings] = Field(
        None,
        description="Organization-wide settings"
    )

    model_config = ConfigDict(from_attributes=True)


class OrganizationResponse(BaseModel):
    """Schema for organization response."""
    id: UUID = Field(..., description="Organization UUID")
    name: str = Field(..., description="Display name")
    slug: str = Field(..., description="URL-safe identifier")
    plan: OrganizationPlan = Field(..., description="Subscription plan")
    settings: dict = Field(default_factory=dict, description="Organization settings")
    teams_count: int = Field(0, description="Number of teams")
    users_count: int = Field(0, description="Number of users")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True)


class OrganizationListResponse(BaseModel):
    """Schema for paginated organization list."""
    items: list[OrganizationResponse] = Field(default_factory=list)
    total: int = Field(0, ge=0)
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
    has_next: bool = Field(False)

    model_config = ConfigDict(from_attributes=True)


# =========================================================================
# Team Schemas
# =========================================================================

class TeamSettings(BaseModel):
    """Team-specific settings including SASE config."""
    default_gate_approvers: list[UUID] = Field(
        default_factory=list,
        description="Default approvers for gate reviews"
    )
    notification_channel: Optional[str] = Field(
        None,
        pattern=r"^(slack|email|webhook)$",
        description="Notification channel type"
    )
    webhook_url: Optional[str] = Field(
        None,
        max_length=500,
        description="Webhook URL for notifications"
    )
    auto_assign_projects: bool = Field(
        False,
        description="Auto-assign new projects to team"
    )
    mentor_scripts: list[str] = Field(
        default_factory=list,
        description="MentorScript references"
    )
    briefing_templates: list[str] = Field(
        default_factory=list,
        description="BriefingScript template references"
    )
    agentic_maturity: AgenticMaturity = Field(
        AgenticMaturity.L0,
        description="SASE agentic maturity level"
    )
    crp_threshold: float = Field(
        0.7,
        ge=0.0,
        le=1.0,
        description="CRP threshold (confidence below triggers consultation)"
    )
    auto_approve_mrp: bool = Field(
        False,
        description="Auto-approve MRP (no human VCR required)"
    )

    model_config = ConfigDict(from_attributes=True)


class TeamCreate(BaseModel):
    """Schema for creating a new team."""
    organization_id: UUID = Field(..., description="Parent organization UUID")
    name: str = Field(
        ...,
        min_length=2,
        max_length=255,
        description="Display name of the team",
        examples=["Backend Team"]
    )
    slug: str = Field(
        ...,
        min_length=2,
        max_length=100,
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
        description="URL-safe identifier (unique per organization)",
        examples=["backend-team"]
    )
    description: Optional[str] = Field(
        None,
        max_length=1000,
        description="Team description"
    )
    settings: Optional[TeamSettings] = Field(
        default_factory=TeamSettings,
        description="Team-specific settings"
    )

    model_config = ConfigDict(from_attributes=True)


class TeamUpdate(BaseModel):
    """Schema for updating a team."""
    name: Optional[str] = Field(
        None,
        min_length=2,
        max_length=255,
        description="Display name of the team"
    )
    slug: Optional[str] = Field(
        None,
        min_length=2,
        max_length=100,
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
        description="URL-safe identifier"
    )
    description: Optional[str] = Field(
        None,
        max_length=1000,
        description="Team description"
    )
    settings: Optional[TeamSettings] = Field(
        None,
        description="Team-specific settings"
    )

    model_config = ConfigDict(from_attributes=True)


class TeamResponse(BaseModel):
    """Schema for team response."""
    id: UUID = Field(..., description="Team UUID")
    organization_id: UUID = Field(..., description="Parent organization UUID")
    name: str = Field(..., description="Display name")
    slug: str = Field(..., description="URL-safe identifier")
    description: Optional[str] = Field(None, description="Team description")
    settings: dict = Field(default_factory=dict, description="Team settings")
    members_count: int = Field(0, description="Number of members")
    human_members_count: int = Field(0, description="Number of human members")
    ai_agents_count: int = Field(0, description="Number of AI agents")
    projects_count: int = Field(0, description="Number of projects")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True)


class TeamListResponse(BaseModel):
    """Schema for paginated team list."""
    items: list[TeamResponse] = Field(default_factory=list)
    total: int = Field(0, ge=0)
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
    has_next: bool = Field(False)

    model_config = ConfigDict(from_attributes=True)


class TeamStatistics(BaseModel):
    """Schema for team statistics."""
    team_id: UUID = Field(..., description="Team UUID")
    team_name: str = Field(..., description="Team display name")
    total_members: int = Field(0, description="Total members")
    human_members: int = Field(0, description="Human members (SE4H)")
    ai_agents: int = Field(0, description="AI agents (SE4A)")
    owners_count: int = Field(0, description="Number of owners")
    admins_count: int = Field(0, description="Number of admins")
    total_projects: int = Field(0, description="Total projects")
    active_projects: int = Field(0, description="Active projects")
    agentic_maturity: AgenticMaturity = Field(
        AgenticMaturity.L0,
        description="Current agentic maturity level"
    )

    model_config = ConfigDict(from_attributes=True)


# =========================================================================
# TeamMember Schemas
# =========================================================================

class TeamMemberAdd(BaseModel):
    """Schema for adding a member to a team.

    Sprint 105: Accept user_id (UUID) OR email (string).
    If email is provided, the service will lookup the user by email.

    Note: team_id is optional in schema because it's provided via URL path
    and set by the route handler before service call.
    """
    team_id: Optional[UUID] = Field(None, description="Team UUID (set from URL path)")
    user_id: Optional[UUID] = Field(None, description="User UUID to add (optional if email provided)")
    email: Optional[str] = Field(None, description="User email to add (optional if user_id provided)")
    role: TeamRole = Field(
        TeamRole.MEMBER,
        description="Member role in team"
    )
    member_type: MemberType = Field(
        MemberType.HUMAN,
        description="Member type (human or ai_agent)"
    )

    @model_validator(mode="after")
    def validate_user_identifier(self) -> "TeamMemberAdd":
        """Validate that either user_id or email is provided."""
        if not self.user_id and not self.email:
            raise ValueError("Either user_id or email must be provided")
        return self

    @model_validator(mode="after")
    def validate_ai_agent_role(self) -> "TeamMemberAdd":
        """Validate that AI agents cannot have owner/admin roles (CTO R1/R2)."""
        if self.member_type == MemberType.AI_AGENT and self.role in (TeamRole.OWNER, TeamRole.ADMIN):
            raise ValueError(
                "AI agents cannot be owners or admins per SASE framework. "
                "Only humans (SE4H) can have VCR authority."
            )
        return self

    model_config = ConfigDict(from_attributes=True)


class TeamMemberUpdate(BaseModel):
    """Schema for updating a team member."""
    role: Optional[TeamRole] = Field(
        None,
        description="New role in team"
    )

    model_config = ConfigDict(from_attributes=True)


class TeamMemberResponse(BaseModel):
    """Schema for team member response."""
    id: UUID = Field(..., description="Membership UUID")
    team_id: UUID = Field(..., description="Team UUID")
    user_id: UUID = Field(..., description="User UUID")
    role: TeamRole = Field(..., description="Member role")
    member_type: MemberType = Field(..., description="Member type")
    sase_role: str = Field(..., description="SASE framework role designation")
    joined_at: datetime = Field(..., description="When user joined the team")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    # User details (populated from relationship)
    user_email: Optional[str] = Field(None, description="User email")
    user_name: Optional[str] = Field(None, description="User display name")
    user_avatar_url: Optional[str] = Field(None, description="User avatar URL")

    model_config = ConfigDict(from_attributes=True)


class TeamMemberListResponse(BaseModel):
    """Schema for paginated team member list."""
    items: list[TeamMemberResponse] = Field(default_factory=list)
    total: int = Field(0, ge=0)
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
    has_next: bool = Field(False)

    model_config = ConfigDict(from_attributes=True)


# =========================================================================
# User Assignment Schemas
# =========================================================================

class UserOrganizationAssign(BaseModel):
    """Schema for assigning a user to an organization."""
    user_id: UUID = Field(..., description="User UUID")
    organization_id: UUID = Field(..., description="Organization UUID")

    model_config = ConfigDict(from_attributes=True)


class ProjectTeamAssign(BaseModel):
    """Schema for assigning a project to a team."""
    project_id: UUID = Field(..., description="Project UUID")
    team_id: UUID = Field(..., description="Team UUID")

    model_config = ConfigDict(from_attributes=True)


# =========================================================================
# Bulk Operation Schemas
# =========================================================================

class BulkAddMembersRequest(BaseModel):
    """Schema for bulk adding members to a team."""
    team_id: UUID = Field(..., description="Team UUID")
    members: list[TeamMemberAdd] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="List of members to add"
    )

    model_config = ConfigDict(from_attributes=True)


class BulkOperationResult(BaseModel):
    """Schema for bulk operation result."""
    success_count: int = Field(0, description="Number of successful operations")
    failure_count: int = Field(0, description="Number of failed operations")
    errors: list[dict] = Field(
        default_factory=list,
        description="List of errors with details"
    )

    model_config = ConfigDict(from_attributes=True)
