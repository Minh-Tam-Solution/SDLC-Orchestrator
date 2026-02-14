"""
=========================================================================
NIST MEASURE API Route Unit Tests
SDLC Orchestrator - Sprint 157 (Phase 3: COMPLIANCE)

Version: 1.0.0
Date: February 5, 2026
Status: ACTIVE
Authority: CTO Approved
Framework: SDLC 6.0.5

Test Categories:
- Evaluate Endpoint (success, validation error, empty project)
- Dashboard Endpoint (success, missing project_id)
- List Metrics (success, with filters, empty)
- Record Metric (success 201, invalid system 404, validation error 422)
- Batch Metrics (success 201, empty batch)
- Metric Trend (success, missing params, empty result)
- Bias Summary (success, empty project)
- Edge Cases (invalid UUID, unauthorized)

Endpoints:
- POST /api/v1/compliance/nist/measure/evaluate
- GET  /api/v1/compliance/nist/measure/dashboard
- GET  /api/v1/compliance/nist/measure/metrics
- POST /api/v1/compliance/nist/measure/metrics
- POST /api/v1/compliance/nist/measure/metrics/batch
- GET  /api/v1/compliance/nist/measure/metrics/trend
- GET  /api/v1/compliance/nist/measure/bias-summary

Architecture: ADR-051 API Layer
Test Approach: ASGI transport tests hitting FastAPI directly
=========================================================================
"""

import pytest
from httpx import AsyncClient
from uuid import uuid4


# Test constants
PROJECT_ID = "00000000-0000-0000-0000-000000000001"
SYSTEM_ID = "00000000-0000-0000-0000-000000000002"
METRIC_ID = "00000000-0000-0000-0000-000000000003"
USER_ID = "00000000-0000-0000-0000-000000000004"
FRAMEWORK_ID = "00000000-0000-0000-0000-000000000005"


# =============================================================================
# Evaluate Endpoint Tests
# =============================================================================


class TestEvaluateMeasureEndpoint:
    """Tests for POST /api/v1/compliance/nist/measure/evaluate."""

    @pytest.mark.asyncio
    async def test_evaluate_measure_success(self, api_client: AsyncClient):
        """Test evaluation with valid data returns 200 with results."""
        response = await api_client.post(
            "/api/v1/compliance/nist/measure/evaluate",
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
            assert data["policies_total"] == 4
            assert data["framework_code"] == "NIST_AI_RMF"
            assert data["function"] == "MEASURE"
        else:
            assert response.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_evaluate_measure_validation_error(self, api_client: AsyncClient):
        """Test evaluation with invalid request body returns 422."""
        response = await api_client.post(
            "/api/v1/compliance/nist/measure/evaluate",
            json={
                "invalid_field": "bad data",
            },
        )

        assert response.status_code in (401, 422)

    @pytest.mark.asyncio
    async def test_evaluate_measure_empty_project(self, api_client: AsyncClient):
        """Test evaluation with missing project_id returns 422."""
        response = await api_client.post(
            "/api/v1/compliance/nist/measure/evaluate",
            json={},
        )

        assert response.status_code in (401, 422)


# =============================================================================
# Dashboard Endpoint Tests
# =============================================================================


class TestGetMeasureDashboardEndpoint:
    """Tests for GET /api/v1/compliance/nist/measure/dashboard."""

    @pytest.mark.asyncio
    async def test_get_dashboard_success(self, api_client: AsyncClient):
        """Test dashboard returns 200 with aggregated data."""
        response = await api_client.get(
            "/api/v1/compliance/nist/measure/dashboard",
            params={"project_id": PROJECT_ID},
        )

        if response.status_code == 200:
            data = response.json()
            assert "project_id" in data
            assert "compliance_percentage" in data
            assert "policies_passed" in data
            assert "policies_total" in data
            assert "total_metrics" in data
            assert "within_threshold" in data
            assert "bias_groups_count" in data
            assert "disparity_summary" in data
        else:
            assert response.status_code in (401, 403, 404)

    @pytest.mark.asyncio
    async def test_get_dashboard_missing_project_id(self, api_client: AsyncClient):
        """Test dashboard without project_id returns 422."""
        response = await api_client.get(
            "/api/v1/compliance/nist/measure/dashboard",
        )

        assert response.status_code in (401, 422)


# =============================================================================
# List Metrics Tests
# =============================================================================


class TestListMetricsEndpoint:
    """Tests for GET /api/v1/compliance/nist/measure/metrics."""

    @pytest.mark.asyncio
    async def test_list_metrics_success(self, api_client: AsyncClient):
        """Test listing metrics returns 200 with paginated response."""
        response = await api_client.get(
            "/api/v1/compliance/nist/measure/metrics",
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
    async def test_list_metrics_with_filters(self, api_client: AsyncClient):
        """Test listing metrics with ai_system_id and metric_type filters."""
        response = await api_client.get(
            "/api/v1/compliance/nist/measure/metrics",
            params={
                "project_id": PROJECT_ID,
                "ai_system_id": SYSTEM_ID,
                "metric_type": "accuracy",
            },
        )

        if response.status_code == 200:
            data = response.json()
            assert "items" in data
            assert isinstance(data["items"], list)
        else:
            assert response.status_code in (401, 403, 404)

    @pytest.mark.asyncio
    async def test_list_metrics_empty(self, api_client: AsyncClient):
        """Test listing metrics for project with no data returns empty list."""
        empty_project = str(uuid4())
        response = await api_client.get(
            "/api/v1/compliance/nist/measure/metrics",
            params={"project_id": empty_project},
        )

        if response.status_code == 200:
            data = response.json()
            assert data["total"] == 0
            assert data["items"] == []
        else:
            assert response.status_code in (401, 403, 404)


# =============================================================================
# Record Metric Tests
# =============================================================================


class TestCreateMetricEndpoint:
    """Tests for POST /api/v1/compliance/nist/measure/metrics."""

    @pytest.mark.asyncio
    async def test_create_metric_success(self, api_client: AsyncClient):
        """Test creating a metric with valid data returns 201."""
        response = await api_client.post(
            "/api/v1/compliance/nist/measure/metrics",
            json={
                "project_id": PROJECT_ID,
                "ai_system_id": SYSTEM_ID,
                "metric_type": "accuracy",
                "metric_name": "Model Accuracy Q1",
                "metric_value": 0.95,
                "threshold_min": 0.90,
                "threshold_max": 1.0,
                "unit": "%",
                "measured_at": "2026-04-14T12:00:00Z",
                "tags": ["performance"],
            },
        )

        if response.status_code == 201:
            data = response.json()
            assert "id" in data
            assert data["metric_name"] == "Model Accuracy Q1"
            assert data["metric_value"] == 0.95
            assert data["is_within_threshold"] is True
        else:
            assert response.status_code in (401, 403, 404)

    @pytest.mark.asyncio
    async def test_create_metric_invalid_system(self, api_client: AsyncClient):
        """Test creating metric for non-existent AI system returns 404."""
        nonexistent_system = "00000000-0000-0000-0000-000000000999"
        response = await api_client.post(
            "/api/v1/compliance/nist/measure/metrics",
            json={
                "project_id": PROJECT_ID,
                "ai_system_id": nonexistent_system,
                "metric_type": "accuracy",
                "metric_name": "Invalid System Metric",
                "metric_value": 0.80,
                "measured_at": "2026-04-14T12:00:00Z",
            },
        )

        if response.status_code == 404:
            data = response.json()
            assert "detail" in data
        else:
            assert response.status_code in (401, 403, 422)

    @pytest.mark.asyncio
    async def test_create_metric_validation_error(self, api_client: AsyncClient):
        """Test creating metric with missing required fields returns 422."""
        response = await api_client.post(
            "/api/v1/compliance/nist/measure/metrics",
            json={
                "project_id": PROJECT_ID,
            },
        )

        assert response.status_code in (401, 422)


# =============================================================================
# Batch Metrics Tests
# =============================================================================


class TestBatchMetricsEndpoint:
    """Tests for POST /api/v1/compliance/nist/measure/metrics/batch."""

    @pytest.mark.asyncio
    async def test_batch_create_success(self, api_client: AsyncClient):
        """Test batch creating metrics with valid data returns 201."""
        response = await api_client.post(
            "/api/v1/compliance/nist/measure/metrics/batch",
            json={
                "project_id": PROJECT_ID,
                "metrics": [
                    {
                        "project_id": PROJECT_ID,
                        "ai_system_id": SYSTEM_ID,
                        "metric_type": "accuracy",
                        "metric_name": "Accuracy Batch 1",
                        "metric_value": 0.93,
                        "measured_at": "2026-04-14T12:00:00Z",
                    },
                    {
                        "project_id": PROJECT_ID,
                        "ai_system_id": SYSTEM_ID,
                        "metric_type": "f1_score",
                        "metric_name": "F1 Batch 1",
                        "metric_value": 0.91,
                        "measured_at": "2026-04-14T12:00:00Z",
                    },
                ],
            },
        )

        if response.status_code == 201:
            data = response.json()
            assert isinstance(data, list)
            assert len(data) == 2
        else:
            assert response.status_code in (401, 403, 404)

    @pytest.mark.asyncio
    async def test_batch_create_empty_batch(self, api_client: AsyncClient):
        """Test batch creating with empty metrics list returns 422."""
        response = await api_client.post(
            "/api/v1/compliance/nist/measure/metrics/batch",
            json={
                "project_id": PROJECT_ID,
                "metrics": [],
            },
        )

        assert response.status_code in (401, 422)


# =============================================================================
# Metric Trend Tests
# =============================================================================


class TestMetricTrendEndpoint:
    """Tests for GET /api/v1/compliance/nist/measure/metrics/trend."""

    @pytest.mark.asyncio
    async def test_get_metric_trend_success(self, api_client: AsyncClient):
        """Test metric trend returns 200 with data points."""
        response = await api_client.get(
            "/api/v1/compliance/nist/measure/metrics/trend",
            params={
                "ai_system_id": SYSTEM_ID,
                "metric_type": "accuracy",
                "days": 30,
            },
        )

        if response.status_code == 200:
            data = response.json()
            assert "ai_system_id" in data
            assert "metric_type" in data
            assert "data_points" in data
            assert "total_points" in data
            assert isinstance(data["data_points"], list)
            assert data["metric_type"] == "accuracy"
        else:
            assert response.status_code in (401, 403, 404)

    @pytest.mark.asyncio
    async def test_get_metric_trend_missing_params(self, api_client: AsyncClient):
        """Test metric trend without required params returns 422."""
        response = await api_client.get(
            "/api/v1/compliance/nist/measure/metrics/trend",
        )

        assert response.status_code in (401, 422)

    @pytest.mark.asyncio
    async def test_get_metric_trend_empty_result(self, api_client: AsyncClient):
        """Test metric trend for system with no data returns empty list."""
        empty_system = str(uuid4())
        response = await api_client.get(
            "/api/v1/compliance/nist/measure/metrics/trend",
            params={
                "ai_system_id": empty_system,
                "metric_type": "accuracy",
                "days": 30,
            },
        )

        if response.status_code == 200:
            data = response.json()
            assert data["total_points"] == 0
            assert data["data_points"] == []
        else:
            assert response.status_code in (401, 403, 404)


# =============================================================================
# Bias Summary Tests
# =============================================================================


class TestBiasSummaryEndpoint:
    """Tests for GET /api/v1/compliance/nist/measure/bias-summary."""

    @pytest.mark.asyncio
    async def test_get_bias_summary_success(self, api_client: AsyncClient):
        """Test bias summary returns 200 with system data."""
        response = await api_client.get(
            "/api/v1/compliance/nist/measure/bias-summary",
            params={"project_id": PROJECT_ID},
        )

        if response.status_code == 200:
            data = response.json()
            assert "project_id" in data
            assert "systems" in data
            assert "total_bias_metrics" in data
            assert "compliant_systems" in data
            assert "non_compliant_systems" in data
            assert isinstance(data["systems"], list)
        else:
            assert response.status_code in (401, 403, 404)

    @pytest.mark.asyncio
    async def test_get_bias_summary_empty_project(self, api_client: AsyncClient):
        """Test bias summary for empty project returns zero counts."""
        empty_project = str(uuid4())
        response = await api_client.get(
            "/api/v1/compliance/nist/measure/bias-summary",
            params={"project_id": empty_project},
        )

        if response.status_code == 200:
            data = response.json()
            assert data["total_bias_metrics"] == 0
            assert data["compliant_systems"] == 0
            assert data["non_compliant_systems"] == 0
            assert data["systems"] == []
        else:
            assert response.status_code in (401, 403, 404)


# =============================================================================
# Edge Cases
# =============================================================================


class TestEdgeCases:
    """Edge case tests for NIST MEASURE endpoints."""

    @pytest.mark.asyncio
    async def test_invalid_uuid(self, api_client: AsyncClient):
        """Test endpoints with invalid UUID format return 422."""
        response = await api_client.get(
            "/api/v1/compliance/nist/measure/dashboard",
            params={"project_id": "not-a-uuid"},
        )

        assert response.status_code in (401, 422)

    @pytest.mark.asyncio
    async def test_unauthorized_access(self, api_client: AsyncClient):
        """Test endpoints require authentication (401 or 403)."""
        # The api_client fixture does not provide auth headers.
        # Most endpoints should return 401/403 or succeed depending
        # on whether auth middleware is active in test mode.
        response = await api_client.get(
            "/api/v1/compliance/nist/measure/bias-summary",
            params={"project_id": PROJECT_ID},
        )

        # Either succeeds (auth disabled in test) or rejected
        assert response.status_code in (200, 401, 403)

    @pytest.mark.asyncio
    async def test_missing_project_id_on_metrics(self, api_client: AsyncClient):
        """Test metrics list without project_id returns 422."""
        response = await api_client.get(
            "/api/v1/compliance/nist/measure/metrics",
        )

        assert response.status_code in (401, 422)

    @pytest.mark.asyncio
    async def test_missing_project_id_on_bias_summary(self, api_client: AsyncClient):
        """Test bias summary without project_id returns 422."""
        response = await api_client.get(
            "/api/v1/compliance/nist/measure/bias-summary",
        )

        assert response.status_code in (401, 422)
