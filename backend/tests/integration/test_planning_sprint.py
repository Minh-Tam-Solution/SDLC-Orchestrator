"""
=========================================================================
Integration Tests for Sprint API
SDLC Orchestrator - Sprint 75 (Planning API Validation)

SDLC Stage: 04 - BUILD
Sprint: 75 - Planning API Validation
Framework: SDLC 5.1.3 (Sprint Planning Governance)
Reference: ADR-013-Planning-Hierarchy

Purpose:
Test Sprint API endpoints including:
- Sprint CRUD operations
- Sprint numbering (immutable per Rule #1)
- Phase relationship
- Sprint status transitions
- G-Sprint gate initialization

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
from app.models.sprint import Sprint
from app.models.sprint_gate_evaluation import SprintGateEvaluation
from app.models.user import User


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
async def test_project(db_session, test_user):
    """Create a test project owned by test_user."""
    project = Project(
        name="Sprint Test Project",
        slug=f"sprint-test-{uuid4().hex[:8]}",
        description="Project for testing Sprint API",
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
        name="Phase 1",
        status="in_progress",
    )
    db_session.add(phase)
    await db_session.commit()
    await db_session.refresh(phase)
    return phase


@pytest.fixture
async def test_sprint(db_session, test_project, test_phase, test_user):
    """Create a test sprint."""
    sprint = Sprint(
        project_id=test_project.id,
        phase_id=test_phase.id,
        number=74,
        name="Sprint 74",
        goal="Implement Planning Hierarchy",
        status="planning",
        start_date=date.today(),
        end_date=date.today() + timedelta(days=10),
        capacity_points=40,
        team_size=5,
        created_by=test_user.id,
    )
    db_session.add(sprint)
    await db_session.commit()
    await db_session.refresh(sprint)
    return sprint


@pytest.fixture
async def other_project(db_session, test_admin):
    """Create a project owned by another user."""
    project = Project(
        name="Other Sprint Project",
        slug=f"other-sprint-{uuid4().hex[:8]}",
        owner_id=test_admin.id,
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)
    return project


# =============================================================================
# Sprint CRUD Tests
# =============================================================================


class TestSprintAPI:
    """Test Sprint CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_sprint_success(
        self, client: AsyncClient, auth_headers, test_project, test_phase
    ):
        """Test creating a sprint successfully."""
        response = await client.post(
            "/api/v1/planning/sprints",
            json={
                "project_id": str(test_project.id),
                "phase_id": str(test_phase.id),
                "number": 75,
                "name": "Sprint 75",
                "goal": "Implement API validation",
                "start_date": str(date.today()),
                "end_date": str(date.today() + timedelta(days=10)),
                "capacity_points": 35,
                "team_size": 4,
            },
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Sprint 75"
        assert data["number"] == 75
        assert data["goal"] == "Implement API validation"
        assert data["status"] == "planning"
        assert data["g_sprint_status"] == "pending"

    @pytest.mark.asyncio
    async def test_create_sprint_auto_number(
        self, client: AsyncClient, auth_headers, test_project, test_phase, test_sprint
    ):
        """Test that sprint number auto-increments within project."""
        response = await client.post(
            "/api/v1/planning/sprints",
            json={
                "project_id": str(test_project.id),
                "phase_id": str(test_phase.id),
                "name": "Next Sprint",
                "goal": "Continue work",
            },
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        # Should be 75 since test_sprint is 74
        assert data["number"] == 75

    @pytest.mark.asyncio
    async def test_create_sprint_duplicate_number_fails(
        self, client: AsyncClient, auth_headers, test_project, test_phase, test_sprint
    ):
        """Test creating a sprint with duplicate number fails (Rule #1)."""
        response = await client.post(
            "/api/v1/planning/sprints",
            json={
                "project_id": str(test_project.id),
                "number": 74,  # Same as test_sprint
                "name": "Duplicate Sprint",
                "goal": "Should fail",
            },
            headers=auth_headers,
        )

        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_create_sprint_without_phase(
        self, client: AsyncClient, auth_headers, test_project
    ):
        """Test creating a sprint without phase (direct to project)."""
        response = await client.post(
            "/api/v1/planning/sprints",
            json={
                "project_id": str(test_project.id),
                "number": 1,
                "name": "Standalone Sprint",
                "goal": "Test without phase",
            },
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["phase_id"] is None

    @pytest.mark.asyncio
    async def test_create_sprint_other_project_forbidden(
        self, client: AsyncClient, auth_headers, other_project
    ):
        """Test creating a sprint on other user's project fails."""
        response = await client.post(
            "/api/v1/planning/sprints",
            json={
                "project_id": str(other_project.id),
                "name": "Forbidden Sprint",
                "goal": "Should fail",
            },
            headers=auth_headers,
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_get_sprint_success(
        self, client: AsyncClient, auth_headers, test_sprint
    ):
        """Test getting a sprint by ID."""
        response = await client.get(
            f"/api/v1/planning/sprints/{test_sprint.id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_sprint.id)
        assert data["number"] == test_sprint.number
        assert data["goal"] == test_sprint.goal

    @pytest.mark.asyncio
    async def test_get_sprint_not_found(
        self, client: AsyncClient, auth_headers
    ):
        """Test getting a non-existent sprint returns 404."""
        fake_id = uuid4()
        response = await client.get(
            f"/api/v1/planning/sprints/{fake_id}",
            headers=auth_headers,
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_list_project_sprints(
        self, client: AsyncClient, auth_headers, test_project, test_sprint
    ):
        """Test listing sprints for a project."""
        response = await client.get(
            f"/api/v1/planning/projects/{test_project.id}/sprints",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) >= 1
        assert any(s["id"] == str(test_sprint.id) for s in data["items"])

    @pytest.mark.asyncio
    async def test_update_sprint_success(
        self, client: AsyncClient, auth_headers, test_sprint
    ):
        """Test updating a sprint."""
        response = await client.put(
            f"/api/v1/planning/sprints/{test_sprint.id}",
            json={
                "name": "Updated Sprint Name",
                "goal": "Updated goal",
                "capacity_points": 45,
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Sprint Name"
        assert data["goal"] == "Updated goal"
        assert data["capacity_points"] == 45
        # Number should not change
        assert data["number"] == test_sprint.number

    @pytest.mark.asyncio
    async def test_update_sprint_number_immutable(
        self, client: AsyncClient, auth_headers, test_sprint
    ):
        """Test that sprint number cannot be changed (Rule #1)."""
        original_number = test_sprint.number
        response = await client.put(
            f"/api/v1/planning/sprints/{test_sprint.id}",
            json={
                "number": 999,  # Try to change number
            },
            headers=auth_headers,
        )

        # Either 400 (rejected) or 200 (ignored)
        if response.status_code == 200:
            data = response.json()
            # Number should remain unchanged
            assert data["number"] == original_number

    @pytest.mark.asyncio
    async def test_sprint_status_transition(
        self, client: AsyncClient, auth_headers, test_sprint
    ):
        """Test sprint status transitions."""
        # planning -> in_progress
        response = await client.put(
            f"/api/v1/planning/sprints/{test_sprint.id}",
            json={"status": "in_progress"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "in_progress"

    @pytest.mark.asyncio
    async def test_delete_sprint_success(
        self, client: AsyncClient, auth_headers, db_session, test_project, test_user
    ):
        """Test deleting a sprint."""
        # Create a sprint to delete
        sprint = Sprint(
            project_id=test_project.id,
            number=999,
            name="Sprint to Delete",
            goal="Will be deleted",
            created_by=test_user.id,
        )
        db_session.add(sprint)
        await db_session.commit()
        await db_session.refresh(sprint)

        response = await client.delete(
            f"/api/v1/planning/sprints/{sprint.id}",
            headers=auth_headers,
        )

        assert response.status_code == 204

        # Verify deletion
        get_response = await client.get(
            f"/api/v1/planning/sprints/{sprint.id}",
            headers=auth_headers,
        )
        assert get_response.status_code == 404
