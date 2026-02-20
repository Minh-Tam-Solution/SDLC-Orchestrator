---
sdlc_version: "6.1.0"
document_type: "Architecture Decision Record"
status: "APPROVED"
adr_number: "062"
spec_id: "ADR-062"
tier: "ENTERPRISE"
stage: "02 - Design"
created_date: "2026-02-19"
approved_date: "2026-02-20"
---

# ADR-062 — Compliance Evidence Types

**Status**: APPROVED (CTO sign-off Sprint 183)
**Date**: February 20, 2026
**Author**: @architect
**Reviewer**: CTO
**Sprint**: Sprint 183 — Enterprise SSO Implementation + Compliance Evidence
**Supersedes**: None

---

## Context

The Evidence Vault currently supports general evidence types stored as `VARCHAR(50)` in
`gate_evidence.evidence_type`, enforced at the application layer via Pydantic validator.
Existing types: `DESIGN_DOCUMENT`, `TEST_RESULTS`, `CODE_REVIEW`, `DEPLOYMENT_PROOF`,
`DOCUMENTATION`, `COMPLIANCE`, and 4 RFC-SDLC-602 types.

The generic `COMPLIANCE` type is a catch-all with no framework differentiation.
Enterprise customers in regulated industries require:
1. **SOC2 Type II readiness** — evidence tagged as `SOC2_CONTROL` for auditors
2. **HIPAA compliance** — PHI access audit evidence tagged as `HIPAA_AUDIT`
3. **NIST AI RMF** — AI governance evidence tagged as `NIST_AI_RMF`
4. **ISO 27001** — information security controls tagged as `ISO27001`

Without compliance-specific evidence types, ENTERPRISE customers cannot generate
compliance-specific evidence packs (Sprint 185 SOC2 Pack Generator requires these types).

---

## Problem Statement

The existing `COMPLIANCE` type is a single catch-all that:
1. Cannot be filtered by framework (SOC2 vs HIPAA vs NIST vs ISO27001)
2. Does not provide auditor-facing metadata about which control is evidenced
3. Blocks Sprint 185 SOC2 Pack Generator (which filters by `SOC2_CONTROL`)

---

## Decision — 4 Locked Decisions

### D-062-01: 4 New Compliance Evidence Types (UPPERCASE, VARCHAR)

Extend the Pydantic validator `allowed_types` set with 4 new uppercase string values.
Storage is `VARCHAR(50)` — no PostgreSQL enum DDL required (decided Sprint 182 research).

```python
# backend/app/schemas/evidence.py — allowed_types validator set
"SOC2_CONTROL"   # SOC2 Trust Service Criteria (Security/Availability/Confidentiality)
"HIPAA_AUDIT"    # PHI access audit records (HIPAA minimum necessary access)
"NIST_AI_RMF"    # NIST AI Risk Management Framework v1.1 controls
"ISO27001"       # ISO 27001:2022 Annex A controls mapping
```

**Backward compatible**: existing `COMPLIANCE` type retained as generic fallback.

---

### D-062-02: Open Question Resolutions

| # | Question | Decision | Rationale |
|---|----------|----------|-----------|
| 1 | SOC2 Trust Service Criteria: enum or free-text? | **Free-text in metadata JSONB** | Trust criteria change across SOC2 versions; flexibility > rigidity. Sprint 185 adds JSON Schema validation. |
| 2 | HIPAA retention 6 years: `expires_at` or metadata only? | **Metadata only (Sprint 183)** | `expires_at` enforcement is Sprint 185+ scope. Sprint 183 only extends the type enum. |
| 3 | NIST AI RMF: v1.0 or v1.1? | **v1.1** (January 2025) | v1.1 is the current release; enterprise customers expect current standard. |
| 4 | ISO 27001: 2013 or 2022? | **ISO 27001:2022** | 2022 edition is current; 2013 is deprecated. New enterprise customers expect 2022. |

---

### D-062-03: Storage Layer — VARCHAR(50), NOT PostgreSQL Enum

The `gate_evidence.evidence_type` column is `VARCHAR(50)`, not a PostgreSQL native enum.
Discovered during Sprint 183 implementation (confirmed by `s182_001` migration DDL).

**Consequences of VARCHAR decision**:
- Alembic migration `s183_002` is documentation-only (no DDL change)
- No `ALTER TYPE ... ADD VALUE` needed
- Enforcement is 100% at application layer (Pydantic validator)
- Downgrade is a no-op: existing rows with new type values are valid VARCHAR

**Migration strategy**: `s183_002_compliance_evidence_types.py` adds a SQL COMMENT ON COLUMN
to document allowed values and creates a checkpoint in Alembic history.

---

### D-062-04: Compliance Evidence Filter API

Add `compliance_type` query parameter to `GET /api/v1/evidence` to filter by compliance
framework. Implemented in Sprint 183 (evidence.py route update).

```
GET /api/v1/evidence?compliance_type=SOC2_CONTROL
GET /api/v1/evidence?compliance_type=HIPAA_AUDIT
GET /api/v1/evidence?compliance_type=NIST_AI_RMF
GET /api/v1/evidence?compliance_type=ISO27001
```

---

## Implementation (Sprint 183)

### Files Modified

| File | Change |
|------|--------|
| `backend/app/schemas/evidence.py` | Add 4 types to `allowed_types` set in `validate_evidence_type` |
| `backend/alembic/versions/s183_002_compliance_evidence_types.py` | Documentation migration (COMMENT ON COLUMN) |

### Pydantic Validator (evidence.py)

```python
allowed_types = {
    # Existing types (unchanged)
    "DESIGN_DOCUMENT", "TEST_RESULTS", "CODE_REVIEW",
    "DEPLOYMENT_PROOF", "DOCUMENTATION", "COMPLIANCE",
    "E2E_TESTING_REPORT", "API_DOCUMENTATION_REFERENCE",
    "SECURITY_TESTING_RESULTS", "STAGE_CROSS_REFERENCE",
    # Sprint 183 — ADR-062
    "SOC2_CONTROL",
    "HIPAA_AUDIT",
    "NIST_AI_RMF",
    "ISO27001",
}
```

### Compliance Evidence Metadata Schemas

**SOC2_CONTROL** — `evidence.metadata` JSONB:
```json
{
  "compliance_type": "SOC2_CONTROL",
  "trust_service_criteria": "CC6.1",
  "control_name": "Logical and Physical Access Controls",
  "collection_period": "2026-01-01/2026-03-31",
  "auditor_reference": "Ernst & Young LLP"
}
```

**HIPAA_AUDIT** — `evidence.metadata` JSONB:
```json
{
  "compliance_type": "HIPAA_AUDIT",
  "phi_category": "access_log",
  "minimum_necessary_check": true,
  "de_identified": false,
  "retention_note": "6-year retention required; enforce via data lifecycle policy"
}
```

**NIST_AI_RMF** — `evidence.metadata` JSONB (v1.1 functions):
```json
{
  "compliance_type": "NIST_AI_RMF",
  "function": "GOVERN",
  "category": "GOVERN 1.1",
  "subcategory": "AI risk management policies established",
  "framework_version": "1.1"
}
```

**ISO27001** — `evidence.metadata` JSONB (2022 edition):
```json
{
  "compliance_type": "ISO27001",
  "annex_a_control": "A.5.1",
  "control_name": "Policies for information security",
  "iso_edition": "2022",
  "implementation_status": "implemented"
}
```

---

## Alternatives Considered

| Option | Rejected Reason |
|--------|----------------|
| Separate `compliance_evidence` table | Over-engineering; metadata JSONB is sufficient for Sprint 183 |
| String tags instead of typed values | No validation; breaks filtering; type safety lost |
| Single `COMPLIANCE` + metadata filter | Cannot filter by `evidence_type` column index efficiently |
| PostgreSQL native enum | `evidence_type` is VARCHAR; changing to enum requires full column migration (disruptive) |

---

## Non-Goals

1. **SOC2 Pack Generator** — Sprint 185 deliverable
2. **HIPAA PHI retention enforcement** — regulatory scope; enforcement in Sprint 185+
3. **ISO 27001 certification assistance** — assessment/certification out of Orchestrator scope
4. **NIST AI RMF automated control testing** — Sprint 184+ (Jira integration needed)

---

## Consequences

**Positive**:
- Enables Sprint 185 SOC2 Pack Generator (requires `SOC2_CONTROL` typed evidence)
- Enterprise customers can tag evidence by compliance framework from Sprint 183
- Backward compatible — existing `COMPLIANCE` type still valid
- Zero downtime: VARCHAR change, no DDL locking

**Negative**:
- Application-layer validation only: direct DB inserts can bypass type enforcement
  (acceptable: trusted internal writes only; external access via API)

**Neutral**:
- `evidence.metadata` JSONB structure is flexible; JSON Schema validation deferred to Sprint 185

---

## Sprint 185 Follow-up Tasks

1. **SOC2 Evidence Pack Generator** — auto-collect `SOC2_CONTROL` evidence and map to
   SOC2 Trust Service Criteria matrix
2. **HIPAA Retention Enforcement** — add `retention_until` computed field for HIPAA evidence
3. **JSON Schema Validation** — validate `evidence.metadata` structure per compliance type
4. **ISO 27001 Controls Matrix** — map existing evidence to ISO 27001:2022 Annex A controls

---

## Sign-off

| Role | Decision | Date |
|------|----------|------|
| @architect | ✅ APPROVED | 2026-02-20 |
| CTO | ✅ APPROVED | 2026-02-20 |

[@cto: ADR-062 finalized Sprint 183. 4 locked decisions. VARCHAR storage (no DDL), NIST v1.1,
ISO 27001:2022, SOC2 free-text metadata, HIPAA retention deferred to Sprint 185.
Migration s183_002 is documentation-only checkpoint. Validator updated in evidence.py.]
