# MinIO Troubleshooting Guide - Week 7 Day 4 Issue
**SDLC Orchestrator - Infrastructure Recovery Plan**

---

## 🚨 CRITICAL ISSUE IDENTIFIED

**Date**: November 25, 2025
**Issue**: MinIO container persistently unhealthy (3+ hours)
**Impact**: Integration tests blocked, unable to measure MinIO service coverage
**Priority**: P0 - BLOCKER for Week 7 completion

---

## 📊 PROBLEM SUMMARY

### Current State

```bash
$ docker-compose ps minio
NAME         STATUS
sdlc-minio   Up 2 hours (unhealthy)  # ← Health check failing
```

**Symptoms**:
- Container running but health check reports unhealthy
- S3 API responds to requests (port 9000 accessible)
- Integration tests hang indefinitely on MinIO operations
- Test execution times exceed 3+ minutes per test

**Evidence**:
```
MinIO Logs:
- "Standard parity is set to 0. This can lead to data loss"
- "You are running an older version of MinIO released 2 years before the latest release"
- MinIO version: RELEASE.2024-01-01T16-36-33Z (2 years old)
```

---

## 🔍 ROOT CAUSE ANALYSIS

### Hypothesis 1: Outdated MinIO Version ⭐ **MOST LIKELY**

**Evidence**:
- Current version: `RELEASE.2024-01-01T16-36-33Z` (January 2024)
- Latest version: `RELEASE.2024-11-01T...` (November 2024)
- Age: 2 years behind latest release
- Warning: "Update: Run `mc admin update`"

**Impact**:
- Health endpoint may have changed
- Bug fixes not applied
- Security vulnerabilities possible

**Solution**: Update to latest stable MinIO version

---

### Hypothesis 2: Health Check Misconfiguration

**Current Health Check** (docker-compose.yml):
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

**Issues**:
- Health endpoint path may be incorrect for old MinIO version
- `curl` may not be installed in MinIO container
- Timeout (10s) may be too short for slow responses

**Solution**: Use MinIO-native health check command

---

### Hypothesis 3: Storage Configuration Issue

**Warning**: "Standard parity is set to 0. This can lead to data loss"

**Analysis**:
- Single-node MinIO deployment (no erasure coding)
- Parity set to 0 (degraded mode)
- May cause health check to report degraded state as unhealthy

**Solution**: Accept single-node configuration, adjust health check expectations

---

### Hypothesis 4: Resource Constraints

**Current Resource Limits**: None specified

**Potential Issues**:
- CPU/memory starvation
- Slow I/O operations
- Network congestion

**Solution**: Set explicit resource limits and requests

---

## ✅ RECOMMENDED SOLUTIONS (Priority Order)

### Solution 1: Update MinIO to Latest Version (HIGHEST PRIORITY)

**Change**: Update docker-compose.yml

```yaml
# BEFORE (Current - 2 years old):
services:
  minio:
    image: minio/minio:RELEASE.2024-01-01T16-36-33Z

# AFTER (Latest stable):
services:
  minio:
    image: minio/minio:RELEASE.2024-11-07T00-52-20Z
    # Or use latest tag (with caution):
    # image: minio/minio:latest
```

**Steps**:
```bash
# 1. Backup existing MinIO data (if needed)
docker cp sdlc-minio:/data ./minio-backup

# 2. Stop old container
docker-compose down minio

# 3. Update docker-compose.yml (image version)

# 4. Pull new image
docker-compose pull minio

# 5. Start new container
docker-compose up -d minio

# 6. Wait for health check
watch -n 2 'docker-compose ps minio | grep health'

# 7. Verify S3 API
curl -I http://localhost:9000
```

**Expected Outcome**:
- Health check passes
- Modern MinIO features available
- Bug fixes applied

**Risk**: LOW (MinIO is backward compatible)

---

### Solution 2: Fix Health Check Configuration

**Change**: Use MinIO-native health check

```yaml
# BEFORE (Current - using curl):
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s

# AFTER (MinIO-native check):
healthcheck:
  test: ["CMD", "mc", "ready", "local"]
  interval: 10s        # ← Faster checks
  timeout: 5s          # ← Shorter timeout
  retries: 5           # ← More retries
  start_period: 30s    # ← Adequate startup time
```

**Note**: Requires MinIO Client (mc) to be available in container (included by default)

**Alternative** (if mc not available):
```yaml
healthcheck:
  test: ["CMD-SHELL", "curl -f http://localhost:9000/minio/health/ready || exit 1"]
  interval: 10s
  timeout: 5s
  retries: 5
  start_period: 30s
```

**Steps**:
```bash
# 1. Update docker-compose.yml

# 2. Restart MinIO
docker-compose up -d minio --force-recreate

# 3. Monitor health
docker-compose ps minio
```

**Expected Outcome**: Health check passes

**Risk**: VERY LOW (configuration change only)

---

### Solution 3: Set Resource Limits

**Change**: Add resource constraints

```yaml
services:
  minio:
    image: minio/minio:RELEASE.2024-11-07T00-52-20Z
    deploy:
      resources:
        limits:
          cpus: '1.0'      # Max 1 CPU core
          memory: 512M      # Max 512MB RAM
        reservations:
          cpus: '0.5'      # Guarantee 0.5 CPU
          memory: 256M      # Guarantee 256MB RAM
```

**Steps**:
```bash
# 1. Update docker-compose.yml

# 2. Restart with resource limits
docker-compose up -d minio --force-recreate

# 3. Monitor resource usage
docker stats sdlc-minio
```

**Expected Outcome**:
- Predictable resource allocation
- Faster responses
- Better performance

**Risk**: LOW (512MB is adequate for dev environment)

---

### Solution 4: Complete MinIO Configuration Overhaul

**Full docker-compose.yml MinIO Section** (RECOMMENDED):

```yaml
services:
  minio:
    image: minio/minio:RELEASE.2024-11-07T00-52-20Z
    container_name: sdlc-minio
    restart: unless-stopped

    # Environment
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
      MINIO_BROWSER: "on"
      MINIO_PROMETHEUS_AUTH_TYPE: public

    # Ports
    ports:
      - "9000:9000"  # S3 API
      - "9001:9001"  # Console

    # Storage
    volumes:
      - minio_data:/data

    # Command
    command: server /data --console-address ":9001"

    # Health Check (MinIO-native)
    healthcheck:
      test: ["CMD", "mc", "ready", "local"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s

    # Resource Limits
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M

    # Network
    networks:
      - sdlc-network

volumes:
  minio_data:
    driver: local

networks:
  sdlc-network:
    driver: bridge
```

**Steps**:
```bash
# 1. Backup current docker-compose.yml
cp docker-compose.yml docker-compose.yml.backup

# 2. Update MinIO section with new configuration

# 3. Stop all services
docker-compose down

# 4. Remove old MinIO container and volume (CAUTION: loses data)
docker rm -f sdlc-minio
docker volume rm sdlc-orchestrator_minio_data

# 5. Start services with new config
docker-compose up -d

# 6. Wait for health check
sleep 30
docker-compose ps minio

# 7. Verify MinIO is healthy
curl http://localhost:9000/minio/health/ready
```

**Expected Outcome**:
- Clean MinIO installation
- Modern version
- Proper health checks
- Resource limits

**Risk**: MEDIUM (data loss if not backed up first)

---

## 🧪 VALIDATION STEPS

### After Applying Fix:

1. **Check Container Health**:
```bash
docker-compose ps minio
# Expected: Up X seconds (healthy)
```

2. **Test S3 API**:
```bash
curl http://localhost:9000/minio/health/ready
# Expected: 200 OK

curl -I http://localhost:9000
# Expected: 400 Bad Request (normal for unauthenticated request)
```

3. **Test MinIO Console**:
```bash
open http://localhost:9001
# Login: minioadmin / minioadmin
# Verify: Buckets visible, no errors
```

4. **Run MinIO Integration Tests**:
```bash
cd /Users/dttai/Documents/Python/02.MTC/SDLC\ Orchestrator/SDLC-Orchestrator

export PYTHONPATH="/Users/dttai/Documents/Python/02.MTC/SDLC Orchestrator/SDLC-Orchestrator/backend"

# Run quick tests (skip slow multipart uploads)
pytest tests/integration/test_minio_integration.py \
  -v \
  -m "minio and not slow" \
  --tb=short

# Expected: 11 tests passing (bucket, upload, download, SHA256, presigned, metadata)
```

5. **Run All MinIO Tests** (including slow):
```bash
pytest tests/integration/test_minio_integration.py \
  -v \
  --cov=backend/app/services/minio_service \
  --cov-report=term

# Expected: 13 tests passing (including 6MB/10MB multipart uploads)
# Expected Coverage: 60%+ (up from 25%)
```

---

## 📋 DAY 5 MORNING ACTION PLAN

### Step 1: Diagnose MinIO Issue (15 minutes)

```bash
# Check MinIO logs
docker logs sdlc-minio --tail 100

# Check MinIO health endpoint directly
docker exec sdlc-minio mc ready local

# Check resource usage
docker stats sdlc-minio --no-stream

# Check MinIO version
docker exec sdlc-minio minio --version
```

**Decision Point**:
- If logs show clear error → Fix specific issue
- If version is old → Proceed to update
- If resource-constrained → Add limits

---

### Step 2: Apply Fix (30 minutes)

**Option A: Quick Fix** (if time-constrained)
```bash
# Just restart with force recreate
docker-compose up -d minio --force-recreate

# Wait and check health
sleep 30
docker-compose ps minio
```

**Option B: Version Update** (RECOMMENDED)
```bash
# 1. Update docker-compose.yml (MinIO version)
# 2. docker-compose pull minio
# 3. docker-compose up -d minio --force-recreate
# 4. Wait for health check (30-60s)
```

**Option C: Full Overhaul** (if other fixes fail)
```bash
# Use complete configuration from Solution 4 above
```

---

### Step 3: Validate Fix (10 minutes)

```bash
# Health check
docker-compose ps minio | grep healthy

# S3 API test
curl http://localhost:9000/minio/health/ready

# Quick integration test (1 test)
pytest tests/integration/test_minio_integration.py::TestMinioBucketManagement::test_ensure_bucket_exists -v
```

**Success Criteria**:
- ✅ Health check passes
- ✅ S3 API responds
- ✅ At least 1 integration test passes

---

### Step 4: Run Full MinIO Test Suite (20 minutes)

```bash
# Run all MinIO tests
pytest tests/integration/test_minio_integration.py \
  -v \
  --cov=backend/app/services/minio_service \
  --cov-report=term \
  --cov-report=html:htmlcov/minio

# Check coverage report
open htmlcov/minio/index.html
```

**Success Criteria**:
- ✅ 11+ tests passing (13 total if including slow tests)
- ✅ MinIO service coverage 60%+ (from 25%)
- ✅ Zero test failures
- ✅ No test hangs (all complete within 5 minutes)

---

## 🔄 ROLLBACK PLAN (If Fix Fails)

### Emergency Rollback Steps:

1. **Restore Previous Configuration**:
```bash
# Restore backup
cp docker-compose.yml.backup docker-compose.yml

# Restart with old config
docker-compose down
docker-compose up -d
```

2. **Use MinIO Mock Library** (LAST RESORT - violates Zero Mock Policy):
```bash
# Install minio-py for testing
pip install minio

# Create mock MinIO service for tests only
# NOTE: Must escalate to CTO for approval
```

3. **Skip MinIO Tests Temporarily**:
```bash
# Mark tests as skipped
pytest tests/integration/test_minio_integration.py -v -m "not minio"

# Document in GitHub issue
# Continue with other Day 5 work (OPA tests, load testing)
```

**Escalation Path**:
- If 2+ hours spent on MinIO fix → Escalate to DevOps Lead
- If EOD Day 5 and MinIO still unhealthy → Escalate to CTO (accept lower coverage)

---

## 📊 SUCCESS METRICS

### MinIO Health Indicators:

| Metric | Current | Target | Status |
|--------|---------|--------|--------|
| Container Health | unhealthy | healthy | ⚠️ |
| S3 API Response | 400ms+ | <100ms | ⚠️ |
| Test Execution Time | 3+ min/test | <30s/test | ⚠️ |
| Test Pass Rate | 0% (hung) | 100% | ⚠️ |
| Service Coverage | 25% | 60%+ | ⚠️ |

### Post-Fix Targets:

- ✅ Health check: `(healthy)` status
- ✅ S3 API latency: <100ms p95
- ✅ Test execution: <2 minutes for 13 tests
- ✅ Test pass rate: 100% (13/13 passing)
- ✅ Coverage: 60%+ MinIO service (77/128 lines)

---

## 🎯 PREVENTION FOR FUTURE

### Recommended Practices:

1. **Daily Health Checks**:
```bash
# Add to morning routine
docker-compose ps | grep unhealthy

# Set up health check alerts (future)
```

2. **Version Pinning**:
```yaml
# Pin to specific version (not :latest)
image: minio/minio:RELEASE.2024-11-07T00-52-20Z

# Update quarterly (not automatically)
```

3. **Resource Monitoring**:
```bash
# Monitor resource usage weekly
docker stats --no-stream
```

4. **Regular Updates**:
- Monthly: Check for MinIO updates
- Quarterly: Apply updates in staging first
- Annually: Major version upgrades

---

## 📝 LESSONS LEARNED

### What Went Wrong:

1. **Outdated Dependencies**:
   - MinIO version 2 years old
   - No update schedule documented

2. **Health Check Oversight**:
   - Container unhealthy for 3+ hours before discovery
   - No monitoring alerts configured

3. **Resource Management**:
   - No resource limits set
   - Unpredictable performance

### What Went Right:

1. **Early Detection**:
   - Blocker found during Day 4 (not Day 5 morning)
   - Clear recovery plan documented

2. **Test Quality**:
   - MinIO tests created before service was healthy
   - Zero Mock Policy maintained

3. **Documentation**:
   - Comprehensive troubleshooting guide created
   - Recovery plan for Day 5

---

## 🚀 CONCLUSION

**MinIO Issue Summary**:
- Root Cause: Outdated version + misconfigured health check
- Impact: Day 4 test execution blocked
- Solution: Update to latest MinIO version + fix health check
- Timeline: 1 hour fix time on Day 5 morning
- Confidence: 90% (well-understood problem)

**Day 5 Recovery Plan**:
1. Morning (9am): Apply MinIO fix (1 hour)
2. Morning (10am): Run MinIO tests (30 minutes)
3. Morning (11am): Fix evidence upload bug (1 hour)
4. Afternoon: OPA tests + load testing (4 hours)

**Gate G3 Impact**: Minimal (1-day delay, recoverable)

---

**Document Status**: ✅ **COMPLETE**
**Framework**: ✅ **SDLC 4.9 COMPLETE LIFECYCLE**
**Authority**: Backend Lead + DevOps Lead
**Next Review**: Day 5 Morning (Post-Fix Validation)

---

*"Infrastructure issues are learning opportunities. We document, diagnose, and deploy fixes with discipline."* ⚔️
