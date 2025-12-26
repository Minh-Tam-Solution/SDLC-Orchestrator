"""
=========================================================================
Preview API Routes - QR Code Mobile Preview
SDLC Orchestrator - Sprint 51B

Version: 1.0.0
Date: December 26, 2025
Status: ACTIVE - Sprint 51B Implementation
Authority: Backend Team + CTO Approved
Foundation: QR-Preview-Design.md

Purpose:
- Create shareable preview URLs with QR codes
- Serve preview content (public endpoint)
- Manage preview lifecycle (delete, expire)

References:
- docs/02-design/14-Technical-Specs/QR-Preview-Design.md
=========================================================================
"""

import base64
import json
import logging
import secrets
from datetime import datetime, timedelta
from io import BytesIO
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from redis.asyncio import Redis

from app.api.dependencies import get_current_active_user, get_redis
from app.core.config import settings
from app.models.user import User
from app.schemas.preview import (
    PreviewContent,
    PreviewFile,
    PreviewMetadata,
    PreviewRequest,
    PreviewResponse,
)
from app.services.codegen.session_manager import SessionManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/codegen", tags=["Preview"])


@router.post("/sessions/{session_id}/preview", response_model=PreviewResponse)
async def create_preview(
    session_id: UUID,
    request: PreviewRequest,
    current_user: User = Depends(get_current_active_user),
    redis: Redis = Depends(get_redis),
):
    """
    Create a shareable preview URL for generated code.

    Sprint 51B: QR Mobile Preview Feature

    Creates a preview link that can be shared via QR code.
    Preview links expire after the specified duration (default 24h).

    Args:
        session_id: UUID of the generation session
        request: Preview options (password, expiration)

    Returns:
        PreviewResponse with URL and QR code image data

    Raises:
        404: Session not found
        403: User not authorized
        400: No files to preview
    """
    session_manager = SessionManager(redis)

    # Get session
    session = await session_manager.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found or expired"
        )

    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create preview for this session"
        )

    # Get generated files
    files = await session_manager.get_completed_files(session_id)
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No files to preview. Generate files first."
        )

    # Generate secure token
    token = secrets.token_urlsafe(32)

    # Calculate expiration
    expires_at = datetime.utcnow() + timedelta(hours=request.expires_in_hours)

    # Hash password if provided
    password_hash = None
    if request.password:
        import bcrypt
        password_hash = bcrypt.hashpw(
            request.password.encode(),
            bcrypt.gensalt()
        ).decode()

    # Create metadata
    metadata = PreviewMetadata(
        token=token,
        session_id=session_id,
        project_id=session.project_id,
        user_id=current_user.id,
        app_name=session.blueprint_version or "Generated App",
        created_at=datetime.utcnow(),
        expires_at=expires_at,
        password_protected=password_hash is not None,
        password_hash=password_hash
    )

    # Convert files to preview format
    preview_files = [
        PreviewFile(
            path=f.file_path,
            content=f.content,
            language=f.language,
            lines=f.lines
        )
        for f in files
    ]

    # Store in Redis
    ttl_seconds = request.expires_in_hours * 3600

    pipe = redis.pipeline()
    pipe.setex(
        f"preview:{token}:metadata",
        ttl_seconds,
        metadata.model_dump_json()
    )
    pipe.setex(
        f"preview:{token}:files",
        ttl_seconds,
        json.dumps([f.model_dump() for f in preview_files], default=str)
    )
    await pipe.execute()

    # Build preview URL
    preview_base = getattr(settings, 'PREVIEW_BASE_URL', 'http://localhost:3000')
    preview_url = f"{preview_base}/preview/{token}"

    # Generate QR code
    qr_data = _generate_qr_code(preview_url)

    logger.info(
        f"Created preview for session {session_id}: "
        f"token={token[:8]}..., expires={expires_at}, files={len(files)}"
    )

    return PreviewResponse(
        preview_url=preview_url,
        token=token,
        expires_at=expires_at,
        qr_data=qr_data
    )


@router.get("/preview/{token}")
async def get_preview(
    token: str,
    password: Optional[str] = Query(None),
    redis: Redis = Depends(get_redis),
) -> PreviewContent:
    """
    Get preview content by token.

    Sprint 51B: Public endpoint (no auth required)

    This endpoint is public so preview links can be shared without login.

    Args:
        token: Preview token from URL
        password: Password if preview is protected

    Returns:
        PreviewContent with files and metadata

    Raises:
        404: Preview not found or expired
        401: Password required or invalid
    """
    # Get metadata
    metadata_json = await redis.get(f"preview:{token}:metadata")
    if not metadata_json:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Preview not found or expired"
        )

    metadata = PreviewMetadata.model_validate_json(metadata_json)

    # Check password if protected
    if metadata.password_protected:
        if not password:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Password required",
                headers={"X-Password-Required": "true"}
            )
        import bcrypt
        if not bcrypt.checkpw(password.encode(), metadata.password_hash.encode()):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid password"
            )

    # Get files
    files_json = await redis.get(f"preview:{token}:files")
    if not files_json:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Preview files not found"
        )

    files = [PreviewFile.model_validate(f) for f in json.loads(files_json)]

    # Increment view count
    metadata.view_count += 1
    ttl = await redis.ttl(f"preview:{token}:metadata")
    if ttl > 0:
        await redis.setex(
            f"preview:{token}:metadata",
            ttl,
            metadata.model_dump_json()
        )

    return PreviewContent(
        app_name=metadata.app_name,
        files=files,
        file_count=len(files),
        total_lines=sum(f.lines for f in files),
        created_at=metadata.created_at,
        expires_at=metadata.expires_at,
        view_count=metadata.view_count
    )


@router.delete("/preview/{token}")
async def delete_preview(
    token: str,
    current_user: User = Depends(get_current_active_user),
    redis: Redis = Depends(get_redis),
):
    """
    Delete a preview before expiration.

    Args:
        token: Preview token to delete

    Returns:
        Success message

    Raises:
        404: Preview not found
        403: User not authorized
    """
    # Get metadata to check ownership
    metadata_json = await redis.get(f"preview:{token}:metadata")
    if not metadata_json:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Preview not found"
        )

    metadata = PreviewMetadata.model_validate_json(metadata_json)

    if metadata.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this preview"
        )

    # Delete from Redis
    await redis.delete(
        f"preview:{token}:metadata",
        f"preview:{token}:files"
    )

    logger.info(f"Deleted preview {token[:8]}... for user {current_user.id}")

    return {"message": "Preview deleted successfully"}


def _generate_qr_code(url: str) -> str:
    """
    Generate QR code as base64 data URL.

    Args:
        url: URL to encode in QR code

    Returns:
        Data URL string (data:image/png;base64,...)
    """
    try:
        import qrcode
        from qrcode.image.pure import PyPNGImage

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        # Convert to base64
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        qr_base64 = base64.b64encode(buffer.getvalue()).decode()

        return f"data:image/png;base64,{qr_base64}"
    except ImportError:
        # qrcode library not installed, return placeholder
        logger.warning("qrcode library not installed, using placeholder")
        return "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    except Exception as e:
        logger.error(f"Failed to generate QR code: {e}")
        return ""
