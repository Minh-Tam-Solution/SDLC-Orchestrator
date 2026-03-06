"""
=========================================================================
MFA TOTP Enrollment Routes - Sprint 211 Track B
SDLC Orchestrator - Stage 04 (BUILD -> DEPLOY)

Version: 1.0.0
Date: February 27, 2026
Status: ACTIVE - Sprint 211 Track B (MFA TOTP Enrollment)
Authority: Backend Lead + CTO Approved
Foundation: ADR-027 MFA Enforcement, OWASP ASVS Level 2
Framework: SDLC 6.1.1

Purpose:
- TOTP secret generation and QR code provisioning
- TOTP verification to activate MFA
- Admin-only MFA disable for user accounts
- MFA status reporting with grace period calculation

Endpoints:
- POST /auth/mfa/setup   - Generate TOTP secret + QR code + backup codes
- POST /auth/mfa/verify  - Verify TOTP code and enable MFA
- POST /auth/mfa/disable - Admin-only: disable MFA for a user
- GET  /auth/mfa/status  - Current user's MFA status

Security:
- TOTP secrets: base32-encoded, stored in user record
- Backup codes: bcrypt-hashed (cost=12) before storage
- QR code: in-memory only, never persisted
- Provisioning URI: standard otpauth:// format
- Admin disable: requires superuser (is_superuser=True)

Dependencies:
- pyotp 2.9.0 (MIT) - TOTP generation and verification
- qrcode 8.2 (BSD) - QR code generation
- bcrypt (Apache 2.0) - backup code hashing

Zero Mock Policy: Production-ready MFA enrollment implementation
=========================================================================
"""

import base64
import io
import json
import logging
import secrets
from datetime import datetime, timezone
from math import ceil
from typing import Optional
from uuid import UUID

import bcrypt
import pyotp
import qrcode
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, require_superuser
from app.db.session import get_db
from app.models.user import User

logger = logging.getLogger(__name__)

# =========================================================================
# Router
# =========================================================================

router = APIRouter(prefix="/auth/mfa", tags=["MFA"])


# =========================================================================
# Request / Response Schemas
# =========================================================================


class MFAVerifyRequest(BaseModel):
    """Request body for TOTP verification."""

    code: str = Field(
        ...,
        min_length=6,
        max_length=6,
        pattern=r"^\d{6}$",
        description="6-digit TOTP code from authenticator app",
        examples=["123456"],
    )

    model_config = ConfigDict(json_schema_extra={"examples": [{"code": "123456"}]})


class MFADisableRequest(BaseModel):
    """Request body for admin MFA disable."""

    user_id: UUID = Field(
        ...,
        description="UUID of the user whose MFA should be disabled",
    )


class MFASetupResponse(BaseModel):
    """Response body for MFA setup endpoint."""

    secret: str = Field(..., description="Base32-encoded TOTP secret")
    qr_code_uri: str = Field(
        ..., description="Data URI of QR code PNG image (data:image/png;base64,...)"
    )
    backup_codes: list[str] = Field(
        ..., description="10 one-time backup codes (8-char hex each)"
    )


class MFAVerifyResponse(BaseModel):
    """Response body for MFA verify endpoint."""

    message: str
    enabled_at: str = Field(
        ..., description="ISO 8601 timestamp when MFA was enabled"
    )


class MFADisableResponse(BaseModel):
    """Response body for admin MFA disable endpoint."""

    message: str
    user_id: str


class MFAStatusResponse(BaseModel):
    """Response body for MFA status endpoint."""

    mfa_enabled: bool
    has_secret: bool
    mfa_setup_deadline: Optional[str] = Field(
        None, description="ISO 8601 deadline or null"
    )
    is_mfa_exempt: bool
    grace_period_remaining_days: Optional[int] = Field(
        None, description="Days until MFA setup deadline, or null if no deadline"
    )


# =========================================================================
# Helper Functions
# =========================================================================


def _generate_qr_data_uri(provisioning_uri: str) -> str:
    """
    Generate a QR code as a base64-encoded PNG data URI.

    Args:
        provisioning_uri: otpauth:// URI for the TOTP secret.

    Returns:
        Data URI string: ``data:image/png;base64,<base64 bytes>``.

    Raises:
        ValueError: If the provisioning URI is empty.
    """
    if not provisioning_uri:
        raise ValueError("provisioning_uri must not be empty")

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(provisioning_uri)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    b64 = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{b64}"


def _generate_backup_codes(count: int = 10) -> list[str]:
    """
    Generate a list of cryptographically random backup codes.

    Args:
        count: Number of backup codes to generate (default 10).

    Returns:
        List of 8-character hex strings (e.g. ``["a1b2c3d4", ...]``).
    """
    return [secrets.token_hex(4) for _ in range(count)]


def _hash_backup_codes(codes: list[str]) -> str:
    """
    Hash each backup code with bcrypt and return as JSON array.

    Backup codes are hashed individually so that a single code can be
    verified without revealing the others.

    Args:
        codes: Plain-text backup codes.

    Returns:
        JSON-encoded list of bcrypt hashes.
    """
    hashed = [
        bcrypt.hashpw(code.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")
        for code in codes
    ]
    return json.dumps(hashed)


# =========================================================================
# Endpoints
# =========================================================================


@router.post(
    "/setup",
    response_model=MFASetupResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate TOTP secret and QR code for MFA enrollment",
    description=(
        "Generates a new TOTP secret, returns a scannable QR code data URI, "
        "and provides 10 one-time backup codes. Does NOT enable MFA — call "
        "/verify with a valid TOTP code to activate."
    ),
    responses={
        400: {"description": "MFA already enabled for this user"},
    },
)
async def mfa_setup(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MFASetupResponse:
    """
    Generate TOTP secret, QR code, and backup codes for MFA enrollment.

    This endpoint is idempotent for users who have not yet completed
    verification: calling it again will overwrite the pending secret and
    backup codes (the previous ones become invalid).

    Args:
        current_user: Authenticated user from JWT/cookie.
        db: Async database session.

    Returns:
        MFASetupResponse with secret, QR code data URI, and backup codes.

    Raises:
        HTTPException(400): If user already has MFA enabled.
    """
    if current_user.mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA already enabled",
        )

    # Generate TOTP secret
    secret = pyotp.random_base32()

    # Build provisioning URI (otpauth://totp/...)
    totp = pyotp.totp.TOTP(secret)
    provisioning_uri = totp.provisioning_uri(
        name=current_user.email,
        issuer_name="SDLC Orchestrator",
    )

    # Generate QR code as base64 data URI
    qr_code_uri = _generate_qr_data_uri(provisioning_uri)

    # Generate and hash backup codes
    backup_codes = _generate_backup_codes(count=10)
    hashed_codes = _hash_backup_codes(backup_codes)

    # Persist secret and hashed backup codes (MFA NOT enabled yet)
    current_user.mfa_secret = secret
    current_user.backup_codes = hashed_codes
    await db.flush()

    logger.info(
        "MFA setup initiated for user %s (%s)",
        current_user.id,
        current_user.email,
    )

    return MFASetupResponse(
        secret=secret,
        qr_code_uri=qr_code_uri,
        backup_codes=backup_codes,
    )


@router.post(
    "/verify",
    response_model=MFAVerifyResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify TOTP code and enable MFA",
    description=(
        "Accepts a 6-digit TOTP code and, if valid, enables MFA on the "
        "user account. Must call /setup first to generate the secret."
    ),
    responses={
        400: {
            "description": (
                "MFA already enabled, setup not completed, or invalid TOTP code"
            )
        },
    },
)
async def mfa_verify(
    body: MFAVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MFAVerifyResponse:
    """
    Verify a TOTP code and activate MFA for the user.

    Args:
        body: Request body containing the 6-digit TOTP code.
        current_user: Authenticated user from JWT/cookie.
        db: Async database session.

    Returns:
        MFAVerifyResponse confirming MFA activation with timestamp.

    Raises:
        HTTPException(400): If MFA is already enabled.
        HTTPException(400): If /setup has not been called (no secret stored).
        HTTPException(400): If the TOTP code is invalid or expired.
    """
    if current_user.mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA already enabled",
        )

    if not current_user.mfa_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Call /setup first",
        )

    # Verify TOTP code with a +-1 window (allows 30s clock skew)
    totp = pyotp.TOTP(current_user.mfa_secret)
    if not totp.verify(body.code, valid_window=1):
        logger.warning(
            "MFA verification failed for user %s (%s) — invalid TOTP code",
            current_user.id,
            current_user.email,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid TOTP code",
        )

    # Activate MFA
    now = datetime.now(timezone.utc)
    current_user.mfa_enabled = True
    current_user.mfa_setup_deadline = None  # No longer needed
    await db.flush()

    logger.info(
        "MFA enabled for user %s (%s) at %s",
        current_user.id,
        current_user.email,
        now.isoformat(),
    )

    return MFAVerifyResponse(
        message="MFA enabled successfully",
        enabled_at=now.isoformat(),
    )


@router.post(
    "/disable",
    response_model=MFADisableResponse,
    status_code=status.HTTP_200_OK,
    summary="Admin-only: disable MFA for a user",
    description=(
        "Clears MFA secret, backup codes, and the mfa_enabled flag for the "
        "specified user. Requires superuser access."
    ),
    responses={
        403: {"description": "Superuser access required"},
        404: {"description": "User not found"},
    },
)
async def mfa_disable(
    body: MFADisableRequest,
    admin: User = Depends(require_superuser),
    db: AsyncSession = Depends(get_db),
) -> MFADisableResponse:
    """
    Admin-only endpoint to disable MFA for a target user.

    Clears ``mfa_enabled``, ``mfa_secret``, and ``backup_codes`` on the
    target user record. The user will need to re-enroll via /setup + /verify
    to re-enable MFA.

    Args:
        body: Request body containing the target user_id.
        admin: Superuser performing the action (injected by dependency).
        db: Async database session.

    Returns:
        MFADisableResponse confirming the operation.

    Raises:
        HTTPException(403): If the caller is not a superuser.
        HTTPException(404): If the target user does not exist.
    """
    result = await db.execute(
        select(User).where(User.id == body.user_id)
    )
    target_user = result.scalar_one_or_none()

    if target_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {body.user_id} not found",
        )

    # Clear all MFA state
    target_user.mfa_enabled = False
    target_user.mfa_secret = None
    target_user.backup_codes = None
    await db.flush()

    logger.info(
        "MFA disabled for user %s by admin %s (%s)",
        body.user_id,
        admin.id,
        admin.email,
    )

    return MFADisableResponse(
        message="MFA disabled",
        user_id=str(body.user_id),
    )


@router.get(
    "/status",
    response_model=MFAStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current user's MFA status",
    description=(
        "Returns MFA enrollment state, whether a secret is pending, the "
        "setup deadline (if any), exemption status, and remaining grace "
        "period days."
    ),
)
async def mfa_status(
    current_user: User = Depends(get_current_user),
) -> MFAStatusResponse:
    """
    Return the current user's MFA enrollment status.

    The ``grace_period_remaining_days`` is computed from
    ``mfa_setup_deadline`` and represents the number of calendar days
    remaining before MFA setup becomes mandatory. Returns ``null`` if
    no deadline is set or if the deadline has already passed.

    Args:
        current_user: Authenticated user from JWT/cookie.

    Returns:
        MFAStatusResponse with all MFA-related fields.
    """
    grace_period_remaining_days: Optional[int] = None
    deadline_iso: Optional[str] = None

    if current_user.mfa_setup_deadline is not None:
        deadline = current_user.mfa_setup_deadline
        # Normalise to offset-aware UTC for comparison
        if deadline.tzinfo is None:
            deadline = deadline.replace(tzinfo=timezone.utc)

        deadline_iso = deadline.isoformat()

        remaining = deadline - datetime.now(timezone.utc)
        remaining_days = remaining.total_seconds() / 86400.0

        if remaining_days > 0:
            grace_period_remaining_days = ceil(remaining_days)
        else:
            # Deadline has passed — grace period is 0
            grace_period_remaining_days = 0

    return MFAStatusResponse(
        mfa_enabled=current_user.mfa_enabled,
        has_secret=current_user.mfa_secret is not None,
        mfa_setup_deadline=deadline_iso,
        is_mfa_exempt=current_user.is_mfa_exempt,
        grace_period_remaining_days=grace_period_remaining_days,
    )
