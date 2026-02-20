# SPRINT-49: EP-06 Pilot Execution + Metrics Hardening
## EP-06: IR-Based Vietnamese SME Codegen | Phase 3 (Pilot) | Must Have P0

---

**Document Information**

| Field | Value |
|-------|-------|
| **Sprint ID** | SPRINT-49 |
| **Epic** | EP-06: IR-Based Codegen Engine |
| **Duration** | 2 weeks (Mar 3-14, 2026) |
| **Status** | CEO APPROVED ✅ (Dec 23, 2025) |
| **Priority** | **P0 Must Have** |
| **Team** | 1 Backend + 1 Frontend + 0.5 DevOps |
| **Story Points** | TBD (scope approved after Sprint 48 demo) |
| **Budget** | TBD |
| **Framework** | SDLC 6.1.0 + SASE Level 2 |
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
│  ★ PILOT: 10 Vietnamese SME founders validate EP-06                │
│  ★ METRICS: TTFV <30min, Satisfaction 8/10                         │
├─────────────────────────────────────────────────────────────────────┤
│  LAYER 1: SDLC-ENTERPRISE-FRAMEWORK (Methodology)                   │
│  10 Stages | 4 Tiers | Quality Gates                                │
└─────────────────────────────────────────────────────────────────────┘
```

### Founder Plan Validation

This sprint is **critical for validating** the Founder Plan ($99/team/month):

| Metric | Target | Why It Matters |
|--------|--------|----------------|
| **Pilot participants** | 10 Vietnam SME founders | Real customer validation |
| **TTFV (Time to First Value)** | <30 min | Idea → working app |
| **Satisfaction** | 8/10 | Would recommend to others |
| **Quality gate pass** | 95%+ | Generated code passes Orchestrator checks |

---

## 🎯 Sprint Goal

Run a controlled pilot with Vietnamese SME founders and harden the end-to-end flow until it reliably hits the EP-06 success metrics.

---

## Sprint Objectives

| # | Objective | Priority | Owner |
|---|-----------|----------|-------|
| 1 | Pilot onboarding with 10 Vietnamese SME founders (guided) | P0 | Product + Team |
| 2 | Measure and improve TTFV (idea → working app) | P0 | Full team |
| 3 | Stabilize generation quality (reduce invalid IR + failed gates) | P0 | Backend |
| 4 | Improve reliability of deploy path used in demo/pilot (minimal) | P1 | DevOps |

---

## Success Criteria (from CEO pivot)

| Metric | Target | Status |
|--------|--------|--------|
| Pilot participants | 10 Vietnamese SME founders complete onboarding | TBD |
| TTFV (90th percentile) | <30 minutes | TBD |
| Founder satisfaction | 8/10 (survey) | TBD |
| Quality gate pass rate | 95%+ | TBD |

---

## Pilot Recruitment

**Target**: 10 Vietnamese SME founders across 3 domains

| Domain | Target | Example Use Case |
|--------|--------|------------------|
| **F&B** | 4 founders | Restaurant ordering, menu management |
| **Hospitality** | 3 founders | Hotel booking, guest management |
| **Retail** | 3 founders | Inventory, sales tracking |

**Recruitment Channels**:
- NQH internal network
- Vietnam startup communities
- Referrals from BFlow customers

---

## Notes

- This sprint is intentionally **light on new features** and focused on pilot learnings + reliability.
- DeepCode remains deferred to Q2 2026 as optional provider, gated by EP-06 success.

---

## Document Control

| Field | Value |
|-------|-------|
| **Version** | 2.0.0 |
| **Last Updated** | December 23, 2025 |
| **Owner** | CTO + PM Team |
| **Approved By** | CEO ✅ (Dec 23, 2025) |
