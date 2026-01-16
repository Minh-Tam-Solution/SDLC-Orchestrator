"""
=========================================================================
Admin Panel Schemas - Request/Response Models
SDLC Orchestrator - Stage 03 (BUILD)

Version: 1.0.0
Date: December 16, 2025
Status: ACTIVE - Sprint 37 Admin Panel
Authority: CTO Approved (Dec 16, 2025)
Foundation: ADR-017 Admin Panel Architecture
Framework: SDLC 5.1.1 Complete Lifecycle

Purpose:
- Admin user management schemas
- System settings schemas
- Audit log schemas
- System health schemas
- Dashboard statistics schemas

Security:
- All endpoints require is_superuser=true
- Audit logging for all admin actions

Zero Mock Policy: Production-ready Pydantic models
=========================================================================
"""

from datetime import datetime
from typing import Any, List, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


# =========================================================================
# Dashboard Statistics Schemas
# =========================================================================


class AdminDashboardStats(BaseModel):
    """
    Admin dashboard statistics.

    Response Body:
        {
            "total_users": 150,
            "active_users": 142,
            "inactive_users": 8,
            "superusers": 3,
            "total_projects": 45,
            "total_gates": 180,
            "active_projects": 38,
            "system_status": "healthy"
        }
    """

    total_users: int = Field(..., ge=0, description="Total registered users")
    active_users: int = Field(..., ge=0, description="Active users (is_active=true)")
    inactive_users: int = Field(..., ge=0, description="Inactive users")
    superusers: int = Field(..., ge=0, description="Total superusers")
    total_projects: int = Field(..., ge=0, description="Total projects")
    total_gates: int = Field(..., ge=0, description="Total gates")
    active_projects: int = Field(..., ge=0, description="Active projects")
    system_status: str = Field(..., description="Overall system status (healthy, degraded, unhealthy)")


# =========================================================================
# User Management Schemas
# =========================================================================


class AdminUserListItem(BaseModel):
    """
    User item in admin user list.

    Response Body:
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "email": "nguyen.van.anh@mtc.com.vn",
            "name": "Nguyễn Văn Anh",
            "is_active": true,
            "is_superuser": false,
            "created_at": "2025-10-01T08:00:00Z",
            "last_login": "2025-12-15T10:30:00Z"
        }
    """

    id: UUID = Field(..., description="User UUID")
    email: EmailStr = Field(..., description="User email")
    name: Optional[str] = Field(None, description="User full name")
    is_active: bool = Field(..., description="Active status")
    is_superuser: bool = Field(..., description="Superuser status")
    created_at: datetime = Field(..., description="Account creation timestamp")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")

    class Config:
        from_attributes = True


class AdminUserDetail(BaseModel):
    """
    Detailed user information for admin view.

    Response Body:
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "email": "nguyen.van.anh@mtc.com.vn",
            "name": "Nguyễn Văn Anh",
            "avatar_url": "https://avatars.githubusercontent.com/...",
            "is_active": true,
            "is_superuser": false,
            "mfa_enabled": true,
            "oauth_providers": ["github", "google"],
            "project_count": 5,
            "created_at": "2025-10-01T08:00:00Z",
            "updated_at": "2025-12-01T09:00:00Z",
            "last_login": "2025-12-15T10:30:00Z"
        }
    """

    id: UUID = Field(..., description="User UUID")
    email: EmailStr = Field(..., description="User email")
    name: Optional[str] = Field(None, description="User full name")
    avatar_url: Optional[str] = Field(None, description="Avatar URL")
    is_active: bool = Field(..., description="Active status")
    is_superuser: bool = Field(..., description="Superuser status")
    mfa_enabled: bool = Field(..., description="MFA enabled status")
    oauth_providers: List[str] = Field(default_factory=list, description="Linked OAuth providers")
    project_count: int = Field(default=0, ge=0, description="Number of owned projects")
    created_at: datetime = Field(..., description="Account creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")

    class Config:
        from_attributes = True


class AdminUserCreate(BaseModel):
    """
    Admin user creation request (Sprint 40).

    Request Body:
        {
            "email": "newuser@example.com",
            "password": "SecurePassword123!",
            "name": "New User",
            "is_active": true,
            "is_superuser": false
        }

    Security:
        - Password minimum 12 characters (enforced at schema level)
        - Email must be unique (validated at endpoint)
        - All fields are validated before database insertion
        - Action is audit logged

    CTO Approved: Dec 17, 2025
    """

    email: EmailStr = Field(..., description="User email (must be unique)")
    password: str = Field(..., min_length=12, description="Password (min 12 characters)")
    name: Optional[str] = Field(None, max_length=255, description="User full name")
    is_active: bool = Field(default=True, description="Active status (default: true)")
    is_superuser: bool = Field(default=False, description="Superuser status (default: false)")


class AdminUserUpdate(BaseModel):
    """
    Admin user update request.

    Request Body:
        {
            "name": "Updated Name",
            "is_active": true,
            "is_superuser": false
        }

    Security:
        - Admin cannot modify own account (is_active, is_superuser)
        - System must have at least one superuser
    """

    name: Optional[str] = Field(None, max_length=255, description="User full name")
    is_active: Optional[bool] = Field(None, description="Active status")
    is_superuser: Optional[bool] = Field(None, description="Superuser status")


class AdminUserUpdateFull(BaseModel):
    """
    Admin user full update request (Sprint 40).

    Request Body:
        {
            "email": "updated@example.com",
            "name": "Updated Name",
            "is_active": true,
            "is_superuser": false,
            "new_password": "NewSecurePassword123!"
        }

    Security:
        - Email change triggers warning (user must use new email to login)
        - Password reset min 12 characters (optional)
        - Email uniqueness validated at endpoint
        - All changes audit logged
        - Admin cannot demote self from superuser

    CTO Approved: Dec 17, 2025
    """

    email: Optional[EmailStr] = Field(None, description="User email (must be unique)")
    name: Optional[str] = Field(None, max_length=255, description="User full name")
    is_active: Optional[bool] = Field(None, description="Active status")
    is_superuser: Optional[bool] = Field(None, description="Superuser status")
    new_password: Optional[str] = Field(None, min_length=12, description="New password (min 12 chars, optional)")


class AdminUserListResponse(BaseModel):
    """
    Paginated user list response.

    Response Body:
        {
            "items": [...],
            "total": 150,
            "page": 1,
            "page_size": 20,
            "pages": 8
        }
    """

    items: List[AdminUserListItem] = Field(..., description="List of users")
    total: int = Field(..., ge=0, description="Total users matching filter")
    page: int = Field(..., ge=1, description="Current page number")
    page_size: int = Field(..., ge=1, le=100, description="Items per page")
    pages: int = Field(..., ge=0, description="Total number of pages")


# =========================================================================
# Audit Log Schemas
# =========================================================================


class AuditLogItem(BaseModel):
    """
    Audit log entry.

    Response Body:
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "timestamp": "2025-12-16T10:30:00Z",
            "action": "USER_DEACTIVATED",
            "actor_id": "660e8400-e29b-41d4-a716-446655440001",
            "actor_email": "admin@sdlc-orchestrator.io",
            "target_type": "user",
            "target_id": "770e8400-e29b-41d4-a716-446655440002",
            "target_name": "john.doe@example.com",
            "details": {"previous_status": "active"},
            "ip_address": "192.168.1.100"
        }
    """

    id: UUID = Field(..., description="Audit log UUID")
    timestamp: datetime = Field(..., description="Action timestamp")
    action: str = Field(..., description="Action type (e.g., USER_DEACTIVATED)")
    actor_id: Optional[UUID] = Field(None, description="User UUID who performed action")
    actor_email: Optional[str] = Field(None, description="Actor's email (for display)")
    target_type: Optional[str] = Field(None, description="Target resource type")
    target_id: Optional[UUID] = Field(None, description="Target resource UUID")
    target_name: Optional[str] = Field(None, description="Target name (for display)")
    details: dict = Field(default_factory=dict, description="Additional details")
    ip_address: Optional[str] = Field(None, description="Client IP address")

    class Config:
        from_attributes = True


class AuditLogListResponse(BaseModel):
    """
    Paginated audit log response.

    Response Body:
        {
            "items": [...],
            "total": 5000,
            "page": 1,
            "page_size": 50,
            "pages": 100
        }
    """

    items: List[AuditLogItem] = Field(..., description="List of audit logs")
    total: int = Field(..., ge=0, description="Total logs matching filter")
    page: int = Field(..., ge=1, description="Current page number")
    page_size: int = Field(..., ge=1, le=100, description="Items per page")
    pages: int = Field(..., ge=0, description="Total number of pages")


class AuditLogFilter(BaseModel):
    """
    Audit log filter parameters.

    Query Parameters:
        ?action=USER_DEACTIVATED&actor_id=...&date_from=...&date_to=...
    """

    action: Optional[str] = Field(None, description="Filter by action type")
    actor_id: Optional[UUID] = Field(None, description="Filter by actor UUID")
    target_type: Optional[str] = Field(None, description="Filter by target type")
    target_id: Optional[UUID] = Field(None, description="Filter by target UUID")
    date_from: Optional[datetime] = Field(None, description="Start date filter")
    date_to: Optional[datetime] = Field(None, description="End date filter")
    search: Optional[str] = Field(None, max_length=100, description="Search in actor email or target name")


# =========================================================================
# System Settings Schemas
# =========================================================================


class SystemSettingItem(BaseModel):
    """
    System setting item.

    Response Body:
        {
            "key": "session_timeout_minutes",
            "value": 30,
            "version": 2,
            "category": "security",
            "description": "Session timeout in minutes",
            "updated_at": "2025-12-16T10:30:00Z",
            "updated_by": "admin@sdlc-orchestrator.io"
        }
    """

    key: str = Field(..., description="Setting key")
    value: Any = Field(..., description="Setting value (JSON)")
    version: int = Field(..., ge=1, description="Version number")
    category: str = Field(..., description="Setting category")
    description: Optional[str] = Field(None, description="Human-readable description")
    updated_at: datetime = Field(..., description="Last update timestamp")
    updated_by: Optional[str] = Field(None, description="Email of last updater")

    class Config:
        from_attributes = True


class SystemSettingUpdate(BaseModel):
    """
    System setting update request.

    Request Body:
        {
            "value": 60
        }

    Notes:
        - Previous value is stored for rollback capability
        - Version is automatically incremented
        - Change is audit logged
    """

    value: Any = Field(..., description="New setting value")


class SystemSettingRollback(BaseModel):
    """
    System setting rollback request.

    Request Body:
        {
            "target_version": 1
        }

    Notes:
        - Can only rollback to previous version
        - Rollback is audit logged
    """

    target_version: int = Field(..., ge=1, description="Version to rollback to")


class SystemSettingsListResponse(BaseModel):
    """
    System settings grouped by category.

    Response Body:
        {
            "security": [...],
            "limits": [...],
            "features": [...],
            "notifications": [...],
            "general": [...],
            "ai": [...]
        }
    """

    security: List[SystemSettingItem] = Field(default_factory=list, description="Security settings")
    limits: List[SystemSettingItem] = Field(default_factory=list, description="Limit settings")
    features: List[SystemSettingItem] = Field(default_factory=list, description="Feature flags")
    notifications: List[SystemSettingItem] = Field(default_factory=list, description="Notification settings")
    general: List[SystemSettingItem] = Field(default_factory=list, description="General settings")
    ai: List[SystemSettingItem] = Field(default_factory=list, description="AI provider settings")


# =========================================================================
# System Health Schemas
# =========================================================================


class ServiceHealthStatus(BaseModel):
    """
    Individual service health status.

    Response Body:
        {
            "name": "PostgreSQL",
            "status": "healthy",
            "response_time_ms": 5,
            "details": {"version": "15.5", "connections": 42}
        }
    """

    name: str = Field(..., description="Service name")
    status: str = Field(..., description="Status (healthy, degraded, unhealthy)")
    response_time_ms: Optional[int] = Field(None, ge=0, description="Response time in ms")
    details: dict = Field(default_factory=dict, description="Additional details")


class SystemMetrics(BaseModel):
    """
    System resource metrics.

    Response Body:
        {
            "cpu_usage_percent": 45.2,
            "memory_usage_percent": 62.8,
            "disk_usage_percent": 35.5,
            "active_connections": 42
        }
    """

    cpu_usage_percent: Optional[float] = Field(None, ge=0, le=100, description="CPU usage percentage")
    memory_usage_percent: Optional[float] = Field(None, ge=0, le=100, description="Memory usage percentage")
    disk_usage_percent: Optional[float] = Field(None, ge=0, le=100, description="Disk usage percentage")
    active_connections: Optional[int] = Field(None, ge=0, description="Active database connections")


class SystemHealthResponse(BaseModel):
    """
    Complete system health response.

    Response Body:
        {
            "overall_status": "healthy",
            "services": [...],
            "metrics": {...},
            "checked_at": "2025-12-16T10:30:00Z"
        }
    """

    overall_status: str = Field(..., description="Overall status (healthy, degraded, unhealthy)")
    services: List[ServiceHealthStatus] = Field(..., description="Individual service statuses")
    metrics: SystemMetrics = Field(..., description="System resource metrics")
    checked_at: datetime = Field(..., description="Health check timestamp")


# =========================================================================
# Bulk Action Schemas
# =========================================================================


class BulkUserActionRequest(BaseModel):
    """
    Bulk user action request.

    Request Body:
        {
            "user_ids": ["uuid1", "uuid2", "uuid3"],
            "action": "deactivate"
        }

    Actions:
        - activate: Set is_active=true
        - deactivate: Set is_active=false

    Security:
        - Cannot include self in bulk actions
        - Rate limited to 10 actions per minute
    """

    user_ids: List[UUID] = Field(..., min_length=1, max_length=50, description="List of user UUIDs")
    action: str = Field(..., pattern="^(activate|deactivate)$", description="Action to perform")


class BulkUserActionResponse(BaseModel):
    """
    Bulk user action response.

    Response Body:
        {
            "success_count": 3,
            "failed_count": 1,
            "failed_users": [
                {"user_id": "...", "reason": "Cannot deactivate self"}
            ]
        }
    """

    success_count: int = Field(..., ge=0, description="Number of successful actions")
    failed_count: int = Field(..., ge=0, description="Number of failed actions")
    failed_users: List[dict] = Field(default_factory=list, description="Failed users with reasons")


# =========================================================================
# Bulk Delete Schemas (Sprint 40 Part 3)
# =========================================================================


class BulkDeleteRequest(BaseModel):
    """
    Bulk delete users request (Sprint 40 Part 3).

    Request Body:
        {
            "user_ids": ["uuid1", "uuid2", "uuid3"]
        }

    Security:
        - Maximum 50 users per request (CTO condition)
        - Cannot include self in bulk delete
        - Cannot delete last superuser
        - Rate limited to 5 requests per minute

    CTO Approved: Dec 18, 2025
    """

    user_ids: List[UUID] = Field(
        ...,
        min_length=1,
        max_length=50,
        description="List of user UUIDs to delete (max 50)"
    )


class DeletedUserInfo(BaseModel):
    """
    Information about a successfully deleted user.

    Response Body:
        {
            "user_id": "550e8400-e29b-41d4-a716-446655440001",
            "email": "user@example.com"
        }
    """

    user_id: UUID = Field(..., description="Deleted user's UUID")
    email: str = Field(..., description="Deleted user's email (for confirmation)")


class FailedUserInfo(BaseModel):
    """
    Information about a user that failed to delete.

    Response Body:
        {
            "user_id": "550e8400-e29b-41d4-a716-446655440003",
            "reason": "User is the last superuser"
        }
    """

    user_id: UUID = Field(..., description="User UUID that failed to delete")
    reason: str = Field(..., description="Reason for failure")


class BulkDeleteResponse(BaseModel):
    """
    Bulk delete users response (Sprint 40 Part 3).

    Response Body (Success):
        {
            "success_count": 3,
            "failed_count": 0,
            "deleted_users": [
                {"user_id": "...", "email": "user1@example.com"},
                {"user_id": "...", "email": "user2@example.com"},
                {"user_id": "...", "email": "user3@example.com"}
            ],
            "failed_users": []
        }

    Response Body (Partial Success):
        {
            "success_count": 2,
            "failed_count": 1,
            "deleted_users": [...],
            "failed_users": [
                {"user_id": "...", "reason": "User is the last superuser"}
            ]
        }

    CTO Conditions Applied:
        1. Batch size limit: max 50 users
        2. Partial success handling: detailed report
        3. Rate limiting: 5 req/min per admin

    CTO Approved: Dec 18, 2025
    """

    success_count: int = Field(..., ge=0, description="Number of successfully deleted users")
    failed_count: int = Field(..., ge=0, description="Number of failed deletions")
    deleted_users: List[DeletedUserInfo] = Field(
        default_factory=list,
        description="List of successfully deleted users with emails"
    )
    failed_users: List[FailedUserInfo] = Field(
        default_factory=list,
        description="List of failed deletions with reasons"
    )
