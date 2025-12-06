"""
=========================================================================
AI Council Router - SDLC 4.9.1 AI Council Deliberation
SDLC Orchestrator - Stage 03 (BUILD)

Version: 1.0.0
Date: December 4, 2025
Status: ACTIVE - Sprint 26 Day 3 (API + Compliance Integration)
Authority: Backend Lead + CTO Approved
Foundation: Sprint 26 Plan, ADR-011 (AI Governance Layer)
Framework: SDLC 4.9.1 Complete Lifecycle

Purpose:
- Trigger AI Council deliberations for compliance violations
- Get deliberation status and results
- Auto-council for CRITICAL/HIGH violations
- Multi-provider LLM consensus recommendations

Endpoints:
- POST /council/deliberate - Trigger council deliberation
- GET /council/status/{request_id} - Get deliberation status
- GET /council/history/{project_id} - Get project council history

3-Stage Council Process:
- Stage 1: Parallel Queries (all providers answer independently)
- Stage 2: Peer Review (anonymized ranking)
- Stage 3: Chairman Synthesis (best elements combined)

Council Modes:
- SINGLE: Fast mode (1 provider, <3s target)
- COUNCIL: Accurate mode (3+ providers, <8s target)
- AUTO: Severity-based (CRITICAL/HIGH → council, else single)

Security:
- Authentication required (JWT)
- Project membership required for violation access
- Audit trail for all council requests

Performance Targets:
- Single mode: <3s p95 latency
- Council mode: <8s p95 latency
- Success rate: >95%

Zero Mock Policy: Production-ready AI council with real LLM calls
=========================================================================
"""

import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user
from app.db.session import get_db
from app.models.compliance_scan import ComplianceViolation
from app.models.project import Project, ProjectMember
from app.models.user import User
from app.schemas.council import (
    CouncilMode,
    CouncilProvider,
    CouncilRequest,
    CouncilResponse,
)
from app.services.ai_council_service import AICouncilService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/council", tags=["AI Council"])


# =========================================================================
# Pydantic Schemas (additional response models)
# =========================================================================


class CouncilHistoryItemSchema(BaseModel):
    """Council history item (summary)."""

    request_id: UUID
    violation_id: UUID
    mode_used: str
    confidence_score: int
    providers_used: List[str]
    total_duration_ms: float
    total_cost_usd: float
    created_at: datetime

    class Config:
        from_attributes = True


class CouncilStatsResponse(BaseModel):
    """Council statistics for a project."""

    total_deliberations: int
    single_mode_count: int
    council_mode_count: int
    auto_mode_count: int
    average_confidence: float
    average_duration_ms: float
    total_cost_usd: float
    success_rate: float


# =========================================================================
# Helper Functions
# =========================================================================


async def check_violation_access(
    violation_id: UUID, user: User, db: AsyncSession
) -> ComplianceViolation:
    """
    Check if user has access to the violation's project.

    Args:
        violation_id: UUID of the violation
        user: Current user
        db: Database session

    Returns:
        ComplianceViolation if access granted

    Raises:
        HTTPException: If violation not found or access denied
    """
    # Get violation
    result = await db.execute(
        select(ComplianceViolation).where(ComplianceViolation.id == violation_id)
    )
    violation = result.scalar_one_or_none()

    if not violation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Violation not found: {violation_id}",
        )

    # Get project
    project_result = await db.execute(
        select(Project).where(
            Project.id == violation.project_id,
            Project.deleted_at.is_(None),
        )
    )
    project = project_result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project not found: {violation.project_id}",
        )

    # Check if user is owner
    if project.owner_id == user.id:
        return violation

    # Check if user is member
    membership_result = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project.id,
            ProjectMember.user_id == user.id,
        )
    )
    membership = membership_result.scalar_one_or_none()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. You are not a member of this project.",
        )

    return violation


async def check_project_access(
    project_id: UUID, user: User, db: AsyncSession
) -> Project:
    """
    Check if user has access to the project.

    Args:
        project_id: UUID of the project
        user: Current user
        db: Database session

    Returns:
        Project if access granted

    Raises:
        HTTPException: If project not found or access denied
    """
    # Get project
    result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.deleted_at.is_(None),
        )
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project not found: {project_id}",
        )

    # Check if user is owner
    if project.owner_id == user.id:
        return project

    # Check if user is member
    membership_result = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user.id,
        )
    )
    membership = membership_result.scalar_one_or_none()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. You are not a member of this project.",
        )

    return project


# =========================================================================
# Endpoints
# =========================================================================


@router.post(
    "/deliberate",
    response_model=CouncilResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Trigger AI Council deliberation",
    description="Trigger AI Council deliberation for a compliance violation. "
    "Uses 3-stage process: parallel queries, peer review, chairman synthesis.",
)
async def trigger_deliberation(
    request: CouncilRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> CouncilResponse:
    """
    Trigger AI Council deliberation for a compliance violation.

    This endpoint:
    1. Validates violation access
    2. Determines council mode (single, council, or auto)
    3. Executes 3-stage deliberation:
       - Stage 1: Parallel queries to multiple LLM providers
       - Stage 2: Anonymized peer review and ranking
       - Stage 3: Chairman synthesis of best elements
    4. Stores result and returns comprehensive response

    Performance Targets:
    - Single mode: <3s p95 latency
    - Council mode: <8s p95 latency

    Args:
        request: Council deliberation request
        current_user: Authenticated user
        db: Database session

    Returns:
        CouncilResponse with recommendation and deliberation details
    """
    # Check violation access
    violation = await check_violation_access(request.violation_id, current_user, db)

    logger.info(
        f"Triggering council deliberation for violation {request.violation_id} "
        f"by user {current_user.id} (mode: {request.council_mode})"
    )

    # Create council service
    council_service = AICouncilService(db)

    try:
        # Execute deliberation
        response = await council_service.deliberate(
            violation=violation,
            council_mode=request.council_mode,
            providers=request.providers,
            user_id=current_user.id,
        )

        logger.info(
            f"Council deliberation completed for violation {request.violation_id}: "
            f"mode={response.mode_used}, confidence={response.confidence_score}, "
            f"duration={response.total_duration_ms:.2f}ms, cost=${response.total_cost_usd:.4f}"
        )

        # Update violation with AI recommendation (Sprint 26 integration)
        violation.ai_recommendation = response.recommendation
        violation.ai_provider = f"council-{response.mode_used}"
        violation.ai_confidence = response.confidence_score
        await db.commit()

        return response

    except Exception as e:
        logger.error(
            f"Council deliberation failed for violation {request.violation_id}: {e}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Council deliberation failed: {str(e)}",
        )


@router.get(
    "/status/{request_id}",
    response_model=CouncilResponse,
    summary="Get deliberation status",
    description="Get the status and result of a council deliberation request.",
)
async def get_deliberation_status(
    request_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> CouncilResponse:
    """
    Get the status of a council deliberation request.

    Note: Currently council deliberations are synchronous, so this endpoint
    returns the stored result. Future versions may support async deliberations.

    Args:
        request_id: UUID of the deliberation request
        current_user: Authenticated user
        db: Database session

    Returns:
        CouncilResponse with deliberation result
    """
    # TODO: Implement deliberation_sessions table in future sprint
    # For now, return 501 Not Implemented as deliberations are synchronous
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Deliberation status tracking will be available in Sprint 27. "
        "Currently, deliberations are synchronous and return immediately.",
    )


@router.get(
    "/history/{project_id}",
    response_model=List[CouncilHistoryItemSchema],
    summary="Get project council history",
    description="Get council deliberation history for a project.",
)
async def get_project_council_history(
    project_id: UUID,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    mode: Optional[str] = Query(default=None, description="Filter by council mode"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> List[CouncilHistoryItemSchema]:
    """
    Get council deliberation history for a project.

    Note: This endpoint will be fully implemented in Sprint 27 when
    deliberation_sessions table is added. Currently returns empty list.

    Args:
        project_id: UUID of the project
        limit: Maximum number of results
        offset: Number of results to skip
        mode: Optional filter by council mode
        current_user: Authenticated user
        db: Database session

    Returns:
        List of council history items
    """
    # Check project access
    await check_project_access(project_id, current_user, db)

    # TODO: Implement with deliberation_sessions table in Sprint 27
    # For now, return empty list
    logger.warning(
        f"Council history requested for project {project_id} but not yet implemented"
    )
    return []


@router.get(
    "/stats/{project_id}",
    response_model=CouncilStatsResponse,
    summary="Get project council statistics",
    description="Get aggregated statistics for council deliberations in a project.",
)
async def get_project_council_stats(
    project_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> CouncilStatsResponse:
    """
    Get aggregated council statistics for a project.

    Note: This endpoint will be fully implemented in Sprint 27 when
    deliberation_sessions table is added.

    Args:
        project_id: UUID of the project
        current_user: Authenticated user
        db: Database session

    Returns:
        Council statistics summary
    """
    # Check project access
    await check_project_access(project_id, current_user, db)

    # TODO: Implement with deliberation_sessions table in Sprint 27
    # For now, return zero stats
    logger.warning(
        f"Council stats requested for project {project_id} but not yet implemented"
    )
    return CouncilStatsResponse(
        total_deliberations=0,
        single_mode_count=0,
        council_mode_count=0,
        auto_mode_count=0,
        average_confidence=0.0,
        average_duration_ms=0.0,
        total_cost_usd=0.0,
        success_rate=0.0,
    )


# =========================================================================
# Auto-Council Integration (Sprint 26 Day 3)
# =========================================================================


async def auto_council_for_critical_violations(
    project_id: UUID,
    scan_id: UUID,
    db: AsyncSession,
) -> dict:
    """
    Automatically trigger council deliberation for CRITICAL/HIGH violations.

    This function is called by the compliance scanner after scan completion.
    It identifies CRITICAL and HIGH severity violations and triggers
    council deliberation for each.

    Args:
        project_id: UUID of the project
        scan_id: UUID of the compliance scan
        db: Database session

    Returns:
        Dictionary with council results summary:
        {
            "total_violations": int,
            "council_triggered": int,
            "council_succeeded": int,
            "council_failed": int,
            "average_confidence": float,
            "total_cost_usd": float,
        }
    """
    logger.info(
        f"Auto-council: checking for CRITICAL/HIGH violations in scan {scan_id}"
    )

    # Query CRITICAL and HIGH violations from this scan
    result = await db.execute(
        select(ComplianceViolation).where(
            ComplianceViolation.scan_id == scan_id,
            ComplianceViolation.severity.in_(["CRITICAL", "HIGH"]),
            ComplianceViolation.is_resolved == False,
        )
    )
    violations = result.scalars().all()

    total_violations = len(violations)
    if total_violations == 0:
        logger.info("Auto-council: no CRITICAL/HIGH violations found")
        return {
            "total_violations": 0,
            "council_triggered": 0,
            "council_succeeded": 0,
            "council_failed": 0,
            "average_confidence": 0.0,
            "total_cost_usd": 0.0,
        }

    logger.info(
        f"Auto-council: found {total_violations} CRITICAL/HIGH violations, "
        "triggering council deliberations"
    )

    # Create council service
    council_service = AICouncilService(db)

    # Track results
    council_triggered = 0
    council_succeeded = 0
    council_failed = 0
    confidences = []
    total_cost = 0.0

    # Trigger council for each violation
    for violation in violations:
        try:
            council_triggered += 1

            # Use AUTO mode (will use council for CRITICAL/HIGH)
            response = await council_service.deliberate(
                violation=violation,
                council_mode=CouncilMode.AUTO,
                providers=None,  # Use default providers
                user_id=None,  # System-triggered
            )

            # Update violation with recommendation
            violation.ai_recommendation = response.recommendation
            violation.ai_provider = f"council-{response.mode_used}"
            violation.ai_confidence = response.confidence_score

            council_succeeded += 1
            confidences.append(response.confidence_score)
            total_cost += response.total_cost_usd

            logger.info(
                f"Auto-council: deliberation succeeded for violation {violation.id} "
                f"(confidence: {response.confidence_score})"
            )

        except Exception as e:
            council_failed += 1
            logger.error(
                f"Auto-council: deliberation failed for violation {violation.id}: {e}"
            )
            # Continue with other violations even if one fails

    # Commit all updates
    await db.commit()

    # Calculate average confidence
    average_confidence = sum(confidences) / len(confidences) if confidences else 0.0

    summary = {
        "total_violations": total_violations,
        "council_triggered": council_triggered,
        "council_succeeded": council_succeeded,
        "council_failed": council_failed,
        "average_confidence": average_confidence,
        "total_cost_usd": total_cost,
    }

    logger.info(
        f"Auto-council completed for scan {scan_id}: "
        f"{council_succeeded}/{council_triggered} succeeded, "
        f"avg confidence: {average_confidence:.1f}, "
        f"total cost: ${total_cost:.4f}"
    )

    return summary
