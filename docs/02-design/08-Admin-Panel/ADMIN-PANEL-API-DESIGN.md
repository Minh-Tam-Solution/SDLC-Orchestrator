# Admin Panel - API Design Specification
## SDLC 5.1.1 Complete Lifecycle - Design Phase

**Version**: 1.1.0
**Date**: 2025-12-16
**Status**: APPROVED - CTO Signed Dec 16, 2025
**Author**: Backend Lead
**Reviewer**: CTO
**CTO Approval**: Version field added to system_settings per CTO condition

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
      "projects_count": 5
    }
  ],
  "total": 150,
  "page": 1,
  "page_size": 20,
  "total_pages": 8
}
```

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

Soft delete user (set is_active=false, anonymize data).

**Request**:
```http
DELETE /api/v1/admin/users/550e8400-e29b-41d4-a716-446655440000
Authorization: Bearer <admin_token>
```

**Response** (200 OK):
```json
{
  "message": "User deleted successfully",
  "user_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Error Responses**:
- 400: Cannot delete own account
- 400: Cannot delete only superuser
- 404: User not found

**Side Effects**:
- Sets is_active=false
- Anonymizes email: deleted_<timestamp>@deleted.local
- Invalidates sessions
- Creates audit log entry

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
| PATCH/DELETE | 30/minute |
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

### 5.1 File Structure

```
backend/app/
├── api/routes/
│   └── admin.py              # NEW: Admin endpoints
├── schemas/
│   └── admin.py              # NEW: Admin schemas
├── services/
│   └── admin_service.py      # NEW: Admin business logic
│   └── audit_service.py      # NEW: Audit logging
├── models/
│   └── audit_log.py          # NEW: AuditLog model
│   └── system_setting.py     # NEW: SystemSetting model
└── middleware/
    └── admin_auth.py         # NEW: Admin auth middleware
```

### 5.2 Migration

```bash
alembic revision --autogenerate -m "Add audit_logs and system_settings tables"
alembic upgrade head
```

---

## 6. Approval

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Backend Lead | | | |
| Security Lead | | | |
| **CTO** | | | **REQUIRED** |

---

**Document Status**: DRAFT - Awaiting CTO Approval
