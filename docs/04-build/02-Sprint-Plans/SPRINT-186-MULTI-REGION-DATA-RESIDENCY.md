---
sdlc_version: "6.1.0"
document_type: "Sprint Plan"
status: "PROPOSED"
sprint: "186"
spec_id: "SPRINT-186"
tier: "ENTERPRISE"
stage: "04 - Build"
---

# SPRINT-186 — Multi-Region + Data Residency

**Status**: PROPOSED (pending CTO approval)
**Sprint Duration**: 10 working days
**Sprint Goal**: Storage-level EU data residency + GDPR compliance (NOT database multi-region)
**Epic**: ADR-059 Enterprise-First + ADR-063
**ADR**: ADR-063 (Multi-Region Deployment — storage-only scope)
**Dependencies**: Sprint 185 complete (audit trail + SOC2 evidence pack live)
**Budget**: ~$6,400 (80 hrs at $80/hr)

---

## 1. Sprint Goal

**CRITICAL SCOPE NOTE** (per ADR-059 Expert 5 correction):

Sprint 186 delivers **storage-level data residency only** (MinIO/S3 bucket per region). It does NOT ship multi-region PostgreSQL or database replication. Full DB multi-region is deferred until first signed EU enterprise contract.

| Deliverable | Priority | New LOC | Days |
|-------------|----------|---------|------|
| ADR-063: Multi-Region Deployment Strategy | P0 | ~200 doc | 1 |
| `s186_001_project_data_region.py` migration | P0 | ~40 | 0.5 |
| `storage_region_service.py` | P0 | ~200 | 2 |
| Data residency API routes (4 endpoints) | P0 | ~150 | 1.5 |
| Storage region tests (SR-01..20) | P0 | ~200 | 1 |
| GDPR service (`gdpr_service.py`) | P0 | ~200 | 2 |
| GDPR routes (4 endpoints) | P0 | ~150 | 1 |
| `s186_002_gdpr_tables.py` migration | P0 | ~60 | 0.5 |
| GDPR tests (GD-01..20) | P0 | ~200 | 1 |
| **`?compliance_type=` filter on GET /api/v1/evidence** | **P1 ⚠️** | ~60 | 0.5 |
| **Fernet key rotation runbook** | **P1 ⚠️** | ~80 doc | 0.5 |
| SP-14: SOC2 pack idempotency test | P2 | ~30 | 0.25 |
| **Total** | | **~1,570** | **10** |

> ⚠️ **CTO P1 mandates from Sprint 185 review** — must ship before Sprint 186 close:
> - `?compliance_type=` filter: ADR-062 D-3, outstanding since Sprint 183, 3 sprints overdue.
> - Fernet key rotation runbook: F-03 SHA-256 migration breaks existing tokens; required before any ENTERPRISE customer onboards.

---

## 2. Deliverables

| # | Deliverable | Description | Files | Sprint Day |
|---|------------|-------------|-------|------------|
| 1 | ADR-063 | Multi-Region strategy — storage-only, NOT DB multi-region | New | Day 1 |
| 2 | `s186_001_data_region.py` | Add `projects.data_region` column (ERD v3.5.0: VN, EU, US) | New | Day 1 |
| 3 | `storage_region_service.py` | MinIO region bucket selector + evidence migration | New | Day 2-3 |
| 4 | `data_residency.py` (route) | 4 endpoints: region list, set, get, migrate evidence | New | Day 3-4 |
| 5 | `test_storage_region.py` | SR-01 to SR-20 (20 storage region tests) | New | Day 4 |
| 6 | `gdpr_service.py` | Right to erasure (Art. 17) + DSAR export (Art. 20) | New | Day 5-6 |
| 7 | `gdpr.py` (route) | 4 GDPR endpoints: erasure request, status, DSAR export, consent | New | Day 6-7 |
| 8 | `s186_002_gdpr_tables.py` | `gdpr_erasure_requests` table + `user_consents` FK | New | Day 7 |
| 9 | `test_gdpr_service.py` | GD-01 to GD-20 (20 GDPR tests) | New | Day 8 |
| 10 | ADR-063 finalized | Document constraints: no DB multi-region until EU contract | Modified | Day 9 |
| 11 | Sprint close | SPRINT-186-CLOSE.md + regression | -- | Day 10 |

---

## 3. Daily Schedule

### Day 1: ADR-063 + Migration

**ADR-063: Multi-Region Deployment Strategy**

**5 Locked Decisions**:
1. **Scope**: Storage-level residency only (MinIO/S3 bucket per region). DB remains single-region (Vietnam/Singapore primary).
2. **Regions**: VN (Vietnam/Singapore — primary), EU (Frankfurt — GDPR), US (N. Virginia — future)
3. **Region assignment**: Per-project (`projects.data_region`), not per-organization
4. **Enforcement**: API layer reads `project.data_region` → routes evidence upload to correct MinIO instance
5. **DB multi-region deferred**: Full multi-region DB deferred until first signed EU enterprise contract

**Why NOT multi-region DB in Sprint 186**:
- PostgreSQL read replicas add infrastructure cost ($3,000+/month on AWS RDS)
- Write routing complexity (master-master conflicts)
- No signed EU customer yet — premature optimization
- Storage-level residency satisfies most GDPR requirements (data stored in EU, even if DB metadata is in VN)
- Expert 5 recommendation: "de-scope to storage-only residency"

**ADR-063 Consequences**:
- Evidence files stored in MinIO EU bucket for EU projects ✅
- Evidence SHA256 hashes + metadata still stored in VN database ⚠️
- GDPR Article 17 (erasure): delete from MinIO EU bucket + DB record ✅
- GDPR full data portability: export from VN DB + EU MinIO ✅
- Legal note: DB metadata in VN may require DPA (Data Processing Agreement) with EU customers

**Migration s186_001**:
```sql
ALTER TABLE projects
    ADD COLUMN data_region VARCHAR(10) DEFAULT 'VN'
    CHECK (data_region IN ('VN', 'EU', 'US'));
```

---

### Day 2-3: Storage Region Service

```python
# backend/app/services/storage_region_service.py

MINIO_ENDPOINTS = {
    "VN": os.environ.get("MINIO_ENDPOINT_VN", "http://minio-vn:9000"),
    "EU": os.environ.get("MINIO_ENDPOINT_EU", "http://minio-eu:9000"),
    "US": os.environ.get("MINIO_ENDPOINT_US", "http://minio-us:9000"),
}

MINIO_BUCKET_NAMES = {
    "VN": "evidence-vn",
    "EU": "evidence-eu",
    "US": "evidence-us",
}

class StorageRegionService:
    """
    Routes evidence storage to the correct MinIO instance based on
    project.data_region. Network-only: uses boto3 S3 API (no MinIO SDK).
    """

    def get_s3_client(self, region: str) -> boto3.client:
        """Return boto3 S3 client for the specified region's MinIO instance."""
        endpoint = MINIO_ENDPOINTS.get(region, MINIO_ENDPOINTS["VN"])
        return boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=settings.MINIO_ACCESS_KEY,
            aws_secret_access_key=settings.MINIO_SECRET_KEY,
        )

    async def upload_evidence(
        self, file_data: bytes, object_name: str, region: str
    ) -> str:
        """Upload evidence to region-specific MinIO bucket. Returns S3 key."""
        bucket = MINIO_BUCKET_NAMES.get(region, "evidence-vn")
        s3 = self.get_s3_client(region)
        s3.put_object(Bucket=bucket, Key=object_name, Body=file_data)
        return f"s3://{bucket}/{object_name}"

    async def migrate_evidence_region(
        self, evidence_ids: list[int], new_region: str, db: AsyncSession
    ) -> dict[str, int]:
        """
        Migrate evidence files from current region to new_region.
        Returns: {"migrated": N, "failed": M}
        """
        # 1. For each evidence ID: download from current region
        # 2. Upload to new region MinIO bucket
        # 3. Update gate_evidence.s3_bucket + s3_key in DB
        # 4. Delete from old region (after successful upload + DB update)

    async def delete_evidence_from_region(
        self, s3_key: str, region: str
    ) -> None:
        """Delete evidence file from MinIO region bucket (GDPR erasure)."""
        bucket = MINIO_BUCKET_NAMES.get(region, "evidence-vn")
        s3 = self.get_s3_client(region)
        s3.delete_object(Bucket=bucket, Key=s3_key)
```

**Storage Region Tests (SR-01 to SR-20)**:
```
SR-01: get_s3_client returns boto3 client for VN endpoint
SR-02: get_s3_client returns boto3 client for EU endpoint
SR-03: get_s3_client defaults to VN for unknown region
SR-04: upload_evidence uploads to VN bucket for VN region
SR-05: upload_evidence uploads to EU bucket for EU region
SR-06: upload_evidence returns valid s3:// URI
SR-07: migrate_evidence_region copies file from VN to EU bucket
SR-08: migrate_evidence_region updates DB record s3_bucket + s3_key
SR-09: migrate_evidence_region deletes from old bucket after successful copy
SR-10: migrate_evidence_region returns {"migrated": N, "failed": 0} on success
SR-11: migrate_evidence_region handles partial failure (some files fail)
SR-12: delete_evidence_from_region calls S3 delete_object
SR-13: GET /data-residency/regions returns list of available regions
SR-14: POST /data-residency/projects/{id}/region sets project data_region
SR-15: GET /data-residency/projects/{id}/region returns current region
SR-16: POST /data-residency/projects/{id}/migrate triggers evidence migration
SR-17: POST /data-residency migrate requires ENTERPRISE tier
SR-18: Evidence upload routes read project.data_region to select bucket
SR-19: StorageRegionService uses boto3 (NOT minio SDK — AGPL containment)
SR-20: MINIO_ENDPOINT_EU environment variable override works
```

---

### Day 5-6: GDPR Service

```python
# backend/app/services/gdpr_service.py

class GDPRService:
    """
    GDPR compliance service.
    Implements Article 17 (right to erasure) + Article 20 (data portability).
    All GDPR operations are available to ALL tiers (privacy law applies universally).
    """

    async def request_erasure(
        self, user_id: int, requester_id: int, reason: str, db: AsyncSession
    ) -> GdprErasureRequest:
        """
        Submit GDPR Article 17 erasure request.
        Erasure is processed asynchronously (30-day processing window).
        """
        request = GdprErasureRequest(
            user_id=user_id,
            requested_by=requester_id,
            reason=reason,
            status="pending",
            scheduled_purge_at=datetime.utcnow() + timedelta(days=30),
        )
        db.add(request)
        await db.commit()
        # Soft-delete user data (30-day grace period)
        await self._soft_delete_user_data(user_id, db)
        return request

    async def _soft_delete_user_data(self, user_id: int, db: AsyncSession) -> None:
        """Mark user data for deletion (30-day soft delete → 90-day hard purge)."""
        await db.execute(
            update(User).where(User.id == user_id).values(
                is_active=False,
                erasure_scheduled_at=datetime.utcnow() + timedelta(days=30),
            )
        )
        await db.commit()

    async def execute_erasure(self, erasure_request_id: int, db: AsyncSession) -> dict:
        """
        Execute hard erasure (called by background job at scheduled_purge_at).
        Deletes from MinIO + anonymizes DB records.
        Returns: {"evidence_deleted": N, "db_records_anonymized": M}
        """

    async def export_user_data(self, user_id: int, db: AsyncSession) -> bytes:
        """
        GDPR Article 20: Data Portability.
        Export all user data as JSON archive (ZIP with evidence files).
        """

    async def update_consent(
        self, user_id: int, consent_type: str, granted: bool, db: AsyncSession
    ) -> UserConsent:
        """Update user consent record (MARKETING/ANALYTICS/ESSENTIAL)."""
```

**GDPR Migration (s186_002)**:
```sql
CREATE TABLE gdpr_erasure_requests (
    id                  SERIAL PRIMARY KEY,
    user_id             INTEGER NOT NULL REFERENCES users(id),
    requested_by        INTEGER NOT NULL REFERENCES users(id),
    reason              TEXT,
    status              VARCHAR(20) DEFAULT 'pending'
                            CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    scheduled_purge_at  TIMESTAMP NOT NULL,    -- 30 days from request
    executed_at         TIMESTAMP,             -- Set when actually purged
    evidence_deleted    INTEGER DEFAULT 0,
    db_records_anonymized INTEGER DEFAULT 0,
    created_at          TIMESTAMP DEFAULT NOW()
);

-- user_consents already created in s186_001 (or may exist from ERD v3.5.0)
ALTER TABLE users
    ADD COLUMN IF NOT EXISTS erasure_scheduled_at TIMESTAMP;
```

**GDPR Tests (GD-01 to GD-20)**:
```
GD-01: request_erasure creates GdprErasureRequest with status="pending"
GD-02: request_erasure soft-deletes user (is_active=False)
GD-03: request_erasure sets scheduled_purge_at = 30 days from now
GD-04: _soft_delete_user_data sets erasure_scheduled_at on User
GD-05: execute_erasure deletes evidence files from MinIO
GD-06: execute_erasure anonymizes user PII in DB (email → sha256@deleted.local)
GD-07: execute_erasure sets erasure_request.status="completed"
GD-08: execute_erasure records evidence_deleted count
GD-09: export_user_data returns bytes (ZIP archive)
GD-10: export_user_data ZIP contains user_profile.json
GD-11: export_user_data ZIP contains evidence_list.json
GD-12: update_consent creates UserConsent record
GD-13: update_consent updates existing consent (UNIQUE constraint on user+type)
GD-14: POST /gdpr/erasure submits erasure request
GD-15: GET /gdpr/erasure/{id}/status returns current status
GD-16: POST /gdpr/export returns ZIP archive (streaming)
GD-17: POST /gdpr/consent updates user consent
GD-18: GDPR endpoints accessible by ALL tiers (not gated by tier)
GD-19: Hard erasure background job runs at scheduled_purge_at
GD-20: User export available until scheduled_purge_at (30-day grace period)
```

---

### Day 4 (P1): CTO Mandates — compliance_type Filter + Fernet Runbook

#### P1-01: `?compliance_type=` filter on GET /api/v1/evidence

**Status**: 4 sprints overdue (ADR-062 D-3, Sprint 183). **Cannot slip again** (CTO).

**File**: `backend/app/api/routes/evidence.py`

```python
# Add compliance_type as an optional Query parameter
@router.get("")
async def list_evidence(
    ...
    compliance_type: str | None = Query(
        None,
        description="Filter by compliance evidence type: SOC2_CONTROL | HIPAA_AUDIT | NIST_AI_RMF | ISO27001",
    ),
    ...
):
    # Add to WHERE clause when present:
    if compliance_type:
        conditions.append(GateEvidence.evidence_type == compliance_type.upper())
```

**Test**: CT-01..CT-05 (evidence filter tests):
```
CT-01: GET /evidence?compliance_type=SOC2_CONTROL returns only SOC2_CONTROL records
CT-02: GET /evidence?compliance_type=HIPAA_AUDIT returns only HIPAA_AUDIT records
CT-03: GET /evidence?compliance_type=INVALID returns 422 (Pydantic validation)
CT-04: GET /evidence?compliance_type=soc2_control (lowercase) normalizes and returns SOC2_CONTROL records
CT-05: GET /evidence (no filter) returns all evidence types (unaffected by this change)
```

---

#### P1-02: Fernet Key Rotation Runbook

**Status**: P1 blocker — no ENTERPRISE customer onboarding until runbook exists.

**File**: `docs/09-govern/02-Runbooks/FERNET-KEY-ROTATION.md`

**Runbook covers**:
1. **Detection**: `SELECT COUNT(*) FROM jira_connections WHERE encrypted_api_token IS NOT NULL` — confirm which tokens exist
2. **Pre-flight**: Backup `jira_connections.encrypted_api_token` column
3. **Re-encrypt**: Decrypt with OLD key (zero-padded) → re-encrypt with NEW key (SHA-256)
4. **Verify**: Spot-check 5 tokens decrypt correctly with new key
5. **Cut-over**: Deploy `F-03 SHA-256 jira_connection.py` (already shipped Sprint 185)
6. **Rollback**: Restore from backup if decryption errors > 1%

---

### Day 9-10: Integration + Sprint Close

**Tasks**:
1. Run full regression (all Sprint 181-185 tests)
2. Coverage check: services/storage_region, services/gdpr packages
3. Register new routes in main.py:
   ```python
   from app.api.routes.data_residency import router as data_residency_router
   from app.api.routes.gdpr import router as gdpr_router
   app.include_router(data_residency_router)
   app.include_router(gdpr_router)
   ```
4. Write SPRINT-186-CLOSE.md
5. Finalize ADR-063

---

## 4. Success Criteria

| Criterion | Target | Measurement |
|-----------|--------|-------------|
| Storage region tests pass | 20/20 | SR-01 to SR-20 |
| GDPR tests pass | 20/20 | GD-01 to GD-20 |
| ADR-063 locked | 5/5 decisions | No TBDs |
| Evidence uploads to EU bucket for EU projects | Pass | SR-04, SR-05 |
| GDPR erasure soft-delete works | Pass | GD-02, GD-04 |
| GDPR data export works | Pass | GD-09, GD-10, GD-11 |
| StorageRegionService uses boto3 only (no MinIO SDK) | Pass | SR-19 |
| Zero P0 bugs | 0 | CI clean |

---

## 5. Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| EU MinIO instance not available in dev | Medium | Medium | Use VN MinIO with EU bucket prefix for development |
| GDPR legal accuracy | Medium | HIGH | Legal review required before EU customer delivery |
| Evidence migration downtime during region change | Low | Medium | Blue-green migration: write to both regions during migration period |
| DB metadata in VN for EU projects | HIGH | Medium | Document in DPA template; storage-level residency is legally common |

---

## 6. Dependencies

| Dependency | Type | Status |
|-----------|------|--------|
| Sprint 185 complete | Prerequisite | Required |
| MinIO EU instance | Infrastructure | Required for production; dev uses VN instance |
| boto3 (Apache 2.0) | Package | Already in requirements.txt |
| Legal review: GDPR erasure process | External | Required before EU customer |
| Legal review: DPA template for DB-in-VN | External | Required for EU contracts |

---

## 7. Definition of Done

- [ ] ADR-063 written with storage-only scope explicitly documented
- [ ] `s186_001` migration: projects.data_region column
- [ ] `s186_002` migration: gdpr_erasure_requests table + users.erasure_scheduled_at
- [ ] `storage_region_service.py` using boto3 (AGPL-safe)
- [ ] `gdpr_service.py` implementing Art. 17 + Art. 20
- [ ] 4 data residency endpoints registered
- [ ] 4 GDPR endpoints registered (ALL tiers)
- [ ] 20 storage region tests (SR-01..20) passing
- [ ] 20 GDPR tests (GD-01..20) passing
- [ ] All Sprint 181-185 tests still passing (regression)
- [ ] Legal note in ADR-063: DB metadata in VN covered by DPA
- [ ] **P1: `?compliance_type=` filter on GET /api/v1/evidence (CT-01..05 passing)** — cannot slip
- [ ] **P1: Fernet key rotation runbook (`docs/09-govern/02-Runbooks/FERNET-KEY-ROTATION.md`)** — ENTERPRISE onboarding blocked without this
- [ ] SP-14: SOC2 pack idempotency test (same period → same control coverage)
- [ ] F-04 tech debt: partition-based audit log TTL note in ADR-063 appendix
- [ ] Zero P0 bugs
- [ ] SPRINT-186-CLOSE.md written

---

**CTO P1 Gate**: Sprint 186 cannot close without `?compliance_type=` filter AND Fernet runbook. Both are blocking ENTERPRISE onboarding.

**Approval Required**: CTO + Legal sign-off on GDPR process
**Budget**: ~$6,400 (10 days × 8 hrs × $80/hr)
**Risk Level**: VERY HIGH (GDPR legal accuracy; EU data residency infrastructure)
