"""
=========================================================================
Error Classifier - Self-Healing Code Generation
SDLC Orchestrator - Sprint 51B

Version: 1.0.0
Date: December 26, 2025
Status: ACTIVE - Sprint 51B Implementation
Authority: Backend Team + CTO Approved
Foundation: Self-Healing-Codegen-Design.md

Purpose:
- Classify code generation errors
- Determine recovery strategy (recoverable vs fatal)
- Provide context for retry decisions
- Enable progressive prompt enhancement

References:
- docs/02-design/14-Technical-Specs/Self-Healing-Codegen-Design.md
- docs/02-design/15-Pattern-Adoption/Vibecode-Pattern-Adoption-Plan.md
=========================================================================
"""

from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class ErrorSeverity(str, Enum):
    """Error severity levels for recovery decisions."""
    RECOVERABLE = "recoverable"    # Auto-retry possible
    ESCALATABLE = "escalatable"    # Need human review
    FATAL = "fatal"                # Cannot recover


class ErrorCategory(str, Enum):
    """Error category for targeted fixes."""
    PARSE_FAILURE = "parse_failure"           # LLM output not parseable
    SYNTAX_ERROR = "syntax_error"             # Generated code has syntax errors
    SECURITY_VIOLATION = "security_violation"  # SAST/security check failed
    CONTEXT_MISMATCH = "context_mismatch"     # Import/file reference errors
    PROVIDER_TIMEOUT = "provider_timeout"     # LLM provider timed out
    PROVIDER_ERROR = "provider_error"         # LLM provider returned error
    QUOTA_EXCEEDED = "quota_exceeded"         # Rate limit or token limit
    VALIDATION_FAILED = "validation_failed"   # Quality gate failed
    UNKNOWN = "unknown"                       # Unclassified error


class ErrorContext(BaseModel):
    """
    Rich error context for retry decisions.

    Contains all information needed to:
    - Determine if retry is possible
    - Enhance prompts for next attempt
    - Track retry history
    """
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    suggestion: Optional[str] = None
    original_prompt: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def can_retry(self) -> bool:
        """Check if error can be retried."""
        return (
            self.severity == ErrorSeverity.RECOVERABLE
            and self.retry_count < self.max_retries
        )

    def increment_retry(self) -> "ErrorContext":
        """Return new context with incremented retry count."""
        return ErrorContext(
            category=self.category,
            severity=self.severity,
            message=self.message,
            file_path=self.file_path,
            line_number=self.line_number,
            suggestion=self.suggestion,
            original_prompt=self.original_prompt,
            retry_count=self.retry_count + 1,
            max_retries=self.max_retries,
            metadata=self.metadata,
        )


class ErrorClassifier:
    """
    Classify errors and determine recovery strategy.

    Error Classification Logic:
    1. Match error message against known patterns
    2. Determine category (parse, syntax, security, etc.)
    3. Assign severity (recoverable, escalatable, fatal)
    4. Provide suggestions for retry

    Example usage:
        classifier = ErrorClassifier()
        context = classifier.classify(
            ValueError("SyntaxError: invalid syntax"),
            {"file_path": "app/main.py", "retry_count": 0}
        )
        if context.can_retry():
            # Retry with enhanced prompt
            pass
    """

    # Error patterns and their classifications
    PARSE_PATTERNS = [
        ("Expected '### FILE:'", ErrorCategory.PARSE_FAILURE),
        ("No file markers found", ErrorCategory.PARSE_FAILURE),
        ("Invalid JSON", ErrorCategory.PARSE_FAILURE),
        ("Malformed output", ErrorCategory.PARSE_FAILURE),
        ("Failed to parse", ErrorCategory.PARSE_FAILURE),
        ("Could not extract", ErrorCategory.PARSE_FAILURE),
    ]

    SYNTAX_PATTERNS = [
        ("SyntaxError:", ErrorCategory.SYNTAX_ERROR),
        ("IndentationError:", ErrorCategory.SYNTAX_ERROR),
        ("Unexpected token", ErrorCategory.SYNTAX_ERROR),
        ("ParseError:", ErrorCategory.SYNTAX_ERROR),
        ("TabError:", ErrorCategory.SYNTAX_ERROR),
        ("invalid syntax", ErrorCategory.SYNTAX_ERROR),
    ]

    SECURITY_PATTERNS = [
        ("hardcoded-secret", ErrorCategory.SECURITY_VIOLATION),
        ("sql-injection", ErrorCategory.SECURITY_VIOLATION),
        ("command-injection", ErrorCategory.SECURITY_VIOLATION),
        ("prompt-injection", ErrorCategory.SECURITY_VIOLATION),
        ("xss", ErrorCategory.SECURITY_VIOLATION),
        ("insecure-password", ErrorCategory.SECURITY_VIOLATION),
    ]

    CONTEXT_PATTERNS = [
        ("ImportError:", ErrorCategory.CONTEXT_MISMATCH),
        ("ModuleNotFoundError:", ErrorCategory.CONTEXT_MISMATCH),
        ("No module named", ErrorCategory.CONTEXT_MISMATCH),
        ("Cannot find module", ErrorCategory.CONTEXT_MISMATCH),
        ("File not found", ErrorCategory.CONTEXT_MISMATCH),
    ]

    PROVIDER_PATTERNS = [
        ("connection refused", ErrorCategory.PROVIDER_ERROR),
        ("service unavailable", ErrorCategory.PROVIDER_ERROR),
        ("internal server error", ErrorCategory.PROVIDER_ERROR),
        ("502", ErrorCategory.PROVIDER_ERROR),
        ("503", ErrorCategory.PROVIDER_ERROR),
    ]

    def classify(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None
    ) -> ErrorContext:
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

        # Check for parse failures (most common with LLM output)
        for pattern, category in self.PARSE_PATTERNS:
            if pattern.lower() in error_message.lower():
                return ErrorContext(
                    category=category,
                    severity=ErrorSeverity.RECOVERABLE,
                    message=error_message,
                    suggestion="Retry with stricter format instructions",
                    retry_count=context.get("retry_count", 0),
                    file_path=context.get("file_path"),
                    original_prompt=context.get("original_prompt"),
                    metadata=context.get("metadata", {}),
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
                    file_path=context.get("file_path"),
                    line_number=self._extract_line_number(error_message),
                    original_prompt=context.get("original_prompt"),
                    metadata=context.get("metadata", {}),
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
                    file_path=context.get("file_path"),
                    original_prompt=context.get("original_prompt"),
                    metadata=context.get("metadata", {}),
                )

        # Check for context/import errors
        for pattern, category in self.CONTEXT_PATTERNS:
            if pattern.lower() in error_message.lower():
                return ErrorContext(
                    category=category,
                    severity=ErrorSeverity.RECOVERABLE,
                    message=error_message,
                    suggestion="Verify imports match generated files",
                    retry_count=context.get("retry_count", 0),
                    file_path=context.get("file_path"),
                    original_prompt=context.get("original_prompt"),
                    metadata=context.get("metadata", {}),
                )

        # Check for provider errors
        for pattern, category in self.PROVIDER_PATTERNS:
            if pattern.lower() in error_message.lower():
                return ErrorContext(
                    category=category,
                    severity=ErrorSeverity.RECOVERABLE,
                    message=error_message,
                    suggestion="Retry with fallback provider",
                    retry_count=context.get("retry_count", 0),
                    original_prompt=context.get("original_prompt"),
                    metadata=context.get("metadata", {}),
                )

        # Provider timeout
        if "timeout" in error_message.lower():
            return ErrorContext(
                category=ErrorCategory.PROVIDER_TIMEOUT,
                severity=ErrorSeverity.RECOVERABLE,
                message=error_message,
                suggestion="Retry with fallback provider or increased timeout",
                retry_count=context.get("retry_count", 0),
                original_prompt=context.get("original_prompt"),
                metadata=context.get("metadata", {}),
            )

        # Rate limit / quota exceeded
        if "rate limit" in error_message.lower() or "quota" in error_message.lower():
            return ErrorContext(
                category=ErrorCategory.QUOTA_EXCEEDED,
                severity=ErrorSeverity.ESCALATABLE,
                message=error_message,
                suggestion="Wait or switch provider",
                retry_count=context.get("retry_count", 0),
                original_prompt=context.get("original_prompt"),
                metadata=context.get("metadata", {}),
            )

        # Default to escalatable if unknown
        return ErrorContext(
            category=ErrorCategory.UNKNOWN,
            severity=ErrorSeverity.ESCALATABLE,
            message=error_message,
            suggestion="Review error and adjust configuration",
            retry_count=context.get("retry_count", 0),
            file_path=context.get("file_path"),
            original_prompt=context.get("original_prompt"),
            metadata=context.get("metadata", {}),
        )

    def _extract_line_number(self, error_message: str) -> Optional[int]:
        """Extract line number from error message if present."""
        import re
        # Match patterns like "line 42" or "Line 42" or ":42:"
        patterns = [
            r"line\s+(\d+)",
            r"Line\s+(\d+)",
            r":(\d+):",
        ]
        for pattern in patterns:
            match = re.search(pattern, error_message, re.IGNORECASE)
            if match:
                return int(match.group(1))
        return None

    def is_recoverable(self, error: Exception) -> bool:
        """Quick check if error is recoverable."""
        context = self.classify(error)
        return context.severity == ErrorSeverity.RECOVERABLE
