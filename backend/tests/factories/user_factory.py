"""
User Factory - Test Data Generation

SDLC 5.2.0 Compliance - Test-Driven Development
Framework: Test Strategy 2026

Purpose:
    Generate User model instances and data dictionaries for testing.

Principles:
    1. Sensible defaults (realistic data)
    2. Override support (Partial[User])
    3. Valid model instances (pass validation)
    4. No hardcoded test data in tests

Usage:
    # Get User instance
    user = get_mock_user()
    admin = get_mock_user({"role": "cto", "is_platform_admin": True})

    # Get data dict (for API requests)
    user_data = get_mock_user_data()
    create_data = get_mock_user_create_data({"email": "custom@example.com"})

Reference:
    - User Model: backend/app/models/user.py
    - Test Strategy: docs/05-test/00-TEST-STRATEGY-2026.md § 3.5
    - Factory Pattern Guide: docs/05-test/FACTORY-PATTERN-GUIDE.md (TBD)
"""

from datetime import datetime, UTC
from typing import Optional, Dict, Any
from uuid import uuid4


def get_mock_user(overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Factory for User model instance data.

    Returns a dictionary representing a User model instance with sensible defaults.
    Use this when you need a complete User object for testing.

    Args:
        overrides: Optional dict to override default values

    Returns:
        Dict with User model fields

    Examples:
        # Basic user
        user = get_mock_user()

        # CTO admin
        cto = get_mock_user({
            "email": "cto@example.com",
            "role": "cto",
            "is_platform_admin": True,
        })

        # Developer with MFA
        dev = get_mock_user({
            "email": "dev@example.com",
            "role": "developer",
            "mfa_enabled": True,
        })
    """
    defaults = {
        "id": str(uuid4()),
        "organization_id": str(uuid4()),
        "email": "test.user@example.com",
        "password_hash": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5jtJ3W8KIgSB6",  # "password123"
        "full_name": "Test User",
        "avatar_url": None,
        "role": "developer",
        "is_active": True,
        "is_superuser": False,
        "is_platform_admin": False,
        "mfa_enabled": False,
        "mfa_secret": None,
        "backup_codes": None,
        "mfa_setup_deadline": None,
        "is_mfa_exempt": False,
        "last_login": None,
        "failed_login_count": 0,
        "locked_until": None,
        "deleted_at": None,
        "deleted_by": None,
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
    }

    return {**defaults, **(overrides or {})}


def get_mock_user_data(overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Factory for User data (API response format).

    Returns a dictionary suitable for API response serialization.
    Excludes sensitive fields like password_hash, mfa_secret.

    Args:
        overrides: Optional dict to override default values

    Returns:
        Dict with User API response fields

    Examples:
        # API response data
        response_data = get_mock_user_data()

        # Custom user response
        admin_data = get_mock_user_data({
            "email": "admin@example.com",
            "role": "admin",
        })
    """
    user = get_mock_user(overrides)

    # Remove sensitive fields for API response
    api_safe_fields = {
        "id": user["id"],
        "organization_id": user["organization_id"],
        "email": user["email"],
        "full_name": user["full_name"],
        "avatar_url": user["avatar_url"],
        "role": user["role"],
        "is_active": user["is_active"],
        "is_platform_admin": user["is_platform_admin"],
        "mfa_enabled": user["mfa_enabled"],
        "last_login": user["last_login"],
        "created_at": user["created_at"].isoformat() if isinstance(user["created_at"], datetime) else user["created_at"],
        "updated_at": user["updated_at"].isoformat() if isinstance(user["updated_at"], datetime) else user["updated_at"],
    }

    return api_safe_fields


def get_mock_user_create_data(overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Factory for User creation request data (API POST payload).

    Returns a dictionary suitable for API POST /api/v1/users request.
    Contains only fields required for user creation.

    Args:
        overrides: Optional dict to override default values

    Returns:
        Dict with User creation request fields

    Examples:
        # Create user request
        create_data = get_mock_user_create_data()
        response = client.post("/api/v1/users", json=create_data)

        # Create CTO
        cto_data = get_mock_user_create_data({
            "email": "cto@example.com",
            "password": "SecurePass123!",
            "role": "cto",
        })
    """
    defaults = {
        "email": "test.user@example.com",
        "password": "TestPassword123!",
        "full_name": "Test User",
        "role": "developer",
    }

    return {**defaults, **(overrides or {})}


def get_mock_user_login_data(overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Factory for User login request data (API POST /api/v1/auth/login).

    Args:
        overrides: Optional dict to override default values

    Returns:
        Dict with login request fields

    Examples:
        # Login request
        login_data = get_mock_user_login_data()
        response = client.post("/api/v1/auth/login", json=login_data)

        # Login with custom credentials
        login_data = get_mock_user_login_data({
            "email": "admin@example.com",
            "password": "AdminPass123!",
        })
    """
    defaults = {
        "email": "test.user@example.com",
        "password": "TestPassword123!",
    }

    return {**defaults, **(overrides or {})}


# ─────────────────────────────────────────────────────────────
# Role-Specific Factories
# ─────────────────────────────────────────────────────────────

def get_mock_cto(overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Factory for CTO user"""
    cto_defaults = {
        "email": "cto@example.com",
        "full_name": "Chief Technology Officer",
        "role": "cto",
        "is_platform_admin": True,
    }
    return get_mock_user({**cto_defaults, **(overrides or {})})


def get_mock_engineering_manager(overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Factory for Engineering Manager user"""
    em_defaults = {
        "email": "em@example.com",
        "full_name": "Engineering Manager",
        "role": "engineering_manager",
    }
    return get_mock_user({**em_defaults, **(overrides or {})})


def get_mock_developer(overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Factory for Developer user"""
    dev_defaults = {
        "email": "dev@example.com",
        "full_name": "Software Developer",
        "role": "developer",
    }
    return get_mock_user({**dev_defaults, **(overrides or {})})


def get_mock_qa_engineer(overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Factory for QA Engineer user"""
    qa_defaults = {
        "email": "qa@example.com",
        "full_name": "QA Engineer",
        "role": "qa",
    }
    return get_mock_user({**qa_defaults, **(overrides or {})})
