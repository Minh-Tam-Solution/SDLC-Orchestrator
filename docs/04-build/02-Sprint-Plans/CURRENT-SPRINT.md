# Current Sprint: Sprint 208 — Pre-Release Hardening

**Sprint Duration**: Feb 26, 2026 (1 working day)
**Sprint Goal**: Fix P0 tier gate bypass (TG-41), clean dead code, implement 3 overdue stub commands, register WorkflowResumer in lifespan
**Status**: CLOSED — PM APPROVED ✅ (Feb 26, 2026)
**Priority**: P0 (Release blocker) + P1 (Tech debt)
**Framework**: SDLC 6.1.1
**CTO Score (Sprint 207)**: Pending (Trend: 200→9.2 | 201→9.3 | 202→9.4 | 203→9.5 ↑)
**Previous Sprint**: [Sprint 207 — OTT Workspace Context Management](SPRINT-207-OTT-WORKSPACE.md)
**Detailed Plan**: [SPRINT-208-RELEASE-HARDENING.md](SPRINT-208-RELEASE-HARDENING.md)
**Release Target**: v1.1.0 — Post-GA Hardening

---

## Sprint 208 Goal

Sprint 207 closed the OTT Workspace feature. Full codebase review (PM + Architect) identified 1 P0 blocker and several P1 hygiene items that must be addressed before the next release.

**P0 Blocker**: TG-41 Tier Gate bypass — `/api/v1/magic-link` and `/api/v1/workflows` skip tier enforcement.
**P1 Hygiene**: 3 stub commands (8 sprints overdue), 3 dead code modules.
**P2 Structural**: WorkflowResumer not registered in lifespan.

---

## Sprint 208 Backlog

### Track A — P0: TG-41 Tier Gate Fix ✅

| ID | Item | Status |
|----|------|--------|
| A1 | Add `/api/v1/magic-link` to `ROUTE_TIER_TABLE` — tier STANDARD (2) | ✅ DONE |
| A2 | Add `/api/v1/workflows` to `ROUTE_TIER_TABLE` — tier PROFESSIONAL (3) | ✅ DONE |

**Modified files**: `tier_gate.py` (+2 entries)

### Track B — P1: Dead Code Cleanup ✅

| ID | Item | Status |
|----|------|--------|
| B1 | Delete `billing/` directory (empty, only `__pycache__`) | ✅ DONE |
| B2 | Delete `infrastructure/__init__.py` (broken import to non-existent `minio_service.py`) | ✅ DONE |
| B3 | Delete `browser_agent_service.py` (0 references in codebase) | ✅ DONE |

**Deleted files**: 3 files/dirs (~9.7 KB dead code removed)

### Track C — P1: Implement 3 Stub OTT Commands ✅

| ID | Item | Status |
|----|------|--------|
| C1 | `create_project` — direct async ORM (RF-01: project_service is sync) | ✅ DONE |
| C2 | `submit_evidence` — direct GateEvidence ORM (RF-02: no evidence_service) | ✅ DONE |
| C3 | `update_sprint` — delegate to `handle_update_sprint(db, project_id)` | ✅ DONE |

**Modified files**: `governance_action_handler.py` (+~280 LOC, 3 new async functions)

### Track D — P2: WorkflowResumer Lifespan Registration ✅

| ID | Item | Status |
|----|------|--------|
| D1 | Conditional `WorkflowResumer.start()`/`stop()` in `main.py` lifespan | ✅ DONE |

**Modified files**: `main.py` (+~15 LOC, LANGGRAPH_ENABLED guard)

### Track E — Tests + Regression Guard ✅

| ID | Item | Status |
|----|------|--------|
| E1-E8 | 8 new tests in `test_sprint208_hardening.py` | ✅ 8/8 PASSED |
| E9 | Sprint 200-208 regression guard (310 tests) | ✅ 310/310 PASSED |

**New files**: `test_sprint208_hardening.py` (8 tests)

---

## Definition of Done — Sprint 208

- [x] `/api/v1/magic-link` → tier STANDARD (2) in `ROUTE_TIER_TABLE`
- [x] `/api/v1/workflows` → tier PROFESSIONAL (3) in `ROUTE_TIER_TABLE`
- [x] `billing/` directory deleted
- [x] `infrastructure/__init__.py` deleted
- [x] `browser_agent_service.py` deleted
- [x] `create_project` command — real async ORM implementation (RF-01)
- [x] `submit_evidence` command — real GateEvidence ORM implementation (RF-02)
- [x] `update_sprint` command — wired to sprint_command_handler
- [x] WorkflowResumer conditionally started in lifespan (`LANGGRAPH_ENABLED=true`)
- [x] 8/8 Sprint 208 tests passing
- [x] 310 regression guards passing | 0 regressions
- [x] CURRENT-SPRINT.md updated to Sprint 208

---

## Sprint 208 Close Summary

**Status**: CLOSED — PM APPROVED ✅ (Feb 26, 2026)
**Tests**: 8 new tests | 310 regression guards passing | 0 regressions
**Modified files**: `tier_gate.py` (+2 entries), `governance_action_handler.py` (+~280 LOC), `main.py` (+~15 LOC)
**Deleted files**: `billing/` (empty dir), `infrastructure/__init__.py` (broken import), `browser_agent_service.py` (0 refs)
**New files**: `test_sprint208_hardening.py` (8 tests)

**Key deliverables**:
- TG-41 P0 fix: `/api/v1/magic-link` (tier 2) + `/api/v1/workflows` (tier 3) now gated
- 3 stub commands replaced with real implementations: `create_project` (async ORM), `submit_evidence` (GateEvidence ORM), `update_sprint` (sprint_command_handler delegate)
- CTO RF-01/RF-02 applied: direct async ORM instead of sync project_service, GateEvidence direct ORM instead of non-existent evidence_service
- Dead code: 3 files/dirs removed (~9.7 KB)
- WorkflowResumer conditionally starts in lifespan when `LANGGRAPH_ENABLED=true`
- All 10 command registry slots now have real implementations (0 stubs remaining)

---

## Sprint 207 Close Summary

**Status**: CLOSED — PM APPROVED ✅ (Feb 26, 2026)
**CTO Score**: Pending (Quality Scorecard: Zero Mock 10/10, Type Hints 10/10, AGPL 10/10, Error Handling 9/10, Security 10/10, Testing 10/10)
**Tests**: 15 new tests | 465 regression guards passing | 0 regressions

---

## Sprint 207 Goal (Archived)

Sprint 206 delivered LangGraph Durable Workflows (ADR-066 Phase 2). Sprint 207 addresses a UX gap in the OTT Gateway: users must type 36-char UUIDs for every governance command because there's no "active project" concept in chat.

**Current state** (OTT Gateway):
- `OTT_DEFAULT_PROJECT_ID` env var — admin-configured, one project for ALL users
- No user-facing command to set/switch workspace
- `/gates`, `/approve`, `/evidence` require explicit `project_id` parameter

**Target state**:
- `workspace_service.py` — standardized Redis HASH at `ott:workspace:{channel}:{chat_id}` with 7-day TTL
- `/workspace set bflow` — user sets active project by name in 1 command
- `/workspace list` — user sees all accessible projects
- Governance commands auto-inject `project_id` from workspace (priority chain: explicit → workspace → env → error)

---

## Sprint 207 Backlog

### Track A — workspace_service.py + Alembic Migration ✅

| ID | Item | Status |
|----|------|--------|
| A1 | `workspace_service.py` — `WorkspaceContext` frozen dataclass + 6 functions | ✅ DONE |
| A2 | `resolve_project_by_name()` — ILIKE search with `ProjectMember` join | ✅ DONE |
| A3 | `resolve_project_id()` — 4-level priority chain (D-067-04) | ✅ DONE |
| A4 | Alembic `s207_001` — pg_trgm GIN index on `projects.name` | ✅ DONE |

**New files**: `workspace_service.py` (~210 LOC), `s207_001_projects_name_trgm_index.py`

### Track B — Telegram Command Interface ✅

| ID | Item | Status |
|----|------|--------|
| B1 | `telegram_responder.py` — 4 workspace static commands (/workspace, /workspace_set, /workspace_list, /workspace_clear) | ✅ DONE |
| B2 | `ai_response_handler.py` — 4 slash-to-governance mappings + workspace LLM-bypass intercept | ✅ DONE |

**Modified files**: `telegram_responder.py` (+4 entries), `ai_response_handler.py` (+4 slash mappings + workspace intercept)

### Track C — Governance Injection ✅

| ID | Item | Status |
|----|------|--------|
| C1 | `governance_action_handler.py` — `execute_workspace_command()` dispatch (set/info/list/clear) | ✅ DONE |
| C2 | `execute_governance_action()` — workspace project_id injection for 5 command types | ✅ DONE |
| C3 | `touch_workspace_ttl()` after successful workspace-injected execution | ✅ DONE |
| C4 | Disambiguation list with UUIDs for multi-match (max 5) | ✅ DONE |
| C5 | Group override notice (FR-049-06 P0-4) | ✅ DONE |

**Modified files**: `governance_action_handler.py` (+execute_workspace_command ~250 LOC, +workspace injection ~30 LOC, +TTL touch)

### Track D — Tests ✅

| ID | Item | Status |
|----|------|--------|
| D1 | `WorkspaceContext` frozen dataclass tests | ✅ DONE |
| D2 | `is_uuid()` valid/invalid tests | ✅ DONE |
| D3 | `get_workspace()` — returns context, None on empty, None on Redis error | ✅ DONE |
| D4 | `set_workspace()` — stores HASH with 7-day TTL | ✅ DONE |
| D5 | `clear_workspace()` — deletes key | ✅ DONE |
| D6 | `resolve_project_id()` — 4-level priority chain (explicit/workspace/env/none) | ✅ DONE |
| D7 | `touch_workspace_ttl()` — resets expiry + swallows errors | ✅ DONE |
| D8 | Telegram responder workspace commands present | ✅ DONE |

**New files**: `test_sprint207_ott_workspace.py` (15 tests)

---

## Definition of Done — Sprint 207

- [x] Alembic migration `s207_001` — `pg_trgm` GIN index on `projects.name`
- [x] `workspace_service.py` — `WorkspaceContext` + 6 async functions
- [x] `get_workspace()` returns `None` on `ConnectionError` (graceful degradation D-067-01)
- [x] `/workspace set bflow` (1 match) → stores Redis HASH, replies with tier + stage
- [x] `/workspace set platform` (2-5 matches) → disambiguation list with UUIDs
- [x] `/workspace` → formatted project card when set, guidance when not
- [x] `/workspace list` → user's projects (max 10), `▶` marker on active
- [x] `/workspace clear` → "was: <name>" confirmation, Redis key deleted
- [x] Workspace bypass LLM router (MAX_COMMANDS=10 full — no ToolName slot)
- [x] `resolve_project_id()` — 4-level priority chain (explicit → workspace → env → None)
- [x] Governance commands auto-inject `project_id` from workspace (5 command types)
- [x] TTL touch ONLY on successful workspace-injected governance execution
- [x] 15/15 Sprint 207 tests passing
- [x] 0 regressions from Sprint 207 changes (1198 OTT/agent tests passed, 6 pre-existing failures)
- [x] CURRENT-SPRINT.md updated to Sprint 207
- [x] SPRINT-207-OTT-WORKSPACE.md status: COMPLETE

---

## Sprint 207 Close Summary

**Status**: CLOSED — PM APPROVED ✅
**CTO Score**: Pending (Quality Scorecard: Zero Mock 10/10, Type Hints 10/10, AGPL 10/10, Error Handling 9/10, Security 10/10, Testing 10/10)
**Tests**: 15 new tests | 465 regression guards passing | 0 regressions
**New files**: `workspace_service.py` (~210 LOC), `s207_001_projects_name_trgm_index.py`, `test_sprint207_ott_workspace.py` (15 tests)
**Modified files**: `governance_action_handler.py` (+~280 LOC), `ai_response_handler.py` (+~30 LOC workspace intercept), `telegram_responder.py` (+4 entries)
**PM Verification**: 15/15 tests passed, 465 guard total, code audit CLEAN — SHIP READY

**Key deliverables**:
- `workspace_service.py` — Redis HASH CRUD at `ott:workspace:{channel}:{chat_id}`, 7-day TTL, `WorkspaceContext` frozen dataclass
- `resolve_project_by_name()` — ILIKE search with `ProjectMember` membership check, disambiguation for 2-5 matches
- `resolve_project_id()` — 4-level priority chain: explicit → workspace → OTT_DEFAULT_PROJECT_ID → None
- `execute_workspace_command()` — 4 subcommands (set/info/list/clear) with Vietnamese/English bilingual replies
- Workspace bypass LLM router — intercepts in `ai_response_handler.py` before `route_chat_command()` (MAX_COMMANDS=10 full)
- Auto-injection into 5 governance command types (gate_status, submit_evidence, export_audit, update_sprint, close_sprint)
- TTL touch precision — reset ONLY on successful workspace-injected execution (D-067-02)

---

## Sprint 206 Close Summary

**Status**: CLOSED — All 5 Tracks Complete ✅
**Tests**: 25 new tests (17 RG/WR/ID/CP + 8 WS) | 0 regressions
**Key deliverables**: `WorkflowMetadata` + `WorkflowService` (OCC), `ReflectionGraph` (5-node async), `WorkflowResumer` (dual-path), 3 control plane endpoints

---

## Sprint 205 Close Summary

**Status**: CLOSED — All 3 Tracks Complete ✅
**Tests**: 38 new tests (21 LC + 17 LT) | 0 regressions
**Key deliverables**: `LangChainProvider` (ChatOllama/ChatAnthropic/ChatOpenAI), `LangChainToolRegistry` (5 StructuredTools), `authorize_tool_call()` guard

---

## Sprint 204 Close Summary

**Status**: CLOSED — All 4 Tracks Complete ✅
**Tests**: 87 new tests | 298/298 regression guards passing
**Key deliverables**: `ClassificationResult` + confidence scoring, governance pre-router, `EscalationService` + Magic Link, 5 routing eval cases

---

## Sprint 203 Close Summary

**Status**: CLOSED — All 4 Tracks Complete ✅ | CTO Score: 9.5/10
**Tests**: 110 new tests | 285/285 regression guards passing
**Key deliverables**: `ReflectResult` + `reflect_and_score()` + `MultiJudgeResult` + 15 YAML eval cases + `run_evals.py` CLI

---

*Last Updated*: February 26, 2026 — Sprint 207 COMPLETE ✅
