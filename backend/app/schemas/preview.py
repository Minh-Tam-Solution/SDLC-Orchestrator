"""
=========================================================================
Preview Schemas - QR Code Mobile Preview
SDLC Orchestrator - Sprint 51B

Version: 1.0.0
Date: December 26, 2025
Status: ACTIVE - Sprint 51B Implementation
Authority: Backend Team + CTO Approved
Foundation: QR-Preview-Design.md

Purpose:
- Preview metadata for shareable links
- Preview file representation
- Request/response models for preview API

References:
- docs/02-design/14-Technical-Specs/QR-Preview-Design.md
- docs/02-design/15-Pattern-Adoption/Vibecode-Pattern-Adoption-Plan.md
=========================================================================
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class PreviewMetadata(BaseModel):
    """Metadata for preview session stored in Redis."""
    token: str
    session_id: UUID
    project_id: UUID
    user_id: UUID
    app_name: str
    created_at: datetime
    expires_at: datetime
    view_count: int = 0
    password_protected: bool = False
    password_hash: Optional[str] = None  # bcrypt hash

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }


class PreviewFile(BaseModel):
    """File for preview rendering."""
    path: str
    content: str
    language: str
    lines: int


class PreviewRequest(BaseModel):
    """Request to create preview."""
    password: Optional[str] = None  # Optional password protection
    expires_in_hours: int = Field(default=24, ge=1, le=168)  # 1h to 7d


class PreviewResponse(BaseModel):
    """Response with preview URL and QR data."""
    preview_url: str
    token: str
    expires_at: datetime
    qr_data: str  # Base64 encoded QR code PNG


class PreviewAccessRequest(BaseModel):
    """Request to access preview with password."""
    password: Optional[str] = None


class PreviewContent(BaseModel):
    """Full preview content for display."""
    app_name: str
    files: List[PreviewFile]
    file_count: int
    total_lines: int
    created_at: datetime
    expires_at: datetime
    view_count: int
