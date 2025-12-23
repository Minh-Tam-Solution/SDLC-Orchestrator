"""
Claude Codegen Provider Stub.

Sprint 45: Multi-Provider Codegen Architecture (EP-06)
ADR-022: Provider-Agnostic Codegen Architecture

This module provides a STUB implementation for Claude provider.
NO hard dependency on Anthropic SDK (AGPL-safe, budget-conscious).

Design Decisions:
- Stub only - no actual implementation
- No SDK imports (cost: $1000/month if enabled)
- Available only when ANTHROPIC_API_KEY configured
- Used as fallback when Ollama unavailable

Author: Backend Lead
Date: December 23, 2025
Status: STUB (Deferred implementation)
"""

import json
import logging
from typing import Dict, Any, Optional

from app.core.config import settings
from .base_provider import (
    CodegenProvider,
    CodegenSpec,
    CodegenResult,
    ValidationResult,
    CostEstimate
)

logger = logging.getLogger(__name__)


class ClaudeCodegenProvider(CodegenProvider):
    """
    Claude-based code generation provider.

    STUB implementation - no hard dependency on Anthropic SDK.
    This provider exists in the fallback chain but won't be used
    unless explicitly implemented and API key configured.

    Why Stub?
    - Claude API costs ~$1000/month (vs Ollama $50/month)
    - Ollama-first strategy for Vietnam SME market
    - No vendor lock-in (can implement later if needed)

    To Enable:
    1. Set ANTHROPIC_API_KEY in environment
    2. Implement actual API calls (requires httpx to Anthropic API)
    3. Update is_available to return True

    Configuration:
    - ANTHROPIC_API_KEY: API key from Anthropic dashboard
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Claude provider.

        Args:
            api_key: Anthropic API key (default: settings.ANTHROPIC_API_KEY)
        """
        self._api_key = api_key or settings.ANTHROPIC_API_KEY
        self._model = "claude-sonnet-4-20250514"  # Latest model

    @property
    def name(self) -> str:
        """Provider identifier."""
        return "claude"

    @property
    def is_available(self) -> bool:
        """
        Check if Claude is configured.

        Currently always returns False as this is a stub.
        Set to True and implement API calls to enable.

        Returns:
            False (stub implementation)
        """
        # Only available if API key is set AND implementation is complete
        # Currently stub, so always return False
        if self._api_key:
            logger.debug(
                "Claude API key configured but provider is stub-only. "
                "Implement generate() to enable."
            )
        return False  # Stub - not implemented

    async def generate(self, spec: CodegenSpec) -> CodegenResult:
        """
        Generate code using Claude.

        STUB - Not implemented. Use Ollama instead.

        Args:
            spec: CodegenSpec with app_blueprint

        Raises:
            NotImplementedError: Always (stub implementation)
        """
        raise NotImplementedError(
            "Claude provider not implemented. Use Ollama (primary) instead. "
            "To implement: Add httpx calls to Anthropic Messages API."
        )

    async def validate(
        self,
        code: str,
        context: Dict[str, Any]
    ) -> ValidationResult:
        """
        Validate code using Claude.

        STUB - Not implemented.

        Args:
            code: Code to validate
            context: Additional context

        Raises:
            NotImplementedError: Always (stub implementation)
        """
        raise NotImplementedError(
            "Claude validation not implemented. Use Ollama instead."
        )

    def estimate_cost(self, spec: CodegenSpec) -> CostEstimate:
        """
        Estimate cost for Claude generation.

        Provides realistic cost estimate based on Claude pricing:
        - Input: $3.00 / 1M tokens
        - Output: $15.00 / 1M tokens

        Args:
            spec: CodegenSpec to estimate

        Returns:
            CostEstimate with Claude pricing
        """
        # Estimate tokens based on IR size
        ir_json = json.dumps(spec.app_blueprint)
        ir_tokens = len(ir_json) // 4  # ~4 chars per token

        # Output typically 2-3x input
        estimated_output_tokens = ir_tokens * 3
        estimated_input = ir_tokens

        # Claude Sonnet pricing (as of 2025)
        # Input: $3.00 / 1M tokens, Output: $15.00 / 1M tokens
        input_cost = (estimated_input / 1_000_000) * 3.00
        output_cost = (estimated_output_tokens / 1_000_000) * 15.00
        total_cost = input_cost + output_cost

        return CostEstimate(
            estimated_tokens=estimated_input + estimated_output_tokens,
            estimated_cost_usd=round(total_cost, 4),
            provider=self.name,
            confidence=0.7  # Lower confidence as it's an estimate
        )


class ClaudeProviderError(Exception):
    """Raised when Claude provider encounters an error."""
    pass
