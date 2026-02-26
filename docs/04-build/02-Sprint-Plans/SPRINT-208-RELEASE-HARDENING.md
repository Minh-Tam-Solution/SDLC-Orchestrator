---
sdlc_version: "6.1.1"
document_type: "Sprint Plan"
status: "CLOSED"
sprint: "208"
spec_id: "SPRINT-208"
tier: "PROFESSIONAL"
stage: "04 - Build"
---

# Sprint 208 — Pre-Release Hardening

**Sprint Duration**: Feb 26, 2026 (1 working day)
**Sprint Goal**: Fix P0 tier gate bypass, clean dead code, implement 3 overdue stub commands, consolidate test infrastructure
**Status**: CLOSED — PM APPROVED ✅ (Feb 26, 2026)
**Priority**: P0 (Release blocker) + P1 (Tech debt)
**Framework**: SDLC 6.1.1
**Previous Sprint**: [Sprint 207 — OTT Workspace Context Management](SPRINT-207-OTT-WORKSPACE.md)
**Sprint Close**: [SPRINT-208-CLOSE.md](SPRINT-208-CLOSE.md) *(to be created at close)*
**Release Target**: v1.1.0 — Post-GA Hardening

---

## Sprint 208 Goal

Sprint 207 closed the OTT Workspace feature. Full codebase review (PM + Architect) identified 1 P0 blocker and several P1 hygiene items that must be addressed before the next release:

**P0 Blocker**: TG-41 Tier Gate bypass — `/api/v1/magic-link` and `/api/v1/workflows` skip tier enforcement (CTO Sprint 185 mandate).

**P1 Hygiene**: 3 stub commands occupying command registry slots since Sprint 199 (8 sprints overdue), 3 dead code modules, infrastructure broken import.

**P2 Structural**: WorkflowResumer not registered in lifespan (blocks `LANGGRAPH_ENABLED=true` production toggle).

---

## Day Timeline (1 Working Day)

| Time | Block | Track |
|------|-------|-------|
| 09:00–09:10 | Track A: TG-41 fix (P0) | tier_gate.py + verify TG-41 green |
| 09:10–09:30 | Track B: Dead code deletion (P1) | 3 deletions + import smoke test |
| 09:30–11:00 | Track C: 3 stub commands (P1) | governance_action_handler.py |
| 11:00–11:20 | Track D: WorkflowResumer lifespan (P2) | main.py conditional startup |
| 11:20–11:35 | Track E: Tests + regression guard | full test run |
| 11:35–11:45 | Close: SPRINT-INDEX + CURRENT-SPRINT update | docs |

**Total estimated**: ~2.5 hours coding + 45 min testing/docs = **1 working day**

---

## Sprint 208 Backlog

### Track A — P0: TG-41 Tier Gate Fix (~5 min)

| ID | Item | Est | Status |
|----|------|-----|--------|
| A1 | Add `/api/v1/magic-link` to `ROUTE_TIER_TABLE` — tier STANDARD (2) | 2 min | ✅ DONE |
| A2 | Add `/api/v1/workflows` to `ROUTE_TIER_TABLE` — tier PROFESSIONAL (3) | 2 min | ✅ DONE |
| A3 | Verify `test_tg_41_all_fastapi_routes_in_tier_table` passes | 1 min | ✅ DONE |

**File**: `backend/app/middleware/tier_gate.py` — add 2 lines to `ROUTE_TIER_TABLE` dict.

**Tier rationale**:
- `/api/v1/magic-link`: STANDARD (2) — OOB auth for gate approvals, team collaboration feature
- `/api/v1/workflows`: PROFESSIONAL (3) — LangGraph durable workflows, multi-agent feature

**Exact change** (find the end of `ROUTE_TIER_TABLE` dict in `tier_gate.py`):
```python
# Sprint 207 — magic-link (OOB auth) + LangGraph workflow control plane
"/api/v1/magic-link": 2,   # STANDARD — OOB gate approvals via chat (FR-047, ADR-064)
"/api/v1/workflows": 3,    # PROFESSIONAL — LangGraph durable workflows (ADR-066)
```

**Verify**:
```bash
cd backend
DATABASE_URL="..." python -m pytest tests/unit/test_tier_gate.py::test_tg_41_all_fastapi_routes_in_tier_table -v
```
Expected: `PASSED` (previously failing with 2 ungated routes).

### Track B — P1: Dead Code Cleanup (~15 min)

| ID | Item | Est | Status |
|----|------|-----|--------|
| B1 | Delete `backend/app/services/billing/` — empty directory (only `__pycache__`) | 2 min | ✅ DONE |
| B2 | Delete `backend/app/services/infrastructure/__init__.py` — broken import (references non-existent `minio_service.py`) | 2 min | ✅ DONE |
| B3 | Delete `backend/app/services/browser_agent_service.py` — 0 references in codebase | 2 min | ✅ DONE |
| B4 | Verify no import breakage after deletions | 5 min | ✅ DONE |

**Exact deletions**:
```bash
# B1 — billing/ empty (only __pycache__)
rm -rf backend/app/services/billing/

# B2 — infrastructure/__init__.py broken import (references non-existent minio_service.py at package level)
rm backend/app/services/infrastructure/__init__.py
# NOTE: Keep infrastructure/ directory if other files exist inside

# B3 — browser_agent_service.py (0 grep hits outside itself)
rm backend/app/services/browser_agent_service.py
```

**Validation**:
```bash
cd backend
python -c "from app.main import app; print('✅ import OK')"
# Expected: ✅ import OK (no ImportError)
```

**Confirm no references before deleting** (safety check):
```bash
grep -r "browser_agent_service\|from app.services.billing\|from app.services.infrastructure" backend/app/ --include="*.py" | grep -v __pycache__
# Expected: 0 results
```

### Track C — P1: Implement 3 Stub OTT Commands (~90 min)

These commands have occupied 3 of 10 `command_registry` slots since Sprint 199 (8 sprints ago) with "Feature coming" placeholder responses.

| ID | Item | Est | Status |
|----|------|-----|--------|
| C1 | `create_project` — wire to `project_service.create_project()`, require project name + optional tier | 30 min | ✅ DONE |
| C2 | `submit_evidence` — wire text-based evidence to `evidence_service.create_evidence()`, attach to workspace project | 30 min | ✅ DONE |
| C3 | `update_sprint` — wire to existing `sprint_command_handler.handle_update_sprint()` | 20 min | ✅ DONE |
| C4 | Tests for 3 new command implementations | 10 min | ✅ DONE |

**Files modified**: `backend/app/services/agent_bridge/governance_action_handler.py`
**Dependency**: `resolve_project_id()` from `workspace_service.py` (merged Sprint 207)

**C1 — `create_project` implementation pattern**:

```python
elif tool_name == ToolName.CREATE_PROJECT.value:
    project_name = tool_args.get("name") or tool_args.get("project_name", "")
    tier = tool_args.get("tier", "STANDARD").upper()
    if not project_name:
        await _send_telegram_reply(
            bot_token, chat_id,
            "❌ Thiếu tên project.\nVí dụ: tạo project 'BFlow Alpha' tier PROFESSIONAL",
            channel=channel,
        )
        return False
    async with AsyncSessionLocal() as db:
        from app.services.project_service import project_service
        from app.models.user import User
        user = await db.get(User, user_id)
        org_id = str(user.organization_id) if user and user.organization_id else None
        project = project_service.create_project(db, {
            "project_name": project_name,
            "organization_id": org_id,
            "tier": tier,
            "created_by": str(user_id),
        })
    await _send_telegram_reply(
        bot_token, chat_id,
        f"✅ Project tạo thành công!\n"
        f"📋 {project.project_name}\n"
        f"🎯 Tier: {project.tier}\n"
        f"🆔 ID: {project.id}\n\n"
        f"Đặt workspace: /workspace set {project.project_name}",
        channel=channel,
    )
    handled = True
```

**C2 — `submit_evidence` implementation pattern**:

Current OTT flow: user sends text description → create evidence record with `source="ott"`.
Gate ID resolved from workspace (same priority chain as governance commands).

```python
elif tool_name == ToolName.SUBMIT_EVIDENCE.value:
    description = tool_args.get("description") or tool_args.get("content", "")
    evidence_type = tool_args.get("evidence_type", "DOCUMENTATION")
    gate_id = tool_args.get("gate_id")
    if not description:
        await _send_telegram_reply(
            bot_token, chat_id,
            "❌ Thiếu nội dung evidence.\n"
            "Ví dụ: nộp evidence 'Design review completed by CTO on Feb 26'",
            channel=channel,
        )
        return False
    async with AsyncSessionLocal() as db:
        from app.services.evidence_service import evidence_service
        evidence = await evidence_service.create_text_evidence(db, {
            "description": description,
            "evidence_type": evidence_type,
            "gate_id": gate_id,
            "submitted_by": str(user_id),
            "source": "ott",
        })
    await _send_telegram_reply(
        bot_token, chat_id,
        f"📎 Evidence đã nộp!\n"
        f"🆔 ID: {evidence.id}\n"
        f"📝 Type: {evidence_type}\n"
        f"Status: {evidence.status}",
        channel=channel,
    )
    handled = True
```

**C3 — `update_sprint` implementation pattern** (simplest — delegate to existing handler):

```python
elif tool_name == ToolName.UPDATE_SPRINT.value:
    from app.services.agent_team.sprint_command_handler import handle_update_sprint
    handled = await handle_update_sprint(
        tool_args, bot_token, chat_id, user_id, channel=channel,
    )
```
Replace the existing 8-line stub with this 4-line delegate. `handle_update_sprint` already implemented in Sprint 199.

### Track D — P2: WorkflowResumer Lifespan Registration (~20 min)

| ID | Item | Est | Status |
|----|------|-----|--------|
| D1 | Add `WorkflowResumer.start()`/`stop()` to FastAPI lifespan when `LANGGRAPH_ENABLED=true` | 15 min | ✅ DONE |
| D2 | Test that resumer is NOT started when feature flag is `false` (default) | 5 min | ✅ DONE |

**File**: `backend/app/main.py` — add conditional startup in lifespan context manager.
**Guard**: Only starts when `config.LANGGRAPH_ENABLED` is `True`.

**Exact change** in `lifespan()` function — add after APScheduler startup block:

```python
# Sprint 208 — WorkflowResumer conditional lifespan (ADR-066, LANGGRAPH_ENABLED guard)
workflow_resumer = None
if getattr(config, "LANGGRAPH_ENABLED", False):
    try:
        from app.services.agent_team.workflow_resumer import WorkflowResumer
        workflow_resumer = WorkflowResumer()
        await workflow_resumer.start()
        print("✅ WorkflowResumer started (LANGGRAPH_ENABLED=true)")
    except Exception as e:
        print(f"⚠️  WorkflowResumer failed to start: {e}")
        # Non-fatal — LangGraph workflows will not auto-resume on restart
```

And in the shutdown block (after `yield`):

```python
# Sprint 208 — stop WorkflowResumer if started
if workflow_resumer is not None:
    try:
        await workflow_resumer.stop()
        print("✅ WorkflowResumer stopped")
    except Exception as e:
        print(f"⚠️  WorkflowResumer stop error: {e}")
```

**Default**: `LANGGRAPH_ENABLED` defaults to `False` — no change in production until explicitly set.

### Track E — Tests + Regression Guard (~15 min)

| ID | Item | Est | Status |
|----|------|-----|--------|
| E1 | TG-41 test green (Track A verification) | 2 min | ✅ DONE |
| E2 | Import smoke test after dead code deletion (Track B) | 3 min | ✅ DONE |
| E3 | 3 new command implementation tests (Track C) | included in C4 | ✅ DONE |
| E4 | WorkflowResumer lifespan test (Track D) | included in D2 | ✅ DONE |
| E5 | Full Sprint 205-207 regression run (78 tests) | 5 min | ✅ DONE |

**Full test command**:
```bash
cd backend
DATABASE_URL="postgresql://test:test@localhost:15432/sdlc_test" \
  python -m pytest tests/unit/test_tier_gate.py::test_tg_41_all_fastapi_routes_in_tier_table \
                   tests/unit/test_sprint208_hardening.py \
                   tests/unit/test_sprint207_ott_workspace.py \
                   tests/unit/test_sprint206_workflow_service.py \
                   tests/unit/test_sprint205_langchain.py \
  -v --tb=short
```
Expected: all green, 0 regressions.

---

## Definition of Done — Sprint 208

- [x] `test_tg_41_all_fastapi_routes_in_tier_table` PASSES (0 missing routes)
- [x] `/api/v1/magic-link` → tier STANDARD (2) in `ROUTE_TIER_TABLE`
- [x] `/api/v1/workflows` → tier PROFESSIONAL (3) in `ROUTE_TIER_TABLE`
- [x] `billing/` directory deleted (was empty)
- [x] `infrastructure/__init__.py` deleted (broken import)
- [x] `browser_agent_service.py` deleted (0 references)
- [x] `python -c "from app.main import app"` succeeds after cleanup
- [x] `create_project` command — real implementation via async ORM (RF-01)
- [x] `submit_evidence` command — real implementation via GateEvidence ORM (RF-02)
- [x] `update_sprint` command — wired to sprint_command_handler
- [x] WorkflowResumer conditionally started in lifespan (`LANGGRAPH_ENABLED=true`)
- [x] Tests for 3 new command implementations (8 tests)
- [x] Sprint 205-207 regression guard: 78/78 passing
- [x] 0 new regressions from Sprint 208 changes (310 total)
- [x] CURRENT-SPRINT.md updated to Sprint 208
- [x] SPRINT-INDEX.md updated

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Dead code deletion breaks hidden import | Low | Medium | Smoke test `from app.main import app` + full test run |
| Stub command implementation mismatches existing service API | Low | Low | Read existing service methods before wiring |
| WorkflowResumer interferes with FastAPI lifespan on shutdown | Low | Medium | Feature-flagged, graceful shutdown with timeout |

---

## Architecture Notes

### Tier Assignments (Track A)

Per ADR-059 tier hierarchy:
- **Magic Link** (`/api/v1/magic-link`): OOB authentication for gate approvals via chat. Requires team collaboration → **STANDARD (2)**.
- **Workflows** (`/api/v1/workflows`): LangGraph durable workflow control plane. Multi-agent feature → **PROFESSIONAL (3)**.

### Command Registry Capacity (Track C)

After implementing 3 stubs, all 10 slots will have real implementations:
1. `create_project` ← was stub
2. `get_gate_status` ✅
3. `submit_evidence` ← was stub
4. `request_approval` ✅
5. `export_audit` ✅
6. `update_sprint` ← was stub
7. `close_sprint` ✅
8. `invite_member` ✅
9. `run_evals` ✅
10. `list_notes` ✅

Future OTT commands (Sprint 209+) will need command namespace design (e.g., `/gate approve` subcommand pattern).

### Dead Code Rationale (Track B)

| Module | Created | Purpose | Why Dead |
|--------|---------|---------|----------|
| `billing/` | Sprint ~180 | Future billing logic | Never populated — billing handled by Stripe integration routes |
| `infrastructure/__init__.py` | Sprint ~74 | MinIO service wrapper | MinIO moved to `minio_service.py` at top level; package never updated |
| `browser_agent_service.py` | Sprint ~175 | Browser automation agent | Replaced by tool_context.py pattern; never imported |

### Service API References (Track C)

| Command | Service | Method | Location |
|---------|---------|--------|----------|
| `create_project` | `ProjectService` | `create_project(db, data_dict)` | `backend/app/services/project_service.py:98` |
| `submit_evidence` | `EvidenceService` | `create_text_evidence(db, data_dict)` | `backend/app/services/evidence_service.py` |
| `update_sprint` | `sprint_command_handler` | `handle_update_sprint(args, bot, chat, user, channel)` | `backend/app/services/agent_team/sprint_command_handler.py:31` |

**Note on `submit_evidence`**: If `EvidenceService.create_text_evidence()` does not exist, create a thin wrapper that creates an `GateEvidence` model row with `source="ott"`, `status="uploaded"`, no MinIO upload (text-only). Full file attachment via Telegram file_id can be Sprint 209+ scope.

### WorkflowResumer Status (Track D)

`WorkflowResumer` is already implemented in `backend/app/services/agent_team/workflow_resumer.py` (Sprint 206 Track D). It is NOT currently called from lifespan — the class exists but is never started. Sprint 208 adds the conditional `lifespan()` registration. When `LANGGRAPH_ENABLED=false` (default), the class is never imported, keeping startup fast.

---

## New Test File: `test_sprint208_hardening.py`

Target: `backend/tests/unit/test_sprint208_hardening.py`

**Test cases** (minimum to cover Track A + Track C + Track D):

| ID | Test | What it covers |
|----|------|---------------|
| S208-01 | `test_tier_gate_magic_link_registered` | `/api/v1/magic-link` → tier 2 in ROUTE_TIER_TABLE |
| S208-02 | `test_tier_gate_workflows_registered` | `/api/v1/workflows` → tier 3 in ROUTE_TIER_TABLE |
| S208-03 | `test_create_project_stub_removed` | ToolName.CREATE_PROJECT route returns real response, not "Feature coming" |
| S208-04 | `test_submit_evidence_stub_removed` | ToolName.SUBMIT_EVIDENCE route returns real response |
| S208-05 | `test_update_sprint_delegates_to_handler` | ToolName.UPDATE_SPRINT calls sprint_command_handler |
| S208-06 | `test_workflow_resumer_not_started_by_default` | `LANGGRAPH_ENABLED=false` → resumer not started |
| S208-07 | `test_workflow_resumer_started_when_enabled` | `LANGGRAPH_ENABLED=true` → resumer.start() called |
| S208-08 | `test_import_smoke_no_billing_import` | `from app.main import app` succeeds after billing/ deleted |

---

## G-Sprint-Close Gate — Definition of Done

*(To be filled in at close — create [SPRINT-208-CLOSE.md](SPRINT-208-CLOSE.md) on completion)*

| Criterion | Status |
|-----------|--------|
| All DoD items checked (16/16) | ✅ DONE |
| New tests passing (8/8) | ✅ DONE |
| Regression guard: Sprint 205-207 (78 tests) | ✅ DONE |
| TG-41 CI test green | ✅ DONE |
| 0 new regressions | ✅ DONE |
| SPRINT-INDEX.md updated | ✅ DONE |
| CURRENT-SPRINT.md updated to Sprint 208 | ✅ DONE |
| Code committed + pushed to main | ✅ DONE |

---

## Quality Scorecard (Sprint 208 — CTO Review)

| Dimension | Target | Notes |
|-----------|--------|-------|
| Zero Mock | 10/10 | Track C removes 3 "Feature coming" stubs — real implementations |
| Type Hints | 10/10 | All new code must have full type hints |
| AGPL Compliance | 10/10 | No new AGPL imports |
| Error Handling | 9+/10 | create_project: ProjectValidationError handled |
| Security | 10/10 | No new auth bypass; TG-41 restores full tier coverage |
| Testing | 10/10 | 8 new tests cover all 4 tracks |

---

## CURRENT-SPRINT.md Update (at sprint start)

Update `docs/04-build/02-Sprint-Plans/CURRENT-SPRINT.md`:
- Header: `Sprint 208 — Pre-Release Hardening`
- Status: `ACTIVE`
- Link: `SPRINT-208-RELEASE-HARDENING.md`
- Previous close summaries: append Sprint 207 close summary block

## SPRINT-INDEX.md Update (at sprint close)

Update `docs/04-build/02-Sprint-Plans/SPRINT-INDEX.md`:
- Sprint 208 row: PLANNED → ✅ COMPLETE
- Add deliverables: TG-41 fix, 3 stub commands, dead code cleanup, WorkflowResumer lifespan
- Sprint metrics: ~8 new tests, 0 regressions, 3 files deleted, 2 routes gated

---

*Sprint 208 Plan — Created February 26, 2026*
*Next Sprint*: Sprint 209 — TBD (Zalo workspace support or Zero Mock debt clearance)
