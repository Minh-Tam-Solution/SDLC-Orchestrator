# Sprint 196 — EP-06 Codegen Quality Gates + Vietnamese SME Pilot Prep

```yaml
sprint: 196
title: "EP-06 Codegen Quality Gates + Vietnamese SME Pilot Prep"
duration: "February 24 – March 7, 2026 (10 working days)"
status: PLANNED
priority: P1 (Codegen Production Readiness + Pilot Enablement)
framework: SDLC 6.1.1
epic: EP-06 IR-Based Codegen Engine
previous: "Sprint 195 — Tier Enforcement Unification (ADR-065, CTO 9.2/10)"
trigger: "Sprint 195 deferred original scope (EP-06 + Pilot) after P0 hotfix consumed the sprint"
carry_forwards:
  - "CF-03/TG-41: 8 ungated route prefixes in ROUTE_TIER_TABLE (P2, pre-existing since Sprint 185)"
  - "F-12: Gate 4 Docker sandbox for EP-06 quality pipeline (P3, infrastructure)"
```

---

## Sprint 196 Goal

Sprint 195 was consumed by a P0 hotfix (Tier Enforcement Unification — ADR-065), deferring the original planned scope. Sprint 196 picks up that deferred scope: harden the EP-06 4-Gate Quality Pipeline for production codegen, validate `qwen3-coder:30b` integration, and prepare 3 founding-customer onboarding flows for the Vietnamese SME pilot.

Additionally, Sprint 196 resolves TG-41 (8 ungated routes) — a carry-forward that has persisted since Sprint 185.

**Root Context**:
- EP-06 Gates 1-3 are production-ready (291/291 tests passing)
- Gate 4 (Test Execution) is stubbed — returns `GateStatus.SKIPPED` (requires Docker sandbox)
- `qwen3-coder:30b` (256K context) is deployed on RTX 5090 but not integration-tested end-to-end
- Vietnamese domain templates exist in test suite (530 LOC `test_domain_templates.py`) but no onboarding flows
- `SprintTemplateService` (Sprint 78, 169 LOC) provides template CRUD — can be extended for pilot onboarding

**Conversation-First** (CEO directive Sprint 190): All sprint governance flows through OTT+CLI. Web App = admin-only.

---

## 4-Track Execution Plan

### Track A — Carry-Forward Fixes (Day 1)

Resolve persistent carry-forwards before new feature work begins.

| # | Deliverable | File(s) | Priority | Tests |
|---|-------------|---------|----------|-------|
| A-01 | TG-41: Assign tier levels to 8 ungated routes | `tier_gate.py` | P2 | 1 (TG-41 goes green) |
| A-02 | Gate 4 Docker sandbox (initial implementation) | `quality_pipeline.py` | P3 | 3 |

**A-01 — TG-41 Route Tier Assignment**

8 FastAPI route prefixes registered in `main.py` but missing from `ROUTE_TIER_TABLE`:

| Route Prefix | Proposed Tier | Rationale |
|-------------|---------------|-----------|
| `/api/v1/agents-md` | 2 (STANDARD) | AGENTS.md overlay — team collaboration feature |
| `/api/v1/api` | 1 (LITE) | API documentation/metadata — public-facing |
| `/api/v1/auto-generate` | 3 (PROFESSIONAL) | AI auto-generation — advanced feature |
| `/api/v1/evidence-manifests` | 2 (STANDARD) | Evidence manifest management — extends Evidence Vault |
| `/api/v1/onboarding` | 1 (LITE) | Onboarding wizard — must be accessible to all tiers |
| `/api/v1/risk` | 2 (STANDARD) | Risk analysis — team planning feature |
| `/api/v1/timeline` | 2 (STANDARD) | Project timeline — team planning feature |
| `/api/v1/vibecoding` | 2 (STANDARD) | Vibecoding index — quality assurance feature |

*CTO review required: confirm tier assignments before implementation.*

**A-02 — Gate 4 Docker Sandbox**

Replace the `GateStatus.SKIPPED` stub in `quality_pipeline.py` (line 697) with a real Docker-based test execution:
- Use `subprocess` to run `docker run --rm -v` with generated code mounted
- Timeout: 60s max per test run
- Fallback: if Docker unavailable, return `GateStatus.SKIPPED` with clear message (preserve current behavior)
- Scaffold mode: smoke test only (check if project builds)
- Production mode: full `pytest` execution

---

### Track B — EP-06 Codegen Production Hardening (Day 2-5)

| # | Deliverable | File(s) | Tests |
|---|-------------|---------|-------|
| B-01 | `qwen3-coder:30b` end-to-end integration test | `test_ollama_provider.py`, `ollama_provider.py` | 5 |
| B-02 | Provider fallback chain validation under failure | `test_codegen_service.py`, `codegen_service.py` | 4 |
| B-03 | Gate 1-3 integration test with real `ruff` + `semgrep` | `test_codegen_service_quality_gates.py` | 3 |
| B-04 | Quality Pipeline latency benchmarks | `test_quality_pipeline_benchmark.py` (NEW) | 3 |

**B-01 — qwen3-coder:30b Integration**

Validate the full code generation loop with `qwen3-coder:30b`:
- Prompt with 3 Vietnamese domain specs (E-commerce, HRM, CRM)
- Verify generated code passes Gates 1-3
- Measure latency: target <15s p95
- Verify 256K context window handles large specs without truncation

**B-02 — Provider Fallback Chain**

Test failure scenarios for the Ollama → Claude → Rule-based chain:
- Ollama timeout (>15s) → fallback to Claude
- Ollama connection error → fallback to Claude
- Claude rate limit → fallback to rule-based
- All providers fail → graceful error with Evidence record

**B-03 — Real Tool Integration**

Current Gate 1-3 tests mock subprocess calls. Add integration tests that run real `ruff check` and `semgrep` against generated Python code:
- Gate 1: `ruff check --output-format=json` on generated code
- Gate 2: `semgrep --config=p/python --json` on generated code
- Gate 3: Import validation with real `ast.walk`

**B-04 — Latency Benchmarks**

Create `pytest-benchmark` tests for the quality pipeline:
- Gate 1 (Syntax): target <5s
- Gate 2 (Security): target <10s
- Gate 3 (Context): target <10s
- Gate 4 (Tests): target <60s (Docker)
- Full pipeline (4 gates): target <85s total

---

### Track C — Vietnamese SME Pilot Onboarding (Day 4-8)

| # | Deliverable | File(s) | Tests |
|---|-------------|---------|-------|
| C-01 | E-commerce domain onboarding flow | `pilot_onboarding_service.py` (NEW) | 3 |
| C-02 | HRM domain onboarding flow | `pilot_onboarding_service.py` | 3 |
| C-03 | CRM domain onboarding flow | `pilot_onboarding_service.py` | 3 |
| C-04 | Onboarding API endpoints (2 endpoints) | `api/routes/onboarding.py` | 4 |
| C-05 | Vietnamese domain template validation | `test_domain_templates.py` | 3 |

**C-01/C-02/C-03 — Domain Onboarding Flows**

New `PilotOnboardingService` wraps existing `SprintTemplateService` + `AgentSeedService`:

```python
class PilotOnboardingService:
    async def create_pilot_project(
        self, domain: PilotDomain, org_id: UUID, owner_id: UUID
    ) -> PilotOnboardingResult:
        """
        Create a fully-configured pilot project for a Vietnamese SME.

        Steps:
        1. Create Project with domain metadata (e-commerce/hrm/crm)
        2. Apply domain-specific sprint template (from SprintTemplateService)
        3. Seed domain-specific agent team (from AgentSeedService)
        4. Generate initial CURRENT-SPRINT.md (from SprintFileService)
        5. Return onboarding summary with next steps
        """
```

**3 Domain Templates**:

| Domain | Template | Key Entities | Vietnamese Context |
|--------|----------|-------------|-------------------|
| E-commerce | `ecommerce_vn` | Product, Order, Customer, Payment (VND) | Shopee/Tiki integration patterns, COD support |
| HRM | `hrm_vn` | Employee, Attendance, Payroll, Leave | Vietnamese labor law compliance, social insurance |
| CRM | `crm_vn` | Lead, Contact, Deal, Activity | Zalo integration, Vietnamese phone format |

**C-04 — Onboarding API**

Two new endpoints registered in existing `onboarding.py` router:

```
POST /api/v1/onboarding/pilot          — Create pilot project for founding customer
GET  /api/v1/onboarding/pilot/domains  — List available domain templates
```

---

### Track D — Quality + Documentation (Day 8-10)

| # | Deliverable | File(s) | Tests |
|---|-------------|---------|-------|
| D-01 | Codegen E2E test: spec → IR → code → validate | `test_codegen_e2e.py` (NEW) | 3 |
| D-02 | Onboarding test expansion | `test_onboarding.py` | 8 |
| D-03 | Sprint 196 close documentation | SPRINT-196-CLOSE.md | — |
| D-04 | Update SPRINT-INDEX.md + CURRENT-SPRINT.md | Sprint docs | — |

**D-01 — Codegen E2E Test**

End-to-end test covering the full pipeline:
1. Input: Vietnamese E-commerce spec (product CRUD)
2. IR transformation
3. Code generation (Ollama qwen3-coder:30b or mock)
4. Quality Pipeline (Gates 1-3)
5. Evidence capture
6. Assert: generated code passes all gates

**D-02 — Onboarding Test Expansion**

Current `test_onboarding.py` has ~4 tests (570 LOC — mostly setup). Expand to 12+ tests:
- Pilot project creation for each domain (3)
- Domain template listing (1)
- Duplicate pilot prevention (1)
- Invalid domain handling (1)
- Agent seeding verification (1)
- Sprint template application (1)

---

## Files Summary

| File | Action | LOC | Track |
|------|--------|-----|-------|
| `backend/app/middleware/tier_gate.py` | MODIFY | +10 | A |
| `backend/app/services/codegen/quality_pipeline.py` | MODIFY | +80 | A+B |
| `backend/app/services/codegen/ollama_provider.py` | MODIFY | +20 | B |
| `backend/app/services/codegen/codegen_service.py` | MODIFY | +15 | B |
| `backend/app/services/pilot_onboarding_service.py` | NEW | ~200 | C |
| `backend/app/api/routes/onboarding.py` | MODIFY | +40 | C |
| `backend/app/schemas/onboarding.py` | NEW/MODIFY | ~60 | C |
| `backend/tests/unit/test_tier_gate.py` | VERIFY | — | A (TG-41 green) |
| `backend/tests/unit/services/codegen/test_quality_pipeline_benchmark.py` | NEW | ~100 | B |
| `backend/tests/unit/services/codegen/test_codegen_e2e.py` | NEW | ~120 | D |
| `backend/tests/unit/test_onboarding.py` | MODIFY | +200 | D |
| Sprint docs (CLOSE, INDEX, CURRENT-SPRINT) | MODIFY | ~100 | D |

**Total**: ~945 LOC (production + tests)

---

## ADR-065 Invariant Verification

Sprint 196 inherits the ADR-065 invariants from Sprint 195. All new endpoints must comply:

| Invariant | Sprint 196 Impact |
|-----------|-------------------|
| INV-01: All 3 middleware resolve tier consistently (org-based) | A-01 assigns tiers to 8 new routes — middleware already correct |
| INV-02: is_superuser OR is_platform_admin → ENTERPRISE everywhere | No change — middleware unchanged |
| INV-03: No org memberships → LITE (safe default) | No change |
| INV-04: Frontend tier display === backend tier resolution | No change — `useUserTier.ts` fixed in Sprint 195 |

---

## Success Criteria

- [ ] TG-41 test passes (0 ungated routes) — carry-forward resolved
- [ ] Gate 4 Docker sandbox runs `pytest` on generated code (scaffold mode)
- [ ] `qwen3-coder:30b` generates valid code for 3 Vietnamese domain specs
- [ ] Provider fallback chain handles timeout/error scenarios correctly
- [ ] 3 founding-customer onboarding flows functional via API
- [ ] Codegen E2E test passes (spec → IR → code → validate)
- [ ] Quality Pipeline p95 latency benchmarked: <15s (Ollama), <85s (full pipeline)
- [ ] Onboarding tests expanded from ~4 to 12+ test cases
- [ ] `ruff check` 0 errors on all modified files
- [ ] G-Sprint-Close within 24h of sprint end

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Docker unavailable in CI environment | Medium | Gate 4 tests skip | Fallback to `GateStatus.SKIPPED` — same as current behavior |
| Ollama server latency >15s for large specs | Medium | Benchmark failure | Use smaller specs for benchmark; set realistic targets |
| `qwen3-coder:30b` Vietnamese code quality low | Low | Pilot delay | Fallback to Claude for Vietnamese pilot; validate in B-01 |
| Onboarding flows depend on `SprintTemplateService` gaps | Low | C-track delay | SprintTemplateService already has CRUD; minimal extension needed |

---

## Dependencies

| Dependency | Status | Sprint 196 Impact |
|-----------|--------|-------------------|
| EP-06 Quality Pipeline (Gates 1-3) | ✅ Production-ready (291/291 tests) | Foundation for Track B hardening |
| ADR-065 Tier Resolution | ✅ Complete (Sprint 195) | A-01 assigns tiers to remaining routes |
| AgentSeedService (12 roles) | ✅ Complete (Sprint 194) | C-01/C-02/C-03 seed domain agents |
| SprintTemplateService | ✅ Active (Sprint 78) | C-01/C-02/C-03 apply domain templates |
| SprintFileService | ✅ Complete (Sprint 193) | C-01/C-02/C-03 generate CURRENT-SPRINT.md |
| Docker (for Gate 4) | ⚠️ Required | A-02 needs Docker daemon access |
| Ollama `qwen3-coder:30b` | ⚠️ Required for B-01 | Must be running on RTX 5090 |

---

## Sprint 196 Schedule

| Day | Track | Focus |
|-----|-------|-------|
| Day 1 | A | TG-41 fix + Gate 4 Docker sandbox |
| Day 2-3 | B | qwen3-coder:30b integration + fallback chain validation |
| Day 4-5 | B+C | Quality Pipeline benchmarks + E-commerce onboarding |
| Day 6-7 | C | HRM + CRM onboarding flows + API endpoints |
| Day 8 | C+D | Onboarding test expansion + codegen E2E test |
| Day 9 | D | Documentation + sprint close prep |
| Day 10 | D | G-Sprint-Close submission |

---

**Sprint 196 Planned**: February 22, 2026
**Target Start**: February 24, 2026
**Target End**: March 7, 2026
**Updated By**: PM + AI Development Partner
**Framework Version**: SDLC 6.1.1
**Previous Sprint**: [Sprint 195 COMPLETE — Tier Enforcement Unification (ADR-065)](SPRINT-195-TIER-ENFORCEMENT-UNIFICATION.md)
