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
from app.services.codegen.provider_registry import ProviderRegistry
from app.services.codegen.codegen_service import (
    CodegenService,
    NoProviderAvailableError,
    GenerationError,
)


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

    def test_init_with_custom_registry(self):
        """Test service with custom registry."""
        custom_registry = ProviderRegistry()
        service = CodegenService(custom_registry=custom_registry, auto_register=False)

        assert service._registry is custom_registry

    def test_init_auto_register_false(self):
        """Test service without auto-registration."""
        custom_registry = ProviderRegistry()
        service = CodegenService(custom_registry=custom_registry, auto_register=False)

        # Should have no providers
        assert len(service._registry) == 0


class TestListProviders:
    """Test list_providers functionality."""

    def test_list_providers_empty(self):
        """Test listing when no providers registered."""
        custom_registry = ProviderRegistry()
        service = CodegenService(custom_registry=custom_registry, auto_register=False)

        providers = service.list_providers()

        assert len(providers) == 0

    def test_list_providers_with_mock(self):
        """Test listing with mock provider."""
        custom_registry = ProviderRegistry()
        custom_registry.register(MockProvider(name="test", available=True))
        service = CodegenService(custom_registry=custom_registry, auto_register=False)

        providers = service.list_providers()

        assert len(providers) == 1
        assert providers[0]["name"] == "test"
        assert providers[0]["available"] is True


class TestGenerate:
    """Test generate functionality."""

    @pytest.mark.asyncio
    async def test_generate_uses_preferred_provider(self):
        """Test generate uses preferred provider when available."""
        custom_registry = ProviderRegistry()
        mock_ollama = MockProvider(name="ollama", available=True)
        mock_claude = MockProvider(name="claude", available=True)
        custom_registry.register(mock_ollama)
        custom_registry.register(mock_claude)

        service = CodegenService(custom_registry=custom_registry, auto_register=False)

        spec = CodegenSpec(
            app_blueprint={"name": "Test", "modules": []},
            language="python",
            framework="fastapi"
        )

        result = await service.generate(spec, preferred_provider="claude")

        assert result.provider == "claude"

    @pytest.mark.asyncio
    async def test_generate_no_provider_raises(self):
        """Test generate raises when no providers available."""
        custom_registry = ProviderRegistry()
        service = CodegenService(custom_registry=custom_registry, auto_register=False)

        spec = CodegenSpec(
            app_blueprint={"name": "Test", "modules": []},
            language="python",
            framework="fastapi"
        )

        with pytest.raises(NoProviderAvailableError):
            await service.generate(spec)

    @pytest.mark.asyncio
    async def test_generate_handles_failure(self):
        """Test generate handles provider failure."""
        custom_registry = ProviderRegistry()
        failing_provider = MockProvider(name="ollama", available=True, should_fail=True)
        custom_registry.register(failing_provider)

        service = CodegenService(custom_registry=custom_registry, auto_register=False)

        spec = CodegenSpec(
            app_blueprint={"name": "Test", "modules": []},
            language="python",
            framework="fastapi"
        )

        with pytest.raises(GenerationError):
            await service.generate(spec)


class TestValidate:
    """Test validate functionality."""

    @pytest.mark.asyncio
    async def test_validate_with_provider(self):
        """Test validate with available provider."""
        custom_registry = ProviderRegistry()
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
        custom_registry.register(mock_provider)

        service = CodegenService(custom_registry=custom_registry, auto_register=False)

        result = await service.validate(
            "def foo(): pass",
            {"language": "python"}
        )

        assert result.valid is True
        assert len(result.warnings) == 1

    @pytest.mark.asyncio
    async def test_validate_no_provider_raises(self):
        """Test validate raises when no providers."""
        custom_registry = ProviderRegistry()
        service = CodegenService(custom_registry=custom_registry, auto_register=False)

        with pytest.raises(NoProviderAvailableError):
            await service.validate("code", {})


class TestEstimateCost:
    """Test cost estimation functionality."""

    def test_estimate_cost_single_provider(self):
        """Test cost estimation for single provider."""
        custom_registry = ProviderRegistry()
        custom_registry.register(MockProvider(name="ollama", available=True))

        service = CodegenService(custom_registry=custom_registry, auto_register=False)

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
        custom_registry = ProviderRegistry()
        custom_registry.register(MockProvider(name="ollama", available=True))
        custom_registry.register(MockProvider(name="claude", available=True))

        service = CodegenService(custom_registry=custom_registry, auto_register=False)

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
        """Test cost estimation for all providers."""
        custom_registry = ProviderRegistry()
        custom_registry.register(MockProvider(name="ollama", available=True))
        custom_registry.register(MockProvider(name="claude", available=False))
        custom_registry.register(MockProvider(name="deepcode", available=True))

        service = CodegenService(custom_registry=custom_registry, auto_register=False)

        spec = CodegenSpec(
            app_blueprint={"name": "Test", "modules": []},
            language="python",
            framework="fastapi"
        )

        # No provider_names = all providers
        estimates = service.estimate_cost(spec)

        # Should include all registered providers
        assert "ollama" in estimates
        assert "claude" in estimates
        assert "deepcode" in estimates

    def test_estimate_cost_empty_when_no_providers(self):
        """Test cost estimation returns empty when no providers."""
        custom_registry = ProviderRegistry()
        service = CodegenService(custom_registry=custom_registry, auto_register=False)

        spec = CodegenSpec(
            app_blueprint={"name": "Test", "modules": []},
            language="python",
            framework="fastapi"
        )

        estimates = service.estimate_cost(spec)

        assert estimates == {}


class TestGetCheapestProvider:
    """Test get_cheapest_provider functionality."""

    def test_get_cheapest_provider(self):
        """Test getting cheapest available provider."""
        custom_registry = ProviderRegistry()
        custom_registry.register(MockProvider(name="ollama", available=True))
        custom_registry.register(MockProvider(name="claude", available=True))

        service = CodegenService(custom_registry=custom_registry, auto_register=False)

        spec = CodegenSpec(
            app_blueprint={"name": "Test", "modules": []},
            language="python",
            framework="fastapi"
        )

        result = service.get_cheapest_provider(spec)

        # Should return a tuple of (name, estimate)
        assert result is not None
        name, estimate = result
        assert name in ["ollama", "claude"]

    def test_get_cheapest_none_when_empty(self):
        """Test returns None when no providers available."""
        custom_registry = ProviderRegistry()
        service = CodegenService(custom_registry=custom_registry, auto_register=False)

        spec = CodegenSpec(
            app_blueprint={"name": "Test", "modules": []},
            language="python",
            framework="fastapi"
        )

        result = service.get_cheapest_provider(spec)

        assert result is None


class TestHealthCheck:
    """Test health check functionality."""

    def test_health_returns_status(self):
        """Test health returns service status."""
        custom_registry = ProviderRegistry()
        custom_registry.register(MockProvider(name="ollama", available=True))

        service = CodegenService(custom_registry=custom_registry, auto_register=False)

        health = service.health_check()

        assert "healthy" in health
        assert "providers" in health
        assert health["healthy"] is True

    def test_health_unhealthy_when_no_providers(self):
        """Test health shows unhealthy when no providers."""
        custom_registry = ProviderRegistry()
        service = CodegenService(custom_registry=custom_registry, auto_register=False)

        health = service.health_check()

        assert health["healthy"] is False
        assert health["available_count"] == 0

    def test_health_with_mixed_providers(self):
        """Test health with available and unavailable providers."""
        custom_registry = ProviderRegistry()
        custom_registry.register(MockProvider(name="ollama", available=True))
        custom_registry.register(MockProvider(name="claude", available=False))

        service = CodegenService(custom_registry=custom_registry, auto_register=False)

        health = service.health_check()

        assert health["healthy"] is True
        assert health["available_count"] == 1
        assert health["total_count"] == 2
        assert health["providers"]["ollama"] is True
        assert health["providers"]["claude"] is False


class TestSetFallbackChain:
    """Test fallback chain configuration."""

    def test_set_fallback_chain(self):
        """Test setting custom fallback chain."""
        custom_registry = ProviderRegistry()
        service = CodegenService(custom_registry=custom_registry, auto_register=False)

        service.set_fallback_chain(["claude", "ollama"])

        # Verify chain was set
        chain = custom_registry.get_fallback_chain()
        assert chain == ["claude", "ollama"]
