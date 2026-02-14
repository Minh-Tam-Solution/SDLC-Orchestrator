"""
Integration Tests for Organization Invitations API
SDLC Orchestrator - Sprint 146 (Organization Access Control)

SDLC Stage: 04 - BUILD
Sprint: 146 - Organization Access Control System
Framework: SDLC 6.0.5
Reference: ADR-047-Organization-Invitation-System-Architecture

Purpose:
Test Organization Invitations API endpoints including:
- Send invitation (with RBAC, rate limiting)
- Resend invitation (new token generation)
- Accept/Decline invitation
- List/Cancel invitations
- Direct member addition

Security Tests:
- SHA256 token hashing (never store raw)
- Rate limiting (50/hour per org)
- RBAC (owner can invite admin, admin can invite member only)
- Email verification (user email must match invited email)

Test Coverage Target: 90%+
"""

import pytest
import pytest_asyncio
from datetime import datetime, timezone
from httpx import AsyncClient
from uuid import uuid4

from app.models.organization import Organization, UserOrganization
from app.models.organization_invitation import OrganizationInvitation
from app.models.user import User
from app.core.security import get_password_hash


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest_asyncio.fixture
async def test_org_with_owner(db_session):
    """Create a test organization with an owner user."""
    # Create organization
    org = Organization(
        name="Test Org for Invitations",
        slug=f"test-org-inv-{uuid4().hex[:8]}",
        plan="pro",
        settings={
            "require_mfa": False,
            "allowed_domains": ["test.com"],
        }
    )
    db_session.add(org)
    await db_session.flush()

    # Create owner user
    owner = User(
        email=f"owner-{uuid4().hex[:8]}@test.com",
        password_hash=get_password_hash("password123"),
        full_name="Organization Owner",
        organization_id=org.id,
        is_active=True,
        is_verified=True
    )
    db_session.add(owner)
    await db_session.flush()

    # Create owner membership
    membership = UserOrganization(
        user_id=owner.id,
        organization_id=org.id,
        role="owner",
        joined_at=datetime.now(timezone.utc)
    )
    db_session.add(membership)
    await db_session.commit()
    await db_session.refresh(org)
    await db_session.refresh(owner)

    return {"org": org, "owner": owner}


@pytest_asyncio.fixture
async def owner_auth_headers(client: AsyncClient, test_org_with_owner):
    """Get authentication headers for the organization owner."""
    owner = test_org_with_owner["owner"]
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": owner.email, "password": "password123"},
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    data = response.json()
    return {"Authorization": f"Bearer {data['access_token']}"}


@pytest_asyncio.fixture
async def test_org_with_admin(db_session, test_org_with_owner):
    """Create an admin user in the test organization."""
    org = test_org_with_owner["org"]

    # Create admin user
    admin = User(
        email=f"admin-{uuid4().hex[:8]}@test.com",
        password_hash=get_password_hash("password123"),
        full_name="Organization Admin",
        organization_id=org.id,
        is_active=True,
        is_verified=True
    )
    db_session.add(admin)
    await db_session.flush()

    # Create admin membership
    membership = UserOrganization(
        user_id=admin.id,
        organization_id=org.id,
        role="admin",
        joined_at=datetime.now(timezone.utc)
    )
    db_session.add(membership)
    await db_session.commit()
    await db_session.refresh(admin)

    return {**test_org_with_owner, "admin": admin}


@pytest_asyncio.fixture
async def org_admin_auth_headers(client: AsyncClient, test_org_with_admin):
    """Get authentication headers for the organization admin."""
    admin = test_org_with_admin["admin"]
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": admin.email, "password": "password123"},
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    data = response.json()
    return {"Authorization": f"Bearer {data['access_token']}"}


@pytest_asyncio.fixture
async def existing_user(db_session):
    """Create an existing user that can be added directly to org."""
    user = User(
        email=f"existing-{uuid4().hex[:8]}@example.com",
        password_hash=get_password_hash("password123"),
        full_name="Existing User",
        is_active=True,
        is_verified=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


# =============================================================================
# Send Invitation Tests
# =============================================================================

class TestSendInvitation:
    """Test sending organization invitations."""

    @pytest.mark.asyncio
    async def test_owner_send_invitation_success(
        self, client: AsyncClient, owner_auth_headers, test_org_with_owner
    ):
        """Test owner can send invitation to join organization."""
        org = test_org_with_owner["org"]

        response = await client.post(
            f"/api/v1/organizations/{org.id}/invitations",
            json={
                "invited_email": "newuser@example.com",
                "role": "member",
                "message": "Welcome to our team!"
            },
            headers=owner_auth_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["invited_email"] == "newuser@example.com"
        assert data["role"] == "member"
        assert data["status"] == "pending"
        assert "invitation_id" in data or "id" in data
        assert "expires_at" in data

    @pytest.mark.asyncio
    async def test_owner_can_invite_admin(
        self, client: AsyncClient, owner_auth_headers, test_org_with_owner
    ):
        """Test owner can invite users with admin role."""
        org = test_org_with_owner["org"]

        response = await client.post(
            f"/api/v1/organizations/{org.id}/invitations",
            json={
                "invited_email": "newadmin@example.com",
                "role": "admin"
            },
            headers=owner_auth_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["role"] == "admin"

    @pytest.mark.asyncio
    async def test_admin_can_invite_member(
        self, client: AsyncClient, org_admin_auth_headers, test_org_with_admin
    ):
        """Test admin can invite users with member role."""
        org = test_org_with_admin["org"]

        response = await client.post(
            f"/api/v1/organizations/{org.id}/invitations",
            json={
                "invited_email": "newmember@example.com",
                "role": "member"
            },
            headers=org_admin_auth_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["role"] == "member"

    @pytest.mark.asyncio
    async def test_admin_cannot_invite_admin(
        self, client: AsyncClient, org_admin_auth_headers, test_org_with_admin
    ):
        """Test admin cannot invite users with admin role (only owner can)."""
        org = test_org_with_admin["org"]

        response = await client.post(
            f"/api/v1/organizations/{org.id}/invitations",
            json={
                "invited_email": "newadmin@example.com",
                "role": "admin"
            },
            headers=org_admin_auth_headers
        )

        assert response.status_code == 403
        assert "owner" in response.json()["detail"]["message"].lower()

    @pytest.mark.asyncio
    async def test_cannot_invite_owner_role(
        self, client: AsyncClient, owner_auth_headers, test_org_with_owner
    ):
        """Test cannot invite with owner role (CTO constraint)."""
        org = test_org_with_owner["org"]

        response = await client.post(
            f"/api/v1/organizations/{org.id}/invitations",
            json={
                "invited_email": "wannabe-owner@example.com",
                "role": "owner"  # Invalid - cannot invite as owner
            },
            headers=owner_auth_headers
        )

        # Should be rejected at validation level (422) or forbidden (403)
        assert response.status_code in [403, 422]


# =============================================================================
# List Invitations Tests
# =============================================================================

class TestListInvitations:
    """Test listing organization invitations."""

    @pytest.mark.asyncio
    async def test_owner_can_list_invitations(
        self, client: AsyncClient, owner_auth_headers, test_org_with_owner
    ):
        """Test owner can list all invitations."""
        org = test_org_with_owner["org"]

        # First send some invitations
        for i in range(3):
            await client.post(
                f"/api/v1/organizations/{org.id}/invitations",
                json={"invited_email": f"user{i}@example.com", "role": "member"},
                headers=owner_auth_headers
            )

        # List invitations
        response = await client.get(
            f"/api/v1/organizations/{org.id}/invitations",
            headers=owner_auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 3

    @pytest.mark.asyncio
    async def test_filter_invitations_by_status(
        self, client: AsyncClient, owner_auth_headers, test_org_with_owner
    ):
        """Test filtering invitations by status."""
        org = test_org_with_owner["org"]

        # Send invitation
        await client.post(
            f"/api/v1/organizations/{org.id}/invitations",
            json={"invited_email": "filtertest@example.com", "role": "member"},
            headers=owner_auth_headers
        )

        # Filter by pending status
        response = await client.get(
            f"/api/v1/organizations/{org.id}/invitations",
            params={"status": "pending"},
            headers=owner_auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        for invitation in data:
            assert invitation["status"] == "pending"


# =============================================================================
# Direct Member Addition Tests
# =============================================================================

class TestDirectMemberAddition:
    """Test direct member addition (bypass invitation)."""

    @pytest.mark.asyncio
    async def test_owner_add_member_directly(
        self, client: AsyncClient, owner_auth_headers, test_org_with_owner, existing_user
    ):
        """Test owner can add existing user directly."""
        org = test_org_with_owner["org"]

        response = await client.post(
            f"/api/v1/organizations/{org.id}/members",
            json={
                "user_email": existing_user.email,
                "role": "member"
            },
            headers=owner_auth_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert str(data["user_id"]) == str(existing_user.id)
        assert data["role"] == "member"
        assert data["organization_name"] == org.name

    @pytest.mark.asyncio
    async def test_owner_can_add_admin_directly(
        self, client: AsyncClient, owner_auth_headers, test_org_with_owner, db_session
    ):
        """Test owner can add user with admin role directly."""
        org = test_org_with_owner["org"]

        # Create another user
        user = User(
            email=f"directadmin-{uuid4().hex[:8]}@example.com",
            password_hash=get_password_hash("password123"),
            full_name="Direct Admin User",
            is_active=True,
            is_verified=True
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        response = await client.post(
            f"/api/v1/organizations/{org.id}/members",
            json={
                "user_email": user.email,
                "role": "admin"
            },
            headers=owner_auth_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["role"] == "admin"

    @pytest.mark.asyncio
    async def test_admin_cannot_add_admin_directly(
        self, client: AsyncClient, org_admin_auth_headers, test_org_with_admin, existing_user
    ):
        """Test admin cannot add user with admin role (only owner can)."""
        org = test_org_with_admin["org"]

        response = await client.post(
            f"/api/v1/organizations/{org.id}/members",
            json={
                "user_email": existing_user.email,
                "role": "admin"
            },
            headers=org_admin_auth_headers
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_add_non_existent_user_fails(
        self, client: AsyncClient, owner_auth_headers, test_org_with_owner
    ):
        """Test adding non-existent user fails with 404."""
        org = test_org_with_owner["org"]

        response = await client.post(
            f"/api/v1/organizations/{org.id}/members",
            json={
                "user_email": "nonexistent@example.com",
                "role": "member"
            },
            headers=owner_auth_headers
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_add_already_member_fails(
        self, client: AsyncClient, owner_auth_headers, test_org_with_owner, existing_user, db_session
    ):
        """Test adding user who is already a member fails with 409."""
        org = test_org_with_owner["org"]

        # First add the user
        membership = UserOrganization(
            user_id=existing_user.id,
            organization_id=org.id,
            role="member",
            joined_at=datetime.utcnow()
        )
        db_session.add(membership)
        await db_session.commit()

        # Try to add again
        response = await client.post(
            f"/api/v1/organizations/{org.id}/members",
            json={
                "user_email": existing_user.email,
                "role": "member"
            },
            headers=owner_auth_headers
        )

        assert response.status_code == 409
        assert "already" in response.json()["detail"].lower()


# =============================================================================
# Cancel Invitation Tests
# =============================================================================

class TestCancelInvitation:
    """Test canceling invitations."""

    @pytest.mark.asyncio
    async def test_owner_cancel_invitation(
        self, client: AsyncClient, owner_auth_headers, test_org_with_owner
    ):
        """Test owner can cancel pending invitation."""
        org = test_org_with_owner["org"]

        # Send invitation
        send_response = await client.post(
            f"/api/v1/organizations/{org.id}/invitations",
            json={"invited_email": "tocancel@example.com", "role": "member"},
            headers=owner_auth_headers
        )
        assert send_response.status_code == 201
        invitation_id = send_response.json().get("invitation_id") or send_response.json().get("id")

        # Cancel invitation
        response = await client.delete(
            f"/api/v1/org-invitations/{invitation_id}",
            headers=owner_auth_headers
        )

        assert response.status_code == 204


# =============================================================================
# Permission & RBAC Tests
# =============================================================================

class TestRBACPermissions:
    """Test RBAC enforcement for invitations."""

    @pytest.mark.asyncio
    async def test_non_member_cannot_send_invitation(
        self, client: AsyncClient, auth_headers, test_org_with_owner
    ):
        """Test non-member cannot send invitations to org."""
        org = test_org_with_owner["org"]

        response = await client.post(
            f"/api/v1/organizations/{org.id}/invitations",
            json={"invited_email": "test@example.com", "role": "member"},
            headers=auth_headers  # Regular test user, not member of org
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_non_member_cannot_list_invitations(
        self, client: AsyncClient, auth_headers, test_org_with_owner
    ):
        """Test non-member cannot list org invitations."""
        org = test_org_with_owner["org"]

        response = await client.get(
            f"/api/v1/organizations/{org.id}/invitations",
            headers=auth_headers
        )

        assert response.status_code == 403


# =============================================================================
# Validation Tests
# =============================================================================

class TestInvitationValidation:
    """Test input validation for invitations."""

    @pytest.mark.asyncio
    async def test_invalid_email_rejected(
        self, client: AsyncClient, owner_auth_headers, test_org_with_owner
    ):
        """Test invalid email format is rejected."""
        org = test_org_with_owner["org"]

        response = await client.post(
            f"/api/v1/organizations/{org.id}/invitations",
            json={"invited_email": "not-an-email", "role": "member"},
            headers=owner_auth_headers
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_invalid_role_rejected(
        self, client: AsyncClient, owner_auth_headers, test_org_with_owner
    ):
        """Test invalid role is rejected."""
        org = test_org_with_owner["org"]

        response = await client.post(
            f"/api/v1/organizations/{org.id}/invitations",
            json={"invited_email": "test@example.com", "role": "superadmin"},
            headers=owner_auth_headers
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_missing_email_rejected(
        self, client: AsyncClient, owner_auth_headers, test_org_with_owner
    ):
        """Test missing email is rejected."""
        org = test_org_with_owner["org"]

        response = await client.post(
            f"/api/v1/organizations/{org.id}/invitations",
            json={"role": "member"},  # Missing invited_email
            headers=owner_auth_headers
        )

        assert response.status_code == 422
