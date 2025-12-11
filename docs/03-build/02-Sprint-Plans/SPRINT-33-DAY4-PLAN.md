# Sprint 33 - Day 4 Plan
**Date**: 2025-12-17 (Tuesday)
**Sprint**: Sprint 33 - P2 Fixes + Infrastructure Deployment
**Focus**: Database Migration Fix + Cloudflare External Access + Manual Smoke Tests
**Estimated Time**: 6-7 hours

---

## 🎯 **Day 4 Objectives**

### **Primary Goals**
1. ✅ **Complete Cloudflare DNS Setup** (10-15 min) - Enable external access
2. ✅ **Fix Database Migration Blocker** (2-3 hours) - Unblock smoke tests
3. ✅ **Execute Manual Smoke Tests** (1.5 hours) - 8 critical tests
4. ✅ **Apply Monitoring Alert Thresholds** (1 hour) - Grafana + Prometheus
5. ✅ **Day 4 Status Report** (30 min) - Document completion

### **Success Criteria**
- [ ] External access working (https://sdlc.nqh.vn responds with 200)
- [ ] Database schema created (24 tables + seed data)
- [ ] All 8 smoke tests passing
- [ ] Prometheus alerts configured (p95>100ms, error>1%, disk>80%)
- [ ] Zero P0/P1 bugs introduced

---

## 📋 **Task Breakdown**

### **Task 1: Cloudflare DNS & Tunnel (10-15 min)** 🔴 BLOCKER

**Reference**: [CLOUDFLARE-DNS-SETUP-COMMANDS.md](../03-Deployment-Guides/CLOUDFLARE-DNS-SETUP-COMMANDS.md)

**Steps**:
1. Add DNS routes via Cloudflare Dashboard:
   - Navigate to: Zero Trust → Networks → Tunnels → `my-tunnel`
   - Add hostname: `sdlc.nqh.vn` → `http://localhost:8310`
   - Add hostname: `sdlc-api.nqh.vn` → `http://localhost:8300`

2. Reload tunnel daemon:
   ```bash
   sudo systemctl restart cloudflared
   ```

3. Verify external access (wait 2-5 min for DNS):
   ```bash
   curl -I https://sdlc.nqh.vn
   curl -I https://sdlc-api.nqh.vn/health
   ```

**Expected Output**:
```
HTTP/2 200
server: cloudflare
...
```

---

### **Task 2: Fix Database Migration (2-3 hours)** 🔴 BLOCKER

**Root Cause** (Sprint 33 Day 3 Discovery):
- Alembic runs all migrations in single transaction
- Last migration (`k6f7g8h9i0j1`) tries to create index that exists
- Transaction fails → PostgreSQL rolls back ALL changes
- Result: 0 tables created despite successful migration logs

**Investigation Summary**:
```
✅ Migration logs show success (13 migrations executed)
✅ Seed data logs show success (4 projects, 12 users, 26 gates)
❌ Final index creation fails: "relation ix_gate_approvals_gate_id already exists"
❌ Transaction rollback → tables never committed
```

**Solution Options**:

#### **Option A: Comment Out Problematic Migration** (QUICKEST - 30 min)

1. Temporarily comment out `k6f7g8h9i0j1` migration:
   ```bash
   cd /home/nqh/shared/SDLC-Orchestrator/backend/alembic/versions
   mv k6f7g8h9i0j1_add_gate_g3_perf_indexes.py k6f7g8h9i0j1_add_gate_g3_perf_indexes.py.bak
   ```

2. Rebuild backend + run migration:
   ```bash
   docker compose build backend
   docker compose up -d backend
   sleep 10
   docker exec sdlc-backend bash -c "cd /app && alembic upgrade head"
   ```

3. Verify tables created:
   ```bash
   docker exec sdlc-postgres psql -U sdlc_user -d sdlc_orchestrator -c "\dt" | wc -l
   # Expected: ~30 lines (24 tables + headers)
   ```

4. Re-enable migration after tables exist:
   ```bash
   mv k6f7g8h9i0j1_add_gate_g3_perf_indexes.py.bak k6f7g8h9i0j1_add_gate_g3_perf_indexes.py
   docker compose build backend
   docker compose restart backend
   ```

#### **Option B: Manual Schema Import** (PROVEN - 1 hour)

1. Find a working environment (dev/local) with full schema
2. Export schema:
   ```bash
   pg_dump -U sdlc_user -d sdlc_orchestrator --schema-only --no-owner --no-privileges > schema.sql
   ```

3. Import to production:
   ```bash
   docker exec -i sdlc-postgres psql -U sdlc_user -d sdlc_orchestrator < schema.sql
   ```

4. Verify:
   ```bash
   docker exec sdlc-postgres psql -U sdlc_user -d sdlc_orchestrator -c "\dt"
   ```

#### **Option C: Split Migrations** (PROPER FIX - 2-3 hours)

1. Modify `alembic/env.py` to disable transactional DDL:
   ```python
   context.configure(
       connection=connection,
       target_metadata=target_metadata,
       transaction_per_migration=True,  # ADD THIS
   )
   ```

2. Test in dev environment
3. Apply to production

**Recommended**: **Option A** (quickest, unblocks smoke tests)
**Follow-up**: **Option C** as technical debt in Sprint 34

---

### **Task 3: Manual Smoke Tests (1.5 hours)**

**Prerequisites**: Database schema created + external access working

**Test Checklist** (from Day 2 deferred tests):

#### **Test 1: Auth (Login + JWT) - 10 min**
```bash
# Login
curl -X POST https://sdlc-api.nqh.vn/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# Expected: {"access_token":"...","token_type":"bearer"}

# Store token
TOKEN="<access_token_from_above>"

# Test authenticated endpoint
curl -H "Authorization: Bearer $TOKEN" \
  https://sdlc-api.nqh.vn/api/v1/projects

# Expected: 200 OK with project list
```

**Success Criteria**: ✅ Login returns JWT, token works on authenticated endpoint

---

#### **Test 2: Gate Evaluation - 15 min**
```bash
# Get project ID
PROJECT_ID=$(curl -s -H "Authorization: Bearer $TOKEN" \
  https://sdlc-api.nqh.vn/api/v1/projects | \
  python3 -c "import sys,json; print(json.load(sys.stdin)['items'][0]['id'])")

# Evaluate gate
curl -X POST https://sdlc-api.nqh.vn/api/v1/gates/evaluate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"project_id\":\"$PROJECT_ID\",\"gate_type\":\"G0_1\"}"

# Expected: 200 OK with policy decision {"is_passed":true/false,"violations":[...]}
```

**Success Criteria**: ✅ Gate evaluation returns 200 with decision payload

---

#### **Test 3: Evidence Vault (Upload/Download) - 15 min**
```bash
# Create test file
echo "Test evidence document" > /tmp/test_evidence.txt

# Upload evidence
EVIDENCE_RESP=$(curl -X POST https://sdlc-api.nqh.vn/api/v1/evidence \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/tmp/test_evidence.txt" \
  -F "gate_id=$GATE_ID" \
  -F "evidence_type=document")

# Extract evidence ID
EVIDENCE_ID=$(echo $EVIDENCE_RESP | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

# Download evidence
curl -H "Authorization: Bearer $TOKEN" \
  https://sdlc-api.nqh.vn/api/v1/evidence/$EVIDENCE_ID/download \
  -o /tmp/downloaded_evidence.txt

# Verify checksum
diff /tmp/test_evidence.txt /tmp/downloaded_evidence.txt
# Expected: No output (files identical)
```

**Success Criteria**: ✅ Upload returns evidence ID, download matches original

---

#### **Test 4: AI/Policy Endpoints - 10 min**
```bash
# Test AI context endpoint
curl -H "Authorization: Bearer $TOKEN" \
  https://sdlc-api.nqh.vn/api/v1/ai/context?gate_type=G0_1

# Expected: 200 OK with AI context payload

# Test OPA policy fetch
curl -H "Authorization: Bearer $TOKEN" \
  https://sdlc-api.nqh.vn/api/v1/policies/gate/G0_1

# Expected: 200 OK with policy rules
```

**Success Criteria**: ✅ Both endpoints return 200 with expected payloads

---

#### **Test 5: Frontend CSP Validation - 15 min**
```bash
# Open browser (incognito)
open -na "Google Chrome" --args --incognito https://sdlc.nqh.vn

# Steps:
1. Open DevTools (F12)
2. Navigate to Console tab
3. Check for CSP errors (should be NONE)
4. Navigate to: Projects → Gate Detail → Evidence Vault
5. Verify no CSP violations in console

# Expected: Clean console, no "Content Security Policy" errors
```

**Success Criteria**: ✅ No CSP violations in browser console

---

#### **Test 6: CORS Validation - 10 min**
```bash
# Test from allowed origin (should succeed)
curl -I -H "Origin: https://sdlc.nqh.vn" \
  https://sdlc-api.nqh.vn/api/v1/projects

# Expected: Access-Control-Allow-Origin: https://sdlc.nqh.vn

# Test from disallowed origin (should fail)
curl -I -H "Origin: https://evil.com" \
  https://sdlc-api.nqh.vn/api/v1/projects

# Expected: No Access-Control-Allow-Origin header
```

**Success Criteria**: ✅ Allowed origin passes, disallowed origin blocked

---

#### **Test 7: SECRET_KEY Guard - 5 min**
```bash
# Verify production backend has ≥32 char secret
docker exec sdlc-backend bash -c 'echo ${#SECRET_KEY}'
# Expected: ≥32

# Test with short key (should fail)
docker run -e SECRET_KEY="short" sdlc-orchestrator-backend
# Expected: Startup error (P2 guard triggers)
```

**Success Criteria**: ✅ Production secret ≥32 chars, short key rejected

---

#### **Test 8: Health & Metrics - 10 min**
```bash
# Backend health
curl https://sdlc-api.nqh.vn/health
# Expected: {"status":"healthy",...}

# Prometheus scrape (internal)
curl http://localhost:9096/metrics | grep sdlc_

# Expected: Metrics like:
# sdlc_http_requests_total{...} 123
# sdlc_http_request_duration_seconds_bucket{...} 0.05

# Check p95 latency
curl http://localhost:9096/api/v1/query?query='histogram_quantile(0.95, rate(sdlc_http_request_duration_seconds_bucket[5m]))'
# Expected: p95 < 0.100 (100ms)

# Check error rate
curl http://localhost:9096/api/v1/query?query='rate(sdlc_http_requests_total{status=~"5.."}[5m])'
# Expected: < 0.01 (1%)
```

**Success Criteria**: ✅ All health checks OK, p95 <100ms, error <1%

---

### **Task 4: Monitoring Alert Thresholds (1 hour)**

**Reference**: [MONITORING-ALERT-THRESHOLDS.md](../../07-operate/01-Monitoring-Alerting/MONITORING-ALERT-THRESHOLDS.md)

#### **Subtask 4.1: Create Prometheus Alert Rules** (30 min)

1. Create alert rules file:
   ```bash
   cat > infrastructure/monitoring/prometheus/rules/sdlc_alerts.yml <<'EOF'
   groups:
     - name: sdlc_api_performance
       interval: 30s
       rules:
         - alert: HighAPILatency
           expr: histogram_quantile(0.95, rate(sdlc_http_request_duration_seconds_bucket[5m])) > 0.100
           for: 5m
           labels:
             severity: warning
             team: backend
           annotations:
             summary: "API p95 latency exceeds 100ms"
             description: "p95 latency is {{ $value }}s (target: <0.100s)"

         - alert: HighErrorRate
           expr: rate(sdlc_http_requests_total{status=~"5.."}[5m]) > 0.01
           for: 3m
           labels:
             severity: critical
             team: backend
           annotations:
             summary: "API error rate exceeds 1%"
             description: "Error rate is {{ $value }} (target: <0.01)"

         - alert: HighDiskUsage
           expr: (node_filesystem_avail_bytes / node_filesystem_size_bytes) < 0.20
           for: 10m
           labels:
             severity: warning
             team: devops
           annotations:
             summary: "Disk usage exceeds 80%"
             description: "Free space is {{ $value }}%"
   EOF
   ```

2. Reload Prometheus:
   ```bash
   curl -X POST http://localhost:9096/-/reload
   ```

3. Verify alerts loaded:
   ```bash
   curl http://localhost:9096/api/v1/rules | python3 -m json.tool
   ```

#### **Subtask 4.2: Configure Grafana Dashboards** (30 min)

1. Import SDLC dashboard:
   ```bash
   curl -X POST http://localhost:3001/api/dashboards/db \
     -H "Authorization: Bearer $GRAFANA_API_KEY" \
     -H "Content-Type: application/json" \
     -d @infrastructure/monitoring/grafana/dashboards/sdlc_overview.json
   ```

2. Set up alert notifications (Slack/Email)

3. Test alert firing:
   ```bash
   # Trigger high latency (simulate slow query)
   ab -n 1000 -c 50 https://sdlc-api.nqh.vn/api/v1/projects
   ```

---

### **Task 5: Day 4 Status Report (30 min)**

Create: `docs/09-govern/01-CTO-Reports/2025-12-17-CTO-SPRINT-33-DAY4-STATUS.md`

**Required Sections**:
- Executive Summary (achievements + blockers resolved)
- Task Completion Status (5 tasks)
- Smoke Test Results (8/8 tests)
- Monitoring Configuration (alert rules + dashboards)
- Sprint Progress Update (Day 1-4 average rating)
- Next Steps (Day 5: Team onboarding)

---

## 🚨 **Known Blockers & Mitigation**

### **Blocker 1: Database Migration** (HIGH PRIORITY)
**Status**: Fix in progress (Task 2)
**Impact**: Blocks smoke tests
**Mitigation**: Use Option A (comment out problematic migration)
**ETA**: 30 min

### **Blocker 2: Cloudflare DNS Manual Setup** (MEDIUM PRIORITY)
**Status**: Requires dashboard access
**Impact**: External access unavailable until DNS added
**Mitigation**: Follow CLOUDFLARE-DNS-SETUP-COMMANDS.md step-by-step
**ETA**: 10-15 min

---

## 📊 **Success Metrics**

| Metric | Target | Expected | Status |
|--------|--------|----------|--------|
| External Access | Working | ✅ | ⏳ PENDING |
| Database Tables | 24 created | 24 | ⏳ PENDING |
| Smoke Tests | 8/8 passing | 8/8 | ⏳ PENDING |
| Alert Rules | 3+ configured | 3 | ⏳ PENDING |
| Grafana Dashboards | 1+ imported | 1 | ⏳ PENDING |
| P0/P1 Bugs | 0 | 0 | ✅ ON TRACK |
| Day 4 Rating | ≥9.0/10 | 9.3/10 | ⏳ PENDING |

---

## 🎯 **Sprint 33 Progress After Day 4**

| Day | Focus | Rating | Status |
|-----|-------|--------|--------|
| Day 1 | P2 Security Fixes | 9.5/10 | ✅ |
| Day 2 | Staging Infrastructure | 7.0/10 | ✅ |
| Day 3 | Production + Beta + Cloudflare | 9.2/10 | ✅ |
| **Day 4** | **DB Fix + External Access + Smoke Tests** | **9.3/10** | **⏳ IN PROGRESS** |
| Day 5 | Team 1-2 Onboarding | - | ⏳ PLANNED |

**Target Average**: 8.75/10 (Excellent)
**Current Average (Day 1-3)**: 8.57/10 (Strong)
**Projected Average (Day 1-4)**: 8.75/10 (On Target)

---

## 📝 **Notes for Execution**

1. **Start with Task 1 (Cloudflare)**: Quick win, unblocks external testing
2. **Task 2 (DB Migration)**: Use Option A for speed, document Option C for Sprint 34
3. **Task 3 (Smoke Tests)**: Document ALL results (pass/fail with logs)
4. **Task 4 (Monitoring)**: Basic setup only, fine-tuning in Day 5
5. **Task 5 (Report)**: Include lessons learned from DB migration debugging

---

**Day 4 Estimated Timeline**:
- 08:00-08:15: Cloudflare DNS setup (Task 1)
- 08:15-10:45: DB migration fix + verification (Task 2)
- 10:45-12:15: Manual smoke tests (Task 3)
- 12:15-13:15: Lunch break
- 13:15-14:15: Monitoring setup (Task 4)
- 14:15-14:45: Day 4 status report (Task 5)
- 14:45-15:00: Buffer for unexpected issues

**Total**: 6 hours 45 minutes (including 1h lunch)

---

**Document Status**: ✅ READY FOR EXECUTION
**Next Review**: End of Day 4 (2025-12-17 15:00)
**Owner**: DevOps + Backend + QA Teams
