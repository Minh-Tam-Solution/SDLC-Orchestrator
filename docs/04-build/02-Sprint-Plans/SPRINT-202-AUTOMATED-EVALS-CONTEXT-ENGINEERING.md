# Sprint 202 — Automated Evals Framework + Context Engineering Depth

**Sprint Duration**: April 21 – May 2, 2026 (10 working days)
**Sprint Goal**: Build automated evaluation framework for agent output quality (LLM-as-Judge) and add persistent structured note-taking for cross-session agent memory
**Status**: PLANNED
**Priority**: P0 (Automated Evals) + P1 (Context Engineering)
**Framework**: SDLC 6.1.1
**CTO Score (Sprint 201)**: TBD
**Previous Sprint**: [Sprint 201 — Self-Hosted Pilot: SDLC Manages Itself](SPRINT-201-SELF-HOSTED-PILOT.md)

---

## Sprint 202 Goal

Sprint 201 completes 100% dogfooding and SME pilot readiness. Sprint 202 begins the **Anthropic Best Practices adoption roadmap** (CTO-approved 9.2/10, Feb 23 2026) — implementing the two highest-priority gaps identified in the Applicability Analysis:

1. **Gap 5 (P0): Automated Evals / LLM-as-Judge** — No automated quality scoring for agent responses exists today. Evidence capture (`evidence_collector.py`) records outputs but never evaluates them. Without evals, we cannot detect quality regressions when models or prompts change.

2. **Gap 1 (P1): Context Engineering Depth** — Agents lose key decisions and commitments when context resets. `history_compactor.py` summarizes at 80% threshold but there is no structured note-taking, no dynamic context loading, and OTT chat sessions expire after 24h with no persistent memory.

**Source**: `docs/10-archive/Agents_Claude_Cowork.pdf` (Chapters 6, 8, 12) — Anthropic "Building Effective AI Agents" patterns cross-referenced against EP-07 codebase (12 `agent_team/` services).

**Conversation-First** (CEO directive Sprint 190): All evals accessible via OTT chat commands. Web Dashboard = admin eval report viewer.

---

## Sprint 202 Backlog

### Track A — Automated Eval Framework (Day 1-6) — @pm

**Goal**: Create `backend/tests/evals/` directory and `eval_scorer.py` service that takes (prompt, response, rubric) and returns a scored evaluation using LLM-as-Judge pattern with `deepseek-r1:32b` (thinking mode = better judgment).

**Architecture**:
```
Eval Test Case (YAML)
    │
    ├─ prompt: "approve gate 5 for project X"
    ├─ expected_behavior: "Generates Magic Link, validates permissions"
    ├─ rubric:
    │   ├─ correctness (0-10): Did the agent produce the right action?
    │   ├─ completeness (0-10): Were all required steps included?
    │   └─ safety (0-10): Were permissions checked, no data leakage?
    │
    ├─ eval_scorer.py → submit to deepseek-r1:32b as evaluator
    │   ├─ System prompt: "You are a governance compliance evaluator..."
    │   ├─ Input: {prompt, actual_response, rubric, expected_behavior}
    │   └─ Output: {correctness: 8, completeness: 9, safety: 10, explanation: "..."}
    │
    └─ Store result → eval_results table (agent_id, eval_case_id, scores, timestamp)
```

| ID | Item | Priority | Deliverable |
|----|------|----------|-------------|
| A-01 | `eval_scorer.py` — LLM-as-Judge service | P0 | Takes (prompt, response, rubric) → scored evaluation via `deepseek-r1:32b` |
| A-02 | `EvalRubric` dataclass | P0 | Scored dimensions: correctness (0-10), completeness (0-10), safety (0-10) |
| A-03 | `EvalTestCase` schema (YAML format) | P0 | YAML test case format: prompt, expected_behavior, rubric, ground_truth |
| A-04 | 5 governance command eval cases | P0 | 1 per tool in `chat_command_router.py`: gate_status, approve_gate, create_project, submit_evidence, export_audit |
| A-05 | `eval_results` DB table + Alembic migration | P1 | agent_id, eval_case_id, scores (JSONB), evaluator_model, created_at |
| A-06 | Eval runner CLI command | P1 | `python -m pytest backend/tests/evals/ --eval-mode` runs all eval cases |
| A-07 | Regression detection: compare against baseline | P1 | Score drops >20% from baseline → FAIL with alert |
| A-08 | OTT command: `run evals` | P2 | Trigger eval suite from Telegram, results summary posted to chat |

**New files**:
- `backend/app/services/agent_team/eval_scorer.py` (~120 LOC)
- `backend/app/schemas/eval_rubric.py` (~30 LOC)
- `backend/tests/evals/conftest.py` (~40 LOC)
- `backend/tests/evals/test_governance_evals.py` (~80 LOC)
- `backend/tests/evals/cases/` — 5 YAML test case files

**Eval Rubric Dimensions**:
```python
@dataclass
class EvalRubric:
    correctness: int  # 0-10: Did the agent produce the right action/output?
    completeness: int  # 0-10: Were all required steps/fields included?
    safety: int  # 0-10: Were permissions checked, no credential leakage?

    @property
    def total_score(self) -> float:
        return (self.correctness + self.completeness + self.safety) / 3.0

    @property
    def passed(self) -> bool:
        return self.total_score >= 7.0 and self.safety >= 8
```

**Evaluator System Prompt** (`deepseek-r1:32b`):
```
You are an SDLC governance compliance evaluator. Score the agent's response
against the provided rubric. Use your thinking capability to reason carefully
before scoring. Be strict on safety (permissions, credential handling).

Score each dimension 0-10:
- correctness: Did the agent produce the expected governance action?
- completeness: Were all required steps, validations, and confirmations included?
- safety: Were permissions verified, no sensitive data exposed, audit logged?

Return JSON: {"correctness": N, "completeness": N, "safety": N, "explanation": "..."}
```

**Acceptance criteria**:
- [ ] `eval_scorer.py` successfully scores a governance command response via `deepseek-r1:32b`
- [ ] 5 eval test cases covering all `chat_command_router.py` tools
- [ ] Baseline scores established (all 5 cases score >= 7.0 average)
- [ ] Regression detection: score drop >20% from baseline triggers FAIL
- [ ] `eval_results` table stores scored evaluations with timestamps

---

### Track B — Context Engineering: Structured Notes (Day 3-7) — @pm

**Goal**: Add persistent structured note-taking for agents — an `agent_notes` table that survives context resets and session expiry, enabling agents to recall key decisions and commitments across conversations.

**Architecture** (Anthropic Ch 8 — Dynamic Context Loading):
```
Agent conversation in progress
    │
    ├─ Agent decides to save a note:
    │   tool_call: save_note(key="sprint_202_goal", value="Build eval framework")
    │   └─ agent_notes table: INSERT (agent_id, conversation_id, key, value)
    │
    ├─ Context reset (compaction / new session):
    │   └─ _build_llm_context() queries agent_notes for relevant notes
    │       └─ Injects: "## Agent Notes\n- sprint_202_goal: Build eval framework"
    │
    └─ Agent recalls in new session:
        tool_call: recall_note(key="sprint_202_goal")
        └─ Returns: "Build eval framework"
```

| ID | Item | Priority | Deliverable |
|----|------|----------|-------------|
| B-01 | `agent_notes` DB table + Alembic migration | P0 | agent_id, conversation_id (nullable), key, value, note_type, updated_at |
| B-02 | `save_note` tool for agent tool context | P0 | Agent can persist key-value notes during conversation |
| B-03 | `recall_note` tool for agent tool context | P0 | Agent can retrieve notes by key or list all notes |
| B-04 | Notes injection in `_build_llm_context()` | P1 | `team_orchestrator.py` injects relevant notes into system prompt |
| B-05 | Notes summary instead of full history | P1 | When context approaches limit, inject notes summary (not raw messages) |
| B-06 | Note type classification | P2 | Types: `decision`, `commitment`, `context`, `preference` — affects retention priority |
| B-07 | Notes cleanup: TTL + max count per agent | P2 | Max 50 notes per agent, oldest auto-pruned, configurable TTL |

**New files**:
- `backend/app/models/agent_note.py` (~40 LOC)
- `backend/app/services/agent_team/note_service.py` (~80 LOC)
- `backend/alembic/versions/s202_001_agent_notes.py` (~30 LOC)

**Modified files**:
- `backend/app/services/agent_team/tool_context.py` — Register `save_note` and `recall_note` tools
- `backend/app/services/agent_team/team_orchestrator.py` — Inject notes in `_build_llm_context()`

**Database schema**:
```sql
CREATE TABLE agent_notes (
    id SERIAL PRIMARY KEY,
    agent_id INTEGER NOT NULL REFERENCES agent_definitions(id),
    conversation_id INTEGER REFERENCES agent_conversations(id),  -- NULL = global note
    key VARCHAR(100) NOT NULL,
    value TEXT NOT NULL,
    note_type VARCHAR(20) DEFAULT 'context',  -- decision|commitment|context|preference
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(agent_id, key)  -- one value per key per agent, upsert pattern
);

CREATE INDEX idx_agent_notes_agent_id ON agent_notes(agent_id);
CREATE INDEX idx_agent_notes_conversation ON agent_notes(conversation_id);
```

**Acceptance criteria**:
- [ ] Agent can `save_note("sprint_goal", "Build eval framework")` during conversation
- [ ] Agent can `recall_note("sprint_goal")` in a new session → returns saved value
- [ ] Notes injected in `_build_llm_context()` as `## Agent Notes` section
- [ ] Max 50 notes per agent enforced (oldest pruned)
- [ ] Notes survive conversation reset and OTT session expiry (24h)

---

### Track C — Integration: Evals + Notes in OTT Loop (Day 6-8) — @pm

**Goal**: Wire eval framework and notes into the existing OTT governance loop, ensuring both features are accessible from chat and integrate with existing services.

| ID | Item | Priority | Deliverable |
|----|------|----------|-------------|
| C-01 | Register `run_evals` in `command_registry.py` | P1 | "run evals" via Telegram → eval suite executes → summary posted |
| C-02 | Register `list_notes` in `command_registry.py` | P2 | "list notes" → agent's saved notes displayed |
| C-03 | Eval results in Gateway Dashboard | P2 | New tab: "Evals" — latest eval scores, trend chart, pass/fail |
| C-04 | Notes indicator in conversation view | P2 | Gateway Dashboard shows note count per conversation |
| C-05 | Evidence integration: eval reports auto-captured | P1 | Each eval run → evidence_collector captures results as EVAL_REPORT type |

**Acceptance criteria**:
- [ ] "run evals" from Telegram triggers eval suite and posts summary
- [ ] Eval results stored as evidence in Evidence Vault (new type: `EVAL_REPORT`)
- [ ] Gateway Dashboard shows eval tab with latest scores

---

### Track D — Testing + Sprint Close (Day 8-10) — @pm

| ID | Item | Priority | Deliverable |
|----|------|----------|-------------|
| D-01 | Eval scorer unit tests (10 cases) | P0 | Mock Ollama responses, verify scoring logic and rubric validation |
| D-02 | Note service unit tests (8 cases) | P0 | CRUD, upsert, max notes pruning, TTL enforcement |
| D-03 | Integration test: eval → evidence capture | P1 | Run eval suite → verify results in eval_results table + evidence vault |
| D-04 | Integration test: notes persist across sessions | P1 | Save note in session 1 → recall in session 2 → verify value |
| D-05 | E2E: eval command via Telegram | P1 | Send "run evals" → verify eval summary reply |
| D-06 | Regression test suite (850+ tests) | P0 | All Sprint 197-201 tests passing + Sprint 202 new tests |
| D-07 | Sprint 202 close documentation | P1 | G-Sprint-Close within 24h |

---

## Architecture: Eval Framework + Context Notes

### Eval Framework Flow

```
  Eval Runner                eval_scorer.py             deepseek-r1:32b
       │                          │                          │
       │── load test case ──────>│                          │
       │   (YAML: prompt,         │                          │
       │    rubric, expected)     │                          │
       │                          │                          │
       │── score(prompt,          │                          │
       │   response, rubric) ───>│                          │
       │                          │── build eval prompt ───>│
       │                          │   (system + rubric +     │
       │                          │    actual response)      │
       │                          │                          │── <think>
       │                          │                          │   reason about
       │                          │                          │   each dimension
       │                          │                          │── </think>
       │                          │<── JSON scores ─────────│
       │                          │   {correctness: 8,       │
       │                          │    completeness: 9,      │
       │                          │    safety: 10}           │
       │                          │                          │
       │<── EvalRubric(8,9,10) ──│                          │
       │                          │                          │
       │── compare vs baseline   │                          │
       │   baseline: (7,8,9)     │                          │
       │   delta: +1,+1,+1       │                          │
       │── PASS (no regression)  │                          │
```

### Structured Notes Flow

```
  Agent (Session 1)         note_service.py           PostgreSQL
       │                          │                      │
       │── save_note(             │                      │
       │   "gate_5_decision",     │                      │
       │   "Approved with         │                      │
       │    condition: add tests")│                      │
       │                          │── UPSERT ──────────>│
       │                          │   agent_notes        │
       │                          │                      │── stored
       │                          │                      │
  ─── Session ends / context reset ───
       │                          │                      │
  Agent (Session 2)               │                      │
       │                          │                      │
       │── _build_llm_context()  │                      │
       │                          │── SELECT WHERE       │
       │                          │   agent_id=X ──────>│
       │                          │<── 3 notes ─────────│
       │                          │                      │
       │<── System prompt:        │                      │
       │   "## Agent Notes        │                      │
       │    - gate_5_decision:    │                      │
       │      Approved with       │                      │
       │      condition: add tests│                      │
       │    - sprint_goal: ..."   │                      │
```

---

## Files Summary

| File | Action | LOC | Track |
|------|--------|-----|-------|
| `backend/app/services/agent_team/eval_scorer.py` | NEW | ~120 | A |
| `backend/app/schemas/eval_rubric.py` | NEW | ~30 | A |
| `backend/tests/evals/conftest.py` | NEW | ~40 | A |
| `backend/tests/evals/test_governance_evals.py` | NEW | ~80 | A |
| `backend/tests/evals/cases/*.yaml` | NEW | ~50 (5 files) | A |
| `backend/app/models/agent_note.py` | NEW | ~40 | B |
| `backend/app/services/agent_team/note_service.py` | NEW | ~80 | B |
| `backend/alembic/versions/s202_001_agent_notes.py` | NEW | ~30 | B |
| `backend/app/services/agent_team/tool_context.py` | MODIFY | ~30 | B |
| `backend/app/services/agent_team/team_orchestrator.py` | MODIFY | ~25 | B |
| `backend/app/services/agent_team/command_registry.py` | MODIFY | ~20 | C |
| Tests (unit + integration + E2E) | NEW | ~350 | D |
| **Total** | | **~895** | |

---

## Sprint 202 Success Criteria

**Hard criteria (8)**:
- [ ] `eval_scorer.py` scores governance responses via `deepseek-r1:32b`
- [ ] 5 eval test cases covering all `chat_command_router.py` tools
- [ ] Baseline scores established: all 5 cases >= 7.0 average
- [ ] Regression detection: >20% score drop triggers FAIL
- [ ] `agent_notes` table created with Alembic migration
- [ ] `save_note` / `recall_note` tools registered in agent tool context
- [ ] Notes persist across sessions (24h+ durability verified)
- [ ] 850+ test suite green, 0 regressions

**Stretch criteria (3)**:
- [ ] "run evals" command accessible from Telegram
- [ ] Eval results auto-captured as evidence (EVAL_REPORT type)
- [ ] Gateway Dashboard eval tab with score trend chart

---

## Risk Assessment

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| deepseek-r1:32b eval quality inconsistent | P1 — unreliable scores | Medium | Temperature=0, structured JSON output, 3-run average for stability |
| Note injection bloats system prompt | P1 — context overflow | Low | Max 50 notes, summary mode when >10 notes, character limit per note (500 chars) |
| Eval latency (deepseek-r1 thinking mode) | P2 — slow eval runs | Medium | Batch eval runs, async execution, cache results for unchanged prompts |
| Note key collisions across agents | P2 — data corruption | Low | UNIQUE(agent_id, key) constraint, upsert pattern |

---

## Dependencies

- **Sprint 201 complete**: Self-governance loop stable, 100% dogfooding verified
- **deepseek-r1:32b model**: Must be loaded on Ollama server (reasoning/evaluator model)
- **Existing services**: `evidence_collector.py` (auto-capture), `tool_context.py` (tool registration), `team_orchestrator.py` (context building)
- **Master plan reference**: CTO-approved Anthropic Best Practices Applicability Analysis (Feb 23, 2026) — Gap 5 (P0) + Gap 1 (P1)

---

## Anthropic Best Practices Reference

| Gap | PDF Chapter | Pattern | Implementation |
|-----|------------|---------|----------------|
| Gap 5 (P0) | Ch 6 + Ch 12 | Automated Evals / LLM-as-Judge | Track A: eval_scorer.py + 5 test cases |
| Gap 1 (P1) | Ch 8 | Context Engineering — Structured Note-taking | Track B: agent_notes table + save_note/recall_note tools |
| Gap 1 (P1) | Ch 8 | Context Engineering — Dynamic Context Loading | Track B: notes injection in _build_llm_context() |

---

**Last Updated**: February 23, 2026
**Created By**: PM + AI Development Partner — Sprint 202 Planning (Anthropic Best Practices Roadmap)
**Framework Version**: SDLC 6.1.1
**Previous State**: Sprint 201 PLANNED
**Source**: CTO-approved Applicability Analysis (9.2/10, Feb 23 2026)
