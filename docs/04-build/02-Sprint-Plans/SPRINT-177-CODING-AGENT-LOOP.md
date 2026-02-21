# Sprint 177: "Coding Agent Loop + Multi-Agent Core Services" — ADR-055 Phase 2 + ADR-056 P0 Implementation

**Sprint Duration**: March 31 - April 11, 2026 (10 working days)
**Status**: PLANNED
**Phase**: Stage 04 (BUILD) — Autonomous Codegen Phase 2 + Multi-Agent Core Implementation
**Framework**: SDLC 6.1.0
**Priority**: P0 (ADR-055 Phase 2 + ADR-056 P0 Services)
**Previous Sprint**: [Sprint 176 — Autonomous Codegen & Multi-Agent Foundation](SPRINT-176-AUTONOMOUS-CODEGEN-PILOT-PREP.md)
**ADR References**:
- [ADR-055 — Autonomous Codegen with 4-Gate Validation](../../02-design/ADR-055-Autonomous-Codegen-4-Gate-Validation.md)
- [ADR-056 — Multi-Agent Team Engine](../../02-design/ADR-056-Multi-Agent-Team-Engine.md)
**Epic**: [EP-07 — Multi-Agent Team Engine](../../01-planning/02-Epics/EP-07-Multi-Agent-Team-Engine.md)
**Framework Reference**: [11-AUTONOMOUS-CODEGEN-PATTERNS.md](../../../SDLC-Enterprise-Framework/03-AI-GOVERNANCE/11-AUTONOMOUS-CODEGEN-PATTERNS.md)
**Archived**: Pre-ADR-056 version → docs/10-archive/04-Legacy/02-Sprint-Plans/

---

## Sprint Goal

Implement **ADR-055 Phase 2** (Coding Agent Loop with Gates G2/G3) AND **ADR-056 P0 Core Services** (12 service files, 3 DB tables, 5 P0 API endpoints, 73 unit tests). This sprint builds the multi-agent infrastructure that the coding agent loop depends on for agent-to-agent delegation, provider failover, and security guards.

---

## Sprint Context

**ADR-055 + ADR-056 3-Sprint Arc**:
```
Sprint 176: ADR-056 Foundation + Initializer Agent + Gate G1     ✅ COMPLETE
            ↓ Design docs, schemas, design contracts
            ↓ Spec parsing → feature_list.json

Sprint 177: ADR-056 P0 Services + Coding Agent Loop + G2/G3     ← YOU ARE HERE
            ↓ 3 DB tables (agent_definitions, conversations, messages)
            ↓ 12 service files (registry, queue, tracker, invoker, etc.)
            ↓ 5 P0 API endpoints + 73 unit tests
            ↓ Coding Agent iterative generation + Browser Agent

Sprint 178: Multi-Agent E2E + OTT Scaffold + Codegen Pilot
            → Integration tests + Vietnamese SME Launch
```

**Sprint 176 Deliverables** (dependencies for Sprint 177):
- ADR-056 design documents (BC-056, EP-07, FR-037 to FR-041, STM-056, TP-056)
- Updated Data Model ERD v3.4.0, API Spec v3.6.0
- Design contracts: ConversationLimits, FailoverClassifier, InputSanitizer, ShellGuard, ToolContext, ReflectStep
- Pydantic schemas: `backend/app/schemas/agent_team.py`
- Initializer Agent service (`feature_list.json` generation)
- Gate G1 (Spec Review) with OPA policy

**ADR-056 Sprint 177 Scope** (NEW):

| Day | ADR-056 Deliverable | LOC |
|-----|---------------------|-----|
| 1 | Alembic migration: 3 tables (agent_definitions, agent_conversations, agent_messages) | ~140 |
| 2 | `agent_registry.py` + `mention_parser.py` | ~230 |
| 3 | `message_queue.py` (lane-based, SKIP LOCKED + Redis notify) | ~250 |
| 4 | `conversation_tracker.py` (6 guards + parent-child + budget) | ~200 |
| 5 | `agent_invoker.py` (failover + cooldowns + error-as-string) | ~250 |
| 6 | 5 P0 API endpoints in `routes/agent_team.py` | ~300 |
| 7-8 | Unit tests: 73 test cases across 6 modules | ~500 |

**Sprint 177 Builds On**:
- ADR-056 design contracts from Sprint 176
- `feature_list.json` from Initializer Agent
- Gate state machine from Sprint 173
- Browser Agent from Sprint 176
- MCP client service from Sprint 174

---

## Success Criteria

- [ ] Coding Agent service implements iterative generation loop
- [ ] Gate G2 (Coding Review) integrated — blocks deployment if code quality fails
- [ ] Gate G3 (Testing) integrated — blocks deployment if tests fail
- [ ] Browser Agent performs E2E validation on generated code
- [ ] Auto-correction loop handles up to 3 retry attempts
- [ ] Full workflow: `sdlcctl codegen run --spec spec.yaml` → deployed code
- [ ] Code generation produces Django/React templates with 80%+ test coverage
- [ ] All existing tests pass (0 regressions)
- [ ] ADR-055 Phase 2 integration tests passing

---

## Key Metrics

| Metric | Target | How to Check |
|--------|--------|--------------|
| Code generation success rate (first attempt) | >60% | Track gate G2 pass rate |
| Auto-correction success rate (3 retries) | >85% | Track iterations before gate pass |
| E2E Browser Agent validation | >95% | Browser test pass rate on generated code |
| Gate G2 false positive rate | <5% | Manual review sample of 20 generated features |
| Gate G3 test coverage enforcement | >80% | OPA policy check on pytest coverage |
| End-to-end workflow time (spec → deployed) | <10 min | `time sdlcctl codegen run --spec spec.yaml` |
| Context cache hit rate (iterations) | >70% | Claude Code cache metrics |

---

## Scope

### In Scope

| # | Deliverable | Priority | Days |
|---|-------------|----------|------|
| 1 | Coding Agent service — iterative generation loop | P0 | 3 |
| 2 | Gate G2 (Coding Review) — OPA policy + Semgrep integration | P0 | 2 |
| 3 | Gate G3 (Testing) — pytest coverage enforcement | P0 | 2 |
| 4 | Browser Agent E2E validation loop | P0 | 1.5 |
| 5 | Auto-correction mechanism (max 3 retries) | P0 | 1 |
| 6 | Django + React code templates (80%+ coverage) | P1 | 1 |
| 7 | Integration testing + end-to-end workflow | P0 | 1 |
| 8 | CLI enhancement: `sdlcctl codegen run` | P1 | 0.5 |

**Total**: 12 task-days across 10 calendar days (overlap on smaller tasks)

### Out of Scope (Deferred to Sprint 178+)

| Item | Reason | Sprint |
|------|--------|--------|
| Gate G4 (Deployment) | Pilot deployment uses manual verification | Sprint 178 |
| Multi-provider codegen (OpenAI, Gemini) | ADR-022 deferred, Claude Code only for MVP | Sprint 179+ |
| Custom code templates per organization | Enterprise feature, no demand yet | Future |
| Real-time progress streaming (SSE) | Polling sufficient for MVP | Sprint 179+ |
| Rollback mechanism for failed deployments | Manual rollback for pilot | Sprint 179+ |

---

## Architecture

### Coding Agent Loop (ADR-055 Phase 2)

```
┌─────────────────────────────────────────────────────────┐
│  1. Initializer Agent (Sprint 176)                     │
│     Input: spec.yaml                                    │
│     Output: feature_list.json                          │
│     Gate G1: ✓ Spec Review                            │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  2. Coding Agent (Sprint 177) — ITERATIVE LOOP          │
│     for each feature in feature_list.json:             │
│       • Generate code (Django model + React component)  │
│       • Run Semgrep (SAST)                             │
│       • Gate G2: ✓ Coding Review                       │
│       • Generate tests (pytest + Playwright)           │
│       • Run tests                                       │
│       • Gate G3: ✓ Testing (80%+ coverage)             │
│       • If FAIL: Auto-correct (max 3 retries)          │
│       • If PASS: Store evidence + move to next feature │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  3. Browser Agent E2E Validation (Sprint 177)           │
│     • Start dev server                                  │
│     • Run Playwright E2E tests                         │
│     • Screenshot on failure                            │
│     • Retry logic (3 attempts)                         │
│     • Evidence capture (screenshots + HTML + logs)     │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  4. Deployment (Sprint 178)                             │
│     Gate G4: Manual review for pilot                   │
│     Deploy to staging → Vietnamese SME validation      │
└─────────────────────────────────────────────────────────┘
```

---

## Daily Schedule

### **Days 1-3: Coding Agent Core** (P0)

**Day 1**: Architecture + Service Skeleton
- Create `app/services/coding_agent_service.py`
- Schema definitions (`CodingRequest`, `CodeArtifact`, `GenerationResult`)
- API endpoint: `POST /api/v1/codegen/code`
- Integration with `feature_list.json` from Initializer Agent

**Day 2**: Iterative Generation Loop
- Feature-by-feature iteration logic
- Template system (Django models + React components)
- Context cache integration (L1 Redis + L2 Anthropic)
- Progress tracking (store intermediate results)

**Day 3**: Auto-Correction Mechanism
- Retry logic (max 3 attempts per feature)
- Error parsing from Semgrep + pytest
- Context injection for fixes
- Exponential backoff between retries

---

### **Days 4-5: Gate G2 — Coding Review** (P0)

**Day 4**: OPA Policy + Semgrep Integration
- OPA policy: `g2_coding_review.rego`
- Semgrep SAST scan integration
- Rules: security (OWASP), code quality, Django/React patterns
- Evidence storage (Semgrep JSON + OPA decision)

**Day 5**: Gate G2 Integration + Testing
- `compute_gate_actions()` integration
- Gate state transitions (pending → pass/fail)
- Unit tests for policy evaluation
- False positive rate validation (sample 20 features)

---

### **Days 6-7: Gate G3 — Testing** (P0)

**Day 6**: Pytest Coverage Enforcement
- OPA policy: `g3_testing.rego`
- pytest execution wrapper
- Coverage threshold: 80%+ (configurable)
- Test generation templates (model tests + API tests)

**Day 7**: Gate G3 Integration + Playwright
- E2E test generation (React component tests)
- Playwright template integration
- Gate state transitions
- Coverage report storage (Evidence Vault)

---

### **Days 8-9: Browser Agent E2E Validation** (P0 + P1)

**Day 8**: Browser Agent Loop Enhancement
- Dev server management (subprocess)
- Playwright execution in headless mode
- Screenshot-on-failure enhancement
- Evidence capture (screenshots + HTML + console logs)

**Day 9**: Django + React Code Templates
- Django model template (with migrations)
- Django REST API template (serializers + views)
- React component template (with hooks)
- Test templates (80%+ coverage patterns)

---

### **Day 10: Integration + Verification** (P0)

- End-to-end workflow testing (`spec.yaml → deployed code`)
- Regression testing (all existing tests)
- CLI enhancement: `sdlcctl codegen run --spec spec.yaml`
- Integration tests: 10 sample features (CRUD, dashboards, forms)
- Documentation: CLAUDE.md module zone update

---

## Key Deliverables (15 Files)

### **Backend Services** (5 new files)
1. `app/services/coding_agent_service.py` — Iterative code generation loop
2. `app/schemas/codegen.py` — Extended schemas (CodingRequest, CodeArtifact, GenerationResult)
3. `app/api/v1/endpoints/codegen.py` — Extended with POST `/api/v1/codegen/code`
4. `app/services/auto_correction_service.py` — Retry logic + error parsing
5. `app/services/template_service.py` — Django + React code templates

### **OPA Policies** (2 new files)
6. `policy-packs/rego/gates/g2_coding_review.rego` — Code quality + SAST
7. `policy-packs/rego/gates/g3_testing.rego` — Test coverage enforcement

### **Code Templates** (4 new files)
8. `backend/app/templates/codegen/django_model.py.j2` — Django model template
9. `backend/app/templates/codegen/django_api.py.j2` — DRF API template
10. `backend/app/templates/codegen/react_component.tsx.j2` — React component
11. `backend/app/templates/codegen/test_suite.py.j2` — Pytest template

### **Tests** (3 new files)
12. `tests/unit/test_coding_agent.py` — Unit tests for Coding Agent
13. `tests/unit/test_auto_correction.py` — Auto-correction logic tests
14. `tests/integration/test_gates_g2_g3.py` — Gate G2/G3 integration tests

### **CLI** (1 modified file)
15. `backend/sdlcctl/commands/codegen.py` — Extended with `codegen run` command

---

## Gate Policies

### **Gate G2: Coding Review**

**OPA Policy**: `g2_coding_review.rego`

**Evaluation Criteria**:
```rego
# PASS if ALL conditions met:
- Semgrep SAST: 0 high/critical issues
- Code quality: Pylint score >7.0 (Python) / ESLint 0 errors (TypeScript)
- Django patterns: Models follow naming conventions, migrations present
- React patterns: Components use hooks, no deprecated lifecycle methods
- Evidence stored: Semgrep JSON report + code diff

# FAIL → Auto-correction triggered (max 3 retries)
```

**Evidence Required**:
- Generated code files (`.py`, `.tsx`)
- Semgrep SAST report (JSON)
- Pylint/ESLint output
- Code diff from previous iteration (for retries)

---

### **Gate G3: Testing**

**OPA Policy**: `g3_testing.rego`

**Evaluation Criteria**:
```rego
# PASS if ALL conditions met:
- pytest coverage: ≥80% (line coverage)
- All tests passing: exit code 0
- E2E Playwright tests: ≥1 test per feature
- Test quality: No empty test bodies, proper assertions
- Evidence stored: pytest coverage report + Playwright screenshots

# FAIL → Auto-correction triggered (max 3 retries)
```

**Evidence Required**:
- pytest coverage report (XML + HTML)
- Test files (`.py`, `.spec.ts`)
- Playwright screenshots (on failure)
- Test execution logs

---

## Auto-Correction Loop

**Trigger**: Gate G2 or G3 fails
**Max Retries**: 3 attempts
**Strategy**: Exponential backoff (5s, 10s, 20s between retries)

**Auto-Correction Process**:
```
Attempt 1: Generate code
  ↓
Gate G2: FAIL (Semgrep: SQL injection found)
  ↓
Retry 1: Include Semgrep error in context → regenerate
  ↓
Gate G2: PASS
  ↓
Gate G3: FAIL (Coverage 65%, target 80%)
  ↓
Retry 1: Include coverage gaps in context → regenerate tests
  ↓
Gate G3: PASS
  ↓ 
SUCCESS: Move to next feature
```

**Failure After 3 Retries**:
- Store partial results + error evidence
- Mark feature as "requires_manual_intervention"
- Continue with remaining features
- Generate summary report for human review

---

## Integration Points

### **Sprint 176 Dependencies**
- Initializer Agent service → `feature_list.json`
- Gate G1 (Spec Review) → must pass before Sprint 177 workflow
- Browser Agent v2 → reuse for E2E validation
- Evidence Vault → store all gate artifacts

### **Sprint 174 Dependencies**
- Context cache service (L1 + L2) → reduce token costs in iterations
- MCP client service → optional LLM provider abstraction
- CLAUDE.md PRO tier → prompt engineering patterns

### **Sprint 173 Dependencies**
- Gate state machine → `compute_gate_actions()` for G2/G3
- Evidence model → store Semgrep/pytest reports
- OPA service → policy evaluation for gates

---

## Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Low code generation success rate (<60%) | High | Extensive template testing, fallback to simpler patterns |
| High false positive rate (>5%) Gate G2 | Medium | Manual review sample, tune Semgrep rules |
| Auto-correction doesn't improve (retries fail) | Medium | Max 3 retries, manual intervention queue |
| Browser Agent flakiness in headless mode | Medium | Retry logic, screenshot evidence, timeout tuning |
| Context cache misses (>30%) | Low | Cache key optimization, L1 Redis + L2 Anthropic |

---

## Testing Strategy

### **Unit Tests** (50+ tests)
- Coding Agent service (iteration logic)
- Auto-correction mechanism (retry logic)
- Template rendering (Jinja2)
- OPA policy evaluation (G2/G3)

### **Integration Tests** (20+ tests)
- Full workflow: `feature_list.json` → generated code → tests pass
- Gate transitions (pending → pass → fail → retry)
- Evidence storage (Semgrep + pytest reports)
- Browser Agent E2E validation

### **E2E Tests** (10 sample features)
- User CRUD (Django model + React list/detail)
- Dashboard with charts (aggregations + React components)
- Form with validation (serializers + React form)
- Authentication flow (Django auth + React login)
- File upload (storage + React dropzone)

---

## Metrics Tracking

| Metric | Sprint 177 Target | Sprint 178 Production Target |
|--------|-------------------|------------------------------|
| Code generation success (1st attempt) | >60% | >75% |
| Auto-correction success (3 retries) | >85% | >90% |
| Gate G2 pass rate | >55% | >70% |
| Gate G3 pass rate | >50% | >65% |
| False positive rate | <5% | <3% |
| E2E validation pass rate | >95% | >98% |
| End-to-end workflow time | <10 min | <8 min |

---

## Documentation Updates

### **CLAUDE.md Module Zone**
Add Coding Agent + Gates G2/G3 modules:
```markdown
## Module Zone (continued)

### Coding Agent (Sprint 177)
**Purpose**: Iterative code generation with auto-correction loop
**State**: PRODUCTION (Sprint 177)
**Prompt Pattern**: Feature-based generation with gate feedback
**Integration**: `feature_list.json` → Django/React templates

### Gate G2: Coding Review (Sprint 177)
**Policy**: g2_coding_review.rego
**Criteria**: Semgrep SAST + code quality (Pylint/ESLint)
**Auto-correction**: Max 3 retries with context injection

### Gate G3: Testing (Sprint 177)
**Policy**: g3_testing.rego  
**Criteria**: pytest coverage ≥80% + E2E Playwright tests
**Auto-correction**: Test generation with coverage gaps feedback
```

### **ADR-055 Updates**
- Implementation status: Phase 2 COMPLETE
- Actual metrics vs. targets
- Lessons learned (auto-correction patterns)

---

## Definition of Done

- [ ] Coding Agent service deployed and tested
- [ ] Gates G2/G3 integrated with gate state machine
- [ ] Auto-correction loop tested with 10 failure scenarios
- [ ] Django + React templates generate 80%+ test coverage
- [ ] Browser Agent E2E validation passing on 10 sample features
- [ ] All existing tests passing (0 regressions)
- [ ] CLI `sdlcctl codegen run --spec spec.yaml` functional
- [ ] End-to-end workflow <10 min for 5-feature spec
- [ ] Documentation updated (CLAUDE.md, ADR-055)
- [ ] Sprint completion report created

---

## Sprint Retrospective Prep

**Key Questions**:
1. What was the actual code generation success rate? (target >60%)
2. Did auto-correction improve outcomes? (target >85% after retries)
3. What were the most common G2/G3 failures?
4. How reliable was Browser Agent in headless mode? (target >95%)
5. What emerging patterns should inform Sprint 178?

---

## Handoff to Sprint 178

**Critical Deliverables for Pilot**:
- Working end-to-end codegen workflow
- Django + React templates with 80%+ coverage
- Gates G2/G3 enforcing quality standards
- Evidence Vault with all gate artifacts

**Sprint 178 Will Add**:
- Gate G4 (Deployment) for staging/production
- Vietnamese SME pilot onboarding (5 customers)
- Production monitoring + observability
- Mobile responsive for Sprint 175 pages

---

## Refs

- **ADR-055**: Autonomous Codegen with 4-Gate Validation (558 lines)
- **Framework**: 03-AI-GOVERNANCE/11-AUTONOMOUS-CODEGEN-PATTERNS.md
- **Sprint 176**: Initializer Agent + Gate G1 (COMPLETE)
- **Sprint 173**: Gate state machine (`compute_gate_actions()`)
- **Sprint 174**: Context cache service (8x cost reduction)
- **SDLC**: 6.0.6 (7-Pillar + AI Governance)

---

**Status**: PLANNED  
**Next Sprint**: [Sprint 178 — Autonomous Codegen Pilot](SPRINT-178-AUTONOMOUS-CODEGEN-PILOT.md)  
**Execution Start**: March 31, 2026
