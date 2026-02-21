---
sdlc_version: "6.1.0"
document_type: "Business Case"
status: "PROPOSED"
sprint: "189-192"
spec_id: "BC-064"
tier: "ALL"
stage: "00 - Foundation"
---

# Chat-First Governance Loop — Business Case

**Status**: PROPOSED (Sprint 189-192)
**Date**: February 21, 2026
**Author**: CTO Nguyen Quoc Huy
**Framework**: SDLC 6.1.0 (ALL tiers)
**Gate**: G0.1 Foundation Ready
**References**: ADR-064 (Option D+), EP-08, Product Roadmap v9.0.0, BRD v4.0.0

---

## 1. Problem Statement

### 1.1 Current State

After 188 sprints and GA launch (v2.0.0-ga), the SDLC Orchestrator has **strong enterprise infrastructure** but a **UX layer that fails to deliver value faster than the manual alternative**:

- **35+ dashboard pages**, 91 frontend routes, 688 API endpoints — cognitive overload
- **28% of backend service code is frozen/unused** (~18.3K LOC identified for deletion)
- **CEO manually plays CEO/CPO/CTO oversight roles** across multiple repos (Bflow, NQH-Bot)
- Platform is **NOT faster** than CEO manually using Claude Code + SDLC Framework docs
- "CEO Liberation" promise — the core product thesis — remains unfulfilled

### 1.2 Gap Analysis

| Capability | Current State | Required State | Gap |
|-----------|---------------|---------------|-----|
| Governance UX | 35+ dashboard pages | Single chat thread | CRITICAL |
| CEO delegation | Manual oversight | Automated governance loop | CRITICAL |
| Code health | 28% frozen/unused code | Clean, maintainable codebase | HIGH |
| Gate approval (OTT) | Requires web login | Magic Link single-click | HIGH |
| Evidence submission | Web upload only | Chat + file attachment | MEDIUM |
| SDLC Framework realization | Buried in UI complexity | Chat = the framework UX | MEDIUM |

### 1.3 Impact of Not Solving

- **CEO remains bottleneck**: Cannot delegate governance to PMs via current UX
- **Product-market fit risk**: If manual AI + docs is faster, platform has zero value-add
- **Technical debt compounds**: 18.3K LOC of frozen code increases maintenance burden
- **Competitive disadvantage**: Simpler chat-based tools (TinySDLC, 3.7K LOC) feel more effective
- **GA launch investment at risk**: $564K + 188 sprints of engineering delivers a product CEO won't use

---

## 2. Proposed Solution

Build the **Chat-First Governance Loop** as a thin LLM Function Calling facade (~500 LOC new) on top of the existing Enterprise Control Plane, then aggressively clean up ~18.3K LOC of dead code.

**Architecture Decision**: Option D+ (Chat-First Facade) — chosen unanimously by 7/7 expert panel. Approved over Option C (OpenClaw rebuild, $60-90K, 12-18 sprints).

**Key Insight**: The problem is UX/focus, not architecture. Existing infrastructure (agent_team services, OTT gateway, OPA, audit logs, tier enforcement) is production-ready. A chat command router + cleanup fixes it.

### North Star Loop

```
@mention → Gate Actions → Evidence → Approve (Magic Link) → Audit Export
```

### Architecture (ADR-064, 4 Locked Decisions)

| Decision | Rule |
|----------|------|
| D-064-01 | Chat = UX layer, Control Plane = truth |
| D-064-02 | LLM Function Calling with Pydantic validation (10 tools max) |
| D-064-03 | Actions Contract: bot reads `/gates/{id}/actions`, NEVER decides |
| D-064-04 | Magic Link = OOB auth (HMAC-SHA256, 5-min TTL, single-use) |

### 3 Invariants

| ID | Invariant |
|----|-----------|
| INV-01 | Agent NEVER decides gate truth — reads from Control Plane |
| INV-02 | PRO/ENTERPRISE = enforcement-first (tier gate middleware enforced) |
| INV-03 | Every chat approval → immutable audit_logs row |

### What Already Exists (Leveraged, Not Rebuilt)

| Component | LOC | Status |
|-----------|-----|--------|
| agent_team/ (18 services) | 4,777 | Production |
| agent_bridge/ (4 OTT channels) | 833 | Production |
| ott_gateway.py (Telegram/Zalo/Teams/Slack) | 233 | Production |
| mention_parser.py (@mention routing) | 206 | Production |
| SAML SSO + GDPR + Audit logs | ~2,143 | Production |
| Usage limits + Tier gate middleware | 845 | Production |

---

## 3. Business Value

### 3.1 Revenue Impact

| Metric | Without Chat-First | With Chat-First | Delta |
|--------|-------------------|-----------------|-------|
| CEO governance delegation | Blocked | Automated via chat | Unblocks entire product thesis |
| Time to first governance loop | 30+ min (35 pages) | <10 min (single chat) | 3x improvement |
| OTT channel governance | View-only | Full CRUD + approve | Unlocks mobile-first Vietnam market |
| Codebase maintenance cost | ~18K LOC dead weight | Clean, focused codebase | -28% maintenance burden |
| Platform vs manual AI | Platform slower | Platform faster | Product-market fit achieved |

### 3.2 Operational Impact

| Metric | Without Chat-First | With Chat-First | Delta |
|--------|-------------------|-----------------|-------|
| CEO time on governance | 4-8 hrs/week manual | <1 hr/week via chat | 75-87% time reduction |
| PM governance capability | Requires CEO coaching | Self-serve via chat | Team scaling unblocked |
| Frontend complexity | 35+ pages, 91 routes | 5 core pages + chat | 85% reduction in UX surface |
| Dead code incidents | 18.3K LOC risk surface | Deleted | Risk eliminated |

### 3.3 Strategic Value

- **CEO Liberation**: The founding thesis — any PM achieves CEO-level governance via chat
- **Framework Realization**: SDLC Framework gate/evidence workflow becomes the chat UX, not a hidden feature
- **Codebase Health**: Sprint 190 cleanup positions platform for sustainable growth
- **Competitive Moat**: Dynamic chat governance > static dashboards > manual AI + docs
- **Option Value**: Chat layer enables future AI agent workflows (Initializer → Coder → Reviewer → Gate)

---

## 4. Cost Estimate

### 4.1 Development Cost

| Item | Effort | Cost (at $80/hr) |
|------|--------|------------------|
| chat_command_router.py (~300 LOC) | 24 hrs | $1,920 |
| magic_link_service.py (~150 LOC) | 12 hrs | $960 |
| Gate Actions requires_oob_auth (~25 LOC) | 4 hrs | $320 |
| OTT gateway dedupe (~30 LOC) | 4 hrs | $320 |
| Config + wiring | 4 hrs | $320 |
| Acceptance tests (6 test cases) | 16 hrs | $1,280 |
| Sprint 190: Aggressive cleanup (~18.3K LOC deletion) | 40 hrs | $3,200 |
| Sprint 190: Dashboard simplification (35→5 pages) | 24 hrs | $1,920 |
| Sprint 191-192: Enterprise hardening (Teams/Slack, SSO, agent chain) | 80 hrs | $6,400 |
| Documentation (SDLC compliance) | 16 hrs | $1,280 |
| Integration tests + E2E | 24 hrs | $1,920 |
| Buffer (10%) | 25 hrs | $2,000 |
| **Total** | **273 hrs** | **~$22,000** |

### 4.2 Ongoing Cost

| Item | Monthly Cost |
|------|-------------|
| Ollama inference (qwen3:32b, primary) | $50 (existing) |
| Claude Haiku fallback | ~$20 (only on Ollama failure) |
| Redis (magic link + dedupe) | Existing infrastructure |
| PostgreSQL (no new tables) | Existing infrastructure |
| **Total incremental** | **~$70/mo** |

### 4.3 ROI Calculation

- **Investment**: ~$22,000 (one-time) + $840/yr (incremental infra)
- **Comparison**: Option C (OpenClaw rebuild) would cost $60-90K over 12-18 sprints
- **Savings vs Option C**: $38-68K saved + 7-13 sprints saved
- **CEO Time Recovery**: 3-7 hrs/week × 52 weeks × $200/hr = $31,200-72,800/yr
- **Codebase Maintenance Savings**: -18.3K LOC × estimated $2/LOC/yr = ~$36,600/yr reduced maintenance
- **Payback Period**: < 2 months (CEO time savings alone)
- **3-Year ROI**: >15x (conservative, CEO time + maintenance savings only)

---

## 5. Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Ollama Vietnamese tool calling quality insufficient | MEDIUM | HIGH | Day 1 PoC test (GO/NO-GO); fallback: Claude Haiku |
| Cleanup breaks hidden dependencies | LOW | HIGH | Feature-flag first (Sprint 190); delete after 1 sprint observation |
| Chat UX slower than expected for complex workflows | LOW | MEDIUM | Break-glass web approve (Sprint 192, feature-flagged) |
| Magic Link token security | LOW | CRITICAL | HMAC-SHA256 + 5-min TTL + single-use + async Redis |
| LLM hallucinating gate actions | MEDIUM | HIGH | Bounded function calling (10 tools max); Pydantic validation; Actions Contract (bot reads, never decides) |
| Team resistance to dashboard removal | LOW | LOW | Feature-flag (not delete) in Sprint 190; only delete in Sprint 191 after validation |
| Ollama latency on production hardware | LOW | MEDIUM | run_in_threadpool wrapping (T-08); Claude fallback chain |
| OTT webhook replay attacks | MEDIUM | MEDIUM | Redis-based event_id deduplication at gateway (T-04) |
| Sprint scope creep (4 sprints) | MEDIUM | MEDIUM | Strict Phase 0 GO/NO-GO gate after Sprint 189 |
| Enterprise customers need web approval | LOW | MEDIUM | Break-glass admin button (Sprint 192, feature-flagged) |

---

## 6. Success Criteria (Gate G0.1)

### Phase 0 PoC (Sprint 189, GO/NO-GO)

| # | Criterion | Target | Measurement |
|---|-----------|--------|-------------|
| 1 | Happy path governance loop | <10 min, ≤8 interactions, OPA decision in audit_logs | E2E test |
| 2 | Actions contract enforced | Router NEVER bypasses OPA. Bot explains "why not" for blocked actions | Unit test |
| 3 | Evidence integrity | SHA256 server-side. User selects type. Hash mismatch → reject | Integration test |
| 4 | Non-happy paths (6 cases) | DRAFT approve→409; duplicate→idempotent; no perm→403; hash mismatch→reject; replay→dedupe; concurrent→consistent | E2E test |
| 5 | Developer bootstrap | bootstrap_dev.sh → admin + sample project → <5 min | Manual test |
| 6 | Bounded LLM | Invalid tool→clarification; Pydantic fail→retry 2x then error; hallucinated gate_id→rejected | Unit test |

### Post-Cleanup (Sprint 190)

| Criterion | Target |
|-----------|--------|
| ruff check backend/ | 0 errors |
| pytest backend/tests/ | All green |
| Backend LOC reduction | ~120K → ~100K |
| Dashboard default view | 5 core pages (from 35+) |

### Enterprise Hardening (Sprint 191-192)

| Criterion | Target |
|-----------|--------|
| Teams + Slack parity | Full governance loop via enterprise OTT |
| SSO + Magic Link integration | SAML 2.0 → Magic Link for enterprise users |
| Agent workflow chain | @pm → @architect → @coder → @reviewer → gate |
| Compliance export | @pm compliance report → audit PDF |

---

## 7. Timeline

| Sprint | Focus | Key Deliverables | LOC Impact |
|--------|-------|-----------------|------------|
| 189 | Chat Command Router + Magic Link | chat_command_router.py, magic_link_service.py, requires_oob_auth, 6 acceptance tests | +~500 LOC |
| 190 | Aggressive Cleanup | Delete ~18.3K LOC frozen code, feature-flag 25+ dashboard pages, DB table deprecation | -~18,300 LOC |
| 191 | Enterprise Channels + SSO | Teams/Slack parity, SAML→Magic Link, agent workflow chain, GitHub evidence auto-capture | +~800 LOC |
| 192 | Compliance + Hardening | Compliance export, dashboard read-only mode, break-glass web approve, performance tuning | +~500 LOC |

**Net Impact**: +~1,800 LOC new — ~18,300 LOC deleted = **-16,500 LOC net** (cleaner, focused codebase)

---

## 8. CTO Conditions (11 Non-Negotiables)

All 11 conditions from ADR-064 review MUST be enforced during implementation:

### Technical Conditions (T-01 through T-09)

| ID | Condition |
|----|-----------|
| T-01 | Bounded function calling: 10 tools max, Pydantic schema per tool |
| T-02 | Native Ollama `/api/chat` (NOT LangChain or abstraction layers) |
| T-03 | Evidence type: user-selected (NOT inferred by LLM) |
| T-04 | Dedupe at gateway layer (Redis event_id, NOT at router) |
| T-05 | Async Redis client (import from app/utils/redis.py) |
| T-06 | OPA decision must persist to audit_logs table |
| T-07 | Alembic migration downgrade = raise NotImplementedError |
| T-08 | run_in_threadpool for Ollama HTTP calls |
| T-09 | run_in_threadpool for ProjectService sync methods |

### Architecture Conditions (A-01 through A-04)

| ID | Condition |
|----|-----------|
| A-01 | requires_oob_auth is new code (not refactoring existing field) |
| A-02 | Correct async Redis import (not sync redis.Redis) |
| A-03 | OPA→audit_logs uses proper column mapping |
| A-04 | All code samples in Sprint plan are pseudocode (implementation may differ) |

---

## 9. Approval

| Role | Name | Decision | Date |
|------|------|----------|------|
| CTO | Nguyen Quoc Huy | APPROVED (with 11 conditions) | Feb 21, 2026 |
| Expert Panel | 7 domain experts | APPROVED (7/7 vote for Option D+) | Feb 21, 2026 |
| CPO | — | PENDING | — |
| CEO | — | PENDING | — |

---

*BC-064 — Chat-First Governance Loop Business Case*
*SDLC Orchestrator — Operating System for Software 3.0*
*"Chat = UX. Control Plane = Truth. Ship the loop, delete the noise."*
