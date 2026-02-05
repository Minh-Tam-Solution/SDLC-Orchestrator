"""
=========================================================================
Notification Service - Alert & Notification Management
SDLC Orchestrator - Stage 03 (BUILD)

Version: 1.1.0
Date: February 3, 2026
Status: ACTIVE - Sprint 153 (WebSocket Integration)
Authority: Backend Lead + CTO Approved
Foundation: Sprint 21 Plan, ADR-007 Approved, Sprint 153 Plan
Framework: SDLC 6.0.3 Complete Lifecycle

Purpose:
- Send email notifications for compliance violations
- Send Slack/Teams webhook notifications
- Create in-app notification records
- Real-time WebSocket notifications (Sprint 153)

Notification Types:
1. COMPLIANCE_VIOLATION: Critical/high violations detected
2. SCAN_COMPLETED: Compliance scan finished
3. GATE_APPROVAL_REQUIRED: Gate needs approval
4. GATE_APPROVED: Gate was approved
5. GATE_REJECTED: Gate was rejected
6. EVIDENCE_UPLOADED: New evidence uploaded
7. PROJECT_CREATED: New project created
8. MEMBER_INVITED: Member invited to project

Channels:
- Email (SMTP/SendGrid)
- Slack (Webhook)
- Microsoft Teams (Webhook)
- In-app (Database + WebSocket)
- WebSocket (Real-time push - Sprint 153)

Zero Mock Policy: Production-ready notification system
=========================================================================
"""

import logging
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID

import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.middleware.business_metrics import NotificationMetrics
from app.models.project import Project
from app.models.support import Notification
from app.models.user import User

logger = logging.getLogger(__name__)


# ============================================================================
# Notification Types & Configuration
# ============================================================================


class NotificationType(str, Enum):
    """Types of notifications."""

    COMPLIANCE_VIOLATION = "compliance_violation"
    SCAN_COMPLETED = "scan_completed"
    GATE_APPROVAL_REQUIRED = "gate_approval_required"
    GATE_APPROVED = "gate_approved"
    GATE_REJECTED = "gate_rejected"
    EVIDENCE_UPLOADED = "evidence_uploaded"
    PROJECT_CREATED = "project_created"
    MEMBER_INVITED = "member_invited"


class NotificationChannel(str, Enum):
    """Notification delivery channels."""

    EMAIL = "email"
    SLACK = "slack"
    TEAMS = "teams"
    IN_APP = "in_app"
    WEBHOOK = "webhook"
    WEBSOCKET = "websocket"  # Sprint 153 - Real-time push


class NotificationPriority(str, Enum):
    """Notification priority levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class NotificationPayload:
    """Notification payload data."""

    type: NotificationType
    priority: NotificationPriority
    title: str
    message: str
    project_id: Optional[UUID] = None
    project_name: Optional[str] = None
    user_id: Optional[UUID] = None
    metadata: dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


# ============================================================================
# Notification Service
# ============================================================================


class NotificationService:
    """
    Service for sending notifications across multiple channels.

    Features:
    - Multi-channel delivery (email, Slack, Teams, in-app)
    - Priority-based routing
    - Template-based message formatting
    - Delivery status tracking

    Usage:
        notification_service = NotificationService(db)

        await notification_service.send_violation_alert(
            project=project,
            violations=violations,
            compliance_score=85,
            recipients=[owner, pm],
        )
    """

    def __init__(self, db: Optional[AsyncSession] = None):
        """
        Initialize notification service.

        Args:
            db: Optional database session for in-app notifications
        """
        self.db = db
        self.email_enabled = bool(getattr(settings, "SMTP_HOST", None))
        self.slack_enabled = bool(getattr(settings, "SLACK_WEBHOOK_URL", None))
        self.teams_enabled = bool(getattr(settings, "TEAMS_WEBHOOK_URL", None))

    # ========================================================================
    # High-Level Notification Methods
    # ========================================================================

    async def send_violation_alert(
        self,
        project: Project,
        violations: list,
        compliance_score: int,
        recipients: list[User],
    ) -> dict[str, Any]:
        """
        Send compliance violation alert to project stakeholders.

        Args:
            project: Project with violations
            violations: List of violation objects
            compliance_score: Current compliance score
            recipients: List of users to notify

        Returns:
            Delivery status for each channel
        """
        # Count violations by severity
        critical_count = len([v for v in violations if v.severity == "critical"])
        high_count = len([v for v in violations if v.severity == "high"])
        medium_count = len([v for v in violations if v.severity == "medium"])

        # Determine priority
        if critical_count > 0:
            priority = NotificationPriority.CRITICAL
        elif high_count > 0:
            priority = NotificationPriority.HIGH
        else:
            priority = NotificationPriority.MEDIUM

        # Build notification payload
        payload = NotificationPayload(
            type=NotificationType.COMPLIANCE_VIOLATION,
            priority=priority,
            title=f"Compliance Violations Detected: {project.name}",
            message=self._format_violation_message(
                project=project,
                violations=violations,
                compliance_score=compliance_score,
            ),
            project_id=project.id,
            project_name=project.name,
            metadata={
                "compliance_score": compliance_score,
                "violations_count": len(violations),
                "critical_count": critical_count,
                "high_count": high_count,
                "medium_count": medium_count,
            },
        )

        # Send to all channels
        results = await self._send_to_all_channels(payload, recipients)

        logger.info(
            f"Sent violation alert for project {project.name}: "
            f"violations={len(violations)}, recipients={len(recipients)}"
        )

        return results

    async def send_scan_completed_notification(
        self,
        project: Project,
        compliance_score: int,
        violations_count: int,
        triggered_by: Optional[User] = None,
    ) -> dict[str, Any]:
        """
        Send notification when compliance scan completes.

        Args:
            project: Scanned project
            compliance_score: Scan result score
            violations_count: Number of violations
            triggered_by: User who triggered scan

        Returns:
            Delivery status
        """
        # Determine priority based on score
        if compliance_score < 50:
            priority = NotificationPriority.HIGH
        elif compliance_score < 80:
            priority = NotificationPriority.MEDIUM
        else:
            priority = NotificationPriority.LOW

        payload = NotificationPayload(
            type=NotificationType.SCAN_COMPLETED,
            priority=priority,
            title=f"Compliance Scan Completed: {project.name}",
            message=self._format_scan_completed_message(
                project=project,
                compliance_score=compliance_score,
                violations_count=violations_count,
            ),
            project_id=project.id,
            project_name=project.name,
            user_id=triggered_by.id if triggered_by else None,
            metadata={
                "compliance_score": compliance_score,
                "violations_count": violations_count,
            },
        )

        # Send only to triggered user (if any) and in-app
        recipients = [triggered_by] if triggered_by else []
        return await self._send_to_all_channels(payload, recipients)

    async def send_gate_approval_notification(
        self,
        project: Project,
        gate_name: str,
        gate_code: str,
        approvers: list[User],
        submitted_by: User,
    ) -> dict[str, Any]:
        """
        Send notification when gate needs approval.

        Args:
            project: Project containing the gate
            gate_name: Name of the gate
            gate_code: Gate code (e.g., G2)
            approvers: List of users who can approve
            submitted_by: User who submitted the gate

        Returns:
            Delivery status
        """
        payload = NotificationPayload(
            type=NotificationType.GATE_APPROVAL_REQUIRED,
            priority=NotificationPriority.HIGH,
            title=f"Gate Approval Required: {gate_code} - {project.name}",
            message=(
                f"Gate {gate_code} ({gate_name}) in project {project.name} "
                f"has been submitted for approval by {submitted_by.name or submitted_by.email}.\n\n"
                f"Please review and approve/reject the gate."
            ),
            project_id=project.id,
            project_name=project.name,
            metadata={
                "gate_name": gate_name,
                "gate_code": gate_code,
                "submitted_by": str(submitted_by.id),
            },
        )

        return await self._send_to_all_channels(payload, approvers)

    async def send_gate_approved_notification(
        self,
        project: Project,
        gate_name: str,
        gate_code: str,
        approved_by: User,
        comments: Optional[str] = None,
        recipients: list[User] = None,
    ) -> dict[str, Any]:
        """
        Send notification when gate is approved.

        Args:
            project: Project containing the gate
            gate_name: Name of the gate
            gate_code: Gate code (e.g., G2)
            approved_by: User who approved
            comments: Approval comments
            recipients: List of users to notify

        Returns:
            Delivery status
        """
        message = (
            f"Gate {gate_code} ({gate_name}) in project {project.name} "
            f"has been *approved* by {approved_by.name or approved_by.email}."
        )
        if comments:
            message += f"\n\n**Comments:** {comments}"

        payload = NotificationPayload(
            type=NotificationType.GATE_APPROVED,
            priority=NotificationPriority.MEDIUM,
            title=f"Gate Approved: {gate_code} - {project.name}",
            message=message,
            project_id=project.id,
            project_name=project.name,
            metadata={
                "gate_name": gate_name,
                "gate_code": gate_code,
                "approved_by": str(approved_by.id),
                "approved_by_name": approved_by.name or approved_by.email,
                "comments": comments,
            },
        )

        return await self._send_to_all_channels(payload, recipients or [])

    async def send_gate_rejected_notification(
        self,
        project: Project,
        gate_name: str,
        gate_code: str,
        rejected_by: User,
        comments: Optional[str] = None,
        recipients: list[User] = None,
    ) -> dict[str, Any]:
        """
        Send notification when gate is rejected.

        Args:
            project: Project containing the gate
            gate_name: Name of the gate
            gate_code: Gate code (e.g., G2)
            rejected_by: User who rejected
            comments: Rejection reason
            recipients: List of users to notify

        Returns:
            Delivery status
        """
        message = (
            f"Gate {gate_code} ({gate_name}) in project {project.name} "
            f"has been *rejected* by {rejected_by.name or rejected_by.email}."
        )
        if comments:
            message += f"\n\n**Rejection Reason:** {comments}"
        message += "\n\nPlease review the feedback and resubmit when ready."

        payload = NotificationPayload(
            type=NotificationType.GATE_REJECTED,
            priority=NotificationPriority.HIGH,  # Higher priority for rejections
            title=f"Gate Rejected: {gate_code} - {project.name}",
            message=message,
            project_id=project.id,
            project_name=project.name,
            metadata={
                "gate_name": gate_name,
                "gate_code": gate_code,
                "rejected_by": str(rejected_by.id),
                "rejected_by_name": rejected_by.name or rejected_by.email,
                "comments": comments,
            },
        )

        return await self._send_to_all_channels(payload, recipients or [])

    # ========================================================================
    # Channel-Specific Methods
    # ========================================================================

    async def _send_to_all_channels(
        self,
        payload: NotificationPayload,
        recipients: list[User],
    ) -> dict[str, Any]:
        """
        Send notification to all enabled channels.

        Args:
            payload: Notification payload
            recipients: List of recipient users

        Returns:
            Delivery status per channel
        """
        results = {
            "in_app": False,
            "email": False,
            "slack": False,
            "teams": False,
            "websocket": False,  # Sprint 153
        }

        # Always send in-app notification
        if self.db:
            start_time = time.time()
            try:
                await self._send_in_app_notification(payload, recipients)
                results["in_app"] = True
                # Record successful in-app notification metrics
                delivery_seconds = time.time() - start_time
                NotificationMetrics.record_notification_sent(
                    channel="in_app",
                    notification_type=payload.type.value,
                    priority=payload.priority.value,
                    delivery_seconds=delivery_seconds,
                    status="success",
                )
            except Exception as e:
                logger.error(f"Failed to send in-app notification: {e}")
                NotificationMetrics.record_notification_failure(
                    channel="in_app",
                    notification_type=payload.type.value,
                    failure_reason=str(type(e).__name__),
                )

        # Send WebSocket notification (Sprint 153 - Real-time)
        start_time = time.time()
        try:
            ws_sent = await self._send_websocket_notification(payload, recipients)
            results["websocket"] = ws_sent > 0
            if ws_sent > 0:
                delivery_seconds = time.time() - start_time
                NotificationMetrics.record_notification_sent(
                    channel="websocket",
                    notification_type=payload.type.value,
                    priority=payload.priority.value,
                    delivery_seconds=delivery_seconds,
                    status="success",
                )
        except Exception as e:
            logger.error(f"Failed to send WebSocket notification: {e}")
            NotificationMetrics.record_notification_failure(
                channel="websocket",
                notification_type=payload.type.value,
                failure_reason=str(type(e).__name__),
            )

        # Send email for high/critical priority
        if self.email_enabled and payload.priority in (
            NotificationPriority.CRITICAL,
            NotificationPriority.HIGH,
        ):
            start_time = time.time()
            try:
                await self._send_email_notification(payload, recipients)
                results["email"] = True
                delivery_seconds = time.time() - start_time
                NotificationMetrics.record_notification_sent(
                    channel="email",
                    notification_type=payload.type.value,
                    priority=payload.priority.value,
                    delivery_seconds=delivery_seconds,
                    status="success",
                )
            except Exception as e:
                logger.error(f"Failed to send email notification: {e}")
                NotificationMetrics.record_notification_failure(
                    channel="email",
                    notification_type=payload.type.value,
                    failure_reason=str(type(e).__name__),
                )

        # Send Slack for critical violations
        if self.slack_enabled and payload.priority == NotificationPriority.CRITICAL:
            start_time = time.time()
            try:
                await self._send_slack_notification(payload)
                results["slack"] = True
                delivery_seconds = time.time() - start_time
                NotificationMetrics.record_notification_sent(
                    channel="slack",
                    notification_type=payload.type.value,
                    priority=payload.priority.value,
                    delivery_seconds=delivery_seconds,
                    status="success",
                )
            except Exception as e:
                logger.error(f"Failed to send Slack notification: {e}")
                NotificationMetrics.record_notification_failure(
                    channel="slack",
                    notification_type=payload.type.value,
                    failure_reason=str(type(e).__name__),
                )

        # Send Teams for critical violations
        if self.teams_enabled and payload.priority == NotificationPriority.CRITICAL:
            start_time = time.time()
            try:
                await self._send_teams_notification(payload)
                results["teams"] = True
                delivery_seconds = time.time() - start_time
                NotificationMetrics.record_notification_sent(
                    channel="teams",
                    notification_type=payload.type.value,
                    priority=payload.priority.value,
                    delivery_seconds=delivery_seconds,
                    status="success",
                )
            except Exception as e:
                logger.error(f"Failed to send Teams notification: {e}")
                NotificationMetrics.record_notification_failure(
                    channel="teams",
                    notification_type=payload.type.value,
                    failure_reason=str(type(e).__name__),
                )

        return results

    async def _send_in_app_notification(
        self,
        payload: NotificationPayload,
        recipients: list[User],
    ) -> None:
        """
        Create in-app notification records.

        Args:
            payload: Notification payload
            recipients: List of recipient users
        """
        if not self.db:
            return

        for user in recipients:
            notification = Notification(
                user_id=user.id,
                notification_type=payload.type.value,
                title=payload.title,
                message=payload.message[:1000],  # Truncate for DB
                priority=payload.priority.value,
                project_id=payload.project_id,
                extra_data=payload.metadata,  # 'metadata' is reserved in SQLAlchemy
                is_read=False,
            )
            self.db.add(notification)

        await self.db.commit()

        logger.debug(
            f"Created {len(recipients)} in-app notifications for {payload.type.value}"
        )

    async def _send_websocket_notification(
        self,
        payload: NotificationPayload,
        recipients: list[User],
    ) -> int:
        """
        Send real-time notification via WebSocket (Sprint 153).

        Args:
            payload: Notification payload
            recipients: List of recipient users

        Returns:
            Number of users successfully notified
        """
        try:
            from app.services.websocket_manager import (
                WebSocketEvent,
                WebSocketEventType,
                get_websocket_manager,
            )

            manager = get_websocket_manager()

            # Map notification type to WebSocket event type
            event_type_map = {
                NotificationType.GATE_APPROVED: WebSocketEventType.GATE_APPROVED,
                NotificationType.GATE_REJECTED: WebSocketEventType.GATE_REJECTED,
                NotificationType.GATE_APPROVAL_REQUIRED: WebSocketEventType.GATE_APPROVAL_REQUIRED,
                NotificationType.EVIDENCE_UPLOADED: WebSocketEventType.EVIDENCE_UPLOADED,
                NotificationType.COMPLIANCE_VIOLATION: WebSocketEventType.POLICY_VIOLATION,
                NotificationType.SCAN_COMPLETED: WebSocketEventType.NOTIFICATION_CREATED,
                NotificationType.PROJECT_CREATED: WebSocketEventType.PROJECT_UPDATED,
                NotificationType.MEMBER_INVITED: WebSocketEventType.MEMBER_ADDED,
            }

            ws_event_type = event_type_map.get(
                payload.type,
                WebSocketEventType.NOTIFICATION_CREATED,
            )

            # Create WebSocket event
            event = WebSocketEvent(
                event_type=ws_event_type,
                payload={
                    "title": payload.title,
                    "message": payload.message[:500],  # Truncate for WS
                    "priority": payload.priority.value,
                    "notification_type": payload.type.value,
                    "metadata": payload.metadata or {},
                },
                project_id=payload.project_id,
            )

            # Send to project subscribers if project_id exists
            if payload.project_id:
                sent_count = await manager.broadcast_to_project(
                    project_id=payload.project_id,
                    event=event,
                )
                logger.debug(
                    f"WebSocket broadcast to project {payload.project_id}: {sent_count} users"
                )
                return sent_count

            # Otherwise send to specific recipients
            if recipients:
                user_ids = [user.id for user in recipients]
                sent_count = await manager.broadcast_to_users(user_ids, event)
                logger.debug(f"WebSocket broadcast to {sent_count}/{len(recipients)} users")
                return sent_count

            return 0

        except ImportError:
            logger.warning("WebSocket manager not available")
            return 0
        except Exception as e:
            logger.error(f"WebSocket notification error: {e}")
            return 0

    async def _send_email_notification(
        self,
        payload: NotificationPayload,
        recipients: list[User],
    ) -> None:
        """
        Send email notification via SMTP.

        Args:
            payload: Notification payload
            recipients: List of recipient users
        """
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        smtp_host = getattr(settings, "SMTP_HOST", None)
        if not smtp_host:
            # SMTP not configured, log and skip
            for user in recipients:
                logger.info(
                    f"[SMTP not configured] Would send email to {user.email}: "
                    f"Subject: {payload.title}"
                )
            return

        smtp_port = getattr(settings, "SMTP_PORT", 587)
        smtp_user = getattr(settings, "SMTP_USER", None)
        smtp_password = getattr(settings, "SMTP_PASSWORD", None)
        smtp_use_tls = getattr(settings, "SMTP_USE_TLS", True)
        from_email = getattr(settings, "SMTP_FROM_EMAIL", "noreply@sdlc-orchestrator.com")
        from_name = getattr(settings, "SMTP_FROM_NAME", "SDLC Orchestrator")

        for user in recipients:
            try:
                # Build email message
                msg = MIMEMultipart("alternative")
                msg["Subject"] = payload.title
                msg["From"] = f"{from_name} <{from_email}>"
                msg["To"] = user.email

                # Plain text version
                text_content = f"""
{payload.title}

{payload.message}

---
Project: {payload.project_name or 'N/A'}
Priority: {payload.priority.value.upper()}

This is an automated message from SDLC Orchestrator.
"""

                # HTML version
                html_content = self._format_email_html(payload)

                msg.attach(MIMEText(text_content, "plain"))
                msg.attach(MIMEText(html_content, "html"))

                # Send email
                with smtplib.SMTP(smtp_host, smtp_port) as server:
                    if smtp_use_tls:
                        server.starttls()
                    if smtp_user and smtp_password:
                        server.login(smtp_user, smtp_password)
                    server.sendmail(from_email, user.email, msg.as_string())

                logger.info(f"Email sent to {user.email}: {payload.title}")

            except Exception as e:
                logger.error(f"Failed to send email to {user.email}: {e}")
                # Don't raise - continue with other recipients

    def _format_email_html(self, payload: NotificationPayload) -> str:
        """
        Format email body as HTML.

        Args:
            payload: Notification payload

        Returns:
            HTML formatted email body
        """
        priority_color = {
            "critical": "#dc2626",  # red-600
            "high": "#ea580c",      # orange-600
            "medium": "#ca8a04",    # yellow-600
            "low": "#16a34a",       # green-600
        }.get(payload.priority.value, "#6b7280")

        metadata_html = ""
        if payload.metadata:
            metadata_items = []
            if "compliance_score" in payload.metadata:
                metadata_items.append(
                    f"<li><strong>Compliance Score:</strong> {payload.metadata['compliance_score']}%</li>"
                )
            if "violations_count" in payload.metadata:
                metadata_items.append(
                    f"<li><strong>Violations:</strong> {payload.metadata['violations_count']}</li>"
                )
            if "critical_count" in payload.metadata:
                metadata_items.append(
                    f"<li><strong>Critical:</strong> {payload.metadata['critical_count']}</li>"
                )
            if "high_count" in payload.metadata:
                metadata_items.append(
                    f"<li><strong>High:</strong> {payload.metadata['high_count']}</li>"
                )
            if metadata_items:
                metadata_html = f"<ul>{''.join(metadata_items)}</ul>"

        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: {priority_color}; color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
        .content {{ background: #f9fafb; padding: 20px; border: 1px solid #e5e7eb; border-top: none; }}
        .footer {{ background: #f3f4f6; padding: 15px; font-size: 12px; color: #6b7280; border-radius: 0 0 8px 8px; }}
        .priority {{ display: inline-block; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; background: {priority_color}; color: white; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1 style="margin: 0; font-size: 20px;">{payload.title}</h1>
            <span class="priority">{payload.priority.value.upper()}</span>
        </div>
        <div class="content">
            <p>{payload.message.replace(chr(10), '<br>')}</p>
            {metadata_html}
            <p><strong>Project:</strong> {payload.project_name or 'N/A'}</p>
        </div>
        <div class="footer">
            <p>This is an automated message from SDLC Orchestrator.</p>
            <p>© 2025 SDLC Orchestrator. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
"""

    async def _send_slack_notification(
        self,
        payload: NotificationPayload,
    ) -> None:
        """
        Send Slack webhook notification.

        Args:
            payload: Notification payload
        """
        slack_url = getattr(settings, "SLACK_WEBHOOK_URL", None)
        if not slack_url:
            return

        # Build Slack message with blocks
        slack_message = {
            "text": payload.title,
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"🚨 {payload.title}",
                    },
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": payload.message,
                    },
                },
            ],
        }

        # Add metadata as context
        if payload.metadata:
            context_elements = []
            if "compliance_score" in payload.metadata:
                context_elements.append({
                    "type": "mrkdwn",
                    "text": f"*Score:* {payload.metadata['compliance_score']}%",
                })
            if "violations_count" in payload.metadata:
                context_elements.append({
                    "type": "mrkdwn",
                    "text": f"*Violations:* {payload.metadata['violations_count']}",
                })

            if context_elements:
                slack_message["blocks"].append({
                    "type": "context",
                    "elements": context_elements,
                })

        async with httpx.AsyncClient() as client:
            response = await client.post(
                slack_url,
                json=slack_message,
                timeout=10.0,
            )
            response.raise_for_status()

        logger.info(f"Sent Slack notification: {payload.title}")

    async def _send_teams_notification(
        self,
        payload: NotificationPayload,
    ) -> None:
        """
        Send Microsoft Teams webhook notification.

        Args:
            payload: Notification payload
        """
        teams_url = getattr(settings, "TEAMS_WEBHOOK_URL", None)
        if not teams_url:
            return

        # Build Teams adaptive card
        teams_message = {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": "FF0000" if payload.priority == NotificationPriority.CRITICAL else "FFA500",
            "summary": payload.title,
            "sections": [
                {
                    "activityTitle": payload.title,
                    "activitySubtitle": payload.project_name or "",
                    "text": payload.message,
                    "facts": [
                        {
                            "name": "Priority",
                            "value": payload.priority.value.upper(),
                        },
                    ],
                }
            ],
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                teams_url,
                json=teams_message,
                timeout=10.0,
            )
            response.raise_for_status()

        logger.info(f"Sent Teams notification: {payload.title}")

    # ========================================================================
    # Message Formatting
    # ========================================================================

    def _format_violation_message(
        self,
        project: Project,
        violations: list,
        compliance_score: int,
    ) -> str:
        """Format violation alert message."""
        critical_count = len([v for v in violations if v.severity == "critical"])
        high_count = len([v for v in violations if v.severity == "high"])

        message = (
            f"Compliance scan detected {len(violations)} violation(s) in project *{project.name}*.\n\n"
            f"**Compliance Score:** {compliance_score}%\n"
            f"**Critical Violations:** {critical_count}\n"
            f"**High Violations:** {high_count}\n\n"
        )

        # Add top 3 violations
        if violations:
            message += "**Top Violations:**\n"
            for i, v in enumerate(violations[:3], 1):
                severity_emoji = "🔴" if v.severity == "critical" else "🟠" if v.severity == "high" else "🟡"
                message += f"{i}. {severity_emoji} [{v.severity.upper()}] {v.description}\n"

        return message

    def _format_scan_completed_message(
        self,
        project: Project,
        compliance_score: int,
        violations_count: int,
    ) -> str:
        """Format scan completed message."""
        status_emoji = "✅" if compliance_score >= 80 else "⚠️" if compliance_score >= 50 else "❌"

        return (
            f"Compliance scan for project *{project.name}* has completed.\n\n"
            f"{status_emoji} **Compliance Score:** {compliance_score}%\n"
            f"**Violations Found:** {violations_count}\n\n"
            f"View full report in SDLC Orchestrator."
        )


# ============================================================================
# Global Instance
# ============================================================================


def create_notification_service(
    db: Optional[AsyncSession] = None,
) -> NotificationService:
    """
    Factory function to create NotificationService instance.

    Args:
        db: Optional database session

    Returns:
        Configured NotificationService instance
    """
    return NotificationService(db=db)
