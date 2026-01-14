# ADR-027 Phase 1 - Integration Test Plan

**Date**: January 14, 2026
**Status**: Ready for Execution
**Duration**: 2 hours
**Author**: Claude Sonnet 4.5 (AI Assistant)
**Purpose**: Verify all 4 settings work together in production-like environment

---

## 🎯 Test Objectives

1. **Cross-Setting Integration**: Verify all 4 settings work simultaneously without conflicts
2. **Cache Coherence**: Verify Redis cache invalidation works across all settings
3. **Performance**: Verify <100ms p95 API latency maintained with all enforcement active
4. **End-to-End**: Verify admin changes propagate to user-facing behavior

---

## 📋 Pre-Test Setup

### Environment Requirements
- Backend running locally or in staging
- Frontend Admin UI accessible
- PostgreSQL database with migrations applied
- Redis cache running
- Test user accounts available

### Database Migrations
```bash
cd backend
alembic upgrade head

# Verify migrations applied
alembic current
# Should show: sb5313e82078 (head)
```

### Seed Test Data
```sql
-- Create test admin
INSERT INTO users (id, email, password_hash, name, is_active, is_superuser)
VALUES (
    gen_random_uuid(),
    'admin.test@sdlc.local',
    '$2b$12$...',  -- hash for "AdminTest123!"
    'Test Admin',
    true,
    true
);

-- Create test users
INSERT INTO users (id, email, password_hash, name, is_active, is_superuser)
VALUES
    (gen_random_uuid(), 'user1@sdlc.local', '$2b$12$...', 'Test User 1', true, false),
    (gen_random_uuid(), 'user2@sdlc.local', '$2b$12$...', 'Test User 2', true, false),
    (gen_random_uuid(), 'user3@sdlc.local', '$2b$12$...', 'Test User 3', true, false);
```

---

## 🧪 Integration Test Cases

### Test Suite 1: All Settings Enabled (30 min)

#### IT-1: Baseline Configuration
**Setup**:
```sql
-- Set all 4 settings to enforced values
UPDATE system_settings SET value = 15 WHERE key = 'session_timeout_minutes';
UPDATE system_settings SET value = 3 WHERE key = 'max_login_attempts';
UPDATE system_settings SET value = 16 WHERE key = 'password_min_length';
UPDATE system_settings SET value = 'true' WHERE key = 'mfa_required';
COMMIT;

-- Invalidate Redis cache
FLUSHDB;
```

**Expected**: All settings take effect within 5 minutes (cache TTL)

---

#### IT-2: session_timeout_minutes Integration
**Test Steps**:
1. Login as user1@sdlc.local
2. Get JWT token (15-min expiry)
3. Wait 16 minutes
4. Try to access protected endpoint (GET /api/v1/projects)

**Expected**:
- ✅ Step 2: Token created with `exp` = now + 15 minutes
- ✅ Step 4: 401 Unauthorized (token expired)

**Verification**:
```bash
# Decode JWT to verify expiry
python3 -c "
import jwt
token = 'YOUR_TOKEN_HERE'
decoded = jwt.decode(token, options={'verify_signature': False})
print(f'Expires: {decoded[\"exp\"]}')
print(f'Duration: {decoded[\"exp\"] - decoded[\"iat\"]} seconds')
# Should show 900 seconds (15 minutes)
"
```

---

#### IT-3: max_login_attempts Integration
**Test Steps**:
1. Try login as user2@sdlc.local with wrong password (3 times)
2. Check database: `SELECT failed_login_count, locked_until FROM users WHERE email='user2@sdlc.local'`
3. Try login with correct password

**Expected**:
- ✅ After 3rd failure: Account locked, 403 Forbidden
- ✅ Database shows: `failed_login_count=3`, `locked_until` set to now+30min
- ✅ Correct password rejected with 403 (still locked)

**Verification**:
```sql
-- Check lockout state
SELECT
    email,
    failed_login_count,
    locked_until,
    (locked_until > NOW()) as is_locked
FROM users
WHERE email = 'user2@sdlc.local';

-- Expected:
-- failed_login_count: 3
-- locked_until: 2026-01-14 13:00:00 (30 min future)
-- is_locked: true
```

---

#### IT-4: password_min_length Integration
**Test Steps**:
1. Try register new user with 12-char password: `Password12!` (fails, need 16+)
2. Try register with 16-char password: `SecurePassword1!` (succeeds)
3. Admin tries create user with 10-char password (fails)

**Expected**:
- ✅ Step 1: 400 Bad Request, "Password must be at least 16 characters long"
- ✅ Step 2: 201 Created, user registered
- ✅ Step 3: 400 Bad Request

**Verification**:
```bash
# Test registration endpoint
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "short.pass@test.com",
    "password": "Password12!",
    "name": "Short Pass"
  }'

# Expected: {"detail": "Password must be at least 16 characters long"}
```

---

#### IT-5: mfa_required Integration
**Test Steps**:
1. Login as user3@sdlc.local (no MFA enabled)
2. Access protected endpoint (GET /api/v1/projects)
3. Check response headers for `X-MFA-Setup-Required`
4. Verify database: `SELECT mfa_setup_deadline FROM users WHERE email='user3@sdlc.local'`

**Expected**:
- ✅ Step 2: 200 OK (grace period active)
- ✅ Step 3: Header present: `X-MFA-Setup-Required: 7 days remaining`
- ✅ Step 4: `mfa_setup_deadline` set to now + 7 days

**Verification**:
```sql
-- Check MFA deadline
SELECT
    email,
    mfa_enabled,
    is_mfa_exempt,
    mfa_setup_deadline,
    EXTRACT(day FROM (mfa_setup_deadline - NOW())) as days_remaining
FROM users
WHERE email = 'user3@sdlc.local';

-- Expected:
-- mfa_enabled: false
-- is_mfa_exempt: false
-- days_remaining: ~7
```

---

### Test Suite 2: Cross-Setting Interactions (30 min)

#### IT-6: Session Timeout + Account Lockout
**Scenario**: User's session expires while account is locked

**Test Steps**:
1. Lock user2's account (3 failed logins)
2. Wait 16 minutes (session timeout)
3. Try to access API with expired token

**Expected**:
- ✅ 401 Unauthorized (token expired, not 403 for account lock)
- Lockout check happens AFTER authentication

---

#### IT-7: Password Change + MFA Requirement
**Scenario**: User changes password while MFA enforcement is active

**Test Steps**:
1. Admin updates user3's password (new password must be 16+ chars)
2. User3 logs in with new password
3. Verify MFA grace period still applies

**Expected**:
- ✅ Password validation enforces 16-char minimum
- ✅ MFA grace period persists (deadline not reset)

---

#### IT-8: Admin Exemptions + Settings Changes
**Scenario**: Admin exempts user from MFA, then changes max_login_attempts

**Test Steps**:
1. Admin exempts user3 from MFA: `POST /api/v1/admin/users/{id}/mfa-exempt`
2. User3 accesses API (no MFA warning)
3. Admin changes max_login_attempts from 3 to 5
4. User3 fails login 4 times (should NOT lock yet)

**Expected**:
- ✅ Step 2: No `X-MFA-Setup-Required` header
- ✅ Step 4: Account not locked (need 5 failures)

---

### Test Suite 3: Cache Invalidation (20 min)

#### IT-9: Setting Change Propagation
**Test Steps**:
1. Admin changes `session_timeout_minutes` from 15 to 30
2. Wait 1 minute (< cache TTL)
3. User logs in → check JWT expiry
4. Wait 5 minutes (> cache TTL)
5. User logs in again → check JWT expiry

**Expected**:
- ✅ Step 3: Token has 15-min expiry (old cached value)
- ✅ Step 5: Token has 30-min expiry (new value after cache refresh)

**Verification**:
```python
import jwt
from datetime import datetime

# Decode both tokens
token1 = "TOKEN_FROM_STEP_3"
token2 = "TOKEN_FROM_STEP_5"

decoded1 = jwt.decode(token1, options={'verify_signature': False})
decoded2 = jwt.decode(token2, options={'verify_signature': False})

duration1 = decoded1['exp'] - decoded1['iat']
duration2 = decoded2['exp'] - decoded2['iat']

print(f"Token 1 duration: {duration1 / 60} minutes")  # Should be ~15
print(f"Token 2 duration: {duration2 / 60} minutes")  # Should be ~30
```

---

#### IT-10: Multi-Setting Cache Coherence
**Test Steps**:
1. Admin changes all 4 settings simultaneously
2. Wait 6 minutes (force cache refresh)
3. Test all 4 behaviors

**Expected**:
- ✅ All 4 settings use new values after cache refresh
- ✅ No stale values, no inconsistencies

---

### Test Suite 4: Performance & Stress (20 min)

#### IT-11: Latency with All Enforcement Active
**Test Steps**:
1. Enable all 4 settings with strict values
2. Run 100 concurrent login requests
3. Measure p50, p95, p99 latencies

**Expected**:
- ✅ p95 latency < 100ms
- ✅ p99 latency < 200ms
- ✅ No timeouts, no errors

**Load Test Script**:
```python
import asyncio
import aiohttp
import time
from statistics import quantiles

async def login_request(session, email, password):
    start = time.time()
    async with session.post(
        'http://localhost:8000/api/v1/auth/login',
        json={'email': email, 'password': password}
    ) as resp:
        duration = (time.time() - start) * 1000  # ms
        return resp.status, duration

async def load_test():
    async with aiohttp.ClientSession() as session:
        tasks = [
            login_request(session, f'user{i}@test.com', 'Password123!')
            for i in range(100)
        ]
        results = await asyncio.gather(*tasks)

    durations = [d for _, d in results]
    p50, p95, p99 = quantiles(durations, n=100)

    print(f"p50: {p50:.2f}ms")
    print(f"p95: {p95:.2f}ms")
    print(f"p99: {p99:.2f}ms")

    # Assertions
    assert p95 < 100, f"p95 latency {p95}ms exceeds 100ms target"
    assert p99 < 200, f"p99 latency {p99}ms exceeds 200ms target"

asyncio.run(load_test())
```

---

#### IT-12: Cache Hit Rate
**Test Steps**:
1. Monitor Redis cache hits/misses during load test
2. Calculate hit rate

**Expected**:
- ✅ Cache hit rate > 95% (settings cached for 5 minutes)

**Verification**:
```bash
# Monitor Redis stats
redis-cli INFO stats | grep keyspace_hits
redis-cli INFO stats | grep keyspace_misses

# Calculate hit rate
hit_rate = hits / (hits + misses) * 100
# Should be > 95%
```

---

### Test Suite 5: Edge Cases (20 min)

#### IT-13: Expired Deadline + Exemption
**Test Steps**:
1. User has expired MFA deadline (locked out)
2. Admin exempts user
3. User tries to access API

**Expected**:
- ✅ Access granted immediately (exemption overrides deadline)

---

#### IT-14: Concurrent Setting Changes
**Test Steps**:
1. Admin 1 changes session_timeout to 20
2. Admin 2 changes session_timeout to 25 (1 second later)
3. Wait 6 minutes
4. Verify final value

**Expected**:
- ✅ Last write wins (value = 25)
- ✅ No race condition errors

---

#### IT-15: Database Unavailable Fallback
**Test Steps**:
1. Stop PostgreSQL
2. Try to read settings (should use cached values)
3. Try to update settings (should fail gracefully)

**Expected**:
- ✅ Read operations succeed (Redis cache fallback)
- ✅ Write operations return 503 Service Unavailable

---

## 📊 Success Criteria

| Metric | Target | Pass/Fail |
|--------|--------|-----------|
| All 4 settings functional | 100% | ☐ |
| Cross-setting interactions work | 100% | ☐ |
| Cache invalidation correct | 100% | ☐ |
| p95 API latency | <100ms | ☐ |
| Cache hit rate | >95% | ☐ |
| Edge cases handled | 100% | ☐ |
| Zero errors/crashes | 100% | ☐ |

---

## 🐛 Issue Tracking

| Test Case | Status | Issue | Resolution |
|-----------|--------|-------|------------|
| IT-1 | ☐ | | |
| IT-2 | ☐ | | |
| ... | | | |

---

## 📝 Test Report Template

```markdown
# ADR-027 Phase 1 Integration Test Report

**Date**: [DATE]
**Tester**: [NAME]
**Duration**: [TIME]
**Environment**: [staging/local]

## Summary
- Total Tests: 15
- Passed: X
- Failed: Y
- Blocked: Z

## Failed Tests
1. [Test ID]: [Description]
   - Expected: [X]
   - Actual: [Y]
   - Root Cause: [Z]
   - Fix Required: [Action]

## Performance Results
- p50 latency: Xms
- p95 latency: Yms
- p99 latency: Zms
- Cache hit rate: X%

## Recommendation
☐ Ready for CTO Demo
☐ Requires fixes before demo
```

---

**Status**: Ready for execution
**Next Step**: Run test suite and document results
