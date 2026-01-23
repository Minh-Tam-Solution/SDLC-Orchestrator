"""
=========================================================================
Feedback Learning API Routes - EP-11 Feedback Loop Closure
SDLC Orchestrator - Sprint 100 (Feedback Learning Service)

Version: 1.0.0
Date: January 23, 2026
Status: ACTIVE - Sprint 100 Implementation
Authority: Backend Lead + CTO Approved
Reference: docs/02-design/14-Technical-Specs/Feedback-Learning-Service-Design.md

Endpoints:
- /learnings: PR Learning CRUD + extraction
- /hints: Decomposition Hint CRUD + usage tracking
- /aggregations: Learning aggregation + suggestion management
- /webhooks: GitHub webhook handlers for PR events

EP-11 Feedback Loop:
1. POST /learnings/extract → Extract from PR comment
2. GET /learnings → List/filter learnings
3. POST /aggregations → Create monthly aggregation
4. POST /aggregations/{id}/apply → Apply suggestions to hints

Zero Mock Policy: Production-ready FastAPI routes
=========================================================================
"""

from datetime import date, datetime
from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status, Request, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.project import Project
from app.schemas.feedback_learning import (
    FeedbackType,
    Severity,
    LearningStatus,
    HintType,
    HintCategory,
    HintStatus,
    AggregationPeriod,
    AggregationStatus,
    PRLearningCreate,
    PRLearningExtract,
    PRLearningUpdate,
    PRLearningResponse,
    PRLearningListResponse,
    PRLearningStats,
    DecompositionHintCreate,
    DecompositionHintUpdate,
    DecompositionHintResponse,
    DecompositionHintListResponse,
    DecompositionHintStats,
    HintUsageCreate,
    HintUsageFeedback,
    HintUsageResponse,
    LearningAggregationCreate,
    LearningAggregationResponse,
    LearningAggregationListResponse,
    AggregationApplyRequest,
    AggregationRejectRequest,
    LearningFilterParams,
    HintFilterParams,
    BulkLearningStatusUpdate,
    BulkHintStatusUpdate,
    GitHubReviewCommentWebhook,
    GitHubPullRequestWebhook,
)
from app.services.feedback_learning_service import FeedbackLearningService
from app.services.ollama_service import OllamaService

router = APIRouter(prefix="/learnings", tags=["Feedback Learning (EP-11)"])


# ============================================================================
# Dependencies
# ============================================================================


async def get_feedback_learning_service(
    db: AsyncSession = Depends(get_db),
) -> FeedbackLearningService:
    """Get FeedbackLearningService instance."""
    ollama = OllamaService()
    return FeedbackLearningService(db, ollama)


async def verify_project_access(
    project_id: UUID,
    db: AsyncSession,
    user: User,
) -> Project:
    """Verify user has access to the project."""
    from sqlalchemy import select
    from app.models.project import ProjectMember

    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    # Check if user is owner or member
    if project.owner_id != user.id:
        member_result = await db.execute(
            select(ProjectMember).where(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == user.id,
            )
        )
        if not member_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this project",
            )

    return project


# ============================================================================
# PR Learning Endpoints
# ============================================================================


@router.post(
    "/projects/{project_id}/learnings",
    response_model=PRLearningResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a learning manually",
    description="Create a PR learning record manually (not from AI extraction).",
)
async def create_learning(
    project_id: UUID,
    data: PRLearningCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: FeedbackLearningService = Depends(get_feedback_learning_service),
):
    """Create a PR learning manually."""
    await verify_project_access(project_id, db, current_user)

    learning = await service.create_learning_manual(
        project_id=project_id,
        data=data,
        user_id=current_user.id,
    )

    return PRLearningResponse.model_validate(learning.to_dict())


@router.post(
    "/projects/{project_id}/learnings/extract",
    response_model=PRLearningResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Extract learning from PR comment",
    description="Use AI to extract a learning from a PR review comment.",
)
async def extract_learning(
    project_id: UUID,
    data: PRLearningExtract,
    use_ai: bool = Query(True, description="Use AI for extraction"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: FeedbackLearningService = Depends(get_feedback_learning_service),
):
    """Extract a learning from a PR review comment using AI."""
    await verify_project_access(project_id, db, current_user)

    learning = await service.extract_learning_from_comment(
        project_id=project_id,
        comment_data=data,
        use_ai=use_ai,
    )

    return PRLearningResponse.model_validate(learning.to_dict())


@router.get(
    "/projects/{project_id}/learnings",
    response_model=PRLearningListResponse,
    summary="List learnings",
    description="List PR learnings with optional filtering and pagination.",
)
async def list_learnings(
    project_id: UUID,
    feedback_type: Optional[FeedbackType] = None,
    severity: Optional[Severity] = None,
    learning_status: Optional[LearningStatus] = Query(None, alias="status"),
    ai_extracted: Optional[bool] = None,
    applied_to_claude_md: Optional[bool] = None,
    applied_to_decomposition: Optional[bool] = None,
    pr_number: Optional[int] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: FeedbackLearningService = Depends(get_feedback_learning_service),
):
    """List PR learnings with filtering."""
    await verify_project_access(project_id, db, current_user)

    filters = LearningFilterParams(
        feedback_type=feedback_type,
        severity=severity,
        status=learning_status,
        ai_extracted=ai_extracted,
        applied_to_claude_md=applied_to_claude_md,
        applied_to_decomposition=applied_to_decomposition,
        pr_number=pr_number,
        from_date=from_date,
        to_date=to_date,
        search=search,
    )

    learnings, total = await service.list_learnings(
        project_id=project_id,
        filters=filters,
        page=page,
        page_size=page_size,
    )

    return PRLearningListResponse(
        items=[PRLearningResponse.model_validate(l.to_dict()) for l in learnings],
        total=total,
        page=page,
        page_size=page_size,
        has_more=(page * page_size) < total,
    )


@router.get(
    "/projects/{project_id}/learnings/stats",
    response_model=PRLearningStats,
    summary="Get learning statistics",
    description="Get aggregated statistics for PR learnings.",
)
async def get_learning_stats(
    project_id: UUID,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: FeedbackLearningService = Depends(get_feedback_learning_service),
):
    """Get learning statistics."""
    await verify_project_access(project_id, db, current_user)

    return await service.get_learning_stats(
        project_id=project_id,
        from_date=from_date,
        to_date=to_date,
    )


@router.get(
    "/projects/{project_id}/learnings/{learning_id}",
    response_model=PRLearningResponse,
    summary="Get a learning",
    description="Get a specific PR learning by ID.",
)
async def get_learning(
    project_id: UUID,
    learning_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: FeedbackLearningService = Depends(get_feedback_learning_service),
):
    """Get a specific learning."""
    await verify_project_access(project_id, db, current_user)

    learning = await service.get_learning(learning_id)
    if not learning or learning.project_id != project_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Learning not found",
        )

    return PRLearningResponse.model_validate(learning.to_dict())


@router.patch(
    "/projects/{project_id}/learnings/{learning_id}",
    response_model=PRLearningResponse,
    summary="Update a learning",
    description="Update a PR learning record.",
)
async def update_learning(
    project_id: UUID,
    learning_id: UUID,
    data: PRLearningUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: FeedbackLearningService = Depends(get_feedback_learning_service),
):
    """Update a learning."""
    await verify_project_access(project_id, db, current_user)

    learning = await service.update_learning(learning_id, data)
    if not learning:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Learning not found",
        )

    return PRLearningResponse.model_validate(learning.to_dict())


@router.post(
    "/projects/{project_id}/learnings/bulk-status",
    response_model=dict,
    summary="Bulk update learning status",
    description="Update status for multiple learnings at once.",
)
async def bulk_update_learning_status(
    project_id: UUID,
    data: BulkLearningStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: FeedbackLearningService = Depends(get_feedback_learning_service),
):
    """Bulk update learning status."""
    await verify_project_access(project_id, db, current_user)

    updated_count = 0
    for learning_id in data.learning_ids:
        learning = await service.update_learning(
            learning_id,
            PRLearningUpdate(status=data.status),
        )
        if learning:
            updated_count += 1

    return {"updated_count": updated_count, "total_requested": len(data.learning_ids)}


# ============================================================================
# Decomposition Hint Endpoints
# ============================================================================


@router.post(
    "/projects/{project_id}/hints",
    response_model=DecompositionHintResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a hint",
    description="Create a decomposition hint manually.",
)
async def create_hint(
    project_id: UUID,
    data: DecompositionHintCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: FeedbackLearningService = Depends(get_feedback_learning_service),
):
    """Create a decomposition hint."""
    await verify_project_access(project_id, db, current_user)

    hint = await service.create_hint(
        project_id=project_id,
        data=data,
        user_id=current_user.id,
    )

    return DecompositionHintResponse.model_validate(hint.to_dict())


@router.get(
    "/projects/{project_id}/hints",
    response_model=DecompositionHintListResponse,
    summary="List hints",
    description="List decomposition hints with optional filtering.",
)
async def list_hints(
    project_id: UUID,
    hint_type: Optional[HintType] = None,
    category: Optional[HintCategory] = None,
    hint_status: Optional[HintStatus] = Query(None, alias="status"),
    ai_generated: Optional[bool] = None,
    human_verified: Optional[bool] = None,
    min_confidence: Optional[float] = Query(None, ge=0.0, le=1.0),
    min_effectiveness: Optional[float] = Query(None, ge=0.0, le=1.0),
    applies_to: Optional[str] = None,
    language: Optional[str] = None,
    framework: Optional[str] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: FeedbackLearningService = Depends(get_feedback_learning_service),
):
    """List decomposition hints."""
    await verify_project_access(project_id, db, current_user)

    filters = HintFilterParams(
        hint_type=hint_type,
        category=category,
        status=hint_status,
        ai_generated=ai_generated,
        human_verified=human_verified,
        min_confidence=min_confidence,
        min_effectiveness=min_effectiveness,
        applies_to=applies_to,
        language=language,
        framework=framework,
        search=search,
    )

    hints, total = await service.list_hints(
        project_id=project_id,
        filters=filters,
        page=page,
        page_size=page_size,
    )

    return DecompositionHintListResponse(
        items=[DecompositionHintResponse.model_validate(h.to_dict()) for h in hints],
        total=total,
        page=page,
        page_size=page_size,
        has_more=(page * page_size) < total,
    )


@router.get(
    "/projects/{project_id}/hints/active",
    response_model=list[DecompositionHintResponse],
    summary="Get active hints for decomposition",
    description="Get hints relevant for a specific decomposition context.",
)
async def get_active_hints(
    project_id: UUID,
    applies_to: Optional[str] = None,
    language: Optional[str] = None,
    framework: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: FeedbackLearningService = Depends(get_feedback_learning_service),
):
    """Get active hints for decomposition."""
    await verify_project_access(project_id, db, current_user)

    hints = await service.get_active_hints_for_decomposition(
        project_id=project_id,
        applies_to=applies_to,
        language=language,
        framework=framework,
    )

    return [DecompositionHintResponse.model_validate(h.to_dict()) for h in hints]


@router.get(
    "/projects/{project_id}/hints/stats",
    response_model=DecompositionHintStats,
    summary="Get hint statistics",
    description="Get aggregated statistics for decomposition hints.",
)
async def get_hint_stats(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: FeedbackLearningService = Depends(get_feedback_learning_service),
):
    """Get hint statistics."""
    await verify_project_access(project_id, db, current_user)
    return await service.get_hint_stats(project_id)


@router.get(
    "/projects/{project_id}/hints/{hint_id}",
    response_model=DecompositionHintResponse,
    summary="Get a hint",
    description="Get a specific decomposition hint by ID.",
)
async def get_hint(
    project_id: UUID,
    hint_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: FeedbackLearningService = Depends(get_feedback_learning_service),
):
    """Get a specific hint."""
    await verify_project_access(project_id, db, current_user)

    hint = await service.get_hint(hint_id)
    if not hint or hint.project_id != project_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hint not found",
        )

    return DecompositionHintResponse.model_validate(hint.to_dict())


@router.patch(
    "/projects/{project_id}/hints/{hint_id}",
    response_model=DecompositionHintResponse,
    summary="Update a hint",
    description="Update a decomposition hint.",
)
async def update_hint(
    project_id: UUID,
    hint_id: UUID,
    data: DecompositionHintUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: FeedbackLearningService = Depends(get_feedback_learning_service),
):
    """Update a hint."""
    await verify_project_access(project_id, db, current_user)

    hint = await service.update_hint(hint_id, data)
    if not hint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hint not found",
        )

    return DecompositionHintResponse.model_validate(hint.to_dict())


@router.post(
    "/projects/{project_id}/hints/{hint_id}/verify",
    response_model=DecompositionHintResponse,
    summary="Verify a hint",
    description="Mark a hint as verified by a human.",
)
async def verify_hint(
    project_id: UUID,
    hint_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: FeedbackLearningService = Depends(get_feedback_learning_service),
):
    """Verify a hint."""
    await verify_project_access(project_id, db, current_user)

    hint = await service.verify_hint(hint_id, current_user.id)
    if not hint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hint not found",
        )

    return DecompositionHintResponse.model_validate(hint.to_dict())


@router.post(
    "/projects/{project_id}/hints/usage",
    response_model=HintUsageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record hint usage",
    description="Record usage of hints during task decomposition.",
)
async def record_hint_usage(
    project_id: UUID,
    data: HintUsageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: FeedbackLearningService = Depends(get_feedback_learning_service),
):
    """Record hint usage."""
    await verify_project_access(project_id, db, current_user)

    usage = await service.record_hint_usage(
        project_id=project_id,
        data=data,
        user_id=current_user.id,
    )

    return HintUsageResponse.model_validate(usage.to_dict())


@router.post(
    "/projects/{project_id}/hints/usage/{usage_id}/feedback",
    response_model=HintUsageResponse,
    summary="Provide hint usage feedback",
    description="Provide feedback on the outcome of using a hint.",
)
async def provide_hint_feedback(
    project_id: UUID,
    usage_id: UUID,
    data: HintUsageFeedback,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: FeedbackLearningService = Depends(get_feedback_learning_service),
):
    """Provide feedback on hint usage."""
    await verify_project_access(project_id, db, current_user)

    usage = await service.provide_hint_feedback(usage_id, data)
    if not usage:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usage log not found",
        )

    return HintUsageResponse.model_validate(usage.to_dict())


# ============================================================================
# Learning Aggregation Endpoints
# ============================================================================


@router.post(
    "/projects/{project_id}/aggregations",
    response_model=LearningAggregationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create aggregation",
    description="Create and process a learning aggregation for a period.",
)
async def create_aggregation(
    project_id: UUID,
    data: LearningAggregationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: FeedbackLearningService = Depends(get_feedback_learning_service),
):
    """Create a learning aggregation."""
    await verify_project_access(project_id, db, current_user)

    aggregation = await service.create_aggregation(
        project_id=project_id,
        data=data,
    )

    return LearningAggregationResponse.model_validate(aggregation.to_dict())


@router.get(
    "/projects/{project_id}/aggregations",
    response_model=LearningAggregationListResponse,
    summary="List aggregations",
    description="List learning aggregations with pagination.",
)
async def list_aggregations(
    project_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: FeedbackLearningService = Depends(get_feedback_learning_service),
):
    """List learning aggregations."""
    await verify_project_access(project_id, db, current_user)

    aggregations, total = await service.list_aggregations(
        project_id=project_id,
        page=page,
        page_size=page_size,
    )

    return LearningAggregationListResponse(
        items=[
            LearningAggregationResponse.model_validate(a.to_dict())
            for a in aggregations
        ],
        total=total,
        page=page,
        page_size=page_size,
        has_more=(page * page_size) < total,
    )


@router.get(
    "/projects/{project_id}/aggregations/{aggregation_id}",
    response_model=LearningAggregationResponse,
    summary="Get aggregation",
    description="Get a specific learning aggregation.",
)
async def get_aggregation(
    project_id: UUID,
    aggregation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: FeedbackLearningService = Depends(get_feedback_learning_service),
):
    """Get a specific aggregation."""
    await verify_project_access(project_id, db, current_user)

    aggregation = await service.get_aggregation(aggregation_id)
    if not aggregation or aggregation.project_id != project_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aggregation not found",
        )

    return LearningAggregationResponse.model_validate(aggregation.to_dict())


@router.post(
    "/projects/{project_id}/aggregations/{aggregation_id}/apply",
    response_model=LearningAggregationResponse,
    summary="Apply aggregation suggestions",
    description="Apply the suggestions from an aggregation (creates hints, etc.).",
)
async def apply_aggregation(
    project_id: UUID,
    aggregation_id: UUID,
    data: AggregationApplyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: FeedbackLearningService = Depends(get_feedback_learning_service),
):
    """Apply aggregation suggestions."""
    await verify_project_access(project_id, db, current_user)

    aggregation = await service.apply_aggregation(
        aggregation_id=aggregation_id,
        request=data,
        user_id=current_user.id,
    )

    if not aggregation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aggregation not found",
        )

    return LearningAggregationResponse.model_validate(aggregation.to_dict())


@router.post(
    "/projects/{project_id}/aggregations/{aggregation_id}/reject",
    response_model=LearningAggregationResponse,
    summary="Reject aggregation suggestions",
    description="Reject the suggestions from an aggregation.",
)
async def reject_aggregation(
    project_id: UUID,
    aggregation_id: UUID,
    data: AggregationRejectRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: FeedbackLearningService = Depends(get_feedback_learning_service),
):
    """Reject aggregation suggestions."""
    await verify_project_access(project_id, db, current_user)

    aggregation = await service.reject_aggregation(
        aggregation_id=aggregation_id,
        reason=data.reason,
        user_id=current_user.id,
    )

    if not aggregation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aggregation not found",
        )

    return LearningAggregationResponse.model_validate(aggregation.to_dict())


# ============================================================================
# Utility Endpoints
# ============================================================================


@router.post(
    "/projects/{project_id}/generate-hints",
    response_model=dict,
    summary="Generate hints from learnings",
    description="Generate decomposition hints from unapplied learnings (monthly job).",
)
async def generate_hints_from_learnings(
    project_id: UUID,
    since: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: FeedbackLearningService = Depends(get_feedback_learning_service),
):
    """Generate hints from learnings."""
    await verify_project_access(project_id, db, current_user)

    hints_created = await service.generate_hints_from_learnings(
        project_id=project_id,
        since=since,
    )

    return {"hints_created": hints_created}
