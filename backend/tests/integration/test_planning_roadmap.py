"""
=========================================================================
Integration Tests for Roadmap API
SDLC Orchestrator - Sprint 75 (Planning API Validation)

SDLC Stage: 04 - BUILD
Sprint: 75 - Planning API Validation
Framework: SDLC 5.1.3 (Sprint Planning Governance)
Reference: ADR-013-Planning-Hierarchy

Purpose:
Test Roadmap API endpoints including:
- Roadmap CRUD operations
- Project access validation
- Response serialization

Test Coverage Target: 90%+
=========================================================================
"""

import pytest
from httpx import AsyncClient
from uuid import uuid4

from app.models.project import Project, ProjectMember
from app.models.roadmap import Roadmap
from app.models.user import User


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
async def test_project(db_session, test_user):
    """Create a test project owned by test_user."""
    project = Project(
        name="Test Project",
        slug=f"test-project-{uuid4().hex[:8]}",
        description="Project for testing Planning API",
        owner_id=test_user.id,
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)
    return project


@pytest.fixture
async def test_roadmap(db_session, test_project, test_user):
    """Create a test roadmap."""
    roadmap = Roadmap(
        project_id=test_project.id,
        name="2026 Roadmap",
        description="Test roadmap for 2026",
        vision="Build the best product",
        review_cadence="quarterly",
        status="active",
        created_by=test_user.id,
    )
    db_session.add(roadmap)
    await db_session.commit()
    await db_session.refresh(roadmap)
    return roadmap


@pytest.fixture
async def other_project(db_session, test_admin):
    """Create a project owned by another user (admin)."""
    project = Project(
        name="Other Project",
        slug=f"other-project-{uuid4().hex[:8]}",
        description="Project owned by admin",
        owner_id=test_admin.id,
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)
    return project


# =============================================================================
# Roadmap CRUD Tests
# =============================================================================


class TestRoadmapAPI:
    """Test Roadmap CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_roadmap_success(
        self, client: AsyncClient, auth_headers, test_project
    ):
        """Test creating a roadmap successfully."""
        response = await client.post(
            "/api/v1/planning/roadmaps",
            json={
                "project_id": str(test_project.id),
                "name": "Q1 2026 Roadmap",
                "description": "First quarter roadmap",
                "vision": "Launch MVP",
                "review_cadence": "monthly",
            },
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Q1 2026 Roadmap"
        assert data["project_id"] == str(test_project.id)
        assert data["status"] == "active"
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_roadmap_without_auth(
        self, client: AsyncClient, test_project
    ):
        """Test creating a roadmap without authentication fails."""
        response = await client.post(
            "/api/v1/planning/roadmaps",
            json={
                "project_id": str(test_project.id),
                "name": "Unauthorized Roadmap",
            },
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_roadmap_other_project_forbidden(
        self, client: AsyncClient, auth_headers, other_project
    ):
        """Test creating a roadmap on other user's project fails."""
        response = await client.post(
            "/api/v1/planning/roadmaps",
            json={
                "project_id": str(other_project.id),
                "name": "Forbidden Roadmap",
            },
            headers=auth_headers,
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_get_roadmap_success(
        self, client: AsyncClient, auth_headers, test_roadmap
    ):
        """Test getting a roadmap by ID."""
        response = await client.get(
            f"/api/v1/planning/roadmaps/{test_roadmap.id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_roadmap.id)
        assert data["name"] == test_roadmap.name

    @pytest.mark.asyncio
    async def test_get_roadmap_not_found(
        self, client: AsyncClient, auth_headers
    ):
        """Test getting a non-existent roadmap returns 404."""
        fake_id = uuid4()
        response = await client.get(
            f"/api/v1/planning/roadmaps/{fake_id}",
            headers=auth_headers,
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_list_project_roadmaps(
        self, client: AsyncClient, auth_headers, test_project, test_roadmap
    ):
        """Test listing roadmaps for a project."""
        response = await client.get(
            f"/api/v1/planning/projects/{test_project.id}/roadmaps",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) >= 1
        assert any(r["id"] == str(test_roadmap.id) for r in data["items"])

    @pytest.mark.asyncio
    async def test_update_roadmap_success(
        self, client: AsyncClient, auth_headers, test_roadmap
    ):
        """Test updating a roadmap."""
        response = await client.put(
            f"/api/v1/planning/roadmaps/{test_roadmap.id}",
            json={
                "name": "Updated Roadmap Name",
                "description": "Updated description",
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Roadmap Name"
        assert data["description"] == "Updated description"

    @pytest.mark.asyncio
    async def test_delete_roadmap_success(
        self, client: AsyncClient, auth_headers, db_session, test_project, test_user
    ):
        """Test deleting a roadmap."""
        # Create a roadmap to delete
        roadmap = Roadmap(
            project_id=test_project.id,
            name="Roadmap to Delete",
            created_by=test_user.id,
        )
        db_session.add(roadmap)
        await db_session.commit()
        await db_session.refresh(roadmap)

        response = await client.delete(
            f"/api/v1/planning/roadmaps/{roadmap.id}",
            headers=auth_headers,
        )

        assert response.status_code == 204

        # Verify deletion
        get_response = await client.get(
            f"/api/v1/planning/roadmaps/{roadmap.id}",
            headers=auth_headers,
        )
        assert get_response.status_code == 404
