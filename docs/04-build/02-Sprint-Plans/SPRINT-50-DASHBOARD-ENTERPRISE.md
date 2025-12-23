# SPRINT-50: EP-06 Productization Baseline (Packaging + Docs)
## EP-06: IR-Based Vietnamese SME Codegen | Phase 4

---

**Document Information**

| Field | Value |
|-------|-------|
| **Sprint ID** | SPRINT-50 |
| **Epic** | EP-06: IR-Based Codegen Engine |
| **Duration** | 2 weeks (Mar 17-28, 2026) |
| **Status** | PLANNED |
| **Team** | 1 Backend + 1 Frontend + 0.5 DevOps + 0.5 QA |
| **Story Points** | TBD |
| **Budget** | TBD |
| **Framework** | SDLC 5.1.1 + SASE Level 2 |
| **Strategic Context** | [Strategic Pivot from DeepCode](../../09-govern/04-Strategic-Updates/2025-12-22-STRATEGIC-PIVOT-DEEPCODE-TO-IR-CODEGEN.md) |

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

- Pilot can be repeated with minimal manual steps
- Generation runs produce consistent metrics (latency/cost/pass rate)
- Clear go/no-go decision artifact exists for optional DeepCode provider in Q2
