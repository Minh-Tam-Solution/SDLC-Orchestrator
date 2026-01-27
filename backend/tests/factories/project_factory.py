"""
Project Factory - Test Data Generation

SDLC 5.2.0 Compliance - Test-Driven Development
Framework: Test Strategy 2026

Purpose:
    Generate Project model instances and data dictionaries for testing.

Principles:
    1. Sensible defaults (realistic project data)
    2. Override support (Partial[Project])
    3. Valid model instances (pass validation)
    4. Multi-tenancy support (project-level isolation)

Usage:
    # Get Project instance
    project = get_mock_project()
    archived = get_mock_project({"is_active": False})

    # Get data dict (for API requests)
    project_data = get_mock_project_data()
    create_data = get_mock_project_create_data({"name": "My Project"})

Reference:
    - Project Model: backend/app/models/project.py
    - Test Strategy: docs/05-test/00-TEST-STRATEGY-2026.md § 3.5
    - Factory Pattern Guide: docs/05-test/FACTORY-PATTERN-GUIDE.md (TBD)
"""

from datetime import datetime, UTC
from typing import Optional, Dict, Any
from uuid import uuid4


def get_mock_project(overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Factory for Project model instance data.

    Returns a dictionary representing a Project model instance with sensible defaults.
    Use this when you need a complete Project object for testing.

    Args:
        overrides: Optional dict to override default values

    Returns:
        Dict with Project model fields

    Examples:
        # Basic project
        project = get_mock_project()

        # E-commerce project
        ecommerce = get_mock_project({
            "name": "E-commerce Platform",
            "slug": "ecommerce-platform",
            "description": "Next.js + Stripe + PostgreSQL",
        })

        # GitHub-synced project
        synced = get_mock_project({
            "github_repo_id": "123456789",
            "github_repo_full_name": "org/repo",
            "github_sync_status": "synced",
        })
    """
    defaults = {
        "id": str(uuid4()),
        "name": "Test Project",
        "slug": "test-project",
        "description": "Test project for automated testing",
        "owner_id": str(uuid4()),
        "is_active": True,
        "github_repo_id": None,
        "github_repo_full_name": None,
        "github_sync_status": "pending",
        "github_synced_at": None,
        "framework_version": "5.2.0",
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
        "deleted_at": None,
    }

    return {**defaults, **(overrides or {})}


def get_mock_project_data(overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Factory for Project data (API response format).

    Returns a dictionary suitable for API response serialization.

    Args:
        overrides: Optional dict to override default values

    Returns:
        Dict with Project API response fields

    Examples:
        # API response data
        response_data = get_mock_project_data()

        # Custom project response
        project_data = get_mock_project_data({
            "name": "Instagram Clone",
            "description": "Social media platform",
        })
    """
    project = get_mock_project(overrides)

    api_safe_fields = {
        "id": project["id"],
        "name": project["name"],
        "slug": project["slug"],
        "description": project["description"],
        "owner_id": project["owner_id"],
        "is_active": project["is_active"],
        "github_repo_id": project["github_repo_id"],
        "github_repo_full_name": project["github_repo_full_name"],
        "github_sync_status": project["github_sync_status"],
        "github_synced_at": project["github_synced_at"],
        "framework_version": project["framework_version"],
        "created_at": project["created_at"].isoformat() if isinstance(project["created_at"], datetime) else project["created_at"],
        "updated_at": project["updated_at"].isoformat() if isinstance(project["updated_at"], datetime) else project["updated_at"],
    }

    return api_safe_fields


def get_mock_project_create_data(overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Factory for Project creation request data (API POST payload).

    Returns a dictionary suitable for API POST /api/v1/projects request.
    Contains only fields required for project creation.

    Args:
        overrides: Optional dict to override default values

    Returns:
        Dict with Project creation request fields

    Examples:
        # Create project request
        create_data = get_mock_project_create_data()
        response = client.post("/api/v1/projects", json=create_data)

        # Create with custom data
        project_data = get_mock_project_create_data({
            "name": "Blog API",
            "description": "FastAPI + PostgreSQL REST API",
        })
    """
    defaults = {
        "name": "Test Project",
        "slug": "test-project",
        "description": "Test project for automated testing",
        "framework_version": "5.2.0",
    }

    return {**defaults, **(overrides or {})}


def get_mock_project_update_data(overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Factory for Project update request data (API PUT payload).

    Args:
        overrides: Optional dict to override default values

    Returns:
        Dict with Project update request fields

    Examples:
        # Update project
        update_data = get_mock_project_update_data({
            "name": "Updated Project Name",
            "is_active": False,
        })
        response = client.put(f"/api/v1/projects/{id}", json=update_data)
    """
    defaults = {
        "name": "Updated Test Project",
        "description": "Updated description",
    }

    return {**defaults, **(overrides or {})}


# ─────────────────────────────────────────────────────────────
# Domain-Specific Project Factories
# ─────────────────────────────────────────────────────────────

def get_mock_ecommerce_project(overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Factory for E-commerce project"""
    ecommerce_defaults = {
        "name": "E-commerce Platform",
        "slug": "ecommerce-platform",
        "description": "Next.js 14 + Stripe + PostgreSQL + Redis",
    }
    return get_mock_project({**ecommerce_defaults, **(overrides or {})})


def get_mock_saas_project(overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Factory for SaaS project"""
    saas_defaults = {
        "name": "SaaS Subscription Platform",
        "slug": "saas-subscription",
        "description": "Next.js + Stripe Subscriptions + Multi-tenant",
    }
    return get_mock_project({**saas_defaults, **(overrides or {})})


def get_mock_api_project(overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Factory for API project"""
    api_defaults = {
        "name": "REST API Backend",
        "slug": "rest-api-backend",
        "description": "FastAPI + PostgreSQL + Redis + OPA",
    }
    return get_mock_project({**api_defaults, **(overrides or {})})


def get_mock_mobile_project(overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Factory for Mobile project"""
    mobile_defaults = {
        "name": "Mobile Social App",
        "slug": "mobile-social-app",
        "description": "React Native + Expo + Zustand + Firebase",
    }
    return get_mock_project({**mobile_defaults, **(overrides or {})})


def get_mock_github_synced_project(overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Factory for GitHub-synced project"""
    github_defaults = {
        "name": "GitHub Synced Project",
        "slug": "github-synced-project",
        "github_repo_id": "123456789",
        "github_repo_full_name": "organization/repository",
        "github_sync_status": "synced",
        "github_synced_at": datetime.now(UTC),
    }
    return get_mock_project({**github_defaults, **(overrides or {})})
