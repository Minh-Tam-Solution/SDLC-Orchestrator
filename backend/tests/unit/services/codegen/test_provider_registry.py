"""
Unit tests for ProviderRegistry.

Sprint 45: Multi-Provider Codegen Architecture (EP-06)
Tests for provider_registry.py functionality.

Author: Backend Lead
Date: December 23, 2025
"""

import pytest
from typing import Dict, Any

from app.services.codegen.base_provider import (
    CodegenProvider,
    CodegenSpec,
    CodegenResult,
    ValidationResult,
    CostEstimate
)
from app.services.codegen.provider_registry import ProviderRegistry


class MockProvider(CodegenProvider):
    """Mock provider for testing."""

    def __init__(self, name: str, available: bool = True):
        self._name = name
        self._available = available

    @property
    def name(self) -> str:
        return self._name

    @property
    def is_available(self) -> bool:
        return self._available

    async def generate(self, spec: CodegenSpec) -> CodegenResult:
        return CodegenResult(code="mock", provider=self._name)

    async def validate(
        self, code: str, context: Dict[str, Any]
    ) -> ValidationResult:
        return ValidationResult(valid=True)

    def estimate_cost(self, spec: CodegenSpec) -> CostEstimate:
        return CostEstimate(
            estimated_tokens=100,
            estimated_cost_usd=0.001,
            provider=self._name,
            confidence=0.9
        )


class TestProviderRegistry:
    """Tests for ProviderRegistry."""

    @pytest.fixture
    def registry(self):
        """Create fresh registry for each test."""
        return ProviderRegistry()

    def test_empty_registry(self, registry):
        """Test empty registry state."""
        assert len(registry) == 0
        assert registry.list_all() == []
        assert registry.list_available() == []

    def test_register_provider(self, registry):
        """Test registering a provider."""
        provider = MockProvider("test")
        registry.register(provider)

        assert len(registry) == 1
        assert "test" in registry
        assert registry.get("test") is provider

    def test_register_multiple(self, registry):
        """Test registering multiple providers."""
        registry.register(MockProvider("provider1"))
        registry.register(MockProvider("provider2"))
        registry.register(MockProvider("provider3"))

        assert len(registry) == 3
        assert registry.list_all() == ["provider1", "provider2", "provider3"]

    def test_register_replaces_existing(self, registry):
        """Test registering same name replaces existing."""
        old = MockProvider("test", available=False)
        new = MockProvider("test", available=True)

        registry.register(old)
        assert registry.get("test").is_available is False

        registry.register(new)
        assert len(registry) == 1
        assert registry.get("test").is_available is True

    def test_unregister_provider(self, registry):
        """Test unregistering a provider."""
        registry.register(MockProvider("test"))
        assert len(registry) == 1

        result = registry.unregister("test")
        assert result is True
        assert len(registry) == 0
        assert "test" not in registry

    def test_unregister_nonexistent(self, registry):
        """Test unregistering nonexistent provider."""
        result = registry.unregister("nonexistent")
        assert result is False

    def test_get_nonexistent(self, registry):
        """Test getting nonexistent provider."""
        assert registry.get("nonexistent") is None

    def test_list_available_filters(self, registry):
        """Test list_available filters by availability."""
        registry.register(MockProvider("available1", available=True))
        registry.register(MockProvider("unavailable", available=False))
        registry.register(MockProvider("available2", available=True))

        available = registry.list_available()
        assert len(available) == 2
        assert "available1" in available
        assert "available2" in available
        assert "unavailable" not in available

    def test_set_fallback_chain(self, registry):
        """Test setting fallback chain."""
        chain = ["ollama", "claude", "deepcode"]
        registry.set_fallback_chain(chain)

        assert registry.get_fallback_chain() == chain

    def test_get_fallback_chain_copy(self, registry):
        """Test get_fallback_chain returns copy."""
        chain = ["a", "b", "c"]
        registry.set_fallback_chain(chain)

        returned = registry.get_fallback_chain()
        returned.append("d")

        assert registry.get_fallback_chain() == ["a", "b", "c"]

    def test_select_preferred_available(self, registry):
        """Test select_provider with available preferred."""
        registry.register(MockProvider("ollama", available=True))
        registry.register(MockProvider("claude", available=True))
        registry.set_fallback_chain(["ollama", "claude"])

        selected = registry.select_provider(preferred="claude")
        assert selected.name == "claude"

    def test_select_preferred_unavailable_fallback(self, registry):
        """Test fallback when preferred unavailable."""
        registry.register(MockProvider("ollama", available=True))
        registry.register(MockProvider("claude", available=False))
        registry.set_fallback_chain(["ollama", "claude"])

        selected = registry.select_provider(preferred="claude")
        assert selected.name == "ollama"

    def test_select_uses_fallback_chain_order(self, registry):
        """Test selection follows fallback chain order."""
        registry.register(MockProvider("third", available=True))
        registry.register(MockProvider("first", available=True))
        registry.register(MockProvider("second", available=True))
        registry.set_fallback_chain(["first", "second", "third"])

        selected = registry.select_provider()
        assert selected.name == "first"

    def test_select_skips_unavailable_in_chain(self, registry):
        """Test selection skips unavailable providers."""
        registry.register(MockProvider("first", available=False))
        registry.register(MockProvider("second", available=False))
        registry.register(MockProvider("third", available=True))
        registry.set_fallback_chain(["first", "second", "third"])

        selected = registry.select_provider()
        assert selected.name == "third"

    def test_select_returns_none_all_unavailable(self, registry):
        """Test select returns None when all unavailable."""
        registry.register(MockProvider("a", available=False))
        registry.register(MockProvider("b", available=False))
        registry.set_fallback_chain(["a", "b"])

        selected = registry.select_provider()
        assert selected is None

    def test_select_finds_any_available_outside_chain(self, registry):
        """Test finds available provider not in chain."""
        registry.register(MockProvider("not_in_chain", available=True))
        registry.register(MockProvider("in_chain", available=False))
        registry.set_fallback_chain(["in_chain"])

        selected = registry.select_provider()
        assert selected.name == "not_in_chain"

    def test_get_provider_info(self, registry):
        """Test get_provider_info returns correct format."""
        registry.register(MockProvider("ollama", available=True))
        registry.register(MockProvider("claude", available=False))
        registry.set_fallback_chain(["ollama", "claude"])

        info = registry.get_provider_info()

        assert len(info) == 2

        ollama_info = next(p for p in info if p["name"] == "ollama")
        assert ollama_info["available"] is True
        assert ollama_info["fallback_position"] == 0
        assert ollama_info["primary"] is True

        claude_info = next(p for p in info if p["name"] == "claude")
        assert claude_info["available"] is False
        assert claude_info["fallback_position"] == 1
        assert claude_info["primary"] is False

    def test_get_provider_info_not_in_chain(self, registry):
        """Test provider_info for provider not in chain."""
        registry.register(MockProvider("orphan", available=True))
        registry.set_fallback_chain([])

        info = registry.get_provider_info()
        orphan_info = info[0]

        assert orphan_info["fallback_position"] == -1
        assert orphan_info["primary"] is False

    def test_clear_registry(self, registry):
        """Test clearing registry."""
        registry.register(MockProvider("a"))
        registry.register(MockProvider("b"))
        registry.set_fallback_chain(["a", "b"])

        registry.clear()

        assert len(registry) == 0
        assert registry.get_fallback_chain() == []

    def test_contains_operator(self, registry):
        """Test __contains__ operator."""
        registry.register(MockProvider("exists"))

        assert "exists" in registry
        assert "not_exists" not in registry

    def test_repr(self, registry):
        """Test registry repr."""
        registry.register(MockProvider("a"))
        registry.register(MockProvider("b"))

        r = repr(registry)
        assert "ProviderRegistry" in r
        assert "a" in r
        assert "b" in r
