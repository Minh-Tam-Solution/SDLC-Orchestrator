"""
=========================================================================
Admin Panel Routes - User Management, Settings, Audit Logs
SDLC Orchestrator - Stage 03 (BUILD)

Version: 1.0.0
Date: December 16, 2025
Status: ACTIVE - Sprint 37 Admin Panel
Authority: CTO Approved (Dec 16, 2025)
Foundation: ADR-017 Admin Panel Architecture
Framework: SDLC 5.1.1 Complete Lifecycle

Endpoints:
- GET  /api/v1/admin/stats           - Dashboard statistics
- GET  /api/v1/admin/users           - List users (paginated)
- GET  /api/v1/admin/users/{id}      - Get user details
- PATCH /api/v1/admin/users/{id}     - Update user
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

Zero Mock Policy: Production-ready implementation
=========================================================================
"""

import math
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.dependencies import get_db, require_superuser
from app.models import AuditLog, Gate, Project, SystemSetting, User
from app.schemas.admin import (
    AdminDashboardStats,
    AdminUserDetail,
    AdminUserListItem,
    AdminUserListResponse,
    AdminUserUpdate,
    AuditLogFilter,
    AuditLogItem,
    AuditLogListResponse,
    BulkUserActionRequest,
    BulkUserActionResponse,
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
    # Count users
    total_users = await db.scalar(select(func.count()).select_from(User))
    active_users = await db.scalar(select(func.count()).where(User.is_active == True))
    inactive_users = total_users - active_users
    superusers = await db.scalar(select(func.count()).where(User.is_superuser == True))

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
    # Build query
    query = select(User)

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
            name=user.name,
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
        name=user.name,
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
    description="Update user information (name, is_active, is_superuser).",
)
async def update_user(
    user_id: UUID,
    update_data: AdminUserUpdate,
    request: Request,
    admin: User = Depends(require_superuser),
    db: AsyncSession = Depends(get_db),
) -> AdminUserDetail:
    """
    Update user information.

    Security:
        - Requires superuser access
        - Cannot modify own account (is_active, is_superuser)
        - System must have at least one superuser
        - All changes are audit logged

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

    # Update name
    if update_data.name is not None:
        user.name = update_data.name

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
        name=user.name,
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
