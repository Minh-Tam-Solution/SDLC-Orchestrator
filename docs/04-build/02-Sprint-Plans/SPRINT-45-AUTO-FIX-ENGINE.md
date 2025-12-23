# SPRINT-45: Multi-Provider Codegen Architecture
## EP-06: IR-Based Vietnamese SME Codegen | Phase 1

---

**Document Information**

| Field | Value |
|-------|-------|
| **Sprint ID** | SPRINT-45 |
| **Epic** | EP-06: IR-Based Codegen Engine |
| **Duration** | 2 weeks (Jan 6-17, 2026) |
| **Status** | APPROVED ✅ |
| **Team** | 1 Backend Lead + 0.5 Architect |
| **Story Points** | 13 SP |
| **Budget** | $3,000 |
| **Framework** | SDLC 5.1.1 + SASE Level 2 |
| **Strategic Context** | [Strategic Pivot from DeepCode](../../09-govern/04-Strategic-Updates/2025-12-22-STRATEGIC-PIVOT-DEEPCODE-TO-IR-CODEGEN.md) |

---

## �� Strategic Context

**CTO Direction:** Orchestrator remains the **control plane** for all AI coders. DeepCode is a **provider plugin** (optional, deferred), not the default engine.

**Sprint 45 goal:** establish a provider-agnostic codegen substrate (interface + routing + API) that can orchestrate Ollama/Claude/DeepCode without hard coupling.

---

## Sprint Goals

### Primary Objectives

| # | Objective | Priority | Owner |
|---|-----------|----------|-------|
| 1 | Define `CodegenProvider` interface (`generate` / `validate` / `estimate_cost`) | P0 | Backend Lead |
| 2 | Implement provider registry + routing (select + fallback chain) | P0 | Backend Lead |
| 3 | Implement `OllamaCodegenProvider` (Vietnamese-optimized prompts) | P0 | Backend Dev |
| 4 | Add `ClaudeCodegenProvider` + `DeepCodeProvider` stubs (no hard dependency) | P1 | Backend Dev |
| 5 | Expose provider-agnostic API endpoints | P0 | Backend Lead |

### Success Criteria

| Metric | Target | Measurement |
|--------|--------|-------------|
| Providers available | ≥3 (Ollama + Claude + DeepCode stub) | `/codegen/providers` output |
| Routing works | Configurable provider selection + fallback | Integration test |
| No provider hard dependency | System starts with only Ollama enabled | Local run |
| Quality gate hook | `validate` executes per provider | Unit tests |

---

## Deliverables

### 1) Provider Contract

- `CodegenProvider` interface:
  - `generate(spec: dict) -> str`
  - `validate(code: str) -> bool`
  - `estimate_cost(spec: dict) -> float`

### 2) Provider Registry + Routing

- Provider discovery/registration
- Routing by project config (explicit provider name)
- Fallback chain (e.g., `ollama -> claude -> deepcode`) without blocking the system when a provider is missing

### 3) Ollama Provider (Primary)

- Vietnamese prompt templates aligned to the IR schemas under `backend/app/schemas/codegen/`
- Output shape: returns generated code bundle (implementation-defined) that later sprints can persist into repo structure

### 4) API Endpoints (Provider-Agnostic)

- `POST /api/v1/codegen/generate`
- `POST /api/v1/codegen/validate`
- `GET /api/v1/codegen/providers`

---

## Scope / Non-Goals

**In scope:** interface, routing, primary provider, minimal API surface.

**Out of scope (explicit):**
- Building a “DeepCode-first” engine
- Full AppBlueprint → full-stack generation (starts Sprint 46)
- Any new UI beyond existing patterns

---

## Execution Plan

### Week 1 (Jan 6-10): Contract + Routing
- Implement `CodegenProvider` contract
- Implement registry and selection/fallback
- Wire minimal API routes and service layer

### Week 2 (Jan 13-17): Ollama Provider + Integration
- Implement `OllamaCodegenProvider`
- Add Claude + DeepCode stubs
- Add basic integration tests and a demo IR payload

---

## Demo Definition

Given a minimal `AppBlueprint` JSON, the system:
- Lists available providers
- Generates code via Ollama
- Runs provider validation
