---
sdlc_version: "6.1.0"
document_type: "Architecture Decision Record"
status: "APPROVED"
sprint: "186"
spec_id: "ADR-063"
tier: "ENTERPRISE"
stage: "02 - Design"
---

# ADR-063: Multi-Region Deployment Strategy

**Status**: APPROVED
**Date**: February 2026
**Authors**: CTO + Backend Architect
**Sprint**: 186 (storage-level residency) → 187 (G4 validation)
**Supersedes**: None
**Referenced by**: Sprint 186, Sprint 187, FR-045 (Art.20 data export)

---

## 1. Context

Sprint 186 (ADR-059 Expert 5 de-scope, Feb 2026) shipped **storage-level data residency**:
- ENTERPRISE customers can select a MinIO/S3 bucket per project (VN / EU / US)
- The primary PostgreSQL database remains **single-region** (Vietnam / Singapore)
- EU data residency is enforced at the object storage layer only

This ADR documents the full multi-region architecture decision, including the deliberate de-scoping of DB multi-region, the data flow, GDPR compliance posture, and the conditions under which full multi-region DB replication would be added.

### Problem Statement

Enterprise customers in the EU require GDPR-compliant data residency. Options:
1. **Storage-only residency** — evidence files in EU MinIO bucket; metadata in VN DB
2. **Full multi-region** — separate PostgreSQL per region with replication
3. **EU-only deployment** — second full stack in EU

The original Sprint 186 plan included multi-region DB. Expert 5 review (ADR-059) de-scoped to Option 1 (storage-only) pending first EU enterprise contract.

---

## 2. Decision

### Decision D-1: Storage-Level Residency (APPROVED)

**Evidence files** (MinIO/S3) are stored in the region selected per project (`project.data_region`):

| Region | MinIO Bucket | GDPR Compliant | Status |
|--------|-------------|----------------|--------|
| VN | `sdlc-evidence-vn` | No | ✅ Live |
| EU | `sdlc-evidence-eu` | Yes (Frankfurt) | ✅ Live |
| US | `sdlc-evidence-us` | No | ⏳ Future |

**Metadata** (PostgreSQL: project records, user data, gate state) remains in the **Vietnam/Singapore primary database**.

### Decision D-2: Single-Region DB Until First EU Contract (APPROVED)

Full multi-region PostgreSQL (read replicas, write routing) is **deferred** until:
- First signed EU enterprise contract requiring full data residency
- OR Sprint 188 G4 requirement (whichever comes first)

**Rationale**: Running multi-region PostgreSQL adds ~$3,000/month cost and 3 weeks of engineering for a feature with no confirmed buyer. Storage-level residency satisfies 90% of EU GDPR requirements at 10% of the cost.

### Decision D-3: CDN + Regional Routing (PROPOSED — Sprint 188)

API layer remains single-region (Vietnam). CDN (Cloudflare) provides:
- Edge caching for static assets + dashboard
- EU → VN latency: ~180ms (acceptable for compliance dashboard; not real-time gaming)

### Decision D-4: GDPR Compliance Posture (APPROVED)

Under storage-level residency, the GDPR compliance posture is:

| GDPR Requirement | Status | Mechanism |
|-----------------|--------|-----------|
| Art.5(1)(f) data stored in EU | ✅ Partial | Evidence files in `sdlc-evidence-eu` MinIO bucket |
| Art.25 data protection by design | ✅ | Org-scoped queries, DPO gate, consent logs |
| Art.7 consent records | ✅ | `gdpr_consent_logs` table |
| Art.15 DSAR access | ✅ | `/gdpr/dsar` + `/gdpr/me/data-export` endpoints |
| Art.17 right to erasure | ⏳ Sprint 187 | Soft delete + 30-day purge pipeline |
| Art.20 data portability | ✅ Sprint 187 | `/gdpr/me/data-export/full` full PII JSON export |
| Art.32 security of processing | ✅ | Fernet at-rest encryption (Sprint 185), TLS in transit |

**Limitation acknowledged**: PostgreSQL metadata (user email, project names, gate records) is stored in Vietnam. This is disclosed in the Data Processing Agreement (DPA) template as: "Metadata is processed in Singapore (primary) with EU evidence files stored in Frankfurt."

---

## 3. Architecture Diagram

```
                        Cloudflare CDN (edge cache)
                               │
                ┌──────────────┴──────────────┐
                │                             │
         EU users                       VN/APAC users
                │                             │
                └──────────┬──────────────────┘
                           │
                    FastAPI / Backend
                    (Vietnam/Singapore)
                           │
              ┌────────────┴────────────┐
              │                         │
       PostgreSQL                  Redis 7.2
       (primary: VN)               (sessions)
              │
              │ StorageRegionService
              │ selects bucket per project
              │
     ┌────────┴────────┐
     │                 │
  MinIO VN          MinIO EU
  sdlc-evidence-vn  sdlc-evidence-eu
  (Asia Pacific)    (Frankfurt, GDPR)
```

---

## 4. Alternatives Considered

### Alt-A: Full Multi-Region PostgreSQL (Rejected for Sprint 186-187)

- **Pro**: Full GDPR compliance; EU metadata also in EU
- **Con**: +$3,000/month; 3 weeks engineering; requires Patroni/Citus; not justified without EU customer
- **Decision**: Deferred to Sprint 188+ post first EU contract signing

### Alt-B: EU-Only Second Deployment (Rejected)

- **Pro**: Complete isolation; simplest GDPR story
- **Con**: 2x operational cost; split codebase maintenance; Vietnam pilot customers cannot use EU instance
- **Decision**: Not viable at current scale

### Alt-C: Data Classification + Selective Encryption (Future Consideration)

- **Pro**: Single DB with field-level EU data tagged; cheaper than multi-region
- **Con**: Complex query routing; Sprint 188 scope only if EU contract materialises
- **Decision**: Document as future option; not in scope

---

## 5. Consequences

### Positive

- EU evidence files stored in Frankfurt (GDPR Art.5 partial compliance for file storage)
- Minimal operational overhead (single DB, known patterns)
- StorageRegionService is bucket-agnostic — adding US region requires only a new MinIO deployment and config entry
- ENTERPRISE customers can select EU region per project for compliance reporting

### Negative / Risks

| Risk | Likelihood | Mitigation |
|------|-----------|-----------|
| EU regulator challenges metadata in VN | Low | DPA template discloses VN metadata; standard cloud practice |
| First EU customer demands full residency | Medium | Sprint 188 full multi-region plan is ready to execute |
| EU ↔ VN latency for metadata queries | Low | p95 <100ms confirmed; EU↔SG is ~180ms round-trip |
| MinIO EU bucket availability event | Low | Cloudflare Backblaze fallback (Sprint 188 enhancement) |

### Non-Goals

- Multi-region API deployment (Sprint 188)
- Full PostgreSQL read replica in EU (post-first-EU-contract)
- GDPR Art.17 automated purge pipeline (Sprint 187 P2)

---

## 6. Migration Path to Full Multi-Region (When Triggered)

Trigger: First EU enterprise contract signed OR 10+ EU projects created.

Steps:
1. Deploy PostgreSQL read replica in Frankfurt (AWS RDS Multi-AZ)
2. Route EU read queries via `PGSSLMODE=require PG_EU_READ_URL`
3. Migrate EU-region project metadata via `pg_dump --table projects WHERE data_region = 'EU'`
4. Enable write routing for EU users via PgBouncer regional endpoint
5. Update `StorageRegionService` to include DB endpoint per region
6. Compliance: EU DPA addendum updated to reflect full EU residency

Timeline: ~3 weeks engineering, estimated Sprint 188 (10 days) + Sprint 189 (5 days validation).

---

## 7. Follow-up ADRs

| ADR | Title | Status |
|-----|-------|--------|
| ADR-059 | Enterprise-First Refocus (de-scoped multi-region DB) | ✅ Approved |
| ADR-064 | Full Multi-Region PostgreSQL | ⏳ Draft when EU contract signed |
| ADR-065 | GDPR Art.17 Automated Purge Pipeline | ⏳ Sprint 187 P2 |

---

## 8. Decision Log

| Date | Decision | Decider |
|------|----------|---------|
| 2026-02-19 | Storage-level residency only (Expert 5 de-scope, ADR-059) | CTO |
| 2026-02-20 | ADR-063 written as Sprint 186 P1 BLOCK G4 condition | CTO |
| 2026-02-20 | D-4 GDPR compliance posture with Art.17/20 status | Backend Architect |
