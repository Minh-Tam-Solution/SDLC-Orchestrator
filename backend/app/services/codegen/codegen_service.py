"""
Codegen Service Orchestrator.

Sprint 45: Multi-Provider Codegen Architecture (EP-06)
Sprint 48: Quality Gates + Ollama Optimization + MVP Hardening
ADR-022: Provider-Agnostic Codegen Architecture

This module implements the main orchestrator service for code generation.
Manages provider selection, fallback chains, and error handling.

Design Decisions:
- Singleton service pattern
- Auto-registration of all providers
- Configurable fallback chain (Ollama → Claude → DeepCode)
- Comprehensive error handling with custom exceptions
- Quality gate validation for generated code (Sprint 48)

Author: Backend Lead
Date: December 23, 2025
Status: ACTIVE
"""

import logging
from dataclasses import dataclass
from typing import Optional, List, Dict, Any

from .provider_registry import registry, ProviderRegistry
from .base_provider import (
    CodegenProvider,
    CodegenSpec,
    CodegenResult,
    ValidationResult,
    CostEstimate
)
from .ollama_provider import OllamaCodegenProvider
from .claude_provider import ClaudeCodegenProvider
from .deepcode_provider import DeepCodeProvider
from .app_builder_provider import AppBuilderProvider
from .intent_router import IntentRouter, IntentType

logger = logging.getLogger(__name__)


@dataclass
class QualityGatedResult:
    """
    Result from code generation with quality gate validation.

    Sprint 48: Quality Gates for generated code.

    Attributes:
        result: The CodegenResult from provider
        quality_passed: Whether all quality gates passed
        quality_details: Detailed quality gate results
        blocked: Whether generation was blocked by quality gates
    """
    result: CodegenResult
    quality_passed: bool
    quality_details: Dict[str, Any]
    blocked: bool = False


class NoProviderAvailableError(Exception):
    """
    Raised when no codegen providers are available.

    This exception indicates that all providers in the fallback chain
    are either not configured or not reachable.

    Example:
        >>> try:
        ...     result = await service.generate(spec)
        ... except NoProviderAvailableError:
        ...     return {"error": "No AI providers available"}
    """
    pass


class GenerationError(Exception):
    """
    Raised when code generation fails.

    This exception wraps provider-specific errors and provides
    additional context about the failure.

    Attributes:
        provider: Name of the provider that failed
        original_error: The original exception that caused the failure
    """

    def __init__(
        self,
        message: str,
        provider: Optional[str] = None,
        original_error: Optional[Exception] = None
    ):
        super().__init__(message)
        self.provider = provider
        self.original_error = original_error


class ValidationError(Exception):
    """Raised when code validation fails."""
    pass


class CodegenService:
    """
    Main orchestrator service for code generation.

    Manages provider selection, fallback, and error handling.
    This is the primary interface for code generation in the application.

    Features:
    - Auto-registration of all providers
    - Configurable fallback chain
    - Provider status monitoring
    - Cost estimation across providers
    - Comprehensive error handling

    Example:
        >>> service = CodegenService()
        >>> result = await service.generate(spec)
        >>> print(result.files)  # {"app/main.py": "..."}

    Configuration:
        Default fallback chain: ['ollama', 'claude', 'deepcode']
        Can be customized via set_fallback_chain()
    """

    def __init__(
        self,
        custom_registry: Optional[ProviderRegistry] = None,
        auto_register: bool = True
    ):
        """
        Initialize CodegenService.

        Args:
            custom_registry: Optional custom registry (default: global registry)
            auto_register: Whether to auto-register default providers
        """
        # NOTE: ProviderRegistry implements __len__, so an empty registry is
        # falsy. We must explicitly check for None to respect a caller-provided
        # custom registry even when it starts empty.
        self._registry = custom_registry if custom_registry is not None else registry
        self._initialized = False

        # Sprint 106: Intent Router for automatic provider selection
        self._intent_router = IntentRouter(confidence_threshold=0.75)

        if auto_register:
            self._register_default_providers()

    def _register_default_providers(self) -> None:
        """
        Register default providers and set fallback chain.

        Registers:
        - AppBuilderProvider (deterministic scaffolding, Sprint 106)
        - OllamaCodegenProvider (primary LLM)
        - ClaudeCodegenProvider (fallback 1)
        - DeepCodeProvider (fallback 2)

        Note:
            app-builder is NOT in default fallback chain.
            It's only used when Intent Router detects NEW_SCAFFOLD (confidence ≥ 0.75).
            For explicit use: preferred_provider="app-builder"
        """
        if self._initialized:
            return

        # Register App Builder Provider (Sprint 106)
        try:
            self._registry.register(AppBuilderProvider())
            logger.info("Registered AppBuilderProvider (deterministic scaffolding)")
        except Exception as e:
            logger.warning(f"Failed to register AppBuilderProvider: {e}")

        # Register LLM providers
        try:
            self._registry.register(OllamaCodegenProvider())
            logger.info("Registered OllamaCodegenProvider")
        except Exception as e:
            logger.warning(f"Failed to register OllamaCodegenProvider: {e}")

        try:
            self._registry.register(ClaudeCodegenProvider())
            logger.info("Registered ClaudeCodegenProvider")
        except Exception as e:
            logger.warning(f"Failed to register ClaudeCodegenProvider: {e}")

        try:
            self._registry.register(DeepCodeProvider())
            logger.info("Registered DeepCodeProvider")
        except Exception as e:
            logger.warning(f"Failed to register DeepCodeProvider: {e}")

        # Set default fallback chain (app-builder NOT included, intent-based routing)
        self._registry.set_fallback_chain(['ollama', 'claude', 'deepcode'])

        self._initialized = True
        logger.info(
            f"CodegenService initialized with {len(self._registry)} providers"
        )

    def list_providers(self) -> List[Dict[str, Any]]:
        """
        List all registered providers with availability status.

        Returns:
            List of provider info dicts with name, availability, and position

        Example:
            >>> service.list_providers()
            [
                {"name": "ollama", "available": True, "primary": True},
                {"name": "claude", "available": False, "primary": False},
                {"name": "deepcode", "available": False, "primary": False}
            ]
        """
        return self._registry.get_provider_info()

    def get_available_providers(self) -> List[str]:
        """
        Get list of currently available provider names.

        Returns:
            List of available provider names
        """
        return self._registry.list_available()

    def set_fallback_chain(self, chain: List[str]) -> None:
        """
        Set custom fallback chain.

        Args:
            chain: Ordered list of provider names

        Example:
            >>> service.set_fallback_chain(['claude', 'ollama'])
        """
        self._registry.set_fallback_chain(chain)

    def _route_by_intent(
        self,
        spec: CodegenSpec,
        has_existing_repo: bool = False
    ) -> Optional[str]:
        """
        Route codegen request to appropriate provider based on intent detection.

        Sprint 106: Intent-based routing for app-builder provider.

        Routing Logic:
        1. Detect intent from spec description
        2. If NEW_SCAFFOLD + confidence ≥ 0.75 → "app-builder"
        3. If DOMAIN_SME → "ep06-sme" (future)
        4. Otherwise → None (use fallback chain)

        Args:
            spec: Code generation specification
            has_existing_repo: True if user has uploaded repo context

        Returns:
            Provider name to use, or None to use fallback chain

        Example:
            >>> provider = service._route_by_intent(
            ...     CodegenSpec(description="Create Instagram clone with Next.js")
            ... )
            >>> # Returns "app-builder" if confidence ≥ 0.75
        """
        try:
            detection = self._intent_router.detect_intent(
                description=spec.description,
                domain=spec.domain if hasattr(spec, 'domain') else None,
                has_existing_repo=has_existing_repo
            )

            logger.info(
                f"Intent detection: {detection.intent.value} "
                f"(confidence: {detection.confidence:.2f}) → "
                f"Recommended: {detection.recommended_provider}"
            )

            # Route to app-builder if NEW_SCAFFOLD with high confidence
            if self._intent_router.should_use_app_builder(detection):
                logger.info(
                    f"Auto-routing to app-builder (confidence: {detection.confidence:.2f})"
                )
                return "app-builder"

            # For other intents, use fallback chain
            # (DOMAIN_SME routing to ep06-sme can be added in future)
            return None

        except Exception as e:
            logger.warning(f"Intent routing failed: {e}, using fallback chain")
            return None

    async def generate(
        self,
        spec: CodegenSpec,
        preferred_provider: Optional[str] = None,
        use_cache: bool = True,
        has_existing_repo: bool = False,
    ) -> CodegenResult:
        """
        Generate code using available provider.

        Sprint 106: Intent-based routing with automatic app-builder selection.
        - NEW_SCAFFOLD (confidence ≥ 0.75) → auto-routes to app-builder
        - Otherwise → uses preferred_provider or fallback chain

        Args:
            spec: CodegenSpec with app_blueprint
            preferred_provider: Optional preferred provider name
            use_cache: Whether to use cache (default: True)
            has_existing_repo: True if user has uploaded repo context

        Returns:
            CodegenResult with generated code

        Raises:
            NoProviderAvailableError: No providers available
            GenerationError: Generation failed

        Example:
            >>> # Auto-routing to app-builder
            >>> result = await service.generate(
            ...     spec=CodegenSpec(description="Create Instagram clone")
            ... )
            >>> # Manual provider selection
            >>> result = await service.generate(
            ...     spec=CodegenSpec(description="Add auth"),
            ...     preferred_provider="ollama"
            ... )
        """
        # Sprint 48: Check cache first
        if use_cache:
            try:
                from .codegen_cache import get_codegen_cache
                cache = get_codegen_cache()
                cached_result = await cache.get(spec)
                if cached_result:
                    logger.info(
                        f"Cache hit: {len(cached_result.files)} files, "
                        f"{cached_result.generation_time_ms}ms retrieval"
                    )
                    return cached_result
            except Exception as e:
                logger.warning(f"Cache lookup failed: {e}")

        # Sprint 106: Intent-based routing (if no explicit provider specified)
        if preferred_provider is None:
            routed_provider = self._route_by_intent(spec, has_existing_repo)
            if routed_provider:
                preferred_provider = routed_provider
                logger.info(f"Intent router selected: {preferred_provider}")

        provider = self._registry.select_provider(preferred_provider)

        if not provider:
            logger.error("No codegen providers available")
            raise NoProviderAvailableError(
                "No codegen providers available. "
                "Check Ollama connection at CODEGEN_OLLAMA_URL."
            )

        logger.info(f"Generating code with provider: {provider.name}")

        try:
            result = await provider.generate(spec)
            logger.info(
                f"Generation complete: {len(result.files)} files, "
                f"{result.tokens_used} tokens, {result.generation_time_ms}ms"
            )

            # Sprint 48: Cache result for future requests
            if use_cache:
                try:
                    from .codegen_cache import get_codegen_cache
                    cache = get_codegen_cache()
                    await cache.set(spec, result)
                except Exception as e:
                    logger.warning(f"Cache set failed: {e}")

            return result

        except NotImplementedError as e:
            # Provider is stub - try fallback
            logger.warning(
                f"Provider {provider.name} not implemented, trying fallback"
            )
            return await self._try_fallback_generation(spec, provider.name)

        except Exception as e:
            logger.error(
                f"Generation failed with {provider.name}: {e}",
                exc_info=True
            )
            raise GenerationError(
                f"Code generation failed: {e}",
                provider=provider.name,
                original_error=e
            )

    async def _try_fallback_generation(
        self,
        spec: CodegenSpec,
        failed_provider: str
    ) -> CodegenResult:
        """
        Try generation with fallback providers.

        Args:
            spec: CodegenSpec with app_blueprint
            failed_provider: Name of provider that failed

        Returns:
            CodegenResult from fallback provider

        Raises:
            NoProviderAvailableError: No fallback providers available
        """
        chain = self._registry.get_fallback_chain()

        # Find position of failed provider and try rest of chain
        try:
            start_idx = chain.index(failed_provider) + 1
        except ValueError:
            start_idx = 0

        for name in chain[start_idx:]:
            provider = self._registry.get(name)
            if provider and provider.is_available:
                try:
                    logger.info(f"Trying fallback provider: {name}")
                    return await provider.generate(spec)
                except NotImplementedError:
                    continue
                except Exception as e:
                    logger.warning(f"Fallback {name} failed: {e}")
                    continue

        raise NoProviderAvailableError(
            f"All fallback providers failed after {failed_provider}"
        )

    async def validate(
        self,
        code: str,
        context: Dict[str, Any],
        provider_name: Optional[str] = None
    ) -> ValidationResult:
        """
        Validate generated code.

        Args:
            code: Code to validate
            context: Additional context (language, framework, etc.)
            provider_name: Optional specific provider to use

        Returns:
            ValidationResult with validation status

        Raises:
            NoProviderAvailableError: No providers available
            ValidationError: Validation failed

        Example:
            >>> result = await service.validate(
            ...     code="def foo(): pass",
            ...     context={"language": "python"}
            ... )
        """
        provider = self._registry.select_provider(provider_name)

        if not provider:
            raise NoProviderAvailableError(
                "No codegen providers available for validation"
            )

        try:
            return await provider.validate(code, context)
        except NotImplementedError:
            # Return default valid for stub providers
            logger.warning(
                f"Provider {provider.name} validation not implemented"
            )
            return ValidationResult(
                valid=True,
                errors=[],
                warnings=[f"Validation not available for {provider.name}"],
                suggestions=[]
            )
        except Exception as e:
            logger.error(f"Validation failed: {e}", exc_info=True)
            raise ValidationError(f"Code validation failed: {e}")

    def estimate_cost(
        self,
        spec: CodegenSpec,
        provider_names: Optional[List[str]] = None
    ) -> Dict[str, CostEstimate]:
        """
        Estimate cost for all available providers.

        Args:
            spec: CodegenSpec to estimate
            provider_names: Optional list of specific providers

        Returns:
            Dict mapping provider names to CostEstimates

        Example:
            >>> estimates = service.estimate_cost(spec)
            >>> for name, est in estimates.items():
            ...     print(f"{name}: ${est.estimated_cost_usd:.4f}")
        """
        estimates: Dict[str, CostEstimate] = {}

        # Determine which providers to estimate
        if provider_names:
            names = provider_names
        else:
            names = self._registry.list_all()

        for name in names:
            provider = self._registry.get(name)
            if provider:
                try:
                    estimates[name] = provider.estimate_cost(spec)
                except Exception as e:
                    logger.warning(f"Cost estimate failed for {name}: {e}")

        return estimates

    def get_cheapest_provider(
        self,
        spec: CodegenSpec
    ) -> Optional[tuple[str, CostEstimate]]:
        """
        Get the cheapest available provider for a spec.

        Args:
            spec: CodegenSpec to estimate

        Returns:
            Tuple of (provider_name, estimate) or None if no providers

        Example:
            >>> cheapest = service.get_cheapest_provider(spec)
            >>> if cheapest:
            ...     name, estimate = cheapest
            ...     print(f"Use {name}: ${estimate.estimated_cost_usd:.4f}")
        """
        estimates = self.estimate_cost(spec)

        # Filter to available providers only
        available_estimates = {
            name: est for name, est in estimates.items()
            if self._registry.get(name) and
            self._registry.get(name).is_available
        }

        if not available_estimates:
            return None

        # Sort by cost
        cheapest_name = min(
            available_estimates,
            key=lambda n: available_estimates[n].estimated_cost_usd
        )
        return (cheapest_name, available_estimates[cheapest_name])

    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on all providers.

        Returns:
            Dict with health status for all providers

        Example:
            >>> health = service.health_check()
            >>> print(health)
            {
                "healthy": True,
                "providers": {"ollama": True, "claude": False},
                "available_count": 1
            }
        """
        providers_status = {}
        for name in self._registry.list_all():
            provider = self._registry.get(name)
            if provider:
                providers_status[name] = provider.is_available

        available_count = sum(1 for v in providers_status.values() if v)

        return {
            "healthy": available_count > 0,
            "providers": providers_status,
            "available_count": available_count,
            "total_count": len(providers_status),
            "fallback_chain": self._registry.get_fallback_chain()
        }

    async def generate_with_quality_gates(
        self,
        spec: CodegenSpec,
        preferred_provider: Optional[str] = None,
        enable_security_scan: bool = True,
        enable_architecture_check: bool = True,
        block_on_failure: bool = True,
    ) -> QualityGatedResult:
        """
        Generate code with quality gate validation (Sprint 48).

        Runs code generation followed by quality gate validation:
        1. Syntax validation - code must parse
        2. Architecture validation - layer separation
        3. Security scan - OWASP patterns
        4. Complexity check - function/class limits

        Args:
            spec: CodegenSpec with app_blueprint
            preferred_provider: Optional preferred provider name
            enable_security_scan: Enable security pattern detection
            enable_architecture_check: Enable architecture validation
            block_on_failure: Whether to mark result as blocked on failure

        Returns:
            QualityGatedResult with generation result and quality status

        Example:
            >>> result = await service.generate_with_quality_gates(spec)
            >>> if result.quality_passed:
            ...     print("Code passed all quality gates")
            >>> else:
            ...     print(f"Quality issues: {result.quality_details}")
        """
        # Import here to avoid circular imports
        from app.services.validators.codegen_quality_validator import (
            CodegenQualityValidator
        )

        # Generate code
        codegen_result = await self.generate(spec, preferred_provider)

        # Run quality gates
        validator = CodegenQualityValidator(
            enable_security_scan=enable_security_scan,
            enable_architecture_check=enable_architecture_check,
        )

        quality_result = await validator.validate_generated_code(
            files=codegen_result.files,
            language=spec.language,
            framework=spec.framework,
        )

        # Build quality details
        quality_details = {
            "validator": quality_result.validator_name,
            "status": quality_result.status.value,
            "message": quality_result.message,
            "duration_ms": quality_result.duration_ms,
            **quality_result.details,
        }

        quality_passed = quality_result.status.value in ("passed", "skipped")
        blocked = block_on_failure and not quality_passed

        logger.info(
            f"Quality gates {'PASSED' if quality_passed else 'FAILED'}: "
            f"{quality_details.get('error_count', 0)} errors, "
            f"{quality_details.get('warning_count', 0)} warnings"
        )

        return QualityGatedResult(
            result=codegen_result,
            quality_passed=quality_passed,
            quality_details=quality_details,
            blocked=blocked,
        )


# Global service instance
_service: Optional[CodegenService] = None


def get_codegen_service() -> CodegenService:
    """
    Get or create the global CodegenService instance.

    Returns:
        CodegenService singleton instance
    """
    global _service
    if _service is None:
        _service = CodegenService()
    return _service
