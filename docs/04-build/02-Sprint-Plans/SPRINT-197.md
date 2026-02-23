# Sprint 197 — Master Test Plan + Technical Debt + Go-Live Preparation

**Sprint Duration**: February 24 – March 7, 2026 (10 working days)
**Sprint Goal**: Establish comprehensive master test plan for Stage 05, resolve critical technical debt from Sprint 196 carry-forwards, and close all go-live blockers (36 server errors, API health 94.8% → 97%+)
**Status**: COMPLETE ✅ (CTO 9.3/10)
**Priority**: P0 (Go-Live Readiness)
**Framework**: SDLC 6.1.1
**CTO Score (Sprint 196)**: 9.3/10 (PM Review)
**Previous Sprint**: [Sprint 196 COMPLETE — EP-06 Codegen Quality Gates + Vietnamese SME Pilot Prep](SPRINT-196-CODEGEN-PILOT-PREP.md)

---

## Sprint 197 Goal

Sprint 196 delivered 3 Vietnamese domain templates and 430 codegen tests but the E2E API report (Feb 21) reveals **36 server errors** and **94.8% API health** (target: >95%). Sprint 197 addresses these go-live blockers while establishing the master test plan for Stage 05 and resolving accumulated technical debt.

**Three pillars**:
1. **Master Test Plan** — Comprehensive Stage 05 test documentation (missing: Security, Performance, Accessibility)
2. **Technical Debt** — Sprint 196 carry-forwards (CF-01/02/03) + P1 code TODOs
3. **Go-Live Blockers** — Fix 36 server errors, achieve API health >97%

**Conversation-First** (CEO directive Sprint 190): All sprint governance flows through OTT+CLI. Web App = admin-only.

---

## Sprint 197 Backlog

### Track A — Master Test Plan: Stage 05 Documentation (Day 1-4) — @tester

**Goal**: Create comprehensive test documentation for 3 missing test categories + update existing docs.

| ID | Item | Priority | Deliverable |
|----|------|----------|-------------|
| A-01 | Master Test Plan index (docs/05-test/MASTER-TEST-PLAN.md) | P1 | Unified test plan covering all 7 categories with traceability to SDLC 6.1.1 stages |
| A-02 | Security Testing plan (docs/05-test/02-Security-Testing/) | P1 | OWASP ASVS L2 test procedures, Semgrep CI rules, penetration test checklist |
| A-03 | Performance Testing plan (docs/05-test/05-Performance-Testing/) | P2 | Locust scenarios (100K concurrent), p95 <100ms verification, DB query profiling |
| A-04 | Accessibility Testing plan (docs/05-test/06-Accessibility-Testing/) | P2 | WCAG 2.1 AA checklist, Lighthouse CI >90 score, keyboard navigation matrix |
| A-05 | Update E2E Testing docs (docs/05-test/07-E2E-Testing/) | P1 | Add Playwright critical path tests (10 user journeys), codegen E2E flow |
| A-06 | Test factory specifications | P2 | Factory patterns for 6 core models (User, Project, Gate, Evidence, Policy, Codegen) |

**Acceptance criteria**:
- [ ] MASTER-TEST-PLAN.md links to all 7 test categories (01-09)
- [ ] Security testing plan covers OWASP API1-10 (not just API1-2)
- [ ] Performance testing plan includes Locust scripts for 3 endpoints
- [ ] Accessibility plan has automated Lighthouse CI config
- [ ] 10 critical E2E user journeys documented with Playwright selectors

---

### Track B — Go-Live Blockers: Fix 36 Server Errors (Day 2-5) — @pm

**Goal**: Reduce server errors from 36 → 0, API health from 94.8% → 97%+.

| ID | Item | Root Cause | Priority | Action |
|----|------|-----------|----------|--------|
| B-01 | Fix double-prefixed routes (~10 endpoints) | Router registration adds `/api/v1/` prefix twice | P0 | Audit all router `include_router()` calls, remove duplicate prefixes |
| B-02 | Fix missing env var endpoints (~5 endpoints) | `GITHUB_APP_WEBHOOK_SECRET`, Ollama URL, Payments config not set | P1 | Add graceful fallback when env vars missing (return 503 + actionable message) |
| B-03 | Fix DB/service dependency failures (~8 endpoints) | Missing migrations, uninitialized services | P1 | Run `alembic upgrade head`, ensure all services init on startup |
| B-04 | Fix auth timeout endpoints (~3 endpoints) | Register/forgot-password/reset-password >15s | P2 | Profile auth flow, optimize bcrypt rounds or add async |
| B-05 | Re-run E2E API test suite | Validate fixes | P0 | Generate new E2E-API-REPORT-2026-02-XX.md with >97% health |

**Acceptance criteria**:
- [ ] 0 double-prefixed routes (`/api/v1/api/v1/...` eliminated)
- [ ] Server error count: 36 → <5
- [ ] API health score: 94.8% → >97%
- [ ] New E2E report generated and stored in `docs/05-test/07-E2E-Testing/reports/`

---

### Track C — Technical Debt Resolution (Day 3-7) — @pm

**Goal**: Resolve Sprint 196 carry-forwards + top P1 TODOs.

| ID | Item | Source | Priority | Action |
|----|------|--------|----------|--------|
| C-01 | Fix ruff lint warnings in generated code | Sprint 196 Known Issue #1 | P1 | Fix template imports: add `from datetime import date`, remove unused `sqlalchemy.Column`, fix `true` → `True` |
| C-02 | Fix model processor filename truncation | Sprint 196 Known Issue #2 | P1 | Increase max filename length to 50 chars, `Employee` → `employee.py` |
| C-03 | Enable Gate 4 subprocess sandbox | CF-01 (P2) | P2 | Add `GATE4_ENABLED` env var, flip `skip_tests` default when enabled |
| C-04 | Create pytest-benchmark suite | CF-02 (P3) | P3 | `test_quality_pipeline_benchmark.py` — Gate 1-4 latency benchmarks |
| C-05 | Fix auth.py L703 redundant condition | CF-03 (P3) | P3 | Remove redundant condition in tier_rank logic |
| C-06 | Fix validation test collection warnings | 9 pytest warnings | P3 | Rename inner `TestValidator*` classes to `_TestValidator*` to avoid pytest collection conflicts |
| C-07 | Install pytest-benchmark | Missing dependency | P3 | Add `pytest-benchmark>=4.0` to requirements-test.txt |

**Acceptance criteria**:
- [ ] `ruff check` passes on all 6 domain template generated code (Gate 1 green)
- [ ] Generated filenames: `Employee` → `employee.py` (not `employe.py`)
- [ ] Gate 4 activatable via `GATE4_ENABLED=true` env var
- [ ] `test_quality_pipeline_benchmark.py` exists with 4+ benchmarks
- [ ] 0 pytest collection warnings in `tests/unit/validation/`

---

### Track D — Go-Live Readiness Checklist (Day 8-10) — @pm + @tester

**Goal**: Final go-live readiness verification against SDLC 6.1.1 Stage 05 exit criteria.

| ID | Item | Priority | Action |
|----|------|----------|--------|
| D-01 | Go-live readiness matrix update | P1 | Update `REMEDIATION-PLAN-GOLIVE-2026.md` with Sprint 197 progress |
| D-02 | OWASP ASVS L2 re-validation | P1 | Verify 264/264 requirements still met after Sprint 196-197 changes |
| D-03 | Full test suite green run | P0 | `pytest backend/tests/ -v` — 4,547+ tests, 0 failures |
| D-04 | Sprint 197 close documentation | P1 | G-Sprint-Close submission within 24h |

**Acceptance criteria**:
- [ ] Go-live readiness matrix shows all P0/P1 items resolved
- [ ] OWASP ASVS L2 score maintained at ≥98%
- [ ] Full backend test suite passes (4,547+ tests)
- [ ] G-Sprint-Close submitted

---

## Sprint 197 Success Criteria

- [ ] MASTER-TEST-PLAN.md created with 7-category coverage
- [ ] Security/Performance/Accessibility test plans created (3 new docs)
- [ ] Server errors reduced: 36 → <5
- [ ] API health score: 94.8% → >97%
- [ ] ruff lint warnings fixed in codegen templates (Gate 1 green for all 6 domains)
- [ ] Model processor filename truncation fixed (`Employee` → `employee.py`)
- [ ] Gate 4 activatable via env var (CF-01 resolved)
- [ ] pytest-benchmark suite created (CF-02 resolved)
- [ ] Full backend test suite green (4,547+ tests, 0 failures)
- [ ] Go-live readiness matrix updated
- [ ] G-Sprint-Close within 24h of sprint end

---

## Current Test Metrics (Sprint 196 Baseline)

| Metric | Current | Target | Gap |
|--------|---------|--------|-----|
| Backend test files | 214 | 220+ | +6 |
| Backend test functions | 4,547 (collected) | 4,600+ | +53 |
| Unit tests | 3,096 | 3,200+ | +104 |
| Integration tests | 993 | 1,000+ | +7 |
| E2E tests | 85 | 100+ | +15 |
| API health score | 94.8% | >97% | +2.2% |
| Server errors (5xx) | 36 | <5 | -31 |
| Codegen tests | 430 | 430 (maintained) | 0 |
| OWASP ASVS L2 | 98.4% | ≥98% | 0 |
| p95 latency | 14.0ms | <100ms | PASS |

---

## Technical Debt Inventory (Sprint 197 Scope)

### P1 — Critical (Sprint 197 Target)

| # | Issue | Files | Effort |
|---|-------|-------|--------|
| 1 | Ruff lint warnings in generated code (unused imports, undefined names) | Codegen templates | 4-6h |
| 2 | Model processor filename truncation | `model_processor.py` | 2-3h |
| 3 | 10 double-prefixed routes (`/api/v1/api/v1/...`) | Router includes in `main.py` | 2-3h |
| 4 | 5 missing env var endpoints returning 500 | Webhook/Ollama/Payments routes | 2-3h |
| 5 | 8 DB/service dependency failures | Various routes | 3-4h |

**Total P1 effort**: ~15-19 hours

### P2 — Medium (Sprint 197 Stretch)

| # | Issue | Files | Effort |
|---|-------|-------|--------|
| 1 | Gate 4 `skip_tests=True` default (CF-01) | `quality_pipeline.py` | 1-2h |
| 2 | CRP smart reviewer assignment stub | `crp_service.py` | 2-3h |
| 3 | Blueprint reconstruction from session stub | `codegen.py` | 2-3h |
| 4 | Auth timeout on register/forgot-password | Auth routes | 2-3h |

### P3 — Low (Backlog for Sprint 198+)

| # | Issue | Effort |
|---|-------|--------|
| 1 | pytest-benchmark file (CF-02) | 2h |
| 2 | auth.py L703 redundant condition (CF-03) | 30min |
| 3 | Validation test collection warnings | 1h |
| 4 | Vibecoding caching not persisted (3 TODOs) | 3-4h |
| 5 | GitHub webhook status not posted | 2-3h |

---

## Stage 05 Test Documentation Gap Analysis

| Category | Directory | Status | Sprint 197 Action |
|----------|-----------|--------|-------------------|
| 00 - Test Strategy | `00-TEST-STRATEGY-2026.md` | ✅ EXISTS | Reference in MASTER-TEST-PLAN.md |
| 01 - Test Strategy | `01-Test-Strategy/` | ✅ EXISTS (5 docs) | Link from master plan |
| 02 - Security Testing | **MISSING** | ❌ EMPTY | **CREATE**: OWASP procedures, Semgrep CI, pentest checklist |
| 03 - Unit Testing | `03-Unit-Testing/` | ✅ EXISTS (2 docs) | Add factory pattern guide |
| 04 - Integration Testing | `04-Integration-Testing/` | ✅ EXISTS (2 docs) | Add OPA/Redis/Ollama test plans |
| 05 - Performance Testing | **MISSING** | ❌ EMPTY | **CREATE**: Locust scenarios, p95 verification, DB profiling |
| 06 - Accessibility Testing | **MISSING** | ❌ EMPTY | **CREATE**: WCAG 2.1 AA, Lighthouse CI, keyboard nav |
| 07 - E2E Testing | `07-E2E-Testing/` | ✅ EXISTS (10+ docs) | Add 10 Playwright critical paths |
| 08 - API Testing | `08-API-Testing/` | ✅ EXISTS (1 doc) | Expand beyond GitHub to all 91 endpoints |
| 09 - Load Testing | `09-Load-Testing/` | ✅ EXISTS (1 doc) | Add Locust scripts |

---

## Risk Assessment

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Double-prefix routes deeper than expected | P0 — more endpoints broken | Medium | Comprehensive router audit in Track B |
| Template fixes break existing domain tests | P1 — regression | Medium | Run full 430 codegen tests after each fix |
| API health target (>97%) not achievable in 1 sprint | P1 — go-live delay | Low | Focus on P0 server errors first; stretch to 97% |
| Missing env vars in staging | P2 — test failures | High | Document all required env vars in .env.example |

---

## Dependencies

- **Staging environment**: Must be available for E2E re-test (Track B-05)
- **pytest-benchmark**: Must be installed before CF-02 (Track C-07 → C-04)
- **Codegen templates**: Template fixes (Track C-01) must precede E2E re-validation

---

---

## G-Sprint-Close Verdict

**CTO Score**: 9.3/10 — APPROVED
**Date**: February 23, 2026
**Reviewer**: CTO

### Completed (8/8 items)

| Track | Items | Status |
|-------|-------|--------|
| B-01 | Double-prefix fix (invitations + org-invitations) + TG-41 gap | ✅ |
| C-01 | Ruff lint warnings in `model.py.j2` (Column, Date, boolean) | ✅ |
| C-02 | Singularization fix in `model_processor.py` + `endpoint_processor.py` | ✅ |
| C-03 | `GATE4_ENABLED` env var in `quality_pipeline.py` | ✅ |
| C-04 | `test_quality_pipeline_benchmark.py` — 6 benchmarks | ✅ |
| C-05 | Removed redundant condition in `auth.py` | ✅ |
| C-06 | Fixed 5 pytest collection warnings in `test_base_validator.py` | ✅ |
| C-07 | Added `pytest-benchmark>=4.0` to `dev.txt` | ✅ |

### Test Verification

| Suite | Count | Status |
|-------|-------|--------|
| Codegen (templates, E2E, benchmarks, pipeline) | 436 | ✅ |
| Middleware (tier gate, CFG, usage limits) | 97 | ✅ |
| Validation (base validator, registry) | 29 | ✅ |
| Other affected quick tests | 114 | ✅ |
| **Sprint 197 Total** | **676** | **0 regressions** |

### Carry-Forwards → Sprint 198

| ID | Item | Reason |
|----|------|--------|
| CF-01 | B-02/B-03: env var endpoints + DB/service failures | Pre-existing (153 failures + 99 errors) |
| CF-02 | B-04/B-05: auth timeouts + E2E re-run | Depends on staging environment |
| CF-03 | Track A: Master Test Plan (6 items) | Assigned to @tester, not PM scope |

---

**Last Updated**: February 23, 2026
**Created By**: PM + AI Development Partner — Sprint 197 G-Sprint-Close
**Framework Version**: SDLC 6.1.1
**Previous State**: Sprint 196 COMPLETE (9.3/10)
