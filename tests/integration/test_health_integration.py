"""
Integration Tests for Health & Metrics API

File: tests/integration/test_health_integration.py
Version: 1.0.0
Date: December 12, 2025
Status: ACTIVE - Week 6 Day 1
Authority: Backend Lead + QA Lead
Framework: SDLC 4.9 Complete Lifecycle

Test Coverage:
- GET /health - Overall API health check
- GET /metrics - System metrics (Prometheus format)

Total Endpoints: 2
Total Tests: 4+
Target Coverage: 90%+
"""

import pytest
from httpx import AsyncClient


@pytest.mark.integration
@pytest.mark.smoke
class TestHealthCheck:
    """Integration tests for health check endpoint."""

    async def test_health_check_success(self, client: AsyncClient):
        """Test overall API health check."""
        response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()

        assert "status" in data
        assert data["status"] == "healthy"
        assert "version" in data
        assert data["version"] == "1.0.0"
        assert "service" in data

    async def test_readiness_check_success(self, client: AsyncClient):
        """Test readiness check with dependency status."""
        response = await client.get("/health/ready")

        assert response.status_code == 200
        data = response.json()

        assert "status" in data
        assert data["status"] == "ready"
        assert "dependencies" in data

        # Verify all dependencies are checked
        dependencies = data["dependencies"]
        assert "postgres" in dependencies
        assert "redis" in dependencies
        assert "opa" in dependencies
        assert "minio" in dependencies

    async def test_readiness_check_dependencies(self, client: AsyncClient):
        """Test readiness check includes all dependency statuses."""
        response = await client.get("/health/ready")

        assert response.status_code == 200
        data = response.json()

        # All dependencies should report status
        for service in ["postgres", "redis", "opa", "minio"]:
            assert service in data["dependencies"]
            assert isinstance(data["dependencies"][service], str)


@pytest.mark.integration
@pytest.mark.smoke
class TestMetrics:
    """Integration tests for metrics endpoint."""

    async def test_metrics_success(self, client: AsyncClient):
        """Test system metrics endpoint (Prometheus format)."""
        response = await client.get("/metrics")

        assert response.status_code == 200
        assert "text/plain" in response.headers["content-type"]

        # Verify Prometheus format metrics
        metrics_text = response.text
        assert "# HELP" in metrics_text or "# TYPE" in metrics_text

    async def test_metrics_includes_http_requests(self, client: AsyncClient):
        """Test metrics includes HTTP request counters."""
        response = await client.get("/metrics")

        assert response.status_code == 200
        metrics_text = response.text

        # Should include HTTP request metrics
        assert "http_requests_total" in metrics_text or "http_request" in metrics_text

    async def test_metrics_includes_response_time(self, client: AsyncClient):
        """Test metrics includes response time histograms."""
        response = await client.get("/metrics")

        assert response.status_code == 200
        metrics_text = response.text

        # Should include response time metrics
        assert (
            "http_request_duration" in metrics_text or "response_time" in metrics_text
        )
