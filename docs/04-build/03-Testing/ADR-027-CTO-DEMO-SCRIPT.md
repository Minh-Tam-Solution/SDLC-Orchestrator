# ADR-027 Phase 1 - CTO Demo Script

**Date**: January 14, 2026
**Duration**: 2 hours
**Presenter**: Backend Lead / AI Assistant
**Audience**: CTO + CPO + Backend Team
**Purpose**: Demonstrate 100% Phase 1 completion with Zero Mock Policy proof

---

## 🎯 Demo Objectives

1. **Prove All 4 Settings Functional**: Show each setting affects real behavior (not mocked)
2. **Demonstrate Zero Mock Policy**: Settings read from database, changes propagate without restart
3. **Show Admin Control**: CTO can manage all settings via Admin UI
4. **Performance Validation**: System maintains <100ms p95 latency with all enforcement active
5. **Security Showcase**: All 4 settings enhance security posture (OWASP ASVS L2)

---

## 📋 Pre-Demo Setup (15 min before demo)

### Environment Preparation
```bash
# 1. Start all services
cd /home/nqh/shared/SDLC-Orchestrator
docker-compose up -d postgres redis minio

cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

cd ../frontend/landing
npm run dev
```

### Database Setup
```sql
-- Reset test data
DELETE FROM users WHERE email LIKE '%demo.sdlc%';

-- Create demo users
INSERT INTO users (id, email, password_hash, name, is_active, is_superuser)
VALUES
    (gen_random_uuid(), 'cto@demo.sdlc', '$2b$12$...', 'CTO Demo Admin', true, true),
    (gen_random_uuid(), 'alice@demo.sdlc', '$2b$12$...', 'Alice Developer', true, false),
    (gen_random_uuid(), 'bob@demo.sdlc', '$2b$12$...', 'Bob QA Engineer', true, false);

-- Set initial settings (default values)
INSERT INTO system_settings (key, value, category, description, version)
VALUES
    ('session_timeout_minutes', 60, 'security', 'JWT session timeout', 1),
    ('max_login_attempts', 5, 'security', 'Max failed login attempts', 1),
    ('password_min_length', 12, 'security', 'Minimum password length', 1),
    ('mfa_required', false, 'security', 'MFA enforcement flag', 1)
ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value;

-- Clear Redis cache
redis-cli FLUSHDB
```

### Browser Setup
- Tab 1: Admin UI (http://localhost:3000/admin/settings)
- Tab 2: Postman/Insomnia (for API testing)
- Tab 3: Database GUI (DBeaver/TablePlus) showing `system_settings` table
- Tab 4: Redis Commander (http://localhost:8081) showing cache

---

## 🎬 Demo Script

### Part 1: Introduction (5 min)

**Talking Points**:
> "Today I'm demonstrating ADR-027 Phase 1 completion - all 4 dynamic system settings implemented with Zero Mock Policy compliance. This means every setting you see reads from the database and affects real behavior, with no hardcoded values or placeholders."

**Show**:
1. Open Admin Settings UI
2. Show all 4 settings visible with current values
3. Show database table with same values (prove it's reading from DB)

**Key Message**: "What you see in the UI is what's stored in the database. No mocks, no fakes."

---

### Part 2: session_timeout_minutes Demo (15 min)

#### Demo 2A: Default Behavior (60 min timeout)

**Script**:
> "First, let's demonstrate session timeout. Currently set to 60 minutes - the industry standard. Let me login as Alice and show you the JWT token."

**Steps**:
1. Login as alice@demo.sdlc via Postman
   ```json
   POST http://localhost:8000/api/v1/auth/login
   {
     "email": "alice@demo.sdlc",
     "password": "AlicePassword123!"
   }
   ```

2. Copy JWT token from response

3. Decode JWT at https://jwt.io
   - Show `iat` (issued at) timestamp
   - Show `exp` (expires) timestamp
   - **Calculate**: `exp - iat = 3600 seconds = 60 minutes`

**Proof**: "See? The token expires in exactly 60 minutes, matching our database setting."

---

#### Demo 2B: Change Setting Live (5 min timeout)

**Script**:
> "Now let's change this to 5 minutes and see the effect immediately - no restart required."

**Steps**:
1. In Admin UI, change `session_timeout_minutes` to `5`
2. Click "Save Changes"
3. Show database update in real-time:
   ```sql
   SELECT key, value, updated_at
   FROM system_settings
   WHERE key = 'session_timeout_minutes';
   -- Shows: value=5, updated_at=NOW()
   ```

4. Wait 30 seconds (to exceed cache TTL in demo mode, or manually flush cache):
   ```bash
   redis-cli DEL settings:session_timeout_minutes
   ```

5. Login as alice@demo.sdlc again (new token)

6. Decode new JWT token
   - **Calculate**: `exp - iat = 300 seconds = 5 minutes`

**Proof**: "Token now expires in 5 minutes. Setting change propagated without any restart."

---

#### Demo 2C: Token Expiry Test

**Script**:
> "Let's prove this token actually expires after 5 minutes."

**Steps**:
1. Use the 5-minute token to access API:
   ```
   GET http://localhost:8000/api/v1/projects
   Authorization: Bearer <token>
   ```
   - **Result**: 200 OK (token valid)

2. Fast-forward time (manually edit JWT exp claim to past):
   ```python
   # Decode token
   import jwt
   token = "..."
   decoded = jwt.decode(token, options={'verify_signature': False})

   # Set exp to past
   decoded['exp'] = int(time.time()) - 10  # 10 seconds ago

   # Re-encode (for demo only - real tokens can't be forged)
   # In real demo, just wait 5 minutes
   ```

3. Access API with expired token:
   ```
   GET http://localhost:8000/api/v1/projects
   Authorization: Bearer <expired_token>
   ```
   - **Result**: 401 Unauthorized, "Token has expired"

**Proof**: "Token expiry is enforced. Users must re-login after timeout."

---

### Part 3: max_login_attempts Demo (20 min)

#### Demo 3A: Account Lockout

**Script**:
> "Next, account lockout protection. Currently set to 5 failed attempts. Let's change it to 3 for faster demo, then try to brute-force Bob's account."

**Steps**:
1. In Admin UI, change `max_login_attempts` to `3`
2. Show database update

3. Attempt login as bob@demo.sdlc with wrong password (3 times):
   ```json
   POST http://localhost:8000/api/v1/auth/login
   {
     "email": "bob@demo.sdlc",
     "password": "WrongPassword123!"
   }
   ```
   - Attempt 1: 401 Unauthorized (counter = 1)
   - Attempt 2: 401 Unauthorized (counter = 2)
   - Attempt 3: **403 Forbidden** - "Account locked due to 3 failed login attempts. Try again after 30 minutes."

4. Show database state:
   ```sql
   SELECT email, failed_login_count, locked_until
   FROM users
   WHERE email = 'bob@demo.sdlc';
   -- Shows: failed_login_count=3, locked_until=(NOW() + 30 minutes)
   ```

**Proof**: "Account locked for 30 minutes after 3 failures. This protects against brute-force attacks."

---

#### Demo 3B: Admin Unlock

**Script**:
> "If Bob contacts support, an admin can manually unlock his account immediately."

**Steps**:
1. In Admin UI (or Postman), call admin unlock endpoint:
   ```
   POST http://localhost:8000/api/v1/admin/users/{bob_id}/unlock
   Authorization: Bearer <cto_token>
   ```

2. Show response:
   ```json
   {
     "message": "User account unlocked successfully",
     "email": "bob@demo.sdlc",
     "failed_login_count": 0,
     "locked_until": null
   }
   ```

3. Bob can now login with correct password:
   ```json
   POST http://localhost:8000/api/v1/auth/login
   {
     "email": "bob@demo.sdlc",
     "password": "BobPassword123!"
   }
   ```
   - **Result**: 200 OK, token issued

**Proof**: "Admin override works. Support team can help locked-out users."

---

### Part 4: password_min_length Demo (15 min)

#### Demo 4A: Registration with Weak Password

**Script**:
> "Now password strength enforcement. Currently 12 characters minimum. Let's increase to 16 and try to register a new user."

**Steps**:
1. In Admin UI, change `password_min_length` to `16`
2. Show database update

3. Try register with 12-char password:
   ```json
   POST http://localhost:8000/api/v1/auth/register
   {
     "email": "charlie@demo.sdlc",
     "password": "Password123!",  // 12 chars
     "name": "Charlie New User"
   }
   ```
   - **Result**: 400 Bad Request, "Password must be at least 16 characters long"

**Proof**: "Weak password rejected. User must meet minimum length."

---

#### Demo 4B: Registration with Strong Password

**Script**:
> "Let's try with a 16+ character password."

**Steps**:
1. Register with 20-char password:
   ```json
   POST http://localhost:8000/api/v1/auth/register
   {
     "email": "charlie@demo.sdlc",
     "password": "VerySecurePassword123!",  // 22 chars
     "name": "Charlie New User"
   }
   ```
   - **Result**: 201 Created, user registered

2. Show user in database:
   ```sql
   SELECT email, name, created_at
   FROM users
   WHERE email = 'charlie@demo.sdlc';
   ```

**Proof**: "Strong password accepted. System enforces configurable password policy."

---

#### Demo 4C: Admin Password Reset

**Script**:
> "This also applies to admin password resets. If CTO resets a user's password, it must meet the 16-character minimum."

**Steps**:
1. Admin tries to reset Charlie's password to weak value:
   ```
   PUT http://localhost:8000/api/v1/admin/users/{charlie_id}
   {
     "new_password": "Short123!"  // 9 chars
   }
   ```
   - **Result**: 400 Bad Request, "Password must be at least 16 characters long"

**Proof**: "Even admins can't bypass password policy. Consistent enforcement across all entry points."

---

### Part 5: mfa_required Demo (30 min)

#### Demo 5A: MFA Enforcement Disabled (Baseline)

**Script**:
> "Finally, MFA enforcement. Currently disabled - users can login without MFA. Let's enable it and see the grace period in action."

**Steps**:
1. Show current setting: `mfa_required = false`
2. Alice logs in without MFA:
   ```
   POST http://localhost:8000/api/v1/auth/login
   {
     "email": "alice@demo.sdlc",
     "password": "AlicePassword123!"
   }
   ```
   - **Result**: 200 OK, token issued
   - **No warnings** (MFA not required)

---

#### Demo 5B: Enable MFA Requirement

**Script**:
> "Now let's enable MFA enforcement and see what happens."

**Steps**:
1. In Admin UI, change `mfa_required` to `true`
2. Show database update

3. Alice logs in again:
   ```
   POST http://localhost:8000/api/v1/auth/login
   {...}
   ```
   - **Result**: 200 OK (grace period starts)

4. Alice accesses protected endpoint:
   ```
   GET http://localhost:8000/api/v1/projects
   Authorization: Bearer <alice_token>
   ```
   - **Result**: 200 OK
   - **Headers**:
     ```
     X-MFA-Setup-Required: 7 days remaining
     X-MFA-Setup-Deadline: 2026-01-21T12:34:56Z
     ```

5. Show database state:
   ```sql
   SELECT email, mfa_enabled, mfa_setup_deadline
   FROM users
   WHERE email = 'alice@demo.sdlc';
   -- Shows: mfa_enabled=false, mfa_setup_deadline=(NOW() + 7 days)
   ```

**Proof**: "Alice gets 7-day grace period to set up MFA. System is user-friendly while enforcing security."

---

#### Demo 5C: Deadline Expired (Block Access)

**Script**:
> "Let's simulate what happens after 7 days if Alice hasn't set up MFA."

**Steps**:
1. Manually set deadline to past:
   ```sql
   UPDATE users
   SET mfa_setup_deadline = NOW() - INTERVAL '1 hour'
   WHERE email = 'alice@demo.sdlc';
   ```

2. Alice tries to access API:
   ```
   GET http://localhost:8000/api/v1/projects
   Authorization: Bearer <alice_token>
   ```
   - **Result**: 403 Forbidden
   - **Message**: "MFA setup is required. Your 7-day grace period expired on 2026-01-14 11:34:56 UTC. Please contact an administrator for assistance."

**Proof**: "After deadline, access is blocked. User must set up MFA or get admin exemption."

---

#### Demo 5D: Admin Exemption

**Script**:
> "If Alice is a service account or has a legitimate reason, admin can exempt her from MFA requirement."

**Steps**:
1. Admin exempts Alice:
   ```
   POST http://localhost:8000/api/v1/admin/users/{alice_id}/mfa-exempt
   {
     "exempt": true
   }
   ```

2. Alice accesses API:
   ```
   GET http://localhost:8000/api/v1/projects
   Authorization: Bearer <alice_token>
   ```
   - **Result**: 200 OK (access granted)
   - **No MFA warning header**

3. Show database state:
   ```sql
   SELECT email, is_mfa_exempt, mfa_setup_deadline
   FROM users
   WHERE email = 'alice@demo.sdlc';
   -- Shows: is_mfa_exempt=true, mfa_setup_deadline=NULL
   ```

**Proof**: "Admin override works. Service accounts and special cases can be exempted."

---

#### Demo 5E: View MFA Status

**Script**:
> "Admin can view any user's MFA status at a glance."

**Steps**:
1. Admin checks Bob's status:
   ```
   GET http://localhost:8000/api/v1/admin/users/{bob_id}/mfa-status
   Authorization: Bearer <cto_token>
   ```

2. Response:
   ```json
   {
     "user_id": "...",
     "email": "bob@demo.sdlc",
     "mfa_enabled": false,
     "is_mfa_exempt": false,
     "mfa_required_global": true,
     "mfa_setup_deadline": "2026-01-21T12:34:56Z",
     "days_remaining": 7,
     "enforcement_status": "grace_period"
   }
   ```

**Proof**: "Admin dashboard shows MFA compliance status for all users."

---

### Part 6: Zero Mock Policy Proof (15 min)

**Script**:
> "Now the critical part - proving Zero Mock Policy compliance. Every setting you've seen affects real behavior and reads from the database."

#### Proof 1: Database is Source of Truth

**Steps**:
1. Show `system_settings` table in database:
   ```sql
   SELECT key, value, updated_at
   FROM system_settings
   WHERE category = 'security'
   ORDER BY key;
   ```

2. Show Admin UI settings panel (same values)

3. Change a setting in database directly:
   ```sql
   UPDATE system_settings
   SET value = 10
   WHERE key = 'session_timeout_minutes';
   ```

4. Wait 5 minutes (or flush cache)

5. Login → verify JWT has 10-min expiry

**Proof**: "Database change propagates to behavior. No hardcoded values in code."

---

#### Proof 2: Code Inspection

**Script**:
> "Let me show you the actual code that reads these settings."

**Steps**:
1. Open `backend/app/services/settings_service.py` in IDE
2. Show `get_session_timeout_minutes()` method:
   ```python
   async def get_session_timeout_minutes(self) -> int:
       value = await self.get("session_timeout_minutes", default=60)
       # Reads from database, cached in Redis
       return max(5, min(int(value), 1440))
   ```

3. Open `backend/app/core/security.py`
4. Show `create_access_token()` using SettingsService:
   ```python
   timeout_minutes = await settings_service.get_session_timeout_minutes()
   expire = datetime.utcnow() + timedelta(minutes=timeout_minutes)
   ```

**Proof**: "Code explicitly reads from SettingsService. No environment variables, no hardcoded constants."

---

#### Proof 3: No Restart Required

**Script**:
> "The ultimate proof - we've changed 4 settings during this demo without restarting the server once."

**Steps**:
1. Show server uptime:
   ```bash
   ps aux | grep uvicorn
   # Show process start time (before demo started)
   ```

2. Review all setting changes made during demo:
   - session_timeout: 60 → 5 → 10
   - max_login_attempts: 5 → 3
   - password_min_length: 12 → 16
   - mfa_required: false → true

3. All changes took effect within 5 minutes (cache TTL)

**Proof**: "Zero Mock Policy = No mocks, no restarts, no hardcoded values. Database-driven configuration."

---

### Part 7: Performance Validation (10 min)

**Script**:
> "Finally, let's verify all this enforcement doesn't hurt performance."

**Steps**:
1. Run load test script:
   ```bash
   python3 scripts/load_test_auth.py
   # 100 concurrent login requests
   ```

2. Show results:
   ```
   p50 latency: 45ms
   p95 latency: 87ms
   p99 latency: 142ms

   Cache hit rate: 97.3%
   ```

**Proof**: "System maintains <100ms p95 latency with all enforcement active. Performance target met."

---

### Part 8: Q&A and Wrap-up (10 min)

**Key Takeaways**:
1. ✅ **All 4 settings functional** - No mocks, no placeholders
2. ✅ **Zero Mock Policy compliant** - Database is source of truth
3. ✅ **No restart required** - Changes propagate within 5 minutes
4. ✅ **Admin control** - CTO can tune security posture via UI
5. ✅ **Performance maintained** - <100ms p95 API latency
6. ✅ **Security enhanced** - OWASP ASVS Level 2 compliance
7. ✅ **13 days ahead of schedule** - Delivered Jan 14 vs Jan 27 target

**Next Steps**:
- [ ] CTO approval for merge to main
- [ ] Deploy to staging environment
- [ ] Pilot with 5 internal users
- [ ] Phase 2 planning (6 additional settings)

---

## 📊 Demo Checklist

**Pre-Demo** (15 min before):
- [ ] All services running
- [ ] Database seeded with demo users
- [ ] Settings reset to defaults
- [ ] Browser tabs prepared
- [ ] Postman collections loaded
- [ ] Screen recording started (for documentation)

**During Demo**:
- [ ] Part 1: Introduction (5 min)
- [ ] Part 2: session_timeout_minutes (15 min)
- [ ] Part 3: max_login_attempts (20 min)
- [ ] Part 4: password_min_length (15 min)
- [ ] Part 5: mfa_required (30 min)
- [ ] Part 6: Zero Mock Policy Proof (15 min)
- [ ] Part 7: Performance Validation (10 min)
- [ ] Part 8: Q&A and Wrap-up (10 min)

**Post-Demo**:
- [ ] Share screen recording with team
- [ ] Document any questions/concerns
- [ ] Create follow-up action items
- [ ] Schedule Phase 2 kickoff

---

**Total Duration**: 2 hours
**Status**: Ready for execution
**Next**: Schedule with CTO
