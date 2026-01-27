"""
=========================================================================
Auto-Generation API Routes - Compliance Artifact Generation
SDLC Orchestrator - Sprint 108 (Governance Foundation)

Version: 1.0.0
Date: January 27, 2026
Status: ACTIVE - Sprint 108 Day 2
Authority: CTO + Backend Lead Approved
Framework: SDLC 5.3.0 Quality Assurance System

Endpoints:
- POST /auto-generate/intent - Generate intent document
- POST /auto-generate/ownership - Suggest file ownership
- POST /auto-generate/context - Attach context to PR
- POST /auto-generate/attestation - Generate AI attestation
- POST /auto-generate/all - Generate all artifacts for PR
- GET /auto-generate/health - Health check

CORE PRINCIPLE:
  "GOVERNANCE MUST BE THE FASTEST WAY"
  Target: <5 minutes per PR (80% faster than 30 min baseline)

Zero Mock Policy: Real implementations with Ollama integration
=========================================================================
"""

import logging
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.api.dependencies import get_current_user, get_db
from app.models.user import User
from app.services.governance.auto_generator import (
    AutoGenerationService,
    TaskContext,
    FileContext,
    PRContext,
    AISessionContext,
    GenerationResult,
    FallbackLevel,
    get_auto_generation_service,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auto-generate", tags=["Auto-Generation"])


# ============================================================================
# Request/Response Models
# ============================================================================


class GenerateIntentRequest(BaseModel):
    """Request to generate intent document."""

    task_id: str = Field(..., description="Task identifier (e.g., TASK-123)")
    title: str = Field(..., description="Task title", max_length=200)
    description: str = Field(..., description="Task description", max_length=2000)
    acceptance_criteria: Optional[str] = Field(
        None, description="Task acceptance criteria", max_length=1000
    )
    project_name: Optional[str] = Field(None, description="Project name")
    assignee: Optional[str] = Field(None, description="Task assignee")

    model_config = {
        "json_schema_extra": {
            "example": {
                "task_id": "TASK-1234",
                "title": "Add user profile caching",
                "description": "Implement Redis caching for user profile API to reduce latency from 850ms to <100ms p95",
                "acceptance_criteria": "- p95 latency <100ms\n- Cache hit rate >90%\n- TTL 15 minutes",
                "project_name": "SDLC Orchestrator",
                "assignee": "backend-lead",
            }
        }
    }


class SuggestOwnershipRequest(BaseModel):
    """Request to suggest file ownership."""

    file_path: str = Field(..., description="File path relative to repository root")
    repository_path: Optional[str] = Field(
        ".", description="Path to repository root"
    )
    is_new_file: bool = Field(False, description="Whether this is a new file")
    task_creator: Optional[str] = Field(
        None, description="Username of task creator"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "file_path": "backend/app/services/governance/auto_generator.py",
                "repository_path": ".",
                "is_new_file": True,
                "task_creator": "backend-lead",
            }
        }
    }


class AttachContextRequest(BaseModel):
    """Request to attach context to PR."""

    pr_number: int = Field(..., description="Pull request number")
    pr_title: str = Field(..., description="Pull request title", max_length=200)
    pr_description: str = Field(
        "", description="Pull request description", max_length=5000
    )
    changed_files: list[str] = Field(
        default_factory=list, description="List of changed file paths"
    )
    repository_path: Optional[str] = Field(
        ".", description="Path to repository root"
    )
    author: Optional[str] = Field(None, description="PR author username")

    model_config = {
        "json_schema_extra": {
            "example": {
                "pr_number": 123,
                "pr_title": "feat: Add auto-generation service",
                "pr_description": "Implements 4 generators for compliance artifacts",
                "changed_files": [
                    "backend/app/services/governance/auto_generator.py",
                    "backend/app/api/routes/auto_generation.py",
                ],
                "repository_path": ".",
                "author": "backend-lead",
            }
        }
    }


class GenerateAttestationRequest(BaseModel):
    """Request to generate AI attestation template."""

    pr_number: int = Field(..., description="Pull request number")
    pr_title: str = Field(..., description="Pull request title")
    pr_author: Optional[str] = Field(None, description="PR author username")
    session_id: str = Field(..., description="AI session identifier")
    provider: str = Field(..., description="AI provider name")
    model: str = Field(..., description="AI model name")
    generated_lines: int = Field(..., ge=0, description="Number of AI-generated lines")
    timestamp: datetime = Field(..., description="When code was generated")
    prompts: list[str] = Field(
        default_factory=list, description="List of prompts used"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "pr_number": 123,
                "pr_title": "feat: Add auto-generation service",
                "pr_author": "backend-lead",
                "session_id": "sess_abc123xyz",
                "provider": "Claude",
                "model": "claude-sonnet-4-5-20250929",
                "generated_lines": 450,
                "timestamp": "2026-01-27T10:30:00Z",
                "prompts": ["Create an auto-generation service with 4 generators..."],
            }
        }
    }


class GenerateAllRequest(BaseModel):
    """Request to generate all compliance artifacts for a PR."""

    pr_number: int = Field(..., description="Pull request number")
    pr_title: str = Field(..., description="Pull request title")
    pr_description: str = Field("", description="Pull request description")
    changed_files: list[str] = Field(
        default_factory=list, description="List of changed file paths"
    )
    repository_path: Optional[str] = Field(".", description="Repository path")
    author: Optional[str] = Field(None, description="PR author")

    # Optional task context
    task_id: Optional[str] = Field(None, description="Task identifier")
    task_title: Optional[str] = Field(None, description="Task title")
    task_description: Optional[str] = Field(None, description="Task description")

    # Optional AI session context
    ai_session_id: Optional[str] = Field(None, description="AI session ID")
    ai_provider: Optional[str] = Field(None, description="AI provider")
    ai_model: Optional[str] = Field(None, description="AI model")
    ai_generated_lines: Optional[int] = Field(None, description="AI-generated lines")

    model_config = {
        "json_schema_extra": {
            "example": {
                "pr_number": 123,
                "pr_title": "feat: Add auto-generation service",
                "pr_description": "Implements compliance artifact generators",
                "changed_files": [
                    "backend/app/services/governance/auto_generator.py"
                ],
                "task_id": "TASK-1234",
                "task_title": "Add auto-generation service",
                "task_description": "Create 4 generators for compliance artifacts",
            }
        }
    }


class GenerationResultResponse(BaseModel):
    """Response for generation result."""

    success: bool = Field(..., description="Whether generation completed")
    fallback_level: str = Field(
        ..., description="Which fallback level was used (llm, template, minimal)"
    )
    content: str = Field(..., description="Generated content")
    confidence: int = Field(..., ge=0, le=100, description="Confidence score 0-100")
    latency_ms: float = Field(..., description="Generation time in milliseconds")
    generator_type: str = Field(..., description="Type of generator used")
    ui_badge: dict[str, str] = Field(
        ..., description="UI badge with color and text"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )
    error: Optional[str] = Field(None, description="Error message if failed")


class OwnershipResultResponse(GenerationResultResponse):
    """Response for ownership suggestion."""

    owner: Optional[str] = Field(None, description="Suggested owner")
    module: Optional[str] = Field(None, description="Detected module")
    source: Optional[str] = Field(
        None, description="Source of suggestion (CODEOWNERS, git_blame, etc)"
    )


class ContextResultResponse(GenerationResultResponse):
    """Response for context attachment."""

    adrs_found: int = Field(0, description="Number of ADRs found")
    specs_found: int = Field(0, description="Number of specs found")
    modules_detected: list[str] = Field(
        default_factory=list, description="Detected modules"
    )


class AttestationResultResponse(GenerationResultResponse):
    """Response for attestation generation."""

    min_review_time_minutes: float = Field(
        ..., description="Minimum review time required"
    )
    prompt_hash: str = Field(..., description="Hash of prompts for audit")


class GenerateAllResponse(BaseModel):
    """Response for generate all operation."""

    context: ContextResultResponse
    intent: Optional[GenerationResultResponse] = None
    ownership: list[OwnershipResultResponse] = Field(default_factory=list)
    attestation: Optional[AttestationResultResponse] = None
    total_latency_ms: float
    all_successful: bool


class HealthResponse(BaseModel):
    """Health check response."""

    service: str
    healthy: bool
    ollama_available: bool
    ollama_models: list[str]
    generators: dict[str, str]
    fail_safe_enabled: bool
    target_latency: str


# ============================================================================
# Helper Functions
# ============================================================================


def result_to_response(result: GenerationResult) -> GenerationResultResponse:
    """Convert GenerationResult to API response."""
    return GenerationResultResponse(
        success=result.success,
        fallback_level=result.fallback_level.value,
        content=result.content,
        confidence=result.confidence,
        latency_ms=result.latency_ms,
        generator_type=result.generator_type.value,
        ui_badge=result.ui_badge,
        metadata=result.metadata,
        error=result.error,
    )


# ============================================================================
# API Endpoints
# ============================================================================


@router.post(
    "/intent",
    response_model=GenerationResultResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate Intent Document",
    description="""
Generate an intent document from task description.

Uses 3-level fallback:
1. LLM (Ollama qwen3:32b) - Best quality (~10s)
2. Template - Deterministic (~1s)
3. Minimal - Basic structure (~0.5s)

Time saved: ~15 minutes per task
""",
)
async def generate_intent(
    request: GenerateIntentRequest,
    current_user: User = Depends(get_current_user),
) -> GenerationResultResponse:
    """Generate intent document for a task."""
    logger.info(
        f"Generate intent request: task_id={request.task_id}, user={current_user.id}"
    )

    service = get_auto_generation_service()

    task = TaskContext(
        task_id=request.task_id,
        title=request.title,
        description=request.description,
        acceptance_criteria=request.acceptance_criteria,
        project_name=request.project_name,
        assignee=request.assignee,
    )

    result = await service.generate_intent(task)

    return result_to_response(result)


@router.post(
    "/ownership",
    response_model=OwnershipResultResponse,
    status_code=status.HTTP_200_OK,
    summary="Suggest File Ownership",
    description="""
Suggest ownership for a file based on multiple sources.

Algorithm (priority order):
1. CODEOWNERS file (confidence: 1.0)
2. Directory patterns (confidence: 0.9)
3. Git blame (confidence: 0.7)
4. Task creator (confidence: 0.5)
5. Extension fallback (confidence: 0.3)

Time saved: ~2 minutes per file
""",
)
async def suggest_ownership(
    request: SuggestOwnershipRequest,
    current_user: User = Depends(get_current_user),
) -> OwnershipResultResponse:
    """Suggest ownership for a file."""
    logger.info(
        f"Suggest ownership request: file={request.file_path}, user={current_user.id}"
    )

    service = get_auto_generation_service()

    from pathlib import Path

    ext = Path(request.file_path).suffix

    file = FileContext(
        file_path=request.file_path,
        repository_path=request.repository_path or ".",
        file_extension=ext,
        is_new_file=request.is_new_file,
        task_creator=request.task_creator,
    )

    result = await service.suggest_ownership(file)

    return OwnershipResultResponse(
        success=result.success,
        fallback_level=result.fallback_level.value,
        content=result.content,
        confidence=result.confidence,
        latency_ms=result.latency_ms,
        generator_type=result.generator_type.value,
        ui_badge=result.ui_badge,
        metadata=result.metadata,
        error=result.error,
        owner=result.metadata.get("owner"),
        module=result.metadata.get("module"),
        source=result.metadata.get("source"),
    )


@router.post(
    "/context",
    response_model=ContextResultResponse,
    status_code=status.HTTP_200_OK,
    summary="Attach Context to PR",
    description="""
Auto-attach ADRs, specs, and design docs to PR description.

Algorithm:
1. Extract modules from changed files
2. Find ADRs mentioning those modules
3. Find specs in related directories
4. Format context section for PR

Time saved: ~5 minutes per PR
""",
)
async def attach_context(
    request: AttachContextRequest,
    current_user: User = Depends(get_current_user),
) -> ContextResultResponse:
    """Attach context (ADRs, specs) to PR."""
    logger.info(
        f"Attach context request: pr={request.pr_number}, user={current_user.id}"
    )

    service = get_auto_generation_service()

    pr = PRContext(
        pr_number=request.pr_number,
        pr_title=request.pr_title,
        pr_description=request.pr_description,
        changed_files=request.changed_files,
        repository_path=request.repository_path or ".",
        author=request.author,
    )

    result = await service.attach_context(pr)

    return ContextResultResponse(
        success=result.success,
        fallback_level=result.fallback_level.value,
        content=result.content,
        confidence=result.confidence,
        latency_ms=result.latency_ms,
        generator_type=result.generator_type.value,
        ui_badge=result.ui_badge,
        metadata=result.metadata,
        error=result.error,
        adrs_found=result.metadata.get("adrs_found", 0),
        specs_found=result.metadata.get("specs_found", 0),
        modules_detected=result.metadata.get("modules", []),
    )


@router.post(
    "/attestation",
    response_model=AttestationResultResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate AI Attestation",
    description="""
Generate attestation template for AI-generated code.

Auto-fills 80%:
- AI provider, model, session ID
- Prompt hash, generated lines, timestamp

Developer confirms 20%:
- Review time (minimum 2 sec/line)
- Modifications made
- Understanding confirmation

Time saved: ~8 minutes per AI session
""",
)
async def generate_attestation(
    request: GenerateAttestationRequest,
    current_user: User = Depends(get_current_user),
) -> AttestationResultResponse:
    """Generate attestation template for AI-generated code."""
    logger.info(
        f"Generate attestation request: pr={request.pr_number}, user={current_user.id}"
    )

    service = get_auto_generation_service()

    pr = PRContext(
        pr_number=request.pr_number,
        pr_title=request.pr_title,
        pr_description="",
        changed_files=[],
        repository_path=".",
        author=request.pr_author,
    )

    ai_session = AISessionContext(
        session_id=request.session_id,
        provider=request.provider,
        model=request.model,
        generated_lines=request.generated_lines,
        timestamp=request.timestamp,
        prompts=request.prompts,
    )

    result = await service.generate_attestation(pr, ai_session)

    return AttestationResultResponse(
        success=result.success,
        fallback_level=result.fallback_level.value,
        content=result.content,
        confidence=result.confidence,
        latency_ms=result.latency_ms,
        generator_type=result.generator_type.value,
        ui_badge=result.ui_badge,
        metadata=result.metadata,
        error=result.error,
        min_review_time_minutes=result.metadata.get("min_review_time_minutes", 0),
        prompt_hash=result.metadata.get("prompt_hash", ""),
    )


@router.post(
    "/all",
    response_model=GenerateAllResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate All Compliance Artifacts",
    description="""
Generate all applicable compliance artifacts for a PR.

Generates:
- Context attachment (always)
- Intent document (if task provided)
- Ownership suggestions (for changed files)
- Attestation template (if AI session provided)

Combined time saved: ~30 minutes per PR
""",
)
async def generate_all(
    request: GenerateAllRequest,
    current_user: User = Depends(get_current_user),
) -> GenerateAllResponse:
    """Generate all compliance artifacts for a PR."""
    logger.info(
        f"Generate all request: pr={request.pr_number}, user={current_user.id}"
    )

    import time

    start_time = time.time()

    service = get_auto_generation_service()

    # Build PR context
    pr = PRContext(
        pr_number=request.pr_number,
        pr_title=request.pr_title,
        pr_description=request.pr_description,
        changed_files=request.changed_files,
        repository_path=request.repository_path or ".",
        author=request.author,
    )

    # Build optional task context
    task = None
    if request.task_id and request.task_title:
        task = TaskContext(
            task_id=request.task_id,
            title=request.task_title,
            description=request.task_description or "",
        )

    # Build optional AI session context
    ai_session = None
    if request.ai_session_id and request.ai_provider:
        ai_session = AISessionContext(
            session_id=request.ai_session_id,
            provider=request.ai_provider,
            model=request.ai_model or "unknown",
            generated_lines=request.ai_generated_lines or 0,
            timestamp=datetime.now(timezone.utc),
            prompts=[],
        )

    # Generate all
    results = await service.generate_all_for_pr(pr, task, ai_session)

    total_latency = (time.time() - start_time) * 1000

    # Build context response
    context_result = results["context"]
    context_response = ContextResultResponse(
        success=context_result.success,
        fallback_level=context_result.fallback_level.value,
        content=context_result.content,
        confidence=context_result.confidence,
        latency_ms=context_result.latency_ms,
        generator_type=context_result.generator_type.value,
        ui_badge=context_result.ui_badge,
        metadata=context_result.metadata,
        error=context_result.error,
        adrs_found=context_result.metadata.get("adrs_found", 0),
        specs_found=context_result.metadata.get("specs_found", 0),
        modules_detected=context_result.metadata.get("modules", []),
    )

    # Build optional intent response
    intent_response = None
    if "intent" in results:
        intent_result = results["intent"]
        intent_response = result_to_response(intent_result)

    # Build ownership responses
    ownership_responses = []
    if "ownership" in results:
        for ownership_result in results["ownership"]:
            ownership_responses.append(
                OwnershipResultResponse(
                    success=ownership_result.success,
                    fallback_level=ownership_result.fallback_level.value,
                    content=ownership_result.content,
                    confidence=ownership_result.confidence,
                    latency_ms=ownership_result.latency_ms,
                    generator_type=ownership_result.generator_type.value,
                    ui_badge=ownership_result.ui_badge,
                    metadata=ownership_result.metadata,
                    error=ownership_result.error,
                    owner=ownership_result.metadata.get("owner"),
                    module=ownership_result.metadata.get("module"),
                    source=ownership_result.metadata.get("source"),
                )
            )

    # Build optional attestation response
    attestation_response = None
    if "attestation" in results:
        attestation_result = results["attestation"]
        attestation_response = AttestationResultResponse(
            success=attestation_result.success,
            fallback_level=attestation_result.fallback_level.value,
            content=attestation_result.content,
            confidence=attestation_result.confidence,
            latency_ms=attestation_result.latency_ms,
            generator_type=attestation_result.generator_type.value,
            ui_badge=attestation_result.ui_badge,
            metadata=attestation_result.metadata,
            error=attestation_result.error,
            min_review_time_minutes=attestation_result.metadata.get(
                "min_review_time_minutes", 0
            ),
            prompt_hash=attestation_result.metadata.get("prompt_hash", ""),
        )

    # Check if all successful
    all_successful = context_result.success
    if intent_response:
        all_successful = all_successful and intent_response.success
    if ownership_responses:
        all_successful = all_successful and all(r.success for r in ownership_responses)
    if attestation_response:
        all_successful = all_successful and attestation_response.success

    return GenerateAllResponse(
        context=context_response,
        intent=intent_response,
        ownership=ownership_responses,
        attestation=attestation_response,
        total_latency_ms=total_latency,
        all_successful=all_successful,
    )


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Auto-Generation Health Check",
    description="Check health of auto-generation service including Ollama status.",
)
async def health_check() -> HealthResponse:
    """Check health of auto-generation service."""
    service = get_auto_generation_service()
    health = service.health_check()

    return HealthResponse(
        service=health["service"],
        healthy=health["healthy"],
        ollama_available=health["ollama_available"],
        ollama_models=health["ollama_models"],
        generators=health["generators"],
        fail_safe_enabled=health["fail_safe_enabled"],
        target_latency=health["target_latency"],
    )
