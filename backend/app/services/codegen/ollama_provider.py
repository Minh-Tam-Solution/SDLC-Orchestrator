"""
Ollama Codegen Provider Implementation.

Sprint 45: Multi-Provider Codegen Architecture (EP-06)
ADR-022: Provider-Agnostic Codegen Architecture

This module implements the primary codegen provider using Ollama.
Optimized for Vietnam SME market with Vietnamese-language prompts.

Design Decisions:
- Ollama-first for cost efficiency (~$50/month vs $1000/month cloud)
- Vietnamese-optimized prompts for SME market wedge (40%)
- qwen3-coder:30b as primary model (1.8x faster, 256K context)
- Retry with exponential backoff for resilience
- Structured output parsing (### FILE: format)

Model Updates (Dec 24, 2025):
- qwen2.5-coder:32b → qwen3-coder:30b (1.8x faster, 256K context, 18GB)
- qwen2.5:14b-instruct → qwen3:8b (fast draft)
- qwen2.5:32b → mistral-small3.2:24b (enterprise assistant)

Author: Backend Lead
Date: December 23, 2025
Status: ACTIVE
"""

import json
import inspect
import re
import time
import logging
from typing import Dict, Any, Optional, AsyncGenerator
from dataclasses import dataclass

import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

from .file_parser import FileBoundaryParser, ParserState, ParsedFile

from app.core.config import settings
from .base_provider import (
    CodegenProvider,
    CodegenSpec,
    CodegenResult,
    ValidationResult,
    CostEstimate
)
from .templates.base_templates import TemplateContext, GenerationType
from .templates.fastapi_templates import FastAPITemplates

logger = logging.getLogger(__name__)

# Template registry for different frameworks
FRAMEWORK_TEMPLATES = {
    "fastapi": FastAPITemplates(),
}


class OllamaCodegenProvider(CodegenProvider):
    """
    Ollama-based code generation provider.

    Primary provider for Vietnam SME codegen (EP-06 Mode B).
    Uses company GPU server for cost efficiency.

    Features:
    - Vietnamese-optimized prompts
    - qwen3-coder:30b for production code (1.8x faster, 256K context)
    - qwen3:8b for fast autocomplete (<3s)
    - Retry with exponential backoff
    - Structured file output parsing

    Configuration (via environment variables):
    - CODEGEN_OLLAMA_URL: Ollama server URL
    - CODEGEN_MODEL_PRIMARY: Primary model for code generation
    - CODEGEN_TIMEOUT: Request timeout in seconds

    Example:
        >>> provider = OllamaCodegenProvider()
        >>> result = await provider.generate(spec)
        >>> print(result.files)  # {"app/main.py": "..."}
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[int] = None
    ):
        """
        Initialize Ollama provider.

        Args:
            base_url: Ollama API URL (default: settings.CODEGEN_OLLAMA_URL)
            model: Model to use (default: settings.CODEGEN_MODEL_PRIMARY)
            timeout: Request timeout in seconds (default: settings.CODEGEN_TIMEOUT)
        """
        self.base_url = base_url or settings.CODEGEN_OLLAMA_URL
        self.model = model or settings.CODEGEN_MODEL_PRIMARY
        self.timeout = timeout or settings.CODEGEN_TIMEOUT
        self._available: Optional[bool] = None
        self._last_health_check: float = 0
        self._health_check_ttl: float = 60.0  # Cache health check for 60s

    @property
    def name(self) -> str:
        """Provider identifier."""
        return "ollama"

    @property
    def is_available(self) -> bool:
        """
        Check if Ollama is configured and reachable.

        Uses cached result if within TTL to avoid excessive API calls.
        """
        now = time.time()
        if (
            self._available is not None and
            now - self._last_health_check < self._health_check_ttl
        ):
            return self._available

        self._available = self._check_availability()
        self._last_health_check = now
        return self._available

    def _check_availability(self) -> bool:
        """
        Check if Ollama is reachable.

        Returns:
            True if Ollama API responds successfully
        """
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(f"{self.base_url}/api/tags")
                if response.status_code == 200:
                    # Check if model is available
                    data = response.json()
                    models = [m.get("name", "") for m in data.get("models", [])]
                    # Check for model (with or without tag suffix)
                    model_base = self.model.split(":")[0]
                    available = any(model_base in m for m in models)
                    if not available:
                        logger.warning(
                            f"Ollama available but model {self.model} not found. "
                            f"Available: {models[:5]}..."
                        )
                    return True  # Still available even if model missing
                return False
        except httpx.ConnectError as e:
            logger.debug(f"Ollama connection failed: {e}")
            return False
        except httpx.TimeoutException:
            logger.debug("Ollama health check timed out")
            return False
        except Exception as e:
            logger.warning(f"Ollama availability check failed: {e}")
            return False

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type((httpx.ConnectError, httpx.TimeoutException))
    )
    async def generate(self, spec: CodegenSpec) -> CodegenResult:
        """
        Generate code using Ollama.

        Args:
            spec: CodegenSpec with app_blueprint

        Returns:
            CodegenResult with generated code and files

        Raises:
            httpx.HTTPStatusError: If Ollama returns error status
            httpx.TimeoutException: If request times out
        """
        start_time = time.time()

        prompt = self._build_generation_prompt(spec)

        logger.info(
            f"Generating code with Ollama: model={self.model}, "
            f"language={spec.language}, framework={spec.framework}"
        )

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "temperature": 0.3,  # Lower for deterministic code
                    "stream": False,
                    "options": {
                        "num_ctx": 8192,  # Context window
                        "num_predict": 4096,  # Max tokens to generate
                    }
                }
            )
            response.raise_for_status()
            result = response.json()
            if inspect.isawaitable(result):
                result = await result

        generation_time_ms = int((time.time() - start_time) * 1000)

        # Parse output into files
        raw_output = result.get("response", "")
        files = self._parse_code_output(raw_output)

        # Extract token counts
        prompt_tokens = result.get("prompt_eval_count", 0)
        completion_tokens = result.get("eval_count", 0)

        logger.info(
            f"Ollama generation complete: {len(files)} files, "
            f"{completion_tokens} tokens, {generation_time_ms}ms"
        )

        return CodegenResult(
            code=raw_output,
            files=files,
            metadata={
                "model": self.model,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
                "temperature": 0.3
            },
            provider=self.name,
            tokens_used=prompt_tokens + completion_tokens,
            generation_time_ms=generation_time_ms
        )

    async def validate(
        self,
        code: str,
        context: Dict[str, Any]
    ) -> ValidationResult:
        """
        Validate generated code using Ollama.

        Args:
            code: Generated code to validate
            context: Additional context (language, framework, etc.)

        Returns:
            ValidationResult with validation status
        """
        prompt = self._build_validation_prompt(code, context)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "temperature": 0.1,  # Very low for consistent validation
                    "stream": False,
                    "options": {
                        "num_ctx": 4096,
                        "num_predict": 1024,
                    }
                }
            )
            response.raise_for_status()
            result = response.json()
            if inspect.isawaitable(result):
                result = await result

        return self._parse_validation_result(result.get("response", ""))

    def estimate_cost(self, spec: CodegenSpec) -> CostEstimate:
        """
        Estimate cost for generation.

        Ollama is self-hosted, so cost is essentially just electricity.
        We estimate ~$0.001 per 1K tokens for fair comparison.

        Args:
            spec: CodegenSpec to estimate

        Returns:
            CostEstimate with token and cost projections
        """
        # Estimate tokens based on IR size
        ir_json = json.dumps(spec.app_blueprint)
        ir_tokens = len(ir_json) // 4  # Rough estimate: 4 chars per token

        # Output typically 2-3x input for code generation
        estimated_output_tokens = ir_tokens * 3
        estimated_total = ir_tokens + estimated_output_tokens

        # Ollama cost: ~$0.001 per 1K tokens (electricity only)
        cost_per_1k = 0.001
        estimated_cost = cost_per_1k * (estimated_total / 1000)

        return CostEstimate(
            estimated_tokens=estimated_total,
            estimated_cost_usd=round(estimated_cost, 6),
            provider=self.name,
            confidence=0.85
        )

    def _build_generation_prompt(self, spec: CodegenSpec) -> str:
        """
        Build Vietnamese-optimized prompt for code generation.

        Uses template system for framework-specific prompts.
        Falls back to generic prompt if framework not supported.

        Args:
            spec: CodegenSpec with app_blueprint

        Returns:
            Formatted prompt string
        """
        # Try to use framework-specific template
        template = FRAMEWORK_TEMPLATES.get(spec.framework.lower())

        if template:
            # Build context for template
            blueprint_json = json.dumps(
                spec.app_blueprint, indent=2, ensure_ascii=False
            )
            context = TemplateContext(
                app_name=spec.app_blueprint.get("name", "App"),
                app_description=spec.app_blueprint.get("description"),
                blueprint_json=blueprint_json,
                generation_type=(
                    GenerationType.MODULE if spec.target_module
                    else GenerationType.FULL_APP
                ),
                target_module=spec.target_module,
                language=spec.language,
                framework=spec.framework,
                database=spec.app_blueprint.get("database", "postgresql"),
                vietnamese_comments=True
            )
            return template.get_generation_prompt(context)

        # Fallback to generic prompt
        return self._build_generic_prompt(spec)

    def _build_generic_prompt(self, spec: CodegenSpec) -> str:
        """
        Build generic prompt for unsupported frameworks.

        Args:
            spec: CodegenSpec with app_blueprint

        Returns:
            Formatted prompt string
        """
        blueprint_json = json.dumps(spec.app_blueprint, indent=2, ensure_ascii=False)

        target_instruction = (
            f"Chỉ tạo module: {spec.target_module}"
            if spec.target_module
            else "Tạo tất cả modules"
        )

        return f"""Bạn là một AI chuyên gia phát triển phần mềm cho doanh nghiệp SME Việt Nam.

## Nhiệm vụ
Dựa trên đặc tả IR (Intermediate Representation) sau, hãy tạo code {spec.framework} hoàn chỉnh, production-ready.

## App Blueprint (IR)
```json
{blueprint_json}
```

## Yêu cầu kỹ thuật
- **Ngôn ngữ**: {spec.language}
- **Framework**: {spec.framework}
- **Scope**: {target_instruction}

## Quy tắc coding
1. Production-ready code, không có TODO hoặc placeholder
2. Type hints đầy đủ
3. Error handling đúng chuẩn
4. Comments tiếng Việt cho business logic phức tạp
5. Tuân thủ coding conventions của {spec.framework}

## Output Format
Mỗi file bắt đầu bằng `### FILE: path/to/file.ext`
Code trong block ```{spec.language}```

### FILE: example/file.{self._get_extension(spec.language)}
```{spec.language}
# code here
```

Bắt đầu tạo code:
"""

    def _get_extension(self, language: str) -> str:
        """Get file extension for language."""
        extensions = {
            "python": "py",
            "typescript": "ts",
            "javascript": "js",
            "go": "go",
            "rust": "rs",
            "java": "java"
        }
        return extensions.get(language.lower(), "txt")

    def _build_validation_prompt(
        self,
        code: str,
        context: Dict[str, Any]
    ) -> str:
        """
        Build validation prompt.

        Uses template system if framework is specified in context.

        Args:
            code: Code to validate
            context: Additional context

        Returns:
            Formatted validation prompt
        """
        # Try framework-specific template
        framework = context.get("framework", "").lower()
        template = FRAMEWORK_TEMPLATES.get(framework)

        if template:
            return template.get_validation_prompt(code, context)

        # Fallback to generic validation prompt
        context_str = json.dumps(context, ensure_ascii=False, indent=2) if context else "{}"

        return f"""Bạn là senior code reviewer với kinh nghiệm về phát triển phần mềm.

## Code cần review
```
{code[:6000]}
```

## Context
{context_str}

## Yêu cầu đánh giá
Kiểm tra code về các tiêu chí:
1. **Errors** (Lỗi nghiêm trọng): Bugs, security vulnerabilities, logic errors
2. **Warnings** (Cảnh báo): Code smell, performance issues, best practice violations
3. **Suggestions** (Gợi ý): Improvements, refactoring opportunities, optimizations

## Output Format (JSON only)
```json
{{
  "valid": true/false,
  "errors": ["Mô tả lỗi bằng tiếng Việt"],
  "warnings": ["Cảnh báo bằng tiếng Việt"],
  "suggestions": ["Gợi ý cải thiện bằng tiếng Việt"]
}}
```

Chỉ trả về JSON, không có text khác.
"""

    def _parse_code_output(self, output: str) -> Dict[str, str]:
        """
        Parse Ollama output into file dictionary.

        Parses the ### FILE: format into a dict mapping
        file paths to their contents.

        Args:
            output: Raw Ollama output

        Returns:
            Dict mapping file paths to contents
        """
        files: Dict[str, str] = {}
        current_file: Optional[str] = None
        current_content: list = []
        in_code_block = False

        for line in output.split('\n'):
            # Check for file marker
            if line.startswith('### FILE:'):
                # Save previous file
                if current_file and current_content:
                    content = '\n'.join(current_content)
                    # Clean up code block markers
                    content = self._clean_code_content(content)
                    files[current_file] = content

                # Start new file
                current_file = line.replace('### FILE:', '').strip()
                current_content = []
                in_code_block = False
            elif current_file:
                # Track code block state
                if line.startswith('```'):
                    in_code_block = not in_code_block
                    if not in_code_block:
                        continue  # Skip closing ```
                    if in_code_block and len(line) > 3:
                        continue  # Skip opening ```python
                    continue
                current_content.append(line)

        # Save last file
        if current_file and current_content:
            content = '\n'.join(current_content)
            content = self._clean_code_content(content)
            files[current_file] = content

        return files

    def _clean_code_content(self, content: str) -> str:
        """
        Clean up code content.

        Removes stray code block markers and trims whitespace.

        Args:
            content: Raw code content

        Returns:
            Cleaned code content
        """
        # Remove any remaining code block markers
        content = re.sub(r'^```\w*\n?', '', content)
        content = re.sub(r'\n?```$', '', content)
        return content.strip()

    def _parse_validation_result(self, output: str) -> ValidationResult:
        """
        Parse validation output into ValidationResult.

        Attempts to extract JSON from the output. Falls back to
        default valid result if parsing fails.

        Args:
            output: Raw validation output

        Returns:
            ValidationResult parsed from output
        """
        try:
            # Try to extract JSON from output
            json_match = re.search(r'\{[^{}]*\}', output, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                return ValidationResult(
                    valid=data.get("valid", True),
                    errors=data.get("errors", []),
                    warnings=data.get("warnings", []),
                    suggestions=data.get("suggestions", [])
                )
        except json.JSONDecodeError:
            pass
        except Exception as e:
            logger.warning(f"Failed to parse validation output: {e}")

        # Default to valid with warning about parse failure
        return ValidationResult(
            valid=True,
            errors=[],
            warnings=["Could not parse validation output from LLM"],
            suggestions=[]
        )

    # =========================================================================
    # Sprint 51B: Streaming Code Generation
    # =========================================================================

    async def generate_streaming(
        self,
        spec: CodegenSpec
    ) -> AsyncGenerator[ParsedFile, None]:
        """
        Generate code using Ollama with real-time streaming.

        Sprint 51B: Stream tokens from Ollama and emit files as they complete.

        This method:
        1. Sends prompt to Ollama with stream=True
        2. Accumulates tokens in buffer
        3. Uses FileBoundaryParser to detect file boundaries
        4. Yields ParsedFile objects as soon as complete

        Args:
            spec: CodegenSpec with app_blueprint

        Yields:
            ParsedFile objects as they are completed

        Example:
            async for file in provider.generate_streaming(spec):
                print(f"Generated: {file.path} ({file.lines} lines)")
                # Process file immediately
        """
        prompt = self._build_generation_prompt(spec)
        parser = FileBoundaryParser()
        state = ParserState()

        logger.info(
            f"Starting streaming generation: model={self.model}, "
            f"language={spec.language}, framework={spec.framework}"
        )

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "temperature": 0.3,
                        "stream": True,
                        "options": {
                            "num_ctx": 8192,
                            "num_predict": 4096,
                        }
                    }
                ) as response:
                    response.raise_for_status()

                    async for line in response.aiter_lines():
                        if not line:
                            continue

                        try:
                            chunk = json.loads(line)
                            token = chunk.get("response", "")

                            if token:
                                # Feed token to parser
                                completed_files = parser.parse_chunk(token, state)

                                # Yield any completed files immediately
                                for file in completed_files:
                                    logger.debug(
                                        f"Streaming file complete: {file.path} "
                                        f"({file.lines} lines)"
                                    )
                                    yield file

                            # Check if generation is done
                            if chunk.get("done", False):
                                break

                        except json.JSONDecodeError:
                            logger.warning(f"Failed to parse Ollama chunk: {line[:100]}")
                            continue

            # Finalize: get any remaining file in buffer
            final_file = parser.finalize_stream(state)
            if final_file:
                logger.debug(
                    f"Streaming final file: {final_file.path} "
                    f"({final_file.lines} lines)"
                )
                yield final_file

            logger.info(
                f"Streaming generation complete: {len(state.parsed_files)} files"
            )

        except httpx.ConnectError as e:
            logger.error(f"Ollama connection failed: {e}")
            raise
        except httpx.TimeoutException as e:
            logger.error(f"Ollama streaming timeout: {e}")
            raise
        except Exception as e:
            logger.exception(f"Unexpected error in streaming generation: {e}")
            raise

    async def generate_streaming_with_metadata(
        self,
        spec: CodegenSpec
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Generate code with streaming and emit structured events.

        Like generate_streaming but yields dict events for SSE compatibility.

        Yields:
            Dict events with type: 'file_generating', 'file_generated', etc.
        """
        async for file in self.generate_streaming(spec):
            # First yield generating event
            yield {
                "type": "file_generating",
                "path": file.path,
            }

            # Then yield generated event with content
            yield {
                "type": "file_generated",
                "path": file.path,
                "content": file.content,
                "lines": file.lines,
                "language": file.language,
                "syntax_valid": self._quick_syntax_check(file.content, file.language),
            }

    def _quick_syntax_check(self, content: str, language: str) -> bool:
        """Quick syntax validation for common languages."""
        if language == "python":
            try:
                import ast
                ast.parse(content)
                return True
            except SyntaxError:
                return False
        elif language == "json":
            try:
                json.loads(content)
                return True
            except json.JSONDecodeError:
                return False
        # For other languages, assume valid
        return True

    def invalidate_cache(self) -> None:
        """Force re-check of availability on next access."""
        self._available = None
        self._last_health_check = 0
