---
sdlc_version: "6.1.0"
document_type: "Architecture Decision Record"
status: "APPROVED"
sprint: "189"
spec_id: "ADR-064"
tier: "ALL"
stage: "02 - Design"
owner: "CTO"
approved_by: "CEO + CTO + CPO"
approved_date: "2026-02-21"
---

# ADR-064 — Chat-First Facade (Option D+)

**Status**: APPROVED (CEO + CTO + CPO, Feb 21, 2026)
**Sprint**: 189-192
**Deciders**: CEO, CTO, CPO
**Category**: Strategic Architecture + UX Pivot
**Supersedes**: N/A (new direction, complements ADR-059 Enterprise-First)
**Triggers**: EP-08 (Chat-First Governance Loop), FR-046, FR-047, FR-048
**Related**: ADR-056 (Multi-Agent), ADR-059 (Enterprise-First), ADR-060 (OTT Channels)

---

## 1. Context

### 1.1 Triggering Event

After 188 sprints, the CEO identified a critical UX problem:

> "The SDLC Orchestrator is hard to use and not faster than manually having AI tools read the SDLC Framework docs. TinySDLC (3.7K LOC, chat-native) feels simpler and more effective."

The platform has strong enterprise infrastructure (OTT channels, SAML SSO, GDPR, audit logs, usage limits, multi-agent orchestration) but the **UX layer** fails to make this accessible. Users interact with 35+ dashboard pages instead of a simple governance loop.

### 1.2 Core Problem

The CEO currently manually oversees CEO/CPO/CTO roles across multiple repos (Bflow, NQH-Bot). The platform should **encode these governance patterns** into automated loops so any PM can achieve CEO-level oversight via chat `@mention` commands.

**Problem decomposition**:

| # | Problem | Root Cause |
|---|---------|------------|
| 1 | Product not faster than manual AI | No chat-native governance loop |
| 2 | Hard to use | 35+ dashboard pages, no single UX thread |
| 3 | Doesn't realize SDLC Framework clearly | Framework concepts buried in UI complexity |
| 4 | CEO manually plays multiple roles | Governance patterns not encoded in platform |

### 1.3 Options Evaluated

| Option | Description | Cost | Timeline | Expert Vote |
|--------|-------------|------|----------|-------------|
| **A** | Continue incrementally | $0 | Ongoing | 0/7 |
| **B** | Full rewrite on OpenClaw | $60-90K | 12-18 sprints | 0/7 |
| **C** | OpenClaw-First rebuild | $60-90K | 12-18 sprints | 3.5/7 (initial) |
| **D+ (CHOSEN)** | Chat-First Facade + Cleanup | ~$24K | 5 sprints | **7/7 (final)** |

### 1.4 What Already Exists (Re-Audit)

The Orchestrator already has substantial infrastructure that Option D+ leverages:

| Component | LOC | Status |
|-----------|-----|--------|
| agent_team/ (18 services) | 4,777 | Production |
| agent_bridge/ (6 services, 4 OTT channels) | 833 | Production |
| ott_gateway.py (Telegram/Zalo/Teams/Slack) | 233 | Production |
| mention_parser.py (@mention routing) | 206 | Production |
| protocol_adapter.py (OrchestratorMessage) | 201 | Production |
| SAML SSO | 818 | Production |
| GDPR compliance | 925 | Production |
| Audit logs (immutable) | ~400 | Production |
| Usage limits middleware | 431 | Production |
| Tier gate middleware | 414 | Production |

**Key insight**: The problem is UX/focus, not architecture. A chat command router (~300 LOC) + cleanup (~18K LOC deleted) fixes it.

---

## 2. Decision

**Adopt Option D+ (Chat-First Facade)**: Add a thin LLM Function Calling layer on top of the existing enterprise control plane, wire it through the existing OTT gateway, and aggressively remove ~18K LOC of frozen/unused code.

### 2.1 Locked Decisions (4)

| # | Decision | Rationale |
|---|----------|-----------|
| D-064-01 | **Chat = UX, Control Plane = Truth** | Agent layer NEVER decides gate status, evidence validity, or permissions. All mutations go through existing REST API services. |
| D-064-02 | **LLM Function Calling, NOT regex** | Vietnamese natural language ("Ê @pm, tạo dự án X đi") requires LLM intent extraction. Native Ollama `/api/chat` tools parameter, NOT LangChain. |
| D-064-03 | **Actions Contract pattern** | `GET /gates/{id}/actions` is the SSOT for what a user can do. Chat router ALWAYS consults `/actions` before suggesting mutations. Router NEVER bypasses. |
| D-064-04 | **Magic Link for OOB auth** | Gate approvals via chat require out-of-band authentication. Single-use HMAC-signed tokens, 5-min expiry, triggered by `requires_oob_auth` in Actions response. |

### 2.2 Architecture

```
LAYER A: Chat Interface (NEW — ~500 LOC)
  • chat_command_router.py — Bounded LLM Function Calling + Pydantic validation
  • magic_link_service.py — HMAC signed, /actions-triggered, 5-min expiry
  • Existing: ott_gateway.py (+ dedupe), mention_parser.py, protocol_adapter.py, 4 normalizers

LAYER B: Enterprise Control Plane (EXISTS — keep, harden)
  • /gates/{id}/actions — server decides permissions (Actions Contract, D-064-03)
  • /evidence — SHA256 server-side + required types enforcement
  • RBAC + RLS, OPA (separate container), audit logs (immutable)
  • Usage limits, tier enforcement, billing

LAYER C: Persistence (EXISTS — keep)
  • PostgreSQL (33+ tables), Redis, MinIO/S3, OPA
```

**Invariants**:
- INV-01: Agent layer NEVER decides truth. Truth = control plane (D-064-01).
- INV-02: PRO/ENTERPRISE = enforcement-first (OPA blocks), not convention.
- INV-03: Every chat approval creates an immutable audit log entry.

### 2.3 North Star Loop

```
@mention → Gate Actions → Evidence → Approve (Magic Link) → Audit Export
```

**Any feature NOT serving this loop → Freeze/Defer. Do NOT expand scope.**

---

## 3. Expert Corrections (13 Conditions)

### 3.1 Original Conditions (T-01 through T-09)

| # | Condition | Impact |
|---|-----------|--------|
| T-01 | Bounded Function Calling: allowlist + Pydantic validation, max 2 retries | Prevents hallucination bypass |
| T-02 | Native Ollama `/api/chat` tools parameter, NOT LangChain. Add NEW `async def chat()` method to `ollama_service.py` (~40 LOC) — existing `generate()` uses `/api/generate` which does NOT support tool calling | No unnecessary dependency; correct endpoint |
| T-03 | Evidence type = user-selected, NOT auto-detect | No compliance risk |
| T-04 | Dedupe at OTT gateway, NOT router | Full coverage |
| T-05 | Use `app/utils/redis.py` async client | Consistency with existing codebase |
| T-06 | OPA decision → audit_logs for PoC | Enforcement verification |
| T-07 | Migration downgrade = NotImplementedError | Honest about irreversibility |
| T-08 | `run_in_threadpool` for SYNC Ollama calls — `ollama_service.generate()` and `ollama_service.chat()` use `requests.post()` (sync). Must wrap with `starlette.concurrency.run_in_threadpool` in async context | Prevents event loop blocking |
| T-09 | `run_in_threadpool` for SYNC `ProjectService.create_project()` — uses sync `Session`. Must wrap with `run_in_threadpool` in async chat context | Prevents event loop blocking |

### 3.2 Addendum Conditions (A-01 through A-04)

| # | Condition | Impact |
|---|-----------|--------|
| A-01 | `requires_oob_auth` is NEW code (~20 LOC) in gate_service.py + gate.py | Budget Day 5 |
| A-02 | Use `app/utils/redis.py` async client (NOT `app/core/redis.py`) | Correct import path |
| A-03 | OPA decision → audit_logs for PoC, proper column Phase 1 | Lightweight solution |
| A-04 | Code samples are pseudocode; T-02 overrides | Implementation guidance |

---

## 4. Consequences

### 4.1 Positive

- **~$24K / 5 sprints** vs $60-90K / 12-18 sprints for Option C
- **~500 LOC new** + **~18K LOC deleted** = net reduction in codebase complexity
- **Reuses 100%** of existing enterprise infrastructure (OTT, SSO, audit, usage limits)
- **Validates cheaply**: 10-day PoC with GO/NO-GO gate before committing to full implementation
- **CEO governance patterns encoded**: any PM achieves CEO-level oversight via `@pm`, `@reviewer`

### 4.2 Negative

- **Day 1 risk**: Ollama Vietnamese tool calling is unproven (fallback: Claude Haiku)
- **Dashboard becomes secondary**: read-only mode may confuse existing internal users
- **Cleanup is irreversible**: deleted code cannot be easily restored (git history preserved)

### 4.3 Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Ollama Vietnamese tool calling fails | MEDIUM | HIGH | Day 1 test; fallback to Claude Haiku ($0.25/1M tokens) |
| Chat UX slower than dashboard for power users | LOW | MEDIUM | Break-glass web approve button (A-01, Phase 1) |
| Cleanup breaks undiscovered dependencies | LOW | HIGH | Feature-flag first, delete after verification |

---

## 5. Implementation Roadmap

| Phase | Sprint | Duration | Cost | Deliverables |
|-------|--------|----------|------|-------------|
| Phase 0 | PoC | 10 days | ~$4K | chat_command_router + magic_link_service + 6 acceptance tests |
| Phase 1 | 189-190 | 16 days | ~$10K | Chat governance loop + aggressive cleanup (~18K LOC) |
| Phase 2 | 191-192 | 16 days | ~$10K | Enterprise hardening + compliance export |
| Phase 3 | 193 | Checkpoint | — | Re-evaluate: chat vs dashboard preference, pilot readiness |

**GO/NO-GO Gate (Day 10 of PoC)**: All 6 acceptance tests pass → proceed. Any fail → document failure, re-evaluate Option C.

---

## 6. References

- ADR-056: Multi-Agent Team Engine (locked decisions D-056-01 through D-056-04)
- ADR-058: ZeroClaw Best Practice Adoption (security hardening)
- ADR-059: Enterprise-First Refocus (tier strategy)
- ADR-060: Route Registration Standards (OTT gateway)
- EP-08: Chat-First Governance Loop (epic)
- FR-046: Chat Command Router (functional requirement)
- FR-047: Magic Link OOB Authentication (functional requirement)
- FR-048: OTT Gateway Webhook Dedupe (functional requirement)
- STM-064: Chat-First Facade Security Threat Model
