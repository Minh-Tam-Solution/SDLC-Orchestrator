"""
Codegen API Routes.

Sprint 45: Multi-Provider Codegen Architecture (EP-06)
ADR-022: Provider-Agnostic Codegen Architecture

This module provides REST API endpoints for code generation service.
Supports multi-provider architecture with Ollama as primary provider.

Endpoints:
- GET  /codegen/providers - List available providers
- POST /codegen/generate - Generate code from IR specification
- POST /codegen/validate - Validate generated code
- POST /codegen/estimate - Estimate generation cost
- GET  /codegen/health - Provider health check

Author: Backend Lead
Date: December 23, 2025
Status: ACTIVE
"""

import logging
from typing import Optional, Dict, Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.api.dependencies import get_current_active_user
from app.models.user import User
from app.services.codegen.codegen_service import (
    CodegenService,
    NoProviderAvailableError,
    GenerationError,
    get_codegen_service
)
from app.services.codegen.base_provider import CodegenSpec

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/codegen", tags=["Codegen"])


# ============================================================================
# Request/Response Models
# ============================================================================


class GenerateRequest(BaseModel):
    """
    Request model for code generation.

    Attributes:
        app_blueprint: IR specification defining the app to generate
        target_module: Optional specific module to generate
        language: Target programming language (default: python)
        framework: Target framework (default: fastapi)
        preferred_provider: Optional preferred provider name
    """
    app_blueprint: Dict[str, Any] = Field(
        ...,
        description="App blueprint (IR specification)"
    )
    target_module: Optional[str] = Field(
        None,
        description="Specific module to generate (None = all)"
    )
    language: str = Field(
        "python",
        description="Target programming language"
    )
    framework: str = Field(
        "fastapi",
        description="Target framework"
    )
    preferred_provider: Optional[str] = Field(
        None,
        description="Preferred provider (ollama, claude, etc.)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "app_blueprint": {
                    "name": "TaskManager",
                    "description": "Hệ thống quản lý công việc cho SME",
                    "modules": [
                        {
                            "name": "tasks",
                            "entities": [
                                {
                                    "name": "Task",
                                    "fields": [
                                        {"name": "id", "type": "uuid", "primary": True},
                                        {"name": "title", "type": "string", "max_length": 200},
                                        {"name": "description", "type": "text"},
                                        {"name": "status", "type": "enum", "values": ["todo", "in_progress", "done"]},
                                        {"name": "due_date", "type": "datetime", "nullable": True}
                                    ]
                                }
                            ]
                        }
                    ]
                },
                "language": "python",
                "framework": "fastapi"
            }
        }


class ValidateRequest(BaseModel):
    """
    Request model for code validation.

    Attributes:
        code: Code to validate
        context: Additional context for validation
        provider: Optional specific provider to use
    """
    code: str = Field(
        ...,
        description="Code to validate",
        min_length=1,
        max_length=100000
    )
    context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional context (language, framework, etc.)"
    )
    provider: Optional[str] = Field(
        None,
        description="Specific provider to use"
    )


class ProviderInfo(BaseModel):
    """Provider information response model."""
    name: str
    available: bool
    fallback_position: int
    primary: bool


class ProvidersResponse(BaseModel):
    """Response model for list providers endpoint."""
    providers: List[ProviderInfo]
    fallback_chain: List[str]


class GenerateResponse(BaseModel):
    """Response model for generate endpoint."""
    success: bool
    provider: str
    files: Dict[str, str]
    tokens_used: int
    generation_time_ms: int
    metadata: Dict[str, Any]


class ValidateResponse(BaseModel):
    """Response model for validate endpoint."""
    valid: bool
    errors: List[str]
    warnings: List[str]
    suggestions: List[str]


class CostEstimateItem(BaseModel):
    """Cost estimate for a single provider."""
    estimated_tokens: int
    estimated_cost_usd: float
    confidence: float


class EstimateResponse(BaseModel):
    """Response model for estimate endpoint."""
    estimates: Dict[str, CostEstimateItem]
    recommended_provider: Optional[str]


class HealthResponse(BaseModel):
    """Response model for health check endpoint."""
    healthy: bool
    providers: Dict[str, bool]
    available_count: int
    total_count: int
    fallback_chain: List[str]


# ============================================================================
# Dependency
# ============================================================================


def get_service() -> CodegenService:
    """Get the global CodegenService instance."""
    return get_codegen_service()


# ============================================================================
# Endpoints
# ============================================================================


@router.get("/providers", response_model=ProvidersResponse)
async def list_providers(
    current_user: User = Depends(get_current_active_user),
    service: CodegenService = Depends(get_service)
) -> ProvidersResponse:
    """
    List available codegen providers.

    Returns all registered providers with their availability status
    and position in the fallback chain.

    Returns:
        ProvidersResponse with provider list and fallback chain
    """
    providers = service.list_providers()
    health = service.health_check()

    return ProvidersResponse(
        providers=[ProviderInfo(**p) for p in providers],
        fallback_chain=health["fallback_chain"]
    )


@router.post("/generate", response_model=GenerateResponse)
async def generate_code(
    request: GenerateRequest,
    current_user: User = Depends(get_current_active_user),
    service: CodegenService = Depends(get_service)
) -> GenerateResponse:
    """
    Generate code from IR specification.

    Takes an app blueprint (IR) and generates production-ready code
    using the available AI provider (Ollama by default).

    Args:
        request: GenerateRequest with app_blueprint and options

    Returns:
        GenerateResponse with generated files and metadata

    Raises:
        503: No providers available
        500: Generation failed
    """
    logger.info(
        f"Code generation requested by user {current_user.id}: "
        f"language={request.language}, framework={request.framework}"
    )

    try:
        spec = CodegenSpec(
            app_blueprint=request.app_blueprint,
            target_module=request.target_module,
            language=request.language,
            framework=request.framework
        )

        result = await service.generate(
            spec,
            preferred_provider=request.preferred_provider
        )

        logger.info(
            f"Generation complete for user {current_user.id}: "
            f"{len(result.files)} files, {result.tokens_used} tokens"
        )

        return GenerateResponse(
            success=True,
            provider=result.provider,
            files=result.files,
            tokens_used=result.tokens_used,
            generation_time_ms=result.generation_time_ms,
            metadata=result.metadata
        )

    except NoProviderAvailableError as e:
        logger.error(f"No providers available: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )

    except GenerationError as e:
        logger.error(f"Generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Code generation failed: {e}"
        )

    except Exception as e:
        logger.exception(f"Unexpected error during generation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {e}"
        )


@router.post("/validate", response_model=ValidateResponse)
async def validate_code(
    request: ValidateRequest,
    current_user: User = Depends(get_current_active_user),
    service: CodegenService = Depends(get_service)
) -> ValidateResponse:
    """
    Validate generated code.

    Performs AI-powered validation on code to check for errors,
    potential issues, and improvement suggestions.

    Args:
        request: ValidateRequest with code and context

    Returns:
        ValidateResponse with validation results

    Raises:
        503: No providers available
        500: Validation failed
    """
    logger.info(
        f"Code validation requested by user {current_user.id}: "
        f"{len(request.code)} chars"
    )

    try:
        result = await service.validate(
            request.code,
            request.context,
            provider_name=request.provider
        )

        return ValidateResponse(
            valid=result.valid,
            errors=result.errors,
            warnings=result.warnings,
            suggestions=result.suggestions
        )

    except NoProviderAvailableError as e:
        logger.error(f"No providers available for validation: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )

    except Exception as e:
        logger.exception(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Validation failed: {e}"
        )


@router.post("/estimate", response_model=EstimateResponse)
async def estimate_cost(
    request: GenerateRequest,
    current_user: User = Depends(get_current_active_user),
    service: CodegenService = Depends(get_service)
) -> EstimateResponse:
    """
    Estimate generation cost across providers.

    Returns cost estimates for all available providers to help
    with budget management and provider selection.

    Args:
        request: GenerateRequest with app_blueprint

    Returns:
        EstimateResponse with per-provider cost estimates
    """
    spec = CodegenSpec(
        app_blueprint=request.app_blueprint,
        target_module=request.target_module,
        language=request.language,
        framework=request.framework
    )

    estimates = service.estimate_cost(spec)

    # Convert to response format
    estimate_items = {
        name: CostEstimateItem(
            estimated_tokens=est.estimated_tokens,
            estimated_cost_usd=est.estimated_cost_usd,
            confidence=est.confidence
        )
        for name, est in estimates.items()
    }

    # Find cheapest available provider
    cheapest = service.get_cheapest_provider(spec)
    recommended = cheapest[0] if cheapest else None

    return EstimateResponse(
        estimates=estimate_items,
        recommended_provider=recommended
    )


@router.get("/health", response_model=HealthResponse)
async def health_check(
    service: CodegenService = Depends(get_service)
) -> HealthResponse:
    """
    Provider health check.

    Returns health status for all providers without requiring
    authentication (useful for monitoring).

    Returns:
        HealthResponse with provider status
    """
    health = service.health_check()

    return HealthResponse(
        healthy=health["healthy"],
        providers=health["providers"],
        available_count=health["available_count"],
        total_count=health["total_count"],
        fallback_chain=health["fallback_chain"]
    )
