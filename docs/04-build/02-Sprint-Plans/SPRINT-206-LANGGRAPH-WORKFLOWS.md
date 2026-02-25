---
sdlc_version: "6.1.1"
document_type: "Sprint Plan"
status: "PROPOSED"
sprint: "206"
spec_id: "SP-206"
tier: "PROFESSIONAL"
stage: "04 - Build"
---

# Sprint 206 — LangGraph Durable Workflows

| Field | Value |
|-------|-------|
| **Sprint** | 206 |
| **Duration** | 5 working days |
| **Goal** | Add LangGraph durable async workflows for reflection loops with crash recovery |
| **ADR** | ADR-066 (D-066-02 through D-066-06) |
| **FR** | FR-046 (LangGraph Reflection Workflow) |
| **LOC** | ~1,200 |
| **Risk** | MEDIUM (new Docker service, async resume architecture) |
| **Dependencies** | Sprint 205 complete, `langgraph>=0.2.0` in enterprise.txt |

---

## 1. Sprint Goal

Add LangGraph durable async workflow graphs for reflection loops (Coder <-> Reviewer). Workflows survive crashes via Postgres checkpoint in `agent_conversations.metadata_` JSONB. WorkflowResumer runs as a separate Docker service with dual-path resume (pub/sub fast + reconciler fallback). End-to-end idempotency at 3 layers.

---

## 2. Current State → Target State

| Aspect | Current (Sprint 205) | Target (Sprint 206) |
|--------|---------------------|---------------------|
| Workflow orchestration | Manual in team_orchestrator | LangGraph StateGraph |
| Crash recovery | None (restart = lost state) | Postgres checkpoint in metadata_ JSONB |
| Reflection loop | Not possible | Coder -> Reviewer -> Retry (max 3) |
| Workflow resume | N/A | WorkflowResumer (pub/sub + reconciler) |
| Idempotency | Message-level dedupe only | 3-layer: workflow + message + control plane |

---

## 3. Architecture

```
NEW SERVICE:
  workflow_resumer (Docker, replicas: 1)
    ├── Redis pub/sub listener (fast path)
    ├── Reconciler polling 30s (fallback)
    └── Stuck detection (>5min waiting → auto-resume)

NEW FILES:
  workflows/__init__.py
  workflows/graph_state.py       # ReflectionState, WorkflowMetadata Pydantic
  workflows/reflection_graph.py  # async StateGraph, max 3 iterations
  workflow_resumer.py            # pub/sub + reconciler, OCC
  routes/workflows.py            # POST /reflection, GET /status, POST /approve

MODIFIED FILES:
  team_orchestrator.py           # enqueue_async() (non-blocking)
  main.py                        # register workflows router
  docker-compose.yml             # workflow_resumer service

MIGRATION:
  Alembic: partial index on metadata_ JSONB
```

---

## 4. Backlog

### Track A: JSONB Schema + Migration (Day 1)

| # | Task | File | LOC | Day |
|---|------|------|-----|-----|
| A1 | Create `workflows/graph_state.py` — WorkflowMetadata Pydantic model | new | ~60 | 1 |
| A2 | Create `workflows/__init__.py` | new | ~5 | 1 |
| A3 | Create Alembic migration — partial index on metadata_ JSONB | new | ~30 | 1 |
| A4 | 64KB size validation before JSONB write | `graph_state.py` | incl | 1 |
| A5 | OCC version field increment logic | `graph_state.py` | incl | 1 |

### Track B: Reflection Graph (Day 2-3)

| # | Task | File | LOC | Day |
|---|------|------|-----|-----|
| B1 | Create `workflows/reflection_graph.py` — async StateGraph | new | ~200 | 2 |
| B2 | Coder node + Reviewer node + Decision node | `reflection_graph.py` | incl | 2 |
| B3 | Max 3 iterations with configurable limit | `reflection_graph.py` | incl | 2 |
| B4 | Add `enqueue_async()` to `team_orchestrator.py` | modified | ~30 | 3 |
| B5 | Control plane refresh at decision node (GET /gates/{id}/actions) | `reflection_graph.py` | incl | 3 |

### Track C: WorkflowResumer (Day 3-4)

| # | Task | File | LOC | Day |
|---|------|------|-----|-----|
| C1 | Create `workflow_resumer.py` — pub/sub listener (fast path) | new | ~200 | 3 |
| C2 | Reconciler polling (30s fallback) | `workflow_resumer.py` | incl | 3 |
| C3 | Stuck detection (>5min waiting → auto-resume) | `workflow_resumer.py` | incl | 4 |
| C4 | OCC: concurrent resume → 1 pass, 1 no-op | `workflow_resumer.py` | incl | 4 |
| C5 | Add workflow_resumer service to `docker-compose.yml` | modified | ~10 | 4 |

### Track D: API + Idempotency (Day 4)

| # | Task | File | LOC | Day |
|---|------|------|-----|-----|
| D1 | Create `routes/workflows.py` — 3 endpoints | new | ~120 | 4 |
| D2 | Register workflows router in `main.py` | modified | ~5 | 4 |
| D3 | Workflow step idempotency (workflow_id, step_id) | `reflection_graph.py` | incl | 4 |
| D4 | Message enqueue idempotency_key param | `team_orchestrator.py` | incl | 4 |
| D5 | X-Idempotency-Key header on control plane routes | `routes/workflows.py` | incl | 4 |

### Track E: Tests + Verification (Day 5)

| # | Task | File | LOC | Day |
|---|------|------|-----|-----|
| E1 | Write `test_reflection_graph.py` (7 test cases: RG-01 to RG-07) | new | ~175 | 5 |
| E2 | Write `test_workflow_resumer.py` (5 test cases: WR-01 to WR-05) | new | ~175 | 5 |
| E3 | Write idempotency tests (3 test cases: ID-01 to ID-03) | new | incl | 5 |
| E4 | Write control plane tests (2 test cases: CP-01 to CP-02) | new | incl | 5 |
| E5 | Regression: all existing tests pass | — | — | 5 |
| E6 | Crash recovery test: start workflow → kill resumer → restart → verify | manual | — | 5 |

---

## 5. Implementation Checklist (20 items from CTO review)

### JSONB Schema (5)
- [ ] WorkflowMetadata Pydantic model with OCC version
- [ ] next_wakeup_at for reconciler query
- [ ] Partial index on (status, next_wakeup_at)
- [ ] 64KB size validation before write
- [ ] Pydantic validation on all metadata_ reads/writes

### WorkflowResumer (5)
- [ ] Separate Docker service (NOT in main.py)
- [ ] Pub/sub listener (fast path)
- [ ] Reconciler polling 30s (fallback)
- [ ] Leader election OR replicas:1
- [ ] Stuck detection (>5min waiting → auto-resume)

### Idempotency (4)
- [ ] idempotency_keys in WorkflowMetadata
- [ ] idempotency_key param in enqueue_async()
- [ ] X-Idempotency-Key header on control plane routes
- [ ] IdempotencyStore (Redis, 1hr TTL)

### Authorization (2)
- [ ] authorize_tool_call() covers all LangChain tools
- [ ] Test: call without auth → PermissionDenied

### Observability (2)
- [ ] correlation_id through all workflow logs
- [ ] Log 6 fields: workflow_id, step, project_id, lane_id, idempotency_key, provider_profile_key

### Tests (2)
- [ ] Event-missed test (reconciler resumes without pub/sub)
- [ ] OCC test (concurrent resume → 1 pass, 1 no-op)

---

## 6. Verification Commands

```bash
# Reflection graph unit tests
python -m pytest backend/tests/unit/test_reflection_graph.py -v

# WorkflowResumer unit tests
python -m pytest backend/tests/unit/test_workflow_resumer.py -v

# Idempotency tests
python -m pytest backend/tests/unit/ -k "idempotency" -v

# All Sprint 206 tests
python -m pytest backend/tests/unit/ -k "reflection or resumer or idempotency or workflow" -v

# Regression: all existing tests pass
DATABASE_URL="postgresql://test:test@localhost:15432/sdlc_test" \
  python -m pytest backend/tests/ -v --tb=short

# Crash recovery (manual)
# 1. Start workflow: POST /api/v1/workflows/reflection
# 2. Kill resumer: docker stop workflow_resumer
# 3. Restart resumer: docker start workflow_resumer
# 4. Verify: GET /api/v1/workflows/{id}/status → resumed from checkpoint
```

---

## 7. Exit Criteria

| Criterion | Target |
|-----------|--------|
| All existing tests pass (regression) | 691/691 (676 + 15 Sprint 205) |
| RG-01 to RG-07 pass | 7/7 |
| WR-01 to WR-05 pass | 5/5 |
| ID-01 to ID-03 pass | 3/3 |
| CP-01 to CP-02 pass | 2/2 |
| Crash recovery verified | Manual test pass |
| OCC concurrent resume verified | 1 pass, 1 no-op |
| WorkflowResumer NOT in main.py | Verified |
| Zero P0 security bugs | 0 |

---

## 8. Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| LangGraph 0.2.x API instability | MEDIUM | MEDIUM | Pin version, monitor changelog |
| WorkflowResumer crash loop | LOW | HIGH | Health check + auto-restart in Docker |
| Pub/sub event loss under load | MEDIUM | LOW | Reconciler polling as durable fallback |
| JSONB 64KB limit exceeded | LOW | MEDIUM | Store pointers not payloads, validate before write |
| Alembic migration conflict | LOW | LOW | Coordinate with active sprint migrations |
