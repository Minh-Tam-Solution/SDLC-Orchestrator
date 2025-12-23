"""
Codegen API Integration Tests.

Sprint 45: Multi-Provider Codegen Architecture (EP-06)
Integration tests for /api/v1/codegen/* endpoints.

Test Coverage:
- GET  /codegen/providers - List providers
- POST /codegen/generate - Generate code
- POST /codegen/validate - Validate code
- POST /codegen/estimate - Estimate cost
- GET  /codegen/health - Health check

Author: Backend Lead
Date: December 23, 2025
Status: ACTIVE
"""

import pytest
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock, MagicMock

from app.services.codegen.base_provider import (
    CodegenResult,
    ValidationResult,
    CostEstimate
)


# ============================================================================
# Health Check Tests (No Auth Required)
# ============================================================================


@pytest.mark.asyncio
async def test_codegen_health_endpoint(client: AsyncClient):
    """Test GET /api/v1/codegen/health endpoint."""
    response = await client.get("/api/v1/codegen/health")

    assert response.status_code == 200
    data = response.json()

    assert "healthy" in data
    assert "providers" in data
    assert "available_count" in data
    assert "total_count" in data
    assert "fallback_chain" in data

    # Verify fallback chain structure
    assert isinstance(data["fallback_chain"], list)
    assert "ollama" in data["fallback_chain"]


@pytest.mark.asyncio
async def test_codegen_health_shows_provider_status(client: AsyncClient):
    """Test health endpoint shows status for each provider."""
    response = await client.get("/api/v1/codegen/health")

    assert response.status_code == 200
    data = response.json()

    providers = data["providers"]
    assert "ollama" in providers
    assert "claude" in providers
    assert "deepcode" in providers

    # Each provider should have boolean status
    for name, status in providers.items():
        assert isinstance(status, bool)


# ============================================================================
# Provider List Tests (Auth Required)
# ============================================================================


@pytest.mark.asyncio
async def test_codegen_providers_requires_auth(client: AsyncClient):
    """Test GET /api/v1/codegen/providers requires authentication."""
    response = await client.get("/api/v1/codegen/providers")

    # Should return 401/403 without auth
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_codegen_providers_with_auth(
    client: AsyncClient,
    auth_headers: dict
):
    """Test GET /api/v1/codegen/providers with authentication."""
    response = await client.get(
        "/api/v1/codegen/providers",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert "providers" in data
    assert "fallback_chain" in data

    # Verify provider info structure
    providers = data["providers"]
    assert len(providers) >= 3  # ollama, claude, deepcode

    for provider in providers:
        assert "name" in provider
        assert "available" in provider
        assert "fallback_position" in provider
        assert "primary" in provider


@pytest.mark.asyncio
async def test_codegen_providers_primary_is_ollama(
    client: AsyncClient,
    auth_headers: dict
):
    """Test that ollama is marked as primary provider."""
    response = await client.get(
        "/api/v1/codegen/providers",
        headers=auth_headers
    )

    assert response.status_code == 200
    providers = response.json()["providers"]

    # Find primary provider
    primary = [p for p in providers if p.get("primary")]

    # At least one primary
    assert len(primary) >= 1

    # Ollama should be in position 0 (primary)
    ollama = next((p for p in providers if p["name"] == "ollama"), None)
    assert ollama is not None
    assert ollama["fallback_position"] == 0


# ============================================================================
# Generate Endpoint Tests (Auth Required)
# ============================================================================


@pytest.mark.asyncio
async def test_codegen_generate_requires_auth(client: AsyncClient):
    """Test POST /api/v1/codegen/generate requires authentication."""
    response = await client.post(
        "/api/v1/codegen/generate",
        json={
            "app_blueprint": {"name": "Test"},
            "language": "python",
            "framework": "fastapi"
        }
    )

    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_codegen_generate_validation_error(
    client: AsyncClient,
    auth_headers: dict
):
    """Test generate endpoint validates request body."""
    # Missing required field
    response = await client.post(
        "/api/v1/codegen/generate",
        headers=auth_headers,
        json={}
    )

    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_codegen_generate_with_mock_provider(
    client: AsyncClient,
    auth_headers: dict
):
    """Test generate endpoint with mocked provider."""
    mock_result = CodegenResult(
        code="# Generated code",
        files={
            "app/main.py": "from fastapi import FastAPI\napp = FastAPI()",
            "app/models.py": "# Models"
        },
        metadata={"model": "test"},
        provider="ollama",
        tokens_used=500,
        generation_time_ms=1000
    )

    with patch(
        'app.services.codegen.codegen_service.CodegenService.generate',
        new_callable=AsyncMock
    ) as mock_generate:
        mock_generate.return_value = mock_result

        response = await client.post(
            "/api/v1/codegen/generate",
            headers=auth_headers,
            json={
                "app_blueprint": {
                    "name": "TestApp",
                    "modules": [
                        {"name": "users", "entities": []}
                    ]
                },
                "language": "python",
                "framework": "fastapi"
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["provider"] == "ollama"
        assert len(data["files"]) == 2
        assert "app/main.py" in data["files"]
        assert data["tokens_used"] == 500
        assert data["generation_time_ms"] == 1000


@pytest.mark.asyncio
async def test_codegen_generate_with_preferred_provider(
    client: AsyncClient,
    auth_headers: dict
):
    """Test generate with preferred provider parameter."""
    mock_result = CodegenResult(
        code="# code",
        files={"main.py": "# code"},
        provider="claude",
        tokens_used=100,
        generation_time_ms=500
    )

    with patch(
        'app.services.codegen.codegen_service.CodegenService.generate',
        new_callable=AsyncMock
    ) as mock_generate:
        mock_generate.return_value = mock_result

        response = await client.post(
            "/api/v1/codegen/generate",
            headers=auth_headers,
            json={
                "app_blueprint": {"name": "Test"},
                "preferred_provider": "claude"
            }
        )

        assert response.status_code == 200

        # Verify preferred_provider was passed
        call_args = mock_generate.call_args
        assert call_args.kwargs.get("preferred_provider") == "claude"


@pytest.mark.asyncio
async def test_codegen_generate_no_provider_available(
    client: AsyncClient,
    auth_headers: dict
):
    """Test generate returns 503 when no providers available."""
    from app.services.codegen.codegen_service import NoProviderAvailableError

    with patch(
        'app.services.codegen.codegen_service.CodegenService.generate',
        new_callable=AsyncMock
    ) as mock_generate:
        mock_generate.side_effect = NoProviderAvailableError("No providers")

        response = await client.post(
            "/api/v1/codegen/generate",
            headers=auth_headers,
            json={"app_blueprint": {"name": "Test"}}
        )

        assert response.status_code == 503
        assert "No providers" in response.json()["detail"]


# ============================================================================
# Validate Endpoint Tests
# ============================================================================


@pytest.mark.asyncio
async def test_codegen_validate_requires_auth(client: AsyncClient):
    """Test POST /api/v1/codegen/validate requires authentication."""
    response = await client.post(
        "/api/v1/codegen/validate",
        json={"code": "print('hello')"}
    )

    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_codegen_validate_with_mock_provider(
    client: AsyncClient,
    auth_headers: dict
):
    """Test validate endpoint with mocked provider."""
    mock_result = ValidationResult(
        valid=True,
        errors=[],
        warnings=["Consider adding type hints"],
        suggestions=["Add docstring"]
    )

    with patch(
        'app.services.codegen.codegen_service.CodegenService.validate',
        new_callable=AsyncMock
    ) as mock_validate:
        mock_validate.return_value = mock_result

        response = await client.post(
            "/api/v1/codegen/validate",
            headers=auth_headers,
            json={
                "code": "def hello(): pass",
                "context": {"language": "python"}
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert data["valid"] is True
        assert data["errors"] == []
        assert len(data["warnings"]) == 1
        assert len(data["suggestions"]) == 1


@pytest.mark.asyncio
async def test_codegen_validate_invalid_code(
    client: AsyncClient,
    auth_headers: dict
):
    """Test validate endpoint with invalid code."""
    mock_result = ValidationResult(
        valid=False,
        errors=["SyntaxError: invalid syntax"],
        warnings=[],
        suggestions=[]
    )

    with patch(
        'app.services.codegen.codegen_service.CodegenService.validate',
        new_callable=AsyncMock
    ) as mock_validate:
        mock_validate.return_value = mock_result

        response = await client.post(
            "/api/v1/codegen/validate",
            headers=auth_headers,
            json={"code": "def bad syntax {"}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["valid"] is False
        assert len(data["errors"]) == 1


# ============================================================================
# Estimate Endpoint Tests
# ============================================================================


@pytest.mark.asyncio
async def test_codegen_estimate_requires_auth(client: AsyncClient):
    """Test POST /api/v1/codegen/estimate requires authentication."""
    response = await client.post(
        "/api/v1/codegen/estimate",
        json={"app_blueprint": {"name": "Test"}}
    )

    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_codegen_estimate_returns_all_providers(
    client: AsyncClient,
    auth_headers: dict
):
    """Test estimate endpoint returns cost for all providers."""
    mock_estimates = {
        "ollama": CostEstimate(
            estimated_tokens=1000,
            estimated_cost_usd=0.001,
            provider="ollama",
            confidence=0.85
        ),
        "claude": CostEstimate(
            estimated_tokens=1000,
            estimated_cost_usd=0.018,
            provider="claude",
            confidence=0.7
        )
    }

    with patch(
        'app.services.codegen.codegen_service.CodegenService.estimate_cost'
    ) as mock_estimate:
        mock_estimate.return_value = mock_estimates

        with patch(
            'app.services.codegen.codegen_service.CodegenService.get_cheapest_provider'
        ) as mock_cheapest:
            mock_cheapest.return_value = ("ollama", mock_estimates["ollama"])

            response = await client.post(
                "/api/v1/codegen/estimate",
                headers=auth_headers,
                json={
                    "app_blueprint": {"name": "Test", "modules": []},
                    "language": "python"
                }
            )

            assert response.status_code == 200
            data = response.json()

            assert "estimates" in data
            assert "recommended_provider" in data
            assert data["recommended_provider"] == "ollama"

            # Check estimate structure
            if "ollama" in data["estimates"]:
                ollama_est = data["estimates"]["ollama"]
                assert "estimated_tokens" in ollama_est
                assert "estimated_cost_usd" in ollama_est
                assert "confidence" in ollama_est


@pytest.mark.asyncio
async def test_codegen_estimate_recommends_cheapest(
    client: AsyncClient,
    auth_headers: dict
):
    """Test estimate recommends cheapest available provider."""
    mock_estimates = {
        "ollama": CostEstimate(
            estimated_tokens=1000,
            estimated_cost_usd=0.001,
            provider="ollama",
            confidence=0.85
        ),
        "claude": CostEstimate(
            estimated_tokens=1000,
            estimated_cost_usd=0.050,
            provider="claude",
            confidence=0.7
        )
    }

    with patch(
        'app.services.codegen.codegen_service.CodegenService.estimate_cost'
    ) as mock_estimate:
        mock_estimate.return_value = mock_estimates

        with patch(
            'app.services.codegen.codegen_service.CodegenService.get_cheapest_provider'
        ) as mock_cheapest:
            # Ollama is cheaper
            mock_cheapest.return_value = ("ollama", mock_estimates["ollama"])

            response = await client.post(
                "/api/v1/codegen/estimate",
                headers=auth_headers,
                json={"app_blueprint": {"name": "Test"}}
            )

            assert response.status_code == 200
            assert response.json()["recommended_provider"] == "ollama"


# ============================================================================
# Error Handling Tests
# ============================================================================


@pytest.mark.asyncio
async def test_codegen_generate_handles_unexpected_error(
    client: AsyncClient,
    auth_headers: dict
):
    """Test generate handles unexpected errors gracefully."""
    with patch(
        'app.services.codegen.codegen_service.CodegenService.generate',
        new_callable=AsyncMock
    ) as mock_generate:
        mock_generate.side_effect = Exception("Unexpected error")

        response = await client.post(
            "/api/v1/codegen/generate",
            headers=auth_headers,
            json={"app_blueprint": {"name": "Test"}}
        )

        assert response.status_code == 500
        assert "Unexpected error" in response.json()["detail"]


@pytest.mark.asyncio
async def test_codegen_validate_handles_provider_error(
    client: AsyncClient,
    auth_headers: dict
):
    """Test validate handles provider errors."""
    from app.services.codegen.codegen_service import NoProviderAvailableError

    with patch(
        'app.services.codegen.codegen_service.CodegenService.validate',
        new_callable=AsyncMock
    ) as mock_validate:
        mock_validate.side_effect = NoProviderAvailableError("No providers")

        response = await client.post(
            "/api/v1/codegen/validate",
            headers=auth_headers,
            json={"code": "test"}
        )

        assert response.status_code == 503


# ============================================================================
# Vietnamese Content Tests
# ============================================================================


@pytest.mark.asyncio
async def test_codegen_generate_vietnamese_app(
    client: AsyncClient,
    auth_headers: dict
):
    """Test generate with Vietnamese app blueprint."""
    mock_result = CodegenResult(
        code="# Quản lý công việc",
        files={"app/main.py": "# Ứng dụng quản lý"},
        provider="ollama",
        tokens_used=500,
        generation_time_ms=2000
    )

    with patch(
        'app.services.codegen.codegen_service.CodegenService.generate',
        new_callable=AsyncMock
    ) as mock_generate:
        mock_generate.return_value = mock_result

        response = await client.post(
            "/api/v1/codegen/generate",
            headers=auth_headers,
            json={
                "app_blueprint": {
                    "name": "QuanLyCongViec",
                    "description": "Hệ thống quản lý công việc cho SME Việt Nam",
                    "modules": [
                        {
                            "name": "congviec",
                            "entities": [
                                {
                                    "name": "CongViec",
                                    "fields": [
                                        {"name": "tieu_de", "type": "string"},
                                        {"name": "mo_ta", "type": "text"},
                                        {"name": "trang_thai", "type": "enum"}
                                    ]
                                }
                            ]
                        }
                    ]
                },
                "language": "python",
                "framework": "fastapi"
            }
        )

        assert response.status_code == 200
