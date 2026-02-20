# ADR-027: System Settings Real Implementation (Zero Mock Violation Fix)

**Status**: 🟡 PROPOSED (Awaiting CTO Approval)  
**Date**: 2026-01-14  
**Priority**: 🔴 **P0 - CRITICAL** (Framework Integrity Violation)  
**Impact**: Security, Compliance, Framework Credibility

---

## Context

### Problem Statement

**Critical Discovery**: All 8 system settings in Admin Panel are **MOCK implementations** that violate SDLC 6.1.0 Zero Mock Policy:

| Setting | Current State | Impact |
|---------|---------------|--------|
| `session_timeout_minutes` | ❌ MOCK | Auth uses hardcoded `ACCESS_TOKEN_EXPIRE_HOURS` env var |
| `max_login_attempts` | ❌ MOCK | No account lockout logic exists |
| `max_projects_per_user` | ❌ MOCK | No project creation validation |
| `max_file_size_mb` | ❌ MOCK | No file upload size check |
| `ai_council_enabled` | ❌ MOCK | AICouncilService ignores this flag |
| `mfa_required` | ❌ MOCK | MFA always optional, never enforced |
| `password_min_length` | ❌ MOCK | No password validation logic |
| `evidence_retention_days` | ❌ MOCK | No auto-archive/cleanup |

**Severity**: 
- **Framework Integrity**: SDLC Orchestrator (tool enforcing SDLC) violates its own Zero Mock Policy
- **Security Risk**: Admin believes they can enforce security policies, but changes have no effect
- **Compliance Risk**: Settings appear to control behavior but don't - audit trail is misleading
- **Credibility Risk**: Cannot enforce SDLC 6.1.0 on teams while violating it ourselves

### Why This Happened

Settings were implemented as:
1. **Database layer**: CRUD operations work (store/retrieve values)
2. **Admin UI**: Users can view/edit settings successfully
3. **Business logic**: **NOT CONNECTED** - services use hardcoded/env values

This is a classic "UI-first, logic-later" anti-pattern that violates our own principles.

---

## Decision

### Guiding Principles

1. **Framework Integrity First**: SDLC Orchestrator MUST comply with SDLC 6.1.0
2. **Zero Mock Policy**: No setting can exist without real enforcement
3. **Security by Default**: Auth/security settings are P0
4. **Phased Approach**: Fix critical settings immediately, plan others systematically

### Proposed Solution

Implement settings in **3 phases** based on security impact and complexity:

---

## Implementation Roadmap

### **Phase 1: Critical Security Settings (Week 1-2)** 🔴 P0

**Target**: Auth & access control (cannot ship without these)

| Setting | Implementation | Complexity | Timeline |
|---------|---------------|------------|----------|
| `session_timeout_minutes` | Replace `ACCESS_TOKEN_EXPIRE_HOURS` with DB setting | LOW | 2 days |
| `max_login_attempts` | Add account lockout middleware + unlock endpoint | MEDIUM | 3 days |
| `mfa_required` | Enforce MFA check in login flow when flag=true | MEDIUM | 3 days |
| `password_min_length` | Add validation in user create/update endpoints | LOW | 1 day |

**Acceptance Criteria**:
- ✅ Admin changes session timeout → tokens expire at new duration
- ✅ Admin enables MFA required → all users must configure MFA
- ✅ Admin sets max login attempts → accounts lock after N failures
- ✅ Admin sets password min length → create user validates length

**Testing**:
- Unit tests for each setting's enforcement logic
- Integration tests for setting changes propagating
- Manual E2E test: change setting → verify behavior changes

---

### **Phase 2: Resource Limits (Week 3-4)** 🟡 P1

**Target**: Platform resource management

| Setting | Implementation | Complexity | Timeline |
|---------|---------------|------------|----------|
| `max_projects_per_user` | Check in project creation endpoint | LOW | 2 days |
| `max_file_size_mb` | Add file size validation in upload middleware | LOW | 2 days |
| `ai_council_enabled` | Gate AICouncilService calls with flag check | LOW | 1 day |

**Acceptance Criteria**:
- ✅ User at project limit → 400 error with clear message
- ✅ File exceeds limit → 413 error (Payload Too Large)
- ✅ AI Council disabled → endpoints return 503 (Service Unavailable)

---

### **Phase 3: Lifecycle & Advanced (Week 5-6)** 🟢 P2

**Target**: Data lifecycle management

| Setting | Implementation | Complexity | Timeline |
|---------|---------------|------------|----------|
| `evidence_retention_days` | Background job to archive/delete old evidence | HIGH | 5 days |

**Acceptance Criteria**:
- ✅ Evidence older than N days auto-archived to cold storage
- ✅ Archived evidence retrievable via separate API
- ✅ Delete after (N + grace period) with audit log

**Complexity Drivers**:
- Requires background job scheduler (Celery/APScheduler)
- S3/cold storage integration
- Audit trail for deletions
- Rollback mechanism if archive fails

---

## Technical Design

### 1. Settings Service (Singleton Pattern)

```python
# backend/app/services/settings_service.py
from functools import lru_cache
from app.db.session import get_db
from app.models.settings import SystemSetting

class SettingsService:
    """
    Centralized settings service with caching.
    All business logic MUST read settings via this service.
    """
    
    @lru_cache(maxsize=128)
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get setting value with cache (5-min TTL)."""
        db = next(get_db())
        setting = db.query(SystemSetting).filter_by(key=key).first()
        return setting.value if setting else default
    
    def invalidate_cache(self):
        """Clear cache when settings updated via admin."""
        self.get_setting.cache_clear()

# Global instance
settings_service = SettingsService()
```

### 2. Auth Integration Example

```python
# backend/app/core/security.py
from app.services.settings_service import settings_service

def create_access_token(data: dict) -> str:
    # OLD: expires = timedelta(hours=settings.ACCESS_TOKEN_EXPIRE_HOURS)
    # NEW: Read from DB
    timeout_minutes = settings_service.get_setting(
        "session_timeout_minutes", 
        default=30
    )
    expires = timedelta(minutes=timeout_minutes)
    # ... rest of token creation
```

### 3. Setting Update Hook

```python
# backend/app/api/routes/settings.py
@router.put("/settings/{key}")
async def update_setting(key: str, value: Any, db: Session):
    # Update DB
    setting = db.query(SystemSetting).filter_by(key=key).first()
    setting.value = value
    db.commit()
    
    # Invalidate cache
    settings_service.invalidate_cache()
    
    # Emit event for real-time services (if needed)
    await event_bus.emit("setting.updated", key=key, value=value)
    
    return {"status": "updated", "key": key}
```

---

## Migration Strategy

### Backward Compatibility

**Problem**: Existing deployments rely on env vars like `ACCESS_TOKEN_EXPIRE_HOURS`

**Solution**: Graceful migration
1. On first startup, populate DB settings from env vars (if not exist)
2. Add deprecation warnings in logs for 2 sprints
3. Remove env var support in Q2 2026

```python
# backend/app/core/init_settings.py
def migrate_env_to_db():
    """One-time migration: env vars → DB settings."""
    if not settings_service.get_setting("session_timeout_minutes"):
        timeout_hours = os.getenv("ACCESS_TOKEN_EXPIRE_HOURS", 2)
        settings_service.set_setting(
            "session_timeout_minutes", 
            timeout_hours * 60
        )
        logger.warning(
            f"Migrated ACCESS_TOKEN_EXPIRE_HOURS to DB. "
            f"Env var deprecated - will be removed in Q2 2026."
        )
```

---

## Security Considerations

### 1. Privilege Escalation Prevention

**Risk**: User with admin access changes session timeout to 1 year → effectively permanent tokens

**Mitigation**:
- Hard limits in code (e.g., session timeout max = 7 days)
- Audit log all setting changes with user ID + timestamp
- Alert on suspicious changes (e.g., timeout > 24 hours)

### 2. Feature Flag Abuse

**Risk**: Disable MFA required → downgrade security for entire platform

**Mitigation**:
- Require approval workflow for critical security settings
- VCR (Verification & Compliance Record) for sensitive changes
- Rollback mechanism with 1-click restore

### 3. Cache Poisoning

**Risk**: If cache not invalidated, stale settings persist

**Mitigation**:
- Cache TTL = 5 minutes max
- Explicit invalidation on update
- Health check endpoint verifies cache freshness

---

## API Key Management (Separate Concern)

### Why Separate ADR Needed

API keys (OpenAI, Claude, custom AI providers) are **NOT system settings** because:
1. **Secrets Management**: Keys need encryption at rest, access control
2. **Multi-tenancy**: Different projects may use different API keys
3. **Rotation**: Keys expire, need rotation workflow
4. **Cost Tracking**: Usage tied to billing, need per-key metrics

### Recommended Approach

**Defer to separate ADR**: "ADR-028: External AI Provider Key Management"

**Placeholder**: For Phase 1, use env vars for API keys. Add proper secrets management in Q2.

---

## Testing Strategy

### Unit Tests (Per Setting)

```python
def test_session_timeout_from_db():
    # Set DB value to 15 minutes
    settings_service.set_setting("session_timeout_minutes", 15)
    
    # Create token
    token = create_access_token({"user_id": 123})
    
    # Verify expiry is 15 minutes
    payload = decode_token(token)
    assert payload["exp"] - payload["iat"] == 15 * 60
```

### Integration Tests

```python
def test_admin_changes_session_timeout():
    # Admin updates setting via API
    response = client.put("/api/v1/settings/session_timeout_minutes", json=15)
    assert response.status_code == 200
    
    # New tokens use new timeout
    login_response = client.post("/api/v1/auth/login", ...)
    token = login_response.json()["access_token"]
    # Verify token expiry = 15 min
```

### E2E Tests

Manual checklist for each Phase 1 setting:
1. Change setting via Admin UI
2. Trigger affected workflow (login, create user, etc.)
3. Verify behavior matches new setting
4. Revert setting
5. Verify behavior reverts

---

## Rollout Plan

### Sprint N: Design Approval (This Sprint)

- [ ] CTO reviews and approves ADR-027
- [ ] Prioritize Phase 1 settings order
- [ ] Assign owner (BE Lead)

### Sprint N+1: Phase 1 Implementation

**Week 1**:
- [ ] `session_timeout_minutes` + tests
- [ ] `password_min_length` + tests
- [ ] PR review + merge

**Week 2**:
- [ ] `max_login_attempts` + lockout logic + tests
- [ ] `mfa_required` + enforcement + tests
- [ ] Integration tests for all Phase 1
- [ ] Deploy to staging + manual E2E
- [ ] Production deployment

### Sprint N+2: Phase 2 Implementation

- [ ] `max_projects_per_user` + tests
- [ ] `max_file_size_mb` + tests
- [ ] `ai_council_enabled` + tests
- [ ] Deploy to production

### Sprint N+3: Phase 3 Planning

- [ ] ADR for evidence retention architecture
- [ ] Prototype background job scheduler
- [ ] Cold storage integration design

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Backward incompatibility** | HIGH | Env var migration script + 2-sprint deprecation period |
| **Cache staleness** | MEDIUM | 5-min TTL + explicit invalidation on update |
| **Performance regression** | LOW | Cached reads = O(1), 5-min refresh acceptable |
| **Security downgrade** | HIGH | Hard limits + audit logs + approval workflow |
| **Scope creep** | MEDIUM | Strict phase boundaries, defer API key mgmt to separate ADR |

---

## Success Metrics

### Phase 1 Exit Criteria

- ✅ All 4 critical settings connected to business logic
- ✅ 100% test coverage for enforcement logic
- ✅ Admin can change each setting → behavior changes immediately
- ✅ Zero Mock Policy violations = 0
- ✅ Backward compatibility maintained (env vars still work with warnings)

### Overall Success (All Phases)

- ✅ 8/8 settings fully functional (no mocks)
- ✅ SDLC Orchestrator complies with SDLC 6.1.0
- ✅ Framework credibility restored
- ✅ Security posture improved (MFA enforcement, lockout, session timeout)

---

## Alternatives Considered

### Alternative 1: Remove Mock Settings Entirely

**Pros**: Honest about current capabilities
**Cons**: 
- Breaks existing admin UI
- Loss of future extensibility
- Doesn't solve the root problem

**Verdict**: ❌ Rejected - band-aid solution

### Alternative 2: Implement All 8 Settings Immediately

**Pros**: Complete solution in one sprint
**Cons**:
- High risk (too much change at once)
- Blocks other critical work
- Evidence retention needs architecture work

**Verdict**: ❌ Rejected - too risky, violates incremental delivery

### Alternative 3: Phased Implementation (CHOSEN)

**Pros**:
- Security-first prioritization
- Manageable scope per sprint
- Early value delivery (Phase 1 = immediate security improvement)
- Low risk (incremental, well-tested)

**Verdict**: ✅ **APPROVED** (pending CTO confirmation)

---

## Open Questions

1. **Q**: Should we gate setting changes behind VCR workflow?
   **A**: For Phase 1, no (adds complexity). Add in Phase 2+ for critical settings.

2. **Q**: How to handle distributed deployments (multiple backend pods)?
   **A**: Cache TTL + invalidation via Redis pub/sub ensures 5-min consistency.

3. **Q**: What if admin sets session timeout = 0?
   **A**: Code enforces min=5 minutes, max=7 days. Validation on update.

4. **Q**: API key management timeline?
   **A**: Separate ADR (ADR-028), target Q2 2026. Use env vars until then.

---

## Decision

**PROPOSED**: Implement in 3 phases as outlined above.

**CTO Approval Required**:
- ✅ / ❌ Approve phased approach (vs all-at-once)
- ✅ / ❌ Approve Phase 1 scope (4 security settings)
- ✅ / ❌ Approve 6-week timeline (2 weeks per phase)
- ✅ / ❌ Defer API key management to separate ADR

**Next Steps After Approval**:
1. Create Sprint N+1 backlog items for Phase 1
2. Assign BE Lead as owner
3. Schedule design review with team
4. Begin implementation Week 1 of Sprint N+1

---

## References

- **SDLC 6.1.0 Zero Mock Policy**: `/SDLC-Enterprise-Framework/02-Core-Methodology/03-Quality-Standards.md`
- **Current Implementation**: `backend/app/models/settings.py`, `backend/app/api/routes/settings.py`
- **Auth Logic**: `backend/app/core/security.py`
- **Related**: ADR-028 (API Key Management - TBD)

---

**Author**: AI Assistant (GitHub Copilot)  
**Reviewer**: CTO (Pending)  
**Status**: 🟡 **AWAITING APPROVAL**
