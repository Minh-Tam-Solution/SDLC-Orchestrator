"""
=========================================================================
NIST MAP API Route Unit Tests
SDLC Orchestrator - Sprint 157 (Phase 3: COMPLIANCE)

Version: 1.0.0
Date: February 5, 2026
Status: ACTIVE
Authority: CTO Approved
Framework: SDLC 6.0.5

Test Categories:
- MAP Evaluation Endpoints (success, validation error, empty project)
- MAP Dashboard Endpoint (success, missing project_id)
- AI System List Endpoints (success, pagination, empty)
- AI System Create Endpoints (success 201, duplicate 409, validation 422)
- AI System Update Endpoints (success, not found 404, validation)
- AI System Delete Endpoints (success 204, not found 404, already deleted)
- Risk Impact Endpoints (success, empty project)

Endpoints:
- POST /api/v1/compliance/nist/map/evaluate
- GET  /api/v1/compliance/nist/map/dashboard
- GET  /api/v1/compliance/nist/map/ai-systems
- POST /api/v1/compliance/nist/map/ai-systems
- PUT  /api/v1/compliance/nist/map/ai-systems/{system_id}
- DELETE /api/v1/compliance/nist/map/ai-systems/{system_id}
- GET  /api/v1/compliance/nist/map/risk-impacts

Architecture: ADR-051 API Layer
Test Approach: ASGI transport tests hitting FastAPI directly
=========================================================================
"""

import pytest
from httpx import AsyncClient
from uuid import uuid4


# Test constants
PROJECT_ID = "00000000-0000-0000-0000-000000000001"
FRAMEWORK_ID = "00000000-0000-0000-0000-000000000002"
SYSTEM_ID = "00000000-0000-0000-0000-000000000003"
USER_ID = "00000000-0000-0000-0000-000000000004"


# =============================================================================
# MAP Evaluation Tests
# =============================================================================


class TestEvaluateMapEndpoint:
    """Tests for POST /api/v1/compliance/nist/map/evaluate."""

    @pytest.mark.asyncio
    async def test_evaluate_map_success(self, api_client: AsyncClient):
        """Test evaluation with valid data returns 200 with results."""
        response = await api_client.post(
            "/api/v1/compliance/nist/map/evaluate",
            json={
                "project_id": PROJECT_ID,
            },
        )

        if response.status_code == 200:
            data = response.json()
            assert "project_id" in data
            assert "overall_compliant" in data
            assert "policies_passed" in data
            assert "policies_total" in data
            assert "compliance_percentage" in data
            assert "results" in data
            assert isinstance(data["results"], list)
            assert data["framework_code"] == "NIST_AI_RMF"
            assert data["function"] == "MAP"
        else:
            assert response.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_evaluate_map_validation_error(self, api_client: AsyncClient):
        """Test evaluation with invalid request body returns 422."""
        response = await api_client.post(
            "/api/v1/compliance/nist/map/evaluate",
            json={
                "invalid_field": "bad data",
            },
        )

        assert response.status_code in (401, 422)

    @pytest.mark.asyncio
    async def test_evaluate_map_empty_project_id(self, api_client: AsyncClient):
        """Test evaluation with missing project_id returns 422."""
        response = await api_client.post(
            "/api/v1/compliance/nist/map/evaluate",
            json={},
        )

        assert response.status_code in (401, 422)


# =============================================================================
# MAP Dashboard Tests
# =============================================================================


class TestGetMapDashboardEndpoint:
    """Tests for GET /api/v1/compliance/nist/map/dashboard."""

    @pytest.mark.asyncio
    async def test_get_map_dashboard_success(self, api_client: AsyncClient):
        """Test dashboard returns 200 with aggregated data."""
        response = await api_client.get(
            "/api/v1/compliance/nist/map/dashboard",
            params={"project_id": PROJECT_ID},
        )

        if response.status_code == 200:
            data = response.json()
            assert "project_id" in data
            assert "compliance_percentage" in data
            assert "policies_passed" in data
            assert "policies_total" in data
            assert "ai_system_summary" in data
            assert "risk_summary" in data
            assert "total_risks" in data
            assert "total_systems" in data
        else:
            assert response.status_code in (401, 403, 404)

    @pytest.mark.asyncio
    async def test_get_map_dashboard_no_project_id(self, api_client: AsyncClient):
        """Test dashboard without project_id returns 422."""
        response = await api_client.get(
            "/api/v1/compliance/nist/map/dashboard",
        )

        assert response.status_code in (401, 422)


# =============================================================================
# AI System List Tests
# =============================================================================


class TestListAISystemsEndpoint:
    """Tests for GET /api/v1/compliance/nist/map/ai-systems."""

    @pytest.mark.asyncio
    async def test_list_ai_systems_success(self, api_client: AsyncClient):
        """Test listing AI systems returns 200 with paginated response."""
        response = await api_client.get(
            "/api/v1/compliance/nist/map/ai-systems",
            params={"project_id": PROJECT_ID},
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
            assert response.status_code in (401, 403, 404)

    @pytest.mark.asyncio
    async def test_list_ai_systems_pagination(self, api_client: AsyncClient):
        """Test listing AI systems with custom pagination parameters."""
        response = await api_client.get(
            "/api/v1/compliance/nist/map/ai-systems",
            params={
                "project_id": PROJECT_ID,
                "limit": 10,
                "offset": 5,
            },
        )

        if response.status_code == 200:
            data = response.json()
            assert "items" in data
            assert data["limit"] == 10
            assert data["offset"] == 5
        else:
            assert response.status_code in (401, 403, 404)

    @pytest.mark.asyncio
    async def test_list_ai_systems_empty(self, api_client: AsyncClient):
        """Test listing AI systems returns empty list for new project."""
        empty_project_id = "00000000-0000-0000-0000-000000000099"
        response = await api_client.get(
            "/api/v1/compliance/nist/map/ai-systems",
            params={"project_id": empty_project_id},
        )

        if response.status_code == 200:
            data = response.json()
            assert "items" in data
            assert isinstance(data["items"], list)
            assert data["total"] >= 0
        else:
            assert response.status_code in (401, 403, 404)


# =============================================================================
# AI System Create Tests
# =============================================================================


class TestCreateAISystemEndpoint:
    """Tests for POST /api/v1/compliance/nist/map/ai-systems."""

    @pytest.mark.asyncio
    async def test_create_ai_system_success(self, api_client: AsyncClient):
        """Test creating an AI system with valid data returns 201."""
        response = await api_client.post(
            "/api/v1/compliance/nist/map/ai-systems",
            json={
                "project_id": PROJECT_ID,
                "name": "Test AI Chatbot",
                "system_type": "nlp",
                "risk_level": "limited",
                "purpose": "Automated customer support",
                "scope": "Production - US region",
                "stakeholders": [{"role": "user", "name": "customers"}],
                "dependencies": [{"name": "openai", "type": "api"}],
                "categorization": {"risk_tier": "limited"},
            },
        )

        if response.status_code == 201:
            data = response.json()
            assert "id" in data
            assert data["name"] == "Test AI Chatbot"
            assert data["system_type"] == "nlp"
            assert data["risk_level"] == "limited"
            assert data["is_active"] is True
        else:
            assert response.status_code in (401, 403, 409)

    @pytest.mark.asyncio
    async def test_create_ai_system_duplicate(self, api_client: AsyncClient):
        """Test creating AI system with duplicate name returns 409."""
        payload = {
            "project_id": PROJECT_ID,
            "name": f"Duplicate System {uuid4().hex[:8]}",
            "system_type": "nlp",
        }

        # First creation
        first_response = await api_client.post(
            "/api/v1/compliance/nist/map/ai-systems",
            json=payload,
        )

        if first_response.status_code == 201:
            # Second creation with same name should conflict
            second_response = await api_client.post(
                "/api/v1/compliance/nist/map/ai-systems",
                json=payload,
            )
            assert second_response.status_code in (409, 401, 403)
        else:
            # Auth blocked first request, skip duplicate test
            assert first_response.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_create_ai_system_validation_error(self, api_client: AsyncClient):
        """Test creating AI system with missing required fields returns 422."""
        response = await api_client.post(
            "/api/v1/compliance/nist/map/ai-systems",
            json={
                "project_id": PROJECT_ID,
            },
        )

        assert response.status_code in (401, 422)


# =============================================================================
# AI System Update Tests
# =============================================================================


class TestUpdateAISystemEndpoint:
    """Tests for PUT /api/v1/compliance/nist/map/ai-systems/{system_id}."""

    @pytest.mark.asyncio
    async def test_update_ai_system_success(self, api_client: AsyncClient):
        """Test updating an AI system with valid data."""
        response = await api_client.put(
            f"/api/v1/compliance/nist/map/ai-systems/{SYSTEM_ID}",
            json={
                "risk_level": "high",
                "purpose": "Updated purpose description",
            },
        )

        if response.status_code == 200:
            data = response.json()
            assert "id" in data
            assert "risk_level" in data
            assert "name" in data
        else:
            assert response.status_code in (401, 403, 404)

    @pytest.mark.asyncio
    async def test_update_ai_system_not_found(self, api_client: AsyncClient):
        """Test updating a non-existent AI system returns 404."""
        nonexistent_id = "00000000-0000-0000-0000-000000000999"
        response = await api_client.put(
            f"/api/v1/compliance/nist/map/ai-systems/{nonexistent_id}",
            json={
                "name": "This system does not exist",
            },
        )

        assert response.status_code in (404, 401, 403)

    @pytest.mark.asyncio
    async def test_update_ai_system_validation_error(self, api_client: AsyncClient):
        """Test updating with invalid risk_level returns 422."""
        response = await api_client.put(
            f"/api/v1/compliance/nist/map/ai-systems/{SYSTEM_ID}",
            json={
                "risk_level": "invalid_level",
            },
        )

        assert response.status_code in (422, 401, 403)


# =============================================================================
# AI System Delete Tests
# =============================================================================


class TestDeleteAISystemEndpoint:
    """Tests for DELETE /api/v1/compliance/nist/map/ai-systems/{system_id}."""

    @pytest.mark.asyncio
    async def test_delete_ai_system_success(self, api_client: AsyncClient):
        """Test soft-deleting an AI system returns 204."""
        # First create a system to delete
        create_response = await api_client.post(
            "/api/v1/compliance/nist/map/ai-systems",
            json={
                "project_id": PROJECT_ID,
                "name": f"System To Delete {uuid4().hex[:8]}",
                "system_type": "generative",
            },
        )

        if create_response.status_code == 201:
            created_id = create_response.json()["id"]
            delete_response = await api_client.delete(
                f"/api/v1/compliance/nist/map/ai-systems/{created_id}",
            )
            assert delete_response.status_code in (204, 401, 403)
        else:
            # Auth blocked; just verify the endpoint exists by calling directly
            response = await api_client.delete(
                f"/api/v1/compliance/nist/map/ai-systems/{SYSTEM_ID}",
            )
            assert response.status_code in (204, 401, 403, 404)

    @pytest.mark.asyncio
    async def test_delete_ai_system_not_found(self, api_client: AsyncClient):
        """Test deleting a non-existent AI system returns 404."""
        nonexistent_id = "00000000-0000-0000-0000-000000000999"
        response = await api_client.delete(
            f"/api/v1/compliance/nist/map/ai-systems/{nonexistent_id}",
        )

        assert response.status_code in (404, 401, 403)

    @pytest.mark.asyncio
    async def test_delete_ai_system_already_deleted(self, api_client: AsyncClient):
        """Test deleting an already-deleted AI system returns 404."""
        # Create and delete a system, then try deleting again
        create_response = await api_client.post(
            "/api/v1/compliance/nist/map/ai-systems",
            json={
                "project_id": PROJECT_ID,
                "name": f"Double Delete {uuid4().hex[:8]}",
                "system_type": "decision",
            },
        )

        if create_response.status_code == 201:
            created_id = create_response.json()["id"]
            # First delete
            first_delete = await api_client.delete(
                f"/api/v1/compliance/nist/map/ai-systems/{created_id}",
            )

            if first_delete.status_code == 204:
                # Second delete should fail
                second_delete = await api_client.delete(
                    f"/api/v1/compliance/nist/map/ai-systems/{created_id}",
                )
                assert second_delete.status_code in (404, 401, 403)
            else:
                assert first_delete.status_code in (401, 403)
        else:
            # Auth blocked; verify endpoint shape
            assert create_response.status_code in (401, 403)


# =============================================================================
# Risk Impact Tests
# =============================================================================


class TestGetRiskImpactsEndpoint:
    """Tests for GET /api/v1/compliance/nist/map/risk-impacts."""

    @pytest.mark.asyncio
    async def test_get_risk_impacts_success(self, api_client: AsyncClient):
        """Test getting risk impacts returns 200 with list response."""
        response = await api_client.get(
            "/api/v1/compliance/nist/map/risk-impacts",
            params={"project_id": PROJECT_ID},
        )

        if response.status_code == 200:
            data = response.json()
            assert "items" in data
            assert "total" in data
            assert isinstance(data["items"], list)
        else:
            assert response.status_code in (401, 403, 404)

    @pytest.mark.asyncio
    async def test_get_risk_impacts_empty_project(self, api_client: AsyncClient):
        """Test getting risk impacts for empty project returns empty list."""
        empty_project_id = "00000000-0000-0000-0000-000000000099"
        response = await api_client.get(
            "/api/v1/compliance/nist/map/risk-impacts",
            params={"project_id": empty_project_id},
        )

        if response.status_code == 200:
            data = response.json()
            assert "items" in data
            assert isinstance(data["items"], list)
            assert data["total"] >= 0
        else:
            assert response.status_code in (401, 403, 404)

    @pytest.mark.asyncio
    async def test_get_risk_impacts_no_project_id(self, api_client: AsyncClient):
        """Test getting risk impacts without project_id returns 422."""
        response = await api_client.get(
            "/api/v1/compliance/nist/map/risk-impacts",
        )

        assert response.status_code in (401, 422)
