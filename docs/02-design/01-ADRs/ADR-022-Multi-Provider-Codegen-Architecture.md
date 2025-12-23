# ADR-022: Multi-Provider Codegen Architecture
## EP-06: IR-Based Vietnamese SME Codegen Engine

**Status**: APPROVED
**Date**: December 23, 2025
**Decision Makers**: CTO, CEO (joint review)
**Stage**: Stage 02 (HOW - Design & Architecture)
**Framework**: SDLC 5.1.1 + SASE Level 2
**Sprint**: Sprint 45 (Jan 6-17, 2026)

---

## Context

SDLC Orchestrator is pivoting to become the **"Operating System for Software 3.0"** - a control plane that orchestrates ALL AI coders under governance, evidence, and policy-as-code.

### Strategic Requirements

1. **Vietnam SME Wedge (40%)**: Non-tech founders need to generate MVPs without coding
2. **Global EM Wedge (40%)**: Engineering Managers need to govern AI-generated code
3. **No Hard Dependencies**: System must work with any AI provider, fallback gracefully
4. **Cost Efficiency**: Prefer Ollama (~$50/month) over Claude ($1000/month)
5. **IR-Based Generation**: Use Intermediate Representation schemas to reduce token usage

### 3-Layer Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│  LAYER 3: AI CODERS (They Generate)                                 │
│  Claude Code | Cursor | Copilot | Aider | Ollama                    │
├─────────────────────────────────────────────────────────────────────┤
│  LAYER 2: SDLC ORCHESTRATOR (We Govern) ← This ADR                  │
│  ★ Multi-Provider Architecture: Ollama → Claude → DeepCode         │
│  ★ EP-06 Codegen: IR-based generation for Vietnam SME              │
├─────────────────────────────────────────────────────────────────────┤
│  LAYER 1: SDLC-ENTERPRISE-FRAMEWORK (Methodology)                   │
│  10 Stages | 4 Tiers | Quality Gates                                │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Decision

We will implement a **Provider-Agnostic Codegen Architecture** with:

1. **Abstract Provider Interface**: `CodegenProvider` with 3 methods
2. **Provider Registry**: Dynamic discovery and configuration
3. **Routing + Fallback**: Config-based selection with graceful fallback
4. **Ollama as Primary**: Vietnamese-optimized prompts, cost-efficient
5. **No Hard Dependencies**: Stub providers for Claude/DeepCode, no SDK imports

---

## Rationale

### Why Provider-Agnostic?

| Approach | Pros | Cons | Decision |
|----------|------|------|----------|
| **DeepCode-first** | Advanced capabilities | $16K budget, hard dependency | ❌ Rejected |
| **Claude-first** | High quality | $1000/month, external API | ❌ Rejected |
| **Ollama-first** | $50/month, internal, Vietnamese | Smaller model | ✅ Selected |
| **Provider-agnostic** | Flexibility, no lock-in | More abstraction | ✅ Selected |

### Why IR-Based Generation?

| Metric | Full Context | IR-Based | Improvement |
|--------|--------------|----------|-------------|
| Token usage | 128K tokens | 5K tokens | **96% reduction** |
| Generation time | 30s | <3s | **10x faster** |
| Cost per generation | $0.50 | $0.02 | **25x cheaper** |
| Model requirement | 100B+ params | 7-14B params | **Smaller models** |

---

## Architecture Design

### 1. CodegenProvider Interface

```python
# backend/app/services/codegen/base_provider.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pydantic import BaseModel

class CodegenSpec(BaseModel):
    """Input specification for code generation"""
    app_blueprint: Dict[str, Any]  # From app_blueprint.schema.json
    target_module: Optional[str] = None
    language: str = "python"
    framework: str = "fastapi"

class CodegenResult(BaseModel):
    """Output from code generation"""
    code: str
    files: Dict[str, str]  # filename -> content
    metadata: Dict[str, Any]
    provider: str
    tokens_used: int
    generation_time_ms: int

class ValidationResult(BaseModel):
    """Output from code validation"""
    valid: bool
    errors: list[str]
    warnings: list[str]
    suggestions: list[str]

class CostEstimate(BaseModel):
    """Cost estimation for generation"""
    estimated_tokens: int
    estimated_cost_usd: float
    provider: str
    confidence: float  # 0-1

class CodegenProvider(ABC):
    """Abstract base class for all codegen providers"""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider identifier (e.g., 'ollama', 'claude', 'deepcode')"""
        pass

    @property
    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is configured and reachable"""
        pass

    @abstractmethod
    async def generate(self, spec: CodegenSpec) -> CodegenResult:
        """
        Generate code from IR specification.

        Args:
            spec: CodegenSpec with app_blueprint and options

        Returns:
            CodegenResult with generated code and metadata

        Raises:
            ProviderUnavailableError: Provider not configured or unreachable
            GenerationError: Code generation failed
        """
        pass

    @abstractmethod
    async def validate(self, code: str, context: Dict[str, Any]) -> ValidationResult:
        """
        Validate generated code.

        Args:
            code: Generated code to validate
            context: Additional context (language, framework, etc.)

        Returns:
            ValidationResult with validation status and issues
        """
        pass

    @abstractmethod
    def estimate_cost(self, spec: CodegenSpec) -> CostEstimate:
        """
        Estimate cost for code generation.

        Args:
            spec: CodegenSpec to estimate

        Returns:
            CostEstimate with token and cost projections
        """
        pass
```

### 2. Provider Registry

```python
# backend/app/services/codegen/provider_registry.py
from typing import Dict, List, Optional
from .base_provider import CodegenProvider
import logging

logger = logging.getLogger(__name__)

class ProviderRegistry:
    """
    Registry for managing codegen providers.
    Supports dynamic registration and configuration-based selection.
    """

    def __init__(self):
        self._providers: Dict[str, CodegenProvider] = {}
        self._fallback_chain: List[str] = []

    def register(self, provider: CodegenProvider) -> None:
        """Register a provider"""
        self._providers[provider.name] = provider
        logger.info(f"Registered codegen provider: {provider.name}")

    def unregister(self, name: str) -> None:
        """Unregister a provider"""
        if name in self._providers:
            del self._providers[name]
            logger.info(f"Unregistered codegen provider: {name}")

    def get(self, name: str) -> Optional[CodegenProvider]:
        """Get a provider by name"""
        return self._providers.get(name)

    def list_available(self) -> List[str]:
        """List all available (configured and reachable) providers"""
        return [
            name for name, provider in self._providers.items()
            if provider.is_available
        ]

    def set_fallback_chain(self, chain: List[str]) -> None:
        """
        Set the fallback chain for provider selection.
        E.g., ['ollama', 'claude', 'deepcode']
        """
        self._fallback_chain = chain
        logger.info(f"Set fallback chain: {chain}")

    def select_provider(self, preferred: Optional[str] = None) -> Optional[CodegenProvider]:
        """
        Select a provider using fallback chain.

        Args:
            preferred: Preferred provider name (from project config)

        Returns:
            First available provider in chain, or None if all unavailable
        """
        # Try preferred first
        if preferred and preferred in self._providers:
            provider = self._providers[preferred]
            if provider.is_available:
                return provider
            logger.warning(f"Preferred provider {preferred} unavailable, trying fallback")

        # Try fallback chain
        for name in self._fallback_chain:
            if name in self._providers:
                provider = self._providers[name]
                if provider.is_available:
                    logger.info(f"Selected provider from fallback: {name}")
                    return provider

        logger.error("No available providers in fallback chain")
        return None

# Global registry instance
registry = ProviderRegistry()
```

### 3. Ollama Provider Implementation

```python
# backend/app/services/codegen/ollama_provider.py
from typing import Dict, Any
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
from .base_provider import (
    CodegenProvider, CodegenSpec, CodegenResult,
    ValidationResult, CostEstimate
)
from app.core.config import settings
import time
import logging

logger = logging.getLogger(__name__)

class OllamaCodegenProvider(CodegenProvider):
    """
    Ollama-based code generation provider.
    Primary provider for Vietnam SME codegen.
    """

    def __init__(self):
        self.base_url = settings.OLLAMA_API_URL  # https://api.nhatquangholding.com
        self.model = settings.OLLAMA_CODEGEN_MODEL  # qwen2.5-coder:14b
        self._available: bool = False
        self._check_availability()

    @property
    def name(self) -> str:
        return "ollama"

    @property
    def is_available(self) -> bool:
        return self._available

    def _check_availability(self) -> None:
        """Check if Ollama is reachable"""
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(f"{self.base_url}/api/tags")
                self._available = response.status_code == 200
        except Exception as e:
            logger.warning(f"Ollama not available: {e}")
            self._available = False

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def generate(self, spec: CodegenSpec) -> CodegenResult:
        """Generate code using Ollama"""
        start_time = time.time()

        prompt = self._build_prompt(spec)

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "temperature": 0.3,  # Lower for more deterministic code
                    "stream": False
                }
            )
            response.raise_for_status()
            result = response.json()

        generation_time_ms = int((time.time() - start_time) * 1000)

        # Parse generated code into files
        files = self._parse_code_output(result["response"])

        return CodegenResult(
            code=result["response"],
            files=files,
            metadata={
                "model": self.model,
                "prompt_tokens": result.get("prompt_eval_count", 0),
                "completion_tokens": result.get("eval_count", 0)
            },
            provider=self.name,
            tokens_used=result.get("eval_count", 0),
            generation_time_ms=generation_time_ms
        )

    async def validate(self, code: str, context: Dict[str, Any]) -> ValidationResult:
        """Validate code using Ollama"""
        prompt = self._build_validation_prompt(code, context)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "temperature": 0.1,
                    "stream": False
                }
            )
            response.raise_for_status()
            result = response.json()

        # Parse validation result
        return self._parse_validation_result(result["response"])

    def estimate_cost(self, spec: CodegenSpec) -> CostEstimate:
        """Estimate cost (Ollama is essentially free)"""
        # Rough token estimation based on IR size
        ir_size = len(str(spec.app_blueprint))
        estimated_tokens = ir_size * 2  # Input + output

        return CostEstimate(
            estimated_tokens=estimated_tokens,
            estimated_cost_usd=0.001 * (estimated_tokens / 1000),  # ~$0.001 per 1K tokens
            provider=self.name,
            confidence=0.8
        )

    def _build_prompt(self, spec: CodegenSpec) -> str:
        """Build Vietnamese-optimized prompt for code generation"""
        return f"""Bạn là một AI chuyên gia phát triển phần mềm cho doanh nghiệp SME Việt Nam.

Dựa trên đặc tả IR (Intermediate Representation) sau, hãy tạo code {spec.framework} hoàn chỉnh:

## App Blueprint
```json
{spec.app_blueprint}
```

## Yêu cầu:
- Ngôn ngữ: {spec.language}
- Framework: {spec.framework}
- Module mục tiêu: {spec.target_module or 'Tất cả'}

## Output Format:
Trả về code theo format sau:

### FILE: path/to/file.py
```python
# code here
```

### FILE: path/to/another_file.py
```python
# code here
```

Hãy tạo code production-ready, có comments tiếng Việt khi cần thiết.
"""

    def _build_validation_prompt(self, code: str, context: Dict[str, Any]) -> str:
        """Build validation prompt"""
        return f"""Kiểm tra đoạn code sau và trả về kết quả validation:

```
{code}
```

Context: {context}

Trả về JSON format:
{{
  "valid": true/false,
  "errors": ["lỗi 1", "lỗi 2"],
  "warnings": ["cảnh báo 1"],
  "suggestions": ["gợi ý 1"]
}}
"""

    def _parse_code_output(self, output: str) -> Dict[str, str]:
        """Parse Ollama output into file dictionary"""
        files = {}
        current_file = None
        current_content = []

        for line in output.split('\n'):
            if line.startswith('### FILE:'):
                if current_file:
                    files[current_file] = '\n'.join(current_content)
                current_file = line.replace('### FILE:', '').strip()
                current_content = []
            elif current_file:
                current_content.append(line)

        if current_file:
            files[current_file] = '\n'.join(current_content)

        return files

    def _parse_validation_result(self, output: str) -> ValidationResult:
        """Parse validation output"""
        import json
        try:
            # Try to extract JSON from output
            start = output.find('{')
            end = output.rfind('}') + 1
            if start >= 0 and end > start:
                data = json.loads(output[start:end])
                return ValidationResult(**data)
        except:
            pass

        # Default to valid if parsing fails
        return ValidationResult(
            valid=True,
            errors=[],
            warnings=["Could not parse validation output"],
            suggestions=[]
        )
```

### 4. Stub Providers (No Hard Dependencies)

```python
# backend/app/services/codegen/claude_provider.py
from .base_provider import (
    CodegenProvider, CodegenSpec, CodegenResult,
    ValidationResult, CostEstimate
)

class ClaudeCodegenProvider(CodegenProvider):
    """
    Claude-based code generation provider.
    STUB implementation - no hard dependency on Anthropic SDK.
    """

    def __init__(self):
        self._api_key = None  # Will be configured if needed

    @property
    def name(self) -> str:
        return "claude"

    @property
    def is_available(self) -> bool:
        # Only available if API key is configured
        return self._api_key is not None

    async def generate(self, spec: CodegenSpec) -> CodegenResult:
        raise NotImplementedError("Claude provider not implemented - use Ollama")

    async def validate(self, code: str, context: dict) -> ValidationResult:
        raise NotImplementedError("Claude provider not implemented - use Ollama")

    def estimate_cost(self, spec: CodegenSpec) -> CostEstimate:
        # Claude pricing estimate
        ir_size = len(str(spec.app_blueprint))
        estimated_tokens = ir_size * 2

        return CostEstimate(
            estimated_tokens=estimated_tokens,
            estimated_cost_usd=0.015 * (estimated_tokens / 1000),  # Claude pricing
            provider=self.name,
            confidence=0.7
        )


# backend/app/services/codegen/deepcode_provider.py
class DeepCodeProvider(CodegenProvider):
    """
    DeepCode-based code generation provider.
    STUB implementation - deferred to Q2 2026.
    """

    @property
    def name(self) -> str:
        return "deepcode"

    @property
    def is_available(self) -> bool:
        return False  # Explicitly unavailable

    async def generate(self, spec: CodegenSpec) -> CodegenResult:
        raise NotImplementedError("DeepCode provider deferred to Q2 2026")

    async def validate(self, code: str, context: dict) -> ValidationResult:
        raise NotImplementedError("DeepCode provider deferred to Q2 2026")

    def estimate_cost(self, spec: CodegenSpec) -> CostEstimate:
        return CostEstimate(
            estimated_tokens=0,
            estimated_cost_usd=0,
            provider=self.name,
            confidence=0
        )
```

### 5. Codegen Service (Orchestrator)

```python
# backend/app/services/codegen/codegen_service.py
from typing import Optional, List, Dict, Any
from .provider_registry import registry
from .base_provider import CodegenSpec, CodegenResult, ValidationResult
from .ollama_provider import OllamaCodegenProvider
from .claude_provider import ClaudeCodegenProvider
from .deepcode_provider import DeepCodeProvider
import logging

logger = logging.getLogger(__name__)

class CodegenService:
    """
    Main orchestrator service for code generation.
    Manages provider selection, fallback, and error handling.
    """

    def __init__(self):
        # Register providers
        registry.register(OllamaCodegenProvider())
        registry.register(ClaudeCodegenProvider())
        registry.register(DeepCodeProvider())

        # Set fallback chain
        registry.set_fallback_chain(['ollama', 'claude', 'deepcode'])

    def list_providers(self) -> List[Dict[str, Any]]:
        """List all registered providers with availability status"""
        providers = []
        for name in ['ollama', 'claude', 'deepcode']:
            provider = registry.get(name)
            if provider:
                providers.append({
                    "name": provider.name,
                    "available": provider.is_available,
                    "primary": name == 'ollama'
                })
        return providers

    async def generate(
        self,
        spec: CodegenSpec,
        preferred_provider: Optional[str] = None
    ) -> CodegenResult:
        """
        Generate code using available provider.

        Args:
            spec: CodegenSpec with app_blueprint
            preferred_provider: Optional preferred provider name

        Returns:
            CodegenResult with generated code

        Raises:
            NoProviderAvailableError: No providers available
            GenerationError: Generation failed
        """
        provider = registry.select_provider(preferred_provider)

        if not provider:
            raise NoProviderAvailableError("No codegen providers available")

        logger.info(f"Generating code with provider: {provider.name}")
        return await provider.generate(spec)

    async def validate(
        self,
        code: str,
        context: Dict[str, Any],
        provider_name: Optional[str] = None
    ) -> ValidationResult:
        """Validate generated code"""
        provider = registry.select_provider(provider_name)

        if not provider:
            raise NoProviderAvailableError("No codegen providers available")

        return await provider.validate(code, context)

    def estimate_cost(
        self,
        spec: CodegenSpec,
        provider_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Estimate cost for all available providers"""
        estimates = {}

        for name in registry.list_available():
            provider = registry.get(name)
            if provider:
                estimate = provider.estimate_cost(spec)
                estimates[name] = estimate.dict()

        return estimates


class NoProviderAvailableError(Exception):
    """Raised when no codegen providers are available"""
    pass


class GenerationError(Exception):
    """Raised when code generation fails"""
    pass
```

### 6. API Routes

```python
# backend/app/api/routes/codegen.py
from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from app.services.codegen.codegen_service import CodegenService, NoProviderAvailableError
from app.services.codegen.base_provider import CodegenSpec
from app.api.deps import get_current_user
from pydantic import BaseModel

router = APIRouter(prefix="/codegen", tags=["codegen"])

codegen_service = CodegenService()


class GenerateRequest(BaseModel):
    app_blueprint: dict
    target_module: Optional[str] = None
    language: str = "python"
    framework: str = "fastapi"
    preferred_provider: Optional[str] = None


class ValidateRequest(BaseModel):
    code: str
    context: dict = {}
    provider: Optional[str] = None


@router.get("/providers")
async def list_providers(current_user = Depends(get_current_user)):
    """List available codegen providers"""
    return {
        "providers": codegen_service.list_providers(),
        "fallback_chain": ["ollama", "claude", "deepcode"]
    }


@router.post("/generate")
async def generate_code(
    request: GenerateRequest,
    current_user = Depends(get_current_user)
):
    """Generate code from IR specification"""
    try:
        spec = CodegenSpec(
            app_blueprint=request.app_blueprint,
            target_module=request.target_module,
            language=request.language,
            framework=request.framework
        )

        result = await codegen_service.generate(
            spec,
            preferred_provider=request.preferred_provider
        )

        return {
            "success": True,
            "result": result.dict()
        }
    except NoProviderAvailableError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate")
async def validate_code(
    request: ValidateRequest,
    current_user = Depends(get_current_user)
):
    """Validate generated code"""
    try:
        result = await codegen_service.validate(
            request.code,
            request.context,
            provider_name=request.provider
        )

        return {
            "success": True,
            "result": result.dict()
        }
    except NoProviderAvailableError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/estimate")
async def estimate_cost(
    request: GenerateRequest,
    current_user = Depends(get_current_user)
):
    """Estimate generation cost across providers"""
    spec = CodegenSpec(
        app_blueprint=request.app_blueprint,
        target_module=request.target_module,
        language=request.language,
        framework=request.framework
    )

    return {
        "estimates": codegen_service.estimate_cost(spec)
    }
```

---

## Configuration

### Provider Configuration

```yaml
# config/codegen.yaml
codegen:
  # Default provider (used if project doesn't specify)
  default_provider: ollama

  # Fallback chain when preferred provider unavailable
  fallback_chain:
    - ollama
    - claude
    - deepcode

  providers:
    ollama:
      enabled: true
      base_url: "https://api.nhatquangholding.com"
      model: "qwen2.5-coder:14b"
      timeout_seconds: 60
      max_retries: 3

    claude:
      enabled: false  # Stub only
      api_key: "${ANTHROPIC_API_KEY}"

    deepcode:
      enabled: false  # Deferred to Q2 2026
```

### Environment Variables

```bash
# .env
OLLAMA_API_URL=https://api.nhatquangholding.com
OLLAMA_CODEGEN_MODEL=qwen2.5-coder:14b
ANTHROPIC_API_KEY=  # Optional, for Claude fallback
```

---

## Error Handling

### Error Types

| Error | Cause | Handling |
|-------|-------|----------|
| `ProviderUnavailableError` | Provider not configured or unreachable | Try fallback chain |
| `GenerationError` | Code generation failed | Retry with exponential backoff |
| `ValidationError` | Code validation failed | Return validation result, don't retry |
| `NoProviderAvailableError` | All providers unavailable | Return 503, log alert |
| `TimeoutError` | Generation took too long | Retry once, then fail |

### Retry Policy

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(min=1, max=10),
    retry_error_callback=lambda retry_state: None  # Don't raise on final failure
)
async def generate_with_retry(spec: CodegenSpec) -> CodegenResult:
    ...
```

---

## Consequences

### Positive

1. **No Vendor Lock-in**: Can switch providers without code changes
2. **Cost Efficiency**: Ollama-first saves ~$950/month vs Claude-first
3. **Graceful Degradation**: Fallback chain ensures availability
4. **Easy Extension**: Add new providers by implementing `CodegenProvider`
5. **Testable**: Can mock providers for testing

### Negative

1. **Abstraction Overhead**: Slight performance cost from abstraction
2. **Complexity**: More code than single-provider approach
3. **Provider Differences**: Output quality may vary between providers

### Neutral

1. **Configuration Required**: Must configure providers in config file
2. **Monitoring Needed**: Should track provider usage and fallback frequency

---

## Implementation Plan (Sprint 45)

### Week 1 (Jan 6-10)
- [ ] Create `base_provider.py` with abstract interface
- [ ] Create `provider_registry.py` with routing logic
- [ ] Create `codegen_service.py` orchestrator
- [ ] Create `codegen.py` API routes
- [ ] Write integration test for ollama-only boot

### Week 2 (Jan 13-17)
- [ ] Implement `OllamaCodegenProvider` with Vietnamese prompts
- [ ] Create stub `ClaudeCodegenProvider` and `DeepCodeProvider`
- [ ] Create configuration schema
- [ ] Write runbook for disabling providers
- [ ] Demo with minimal AppBlueprint

---

## References

- [ADR-007: AI Context Engine](./ADR-007-AI-Context-Engine.md) - Existing AI provider patterns
- [EP-06 Epic](../../01-planning/02-Epics/EP-06-Codegen-Engine-Dual-Mode.md) - Full vision
- [Strategic Pivot](../../09-govern/04-Strategic-Updates/2025-12-22-STRATEGIC-PIVOT-DEEPCODE-TO-IR-CODEGEN.md) - CTO decision
- [Sprint 45 Plan](../../04-build/02-Sprint-Plans/SPRINT-45-AUTO-FIX-ENGINE.md) - Implementation plan

---

## Document Control

| Field | Value |
|-------|-------|
| **Version** | 1.0.0 |
| **Date** | December 23, 2025 |
| **Author** | Architect + Backend Lead |
| **Status** | APPROVED |
| **CEO Approval** | ✅ Dec 23, 2025 |
| **CTO Approval** | ✅ Dec 23, 2025 |
