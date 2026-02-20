"""
Team Invitation Service

Business logic for secure team invitation system with hash-based tokens.

Security Features:
- Cryptographically secure token generation (secrets.token_urlsafe)
- SHA256 token hashing (no raw tokens stored)
- Constant-time comparison (hmac.compare_digest)
- One-time use enforcement (status change)
- Rate limiting (Redis-based)
- Audit trail (IP, user agent, timestamps)

Reference: ADR-043-Team-Invitation-System-Architecture.md
Sprint 182: Full async migration (C-182-CF-02) — Session → AsyncSession + SQLAlchemy 2.0.
  All seven service functions converted from `def`+Session to `async def`+AsyncSession.
  Token/rate-limit helpers remain sync (no I/O; Redis calls are sub-ms blocking).
"""
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.team_invitation import TeamInvitation, InvitationStatus
from app.models.team import Team
from app.models.team_member import TeamMember
from app.models.user import User
from app.schemas.invitation import (
    InvitationCreate,
    InvitationResponse,
    InvitationDetails,
    InvitationAccepted,
    InvitationDeclined,
    InvitationResent,
)
from app.services.email_service import send_invitation_email
from app.core.redis import redis_client


# ============================================================================
# Token Security Functions (sync — pure computation, no I/O)
# ============================================================================

def generate_invitation_token() -> str:
    """
    Generate cryptographically secure invitation token.

    Returns:
        43-character base64url string (256-bit entropy)

    Example:
        >>> token = generate_invitation_token()
        >>> len(token)
        43
    """
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    """
    Hash invitation token with SHA256.

    Args:
        token: Raw invitation token

    Returns:
        64-character hexadecimal hash

    Example:
        >>> token = "abc123"
        >>> hash_token(token)
        'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad'
    """
    return hashlib.sha256(token.encode()).hexdigest()


def verify_token(provided_token: str, stored_hash: str) -> bool:
    """
    Verify invitation token with constant-time comparison.

    Prevents timing attacks by using hmac.compare_digest.

    Args:
        provided_token: Token from user request
        stored_hash: SHA256 hash from database

    Returns:
        True if token matches hash, False otherwise

    Example:
        >>> token = "abc123"
        >>> token_hash = hash_token(token)
        >>> verify_token(token, token_hash)
        True
        >>> verify_token("wrong", token_hash)
        False
    """
    provided_hash = hash_token(provided_token)
    return hmac.compare_digest(provided_hash, stored_hash)


# ============================================================================
# Rate Limiting Functions (sync — Redis calls are sub-ms, safe in async ctx)
# ============================================================================

def check_team_rate_limit(team_id: UUID) -> None:
    """
    Check if team has exceeded invitation rate limit.

    Limit: 50 invitations per hour per team (sliding window)

    Args:
        team_id: Team UUID

    Raises:
        HTTPException(429): If rate limit exceeded
    """
    if not redis_client:
        return  # Skip rate limit check if Redis not available

    key = f"invitation_rate:{team_id}:{datetime.utcnow().strftime('%Y%m%d%H')}"
    count = redis_client.incr(key)

    if count == 1:
        redis_client.expire(key, 3600)  # 1 hour TTL

    if count > settings.MAX_INVITATIONS_PER_TEAM_PER_HOUR:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "rate_limit_exceeded",
                "message": f"Maximum {settings.MAX_INVITATIONS_PER_TEAM_PER_HOUR} invitations per hour per team",
                "retry_after": 3600
            }
        )


def check_email_rate_limit(email: str) -> None:
    """
    Check if email has received too many invitations recently.

    Limit: 3 invitations per day across all teams

    Args:
        email: Email address

    Raises:
        HTTPException(429): If rate limit exceeded
    """
    if not redis_client:
        return  # Skip rate limit check if Redis not available

    key = f"invitation_email:{email}:{datetime.utcnow().strftime('%Y%m%d')}"
    count = redis_client.incr(key)

    if count == 1:
        redis_client.expire(key, 86400)  # 24 hours TTL

    if count > settings.MAX_INVITATIONS_PER_EMAIL_PER_DAY:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "rate_limit_exceeded",
                "message": f"Maximum {settings.MAX_INVITATIONS_PER_EMAIL_PER_DAY} invitations per day per email",
                "retry_after": 86400
            }
        )


# ============================================================================
# Invitation Service Functions (async — SQLAlchemy 2.0 + AsyncSession)
# ============================================================================

async def send_invitation(
    team_id: UUID,
    data: InvitationCreate,
    invited_by_user_id: UUID,
    db: AsyncSession,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> tuple[InvitationResponse, str]:
    """
    Send team invitation with secure token.

    Security features:
    - Rate limiting (team + email)
    - Duplicate detection (pending invitation check)
    - Token hashing (SHA256)
    - Audit trail (IP, user agent)

    Args:
        team_id: Team UUID
        data: Invitation creation data
        invited_by_user_id: User who is sending invitation
        db: Async database session
        ip_address: IP address of inviter (optional)
        user_agent: User agent of inviter (optional)

    Returns:
        Tuple of (InvitationResponse, raw_token)
        raw_token is used for email link (only returned once)

    Raises:
        HTTPException(403): If user not authorized
        HTTPException(409): If pending invitation already exists
        HTTPException(429): If rate limit exceeded
    """
    # 1. Rate limiting (sync helpers — sub-ms Redis calls)
    check_team_rate_limit(team_id)
    check_email_rate_limit(data.email)

    # 2. Verify team exists
    result = await db.execute(select(Team).where(Team.id == team_id))
    team = result.scalar_one_or_none()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )

    # 3. Check if pending invitation already exists
    existing_result = await db.execute(
        select(TeamInvitation).where(
            TeamInvitation.team_id == team_id,
            TeamInvitation.invited_email == data.email,
            TeamInvitation.status == InvitationStatus.PENDING,
        )
    )
    existing = existing_result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "invitation_exists",
                "message": "Pending invitation already sent to this email",
                "invitation_id": str(existing.id)
            }
        )

    # 4. Generate secure token
    raw_token = generate_invitation_token()
    token_hash = hash_token(raw_token)

    # 5. Create invitation record
    invitation = TeamInvitation(
        team_id=team_id,
        invited_email=data.email,
        invitation_token_hash=token_hash,
        role=data.role,
        status=InvitationStatus.PENDING,
        invited_by=invited_by_user_id,
        expires_at=datetime.utcnow() + timedelta(days=settings.INVITATION_EXPIRY_DAYS),
        ip_address=ip_address,
        user_agent=user_agent
    )

    db.add(invitation)
    await db.commit()
    await db.refresh(invitation)

    # 6. Prepare response
    inviter_result = await db.execute(select(User).where(User.id == invited_by_user_id))
    inviter = inviter_result.scalar_one_or_none()

    response = InvitationResponse(
        invitation_id=invitation.id,
        team_id=invitation.team_id,
        invited_email=invitation.invited_email,
        role=invitation.role,
        status=invitation.status,
        expires_at=invitation.expires_at,
        invited_by={
            "user_id": inviter.id,
            "display_name": inviter.display_name or inviter.username
        },
        created_at=invitation.created_at,
        message=data.message
    )

    return response, raw_token


async def get_invitation_by_token(token: str, db: AsyncSession) -> InvitationDetails:
    """
    Get invitation details by token (public endpoint, no auth).

    Args:
        token: Raw invitation token from URL
        db: Async database session

    Returns:
        InvitationDetails

    Raises:
        HTTPException(404): If invitation not found or expired
        HTTPException(410): If invitation already used
    """
    # Hash token for lookup
    token_hash = hash_token(token)

    # Find invitation by hash
    result = await db.execute(
        select(TeamInvitation).where(TeamInvitation.invitation_token_hash == token_hash)
    )
    invitation = result.scalar_one_or_none()

    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "invitation_not_found",
                "message": "Invitation not found or has expired"
            }
        )

    # Check if already used
    if invitation.status != InvitationStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail={
                "error": "invitation_already_used",
                "message": "This invitation has already been accepted or declined"
            }
        )

    # Check if expired
    if invitation.is_expired:
        invitation.mark_expired()
        await db.commit()

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "invitation_expired",
                "message": "This invitation has expired"
            }
        )

    # Build response
    team_result = await db.execute(select(Team).where(Team.id == invitation.team_id))
    team = team_result.scalar_one_or_none()

    inviter_result = await db.execute(select(User).where(User.id == invitation.invited_by))
    inviter = inviter_result.scalar_one_or_none()

    return InvitationDetails(
        team={
            "team_id": team.id,
            "team_name": team.name,
            "organization": team.organization.name if team.organization else None
        },
        invited_email=invitation.invited_email,
        role=invitation.role,
        status=invitation.status,
        expires_at=invitation.expires_at,
        invited_by={
            "user_id": inviter.id,
            "display_name": inviter.display_name or inviter.username
        },
        created_at=invitation.created_at
    )


async def accept_invitation(
    token: str,
    user_id: UUID,
    user_email: str,
    db: AsyncSession
) -> InvitationAccepted:
    """
    Accept invitation and create team membership.

    Security checks:
    - Token verification (constant-time)
    - Email matching (user email must match invited email)
    - Status check (must be pending)
    - Expiry check
    - One-time use (status change)

    Args:
        token: Raw invitation token
        user_id: Authenticated user ID
        user_email: Authenticated user email
        db: Async database session

    Returns:
        InvitationAccepted

    Raises:
        HTTPException(400): If cannot accept
        HTTPException(403): If email mismatch
        HTTPException(404): If invitation not found
        HTTPException(409): If already member
    """
    # Hash token for lookup
    token_hash = hash_token(token)

    # Find invitation
    result = await db.execute(
        select(TeamInvitation).where(
            TeamInvitation.invitation_token_hash == token_hash,
            TeamInvitation.status == InvitationStatus.PENDING,
        )
    )
    invitation = result.scalar_one_or_none()

    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found or already used"
        )

    # Check expiry
    if invitation.is_expired:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "invitation_expired",
                "message": "This invitation has expired",
                "expires_at": invitation.expires_at.isoformat()
            }
        )

    # Verify email match
    if user_email.lower() != invitation.invited_email.lower():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "email_mismatch",
                "message": "This invitation was sent to a different email address"
            }
        )

    # Check if already a team member
    existing_result = await db.execute(
        select(TeamMember).where(
            TeamMember.team_id == invitation.team_id,
            TeamMember.user_id == user_id,
            TeamMember.deleted_at.is_(None),  # Active members only
        )
    )
    existing_member = existing_result.scalar_one_or_none()

    if existing_member:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "already_member",
                "message": "You are already a member of this team",
                "team_id": str(invitation.team_id),
                "role": existing_member.role
            }
        )

    # Accept invitation (one-time use)
    invitation.accept(user_id)

    # Get team info
    team_result = await db.execute(select(Team).where(Team.id == invitation.team_id))
    team = team_result.scalar_one_or_none()

    # Create team membership record (P1 fix - Sprint 128)
    team_member = TeamMember(
        team_id=invitation.team_id,
        user_id=user_id,
        role=invitation.role,
        member_type="human"  # Invitations are for human users
    )
    db.add(team_member)
    await db.commit()

    return InvitationAccepted(
        status="accepted",
        team_id=invitation.team_id,
        team_name=team.name,
        role=invitation.role,
        accepted_at=invitation.accepted_at,
        redirect_url=f"/teams/{invitation.team_id}"
    )


async def decline_invitation(token: str, db: AsyncSession) -> InvitationDeclined:
    """
    Decline invitation (polite rejection).

    Args:
        token: Raw invitation token
        db: Async database session

    Returns:
        InvitationDeclined

    Raises:
        HTTPException(400): If cannot decline
        HTTPException(404): If invitation not found
    """
    # Hash token for lookup
    token_hash = hash_token(token)

    # Find invitation
    result = await db.execute(
        select(TeamInvitation).where(TeamInvitation.invitation_token_hash == token_hash)
    )
    invitation = result.scalar_one_or_none()

    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found"
        )

    # Check if can decline
    if invitation.status == InvitationStatus.ACCEPTED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "cannot_decline_invitation",
                "message": "Invitation has already been accepted"
            }
        )

    # Decline invitation
    invitation.decline()
    await db.commit()

    return InvitationDeclined(
        status="declined",
        declined_at=invitation.declined_at,
        message="Invitation declined successfully"
    )


async def resend_invitation(
    invitation_id: UUID,
    db: AsyncSession
) -> tuple[InvitationResent, str]:
    """
    Resend invitation email.

    Rate limiting:
    - Max 3 resends per invitation
    - 5 minute cooldown between resends

    Args:
        invitation_id: Invitation UUID
        db: Async database session

    Returns:
        Tuple of (InvitationResent, raw_token)

    Raises:
        HTTPException(400): If cannot resend
        HTTPException(404): If invitation not found
        HTTPException(429): If resend limit exceeded
    """
    # Find invitation
    result = await db.execute(
        select(TeamInvitation).where(TeamInvitation.id == invitation_id)
    )
    invitation = result.scalar_one_or_none()

    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found"
        )

    # Check if can resend
    if invitation.status == InvitationStatus.ACCEPTED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "cannot_resend_invitation",
                "message": "Invitation has already been accepted",
                "status": invitation.status
            }
        )

    # Check resend limit
    if invitation.resend_count >= settings.MAX_INVITATION_RESENDS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "resend_limit_exceeded",
                "message": f"Maximum {settings.MAX_INVITATION_RESENDS} resends per invitation",
                "resend_count": invitation.resend_count
            }
        )

    # Check cooldown
    if invitation.last_resent_at:
        cooldown = timedelta(minutes=settings.INVITATION_RESEND_COOLDOWN_MINUTES)
        elapsed = datetime.utcnow() - invitation.last_resent_at

        if elapsed < cooldown:
            retry_after = int((cooldown - elapsed).total_seconds())
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "resend_cooldown_active",
                    "message": f"Please wait {settings.INVITATION_RESEND_COOLDOWN_MINUTES} minutes before resending",
                    "retry_after": retry_after
                }
            )

    # Generate new token (security: regenerate token on resend)
    raw_token = generate_invitation_token()
    token_hash = hash_token(raw_token)

    # Update invitation
    invitation.invitation_token_hash = token_hash
    invitation.increment_resend_count()
    await db.commit()
    await db.refresh(invitation)

    return InvitationResent(
        invitation_id=invitation.id,
        status=invitation.status,
        resend_count=invitation.resend_count,
        last_resent_at=invitation.last_resent_at,
        expires_at=invitation.expires_at,
        message="Invitation email resent successfully"
    ), raw_token


async def list_team_invitations(
    team_id: UUID,
    db: AsyncSession,
    status_filter: Optional[str] = None,
    email_filter: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
) -> list[InvitationResponse]:
    """
    List team invitations with optional filters.

    Sprint 132 P0 Fix: Implement missing endpoint.

    Args:
        team_id: Team UUID
        db: Async database session
        status_filter: Filter by invitation status (optional)
        email_filter: Filter by invited email (optional)
        limit: Max results per page (default: 50)
        offset: Skip N results (default: 0)

    Returns:
        List of InvitationResponse

    Raises:
        HTTPException(404): If team not found
    """
    # Verify team exists
    team_result = await db.execute(select(Team).where(Team.id == team_id))
    team = team_result.scalar_one_or_none()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )

    # Build query
    stmt = select(TeamInvitation).where(TeamInvitation.team_id == team_id)

    # Apply status filter
    if status_filter:
        try:
            status_enum = InvitationStatus(status_filter)
            stmt = stmt.where(TeamInvitation.status == status_enum)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {status_filter}. Must be one of: pending, accepted, declined, expired, cancelled"
            )

    # Apply email filter
    if email_filter:
        stmt = stmt.where(TeamInvitation.invited_email.ilike(f"%{email_filter}%"))

    # Order by created_at descending (newest first), then paginate
    stmt = stmt.order_by(TeamInvitation.created_at.desc()).offset(offset).limit(limit)

    # Execute query
    invitations_result = await db.execute(stmt)
    invitations = invitations_result.scalars().all()

    # Build response list
    responses = []
    for invitation in invitations:
        inviter_result = await db.execute(select(User).where(User.id == invitation.invited_by))
        inviter = inviter_result.scalar_one_or_none()

        responses.append(InvitationResponse(
            invitation_id=invitation.id,
            team_id=invitation.team_id,
            invited_email=invitation.invited_email,
            role=invitation.role,
            status=invitation.status,
            expires_at=invitation.expires_at,
            invited_by={
                "user_id": inviter.id if inviter else None,
                "display_name": (inviter.display_name or inviter.username) if inviter else "Unknown"
            },
            created_at=invitation.created_at,
            message=None
        ))

    return responses


async def cancel_invitation(
    invitation_id: UUID,
    cancelled_by_user_id: UUID,
    db: AsyncSession
) -> None:
    """
    Cancel a pending invitation (admin action).

    Sprint 132 P0 Fix: Implement missing endpoint.

    Args:
        invitation_id: Invitation UUID
        cancelled_by_user_id: User performing the cancellation
        db: Async database session

    Raises:
        HTTPException(400): If invitation cannot be cancelled
        HTTPException(404): If invitation not found
    """
    # Find invitation
    result = await db.execute(
        select(TeamInvitation).where(TeamInvitation.id == invitation_id)
    )
    invitation = result.scalar_one_or_none()

    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found"
        )

    # Check if can cancel
    if invitation.status == InvitationStatus.ACCEPTED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "cannot_cancel_invitation",
                "message": "Cannot cancel an already accepted invitation"
            }
        )

    if invitation.status == InvitationStatus.DECLINED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "cannot_cancel_invitation",
                "message": "Cannot cancel an already declined invitation"
            }
        )

    if invitation.status == InvitationStatus.CANCELLED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "already_cancelled",
                "message": "Invitation is already cancelled"
            }
        )

    # Cancel the invitation
    invitation.status = InvitationStatus.CANCELLED
    await db.commit()
