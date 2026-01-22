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
from app.models.council_session import (
    CouncilSession,
    CouncilModeType,
    CouncilSessionStatus,
)
from app.models.project import Project, ProjectMember
from app.models.user import User
from app.schemas.council import (
    CouncilDecision,
    CouncilDecisionRequest,
    CouncilMode,
    CouncilProvider,
    CouncilRequest,
    CouncilResponse,
)
from app.services.ai_council_service import AICouncilService
from app.services.settings_service import SettingsService

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
    1. Checks if AI Council is enabled (ADR-027 Phase 2)
    2. Validates violation access
    3. Determines council mode (single, council, or auto)
    4. Executes 3-stage deliberation:
       - Stage 1: Parallel queries to multiple LLM providers
       - Stage 2: Anonymized peer review and ranking
       - Stage 3: Chairman synthesis of best elements
    5. Stores result and returns comprehensive response

    Performance Targets:
    - Single mode: <3s p95 latency
    - Council mode: <8s p95 latency

    Args:
        request: Council deliberation request
        current_user: Authenticated user
        db: Database session

    Returns:
        CouncilResponse with recommendation and deliberation details

    Raises:
        HTTPException 503: If AI Council is disabled by admin
    """
    # ADR-027 Phase 2: Check if AI Council is enabled
    settings_service = SettingsService(db)
    if not await settings_service.is_ai_council_enabled():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI Council is currently disabled. Contact admin to enable this feature.",
        )

    # Check violation access
    violation = await check_violation_access(request.violation_id, current_user, db)

    logger.info(
        f"Triggering council deliberation for violation {request.violation_id} "
        f"by user {current_user.id} (mode: {request.council_mode})"
    )

    # Create council service
    council_service = AICouncilService(db)

    # Map schema enum to model enum
    mode_requested = CouncilModeType.AUTO
    if request.council_mode == CouncilMode.SINGLE:
        mode_requested = CouncilModeType.SINGLE
    elif request.council_mode == CouncilMode.COUNCIL:
        mode_requested = CouncilModeType.COUNCIL

    # Create session record (pending)
    session = CouncilSession(
        project_id=violation.project_id,
        violation_id=violation.id,
        triggered_by=current_user.id,
        mode_requested=mode_requested,
        status=CouncilSessionStatus.IN_PROGRESS,
    )
    db.add(session)
    await db.flush()  # Get session ID

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

        # Update session with results
        mode_used = CouncilModeType.SINGLE
        if response.mode_used == "council":
            mode_used = CouncilModeType.COUNCIL
        elif response.mode_used == "auto":
            mode_used = CouncilModeType.AUTO

        session.mode_used = mode_used
        session.status = CouncilSessionStatus.COMPLETED
        session.providers_used = [p.name for p in response.providers_used] if response.providers_used else []
        session.recommendation = response.recommendation
        session.confidence_score = response.confidence_score
        session.total_duration_ms = response.total_duration_ms
        session.total_cost_usd = response.total_cost_usd
        session.completed_at = datetime.utcnow()

        # Store provider responses if available
        if hasattr(response, 'provider_responses') and response.provider_responses:
            session.provider_responses = [
                {
                    "provider": pr.get("provider"),
                    "model": pr.get("model"),
                    "response": pr.get("response", "")[:1000],  # Truncate
                    "latency_ms": pr.get("latency_ms"),
                    "cost_usd": pr.get("cost_usd"),
                    "tokens_used": pr.get("tokens_used"),
                }
                for pr in response.provider_responses
            ]

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

        # Update session with failure
        session.status = CouncilSessionStatus.FAILED
        session.error_message = str(e)
        session.completed_at = datetime.utcnow()
        await db.commit()

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

    Args:
        request_id: UUID of the deliberation request
        current_user: Authenticated user
        db: Database session

    Returns:
        CouncilResponse with deliberation result
    """
    # Query session from database
    result = await db.execute(
        select(CouncilSession).where(CouncilSession.id == request_id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deliberation session not found: {request_id}",
        )

    # Check project access
    await check_project_access(session.project_id, current_user, db)

    # Map status
    if session.status == CouncilSessionStatus.FAILED:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Deliberation failed: {session.error_message}",
        )

    if session.status in (CouncilSessionStatus.PENDING, CouncilSessionStatus.IN_PROGRESS):
        raise HTTPException(
            status_code=status.HTTP_202_ACCEPTED,
            detail="Deliberation is still in progress. Please check again later.",
        )

    # Build response from session
    providers_used = []
    if session.providers_used:
        for p in session.providers_used:
            try:
                providers_used.append(CouncilProvider(p.upper()))
            except ValueError:
                pass

    mode_used = session.mode_used.value if session.mode_used else "single"

    return CouncilResponse(
        request_id=session.id,
        violation_id=session.violation_id,
        mode_used=mode_used,
        providers_used=providers_used,
        recommendation=session.recommendation or "",
        confidence_score=session.confidence_score or 0,
        total_duration_ms=session.total_duration_ms or 0.0,
        total_cost_usd=session.total_cost_usd or 0.0,
        created_at=session.created_at,
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

    # Build query
    query = select(CouncilSession).where(
        CouncilSession.project_id == project_id,
        CouncilSession.status == CouncilSessionStatus.COMPLETED,
    )

    # Apply mode filter
    if mode:
        mode_lower = mode.lower()
        if mode_lower == "single":
            query = query.where(CouncilSession.mode_used == CouncilModeType.SINGLE)
        elif mode_lower == "council":
            query = query.where(CouncilSession.mode_used == CouncilModeType.COUNCIL)
        elif mode_lower == "auto":
            query = query.where(CouncilSession.mode_used == CouncilModeType.AUTO)

    # Order by created_at DESC and apply pagination
    query = query.order_by(desc(CouncilSession.created_at)).offset(offset).limit(limit)

    result = await db.execute(query)
    sessions = result.scalars().all()

    # Convert to response format
    history = []
    for session in sessions:
        history.append(
            CouncilHistoryItemSchema(
                request_id=session.id,
                violation_id=session.violation_id,
                mode_used=session.mode_used.value if session.mode_used else "single",
                confidence_score=session.confidence_score or 0,
                providers_used=session.providers_used or [],
                total_duration_ms=session.total_duration_ms or 0.0,
                total_cost_usd=session.total_cost_usd or 0.0,
                created_at=session.created_at,
            )
        )

    return history


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

    Args:
        project_id: UUID of the project
        current_user: Authenticated user
        db: Database session

    Returns:
        Council statistics summary
    """
    from sqlalchemy import func as sqlfunc

    # Check project access
    await check_project_access(project_id, current_user, db)

    # Get all sessions for this project
    result = await db.execute(
        select(CouncilSession).where(CouncilSession.project_id == project_id)
    )
    sessions = result.scalars().all()

    if not sessions:
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

    # Calculate stats
    total_deliberations = len(sessions)
    single_mode_count = 0
    council_mode_count = 0
    auto_mode_count = 0
    completed_count = 0
    confidences = []
    durations = []
    total_cost = 0.0

    for session in sessions:
        # Count by mode
        if session.mode_used == CouncilModeType.SINGLE:
            single_mode_count += 1
        elif session.mode_used == CouncilModeType.COUNCIL:
            council_mode_count += 1
        elif session.mode_used == CouncilModeType.AUTO:
            auto_mode_count += 1

        # Track completed sessions
        if session.status == CouncilSessionStatus.COMPLETED:
            completed_count += 1
            if session.confidence_score:
                confidences.append(session.confidence_score)
            if session.total_duration_ms:
                durations.append(session.total_duration_ms)

        # Accumulate cost
        if session.total_cost_usd:
            total_cost += session.total_cost_usd

    # Calculate averages
    average_confidence = sum(confidences) / len(confidences) if confidences else 0.0
    average_duration_ms = sum(durations) / len(durations) if durations else 0.0
    success_rate = (completed_count / total_deliberations * 100) if total_deliberations > 0 else 0.0

    return CouncilStatsResponse(
        total_deliberations=total_deliberations,
        single_mode_count=single_mode_count,
        council_mode_count=council_mode_count,
        auto_mode_count=auto_mode_count,
        average_confidence=round(average_confidence, 2),
        average_duration_ms=round(average_duration_ms, 2),
        total_cost_usd=round(total_cost, 4),
        success_rate=round(success_rate, 2),
    )


# =========================================================================
# Sprint 77: Council Decisions with Sprint Context
# =========================================================================


@router.post(
    "/decide",
    response_model=CouncilDecision,
    summary="Request council decision with sprint context",
    description="""
    Sprint 77 Day 1: AI Council Sprint Context Integration

    Request an AI Council decision with full sprint context.
    The council considers sprint health, team availability, velocity,
    and backlog status when making decisions.

    Decision types:
    - code_review: Review code changes
    - architecture: Architecture decisions
    - security: Security review
    - prioritization: Backlog prioritization
    - estimation: Story point estimation
    - blocker: Blocker resolution
    """,
)
async def request_council_decision(
    request: CouncilDecisionRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> CouncilDecision:
    """
    Request an AI Council decision with sprint context.

    Sprint 77 Day 1: AI Council Sprint Context Integration

    Args:
        request: CouncilDecisionRequest with decision_type and sprint_context
        current_user: Authenticated user
        db: Database session

    Returns:
        CouncilDecision with recommendation and sprint-aware adjustments

    Example:
        POST /council/decide
        {
            "decision_type": "code_review",
            "resource_id": "uuid",
            "resource_type": "backlog_item",
            "requester_id": "uuid",
            "description": "Review refactored authentication module",
            "sprint_context": {
                "sprint_id": "uuid",
                "sprint_number": 77,
                "sprint_name": "Sprint 77",
                "sprint_goal": "AI Council Integration",
                "velocity": { "average": 38, "trend": "stable" },
                "health": { "completion_rate": 65, "risk_level": "low" }
            }
        }
    """
    logger.info(
        f"Council decision requested: type={request.decision_type.value}, "
        f"resource={request.resource_type}/{request.resource_id}, "
        f"requester={request.requester_id}"
    )

    # Verify requester is current user or has admin access
    if request.requester_id != current_user.id:
        # Sprint 88: Platform admins CANNOT access customer data
        # Check if user has regular admin rights (not platform admin)
        is_regular_admin = current_user.is_superuser and not current_user.is_platform_admin
        if not is_regular_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot request decisions for other users",
            )

    # If sprint context provided, verify sprint access
    if request.sprint_context:
        sprint_id = request.sprint_context.sprint_id
        from app.models.sprint import Sprint
        result = await db.execute(
            select(Sprint).where(Sprint.id == sprint_id)
        )
        sprint = result.scalar_one_or_none()
        if not sprint:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sprint not found: {sprint_id}",
            )
        # Check project access
        await check_project_access(sprint.project_id, current_user, db)

    # Create council service
    council_service = AICouncilService(db)

    try:
        # Make decision with sprint context
        decision = await council_service.make_decision(request)

        logger.info(
            f"Council decision completed: type={decision.decision_type.value}, "
            f"confidence={decision.confidence}, "
            f"urgency_adjusted={decision.urgency_adjusted}, "
            f"duration={decision.total_duration_ms:.2f}ms"
        )

        return decision

    except Exception as e:
        logger.error(f"Council decision failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Council decision failed: {str(e)}",
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
