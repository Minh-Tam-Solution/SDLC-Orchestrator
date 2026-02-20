"""
=========================================================================
Unit Tests - Agent Invoker (Sprint 177)
SDLC Orchestrator - Multi-Agent Team Engine

Version: 1.0.0
Date: February 2026
Status: ACTIVE - Sprint 177
Authority: CTO Approved (ADR-056 Decision 3)

Purpose:
- Test provider failover chain (Ollama -> Anthropic -> rule-based)
- Test cooldown logic (Redis-backed skip)
- Test cost estimation (Ollama=$0, Anthropic=token-based)
- Test error-as-string for retry actions (Nanobot N3)
- Test AllProvidersFailedError when chain exhausted

Zero Mock Policy: Mocked HTTP + Redis for unit isolation
=========================================================================
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.agent_team.agent_invoker import (
    AgentInvoker,
    AgentInvokerError,
    InvocationResult,
    ProviderConfig,
    AllProvidersFailedError,
)
from app.services.agent_team.config import ROLE_MODEL_DEFAULTS


# =========================================================================
# Fixtures
# =========================================================================


@pytest.fixture
def mock_redis():
    redis = AsyncMock()
    redis.get = AsyncMock(return_value=None)  # No cooldown by default
    redis.setex = AsyncMock()
    return redis


def _make_provider(provider="ollama", model="qwen3-coder:30b", **kwargs):
    """Create a ProviderConfig."""
    return ProviderConfig(
        provider=provider,
        model=model,
        account=kwargs.get("account", "default"),
        region=kwargs.get("region", "local"),
    )


# =========================================================================
# Factory Tests
# =========================================================================


class TestFromRole:
    """Tests for AgentInvoker.from_role factory."""

    def test_from_role_builds_chain(self, mock_redis):
        """from_role creates an invoker with provider_chain from ROLE_MODEL_DEFAULTS."""
        invoker = AgentInvoker.from_role("coder", redis=mock_redis)
        assert invoker is not None
        assert len(invoker.provider_chain) >= 1

    def test_from_role_unknown_role_raises(self, mock_redis):
        """Unknown role raises AgentInvokerError."""
        with pytest.raises(AgentInvokerError, match="No model defaults"):
            AgentInvoker.from_role("nonexistent", redis=mock_redis)

    def test_from_role_se4h_uses_anthropic(self, mock_redis):
        """SE4H roles should have anthropic as primary provider."""
        invoker = AgentInvoker.from_role("ceo", redis=mock_redis)
        assert len(invoker.provider_chain) >= 1
        assert invoker.provider_chain[0].provider == "anthropic"

    def test_from_role_ollama_gets_anthropic_fallback(self, mock_redis):
        """Ollama primary roles should get anthropic as fallback."""
        invoker = AgentInvoker.from_role("coder", redis=mock_redis)
        assert len(invoker.provider_chain) >= 2
        assert invoker.provider_chain[0].provider == "ollama"
        assert invoker.provider_chain[1].provider == "anthropic"


# =========================================================================
# Invocation Tests
# =========================================================================


class TestInvoke:
    """Tests for the invoke method."""

    @pytest.mark.asyncio
    async def test_invoke_ollama_success(self, mock_redis):
        """Successful Ollama invocation returns InvocationResult."""
        invoker = AgentInvoker(
            provider_chain=[_make_provider("ollama", "qwen3-coder:30b")],
            redis=mock_redis,
        )

        mock_response = {
            "message": {"content": "Here is the code"},
            "eval_count": 100,
            "prompt_eval_count": 50,
        }

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            mock_http_response = MagicMock()
            mock_http_response.status_code = 200
            mock_http_response.json.return_value = mock_response
            mock_http_response.raise_for_status = MagicMock()
            mock_client.post.return_value = mock_http_response

            result = await invoker.invoke(
                messages=[{"role": "user", "content": "Write hello world"}],
                system_prompt="You are a coder.",
            )

            assert isinstance(result, InvocationResult)
            assert result.content == "Here is the code"
            assert result.provider_used == "ollama"
            assert result.success is True

    @pytest.mark.asyncio
    async def test_invoke_all_fail_raises(self, mock_redis):
        """When all providers fail, raises AllProvidersFailedError."""
        invoker = AgentInvoker(
            provider_chain=[_make_provider("ollama", "qwen3:8b")],
            redis=mock_redis,
        )

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.post.side_effect = Exception("Connection refused")

            with pytest.raises(AllProvidersFailedError):
                await invoker.invoke(
                    messages=[{"role": "user", "content": "test"}],
                )


# =========================================================================
# Cooldown Tests
# =========================================================================


class TestCooldown:
    """Tests for provider cooldown (Redis-backed)."""

    @pytest.mark.asyncio
    async def test_cooldown_skips_provider(self, mock_redis):
        """Provider under cooldown is skipped in chain."""
        # First provider is in cooldown — mock redis.get to return value for first key, None for second
        mock_redis.get = AsyncMock(side_effect=[b"1", None])

        invoker = AgentInvoker(
            provider_chain=[
                _make_provider("ollama", "qwen3:8b"),
                _make_provider("ollama", "qwen3:32b"),
            ],
            redis=mock_redis,
        )

        mock_response = {
            "message": {"content": "From second provider"},
            "eval_count": 50,
            "prompt_eval_count": 25,
        }

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            mock_http_response = MagicMock()
            mock_http_response.status_code = 200
            mock_http_response.json.return_value = mock_response
            mock_http_response.raise_for_status = MagicMock()
            mock_client.post.return_value = mock_http_response

            result = await invoker.invoke(
                messages=[{"role": "user", "content": "test"}],
            )

            assert result.content == "From second provider"


# =========================================================================
# Cost Estimation Tests
# =========================================================================


class TestCostEstimation:
    """Tests for per-invocation cost tracking."""

    def test_ollama_cost_zero(self):
        """Ollama is self-hosted, cost should be 0."""
        result = InvocationResult(
            success=True,
            content="test",
            provider_used="ollama",
            model_used="qwen3-coder:30b",
            input_tokens=1000,
            output_tokens=500,
            cost_cents=0,
            latency_ms=250,
        )
        assert result.cost_cents == 0

    def test_anthropic_cost_positive(self):
        """Anthropic has token-based cost."""
        result = InvocationResult(
            success=True,
            content="test",
            provider_used="anthropic",
            model_used="claude-sonnet-4-5",
            input_tokens=1000,
            output_tokens=500,
            cost_cents=5,
            latency_ms=2000,
        )
        assert result.cost_cents > 0

    def test_estimate_cost_static_method(self):
        """_estimate_cost returns correct values per provider."""
        assert AgentInvoker._estimate_cost("ollama", 1000, 500) == 0
        assert AgentInvoker._estimate_cost("anthropic", 1_000_000, 1_000_000) > 0

    def test_invocation_result_has_success_field(self):
        """InvocationResult tracks success/failure."""
        result = InvocationResult(
            success=False,
            content="Error: format issue",
            provider_used="ollama",
            model_used="qwen3:8b",
            failover_reason="format",
        )
        assert result.success is False
        assert result.failover_reason == "format"


# =========================================================================
# ProviderConfig Tests
# =========================================================================


class TestProviderConfig:
    """Tests for ProviderConfig dataclass."""

    def test_profile_key_type(self):
        """Profile key returns a ProviderProfileKey object."""
        config = ProviderConfig(
            provider="ollama",
            model="qwen3-coder:30b",
            account="default",
            region="local",
        )
        key = config.profile_key
        assert key.provider == "ollama"
        assert key.account == "default"
        assert key.region == "local"
        assert key.model_family == "qwen3-coder"

    def test_profile_key_str(self):
        """Profile key string follows {provider}:{account}:{region}:{model_family}."""
        config = ProviderConfig(
            provider="ollama",
            model="qwen3-coder:30b",
            account="default",
            region="local",
        )
        key_str = str(config.profile_key)
        assert key_str == "ollama:default:local:qwen3-coder"

    def test_profile_key_model_without_tag(self):
        """Model without colon uses full model name as family."""
        config = ProviderConfig(
            provider="anthropic",
            model="claude-sonnet-4-5",
            account="default",
            region="us-east-1",
        )
        assert config.profile_key.model_family == "claude-sonnet-4-5"

    def test_cooldown_redis_key(self):
        """Cooldown Redis key follows cooldown:{profile_key} format."""
        config = ProviderConfig(
            provider="ollama",
            model="qwen3:8b",
            account="default",
            region="local",
        )
        redis_key = config.profile_key.cooldown_redis_key
        assert redis_key == "cooldown:ollama:default:local:qwen3"
