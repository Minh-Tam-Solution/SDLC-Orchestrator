# Current Sprint: Sprint 202 — Automated Evals Framework + Context Engineering Depth

**Sprint Duration**: April 21 – May 2, 2026 (10 working days)
**Sprint Goal**: Implement LLM-as-Judge eval framework for agent governance responses + structured agent notes for cross-session memory
**Status**: CLOSED — Track A ✅, Track B ✅, Track C ✅, Track D ✅
**Priority**: P0 (Anthropic Best Practices Gap 5 — Evals)
**Framework**: SDLC 6.1.1
**CTO Score (Sprint 201)**: 9.3/10
**Previous Sprint**: [Sprint 201 — Self-Hosted Pilot](SPRINT-201-SELF-HOSTED-PILOT.md)
**Detailed Plan**: [SPRINT-202-AUTOMATED-EVALS-CONTEXT-ENGINEERING.md](SPRINT-202-AUTOMATED-EVALS-CONTEXT-ENGINEERING.md)

---

## Sprint 202 Goal

Sprint 201 achieved 100% dogfooding. Sprint 202 closes Anthropic Best Practices Gap 5 (Evals) and deepens context engineering (structured agent notes for cross-session memory).

**Two pillars**:
1. **Automated Evals** — LLM-as-Judge scoring framework with YAML test cases and regression detection
2. **Context Engineering** — Structured agent notes (save_note/recall_note) persisted across sessions

---

## Sprint 202 Backlog

### Track A — Automated Eval Framework ✅

| ID | Item | Priority | Status |
|----|------|----------|--------|
| A-01 | EvalRubric schema (correctness/completeness/safety 0-10) | P0 | ✅ DONE |
| A-02 | EvalScorer service (LLM-as-Judge via deepseek-r1:32b) | P0 | ✅ DONE |
| A-03 | 5 YAML eval test cases (governance commands) | P0 | ✅ DONE |
| A-04 | EvalSuiteResult aggregation + regression detection | P0 | ✅ DONE |

**New files**:
- `backend/app/schemas/eval_rubric.py` (~140 LOC) — EvalRubric, EvalTestCase, EvalRunResult, EvalSuiteResult
- `backend/app/services/agent_team/eval_scorer.py` (~290 LOC) — EvalScorer with YAML loading, JSON parsing, `<think>` tag handling, regex fallback
- `backend/tests/evals/cases/eval_gate_status.yaml` — Gate status query eval case
- `backend/tests/evals/cases/eval_approve_gate.yaml` — Gate approval eval case
- `backend/tests/evals/cases/eval_create_project.yaml` — Project creation eval case
- `backend/tests/evals/cases/eval_submit_evidence.yaml` — Evidence submission eval case
- `backend/tests/evals/cases/eval_export_audit.yaml` — Audit export eval case
- `backend/tests/evals/conftest.py` (~70 LOC) — Shared fixtures (mock OllamaService, EvalScorer, rubrics)

### Track B — Context Engineering (Structured Agent Notes) ✅

| ID | Item | Priority | Status |
|----|------|----------|--------|
| B-01 | AgentNote model + Alembic migration | P0 | ✅ DONE |
| B-02 | NoteService (UPSERT, recall, list, format_for_context) | P0 | ✅ DONE |
| B-03 | Notes injected in team_orchestrator `_build_llm_context()` | P0 | ✅ DONE |
| B-04 | Tool context constants (SPAWN_TOOLS, NOTE_TOOLS, INTERNAL_TOOLS) | P1 | ✅ DONE |

**New files**:
- `backend/app/models/agent_note.py` (~65 LOC) — UUID PK, agent_id FK, conversation_id FK, key/value/note_type, UNIQUE(agent_id, key)
- `backend/app/services/agent_team/note_service.py` (~200 LOC) — UPSERT pattern, MAX_NOTES_PER_AGENT=50, TTL pruning, format_notes_for_context()
- `backend/alembic/versions/s202_001_agent_notes.py` (~65 LOC) — Creates agent_notes table with UUID columns, FKs, indexes

**Modified files**:
- `backend/app/services/agent_team/team_orchestrator.py` — NoteService import + notes injection in `_build_llm_context()` (try/except guarded)
- `backend/app/services/agent_team/tool_context.py` — Added SPAWN_TOOLS, NOTE_TOOLS, INTERNAL_TOOLS frozensets

### Track C — OTT Integration (run_evals + list_notes) ✅

| ID | Item | Priority | Status |
|----|------|----------|--------|
| C-01 | Register `run_evals` command (slot 9/10) | P0 | ✅ DONE |
| C-02 | Register `list_notes` command (slot 10/10) | P0 | ✅ DONE |
| C-03 | Evidence collector: `capture_eval_report()` method | P0 | ✅ DONE |

**Modified files**:
- `backend/app/services/agent_team/command_registry.py` — +2 commands, +2 Pydantic models (RunEvalsParams, ListNotesParams), ToolName enum expanded, 8→10 commands (MAX_COMMANDS reached)
- `backend/app/services/agent_team/evidence_collector.py` — +`capture_eval_report()` method for EVAL_REPORT evidence type

### Track D — Tests + Sprint Close ✅

| ID | Item | Priority | Status |
|----|------|----------|--------|
| D-01 | Sprint 202 test suite (50 tests across 10 classes) | P0 | ✅ DONE |
| D-02 | Full regression suite (0 Sprint 202 regressions) | P0 | ✅ DONE |
| D-03 | CURRENT-SPRINT.md + SPRINT-INDEX.md updated | P0 | ✅ DONE |

**Test suite** (`test_sprint202_evals_context.py`):
- 10 test classes, 50 tests covering all 4 tracks
- EvalRubric schema (6), EvalScorer scoring (6), YAML loading (4), EvalSuiteResult (4), AgentNote model (4), NoteService CRUD (8), Notes injection (4), Command registry (4), Evidence capture (2), Tool context (2), Regression guards (6)

**Regression fixes**:
- `test_registry_has_8_commands` → `test_registry_has_10_commands` (3 test files)
- `vietnamese_keywords` list expanded (+`chạy`, +`xem`)
- OllamaResponse field alignment (`text` → `response`, field names corrected)

---

## Sprint 202 Deliverables Summary

| Track | Deliverable | LOC | Status |
|-------|------------|-----|--------|
| A | EvalRubric schema | ~140 | ✅ |
| A | EvalScorer service (LLM-as-Judge) | ~290 | ✅ |
| A | 5 YAML eval test cases | ~75 | ✅ |
| A | Eval conftest fixtures | ~70 | ✅ |
| B | AgentNote model | ~65 | ✅ |
| B | NoteService (CRUD + UPSERT) | ~200 | ✅ |
| B | Alembic migration (s202_001) | ~65 | ✅ |
| B | Orchestrator + tool_context mods | ~25 | ✅ |
| C | Command registry (+2 commands) | ~40 | ✅ |
| C | Evidence collector (eval reports) | ~55 | ✅ |
| D | Test suite (50 tests) | ~430 | ✅ |
| D | Regression fixes | ~15 | ✅ |
| **Total** | | **~1,470** | **✅** |

---

## Command Registry (10/10 — MAX_COMMANDS reached)

| Command | Sprint Added | OTT | Vietnamese | Status |
|---------|-------------|-----|------------|--------|
| `create_project` | 191 | ✅ | "tạo dự án" | ✅ |
| `get_gate_status` | 191 | ✅ | "trạng thái gate" | ✅ |
| `submit_evidence` | 191 | ✅ | "nộp bằng chứng" | ✅ |
| `request_approval` | 191 | ✅ | "duyệt" | ✅ |
| `export_audit` | 201 | ✅ | "xuất báo cáo" | ✅ |
| `update_sprint` | 194 | ✅ | "cập nhật sprint" | ✅ |
| `close_sprint` | 201 | ✅ | "đóng sprint" | ✅ |
| `invite_member` | 201 | ✅ | "mời thành viên" | ✅ |
| `run_evals` | **202** | ✅ | "chạy đánh giá" | ✅ NEW |
| `list_notes` | **202** | ✅ | "xem ghi chú" | ✅ NEW |

---

## Test Results

```
Sprint 202 Tests:  50 passed in 0.34s
Regression Suite:  135 passed, 0 Sprint 202 regressions
(1 pre-existing failure: test_steer_mode_process_by_id — confirmed pre-Sprint 202)
Regression fixes:  command count 8→10 (3 files), Vietnamese keywords (+2), OllamaResponse fields (6 instances)
```

---

## G-Sprint-Close Gate

| Gate | Status | Date | Reviewer | Score |
|------|--------|------|----------|-------|
| G-Sprint-Close | ✅ APPROVED | 2026-02-24 | @dev-team | 8/8 hard criteria met, 50/50 Sprint 202 tests, 0 regressions |

### Carry-Forward to Next Sprint

| Item | Origin |
|---|---|
| SC-200-01: `source="chat"` audit log field | Sprint 199 deferred |
| MAX_COMMANDS=10 reached — consider dynamic routing | Sprint 202 observation |
| eval_results DB table (persistent eval storage) | Sprint 202 stretch goal |
| Eval evidence auto-capture in run_suite flow | Sprint 202 stretch goal |

---

**Updated By**: @dev-team via Claude Code
**Next Sprint**: [Sprint 203 — Evaluator-Optimizer + Evals Expansion](SPRINT-203-EVALUATOR-OPTIMIZER-EVALS-EXPANSION.md)
