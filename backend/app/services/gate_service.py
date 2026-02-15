"""
=========================================================================
Gate Service - Quality Gate Management (FR1)
SDLC Orchestrator - Sprint 107 (Test Strategy 2026)

Version: 1.0.0
Date: January 27, 2026
Status: ACTIVE - Sprint 107 (GREEN Phase Implementation)
Authority: Backend Lead + CTO Approved
Foundation: Test Strategy 2026, TDD Iron Law
Framework: SDLC 5.3.0 Complete Lifecycle

Purpose:
- Quality gate CRUD operations (create, read, update, delete)
- Gate lifecycle management (DRAFT → PENDING → APPROVED/REJECTED)
- Multi-stage gate support (G0.1, G0.2, G1, G2...G9)
- Evidence attachment and validation

TDD Compliance:
- Test-First: All 12 tests written before implementation
- RED → GREEN → REFACTOR workflow
- 100% coverage target for core business logic

Design References:
- Data Model: docs/01-planning/03-Data-Model/Database-Schema.md
- FR1: docs/01-planning/01-Requirements/Functional-Requirements-Document.md
- Test Stubs: backend/tests/services/test_gate_service.py
- Test Factory: backend/tests/factories/gate_factory.py

Zero Mock Policy: Real SQLAlchemy operations (no mocks in production)
=========================================================================
"""

import logging
from datetime import datetime, UTC
from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.gate import Gate
from app.models.gate_evidence import GateEvidence
from app.models.project import Project
from app.models.user import User
from app.schemas.gate import GateStatus, VALID_TRANSITIONS

logger = logging.getLogger(__name__)


# ============================================================================
# Custom Exceptions
# ============================================================================


class GateServiceError(Exception):
    """Base exception for gate service errors."""
    pass


class GateNotFoundError(GateServiceError):
    """Exception raised when gate is not found."""
    pass


class InvalidGateCodeError(GateServiceError):
    """Exception raised when gate code is invalid."""
    pass


class GateValidationError(GateServiceError):
    """Exception raised when gate validation fails."""
    pass


class InvalidTransitionError(GateServiceError):
    """Exception raised when a gate state transition is not allowed (Sprint 173 — ADR-053)."""

    def __init__(self, action: str, current_status: str, allowed_from: set):
        self.action = action
        self.current_status = current_status
        self.allowed_from = allowed_from
        super().__init__(
            f"Cannot {action} gate from status: {current_status}. "
            f"Allowed from: {', '.join(s.value if hasattr(s, 'value') else str(s) for s in allowed_from)}"
        )


# ============================================================================
# Sprint 173: Shared Gate Actions Computation (ADR-053 — SSOT Invariant)
# ============================================================================


# Roles that map to governance:approve scope
APPROVER_ROLES = {"cto", "cpo", "ceo", "CTO", "CPO", "CEO"}


def _user_has_approve_scope(user: User) -> bool:
    """Check if user has governance:approve scope (mapped to RBAC roles)."""
    if not hasattr(user, "roles") or not user.roles:
        return False
    user_role_names = {r.name.lower() for r in user.roles}
    return bool(user_role_names & {r.lower() for r in APPROVER_ROLES})


async def compute_gate_actions(
    gate: Gate,
    user: User,
    db: AsyncSession,
) -> Dict[str, Any]:
    """
    Compute available gate actions for a user (Sprint 173 — ADR-053).

    SSOT Invariant: This function is used by BOTH GET /gates/{id}/actions
    AND all mutation endpoints. What this function reports is exactly what
    mutations enforce.

    Args:
        gate: Gate model instance
        user: Current authenticated user
        db: Database session

    Returns:
        Dict with actions, reasons, evidence status
    """
    current_status = gate.status
    actions = {
        "can_evaluate": False,
        "can_submit": False,
        "can_approve": False,
        "can_reject": False,
        "can_upload_evidence": False,
    }
    reasons: Dict[str, str] = {}

    has_approve_scope = _user_has_approve_scope(user)

    # --- evaluate ---
    evaluate_rule = VALID_TRANSITIONS["evaluate"]
    if current_status in {s.value for s in evaluate_rule["allowed_from"]}:
        actions["can_evaluate"] = True
    else:
        reasons["can_evaluate"] = f"Cannot evaluate from status: {current_status}"

    # --- submit ---
    submit_rule = VALID_TRANSITIONS["submit"]
    if current_status in {s.value for s in submit_rule["allowed_from"]}:
        actions["can_submit"] = True
    else:
        reasons["can_submit"] = (
            f"Gate must be EVALUATED to submit (current: {current_status})"
        )

    # --- approve ---
    approve_rule = VALID_TRANSITIONS["approve"]
    if current_status in {s.value for s in approve_rule["allowed_from"]} and has_approve_scope:
        actions["can_approve"] = True
    else:
        if not has_approve_scope:
            reasons["can_approve"] = "Missing required scope: governance:approve"
        else:
            reasons["can_approve"] = (
                f"Gate must be SUBMITTED to approve (current: {current_status})"
            )

    # --- reject ---
    reject_rule = VALID_TRANSITIONS["reject"]
    if current_status in {s.value for s in reject_rule["allowed_from"]} and has_approve_scope:
        actions["can_reject"] = True
    else:
        if not has_approve_scope:
            reasons["can_reject"] = "Missing required scope: governance:approve"
        else:
            reasons["can_reject"] = (
                f"Gate must be SUBMITTED to reject (current: {current_status})"
            )

    # --- evidence upload ---
    # Allowed from any status except APPROVED and ARCHIVED
    if current_status not in (GateStatus.APPROVED.value, GateStatus.ARCHIVED.value):
        actions["can_upload_evidence"] = True
    else:
        reasons["can_upload_evidence"] = (
            f"Cannot upload evidence for {current_status} gate"
        )

    # --- evidence status ---
    required_evidence: List[str] = []
    submitted_evidence_types: List[str] = []

    # Extract required evidence types from exit criteria
    if gate.exit_criteria:
        for criterion in gate.exit_criteria:
            if isinstance(criterion, dict):
                ev_type = criterion.get("evidence_type") or criterion.get("id", "")
                if ev_type:
                    required_evidence.append(ev_type)

    # Query submitted evidence types
    if required_evidence:
        result = await db.execute(
            select(GateEvidence.evidence_type)
            .where(
                GateEvidence.gate_id == gate.id,
                GateEvidence.deleted_at.is_(None),
            )
            .distinct()
        )
        submitted_evidence_types = [row[0] for row in result.all()]

    missing_evidence = [
        e for e in required_evidence if e not in submitted_evidence_types
    ]

    # Block submit if missing evidence (SDLC Expert v2 fix)
    if actions["can_submit"] and missing_evidence:
        actions["can_submit"] = False
        reasons["can_submit"] = (
            f"Cannot submit: missing required evidence: {', '.join(missing_evidence)}"
        )

    return {
        "gate_id": gate.id,
        "status": current_status,
        "actions": actions,
        "reasons": reasons,
        "required_evidence": required_evidence,
        "submitted_evidence": submitted_evidence_types,
        "missing_evidence": missing_evidence,
    }


def validate_transition(action: str, current_status: str) -> str:
    """
    Validate a gate state transition and return target status (Sprint 173).

    Args:
        action: Transition action (evaluate, submit, approve, reject)
        current_status: Current gate status string

    Returns:
        Target status value

    Raises:
        InvalidTransitionError: If transition is not allowed
    """
    rule = VALID_TRANSITIONS.get(action)
    if not rule:
        raise GateServiceError(f"Unknown action: {action}")

    allowed_values = {s.value for s in rule["allowed_from"]}
    if current_status not in allowed_values:
        raise InvalidTransitionError(action, current_status, rule["allowed_from"])

    return rule["target"].value


# ============================================================================
# Gate Service
# ============================================================================


# Valid gate codes (SDLC 5.3.0)
VALID_GATE_CODES = [
    "G0.1",  # Foundation Ready (WHY stage)
    "G0.2",  # Solution Diversity (WHY stage)
    "G1",    # Design Ready (WHAT stage)
    "G2",    # Ship Ready (HOW stage)
    "G3",    # Build Complete (BUILD stage)
    "G4",    # Test Complete (TEST stage)
    "G5",    # Deploy Ready (DEPLOY stage)
    "G6",    # Operate Ready (OPERATE stage)
    "G7",    # Integration Complete (INTEGRATE stage)
    "G8",    # Collaboration Ready (COLLABORATE stage)
    "G9",    # Governance Complete (GOVERN stage)
]

# Gate code to stage mapping
GATE_CODE_TO_STAGE = {
    "G0.1": "WHY",
    "G0.2": "WHY",
    "G1": "WHAT",
    "G2": "HOW",
    "G3": "BUILD",
    "G4": "TEST",
    "G5": "DEPLOY",
    "G6": "OPERATE",
    "G7": "INTEGRATE",
    "G8": "COLLABORATE",
    "G9": "GOVERN",
}


class GateService:
    """
    Service for managing quality gates (FR1).

    Responsibilities:
        - Gate CRUD operations
        - Gate lifecycle management
        - Exit criteria validation
        - Multi-approver workflow support

    Usage:
        gate_service = GateService(db_session)
        gate = await gate_service.create_gate(project_id, gate_code, data)
        await gate_service.approve_gate(gate_id, approver_id, comment)
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize GateService.

        Args:
            db: SQLAlchemy async database session
        """
        self.db = db

    # ========================================================================
    # CREATE Operations
    # ========================================================================

    async def create_gate(
        self,
        project_id: UUID,
        gate_code: str,
        gate_name: str,
        created_by: UUID,
        description: Optional[str] = None,
        exit_criteria: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> Gate:
        """
        Create a new quality gate.

        TDD: Implements test_create_gate_g01_success, test_create_gate_g2_with_architecture_review

        Args:
            project_id: Project UUID
            gate_code: Gate code (G0.1, G0.2, G1...G9)
            gate_name: Human-readable gate name
            created_by: User UUID who created the gate
            description: Optional gate description
            exit_criteria: Optional list of exit criteria
            **kwargs: Additional gate-specific fields

        Returns:
            Created Gate instance

        Raises:
            InvalidGateCodeError: If gate_code is invalid
            GateValidationError: If validation fails
        """
        # Validate gate code
        if gate_code not in VALID_GATE_CODES:
            raise InvalidGateCodeError(
                f"Invalid gate code: {gate_code}. "
                f"Valid codes: {', '.join(VALID_GATE_CODES)}"
            )

        # Determine stage from gate code
        stage = GATE_CODE_TO_STAGE[gate_code]

        # Create gate instance
        gate = Gate(
            project_id=project_id,
            gate_type=gate_code,  # Store gate code in gate_type field
            gate_name=gate_name,
            stage=stage,
            created_by=created_by,
            status="DRAFT",
            description=description,
            exit_criteria=exit_criteria or [],
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        # Add gate-specific fields
        for key, value in kwargs.items():
            if hasattr(gate, key):
                setattr(gate, key, value)

        # Save to database
        self.db.add(gate)
        await self.db.commit()
        await self.db.refresh(gate)

        logger.info(
            f"Gate created: {gate.gate_name} ({gate.gate_type}) "
            f"for project {project_id}"
        )

        return gate

    # ========================================================================
    # READ Operations
    # ========================================================================

    async def get_gate_by_id(self, gate_id: UUID) -> Optional[Gate]:
        """
        Retrieve gate by ID.

        TDD: Implements test_get_gate_by_id_success, test_get_gate_by_id_not_found

        Args:
            gate_id: Gate UUID

        Returns:
            Gate instance if found, None otherwise
        """
        stmt = select(Gate).where(
            and_(
                Gate.id == gate_id,
                Gate.deleted_at.is_(None)  # Exclude soft-deleted gates
            )
        )
        result = await self.db.execute(stmt)
        gate = result.scalar_one_or_none()

        if gate:
            logger.debug(f"Gate retrieved: {gate.gate_name} ({gate.id})")
        else:
            logger.debug(f"Gate not found: {gate_id}")

        return gate

    async def list_gates_by_project(
        self,
        project_id: UUID,
        status: Optional[str] = None
    ) -> List[Gate]:
        """
        List all gates for a project.

        TDD: Implements test_list_gates_by_project_success

        Args:
            project_id: Project UUID
            status: Optional status filter (DRAFT, PENDING_APPROVAL, APPROVED, REJECTED)

        Returns:
            List of Gate instances ordered by gate_type (G0.1, G0.2, G1...)
        """
        conditions = [
            Gate.project_id == project_id,
            Gate.deleted_at.is_(None)
        ]

        if status:
            conditions.append(Gate.status == status)

        stmt = (
            select(Gate)
            .where(and_(*conditions))
            .order_by(Gate.gate_type)  # G0.1, G0.2, G1, G2...
        )

        result = await self.db.execute(stmt)
        gates = result.scalars().all()

        logger.debug(
            f"Listed {len(gates)} gates for project {project_id}"
            + (f" with status {status}" if status else "")
        )

        return list(gates)

    # ========================================================================
    # UPDATE Operations
    # ========================================================================

    async def update_gate_status(
        self,
        gate_id: UUID,
        status: str,
        **timestamps
    ) -> Gate:
        """
        Update gate status.

        TDD: Implements test_update_gate_status_to_passed

        Args:
            gate_id: Gate UUID
            status: New status (DRAFT, PENDING_APPROVAL, APPROVED, REJECTED)
            **timestamps: Optional timestamps (passed_at, rejected_at, etc.)

        Returns:
            Updated Gate instance

        Raises:
            GateNotFoundError: If gate not found
        """
        gate = await self.get_gate_by_id(gate_id)
        if not gate:
            raise GateNotFoundError(f"Gate not found: {gate_id}")

        # Update status
        gate.status = status
        gate.updated_at = datetime.now(UTC)

        # Update timestamps
        for key, value in timestamps.items():
            if hasattr(gate, key):
                setattr(gate, key, value)

        await self.db.commit()
        await self.db.refresh(gate)

        logger.info(f"Gate status updated: {gate.gate_name} → {status}")

        return gate

    async def approve_gate(
        self,
        gate_id: UUID,
        approver_id: UUID,
        approval_comment: Optional[str] = None
    ) -> Gate:
        """
        Approve a gate.

        TDD: Implements test_approve_gate_with_approver_data

        Args:
            gate_id: Gate UUID
            approver_id: User UUID who approved
            approval_comment: Optional approval comment

        Returns:
            Updated Gate instance

        Raises:
            GateNotFoundError: If gate not found
        """
        gate = await self.get_gate_by_id(gate_id)
        if not gate:
            raise GateNotFoundError(f"Gate not found: {gate_id}")

        # Update gate
        gate.status = "APPROVED"
        gate.approved_at = datetime.now(UTC)
        gate.updated_at = datetime.now(UTC)

        # Store approver info (if fields exist in model)
        if hasattr(gate, 'approver_id'):
            gate.approver_id = approver_id
        if hasattr(gate, 'approval_comment') and approval_comment:
            gate.approval_comment = approval_comment

        await self.db.commit()
        await self.db.refresh(gate)

        logger.info(
            f"Gate approved: {gate.gate_name} by user {approver_id}"
        )

        return gate

    async def reject_gate(
        self,
        gate_id: UUID,
        approver_id: UUID,
        rejection_reason: str
    ) -> Gate:
        """
        Reject a gate.

        TDD: Implements test_reject_gate_with_reason

        Args:
            gate_id: Gate UUID
            approver_id: User UUID who rejected
            rejection_reason: Reason for rejection (required)

        Returns:
            Updated Gate instance

        Raises:
            GateNotFoundError: If gate not found
            GateValidationError: If rejection_reason is empty
        """
        if not rejection_reason or not rejection_reason.strip():
            raise GateValidationError("Rejection reason is required")

        gate = await self.get_gate_by_id(gate_id)
        if not gate:
            raise GateNotFoundError(f"Gate not found: {gate_id}")

        # Update gate
        gate.status = "REJECTED"
        gate.rejected_at = datetime.now(UTC)
        gate.updated_at = datetime.now(UTC)

        # Store rejection info (if fields exist in model)
        if hasattr(gate, 'approver_id'):
            gate.approver_id = approver_id
        if hasattr(gate, 'rejection_reason'):
            gate.rejection_reason = rejection_reason

        await self.db.commit()
        await self.db.refresh(gate)

        logger.info(
            f"Gate rejected: {gate.gate_name} by user {approver_id}. "
            f"Reason: {rejection_reason}"
        )

        return gate

    # ========================================================================
    # DELETE Operations
    # ========================================================================

    async def delete_gate(
        self,
        gate_id: UUID,
        cascade: bool = False
    ) -> bool:
        """
        Soft delete a gate.

        TDD: Implements test_delete_gate_success, test_delete_gate_with_evidence_cascade

        Args:
            gate_id: Gate UUID
            cascade: If True, also soft delete related evidence

        Returns:
            True if deleted successfully

        Raises:
            GateNotFoundError: If gate not found
        """
        gate = await self.get_gate_by_id(gate_id)
        if not gate:
            raise GateNotFoundError(f"Gate not found: {gate_id}")

        # Soft delete gate
        gate.deleted_at = datetime.now(UTC)
        gate.updated_at = datetime.now(UTC)

        # Cascade delete evidence if requested
        if cascade and hasattr(gate, 'evidence'):
            for evidence in gate.evidence:
                evidence.deleted_at = datetime.now(UTC)
                evidence.updated_at = datetime.now(UTC)

        await self.db.commit()

        logger.info(
            f"Gate deleted: {gate.gate_name} "
            + ("with cascade" if cascade else "")
        )

        return True
