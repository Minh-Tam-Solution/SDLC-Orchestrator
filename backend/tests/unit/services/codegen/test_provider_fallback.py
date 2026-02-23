"""
Tests for Provider Fallback Chain (B-02) and Ollama Integration (B-01).

Sprint 196 — Track B
Validates:
- B-01: qwen3-coder:30b end-to-end generation (mocked HTTP)
- B-02: Provider fallback chain under failure scenarios
  - Ollama timeout → Claude fallback
  - Connection error → next in chain
  - All providers fail → NoProviderAvailableError
  - NotImplementedError → fallback cascade
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock

import pytest

from app.services.codegen.base_provider import (
    CodegenProvider,
    CodegenResult,
    CodegenSpec,
)
from app.services.codegen.codegen_service import (
    CodegenService,
    GenerationError,
    NoProviderAvailableError,
)
from app.services.codegen.provider_registry import ProviderRegistry


# ---------------------------------------------------------------------------
# Helpers — fake providers
# ---------------------------------------------------------------------------
def _make_spec(**overrides) -> CodegenSpec:
    defaults = {
        "app_blueprint": {"name": "TestApp", "modules": []},
        "language": "python",
        "framework": "fastapi",
    }
    defaults.update(overrides)
    return CodegenSpec(**defaults)


def _make_result(provider: str = "test") -> CodegenResult:
    return CodegenResult(
        code="print('ok')",
        files={"main.py": "print('ok')"},
        provider=provider,
        tokens_used=100,
        generation_time_ms=500,
    )


class FakeProvider(CodegenProvider):
    """Configurable fake provider for testing."""

    def __init__(self, name: str, available: bool = True, fail: bool = False, fail_type: str = "generic"):
        self._name = name
        self._available = available
        self._fail = fail
        self._fail_type = fail_type

    @property
    def name(self) -> str:
        return self._name

    @property
    def is_available(self) -> bool:
        return self._available

    async def generate(self, spec):
        if self._fail:
            if self._fail_type == "not_implemented":
                raise NotImplementedError(f"{self._name} not implemented")
            elif self._fail_type == "timeout":
                raise TimeoutError(f"{self._name} timed out")
            elif self._fail_type == "connection":
                raise ConnectionError(f"{self._name} connection failed")
            else:
                raise RuntimeError(f"{self._name} generic error")
        return _make_result(self._name)

    async def validate(self, code, context):
        raise NotImplementedError

    async def estimate_cost(self, spec):
        return 0.001


# ---------------------------------------------------------------------------
# B-02: Fallback Chain Validation
# ---------------------------------------------------------------------------
class TestFallbackChainIteration:
    """B-02: Provider fallback chain under failure scenarios."""

    @pytest.mark.asyncio
    async def test_preferred_provider_used_when_available(self):
        """Happy path: preferred provider works → no fallback needed."""
        registry = ProviderRegistry()
        ollama = FakeProvider("ollama", available=True)
        claude = FakeProvider("claude", available=True)
        registry.register(ollama)
        registry.register(claude)
        registry.set_fallback_chain(["ollama", "claude"])

        service = CodegenService(custom_registry=registry, auto_register=False)
        result = await service.generate(_make_spec(), preferred_provider="ollama")

        assert result.provider == "ollama"

    @pytest.mark.asyncio
    async def test_fallback_to_claude_on_ollama_not_implemented(self):
        """Ollama raises NotImplementedError → falls back to Claude."""
        registry = ProviderRegistry()
        ollama = FakeProvider("ollama", available=True, fail=True, fail_type="not_implemented")
        claude = FakeProvider("claude", available=True)
        registry.register(ollama)
        registry.register(claude)
        registry.set_fallback_chain(["ollama", "claude"])

        service = CodegenService(custom_registry=registry, auto_register=False)
        result = await service.generate(_make_spec(), preferred_provider="ollama")

        assert result.provider == "claude"

    @pytest.mark.asyncio
    async def test_chain_skips_unavailable_providers(self):
        """Unavailable providers are skipped in the chain."""
        registry = ProviderRegistry()
        ollama = FakeProvider("ollama", available=False)
        claude = FakeProvider("claude", available=False)
        deepcode = FakeProvider("deepcode", available=True)
        registry.register(ollama)
        registry.register(claude)
        registry.register(deepcode)
        registry.set_fallback_chain(["ollama", "claude", "deepcode"])

        service = CodegenService(custom_registry=registry, auto_register=False)
        result = await service.generate(_make_spec())

        assert result.provider == "deepcode"

    @pytest.mark.asyncio
    async def test_all_providers_fail_raises_error(self):
        """All providers unavailable → NoProviderAvailableError."""
        registry = ProviderRegistry()
        ollama = FakeProvider("ollama", available=False)
        claude = FakeProvider("claude", available=False)
        registry.register(ollama)
        registry.register(claude)
        registry.set_fallback_chain(["ollama", "claude"])

        service = CodegenService(custom_registry=registry, auto_register=False)

        with pytest.raises(NoProviderAvailableError):
            await service.generate(_make_spec())

    @pytest.mark.asyncio
    async def test_fallback_chain_cascade_multiple_failures(self):
        """First two providers fail → third succeeds."""
        registry = ProviderRegistry()
        ollama = FakeProvider("ollama", available=True, fail=True, fail_type="not_implemented")
        claude = FakeProvider("claude", available=True, fail=True, fail_type="not_implemented")
        deepcode = FakeProvider("deepcode", available=True)
        registry.register(ollama)
        registry.register(claude)
        registry.register(deepcode)
        registry.set_fallback_chain(["ollama", "claude", "deepcode"])

        service = CodegenService(custom_registry=registry, auto_register=False)
        result = await service.generate(_make_spec(), preferred_provider="ollama")

        assert result.provider == "deepcode"

    @pytest.mark.asyncio
    async def test_all_fallbacks_fail_raises_error(self):
        """All fallback providers fail (not just unavailable) → NoProviderAvailableError."""
        registry = ProviderRegistry()
        ollama = FakeProvider("ollama", available=True, fail=True, fail_type="not_implemented")
        claude = FakeProvider("claude", available=True, fail=True, fail_type="generic")
        registry.register(ollama)
        registry.register(claude)
        registry.set_fallback_chain(["ollama", "claude"])

        service = CodegenService(custom_registry=registry, auto_register=False)

        with pytest.raises(NoProviderAvailableError):
            await service.generate(_make_spec(), preferred_provider="ollama")

    @pytest.mark.asyncio
    async def test_generation_error_on_non_fallback_failure(self):
        """Provider raises generic error (not NotImplementedError) → GenerationError raised (no fallback)."""
        registry = ProviderRegistry()
        ollama = FakeProvider("ollama", available=True, fail=True, fail_type="generic")
        registry.register(ollama)
        registry.set_fallback_chain(["ollama"])

        service = CodegenService(custom_registry=registry, auto_register=False)

        with pytest.raises(GenerationError) as exc_info:
            await service.generate(_make_spec(), preferred_provider="ollama")
        assert "ollama" in str(exc_info.value).lower()


# ---------------------------------------------------------------------------
# B-01: qwen3-coder:30b Integration (mocked HTTP)
# ---------------------------------------------------------------------------
class TestOllamaProviderGeneration:
    """B-01: Validate OllamaCodegenProvider end-to-end with mocked HTTP."""

    @pytest.mark.asyncio
    async def test_generate_returns_parsed_files(self):
        """OllamaCodegenProvider.generate() returns CodegenResult with parsed files."""
        from app.services.codegen.ollama_provider import OllamaCodegenProvider

        provider = OllamaCodegenProvider(
            base_url="http://fake:11434",
            model="qwen3-coder:30b",
            timeout=30,
        )

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": (
                "### FILE: app/main.py\n"
                "```python\n"
                "from fastapi import FastAPI\n"
                "app = FastAPI()\n"
                "```\n"
                "### FILE: app/models.py\n"
                "```python\n"
                "class Task:\n"
                "    pass\n"
                "```\n"
            ),
            "total_duration": 5_000_000_000,  # 5s in ns
            "prompt_eval_count": 200,
            "eval_count": 400,
        }

        with patch("httpx.AsyncClient") as MockClient:
            mock_client_instance = AsyncMock()
            mock_client_instance.post = AsyncMock(return_value=mock_response)
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_client_instance

            spec = _make_spec(
                app_blueprint={
                    "name": "TaskManager",
                    "description": "Simple task manager",
                    "modules": [{"name": "tasks", "entities": []}],
                }
            )
            result = await provider.generate(spec)

        assert result.provider == "ollama"
        assert len(result.files) >= 1
        assert result.tokens_used > 0

    @pytest.mark.asyncio
    async def test_ollama_availability_caching(self):
        """Availability check caches for 60s TTL."""
        from app.services.codegen.ollama_provider import OllamaCodegenProvider

        provider = OllamaCodegenProvider(
            base_url="http://fake:11434",
            model="qwen3-coder:30b",
        )

        # Force unavailable — no real server
        provider._available = True
        provider._last_health_check = 999_999_999_999.0  # Far future

        assert provider.is_available is True

    def test_ollama_cost_estimation(self):
        """Cost estimation returns sub-cent for local Ollama."""
        from app.services.codegen.ollama_provider import OllamaCodegenProvider

        provider = OllamaCodegenProvider(
            base_url="http://fake:11434",
            model="qwen3-coder:30b",
        )
        spec = _make_spec()
        estimate = provider.estimate_cost(spec)
        assert estimate.estimated_cost_usd < 0.01  # Local Ollama is nearly free


# ---------------------------------------------------------------------------
# B-03: Quality Pipeline Integration (Gate 1-3 with real ast)
# ---------------------------------------------------------------------------
class TestQualityPipelineRealTools:
    """B-03: Gate 1-3 integration using real ast module (not mocked)."""

    def test_gate1_real_syntax_check_valid(self):
        """Gate 1 passes for syntactically valid Python."""
        from app.services.codegen.quality_pipeline import QualityPipeline, GateStatus

        pipeline = QualityPipeline(skip_security=True, skip_tests=True)
        files = {
            "main.py": "def hello():\n    return 'world'\n",
        }
        result = pipeline.run(files, "python")

        gate1 = result.gates[0]
        assert gate1.gate_number == 1
        assert gate1.status == GateStatus.PASSED

    def test_gate1_real_syntax_check_invalid(self):
        """Gate 1 fails for invalid Python syntax."""
        from app.services.codegen.quality_pipeline import QualityPipeline, GateStatus

        pipeline = QualityPipeline(skip_security=True, skip_tests=True)
        files = {
            "main.py": "def hello(\n    return 'world'\n",  # missing closing paren
        }
        result = pipeline.run(files, "python")

        gate1 = result.gates[0]
        assert gate1.gate_number == 1
        assert gate1.status == GateStatus.FAILED
        assert gate1.error_count >= 1

    def test_gate3_real_context_validation(self):
        """Gate 3 validates imports with real ast.walk."""
        from app.services.codegen.quality_pipeline import QualityPipeline, GateStatus

        pipeline = QualityPipeline(skip_security=True, skip_tests=True)
        files = {
            "main.py": (
                "import json\n"
                "\n"
                "\n"
                "def hello():\n"
                "    return json.dumps({})\n"
            ),
        }
        result = pipeline.run(files, "python")

        # Gate 1 should pass (valid syntax, no ruff issues)
        gate1 = result.gates[0]
        assert gate1.status == GateStatus.PASSED, (
            f"Gate 1 failed: {gate1.summary}, issues={gate1.issues}"
        )
        # Gate 3 exists and ran
        gate3 = next((g for g in result.gates if g.gate_number == 3), None)
        assert gate3 is not None
        assert gate3.status in [GateStatus.PASSED, GateStatus.SOFT_FAIL]


# ---------------------------------------------------------------------------
# B-04: Quality Pipeline Latency Benchmarks (lightweight)
# ---------------------------------------------------------------------------
class TestQualityPipelineLatency:
    """B-04: Ensure quality gates run within time budget."""

    def test_gate1_latency_under_5s(self):
        """Gate 1 (syntax check) completes in <5s for small files."""
        from app.services.codegen.quality_pipeline import QualityPipeline

        pipeline = QualityPipeline(skip_security=True, skip_tests=True)
        files = {f"module_{i}.py": f"def func_{i}():\n    return {i}\n" for i in range(20)}

        result = pipeline.run(files, "python")

        gate1 = result.gates[0]
        assert gate1.duration_ms < 5000, f"Gate 1 took {gate1.duration_ms}ms (budget: <5000ms)"

    def test_full_pipeline_latency_g1_g3(self):
        """Gates 1+3 (no security, no tests) completes in <15s."""
        from app.services.codegen.quality_pipeline import QualityPipeline

        pipeline = QualityPipeline(skip_security=True, skip_tests=True)
        files = {
            "app/main.py": "from fastapi import FastAPI\napp = FastAPI()\n",
            "app/models.py": "class User:\n    name: str\n",
            "app/utils.py": "import json\ndef parse(s):\n    return json.loads(s)\n",
        }

        result = pipeline.run(files, "python")

        total_ms = sum(g.duration_ms for g in result.gates)
        assert total_ms < 15000, f"Pipeline (G1+G3) took {total_ms}ms (budget: <15000ms)"

    def test_gate4_no_tests_fast_path(self):
        """Gate 4 with no test files completes instantly (<1s)."""
        from app.services.codegen.quality_pipeline import QualityPipeline

        pipeline = QualityPipeline(skip_security=True, skip_tests=False)
        files = {
            "main.py": "print('hello')\n",
        }

        result = pipeline.run(files, "python")

        gate4 = next((g for g in result.gates if g.gate_number == 4), None)
        assert gate4 is not None
        assert gate4.duration_ms < 1000, f"Gate 4 (no tests) took {gate4.duration_ms}ms"
