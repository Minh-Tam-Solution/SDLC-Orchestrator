"""
=========================================================================
Retry Strategy - Self-Healing Code Generation
SDLC Orchestrator - Sprint 51B

Version: 1.0.0
Date: December 26, 2025
Status: ACTIVE - Sprint 51B Implementation
Authority: Backend Team + CTO Approved
Foundation: Self-Healing-Codegen-Design.md

Purpose:
- Self-healing retry logic with progressive prompt enhancement
- Exponential backoff (2s, 4s, 8s)
- Error context injection into prompts
- Provider fallback on timeout
- Circuit breaker integration

References:
- docs/02-design/14-Technical-Specs/Self-Healing-Codegen-Design.md
- docs/02-design/15-Pattern-Adoption/Vibecode-Pattern-Adoption-Plan.md
=========================================================================
"""

import asyncio
import logging
from functools import wraps
from typing import Awaitable, Callable, Optional, TypeVar

from app.services.codegen.error_classifier import (
    ErrorCategory,
    ErrorClassifier,
    ErrorContext,
    ErrorSeverity,
)

logger = logging.getLogger(__name__)

T = TypeVar('T')


class RecoverableError(Exception):
    """Exception for errors that can be retried."""

    def __init__(self, context: ErrorContext):
        self.context = context
        super().__init__(context.message)


class EscalatableError(Exception):
    """Exception for errors that need human intervention."""

    def __init__(self, context: ErrorContext):
        self.context = context
        super().__init__(context.message)


class FatalError(Exception):
    """Exception for errors that cannot be recovered."""

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
    - Circuit breaker integration (future)

    Example usage:
        retry = SelfHealingRetry(max_attempts=3)

        @retry.with_healing(prompt_enhancer=default_prompt_enhancer)
        async def generate_code(prompt: str) -> str:
            return await provider.generate(prompt)

        try:
            result = await generate_code(prompt="Generate...")
        except EscalatableError as e:
            # Need human intervention
            notify_admin(e.context)
    """

    def __init__(
        self,
        max_attempts: int = 3,
        min_wait: float = 2.0,
        max_wait: float = 10.0,
        classifier: Optional[ErrorClassifier] = None
    ):
        """
        Initialize retry strategy.

        Args:
            max_attempts: Maximum number of retry attempts
            min_wait: Minimum wait time between retries (seconds)
            max_wait: Maximum wait time between retries (seconds)
            classifier: Error classifier instance
        """
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

        Returns:
            Decorated async function with self-healing retry logic
        """
        def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
            @wraps(func)
            async def wrapper(*args, **kwargs) -> T:
                last_error: Optional[ErrorContext] = None
                retry_count = 0

                while retry_count < self.max_attempts:
                    try:
                        # Enhance prompt if we have error context from previous attempt
                        if last_error and prompt_enhancer and 'prompt' in kwargs:
                            kwargs['prompt'] = prompt_enhancer(
                                kwargs['prompt'],
                                last_error
                            )
                            kwargs['retry_context'] = last_error

                        return await func(*args, **kwargs)

                    except RecoverableError as e:
                        # Already classified as recoverable
                        retry_count += 1
                        last_error = e.context.increment_retry()

                        if not last_error.can_retry():
                            raise EscalatableError(last_error)

                        await self._wait_with_backoff(retry_count)

                    except EscalatableError:
                        # Already escalated, re-raise
                        raise

                    except FatalError:
                        # Cannot recover, re-raise
                        raise

                    except Exception as e:
                        # Classify the error
                        retry_count += 1
                        error_context = self.classifier.classify(
                            e,
                            context={
                                "retry_count": retry_count,
                                "original_prompt": kwargs.get('prompt'),
                                "file_path": kwargs.get('file_path'),
                                "metadata": kwargs.get('metadata', {})
                            }
                        )

                        if not error_context.can_retry():
                            if error_context.severity == ErrorSeverity.ESCALATABLE:
                                raise EscalatableError(error_context)
                            elif error_context.severity == ErrorSeverity.FATAL:
                                raise FatalError(error_context)
                            raise

                        last_error = error_context
                        await self._wait_with_backoff(retry_count)

                # Max retries exceeded
                if last_error:
                    raise EscalatableError(last_error)
                raise RuntimeError("Max retries exceeded with no error context")

            return wrapper
        return decorator

    async def _wait_with_backoff(self, retry_count: int) -> None:
        """
        Wait with exponential backoff.

        Args:
            retry_count: Current retry attempt number
        """
        wait_time = min(
            self.min_wait * (2 ** (retry_count - 1)),
            self.max_wait
        )
        logger.warning(
            f"Recoverable error (attempt {retry_count}/{self.max_attempts}). "
            f"Retrying in {wait_time:.1f}s"
        )
        await asyncio.sleep(wait_time)

    async def execute_with_fallback(
        self,
        primary: Callable[..., Awaitable[T]],
        fallback: Callable[..., Awaitable[T]],
        *args,
        **kwargs
    ) -> T:
        """
        Execute with fallback provider on failure.

        Args:
            primary: Primary function to execute
            fallback: Fallback function if primary fails
            *args: Arguments for both functions
            **kwargs: Keyword arguments for both functions

        Returns:
            Result from primary or fallback function
        """
        try:
            return await primary(*args, **kwargs)
        except (RecoverableError, EscalatableError) as e:
            logger.warning(
                f"Primary function failed: {e.context.message}. "
                f"Trying fallback..."
            )
            return await fallback(*args, **kwargs)


def default_prompt_enhancer(prompt: str, error: ErrorContext) -> str:
    """
    Enhance prompt with error context for better retry.

    Adds specific instructions based on error category to help
    the LLM avoid making the same mistake.

    Args:
        prompt: Original prompt
        error: Error context from previous attempt

    Returns:
        Enhanced prompt with error-specific instructions
    """
    enhancements = []

    if error.category == ErrorCategory.PARSE_FAILURE:
        enhancements.append(
            "\n\n**IMPORTANT FORMAT REQUIREMENTS**:\n"
            "Your previous response was not properly formatted. "
            "You MUST use the exact format:\n"
            "```\n"
            "### FILE: path/to/file.py\n"
            "```python\n"
            "# file content here\n"
            "```\n"
            "```\n"
            "Do NOT include any other markers or prefixes."
        )

    elif error.category == ErrorCategory.SYNTAX_ERROR:
        enhancements.append(
            f"\n\n**SYNTAX ERROR TO FIX**:\n"
            f"Your previous code had a syntax error:\n"
            f"```\n{error.message}\n```\n"
            f"Please fix this error and ensure all code is valid Python/TypeScript."
        )
        if error.file_path:
            enhancements.append(f"The error was in file: {error.file_path}")
        if error.line_number:
            enhancements.append(f"Error at line: {error.line_number}")

    elif error.category == ErrorCategory.SECURITY_VIOLATION:
        enhancements.append(
            f"\n\n**SECURITY REQUIREMENTS**:\n"
            f"Your previous code violated security rules:\n"
            f"- {error.message}\n\n"
            f"Please ensure:\n"
            f"- No hardcoded secrets or API keys\n"
            f"- Use environment variables for configuration\n"
            f"- Use parameterized queries for database access\n"
            f"- Validate and sanitize all user inputs\n"
            f"- Follow OWASP security guidelines"
        )

    elif error.category == ErrorCategory.CONTEXT_MISMATCH:
        enhancements.append(
            f"\n\n**IMPORT/REFERENCE ERROR**:\n"
            f"Your previous code had reference errors:\n"
            f"- {error.message}\n\n"
            f"Please ensure all imports reference existing files and modules "
            f"that you are generating in this session."
        )

    elif error.category == ErrorCategory.PROVIDER_TIMEOUT:
        enhancements.append(
            "\n\n**OPTIMIZATION REQUESTED**:\n"
            "Previous generation timed out. Please generate a more concise "
            "implementation. Focus on core functionality first."
        )

    if enhancements:
        return prompt + "\n".join(enhancements)

    return prompt


def create_healing_wrapper(
    max_attempts: int = 3,
    prompt_enhancer: Optional[Callable[[str, ErrorContext], str]] = None
) -> Callable:
    """
    Factory function to create self-healing wrapper.

    Args:
        max_attempts: Maximum retry attempts
        prompt_enhancer: Optional custom prompt enhancer

    Returns:
        Decorator function for self-healing

    Example:
        healing = create_healing_wrapper(max_attempts=3)

        @healing
        async def generate(prompt: str) -> str:
            return await provider.generate(prompt)
    """
    retry = SelfHealingRetry(max_attempts=max_attempts)
    enhancer = prompt_enhancer or default_prompt_enhancer
    return retry.with_healing(prompt_enhancer=enhancer)
