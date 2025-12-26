# Self-Healing Code Generation - Technical Design

**Version**: 1.0.0
**Status**: Ready for Implementation
**Sprint**: 51B
**Priority**: HIGH
**Effort**: 1 day
**Author**: CTO
**Date**: December 25, 2025

---

## 1. Overview

### 1.1 Problem Statement

Code generation failures currently require:
- Full regeneration from scratch
- Manual intervention to fix prompts
- No learning from previous failures

Common failure modes:
- Parse failures (malformed output from LLM)
- Quality gate failures (syntax errors, security issues)
- Provider timeouts
- Token limit exceeded

### 1.2 Solution

Implement self-healing with:
- Automatic retry with error context injection
- Error classification (recoverable vs fatal)
- Progressive prompt enhancement on failure
- Circuit breaker for provider failures

### 1.3 Success Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Manual intervention rate | 40%+ | <10% |
| Auto-recovery success rate | 0% | 80%+ |
| Failed generation waste | 100% | <20% |

---

## 2. Architecture

### 2.1 Error Classification

```python
# backend/app/services/codegen/error_classifier.py

from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel


class ErrorSeverity(str, Enum):
    """Error severity levels"""
    RECOVERABLE = "recoverable"    # Auto-retry possible
    ESCALATABLE = "escalatable"    # Need human review
    FATAL = "fatal"                # Cannot recover


class ErrorCategory(str, Enum):
    """Error category for targeted fixes"""
    PARSE_FAILURE = "parse_failure"           # LLM output not parseable
    SYNTAX_ERROR = "syntax_error"             # Generated code has syntax errors
    SECURITY_VIOLATION = "security_violation" # SAST/security check failed
    CONTEXT_MISMATCH = "context_mismatch"     # Import/file reference errors
    PROVIDER_TIMEOUT = "provider_timeout"     # LLM provider timed out
    PROVIDER_ERROR = "provider_error"         # LLM provider returned error
    QUOTA_EXCEEDED = "quota_exceeded"         # Rate limit or token limit
    VALIDATION_FAILED = "validation_failed"   # Quality gate failed


class ErrorContext(BaseModel):
    """Rich error context for retry decisions"""
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    suggestion: Optional[str] = None
    original_prompt: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    metadata: Dict[str, Any] = {}

    def can_retry(self) -> bool:
        """Check if error can be retried"""
        return (
            self.severity == ErrorSeverity.RECOVERABLE
            and self.retry_count < self.max_retries
        )


class ErrorClassifier:
    """Classify errors and determine recovery strategy"""

    # Error patterns and their classifications
    PARSE_PATTERNS = [
        ("Expected '### FILE:'", ErrorCategory.PARSE_FAILURE),
        ("No file markers found", ErrorCategory.PARSE_FAILURE),
        ("Invalid JSON", ErrorCategory.PARSE_FAILURE),
        ("Malformed output", ErrorCategory.PARSE_FAILURE),
    ]

    SYNTAX_PATTERNS = [
        ("SyntaxError:", ErrorCategory.SYNTAX_ERROR),
        ("IndentationError:", ErrorCategory.SYNTAX_ERROR),
        ("Unexpected token", ErrorCategory.SYNTAX_ERROR),
        ("ParseError:", ErrorCategory.SYNTAX_ERROR),
    ]

    SECURITY_PATTERNS = [
        ("hardcoded-secret", ErrorCategory.SECURITY_VIOLATION),
        ("sql-injection", ErrorCategory.SECURITY_VIOLATION),
        ("command-injection", ErrorCategory.SECURITY_VIOLATION),
        ("prompt-injection", ErrorCategory.SECURITY_VIOLATION),
    ]

    def classify(self, error: Exception, context: Dict[str, Any] = None) -> ErrorContext:
        """
        Classify an error and determine recovery strategy.

        Args:
            error: The exception that occurred
            context: Additional context (file_path, retry_count, etc.)

        Returns:
            ErrorContext with classification and recovery info
        """
        error_message = str(error)
        context = context or {}

        # Check for parse failures
        for pattern, category in self.PARSE_PATTERNS:
            if pattern.lower() in error_message.lower():
                return ErrorContext(
                    category=category,
                    severity=ErrorSeverity.RECOVERABLE,
                    message=error_message,
                    suggestion="Retry with stricter format instructions",
                    retry_count=context.get("retry_count", 0),
                    **context
                )

        # Check for syntax errors
        for pattern, category in self.SYNTAX_PATTERNS:
            if pattern.lower() in error_message.lower():
                return ErrorContext(
                    category=category,
                    severity=ErrorSeverity.RECOVERABLE,
                    message=error_message,
                    suggestion="Include syntax error in prompt for correction",
                    retry_count=context.get("retry_count", 0),
                    **context
                )

        # Check for security violations
        for pattern, category in self.SECURITY_PATTERNS:
            if pattern.lower() in error_message.lower():
                return ErrorContext(
                    category=category,
                    severity=ErrorSeverity.RECOVERABLE,
                    message=error_message,
                    suggestion="Add security constraints to prompt",
                    retry_count=context.get("retry_count", 0),
                    **context
                )

        # Provider-specific errors
        if "timeout" in error_message.lower():
            return ErrorContext(
                category=ErrorCategory.PROVIDER_TIMEOUT,
                severity=ErrorSeverity.RECOVERABLE,
                message=error_message,
                suggestion="Retry with fallback provider",
                retry_count=context.get("retry_count", 0),
                **context
            )

        if "rate limit" in error_message.lower() or "quota" in error_message.lower():
            return ErrorContext(
                category=ErrorCategory.QUOTA_EXCEEDED,
                severity=ErrorSeverity.ESCALATABLE,
                message=error_message,
                suggestion="Wait or switch provider",
                retry_count=context.get("retry_count", 0),
                **context
            )

        # Default to escalatable if unknown
        return ErrorContext(
            category=ErrorCategory.VALIDATION_FAILED,
            severity=ErrorSeverity.ESCALATABLE,
            message=error_message,
            suggestion="Review error and adjust configuration",
            retry_count=context.get("retry_count", 0),
            **context
        )
```

### 2.2 Retry Strategy

```python
# backend/app/services/codegen/retry_strategy.py

from typing import Optional, Callable, TypeVar, Awaitable
from functools import wraps
import asyncio
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
    RetryError
)
import logging

from app.services.codegen.error_classifier import (
    ErrorClassifier,
    ErrorContext,
    ErrorSeverity,
    ErrorCategory
)

logger = logging.getLogger(__name__)

T = TypeVar('T')


class RecoverableError(Exception):
    """Exception for errors that can be retried"""
    def __init__(self, context: ErrorContext):
        self.context = context
        super().__init__(context.message)


class EscalatableError(Exception):
    """Exception for errors that need human intervention"""
    def __init__(self, context: ErrorContext):
        self.context = context
        super().__init__(context.message)


class SelfHealingRetry:
    """
    Self-healing retry logic with progressive prompt enhancement.

    Features:
    - Exponential backoff (2s, 4s, 8s)
    - Error context injection into prompts
    - Provider fallback on timeout
    - Circuit breaker integration
    """

    def __init__(
        self,
        max_attempts: int = 3,
        min_wait: float = 2.0,
        max_wait: float = 10.0,
        classifier: Optional[ErrorClassifier] = None
    ):
        self.max_attempts = max_attempts
        self.min_wait = min_wait
        self.max_wait = max_wait
        self.classifier = classifier or ErrorClassifier()

    def with_healing(
        self,
        prompt_enhancer: Optional[Callable[[str, ErrorContext], str]] = None
    ):
        """
        Decorator for self-healing retry logic.

        Args:
            prompt_enhancer: Function to enhance prompt with error context
        """
        def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
            @wraps(func)
            async def wrapper(*args, **kwargs) -> T:
                last_error: Optional[ErrorContext] = None
                retry_count = 0

                while retry_count < self.max_attempts:
                    try:
                        # Enhance prompt if we have error context
                        if last_error and prompt_enhancer and 'prompt' in kwargs:
                            kwargs['prompt'] = prompt_enhancer(
                                kwargs['prompt'],
                                last_error
                            )
                            kwargs['retry_context'] = last_error

                        return await func(*args, **kwargs)

                    except Exception as e:
                        retry_count += 1
                        error_context = self.classifier.classify(
                            e,
                            context={
                                "retry_count": retry_count,
                                "original_prompt": kwargs.get('prompt'),
                                **kwargs.get('metadata', {})
                            }
                        )

                        if not error_context.can_retry():
                            if error_context.severity == ErrorSeverity.ESCALATABLE:
                                raise EscalatableError(error_context)
                            raise

                        last_error = error_context

                        # Calculate backoff
                        wait_time = min(
                            self.min_wait * (2 ** retry_count),
                            self.max_wait
                        )

                        logger.warning(
                            f"Recoverable error (attempt {retry_count}/{self.max_attempts}): "
                            f"{error_context.category.value}. Retrying in {wait_time}s"
                        )

                        await asyncio.sleep(wait_time)

                # Max retries exceeded
                if last_error:
                    raise EscalatableError(last_error)
                raise

            return wrapper
        return decorator


def default_prompt_enhancer(prompt: str, error: ErrorContext) -> str:
    """
    Enhance prompt with error context for better retry.

    Adds specific instructions based on error category.
    """
    enhancements = []

    if error.category == ErrorCategory.PARSE_FAILURE:
        enhancements.append(
            "\n\n**IMPORTANT**: Your previous response was not properly formatted. "
            "You MUST use the exact format: '### FILE: path/to/file.py' followed by "
            "the file content in a code block. Do NOT include any other markers."
        )

    elif error.category == ErrorCategory.SYNTAX_ERROR:
        enhancements.append(
            f"\n\n**IMPORTANT**: Your previous code had a syntax error:\n"
            f"```\n{error.message}\n```\n"
            f"Please fix this error and ensure all code is valid Python/TypeScript."
        )
        if error.file_path:
            enhancements.append(f"The error was in file: {error.file_path}")

    elif error.category == ErrorCategory.SECURITY_VIOLATION:
        enhancements.append(
            f"\n\n**SECURITY REQUIREMENT**: Your previous code violated security rules:\n"
            f"- {error.message}\n"
            f"Please ensure:\n"
            f"- No hardcoded secrets or API keys\n"
            f"- Use environment variables for configuration\n"
            f"- Use parameterized queries for database access\n"
            f"- Validate and sanitize all inputs"
        )

    elif error.category == ErrorCategory.CONTEXT_MISMATCH:
        enhancements.append(
            f"\n\n**IMPORTANT**: Your previous code had reference errors:\n"
            f"- {error.message}\n"
            f"Please ensure all imports reference existing files and modules."
        )

    if enhancements:
        return prompt + "\n".join(enhancements)

    return prompt
```

### 2.3 Integration with CodegenService

```python
# backend/app/services/codegen/codegen_service.py (additions)

from app.services.codegen.retry_strategy import (
    SelfHealingRetry,
    RecoverableError,
    EscalatableError,
    default_prompt_enhancer
)
from app.services.codegen.error_classifier import ErrorContext, ErrorCategory


class CodegenService:
    """Enhanced CodegenService with self-healing capabilities"""

    def __init__(self, ...):
        # ... existing init ...
        self.retry = SelfHealingRetry(
            max_attempts=settings.MAX_RETRY_ATTEMPTS,
            min_wait=settings.RETRY_MIN_WAIT,
            max_wait=settings.RETRY_MAX_WAIT
        )
        self.classifier = ErrorClassifier()

    @self.retry.with_healing(prompt_enhancer=default_prompt_enhancer)
    async def generate_file(
        self,
        file_spec: FileSpec,
        prompt: str,
        retry_context: Optional[ErrorContext] = None,
        **kwargs
    ) -> GeneratedFile:
        """
        Generate a single file with self-healing.

        Args:
            file_spec: Specification for the file to generate
            prompt: Generation prompt
            retry_context: Error context from previous attempt (injected by retry)

        Returns:
            GeneratedFile with content
        """
        try:
            # Add retry context to prompt if available
            enhanced_prompt = prompt
            if retry_context:
                enhanced_prompt = default_prompt_enhancer(prompt, retry_context)

            # Call provider
            result = await self.provider.generate(enhanced_prompt)

            # Parse output
            file = self.parser.parse_single_file(result, file_spec)

            # Validate
            validation_result = await self.validate_file(file)
            if not validation_result.passed:
                raise ValueError(
                    f"Validation failed: {validation_result.errors}"
                )

            return file

        except Exception as e:
            # Classify and potentially retry
            error_context = self.classifier.classify(e, {
                "file_path": file_spec.path,
                "retry_count": kwargs.get('_retry_count', 0)
            })

            if error_context.can_retry():
                raise RecoverableError(error_context)
            raise

    async def generate_with_healing(
        self,
        request: GenerateRequest,
        on_file: Callable[[GeneratedFile], Awaitable[None]],
        on_error: Callable[[ErrorContext], Awaitable[None]],
        on_healing: Callable[[ErrorContext, int], Awaitable[None]]
    ) -> GenerationResult:
        """
        Generate all files with self-healing and callbacks.

        Args:
            request: Generation request
            on_file: Callback when file is generated
            on_error: Callback when unrecoverable error occurs
            on_healing: Callback when self-healing is attempted

        Returns:
            GenerationResult with all files and any errors
        """
        files = []
        errors = []
        healed_count = 0

        for file_spec in request.files:
            try:
                file = await self.generate_file(
                    file_spec=file_spec,
                    prompt=self._build_prompt(request.blueprint, file_spec)
                )
                files.append(file)
                await on_file(file)

            except RecoverableError as e:
                # Self-healing in progress
                healed_count += 1
                await on_healing(e.context, healed_count)
                # Retry is handled by decorator

            except EscalatableError as e:
                # Need human intervention
                errors.append(e.context)
                await on_error(e.context)

            except Exception as e:
                # Unexpected error
                error_context = self.classifier.classify(e)
                errors.append(error_context)
                await on_error(error_context)

        return GenerationResult(
            files=files,
            errors=errors,
            healed_count=healed_count,
            success=len(errors) == 0
        )
```

---

## 3. Quality Gate Integration

### 3.1 Quality Pipeline with Auto-Fix Suggestions

```python
# backend/app/services/codegen/quality_pipeline.py (additions)

from typing import List, Optional
from dataclasses import dataclass

from app.services.codegen.error_classifier import ErrorContext, ErrorCategory


@dataclass
class FixSuggestion:
    """Suggestion for fixing a quality issue"""
    issue: str
    suggestion: str
    auto_fixable: bool
    fix_prompt: Optional[str] = None  # Prompt addition for LLM to fix


class QualityPipelineWithHealing:
    """Quality pipeline that provides fix suggestions for self-healing"""

    async def validate_with_suggestions(
        self,
        file: GeneratedFile
    ) -> tuple[ValidationResult, List[FixSuggestion]]:
        """
        Validate file and return fix suggestions.

        Returns:
            (ValidationResult, List of FixSuggestion)
        """
        result = await self.validate(file)
        suggestions = []

        for error in result.errors:
            suggestion = self._get_fix_suggestion(error, file)
            if suggestion:
                suggestions.append(suggestion)

        return result, suggestions

    def _get_fix_suggestion(
        self,
        error: ValidationError,
        file: GeneratedFile
    ) -> Optional[FixSuggestion]:
        """Generate fix suggestion based on error type"""

        # Syntax errors
        if "SyntaxError" in error.message:
            return FixSuggestion(
                issue=error.message,
                suggestion="Fix syntax error on the indicated line",
                auto_fixable=True,
                fix_prompt=f"""
The file {file.path} has a syntax error:
{error.message}

Please regenerate ONLY this file with the syntax error fixed.
Ensure the code is valid {file.language}.
"""
            )

        # Missing imports
        if "ImportError" in error.message or "ModuleNotFoundError" in error.message:
            return FixSuggestion(
                issue=error.message,
                suggestion="Add missing import or check module path",
                auto_fixable=True,
                fix_prompt=f"""
The file {file.path} has an import error:
{error.message}

Please regenerate ONLY this file with the correct import.
Ensure the imported module exists in the project structure.
"""
            )

        # Security issues
        if error.category == "security":
            security_rule = error.rule_id or "security violation"
            return FixSuggestion(
                issue=error.message,
                suggestion=f"Fix security issue: {security_rule}",
                auto_fixable=True,
                fix_prompt=f"""
The file {file.path} has a security issue:
Rule: {security_rule}
Message: {error.message}

Please regenerate ONLY this file with the security issue fixed:
- If it's a hardcoded secret, use environment variables
- If it's SQL injection, use parameterized queries
- If it's command injection, validate and sanitize inputs
"""
            )

        # Type errors
        if "TypeError" in error.message or "type" in error.category:
            return FixSuggestion(
                issue=error.message,
                suggestion="Fix type annotation or type mismatch",
                auto_fixable=True,
                fix_prompt=f"""
The file {file.path} has a type error:
{error.message}

Please regenerate ONLY this file with correct type annotations.
"""
            )

        return None

    def build_healing_prompt(
        self,
        original_prompt: str,
        file: GeneratedFile,
        suggestions: List[FixSuggestion]
    ) -> str:
        """Build enhanced prompt for self-healing retry"""
        healing_instructions = "\n\n## FIX REQUIRED\n\n"
        healing_instructions += f"Your previous generation of `{file.path}` had issues:\n\n"

        for i, suggestion in enumerate(suggestions, 1):
            healing_instructions += f"{i}. **{suggestion.issue}**\n"
            healing_instructions += f"   Fix: {suggestion.suggestion}\n"
            if suggestion.fix_prompt:
                healing_instructions += f"\n{suggestion.fix_prompt}\n"

        healing_instructions += "\nPlease regenerate the file with these issues fixed.\n"

        return original_prompt + healing_instructions
```

---

## 4. Circuit Breaker Integration

### 4.1 Circuit Breaker for Providers

```python
# backend/app/services/codegen/circuit_breaker.py

from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Callable, TypeVar, Awaitable
from functools import wraps
import asyncio
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')


class CircuitState(str, Enum):
    CLOSED = "closed"       # Normal operation
    OPEN = "open"           # Failing, reject all calls
    HALF_OPEN = "half_open" # Testing if recovered


class CircuitBreaker:
    """
    Circuit breaker for provider failure handling.

    States:
    - CLOSED: Normal operation, track failures
    - OPEN: Reject all calls, wait for recovery_timeout
    - HALF_OPEN: Allow limited calls to test recovery
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        success_threshold: int = 3,
        expected_exceptions: tuple = (Exception,)
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold
        self.expected_exceptions = expected_exceptions

        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.last_state_change: datetime = datetime.utcnow()

    @property
    def is_closed(self) -> bool:
        return self.state == CircuitState.CLOSED

    @property
    def is_open(self) -> bool:
        if self.state == CircuitState.OPEN:
            # Check if recovery timeout has passed
            if self.last_failure_time:
                elapsed = (datetime.utcnow() - self.last_failure_time).total_seconds()
                if elapsed >= self.recovery_timeout:
                    self._transition_to(CircuitState.HALF_OPEN)
                    return False
            return True
        return False

    def _transition_to(self, new_state: CircuitState):
        """Transition to new state"""
        old_state = self.state
        self.state = new_state
        self.last_state_change = datetime.utcnow()
        logger.info(f"Circuit breaker '{self.name}': {old_state.value} -> {new_state.value}")

        if new_state == CircuitState.CLOSED:
            self.failure_count = 0
            self.success_count = 0
        elif new_state == CircuitState.HALF_OPEN:
            self.success_count = 0

    def record_success(self):
        """Record a successful call"""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                self._transition_to(CircuitState.CLOSED)
        elif self.state == CircuitState.CLOSED:
            # Reset failure count on success
            self.failure_count = 0

    def record_failure(self):
        """Record a failed call"""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()

        if self.state == CircuitState.HALF_OPEN:
            # Any failure in half-open goes back to open
            self._transition_to(CircuitState.OPEN)
        elif self.state == CircuitState.CLOSED:
            if self.failure_count >= self.failure_threshold:
                self._transition_to(CircuitState.OPEN)

    def __call__(self, func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        """Decorator for protecting async functions"""
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            if self.is_open:
                raise CircuitOpenError(
                    f"Circuit breaker '{self.name}' is open. "
                    f"Retry after {self.recovery_timeout}s"
                )

            try:
                result = await func(*args, **kwargs)
                self.record_success()
                return result

            except self.expected_exceptions as e:
                self.record_failure()
                raise

        return wrapper


class CircuitOpenError(Exception):
    """Exception raised when circuit breaker is open"""
    pass


# Pre-configured circuit breakers
PROVIDER_CIRCUIT_BREAKERS = {
    "ollama": CircuitBreaker(
        name="ollama",
        failure_threshold=5,
        recovery_timeout=30,
        success_threshold=3
    ),
    "claude": CircuitBreaker(
        name="claude",
        failure_threshold=3,
        recovery_timeout=60,
        success_threshold=2
    ),
    "deepcode": CircuitBreaker(
        name="deepcode",
        failure_threshold=3,
        recovery_timeout=60,
        success_threshold=2
    )
}


def get_circuit_breaker(provider: str) -> CircuitBreaker:
    """Get circuit breaker for a provider"""
    return PROVIDER_CIRCUIT_BREAKERS.get(
        provider,
        CircuitBreaker(name=provider)
    )
```

---

## 5. SSE Events for Self-Healing

### 5.1 Event Types

```python
# backend/app/schemas/streaming.py (additions)

from typing import Literal
from pydantic import BaseModel


class HealingAttemptEvent(BaseModel):
    """SSE event when self-healing is attempted"""
    type: Literal["healing_attempt"] = "healing_attempt"
    session_id: str
    file_path: str
    attempt_number: int
    max_attempts: int
    error_category: str
    error_message: str
    healing_strategy: str  # What we're doing to fix it


class HealingSuccessEvent(BaseModel):
    """SSE event when self-healing succeeds"""
    type: Literal["healing_success"] = "healing_success"
    session_id: str
    file_path: str
    attempts_taken: int
    time_to_heal_ms: int


class HealingFailedEvent(BaseModel):
    """SSE event when self-healing fails after all retries"""
    type: Literal["healing_failed"] = "healing_failed"
    session_id: str
    file_path: str
    final_error: str
    attempts_exhausted: int
    needs_human_intervention: bool
    suggestion: str


class CircuitBreakerEvent(BaseModel):
    """SSE event for circuit breaker state changes"""
    type: Literal["circuit_breaker"] = "circuit_breaker"
    provider: str
    state: str  # closed, open, half_open
    reason: str
    retry_after_seconds: Optional[int] = None
```

### 5.2 Frontend Handling

```typescript
// frontend/web/src/hooks/useSelfHealing.ts

import { useState, useCallback } from 'react';

interface HealingState {
  isHealing: boolean;
  currentFile: string | null;
  attemptNumber: number;
  maxAttempts: number;
  healingHistory: HealingAttempt[];
}

interface HealingAttempt {
  file_path: string;
  error_category: string;
  error_message: string;
  success: boolean;
  attempts_taken: number;
  time_to_heal_ms?: number;
}

export function useSelfHealing() {
  const [state, setState] = useState<HealingState>({
    isHealing: false,
    currentFile: null,
    attemptNumber: 0,
    maxAttempts: 3,
    healingHistory: [],
  });

  const handleHealingEvent = useCallback((event: MessageEvent) => {
    const data = JSON.parse(event.data);

    switch (data.type) {
      case 'healing_attempt':
        setState(prev => ({
          ...prev,
          isHealing: true,
          currentFile: data.file_path,
          attemptNumber: data.attempt_number,
          maxAttempts: data.max_attempts,
        }));
        break;

      case 'healing_success':
        setState(prev => ({
          ...prev,
          isHealing: false,
          currentFile: null,
          healingHistory: [
            ...prev.healingHistory,
            {
              file_path: data.file_path,
              error_category: 'resolved',
              error_message: '',
              success: true,
              attempts_taken: data.attempts_taken,
              time_to_heal_ms: data.time_to_heal_ms,
            }
          ]
        }));
        break;

      case 'healing_failed':
        setState(prev => ({
          ...prev,
          isHealing: false,
          currentFile: null,
          healingHistory: [
            ...prev.healingHistory,
            {
              file_path: data.file_path,
              error_category: data.final_error,
              error_message: data.suggestion,
              success: false,
              attempts_taken: data.attempts_exhausted,
            }
          ]
        }));
        break;
    }
  }, []);

  return {
    ...state,
    handleHealingEvent,
  };
}
```

---

## 6. Configuration

### 6.1 Environment Variables

```bash
# .env.example additions

# Self-Healing Configuration
MAX_RETRY_ATTEMPTS=3               # Max retries per file
RETRY_MIN_WAIT=2                   # Minimum wait between retries (seconds)
RETRY_MAX_WAIT=10                  # Maximum wait between retries (seconds)
RETRY_BACKOFF_MULTIPLIER=2         # Exponential backoff multiplier

# Circuit Breaker
CIRCUIT_BREAKER_ENABLED=true
CIRCUIT_FAILURE_THRESHOLD=5        # Failures before opening
CIRCUIT_RECOVERY_TIMEOUT=30        # Seconds before half-open
CIRCUIT_SUCCESS_THRESHOLD=3        # Successes to close
```

### 6.2 Settings

```python
# backend/app/core/config.py additions

class Settings(BaseSettings):
    # ... existing settings ...

    # Self-Healing
    MAX_RETRY_ATTEMPTS: int = 3
    RETRY_MIN_WAIT: float = 2.0
    RETRY_MAX_WAIT: float = 10.0
    RETRY_BACKOFF_MULTIPLIER: float = 2.0

    # Circuit Breaker
    CIRCUIT_BREAKER_ENABLED: bool = True
    CIRCUIT_FAILURE_THRESHOLD: int = 5
    CIRCUIT_RECOVERY_TIMEOUT: float = 30.0
    CIRCUIT_SUCCESS_THRESHOLD: int = 3
```

---

## 7. Testing

### 7.1 Unit Tests

```python
# backend/tests/unit/services/test_self_healing.py

import pytest
from unittest.mock import AsyncMock, patch

from app.services.codegen.error_classifier import (
    ErrorClassifier,
    ErrorCategory,
    ErrorSeverity,
    ErrorContext
)
from app.services.codegen.retry_strategy import (
    SelfHealingRetry,
    RecoverableError,
    default_prompt_enhancer
)


class TestErrorClassifier:

    def test_classifies_parse_failure(self):
        classifier = ErrorClassifier()
        error = ValueError("Expected '### FILE:' marker not found")

        result = classifier.classify(error)

        assert result.category == ErrorCategory.PARSE_FAILURE
        assert result.severity == ErrorSeverity.RECOVERABLE

    def test_classifies_syntax_error(self):
        classifier = ErrorClassifier()
        error = SyntaxError("invalid syntax at line 10")

        result = classifier.classify(error)

        assert result.category == ErrorCategory.SYNTAX_ERROR
        assert result.severity == ErrorSeverity.RECOVERABLE

    def test_classifies_security_violation(self):
        classifier = ErrorClassifier()
        error = ValueError("hardcoded-secret detected in config.py")

        result = classifier.classify(error)

        assert result.category == ErrorCategory.SECURITY_VIOLATION
        assert result.severity == ErrorSeverity.RECOVERABLE

    def test_classifies_timeout_as_recoverable(self):
        classifier = ErrorClassifier()
        error = TimeoutError("Request timeout after 30s")

        result = classifier.classify(error)

        assert result.category == ErrorCategory.PROVIDER_TIMEOUT
        assert result.severity == ErrorSeverity.RECOVERABLE

    def test_classifies_quota_as_escalatable(self):
        classifier = ErrorClassifier()
        error = ValueError("Rate limit exceeded")

        result = classifier.classify(error)

        assert result.category == ErrorCategory.QUOTA_EXCEEDED
        assert result.severity == ErrorSeverity.ESCALATABLE


class TestPromptEnhancer:

    def test_enhances_for_parse_failure(self):
        error = ErrorContext(
            category=ErrorCategory.PARSE_FAILURE,
            severity=ErrorSeverity.RECOVERABLE,
            message="No file markers found"
        )

        result = default_prompt_enhancer("Generate a file", error)

        assert "### FILE:" in result
        assert "IMPORTANT" in result

    def test_enhances_for_syntax_error(self):
        error = ErrorContext(
            category=ErrorCategory.SYNTAX_ERROR,
            severity=ErrorSeverity.RECOVERABLE,
            message="IndentationError: unexpected indent",
            file_path="main.py"
        )

        result = default_prompt_enhancer("Generate a file", error)

        assert "syntax error" in result.lower()
        assert "main.py" in result

    def test_enhances_for_security_violation(self):
        error = ErrorContext(
            category=ErrorCategory.SECURITY_VIOLATION,
            severity=ErrorSeverity.RECOVERABLE,
            message="hardcoded-secret: API key in source"
        )

        result = default_prompt_enhancer("Generate a file", error)

        assert "SECURITY" in result
        assert "environment variables" in result.lower()


class TestSelfHealingRetry:

    @pytest.mark.asyncio
    async def test_retries_on_recoverable_error(self):
        retry = SelfHealingRetry(max_attempts=3)
        call_count = 0

        @retry.with_healing()
        async def flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Expected '### FILE:'")
            return "success"

        result = await flaky_function()

        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_raises_after_max_retries(self):
        retry = SelfHealingRetry(max_attempts=2)

        @retry.with_healing()
        async def always_fails():
            raise ValueError("Expected '### FILE:'")

        with pytest.raises(Exception):
            await always_fails()

    @pytest.mark.asyncio
    async def test_uses_prompt_enhancer(self):
        enhanced_prompts = []

        def track_enhancer(prompt, error):
            enhanced_prompts.append((prompt, error))
            return prompt + " [ENHANCED]"

        retry = SelfHealingRetry(max_attempts=2)
        call_count = 0

        @retry.with_healing(prompt_enhancer=track_enhancer)
        async def function_with_prompt(prompt):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Parse error")
            return prompt

        result = await function_with_prompt(prompt="original")

        assert len(enhanced_prompts) == 1
        assert "[ENHANCED]" in result
```

---

## 8. Monitoring

### 8.1 Prometheus Metrics

```python
# Metrics to add

healing_attempts_total = Counter(
    'codegen_healing_attempts_total',
    'Total self-healing attempts',
    ['error_category', 'outcome']  # outcome: success, failure
)

healing_duration_seconds = Histogram(
    'codegen_healing_duration_seconds',
    'Time spent in self-healing',
    buckets=[1, 2, 5, 10, 20, 30, 60]
)

circuit_breaker_state = Gauge(
    'codegen_circuit_breaker_state',
    'Circuit breaker state (0=closed, 1=open, 2=half_open)',
    ['provider']
)

circuit_breaker_failures = Counter(
    'codegen_circuit_breaker_failures_total',
    'Total circuit breaker failures',
    ['provider']
)
```

---

## 9. Rollout Plan

### Day 1 (Morning): Core Implementation
- [ ] Implement ErrorClassifier
- [ ] Implement SelfHealingRetry
- [ ] Implement prompt enhancers
- [ ] Unit tests

### Day 1 (Afternoon): Integration
- [ ] Integrate with CodegenService
- [ ] Add SSE events
- [ ] Add circuit breaker
- [ ] Integration tests

### Day 1 (Evening): Frontend + Deploy
- [ ] Add useSelfHealing hook
- [ ] Add HealingProgress component
- [ ] Deploy to staging
- [ ] E2E tests

---

## 10. References

- [Vibecode Pattern Adoption Plan](../15-Pattern-Adoption/Vibecode-Pattern-Adoption-Plan.md)
- [Session Checkpoint Design](./Session-Checkpoint-Design.md)
- [Circuit Breaker Pattern](https://martinfowler.com/bliki/CircuitBreaker.html)
- [Tenacity Library](https://tenacity.readthedocs.io/)

---

**Last Updated**: December 25, 2025
**Owner**: Backend Team
**Status**: Ready for Implementation
