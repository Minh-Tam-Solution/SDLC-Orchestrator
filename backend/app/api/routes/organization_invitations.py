"""
Organization Invitation API Endpoints

RESTful API for secure organization invitation system with hash-based tokens.

Security Features:
- Rate limiting (Redis-based, 50/hour per org)
- Token hashing (SHA256, never store raw)
- Audit trail (IP, user agent, timestamps)
- Email verification
- One-time use enforcement
- RBAC (owner/admin can invite, only owner can invite admin)

Reference: ADR-047-Organization-Invitation-System.md
Sprint: 146
"""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.organization import Organization, UserOrganization
from app.models.organization_invitation import OrganizationInvitation
from app.schemas.organization_invitation import (
    OrgInvitationCreate,
    OrgInvitationResponse,
    OrgInvitationDetails,
    OrgInvitationAccepted,
    OrgInvitationDeclined,
    OrgInvitationResent,
)
from app.services import organization_invitation_service
from app.services.email_service import send_invitation_email

router = APIRouter(tags=["organization-invitations"])


# ============================================================================
# Organization Admin Endpoints (Authenticated)
# ============================================================================

@router.post(
    "/organizations/{organization_id}/invitations",
    response_model=OrgInvitationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Send organization invitation",
    description="""
    Send invitation to join organization with secure token.

    **Security**:
    - Rate limiting: 50 invitations/hour per organization
    - Email rate limit: 10 invitations/day per email
    - Token hashing: SHA256 (never store raw)
    - Audit trail: IP address, user agent, timestamp

    **Permissions**:
    - Organization owner: Can invite with admin/member role
    - Organization admin: Can invite members only
    - Note: Cannot invite as 'owner' (CTO constraint)

    **Errors**:
    - 403: User not authorized to invite
    - 404: Organization not found
    - 409: Pending invitation already exists
    - 429: Rate limit exceeded
    """,
)
async def send_invitation(
    organization_id: UUID,
    data: OrgInvitationCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> OrgInvitationResponse:
    """
    Send organization invitation with secure token.

    Args:
        organization_id: Organization UUID
        data: Invitation creation data
        request: FastAPI request (for IP/user agent)
        current_user: Authenticated user sending invitation
        db: Database session

    Returns:
        OrgInvitationResponse with invitation_id, email, status, expires_at
    """
    # Extract audit trail info
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("User-Agent")

    # Send invitation (returns response + raw token for email)
    response, raw_token = organization_invitation_service.send_org_invitation(
        organization_id=organization_id,
        data=data,
        invited_by_user_id=current_user.id,
        db=db,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    # Send invitation email (async)
    try:
        send_invitation_email(
            to_email=response.invited_email,
            invitation_token=raw_token,
            team_name=response.organization_name,  # Reuse team_name parameter for org
            inviter_name=response.invited_by["display_name"],
            expires_at=response.expires_at,
            message=data.message,
        )
    except Exception as e:
        import logging
        logging.error(f"Failed to send organization invitation email: {str(e)}")

    return response


@router.post(
    "/org-invitations/{invitation_id}/resend",
    response_model=OrgInvitationResent,
    summary="Resend organization invitation email",
    description="""
    Resend invitation email with new token.

    **Security**:
    - Generates NEW token (invalidates old token)
    - Rate limiting: Max 3 resends per invitation
    - Cooldown: 5 minutes between resends

    **Permissions**:
    - Organization owner/admin only
    """,
)
async def resend_invitation(
    invitation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> OrgInvitationResent:
    """
    Resend organization invitation email with new token.
    """
    # Get invitation first for permission check
    invitation = db.query(OrganizationInvitation).filter(
        OrganizationInvitation.id == invitation_id
    ).first()

    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "invitation_not_found", "message": "Invitation not found"}
        )

    # RBAC: Check user is org owner/admin
    membership = db.query(UserOrganization).filter(
        UserOrganization.organization_id == invitation.organization_id,
        UserOrganization.user_id == current_user.id,
        UserOrganization.role.in_(["owner", "admin"])
    ).first()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "not_authorized",
                "message": "You must be an organization owner or admin to resend invitations"
            }
        )

    # Resend invitation
    response, raw_token = organization_invitation_service.resend_org_invitation(
        invitation_id=invitation_id,
        db=db,
    )

    # Refresh invitation and send email
    invitation = db.query(OrganizationInvitation).filter(
        OrganizationInvitation.id == invitation_id
    ).first()

    org = db.query(Organization).filter(Organization.id == invitation.organization_id).first()
    inviter = db.query(User).filter(User.id == invitation.invited_by).first()

    try:
        send_invitation_email(
            to_email=invitation.invited_email,
            invitation_token=raw_token,
            team_name=org.name if org else "Organization",
            inviter_name=inviter.display_name or inviter.username if inviter else "Admin",
            expires_at=response.expires_at,
            message=None,
        )
    except Exception as e:
        import logging
        logging.error(f"Failed to resend organization invitation email: {str(e)}")

    return response


# ============================================================================
# Public Endpoints (No Authentication)
# ============================================================================

@router.get(
    "/org-invitations/{token}",
    response_model=OrgInvitationDetails,
    summary="Get organization invitation details by token",
    description="""
    Get invitation details for acceptance page (public endpoint).

    **Security**:
    - No authentication required (token is the credential)
    - Constant-time token verification (prevents timing attacks)
    """,
)
async def get_invitation_by_token(
    token: str,
    db: Session = Depends(get_db),
) -> OrgInvitationDetails:
    """
    Get organization invitation details by token (public endpoint).
    """
    return organization_invitation_service.get_org_invitation_by_token(token=token, db=db)


@router.post(
    "/org-invitations/{token}/accept",
    response_model=OrgInvitationAccepted,
    summary="Accept organization invitation",
    description="""
    Accept invitation and create organization membership.

    **Security**:
    - Requires authentication (user must be logged in)
    - Email verification (user email must match invited email)
    - One-time use (status change prevents replay)
    """,
)
async def accept_invitation(
    token: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> OrgInvitationAccepted:
    """
    Accept organization invitation and create membership.
    """
    return organization_invitation_service.accept_org_invitation(
        token=token,
        user_id=current_user.id,
        user_email=current_user.email,
        db=db,
    )


@router.post(
    "/org-invitations/{token}/decline",
    response_model=OrgInvitationDeclined,
    summary="Decline organization invitation",
    description="""
    Decline invitation politely (no membership created).

    **Security**:
    - No authentication required (anonymous decline allowed)
    - One-time use (status change prevents replay)
    """,
)
async def decline_invitation(
    token: str,
    db: Session = Depends(get_db),
) -> OrgInvitationDeclined:
    """
    Decline organization invitation (polite rejection).
    """
    return organization_invitation_service.decline_org_invitation(token=token, db=db)


# ============================================================================
# Organization Management Endpoints (List/Cancel)
# ============================================================================

@router.get(
    "/organizations/{organization_id}/invitations",
    response_model=list[OrgInvitationResponse],
    summary="List organization invitations",
    description="""
    List all invitations for an organization (pending, accepted, declined).

    **Permissions**:
    - Organization owner/admin only

    **Filters** (query params):
    - status: Filter by status (pending, accepted, declined, expired, cancelled)
    - email: Filter by invited email

    **Pagination**:
    - limit: Max results per page (default: 50)
    - offset: Skip N results (default: 0)
    """,
)
async def list_org_invitations(
    organization_id: UUID,
    status: Optional[str] = None,
    email: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[OrgInvitationResponse]:
    """
    List organization invitations with optional filters.
    """
    # Check user is org owner/admin
    membership = db.query(UserOrganization).filter(
        UserOrganization.organization_id == organization_id,
        UserOrganization.user_id == current_user.id,
        UserOrganization.role.in_(["owner", "admin"])
    ).first()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only organization owners and admins can view invitations"
        )

    return organization_invitation_service.list_org_invitations(
        organization_id=organization_id,
        db=db,
        status_filter=status,
        email_filter=email,
        limit=limit,
        offset=offset
    )


@router.delete(
    "/org-invitations/{invitation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cancel organization invitation",
    description="""
    Cancel pending invitation (admin action).

    **Permissions**:
    - Organization owner/admin only

    **Effect**:
    - Status changed to 'cancelled'
    - Invitation token invalidated
    """,
)
async def cancel_invitation(
    invitation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """
    Cancel pending organization invitation (admin action).
    """
    organization_invitation_service.cancel_org_invitation(
        invitation_id=invitation_id,
        cancelled_by_user_id=current_user.id,
        db=db
    )
