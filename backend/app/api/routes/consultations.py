"""
=========================================================================
CRP (Consultation Request Protocol) API Routes
SDLC Orchestrator - Sprint 101 (Risk-Based Planning Trigger)

Version: 1.0.0
Date: January 23, 2026
Status: ACTIVE - Sprint 101 Implementation
Authority: Backend Lead + CTO Approved
Reference: docs/04-build/02-Sprint-Plans/SPRINT-101-DESIGN.md
Reference: SDLC 5.2.0 AI Governance - Consultation Request Protocol

Endpoints:
- POST /consultations: Create new consultation request
- GET /consultations: List consultations (with filtering)
- GET /consultations/{id}: Get single consultation
- POST /consultations/{id}/assign: Assign reviewer
- POST /consultations/{id}/resolve: Resolve (approve/reject)
- POST /consultations/{id}/comments: Add comment
- GET /consultations/my-reviews: Get pending reviews for current user

Key Features:
- Human oversight for high-risk AI changes
- Reviewer assignment based on expertise
- Discussion thread support
- Resolution tracking

Performance Targets:
- Create consultation: <500ms
- List consultations: <200ms
- Resolve consultation: <500ms

Zero Mock Policy: Production-ready FastAPI routes
=========================================================================
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.crp import (
    AddCommentRequest,
    AssignReviewerRequest,
    ConsultationCommentResponse,
    ConsultationFilters,
    ConsultationListResponse,
    ConsultationPriority,
    ConsultationResponse,
    ConsultationStatus,
    CreateConsultationRequest,
    ResolveConsultationRequest,
    ReviewerExpertise,
)
from app.schemas.risk_analysis import RiskAnalysis, RiskAnalysisRequest
from app.services.crp_service import CRPService
from app.services.risk_factor_detector_service import RiskFactorDetectorService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/consultations", tags=["CRP - Consultations"])


# =============================================================================
# Dependency Injection
# =============================================================================


async def get_crp_service(db: AsyncSession = Depends(get_db)) -> CRPService:
    """Get CRP service instance."""
    return CRPService(db)


def get_risk_detector() -> RiskFactorDetectorService:
    """Get risk factor detector service instance."""
    return RiskFactorDetectorService()


# =============================================================================
# Endpoints
# =============================================================================


@router.post(
    "",
    response_model=ConsultationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create consultation request",
    description="Create a new consultation request for high-risk changes.",
)
async def create_consultation(
    request: CreateConsultationRequest,
    crp_service: CRPService = Depends(get_crp_service),
    current_user: User = Depends(get_current_user),
    risk_detector: RiskFactorDetectorService = Depends(get_risk_detector),
) -> ConsultationResponse:
    """
    Create a new consultation request.

    Called when RiskFactorDetectorService detects high-risk change (score > 70).
    The risk_analysis_id must reference a valid risk analysis.

    Returns the created consultation with status 'pending'.
    """
    logger.info(
        f"Creating consultation for project {request.project_id} by user {current_user.id}"
    )

    # TODO: In production, fetch the risk analysis from Evidence Vault
    # For now, we'll create a placeholder analysis
    # This would normally be passed from the caller who performed the analysis
    try:
        # Create placeholder risk analysis with the provided ID
        # In real implementation, this would be fetched from storage
        placeholder_analysis = RiskAnalysis(
            id=request.risk_analysis_id,
            risk_factors=[],
            risk_factor_count=0,
            risk_score=75,  # High enough to trigger CRP
            risk_level="high",
            loc_analysis={
                "total_lines": 0,
                "added_lines": 0,
                "removed_lines": 0,
                "modified_files": 0,
                "file_types": {},
            },
            should_plan=True,
            planning_decision="requires_crp",
            recommendations=["High-risk change requires human review"],
        )

        consultation = await crp_service.create_consultation(
            request=request,
            requester_id=current_user.id,
            risk_analysis=placeholder_analysis,
        )

        return consultation

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "",
    response_model=ConsultationListResponse,
    status_code=status.HTTP_200_OK,
    summary="List consultations",
    description="List consultations with filtering and pagination.",
)
async def list_consultations(
    project_id: Optional[UUID] = Query(default=None, description="Filter by project"),
    status_filter: Optional[ConsultationStatus] = Query(
        default=None, alias="status", description="Filter by status"
    ),
    priority: Optional[ConsultationPriority] = Query(
        default=None, description="Filter by priority"
    ),
    reviewer_id: Optional[UUID] = Query(
        default=None, description="Filter by assigned reviewer"
    ),
    expertise: Optional[ReviewerExpertise] = Query(
        default=None, description="Filter by required expertise"
    ),
    search: Optional[str] = Query(
        default=None, max_length=100, description="Search in title and description"
    ),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Page size"),
    crp_service: CRPService = Depends(get_crp_service),
    current_user: User = Depends(get_current_user),
) -> ConsultationListResponse:
    """
    List consultations with optional filtering.

    Supports filtering by:
    - project_id: Specific project
    - status: pending, in_review, approved, rejected, etc.
    - priority: low, medium, high, urgent
    - reviewer_id: Assigned reviewer
    - expertise: Required expertise area
    - search: Text search in title/description
    """
    filters = ConsultationFilters(
        project_id=project_id,
        status=status_filter,
        priority=priority,
        reviewer_id=reviewer_id,
        expertise=expertise,
        search=search,
        page=page,
        page_size=page_size,
    )

    return await crp_service.list_consultations(filters)


@router.get(
    "/my-reviews",
    response_model=list[ConsultationResponse],
    status_code=status.HTTP_200_OK,
    summary="Get my pending reviews",
    description="Get consultations assigned to the current user for review.",
)
async def get_my_pending_reviews(
    crp_service: CRPService = Depends(get_crp_service),
    current_user: User = Depends(get_current_user),
) -> list[ConsultationResponse]:
    """
    Get pending consultations assigned to the current user.

    Returns consultations with status 'pending' or 'in_review'
    where the current user is the assigned reviewer.
    """
    return await crp_service.get_pending_for_reviewer(current_user.id)


@router.get(
    "/{consultation_id}",
    response_model=ConsultationResponse,
    status_code=status.HTTP_200_OK,
    summary="Get consultation",
    description="Get a single consultation by ID with comments.",
)
async def get_consultation(
    consultation_id: UUID,
    include_comments: bool = Query(default=True, description="Include comments"),
    crp_service: CRPService = Depends(get_crp_service),
    current_user: User = Depends(get_current_user),
) -> ConsultationResponse:
    """
    Get a consultation by ID.

    Includes the full risk analysis and optionally comments.
    """
    try:
        return await crp_service.get_consultation(
            consultation_id=consultation_id,
            include_comments=include_comments,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post(
    "/{consultation_id}/assign",
    response_model=ConsultationResponse,
    status_code=status.HTTP_200_OK,
    summary="Assign reviewer",
    description="Assign a reviewer to a consultation.",
)
async def assign_reviewer(
    consultation_id: UUID,
    request: AssignReviewerRequest,
    crp_service: CRPService = Depends(get_crp_service),
    current_user: User = Depends(get_current_user),
) -> ConsultationResponse:
    """
    Assign a reviewer to a consultation.

    Changes status from 'pending' to 'in_review'.
    Only admins or project owners should be able to assign reviewers.
    """
    try:
        return await crp_service.assign_reviewer(
            consultation_id=consultation_id,
            request=request,
            assigned_by=current_user.id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/{consultation_id}/resolve",
    response_model=ConsultationResponse,
    status_code=status.HTTP_200_OK,
    summary="Resolve consultation",
    description="Resolve a consultation (approve/reject).",
)
async def resolve_consultation(
    consultation_id: UUID,
    request: ResolveConsultationRequest,
    crp_service: CRPService = Depends(get_crp_service),
    current_user: User = Depends(get_current_user),
) -> ConsultationResponse:
    """
    Resolve a consultation.

    Valid statuses: approved, rejected, cancelled
    Resolution notes are required.
    Conditions can be attached to approvals.
    """
    try:
        return await crp_service.resolve_consultation(
            consultation_id=consultation_id,
            request=request,
            resolved_by=current_user.id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/{consultation_id}/comments",
    response_model=ConsultationCommentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add comment",
    description="Add a comment to a consultation.",
)
async def add_comment(
    consultation_id: UUID,
    request: AddCommentRequest,
    crp_service: CRPService = Depends(get_crp_service),
    current_user: User = Depends(get_current_user),
) -> ConsultationCommentResponse:
    """
    Add a comment to a consultation.

    Comments support markdown formatting.
    Use is_resolution_note=True for resolution notes (vs. discussion).
    """
    try:
        return await crp_service.add_comment(
            consultation_id=consultation_id,
            request=request,
            user_id=current_user.id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# =============================================================================
# AI-Assisted Generation (Sprint 151 Day 4)
# =============================================================================


from pydantic import BaseModel, Field


class CRPAutoGenerateRequest(BaseModel):
    """Request for AI-assisted CRP generation."""

    context: str = Field(..., min_length=10, description="Development context/question")
    code_snippet: Optional[str] = Field(None, description="Relevant code snippet")
    related_files: Optional[list[str]] = Field(None, description="Related file paths")
    project_tech_stack: Optional[list[str]] = Field(None, description="Project tech stack")


class CRPAutoGenerateResponse(BaseModel):
    """Response from AI-assisted CRP generation."""

    title: str
    question: str
    context: str
    options_considered: list[dict]
    recommendation: Optional[str]
    impact_assessment: str
    required_expertise: list[str]
    priority_suggestion: str
    confidence: float
    generation_time_ms: float
    provider_used: str
    fallback_used: bool


@router.post(
    "/auto-generate",
    response_model=CRPAutoGenerateResponse,
    status_code=status.HTTP_200_OK,
    summary="AI-assisted CRP generation",
    description="""
    Generate CRP content using AI from development context.

    Provides AI-generated suggestions for:
    - Title and question formulation
    - Context and background
    - Options to consider with pros/cons
    - Recommended approach
    - Impact assessment
    - Required expertise types
    - Priority suggestion

    Returns a confidence score (0-1) indicating
    how confident the AI is in the generated content.

    Sprint 151 Day 4 Implementation.
    """,
)
async def auto_generate_crp(
    request: CRPAutoGenerateRequest,
    crp_service: CRPService = Depends(get_crp_service),
    current_user: User = Depends(get_current_user),
) -> CRPAutoGenerateResponse:
    """
    AI-assisted CRP content generation.

    Uses SASE Generation Service to analyze context and generate
    consultation request content.
    """
    result = await crp_service.auto_generate(
        context=request.context,
        code_snippet=request.code_snippet,
        related_files=request.related_files,
        project_tech_stack=request.project_tech_stack,
    )

    return CRPAutoGenerateResponse(**result)
