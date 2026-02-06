"""
Tier Approval Schemas - Sprint 161

Pydantic schemas for tier-based gate approval system.

CTO v2.5 Adjustment #3:
- ApprovalChainMetadata dataclass (return type for create_approval_request)
- Includes chain_id, decision_ids, required_roles, expires_at, is_self_approval

Reference: docs/04-build/02-Sprint-Plans/SPRINT-161-164-TIER-BASED-GATE-APPROVAL.md
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict
from dataclasses import dataclass


# =====================================================================
# ENUMS
# =====================================================================

class ProjectTier(str):
    """Project tier for approval routing."""
    FREE = "FREE"
    STANDARD = "STANDARD"
    PROFESSIONAL = "PROFESSIONAL"
    ENTERPRISE = "ENTERPRISE"


class FunctionalRole(str):
    """Functional roles for approval authority."""
    PM = "PM"
    CTO = "CTO"
    CEO = "CEO"
    QA_LEAD = "QA_LEAD"
    COMPLIANCE_OFFICER = "COMPLIANCE_OFFICER"


class DecisionAction(str):
    """Decision action types."""
    REQUEST = "REQUEST"
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    ESCALATE = "ESCALATE"  # CTO v2.5 adjustment #1
    COMMENT = "COMMENT"


class DecisionStatus(str):
    """Decision status types."""
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


# =====================================================================
# PROJECT FUNCTION ROLE SCHEMAS
# =====================================================================

class ProjectFunctionRoleBase(BaseModel):
    """Base schema for project function role."""
    project_id: UUID
    user_id: UUID
    functional_role: str = Field(..., description="Functional role (PM/CTO/CEO/QA_LEAD/COMPLIANCE_OFFICER)")


class ProjectFunctionRoleCreate(ProjectFunctionRoleBase):
    """Schema for creating project function role."""
    assigned_by: Optional[UUID] = Field(None, description="User who assigned this role")


class ProjectFunctionRoleUpdate(BaseModel):
    """Schema for updating project function role."""
    functional_role: Optional[str] = Field(None, description="Functional role (PM/CTO/CEO/QA_LEAD/COMPLIANCE_OFFICER)")


class ProjectFunctionRoleResponse(ProjectFunctionRoleBase):
    """Schema for project function role response."""
    id: UUID
    assigned_at: datetime
    assigned_by: Optional[UUID] = None

    model_config = ConfigDict(from_attributes=True)


# =====================================================================
# GATE DECISION SCHEMAS
# =====================================================================

class GateDecisionBase(BaseModel):
    """Base schema for gate decision."""
    gate_id: UUID
    project_id: UUID
    action: str = Field(..., description="Decision action (REQUEST/APPROVE/REJECT/ESCALATE/COMMENT)")
    chain_id: UUID = Field(..., description="Groups related decisions (council review)")
    step_index: int = Field(default=0, ge=0, description="Sequential step in approval chain (0-based)")
    required_roles: List[str] = Field(..., description="Roles required at this step")


class GateDecisionCreate(GateDecisionBase):
    """Schema for creating gate decision."""
    actor_id: UUID
    comments: Optional[str] = None
    evidence_ids: Optional[List[UUID]] = None
    expires_at: Optional[datetime] = None  # CTO v2.5 adjustment #2


class GateDecisionUpdate(BaseModel):
    """Schema for updating gate decision."""
    action: Optional[str] = Field(None, description="Decision action")
    status: Optional[str] = Field(None, description="Decision status (PENDING/COMPLETED/CANCELLED)")
    comments: Optional[str] = None
    evidence_ids: Optional[List[UUID]] = None
    completed_at: Optional[datetime] = None


class GateDecisionResponse(GateDecisionBase):
    """Schema for gate decision response."""
    id: UUID
    actor_id: UUID
    status: str
    comments: Optional[str] = None
    evidence_ids: Optional[List[UUID]] = None
    created_at: datetime
    expires_at: Optional[datetime] = None  # CTO v2.5 adjustment #2
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# =====================================================================
# APPROVAL CHAIN METADATA (CTO v2.5 Adjustment #3)
# =====================================================================

@dataclass
class ApprovalChainMetadata:
    """
    Metadata for created approval chain.

    CTO v2.5 Adjustment #3:
    - Service method returns this dataclass instead of List[UUID]
    - Provides rich context about created approval chain

    Attributes:
        chain_id: UUID grouping related decisions
        decision_ids: List of created decision record IDs
        required_roles: List of functional roles required for approval
        expires_at: When decisions expire (for timeout/escalation)
        is_self_approval: Whether this was a self-approval case (FREE tier)

    Example:
        >>> metadata = ApprovalChainMetadata(
        ...     chain_id=uuid4(),
        ...     decision_ids=[uuid1, uuid2],
        ...     required_roles=['CTO', 'CEO'],
        ...     expires_at=datetime.utcnow() + timedelta(hours=48),
        ...     is_self_approval=False
        ... )
    """
    chain_id: UUID
    decision_ids: List[UUID]
    required_roles: List[str]
    expires_at: Optional[datetime]
    is_self_approval: bool


# =====================================================================
# REQUEST/RESPONSE SCHEMAS (API Layer)
# =====================================================================

class CreateApprovalRequestRequest(BaseModel):
    """Schema for creating approval request."""
    gate_id: UUID = Field(..., description="Gate requiring approval")


class CreateApprovalRequestResponse(BaseModel):
    """Schema for approval request response."""
    chain_id: UUID
    decision_ids: List[UUID]
    required_roles: List[str]
    expires_at: Optional[datetime]
    is_self_approval: bool
    message: str

    model_config = ConfigDict(from_attributes=True)


class RecordDecisionRequest(BaseModel):
    """Schema for recording approval/rejection decision."""
    decision_id: UUID = Field(..., description="Decision record ID")
    action: str = Field(..., description="Decision action (APPROVE/REJECT)")
    comments: Optional[str] = Field(None, description="Decision comments")
    evidence_ids: Optional[List[UUID]] = Field(None, description="Evidence IDs supporting decision")


class RecordDecisionResponse(BaseModel):
    """Schema for decision record response."""
    decision_id: UUID
    action: str
    status: str
    completed_at: Optional[datetime]
    message: str

    model_config = ConfigDict(from_attributes=True)


# =====================================================================
# TIER CONFIG SCHEMAS (Sprint 162 - Preview)
# =====================================================================

class TierApprovalRulesResponse(BaseModel):
    """Schema for tier approval rules (read-only)."""
    tier: str
    gate_code: str
    required_roles: List[str]
    allow_self_approval: bool

    model_config = ConfigDict(from_attributes=True)
