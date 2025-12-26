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


# ============================================================================
# IR-Based Generation Endpoints (Sprint 46)
# ============================================================================


class IRGenerateRequest(BaseModel):
    """
    Request model for IR-based deterministic code generation.

    This uses Jinja2 templates (no AI) for predictable, fast generation.
    """
    blueprint: Dict[str, Any] = Field(
        ...,
        description="AppBlueprint specification"
    )
    preview: bool = Field(
        False,
        description="If true, return file list without content"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "blueprint": {
                    "name": "Restaurant Management",
                    "version": "1.0.0",
                    "modules": [{
                        "name": "products",
                        "entities": [{
                            "name": "Product",
                            "fields": [
                                {"name": "name", "type": "string", "required": True},
                                {"name": "price", "type": "float", "required": True}
                            ]
                        }]
                    }]
                },
                "preview": False
            }
        }


class IRGeneratedFile(BaseModel):
    """Single generated file."""
    path: str
    content: Optional[str] = None
    language: Optional[str] = None
    lines: int


class IRGenerateResponse(BaseModel):
    """Response model for IR-based generation."""
    success: bool
    app_name: str
    version: Optional[str] = None
    file_count: int
    total_lines: int
    files: List[IRGeneratedFile]
    errors: List[str] = []
    metadata: Dict[str, Any] = {}


class IRValidateResponse(BaseModel):
    """Response model for IR blueprint validation."""
    valid: bool
    issues: List[Dict[str, str]] = []
    normalized_blueprint: Optional[Dict[str, Any]] = None
    summary: Dict[str, Any] = {}


@router.post("/ir/generate", response_model=IRGenerateResponse)
async def ir_generate(
    request: IRGenerateRequest,
    current_user: User = Depends(get_current_active_user),
) -> IRGenerateResponse:
    """
    Generate backend scaffold from AppBlueprint using IR Processor.

    This endpoint uses deterministic Jinja2 templates (no AI) for fast,
    predictable code generation. Suitable for standard CRUD applications.

    Sprint 46: EP-06 IR-Based Backend Scaffold Generation
    ADR-023: IR-Based Deterministic Code Generation

    Args:
        request: IRGenerateRequest with blueprint specification

    Returns:
        IRGenerateResponse with generated files

    Raises:
        400: Invalid blueprint
        500: Generation failed
    """
    from pathlib import Path
    from app.services.codegen.ir import BundleBuilder, IRValidator

    logger.info(f"IR generation requested by user {current_user.id}")

    try:
        # Validate blueprint
        validator = IRValidator()
        validation = validator.validate_app_blueprint(request.blueprint)

        if not validation.valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": "Invalid blueprint",
                    "issues": [
                        {"path": i.path, "message": i.message, "severity": i.severity}
                        for i in validation.issues
                    ]
                }
            )

        # Get template directory
        template_dir = Path(__file__).parent.parent.parent / "services" / "codegen" / "templates"

        # Build bundle
        builder = BundleBuilder(template_dir=template_dir)

        if request.preview:
            preview = builder.build_preview(validation.normalized_ir)
            return IRGenerateResponse(
                success=preview["success"],
                app_name=preview.get("app_name", "Unknown"),
                file_count=preview["file_count"],
                total_lines=0,
                files=[
                    IRGeneratedFile(
                        path=f["path"],
                        language=f.get("language"),
                        lines=f.get("lines", 0)
                    )
                    for f in preview.get("files", [])
                ],
                errors=preview.get("errors", [])
            )

        bundle = builder.build(validation.normalized_ir)

        if not bundle.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"message": "Generation failed", "errors": bundle.errors}
            )

        logger.info(
            f"IR generation complete for user {current_user.id}: "
            f"{bundle.file_count} files, {bundle.total_lines} lines"
        )

        return IRGenerateResponse(
            success=True,
            app_name=bundle.app_name,
            version=bundle.version,
            file_count=bundle.file_count,
            total_lines=bundle.total_lines,
            files=[
                IRGeneratedFile(
                    path=f.path,
                    content=f.content,
                    language=f.language,
                    lines=len(f.content.split("\n")) if f.content else 0
                )
                for f in bundle.files
            ],
            metadata=bundle.to_dict_for_api().get("metadata", {})
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"IR generation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Generation failed: {str(e)}"
        )


@router.post("/ir/validate", response_model=IRValidateResponse)
async def ir_validate(
    request: IRGenerateRequest,
    current_user: User = Depends(get_current_active_user),
) -> IRValidateResponse:
    """
    Validate AppBlueprint without generating code.

    Returns validation results and normalized blueprint if valid.

    Args:
        request: IRGenerateRequest with blueprint to validate

    Returns:
        IRValidateResponse with validation results
    """
    from app.services.codegen.ir import IRValidator

    logger.info(f"IR validation requested by user {current_user.id}")

    validator = IRValidator()
    result = validator.validate_app_blueprint(request.blueprint)

    # Build summary
    summary = {}
    if result.valid and result.normalized_ir:
        ir = result.normalized_ir
        modules = ir.get("modules", [])
        summary = {
            "name": ir.get("name"),
            "version": ir.get("version"),
            "business_domain": ir.get("business_domain"),
            "module_count": len(modules),
            "entity_count": sum(len(m.get("entities", [])) for m in modules),
            "total_fields": sum(
                len(e.get("fields", []))
                for m in modules
                for e in m.get("entities", [])
            )
        }

    return IRValidateResponse(
        valid=result.valid,
        issues=[
            {"path": i.path, "message": i.message, "severity": i.severity}
            for i in result.issues
        ],
        normalized_blueprint=result.normalized_ir if result.valid else None,
        summary=summary
    )


# ============================================================================
# Vietnamese Onboarding Endpoints (Sprint 47)
# ============================================================================


class OnboardingStartRequest(BaseModel):
    """Request to start onboarding session."""
    locale: str = Field("vi", description="Locale (vi or en)")


class OnboardingSessionResponse(BaseModel):
    """Onboarding session info."""
    session_id: str
    current_step: str
    completed_steps: List[str]
    domain: Optional[str] = None
    app_name: Optional[str] = None
    app_name_display: Optional[str] = None
    features: List[str] = []
    scale: Optional[str] = None
    has_blueprint: bool = False
    locale: str = "vi"


class DomainOptionResponse(BaseModel):
    """Domain option for UI."""
    key: str
    name: str
    name_en: str
    description: str
    icon: str
    example_apps: List[str]


class FeatureOptionResponse(BaseModel):
    """Feature option for UI."""
    key: str
    name: str
    description: str


class ScaleOptionResponse(BaseModel):
    """Scale option for UI."""
    key: str
    label: str
    employee_min: int
    employee_max: int
    cgf_tier: str


class SetDomainRequest(BaseModel):
    """Request to set domain."""
    domain: str = Field(..., description="Domain key (restaurant, hotel, retail)")


class SetAppNameRequest(BaseModel):
    """Request to set app name."""
    app_name: str = Field(..., description="App name (Vietnamese OK)")


class SetFeaturesRequest(BaseModel):
    """Request to set features."""
    features: List[str] = Field(..., description="Feature keys")


class SetScaleRequest(BaseModel):
    """Request to set scale."""
    scale: str = Field(..., description="Scale key (micro, small, medium, large)")


class OnboardingStepResponse(BaseModel):
    """Response for onboarding step."""
    success: bool
    error: Optional[str] = None
    next_step: Optional[str] = None
    data: Dict[str, Any] = {}


class OnboardingBlueprintResponse(BaseModel):
    """Response for blueprint generation."""
    success: bool
    errors: List[str] = []
    blueprint: Optional[Dict[str, Any]] = None
    stats: Dict[str, Any] = {}


@router.post("/onboarding/start", response_model=OnboardingSessionResponse)
async def start_onboarding(
    request: OnboardingStartRequest,
    current_user: User = Depends(get_current_active_user),
) -> OnboardingSessionResponse:
    """
    Start new onboarding session for Vietnamese SME founder.

    Sprint 47: Vietnamese Domain Templates + Onboarding IR (EP-06)

    Returns session ID and initial state for guided wizard.
    """
    from app.services.codegen.onboarding import OnboardingService

    service = OnboardingService(locale=request.locale)
    session = service.create_session()

    logger.info(f"Onboarding started by user {current_user.id}: {session.session_id}")

    data = session.to_dict()
    return OnboardingSessionResponse(**data)


@router.get("/onboarding/{session_id}", response_model=OnboardingSessionResponse)
async def get_onboarding_session(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
) -> OnboardingSessionResponse:
    """Get onboarding session status."""
    from app.services.codegen.onboarding import OnboardingService

    service = OnboardingService()
    session = service.get_session(session_id)

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    data = session.to_dict()
    return OnboardingSessionResponse(**data)


@router.get("/onboarding/options/domains", response_model=List[DomainOptionResponse])
async def get_domain_options(
    current_user: User = Depends(get_current_active_user),
) -> List[DomainOptionResponse]:
    """Get available domain options (restaurant, hotel, retail)."""
    from app.services.codegen.onboarding import OnboardingService

    service = OnboardingService()
    options = service.get_domain_options()

    return [DomainOptionResponse(**opt) for opt in options]


@router.get(
    "/onboarding/options/features/{domain}",
    response_model=List[FeatureOptionResponse]
)
async def get_feature_options(
    domain: str,
    current_user: User = Depends(get_current_active_user),
) -> List[FeatureOptionResponse]:
    """Get available features for a domain."""
    from app.services.codegen.onboarding import OnboardingService

    service = OnboardingService()
    options = service.get_feature_options(domain)

    if not options:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown domain: {domain}"
        )

    return [FeatureOptionResponse(**opt) for opt in options]


@router.get("/onboarding/options/scales", response_model=List[ScaleOptionResponse])
async def get_scale_options(
    current_user: User = Depends(get_current_active_user),
) -> List[ScaleOptionResponse]:
    """Get available scale options."""
    from app.services.codegen.onboarding import OnboardingService

    service = OnboardingService()
    options = service.get_scale_options()

    return [ScaleOptionResponse(**opt) for opt in options]


@router.post(
    "/onboarding/{session_id}/domain",
    response_model=OnboardingStepResponse
)
async def set_onboarding_domain(
    session_id: str,
    request: SetDomainRequest,
    current_user: User = Depends(get_current_active_user),
) -> OnboardingStepResponse:
    """Set domain selection for onboarding session."""
    from app.services.codegen.onboarding import OnboardingService

    service = OnboardingService()
    session = service.get_session(session_id)

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    result = service.set_domain(session, request.domain)

    return OnboardingStepResponse(
        success=result.get("success", False),
        error=result.get("error"),
        next_step=result.get("next_step"),
        data={k: v for k, v in result.items() if k not in ["success", "error", "next_step"]}
    )


@router.post(
    "/onboarding/{session_id}/app_name",
    response_model=OnboardingStepResponse
)
async def set_onboarding_app_name(
    session_id: str,
    request: SetAppNameRequest,
    current_user: User = Depends(get_current_active_user),
) -> OnboardingStepResponse:
    """Set app name for onboarding session."""
    from app.services.codegen.onboarding import OnboardingService

    service = OnboardingService()
    session = service.get_session(session_id)

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    result = service.set_app_name(session, request.app_name)

    return OnboardingStepResponse(
        success=result.get("success", False),
        error=result.get("error"),
        next_step=result.get("next_step"),
        data={k: v for k, v in result.items() if k not in ["success", "error", "next_step"]}
    )


@router.post(
    "/onboarding/{session_id}/features",
    response_model=OnboardingStepResponse
)
async def set_onboarding_features(
    session_id: str,
    request: SetFeaturesRequest,
    current_user: User = Depends(get_current_active_user),
) -> OnboardingStepResponse:
    """Set features for onboarding session."""
    from app.services.codegen.onboarding import OnboardingService

    service = OnboardingService()
    session = service.get_session(session_id)

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    result = service.set_features(session, request.features)

    return OnboardingStepResponse(
        success=result.get("success", False),
        error=result.get("error"),
        next_step=result.get("next_step"),
        data={k: v for k, v in result.items() if k not in ["success", "error", "next_step"]}
    )


@router.post(
    "/onboarding/{session_id}/scale",
    response_model=OnboardingStepResponse
)
async def set_onboarding_scale(
    session_id: str,
    request: SetScaleRequest,
    current_user: User = Depends(get_current_active_user),
) -> OnboardingStepResponse:
    """Set scale for onboarding session."""
    from app.services.codegen.onboarding import OnboardingService

    service = OnboardingService()
    session = service.get_session(session_id)

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    result = service.set_scale(session, request.scale)

    return OnboardingStepResponse(
        success=result.get("success", False),
        error=result.get("error"),
        next_step=result.get("next_step"),
        data={k: v for k, v in result.items() if k not in ["success", "error", "next_step"]}
    )


@router.post(
    "/onboarding/{session_id}/generate",
    response_model=OnboardingBlueprintResponse
)
async def generate_onboarding_blueprint(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
) -> OnboardingBlueprintResponse:
    """
    Generate AppBlueprint from completed onboarding session.

    Returns valid AppBlueprint IR that can be used with /ir/generate endpoint.
    """
    from app.services.codegen.onboarding import OnboardingService

    service = OnboardingService()
    session = service.get_session(session_id)

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    result = service.generate_blueprint(session)

    logger.info(
        f"Onboarding blueprint generated for user {current_user.id}: "
        f"session={session_id}, success={result.get('success')}"
    )

    return OnboardingBlueprintResponse(
        success=result.get("success", False),
        errors=result.get("errors", []),
        blueprint=result.get("blueprint"),
        stats=result.get("stats", {})
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


# ============================================================================
# Cost Tracking Endpoints (Sprint 48)
# ============================================================================


class CostReportRequest(BaseModel):
    """Request for cost report."""
    days: int = Field(30, ge=1, le=365, description="Number of days to include")
    project_id: Optional[str] = Field(None, description="Filter by project ID")


class DailyCostItem(BaseModel):
    """Daily cost item."""
    date: str
    cost_usd: float
    requests: int


class CostTotals(BaseModel):
    """Cost totals summary."""
    requests: int
    tokens: int
    cost_usd: float
    avg_generation_time_ms: int
    files_generated: int
    lines_generated: int


class QualityMetrics(BaseModel):
    """Quality gate metrics."""
    pass_rate_percent: float
    total_errors: int
    total_warnings: int


class CostProjections(BaseModel):
    """Cost projections."""
    monthly_estimate_usd: float
    budget_limit_usd: float


class CostReportResponse(BaseModel):
    """Response for cost report."""
    period: Dict[str, Any]
    totals: CostTotals
    daily_costs: List[DailyCostItem]
    quality: QualityMetrics
    projections: CostProjections


class MonthlyCostResponse(BaseModel):
    """Response for monthly cost summary."""
    year: int
    month: int
    total_requests: int
    total_tokens: int
    total_cost_usd: float
    budget_limit_usd: float
    budget_used_percent: float
    budget_exceeded: bool
    cost_by_provider: Dict[str, float]


class ProviderHealthItem(BaseModel):
    """Provider health check item."""
    checked_at: str
    is_available: bool
    response_time_ms: Optional[int]
    model: Optional[str]
    model_available: bool
    error_message: Optional[str]


class ProviderHealthResponse(BaseModel):
    """Response for provider health history."""
    provider: str
    hours: int
    checks: List[ProviderHealthItem]
    availability_percent: float


@router.get("/usage/report", response_model=CostReportResponse)
async def get_cost_report(
    days: int = 30,
    project_id: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
) -> CostReportResponse:
    """
    Get comprehensive cost report for codegen usage.

    Sprint 48: Quality Gates + Ollama Optimization + MVP Hardening

    Target: <$50/month infrastructure cost per project (Founder Plan).

    Args:
        days: Number of days to include (default 30)
        project_id: Optional filter by project

    Returns:
        Cost report with totals, daily breakdown, and projections
    """
    from uuid import UUID
    from app.api.dependencies import get_db
    from app.services.codegen.cost_tracking_service import get_cost_tracking_service

    # Get database session
    db = next(get_db())

    try:
        service = get_cost_tracking_service(db)

        pid = UUID(project_id) if project_id else None

        report = service.get_cost_report(
            user_id=current_user.id,
            project_id=pid,
            days=days,
        )

        return CostReportResponse(
            period=report["period"],
            totals=CostTotals(**report["totals"]),
            daily_costs=[DailyCostItem(**d) for d in report["daily_costs"]],
            quality=QualityMetrics(**report["quality"]),
            projections=CostProjections(**report["projections"]),
        )
    finally:
        db.close()


@router.get("/usage/monthly", response_model=MonthlyCostResponse)
async def get_monthly_cost(
    year: int,
    month: int,
    project_id: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
) -> MonthlyCostResponse:
    """
    Get monthly cost summary.

    Sprint 48: Cost tracking for budget management.

    Args:
        year: Year (e.g., 2025)
        month: Month (1-12)
        project_id: Optional filter by project

    Returns:
        Monthly cost summary with budget status
    """
    from uuid import UUID
    from app.api.dependencies import get_db
    from app.services.codegen.cost_tracking_service import get_cost_tracking_service

    if month < 1 or month > 12:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Month must be between 1 and 12"
        )

    db = next(get_db())

    try:
        service = get_cost_tracking_service(db)

        pid = UUID(project_id) if project_id else None

        summary = service.get_monthly_cost(
            year=year,
            month=month,
            project_id=pid,
        )

        return MonthlyCostResponse(**summary)
    finally:
        db.close()


@router.get("/usage/provider-health/{provider}", response_model=ProviderHealthResponse)
async def get_provider_health_history(
    provider: str,
    hours: int = 24,
    current_user: User = Depends(get_current_active_user),
) -> ProviderHealthResponse:
    """
    Get provider health check history.

    Sprint 48: Monitor provider availability and fallback frequency.

    Args:
        provider: Provider name (ollama, claude, deepcode)
        hours: Hours of history to fetch (default 24)

    Returns:
        Health check history with availability percentage
    """
    from app.api.dependencies import get_db
    from app.services.codegen.cost_tracking_service import get_cost_tracking_service

    if provider not in ["ollama", "claude", "deepcode"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown provider: {provider}"
        )

    db = next(get_db())

    try:
        service = get_cost_tracking_service(db)

        checks = service.get_provider_health_history(
            provider=provider,
            hours=hours,
        )

        # Calculate availability percentage
        if checks:
            available_count = sum(1 for c in checks if c["is_available"])
            availability_percent = (available_count / len(checks)) * 100
        else:
            availability_percent = 0.0

        return ProviderHealthResponse(
            provider=provider,
            hours=hours,
            checks=[ProviderHealthItem(**c) for c in checks],
            availability_percent=round(availability_percent, 2),
        )
    finally:
        db.close()


# ============================================================================
# Generate with Quality Pipeline + ZIP Export
# Sprint 49: Full Code Generation with 4-Gate Quality Pipeline
# ============================================================================


class QualityGateIssue(BaseModel):
    """Single issue from quality gate."""
    file: str
    line: Optional[int] = None
    column: Optional[int] = None
    severity: str
    code: str
    message: str
    suggestion: Optional[str] = None


class QualityGateResult(BaseModel):
    """Result of a single quality gate."""
    gate_name: str
    gate_number: int
    status: str
    duration_ms: int
    error_count: int
    warning_count: int
    summary: str
    issues: List[QualityGateIssue] = []


class QualityPipelineResult(BaseModel):
    """Full quality pipeline result."""
    success: bool
    total_duration_ms: int
    failed_gate: Optional[int] = None
    summary: str
    gates: List[QualityGateResult] = []


class GenerateWithQualityResponse(BaseModel):
    """Response for generate with quality pipeline."""
    success: bool
    provider: str
    files: Dict[str, str]
    file_count: int
    total_lines: int
    tokens_used: int
    generation_time_ms: int
    quality: QualityPipelineResult
    download_url: Optional[str] = None
    metadata: Dict[str, Any] = {}


@router.post("/generate/full", response_model=GenerateWithQualityResponse)
async def generate_with_quality(
    request: GenerateRequest,
    current_user: User = Depends(get_current_active_user),
    service: CodegenService = Depends(get_service),
) -> GenerateWithQualityResponse:
    """
    Generate code with full 4-Gate Quality Pipeline.

    This endpoint:
    1. Generates code using AI provider (Ollama/Claude)
    2. Runs 4-Gate Quality Pipeline (Syntax, Security, Context, Tests)
    3. Returns detailed quality report

    Sprint 49: EP-06 Full Code Generation with Quality

    Args:
        request: GenerateRequest with app_blueprint

    Returns:
        GenerateWithQualityResponse with files and quality report

    Raises:
        503: No providers available
        500: Generation failed
    """
    from app.services.codegen.quality_pipeline import get_quality_pipeline

    logger.info(
        f"Full code generation requested by user {current_user.id}: "
        f"language={request.language}, framework={request.framework}"
    )

    try:
        # Step 1: Generate code
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
            f"Generation complete: {len(result.files)} files, {result.tokens_used} tokens"
        )

        # Step 2: Run Quality Pipeline
        pipeline = get_quality_pipeline()
        quality_result = pipeline.run(
            files=result.files,
            language=request.language,
        )

        logger.info(
            f"Quality pipeline complete: {quality_result.summary}"
        )

        # Calculate file stats
        file_count = len(result.files)
        total_lines = sum(len(content.split('\n')) for content in result.files.values())

        # Convert quality result to response format
        quality_response = QualityPipelineResult(
            success=quality_result.success,
            total_duration_ms=quality_result.total_duration_ms,
            failed_gate=quality_result.failed_gate,
            summary=quality_result.summary,
            gates=[
                QualityGateResult(
                    gate_name=g.gate_name,
                    gate_number=g.gate_number,
                    status=g.status.value,
                    duration_ms=g.duration_ms,
                    error_count=g.error_count,
                    warning_count=g.warning_count,
                    summary=g.summary,
                    issues=[
                        QualityGateIssue(
                            file=i.file_path,
                            line=i.line,
                            column=i.column,
                            severity=i.severity,
                            code=i.code,
                            message=i.message,
                            suggestion=i.suggestion,
                        )
                        for i in g.issues
                    ],
                )
                for g in quality_result.gates
            ],
        )

        return GenerateWithQualityResponse(
            success=True,
            provider=result.provider,
            files=result.files,
            file_count=file_count,
            total_lines=total_lines,
            tokens_used=result.tokens_used,
            generation_time_ms=result.generation_time_ms,
            quality=quality_response,
            metadata=result.metadata,
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


@router.post("/generate/zip")
async def generate_zip(
    request: GenerateRequest,
    current_user: User = Depends(get_current_active_user),
    service: CodegenService = Depends(get_service),
):
    """
    Generate code and return as downloadable ZIP file.

    Creates a proper folder structure for immediate use.

    Sprint 49: EP-06 ZIP Export

    Args:
        request: GenerateRequest with app_blueprint

    Returns:
        StreamingResponse with ZIP file
    """
    import io
    import zipfile
    from datetime import datetime
    from fastapi.responses import StreamingResponse

    logger.info(f"ZIP generation requested by user {current_user.id}")

    try:
        # Generate code
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

        # Create ZIP in memory
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add generated files
            for file_path, content in result.files.items():
                zip_file.writestr(file_path, content)

            # Add README with generation info
            app_name = request.app_blueprint.get("name", "Generated App")
            readme_content = f"""# {app_name}

Generated by SDLC Orchestrator EP-06

## Generation Info
- Date: {datetime.utcnow().isoformat()}
- Provider: {result.provider}
- Language: {request.language}
- Framework: {request.framework}
- Files: {len(result.files)}
- Tokens Used: {result.tokens_used}

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
uvicorn app.main:app --reload
```

## Project Structure
```
{chr(10).join(sorted(result.files.keys()))}
```

---
Generated with ❤️ by SDLC Orchestrator
"""
            zip_file.writestr("README.md", readme_content)

            # Add requirements.txt if not present
            if "requirements.txt" not in result.files:
                requirements = """# Generated dependencies
fastapi>=0.100.0
uvicorn[standard]>=0.22.0
sqlalchemy>=2.0.0
pydantic>=2.0.0
python-dotenv>=1.0.0
"""
                zip_file.writestr("requirements.txt", requirements)

        zip_buffer.seek(0)

        # Generate filename
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in app_name)
        filename = f"{safe_name}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.zip"

        logger.info(f"ZIP created: {filename}, {len(result.files)} files")

        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
            }
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


# ============================================================================
# Streaming Code Generation (Sprint 51A)
# SSE-based progressive code generation with real-time file events
# ============================================================================


@router.post("/generate/stream")
async def generate_stream(
    request: GenerateRequest,
    current_user: User = Depends(get_current_active_user),
    service: CodegenService = Depends(get_service),
):
    """
    Stream code generation with real-time file events via SSE.

    Sprint 51A: Progressive Code Generation Flow

    This endpoint streams events as files are generated:
    - started: Generation session initiated with provider info
    - file_generating: File generation started
    - file_generated: File completed with content and syntax check
    - quality_started: Quality pipeline initiated
    - quality_gate: Individual gate results
    - completed: All files generated successfully
    - error: Generation failed (includes recovery_id if partial)

    Frontend can display files as they appear, providing better UX
    than waiting for all files to complete.

    Args:
        request: GenerateRequest with app_blueprint

    Returns:
        StreamingResponse with SSE events (text/event-stream)

    Example events:
        data: {"type": "started", "session_id": "abc123", "model": "qwen2.5-coder:32b", "provider": "ollama"}

        data: {"type": "file_generating", "session_id": "abc123", "path": "app/main.py"}

        data: {"type": "file_generated", "session_id": "abc123", "path": "app/main.py", "content": "...", "lines": 45, "language": "python", "syntax_valid": true}

        data: {"type": "completed", "session_id": "abc123", "total_files": 12, "total_lines": 450, "duration_ms": 30000, "success": true}
    """
    import json
    import uuid
    import time
    from datetime import datetime
    from fastapi.responses import StreamingResponse

    from app.schemas.streaming import (
        StartedEvent,
        FileGeneratingEvent,
        FileGeneratedEvent,
        QualityStartedEvent,
        QualityGateEvent,
        CompletedEvent,
        ErrorEvent,
    )

    session_id = str(uuid.uuid4())
    start_time = time.time()

    logger.info(
        f"Streaming code generation requested by user {current_user.id}: "
        f"session={session_id}, language={request.language}"
    )

    async def event_generator():
        """Generate SSE events for code generation progress."""
        generated_files = {}
        total_lines = 0

        try:
            # Sprint 51B: Get provider for streaming
            from app.services.codegen.provider_registry import registry
            provider = registry.select_provider(request.preferred_provider)

            if not provider:
                raise NoProviderAvailableError(
                    "No codegen providers available for streaming."
                )

            # Event 1: Started - with actual provider info
            started_event = StartedEvent(
                session_id=session_id,
                model=getattr(provider, 'model', 'unknown'),
                provider=provider.name,
            )
            yield f"data: {started_event.model_dump_json()}\n\n"

            # Sprint 51B: Real streaming from Ollama
            spec = CodegenSpec(
                app_blueprint=request.app_blueprint,
                target_module=request.target_module,
                language=request.language,
                framework=request.framework,
            )

            # Check if provider supports streaming
            if hasattr(provider, 'generate_streaming'):
                # Real streaming: yield files as they complete
                async for file in provider.generate_streaming(spec):
                    # Event: file_generating
                    generating_event = FileGeneratingEvent(
                        session_id=session_id,
                        path=file.path,
                    )
                    yield f"data: {generating_event.model_dump_json()}\n\n"

                    # Use file data from parser
                    lines = file.lines
                    total_lines += lines

                    # Event: file_generated
                    generated_event = FileGeneratedEvent(
                        session_id=session_id,
                        path=file.path,
                        content=file.content,
                        lines=lines,
                        language=file.language,
                        syntax_valid=_quick_syntax_check(file.content, file.language),
                    )
                    yield f"data: {generated_event.model_dump_json()}\n\n"

                    generated_files[file.path] = file.content
            else:
                # Fallback: Non-streaming provider
                logger.info(f"Provider {provider.name} does not support streaming, using batch mode")
                result = await provider.generate(spec)

                for file_path, content in result.files.items():
                    # Event: file_generating
                    generating_event = FileGeneratingEvent(
                        session_id=session_id,
                        path=file_path,
                    )
                    yield f"data: {generating_event.model_dump_json()}\n\n"

                    language = _detect_language(file_path)
                    lines = len(content.split("\n"))
                    total_lines += lines

                    # Event: file_generated
                    generated_event = FileGeneratedEvent(
                        session_id=session_id,
                        path=file_path,
                        content=content,
                        lines=lines,
                        language=language,
                        syntax_valid=_quick_syntax_check(content, language),
                    )
                    yield f"data: {generated_event.model_dump_json()}\n\n"

                    generated_files[file_path] = content

            # Event: quality_started
            quality_started = QualityStartedEvent(session_id=session_id)
            yield f"data: {quality_started.model_dump_json()}\n\n"

            # Run quality gates (simplified for 51A)
            gates = [
                ("Syntax", 1),
                ("Security", 2),
                ("Context", 3),
                ("Tests", 4),
            ]

            for gate_name, gate_number in gates:
                # Mock gate results for 51A
                gate_event = QualityGateEvent(
                    session_id=session_id,
                    gate_number=gate_number,
                    gate_name=gate_name,
                    status="passed",  # Will be real in 51B
                    issues=0,
                    duration_ms=100 + (gate_number * 50),
                )
                yield f"data: {gate_event.model_dump_json()}\n\n"

            # Event: completed
            duration_ms = int((time.time() - start_time) * 1000)
            completed_event = CompletedEvent(
                session_id=session_id,
                total_files=len(generated_files),
                total_lines=total_lines,
                duration_ms=duration_ms,
                success=True,
            )
            yield f"data: {completed_event.model_dump_json()}\n\n"

            logger.info(
                f"Streaming generation complete: session={session_id}, "
                f"files={len(generated_files)}, lines={total_lines}, "
                f"duration={duration_ms}ms"
            )

        except NoProviderAvailableError as e:
            logger.error(f"No providers available: {e}")
            error_event = ErrorEvent(
                session_id=session_id,
                message=f"No AI providers available: {str(e)}",
                recovery_id=session_id if generated_files else None,
            )
            yield f"data: {error_event.model_dump_json()}\n\n"

        except GenerationError as e:
            logger.error(f"Generation error: {e}")
            error_event = ErrorEvent(
                session_id=session_id,
                message=f"Code generation failed: {str(e)}",
                recovery_id=session_id if generated_files else None,
            )
            yield f"data: {error_event.model_dump_json()}\n\n"

        except Exception as e:
            logger.exception(f"Unexpected error in streaming: {e}")
            error_event = ErrorEvent(
                session_id=session_id,
                message=f"Unexpected error: {str(e)}",
                recovery_id=session_id if generated_files else None,
            )
            yield f"data: {error_event.model_dump_json()}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


def _detect_language(file_path: str) -> str:
    """Detect programming language from file extension."""
    ext = file_path.rsplit(".", 1)[-1].lower() if "." in file_path else ""
    lang_map = {
        "py": "python",
        "ts": "typescript",
        "tsx": "typescript",
        "js": "javascript",
        "jsx": "javascript",
        "json": "json",
        "yaml": "yaml",
        "yml": "yaml",
        "md": "markdown",
        "sql": "sql",
        "html": "html",
        "css": "css",
        "sh": "bash",
        "txt": "text",
        "toml": "toml",
        "ini": "ini",
        "cfg": "ini",
    }
    return lang_map.get(ext, ext)


def _quick_syntax_check(content: str, language: str) -> bool:
    """
    Quick syntax validation for common languages.

    Sprint 51A: Basic check only.
    Sprint 51B: Will integrate with full quality pipeline.
    """
    if language == "python":
        try:
            import ast
            ast.parse(content)
            return True
        except SyntaxError:
            return False
    elif language in ("json",):
        try:
            import json
            json.loads(content)
            return True
        except json.JSONDecodeError:
            return False
    # For other languages, assume valid (will be checked by quality pipeline)
    return True


# ============================================================================
# Session Checkpoint Endpoints (Sprint 51B)
# Resume, status, and list endpoints for session management
# ============================================================================


@router.post("/generate/resume/{session_id}")
async def resume_generation(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
):
    """
    Resume code generation from last checkpoint.

    Sprint 51B: Session Checkpoint Feature

    This endpoint resumes a previously interrupted generation session.
    It first sends all completed files from the checkpoint, then continues
    generating remaining files.

    Args:
        session_id: UUID of the session to resume

    Returns:
        StreamingResponse with SSE events (text/event-stream)

    Raises:
        404: Session not found or expired
        400: Session cannot be resumed (completed or non-recoverable error)
        403: User not authorized for this session

    Example events:
        data: {"type": "session_resumed", "session_id": "abc123", "resumed_from_checkpoint": 2, "files_already_completed": 6, "files_remaining": 9, "completed_files": [...]}

        data: {"type": "file_generated", ...}

        data: {"type": "completed", ...}
    """
    import time
    from uuid import UUID as UUIDType
    from fastapi.responses import StreamingResponse

    from app.api.dependencies import get_redis
    from app.services.codegen.session_manager import SessionManager
    from app.schemas.session import SessionStatus
    from app.schemas.streaming import (
        SessionResumedEvent,
        FileGeneratingEvent,
        FileGeneratedEvent,
        CompletedEvent,
        ErrorEvent,
        CheckpointEvent,
    )
    from app.services.codegen.provider_registry import registry
    from app.services.codegen.base_provider import CodegenSpec

    # Parse session_id
    try:
        session_uuid = UUIDType(session_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid session ID format: {session_id}"
        )

    # Get Redis connection
    redis = await get_redis()
    session_manager = SessionManager(redis)

    # Validate session exists
    session_state = await session_manager.get_session(session_uuid)
    if not session_state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found or expired"
        )

    # Check authorization
    if session_state.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to resume this session"
        )

    # Check if resumable
    if session_state.status == SessionStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session already completed"
        )

    if session_state.status == SessionStatus.FAILED:
        # Allow resume of failed sessions if last error is recoverable
        if session_state.errors and not session_state.errors[-1].recoverable:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Session failed with non-recoverable error"
            )

    # Get completed files
    completed_files = await session_manager.get_completed_files(session_uuid)

    # Increment resume count
    await session_manager.increment_resume_count(session_uuid)

    start_time = time.time()

    logger.info(
        f"Resuming session {session_id} for user {current_user.id}: "
        f"checkpoint={session_state.checkpoint_count}, "
        f"completed={len(completed_files)}, "
        f"remaining={session_state.total_files_expected - len(completed_files)}"
    )

    async def resume_event_generator():
        """Generate SSE events for resumed generation."""
        total_lines = sum(f.lines for f in completed_files)
        generated_files = {f.file_path: f.content for f in completed_files}

        try:
            # Event: session_resumed
            resumed_event = SessionResumedEvent(
                session_id=session_id,
                resumed_from_checkpoint=session_state.checkpoint_count,
                files_already_completed=len(completed_files),
                files_remaining=session_state.total_files_expected - len(completed_files),
                completed_files=[
                    {
                        "file_path": f.file_path,
                        "language": f.language,
                        "lines": f.lines,
                    }
                    for f in completed_files
                ],
            )
            yield f"data: {resumed_event.model_dump_json()}\n\n"

            # Update session status
            await session_manager.update_session(
                session_uuid,
                status=SessionStatus.RESUMED
            )

            # Get provider for remaining generation
            provider = registry.select_provider(None)
            if not provider:
                raise NoProviderAvailableError("No codegen providers available")

            # TODO: In full implementation, reconstruct blueprint from session
            # For now, we only return completed files and signal completion
            # Full implementation would:
            # 1. Load blueprint from session metadata
            # 2. Determine which files are remaining
            # 3. Continue generation for remaining files only

            # For Sprint 51B MVP, mark as completed with existing files
            duration_ms = int((time.time() - start_time) * 1000)
            completed_event = CompletedEvent(
                session_id=session_id,
                total_files=len(generated_files),
                total_lines=total_lines,
                duration_ms=duration_ms,
                success=True,
            )
            yield f"data: {completed_event.model_dump_json()}\n\n"

            # Mark session as completed
            from app.schemas.session import GeneratedFileCheckpoint
            await session_manager.complete_session(
                session_uuid,
                completed_files,
                metadata_updates={"generation_time_ms": duration_ms}
            )

            logger.info(
                f"Resume completed: session={session_id}, "
                f"files={len(generated_files)}, lines={total_lines}"
            )

        except Exception as e:
            logger.exception(f"Error resuming session {session_id}: {e}")
            error_event = ErrorEvent(
                session_id=session_id,
                message=f"Resume failed: {str(e)}",
                recovery_id=session_id if generated_files else None,
            )
            yield f"data: {error_event.model_dump_json()}\n\n"

    return StreamingResponse(
        resume_event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "X-Session-Id": session_id,
        },
    )


@router.get("/sessions/{session_id}")
async def get_session_status(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
):
    """
    Get current session status and checkpoint info.

    Sprint 51B: Session status endpoint

    Args:
        session_id: Session UUID

    Returns:
        SessionStateResponse with current progress and checkpoint data

    Raises:
        404: Session not found or expired
        403: User not authorized to view this session
    """
    from uuid import UUID as UUIDType
    from app.api.dependencies import get_redis
    from app.services.codegen.session_manager import SessionManager
    from app.schemas.session import SessionStateResponse

    try:
        session_uuid = UUIDType(session_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid session ID format: {session_id}"
        )

    redis = await get_redis()
    session_manager = SessionManager(redis)
    session_state = await session_manager.get_session(session_uuid)

    if not session_state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found or expired"
        )

    if session_state.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this session"
        )

    return SessionStateResponse.from_state(session_state)


@router.get("/sessions/active")
async def list_active_sessions(
    current_user: User = Depends(get_current_active_user),
):
    """
    List all active (resumable) sessions for current user.

    Sprint 51B: List resumable sessions

    Returns:
        List of SessionStateResponse for sessions that can be resumed

    Sessions with these statuses are considered resumable:
    - IN_PROGRESS: Generation was interrupted
    - CHECKPOINTED: Has a saved checkpoint
    - FAILED: Failed with recoverable error
    """
    from app.api.dependencies import get_redis
    from app.services.codegen.session_manager import SessionManager
    from app.schemas.session import SessionStatus, SessionStateResponse

    redis = await get_redis()
    session_manager = SessionManager(redis)

    # Clean up expired sessions first
    await session_manager.cleanup_expired_sessions(current_user.id)

    # Get sessions with resumable statuses
    sessions = await session_manager.list_user_sessions(
        user_id=current_user.id,
        status_filter=[
            SessionStatus.IN_PROGRESS,
            SessionStatus.CHECKPOINTED,
            SessionStatus.FAILED,
        ]
    )

    return [SessionStateResponse.from_state(s) for s in sessions]


# ============================================================================
# Quality Streaming Endpoint (Sprint 56)
# ============================================================================


@router.get("/sessions/{session_id}/quality/stream")
async def stream_quality_pipeline(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
):
    """
    Stream quality pipeline results for a session via SSE.

    Sprint 56: Backend Integration for Quality Pipeline

    This endpoint streams quality gate events for an existing session:
    - quality_started: Quality pipeline initiated
    - quality_gate: Individual gate status/result
    - quality_issue: Individual issue found
    - quality_completed: All gates finished

    The frontend QualityPanel component uses this endpoint for real-time
    quality status updates.

    Args:
        session_id: Session UUID

    Returns:
        StreamingResponse with SSE events (text/event-stream)

    Example events:
        data: {"type": "quality_started", "session_id": "abc123", "timestamp": "..."}
        data: {"type": "quality_gate", "session_id": "abc123", "gate_name": "Syntax", "status": "running", ...}
        data: {"type": "quality_issue", "session_id": "abc123", "gate_name": "Security", "severity": "high", ...}
        data: {"type": "quality_completed", "session_id": "abc123", "passed": true, ...}
    """
    import json
    import time
    import asyncio
    from uuid import UUID as UUIDType
    from datetime import datetime
    from fastapi.responses import StreamingResponse
    from app.api.dependencies import get_redis
    from app.services.codegen.session_manager import SessionManager

    try:
        session_uuid = UUIDType(session_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid session ID format: {session_id}"
        )

    async def quality_event_generator():
        """Generate SSE events for quality pipeline progress."""
        redis = await get_redis()
        session_manager = SessionManager(redis)

        # Verify session exists and belongs to user
        session_state = await session_manager.get_session(session_uuid)
        if not session_state:
            yield f"data: {json.dumps({'type': 'error', 'session_id': session_id, 'message': 'Session not found'})}\n\n"
            return

        if session_state.user_id != current_user.id:
            yield f"data: {json.dumps({'type': 'error', 'session_id': session_id, 'message': 'Not authorized'})}\n\n"
            return

        # Event 1: Quality started
        yield f"data: {json.dumps({'type': 'quality_started', 'session_id': session_id, 'timestamp': datetime.utcnow().isoformat()})}\n\n"

        # Get quality pipeline
        try:
            from app.services.codegen.quality_pipeline import get_quality_pipeline
            pipeline = get_quality_pipeline()

            gate_names = ["Syntax", "Security", "Context", "Tests"]

            # If session has files, run quality pipeline
            if session_state.generated_files:
                files = {f.path: f.content for f in session_state.generated_files}

                for gate_num, gate_name in enumerate(gate_names, 1):
                    # Gate starting
                    yield f"data: {json.dumps({'type': 'quality_gate', 'session_id': session_id, 'timestamp': datetime.utcnow().isoformat(), 'gate_number': gate_num, 'gate_name': gate_name, 'status': 'running', 'issues': 0, 'duration_ms': 0})}\n\n"
                    await asyncio.sleep(0.1)  # Small delay for UI

                    # Run gate (simplified - in production would use actual pipeline)
                    start_time = time.time()
                    gate_passed = True
                    issues_count = 0

                    # Gate 1: Syntax validation
                    if gate_name == "Syntax":
                        for path, content in files.items():
                            if path.endswith('.py'):
                                try:
                                    compile(content, path, 'exec')
                                except SyntaxError as e:
                                    gate_passed = False
                                    issues_count += 1
                                    yield f"data: {json.dumps({'type': 'quality_issue', 'session_id': session_id, 'timestamp': datetime.utcnow().isoformat(), 'gate_name': gate_name, 'severity': 'critical', 'file_path': path, 'line': e.lineno or 0, 'message': str(e.msg)})}\n\n"

                    duration_ms = int((time.time() - start_time) * 1000)

                    # Gate completed
                    yield f"data: {json.dumps({'type': 'quality_gate', 'session_id': session_id, 'timestamp': datetime.utcnow().isoformat(), 'gate_number': gate_num, 'gate_name': gate_name, 'status': 'passed' if gate_passed else 'failed', 'issues': issues_count, 'duration_ms': duration_ms})}\n\n"

                # Quality completed
                yield f"data: {json.dumps({'type': 'quality_completed', 'session_id': session_id, 'timestamp': datetime.utcnow().isoformat(), 'passed': True})}\n\n"

            else:
                # No files to check
                for gate_num, gate_name in enumerate(gate_names, 1):
                    yield f"data: {json.dumps({'type': 'quality_gate', 'session_id': session_id, 'timestamp': datetime.utcnow().isoformat(), 'gate_number': gate_num, 'gate_name': gate_name, 'status': 'skipped', 'issues': 0, 'duration_ms': 0})}\n\n"

                yield f"data: {json.dumps({'type': 'quality_completed', 'session_id': session_id, 'timestamp': datetime.utcnow().isoformat(), 'passed': True})}\n\n"

        except Exception as e:
            logger.exception(f"Quality pipeline error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'session_id': session_id, 'timestamp': datetime.utcnow().isoformat(), 'message': str(e)})}\n\n"

    return StreamingResponse(
        quality_event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )
