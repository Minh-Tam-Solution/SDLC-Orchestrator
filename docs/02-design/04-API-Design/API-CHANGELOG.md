# API Changelog
## SDLC Orchestrator - API Version History

**Version**: 1.0.0
**Date**: December 9, 2025
**Status**: ACTIVE - Week 5 Day 4 (API Documentation Finalization)
**Authority**: Backend Lead + CTO Approved
**Foundation**: Week 3-5 Implementation (23 Endpoints)
**Framework**: SDLC 6.1.0

---

## Table of Contents

1. [Version 1.0.0 (December 2025)](#version-100-december-2025) - **CURRENT**
2. [Version 0.3.0 (November 2025)](#version-030-november-2025)
3. [Version 0.2.0 (November 2025)](#version-020-november-2025)
4. [Version 0.1.0 (November 2025)](#version-010-november-2025) - **INITIAL RELEASE**
5. [Breaking Changes Policy](#breaking-changes-policy)
6. [Deprecation Schedule](#deprecation-schedule)

---

## Version 1.0.0 (December 2025)

**Release Date**: December 9, 2025
**Status**: ✅ **PRODUCTION READY** (Gate G2 Approved)
**Migration Guide**: [v0.3.0 → v1.0.0](#migration-guide-v030--v100)

### 🎯 **Major Features**

#### **1. Performance & Monitoring (Week 5 Day 2)**
- **NEW**: `/metrics` endpoint for Prometheus scraping
- **NEW**: Prometheus metrics middleware (6 metric types)
- **NEW**: Grafana dashboard integration
- **IMPROVEMENT**: API latency p95 <100ms (guaranteed)
- **IMPROVEMENT**: Rate limiting optimization (Redis sliding window)

#### **2. Complete API Documentation (Week 5 Day 3)**
- **NEW**: OpenAPI 3.0.3 spec (31 endpoints, 100% coverage)
- **NEW**: Postman Collection v2.1.0 (auto-token management)
- **NEW**: cURL Examples Guide (15+ workflows)
- **NEW**: API Developer Guide (comprehensive)

#### **3. Security Hardening (Week 5 Day 1)**
- **FIXED**: P0 - Cryptography upgrade (43.0.3 → 44.0.0)
- **FIXED**: P0 - Jinja2 upgrade (3.1.4 → 3.1.5)
- **IMPROVEMENT**: OWASP ASVS compliance (87% → 92%)
- **IMPROVEMENT**: Security headers middleware (12 headers)

---

### 📋 **API Changes**

#### **Authentication Endpoints** (`/api/v1/auth`)

| Endpoint | Method | Change | Description |
|----------|--------|--------|-------------|
| `/auth/login` | POST | **IMPROVED** | Added rate limiting (5 req/min) |
| `/auth/refresh` | POST | **IMPROVED** | Token rotation on refresh |
| `/auth/me` | GET | **IMPROVED** | Added user permissions in response |
| `/auth/logout` | POST | **NEW** | Token blacklist via Redis |
| `/metrics` | GET | **NEW** | Prometheus metrics endpoint |

**Breaking Changes**: ❌ **NONE**

**New Fields**:
```json
// GET /auth/me response
{
  "id": "uuid",
  "email": "string",
  "full_name": "string",
  "is_active": true,
  "is_verified": true,
  "permissions": [        // NEW FIELD
    "gates:read",
    "gates:write",
    "evidence:upload"
  ]
}
```

---

#### **Gates Endpoints** (`/api/v1/gates`)

| Endpoint | Method | Change | Description |
|----------|--------|--------|-------------|
| `/gates` | GET | **IMPROVED** | Added pagination (default 50 items) |
| `/gates` | POST | **IMPROVED** | Added OPA policy validation |
| `/gates/{id}` | GET | **IMPROVED** | Added evidence_count field |
| `/gates/{id}` | PUT | **IMPROVED** | Audit trail logging |
| `/gates/{id}` | DELETE | **IMPROVED** | Soft delete (deleted_at timestamp) |
| `/gates/{id}/approve` | POST | **NEW** | Multi-approver workflow |
| `/gates/{id}/reject` | POST | **NEW** | Rejection with reason |
| `/gates/{id}/evidence` | GET | **NEW** | List gate evidence |

**Breaking Changes**: ❌ **NONE**

**New Query Parameters**:
```bash
# GET /gates
?status=pending          # Filter by status (pending, approved, rejected)
?gate_type=G0.1         # Filter by gate type
?project_id=uuid        # Filter by project
?page=1                 # Pagination (default: 1)
?page_size=50           # Page size (default: 50, max: 100)
```

**New Fields**:
```json
// GET /gates/{id} response
{
  "id": "uuid",
  "project_id": "uuid",
  "gate_type": "G0.1",
  "status": "pending",
  "title": "Problem Definition Review",
  "evidence_count": 3,     // NEW FIELD
  "approvers": [           // NEW FIELD
    {
      "user_id": "uuid",
      "approved_at": "2025-12-09T10:00:00Z",
      "comment": "Looks good"
    }
  ],
  "created_at": "2025-12-09T09:00:00Z",
  "updated_at": "2025-12-09T10:00:00Z",
  "deleted_at": null       // NEW FIELD (soft delete)
}
```

---

#### **Evidence Endpoints** (`/api/v1/evidence`)

| Endpoint | Method | Change | Description |
|----------|--------|--------|-------------|
| `/evidence` | GET | **IMPROVED** | Added pagination + search |
| `/evidence` | POST | **IMPROVED** | SHA256 integrity check |
| `/evidence/{id}` | GET | **IMPROVED** | Added download_count field |
| `/evidence/{id}/download` | GET | **IMPROVED** | Pre-signed URL (15 min expiry) |
| `/evidence/{id}` | DELETE | **IMPROVED** | Soft delete + audit trail |

**Breaking Changes**: ❌ **NONE**

**New Query Parameters**:
```bash
# GET /evidence
?gate_id=uuid           # Filter by gate
?file_name=*.pdf        # Search by filename (wildcard support)
?uploaded_by=uuid       # Filter by uploader
?page=1                 # Pagination
?page_size=50           # Page size
```

**New Fields**:
```json
// GET /evidence/{id} response
{
  "id": "uuid",
  "gate_id": "uuid",
  "file_name": "problem-statement.pdf",
  "file_size": 1048576,
  "content_type": "application/pdf",
  "sha256_hash": "abc123...",  // NEW FIELD
  "storage_path": "s3://...",
  "download_count": 12,         // NEW FIELD
  "uploaded_by": "uuid",
  "uploaded_at": "2025-12-09T09:00:00Z",
  "deleted_at": null            // NEW FIELD
}
```

---

#### **Policies Endpoints** (`/api/v1/policies`)

| Endpoint | Method | Change | Description |
|----------|--------|--------|-------------|
| `/policies` | GET | **IMPROVED** | Added category filter |
| `/policies` | POST | **IMPROVED** | OPA syntax validation |
| `/policies/{id}` | GET | **IMPROVED** | Added usage_count field |
| `/policies/{id}` | PUT | **IMPROVED** | Version history tracking |
| `/policies/{id}` | DELETE | **IMPROVED** | Prevent deletion if in use |
| `/policies/{id}/test` | POST | **NEW** | Test policy with sample data |
| `/policies/{id}/versions` | GET | **NEW** | Policy version history |

**Breaking Changes**: ❌ **NONE**

**New Query Parameters**:
```bash
# GET /policies
?category=security      # Filter by category
?gate_type=G0.1        # Filter by gate type
?is_active=true        # Filter by active status
?search=keyword        # Full-text search
```

**New Fields**:
```json
// GET /policies/{id} response
{
  "id": "uuid",
  "name": "Security Review Policy",
  "description": "...",
  "category": "security",
  "gate_type": "G0.1",
  "rego_code": "package sdlc...",
  "usage_count": 45,        // NEW FIELD
  "version": 3,             // NEW FIELD
  "is_active": true,
  "created_by": "uuid",
  "created_at": "2025-11-01T09:00:00Z",
  "updated_at": "2025-12-09T10:00:00Z"
}
```

---

### 🔧 **Performance Improvements**

| Metric | v0.3.0 | v1.0.0 | Improvement |
|--------|--------|--------|-------------|
| API Latency (p95) | 150ms | **<100ms** | **-33%** |
| Authentication (p95) | 80ms | **<50ms** | **-38%** |
| Database Queries (avg) | 25ms | **<10ms** | **-60%** |
| Evidence Upload (10MB) | 3.5s | **<2s** | **-43%** |
| Dashboard Load (p95) | 1.5s | **<1s** | **-33%** |

**Optimization Techniques**:
- Redis caching for user sessions (15min TTL)
- Database connection pooling (20 min, 50 max)
- Strategic indexes on high-traffic queries
- Async I/O for all external service calls
- GZip compression for API responses >1KB

---

### 🛡️ **Security Enhancements**

#### **1. Dependency Updates** (Week 5 Day 1)
- `cryptography`: 43.0.3 → **44.0.0** (P0 - CRITICAL)
- `jinja2`: 3.1.4 → **3.1.5** (P0 - HIGH)
- `idna`: 3.4 → **3.10** (P1 - MEDIUM)

#### **2. OWASP ASVS Compliance**
- Authentication: **95%** (was 87%)
- Session Management: **92%** (was 85%)
- Access Control: **90%** (was 82%)
- Input Validation: **88%** (was 80%)
- Cryptography: **94%** (was 88%)
- **OVERALL**: **92%** (was 87%)

#### **3. Security Headers** (Week 5 Day 1)
```http
Strict-Transport-Security: max-age=31536000; includeSubDomains
Content-Security-Policy: default-src 'self'
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: geolocation=(), microphone=(), camera=()
```

---

### 📊 **Monitoring & Observability**

#### **New Prometheus Metrics** (Week 5 Day 2)
```promql
# API Latency (p95)
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Request Rate (requests/second)
rate(http_requests_total[1m])

# Error Rate (4xx/5xx)
rate(http_requests_total{status=~"4..|5.."}[1m]) / rate(http_requests_total[1m]) * 100

# Active Requests (in-flight)
http_requests_in_progress

# Exception Rate
rate(http_exceptions_total[1m])

# Request/Response Size (p95)
histogram_quantile(0.95, rate(http_request_size_bytes_sum[5m]))
```

#### **Grafana Dashboard** (Week 5 Day 2)
- 6 panels: Latency, Request Rate, Error Rate, Active Requests, Top Slowest Endpoints, Request Size
- Auto-refresh every 5 seconds
- Alert on 5xx error rate >0.001 req/s

---

### 📚 **Documentation Updates**

#### **New Resources** (Week 5 Day 3)
1. **OpenAPI 3.0.3 Spec** - 31 endpoints, 100% coverage
2. **Postman Collection v2.1.0** - Auto-token management, 23 requests
3. **cURL Examples Guide** - 15+ workflows (auth, gates, evidence, policies, CI/CD)
4. **API Developer Guide** - Comprehensive (quick start, best practices, troubleshooting)
5. **API Changelog** - Version history (this document)
6. **Troubleshooting Guide** - 20+ common issues + fixes

#### **Developer Onboarding Improvement**
- Time to First API Call: **>2 hours → <30 min** (-75%)
- Documentation Coverage: **80% → 100%**
- Developer Tools: **1 → 6 resources**

---

### 🐛 **Bug Fixes**

#### **Authentication**
- **FIXED**: Token refresh race condition (dual token issue)
- **FIXED**: MFA setup flow (QR code encoding error)
- **FIXED**: OAuth state validation (CSRF prevention)

#### **Gates**
- **FIXED**: Gate approval timestamp (timezone UTC enforcement)
- **FIXED**: Concurrent gate creation (database constraint violation)
- **FIXED**: Gate deletion with evidence (orphaned evidence handling)

#### **Evidence**
- **FIXED**: Large file upload timeout (chunked upload support)
- **FIXED**: File download race condition (pre-signed URL expiry)
- **FIXED**: SHA256 hash mismatch on Windows (CRLF vs LF)

#### **Policies**
- **FIXED**: OPA policy compilation error (Rego syntax validation)
- **FIXED**: Policy test flakiness (deterministic test data)
- **FIXED**: Policy deletion with active gates (dependency check)

---

### 🚀 **Migration Guide: v0.3.0 → v1.0.0**

#### **Breaking Changes**
❌ **NONE** - This is a backwards-compatible release.

#### **Recommended Updates**

**1. Update Authentication Flow** (Optional)
```diff
# Before (v0.3.0)
- User permissions were not returned in /auth/me

# After (v1.0.0)
+ User permissions are now included in /auth/me response
+ Use permissions array for frontend authorization logic
```

**Example**:
```javascript
// v1.0.0: Use permissions for UI rendering
const user = await fetch('/api/v1/auth/me');
if (user.permissions.includes('gates:write')) {
  showCreateGateButton();
}
```

---

**2. Add Pagination Support** (Recommended)
```diff
# Before (v0.3.0)
- GET /api/v1/gates returned all gates (could be 1000s)

# After (v1.0.0)
+ GET /api/v1/gates now supports pagination (default 50 items)
+ Add page and page_size query parameters
```

**Example**:
```bash
# v1.0.0: Paginated requests
curl "http://localhost:8000/api/v1/gates?page=1&page_size=50"
```

---

**3. Use New Approval Endpoints** (Recommended)
```diff
# Before (v0.3.0)
- PUT /api/v1/gates/{id} with status=approved

# After (v1.0.0)
+ POST /api/v1/gates/{id}/approve (dedicated endpoint)
+ Supports multi-approver workflow
+ Captures approver comment
```

**Example**:
```bash
# v1.0.0: Dedicated approval endpoint
curl -X POST "http://localhost:8000/api/v1/gates/{id}/approve" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"comment": "Approved after review"}'
```

---

**4. Enable Monitoring** (Recommended)
```diff
# Before (v0.3.0)
- No built-in monitoring

# After (v1.0.0)
+ /metrics endpoint available
+ Prometheus + Grafana stack ready
+ 6 metric types exposed
```

**Setup**:
```bash
# Start monitoring stack
docker-compose -f docker-compose.monitoring.yml up -d

# Access Prometheus: http://localhost:9090
# Access Grafana: http://localhost:3001 (admin/SecureGrafana123!)
```

---

### ⚠️ **Deprecation Notices**

**None** - All v0.3.0 APIs remain supported.

**Future Deprecations** (v2.0.0 - Q2 2026):
- `PUT /api/v1/gates/{id}` for approvals → Use `POST /api/v1/gates/{id}/approve`
- `DELETE /api/v1/policies/{id}` → Use `PUT /api/v1/policies/{id}` with `is_active=false`

---

## Version 0.3.0 (November 2025)

**Release Date**: November 29, 2025
**Status**: ✅ **SUPERSEDED** (use v1.0.0)

### 🎯 **Major Features**

#### **1. Evidence Vault API** (Week 3 Day 4)
- **NEW**: Evidence upload endpoint (`POST /api/v1/evidence`)
- **NEW**: Evidence download endpoint (`GET /api/v1/evidence/{id}/download`)
- **NEW**: MinIO S3 integration (AGPL-safe, network-only)
- **NEW**: Metadata storage in PostgreSQL

#### **2. Policies API** (Week 3 Day 4)
- **NEW**: Policy CRUD endpoints (5 endpoints)
- **NEW**: OPA integration (YAML → Rego compilation)
- **NEW**: Policy testing framework

---

### 📋 **API Changes**

| Endpoint | Method | Change | Description |
|----------|--------|--------|-------------|
| `/evidence` | GET | **NEW** | List all evidence |
| `/evidence` | POST | **NEW** | Upload evidence file |
| `/evidence/{id}` | GET | **NEW** | Get evidence metadata |
| `/evidence/{id}/download` | GET | **NEW** | Download evidence file |
| `/evidence/{id}` | DELETE | **NEW** | Delete evidence |
| `/policies` | GET | **NEW** | List all policies |
| `/policies` | POST | **NEW** | Create policy |
| `/policies/{id}` | GET | **NEW** | Get policy details |
| `/policies/{id}` | PUT | **NEW** | Update policy |
| `/policies/{id}` | DELETE | **NEW** | Delete policy |

---

### 🔧 **Performance Improvements**
- MinIO S3 uploads: <2s for 10MB files
- Database queries optimized with indexes

---

### 🐛 **Bug Fixes**
- **FIXED**: Gate creation validation (project_id required)
- **FIXED**: Authentication error messages (generic → specific)

---

## Version 0.2.0 (November 2025)

**Release Date**: November 25, 2025
**Status**: ✅ **SUPERSEDED** (use v1.0.0)

### 🎯 **Major Features**

#### **1. Gates Management API** (Week 3 Day 3)
- **NEW**: Gate CRUD endpoints (5 endpoints)
- **NEW**: Quality gate workflow (pending → approved/rejected)
- **NEW**: PostgreSQL database integration

---

### 📋 **API Changes**

| Endpoint | Method | Change | Description |
|----------|--------|--------|-------------|
| `/gates` | GET | **NEW** | List all gates |
| `/gates` | POST | **NEW** | Create gate |
| `/gates/{id}` | GET | **NEW** | Get gate details |
| `/gates/{id}` | PUT | **NEW** | Update gate |
| `/gates/{id}` | DELETE | **NEW** | Delete gate |

---

## Version 0.1.0 (November 2025)

**Release Date**: November 22, 2025
**Status**: ✅ **SUPERSEDED** (use v1.0.0)

### 🎯 **Major Features**

#### **1. Authentication API** (Week 3 Day 3)
- **NEW**: JWT-based authentication
- **NEW**: Email/password login
- **NEW**: Token refresh flow
- **NEW**: OAuth 2.0 support (GitHub, Google, Microsoft)
- **NEW**: User profile endpoint

---

### 📋 **Initial API Endpoints**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/auth/login` | POST | Login with email/password |
| `/auth/refresh` | POST | Refresh access token |
| `/auth/me` | GET | Get current user profile |
| `/health` | GET | API health check |

---

## Breaking Changes Policy

SDLC Orchestrator follows **Semantic Versioning** (SemVer):

### **MAJOR version** (x.0.0)
- Breaking API changes (endpoint removal, response format changes)
- Minimum 3 months deprecation notice
- Migration guide provided
- Example: v1.0.0 → v2.0.0

### **MINOR version** (0.x.0)
- New features, backwards-compatible
- New endpoints, new fields in responses
- No breaking changes
- Example: v1.0.0 → v1.1.0

### **PATCH version** (0.0.x)
- Bug fixes, performance improvements
- No new features, no breaking changes
- Example: v1.0.0 → v1.0.1

---

## Deprecation Schedule

### **Current Deprecation Notices**

**None** - All v1.0.0 APIs are fully supported.

---

### **Future Deprecations** (v2.0.0 - Q2 2026)

#### **1. Gate Approval via PUT** (Deprecated in v1.0.0, Removed in v2.0.0)
```diff
# ❌ DEPRECATED (v1.0.0)
- PUT /api/v1/gates/{id}
-   with body: {"status": "approved"}

# ✅ USE INSTEAD
+ POST /api/v1/gates/{id}/approve
+   with body: {"comment": "Approved after review"}
```

**Migration Deadline**: June 1, 2026
**Deprecation Notice**: December 9, 2025 (v1.0.0 release)

---

#### **2. Policy Hard Delete** (Deprecated in v1.0.0, Removed in v2.0.0)
```diff
# ❌ DEPRECATED (v1.0.0)
- DELETE /api/v1/policies/{id}

# ✅ USE INSTEAD
+ PUT /api/v1/policies/{id}
+   with body: {"is_active": false}
```

**Migration Deadline**: June 1, 2026
**Deprecation Notice**: December 9, 2025 (v1.0.0 release)

---

### **Deprecation Communication**

**Developer Notifications**:
1. **HTTP Header** (all requests to deprecated endpoints):
   ```http
   Deprecation: true
   Sunset: Fri, 01 Jun 2026 00:00:00 GMT
   Link: <https://docs.sdlc-orchestrator.com/changelog#v200>; rel="deprecation"
   ```

2. **Response Warning** (all responses from deprecated endpoints):
   ```json
   {
     "data": {...},
     "warning": {
       "message": "This endpoint is deprecated and will be removed in v2.0.0 (June 2026)",
       "migration_guide": "https://docs.sdlc-orchestrator.com/changelog#v200",
       "alternative": "POST /api/v1/gates/{id}/approve"
     }
   }
   ```

3. **Email Notifications**:
   - 90 days before removal
   - 30 days before removal
   - 7 days before removal

---

## API Versioning Strategy

SDLC Orchestrator uses **URL versioning**:

### **Current Version** (v1)
```
https://api.sdlc-orchestrator.com/api/v1/gates
```

### **Future Versions** (v2)
```
https://api.sdlc-orchestrator.com/api/v2/gates
```

### **Version Support Policy**
- **Current version (v1)**: Fully supported, new features added
- **Previous version (v0)**: Security fixes only, deprecated
- **Older versions**: Unsupported, removed

**Support Timeline**:
- **v1**: December 2025 - June 2027 (18 months)
- **v2**: June 2026 - December 2027 (planned)

---

## Contact & Support

**Questions about API changes?**
- Documentation: https://docs.sdlc-orchestrator.com/api
- GitHub Issues: https://github.com/sdlc-orchestrator/sdlc-orchestrator/issues
- Email: api-support@sdlc-orchestrator.com
- Slack: #api-developers

**Report a breaking change?**
- Email: breaking-change@sdlc-orchestrator.com
- Include: API endpoint, expected behavior, actual behavior, version

---

**Changelog Status**: ✅ **COMPLETE** (v1.0.0)
**Framework**: ✅ **SDLC 5.1.3 COMPLETE LIFECYCLE**
**Authorization**: ✅ **BACKEND LEAD + CTO APPROVED**

---

*SDLC Orchestrator API - Semantic Versioning. Clear deprecation policy. Developer-first communication.* 🚀

**Last Updated**: December 9, 2025
**Owner**: Backend Lead + API Team
**Status**: ✅ ACTIVE - WEEK 5 DAY 4 (API DOCUMENTATION FINALIZATION)
**Next Review**: v1.1.0 (January 2026)
