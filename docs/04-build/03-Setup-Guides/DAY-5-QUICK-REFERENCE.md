# Week 7 Day 5 Morning - Quick Reference Card
**SDLC Orchestrator - Essential Commands**

---

## 🚀 **QUICK START (Copy-Paste Ready)**

```bash
# Navigate to project
cd /Users/dttai/Documents/Python/02.MTC/SDLC\ Orchestrator/SDLC-Orchestrator

# Set Python path
export PYTHONPATH="/Users/dttai/Documents/Python/02.MTC/SDLC Orchestrator/SDLC-Orchestrator/backend"
```

---

## 🔧 **STEP 1: FIX MINIO (5-10 minutes)**

```bash
# Check current status
docker-compose ps minio

# Run automated fix
./scripts/fix-minio-health.sh

# Validate fix
./scripts/validate-minio-health.sh
```

**Expected Result**: All validations pass, MinIO healthy

---

## 🧪 **STEP 2: RUN TESTS (30 minutes)**

### **Quick Tests** (11 tests, <1 minute)

```bash
pytest tests/integration/test_minio_integration.py \
  -v \
  -m "minio and not slow" \
  --tb=short
```

**Expected**: 11 passed in <1 minute

---

### **Full Suite with Coverage** (13 tests, <2 minutes)

```bash
pytest tests/integration/test_minio_integration.py \
  -v \
  --cov=backend/app/services/minio_service \
  --cov-report=term \
  --cov-report=html:htmlcov/minio \
  --tb=short
```

**Expected**: 13 passed, 60%+ coverage in <2 minutes

---

### **View Coverage Report**

```bash
open htmlcov/minio/index.html
```

---

## 📊 **STEP 3: CHECK RESULTS**

```bash
# Generate JSON report
pytest tests/integration/test_minio_integration.py \
  -v \
  --json-report \
  --json-report-file=/tmp/minio_test_results.json \
  --cov=backend/app/services/minio_service \
  --cov-report=json:/tmp/minio_coverage.json

# View test results
cat /tmp/minio_test_results.json | python -m json.tool | grep -A 5 "summary"

# View coverage summary
cat /tmp/minio_coverage.json | python -m json.tool | grep "percent_covered"
```

---

## 🔍 **TROUBLESHOOTING COMMANDS**

### **MinIO Health Issues**

```bash
# Check logs
docker logs sdlc-minio --tail 100

# Check health endpoint
curl -v http://localhost:9000/minio/health/ready

# Check inside container
docker exec sdlc-minio curl -f http://localhost:9000/minio/health/ready

# Check resource usage
docker stats sdlc-minio --no-stream

# Restart MinIO
docker-compose restart minio
sleep 30
docker-compose ps minio
```

---

### **Test Execution Issues**

```bash
# Kill hung tests
pkill -9 -f "pytest.*minio"

# Run single test for debugging
pytest tests/integration/test_minio_integration.py::TestMinioBucketManagement::test_ensure_bucket_exists -vv

# Skip slow tests
pytest tests/integration/test_minio_integration.py -v -m "minio and not slow"

# Increase timeout
pytest tests/integration/test_minio_integration.py -v --timeout=300
```

---

### **Coverage Issues**

```bash
# Check what's covered
pytest tests/integration/test_minio_integration.py \
  --cov=backend/app/services/minio_service \
  --cov-report=term-missing

# View specific file coverage
coverage report --include="backend/app/services/minio_service.py"

# Generate detailed HTML report
coverage html --directory=htmlcov/minio
open htmlcov/minio/backend/app/services/minio_service.py.html
```

---

## 📝 **GIT COMMIT**

```bash
# Stage changes
git add tests/integration/test_minio_integration.py
git add scripts/fix-minio-health.sh
git add scripts/validate-minio-health.sh
git add docs/03-Development-Implementation/02-Setup-Guides/

# Create commit (fill in metrics)
git commit -m "feat: Week 7 Day 5 Morning - MinIO Tests Complete

- MinIO health fixed (version updated)
- 13/13 tests passing
- Coverage: ___%  (target: 60%+)
- Test execution: <2 minutes

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## ✅ **SUCCESS CRITERIA**

- [ ] MinIO healthy: `docker-compose ps minio` shows `(healthy)`
- [ ] Quick tests: `11 passed` in <1 minute
- [ ] Full suite: `13 passed` in <2 minutes
- [ ] Coverage: `60%+` in report
- [ ] HTML report: Opens successfully
- [ ] Git commit: Created successfully

---

## 📞 **ESCALATION**

**Blocked >1 hour?**

1. MinIO health → DevOps Lead
2. Test failures → Backend Lead
3. Coverage issues → QA Lead
4. Critical blocker → CTO

---

## 🎯 **METRICS TO DOCUMENT**

Fill in after running tests:

```
Total Tests:           13
Passing:              _____
Failed:               _____
Skipped:              _____
Execution Time:       _____ seconds

Previous Coverage:     25% (32/128 lines)
Current Coverage:      _____% (_____/128 lines)
Coverage Increase:     +_____%
Target Met:           yes / no
```

---

## 📚 **FULL DOCUMENTATION**

For detailed instructions, see:
- `docs/03-Development-Implementation/02-Setup-Guides/DAY-5-MORNING-RUNBOOK.md`
- `docs/03-Development-Implementation/02-Setup-Guides/MINIO-TROUBLESHOOTING-GUIDE.md`

---

**Document**: Quick Reference Card
**Version**: 1.0.0
**Date**: November 25, 2025
**Framework**: SDLC 4.9 Complete Lifecycle
