"""
=========================================================================
Policies API Router - Policy Pack Library Management (FR5)
SDLC Orchestrator - Stage 03 (BUILD)

Version: 2.0.0
Date: December 4, 2025
Status: ACTIVE - Week 4 Day 4 (OPA Integration COMPLETE) ✅
Authority: Backend Lead + CTO Approved
Foundation: FR5 (Policy Pack Library), FR1 (Gate Engine), Data Model v0.1
Framework: SDLC 4.9 Complete Lifecycle

Purpose:
- Policy library management (list, get policies)
- Policy evaluation (OPA integration)
- Policy evaluation history

API Endpoints (4):
1. GET /policies - List policies with filters ✅ Production-ready
2. GET /policies/{id} - Get policy details ✅ Production-ready
3. POST /policies/evaluate - Evaluate policy against gate ✅ REAL OPA
4. GET /policies/evaluations/{gate_id} - Get policy evaluations for gate ✅ Production-ready

Week 4 Day 4 Upgrade:
✅ OPA integration COMPLETE (REST API, real Rego execution)
✅ Policy evaluation via OPA (network-only, AGPL-safe)
✅ Violation tracking and reporting
✅ Timeout handling (5s fail-safe)

Zero Mock Policy: 100% COMPLIANCE (all mocks removed) ✅
=========================================================================
"""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user
from app.db.session import get_db
from app.models.gate import Gate
from app.models.policy import Policy, PolicyEvaluation
from app.models.user import User
from app.schemas.policy import (
    PolicyEvaluationListResponse,
    PolicyEvaluationRequest,
    PolicyEvaluationResponse,
    PolicyListResponse,
    PolicyResponse,
)
from app.services.opa_service import OPAEvaluationError, opa_service

router = APIRouter()


# ============================================================================
# Policy Endpoints
# ============================================================================


@router.get(
    "/policies",
    response_model=PolicyListResponse,
    summary="List policies",
    description="""
    List policies from policy pack library with filters.

    **Query Parameters**:
    - stage: Filter by SDLC stage (WHY, WHAT, BUILD, etc.)
    - is_active: Filter by active status (default: true)
    - page: Page number (default: 1)
    - page_size: Items per page (default: 20, max: 100)

    **Response** (200 OK):
    - Paginated list of policies
    - Total count and pages
    """,
)
async def list_policies(
    stage: Optional[str] = Query(None, description="Filter by SDLC stage"),
    is_active: bool = Query(True, description="Filter by active status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List policies with pagination and filtering."""

    # Build query
    query = select(Policy).where(Policy.is_active == is_active)

    # Apply filters
    if stage:
        query = query.where(Policy.stage == stage.upper())

    # Get total count
    count_query = select(func.count()).select_from(Policy).where(Policy.is_active == is_active)
    if stage:
        count_query = count_query.where(Policy.stage == stage.upper())

    result = await db.execute(count_query)
    total = result.scalar()

    # Apply pagination
    offset = (page - 1) * page_size
    query = query.order_by(Policy.stage, Policy.policy_code).offset(offset).limit(page_size)

    # Fetch policies
    result = await db.execute(query)
    policies = result.scalars().all()

    # Build response
    items = [
        PolicyResponse(
            id=policy.id,
            policy_name=policy.policy_name,
            policy_code=policy.policy_code,
            stage=policy.stage,
            description=policy.description,
            rego_code=policy.rego_code,
            severity=policy.severity,
            is_active=policy.is_active,
            version=policy.version,
            created_at=policy.created_at,
            updated_at=policy.updated_at,
        )
        for policy in policies
    ]

    return PolicyListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    )


@router.get(
    "/policies/{policy_id}",
    response_model=PolicyResponse,
    summary="Get policy details",
    description="""
    Get policy details by ID.

    **Response** (200 OK):
    - Policy metadata with Rego code
    - Policy severity and version

    **Response** (404 Not Found):
    - Policy not found
    """,
)
async def get_policy(
    policy_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get policy details by ID."""

    # Fetch policy
    result = await db.execute(select(Policy).where(Policy.id == policy_id))
    policy = result.scalar_one_or_none()

    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Policy with ID {policy_id} not found",
        )

    return PolicyResponse(
        id=policy.id,
        policy_name=policy.policy_name,
        policy_code=policy.policy_code,
        stage=policy.stage,
        description=policy.description,
        rego_code=policy.rego_code,
        severity=policy.severity,
        is_active=policy.is_active,
        version=policy.version,
        created_at=policy.created_at,
        updated_at=policy.updated_at,
    )


@router.post(
    "/policies/evaluate",
    response_model=PolicyEvaluationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Evaluate policy",
    description="""
    Evaluate a policy against a gate with custom input data.

    **Week 4 Day 4 - REAL OPA Integration** ✅:
    - OPA evaluation via REST API (http://opa:8181)
    - Real Rego policy execution
    - Violation detection and tracking
    - Timeout handling (5s fail-safe)

    **Request Body**:
    - gate_id: Gate UUID
    - policy_id: Policy UUID
    - input_data: JSON input data for policy evaluation

    **Response** (201 Created):
    - Policy evaluation result (pass/fail)
    - List of violations (if failed)
    - Execution metadata (response time, etc.)
    """,
)
async def evaluate_policy(
    request: PolicyEvaluationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Evaluate a policy against a gate with REAL OPA integration."""

    # Validate gate exists
    result = await db.execute(select(Gate).where(Gate.id == request.gate_id))
    gate = result.scalar_one_or_none()

    if not gate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Gate with ID {request.gate_id} not found",
        )

    # Validate policy exists
    result = await db.execute(select(Policy).where(Policy.id == request.policy_id))
    policy = result.scalar_one_or_none()

    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Policy with ID {request.policy_id} not found",
        )

    # Real OPA evaluation
    try:
        opa_result = opa_service.evaluate_policy(
            policy_code=policy.policy_code,
            stage=gate.stage,
            input_data=request.input_data,
        )

        result_status = "pass" if opa_result["allowed"] else "fail"
        violations = opa_result["violations"]

    except OPAEvaluationError as e:
        # OPA evaluation failed (timeout, connection error, etc.)
        # Record as failed evaluation with error message
        result_status = "fail"
        violations = [f"OPA evaluation error: {str(e)}"]

    # Create evaluation record
    evaluation = PolicyEvaluation(
        id=uuid4(),
        gate_id=request.gate_id,
        policy_id=request.policy_id,
        evaluation_result={
            "result": result_status,
            "violations": violations,
            "metadata": opa_result.get("metadata", {}) if "opa_result" in locals() else {},
        },
        is_passed=(result_status == "pass"),
        violations=violations,
        evaluated_at=datetime.utcnow(),
    )
    db.add(evaluation)
    await db.commit()
    await db.refresh(evaluation)

    return PolicyEvaluationResponse(
        id=evaluation.id,
        gate_id=evaluation.gate_id,
        policy_id=evaluation.policy_id,
        policy_name=policy.policy_name,
        result=result_status,
        violations=violations,
        evaluated_at=evaluation.evaluated_at,
        evaluated_by=f"user-{current_user.id}",
    )


@router.get(
    "/policies/evaluations/{gate_id}",
    response_model=PolicyEvaluationListResponse,
    summary="Get policy evaluations for gate",
    description="""
    Get all policy evaluation results for a specific gate.

    **Response** (200 OK):
    - List of policy evaluations
    - Total evaluations, passed, failed, pass rate
    """,
)
async def get_gate_evaluations(
    gate_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get all policy evaluations for a gate."""

    # Validate gate exists
    result = await db.execute(select(Gate).where(Gate.id == gate_id))
    gate = result.scalar_one_or_none()

    if not gate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Gate with ID {gate_id} not found",
        )

    # Fetch evaluations with policy details
    result = await db.execute(
        select(PolicyEvaluation, Policy)
        .join(Policy, PolicyEvaluation.policy_id == Policy.id)
        .where(PolicyEvaluation.gate_id == gate_id)
        .order_by(PolicyEvaluation.evaluated_at.desc())
    )
    evaluation_rows = result.all()

    # Build response
    items = []
    total = len(evaluation_rows)
    passed = 0
    failed = 0

    for row in evaluation_rows:
        evaluation = row.PolicyEvaluation
        policy = row.Policy

        if evaluation.is_passed:
            passed += 1
        else:
            failed += 1

        items.append(
            PolicyEvaluationResponse(
                id=evaluation.id,
                gate_id=evaluation.gate_id,
                policy_id=evaluation.policy_id,
                policy_name=policy.policy_name,
                result="pass" if evaluation.is_passed else "fail",
                violations=evaluation.violations or [],
                evaluated_at=evaluation.evaluated_at,
                evaluated_by="system",  # TODO: Track evaluator user_id
            )
        )

    pass_rate = (passed / total * 100) if total > 0 else 0.0

    return PolicyEvaluationListResponse(
        items=items,
        total=total,
        passed=passed,
        failed=failed,
        pass_rate=pass_rate,
    )
