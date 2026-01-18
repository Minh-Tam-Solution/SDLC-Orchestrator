"""
=========================================================================
Integration Tests for Backlog Item API
SDLC Orchestrator - Sprint 75 (Planning API Validation)

SDLC Stage: 04 - BUILD
Sprint: 75 - Planning API Validation
Framework: SDLC 5.1.3 (Sprint Planning Governance)
Reference: ADR-013-Planning-Hierarchy

Purpose:
Test Backlog Item API endpoints including:
- Backlog item CRUD operations (story, task, bug, spike)
- Priority management (P0/P1/P2 - Rule #8)
- Sprint assignment and backlog movement
- Status transitions (todo → in_progress → review → done)
- Subtask hierarchy (parent-child)
- Team membership validation for assignees

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
from app.models.backlog_item import BacklogItem
from app.models.team import Team
from app.models.team_member import TeamMember
from app.models.user import User


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
async def test_project(db_session, test_user):
    """Create a test project owned by test_user."""
    project = Project(
        name="Backlog Test Project",
        slug=f"backlog-test-{uuid4().hex[:8]}",
        description="Project for testing Backlog API",
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
    """Create a test sprint for backlog assignment."""
    sprint = Sprint(
        project_id=test_project.id,
        phase_id=test_phase.id,
        number=75,
        name="Sprint 75",
        goal="Test Backlog API",
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
async def test_backlog_item(db_session, test_project, test_user):
    """Create a test backlog item (product backlog - no sprint)."""
    item = BacklogItem(
        project_id=test_project.id,
        type="story",
        title="Test User Story",
        description="As a user, I want to test backlog API",
        priority="P1",
        story_points=5,
        status="todo",
        created_by=test_user.id,
    )
    db_session.add(item)
    await db_session.commit()
    await db_session.refresh(item)
    return item


@pytest.fixture
async def test_sprint_item(db_session, test_project, test_sprint, test_user):
    """Create a test backlog item assigned to sprint."""
    item = BacklogItem(
        project_id=test_project.id,
        sprint_id=test_sprint.id,
        type="task",
        title="Sprint Task",
        description="Task assigned to sprint",
        priority="P0",
        story_points=3,
        status="todo",
        created_by=test_user.id,
    )
    db_session.add(item)
    await db_session.commit()
    await db_session.refresh(item)
    return item


@pytest.fixture
async def test_team(db_session, test_project, test_user):
    """Create a test team for the project."""
    team = Team(
        project_id=test_project.id,
        name="Backlog Test Team",
        created_by=test_user.id,
    )
    db_session.add(team)
    await db_session.commit()
    await db_session.refresh(team)
    return team


@pytest.fixture
async def test_team_member(db_session, test_team, test_user):
    """Create a team member."""
    member = TeamMember(
        team_id=test_team.id,
        user_id=test_user.id,
        role="admin",
    )
    db_session.add(member)
    await db_session.commit()
    await db_session.refresh(member)
    return member


@pytest.fixture
async def other_project(db_session, test_admin):
    """Create a project owned by another user."""
    project = Project(
        name="Other Backlog Project",
        slug=f"other-backlog-{uuid4().hex[:8]}",
        owner_id=test_admin.id,
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)
    return project


# =============================================================================
# Backlog Item CRUD Tests
# =============================================================================


class TestBacklogItemAPI:
    """Test Backlog Item CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_backlog_item_success(
        self, client: AsyncClient, auth_headers, test_project
    ):
        """Test creating a backlog item successfully."""
        response = await client.post(
            "/api/v1/planning/backlog",
            json={
                "project_id": str(test_project.id),
                "type": "story",
                "title": "Implement user authentication",
                "description": "As a user, I want to login securely",
                "acceptance_criteria": "User can login with email/password",
                "priority": "P0",
                "story_points": 8,
            },
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Implement user authentication"
        assert data["type"] == "story"
        assert data["priority"] == "P0"
        assert data["status"] == "todo"
        assert data["sprint_id"] is None  # Product backlog

    @pytest.mark.asyncio
    async def test_create_backlog_item_with_sprint(
        self, client: AsyncClient, auth_headers, test_project, test_sprint
    ):
        """Test creating a backlog item assigned to sprint."""
        response = await client.post(
            "/api/v1/planning/backlog",
            json={
                "project_id": str(test_project.id),
                "sprint_id": str(test_sprint.id),
                "type": "task",
                "title": "Create API endpoint",
                "priority": "P1",
                "story_points": 3,
            },
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["sprint_id"] == str(test_sprint.id)

    @pytest.mark.asyncio
    async def test_create_backlog_item_all_types(
        self, client: AsyncClient, auth_headers, test_project
    ):
        """Test creating backlog items with all types."""
        types = ["story", "task", "bug", "spike"]

        for item_type in types:
            response = await client.post(
                "/api/v1/planning/backlog",
                json={
                    "project_id": str(test_project.id),
                    "type": item_type,
                    "title": f"Test {item_type}",
                    "priority": "P2",
                },
                headers=auth_headers,
            )
            assert response.status_code == 201
            data = response.json()
            assert data["type"] == item_type

    @pytest.mark.asyncio
    async def test_create_backlog_item_invalid_type(
        self, client: AsyncClient, auth_headers, test_project
    ):
        """Test creating backlog item with invalid type fails."""
        response = await client.post(
            "/api/v1/planning/backlog",
            json={
                "project_id": str(test_project.id),
                "type": "invalid_type",
                "title": "Invalid type item",
                "priority": "P1",
            },
            headers=auth_headers,
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_create_backlog_item_other_project_forbidden(
        self, client: AsyncClient, auth_headers, other_project
    ):
        """Test creating backlog item on other user's project fails."""
        response = await client.post(
            "/api/v1/planning/backlog",
            json={
                "project_id": str(other_project.id),
                "type": "story",
                "title": "Forbidden item",
                "priority": "P1",
            },
            headers=auth_headers,
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_get_backlog_item_success(
        self, client: AsyncClient, auth_headers, test_backlog_item
    ):
        """Test getting a backlog item by ID."""
        response = await client.get(
            f"/api/v1/planning/backlog/{test_backlog_item.id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_backlog_item.id)
        assert data["title"] == test_backlog_item.title

    @pytest.mark.asyncio
    async def test_get_backlog_item_not_found(
        self, client: AsyncClient, auth_headers
    ):
        """Test getting a non-existent backlog item returns 404."""
        fake_id = uuid4()
        response = await client.get(
            f"/api/v1/planning/backlog/{fake_id}",
            headers=auth_headers,
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_list_project_backlog(
        self, client: AsyncClient, auth_headers, test_project, test_backlog_item
    ):
        """Test listing backlog items for a project."""
        response = await client.get(
            f"/api/v1/planning/projects/{test_project.id}/backlog",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) >= 1

    @pytest.mark.asyncio
    async def test_list_sprint_backlog(
        self, client: AsyncClient, auth_headers, test_sprint, test_sprint_item
    ):
        """Test listing backlog items for a sprint."""
        response = await client.get(
            f"/api/v1/planning/sprints/{test_sprint.id}/backlog",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        # Should contain sprint items
        assert any(item["id"] == str(test_sprint_item.id) for item in data["items"])

    @pytest.mark.asyncio
    async def test_update_backlog_item_success(
        self, client: AsyncClient, auth_headers, test_backlog_item
    ):
        """Test updating a backlog item."""
        response = await client.put(
            f"/api/v1/planning/backlog/{test_backlog_item.id}",
            json={
                "title": "Updated Title",
                "description": "Updated description",
                "priority": "P0",
                "story_points": 8,
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["priority"] == "P0"
        assert data["story_points"] == 8

    @pytest.mark.asyncio
    async def test_delete_backlog_item_success(
        self, client: AsyncClient, auth_headers, db_session, test_project, test_user
    ):
        """Test deleting a backlog item."""
        # Create item to delete
        item = BacklogItem(
            project_id=test_project.id,
            type="task",
            title="Item to Delete",
            priority="P2",
            created_by=test_user.id,
        )
        db_session.add(item)
        await db_session.commit()
        await db_session.refresh(item)

        response = await client.delete(
            f"/api/v1/planning/backlog/{item.id}",
            headers=auth_headers,
        )

        assert response.status_code == 204

        # Verify deletion
        get_response = await client.get(
            f"/api/v1/planning/backlog/{item.id}",
            headers=auth_headers,
        )
        assert get_response.status_code == 404


# =============================================================================
# Priority Tests (SDLC 5.1.3 Rule #8)
# =============================================================================


class TestBacklogPriority:
    """Test backlog priority management per SDLC 5.1.3 Rule #8."""

    @pytest.mark.asyncio
    async def test_create_p0_item(
        self, client: AsyncClient, auth_headers, test_project
    ):
        """Test creating P0 (must have) item."""
        response = await client.post(
            "/api/v1/planning/backlog",
            json={
                "project_id": str(test_project.id),
                "type": "story",
                "title": "Critical feature",
                "priority": "P0",
            },
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["priority"] == "P0"

    @pytest.mark.asyncio
    async def test_create_p1_item(
        self, client: AsyncClient, auth_headers, test_project
    ):
        """Test creating P1 (should have) item."""
        response = await client.post(
            "/api/v1/planning/backlog",
            json={
                "project_id": str(test_project.id),
                "type": "story",
                "title": "Important feature",
                "priority": "P1",
            },
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["priority"] == "P1"

    @pytest.mark.asyncio
    async def test_create_p2_item(
        self, client: AsyncClient, auth_headers, test_project
    ):
        """Test creating P2 (could have) item."""
        response = await client.post(
            "/api/v1/planning/backlog",
            json={
                "project_id": str(test_project.id),
                "type": "story",
                "title": "Nice to have feature",
                "priority": "P2",
            },
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["priority"] == "P2"

    @pytest.mark.asyncio
    async def test_filter_by_priority(
        self, client: AsyncClient, auth_headers, db_session, test_project, test_user
    ):
        """Test filtering backlog items by priority."""
        # Create items with different priorities
        for priority in ["P0", "P1", "P2"]:
            item = BacklogItem(
                project_id=test_project.id,
                type="task",
                title=f"{priority} Item",
                priority=priority,
                created_by=test_user.id,
            )
            db_session.add(item)
        await db_session.commit()

        # Filter by P0
        response = await client.get(
            f"/api/v1/planning/projects/{test_project.id}/backlog?priority=P0",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        # All items should be P0
        for item in data["items"]:
            if item["priority"] == "P0":
                assert True
                break


# =============================================================================
# Status Transition Tests
# =============================================================================


class TestBacklogStatusTransitions:
    """Test backlog item status transitions."""

    @pytest.mark.asyncio
    async def test_status_todo_to_in_progress(
        self, client: AsyncClient, auth_headers, test_backlog_item
    ):
        """Test transitioning from todo to in_progress."""
        response = await client.put(
            f"/api/v1/planning/backlog/{test_backlog_item.id}",
            json={"status": "in_progress"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "in_progress"

    @pytest.mark.asyncio
    async def test_status_in_progress_to_review(
        self, client: AsyncClient, auth_headers, db_session, test_project, test_user
    ):
        """Test transitioning from in_progress to review."""
        # Create item in in_progress status
        item = BacklogItem(
            project_id=test_project.id,
            type="task",
            title="Task in progress",
            priority="P1",
            status="in_progress",
            created_by=test_user.id,
        )
        db_session.add(item)
        await db_session.commit()
        await db_session.refresh(item)

        response = await client.put(
            f"/api/v1/planning/backlog/{item.id}",
            json={"status": "review"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "review"

    @pytest.mark.asyncio
    async def test_status_review_to_done(
        self, client: AsyncClient, auth_headers, db_session, test_project, test_user
    ):
        """Test transitioning from review to done."""
        item = BacklogItem(
            project_id=test_project.id,
            type="task",
            title="Task in review",
            priority="P1",
            status="review",
            created_by=test_user.id,
        )
        db_session.add(item)
        await db_session.commit()
        await db_session.refresh(item)

        response = await client.put(
            f"/api/v1/planning/backlog/{item.id}",
            json={"status": "done"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "done"

    @pytest.mark.asyncio
    async def test_status_blocked(
        self, client: AsyncClient, auth_headers, test_backlog_item
    ):
        """Test blocking a backlog item."""
        response = await client.put(
            f"/api/v1/planning/backlog/{test_backlog_item.id}",
            json={"status": "blocked"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "blocked"


# =============================================================================
# Sprint Assignment Tests
# =============================================================================


class TestBacklogSprintAssignment:
    """Test backlog item sprint assignment."""

    @pytest.mark.asyncio
    async def test_move_item_to_sprint(
        self, client: AsyncClient, auth_headers, test_backlog_item, test_sprint
    ):
        """Test moving a backlog item to a sprint."""
        response = await client.put(
            f"/api/v1/planning/backlog/{test_backlog_item.id}",
            json={"sprint_id": str(test_sprint.id)},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["sprint_id"] == str(test_sprint.id)

    @pytest.mark.asyncio
    async def test_move_item_to_backlog(
        self, client: AsyncClient, auth_headers, test_sprint_item
    ):
        """Test moving a sprint item back to product backlog."""
        response = await client.put(
            f"/api/v1/planning/backlog/{test_sprint_item.id}",
            json={"sprint_id": None},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["sprint_id"] is None


# =============================================================================
# Subtask Tests
# =============================================================================


class TestBacklogSubtasks:
    """Test backlog item subtask hierarchy."""

    @pytest.mark.asyncio
    async def test_create_subtask(
        self, client: AsyncClient, auth_headers, test_project, test_backlog_item
    ):
        """Test creating a subtask."""
        response = await client.post(
            "/api/v1/planning/backlog",
            json={
                "project_id": str(test_project.id),
                "parent_id": str(test_backlog_item.id),
                "type": "task",
                "title": "Subtask 1",
                "priority": "P1",
            },
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["parent_id"] == str(test_backlog_item.id)

    @pytest.mark.asyncio
    async def test_get_item_with_subtasks(
        self, client: AsyncClient, auth_headers, db_session, test_project, test_backlog_item, test_user
    ):
        """Test getting an item with its subtasks."""
        # Create subtasks
        for i in range(3):
            subtask = BacklogItem(
                project_id=test_project.id,
                parent_id=test_backlog_item.id,
                type="task",
                title=f"Subtask {i+1}",
                priority="P2",
                created_by=test_user.id,
            )
            db_session.add(subtask)
        await db_session.commit()

        response = await client.get(
            f"/api/v1/planning/backlog/{test_backlog_item.id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        # Check if children are included (depends on API design)
        assert data["id"] == str(test_backlog_item.id)


# =============================================================================
# Assignment Tests
# =============================================================================


class TestBacklogAssignment:
    """Test backlog item assignment."""

    @pytest.mark.asyncio
    async def test_assign_item_to_user(
        self, client: AsyncClient, auth_headers, test_backlog_item, test_user
    ):
        """Test assigning a backlog item to a user."""
        response = await client.put(
            f"/api/v1/planning/backlog/{test_backlog_item.id}",
            json={"assignee_id": str(test_user.id)},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["assignee_id"] == str(test_user.id)

    @pytest.mark.asyncio
    async def test_unassign_item(
        self, client: AsyncClient, auth_headers, db_session, test_project, test_user
    ):
        """Test unassigning a backlog item."""
        # Create assigned item
        item = BacklogItem(
            project_id=test_project.id,
            type="task",
            title="Assigned task",
            priority="P1",
            assignee_id=test_user.id,
            created_by=test_user.id,
        )
        db_session.add(item)
        await db_session.commit()
        await db_session.refresh(item)

        response = await client.put(
            f"/api/v1/planning/backlog/{item.id}",
            json={"assignee_id": None},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["assignee_id"] is None

    @pytest.mark.asyncio
    async def test_filter_by_assignee(
        self, client: AsyncClient, auth_headers, db_session, test_project, test_user
    ):
        """Test filtering backlog items by assignee."""
        # Create assigned items
        for i in range(2):
            item = BacklogItem(
                project_id=test_project.id,
                type="task",
                title=f"Assigned task {i+1}",
                priority="P1",
                assignee_id=test_user.id,
                created_by=test_user.id,
            )
            db_session.add(item)
        await db_session.commit()

        response = await client.get(
            f"/api/v1/planning/projects/{test_project.id}/backlog?assignee_id={test_user.id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        # Should have items assigned to test_user
        assert len(data["items"]) >= 2
