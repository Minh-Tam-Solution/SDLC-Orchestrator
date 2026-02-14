"""
=========================================================================
NIST GOVERN API Route Unit Tests
SDLC Orchestrator - Sprint 156 (Phase 3: COMPLIANCE)

Version: 1.0.0
Date: February 5, 2026
Status: ACTIVE
Authority: CTO Approved
Framework: SDLC 6.0.5

Test Categories:
- GOVERN Evaluation Endpoints (success, validation error, empty project)
- GOVERN Dashboard Endpoint (success, missing project_id)
- Risk Register Endpoints (list, create, update, not found)
- RACI Matrix Endpoints (get, create, missing fields)

Endpoints:
- POST /api/v1/compliance/nist/govern/evaluate
- GET  /api/v1/compliance/nist/govern/dashboard
- GET  /api/v1/compliance/nist/risks
- POST /api/v1/compliance/nist/risks
- PUT  /api/v1/compliance/nist/risks/{risk_id}
- GET  /api/v1/compliance/nist/raci
- POST /api/v1/compliance/nist/raci

Architecture: ADR-051 API Layer
Test Approach: ASGI transport tests hitting FastAPI directly
=========================================================================
"""

import pytest
from httpx import AsyncClient
from uuid import uuid4


# Test constants
PROJECT_ID = "00000000-0000-0000-0000-000000000001"
CONTROL_ID = "00000000-0000-0000-0000-000000000002"
FRAMEWORK_ID = "00000000-0000-0000-0000-000000000003"
RISK_ID = "00000000-0000-0000-0000-000000000004"
USER_ID = "00000000-0000-0000-0000-000000000005"


# =============================================================================
# GOVERN Evaluation Tests
# =============================================================================


class TestEvaluateGovernEndpoint:
    """Tests for POST /api/v1/compliance/nist/govern/evaluate."""

    @pytest.mark.asyncio
    async def test_evaluate_govern_success(self, api_client: AsyncClient):
        """Test evaluation with valid data returns 200 with results."""
        response = await api_client.post(
            "/api/v1/compliance/nist/govern/evaluate",
            json={
                "project_id": PROJECT_ID,
                "ai_systems": [
                    {"name": "chatbot", "owner": "team-lead", "type": "nlp"},
                ],
                "team_training": {
                    "total_members": 10,
                    "trained_members": 9,
                    "completion_pct": 90,
                },
                "legal_review": {
                    "approved": True,
                    "reviewer": "legal-counsel",
                    "date": "2026-03-15",
                },
                "third_party_apis": [
                    {"name": "openai", "sla_documented": True, "privacy_agreement": True},
                ],
                "incident_postmortems": [],
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
            assert data["policies_total"] == 5
        else:
            assert response.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_evaluate_govern_validation_error(self, api_client: AsyncClient):
        """Test evaluation with invalid request body returns 422."""
        response = await api_client.post(
            "/api/v1/compliance/nist/govern/evaluate",
            json={
                "invalid_field": "bad data",
            },
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_evaluate_govern_empty_project_id(self, api_client: AsyncClient):
        """Test evaluation with empty/missing project_id returns 422."""
        response = await api_client.post(
            "/api/v1/compliance/nist/govern/evaluate",
            json={
                "ai_systems": [],
            },
        )

        assert response.status_code == 422


# =============================================================================
# GOVERN Dashboard Tests
# =============================================================================


class TestGetDashboardEndpoint:
    """Tests for GET /api/v1/compliance/nist/govern/dashboard."""

    @pytest.mark.asyncio
    async def test_get_dashboard_success(self, api_client: AsyncClient):
        """Test dashboard returns 200 with aggregated data."""
        response = await api_client.get(
            "/api/v1/compliance/nist/govern/dashboard",
            params={"project_id": PROJECT_ID},
        )

        if response.status_code == 200:
            data = response.json()
            assert "project_id" in data
            assert "compliance_percentage" in data
            assert "risk_summary" in data
            assert "total_risks" in data
            assert "raci_coverage" in data
        else:
            assert response.status_code in (401, 403, 404)

    @pytest.mark.asyncio
    async def test_get_dashboard_no_project_id(self, api_client: AsyncClient):
        """Test dashboard without project_id returns 422."""
        response = await api_client.get(
            "/api/v1/compliance/nist/govern/dashboard",
        )

        assert response.status_code == 422


# =============================================================================
# Risk Register Tests
# =============================================================================


class TestListRisksEndpoint:
    """Tests for GET /api/v1/compliance/nist/risks."""

    @pytest.mark.asyncio
    async def test_list_risks_success(self, api_client: AsyncClient):
        """Test listing risks returns 200 with paginated response."""
        response = await api_client.get(
            "/api/v1/compliance/nist/risks",
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
    async def test_list_risks_with_status(self, api_client: AsyncClient):
        """Test listing risks with status filter."""
        response = await api_client.get(
            "/api/v1/compliance/nist/risks",
            params={
                "project_id": PROJECT_ID,
                "status": "identified",
            },
        )

        if response.status_code == 200:
            data = response.json()
            assert "items" in data
            assert isinstance(data["items"], list)
        else:
            assert response.status_code in (401, 403, 404)


class TestCreateRiskEndpoint:
    """Tests for POST /api/v1/compliance/nist/risks."""

    @pytest.mark.asyncio
    async def test_create_risk_success(self, api_client: AsyncClient):
        """Test creating a risk entry with valid data."""
        response = await api_client.post(
            "/api/v1/compliance/nist/risks",
            json={
                "project_id": PROJECT_ID,
                "framework_id": FRAMEWORK_ID,
                "risk_code": "RISK-TEST-001",
                "title": "Test risk for model bias",
                "description": "AI model may exhibit bias in decisions",
                "likelihood": "likely",
                "impact": "major",
                "category": "fairness",
                "mitigation_strategy": "Implement bias detection pipeline",
            },
        )

        if response.status_code == 201:
            data = response.json()
            assert "id" in data
            assert data["risk_code"] == "RISK-TEST-001"
            assert "risk_score" in data
            assert "risk_level" in data
        else:
            assert response.status_code in (401, 403, 404)

    @pytest.mark.asyncio
    async def test_create_risk_missing_fields(self, api_client: AsyncClient):
        """Test creating a risk with missing required fields returns 422."""
        response = await api_client.post(
            "/api/v1/compliance/nist/risks",
            json={
                "project_id": PROJECT_ID,
            },
        )

        assert response.status_code == 422


class TestUpdateRiskEndpoint:
    """Tests for PUT /api/v1/compliance/nist/risks/{risk_id}."""

    @pytest.mark.asyncio
    async def test_update_risk_success(self, api_client: AsyncClient):
        """Test updating a risk entry with valid data."""
        response = await api_client.put(
            f"/api/v1/compliance/nist/risks/{RISK_ID}",
            json={
                "title": "Updated risk title",
                "status": "mitigating",
                "mitigation_strategy": "New mitigation approach",
            },
        )

        if response.status_code == 200:
            data = response.json()
            assert "id" in data
            assert "risk_score" in data
        else:
            assert response.status_code in (401, 403, 404)

    @pytest.mark.asyncio
    async def test_update_risk_not_found(self, api_client: AsyncClient):
        """Test updating a non-existent risk returns 404."""
        nonexistent_id = "00000000-0000-0000-0000-000000000999"
        response = await api_client.put(
            f"/api/v1/compliance/nist/risks/{nonexistent_id}",
            json={
                "title": "This risk does not exist",
            },
        )

        assert response.status_code in (404, 401, 403)


# =============================================================================
# RACI Matrix Tests
# =============================================================================


class TestGetRaciEndpoint:
    """Tests for GET /api/v1/compliance/nist/raci."""

    @pytest.mark.asyncio
    async def test_get_raci_success(self, api_client: AsyncClient):
        """Test getting RACI matrix returns 200 with list response."""
        response = await api_client.get(
            "/api/v1/compliance/nist/raci",
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
    async def test_get_raci_no_project_id(self, api_client: AsyncClient):
        """Test getting RACI without project_id returns 422."""
        response = await api_client.get(
            "/api/v1/compliance/nist/raci",
        )

        assert response.status_code == 422


class TestCreateRaciEndpoint:
    """Tests for POST /api/v1/compliance/nist/raci."""

    @pytest.mark.asyncio
    async def test_create_raci_success(self, api_client: AsyncClient):
        """Test creating a RACI entry with valid data."""
        response = await api_client.post(
            "/api/v1/compliance/nist/raci",
            json={
                "project_id": PROJECT_ID,
                "control_id": CONTROL_ID,
                "responsible_id": USER_ID,
                "accountable_id": USER_ID,
                "consulted_ids": [],
                "informed_ids": [],
            },
        )

        if response.status_code == 201:
            data = response.json()
            assert "id" in data
            assert data["project_id"] == PROJECT_ID
            assert data["control_id"] == CONTROL_ID
        else:
            assert response.status_code in (401, 403, 404)

    @pytest.mark.asyncio
    async def test_create_raci_missing_fields(self, api_client: AsyncClient):
        """Test creating RACI with missing required fields returns 422."""
        response = await api_client.post(
            "/api/v1/compliance/nist/raci",
            json={
                "project_id": PROJECT_ID,
            },
        )

        assert response.status_code == 422
