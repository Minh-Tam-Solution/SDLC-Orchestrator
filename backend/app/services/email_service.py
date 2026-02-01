"""
Email Service

Multi-provider email service for team invitations and notifications.
Supports Gmail SMTP (development) and SendGrid API (production).

Security Features:
- Template-based emails (prevent injection)
- Rate limiting (handled at service layer)
- HTML escaping (prevent XSS)
- TLS encryption for SMTP

Reference: ADR-043-Team-Invitation-System-Architecture.md
"""
import logging
import os
import smtplib
import ssl
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

import requests
from fastapi import HTTPException

from app.core.config import settings

logger = logging.getLogger(__name__)

# ============================================================================
# Email Configuration
# ============================================================================

EMAIL_PROVIDER = os.getenv("EMAIL_PROVIDER", "gmail")  # "gmail" or "sendgrid"

# Gmail SMTP Configuration
GMAIL_EMAIL = os.getenv("GMAIL_EMAIL", "")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")
GMAIL_SMTP_SERVER = "smtp.gmail.com"
GMAIL_SMTP_PORT = 587

# SendGrid Configuration
SENDGRID_API_URL = "https://api.sendgrid.com/v3/mail/send"
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "")

# Common Configuration
FROM_EMAIL = os.getenv("EMAIL_FROM_ADDRESS", "") or GMAIL_EMAIL or "noreply@sdlc-orchestrator.com"
FROM_NAME = os.getenv("EMAIL_FROM_NAME", "SDLC Orchestrator")

# Sandbox Mode (logs instead of sending)
EMAIL_SANDBOX_MODE = os.getenv("EMAIL_SANDBOX_MODE", "false").lower() == "true"


# ============================================================================
# Email Templates
# ============================================================================

def get_invitation_email_html(
    team_name: str,
    inviter_name: str,
    invitation_link: str,
    role: str,
    expires_at: datetime,
    message: Optional[str] = None,
) -> str:
    """
    Generate HTML email for team invitation.

    Args:
        team_name: Name of team user is invited to
        inviter_name: Name of person who sent invitation
        invitation_link: Full URL with invitation token
        role: Team role (owner, admin, member)
        expires_at: Invitation expiry datetime
        message: Optional personal message from inviter

    Returns:
        HTML string for email body
    """
    # Format expiry date for display
    expiry_str = expires_at.strftime("%B %d, %Y at %I:%M %p UTC")

    # HTML escape message to prevent XSS
    message_html = ""
    if message:
        message_safe = (
            message.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#x27;")
        )
        message_html = f"""
        <div style="background-color: #f8f9fa; border-left: 4px solid #0066cc; padding: 16px; margin: 24px 0;">
            <p style="margin: 0; color: #495057; font-style: italic;">"{message_safe}"</p>
        </div>
        """

    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Team Invitation</title>
    </head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #212529; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background-color: #ffffff; border: 1px solid #dee2e6; border-radius: 8px; overflow: hidden;">
            <!-- Header -->
            <div style="background-color: #0066cc; color: white; padding: 32px 24px; text-align: center;">
                <h1 style="margin: 0; font-size: 28px; font-weight: 600;">You're Invited!</h1>
            </div>

            <!-- Body -->
            <div style="padding: 32px 24px;">
                <p style="font-size: 16px; margin: 0 0 16px 0;">Hi there,</p>

                <p style="font-size: 16px; margin: 0 0 16px 0;">
                    <strong>{inviter_name}</strong> has invited you to join the team <strong>{team_name}</strong> as a <strong>{role}</strong>.
                </p>

                {message_html}

                <p style="font-size: 16px; margin: 16px 0;">
                    To accept this invitation and join the team, click the button below:
                </p>

                <!-- CTA Button -->
                <div style="text-align: center; margin: 32px 0;">
                    <a href="{invitation_link}" style="display: inline-block; background-color: #0066cc; color: white; padding: 14px 32px; text-decoration: none; border-radius: 6px; font-size: 16px; font-weight: 600;">Accept Invitation</a>
                </div>

                <p style="font-size: 14px; color: #6c757d; margin: 16px 0;">
                    Or copy and paste this link into your browser:<br>
                    <a href="{invitation_link}" style="color: #0066cc; word-break: break-all;">{invitation_link}</a>
                </p>

                <!-- Expiry Notice -->
                <div style="background-color: #fff3cd; border: 1px solid #ffeeba; border-radius: 6px; padding: 16px; margin: 24px 0;">
                    <p style="margin: 0; font-size: 14px; color: #856404;">
                        ⏰ <strong>Important:</strong> This invitation expires on {expiry_str}
                    </p>
                </div>

                <p style="font-size: 14px; color: #6c757d; margin: 16px 0;">
                    If you don't want to join this team, you can simply ignore this email or <a href="{invitation_link.replace('/accept', '/decline')}" style="color: #0066cc;">decline the invitation</a>.
                </p>
            </div>

            <!-- Footer -->
            <div style="background-color: #f8f9fa; padding: 24px; text-align: center; border-top: 1px solid #dee2e6;">
                <p style="margin: 0 0 8px 0; font-size: 14px; color: #6c757d;">
                    Sent by <strong>SDLC Orchestrator</strong>
                </p>
                <p style="margin: 0; font-size: 12px; color: #adb5bd;">
                    This is an automated email. Please do not reply to this message.
                </p>
            </div>
        </div>

        <!-- Legal Footer -->
        <div style="text-align: center; padding: 24px 0; color: #adb5bd; font-size: 12px;">
            <p style="margin: 0;">
                SDLC Orchestrator - Operating System for Software 3.0<br>
                © 2026 SDLC Orchestrator. All rights reserved.
            </p>
        </div>
    </body>
    </html>
    """

    return html


def get_invitation_confirmation_html(
    team_name: str,
    role: str,
    dashboard_link: str,
) -> str:
    """
    Generate HTML email for invitation acceptance confirmation.

    Args:
        team_name: Name of team user joined
        role: Team role assigned
        dashboard_link: URL to team dashboard

    Returns:
        HTML string for confirmation email body
    """
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Welcome to the Team!</title>
    </head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #212529; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background-color: #ffffff; border: 1px solid #dee2e6; border-radius: 8px; overflow: hidden;">
            <!-- Header -->
            <div style="background-color: #28a745; color: white; padding: 32px 24px; text-align: center;">
                <h1 style="margin: 0; font-size: 28px; font-weight: 600;">Welcome to the Team!</h1>
            </div>

            <!-- Body -->
            <div style="padding: 32px 24px;">
                <p style="font-size: 16px; margin: 0 0 16px 0;">Congratulations! 🎉</p>

                <p style="font-size: 16px; margin: 0 0 16px 0;">
                    You've successfully joined <strong>{team_name}</strong> as a <strong>{role}</strong>.
                </p>

                <p style="font-size: 16px; margin: 16px 0;">
                    You now have access to the team dashboard and can start collaborating with your teammates.
                </p>

                <!-- CTA Button -->
                <div style="text-align: center; margin: 32px 0;">
                    <a href="{dashboard_link}" style="display: inline-block; background-color: #28a745; color: white; padding: 14px 32px; text-decoration: none; border-radius: 6px; font-size: 16px; font-weight: 600;">Go to Team Dashboard</a>
                </div>

                <!-- Next Steps -->
                <div style="background-color: #f8f9fa; border-radius: 6px; padding: 24px; margin: 24px 0;">
                    <h3 style="margin: 0 0 16px 0; font-size: 18px; color: #212529;">Next Steps:</h3>
                    <ul style="margin: 0; padding-left: 20px; font-size: 14px; color: #495057;">
                        <li style="margin-bottom: 8px;">Complete your profile setup</li>
                        <li style="margin-bottom: 8px;">Review team projects and gates</li>
                        <li style="margin-bottom: 8px;">Connect with team members</li>
                        <li>Start contributing to your first project</li>
                    </ul>
                </div>

                <p style="font-size: 14px; color: #6c757d; margin: 16px 0;">
                    Need help getting started? Check out our <a href="https://docs.sdlc-orchestrator.com" style="color: #0066cc;">documentation</a> or contact support.
                </p>
            </div>

            <!-- Footer -->
            <div style="background-color: #f8f9fa; padding: 24px; text-align: center; border-top: 1px solid #dee2e6;">
                <p style="margin: 0 0 8px 0; font-size: 14px; color: #6c757d;">
                    Sent by <strong>SDLC Orchestrator</strong>
                </p>
                <p style="margin: 0; font-size: 12px; color: #adb5bd;">
                    This is an automated email. Please do not reply to this message.
                </p>
            </div>
        </div>

        <!-- Legal Footer -->
        <div style="text-align: center; padding: 24px 0; color: #adb5bd; font-size: 12px;">
            <p style="margin: 0;">
                SDLC Orchestrator - Operating System for Software 3.0<br>
                © 2026 SDLC Orchestrator. All rights reserved.
            </p>
        </div>
    </body>
    </html>
    """

    return html


# ============================================================================
# Email Sending Functions
# ============================================================================

def send_email_via_gmail(
    to_email: str,
    subject: str,
    html_content: str,
    from_email: str = FROM_EMAIL,
    from_name: str = FROM_NAME,
) -> None:
    """
    Send email via Gmail SMTP with App Password.

    Args:
        to_email: Recipient email address
        subject: Email subject line
        html_content: HTML email body
        from_email: Sender email address
        from_name: Sender display name

    Raises:
        HTTPException(500): If email send fails
    """
    if not GMAIL_EMAIL or not GMAIL_APP_PASSWORD:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "email_not_configured",
                "message": "Gmail credentials not configured. Set GMAIL_EMAIL and GMAIL_APP_PASSWORD.",
            },
        )

    # Create message
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{from_name} <{from_email}>"
    msg["To"] = to_email

    # Attach HTML content
    html_part = MIMEText(html_content, "html")
    msg.attach(html_part)

    try:
        # Create secure connection
        context = ssl.create_default_context()

        with smtplib.SMTP(GMAIL_SMTP_SERVER, GMAIL_SMTP_PORT) as server:
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()
            server.login(GMAIL_EMAIL, GMAIL_APP_PASSWORD)
            server.sendmail(from_email, to_email, msg.as_string())

        logger.info(f"✅ Email sent via Gmail to: {to_email}")

    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"Gmail authentication failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "email_auth_failed",
                "message": "Gmail authentication failed. Check GMAIL_EMAIL and GMAIL_APP_PASSWORD.",
            },
        )
    except smtplib.SMTPException as e:
        logger.error(f"Gmail SMTP error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "email_send_failed",
                "message": f"Gmail SMTP error: {str(e)}",
            },
        )


def send_email_via_sendgrid(
    to_email: str,
    subject: str,
    html_content: str,
    from_email: str = FROM_EMAIL,
    from_name: str = FROM_NAME,
) -> None:
    """
    Send email via SendGrid API.

    Args:
        to_email: Recipient email address
        subject: Email subject line
        html_content: HTML email body
        from_email: Sender email address
        from_name: Sender display name

    Raises:
        HTTPException(500): If email send fails
    """
    if not SENDGRID_API_KEY:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "email_not_configured",
                "message": "SendGrid API key not configured. Set SENDGRID_API_KEY.",
            },
        )

    # SendGrid API request payload
    payload = {
        "personalizations": [
            {
                "to": [{"email": to_email}],
                "subject": subject,
            }
        ],
        "from": {
            "email": from_email,
            "name": from_name,
        },
        "content": [
            {
                "type": "text/html",
                "value": html_content,
            }
        ],
    }

    try:
        response = requests.post(
            SENDGRID_API_URL,
            json=payload,
            headers={
                "Authorization": f"Bearer {SENDGRID_API_KEY}",
                "Content-Type": "application/json",
            },
            timeout=10,
        )

        if response.status_code != 202:
            error_detail = response.json() if response.text else {}
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "email_send_failed",
                    "message": "Failed to send email via SendGrid",
                    "sendgrid_error": error_detail,
                },
            )

        logger.info(f"✅ Email sent via SendGrid to: {to_email}")

    except requests.RequestException as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "email_send_failed",
                "message": f"SendGrid API request failed: {str(e)}",
            },
        )


def send_email(
    to_email: str,
    subject: str,
    html_content: str,
    from_email: str = FROM_EMAIL,
    from_name: str = FROM_NAME,
) -> None:
    """
    Send email using configured provider (Gmail or SendGrid).

    Args:
        to_email: Recipient email address
        subject: Email subject line
        html_content: HTML email body
        from_email: Sender email address
        from_name: Sender display name

    Raises:
        HTTPException(500): If email send fails
    """
    # Sandbox mode: log instead of sending
    if EMAIL_SANDBOX_MODE:
        logger.info(
            f"[SANDBOX MODE] Email to {to_email}:\n"
            f"Subject: {subject}\n"
            f"Body preview: {html_content[:300]}..."
        )
        print(f"\n{'='*60}")
        print(f"📧 [SANDBOX] Email would be sent to: {to_email}")
        print(f"   Subject: {subject}")
        print(f"   Provider: {EMAIL_PROVIDER}")
        print(f"{'='*60}\n")
        return

    # Route to appropriate provider
    if EMAIL_PROVIDER == "gmail":
        send_email_via_gmail(to_email, subject, html_content, from_email, from_name)
    elif EMAIL_PROVIDER == "sendgrid":
        send_email_via_sendgrid(to_email, subject, html_content, from_email, from_name)
    else:
        # Fallback: try Gmail, then SendGrid
        if GMAIL_EMAIL and GMAIL_APP_PASSWORD:
            send_email_via_gmail(to_email, subject, html_content, from_email, from_name)
        elif SENDGRID_API_KEY:
            send_email_via_sendgrid(to_email, subject, html_content, from_email, from_name)
        else:
            logger.warning(f"[NO EMAIL CONFIG] Would send to {to_email}: {subject}")
            print(f"\n⚠️ Email not sent (no provider configured): {to_email}")


def send_invitation_email(
    to_email: str,
    invitation_token: str,
    team_name: str,
    inviter_name: str,
    expires_at: datetime,
    role: str = "member",
    message: Optional[str] = None,
) -> None:
    """
    Send team invitation email with magic link.

    Args:
        to_email: Email address of invitee
        invitation_token: Raw invitation token (for URL)
        team_name: Name of team
        inviter_name: Name of person who sent invitation
        expires_at: Invitation expiry datetime
        role: Team role (default: member)
        message: Optional personal message from inviter

    Raises:
        HTTPException(500): If email send fails
    """
    # Build invitation link
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    invitation_link = f"{frontend_url}/invitations/accept?token={invitation_token}"

    # Generate HTML email
    html_content = get_invitation_email_html(
        team_name=team_name,
        inviter_name=inviter_name,
        invitation_link=invitation_link,
        role=role,
        expires_at=expires_at,
        message=message,
    )

    # Send email
    subject = f"{inviter_name} invited you to join {team_name}"

    send_email(
        to_email=to_email,
        subject=subject,
        html_content=html_content,
    )


def send_invitation_accepted_email(
    to_email: str,
    team_name: str,
    role: str,
    team_id: str,
) -> None:
    """
    Send confirmation email after invitation acceptance.

    Args:
        to_email: Email address of new team member
        team_name: Name of team
        role: Team role assigned
        team_id: Team UUID for dashboard link

    Raises:
        HTTPException(500): If email send fails
    """
    # Build dashboard link
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    dashboard_link = f"{frontend_url}/teams/{team_id}"

    # Generate HTML email
    html_content = get_invitation_confirmation_html(
        team_name=team_name,
        role=role,
        dashboard_link=dashboard_link,
    )

    # Send email
    subject = f"Welcome to {team_name}!"

    send_email(
        to_email=to_email,
        subject=subject,
        html_content=html_content,
    )


def send_invitation_declined_notification(
    to_email: str,
    team_name: str,
    invitee_email: str,
) -> None:
    """
    Notify team admin when invitation is declined.

    Args:
        to_email: Email address of team admin/owner
        team_name: Name of team
        invitee_email: Email address of person who declined

    Raises:
        HTTPException(500): If email send fails
    """
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Invitation Declined</title>
    </head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #212529; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background-color: #ffffff; border: 1px solid #dee2e6; border-radius: 8px; overflow: hidden;">
            <div style="background-color: #6c757d; color: white; padding: 32px 24px; text-align: center;">
                <h1 style="margin: 0; font-size: 28px; font-weight: 600;">Invitation Declined</h1>
            </div>

            <div style="padding: 32px 24px;">
                <p style="font-size: 16px; margin: 0 0 16px 0;">
                    {invitee_email} has declined the invitation to join <strong>{team_name}</strong>.
                </p>

                <p style="font-size: 14px; color: #6c757d; margin: 16px 0;">
                    You can send a new invitation at any time if needed.
                </p>
            </div>

            <div style="background-color: #f8f9fa; padding: 24px; text-align: center; border-top: 1px solid #dee2e6;">
                <p style="margin: 0; font-size: 12px; color: #adb5bd;">
                    This is an automated notification from SDLC Orchestrator.
                </p>
            </div>
        </div>
    </body>
    </html>
    """

    subject = f"Invitation to {team_name} was declined"

    send_email(
        to_email=to_email,
        subject=subject,
        html_content=html,
    )
