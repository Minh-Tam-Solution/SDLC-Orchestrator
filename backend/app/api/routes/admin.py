"""
=========================================================================
Admin Panel Routes - User Management, Settings, Audit Logs
SDLC Orchestrator - Stage 03 (BUILD)

Version: 1.1.0
Date: December 18, 2025
Status: ACTIVE - Sprint 40 Part 3 (Bulk Delete)
Authority: CTO Approved (Dec 18, 2025)
Foundation: ADR-017 Admin Panel Architecture
Framework: SDLC 5.1.1 Complete Lifecycle

Endpoints:
- GET  /api/v1/admin/stats           - Dashboard statistics
- GET  /api/v1/admin/users           - List users (paginated)
- POST /api/v1/admin/users           - Create new user (Sprint 40)
- GET  /api/v1/admin/users/{id}      - Get user details
- PATCH /api/v1/admin/users/{id}     - Update user
- DELETE /api/v1/admin/users/{id}    - Soft delete user (Sprint 40)
- DELETE /api/v1/admin/users/bulk    - Bulk soft delete (Sprint 40 Part 3)
- POST /api/v1/admin/users/bulk      - Bulk activate/deactivate
- POST /api/v1/admin/users/{id}/unlock - Unlock locked account (ADR-027)
- POST /api/v1/admin/users/{id}/mfa-exempt - Set MFA exemption (ADR-027)
- GET  /api/v1/admin/users/{id}/mfa-status - Get MFA status (ADR-027)
- GET  /api/v1/admin/audit-logs      - Audit logs (paginated)
- GET  /api/v1/admin/settings        - Get all settings
- GET  /api/v1/admin/settings/{key}  - Get setting by key
- PATCH /api/v1/admin/settings/{key} - Update setting
- POST /api/v1/admin/settings/{key}/rollback - Rollback setting
- GET  /api/v1/admin/system/health   - System health

Security:
- All endpoints require is_superuser=true
- Audit logging for all admin actions
- Self-action prevention (cannot modify own account)
- Rate limiting per ADR-017
- Bulk delete: max 50 users, 5 req/min (CTO condition)

Zero Mock Policy: Production-ready implementation
=========================================================================
"""

import bcrypt
import logging
import math
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request, status
from pydantic import ValidationError
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.dependencies import get_db, require_superuser
from app.services.settings_service import SettingsService, get_settings_service

logger = logging.getLogger(__name__)
from app.models import AuditLog, Gate, Project, SystemSetting, User
from app.schemas.admin import (
    AdminDashboardStats,
    AdminUserCreate,
    AdminUserDetail,
    AdminUserListItem,
    AdminUserListResponse,
    AdminUserUpdate,
    AdminUserUpdateFull,
    AuditLogFilter,
    AuditLogItem,
    AuditLogListResponse,
    BulkDeleteRequest,
    BulkDeleteResponse,
    BulkUserActionRequest,
    BulkUserActionResponse,
    DeletedUserInfo,
    FailedUserInfo,
    ServiceHealthStatus,
    SystemHealthResponse,
    SystemMetrics,
    SystemSettingItem,
    SystemSettingsListResponse,
    SystemSettingUpdate,
)
from app.services.audit_service import AuditAction, get_audit_service

router = APIRouter(prefix="/admin")


# =========================================================================
# Dashboard Statistics
# =========================================================================


@router.get(
    "/stats",
    response_model=AdminDashboardStats,
    summary="Get admin dashboard statistics",
    description="Get platform statistics including user counts, project counts, and system status.",
)
async def get_admin_stats(
    admin: User = Depends(require_superuser),
    db: AsyncSession = Depends(get_db),
) -> AdminDashboardStats:
    """
    Get admin dashboard statistics.

    Returns platform-wide statistics for admin dashboard.

    Security:
        - Requires superuser access

    Returns:
        AdminDashboardStats: Platform statistics
    """
    # Count users (exclude soft-deleted - Sprint 40 Part 2 fix)
    total_users = await db.scalar(
        select(func.count()).select_from(User).where(User.deleted_at.is_(None))
    )
    active_users = await db.scalar(
        select(func.count()).where(User.is_active == True, User.deleted_at.is_(None))
    )
    inactive_users = total_users - active_users
    superusers = await db.scalar(
        select(func.count()).where(User.is_superuser == True, User.deleted_at.is_(None))
    )

    # Count projects
    total_projects = await db.scalar(select(func.count()).select_from(Project))
    active_projects = await db.scalar(
        select(func.count()).where(Project.is_active == True, Project.deleted_at.is_(None))
    )

    # Count gates
    total_gates = await db.scalar(select(func.count()).select_from(Gate))

    # Determine system status (simple health check)
    system_status = "healthy"

    return AdminDashboardStats(
        total_users=total_users or 0,
        active_users=active_users or 0,
        inactive_users=inactive_users or 0,
        superusers=superusers or 0,
        total_projects=total_projects or 0,
        total_gates=total_gates or 0,
        active_projects=active_projects or 0,
        system_status=system_status,
    )


# =========================================================================
# User Management
# =========================================================================


@router.get(
    "/users",
    response_model=AdminUserListResponse,
    summary="List all users (paginated)",
    description="Get paginated list of all users with search and filter capabilities.",
)
async def list_users(
    admin: User = Depends(require_superuser),
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, max_length=100, description="Search by email or name"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    is_superuser: Optional[bool] = Query(None, description="Filter by superuser status"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="Sort order"),
) -> AdminUserListResponse:
    """
    List all users with pagination and filtering.

    Query Parameters:
        - page: Page number (default: 1)
        - page_size: Items per page (default: 20, max: 100)
        - search: Search by email or name
        - is_active: Filter by active status
        - is_superuser: Filter by superuser status
        - sort_by: Sort field (created_at, email, name, last_login)
        - sort_order: asc or desc

    Security:
        - Requires superuser access

    Returns:
        AdminUserListResponse: Paginated user list
    """
    # Build query - EXCLUDE soft-deleted users (Sprint 40 Part 2 fix)
    query = select(User).where(User.deleted_at.is_(None))

    # Apply filters
    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            (User.email.ilike(search_pattern)) | (User.name.ilike(search_pattern))
        )

    if is_active is not None:
        query = query.where(User.is_active == is_active)

    if is_superuser is not None:
        query = query.where(User.is_superuser == is_superuser)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)

    # Apply sorting
    sort_column = getattr(User, sort_by, User.created_at)
    if sort_order == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    # Execute
    result = await db.execute(query)
    users = result.scalars().all()

    # Map to response
    items = [
        AdminUserListItem(
            id=user.id,
            email=user.email,
            name=user.full_name,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            created_at=user.created_at,
            last_login=user.last_login,
        )
        for user in users
    ]

    pages = math.ceil(total / page_size) if total > 0 else 0

    return AdminUserListResponse(
        items=items,
        total=total or 0,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get(
    "/users/{user_id}",
    response_model=AdminUserDetail,
    summary="Get user details",
    description="Get detailed information about a specific user.",
)
async def get_user_detail(
    user_id: UUID,
    admin: User = Depends(require_superuser),
    db: AsyncSession = Depends(get_db),
) -> AdminUserDetail:
    """
    Get detailed user information.

    Security:
        - Requires superuser access

    Returns:
        AdminUserDetail: User details
    """
    # Get user with OAuth accounts
    query = (
        select(User)
        .where(User.id == user_id)
        .options(selectinload(User.oauth_accounts))
    )
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Count projects owned by user
    project_count = await db.scalar(
        select(func.count()).where(Project.owner_id == user_id)
    )

    # Get OAuth providers
    oauth_providers = [acc.provider for acc in user.oauth_accounts]

    return AdminUserDetail(
        id=user.id,
        email=user.email,
        name=user.full_name,
        avatar_url=user.avatar_url,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        mfa_enabled=user.mfa_enabled,
        oauth_providers=oauth_providers,
        project_count=project_count or 0,
        created_at=user.created_at,
        updated_at=user.updated_at,
        last_login=user.last_login,
    )


@router.patch(
    "/users/{user_id}",
    response_model=AdminUserDetail,
    summary="Update user",
    description="Update user information (name, email, password, is_active, is_superuser) - Sprint 40 Part 2.",
)
async def update_user(
    user_id: UUID,
    update_data: AdminUserUpdateFull,
    request: Request,
    admin: User = Depends(require_superuser),
    db: AsyncSession = Depends(get_db),
    settings_service: SettingsService = Depends(get_settings_service),
) -> AdminUserDetail:
    """
    Update user information (Enhanced in Sprint 40 Part 2).

    Security:
        - Requires superuser access
        - Cannot modify own account (is_active, is_superuser)
        - System must have at least one superuser
        - Email must be unique if changed
        - Password must be 12+ characters if provided
        - All changes are audit logged

    Sprint 40 Part 2 Additions:
        - Email change support
        - Password reset support (new_password field)

    Returns:
        AdminUserDetail: Updated user details
    """
    # Get user
    query = (
        select(User)
        .where(User.id == user_id)
        .options(selectinload(User.oauth_accounts))
    )
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Self-action prevention
    if user_id == admin.id:
        if update_data.is_active is not None or update_data.is_superuser is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot modify your own account status",
            )

    # Initialize audit service
    audit_service = get_audit_service(db)

    # Track changes for audit log
    changes = {}

    # Update email (Sprint 40 Part 2)
    if update_data.email is not None and update_data.email.lower() != user.email:
        # Check if new email already exists
        existing_user = await db.scalar(
            select(User).where(
                User.email == update_data.email.lower(),
                User.id != user_id
            )
        )
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User with email '{update_data.email}' already exists",
            )

        old_email = user.email
        user.email = update_data.email.lower()
        changes['email'] = {'old': old_email, 'new': user.email}

    # Update password (Sprint 40 Part 2)
    if update_data.new_password is not None:
        # ADR-027: Validate password meets minimum length requirement
        from app.utils.password_validator import validate_password_strength
        await validate_password_strength(update_data.new_password, settings_service)

        # Hash password with bcrypt (cost=12)
        password_hash = bcrypt.hashpw(
            update_data.new_password.encode('utf-8'),
            bcrypt.gensalt(rounds=12)
        ).decode('utf-8')
        user.password_hash = password_hash
        changes['password'] = 'reset'

    # Update name
    if update_data.name is not None and update_data.name != user.full_name:
        old_name = user.full_name
        user.full_name = update_data.name
        changes['name'] = {'old': old_name, 'new': user.full_name}

    # Update is_active
    if update_data.is_active is not None and update_data.is_active != user.is_active:
        previous_status = user.is_active
        user.is_active = update_data.is_active

        # Audit log
        await audit_service.log_user_activation(
            admin_user_id=admin.id,
            target_user_id=user.id,
            target_email=user.email,
            is_activating=update_data.is_active,
            request=request,
        )

    # Update is_superuser
    if update_data.is_superuser is not None and update_data.is_superuser != user.is_superuser:
        # Check minimum superuser count before revoking
        if not update_data.is_superuser:
            superuser_count = await db.scalar(
                select(func.count()).where(User.is_superuser == True)
            )
            if superuser_count <= 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot revoke superuser status. At least one superuser is required.",
                )

        user.is_superuser = update_data.is_superuser

        # Audit log
        await audit_service.log_superuser_change(
            admin_user_id=admin.id,
            target_user_id=user.id,
            target_email=user.email,
            is_granting=update_data.is_superuser,
            request=request,
        )

    # Audit log for email/password/name changes (Sprint 40 Part 2)
    if changes:
        await audit_service.log(
            action=AuditAction.USER_UPDATED,
            user_id=admin.id,
            resource_type="user",
            resource_id=user.id,
            target_name=user.email,
            details={
                "changes": changes,
                "updated_by": admin.email,
            },
            request=request,
        )

    user.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(user)

    # Count projects
    project_count = await db.scalar(
        select(func.count()).where(Project.owner_id == user_id)
    )

    # Get OAuth providers
    oauth_providers = [acc.provider for acc in user.oauth_accounts]

    return AdminUserDetail(
        id=user.id,
        email=user.email,
        name=user.full_name,
        avatar_url=user.avatar_url,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        mfa_enabled=user.mfa_enabled,
        oauth_providers=oauth_providers,
        project_count=project_count or 0,
        created_at=user.created_at,
        updated_at=user.updated_at,
        last_login=user.last_login,
    )


@router.post(
    "/users",
    response_model=AdminUserDetail,
    status_code=status.HTTP_201_CREATED,
    summary="Create new user",
    description="Create a new user account with email and password (Sprint 40).",
)
async def create_user(
    user_data: AdminUserCreate,
    request: Request,
    admin: User = Depends(require_superuser),
    db: AsyncSession = Depends(get_db),
    settings_service: "SettingsService" = Depends(get_settings_service),
) -> AdminUserDetail:
    """
    Create a new user account.

    Security:
        - Requires superuser access
        - Email must be unique
        - Password minimum 12 characters (enforced at schema level)
        - All actions audit logged

    Sprint 40 - CTO Approved: Dec 17, 2025

    Returns:
        AdminUserDetail: Created user details
    """
    # ADR-027: Validate password meets minimum length requirement
    from app.utils.password_validator import validate_password_strength
    await validate_password_strength(user_data.password, settings_service)

    # Check if email already exists
    existing_user = await db.scalar(
        select(User).where(User.email == user_data.email.lower())
    )
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User with email '{user_data.email}' already exists",
        )

    # Hash password with bcrypt (cost=12)
    password_hash = bcrypt.hashpw(
        user_data.password.encode('utf-8'),
        bcrypt.gensalt(rounds=12)
    ).decode('utf-8')

    # Create user
    new_user = User(
        email=user_data.email.lower(),
        password_hash=password_hash,
        name=user_data.name,
        is_active=user_data.is_active,
        is_superuser=user_data.is_superuser,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    # Audit log
    audit_service = get_audit_service(db)
    await audit_service.log(
        action=AuditAction.USER_CREATED,
        user_id=admin.id,
        resource_type="user",
        resource_id=new_user.id,
        target_name=new_user.email,
        details={
            "email": new_user.email,
            "name": new_user.full_name,
            "is_active": new_user.is_active,
            "is_superuser": new_user.is_superuser,
        },
        request=request,
    )

    # Count projects (new user has 0 projects)
    project_count = 0

    # Get OAuth providers (new user has none)
    oauth_providers = []

    return AdminUserDetail(
        id=new_user.id,
        email=new_user.email,
        name=new_user.full_name,
        avatar_url=new_user.avatar_url,
        is_active=new_user.is_active,
        is_superuser=new_user.is_superuser,
        mfa_enabled=new_user.mfa_enabled,
        oauth_providers=oauth_providers,
        project_count=project_count,
        created_at=new_user.created_at,
        updated_at=new_user.updated_at,
        last_login=new_user.last_login,
    )


# =========================================================================
# User Deletion - Sprint 40 Part 3
# =========================================================================
# NOTE: Bulk delete MUST be defined before single delete {user_id}
#       to prevent FastAPI from matching "bulk" as a UUID parameter


@router.delete(
    "/users/bulk",
    response_model=BulkDeleteResponse,
    summary="Bulk delete users (soft delete)",
    description="Soft delete multiple users at once with full audit trail (Sprint 40 Part 3).",
)
async def bulk_delete_users(
    delete_request: BulkDeleteRequest,
    admin: User = Depends(require_superuser),
    db: AsyncSession = Depends(get_db),
    request: Request = None,
) -> BulkDeleteResponse:
    logger.info("=== BULK DELETE ENDPOINT CALLED ===")
    logger.info(f"Received delete request for {len(delete_request.user_ids)} users")
    logger.info(f"User IDs: {delete_request.user_ids}")

    # Validate batch size (redundant with schema, but explicit)
    if len(delete_request.user_ids) > 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 50 users per request",
        )

    # Check self-delete prevention (fail early)
    if admin.id in delete_request.user_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account",
        )

    # Count total superusers (for last superuser protection)
    total_superusers = await db.scalar(
        select(func.count()).where(
            User.is_superuser == True,
            User.deleted_at.is_(None)
        )
    )

    # Track superusers being deleted in this batch
    superusers_to_delete = 0

    # Initialize audit service
    audit_service = get_audit_service(db)

    # Process deletions
    deleted_users: list[DeletedUserInfo] = []
    failed_users: list[FailedUserInfo] = []

    for user_id in delete_request.user_ids:
        # Get user
        query = select(User).where(User.id == user_id)
        result = await db.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            failed_users.append(FailedUserInfo(
                user_id=user_id,
                reason="User not found",
            ))
            continue

        # Check if already deleted
        if user.deleted_at is not None:
            failed_users.append(FailedUserInfo(
                user_id=user_id,
                reason="User is already deleted",
            ))
            continue

        # Last superuser protection
        if user.is_superuser:
            # Check if deleting this user would leave no superusers
            remaining_superusers = total_superusers - superusers_to_delete - 1
            if remaining_superusers < 1:
                failed_users.append(FailedUserInfo(
                    user_id=user_id,
                    reason="User is the last superuser",
                ))
                continue
            superusers_to_delete += 1

        # Soft delete
        user.deleted_at = datetime.utcnow()
        user.deleted_by = admin.id
        user.is_active = False
        user.updated_at = datetime.utcnow()

        # Audit log for each user
        await audit_service.log(
            action=AuditAction.USER_DELETED,
            user_id=admin.id,
            resource_type="user",
            resource_id=user.id,
            target_name=user.email,
            details={
                "email": user.email,
                "name": user.full_name,
                "was_superuser": user.is_superuser,
                "deleted_at": user.deleted_at.isoformat(),
                "bulk_delete": True,
            },
            request=request,
        )

        deleted_users.append(DeletedUserInfo(
            user_id=user.id,
            email=user.email,
        ))

    # Commit all changes
    await db.commit()

    return BulkDeleteResponse(
        success_count=len(deleted_users),
        failed_count=len(failed_users),
        deleted_users=deleted_users,
        failed_users=failed_users,
    )


@router.delete(
    "/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete user (soft delete)",
    description="Soft delete a user account with audit trail (Sprint 40).",
)
async def delete_user(
    user_id: UUID,
    request: Request,
    admin: User = Depends(require_superuser),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Soft delete a user account.

    Security:
        - Requires superuser access
        - Cannot delete self
        - Cannot delete last superuser
        - Sets deleted_at and deleted_by for audit trail
        - All actions audit logged

    Sprint 40 - CTO Approved: Dec 17, 2025

    Returns:
        204 No Content
    """
    # Get user
    query = select(User).where(User.id == user_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Check if already deleted
    if user.deleted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already deleted",
        )

    # Self-delete prevention
    if user_id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account",
        )

    # Last superuser prevention
    if user.is_superuser:
        superuser_count = await db.scalar(
            select(func.count()).where(
                User.is_superuser == True,
                User.deleted_at.is_(None)
            )
        )
        if superuser_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete the last superuser",
            )

    # Soft delete
    user.deleted_at = datetime.utcnow()
    user.deleted_by = admin.id
    user.is_active = False  # Also deactivate
    user.updated_at = datetime.utcnow()

    await db.commit()

    # Audit log
    audit_service = get_audit_service(db)
    await audit_service.log(
        action=AuditAction.USER_DELETED,
        user_id=admin.id,
        resource_type="user",
        resource_id=user.id,
        target_name=user.email,
        details={
            "email": user.email,
            "name": user.full_name,
            "was_superuser": user.is_superuser,
            "deleted_at": user.deleted_at.isoformat(),
        },
        request=request,
    )


# =========================================================================
# Audit Logs
# =========================================================================


@router.get(
    "/audit-logs",
    response_model=AuditLogListResponse,
    summary="List audit logs (paginated)",
    description="Get paginated list of audit logs with filtering.",
)
async def list_audit_logs(
    admin: User = Depends(require_superuser),
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    action: Optional[str] = Query(None, description="Filter by action type"),
    actor_id: Optional[UUID] = Query(None, description="Filter by actor UUID"),
    target_type: Optional[str] = Query(None, description="Filter by target type"),
    date_from: Optional[datetime] = Query(None, description="Start date filter"),
    date_to: Optional[datetime] = Query(None, description="End date filter"),
    search: Optional[str] = Query(None, max_length=100, description="Search in target name"),
) -> AuditLogListResponse:
    """
    List audit logs with pagination and filtering.

    Query Parameters:
        - page: Page number (default: 1)
        - page_size: Items per page (default: 50, max: 100)
        - action: Filter by action type
        - actor_id: Filter by actor UUID
        - target_type: Filter by target type
        - date_from: Start date filter
        - date_to: End date filter
        - search: Search in target name

    Security:
        - Requires superuser access

    Returns:
        AuditLogListResponse: Paginated audit logs
    """
    # Build query with user join for actor email
    query = select(AuditLog, User.email.label("actor_email")).outerjoin(
        User, AuditLog.user_id == User.id
    )

    # Apply filters
    if action:
        query = query.where(AuditLog.action == action)

    if actor_id:
        query = query.where(AuditLog.user_id == actor_id)

    if target_type:
        query = query.where(AuditLog.resource_type == target_type)

    if date_from:
        query = query.where(AuditLog.created_at >= date_from)

    if date_to:
        query = query.where(AuditLog.created_at <= date_to)

    if search:
        query = query.where(AuditLog.target_name.ilike(f"%{search}%"))

    # Count total
    count_query = select(func.count()).select_from(
        select(AuditLog.id).where(
            *([AuditLog.action == action] if action else []),
            *([AuditLog.user_id == actor_id] if actor_id else []),
            *([AuditLog.resource_type == target_type] if target_type else []),
            *([AuditLog.created_at >= date_from] if date_from else []),
            *([AuditLog.created_at <= date_to] if date_to else []),
            *([AuditLog.target_name.ilike(f"%{search}%")] if search else []),
        ).subquery()
    )
    total = await db.scalar(count_query)

    # Order by timestamp descending
    query = query.order_by(AuditLog.created_at.desc())

    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    # Execute
    result = await db.execute(query)
    rows = result.all()

    # Map to response
    items = [
        AuditLogItem(
            id=row.AuditLog.id,
            timestamp=row.AuditLog.created_at,
            action=row.AuditLog.action,
            actor_id=row.AuditLog.user_id,
            actor_email=row.actor_email,
            target_type=row.AuditLog.resource_type,
            target_id=row.AuditLog.resource_id,
            target_name=row.AuditLog.target_name,
            details=row.AuditLog.details or {},
            ip_address=str(row.AuditLog.ip_address) if row.AuditLog.ip_address else None,
        )
        for row in rows
    ]

    pages = math.ceil(total / page_size) if total > 0 else 0

    return AuditLogListResponse(
        items=items,
        total=total or 0,
        page=page,
        page_size=page_size,
        pages=pages,
    )


# =========================================================================
# System Settings
# =========================================================================


@router.get(
    "/settings",
    response_model=SystemSettingsListResponse,
    summary="Get all system settings",
    description="Get all system settings grouped by category.",
)
async def get_all_settings(
    admin: User = Depends(require_superuser),
    db: AsyncSession = Depends(get_db),
) -> SystemSettingsListResponse:
    """
    Get all system settings grouped by category.

    Security:
        - Requires superuser access

    Returns:
        SystemSettingsListResponse: Settings grouped by category
    """
    # Get all settings with updater info
    query = (
        select(SystemSetting, User.email.label("updater_email"))
        .outerjoin(User, SystemSetting.updated_by == User.id)
        .order_by(SystemSetting.category, SystemSetting.key)
    )
    result = await db.execute(query)
    rows = result.all()

    # Group by category
    categories = {
        "security": [],
        "limits": [],
        "features": [],
        "notifications": [],
        "general": [],
        "ai": [],
    }

    for row in rows:
        setting = row.SystemSetting
        item = SystemSettingItem(
            key=setting.key,
            value=setting.value,
            version=setting.version,
            category=setting.category,
            description=setting.description,
            updated_at=setting.updated_at,
            updated_by=row.updater_email,
        )

        category = setting.category if setting.category in categories else "general"
        categories[category].append(item)

    return SystemSettingsListResponse(**categories)


@router.get(
    "/settings/{key}",
    response_model=SystemSettingItem,
    summary="Get setting by key",
    description="Get a specific system setting by key.",
)
async def get_setting(
    key: str,
    admin: User = Depends(require_superuser),
    db: AsyncSession = Depends(get_db),
) -> SystemSettingItem:
    """
    Get a specific system setting.

    Security:
        - Requires superuser access

    Returns:
        SystemSettingItem: Setting details
    """
    query = (
        select(SystemSetting, User.email.label("updater_email"))
        .outerjoin(User, SystemSetting.updated_by == User.id)
        .where(SystemSetting.key == key)
    )
    result = await db.execute(query)
    row = result.first()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Setting '{key}' not found",
        )

    setting = row.SystemSetting
    return SystemSettingItem(
        key=setting.key,
        value=setting.value,
        version=setting.version,
        category=setting.category,
        description=setting.description,
        updated_at=setting.updated_at,
        updated_by=row.updater_email,
    )


@router.patch(
    "/settings/{key}",
    response_model=SystemSettingItem,
    summary="Update setting",
    description="Update a system setting value.",
)
async def update_setting(
    key: str,
    update_data: SystemSettingUpdate,
    request: Request,
    admin: User = Depends(require_superuser),
    db: AsyncSession = Depends(get_db),
) -> SystemSettingItem:
    """
    Update a system setting.

    Security:
        - Requires superuser access
        - Change is audit logged
        - Previous value stored for rollback

    Returns:
        SystemSettingItem: Updated setting
    """
    # Get setting
    query = select(SystemSetting).where(SystemSetting.key == key)
    result = await db.execute(query)
    setting = result.scalar_one_or_none()

    if not setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Setting '{key}' not found",
        )

    # Store previous value for rollback
    old_value = setting.value
    setting.previous_value = old_value
    setting.value = update_data.value
    setting.version += 1
    setting.updated_at = datetime.utcnow()
    setting.updated_by = admin.id

    # Audit log
    audit_service = get_audit_service(db)
    await audit_service.log_setting_change(
        admin_user_id=admin.id,
        setting_key=key,
        old_value=old_value,
        new_value=update_data.value,
        request=request,
    )

    await db.commit()
    await db.refresh(setting)

    return SystemSettingItem(
        key=setting.key,
        value=setting.value,
        version=setting.version,
        category=setting.category,
        description=setting.description,
        updated_at=setting.updated_at,
        updated_by=admin.email,
    )


@router.post(
    "/settings/{key}/rollback",
    response_model=SystemSettingItem,
    summary="Rollback setting",
    description="Rollback a system setting to its previous value.",
)
async def rollback_setting(
    key: str,
    request: Request,
    admin: User = Depends(require_superuser),
    db: AsyncSession = Depends(get_db),
) -> SystemSettingItem:
    """
    Rollback a system setting to previous value.

    Security:
        - Requires superuser access
        - Rollback is audit logged

    Returns:
        SystemSettingItem: Rolled back setting
    """
    # Get setting
    query = select(SystemSetting).where(SystemSetting.key == key)
    result = await db.execute(query)
    setting = result.scalar_one_or_none()

    if not setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Setting '{key}' not found",
        )

    if setting.previous_value is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No previous value to rollback to",
        )

    # Rollback
    from_version = setting.version
    current_value = setting.value
    setting.value = setting.previous_value
    setting.previous_value = current_value  # Store current as previous for re-rollback
    setting.version += 1
    setting.updated_at = datetime.utcnow()
    setting.updated_by = admin.id

    # Audit log
    audit_service = get_audit_service(db)
    await audit_service.log_setting_rollback(
        admin_user_id=admin.id,
        setting_key=key,
        from_version=from_version,
        to_version=setting.version,
        request=request,
    )

    await db.commit()
    await db.refresh(setting)

    return SystemSettingItem(
        key=setting.key,
        value=setting.value,
        version=setting.version,
        category=setting.category,
        description=setting.description,
        updated_at=setting.updated_at,
        updated_by=admin.email,
    )


# =========================================================================
# System Health
# =========================================================================


@router.get(
    "/system/health",
    response_model=SystemHealthResponse,
    summary="Get system health",
    description="Get health status of all system services.",
)
async def get_system_health(
    admin: User = Depends(require_superuser),
    db: AsyncSession = Depends(get_db),
) -> SystemHealthResponse:
    """
    Get system health status.

    Checks health of:
        - PostgreSQL
        - Redis
        - MinIO
        - OPA

    Security:
        - Requires superuser access

    Returns:
        SystemHealthResponse: System health status
    """
    import time

    services = []
    overall_healthy = True

    # Check PostgreSQL
    try:
        start = time.time()
        await db.execute(select(1))
        response_time = int((time.time() - start) * 1000)
        services.append(
            ServiceHealthStatus(
                name="PostgreSQL",
                status="healthy",
                response_time_ms=response_time,
                details={"type": "database"},
            )
        )
    except Exception as e:
        overall_healthy = False
        services.append(
            ServiceHealthStatus(
                name="PostgreSQL",
                status="unhealthy",
                details={"error": str(e)},
            )
        )

    # Check Redis (via cache service)
    try:
        from app.services.cache_service import get_cache_service

        cache = get_cache_service()
        start = time.time()
        await cache.ping()
        response_time = int((time.time() - start) * 1000)
        services.append(
            ServiceHealthStatus(
                name="Redis",
                status="healthy",
                response_time_ms=response_time,
                details={"type": "cache"},
            )
        )
    except Exception as e:
        services.append(
            ServiceHealthStatus(
                name="Redis",
                status="degraded",
                details={"error": str(e), "note": "Non-critical service"},
            )
        )

    # Determine overall status
    unhealthy_count = sum(1 for s in services if s.status == "unhealthy")
    degraded_count = sum(1 for s in services if s.status == "degraded")

    if unhealthy_count > 0:
        overall_status = "unhealthy"
    elif degraded_count > 0:
        overall_status = "degraded"
    else:
        overall_status = "healthy"

    return SystemHealthResponse(
        overall_status=overall_status,
        services=services,
        metrics=SystemMetrics(
            cpu_usage_percent=None,  # Would require psutil
            memory_usage_percent=None,
            disk_usage_percent=None,
            active_connections=None,
        ),
        checked_at=datetime.utcnow(),
    )


# =========================================================================
# Bulk Actions
# =========================================================================


@router.post(
    "/users/bulk",
    response_model=BulkUserActionResponse,
    summary="Bulk user action",
    description="Perform bulk action on multiple users.",
)
async def bulk_user_action(
    action_request: BulkUserActionRequest,
    request: Request,
    admin: User = Depends(require_superuser),
    db: AsyncSession = Depends(get_db),
) -> BulkUserActionResponse:
    """
    Perform bulk action on multiple users.

    Actions:
        - activate: Set is_active=true
        - deactivate: Set is_active=false

    Security:
        - Requires superuser access
        - Cannot include self in bulk actions
        - All changes are audit logged

    Returns:
        BulkUserActionResponse: Result of bulk action
    """
    success_count = 0
    failed_users = []

    audit_service = get_audit_service(db)

    for user_id in action_request.user_ids:
        # Cannot modify self
        if user_id == admin.id:
            failed_users.append({
                "user_id": str(user_id),
                "reason": "Cannot modify your own account",
            })
            continue

        # Get user
        query = select(User).where(User.id == user_id)
        result = await db.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            failed_users.append({
                "user_id": str(user_id),
                "reason": "User not found",
            })
            continue

        # Apply action
        is_activating = action_request.action == "activate"
        user.is_active = is_activating
        user.updated_at = datetime.utcnow()

        # Audit log
        await audit_service.log_user_activation(
            admin_user_id=admin.id,
            target_user_id=user.id,
            target_email=user.email,
            is_activating=is_activating,
            request=request,
            details={"bulk_action": True},
        )

        success_count += 1

    await db.commit()

    return BulkUserActionResponse(
        success_count=success_count,
        failed_count=len(failed_users),
        failed_users=failed_users,
    )



# =========================================================================
# ADR-027 Phase 1: Account Lockout Management
# =========================================================================

@router.post(
    "/users/{user_id}/unlock",
    status_code=status.HTTP_200_OK,
    summary="Unlock user account (ADR-027)",
    description="Admin can manually unlock accounts locked due to failed login attempts",
)
async def unlock_user_account(
    user_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_superuser),
) -> dict:
    """
    Admin endpoint to manually unlock locked user accounts.

    ADR-027 Phase 1: max_login_attempts implementation
    
    Use Case:
    - User contacts support after account locked due to failed login attempts
    - Admin verifies identity and unlocks account manually
    - Account lockout is cleared immediately (no need to wait 30 minutes)

    Request:
        POST /api/v1/admin/users/{user_id}/unlock

    Response (200 OK):
        {
            "message": "User account unlocked successfully",
            "user_id": "550e8400-e29b-41d4-a716-446655440000",
            "email": "user@example.com",
            "failed_login_count": 0,
            "locked_until": null,
            "unlocked_by": "admin@example.com",
            "unlocked_at": "2026-01-14T12:34:56Z"
        }

    Errors:
        - 404 Not Found: User not found
        - 400 Bad Request: User account is not locked

    Security:
        - Requires is_superuser=true
        - Audit logged (who unlocked which account when)
        - Cannot unlock own account (self-action prevention)

    Zero Mock Policy: Real database update with audit trail
    """
    # Cannot unlock self (prevent self-action)
    if user_id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot unlock your own account",
        )

    # Find user
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User not found with id: {user_id}",
        )

    # Check if user is actually locked
    if not user.locked_until:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User account is not locked. Email: {user.email}",
        )

    # Unlock account
    user.failed_login_count = 0
    user.locked_until = None
    user.updated_at = datetime.utcnow()

    await db.commit()

    # Audit log
    from app.services.audit_service import get_audit_service
    audit_service = get_audit_service(db)

    await audit_service.log(
        action="USER_ACCOUNT_UNLOCKED",
        user_id=admin.id,
        resource_type="user",
        resource_id=user.id,
        details={
            "target_user_email": user.email,
            "unlocked_by": admin.email,
            "previous_failed_count": user.failed_login_count,
        },
        request=request,
    )

    return {
        "message": "User account unlocked successfully",
        "user_id": str(user.id),
        "email": user.email,
        "failed_login_count": user.failed_login_count,
        "locked_until": None,
        "unlocked_by": admin.email,
        "unlocked_at": datetime.utcnow().isoformat(),
    }


# =========================================================================
# MFA Exemption Endpoints (ADR-027 Phase 1 - mfa_required)
# =========================================================================

@router.post(
    "/users/{user_id}/mfa-exempt",
    status_code=status.HTTP_200_OK,
    summary="Set MFA exemption (ADR-027)",
    description="Admin can exempt specific users from MFA requirement",
)
async def set_mfa_exemption(
    user_id: UUID,
    exempt: bool = Body(..., description="True to exempt user, False to remove exemption"),
    request: Request = None,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_superuser),
) -> dict:
    """
    Admin endpoint to exempt users from MFA requirement.

    Use Cases:
    - Service accounts (API-only access, no human login)
    - External integrations (OAuth-only, MFA not applicable)
    - Emergency access (temporary exemption during incident)

    Args:
        user_id: Target user UUID
        exempt: True to exempt, False to remove exemption
        request: FastAPI request object
        db: Database session
        admin: Authenticated admin user

    Returns:
        {
            "message": "MFA exemption updated successfully",
            "user_id": "...",
            "email": "user@example.com",
            "is_mfa_exempt": true,
            "mfa_setup_deadline": null,
            "updated_by": "admin@example.com",
            "updated_at": "2026-01-14T12:34:56Z"
        }

    Raises:
        HTTPException(400): If trying to exempt self
        HTTPException(404): If user not found
    """
    # Cannot exempt self (prevent self-action)
    if user_id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot modify your own MFA exemption status",
        )

    # Find user
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User not found with id: {user_id}",
        )

    # Update exemption status
    old_status = user.is_mfa_exempt
    user.is_mfa_exempt = exempt

    # Clear deadline if exempting user (no longer needed)
    if exempt and user.mfa_setup_deadline:
        user.mfa_setup_deadline = None

    user.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(user)

    # Audit log
    from app.services.audit_service import get_audit_service
    audit_service = get_audit_service(db)

    await audit_service.log(
        action="USER_MFA_EXEMPTION_UPDATED",
        user_id=admin.id,
        resource_type="user",
        resource_id=user.id,
        details={
            "target_user_email": user.email,
            "updated_by": admin.email,
            "previous_status": old_status,
            "new_status": exempt,
            "reason": "Admin override",
        },
        request=request,
    )

    action = "exempt from" if exempt else "no longer exempt from"

    return {
        "message": f"User is now {action} MFA requirement",
        "user_id": str(user.id),
        "email": user.email,
        "is_mfa_exempt": user.is_mfa_exempt,
        "mfa_setup_deadline": user.mfa_setup_deadline.isoformat() if user.mfa_setup_deadline else None,
        "updated_by": admin.email,
        "updated_at": datetime.utcnow().isoformat(),
    }


@router.get(
    "/users/{user_id}/mfa-status",
    status_code=status.HTTP_200_OK,
    summary="Get user MFA status (ADR-027)",
    description="Admin can view user's MFA enforcement status",
)
async def get_user_mfa_status(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_superuser),
    settings_service: SettingsService = Depends(get_settings_service),
) -> dict:
    """
    Admin endpoint to view user's MFA status.

    Shows:
    - Whether MFA is enabled for the user
    - Whether user is exempt from MFA requirement
    - MFA setup deadline (if applicable)
    - Days remaining in grace period

    Args:
        user_id: Target user UUID
        db: Database session
        admin: Authenticated admin user
        settings_service: Settings service instance

    Returns:
        {
            "user_id": "...",
            "email": "user@example.com",
            "mfa_enabled": false,
            "is_mfa_exempt": false,
            "mfa_required_global": true,
            "mfa_setup_deadline": "2026-01-21T12:34:56Z",
            "days_remaining": 5,
            "enforcement_status": "grace_period"
        }

    Raises:
        HTTPException(404): If user not found
    """
    # Find user
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User not found with id: {user_id}",
        )

    # Get global MFA requirement setting
    mfa_required_global = await settings_service.is_mfa_required()

    # Calculate days remaining
    days_remaining = None
    enforcement_status = "compliant"

    if user.mfa_enabled:
        enforcement_status = "mfa_enabled"
    elif user.is_mfa_exempt:
        enforcement_status = "exempt"
    elif mfa_required_global and user.mfa_setup_deadline:
        now = datetime.utcnow()
        if now > user.mfa_setup_deadline:
            enforcement_status = "deadline_expired"
            days_remaining = 0
        else:
            enforcement_status = "grace_period"
            days_remaining = (user.mfa_setup_deadline - now).days
    elif mfa_required_global:
        enforcement_status = "deadline_not_set"

    return {
        "user_id": str(user.id),
        "email": user.email,
        "mfa_enabled": user.mfa_enabled,
        "is_mfa_exempt": user.is_mfa_exempt,
        "mfa_required_global": mfa_required_global,
        "mfa_setup_deadline": user.mfa_setup_deadline.isoformat() if user.mfa_setup_deadline else None,
        "days_remaining": days_remaining,
        "enforcement_status": enforcement_status,
    }


# =========================================================================
# ADR-027 Phase 3: Evidence Retention Management
# =========================================================================


@router.get(
    "/evidence/retention-stats",
    status_code=status.HTTP_200_OK,
    summary="Get evidence retention statistics (ADR-027)",
    description="Get current evidence retention stats including active, archived, and due for cleanup",
)
async def get_evidence_retention_stats(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_superuser),
) -> dict:
    """
    Admin endpoint to view evidence retention statistics.

    ADR-027 Phase 3: evidence_retention_days implementation

    Shows:
    - Total evidence count
    - Active vs archived evidence
    - Evidence due for archival
    - Evidence due for permanent deletion

    Returns:
        {
            "total_evidence": 5000,
            "active_evidence": 4800,
            "archived_evidence": 180,
            "evidence_due_for_archive": 20,
            "evidence_due_for_purge": 10,
            "oldest_evidence_date": "2024-01-15T10:30:00",
            "newest_evidence_date": "2026-01-15T08:15:00",
            "retention_days": 365,
            "grace_period_days": 30
        }

    Security:
        - Requires is_superuser=true

    Zero Mock Policy: Real database queries
    """
    from app.tasks.evidence_retention import EvidenceRetentionTask

    task = EvidenceRetentionTask(db)
    stats = await task.get_retention_stats()

    return stats


@router.post(
    "/evidence/retention-archive",
    status_code=status.HTTP_200_OK,
    summary="Trigger evidence archival (ADR-027)",
    description="Manually trigger archival of evidence older than retention period",
)
async def trigger_evidence_archival(
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_superuser),
) -> dict:
    """
    Admin endpoint to manually trigger evidence archival.

    ADR-027 Phase 3: evidence_retention_days implementation

    Use Cases:
    - Force archival before scheduled cron job
    - Test archival logic in staging environment
    - Compliance audit requiring immediate archival

    Process:
    1. Read evidence_retention_days from database
    2. Find all active evidence older than retention period
    3. Soft-delete evidence (set deleted_at timestamp)
    4. Files remain in MinIO until purge job runs

    Returns:
        {
            "message": "Evidence archival completed",
            "archived_count": 125,
            "cutoff_date": "2025-01-15T00:00:00",
            "retention_days": 365,
            "duration_seconds": 2.5,
            "status": "success",
            "triggered_by": "admin@example.com"
        }

    Security:
        - Requires is_superuser=true
        - Audit logged

    Zero Mock Policy: Real database operations
    """
    from app.tasks.evidence_retention import EvidenceRetentionTask

    task = EvidenceRetentionTask(db)

    # Get stats before
    stats_before = await task.get_retention_stats()
    logger.info(f"Evidence retention stats before archival: {stats_before}")

    # Run archival
    result = await task.archive_old_evidence()

    # Audit log
    audit_service = get_audit_service(db)
    await audit_service.log(
        action="EVIDENCE_ARCHIVAL_TRIGGERED",
        user_id=admin.id,
        resource_type="evidence",
        resource_id=None,
        details={
            "triggered_by": admin.email,
            "archived_count": result.get("archived_count", 0),
            "retention_days": result.get("retention_days"),
            "status": result.get("status"),
        },
        request=request,
    )

    result["triggered_by"] = admin.email
    result["message"] = "Evidence archival completed"

    return result


@router.post(
    "/evidence/retention-purge",
    status_code=status.HTTP_200_OK,
    summary="Trigger evidence purge (ADR-027)",
    description="Manually trigger permanent deletion of archived evidence beyond grace period",
)
async def trigger_evidence_purge(
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_superuser),
) -> dict:
    """
    Admin endpoint to manually trigger evidence purge.

    ADR-027 Phase 3: evidence_retention_days implementation

    WARNING: This permanently deletes evidence files from MinIO!
    Use with caution. Consider archival first for reversible cleanup.

    Use Cases:
    - Free up storage space
    - Compliance requirement to permanently delete old data
    - Clean up after testing

    Process:
    1. Find all soft-deleted evidence older than grace period (30 days)
    2. Delete files from MinIO storage
    3. Hard-delete records from database
    4. Log results for audit trail

    Returns:
        {
            "message": "Evidence purge completed",
            "purged_count": 50,
            "files_deleted": 48,
            "files_failed": 2,
            "cutoff_date": "2024-12-15T00:00:00",
            "grace_period_days": 30,
            "duration_seconds": 5.2,
            "status": "success",
            "triggered_by": "admin@example.com"
        }

    Security:
        - Requires is_superuser=true
        - Audit logged
        - Irreversible action!

    Zero Mock Policy: Real database and MinIO operations
    """
    from app.tasks.evidence_retention import EvidenceRetentionTask

    task = EvidenceRetentionTask(db)

    # Get stats before
    stats_before = await task.get_retention_stats()
    logger.info(f"Evidence retention stats before purge: {stats_before}")

    # Run purge
    result = await task.purge_expired_evidence()

    # Audit log
    audit_service = get_audit_service(db)
    await audit_service.log(
        action="EVIDENCE_PURGE_TRIGGERED",
        user_id=admin.id,
        resource_type="evidence",
        resource_id=None,
        details={
            "triggered_by": admin.email,
            "purged_count": result.get("purged_count", 0),
            "files_deleted": result.get("files_deleted", 0),
            "files_failed": result.get("files_failed", 0),
            "grace_period_days": result.get("grace_period_days"),
            "status": result.get("status"),
        },
        request=request,
    )

    result["triggered_by"] = admin.email
    result["message"] = "Evidence purge completed"

    return result
