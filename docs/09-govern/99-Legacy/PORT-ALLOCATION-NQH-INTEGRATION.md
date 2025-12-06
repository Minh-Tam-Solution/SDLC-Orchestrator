# SDLC Orchestrator - NQH Infrastructure Port Integration

**Version**: 1.1.0
**Date**: November 29, 2025
**Status**: ✅ APPROVED - IT Admin Approved
**Contact**: IT Team - dvhiep@nqh.com.vn - 0938559119
**Approval Date**: November 29, 2025

---

## Overview

This document proposes port allocation for **SDLC Orchestrator** to be integrated into the NQH Infrastructure (192.168.0.223) alongside existing platforms (Bflow, NQH Bot, SOP Generator, etc.).

---

## Proposed Port Allocation for SDLC Orchestrator

### Development Environment (Local)

| Port | Service | Container | Purpose | Status |
|------|---------|-----------|---------|--------|
| 8000 | FastAPI Backend | `sdlc-backend` | REST API | ✅ Configured |
| 3000 | Vite Dev Server | `N/A (local)` | Frontend Dev | ✅ Configured |
| 5432 | PostgreSQL | `sdlc-postgres` | Database | ✅ Configured |
| 6379 | Redis | `sdlc-redis` | Cache/Sessions | ✅ Configured |
| 9000 | MinIO API | `sdlc-minio` | Evidence Storage | ✅ Configured |
| 9001 | MinIO Console | `sdlc-minio` | Storage Admin | ✅ Configured |
| 8181 | OPA | `sdlc-opa` | Policy Engine | ✅ Configured |

### Staging Environment (Offset Ports - Avoids Dev Conflict)

| Port | Service | Container | Purpose | Status |
|------|---------|-----------|---------|--------|
| 8000 | FastAPI Backend | `sdlc-staging-backend` | REST API | ✅ Active |
| 4000 | Nginx Frontend | `sdlc-staging-frontend` | Production Build | ✅ Active |
| 5433 | PostgreSQL | `sdlc-staging-postgres` | Staging DB | ✅ Active |
| 6380 | Redis | `sdlc-staging-redis` | Staging Cache | ✅ Active |
| 9002 | MinIO API | `sdlc-staging-minio` | Evidence Storage | ✅ Active |
| 9003 | MinIO Console | `sdlc-staging-minio` | Storage Admin | ✅ Active |
| 8182 | OPA | `sdlc-staging-opa` | Policy Engine | ✅ Active |

---

## Proposed NQH Production Port Allocation

**Recommended Port Range**: `8300-8399` (SDLC Platform)

Following NQH allocation strategy:
- AI Infrastructure: 3000-3100, 8080-8200
- Bflow Staging: 8100-8199
- **SDLC Orchestrator: 8300-8399** (NEW)

### Production Ports (Proposed for 192.168.0.223)

| Port | Service | Container | Purpose | Status |
|------|---------|-----------|---------|--------|
| **8300** | **SDLC Backend** | `sdlc-backend-prod` | **FastAPI REST API** | ✅ Approved |
| **8310** | **SDLC Frontend** | `sdlc-frontend-prod` | **React SPA (Nginx)** | ✅ Approved |
| **5450** | PostgreSQL | `sdlc-postgres-prod` | SDLC Database | ✅ Approved |
| **6395** | Redis | `sdlc-redis-prod` | SDLC Cache | ✅ Approved |
| **9010** | MinIO API | `sdlc-minio-prod` | Evidence Storage | ✅ Approved |
| **9011** | MinIO Console | `sdlc-minio-prod` | Storage Admin | ✅ Approved |
| **8185** | OPA | `sdlc-opa-prod` | Policy Engine | ✅ Approved |

---

## Cloudflare Tunnel Route (Approved)

| Subdomain | Public URL | Local Service | Port | Status |
|-----------|------------|---------------|------|--------|
| sdlc | https://sdlc.nqh.vn | localhost:8310 | 8310 | ✅ Approved |
| sdlc-api | https://sdlc-api.nqh.vn | localhost:8300 | 8300 | ✅ Approved |

---

## Port Conflict Analysis

### No Conflicts with Existing NQH Infrastructure

| Existing Service | Port | SDLC Proposed | Conflict? |
|------------------|------|---------------|-----------|
| Open WebUI | 3000 | 8300 (backend) | ❌ No |
| Bflow Auth | 8100 | 8310 (frontend) | ❌ No |
| Bflow Financial | 8101 | N/A | ❌ No |
| Kafka UI | 9090 | 9010 (MinIO) | ❌ No |
| Sentry | 9099 | N/A | ❌ No |
| ClickHouse HTTP | 8123 | N/A | ❌ No |
| Superset | 8088 | N/A | ❌ No |

### Reserved Port Ranges (Avoid)

| Range | Reserved For | Status |
|-------|--------------|--------|
| 3000-3100 | AI Infrastructure | ⚠️ Avoid |
| 6100-6500 | N8N Workflow | ⚠️ Avoid |
| 7100-7500 | NQH Bot | ⚠️ Avoid |
| 8100-8199 | Bflow Staging | ⚠️ Avoid |
| **8300-8399** | **SDLC Orchestrator** | ✅ Proposed |

---

## Environment Variable Configuration

All ports are configurable via environment variables:

```bash
# Backend
API_PORT=8300
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5450/sdlc_orchestrator
REDIS_URL=redis://localhost:6395/0
MINIO_ENDPOINT=localhost:9010
OPA_URL=http://localhost:8185

# Frontend
FRONTEND_PORT=8310
VITE_API_URL=http://localhost:8300

# CORS
ALLOWED_ORIGINS=http://localhost:8310,https://sdlc.nqh.vn
```

---

## Action Items for IT Team

1. **Review Port Allocation**: Confirm ports 8300-8399 are available
2. **Database Setup**: Create PostgreSQL database on port 5450
3. **Redis Instance**: Configure Redis on port 6395
4. **MinIO Setup**: Deploy MinIO on ports 9010/9011
5. **Cloudflare Tunnel**: Add routes for sdlc.nqh.vn and sdlc-api.nqh.vn
6. **Firewall Rules**: Open necessary ports for internal access

---

## Integration with Existing NQH Monitoring

| Component | Integration Point | Configuration |
|-----------|-------------------|---------------|
| Prometheus | `sdlc-backend:8300/metrics` | Add to scrape targets |
| Grafana | Import SDLC dashboards | Port 3001 (existing) |
| Sentry | `SENTRY_DSN` env var | Use existing Sentry :9099 |
| ELK Stack | Filebeat → Elasticsearch | Log shipping |

---

## Summary

| Environment | Backend | Frontend | Database | Redis | MinIO | OPA |
|-------------|---------|----------|----------|-------|-------|-----|
| Development | 8000 | 3000 | 5432 | 6379 | 9000/9001 | 8181 |
| Staging | 8000 | 4000 | 5433 | 6380 | 9002/9003 | 8182 |
| **Production** | **8300** | **8310** | **5450** | **6395** | **9010/9011** | **8185** |

---

**Next Steps**:
1. Send this document to IT Team (dvhiep@nqh.com.vn)
2. Wait for port allocation approval
3. Update NQH PORT_ALLOCATION_MANAGEMENT.md with SDLC section
4. Deploy to production infrastructure

---

**Document Version**: 1.0.0
**Created**: November 29, 2025
**Author**: SDLC Orchestrator Team
**Pending Approval**: IT Team (dvhiep@nqh.com.vn)
