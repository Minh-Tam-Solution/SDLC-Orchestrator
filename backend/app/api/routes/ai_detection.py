"""
AI Detection API Routes - Sprint 42

SDLC Stage: 04 - BUILD
Sprint: 42 - AI Detection & Validation Pipeline
Framework: SDLC 5.1.1
Epic: EP-02 AI Safety Layer v1

Purpose:
API endpoints for AI detection service including:
- Detection status and configuration
- Shadow mode management
- Manual detection trigger for testing

Endpoints:
- GET /api/v1/ai-detection/status - Get detection service status
- GET /api/v1/ai-detection/shadow-mode - Get shadow mode status
- POST /api/v1/ai-detection/analyze - Analyze a PR for AI content
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.services.ai_detection import AIToolType
from app.services.ai_detection.service import (
    DETECTION_THRESHOLD,
    GitHubAIDetectionService,
)
from app.services.ai_detection.shadow_mode import (
    get_shadow_mode_status,
    log_shadow_result,
    shadow_mode_config,
)

router = APIRouter(prefix="/ai-detection", tags=["AI Detection"])


class PRAnalysisRequest(BaseModel):
    """Request body for PR analysis."""

    pr_id: str = Field(..., description="PR identifier")
    title: str = Field(..., description="PR title")
    body: Optional[str] = Field(None, description="PR body/description")
    commits: List[Dict[str, Any]] = Field(
        default_factory=list, description="List of commit objects"
    )
    diff: Optional[str] = Field(None, description="Unified diff content")


class PRAnalysisResponse(BaseModel):
    """Response for PR analysis."""

    pr_id: str
    is_ai_generated: bool
    confidence: float
    detected_tool: Optional[str]
    detection_method: str
    detection_duration_ms: int
    individual_confidences: Dict[str, float]
    weighted_confidence: float
    detection_threshold: float


class DetectionStatusResponse(BaseModel):
    """Response for detection service status."""

    service: str
    version: str
    detection_threshold: float
    strategies: List[str]
    weights: Dict[str, float]
    shadow_mode: Dict[str, Any]


@router.get("/status", response_model=DetectionStatusResponse)
async def get_detection_status() -> DetectionStatusResponse:
    """
    Get AI detection service status and configuration.

    Returns current detection threshold, strategies, weights, and shadow mode status.
    """
    return DetectionStatusResponse(
        service="GitHubAIDetectionService",
        version="1.0.0",
        detection_threshold=DETECTION_THRESHOLD,
        strategies=["metadata", "commit", "pattern"],
        weights={"metadata": 0.4, "commit": 0.4, "pattern": 0.2},
        shadow_mode=get_shadow_mode_status(),
    )


@router.get("/shadow-mode")
async def get_shadow_mode() -> Dict[str, Any]:
    """
    Get shadow mode configuration and status.

    Shadow mode enables production validation without affecting users.
    """
    return {
        "status": "enabled" if shadow_mode_config.is_enabled else "disabled",
        "config": get_shadow_mode_status(),
        "description": (
            "Shadow mode logs detection results for production validation "
            "without blocking or modifying PRs."
        ),
    }


@router.post("/analyze", response_model=PRAnalysisResponse)
async def analyze_pr(request: PRAnalysisRequest) -> PRAnalysisResponse:
    """
    Analyze a PR for AI-generated content.

    This endpoint can be used for:
    - Manual testing of the detection service
    - Integration with GitHub webhooks
    - Debugging detection issues

    The result is also logged in shadow mode for production validation.
    """
    service = GitHubAIDetectionService()

    pr_data = {
        "title": request.title,
        "body": request.body or "",
    }

    result = await service.detect(
        pr_data=pr_data,
        commits=request.commits,
        diff=request.diff or "",
    )

    # Log in shadow mode if enabled
    if shadow_mode_config.is_enabled:
        log_shadow_result(
            pr_id=request.pr_id,
            pr_title=request.title,
            result=result,
        )

    # Extract evidence details
    evidence = result.detection_evidence or {}

    return PRAnalysisResponse(
        pr_id=request.pr_id,
        is_ai_generated=result.is_ai_generated,
        confidence=result.confidence,
        detected_tool=result.detected_tool.value if result.detected_tool else None,
        detection_method=result.detection_method.value,
        detection_duration_ms=result.detection_duration_ms,
        individual_confidences=evidence.get("individual_confidences", {}),
        weighted_confidence=evidence.get("weighted_confidence", result.confidence),
        detection_threshold=evidence.get("detection_threshold", DETECTION_THRESHOLD),
    )


@router.get("/tools")
async def get_supported_tools() -> Dict[str, Any]:
    """
    Get list of supported AI tools for detection.

    Returns all AI coding tools that can be detected by the service.
    """
    return {
        "tools": [
            {"id": tool.value, "name": tool.name.replace("_", " ").title()}
            for tool in AIToolType
        ],
        "count": len(AIToolType),
    }
