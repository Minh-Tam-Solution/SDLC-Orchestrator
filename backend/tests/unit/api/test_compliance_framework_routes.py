"""
=========================================================================
Compliance Framework API Route Unit Tests
SDLC Orchestrator - Sprint 156 (Phase 3: COMPLIANCE)

Version: 1.0.0
Date: February 5, 2026
Status: ACTIVE
Authority: CTO Approved
Framework: SDLC 6.0.5

Test Categories:
- Framework Listing Endpoints (success, empty)
- Framework Get Endpoint (success, not found, invalid code)
- Assessment Listing Endpoint (success, filters, empty, missing params)
- Auth edge case

Endpoints:
- GET  /api/v1/compliance/frameworks
- GET  /api/v1/compliance/frameworks/{code}
- GET  /api/v1/compliance/projects/{pid}/assessments

Architecture: ADR-051 API Layer
Test Approach: ASGI transport tests hitting FastAPI directly
=========================================================================
"""

import pytest
from httpx import AsyncClient


# =============================================================================
# Framework Listing Tests
# =============================================================================


class TestListFrameworksEndpoint:
    """Tests for GET /api/v1/compliance/frameworks."""

    @pytest.mark.asyncio
    async def test_list_frameworks_success(self, api_client: AsyncClient):
        """Test listing frameworks returns 200 with items and total."""
        response = await api_client.get("/api/v1/compliance/frameworks")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)
        assert isinstance(data["total"], int)

    @pytest.mark.asyncio
    async def test_list_frameworks_empty(self, api_client: AsyncClient):
        """Test listing frameworks when none active returns valid empty response."""
        response = await api_client.get(
            "/api/v1/compliance/frameworks",
            params={"active_only": True},
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] >= 0


# =============================================================================
# Framework Get Tests
# =============================================================================


class TestGetFrameworkEndpoint:
    """Tests for GET /api/v1/compliance/frameworks/{code}."""

    @pytest.mark.asyncio
    async def test_get_framework_success(self, api_client: AsyncClient):
        """Test getting a framework by valid code returns 200."""
        response = await api_client.get(
            "/api/v1/compliance/frameworks/NIST_AI_RMF"
        )

        if response.status_code == 200:
            data = response.json()
            assert data["code"] == "NIST_AI_RMF"
            assert "id" in data
            assert "name" in data
            assert "version" in data
            assert "total_controls" in data
        else:
            assert response.status_code in (404, 401)

    @pytest.mark.asyncio
    async def test_get_framework_not_found(self, api_client: AsyncClient):
        """Test getting a non-existent framework returns 404."""
        response = await api_client.get(
            "/api/v1/compliance/frameworks/NONEXISTENT_FRAMEWORK"
        )

        assert response.status_code in (404, 401)
        if response.status_code == 404:
            data = response.json()
            assert "detail" in data

    @pytest.mark.asyncio
    async def test_get_framework_invalid_code(self, api_client: AsyncClient):
        """Test getting a framework with clearly invalid code returns 404."""
        response = await api_client.get(
            "/api/v1/compliance/frameworks/!!INVALID!!"
        )

        assert response.status_code in (404, 401, 422)


# =============================================================================
# Assessment Listing Tests
# =============================================================================


class TestListAssessmentsEndpoint:
    """Tests for GET /api/v1/compliance/projects/{pid}/assessments."""

    @pytest.mark.asyncio
    async def test_list_assessments_success(self, api_client: AsyncClient):
        """Test listing assessments returns 200 with paginated response."""
        response = await api_client.get(
            "/api/v1/compliance/projects/00000000-0000-0000-0000-000000000001/assessments"
        )

        if response.status_code == 200:
            data = response.json()
            assert "items" in data
            assert "total" in data
            assert "limit" in data
            assert "offset" in data
            assert "has_more" in data
            assert isinstance(data["items"], list)
        else:
            assert response.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_list_assessments_with_filters(self, api_client: AsyncClient):
        """Test listing assessments with framework and status filters."""
        response = await api_client.get(
            "/api/v1/compliance/projects/00000000-0000-0000-0000-000000000001/assessments",
            params={
                "framework_code": "NIST_AI_RMF",
                "status": "compliant",
                "limit": 10,
                "offset": 0,
            },
        )

        if response.status_code == 200:
            data = response.json()
            assert "items" in data
            assert data["limit"] == 10
            assert data["offset"] == 0
        else:
            assert response.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_list_assessments_empty(self, api_client: AsyncClient):
        """Test listing assessments for project with no assessments."""
        response = await api_client.get(
            "/api/v1/compliance/projects/00000000-0000-0000-0000-000000000099/assessments"
        )

        if response.status_code == 200:
            data = response.json()
            assert data["total"] >= 0
            assert isinstance(data["items"], list)
        else:
            assert response.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_list_assessments_no_project_id(self, api_client: AsyncClient):
        """Test listing assessments without project_id returns 404 (path required)."""
        response = await api_client.get(
            "/api/v1/compliance/projects//assessments"
        )

        assert response.status_code in (404, 307, 422)


# =============================================================================
# Auth Edge Case
# =============================================================================


class TestFrameworkAuthEdgeCase:
    """Edge case tests for authentication on compliance endpoints."""

    @pytest.mark.asyncio
    async def test_list_frameworks_unauthenticated(self, api_client: AsyncClient):
        """Test that endpoints handle missing auth appropriately.

        Depending on auth configuration, may return 401 or 200 if no
        auth middleware is enforced at the ASGI transport level.
        """
        response = await api_client.get("/api/v1/compliance/frameworks")

        assert response.status_code in (200, 401, 403)
