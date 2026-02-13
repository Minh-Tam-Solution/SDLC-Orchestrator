# SPRINT-50: EP-06 Productization Baseline
## EP-06: IR-Based Vietnamese SME Codegen | Phase 4 | Must Have P0

---

**Document Information**

| Field | Value |
|-------|-------|
| **Sprint ID** | SPRINT-50 |
| **Epic** | EP-06: IR-Based Codegen Engine |
| **Duration** | 2 weeks (Mar 17-28, 2026) |
| **Status** | CEO APPROVED ✅ (Dec 23, 2025) |
| **Priority** | **P0 Must Have** |
| **Team** | 1 Backend + 1 Frontend + 0.5 DevOps + 0.5 QA |
| **Story Points** | TBD |
| **Budget** | TBD |
| **Framework** | SDLC 5.1.3 + SASE Level 2 |
| **Strategic Context** | [Expert Feedback Integration](../../09-govern/05-Knowledge-Transfer/02-Expert-Response/FINAL-EXECUTIVE-SUMMARY.md) |

---

## 🎯 Strategic Context (CEO Approved - Dec 23, 2025)

### Operating System for Software 3.0

**Positioning**: We are the **control plane** that orchestrates ALL AI coders under governance, evidence, and policy-as-code.

```
┌─────────────────────────────────────────────────────────────────────┐
│  LAYER 3: AI CODERS (They Generate)                                 │
│  Claude Code | Cursor | Copilot | Aider | Ollama                    │
├─────────────────────────────────────────────────────────────────────┤
│  LAYER 2: SDLC ORCHESTRATOR (We Govern) ← This Sprint               │
│  ★ PRODUCTIZATION: Repeatable workflow, minimal manual steps       │
│  ★ Q2 DECISION GATE: Go/No-Go for DeepCode provider               │
├─────────────────────────────────────────────────────────────────────┤
│  LAYER 1: SDLC-ENTERPRISE-FRAMEWORK (Methodology)                   │
│  10 Stages | 4 Tiers | Quality Gates                                │
└─────────────────────────────────────────────────────────────────────┘
```

### EP-06 Success Gate

Sprint 50 ends Q1 2026 EP-06 development. Success determines:

| Outcome | Criteria | Next Step |
|---------|----------|-----------|
| **EP-06 SUCCESS** | 10 pilots complete, 8/10 satisfaction, <30min TTFV | Proceed to Founder Plan GA |
| **EP-06 PARTIAL** | 5-9 pilots, 6-7/10 satisfaction | Sprint 51-52: hardening |
| **EP-06 FAIL** | <5 pilots, <6/10 satisfaction | Re-evaluate strategy |

---

## 🎯 Sprint Goal

Package EP-06 into a repeatable baseline that can be demoed and adopted without heavy team involvement.

---

## Sprint Objectives

| # | Objective | Priority | Owner |
|---|-----------|----------|-------|
| 1 | Document the end-to-end EP-06 workflow (onboarding → IR → generate → gates → deploy) | P0 | Full team |
| 2 | Add minimal observability/reporting for generation runs (cost/latency/pass rate) | P1 | Backend |
| 3 | Harden configuration defaults (provider selection + fallback) | P0 | Backend |
| 4 | Prepare Q2 decision gate for optional DeepCode provider (go/no-go criteria only) | P1 | CTO/Architect |

---

## Success Criteria

| Metric | Target | Status |
|--------|--------|--------|
| Pilot repeatable | Can be run with minimal manual steps | TBD |
| Metrics consistent | Generation runs produce consistent latency/cost/pass rate | TBD |
| DeepCode decision | Clear go/no-go criteria documented | TBD |

---

## Deliverables

### 1) EP-06 Documentation Suite

- User Guide: Vietnamese SME onboarding flow
- Technical Guide: Provider configuration, IR schema reference
- Troubleshooting Guide: Common issues and fixes

### 2) Observability Dashboard

- Generation metrics: latency, cost, pass rate
- Pilot metrics: TTFV, satisfaction, completion rate
- Provider metrics: Ollama performance, fallback usage

### 3) Q2 DeepCode Decision Gate

| Criteria | Threshold | Impact |
|----------|-----------|--------|
| EP-06 pilot success | ≥8/10 founders satisfied | Proceed with DeepCode as optional |
| Cost savings | Ollama <$50/mo vs Claude $1000/mo | Maintain Ollama-first strategy |
| Quality | 95%+ gate pass rate | DeepCode not needed for quality |

---

## Year 1 Target Validation

At end of Sprint 50, validate:

| Metric | Target | Status |
|--------|--------|--------|
| **Vietnam SME pipeline** | 25 teams interested | TBD |
| **Founder Plan conversions** | 5 paid teams | TBD |
| **TTFV** | <30 min (median) | TBD |
| **Satisfaction** | 8/10 average | TBD |

---

## Document Control

| Field | Value |
|-------|-------|
| **Version** | 2.0.0 |
| **Last Updated** | December 23, 2025 |
| **Owner** | CTO + PM Team |
| **Approved By** | CEO ✅ (Dec 23, 2025) |
