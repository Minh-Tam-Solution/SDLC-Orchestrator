# =========================================================================
# STATUS: FROZEN (Sprint 173, Feb 2026)
# TIER: Deferred (Q2 2026 extraction)
# REASON: Non-core for current phase. Working code preserved.
# REACTIVATION: CPO approval required.
# DO NOT: Delete, refactor, or add features without CTO approval.
# =========================================================================
"""
SDLC Orchestrator - Codegen Service Package.

Sprint 45: Multi-Provider Codegen Architecture (EP-06)
ADR-022: Provider-Agnostic Codegen Architecture

This package implements the codegen engine with:
- CodegenProvider abstract interface
- Provider Registry with fallback chain
- Ollama-first implementation (cost-efficient)
- Stub providers for Claude/DeepCode (no hard dependencies)

Author: Backend Lead
Date: December 23, 2025
Status: ACTIVE
"""

from .base_provider import (
    CodegenProvider,
    CodegenSpec,
    CodegenResult,
    ValidationResult,
    CostEstimate,
)
from .provider_registry import ProviderRegistry, registry
from .codegen_service import (
    CodegenService,
    NoProviderAvailableError,
    GenerationError,
    QualityGatedResult,
)

__all__ = [
    # Base Provider
    "CodegenProvider",
    "CodegenSpec",
    "CodegenResult",
    "ValidationResult",
    "CostEstimate",
    # Registry
    "ProviderRegistry",
    "registry",
    # Service
    "CodegenService",
    "NoProviderAvailableError",
    "GenerationError",
    "QualityGatedResult",
]
