"""
Unit Tests for Team Models
SDLC Orchestrator - Sprint 70 (Teams Foundation)
Updated: Sprint 75 (Team Role Authorization)

SDLC Stage: 04 - BUILD
Sprint: 70 - Teams Foundation, 75 - Team Role Authorization
Framework: SDLC 5.1.3 (Sprint Planning Governance)
Reference: ADR-028-Teams-Feature-Architecture
Reference: SDLC-Sprint-Planning-Governance.md

Purpose:
Test Organization, Team, and TeamMember models including:
- CRUD operations
- Relationships and cascades
- SASE constraint validation (ai_agent role restrictions)
- Property methods
- Sprint Gate Authorization (Sprint 75):
  - can_approve_sprint_gate (SE4H Coach only)
  - can_create_sprint (humans only)
  - can_manage_backlog (all active members)
  - can_perform_action for G-Sprint/G-Sprint-Close

Test Coverage Target: 90%+
"""

from datetime import datetime
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from app.models.organization import Organization
from app.models.team import Team
from app.models.team_member import TeamMember


# =============================================================================
# Organization Model Tests (S70-T19)
# =============================================================================


class TestOrganizationModel:
    """Test Organization model."""

    def test_organization_create_minimal(self):
        """Test creating organization with minimal required fields."""
        org = Organization(
            name="Acme Corporation",
            slug="acme-corp",
            plan="free",
        )

        assert org.name == "Acme Corporation"
        assert org.slug == "acme-corp"
        assert org.plan == "free"

    def test_organization_create_with_all_fields(self):
        """Test creating organization with all fields."""
        settings = {
            "require_mfa": True,
            "allowed_domains": ["acme.com"],
            "max_teams": 10
        }
        org = Organization(
            name="Enterprise Corp",
            slug="enterprise-corp",
            plan="enterprise",
            settings=settings
        )

        assert org.name == "Enterprise Corp"
        assert org.slug == "enterprise-corp"
        assert org.plan == "enterprise"
        assert org.settings["require_mfa"] is True
        assert org.settings["max_teams"] == 10

    def test_organization_is_enterprise(self):
        """Test is_enterprise property."""
        free_org = Organization(name="Free", slug="free", plan="free")
        enterprise_org = Organization(name="Enterprise", slug="enterprise", plan="enterprise")

        assert free_org.is_enterprise is False
        assert enterprise_org.is_enterprise is True

    def test_organization_is_paid(self):
        """Test is_paid property."""
        free_org = Organization(name="Free", slug="free", plan="free")
        starter_org = Organization(name="Starter", slug="starter", plan="starter")
        pro_org = Organization(name="Pro", slug="pro", plan="pro")
        enterprise_org = Organization(name="Enterprise", slug="enterprise", plan="enterprise")

        assert free_org.is_paid is False
        assert starter_org.is_paid is True
        assert pro_org.is_paid is True
        assert enterprise_org.is_paid is True

    def test_organization_require_mfa(self):
        """Test require_mfa property."""
        org_no_mfa = Organization(name="Test", slug="test", settings={})
        org_mfa = Organization(name="Test", slug="test2", settings={"require_mfa": True})

        assert org_no_mfa.require_mfa is False
        assert org_mfa.require_mfa is True

    def test_organization_allowed_email_domains(self):
        """Test allowed_email_domains property."""
        org_no_domains = Organization(name="Test", slug="test", settings={})
        org_domains = Organization(
            name="Test", slug="test2",
            settings={"allowed_domains": ["acme.com", "example.org"]}
        )

        assert org_no_domains.allowed_email_domains == []
        assert org_domains.allowed_email_domains == ["acme.com", "example.org"]

    def test_organization_is_email_allowed(self):
        """Test is_email_allowed method."""
        org_no_restriction = Organization(name="Test", slug="test", settings={})
        org_restricted = Organization(
            name="Test", slug="test2",
            settings={"allowed_domains": ["acme.com", "example.org"]}
        )

        # No domain restrictions
        assert org_no_restriction.is_email_allowed("user@random.com") is True

        # With domain restrictions
        assert org_restricted.is_email_allowed("user@acme.com") is True
        assert org_restricted.is_email_allowed("user@ACME.COM") is True  # Case insensitive
        assert org_restricted.is_email_allowed("user@example.org") is True
        assert org_restricted.is_email_allowed("user@notallowed.com") is False

    def test_organization_agentic_maturity(self):
        """Test agentic_maturity property."""
        org_no_sase = Organization(name="Test", slug="test", settings={})
        org_l2 = Organization(
            name="Test", slug="test2",
            settings={"sase_config": {"agentic_maturity": "L2"}}
        )

        assert org_no_sase.agentic_maturity == "L0"  # Default
        assert org_l2.agentic_maturity == "L2"

    def test_organization_repr(self):
        """Test __repr__ method."""
        org_id = uuid4()
        org = Organization(name="Test", slug="test-org", plan="pro")
        org.id = org_id

        repr_str = repr(org)
        assert "test-org" in repr_str
        assert "pro" in repr_str


# =============================================================================
# Team Model Tests (S70-T20)
# =============================================================================


class TestTeamModel:
    """Test Team model."""

    def test_team_create_minimal(self):
        """Test creating team with minimal required fields."""
        org_id = uuid4()
        team = Team(
            organization_id=org_id,
            name="Backend Team",
            slug="backend-team",
            settings={},
        )

        assert team.organization_id == org_id
        assert team.name == "Backend Team"
        assert team.slug == "backend-team"
        assert team.settings == {}
        assert team.description is None

    def test_team_create_with_all_fields(self):
        """Test creating team with all fields."""
        org_id = uuid4()
        settings = {
            "agentic_maturity": "L2",
            "crp_threshold": 0.8,
            "auto_approve_mrp": False,
            "mentor_scripts": ["coding-standards", "security-guidelines"]
        }
        team = Team(
            organization_id=org_id,
            name="AI Team",
            slug="ai-team",
            description="Team working on AI features",
            settings=settings
        )

        assert team.description == "Team working on AI features"
        assert team.settings["agentic_maturity"] == "L2"
        assert team.settings["crp_threshold"] == 0.8

    def test_team_agentic_maturity(self):
        """Test agentic_maturity property."""
        team_default = Team(
            organization_id=uuid4(),
            name="Test",
            slug="test",
            settings={}
        )
        team_l3 = Team(
            organization_id=uuid4(),
            name="Test2",
            slug="test2",
            settings={"agentic_maturity": "L3"}
        )

        assert team_default.agentic_maturity == "L0"  # Default
        assert team_l3.agentic_maturity == "L3"

    def test_team_crp_threshold(self):
        """Test crp_threshold property."""
        team_default = Team(
            organization_id=uuid4(),
            name="Test",
            slug="test",
            settings={}
        )
        team_custom = Team(
            organization_id=uuid4(),
            name="Test2",
            slug="test2",
            settings={"crp_threshold": 0.85}
        )

        assert team_default.crp_threshold == 0.7  # Default
        assert team_custom.crp_threshold == 0.85

    def test_team_auto_approve_mrp(self):
        """Test auto_approve_mrp property."""
        team_default = Team(
            organization_id=uuid4(),
            name="Test",
            slug="test",
            settings={}
        )
        team_auto = Team(
            organization_id=uuid4(),
            name="Test2",
            slug="test2",
            settings={"auto_approve_mrp": True}
        )

        assert team_default.auto_approve_mrp is False  # Default
        assert team_auto.auto_approve_mrp is True

    def test_team_mentor_scripts(self):
        """Test mentor_scripts property."""
        team_no_scripts = Team(
            organization_id=uuid4(),
            name="Test",
            slug="test",
            settings={}
        )
        team_scripts = Team(
            organization_id=uuid4(),
            name="Test2",
            slug="test2",
            settings={"mentor_scripts": ["script1", "script2"]}
        )

        assert team_no_scripts.mentor_scripts == []
        assert team_scripts.mentor_scripts == ["script1", "script2"]

    def test_team_briefing_templates(self):
        """Test briefing_templates property."""
        team_no_templates = Team(
            organization_id=uuid4(),
            name="Test",
            slug="test",
            settings={}
        )
        team_templates = Team(
            organization_id=uuid4(),
            name="Test2",
            slug="test2",
            settings={"briefing_templates": ["template1"]}
        )

        assert team_no_templates.briefing_templates == []
        assert team_templates.briefing_templates == ["template1"]

    def test_team_repr(self):
        """Test __repr__ method."""
        org_id = uuid4()
        team_id = uuid4()
        team = Team(
            organization_id=org_id,
            name="Backend",
            slug="backend"
        )
        team.id = team_id

        repr_str = repr(team)
        assert "backend" in repr_str


# =============================================================================
# TeamMember Model Tests (S70-T21)
# =============================================================================


class TestTeamMemberModel:
    """Test TeamMember model."""

    def test_team_member_create_minimal(self):
        """Test creating team member with minimal fields."""
        team_id = uuid4()
        user_id = uuid4()

        member = TeamMember(
            team_id=team_id,
            user_id=user_id,
            role="member",
            member_type="human",
        )

        assert member.team_id == team_id
        assert member.user_id == user_id
        assert member.role == "member"
        assert member.member_type == "human"

    def test_team_member_create_owner(self):
        """Test creating team owner (human)."""
        member = TeamMember(
            team_id=uuid4(),
            user_id=uuid4(),
            role="owner",
            member_type="human"
        )

        assert member.role == "owner"
        assert member.member_type == "human"
        assert member.is_owner is True
        assert member.is_admin_or_owner is True

    def test_team_member_create_admin(self):
        """Test creating team admin (human)."""
        member = TeamMember(
            team_id=uuid4(),
            user_id=uuid4(),
            role="admin",
            member_type="human"
        )

        assert member.role == "admin"
        assert member.is_admin is True
        assert member.is_admin_or_owner is True
        assert member.is_owner is False

    def test_team_member_create_ai_agent(self):
        """Test creating AI agent member (CTO R1/R2)."""
        member = TeamMember(
            team_id=uuid4(),
            user_id=uuid4(),
            role="ai_agent",
            member_type="ai_agent"
        )

        assert member.role == "ai_agent"
        assert member.member_type == "ai_agent"
        assert member.is_ai_agent is True
        assert member.is_human is False
        assert member.is_executor is True

    def test_team_member_is_coach(self):
        """Test is_coach property (SE4H Coach)."""
        owner = TeamMember(
            team_id=uuid4(),
            user_id=uuid4(),
            role="owner",
            member_type="human"
        )
        admin = TeamMember(
            team_id=uuid4(),
            user_id=uuid4(),
            role="admin",
            member_type="human"
        )
        member = TeamMember(
            team_id=uuid4(),
            user_id=uuid4(),
            role="member",
            member_type="human"
        )
        ai_agent = TeamMember(
            team_id=uuid4(),
            user_id=uuid4(),
            role="ai_agent",
            member_type="ai_agent"
        )

        assert owner.is_coach is True
        assert admin.is_coach is True
        assert member.is_coach is False
        assert ai_agent.is_coach is False

    def test_team_member_can_manage_members(self):
        """Test can_manage_members property."""
        human_owner = TeamMember(
            team_id=uuid4(),
            user_id=uuid4(),
            role="owner",
            member_type="human"
        )
        human_admin = TeamMember(
            team_id=uuid4(),
            user_id=uuid4(),
            role="admin",
            member_type="human"
        )
        human_member = TeamMember(
            team_id=uuid4(),
            user_id=uuid4(),
            role="member",
            member_type="human"
        )

        assert human_owner.can_manage_members is True
        assert human_admin.can_manage_members is True
        assert human_member.can_manage_members is False

    def test_team_member_can_approve_vcr(self):
        """Test can_approve_vcr property (human coaches only)."""
        human_owner = TeamMember(
            team_id=uuid4(),
            user_id=uuid4(),
            role="owner",
            member_type="human"
        )
        human_member = TeamMember(
            team_id=uuid4(),
            user_id=uuid4(),
            role="member",
            member_type="human"
        )
        ai_agent = TeamMember(
            team_id=uuid4(),
            user_id=uuid4(),
            role="ai_agent",
            member_type="ai_agent"
        )

        assert human_owner.can_approve_vcr is True
        assert human_member.can_approve_vcr is False
        assert ai_agent.can_approve_vcr is False

    def test_team_member_get_sase_role(self):
        """Test get_sase_role method."""
        owner = TeamMember(
            team_id=uuid4(),
            user_id=uuid4(),
            role="owner",
            member_type="human"
        )
        admin = TeamMember(
            team_id=uuid4(),
            user_id=uuid4(),
            role="admin",
            member_type="human"
        )
        member = TeamMember(
            team_id=uuid4(),
            user_id=uuid4(),
            role="member",
            member_type="human"
        )
        ai_agent = TeamMember(
            team_id=uuid4(),
            user_id=uuid4(),
            role="ai_agent",
            member_type="ai_agent"
        )

        assert owner.get_sase_role() == "SE4H_Coach"
        assert admin.get_sase_role() == "SE4H_Coach"
        assert member.get_sase_role() == "SE4H_Member"
        assert ai_agent.get_sase_role() == "SE4A_Executor"

    def test_team_member_can_perform_action(self):
        """Test can_perform_action method."""
        owner = TeamMember(
            team_id=uuid4(),
            user_id=uuid4(),
            role="owner",
            member_type="human"
        )
        admin = TeamMember(
            team_id=uuid4(),
            user_id=uuid4(),
            role="admin",
            member_type="human"
        )
        member = TeamMember(
            team_id=uuid4(),
            user_id=uuid4(),
            role="member",
            member_type="human"
        )
        ai_agent = TeamMember(
            team_id=uuid4(),
            user_id=uuid4(),
            role="ai_agent",
            member_type="ai_agent"
        )

        # Owner-only actions
        assert owner.can_perform_action("delete_team") is True
        assert admin.can_perform_action("delete_team") is False

        # Admin actions
        assert owner.can_perform_action("add_member") is True
        assert admin.can_perform_action("add_member") is True
        assert member.can_perform_action("add_member") is False

        # AI agent actions
        assert ai_agent.can_perform_action("execute_task") is True
        assert ai_agent.can_perform_action("add_member") is False

    def test_team_member_repr(self):
        """Test __repr__ method."""
        team_id = uuid4()
        user_id = uuid4()
        member_id = uuid4()

        member = TeamMember(
            team_id=team_id,
            user_id=user_id,
            role="admin"
        )
        member.id = member_id

        repr_str = repr(member)
        assert "admin" in repr_str


# =============================================================================
# Relationship Tests (S70-T22)
# =============================================================================


class TestTeamRelationships:
    """Test relationships between Team models."""

    def test_organization_teams_relationship_initialized(self):
        """Test that organization teams relationship is initialized."""
        org = Organization(name="Test", slug="test")
        # The teams list should be initialized by SQLAlchemy
        assert hasattr(org, 'teams')

    def test_team_organization_relationship_initialized(self):
        """Test that team organization relationship is initialized."""
        team = Team(
            organization_id=uuid4(),
            name="Test",
            slug="test"
        )
        assert hasattr(team, 'organization')

    def test_team_members_relationship_initialized(self):
        """Test that team members relationship is initialized."""
        team = Team(
            organization_id=uuid4(),
            name="Test",
            slug="test"
        )
        assert hasattr(team, 'members')

    def test_team_projects_relationship_initialized(self):
        """Test that team projects relationship is initialized."""
        team = Team(
            organization_id=uuid4(),
            name="Test",
            slug="test"
        )
        assert hasattr(team, 'projects')

    def test_team_member_team_relationship_initialized(self):
        """Test that team member team relationship is initialized."""
        member = TeamMember(
            team_id=uuid4(),
            user_id=uuid4()
        )
        assert hasattr(member, 'team')

    def test_team_member_user_relationship_initialized(self):
        """Test that team member user relationship is initialized."""
        member = TeamMember(
            team_id=uuid4(),
            user_id=uuid4()
        )
        assert hasattr(member, 'user')


# =============================================================================
# Constraint Violation Tests (S70-T23)
# =============================================================================


class TestTeamConstraints:
    """Test database constraints for Team models."""

    def test_team_member_role_values(self):
        """Test that only valid role values are allowed."""
        valid_roles = ["owner", "admin", "member", "ai_agent"]

        for role in valid_roles:
            member = TeamMember(
                team_id=uuid4(),
                user_id=uuid4(),
                role=role
            )
            assert member.role == role

    def test_team_member_type_values(self):
        """Test that only valid member_type values are allowed."""
        valid_types = ["human", "ai_agent"]

        for member_type in valid_types:
            member = TeamMember(
                team_id=uuid4(),
                user_id=uuid4(),
                member_type=member_type
            )
            assert member.member_type == member_type

    def test_organization_plan_values(self):
        """Test that only valid plan values are allowed."""
        valid_plans = ["free", "starter", "pro", "enterprise"]

        for plan in valid_plans:
            org = Organization(
                name="Test",
                slug=f"test-{plan}",
                plan=plan
            )
            assert org.plan == plan


# =============================================================================
# Pydantic Schema Validation Tests
# =============================================================================


class TestTeamSchemaValidation:
    """Test Pydantic schema validation for Team models."""

    def test_team_member_add_schema_ai_agent_owner_rejected(self):
        """Test that AI agent cannot be assigned owner role via schema."""
        from app.schemas.team import TeamMemberAdd, TeamRole, MemberType

        with pytest.raises(ValueError) as excinfo:
            TeamMemberAdd(
                team_id=uuid4(),
                user_id=uuid4(),
                role=TeamRole.OWNER,
                member_type=MemberType.AI_AGENT
            )

        assert "AI agents cannot be owners or admins" in str(excinfo.value)

    def test_team_member_add_schema_ai_agent_admin_rejected(self):
        """Test that AI agent cannot be assigned admin role via schema."""
        from app.schemas.team import TeamMemberAdd, TeamRole, MemberType

        with pytest.raises(ValueError) as excinfo:
            TeamMemberAdd(
                team_id=uuid4(),
                user_id=uuid4(),
                role=TeamRole.ADMIN,
                member_type=MemberType.AI_AGENT
            )

        assert "AI agents cannot be owners or admins" in str(excinfo.value)

    def test_team_member_add_schema_ai_agent_member_allowed(self):
        """Test that AI agent can be assigned member role."""
        from app.schemas.team import TeamMemberAdd, TeamRole, MemberType

        # Should not raise
        member = TeamMemberAdd(
            team_id=uuid4(),
            user_id=uuid4(),
            role=TeamRole.MEMBER,
            member_type=MemberType.AI_AGENT
        )

        assert member.role == TeamRole.MEMBER
        assert member.member_type == MemberType.AI_AGENT

    def test_team_member_add_schema_ai_agent_role_allowed(self):
        """Test that AI agent can be assigned ai_agent role."""
        from app.schemas.team import TeamMemberAdd, TeamRole, MemberType

        # Should not raise
        member = TeamMemberAdd(
            team_id=uuid4(),
            user_id=uuid4(),
            role=TeamRole.AI_AGENT,
            member_type=MemberType.AI_AGENT
        )

        assert member.role == TeamRole.AI_AGENT
        assert member.member_type == MemberType.AI_AGENT

    def test_organization_slug_pattern_validation(self):
        """Test organization slug pattern validation."""
        from app.schemas.team import OrganizationCreate

        # Valid slugs
        valid_slugs = ["acme", "acme-corp", "test-123", "a1b2c3"]
        for slug in valid_slugs:
            org = OrganizationCreate(name="Test", slug=slug)
            assert org.slug == slug

        # Invalid slugs
        invalid_slugs = ["Acme", "acme_corp", "-acme", "acme-", "acme--corp"]
        for slug in invalid_slugs:
            with pytest.raises(ValueError):
                OrganizationCreate(name="Test", slug=slug)

    def test_team_slug_pattern_validation(self):
        """Test team slug pattern validation."""
        from app.schemas.team import TeamCreate

        # Valid slugs
        org_id = uuid4()
        valid_slugs = ["backend", "backend-team", "team-123"]
        for slug in valid_slugs:
            team = TeamCreate(
                organization_id=org_id,
                name="Test",
                slug=slug
            )
            assert team.slug == slug

        # Invalid slugs
        invalid_slugs = ["Backend", "backend_team", "-backend"]
        for slug in invalid_slugs:
            with pytest.raises(ValueError):
                TeamCreate(
                    organization_id=org_id,
                    name="Test",
                    slug=slug
                )

    def test_team_settings_crp_threshold_range(self):
        """Test CRP threshold validation (0.0 to 1.0)."""
        from app.schemas.team import TeamSettings

        # Valid thresholds
        for threshold in [0.0, 0.5, 0.7, 1.0]:
            settings = TeamSettings(crp_threshold=threshold)
            assert settings.crp_threshold == threshold

        # Invalid thresholds
        for threshold in [-0.1, 1.1, 2.0]:
            with pytest.raises(ValueError):
                TeamSettings(crp_threshold=threshold)


# =============================================================================
# Sprint Gate Authorization Tests (Sprint 75)
# =============================================================================


class TestSprintGateAuthorization:
    """
    Test Sprint Gate Authorization - Sprint 75 Integration.

    SDLC 5.1.3 Sprint Planning Governance:
    - Only SE4H Coach (team owner/admin) can approve sprint gates
    - AI agents (SE4A) cannot approve governance gates
    - Human oversight enforcement for G-Sprint/G-Sprint-Close
    """

    def test_can_approve_sprint_gate_owner(self):
        """Test that team owner can approve sprint gates."""
        owner = TeamMember(
            team_id=uuid4(),
            user_id=uuid4(),
            role="owner",
            member_type="human"
        )

        assert owner.can_approve_sprint_gate is True

    def test_can_approve_sprint_gate_admin(self):
        """Test that team admin can approve sprint gates."""
        admin = TeamMember(
            team_id=uuid4(),
            user_id=uuid4(),
            role="admin",
            member_type="human"
        )

        assert admin.can_approve_sprint_gate is True

    def test_can_approve_sprint_gate_member_rejected(self):
        """Test that regular member cannot approve sprint gates."""
        member = TeamMember(
            team_id=uuid4(),
            user_id=uuid4(),
            role="member",
            member_type="human"
        )

        assert member.can_approve_sprint_gate is False

    def test_can_approve_sprint_gate_ai_agent_rejected(self):
        """Test that AI agent cannot approve sprint gates (SASE constraint)."""
        ai_agent = TeamMember(
            team_id=uuid4(),
            user_id=uuid4(),
            role="ai_agent",
            member_type="ai_agent"
        )

        assert ai_agent.can_approve_sprint_gate is False
        assert ai_agent.is_ai_agent is True

    def test_can_create_sprint_human_member(self):
        """Test that human member can create sprints."""
        human_member = TeamMember(
            team_id=uuid4(),
            user_id=uuid4(),
            role="member",
            member_type="human"
        )

        assert human_member.can_create_sprint is True

    def test_can_create_sprint_human_owner(self):
        """Test that human owner can create sprints."""
        human_owner = TeamMember(
            team_id=uuid4(),
            user_id=uuid4(),
            role="owner",
            member_type="human"
        )

        assert human_owner.can_create_sprint is True

    def test_can_create_sprint_ai_agent_rejected(self):
        """Test that AI agent cannot create sprints."""
        ai_agent = TeamMember(
            team_id=uuid4(),
            user_id=uuid4(),
            role="ai_agent",
            member_type="ai_agent"
        )

        assert ai_agent.can_create_sprint is False

    def test_can_manage_backlog_all_active_members(self):
        """Test that all active members can manage backlog."""
        human_member = TeamMember(
            team_id=uuid4(),
            user_id=uuid4(),
            role="member",
            member_type="human"
        )
        ai_agent = TeamMember(
            team_id=uuid4(),
            user_id=uuid4(),
            role="ai_agent",
            member_type="ai_agent"
        )

        assert human_member.can_manage_backlog is True
        assert ai_agent.can_manage_backlog is True

    def test_can_manage_backlog_deleted_member_rejected(self):
        """Test that deleted members cannot manage backlog."""
        deleted_member = TeamMember(
            team_id=uuid4(),
            user_id=uuid4(),
            role="member",
            member_type="human"
        )
        deleted_member.deleted_at = datetime.utcnow()

        assert deleted_member.can_manage_backlog is False

    def test_can_perform_action_g_sprint_approval(self):
        """Test can_perform_action for G-Sprint approval."""
        owner = TeamMember(
            team_id=uuid4(),
            user_id=uuid4(),
            role="owner",
            member_type="human"
        )
        admin = TeamMember(
            team_id=uuid4(),
            user_id=uuid4(),
            role="admin",
            member_type="human"
        )
        member = TeamMember(
            team_id=uuid4(),
            user_id=uuid4(),
            role="member",
            member_type="human"
        )
        ai_agent = TeamMember(
            team_id=uuid4(),
            user_id=uuid4(),
            role="ai_agent",
            member_type="ai_agent"
        )

        # Only SE4H Coach (owner/admin) can approve
        assert owner.can_perform_action("approve_g_sprint") is True
        assert admin.can_perform_action("approve_g_sprint") is True
        assert member.can_perform_action("approve_g_sprint") is False
        assert ai_agent.can_perform_action("approve_g_sprint") is False

    def test_can_perform_action_g_sprint_close_approval(self):
        """Test can_perform_action for G-Sprint-Close approval."""
        owner = TeamMember(
            team_id=uuid4(),
            user_id=uuid4(),
            role="owner",
            member_type="human"
        )
        admin = TeamMember(
            team_id=uuid4(),
            user_id=uuid4(),
            role="admin",
            member_type="human"
        )
        member = TeamMember(
            team_id=uuid4(),
            user_id=uuid4(),
            role="member",
            member_type="human"
        )
        ai_agent = TeamMember(
            team_id=uuid4(),
            user_id=uuid4(),
            role="ai_agent",
            member_type="ai_agent"
        )

        # Only SE4H Coach (owner/admin) can approve
        assert owner.can_perform_action("approve_g_sprint_close") is True
        assert admin.can_perform_action("approve_g_sprint_close") is True
        assert member.can_perform_action("approve_g_sprint_close") is False
        assert ai_agent.can_perform_action("approve_g_sprint_close") is False

    def test_can_perform_action_create_sprint(self):
        """Test can_perform_action for sprint creation."""
        owner = TeamMember(
            team_id=uuid4(),
            user_id=uuid4(),
            role="owner",
            member_type="human"
        )
        member = TeamMember(
            team_id=uuid4(),
            user_id=uuid4(),
            role="member",
            member_type="human"
        )
        ai_agent = TeamMember(
            team_id=uuid4(),
            user_id=uuid4(),
            role="ai_agent",
            member_type="ai_agent"
        )

        # Any active member can create sprints
        assert owner.can_perform_action("create_sprint") is True
        assert member.can_perform_action("create_sprint") is True
        assert ai_agent.can_perform_action("create_sprint") is True

    def test_can_perform_action_manage_backlog(self):
        """Test can_perform_action for backlog management."""
        owner = TeamMember(
            team_id=uuid4(),
            user_id=uuid4(),
            role="owner",
            member_type="human"
        )
        member = TeamMember(
            team_id=uuid4(),
            user_id=uuid4(),
            role="member",
            member_type="human"
        )
        ai_agent = TeamMember(
            team_id=uuid4(),
            user_id=uuid4(),
            role="ai_agent",
            member_type="ai_agent"
        )

        # Any active member can manage backlog
        assert owner.can_perform_action("manage_backlog") is True
        assert member.can_perform_action("manage_backlog") is True
        assert ai_agent.can_perform_action("manage_backlog") is True

    def test_sprint_gate_approval_sase_alignment(self):
        """
        Test SASE framework alignment for sprint gate authorization.

        SE4H Coach (human owner/admin):
        - Can approve G-Sprint
        - Can approve G-Sprint-Close
        - Has VCR authority

        SE4A Executor (AI agent):
        - Cannot approve gates
        - Cannot hold VCR authority
        """
        coach = TeamMember(
            team_id=uuid4(),
            user_id=uuid4(),
            role="owner",
            member_type="human"
        )
        executor = TeamMember(
            team_id=uuid4(),
            user_id=uuid4(),
            role="ai_agent",
            member_type="ai_agent"
        )

        # SASE role verification
        assert coach.get_sase_role() == "SE4H_Coach"
        assert executor.get_sase_role() == "SE4A_Executor"

        # Sprint gate authorization
        assert coach.can_approve_sprint_gate is True
        assert executor.can_approve_sprint_gate is False

        # VCR authority (same as sprint gate for coaches)
        assert coach.can_approve_vcr is True
        assert executor.can_approve_vcr is False
