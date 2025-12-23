"""
Provider Registry for Codegen Providers.

Sprint 45: Multi-Provider Codegen Architecture (EP-06)
ADR-022: Provider-Agnostic Codegen Architecture

This module implements the registry pattern for managing codegen providers.
Supports dynamic registration, configuration-based selection, and fallback chains.

Design Decisions:
- Singleton pattern for global registry instance
- Fallback chain for graceful degradation
- Dynamic provider registration/unregistration
- Configuration-based provider selection

Author: Backend Lead
Date: December 23, 2025
Status: ACTIVE
"""

from typing import Dict, List, Optional
import logging

from .base_provider import CodegenProvider

logger = logging.getLogger(__name__)


class ProviderRegistry:
    """
    Registry for managing codegen providers.

    Supports dynamic registration and configuration-based selection.
    Implements fallback chain pattern for high availability.

    Attributes:
        _providers: Dict of registered providers by name
        _fallback_chain: Ordered list of provider names for fallback

    Example:
        >>> registry = ProviderRegistry()
        >>> registry.register(OllamaProvider())
        >>> registry.set_fallback_chain(['ollama', 'claude'])
        >>> provider = registry.select_provider()
    """

    def __init__(self):
        """Initialize empty registry."""
        self._providers: Dict[str, CodegenProvider] = {}
        self._fallback_chain: List[str] = []

    def register(self, provider: CodegenProvider) -> None:
        """
        Register a provider.

        Args:
            provider: CodegenProvider instance to register

        Note:
            If a provider with the same name already exists,
            it will be replaced with the new one.

        Example:
            >>> registry.register(OllamaProvider())
        """
        self._providers[provider.name] = provider
        logger.info(f"Registered codegen provider: {provider.name}")

    def unregister(self, name: str) -> bool:
        """
        Unregister a provider by name.

        Args:
            name: Provider name to unregister

        Returns:
            True if provider was unregistered, False if not found

        Example:
            >>> registry.unregister("claude")
        """
        if name in self._providers:
            del self._providers[name]
            logger.info(f"Unregistered codegen provider: {name}")
            return True
        return False

    def get(self, name: str) -> Optional[CodegenProvider]:
        """
        Get a provider by name.

        Args:
            name: Provider name to retrieve

        Returns:
            CodegenProvider if found, None otherwise

        Example:
            >>> provider = registry.get("ollama")
        """
        return self._providers.get(name)

    def list_all(self) -> List[str]:
        """
        List all registered provider names.

        Returns:
            List of all registered provider names

        Example:
            >>> registry.list_all()
            ['ollama', 'claude', 'deepcode']
        """
        return list(self._providers.keys())

    def list_available(self) -> List[str]:
        """
        List all available (configured and reachable) provider names.

        Only returns providers where is_available == True.

        Returns:
            List of available provider names

        Example:
            >>> registry.list_available()
            ['ollama']  # Only ollama is running
        """
        return [
            name for name, provider in self._providers.items()
            if provider.is_available
        ]

    def set_fallback_chain(self, chain: List[str]) -> None:
        """
        Set the fallback chain for provider selection.

        The fallback chain determines the order in which providers
        are tried when the preferred provider is unavailable.

        Args:
            chain: Ordered list of provider names

        Example:
            >>> registry.set_fallback_chain(['ollama', 'claude', 'deepcode'])
        """
        self._fallback_chain = chain
        logger.info(f"Set fallback chain: {chain}")

    def get_fallback_chain(self) -> List[str]:
        """
        Get the current fallback chain.

        Returns:
            List of provider names in fallback order
        """
        return self._fallback_chain.copy()

    def select_provider(
        self,
        preferred: Optional[str] = None
    ) -> Optional[CodegenProvider]:
        """
        Select a provider using fallback chain.

        First tries the preferred provider (if specified and available),
        then tries each provider in the fallback chain in order.

        Args:
            preferred: Preferred provider name (from project config)

        Returns:
            First available provider in chain, or None if all unavailable

        Example:
            >>> provider = registry.select_provider(preferred="claude")
            >>> if provider:
            ...     result = await provider.generate(spec)
        """
        # Try preferred first
        if preferred and preferred in self._providers:
            provider = self._providers[preferred]
            if provider.is_available:
                logger.debug(f"Selected preferred provider: {preferred}")
                return provider
            logger.warning(
                f"Preferred provider {preferred} unavailable, trying fallback"
            )

        # Try fallback chain
        for name in self._fallback_chain:
            if name in self._providers:
                provider = self._providers[name]
                if provider.is_available:
                    logger.info(f"Selected provider from fallback: {name}")
                    return provider
                logger.debug(f"Fallback provider {name} unavailable, skipping")

        # Try any available provider as last resort
        for name, provider in self._providers.items():
            if provider.is_available:
                logger.warning(
                    f"No fallback chain providers available, "
                    f"using first available: {name}"
                )
                return provider

        logger.error("No available providers in registry")
        return None

    def get_provider_info(self) -> List[Dict[str, any]]:
        """
        Get detailed info about all registered providers.

        Returns list of dicts with name, availability, and position
        in fallback chain.

        Returns:
            List of provider info dicts

        Example:
            >>> registry.get_provider_info()
            [
                {"name": "ollama", "available": True, "fallback_position": 0},
                {"name": "claude", "available": False, "fallback_position": 1}
            ]
        """
        info = []
        for name, provider in self._providers.items():
            position = (
                self._fallback_chain.index(name)
                if name in self._fallback_chain
                else -1
            )
            info.append({
                "name": name,
                "available": provider.is_available,
                "fallback_position": position,
                "primary": position == 0 if position >= 0 else False
            })
        return sorted(info, key=lambda x: (
            x["fallback_position"] if x["fallback_position"] >= 0 else 999
        ))

    def clear(self) -> None:
        """
        Clear all registered providers.

        Useful for testing or reconfiguration.
        """
        self._providers.clear()
        self._fallback_chain.clear()
        logger.info("Cleared all providers from registry")

    def __len__(self) -> int:
        """Return number of registered providers."""
        return len(self._providers)

    def __contains__(self, name: str) -> bool:
        """Check if provider is registered."""
        return name in self._providers

    def __repr__(self) -> str:
        """String representation of registry."""
        providers = ", ".join(self._providers.keys())
        return f"<ProviderRegistry(providers=[{providers}])>"


# Global registry instance
# This is the singleton used throughout the application
registry = ProviderRegistry()
