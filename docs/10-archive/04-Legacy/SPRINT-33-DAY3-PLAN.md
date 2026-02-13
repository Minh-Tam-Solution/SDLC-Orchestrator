# Sprint 33 Day 3 Plan - Beta Environment + Cloudflare Tunnel

**Date**: December 18, 2025 (Wednesday)
**Sprint**: Sprint 33 - Beta Pilot Deployment
**Day**: Day 3 of 10
**Owner**: DevOps Lead + Backend Lead
**Status**: 📋 **PLANNED**

---

## Objectives

Deploy production-ready beta environment with external access via Cloudflare Tunnel for 5 internal pilot teams (38 users).

### Success Criteria

1. ✅ Beta environment running with 8/8 services healthy
2. ✅ Database schema populated (24+ tables)
3. ✅ Cloudflare Tunnel configured (`sdlc.nqh.vn`, `sdlc-api.nhatquangholding.com`)
4. ✅ Manual smoke tests passing (5/8 minimum)
5. ✅ External access validated (from non-NQH network)
6. ✅ P2 security fixes verified in beta

---

## Pre-requisites (From Day 2)

### Available Resources

**Working Infrastructure** ✅:
- Production docker-compose.yml (proven working in production)
- P2 security fixes committed (CORS, CSP, SECRET_KEY)
- Frontend build fixed (utils.ts created)
- Port allocation approved by IT Team

**Documentation** ✅:
- [Day 2 Status Report](../../09-govern/01-CTO-Reports/2025-12-16-CTO-SPRINT-33-DAY2-STATUS.md)
- [Technical Debt Ticket](../../08-maintain/02-Technical-Debt/TD-SPRINT34-DB-MIGRATION-AUTOMATION.md)
- [Smoke Test Checklist](../../06-deploy/01-Deployment-Strategy/SPRINT-33-DAY2-SMOKE-TESTS.md)

### Known Issues (Workarounds Required)

**Issue 1: Database Migration Automation** (from Day 2)
- **Status**: Technical debt TD-SPRINT34-001
- **Workaround**: Manual schema export/import from production
- **Time**: 15 minutes

**Issue 2: Port Conflicts** (from Day 2)
- **Status**: Host has services on 9093
- **Workaround**: Remap ports in docker-compose (9093 → 9094)
- **Time**: 10 minutes

---

## Phase 1: Environment Setup (1 hour)

### Task 1.1: Prepare Beta Docker Compose

**Objective**: Create beta-specific docker-compose with correct ports

```bash
# 1. Copy production compose as baseline
cp docker-compose.yml docker-compose.beta.yml

# 2. Remap conflicting ports
# - Alertmanager: 9093 → 9094
# - Grafana: 3000 → 3005 (already in IT allocation)
# - Others: Use beta ports from IT allocation

# 3. Update service names (sdlc-* → sdlc-beta-*)
sed -i 's/container_name: sdlc-/container_name: sdlc-beta-/g' docker-compose.beta.yml

# 4. Create beta network
# - Network: sdlc-beta-network
# - Volumes: beta_postgres_data, beta_redis_data, etc.
```

**Port Mapping (Beta Environment)**:

| Service | Production Port | Beta Port | Status |
|---------|----------------|-----------|--------|
| Backend API | 8000 | 8300 | ✅ Available |
| Frontend Web | 3000 | 8310 | ✅ Available |
| PostgreSQL | 5432 | 5450 | ✅ Available |
| Redis | 6379 | 6395 | ✅ Available |
| MinIO API | 9000 | 9010 | ✅ Available |
| MinIO Console | 9001 | 9015 | ✅ Available |
| OPA | 8181 | 8185 | ✅ Available |
| Prometheus | 9090 | 9011 | ✅ Available |
| Grafana | 3000 | 3005 | ✅ Available |
| Alertmanager | 9093 | 9094 | ⚠️ Remapped (conflict) |

**Expected Output**: `docker-compose.beta.yml` ready for deployment

---

### Task 1.2: Configure Beta Environment Variables

**Objective**: Create `.env.beta` with production-grade secrets

```bash
# 1. Copy production env as template
cp .env.production .env.beta

# 2. Update critical settings
# - DEBUG=false (production mode)
# - SECRET_KEY (32+ chars, different from prod)
# - ALLOWED_ORIGINS (beta-specific)
# - DATABASE credentials (beta-specific)

# 3. Verify SECRET_KEY strength
python3 -c "
import secrets
key = secrets.token_urlsafe(32)
print(f'SECRET_KEY={key}')
print(f'Length: {len(key)} chars (OK: {len(key) >= 32})')
"
```

**Required Variables**:

```env
# App Config
DEBUG=false
ENVIRONMENT=beta
ALLOWED_ORIGINS=https://sdlc.nqh.vn,http://localhost:8310

# Database
POSTGRES_PASSWORD=<generate-secure-32-chars>
DATABASE_URL=postgresql+asyncpg://sdlc_beta_user:${POSTGRES_PASSWORD}@postgres:5432/sdlc_orchestrator_beta

# Redis
REDIS_PASSWORD=<generate-secure-32-chars>
REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0

# MinIO
MINIO_ROOT_USER=<generate-secure-16-chars>
MINIO_ROOT_PASSWORD=<generate-secure-32-chars>

# JWT
JWT_SECRET_KEY=<generate-secure-43-chars>
ACCESS_TOKEN_EXPIRE_HOURS=1
REFRESH_TOKEN_EXPIRE_DAYS=30

# Frontend
VITE_API_URL=https://sdlc-api.nhatquangholding.com
```

**Expected Output**: `.env.beta` with all secrets generated and validated

---

### Task 1.3: Deploy Beta Services

**Objective**: Start all 8 beta services

```bash
# 1. Stop any existing beta containers
docker compose -f docker-compose.beta.yml --env-file .env.beta down -v

# 2. Pull latest images
docker compose -f docker-compose.beta.yml --env-file .env.beta pull

# 3. Build frontend with beta API URL
docker compose -f docker-compose.beta.yml --env-file .env.beta build frontend

# 4. Start all services
docker compose -f docker-compose.beta.yml --env-file .env.beta up -d

# 5. Wait for services to be healthy (60 seconds)
sleep 60

# 6. Verify all services running
docker compose -f docker-compose.beta.yml --env-file .env.beta ps
```

**Expected Output**: 8/8 services running and healthy

**Validation**:
```bash
# Check health endpoints
curl http://localhost:8300/health  # Backend
curl http://localhost:8310/        # Frontend
curl http://localhost:9011/-/healthy  # Prometheus
```

---

## Phase 2: Database Setup (30 minutes)

### Task 2.1: Manual Schema Setup (Workaround for TD-SPRINT34-001)

**Objective**: Populate beta database with complete schema

**Option A: Export from Production** ⭐ **RECOMMENDED**

```bash
# 1. Export schema from production (schema-only, no data)
docker exec sdlc-postgres pg_dump -U sdlc_user -d sdlc_orchestrator \
  --schema-only --no-owner --no-acl > /tmp/beta-schema.sql

# 2. Import to beta
cat /tmp/beta-schema.sql | docker exec -i sdlc-beta-postgres \
  psql -U sdlc_beta_user -d sdlc_orchestrator_beta

# 3. Mark alembic as current version
docker exec sdlc-beta-backend alembic stamp head

# 4. Verify tables created
docker exec sdlc-beta-postgres psql -U sdlc_beta_user \
  -d sdlc_orchestrator_beta -c "\dt" | wc -l
# Expected: 24+ tables
```

**Option B: Run Seed Migration Manually**

```bash
# 1. Create tables from migrations
docker exec sdlc-beta-backend alembic upgrade head

# 2. If fails, investigate (see TD-SPRINT34-001)

# 3. Manual table creation as fallback
# (Use SQL from alembic migrations)
```

**Expected Output**: 24+ tables created in beta database

**Validation**:
```bash
# Check critical tables exist
docker exec sdlc-beta-postgres psql -U sdlc_beta_user \
  -d sdlc_orchestrator_beta -c "
    SELECT COUNT(*) FROM information_schema.tables
    WHERE table_schema = 'public';
  "
# Expected: 24+ tables

# Check seed users exist (from migration a502ce0d23a7)
docker exec sdlc-beta-postgres psql -U sdlc_beta_user \
  -d sdlc_orchestrator_beta -c "SELECT COUNT(*) FROM users;"
# Expected: 10+ users (BFlow, NQH-Bot, MTEP, etc.)
```

---

### Task 2.2: Verify Backend Connectivity

**Objective**: Ensure backend can query database

```bash
# 1. Check backend health with DB dependency
curl http://localhost:8300/health/ready | jq

# Expected output:
# {
#   "status": "ready",
#   "dependencies": {
#     "postgres": {"status": "connected", "healthy": true},
#     "redis": {"status": "connected", "healthy": true},
#     "opa": {"status": "connected", "healthy": true},
#     "minio": {"status": "connected", "healthy": true},
#     "scheduler": {"status": "running", "healthy": true}
#   }
# }

# 2. Test API endpoint that requires DB
curl http://localhost:8300/api/v1/auth/health | jq
# Expected: {"status": "healthy", "database": true}
```

**Expected Output**: All dependencies healthy, DB queries working

---

## Phase 3: Cloudflare Tunnel Setup (1 hour)

### Task 3.1: Install Cloudflare Tunnel

**Objective**: Install `cloudflared` on host server

```bash
# 1. Download cloudflared
wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb

# 2. Install
sudo dpkg -i cloudflared-linux-amd64.deb

# 3. Verify installation
cloudflared --version
# Expected: cloudflared version 2024.x.x
```

**Expected Output**: `cloudflared` binary available in PATH

---

### Task 3.2: Authenticate Cloudflare Tunnel

**Objective**: Link tunnel to NQH Cloudflare account

```bash
# 1. Login to Cloudflare (opens browser)
cloudflared tunnel login

# 2. Select nqh.vn domain when prompted

# 3. Verify authentication
ls ~/.cloudflared/
# Expected: cert.pem created
```

**Expected Output**: Cloudflare credentials stored in `~/.cloudflared/cert.pem`

---

### Task 3.3: Create Tunnel

**Objective**: Create named tunnel for SDLC beta

```bash
# 1. Create tunnel
cloudflared tunnel create sdlc-beta

# 2. Note tunnel ID (will be in output)
# Example: Created tunnel sdlc-beta with id abc123-def456-ghi789

# 3. Verify tunnel created
cloudflared tunnel list
# Expected: sdlc-beta tunnel listed

# 4. Save tunnel credentials
# Credentials stored in: ~/.cloudflared/<tunnel-id>.json
```

**Expected Output**: Tunnel `sdlc-beta` created with unique ID

---

### Task 3.4: Configure Tunnel Routes

**Objective**: Route `sdlc.nqh.vn` and `sdlc-api.nhatquangholding.com` to beta services

**Create tunnel config**: `~/.cloudflared/config.yml`

```yaml
tunnel: <tunnel-id>
credentials-file: /home/nqh/.cloudflared/<tunnel-id>.json

ingress:
  # Frontend: sdlc.nqh.vn → localhost:8310
  - hostname: sdlc.nqh.vn
    service: http://localhost:8310
    originRequest:
      noTLSVerify: true

  # Backend API: sdlc-api.nhatquangholding.com → localhost:8300
  - hostname: sdlc-api.nhatquangholding.com
    service: http://localhost:8300
    originRequest:
      noTLSVerify: true

  # Catch-all (required)
  - service: http_status:404
```

**Create DNS records**:

```bash
# 1. Create DNS CNAME for frontend
cloudflared tunnel route dns sdlc-beta sdlc.nqh.vn

# 2. Create DNS CNAME for backend
cloudflared tunnel route dns sdlc-beta sdlc-api.nhatquangholding.com

# 3. Verify DNS records created
nslookup sdlc.nqh.vn
nslookup sdlc-api.nhatquangholding.com
# Expected: CNAME pointing to <tunnel-id>.cfargotunnel.com
```

**Expected Output**: DNS records created, tunnel config ready

---

### Task 3.5: Start Tunnel Service

**Objective**: Run tunnel as systemd service

**Create systemd service**: `/etc/systemd/system/cloudflared-sdlc-beta.service`

```ini
[Unit]
Description=Cloudflare Tunnel for SDLC Beta
After=network.target

[Service]
Type=simple
User=nqh
ExecStart=/usr/local/bin/cloudflared tunnel --config /home/nqh/.cloudflared/config.yml run sdlc-beta
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
```

**Start service**:

```bash
# 1. Reload systemd
sudo systemctl daemon-reload

# 2. Enable service (start on boot)
sudo systemctl enable cloudflared-sdlc-beta

# 3. Start service
sudo systemctl start cloudflared-sdlc-beta

# 4. Check status
sudo systemctl status cloudflared-sdlc-beta
# Expected: active (running)

# 5. Check tunnel connection
cloudflared tunnel info sdlc-beta
# Expected: Connector connected
```

**Expected Output**: Tunnel running as systemd service, connected to Cloudflare

---

### Task 3.6: Validate External Access

**Objective**: Confirm services accessible via public URLs

```bash
# 1. Test frontend from external network
curl -I https://sdlc.nqh.vn
# Expected: 200 OK, HTML content

# 2. Test backend API from external network
curl https://sdlc-api.nhatquangholding.com/health | jq
# Expected: {"status": "healthy", ...}

# 3. Test from mobile network (outside NQH)
# - Open https://sdlc.nqh.vn in mobile browser
# - Verify dashboard loads
# - Check network tab for API calls to sdlc-api.nhatquangholding.com
```

**Expected Output**: Both URLs accessible from internet, SSL working (Cloudflare cert)

---

## Phase 4: Manual Smoke Tests (1.5 hours)

### Test 1: Authentication Flow ✅

**Objective**: Login with seed user, verify JWT

```bash
# 1. Get seed user credentials (from migration a502ce0d23a7)
# Example: admin@bflow.vn / SecurePassword123!

# 2. Login via API
curl -X POST https://sdlc-api.nhatquangholding.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin@bflow.vn",
    "password": "SecurePassword123!"
  }' | jq

# Expected: {"access_token": "...", "refresh_token": "..."}

# 3. Extract token
TOKEN="<access_token_from_step_2>"

# 4. Verify token works
curl https://sdlc-api.nhatquangholding.com/api/v1/auth/me \
  -H "Authorization: Bearer $TOKEN" | jq

# Expected: User profile with email, roles, etc.
```

**Evidence**: JWT token works, user data returned

---

### Test 2: P2 Security Validation ✅

**Objective**: Verify Day 1 P2 fixes active in beta

**Test 2.1: CORS Explicit Methods**

```bash
# Test from allowed origin
curl -X OPTIONS https://sdlc-api.nhatquangholding.com/api/v1/auth/login \
  -H "Origin: https://sdlc.nqh.vn" \
  -H "Access-Control-Request-Method: POST" \
  -v 2>&1 | grep "Access-Control-Allow-Methods"

# Expected: Access-Control-Allow-Methods: GET, POST, PUT, PATCH, DELETE, OPTIONS

# Verify TRACE blocked
curl -X TRACE https://sdlc-api.nhatquangholding.com/api/v1/auth/login \
  -H "Origin: https://sdlc.nqh.vn" -v

# Expected: 405 Method Not Allowed
```

**Test 2.2: CSP Strict Policy**

```bash
# Check CSP header
curl -I https://sdlc-api.nhatquangholding.com/api/v1/auth/login | grep "Content-Security-Policy"

# Expected: Content-Security-Policy: default-src 'self'; script-src 'self'; ...
# NO 'unsafe-inline' or 'unsafe-eval'
```

**Test 2.3: SECRET_KEY Validator**

```bash
# Check backend logs for SECRET_KEY length
docker logs sdlc-beta-backend 2>&1 | grep -i "secret" | head -5

# If key < 32 chars in production (DEBUG=false), should see ValueError
# If key >= 32 chars, no error (normal startup)
```

**Evidence**: All P2 fixes active, no regressions

---

### Test 3: Frontend Load + CSP Validation ✅

**Objective**: Dashboard loads without CSP violations

```bash
# 1. Open dashboard in browser
open https://sdlc.nqh.vn

# 2. Open DevTools Console (F12)

# 3. Check for CSP violations
# Look for errors like: "Refused to execute inline script"

# 4. Verify page renders correctly
# - Login form visible
# - React app loaded
# - No console errors (except expected API 401 when not logged in)
```

**Evidence**: Dashboard loads, no CSP violations in console

---

### Test 4: Gate Evaluation ✅

**Objective**: Policy engine (OPA) works

```bash
# 1. Login and get token (from Test 1)

# 2. Create test project
curl -X POST https://sdlc-api.nhatquangholding.com/api/v1/projects \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Beta Smoke Test Project",
    "description": "Day 3 smoke test",
    "tier": "tier-1-full-sdlc"
  }' | jq

# Extract project_id

# 3. Evaluate gate
curl -X POST https://sdlc-api.nhatquangholding.com/api/v1/gates/evaluate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "<project_id>",
    "gate": "G0.1",
    "evidence": {"problem_statement": "Test problem"}
  }' | jq

# Expected: {"allowed": true/false, "reasons": [...]}
```

**Evidence**: OPA policy evaluation works, gates can be evaluated

---

### Test 5: Evidence Vault Upload ✅

**Objective**: MinIO S3 storage works

```bash
# 1. Create test file
echo "Sprint 33 Day 3 Beta Smoke Test Evidence" > /tmp/beta-test-evidence.txt

# 2. Upload to Evidence Vault
curl -X POST https://sdlc-api.nhatquangholding.com/api/v1/evidence/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/tmp/beta-test-evidence.txt" \
  -F "project_id=<project_id>" \
  -F "gate=G0.1" \
  -F "evidence_type=document" | jq

# Expected: {"id": "...", "s3_path": "s3://evidence-vault/..."}

# 3. Download evidence
curl -X GET https://sdlc-api.nhatquangholding.com/api/v1/evidence/<evidence_id>/download \
  -H "Authorization: Bearer $TOKEN" \
  -o /tmp/beta-downloaded.txt

# 4. Verify content matches
diff /tmp/beta-test-evidence.txt /tmp/beta-downloaded.txt
# Expected: No diff
```

**Evidence**: MinIO upload/download works, file integrity preserved

---

## Phase 5: Documentation & Sign-off (30 minutes)

### Task 5.1: Create Day 3 Completion Report

**Objective**: Document all deployment steps and results

**Report Contents**:
1. Beta environment configuration (ports, services, versions)
2. Cloudflare Tunnel setup (DNS records, tunnel ID, config)
3. Manual smoke test results (5/8 minimum passing)
4. External access validation (screenshots from mobile network)
5. P2 security validation (CORS, CSP, SECRET_KEY evidence)
6. Known issues and workarounds (DB migration manual step)
7. Next steps (Day 4: Monitoring setup)

**File**: `docs/09-govern/01-CTO-Reports/2025-12-18-CTO-SPRINT-33-DAY3-COMPLETE.md`

---

### Task 5.2: Update Sprint Status

**Objective**: Mark Day 3 complete in CURRENT-SPRINT.md

```markdown
**Day 3 Progress**: ✅ **BETA ENVIRONMENT COMPLETE** - External access via Cloudflare Tunnel (9/10)
```

**Update Success Criteria**:
- [x] Beta environment deployed via Cloudflare Tunnel ✅ **DAY 3 COMPLETE**

---

### Task 5.3: Notify Pilot Teams

**Objective**: Send beta access credentials to 5 teams

**Email Template**:

```
Subject: SDLC Orchestrator Beta Access Ready - Team [BFlow/NQH-Bot/MTEP/...]

Hi [Team Lead],

Your beta access to SDLC Orchestrator is now ready!

🔗 Access URLs:
- Dashboard: https://sdlc.nqh.vn
- API Docs: https://sdlc-api.nhatquangholding.com/api/docs

🔐 Login Credentials:
- Email: [team-specific email from seed data]
- Password: [provided separately via secure channel]

📅 Onboarding Schedule:
- Teams 1-2 (BFlow, NQH-Bot): Dec 20
- Teams 3-4 (MTEP, Orchestrator): Dec 23
- Team 5 (Superset): Dec 24

📚 Documentation:
- User Guide: https://sdlc.nqh.vn/docs/user-guide
- Quick Start: https://sdlc.nqh.vn/docs/quick-start

🐛 Report Issues:
- #sdlc-beta-feedback Slack channel
- Email: devops@nqh.vn

Thank you for participating in our beta pilot!

Best regards,
DevOps Team
```

---

## Success Criteria Review

At end of Day 3, verify all criteria met:

1. ✅ Beta environment running with 8/8 services healthy
2. ✅ Database schema populated (24+ tables)
3. ✅ Cloudflare Tunnel configured (`sdlc.nqh.vn`, `sdlc-api.nhatquangholding.com`)
4. ✅ Manual smoke tests passing (5/8 minimum)
5. ✅ External access validated (from non-NQH network)
6. ✅ P2 security fixes verified in beta
7. ✅ Day 3 report created and committed
8. ✅ Pilot teams notified of beta access

**Target Score**: 9/10 (1 point deducted for manual DB setup workaround)

---

## Risk Mitigation

### Risk 1: Cloudflare Tunnel Connection Fails

**Likelihood**: Low
**Impact**: High (blocks external access)
**Mitigation**:
- Test tunnel connection before DNS routing
- Have ngrok as backup (temporary public URL)
- Document rollback to port forwarding

### Risk 2: Database Schema Import Fails

**Likelihood**: Medium (based on Day 2 experience)
**Impact**: High (blocks all API functionality)
**Mitigation**:
- Use proven Workaround A (manual export/import)
- Have SQL schema file pre-generated from production
- Test import on staging first before beta

### Risk 3: P2 Fixes Cause Frontend Issues

**Likelihood**: Low (fixes are backend middleware)
**Impact**: Medium (may need to relax CSP temporarily)
**Mitigation**:
- Test frontend locally with strict CSP before deployment
- Have CSP rollback plan (add 'unsafe-inline' temporarily)
- Monitor browser console for CSP violations during smoke tests

---

## Timeline

**Total Estimated Time**: 4 hours

| Phase | Duration | Status |
|-------|----------|--------|
| Phase 1: Environment Setup | 1 hour | ⏳ Pending |
| Phase 2: Database Setup | 30 min | ⏳ Pending |
| Phase 3: Cloudflare Tunnel | 1 hour | ⏳ Pending |
| Phase 4: Manual Smoke Tests | 1.5 hours | ⏳ Pending |
| Phase 5: Documentation | 30 min | ⏳ Pending |

**Start**: 9:00 AM
**Target Completion**: 1:00 PM (with 1-hour buffer)

---

## References

**Day 2 Documents**:
- [Day 2 Status Report](../../09-govern/01-CTO-Reports/2025-12-16-CTO-SPRINT-33-DAY2-STATUS.md)
- [Technical Debt - DB Migration](../../08-maintain/02-Technical-Debt/TD-SPRINT34-DB-MIGRATION-AUTOMATION.md)

**Sprint 33 Planning**:
- [Sprint 33 Plan](./SPRINT-33-BETA-PILOT-DEPLOYMENT.md)
- [Current Sprint Status](./CURRENT-SPRINT.md)

**Deployment Runbooks**:
- [Staging-Beta Deployment](../../06-deploy/01-Deployment-Strategy/STAGING-BETA-DEPLOYMENT-RUNBOOK.md)
- [IT Team Port Allocation](../../06-deploy/01-Deployment-Strategy/IT-TEAM-PORT-ALLOCATION-ALIGNMENT.md)

---

**Plan Created**: December 16, 2025 (End of Day 2)
**Owner**: DevOps Lead + Backend Lead
**Approved By**: CTO (pending)
**Status**: 📋 **READY FOR EXECUTION**
