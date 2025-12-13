# Incident Report: Frontend Blank Page & 502 Bad Gateway

**Incident ID**: INC-2025-12-13-001
**Date**: December 13, 2025
**Severity**: P1 (Critical - Complete Service Outage)
**Status**: ✅ RESOLVED
**Duration**: ~90 minutes
**Reported By**: Development Team
**Resolved By**: AI Agent (Claude Sonnet 4.5) + DevOps

---

## Executive Summary

SDLC Orchestrator frontend experienced complete service outage with two critical issues:
1. **Blank page** - Circular dependency in charts-vendor bundle
2. **502 Bad Gateway** - nginx proxy port mismatch

Both issues resolved through configuration updates. No data loss. All services restored to healthy state.

---

## Timeline

| Time | Event |
|------|-------|
| 13:15 | User reports frontend showing blank page |
| 13:20 | Created debug page, user provides error: "Cannot access 'P' before initialization" |
| 13:25 | Identified root cause: charts-vendor circular dependency |
| 13:30 | Fixed vite.config.ts, rebuilt frontend |
| 13:35 | Frontend loads successfully |
| 13:40 | User reports 502 error on login |
| 13:45 | Identified nginx proxy pointing to wrong port (8000 vs 8300) |
| 13:50 | Fixed nginx.conf and Dockerfile |
| 14:00 | Rebuilt and restarted both containers |
| 14:05 | ✅ All services operational, incident resolved |

---

## Issue 1: Frontend Blank Page

### Symptoms
- Frontend at `http://localhost:8310` showing completely blank page
- No errors in nginx logs
- JavaScript loading but failing at runtime

### Root Cause
**Circular dependency in Recharts + D3 libraries** when code-split into separate vendor bundle.

Error message:
```
Uncaught ReferenceError: Cannot access 'P' before initialization
  at charts-vendor-CdNFaQ6U.js:9
```

**Technical Details**:
- Vite's manual chunks strategy split recharts + d3 into `charts-vendor` bundle
- ES module initialization order caused variable hoisting problem
- Variable 'P' accessed before initialization due to circular imports

### Solution
**Disabled charts code splitting** - keep charts inline in main bundle.

**File**: `frontend/web/vite.config.ts:92-96`
```typescript
// Charts library - DISABLED due to circular dependency issue
// Keep charts in main bundle to avoid "Cannot access 'P' before initialization" error
// if (id.includes('recharts') || id.includes('d3-')) {
//   return 'charts-vendor'
// }
```

**Trade-off**:
- ✅ Eliminates initialization errors
- ✅ Reliable chart rendering
- ⚠️ CompliancePage bundle increased: 130KB → 492KB (gzipped)

**Verification**:
```bash
# Before: charts-vendor-CdNFaQ6U.js exists (130KB)
# After: No charts-vendor, charts in CompliancePage-DQ9fhqWH.js (492KB)
```

---

## Issue 2: 502 Bad Gateway

### Symptoms
- All API requests returning HTTP 502 Bad Gateway
- Login endpoint failing
- Backend healthy when accessed directly

### Root Cause
**Port mismatch between nginx proxy configuration and actual backend service**.

**Configuration Conflict**:
- nginx.conf: `proxy_pass http://backend:8000/api/` (WRONG)
- Backend actual port: `8300` (per docker-compose.yml)
- Backend Dockerfile: EXPOSE 8000 (INCONSISTENT)

### Solution
**Standardized all configurations to port 8300**.

**Changes Made**:

1. **nginx.conf** (line 36):
```nginx
# Before
proxy_pass http://backend:8000/api/;

# After
proxy_pass http://backend:8300/api/;
```

2. **backend/Dockerfile** (lines 39, 43, 46):
```dockerfile
# Before
EXPOSE 8000
HEALTHCHECK ... http://localhost:8000/api/v1/health
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# After
EXPOSE 8300
HEALTHCHECK ... http://localhost:8300/health
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8300"]
```

**Verification**:
```bash
# Backend health check
curl http://localhost:8300/health
# {"status":"healthy","version":"1.2.0","service":"sdlc-orchestrator-backend"}

# Login endpoint (via nginx)
curl -X POST http://localhost:8310/api/v1/auth/login -d '{"email":"test","password":"test"}'
# {"detail":"Incorrect email or password"}  ← Valid auth response!
```

---

## Port Configuration (Final)

**Aligned with IT Team PORT_ALLOCATION_MANAGEMENT.md**:

| Service | Port | Container | Status |
|---------|------|-----------|--------|
| Backend API | 8300 | sdlc-backend | ✅ |
| Frontend Web | 8310 | sdlc-frontend | ✅ |
| PostgreSQL | 5432 | sdlc-postgres | ✅ |
| Redis | 6379 | sdlc-redis | ✅ |
| MinIO API | 9097 | sdlc-minio | ✅ |
| MinIO Console | 9098 | sdlc-minio | ✅ |
| OPA | 8181 | sdlc-opa | ✅ |
| Grafana | 3001 | sdlc-grafana | ✅ |
| Prometheus | 9096 | sdlc-prometheus | ✅ |

**Public Routes (Planned)**:
- Frontend: https://sdlc.nqh.vn → localhost:8310
- Backend API: https://sdlc-api.nqh.vn → localhost:8300

---

## Prevention Measures

### Immediate Actions
1. ✅ Port consistency enforced across all config files
2. ✅ Healthcheck endpoints updated to match actual service
3. ✅ Docker rebuild with corrected configurations

### Long-term Improvements
1. **Pre-commit validation**: Verify port consistency across configs
2. **Integration tests**: Test nginx → backend proxy in CI/CD
3. **Health monitoring**: Alert on 502 errors (Prometheus + Grafana)
4. **Documentation**: Update deployment runbook with port verification steps

---

## Lessons Learned

1. **Code Splitting Trade-offs**:
   - Large libraries (recharts, d3) may have circular dependencies
   - Inline bundling acceptable if it prevents runtime errors
   - Always test production builds before deployment

2. **Port Management**:
   - Centralized port allocation critical (IT's PORT_ALLOCATION_MANAGEMENT.md)
   - Dockerfile EXPOSE should match docker-compose ports
   - Health checks must use actual service ports

3. **Debugging Strategy**:
   - Browser console essential for frontend errors
   - Test direct backend access to isolate proxy issues
   - Docker logs reveal actual listening ports

---

## Related Commits

1. `c49f37a` - fix: Resolve 502 Bad Gateway and frontend blank page issues
2. Previous commits - Framework 5.1.1 version consistency updates

---

## References

- **Port Allocation**: `/home/nqh/shared/models/docs/admin/PORT_ALLOCATION_MANAGEMENT.md`
- **Vite Config**: `frontend/web/vite.config.ts`
- **Nginx Config**: `frontend/web/nginx.conf`
- **Backend Dockerfile**: `backend/Dockerfile`
- **Docker Compose**: `docker-compose.yml`

---

**Document Status**: ACTIVE
**Last Updated**: December 13, 2025
**Framework**: SDLC 5.1.1 Complete Lifecycle
**Stage**: 07-OPERATE (Incident Response)
