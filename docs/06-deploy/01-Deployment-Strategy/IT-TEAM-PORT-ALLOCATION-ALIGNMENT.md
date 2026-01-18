# IT Team Port Allocation Alignment
## SDLC Orchestrator Deployment - Production Environment

**Date**: December 13, 2025
**Author**: PM + DevOps Lead
**IT Team Contact**: dvhiep@nqh.com.vn (0938559119)
**Status**: ✅ APPROVED (Nov 29, 2025)
**Framework**: SDLC 5.1.3

---

## Executive Summary

**Status**: ✅ PORT ALLOCATION APPROVED

SDLC Orchestrator port allocations were **APPROVED** by IT Team on November 29, 2025 (documented in [PORT_ALLOCATION_MANAGEMENT.md](file:///home/nqh/shared/models/docs/admin/PORT_ALLOCATION_MANAGEMENT.md) v2.1). This document confirms alignment and provides deployment coordination details.

### Allocated Ports (7 Services)

| Port | Service | Status |
|------|---------|--------|
| **8300** | Backend API (FastAPI) | ✅ Approved |
| **8310** | Frontend (React/Nginx) | ✅ Approved |
| 5450 | PostgreSQL Database | ✅ Approved |
| 6395 | Redis Cache/Sessions | ✅ Approved |
| 9010 | MinIO S3 API | ✅ Approved |
| 9011 | MinIO Console | ✅ Approved |
| 8185 | OPA Policy Engine | ✅ Approved |

**Total Ports**: 7 (within approved range: 8300-8399)

---

## 📋 Port Allocation Details

### SDLC Orchestrator Production Stack

**Reference**: [PORT_ALLOCATION_MANAGEMENT.md](file:///home/nqh/shared/models/docs/admin/PORT_ALLOCATION_MANAGEMENT.md) Section "SDLC Orchestrator - Production (7 Services)"

```yaml
Platform: SDLC Orchestrator
Environment: Production
Server: 192.168.0.223 (NQH Infrastructure)
Approval Date: November 29, 2025
IT Team: dvhiep@nqh.com.vn
Document Version: 2.1
```

### Port Mapping Table

| Port | Service | Container Name | Purpose | Protocol | Public URL |
|------|---------|----------------|---------|----------|------------|
| **8300** | **SDLC Backend** | `sdlc-backend-prod` | **FastAPI REST API** | HTTP | https://sdlc-api.nhatquangholding.com |
| **8310** | **SDLC Frontend** | `sdlc-frontend-prod` | **React SPA (Nginx)** | HTTP | https://sdlc.nqh.vn |
| 5450 | PostgreSQL | `sdlc-postgres-prod` | SDLC Database | TCP | Internal only |
| 6395 | Redis | `sdlc-redis-prod` | Cache/Sessions | TCP | Internal only |
| 9010 | MinIO API | `sdlc-minio-prod` | Evidence Storage (S3 API) | HTTP | Internal only |
| 9011 | MinIO Console | `sdlc-minio-prod` | Storage Admin UI | HTTP | Internal only |
| 8185 | OPA | `sdlc-opa-prod` | Policy Engine | HTTP | Internal only |

---

## 🌐 Cloudflare Tunnel Configuration

### Reserved Public URLs

**Tunnel ID**: `4eb54608-b582-450e-b081-bd6bcc8f59f9`

| Subdomain | Public URL | Local Service | Port | Status | Notes |
|-----------|------------|---------------|------|--------|-------|
| **sdlc** | **https://sdlc.nqh.vn** | localhost:8310 | 8310 | 🆕 Approved | SDLC Frontend (React SPA) |
| **sdlc-api** | **https://sdlc-api.nhatquangholding.com** | localhost:8300 | 8300 | 🆕 Approved | SDLC Backend API (FastAPI) |

### Tunnel Configuration (Cloudflare Dashboard)

```yaml
# Cloudflare Tunnel Route 1: Frontend
Subdomain: sdlc
Public Hostname: sdlc.nqh.vn
Type: HTTP
URL: localhost:8310
Status: Approved (Nov 29, 2025)

# Cloudflare Tunnel Route 2: Backend API
Subdomain: sdlc-api
Public Hostname: sdlc-api.nhatquangholding.com
Type: HTTP
URL: localhost:8300
Status: Approved (Nov 29, 2025)
```

**Action Required**: Configure these routes in Cloudflare Tunnel dashboard before deployment.

---

## 🔍 Port Conflict Verification

### Conflict Check (December 13, 2025)

Verified against current NQH infrastructure:

| Port | SDLC Service | Existing Service | Status |
|------|--------------|------------------|--------|
| 8300 | SDLC Backend | None | ✅ Available |
| 8310 | SDLC Frontend | None | ✅ Available |
| 5450 | PostgreSQL | None | ✅ Available |
| 6395 | Redis | None | ✅ Available |
| 9010 | MinIO API | None | ✅ Available |
| 9011 | MinIO Console | None | ✅ Available |
| 8185 | OPA | None | ✅ Available |

**Result**: ✅ NO CONFLICTS (All 7 ports available)

### Nearby Port Usage

**8300 Range**:
- 8300 → SDLC Backend ✅
- 8301-8309 → Reserved for SDLC future services
- 8310 → SDLC Frontend ✅
- 8311-8399 → Reserved for SDLC expansion

**Isolation Strategy**: SDLC Orchestrator has dedicated 8300-8399 range (100 ports reserved).

---

## 🐳 Docker Compose Configuration

### Production Environment Variables

```bash
# SDLC Orchestrator - Production Environment
# File: /home/nqh/shared/SDLC-Orchestrator/.env.production

# ============================================================================
# Server Configuration
# ============================================================================
SERVER_HOST=192.168.0.223
ENVIRONMENT=production

# ============================================================================
# Public URLs (Cloudflare Tunnel)
# ============================================================================
FRONTEND_PUBLIC_URL=https://sdlc.nqh.vn
BACKEND_PUBLIC_URL=https://sdlc-api.nhatquangholding.com
CORS_ORIGINS=https://sdlc.nqh.vn,https://sdlc-api.nhatquangholding.com

# ============================================================================
# Backend API (FastAPI)
# ============================================================================
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8300
BACKEND_CONTAINER_NAME=sdlc-backend-prod
BACKEND_IMAGE=sdlc-orchestrator/backend:1.0.0

# ============================================================================
# Frontend (React + Nginx)
# ============================================================================
FRONTEND_HOST=0.0.0.0
FRONTEND_PORT=8310
FRONTEND_CONTAINER_NAME=sdlc-frontend-prod
FRONTEND_IMAGE=sdlc-orchestrator/frontend:1.0.0
REACT_APP_API_BASE_URL=https://sdlc-api.nhatquangholding.com

# ============================================================================
# PostgreSQL Database
# ============================================================================
POSTGRES_HOST=sdlc-postgres-prod
POSTGRES_PORT=5450
POSTGRES_DB=sdlc_orchestrator_prod
POSTGRES_USER=sdlc_admin
POSTGRES_PASSWORD=<SECURE_PASSWORD_32_CHARS>
POSTGRES_CONTAINER_NAME=sdlc-postgres-prod
POSTGRES_IMAGE=postgres:15.5-alpine
DATABASE_URL=postgresql://sdlc_admin:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:5450/sdlc_orchestrator_prod

# ============================================================================
# Redis Cache
# ============================================================================
REDIS_HOST=sdlc-redis-prod
REDIS_PORT=6395
REDIS_PASSWORD=<SECURE_REDIS_PASSWORD>
REDIS_CONTAINER_NAME=sdlc-redis-prod
REDIS_IMAGE=redis:7.2-alpine
REDIS_URL=redis://:${REDIS_PASSWORD}@${REDIS_HOST}:6395/0

# ============================================================================
# MinIO S3 Storage
# ============================================================================
MINIO_ENDPOINT=sdlc-minio-prod:9010
MINIO_API_PORT=9010
MINIO_CONSOLE_PORT=9011
MINIO_ROOT_USER=sdlc_minio_admin
MINIO_ROOT_PASSWORD=<SECURE_MINIO_PASSWORD_32_CHARS>
MINIO_CONTAINER_NAME=sdlc-minio-prod
MINIO_IMAGE=minio/minio:latest
MINIO_BUCKET_EVIDENCE=sdlc-evidence-vault-prod
MINIO_BUCKET_REPORTS=sdlc-reports-prod
MINIO_BUCKET_ORCHDOCS=sdlc-orchdocs-prod

# ============================================================================
# OPA Policy Engine
# ============================================================================
OPA_HOST=sdlc-opa-prod
OPA_PORT=8185
OPA_CONTAINER_NAME=sdlc-opa-prod
OPA_IMAGE=openpolicyagent/opa:0.58.0-rootless
OPA_URL=http://sdlc-opa-prod:8185

# ============================================================================
# Monitoring (Reuse existing NQH infrastructure)
# ============================================================================
PROMETHEUS_URL=http://192.168.0.223:9091  # Bflow Prometheus
GRAFANA_URL=http://192.168.0.223:3001    # Bflow Grafana

# ============================================================================
# Security
# ============================================================================
SECRET_KEY=<GENERATE_WITH_openssl_rand_-base64_32>
JWT_SECRET_KEY=<GENERATE_WITH_openssl_rand_-base64_32>
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=30

# ============================================================================
# GitHub Integration (Optional)
# ============================================================================
GITHUB_APP_ID=
GITHUB_APP_PRIVATE_KEY=
GITHUB_WEBHOOK_SECRET=
```

### Docker Compose Port Mapping

```yaml
# docker-compose.production.yml excerpt
version: '3.8'

services:
  backend:
    container_name: sdlc-backend-prod
    ports:
      - "8300:8300"  # Backend API (FastAPI)

  frontend:
    container_name: sdlc-frontend-prod
    ports:
      - "8310:80"    # Frontend (Nginx serves on 80, mapped to 8310)

  postgres:
    container_name: sdlc-postgres-prod
    ports:
      - "5450:5432"  # PostgreSQL (internal 5432 → external 5450)

  redis:
    container_name: sdlc-redis-prod
    ports:
      - "6395:6379"  # Redis (internal 6379 → external 6395)

  minio:
    container_name: sdlc-minio-prod
    ports:
      - "9010:9000"  # MinIO API (internal 9000 → external 9010)
      - "9011:9001"  # MinIO Console (internal 9001 → external 9011)

  opa:
    container_name: sdlc-opa-prod
    ports:
      - "8185:8181"  # OPA (internal 8181 → external 8185)
```

---

## 📊 Alignment with IT Team Standards

### Compliance Checklist

| IT Standard | SDLC Orchestrator | Status |
|-------------|-------------------|--------|
| **Port Range Allocation** | 8300-8399 (100 ports reserved) | ✅ Compliant |
| **Container Naming** | `sdlc-<service>-prod` | ✅ Compliant |
| **Network Isolation** | Docker network `sdlc-network-prod` | ✅ Compliant |
| **Public-Facing via Cloudflare** | `sdlc.nqh.vn`, `sdlc-api.nhatquangholding.com` | ✅ Approved |
| **Database Port Prefix** | 5xxx range (5450) | ✅ Compliant |
| **Redis Port Prefix** | 6xxx range (6395) | ✅ Compliant |
| **Service Port Range** | 8xxx range (8300, 8310, 8185) | ✅ Compliant |
| **Storage Port Range** | 9xxx range (9010, 9011) | ✅ Compliant |

**Overall Compliance**: ✅ 100% (8/8 criteria met)

---

## 🔒 Security Considerations

### Internal-Only Services (No Public Access)

The following services are **NOT exposed** via Cloudflare Tunnel (internal network only):

1. **PostgreSQL** (port 5450)
   - Direct access blocked by firewall
   - Only accessible from Docker network `sdlc-network-prod`

2. **Redis** (port 6395)
   - Password-protected
   - Only accessible from Docker network

3. **MinIO** (ports 9010, 9011)
   - API (9010): Backend API only
   - Console (9011): Admin access only (optional reverse proxy)

4. **OPA** (port 8185)
   - Policy engine accessed by Backend API only
   - No external exposure

### Public-Facing Services (via Cloudflare Tunnel)

1. **Frontend** (https://sdlc.nqh.vn → localhost:8310)
   - React SPA served via Nginx
   - TLS termination at Cloudflare
   - DDoS protection enabled

2. **Backend API** (https://sdlc-api.nhatquangholding.com → localhost:8300)
   - FastAPI REST API
   - TLS termination at Cloudflare
   - Rate limiting: 100 req/min/user (application-level)

---

## 🚀 Deployment Coordination

### IT Team Coordination Points

**Contact**: dvhiep@nqh.com.vn (0938559119)

### Pre-Deployment (Sprint 32 Day 1-2)

- [ ] **Verify Port Availability** (IT Team)
  - Run `ss -tulnp | grep -E '8300|8310|5450|6395|9010|9011|8185'`
  - Confirm all 7 ports are free

- [ ] **Configure Firewall Rules** (IT Team)
  - Allow internal Docker network communication
  - Block external access to 5450, 6395, 9010, 9011, 8185
  - Allow Cloudflare IPs to 8300, 8310

- [ ] **Setup Cloudflare Tunnel Routes** (IT Team + PM)
  - Add route: `sdlc.nqh.vn → localhost:8310`
  - Add route: `sdlc-api.nhatquangholding.com → localhost:8300`
  - Test DNS propagation

### Deployment Day (Sprint 32 Day 3)

- [ ] **Start Services** (DevOps Lead)
  - `cd /home/nqh/shared/SDLC-Orchestrator`
  - `docker-compose -f docker-compose.production.yml up -d`
  - Verify all 7 containers healthy

- [ ] **Verify Port Binding** (DevOps + IT Team)
  - `docker ps --format "table {{.Names}}\t{{.Ports}}" | grep sdlc`
  - Confirm all ports listening

- [ ] **Test Public URLs** (PM + IT Team)
  - Frontend: `curl -I https://sdlc.nqh.vn`
  - Backend: `curl -I https://sdlc-api.nhatquangholding.com/health`

### Post-Deployment (Sprint 32 Day 4-5)

- [ ] **Monitor Port Usage** (IT Team)
  - Check for unexpected traffic
  - Verify firewall rules effective

- [ ] **Update Documentation** (PM)
  - Update PORT_ALLOCATION_MANAGEMENT.md status to "Active"
  - Document actual deployment date

---

## 📈 Monitoring Integration

### Reuse Existing NQH Infrastructure

**Strategy**: SDLC Orchestrator integrates with existing monitoring stack (no new ports needed).

| Service | Existing Port | Container | Purpose |
|---------|---------------|-----------|---------|
| Prometheus | 9091 | `bflow-staging-prometheus` | Metrics collection |
| Grafana | 3001 | `bflow-staging-grafana` | Dashboard visualization |

### SDLC Orchestrator Metrics Endpoints

```yaml
Backend API Metrics:
  - URL: http://localhost:8300/metrics
  - Format: Prometheus
  - Scrape Interval: 15s

PostgreSQL Exporter:
  - URL: http://localhost:5450/metrics (via postgres_exporter sidecar)
  - Format: Prometheus
  - Scrape Interval: 30s

Redis Exporter:
  - URL: http://localhost:6395/metrics (via redis_exporter sidecar)
  - Format: Prometheus
  - Scrape Interval: 30s
```

**Configuration**: Add scrape targets to Bflow Prometheus (`/home/nqh/shared/Bflow-Platform/infrastructure/monitoring/prometheus/prometheus.yml`)

---

## 🔧 Troubleshooting

### Port Conflict Resolution

**Scenario**: Port already in use during deployment.

```bash
# 1. Identify process using port (e.g., 8300)
sudo lsof -i :8300

# 2. Check Docker containers
docker ps | grep 8300

# 3. If conflict exists, coordinate with IT Team
# Contact: dvhiep@nqh.com.vn (0938559119)

# 4. Emergency fallback ports (if needed)
# Backend:  8300 → 8320 (fallback)
# Frontend: 8310 → 8321 (fallback)
```

### Service Health Check

```bash
# Check all SDLC services
docker ps --filter "name=sdlc-*" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Test internal connectivity
docker exec sdlc-backend-prod curl -I http://sdlc-postgres-prod:5432
docker exec sdlc-backend-prod curl -I http://sdlc-redis-prod:6379

# Test public URLs
curl -I https://sdlc.nqh.vn
curl https://sdlc-api.nhatquangholding.com/health
```

---

## 📋 Deployment Checklist

### IT Team Pre-Deployment

- [ ] Verify port availability (all 7 ports)
- [ ] Configure firewall rules
- [ ] Setup Cloudflare Tunnel routes (2 routes)
- [ ] Test DNS resolution for `sdlc.nqh.vn` and `sdlc-api.nhatquangholding.com`
- [ ] Verify Docker network `sdlc-network-prod` created

### DevOps Deployment

- [ ] Pull Docker images (6 images)
- [ ] Create production environment file (`.env.production`)
- [ ] Run database migrations (`alembic upgrade head`)
- [ ] Start services (`docker-compose up -d`)
- [ ] Verify all containers healthy (7/7)
- [ ] Seed initial data (admin user, default policies)

### Post-Deployment Verification

- [ ] Test public URLs (frontend + backend)
- [ ] Verify internal connectivity (DB, Redis, MinIO, OPA)
- [ ] Check Prometheus scraping metrics
- [ ] Review Grafana dashboards
- [ ] Test authentication flow
- [ ] Execute smoke tests (5 critical user journeys)

---

## 📞 Contact Information

### IT Team

**Primary Contact**: dvhiep@nqh.com.vn
**Phone**: 0938559119
**Availability**: Business hours + on-call for production issues

### SDLC Orchestrator Team

| Role | Contact | Availability |
|------|---------|--------------|
| DevOps Lead | devops@sdlc-team.local | Business hours + on-call |
| Backend Lead | backend@sdlc-team.local | Business hours |
| PM/PJM | pm@sdlc-team.local | Business hours |

### Escalation Path

```
1. DevOps Lead → Troubleshoot service issues
2. IT Team (dvhiep) → Network/port/firewall issues
3. CTO → Architecture/security decisions
```

---

## 📚 Reference Documents

**NQH Infrastructure**:
- [PORT_ALLOCATION_MANAGEMENT.md](file:///home/nqh/shared/models/docs/admin/PORT_ALLOCATION_MANAGEMENT.md) (v2.1)
- [AUTO_START_SERVICES.md](file:///home/nqh/shared/models/docs/admin/AUTO_START_SERVICES.md)
- [CLOUDFLARE_ADD_SOP_DOMAIN.md](file:///home/nqh/shared/models/docs/admin/CLOUDFLARE_ADD_SOP_DOMAIN.md)

**SDLC Orchestrator**:
- [Docker Deployment Guide](../DOCKER-DEPLOYMENT-GUIDE.md)
- [Kubernetes Deployment Guide](../KUBERNETES-DEPLOYMENT-GUIDE.md)
- [Monitoring Setup Guide](../MONITORING-OBSERVABILITY-GUIDE.md)
- [Security Baseline](../../02-Design-Architecture/06-Security-RBAC/Security-Baseline.md)

---

## 📝 Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0.0 | Dec 13, 2025 | Initial alignment document post-Gate G3 approval | PM + DevOps Lead |

---

**Document Status**: FINAL - Ready for Deployment
**IT Team Approval**: ✅ APPROVED (Nov 29, 2025)
**Port Allocation**: ✅ CONFIRMED (7 ports)
**Cloudflare Routes**: 🆕 PENDING CONFIGURATION (2 routes)
**Framework**: SDLC 5.1.3

---

*"Coordination with IT Team ensures zero deployment conflicts. Pre-approved ports = smooth production launch."*

**Generated**: December 13, 2025
**Owner**: PM + DevOps Lead + IT Team
**Review**: Pre-deployment verification (Sprint 32 Day 1)
