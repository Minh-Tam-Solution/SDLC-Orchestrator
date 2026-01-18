"""
=========================================================================
Integration Tests for Phase API
SDLC Orchestrator - Sprint 75 (Planning API Validation)

SDLC Stage: 04 - BUILD
Sprint: 75 - Planning API Validation
Framework: SDLC 5.1.3 (Sprint Planning Governance)
Reference: ADR-013-Planning-Hierarchy

Purpose:
Test Phase API endpoints including:
- Phase CRUD operations
- Roadmap relationship validation
- Phase numbering within roadmap

Test Coverage Target: 90%+
=========================================================================
"""

import pytest
from httpx import AsyncClient
from uuid import uuid4
from datetime import date, timedelta

from app.models.project import Project
from app.models.roadmap import Roadmap
from app.models.phase import Phase
from app.models.user import User


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
async def test_project(db_session, test_user):
    """Create a test project owned by test_user."""
    project = Project(
        name="Phase Test Project",
        slug=f"phase-test-{uuid4().hex[:8]}",
        description="Project for testing Phase API",
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
        description="Test roadmap",
        status="active",
        created_by=test_user.id,
    )
    db_session.add(roadmap)
    await db_session.commit()
    await db_session.refresh(roadmap)
    return roadmap


@pytest.fixture
async def test_phase(db_session, test_roadmap):
    """Create a test phase."""
    phase = Phase(
        roadmap_id=test_roadmap.id,
        number=1,
        name="Phase 1: Foundation",
        theme="Infrastructure Setup",
        objective="Build core infrastructure",
        status="planned",
        start_date=date.today(),
        end_date=date.today() + timedelta(weeks=4),
    )
    db_session.add(phase)
    await db_session.commit()
    await db_session.refresh(phase)
    return phase


@pytest.fixture
async def other_roadmap(db_session, test_admin):
    """Create a roadmap owned by another user."""
    project = Project(
        name="Other Project",
        slug=f"other-{uuid4().hex[:8]}",
        owner_id=test_admin.id,
    )
    db_session.add(project)
    await db_session.flush()

    roadmap = Roadmap(
        project_id=project.id,
        name="Other Roadmap",
        created_by=test_admin.id,
    )
    db_session.add(roadmap)
    await db_session.commit()
    await db_session.refresh(roadmap)
    return roadmap


# =============================================================================
# Phase CRUD Tests
# =============================================================================


class TestPhaseAPI:
    """Test Phase CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_phase_success(
        self, client: AsyncClient, auth_headers, test_roadmap
    ):
        """Test creating a phase successfully."""
        response = await client.post(
            "/api/v1/planning/phases",
            json={
                "roadmap_id": str(test_roadmap.id),
                "number": 1,
                "name": "Phase 1: MVP",
                "theme": "Core Features",
                "objective": "Deliver minimum viable product",
                "start_date": str(date.today()),
                "end_date": str(date.today() + timedelta(weeks=6)),
            },
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Phase 1: MVP"
        assert data["number"] == 1
        assert data["roadmap_id"] == str(test_roadmap.id)
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_phase_auto_number(
        self, client: AsyncClient, auth_headers, test_roadmap, test_phase
    ):
        """Test that phase number auto-increments if not provided."""
        response = await client.post(
            "/api/v1/planning/phases",
            json={
                "roadmap_id": str(test_roadmap.id),
                "name": "Phase 2: Growth",
                "theme": "Scale Features",
            },
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        # Should be 2 since test_phase is number 1
        assert data["number"] == 2

    @pytest.mark.asyncio
    async def test_create_phase_duplicate_number_fails(
        self, client: AsyncClient, auth_headers, test_roadmap, test_phase
    ):
        """Test creating a phase with duplicate number fails."""
        response = await client.post(
            "/api/v1/planning/phases",
            json={
                "roadmap_id": str(test_roadmap.id),
                "number": 1,  # Same as test_phase
                "name": "Duplicate Phase",
            },
            headers=auth_headers,
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_create_phase_other_roadmap_forbidden(
        self, client: AsyncClient, auth_headers, other_roadmap
    ):
        """Test creating a phase on other user's roadmap fails."""
        response = await client.post(
            "/api/v1/planning/phases",
            json={
                "roadmap_id": str(other_roadmap.id),
                "name": "Forbidden Phase",
            },
            headers=auth_headers,
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_get_phase_success(
        self, client: AsyncClient, auth_headers, test_phase
    ):
        """Test getting a phase by ID."""
        response = await client.get(
            f"/api/v1/planning/phases/{test_phase.id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_phase.id)
        assert data["name"] == test_phase.name
        assert data["number"] == test_phase.number

    @pytest.mark.asyncio
    async def test_list_roadmap_phases(
        self, client: AsyncClient, auth_headers, test_roadmap, test_phase
    ):
        """Test listing phases for a roadmap."""
        response = await client.get(
            f"/api/v1/planning/roadmaps/{test_roadmap.id}/phases",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) >= 1
        assert any(p["id"] == str(test_phase.id) for p in data["items"])

    @pytest.mark.asyncio
    async def test_update_phase_success(
        self, client: AsyncClient, auth_headers, test_phase
    ):
        """Test updating a phase."""
        response = await client.put(
            f"/api/v1/planning/phases/{test_phase.id}",
            json={
                "name": "Updated Phase Name",
                "theme": "Updated Theme",
                "status": "in_progress",
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Phase Name"
        assert data["theme"] == "Updated Theme"
        assert data["status"] == "in_progress"

    @pytest.mark.asyncio
    async def test_delete_phase_success(
        self, client: AsyncClient, auth_headers, db_session, test_roadmap
    ):
        """Test deleting a phase."""
        # Create a phase to delete
        phase = Phase(
            roadmap_id=test_roadmap.id,
            number=99,
            name="Phase to Delete",
        )
        db_session.add(phase)
        await db_session.commit()
        await db_session.refresh(phase)

        response = await client.delete(
            f"/api/v1/planning/phases/{phase.id}",
            headers=auth_headers,
        )

        assert response.status_code == 204

        # Verify deletion
        get_response = await client.get(
            f"/api/v1/planning/phases/{phase.id}",
            headers=auth_headers,
        )
        assert get_response.status_code == 404
