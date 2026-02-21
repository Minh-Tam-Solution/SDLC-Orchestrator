"""
=========================================================================
Ollama AI Service - Local LLM Integration for Compliance Recommendations
SDLC Orchestrator - Stage 03 (BUILD)

Version: 1.0.0
Date: December 2, 2025
Status: ACTIVE - Sprint 21 Day 3 (AI Integration)
Authority: Backend Lead + CTO Approved
Foundation: ADR-007 (AI Context Engine - Ollama Integration), Sprint 21 Plan
Framework: SDLC 4.9.1 Complete Lifecycle

Purpose:
- Local AI inference via Ollama HTTP API
- Generate violation recommendations with context
- Cost optimization: $50/month vs $1,000/month cloud APIs
- Privacy-first: No external API calls required

Ollama Integration Strategy:
✅ Network-only access via HTTP REST API (same pattern as OPA)
✅ NO Ollama SDK imports (avoid tight coupling)
✅ Docker container isolation (ollama:11434)
✅ Fallback chain: Ollama → Claude → GPT-4 → Rule-based

Cost Savings (ADR-007):
- Ollama: $50/month (self-hosted, only electricity)
- Claude: $1,000/month (API costs)
- GPT-4: $800/month (API costs)
- Savings: $11,400/year (95% cost reduction)

Performance:
- Ollama latency: <100ms (local network)
- Cloud API latency: 300-500ms (network + inference)

Zero Mock Policy: 100% real HTTP implementation
=========================================================================
"""

import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

import requests
from requests.exceptions import ConnectionError, HTTPError, RequestException, Timeout

from app.core.config import settings

logger = logging.getLogger(__name__)


# ============================================================================
# Ollama Models Configuration
# ============================================================================


class OllamaModel(str, Enum):
    """
    Supported Ollama models for different use cases.

    Model Strategy v3.0 (December 27, 2025):
    - 10 models optimized for RTX 5090 32GB
    - Primary: qwen3-coder:30b (256K context), qwen3:32b (Vietnamese)
    - Reference: /home/nqh/shared/models/core/docs/admin/MODEL_STRATEGY_2025.md
    """

    # PRIMARY MODELS (Model Strategy v3.0)
    # Code generation - 256K context, production-ready
    QWEN3_CODER_30B = "qwen3-coder:30b"

    # Vietnamese chat - excellent Vietnamese, fast
    QWEN3_32B = "qwen3:32b"

    # Deep reasoning - thinking mode, complex analysis
    DEEPSEEK_R1_32B = "deepseek-r1:32b-qwen-distill-q4_K_M"

    # SOP RAG - structured JSON output
    MISTRAL_SMALL_24B = "mistral-small3.2:24b-instruct-2506-q4_K_M"

    # Vietnamese reasoning - cultural context
    GPT_OSS_20B = "gpt-oss:20b"

    # FAST MODELS
    # Vietnamese fast - quick responses
    QWEN3_14B = "qwen3:14b"

    # Fastest chat - real-time
    QWEN3_8B = "qwen3:8b"

    # Fast tasks - classification, simple Q&A
    MINISTRAL_8B = "ministral-3:8b-instruct-2512-q4_K_M"

    # Creative writing - marketing, storytelling
    GEMMA3_12B = "gemma3:12b"

    # EMBEDDINGS (hidden, for RAG only)
    BGE_M3 = "bge-m3:latest"

    # LEGACY MODELS (kept for backward compatibility)
    CODELLAMA_7B = "codellama:7b"
    CODELLAMA_13B = "codellama:13b"
    LLAMA2_13B = "llama2:13b"
    MISTRAL_7B = "mistral:7b"

    # Default model for compliance recommendations (Model Strategy v3.0)
    DEFAULT = "qwen3:32b"

    # Default model for code generation
    DEFAULT_CODE = "qwen3-coder:30b"

    # Default model for Vietnamese content
    DEFAULT_VIETNAMESE = "qwen3:32b"


@dataclass
class OllamaResponse:
    """Structured response from Ollama API."""

    model: str
    response: str
    done: bool
    total_duration_ns: int
    load_duration_ns: int
    prompt_eval_count: int
    eval_count: int
    eval_duration_ns: int

    @property
    def total_duration_ms(self) -> float:
        """Total duration in milliseconds."""
        return self.total_duration_ns / 1_000_000

    @property
    def tokens_per_second(self) -> float:
        """Inference speed in tokens/second."""
        if self.eval_duration_ns > 0:
            return (self.eval_count / self.eval_duration_ns) * 1_000_000_000
        return 0.0


# ============================================================================
# Ollama Service
# ============================================================================


class OllamaService:
    """
    Ollama AI service adapter using HTTP REST API.

    AGPL-Safe Implementation (same pattern as OPAService):
    - Uses Python requests library (Apache 2.0 license)
    - Network-only access via HTTP REST API
    - No code dependencies on Ollama libraries

    Ollama REST API Endpoints:
    - POST /api/generate - Generate text completion
    - POST /api/chat - Chat completion (multi-turn)
    - GET /api/tags - List available models
    - POST /api/pull - Pull model from registry
    - GET /api/show - Show model info
    - DELETE /api/delete - Delete model

    Usage:
        ollama = OllamaService()

        # Generate violation recommendation
        recommendation = await ollama.generate_recommendation(
            violation_type="missing_documentation",
            severity="high",
            location="docs/00-Project-Foundation",
            description="Missing required SDLC 4.9.1 stage folder"
        )

        print(recommendation.response)
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: str = OllamaModel.DEFAULT.value,
        timeout: int = 30,
    ):
        """
        Initialize Ollama service with REST API endpoint.

        Args:
            base_url: Ollama server URL (default: from settings or localhost:11434)
            model: Default model to use (default: llama2:13b)
            timeout: Request timeout in seconds (default: 30s)
        """
        # Get Ollama URL from settings or use default
        self.base_url = base_url or getattr(
            settings, "OLLAMA_URL", "http://localhost:11434"
        )
        self.model = model
        self.timeout = timeout
        self._is_available: Optional[bool] = None

        logger.info(f"Ollama service initialized: {self.base_url} (model: {self.model})")

    # ============================================================================
    # Health Check
    # ============================================================================

    def health_check(self) -> dict[str, Any]:
        """
        Check Ollama service health and list available models.

        Returns:
            Health status:
            {
                "healthy": bool,
                "models": list[str],
                "version": str
            }

        Example:
            health = ollama.health_check()
            if health["healthy"]:
                print(f"✅ Ollama is healthy with models: {health['models']}")
        """
        try:
            # Try to list models (this also checks connectivity)
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=5,
            )

            if response.status_code == 200:
                data = response.json()
                models = [m.get("name", "") for m in data.get("models", [])]

                self._is_available = True

                return {
                    "healthy": True,
                    "models": models,
                    "version": "ollama",
                }
            else:
                self._is_available = False
                return {
                    "healthy": False,
                    "models": [],
                    "version": "unknown",
                    "error": f"HTTP {response.status_code}",
                }

        except ConnectionError:
            self._is_available = False
            logger.warning(f"Ollama not available at {self.base_url}")
            return {
                "healthy": False,
                "models": [],
                "version": "unknown",
                "error": "Connection refused - Ollama not running",
            }

        except Exception as e:
            self._is_available = False
            logger.error(f"Ollama health check failed: {e}")
            return {
                "healthy": False,
                "models": [],
                "version": "unknown",
                "error": str(e),
            }

    @property
    def is_available(self) -> bool:
        """Check if Ollama is available (cached result)."""
        if self._is_available is None:
            self.health_check()
        return self._is_available or False

    # ============================================================================
    # Text Generation
    # ============================================================================

    def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stream: bool = False,
    ) -> OllamaResponse:
        """
        Generate text completion using Ollama.

        Args:
            prompt: User prompt/input
            model: Model to use (default: self.model)
            system: System prompt for context
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            stream: Enable streaming (not supported in this sync version)

        Returns:
            OllamaResponse with generated text

        Raises:
            OllamaError: If generation fails

        Example:
            response = ollama.generate(
                prompt="Explain why documentation is important in SDLC",
                system="You are an expert in software development lifecycle.",
                temperature=0.3
            )
            print(response.response)
        """
        url = f"{self.base_url}/api/generate"
        model = model or self.model

        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,  # Always false for sync version
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        if system:
            payload["system"] = system

        try:
            start_time = time.time()

            logger.debug(f"Ollama generate: model={model}, prompt_len={len(prompt)}")

            response = requests.post(
                url,
                json=payload,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"},
            )

            response.raise_for_status()

            data = response.json()

            elapsed_ms = (time.time() - start_time) * 1000
            logger.info(f"Ollama response: {elapsed_ms:.0f}ms, tokens={data.get('eval_count', 0)}")

            return OllamaResponse(
                model=data.get("model", model),
                response=data.get("response", ""),
                done=data.get("done", True),
                total_duration_ns=data.get("total_duration", 0),
                load_duration_ns=data.get("load_duration", 0),
                prompt_eval_count=data.get("prompt_eval_count", 0),
                eval_count=data.get("eval_count", 0),
                eval_duration_ns=data.get("eval_duration", 0),
            )

        except Timeout:
            logger.error(f"Ollama request timeout after {self.timeout}s")
            raise OllamaError(f"Request timed out after {self.timeout}s")

        except ConnectionError:
            logger.error(f"Ollama not available at {self.base_url}")
            self._is_available = False
            raise OllamaError(f"Ollama not available at {self.base_url}")

        except RequestException as e:
            logger.error(f"Ollama request failed: {e}")
            raise OllamaError(f"Request failed: {str(e)}")

    # ============================================================================
    # Chat Completion with Tool Calling (Sprint 189 — ADR-064 T-02)
    # ============================================================================

    def chat(
        self,
        messages: list[dict[str, str]],
        model: Optional[str] = None,
        tools: Optional[list[dict[str, Any]]] = None,
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ) -> dict[str, Any]:
        """
        Chat completion using Ollama /api/chat with native tool calling.

        Sprint 189 P0-1: This method calls /api/chat (NOT /api/generate) to
        support the `tools` parameter for LLM Function Calling. The existing
        generate() method only calls /api/generate which does NOT support tools.

        This method is SYNC — callers in async context MUST wrap with
        starlette.concurrency.run_in_threadpool (ADR-064 T-08).

        Args:
            messages: Chat messages [{"role": "system"|"user"|"assistant", "content": "..."}]
            model: Model to use (default: self.model, recommended: qwen3:32b for Vietnamese)
            tools: Ollama tool definitions for function calling. Each tool:
                   {"type": "function", "function": {"name": str, "description": str, "parameters": dict}}
            temperature: Sampling temperature (default: 0.3 for deterministic tool calls)
            max_tokens: Maximum tokens to generate

        Returns:
            Raw Ollama /api/chat response dict containing:
            - message.content: Text response (may be empty if tool_calls present)
            - message.tool_calls: List of tool calls [{"function": {"name": str, "arguments": dict}}]
            - model, created_at, done, total_duration, eval_count, etc.

        Raises:
            OllamaError: If chat request fails

        Example:
            tools = [{"type": "function", "function": {
                "name": "create_project",
                "description": "Create a new project",
                "parameters": {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]}
            }}]
            response = ollama.chat(
                messages=[{"role": "user", "content": "Tạo dự án Bflow"}],
                tools=tools,
            )
            if response.get("message", {}).get("tool_calls"):
                tool_call = response["message"]["tool_calls"][0]
                fn_name = tool_call["function"]["name"]
                fn_args = tool_call["function"]["arguments"]
        """
        url = f"{self.base_url}/api/chat"
        model = model or self.model

        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        if tools:
            payload["tools"] = tools

        try:
            start_time = time.time()

            logger.debug(
                "Ollama chat: model=%s messages=%d tools=%d",
                model,
                len(messages),
                len(tools) if tools else 0,
            )

            response = requests.post(
                url,
                json=payload,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"},
            )

            response.raise_for_status()

            data = response.json()

            elapsed_ms = (time.time() - start_time) * 1000
            tool_calls = data.get("message", {}).get("tool_calls", [])
            logger.info(
                "Ollama chat response: %.0fms, tool_calls=%d, model=%s",
                elapsed_ms,
                len(tool_calls),
                model,
            )

            return data

        except Timeout:
            logger.error("Ollama chat timeout after %ds", self.timeout)
            raise OllamaError(f"Chat request timed out after {self.timeout}s")

        except ConnectionError:
            logger.error("Ollama not available at %s", self.base_url)
            self._is_available = False
            raise OllamaError(f"Ollama not available at {self.base_url}")

        except HTTPError as e:
            status_code = e.response.status_code if e.response is not None else 0
            logger.error(
                "Ollama chat HTTP error: status=%d model=%s url=%s",
                status_code,
                model,
                url,
            )
            raise OllamaError(
                f"Chat request failed: HTTP {status_code}",
            ) from e

        except RequestException as e:
            logger.error("Ollama chat request failed: %s", e)
            raise OllamaError(f"Chat request failed: {str(e)}")

    # ============================================================================
    # Violation Recommendation Generation
    # ============================================================================

    def generate_recommendation(
        self,
        violation_type: str,
        severity: str,
        location: str,
        description: str,
        context: Optional[dict[str, Any]] = None,
        model: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Generate AI recommendation for a compliance violation.

        This is the primary method for Sprint 21 Compliance Scanner integration.

        Args:
            violation_type: Type of violation (e.g., "missing_documentation")
            severity: Severity level ("critical", "high", "medium", "low", "info")
            location: File/folder path or code location
            description: Human-readable description of the violation
            context: Additional context (project info, stage, etc.)
            model: Model to use (default: codellama for code, llama2 for docs)

        Returns:
            Recommendation result:
            {
                "recommendation": str,  # AI-generated fix recommendation
                "confidence": int,  # Confidence score (0-100)
                "model": str,  # Model used
                "duration_ms": float,  # Inference time
                "tokens": int  # Tokens generated
            }

        Example:
            result = ollama.generate_recommendation(
                violation_type="missing_documentation",
                severity="high",
                location="docs/00-Project-Foundation",
                description="Missing required SDLC 4.9.1 stage folder",
                context={"project_name": "My Project", "stage": "WHY"}
            )
            print(f"Recommendation: {result['recommendation']}")
            print(f"Confidence: {result['confidence']}%")
        """
        # Choose appropriate model based on violation type
        if model is None:
            if violation_type in ("doc_code_drift", "api_not_documented", "db_schema_drift"):
                model = OllamaModel.CODELLAMA_13B.value
            else:
                model = OllamaModel.LLAMA2_13B.value

        # Build system prompt with SDLC 4.9.1 context
        system_prompt = self._build_recommendation_system_prompt()

        # Build user prompt with violation details
        user_prompt = self._build_recommendation_user_prompt(
            violation_type=violation_type,
            severity=severity,
            location=location,
            description=description,
            context=context,
        )

        try:
            # Generate recommendation
            response = self.generate(
                prompt=user_prompt,
                model=model,
                system=system_prompt,
                temperature=0.3,  # Lower temperature for more focused recommendations
                max_tokens=1024,
            )

            # Calculate confidence based on response length and coherence
            confidence = self._calculate_confidence(response)

            return {
                "recommendation": response.response.strip(),
                "confidence": confidence,
                "model": response.model,
                "duration_ms": response.total_duration_ms,
                "tokens": response.eval_count,
            }

        except OllamaError as e:
            logger.error(f"Failed to generate recommendation: {e}")
            # Return fallback recommendation
            return self._get_fallback_recommendation(
                violation_type=violation_type,
                severity=severity,
                location=location,
                description=description,
            )

    def _build_recommendation_system_prompt(self) -> str:
        """Build system prompt for SDLC 5.1.3 compliance recommendations."""
        return """You are an expert SDLC 5.1.3 compliance advisor. Your role is to provide actionable recommendations for fixing compliance violations.

SDLC 5.1.3 Framework Overview (10 Stages + Archive):
- Stage 00 FOUNDATION (WHY?): Strategic Discovery & Validation
- Stage 01 PLANNING (WHAT?): Requirements & User Stories
- Stage 02 DESIGN (HOW?): Architecture & Technical Design
- Stage 03 INTEGRATE: API Contracts & Third-party Setup
- Stage 04 BUILD: Development & Implementation
- Stage 05 TEST: Quality Assurance & Validation
- Stage 06 DEPLOY: Release & Deployment
- Stage 07 OPERATE: Production Operations & Monitoring
- Stage 08 COLLABORATE: Team Coordination & Knowledge
- Stage 09 GOVERN: Compliance & Strategic Oversight
- Stage 10 ARCHIVE: Project Archive (Legacy Docs)

Guidelines for recommendations:
1. Be specific and actionable
2. Provide concrete steps to fix the violation
3. Reference SDLC 5.1.3 best practices
4. Suggest documentation templates if needed
5. Keep recommendations concise (3-5 bullet points)
6. Prioritize quick wins over major refactoring"""

    def _build_recommendation_user_prompt(
        self,
        violation_type: str,
        severity: str,
        location: str,
        description: str,
        context: Optional[dict[str, Any]] = None,
    ) -> str:
        """Build user prompt with violation details."""
        context = context or {}

        prompt = f"""Please provide a recommendation to fix this SDLC 5.1.3 compliance violation:

**Violation Type**: {violation_type.replace("_", " ").title()}
**Severity**: {severity.upper()}
**Location**: {location}
**Description**: {description}
"""

        if context:
            if "project_name" in context:
                prompt += f"\n**Project**: {context['project_name']}"
            if "stage" in context:
                prompt += f"\n**Current Stage**: {context['stage']}"
            if "existing_files" in context:
                prompt += f"\n**Existing Files**: {', '.join(context['existing_files'][:5])}"

        prompt += """

Provide a concise recommendation with:
1. Root cause analysis (1 sentence)
2. Specific fix steps (3-5 bullet points)
3. Prevention tips (1-2 bullet points)

Format your response as actionable steps, not a general explanation."""

        return prompt

    def _calculate_confidence(self, response: OllamaResponse) -> int:
        """
        Calculate confidence score based on response quality.

        Factors:
        - Response length (too short = low confidence)
        - Presence of actionable language (should, must, create, add, fix)
        - Bullet points/structure
        """
        text = response.response.lower()

        # Base confidence
        confidence = 50

        # Length factor (50-500 chars is ideal)
        text_len = len(response.response)
        if text_len < 50:
            confidence -= 20
        elif text_len < 100:
            confidence -= 10
        elif 100 <= text_len <= 500:
            confidence += 10
        elif text_len > 1000:
            confidence -= 5  # Too verbose

        # Actionable language
        action_words = ["create", "add", "fix", "update", "remove", "implement", "should", "must", "need"]
        action_count = sum(1 for word in action_words if word in text)
        confidence += min(action_count * 5, 20)

        # Structure (bullet points, numbered lists)
        if any(marker in text for marker in ["1.", "2.", "- ", "* ", "•"]):
            confidence += 10

        # Clamp to 0-100
        return max(0, min(100, confidence))

    def _get_fallback_recommendation(
        self,
        violation_type: str,
        severity: str,
        location: str,
        description: str,
    ) -> dict[str, Any]:
        """
        Get rule-based fallback recommendation when AI is unavailable.

        This ensures the system works even without Ollama running.
        """
        fallback_recommendations = {
            "missing_documentation": f"""**Recommendation for Missing Documentation**

1. **Root Cause**: Required SDLC 5.1.3 documentation folder/file is missing at `{location}`.

2. **Fix Steps**:
   - Create the missing folder structure at `{location}`
   - Add required documentation files (README.md, relevant stage docs)
   - Follow SDLC 5.1.3 templates in docs/templates/
   - Link to parent stage documentation
   - Submit for review via PR

3. **Prevention**:
   - Use `sdlcctl init` to scaffold required folders
   - Enable pre-commit hooks for doc validation""",

            "skipped_stage": f"""**Recommendation for Skipped Stage**

1. **Root Cause**: A required SDLC stage was bypassed without proper gate approval.

2. **Fix Steps**:
   - Review stage requirements at the skipped stage
   - Complete minimum viable documentation
   - Create gate evidence (artifacts, approvals)
   - Request gate approval from stakeholders
   - Update stage progression tracking

3. **Prevention**:
   - Enable gate enforcement in project settings
   - Configure webhook notifications for stage transitions""",

            "doc_code_drift": f"""**Recommendation for Doc-Code Drift**

1. **Root Cause**: Documentation at `{location}` is out of sync with current code implementation.

2. **Fix Steps**:
   - Compare documentation with current codebase
   - Update API contracts in OpenAPI spec
   - Regenerate API documentation
   - Update code examples in docs
   - Add automated doc-code sync check to CI

3. **Prevention**:
   - Use doc generation from code comments
   - Add doc validation to PR checks""",

            "policy_violation": f"""**Recommendation for Policy Violation**

1. **Root Cause**: Code or configuration violates defined SDLC policy rules.

2. **Fix Steps**:
   - Review violated policy requirements
   - Update code/configuration to comply
   - Add unit tests for policy compliance
   - Request policy exception if needed (with justification)
   - Document any approved exceptions

3. **Prevention**:
   - Run policy checks locally before commit
   - Enable OPA policy evaluation in CI pipeline""",

            "test_coverage_low": f"""**Recommendation for Low Test Coverage**

1. **Root Cause**: Test coverage at `{location}` is below required threshold.

2. **Fix Steps**:
   - Identify uncovered code paths
   - Write unit tests for critical functions
   - Add integration tests for API endpoints
   - Run coverage report: pytest --cov
   - Target 95%+ coverage for business logic

3. **Prevention**:
   - Set coverage thresholds in CI configuration
   - Review coverage in PR checks""",
        }

        # Default fallback for unknown violation types
        default_recommendation = f"""**Recommendation for {violation_type.replace("_", " ").title()}**

1. **Root Cause**: Compliance check detected an issue at `{location}`.

2. **Fix Steps**:
   - Review the violation description: {description}
   - Consult SDLC 5.1.3 documentation for requirements
   - Address the specific issue identified
   - Validate fix with local compliance scan
   - Submit changes for review

3. **Prevention**:
   - Enable continuous compliance monitoring
   - Add pre-commit hooks for validation"""

        recommendation_text = fallback_recommendations.get(violation_type, default_recommendation)

        return {
            "recommendation": recommendation_text,
            "confidence": 60,  # Fallback recommendations have moderate confidence
            "model": "rule-based-fallback",
            "duration_ms": 0.0,
            "tokens": 0,
        }

    # ============================================================================
    # Sprint 77: Custom Prompt Generation
    # ============================================================================

    def generate_from_prompt(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 1500,
    ) -> dict[str, Any]:
        """
        Generate AI response from a custom prompt.

        Sprint 77 Day 1: AI Council Sprint Context Integration

        Args:
            prompt: Custom prompt to send to AI
            model: Model to use (default: self.model)
            temperature: Sampling temperature (default: 0.3 for focused output)
            max_tokens: Maximum tokens to generate

        Returns:
            Response result:
            {
                "recommendation": str,  # AI-generated response
                "confidence": int,  # Confidence score (0-100)
                "model": str,  # Model used
                "duration_ms": float,  # Inference time
                "tokens": int  # Tokens generated
            }

        Example:
            result = ollama.generate_from_prompt(
                prompt="Review this code for security issues...",
            )
            print(f"Response: {result['recommendation']}")
        """
        try:
            response = self.generate(
                prompt=prompt,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            # Calculate confidence
            confidence = self._calculate_confidence(response)

            return {
                "recommendation": response.response.strip(),
                "confidence": confidence,
                "model": response.model,
                "duration_ms": response.total_duration_ms,
                "tokens": response.eval_count,
            }

        except OllamaError as e:
            logger.error(f"Failed to generate from prompt: {e}")
            return {
                "recommendation": "Unable to generate AI response. Please review manually.",
                "confidence": 20,
                "model": "fallback",
                "duration_ms": 0.0,
                "tokens": 0,
            }

    # ============================================================================
    # Batch Recommendation Generation
    # ============================================================================

    def generate_recommendations_batch(
        self,
        violations: list[dict[str, Any]],
        context: Optional[dict[str, Any]] = None,
    ) -> list[dict[str, Any]]:
        """
        Generate recommendations for multiple violations.

        Args:
            violations: List of violation dicts with keys:
                - violation_type, severity, location, description
            context: Shared context for all violations

        Returns:
            List of recommendation results

        Example:
            violations = [
                {"violation_type": "missing_documentation", "severity": "high", ...},
                {"violation_type": "doc_code_drift", "severity": "medium", ...},
            ]
            results = ollama.generate_recommendations_batch(violations)
        """
        results = []

        for violation in violations:
            result = self.generate_recommendation(
                violation_type=violation.get("violation_type", "unknown"),
                severity=violation.get("severity", "medium"),
                location=violation.get("location", "unknown"),
                description=violation.get("description", "No description"),
                context=context,
            )
            results.append(result)

        return results

    # ============================================================================
    # Model Management
    # ============================================================================

    def list_models(self) -> list[dict[str, Any]]:
        """
        List available models in Ollama.

        Returns:
            List of model info dicts:
            [
                {"name": "llama2:13b", "size": "7.4GB", "modified": "2024-01-15"},
                ...
            ]
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=10,
            )
            response.raise_for_status()

            data = response.json()
            models = data.get("models", [])

            return [
                {
                    "name": m.get("name", ""),
                    "size": self._format_size(m.get("size", 0)),
                    "modified": m.get("modified_at", ""),
                    "digest": m.get("digest", "")[:12],
                }
                for m in models
            ]

        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            return []

    def pull_model(self, model: str) -> dict[str, Any]:
        """
        Pull a model from Ollama registry.

        Args:
            model: Model name to pull (e.g., "llama2:13b")

        Returns:
            Pull result:
            {
                "success": bool,
                "model": str,
                "message": str
            }
        """
        try:
            logger.info(f"Pulling model: {model}")

            response = requests.post(
                f"{self.base_url}/api/pull",
                json={"name": model, "stream": False},
                timeout=600,  # 10 minutes for large models
            )
            response.raise_for_status()

            return {
                "success": True,
                "model": model,
                "message": f"Model {model} pulled successfully",
            }

        except Exception as e:
            logger.error(f"Failed to pull model {model}: {e}")
            return {
                "success": False,
                "model": model,
                "message": f"Failed to pull model: {str(e)}",
            }

    def _format_size(self, size_bytes: int) -> str:
        """Format bytes to human-readable size."""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size_bytes < 1024:
                return f"{size_bytes:.1f}{unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f}PB"


# ============================================================================
# Custom Exceptions
# ============================================================================


class OllamaError(Exception):
    """Exception raised when Ollama operations fail."""

    pass


# ============================================================================
# Factory Functions
# ============================================================================


def create_ollama_service(
    base_url: Optional[str] = None,
    model: str = OllamaModel.DEFAULT.value,
) -> OllamaService:
    """
    Factory function to create OllamaService instance.

    Args:
        base_url: Ollama server URL (default: from settings)
        model: Default model to use

    Returns:
        OllamaService instance

    Example:
        ollama = create_ollama_service()
        if ollama.is_available:
            result = ollama.generate_recommendation(...)
    """
    return OllamaService(base_url=base_url, model=model)


# ============================================================================
# Global Instance (Lazy Initialization)
# ============================================================================

_ollama_service: Optional[OllamaService] = None


def get_ollama_service() -> OllamaService:
    """
    Get global OllamaService instance (singleton pattern).

    Returns:
        OllamaService instance

    Example:
        ollama = get_ollama_service()
        health = ollama.health_check()
    """
    global _ollama_service
    if _ollama_service is None:
        _ollama_service = create_ollama_service()
    return _ollama_service
