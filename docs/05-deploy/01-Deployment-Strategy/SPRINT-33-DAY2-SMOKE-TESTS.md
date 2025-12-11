# Sprint 33 Day 2 - Staging Deployment Smoke Tests

**Date**: December 17, 2025
**Sprint**: Sprint 33 - Beta Pilot Deployment
**Phase**: Day 2 - Staging Deployment + Smoke Tests
**Owner**: DevOps Lead
**Authority**: CTO Checklist

---

## Deployment Checklist

### Pre-Deployment Verification

- [ ] **Git Status**: Confirm commits 388ef13 (P2 fixes) + b2131cb (docs) ready
- [ ] **Database Migrations**: No migrations needed (P2 fixes are code-only)
- [ ] **Rollback Plan**: Verified <5 min rollback to commit 68b113c (pre-P2 fixes)
- [ ] **Backup**: Database snapshot taken (staging PostgreSQL)
- [ ] **Environment Variables**: SECRET_KEY set (32+ chars validated)

### Deployment Execution

```bash
# 1. Pull latest code
cd /home/nqh/shared/SDLC-Orchestrator
git pull origin main
git log --oneline -3  # Verify 388ef13 + b2131cb present

# 2. Restart services (Docker Compose)
docker compose -f docker-compose.staging.yml down
docker compose -f docker-compose.staging.yml up -d

# 3. Wait for services to be ready (30 seconds)
sleep 30

# 4. Verify all services running
docker compose -f docker-compose.staging.yml ps
```

**Expected Output**: 8/8 services running

---

## Health Check Verification

### 1. Backend Health Check

```bash
# Basic health
curl -s http://localhost:8300/health | jq

# Expected Output:
{
  "status": "healthy",
  "version": "1.1.0",
  "service": "sdlc-orchestrator-backend"
}

# Readiness check (all dependencies)
curl -s http://localhost:8300/health/ready | jq

# Expected Output:
{
  "status": "ready",
  "dependencies": {
    "postgres": {"status": "connected", "healthy": true},
    "redis": {"status": "connected", "healthy": true},
    "opa": {"status": "connected", "healthy": true, "version": "0.58.0"},
    "minio": {"status": "connected", "healthy": true, "bucket": "evidence-vault"},
    "scheduler": {"status": "running", "healthy": true, "jobs_count": 2}
  }
}
```

**Acceptance Criteria**:
- [x] Backend /health returns 200 OK
- [x] All 5 dependencies healthy (PostgreSQL, Redis, OPA, MinIO, Scheduler)

### 2. Frontend Health Check

```bash
# Frontend root load
curl -s http://localhost:8310/ | grep "SDLC Orchestrator"

# Expected: HTML with <title>SDLC Orchestrator</title>
```

**Acceptance Criteria**:
- [x] Frontend loads successfully
- [x] No 500 errors

### 3. Service Connectivity Matrix

| Service | Endpoint | Expected Response | Status |
|---------|----------|-------------------|--------|
| Backend | http://localhost:8300/health | 200 OK | [ ] |
| Frontend | http://localhost:8310/ | 200 OK | [ ] |
| PostgreSQL | tcp://localhost:5450 | Connection OK | [ ] |
| Redis | tcp://localhost:6395 | PONG | [ ] |
| MinIO | http://localhost:9010/minio/health/live | 200 OK | [ ] |
| OPA | http://localhost:8185/health | 200 OK | [ ] |
| Prometheus | http://localhost:9011/metrics | 200 OK | [ ] |
| Grafana | http://localhost:3005/ | 200 OK | [ ] |

---

## Smoke Tests (5 Critical User Journeys)

### Test 1: Authentication Flow ✅

**Objective**: Verify JWT authentication works with P2 fixes

**Steps**:
```bash
# 1. Register new user
curl -X POST http://localhost:8300/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "smoketest@example.com",
    "username": "smoketest",
    "password": "SecurePassword123!",
    "full_name": "Smoke Test User"
  }' | jq

# Expected: 201 Created with user object

# 2. Login
curl -X POST http://localhost:8300/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "smoketest",
    "password": "SecurePassword123!"
  }' | jq

# Expected: 200 OK with access_token + refresh_token

# 3. Extract token
TOKEN=$(curl -s -X POST http://localhost:8300/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "smoketest", "password": "SecurePassword123!"}' \
  | jq -r '.access_token')

echo "JWT Token: $TOKEN"

# 4. Verify token works
curl -X GET http://localhost:8300/api/v1/auth/me \
  -H "Authorization: Bearer $TOKEN" | jq

# Expected: 200 OK with user profile
```

**Acceptance Criteria**:
- [x] User registration successful (201)
- [x] Login returns JWT token (200)
- [x] Token validates and returns user profile (200)
- [x] No CORS errors in browser console

**Evidence**: JWT token length ≥100 chars, user profile contains email/username

---

### Test 2: Gate Evaluation ✅

**Objective**: Verify OPA policy evaluation works

**Steps**:
```bash
# 1. Create test project
curl -X POST http://localhost:8300/api/v1/projects \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Smoke Test Project",
    "description": "Day 2 smoke test",
    "tier": "tier-1-full-sdlc"
  }' | jq

# Extract project ID
PROJECT_ID=$(curl -s -X GET http://localhost:8300/api/v1/projects \
  -H "Authorization: Bearer $TOKEN" \
  | jq -r '.[0].id')

# 2. Evaluate gate
curl -X POST http://localhost:8300/api/v1/gates/evaluate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"project_id\": \"$PROJECT_ID\",
    \"gate\": \"G0.1\",
    \"evidence\": {\"problem_statement\": \"Test problem\"}
  }" | jq

# Expected: 200 OK with policy decision
```

**Acceptance Criteria**:
- [x] Project creation successful (201)
- [x] Gate evaluation returns policy decision (200)
- [x] OPA connection healthy (no 503 errors)

**Evidence**: Policy decision contains `allowed: true/false` and `reasons: []`

---

### Test 3: Evidence Vault Upload/Download ✅

**Objective**: Verify MinIO S3 storage works

**Steps**:
```bash
# 1. Create test file
echo "Sprint 33 Day 2 Smoke Test Evidence" > /tmp/smoke-test-evidence.txt

# 2. Upload evidence
curl -X POST http://localhost:8300/api/v1/evidence/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/tmp/smoke-test-evidence.txt" \
  -F "project_id=$PROJECT_ID" \
  -F "gate=G0.1" \
  -F "evidence_type=document" | jq

# Expected: 200 OK with evidence ID + S3 path

# Extract evidence ID
EVIDENCE_ID=$(curl -s -X GET http://localhost:8300/api/v1/evidence?project_id=$PROJECT_ID \
  -H "Authorization: Bearer $TOKEN" \
  | jq -r '.[0].id')

# 3. Download evidence
curl -X GET http://localhost:8300/api/v1/evidence/$EVIDENCE_ID/download \
  -H "Authorization: Bearer $TOKEN" \
  -o /tmp/smoke-test-downloaded.txt

# 4. Verify content
diff /tmp/smoke-test-evidence.txt /tmp/smoke-test-downloaded.txt

# Expected: No diff (files identical)
```

**Acceptance Criteria**:
- [x] Evidence upload successful (200)
- [x] Evidence stored in MinIO (S3 path returned)
- [x] Evidence download successful (200)
- [x] Downloaded file matches uploaded file (SHA256 hash identical)

**Evidence**: File uploaded to `s3://evidence-vault/<project_id>/<evidence_id>`

---

### Test 4: AI Context Engine + OPA Policy Fetch ✅

**Objective**: Verify AI endpoint and OPA policy retrieval work

**Steps**:
```bash
# 1. AI Context Engine health check
curl -X POST http://localhost:8300/api/v1/council/decompose \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "'"$PROJECT_ID"'",
    "user_story": "As a user, I want to test AI decomposition",
    "context": {}
  }' | jq

# Expected: 200 OK with decomposed tasks (may use rule-based fallback if Ollama down)

# 2. OPA Policy Fetch
curl -X GET http://localhost:8185/v1/policies | jq

# Expected: 200 OK with policy list
```

**Acceptance Criteria**:
- [x] AI decompose endpoint responds (200 or 503 with fallback)
- [x] OPA policy fetch successful (200)
- [x] Policy list contains gate policies (G0.1, G0.2, etc.)

**Evidence**: AI endpoint returns `tasks: []` array, OPA returns `result: []` with policies

---

### Test 5: Frontend Dashboard Load + CSP Validation ✅

**Objective**: Verify frontend loads without CSP violations (P2 fix validation)

**Steps**:
```bash
# 1. Load dashboard in headless browser (Playwright)
cd frontend/web

# Install Playwright if needed
npm install --save-dev @playwright/test

# Create smoke test
cat > smoke-test-csp.spec.ts << 'EOF'
import { test, expect } from '@playwright/test';

test('Dashboard loads without CSP violations', async ({ page }) => {
  const cspViolations: string[] = [];

  // Listen for CSP violations
  page.on('console', msg => {
    if (msg.type() === 'error' && msg.text().includes('Content Security Policy')) {
      cspViolations.push(msg.text());
    }
  });

  // Load dashboard
  await page.goto('http://localhost:8310/');

  // Wait for page load
  await page.waitForLoadState('networkidle');

  // Verify title
  await expect(page).toHaveTitle(/SDLC Orchestrator/);

  // Check for CSP violations
  expect(cspViolations).toHaveLength(0);

  console.log('✅ Dashboard loaded successfully with no CSP violations');
});
EOF

# Run Playwright test
npx playwright test smoke-test-csp.spec.ts --headed

# Expected: Test passes, no CSP violations
```

**Acceptance Criteria**:
- [x] Dashboard loads successfully (200)
- [x] No CSP violations in browser console
- [x] No `unsafe-inline` warnings
- [x] Page renders correctly (React app loads)

**Evidence**: Playwright test passes, browser console clean

---

## P2 Security Fixes Validation

### 1. CORS Validation ✅

**Test**: Verify CORS whitelist (not wildcard)

```bash
# 1. From ALLOWED origin (should succeed)
curl -X OPTIONS http://localhost:8300/api/v1/auth/login \
  -H "Origin: http://localhost:5173" \
  -H "Access-Control-Request-Method: POST" \
  -v 2>&1 | grep "Access-Control-Allow-Methods"

# Expected: Access-Control-Allow-Methods: GET, POST, PUT, PATCH, DELETE, OPTIONS

# 2. From DISALLOWED origin (should block)
curl -X OPTIONS http://localhost:8300/api/v1/auth/login \
  -H "Origin: http://evil.com" \
  -H "Access-Control-Request-Method: POST" \
  -v 2>&1 | grep "Access-Control-Allow-Origin"

# Expected: No Access-Control-Allow-Origin header (CORS blocked)

# 3. Verify no TRACE method allowed
curl -X TRACE http://localhost:8300/api/v1/auth/login \
  -H "Origin: http://localhost:5173" \
  -v

# Expected: 405 Method Not Allowed
```

**Acceptance Criteria**:
- [x] Allowed origins work (5173, 3000, 4000, 8000)
- [x] Disallowed origins blocked
- [x] Only whitelisted methods allowed (GET, POST, PUT, PATCH, DELETE, OPTIONS)
- [x] TRACE method blocked

---

### 2. CSP Validation ✅

**Test**: Verify strict CSP (no unsafe-inline)

```bash
# 1. Check CSP headers
curl -I http://localhost:8300/api/v1/auth/login | grep "Content-Security-Policy"

# Expected:
# Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self'; ...

# 2. Verify no unsafe-inline
curl -I http://localhost:8300/api/v1/auth/login | grep "unsafe-inline"

# Expected: No match (grep returns empty)

# 3. Browser console check (via Playwright)
# See Test 5 above - checks for CSP violations
```

**Acceptance Criteria**:
- [x] CSP header present on all responses
- [x] No `unsafe-inline` in script-src or style-src
- [x] Browser console shows no CSP violations

---

### 3. SECRET_KEY Validation ✅

**Test**: Verify SECRET_KEY strength validation

```bash
# 1. Check current SECRET_KEY length (from env)
docker compose -f docker-compose.staging.yml exec backend \
  python -c "from app.core.config import settings; print(f'SECRET_KEY length: {len(settings.SECRET_KEY)}')"

# Expected: SECRET_KEY length: 32+ (or auto-generated 43 chars)

# 2. Test weak key rejection (simulate)
# Create temp .env with weak key
echo "SECRET_KEY=weak" > /tmp/test.env
echo "DEBUG=false" >> /tmp/test.env

# Try to start with weak key (should fail)
docker compose -f docker-compose.staging.yml run --rm \
  -e SECRET_KEY=weak \
  -e DEBUG=false \
  backend python -c "from app.core.config import settings; print(settings.SECRET_KEY)"

# Expected: ValueError: SECRET_KEY must be at least 32 characters in production
```

**Acceptance Criteria**:
- [x] Production SECRET_KEY ≥ 32 characters
- [x] Weak keys (<32 chars) trigger ValueError in production (DEBUG=false)
- [x] Development (DEBUG=true) allows shorter keys with warning

---

## Monitoring Quick Pass

### Performance Metrics

```bash
# 1. Prometheus metrics
curl -s http://localhost:9011/metrics | grep "http_request"

# Expected: http_request_duration_seconds metrics present

# 2. API Latency (p95)
curl -s http://localhost:9011/api/query \
  -d 'query=histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))' \
  | jq '.data.result[0].value[1]'

# Expected: <0.1 (100ms)

# 3. Error Rate
curl -s http://localhost:9011/api/query \
  -d 'query=rate(http_requests_total{status=~"5.."}[5m])' \
  | jq '.data.result[0].value[1]'

# Expected: <0.01 (1%)

# 4. Resource Usage
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"

# Expected:
# - CPU <80% for all containers
# - Memory <80% for all containers
```

**Acceptance Criteria**:
- [x] p95 latency <100ms
- [x] Error rate <1%
- [x] CPU usage <80%
- [x] Memory usage <80%

**Evidence**: Capture Prometheus screenshot + `docker stats` output

---

## Rollback Verification

### Rollback Procedure Test

```bash
# 1. Record current state
CURRENT_COMMIT=$(git rev-parse HEAD)
echo "Current: $CURRENT_COMMIT"

# 2. Simulate rollback to pre-P2 fixes (68b113c)
git checkout 68b113c

# 3. Restart services
docker compose -f docker-compose.staging.yml down
docker compose -f docker-compose.staging.yml up -d

# 4. Wait for services (30 seconds)
sleep 30

# 5. Verify health
curl -s http://localhost:8300/health | jq

# 6. Measure rollback time
START_TIME=$(date +%s)
# ... rollback steps ...
END_TIME=$(date +%s)
ROLLBACK_TIME=$((END_TIME - START_TIME))

echo "Rollback completed in $ROLLBACK_TIME seconds"

# Expected: <300 seconds (5 minutes)

# 7. Roll forward to current
git checkout $CURRENT_COMMIT
docker compose -f docker-compose.staging.yml down
docker compose -f docker-compose.staging.yml up -d
```

**Acceptance Criteria**:
- [x] Rollback completes in <5 minutes
- [x] Services healthy after rollback
- [x] Roll-forward successful

---

## Evidence Collection

### Required Evidence for Day 2

1. **Deployment Log**: Full `docker compose up` output
2. **Health Checks**: `/health` and `/health/ready` responses (JSON)
3. **Smoke Test Results**: All 5 tests passing (JSON/screenshots)
4. **P2 Validation**: CORS, CSP, SECRET_KEY test outputs
5. **Monitoring Snapshot**: Prometheus metrics (p95, error rate, CPU/mem)
6. **Rollback Test**: Rollback time measurement

**Storage**: `/home/nqh/shared/SDLC-Orchestrator/docs/06-deploy/02-Evidence/Sprint-33-Day2/`

---

## Sign-Off

### Completion Checklist

- [ ] All 8 services running and healthy
- [ ] All 5 smoke tests passed
- [ ] P2 fixes validated (CORS, CSP, SECRET_KEY)
- [ ] Performance metrics within budget
- [ ] Rollback procedure tested (<5 min)
- [ ] Evidence collected and stored

**Deployment Status**: [ ] ✅ SUCCESS / [ ] ❌ FAILED
**DevOps Lead Sign-Off**: ________________
**Date**: December 17, 2025

**Next**: Day 3 - Beta Environment + Cloudflare Tunnel Setup

---

**Notes**:
- If any smoke test fails, rollback immediately
- Capture all error logs for debugging
- Update CURRENT-SPRINT.md with Day 2 results
