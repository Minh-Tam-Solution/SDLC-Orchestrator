"""
Policy Schemas - OPA Policy Library

SDLC Stage: 04 - BUILD
Sprint: 43 - Policy Guards & Evidence UI
Framework: SDLC 5.1.1 (10-Stage Lifecycle, 4-Tier Classification)
Epic: EP-02 AI Safety Layer v1

Purpose:
- Policy library request/response schemas
- Policy evaluation request/response schemas
- Custom policy schemas
- Policy test case schemas

Policy Types:
- Pre-built policies: 110+ policies for all 10 SDLC stages (00-09)
- Custom policies: Project-specific policy customizations
- Policy tests: Test cases for policy validation

SDLC 5.1.1 Stages:
- 00-foundation (WHY?)
- 01-planning (WHAT?)
- 02-design (HOW?)
- 03-integrate (How connect?)
- 04-build (Building right?)
- 05-test (Works correctly?)
- 06-deploy (Ship safely?)
- 07-operate (Running reliably?)
- 08-collaborate (Team effective?)
- 09-govern (Compliant?)

Version: 2.0.0
Updated: December 2025
Zero Mock Policy: Production-ready Pydantic v2 schemas
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class PolicyResponse(BaseModel):
    """
    Policy response schema.

    Response (200 OK):
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "policy_name": "FRD Completeness Check",
            "policy_code": "FRD_COMPLETENESS",
            "stage": "WHAT",
            "description": "Verify FRD has all required sections",
            "rego_code": "package sdlc.what.frd_completeness ...",
            "severity": "ERROR",
            "is_active": true,
            "version": "1.0.0",
            "created_at": "2025-11-18T10:00:00Z",
            "updated_at": "2025-11-18T10:00:00Z"
        }
    """

    id: UUID
    policy_name: str
    policy_code: str
    stage: str
    description: str
    rego_code: str
    severity: str  # 'INFO', 'WARNING', 'ERROR', 'CRITICAL'
    is_active: bool
    version: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PolicyUpdate(BaseModel):
    """
    Policy update request schema.

    Request Body:
        {
            "policy_name": "Updated Policy Name",
            "description": "Updated description",
            "rego_code": "package updated...",
            "severity": "ERROR",
            "is_active": true,
            "version": "1.0.1"
        }
    """

    policy_name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    rego_code: Optional[str] = Field(None, min_length=1)
    severity: Optional[str] = Field(None, pattern="^(INFO|WARNING|ERROR|CRITICAL)$")
    is_active: Optional[bool] = None
    version: Optional[str] = Field(None, pattern=r"^\d+\.\d+\.\d+$")


class PolicyListResponse(BaseModel):
    """
    Policy list response schema with pagination.

    Response (200 OK):
        {
            "items": [
                {"id": "...", "policy_name": "FRD Completeness Check", ...}
            ],
            "total": 110,
            "page": 1,
            "page_size": 20,
            "pages": 6
        }
    """

    items: List[PolicyResponse]
    total: int
    page: int
    page_size: int
    pages: int


class PolicyEvaluationRequest(BaseModel):
    """
    Policy evaluation request schema.

    Request Body:
        {
            "gate_id": "550e8400-e29b-41d4-a716-446655440000",
            "policy_id": "660e8400-e29b-41d4-a716-446655440000",
            "input_data": {
                "frd_sections": {
                    "Introduction": true,
                    "Functional Requirements": true,
                    "API Contracts": false
                }
            }
        }

    Validation:
        - gate_id: Must be valid UUID
        - policy_id: Must be valid UUID
        - input_data: JSON object for OPA evaluation
    """

    gate_id: UUID = Field(..., description="Gate UUID")
    policy_id: UUID = Field(..., description="Policy UUID")
    input_data: dict = Field(..., description="Input data for OPA policy evaluation")


class PolicyEvaluationResponse(BaseModel):
    """
    Policy evaluation response schema.

    Response (200 OK - Policy Passed):
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "gate_id": "...",
            "policy_id": "...",
            "policy_name": "FRD Completeness Check",
            "result": "pass",
            "violations": [],
            "evaluated_at": "2025-11-18T10:30:00Z",
            "evaluated_by": "user-123"
        }

    Response (200 OK - Policy Failed):
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "gate_id": "...",
            "policy_id": "...",
            "policy_name": "FRD Completeness Check",
            "result": "fail",
            "violations": [
                "FRD missing required section: API Contracts"
            ],
            "evaluated_at": "2025-11-18T10:30:00Z",
            "evaluated_by": "user-123"
        }
    """

    id: UUID
    gate_id: UUID
    policy_id: UUID
    policy_name: str
    result: str  # 'pass', 'fail'
    violations: List[str]
    evaluated_at: datetime
    evaluated_by: str

    model_config = {"from_attributes": True}


class PolicyEvaluationListResponse(BaseModel):
    """
    Policy evaluation list response schema.

    Response (200 OK):
        {
            "items": [
                {"id": "...", "policy_name": "FRD Completeness Check", "result": "pass", ...}
            ],
            "total": 15,
            "passed": 12,
            "failed": 3,
            "pass_rate": 80.0
        }
    """

    items: List[PolicyEvaluationResponse]
    total: int
    passed: int
    failed: int
    pass_rate: float
