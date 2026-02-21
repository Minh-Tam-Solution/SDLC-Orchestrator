"""
=========================================================================
Gates Router - Quality Gate Management (FR1)
SDLC Orchestrator - Stage 03 (BUILD)

Version: 1.0.0
Date: November 28, 2025
Status: ACTIVE - Week 3 Day 3 API Implementation
Authority: Backend Lead + CTO Approved
Foundation: FastAPI, FR1 (Quality Gate Management), OPA Policy Engine
Framework: SDLC 4.9 Complete Lifecycle

Purpose:
- Quality gate CRUD operations
- Gate submission workflow
- Multi-level approval (CTO, CPO, CEO)
- Policy evaluation integration (OPA)
- Evidence attachment

Endpoints:
- POST /gates - Create new gate
- GET /gates - List gates (with pagination + filters)
- GET /gates/{gate_id} - Get gate details
- PUT /gates/{gate_id} - Update gate
- DELETE /gates/{gate_id} - Delete gate (soft delete)
- POST /gates/{gate_id}/submit - Submit gate for approval
- POST /gates/{gate_id}/approve - Approve/reject gate (CTO/CPO/CEO only)
- GET /gates/{gate_id}/approvals - Get gate approval history

Security:
- Authentication required (JWT)
- RBAC: CTO/CPO/CEO for approvals
- Project membership required for gate access

Zero Mock Policy: Production-ready gate management
=========================================================================
"""

from datetime import datetime
import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.dependencies import get_current_active_user, require_roles
from app.db.session import get_db
from app.models.gate import Gate
from app.models.gate_approval import GateApproval
from app.models.gate_evidence import GateEvidence
from app.models.policy import PolicyEvaluation
from app.models.project import Project, ProjectMember
from app.models.user import User, Role
from app.schemas.gate import (
    EvidenceUploadResponse,
    GateActionsResponse,
    GateApprovalRequest,
    GateApprovalResponse,
    GateApproveRequest,
    GateCreateRequest,
    GateEvaluateResponse,
    GateListResponse,
    GateRejectRequest,
    GateResponse,
    GateSubmitRequest,
    GateStatus,
    GateUpdateRequest,
    VALID_TRANSITIONS,
)
from app.services.gate_service import (
    compute_gate_actions,
    validate_transition,
    InvalidTransitionError,
)
from app.middleware.idempotency import check_idempotency, store_idempotency

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/gates", tags=["Gates"])


# =========================================================================
# Helper Functions
# =========================================================================


async def check_project_membership(
    project_id: UUID, user: User, db: AsyncSession
) -> bool:
    """
    Check if user is a member of the project.

    Args:
        project_id: Project UUID
        user: Current user
        db: Database session

    Returns:
        True if user is a member, False otherwise
    """
    result = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user.id,
        )
    )
    return result.scalar_one_or_none() is not None


async def get_gate_or_404(gate_id: UUID, db: AsyncSession) -> Gate:
    """
    Get gate by ID or raise 404.

    Args:
        gate_id: Gate UUID
        db: Database session

    Returns:
        Gate object

    Raises:
        HTTPException(404): If gate not found
    """
    result = await db.execute(
        select(Gate)
        .where(Gate.id == gate_id, Gate.deleted_at.is_(None))
        .options(
            selectinload(Gate.project),
            selectinload(Gate.approvals),
        )
    )
    gate = result.scalar_one_or_none()

    if not gate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Gate {gate_id} not found",
        )

    return gate


async def get_evidence_count(gate_id: UUID, db: AsyncSession) -> int:
    """
    Get count of evidence attached to a gate.

    Args:
        gate_id: Gate UUID
        db: Database session

    Returns:
        Number of evidence files attached to the gate
    """
    result = await db.scalar(
        select(func.count())
        .select_from(GateEvidence)
        .where(
            GateEvidence.gate_id == gate_id,
            GateEvidence.deleted_at.is_(None),
        )
    )
    return result or 0


async def get_policy_violations(gate_id: UUID, db: AsyncSession) -> list:
    """
    Get policy violations for a gate.

    Args:
        gate_id: Gate UUID
        db: Database session

    Returns:
        List of policy violations (from failed PolicyEvaluation records)
    """
    result = await db.execute(
        select(PolicyEvaluation)
        .where(
            PolicyEvaluation.gate_id == gate_id,
            PolicyEvaluation.is_passed == False,
        )
        .order_by(PolicyEvaluation.evaluated_at.desc())
    )
    evaluations = result.scalars().all()

    violations = []
    for eval in evaluations:
        if eval.violations:
            for violation in eval.violations:
                violations.append({
                    "policy_id": str(eval.policy_id) if eval.policy_id else None,
                    "message": violation.get("message", str(violation)) if isinstance(violation, dict) else str(violation),
                    "evaluated_at": eval.evaluated_at.isoformat() if eval.evaluated_at else None,
                })
    return violations


async def get_gate_approvers(db: AsyncSession) -> List[User]:
    """
    Get users who can approve gates (CTO, CPO, CEO roles).

    Args:
        db: Database session

    Returns:
        List of users with approval roles
    """
    result = await db.execute(
        select(User)
        .join(User.roles)
        .where(
            Role.name.in_(["cto", "cpo", "ceo", "CTO", "CPO", "CEO"]),
            User.is_active == True,
        )
        .distinct()
    )
    return list(result.scalars().all())


async def get_gate_stakeholders(gate: Gate, db: AsyncSession) -> List[User]:
    """
    Get users who should be notified about gate status changes.

    This includes:
    - Gate creator
    - Project owner
    - PM role users in the project

    Args:
        gate: Gate object
        db: Database session

    Returns:
        List of stakeholder users
    
    OPTIMIZED: Single JOIN query instead of 2 separate queries (Sprint 146 Performance Fix)
    """
    stakeholder_ids = set()

    # Add gate creator
    if gate.created_by:
        stakeholder_ids.add(gate.created_by)

    # OPTIMIZED: Single query with JOIN to get users directly
    result = await db.execute(
        select(User)
        .join(ProjectMember, ProjectMember.user_id == User.id)
        .where(
            ProjectMember.project_id == gate.project_id,
            ProjectMember.role.in_(["owner", "pm", "admin"]),
            User.is_active == True,
        )
        .distinct()
    )
    stakeholders = list(result.scalars().all())
    
    # Add gate creator if not already in stakeholders
    if gate.created_by and gate.created_by not in {u.id for u in stakeholders}:
        creator_result = await db.execute(
            select(User).where(
                User.id == gate.created_by,
                User.is_active == True,
            )
        )
        creator = creator_result.scalar_one_or_none()
        if creator:
            stakeholders.append(creator)

    return stakeholders


async def evaluate_gate_policies(gate: Gate, db: AsyncSession) -> list:
    """
    Evaluate policies for a gate using OPA (TD-03).

    This function:
    1. Fetches applicable policies for the gate's stage
    2. Evaluates each policy via OPA REST API
    3. Stores results in PolicyEvaluation table
    4. Returns list of violations for API response

    Args:
        gate: Gate object to evaluate
        db: Database session

    Returns:
        List of policy violations (empty if all policies passed)
    """
    from app.services.opa_service import opa_service, OPAEvaluationError
    from app.models.policy import Policy

    violations = []

    # Fetch applicable policies for this gate's stage
    result = await db.execute(
        select(Policy)
        .where(
            Policy.stage == gate.stage,
            Policy.is_active == True,
            Policy.deleted_at.is_(None),
        )
    )
    policies = result.scalars().all()

    if not policies:
        logger.info(f"No active policies found for gate {gate.id} (stage: {gate.stage})")
        return violations

    # Prepare input data for OPA evaluation
    input_data = {
        "gate_id": str(gate.id),
        "gate_name": gate.gate_name,
        "gate_type": gate.gate_type,
        "stage": gate.stage,
        "exit_criteria": gate.exit_criteria or [],
        "project_id": str(gate.project_id),
    }

    # Evaluate each policy
    for policy in policies:
        try:
            # Call OPA to evaluate policy
            opa_result = opa_service.evaluate_policy(
                policy_code=policy.policy_code,
                stage=gate.stage,
                input_data=input_data,
            )

            is_passed = opa_result.get("allowed", False)
            policy_violations = opa_result.get("violations", [])

            # Store evaluation result
            evaluation = PolicyEvaluation(
                gate_id=gate.id,
                policy_id=policy.id,
                is_passed=is_passed,
                violations=policy_violations if not is_passed else None,
                evaluated_at=datetime.utcnow(),
                evaluation_metadata=opa_result.get("metadata", {}),
            )
            db.add(evaluation)

            # Collect violations for response
            if not is_passed and policy_violations:
                for v in policy_violations:
                    violations.append({
                        "policy_id": str(policy.id),
                        "policy_code": policy.policy_code,
                        "message": v if isinstance(v, str) else v.get("message", str(v)),
                        "evaluated_at": datetime.utcnow().isoformat(),
                    })

            logger.info(
                f"Policy {policy.policy_code} evaluated for gate {gate.id}: "
                f"{'PASSED' if is_passed else 'FAILED'}"
            )

        except OPAEvaluationError as e:
            # Log error but don't block gate submission
            logger.warning(
                f"OPA evaluation failed for policy {policy.policy_code} "
                f"on gate {gate.id}: {e}"
            )
            # Store failed evaluation
            evaluation = PolicyEvaluation(
                gate_id=gate.id,
                policy_id=policy.id,
                is_passed=False,
                violations=[{"message": f"Policy evaluation error: {str(e)}"}],
                evaluated_at=datetime.utcnow(),
                evaluation_metadata={"error": str(e)},
            )
            db.add(evaluation)

            violations.append({
                "policy_id": str(policy.id),
                "policy_code": policy.policy_code,
                "message": f"Policy evaluation error: {str(e)}",
                "evaluated_at": datetime.utcnow().isoformat(),
            })

        except Exception as e:
            # Unexpected error - log and continue
            logger.error(
                f"Unexpected error evaluating policy {policy.policy_code} "
                f"on gate {gate.id}: {e}"
            )

    return violations


# =========================================================================
# CRUD Endpoints
# =========================================================================


@router.post("", response_model=GateResponse, status_code=status.HTTP_201_CREATED)
async def create_gate(
    gate_data: GateCreateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> GateResponse:
    """
    Create new quality gate.

    Request Body:
        {
            "project_id": "550e8400-e29b-41d4-a716-446655440000",
            "gate_name": "G2",
            "gate_type": "SHIP_READY",
            "stage": "SHIP",
            "description": "G2 (Ship Ready) - Production deployment approval",
            "exit_criteria": [
                {"criterion": "Zero P0 bugs", "status": "pending"}
            ]
        }

    Response (201 Created):
        {
            "id": "...",
            "project_id": "...",
            "gate_name": "G2",
            "status": "DRAFT",
            ...
        }

    Errors:
        - 401 Unauthorized: Invalid token
        - 403 Forbidden: User not project member
        - 404 Not Found: Project not found

    Flow:
        1. Validate user is project member
        2. Create gate in DRAFT status
        3. Set created_by to current user
        4. Return gate details
    """
    # Verify project exists
    result = await db.execute(
        select(Project).where(Project.id == gate_data.project_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {gate_data.project_id} not found",
        )

    # Verify user is project member
    is_member = await check_project_membership(gate_data.project_id, current_user, db)
    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be a project member to create gates",
        )

    # Create gate
    gate = Gate(
        project_id=gate_data.project_id,
        gate_name=gate_data.gate_name,
        gate_type=gate_data.gate_type,
        stage=gate_data.stage,
        description=gate_data.description,
        exit_criteria=gate_data.exit_criteria,
        status="DRAFT",
        created_by=current_user.id,
    )

    db.add(gate)
    await db.commit()
    await db.refresh(gate)

    return GateResponse(
        id=gate.id,
        project_id=gate.project_id,
        gate_name=gate.gate_name,
        gate_type=gate.gate_type,
        stage=gate.stage,
        status=gate.status,
        description=gate.description,
        exit_criteria=gate.exit_criteria,
        created_by=gate.created_by,
        created_at=gate.created_at,
        updated_at=gate.updated_at,
        approved_at=gate.approved_at,
        deleted_at=gate.deleted_at,
        approvals=[],
        evidence_count=0,
        policy_violations=[],
    )


@router.get("", response_model=GateListResponse, status_code=status.HTTP_200_OK)
async def list_gates(
    project_id: Optional[UUID] = Query(None, description="Filter by project ID"),
    stage: Optional[str] = Query(None, description="Filter by stage (WHY, WHAT, BUILD, etc.)"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status (DRAFT, APPROVED, etc.)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> GateListResponse:
    """
    List quality gates with pagination and filters.

    Query Parameters:
        - project_id: Filter by project UUID
        - stage: Filter by stage (WHY, WHAT, BUILD, TEST, SHIP, etc.)
        - status: Filter by status (DRAFT, PENDING_APPROVAL, APPROVED, REJECTED)
        - page: Page number (default: 1)
        - page_size: Items per page (default: 20, max: 100)

    Response (200 OK):
        {
            "items": [
                {"id": "...", "gate_name": "G2", ...}
            ],
            "total": 9,
            "page": 1,
            "page_size": 20,
            "pages": 1
        }

    Errors:
        - 401 Unauthorized: Invalid token

    Flow:
        1. Build query with filters
        2. Get total count
        3. Apply pagination
        4. Return paginated results
    """
    # Build base query (only gates in user's projects)
    query = select(Gate).where(Gate.deleted_at.is_(None))

    # Apply filters
    if project_id:
        # Verify user is project member
        is_member = await check_project_membership(project_id, current_user, db)
        if not is_member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You must be a project member to view gates",
            )
        query = query.where(Gate.project_id == project_id)

    if stage:
        query = query.where(Gate.stage == stage)

    if status_filter:
        query = query.where(Gate.status == status_filter)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query) or 0

    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    # Execute query
    result = await db.execute(query)
    gates = result.scalars().all()

    # Convert to response models
    items = [
        GateResponse(
            id=gate.id,
            project_id=gate.project_id,
            gate_name=gate.gate_name,
            gate_type=gate.gate_type,
            stage=gate.stage,
            status=gate.status,
            description=gate.description,
            exit_criteria=gate.exit_criteria,
            created_by=gate.created_by,
            created_at=gate.created_at,
            updated_at=gate.updated_at,
            approved_at=gate.approved_at,
            deleted_at=gate.deleted_at,
            approvals=[],
            evidence_count=0,
            policy_violations=[],
        )
        for gate in gates
    ]

    # Calculate total pages
    pages = (total + page_size - 1) // page_size

    return GateListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get("/{gate_id}", response_model=GateResponse, status_code=status.HTTP_200_OK)
async def get_gate(
    gate_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> GateResponse:
    """
    Get gate details by ID.

    Path Parameters:
        - gate_id: Gate UUID

    Response (200 OK):
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "gate_name": "G2",
            "status": "APPROVED",
            "approvals": [
                {
                    "approved_by_name": "Hoàng Văn Em (CTO)",
                    "is_approved": true,
                    "approved_at": "2025-11-28T10:30:00Z"
                }
            ],
            ...
        }

    Errors:
        - 401 Unauthorized: Invalid token
        - 403 Forbidden: User not project member
        - 404 Not Found: Gate not found

    Flow:
        1. Fetch gate by ID
        2. Verify user is project member
        3. Load approvals, evidence count, policy violations
        4. Return gate details
    """
    gate = await get_gate_or_404(gate_id, db)

    # Verify user is project member
    is_member = await check_project_membership(gate.project_id, current_user, db)
    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be a project member to view this gate",
        )

    # Get approval details
    approvals = [
        {
            "id": str(approval.id),
            "approved_by": str(approval.approver_id),
            "is_approved": approval.is_approved,
            "comments": approval.comments,
            "approved_at": approval.approved_at.isoformat(),
        }
        for approval in gate.approvals
    ]

    # Get real evidence count and policy violations (TD-04+05)
    evidence_count = await get_evidence_count(gate_id, db)
    policy_violations = await get_policy_violations(gate_id, db)

    return GateResponse(
        id=gate.id,
        project_id=gate.project_id,
        gate_name=gate.gate_name,
        gate_type=gate.gate_type,
        stage=gate.stage,
        status=gate.status,
        description=gate.description,
        exit_criteria=gate.exit_criteria,
        created_by=gate.created_by,
        created_at=gate.created_at,
        updated_at=gate.updated_at,
        approved_at=gate.approved_at,
        deleted_at=gate.deleted_at,
        approvals=approvals,
        evidence_count=evidence_count,
        policy_violations=policy_violations,
    )


@router.put("/{gate_id}", response_model=GateResponse, status_code=status.HTTP_200_OK)
async def update_gate(
    gate_id: UUID,
    gate_data: GateUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> GateResponse:
    """
    Update gate details.

    Path Parameters:
        - gate_id: Gate UUID

    Request Body:
        {
            "gate_name": "G2 (Updated)",
            "description": "Updated description",
            "exit_criteria": [...]
        }

    Response (200 OK):
        {
            "id": "...",
            "gate_name": "G2 (Updated)",
            ...
        }

    Errors:
        - 401 Unauthorized: Invalid token
        - 403 Forbidden: User not project member or gate already approved
        - 404 Not Found: Gate not found

    Flow:
        1. Fetch gate by ID
        2. Verify user is project member
        3. Verify gate status is DRAFT (cannot update approved gates)
        4. Update gate fields
        5. Return updated gate
    """
    gate = await get_gate_or_404(gate_id, db)

    # Verify user is project member
    is_member = await check_project_membership(gate.project_id, current_user, db)
    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be a project member to update this gate",
        )

    # Verify gate status is DRAFT or PENDING_APPROVAL
    if gate.status not in ["DRAFT", "PENDING_APPROVAL"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Cannot update gate with status '{gate.status}' (only DRAFT or PENDING_APPROVAL allowed)",
        )

    # Update fields (partial update)
    if gate_data.gate_name is not None:
        gate.gate_name = gate_data.gate_name
    if gate_data.gate_type is not None:
        gate.gate_type = gate_data.gate_type
    if gate_data.description is not None:
        gate.description = gate_data.description
    if gate_data.exit_criteria is not None:
        gate.exit_criteria = gate_data.exit_criteria

    gate.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(gate)

    # Get real evidence count and policy violations (TD-04+05)
    evidence_count = await get_evidence_count(gate_id, db)
    policy_violations = await get_policy_violations(gate_id, db)

    return GateResponse(
        id=gate.id,
        project_id=gate.project_id,
        gate_name=gate.gate_name,
        gate_type=gate.gate_type,
        stage=gate.stage,
        status=gate.status,
        description=gate.description,
        exit_criteria=gate.exit_criteria,
        created_by=gate.created_by,
        created_at=gate.created_at,
        updated_at=gate.updated_at,
        approved_at=gate.approved_at,
        deleted_at=gate.deleted_at,
        approvals=[],
        evidence_count=evidence_count,
        policy_violations=policy_violations,
    )


@router.delete("/{gate_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_gate(
    gate_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Delete gate (soft delete).

    Path Parameters:
        - gate_id: Gate UUID

    Response (204 No Content):
        (empty response)

    Errors:
        - 401 Unauthorized: Invalid token
        - 403 Forbidden: User not project member or gate already approved
        - 404 Not Found: Gate not found

    Flow:
        1. Fetch gate by ID
        2. Verify user is project member
        3. Verify gate status is DRAFT (cannot delete approved gates)
        4. Soft delete gate (set deleted_at timestamp)
        5. Return 204 No Content
    """
    gate = await get_gate_or_404(gate_id, db)

    # Verify user is project member
    is_member = await check_project_membership(gate.project_id, current_user, db)
    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be a project member to delete this gate",
        )

    # Verify gate status is DRAFT
    if gate.status != "DRAFT":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Cannot delete gate with status '{gate.status}' (only DRAFT allowed)",
        )

    # Soft delete gate
    gate.deleted_at = datetime.utcnow()
    await db.commit()

    return None


# =========================================================================
# Sprint 173: Governance Loop Endpoints (ADR-053)
# =========================================================================


@router.get("/{gate_id}/actions", response_model=GateActionsResponse, status_code=status.HTTP_200_OK)
async def get_gate_actions(
    gate_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> GateActionsResponse:
    """
    Server-driven capability discovery (Sprint 173 — ADR-053).

    SSOT Invariant: Uses compute_gate_actions() — the same function
    used by all mutation endpoints. No permission drift.

    All 3 clients (Web, CLI, Extension) MUST call this endpoint before
    showing action buttons/options. No client-side permission computation.

    Response (200 OK):
        {
            "gate_id": "uuid",
            "status": "SUBMITTED",
            "actions": {"can_evaluate": false, "can_approve": true, ...},
            "reasons": {"can_evaluate": "Cannot evaluate from status: SUBMITTED"},
            "missing_evidence": ["security-scan"]
        }
    """
    gate = await get_gate_or_404(gate_id, db)

    # Verify user is project member
    is_member = await check_project_membership(gate.project_id, current_user, db)
    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be a project member to view gate actions",
        )

    result = await compute_gate_actions(gate, current_user, db)

    return GateActionsResponse(
        gate_id=result["gate_id"],
        status=result["status"],
        actions=result["actions"],
        reasons=result["reasons"],
        required_evidence=result["required_evidence"],
        submitted_evidence=result["submitted_evidence"],
        missing_evidence=result["missing_evidence"],
    )


@router.post("/{gate_id}/evaluate", response_model=GateEvaluateResponse, status_code=status.HTTP_200_OK)
async def evaluate_gate(
    gate_id: UUID,
    request: Request = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> GateEvaluateResponse:
    """
    Evaluate gate exit criteria (Sprint 173 — ADR-053).

    Transition: DRAFT/EVALUATED/EVALUATED_STALE/REJECTED → EVALUATED

    Response (200 OK):
        {
            "gate_id": "uuid",
            "status": "EVALUATED",
            "evaluated_at": "2026-02-15T10:30:00Z",
            "exit_criteria": [...],
            "summary": {"total": 3, "met": 2, "unmet": 1, "pass_rate": 66.7}
        }

    Errors:
        - 409 Conflict: Invalid state transition
    """
    gate = await get_gate_or_404(gate_id, db)

    # Verify project membership
    is_member = await check_project_membership(gate.project_id, current_user, db)
    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be a project member to evaluate this gate",
        )

    # Check idempotency
    if request:
        cached = await check_idempotency(request, current_user.id, str(gate_id), "evaluate")
        if cached:
            return GateEvaluateResponse(**cached)

    # Validate state transition (SSOT — uses same VALID_TRANSITIONS)
    try:
        target_status = validate_transition("evaluate", gate.status)
    except InvalidTransitionError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )

    # Evaluate exit criteria against evidence
    exit_criteria = gate.exit_criteria or []
    evaluated_criteria = []
    met_count = 0

    for criterion in exit_criteria:
        if isinstance(criterion, dict):
            criterion_copy = dict(criterion)
            # Check if evidence exists for this criterion
            evidence_type = criterion.get("evidence_type") or criterion.get("id", "")
            if evidence_type:
                result = await db.execute(
                    select(func.count())
                    .select_from(GateEvidence)
                    .where(
                        GateEvidence.gate_id == gate.id,
                        GateEvidence.evidence_type == evidence_type,
                        GateEvidence.deleted_at.is_(None),
                    )
                )
                has_evidence = (result.scalar() or 0) > 0
                criterion_copy["met"] = has_evidence
            else:
                criterion_copy["met"] = criterion.get("met", False)

            if criterion_copy.get("met", False):
                met_count += 1
            evaluated_criteria.append(criterion_copy)
        else:
            evaluated_criteria.append(criterion)

    total = len(evaluated_criteria)
    unmet = total - met_count
    pass_rate = round((met_count / total * 100), 1) if total > 0 else 0.0

    # Update gate
    now = datetime.utcnow()
    gate.status = target_status
    gate.exit_criteria = evaluated_criteria
    gate.evaluated_at = now
    gate.updated_at = now

    await db.commit()
    await db.refresh(gate)

    response_data = {
        "gate_id": gate.id,
        "status": gate.status,
        "evaluated_at": now,
        "exit_criteria": evaluated_criteria,
        "summary": {
            "total": total,
            "met": met_count,
            "unmet": unmet,
            "pass_rate": pass_rate,
        },
    }

    # Store idempotency
    if request:
        await store_idempotency(request, current_user.id, str(gate_id), "evaluate", response_data)

    return GateEvaluateResponse(**response_data)


# =========================================================================
# Approval Workflow Endpoints (Sprint 173 — Updated)
# =========================================================================


@router.post("/{gate_id}/submit", response_model=GateResponse, status_code=status.HTTP_200_OK)
async def submit_gate(
    gate_id: UUID,
    submit_data: GateSubmitRequest,
    request: Request = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> GateResponse:
    """
    Submit gate for approval (Sprint 173 — ADR-053).

    Transition: EVALUATED → SUBMITTED
    Precondition: missing_evidence must be empty (SDLC Expert v2)

    Response (200 OK):
        {"id": "...", "status": "SUBMITTED", ...}

    Errors:
        - 409 Conflict: Invalid state transition
        - 422 Unprocessable Entity: Missing required evidence
    """
    gate = await get_gate_or_404(gate_id, db)

    # Verify user is project member
    is_member = await check_project_membership(gate.project_id, current_user, db)
    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be a project member to submit this gate",
        )

    # Check idempotency
    if request:
        cached = await check_idempotency(request, current_user.id, str(gate_id), "submit")
        if cached:
            return GateResponse(**cached)

    # Use compute_gate_actions for SSOT validation (same function as /actions)
    gate_actions = await compute_gate_actions(gate, current_user, db)

    if not gate_actions["actions"]["can_submit"]:
        reason = gate_actions["reasons"].get("can_submit", "Cannot submit gate")

        # Distinguish between state transition error and missing evidence
        if gate_actions["missing_evidence"]:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=reason,
            )

        # State transition error
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=reason,
        )

    # Validate state transition
    try:
        target_status = validate_transition("submit", gate.status)
    except InvalidTransitionError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )

    # Update gate status
    gate.status = target_status
    gate.updated_at = datetime.utcnow()

    # Trigger OPA policy evaluation
    policy_violations = await evaluate_gate_policies(gate, db)

    # Send notifications to CTO/CPO/CEO
    try:
        from app.services.notification_service import create_notification_service

        notification_service = create_notification_service(db)
        approvers = await get_gate_approvers(db)

        if approvers:
            await notification_service.send_gate_approval_notification(
                project=gate.project,
                gate_name=gate.gate_name,
                gate_code=gate.gate_type or gate.gate_name,
                approvers=approvers,
                submitted_by=current_user,
            )
            logger.info(
                f"Sent gate approval notifications to {len(approvers)} approvers "
                f"for gate {gate.gate_name}"
            )
    except Exception as e:
        logger.error(f"Failed to send gate approval notifications: {e}")

    await db.commit()
    await db.refresh(gate)

    evidence_count = await get_evidence_count(gate_id, db)

    response = GateResponse(
        id=gate.id,
        project_id=gate.project_id,
        gate_name=gate.gate_name,
        gate_type=gate.gate_type,
        stage=gate.stage,
        status=gate.status,
        description=gate.description,
        exit_criteria=gate.exit_criteria,
        created_by=gate.created_by,
        created_at=gate.created_at,
        updated_at=gate.updated_at,
        approved_at=gate.approved_at,
        deleted_at=gate.deleted_at,
        approvals=[],
        evidence_count=evidence_count,
        policy_violations=policy_violations,
    )

    # Store idempotency
    if request:
        await store_idempotency(
            request, current_user.id, str(gate_id), "submit",
            response.model_dump(),
        )

    return response


@router.post("/{gate_id}/approve", response_model=GateResponse, status_code=status.HTTP_200_OK)
async def approve_gate(
    gate_id: UUID,
    approval_data: GateApproveRequest,
    request: Request = None,
    current_user: User = Depends(require_roles(["CTO", "CPO", "CEO"])),
    db: AsyncSession = Depends(get_db),
) -> GateResponse:
    """
    Approve gate (Sprint 173 — CTO Mod 1: separate endpoint).

    Transition: SUBMITTED → APPROVED
    Requires: governance:approve scope (CTO/CPO/CEO roles)
    Comment: Required

    Response (200 OK):
        {"id": "...", "status": "APPROVED", "approved_at": "...", ...}

    Errors:
        - 403 Forbidden: User not CTO/CPO/CEO
        - 409 Conflict: Gate not in SUBMITTED status
    """
    gate = await get_gate_or_404(gate_id, db)

    # Check idempotency
    if request:
        cached = await check_idempotency(request, current_user.id, str(gate_id), "approve")
        if cached:
            return GateResponse(**cached)

    # Validate state transition (SSOT — same VALID_TRANSITIONS)
    try:
        target_status = validate_transition("approve", gate.status)
    except InvalidTransitionError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )

    # Create approval record
    approval = GateApproval(
        gate_id=gate.id,
        approver_id=current_user.id,
    )
    approval.approve(comments=approval_data.comment)
    db.add(approval)

    # Update gate status
    now = datetime.utcnow()
    gate.status = target_status
    gate.approved_at = now
    gate.updated_at = now

    await db.commit()
    await db.refresh(gate)
    await db.refresh(approval)

    evidence_count = await get_evidence_count(gate_id, db)
    policy_violations = await get_policy_violations(gate_id, db)

    # Background notifications
    import asyncio

    async def _notify():
        try:
            from app.services.notification_service import create_notification_service
            notification_service = create_notification_service(db)
            stakeholders = await get_gate_stakeholders(gate, db)
            if stakeholders:
                await notification_service.send_gate_approved_notification(
                    project=gate.project,
                    gate_name=gate.gate_name,
                    gate_code=gate.gate_type or gate.gate_name,
                    approved_by=current_user,
                    comments=approval_data.comment,
                    recipients=stakeholders,
                )
        except Exception as e:
            logger.error(f"Failed to send gate approval notifications: {e}")

    asyncio.create_task(_notify())

    response = GateResponse(
        id=gate.id,
        project_id=gate.project_id,
        gate_name=gate.gate_name,
        gate_type=gate.gate_type,
        stage=gate.stage,
        status=gate.status,
        description=gate.description,
        exit_criteria=gate.exit_criteria,
        created_by=gate.created_by,
        created_at=gate.created_at,
        updated_at=gate.updated_at,
        approved_at=gate.approved_at,
        deleted_at=gate.deleted_at,
        approvals=[{
            "id": str(approval.id),
            "approved_by": str(approval.approver_id),
            "is_approved": approval.is_approved,
            "comments": approval.comments,
            "approved_at": approval.approved_at.isoformat(),
        }],
        evidence_count=evidence_count,
        policy_violations=policy_violations,
    )

    if request:
        await store_idempotency(
            request, current_user.id, str(gate_id), "approve",
            response.model_dump(),
        )

    return response


@router.post("/{gate_id}/reject", response_model=GateResponse, status_code=status.HTTP_200_OK)
async def reject_gate(
    gate_id: UUID,
    reject_data: GateRejectRequest,
    request: Request = None,
    current_user: User = Depends(require_roles(["CTO", "CPO", "CEO"])),
    db: AsyncSession = Depends(get_db),
) -> GateResponse:
    """
    Reject gate (Sprint 173 — CTO Mod 1: separate endpoint, ADR-053).

    Transition: SUBMITTED → REJECTED
    Requires: governance:approve scope (CTO/CPO/CEO roles)
    Comment: Required
    After rejection: Gate can be re-evaluated (REJECTED → EVALUATED)

    Response (200 OK):
        {"id": "...", "status": "REJECTED", "rejected_at": "...", ...}

    Errors:
        - 403 Forbidden: User not CTO/CPO/CEO
        - 409 Conflict: Gate not in SUBMITTED status
    """
    gate = await get_gate_or_404(gate_id, db)

    # Check idempotency
    if request:
        cached = await check_idempotency(request, current_user.id, str(gate_id), "reject")
        if cached:
            return GateResponse(**cached)

    # Validate state transition
    try:
        target_status = validate_transition("reject", gate.status)
    except InvalidTransitionError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )

    # Create rejection record
    approval = GateApproval(
        gate_id=gate.id,
        approver_id=current_user.id,
    )
    approval.reject(comments=reject_data.comment)
    db.add(approval)

    # Update gate status
    now = datetime.utcnow()
    gate.status = target_status
    gate.rejected_at = now
    gate.updated_at = now

    await db.commit()
    await db.refresh(gate)
    await db.refresh(approval)

    evidence_count = await get_evidence_count(gate_id, db)
    policy_violations = await get_policy_violations(gate_id, db)

    # Background notifications
    import asyncio

    async def _notify():
        try:
            from app.services.notification_service import create_notification_service
            notification_service = create_notification_service(db)
            stakeholders = await get_gate_stakeholders(gate, db)
            if stakeholders:
                await notification_service.send_gate_rejected_notification(
                    project=gate.project,
                    gate_name=gate.gate_name,
                    gate_code=gate.gate_type or gate.gate_name,
                    rejected_by=current_user,
                    comments=reject_data.comment,
                    recipients=stakeholders,
                )
        except Exception as e:
            logger.error(f"Failed to send gate rejection notifications: {e}")

    asyncio.create_task(_notify())

    action_timestamp = approval.rejected_at or approval.approved_at
    response = GateResponse(
        id=gate.id,
        project_id=gate.project_id,
        gate_name=gate.gate_name,
        gate_type=gate.gate_type,
        stage=gate.stage,
        status=gate.status,
        description=gate.description,
        exit_criteria=gate.exit_criteria,
        created_by=gate.created_by,
        created_at=gate.created_at,
        updated_at=gate.updated_at,
        approved_at=gate.approved_at,
        deleted_at=gate.deleted_at,
        approvals=[{
            "id": str(approval.id),
            "approved_by": str(approval.approver_id),
            "is_approved": approval.is_approved,
            "comments": approval.comments,
            "approved_at": action_timestamp.isoformat() if action_timestamp else None,
        }],
        evidence_count=evidence_count,
        policy_violations=policy_violations,
    )

    if request:
        await store_idempotency(
            request, current_user.id, str(gate_id), "reject",
            response.model_dump(),
        )

    return response


# =========================================================================
# Sprint 173: Evidence Upload Endpoint (ADR-053 — Evidence Contract)
# =========================================================================


@router.post("/{gate_id}/evidence", response_model=EvidenceUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_evidence(
    gate_id: UUID,
    request: Request = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> EvidenceUploadResponse:
    """
    Upload evidence for a gate (Sprint 173 — ADR-053 Evidence Contract).

    Content-Type: multipart/form-data

    Form Fields:
        - file: Binary file data (required)
        - evidence_type: Evidence type string (required)
        - description: Evidence description (optional)
        - sha256_client: Client-computed SHA256 hash (required for cli/extension/web, optional for other)
        - source: Upload source — cli, extension, web, other (default: web)

    Side Effects:
        - If gate status is EVALUATED → automatically set to EVALUATED_STALE
        - Server re-computes SHA256 and compares with client hash
        - Evidence bound to gate's exit_criteria_version via criteria_snapshot_id

    Response (201 Created):
        {
            "evidence_id": "uuid",
            "sha256_client": "a1b2c3d4...",
            "sha256_server": "a1b2c3d4...",
            "integrity_verified": true,
            "gate_status_changed": true,
            "new_gate_status": "EVALUATED_STALE"
        }

    Errors:
        - 400 Bad Request: SHA256 hash mismatch (corruption/tampering)
        - 403 Forbidden: Gate is APPROVED or ARCHIVED
    """
    import hashlib
    from fastapi import Form, UploadFile, File
    gate = await get_gate_or_404(gate_id, db)

    # Verify project membership
    is_member = await check_project_membership(gate.project_id, current_user, db)
    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be a project member to upload evidence",
        )

    # Check if evidence upload is allowed for this gate status
    if gate.status in (GateStatus.APPROVED.value, GateStatus.ARCHIVED.value):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Cannot upload evidence for {gate.status} gate",
        )

    # Parse multipart form data
    form = await request.form()
    file = form.get("file")
    evidence_type = form.get("evidence_type", "")
    description = form.get("description")
    sha256_client = form.get("sha256_client")
    source = form.get("source", "web")

    if not file or not hasattr(file, "read"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File is required",
        )

    if not evidence_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="evidence_type is required",
        )

    # Validate source
    valid_sources = {"cli", "extension", "web", "other"}
    if source not in valid_sources:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid source: {source}. Must be one of: {', '.join(valid_sources)}",
        )

    # Read file content and compute server-side SHA256
    file_content = await file.read()
    file_size = len(file_content)
    sha256_server = hashlib.sha256(file_content).hexdigest()

    # Verify integrity: client hash vs server hash
    integrity_verified = True
    if sha256_client:
        if sha256_client != sha256_server:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="SHA256 hash mismatch: file may be corrupted or tampered",
            )
    else:
        # No client hash provided
        if source != "other":
            logger.warning(
                f"Evidence upload without sha256_client from source={source} "
                f"gate={gate_id} user={current_user.id}"
            )
        integrity_verified = False

    # Upload to MinIO via S3 API (network-only, AGPL-safe)
    file_name = getattr(file, "filename", "evidence_file")
    s3_key = f"evidence/{gate_id}/{file_name}"

    try:
        import requests as http_requests
        from app.core.config import settings

        minio_url = getattr(settings, "MINIO_URL", "http://minio:9000")
        minio_bucket = getattr(settings, "MINIO_BUCKET", "sdlc-evidence")

        upload_response = http_requests.put(
            f"{minio_url}/{minio_bucket}/{s3_key}",
            data=file_content,
            headers={"Content-Type": getattr(file, "content_type", "application/octet-stream")},
            timeout=120,
        )
        upload_response.raise_for_status()
    except Exception as e:
        logger.error(f"MinIO upload failed for gate {gate_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Evidence storage failed: {str(e)}",
        )

    # Create evidence record
    evidence = GateEvidence(
        gate_id=gate.id,
        file_name=file_name,
        file_size=file_size,
        file_type=getattr(file, "content_type", "application/octet-stream"),
        evidence_type=evidence_type,
        s3_key=s3_key,
        s3_bucket=getattr(settings, "MINIO_BUCKET", "sdlc-evidence"),
        sha256_hash=sha256_client,
        sha256_server=sha256_server,
        criteria_snapshot_id=gate.exit_criteria_version,
        source=source,
        description=description,
        uploaded_by=current_user.id,
        uploaded_at=datetime.utcnow(),
    )
    db.add(evidence)

    # Side effect: EVALUATED → EVALUATED_STALE (ADR-053)
    gate_status_changed = False
    new_gate_status = None

    if gate.status == GateStatus.EVALUATED.value:
        gate.status = GateStatus.EVALUATED_STALE.value
        gate.updated_at = datetime.utcnow()
        gate_status_changed = True
        new_gate_status = GateStatus.EVALUATED_STALE.value
        logger.info(
            f"Gate {gate_id} status changed: EVALUATED → EVALUATED_STALE "
            f"(evidence upload by user {current_user.id})"
        )

    await db.commit()
    await db.refresh(evidence)

    return EvidenceUploadResponse(
        evidence_id=evidence.id,
        gate_id=gate.id,
        file_name=file_name,
        file_size=file_size,
        evidence_type=evidence_type,
        sha256_client=sha256_client,
        sha256_server=sha256_server,
        integrity_verified=integrity_verified,
        criteria_snapshot_id=gate.exit_criteria_version,
        source=source,
        gate_status_changed=gate_status_changed,
        new_gate_status=new_gate_status,
    )


# =========================================================================
# Approval History Endpoint
# =========================================================================


@router.get("/{gate_id}/approvals", response_model=List[GateApprovalResponse], status_code=status.HTTP_200_OK)
async def get_gate_approvals(
    gate_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> List[GateApprovalResponse]:
    """
    Get gate approval history.

    Path Parameters:
        - gate_id: Gate UUID

    Response (200 OK):
        [
            {
                "id": "...",
                "approved_by": "...",
                "approved_by_name": "Hoàng Văn Em (CTO)",
                "approved_by_role": "CTO",
                "is_approved": true,
                "comments": "...",
                "approved_at": "2025-11-28T10:30:00Z"
            }
        ]

    Errors:
        - 401 Unauthorized: Invalid token
        - 403 Forbidden: User not project member
        - 404 Not Found: Gate not found

    Flow:
        1. Fetch gate by ID
        2. Verify user is project member
        3. Fetch approval records with approver details
        4. Return approval list
    """
    gate = await get_gate_or_404(gate_id, db)

    # Verify user is project member
    is_member = await check_project_membership(gate.project_id, current_user, db)
    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be a project member to view gate approvals",
        )

    # Fetch approvals with user details and roles (TD-06)
    result = await db.execute(
        select(GateApproval, User)
        .join(User, GateApproval.approver_id == User.id)
        .where(GateApproval.gate_id == gate_id)
        .order_by(GateApproval.approved_at.desc())
        .options(selectinload(User.roles))
    )
    approvals = result.all()

    def get_approver_role(user: User) -> str:
        """Get the highest priority role for an approver (TD-06)."""
        # C-suite roles in priority order
        c_suite_priority = ["ceo", "cto", "cpo", "cio", "cfo"]
        role_names = [r.name.lower() for r in user.roles]

        for role in c_suite_priority:
            if role in role_names:
                return role.upper()

        # Fallback to first role or 'Member'
        if user.roles:
            return user.roles[0].display_name or user.roles[0].name.upper()
        return "Member"

    return [
        GateApprovalResponse(
            id=approval.GateApproval.id,
            gate_id=approval.GateApproval.gate_id,
            approved_by=approval.GateApproval.approver_id,
            approved_by_name=approval.User.name,
            approved_by_role=get_approver_role(approval.User),
            is_approved=approval.GateApproval.is_approved,
            comments=approval.GateApproval.comments,
            approved_at=approval.GateApproval.approved_at,
        )
        for approval in approvals
    ]


# =========================================================================
# Break-Glass Approve (Sprint 192 — Feature-Flagged)
# =========================================================================


class BreakGlassApproveRequest(GateApproveRequest):
    """Break-glass approve request — requires justification fields."""

    reason: str  # min 50 chars enforced below
    incident_ticket: str
    severity: str  # P0 or P1


@router.post(
    "/{gate_id}/break-glass-approve",
    response_model=GateApprovalResponse,
    status_code=status.HTTP_200_OK,
    summary="Break-glass emergency gate approve (admin/owner only)",
    responses={
        404: {"description": "Feature disabled or gate not found"},
        403: {"description": "Insufficient role or rate limited"},
        422: {"description": "Validation error"},
    },
)
async def break_glass_approve_gate(
    gate_id: UUID,
    request: BreakGlassApproveRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> GateApprovalResponse:
    """
    Emergency break-glass gate approval bypassing normal approval workflow.

    Feature-flagged: returns 404 when BREAK_GLASS_WEB_ENABLED=false.
    Requires admin/owner/CTO/CEO role. Rate limited to 2 per user per week.

    Required fields:
        reason: Justification (min 50 chars).
        incident_ticket: Reference to incident ticket.
        severity: P0 or P1.

    Audit: action="break_glass_approve", source="break_glass_web".
    """
    from app.core.config import Settings
    settings = Settings()

    if not settings.BREAK_GLASS_WEB_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="break-glass approve is not enabled",
        )

    # Validate role — CTO P2-2: use actual role names from user model
    allowed_roles = {"ceo", "cto", "admin", "owner"}
    user_roles = set()
    if hasattr(current_user, "roles") and current_user.roles:
        user_roles = {r.name.lower() for r in current_user.roles}
    if hasattr(current_user, "role") and current_user.role:
        user_roles.add(current_user.role.lower())

    if not user_roles & allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="break-glass approve requires admin, owner, CTO, or CEO role",
        )

    # Validate request fields
    if len(request.reason) < 50:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="reason must be at least 50 characters",
        )

    if request.severity not in ("P0", "P1"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="severity must be P0 or P1",
        )

    # Rate limit: max 2 break-glass per user per week (Redis)
    try:
        from app.utils.redis import get_redis_client
        redis = await get_redis_client()
        rate_key = f"break_glass:{current_user.id}"
        count = await redis.get(rate_key)
        if count and int(count) >= 2:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="break-glass rate limit exceeded (max 2 per week)",
            )
        pipe = redis.pipeline()
        pipe.incr(rate_key)
        pipe.expire(rate_key, 7 * 24 * 3600)  # 1 week TTL
        await pipe.execute()
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("break_glass: rate limit check failed: %s", str(exc))

    # Fetch gate
    gate = await db.get(Gate, gate_id)
    if not gate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"gate {gate_id} not found",
        )

    # Approve gate (bypass normal SUBMITTED state requirement)
    now = datetime.utcnow()
    gate.status = "APPROVED"
    gate.approved_at = now

    # Create approval record
    approval = GateApproval(
        gate_id=gate_id,
        approver_id=current_user.id,
        is_approved=True,
        comments=(
            f"[BREAK-GLASS] severity={request.severity} "
            f"ticket={request.incident_ticket} "
            f"reason={request.reason}"
        ),
        approved_at=now,
    )
    db.add(approval)

    # Audit log
    try:
        from app.models.audit_log import AuditLog
        audit = AuditLog(
            event_type="gate_action",
            action="break_glass_approve",
            actor_id=str(current_user.id),
            actor_email=current_user.email,
            resource_type="gate",
            resource_id=str(gate_id),
            detail={
                "severity": request.severity,
                "incident_ticket": request.incident_ticket,
                "reason": request.reason[:200],
                "source": "break_glass_web",
                "previous_status": gate.status,
            },
        )
        db.add(audit)
    except Exception as exc:
        logger.warning("break_glass: audit log failed: %s", str(exc))

    await db.commit()
    await db.refresh(approval)

    logger.info(
        "break_glass: approved gate=%s user=%s severity=%s ticket=%s",
        gate_id, current_user.email, request.severity, request.incident_ticket,
    )

    return GateApprovalResponse(
        id=approval.id,
        gate_id=approval.gate_id,
        approved_by=approval.approver_id,
        approved_by_name=current_user.name or current_user.email,
        approved_by_role="BREAK-GLASS",
        is_approved=True,
        comments=approval.comments,
        approved_at=approval.approved_at,
    )
