"""
Team Invitation API Endpoints

RESTful API for secure team invitation system with hash-based tokens.

Security Features:
- Rate limiting (Redis-based)
- Token hashing (SHA256, never store raw)
- Audit trail (IP, user agent, timestamps)
- Email verification
- One-time use enforcement

Reference: ADR-043-Team-Invitation-System-Architecture.md
API Spec: docs/01-planning/05-API-Design/Team-Invitation-API-Spec.md

Sprint 181: Async fix — registered route + AsyncSession (ADR-059 ENTERPRISE activation).
Sprint 182: C-182-CF-02 — invitation_service.py fully migrated to async def + AsyncSession.
  All sync bridge calls removed. Service called directly with await.
"""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.team import Team
from app.models.team_member import TeamMember
from app.models.team_invitation import TeamInvitation
from app.schemas.invitation import (
    InvitationCreate,
    InvitationResponse,
    InvitationDetails,
    InvitationAccepted,
    InvitationDeclined,
    InvitationResent,
)
from app.services import invitation_service
from app.services.email_service import send_invitation_email

router = APIRouter(prefix="/api/v1", tags=["invitations"])


# ============================================================================
# Team Admin Endpoints (Authenticated)
# ============================================================================

@router.post(
    "/teams/{team_id}/invitations",
    response_model=InvitationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Send team invitation",
    description="""
    Send invitation to join team with secure token.

    **Security**:
    - Rate limiting: 50 invitations/hour per team
    - Email rate limit: 3 invitations/day per email
    - Token hashing: SHA256 (never store raw)
    - Audit trail: IP address, user agent, timestamp

    **Permissions**:
    - Team owner: Can invite with any role
    - Team admin: Can invite members only

    **Errors**:
    - 403: User not authorized to invite
    - 409: Pending invitation already exists
    - 429: Rate limit exceeded
    """,
)
async def send_invitation(
    team_id: UUID,
    data: InvitationCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> InvitationResponse:
    """
    Send team invitation with secure token.

    Args:
        team_id: Team UUID
        data: Invitation creation data
        request: FastAPI request (for IP/user agent)
        current_user: Authenticated user sending invitation
        db: Database session (AsyncSession)

    Returns:
        InvitationResponse with invitation_id, email, status, expires_at

    Raises:
        HTTPException(403): If user not authorized
        HTTPException(409): If pending invitation exists
        HTTPException(429): If rate limit exceeded
    """
    # RBAC enforcement — check user permission to invite
    result = await db.execute(
        select(TeamMember).where(
            TeamMember.team_id == team_id,
            TeamMember.user_id == current_user.id,
            TeamMember.deleted_at.is_(None),
            TeamMember.role.in_(["owner", "admin"]),
        )
    )
    membership = result.scalar_one_or_none()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "not_authorized",
                "message": "You must be a team owner or admin to send invitations"
            }
        )

    # Fetch team for email (service also checks existence; this avoids second 404 path)
    team_result = await db.execute(select(Team).where(Team.id == team_id))
    team = team_result.scalar_one_or_none()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "team_not_found", "message": "Team not found"}
        )

    # Extract audit trail info
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("User-Agent")

    # Send invitation via async service (C-182-CF-02: no more db.run_sync bridge)
    response, raw_token = await invitation_service.send_invitation(
        team_id=team_id,
        data=data,
        invited_by_user_id=current_user.id,
        db=db,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    # Send invitation email (async)
    # Email sent AFTER database commit to prevent ghost invitations
    try:
        send_invitation_email(
            to_email=response.invited_email,
            invitation_token=raw_token,
            team_name=team.name,
            inviter_name=response.invited_by["display_name"],
            expires_at=response.expires_at,
            message=data.message,
        )
    except Exception as e:
        # Log email failure but don't fail the request
        # Admin can resend invitation later
        import logging
        logging.error(f"Failed to send invitation email: {str(e)}")

    return response


@router.post(
    "/invitations/{invitation_id}/resend",
    response_model=InvitationResent,
    summary="Resend invitation email",
    description="""
    Resend invitation email with new token.

    **Security**:
    - Generates NEW token (invalidates old token)
    - Rate limiting: Max 3 resends per invitation
    - Cooldown: 5 minutes between resends

    **Permissions**:
    - Team owner/admin only

    **Errors**:
    - 400: Invitation already accepted/declined
    - 404: Invitation not found
    - 429: Resend limit exceeded or cooldown active
    """,
)
async def resend_invitation(
    invitation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> InvitationResent:
    """
    Resend invitation email with new token.

    Args:
        invitation_id: Invitation UUID
        current_user: Authenticated user (must be team admin/owner)
        db: Database session (AsyncSession)

    Returns:
        InvitationResent with resend_count, last_resent_at

    Raises:
        HTTPException(400): If cannot resend
        HTTPException(404): If invitation not found
        HTTPException(429): If rate limit exceeded
    """
    # Fetch invitation for RBAC check
    inv_result = await db.execute(
        select(TeamInvitation).where(TeamInvitation.id == invitation_id)
    )
    invitation = inv_result.scalar_one_or_none()

    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "invitation_not_found", "message": "Invitation not found"}
        )

    # RBAC enforcement — check user permission to resend
    membership_result = await db.execute(
        select(TeamMember).where(
            TeamMember.team_id == invitation.team_id,
            TeamMember.user_id == current_user.id,
            TeamMember.deleted_at.is_(None),
            TeamMember.role.in_(["owner", "admin"]),
        )
    )
    membership = membership_result.scalar_one_or_none()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "not_authorized",
                "message": "You must be a team owner or admin to resend invitations"
            }
        )

    # Resend invitation — async service (C-182-CF-02: no more db.run_sync bridge)
    response, raw_token = await invitation_service.resend_invitation(
        invitation_id=invitation_id,
        db=db,
    )

    # Fetch relationships for email (session committed in service; fresh reads)
    fresh_inv_result = await db.execute(
        select(TeamInvitation).where(TeamInvitation.id == invitation_id)
    )
    invitation = fresh_inv_result.scalar_one_or_none()

    team_result = await db.execute(select(Team).where(Team.id == invitation.team_id))
    team = team_result.scalar_one_or_none()

    inviter_result = await db.execute(select(User).where(User.id == invitation.invited_by))
    inviter = inviter_result.scalar_one_or_none()

    # Send invitation email with new token
    try:
        send_invitation_email(
            to_email=invitation.invited_email,
            invitation_token=raw_token,
            team_name=team.name if team else "Unknown Team",
            inviter_name=inviter.display_name or inviter.username if inviter else "Team Admin",
            expires_at=response.expires_at,
            message=None,
        )
    except Exception as e:
        import logging
        logging.error(f"Failed to resend invitation email: {str(e)}")

    return response


# ============================================================================
# Public Endpoints (No Authentication)
# ============================================================================

@router.get(
    "/invitations/{token}",
    response_model=InvitationDetails,
    summary="Get invitation details by token",
    description="""
    Get invitation details for acceptance page (public endpoint).

    **Security**:
    - No authentication required (token is the credential)
    - Constant-time token verification (prevents timing attacks)
    - Rate limiting: 10 requests/minute per IP

    **Use Case**:
    - User clicks invitation link in email
    - Frontend shows team name, role, inviter info
    - User decides to accept or decline

    **Errors**:
    - 404: Invitation not found or expired
    - 410: Invitation already used (accepted/declined)
    """,
)
async def get_invitation_by_token(
    token: str,
    db: AsyncSession = Depends(get_db),
) -> InvitationDetails:
    """
    Get invitation details by token (public endpoint).

    Args:
        token: Raw invitation token from URL
        db: Database session (AsyncSession)

    Returns:
        InvitationDetails with team info, role, inviter, expiry

    Raises:
        HTTPException(404): If invitation not found or expired
        HTTPException(410): If invitation already used
    """
    return await invitation_service.get_invitation_by_token(token=token, db=db)


@router.post(
    "/invitations/{token}/accept",
    response_model=InvitationAccepted,
    summary="Accept team invitation",
    description="""
    Accept invitation and create team membership.

    **Security**:
    - Requires authentication (user must be logged in)
    - Email verification (user email must match invited email)
    - One-time use (status change prevents replay)
    - Constant-time token verification

    **Flow**:
    1. User clicks invitation link → Signup/Login
    2. User accepts invitation → Team membership created
    3. User redirected to team dashboard

    **Errors**:
    - 400: Invitation expired or cannot accept
    - 403: Email mismatch (user email != invited email)
    - 404: Invitation not found
    - 409: User already member of team
    """,
)
async def accept_invitation(
    token: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> InvitationAccepted:
    """
    Accept invitation and create team membership.

    Args:
        token: Raw invitation token from URL
        current_user: Authenticated user accepting invitation
        db: Database session (AsyncSession)

    Returns:
        InvitationAccepted with team_id, role, redirect_url

    Raises:
        HTTPException(400): If cannot accept
        HTTPException(403): If email mismatch
        HTTPException(404): If invitation not found
        HTTPException(409): If already member
    """
    return await invitation_service.accept_invitation(
        token=token,
        user_id=current_user.id,
        user_email=current_user.email,
        db=db,
    )


@router.post(
    "/invitations/{token}/decline",
    response_model=InvitationDeclined,
    summary="Decline team invitation",
    description="""
    Decline invitation politely (no team membership created).

    **Security**:
    - No authentication required (anonymous decline allowed)
    - One-time use (status change prevents replay)

    **Use Case**:
    - User receives invitation but doesn't want to join
    - User can decline without creating account

    **Errors**:
    - 400: Invitation already accepted (cannot decline)
    - 404: Invitation not found
    """,
)
async def decline_invitation(
    token: str,
    db: AsyncSession = Depends(get_db),
) -> InvitationDeclined:
    """
    Decline invitation (polite rejection).

    Args:
        token: Raw invitation token from URL
        db: Database session (AsyncSession)

    Returns:
        InvitationDeclined with declined_at timestamp

    Raises:
        HTTPException(400): If cannot decline
        HTTPException(404): If invitation not found
    """
    return await invitation_service.decline_invitation(token=token, db=db)


# ============================================================================
# Team Management Endpoints (List/Cancel)
# ============================================================================

@router.get(
    "/teams/{team_id}/invitations",
    response_model=list[InvitationResponse],
    summary="List team invitations",
    description="""
    List all invitations for a team (pending, accepted, declined).

    **Permissions**:
    - Team owner/admin only

    **Filters** (query params):
    - status: Filter by status (pending, accepted, declined, expired)
    - email: Filter by invited email

    **Pagination**:
    - limit: Max results per page (default: 50)
    - offset: Skip N results (default: 0)
    """,
)
async def list_team_invitations(
    team_id: UUID,
    invitation_status: Optional[str] = None,
    email: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[InvitationResponse]:
    """
    List team invitations with optional filters.

    Args:
        team_id: Team UUID
        invitation_status: Filter by invitation status (optional)
        email: Filter by invited email (optional)
        limit: Max results per page
        offset: Skip N results
        current_user: Authenticated user (must be team admin/owner)
        db: Database session (AsyncSession)

    Returns:
        List of InvitationResponse

    Raises:
        HTTPException(403): If user not authorized
    """
    # RBAC enforcement — check user is team admin/owner
    member_result = await db.execute(
        select(TeamMember).where(
            TeamMember.team_id == team_id,
            TeamMember.user_id == current_user.id,
            TeamMember.deleted_at.is_(None),
        )
    )
    team_member = member_result.scalar_one_or_none()

    if not team_member or team_member.role not in ("owner", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only team owners and admins can view invitations"
        )

    # List invitations — async service (C-182-CF-02: no more db.run_sync bridge)
    return await invitation_service.list_team_invitations(
        team_id=team_id,
        db=db,
        status_filter=invitation_status,
        email_filter=email,
        limit=limit,
        offset=offset,
    )


@router.delete(
    "/invitations/{invitation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cancel invitation",
    description="""
    Cancel pending invitation (admin action).

    **Permissions**:
    - Team owner/admin only

    **Effect**:
    - Status changed to 'cancelled'
    - Invitation token invalidated
    - Cannot be accepted/declined after cancellation

    **Errors**:
    - 400: Invitation already accepted/declined (cannot cancel)
    - 403: User not authorized
    - 404: Invitation not found
    """,
)
async def cancel_invitation(
    invitation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Cancel pending invitation (admin action).

    Args:
        invitation_id: Invitation UUID
        current_user: Authenticated user (must be team admin/owner)
        db: Database session (AsyncSession)

    Raises:
        HTTPException(400): If cannot cancel
        HTTPException(403): If user not authorized
        HTTPException(404): If invitation not found
    """
    # Fetch invitation for RBAC check
    inv_result = await db.execute(
        select(TeamInvitation).where(TeamInvitation.id == invitation_id)
    )
    invitation = inv_result.scalar_one_or_none()

    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found"
        )

    # RBAC enforcement — check user is team admin/owner
    member_result = await db.execute(
        select(TeamMember).where(
            TeamMember.team_id == invitation.team_id,
            TeamMember.user_id == current_user.id,
            TeamMember.deleted_at.is_(None),
        )
    )
    team_member = member_result.scalar_one_or_none()

    if not team_member or team_member.role not in ("owner", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only team owners and admins can cancel invitations"
        )

    # Cancel invitation — async service (C-182-CF-02: no more db.run_sync bridge)
    await invitation_service.cancel_invitation(
        invitation_id=invitation_id,
        cancelled_by_user_id=current_user.id,
        db=db,
    )
