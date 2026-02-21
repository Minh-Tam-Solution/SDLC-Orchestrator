---
sdlc_version: "6.1.0"
document_type: "Sprint Plan"
status: "PROPOSED"
sprint: "185"
spec_id: "SPRINT-185"
tier: "ENTERPRISE"
stage: "04 - Build"
---

# SPRINT-185 — Advanced Audit Trail + SOC2 Evidence Pack

**Status**: PROPOSED (pending CTO approval)
**Sprint Duration**: 8 working days
**Sprint Goal**: SOC2 Type II readiness — immutable audit log + evidence pack generator
**Epic**: ADR-059 Enterprise-First
**ADR**: ADR-059 (ENTERPRISE tier compliance)
**Dependencies**: Sprint 184 complete (tier gates enforced, Jira integration live)
**Budget**: ~$5,120 (64 hrs at $80/hr)

---

## 1. Sprint Goal

Three tracks:
1. **Immutable Audit Trail** — Append-only PostgreSQL audit log for SOC2 Type II
2. **SOC2 Evidence Pack Generator** — Auto-generate PDF evidence pack from Evidence Vault
3. **HIPAA Compliance Pack** — HIPAA-specific PHI access audit trail

| Deliverable | Priority | New LOC | Days |
|-------------|----------|---------|------|
| `audit_trail.py` routes + model | P0 | ~250 | 2 |
| PostgreSQL append-only trigger | P0 | ~30 SQL | 0.5 |
| `s185_001_audit_trail.py` migration | P0 | ~80 | 0.5 |
| Audit trail tests (AT-01..20) | P0 | ~250 | 1 |
| `soc2_pack_service.py` | P0 | ~300 | 2 |
| SOC2 PDF generation (weasyprint Apache 2.0) | P0 | ~100 | 0.5 |
| SOC2 pack tests (SP-01..15) | P0 | ~200 | 1 |
| HIPAA compliance pack (audit log filter) | P1 | ~100 | 0.5 |
| Integration + regression | -- | ~50 | 1.5 |
| **Total** | | **~1,360** | **8** |

---

## 2. Deliverables

| # | Deliverable | Description | Files | Sprint Day |
|---|------------|-------------|-------|------------|
| 1 | `s185_001_audit_trail.py` | Alembic: audit_logs table append-only PostgreSQL trigger | New | Day 1 |
| 2 | `audit_trail.py` (route) | GET /enterprise/audit + POST /enterprise/audit/export | New | Day 1-2 |
| 3 | `audit_log.py` (model) | AppendOnly model (no UPDATE/DELETE trigger enforced) | New | Day 2 |
| 4 | `test_audit_trail.py` | AT-01 to AT-20 (20 tests: immutability, export, filter) | New | Day 3 |
| 5 | `soc2_pack_service.py` | Map Evidence Vault → SOC2 Trust Service Criteria | New | Day 4-5 |
| 6 | `s185_002_soc2_metadata.py` | evidence.soc2_criteria column (which TSC control this covers) | New | Day 4 |
| 7 | SOC2 PDF generator | weasyprint (Apache 2.0) → PDF evidence pack | In soc2_pack_service | Day 5 |
| 8 | `test_soc2_pack.py` | SP-01 to SP-15 (15 SOC2 pack tests) | New | Day 6 |
| 9 | HIPAA audit trail filter | Filter audit_logs by hipaa_category + PHI access events | Modified | Day 7 |
| 10 | Sprint close + docs | SPRINT-185-CLOSE.md | New | Day 8 |

---

## 3. Daily Schedule

### Day 1: Alembic Migration + Audit Trail Model

**Goal**: Create append-only audit_logs table with PostgreSQL-enforced immutability

**Tasks**:
1. Create `backend/alembic/versions/s185_001_audit_trail.py`:

```sql
-- audit_logs table already exists (ERD v3.5.0: id UUID PK, user_id UUID, created_at, etc.)
-- Sprint 185: extend with compliance audit columns + append-only enforcement trigger
ALTER TABLE audit_logs
    ADD COLUMN IF NOT EXISTS event_type     VARCHAR(50),          -- 'gate_action', 'evidence_access', etc.
    ADD COLUMN IF NOT EXISTS actor_user_id  UUID REFERENCES users(id),     -- NULL for system events
    ADD COLUMN IF NOT EXISTS resource_type  VARCHAR(50),          -- 'gate', 'evidence', 'user', 'tier'
    ADD COLUMN IF NOT EXISTS resource_id    VARCHAR(100),         -- FK value as string (generic)
    ADD COLUMN IF NOT EXISTS action         VARCHAR(50),          -- 'create', 'read', 'update', 'delete'
    ADD COLUMN IF NOT EXISTS old_value      JSONB,                -- Before state (NULL for creates)
    ADD COLUMN IF NOT EXISTS new_value      JSONB,                -- After state (NULL for deletes)
    ADD COLUMN IF NOT EXISTS ip_address     INET,
    ADD COLUMN IF NOT EXISTS user_agent     TEXT,
    ADD COLUMN IF NOT EXISTS tier_at_time   VARCHAR(20);          -- Tier snapshot at audit event time

-- Append-only enforcement: block UPDATE and DELETE on audit_logs
CREATE OR REPLACE FUNCTION prevent_audit_modification()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'audit_logs is append-only: UPDATE and DELETE are not permitted';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER audit_logs_immutable
    BEFORE UPDATE OR DELETE ON audit_logs
    FOR EACH ROW EXECUTE FUNCTION prevent_audit_modification();

-- Indexes for compliance queries
CREATE INDEX idx_audit_actor       ON audit_logs(actor_user_id, created_at DESC);
CREATE INDEX idx_audit_resource    ON audit_logs(resource_type, resource_id, created_at DESC);
CREATE INDEX idx_audit_event_type  ON audit_logs(event_type, created_at DESC);
CREATE INDEX idx_audit_created     ON audit_logs(created_at DESC);

-- 90-day retention: partition by month (or use background cleanup job)
-- Background job: DELETE FROM audit_logs WHERE created_at < NOW() - INTERVAL '90 days'
-- EXCEPTION: audit_logs trigger prevents DELETE → use PostgreSQL partition pruning
```

2. Create `backend/app/models/audit_log.py`:
   - SQLAlchemy model for audit_logs
   - `create_audit_log()` utility function (used by all services)
   - NO `update()` or `delete()` methods — enforcement via PostgreSQL trigger

**Event types to log**:
- Gate actions: create/evaluate/submit/approve/reject
- Evidence access: upload/download/verify
- User admin: create/deactivate/role_change
- Tier changes: upgrade/downgrade
- SSO events: login/logout/provision
- System events: migration_applied/service_restart

---

### Day 1-2: Audit Trail Routes

**API Endpoints** (Section 14 of API Spec v3.7.0):

```python
# backend/app/api/routes/audit_trail.py
router = APIRouter(prefix="/api/v1/enterprise/audit", tags=["Audit Trail"])

@router.get("")
async def list_audit_logs(
    event_type: str | None = None,
    actor_user_id: UUID | None = None,
    resource_type: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    page: int = 1,
    page_size: int = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List audit logs. ENTERPRISE tier required.
    Returns paginated audit events (max 100 per page).
    90-day retention window enforced.
    """

@router.post("/export")
async def export_audit_logs(
    export_request: AuditExportRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Export audit logs as CSV or JSON for compliance review.
    ENTERPRISE tier required.
    Returns streaming download response.
    Export window: max 90 days.
    """
```

---

### Day 3: Audit Trail Tests (AT-01 to AT-20)

```
AT-01: audit_log.create_audit_log() inserts new row
AT-02: PostgreSQL trigger blocks UPDATE on audit_logs (raises exception)
AT-03: PostgreSQL trigger blocks DELETE on audit_logs (raises exception)
AT-04: GET /enterprise/audit returns paginated audit logs
AT-05: GET /enterprise/audit filters by event_type
AT-06: GET /enterprise/audit filters by actor_user_id
AT-07: GET /enterprise/audit filters by resource_type + resource_id
AT-08: GET /enterprise/audit filters by date range
AT-09: GET /enterprise/audit page_size=100 max enforced
AT-10: GET /enterprise/audit returns 402 for non-ENTERPRISE user (TierGateMiddleware)
AT-11: POST /enterprise/audit/export produces valid CSV
AT-12: POST /enterprise/audit/export max 90-day window enforced
AT-13: Audit log records SSO login events (event_type="sso_login")
AT-14: Audit log records gate approval events (event_type="gate_approved")
AT-15: Audit log records evidence download events (event_type="evidence_download")
AT-16: Audit log records tier change events (event_type="tier_upgrade")
AT-17: Audit log records actor IP address
AT-18: Audit log records tier_at_time snapshot
AT-19: Audit log export streaming response (no timeout for large exports)
AT-20: audit_logs 90-day cleanup job runs without deleting (trigger-protected)
```

**Note on AT-20**: The 90-day retention cleanup uses PostgreSQL table partitioning (partition pruning drops old partitions), NOT DELETE statements, which are blocked by the trigger.

---

### Day 4-5: SOC2 Evidence Pack Service

**Goal**: Auto-collect Evidence Vault records → map to SOC2 criteria → generate PDF

```python
# backend/app/services/compliance/soc2_pack_service.py

from weasyprint import HTML  # Apache 2.0 license

SOC2_CRITERIA_MAP = {
    # Common Criteria → Evidence types that satisfy
    "CC1.1": [EvidenceType.DESIGN_DOCUMENT, EvidenceType.SOC2_CONTROL],
    "CC6.1": [EvidenceType.CODE_REVIEW, EvidenceType.SOC2_CONTROL],
    "CC6.6": [EvidenceType.DEPLOYMENT_PROOF, EvidenceType.SOC2_CONTROL],
    "CC7.2": [EvidenceType.TEST_RESULTS, EvidenceType.SOC2_CONTROL],
    "CC8.1": [EvidenceType.CODE_REVIEW, EvidenceType.DEPLOYMENT_PROOF],
    "A1.1":  [EvidenceType.DEPLOYMENT_PROOF, EvidenceType.SOC2_CONTROL],
    "C1.1":  [EvidenceType.COMPLIANCE, EvidenceType.SOC2_CONTROL],
}

class SOC2PackService:
    async def generate_evidence_pack(
        self, project_id: int, period_start: date, period_end: date, db: AsyncSession
    ) -> bytes:
        """
        Generate SOC2 Type II evidence pack as PDF.

        Args:
            project_id: Project to generate evidence for
            period_start: Audit period start date
            period_end: Audit period end date (max 12 months)
            db: Database session

        Returns:
            PDF bytes (weasyprint HTML → PDF)
        """
        evidence = await self._collect_evidence(project_id, period_start, period_end, db)
        criteria_coverage = self._map_to_criteria(evidence)
        html = self._render_html(criteria_coverage, project_id, period_start, period_end)
        return HTML(string=html).write_pdf()

    async def _collect_evidence(self, ...) -> list[GateEvidence]:
        # Query Evidence Vault for all SOC2_CONTROL + CODE_REVIEW + TEST_RESULTS
        # in the specified date range

    def _map_to_criteria(self, evidence: list) -> dict[str, list]:
        # Map each evidence record to one or more SOC2 criteria
        # Returns: {"CC6.1": [evidence1, evidence2], "CC8.1": [evidence3]}

    def _render_html(self, ...) -> str:
        # Render Jinja2 template with evidence mapped to criteria
        # Template: docs/templates/soc2_evidence_pack.html
```

**SOC2 Pack Tests (SP-01 to SP-15)**:
```
SP-01: generate_evidence_pack returns bytes (non-empty PDF)
SP-02: PDF contains project name in title
SP-03: PDF contains audit period dates
SP-04: _map_to_criteria maps SOC2_CONTROL evidence to correct criteria
SP-05: _map_to_criteria maps CODE_REVIEW evidence to CC8.1
SP-06: _map_to_criteria maps TEST_RESULTS to CC7.2
SP-07: _map_to_criteria maps DEPLOYMENT_PROOF to A1.1
SP-08: _collect_evidence queries only specified date range
SP-09: _collect_evidence includes SOC2_CONTROL, TEST_RESULTS, CODE_REVIEW types
SP-10: generate_evidence_pack raises ValueError for period > 12 months
SP-11: POST /enterprise/compliance/soc2/generate triggers generation
SP-12: GET /enterprise/compliance/soc2/{task_id}/status returns generation status
SP-13: GET /enterprise/compliance/soc2/{task_id}/download returns PDF bytes
SP-14: SOC2 pack generation is idempotent (same period returns same criteria mapping)
SP-15: weasyprint Apache 2.0 license (not AGPL) — confirmed safe
```

---

### Day 7: HIPAA Compliance Pack

**Goal**: Filter audit_logs for HIPAA-specific events

**Tasks**:
1. Add `hipaa_category` field to audit event creation:
   ```python
   # HIPAA-specific event categories
   HIPAA_EVENTS = {
       "evidence_access":    "§164.312(b) Audit Controls",
       "user_provisioned":   "§164.308(a)(3) Workforce",
       "tier_upgrade":       "§164.308(a)(1) Risk Management",
       "sso_login":          "§164.308(a)(5) Security Awareness",
   }
   ```

2. HIPAA report endpoint:
   - `GET /enterprise/compliance/hipaa/report?period_start=...&period_end=...`
   - Filters audit_logs by hipaa-relevant event types
   - Returns JSON + optional CSV export

---

## 4. Success Criteria

| Criterion | Target | Measurement |
|-----------|--------|-------------|
| Audit trail tests pass | 20/20 | AT-01 to AT-20 |
| SOC2 pack tests pass | 15/15 | SP-01 to SP-15 |
| Audit log immutability enforced | Pass | AT-02, AT-03 pass |
| SOC2 PDF generates without error | Pass | SP-01 pass |
| Gate actions logged to audit trail | Pass | AT-14 pass |
| SSO events logged | Pass | AT-13 pass |
| weasyprint license confirmed Apache 2.0 | Pass | SP-15 pass |
| Zero P0 bugs | 0 | CI clean |

---

## 5. Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| weasyprint CSS rendering issues | Medium | Low | Use simple table-based HTML template; avoid complex CSS |
| PostgreSQL trigger blocks 90-day cleanup | HIGH | Medium | Use table partitioning for retention (not DELETE) |
| SOC2 criteria mapping accuracy | Medium | HIGH | Legal review of criteria mapping required before customer delivery |
| PDF generation OOM for large evidence packs | Low | Medium | Cap at 500 evidence items per pack; paginate if needed |

---

## 6. Dependencies

| Dependency | Type | Status |
|-----------|------|--------|
| Sprint 184 complete | Prerequisite | Required |
| Tier gate middleware live | Code | Sprint 184 |
| Compliance evidence types (ADR-062) | Code | Sprint 183 |
| weasyprint (Apache 2.0) | Package | `pip install weasyprint` |
| Jinja2 | Package | Already in requirements.txt |
| Legal review: SOC2 criteria mapping | External | Required before customer delivery |

---

## 7. Definition of Done

- [ ] `s185_001_audit_trail.py` migration with PostgreSQL append-only trigger
- [ ] `audit_trail.py` routes (GET list + POST export) registered in main.py
- [ ] 20 audit trail tests (AT-01..20) passing
- [ ] `soc2_pack_service.py` with HTML→PDF generation (weasyprint)
- [ ] 15 SOC2 pack tests (SP-01..15) passing
- [ ] HIPAA audit filter endpoint
- [ ] All Sprint 183-184 tests still passing (regression)
- [ ] Zero P0 bugs
- [ ] Legal note: SOC2 mapping is implementation guide, not legal opinion
- [ ] SPRINT-185-CLOSE.md written

---

**Approval Required**: CTO + Legal sign-off on SOC2 criteria mapping
**Budget**: ~$5,120 (8 days × 8 hrs × $80/hr)
**Risk Level**: HIGH (SOC2 legal accuracy; PostgreSQL trigger retention strategy)
