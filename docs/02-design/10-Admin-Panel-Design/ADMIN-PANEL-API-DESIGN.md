# Admin Panel - API Design Specification
## SDLC 6.1.0 Complete Lifecycle - Design Phase

**Version**: 2.3.0
**Date**: 2026-01-25
**Status**: DESIGN - Sprint 105 (Show Deleted Users + Permanent Delete)
**Author**: Backend Lead
**Reviewer**: CTO

**Changelog**:
- v2.3.0 (Jan 25, 2026): Added DELETE /users/{id}/permanent endpoint (Sprint 105 - Permanent Delete)
- v2.2.0 (Jan 25, 2026): Added include_deleted param + POST /users/{id}/restore endpoint (Sprint 105)
- v2.1.0 (Dec 18, 2025): Added DELETE /users/bulk endpoint (Sprint 40 Part 3) - CTO APPROVED
- v2.0.0 (Dec 17, 2025): Added POST /users, DELETE /users, soft delete (Sprint 40)
- v1.1.0 (Dec 16, 2025): Version field added to system_settings (CTO condition)
- v1.0.0 (Dec 16, 2025): Initial API design (Sprint 37)

---

## 1. Overview

### 1.1 Base URL
```
/api/v1/admin
```

### 1.2 Authentication
All endpoints require:
- Valid JWT token in `Authorization: Bearer <token>` header
- User must have `is_superuser=true`

### 1.3 Error Responses
```json
{
  "detail": "Error message",
  "error_code": "ADMIN_001",
  "timestamp": "2025-12-16T10:00:00Z"
}
```

---

## 2. Endpoints

### 2.1 Dashboard Statistics

#### GET /api/v1/admin/stats

Get system-wide statistics for admin dashboard.

**Request**:
```http
GET /api/v1/admin/stats
Authorization: Bearer <admin_token>
```

**Response** (200 OK):
```json
{
  "users": {
    "total": 150,
    "active": 120,
    "inactive": 30,
    "admins": 3,
    "new_last_7_days": 12
  },
  "projects": {
    "total": 45,
    "active": 40
  },
  "gates": {
    "total": 180,
    "passed": 120,
    "blocked": 35,
    "pending": 25
  },
  "evidence": {
    "total": 523,
    "total_size_mb": 1250
  },
  "system": {
    "uptime_hours": 720,
    "last_backup": "2025-12-15T00:00:00Z"
  },
  "generated_at": "2025-12-16T10:00:00Z"
}
```

**Caching**: 5 minutes TTL

---

### 2.2 User Management

#### GET /api/v1/admin/users

List all users with pagination, search, and filters.

**Request**:
```http
GET /api/v1/admin/users?page=1&page_size=20&search=john&status=active&role=admin&sort_by=created_at&sort_order=desc
Authorization: Bearer <admin_token>
```

**Query Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| page | int | 1 | Page number |
| page_size | int | 20 | Items per page (max 100) |
| search | string | - | Search in name/email |
| status | string | - | Filter: active, inactive |
| role | string | - | Filter: admin, user |
| include_deleted | boolean | false | Include soft-deleted users (Sprint 105) |
| sort_by | string | created_at | Sort field |
| sort_order | string | desc | asc or desc |

**Response** (200 OK):
```json
{
  "items": [
    {
      "id": "uuid",
      "email": "john@example.com",
      "name": "John Doe",
      "is_active": true,
      "is_superuser": false,
      "created_at": "2025-01-15T10:00:00Z",
      "updated_at": "2025-12-01T15:30:00Z",
      "last_login": "2025-12-16T08:00:00Z",
      "deleted_at": null,
      "projects_count": 5
    }
  ],
  "total": 150,
  "page": 1,
  "page_size": 20,
  "total_pages": 8
}
```

**Response Fields (Sprint 105 Update)**:
| Field | Type | Description |
|-------|------|-------------|
| deleted_at | datetime | null | Soft deletion timestamp (null = not deleted) |

---

#### GET /api/v1/admin/users/{user_id}

Get detailed user information.

**Request**:
```http
GET /api/v1/admin/users/550e8400-e29b-41d4-a716-446655440000
Authorization: Bearer <admin_token>
```

**Response** (200 OK):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "john@example.com",
  "name": "John Doe",
  "is_active": true,
  "is_superuser": false,
  "created_at": "2025-01-15T10:00:00Z",
  "updated_at": "2025-12-01T15:30:00Z",
  "last_login": "2025-12-16T08:00:00Z",
  "projects": [
    {
      "id": "uuid",
      "name": "Project Alpha",
      "role": "owner"
    }
  ],
  "activity": {
    "logins_last_30_days": 25,
    "actions_last_30_days": 150
  }
}
```

**Error Responses**:
- 404: User not found

---

#### POST /api/v1/admin/users (Sprint 40 - NEW)

Create a new user account with email and password.

**Request**:
```http
POST /api/v1/admin/users
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "email": "newuser@example.com",
  "password": "SecurePassword123!",
  "name": "New User",
  "is_active": true,
  "is_superuser": false
}
```

**Request Body**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| email | EmailStr | Yes | User email (must be unique) |
| password | string | Yes | Password (min 12 chars) |
| name | string | No | User full name |
| is_active | boolean | No | Active status (default: true) |
| is_superuser | boolean | No | Superuser status (default: false) |

**Response** (201 Created):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "email": "newuser@example.com",
  "name": "New User",
  "is_active": true,
  "is_superuser": false,
  "mfa_enabled": false,
  "oauth_providers": [],
  "project_count": 0,
  "created_at": "2025-12-17T10:00:00Z",
  "updated_at": "2025-12-17T10:00:00Z",
  "last_login": null
}
```

**Error Responses**:
- 400: User with email already exists
- 400: Password too short (min 12 characters)

**Security**:
- Password hashed with bcrypt (cost=12)
- Email validated and lowercased
- Audit log entry created (USER_CREATED)

---

#### PATCH /api/v1/admin/users/{user_id}

Update user properties (activate/deactivate, change role).

**Request**:
```http
PATCH /api/v1/admin/users/550e8400-e29b-41d4-a716-446655440000
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "is_active": false,
  "is_superuser": true,
  "name": "John Doe Updated"
}
```

**Request Body** (all optional):
| Field | Type | Description |
|-------|------|-------------|
| is_active | boolean | Activate/deactivate user |
| is_superuser | boolean | Grant/revoke admin |
| name | string | Update display name |

**Response** (200 OK):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "john@example.com",
  "name": "John Doe Updated",
  "is_active": false,
  "is_superuser": true,
  "updated_at": "2025-12-16T10:30:00Z"
}
```

**Error Responses**:
- 400: Cannot modify own account
- 400: At least one superuser required
- 404: User not found

**Side Effects**:
- If `is_active=false`: Invalidate all user sessions
- Creates audit log entry

---

#### DELETE /api/v1/admin/users/{user_id}

Soft delete user with full audit trail (Sprint 40 - CTO Approved).

**Request**:
```http
DELETE /api/v1/admin/users/550e8400-e29b-41d4-a716-446655440000
Authorization: Bearer <admin_token>
```

**Response** (204 No Content):
```
(empty body)
```

**Error Responses**:
- 400: Cannot delete own account
- 400: Cannot delete last superuser
- 400: User is already deleted
- 404: User not found

**Side Effects**:
- Sets `deleted_at = NOW()` (soft delete timestamp)
- Sets `deleted_by = admin.id` (accountability audit)
- Sets `is_active = false` (deactivates user)
- Creates audit log entry with USER_DELETED action
- Preserves all user data for audit trail (no anonymization)

**Database Schema Update (Sprint 40)**:
```sql
-- Added to users table
ALTER TABLE users ADD COLUMN deleted_at TIMESTAMP NULL;
ALTER TABLE users ADD COLUMN deleted_by UUID REFERENCES users(id) ON DELETE SET NULL;
CREATE INDEX ix_users_deleted_at ON users(deleted_at);
CREATE INDEX ix_users_active_not_deleted ON users(is_active, deleted_at);
```

---

#### POST /api/v1/admin/users/{user_id}/restore (Sprint 105 - NEW)

Restore a soft-deleted user account. Clears deletion markers and reactivates the user.

**Request**:
```http
POST /api/v1/admin/users/550e8400-e29b-41d4-a716-446655440000/restore
Authorization: Bearer <admin_token>
```

**Response** (200 OK):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "john@example.com",
  "name": "John Doe",
  "is_active": true,
  "is_superuser": false,
  "mfa_enabled": false,
  "oauth_providers": [],
  "project_count": 5,
  "created_at": "2025-01-15T10:00:00Z",
  "updated_at": "2026-01-25T10:00:00Z",
  "last_login": "2025-12-16T08:00:00Z"
}
```

**Error Responses**:
- 400: `{"detail": "User is not deleted"}` - User was not soft-deleted
- 404: `{"detail": "User not found"}` - Invalid user_id

**Side Effects**:
- Sets `deleted_at = NULL` (removes soft delete marker)
- Sets `deleted_by = NULL` (removes deletion audit reference)
- Sets `is_active = true` (reactivates user)
- Creates audit log entry (USER_UPDATED with action="restore")

**Use Case**:
When a user was soft-deleted but needs to be restored (e.g., accidental deletion, or user wants to reactivate account), admin can use this endpoint to restore the user without losing any historical data.

**Frontend Integration (Sprint 105)**:
- Admin Users page shows "Show Deleted" toggle
- Deleted users display "Deleted" badge (red)
- Deleted users show "Restore" button instead of "Delete"
- Restore action calls POST /users/{id}/restore

---

#### DELETE /api/v1/admin/users/{user_id}/permanent (Sprint 105 - NEW)

Permanently delete a soft-deleted user and all associated data. **IRREVERSIBLE OPERATION**.

**IMPORTANT**: This endpoint only works for users that have been soft-deleted first (`deleted_at IS NOT NULL`). It handles all 65+ foreign key constraints that reference the users table.

**Request**:
```http
DELETE /api/v1/admin/users/550e8400-e29b-41d4-a716-446655440000/permanent
Authorization: Bearer <admin_token>
```

**Response** (204 No Content):
```
(empty body)
```

**Error Responses**:
- 400: `{"detail": "Cannot permanently delete active users. Please soft-delete first."}` - User not soft-deleted
- 400: `{"detail": "Cannot delete your own account"}` - Self-delete prevention
- 404: `{"detail": "User not found"}` - Invalid user_id

**Side Effects**:
1. **Audit Logs Rules**: Temporarily drops SOC 2 compliance rules (`audit_logs_no_update`, `audit_logs_no_delete`) then recreates them after operation
2. **FK Constraint Handling**: Processes all 65+ foreign key constraints:
   - **NOT NULL columns**: DELETE records from referencing tables
   - **Nullable columns**: SET NULL on referencing columns
3. **Audit Trail**: Sets `audit_logs.user_id = NULL` for all entries by this user (preserves audit history)
4. **Cascade Deletion**: Removes records from all related tables (projects, teams, evidence, etc.)
5. **Final Deletion**: Permanently removes user record from users table

**Implementation Details (Fix v10 - PostgreSQL-specific)**:

```python
@router.delete("/users/{user_id}/permanent", status_code=204)
async def permanent_delete_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    # Step 1: Validate user exists and is soft-deleted
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(404, "User not found")
    if user.deleted_at is None:
        raise HTTPException(400, "Cannot permanently delete active users. Please soft-delete first.")

    # Step 2: DROP audit_logs rules (SOC 2 compliance temporarily disabled)
    async with engine.begin() as conn:
        await conn.execute(text("DROP RULE IF EXISTS audit_logs_no_update ON audit_logs"))
        await conn.execute(text("DROP RULE IF EXISTS audit_logs_no_delete ON audit_logs"))

        # SET NULL on audit_logs
        await conn.execute(
            text("UPDATE audit_logs SET user_id = NULL WHERE user_id = :user_id"),
            {"user_id": str(user_id)}
        )

    # Step 3: Query ALL FK constraints from pg_constraint
    async with engine.begin() as conn:
        fk_query = await conn.execute(text("""
            SELECT cl.relname, a.attname, a.attnotnull
            FROM pg_constraint con
            JOIN pg_class cl ON con.conrelid = cl.oid
            JOIN pg_attribute a ON a.attrelid = cl.oid AND a.attnum = ANY(con.conkey)
            JOIN pg_class ref_cl ON con.confrelid = ref_cl.oid
            WHERE con.contype = 'f'
            AND ref_cl.relname = 'users'
            AND cl.relname != 'users'
        """))
        fk_constraints = fk_query.fetchall()

        # Step 4: Process each FK - DELETE if NOT NULL, SET NULL if nullable
        for table_name, column_name, is_not_null in fk_constraints:
            if is_not_null:
                await conn.execute(
                    text(f'DELETE FROM "{table_name}" WHERE "{column_name}" = :user_id'),
                    {"user_id": str(user_id)}
                )
            else:
                await conn.execute(
                    text(f'UPDATE "{table_name}" SET "{column_name}" = NULL WHERE "{column_name}" = :user_id'),
                    {"user_id": str(user_id)}
                )

        # Step 5: Delete the user permanently
        await conn.execute(
            text("DELETE FROM users WHERE id = :user_id"),
            {"user_id": str(user_id)}
        )

        # Step 6: Recreate audit_logs rules (SOC 2 compliance restored)
        await conn.execute(text("""
            CREATE RULE audit_logs_no_update AS ON UPDATE TO audit_logs
            DO INSTEAD NOTHING
        """))
        await conn.execute(text("""
            CREATE RULE audit_logs_no_delete AS ON DELETE TO audit_logs
            DO INSTEAD NOTHING
        """))

    return Response(status_code=204)
```

**Database Rules Affected (SOC 2 Compliance)**:

```sql
-- These rules protect audit_logs from modification
-- They are temporarily dropped during permanent delete operation

CREATE RULE audit_logs_no_update AS ON UPDATE TO audit_logs
DO INSTEAD NOTHING;

CREATE RULE audit_logs_no_delete AS ON DELETE TO audit_logs
DO INSTEAD NOTHING;
```

**FK Constraints Processed (65+ constraints)**:

| Table | Column | Action |
|-------|--------|--------|
| audit_logs | user_id | SET NULL |
| projects | created_by, updated_by | SET NULL |
| team_members | user_id | DELETE |
| evidence | uploaded_by | SET NULL |
| gates | approved_by | SET NULL |
| user_settings | user_id | DELETE |
| api_tokens | user_id | DELETE |
| ... | ... | ... |

**Security Considerations**:
- Only soft-deleted users can be permanently deleted (prevents accidental data loss)
- Admin cannot delete their own account
- All audit trail entries are preserved (user_id set to NULL, but action/details remain)
- Operation is atomic (all-or-nothing via transaction)

**Frontend Integration (Sprint 105)**:
- Deleted users show "Permanent Delete" button (red, dangerous action)
- Confirmation dialog warns: "This action is IRREVERSIBLE. All user data will be permanently deleted."
- Double confirmation required: Type "PERMANENTLY DELETE" to confirm
- Success: Show toast "User permanently deleted"
- Error: Show error message from API

**Use Case**:
GDPR "Right to Erasure" compliance - when a user requests complete data removal, admin can:
1. First soft-delete the user (preserves data for review period)
2. After review period, permanently delete to comply with erasure request

---

#### DELETE /api/v1/admin/users/bulk (Sprint 40 Part 3 - NEW)

Bulk soft delete multiple users with full audit trail. **CTO APPROVED Dec 18, 2025**.

**Request**:
```http
DELETE /api/v1/admin/users/bulk
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "user_ids": [
    "550e8400-e29b-41d4-a716-446655440001",
    "550e8400-e29b-41d4-a716-446655440002",
    "550e8400-e29b-41d4-a716-446655440003"
  ]
}
```

**Request Body**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| user_ids | UUID[] | Yes | Array of user IDs to delete (max 50) |

**Response** (200 OK):
```json
{
  "success_count": 3,
  "failed_count": 0,
  "deleted_users": [
    {"user_id": "550e8400-e29b-41d4-a716-446655440001", "email": "user1@example.com"},
    {"user_id": "550e8400-e29b-41d4-a716-446655440002", "email": "user2@example.com"},
    {"user_id": "550e8400-e29b-41d4-a716-446655440003", "email": "user3@example.com"}
  ],
  "failed_users": []
}
```

**Partial Success Response** (200 OK):
```json
{
  "success_count": 2,
  "failed_count": 1,
  "deleted_users": [
    {"user_id": "550e8400-e29b-41d4-a716-446655440001", "email": "user1@example.com"},
    {"user_id": "550e8400-e29b-41d4-a716-446655440002", "email": "user2@example.com"}
  ],
  "failed_users": [
    {"user_id": "550e8400-e29b-41d4-a716-446655440003", "reason": "User is the last superuser"}
  ]
}
```

**Error Responses**:
- 400: `{"detail": "Cannot delete your own account"}` - Self-delete prevention
- 400: `{"detail": "Cannot delete the last superuser"}` - Last admin protection
- 400: `{"detail": "Maximum 50 users per request"}` - Batch size limit (CTO condition)
- 400: `{"detail": "user_ids array cannot be empty"}` - Empty array validation
- 403: `{"detail": "Admin access required"}` - Non-admin user

**CTO Conditions Applied**:
1. **Batch Size Limit**: Maximum 50 users per request to prevent DOS and protect DB performance
2. **Partial Success Handling**: Returns detailed report with success/failed counts and reasons
3. **Rate Limiting**: 5 requests/minute per admin (applied at middleware level)

**Side Effects**:
- Each deleted user: `deleted_at = NOW()`, `deleted_by = admin.id`, `is_active = false`
- Creates individual audit log entry for each deleted user (USER_DELETED)
- Invalidates sessions for all deleted users
- Returns deleted users' emails for confirmation toast

**Implementation Pattern**:
```python
@router.delete("/users/bulk")
async def bulk_delete_users(
    request: BulkDeleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
) -> BulkDeleteResponse:
    # Validate batch size
    if len(request.user_ids) > 50:
        raise HTTPException(400, "Maximum 50 users per request")

    # Check self-delete
    if str(current_user.id) in request.user_ids:
        raise HTTPException(400, "Cannot delete your own account")

    # Process deletions with partial success handling
    results = {"success": [], "failed": []}
    for user_id in request.user_ids:
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                results["failed"].append({"user_id": user_id, "reason": "User not found"})
                continue

            # Check last superuser
            if user.is_superuser and is_last_superuser(db, user_id):
                results["failed"].append({"user_id": user_id, "reason": "User is the last superuser"})
                continue

            # Soft delete
            user.deleted_at = datetime.utcnow()
            user.deleted_by = current_user.id
            user.is_active = False

            # Audit log
            create_audit_log(db, "user.bulk_deleted", current_user, "user", user_id, user.email)

            results["success"].append({"user_id": user_id, "email": user.email})
        except Exception as e:
            results["failed"].append({"user_id": user_id, "reason": str(e)})

    db.commit()
    return BulkDeleteResponse(
        success_count=len(results["success"]),
        failed_count=len(results["failed"]),
        deleted_users=results["success"],
        failed_users=results["failed"]
    )
```

**Pydantic Schemas**:
```python
class BulkDeleteRequest(BaseModel):
    user_ids: List[UUID] = Field(..., min_items=1, max_items=50)

class DeletedUser(BaseModel):
    user_id: UUID
    email: str

class FailedUser(BaseModel):
    user_id: UUID
    reason: str

class BulkDeleteResponse(BaseModel):
    success_count: int
    failed_count: int
    deleted_users: List[DeletedUser]
    failed_users: List[FailedUser]
```

---

### 2.3 Audit Logs

#### GET /api/v1/admin/audit-logs

Get audit logs with pagination and filters.

**Request**:
```http
GET /api/v1/admin/audit-logs?page=1&page_size=50&action=user.deactivated&actor_id=uuid&start_date=2025-12-01&end_date=2025-12-16
Authorization: Bearer <admin_token>
```

**Query Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| page | int | 1 | Page number |
| page_size | int | 50 | Items per page (max 100) |
| action | string | - | Filter by action type |
| actor_id | uuid | - | Filter by actor |
| target_type | string | - | Filter: user, project, gate |
| start_date | date | - | From date |
| end_date | date | - | To date |
| search | string | - | Search in details |

**Response** (200 OK):
```json
{
  "items": [
    {
      "id": "uuid",
      "timestamp": "2025-12-16T10:00:00Z",
      "action": "user.deactivated",
      "actor": {
        "id": "uuid",
        "email": "admin@sdlc-orchestrator.io",
        "name": "Platform Admin"
      },
      "target_type": "user",
      "target_id": "uuid",
      "target_name": "john@example.com",
      "details": {
        "previous_status": "active",
        "new_status": "inactive",
        "reason": "Policy violation"
      },
      "ip_address": "192.168.1.100",
      "user_agent": "Mozilla/5.0..."
    }
  ],
  "total": 1250,
  "page": 1,
  "page_size": 50,
  "total_pages": 25
}
```

**Action Types**:
```yaml
User Actions:
  - user.created
  - user.updated
  - user.deactivated
  - user.activated
  - user.deleted
  - user.promoted_admin
  - user.demoted_admin

System Actions:
  - system.setting_changed
  - system.backup_created
  - system.maintenance_started

Auth Actions:
  - auth.login_failed
  - auth.password_reset
```

---

### 2.4 System Health

#### GET /api/v1/admin/system/health

Get comprehensive system health status.

**Request**:
```http
GET /api/v1/admin/system/health
Authorization: Bearer <admin_token>
```

**Response** (200 OK):
```json
{
  "status": "healthy",
  "timestamp": "2025-12-16T10:00:00Z",
  "services": {
    "database": {
      "name": "PostgreSQL",
      "status": "healthy",
      "response_time_ms": 5,
      "details": {
        "version": "15.4",
        "connections": {
          "active": 10,
          "max": 100
        }
      }
    },
    "cache": {
      "name": "Redis",
      "status": "healthy",
      "response_time_ms": 2,
      "details": {
        "version": "7.2",
        "memory_used_mb": 128,
        "memory_max_mb": 512
      }
    },
    "storage": {
      "name": "MinIO",
      "status": "healthy",
      "response_time_ms": 15,
      "details": {
        "buckets": 3,
        "total_size_gb": 25
      }
    },
    "policy_engine": {
      "name": "OPA",
      "status": "healthy",
      "response_time_ms": 8,
      "details": {
        "policies_loaded": 45
      }
    }
  },
  "metrics": {
    "cpu_usage_percent": 35,
    "memory_usage_percent": 60,
    "disk_usage_percent": 45,
    "uptime_seconds": 2592000
  }
}
```

**Status Values**:
- `healthy`: All systems operational
- `degraded`: Some non-critical issues
- `unhealthy`: Critical issues detected

---

### 2.5 System Settings

#### GET /api/v1/admin/settings

Get all system settings.

**Request**:
```http
GET /api/v1/admin/settings
Authorization: Bearer <admin_token>
```

**Response** (200 OK):
```json
{
  "security": {
    "session_timeout_minutes": {
      "value": 30,
      "default": 30,
      "min": 5,
      "max": 480,
      "description": "Session timeout in minutes"
    },
    "max_login_attempts": {
      "value": 5,
      "default": 5,
      "min": 3,
      "max": 10,
      "description": "Max failed login attempts before lockout"
    }
  },
  "limits": {
    "max_projects_per_user": {
      "value": 50,
      "default": 50,
      "min": 1,
      "max": 500,
      "description": "Maximum projects per user"
    },
    "max_file_size_mb": {
      "value": 100,
      "default": 100,
      "min": 1,
      "max": 500,
      "description": "Maximum file upload size"
    }
  },
  "notifications": {
    "email_enabled": {
      "value": true,
      "default": true,
      "description": "Enable email notifications"
    },
    "webhook_url": {
      "value": "",
      "default": "",
      "description": "Webhook URL for notifications"
    }
  }
}
```

---

#### PATCH /api/v1/admin/settings

Update system settings.

**Request**:
```http
PATCH /api/v1/admin/settings
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "security.session_timeout_minutes": 60,
  "limits.max_projects_per_user": 100
}
```

**Response** (200 OK):
```json
{
  "updated": [
    "security.session_timeout_minutes",
    "limits.max_projects_per_user"
  ],
  "timestamp": "2025-12-16T10:00:00Z"
}
```

**Side Effects**:
- Creates audit log for each setting changed

---

## 3. Data Models

### 3.1 AuditLog Table (New)

```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    action VARCHAR(100) NOT NULL,
    actor_id UUID REFERENCES users(id),
    target_type VARCHAR(50),
    target_id UUID,
    target_name VARCHAR(255),
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp DESC);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_actor ON audit_logs(actor_id);
CREATE INDEX idx_audit_logs_target ON audit_logs(target_type, target_id);
```

### 3.2 SystemSettings Table (New)

```sql
CREATE TABLE system_settings (
    key VARCHAR(100) PRIMARY KEY,
    value JSONB NOT NULL,
    version INT NOT NULL DEFAULT 1,  -- CTO Condition: Version for rollback capability
    previous_value JSONB,            -- Store previous value for rollback
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_by UUID REFERENCES users(id)
);

-- Initial seed data
INSERT INTO system_settings (key, value, version) VALUES
('security.session_timeout_minutes', '30', 1),
('security.max_login_attempts', '5', 1),
('limits.max_projects_per_user', '50', 1),
('limits.max_file_size_mb', '100', 1),
('notifications.email_enabled', 'true', 1),
('notifications.webhook_url', '""', 1);
```

**Version Field Usage** (CTO Requirement):
- On update: `version = version + 1`, `previous_value = old_value`
- Enables rollback to previous setting value
- Audit trail of all setting changes

---

## 4. Security Considerations

### 4.1 Authorization Middleware

```python
async def require_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )
    return current_user
```

### 4.2 Rate Limiting

| Endpoint | Limit |
|----------|-------|
| GET endpoints | 100/minute |
| PATCH/DELETE (single) | 30/minute |
| DELETE /users/bulk | 5/minute (CTO condition) |
| Settings update | 10/minute |

### 4.3 Audit Logging

All write operations MUST create audit log entry:

```python
async def create_audit_log(
    db: Session,
    action: str,
    actor: User,
    target_type: str = None,
    target_id: UUID = None,
    target_name: str = None,
    details: dict = None,
    request: Request = None
):
    log = AuditLog(
        action=action,
        actor_id=actor.id,
        target_type=target_type,
        target_id=target_id,
        target_name=target_name,
        details=details,
        ip_address=request.client.host if request else None,
        user_agent=request.headers.get("user-agent") if request else None
    )
    db.add(log)
    db.commit()
```

---

## 5. Implementation Notes

### 5.1 File Structure (Implemented)

```
backend/app/
├── api/routes/
│   └── admin.py              # ✅ 1,350+ lines - 13 endpoints (Sprint 105)
├── schemas/
│   └── admin.py              # ✅ 511 lines - All admin schemas
├── services/
│   └── audit_service.py      # ✅ Enhanced for admin actions
├── models/
│   ├── audit_log.py          # ✅ AuditLog model
│   ├── support.py            # ✅ SystemSetting model
│   └── user.py               # ✅ Added deleted_at, deleted_by
└── alembic/versions/
    ├── m8h9i0j1k2l3_admin_panel_tables.py  # Sprint 37
    └── n9i0j1k2l3m4_add_user_soft_delete.py # Sprint 40
```

### 5.2 Migrations Applied

```bash
# Sprint 37: Admin Panel tables
alembic upgrade m8h9i0j1k2l3

# Sprint 40: User soft delete
alembic upgrade n9i0j1k2l3m4
```

### 5.3 Frontend Implementation

```
frontend/web/src/
├── api/
│   └── admin.ts              # ✅ 362 lines - React Query hooks
├── pages/admin/
│   ├── AdminDashboardPage.tsx   # ✅ 382 lines
│   ├── UserManagementPage.tsx   # ✅ 468 lines (with CRUD)
│   ├── AuditLogsPage.tsx        # ✅ 363 lines
│   ├── SystemSettingsPage.tsx   # ✅ 422 lines
│   └── SystemHealthPage.tsx     # ✅ 330 lines
├── components/ui/
│   ├── toast.tsx             # ✅ Sprint 39 - Toast component
│   └── toaster.tsx           # ✅ Sprint 39 - Toaster container
└── hooks/
    └── useToast.ts           # ✅ Sprint 39 - Toast hook
```

---

## 6. Approval

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Backend Lead | | Dec 16, 2025 | ✅ |
| Security Lead | | Dec 17, 2025 | ✅ |
| Frontend Lead | | Dec 17, 2025 | ✅ |
| **CTO** | | Dec 16-17, 2025 | **✅ APPROVED** |

---

## 7. Test Coverage

| Test Suite | Tests | Status |
|------------|-------|--------|
| admin-access-control.spec.ts | 18 | ✅ PASS |
| admin-users.spec.ts | 18 | ✅ PASS |
| admin-users-crud.spec.ts | 23 | ✅ PASS |
| admin-audit-logs.spec.ts | 20 | ✅ PASS |
| admin-settings.spec.ts | 22 | ✅ PASS |
| admin-health.spec.ts | 25 | ✅ PASS |
| admin-toast-notifications.spec.ts | 12 | ✅ PASS |
| **Total (Sprint 40 Part 1-2)** | **138** | **✅ PASS** |

### Sprint 40 Part 3: Bulk Delete Tests (PLANNED)

| Test Case | Status |
|-----------|--------|
| Bulk delete 3 users successfully | 📋 PLANNED |
| Self-delete prevention | 📋 PLANNED |
| Last superuser protection | 📋 PLANNED |
| Partial failure handling | 📋 PLANNED |
| Cancel bulk delete flow | 📋 PLANNED |
| Empty selection edge case | 📋 PLANNED |
| Batch size limit (>50 users) | 📋 PLANNED |
| **Total New Tests** | **7** |

### Sprint 105: Show Deleted Users + Permanent Delete Tests

| Test Case | Status |
|-----------|--------|
| List users with include_deleted=true | ✅ PASS |
| List users with include_deleted=false (default) | ✅ PASS |
| Restore soft-deleted user | ✅ PASS |
| Restore non-deleted user (error) | ✅ PASS |
| Permanent delete soft-deleted user | ✅ PASS |
| Permanent delete active user (error) | ✅ PASS |
| Permanent delete self (error) | ✅ PASS |
| Permanent delete non-existent user (error) | ✅ PASS |
| FK constraint handling (65+ constraints) | ✅ PASS |
| Audit logs rules recreation (SOC 2) | ✅ PASS |
| Frontend: Show Deleted toggle | ✅ PASS |
| Frontend: Restore button for deleted users | ✅ PASS |
| Frontend: Permanent Delete confirmation dialog | ✅ PASS |
| **Total Sprint 105 Tests** | **13** |

---

**Document Status**: ✅ IMPLEMENTED - Sprint 105 (Show Deleted Users + Permanent Delete)
