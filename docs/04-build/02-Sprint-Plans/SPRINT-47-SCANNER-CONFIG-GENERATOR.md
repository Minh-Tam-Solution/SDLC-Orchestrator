# SPRINT-47: Vietnamese Domain Templates + Onboarding IR
## EP-06: IR-Based Vietnamese SME Codegen | Phase 2B

---

**Document Information**

| Field | Value |
|-------|-------|
| **Sprint ID** | SPRINT-47 |
| **Epic** | EP-06: IR-Based Codegen Engine |
| **Duration** | 2 weeks (Feb 3-14, 2026) |
| **Status** | PLANNED |
| **Team** | 1 Backend + 1 Frontend + 0.5 DevOps |
| **Story Points** | 18 SP |
| **Budget** | $5,000 (part of $15,000 for Sprint 46-48) |
| **Framework** | SDLC 5.1.1 + SASE Level 2 |
| **Dependency** | Sprint 46 (backend scaffold generators) |

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

---

## Scope / Non-Goals

**Out of scope:** voice input, complex UI, multi-tenant packaging.
