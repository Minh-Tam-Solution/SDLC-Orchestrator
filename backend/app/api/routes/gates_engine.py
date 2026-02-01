"""
=========================================================================
Gates Engine API Routes - Gate Evaluation & Policy Integration
SDLC Orchestrator - Sprint 120 (Governance Engine Core)

Version: 1.0.0
Date: January 29, 2026
Status: ACTIVE - Sprint 120 Track B
Authority: CTO + Backend Lead Approved
Framework: SDLC 5.3.0 Quality Assurance System

Endpoints:
- POST /gates-engine/evaluate/{gate_id} - Evaluate single gate
- POST /gates-engine/evaluate-by-code - Evaluate gate by project and code
- GET /gates-engine/prerequisites/{gate_code} - Check prerequisites
- GET /gates-engine/readiness/{project_id} - Get project gate readiness
- GET /gates-engine/policies/{gate_code} - Get policies for gate
- POST /gates-engine/bulk-evaluate - Evaluate multiple gates
- GET /gates-engine/health - Health check

Performance Targets:
- Gate evaluation: <200ms (p95)
- Policy check: <100ms (p95)

Zero Mock Policy: Real OPA calls, real database operations
=========================================================================
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.governance.gates_engine import (
    GatesEngine,
    GateEvaluationResult,
    GateEvaluationStatus,
    EvaluationPhase,
    VALID_GATE_CODES,
    GATE_POLICIES,
    GATE_PREREQUISITES,
    GATE_CODE_TO_STAGE,
    GateNotFoundError,
    InvalidGateCodeError,
    get_gates_engine,
)
from app.services.opa_policy_service import OPAPolicyService, get_opa_policy_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/gates-engine", tags=["Gates Engine"])


# ============================================================================
# Request/Response Models
# ============================================================================


class GateEvaluationRequest(BaseModel):
    """Request model for gate evaluation."""

    submission_data: Optional[Dict[str, Any]] = Field(
        None, description="Submission data for evaluation"
    )
    include_context_check: bool = Field(
        True, description="Include Context Authority V2 check"
    )
    skip_prerequisites: bool = Field(
        False, description="Skip prerequisite check (testing only)"
    )


class EvaluateByCodeRequest(BaseModel):
    """Request for evaluating gate by code."""

    project_id: UUID = Field(..., description="Project UUID")
    gate_code: str = Field(..., description="Gate code (G0.1, G0.2, G1...G9)")
    submission_data: Optional[Dict[str, Any]] = Field(
        None, description="Submission data for evaluation"
    )


class BulkEvaluateRequest(BaseModel):
    """Request for bulk gate evaluation."""

    project_id: UUID = Field(..., description="Project UUID")
    gate_codes: List[str] = Field(
        default_factory=list,
        description="Gate codes to evaluate (empty = all)",
    )
    stop_on_failure: bool = Field(
        True, description="Stop evaluation on first failure"
    )


class CriterionResultResponse(BaseModel):
    """Response for a single criterion result."""

    criterion_id: str
    criterion_name: str
    met: bool
    evidence_provided: bool
    evidence_valid: bool
    policy_passed: bool
    message: str
    evidence_refs: List[str]


class PhaseResultResponse(BaseModel):
    """Response for a single phase result."""

    phase: str
    passed: bool
    message: str
    duration_ms: float
    details: Dict[str, Any]
    errors: List[str]


class GateEvaluationResponse(BaseModel):
    """Response model for gate evaluation."""

    gate_id: UUID
    gate_code: str
    project_id: UUID
    status: str
    overall_passed: bool
    readiness_score: float
    phase_results: List[PhaseResultResponse]
    criteria_results: List[CriterionResultResponse]
    blocking_issues: List[str]
    recommendations: List[str]
    evaluated_at: datetime
    total_duration_ms: float
    context_validation: Optional[Dict[str, Any]]
    vibecoding_index: Optional[float]
    metadata: Dict[str, Any]


class PrerequisitesResponse(BaseModel):
    """Response for prerequisite check."""

    gate_code: str
    stage: str
    prerequisites: List[str]
    all_met: bool
    met_gates: List[str]
    missing_gates: List[str]
    message: str


class GateStatusSummary(BaseModel):
    """Summary of a single gate status."""

    id: Optional[str]
    name: Optional[str]
    status: str
    stage: str
    prerequisites_met: bool
    missing_prerequisites: List[str] = []
    is_blocked: bool
    criteria_met: int = 0
    criteria_total: int = 0


class ReadinessSummaryResponse(BaseModel):
    """Response for project gate readiness."""

    project_id: str
    total_gates: int
    approved_count: int
    current_stage: Optional[str]
    next_gate: Optional[str]
    overall_progress: float
    gates: Dict[str, GateStatusSummary]


class GatePoliciesResponse(BaseModel):
    """Response for gate policies."""

    gate_code: str
    stage: str
    policies: List[str]
    prerequisites: List[str]
    description: str


class BulkEvaluationResponse(BaseModel):
    """Response for bulk evaluation."""

    project_id: str
    evaluated_gates: int
    passed_gates: int
    failed_gates: int
    results: Dict[str, GateEvaluationResponse]
    stop_reason: Optional[str]


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    service: str
    opa_available: bool
    valid_gate_codes: List[str]
    timestamp: datetime


# ============================================================================
# Helper Functions
# ============================================================================


def _convert_to_response(result: GateEvaluationResult) -> GateEvaluationResponse:
    """Convert GateEvaluationResult to response model."""
    return GateEvaluationResponse(
        gate_id=result.gate_id,
        gate_code=result.gate_code,
        project_id=result.project_id,
        status=result.status.value,
        overall_passed=result.overall_passed,
        readiness_score=result.readiness_score,
        phase_results=[
            PhaseResultResponse(
                phase=pr.phase.value,
                passed=pr.passed,
                message=pr.message,
                duration_ms=pr.duration_ms,
                details=pr.details,
                errors=pr.errors,
            )
            for pr in result.phase_results
        ],
        criteria_results=[
            CriterionResultResponse(
                criterion_id=cr.criterion_id,
                criterion_name=cr.criterion_name,
                met=cr.met,
                evidence_provided=cr.evidence_provided,
                evidence_valid=cr.evidence_valid,
                policy_passed=cr.policy_passed,
                message=cr.message,
                evidence_refs=cr.evidence_refs,
            )
            for cr in result.criteria_results
        ],
        blocking_issues=result.blocking_issues,
        recommendations=result.recommendations,
        evaluated_at=result.evaluated_at,
        total_duration_ms=result.total_duration_ms,
        context_validation=result.context_validation,
        vibecoding_index=result.vibecoding_index,
        metadata=result.metadata,
    )


async def _get_engine(
    db: AsyncSession = Depends(get_db),
    opa_service: Optional[OPAPolicyService] = Depends(get_opa_policy_service),
) -> GatesEngine:
    """Get or create GatesEngine with dependencies."""
    return await get_gates_engine(db, opa_service)


# ============================================================================
# Endpoints
# ============================================================================


@router.post(
    "/evaluate/{gate_id}",
    response_model=GateEvaluationResponse,
    summary="Evaluate single gate",
    description="""
    Evaluate a gate for readiness to pass.

    **Evaluation Phases:**
    1. Prerequisites: Check prerequisite gates are approved
    2. Exit Criteria: Verify all exit criteria are met
    3. Policy Evaluation: Run OPA policies for gate
    4. Context Check: Validate context using CA V2
    5. Approval Check: Verify required approvals

    **Readiness Score:**
    - Phase completion: 40%
    - Exit criteria: 40%
    - Vibecoding index: 20%

    Returns detailed evaluation result with recommendations.
    """,
)
async def evaluate_gate(
    gate_id: UUID,
    request: GateEvaluationRequest = GateEvaluationRequest(),
    engine: GatesEngine = Depends(_get_engine),
) -> GateEvaluationResponse:
    """Evaluate a single gate."""
    try:
        result = await engine.evaluate_gate(
            gate_id=gate_id,
            submission_data=request.submission_data,
            include_context_check=request.include_context_check,
            skip_prerequisites=request.skip_prerequisites,
        )

        logger.info(
            f"Gate evaluation: {result.gate_code} - "
            f"{result.status.value} (score: {result.readiness_score:.1f}%)"
        )

        return _convert_to_response(result)

    except GateNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Gate evaluation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gate evaluation failed: {str(e)}",
        )


@router.post(
    "/evaluate-by-code",
    response_model=GateEvaluationResponse,
    summary="Evaluate gate by project and code",
    description="Evaluate a gate by project ID and gate code (G0.1, G0.2, G1...G9).",
)
async def evaluate_by_code(
    request: EvaluateByCodeRequest,
    engine: GatesEngine = Depends(_get_engine),
) -> GateEvaluationResponse:
    """Evaluate gate by project and code."""
    try:
        result = await engine.evaluate_gate_by_code(
            project_id=request.project_id,
            gate_code=request.gate_code,
            submission_data=request.submission_data,
        )

        return _convert_to_response(result)

    except InvalidGateCodeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except GateNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Gate evaluation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gate evaluation failed: {str(e)}",
        )


@router.get(
    "/prerequisites/{gate_code}",
    response_model=PrerequisitesResponse,
    summary="Check gate prerequisites",
    description="Check which prerequisite gates must be passed before a target gate.",
)
async def check_prerequisites(
    gate_code: str,
    project_id: Optional[UUID] = Query(
        None, description="Project ID to check actual status"
    ),
    engine: GatesEngine = Depends(_get_engine),
) -> PrerequisitesResponse:
    """Check prerequisites for a gate."""
    if gate_code not in VALID_GATE_CODES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid gate code: {gate_code}. "
                   f"Valid codes: {', '.join(VALID_GATE_CODES)}",
        )

    prerequisites = GATE_PREREQUISITES.get(gate_code, [])
    stage = GATE_CODE_TO_STAGE.get(gate_code, "UNKNOWN")

    met_gates: List[str] = []
    missing_gates: List[str] = []
    all_met = True

    if project_id:
        all_met, met_gates, missing_gates = await engine.check_gate_prerequisites(
            project_id, gate_code
        )

    if not prerequisites:
        message = f"Gate {gate_code} has no prerequisites"
    elif all_met:
        message = f"All prerequisites met for {gate_code}"
    else:
        message = f"Missing prerequisites: {', '.join(missing_gates)}"

    return PrerequisitesResponse(
        gate_code=gate_code,
        stage=stage,
        prerequisites=prerequisites,
        all_met=all_met,
        met_gates=met_gates,
        missing_gates=missing_gates,
        message=message,
    )


@router.get(
    "/readiness/{project_id}",
    response_model=ReadinessSummaryResponse,
    summary="Get project gate readiness",
    description="Get readiness summary for all gates in a project.",
)
async def get_readiness(
    project_id: UUID,
    engine: GatesEngine = Depends(_get_engine),
) -> ReadinessSummaryResponse:
    """Get project gate readiness summary."""
    try:
        summary = await engine.get_gate_readiness_summary(project_id)

        # Convert gates dict to proper response model
        gates_converted = {}
        for code, data in summary["gates"].items():
            gates_converted[code] = GateStatusSummary(
                id=data.get("id"),
                name=data.get("name"),
                status=data["status"],
                stage=data["stage"],
                prerequisites_met=data.get("prerequisites_met", False),
                missing_prerequisites=data.get("missing_prerequisites", []),
                is_blocked=data.get("is_blocked", True),
                criteria_met=data.get("criteria_met", 0),
                criteria_total=data.get("criteria_total", 0),
            )

        return ReadinessSummaryResponse(
            project_id=summary["project_id"],
            total_gates=summary["total_gates"],
            approved_count=summary.get("approved_count", 0),
            current_stage=summary["current_stage"],
            next_gate=summary["next_gate"],
            overall_progress=summary["overall_progress"],
            gates=gates_converted,
        )

    except Exception as e:
        logger.error(f"Readiness check failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Readiness check failed: {str(e)}",
        )


@router.get(
    "/policies/{gate_code}",
    response_model=GatePoliciesResponse,
    summary="Get policies for gate",
    description="Get the list of OPA policies configured for a gate.",
)
async def get_policies(
    gate_code: str,
) -> GatePoliciesResponse:
    """Get policies configured for a gate."""
    if gate_code not in VALID_GATE_CODES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid gate code: {gate_code}. "
                   f"Valid codes: {', '.join(VALID_GATE_CODES)}",
        )

    policies = GATE_POLICIES.get(gate_code, [])
    prerequisites = GATE_PREREQUISITES.get(gate_code, [])
    stage = GATE_CODE_TO_STAGE.get(gate_code, "UNKNOWN")

    # Generate description
    descriptions = {
        "G0.1": "Foundation Ready - Problem definition and stakeholder identification",
        "G0.2": "Solution Diversity - Solution alternatives evaluated and selected",
        "G1": "Design Ready - Requirements, data model, and architecture complete",
        "G2": "Ship Ready - Architecture review and security baseline passed",
        "G3": "Build Complete - Code, tests, and security scans complete",
        "G4": "Test Complete - Integration, E2E, and performance tests passed",
        "G5": "Deploy Ready - Staging validated and runbooks complete",
        "G6": "Operate Ready - Monitoring and incident response configured",
        "G7": "Integration Complete - API contracts and data flows verified",
        "G8": "Collaboration Ready - Documentation and training complete",
        "G9": "Governance Complete - Compliance and audit trail verified",
    }

    return GatePoliciesResponse(
        gate_code=gate_code,
        stage=stage,
        policies=policies,
        prerequisites=prerequisites,
        description=descriptions.get(gate_code, "No description available"),
    )


@router.post(
    "/bulk-evaluate",
    response_model=BulkEvaluationResponse,
    summary="Evaluate multiple gates",
    description="""
    Evaluate multiple gates for a project.

    If gate_codes is empty, evaluates all gates in order.
    With stop_on_failure=true, stops at first failed gate.
    """,
)
async def bulk_evaluate(
    request: BulkEvaluateRequest,
    engine: GatesEngine = Depends(_get_engine),
) -> BulkEvaluationResponse:
    """Evaluate multiple gates."""
    gate_codes = request.gate_codes or VALID_GATE_CODES

    results: Dict[str, GateEvaluationResponse] = {}
    passed_count = 0
    failed_count = 0
    stop_reason = None

    for gate_code in gate_codes:
        if gate_code not in VALID_GATE_CODES:
            continue

        try:
            result = await engine.evaluate_gate_by_code(
                project_id=request.project_id,
                gate_code=gate_code,
            )

            response = _convert_to_response(result)
            results[gate_code] = response

            if result.overall_passed:
                passed_count += 1
            else:
                failed_count += 1

                if request.stop_on_failure:
                    stop_reason = f"Stopped at {gate_code}: {result.status.value}"
                    break

        except GateNotFoundError:
            # Gate not created yet, skip
            continue
        except Exception as e:
            logger.warning(f"Error evaluating {gate_code}: {e}")
            failed_count += 1

            if request.stop_on_failure:
                stop_reason = f"Error at {gate_code}: {str(e)}"
                break

    return BulkEvaluationResponse(
        project_id=str(request.project_id),
        evaluated_gates=len(results),
        passed_gates=passed_count,
        failed_gates=failed_count,
        results=results,
        stop_reason=stop_reason,
    )


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Gates engine health check",
    description="Check health of gates engine service.",
)
async def health_check(
    opa_service: Optional[OPAPolicyService] = Depends(get_opa_policy_service),
) -> HealthResponse:
    """Health check for gates engine."""
    opa_available = False

    if opa_service:
        try:
            # Try a simple health check on OPA
            opa_available = await opa_service.health_check()
        except Exception:
            opa_available = False

    return HealthResponse(
        status="healthy",
        service="gates_engine",
        opa_available=opa_available,
        valid_gate_codes=VALID_GATE_CODES,
        timestamp=datetime.utcnow(),
    )


@router.get(
    "/stages",
    response_model=Dict[str, str],
    summary="Get gate-to-stage mapping",
    description="Get the mapping of gate codes to SDLC stages.",
)
async def get_stages() -> Dict[str, str]:
    """Get gate-to-stage mapping."""
    return GATE_CODE_TO_STAGE
