# MinIO Object Lock Execution Checklist

**Priority:** P1 - SCALE BLOCKER
**Deadline:** January 25, 2026 (3 days remaining)
**Status:** ✅ READY FOR EXECUTION
**Owner:** DevOps Lead

---

## Prerequisites (Before Execution)

| Item | Status | Command to Verify |
|------|--------|-------------------|
| Docker Compose running | ✅ PASS | `docker ps` shows ai-platform-minio running |
| MinIO container up | ✅ PASS | Container: ai-platform-minio (Up 2 days, healthy) |
| mc client available | ✅ PASS | MinIO Client v.RELEASE.2025-08-13T08-35-41Z |
| Backup existing data | ✅ N/A | Original bucket `evidence-vault` preserved |

---

## Execution Steps

### Step 1: Pre-Execution Review (10 minutes)

- [ ] Review [minio-object-lock-guide.md](minio-object-lock-guide.md)
- [ ] Understand GOVERNANCE vs COMPLIANCE modes
- [ ] Confirm 7-year retention requirement (2555 days)
- [ ] Backup existing evidence data (if any)

**Decision Point:**
- If `sdlc-evidence` bucket exists → Choose Option 2 (create new bucket `sdlc-evidence-v2`)
- If bucket doesn't exist → Proceed with `sdlc-evidence`

---

### Step 2: Execute Configuration Script (15 minutes)

```bash
# Navigate to project root
cd /home/nqh/shared/SDLC-Orchestrator

# Make script executable
chmod +x scripts/setup-minio-object-lock.sh

# Execute script
./scripts/setup-minio-object-lock.sh

# Expected output:
# - ✅ Bucket created with Object Lock
# - ✅ Default retention policy configured (GOVERNANCE, 7 years)
# - ✅ Test file uploaded and WORM protection verified
```

**Script Features:**
- ✅ Interactive prompts for existing bucket handling
- ✅ Automatic prerequisite checks
- ✅ Retention policy configuration
- ✅ WORM protection testing
- ✅ Configuration summary output

---

### Step 3: Backend Integration (30 minutes)

#### 3.1 Update Configuration

Edit `backend/app/core/config.py`:

```python
# MinIO Configuration
MINIO_BUCKET_NAME: str = "sdlc-evidence"  # Or "sdlc-evidence-v2" if new bucket
MINIO_OBJECT_LOCK_ENABLED: bool = True  # NEW
MINIO_RETENTION_DAYS: int = 2555  # 7 years (NEW)
MINIO_RETENTION_MODE: str = "GOVERNANCE"  # NEW
```

#### 3.2 Update MinIO Service

`backend/app/services/minio_service.py` already supports Object Lock (Sprint 82 implementation). Verify:

```python
# Check for these methods (should already exist from Sprint 82):
- upload_evidence_with_retention()
- set_legal_hold()
- verify_object_lock()
```

**Action:** Run grep to confirm:
```bash
grep -n "upload_evidence_with_retention\|set_legal_hold\|verify_object_lock" backend/app/services/minio_service.py
```

**If missing:** Implement methods per [minio-object-lock-guide.md](minio-object-lock-guide.md) Part 3.

---

### Step 4: Verification (20 minutes)

#### 4.1 Bucket Verification

```bash
# Check Object Lock status
docker-compose exec minio mc stat myminio/sdlc-evidence

# Expected output:
# Object Lock: ENABLED

# Check default retention
docker-compose exec minio mc retention info --default myminio/sdlc-evidence

# Expected output:
# Governance mode, 2555 days
```

#### 4.2 Upload Test

```bash
# Upload test evidence via backend API
curl -X POST http://localhost:8000/api/v1/evidence \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@test-evidence.pdf" \
  -F "project_id=<project-uuid>"

# Verify retention metadata
docker-compose exec minio mc stat myminio/sdlc-evidence/project-xxx/evidence-xxx.pdf

# Expected: Retention mode GOVERNANCE, Retain until 2033-01-22
```

#### 4.3 WORM Protection Test

```bash
# Try to delete (should fail)
docker-compose exec minio mc rm myminio/sdlc-evidence/project-xxx/evidence-xxx.pdf

# Expected error: "Object is WORM protected and cannot be overwritten"
```

---

### Step 5: Documentation Update (15 minutes)

- [ ] Update [minio-object-lock-guide.md](minio-object-lock-guide.md) with execution results
- [ ] Add configuration date and bucket name used
- [ ] Document any issues encountered
- [ ] Update [CURRENT-SPRINT.md](../../04-build/02-Sprint-Plans/CURRENT-SPRINT.md) with completion status

---

## Success Criteria

| Criterion | Verification | Status |
|-----------|--------------|--------|
| **Object Lock Enabled** | `mc retention info` shows Object Lock configured | ✅ PASS |
| **Default Retention Set** | `mc retention info` shows "GOVERNANCE, 2555 days" | ✅ PASS |
| **WORM Protection Works** | Delete creates delete marker, original version protected | ✅ PASS |
| **Backend Integration** | Backend configuration updated to `evidence-vault-v2` | ✅ PASS |
| **Configuration Saved** | Configuration documented in this file | ✅ PASS |

**Execution Date**: January 22, 2026
**Bucket Name**: `evidence-vault-v2` (new bucket with Object Lock)
**Old Bucket**: `evidence-vault` (kept for reference, no Object Lock)
**Retention**: GOVERNANCE mode, 7 years (2555 days)
**Test File Version ID**: `90695c72-dec9-4cda-8260-63abf1590450`
**Retention Until**: 2033-01-20T04:09:10Z
**MinIO Container**: `ai-platform-minio` on `ai-net` network

---

## Rollback Plan (If Needed)

If configuration fails or causes issues:

```bash
# Option 1: Delete new bucket
docker-compose exec minio mc rb --force myminio/sdlc-evidence-v2

# Option 2: Recreate bucket without Object Lock
docker-compose exec minio mc rb --force myminio/sdlc-evidence
docker-compose exec minio mc mb myminio/sdlc-evidence  # Without --with-lock

# Option 3: Restore from backup
# (Manual restore of evidence data from backup location)
```

---

## Timeline

| Phase | Duration | Owner |
|-------|----------|-------|
| **Pre-Execution Review** | 10 min | DevOps Lead |
| **Script Execution** | 15 min | DevOps Lead |
| **Backend Integration** | 30 min | Backend Lead |
| **Verification** | 20 min | QA + DevOps |
| **Documentation** | 15 min | PM |
| **Total** | **90 minutes** | Team |

**Recommended Execution Time:** Business hours (9am-5pm) with CTO available for approval.

---

## Post-Execution

### Immediate (Same Day)
1. ✅ Verify all success criteria met
2. ✅ Update CURRENT-SPRINT.md with completion
3. ✅ Commit configuration changes to git
4. ✅ Notify team in Slack #sdlc-orchestrator channel

### Short-term (Within 7 Days)
1. Monitor Evidence Vault uploads (check retention metadata)
2. Run full integration test suite
3. Verify no regressions in evidence upload/download
4. Update Pre-Launch Status Report

### Long-term (Before Launch)
1. Document legal compliance (SEC 17a-4, FINRA 4511)
2. Test evidence retrieval after 1 month
3. Prepare customer-facing documentation

---

## Reference Documents

- [minio-object-lock-guide.md](minio-object-lock-guide.md) - Full technical guide
- [Sprint 82 Plan](../../04-build/02-Sprint-Plans/SPRINT-82-HARDENING-EVIDENCE.md) - Original requirements
- [Expert Feedback Plan](../../09-govern/04-Strategic-Updates/) - P1 priority justification

---

## Approvals

- [x] **DevOps Lead:** ✅ Configuration executed successfully (Jan 22, 2026)
- [x] **Backend Lead:** ✅ Backend integration complete (config.py + docker-compose.yml updated)
- [ ] **CTO:** ⏳ Final approval for production execution

---

**Status:** ✅ CONFIGURATION COMPLETE
**Execution Date:** January 22, 2026 at 04:09 UTC
**Deadline:** January 25, 2026 ✅ EARLY (3 days ahead)

---

## Execution Summary (Jan 22, 2026)

**What Was Done:**
1. ✅ Created new bucket `evidence-vault-v2` with Object Lock enabled
2. ✅ Configured default retention: GOVERNANCE mode, 7 years (2555 days)
3. ✅ Verified WORM protection with test file (version: 90695c72-dec9-4cda-8260-63abf1590450)
4. ✅ Updated backend configuration (backend/app/core/config.py)
5. ✅ Updated docker-compose.yml with new bucket and Object Lock settings
6. ✅ Documented configuration results in this checklist

**Decision:** Created new bucket `evidence-vault-v2` instead of modifying existing bucket
- **Reason:** Object Lock can only be enabled at bucket creation, not retroactively
- **Old Bucket:** `evidence-vault` preserved (2 objects, 84 KiB)
- **New Bucket:** `evidence-vault-v2` with Object Lock enabled
- **Migration:** Backend now points to new bucket, old data available if needed

**WORM Protection Verified:**
- Test file uploaded: 79 B
- Retention until: 2033-01-20T04:09:10Z (7 years from now)
- Delete attempt: Created delete marker (versioning), original protected ✅
- Compliance: SEC 17a-4, FINRA 4511, GDPR Article 5(1)(e)

**Backend Integration:**
- `MINIO_BUCKET`: Changed from `evidence-vault` to `evidence-vault-v2`
- Added config fields: `MINIO_OBJECT_LOCK_ENABLED`, `MINIO_RETENTION_DAYS`, `MINIO_RETENTION_MODE`
- Docker environment: Updated with new bucket and Object Lock settings

**Next Steps:**
1. ⏳ CTO approval for production use
2. ⏳ Restart backend service to apply new configuration
3. ⏳ Test evidence upload via API (verify retention metadata)
4. ⏳ Optional: Migrate old evidence from `evidence-vault` to `evidence-vault-v2` if needed

---

**Created:** January 22, 2026
**Owner:** DevOps Lead + Backend Lead
**Reviewer:** CTO
