# SPRINT-48: Quality Gates + Ollama Optimization + MVP Hardening
## EP-06: IR-Based Vietnamese SME Codegen | Phase 2C | Must Have P0

---

**Document Information**

| Field | Value |
|-------|-------|
| **Sprint ID** | SPRINT-48 |
| **Epic** | EP-06: IR-Based Codegen Engine |
| **Duration** | 2 weeks (Feb 17-28, 2026) |
| **Status** | CEO APPROVED ✅ (Dec 23, 2025) |
| **Priority** | **P0 Must Have** |
| **Team** | 1 Backend + 1 Frontend + 0.5 DevOps |
| **Story Points** | 18 SP |
| **Budget** | $5,000 (part of $15,000 for Sprint 46-48) |
| **Framework** | SDLC 5.1.3 + SASE Level 2 |
| **Dependency** | Sprint 45-47 (providers + IR + onboarding/templates) |
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
│  ★ Quality Gates: Architecture + Security + Tests validation       │
│  ★ Ollama Optimization: <3s generation, cost tracking              │
├─────────────────────────────────────────────────────────────────────┤
│  LAYER 1: SDLC-ENTERPRISE-FRAMEWORK (Methodology)                   │
│  10 Stages | 4 Tiers | Quality Gates                                │
└─────────────────────────────────────────────────────────────────────┘
```

### Cost Target for Founder Plan

| Item | Target | Current |
|------|--------|---------|
| Infrastructure cost | <$50/month per project | TBD |
| Generation latency | <3s (p95) | TBD |
| Quality gate pass rate | ≥95% | TBD |

---

## 🎯 Sprint Goal

Make the generated MVP reliably pass Orchestrator gates, and optimize Ollama cost/latency for Vietnamese SME usage.

---

## Sprint Objectives

| # | Objective | Priority | Owner |
|---|-----------|----------|-------|
| 1 | Add quality gates for generated output (architecture validation + security scan + tests) | P0 | Backend Lead |
| 2 | Implement Ollama optimizations (prompt tuning + caching strategy as applicable) | P0 | Backend Dev |
| 3 | Add cost tracking + basic reporting (per generation) | P1 | Backend Dev |
| 4 | Hardening pass on onboarding + IR generation (reduce invalid output) | P0 | Full team |

---

## Success Criteria

| Metric | Target | Measurement |
|--------|--------|-------------|
| Quality gates pass rate | ≥95% generated outputs pass configured checks | CI run |
| Latency | <3s generation for common tasks (p95) | Benchmark |
| Cost target | <$50/month infra per project (target) | Cost report |

---

## Quality Gates for Generated Code

The generated code must pass:

1. **Architecture Validation**: Layer separation, no circular dependencies
2. **Security Scan**: OWASP checks via Semgrep (Sprint 43 integration)
3. **Test Execution**: Generated tests must pass
4. **Policy Guards**: OPA policies (Sprint 43 integration)

---

## Notes

- DeepCode remains **deferred to Q2 2026** and only as an optional provider plugin, conditional on EP-06 success metrics.
- This sprint focuses on **reliability over features**.

---

## Document Control

| Field | Value |
|-------|-------|
| **Version** | 2.0.0 |
| **Last Updated** | December 23, 2025 |
| **Owner** | CTO + PM Team |
| **Approved By** | CEO ✅ (Dec 23, 2025) |
