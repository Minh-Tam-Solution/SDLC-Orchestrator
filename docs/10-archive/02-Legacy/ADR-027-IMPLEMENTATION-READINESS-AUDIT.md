# ADR-027 Implementation Readiness Audit

**Date**: 2026-01-14
**Status**: ✅ Complete - Ready for implementation
**Auditor**: AI Assistant (Claude)
**Purpose**: Pre-implementation audit to identify integration points and effort estimates

---

## Executive Summary

**Audit Result**: ✅ **GREEN - Ready to proceed**

All 4 Phase 1 settings have clear integration points. No blockers found. Estimated effort: **40 hours** (aligns with ADR-027 estimate).

---

## Phase 1: Security Settings Audit

### 1️⃣ `session_timeout_minutes` (DB → Code Integration)

**Current State**:
- ✅ Token creation: `backend/app/core/security.py:130`
  ```python
  expire = datetime.utcnow() + timedelta(hours=settings.ACCESS_TOKEN_EXPIRE_HOURS)
  ```
- ✅ Uses env var: `ACCESS_TOKEN_EXPIRE_HOURS` from `config.py`
- ❌ Does NOT read from database

**Integration Point**:
```python
# File: backend/app/core/security.py
# Line: 98-140 (create_access_token function)

# BEFORE (current):
expire = datetime.utcnow() + timedelta(hours=settings.ACCESS_TOKEN_EXPIRE_HOURS)

# AFTER (Phase 1):
timeout_minutes = await settings_service.get_session_timeout_minutes()
expire = datetime.utcnow() + timedelta(minutes=timeout_minutes)
```

**Effort**: 4 hours
- 2h: Modify `create_access_token` to accept optional `settings_service`
- 1h: Update all callers (auth.py, github.py)
- 1h: Unit tests (5 test cases)

**Risk**: LOW - Backward compatible (defaults to env var if DB unavailable)

---

### 2️⃣ `max_login_attempts` (Account Lockout - NEW FEATURE)

**Current State**:
- ✅ Audit log exists: `USER_LOGIN_FAILED` action logged
- ❌ No lockout logic (users can attempt infinite times)
- ❌ No `failed_login_count` or `locked_until` columns in User table

**Integration Point**:
```python
# File: backend/app/api/routes/auth.py
# Line: 245-270 (login endpoint)

# NEW LOGIC NEEDED:
1. Check if account is locked (locked_until > now)
2. On failed login: increment failed_login_count
3. If failed_login_count >= max_login_attempts:
   - Set locked_until = now + 30 minutes
   - Log lockout event
4. On successful login: reset failed_login_count = 0
```

**Database Migration Required**:
```sql
ALTER TABLE users ADD COLUMN failed_login_count INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN locked_until TIMESTAMP NULL;
CREATE INDEX idx_users_locked_until ON users(locked_until);
```

**Effort**: 12 hours
- 4h: Database migration + model update
- 4h: Lockout middleware logic
- 2h: Integration with login endpoint
- 2h: Unit + integration tests (10 test cases)

**Risk**: MEDIUM - New feature, needs careful testing (don't lock out admins accidentally)

**Industry Best Practices**:
- Lockout duration: 15-30 minutes (recommend 30 min)
- Max attempts: 3-10 (recommend 5, matches seed data)
- Unlock methods: Time-based auto-unlock + admin manual unlock
- Notification: Email user when account locked (optional Phase 2)

---

### 3️⃣ `mfa_required` (MFA Enforcement - EXISTING FEATURE)

**Current State**:
- ✅ MFA infrastructure exists: User model has `mfa_enabled`, `mfa_secret`, `backup_codes`
- ✅ MFA is optional (users can enable/disable)
- ❌ No enforcement (users can skip MFA even if admin requires it)

**Integration Point**:
```python
# File: backend/app/api/dependencies.py (or new middleware)
# Create: require_mfa_if_enabled() dependency

# NEW LOGIC:
1. Check system setting: mfa_required = true/false
2. If mfa_required = true:
   - Check user.mfa_enabled
   - If user.mfa_enabled = false:
     → Return 403 Forbidden + redirect to MFA setup page
   - If user.mfa_enabled = true:
     → Proceed normally
3. If mfa_required = false:
   - Proceed normally (MFA optional)
```

**Effort**: 8 hours
- 3h: MFA enforcement middleware
- 2h: Integration with protected endpoints (add dependency)
- 2h: Frontend: MFA setup flow + error handling
- 1h: Unit tests (8 test cases)

**Risk**: LOW - Infrastructure exists, just add enforcement layer

**Grace Period**: Recommend 7-day grace period when enabling MFA requirement:
- Day 1: Admin enables `mfa_required`
- Day 1-7: Users see warning banner "MFA required in X days"
- Day 8+: Enforcement begins (403 if MFA not set up)

---

### 4️⃣ `password_min_length` (Password Validation - PARTIAL)

**Current State**:
- ✅ Pydantic validation exists: `min_length=12` hardcoded
  - `backend/app/schemas/admin.py:161` (AdminUserCreate)
  - `backend/app/schemas/admin.py:215` (AdminUserUpdate)
- ❌ No validation in regular user signup (`backend/app/schemas/auth.py:121` - only `min_length=1`)
- ❌ Hardcoded value (not reading from DB)

**Integration Point**:
```python
# File: backend/app/schemas/admin.py + auth.py
# Use Pydantic validator instead of Field min_length

# BEFORE (hardcoded):
password: str = Field(..., min_length=12, description="Password")

# AFTER (dynamic):
password: str = Field(..., description="Password")

@field_validator('password')
def validate_password_length(cls, v, values, **kwargs):
    # Read min_length from settings (async context needed)
    # OR: Use dependency injection in endpoint
    min_length = get_password_min_length_sync()  # Helper function
    if len(v) < min_length:
        raise ValueError(f"Password must be at least {min_length} characters")
    return v
```

**Caveat**: Pydantic validators are synchronous, but DB query is async.

**Solution**: Pre-load setting in FastAPI app startup, store in global cache:
```python
# backend/app/main.py
@app.on_event("startup")
async def load_security_settings():
    app.state.password_min_length = await settings_service.get_password_min_length()
    # Refresh every 5 minutes via background task
```

**Effort**: 6 hours
- 2h: App-level settings cache + refresh task
- 2h: Update Pydantic validators (admin.py, auth.py)
- 1h: Add password validation in user signup endpoint
- 1h: Unit tests (6 test cases)

**Risk**: LOW - Backward compatible (defaults to 12 if DB unavailable)

---

## Phase 1 Total Effort Breakdown

| Setting | Effort | Risk | Dependencies |
|---------|--------|------|--------------|
| session_timeout_minutes | 4h | LOW | None |
| max_login_attempts | 12h | MEDIUM | DB migration |
| mfa_required | 8h | LOW | Existing MFA infra |
| password_min_length | 6h | LOW | App startup cache |
| **TOTAL** | **30h** | **LOW-MEDIUM** | 1 migration |

**Buffer**: +10 hours (testing, code review, bug fixes)
**Final Estimate**: **40 hours** ✅ (matches ADR-027)

---

## Phase 1 Implementation Order (Recommended)

### Week 1 (Sprint N+1, Days 1-5)
**Day 1-2**: `session_timeout_minutes` (4h, LOW risk)
- Quickest win, builds confidence
- Tests SettingsService integration pattern

**Day 3-5**: `max_login_attempts` (12h, MEDIUM risk)
- Most complex (DB migration + new feature)
- Do early to allow testing time

### Week 2 (Sprint N+1, Days 6-10)
**Day 6-7**: `password_min_length` (6h, LOW risk)
- Medium complexity, app-level cache pattern

**Day 8-9**: `mfa_required` (8h, LOW risk)
- Uses existing MFA infra, straightforward

**Day 10**: Buffer + E2E testing (10h)
- Integration tests across all 4 settings
- Manual testing scenarios
- Bug fixes

---

## Blockers & Dependencies

### Database Migration
**Blocker**: Phase 1 requires 1 migration for `max_login_attempts`

**Migration File**: (to be created)
```
backend/alembic/versions/
└── XXXXXX_add_login_lockout_fields.py
    - Add users.failed_login_count (integer, default 0)
    - Add users.locked_until (timestamp, nullable)
    - Create index on locked_until (performance)
```

**Rollback Plan**: Migration is backward compatible (adds columns with defaults)

### SettingsService Dependency
**All 4 settings need**: SettingsService to read from database

**Solution**: Create `SettingsService` first (Day 1 morning, 2h)
- Already designed in ADR-027 (full spec available)
- Redis caching (5-min TTL)
- Fallback to env vars if DB unavailable

---

## Testing Strategy (Per Setting)

### Unit Tests (Individual Setting)
- ✅ Setting exists in DB → code reads correct value
- ✅ Setting missing in DB → code uses default value
- ✅ Setting updated in DB → code reflects change after cache expiry
- ✅ Redis cache hit → fast response (<5ms)
- ✅ Redis cache miss → DB query + cache update

### Integration Tests (Setting + Feature)
- ✅ `session_timeout`: Token expires after N minutes
- ✅ `max_login_attempts`: Account locks after N failures
- ✅ `mfa_required`: Users blocked until MFA set up
- ✅ `password_min_length`: Signup rejects short passwords

### E2E Tests (Admin Panel)
- ✅ Admin changes setting → setting takes effect within 5 minutes
- ✅ Admin enables lockout → user gets locked after failures
- ✅ Admin requires MFA → non-MFA users blocked

---

## Risk Mitigation

### Risk 1: Breaking Existing Deployments
**Probability**: LOW
**Mitigation**:
- Env vars remain as fallback (backward compatible)
- 2-sprint deprecation period (Sprint N+1, N+2)
- Clear migration guide in CHANGELOG

### Risk 2: Account Lockout Logic Locks Out Admins
**Probability**: MEDIUM
**Impact**: HIGH (admin can't unlock themselves)
**Mitigation**:
- Superusers exempt from lockout (hardcoded)
- Admin panel: "Unlock User" button
- Redis manual unlock via CLI (emergency)

### Risk 3: MFA Enforcement Locks Out All Users
**Probability**: LOW
**Impact**: HIGH (no one can log in)
**Mitigation**:
- 7-day grace period (warning banner)
- Superusers can disable `mfa_required` via Admin Panel
- Emergency override via environment variable

### Risk 4: Performance Regression (DB Query Every Token)
**Probability**: LOW
**Mitigation**:
- Redis cache (5-min TTL)
- Cache hit: <5ms overhead
- Load test: 1000 req/s (verify <100ms p95)

---

## Acceptance Criteria (Phase 1 Complete)

### Functional Requirements
- [ ] Admin changes `session_timeout_minutes` → new tokens use new duration
- [ ] Admin sets `max_login_attempts=3` → account locks after 3 failures
- [ ] Admin enables `mfa_required` → non-MFA users see setup prompt
- [ ] Admin sets `password_min_length=16` → signup validates 16+ chars
- [ ] All settings cached in Redis (5-min TTL)
- [ ] Settings update takes effect within 5 minutes (cache expiry)

### Non-Functional Requirements
- [ ] 100% unit test coverage for SettingsService
- [ ] 90% integration test coverage for 4 settings
- [ ] E2E test: Admin workflow (change setting → verify effect)
- [ ] Performance: <5ms cache hit, <50ms cache miss
- [ ] Security: Superusers exempt from lockout
- [ ] Audit: All setting changes logged

### Documentation
- [ ] ADR-027 marked as IMPLEMENTED
- [ ] API docs updated (settings affect token expiry, etc.)
- [ ] Admin guide: How to configure each setting
- [ ] Migration guide: Env vars → database settings

---

## Next Steps (After CTO Approval)

1. **Create Implementation Tickets** (8 stories)
   - SDLC-XXX: Create SettingsService (2h)
   - SDLC-XXX: Integrate session_timeout_minutes (4h)
   - SDLC-XXX: DB migration for login lockout (4h)
   - SDLC-XXX: Implement max_login_attempts logic (8h)
   - SDLC-XXX: Implement mfa_required enforcement (8h)
   - SDLC-XXX: Implement password_min_length validation (6h)
   - SDLC-XXX: Integration tests for Phase 1 (6h)
   - SDLC-XXX: E2E tests + documentation (2h)

2. **Assign Ownership**
   - DRI: BE Lead
   - Support: 1 BE developer (testing)

3. **Schedule Kickoff** (Sprint N+1 Day 1)
   - Design review: 30 min
   - Ticket walkthrough: 30 min
   - Q&A: 15 min

---

## Conclusion

✅ **READY TO PROCEED**

All 4 Phase 1 settings have:
- Clear integration points identified
- Implementation approach defined
- Effort estimated (40h total)
- Risks mitigated
- Testing strategy planned

**Blocker Status**: NONE
**Recommendation**: Approve ADR-027 and begin Sprint N+1 planning.

---

**Auditor Notes**:
- This audit was performed pre-implementation to identify integration complexity
- All code references verified against actual codebase (Jan 14, 2026)
- Effort estimates based on similar features in Sprint 40-44 history
- No Mock Policy violations found in existing auth code (good foundation)

**Confidence Level**: HIGH ✅
