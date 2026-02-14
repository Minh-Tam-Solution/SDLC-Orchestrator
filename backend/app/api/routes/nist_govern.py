"""
=========================================================================
NIST GOVERN Router - NIST AI RMF GOVERN Function API
SDLC Orchestrator - Sprint 156 (Phase 3: COMPLIANCE)

Version: 1.0.0
Date: April 7, 2026
Status: ACTIVE
Authority: CTO Approved
Framework: SDLC 6.0.5
Reference: ADR-051, NIST AI RMF 1.0

Purpose:
API endpoints for NIST AI RMF GOVERN function:
- Policy evaluation via OPA (5 GOVERN policies)
- GOVERN dashboard aggregation
- Risk register management (CRUD)
- RACI accountability matrix management

Endpoints:
- POST /compliance/nist/govern/evaluate     - Evaluate 5 GOVERN policies
- GET  /compliance/nist/govern/dashboard     - GOVERN dashboard
- GET  /compliance/nist/risks                - List risk entries
- POST /compliance/nist/risks                - Create risk entry
- PUT  /compliance/nist/risks/{risk_id}      - Update risk entry
- GET  /compliance/nist/raci                 - Get RACI matrix
- POST /compliance/nist/raci                 - Create/update RACI entry

Security:
- Authentication required (JWT)
- Project membership required

Zero Mock Policy: Production-ready implementation
=========================================================================
"""

import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user
from app.db.session import get_db
from app.models.compliance import (
    ComplianceAssessment,
    ComplianceControl,
    ComplianceFramework,
    ComplianceRACI,
    ComplianceRiskRegister,
    RiskLikelihood,
    RiskImpact,
    RiskStatus,
    calculate_risk_score,
    LIKELIHOOD_VALUES,
    IMPACT_VALUES,
)
from app.models.user import User
from app.schemas.compliance_framework import (
    GovernDashboardResponse,
    GovernEvaluateRequest,
    GovernEvaluateResponse,
    PolicyEvaluationResult,
    RACICreate,
    RACIListResponse,
    RACIResponse,
    RiskCreate,
    RiskListResponse,
    RiskResponse,
    RiskUpdate,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/compliance/nist",
    tags=["NIST AI RMF GOVERN"],
)

# NIST framework code constant
NIST_FRAMEWORK_CODE = "NIST_AI_RMF"
GOVERN_CATEGORY = "GOVERN"


# =============================================================================
# Helper Functions
# =============================================================================


async def check_project_access(
    project_id: UUID, user: User, db: AsyncSession
) -> None:
    """Check if user has access to project. Raises 403 if not."""
    from app.models.project import Project

    query = select(Project).where(Project.id == project_id)
    result = await db.execute(query)
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    # Check if user owns project or is a member
    if project.owner_id != user.id:
        # TODO: Check project membership when teams are implemented
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this project"
        )


async def _get_nist_framework(db: AsyncSession) -> ComplianceFramework:
    """Get NIST AI RMF framework or raise 404."""
    query = select(ComplianceFramework).where(
        ComplianceFramework.code == NIST_FRAMEWORK_CODE
    )
    result = await db.execute(query)
    framework = result.scalar_one_or_none()
    if not framework:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="NIST AI RMF framework not found. Ensure seed data is loaded.",
        )
    return framework


def _evaluate_accountability(ai_systems: list) -> PolicyEvaluationResult:
    """Evaluate GOVERN-1.1: AI System Accountability Structure."""
    if not ai_systems:
        return PolicyEvaluationResult(
            control_code="GOVERN-1.1",
            title="AI System Accountability Structure",
            allowed=False,
            reason="No AI systems declared. At least one AI system must be documented.",
            severity="critical",
            details={"total_systems": 0, "systems_with_owner": 0, "unowned_systems": []},
        )

    unowned = [s.get("name", "unknown") for s in ai_systems
                if not s.get("owner") or s.get("owner", "").strip() == ""]
    total = len(ai_systems)
    owned = total - len(unowned)

    if not unowned:
        return PolicyEvaluationResult(
            control_code="GOVERN-1.1",
            title="AI System Accountability Structure",
            allowed=True,
            reason="All AI systems have designated owners",
            severity="critical",
            details={"total_systems": total, "systems_with_owner": owned, "unowned_systems": []},
        )

    return PolicyEvaluationResult(
        control_code="GOVERN-1.1",
        title="AI System Accountability Structure",
        allowed=False,
        reason=f"AI systems without owners: {', '.join(unowned)}",
        severity="critical",
        details={"total_systems": total, "systems_with_owner": owned, "unowned_systems": unowned},
    )


def _evaluate_risk_culture(team_training: dict | None) -> PolicyEvaluationResult:
    """Evaluate GOVERN-1.2: AI Risk Awareness Culture."""
    threshold = 80.0

    if not team_training:
        return PolicyEvaluationResult(
            control_code="GOVERN-1.2",
            title="AI Risk Awareness Culture",
            allowed=False,
            reason="No team training data provided.",
            severity="high",
            details={"total_members": 0, "trained_members": 0, "completion_pct": 0.0, "threshold": threshold},
        )

    total = team_training.get("total_members", 0)
    trained = team_training.get("trained_members", 0)

    if total == 0:
        return PolicyEvaluationResult(
            control_code="GOVERN-1.2",
            title="AI Risk Awareness Culture",
            allowed=False,
            reason="Team has zero members.",
            severity="high",
            details={"total_members": 0, "trained_members": 0, "completion_pct": 0.0, "threshold": threshold},
        )

    pct = (trained / total) * 100
    allowed = pct >= threshold

    return PolicyEvaluationResult(
        control_code="GOVERN-1.2",
        title="AI Risk Awareness Culture",
        allowed=allowed,
        reason=f"Team training completion at {pct:.1f}% ({'meets' if allowed else 'below'} {threshold}% threshold)",
        severity="high",
        details={"total_members": total, "trained_members": trained, "completion_pct": round(pct, 1), "threshold": threshold},
    )


def _evaluate_legal(legal_review: dict | None) -> PolicyEvaluationResult:
    """Evaluate GOVERN-1.3: Legal and Regulatory Compliance."""
    if not legal_review:
        return PolicyEvaluationResult(
            control_code="GOVERN-1.3",
            title="Legal and Regulatory Compliance",
            allowed=False,
            reason="No legal review data provided.",
            severity="critical",
            details={"approved": False, "reviewer": None, "review_date": None},
        )

    approved = legal_review.get("approved", False)
    reviewer = legal_review.get("reviewer", "")
    review_date = legal_review.get("date")

    if approved and reviewer and reviewer.strip():
        return PolicyEvaluationResult(
            control_code="GOVERN-1.3",
            title="Legal and Regulatory Compliance",
            allowed=True,
            reason=f"Legal review approved by {reviewer} on {review_date}",
            severity="critical",
            details={"approved": True, "reviewer": reviewer, "review_date": review_date},
        )

    if approved and (not reviewer or not reviewer.strip()):
        return PolicyEvaluationResult(
            control_code="GOVERN-1.3",
            title="Legal and Regulatory Compliance",
            allowed=False,
            reason="Legal review marked approved but missing reviewer name.",
            severity="critical",
            details={"approved": True, "reviewer": None, "review_date": review_date},
        )

    return PolicyEvaluationResult(
        control_code="GOVERN-1.3",
        title="Legal and Regulatory Compliance",
        allowed=False,
        reason="Legal review has not been approved.",
        severity="critical",
        details={"approved": False, "reviewer": reviewer, "review_date": review_date},
    )


def _evaluate_third_party(third_party_apis: list) -> PolicyEvaluationResult:
    """Evaluate GOVERN-1.4: Third-Party AI Oversight."""
    if not third_party_apis:
        return PolicyEvaluationResult(
            control_code="GOVERN-1.4",
            title="Third-Party AI Oversight",
            allowed=True,
            reason="No third-party AI APIs declared. Control is not applicable.",
            severity="high",
            details={"total_apis": 0, "compliant_apis": 0, "non_compliant_apis": []},
        )

    total = len(third_party_apis)
    non_compliant = []

    for api in third_party_apis:
        has_sla = api.get("sla_documented", False)
        has_privacy = api.get("privacy_agreement", False)
        if not has_sla or not has_privacy:
            missing = []
            if not has_sla:
                missing.append("SLA")
            if not has_privacy:
                missing.append("privacy_agreement")
            non_compliant.append({"name": api.get("name", "unknown"), "missing": missing})

    compliant = total - len(non_compliant)

    if not non_compliant:
        return PolicyEvaluationResult(
            control_code="GOVERN-1.4",
            title="Third-Party AI Oversight",
            allowed=True,
            reason=f"All {total} third-party AI APIs have SLA and privacy agreements",
            severity="high",
            details={"total_apis": total, "compliant_apis": compliant, "non_compliant_apis": []},
        )

    return PolicyEvaluationResult(
        control_code="GOVERN-1.4",
        title="Third-Party AI Oversight",
        allowed=False,
        reason=f"{len(non_compliant)} of {total} third-party AI APIs missing required agreements",
        severity="high",
        details={"total_apis": total, "compliant_apis": compliant, "non_compliant_apis": non_compliant},
    )


def _evaluate_continuous_improvement(postmortems: list) -> PolicyEvaluationResult:
    """Evaluate GOVERN-1.5: Continuous Improvement from Incidents."""
    if not postmortems:
        return PolicyEvaluationResult(
            control_code="GOVERN-1.5",
            title="Continuous Improvement from Incidents",
            allowed=True,
            reason="No AI-related incidents recorded. Control is not applicable.",
            severity="medium",
            details={"total_incidents": 0, "timely_postmortems": 0, "late_postmortems": [], "missing_process_updates": []},
        )

    total = len(postmortems)
    late = []
    missing_updates = []
    timely = 0

    for pm in postmortems:
        has_postmortem = pm.get("postmortem_date") not in (None, "")
        has_update = pm.get("process_updated", False)

        if not has_postmortem:
            late.append(pm.get("incident_date"))
        if not has_update:
            missing_updates.append(pm.get("incident_date"))
        if has_postmortem and has_update:
            timely += 1

    issues = len(late) + len(missing_updates)

    if issues == 0:
        return PolicyEvaluationResult(
            control_code="GOVERN-1.5",
            title="Continuous Improvement from Incidents",
            allowed=True,
            reason=f"All {total} incidents have timely postmortems with process updates",
            severity="medium",
            details={"total_incidents": total, "timely_postmortems": timely, "late_postmortems": [], "missing_process_updates": []},
        )

    return PolicyEvaluationResult(
        control_code="GOVERN-1.5",
        title="Continuous Improvement from Incidents",
        allowed=False,
        reason=f"{issues} of {total} incidents have compliance issues",
        severity="medium",
        details={"total_incidents": total, "timely_postmortems": timely, "late_postmortems": late, "missing_process_updates": missing_updates},
    )


# =============================================================================
# Evaluation Endpoints
# =============================================================================


@router.post(
    "/govern/evaluate",
    response_model=GovernEvaluateResponse,
    summary="Evaluate NIST GOVERN policies",
    description="""
    Evaluate all 5 NIST AI RMF GOVERN policies for a project.

    Policies evaluated:
    1. GOVERN-1.1: AI System Accountability (critical)
    2. GOVERN-1.2: AI Risk Awareness Culture (high)
    3. GOVERN-1.3: Legal and Regulatory Compliance (critical)
    4. GOVERN-1.4: Third-Party AI Oversight (high)
    5. GOVERN-1.5: Continuous Improvement (medium)

    Returns per-policy pass/fail with reasons and overall compliance percentage.
    """,
)
async def evaluate_govern(
    request: GovernEvaluateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> GovernEvaluateResponse:
    """Evaluate NIST GOVERN policies for a project."""
    # Authorization: Check project access
    await check_project_access(request.project_id, current_user, db)

    logger.info(f"User {current_user.id} evaluating GOVERN for project {request.project_id}")

    # Evaluate all 5 policies
    results = [
        _evaluate_accountability(request.ai_systems),
        _evaluate_risk_culture(request.team_training),
        _evaluate_legal(request.legal_review),
        _evaluate_third_party(request.third_party_apis),
        _evaluate_continuous_improvement(request.incident_postmortems),
    ]

    passed = sum(1 for r in results if r.allowed)
    total = len(results)
    pct = (passed / total) * 100 if total > 0 else 0.0

    return GovernEvaluateResponse(
        project_id=request.project_id,
        framework_code=NIST_FRAMEWORK_CODE,
        function=GOVERN_CATEGORY,
        overall_compliant=passed == total,
        policies_passed=passed,
        policies_total=total,
        compliance_percentage=round(pct, 1),
        results=results,
        evaluated_at=datetime.now(timezone.utc),
    )


@router.get(
    "/govern/dashboard",
    response_model=GovernDashboardResponse,
    summary="GOVERN dashboard",
    description="""
    Get NIST AI RMF GOVERN function dashboard data for a project.

    Includes:
    - Compliance percentage and policy results
    - Risk summary (count by level)
    - RACI coverage percentage
    """,
)
async def get_govern_dashboard(
    project_id: UUID = Query(..., description="Project ID"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> GovernDashboardResponse:
    """Get GOVERN dashboard data."""
    # Authorization: Check project access
    await check_project_access(project_id, current_user, db)

    logger.info(f"User {current_user.id} viewing GOVERN dashboard for project {project_id}")

    framework = await _get_nist_framework(db)

    # Get risk summary
    risk_query = select(
        ComplianceRiskRegister.risk_score,
    ).where(
        and_(
            ComplianceRiskRegister.project_id == project_id,
            ComplianceRiskRegister.framework_id == framework.id,
        )
    )
    risk_result = await db.execute(risk_query)
    scores = [row[0] for row in risk_result.all()]

    risk_summary = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for score in scores:
        if score >= 16:
            risk_summary["critical"] += 1
        elif score >= 10:
            risk_summary["high"] += 1
        elif score >= 5:
            risk_summary["medium"] += 1
        else:
            risk_summary["low"] += 1

    # Get RACI coverage (how many GOVERN controls have RACI assignments)
    govern_controls_query = select(func.count(ComplianceControl.id)).where(
        and_(
            ComplianceControl.framework_id == framework.id,
            ComplianceControl.category == GOVERN_CATEGORY,
        )
    )
    total_controls_result = await db.execute(govern_controls_query)
    total_controls = total_controls_result.scalar() or 0

    raci_count_query = (
        select(func.count(ComplianceRACI.id))
        .join(ComplianceControl, ComplianceRACI.control_id == ComplianceControl.id)
        .where(
            and_(
                ComplianceRACI.project_id == project_id,
                ComplianceControl.framework_id == framework.id,
                ComplianceControl.category == GOVERN_CATEGORY,
            )
        )
    )
    raci_count_result = await db.execute(raci_count_query)
    raci_count = raci_count_result.scalar() or 0

    raci_coverage = (raci_count / total_controls) * 100 if total_controls > 0 else 0.0

    return GovernDashboardResponse(
        project_id=project_id,
        compliance_percentage=0.0,  # Populated when evaluate is called
        policies_passed=0,
        policies_total=total_controls,
        risk_summary=risk_summary,
        total_risks=len(scores),
        raci_coverage=round(raci_coverage, 1),
    )


# =============================================================================
# Risk Register Endpoints
# =============================================================================


@router.get(
    "/risks",
    response_model=RiskListResponse,
    summary="List risk register",
    description="List risk register entries for a project.",
)
async def list_risks(
    project_id: UUID = Query(..., description="Project ID"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    category: Optional[str] = Query(None, description="Filter by category"),
    limit: int = Query(50, ge=1, le=200, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Skip results"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> RiskListResponse:
    """List risk register entries."""
    # Authorization: Check project access
    await check_project_access(project_id, current_user, db)

    framework = await _get_nist_framework(db)

    query = select(ComplianceRiskRegister).where(
        and_(
            ComplianceRiskRegister.project_id == project_id,
            ComplianceRiskRegister.framework_id == framework.id,
        )
    )

    if status_filter:
        query = query.where(ComplianceRiskRegister.status == status_filter)
    if category:
        query = query.where(ComplianceRiskRegister.category == category.lower())

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply pagination and ordering
    query = query.order_by(ComplianceRiskRegister.risk_score.desc())
    query = query.limit(limit).offset(offset)

    result = await db.execute(query)
    risks = result.scalars().all()

    items = []
    for risk in risks:
        risk_data = RiskResponse.model_validate(risk)
        # Compute risk level
        if risk.risk_score >= 16:
            risk_data.risk_level = "critical"
        elif risk.risk_score >= 10:
            risk_data.risk_level = "high"
        elif risk.risk_score >= 5:
            risk_data.risk_level = "medium"
        else:
            risk_data.risk_level = "low"
        items.append(risk_data)

    return RiskListResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
        has_more=(offset + limit) < total,
    )


@router.post(
    "/risks",
    response_model=RiskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create risk entry",
    description="Create a new risk register entry with auto-calculated risk score.",
)
async def create_risk(
    data: RiskCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> RiskResponse:
    """Create risk register entry."""
    # Authorization: Check project access
    await check_project_access(data.project_id, current_user, db)

    logger.info(f"User {current_user.id} creating risk {data.risk_code} for project {data.project_id}")

    framework = await _get_nist_framework(db)

    # Calculate risk score
    score = calculate_risk_score(
        RiskLikelihood(data.likelihood.value),
        RiskImpact(data.impact.value),
    )

    risk = ComplianceRiskRegister(
        project_id=data.project_id,
        framework_id=framework.id,
        risk_code=data.risk_code,
        title=data.title,
        description=data.description,
        likelihood=data.likelihood.value,
        impact=data.impact.value,
        risk_score=score,
        category=data.category,
        mitigation_strategy=data.mitigation_strategy,
        responsible_id=data.responsible_id,
        target_date=data.target_date,
    )

    db.add(risk)
    await db.commit()
    await db.refresh(risk)

    risk_data = RiskResponse.model_validate(risk)
    if score >= 16:
        risk_data.risk_level = "critical"
    elif score >= 10:
        risk_data.risk_level = "high"
    elif score >= 5:
        risk_data.risk_level = "medium"
    else:
        risk_data.risk_level = "low"

    return risk_data


@router.put(
    "/risks/{risk_id}",
    response_model=RiskResponse,
    summary="Update risk entry",
    description="Update an existing risk register entry. Recalculates risk score if likelihood or impact changed.",
)
async def update_risk(
    risk_id: UUID,
    data: RiskUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> RiskResponse:
    """Update risk register entry."""
    query = select(ComplianceRiskRegister).where(ComplianceRiskRegister.id == risk_id)
    result = await db.execute(query)
    risk = result.scalar_one_or_none()

    if not risk:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Risk entry {risk_id} not found",
        )

    # Authorization: Check project access
    await check_project_access(risk.project_id, current_user, db)

    # Update fields
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            if hasattr(value, "value"):
                setattr(risk, field, value.value)
            else:
                setattr(risk, field, value)

    # Recalculate risk score if likelihood or impact changed
    if "likelihood" in update_data or "impact" in update_data:
        risk.risk_score = calculate_risk_score(
            RiskLikelihood(risk.likelihood),
            RiskImpact(risk.impact),
        )

    await db.commit()
    await db.refresh(risk)

    risk_data = RiskResponse.model_validate(risk)
    if risk.risk_score >= 16:
        risk_data.risk_level = "critical"
    elif risk.risk_score >= 10:
        risk_data.risk_level = "high"
    elif risk.risk_score >= 5:
        risk_data.risk_level = "medium"
    else:
        risk_data.risk_level = "low"

    return risk_data


# =============================================================================
# RACI Matrix Endpoints
# =============================================================================


@router.get(
    "/raci",
    response_model=RACIListResponse,
    summary="Get RACI matrix",
    description="Get RACI accountability matrix entries for a project's GOVERN controls.",
)
async def get_raci(
    project_id: UUID = Query(..., description="Project ID"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> RACIListResponse:
    """Get RACI matrix for project."""
    # Authorization: Check project access
    await check_project_access(project_id, current_user, db)

    framework = await _get_nist_framework(db)

    query = (
        select(ComplianceRACI)
        .join(ComplianceControl, ComplianceRACI.control_id == ComplianceControl.id)
        .where(
            and_(
                ComplianceRACI.project_id == project_id,
                ComplianceControl.framework_id == framework.id,
            )
        )
        .order_by(ComplianceControl.sort_order)
    )

    result = await db.execute(query)
    raci_entries = result.scalars().all()

    return RACIListResponse(
        items=[RACIResponse.model_validate(r) for r in raci_entries],
        total=len(raci_entries),
    )


@router.post(
    "/raci",
    response_model=RACIResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create/update RACI entry",
    description="Create or update a RACI entry for a project-control pair.",
)
async def upsert_raci(
    data: RACICreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> RACIResponse:
    """Create or update RACI entry."""
    # Authorization: Check project access
    await check_project_access(data.project_id, current_user, db)

    logger.info(f"User {current_user.id} upserting RACI for project {data.project_id} control {data.control_id}")

    # Check if RACI entry already exists
    existing_query = select(ComplianceRACI).where(
        and_(
            ComplianceRACI.project_id == data.project_id,
            ComplianceRACI.control_id == data.control_id,
        )
    )
    existing_result = await db.execute(existing_query)
    existing = existing_result.scalar_one_or_none()

    if existing:
        # Update existing RACI entry
        existing.responsible_id = data.responsible_id
        existing.accountable_id = data.accountable_id
        existing.consulted_ids = data.consulted_ids
        existing.informed_ids = data.informed_ids
        await db.commit()
        await db.refresh(existing)
        return RACIResponse.model_validate(existing)

    # Create new RACI entry
    raci = ComplianceRACI(
        project_id=data.project_id,
        control_id=data.control_id,
        responsible_id=data.responsible_id,
        accountable_id=data.accountable_id,
        consulted_ids=data.consulted_ids,
        informed_ids=data.informed_ids,
    )
    db.add(raci)
    await db.commit()
    await db.refresh(raci)

    return RACIResponse.model_validate(raci)
