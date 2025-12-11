# Staging → Beta Deployment Runbook
## SDLC Orchestrator - Production Environment

**Version**: 1.0.0
**Date**: December 13, 2025
**Owner**: DevOps Lead + IT Team
**Target Deployment**: December 18, 2025 (Sprint 32 Day 3)
**Framework**: SDLC 5.0.0
**CTO Directive**: Staging deployment with Cloudflare + port mapping

---

## 🎯 Deployment Overview

### Deployment Details

```yaml
Environment: Production (Beta Pilot)
Server: 192.168.0.223 (NQH Infrastructure)
Services: 8 (Backend, Frontend, PostgreSQL, Redis, MinIO, OPA, Prometheus, Grafana)
Public URLs:
  - Frontend: https://sdlc.nqh.vn (port 8310)
  - Backend API: https://sdlc-api.nqh.vn (port 8300)
Deployment Type: Blue-Green (with Docker Compose)
Rollback Target: <5 minutes
```

### Prerequisites Checklist

**Pre-Deployment** (Dec 16-17):
- [ ] P2 fixes completed (CORS, SECRET_KEY, CSP)
- [ ] CPO + Security Lead approvals obtained
- [ ] 30 docs updated to SDLC 5.0.0
- [ ] CTO review + approval for P2 fixes

**IT Team Coordination** (Dec 18 morning):
- [ ] Port availability verified (7 ports: 8300, 8310, 5450, 6395, 9010, 9011, 8185)
- [ ] Firewall rules configured
- [ ] Cloudflare Tunnel routes ready
- [ ] IT Team contact confirmed (dvhiep@nqh.com.vn - 0938559119)

---

## 📋 Pre-Deployment Checklist

### 1. Server Preparation (30 min)

#### Verify Disk Space

```bash
# Check available space (need 20GB+)
df -h /home/nqh/shared/SDLC-Orchestrator
df -h /var/lib/docker

# Expected output: >20GB available
# If low: Clean up old Docker images
docker system prune -a --volumes -f
```

#### Verify Memory & CPU

```bash
# Check available memory (need 4GB+)
free -h

# Check CPU load
top -bn1 | head -20

# Expected: Load average <5.0, Memory >4GB free
```

#### Verify Port Availability

```bash
# Check all 7 SDLC ports are free
ss -tulnp | grep -E '8300|8310|5450|6395|9010|9011|8185'

# Expected output: Empty (no processes listening)
# If occupied: Contact IT Team immediately
```

---

### 2. Code Preparation (15 min)

#### Pull Latest Code

```bash
cd /home/nqh/shared/SDLC-Orchestrator

# Verify on main branch
git branch --show-current
# Expected: main

# Pull latest changes
git fetch origin
git pull origin main

# Verify Sprint 32 tag (if exists)
git tag --list | grep v1.0.0-beta
# Expected: v1.0.0-beta (or similar)

# If tag doesn't exist, create one
git tag -a v1.0.0-beta -m "Sprint 32 Beta Pilot Release"
git push origin v1.0.0-beta
```

#### Verify P2 Fixes Applied

```bash
# Check CORS configuration
grep -r "CORS_ORIGINS" backend/app/core/config.py
# Expected: No wildcard "*", specific domains only

# Check SECRET_KEY validation
grep -r "validate_secret_keys" backend/app/core/security.py
# Expected: Function exists with proper validation

# Check CSP configuration
grep -r "Content-Security-Policy" backend/app/middleware/
# Expected: No unsafe-inline for main app (or documented exception)
```

---

### 3. Environment Configuration (30 min)

#### Create Production Environment File

```bash
cd /home/nqh/shared/SDLC-Orchestrator

# Copy template
cp .env.example .env.production

# Generate SECRET_KEY and JWT_SECRET_KEY
openssl rand -base64 32
# Copy output to .env.production SECRET_KEY

openssl rand -base64 32
# Copy output to .env.production JWT_SECRET_KEY

# Edit .env.production with production values
nano .env.production
```

#### Production Environment Template

```bash
# ============================================================================
# SDLC Orchestrator - Production Environment (Beta Pilot)
# ============================================================================

# Server Configuration
SERVER_HOST=192.168.0.223
ENVIRONMENT=production

# Public URLs (Cloudflare Tunnel)
FRONTEND_PUBLIC_URL=https://sdlc.nqh.vn
BACKEND_PUBLIC_URL=https://sdlc-api.nqh.vn
CORS_ORIGINS=https://sdlc.nqh.vn,https://sdlc-api.nqh.vn

# Backend API (FastAPI)
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8300
BACKEND_CONTAINER_NAME=sdlc-backend-prod
BACKEND_IMAGE=sdlc-orchestrator/backend:1.0.0-beta

# Frontend (React + Nginx)
FRONTEND_HOST=0.0.0.0
FRONTEND_PORT=8310
FRONTEND_CONTAINER_NAME=sdlc-frontend-prod
FRONTEND_IMAGE=sdlc-orchestrator/frontend:1.0.0-beta
REACT_APP_API_BASE_URL=https://sdlc-api.nqh.vn

# PostgreSQL Database
POSTGRES_HOST=sdlc-postgres-prod
POSTGRES_PORT=5450
POSTGRES_DB=sdlc_orchestrator_prod
POSTGRES_USER=sdlc_admin
POSTGRES_PASSWORD=<REPLACE_WITH_SECURE_PASSWORD_32_CHARS>
DATABASE_URL=postgresql://sdlc_admin:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:5450/sdlc_orchestrator_prod

# Redis Cache
REDIS_HOST=sdlc-redis-prod
REDIS_PORT=6395
REDIS_PASSWORD=<REPLACE_WITH_SECURE_PASSWORD>
REDIS_URL=redis://:${REDIS_PASSWORD}@${REDIS_HOST}:6395/0

# MinIO S3 Storage
MINIO_ENDPOINT=sdlc-minio-prod:9010
MINIO_API_PORT=9010
MINIO_CONSOLE_PORT=9011
MINIO_ROOT_USER=sdlc_minio_admin
MINIO_ROOT_PASSWORD=<REPLACE_WITH_SECURE_PASSWORD_32_CHARS>
MINIO_BUCKET_EVIDENCE=sdlc-evidence-vault-prod
MINIO_BUCKET_REPORTS=sdlc-reports-prod

# OPA Policy Engine
OPA_HOST=sdlc-opa-prod
OPA_PORT=8185
OPA_URL=http://sdlc-opa-prod:8185

# Security Keys (CRITICAL - Use openssl rand -base64 32)
SECRET_KEY=<REPLACE_WITH_OUTPUT_FROM_openssl_rand_base64_32>
JWT_SECRET_KEY=<REPLACE_WITH_OUTPUT_FROM_openssl_rand_base64_32>
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=30

# Monitoring (Reuse Bflow infrastructure)
PROMETHEUS_URL=http://192.168.0.223:9091
GRAFANA_URL=http://192.168.0.223:3001
```

#### Validate Environment File

```bash
# Check SECRET_KEY length (must be 32+ chars)
grep "^SECRET_KEY=" .env.production | wc -c
# Expected: >40 (includes "SECRET_KEY=" prefix)

# Check JWT_SECRET_KEY length
grep "^JWT_SECRET_KEY=" .env.production | wc -c
# Expected: >48

# Check no default passwords remain
grep -i "changeme\|password\|admin" .env.production
# Expected: Empty (no matches)

# Verify all placeholders replaced
grep "<REPLACE" .env.production
# Expected: Empty (no placeholders)
```

---

### 4. Docker Image Build (45 min)

#### Build Backend Image

```bash
cd /home/nqh/shared/SDLC-Orchestrator

# Build backend
docker build -t sdlc-orchestrator/backend:1.0.0-beta ./backend

# Verify image created
docker images | grep sdlc-orchestrator/backend
# Expected: sdlc-orchestrator/backend   1.0.0-beta   ...
```

#### Build Frontend Image

```bash
# Build frontend
docker build -t sdlc-orchestrator/frontend:1.0.0-beta ./frontend/web

# Verify image created
docker images | grep sdlc-orchestrator/frontend
# Expected: sdlc-orchestrator/frontend   1.0.0-beta   ...
```

#### Tag Latest

```bash
# Tag as latest for convenience
docker tag sdlc-orchestrator/backend:1.0.0-beta sdlc-orchestrator/backend:latest
docker tag sdlc-orchestrator/frontend:1.0.0-beta sdlc-orchestrator/frontend:latest
```

---

## 🚀 Deployment Steps

### Phase 1: Database Setup (10 min)

#### Start PostgreSQL & Redis

```bash
cd /home/nqh/shared/SDLC-Orchestrator

# Start database services only
docker-compose -f docker-compose.production.yml up -d postgres redis

# Wait for services to be healthy (30 seconds)
sleep 30

# Verify PostgreSQL is running
docker ps --filter "name=sdlc-postgres-prod" --format "table {{.Names}}\t{{.Status}}"
# Expected: sdlc-postgres-prod   Up X seconds (healthy)

# Verify Redis is running
docker ps --filter "name=sdlc-redis-prod" --format "table {{.Names}}\t{{.Status}}"
# Expected: sdlc-redis-prod   Up X seconds (healthy)
```

#### Test Database Connection

```bash
# Test PostgreSQL connection
docker exec sdlc-postgres-prod psql -U sdlc_admin -d sdlc_orchestrator_prod -c "SELECT version();"
# Expected: PostgreSQL 15.5 ... (version output)

# Test Redis connection
docker exec sdlc-redis-prod redis-cli -a ${REDIS_PASSWORD} ping
# Expected: PONG
```

#### Run Database Migrations

```bash
# Start backend temporarily for migration
docker-compose -f docker-compose.production.yml up -d backend

# Wait for backend to start (15 seconds)
sleep 15

# Run Alembic migrations
docker exec sdlc-backend-prod alembic upgrade head

# Verify migrations applied
docker exec sdlc-backend-prod alembic current
# Expected: <revision> (head)

# Check migration history
docker exec sdlc-backend-prod alembic history
# Expected: List of migrations with checkmarks

# Stop backend (will restart later)
docker-compose -f docker-compose.production.yml stop backend
```

---

### Phase 2: Seed Initial Data (15 min)

#### Load Seed Data

```bash
# Start backend again
docker-compose -f docker-compose.production.yml up -d backend

# Wait for backend to start
sleep 15

# Seed admin user + default policies
docker exec sdlc-backend-prod python -m app.scripts.seed_initial_data

# Expected output:
# ✅ Admin user created: admin@sdlc.nqh.vn
# ✅ Default policy packs loaded: 5 packs
# ✅ Default roles created: 13 roles
# ✅ Seed data completed successfully

# Verify admin user exists
docker exec sdlc-backend-prod python -c "
from app.core.database import SessionLocal
from app.models.user import User
db = SessionLocal()
admin = db.query(User).filter(User.email == 'admin@sdlc.nqh.vn').first()
print(f'Admin user: {admin.email}' if admin else 'ERROR: Admin not found')
db.close()
"
# Expected: Admin user: admin@sdlc.nqh.vn
```

---

### Phase 3: Start All Services (10 min)

#### Start Remaining Services

```bash
# Start all services (backend already running)
docker-compose -f docker-compose.production.yml up -d

# Wait for all services to be healthy (60 seconds)
sleep 60

# Verify all 8 services running
docker ps --filter "name=sdlc-*" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Expected output:
# NAMES                    STATUS                   PORTS
# sdlc-backend-prod        Up X min (healthy)       0.0.0.0:8300->8300/tcp
# sdlc-frontend-prod       Up X min (healthy)       0.0.0.0:8310->80/tcp
# sdlc-postgres-prod       Up X min (healthy)       0.0.0.0:5450->5432/tcp
# sdlc-redis-prod          Up X min (healthy)       0.0.0.0:6395->6379/tcp
# sdlc-minio-prod          Up X min (healthy)       0.0.0.0:9010->9000/tcp, 0.0.0.0:9011->9001/tcp
# sdlc-opa-prod            Up X min (healthy)       0.0.0.0:8185->8181/tcp
```

---

### Phase 4: Cloudflare Tunnel Configuration (IT Team - 15 min)

**Coordination**: IT Team (dvhiep@nqh.com.vn)

#### Configure Cloudflare Tunnel Routes

```bash
# IT Team Actions (via Cloudflare Dashboard)

# 1. Login to Cloudflare Dashboard
#    URL: https://dash.cloudflare.com/
#    Account: NQH Infrastructure

# 2. Navigate to Access → Tunnels
#    Tunnel ID: 4eb54608-b582-450e-b081-bd6bcc8f59f9

# 3. Add Public Hostname (Route 1: Frontend)
#    Subdomain: sdlc
#    Domain: nqh.vn
#    Type: HTTP
#    URL: localhost:8310
#    Path: (empty)
#    TLS Verify: Disabled (internal service)
#    No TLS Verify: Enabled
#    HTTP Host Header: (empty)
#    Origin Server Name: (empty)

# 4. Add Public Hostname (Route 2: Backend API)
#    Subdomain: sdlc-api
#    Domain: nqh.vn
#    Type: HTTP
#    URL: localhost:8300
#    Path: (empty)
#    TLS Verify: Disabled (internal service)
#    No TLS Verify: Enabled
#    HTTP Host Header: (empty)
#    Origin Server Name: (empty)

# 5. Save and Deploy
```

#### Verify Cloudflare Routes

```bash
# Test DNS resolution
nslookup sdlc.nqh.vn
# Expected: Cloudflare IP addresses

nslookup sdlc-api.nqh.vn
# Expected: Cloudflare IP addresses

# Test HTTPS access (from external)
curl -I https://sdlc.nqh.vn
# Expected: HTTP/2 200 OK

curl -I https://sdlc-api.nqh.vn/health
# Expected: HTTP/2 200 OK
```

---

### Phase 5: Smoke Tests (15 min)

#### Backend API Health Check

```bash
# Test health endpoint (internal)
curl http://localhost:8300/health

# Expected response:
# {
#   "status": "healthy",
#   "version": "1.0.0-beta",
#   "timestamp": "2025-12-18T...",
#   "services": {
#     "database": "healthy",
#     "redis": "healthy",
#     "opa": "healthy",
#     "minio": "healthy"
#   }
# }

# Test health endpoint (public via Cloudflare)
curl https://sdlc-api.nqh.vn/health
# Expected: Same as above
```

#### Frontend Health Check

```bash
# Test frontend (internal)
curl -I http://localhost:8310

# Expected: HTTP/1.1 200 OK (Nginx serving React app)

# Test frontend (public via Cloudflare)
curl -I https://sdlc.nqh.vn

# Expected: HTTP/2 200 OK
```

#### Authentication Flow Test

```bash
# Test login endpoint
curl -X POST https://sdlc-api.nqh.vn/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@sdlc.nqh.vn",
    "password": "<ADMIN_PASSWORD_FROM_SEED>"
  }'

# Expected response:
# {
#   "access_token": "eyJ...",
#   "refresh_token": "eyJ...",
#   "token_type": "bearer",
#   "expires_in": 900
# }

# Save access token for further tests
export ACCESS_TOKEN="<access_token_from_response>"
```

#### Project Creation Test

```bash
# Test project creation
curl -X POST https://sdlc-api.nqh.vn/api/v1/projects \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Beta Pilot Test Project",
    "description": "Smoke test project",
    "team_size": "STANDARD",
    "sdlc_tier": "PROFESSIONAL"
  }'

# Expected response:
# {
#   "id": "uuid",
#   "name": "Beta Pilot Test Project",
#   "status": "ACTIVE",
#   "created_at": "2025-12-18T..."
# }
```

#### E2E Test Suite (Critical Journeys)

```bash
cd /home/nqh/shared/SDLC-Orchestrator/tests/e2e

# Set environment for E2E tests
export PLAYWRIGHT_BASE_URL=https://sdlc.nqh.vn
export API_BASE_URL=https://sdlc-api.nqh.vn
export TEST_ADMIN_EMAIL=admin@sdlc.nqh.vn
export TEST_ADMIN_PASSWORD=<ADMIN_PASSWORD_FROM_SEED>

# Run smoke test suite (5 critical journeys)
npm run test:smoke

# Expected output:
# ✅ Journey 1: User login (admin@sdlc.nqh.vn)
# ✅ Journey 2: Create project
# ✅ Journey 3: Upload evidence
# ✅ Journey 4: Evaluate Gate G0.1
# ✅ Journey 5: View dashboard
#
# 5 passed (5/5) - 100% success rate
```

---

### Phase 6: Monitoring Setup (15 min)

#### Configure Prometheus Scrape Targets

```bash
# Edit Bflow Prometheus config
nano /home/nqh/shared/Bflow-Platform/infrastructure/monitoring/prometheus/prometheus.yml

# Add SDLC scrape configs:
scrape_configs:
  # ... existing configs ...

  # SDLC Orchestrator Backend
  - job_name: 'sdlc-backend'
    static_configs:
      - targets: ['192.168.0.223:8300']
    metrics_path: '/metrics'
    scrape_interval: 15s
    scrape_timeout: 10s

  # SDLC Orchestrator PostgreSQL
  - job_name: 'sdlc-postgres'
    static_configs:
      - targets: ['192.168.0.223:5450']
    scrape_interval: 30s
    scrape_timeout: 10s

  # SDLC Orchestrator Redis
  - job_name: 'sdlc-redis'
    static_configs:
      - targets: ['192.168.0.223:6395']
    scrape_interval: 30s
    scrape_timeout: 10s

# Save and reload Prometheus
docker restart bflow-staging-prometheus

# Wait for restart
sleep 10
```

#### Verify Prometheus Scraping

```bash
# Check Prometheus targets
curl http://192.168.0.223:9091/api/v1/targets | jq '.data.activeTargets[] | select(.labels.job | contains("sdlc"))'

# Expected: 3 targets (sdlc-backend, sdlc-postgres, sdlc-redis) with state="up"
```

#### Import Grafana Dashboards

```bash
# Copy SDLC dashboards to Grafana
docker cp /home/nqh/shared/SDLC-Orchestrator/infrastructure/monitoring/grafana/dashboards/sdlc-overview.json \
  bflow-staging-grafana:/var/lib/grafana/dashboards/

# Restart Grafana to load dashboards
docker restart bflow-staging-grafana

# Wait for restart
sleep 10

# Verify dashboard imported
curl -u admin:admin http://192.168.0.223:3001/api/dashboards/db/sdlc-overview

# Expected: Dashboard JSON response
```

---

## ✅ Post-Deployment Verification

### Health SLOs (Service Level Objectives)

| Service | SLO | Verification Command | Expected Result |
|---------|-----|----------------------|-----------------|
| **Backend API** | 99.9% uptime | `curl -I https://sdlc-api.nqh.vn/health` | HTTP 200 OK |
| **Frontend** | 99.9% uptime | `curl -I https://sdlc.nqh.vn` | HTTP 200 OK |
| **PostgreSQL** | <10ms query p95 | Check Grafana | p95 < 10ms |
| **Redis** | <5ms latency p95 | Check Grafana | p95 < 5ms |
| **API p95 Latency** | <100ms | Check Grafana | p95 < 100ms |

### Verification Checklist

- [ ] All 8 services running (docker ps)
- [ ] All services healthy (docker ps --filter health)
- [ ] Backend health check: 200 OK
- [ ] Frontend accessible: 200 OK
- [ ] Authentication working (login test)
- [ ] Project creation working (API test)
- [ ] E2E smoke tests: 5/5 passed
- [ ] Prometheus scraping: 3/3 targets UP
- [ ] Grafana dashboards: 1+ dashboards loaded
- [ ] Cloudflare routes: 2/2 routes active

---

## 🔄 Rollback Procedure (<5 min)

### Rollback Triggers

Execute rollback if ANY of these occur:
1. Health check fails (any service unhealthy >5 min)
2. E2E smoke tests fail (any journey fails)
3. API p95 latency >150ms (1.5x target)
4. Database connection lost
5. Critical bug discovered (P0)

### Rollback Steps

```bash
# 1. Stop all SDLC services (30 seconds)
cd /home/nqh/shared/SDLC-Orchestrator
docker-compose -f docker-compose.production.yml down

# 2. Verify all containers stopped
docker ps --filter "name=sdlc-*"
# Expected: Empty (no SDLC containers)

# 3. Remove Cloudflare routes (IT Team - 2 min)
# - Remove sdlc.nqh.vn route
# - Remove sdlc-api.nqh.vn route

# 4. Verify rollback complete
curl -I https://sdlc.nqh.vn
# Expected: 404 Not Found (route removed)

# 5. Notify stakeholders
# - Slack: #sdlc-team
# - Message: "Deployment rolled back due to <reason>. Investigating."

# Total rollback time: <5 min
```

---

## 📊 Monitoring & Alerts

### Alert Thresholds (CTO Mandate)

```yaml
# Grafana Alert Rules

# API Latency Warning
Alert: SDLC API p95 Latency High
Condition: p95 > 100ms for 15 minutes
Severity: Warning
Action: Notify #sdlc-team Slack

# API Latency Critical
Alert: SDLC API p95 Latency Critical
Condition: p95 > 150ms for 5 minutes
Severity: Critical
Action: Page on-call, notify #sdlc-team

# Error Rate Warning
Alert: SDLC Error Rate High
Condition: error_rate > 1% for 10 minutes
Severity: Warning
Action: Notify #sdlc-team

# Error Rate Critical
Alert: SDLC Error Rate Critical
Condition: error_rate > 5% for 5 minutes
Severity: Critical
Action: Page on-call, notify #sdlc-team

# Resource Usage Warning
Alert: SDLC High Resource Usage
Condition: CPU > 70% OR Memory > 70% OR Disk > 80%
Severity: Warning
Action: Notify #sdlc-team

# Resource Usage Critical
Alert: SDLC Critical Resource Usage
Condition: CPU > 90% OR Memory > 90% OR Disk > 90%
Severity: Critical
Action: Page on-call, notify #sdlc-team

# Service Health Critical
Alert: SDLC Service Down
Condition: Any service unhealthy for 1 minute
Severity: Critical
Action: Page on-call, notify #sdlc-team
```

---

## 📞 Incident Response

### On-Call Rotation

**Coverage**: 24/7 during beta pilot (Dec 18 - Jan 18)

| Week | Primary | Secondary |
|------|---------|-----------|
| Week 1 (Dec 18-24) | PM | Backend Lead |
| Week 2 (Dec 25-31) | Backend Lead | PM |
| Week 3 (Jan 1-7) | PM | Backend Lead |
| Week 4 (Jan 8-14) | Backend Lead | PM |

### Escalation Path

```
1. On-Call Engineer (PM / Backend Lead)
   ↓ If not resolved in 30 min
2. Tech Lead + CTO
   ↓ If critical incident (data loss, security breach)
3. CEO + CPO
```

### Incident SLA

| Priority | Description | Response Time | Resolution Time |
|----------|-------------|---------------|-----------------|
| **P0** | Service down, data loss | <30 min | <4 hours |
| **P1** | Feature broken, degraded performance | <2 hours | <24 hours |
| **P2** | Minor bug, UI issue | <1 day | <3 days |
| **P3** | Feature request, cosmetic issue | <3 days | Backlog |

---

## 📝 Deployment Log Template

```
## Deployment Log - <DATE>

### Pre-Deployment
- [ ] P2 fixes verified (CORS, SECRET_KEY, CSP)
- [ ] Code pulled (branch: main, tag: v1.0.0-beta)
- [ ] Environment file created (.env.production)
- [ ] Docker images built (backend, frontend)

### Deployment Execution
- Start time: <TIME>
- Database setup: <DURATION> (target: 10 min)
- Seed data: <DURATION> (target: 15 min)
- Services started: <DURATION> (target: 10 min)
- Cloudflare config: <DURATION> (target: 15 min, IT Team)
- Smoke tests: <DURATION> (target: 15 min)
- End time: <TIME>
- **Total duration**: <TOTAL> (target: <2 hours)

### Verification Results
- Services health: <X>/8 healthy
- Backend health: <PASS/FAIL>
- Frontend health: <PASS/FAIL>
- Authentication: <PASS/FAIL>
- E2E smoke tests: <X>/5 passed
- Prometheus scraping: <X>/3 targets UP
- Grafana dashboards: <PASS/FAIL>

### Issues Encountered
- Issue 1: <DESCRIPTION> - Resolved: <YES/NO>
- Issue 2: <DESCRIPTION> - Resolved: <YES/NO>

### Rollback Performed
- YES / NO
- Reason: <IF YES, EXPLAIN>

### Sign-Off
- DevOps Lead: <NAME> - <TIMESTAMP>
- IT Team: <NAME> - <TIMESTAMP>
- CTO: <NAME> - <TIMESTAMP>
```

---

## 📚 Reference Documents

**Deployment Guides**:
- [Docker Deployment Guide](../DOCKER-DEPLOYMENT-GUIDE.md)
- [IT Team Port Allocation](./IT-TEAM-PORT-ALLOCATION-ALIGNMENT.md)
- [Monitoring Setup Guide](../MONITORING-OBSERVABILITY-GUIDE.md)

**Sprint Plans**:
- [Sprint 32 Detailed Plan](../../03-Development-Implementation/02-Sprint-Plans/SPRINT-32-BETA-PILOT-DEPLOYMENT.md)
- [Current Sprint](../../03-Development-Implementation/02-Sprint-Plans/CURRENT-SPRINT.md)

**Executive Reports**:
- [PM Deployment Readiness](../../09-Executive-Reports/03-PM-Reports/2025-12-13-PM-DEPLOYMENT-READINESS-REVIEW.md)
- [CTO Gate G3 Approval](../../09-Executive-Reports/01-CTO-Reports/2025-12-12-CTO-SPRINT-31-DAY5.md)

---

**Runbook Status**: FINAL - Ready for Dec 18 Deployment
**Owner**: DevOps Lead + IT Team (dvhiep@nqh.com.vn)
**Reviewer**: CTO
**Framework**: SDLC 5.0.0
**Version**: 1.0.0

---

*"<5 minute rollback capability is non-negotiable. Test it before deployment."*

**Created**: December 13, 2025
**Last Updated**: December 13, 2025
**Next Review**: Post-deployment (Dec 18, 2025)
