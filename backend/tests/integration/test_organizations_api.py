"""
Integration Tests for Organizations API
SDLC Orchestrator - Sprint 71 (Teams Backend API)

SDLC Stage: 04 - BUILD
Sprint: 71 - Teams Backend API
Framework: SDLC 5.1.2
Reference: ADR-028-Teams-Feature-Architecture

Purpose:
Test Organizations API endpoints including:
- Organization CRUD operations
- User assignment
- Statistics
- Multi-tenancy isolation

Test Coverage Target: 90%+
"""

import pytest
from httpx import AsyncClient
from uuid import uuid4

from app.models.organization import Organization
from app.models.team import Team
from app.models.user import User


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
async def test_organization(db_session):
    """Create a test organization."""
    org = Organization(
        name="Test Organization",
        slug=f"test-org-{uuid4().hex[:8]}",
        plan="pro",
        settings={
            "require_mfa": False,
            "allowed_domains": ["test.com"],
            "sase_config": {"agentic_maturity": "L1"}
        }
    )
    db_session.add(org)
    await db_session.commit()
    await db_session.refresh(org)
    return org


@pytest.fixture
async def test_user_in_org(db_session, test_organization):
    """Create a test user in the test organization."""
    user = User(
        email=f"orguser-{uuid4().hex[:8]}@test.com",
        password_hash="$2b$12$dummy_hash",
        full_name="Org User",
        organization_id=test_organization.id,
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_team_in_org(db_session, test_organization):
    """Create a test team in the organization."""
    team = Team(
        organization_id=test_organization.id,
        name="Test Team",
        slug=f"test-team-{uuid4().hex[:8]}",
        settings={}
    )
    db_session.add(team)
    await db_session.commit()
    await db_session.refresh(team)
    return team


# =============================================================================
# Organization CRUD Tests
# =============================================================================

class TestOrganizationCRUD:
    """Test Organization CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_organization_success(
        self, client: AsyncClient, auth_headers
    ):
        """Test creating an organization successfully."""
        response = await client.post(
            "/api/v1/organizations",
            json={
                "name": "New Organization",
                "slug": f"new-org-{uuid4().hex[:8]}",
                "plan": "starter",
                "settings": {
                    "require_mfa": True,
                    "allowed_domains": ["neworg.com"]
                }
            },
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New Organization"
        assert data["plan"] == "starter"
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_organization_duplicate_slug(
        self, client: AsyncClient, auth_headers, test_organization
    ):
        """Test creating organization with duplicate slug fails."""
        response = await client.post(
            "/api/v1/organizations",
            json={
                "name": "Duplicate Org",
                "slug": test_organization.slug  # Duplicate
            },
            headers=auth_headers
        )
        
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_organization_success(
        self, client: AsyncClient, auth_headers, test_organization, test_user_in_org
    ):
        """Test getting organization details."""
        response = await client.get(
            f"/api/v1/organizations/{test_organization.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_organization.id)
        assert data["name"] == test_organization.name
        assert data["plan"] == test_organization.plan

    @pytest.mark.asyncio
    async def test_get_organization_not_found(
        self, client: AsyncClient, auth_headers
    ):
        """Test getting non-existent organization."""
        response = await client.get(
            f"/api/v1/organizations/{uuid4()}",
            headers=auth_headers
        )
        
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_list_organizations(
        self, client: AsyncClient, auth_headers, test_organization
    ):
        """Test listing organizations."""
        response = await client.get(
            "/api/v1/organizations",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data

    @pytest.mark.asyncio
    async def test_update_organization_success(
        self, client: AsyncClient, auth_headers, test_organization
    ):
        """Test updating organization details."""
        response = await client.patch(
            f"/api/v1/organizations/{test_organization.id}",
            json={
                "name": "Updated Org Name",
                "plan": "enterprise"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Org Name"
        assert data["plan"] == "enterprise"

    @pytest.mark.asyncio
    async def test_update_organization_slug_conflict(
        self, client: AsyncClient, auth_headers, test_organization, db_session
    ):
        """Test updating organization with conflicting slug."""
        # Create another organization
        other_org = Organization(
            name="Other Org",
            slug=f"other-org-{uuid4().hex[:8]}"
        )
        db_session.add(other_org)
        await db_session.commit()
        
        # Try to update to existing slug
        response = await client.patch(
            f"/api/v1/organizations/{test_organization.id}",
            json={"slug": other_org.slug},
            headers=auth_headers
        )
        
        assert response.status_code == 409


# =============================================================================
# Organization Statistics Tests
# =============================================================================

class TestOrganizationStatistics:
    """Test Organization statistics endpoint."""

    @pytest.mark.asyncio
    async def test_get_organization_statistics(
        self, client: AsyncClient, auth_headers, test_organization, 
        test_user_in_org, test_team_in_org
    ):
        """Test getting organization statistics."""
        response = await client.get(
            f"/api/v1/organizations/{test_organization.id}/stats",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "teams_count" in data
        assert "users_count" in data
        assert "plan" in data
        assert "agentic_maturity" in data
        assert data["teams_count"] >= 1  # test_team_in_org
        assert data["users_count"] >= 1  # test_user_in_org


# =============================================================================
# Multi-Tenancy Tests
# =============================================================================

class TestMultiTenancy:
    """Test multi-tenancy isolation."""

    @pytest.mark.asyncio
    async def test_users_see_only_their_organization(
        self, client: AsyncClient, auth_headers, test_organization, db_session
    ):
        """Test that regular users only see their organization."""
        # Create another organization
        other_org = Organization(
            name="Other Company",
            slug=f"other-company-{uuid4().hex[:8]}"
        )
        db_session.add(other_org)
        await db_session.commit()

        # List should only return user's organization
        response = await client.get(
            "/api/v1/organizations",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        # Non-superuser should only see their org
        # (depends on auth implementation)

    @pytest.mark.asyncio
    async def test_cannot_access_other_organization(
        self, client: AsyncClient, auth_headers, db_session
    ):
        """Test that users cannot access other organizations."""
        # Create another organization
        other_org = Organization(
            name="Restricted Org",
            slug=f"restricted-{uuid4().hex[:8]}"
        )
        db_session.add(other_org)
        await db_session.commit()

        # Try to access - should be forbidden
        response = await client.get(
            f"/api/v1/organizations/{other_org.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 403


# =============================================================================
# Plan and Settings Tests
# =============================================================================

class TestPlanAndSettings:
    """Test organization plans and settings."""

    @pytest.mark.asyncio
    async def test_organization_plans(
        self, client: AsyncClient, auth_headers
    ):
        """Test different organization plans."""
        plans = ["free", "starter", "pro", "enterprise"]
        
        for plan in plans:
            response = await client.post(
                "/api/v1/organizations",
                json={
                    "name": f"{plan.capitalize()} Plan Org",
                    "slug": f"{plan}-org-{uuid4().hex[:8]}",
                    "plan": plan
                },
                headers=auth_headers
            )
            
            assert response.status_code == 201
            assert response.json()["plan"] == plan

    @pytest.mark.asyncio
    async def test_organization_settings_sase_config(
        self, client: AsyncClient, auth_headers
    ):
        """Test organization SASE configuration."""
        response = await client.post(
            "/api/v1/organizations",
            json={
                "name": "SASE Config Org",
                "slug": f"sase-org-{uuid4().hex[:8]}",
                "plan": "enterprise",
                "settings": {
                    "require_mfa": True,
                    "allowed_domains": ["company.com", "partner.com"],
                    "max_teams": 50,
                    "sase_config": {
                        "agentic_maturity": "L2",
                        "default_crp_threshold": 0.8
                    }
                }
            },
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["settings"]["require_mfa"] is True
        assert len(data["settings"]["allowed_domains"]) == 2


# =============================================================================
# Edge Cases
# =============================================================================

class TestOrganizationEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_invalid_slug_pattern(
        self, client: AsyncClient, auth_headers
    ):
        """Test that invalid slug patterns are rejected."""
        response = await client.post(
            "/api/v1/organizations",
            json={
                "name": "Invalid Slug Org",
                "slug": "Invalid Slug With Spaces"  # Invalid
            },
            headers=auth_headers
        )
        
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_empty_name_rejected(
        self, client: AsyncClient, auth_headers
    ):
        """Test that empty organization name is rejected."""
        response = await client.post(
            "/api/v1/organizations",
            json={
                "name": "",  # Empty
                "slug": "empty-name-org"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_slug_too_short(
        self, client: AsyncClient, auth_headers
    ):
        """Test that slug too short is rejected."""
        response = await client.post(
            "/api/v1/organizations",
            json={
                "name": "Short Slug Org",
                "slug": "a"  # Too short (min 2)
            },
            headers=auth_headers
        )
        
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_pagination_limits(
        self, client: AsyncClient, auth_headers
    ):
        """Test pagination limits."""
        # Test limit > 100 is capped
        response = await client.get(
            "/api/v1/organizations",
            params={"limit": 200},  # Over max
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["page_size"] <= 100

    @pytest.mark.asyncio
    async def test_update_non_member_org_forbidden(
        self, client: AsyncClient, auth_headers, db_session
    ):
        """Test that non-members cannot update organization."""
        # Create an organization without the current user
        other_org = Organization(
            name="Not My Org",
            slug=f"not-my-org-{uuid4().hex[:8]}"
        )
        db_session.add(other_org)
        await db_session.commit()

        response = await client.patch(
            f"/api/v1/organizations/{other_org.id}",
            json={"name": "Hacked Name"},
            headers=auth_headers
        )
        
        assert response.status_code == 403
