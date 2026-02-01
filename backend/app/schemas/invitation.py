"""
Team Invitation Schemas

Pydantic schemas for team invitation API request/response validation.

Reference: Team-Invitation-API-Spec.md, ADR-043
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, validator


# ============================================================================
# Request Schemas
# ============================================================================

class InvitationCreate(BaseModel):
    """Request schema for sending team invitation"""

    email: EmailStr = Field(
        ...,
        description="Email address of invitee",
        example="user@example.com"
    )
    role: str = Field(
        ...,
        description="Team role (owner, admin, member)",
        example="member"
    )
    message: Optional[str] = Field(
        None,
        max_length=500,
        description="Optional custom message",
        example="Join our SDLC project!"
    )

    @validator("role")
    def validate_role(cls, v):
        """Validate role is one of allowed values"""
        allowed_roles = {"owner", "admin", "member"}
        if v not in allowed_roles:
            raise ValueError(f"Role must be one of: {allowed_roles}")
        return v


class InvitationDecline(BaseModel):
    """Request schema for declining invitation"""

    reason: Optional[str] = Field(
        None,
        max_length=500,
        description="Optional reason for declining",
        example="Not interested"
    )


# ============================================================================
# Response Schemas
# ============================================================================

class InviterInfo(BaseModel):
    """Nested schema for inviter information"""

    user_id: UUID
    display_name: str

    class Config:
        from_attributes = True


class TeamInfo(BaseModel):
    """Nested schema for team information"""

    team_id: UUID
    team_name: str
    organization: Optional[str] = None

    class Config:
        from_attributes = True


class InvitationResponse(BaseModel):
    """Response schema for invitation creation/retrieval"""

    invitation_id: UUID
    team_id: UUID
    invited_email: EmailStr
    role: str
    status: str
    expires_at: datetime
    invited_by: InviterInfo
    created_at: datetime

    # Optional fields
    message: Optional[str] = None

    class Config:
        from_attributes = True


class InvitationDetails(BaseModel):
    """Response schema for public invitation details (no auth required)"""

    team: TeamInfo
    invited_email: EmailStr
    role: str
    status: str
    expires_at: datetime
    invited_by: InviterInfo
    message: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class InvitationAccepted(BaseModel):
    """Response schema for successful acceptance"""

    status: str = "accepted"
    team_id: UUID
    team_name: str
    role: str
    accepted_at: datetime
    redirect_url: str

    class Config:
        from_attributes = True


class InvitationDeclined(BaseModel):
    """Response schema for successful decline"""

    status: str = "declined"
    declined_at: datetime
    message: str = "Invitation declined successfully"

    class Config:
        from_attributes = True


class InvitationResent(BaseModel):
    """Response schema for successful resend"""

    invitation_id: UUID
    status: str
    resend_count: int
    last_resent_at: datetime
    expires_at: datetime
    message: str = "Invitation email resent successfully"

    class Config:
        from_attributes = True


# ============================================================================
# List Response Schemas
# ============================================================================

class InvitationListItem(BaseModel):
    """Schema for invitation in list view"""

    invitation_id: UUID
    invited_email: EmailStr
    role: str
    status: str
    expires_at: datetime
    created_at: datetime
    resend_count: int

    class Config:
        from_attributes = True


class InvitationListResponse(BaseModel):
    """Response schema for listing invitations"""

    invitations: list[InvitationListItem]
    total: int
    page: int = 1
    per_page: int = 20
    has_next: bool = False


# ============================================================================
# Error Response Schemas (for OpenAPI documentation)
# ============================================================================

class ValidationError(BaseModel):
    """Schema for validation errors (400)"""

    error: str = "validation_error"
    message: str
    details: Optional[dict] = None


class ForbiddenError(BaseModel):
    """Schema for forbidden errors (403)"""

    error: str = "forbidden"
    message: str


class ConflictError(BaseModel):
    """Schema for conflict errors (409)"""

    error: str
    message: str
    invitation_id: Optional[UUID] = None


class RateLimitError(BaseModel):
    """Schema for rate limit errors (429)"""

    error: str
    message: str
    retry_after: int  # Seconds until retry allowed


class GoneError(BaseModel):
    """Schema for gone errors (410)"""

    error: str = "endpoint_deprecated"
    message: str
    deprecation_date: str
    removal_date: str
    migration_guide: str
    replacement_endpoint: str


# ============================================================================
# Deprecated Endpoint Response
# ============================================================================

class DeprecatedMemberAddResponse(BaseModel):
    """Response for deprecated POST /teams/{team_id}/members endpoint"""

    error: str = "endpoint_deprecated"
    message: str = "Email-based member addition is deprecated. Use invitation system instead."
    deprecation_date: str = "2026-02-01"
    removal_date: str = "2026-08-01"
    migration_guide: str = "https://docs.sdlc-orchestrator.com/api/migration/invitations"
    replacement_endpoint: str = "POST /teams/{team_id}/invitations"
