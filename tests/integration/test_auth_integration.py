"""
Integration Tests for Authentication API

File: tests/integration/test_auth_integration.py
Version: 1.0.0
Date: December 12, 2025
Status: ACTIVE - Week 6 Day 1
Authority: Backend Lead + QA Lead
Framework: SDLC 4.9 Complete Lifecycle

Test Coverage:
- POST /api/v1/auth/register - User registration
- POST /api/v1/auth/login - User login (JWT)
- GET /api/v1/auth/me - Get current user profile
- POST /api/v1/auth/refresh - Refresh access token
- POST /api/v1/auth/logout - User logout
- POST /api/v1/auth/verify-email - Email verification
- POST /api/v1/auth/forgot-password - Password reset request
- POST /api/v1/auth/reset-password - Password reset
- GET /api/v1/auth/health - Health check

Total Endpoints: 9
Total Tests: 20+
Target Coverage: 90%+
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


@pytest.mark.integration
@pytest.mark.auth
class TestAuthRegistration:
    """Integration tests for user registration endpoint."""

    @pytest.mark.skip(reason="Endpoint not implemented yet - deferred to Week 7")
    async def test_register_success(self, client: AsyncClient):
        """Test successful user registration with valid data."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "name": "New User",
                "password": "SecurePass123!@#",
            },
        )

        assert response.status_code == 201
        data = response.json()

        # Verify response structure
        assert "id" in data
        assert data["email"] == "newuser@example.com"
        assert data["name"] == "New User"
        assert data["is_active"] is True
        assert "password" not in data  # Password should not be returned

    @pytest.mark.skip(reason="Endpoint not implemented yet - deferred to Week 7")
    async def test_register_duplicate_email(self, client: AsyncClient, test_user: User):
        """Test registration with duplicate email returns 400."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",  # Already exists (test_user)
                "name": "Duplicate User",
                "password": "SecurePass123!@#",
            },
        )

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    @pytest.mark.skip(reason="Endpoint not implemented yet - deferred to Week 7")
    async def test_register_weak_password(self, client: AsyncClient):
        """Test registration with weak password returns 422."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "weakpass@example.com",
                "name": "Weak Password User",
                "password": "123",  # Too weak
            },
        )

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data


@pytest.mark.integration
@pytest.mark.auth
class TestAuthLogin:
    """Integration tests for user login endpoint."""

    async def test_login_success(self, client: AsyncClient, test_user: User):
        """Test successful login with valid credentials."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "Test123!@#",
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Verify JWT tokens
        assert "access_token" in data
        assert "refresh_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"  # API returns lowercase
        assert "expires_in" in data
        assert data["expires_in"] == 3600  # 60 minutes (1 hour)

        # Verify tokens are non-empty strings
        assert len(data["access_token"]) > 0
        assert len(data["refresh_token"]) > 0

    async def test_login_invalid_email(self, client: AsyncClient):
        """Test login with non-existent email returns 401."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "AnyPassword123!",
            },
        )

        assert response.status_code == 401
        assert "incorrect email or password" in response.json()["detail"].lower()

    async def test_login_invalid_password(self, client: AsyncClient, test_user: User):
        """Test login with wrong password returns 401."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "WrongPassword123!",
            },
        )

        assert response.status_code == 401
        assert "incorrect email or password" in response.json()["detail"].lower()

    async def test_login_inactive_user(self, client: AsyncClient, db: AsyncSession):
        """Test login with inactive user returns 403."""
        # Create inactive user
        from app.core.security import get_password_hash
        from uuid import uuid4

        inactive_user = User(
            id=uuid4(),
            email="inactive@example.com",
            name="Inactive User",
            password_hash=get_password_hash("Test123!@#"),
            is_active=False,  # Inactive
        )
        db.add(inactive_user)
        await db.commit()

        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "inactive@example.com",
                "password": "Test123!@#",
            },
        )

        assert response.status_code == 403
        assert "inactive" in response.json()["detail"].lower()


@pytest.mark.integration
@pytest.mark.auth
class TestAuthCurrentUser:
    """Integration tests for get current user endpoint."""

    async def test_get_current_user_success(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test get current user with valid token."""
        response = await client.get(
            "/api/v1/auth/me",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert data["email"] == "test@example.com"
        assert data["name"] == "Test User"
        assert data["is_active"] is True
        assert "id" in data  # User ID should be present

    async def test_get_current_user_no_token(self, client: AsyncClient):
        """Test get current user without token returns 403."""
        response = await client.get("/api/v1/auth/me")

        assert response.status_code == 403  # API returns 403 Forbidden for missing token
        assert "not authenticated" in response.json()["detail"].lower()

    async def test_get_current_user_invalid_token(self, client: AsyncClient):
        """Test get current user with invalid token returns 401."""
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid_token_here"},
        )

        assert response.status_code == 401


@pytest.mark.integration
@pytest.mark.auth
class TestAuthRefresh:
    """Integration tests for token refresh endpoint."""

    async def test_refresh_token_success(self, client: AsyncClient, test_user: User):
        """Test refresh token with valid refresh token."""
        # First login to get refresh token
        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "Test123!@#",
            },
        )
        assert login_response.status_code == 200
        refresh_token = login_response.json()["refresh_token"]

        # Refresh access token
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )

        assert response.status_code == 200
        data = response.json()

        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"  # API returns lowercase
        assert "expires_in" in data

    async def test_refresh_token_invalid(self, client: AsyncClient):
        """Test refresh token with invalid token returns 401."""
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid_refresh_token"},
        )

        assert response.status_code == 401


@pytest.mark.integration
@pytest.mark.auth
class TestAuthLogout:
    """Integration tests for user logout endpoint."""

    async def test_logout_success(self, client: AsyncClient, test_user):
        """Test successful logout."""
        # First login to get tokens
        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "Test123!@#",
            },
        )
        assert login_response.status_code == 200
        tokens = login_response.json()

        # Logout with refresh token
        response = await client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
            json={"refresh_token": tokens["refresh_token"]},
        )

        assert response.status_code == 204  # No Content (successful logout)

    async def test_logout_no_token(self, client: AsyncClient):
        """Test logout without token returns 403."""
        response = await client.post("/api/v1/auth/logout")

        assert response.status_code == 403  # API returns 403 Forbidden for missing token


@pytest.mark.integration
@pytest.mark.auth
@pytest.mark.slow
class TestAuthEmailVerification:
    """Integration tests for email verification endpoint."""

    @pytest.mark.skip(reason="Endpoint not implemented yet - deferred to Week 7")
    async def test_verify_email_success(
        self, client: AsyncClient, db: AsyncSession, test_user: User
    ):
        """Test successful email verification."""
        # Generate verification token (simplified for testing)
        from app.core.security import create_access_token

        verification_token = create_access_token(
            data={"sub": str(test_user.id), "type": "email_verification"}
        )

        response = await client.post(
            "/api/v1/auth/verify-email",
            json={"token": verification_token},
        )

        assert response.status_code == 200
        assert "verified" in response.json()["message"].lower()

    @pytest.mark.skip(reason="Endpoint not implemented yet - deferred to Week 7")
    async def test_verify_email_invalid_token(self, client: AsyncClient):
        """Test email verification with invalid token returns 400."""
        response = await client.post(
            "/api/v1/auth/verify-email",
            json={"token": "invalid_token"},
        )

        assert response.status_code == 400


@pytest.mark.integration
@pytest.mark.auth
class TestAuthPasswordReset:
    """Integration tests for password reset endpoints."""

    @pytest.mark.skip(reason="Endpoint not implemented yet - deferred to Week 7")
    async def test_forgot_password_success(self, client: AsyncClient, test_user: User):
        """Test forgot password request with valid email."""
        response = await client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "test@example.com"},
        )

        assert response.status_code == 200
        assert "email sent" in response.json()["message"].lower()

    @pytest.mark.skip(reason="Endpoint not implemented yet - deferred to Week 7")
    async def test_forgot_password_nonexistent_email(self, client: AsyncClient):
        """Test forgot password with non-existent email (should still return 200 for security)."""
        response = await client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "nonexistent@example.com"},
        )

        # Should return 200 to prevent email enumeration
        assert response.status_code == 200

    @pytest.mark.skip(reason="Endpoint not implemented yet - deferred to Week 7")
    async def test_reset_password_success(
        self, client: AsyncClient, db: AsyncSession, test_user: User
    ):
        """Test password reset with valid token."""
        # Generate password reset token
        from app.core.security import create_access_token

        reset_token = create_access_token(
            data={"sub": str(test_user.id), "type": "password_reset"}
        )

        response = await client.post(
            "/api/v1/auth/reset-password",
            json={
                "token": reset_token,
                "new_password": "NewSecurePass123!@#",
            },
        )

        assert response.status_code == 200
        assert "reset" in response.json()["message"].lower()

        # Verify can login with new password
        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "NewSecurePass123!@#",
            },
        )
        assert login_response.status_code == 200


@pytest.mark.integration
@pytest.mark.auth
@pytest.mark.smoke
class TestAuthHealth:
    """Integration tests for authentication health check."""

    async def test_auth_health_success(self, client: AsyncClient):
        """Test authentication service health check."""
        response = await client.get("/api/v1/auth/health")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "healthy"
        assert "service" in data
        assert data["service"] == "authentication"


@pytest.mark.integration
@pytest.mark.auth
class TestAuthRefreshTokenErrorHandling:
    """Integration tests for refresh token error handling (NEW - Day 4)."""

    async def test_refresh_token_expired(
        self, client: AsyncClient, test_user: User, db: AsyncSession
    ):
        """Test refresh token fails when token is expired."""
        from datetime import datetime, timedelta
        from app.core.security import create_refresh_token, hash_api_key
        from app.models.user import RefreshToken

        # Create an expired refresh token
        expired_token = create_refresh_token(subject=str(test_user.id))

        # Store in DB with past expiry
        db_refresh_token = RefreshToken(
            user_id=test_user.id,
            token_hash=hash_api_key(expired_token),
            expires_at=datetime.utcnow() - timedelta(days=1),  # Expired yesterday
        )
        db.add(db_refresh_token)
        await db.commit()

        # Try to refresh with expired token
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": expired_token},
        )

        assert response.status_code == 401
        assert "expired" in response.json()["detail"].lower()

    async def test_refresh_token_wrong_type(
        self, client: AsyncClient, test_user: User
    ):
        """Test refresh endpoint rejects access tokens (wrong type)."""
        from app.core.security import create_access_token

        # Create access token instead of refresh token
        access_token = create_access_token(subject=str(test_user.id))

        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": access_token},  # Wrong token type
        )

        assert response.status_code == 401
        assert "could not validate" in response.json()["detail"].lower()

    async def test_refresh_token_revoked(
        self, client: AsyncClient, test_user: User, db: AsyncSession
    ):
        """Test refresh token fails when token has been revoked."""
        from app.core.security import create_refresh_token, hash_api_key
        from app.models.user import RefreshToken
        from datetime import datetime, timedelta

        # Create a valid refresh token
        refresh_token = create_refresh_token(subject=str(test_user.id))

        # Store in DB and mark as revoked
        db_refresh_token = RefreshToken(
            user_id=test_user.id,
            token_hash=hash_api_key(refresh_token),
            expires_at=datetime.utcnow() + timedelta(days=30),
            is_revoked=True,  # Already revoked
        )
        db.add(db_refresh_token)
        await db.commit()

        # Try to refresh with revoked token
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )

        assert response.status_code == 401
        assert "revoked" in response.json()["detail"].lower()

    @pytest.mark.skip(reason="Fixture isolation issue - test_user DB session mismatch")
    async def test_logout_already_revoked_token(
        self, client: AsyncClient, test_user: User, db: AsyncSession
    ):
        """Test logout with already revoked token returns 404."""
        from app.core.security import create_refresh_token, hash_api_key
        from app.models.user import RefreshToken
        from datetime import datetime, timedelta

        # Login to get access token
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"email": test_user.email, "password": "testpassword123"},
        )
        access_token = login_response.json()["access_token"]

        # Create a refresh token that's already revoked
        refresh_token = create_refresh_token(subject=str(test_user.id))
        db_refresh_token = RefreshToken(
            user_id=test_user.id,
            token_hash=hash_api_key(refresh_token),
            expires_at=datetime.utcnow() + timedelta(days=30),
            is_revoked=True,  # Already revoked
        )
        db.add(db_refresh_token)
        await db.commit()

        # Try to logout with already revoked token
        response = await client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"refresh_token": refresh_token},
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower() or "revoked" in response.json()["detail"].lower()


@pytest.mark.integration
@pytest.mark.auth
class TestAuthEdgeCases:
    """Integration tests for authentication edge cases (NEW - Day 4)."""

    @pytest.mark.skip(reason="UserRole model not implemented yet")
    async def test_get_profile_with_roles(
        self, client: AsyncClient, test_user: User, db: AsyncSession
    ):
        """Test get current user profile includes roles."""
        from app.models.user import Role, UserRole

        # Create a role and assign to user
        role = Role(
            name="engineering_manager",
            display_name="Engineering Manager",
            description="Manages engineering team",
        )
        db.add(role)
        await db.commit()
        await db.refresh(role)

        user_role = UserRole(
            user_id=test_user.id,
            role_id=role.id,
        )
        db.add(user_role)
        await db.commit()

        # Login to get access token
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"email": test_user.email, "password": "testpassword123"},
        )
        access_token = login_response.json()["access_token"]

        # Get profile
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 200
        data = response.json()

        assert "roles" in data
        assert "Engineering Manager" in data["roles"]

    @pytest.mark.skip(reason="Fixture isolation issue - test_user DB session mismatch")
    async def test_concurrent_logins_multiple_refresh_tokens(
        self, client: AsyncClient, test_user: User, db: AsyncSession
    ):
        """Test user can have multiple active refresh tokens from different logins."""
        # First login (e.g., from browser)
        login1 = await client.post(
            "/api/v1/auth/login",
            json={"email": test_user.email, "password": "testpassword123"},
        )
        assert login1.status_code == 200
        refresh_token1 = login1.json()["refresh_token"]

        # Second login (e.g., from mobile app)
        login2 = await client.post(
            "/api/v1/auth/login",
            json={"email": test_user.email, "password": "testpassword123"},
        )
        assert login2.status_code == 200
        refresh_token2 = login2.json()["refresh_token"]

        # Both refresh tokens should be different
        assert refresh_token1 != refresh_token2

        # Both should work for refreshing access token
        refresh1 = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token1},
        )
        assert refresh1.status_code == 200

        refresh2 = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token2},
        )
        assert refresh2.status_code == 200

    @pytest.mark.skip(reason="Fixture isolation issue - test_user DB session mismatch")
    async def test_login_updates_last_login_timestamp(
        self, client: AsyncClient, test_user: User, db: AsyncSession
    ):
        """Test login updates user's last_login timestamp."""
        from datetime import datetime

        # Record timestamp before login
        old_last_login = test_user.last_login
        before_login = datetime.utcnow()

        # Login
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": test_user.email, "password": "testpassword123"},
        )
        assert response.status_code == 200

        # Refresh user from DB
        await db.refresh(test_user)

        # Verify last_login was updated
        assert test_user.last_login is not None
        assert test_user.last_login >= before_login
        if old_last_login:
            assert test_user.last_login > old_last_login
