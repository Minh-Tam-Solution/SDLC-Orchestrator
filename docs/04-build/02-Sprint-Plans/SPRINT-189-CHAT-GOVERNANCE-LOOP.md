---
sdlc_version: "6.1.0"
document_type: "Sprint Plan"
status: "PROPOSED"
sprint: "189"
spec_id: "SPRINT-189"
tier: "ALL"
stage: "04 - Build"
---

# SPRINT-189 — Chat-First Governance Loop (Phase 0 PoC + Phase 1)

**Status**: PROPOSED (pending CTO approval)
**Sprint Duration**: 8 working days
**Sprint Goal**: Deliver the Chat-First Governance Loop — chat_command_router + magic_link_service + OTT gateway dedupe
**Epic**: EP-08 Chat-First Governance Loop
**ADR**: ADR-064 (Option D+, 4 locked decisions, 11 conditions)
**Dependencies**: Sprint 188 complete (GA Launch), Ollama qwen3:32b Vietnamese tool calling (Day 1 test)
**Budget**: ~$5,120 (64 hrs at $80/hr)

---

## 1. Sprint Goal

Sprint 189 delivers the P0 core of the Chat-First Governance Loop — the minimum viable chat interface that enables the North Star Loop:

```
@mention → Gate Actions → Evidence → Approve (Magic Link) → Audit Export
```

Three deliverables:
1. **chat_command_router.py** — LLM Function Calling with bounded allowlist + Pydantic validation (~300 LOC)
2. **magic_link_service.py** — HMAC-SHA256 signed single-use OOB auth tokens (~150 LOC)
3. **OTT gateway dedupe** — Redis-based event_id deduplication at gateway (~30 LOC)

| Track | Priority | Days |
|-------|----------|------|
| Day 1: Ollama Vietnamese PoC (GO/NO-GO) | P0 | 1 |
| Day 2-3: chat_command_router.py | P0 | 2 |
| Day 4-5: magic_link_service.py + requires_oob_auth | P0 | 2 |
| Day 6: OTT gateway dedupe + wiring | P0 | 1 |
| Day 7: Acceptance tests (6 tests) | P0 | 1 |
| Day 8: Sprint close + CTO review | -- | 1 |
| **Total** | | **8** |

---

## 2. Deliverables

| # | Deliverable | Description | LOC | Sprint Day |
|---|------------|-------------|-----|------------|
| 1 | Ollama Vietnamese tool calling PoC | Test qwen3:32b with `/api/chat` tools parameter on Vietnamese prompts | ~50 | Day 1 |
| 2 | chat_command_router.py | LLM Function Calling router (5 tools, Pydantic validation, Actions Contract) | ~300 | Day 2-3 |
| 3 | magic_link_service.py | HMAC-SHA256 token generation + validation + single-use Redis storage | ~150 | Day 4 |
| 4 | requires_oob_auth | Add field to GateActionsResponse + compute_gate_actions() logic | ~20 | Day 5 |
| 5 | MAGIC_LINK_SECRET | Add to config.py Settings | ~5 | Day 5 |
| 6 | OTT gateway dedupe | Redis-based webhook_dedupe:{channel}:{event_id} at gateway | ~30 | Day 6 |
| 7 | Wiring | Connect ott_gateway → mention_parser → chat_command_router | ~20 | Day 6 |
| 8 | Acceptance tests | 6 tests (happy path, actions contract, evidence, non-happy, bootstrap, bounded LLM) | ~200 | Day 7 |

---

## 3. Daily Schedule

### Day 1: Ollama Vietnamese Tool Calling PoC (GO/NO-GO)

**Goal**: Validate that qwen3:32b can extract tool calls from Vietnamese natural language

**Test Cases**:
```
Input: "Ê @pm, tạo dự án Bflow đi"
Expected: tool_call = create_project(name="Bflow")

Input: "@reviewer approve G2 cho project #123"
Expected: tool_call = request_approval(gate_id=..., action="approve")

Input: "show me gate status for project 5"
Expected: tool_call = get_gate_status(project_id=5)
```

**GO Criteria**: >90% accuracy on 10 Vietnamese test prompts
**NO-GO Action**: Switch to Claude Haiku fallback ($0.25/1M tokens), document failure

**Files**: Temporary `scripts/ollama_vn_poc.py` (~50 LOC)

### Day 2-3: Chat Command Router

**Goal**: Implement bounded LLM Function Calling with Pydantic validation

**New File**: `backend/app/services/agent_team/chat_command_router.py` (~300 LOC)
**Modified File**: `backend/app/services/ollama_service.py` — Add NEW `async def chat()` method (~40 LOC)

**CRITICAL — Ollama `/api/chat` gap (P0-1)**:
- Existing `ollama_service.py` only has `generate()` which calls `/api/generate` — this does NOT support tool calling
- Must add a NEW `chat()` method that calls `/api/chat` with the `tools` parameter for function calling
- CTO preference: Add method to `ollama_service.py` (keeps Ollama abstraction centralized)

**Implementation per ADR-064 conditions**:
- T-01: Bounded allowlist (5 tools) + Pydantic validation, max 2 retries
- T-02: Native Ollama `/api/chat` tools parameter (NOT LangChain); NEW `chat()` method in `ollama_service.py`
- T-08: `run_in_threadpool` for sync Ollama calls (ollama_service uses `requests.post()`)
- T-09: `run_in_threadpool` for sync `ProjectService.create_project()` (uses sync `Session`)
- D-064-02: LLM Function Calling, NOT regex
- D-064-03: Actions Contract — ALWAYS call `compute_gate_actions()` before mutations
- A-04: Code samples in ADR are pseudocode; T-02 overrides

**Tool Schemas** (Pydantic v2):
- `CreateProjectParams(name: str, description: str | None)`
- `GetGateStatusParams(project_id: int | None, gate_id: UUID | None)`
- `SubmitEvidenceParams(gate_id: UUID, evidence_type: str, file_url: str)`
- `RequestApprovalParams(gate_id: UUID, action: Literal["approve", "reject"])`
- `ExportAuditParams(project_id: int, format: Literal["json", "csv"] = "json")`

**Integration (sync/async awareness)**:
- Uses `ollama_service.chat()` for LLM calls — SYNC, wrap with `run_in_threadpool`
- Uses `gate_service.py` for gate operations — ASYNC, direct `await`
- Uses `project_service.py` for project creation — SYNC, wrap with `run_in_threadpool`
- Uses `audit_service.py` for logging with `source="chat"` — ASYNC, direct `await`

### Day 4-5: Magic Link Service + requires_oob_auth

**Goal**: Implement OOB authentication for gate approvals via chat

**New File**: `backend/app/services/agent_team/magic_link_service.py` (~150 LOC)

**Implementation per ADR-064 conditions**:
- D-064-04: HMAC-SHA256 signed tokens, 5-min expiry, single-use
- A-01: `requires_oob_auth` is NEW code (~20 LOC) in gate_service.py + gate.py
- A-02: Use `app/utils/redis.py` async client (NOT `app/core/redis.py`)
- T-05: Use `app/utils/redis.py` async client

**Modified Files**:
- `backend/app/schemas/gate.py` — Add `requires_oob_auth: bool` to GateActionsResponse (~5 LOC)
- `backend/app/services/gate_service.py` — Add OOB auth logic to `compute_gate_actions()` (~15 LOC)
- `backend/app/core/config.py` — Add `MAGIC_LINK_SECRET: str` setting (~5 LOC)

**Token Flow**:
```
Chat: "@reviewer approve G3 #123"
  → chat_command_router checks compute_gate_actions()
  → requires_oob_auth == true
  → magic_link_service.generate_token(gate_id, "approve", user_id)
  → Redis SET magic_link:{signature} TTL 300
  → Return Magic Link URL to chat
  → User clicks → browser SSO → token validated → gate approved
  → Redis DEL magic_link:{signature} (single-use)
```

### Day 6: OTT Gateway Dedupe + Wiring

**Goal**: Add Redis deduplication to OTT gateway and wire the full chat pipeline

**Modified File**: `backend/app/api/routes/ott_gateway.py` (~30 LOC addition)

**Implementation per ADR-064 conditions**:
- T-04: Dedupe at OTT gateway, NOT router (full coverage)
- A-02: Use `app/utils/redis.py` async client

**Dedupe Logic**:
```
webhook arrives → extract event_id per channel
  → Redis GET webhook_dedupe:{channel}:{event_id}
  → EXISTS: return HTTP 200 {"status": "duplicate"} (no processing)
  → NOT EXISTS: Redis SET with TTL 3600, proceed with processing
```

**Wiring**: Connect `ott_gateway.py` → `mention_parser.py` → `chat_command_router.py`
- OTT gateway receives webhook, deduplicates, normalizes
- mention_parser extracts @mention targets
- chat_command_router handles governance commands
- Other messages pass through to existing agent_team pipeline

### Day 7: Acceptance Tests (6 Tests)

**Goal**: All 6 acceptance tests pass (GO/NO-GO for Phase 1)

| # | Test | Pass Criteria |
|---|------|--------------|
| 1 | Happy path + OPA decision | Full governance loop <10 min, ≤8 interactions, OPA decision in audit_logs |
| 2 | Actions contract | GET /gates/{id}/actions returns requires_oob_auth. Bot explains "why not". Router NEVER bypasses. |
| 3 | Evidence contract | SHA256 server-side. User MUST select evidence type. Hash mismatch → reject. |
| 4 | Non-happy paths (6 cases) | DRAFT approve → 409; duplicate → idempotent; no permission → 403; hash mismatch → reject; Slack replay → dedupe; concurrent approvals → consistent |
| 5 | Developer setup | bootstrap_dev.sh → admin + sample project → <5 min |
| 6 | Bounded LLM | Invalid tool → clarification; Pydantic fail → retry 2x then error; hallucinated gate_id → rejected |

**Test File**: `backend/tests/e2e/test_chat_governance_loop_e2e.py`

### Day 8: Sprint Close + CTO Review

- Sprint close documentation (SPRINT-189-CLOSE.md)
- CTO review of chat_command_router.py + magic_link_service.py
- Security review against STM-064 threat model
- GO/NO-GO decision for Sprint 190 cleanup

---

## 4. New Files

| File | LOC | Purpose |
|------|-----|---------|
| `backend/app/services/agent_team/chat_command_router.py` | ~300 | LLM Function Calling router |
| `backend/app/services/agent_team/magic_link_service.py` | ~150 | HMAC-signed OOB auth tokens |
| `scripts/bootstrap_dev.sh` | ~80 | One-command dev setup: creates admin user (via `create_admin.py` pattern), 1 sample project, 1 gate (G1) for acceptance test data |
| `scripts/ollama_vn_poc.py` | ~50 | Vietnamese tool calling PoC (temporary) |

## 5. Modified Files

| File | Change | LOC |
|------|--------|-----|
| `backend/app/schemas/gate.py` | Add `requires_oob_auth` to GateActionsResponse | ~5 |
| `backend/app/services/gate_service.py` | Add OOB auth logic to compute_gate_actions() | ~15 |
| `backend/app/services/ollama_service.py` | Add NEW `async def chat()` method for `/api/chat` with `tools` parameter | ~40 |
| `backend/app/api/routes/ott_gateway.py` | Add Redis-based webhook dedupe | ~30 |
| `backend/app/core/config.py` | Add MAGIC_LINK_SECRET setting | ~5 |

---

## 6. Risk Register

| Risk | Probability | Impact | Mitigation | Day |
|------|-------------|--------|------------|-----|
| Ollama Vietnamese tool calling fails | MEDIUM | HIGH | Day 1 PoC; fallback to Claude Haiku | 1 |
| Redis connection issues in tests | LOW | MEDIUM | Use async Redis mock pattern from STM-056 tests | 7 |
| Magic Link token entropy insufficient | LOW | CRITICAL | HMAC-SHA256 = 256 bits, infeasible brute-force | 4 |
| Gateway dedupe race condition | LOW | LOW | Redis SET NX (atomic) for dedupe key | 6 |

---

## 7. Definition of Done

- [ ] All 6 acceptance tests pass
- [ ] `ruff check backend/` → 0 errors on new files
- [ ] Security review against STM-064 (all C1-C8 mitigations verified)
- [ ] CTO code review APPROVED
- [ ] SPRINT-189-CLOSE.md created with retrospective
- [ ] Ollama Vietnamese accuracy documented (pass/fail with evidence)
