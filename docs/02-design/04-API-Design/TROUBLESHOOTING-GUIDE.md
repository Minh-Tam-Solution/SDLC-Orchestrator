# API Troubleshooting Guide
## SDLC Orchestrator - Common Issues & Solutions

**Version**: 1.0.0
**Date**: December 9, 2025
**Status**: ACTIVE - Week 5 Day 4 (API Documentation Finalization)
**Authority**: Backend Lead + DevOps Lead + CTO Approved
**Foundation**: Week 3-5 Production Experience (23 Endpoints)
**Framework**: SDLC 5.1.3 Complete Lifecycle

---

## Table of Contents

1. [Authentication Issues](#authentication-issues)
2. [Rate Limiting & Throttling](#rate-limiting--throttling)
3. [File Upload Issues](#file-upload-issues)
4. [Database & Performance](#database--performance)
5. [CORS & Cross-Origin Issues](#cors--cross-origin-issues)
6. [Gate Workflow Issues](#gate-workflow-issues)
7. [Policy Evaluation Errors](#policy-evaluation-errors)
8. [Monitoring & Debugging](#monitoring--debugging)
9. [Common HTTP Error Codes](#common-http-error-codes)
10. [FAQ](#faq)

---

## Authentication Issues

### ❌ **Issue 1: 401 Unauthorized - "Invalid or expired token"**

**Symptoms**:
```json
{
  "detail": "Invalid or expired token"
}
```

**Common Causes**:
1. Access token expired (15-minute TTL)
2. Token blacklisted after logout
3. Token malformed or corrupted
4. Token from different environment (dev vs prod)

**Solutions**:

**Solution 1: Refresh your access token**
```bash
# Use refresh token to get new access token
curl -X POST "http://localhost:8000/api/v1/auth/refresh" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "your_refresh_token_here"
  }'
```

**Solution 2: Re-login**
```bash
# Login again to get fresh tokens
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123"
  }'
```

**Solution 3: Check token format**
```bash
# Token must be in "Bearer <token>" format
# ❌ WRONG
curl -H "Authorization: your_token"

# ✅ CORRECT
curl -H "Authorization: Bearer your_token"
```

**Prevention**:
- Implement automatic token refresh (use refresh token before access token expires)
- Store tokens securely (never in localStorage, use httpOnly cookies)
- Use Postman Collection auto-token management

---

### ❌ **Issue 2: 422 Validation Error - "Invalid email or password"**

**Symptoms**:
```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "email"],
      "msg": "value is not a valid email address"
    }
  ]
}
```

**Common Causes**:
1. Email format invalid (missing `@`, `.com`, etc.)
2. Password too short (<8 characters)
3. Extra whitespace in email/password
4. Case sensitivity issues (email is case-insensitive)

**Solutions**:

**Solution 1: Validate email format**
```javascript
// Use regex validation before sending
const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
if (!emailRegex.test(email)) {
  console.error("Invalid email format");
}
```

**Solution 2: Trim whitespace**
```javascript
// Always trim inputs
const cleanEmail = email.trim().toLowerCase();
const cleanPassword = password.trim();
```

**Solution 3: Check password requirements**
```javascript
// Password must be 8+ characters
if (password.length < 8) {
  console.error("Password too short (min 8 characters)");
}
```

---

### ❌ **Issue 3: Token refresh returns 401**

**Symptoms**:
```json
{
  "detail": "Invalid refresh token"
}
```

**Common Causes**:
1. Refresh token expired (30-day TTL)
2. Refresh token already used (rotation policy)
3. User logged out (token blacklisted)
4. Refresh token from different user

**Solutions**:

**Solution 1: Re-login if refresh token expired**
```bash
# If refresh fails, login again
if [ "$refresh_response_code" == "401" ]; then
  curl -X POST "http://localhost:8000/api/v1/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"email": "test@example.com", "password": "password123"}'
fi
```

**Solution 2: Check refresh token rotation**
```javascript
// After refresh, ALWAYS update both tokens
const response = await fetch('/api/v1/auth/refresh', {
  method: 'POST',
  body: JSON.stringify({ refresh_token: oldRefreshToken })
});

const data = await response.json();
// ⚠️ CRITICAL: Update both tokens (rotation)
localStorage.setItem('access_token', data.access_token);
localStorage.setItem('refresh_token', data.refresh_token); // NEW refresh token
```

---

## Rate Limiting & Throttling

### ❌ **Issue 4: 429 Too Many Requests - "Rate limit exceeded"**

**Symptoms**:
```json
{
  "detail": "Rate limit exceeded. Try again in 60 seconds."
}
```
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1638360000
Retry-After: 60
```

**Common Causes**:
1. Exceeded 100 requests/minute per user
2. Burst traffic (multiple requests in <1 second)
3. Authentication endpoint abuse (5 requests/minute limit)
4. Shared IP rate limit (corporate network)

**Solutions**:

**Solution 1: Implement exponential backoff**
```javascript
async function retryWithBackoff(fn, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (error) {
      if (error.status === 429) {
        const retryAfter = error.headers.get('Retry-After') || Math.pow(2, i);
        console.log(`Rate limited. Retrying in ${retryAfter}s...`);
        await sleep(retryAfter * 1000);
      } else {
        throw error;
      }
    }
  }
  throw new Error('Max retries exceeded');
}
```

**Solution 2: Check rate limit headers**
```bash
# Check remaining requests before making API call
curl -I "http://localhost:8000/api/v1/gates" \
  -H "Authorization: Bearer $TOKEN"

# Response headers:
# X-RateLimit-Limit: 100
# X-RateLimit-Remaining: 75  ← 75 requests left
# X-RateLimit-Reset: 1638360000
```

**Solution 3: Use batch endpoints**
```diff
# ❌ BAD: 100 individual requests (will hit rate limit)
- for gate_id in $(cat gate_ids.txt); do
-   curl "http://localhost:8000/api/v1/gates/$gate_id"
- done

# ✅ GOOD: 1 paginated request
+ curl "http://localhost:8000/api/v1/gates?page_size=100"
```

**Prevention**:
- Implement client-side rate limiting (track request count locally)
- Use pagination instead of multiple individual requests
- Cache API responses (reduce redundant calls)
- Contact support for rate limit increase (enterprise plans)

---

### ❌ **Issue 5: Authentication rate limit (5 req/min)**

**Symptoms**:
```json
{
  "detail": "Too many login attempts. Try again in 5 minutes."
}
```

**Common Causes**:
1. Automated testing without rate limit handling
2. Incorrect credentials (repeated failed logins)
3. Multiple CI/CD jobs running in parallel

**Solutions**:

**Solution 1: Cache tokens in CI/CD**
```yaml
# GitHub Actions example
- name: Login to SDLC Orchestrator
  run: |
    # Check if token exists and is valid
    if [ -f .access_token ]; then
      TOKEN=$(cat .access_token)
      # Test token validity
      curl -f "http://localhost:8000/api/v1/auth/me" \
        -H "Authorization: Bearer $TOKEN" && exit 0
    fi

    # Only login if token invalid or missing
    curl -X POST "http://localhost:8000/api/v1/auth/login" \
      -d '{"email": "${{ secrets.API_EMAIL }}", "password": "${{ secrets.API_PASSWORD }}"}' \
      | jq -r '.access_token' > .access_token
```

**Solution 2: Use API keys for CI/CD**
```bash
# Use API keys (no rate limit) instead of login
curl "http://localhost:8000/api/v1/gates" \
  -H "X-API-Key: your_api_key_here"
```

---

## File Upload Issues

### ❌ **Issue 6: 413 Payload Too Large - "File size exceeds limit"**

**Symptoms**:
```json
{
  "detail": "File size exceeds 100MB limit"
}
```

**Common Causes**:
1. File size >100MB (max upload size)
2. Multipart form-data encoding overhead
3. Nginx/proxy upload limit

**Solutions**:

**Solution 1: Check file size before upload**
```javascript
// Validate file size before upload
const maxSize = 100 * 1024 * 1024; // 100MB in bytes
if (file.size > maxSize) {
  alert('File too large. Max size: 100MB');
  return;
}
```

**Solution 2: Compress large files**
```bash
# Compress PDF files before upload
gs -sDEVICE=pdfwrite -dCompatibilityLevel=1.4 -dPDFSETTINGS=/ebook \
  -dNOPAUSE -dQUIET -dBATCH \
  -sOutputFile=compressed.pdf original.pdf

# Upload compressed file
curl -X POST "http://localhost:8000/api/v1/evidence" \
  -H "Authorization: Bearer $TOKEN" \
  -F "gate_id=uuid" \
  -F "file=@compressed.pdf"
```

**Solution 3: Split large files**
```bash
# Split 500MB file into 50MB chunks
split -b 50M large-file.zip chunk_

# Upload chunks separately
for chunk in chunk_*; do
  curl -X POST "http://localhost:8000/api/v1/evidence" \
    -F "file=@$chunk"
done
```

---

### ❌ **Issue 7: Evidence upload returns 500 Internal Server Error**

**Symptoms**:
```json
{
  "detail": "Failed to upload evidence to storage"
}
```

**Common Causes**:
1. MinIO service down (S3 storage unavailable)
2. Network timeout (file upload >60 seconds)
3. Disk space full on MinIO server
4. Invalid file encoding (binary file sent as text)

**Solutions**:

**Solution 1: Check MinIO service health**
```bash
# Check if MinIO is running
docker-compose ps minio

# Check MinIO logs
docker-compose logs minio | tail -50

# Restart MinIO if down
docker-compose restart minio
```

**Solution 2: Use binary mode for file upload**
```bash
# ✅ CORRECT: Binary file upload
curl -X POST "http://localhost:8000/api/v1/evidence" \
  -H "Authorization: Bearer $TOKEN" \
  -F "gate_id=uuid" \
  -F "file=@document.pdf;type=application/pdf"

# ❌ WRONG: Text mode (corrupts binary files)
curl -X POST "http://localhost:8000/api/v1/evidence" \
  --data-binary "@document.pdf"
```

**Solution 3: Increase timeout for large files**
```javascript
// Increase timeout for large file uploads
const response = await fetch('/api/v1/evidence', {
  method: 'POST',
  body: formData,
  timeout: 120000  // 120 seconds (default: 30s)
});
```

---

### ❌ **Issue 8: SHA256 hash mismatch error**

**Symptoms**:
```json
{
  "detail": "File integrity check failed. SHA256 hash mismatch."
}
```

**Common Causes**:
1. File corrupted during upload
2. Line ending conversion (CRLF ↔ LF on Windows)
3. Multipart encoding issue
4. File modified after hash calculation

**Solutions**:

**Solution 1: Calculate hash correctly**
```bash
# ✅ CORRECT: Binary mode hash
sha256sum -b document.pdf

# ❌ WRONG: Text mode hash (different on Windows)
sha256sum document.pdf
```

**Solution 2: Disable auto-conversion**
```bash
# Git: Disable CRLF conversion for binary files
git config --global core.autocrlf false
```

**Solution 3: Retry upload**
```bash
# Sometimes network corruption, just retry
for i in {1..3}; do
  curl -X POST "http://localhost:8000/api/v1/evidence" \
    -F "file=@document.pdf" && break
  echo "Upload failed, retrying..."
  sleep 2
done
```

---

## Database & Performance

### ❌ **Issue 9: Slow API responses (>1 second)**

**Symptoms**:
- API latency >1s (should be <100ms p95)
- Dashboard loading slowly
- Timeout errors (504 Gateway Timeout)

**Common Causes**:
1. Missing database indexes (full table scan)
2. N+1 query problem (100 queries instead of 1)
3. Large result set (pagination missing)
4. Database connection pool exhausted

**Solutions**:

**Solution 1: Enable pagination**
```diff
# ❌ BAD: Fetch all 10,000 gates (10s response time)
- curl "http://localhost:8000/api/v1/gates"

# ✅ GOOD: Fetch 50 gates per page (<100ms)
+ curl "http://localhost:8000/api/v1/gates?page=1&page_size=50"
```

**Solution 2: Check database indexes**
```sql
-- Check for missing indexes
EXPLAIN ANALYZE
SELECT * FROM gates WHERE project_id = 'uuid' AND status = 'pending';

-- Add index if missing
CREATE INDEX idx_gates_project_status ON gates(project_id, status);
```

**Solution 3: Monitor Prometheus metrics**
```bash
# Check API latency p95
curl "http://localhost:9090/api/v1/query?query=histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))"

# If p95 > 0.1s (100ms), investigate slow queries
```

---

### ❌ **Issue 10: Database connection errors**

**Symptoms**:
```json
{
  "detail": "Database connection failed"
}
```

**Common Causes**:
1. PostgreSQL service down
2. Connection pool exhausted (>50 connections)
3. Database credentials changed
4. Network issue (firewall blocking port 5432)

**Solutions**:

**Solution 1: Check PostgreSQL service**
```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# Check PostgreSQL logs
docker-compose logs postgres | tail -50

# Restart PostgreSQL if needed
docker-compose restart postgres
```

**Solution 2: Check connection pool**
```bash
# Check active connections
psql -U sdlc_admin -d sdlc_orchestrator -c "SELECT count(*) FROM pg_stat_activity;"

# If > 50, increase pool size or kill idle connections
psql -U sdlc_admin -d sdlc_orchestrator -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle' AND state_change < now() - interval '5 minutes';"
```

**Solution 3: Verify credentials**
```bash
# Test database connection manually
docker exec -it sdlc_postgres psql -U sdlc_admin -d sdlc_orchestrator

# If connection fails, check docker-compose.yml credentials
```

---

## CORS & Cross-Origin Issues

### ❌ **Issue 11: CORS error in browser**

**Symptoms**:
```
Access to fetch at 'http://localhost:8000/api/v1/gates' from origin 'http://localhost:3000'
has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present.
```

**Common Causes**:
1. Frontend running on different port (localhost:3000 vs localhost:8000)
2. CORS not enabled in backend
3. Credentials (cookies) sent without `Access-Control-Allow-Credentials`
4. Preflight OPTIONS request failing

**Solutions**:

**Solution 1: Enable CORS in backend** (already configured)
```python
# backend/app/main.py - CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Solution 2: Include credentials in frontend**
```javascript
// Include credentials (cookies) in fetch requests
fetch('http://localhost:8000/api/v1/gates', {
  method: 'GET',
  credentials: 'include',  // ⚠️ Required for cookies
  headers: {
    'Authorization': `Bearer ${token}`
  }
});
```

**Solution 3: Handle preflight requests**
```bash
# Test preflight OPTIONS request
curl -X OPTIONS "http://localhost:8000/api/v1/gates" \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: GET" \
  -H "Access-Control-Request-Headers: authorization" \
  -v

# Should return 200 with CORS headers
```

---

## Gate Workflow Issues

### ❌ **Issue 12: Cannot approve gate - 403 Forbidden**

**Symptoms**:
```json
{
  "detail": "Insufficient permissions to approve gate"
}
```

**Common Causes**:
1. User lacks `gates:approve` permission
2. Gate already approved by this user
3. Gate requires 2+ approvers (multi-approval workflow)
4. Gate in wrong status (already approved/rejected)

**Solutions**:

**Solution 1: Check user permissions**
```bash
# Check current user permissions
curl "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer $TOKEN" | jq '.permissions'

# Response should include "gates:approve"
```

**Solution 2: Check gate status**
```bash
# Check gate status before approving
curl "http://localhost:8000/api/v1/gates/{id}" \
  -H "Authorization: Bearer $TOKEN" | jq '.status'

# Status must be "pending" to approve
```

**Solution 3: Use dedicated approval endpoint**
```diff
# ❌ DEPRECATED: Update gate status directly
- curl -X PUT "http://localhost:8000/api/v1/gates/{id}" \
-   -d '{"status": "approved"}'

# ✅ CORRECT: Use dedicated approval endpoint
+ curl -X POST "http://localhost:8000/api/v1/gates/{id}/approve" \
+   -H "Authorization: Bearer $TOKEN" \
+   -d '{"comment": "Approved after review"}'
```

---

### ❌ **Issue 13: Gate creation fails with 422 validation error**

**Symptoms**:
```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "gate_type"],
      "msg": "Invalid gate type. Must be one of: G0.1, G0.2, G1, G2, G3, G4, G5, G6, G7, G8"
    }
  ]
}
```

**Common Causes**:
1. Invalid `gate_type` value
2. Missing required field (`project_id`, `title`)
3. Invalid UUID format
4. Project does not exist

**Solutions**:

**Solution 1: Use valid gate types**
```bash
# Valid gate types (SDLC 5.1.3)
gate_types=(
  "G0.1"  # Problem Definition
  "G0.2"  # Solution Diversity
  "G1"    # Market Validation
  "G2"    # Design Ready
  "G3"    # Ship Ready
  "G4"    # Beta Success
  "G5"    # Growth Ready
  "G6"    # Scale Ready
  "G7"    # Operate Ready
  "G8"    # Sunset Ready
)
```

**Solution 2: Validate required fields**
```javascript
// Validate gate creation payload
const payload = {
  project_id: "550e8400-e29b-41d4-a716-446655440001",  // UUID v4
  gate_type: "G0.1",                                   // Valid gate type
  title: "Problem Definition Review",                  // Required
  status: "pending"                                    // Optional (default: pending)
};

// Validate UUID format
const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
if (!uuidRegex.test(payload.project_id)) {
  console.error("Invalid project_id UUID format");
}
```

---

## Policy Evaluation Errors

### ❌ **Issue 14: OPA policy evaluation fails**

**Symptoms**:
```json
{
  "detail": "Policy evaluation failed: rego_parse_error"
}
```

**Common Causes**:
1. Invalid Rego syntax
2. Missing input data
3. OPA service down
4. Policy compilation timeout

**Solutions**:

**Solution 1: Test policy locally with OPA CLI**
```bash
# Install OPA CLI
brew install opa

# Test policy syntax
opa test policies/security_review.rego

# Evaluate policy with sample data
echo '{"gate_type": "G0.1"}' | opa eval --data policies/security_review.rego 'data.sdlc.allow'
```

**Solution 2: Use policy testing endpoint**
```bash
# Test policy before creating
curl -X POST "http://localhost:8000/api/v1/policies/{id}/test" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "input": {
      "gate_type": "G0.1",
      "evidence_count": 3,
      "approvers_count": 2
    }
  }'
```

**Solution 3: Check OPA service health**
```bash
# Check if OPA is running
docker-compose ps opa

# Check OPA logs
docker-compose logs opa | tail -50

# Test OPA directly
curl "http://localhost:8181/health"
```

---

## Monitoring & Debugging

### ❌ **Issue 15: How to debug slow API requests?**

**Solution**: Use Prometheus + Grafana monitoring stack

**Step 1: Enable monitoring**
```bash
# Start monitoring stack
docker-compose -f docker-compose.monitoring.yml up -d

# Access Grafana: http://localhost:3001
# Login: admin / SecureGrafana123!
```

**Step 2: Check API latency dashboard**
1. Open Grafana (http://localhost:3001)
2. Navigate to "Performance" folder
3. Open "SDLC Orchestrator - Performance Monitoring" dashboard
4. Check "API Latency (p95)" panel

**Step 3: Identify slow endpoints**
```promql
# Query Prometheus for slowest endpoints (p95 latency)
topk(5, histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])))
```

**Step 4: Investigate database queries**
```sql
-- Find slow queries in PostgreSQL
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;
```

---

### ❌ **Issue 16: How to check API health status?**

**Solution**: Use health check endpoint

**Quick Health Check**:
```bash
# Health endpoint (no auth required)
curl "http://localhost:8000/api/v1/health"

# Response (200 OK):
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-12-09T10:00:00Z",
  "services": {
    "database": "up",
    "redis": "up",
    "minio": "up",
    "opa": "up"
  }
}
```

**Detailed Health Check**:
```bash
# Check individual services
docker-compose ps

# Expected output:
# NAME              STATUS
# sdlc_postgres     Up
# sdlc_redis        Up
# sdlc_minio        Up
# sdlc_opa          Up
# sdlc_api          Up
```

---

## Common HTTP Error Codes

### **400 Bad Request**
- **Cause**: Invalid request body, malformed JSON
- **Fix**: Validate JSON syntax, check required fields
- **Example**: Missing `Content-Type: application/json` header

### **401 Unauthorized**
- **Cause**: Missing or invalid access token
- **Fix**: Refresh token or re-login
- **Example**: Token expired (15-minute TTL)

### **403 Forbidden**
- **Cause**: Insufficient permissions
- **Fix**: Check user role and permissions
- **Example**: Non-admin user trying to delete policy

### **404 Not Found**
- **Cause**: Resource does not exist
- **Fix**: Verify UUID is correct, check if resource was deleted
- **Example**: Gate ID does not exist

### **409 Conflict**
- **Cause**: Resource already exists or state conflict
- **Fix**: Check resource uniqueness, verify current state
- **Example**: Approving already-approved gate

### **413 Payload Too Large**
- **Cause**: File size >100MB
- **Fix**: Compress file or split into chunks
- **Example**: Evidence file too large

### **422 Unprocessable Entity**
- **Cause**: Validation error (invalid field values)
- **Fix**: Check field formats, required fields, allowed values
- **Example**: Invalid email format, gate_type not in allowed list

### **429 Too Many Requests**
- **Cause**: Rate limit exceeded (100 req/min)
- **Fix**: Implement backoff strategy, reduce request frequency
- **Example**: 150 requests in 1 minute

### **500 Internal Server Error**
- **Cause**: Backend bug or service unavailable
- **Fix**: Check logs, restart services, contact support
- **Example**: Database connection failed

### **502 Bad Gateway**
- **Cause**: Upstream service down (Nginx → FastAPI)
- **Fix**: Check backend service status, restart containers
- **Example**: FastAPI crashed

### **503 Service Unavailable**
- **Cause**: Service temporarily down (maintenance)
- **Fix**: Wait and retry, check status page
- **Example**: Scheduled maintenance

### **504 Gateway Timeout**
- **Cause**: Request took too long (>60s)
- **Fix**: Optimize query, increase timeout, use pagination
- **Example**: Fetching 10,000 gates without pagination

---

## FAQ

### **Q1: How do I get my API credentials?**

**Development**:
```bash
# Use default test credentials
EMAIL="test@example.com"
PASSWORD="password123"
```

**Production**:
1. Sign up at https://sdlc-orchestrator.com
2. Verify email
3. Login to get access token
4. (Optional) Create API key for CI/CD: Settings → API Keys → Generate

---

### **Q2: What's the difference between access token and refresh token?**

| Feature | Access Token | Refresh Token |
|---------|--------------|---------------|
| **Purpose** | Authenticate API requests | Get new access token |
| **Lifetime** | 15 minutes | 30 days |
| **Storage** | Memory (not localStorage) | httpOnly cookie |
| **Invalidation** | Automatic (expiry) | Logout or rotation |
| **Usage** | Every API request | Token refresh only |

---

### **Q3: How do I know if my request is being rate limited?**

**Check response headers**:
```bash
curl -I "http://localhost:8000/api/v1/gates" \
  -H "Authorization: Bearer $TOKEN"

# Response headers:
X-RateLimit-Limit: 100          # Max requests per minute
X-RateLimit-Remaining: 75       # Requests left this minute
X-RateLimit-Reset: 1638360060   # Unix timestamp when limit resets
```

**Before rate limit (Remaining > 10)**: ✅ Safe to continue
**Near rate limit (Remaining < 10)**: ⚠️ Slow down
**Rate limited (Remaining = 0)**: ❌ Wait for reset

---

### **Q4: Can I upload files >100MB?**

**Short answer**: No, 100MB is the hard limit.

**Workarounds**:
1. Compress files (PDF: `gs -dPDFSETTINGS=/ebook`, ZIP: `7z a -mx=9`)
2. Split large files into <100MB chunks
3. Use external storage (Google Drive, Dropbox) and store link as metadata
4. Contact support for enterprise plan (200MB limit)

---

### **Q5: How do I test my integration locally?**

**Step 1: Start local development environment**
```bash
# Start all services
docker-compose up -d

# Wait for services to be ready (~30 seconds)
docker-compose ps
```

**Step 2: Run database migrations**
```bash
# Apply migrations
docker-compose exec api alembic upgrade head

# Seed test data (optional)
docker-compose exec api python scripts/seed_data.py
```

**Step 3: Test API endpoints**
```bash
# Use Postman Collection (auto-token management)
# OR use cURL examples
bash docs/02-Design-Architecture/04-API-Specifications/CURL-EXAMPLES.md
```

---

### **Q6: What's the recommended way to handle authentication in CI/CD?**

**Option A: API Keys** (recommended)
```yaml
# GitHub Actions
- name: Check gate status
  run: |
    curl "http://localhost:8000/api/v1/gates" \
      -H "X-API-Key: ${{ secrets.SDLC_API_KEY }}"
```

**Option B: Service Account** (for complex workflows)
```yaml
# GitHub Actions
- name: Login with service account
  run: |
    TOKEN=$(curl -X POST "http://localhost:8000/api/v1/auth/login" \
      -d '{"email": "${{ secrets.SERVICE_EMAIL }}", "password": "${{ secrets.SERVICE_PASSWORD }}"}' \
      | jq -r '.access_token')
    echo "::set-output name=token::$TOKEN"
```

---

### **Q7: How do I debug "Database connection failed" errors?**

**Step 1: Check if PostgreSQL is running**
```bash
docker-compose ps postgres
# Should show "Up" status
```

**Step 2: Check PostgreSQL logs**
```bash
docker-compose logs postgres | tail -50
# Look for connection errors, authentication failures
```

**Step 3: Test connection manually**
```bash
# Connect to PostgreSQL
docker exec -it sdlc_postgres psql -U sdlc_admin -d sdlc_orchestrator

# If connection fails, check credentials in docker-compose.yml
```

**Step 4: Restart PostgreSQL**
```bash
docker-compose restart postgres
```

---

### **Q8: What should I do if OPA policy evaluation is slow?**

**Check 1: Policy complexity**
```bash
# Count Rego rules (should be <50 per policy)
grep -c "^[a-z_]*\s*:=" policies/security_review.rego
```

**Check 2: Input data size**
```bash
# Keep input data <10KB (OPA limitation)
echo '{"gate_type": "G0.1"}' | wc -c
```

**Check 3: OPA service health**
```bash
# Check OPA response time
time curl "http://localhost:8181/health"
# Should be <10ms
```

---

### **Q9: How do I rollback a bad API deployment?**

**Docker Compose (development)**:
```bash
# Rollback to previous image
docker-compose down
docker-compose up -d --force-recreate
```

**Kubernetes (production)**:
```bash
# Rollback to previous revision
kubectl rollout undo deployment/sdlc-api

# Check rollout status
kubectl rollout status deployment/sdlc-api
```

---

### **Q10: Where can I find more help?**

**Resources**:
- **Documentation**: [API Developer Guide](./API-DEVELOPER-GUIDE.md)
- **cURL Examples**: [CURL-EXAMPLES.md](./CURL-EXAMPLES.md)
- **Postman Collection**: [SDLC-Orchestrator.postman_collection.json](./SDLC-Orchestrator.postman_collection.json)
- **OpenAPI Spec**: [openapi.yml](./openapi.yml)
- **Changelog**: [API-CHANGELOG.md](./API-CHANGELOG.md)

**Support Channels**:
- **GitHub Issues**: https://github.com/sdlc-orchestrator/sdlc-orchestrator/issues
- **Slack**: #api-developers
- **Email**: api-support@sdlc-orchestrator.com
- **Stack Overflow**: Tag `sdlc-orchestrator`

---

**Troubleshooting Guide Status**: ✅ **COMPLETE**
**Framework**: ✅ **SDLC 5.1.3 COMPLETE LIFECYCLE**
**Authorization**: ✅ **BACKEND LEAD + DEVOPS LEAD + CTO APPROVED**

---

*SDLC Orchestrator API - Clear error messages. Actionable solutions. Developer-first support.* 🔧

**Last Updated**: December 9, 2025
**Owner**: Backend Lead + DevOps Lead
**Status**: ✅ ACTIVE - WEEK 5 DAY 4 (API DOCUMENTATION FINALIZATION)
**Next Review**: Weekly (every Monday)
