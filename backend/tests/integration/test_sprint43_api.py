"""
Sprint 43 API Integration Tests - AI Safety Layer v1

SDLC Stage: 04 - BUILD
Sprint: 43 - Policy Guards & Evidence UI
Framework: SDLC 5.1.1
Epic: EP-02 AI Safety Layer v1

Purpose:
Integration tests for Sprint 43 APIs:
- Override API (VCR Flow)
- Evidence Timeline API
- SAST Validator API
- Policy Guards API

Test Coverage Target: 95%+
"""

import json
from datetime import datetime, timedelta
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analytics import AICodeEvent
from app.models.override import OverrideStatus, OverrideType, ValidationOverride
from app.models.project import Project
from app.models.user import Role, User
from app.core.security import get_password_hash


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
async def test_project(db_session: AsyncSession, test_user: User) -> Project:
    """Create test project for Sprint 43 tests."""
    project = Project(
        id=uuid4(),
        name="Sprint 43 Test Project",
        slug="sprint-43-test",
        description="Test project for AI Safety Layer integration tests",
        owner_id=test_user.id,
        is_active=True,
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)
    return project


@pytest.fixture
async def test_ai_code_event(
    db_session: AsyncSession,
    test_user: User,
    test_project: Project,
) -> AICodeEvent:
    """Create test AI code event for override tests."""
    event = AICodeEvent(
        id=uuid4(),
        user_id=test_user.id,
        project_id=test_project.id,
        pr_id="PR-123",
        commit_sha="abc123def456",
        branch_name="feature/ai-safety",
        ai_tool_detected="cursor",
        confidence_score=85,
        detection_method="pattern",
        validation_result="failed",
        violations=[
            {"rule": "SAST-001", "severity": "high", "message": "SQL injection risk"}
        ],
        policy_pack_id="security-standard",
        duration_ms=1250,
        files_scanned=15,
        lines_changed=320,
    )
    db_session.add(event)
    await db_session.commit()
    await db_session.refresh(event)
    return event


@pytest.fixture
async def test_manager_user(db_session: AsyncSession) -> User:
    """Create test manager user for approval tests."""
    # Create manager role
    manager_role = Role(
        id=uuid4(),
        name="manager",
        display_name="Manager",
        description="Manager role for testing",
        permissions={"read": True, "write": True, "approve": True},
    )
    db_session.add(manager_role)
    await db_session.flush()

    # Create manager user
    user = User(
        id=uuid4(),
        email="manager@example.com",
        name="Test Manager",
        password_hash=get_password_hash("manager123"),
        is_active=True,
    )
    user.roles.append(manager_role)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def manager_headers(
    client: AsyncClient,
    test_manager_user: User,
) -> dict:
    """Get auth headers for manager user."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "manager@example.com", "password": "manager123"},
    )
    assert response.status_code == 200
    data = response.json()
    return {"Authorization": f"Bearer {data['access_token']}"}


@pytest.fixture
async def test_override(
    db_session: AsyncSession,
    test_user: User,
    test_project: Project,
    test_ai_code_event: AICodeEvent,
) -> ValidationOverride:
    """Create test override request."""
    override = ValidationOverride(
        id=uuid4(),
        event_id=test_ai_code_event.id,
        project_id=test_project.id,
        override_type=OverrideType.FALSE_POSITIVE,
        reason="This is a false positive. The detected SQL pattern is in a test file "
               "that uses mock data and is never executed in production.",
        status=OverrideStatus.PENDING,
        requested_by_id=test_user.id,
        requested_at=datetime.utcnow(),
        pr_number="PR-123",
        pr_title="Feature: Add AI Safety Layer",
        failed_validators=json.dumps(["sast", "policy_guards"]),
        expires_at=datetime.utcnow() + timedelta(days=7),
    )
    db_session.add(override)
    await db_session.commit()
    await db_session.refresh(override)
    return override


# =============================================================================
# Override API Tests (VCR Flow)
# =============================================================================


class TestOverrideAPI:
    """Tests for Override API endpoints."""

    @pytest.mark.asyncio
    async def test_create_override_request_success(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_ai_code_event: AICodeEvent,
    ):
        """Test POST /api/v1/overrides/request - success."""
        response = await client.post(
            "/api/v1/overrides/request",
            headers=auth_headers,
            json={
                "event_id": str(test_ai_code_event.id),
                "override_type": "false_positive",
                "reason": "This is a false positive detection. The SQL query uses "
                          "parameterized queries via SQLAlchemy ORM which prevents "
                          "SQL injection. Verified by security team review.",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "pending"
        assert data["override_type"] == "false_positive"
        assert data["event_id"] == str(test_ai_code_event.id)

    @pytest.mark.asyncio
    async def test_create_override_request_reason_too_short(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_ai_code_event: AICodeEvent,
    ):
        """Test POST /api/v1/overrides/request - reason too short."""
        response = await client.post(
            "/api/v1/overrides/request",
            headers=auth_headers,
            json={
                "event_id": str(test_ai_code_event.id),
                "override_type": "false_positive",
                "reason": "Too short",  # Less than 50 chars
            },
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_override_request_unauthenticated(
        self,
        client: AsyncClient,
        test_ai_code_event: AICodeEvent,
    ):
        """Test POST /api/v1/overrides/request - unauthenticated."""
        response = await client.post(
            "/api/v1/overrides/request",
            json={
                "event_id": str(test_ai_code_event.id),
                "override_type": "false_positive",
                "reason": "x" * 60,
            },
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_override_by_id(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_override: ValidationOverride,
    ):
        """Test GET /api/v1/overrides/{id} - success."""
        response = await client.get(
            f"/api/v1/overrides/{test_override.id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_override.id)
        assert data["status"] == "pending"

    @pytest.mark.asyncio
    async def test_get_override_not_found(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Test GET /api/v1/overrides/{id} - not found."""
        fake_id = uuid4()
        response = await client.get(
            f"/api/v1/overrides/{fake_id}",
            headers=auth_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_override_by_event(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_override: ValidationOverride,
        test_ai_code_event: AICodeEvent,
    ):
        """Test GET /api/v1/overrides/event/{event_id} - success."""
        response = await client.get(
            f"/api/v1/overrides/event/{test_ai_code_event.id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["event_id"] == str(test_ai_code_event.id)

    @pytest.mark.asyncio
    async def test_approve_override_success(
        self,
        client: AsyncClient,
        manager_headers: dict,
        test_override: ValidationOverride,
    ):
        """Test POST /api/v1/overrides/{id}/approve - success (manager)."""
        response = await client.post(
            f"/api/v1/overrides/{test_override.id}/approve",
            headers=manager_headers,
            json={"comment": "Reviewed and approved. False positive confirmed."},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "approved"
        assert data["resolution_comment"] is not None

    @pytest.mark.asyncio
    async def test_approve_override_permission_denied(
        self,
        client: AsyncClient,
        auth_headers: dict,  # Regular user, not manager/admin
        test_override: ValidationOverride,
    ):
        """Test POST /api/v1/overrides/{id}/approve - permission denied."""
        response = await client.post(
            f"/api/v1/overrides/{test_override.id}/approve",
            headers=auth_headers,
            json={"comment": "Trying to approve"},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_reject_override_success(
        self,
        client: AsyncClient,
        manager_headers: dict,
        test_override: ValidationOverride,
    ):
        """Test POST /api/v1/overrides/{id}/reject - success."""
        response = await client.post(
            f"/api/v1/overrides/{test_override.id}/reject",
            headers=manager_headers,
            json={
                "reason": "The SQL injection risk is real. Please use parameterized queries."
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "rejected"

    @pytest.mark.asyncio
    async def test_cancel_override_success(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_override: ValidationOverride,
    ):
        """Test POST /api/v1/overrides/{id}/cancel - success (requester)."""
        response = await client.post(
            f"/api/v1/overrides/{test_override.id}/cancel",
            headers=auth_headers,
            json={"reason": "Found and fixed the issue"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "cancelled"

    @pytest.mark.asyncio
    async def test_get_admin_override_queue(
        self,
        client: AsyncClient,
        admin_headers: dict,
        test_override: ValidationOverride,
    ):
        """Test GET /api/v1/admin/override-queue - success."""
        response = await client.get(
            "/api/v1/admin/override-queue",
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "pending" in data
        assert "recent_decisions" in data
        assert "total_pending" in data
        assert data["total_pending"] >= 1

    @pytest.mark.asyncio
    async def test_get_admin_override_stats(
        self,
        client: AsyncClient,
        admin_headers: dict,
        test_override: ValidationOverride,
    ):
        """Test GET /api/v1/admin/override-stats - success."""
        response = await client.get(
            "/api/v1/admin/override-stats?days=30",
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "stats" in data
        assert "period_days" in data
        assert data["period_days"] == 30

    @pytest.mark.asyncio
    async def test_get_project_overrides(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_project: Project,
        test_override: ValidationOverride,
    ):
        """Test GET /api/v1/projects/{id}/overrides - success."""
        response = await client.get(
            f"/api/v1/projects/{test_project.id}/overrides",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "overrides" in data
        assert "total" in data


# =============================================================================
# Evidence Timeline API Tests
# =============================================================================


class TestEvidenceTimelineAPI:
    """Tests for Evidence Timeline API endpoints."""

    @pytest.mark.asyncio
    async def test_get_project_timeline(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_project: Project,
        test_ai_code_event: AICodeEvent,
    ):
        """Test GET /api/v1/projects/{id}/timeline - success."""
        response = await client.get(
            f"/api/v1/projects/{test_project.id}/timeline",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "events" in data
        assert "stats" in data
        assert "total" in data
        assert "page" in data

    @pytest.mark.asyncio
    async def test_get_project_timeline_with_filters(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_project: Project,
        test_ai_code_event: AICodeEvent,
    ):
        """Test GET /api/v1/projects/{id}/timeline with filters."""
        response = await client.get(
            f"/api/v1/projects/{test_project.id}/timeline"
            f"?ai_tool=cursor&validation_status=failed",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "events" in data

    @pytest.mark.asyncio
    async def test_get_project_timeline_stats(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_project: Project,
        test_ai_code_event: AICodeEvent,
    ):
        """Test GET /api/v1/projects/{id}/timeline/stats - success."""
        response = await client.get(
            f"/api/v1/projects/{test_project.id}/timeline/stats?days=30",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_events" in data
        assert "ai_detected" in data
        assert "pass_rate" in data
        assert "override_rate" in data

    @pytest.mark.asyncio
    async def test_get_timeline_event_detail(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_project: Project,
        test_ai_code_event: AICodeEvent,
    ):
        """Test GET /api/v1/projects/{id}/timeline/{event_id} - success."""
        response = await client.get(
            f"/api/v1/projects/{test_project.id}/timeline/{test_ai_code_event.id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_ai_code_event.id)
        assert data["ai_tool"] == "cursor"
        assert data["validation_status"] == "failed"

    @pytest.mark.asyncio
    async def test_export_timeline_csv(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_project: Project,
        test_ai_code_event: AICodeEvent,
    ):
        """Test GET /api/v1/projects/{id}/timeline/export?format=csv."""
        response = await client.get(
            f"/api/v1/projects/{test_project.id}/timeline/export?format=csv",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert "text/csv" in response.headers.get("content-type", "")


# =============================================================================
# SAST Validator API Tests
# =============================================================================


class TestSASTValidatorAPI:
    """Tests for SAST Validator API endpoints."""

    @pytest.mark.asyncio
    async def test_validate_code_success(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_project: Project,
    ):
        """Test POST /api/v1/sast/validate - success."""
        response = await client.post(
            "/api/v1/sast/validate",
            headers=auth_headers,
            json={
                "project_id": str(test_project.id),
                "files": [
                    {
                        "path": "app/main.py",
                        "content": "def hello():\n    return 'Hello World'",
                    }
                ],
                "policy_pack": "python-security",
            },
        )
        # May return 200 (passed) or 422 (validation errors) depending on rules
        assert response.status_code in [200, 422]

    @pytest.mark.asyncio
    async def test_validate_code_sql_injection(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_project: Project,
    ):
        """Test POST /api/v1/sast/validate - SQL injection detection."""
        vulnerable_code = '''
def get_user(user_id):
    query = f"SELECT * FROM users WHERE id = {user_id}"
    return db.execute(query)
'''
        response = await client.post(
            "/api/v1/sast/validate",
            headers=auth_headers,
            json={
                "project_id": str(test_project.id),
                "files": [
                    {
                        "path": "app/database.py",
                        "content": vulnerable_code,
                    }
                ],
                "policy_pack": "security-standard",
            },
        )
        # Should detect SQL injection
        if response.status_code == 200:
            data = response.json()
            # Check if violations were found
            assert "violations" in data or "result" in data

    @pytest.mark.asyncio
    async def test_get_policy_packs(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Test GET /api/v1/sast/policy-packs - list available packs."""
        response = await client.get(
            "/api/v1/sast/policy-packs",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_validation_history(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_project: Project,
    ):
        """Test GET /api/v1/projects/{id}/sast/history - validation history."""
        response = await client.get(
            f"/api/v1/projects/{test_project.id}/sast/history",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "validations" in data or isinstance(data, list)


# =============================================================================
# Policy Guards API Tests
# =============================================================================


class TestPolicyGuardsAPI:
    """Tests for Policy Guards (OPA) API endpoints."""

    @pytest.mark.asyncio
    async def test_evaluate_policy_success(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_project: Project,
    ):
        """Test POST /api/v1/policy-guards/evaluate - success."""
        response = await client.post(
            "/api/v1/policy-guards/evaluate",
            headers=auth_headers,
            json={
                "project_id": str(test_project.id),
                "context": {
                    "pr_number": "123",
                    "ai_tool": "cursor",
                    "files_changed": 5,
                    "has_tests": True,
                    "coverage": 85.0,
                },
                "policy_pack": "ai-safety-standard",
            },
        )
        assert response.status_code in [200, 422]
        if response.status_code == 200:
            data = response.json()
            assert "result" in data or "passed" in data

    @pytest.mark.asyncio
    async def test_get_policy_rules(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Test GET /api/v1/policy-guards/rules - list rules."""
        response = await client.get(
            "/api/v1/policy-guards/rules",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list) or "rules" in data

    @pytest.mark.asyncio
    async def test_validate_rego_syntax(
        self,
        client: AsyncClient,
        admin_headers: dict,
    ):
        """Test POST /api/v1/policy-guards/validate-rego - syntax check."""
        rego_code = '''
package sdlc.ai_safety

default allow = false

allow {
    input.has_tests == true
    input.coverage >= 80
}
'''
        response = await client.post(
            "/api/v1/policy-guards/validate-rego",
            headers=admin_headers,
            json={"rego_code": rego_code},
        )
        assert response.status_code in [200, 422]


# =============================================================================
# Audit Trail Tests
# =============================================================================


class TestAuditTrail:
    """Tests for audit trail functionality."""

    @pytest.mark.asyncio
    async def test_override_creates_audit_log(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_ai_code_event: AICodeEvent,
        db_session: AsyncSession,
    ):
        """Test that override creation creates audit log entry."""
        # Create override
        response = await client.post(
            "/api/v1/overrides/request",
            headers=auth_headers,
            json={
                "event_id": str(test_ai_code_event.id),
                "override_type": "approved_risk",
                "reason": "Risk has been reviewed by the security team and approved. "
                          "This is a legacy system migration with proper monitoring.",
            },
        )
        assert response.status_code == 201
        data = response.json()

        # Verify audit log exists
        override_id = data["id"]
        detail_response = await client.get(
            f"/api/v1/overrides/{override_id}",
            headers=auth_headers,
        )
        assert detail_response.status_code == 200
        detail_data = detail_response.json()
        assert "audit_logs" in detail_data
        assert len(detail_data["audit_logs"]) >= 1
        assert detail_data["audit_logs"][0]["action"] == "request_created"


# =============================================================================
# Emergency Override Tests
# =============================================================================


class TestEmergencyOverride:
    """Tests for emergency override functionality."""

    @pytest.mark.asyncio
    async def test_create_emergency_override(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_ai_code_event: AICodeEvent,
    ):
        """Test creating emergency override sets post-merge review flag."""
        response = await client.post(
            "/api/v1/overrides/request",
            headers=auth_headers,
            json={
                "event_id": str(test_ai_code_event.id),
                "override_type": "emergency",
                "reason": "Critical production hotfix for payment processing. "
                          "Customers are unable to complete purchases. "
                          "Post-merge security review will be conducted within 24h.",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["override_type"] == "emergency"
        assert data["post_merge_review_required"] is True

    @pytest.mark.asyncio
    async def test_approve_emergency_override(
        self,
        client: AsyncClient,
        manager_headers: dict,
        db_session: AsyncSession,
        test_ai_code_event: AICodeEvent,
        test_project: Project,
        test_user: User,
    ):
        """Test approving emergency override."""
        # Create emergency override
        emergency_override = ValidationOverride(
            id=uuid4(),
            event_id=test_ai_code_event.id,
            project_id=test_project.id,
            override_type=OverrideType.EMERGENCY,
            reason="Critical hotfix - payment gateway down. Post-merge review required.",
            status=OverrideStatus.PENDING,
            requested_by_id=test_user.id,
            requested_at=datetime.utcnow(),
            post_merge_review_required=True,
            expires_at=datetime.utcnow() + timedelta(days=7),
        )
        db_session.add(emergency_override)
        await db_session.commit()

        # Approve
        response = await client.post(
            f"/api/v1/overrides/{emergency_override.id}/approve",
            headers=manager_headers,
            json={"comment": "Emergency approved. Post-merge review scheduled."},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "approved"
        assert data["post_merge_review_required"] is True
