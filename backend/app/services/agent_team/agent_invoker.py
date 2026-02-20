"""
=========================================================================
Agent Invoker — Provider failover chain + cooldowns + error-as-string
SDLC Orchestrator - Sprint 177 (Multi-Agent Core Services)
Updated: Sprint 179 — Output credential scrubbing (ADR-058 Pattern A)

Version: 1.0.0
Date: February 2026
Status: ACTIVE - Sprint 177
Authority: CTO Approved (ADR-056 Decision 3)
Reference: ADR-056-Multi-Agent-Team-Engine.md

Purpose:
- Invoke LLM providers with failover chain (Ollama → Anthropic → Rule-based)
- Provider cooldown tracking via Redis (per ProviderProfileKey)
- Error classification via FailoverClassifier (6 reasons)
- Abort Matrix routing (auth/billing → ABORT, rate_limit/timeout → FALLBACK)
- Error-as-string for self-correction (Nanobot N3)

Sources:
- OpenClaw: src/agents/model-fallback.ts (provider chain, cooldowns)
- Nanobot N3: Error-as-string for LLM self-correction
- ADR-056 Decision 3: Provider Profile Key + Abort Matrix
- config.py: ROLE_MODEL_DEFAULTS per role

Architecture:
  Request → Check cooldown → Invoke primary (Ollama)
                                ↓ error
                             Classify error → Abort Matrix
                                ↓ FALLBACK
                             Set cooldown → Invoke fallback (Anthropic)
                                ↓ error
                             Classify → Invoke next fallback
                                ↓ all failed
                             ABORT with structured error

Zero Mock Policy: Production-ready async service with real HTTP calls
=========================================================================
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from app.services.agent_team.failover_classifier import (
    FailoverClassifier,
    FailoverAction,
    FailoverReason,
    ProviderProfileKey,
    COOLDOWN_TTLS,
)
from app.services.agent_team.config import ROLE_MODEL_DEFAULTS
from app.services.agent_team.output_scrubber import OutputScrubber

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class InvocationResult:
    """Result of a provider invocation attempt."""

    success: bool
    content: str
    provider_used: str
    model_used: str
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: int = 0
    cost_cents: int = 0
    failover_reason: str | None = None
    attempts: int = 1


@dataclass
class ProviderConfig:
    """Configuration for a single provider in the failover chain."""

    provider: str
    model: str
    account: str = "default"
    region: str = "local"
    timeout_seconds: int = 30

    @property
    def profile_key(self) -> ProviderProfileKey:
        model_family = self.model.split(":")[0] if ":" in self.model else self.model
        return ProviderProfileKey(
            provider=self.provider,
            account=self.account,
            region=self.region,
            model_family=model_family,
        )


class AgentInvokerError(Exception):
    """Base exception for agent invoker."""


class AllProvidersFailedError(AgentInvokerError):
    """All providers in the failover chain failed or were aborted."""

    def __init__(self, attempts: list[tuple[str, FailoverReason, str]]):
        self.attempts = attempts
        providers = ", ".join(f"{p}({r.value})" for p, r, _ in attempts)
        super().__init__(f"All providers failed: {providers}")


class AgentInvoker:
    """
    Invokes LLM providers with failover chain, cooldown tracking, and
    error classification per ADR-056 Decision 3.

    Failover Chain (per role, configurable):
    1. Primary: Ollama (local, $50/mo)
    2. Fallback 1: Anthropic (cloud, reasoning-quality)
    3. Fallback 2: Rule-based (deterministic, $0)

    Cooldown Tracking (Redis):
    - On FALLBACK: Set Redis key with TTL (rate_limit=60s, timeout=120s)
    - Before invoke: Check cooldown key → skip if still cooling down
    - If Redis unavailable: skip cooldown check (invoke anyway)

    Error-as-String (Nanobot N3):
    - For RETRY actions (format errors): return error as conversation content
      for LLM self-correction instead of raising exception

    Usage:
        invoker = AgentInvoker(
            provider_chain=[
                ProviderConfig(provider="ollama", model="qwen3-coder:30b"),
                ProviderConfig(provider="anthropic", model="claude-sonnet-4-5"),
            ],
            redis=redis_client,
            http_client=httpx_client,
        )
        result = await invoker.invoke(messages=[...], system_prompt="...")
    """

    def __init__(
        self,
        provider_chain: list[ProviderConfig],
        redis: object | None = None,
        http_client: object | None = None,
    ):
        self.provider_chain = provider_chain
        self.redis = redis
        self.http_client = http_client
        self.classifier = FailoverClassifier()

    @classmethod
    def from_role(
        cls,
        sdlc_role: str,
        redis: object | None = None,
        http_client: object | None = None,
    ) -> AgentInvoker:
        """
        Create an AgentInvoker with the default failover chain for an SDLC role.

        Uses ROLE_MODEL_DEFAULTS from config.py to build the primary provider,
        then appends standard fallbacks.
        """
        defaults = ROLE_MODEL_DEFAULTS.get(sdlc_role)
        if not defaults:
            raise AgentInvokerError(f"No model defaults for role: {sdlc_role}")

        chain: list[ProviderConfig] = []

        # Primary provider from ROLE_MODEL_DEFAULTS
        chain.append(
            ProviderConfig(
                provider=defaults["provider"],
                model=defaults["model"],
            )
        )

        # Add cloud fallback if primary is Ollama
        if defaults["provider"] == "ollama":
            chain.append(
                ProviderConfig(
                    provider="anthropic",
                    model="claude-sonnet-4-5",
                    account="default",
                    region="us-east-1",
                    timeout_seconds=60,
                )
            )

        return cls(provider_chain=chain, redis=redis, http_client=http_client)

    async def invoke(
        self,
        messages: list[dict[str, Any]],
        system_prompt: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> InvocationResult:
        """
        Invoke the provider chain with failover logic.

        Tries each provider in order:
        1. Check cooldown → skip if cooling down
        2. Invoke provider → return result if successful
        3. On error: classify → check Abort Matrix
           - ABORT: record attempt, stop chain
           - FALLBACK: set cooldown, try next provider
           - RETRY: return error-as-string content

        Raises:
            AllProvidersFailedError: If all providers failed or aborted.
        """
        failed_attempts: list[tuple[str, FailoverReason, str]] = []
        attempt_count = 0

        for config in self.provider_chain:
            # Check cooldown
            if await self._is_on_cooldown(config.profile_key):
                logger.info(
                    "Provider on cooldown, skipping: %s",
                    config.profile_key,
                )
                continue

            attempt_count += 1
            start_time = time.monotonic()

            try:
                content, input_tokens, output_tokens = await self._call_provider(
                    config=config,
                    messages=messages,
                    system_prompt=system_prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )

                latency_ms = int((time.monotonic() - start_time) * 1000)
                cost_cents = self._estimate_cost(
                    config.provider, input_tokens, output_tokens
                )

                logger.info(
                    "TRACE_PROVIDER status=succeeded: provider=%s, model=%s, "
                    "tokens=%d+%d, latency=%dms, cost=%d cents",
                    config.provider,
                    config.model,
                    input_tokens,
                    output_tokens,
                    latency_ms,
                    cost_cents,
                )

                # Sprint 179 — ADR-058 Pattern A: scrub credentials
                # before content enters agent_messages or LLM context.
                scrubber = OutputScrubber()
                content, scrub_violations = scrubber.scrub(content)
                if scrub_violations:
                    logger.warning(
                        "TRACE_SCRUB_INVOKER provider=%s, patterns=%s",
                        config.provider,
                        scrub_violations,
                    )

                return InvocationResult(
                    success=True,
                    content=content,
                    provider_used=config.provider,
                    model_used=config.model,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    latency_ms=latency_ms,
                    cost_cents=cost_cents,
                    attempts=attempt_count,
                )

            except Exception as e:
                latency_ms = int((time.monotonic() - start_time) * 1000)
                reason, action, error_string = self.classifier.classify_and_route(
                    error=e,
                    provider_key=config.profile_key,
                )

                failed_attempts.append((config.provider, reason, str(e)))

                if action == FailoverAction.ABORT:
                    logger.warning(
                        "TRACE_PROVIDER status=failed: provider=%s, "
                        "reason=%s, action=abort, error=%s",
                        config.provider,
                        reason.value,
                        e,
                    )
                    raise AllProvidersFailedError(failed_attempts)

                if action == FailoverAction.RETRY:
                    # Error-as-string for LLM self-correction (Nanobot N3)
                    logger.info(
                        "Provider RETRY (error-as-string): provider=%s, reason=%s",
                        config.provider,
                        reason.value,
                    )
                    return InvocationResult(
                        success=False,
                        content=error_string,
                        provider_used=config.provider,
                        model_used=config.model,
                        latency_ms=latency_ms,
                        failover_reason=reason.value,
                        attempts=attempt_count,
                    )

                # FALLBACK: set cooldown and try next
                await self._set_cooldown(config.profile_key, reason)
                logger.info(
                    "TRACE_PROVIDER status=failed: provider=%s, "
                    "reason=%s, action=fallback, cooldown=%ds",
                    config.provider,
                    reason.value,
                    COOLDOWN_TTLS.get(reason, 0),
                )

        raise AllProvidersFailedError(failed_attempts)

    async def _call_provider(
        self,
        config: ProviderConfig,
        messages: list[dict[str, Any]],
        system_prompt: str | None,
        max_tokens: int,
        temperature: float,
    ) -> tuple[str, int, int]:
        """
        Call a specific provider's API.

        Returns:
            (content, input_tokens, output_tokens)

        Raises:
            Exception on provider error (classified by caller).
        """
        if config.provider == "ollama":
            return await self._call_ollama(config, messages, system_prompt, max_tokens, temperature)
        elif config.provider == "anthropic":
            return await self._call_anthropic(config, messages, system_prompt, max_tokens, temperature)
        else:
            raise AgentInvokerError(f"Unknown provider: {config.provider}")

    async def _call_ollama(
        self,
        config: ProviderConfig,
        messages: list[dict[str, Any]],
        system_prompt: str | None,
        max_tokens: int,
        temperature: float,
    ) -> tuple[str, int, int]:
        """
        Call Ollama REST API (/api/chat).

        Uses httpx for async HTTP. Falls back to requests if httpx unavailable.
        """
        import httpx

        ollama_url = "http://api.nhatquangholding.com:11434/api/chat"

        ollama_messages = []
        if system_prompt:
            ollama_messages.append({"role": "system", "content": system_prompt})
        ollama_messages.extend(messages)

        payload = {
            "model": config.model,
            "messages": ollama_messages,
            "stream": False,
            "options": {
                "num_predict": max_tokens,
                "temperature": temperature,
            },
        }

        async with httpx.AsyncClient(timeout=config.timeout_seconds) as client:
            response = await client.post(ollama_url, json=payload)
            response.raise_for_status()

        data = response.json()
        content = data.get("message", {}).get("content", "")
        input_tokens = data.get("prompt_eval_count", 0)
        output_tokens = data.get("eval_count", 0)

        return content, input_tokens, output_tokens

    async def _call_anthropic(
        self,
        config: ProviderConfig,
        messages: list[dict[str, Any]],
        system_prompt: str | None,
        max_tokens: int,
        temperature: float,
    ) -> tuple[str, int, int]:
        """
        Call Anthropic Messages API.

        Uses httpx for async HTTP with API key from environment.
        """
        import os
        import httpx

        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise AgentInvokerError("ANTHROPIC_API_KEY not set")

        anthropic_url = "https://api.anthropic.com/v1/messages"

        payload: dict[str, Any] = {
            "model": config.model,
            "max_tokens": max_tokens,
            "messages": messages,
        }
        if system_prompt:
            payload["system"] = system_prompt
        if temperature != 1.0:
            payload["temperature"] = temperature

        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

        async with httpx.AsyncClient(timeout=config.timeout_seconds) as client:
            response = await client.post(anthropic_url, json=payload, headers=headers)
            response.raise_for_status()

        data = response.json()
        content_blocks = data.get("content", [])
        content = "".join(
            block.get("text", "") for block in content_blocks if block.get("type") == "text"
        )
        usage = data.get("usage", {})
        input_tokens = usage.get("input_tokens", 0)
        output_tokens = usage.get("output_tokens", 0)

        return content, input_tokens, output_tokens

    @staticmethod
    def _estimate_cost(provider: str, input_tokens: int, output_tokens: int) -> int:
        """
        Estimate cost in cents for a provider invocation.

        Ollama: $50/month flat → amortized ~$0.002/1K tokens
        Anthropic: ~$3/1M input, ~$15/1M output (Sonnet pricing)
        """
        if provider == "ollama":
            # Flat rate, amortized cost is negligible
            return 0
        elif provider == "anthropic":
            # Approximate Sonnet pricing in cents
            input_cost = (input_tokens / 1_000_000) * 300  # $3/1M = 300 cents/1M
            output_cost = (output_tokens / 1_000_000) * 1500  # $15/1M = 1500 cents/1M
            return max(1, int(input_cost + output_cost))
        return 0

    async def _is_on_cooldown(self, key: ProviderProfileKey) -> bool:
        """Check if provider is on cooldown via Redis."""
        if self.redis is None:
            return False

        try:
            result = await self.redis.get(key.cooldown_redis_key)  # type: ignore[union-attr]
            return result is not None
        except Exception:
            # Redis failure → skip cooldown check (invoke anyway)
            return False

    async def _set_cooldown(
        self, key: ProviderProfileKey, reason: FailoverReason
    ) -> None:
        """Set cooldown for a provider in Redis with TTL based on error reason."""
        if self.redis is None:
            return

        ttl = COOLDOWN_TTLS.get(reason, 0)
        if ttl <= 0:
            return

        try:
            await self.redis.setex(  # type: ignore[union-attr]
                key.cooldown_redis_key,
                ttl,
                reason.value,
            )
            logger.debug(
                "Cooldown set: key=%s, ttl=%ds, reason=%s",
                key,
                ttl,
                reason.value,
            )
        except Exception as e:
            # Redis failure is non-fatal
            logger.warning(
                "Failed to set cooldown (non-fatal): key=%s, error=%s",
                key,
                e,
            )
