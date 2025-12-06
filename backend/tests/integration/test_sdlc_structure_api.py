"""
=========================================================================
SDLC Structure Validation API Tests
SDLC Orchestrator - Stage 03 (BUILD)

Version: 1.0.0
Date: December 5, 2025
Status: ACTIVE - Sprint 30 Day 3
Authority: Backend Lead + CTO Approved
Framework: SDLC 5.0.0 Complete Lifecycle

Purpose:
- Test POST /projects/{id}/validate-structure endpoint
- Test GET /projects/{id}/validation-history endpoint
- Test GET /projects/{id}/compliance-summary endpoint
- Test rate limiting and access control

Test Coverage:
- Validation endpoint with various configurations
- Validation history retrieval and pagination
- Compliance summary aggregation
- Authentication and authorization
- Rate limiting enforcement

Zero Mock Policy: Production-ready integration tests
=========================================================================
"""

import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from uuid import uuid4

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project, ProjectMember
from app.models.user import User
from app.models.sdlc_validation import SDLCValidation


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest_asyncio.fixture(scope="function")
async def sample_project(db_session: AsyncSession, test_user: User) -> Project:
    """Create a sample project for testing."""
    project = Project(
        id=uuid4(),
        name="Test SDLC Project",
        description="Test project for SDLC structure validation",
        owner_id=test_user.id,
        status="active",
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)
    return project


@pytest_asyncio.fixture(scope="function")
async def sample_validation(
    db_session: AsyncSession, sample_project: Project, test_user: User
) -> SDLCValidation:
    """Create a sample validation for testing history."""
    validation = SDLCValidation(
        id=uuid4(),
        project_id=sample_project.id,
        validated_by=test_user.id,
        trigger_type="api",
        tier="professional",
        tier_detected=False,
        is_compliant=True,
        compliance_score=100,
        stages_found=10,
        stages_required=10,
        stages_detail=[
            {"stage_id": "00", "stage_name": "Project Foundation", "folder_name": "00-Project-Foundation", "file_count": 5, "has_readme": True}
        ],
        stages_missing=[],
        p0_status={"total": 15, "found": 15, "missing": 0, "coverage": 100},
        error_count=0,
        warning_count=0,
        issues=[],
        validation_time_ms=150.5,
        validated_at=datetime.utcnow(),
        docs_root="docs",
        strict_mode=False,
        result_hash="abc123def456",
    )
    db_session.add(validation)
    await db_session.commit()
    await db_session.refresh(validation)
    return validation


@pytest_asyncio.fixture(scope="function")
async def multiple_validations(
    db_session: AsyncSession, sample_project: Project, test_user: User
) -> list[SDLCValidation]:
    """Create multiple validations for testing history and trends."""
    validations = []

    for i in range(5):
        validation = SDLCValidation(
            id=uuid4(),
            project_id=sample_project.id,
            validated_by=test_user.id,
            trigger_type="api",
            tier="professional",
            tier_detected=False,
            is_compliant=i >= 3,  # Last 2 are compliant
            compliance_score=60 + (i * 10),  # 60, 70, 80, 90, 100
            stages_found=6 + i,
            stages_required=10,
            stages_detail=[],
            stages_missing=[],
            p0_status={},
            error_count=4 - i if i < 4 else 0,
            warning_count=i,
            issues=[],
            validation_time_ms=100 + (i * 10),
            validated_at=datetime.utcnow() - timedelta(days=i),
            docs_root="docs",
            strict_mode=False,
        )
        db_session.add(validation)
        validations.append(validation)

    await db_session.commit()
    return validations


# ============================================================================
# Validate Structure Endpoint Tests
# ============================================================================


class TestValidateStructure:
    """Tests for POST /projects/{id}/validate-structure endpoint."""

    @pytest.mark.asyncio
    async def test_validate_structure_unauthorized(
        self, client: AsyncClient, sample_project: Project
    ):
        """Test that unauthenticated requests are rejected."""
        response = await client.post(
            f"/api/v1/projects/{sample_project.id}/validate-structure"
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_validate_structure_project_not_found(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test validation of non-existent project."""
        fake_id = uuid4()
        response = await client.post(
            f"/api/v1/projects/{fake_id}/validate-structure",
            headers=auth_headers,
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_validate_structure_access_denied(
        self, client: AsyncClient, sample_project: Project, db_session: AsyncSession
    ):
        """Test that non-members cannot validate project."""
        # Create another user
        from app.core.security import get_password_hash

        other_user = User(
            id=uuid4(),
            email="other@example.com",
            full_name="Other User",
            password_hash=get_password_hash("password123"),
            is_active=True,
            is_verified=True,
        )
        db_session.add(other_user)
        await db_session.commit()

        # Login as other user
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"email": "other@example.com", "password": "password123"},
        )
        other_headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}

        # Try to validate
        response = await client.post(
            f"/api/v1/projects/{sample_project.id}/validate-structure",
            headers=other_headers,
        )
        assert response.status_code == 403
        assert "access denied" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_validate_structure_success(
        self, client: AsyncClient, auth_headers: dict, sample_project: Project
    ):
        """Test successful structure validation."""
        response = await client.post(
            f"/api/v1/projects/{sample_project.id}/validate-structure",
            headers=auth_headers,
            json={
                "docs_root": "docs",
                "strict_mode": False,
                "include_p0": True,
            },
        )
        assert response.status_code == 200

        data = response.json()
        assert "id" in data
        assert data["project_id"] == str(sample_project.id)
        assert "is_compliant" in data or "valid" in data
        assert "compliance_score" in data or "score" in data
        assert "tier" in data
        assert "stages_found" in data
        assert "stages_missing" in data
        assert "validated_at" in data
        assert "validation_time_ms" in data

    @pytest.mark.asyncio
    async def test_validate_structure_with_tier_override(
        self, client: AsyncClient, auth_headers: dict, sample_project: Project
    ):
        """Test validation with explicit tier override."""
        response = await client.post(
            f"/api/v1/projects/{sample_project.id}/validate-structure",
            headers=auth_headers,
            json={
                "tier": "enterprise",
                "docs_root": "docs",
            },
        )
        assert response.status_code == 200

        data = response.json()
        assert data["tier"] == "enterprise"

    @pytest.mark.asyncio
    async def test_validate_structure_with_custom_docs_root(
        self, client: AsyncClient, auth_headers: dict, sample_project: Project
    ):
        """Test validation with custom documentation root."""
        response = await client.post(
            f"/api/v1/projects/{sample_project.id}/validate-structure",
            headers=auth_headers,
            json={
                "docs_root": "documentation",
            },
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_validate_structure_stores_result(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_project: Project,
        db_session: AsyncSession,
    ):
        """Test that validation result is stored in database."""
        from sqlalchemy import select

        response = await client.post(
            f"/api/v1/projects/{sample_project.id}/validate-structure",
            headers=auth_headers,
        )
        assert response.status_code == 200

        data = response.json()
        validation_id = data["id"]

        # Check database
        result = await db_session.execute(
            select(SDLCValidation).where(SDLCValidation.id == validation_id)
        )
        validation = result.scalar_one_or_none()

        assert validation is not None
        assert validation.project_id == sample_project.id


# ============================================================================
# Validation History Endpoint Tests
# ============================================================================


class TestValidationHistory:
    """Tests for GET /projects/{id}/validation-history endpoint."""

    @pytest.mark.asyncio
    async def test_history_unauthorized(
        self, client: AsyncClient, sample_project: Project
    ):
        """Test that unauthenticated requests are rejected."""
        response = await client.get(
            f"/api/v1/projects/{sample_project.id}/validation-history"
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_history_empty(
        self, client: AsyncClient, auth_headers: dict, sample_project: Project
    ):
        """Test history for project with no validations."""
        response = await client.get(
            f"/api/v1/projects/{sample_project.id}/validation-history",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_history_with_validations(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_project: Project,
        sample_validation: SDLCValidation,
    ):
        """Test history with existing validations."""
        response = await client.get(
            f"/api/v1/projects/{sample_project.id}/validation-history",
            headers=auth_headers,
        )
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == str(sample_validation.id)
        assert data[0]["score"] == 100
        assert data[0]["valid"] == True

    @pytest.mark.asyncio
    async def test_history_pagination(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_project: Project,
        multiple_validations: list[SDLCValidation],
    ):
        """Test history pagination."""
        # Get first page
        response = await client.get(
            f"/api/v1/projects/{sample_project.id}/validation-history",
            headers=auth_headers,
            params={"limit": 2, "offset": 0},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

        # Get second page
        response = await client.get(
            f"/api/v1/projects/{sample_project.id}/validation-history",
            headers=auth_headers,
            params={"limit": 2, "offset": 2},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2


# ============================================================================
# Compliance Summary Endpoint Tests
# ============================================================================


class TestComplianceSummary:
    """Tests for GET /projects/{id}/compliance-summary endpoint."""

    @pytest.mark.asyncio
    async def test_summary_unauthorized(
        self, client: AsyncClient, sample_project: Project
    ):
        """Test that unauthenticated requests are rejected."""
        response = await client.get(
            f"/api/v1/projects/{sample_project.id}/compliance-summary"
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_summary_empty_project(
        self, client: AsyncClient, auth_headers: dict, sample_project: Project
    ):
        """Test summary for project with no validations."""
        response = await client.get(
            f"/api/v1/projects/{sample_project.id}/compliance-summary",
            headers=auth_headers,
        )
        assert response.status_code == 200

        data = response.json()
        assert data["project_id"] == str(sample_project.id)
        assert data["validation_count"] == 0
        assert data["current_score"] == 0
        assert data["is_compliant"] == False

    @pytest.mark.asyncio
    async def test_summary_with_validations(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_project: Project,
        sample_validation: SDLCValidation,
    ):
        """Test summary with existing validations."""
        response = await client.get(
            f"/api/v1/projects/{sample_project.id}/compliance-summary",
            headers=auth_headers,
        )
        assert response.status_code == 200

        data = response.json()
        assert data["project_id"] == str(sample_project.id)
        assert data["project_name"] == sample_project.name
        assert data["validation_count"] == 1
        assert data["current_score"] == 100
        assert data["is_compliant"] == True
        assert data["tier"] == "professional"

    @pytest.mark.asyncio
    async def test_summary_with_trend_data(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_project: Project,
        multiple_validations: list[SDLCValidation],
    ):
        """Test summary includes trend data."""
        response = await client.get(
            f"/api/v1/projects/{sample_project.id}/compliance-summary",
            headers=auth_headers,
        )
        assert response.status_code == 200

        data = response.json()
        assert data["validation_count"] == 5
        assert "score_trend" in data
        assert "compliance_history" in data


# ============================================================================
# Rate Limiting Tests
# ============================================================================


class TestRateLimiting:
    """Tests for rate limiting on validation endpoint."""

    @pytest.mark.asyncio
    async def test_rate_limit_not_exceeded(
        self, client: AsyncClient, auth_headers: dict, sample_project: Project
    ):
        """Test that requests within limit succeed."""
        # Make 5 requests (under limit of 10)
        for _ in range(5):
            response = await client.post(
                f"/api/v1/projects/{sample_project.id}/validate-structure",
                headers=auth_headers,
            )
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_rate_limit_exceeded(
        self, client: AsyncClient, auth_headers: dict, sample_project: Project
    ):
        """Test that exceeding rate limit returns 429."""
        # Make 11 requests (over limit of 10)
        for i in range(11):
            response = await client.post(
                f"/api/v1/projects/{sample_project.id}/validate-structure",
                headers=auth_headers,
            )
            if i < 10:
                assert response.status_code == 200
            else:
                assert response.status_code == 429
                assert "rate limit" in response.json()["detail"].lower()


# ============================================================================
# Response Schema Tests
# ============================================================================


class TestResponseSchema:
    """Tests for response schema compliance."""

    @pytest.mark.asyncio
    async def test_validation_response_schema(
        self, client: AsyncClient, auth_headers: dict, sample_project: Project
    ):
        """Test validation response matches expected schema."""
        response = await client.post(
            f"/api/v1/projects/{sample_project.id}/validate-structure",
            headers=auth_headers,
        )
        assert response.status_code == 200

        data = response.json()

        # Required fields
        required_fields = [
            "id",
            "project_id",
            "tier",
            "stages_found",
            "stages_missing",
            "stages_required",
            "p0_status",
            "issues",
            "validated_at",
            "validation_time_ms",
        ]

        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

    @pytest.mark.asyncio
    async def test_history_item_schema(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_project: Project,
        sample_validation: SDLCValidation,
    ):
        """Test history item matches expected schema."""
        response = await client.get(
            f"/api/v1/projects/{sample_project.id}/validation-history",
            headers=auth_headers,
        )
        assert response.status_code == 200

        data = response.json()
        assert len(data) > 0

        item = data[0]
        required_fields = [
            "id",
            "valid",
            "score",
            "tier",
            "stages_found",
            "stages_required",
            "errors",
            "warnings",
            "validated_at",
        ]

        for field in required_fields:
            assert field in item, f"Missing required field: {field}"

    @pytest.mark.asyncio
    async def test_summary_schema(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_project: Project,
        sample_validation: SDLCValidation,
    ):
        """Test compliance summary matches expected schema."""
        response = await client.get(
            f"/api/v1/projects/{sample_project.id}/compliance-summary",
            headers=auth_headers,
        )
        assert response.status_code == 200

        data = response.json()
        required_fields = [
            "project_id",
            "project_name",
            "tier",
            "current_score",
            "is_compliant",
            "validation_count",
            "score_trend",
            "compliance_history",
        ]

        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
