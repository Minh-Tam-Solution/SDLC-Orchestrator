---
sdlc_version: "6.1.0"
document_type: "Sprint Plan"
status: "CLOSED"
sprint: "180"
spec_id: "SPRINT-180-ENTERPRISE-FIRST-REFOCUS"
tier: "PROFESSIONAL"
stage: "04 - Build"
gate: "G-Sprint"
start_date: "2026-02-19"
end_date: "2026-02-24"
---

# SPRINT-180 — Enterprise-First Refocus

**Status**: ✅ **CLOSED** (G-Sprint-Close APPROVED)
**Sprint Duration**: 4 working days (Feb 19–24, 2026)
**Sprint Goal**: Strategic architecture review — ADR-059 Enterprise-First Refocus + Sprint 179 formal close
**Epic**: EP-07 Multi-Agent Team Engine (strategic pivot)
**ADR**: ADR-059 (Enterprise-First Refocus Strategy — 5 locked decisions)
**Framework**: SDLC 6.1.0
**Budget**: $2,560 (32 hrs at $80/hr)
**Previous Sprint**: Sprint 179 — ZeroClaw Security Hardening
**Next Sprint**: Sprint 181 — OTT Foundation + Route Activation

---

## 1. Sprint Goal

> **Docs-only sprint.** No feature code. No migrations. Produce the strategic architecture foundation that Sprint 181+ will build on.

**Trigger**: CTO direction Feb 19, 2026 — "TinySDLC is now OSS for community. SDLC Orchestrator should refocus on Enterprise — large, complex projects."

**Sprint 180 delivers**:
1. Sprint 179 formal close document (G-Sprint-Close gate)
2. ADR-059 — Enterprise-First Refocus Strategy (5 locked decisions, 6 invariants)
3. 78-route tier mapping (15 CORE + 24 STANDARD + 31 PROFESSIONAL + 8 ENTERPRISE)
4. Orphaned route security rubric (7 files, Sprint 181 disposition)
5. Tier-billing migration plan for Sprint 181

---

## 2. Context: CTO Strategic Direction

On Feb 19, 2026, the CTO issued a strategic pivot:

```
Before: SDLC Orchestrator = only product (serves Individual → Enterprise)
        TinySDLC           = internal tool / prototype

After:  TinySDLC           = OSS community product (local-first, MIT/Apache-2.0)
        SDLC Orchestrator  = Commercial enterprise product (cloud-first, Team+ → Enterprise)
```

**Joint @pm + @architect review** produced initial proposal. **CTO review** approved with 6 corrections:

| # | Correction | Impact |
|---|-----------|--------|
| C-180-01 | Class is `ProjectTier` (not `TierLevel`), plain `str` not `enum.Enum` | Appendix C migration |
| C-180-02 | 8+ tier enums with inconsistent values across codebase | Sprint 181 migration scope |
| C-180-03 | `SubscriptionPlan` has no PROFESSIONAL (only FREE/FOUNDER/STANDARD/ENTERPRISE) | 4→6 value migration needed |
| C-180-04 | LITE tier stays — it is the free cloud gateway, not same as TinySDLC | INV-02 in ADR-059 |
| C-180-05 | OTT = ADD enterprise channels, don't drop consumer channels | Section 3 channel priority |
| C-180-06 | "Enterprise-First" not "Enterprise-Only" — investment priority shifts, not exclusion | D2 in ADR-059 |

---

## 3. Deliverables

### ✅ Deliverable 1 — F-179-01 Fix (P0, pre-Sprint)

**Sprint 179 post-sprint DoD gap**: `backend/app/services/agent_team/__init__.py` was missing 6 Sprint 179 exports.

**Fix applied** (before Sprint 180 formally started):

```python
# Lines 59–63 — Sprint 179 imports added
from app.services.agent_team.output_scrubber import OutputScrubber
from app.services.agent_team.history_compactor import HistoryCompactor
from app.services.agent_team.query_classifier import classify, ClassificationRule
from app.services.agent_team.config import DEFAULT_CLASSIFICATION_RULES, MODEL_ROUTE_HINTS

# Lines 111–116 — __all__ entries added
"OutputScrubber", "HistoryCompactor",
"classify", "ClassificationRule",
"DEFAULT_CLASSIFICATION_RULES", "MODEL_ROUTE_HINTS",
```

**Verification** (all pass):
```bash
cd /home/nqh/shared/SDLC-Orchestrator/backend
python3 -c "
from app.services.agent_team import (
    OutputScrubber, HistoryCompactor, classify, ClassificationRule,
    DEFAULT_CLASSIFICATION_RULES, MODEL_ROUTE_HINTS
)
print('AC-0.1: OutputScrubber — PASS')
print('AC-0.2: HistoryCompactor — PASS')
print('AC-0.3: classify — PASS')
print('AC-0.4: ClassificationRule — PASS')
print('AC-0.5: DEFAULT_CLASSIFICATION_RULES — PASS')
print('AC-0.6: MODEL_ROUTE_HINTS — PASS')
"
```

**Status**: ✅ AC-0.1 to AC-0.6 ALL PASS

---

### ✅ Deliverable 2 — Sprint 179 Formal Close (P0, Day 1)

**File**: `docs/04-build/02-Sprint-Plans/SPRINT-179-CLOSE.md`

| Section | Content | Status |
|---------|---------|--------|
| Executive Summary | 15/15 deliverables, 121/121 tests, $3,840 budget | ✅ |
| Deliverables Verification | 4 patterns (A+C+B+E), 15 deliverables table | ✅ |
| F-179-01 Post-Sprint Gap | Cause, fix, AC-0.1 to AC-0.6 verification | ✅ |
| Test Coverage Report | 34 new + 87 prior EP-07 = 121 total | ✅ |
| G-Sprint-Close Checklist | 8/8 criteria pass | ✅ |
| Documentation Updated | 5 documents updated/created | ✅ |
| Sprint Retrospective | F-179-01 lesson → DoD template fix | ✅ |
| Sprint Metrics | All metrics final | ✅ |

**G-Sprint-Close Decision**: ✅ APPROVED (8/8 criteria)

> **P1 correction applied during Sprint 180**: Test count in Section 4 and Section 8 corrected from 57 prior / 91 total → **87 prior / 121 total** (source: TP-056 baseline). File count corrected: new files 4→7, modified files 5→6.

---

### ✅ Deliverable 3 — ADR-059 Enterprise-First Refocus Strategy (P0, Days 1–3)

**File**: `docs/02-design/01-ADRs/ADR-059-Enterprise-First-Refocus.md`

**5 Locked Decisions**:

| # | Decision | Owner | Status |
|---|----------|-------|--------|
| D1 | Tier Model: LITE/STANDARD/PROFESSIONAL/ENTERPRISE; LITE = free cloud gateway | CPO | **LOCKED** |
| D2 | Enterprise-First investment priority: PROFESSIONAL+ gets new features; LITE/STANDARD maintenance-only | CTO + CPO | **LOCKED** |
| D3 | OTT Channel Abstraction: all channels via `protocol_adapter.py`; Teams+Slack=P0; Telegram+Zalo=P1 | Tech Lead | **LOCKED** |
| D4 | Orphaned Routes: 6 → ENTERPRISE (Sprint 181); 1 → CORE with rate-limit (Sprint 181) | Architect | **LOCKED** |
| D5 | Enterprise Feature Roadmap: SSO(182) → Compliance(183) → Integrations(184) → GA(188) | CEO | **LOCKED** |

**6 Invariants**:

| # | Invariant | Summary |
|---|-----------|---------|
| INV-01 | Two-layer model | `project.tier_level` ≠ `subscription.plan` — never conflate feature tier with billing SKU |
| INV-02 | TinySDLC ≠ Orchestrator LITE | Different products, different deployments, different target users |
| INV-03 | HTTP 402 for tier gates | Never return 403 for a tier-blocking event |
| INV-04 | OTT channel priority | Teams/Slack = enterprise P0; Telegram/Zalo = Vietnam pilot P1 |
| INV-05 | LITE hibernate/purge | 30-day hibernate, 90-day purge (GDPR-compliant) |
| INV-06 | Magic Link for G3/G4 | Direct OTT approval blocked for G3/G4; Magic Link JWT (5-min expiry) required |

**Content**:
- Context (1.1–1.4): trigger, current state, two-product ecosystem, CPO G0.1/G0.2 gate approval
- Decision Table: 5 locked decisions + non-goals
- Section 1: Tier vs Billing Separation (INV-01 through INV-03 + CTO corrections)
- Section 2: Orphaned Route Security Rubric (INV-04 partial)
- Section 3: OTT Channel Priority Table (INV-04)
- Section 4: LITE Resource Policy (INV-05)
- Section 5: Sprint 186 De-scope (storage-level only, no multi-region DB)
- Section 6: OTT Security for G3/G4 Gates (INV-06 Magic Link flow)
- Consequences (positive/negative/neutral + CTO answers)
- Follow-up ADRs (ADR-060 through ADR-063)
- Appendix A: 78-route tier mapping (actual files from `backend/app/api/routes/`)
- Appendix B: 7 orphaned route security rubric
- Appendix C: Tier-billing migration plan (Steps 1–6, Alembic with `subscription_plan_enum`)
- Appendix D: CPO pricing decision register (references only, per Expert 4 SSOT rule)
- Appendix E: Out-of-scope deferred items

> **P0 corrections applied during Sprint 180**:
> - Appendix A: Replaced 24+ phantom route file names with actual files from `backend/app/api/routes/` directory + confirmed main.py registrations
> - Appendix C Step 5: Fixed `ALTER TYPE subscriptionplan` → `ALTER TYPE subscription_plan_enum` (confirmed at `models/subscription.py:121` and `alembic/versions/s58_subscription_payment.py`)
> - Appendix C Step 5: Added missing `UPDATE subscriptions SET plan = 'std_starter' WHERE plan = 'standard'` data backfill

---

### ✅ Deliverable 4 — 78-Route Tier Mapping (P1, Day 2)

Complete audit of `backend/app/api/routes/` (76 .py files) cross-referenced with `backend/app/main.py` (71 `include_router()` calls).

| Tier | Registered | Orphaned | Total |
|------|-----------|---------|-------|
| CORE (LITE) | 14 | 1 (templates.py) | 15 |
| STANDARD | 24 | 0 | 24 |
| PROFESSIONAL | 31 | 0 | 31 |
| ENTERPRISE | 2 | 6 (NIST + compliance_framework + invitations) | 8 |
| **Total** | **71** | **7** | **78** |

**Key finding**: 42 endpoints / 3,463 LOC of production-ready ENTERPRISE features exist but are unreachable. No new code required — Sprint 181 activates via `include_router()` + tier gates.

---

### ✅ Deliverable 5 — CPO Business Model Review (P1, Day 3)

CPO (SE4H role) reviewed and approved G0.1/G0.2 gates. Business model decisions BM-01 through BM-10 locked:

| Decision | Summary |
|----------|---------|
| BM-01 | Two-stream revenue: SaaS + Professional Services + Marketplace (Q3 2026+) |
| BM-02 | PROFESSIONAL $499/mo (down from $599 for Vietnam fit) |
| BM-03 | Enterprise $80/seat, 25-seat minimum floor |
| BM-04 | FOUNDER → legacy SKU, no new signups after Sprint 181 launch |
| BM-05 | 14-day PROFESSIONAL trial on LITE signup (no credit card required) |
| BM-06 | Year 1 ARR target: $160K–$350K (vs original $86K–$240K) |
| BM-07 | LTV:CAC 6.6:1 (vs original 4.08:1) |
| BM-08 | Break-even Month 16 (vs Month 18) |
| BM-09 | Two-product ecosystem: TinySDLC OSS + Orchestrator commercial |
| BM-10 | Telegram on STANDARD (Vietnam pilot); Teams/Slack on PROFESSIONAL+ |

All pricing details deferred to CPO Pricing Decision Register (no duplication in ADR-059 per Expert 4 SSOT rule).

---

## 4. DoD Verification

### Acceptance Criteria

| AC | Description | Status |
|----|-------------|--------|
| AC-180-1 | `SPRINT-179-CLOSE.md` created with G-Sprint-Close 8/8 criteria passing | ✅ PASS |
| AC-180-2 | F-179-01 patched: AC-0.1 to AC-0.6 ALL PASS | ✅ PASS |
| AC-180-3 | ADR-059 created: 5 locked decisions, zero TBD | ✅ PASS |
| AC-180-4 | Appendix A: 78 routes mapped, zero phantom file names | ✅ PASS |
| AC-180-5 | Appendix C: `subscription_plan_enum` type name correct + STANDARD backfill present | ✅ PASS |
| AC-180-6 | SPRINT-179-CLOSE.md test counts correct: 87 prior, 121 total | ✅ PASS |
| AC-180-7 | No production code written this sprint (docs-only) | ✅ PASS |
| AC-180-8 | All @reviewer and @architect P0 findings resolved | ✅ PASS |

### Package Export Check (DoD template fix from F-179-01 lesson)

```bash
cd /home/nqh/shared/SDLC-Orchestrator/backend
python3 -c "
from app.services.agent_team import (
    OutputScrubber, HistoryCompactor, classify, ClassificationRule,
    DEFAULT_CLASSIFICATION_RULES, MODEL_ROUTE_HINTS
)
print('Sprint 179 symbols: ALL PASS')
"
```

---

## 5. @reviewer Sign-Off (SDLC 6.1.0 SE4A)

### Review Sign-Off: Sprint 180 Deliverables

**Verdict**: ✅ **APPROVED**

**Checks Completed**:
- Logic correctness: PASS — ADR-059 decisions are internally consistent; invariants do not conflict
- OWASP Top 10 (docs-only sprint): N/A — no production code
- Zero Mock scan: PASS — Appendix A uses actual file names; Appendix C uses real PostgreSQL type name
- Design compliance: PASS — ADR-059 follows ADR template (Context + Options + Decision + Consequences + Non-Goals)
- Dependencies: PASS — no new dependencies introduced

**Findings Resolved** (P0 issues from initial review):

| Finding | Original | Fix Applied |
|---------|----------|------------|
| ADR-059 Appendix A phantom routes | 24+ invented file names | Replaced with actual 78 route files from `backend/app/api/routes/` |
| ADR-059 Appendix C wrong enum type | `subscriptionplan` | Corrected to `subscription_plan_enum` (confirmed at `subscription.py:121`) |
| ADR-059 Appendix C missing STANDARD backfill | Not present | Added `UPDATE subscriptions SET plan = 'std_starter' WHERE plan = 'standard'` |
| SPRINT-179-CLOSE.md test count P1 | 57 prior / 91 total | Corrected to 87 prior / 121 total (TP-056 baseline) |

**G3 Reviewer Status**: READY — all P0 findings resolved; Sprint 181 may proceed.

---

## 6. @architect Sign-Off (SDLC 6.1.0 SE4A)

### G2 Gate: ADR-059 Design Package

**Verdict**: ✅ **APPROVED**

**Checks Completed**:
- ADRs documented in `docs/02-design/`: ✅ (ADR-059)
- Zero TBD decisions: ✅ (5 decisions LOCKED, all invariants defined)
- Non-Goals explicitly stated: ✅ (Section: Non-Goals)
- Orphaned routes disposition documented: ✅ (Appendix B — 7 files, all dispositioned)
- Tier mapping complete: ✅ (Appendix A — 78 routes, zero phantom names)
- Migration plan present: ✅ (Appendix C — Steps 1–6 with Alembic)
- Follow-up ADRs identified: ✅ (ADR-060 through ADR-063)
- CTO corrections applied: ✅ (C-180-01 through C-180-06 all addressed)

**Findings Resolved** (P0/P1 from initial review):

| Finding | Resolution |
|---------|-----------|
| P0-Arch-01: Appendix A phantom routes | Rewritten with actual file names from filesystem audit |
| P1-Arch-02: Missing Options for D3/D4/D5 | G0.2 table documents 3-option CPO decision; D3/D4/D5 context sufficient for SDLC 6.1.0 PROFESSIONAL tier |
| P1-Arch-03: HS256 key management not documented | INV-06 Magic Link documents JWT signing, expiry, JTI; full key rotation policy deferred to ADR-061 (Sprint 182) |
| P2-Arch-04: No Testability section | ADR-059 is a strategic/governance ADR; testability = tier gate enforcement tests in Sprint 184 (ADR-060 scope) |

**G2 Sign-Off**: Architecture foundation for Sprint 181 is approved. [@coder: Sprint 181 may begin route activation per ADR-059 D4 + Appendix B disposition.]

---

## 7. Gate G-Sprint-Close Checklist (SDLC 6.1.0 Pillar 2)

| # | Criterion | Status | Evidence |
|---|-----------|--------|----------|
| 1 | Sprint goal delivered (ADR-059 + Sprint 179 close) | ✅ PASS | Deliverables 1–5 above |
| 2 | All deliverables complete (5/5) | ✅ PASS | Section 3 — all ✅ |
| 3 | No production code (docs-only sprint) | ✅ PASS | Zero new .py files committed |
| 4 | No P0/P1 bugs open | ✅ PASS | All @reviewer + @architect P0 findings resolved |
| 5 | ADR created + locked decisions documented | ✅ PASS | ADR-059 ACCEPTED, 5 decisions LOCKED |
| 6 | Sprint close doc created within 24h | ✅ PASS | This document (Feb 24, 2026) |
| 7 | Next sprint (Sprint 181) backlog defined | ✅ PASS | Sprint 180 plan + Appendix B disposition |
| 8 | CTO corrections applied | ✅ PASS | C-180-01 through C-180-06 all addressed in ADR-059 |

**G-Sprint-Close Decision**: ✅ **APPROVED** — All 8 criteria pass.

---

## 8. Documentation Updated

| Document | Version | Update |
|----------|---------|--------|
| `SPRINT-179-CLOSE.md` | Final | Test counts corrected (87 prior, 121 total); file counts corrected |
| `ADR-059-Enterprise-First-Refocus.md` | ACCEPTED | 5 locked decisions + 6 invariants + 5 appendices |
| `SPRINT-180-ENTERPRISE-FIRST-REFOCUS.md` | Final | This document |

---

## 9. Sprint Retrospective

### What Went Well

- **CTO corrections surfaced early**: C-180-01 through C-180-06 identified before implementation, preventing Sprint 181 bugs. Particularly valuable: discovering `ProjectTier` is a plain `str` class (not `enum.Enum`) and `SubscriptionPlan` has no PROFESSIONAL value.
- **Docs-only discipline held**: No scope creep into implementation. Every "we should also fix..." impulse was documented in ADR-059 Appendix E (deferred) instead of executed.
- **@reviewer / @architect reviews caught P0 issues**: Phantom route names in Appendix A (24+ invented files) and wrong PostgreSQL type name in Appendix C were caught before Sprint 181 could use incorrect data.

### What Needs Improvement

**Lesson: ADR appendices that reference source-of-truth data must be verified against actual files before publishing.**

- Appendix A contained 24+ phantom file names (e.g., `users.py`, `health.py`, `sprint_planning.py`) that do not exist in `backend/app/api/routes/`.
- Root cause: Appendix A was generated from memory/inference rather than from a filesystem `ls` + `grep` of actual files.

**Corrective action**: Before writing any appendix that maps or lists source code files, run:
```bash
ls backend/app/api/routes/*.py | sort
grep "include_router" backend/app/main.py | sort
```
Then cross-reference the two lists. Takes 30 seconds, prevents the class of error found here.

**Lesson: PostgreSQL enum type names are NOT derived from the Python class name.**

- `SubscriptionPlan` class → PostgreSQL type `subscription_plan_enum` (explicit `name=` parameter)
- Always check the Alembic migration or SQLAlchemy `Enum(name=...)` parameter before writing migration scripts.

### Lessons Applied to Sprint 181+

| Lesson | Sprint 181 Action |
|--------|------------------|
| Filesystem audit before route tables | Sprint 181 DoD: `ls routes/` + `grep include_router` before any route table |
| PostgreSQL type name verification | Sprint 181 Alembic: check `name=` in SQLAlchemy column definition |
| Phantom-name prevention | DoD template addition: "Verify all file names against `ls` output" |
| F-179-01 repeat prevention | DoD template still includes `__init__.py` export check (carried from Sprint 179) |

---

## 10. Sprint Metrics

| Metric | Value |
|--------|-------|
| Sprint number | 180 |
| Sprint type | Docs-only (no feature code) |
| Sprint duration | 4 working days |
| Deliverables | 5/5 (100%) |
| New documents | 3 (SPRINT-179-CLOSE.md, ADR-059, SPRINT-180 plan) |
| Modified documents | 1 (SPRINT-179-CLOSE.md corrections) |
| New production code | 0 (docs-only sprint) |
| P0 bugs shipped | 0 |
| Post-creation corrections | 3 (Appendix A phantom routes, Appendix C type name, Sprint 179 test count) |
| Budget | ~$2,560 (32 hrs × $80/hr) |
| Gate G-Sprint-Close | ✅ APPROVED (8/8 criteria) |

---

## 11. Sprint 181 Handoff

**Sprint 181 goal**: OTT Foundation + Orphaned Route Activation

**Pre-conditions from Sprint 180** (all met):
- ✅ ADR-059 D4 locked: 7 orphaned routes dispositioned (Appendix B)
- ✅ ADR-059 D3 locked: OTT channel priority confirmed (Teams/Slack=P0, Telegram/Zalo=P1)
- ✅ Appendix C migration plan ready: `subscription_plan_enum` type name verified, STANDARD backfill present
- ✅ `templates.py` flagged as public endpoint requiring `slowapi` rate limiter (100 req/min per IP)
- ✅ `invitations.py` flagged as needing `sync Session → AsyncSession` fix before registration

**Sprint 181 P0 deliverables** (from ADR-059 Appendix E + Sprint 181 scope):
1. `agent_bridge/` package: `protocol_adapter.py`, `telegram_normalizer.py`, `zalo_normalizer.py`
2. 7 orphaned route registrations in `main.py` (per Appendix B disposition)
3. Alembic migration `s181_001_tier_billing_unification.py` (per Appendix C)
4. `invitations.py` async fix (sync `Session` → `AsyncSession`) before registration
5. `templates.py` `slowapi` rate limiter (100/min per IP)

---

*Sprint 180 formally closed on 2026-02-24. Sprint 181 begins: OTT Foundation + Route Activation.*
