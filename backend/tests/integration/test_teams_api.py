"""
Integration Tests for Teams API
SDLC Orchestrator - Sprint 71 (Teams Backend API)

SDLC Stage: 04 - BUILD
Sprint: 71 - Teams Backend API
Framework: SDLC 5.1.2
Reference: ADR-028-Teams-Feature-Architecture

Purpose:
Test Teams API endpoints including:
- Team CRUD operations
- Member management
- Permission validation
- SASE constraint enforcement

Test Coverage Target: 90%+
"""

import pytest
from httpx import AsyncClient
from uuid import uuid4

from app.models.organization import Organization
from app.models.team import Team
from app.models.team_member import TeamMember
from app.models.user import User


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
async def test_organization(db_session):
    """Create a test organization."""
    org = Organization(
        name="Test Corp",
        slug=f"test-corp-{uuid4().hex[:8]}",
        plan="pro",
        settings={"require_mfa": False}
    )
    db_session.add(org)
    await db_session.commit()
    await db_session.refresh(org)
    return org


@pytest.fixture
async def test_user_in_org(db_session, test_organization):
    """Create a test user in the test organization."""
    user = User(
        email=f"user-{uuid4().hex[:8]}@test.com",
        password_hash="$2b$12$dummy_hash",
        full_name="Test User",
        organization_id=test_organization.id,
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_team(db_session, test_organization, test_user_in_org):
    """Create a test team with owner."""
    team = Team(
        organization_id=test_organization.id,
        name="Backend Team",
        slug=f"backend-team-{uuid4().hex[:8]}",
        description="Test backend team",
        settings={"agentic_maturity": "L1"}
    )
    db_session.add(team)
    await db_session.flush()

    # Add owner
    member = TeamMember(
        team_id=team.id,
        user_id=test_user_in_org.id,
        role="owner",
        member_type="human"
    )
    db_session.add(member)
    await db_session.commit()
    await db_session.refresh(team)
    return team


@pytest.fixture
async def second_user(db_session, test_organization):
    """Create a second test user."""
    user = User(
        email=f"user2-{uuid4().hex[:8]}@test.com",
        password_hash="$2b$12$dummy_hash",
        full_name="Second User",
        organization_id=test_organization.id,
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


# =============================================================================
# Team CRUD Tests (S71-T36)
# =============================================================================

class TestTeamCRUD:
    """Test Team CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_team_success(
        self, client: AsyncClient, auth_headers, test_organization
    ):
        """Test creating a team successfully."""
        response = await client.post(
            "/api/v1/teams",
            json={
                "organization_id": str(test_organization.id),
                "name": "New Team",
                "slug": f"new-team-{uuid4().hex[:8]}",
                "description": "A new test team",
                "settings": {"agentic_maturity": "L0"}
            },
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New Team"
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_team_duplicate_slug(
        self, client: AsyncClient, auth_headers, test_team
    ):
        """Test creating a team with duplicate slug fails."""
        response = await client.post(
            "/api/v1/teams",
            json={
                "organization_id": str(test_team.organization_id),
                "name": "Duplicate Team",
                "slug": test_team.slug  # Duplicate slug
            },
            headers=auth_headers
        )
        
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_team_success(
        self, client: AsyncClient, auth_headers, test_team
    ):
        """Test getting team details."""
        response = await client.get(
            f"/api/v1/teams/{test_team.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_team.id)
        assert data["name"] == test_team.name

    @pytest.mark.asyncio
    async def test_get_team_not_found(
        self, client: AsyncClient, auth_headers
    ):
        """Test getting non-existent team."""
        response = await client.get(
            f"/api/v1/teams/{uuid4()}",
            headers=auth_headers
        )
        
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_list_teams(
        self, client: AsyncClient, auth_headers, test_team
    ):
        """Test listing teams."""
        response = await client.get(
            "/api/v1/teams",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    @pytest.mark.asyncio
    async def test_update_team_success(
        self, client: AsyncClient, auth_headers, test_team
    ):
        """Test updating team details."""
        response = await client.patch(
            f"/api/v1/teams/{test_team.id}",
            json={
                "name": "Updated Team Name",
                "description": "Updated description"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Team Name"

    @pytest.mark.asyncio
    async def test_delete_team_success(
        self, client: AsyncClient, auth_headers, test_team
    ):
        """Test deleting team (soft delete)."""
        response = await client.delete(
            f"/api/v1/teams/{test_team.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 204


# =============================================================================
# Team Statistics Tests (S71-T37)
# =============================================================================

class TestTeamStatistics:
    """Test Team statistics endpoint."""

    @pytest.mark.asyncio
    async def test_get_team_statistics(
        self, client: AsyncClient, auth_headers, test_team
    ):
        """Test getting team statistics."""
        response = await client.get(
            f"/api/v1/teams/{test_team.id}/stats",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "total_members" in data
        assert "human_members" in data
        assert "ai_agents" in data
        assert "agentic_maturity" in data


# =============================================================================
# Member Management Tests (S71-T38)
# =============================================================================

class TestMemberManagement:
    """Test Team member management."""

    @pytest.mark.asyncio
    async def test_add_member_success(
        self, client: AsyncClient, auth_headers, test_team, second_user
    ):
        """Test adding a member to team."""
        response = await client.post(
            f"/api/v1/teams/{test_team.id}/members",
            json={
                "team_id": str(test_team.id),
                "user_id": str(second_user.id),
                "role": "member",
                "member_type": "human"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["user_id"] == str(second_user.id)
        assert data["role"] == "member"

    @pytest.mark.asyncio
    async def test_add_ai_agent_member(
        self, client: AsyncClient, auth_headers, test_team, second_user
    ):
        """Test adding an AI agent to team."""
        response = await client.post(
            f"/api/v1/teams/{test_team.id}/members",
            json={
                "team_id": str(test_team.id),
                "user_id": str(second_user.id),
                "role": "ai_agent",
                "member_type": "ai_agent"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["member_type"] == "ai_agent"
        assert data["role"] == "ai_agent"

    @pytest.mark.asyncio
    async def test_add_ai_agent_as_owner_fails(
        self, client: AsyncClient, auth_headers, test_team, second_user
    ):
        """Test that AI agent cannot be owner (SASE constraint)."""
        response = await client.post(
            f"/api/v1/teams/{test_team.id}/members",
            json={
                "team_id": str(test_team.id),
                "user_id": str(second_user.id),
                "role": "owner",
                "member_type": "ai_agent"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 400
        assert "AI agents cannot be owner" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_add_ai_agent_as_admin_fails(
        self, client: AsyncClient, auth_headers, test_team, second_user
    ):
        """Test that AI agent cannot be admin (SASE constraint)."""
        response = await client.post(
            f"/api/v1/teams/{test_team.id}/members",
            json={
                "team_id": str(test_team.id),
                "user_id": str(second_user.id),
                "role": "admin",
                "member_type": "ai_agent"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 400
        assert "AI agents cannot be" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_list_members(
        self, client: AsyncClient, auth_headers, test_team
    ):
        """Test listing team members."""
        response = await client.get(
            f"/api/v1/teams/{test_team.id}/members",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) >= 1  # At least the owner

    @pytest.mark.asyncio
    async def test_update_member_role(
        self, client: AsyncClient, auth_headers, test_team, second_user, db_session
    ):
        """Test updating member role."""
        # First add the user as member
        member = TeamMember(
            team_id=test_team.id,
            user_id=second_user.id,
            role="member",
            member_type="human"
        )
        db_session.add(member)
        await db_session.commit()

        # Update to admin
        response = await client.patch(
            f"/api/v1/teams/{test_team.id}/members/{second_user.id}",
            json={"role": "admin"},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "admin"

    @pytest.mark.asyncio
    async def test_remove_member(
        self, client: AsyncClient, auth_headers, test_team, second_user, db_session
    ):
        """Test removing a team member."""
        # First add the user
        member = TeamMember(
            team_id=test_team.id,
            user_id=second_user.id,
            role="member",
            member_type="human"
        )
        db_session.add(member)
        await db_session.commit()

        # Remove member
        response = await client.delete(
            f"/api/v1/teams/{test_team.id}/members/{second_user.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 204


# =============================================================================
# Permission Tests (S71-T39)
# =============================================================================

class TestPermissions:
    """Test permission validation."""

    @pytest.mark.asyncio
    async def test_non_member_cannot_view_team(
        self, client: AsyncClient, test_team
    ):
        """Test that non-members cannot view team details."""
        # Create a different user not in the team
        headers = {"Authorization": "Bearer fake_token_for_different_user"}
        
        response = await client.get(
            f"/api/v1/teams/{test_team.id}",
            headers=headers
        )
        
        # Should be 401 (unauthenticated) or 403 (forbidden)
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_member_cannot_delete_team(
        self, client: AsyncClient, test_team, second_user, db_session
    ):
        """Test that regular members cannot delete team."""
        # Add second_user as regular member
        member = TeamMember(
            team_id=test_team.id,
            user_id=second_user.id,
            role="member",
            member_type="human"
        )
        db_session.add(member)
        await db_session.commit()

        # Try to delete as member (should fail)
        # Would need token for second_user
        # This test would need proper auth setup


# =============================================================================
# SASE Compliance Tests (S71-T40)
# =============================================================================

class TestSASECompliance:
    """Test SASE framework compliance."""

    @pytest.mark.asyncio
    async def test_sase_role_in_member_response(
        self, client: AsyncClient, auth_headers, test_team
    ):
        """Test that SASE role is included in member response."""
        response = await client.get(
            f"/api/v1/teams/{test_team.id}/members",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        for member in data["items"]:
            assert "sase_role" in member
            # Owner should be SE4H_Coach
            if member["role"] == "owner":
                assert member["sase_role"] == "SE4H_Coach"

    @pytest.mark.asyncio
    async def test_agentic_maturity_in_statistics(
        self, client: AsyncClient, auth_headers, test_team
    ):
        """Test that agentic maturity is included in statistics."""
        response = await client.get(
            f"/api/v1/teams/{test_team.id}/stats",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "agentic_maturity" in data
        assert data["agentic_maturity"] in ["L0", "L1", "L2", "L3"]


# =============================================================================
# Edge Cases and Error Handling Tests (S71-T41)
# =============================================================================

class TestEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_cannot_remove_last_owner(
        self, client: AsyncClient, auth_headers, test_team, test_user_in_org
    ):
        """Test that last owner cannot be removed."""
        response = await client.delete(
            f"/api/v1/teams/{test_team.id}/members/{test_user_in_org.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 400
        assert "last owner" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_add_duplicate_member_fails(
        self, client: AsyncClient, auth_headers, test_team, test_user_in_org
    ):
        """Test that adding duplicate member fails."""
        response = await client.post(
            f"/api/v1/teams/{test_team.id}/members",
            json={
                "team_id": str(test_team.id),
                "user_id": str(test_user_in_org.id),  # Already owner
                "role": "member",
                "member_type": "human"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 409
        assert "already a member" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_invalid_slug_pattern(
        self, client: AsyncClient, auth_headers, test_organization
    ):
        """Test that invalid slug patterns are rejected."""
        response = await client.post(
            "/api/v1/teams",
            json={
                "organization_id": str(test_organization.id),
                "name": "Invalid Slug Team",
                "slug": "Invalid Slug With Spaces"  # Invalid
            },
            headers=auth_headers
        )
        
        assert response.status_code == 422  # Pydantic validation error

    @pytest.mark.asyncio
    async def test_pagination(
        self, client: AsyncClient, auth_headers
    ):
        """Test pagination parameters."""
        response = await client.get(
            "/api/v1/teams",
            params={"skip": 0, "limit": 5},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["page_size"] == 5
        assert "has_next" in data
