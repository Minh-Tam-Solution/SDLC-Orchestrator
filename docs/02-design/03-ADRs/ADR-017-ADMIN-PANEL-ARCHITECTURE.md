# ADR-017: Admin Panel Architecture

**Status**: APPROVED
**Date**: December 16, 2025
**Approved**: December 16, 2025 (CTO Signed)
**Deciders**: CTO + Backend Lead + Security Lead
**Framework**: SDLC 5.1.1 Complete Lifecycle
**Impact**: Medium - New administrative interface for platform management
**CTO Condition**: Version field added to system_settings for rollback capability

---

## Context

### Problem Statement

SDLC Orchestrator platform requires administrative capabilities for:
1. **User Management**: Platform admins need to manage user accounts (activate/deactivate, grant/revoke superuser status)
2. **System Monitoring**: Real-time visibility into system health and service status
3. **Audit Compliance**: SOC 2 Type II requires comprehensive audit trails of administrative actions
4. **Configuration Management**: Ability to adjust system settings without code deployment

### Current State

- `is_superuser` flag exists on User model but is not enforced on dedicated admin endpoints
- `require_superuser()` dependency exists but no admin routes use it
- No centralized audit logging for administrative actions
- System settings are hardcoded or require environment variable changes

### Business Drivers

1. **SOC 2 Compliance**: Audit requirement for user access management
2. **Operational Efficiency**: Self-service administration reduces engineering overhead
3. **Security Posture**: Centralized control over platform access
4. **Scalability**: As user base grows (target: 500+ users), manual user management is unsustainable

---

## Decision

### Architecture Overview

Implement Admin Panel as a **separate route namespace** (`/api/v1/admin`) with **dedicated authorization layer**, **comprehensive audit logging**, and **configurable system settings**.

```
┌─────────────────────────────────────────────────────────────────┐
│                     ADMIN PANEL ARCHITECTURE                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐        │
│  │  Frontend   │───▶│  API Layer  │───▶│  Services   │        │
│  │  (React)    │    │ (FastAPI)   │    │  (Python)   │        │
│  └─────────────┘    └──────┬──────┘    └──────┬──────┘        │
│                            │                   │               │
│                     ┌──────▼──────┐     ┌──────▼──────┐       │
│                     │  Auth Gate  │     │ Audit Log   │       │
│                     │ is_superuser│     │  Service    │       │
│                     └──────┬──────┘     └──────┬──────┘       │
│                            │                   │               │
│                     ┌──────▼───────────────────▼──────┐       │
│                     │        PostgreSQL               │       │
│                     │  ┌────────┐ ┌────────┐ ┌─────┐ │       │
│                     │  │ users  │ │audit_  │ │syst │ │       │
│                     │  │        │ │logs    │ │_set │ │       │
│                     │  └────────┘ └────────┘ └─────┘ │       │
│                     └─────────────────────────────────┘       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Key Design Decisions

#### 1. Authorization Model: Flag-Based (Not Role-Based)

**Decision**: Use `is_superuser` boolean flag instead of introducing new admin roles.

**Rationale**:
- Existing `is_superuser` field already exists in User model
- Binary admin/non-admin is sufficient for initial scope
- Avoids complexity of role hierarchy (Admin → SuperAdmin → etc.)
- SOC 2 compliance requires clear separation (superuser = admin access)

**Implementation**:
```python
async def require_superuser(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user
```

#### 2. Audit Logging: Append-Only Table

**Decision**: Create dedicated `audit_logs` table with append-only constraint.

**Rationale**:
- SOC 2 CC7.1 requires immutable audit trails
- Separate from application logs for compliance queries
- Enables export/retention policies without affecting performance

**Schema**:
```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    action VARCHAR(100) NOT NULL,      -- e.g., 'user.deactivated'
    actor_id UUID NOT NULL REFERENCES users(id),
    target_type VARCHAR(50),           -- e.g., 'user', 'setting'
    target_id UUID,
    details JSONB,                      -- Additional context
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Prevent updates/deletes
CREATE RULE audit_logs_no_update AS ON UPDATE TO audit_logs DO INSTEAD NOTHING;
CREATE RULE audit_logs_no_delete AS ON DELETE TO audit_logs DO INSTEAD NOTHING;
```

#### 3. System Settings: Database-Backed Configuration

**Decision**: Store configurable settings in `system_settings` table instead of environment variables.

**Rationale**:
- Runtime changes without redeployment
- Audit trail for setting changes
- Sensible defaults with override capability
- Environment variables for secrets only

**Settings Categories**:
| Category | Settings | Default |
|----------|----------|---------|
| Security | session_timeout_minutes | 30 |
| Security | max_login_attempts | 5 |
| Limits | max_projects_per_user | 50 |
| Limits | max_file_size_mb | 100 |
| Features | ai_council_enabled | true |

#### 4. Self-Action Prevention

**Decision**: Admins cannot modify their own account (deactivate, remove superuser).

**Rationale**:
- Prevents accidental self-lockout
- SOC 2 separation of duties principle
- At least one superuser must always exist

**Implementation**:
```python
if target_user_id == current_user.id:
    raise HTTPException(400, "Cannot modify own account")

superuser_count = await db.scalar(
    select(func.count()).where(User.is_superuser == True)
)
if superuser_count <= 1 and removing_superuser:
    raise HTTPException(400, "At least one superuser required")
```

#### 5. Rate Limiting Strategy

**Decision**: Aggressive rate limits on destructive operations.

| Endpoint Type | Limit | Window |
|---------------|-------|--------|
| Read (GET) | 100 | 1 minute |
| Write (PATCH) | 30 | 1 minute |
| Delete | 10 | 1 minute |
| Settings | 10 | 1 minute |

**Rationale**:
- Prevent brute force on user management
- Protect against automation abuse
- Lower limits on destructive operations

---

## Alternatives Considered

### Alternative 1: Separate Admin Service (Microservice)

**Description**: Deploy Admin Panel as standalone microservice.

**Rejected Because**:
- Adds operational complexity (another service to maintain)
- Data synchronization challenges with main database
- Overkill for current scale (< 1000 users)
- Same team maintains both services

### Alternative 2: Third-Party Admin Tool (e.g., Retool, Appsmith)

**Description**: Use low-code admin builder.

**Rejected Because**:
- Vendor lock-in
- Limited customization for SDLC-specific workflows
- Additional cost ($50-500/month)
- Security concerns with external tool accessing user data

### Alternative 3: Role-Based Access Control (RBAC) with Multiple Admin Roles

**Description**: Implement Admin → SuperAdmin → SystemAdmin hierarchy.

**Rejected Because**:
- Premature optimization for current user base
- Increases complexity without clear benefit
- Can be added later if needed
- Binary admin/non-admin sufficient for SOC 2

---

## Consequences

### Positive

1. **Compliance Ready**: Meets SOC 2 Type II requirements for access control and audit logging
2. **Self-Service**: Platform admins can manage users without engineering involvement
3. **Visibility**: Real-time system health monitoring
4. **Traceability**: Complete audit trail of all administrative actions
5. **Flexibility**: Runtime configuration changes without deployment

### Negative

1. **Development Effort**: ~2 weeks for full implementation
2. **Database Growth**: Audit logs will grow (~10KB/action, ~100MB/year at current scale)
3. **Learning Curve**: Admins need training on new interface

### Risks

| Risk | Mitigation |
|------|------------|
| Audit log table grows large | Implement partitioning + 90-day hot data policy |
| Admin account compromise | MFA required for superusers (future) |
| Accidental mass user deactivation | Confirmation dialogs + rate limiting |

---

## Implementation Plan

### Phase 1: Backend Foundation (Sprint 37, Week 1)
- [ ] Create `audit_logs` table migration
- [ ] Create `system_settings` table migration
- [ ] Implement audit service with logging middleware
- [ ] Create admin routes with `require_superuser` protection

### Phase 2: Core Features (Sprint 37, Week 2)
- [ ] User management endpoints (list, update, deactivate)
- [ ] Audit log endpoints with filtering
- [ ] System settings endpoints
- [ ] System health endpoint

### Phase 3: Frontend (Sprint 38, Week 1)
- [ ] Admin layout and navigation
- [ ] User management page
- [ ] Audit logs page
- [ ] System health dashboard
- [ ] Settings page

### Phase 4: Polish & Security (Sprint 38, Week 2)
- [ ] Rate limiting implementation
- [ ] Security testing
- [ ] Documentation
- [ ] CTO review and approval

---

## References

- [ADMIN-PANEL-REQUIREMENTS.md](../08-Admin-Panel/ADMIN-PANEL-REQUIREMENTS.md)
- [ADMIN-PANEL-API-DESIGN.md](../08-Admin-Panel/ADMIN-PANEL-API-DESIGN.md)
- [ADMIN-PANEL-UI-SPECIFICATION.md](../08-Admin-Panel/ADMIN-PANEL-UI-SPECIFICATION.md)
- [ADMIN-PANEL-SECURITY-REVIEW.md](../08-Admin-Panel/ADMIN-PANEL-SECURITY-REVIEW.md)
- [Security-Baseline.md](../06-Security-RBAC/Security-Baseline.md)
- [SOC2-TYPE-I-CONTROLS-MATRIX.md](../06-Security-RBAC/SOC2-TYPE-I-CONTROLS-MATRIX.md)

---

## Approval

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Backend Lead | | | |
| Security Lead | | | |
| **CTO** | | | **REQUIRED** |

---

**Document Status**: PROPOSED - Awaiting CTO Approval
