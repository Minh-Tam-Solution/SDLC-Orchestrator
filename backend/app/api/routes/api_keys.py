"""
=========================================================================
API Keys Router - Personal Access Token Management
SDLC Orchestrator - Stage 03 (BUILD)

Version: 1.0.0
Date: December 26, 2025
Status: ACTIVE - VS Code Extension Authentication
Authority: Backend Lead + CTO Approved
Framework: SDLC 5.1.2 Complete Lifecycle

Purpose:
- Generate personal access tokens for VS Code extension
- List user's API keys (with masked key display)
- Revoke API keys
- Similar to GitHub Personal Access Tokens

Endpoints:
- POST /api-keys - Create new API key
- GET /api-keys - List user's API keys
- DELETE /api-keys/{key_id} - Revoke API key

Security:
- API key shown ONCE on creation (user must save it)
- Key stored as SHA-256 hash (not plaintext)
- Prefix shown for identification (e.g., sdlc_live_abc...)
=========================================================================
"""

from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user
from app.core.security import generate_api_key, hash_api_key
from app.db.session import get_db
from app.models.user import APIKey, User

router = APIRouter(prefix="/api-keys", tags=["API Keys"])


# ============================================
# Pydantic Schemas
# ============================================


class APIKeyCreate(BaseModel):
    """Request to create a new API key."""
    name: str = Field(..., min_length=1, max_length=100, description="Name for this API key (e.g., 'VS Code Extension')")
    expires_in_days: Optional[int] = Field(None, ge=1, le=365, description="Days until expiry (None = never expires)")


class APIKeyResponse(BaseModel):
    """Response for API key (without the actual key)."""
    id: UUID
    name: str
    prefix: str
    last_used_at: Optional[datetime]
    expires_at: Optional[datetime]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class APIKeyCreatedResponse(BaseModel):
    """Response when API key is created (includes the actual key - shown ONCE)."""
    id: UUID
    name: str
    api_key: str = Field(..., description="Full API key - SAVE THIS NOW! It will not be shown again.")
    prefix: str
    expires_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================
# API Endpoints
# ============================================


@router.post("", response_model=APIKeyCreatedResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    key_data: APIKeyCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> APIKeyCreatedResponse:
    """
    Create a new API key for the current user.

    **Important**: The API key will only be shown ONCE in the response.
    Make sure to copy and save it securely.

    Request Body:
        {
            "name": "VS Code Extension",
            "expires_in_days": 90  // Optional, null = never expires
        }

    Response (201 Created):
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "name": "VS Code Extension",
            "api_key": "sdlc_live_abc123...",  // SAVE THIS!
            "prefix": "sdlc_live_abc...",
            "expires_at": "2026-03-26T00:00:00Z",
            "created_at": "2025-12-26T10:00:00Z"
        }

    Usage:
        - Use the `api_key` value in VS Code extension settings
        - Or set as Authorization header: `Bearer <api_key>`
    """
    # Generate new API key
    api_key, key_hash = generate_api_key()
    prefix = api_key[:20] + "..."  # Show first 20 chars for identification

    # Calculate expiry
    expires_at = None
    if key_data.expires_in_days:
        expires_at = datetime.utcnow() + timedelta(days=key_data.expires_in_days)

    # Create database record
    db_api_key = APIKey(
        user_id=current_user.id,
        name=key_data.name,
        key_hash=key_hash,
        prefix=prefix,
        expires_at=expires_at,
        is_active=True,
    )
    db.add(db_api_key)
    await db.commit()
    await db.refresh(db_api_key)

    return APIKeyCreatedResponse(
        id=db_api_key.id,
        name=db_api_key.name,
        api_key=api_key,  # Only shown ONCE!
        prefix=prefix,
        expires_at=expires_at,
        created_at=db_api_key.created_at,
    )


@router.get("", response_model=list[APIKeyResponse])
async def list_api_keys(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[APIKeyResponse]:
    """
    List all API keys for the current user.

    Response (200 OK):
        [
            {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "VS Code Extension",
                "prefix": "sdlc_live_abc...",
                "last_used_at": "2025-12-26T10:00:00Z",
                "expires_at": "2026-03-26T00:00:00Z",
                "is_active": true,
                "created_at": "2025-12-26T10:00:00Z"
            }
        ]

    Note:
        - The actual API key is NOT returned (only shown on creation)
        - Use the `prefix` to identify which key is which
    """
    result = await db.execute(
        select(APIKey)
        .where(APIKey.user_id == current_user.id)
        .order_by(APIKey.created_at.desc())
    )
    api_keys = result.scalars().all()

    return [
        APIKeyResponse(
            id=key.id,
            name=key.name,
            prefix=key.prefix,
            last_used_at=key.last_used_at,
            expires_at=key.expires_at,
            is_active=key.is_active,
            created_at=key.created_at,
        )
        for key in api_keys
    ]


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    key_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Revoke (delete) an API key.

    Path Parameters:
        key_id: UUID of the API key to revoke

    Response (204 No Content):
        (empty response)

    Errors:
        - 404 Not Found: API key not found or doesn't belong to user
    """
    result = await db.execute(
        select(APIKey).where(
            APIKey.id == key_id,
            APIKey.user_id == current_user.id,
        )
    )
    api_key = result.scalar_one_or_none()

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found",
        )

    # Soft revoke (mark as inactive) or hard delete
    # Using hard delete for simplicity
    await db.delete(api_key)
    await db.commit()

    return None
