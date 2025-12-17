"""
=========================================================================
Gate Schemas - Quality Gate Request/Response Models
SDLC Orchestrator - Stage 03 (BUILD)

Version: 1.0.0
Date: November 28, 2025
Status: ACTIVE - Week 3 Day 3 API Implementation
Authority: Backend Lead + CTO Approved
Foundation: OpenAPI 3.0, Pydantic v2, FR1 (Quality Gate Management)
Framework: SDLC 4.9 Complete Lifecycle

Purpose:
- Gate CRUD request/response models
- Gate approval workflow schemas
- Gate evidence attachment schemas
- Gate policy evaluation schemas

Validation:
- Gate name format (e.g., G0.1, G1, G2)
- Stage validation (WHY, WHAT, BUILD, etc.)
- Status validation (DRAFT, PENDING_APPROVAL, APPROVED, REJECTED)

Zero Mock Policy: Production-ready Pydantic models
=========================================================================
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, Field


# =========================================================================
# Gate CRUD Schemas
# =========================================================================


class GateCreateRequest(BaseModel):
    """
    Create new quality gate request.

    Request Body:
        {
            "project_id": "550e8400-e29b-41d4-a716-446655440000",
            "gate_name": "G2",
            "gate_type": "SHIP_READY",
            "stage": "SHIP",
            "description": "G2 (Ship Ready) - Production deployment approval",
            "exit_criteria": [
                {"criterion": "Zero P0 bugs", "status": "pending"},
                {"criterion": "95%+ test coverage", "status": "pending"},
                {"criterion": "Security scan passed", "status": "pending"}
            ]
        }

    Validation:
        - gate_name: Required (e.g., G0.1, G1, G2)
        - stage: Must be valid SDLC 4.9 stage (WHY, WHAT, BUILD, TEST, SHIP, etc.)
        - project_id: Must exist in projects table
    """

    project_id: UUID = Field(..., description="Project UUID")
    gate_name: str = Field(..., min_length=1, max_length=255, description="Gate name (e.g., G0.1, G1, G2)")
    gate_type: str = Field(..., min_length=1, max_length=50, description="Gate type (e.g., FOUNDATION_READY, SHIP_READY)")
    stage: str = Field(..., min_length=1, max_length=20, description="SDLC stage (WHY, WHAT, BUILD, TEST, SHIP, etc.)")
    description: Optional[str] = Field(None, description="Gate description")
    exit_criteria: List[Dict[str, Any]] = Field(
        default_factory=list, description="List of exit criteria (JSONB)"
    )


class GateUpdateRequest(BaseModel):
    """
    Update existing gate request.

    Request Body:
        {
            "gate_name": "G2 (Updated)",
            "description": "Updated description",
            "exit_criteria": [
                {"criterion": "Zero P0 bugs", "status": "passed"},
                {"criterion": "95%+ test coverage", "status": "passed"},
                {"criterion": "Security scan passed", "status": "pending"}
            ]
        }

    Validation:
        - All fields optional (partial update supported)
        - Cannot update status via this endpoint (use submit/approve endpoints)
    """

    gate_name: Optional[str] = Field(None, min_length=1, max_length=255, description="Gate name")
    gate_type: Optional[str] = Field(None, min_length=1, max_length=50, description="Gate type")
    description: Optional[str] = Field(None, description="Gate description")
    exit_criteria: Optional[List[Dict[str, Any]]] = Field(None, description="Exit criteria (JSONB)")


class GateResponse(BaseModel):
    """
    Gate response model.

    Response Body:
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "project_id": "660e8400-e29b-41d4-a716-446655440001",
            "gate_name": "G2",
            "gate_type": "SHIP_READY",
            "stage": "SHIP",
            "status": "DRAFT",
            "description": "G2 (Ship Ready) - Production deployment approval",
            "exit_criteria": [
                {"criterion": "Zero P0 bugs", "status": "pending"}
            ],
            "created_by": "770e8400-e29b-41d4-a716-446655440002",
            "created_at": "2025-11-28T10:00:00Z",
            "updated_at": "2025-11-28T10:00:00Z",
            "approved_at": null,
            "approvals": [],
            "evidence_count": 0,
            "policy_violations": []
        }
    """

    id: UUID = Field(..., description="Gate UUID")
    project_id: UUID = Field(..., description="Project UUID")
    gate_name: str = Field(..., description="Gate name (e.g., G0.1, G1, G2)")
    gate_type: str = Field(..., description="Gate type")
    stage: str = Field(..., description="SDLC stage")
    status: str = Field(..., description="Gate status (DRAFT, PENDING_APPROVAL, APPROVED, REJECTED)")
    description: Optional[str] = Field(None, description="Gate description")
    exit_criteria: Union[List[Union[str, Dict[str, Any]]], Dict[str, Any]] = Field(..., description="Exit criteria (JSONB) - accepts list or dict formats for backward compatibility")
    created_by: Optional[UUID] = Field(None, description="Creator user UUID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    approved_at: Optional[datetime] = Field(None, description="Approval timestamp")
    deleted_at: Optional[datetime] = Field(None, description="Soft delete timestamp")

    # Related data (will be populated from relationships)
    approvals: List[Dict[str, Any]] = Field(default_factory=list, description="List of approvals")
    evidence_count: int = Field(default=0, description="Number of evidence files attached")
    policy_violations: List[Dict[str, Any]] = Field(default_factory=list, description="Policy evaluation violations")

    class Config:
        from_attributes = True  # Pydantic v2: Enable ORM mode


class GateListResponse(BaseModel):
    """
    Paginated gate list response.

    Response Body:
        {
            "items": [
                {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "gate_name": "G2",
                    "status": "APPROVED",
                    ...
                }
            ],
            "total": 9,
            "page": 1,
            "page_size": 20,
            "pages": 1
        }
    """

    items: List[GateResponse] = Field(..., description="List of gates")
    total: int = Field(..., description="Total number of gates")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")
    pages: int = Field(..., description="Total number of pages")


# =========================================================================
# Gate Approval Workflow Schemas
# =========================================================================


class GateSubmitRequest(BaseModel):
    """
    Submit gate for approval request.

    Request Body:
        {
            "message": "Submitting G2 for CTO/CPO approval. All exit criteria met."
        }

    Workflow:
        1. Gate status: DRAFT → PENDING_APPROVAL
        2. Policy evaluation triggered (OPA)
        3. If policies pass: CTO/CPO/CEO notified
        4. If policies fail: Gate rejected with violations
    """

    message: Optional[str] = Field(None, max_length=1000, description="Submission message")


class GateApprovalRequest(BaseModel):
    """
    Approve gate request (CTO, CPO, or CEO).

    Request Body:
        {
            "approved": true,
            "comments": "All exit criteria validated. Security scan passed. Approved for production deployment."
        }

    Validation:
        - approved: Boolean (true = approve, false = reject)
        - comments: Optional approval comments
    """

    approved: bool = Field(..., description="Approval decision (true = approve, false = reject)")
    comments: Optional[str] = Field(None, max_length=1000, description="Approval comments")


class GateApprovalResponse(BaseModel):
    """
    Gate approval record response.

    Response Body:
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "gate_id": "660e8400-e29b-41d4-a716-446655440001",
            "approved_by": "770e8400-e29b-41d4-a716-446655440002",
            "approved_by_name": "Hoàng Văn Em (CTO)",
            "approved_by_role": "CTO",
            "is_approved": true,
            "comments": "All exit criteria validated.",
            "approved_at": "2025-11-28T10:30:00Z"
        }
    """

    id: UUID = Field(..., description="Approval record UUID")
    gate_id: UUID = Field(..., description="Gate UUID")
    approved_by: UUID = Field(..., description="Approver user UUID")
    approved_by_name: str = Field(..., description="Approver full name + role")
    approved_by_role: str = Field(..., description="Approver role (CTO, CPO, CEO)")
    is_approved: bool = Field(..., description="Approval decision")
    comments: Optional[str] = Field(None, description="Approval comments")
    approved_at: datetime = Field(..., description="Approval timestamp")

    class Config:
        from_attributes = True  # Pydantic v2: Enable ORM mode


# =========================================================================
# Gate Evidence Schemas
# =========================================================================


class GateEvidenceUploadRequest(BaseModel):
    """
    Evidence upload request metadata.

    Request Body (multipart/form-data):
        {
            "gate_id": "550e8400-e29b-41d4-a716-446655440000",
            "evidence_type": "test_report",
            "description": "Pytest test results - 95.3% coverage",
            "file": <binary file data>
        }

    Upload Flow:
        1. Frontend: Upload file via multipart/form-data
        2. Backend: Validate file (size, type, virus scan)
        3. Backend: Upload to MinIO S3 (evidence/<gate_id>/<filename>)
        4. Backend: Calculate SHA256 hash (integrity check)
        5. Backend: Store metadata in gate_evidence table
        6. Backend: Return evidence UUID + download URL
    """

    gate_id: UUID = Field(..., description="Gate UUID")
    evidence_type: str = Field(..., min_length=1, max_length=50, description="Evidence type (e.g., test_report, design_doc)")
    description: Optional[str] = Field(None, max_length=1000, description="Evidence description")


class GateEvidenceResponse(BaseModel):
    """
    Evidence file response.

    Response Body:
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "gate_id": "660e8400-e29b-41d4-a716-446655440001",
            "evidence_type": "test_report",
            "file_name": "pytest-report-2025-11-28.html",
            "file_size": 245678,
            "file_hash": "a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3",
            "storage_path": "evidence/660e8400-e29b-41d4-a716-446655440001/pytest-report-2025-11-28.html",
            "download_url": "http://localhost:9000/sdlc-evidence/evidence/...",
            "uploaded_by": "770e8400-e29b-41d4-a716-446655440002",
            "uploaded_at": "2025-11-28T10:30:00Z"
        }
    """

    id: UUID = Field(..., description="Evidence UUID")
    gate_id: UUID = Field(..., description="Gate UUID")
    evidence_type: str = Field(..., description="Evidence type")
    file_name: str = Field(..., description="Original file name")
    file_size: int = Field(..., description="File size in bytes")
    file_hash: str = Field(..., description="SHA-256 file hash (integrity)")
    storage_path: str = Field(..., description="MinIO S3 storage path")
    download_url: str = Field(..., description="Temporary download URL")
    description: Optional[str] = Field(None, description="Evidence description")
    uploaded_by: UUID = Field(..., description="Uploader user UUID")
    uploaded_at: datetime = Field(..., description="Upload timestamp")

    class Config:
        from_attributes = True  # Pydantic v2: Enable ORM mode


# =========================================================================
# Gate Policy Evaluation Schemas
# =========================================================================


class PolicyEvaluationResponse(BaseModel):
    """
    Policy evaluation result response.

    Response Body:
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "gate_id": "660e8400-e29b-41d4-a716-446655440001",
            "policy_id": "770e8400-e29b-41d4-a716-446655440002",
            "policy_name": "Test Coverage Requirement",
            "is_passed": false,
            "violations": [
                {
                    "message": "Test coverage 87.3% is below required 95%",
                    "severity": "ERROR",
                    "location": "pytest-coverage-report.xml"
                }
            ],
            "evaluated_at": "2025-11-28T10:30:00Z"
        }
    """

    id: UUID = Field(..., description="Evaluation record UUID")
    gate_id: UUID = Field(..., description="Gate UUID")
    policy_id: Optional[UUID] = Field(None, description="Policy UUID")
    policy_name: str = Field(..., description="Policy name")
    is_passed: bool = Field(..., description="Evaluation result (true = passed)")
    violations: List[Dict[str, Any]] = Field(..., description="List of violations (if any)")
    evaluated_at: datetime = Field(..., description="Evaluation timestamp")

    class Config:
        from_attributes = True  # Pydantic v2: Enable ORM mode
