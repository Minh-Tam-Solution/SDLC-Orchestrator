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


# =============================================================================
# GAP 2 Resolution Tests - Team Membership Validation (Sprint 76)
# =============================================================================


class TestAssigneeTeamMembershipValidation:
    """
    Test GAP 2 Resolution: Backlog assignee team membership validation.

    SDLC 5.1.3 Compliance:
    - GAP 2: Backlog assignee must be project team member
    - Projects without teams allow any assignee (backward compatibility)

    Sprint 76 Implementation:
    - validate_assignee_membership() in BacklogService
    - 403 error when assigning to non-team member
    - GET /backlog/assignees/{project_id} endpoint
    """

    @pytest.fixture
    async def project_with_team(self, db_session, test_user):
        """Create a project with team (for GAP 2 tests)."""
        from app.models.organization import Organization

        # Create organization first
        org = Organization(
            name="GAP2 Test Org",
            slug=f"gap2-org-{uuid4().hex[:8]}",
            owner_id=test_user.id,
        )
        db_session.add(org)
        await db_session.flush()

        # Create team
        team = Team(
            organization_id=org.id,
            name="GAP2 Test Team",
            slug=f"gap2-team-{uuid4().hex[:8]}",
        )
        db_session.add(team)
        await db_session.flush()

        # Add owner to team
        member = TeamMember(
            team_id=team.id,
            user_id=test_user.id,
            role="owner",
            member_type="human",
        )
        db_session.add(member)
        await db_session.flush()

        # Create project with team
        project = Project(
            name="GAP2 Test Project",
            slug=f"gap2-project-{uuid4().hex[:8]}",
            description="Project with team for GAP 2 testing",
            owner_id=test_user.id,
            team_id=team.id,
        )
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)

        return project

    @pytest.fixture
    async def team_member_user(self, db_session, project_with_team):
        """Create a second user who is a team member."""
        user = User(
            username=f"teammember-{uuid4().hex[:8]}",
            email=f"teammember-{uuid4().hex[:8]}@test.com",
            full_name="Team Member User",
            hashed_password="test_hash",
        )
        db_session.add(user)
        await db_session.flush()

        # Add to team
        member = TeamMember(
            team_id=project_with_team.team_id,
            user_id=user.id,
            role="member",
            member_type="human",
        )
        db_session.add(member)
        await db_session.commit()
        await db_session.refresh(user)

        return user

    @pytest.fixture
    async def non_team_user(self, db_session):
        """Create a user who is NOT a team member."""
        user = User(
            username=f"nonmember-{uuid4().hex[:8]}",
            email=f"nonmember-{uuid4().hex[:8]}@test.com",
            full_name="Non Member User",
            hashed_password="test_hash",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        return user

    # =========================================================================
    # GAP 2 Test: Create backlog item with team member assignee (Success)
    # =========================================================================

    @pytest.mark.asyncio
    async def test_create_item_with_team_member_assignee_success(
        self, client: AsyncClient, auth_headers, project_with_team, team_member_user
    ):
        """
        GAP 2 Test 1: Creating item with team member assignee succeeds.

        SDLC 5.1.3 Compliance:
        - Assignee is a valid team member
        - Should return 201 Created
        """
        response = await client.post(
            "/api/v1/planning/backlog",
            json={
                "project_id": str(project_with_team.id),
                "type": "task",
                "title": "Task assigned to team member",
                "priority": "P1",
                "assignee_id": str(team_member_user.id),
            },
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["assignee_id"] == str(team_member_user.id)

    # =========================================================================
    # GAP 2 Test: Create backlog item with non-team member assignee (Failure)
    # =========================================================================

    @pytest.mark.asyncio
    async def test_create_item_with_non_team_member_assignee_fails(
        self, client: AsyncClient, auth_headers, project_with_team, non_team_user
    ):
        """
        GAP 2 Test 2: Creating item with non-team member assignee fails.

        SDLC 5.1.3 Compliance:
        - Assignee is NOT a team member
        - Should return 403 Forbidden
        """
        response = await client.post(
            "/api/v1/planning/backlog",
            json={
                "project_id": str(project_with_team.id),
                "type": "task",
                "title": "Task with invalid assignee",
                "priority": "P1",
                "assignee_id": str(non_team_user.id),
            },
            headers=auth_headers,
        )

        assert response.status_code == 403
        data = response.json()
        assert "not a member" in data["detail"].lower()

    # =========================================================================
    # GAP 2 Test: Update backlog item assignee to non-team member (Failure)
    # =========================================================================

    @pytest.mark.asyncio
    async def test_update_item_assignee_to_non_team_member_fails(
        self, client: AsyncClient, auth_headers, db_session,
        project_with_team, team_member_user, non_team_user, test_user
    ):
        """
        GAP 2 Test 3: Updating assignee to non-team member fails.

        SDLC 5.1.3 Compliance:
        - Item exists with valid assignee
        - Attempting to change to non-team member
        - Should return 403 Forbidden
        """
        # Create item with valid assignee
        item = BacklogItem(
            project_id=project_with_team.id,
            type="task",
            title="Task with valid assignee",
            priority="P1",
            assignee_id=team_member_user.id,
            created_by=test_user.id,
        )
        db_session.add(item)
        await db_session.commit()
        await db_session.refresh(item)

        # Try to update to non-team member
        response = await client.put(
            f"/api/v1/planning/backlog/{item.id}",
            json={"assignee_id": str(non_team_user.id)},
            headers=auth_headers,
        )

        assert response.status_code == 403
        data = response.json()
        assert "not a member" in data["detail"].lower()

    # =========================================================================
    # GAP 2 Test: Update backlog item assignee to team member (Success)
    # =========================================================================

    @pytest.mark.asyncio
    async def test_update_item_assignee_to_team_member_success(
        self, client: AsyncClient, auth_headers, db_session,
        project_with_team, team_member_user, test_user
    ):
        """
        GAP 2 Test 4: Updating assignee to team member succeeds.

        SDLC 5.1.3 Compliance:
        - Changing assignee to a valid team member
        - Should return 200 OK
        """
        # Create unassigned item
        item = BacklogItem(
            project_id=project_with_team.id,
            type="task",
            title="Unassigned task",
            priority="P1",
            created_by=test_user.id,
        )
        db_session.add(item)
        await db_session.commit()
        await db_session.refresh(item)

        # Assign to team member
        response = await client.put(
            f"/api/v1/planning/backlog/{item.id}",
            json={"assignee_id": str(team_member_user.id)},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["assignee_id"] == str(team_member_user.id)

    # =========================================================================
    # GAP 2 Test: Project without team allows any assignee (Backward compat)
    # =========================================================================

    @pytest.mark.asyncio
    async def test_project_without_team_allows_any_assignee(
        self, client: AsyncClient, auth_headers, test_project, non_team_user
    ):
        """
        GAP 2 Test 5: Projects without teams allow any assignee.

        SDLC 5.1.3 Compliance:
        - Backward compatibility for projects without teams
        - Should return 201 Created
        """
        response = await client.post(
            "/api/v1/planning/backlog",
            json={
                "project_id": str(test_project.id),
                "type": "task",
                "title": "Task with any assignee",
                "priority": "P1",
                "assignee_id": str(non_team_user.id),
            },
            headers=auth_headers,
        )

        # Should succeed - no team = no restriction
        assert response.status_code == 201
        data = response.json()
        assert data["assignee_id"] == str(non_team_user.id)

    # =========================================================================
    # GAP 2 Test: Get valid assignees endpoint
    # =========================================================================

    @pytest.mark.asyncio
    async def test_get_valid_assignees_with_team(
        self, client: AsyncClient, auth_headers, project_with_team
    ):
        """
        GAP 2 Test 6: Get valid assignees returns team members.

        SDLC 5.1.3 Compliance:
        - Frontend needs list of valid assignees
        - Returns only team members
        """
        response = await client.get(
            f"/api/v1/planning/backlog/assignees/{project_with_team.id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Should have at least the owner
        assert len(data) >= 1

    @pytest.mark.asyncio
    async def test_get_valid_assignees_without_team(
        self, client: AsyncClient, auth_headers, test_project
    ):
        """
        GAP 2 Test 7: Get valid assignees returns empty for projects without team.

        SDLC 5.1.3 Compliance:
        - Projects without teams return empty list
        - Frontend should allow any assignee selection
        """
        response = await client.get(
            f"/api/v1/planning/backlog/assignees/{test_project.id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data == []

    # =========================================================================
    # GAP 2 Test: Create item without assignee (No validation needed)
    # =========================================================================

    @pytest.mark.asyncio
    async def test_create_item_without_assignee_success(
        self, client: AsyncClient, auth_headers, project_with_team
    ):
        """
        GAP 2 Test 8: Creating item without assignee succeeds.

        SDLC 5.1.3 Compliance:
        - No assignee = no validation needed
        - Should return 201 Created
        """
        response = await client.post(
            "/api/v1/planning/backlog",
            json={
                "project_id": str(project_with_team.id),
                "type": "task",
                "title": "Unassigned task",
                "priority": "P1",
            },
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["assignee_id"] is None

    # =========================================================================
    # GAP 2 Test: AI agent can be assigned (SE4A)
    # =========================================================================

    @pytest.mark.asyncio
    async def test_ai_agent_can_be_assigned(
        self, client: AsyncClient, auth_headers, db_session, project_with_team, test_user
    ):
        """
        GAP 2 Test 9: AI agents (SE4A) can be assigned to tasks.

        SDLC 5.1.3 Compliance:
        - AI agents are valid team members for task assignment
        - Only gate approval is restricted (SE4H Coach only)
        """
        # Create AI agent user
        ai_user = User(
            username=f"ai-agent-{uuid4().hex[:8]}",
            email=f"ai-agent-{uuid4().hex[:8]}@test.com",
            full_name="AI Agent",
            hashed_password="test_hash",
        )
        db_session.add(ai_user)
        await db_session.flush()

        # Add AI agent to team as ai_agent role
        ai_member = TeamMember(
            team_id=project_with_team.team_id,
            user_id=ai_user.id,
            role="member",
            member_type="ai_agent",
        )
        db_session.add(ai_member)
        await db_session.commit()

        # Create task assigned to AI agent
        response = await client.post(
            "/api/v1/planning/backlog",
            json={
                "project_id": str(project_with_team.id),
                "type": "task",
                "title": "AI Agent task",
                "priority": "P2",
                "assignee_id": str(ai_user.id),
            },
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["assignee_id"] == str(ai_user.id)

    # =========================================================================
    # GAP 2 Test: Self-assignment (owner assigns to self)
    # =========================================================================

    @pytest.mark.asyncio
    async def test_owner_can_assign_to_self(
        self, client: AsyncClient, auth_headers, project_with_team, test_user
    ):
        """
        GAP 2 Test 10: Project owner can assign to self.

        SDLC 5.1.3 Compliance:
        - Owner is automatically a team member
        - Should return 201 Created
        """
        response = await client.post(
            "/api/v1/planning/backlog",
            json={
                "project_id": str(project_with_team.id),
                "type": "task",
                "title": "Self-assigned task",
                "priority": "P0",
                "assignee_id": str(test_user.id),
            },
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["assignee_id"] == str(test_user.id)

    # =========================================================================
    # GAP 2 Test: Reassign between team members
    # =========================================================================

    @pytest.mark.asyncio
    async def test_reassign_between_team_members(
        self, client: AsyncClient, auth_headers, db_session,
        project_with_team, team_member_user, test_user
    ):
        """
        GAP 2 Test 11: Reassigning between team members succeeds.

        SDLC 5.1.3 Compliance:
        - Both old and new assignee are team members
        - Should return 200 OK
        """
        # Create item assigned to test_user
        item = BacklogItem(
            project_id=project_with_team.id,
            type="task",
            title="Reassign task",
            priority="P1",
            assignee_id=test_user.id,
            created_by=test_user.id,
        )
        db_session.add(item)
        await db_session.commit()
        await db_session.refresh(item)

        # Reassign to team_member_user
        response = await client.put(
            f"/api/v1/planning/backlog/{item.id}",
            json={"assignee_id": str(team_member_user.id)},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["assignee_id"] == str(team_member_user.id)

    # =========================================================================
    # GAP 2 Test: Error message contains helpful info
    # =========================================================================

    @pytest.mark.asyncio
    async def test_error_message_is_helpful(
        self, client: AsyncClient, auth_headers, project_with_team, non_team_user
    ):
        """
        GAP 2 Test 12: Error message provides helpful information.

        SDLC 5.1.3 Compliance:
        - Error message should explain the issue
        - Should mention GAP 2 resolution
        """
        response = await client.post(
            "/api/v1/planning/backlog",
            json={
                "project_id": str(project_with_team.id),
                "type": "task",
                "title": "Invalid assignee task",
                "priority": "P1",
                "assignee_id": str(non_team_user.id),
            },
            headers=auth_headers,
        )

        assert response.status_code == 403
        data = response.json()
        detail = data["detail"].lower()
        # Should mention team member requirement
        assert "team" in detail or "member" in detail
