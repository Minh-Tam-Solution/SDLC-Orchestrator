---
sdlc_version: "6.1.1"
document_type: "Architecture Decision Record"
status: "APPROVED"
sprint: "205"
spec_id: "ADR-066"
tier: "PROFESSIONAL"
stage: "02 - Design"
owner: "CTO"
approved_by: "CTO"
approved_date: "2026-02-24"
---

# ADR-066 — LangChain Multi-Agent Orchestration

**Status**: APPROVED (CTO Sign-off 2026-02-24, Sprint 205)
**Date**: February 2026
**Author**: PM + Architect (research), CTO (verification + approval)
**Sprint**: Sprint 205-206
**Framework**: SDLC 6.1.1
**Supersedes**: None (extends ADR-056 Multi-Agent Team Engine)
**References**: ADR-056 (Multi-Agent), ADR-058 (ZeroClaw), ADR-064 (Chat-First Facade)
**Review History**: 5-Expert Panel (3+2), CTO Verification (8.5/10), 8 Findings Resolved
**Source**: CEO MAS Research (`mas/` directory, ~70 pages)

---

## 1. Context

### 1.1 Problem Statement

SDLC Orchestrator's Multi-Agent Team Engine (ADR-056, Sprint 176-179) supports direct Ollama and Anthropic provider calls via `agent_invoker.py`. However, three capabilities are missing:

| # | Gap | Impact |
|---|-----|--------|
| 1 | **No structured output** | Agent responses require regex parsing; no guaranteed JSON schema compliance |
| 2 | **No workflow graphs** | Reflection loops (Coder ↔ Reviewer) and SDLC pipelines (G0→G4) require manual orchestration |
| 3 | **No unified tool calling** | Each provider has different tool calling APIs; adding a provider means writing new tool integration |

### 1.2 CEO Research

The CEO and domain experts produced comprehensive research in `mas/` directory (~70 pages + 5 n8n workflows):

- `mas/01-SDLC-ORCHESTRATOR-ANALYSIS.md` — ADR-056 gap analysis
- `mas/02-MAS-ARCHITECTURE.md` — 12 agent roles, 3 orchestration patterns
- `mas/03-LANGCHAIN-IMPLEMENTATION.md` — Working LangChain code samples
- `mas/n8n/` — 5 production-ready n8n workflow JSONs

### 1.3 Existing Infrastructure

LangChain is already a dependency in `backend/requirements/enterprise.txt`:

```
langchain==0.3.27          # line 10
langchain-core==0.3.72     # line 11
langchain-google-genai==2.1.9  # line 12
langchain-text-splitters==0.3.9  # line 13
langsmith==0.4.11          # line 14
```

Missing packages (must add): `langchain-anthropic`, `langchain-openai`, `langchain-community`, `langgraph`.

### 1.4 ADR-064 Constraint

ADR-064 D-064-02 states:

> "Native Ollama `/api/chat` tools parameter, **NOT LangChain**."

This applies to the **chat-first facade** (Layer A). ADR-066 scopes LangChain to **multi-agent orchestration** (EP-07, Layer 4) only. See Section 4 for the explicit exemption.

---

## 2. Decision

### 2.1 Option Selected: LangChain as Provider Plugin + LangGraph Durable Workflows

Add LangChain as an optional provider in `agent_invoker.py._call_provider()` for multi-agent orchestration (EP-07). Add LangGraph for durable async workflow graphs (reflection loop). n8n integration DEFERRED pending legal review.

**Rating**: 8.5/10 (CTO) after 5-expert review + CTO verification.

### 2.2 Architecture

```
EXISTING (UNCHANGED):
  Layer A: Chat-First Facade (ADR-064)
    • chat_command_router.py — Native Ollama /api/chat tools (D-064-02)
    • magic_link_service.py — OOB auth

EXTENDED (ADR-066):
  Layer 4: Multi-Agent Orchestration (EP-07)
    • agent_invoker.py — NEW: _call_langchain() branch
    • langchain_provider.py — NEW: ChatOllama/Anthropic/OpenAI wrapper
    • langchain_tool_registry.py — NEW: 5 SDLC StructuredTools
    • workflows/reflection_graph.py — NEW: LangGraph StateGraph
    • workflow_resumer.py — NEW: Async resume (pub/sub + reconciler)

UNCHANGED:
  Lane Queue (SKIP LOCKED) — LangGraph nodes are queue CLIENTS
  Security (input_sanitizer + output_scrubber + shell_guard)
  Provider Failover (6-reason abort matrix + Redis cooldowns)
  14 Non-Negotiables (ADR-056)
```

### 2.3 Why LangChain (for EP-07, not chat facade)

| Capability | Direct Ollama | LangChain | Benefit |
|-----------|---------------|-----------|---------|
| Structured Output | Regex parsing | `with_structured_output()` Pydantic | Guaranteed schema |
| Tool Calling | Per-provider implementation | Unified `StructuredTool` interface | 1 implementation for N providers |
| Token Counting | Manual parsing | Callbacks (`on_llm_end`) | Automatic across all providers |
| Streaming | Per-provider `stream=True` | `astream()` with cancellation | Uniform interruption |
| Output Parsing | Manual JSON extraction | `PydanticOutputParser` | Type-safe responses |

---

## 3. Locked Decisions (6)

### D-066-01: LangChain is PROVIDER ONLY — Control Plane is TRUTH

LangChain/LangGraph state is DRAFT. Postgres (gate_service, evidence_service, approval_service) is TRUTH.

**Invariant**: Before ANY decision node in a LangGraph workflow, the workflow MUST call `GET /gates/{id}/actions` to refresh truth from the control plane.

LangChain CANNOT:
- Become SSOT for gate status, evidence validity, or permissions
- Bypass the control plane REST API
- Make direct database queries

### D-066-02: Workflow State in `agent_conversations.metadata_` JSONB

Workflow state is stored in the existing `agent_conversations.metadata_` JSONB column. No new table.

**Schema** (`WorkflowMetadata` Pydantic model):

```python
class WorkflowMetadata(BaseModel):
    workflow_schema_version: str = "1.0.0"
    workflow_id: UUID
    workflow_type: Literal["reflection"]  # Extend later
    status: Literal["waiting", "running", "completed", "failed"]
    current_node: str
    iteration: int = 0
    next_wakeup_at: Optional[datetime] = None
    idempotency_keys: dict[str, str] = {}
    version: int = 1  # OCC (Optimistic Concurrency Control)
    state: dict = {}
```

**Constraints**:
- Size limit: 64KB max. Store pointers (evidence_id for artifacts), not payloads.
- Required partial index: `(metadata_->>'status', metadata_->>'next_wakeup_at') WHERE metadata_->>'workflow_id' IS NOT NULL`
- Pydantic validation required before every read/write.
- `version` field incremented atomically for OCC — concurrent resume → 1 pass, 1 no-op.

### D-066-03: All LangGraph Nodes Use `enqueue_async()`

LangGraph nodes MUST use `team_orchestrator.enqueue_async()` which returns immediately. NEVER block waiting for lane completion.

```
Node → enqueue_async() → SAVE checkpoint → RETURN immediately
                ↓
        Agent completes in lane (SKIP LOCKED preserved)
                ↓
        WorkflowResumer → load checkpoint → resume next node
```

This preserves ADR-056 D-056-02 (Lane Contract: DB is truth, Redis is notify-only).

### D-066-04: n8n DEFERRED

n8n integration is DEFERRED pending legal review of the Sustainable Use License (fair-code).

**Options for future consideration**:
- Option A: Enterprise deploy only (customer VPC, not SaaS)
- Option B: Buy n8n Enterprise license (~$5K/year)
- Option C: Replace with Temporal.io (MIT) or Windmill (Apache 2.0)
- Option D (RECOMMENDED): Skip n8n — LangGraph sufficient, React Flow for visualization

**Legal sign-off required before ANY n8n code is written.**

### D-066-05: WorkflowResumer as Single Instance

WorkflowResumer MUST run as a single instance — either a separate Docker service with `replicas: 1` or via Redis leader election with 30s TTL.

**NEVER run WorkflowResumer in `main.py` with multi-worker uvicorn** — this causes duplicate processing.

**Dual-path design**:
- **Fast path**: Redis pub/sub listener for immediate resume
- **Fallback**: Reconciler polling every 30s for missed events (pub/sub is not durable)
- **Stuck detection**: Workflows in `waiting` status for >5 minutes → auto-resume

### D-066-06: End-to-End Idempotency

Idempotency is required at 3 places:

| Layer | Key | Behavior |
|-------|-----|----------|
| Workflow step | `(workflow_id, step_id)` | Step already completed → no-op |
| Message enqueue | `idempotency_key` param | Already enqueued → return existing message_id |
| Control plane | `X-Idempotency-Key` header | Already processed → return cached response (Redis, 1hr TTL) |

---

## 4. Orchestration Boundaries (ADR-064 Exemption)

### 4.1 Scope Separation

| Scope | Technology | ADR |
|-------|-----------|-----|
| Chat-first facade (Layer A) | Native Ollama `/api/chat` tools | ADR-064 D-064-02 |
| Multi-agent orchestration (EP-07, Layer 4) | LangChain + LangGraph | ADR-066 (this document) |

### 4.2 Exemption Clause

> **D-064-02 "NOT LangChain" applies to the chat-first facade only.** Multi-agent orchestration (EP-07) may use LangChain under ADR-066, scoped to:
>
> - Provider plugin in `agent_invoker.py._call_provider()`
> - Workflow graphs in `workflows/reflection_graph.py`
> - Tool calling in `langchain_tool_registry.py`
> - Fallback chains via LangChain's built-in retry/fallback

LangChain MUST NOT be used in:
- `chat_command_router.py` (ADR-064 scope)
- `ott_gateway.py` or any OTT channel processing
- Any Layer A component

### 4.3 Workflow Changes = Code Changes

All workflow definitions (LangGraph graph definitions, future n8n JSONs) MUST be:
- Versioned in Git
- PR reviewed and approved
- Deployed via promotion path (dev → staging → prod)
- Audit logged per workflow run (correlation_id)

### 4.4 Multi-tenant Isolation

All workflow events MUST include:
- `org_id` + `project_id`
- Scope verification before processing
- Tenant-specific rate limits (inherited from existing `UsageLimitsMiddleware`)

---

## 5. Consequences

### 5.1 Positive

- **Structured output** eliminates regex parsing for agent responses
- **Unified tool calling** — 1 StructuredTool definition serves all providers
- **Durable workflows** — reflection loops survive crashes via Postgres checkpoint
- **Zero disruption** — feature-flagged, existing behavior unchanged when disabled
- **Reuses existing** — `agent_conversations.metadata_` JSONB, `magic_link_service.py`, `tool_context.py`

### 5.2 Negative

- **+4 optional deps** (`langgraph`, `langchain-anthropic`, `langchain-openai`, `langchain-community`)
- **+1 Docker service** (`workflow_resumer` with `replicas: 1`)
- **+1 Alembic migration** (partial index on `metadata_` JSONB)
- **LangChain version drift risk** — must monitor 0.3.x → 1.x migration timeline

### 5.3 Costs

| Item | LOC | Sprint |
|------|-----|--------|
| Phase 1: LangChain Provider Plugin | ~850 | 205 |
| Phase 2: LangGraph Durable Workflows | ~1,200 | 206 |
| **Total** | **~2,050** | **2 sprints** |

---

## 6. Phase 3 Legal Checklist (n8n)

| # | Item | Status |
|---|------|--------|
| 1 | Identify n8n license type (Sustainable Use License, formerly fair-code) | Done |
| 2 | Legal review: SaaS deployment permitted? | Pending |
| 3 | Legal review: customer VPC deployment permitted? | Pending |
| 4 | Cost comparison: n8n Enterprise vs Temporal.io vs Windmill | Pending |
| 5 | CTO decision: proceed or skip (Option D recommended) | Pending |

---

## 7. References

- ADR-056: Multi-Agent Team Engine (4 locked decisions, 14 non-negotiables)
- ADR-058: ZeroClaw Best Practice Adoption (security hardening)
- ADR-064: Chat-First Facade Option D+ (D-064-02 "NOT LangChain" for chat)
- ADR-065: Unified Tier Resolution (tier enforcement)
- EP-07: Multi-Agent Team Engine (epic)
- FR-045: LangChain Provider Plugin (this ADR)
- FR-046: LangGraph Reflection Workflow (this ADR)
- `mas/README.md`: CEO MAS research overview
- `mas/03-LANGCHAIN-IMPLEMENTATION.md`: Working LangChain code samples
- 5-Expert Panel Consolidated Synthesis (Feb 2026)
