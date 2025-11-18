"""
=========================================================================
Evidence Pydantic Schemas - Request/Response Models
SDLC Orchestrator - Stage 03 (BUILD)

Version: 1.0.0
Date: November 17, 2025
Status: ACTIVE - Week 3 Day 4 API Implementation
Authority: Backend Lead + CTO Approved
Foundation: FR2 (Evidence Vault), Data Model v0.1
Framework: SDLC 4.9 Complete Lifecycle

Purpose:
- Evidence upload request/response schemas
- Evidence metadata response schemas
- Evidence integrity check schemas
- Evidence list/filter schemas

Evidence Types:
- DESIGN_DOCUMENT: Architecture diagrams, data models, API specs
- TEST_RESULTS: Unit test, integration test, performance test results
- CODE_REVIEW: Code review reports, static analysis results
- DEPLOYMENT_PROOF: Deployment logs, production screenshots
- DOCUMENTATION: README, user guides, technical docs
- COMPLIANCE: Security scans, license audits, GDPR compliance

Zero Mock Policy: Production-ready Pydantic v2 schemas
=========================================================================
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class EvidenceUploadRequest(BaseModel):
    """
    Evidence upload request schema.

    Request Body (multipart/form-data):
        - file: Binary file upload
        - gate_id: Gate UUID
        - evidence_type: Evidence category
        - description: Optional description

    Validation:
        - file_size: Max 100MB (configurable)
        - allowed_types: pdf, md, png, jpg, json, txt, csv, etc.
        - evidence_type: Must be valid enum
    """

    gate_id: UUID = Field(..., description="Gate UUID")
    evidence_type: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Evidence type (DESIGN_DOCUMENT, TEST_RESULTS, etc.)",
    )
    description: Optional[str] = Field(None, max_length=1000, description="Evidence description")

    @field_validator("evidence_type")
    @classmethod
    def validate_evidence_type(cls, v: str) -> str:
        """Validate evidence type is allowed"""
        allowed_types = {
            "DESIGN_DOCUMENT",
            "TEST_RESULTS",
            "CODE_REVIEW",
            "DEPLOYMENT_PROOF",
            "DOCUMENTATION",
            "COMPLIANCE",
        }
        if v.upper() not in allowed_types:
            raise ValueError(
                f"Invalid evidence_type '{v}'. Allowed: {', '.join(allowed_types)}"
            )
        return v.upper()


class EvidenceResponse(BaseModel):
    """
    Evidence metadata response schema.

    Response (200 OK):
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "gate_id": "...",
            "file_name": "data-model-v0.1.md",
            "file_size": 1400000,
            "file_size_mb": 1.4,
            "file_type": "text/markdown",
            "evidence_type": "DESIGN_DOCUMENT",
            "sha256_hash": "abc123...",
            "description": "Data Model v0.1 - PostgreSQL schema",
            "uploaded_by": "...",
            "uploaded_by_name": "Nguyễn Văn Anh",
            "uploaded_at": "2025-11-17T10:30:00Z",
            "s3_url": "s3://sdlc-evidence/evidence/gate-123/file-456.md",
            "download_url": "/api/v1/evidence/550e8400-e29b-41d4-a716-446655440000/download",
            "integrity_status": "valid",
            "last_integrity_check": "2025-11-17T11:00:00Z"
        }
    """

    id: UUID
    gate_id: UUID
    file_name: str
    file_size: int
    file_size_mb: float
    file_type: str
    evidence_type: str
    sha256_hash: str
    description: Optional[str]
    uploaded_by: UUID
    uploaded_by_name: str
    uploaded_at: datetime
    s3_url: str
    download_url: str
    integrity_status: str  # 'valid', 'failed', 'pending'
    last_integrity_check: Optional[datetime]

    model_config = {"from_attributes": True}


class EvidenceListResponse(BaseModel):
    """
    Evidence list response schema with pagination.

    Response (200 OK):
        {
            "items": [
                {"id": "...", "file_name": "data-model-v0.1.md", ...}
            ],
            "total": 15,
            "page": 1,
            "page_size": 20,
            "pages": 1
        }
    """

    items: List[EvidenceResponse]
    total: int
    page: int
    page_size: int
    pages: int


class IntegrityCheckRequest(BaseModel):
    """
    Integrity check request schema.

    Request Body:
        {
            "force": false
        }

    Validation:
        - force: If True, bypass cache and recompute hash from S3
    """

    force: bool = Field(False, description="Force recompute hash from S3 (bypass cache)")


class IntegrityCheckResponse(BaseModel):
    """
    Integrity check response schema.

    Response (200 OK):
        {
            "evidence_id": "...",
            "file_name": "data-model-v0.1.md",
            "is_valid": true,
            "original_hash": "abc123...",
            "current_hash": "abc123...",
            "checked_at": "2025-11-17T11:00:00Z",
            "checked_by": "user-123",
            "error_message": null
        }

    Response (200 OK - Tampered):
        {
            "evidence_id": "...",
            "file_name": "data-model-v0.1.md",
            "is_valid": false,
            "original_hash": "abc123...",
            "current_hash": "def456...",
            "checked_at": "2025-11-17T11:00:00Z",
            "checked_by": "user-123",
            "error_message": "Hash mismatch! File has been tampered or corrupted."
        }
    """

    evidence_id: UUID
    file_name: str
    is_valid: bool
    original_hash: str
    current_hash: str
    checked_at: datetime
    checked_by: str
    error_message: Optional[str]


class IntegrityCheckHistoryResponse(BaseModel):
    """
    Integrity check history response schema.

    Response (200 OK):
        {
            "evidence_id": "...",
            "file_name": "data-model-v0.1.md",
            "checks": [
                {
                    "id": "...",
                    "checked_at": "2025-11-17T11:00:00Z",
                    "is_valid": true,
                    "checked_by": "system-cron"
                },
                {
                    "id": "...",
                    "checked_at": "2025-11-17T10:00:00Z",
                    "is_valid": true,
                    "checked_by": "user-123"
                }
            ],
            "total_checks": 25,
            "failed_checks": 0,
            "success_rate": 100.0
        }
    """

    evidence_id: UUID
    file_name: str
    checks: List[dict]
    total_checks: int
    failed_checks: int
    success_rate: float
