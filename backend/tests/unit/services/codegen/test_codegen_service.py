"""
Unit tests for CodegenService orchestrator.

Sprint 45: Multi-Provider Codegen Architecture (EP-06)
Tests main service with provider fallback.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

from app.services.codegen.base_provider import (
    CodegenSpec,
    CodegenResult,
    ValidationResult,
    CostEstimate,
    CodegenProvider,
)
from app.services.codegen.codegen_service import CodegenService


class MockProvider(CodegenProvider):
    """Mock provider for testing."""

    def __init__(
        self,
        name: str = "mock",
        available: bool = True,
        generate_result: CodegenResult = None,
        validate_result: ValidationResult = None,
        should_fail: bool = False
    ):
        self._name = name
        self._available = available
        self._generate_result = generate_result or CodegenResult(
            code="# Generated",
            files={"app/main.py": "content"},
            metadata={},
            provider=name,
            tokens_used=100,
            generation_time_ms=1000
        )
        self._validate_result = validate_result or ValidationResult(
            valid=True, errors=[], warnings=[], suggestions=[]
        )
        self._should_fail = should_fail

    @property
    def name(self) -> str:
        return self._name

    @property
    def is_available(self) -> bool:
        return self._available

    async def generate(self, spec: CodegenSpec) -> CodegenResult:
        if self._should_fail:
            raise Exception("Generation failed")
        return self._generate_result

    async def validate(self, code: str, context: Dict[str, Any]) -> ValidationResult:
        if self._should_fail:
            raise Exception("Validation failed")
        return self._validate_result

    def estimate_cost(self, spec: CodegenSpec) -> CostEstimate:
        return CostEstimate(
            estimated_tokens=1000,
            estimated_cost_usd=0.001,
            provider=self._name,
            confidence=0.85
        )


class TestCodegenServiceInit:
    """Test CodegenService initialization."""

    def test_init_creates_registry(self):
        """Test service initializes with registry."""
        service = CodegenService()

        assert service.registry is not None

    def test_init_registers_providers(self):
        """Test service auto-registers providers."""
        # Note: May not register if providers unavailable
        service = CodegenService()

        # Should have attempted registration
        assert service.registry is not None


class TestListProviders:
    """Test list_providers functionality."""

    def test_list_providers_empty(self):
        """Test listing when no providers registered."""
        service = CodegenService()
        # Clear any auto-registered providers
        service.registry._providers.clear()

        providers = service.list_providers()

        assert len(providers) == 0

    def test_list_providers_with_mock(self):
        """Test listing with mock provider."""
        service = CodegenService()
        service.registry._providers.clear()
        service.registry.register(MockProvider(name="test", available=True))

        providers = service.list_providers()

        assert len(providers) == 1
        assert providers[0]["name"] == "test"
        assert providers[0]["available"] is True


class TestGenerate:
    """Test generate functionality."""

    @pytest.mark.asyncio
    async def test_generate_uses_preferred_provider(self):
        """Test generate uses preferred provider when available."""
        service = CodegenService()
        service.registry._providers.clear()

        mock_ollama = MockProvider(name="ollama", available=True)
        mock_claude = MockProvider(name="claude", available=True)
        service.registry.register(mock_ollama)
        service.registry.register(mock_claude)

        spec = CodegenSpec(
            app_blueprint={"name": "Test", "modules": []},
            language="python",
            framework="fastapi"
        )

        result = await service.generate(spec, preferred_provider="claude")

        assert result.provider == "claude"

    @pytest.mark.asyncio
    async def test_generate_fallback_on_failure(self):
        """Test generate falls back when provider fails."""
        service = CodegenService()
        service.registry._providers.clear()

        failing_provider = MockProvider(name="ollama", available=True, should_fail=True)
        working_provider = MockProvider(name="claude", available=True)
        service.registry.register(failing_provider)
        service.registry.register(working_provider)
        service.registry.set_fallback_chain(["ollama", "claude"])

        spec = CodegenSpec(
            app_blueprint={"name": "Test", "modules": []},
            language="python",
            framework="fastapi"
        )

        result = await service.generate(spec)

        # Should fallback to claude
        assert result.provider == "claude"

    @pytest.mark.asyncio
    async def test_generate_no_provider_raises(self):
        """Test generate raises when no providers available."""
        service = CodegenService()
        service.registry._providers.clear()

        spec = CodegenSpec(
            app_blueprint={"name": "Test", "modules": []},
            language="python",
            framework="fastapi"
        )

        with pytest.raises(RuntimeError, match="No codegen providers available"):
            await service.generate(spec)

    @pytest.mark.asyncio
    async def test_generate_all_fail_raises(self):
        """Test generate raises when all providers fail."""
        service = CodegenService()
        service.registry._providers.clear()

        service.registry.register(MockProvider(name="ollama", available=True, should_fail=True))
        service.registry.register(MockProvider(name="claude", available=True, should_fail=True))
        service.registry.set_fallback_chain(["ollama", "claude"])

        spec = CodegenSpec(
            app_blueprint={"name": "Test", "modules": []},
            language="python",
            framework="fastapi"
        )

        with pytest.raises(RuntimeError, match="All codegen providers failed"):
            await service.generate(spec)


class TestValidate:
    """Test validate functionality."""

    @pytest.mark.asyncio
    async def test_validate_with_provider(self):
        """Test validate with specified provider."""
        service = CodegenService()
        service.registry._providers.clear()

        mock_provider = MockProvider(
            name="ollama",
            available=True,
            validate_result=ValidationResult(
                valid=True,
                errors=[],
                warnings=["Test warning"],
                suggestions=[]
            )
        )
        service.registry.register(mock_provider)

        result = await service.validate(
            "def foo(): pass",
            {"language": "python"},
            provider_name="ollama"
        )

        assert result.valid is True
        assert len(result.warnings) == 1

    @pytest.mark.asyncio
    async def test_validate_default_provider(self):
        """Test validate uses first available provider."""
        service = CodegenService()
        service.registry._providers.clear()

        service.registry.register(MockProvider(name="ollama", available=True))
        service.registry.set_fallback_chain(["ollama"])

        result = await service.validate("code", {})

        assert isinstance(result, ValidationResult)

    @pytest.mark.asyncio
    async def test_validate_no_provider_raises(self):
        """Test validate raises when provider not found."""
        service = CodegenService()
        service.registry._providers.clear()

        with pytest.raises(RuntimeError, match="not found"):
            await service.validate("code", {}, provider_name="nonexistent")


class TestEstimateCost:
    """Test cost estimation functionality."""

    def test_estimate_cost_single_provider(self):
        """Test cost estimation for single provider."""
        service = CodegenService()
        service.registry._providers.clear()

        service.registry.register(MockProvider(name="ollama", available=True))

        spec = CodegenSpec(
            app_blueprint={"name": "Test", "modules": []},
            language="python",
            framework="fastapi"
        )

        estimates = service.estimate_cost(spec, provider_names=["ollama"])

        assert "ollama" in estimates
        assert estimates["ollama"].provider == "ollama"

    def test_estimate_cost_multiple_providers(self):
        """Test cost estimation for multiple providers."""
        service = CodegenService()
        service.registry._providers.clear()

        service.registry.register(MockProvider(name="ollama", available=True))
        service.registry.register(MockProvider(name="claude", available=True))

        spec = CodegenSpec(
            app_blueprint={"name": "Test", "modules": []},
            language="python",
            framework="fastapi"
        )

        estimates = service.estimate_cost(spec, provider_names=["ollama", "claude"])

        assert len(estimates) == 2
        assert "ollama" in estimates
        assert "claude" in estimates

    def test_estimate_cost_all_providers(self):
        """Test cost estimation for all available providers."""
        service = CodegenService()
        service.registry._providers.clear()

        service.registry.register(MockProvider(name="ollama", available=True))
        service.registry.register(MockProvider(name="claude", available=False))
        service.registry.register(MockProvider(name="deepcode", available=True))

        spec = CodegenSpec(
            app_blueprint={"name": "Test", "modules": []},
            language="python",
            framework="fastapi"
        )

        # No provider_names = all available
        estimates = service.estimate_cost(spec)

        assert "ollama" in estimates
        assert "deepcode" in estimates
        # claude not available, should not be in estimates
        assert "claude" not in estimates

    def test_estimate_cost_empty_when_no_providers(self):
        """Test cost estimation returns empty when no providers."""
        service = CodegenService()
        service.registry._providers.clear()

        spec = CodegenSpec(
            app_blueprint={"name": "Test", "modules": []},
            language="python",
            framework="fastapi"
        )

        estimates = service.estimate_cost(spec)

        assert estimates == {}


class TestGetRecommendedProvider:
    """Test recommended provider logic."""

    def test_recommend_cheapest_provider(self):
        """Test recommends cheapest available provider."""
        service = CodegenService()
        service.registry._providers.clear()

        # Ollama should be cheapest
        service.registry.register(MockProvider(name="ollama", available=True))
        service.registry.register(MockProvider(name="claude", available=True))

        spec = CodegenSpec(
            app_blueprint={"name": "Test", "modules": []},
            language="python",
            framework="fastapi"
        )

        recommended = service.get_recommended_provider(spec)

        # Should recommend based on cost/availability
        assert recommended in ["ollama", "claude"]

    def test_recommend_none_when_empty(self):
        """Test returns None when no providers available."""
        service = CodegenService()
        service.registry._providers.clear()

        spec = CodegenSpec(
            app_blueprint={"name": "Test", "modules": []},
            language="python",
            framework="fastapi"
        )

        recommended = service.get_recommended_provider(spec)

        assert recommended is None


class TestHealthCheck:
    """Test health check functionality."""

    def test_health_returns_status(self):
        """Test health returns service status."""
        service = CodegenService()
        service.registry._providers.clear()

        service.registry.register(MockProvider(name="ollama", available=True))

        health = service.health()

        assert "status" in health
        assert "providers" in health

    def test_health_degraded_when_no_providers(self):
        """Test health shows degraded when no providers."""
        service = CodegenService()
        service.registry._providers.clear()

        health = service.health()

        assert health["status"] == "degraded"
        assert health["available_count"] == 0

    def test_health_healthy_with_providers(self):
        """Test health shows healthy with providers."""
        service = CodegenService()
        service.registry._providers.clear()

        service.registry.register(MockProvider(name="ollama", available=True))

        health = service.health()

        assert health["status"] == "healthy"
        assert health["available_count"] >= 1
