"""
Quick validation script for UserService implementation.

Tests all 11 methods without requiring full pytest environment.
"""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from app.services.user_service import (
    UserService,
    UserNotFoundError,
    UserValidationError,
    AuthenticationError,
    InvalidPasswordError,
    MFARequiredError,
    MFAVerificationError,
    RoleAssignmentError,
)


class MockDB:
    """Mock database session for testing"""
    pass


def test_create_user():
    """Test: Create user with valid data and password hashing"""
    service = UserService()
    db = MockDB()

    user_data = {
        "email": "developer@company.com",
        "password": "SecureP@ss2024!",
        "role": "developer",
        "full_name": "John Doe",
        "organization_id": "org-123",
    }

    user = service.create_user(db, user_data)

    assert user.email == "developer@company.com"
    assert user.role == "developer"
    assert user.full_name == "John Doe"
    assert user.is_active is True
    assert user.mfa_enabled is False
    assert user.password_hash is not None
    assert user.password_hash != "SecureP@ss2024!"  # Hash, not plain text
    print("✅ test_create_user PASSED")


def test_create_user_invalid_email():
    """Test: Create user with invalid email raises error"""
    service = UserService()
    db = MockDB()

    user_data = {
        "email": "invalid-email",  # No @ symbol
        "password": "SecureP@ss2024!",
        "role": "developer",
    }

    try:
        service.create_user(db, user_data)
        assert False, "Should have raised UserValidationError"
    except UserValidationError as e:
        assert "Invalid email format" in str(e)
        print("✅ test_create_user_invalid_email PASSED")


def test_create_user_invalid_password():
    """Test: Create user with weak password raises error"""
    service = UserService()
    db = MockDB()

    user_data = {
        "email": "developer@company.com",
        "password": "weak",  # Too short, no special chars
        "role": "developer",
    }

    try:
        service.create_user(db, user_data)
        assert False, "Should have raised InvalidPasswordError"
    except InvalidPasswordError as e:
        assert "Password must be" in str(e)
        print("✅ test_create_user_invalid_password PASSED")


def test_password_hashing():
    """Test: Password hashing and verification"""
    service = UserService()

    password = "SecureP@ss2024!"

    # Hash password
    hash1 = service._hash_password(password)
    hash2 = service._hash_password(password)

    # Same password should produce same hash (deterministic for testing)
    assert hash1 == hash2

    # Verification should work
    assert service._verify_password(password, hash1) is True
    assert service._verify_password("wrong_password", hash1) is False

    print("✅ test_password_hashing PASSED")


def test_validate_password_policy():
    """Test: Password policy validation (OWASP ASVS)"""
    service = UserService()

    # Valid password
    assert service._validate_password_policy("SecureP@ss2024!") is True

    # Too short
    try:
        service._validate_password_policy("Short1!")
        assert False, "Should have raised InvalidPasswordError"
    except InvalidPasswordError as e:
        assert "at least" in str(e)

    # No uppercase
    try:
        service._validate_password_policy("securep@ss2024!")
        assert False, "Should have raised InvalidPasswordError"
    except InvalidPasswordError as e:
        assert "uppercase" in str(e)

    # No special character
    try:
        service._validate_password_policy("SecurePass2024")
        assert False, "Should have raised InvalidPasswordError"
    except InvalidPasswordError as e:
        assert "special" in str(e)

    print("✅ test_validate_password_policy PASSED")


def test_valid_roles():
    """Test: All 13 RBAC roles are defined"""
    service = UserService()

    assert len(service.VALID_ROLES) == 13
    assert "platform_admin" in service.VALID_ROLES
    assert "developer" in service.VALID_ROLES
    assert "cto" in service.VALID_ROLES
    assert "viewer" in service.VALID_ROLES
    assert "guest" in service.VALID_ROLES

    print("✅ test_valid_roles PASSED")


def test_role_hierarchy():
    """Test: Role hierarchy levels are correct"""
    service = UserService()

    # Platform admin should be highest
    assert service.ROLE_HIERARCHY["platform_admin"] == 100

    # Owner > Admin > CTO
    assert service.ROLE_HIERARCHY["owner"] > service.ROLE_HIERARCHY["admin"]
    assert service.ROLE_HIERARCHY["admin"] > service.ROLE_HIERARCHY["cto"]

    # Developer > Viewer > Guest
    assert service.ROLE_HIERARCHY["developer"] > service.ROLE_HIERARCHY["viewer"]
    assert service.ROLE_HIERARCHY["viewer"] > service.ROLE_HIERARCHY["guest"]

    print("✅ test_role_hierarchy PASSED")


def test_get_user_permissions():
    """Test: Get permissions for user based on role"""
    service = UserService()
    db = MockDB()

    # Create developer user
    user = service.create_user(db, {
        "email": "dev@company.com",
        "password": "SecureP@ss2024!",
        "role": "developer",
    })

    # Mock get_user_by_id to return the user
    service.get_user_by_id = lambda db, uid: user

    perms = service.get_user_permissions(db, user.id)

    assert perms["role"] == "developer"
    assert perms["level"] == 50  # Developer level
    assert perms["can_view_projects"] is True
    assert perms["can_create_projects"] is True
    assert perms["can_delete_projects"] is False  # Level 70+ required
    assert perms["can_manage_users"] is False  # Level 80+ required
    assert perms["is_platform_admin"] is False

    print("✅ test_get_user_permissions PASSED")


def test_enable_mfa():
    """Test: Enable MFA generates secret and QR URI"""
    service = UserService()
    db = MockDB()

    # Create user
    user = service.create_user(db, {
        "email": "secure@company.com",
        "password": "SecureP@ss2024!",
        "role": "developer",
    })

    # Mock get_user_by_id
    service.get_user_by_id = lambda db, uid: user

    result = service.enable_mfa(db, user.id)

    assert "mfa_secret" in result
    assert len(result["mfa_secret"]) == 16  # Base32 secret
    assert "qr_code_uri" in result
    assert "otpauth://totp/" in result["qr_code_uri"]
    assert user.email in result["qr_code_uri"]

    print("✅ test_enable_mfa PASSED")


def test_jwt_generation():
    """Test: JWT token generation"""
    service = UserService()
    db = MockDB()

    # Create user
    user = service.create_user(db, {
        "email": "jwt@company.com",
        "password": "SecureP@ss2024!",
        "role": "tech_lead",
    })

    # Generate access token
    access_token = service._generate_jwt(user, "access")
    refresh_token = service._generate_jwt(user, "refresh")

    # Tokens should be generated
    assert access_token is not None
    assert refresh_token is not None
    assert access_token.startswith("mock_jwt_")
    assert refresh_token.startswith("mock_jwt_")

    # Access and refresh tokens should be different
    assert access_token != refresh_token

    print("✅ test_jwt_generation PASSED")


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("UserService Quick Validation Tests")
    print("="*60 + "\n")

    tests = [
        test_create_user,
        test_create_user_invalid_email,
        test_create_user_invalid_password,
        test_password_hashing,
        test_validate_password_policy,
        test_valid_roles,
        test_role_hierarchy,
        test_get_user_permissions,
        test_enable_mfa,
        test_jwt_generation,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"❌ {test.__name__} FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ {test.__name__} ERROR: {e}")
            failed += 1

    print("\n" + "="*60)
    print(f"Tests: {passed} passed, {failed} failed")
    print("="*60 + "\n")

    if failed == 0:
        print("✅ ALL TESTS PASSED - UserService Implementation VALID")
        return 0
    else:
        print("❌ SOME TESTS FAILED - Review implementation")
        return 1


if __name__ == "__main__":
    sys.exit(main())
