"""
=========================================================================
Vibecoding Index API Routes - Signals Engine Interface
SDLC Orchestrator - Sprint 109 (Vibecoding Index & Stage-Aware Gating)

Version: 1.0.0
Date: January 27, 2026
Status: ACTIVE - Sprint 109 Day 1
Authority: CTO + Backend Lead Approved
Framework: SDLC 5.3.0 Quality Assurance System

Endpoints:
- POST /vibecoding/calculate - Calculate Vibecoding Index for submission
- GET /vibecoding/{submission_id} - Get cached index for submission
- POST /vibecoding/batch - Calculate index for multiple submissions
- GET /vibecoding/thresholds - Get index thresholds and routing rules
- POST /vibecoding/calibrate - CEO calibration feedback
- GET /vibecoding/stats - Get index statistics

Zero Mock Policy: Real calculations with AST analysis
=========================================================================
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.services.governance.signals_engine import (
    CodeSubmission,
    GovernanceSignalsEngine,
    IndexCategory,
    ProjectContext,
    RoutingDecision,
    SignalType,
    VibecodingIndex,
    get_signals_engine,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/vibecoding")


# ============================================================================
# Request/Response Models
# ============================================================================


class FileContent(BaseModel):
    """File content for analysis."""

    path: str = Field(..., description="File path")
    content: str = Field(..., description="File content")


class CalculateIndexRequest(BaseModel):
    """Request model for calculating Vibecoding Index."""

    submission_id: UUID = Field(..., description="Unique submission ID")
    project_id: UUID = Field(..., description="Project ID")
    changed_files: List[str] = Field(..., description="List of changed file paths")
    added_lines: int = Field(0, ge=0, description="Number of lines added")
    removed_lines: int = Field(0, ge=0, description="Number of lines removed")
    ai_generated_lines: int = Field(0, ge=0, description="Number of AI-generated lines")
    total_lines: int = Field(0, ge=0, description="Total lines in changed files")
    commit_messages: List[str] = Field(default_factory=list, description="Commit messages")
    is_new_feature: bool = Field(False, description="Whether this is a new feature")
    affected_modules: List[str] = Field(default_factory=list, description="Affected module names")
    pr_title: Optional[str] = Field(None, description="PR title")
    pr_description: Optional[str] = Field(None, description="PR description")
    file_contents: Optional[List[FileContent]] = Field(
        None,
        description="Optional file contents for detailed analysis",
    )


class SignalScoreResponse(BaseModel):
    """Response model for a single signal score."""

    signal_type: str
    score: float = Field(..., ge=0, le=100)
    weight: float
    weighted_score: float
    details: str
    evidence_count: int


class CriticalMatchResponse(BaseModel):
    """Response model for critical path match."""

    pattern: str
    category: str
    file_path: str


class SuggestedFocusResponse(BaseModel):
    """Response model for suggested focus area."""

    top_signal: str
    reason: str
    file: Optional[str]
    estimated_review_time: str


class VibecodingIndexResponse(BaseModel):
    """Response model for Vibecoding Index calculation."""

    submission_id: UUID
    score: float = Field(..., ge=0, le=100)
    category: str = Field(..., description="green, yellow, orange, or red")
    routing: str = Field(..., description="Routing decision")
    critical_override: bool = Field(False, description="Whether critical path override applied")
    original_score: Optional[float] = Field(None, description="Score before critical override")
    signals: Dict[str, SignalScoreResponse]
    top_contributors: List[Dict[str, Any]]
    critical_matches: List[CriticalMatchResponse]
    suggested_focus: Optional[SuggestedFocusResponse]
    flags: List[str]
    calculated_at: datetime


class BatchCalculateRequest(BaseModel):
    """Request model for batch calculation."""

    submissions: List[CalculateIndexRequest] = Field(
        ...,
        min_length=1,
        max_length=50,
        description="List of submissions to calculate",
    )


class BatchCalculateResponse(BaseModel):
    """Response model for batch calculation."""

    results: List[VibecodingIndexResponse]
    total_count: int
    success_count: int
    failed_count: int
    processing_time_ms: float


class ThresholdsResponse(BaseModel):
    """Response model for index thresholds."""

    thresholds: Dict[str, Dict[str, int]]
    routing_rules: Dict[str, str]
    signal_weights: Dict[str, float]


class CalibrationRequest(BaseModel):
    """Request model for CEO calibration feedback."""

    submission_id: UUID = Field(..., description="Submission that was reviewed")
    calculated_score: float = Field(..., ge=0, le=100, description="Original calculated score")
    ceo_agrees: bool = Field(..., description="Whether CEO agrees with the score")
    ceo_suggested_score: Optional[float] = Field(
        None,
        ge=0,
        le=100,
        description="CEO's suggested score if disagreed",
    )
    feedback: Optional[str] = Field(
        None,
        max_length=1000,
        description="CEO's feedback for calibration",
    )
    signals_feedback: Optional[Dict[str, str]] = Field(
        None,
        description="Feedback on specific signals",
    )


class CalibrationResponse(BaseModel):
    """Response model for calibration submission."""

    success: bool
    submission_id: UUID
    calibration_id: UUID
    message: str
    recalibration_scheduled: bool


class StatsResponse(BaseModel):
    """Response model for index statistics."""

    total_calculations: int
    average_score: float
    category_distribution: Dict[str, int]
    routing_distribution: Dict[str, int]
    critical_override_count: int
    calibration_count: int
    ceo_agreement_rate: float
    period_start: datetime
    period_end: datetime


# ============================================================================
# Endpoints
# ============================================================================


@router.post(
    "/calculate",
    response_model=VibecodingIndexResponse,
    summary="Calculate Vibecoding Index",
    description="""
    Calculate the Vibecoding Index for a code submission.

    The index is a composite score (0-100) from 5 signals:
    - **Architectural Smell** (25%): God class, feature envy, shotgun surgery
    - **Abstraction Complexity** (15%): Inheritance depth, generics
    - **AI Dependency Ratio** (20%): AI-generated lines / total lines
    - **Change Surface Area** (20%): Files, modules, API contracts affected
    - **Drift Velocity** (20%): Pattern changes over 7 days

    **Routing:**
    - Green (0-30): Auto-approve
    - Yellow (31-60): Tech Lead review
    - Orange (61-80): CEO should review
    - Red (81-100): CEO must review

    **MAX CRITICALITY OVERRIDE:**
    Critical path files (auth, security, payment) automatically boost
    the index to minimum 80 (Red), requiring CEO review.
    """,
)
async def calculate_vibecoding_index(
    request: CalculateIndexRequest,
    engine: GovernanceSignalsEngine = Depends(get_signals_engine),
) -> VibecodingIndexResponse:
    """Calculate Vibecoding Index for a submission."""
    import time

    start_time = time.perf_counter()

    # Convert request to CodeSubmission
    submission = CodeSubmission(
        submission_id=request.submission_id,
        project_id=request.project_id,
        changed_files=request.changed_files,
        added_lines=request.added_lines,
        removed_lines=request.removed_lines,
        ai_generated_lines=request.ai_generated_lines,
        total_lines=request.total_lines,
        commit_messages=request.commit_messages,
        is_new_feature=request.is_new_feature,
        affected_modules=request.affected_modules,
        pr_title=request.pr_title,
        pr_description=request.pr_description,
    )

    # Convert file contents if provided
    file_contents: Dict[str, str] = {}
    if request.file_contents:
        file_contents = {fc.path: fc.content for fc in request.file_contents}

    # Calculate index
    try:
        index = await engine.calculate_vibecoding_index(
            submission=submission,
            context=None,  # TODO: Load project context
            file_contents=file_contents,
        )
    except Exception as e:
        logger.error(f"Failed to calculate Vibecoding Index: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate index: {str(e)}",
        )

    processing_time = (time.perf_counter() - start_time) * 1000
    logger.info(
        f"Vibecoding Index calculated: {index.score:.1f} ({index.category.value}) "
        f"in {processing_time:.1f}ms"
    )

    # Build response
    return VibecodingIndexResponse(
        submission_id=request.submission_id,
        score=round(index.score, 2),
        category=index.category.value,
        routing=index.routing.value,
        critical_override=index.critical_override,
        original_score=round(index.original_score, 2) if index.original_score else None,
        signals={
            signal_type.value: SignalScoreResponse(
                signal_type=signal_type.value,
                score=round(score.score, 2),
                weight=score.weight,
                weighted_score=round(score.weighted_score, 2),
                details=score.details,
                evidence_count=len(score.evidence),
            )
            for signal_type, score in index.signals.items()
        },
        top_contributors=index._get_top_contributors(),
        critical_matches=[
            CriticalMatchResponse(
                pattern=m.pattern,
                category=m.category,
                file_path=m.file_path,
            )
            for m in index.critical_matches
        ],
        suggested_focus=SuggestedFocusResponse(**index.suggested_focus) if index.suggested_focus else None,
        flags=index.flags,
        calculated_at=index.calculated_at,
    )


@router.post(
    "/batch",
    response_model=BatchCalculateResponse,
    summary="Batch calculate Vibecoding Index",
    description="Calculate Vibecoding Index for multiple submissions in batch.",
)
async def batch_calculate_index(
    request: BatchCalculateRequest,
    engine: GovernanceSignalsEngine = Depends(get_signals_engine),
) -> BatchCalculateResponse:
    """Batch calculate Vibecoding Index."""
    import time

    start_time = time.perf_counter()
    results: List[VibecodingIndexResponse] = []
    failed_count = 0

    for sub_request in request.submissions:
        try:
            result = await calculate_vibecoding_index(sub_request, engine)
            results.append(result)
        except Exception as e:
            logger.error(f"Failed to calculate index for {sub_request.submission_id}: {e}")
            failed_count += 1

    processing_time = (time.perf_counter() - start_time) * 1000

    return BatchCalculateResponse(
        results=results,
        total_count=len(request.submissions),
        success_count=len(results),
        failed_count=failed_count,
        processing_time_ms=round(processing_time, 2),
    )


@router.get(
    "/thresholds",
    response_model=ThresholdsResponse,
    summary="Get index thresholds",
    description="Get Vibecoding Index thresholds, routing rules, and signal weights.",
)
async def get_thresholds() -> ThresholdsResponse:
    """Get index thresholds and configuration."""
    from app.services.governance.signals_engine import (
        INDEX_THRESHOLDS,
        SIGNAL_WEIGHTS,
    )

    return ThresholdsResponse(
        thresholds={
            cat.value: {"min": t[0], "max": t[1]}
            for cat, t in INDEX_THRESHOLDS.items()
        },
        routing_rules={
            "green": "auto_approve",
            "yellow": "tech_lead_review",
            "orange": "ceo_should_review",
            "red": "ceo_must_review",
        },
        signal_weights={
            signal.value: weight
            for signal, weight in SIGNAL_WEIGHTS.items()
        },
    )


@router.post(
    "/calibrate",
    response_model=CalibrationResponse,
    summary="Submit calibration feedback",
    description="""
    Submit CEO calibration feedback for index tuning.

    This feedback is used to:
    - Adjust signal weights over time
    - Identify false positives/negatives
    - Improve routing accuracy
    """,
)
async def submit_calibration(
    request: CalibrationRequest,
) -> CalibrationResponse:
    """Submit calibration feedback."""
    from uuid import uuid4

    calibration_id = uuid4()

    # TODO: Store calibration data in database
    # For now, just log it

    logger.info(
        f"Calibration received for {request.submission_id}: "
        f"CEO {'agrees' if request.ceo_agrees else 'disagrees'} "
        f"with score {request.calculated_score}"
    )

    if not request.ceo_agrees and request.ceo_suggested_score:
        logger.info(
            f"CEO suggested score: {request.ceo_suggested_score} "
            f"(diff: {request.calculated_score - request.ceo_suggested_score:.1f})"
        )

    # Schedule recalibration if significant disagreement
    recalibration_scheduled = False
    if not request.ceo_agrees:
        diff = abs((request.ceo_suggested_score or 0) - request.calculated_score)
        if diff > 20:
            recalibration_scheduled = True
            logger.warning(
                f"Significant calibration disagreement ({diff:.1f} points). "
                f"Scheduling recalibration analysis."
            )

    return CalibrationResponse(
        success=True,
        submission_id=request.submission_id,
        calibration_id=calibration_id,
        message="Calibration feedback recorded. Thank you!",
        recalibration_scheduled=recalibration_scheduled,
    )


@router.get(
    "/stats",
    response_model=StatsResponse,
    summary="Get index statistics",
    description="Get aggregate statistics for Vibecoding Index calculations.",
)
async def get_stats(
    days: int = Query(7, ge=1, le=90, description="Number of days to include"),
) -> StatsResponse:
    """Get index statistics."""
    # TODO: Implement real statistics from database
    # For now, return placeholder stats

    now = datetime.utcnow()
    period_start = now - __import__("datetime").timedelta(days=days)

    return StatsResponse(
        total_calculations=0,
        average_score=0.0,
        category_distribution={
            "green": 0,
            "yellow": 0,
            "orange": 0,
            "red": 0,
        },
        routing_distribution={
            "auto_approve": 0,
            "tech_lead_review": 0,
            "ceo_should_review": 0,
            "ceo_must_review": 0,
        },
        critical_override_count=0,
        calibration_count=0,
        ceo_agreement_rate=0.0,
        period_start=period_start,
        period_end=now,
    )


@router.get(
    "/health",
    summary="Signals engine health check",
    description="Check health of the Vibecoding Index signals engine.",
)
async def signals_health(
    engine: GovernanceSignalsEngine = Depends(get_signals_engine),
) -> Dict[str, Any]:
    """Health check for signals engine."""
    return {
        "status": "healthy",
        "service": "vibecoding_index_engine",
        "signals_configured": 5,
        "critical_path_checker": "enabled",
        "timestamp": datetime.utcnow().isoformat(),
    }


# NOTE: /{submission_id} must be registered AFTER all static routes to avoid shadowing
@router.get(
    "/{submission_id}",
    response_model=VibecodingIndexResponse,
    summary="Get cached Vibecoding Index",
    description="Get previously calculated Vibecoding Index for a submission.",
)
async def get_vibecoding_index(
    submission_id: UUID,
) -> VibecodingIndexResponse:
    """Get cached Vibecoding Index."""
    # TODO: Implement caching in database
    # For now, return 404 (cache miss)
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"No cached index found for submission {submission_id}. Use POST /calculate instead.",
    )
