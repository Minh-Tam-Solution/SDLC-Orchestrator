# SPRINT-45: Multi-Provider Codegen Architecture
## EP-06: IR-Based Vietnamese SME Codegen | Phase 1 | Must Have P0

---

**Document Information**

| Field | Value |
|-------|-------|
| **Sprint ID** | SPRINT-45 |
| **Epic** | EP-06: IR-Based Codegen Engine |
| **Duration** | 2 weeks (Jan 6-17, 2026) |
| **Status** | **CTO APPROVED ✅** (Dec 23, 2025) - Ready to Start |
| **Priority** | **P0 Must Have** |
| **Team** | 1 Backend Lead + 0.5 Architect |
| **Story Points** | 13 SP |
| **Budget** | $3,000 |
| **Framework** | SDLC 6.1.0 + SASE Level 2 |
| **Strategic Context** | [Expert Feedback Integration](../../09-govern/05-Knowledge-Transfer/02-Expert-Response/FINAL-EXECUTIVE-SUMMARY.md) |
| **CEO Approval** | ✅ Dec 23, 2025 |
| **CTO Approval** | ✅ Dec 23, 2025 |

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
│  ★ Multi-Provider Architecture: Ollama → Claude → DeepCode         │
│  ★ EP-06 Codegen: IR-based generation for Vietnam SME              │
├─────────────────────────────────────────────────────────────────────┤
│  LAYER 1: SDLC-ENTERPRISE-FRAMEWORK (Methodology)                   │
│  10 Stages | 4 Tiers | Quality Gates                                │
└─────────────────────────────────────────────────────────────────────┘
```

### Dual Wedge Strategy

| Wedge | Target | Pricing | EP-06 Role |
|-------|--------|---------|------------|
| **Vietnam SME (40%)** | Non-tech founders | $99/team/month (Founder Plan) | Primary - IR-based codegen |
| **Global EM (40%)** | Engineering Managers | $30/user/month | BYO AI + governance |
| **Enterprise (20%)** | Large organizations | Custom | BYO AI + governance |

### Year 1 Target

- **30-50 teams** (realistic for 8.5 FTE, founder-led sales)
- **$86K-$144K ARR** (60% Founder, 30% Standard, 10% Enterprise)

**Sprint 45 goal:** Establish provider-agnostic codegen substrate (interface + routing + API) that orchestrates Ollama/Claude/DeepCode without hard coupling.

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
- `POST /api/v1/codegen/estimate` (optional in Sprint 45; keep non-blocking)

---

## Scope / Non-Goals

**In scope:** interface, routing, primary provider, minimal API surface.

**Out of scope (explicit):**
- Building a "DeepCode-first" engine
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
- Lists available providers via `GET /codegen/providers`
- Generates code via Ollama using `POST /codegen/generate`
- Runs provider validation via `POST /codegen/validate`

---

## 🚦 CTO Go Conditions (Non-Negotiable)

### Mandatory Requirements

| Condition | Description | Verification |
|-----------|-------------|--------------|
| **No DeepCode-first** | DeepCode is stub/placeholder only, NO hard dependency, NO blocking when key/SDK missing | Code review |
| **CodegenProvider contract** | Interface has `generate`, `validate`, `estimate_cost` methods | Unit test |
| **Registry + routing** | Provider discovery, config-based selection, fallback chain working | Integration test |
| **Core API endpoints** | `generate`, `validate`, `providers` endpoints operational (estimate is optional) | Smoke test |
| **Ollama as primary** | Ollama provider runs end-to-end with IR input | Demo |

### Test/Quality Gates

| Gate | Requirement | Evidence |
|------|-------------|----------|
| **Integration test** | Routing + fallback chain tested | pytest pass |
| **Ollama-only boot** | System boots when Claude/DeepCode disabled | Runbook + test |
| **No provider hard dependency** | Documented disable procedure | README section |

---

## ✅ Definition of Done (Sprint 45 Gate)

### Demo Checklist

- [ ] `GET /api/v1/codegen/providers` returns list of available providers
- [ ] `POST /api/v1/codegen/generate` with minimal AppBlueprint produces output via Ollama
- [ ] `POST /api/v1/codegen/validate` runs validation per provider
- [ ] (Optional) `POST /api/v1/codegen/estimate` returns a cost estimate
- [ ] System boots with Ollama-only (Claude/DeepCode disabled)
- [ ] Runbook documenting how to disable providers exists

### Quality Checklist

- [ ] All P0 objectives complete
- [ ] Integration test for routing + fallback
- [ ] Unit tests for CodegenProvider contract
- [ ] No hard dependencies on external provider SDKs

---

## ⚠️ Risks & Mitigations (CTO Guidance)

| Risk | Mitigation | Owner |
|------|------------|-------|
| **Output contract scope creep** | Sprint 45 returns implementation-defined bundle only; NO zip/artifact spec (defer to Sprint 46) | Backend Lead |
| **IR schema changes** | Map to existing schemas only; NO schema modifications without CTO approval | Architect |
| **Provider timeout handling** | Define error model in Architect review (Day 1) | Architect |

---

## 🚀 Action Items Before Sprint Start (Day 1)

| # | Action | Owner | Due |
|---|--------|-------|-----|
| 1 | Finalize provider config format + location | Backend Lead | Day 1 AM |
| 2 | Write `ollama-only-boot` integration test | Backend Lead | Day 1 AM |
| 3 | 60-min Architect review: interface + routing + error model | Architect | Day 1 PM |
| 4 | Confirm fallback chain behavior (provider missing/timeout) | Backend Lead + Architect | Day 1 PM |

---

## Document Control

| Field | Value |
|-------|-------|
| **Version** | 3.0.0 |
| **Last Updated** | December 23, 2025 |
| **Owner** | CTO + PM Team |
| **CEO Approval** | ✅ Dec 23, 2025 |
| **CTO Approval** | ✅ Dec 23, 2025 - Ready to Start |
