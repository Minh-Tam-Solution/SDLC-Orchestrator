# Sprint 86: ADR-027 Phase 1 - System Settings Implementation

**Sprint ID:** S86
**Sprint**: Sprint 86 (Originally: Feb 12-22, 2026)
**Epic**: ADR-027 Phase 1 - System Settings Real Implementation (Security)
**Priority**: 🔴 P0 - Critical (Framework Integrity)
**Owner**: BE Lead
**Status**: ✅ **COMPLETED AHEAD OF SCHEDULE** (January 20, 2026)

---

## ✅ Implementation Verification (January 20, 2026)

**All 4 Phase 1 Security Settings: FULLY IMPLEMENTED**

| Setting | Status | Implementation |
|---------|--------|----------------|
| `session_timeout_minutes` | ✅ DONE | SettingsService + Redis caching (5-min TTL) |
| `max_login_attempts` | ✅ DONE | User model fields + lockout logic (30-min lock) |
| `mfa_required` | ✅ DONE | User model fields + 7-day grace period |
| `password_min_length` | ✅ DONE | SettingsService + validation (8-128 range) |

**Key Implementation Files:**

| File | Purpose | Lines |
|------|---------|-------|
| `backend/app/services/settings_service.py` | Core service with Redis caching | 765 |
| `backend/app/models/support.py` | SystemSetting model with JSONB | ~70 |
| `backend/app/models/user.py` | Lockout + MFA fields | +15 |
| `sb5212d71967_add_login_lockout_fields.py` | Migration: failed_login_count, locked_until | ~50 |
| `sb5313e82078_add_mfa_enforcement_fields.py` | Migration: mfa_setup_deadline, is_mfa_exempt | ~50 |

**Test Coverage:**

| Test File | Tests | Status |
|-----------|-------|--------|
| `test_settings_service.py` | 30 tests | ✅ PASS |
| `test_max_login_attempts.py` | 11 tests | ✅ PASS |
| `test_password_min_length.py` | 10 tests | ✅ PASS |
| **Total** | **40+ tests** | ✅ **95%+ coverage** |

**Performance Metrics:**

| Operation | Target | Achieved |
|-----------|--------|----------|
| Cache hit (Redis) | <5ms | ✅ <5ms |
| Cache miss (DB query) | <50ms | ✅ ~30-40ms |
| Settings load (all 8) | <100ms | ✅ <80ms |

**Zero Mock Policy:** ✅ Real PostgreSQL + Redis integration

---

## 📋 Epic Overview (Original Plan)

**Problem**: All 8 system settings are mock - violates SDLC 6.1.0 Zero Mock Policy

**Solution**: Phase 1 fixes 4 critical security settings first (6-week phased approach)

**Phase 1 Scope**:
- `session_timeout_minutes` - JWT token expiry
- `max_login_attempts` - Account lockout
- `mfa_required` - MFA enforcement
- `password_min_length` - Password validation

**Total Effort**: 40 hours (30h implementation + 10h testing/buffer)

---

## 🎫 Implementation Tickets (8 Total)

### Epic Ticket

```yaml
ID: SDLC-ADR027-EPIC
Title: ADR-027 Phase 1 - System Settings Real Implementation
Type: Epic
Priority: P0 - Critical
Labels:
  - security
  - framework-integrity
  - zero-mock-fix
  - adr-027
Sprint: Sprint 86 (Feb 12 - Feb 22, 2026)
Owner: BE Lead
Estimate: 40 hours

Description:
Fix Zero Mock Policy violation - make 4 security settings functional.

Current State:
- Settings exist in database but have NO effect on code
- Admin changes settings → nothing happens
- Violates SDLC 6.1.0 framework that we enforce on others

Phase 1 Target:
- ✅ session_timeout_minutes → controls JWT expiry
- ✅ max_login_attempts → enables account lockout
- ✅ mfa_required → enforces MFA setup
- ✅ password_min_length → validates password strength

Success Criteria:
- [ ] Admin changes setting → code behavior changes within 5 minutes
- [ ] All 4 settings cached in Redis (5-min TTL)
- [ ] 100% test coverage for SettingsService
- [ ] Zero backward compatibility breaks
- [ ] Deployed to staging by Feb 7

References:
- ADR-027-System-Settings-Real-Implementation.md
- ADR-027-CTO-DECISION-MATRIX.md (CTO signed Jan 14)
- ADR-027-IMPLEMENTATION-READINESS-AUDIT.md

Acceptance:
- [ ] CTO demo on Feb 7 (Sprint N+1 review)
- [ ] All child tickets DONE
- [ ] Production-ready (staging green)
```

---

## 🏗️ Foundation Ticket (Prerequisite)

### SDLC-ADR027-000: Create SettingsService

```yaml
ID: SDLC-ADR027-000
Title: [ADR-027][Foundation] Create SettingsService with Redis caching
Type: Task
Priority: P0
Estimate: 2 hours
Assignee: BE Lead
Dependencies: None
Sprint: Sprint 86 (Feb 12 - Feb 22, 2026)

Description:
Create SettingsService to read system settings from database with Redis caching.

Acceptance Criteria:
- [ ] SettingsService reads from system_settings table
- [ ] Redis caching (5-minute TTL)
- [ ] Fallback to defaults if setting not found
- [ ] Cache invalidation method (for admin updates)
- [ ] Typed accessors for all Phase 1 settings
- [ ] Unit tests: 100% coverage

Implementation:
File: backend/app/services/settings_service.py

class SettingsService:
    async def get(key: str, default: Any) -> Any
    async def get_session_timeout_minutes() -> int
    async def get_max_login_attempts() -> int
    async def is_mfa_required() -> bool
    async def get_password_min_length() -> int
    async def invalidate_cache(key: Optional[str]) -> None

Test Cases:
1. Setting exists in DB → return DB value
2. Setting missing → return default
3. Cache hit → no DB query (<5ms)
4. Cache miss → DB query + cache store (<50ms)
5. Cache invalidation works

Files Created:
- backend/app/services/settings_service.py (new file)

Files Modified:
- backend/app/services/__init__.py (add export)

DOD (Definition of Done):
- [ ] Code written and self-reviewed
- [ ] Unit tests pass (pytest)
- [ ] Code review approved (2+ reviewers)
- [ ] Merged to main
- [ ] Deployed to staging
```

---

## 1️⃣ session_timeout_minutes (4 hours)

### SDLC-ADR027-101: Implementation

```yaml
ID: SDLC-ADR027-101
Title: [ADR-027][Phase1] session_timeout_minutes - Implementation
Type: Story
Priority: P0
Estimate: 3 hours
Assignee: BE Lead
Dependencies: SDLC-ADR027-000 (SettingsService)
Sprint: Sprint N+1
Labels: security, jwt, session-management

Description:
Replace hardcoded ACCESS_TOKEN_EXPIRE_HOURS env var with dynamic DB setting.

Current Behavior:
- Token expiry hardcoded: settings.ACCESS_TOKEN_EXPIRE_HOURS (1 hour)
- File: backend/app/core/security.py:130

Target Behavior:
- Token expiry reads from DB: settings_service.get_session_timeout_minutes()
- Admin changes timeout → new tokens use new duration within 5 min

Acceptance Criteria:
- [ ] security.py:create_access_token() uses SettingsService
- [ ] Fallback to 30 minutes if setting not found
- [ ] Setting cached (5-min TTL, <5ms cache hit)
- [ ] Admin change propagates within 5 minutes (cache expiry)
- [ ] Backward compatible (env var still works as fallback)

Implementation Plan:
1. Import SettingsService in security.py
2. Modify create_access_token():
   - Check if settings_service provided (optional param)
   - If yes: timeout = await settings_service.get_session_timeout_minutes()
   - If no: timeout = settings.ACCESS_TOKEN_EXPIRE_HOURS * 60 (fallback)
3. Update all callers (auth.py, github.py, etc.) to pass settings_service
4. Add unit tests (5 test cases)

Files Modified:
- backend/app/core/security.py (line 98-140: create_access_token)
- backend/app/api/routes/auth.py (pass settings_service)
- backend/app/api/routes/github.py (pass settings_service)

Test Cases:
1. Setting=15 → token expires at 15 minutes
2. Setting=60 → token expires at 60 minutes
3. Setting not in DB → fallback to 30 minutes
4. Cache hit → no DB query
5. Admin changes setting → next token uses new value after cache expiry

DOD:
- [ ] Code complete and self-reviewed
- [ ] Unit tests pass (5 test cases)
- [ ] Integration test: Admin changes timeout → verify new tokens
- [ ] Code review approved (2+ reviewers)
- [ ] Merged to main
- [ ] Deployed to staging
- [ ] Manual smoke test in staging

Migration Notes:
- Backward compatible - no DB migration needed
- Env var fallback for 2 sprints (deprecation period)
```

### SDLC-ADR027-102: Testing

```yaml
ID: SDLC-ADR027-102
Title: [ADR-027][Phase1] session_timeout_minutes - Testing
Type: Task
Priority: P0
Estimate: 1 hour
Assignee: QA / BE Developer #2
Dependencies: SDLC-ADR027-101
Sprint: Sprint N+1
Labels: testing, qa

Description:
Comprehensive testing for session_timeout_minutes setting.

Test Coverage:
- Unit tests: Token expiry calculation
- Integration tests: End-to-end setting change flow
- Manual E2E: Admin UI workflow

Tasks:
- [ ] Unit tests: SettingsService.get_session_timeout_minutes()
- [ ] Unit tests: Token expiry calculation in create_access_token()
- [ ] Integration test: Admin changes timeout → new tokens use new value
- [ ] Manual E2E: Login → Admin changes timeout → Login again → Verify
- [ ] Performance test: Cache hit <5ms, cache miss <50ms

Test Scenarios:
1. Happy path: Set timeout=45 → verify tokens expire at 45 min
2. Edge case: Set timeout=0 → should use default (30 min)
3. Edge case: Set timeout=9999 → should cap at reasonable max (e.g., 1440 min = 24h)
4. Cache test: Read setting twice → second read from cache (no DB query)
5. Invalidation test: Change setting → cache cleared → next read from DB

Acceptance:
- [ ] 100% test coverage for modified code
- [ ] All tests pass (green in CI/CD)
- [ ] Manual E2E documented with screenshots
- [ ] Performance verified (<5ms cache hit)

DOD:
- [ ] All test cases written and passing
- [ ] Test coverage report reviewed
- [ ] Manual testing checklist completed
- [ ] QA sign-off
```

---

## 2️⃣ max_login_attempts (12 hours) - MOST COMPLEX

### SDLC-ADR027-201: Implementation

```yaml
ID: SDLC-ADR027-201
Title: [ADR-027][Phase1] max_login_attempts - Implementation
Type: Story
Priority: P0
Estimate: 10 hours
Assignee: BE Lead
Dependencies: SDLC-ADR027-000 (SettingsService)
Sprint: Sprint N+1
Labels: security, authentication, account-lockout

Description:
Implement account lockout after N failed login attempts (currently infinite attempts allowed).

Current Behavior:
- Users can attempt login infinite times
- Only audit log recorded (no enforcement)

Target Behavior:
- Track failed login attempts per user
- Lock account after max_login_attempts exceeded
- Auto-unlock after 30 minutes
- Admin can manually unlock accounts

Acceptance Criteria:
- [ ] DB migration: Add failed_login_count, locked_until to users table
- [ ] Track failed attempts in auth.py:login() endpoint
- [ ] Lock account when failed_login_count >= max_login_attempts
- [ ] Return 403 Forbidden for locked accounts with unlock time
- [ ] Admin unlock endpoint: POST /api/v1/admin/users/{id}/unlock
- [ ] Auto-unlock after 30 minutes (locked_until < now)
- [ ] Reset counter on successful login
- [ ] Email notification on account lock (optional)

Implementation Plan:
1. Create DB migration (add 2 columns to users table)
2. Update User model (add failed_login_count, locked_until fields)
3. Modify login endpoint:
   - Check if account locked (locked_until > now)
   - On failed login: increment failed_login_count
   - If count >= max_login_attempts: set locked_until = now + 30 min
   - On success: reset failed_login_count = 0
4. Create unlock endpoint (admin only)
5. Add audit logging (account locked/unlocked events)
6. Add unit tests (10 test cases)

Files Created:
- alembic/versions/XXXXXX_add_login_lockout_fields.py (migration)
- backend/app/api/routes/admin.py (unlock endpoint - or separate file)

Files Modified:
- backend/app/models/user.py (add 2 fields)
- backend/app/api/routes/auth.py (line 245-270: login logic)
- backend/app/schemas/auth.py (add lockout error response)
- backend/app/services/audit_service.py (add ACCOUNT_LOCKED action)

Database Migration:
```sql
-- File: alembic/versions/XXXXXX_add_login_lockout_fields.py
ALTER TABLE users
  ADD COLUMN failed_login_count INTEGER DEFAULT 0 NOT NULL,
  ADD COLUMN locked_until TIMESTAMP NULL;

CREATE INDEX idx_users_locked_until ON users(locked_until);
```

Test Cases:
1. Fail login N times → account locked (HTTP 403)
2. Fail N-1 times → still can login
3. Locked account → 403 with unlock time in response
4. Locked account after 30 min → auto-unlocked
5. Admin unlocks account → user can login immediately
6. Successful login → reset failed_login_count = 0
7. Superuser exempt from lockout (always can login)
8. Setting changed from 5 to 3 → existing users respect new limit
9. Concurrent login attempts (race condition test)
10. Unlock endpoint: only admins can call

Error Response Format:
```json
{
  "detail": "Account locked due to too many failed login attempts",
  "locked_until": "2026-01-14T15:30:00Z",
  "unlock_in_minutes": 28
}
```

DOD:
- [ ] Migration tested (up/down/rollback)
- [ ] Code complete and self-reviewed
- [ ] Unit tests pass (10 test cases)
- [ ] Integration tests pass
- [ ] Code review approved (2+ reviewers)
- [ ] Merged to main
- [ ] Deployed to staging
- [ ] Manual smoke test in staging

Security Notes:
- Superusers (is_superuser=true) exempt from lockout (emergency access)
- Lockout duration: 30 minutes (not configurable in Phase 1)
- Email notification: Optional (can be Phase 2 enhancement)
```

### SDLC-ADR027-202: Testing

```yaml
ID: SDLC-ADR027-202
Title: [ADR-027][Phase1] max_login_attempts - Testing
Type: Task
Priority: P0
Estimate: 2 hours
Assignee: QA
Dependencies: SDLC-ADR027-201
Sprint: Sprint N+1
Labels: testing, qa, security-critical

Description:
Comprehensive testing for account lockout feature (most critical security feature).

Test Coverage:
- Unit tests: Lockout logic and auto-unlock
- Integration tests: Full login → lockout → unlock flow
- Load tests: Concurrent failed logins (race conditions)
- Manual E2E: Admin workflow

Tasks:
- [ ] Unit tests: Lockout logic in auth.py
- [ ] Unit tests: Auto-unlock calculation
- [ ] Unit tests: Admin unlock endpoint
- [ ] Integration test: Lock → unlock → login flow
- [ ] Load test: 100 concurrent failed logins (verify no race conditions)
- [ ] Manual E2E: Fail login 5 times → verify locked
- [ ] Manual E2E: Admin unlocks account → verify unlocked
- [ ] Manual E2E: Wait 30 min → verify auto-unlock
- [ ] Security test: Non-admin cannot call unlock endpoint

Test Scenarios:
1. Standard lockout: Fail 5 times → locked for 30 min
2. Unlock before timeout: Admin unlocks → user can login
3. Auto-unlock: Wait 30 min → user can login again
4. Counter reset: Fail 4 times → success → fail 4 times (no lock)
5. Superuser exempt: Superuser fails 100 times → never locked
6. Setting change: Change from 5 to 3 → next user respects new limit
7. Concurrent failures: 10 threads fail login simultaneously → counter correct
8. Edge case: locked_until in past → treated as unlocked
9. Edge case: User locked, password reset → still locked (separate flows)
10. API security: Non-admin calls unlock → 403 Forbidden

Edge Cases to Test:
- User locked, then deleted → should be handled gracefully
- Admin changes max_attempts while user is mid-lockout → existing lockout remains
- User locked, admin changes to is_superuser=true → should unlock automatically?
- Database locked_until is NULL vs 0 vs past date → all handled correctly

Performance Test:
- 1000 failed login attempts/sec → lockout counter accurate (no race conditions)
- Verify database index on locked_until improves query speed

Acceptance:
- [ ] 100% test coverage for lockout logic
- [ ] All tests pass (unit + integration + load)
- [ ] Manual E2E documented with video/screenshots
- [ ] Security audit: No bypasses found
- [ ] QA sign-off + Security Lead sign-off

DOD:
- [ ] All test cases written and passing
- [ ] Load test results documented
- [ ] Security checklist completed
- [ ] Manual testing video recorded
- [ ] QA + Security Lead approval
```

---

## 3️⃣ password_min_length (6 hours)

### SDLC-ADR027-301: Implementation

```yaml
ID: SDLC-ADR027-301
Title: [ADR-027][Phase1] password_min_length - Implementation
Type: Story
Priority: P0
Estimate: 4 hours
Assignee: BE Developer #2
Dependencies: SDLC-ADR027-000 (SettingsService)
Sprint: Sprint N+1
Labels: security, password-policy, validation

Description:
Make password length validation dynamic based on DB setting (currently hardcoded to 12).

Current Behavior:
- Password min length hardcoded: min_length=12 in Pydantic schema
- Files: backend/app/schemas/admin.py:161, 215

Target Behavior:
- Password min length reads from DB: settings_service.get_password_min_length()
- Admin changes min length → new users see new requirement immediately

Acceptance Criteria:
- [ ] UserCreate schema validates password length dynamically
- [ ] UserUpdate (password change) uses same validation
- [ ] Error message includes min length: "Password must be at least {N} characters"
- [ ] Setting cached (avoid DB hit on every validation)
- [ ] Admin change → next validation uses new value after cache expiry (5 min)
- [ ] Backward compatible (defaults to 12 if setting missing)

Implementation Plan:
1. Create app-level settings cache in main.py:
   - On startup: Load password_min_length from DB
   - Background task: Refresh every 5 minutes
2. Update Pydantic schemas:
   - Remove hardcoded min_length=12
   - Add custom validator that reads from app.state.password_min_length
3. Add error handling (fallback to 12 if cache unavailable)
4. Unit tests (6 test cases)

Files Modified:
- backend/app/main.py (add startup event + background task)
- backend/app/schemas/admin.py (AdminUserCreate, AdminUserUpdate)
- backend/app/schemas/auth.py (UserCreate - if exists)
- backend/app/api/routes/admin.py (update setting → invalidate cache)

Implementation Detail:
```python
# backend/app/main.py
@app.on_event("startup")
async def load_security_settings():
    settings_svc = SettingsService(db)
    app.state.password_min_length = await settings_svc.get_password_min_length()

@app.on_event("startup")
async def start_settings_refresh_task():
    async def refresh_settings():
        while True:
            await asyncio.sleep(300)  # 5 minutes
            settings_svc = SettingsService(db)
            app.state.password_min_length = await settings_svc.get_password_min_length()
    asyncio.create_task(refresh_settings())

# backend/app/schemas/admin.py
from app.main import app  # Access app.state

class AdminUserCreate(BaseModel):
    password: str = Field(..., description="Password")

    @field_validator('password')
    def validate_password_length(cls, v):
        min_length = getattr(app.state, 'password_min_length', 12)
        if len(v) < min_length:
            raise ValueError(f"Password must be at least {min_length} characters")
        return v
```

Test Cases:
1. Set min_length=12 → password with 11 chars rejected (HTTP 422)
2. Set min_length=8 → password with 8 chars accepted
3. Set min_length=16 → password with 15 chars rejected
4. Change min_length → next validation uses new value after cache refresh
5. Cache hit → validation uses cached value (no DB query)
6. Setting missing in DB → fallback to 12 (default)

DOD:
- [ ] Code complete and self-reviewed
- [ ] Unit tests pass (6 test cases)
- [ ] Integration test: Admin changes min_length → verify
- [ ] Code review approved (2+ reviewers)
- [ ] Merged to main
- [ ] Deployed to staging
- [ ] Manual smoke test in staging
```

### SDLC-ADR027-302: Testing

```yaml
ID: SDLC-ADR027-302
Title: [ADR-027][Phase1] password_min_length - Testing
Type: Task
Priority: P0
Estimate: 2 hours
Assignee: QA
Dependencies: SDLC-ADR027-301
Sprint: Sprint N+1
Labels: testing, qa

Description:
Comprehensive testing for password_min_length validation.

Test Coverage:
- Unit tests: Password validation logic
- Integration tests: User creation with various password lengths
- Manual E2E: Admin changes setting → verify new users see new requirement

Tasks:
- [ ] Unit tests: Password validator in schemas
- [ ] Unit tests: Error messages correct
- [ ] Integration test: Create user with weak password → 422 Unprocessable Entity
- [ ] Integration test: Change password with weak password → 422
- [ ] Manual E2E: Admin changes min_length → create user → verify validation
- [ ] Manual E2E: Test error message format

Test Scenarios:
1. Happy path: Set min_length=12 → password="StrongPass123" → accepted
2. Reject: Set min_length=12 → password="short" → rejected (HTTP 422)
3. Edge case: Set min_length=1 → password="a" → accepted (minimum possible)
4. Edge case: Set min_length=128 → very long password required
5. Admin workflow: Change from 12 to 16 → next user must have 16+ chars
6. Cache refresh: Change setting → wait 5 min → verify new value active

Error Response Format:
```json
{
  "detail": [
    {
      "loc": ["body", "password"],
      "msg": "Password must be at least 12 characters",
      "type": "value_error"
    }
  ]
}
```

Acceptance:
- [ ] 100% test coverage for validation logic
- [ ] All tests pass
- [ ] Manual E2E documented
- [ ] Error messages user-friendly
- [ ] QA sign-off

DOD:
- [ ] All test cases written and passing
- [ ] Manual testing checklist completed
- [ ] QA sign-off
```

---

## 4️⃣ mfa_required (8 hours)

### SDLC-ADR027-401: Implementation

```yaml
ID: SDLC-ADR027-401
Title: [ADR-027][Phase1] mfa_required - Implementation
Type: Story
Priority: P0
Estimate: 6 hours
Assignee: BE Lead
Dependencies: SDLC-ADR027-000 (SettingsService)
Sprint: Sprint N+1
Labels: security, mfa, authentication

Description:
Enforce MFA setup when mfa_required=true (currently MFA is always optional).

Current Behavior:
- MFA is optional (users can enable/disable at will)
- Infrastructure exists: mfa_enabled, mfa_secret, backup_codes in User model

Target Behavior:
- When mfa_required=true: Users MUST set up MFA to access system
- Grace period: 7 days to set up (soft enforcement with warnings)
- After grace period: Hard block until MFA configured
- Admin can exempt specific users (is_mfa_exempt field)

Acceptance Criteria:
- [ ] Check mfa_required setting on login
- [ ] If required + user has no MFA → redirect to setup flow
- [ ] If required + user has MFA → normal 2FA flow
- [ ] Grace period: 7 days (show warning banner, don't block)
- [ ] After grace period → 403 Forbidden until MFA setup
- [ ] Admin can exempt users: is_mfa_exempt=true skips check
- [ ] Superusers automatically exempt

Implementation Plan:
1. DB migration: Add mfa_setup_deadline, is_mfa_exempt to users table
2. Create MFA enforcement middleware
3. On login:
   - Check if mfa_required setting = true
   - If user.mfa_enabled = false:
     - If mfa_setup_deadline is NULL: set deadline = now + 7 days
     - If now > mfa_setup_deadline: Return 403 + redirect to MFA setup
     - If now < mfa_setup_deadline: Allow login + warning header
   - If user.mfa_enabled = true: Normal 2FA flow
4. Add MFA setup endpoint (if not exists)
5. Admin endpoint to exempt users: PATCH /api/v1/admin/users/{id}/mfa-exempt
6. Unit tests (8 test cases)

Files Created:
- alembic/versions/XXXXXX_add_mfa_enforcement_fields.py (migration)
- backend/app/middleware/mfa_middleware.py (enforcement logic)

Files Modified:
- backend/app/models/user.py (add 2 fields)
- backend/app/api/routes/auth.py (integrate middleware)
- backend/app/api/routes/admin.py (add exempt endpoint)

Database Migration:
```sql
ALTER TABLE users
  ADD COLUMN mfa_setup_deadline TIMESTAMP NULL,
  ADD COLUMN is_mfa_exempt BOOLEAN DEFAULT FALSE;
```

Test Cases:
1. mfa_required=false → MFA optional (current behavior)
2. mfa_required=true + user has MFA → normal 2FA flow
3. mfa_required=true + no MFA + day 1-7 → warning, allow access
4. mfa_required=true + no MFA + day 8+ → hard block (403)
5. Exempted user (is_mfa_exempt=true) → never required
6. Superuser → automatically exempt
7. Admin exempts user → is_mfa_exempt set to true
8. User sets up MFA → mfa_setup_deadline cleared, access granted

API Response (Grace Period):
```json
{
  "access_token": "...",
  "warnings": [
    {
      "type": "mfa_required",
      "message": "MFA will be required in 5 days. Please set up MFA.",
      "deadline": "2026-01-21T00:00:00Z"
    }
  ]
}
```

API Response (Hard Block):
```json
{
  "detail": "MFA is required. Please set up MFA to continue.",
  "mfa_setup_url": "/auth/mfa/setup",
  "status_code": 403
}
```

DOD:
- [ ] Migration tested
- [ ] Code complete and self-reviewed
- [ ] Unit tests pass (8 test cases)
- [ ] Integration tests pass
- [ ] Code review approved (2+ reviewers)
- [ ] Merged to main
- [ ] Deployed to staging
- [ ] Manual smoke test in staging

Security Notes:
- Superusers always exempt (emergency access)
- Grace period starts on first login after setting enabled
- Existing MFA users unaffected (already compliant)
```

### SDLC-ADR027-402: Testing

```yaml
ID: SDLC-ADR027-402
Title: [ADR-027][Phase1] mfa_required - Testing
Type: Task
Priority: P0
Estimate: 2 hours
Assignee: QA
Dependencies: SDLC-ADR027-401
Sprint: Sprint N+1
Labels: testing, qa, security-critical

Description:
Comprehensive testing for MFA enforcement feature.

Test Coverage:
- Unit tests: MFA enforcement logic and grace period
- Integration tests: All enforcement scenarios
- Manual E2E: Admin enables MFA requirement → verify user experience

Tasks:
- [ ] Unit tests: MFA enforcement middleware
- [ ] Unit tests: Grace period calculation
- [ ] Unit tests: Exempt logic (is_mfa_exempt, is_superuser)
- [ ] Integration test: 5 enforcement scenarios (see below)
- [ ] Manual E2E: Admin enables mfa_required → verify warning banner
- [ ] Manual E2E: Admin exempts user → verify exemption works
- [ ] Manual E2E: Wait 7 days → verify hard block

Test Scenarios:
1. MFA optional: mfa_required=false → users not prompted
2. MFA with existing setup: mfa_required=true + user has MFA → normal flow
3. Grace period: mfa_required=true + no MFA + day 1-7 → warning
4. Hard block: mfa_required=true + no MFA + day 8+ → 403 Forbidden
5. Exempted user: is_mfa_exempt=true → never required MFA
6. Superuser: is_superuser=true → automatically exempt
7. Admin exempts: Admin calls exempt endpoint → user.is_mfa_exempt=true
8. User completes setup: User sets up MFA → access granted immediately

Grace Period Testing:
- Day 1: Enabled → warning shown, access granted
- Day 3: Warning shown, access granted
- Day 7: Last day warning, access granted
- Day 8: Hard block, 403 Forbidden
- Day 10: Still blocked

Edge Cases:
- MFA required enabled globally, then disabled → users not blocked
- User has MFA, admin requires MFA, user disables MFA → blocked?
- User exempt, admin removes exemption → grace period starts fresh?

Acceptance:
- [ ] 100% test coverage for enforcement logic
- [ ] All test scenarios pass
- [ ] Manual E2E documented with screenshots
- [ ] Security audit: No bypasses found
- [ ] QA + Security Lead sign-off

DOD:
- [ ] All test cases written and passing
- [ ] Manual testing checklist completed
- [ ] Security checklist completed
- [ ] QA + Security Lead approval
```

---

## 📊 Sprint N+1 Schedule (Detailed)

### Week 1: Jan 27-31 (Foundation + First 2 Settings)

**Monday Jan 27**:
- Morning: Sprint kickoff + design review (1h)
- BE Lead: SDLC-ADR027-000 (SettingsService foundation) - 2h
- BE Lead: SDLC-ADR027-101 (session_timeout implementation) - 3h
- Afternoon: Code review + tests

**Tuesday Jan 28**:
- QA: SDLC-ADR027-102 (session_timeout testing) - 1h
- BE Lead: Start SDLC-ADR027-201 (max_login_attempts - DB migration) - 4h
- Evening: Deploy session_timeout to staging

**Wednesday Jan 29**:
- BE Lead: SDLC-ADR027-201 continued (lockout logic) - 4h
- Mid-sprint checkpoint #1 (30 min): Demo session_timeout working

**Thursday Jan 30**:
- BE Lead: SDLC-ADR027-201 continued (unlock endpoint) - 2h
- BE Lead: Code review + refactor

**Friday Jan 31**:
- BE Lead: Finish SDLC-ADR027-201 (final polish) - 2h
- QA: Start SDLC-ADR027-202 (max_login_attempts testing) - 1h

### Week 2: Feb 3-7 (Final 2 Settings + Integration)

**Monday Feb 3**:
- QA: SDLC-ADR027-202 continued (lockout testing) - 1h
- BE Dev #2: SDLC-ADR027-301 (password_min_length) - 4h

**Tuesday Feb 4**:
- QA: SDLC-ADR027-302 (password_min_length testing) - 2h
- BE Lead: SDLC-ADR027-401 (mfa_required implementation) - 4h

**Wednesday Feb 5**:
- BE Lead: SDLC-ADR027-401 continued - 2h
- Mid-sprint checkpoint #2 (30 min): Demo all 4 settings working
- QA: SDLC-ADR027-402 (mfa_required testing) - 1h

**Thursday Feb 6**:
- QA: SDLC-ADR027-402 continued - 1h
- Team: Integration testing (all 4 settings together) - 4h
- Team: Bug fixes from integration tests - 2h

**Friday Feb 7**:
- Morning: Deploy to staging - 1h
- Morning: Final smoke tests in staging - 1h
- Afternoon: Sprint review + CTO demo - 1h
- Afternoon: Retrospective - 30 min

---

## 🎯 Success Criteria (Sprint Exit)

### Functional
- [ ] Admin changes `session_timeout_minutes` → new tokens use new duration
- [ ] Admin sets `max_login_attempts=3` → accounts lock after 3 failures
- [ ] Admin enables `mfa_required` → non-MFA users see setup prompt
- [ ] Admin sets `password_min_length=16` → signup rejects weak passwords
- [ ] All settings cached in Redis (5-min TTL verified)
- [ ] Settings changes take effect within 5 minutes

### Quality
- [ ] 100% unit test coverage for SettingsService
- [ ] 95%+ test coverage for all 4 settings
- [ ] Zero P0/P1 bugs in staging
- [ ] Code review approval from 2+ reviewers per ticket
- [ ] Security audit pass (no bypasses found)

### Performance
- [ ] Cache hit: <5ms (Redis)
- [ ] Cache miss: <50ms (PostgreSQL query)
- [ ] No regression: API p95 remains <100ms
- [ ] Load test: 1000 req/s sustained

### Documentation
- [ ] ADR-027 marked as IMPLEMENTED
- [ ] API docs updated (Swagger/OpenAPI)
- [ ] Admin guide: How to use each setting
- [ ] Migration guide: Env vars deprecation plan

---

## 🚨 Risk Management

### Risk 1: Account Lockout Locks Out Admins
**Mitigation**: Superusers exempt from lockout (hardcoded)

### Risk 2: MFA Requirement Locks Out All Users
**Mitigation**: 7-day grace period + admin exemption

### Risk 3: Performance Regression
**Mitigation**: Redis caching + load testing before deploy

### Risk 4: Breaking Existing Deployments
**Mitigation**: Backward compatible (env vars fallback) + 2-sprint deprecation

---

## 📝 Post-Sprint Actions

**After Sprint N+1 (Feb 10+)**:
- [ ] Monitor production for 1 week (Feb 10-14)
- [ ] Collect metrics (settings change frequency, lockout events, etc.)
- [ ] Retrospective: What went well? What to improve for Phase 2?
- [ ] Plan Phase 2 (3 resource limit settings)
- [ ] Draft ADR-028 (API key management) - mid-February

---

## ✅ Ticket Checklist (Before Sprint Start)

- [ ] All 8 tickets created in project management tool
- [ ] Tickets linked to Epic: SDLC-ADR027-EPIC
- [ ] Tickets assigned to owners
- [ ] Tickets added to Sprint N+1 board
- [ ] Sprint N+1 kickoff scheduled (Jan 27, 9:00 AM)
- [ ] Design review scheduled (Jan 27, 10:00 AM)
- [ ] Checkpoint meetings scheduled (Jan 29, Feb 5)
- [ ] CTO demo scheduled (Feb 7, 2:00 PM)
- [ ] Team capacity confirmed (BE Lead 50%, BE Dev #2 30%, QA 20%)

---

**Status**: ✅ Ready for Sprint N+1 execution (Jan 27 kickoff)

**Next Action**: Create tickets in Jira/Linear/GitHub Issues using templates above
