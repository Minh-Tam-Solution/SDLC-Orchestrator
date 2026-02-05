"""
=========================================================================
VCR (Version Controlled Resolution) Schemas
SDLC Orchestrator - Sprint 151 (SASE Artifacts Enhancement)

Version: 1.0.0
Date: March 4, 2026
Status: ACTIVE
Authority: CTO Approved
Framework: SDLC 6.0.3 SASE Methodology
Reference: SPEC-0024, ADR-048

Purpose:
Pydantic schemas for VCR API request/response validation.
=========================================================================
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class VCRStatus(str, Enum):
    """VCR lifecycle status."""

    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"


# =============================================================================
# Request Schemas
# =============================================================================


class VCRCreate(BaseModel):
    """Schema for creating a new VCR."""

    project_id: UUID = Field(..., description="Associated project ID")
    pr_number: Optional[int] = Field(None, description="GitHub PR number")
    pr_url: Optional[str] = Field(None, max_length=500, description="Full PR URL")
    title: str = Field(..., max_length=255, description="VCR title")
    problem_statement: str = Field(..., min_length=10, description="What problem was solved?")
    root_cause_analysis: Optional[str] = Field(None, description="Root cause (for bugs)")
    solution_approach: str = Field(..., min_length=10, description="How was it solved?")
    implementation_notes: Optional[str] = Field(None, description="Caveats, trade-offs")
    evidence_ids: List[UUID] = Field(default_factory=list, description="Linked evidence")
    adr_ids: List[UUID] = Field(default_factory=list, description="Linked ADRs")
    ai_generated_percentage: float = Field(
        default=0.0, ge=0.0, le=1.0, description="AI-generated code percentage"
    )
    ai_tools_used: List[str] = Field(
        default_factory=list, description="AI tools (Cursor, Copilot, etc.)"
    )
    ai_generation_details: Dict[str, Any] = Field(
        default_factory=dict, description="AI generation metadata"
    )

    @field_validator("ai_tools_used")
    @classmethod
    def validate_ai_tools(cls, v: List[str]) -> List[str]:
        """Validate AI tools list."""
        valid_tools = {
            "cursor", "copilot", "claude", "chatgpt", "cody",
            "tabnine", "amazon-q", "gemini", "windsurf", "other"
        }
        normalized = []
        for tool in v:
            tool_lower = tool.lower().strip()
            if tool_lower not in valid_tools:
                tool_lower = "other"
            normalized.append(tool_lower)
        return normalized


class VCRUpdate(BaseModel):
    """Schema for updating a VCR (draft only)."""

    title: Optional[str] = Field(None, max_length=255)
    problem_statement: Optional[str] = Field(None, min_length=10)
    root_cause_analysis: Optional[str] = None
    solution_approach: Optional[str] = Field(None, min_length=10)
    implementation_notes: Optional[str] = None
    evidence_ids: Optional[List[UUID]] = None
    adr_ids: Optional[List[UUID]] = None
    ai_generated_percentage: Optional[float] = Field(None, ge=0.0, le=1.0)
    ai_tools_used: Optional[List[str]] = None
    ai_generation_details: Optional[Dict[str, Any]] = None
    pr_number: Optional[int] = None
    pr_url: Optional[str] = Field(None, max_length=500)


class VCRRejectRequest(BaseModel):
    """Request for rejecting a VCR."""

    reason: str = Field(..., min_length=10, max_length=2000, description="Rejection reason")


class VCRAutoGenerateRequest(BaseModel):
    """Request for AI-assisted VCR generation."""

    project_id: UUID = Field(..., description="Project ID")
    pr_number: Optional[int] = Field(None, description="GitHub PR number")
    pr_url: Optional[str] = Field(None, description="PR URL")
    context: Optional[str] = Field(None, description="Additional context")


# =============================================================================
# Response Schemas
# =============================================================================


class VCRUserSummary(BaseModel):
    """Brief user info for VCR responses."""

    id: UUID
    name: str
    email: str

    class Config:
        from_attributes = True


class VCRResponse(BaseModel):
    """Schema for VCR API response."""

    id: UUID
    project_id: UUID
    pr_number: Optional[int]
    pr_url: Optional[str]
    title: str
    problem_statement: str
    root_cause_analysis: Optional[str]
    solution_approach: str
    implementation_notes: Optional[str]
    evidence_ids: List[UUID]
    adr_ids: List[UUID]
    ai_generated_percentage: float
    ai_tools_used: List[str]
    ai_generation_details: Dict[str, Any]
    status: VCRStatus
    created_by_id: Optional[UUID]
    approved_by_id: Optional[UUID]
    rejection_reason: Optional[str]
    created_at: datetime
    updated_at: datetime
    submitted_at: Optional[datetime]
    approved_at: Optional[datetime]

    # Relationships (optional, included when needed)
    created_by: Optional[VCRUserSummary] = None
    approved_by: Optional[VCRUserSummary] = None

    class Config:
        from_attributes = True


class VCRListResponse(BaseModel):
    """Paginated list of VCRs."""

    items: List[VCRResponse]
    total: int
    limit: int
    offset: int
    has_more: bool


class VCRAutoGenerateResponse(BaseModel):
    """Response from AI-assisted VCR generation."""

    title: str = Field(..., description="Generated title")
    problem_statement: str = Field(..., description="Generated problem statement")
    root_cause_analysis: Optional[str] = Field(None, description="Generated root cause")
    solution_approach: str = Field(..., description="Generated solution approach")
    implementation_notes: Optional[str] = Field(None, description="Generated notes")
    ai_confidence: float = Field(..., ge=0.0, le=1.0, description="AI confidence score")
    suggested_evidence: List[str] = Field(
        default_factory=list, description="Suggested evidence to attach"
    )


class VCRStatsResponse(BaseModel):
    """VCR statistics for a project."""

    total: int = Field(0, description="Total VCRs")
    draft: int = Field(0, description="Draft VCRs")
    submitted: int = Field(0, description="Submitted (pending approval)")
    approved: int = Field(0, description="Approved VCRs")
    rejected: int = Field(0, description="Rejected VCRs")
    avg_approval_time_hours: Optional[float] = Field(
        None, description="Average approval time in hours"
    )
    ai_involvement_percentage: float = Field(
        0.0, description="Average AI involvement across VCRs"
    )


# =============================================================================
# Telemetry Events (Sprint 150 pattern)
# =============================================================================


class VCREventNames:
    """Event names for VCR telemetry."""

    VCR_CREATED = "vcr_created"
    VCR_SUBMITTED = "vcr_submitted"
    VCR_APPROVED = "vcr_approved"
    VCR_REJECTED = "vcr_rejected"
    VCR_AUTO_GENERATED = "vcr_auto_generated"
