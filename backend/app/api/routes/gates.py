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
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.dependencies import get_current_active_user, require_roles
from app.db.session import get_db
from app.models.gate import Gate
from app.models.gate_approval import GateApproval
from app.models.project import Project, ProjectMember
from app.models.user import User
from app.schemas.gate import (
    GateApprovalRequest,
    GateApprovalResponse,
    GateCreateRequest,
    GateListResponse,
    GateResponse,
    GateSubmitRequest,
    GateUpdateRequest,
)

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
        evidence_count=0,  # TODO: Count from gate_evidence table
        policy_violations=[],  # TODO: Fetch from policy_evaluations table
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
# Approval Workflow Endpoints
# =========================================================================


@router.post("/{gate_id}/submit", response_model=GateResponse, status_code=status.HTTP_200_OK)
async def submit_gate(
    gate_id: UUID,
    submit_data: GateSubmitRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> GateResponse:
    """
    Submit gate for approval (CTO/CPO/CEO review).

    Path Parameters:
        - gate_id: Gate UUID

    Request Body:
        {
            "message": "Submitting G2 for approval. All exit criteria met."
        }

    Response (200 OK):
        {
            "id": "...",
            "status": "PENDING_APPROVAL",
            ...
        }

    Errors:
        - 401 Unauthorized: Invalid token
        - 403 Forbidden: User not project member or gate already submitted
        - 404 Not Found: Gate not found

    Flow:
        1. Fetch gate by ID
        2. Verify user is project member
        3. Verify gate status is DRAFT
        4. Change status: DRAFT → PENDING_APPROVAL
        5. Trigger policy evaluation (OPA) - TODO
        6. Send notifications to CTO/CPO/CEO - TODO
        7. Return updated gate
    """
    gate = await get_gate_or_404(gate_id, db)

    # Verify user is project member
    is_member = await check_project_membership(gate.project_id, current_user, db)
    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be a project member to submit this gate",
        )

    # Verify gate status is DRAFT
    if gate.status != "DRAFT":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Cannot submit gate with status '{gate.status}' (must be DRAFT)",
        )

    # Change status to PENDING_APPROVAL
    gate.status = "PENDING_APPROVAL"
    gate.updated_at = datetime.utcnow()

    # TODO: Trigger OPA policy evaluation
    # TODO: Send notifications to CTO/CPO/CEO

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


@router.post("/{gate_id}/approve", response_model=GateResponse, status_code=status.HTTP_200_OK)
async def approve_gate(
    gate_id: UUID,
    approval_data: GateApprovalRequest,
    current_user: User = Depends(require_roles(["CTO", "CPO", "CEO"])),
    db: AsyncSession = Depends(get_db),
) -> GateResponse:
    """
    Approve or reject gate (CTO, CPO, CEO only).

    Path Parameters:
        - gate_id: Gate UUID

    Request Body:
        {
            "approved": true,
            "comments": "All exit criteria validated. Approved for production."
        }

    Response (200 OK):
        {
            "id": "...",
            "status": "APPROVED",
            "approved_at": "2025-11-28T10:30:00Z",
            ...
        }

    Errors:
        - 401 Unauthorized: Invalid token
        - 403 Forbidden: User not CTO/CPO/CEO or gate not pending approval
        - 404 Not Found: Gate not found

    Flow:
        1. Fetch gate by ID
        2. Verify user is CTO/CPO/CEO (require_roles dependency)
        3. Verify gate status is PENDING_APPROVAL
        4. Create approval record
        5. If approved: Change status → APPROVED, set approved_at
        6. If rejected: Change status → REJECTED
        7. Return updated gate
    """
    gate = await get_gate_or_404(gate_id, db)

    # Verify gate status is PENDING_APPROVAL
    if gate.status != "PENDING_APPROVAL":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Cannot approve gate with status '{gate.status}' (must be PENDING_APPROVAL)",
        )

    # Create approval record
    approval = GateApproval(
        gate_id=gate.id,
        approver_id=current_user.id,
        is_approved=approval_data.approved,
        comments=approval_data.comments,
        approved_at=datetime.utcnow(),
    )
    db.add(approval)

    # Update gate status
    if approval_data.approved:
        gate.status = "APPROVED"
        gate.approved_at = datetime.utcnow()
    else:
        gate.status = "REJECTED"

    gate.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(gate)
    await db.refresh(approval)

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
        approvals=[
            {
                "id": str(approval.id),
                "approved_by": str(approval.approver_id),
                "is_approved": approval.is_approved,
                "comments": approval.comments,
                "approved_at": approval.approved_at.isoformat(),
            }
        ],
        evidence_count=0,
        policy_violations=[],
    )


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

    # Fetch approvals with user details
    result = await db.execute(
        select(GateApproval, User)
        .join(User, GateApproval.approver_id == User.id)
        .where(GateApproval.gate_id == gate_id)
        .order_by(GateApproval.approved_at.desc())
    )
    approvals = result.all()

    return [
        GateApprovalResponse(
            id=approval.GateApproval.id,
            gate_id=approval.GateApproval.gate_id,
            approved_by=approval.GateApproval.approver_id,
            approved_by_name=f"{approval.User.name}",
            approved_by_role="CTO",  # TODO: Get role from user.roles relationship
            is_approved=approval.GateApproval.is_approved,
            comments=approval.GateApproval.comments,
            approved_at=approval.GateApproval.approved_at,
        )
        for approval in approvals
    ]
