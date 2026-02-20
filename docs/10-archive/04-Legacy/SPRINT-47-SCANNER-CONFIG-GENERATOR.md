# SPRINT-47: Vietnamese Domain Templates + Onboarding IR
## EP-06: IR-Based Vietnamese SME Codegen | Phase 2B | Must Have P0

---

**Document Information**

| Field | Value |
|-------|-------|
| **Sprint ID** | SPRINT-47 |
| **Epic** | EP-06: IR-Based Codegen Engine |
| **Duration** | 2 weeks (Feb 3-14, 2026) |
| **Status** | CEO APPROVED ✅ (Dec 23, 2025) |
| **Priority** | **P0 Must Have** |
| **Team** | 1 Backend + 1 Frontend + 0.5 DevOps |
| **Story Points** | 18 SP |
| **Budget** | $5,000 (part of $15,000 for Sprint 46-48) |
| **Framework** | SDLC 6.1.0 + SASE Level 2 |
| **Dependency** | Sprint 46 (backend scaffold generators) |
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
│  ★ Vietnamese Domain Templates: F&B, Hospitality, Retail           │
│  ★ Onboarding → AppBlueprint: Vietnamese text input flow           │
├─────────────────────────────────────────────────────────────────────┤
│  LAYER 1: SDLC-ENTERPRISE-FRAMEWORK (Methodology)                   │
│  10 Stages | 4 Tiers | Quality Gates                                │
└─────────────────────────────────────────────────────────────────────┘
```

### Dual Wedge Strategy - Primary Focus

| Wedge | Target | Pricing | This Sprint Focus |
|-------|--------|---------|-------------------|
| **Vietnam SME (40%)** | Non-tech founders | $99/team/month (Founder Plan) | **Primary - Vietnamese templates** |
| **Global EM (40%)** | Engineering Managers | $30/user/month | - |
| **Enterprise (20%)** | Large organizations | Custom | - |

### Year 1 Target

- **25 Vietnam SME teams** on Founder Plan
- **$30K ARR** from Founder Plan alone (25 × $99 × 12)

---

## 🎯 Sprint Goal

Enable Vietnamese SME founders to go from a short Vietnamese interview/brief to a valid IR (`AppBlueprint`) and generate a first working MVP skeleton.

---

## Sprint Objectives

| # | Objective | Priority | Owner |
|---|-----------|----------|-------|
| 1 | Create Vietnamese domain template library (F&B / Hospitality / Retail) mapped to IR | P0 | Backend Lead |
| 2 | Implement onboarding → IR builder (Vietnamese text input) | P0 | Backend Dev |
| 3 | Add minimal frontend flow (existing UI patterns) to submit onboarding data and view generated IR | P1 | Frontend Dev |
| 4 | Expand provider prompts to use domain templates (Ollama primary) | P0 | Backend Dev |

---

## Deliverables

### 1) Vietnamese Templates (IR-Level)
- F&B: menu, order, table, reservation
- Hospitality: room, booking, guest, billing
- Retail: product, inventory, sale, customer

### 2) Onboarding → AppBlueprint
- Guided Vietnamese questionnaire to produce:
  - actors
  - modules
  - pages
  - entities
- Output must validate against IR schemas

---

## Success Criteria

| Metric | Target | Measurement |
|--------|--------|-------------|
| IR validity | 95%+ onboarding sessions produce schema-valid AppBlueprint | Test runs |
| Founder usability | Vietnamese flow understandable without developer help | Pilot feedback |
| Time to IR | <10 minutes from start to valid AppBlueprint | User testing |

---

## Scope / Non-Goals

**In scope:** Vietnamese templates, onboarding flow, IR generation.

**Out of scope:** voice input, complex UI, multi-tenant packaging.

---

## Founder Plan Validation

This sprint directly supports the **Founder Plan ($99/team/month)** by:
- Enabling non-tech Vietnamese founders to create IR without coding
- Providing domain-specific templates familiar to Vietnam SME market
- Reducing time-to-value to <30 minutes (idea → working app)

---

## Document Control

| Field | Value |
|-------|-------|
| **Version** | 2.0.0 |
| **Last Updated** | December 23, 2025 |
| **Owner** | CTO + PM Team |
| **Approved By** | CEO ✅ (Dec 23, 2025) |
