---
sdlc_version: "6.1.0"
document_type: "Functional Requirement"
status: "IMPLEMENTED"
sprint: "189"
spec_id: "FR-046"
tier: "ALL"
stage: "01 - Planning"
---

# FR-046: Chat Command Router (LLM Function Calling)

**Version**: 1.1.0
**Status**: IMPLEMENTED (Sprint 189 — CTO CONDITIONAL APPROVE 9.4/10)
**Created**: February 2026
**Sprint**: 189
**Framework**: SDLC 6.1.0
**Epic**: EP-08 Chat-First Governance Loop
**ADR**: ADR-064 (D-064-02 LLM Function Calling, D-064-03 Actions Contract)
**Owner**: Backend Team

---

## 1. Overview

### 1.1 Purpose

Route natural language chat messages from OTT channels (Telegram, Zalo, Teams, Slack) to SDLC governance actions via LLM Function Calling. The router extracts user intent using Ollama's native `/api/chat` tools parameter, validates parameters with Pydantic schemas, and delegates execution to existing control plane services.

### 1.2 Business Value

- Enables governance loop via chat: `@pm create project` → `@reviewer approve G2`
- Handles Vietnamese natural language: "Ê @pm, tạo dự án X đi"
- Encodes CEO governance patterns so any PM achieves CEO-level oversight
- Reuses 100% of existing REST API services (gate_service, project_service, etc.)

---

## 2. Functional Requirements

### 2.1 Bounded Tool Allowlist

**GIVEN** a chat message routed to the command router
**WHEN** the LLM extracts a tool call
**THEN** the system SHALL:
1. Validate the tool name against an explicit allowlist of 5 tools:
   - `create_project` — Create a new SDLC project
   - `get_gate_status` — Get gate status and available actions
   - `submit_evidence` — Upload evidence for a gate (type user-selected)
   - `request_approval` — Request gate approval (triggers Magic Link if OOB required)
   - `export_audit` — Export audit trail for a project/gate
2. Reject any tool call NOT in the allowlist with a user-friendly message listing available commands
3. Never execute arbitrary functions or dynamically discovered tools

### 2.2 Pydantic Parameter Validation

**GIVEN** a tool call extracted by the LLM
**WHEN** the tool parameters are received
**THEN** the system SHALL:
1. Validate parameters against a Pydantic schema specific to each tool
2. On validation failure, retry LLM extraction with the error message (max 2 retries)
3. After 3 total attempts (1 initial + 2 retries), return a graceful error asking the user to rephrase
4. Never pass unvalidated parameters to the control plane

### 2.3 Actions Contract Enforcement (D-064-03)

**GIVEN** a tool call that mutates gate state (submit, approve, reject)
**WHEN** the router processes the request
**THEN** the system SHALL:
1. ALWAYS call `compute_gate_actions(gate, user, db)` before executing
2. Check the relevant `can_*` field in the actions response
3. If action is disallowed, return the `reasons` explanation to the user via chat
4. NEVER bypass the Actions Contract — even if the LLM suggests it

### 2.4 LLM Integration (Native Ollama, NOT LangChain)

**GIVEN** a chat message requiring intent extraction
**WHEN** the router calls the LLM
**THEN** the system SHALL:
1. Use Ollama's native `/api/chat` endpoint with the `tools` parameter
2. Add a NEW `async def chat()` method to `ollama_service.py` (~40 LOC) that calls `/api/chat` with `tools` parameter (existing `generate()` uses `/api/generate` which does NOT support tool calling)
3. Use `qwen3:32b` as primary model (Vietnamese support)
4. Include a system prompt defining the governance context
5. NOT import LangChain, LlamaIndex, or any LLM orchestration framework
6. Fallback to Claude Haiku via Anthropic API if Ollama unavailable

### 2.5 Response Formatting

**GIVEN** a tool execution result from the control plane
**WHEN** the router formats the response
**THEN** the system SHALL:
1. Format results as clear, concise chat messages
2. Include gate status, evidence status, and next recommended action
3. For gate status queries, show the Actions Contract response in human-readable form
4. For approvals requiring OOB auth, include the Magic Link URL

### 2.6 Integration with Existing Services

**GIVEN** a validated tool call
**WHEN** the router executes the action
**THEN** the system SHALL:
1. Call existing service layer functions (NOT raw SQL, NOT direct model access)
2. Wrap SYNC service calls with `run_in_threadpool` to avoid blocking the async event loop:
   - `ollama_service.generate()` / `ollama_service.chat()` — SYNC (uses `requests.post()`)
   - `project_service.create_project()` — SYNC (uses `Session`)
3. Call ASYNC services directly with `await`:
   - `gate_service.compute_gate_actions()` — ASYNC (uses `AsyncSession`)
   - `gate_service.approve_gate()` — ASYNC (uses `AsyncSession`)
   - `audit_service.log()` — ASYNC
4. Log all actions via `AuditService.log()` with `source="chat"`
5. Respect existing RBAC, tier enforcement, and usage limits
6. Use the OrchestratorMessage's `sender_id` to resolve the authenticated user

---

## 3. Non-Functional Requirements

| Requirement | Target |
|-------------|--------|
| Chat response latency (p95) | <3 seconds |
| LLM intent extraction accuracy (Vietnamese) | >90% on test corpus |
| Max retries on Pydantic validation failure | 2 (3 total attempts) |
| Tool allowlist size | 5 (expandable via config) |
| Fallback when Ollama unavailable | Claude Haiku ($0.25/1M tokens) |

---

## 4. File Location

`backend/app/services/agent_team/chat_command_router.py` (~300 LOC)

---

## 5. Dependencies

- `backend/app/services/ollama_service.py` — LLM calls (SYNC — requires `run_in_threadpool`); NEW `chat()` method for `/api/chat` with `tools`
- `backend/app/services/gate_service.py` — compute_gate_actions(), approve_gate(), etc. (ASYNC — direct `await`)
- `backend/app/services/project_service.py` — create_project() (SYNC — requires `run_in_threadpool`)
- `backend/app/services/audit_service.py` — AuditService.log() (ASYNC — direct `await`)
- `backend/app/services/agent_team/mention_parser.py` — @mention extraction
- `backend/app/services/agent_bridge/protocol_adapter.py` — OrchestratorMessage
- `backend/app/utils/redis.py` — async Redis client
- `backend/app/core/config.py` — OLLAMA_URL, model settings
- `starlette.concurrency.run_in_threadpool` — wraps sync calls in async context
