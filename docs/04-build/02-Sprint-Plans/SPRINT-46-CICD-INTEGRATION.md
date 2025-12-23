# SPRINT-46: IR Processors (Backend Scaffold)
## EP-06: IR-Based Vietnamese SME Codegen | Phase 2A

---

**Document Information**

| Field | Value |
|-------|-------|
| **Sprint ID** | SPRINT-46 |
| **Epic** | EP-06: IR-Based Codegen Engine |
| **Duration** | 2 weeks (Jan 20-31, 2026) |
| **Status** | PLANNED |
| **Team** | 2 Backend + 0.5 Architect |
| **Story Points** | 18 SP |
| **Budget** | $5,000 (part of $15,000 for Sprint 46-48) |
| **Framework** | SDLC 5.1.1 + SASE Level 2 |
| **Dependency** | Sprint 45 (provider contract + API) |

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
