# Project Context — SDLC Orchestrator

*-CyEyes-* — Phase -1 Analysis Record

**Analyzed**: 2026-02-20
**By**: @tester (e2e-api-testing skill v1.2.0)

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
| **Admin (superuser)** | `taidt@mtsolution.com.vn` | `TestAdmin@2026` | Reset for E2E testing |
| Source | `backend/create_admin.py` | | Original: `Admin@123456` — locked after retries |

> ⚠️ NOTE: The original `Admin@123456` password was rejected (account locked). Password was reset to `TestAdmin@2026` via direct DB update for testing. After testing, consider resetting to `Admin@123456` and unlocking: `UPDATE users SET password_hash=<hash>, failed_login_count=0, locked_until=NULL WHERE email='taidt@mtsolution.com.vn'`

## API Entry Points

| Endpoint | URL |
|----------|-----|
| Health | `http://localhost:8300/health` |
| Ready | `http://localhost:8300/health/ready` |
| Swagger UI | `http://localhost:8300/api/docs` |
| OpenAPI JSON | `http://localhost:8300/api/openapi.json` |
| Metrics | `http://localhost:8300/metrics` |

## OpenAPI Spec

- **Saved to**: `docs/03-Integration-APIs/02-API-Specifications/openapi.json`
- **Size**: 1.28MB
- **Total Paths**: 550
- **Total Operations**: 622

## Key Finding — Staging Build Gap

The staging environment runs an older build. The following Sprint 181-188 code is in the repo (committed in `8d02dfe`) but **NOT deployed to staging**:
- Sprint 181: NIST routes, templates route, compliance framework
- Sprint 182-183: Enterprise SSO routes
- Sprint 185: SOC2 pack generation (audit logs are deployed ✅)
- Sprint 186: Data residency, GDPR routes
- Sprint 176-179: Multi-agent team engine routes
- Sprint 188: `/api/v1/payments/subscriptions/me`

**Action**: Deploy latest `main` branch to staging to complete Sprint 181-188 validation.
