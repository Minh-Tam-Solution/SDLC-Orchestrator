---
sdlc_version: "6.1.0"
document_type: "Business Case"
status: "PROPOSED"
sprint: "176-179"
spec_id: "BC-056"
tier: "PROFESSIONAL"
stage: "00 - Foundation"
---

# Multi-Agent Team Engine — Business Case

**Status**: PROPOSED (Sprint 176-179)
**Date**: February 2026
**Author**: CTO Nguyen Quoc Huy
**Framework**: SDLC 6.1.0 (PROFESSIONAL tier)
**Gate**: G0.1 Foundation Ready
**References**: ADR-056, ADR-058, EP-07, Product Roadmap v7.0.0

---

## 1. Problem Statement

### 1.1 Current State

SDLC Orchestrator's AI capabilities are **single-agent only**:

- **AI Council Service** (`ai_council_service.py`, 1,896 LOC) is FROZEN since Sprint 173
- Each AI task runs as an isolated request-response cycle — no agent collaboration
- EP-06 Codegen uses single-provider invocation without delegation or failover classification
- ADR-055 (Autonomous Codegen) requires Initializer → Coder → Reviewer agent chain, but **no infrastructure exists** for agent-to-agent communication

### 1.2 Gap Analysis

| Capability | Current State | Required State | Gap |
|-----------|---------------|---------------|-----|
| Agent-to-agent messaging | None | Lane-based queue with SKIP LOCKED | CRITICAL |
| Agent delegation (parent-child) | None | Depth-limited delegation chain | CRITICAL |
| Provider failover | Basic retry | 6-reason classification + abort matrix | HIGH |
| Token budget tracking | Per-request | Per-conversation with circuit breaker | HIGH |
| External input sanitization | None | 12-pattern regex + wrapping | HIGH |
| Shell command safety | None | 8 deny patterns + path restriction | HIGH |
| OTT channel integration | None | Plugin-based gateway (Telegram, Zalo) | MEDIUM |

### 1.3 Impact of Not Solving

- **ADR-055 Blocked**: Autonomous Codegen cannot function without multi-agent infrastructure
- **Vietnamese SME Pilot Delayed**: OTT integration (Telegram/Zalo) requires agent messaging
- **Security Risk**: No input sanitization or shell command guard for agent tool execution
- **Cost Overruns**: No per-conversation budget tracking enables runaway AI spend

---

## 2. Proposed Solution

Build the **Multi-Agent Team Engine (MATE)** as a foundational service layer in SDLC Orchestrator, absorbing production-proven patterns from three external codebases:

| Source | Patterns Absorbed | LOC Reference |
|--------|------------------|---------------|
| OpenClaw (36 channels, Node.js) | Lane queue, failover classification, session scoping | 7 patterns |
| TinyClaw (file-based queue, Python) | @mention routing, loop guards, SDLC roles | 7 patterns |
| Nanobot (~3,663 LOC, Python) | Tool context, shell guard, reflect step, error-as-string | 5 patterns |
| ZeroClaw (Rust, 12.5K stars, MIT) | Credential scrubbing, env scrubbing, history compaction, query classification | 4 patterns |

**Architecture Decision**: Option C (Hybrid) — absorb *patterns* (not code) into Python backend. Approved by dual expert review (A+ rating, 92% confidence).

**Sprint 179 Extension** (ADR-058): Research identified 4 additional ZeroClaw patterns for security hardening and operational optimization. CTO approved A (credential scrub), C (env scrub), B (history compaction), E (query classification). Deferred D (tool dispatch) and G (approval flow) to ADR-057.

---

## 3. Business Value

### 3.1 Revenue Impact

| Metric | Without MATE | With MATE | Delta |
|--------|-------------|-----------|-------|
| Autonomous Codegen launch | Blocked | Sprint 178 | Unblocks $50K EP-06 investment |
| Vietnamese SME pilot | CLI only | CLI + Telegram + Zalo | +3 channels, +200 potential users |
| Agent collaboration features | None | Multi-agent workflows | Premium tier differentiator |
| Provider cost optimization | ~$1,000/mo (Claude only) | ~$50/mo (Ollama primary) | 95% cost reduction |

### 3.2 Operational Impact

| Metric | Without MATE | With MATE | Delta |
|--------|-------------|-----------|-------|
| AI task failure handling | Manual retry | Auto-failover (6 reasons) | -80% manual intervention |
| Runaway cost incidents | Unbounded | Budget circuit breaker | $0 overrun |
| Security incidents (shell/prompt) | Unprotected | 20 deny patterns | Risk: CRITICAL → LOW |
| Agent loop incidents | Unbounded | 6 loop guards | Risk: HIGH → LOW |

### 3.3 Strategic Value

- **Platform Moat**: Dynamic agent collaboration is a key differentiator vs static AGENTS.md
- **OTT Market**: Vietnamese SME market uses Telegram/Zalo primarily — OTT gateway unlocks this segment
- **Ecosystem Play**: MATE enables TinySDLC ↔ Orchestrator interoperability via canonical protocol

---

## 4. Cost Estimate

### 4.1 Development Cost

| Item | Effort | Cost (at $80/hr) |
|------|--------|------------------|
| Backend services (12 files, ~1,500 LOC) | 40 hrs | $3,200 |
| Database schema (3 tables + migration) | 8 hrs | $640 |
| API endpoints (5 P0 + 6 P1) | 24 hrs | $1,920 |
| Unit tests (87 test cases) | 16 hrs | $1,280 |
| Integration tests (14 test cases) | 12 hrs | $960 |
| OTT Gateway scaffold (P1) | 20 hrs | $1,600 |
| Documentation (SDLC compliance) | 12 hrs | $960 |
| Sprint 179: ZeroClaw patterns (4 patterns, ~440 LOC) | 48 hrs | $3,840 |
| **Total** | **180 hrs** | **$14,400** |

### 4.2 Ongoing Cost

| Item | Monthly Cost |
|------|-------------|
| Ollama inference (primary provider) | $50 |
| Redis (cooldown state, pub/sub) | Existing infrastructure |
| PostgreSQL (3 new tables) | Existing infrastructure |
| **Total incremental** | **$50/mo** |

### 4.3 ROI Calculation

- **Investment**: $14,400 (one-time) + $600/yr (Ollama)
- **Returns**: Unblocks $50K EP-06 investment + $19,800/mo MRR potential (Vietnamese SME)
- **Payback Period**: < 1 month after Vietnamese SME pilot launch
- **3-Year ROI**: >40x

---

## 5. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Agent loop abuse (runaway costs) | High | High | 6 loop guards + budget circuit breaker |
| Prompt injection via OTT | High | Critical | 12-pattern InputSanitizer + wrapping |
| Shell command injection | Medium | Critical | 8-pattern ShellGuard + path restriction |
| Provider vendor lock-in | Low | Medium | 4-field provider profile key + failover |
| Infinite delegation chain | Medium | High | max_delegation_depth + can_spawn_subagent |

---

## 6. Success Criteria (Gate G0.1)

| Criterion | Target | Measurement |
|-----------|--------|-------------|
| ADR-056 approved | CTO sign-off | ADR document status |
| Security threat model complete | 13 surfaces covered | STM-056 review |
| Test plan complete | 121+ test cases | TP-056 review |
| Sprint plans updated | 176-179 scope locked | Sprint plan review |
| Stakeholder alignment | CTO + CPO + CEO | Business case approval |

---

## 7. Timeline

| Sprint | Focus | Deliverables |
|--------|-------|-------------|
| 176 | Foundation + Design | ADR-056, schemas, threat model, test plan, SDLC docs |
| 177 | Core Services | 12 service files, 3 DB tables, 5 P0 endpoints, unit tests |
| 178 | Integration + Pilot | OTT gateway scaffold, E2E tests, Vietnamese SME demo |
| 179 | ZeroClaw Hardening | Credential scrubbing (A+C), history compaction (B), query classification (E) |

---

## 8. Approval

| Role | Name | Decision | Date |
|------|------|----------|------|
| CTO | Nguyen Quoc Huy | APPROVED | Feb 2026 |
| CPO | — | PENDING | — |
| CEO | — | PENDING | — |
