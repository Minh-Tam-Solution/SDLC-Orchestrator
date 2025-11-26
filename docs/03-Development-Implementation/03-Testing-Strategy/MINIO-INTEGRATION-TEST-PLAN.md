# MinIO Integration Test Plan
## Coverage Improvement Strategy for Week 7 Day 4

**Date:** November 23, 2025  
**Target:** Increase MinIO service coverage from 25% → 60%+ (+35%)  
**Impact:** +4-5% total project coverage  
**Author:** Backend Lead + QA Lead  
**Status:** 📋 **PLAN READY** - Ready for implementation

---

## 🎯 OBJECTIVE

Add comprehensive integration tests for `MinIOService` to improve test coverage and validate S3-compatible storage functionality.

**Current Coverage:** 25% (6/23 methods tested indirectly via API)  
**Target Coverage:** 60%+ (14/23 methods directly tested)  
**Coverage Gap:** -35% (8 methods untested)

---

## 📊 COVERAGE ANALYSIS

### Current Test Coverage (25%)

**Methods Tested via Evidence API:**
- ✅ `upload_file()` - Indirectly via `POST /evidence/upload`
- ✅ `compute_sha256()` - Indirectly via upload workflow
- ⏳ `download_file()` - Partial (via `GET /evidence/{id}/download`)

**Methods NOT Tested:**
- ❌ `ensure_bucket_exists()` - Bucket management
- ❌ `upload_multipart()` - Large file uploads (>5MB)
- ❌ `verify_sha256()` - Hash verification
- ❌ `generate_presigned_upload_url()` - Presigned upload URLs
- ❌ `generate_presigned_download_url()` - Presigned download URLs
- ❌ Error handling paths (ClientError, network failures)
- ❌ Multipart upload failure/abort scenarios

---

## 🧪 TEST PLAN

### Test File: `tests/integration/test_minio_service_integration.py`

**Target:** 12+ integration tests covering all MinIO service methods

---

### Test Suite 1: Bucket Management (2 tests)

#### Test 1.1: `test_ensure_bucket_exists_success`
**Objective:** Verify bucket creation when bucket doesn't exist

**Test Steps:**
1. Delete bucket if exists (cleanup)
2. Call `minio_service.ensure_bucket_exists()`
3. Verify bucket exists using `head_bucket()`
4. Verify bucket can store objects

**Expected Result:** Bucket created successfully, no exceptions

**Coverage:** `ensure_bucket_exists()` - new bucket path

---

#### Test 1.2: `test_ensure_bucket_exists_already_exists`
**Objective:** Verify no error when bucket already exists

**Test Steps:**
1. Create bucket manually
2. Call `minio_service.ensure_bucket_exists()`
3. Verify no exceptions raised

**Expected Result:** No error, method returns successfully

**Coverage:** `ensure_bucket_exists()` - existing bucket path

---

### Test Suite 2: File Upload (3 tests)

#### Test 2.1: `test_upload_file_success`
**Objective:** Verify successful file upload with SHA256 integrity

**Test Steps:**
1. Create test file (BytesIO with known content)
2. Call `minio_service.upload_file()`
3. Verify return values (bucket, key, sha256_hash)
4. Verify SHA256 hash matches computed hash
5. Verify file exists in MinIO via `download_file()`

**Expected Result:** File uploaded, SHA256 hash correct, file retrievable

**Coverage:** `upload_file()` - happy path

---

#### Test 2.2: `test_upload_file_with_metadata`
**Objective:** Verify custom metadata is stored correctly

**Test Steps:**
1. Create test file with metadata: `{"gate_id": "123", "user_id": "456"}`
2. Call `minio_service.upload_file()` with metadata
3. Verify metadata stored in MinIO object
4. Verify SHA256 hash added to metadata automatically

**Expected Result:** Metadata stored, SHA256 in metadata

**Coverage:** `upload_file()` - metadata handling

---

#### Test 2.3: `test_upload_file_invalid_bucket`
**Objective:** Verify error handling for invalid bucket configuration

**Test Steps:**
1. Temporarily set invalid bucket name
2. Call `minio_service.upload_file()`
3. Verify `ClientError` raised with appropriate error code

**Expected Result:** `ClientError` raised (bucket not found)

**Coverage:** `upload_file()` - error handling path

---

### Test Suite 3: Multipart Upload (3 tests)

#### Test 3.1: `test_upload_multipart_success`
**Objective:** Verify successful multipart upload for large files

**Test Steps:**
1. Create large test file (>5MB, e.g., 6MB)
2. Call `minio_service.upload_multipart()` with `part_size=5MB`
3. Verify return values (bucket, key, sha256_hash)
4. Verify file uploaded in multiple parts (check logs)
5. Verify file integrity via `download_file()` + SHA256 verification

**Expected Result:** Large file uploaded via multipart, integrity verified

**Coverage:** `upload_multipart()` - happy path

---

#### Test 3.2: `test_upload_multipart_part_size_custom`
**Objective:** Verify custom part size works correctly

**Test Steps:**
1. Create 10MB test file
2. Call `minio_service.upload_multipart()` with `part_size=2MB`
3. Verify 5 parts created (10MB / 2MB = 5 parts)
4. Verify file integrity

**Expected Result:** File uploaded in 5 parts, integrity verified

**Coverage:** `upload_multipart()` - custom part size

---

#### Test 3.3: `test_upload_multipart_failure_abort`
**Objective:** Verify multipart upload abort on failure

**Test Steps:**
1. Start multipart upload with invalid credentials (mock)
2. Verify upload fails
3. Verify `abort_multipart_upload()` called automatically
4. Verify no orphaned parts in MinIO

**Expected Result:** Upload aborted, no orphaned parts

**Coverage:** `upload_multipart()` - error handling + abort logic

---

### Test Suite 4: File Download (2 tests)

#### Test 4.1: `test_download_file_success`
**Objective:** Verify successful file download

**Test Steps:**
1. Upload test file using `upload_file()`
2. Call `minio_service.download_file()` with object key
3. Verify downloaded content matches original content
4. Verify content type preserved

**Expected Result:** File downloaded correctly, content matches

**Coverage:** `download_file()` - happy path

---

#### Test 4.2: `test_download_file_not_found`
**Objective:** Verify error handling for non-existent file

**Test Steps:**
1. Call `minio_service.download_file()` with non-existent key
2. Verify `ClientError` raised with 404 error code

**Expected Result:** `ClientError` raised (object not found)

**Coverage:** `download_file()` - error handling path

---

### Test Suite 5: SHA256 Integrity (2 tests)

#### Test 5.1: `test_verify_sha256_success`
**Objective:** Verify SHA256 hash verification for valid files

**Test Steps:**
1. Upload test file, get SHA256 hash
2. Download file content
3. Call `minio_service.verify_sha256()` with content and hash
4. Verify verification returns `True`

**Expected Result:** SHA256 verification passes

**Coverage:** `verify_sha256()` - happy path

---

#### Test 5.2: `test_verify_sha256_failure`
**Objective:** Verify SHA256 hash verification detects tampering

**Test Steps:**
1. Upload test file, get SHA256 hash
2. Download file content and modify it (tamper)
3. Call `minio_service.verify_sha256()` with tampered content and original hash
4. Verify verification returns `False`

**Expected Result:** SHA256 verification fails (tampering detected)

**Coverage:** `verify_sha256()` - failure path

---

### Test Suite 6: Presigned URLs (2 tests)

#### Test 6.1: `test_generate_presigned_upload_url`
**Objective:** Verify presigned upload URL generation

**Test Steps:**
1. Call `minio_service.generate_presigned_upload_url()` with object key
2. Verify URL is generated (non-empty)
3. Verify URL contains bucket name and object key
4. Verify URL expires within expected time (default: 1 hour)

**Expected Result:** Valid presigned upload URL generated

**Coverage:** `generate_presigned_upload_url()` - happy path

---

#### Test 6.2: `test_generate_presigned_download_url`
**Objective:** Verify presigned download URL generation

**Test Steps:**
1. Upload test file
2. Call `minio_service.generate_presigned_download_url()` with object key
3. Verify URL is generated (non-empty)
4. Verify URL can be used to download file via HTTP GET
5. Verify URL expires within expected time

**Expected Result:** Valid presigned download URL generated, file accessible

**Coverage:** `generate_presigned_download_url()` - happy path

---

## 📋 IMPLEMENTATION CHECKLIST

### Setup Requirements

- [ ] MinIO service running (Docker Compose)
- [ ] Test bucket configured (`MINIO_BUCKET` env var)
- [ ] MinIO credentials configured (`MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY`)
- [ ] Test fixtures for file objects (BytesIO)

### Test Implementation

- [ ] Create `tests/integration/test_minio_service_integration.py`
- [ ] Implement bucket management tests (2 tests)
- [ ] Implement file upload tests (3 tests)
- [ ] Implement multipart upload tests (3 tests)
- [ ] Implement file download tests (2 tests)
- [ ] Implement SHA256 integrity tests (2 tests)
- [ ] Implement presigned URL tests (2 tests)
- [ ] Add proper cleanup (delete test objects after tests)

### Test Execution

- [ ] Run test suite: `pytest tests/integration/test_minio_service_integration.py -v`
- [ ] Verify all 12 tests pass
- [ ] Check coverage report: MinIO service 60%+ coverage
- [ ] Verify total project coverage increased by +4-5%

---

## 📈 EXPECTED COVERAGE IMPROVEMENT

### MinIO Service Coverage

| Method | Current | After Tests | Improvement |
|--------|---------|-------------|-------------|
| `ensure_bucket_exists()` | 0% | 100% | +100% |
| `upload_file()` | 50% | 100% | +50% |
| `upload_multipart()` | 0% | 100% | +100% |
| `download_file()` | 30% | 100% | +70% |
| `compute_sha256()` | 100% | 100% | 0% |
| `verify_sha256()` | 0% | 100% | +100% |
| `generate_presigned_upload_url()` | 0% | 100% | +100% |
| `generate_presigned_download_url()` | 0% | 100% | +100% |
| **Overall** | **25%** | **60%+** | **+35%** |

### Total Project Coverage

| Component | Current | After | Improvement |
|-----------|---------|-------|-------------|
| **MinIO Service** | 25% | 60%+ | +35% |
| **Total Project** | ~66% | ~70-71% | **+4-5%** |

---

## ⏱️ ESTIMATED EFFORT

**Time Required:** 4-5 hours

**Breakdown:**
- Test file setup: 30 minutes
- Bucket management tests: 45 minutes
- File upload tests: 1 hour
- Multipart upload tests: 1 hour
- Download + integrity tests: 1 hour
- Presigned URL tests: 30 minutes
- Execution + debugging: 30 minutes

**Target:** Complete by end of Day 4 (Nov 25, 2025)

---

## ✅ SUCCESS CRITERIA

1. ✅ **12+ tests** passing for MinIO service
2. ✅ **MinIO coverage** increased from 25% → 60%+
3. ✅ **Total coverage** increased from ~66% → ~70-71%
4. ✅ **All test methods** cover both happy paths and error cases
5. ✅ **Zero flaky tests** (tests stable, repeatable)

---

## 🚀 NEXT STEPS

1. ✅ **Review Test Plan** - Validate test scenarios
2. ⏳ **Implement Tests** - Create `test_minio_service_integration.py`
3. ⏳ **Run Test Suite** - Execute and verify coverage
4. ⏳ **Document Results** - Update coverage metrics

---

**Status:** 📋 **PLAN READY** - Ready for implementation Day 4 afternoon  
**Priority:** 🔴 **HIGH** - Critical for Gate G3 coverage target (90%+)  
**Confidence:** 🟢 **HIGH** - Clear test scenarios, straightforward implementation

---

*MinIO Integration Test Plan - Week 7 Day 4* ✅  
*Target: 60%+ MinIO coverage, +4-5% total project coverage* 🚀

