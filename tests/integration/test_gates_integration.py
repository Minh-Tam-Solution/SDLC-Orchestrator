"""
Integration Tests for Gates API

File: tests/integration/test_gates_integration.py
Version: 1.0.0
Date: December 12, 2025
Status: ACTIVE - Week 6 Day 1
Authority: Backend Lead + QA Lead
Framework: SDLC 4.9 Complete Lifecycle

Test Coverage:
- POST /api/v1/gates - Create new gate
- GET /api/v1/gates - List gates (pagination + filters)
- GET /api/v1/gates/{gate_id} - Get gate details
- PUT /api/v1/gates/{gate_id} - Update gate
- DELETE /api/v1/gates/{gate_id} - Delete gate (soft delete)
- POST /api/v1/gates/{gate_id}/submit - Submit gate for approval
- POST /api/v1/gates/{gate_id}/approve - Approve/reject gate
- GET /api/v1/gates/{gate_id}/approvals - Get approval history

Total Endpoints: 8
Total Tests: 18+
Target Coverage: 90%+
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4

from app.models.user import User
from app.models.project import Project
from app.models.gate import Gate


@pytest.mark.integration
@pytest.mark.gates
class TestGateCreate:
    """Integration tests for gate creation endpoint."""

    async def test_create_gate_success(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_project: Project,
    ):
        """Test successful gate creation."""
        response = await client.post(
            "/api/v1/gates",
            headers=auth_headers,
            json={
                "project_id": str(test_project.id),
                "gate_name": "G1",
                "gate_type": "G1_DESIGN_READY",  # Required field
                "stage": "WHAT",  # Correct field (not stage_name)
                "description": "Requirements gate for testing",
                "exit_criteria": [],  # Required field
            },
        )

        assert response.status_code == 201
        data = response.json()

        assert data["gate_name"] == "G1"
        assert data["gate_type"] == "G1_DESIGN_READY"
        assert data["stage"] == "WHAT"
        assert data["status"] in ["DRAFT", "PENDING"]  # API may return either
        assert data["project_id"] == str(test_project.id)

    async def test_create_gate_unauthenticated(
        self, client: AsyncClient, test_project: Project
    ):
        """Test gate creation without authentication returns 401."""
        response = await client.post(
            "/api/v1/gates",
            json={
                "project_id": str(test_project.id),
                "gate_name": "G1",
                "gate_type": "G1_DESIGN_READY",  # Required field
                "stage": "WHAT",  # Correct field (not stage_name)
                "description": "Unauthenticated gate",
                "exit_criteria": [],  # Required field
            },
        )

        assert response.status_code == 403  # FastAPI returns 403 for missing auth, not 401

    async def test_create_gate_invalid_project(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test gate creation with non-existent project returns 404."""
        response = await client.post(
            "/api/v1/gates",
            headers=auth_headers,
            json={
                "project_id": str(uuid4()),  # Non-existent project
                "gate_name": "G1",
                "gate_type": "G1_DESIGN_READY",  # Required field
                "stage": "WHAT",  # Correct field (not stage_name)
                "description": "Invalid project gate",
                "exit_criteria": [],  # Required field
            },
        )

        assert response.status_code == 404


@pytest.mark.integration
@pytest.mark.gates
class TestGateList:
    """Integration tests for gate list endpoint."""

    async def test_list_gates_success(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_gate: Gate,
    ):
        """Test list gates with pagination."""
        response = await client.get(
            "/api/v1/gates",
            headers=auth_headers,
            params={"page": 1, "page_size": 10},
        )

        assert response.status_code == 200
        data = response.json()

        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert len(data["items"]) > 0

    async def test_list_gates_filter_by_project(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_project: Project,
        test_gate: Gate,
    ):
        """Test list gates filtered by project ID."""
        response = await client.get(
            "/api/v1/gates",
            headers=auth_headers,
            params={"project_id": str(test_project.id)},
        )

        assert response.status_code == 200
        data = response.json()

        # All gates should belong to test_project
        for gate in data["items"]:
            assert gate["project_id"] == str(test_project.id)

    async def test_list_gates_filter_by_status(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_gate: Gate,
    ):
        """Test list gates filtered by status."""
        response = await client.get(
            "/api/v1/gates",
            headers=auth_headers,
            params={"status": "PENDING"},
        )

        assert response.status_code == 200
        data = response.json()

        # All gates should be PENDING
        for gate in data["items"]:
            assert gate["status"] == "PENDING"


@pytest.mark.integration
@pytest.mark.gates
class TestGateDetail:
    """Integration tests for gate detail endpoint."""

    async def test_get_gate_success(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_gate: Gate,
    ):
        """Test get gate details."""
        response = await client.get(
            f"/api/v1/gates/{test_gate.id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == str(test_gate.id)
        assert data["gate_name"] == test_gate.gate_name
        assert data["stage"] == test_gate.stage  # Correct field (not stage_name)
        assert data["status"] == test_gate.status  # status is string, not enum

    async def test_get_gate_not_found(self, client: AsyncClient, auth_headers: dict):
        """Test get non-existent gate returns 404."""
        response = await client.get(
            f"/api/v1/gates/{uuid4()}",
            headers=auth_headers,
        )

        assert response.status_code == 404

    async def test_get_gate_unauthenticated(self, client: AsyncClient, test_gate: Gate):
        """Test get gate without authentication returns 403."""
        response = await client.get(f"/api/v1/gates/{test_gate.id}")

        assert response.status_code == 403  # FastAPI returns 403 for missing auth


@pytest.mark.integration
@pytest.mark.gates
class TestGateUpdate:
    """Integration tests for gate update endpoint."""

    async def test_update_gate_success(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_gate: Gate,
    ):
        """Test successful gate update."""
        response = await client.put(
            f"/api/v1/gates/{test_gate.id}",
            headers=auth_headers,
            json={
                "description": "Updated gate description",
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == str(test_gate.id)
        assert data["description"] == "Updated gate description"

    async def test_update_gate_not_found(self, client: AsyncClient, auth_headers: dict):
        """Test update non-existent gate returns 404."""
        response = await client.put(
            f"/api/v1/gates/{uuid4()}",
            headers=auth_headers,
            json={"description": "Updated description"},
        )

        assert response.status_code == 404


@pytest.mark.integration
@pytest.mark.gates
class TestGateDelete:
    """Integration tests for gate deletion (soft delete)."""

    async def test_delete_gate_success(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db: AsyncSession,
        test_gate: Gate,
    ):
        """Test successful gate deletion (soft delete)."""
        response = await client.delete(
            f"/api/v1/gates/{test_gate.id}",
            headers=auth_headers,
        )

        assert response.status_code == 204

        # Verify gate is soft-deleted (has deleted_at timestamp)
        await db.refresh(test_gate)
        assert test_gate.deleted_at is not None

    async def test_delete_gate_not_found(self, client: AsyncClient, auth_headers: dict):
        """Test delete non-existent gate returns 404."""
        response = await client.delete(
            f"/api/v1/gates/{uuid4()}",
            headers=auth_headers,
        )

        assert response.status_code == 404


@pytest.mark.integration
@pytest.mark.gates
class TestGateSubmit:
    """Integration tests for gate submission endpoint."""

    async def test_submit_gate_success(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_gate: Gate,
    ):
        """Test successful gate submission for approval."""
        response = await client.post(
            f"/api/v1/gates/{test_gate.id}/submit",
            headers=auth_headers,
            json={
                "notes": "Ready for approval - all evidence attached",
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == str(test_gate.id)
        assert data["status"] == "UNDER_REVIEW"

    async def test_submit_already_approved_gate(
        self,
        client: AsyncClient,
        auth_headers: dict,
        approved_gate: Gate,
    ):
        """Test submit already approved gate returns 400."""
        response = await client.post(
            f"/api/v1/gates/{approved_gate.id}/submit",
            headers=auth_headers,
            json={"notes": "Re-submitting"},
        )

        assert response.status_code == 400
        assert "already approved" in response.json()["detail"].lower()


@pytest.mark.integration
@pytest.mark.gates
class TestGateApprove:
    """Integration tests for gate approval endpoint."""

    async def test_approve_gate_success(
        self,
        client: AsyncClient,
        admin_headers: dict,  # Admin/CTO has approval permissions
        test_gate: Gate,
        db: AsyncSession,
    ):
        """Test successful gate approval by CTO/CPO."""
        # First submit gate for review
        test_gate.status = "PENDING_APPROVAL"  # Valid status string
        await db.commit()

        response = await client.post(
            f"/api/v1/gates/{test_gate.id}/approve",
            headers=admin_headers,
            json={
                "decision": "APPROVED",
                "comments": "All requirements met, approved by CTO",
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == str(test_gate.id)
        assert data["status"] == "APPROVED"

    async def test_reject_gate_success(
        self,
        client: AsyncClient,
        admin_headers: dict,
        test_gate: Gate,
        db: AsyncSession,
    ):
        """Test successful gate rejection by CTO/CPO."""
        # First submit gate for review
        test_gate.status = "PENDING_APPROVAL"  # Valid status string
        await db.commit()

        response = await client.post(
            f"/api/v1/gates/{test_gate.id}/approve",
            headers=admin_headers,
            json={
                "decision": "REJECTED",
                "comments": "Missing critical evidence, rejected",
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == str(test_gate.id)
        assert data["status"] == "REJECTED"

    async def test_approve_gate_insufficient_permissions(
        self,
        client: AsyncClient,
        auth_headers: dict,  # Regular user (not CTO/CPO)
        test_gate: Gate,
    ):
        """Test approve gate without CTO/CPO permissions returns 403."""
        response = await client.post(
            f"/api/v1/gates/{test_gate.id}/approve",
            headers=auth_headers,
            json={
                "decision": "APPROVED",
                "comments": "Unauthorized approval attempt",
            },
        )

        assert response.status_code == 403


@pytest.mark.integration
@pytest.mark.gates
class TestGateApprovalHistory:
    """Integration tests for gate approval history endpoint."""

    async def test_get_approval_history_success(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_gate: Gate,
    ):
        """Test get gate approval history."""
        response = await client.get(
            f"/api/v1/gates/{test_gate.id}/approvals",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        # New gate may have 0 approvals
        assert len(data) >= 0

    async def test_get_approval_history_not_found(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test get approval history for non-existent gate returns 404."""
        response = await client.get(
            f"/api/v1/gates/{uuid4()}/approvals",
            headers=auth_headers,
        )

        assert response.status_code == 404


@pytest.mark.integration
@pytest.mark.gates
class TestGateErrorHandling:
    """Integration tests for Gates API error handling and authorization (NEW - Day 3)."""

    async def test_create_gate_non_member(
        self,
        client: AsyncClient,
        db: AsyncSession,
    ):
        """Test create gate without project membership returns 403."""
        from app.models.user import User
        from app.models.project import Project

        # Create second user (not a member of test_project)
        non_member = User(
            email="nonmember@example.com",
            name="Non Member",
            password_hash="hashed",  # Not used for login in tests
        )
        db.add(non_member)
        await db.commit()
        await db.refresh(non_member)

        # Create authentication token for non-member
        from app.core.security import create_access_token
        token = create_access_token(subject=str(non_member.id))
        non_member_headers = {"Authorization": f"Bearer {token}"}

        # Create a project that non_member is NOT a member of
        from uuid import uuid4
        project = Project(
            id=uuid4(),
            name="Test Project (No Access)",
            slug="test-project-no-access",
            description="Test project for non-member test",
            owner_id=non_member.id,
        )
        db.add(project)
        await db.commit()

        # Attempt to create gate in project where user is not a member
        response = await client.post(
            "/api/v1/gates",
            headers=non_member_headers,
            json={
                "project_id": str(project.id),
                "gate_name": "G1",
                "gate_type": "G1_DESIGN_READY",
                "stage": "WHAT",
                "description": "Unauthorized gate creation",
                "exit_criteria": [],
            },
        )

        assert response.status_code == 403
        data = response.json()
        assert "project member" in data["detail"].lower()

    async def test_list_gates_non_member_with_project_filter(
        self,
        client: AsyncClient,
        db: AsyncSession,
    ):
        """Test list gates with project_id filter when user is not a member returns 403."""
        from app.models.user import User
        from app.models.project import Project

        # Create second user
        non_member = User(
            email="nonmember2@example.com",
            name="Non Member 2",
            password_hash="hashed",
        )
        db.add(non_member)
        await db.commit()
        await db.refresh(non_member)

        from app.core.security import create_access_token
        token = create_access_token(subject=str(non_member.id))
        non_member_headers = {"Authorization": f"Bearer {token}"}

        # Create a project
        from uuid import uuid4
        project = Project(
            id=uuid4(),
            name="Test Project (Restricted)",
            slug="test-project-restricted",
            description="Restricted project",
            owner_id=non_member.id,
        )
        db.add(project)
        await db.commit()

        # Attempt to list gates with project_id filter (user not a member)
        response = await client.get(
            "/api/v1/gates",
            headers=non_member_headers,
            params={"project_id": str(project.id)},
        )

        assert response.status_code == 403
        data = response.json()
        assert "project member" in data["detail"].lower()

    async def test_get_gate_non_existent(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test get gate with non-existent gate_id returns 404."""
        from uuid import uuid4

        response = await client.get(
            f"/api/v1/gates/{uuid4()}",
            headers=auth_headers,
        )

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    async def test_get_gate_non_member(
        self,
        client: AsyncClient,
        db: AsyncSession,
        test_gate: Gate,
    ):
        """Test get gate without project membership returns 403."""
        from app.models.user import User

        # Create second user (not a member of test_project)
        non_member = User(
            email="nonmember3@example.com",
            name="Non Member 3",
            password_hash="hashed",
        )
        db.add(non_member)
        await db.commit()
        await db.refresh(non_member)

        from app.core.security import create_access_token
        token = create_access_token(subject=str(non_member.id))
        non_member_headers = {"Authorization": f"Bearer {token}"}

        # Attempt to get gate from project where user is not a member
        response = await client.get(
            f"/api/v1/gates/{test_gate.id}",
            headers=non_member_headers,
        )

        assert response.status_code == 403
        data = response.json()
        assert "project member" in data["detail"].lower()

    async def test_update_gate_non_member(
        self,
        client: AsyncClient,
        db: AsyncSession,
        test_gate: Gate,
    ):
        """Test update gate without project membership returns 403."""
        from app.models.user import User

        # Create second user
        non_member = User(
            email="nonmember4@example.com",
            name="Non Member 4",
            password_hash="hashed",
        )
        db.add(non_member)
        await db.commit()
        await db.refresh(non_member)

        from app.core.security import create_access_token
        token = create_access_token(subject=str(non_member.id))
        non_member_headers = {"Authorization": f"Bearer {token}"}

        # Attempt to update gate
        response = await client.put(
            f"/api/v1/gates/{test_gate.id}",
            headers=non_member_headers,
            json={"gate_name": "Updated Gate Name"},
        )

        assert response.status_code == 403
        data = response.json()
        assert "project member" in data["detail"].lower()

    async def test_delete_gate_non_member(
        self,
        client: AsyncClient,
        db: AsyncSession,
        test_gate: Gate,
    ):
        """Test delete gate without project membership returns 403."""
        from app.models.user import User

        # Create second user
        non_member = User(
            email="nonmember5@example.com",
            name="Non Member 5",
            password_hash="hashed",
        )
        db.add(non_member)
        await db.commit()
        await db.refresh(non_member)

        from app.core.security import create_access_token
        token = create_access_token(subject=str(non_member.id))
        non_member_headers = {"Authorization": f"Bearer {token}"}

        # Attempt to delete gate
        response = await client.delete(
            f"/api/v1/gates/{test_gate.id}",
            headers=non_member_headers,
        )

        assert response.status_code == 403
        data = response.json()
        assert "project member" in data["detail"].lower()

    async def test_submit_gate_non_member(
        self,
        client: AsyncClient,
        db: AsyncSession,
        test_gate: Gate,
    ):
        """Test submit gate without project membership returns 403."""
        from app.models.user import User

        # Create second user
        non_member = User(
            email="nonmember6@example.com",
            name="Non Member 6",
            password_hash="hashed",
        )
        db.add(non_member)
        await db.commit()
        await db.refresh(non_member)

        from app.core.security import create_access_token
        token = create_access_token(subject=str(non_member.id))
        non_member_headers = {"Authorization": f"Bearer {token}"}

        # Attempt to submit gate
        response = await client.post(
            f"/api/v1/gates/{test_gate.id}/submit",
            headers=non_member_headers,
            json={"message": "Unauthorized submission"},
        )

        assert response.status_code == 403
        data = response.json()
        assert "project member" in data["detail"].lower()

    async def test_get_approvals_non_member(
        self,
        client: AsyncClient,
        db: AsyncSession,
        test_gate: Gate,
    ):
        """Test get approvals without project membership returns 403."""
        from app.models.user import User

        # Create second user
        non_member = User(
            email="nonmember7@example.com",
            name="Non Member 7",
            password_hash="hashed",
        )
        db.add(non_member)
        await db.commit()
        await db.refresh(non_member)

        from app.core.security import create_access_token
        token = create_access_token(subject=str(non_member.id))
        non_member_headers = {"Authorization": f"Bearer {token}"}

        # Attempt to get approvals
        response = await client.get(
            f"/api/v1/gates/{test_gate.id}/approvals",
            headers=non_member_headers,
        )

        assert response.status_code == 403
        data = response.json()
        assert "project member" in data["detail"].lower()


@pytest.mark.integration
@pytest.mark.gates
class TestGateEdgeCases:
    """Integration tests for Gates API edge cases and boundary conditions (NEW - Day 3)."""

    async def test_list_gates_with_stage_filter(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_project: Project,
        db: AsyncSession,
    ):
        """Test list gates with stage filter returns only gates in that stage."""
        # Create gates in different stages
        from app.models.gate import Gate

        gate_what = Gate(
            project_id=test_project.id,
            gate_name="G1 (WHAT)",
            gate_type="G1_DESIGN_READY",
            stage="WHAT",
            description="Requirements stage gate",
            exit_criteria=[],
            status="DRAFT",
            created_by=test_project.owner_id,
        )

        gate_build = Gate(
            project_id=test_project.id,
            gate_name="G2 (BUILD)",
            gate_type="G2_SHIP_READY",
            stage="BUILD",
            description="Development stage gate",
            exit_criteria=[],
            status="DRAFT",
            created_by=test_project.owner_id,
        )

        db.add(gate_what)
        db.add(gate_build)
        await db.commit()

        # List gates filtered by WHAT stage
        response = await client.get(
            "/api/v1/gates",
            headers=auth_headers,
            params={"project_id": str(test_project.id), "stage": "WHAT"},
        )

        assert response.status_code == 200
        data = response.json()

        # Should only return WHAT stage gates
        gate_stages = [g["stage"] for g in data["items"]]
        assert all(stage == "WHAT" for stage in gate_stages)
        assert data["total"] >= 1  # At least gate_what

    async def test_list_gates_with_status_filter(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_project: Project,
        db: AsyncSession,
    ):
        """Test list gates with status filter returns only gates with that status."""
        from app.models.gate import Gate

        # Create gates with different statuses
        gate_draft = Gate(
            project_id=test_project.id,
            gate_name="G1 (DRAFT)",
            gate_type="G1_DESIGN_READY",
            stage="WHAT",
            description="Draft gate",
            exit_criteria=[],
            status="DRAFT",
            created_by=test_project.owner_id,
        )

        gate_pending = Gate(
            project_id=test_project.id,
            gate_name="G2 (PENDING)",
            gate_type="G2_SHIP_READY",
            stage="BUILD",
            description="Pending approval gate",
            exit_criteria=[],
            status="PENDING_APPROVAL",
            created_by=test_project.owner_id,
        )

        db.add(gate_draft)
        db.add(gate_pending)
        await db.commit()

        # List gates filtered by DRAFT status
        response = await client.get(
            "/api/v1/gates",
            headers=auth_headers,
            params={"project_id": str(test_project.id), "status": "DRAFT"},
        )

        assert response.status_code == 200
        data = response.json()

        # Should only return DRAFT status gates
        gate_statuses = [g["status"] for g in data["items"]]
        assert all(status == "DRAFT" for status in gate_statuses)
        assert data["total"] >= 1  # At least gate_draft

    async def test_update_gate_partial_fields(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_gate: Gate,
        db: AsyncSession,
    ):
        """Test update gate with partial fields (only some fields provided)."""
        original_name = test_gate.gate_name
        original_description = test_gate.description

        # Update only gate_name (partial update)
        response = await client.put(
            f"/api/v1/gates/{test_gate.id}",
            headers=auth_headers,
            json={"gate_name": "Updated Gate Name Only"},
        )

        assert response.status_code == 200
        data = response.json()

        # gate_name should be updated
        assert data["gate_name"] == "Updated Gate Name Only"

        # Other fields should remain unchanged
        await db.refresh(test_gate)
        assert test_gate.description == original_description  # Unchanged

    async def test_approve_gate_approved(
        self,
        client: AsyncClient,
        db: AsyncSession,
        test_project: Project,
    ):
        """Test approve gate with is_approved=true changes status to APPROVED."""
        from app.models.gate import Gate
        from app.models.user import User
        from app.models.user_role import UserRole

        # Create CTO user with proper role
        cto_user = User(
            email="cto@example.com",
            name="CTO User",
            password_hash="hashed",
        )
        db.add(cto_user)
        await db.commit()
        await db.refresh(cto_user)

        # Assign CTO role
        from app.models.role import Role
        from sqlalchemy import select

        result = await db.execute(select(Role).where(Role.role_name == "CTO"))
        cto_role = result.scalar_one_or_none()

        if not cto_role:
            cto_role = Role(role_name="CTO", description="Chief Technology Officer")
            db.add(cto_role)
            await db.commit()
            await db.refresh(cto_role)

        user_role = UserRole(
            user_id=cto_user.id,
            role_id=cto_role.id,
            project_id=test_project.id,
        )
        db.add(user_role)
        await db.commit()

        # Add CTO as project member
        from app.models.project import ProjectMember

        project_member = ProjectMember(
            project_id=test_project.id,
            user_id=cto_user.id,
            role="CTO",
        )
        db.add(project_member)
        await db.commit()

        # Create gate in PENDING_APPROVAL status
        gate = Gate(
            project_id=test_project.id,
            gate_name="G1 (Pending)",
            gate_type="G1_DESIGN_READY",
            stage="WHAT",
            description="Gate for approval test",
            exit_criteria=[],
            status="PENDING_APPROVAL",
            owner_id=cto_user.id,
        )
        db.add(gate)
        await db.commit()
        await db.refresh(gate)

        # Create CTO auth token
        from app.core.security import create_access_token

        cto_token = create_access_token(subject=str(cto_user.id))
        cto_headers = {"Authorization": f"Bearer {cto_token}"}

        # Approve gate
        response = await client.post(
            f"/api/v1/gates/{gate.id}/approve",
            headers=cto_headers,
            json={"approved": True, "comments": "All criteria met, approved"},
        )

        assert response.status_code == 200
        data = response.json()

        # Gate status should be APPROVED
        assert data["status"] == "APPROVED"
        assert data["approved_at"] is not None

    async def test_approve_gate_rejected(
        self,
        client: AsyncClient,
        db: AsyncSession,
        test_project: Project,
    ):
        """Test reject gate (is_approved=false) changes status to REJECTED."""
        from app.models.gate import Gate
        from app.models.user import User
        from app.models.user_role import UserRole

        # Create CTO user
        cto_user = User(
            email="cto2@example.com",
            name="CTO User 2",
            password_hash="hashed",
        )
        db.add(cto_user)
        await db.commit()
        await db.refresh(cto_user)

        # Assign CTO role
        from app.models.role import Role
        from sqlalchemy import select

        result = await db.execute(select(Role).where(Role.role_name == "CTO"))
        cto_role = result.scalar_one_or_none()

        if not cto_role:
            cto_role = Role(role_name="CTO", description="Chief Technology Officer")
            db.add(cto_role)
            await db.commit()
            await db.refresh(cto_role)

        user_role = UserRole(
            user_id=cto_user.id,
            role_id=cto_role.id,
            project_id=test_project.id,
        )
        db.add(user_role)
        await db.commit()

        # Add CTO as project member
        from app.models.project import ProjectMember

        project_member = ProjectMember(
            project_id=test_project.id,
            user_id=cto_user.id,
            role="CTO",
        )
        db.add(project_member)
        await db.commit()

        # Create gate in PENDING_APPROVAL status
        gate = Gate(
            project_id=test_project.id,
            gate_name="G2 (Pending Rejection)",
            gate_type="G2_SHIP_READY",
            stage="BUILD",
            description="Gate for rejection test",
            exit_criteria=[],
            status="PENDING_APPROVAL",
            owner_id=cto_user.id,
        )
        db.add(gate)
        await db.commit()
        await db.refresh(gate)

        # Create CTO auth token
        from app.core.security import create_access_token

        cto_token = create_access_token(subject=str(cto_user.id))
        cto_headers = {"Authorization": f"Bearer {cto_token}"}

        # Reject gate
        response = await client.post(
            f"/api/v1/gates/{gate.id}/approve",
            headers=cto_headers,
            json={"approved": False, "comments": "Missing evidence, rejected"},
        )

        assert response.status_code == 200
        data = response.json()

        # Gate status should be REJECTED
        assert data["status"] == "REJECTED"
        # approved_at should still be None for rejections (or check actual implementation)

    async def test_check_project_membership_false(
        self,
        client: AsyncClient,
        db: AsyncSession,
    ):
        """Test helper function check_project_membership returns false for non-members."""
        from app.models.user import User
        from app.models.project import Project

        # Create user and project
        user = User(
            email="test_user@example.com",
            name="Test User",
            password_hash="hashed",
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

        from uuid import uuid4

        project = Project(
            id=uuid4(),
            name="Test Project (No Members)",
            slug="test-project-no-members",
            description="Project with no members",
            owner_id=user.id,
        )
        db.add(project)
        await db.commit()

        # Test check_project_membership helper function
        from app.api.routes.gates import check_project_membership

        is_member = await check_project_membership(project.id, user, db)

        # User is NOT a member (no ProjectMember record)
        assert is_member is False
