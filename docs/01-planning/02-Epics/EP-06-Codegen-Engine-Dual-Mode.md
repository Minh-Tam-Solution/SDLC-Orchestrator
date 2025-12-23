# EP-06 – Codegen Engine with Dual Mode (BYO + Native OSS)

| Field | Value |
|-------|-------|
| **Epic ID** | EP-06 |
| **Title** | Codegen Engine with Dual Mode |
| **Status** | Draft |
| **Owner** | CTO / Platform Team |
| **Created** | 2025-12-21 |
| **SDLC Version** | 5.1.0 |
| **Stage** | 01-planning |
| **Timeline** | Sprint 50–55 (May–July 2026) |

## Related Documents

- [Product-Roadmap-2026-Software3.0.md](../01-Roadmap/Product-Roadmap-2026-Software3.0.md)
- [EP-02-AI-Safety-Layer.md](EP-02-AI-Safety-Layer.md)
- [EP-04-SDLC-Structure-Enforcement.md](EP-04-SDLC-Structure-Enforcement.md)
- [EP-05-SDLC-Version-Migration-Engine.md](EP-05-SDLC-Version-Migration-Engine.md)

---

## 1. Executive Summary

### CEO Vision

> **Không cạnh tranh trực diện với các AI codex mạnh như Claude Code / Cursor, mà dùng SDLC 5.0 + governance + IR decomposition để biến model open-source tầm trung (7–14B) thành một "codex đủ xài nhưng an toàn và được kiểm soát".**

### Tri-Mode Strategy (Updated Dec 2025)

| Mode | Target Users | AI Backend | Orchestrator Role |
|------|--------------|------------|-------------------|
| **Mode A – BYO Codex** | Enterprise dev teams | Claude Code / Cursor / Copilot | AI Safety & Governance Layer |
| **Mode B – Native OSS** | SME / non-tech founders | **qwen2.5-coder:32b** (92.7% HumanEval) | Full codegen + governance |
| **Mode C – Hybrid Fallback** | Dev teams (credit exhausted) | Claude Code → Continue.dev | **Seamless failover orchestration** |

> **UPDATE Dec 2025:** IT Admin đã deploy 10 models trên RTX 5090, bao gồm qwen2.5-coder:32b với 92.7% HumanEval score - cao hơn dự kiến ban đầu (CodeLlama 13B ~60%)!

### 🔥 NEW: Mode C – Hybrid Fallback (Real Pain Point from Dev Team)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  MODE C: HYBRID FALLBACK - "Never Stop Coding"                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  CURRENT PROBLEM (Dec 2025):                                                │
│  ───────────────────────────                                                │
│  • Team dùng Claude Code vì long context (200K) → dễ kiểm soát chất lượng  │
│  • Khi credit hết limit → PHẢI CHỜ RENEW → Downtime 🔴                      │
│  • IT Admin đã có Continue.dev + Ollama ready → nhưng team không dùng      │
│  • Lý do: Thiếu SDLC governance để đảm bảo chất lượng với smaller context   │
│                                                                             │
│  SOLUTION: SDLC ORCHESTRATOR AS QUALITY EQUALIZER                           │
│  ─────────────────────────────────────────────────                          │
│                                                                             │
│  ┌───────────────┐                           ┌───────────────┐              │
│  │  Claude Code  │  Credit OK ✓              │  Continue.dev │              │
│  │  (200K ctx)   │◄─────────────────────────▶│ + qwen2.5-32b │              │
│  │  $100-200/mo  │                           │  (32K ctx)    │              │
│  └───────┬───────┘     SDLC Orchestrator     └───────┬───────┘              │
│          │             orchestrates both             │                      │
│          │                    │                      │                      │
│          └────────────────────┼──────────────────────┘                      │
│                               ▼                                             │
│                    ┌─────────────────────┐                                  │
│                    │  IR Decomposition   │  ◄── Key to quality parity!      │
│                    │  (5-10KB per task)  │                                  │
│                    └─────────────────────┘                                  │
│                               │                                             │
│                               ▼                                             │
│                    ┌─────────────────────┐                                  │
│                    │  AI Safety Layer    │  ◄── Same governance both modes  │
│                    │  + Quality Gates    │                                  │
│                    └─────────────────────┘                                  │
│                               │                                             │
│                               ▼                                             │
│                    ┌─────────────────────┐                                  │
│                    │  CONSISTENT OUTPUT  │  ◄── Team doesn't notice switch! │
│                    │  (VCR Checkpoint)   │                                  │
│                    └─────────────────────┘                                  │
│                                                                             │
│  BENEFITS:                                                                  │
│  ─────────                                                                  │
│  ✅ Zero downtime when Claude credits exhausted                             │
│  ✅ Same code quality via IR decomposition + governance                     │
│  ✅ Leverage IT Admin's existing infrastructure (ROI!)                      │
│  ✅ Team confidence: "SDLC Orchestrator đảm bảo chất lượng"                 │
│  ✅ Cost savings: $0 for overflow usage                                     │
│                                                                             │
│  AUTO-FAILOVER LOGIC:                                                       │
│  ────────────────────                                                       │
│  if (claude_api.status == 429 || credit_remaining < threshold):             │
│      log("Claude credit exhausted, switching to Continue.dev + Ollama")     │
│      backend = "qwen2.5-coder:32b"  # IT Admin's infrastructure             │
│      decompose_context_to_IR()       # Break 200K → multiple 5K chunks      │
│      apply_same_governance()         # AI Safety Layer                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Key Insight: Governance > Raw Model IQ

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  TRADITIONAL APPROACH              SDLC ORCHESTRATOR APPROACH               │
│  ────────────────────              ───────────────────────────              │
│                                                                             │
│  "Build me a SaaS app"             Stage 00: "What problem?" (2KB context)  │
│       ↓                                 ↓                                   │
│  [128K+ tokens needed]             Stage 01: "5 features" (3KB context)     │
│  [Entire codebase context]              ↓                                   │
│  [Model cost: $200+/mo]            Stage 02: "Tech stack" (3KB context)     │
│       ↓                                 ↓                                   │
│  Generated code                    Stage 04: Feature 1 → Code (5KB context) │
│  (may hallucinate at scale)             ↓                                   │
│                                    Stage 04: Feature 2 → Code (5KB context) │
│                                                                             │
│  Context: 128K tokens              Context: 5K tokens per step              │
│  Model: Claude 3.5 ($20/mo)        Model: qwen2.5-coder:32b (free, 92.7%)   │
│  Risk: Uncontrolled drift          Risk: Controlled by VCR checkpoints      │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Problem Statement

### Pain Point 1: AI Codex Cost Barrier for SMEs

| AI Codex | Monthly Cost | Target Users | SME Accessible? |
|----------|--------------|--------------|-----------------|
| Claude Code Max | $100-200 | Pro developers | ❌ Too expensive |
| Cursor Pro | $20-40 | Pro developers | ⚠️ Still needs dev skills |
| GitHub Copilot | $19-39 | Pro developers | ⚠️ Still needs dev skills |
| Lovable | $20-50 | Non-tech | ✅ But no governance |

**Gap:** No solution for SME/non-tech that is both **affordable** AND **governed**.

### Pain Point 2: Non-Tech Founders Excluded

Current AI codex tools assume:
- User knows English well
- User understands programming concepts
- User can review/debug generated code

**Reality for Vietnamese SME founders:**
- May not be fluent in English
- Don't know programming
- Have creative ideas but can't execute
- Need guidance from idea → product → marketplace

### Pain Point 3: AI-Generated Code Without Governance

| Problem | Impact |
|---------|--------|
| No traceability | Can't audit what AI generated |
| No architecture control | AI may create inconsistent patterns |
| No quality gates | Bugs slip to production |
| No evidence trail | Compliance/security issues |

### Pain Point 4: Credit Exhaustion Downtime (Real Issue - Dec 2025) 🔥

> **From Dev Team:** "Team vẫn dùng Claude Code vì long context nên dễ kiểm soát chất lượng hơn, tuy nhiên khi credit đến limit thì phải chờ renew"

| Current Situation | Impact |
|-------------------|--------|
| Team uses Claude Code exclusively | Single point of failure |
| Claude credit exhausted → wait for renewal | **Productivity loss (days)** |
| IT Admin has Continue.dev + Ollama ready | Infrastructure underutilized |
| Team won't use OSS models directly | **Fear of quality degradation** |

**Root Cause Analysis:**
```
WHY team không chuyển sang Continue.dev khi hết Claude credit?
    └── Vì sợ chất lượng code giảm
        └── Vì qwen2.5-coder chỉ có 32K context vs Claude 200K
            └── Vì cần send toàn bộ codebase làm context
                └── Vì THIẾU SDLC governance để decompose task! ◄── ROOT CAUSE
```

**Solution:** SDLC Orchestrator làm **Context Equalizer** - decompose 200K context thành nhiều 5K chunks với IR, apply same governance → cùng output quality!

---

## 3. Solution: Codegen Engine with Tri-Mode

### 3.1. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    SDLC ORCHESTRATOR: CODEGEN ENGINE                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐         │
│  │  INTENT LAYER   │───▶│ BLUEPRINT LAYER │───▶│  CODEGEN LAYER  │         │
│  │  (existing)     │    │  (IR v0)        │    │  (new)          │         │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘         │
│         │                       │                      │                    │
│         ▼                       ▼                      ▼                    │
│  • Idea intake          • AppBlueprint         ┌──────────────────┐        │
│  • Story mapping        • ModuleSpec           │ Backend A: BYO   │        │
│  • Requirements         • PageSpec             │ (Claude/Cursor)  │        │
│  • Policies/Gates       • DataModelSpec        ├──────────────────┤        │
│                                                │ Backend B: Native│        │
│                                                │ (CodeLlama/DS)   │        │
│                                                └──────────────────┘        │
│                                                         │                   │
│                              ┌──────────────────────────┘                   │
│                              ▼                                              │
│                    ┌─────────────────────────────────────┐                 │
│                    │    AI SAFETY & GOVERNANCE LAYER     │                 │
│                    │  (existing - ALL code must pass)    │                 │
│                    ├─────────────────────────────────────┤                 │
│                    │ • Validators (lint, type, arch)     │                 │
│                    │ • Policy Guards (security, license) │                 │
│                    │ • Evidence Trail (MRP, VCR)         │                 │
│                    │ • Test Generation & Coverage        │                 │
│                    └─────────────────────────────────────┘                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2. Intermediate Representation (IR) – Key to Small Model Success

Instead of sending raw prompts to models, we use **structured IR**:

```yaml
# Example: IR reduces context from 100KB to 5KB per task
app:
  name: "Dalat Homestay Booking"
  domain: "HOSPITALITY"
  locale: "vi-VN"
  
entities:
  - Booking { id, guest_id, room_id, checkin, checkout, status }
  - Payment { id, booking_id, amount, method, status }
  
use_cases:
  - "Guest creates booking"
  - "Staff approves booking"
  
# Codegen prompt for OSS model becomes:
# "Generate FastAPI router for Booking with CRUD endpoints,
#  using SQLAlchemy, following this ModuleSpec..."
```

**Benefits of IR-based codegen:**
- Reduces token usage by 90%
- Constrains model output to templates
- Enables smaller models (7-14B) to succeed
- Provides traceability from requirement to code

### 3.3. Lovable-style Journey for Non-Tech Users

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  HÀNH TRÌNH: TỪ Ý TƯỞNG → MVP → MARKETPLACE (Tiếng Việt)                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  STEP 1: Ý TƯỞNG (Chat tiếng Việt)                    SDLC Artifact         │
│  ─────────────────────────────────                    ─────────────         │
│  User: "Em muốn làm app đặt phòng homestay           → BriefingScript       │
│         cho Đà Lạt, có thanh toán online"            → PRD nhẹ              │
│                                                                             │
│  Orchestrator: Detect domain → suggest template      → AppBlueprint         │
│                                                                             │
│  ════════════════════════════════════════════════════════════════════════  │
│                                                                             │
│  STEP 2: BLUEPRINT (Auto-generate, user confirms)    SDLC Artifact         │
│  ─────────────────────────────────────────────────   ─────────────         │
│  • Tech stack: React + Tailwind + FastAPI            → Tech Spec            │
│  • Data model: Room, Booking, Payment, User          → DataModelSpec        │
│  • Screens: Landing, Search, Checkout, Dashboard     → PageSpec             │
│  • Flow: 4 use-cases auto-mapped                     → Use Case Diagram     │
│                                                                             │
│  User: ✓ Confirm or request changes (tiếng Việt)     → VCR (approval)       │
│                                                                             │
│  ════════════════════════════════════════════════════════════════════════  │
│                                                                             │
│  STEP 3: CODEGEN (Module-by-module, governed)        SDLC Artifact         │
│  ─────────────────────────────────────────────────   ─────────────         │
│  Task 1: "Create Room API endpoints"                 → LoopScript           │
│  Task 2: "Create Booking form component"             → LoopScript           │
│  Task 3: "Create payment integration stub"           → LoopScript           │
│                                                                             │
│  Each task: ModuleSpec → CodeLlama 13B → Code        → MRP (evidence)       │
│             → Validators → Tests → PR                → VCR (approval)       │
│                                                                             │
│  ════════════════════════════════════════════════════════════════════════  │
│                                                                             │
│  STEP 4: PREVIEW & CHỈNH SỬA (Chat tiếng Việt)       SDLC Artifact         │
│  ─────────────────────────────────────────────────   ─────────────         │
│  User: "Sửa nút đặt phòng to hơn, đổi màu xanh"      → Change Request       │
│  User: "Thêm bước xác nhận qua OTP"                  → Requirement Update   │
│                                                                             │
│  Orchestrator: Map → ModuleSpec change → Regen       → MRP + VCR            │
│                                                                             │
│  ════════════════════════════════════════════════════════════════════════  │
│                                                                             │
│  STEP 5: DEPLOY & MARKETPLACE                        SDLC Artifact         │
│  ─────────────────────────────────────────────────   ─────────────         │
│  • One-click deploy: Vercel / Render / Cloud Run     → Release Evidence     │
│  • Auto-generate: Privacy page, Terms stub, SEO      → Compliance Docs      │
│  • Marketplace submission checklist                  → Launch Checklist     │
│                                                                             │
│  Result: Live app at https://dalat-homestay.app 🎉   → Stage 06-07 Complete │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  METRICS                                                                    │
│  • Total time: 2-4 hours (with VCR checkpoints)                            │
│  • Cost: $0 (local Ollama) or $50/mo (hosted)                              │
│  • Technical knowledge: ZERO                                                │
│  • Code quality: Governed by AI Safety Layer                                │
│  • Traceability: Full SDLC artifacts from idea to deploy                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Objectives & Success Metrics

### 4.1. Objectives

1. Design & integrate **Codegen Engine** (dual backend) into Orchestrator architecture
2. Standardize **IR v0** (AppBlueprint, ModuleSpec, PageSpec, DataModelSpec) as intermediate layer
3. Expose **codegen-service API v0** (module, tests, refactor) for both dev and non-tech flows
4. Connect Codegen Engine with **AI Safety Layer v1** (all generated code must pass validation)
5. Prepare foundation for **Vietnamese-first SME/non-tech product**

### 4.2. Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Demo app generated via Mode B (OSS) | ≥ 1 full app | Backend + basic UI, 100% from IR |
| Modules passing quality gates | ≥ 3 modules | Lint + tests + coverage ≥ 70% |
| Time to generate + validate 1 module | ≤ 3 minutes | End-to-end timing |
| Design Partners using Codegen Engine | ≥ 2 partners | Mode A or Mode B pilot |

---

## 5. Scope

### 5.1. In Scope (EP-06)

| # | Deliverable | Description |
|---|-------------|-------------|
| 1 | Product Vision update | Add "Codegen Engine – Dual Mode" section to Vision v3.1 |
| 2 | IR v0 schemas | JSON schemas: AppBlueprint, ModuleSpec, PageSpec, DataModelSpec |
| 3 | Codegen service API v0 | 3 endpoints: `/generate/module`, `/generate/tests`, `/refactor` |
| 4 | OSS model integration | **qwen2.5-coder:32b** (92.7% HumanEval) via OllamaService |
| 5 | Model Roles Strategy | Configure 5 roles: default, chat, edit, apply, autocomplete |
| 6 | Non-tech founder journey | Storyboard mapping idea → MVP → deploy with SDLC artifacts |

### 5.2. Out of Scope (EP-06)

- UI Builder drag & drop (future epic)
- Multi-service / microservices generation (v1+)
- Full CI/CD infrastructure generation (v1+)
- Rich marketplace integration (future epic)

---

## 6. Deliverables

### 6.1. Vision v3.1

Update `docs/00-foundation/01-Vision/` with Codegen Engine Dual Mode section.

### 6.2. IR v0 Schemas

```
backend/app/schemas/codegen/
├── app_blueprint.schema.json
├── module_spec.schema.json
├── page_spec.schema.json
└── data_model.schema.json
```

### 6.3. Codegen Service API v0

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/codegen/module` | POST | Generate module code from ModuleSpec |
| `/api/v1/codegen/tests` | POST | Generate tests for existing module |
| `/api/v1/codegen/refactor` | POST | Refactor code based on instructions |

### 6.4. OSS Model Integration (NQH AI Platform - December 2025)

> **IT Admin Infrastructure:** RTX 5090 32GB with 10 production models already deployed!
> **API Endpoint:** `https://api.nhatquangholding.com` (NAT to internal Ollama server)

#### Available Models (via Continue.dev Training Docs)

| Model | Size | Speed | HumanEval | Use Case |
|-------|------|-------|-----------|----------|
| 🎯 **qwen2.5-coder:32b-instruct** | 19GB | ~6s | **92.7%** | **Production Code - PRIMARY** |
| ⚡ **qwen2.5:14b-instruct** | 9GB | ~4s | N/A | Fast Tasks, Autocomplete |
| 🇻🇳 **qwen2.5:32b** | 19GB | ~8s | N/A | Vietnamese + Code |
| 🇻🇳 **qwen3:14b** | 9.3GB | ~4s | N/A | Vietnamese Chat |
| 💨 **ministral-3:8b** | 6GB | ~3s | N/A | Quick Processing |

#### Model Roles Strategy (IT Admin Update - Dec 2025)

```json
{
  "modelRoles": {
    "default": "qwen2.5-coder:32b-instruct-q4_K_M",   // PRIMARY CODE - 92.7% HumanEval
    "chat": "qwen2.5:32b",                            // General + Vietnamese support
    "edit": "qwen2.5-coder:32b-instruct-q4_K_M",      // Accurate code changes
    "apply": "qwen2.5-coder:32b-instruct-q4_K_M",     // Precise modifications
    "autocomplete": "qwen2.5:14b-instruct"            // Fast (~4s)
  }
}
```

#### Task-to-Model Mapping (Aligned with Continue.dev Config)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  CODEGEN MODEL ROLES (Leveraging IT Admin's 10-Model Strategy)             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ROLE              MODEL                         SPEED   PURPOSE            │
│  ────────────────  ────────────────────────────  ──────  ─────────────────  │
│  default/edit      qwen2.5-coder:32b-instruct    ~6s     Production code    │
│  chat              qwen2.5:32b                   ~8s     General + Viet     │
│  autocomplete      qwen2.5:14b-instruct          ~4s     Tab completion     │
│  vietnamese        qwen3:14b                     ~4s     VN docs/comments   │
│  ultra-fast        qwen3:8b                      <3s     Quick drafts       │
│                                                                             │
│  Continue.dev + Claude Strategy:                                            │
│  ─────────────────────────────────────────────────────────────────────────  │
│  • Continue.dev: Quick edits, autocomplete, <500 lines, simple tasks       │
│  • Claude Code: Multi-file refactor, architecture, complex debug            │
│  • Mode C Hybrid: SDLC Orchestrator handles failover seamlessly            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Model Selection by Task Type

| Task Type | Model | Rationale |
|-----------|-------|-----------|
| **Production Code** | qwen2.5-coder:32b-instruct | PRIMARY - 92.7% HumanEval, ~6s |
| **Quick Edits** | qwen2.5:14b-instruct | Fast (~4s), replaced qwen2.5-coder:14b |
| **Tab Autocomplete** | qwen2.5:14b-instruct | Real-time suggestions |
| **Vietnamese Docs** | qwen3:14b | Best Vietnamese support |
| **Ultra-fast Drafts** | qwen3:8b | Fastest (<3s) |
| **General Chat** | qwen2.5:32b | Good bilingual support |
| **Multi-file Refactor** | Claude Code (BYO) | Complex, needs 200K context |

#### Configuration

```python
# Configuration (backend/app/core/config.py)
CODEGEN_OLLAMA_URL = "https://api.nhatquangholding.com"  # NAT via router
CODEGEN_MODEL_PRIMARY = "qwen2.5-coder:32b-instruct-q4_K_M"  # 92.7% HumanEval!
CODEGEN_MODEL_FAST = "qwen2.5:14b-instruct"  # For autocomplete
CODEGEN_MODEL_VIETNAMESE = "qwen3:14b"  # For Vietnamese prompts
CODEGEN_TIMEOUT = 120  # Longer timeout for code generation
```

#### Why This Changes Everything

| Metric | Original Plan (CodeLlama 13B) | With IT Admin's qwen2.5-coder:32b |
|--------|-------------------------------|-----------------------------------|
| HumanEval Score | ~60% | **92.7%** (+32.7%) |
| Code Quality | Moderate | **Near-Copilot level** |
| Vietnamese Support | Poor | **Excellent** (via qwen3:14b) |
| Infrastructure | Need to setup | **Already deployed!** |
| Continue.dev | Need to integrate | **Already integrated by IT Admin** |

> **Key Insight:** IT Admin đã build hạ tầng AI hoàn chỉnh, nhưng dev team chưa dùng nhiều vì thiếu SDLC automation (EP-04/EP-05). EP-06 sẽ bridge gap này bằng cách integrate sdlcctl với Continue.dev + Ollama infrastructure.

### 6.5. Non-Tech Founder Journey Doc

`docs/02-design/Non-Tech-Founder-Journey.md` with storyboard and SDLC artifact mapping.

---

## 7. Timeline & Sprint Mapping

| Sprint | Dates | Focus | Deliverables |
|--------|-------|-------|--------------|
| 50 | May 5-16, 2026 | Vision + IR Design | Vision v3.1, IR schema drafts |
| 51 | May 19-30, 2026 | IR Implementation | Final IR schemas, Pydantic models |
| 52 | Jun 2-13, 2026 | API v0 | Codegen endpoints, OpenAPI spec |
| 53 | Jun 16-27, 2026 | Model Integration | OSS model wiring, prompt templates |
| 54 | Jun 30-Jul 11, 2026 | Non-tech Journey | Storyboard, UX flow, prototype |
| 55 | Jul 14-25, 2026 | Integration & Demo | End-to-end demo, Design Partner pilot |

---

## 8. Functional Requirements

### FR-01: IR-Based Code Generation

System can receive `ModuleSpec` + `DataModelSpec` + `AppBlueprint` and generate:
- Backend code files (FastAPI/Django)
- Basic test files

### FR-02: UI Component Generation

System can receive `PageSpec` and generate:
- Simple React page/component

### FR-03: Test Generation

System can generate supplementary tests for existing modules based on coverage target.

### FR-04: Backend Selection

System allows selection of codegen backend:
- `native_oss` (CodeLlama/DeepSeek)
- `external_codex` (Claude/Cursor API - future)

### FR-05: Governance Integration

All generated code must:
- Be tagged with `source = Codegen Engine v0`
- Pass through AI Safety Layer (validators + policy guards + Evidence Trail)

---

## 9. Non-Functional Requirements

| Requirement | Target |
|-------------|--------|
| Response time per module generation | ≤ 60 seconds (7-14B model) |
| Drift control | Code must follow template + constraints |
| Observability | Log model, prompt length, token usage, success/failure |
| Security | No secrets/env values in prompts or evidence |

---

## 10. Dependencies

| Dependency | Status | Required By |
|------------|--------|-------------|
| AI Safety Layer v1 (EP-02) | ✅ Existing | Sprint 50 |
| OllamaService | ✅ Existing | Sprint 53 |
| Company GPU Server | ✅ **CEO Approved** | Sprint 53 |
| Git integration (GitHub/GitLab) | ✅ Existing | Sprint 55 |
| Analytics (usage tracking) | ⏳ Planned | Sprint 55 |

### 10.1. Infrastructure (CEO Approved)

| Resource | Endpoint | Purpose |
|----------|----------|---------|
| Company GPU Server | `api.nhatquangholding.com:11434` | Mode B OSS inference |
| Models Available | CodeLlama 7B/13B, Llama2, DeepSeek | Code generation |
| Cost | $0 (company infrastructure) | No additional cost |

---

## 11. Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| OSS model quality unstable | Medium | High | IR-based prompting + strict templates + validation |
| Scope creep to UI/frontend | High | Medium | v0 focuses on backend + basic React; rich UI builder for later |
| Non-tech journey too complex | Medium | Medium | 5-step flow, test with 2-3 real users |
| Model performance on low-end hardware | Medium | Medium | Support cloud inference option |

---

## 12. Competitive Positioning

| Aspect | Lovable | Claude Code | SDLC Orchestrator |
|--------|---------|-------------|-------------------|
| Target | Non-tech | Pro devs | Both (Dual Mode) |
| Governance | None | None | Full SDLC 5.0 |
| Traceability | None | Git only | Artifacts + Evidence |
| Model | Proprietary | Claude | BYO or OSS |
| Cost | $20-50/mo | $100-200/mo | $0-50/mo (OSS) |
| Differentiator | "Vibe coding" | Raw power | **AI-Native SDLC** |

---

## 13. Open Questions

1. **Default backend stack:** FastAPI or Django for v0?
2. **IR storage:** YAML in repo, JSON in DB, or both?
3. **Test depth:** Simple tests or target high coverage in v0?
4. **Refactor endpoint:** Include in v0 or defer to v1?

---

## Appendix A: Tier-Based Features

| Feature | Free | Pro | Enterprise |
|---------|------|-----|------------|
| Mode A (BYO Codex) | ✅ Basic | ✅ Full | ✅ Full + Custom |
| Mode B (Native OSS) | ✅ 3 modules/mo | ✅ Unlimited | ✅ Unlimited + Priority |
| IR Templates | 5 templates | 20 templates | Custom templates |
| Non-tech Journey | ✅ Basic | ✅ Full | ✅ + Onboarding support |
| Multilingual | English only | + Vietnamese | + All locales |

---

## Appendix B: Research References

### Text2App / LLM4FaaS Approach

Research shows that using **intermediate representation / abstraction** significantly reduces model requirements while maintaining output quality:

- **Text2App**: Natural Language → Intermediate Spec → Code
- **LLM4FaaS**: LLM + Abstraction Layer to reduce complexity

Key findings:
- 90% reduction in token usage
- Smaller models (7-14B) can match larger models with proper IR
- Template-based generation reduces hallucination

### Lovable Analysis

Lovable's success factors for non-tech users:
- Natural language input (no code required)
- Template-based scaffolding
- Preview before deploy
- One-click deployment

**Our differentiation:**
- Full SDLC governance (Lovable has none)
- Evidence trail for compliance
- Architecture consistency
- Vietnamese-first support

---

*Document created: 2025-12-21*
*Last updated: 2025-12-21*
*Author: CTO / Platform Team*
