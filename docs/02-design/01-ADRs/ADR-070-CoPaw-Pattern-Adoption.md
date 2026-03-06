---
sdlc_version: "6.1.1"
document_type: "Architecture Decision Record"
status: "APPROVED"
sprint: "218-221"
spec_id: "ADR-070"
tier: "PROFESSIONAL"
stage: "02 - Design"
owner: "CTO"
---

# ADR-070 — CoPaw/AgentScope Pattern Adoption for EP-07

**Status**: APPROVED (CTO Verdict 9/10 — PDR-001 synthesis)
**Date**: March 2026
**Author**: PM + Architect + CTO
**Sprint**: Sprint 218-221
**Framework**: SDLC 6.1.1
**Supersedes**: None
**References**: ADR-056 (Multi-Agent Team Engine), ADR-069 (MTClaw Best Practice Adoption), PDR-001 (CoPaw Porting Decision)

---

## 1. Context

### 1.1 Problem Statement

EP-07 Multi-Agent Team Engine (ADR-056) provides the control plane — lane-based queue, SKIP LOCKED, OPA policy gates, evidence trail, provider failover. However, 6 capability gaps remain:

| Gap | Impact | Pattern Source |
|-----|--------|---------------|
| No skill access control (per-agent grants) | All agents see all skills regardless of role | CoPaw skills/loader.go |
| No full-text skill search | Agent cannot discover relevant skills by query | CoPaw skills/search.go |
| No agent liveness monitoring | Stalled agents not detected/recovered | CoPaw heartbeat system |
| No cross-agent shared workspace | Agents cannot share artifacts within a conversation | CoPaw shared memory |
| No structured approval feedback | Human approvals are binary (approve/reject) — no feedback text | CoPaw human-in-the-loop |
| No group consensus mechanism | Multi-agent voting/deliberation not supported | AgentScope MsgHub + CoPaw voting |

### 1.2 Research — CoPaw and AgentScope

**CoPaw** (github.com/agentscope-ai/CoPaw): Personal AI assistant, Apache 2.0, Python/FastAPI.
- SKILL.md 3-directory lifecycle, 7 OTT channels, memory compaction at 70%, cron/heartbeat
- Same tech stack as SDLC Orchestrator (Python, FastAPI, Redis)
- Single-user focused — no multi-tenancy

**AgentScope** (github.com/agentscope-ai/agentscope): Multi-agent framework, Apache 2.0.
- MsgHub for broadcast multi-agent communication
- Pipeline DSL (Sequential + Fanout)
- ReActAgent execution loop
- NO multi-tenancy built-in

### 1.3 Expert Analysis (PDR-001)

Two independent experts evaluated adoption options:

| Expert | Position | Verdict |
|--------|----------|---------|
| Expert A | Replace EP-07 with AgentScope Runtime as control plane | **REJECTED** — migration risk high, EP-07 is competitive moat |
| Expert B | Keep EP-07, use CoPaw as pattern source, AgentScope as execution concept | **ACCEPTED** — zero migration risk, 100% additive |

---

## 2. Decision

### 2.1 Core Decision

**EP-07 remains the Control Plane.** CoPaw provides 6 patterns ported as additive extensions. AgentScope provides conceptual patterns only (MsgHub broadcast). Zero migration risk.

### 2.2 Invariants (Cannot Be Violated)

1. EP-07 lane queue + SKIP LOCKED + OPA + evidence trail + failover = **unchanged**
2. 74 existing tests (S216+S217) must continue passing after each sprint
3. ADR-056 contracts preserved — **no breaking changes**
4. Gate authority G0-G4 belongs to EP-07; **consensus is advisory only** (cannot bypass gates)

### 2.3 EP-07 ↔ AgentScope Interface Contract

| Step | Owner | Description |
|------|-------|-------------|
| 1. Dispatch | EP-07 (unchanged) | Send task with `agent_assignment` block: agent_type, toolkit, skills_grants, memory_namespace |
| 2. Execute | AgentScope pattern (new) | ReActAgent.execute(task) → runs with skills + memory + tools |
| 3. Return | AgentScope → EP-07 | Returns: result + evidence + gate_signals + audit_trace |
| 4. Gate evaluate | EP-07 (unchanged) | Consumes gate_signals → PASS/FAIL → advance lane |

### 2.4 Six Patterns Adopted

| # | Pattern | Source | Sprint | New Tables |
|---|---------|--------|--------|------------|
| P1 | Message Protocol (broadcast filter) | AgentScope Msg | S218 | — |
| P2 | Group Consensus (voting, quorum) | CoPaw + MsgHub | S221 | consensus_sessions, consensus_votes |
| P3 | Skills Engine (grants + tsvector search) | CoPaw skills | S218 | skill_agent_grants |
| P4 | Human-in-the-Loop (approval feedback) | CoPaw | S220 | — |
| P5 | Shared Memory (cross-agent workspace) | CoPaw ReMe | S219-S220 | shared_workspace_items |
| P6 | Agent Liveness (heartbeat, recovery) | CoPaw heartbeat | S219 | — |

---

## 3. Consequences

### 3.1 Positive

- **Zero migration risk**: All patterns are additive — no existing code modified in breaking ways
- **6 capability gaps closed**: Skills access control, search, liveness, workspace, feedback, consensus
- **~2,100 LOC total**: Achievable in 4 sprints at current velocity (~500 LOC/sprint)
- **Reuse existing infrastructure**: Redis (heartbeat keys), PostgreSQL (tsvector, JSONB), lane queue (broadcast)

### 3.2 Negative

- **4 new tables**: Additional schema complexity (skill_agent_grants, shared_workspace_items, consensus_sessions, consensus_votes)
- **context_injector.py grows**: From 4 builders to 7 builders — may need refactoring after S221
- **Consensus is advisory only**: Development teams expecting binding votes will need education

### 3.3 Risks

| Risk | Probability | Mitigation |
|------|-------------|------------|
| S219 LOC exceeds velocity (~800 LOC) | Medium | Defer `escalate_to_lead` conflict strategy to S220 |
| S220/S221 parallel merge conflict on context_injector.py | Low | Feature branches + lazy import for consensus builder |
| Workspace version=-1 soft delete queries | Low | All queries include `WHERE version > 0` |

---

## 4. Alternatives Considered

### 4.1 Replace EP-07 with AgentScope Runtime (Expert A — REJECTED)

- **Effort**: ~Phase 1: 80h, Phase 2: 60h
- **Risk**: High — EP-07 is the competitive moat (lane queue, OPA gates, evidence trail)
- **Rejected because**: Migration risk too high, EP-07 already handles orchestration

### 4.2 Full CoPaw Code Port (REJECTED)

- **Problem**: CoPaw is single-user, file-based storage (no DB). Direct code port would require rewriting for multi-tenancy.
- **Rejected because**: Pattern extraction is sufficient; code structure doesn't match our DB-first architecture

### 4.3 AgentScope as Full Execution Engine (REJECTED)

- **Problem**: AgentScope has no multi-tenancy, no OPA integration, no evidence trail
- **Rejected because**: Would duplicate EP-07 capabilities while missing governance features

---

## 5. Implementation Timeline

```
S217 ✅ → S218 (grants + search + metadata)
                ↓
           S219 (heartbeat + workspace) + ADR-072
              ↓         ↓
         S220 (memory)  S221 (consensus)
         [parallel]     [parallel]
```

Total: ~8 weeks with S220/S221 parallelization.
Acceptance gate: 229 cumulative tests passing.

---

## 6. Related ADRs

- **ADR-072** (Sprint 219): Shared Workspace Schema — 3 conflict resolution strategies, parent-child isolation
- **ADR-071** (Deferred S222+): Channel Adapter Interface — OTT channels unified adapter
