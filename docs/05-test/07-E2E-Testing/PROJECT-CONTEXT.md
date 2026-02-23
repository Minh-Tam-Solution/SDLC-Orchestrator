# Project Context — SDLC Orchestrator

*-CyEyes-* — Phase -1 Analysis Record

**Analyzed**: 2026-02-21
**By**: @tester (e2e-api-testing skill v2.0.0, SDLC 6.1.1)

---

## Backend Service

| Property | Value |
|----------|-------|
| **Framework** | FastAPI (Uvicorn) |
| **Location** | `backend/app/` |
| **Port** | 8300 |
| **Base URL** | `http://localhost:8300` |
| **Container** | `sdlc-staging-backend` |
| **Version** | 1.2.0 |
| **Health** | `/health` → `{"status":"healthy","version":"1.2.0"}` |

## Supporting Services

| Service | Container | Port | Status |
|---------|-----------|------|--------|
| PostgreSQL | `sdlc-staging-postgres` | 5450 | ✅ |
| Redis | `sdlc-staging-redis` | 6395 | ✅ |
| MinIO | `sdlc-staging-minio` | 9010 | ✅ |
| OPA | `sdlc-staging-opa` | 8185 | ✅ |
| Frontend | `sdlc-staging-frontend` | 8310 | ✅ |

## Test Credentials

| Role | Email | Password | Notes |
|------|-------|----------|-------|
| **Admin (superuser)** | `taidt@mtsolution.com.vn` | `Admin@123456` | Active — login confirmed 2026-02-21 |
| Source | `backend/create_admin.py` | | Account unlocked, original password works |

> NOTE: Account was previously locked (2026-02-20). As of 2026-02-21, `Admin@123456` works. Login via `POST /api/v1/auth/login`.

## API Entry Points

| Endpoint | URL |
|----------|-----|
| Health | `http://localhost:8300/health` |
| Ready | `http://localhost:8300/health/ready` |
| Swagger UI | `http://localhost:8300/api/docs` |
| OpenAPI JSON | `http://localhost:8300/api/openapi.json` |
| Metrics | `http://localhost:8300/metrics` |

## OpenAPI Spec

- **SSOT Location**: `docs/03-integrate/02-API-Specifications/openapi.json`
- **Live endpoint**: `http://localhost:8300/api/openapi.json`
- **Total Paths**: 617
- **Total Operations**: 704 (GET: 375, POST: 266, PUT: 27, DELETE: 26, PATCH: 10)

## Latest E2E Test Results (2026-02-21)

- **Report**: [E2E-API-REPORT-2026-02-21.md](reports/E2E-API-REPORT-2026-02-21.md)
- **Tested**: 698/704 operations (6 skipped)
- **API Health Score**: 94.7% (non-5xx responses)
- **Direct Pass Rate**: 25.4% (auto-generated bodies — manual tests would be higher)
- **Server Errors**: 36 endpoints (5.2%) — needs investigation
- **Avg Response Time**: fast (<100ms p95)

## Key Finding — Staging Build Gap

The staging environment runs an older build. The following Sprint 181-188 code is in the repo (committed in `8d02dfe`) but **NOT deployed to staging**:
- Sprint 181: NIST routes, templates route, compliance framework
- Sprint 182-183: Enterprise SSO routes
- Sprint 185: SOC2 pack generation (audit logs are deployed ✅)
- Sprint 186: Data residency, GDPR routes
- Sprint 176-179: Multi-agent team engine routes
- Sprint 188: `/api/v1/payments/subscriptions/me`

**Action**: Deploy latest `main` branch to staging to complete Sprint 181-188 validation.
