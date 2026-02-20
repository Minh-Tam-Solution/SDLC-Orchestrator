# SPRINT-46: IR Processors (Backend Scaffold)
## EP-06: IR-Based Vietnamese SME Codegen | Phase 2A | Must Have P0

---

**Document Information**

| Field | Value |
|-------|-------|
| **Sprint ID** | SPRINT-46 |
| **Epic** | EP-06: IR-Based Codegen Engine |
| **Duration** | 2 weeks (Jan 20-31, 2026) |
| **Status** | CEO APPROVED ✅ (Dec 23, 2025) |
| **Priority** | **P0 Must Have** |
| **Team** | 2 Backend + 0.5 Architect |
| **Story Points** | 18 SP |
| **Budget** | $5,000 (part of $15,000 for Sprint 46-48) |
| **Framework** | SDLC 6.1.0 + SASE Level 2 |
| **Dependency** | Sprint 45 (provider contract + API) |
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
│  ★ IR → Backend Scaffold: FastAPI + SQLAlchemy + Alembic           │
│  ★ EP-06 Codegen: IR-based generation for Vietnam SME              │
├─────────────────────────────────────────────────────────────────────┤
│  LAYER 1: SDLC-ENTERPRISE-FRAMEWORK (Methodology)                   │
│  10 Stages | 4 Tiers | Quality Gates                                │
└─────────────────────────────────────────────────────────────────────┘
```

### Dual Wedge Strategy

| Wedge | Target | Pricing | This Sprint |
|-------|--------|---------|-------------|
| **Vietnam SME (40%)** | Non-tech founders | $99/team/month | IR → runnable backend |
| **Global EM (40%)** | Engineering Managers | $30/user/month | - |
| **Enterprise (20%)** | Large organizations | Custom | - |

---

## 🎯 Sprint Goal

Turn IR schemas into deterministic generation steps:

`AppBlueprint` → backend scaffold (FastAPI + SQLAlchemy + Alembic) with module-level CRUD primitives.

---

## Sprint Objectives

| # | Objective | Priority | Owner |
|---|-----------|----------|-------|
| 1 | Implement IR validation against JSON schemas (`AppBlueprint`, `ModuleSpec`, `DataModelSpec`) | P0 | Backend Lead |
| 2 | Build backend code generator: project scaffold + core wiring | P0 | Backend Dev 1 |
| 3 | Generate entities + migrations from `DataModelSpec` | P0 | Backend Dev 2 |
| 4 | Generate CRUD endpoints/tests from `ModuleSpec` (minimal) | P1 | Backend Dev 1 |
| 5 | Produce a runnable local backend output bundle (definition documented) | P0 | Backend Lead |

---

## Deliverables

### 1) IR Validation
- Schema validation step before generation
- Human-readable error output (field path + message)

### 2) Backend Scaffold Generation
- FastAPI app skeleton
- SQLAlchemy models + session
- Alembic migration scaffold

### 3) Deterministic Output Contract

Define how generated code is returned from the API (e.g., zip artifact or in-memory bundle metadata).

---

## Success Criteria

| Metric | Target | Measurement |
|--------|--------|-------------|
| IR validation | 100% schema-valid inputs accepted | Unit tests |
| Backend runs | Generated scaffold boots locally | Smoke test |
| Minimal CRUD | At least 1 module generates create/read endpoints | Integration test |

---

## Scope / Non-Goals

**In scope:** backend scaffold + data model + minimal CRUD.

**Out of scope:**
- Full React UI generation (starts Sprint 47/48)
- One-click deploy
- DeepCode integration

---

## Document Control

| Field | Value |
|-------|-------|
| **Version** | 2.0.0 |
| **Last Updated** | December 23, 2025 |
| **Owner** | CTO + PM Team |
| **Approved By** | CEO ✅ (Dec 23, 2025) |
