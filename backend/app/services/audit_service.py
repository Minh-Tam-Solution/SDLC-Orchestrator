# File: backend/app/services/audit_service.py
# Version: 1.0.0
# Status: ACTIVE - STAGE 03 (BUILD)
# Date: December 2, 2025
# Authority: CTO Approved
# Foundation: Sprint 23 Security Hardening, SDLC 4.9.1 Compliance
#
# Description:
# Centralized audit logging service for tracking all security-sensitive
# operations. Provides comprehensive audit trail for compliance (SOC 2,
# HIPAA) and security monitoring.
#
# Actions Tracked:
# - Authentication: Login, logout, token refresh, MFA events
# - Authorization: Permission changes, role assignments
# - Data Access: Gate views, evidence downloads
# - Modifications: Create, update, delete operations
# - Admin Actions: User management, policy changes

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


class AuditAction(str, Enum):
    """Enumeration of all auditable actions."""

    # Authentication Events
    USER_LOGIN = "USER_LOGIN"
    USER_LOGIN_FAILED = "USER_LOGIN_FAILED"
    USER_LOGOUT = "USER_LOGOUT"
    TOKEN_REFRESH = "TOKEN_REFRESH"
    MFA_ENABLED = "MFA_ENABLED"
    MFA_DISABLED = "MFA_DISABLED"
    MFA_VERIFIED = "MFA_VERIFIED"
    MFA_FAILED = "MFA_FAILED"
    PASSWORD_CHANGED = "PASSWORD_CHANGED"
    PASSWORD_RESET_REQUESTED = "PASSWORD_RESET_REQUESTED"
    PASSWORD_RESET_COMPLETED = "PASSWORD_RESET_COMPLETED"

    # OAuth Events
    OAUTH_CONNECTED = "OAUTH_CONNECTED"
    OAUTH_DISCONNECTED = "OAUTH_DISCONNECTED"
    OAUTH_TOKEN_REFRESHED = "OAUTH_TOKEN_REFRESHED"

    # User Management (Admin)
    USER_CREATED = "USER_CREATED"
    USER_UPDATED = "USER_UPDATED"
    USER_DELETED = "USER_DELETED"
    USER_ACTIVATED = "USER_ACTIVATED"
    USER_DEACTIVATED = "USER_DEACTIVATED"
    ROLE_ASSIGNED = "ROLE_ASSIGNED"
    ROLE_REVOKED = "ROLE_REVOKED"
    PERMISSION_CHANGED = "PERMISSION_CHANGED"

    # Admin Panel Events (Sprint 37 - ADR-017)
    USER_SUPERUSER_GRANTED = "USER_SUPERUSER_GRANTED"
    USER_SUPERUSER_REVOKED = "USER_SUPERUSER_REVOKED"
    ADMIN_LOGIN = "ADMIN_LOGIN"
    ADMIN_LOGIN_FAILED = "ADMIN_LOGIN_FAILED"
    SETTING_UPDATED = "SETTING_UPDATED"
    SETTING_ROLLBACK = "SETTING_ROLLBACK"
    ADMIN_BULK_ACTION = "ADMIN_BULK_ACTION"

    # Project Events
    PROJECT_CREATED = "PROJECT_CREATED"
    PROJECT_UPDATED = "PROJECT_UPDATED"
    PROJECT_DELETED = "PROJECT_DELETED"
    PROJECT_MEMBER_ADDED = "PROJECT_MEMBER_ADDED"
    PROJECT_MEMBER_REMOVED = "PROJECT_MEMBER_REMOVED"

    # Gate Events
    GATE_CREATED = "GATE_CREATED"
    GATE_UPDATED = "GATE_UPDATED"
    GATE_DELETED = "GATE_DELETED"
    GATE_SUBMITTED = "GATE_SUBMITTED"
    GATE_APPROVED = "GATE_APPROVED"
    GATE_REJECTED = "GATE_REJECTED"
    GATE_VIEWED = "GATE_VIEWED"

    # Evidence Events
    EVIDENCE_UPLOADED = "EVIDENCE_UPLOADED"
    EVIDENCE_DOWNLOADED = "EVIDENCE_DOWNLOADED"
    EVIDENCE_DELETED = "EVIDENCE_DELETED"
    EVIDENCE_INTEGRITY_CHECK = "EVIDENCE_INTEGRITY_CHECK"

    # Policy Events
    POLICY_CREATED = "POLICY_CREATED"
    POLICY_UPDATED = "POLICY_UPDATED"
    POLICY_DELETED = "POLICY_DELETED"
    POLICY_EVALUATED = "POLICY_EVALUATED"
    POLICY_PACK_APPLIED = "POLICY_PACK_APPLIED"

    # Compliance Events
    COMPLIANCE_SCAN_STARTED = "COMPLIANCE_SCAN_STARTED"
    COMPLIANCE_SCAN_COMPLETED = "COMPLIANCE_SCAN_COMPLETED"
    VIOLATION_CREATED = "VIOLATION_CREATED"
    VIOLATION_RESOLVED = "VIOLATION_RESOLVED"

    # AI Events
    AI_RECOMMENDATION_REQUESTED = "AI_RECOMMENDATION_REQUESTED"
    AI_RECOMMENDATION_APPLIED = "AI_RECOMMENDATION_APPLIED"

    # AI Council Events (Sprint 26)
    AI_COUNCIL_REQUESTED = "AI_COUNCIL_REQUESTED"
    AI_COUNCIL_STAGE1_COMPLETE = "AI_COUNCIL_STAGE1_COMPLETE"
    AI_COUNCIL_STAGE2_COMPLETE = "AI_COUNCIL_STAGE2_COMPLETE"
    AI_COUNCIL_STAGE3_COMPLETE = "AI_COUNCIL_STAGE3_COMPLETE"
    AI_COUNCIL_COMPLETE = "AI_COUNCIL_COMPLETE"
    AI_COUNCIL_FALLBACK = "AI_COUNCIL_FALLBACK"
    AI_COUNCIL_FAILED = "AI_COUNCIL_FAILED"

    # System Events
    SYSTEM_STARTUP = "SYSTEM_STARTUP"
    SYSTEM_SHUTDOWN = "SYSTEM_SHUTDOWN"
    CONFIG_CHANGED = "CONFIG_CHANGED"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    SECURITY_ALERT = "SECURITY_ALERT"

    # API Key Events
    API_KEY_CREATED = "API_KEY_CREATED"
    API_KEY_REVOKED = "API_KEY_REVOKED"
    API_KEY_USED = "API_KEY_USED"


class AuditService:
    """
    Centralized audit logging service.

    Provides methods for logging all security-sensitive operations
    with consistent format and metadata capture.

    Usage:
        audit_service = AuditService(db)
        await audit_service.log(
            action=AuditAction.USER_LOGIN,
            user_id=user.id,
            resource_type="user",
            resource_id=user.id,
            details={"login_method": "password"},
            request=request
        )
    """

    def __init__(self, db: AsyncSession):
        """Initialize audit service with async database session."""
        self.db = db

    async def log(
        self,
        action: AuditAction,
        user_id: UUID | None = None,
        resource_type: str | None = None,
        resource_id: UUID | None = None,
        target_name: str | None = None,
        details: dict[str, Any] | None = None,
        request: Request | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AuditLog:
        """
        Log an auditable action.

        Args:
            action: The action being logged (AuditAction enum)
            user_id: UUID of the user performing the action (None for system events)
            resource_type: Type of resource affected ('user', 'gate', 'evidence', etc.)
            resource_id: UUID of the affected resource
            target_name: Human-readable name of the target (e.g., user email, setting key)
            details: Additional context as JSON-serializable dict
            request: FastAPI Request object (for extracting IP/user agent)
            ip_address: Client IP address (if not using request)
            user_agent: Client user agent (if not using request)

        Returns:
            AuditLog: The created audit log entry

        Example:
            audit_service.log(
                action=AuditAction.GATE_APPROVED,
                user_id=approver.id,
                resource_type="gate",
                resource_id=gate.id,
                details={
                    "gate_name": "G1 Design Ready",
                    "approver_role": "CTO",
                    "previous_status": "pending"
                },
                request=request
            )
        """
        # Extract client info from request if provided
        if request:
            ip_address = ip_address or self._get_client_ip(request)
            user_agent = user_agent or request.headers.get("user-agent", "")[:512]

        # Map legacy action to Sprint 185 event_type
        action_str = action.value if isinstance(action, AuditAction) else action
        event_type = self._action_to_event_type(action_str)

        # Include target_name in detail payload if provided
        detail_payload = dict(details) if details else {}
        if target_name:
            detail_payload["target_name"] = target_name

        # Create audit log entry using Sprint 185 schema
        audit_log = AuditLog.create_event(
            event_type=event_type,
            action=action_str,
            actor_id=str(user_id) if user_id else None,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id else None,
            detail=detail_payload or None,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        self.db.add(audit_log)
        await self.db.commit()
        await self.db.refresh(audit_log)

        return audit_log

    @staticmethod
    def _action_to_event_type(action: str) -> str:
        """Map legacy AuditAction string to Sprint 185 event_type."""
        action_upper = action.upper()
        if action_upper.startswith(("USER_", "ADMIN_", "ROLE_", "PERMISSION_")):
            return "user_admin"
        if action_upper.startswith("GATE_"):
            return "gate_action"
        if action_upper.startswith("EVIDENCE_"):
            return "evidence_access"
        if action_upper.startswith(("POLICY_", "COMPLIANCE_", "VIOLATION_")):
            return "gate_action"
        if action_upper.startswith("AI_"):
            return "system_event"
        if action_upper.startswith(("API_KEY_",)):
            return "api_key_event"
        if action_upper.startswith(("SYSTEM_", "CONFIG_", "RATE_LIMIT_", "SECURITY_")):
            return "system_event"
        if action_upper.startswith("OAUTH_"):
            return "sso_event"
        if action_upper.startswith("PASSWORD_") or action_upper.startswith("MFA_"):
            return "user_admin"
        if action_upper.startswith("TOKEN_"):
            return "user_admin"
        return "system_event"

    async def log_login(
        self,
        user_id: UUID,
        success: bool,
        request: Request,
        login_method: str = "password",
        failure_reason: str | None = None,
    ) -> AuditLog:
        """Log a login attempt."""
        action = AuditAction.USER_LOGIN if success else AuditAction.USER_LOGIN_FAILED
        details = {"login_method": login_method}
        if failure_reason:
            details["failure_reason"] = failure_reason

        return await self.log(
            action=action,
            user_id=user_id if success else None,
            resource_type="user",
            resource_id=user_id,
            details=details,
            request=request,
        )

    async def log_logout(self, user_id: UUID, request: Request) -> AuditLog:
        """Log a user logout."""
        return await self.log(
            action=AuditAction.USER_LOGOUT,
            user_id=user_id,
            resource_type="user",
            resource_id=user_id,
            request=request,
        )

    async def log_gate_action(
        self,
        action: AuditAction,
        user_id: UUID,
        gate_id: UUID,
        gate_name: str,
        request: Request,
        details: dict[str, Any] | None = None,
    ) -> AuditLog:
        """Log a gate-related action."""
        log_details = {"gate_name": gate_name}
        if details:
            log_details.update(details)

        return await self.log(
            action=action,
            user_id=user_id,
            resource_type="gate",
            resource_id=gate_id,
            details=log_details,
            request=request,
        )

    async def log_evidence_action(
        self,
        action: AuditAction,
        user_id: UUID,
        evidence_id: UUID,
        filename: str,
        request: Request,
        details: dict[str, Any] | None = None,
    ) -> AuditLog:
        """Log an evidence-related action."""
        log_details = {"filename": filename}
        if details:
            log_details.update(details)

        return await self.log(
            action=action,
            user_id=user_id,
            resource_type="evidence",
            resource_id=evidence_id,
            details=log_details,
            request=request,
        )

    async def log_admin_action(
        self,
        action: AuditAction,
        admin_user_id: UUID,
        target_user_id: UUID,
        request: Request,
        details: dict[str, Any] | None = None,
    ) -> AuditLog:
        """Log an administrative action on a user."""
        return await self.log(
            action=action,
            user_id=admin_user_id,
            resource_type="user",
            resource_id=target_user_id,
            details=details,
            request=request,
        )

    async def log_security_alert(
        self,
        alert_type: str,
        severity: str,
        request: Request | None = None,
        user_id: UUID | None = None,
        details: dict[str, Any] | None = None,
    ) -> AuditLog:
        """Log a security alert."""
        log_details = {"alert_type": alert_type, "severity": severity}
        if details:
            log_details.update(details)

        return await self.log(
            action=AuditAction.SECURITY_ALERT,
            user_id=user_id,
            details=log_details,
            request=request,
        )

    async def log_rate_limit(
        self,
        endpoint: str,
        request: Request,
        user_id: UUID | None = None,
    ) -> AuditLog:
        """Log a rate limit exceeded event."""
        return await self.log(
            action=AuditAction.RATE_LIMIT_EXCEEDED,
            user_id=user_id,
            details={
                "endpoint": endpoint,
                "limit_type": "user" if user_id else "ip",
            },
            request=request,
        )

    async def log_ai_council_action(
        self,
        action: AuditAction,
        user_id: UUID | None,
        violation_id: UUID,
        request: Request | None = None,
        details: dict[str, Any] | None = None,
    ) -> AuditLog:
        """
        Log an AI Council action.

        Args:
            action: AI Council action (AI_COUNCIL_*)
            user_id: User who triggered the council
            violation_id: Violation being analyzed
            request: FastAPI request (optional)
            details: Additional context (providers, duration, etc.)

        Example:
            await audit_service.log_ai_council_action(
                action=AuditAction.AI_COUNCIL_COMPLETE,
                user_id=user.id,
                violation_id=violation.id,
                details={
                    "mode": "council",
                    "providers_used": ["ollama", "claude", "gpt4"],
                    "confidence": 95,
                    "duration_ms": 5200,
                    "cost_usd": 0.05
                }
            )
        """
        log_details = {"violation_id": str(violation_id)}
        if details:
            log_details.update(details)

        return await self.log(
            action=action,
            user_id=user_id,
            resource_type="ai_council",
            resource_id=violation_id,
            details=log_details,
            request=request,
        )

    # =====================================================
    # Admin Panel Methods (Sprint 37 - ADR-017)
    # =====================================================

    async def log_user_activation(
        self,
        admin_user_id: UUID,
        target_user_id: UUID,
        target_email: str,
        is_activating: bool,
        request: Request,
        details: dict[str, Any] | None = None,
    ) -> AuditLog:
        """
        Log user activation or deactivation by admin.

        Args:
            admin_user_id: UUID of admin performing the action
            target_user_id: UUID of user being activated/deactivated
            target_email: Email of the target user (for display)
            is_activating: True if activating, False if deactivating
            request: FastAPI request
            details: Additional context

        Example:
            await audit_service.log_user_activation(
                admin_user_id=admin.id,
                target_user_id=user.id,
                target_email=user.email,
                is_activating=False,
                request=request,
                details={"reason": "Policy violation"}
            )
        """
        action = AuditAction.USER_ACTIVATED if is_activating else AuditAction.USER_DEACTIVATED
        log_details = {"previous_status": "inactive" if is_activating else "active"}
        if details:
            log_details.update(details)

        return await self.log(
            action=action,
            user_id=admin_user_id,
            resource_type="user",
            resource_id=target_user_id,
            target_name=target_email,
            details=log_details,
            request=request,
        )

    async def log_superuser_change(
        self,
        admin_user_id: UUID,
        target_user_id: UUID,
        target_email: str,
        is_granting: bool,
        request: Request,
        details: dict[str, Any] | None = None,
    ) -> AuditLog:
        """
        Log superuser status grant or revocation.

        Args:
            admin_user_id: UUID of admin performing the action
            target_user_id: UUID of user being granted/revoked superuser
            target_email: Email of the target user
            is_granting: True if granting, False if revoking
            request: FastAPI request
            details: Additional context
        """
        action = AuditAction.USER_SUPERUSER_GRANTED if is_granting else AuditAction.USER_SUPERUSER_REVOKED
        log_details = {"previous_superuser_status": not is_granting}
        if details:
            log_details.update(details)

        return await self.log(
            action=action,
            user_id=admin_user_id,
            resource_type="user",
            resource_id=target_user_id,
            target_name=target_email,
            details=log_details,
            request=request,
        )

    async def log_setting_change(
        self,
        admin_user_id: UUID,
        setting_key: str,
        old_value: Any,
        new_value: Any,
        request: Request,
        details: dict[str, Any] | None = None,
    ) -> AuditLog:
        """
        Log system setting change.

        Args:
            admin_user_id: UUID of admin changing the setting
            setting_key: Key of the setting being changed
            old_value: Previous setting value
            new_value: New setting value
            request: FastAPI request
            details: Additional context
        """
        log_details = {
            "old_value": old_value,
            "new_value": new_value,
        }
        if details:
            log_details.update(details)

        return await self.log(
            action=AuditAction.SETTING_UPDATED,
            user_id=admin_user_id,
            resource_type="setting",
            resource_id=None,
            target_name=setting_key,
            details=log_details,
            request=request,
        )

    async def log_setting_rollback(
        self,
        admin_user_id: UUID,
        setting_key: str,
        from_version: int,
        to_version: int,
        request: Request,
        details: dict[str, Any] | None = None,
    ) -> AuditLog:
        """
        Log system setting rollback.

        Args:
            admin_user_id: UUID of admin performing rollback
            setting_key: Key of the setting being rolled back
            from_version: Version rolling back from
            to_version: Version rolling back to
            request: FastAPI request
            details: Additional context
        """
        log_details = {
            "from_version": from_version,
            "to_version": to_version,
        }
        if details:
            log_details.update(details)

        return await self.log(
            action=AuditAction.SETTING_ROLLBACK,
            user_id=admin_user_id,
            resource_type="setting",
            resource_id=None,
            target_name=setting_key,
            details=log_details,
            request=request,
        )

    def _get_client_ip(self, request: Request) -> str | None:
        """Extract client IP from request, handling proxies."""
        # Check X-Forwarded-For header (for load balancers/proxies)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            # Get the first IP in the chain (original client)
            return forwarded_for.split(",")[0].strip()

        # Check X-Real-IP header
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip

        # Fall back to direct client IP
        if request.client:
            return request.client.host

        return None


def get_audit_service(db: AsyncSession) -> AuditService:
    """Factory function to get an AuditService instance."""
    return AuditService(db)
