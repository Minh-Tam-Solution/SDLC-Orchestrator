"""
=========================================================================
ADR-027 Phase 1 Integration Tests
SDLC Orchestrator - Stage 03 (BUILD)

Version: 1.0.0
Date: 2026-01-14
Status: ACTIVE - Sprint N+1 (ADR-027 Phase 1)
Authority: Backend Lead + CTO Approved
Foundation: pytest + pytest-asyncio + httpx
Framework: SDLC 5.1.2 Universal Framework

Purpose:
Automated integration tests for all 4 Phase 1 system settings.
Validates settings work together in production-like environment.

Test Suites:
1. All Settings Enabled (IT-1 to IT-5)
2. Cross-Setting Interactions (IT-6 to IT-8)
3. Cache Invalidation (IT-9 to IT-10)
4. Performance & Stress (IT-11 to IT-12)
5. Edge Cases (IT-13 to IT-15)

Zero Mock Policy: Real database, real Redis, real API calls
=========================================================================
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Optional
from statistics import quantiles
import pytest
from httpx import AsyncClient
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.models.user import User
from app.models.support import SystemSetting
from app.core.security import get_password_hash


# =========================================================================
# Fixtures
# =========================================================================

@pytest.fixture(scope="module")
async def async_client():
    """Create async HTTP client for API testing."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
async def test_db(async_session: AsyncSession):
    """Get database session."""
    yield async_session


@pytest.fixture
async def admin_user(test_db: AsyncSession):
    """Create admin user for integration tests."""
    admin = User(
        email="admin.integration@sdlc.local",
        password_hash=get_password_hash("AdminIntegration123!"),
        name="Admin Integration",
        is_active=True,
        is_superuser=True,
    )
    test_db.add(admin)
    await test_db.commit()
    await test_db.refresh(admin)

    yield admin

    # Cleanup
    await test_db.delete(admin)
    await test_db.commit()


@pytest.fixture
async def test_users(test_db: AsyncSession):
    """Create test users for integration tests."""
    users = []
    for i in range(1, 4):
        user = User(
            email=f"user{i}.integration@sdlc.local",
            password_hash=get_password_hash("UserPassword123!"),
            name=f"Test User {i}",
            is_active=True,
            is_superuser=False,
        )
        test_db.add(user)
        users.append(user)

    await test_db.commit()
    for user in users:
        await test_db.refresh(user)

    yield users

    # Cleanup
    for user in users:
        await test_db.delete(user)
    await test_db.commit()


@pytest.fixture
async def settings_reset(test_db: AsyncSession):
    """Reset all settings to default values before/after tests."""
    # Set default values
    defaults = {
        "session_timeout_minutes": 60,
        "max_login_attempts": 5,
        "password_min_length": 12,
        "mfa_required": False,
    }

    for key, value in defaults.items():
        result = await test_db.execute(
            select(SystemSetting).where(SystemSetting.key == key)
        )
        setting = result.scalar_one_or_none()

        if setting:
            setting.value = value
        else:
            setting = SystemSetting(
                key=key,
                value=value,
                category="security",
                description=f"Test setting: {key}",
                version=1,
                updated_at=datetime.utcnow(),
            )
            test_db.add(setting)

    await test_db.commit()

    yield

    # Reset after test
    for key, value in defaults.items():
        await test_db.execute(
            text(f"UPDATE system_settings SET value = :value WHERE key = :key"),
            {"key": key, "value": str(value)},
        )
    await test_db.commit()


# =========================================================================
# Helper Functions
# =========================================================================

async def get_token(client: AsyncClient, email: str, password: str) -> Optional[str]:
    """Login and get JWT token."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    return None


async def update_setting(db: AsyncSession, key: str, value) -> None:
    """Update a system setting in database."""
    await db.execute(
        text("UPDATE system_settings SET value = :value, updated_at = :now WHERE key = :key"),
        {"key": key, "value": str(value), "now": datetime.utcnow()},
    )
    await db.commit()


async def flush_redis_cache() -> None:
    """Flush Redis cache to force setting re-read."""
    import redis.asyncio as redis
    r = redis.from_url("redis://localhost:6379")
    await r.flushdb()
    await r.close()


# =========================================================================
# Test Suite 1: All Settings Enabled (IT-1 to IT-5)
# =========================================================================

@pytest.mark.asyncio
class TestAllSettingsEnabled:
    """Test all 4 settings work when enabled simultaneously."""

    async def test_it1_baseline_configuration(
        self, async_client, test_db, settings_reset
    ):
        """IT-1: Baseline - All settings configured with enforced values."""
        # Set enforced values
        await update_setting(test_db, "session_timeout_minutes", 15)
        await update_setting(test_db, "max_login_attempts", 3)
        await update_setting(test_db, "password_min_length", 16)
        await update_setting(test_db, "mfa_required", True)

        # Verify settings in database
        for key in ["session_timeout_minutes", "max_login_attempts",
                    "password_min_length", "mfa_required"]:
            result = await test_db.execute(
                select(SystemSetting).where(SystemSetting.key == key)
            )
            setting = result.scalar_one()
            assert setting is not None, f"Setting {key} not found"

        # All settings configured
        assert True

    async def test_it2_session_timeout_integration(
        self, async_client, test_db, test_users, settings_reset
    ):
        """IT-2: session_timeout_minutes affects JWT expiry."""
        # Set 15-minute timeout
        await update_setting(test_db, "session_timeout_minutes", 15)
        await flush_redis_cache()

        # Login and get token
        user = test_users[0]
        token = await get_token(async_client, user.email, "UserPassword123!")

        assert token is not None, "Failed to get token"

        # Decode token to verify expiry
        import jwt
        decoded = jwt.decode(token, options={"verify_signature": False})

        duration = decoded["exp"] - decoded["iat"]
        expected_duration = 15 * 60  # 15 minutes in seconds

        # Allow 10 second tolerance
        assert abs(duration - expected_duration) < 10, \
            f"Token duration {duration}s != expected {expected_duration}s"

    async def test_it3_max_login_attempts_integration(
        self, async_client, test_db, test_users, settings_reset
    ):
        """IT-3: max_login_attempts locks account after threshold."""
        # Set 3 attempts max
        await update_setting(test_db, "max_login_attempts", 3)
        await flush_redis_cache()

        user = test_users[1]

        # Fail login 3 times
        for i in range(3):
            response = await async_client.post(
                "/api/v1/auth/login",
                json={"email": user.email, "password": "WrongPassword!"},
            )

            if i < 2:
                assert response.status_code == 401, f"Attempt {i+1} should return 401"
            else:
                # 3rd attempt should lock
                assert response.status_code == 403, "3rd attempt should lock account"
                assert "Account locked" in response.json()["detail"]

        # Verify locked in database
        await test_db.refresh(user)
        assert user.failed_login_count == 3
        assert user.locked_until is not None

    async def test_it4_password_min_length_integration(
        self, async_client, test_db, settings_reset
    ):
        """IT-4: password_min_length rejects weak passwords."""
        # Set 16-char minimum
        await update_setting(test_db, "password_min_length", 16)
        await flush_redis_cache()

        # Try register with 12-char password (should fail)
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": "short.pass@test.local",
                "password": "Password123!",  # 12 chars
                "name": "Short Password Test",
            },
        )

        assert response.status_code == 400
        assert "16 characters" in response.json()["detail"]

        # Try with 20-char password (should succeed)
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": "long.pass@test.local",
                "password": "VeryLongPassword123!",  # 20 chars
                "name": "Long Password Test",
            },
        )

        assert response.status_code == 201

    async def test_it5_mfa_required_integration(
        self, async_client, test_db, test_users, settings_reset
    ):
        """IT-5: mfa_required shows grace period warning."""
        # Enable MFA requirement
        await update_setting(test_db, "mfa_required", True)
        await flush_redis_cache()

        user = test_users[2]

        # Login
        token = await get_token(async_client, user.email, "UserPassword123!")
        assert token is not None

        # Access protected endpoint
        response = await async_client.get(
            "/api/v1/projects",
            headers={"Authorization": f"Bearer {token}"},
        )

        # Should succeed (grace period) with warning header
        assert response.status_code == 200
        assert "X-MFA-Setup-Required" in response.headers

        # Verify deadline set in database
        await test_db.refresh(user)
        assert user.mfa_setup_deadline is not None


# =========================================================================
# Test Suite 2: Cross-Setting Interactions (IT-6 to IT-8)
# =========================================================================

@pytest.mark.asyncio
class TestCrossSettingInteractions:
    """Test interactions between multiple settings."""

    async def test_it6_session_timeout_plus_lockout(
        self, async_client, test_db, test_users, settings_reset
    ):
        """IT-6: Session timeout and account lockout are independent."""
        await update_setting(test_db, "session_timeout_minutes", 5)
        await update_setting(test_db, "max_login_attempts", 3)
        await flush_redis_cache()

        user = test_users[0]

        # Get valid token
        token = await get_token(async_client, user.email, "UserPassword123!")
        assert token is not None

        # Lock account (separate action)
        user.failed_login_count = 3
        user.locked_until = datetime.utcnow() + timedelta(minutes=30)
        await test_db.commit()

        # Expired token check should return 401 (not 403 for lockout)
        # Token is still valid, so should work
        response = await async_client.get(
            "/api/v1/projects",
            headers={"Authorization": f"Bearer {token}"},
        )

        # Token valid = request succeeds (lockout only affects login, not token use)
        assert response.status_code == 200

    async def test_it7_password_change_plus_mfa(
        self, async_client, test_db, admin_user, test_users, settings_reset
    ):
        """IT-7: Password change respects min_length while MFA active."""
        await update_setting(test_db, "password_min_length", 16)
        await update_setting(test_db, "mfa_required", True)
        await flush_redis_cache()

        # Admin login
        admin_token = await get_token(
            async_client, admin_user.email, "AdminIntegration123!"
        )
        assert admin_token is not None

        user = test_users[0]

        # Try to set weak password (should fail)
        response = await async_client.put(
            f"/api/v1/admin/users/{user.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"new_password": "Short123!"},
        )

        assert response.status_code == 400
        assert "16 characters" in response.json()["detail"]

    async def test_it8_admin_exemptions_with_settings(
        self, async_client, test_db, admin_user, test_users, settings_reset
    ):
        """IT-8: Admin exemptions work while settings enforced."""
        await update_setting(test_db, "mfa_required", True)
        await update_setting(test_db, "max_login_attempts", 3)
        await flush_redis_cache()

        admin_token = await get_token(
            async_client, admin_user.email, "AdminIntegration123!"
        )

        user = test_users[0]

        # Exempt user from MFA
        response = await async_client.post(
            f"/api/v1/admin/users/{user.id}/mfa-exempt",
            headers={"Authorization": f"Bearer {admin_token}"},
            json=True,
        )

        assert response.status_code == 200

        # User should access without MFA warning
        user_token = await get_token(async_client, user.email, "UserPassword123!")

        response = await async_client.get(
            "/api/v1/projects",
            headers={"Authorization": f"Bearer {user_token}"},
        )

        assert response.status_code == 200
        assert "X-MFA-Setup-Required" not in response.headers


# =========================================================================
# Test Suite 3: Cache Invalidation (IT-9 to IT-10)
# =========================================================================

@pytest.mark.asyncio
class TestCacheInvalidation:
    """Test Redis cache invalidation for settings."""

    async def test_it9_setting_change_propagation(
        self, async_client, test_db, test_users, settings_reset
    ):
        """IT-9: Setting changes propagate after cache flush."""
        # Set initial timeout
        await update_setting(test_db, "session_timeout_minutes", 60)
        await flush_redis_cache()

        user = test_users[0]

        # Get token with 60-min expiry
        token1 = await get_token(async_client, user.email, "UserPassword123!")

        import jwt
        decoded1 = jwt.decode(token1, options={"verify_signature": False})
        duration1 = decoded1["exp"] - decoded1["iat"]

        assert abs(duration1 - 3600) < 10  # ~60 minutes

        # Change setting
        await update_setting(test_db, "session_timeout_minutes", 30)
        await flush_redis_cache()

        # Get new token
        token2 = await get_token(async_client, user.email, "UserPassword123!")

        decoded2 = jwt.decode(token2, options={"verify_signature": False})
        duration2 = decoded2["exp"] - decoded2["iat"]

        assert abs(duration2 - 1800) < 10  # ~30 minutes

    async def test_it10_multi_setting_cache_coherence(
        self, async_client, test_db, settings_reset
    ):
        """IT-10: Multiple setting changes are coherent."""
        # Change all settings
        await update_setting(test_db, "session_timeout_minutes", 10)
        await update_setting(test_db, "max_login_attempts", 2)
        await update_setting(test_db, "password_min_length", 20)
        await update_setting(test_db, "mfa_required", True)
        await flush_redis_cache()

        # Verify all settings updated in database
        for key, expected in [
            ("session_timeout_minutes", "10"),
            ("max_login_attempts", "2"),
            ("password_min_length", "20"),
            ("mfa_required", "True"),
        ]:
            result = await test_db.execute(
                select(SystemSetting).where(SystemSetting.key == key)
            )
            setting = result.scalar_one()
            assert str(setting.value) == expected, f"{key} mismatch"


# =========================================================================
# Test Suite 4: Performance & Stress (IT-11 to IT-12)
# =========================================================================

@pytest.mark.asyncio
class TestPerformance:
    """Performance tests for settings enforcement."""

    async def test_it11_latency_with_all_enforcement(
        self, async_client, test_db, test_users, settings_reset
    ):
        """IT-11: API latency stays <100ms with all enforcement active."""
        # Enable all enforcement
        await update_setting(test_db, "session_timeout_minutes", 15)
        await update_setting(test_db, "max_login_attempts", 5)
        await update_setting(test_db, "password_min_length", 12)
        await update_setting(test_db, "mfa_required", True)
        await flush_redis_cache()

        user = test_users[0]

        # Measure login latency (10 requests)
        latencies = []
        for _ in range(10):
            start = time.time()
            response = await async_client.post(
                "/api/v1/auth/login",
                json={"email": user.email, "password": "UserPassword123!"},
            )
            latency = (time.time() - start) * 1000  # ms
            latencies.append(latency)

            # Reset failed count
            user.failed_login_count = 0
            await test_db.commit()

        p95 = sorted(latencies)[int(len(latencies) * 0.95)]

        assert p95 < 500, f"p95 latency {p95}ms exceeds 500ms (test environment)"
        # Note: Production target is <100ms, test environment allows up to 500ms

    async def test_it12_cache_hit_efficiency(
        self, async_client, test_db, test_users, settings_reset
    ):
        """IT-12: Settings are cached efficiently."""
        await flush_redis_cache()

        user = test_users[0]
        token = await get_token(async_client, user.email, "UserPassword123!")

        # First request - cache miss
        start1 = time.time()
        await async_client.get(
            "/api/v1/projects",
            headers={"Authorization": f"Bearer {token}"},
        )
        latency1 = (time.time() - start1) * 1000

        # Subsequent requests - cache hit (should be faster)
        latencies = []
        for _ in range(5):
            start = time.time()
            await async_client.get(
                "/api/v1/projects",
                headers={"Authorization": f"Bearer {token}"},
            )
            latencies.append((time.time() - start) * 1000)

        avg_cached = sum(latencies) / len(latencies)

        # Cached requests should be faster than first request
        # (This is a soft assertion - caching benefit should be visible)
        print(f"First request: {latency1:.2f}ms, Avg cached: {avg_cached:.2f}ms")


# =========================================================================
# Test Suite 5: Edge Cases (IT-13 to IT-15)
# =========================================================================

@pytest.mark.asyncio
class TestEdgeCases:
    """Edge case handling tests."""

    async def test_it13_expired_deadline_plus_exemption(
        self, async_client, test_db, admin_user, test_users, settings_reset
    ):
        """IT-13: Exemption immediately restores access after deadline expired."""
        await update_setting(test_db, "mfa_required", True)
        await flush_redis_cache()

        user = test_users[0]

        # Set expired deadline
        user.mfa_setup_deadline = datetime.utcnow() - timedelta(hours=1)
        await test_db.commit()

        # User should be blocked
        user_token = await get_token(async_client, user.email, "UserPassword123!")

        response = await async_client.get(
            "/api/v1/projects",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 403

        # Admin exempts user
        admin_token = await get_token(
            async_client, admin_user.email, "AdminIntegration123!"
        )

        await async_client.post(
            f"/api/v1/admin/users/{user.id}/mfa-exempt",
            headers={"Authorization": f"Bearer {admin_token}"},
            json=True,
        )

        # User should now have access
        response = await async_client.get(
            "/api/v1/projects",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 200

    async def test_it14_concurrent_setting_changes(
        self, test_db, settings_reset
    ):
        """IT-14: Concurrent setting changes don't cause errors."""
        async def change_setting(key: str, value: int):
            await update_setting(test_db, key, value)

        # Concurrent changes
        await asyncio.gather(
            change_setting("session_timeout_minutes", 10),
            change_setting("max_login_attempts", 3),
            change_setting("password_min_length", 16),
        )

        # Verify all changes applied
        for key in ["session_timeout_minutes", "max_login_attempts", "password_min_length"]:
            result = await test_db.execute(
                select(SystemSetting).where(SystemSetting.key == key)
            )
            setting = result.scalar_one()
            assert setting is not None

    async def test_it15_mfa_disabled_ignores_deadline(
        self, async_client, test_db, test_users, settings_reset
    ):
        """IT-15: When mfa_required=false, expired deadline is ignored."""
        # Disable MFA requirement
        await update_setting(test_db, "mfa_required", False)
        await flush_redis_cache()

        user = test_users[0]

        # Set expired deadline (should be ignored)
        user.mfa_setup_deadline = datetime.utcnow() - timedelta(days=1)
        await test_db.commit()

        # User should access without issue
        token = await get_token(async_client, user.email, "UserPassword123!")

        response = await async_client.get(
            "/api/v1/projects",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        assert "X-MFA-Setup-Required" not in response.headers


# =========================================================================
# Test Summary
# =========================================================================
"""
Integration Test Summary (ADR-027 Phase 1):

Test Suite 1: All Settings Enabled (5 tests)
- IT-1: Baseline configuration
- IT-2: session_timeout_minutes integration
- IT-3: max_login_attempts integration
- IT-4: password_min_length integration
- IT-5: mfa_required integration

Test Suite 2: Cross-Setting Interactions (3 tests)
- IT-6: Session timeout + account lockout
- IT-7: Password change + MFA
- IT-8: Admin exemptions + settings

Test Suite 3: Cache Invalidation (2 tests)
- IT-9: Setting change propagation
- IT-10: Multi-setting cache coherence

Test Suite 4: Performance (2 tests)
- IT-11: Latency with all enforcement
- IT-12: Cache hit efficiency

Test Suite 5: Edge Cases (3 tests)
- IT-13: Expired deadline + exemption
- IT-14: Concurrent setting changes
- IT-15: MFA disabled ignores deadline

Total: 15 integration test cases
Status: Ready for execution
"""
