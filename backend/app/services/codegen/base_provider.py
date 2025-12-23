"""
CodegenProvider Abstract Interface.

Sprint 45: Multi-Provider Codegen Architecture (EP-06)
ADR-022: Provider-Agnostic Codegen Architecture

This module defines the abstract interface for all codegen providers.
All providers (Ollama, Claude, DeepCode) must implement this interface.

Design Decisions:
- Abstract base class pattern for provider interface
- Pydantic models for type-safe data transfer
- 3 core methods: generate(), validate(), estimate_cost()
- Properties for name and availability

Author: Backend Lead
Date: December 23, 2025
Status: ACTIVE
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field


class CodegenSpec(BaseModel):
    """
    Input specification for code generation.

    This is the IR (Intermediate Representation) that defines what code
    to generate. Uses app_blueprint schema for structured generation.

    Attributes:
        app_blueprint: Dict from app_blueprint.schema.json defining the app
        target_module: Optional specific module to generate (None = all)
        language: Target programming language (default: python)
        framework: Target framework (default: fastapi)
        options: Additional provider-specific options

    Example:
        >>> spec = CodegenSpec(
        ...     app_blueprint={
        ...         "name": "TaskManager",
        ...         "modules": [{"name": "tasks", "entities": [...]}]
        ...     },
        ...     language="python",
        ...     framework="fastapi"
        ... )
    """
    app_blueprint: Dict[str, Any] = Field(
        ...,
        description="App blueprint from app_blueprint.schema.json"
    )
    target_module: Optional[str] = Field(
        None,
        description="Specific module to generate (None = all modules)"
    )
    language: str = Field(
        "python",
        description="Target programming language"
    )
    framework: str = Field(
        "fastapi",
        description="Target framework"
    )
    options: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional provider-specific options"
    )


class CodegenResult(BaseModel):
    """
    Output from code generation.

    Contains the generated code, file mapping, and metadata about
    the generation process (tokens used, time taken, etc).

    Attributes:
        code: Raw generated code output (full response)
        files: Dict mapping file paths to file contents
        metadata: Additional metadata (model, tokens, etc)
        provider: Name of the provider that generated the code
        tokens_used: Total tokens consumed in generation
        generation_time_ms: Time taken for generation in milliseconds

    Example:
        >>> result = CodegenResult(
        ...     code="...",
        ...     files={"app/models/task.py": "class Task:..."},
        ...     metadata={"model": "qwen2.5-coder:32b"},
        ...     provider="ollama",
        ...     tokens_used=1500,
        ...     generation_time_ms=2500
        ... )
    """
    code: str = Field(
        ...,
        description="Raw generated code output"
    )
    files: Dict[str, str] = Field(
        default_factory=dict,
        description="Dict mapping file paths to contents"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata about generation"
    )
    provider: str = Field(
        ...,
        description="Name of provider that generated the code"
    )
    tokens_used: int = Field(
        0,
        description="Total tokens consumed",
        ge=0
    )
    generation_time_ms: int = Field(
        0,
        description="Generation time in milliseconds",
        ge=0
    )


class ValidationResult(BaseModel):
    """
    Output from code validation.

    Contains validation status and categorized issues found
    (errors, warnings, suggestions).

    Attributes:
        valid: Overall validation status (True = passed)
        errors: List of critical errors that must be fixed
        warnings: List of warnings that should be addressed
        suggestions: List of optional improvements

    Example:
        >>> result = ValidationResult(
        ...     valid=False,
        ...     errors=["Missing required import"],
        ...     warnings=["Function too long (>50 lines)"],
        ...     suggestions=["Consider adding type hints"]
        ... )
    """
    valid: bool = Field(
        ...,
        description="Overall validation status"
    )
    errors: List[str] = Field(
        default_factory=list,
        description="Critical errors that must be fixed"
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="Warnings that should be addressed"
    )
    suggestions: List[str] = Field(
        default_factory=list,
        description="Optional improvement suggestions"
    )


class CostEstimate(BaseModel):
    """
    Cost estimation for code generation.

    Provides upfront cost estimates before running generation,
    helping with budget management and provider selection.

    Attributes:
        estimated_tokens: Estimated total tokens (input + output)
        estimated_cost_usd: Estimated cost in USD
        provider: Provider name for this estimate
        confidence: Confidence level 0-1 (1 = highly confident)

    Example:
        >>> estimate = CostEstimate(
        ...     estimated_tokens=5000,
        ...     estimated_cost_usd=0.05,
        ...     provider="ollama",
        ...     confidence=0.85
        ... )
    """
    estimated_tokens: int = Field(
        ...,
        description="Estimated total tokens",
        ge=0
    )
    estimated_cost_usd: float = Field(
        ...,
        description="Estimated cost in USD",
        ge=0
    )
    provider: str = Field(
        ...,
        description="Provider name for this estimate"
    )
    confidence: float = Field(
        ...,
        description="Confidence level 0-1",
        ge=0,
        le=1
    )


class CodegenProvider(ABC):
    """
    Abstract base class for all codegen providers.

    All codegen providers (Ollama, Claude, DeepCode) must implement
    this interface. This ensures consistent API across providers
    and enables seamless fallback when one provider is unavailable.

    Properties:
        name: Provider identifier (e.g., 'ollama', 'claude', 'deepcode')
        is_available: Whether provider is configured and reachable

    Methods:
        generate(): Generate code from IR specification
        validate(): Validate generated code
        estimate_cost(): Estimate cost before generation

    Example Implementation:
        >>> class MyProvider(CodegenProvider):
        ...     @property
        ...     def name(self) -> str:
        ...         return "my_provider"
        ...
        ...     @property
        ...     def is_available(self) -> bool:
        ...         return self._check_health()
        ...
        ...     async def generate(self, spec: CodegenSpec) -> CodegenResult:
        ...         # Implementation
        ...         pass
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Provider identifier.

        Returns a unique string identifier for this provider.
        Used for logging, configuration, and provider selection.

        Returns:
            str: Provider name (e.g., 'ollama', 'claude', 'deepcode')
        """
        pass

    @property
    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if provider is configured and reachable.

        Performs a quick health check to determine if this provider
        can be used for code generation. Should be fast (<5s).

        Returns:
            bool: True if provider is ready to accept requests
        """
        pass

    @abstractmethod
    async def generate(self, spec: CodegenSpec) -> CodegenResult:
        """
        Generate code from IR specification.

        Takes an IR specification (app_blueprint) and generates
        complete, production-ready code files.

        Args:
            spec: CodegenSpec with app_blueprint and options

        Returns:
            CodegenResult with generated code and metadata

        Raises:
            ProviderUnavailableError: Provider not configured or unreachable
            GenerationError: Code generation failed

        Example:
            >>> result = await provider.generate(CodegenSpec(
            ...     app_blueprint={"name": "App", "modules": [...]},
            ...     language="python",
            ...     framework="fastapi"
            ... ))
            >>> print(result.files)  # {"app/main.py": "...", ...}
        """
        pass

    @abstractmethod
    async def validate(
        self,
        code: str,
        context: Dict[str, Any]
    ) -> ValidationResult:
        """
        Validate generated code.

        Performs AI-powered validation on generated code to check
        for errors, potential issues, and improvement suggestions.

        Args:
            code: Generated code to validate
            context: Additional context (language, framework, etc.)

        Returns:
            ValidationResult with validation status and issues

        Example:
            >>> result = await provider.validate(
            ...     code="def foo(): pass",
            ...     context={"language": "python"}
            ... )
            >>> print(result.valid)  # True
        """
        pass

    @abstractmethod
    def estimate_cost(self, spec: CodegenSpec) -> CostEstimate:
        """
        Estimate cost for code generation.

        Provides upfront cost estimation before running the actual
        generation. Helps with budget management and provider selection.

        Args:
            spec: CodegenSpec to estimate

        Returns:
            CostEstimate with token and cost projections

        Example:
            >>> estimate = provider.estimate_cost(spec)
            >>> print(f"Estimated: ${estimate.estimated_cost_usd:.2f}")
        """
        pass

    def __repr__(self) -> str:
        """String representation of provider."""
        status = "available" if self.is_available else "unavailable"
        return f"<{self.__class__.__name__}(name={self.name}, {status})>"
