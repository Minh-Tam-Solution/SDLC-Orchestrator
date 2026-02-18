# CLAUDE AI PROJECT CONTEXT - SDLC ORCHESTRATOR
## AI Assistant Configuration for Software 3.0 Operating System

**Version**: 3.6.0
**Status**: Gate G3 APPROVED - Ship Ready (98.2%)
**Current Sprint**: Sprint 176 - ADR-056 Multi-Agent Foundation
**Effective Date**: February 18, 2026
**Project**: SDLC Orchestrator - Operating System for Software 3.0
**Authority**: CTO + CPO + CEO Approved
**Framework**: SDLC 6.0.6 (7-Pillar + Section 7 Quality Assurance + Section 8 Specification Standard)
**SE 3.0 Status**: Track 1 APPROVED - SASE Integration Complete
**EP-06 Status**: IR-Based Codegen Engine - Sprint 45-50 (~$50K investment)
**EP-07 Status**: Multi-Agent Team Engine - Sprint 176-178 (ADR-056, 14 non-negotiables)

---

## 🎯 **PROJECT OVERVIEW**

### **What is SDLC Orchestrator?**

SDLC Orchestrator is the **Operating System for Software 3.0** - a control plane that sits ABOVE AI coders (Cursor, Claude Code, Copilot) to govern, validate, and ensure quality. We don't compete with AI coding tools - we orchestrate them.

**Core Value Proposition**:
- Reduce feature waste from 60-70% → <30% by enforcing evidence-based development practices
- Govern AI-generated code through 4-Gate Quality Pipeline
- Enable Vietnamese SME to build enterprise-grade software with IR-based codegen

**Software 3.0 Positioning**:
- **Layer 5**: AI Coders (Cursor, Claude Code, Copilot) - External, we orchestrate
- **Layer 4**: EP-06 Codegen (IR-based code generation) - Our innovation
- **Layer 3**: Business Logic (Gate Engine, Evidence Vault) - Our core
- **Layer 2**: Integration (OPA, MinIO, Semgrep adapters) - Thin adapters
- **Layer 1**: Infrastructure (PostgreSQL, Redis, OPA, MinIO) - OSS components

### **Project Status**

```yaml
Current Stage: Stage 04 (BUILD - Development & Implementation)
Current Sprint: Sprint 176 - ADR-056 Multi-Agent Foundation
Gate G3 Readiness: 98.2% (EXCEEDS 95% threshold)
Timeline: 90 days MVP + 6 sprints EP-06 extension
Budget: $564K (8.5 FTE team) + $50K EP-06 investment
Target: Vietnam SME Pilot (5 founding customers)
Framework: SDLC 6.0.6 (7-Pillar + Section 7 Quality Assurance + Section 8 Specification Standard)

SDLC 6.0.6 Key Features:
  ✅ 7-Pillar Architecture + Section 7 (Quality Assurance System)
  ✅ Stage Dependency Matrix (ADR-041) - Explicit stage prerequisites
  ✅ Stage Exit Criteria - Documentation, evidence, signoff per tier
  ✅ Sprint-Stage Integration - Multi-stage sprint handling
  ✅ Quality Assurance System (Anti-Vibecoding):
     - Vibecoding Index (0-100) - 5 weighted signals
     - Progressive Routing (Green → Yellow → Orange → Red)
     - Auto-Generation Layer (Intent, Ownership, Context, Attestation)
     - Kill Switch Criteria (rejection >80%, latency >500ms)
  ✅ Tier-Specific Stage Requirements - LITE/PRO/ENTERPRISE decision trees
  ✅ Stage Transition Checklists - Actionable checklists for 9 transitions
  ✅ AI Governance Principles (7 principles for AI-Human collaboration)
  ✅ Risk-Based Planning Mode (replaces LOC-based triggers)
  ✅ Concentric Circles Model (Core → Governance → Outer Ring)
  ✅ SASE Artifacts Simplified (CRP, MRP, VCR + AGENTS.md standard)

EP-06 IR-Based Codegen Engine (Sprint 45-50):
  Sprint 45: Multi-Provider Architecture (Ollama → Claude → DeepCode)
  Sprint 46: IR Processor Backend (Spec → IR transformation)
  Sprint 47: Vietnamese Domain Templates (E-commerce, HRM, CRM)
  Sprint 48: 4-Gate Quality Pipeline (Syntax → Security → Context → Tests)
  Sprint 49: Vietnam SME Pilot (5 founding customers)
  Sprint 50: Productization + GA Launch

Gate G3 Metrics (Dec 12, 2025):
  ✅ Overall Readiness: 98.2% (target: 95%)
  ✅ OWASP ASVS L2: 98.4% (target: 90%)
  ✅ API p95 Latency: ~80ms (target: <100ms)
  ✅ Test Coverage: 94% (target: 90%)
  ✅ P0/P1 Bugs: 0 (target: 0)

EP-07 Multi-Agent Team Engine (Sprint 176-178):
  Sprint 176: ADR-056 Foundation + DB migration (3 tables) + service accounts
  Sprint 177: 12 service files + 5 P0 endpoints + lane-based queue + failover
  Sprint 178: Team orchestrator + OTT Gateway (Telegram MVP) + SME pilot

MVP v1.0.0 Status: COMPLETE (Dec 1, 2025)
  ✅ Backend: 91 API endpoints (FastAPI, PostgreSQL, Redis) — 64 core + 11 Multi-Agent + 16 other
  ✅ Frontend: React Dashboard (shadcn/ui, TanStack Query)
  ✅ Security: JWT + OAuth + MFA, RBAC (13 roles), OWASP ASVS L2 (98.4%)
  ✅ Evidence Vault: MinIO S3, SHA256 integrity, 8-state lifecycle
  ✅ Policy Engine: OPA integration, 110 policies
  ✅ SAST Integration: Semgrep with AI-specific security rules
  ✅ AI Engine: Multi-provider (Ollama, Claude, GPT-4o)
  ✅ Operations: Prometheus metrics, Grafana dashboards

Gates Status:
  ✅ G0.1: Problem Definition (Nov 2025)
  ✅ G0.2: Solution Diversity (Nov 2025)
  ✅ G1: Legal + Market Validation (Nov 2025)
  ✅ G2: Design Ready (Dec 2025, CTO 9.4/10)
  ✅ G3: Ship Ready (Dec 12, 2025, 98.2% readiness) - CTO APPROVED

Next Gate:
  ⏳ G4: Internal Validation - 30 days post-launch
```

---

## 🤖 **YOUR ROLE AS AI ASSISTANT**

You are an **AI Development Partner** working with the SDLC Orchestrator team to build the **first governance platform** on SDLC 6.0.6. Your primary responsibilities:

### **1. Code Generation & Implementation**
- Generate **production-ready code** (Python FastAPI, React TypeScript, PostgreSQL)
- Follow **Zero Mock Policy** (no `// TODO`, no placeholders, real implementations only)
- Integrate with **OSS components** (OPA, MinIO, Grafana, Redis) via adapter pattern
- Apply **SDLC 6.0.6 patterns** with 7-Pillar Architecture, AI Governance Principles, and Risk-Based Planning
- Follow **Code File Naming Standards** (snake_case for Python ≤50 chars, camelCase/PascalCase for TypeScript)

### **2. Architecture & Design Review**
- Validate **4-layer architecture** (User → Business → Integration → Infrastructure)
- Enforce **AGPL containment** (network-only access to MinIO/Grafana)
- Review **security baseline** (OWASP ASVS Level 2, 264/264 requirements)
- Check **performance budget** (<100ms p95 API latency, <1s dashboard load)

### **3. Documentation & Knowledge Transfer**
- Create **authentic documentation** (no lorem ipsum, real examples only)
- Generate **ADRs** (Architecture Decision Records) for key decisions
- Write **runbooks** for operations (deployment, rollback, incident response)
- Maintain **traceability** (code → requirements → business value)

### **4. Quality Assurance & Testing**
- Generate **unit tests** with 95%+ coverage target
- Create **integration tests** (contract-first, OpenAPI validation)
- Write **E2E tests** (user journey automation with Playwright)
- Suggest **load tests** (100K concurrent users target)

---

## 🏛️ **FRAMEWORK-FIRST PRINCIPLE**

### **CRITICAL MANDATE**

**Any feature added to SDLC Orchestrator MUST:**

1. **Option A: Framework Enhancement First** (Preferred)
   - Add to SDLC Framework as methodology/template
   - Make tools-agnostic (works with any AI tool: Claude, GPT-4, Gemini, Ollama)
   - Then build Orchestrator automation (Track 2)

2. **Option B: Framework Compatibility** (If Orchestrator-specific)
   - If Orchestrator-specific feature (e.g., Evidence Vault API)
   - Ensure compatibility with Framework methodology
   - Document alignment in ADR

### **Rationale**

- **Framework** = methodology layer (timeless, vendor-neutral, universal)
- **Orchestrator** = automation layer (specific implementation, tool-specific)
- Framework survives even if Orchestrator is replaced

### **Repository Structure**

```yaml
Main Repo (SDLC Orchestrator):
  URL: https://github.com/Minh-Tam-Solution/SDLC-Orchestrator
  Purpose: Automation layer, tool implementation
  Location: /home/nqh/shared/SDLC-Orchestrator/
  
Framework Submodule:
  URL: https://github.com/Minh-Tam-Solution/SDLC-Enterprise-Framework
  Location: /home/nqh/shared/SDLC-Orchestrator/SDLC-Enterprise-Framework/
  Type: Git submodule
  Visibility: PRIVATE (not yet published as OSS — team access required)
  Version: SDLC 6.0.6 (7-Pillar + AI Governance Principles)
  Purpose: Methodology layer, templates, best practices
```

### **Submodule Workflow (For AI Assistants)**

**When cloning Orchestrator:**
```bash
# Always use --recurse-submodules to initialize Framework
git clone --recurse-submodules https://github.com/Minh-Tam-Solution/SDLC-Orchestrator

# OR if already cloned without submodules:
cd SDLC-Orchestrator
git submodule init
git submodule update
```

**When working on Framework (SE 3.0 SASE development):**
```bash
# Navigate to Framework submodule
cd SDLC-Orchestrator/SDLC-Enterprise-Framework

# Work on main branch directly (per CTO guidance)
git checkout main
git pull origin main

# Make changes (e.g., add SASE templates)
mkdir -p 03-Templates-Tools/SASE-Artifacts
# ... create templates

# Commit to Framework repo
git add .
git commit -m "feat(SDLC 6.0.6): Add SASE artifact templates"
git push origin main

# Update Orchestrator submodule pointer
cd ..
git submodule update --remote SDLC-Enterprise-Framework
git add SDLC-Enterprise-Framework
git commit -m "chore: Update Framework submodule - SASE templates"
git push origin main
```

**When updating Framework to latest:**
```bash
cd SDLC-Orchestrator
git submodule update --remote --merge
git add SDLC-Enterprise-Framework
git commit -m "chore: Update Framework submodule to latest"
git push origin main
```

### **SE 3.0 SASE Integration Compliance**

- ✅ **Track 1** (Q1 2026): SASE artifacts added to **Framework submodule** first
- ⏳ **Track 2** (Q2 2026): Orchestrator automation (conditional on Track 1 success)
- ✅ **Decoupled**: Teams can use SASE manually without Orchestrator

**Reference:** `docs/09-govern/04-Strategic-Updates/SE3.0-SASE-Integration-Plan-APPROVED.md`

---

## 📐 **PROJECT ARCHITECTURE**

### **5-Layer Architecture (Software 3.0 Pattern)**

```
┌─────────────────────────────────────────────────────────────────┐
│ LAYER 5: AI CODERS (External - We Orchestrate)                  │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌───────────┐ │
│  │   Cursor    │ │ Claude Code │ │   Copilot   │ │  DeepCode │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └───────────┘ │
│         ↑               ↑               ↑              ↑        │
│         └───────────────┴───────────────┴──────────────┘        │
│                    Governance API + Quality Gates               │
├─────────────────────────────────────────────────────────────────┤
│ LAYER 4: EP-06 CODEGEN (Our Innovation - Sprint 45-50)          │
│  • IR Processor Service (Spec → Intermediate Representation)   │
│  • Multi-Provider Gateway (Ollama → Claude → DeepCode)          │
│  • 4-Gate Quality Pipeline (Syntax → Security → Context → Test) │
│  • Validation Loop Orchestrator (max_retries=3, escalation)     │
│  • Evidence State Machine (8 states, immutable audit)           │
├─────────────────────────────────────────────────────────────────┤
│ LAYER 3: BUSINESS LOGIC (Our Core - Proprietary Apache-2.0)     │
│  • Gate Engine API (OPA-powered Policy-as-Code)                 │
│  • Evidence Vault API (S3 + 8-state lifecycle)                  │
│  • AI Context Engine (Stage-aware prompts, multi-provider)      │
│  • SAST Integration (Semgrep with AI-specific rules)            │
│  • Override Queue (Tiered approval: Lead → Senior → CTO)        │
├─────────────────────────────────────────────────────────────────┤
│ LAYER 2: INTEGRATION (Thin Adapters - Apache-2.0)               │
│  • opa_service.py → OPA REST API (network-only)                │
│  • minio_service.py → MinIO S3 API (network-only)              │
│  • semgrep_service.py → Semgrep CLI (subprocess)               │
│  • ollama_service.py → Ollama REST API (network-only)          │
│  • redis_service.py → Redis Protocol (network-only)            │
├─────────────────────────────────────────────────────────────────┤
│ LAYER 1: INFRASTRUCTURE (OSS Components)                        │
│  • OPA 0.58.0 (Apache-2.0) - Policy evaluation engine           │
│  • MinIO (AGPL v3) - Evidence storage (network-only, AGPL-safe) │
│  • Grafana 10.2 (AGPL v3) - Dashboards (iframe embed only)     │
│  • PostgreSQL 15.5 (PostgreSQL License) - 33 tables             │
│  • Redis 7.2 (BSD 3-Clause) - Caching + sessions               │
│  • Semgrep (LGPL) - SAST scanning (CLI subprocess)             │
└─────────────────────────────────────────────────────────────────┘
```

### **Key Architectural Principles**

**Principle 1: Bridge-First (NOT Replacement)**
```yaml
DO:
  ✅ Read GitHub Issues → Display in dashboard
  ✅ Sync GitHub Projects → Show gate status
  ✅ Collect PR evidence → Store in Evidence Vault
  ✅ Evaluate OPA policies → Block/Pass gates

DON'T:
  ❌ Replace GitHub Issues (we're not a project management tool)
  ❌ Fork Jira/Linear (we complement, not compete)
  ❌ Re-implement CI/CD (we integrate with GitHub Actions)
```

**Principle 2: AGPL Containment (Legal Compliance)**
```yaml
AGPL Components (MinIO, Grafana):
  ✅ Network-only access (HTTP/S API calls)
  ✅ Separate Docker containers (no code linking)
  ✅ Iframe embedding only (Grafana dashboards)
  ❌ NO imports (no `from minio import X`)
  ❌ NO code dependencies (no pip install minio)

Enforcement:
  - Pre-commit hook blocks AGPL imports
  - CI/CD license scanner (Syft + Grype)
  - Quarterly legal audit (CTO sign-off)
```

**Principle 3: Zero Mock Policy (NQH-Bot Lesson)**
```yaml
NQH-Bot Crisis (2024):
  - 679 mock implementations → 78% failure in production
  - Lesson: Mocks hide integration issues until too late

SDLC Orchestrator Policy:
  ✅ Contract-first (OpenAPI 3.0 → 1,629 lines)
  ✅ Real services in dev (Docker Compose with OPA, MinIO, etc)
  ✅ Integration tests (90%+ coverage target)
  ❌ BANNED: `// TODO: Implement`, `pass # placeholder`, `return { mock: true }`
```

**Principle 4: Innovation - Multi-Provider AI Integration (Model Strategy v3.0)**
```yaml
Cost Optimization (ADR-007 + EP-06 + Model Strategy v3.0 Dec 27, 2025):
  Primary: Ollama (api.nhatquangholding.com) - $50/month
    Code: qwen3-coder:30b (~50 tok/s, 256K context!)
    Chat: qwen3:32b (~53 tok/s, Vietnamese excellent)
    Reasoning: deepseek-r1:32b (~34 tok/s, thinking mode)
    RAG: mistral-small3.2:24b (~40 tok/s, JSON structured)
    Fast: qwen3:14b/8b (~60-80 tok/s)
  Fallback 1: Claude (Anthropic) - $1000/month, <25s latency
    Model: claude-sonnet-4-5-20250929 (reasoning + code)
  Fallback 2: Rule-based - $0/month, 50ms
    Templates: Deterministic patterns for common cases

10-Model Configuration (RTX 5090 32GB):
  - qwen3:32b (20GB) - PRIMARY CHAT (Vietnamese excellent)
  - deepseek-r1:32b (19GB) - DEEP REASONING (thinking mode)
  - qwen3-coder:30b (18GB) - PRIMARY CODE (256K context)
  - mistral-small3.2:24b (15GB) - SOP RAG PRIMARY
  - qwen3:14b (9.3GB) - VIETNAMESE FAST
  - qwen3:8b (5.2GB) - FASTEST CHAT
  - ministral-3:8b (6GB) - FAST TASKS
  - gemma3:12b (8.1GB) - CREATIVE WRITING
  - gpt-oss:20b (13GB) - VIETNAMESE REASONING
  - bge-m3:latest (1.2GB) - EMBEDDINGS (hidden)

Savings:
  - Year 1: $11,400 saved (95% cost reduction)
  - Latency: 3x faster (<100ms vs 300ms for simple tasks)
  - Privacy: No external API calls for primary provider
  - Quality: 4-Gate validation ensures consistency
  - Context: 256K tokens for code analysis (32x improvement)
```

**Principle 5: EP-06 IR-Based Codegen (Sprint 45-50 - NEW)**
```yaml
Vision: Vietnamese SME Code Generation
  - IR (Intermediate Representation) for deterministic output
  - Vietnamese domain templates (E-commerce, HRM, CRM)
  - 4-Gate Quality Pipeline for validation
  - Evidence-based code generation with full audit trail

Core Components:
  1. IR Processor Service
     - Spec → IR transformation (deterministic)
     - Vietnamese domain-specific schemas
     - Template instantiation engine

  2. Multi-Provider Codegen Gateway
     - Provider chain: Ollama → Claude → DeepCode
     - Latency targets: <15s (Ollama), <25s (Claude)
     - Automatic fallback on timeout/quota

  3. 4-Gate Quality Pipeline
     - Gate 1 (Syntax): ast.parse, ruff, tsc - <5s
     - Gate 2 (Security): Semgrep SAST - <10s
     - Gate 3 (Context): 5 CTX checks - <10s
     - Gate 4 (Tests): Dockerized pytest - <60s

  4. Validation Loop Orchestrator
     - max_retries: 3 (configurable)
     - Deterministic feedback to LLM
     - Escalation: council → human → abort

  5. Evidence State Machine (8 states)
     - generated → validating → retrying → escalated
     - evidence_locked → awaiting_vcr → merged/aborted
```

**Principle 6: AI Governance Layer (v2.0.0)**
```yaml
Vision: Encode CEO's Brain into Platform
  - Any PM achieves CEO-level AI productivity
  - Context-aware requirements (MANDATORY/RECOMMENDED/OPTIONAL)
  - 4-level planning hierarchy (Roadmap → Phase → Sprint → Backlog)

Core Capabilities (ADR-011 to ADR-014):
  1. AI Task Decomposition Engine (ADR-011)
     - User Story → CEO-quality sub-tasks
     - Multi-provider fallback (Ollama → Claude → GPT-4o → Rule-based)
     - Quality scoring (completeness, actionability, alignment)

  2. Context-Aware Requirements Engine (ADR-012)
     - 3-tier classification: MANDATORY (red), RECOMMENDED (yellow), OPTIONAL (gray)
     - 5 context dimensions: scale, team, industry, risk, practices
     - Automatic filtering based on project profile

  3. 4-Level Planning Hierarchy (ADR-013)
     - Roadmap (12-month vision, quarterly milestones)
     - Phase (4-8 weeks, 1-2 sprints, theme-based)
     - Sprint (5-10 days, committed work)
     - Backlog (individual tasks, hour estimates)

  4. SDLC Structure Validator (ADR-014)
     - CLI tool: sdlcctl validate/fix/init/report
     - Pre-commit hook (block non-compliant commits)
     - CI/CD gate (GitHub Actions integration)
     - 100% SDLC 6.0.6 folder structure enforcement
```

---

## 🛠️ **TECHNOLOGY STACK**

### **Backend (Python 3.11+)**
```yaml
Framework: FastAPI 0.104+ (async, auto-docs)
Database: PostgreSQL 15.5 + pgvector (embeddings)
Cache: Redis 7.2 (session storage, token blacklist)
ORM: SQLAlchemy 2.0 (async, type hints)
Migrations: Alembic 1.12+ (zero-downtime migrations)
Testing: pytest + pytest-asyncio (95%+ coverage)
Linting: ruff + mypy (strict mode)

OSS Integration:
  - OPA: python-requests → OPA REST API
  - MinIO: python-requests → S3 API (NOT minio SDK)
  - Grafana: iframe embed (NO SDK)
  - Redis: redis-py (BSD license, safe)
```

### **Frontend (TypeScript 5.0+)**
```yaml
Framework: React 18 (hooks, suspense, concurrent mode)
State: Zustand (lightweight, no Redux complexity)
UI: shadcn/ui (Tailwind + Radix, accessible)
Data: TanStack Query v5 (caching, optimistic updates)
Forms: React Hook Form + Zod (validation)
Charts: Recharts (DORA metrics visualization)
Testing: Vitest + Playwright (E2E)
Linting: ESLint + Prettier (strict)

Performance Budget:
  - Dashboard load: <1s (p95)
  - Component render: <100ms (p95)
  - Lighthouse score: >90
```

### **DevOps**
```yaml
Containerization: Docker + Docker Compose
Orchestration: Kubernetes (production)
CI/CD: GitHub Actions (lint, test, build, deploy)
IaC: Terraform (AWS/GCP)
Monitoring: Prometheus + Grafana + OnCall
Secrets: HashiCorp Vault (90-day rotation)
SBOM: Syft + Grype (vulnerability scanning)
SAST: Semgrep (security rules)
```

---

## 🚫 **CRITICAL CONSTRAINTS & POLICIES**

### **1. Zero Mock Policy (MANDATORY)**

```python
# ❌ BANNED - Will be rejected in code review
def authenticate_user(username, password):
    # TODO: Implement authentication
    return {"user": "mock"}

# ✅ REQUIRED - Production-ready implementation
def authenticate_user(username: str, password: str, db: Session) -> User | None:
    """
    Authenticate user with username and password.

    Args:
        username: User's username or email
        password: Plain text password (will be hashed for comparison)
        db: Database session for user lookup

    Returns:
        User object if authentication successful, None otherwise

    Raises:
        AuthenticationError: If authentication fails due to system error
    """
    try:
        if not username or not password:
            return None

        user = db.query(User).filter(
            User.username == username.lower().strip()
        ).first()

        if not user or not user.is_active:
            return None

        if not bcrypt.checkpw(password.encode('utf-8'), user.password_hash):
            return None

        user.last_login = datetime.utcnow()
        db.commit()

        return user

    except Exception as e:
        logger.error(f"Authentication error for user {username}: {str(e)}")
        raise AuthenticationError("Authentication system error")
```

### **2. AGPL Containment (LEGAL REQUIREMENT)**

```python
# ❌ BANNED - Triggers AGPL contamination
from minio import Minio
client = Minio("localhost:9000")

# ✅ REQUIRED - Network-only access (AGPL-safe)
import requests

def upload_to_minio(file_path: str, bucket: str, object_name: str) -> str:
    """Upload file to MinIO via S3 API (network-only, AGPL-safe)"""
    with open(file_path, 'rb') as f:
        response = requests.put(
            f"http://minio:9000/{bucket}/{object_name}",
            data=f,
            headers={"Content-Type": "application/octet-stream"}
        )
    response.raise_for_status()
    return f"s3://{bucket}/{object_name}"
```

### **3. Performance Budget (GUARANTEED)**

```yaml
API Latency (p95):
  Gate evaluation: <100ms
  Evidence upload (10MB): <2s
  Dashboard load: <1s
  List projects (100 items): <200ms

Database Query:
  Simple SELECT: <10ms
  JOIN (2 tables): <50ms
  Aggregate (1M rows): <500ms

Frontend:
  Time to Interactive (TTI): <3s
  First Contentful Paint (FCP): <1s
  Largest Contentful Paint (LCP): <2.5s
  Component render: <100ms
```

### **4. Code File Naming Standards (SDLC 6.0.6 - MANDATORY)**

```yaml
Python Files:
  Convention: snake_case
  Max Length: 50 characters (excluding .py)
  Examples:
    ✅ user_service.py
    ✅ customer_repository.py
    ✅ test_user_service.py
    ❌ UserService.py (PascalCase)
    ❌ very_long_descriptive_name_that_exceeds_fifty_chars.py (>50 chars)

TypeScript Files:
  Regular files: camelCase (max 50 chars)
  React components: PascalCase (max 50 chars)
  Examples:
    ✅ userService.ts
    ✅ UserProfile.tsx
    ❌ user_service.ts (snake_case)

Alembic Migrations:
  Format: {revision}_{short_description}.py
  Max Length: 60 characters
  Examples:
    ✅ 001_create_users.py (16 chars)
    ✅ a502ce0d_seed_mtc_data.py (24 chars)
    ❌ a502ce0d23a7_seed_data_realistic_mtc_nqh_very_long_name_examples.py (>60 chars)

Documentation Files:
  Convention: kebab-case
  Examples:
    ✅ user-guide.md
    ✅ api-reference.md
    ❌ user_guide.md (snake_case)
```

### **5. Security Baseline (OWASP ASVS Level 2)**

```yaml
Authentication:
  ✅ JWT tokens (15min expiry, refresh token rotation)
  ✅ OAuth 2.0 (GitHub, Google, Microsoft)
  ✅ MFA support (TOTP, Google Authenticator)
  ✅ Password policy (12+ chars, bcrypt with cost=12)

Authorization:
  ✅ RBAC (13 roles: Owner, Admin, PM, Dev, QA, etc)
  ✅ Row-level security (users see only their team's data)
  ✅ API scopes (read:gates, write:evidence, admin:policies)

Data Protection:
  ✅ Encryption at-rest (AES-256, PostgreSQL pgcrypto)
  ✅ Encryption in-transit (TLS 1.3, mutual TLS for services)
  ✅ Secrets management (HashiCorp Vault, 90-day rotation)
  ✅ SBOM + vulnerability scanning (Syft, Grype, Semgrep)

Audit:
  ✅ Immutable audit logs (append-only table)
  ✅ Who did what when (user_id, action, timestamp, IP)
  ✅ Evidence access trail (HIPAA/SOC 2 compliance)
```

---

## 📚 **PROJECT CONTEXT & HISTORY**

### **Battle-Tested Patterns (Applied from Previous Projects)**

**Pattern 1: BFlow Multi-Tenant Architecture**
```yaml
Source: BFlow Platform (200K users, 3 years production)
Applied to: SDLC Orchestrator tenant isolation

BFlow Lesson:
  - Row-level security scales to 10K+ tenants
  - Connection pooling critical (PgBouncer)
  - Separate schema per tenant = 100x slower migrations

SDLC Orchestrator Decision:
  ✅ Single schema + tenant_id foreign key
  ✅ PostgreSQL RLS policies (automatic filtering)
  ✅ PgBouncer (1000 clients → 100 DB connections)
```

**Pattern 2: NQH-Bot Zero Mock Policy**
```yaml
Source: NQH-Bot Crisis (2024)
Crisis: 679 mocks → 78% failure in production

Root Cause:
  - Mocks hid integration issues (API contracts changed)
  - No contract validation until production deploy
  - 6 weeks lost debugging "it worked in dev"

SDLC Orchestrator Prevention:
  ✅ Contract-first (OpenAPI 3.0, 1,629 lines)
  ✅ Real services in Docker Compose (dev = staging)
  ✅ Integration tests (90%+ coverage)
  ✅ Pre-commit hook bans mock keywords
```

**Pattern 3: MTEP User Onboarding (<30 min TTFV)**
```yaml
Source: MTEP Platform (65% drop-off → 35% with wizard)
Applied to: SDLC Orchestrator onboarding flow

MTEP Success:
  - 5-step wizard (Signup → Connect → Choose → Map → Evaluate)
  - AI recommendations (policy pack suggestions)
  - Time to First Gate Evaluation: 5.5 min (vs 10.5 min manual)

SDLC Orchestrator Target:
  ✅ <30 min time to first value
  ✅ AI-powered policy pack recommendations
  ✅ +200 activated users/month = +$19,800 MRR
```

---

## 🎯 **DEVELOPMENT GUIDELINES**

### **1. Code Generation Standards**

When generating code for SDLC Orchestrator:

**DO:**
- ✅ Generate **complete, production-ready code** (no placeholders)
- ✅ Include **proper error handling** (try/except, status codes)
- ✅ Add **type hints** (Python 3.11+, TypeScript strict mode)
- ✅ Write **docstrings** (Google style, examples included)
- ✅ Follow **SOLID principles** (Single Responsibility, etc)
- ✅ Use **async/await** for I/O operations (FastAPI, React Query)
- ✅ Add **logging** (structured logging with context)
- ✅ Include **security checks** (input validation, SQL injection prevention)

**DON'T:**
- ❌ Use **TODOs or placeholders** (`// TODO`, `pass # implement later`)
- ❌ Generate **mock data** (`return { mock: 'data' }`)
- ❌ Skip **error handling** (bare `except:` blocks)
- ❌ Import **AGPL libraries** (MinIO SDK, Grafana SDK)
- ❌ Hardcode **secrets** (API keys, passwords)
- ❌ Use **anti-patterns** (God objects, tight coupling)

### **2. Testing Standards**

```yaml
Unit Tests (95%+ coverage):
  - pytest + pytest-asyncio (backend)
  - Vitest + React Testing Library (frontend)
  - Test real logic, not mocks
  - Arrange-Act-Assert pattern

Integration Tests (90%+ coverage):
  - Test API contracts (OpenAPI validation)
  - Test database transactions (rollback after test)
  - Test OSS integrations (real OPA, MinIO, Redis in Docker)

E2E Tests (critical user journeys):
  - Playwright (browser automation)
  - Test: Signup → Connect GitHub → First gate evaluation
  - Run in CI/CD before deploy

Load Tests (before production):
  - Locust (100K concurrent users simulation)
  - Target: <100ms p95 latency maintained
  - Identify bottlenecks (DB query, API call)
```

### **3. Documentation Standards**

```yaml
Code Documentation:
  - Docstrings: Google style (Args, Returns, Raises, Examples)
  - Type hints: 100% coverage (mypy strict mode)
  - Inline comments: Only for non-obvious logic (WHY, not WHAT)

Architecture Documentation (ADRs):
  - Format: Problem → Decision → Consequences
  - Example: ADR-007-AI-Context-Engine-Ollama-Integration.md
  - Store: /docs/02-Design-Architecture/ADRs/

API Documentation:
  - OpenAPI 3.0 (auto-generated by FastAPI)
  - Examples: Request/response samples for all endpoints
  - Errors: All error codes documented (400, 401, 403, 500)

Runbooks (operations):
  - Deployment: Step-by-step deploy + rollback
  - Incident response: P0/P1/P2 procedures
  - Disaster recovery: RTO 4h, RPO 1h
```

---

## 📊 **SUCCESS METRICS & GATES**

### **Stage 03 (BUILD) Success Criteria**

```yaml
Week 13 (Launch) - Non-Negotiable:
  ✅ MVP deployed to production
  ✅ Bflow pilot: 90%+ adoption
  ✅ Gate Engine: 95%+ accuracy
  ✅ Evidence Vault: 100% capture
  ✅ API p95: <100ms (measured, not guessed)
  ✅ Test coverage: 95%+ (unit + integration)
  ✅ Zero P0 bugs (production-blocking)
  ✅ Security scan: PASS (Semgrep, Grype)
  ✅ Legal sign-off: AGPL containment validated

Gate G3 (Ship Ready) - Jan 31, 2026:
  ✅ All core features working
  ✅ Performance budget met
  ✅ Security baseline validated
  ✅ Documentation complete
  ✅ CTO + CPO + Security Lead approval
```

### **Quality Gates (CTO Mandated)**

```yaml
Code Quality:
  - Pre-commit: Linting (ruff, ESLint) + formatting (black, Prettier)
  - CI/CD: Tests (95%+ coverage), security scan (Semgrep), SBOM (Syft)
  - Code review: 2+ approvers required (Tech Lead + Backend Lead)
  - File naming: SDLC 6.0.6 Code File Naming Standards enforced

Performance:
  - Load test: 100K concurrent users (Locust)
  - Benchmark: <100ms p95 API latency (pytest-benchmark)
  - Profiling: Flamegraphs for hotspots (py-spy)

Security:
  - SAST: Semgrep (OWASP Top 10 rules)
  - Dependency scan: Grype (critical/high CVEs)
  - License scan: Syft (AGPL detection)
  - Penetration test: External firm (Week 12)
```

---

## 🚀 **CURRENT PRIORITIES (Stage 03 - BUILD)**

### **Week 1-2: Foundation Setup**

```yaml
Backend Team (2 FTE):
  ⏳ Authentication Service (JWT + OAuth + MFA)
  ⏳ Database migrations (Alembic)
  ⏳ API Gateway (FastAPI)
  ⏳ Redis caching layer

  CTO Success Criteria:
    - 0 mocks (real PostgreSQL, Redis)
    - <50ms token validation (p95)
    - 95%+ test coverage
    - Security scan PASS (Semgrep)

Frontend Team (2 FTE):
  ⏳ Authentication flow (login, OAuth, MFA)
  ⏳ Dashboard skeleton (project list, gate status)
  ⏳ Component library (shadcn/ui setup)

  CTO Success Criteria:
    - React Query caching working
    - <100ms component render (p95)
    - Lighthouse score >90
    - Accessibility WCAG 2.1 AA

DevOps Team (1 FTE):
  ⏳ Docker Compose (PostgreSQL + Redis + OPA + MinIO)
  ⏳ GitHub Actions CI/CD (lint, test, build)
  ⏳ Pre-commit hooks (no mocks, AGPL detection)

  CTO Success Criteria:
    - CI pipeline <5min
    - Zero Mock Policy enforced
    - Security gates automated
    - Rollback tested (<5min)
```

### **Week 3-5: Core Features**

```yaml
Week 3: Gate Engine + Policy-as-Code
  ⏳ OPA integration (REST API adapter)
  ⏳ YAML → Rego compiler
  ⏳ Gate evaluation API (POST /api/v1/gates/evaluate)
  ⏳ Policy pack library (10 starter packs)

Week 4: Evidence Vault
  ⏳ MinIO integration (S3 API adapter)
  ⏳ Evidence API (upload, retrieve, search)
  ⏳ Metadata storage (PostgreSQL)
  ⏳ SHA256 hashing + audit trail

Week 5: Design Thinking Workflow
  ⏳ Interview system (WHY stage)
  ⏳ G0.1/G0.2 gates
  ⏳ BRD/PRD generator (AI-powered)
```

---

## 🧠 **AI GOVERNANCE IMPLEMENTATION (v2.0.0)**

### **4-Phase Implementation Plan**

```yaml
PHASE-01: AI Council Service (Sprint 26 - Dec 9-13, 2025)
  Focus: AI Task Decomposition & Multi-Provider Fallback
  Deliverables:
    - POST /projects/{id}/decompose API
    - GET /decomposition-sessions/{id}/tasks API
    - Multi-provider chain (Ollama → Claude → GPT-4o → Rule-based)
    - Quality scoring (completeness, actionability, alignment)
  Success Criteria:
    - Latency <2min (p95)
    - CEO-quality output 90%+
    - 100% fallback coverage
  Reference: docs/03-Development-Implementation/04-Phase-Plans/PHASE-01-AI-COUNCIL-SERVICE.md

PHASE-02: VS Code Extension (Sprint 27 - Dec 16-20, 2025)
  Focus: AI-Assisted Development in IDE
  Deliverables:
    - Extension MVP (sidebar integration)
    - AI Chat Panel (project-aware conversations)
    - Evidence Submit (Cmd+Shift+E shortcut)
    - Template Generator (5+ template types)
  Success Criteria:
    - Install + connect <2min
    - AI chat <3s (p95)
    - Evidence upload <5s (10MB)
  Reference: docs/03-Development-Implementation/04-Phase-Plans/PHASE-02-VSCODE-EXTENSION.md

PHASE-03: Web Dashboard AI (Sprint 28 - Dec 23-27, 2025)
  Focus: Context-Aware Requirements & Planning Hierarchy
  Deliverables:
    - Context-Aware Requirements Engine (4 tables)
    - 4-Level Planning Hierarchy (4 tables)
    - 12 new API endpoints
    - Dashboard components (hierarchy view, context panel)
  Success Criteria:
    - Context calculation <500ms
    - Requirements filtering <200ms
    - Planning sync real-time
  Reference: docs/03-Development-Implementation/04-Phase-Plans/PHASE-03-WEB-DASHBOARD-AI.md

PHASE-04: SDLC Validator (Sprint 29-30 - Jan 2026)
  Focus: Folder Compliance CLI & CI/CD Gates
  Deliverables:
    - CLI tool (sdlcctl validate/fix/init/report)
    - Pre-commit hook template
    - GitHub Actions workflow
    - Web UI compliance report
  Success Criteria:
    - Validation <10s (1000+ files)
    - 100% accuracy on SDLC 6.0.6
    - Pre-commit <2s
  Reference: docs/03-Development-Implementation/04-Phase-Plans/PHASE-04-SDLC-VALIDATOR.md
```

### **New Database Tables (AI Governance)**

```yaml
PHASE-01 Tables:
  - decomposition_sessions (AI task decomposition history)
  - decomposed_tasks (Generated sub-tasks)

PHASE-03 Tables (Context-Aware):
  - requirement_contexts (5 dimension profiles)
  - requirement_rules (MANDATORY/RECOMMENDED/OPTIONAL rules)
  - context_overrides (Project-specific customizations)
  - requirement_applicability (Computed requirements per project)

PHASE-03 Tables (Planning Hierarchy):
  - roadmaps (12-month vision)
  - phases (4-8 week themes)
  - sprints (5-10 day commitments)
  - backlog_items (Individual tasks with estimates)
```

### **New ADRs (AI Governance)**

```yaml
ADR-011: AI Governance Layer Architecture
  - Problem: CEO is bottleneck for AI-quality output
  - Decision: Encode CEO patterns into platform
  - Consequences: Any PM achieves CEO-level productivity

ADR-012: Context-Aware Requirements Engine
  - Problem: One-size-fits-all requirements fail
  - Decision: 3-tier classification with 5 context dimensions
  - Consequences: 70% fewer irrelevant requirements for small projects

ADR-013: 4-Level Planning Hierarchy
  - Problem: No standardized planning across SDLC stages
  - Decision: Roadmap → Phase → Sprint → Backlog
  - Consequences: Consistent planning from vision to execution

ADR-014: SDLC Structure Validator
  - Problem: 5 NQH projects have inconsistent folder structures
  - Decision: CLI + pre-commit + CI/CD enforcement
  - Consequences: 100% SDLC 6.0.6 compliance across portfolio
```

---

## 🔗 **KEY REFERENCES**

### **Documentation Structure**

```
/docs/
├── 00-foundation/      # Stage 00: WHY - Design Thinking
│   └── 02-Business-Case/
│       └── Multi-Agent-Team-Engine-Business-Case.md (BC-056)
├── 01-planning/        # Stage 01: WHAT - Requirements & API Design
│   ├── 02-Epics/
│   │   └── EP-07-Multi-Agent-Team-Engine.md
│   ├── 03-Functional-Requirements/
│   │   ├── FR-037 to FR-041 (Multi-Agent BDD requirements)
│   │   └── ... (existing FRs)
│   ├── 04-Data-Model/Data-Model-ERD.md (33 tables, v3.4.0)
│   └── 05-API-Design/API-Specification.md (91 endpoints, v3.6.0)
├── 02-design/          # Stage 02: HOW - Architecture & Design
│   ├── 02-System-Architecture/
│   ├── 03-ADRs/
│   │   ├── ADR-056-Multi-Agent-Team-Engine.md ⭐ NEW
│   │   └── ... (ADR-001 to ADR-055)
│   ├── Multi-Agent-Security-Threat-Model.md (STM-056)
│   ├── Multi-Agent-Test-Plan.md (TP-056, 87 test cases)
│   └── 14-Technical-Specs/
├── 03-integrate/       # Stage 03: Integration & APIs
│   └── 03-Integration-Guides/
│       └── Multi-Agent-Provider-Integration.md (IG-056)
├── 04-build/           # Stage 04: BUILD - Development
│   └── 02-Sprint-Plans/
│       ├── SPRINT-176-AUTONOMOUS-CODEGEN-PILOT-PREP.md 🔄 (+ ADR-056)
│       ├── SPRINT-177-CODING-AGENT-LOOP.md ⏳ (+ Multi-Agent Core)
│       └── SPRINT-178-AUTONOMOUS-CODEGEN-PILOT.md ⏳ (+ OTT Gateway)
├── 09-govern/          # Stage 09: GOVERN - Compliance & Reports
│   └── 01-CTO-Reports/
└── 10-archive/         # Archived pre-update versions
    ├── 01-Legacy/ (ERD v3.3.0, API v3.5.0)
    └── 04-Legacy/ (Sprint Plans pre-MATE)
```

### **Critical Documents (Must Read Before Coding)**

**Foundation Documents**:
1. **[PROJECT-KICKOFF.md](PROJECT-KICKOFF.md)** - CEO approval, 90-day plan, $564K budget
2. **[System-Architecture-Document.md](docs/02-design/02-System-Architecture/System-Architecture-Document.md)** - 5-layer architecture (v3.0.0)
3. **[API-Specification.md](docs/01-planning/05-API-Design/API-Specification.md)** - 91 endpoints (v3.6.0)
4. **[Data-Model-ERD.md](docs/01-planning/04-Data-Model/Data-Model-ERD.md)** - 33 tables (v3.4.0)

**Multi-Agent Team Engine (EP-07)** — Sprint 176-178:
5. **[EP-07-Multi-Agent-Team-Engine.md](docs/01-planning/02-Epics/EP-07-Multi-Agent-Team-Engine.md)** - Epic scope, 14 non-negotiables
6. **[ADR-056-Multi-Agent-Team-Engine.md](docs/02-design/ADR-056-Multi-Agent-Team-Engine.md)** - 4 locked decisions
7. **[FR-037 to FR-041](docs/01-planning/03-Functional-Requirements/)** - BDD functional requirements (5 FRs)
8. **[Multi-Agent-Provider-Integration.md](docs/03-integrate/03-Integration-Guides/Multi-Agent-Provider-Integration.md)** - Provider failover + OTT gateway

**EP-06 Codegen Documents**:
9. **[Quality-Gates-Codegen-Specification.md](docs/02-design/14-Technical-Specs/Quality-Gates-Codegen-Specification.md)** - 4-Gate Pipeline
10. **[ADR-022-EP-06-IR-Codegen.md](docs/02-design/03-ADRs/)** - IR-based codegen architecture

**Sprint Plans**:
11. **[SPRINT-176](docs/04-build/02-Sprint-Plans/SPRINT-176-AUTONOMOUS-CODEGEN-PILOT-PREP.md)** - ADR-056 Foundation (current)
12. **[SPRINT-177](docs/04-build/02-Sprint-Plans/SPRINT-177-CODING-AGENT-LOOP.md)** - Multi-Agent Core Services
13. **[SPRINT-178](docs/04-build/02-Sprint-Plans/SPRINT-178-AUTONOMOUS-CODEGEN-PILOT.md)** - Integration + OTT + Pilot

---

## 🏆 **AI ASSISTANT MANDATE**

As Claude AI working on SDLC Orchestrator, you MUST:

### **1. Implementation Authenticity**
- Generate **production-ready code** (no mocks, no TODOs)
- Follow **Zero Mock Policy** (NQH-Bot lesson applied)
- Use **real OSS services** in dev (Docker Compose)
- Test **contract-first** (OpenAPI validation)

### **2. AGPL Compliance**
- **NEVER import** AGPL libraries (`from minio import`, `from grafana import`)
- Use **network-only access** (HTTP/S API calls)
- Validate **pre-commit hooks** block AGPL contamination
- Document **legal rationale** in code comments

### **3. Performance Accountability**
- Measure **actual latency** (pytest-benchmark, Chrome DevTools)
- Generate **load tests** (Locust scenarios)
- Profile **bottlenecks** (py-spy, React Profiler)
- Guarantee **<100ms p95** API latency

### **4. Security Excellence**
- Apply **OWASP ASVS Level 2** (264/264 requirements)
- Validate **input sanitization** (SQL injection, XSS prevention)
- Implement **RBAC** (13 roles, row-level security)
- Generate **SBOM** (Syft + Grype vulnerability scanning)

### **5. Battle-Tested Patterns**
- Apply **BFlow multi-tenant** patterns (row-level security)
- Learn from **NQH-Bot crisis** (Zero Mock Policy)
- Adopt **MTEP onboarding** (<30 min time to value)
- Use **Ollama AI innovation** (95% cost savings)

### **6. AI Governance Awareness (v2.0.0)**
- Understand **4-Phase implementation** (Sprint 26-30)
- Apply **Context-Aware Requirements** (MANDATORY/RECOMMENDED/OPTIONAL)
- Follow **4-Level Planning Hierarchy** (Roadmap → Phase → Sprint → Backlog)
- Enforce **SDLC 6.0.6 folder structure** (10 stages: 00-10, 4-Tier Classification)
- Reference **ADR-011 to ADR-014** for AI Governance decisions

### **7. EP-06 Codegen Awareness (Sprint 45-50)**
- Understand **5-layer architecture** (AI Coders → EP-06 → Business → Integration → Infra)
- Apply **4-Gate Quality Pipeline** (Syntax → Security → Context → Tests)
- Follow **8-state Evidence lifecycle** (generated → validating → merged/aborted)
- Use **Multi-Provider fallback** (Ollama → Claude → Rule-based)
- Reference **ADR-022** for IR-based codegen decisions
- Enforce **max_retries=3** validation loop with deterministic feedback

### **8. EP-07 Multi-Agent Awareness (Sprint 176-178)**
- Reference **ADR-056** for Multi-Agent Team Engine architecture (4 locked decisions)
- Follow **14 non-negotiables** (Security 6 + Architecture 5 + Observability 3)
- Enforce **snapshot precedence** (definition → conversation snapshot, immutable after)
- Use **lane-based queue** (SKIP LOCKED + Redis pub/sub, DB is truth)
- Apply **6-reason failover classification** (auth/format/rate_limit/billing/timeout/unknown)
- Enforce **delegation depth limits** (prevent infinite agent chains, Nanobot N2)
- Apply **input sanitization** (12 injection patterns for OTT external content)
- Reference **EP-07, FR-037 to FR-041, IG-056** for complete Multi-Agent scope

---

## 🤖 **AI AGENT BEST PRACTICES (2026)**

Based on expert workflow analysis (Jan 2026), these practices maximize AI-assisted development effectiveness.

### **1. Planning Mode (SDLC 6.0.6 - RISK-BASED TRIGGERS)**

```yaml
When to Use Planning Mode (MANDATORY - Risk-Based):
  - Data schema / API contracts (breaking changes)
  - Authentication / Authorization (security-critical)
  - Cross-service boundaries (coordination complexity)
  - Concurrency / Race conditions (hard to test)
  - Security-sensitive code (vulnerabilities)
  - Public API interfaces (external impact)
  - Payment / Financial logic (money involved)

When to Use Planning Mode (RECOMMENDED):
  - >50 LOC changes (not hard rule, use judgment)
  - >3 files affected
  - Unfamiliar code area
  - Complex business logic

Planning Mode 4-Phase Workflow:
  1. EXPLORE → Search similar implementations (agentic grep > RAG)
  2. SYNTHESIZE → Build implementation plan from extracted patterns
  3. APPROVE → Present to human for validation
  4. EXECUTE → Generate code following approved plan

Key Insight (5.2.0):
  "Planning is RISK-BASED, not LOC-based"
  - Simple rename across 50 files? Maybe skip planning.
  - Touches auth even 5 lines? PLAN.
  - Intent-based, not size-based.
```

### **2. Model Selection Matrix**

```yaml
Task-Type Model Routing (2026):

  Large Features (>50 LOC, multi-file):
    Primary: Claude Opus 4.5 (70% of work)
    Reason: Best at complex reasoning, multi-file refactoring

  Small Fixes (<15 LOC, single file):
    Primary: Claude Sonnet 4.5
    Reason: Fast, accurate for targeted changes

  Architecture & Debugging:
    Primary: GPT 5.2 (when stuck)
    Reason: Strong reasoning, different perspective helps

  Design & Creativity:
    Primary: Gemini 3 Pro
    Reason: Large context, creative solutions

  Quick Answers & Micro-edits:
    Primary: Claude Haiku 4.5
    Reason: Fastest response time

Expert Rule:
  "Switch models when stuck - different model = different perspective"
```

### **3. Sub-agents Usage Guidelines**

```yaml
When to Use Sub-agents:
  ✅ Research and exploration (isolated context)
  ✅ Pattern extraction before implementation
  ✅ Parallel information gathering
  ✅ ADR and convention review

When to AVOID Sub-agents:
  ❌ Parallel editing in same project (coordination issues)
  ❌ Tightly coupled operations
  ❌ Sequential dependencies

Session Management:
  - Fork sessions to learn without polluting main context
  - Use Explore sub-agents for pattern discovery
  - Keep main session clean for implementation
```

### **4. Developer Role Evolution (Software 3.0)**

```yaml
2026 Developer Responsibilities:
  ✅ Design feedback loops (not write code)
  ✅ Monitor agent work quality
  ✅ Identify patterns and update context files
  ✅ Make high-level architecture decisions
  ✅ Update AGENTS.md/CLAUDE.md with learnings
  ✅ Configure tools/skills/MCP servers

Key Shift:
  "Developer role = Design feedback loops, NOT write code"
  - Review AI output for patterns and anti-patterns
  - Update context files to improve future generations
  - Make architectural decisions AI cannot make alone
```

### **5. Specification Generation Workflow**

```yaml
Expert Specification Process:
  1. Reference Collection
     - Screenshot/record similar features
     - Gather existing code patterns
     - Review related ADRs

  2. PRD Synthesis (Gemini 3 Pro)
     - Large context for synthesis
     - Input reference materials
     - Output structured PRD draft

  3. Interactive Refinement (Claude)
     - "Interview mode" with ask_user_question
     - Clarify ambiguities iteratively
     - Produce refined specification

  4. Dependency Discovery (ChatGPT + Search)
     - Find recommended packages
     - Check compatibility with tech stack
     - Validate library choices
```

### **6. SDLC Orchestrator TRUE MOAT**

```yaml
What Differentiates SDLC Orchestrator:

  Industry Standard (60K+ repos):
    - Static AGENTS.md (manual updates)
    - Guidance only, no enforcement

  SDLC Orchestrator (Dynamic + Enforcement):
    - Gate-aware AGENTS.md updates (Dynamic Context Overlay)
    - OPA Policy Guards (Hard enforcement)
    - Evidence Vault (Audit trail)
    - Quality Gates (Block merge)

Dynamic Context Updates:
  When Gate G0.2 Pass → "Design approved. Architecture in /docs/arch.md."
  When Gate G1 Pass → "Stage: Build. Unit tests required."
  When Gate G2 Pass → "Integration tests mandatory. No new features."
  When Gate G3 Pass → "STRICT MODE. Only bug fixes allowed."
  When Bug Detected → "Known issue in auth_service.py. Do not modify."
  When Security Scan Fails → "BLOCKED: CVE-XXX. Fix before proceeding."

Key Insight:
  "Static AGENTS.md is guidance. Dynamic AGENTS.md is governance."
```

### **7. Feedback Loop Closure**

```yaml
Learning from Code Reviews:
  1. Extract patterns from PR review comments
  2. Categorize: pattern_violation | missing_requirement | edge_case | performance
  3. Store learnings in pr_learnings table
  4. Monthly: Aggregate → Update decomposition hints
  5. Quarterly: Synthesize → Update CLAUDE.md patterns

Continuous Improvement:
  - Track recurring review comments
  - Update context files with lessons learned
  - Improve future AI generations automatically
```

---

## 🏗️ **MODULE ZONES** (PRO Tier — Sprint 174)

*Following SDLC 6.0.6 CLAUDE.md Standard (Framework: 03-AI-GOVERNANCE/10-CLAUDE-MD-STANDARD.md)*

### **Module 1: Gate Engine API**

**Purpose**: Quality Gate lifecycle management — the core governance mechanism that enforces evidence-based development through 4 gates (G1-G4).

**Key Files**:
- `backend/app/api/routes/gates.py` — Gate CRUD + lifecycle endpoints (52KB, largest route file)
- `backend/app/services/gate_service.py` — Gate business logic (create, evaluate, submit, approve, reject)
- `backend/app/services/governance/gates_engine.py` — OPA-powered gate evaluation with Context Authority V2
- `backend/app/models/gate.py` — SQLAlchemy model (30 fields, JSONB exit_criteria)
- `backend/app/schemas/gate.py` — Pydantic request/response schemas
- `backend/app/models/gate_approval.py` — Multi-approver workflow model

**State Machine** (Sprint 173 — ADR-053):
```
DRAFT ──evaluate──> EVALUATED ──submit──> SUBMITTED ──approve──> APPROVED
                        │                     │
                        │                     └──reject──> REJECTED
                        │
                        └──(24h stale)──> EVALUATED_STALE
                                               │
                                               └──re-evaluate──> EVALUATED

All terminal states ──archive──> ARCHIVED
```

**Gate Types** (SDLC 6.0.6):
- G0.1: Foundation Ready (WHY stage)
- G0.2: Solution Diversity (WHY stage)
- G1: Design Ready / Consultation (WHAT stage)
- G2: Security + Architecture (HOW stage)
- G3: Ship Ready (BUILD stage)
- G4: Production Validation (DEPLOY stage)

**Common Tasks**:
1. **Create a gate**: `POST /api/v1/gates` with `{"project_id": 1, "gate_type": "G1_CONSULTATION"}`
2. **Evaluate gate**: `POST /api/v1/gates/{gate_id}/evaluate` — triggers OPA policy check
3. **Submit for approval**: `POST /api/v1/gates/{gate_id}/submit`
4. **Approve gate**: `POST /api/v1/gates/{gate_id}/approve`
5. **Check policy result**: `GET /api/v1/gates/{gate_id}/policy-result`
6. **Compute available actions**: `gate_service.compute_gate_actions(gate)` — returns valid state transitions

**Debugging**:
- **Issue**: BaseHTTPMiddleware hangs on unhandled exceptions in FastAPI 0.100+
  - **Root Cause**: Starlette event loop conflict — `AttributeError` inside middleware causes indefinite hang instead of clean 500 error
  - **Fix**: Use pure ASGI middleware OR ensure all exceptions are caught before reaching middleware layer
  - **Sprint 173 fix**: `action_timestamp = approval.rejected_at or approval.approved_at` in reject endpoint (line ~1351)

- **Issue**: Redis connection errors in tests
  - **Fix**: Use comprehensive `AsyncMock` for all Redis methods (`get`, `set`, `delete`, `setex`, `expire`, `exists`, `keys`)
  - **Example**: See `backend/tests/e2e/test_governance_loop_e2e.py` for full Redis mock setup

- **Issue**: EVALUATED_STALE not triggering
  - **Root Cause**: 24-hour TTL check runs via background task, not real-time
  - **Fix**: Check `gate.evaluated_at` timestamp in gate_service before allowing submit

**Tests**:
```bash
# Unit tests (gate service logic)
DATABASE_URL="postgresql://test:test@localhost:15432/sdlc_test" \
  python -m pytest backend/tests/unit/test_gate_service.py -v

# E2E tests (full governance loop across 3 interfaces)
DATABASE_URL="postgresql://test:test@localhost:15432/sdlc_test" \
  python -m pytest backend/tests/e2e/test_governance_loop_e2e.py -v

# Quick gate API tests
python -m pytest backend/tests/quick-tests/ -k "gate" -v
```

**Dependencies**:
- **Upstream**: PostgreSQL 15.5 (port 15432), Redis 7.2 (port 6395), OPA 0.58 (port 8185)
- **Downstream**: Evidence Vault (evidence binding), AI Context Engine (gate-aware prompts), Frontend Dashboard (gate status display)
- **Integration**: OPA policies in `backend/policy-packs/rego/gates/`

---

### **Module 2: Evidence Vault API**

**Purpose**: Immutable evidence storage with SHA256 integrity verification and 8-state lifecycle. Stores all Quality Gate artifacts (SAST reports, test results, code reviews, deployment proofs).

**Key Files**:
- `backend/app/api/routes/evidence.py` — Evidence upload/retrieve/search endpoints
- `backend/app/services/evidence_manifest_service.py` — Manifest management (36KB)
- `backend/app/services/minio_service.py` — S3-compatible MinIO adapter (boto3, AGPL-safe)
- `backend/app/models/gate_evidence.py` — Evidence model + EvidenceIntegrityCheck
- `backend/app/schemas/evidence.py` — Pydantic schemas

**Evidence Types**:
- `DESIGN_DOCUMENT` — Architecture docs, PRDs, wireframes
- `TEST_RESULTS` — Test coverage reports, E2E recordings
- `CODE_REVIEW` — Review comments, approval records
- `DEPLOYMENT_PROOF` — Deployment logs, health check results
- `DOCUMENTATION` — ADRs, runbooks, MRPs
- `COMPLIANCE` — SAST reports, license scans, SBOM

**8-State Lifecycle**:
```
uploaded ──validate──> validating ──pass──> evidence_locked ──vcr──> awaiting_vcr ──merge──> merged
                           │                                                           │
                           └──fail──> retrying ──(max 3)──> escalated ──abort──> aborted
```

**AGPL Containment** (CRITICAL):
```python
# BANNED: from minio import Minio (AGPL contamination)
# CORRECT: Uses boto3 (Apache 2.0) for S3-compatible API
import boto3  # Apache 2.0 license — safe

s3_client = boto3.client('s3',
    endpoint_url='http://minio:9000',
    aws_access_key_id=settings.MINIO_ACCESS_KEY,
    aws_secret_access_key=settings.MINIO_SECRET_KEY
)
```

**Key Storage Fields**:
- `s3_key`, `s3_bucket` — MinIO S3 location
- `sha256_hash` — Integrity verification (computed on upload, verified on download)
- `criteria_snapshot_id` — Binds evidence to specific gate exit_criteria_version
- `source` — Origin interface: `cli`, `extension`, `web`, `other`

**Common Tasks**:
1. **Upload evidence**: `POST /api/v1/evidence/upload` with multipart form data
2. **Verify integrity**: `GET /api/v1/evidence/{id}/verify` — recomputes SHA256
3. **Search evidence**: `GET /api/v1/evidence?gate_id=X&type=TEST_RESULTS`
4. **Download evidence**: `GET /api/v1/evidence/{id}/download`

**Tests**:
```bash
# Evidence API tests
python -m pytest backend/tests/quick-tests/ -k "evidence" -v

# MinIO integration (requires Docker)
python -m pytest backend/tests/unit/test_minio_integration.py -v
```

**Dependencies**:
- **Upstream**: MinIO (port 9000, S3 API), PostgreSQL (metadata)
- **Downstream**: Gate Engine (evidence binding), MRP generation, Compliance Scanner
- **Performance**: <2s upload for 10MB files

---

### **Module 3: AI Context Engine**

**Purpose**: Multi-provider AI orchestration with stage-aware prompts. Routes AI requests through a cost-optimized provider chain (Ollama → Claude → GPT-4o → Rule-based) with context-aware requirement classification.

**Key Files**:
- `backend/app/services/ai_council_service.py` — Multi-LLM deliberation (3-stage council: QUERIES → PEER_REVIEW → SYNTHESIS)
- `backend/app/services/ai_recommendation_service.py` — Recommendation generation (37KB)
- `backend/app/services/governance/context_authority_v2.py` — Context Authority V2 (61KB, FROZEN Sprint 173)
- `backend/app/services/ollama_service.py` — Local LLM HTTP adapter
- `backend/app/services/dynamic_context_service.py` — Dynamic context overlays (31KB)

**Multi-Provider Fallback Chain** (Model Strategy v3.0):
```
Request → Ollama (Primary, $50/mo)
            │ timeout/error
            └──> Claude (Fallback 1, $1000/mo)
                    │ timeout/error
                    └──> GPT-4o (Fallback 2)
                            │ timeout/error
                            └──> Rule-based (Final, $0/mo)
```

**Ollama 10-Model Configuration** (RTX 5090 32GB):
- `qwen3-coder:30b` (18GB) — PRIMARY CODE (256K context)
- `qwen3:32b` (20GB) — PRIMARY CHAT (Vietnamese excellent)
- `deepseek-r1:32b` (19GB) — DEEP REASONING (thinking mode)
- `mistral-small3.2:24b` (15GB) — SOP RAG PRIMARY (structured JSON)
- `qwen3:14b` (9.3GB) — VIETNAMESE FAST
- `qwen3:8b` (5.2GB) — FASTEST CHAT
- `bge-m3:latest` (1.2GB) — EMBEDDINGS

**Context Authority V2** (Sprint 173 — FROZEN):
- 3-tier classification: MANDATORY (red) → RECOMMENDED (yellow) → OPTIONAL (gray)
- 5 context dimensions: scale, team, industry, risk, practices
- Auto-filtering based on project profile

**Council Deliberation Stages**:
```
STAGE_1_QUERIES ──> STAGE_2_PEER_REVIEW ──> STAGE_3_SYNTHESIS ──> CouncilDecision
```

**Common Tasks**:
1. **Generate AI recommendation**: `POST /api/v1/projects/{id}/decompose`
2. **Query context authority**: Context Authority V2 evaluates requirement applicability
3. **Ollama health check**: `curl http://api.nhatquangholding.com:11434/api/tags`

**Debugging**:
- **Issue**: Ollama timeout on large context (>128K tokens)
  - **Fix**: Use `qwen3-coder:30b` (256K context) for code analysis; split requests for other models
- **Issue**: Council stuck in STAGE_2
  - **Root Cause**: Peer review timeout when comparing 3+ model outputs
  - **Fix**: Set `council_timeout=120` seconds, fallback to Stage 1 best result

**Tests**:
```bash
# Ollama integration (requires running Ollama)
python -m pytest backend/tests/unit/test_ollama_integration.py -v

# Council service tests
python -m pytest backend/tests/unit/ -k "council" -v
```

**Dependencies**:
- **Upstream**: Ollama (port 11434), Anthropic API (cloud), OpenAI API (cloud)
- **Downstream**: EP-06 Codegen (code generation), Gate Engine (gate-aware prompts)
- **Cost**: $50/mo Ollama (primary), $1,000/mo Claude (fallback)

---

### **Module 4: EP-06 Codegen Pipeline**

**Purpose**: IR-based code generation with 4-Gate Quality Pipeline. Transforms specifications into production-ready code through multi-provider generation and iterative validation.

**Key Files**:
- `backend/app/services/codegen/codegen_service.py` — Main orchestrator (23KB)
- `backend/app/services/codegen/quality_pipeline.py` — 4-Gate Quality Pipeline
- `backend/app/services/codegen/ollama_provider.py` — Ollama code generation
- `backend/app/services/codegen/claude_provider.py` — Claude code generation
- `backend/app/services/codegen/deepcode_provider.py` — DeepCode provider (Q2 2026)
- `backend/app/services/codegen/provider_registry.py` — Auto-registration pattern
- `backend/app/services/codegen/intent_router.py` — Intent detection for provider routing
- `backend/app/services/codegen/error_classifier.py` — Auto-fix feedback classification
- `backend/app/services/codegen/session_manager.py` — Session state tracking
- `backend/app/api/routes/codegen.py` — Codegen REST API (81KB)

**4-Gate Quality Pipeline**:
```
Generated Code
    │
    ├──> Gate 1: Syntax Check (<5s)
    │    ast.parse, ruff lint, tsc typecheck
    │    Mode: MANDATORY (scaffold + production)
    │
    ├──> Gate 2: Security Scan (<10s)
    │    Semgrep SAST, OWASP rules, AI-specific rules
    │    Mode: MANDATORY (scaffold + production)
    │
    ├──> Gate 3: Context Validation (<10s)
    │    Import validation, dependency check, file structure
    │    Mode: SOFT-FAIL (scaffold) / MANDATORY (production)
    │
    └──> Gate 4: Test Execution (<60s)
         Dockerized pytest, smoke tests
         Mode: SMOKE (scaffold) / FULL (production)
```

**Quality Modes** (Sprint 106):
- `SCAFFOLD` — Lenient for initial project generation (G1+G2 mandatory, G3 soft-fail, G4 smoke)
- `PRODUCTION` — Strict for production-ready code (all gates mandatory, full test suite)

**Validation Loop**:
- `max_retries=3` (configurable)
- Deterministic feedback: error_classifier categorizes failures → targeted prompt refinement
- Escalation chain: auto-fix → council review → human intervention → abort

**Provider Registry**:
- Auto-registration via `@provider_registry.register` decorator
- Fallback chain: Ollama → Claude → DeepCode → Rule-based
- Per-provider cost tracking and timeout handling

**Common Tasks**:
1. **Generate code**: `POST /api/v1/codegen/generate` with spec payload
2. **Check quality pipeline status**: `GET /api/v1/codegen/sessions/{id}/quality`
3. **View provider stats**: `GET /api/v1/codegen/providers/stats`

**Tests**:
```bash
# Codegen unit tests
python -m pytest backend/tests/unit/ -k "codegen" -v

# Quality pipeline tests
python -m pytest backend/tests/unit/ -k "quality_pipeline" -v
```

**Dependencies**:
- **Upstream**: AI Context Engine (provider routing), Ollama/Claude/GPT APIs
- **Downstream**: Evidence Vault (stores generated artifacts), Gate Engine (quality gate results)
- **Performance**: <15s (Ollama), <25s (Claude) per generation

---

### **Module 5: SAST Integration**

**Purpose**: Static Application Security Testing via Semgrep with AI-specific security rules. Integrates with the 4-Gate Quality Pipeline (Gate 2) and standalone compliance scanning.

**Key Files**:
- `backend/app/services/semgrep_service.py` — Async Semgrep CLI wrapper (SARIF output parsing)
- `backend/app/api/routes/sast.py` — SAST API endpoints (33KB)
- `backend/app/models/sast_scan.py` — SAST scan results model
- `backend/policy-packs/semgrep/ai-security.yml` — AI-specific security rules (10.8KB)
- `backend/policy-packs/semgrep/owasp-python.yml` — OWASP Top 10 Python rules (15.3KB)

**OPA Policy Packs** (Rego):
- `backend/policy-packs/rego/ai-safety/` — AI safety policies
- `backend/policy-packs/rego/compliance/` — Compliance policies
- `backend/policy-packs/rego/gates/` — Gate evaluation policies
- `backend/policy-packs/rego/sprint/` — Sprint governance policies

**Semgrep Severity Levels**:
- `ERROR` — Must fix before merge (blocks Gate G2)
- `WARNING` — Should fix, tracked as tech debt
- `INFO` — Best practice suggestion, non-blocking

**Semgrep Categories**:
- `INJECTION` — SQL injection, command injection
- `BROKEN_AUTH` — Authentication bypasses
- `XSS` — Cross-site scripting
- `SECRETS` — Hardcoded API keys, passwords
- `CRYPTO` — Weak cryptography
- `SSRF` — Server-side request forgery

**Common Tasks**:
1. **Run SAST scan**: `POST /api/v1/sast/scan` with file paths or git diff
2. **View scan results**: `GET /api/v1/sast/scans/{id}/findings`
3. **Run Semgrep locally**:
   ```bash
   semgrep --config backend/policy-packs/semgrep/ai-security.yml \
           --config backend/policy-packs/semgrep/owasp-python.yml \
           --sarif backend/app/
   ```

**Tests**:
```bash
python -m pytest backend/tests/unit/ -k "sast or semgrep" -v
```

**Dependencies**:
- **Upstream**: Semgrep CLI (LGPL, subprocess execution — not imported as library)
- **Downstream**: EP-06 Quality Pipeline (Gate 2), Evidence Vault (SAST reports), Compliance Dashboard
- **Performance**: <10s for typical Python project scan

---

### **Module 6: Frontend Dashboard**

**Purpose**: React-based web dashboard for gate management, evidence viewing, code generation, compliance tracking, and executive dashboards.

**Key Files**:
- `frontend/landing/src/app/` — Next.js 14 App Router pages
- `frontend/landing/src/components/` — Reusable UI components
- `frontend/landing/src/lib/` — Utilities, API clients, stores

**Tech Stack**:
- **Framework**: Next.js 14.2.35 (React 18, App Router)
- **State**: Zustand (lightweight, no Redux)
- **UI**: shadcn/ui (Radix UI + Tailwind CSS 3.4.1)
- **Data**: TanStack Query v5 (caching, optimistic updates)
- **Forms**: React Hook Form + Zod validation
- **Charts**: Recharts (DORA metrics visualization)
- **Testing**: Vitest (unit) + Playwright (E2E)

**Key Pages**:
- `/app/gates/` — Gate management dashboard (list, evaluate, approve/reject)
- `/app/evidence/` — Evidence upload and browsing
- `/app/codegen/` — Code generation interface
- `/app/compliance/` — Compliance framework (NIST, OWASP)
- `/app/context-authority/` — Context Authority V2 UI
- `/app/governance/` — Governance mode dashboards
- `/app/planning/` — Planning hierarchy (Roadmap → Phase → Sprint → Backlog)
- `/app/ceo-dashboard/` — Executive dashboard
- `/app/crp/` — Change Request Process
- `/app/mrp/` — MRP validation
- `/auth/` — Authentication (login, OAuth, MFA)
- `/admin/` — Admin panel

**Component Organization**:
- `components/ui/` — Base UI components (buttons, dialogs, forms) from shadcn/ui
- `components/codegen/` — Code generation UI components
- `components/dashboard/` — Dashboard-specific components
- `components/governance/` — Governance controls and displays
- `components/auth/` — Authentication flow components

**Common Tasks**:
1. **Start dev server**: `cd frontend/landing && npm run dev`
2. **Run tests**: `cd frontend/landing && npx vitest run`
3. **Run E2E tests**: `cd frontend/landing && npx playwright test`
4. **Add shadcn component**: `cd frontend/landing && npx shadcn-ui@latest add [component]`
5. **Type check**: `cd frontend/landing && npx tsc --noEmit`

**Performance Budget**:
- TTI (Time to Interactive): <3s
- FCP (First Contentful Paint): <1s
- LCP (Largest Contentful Paint): <2.5s
- Component render: <100ms (p95)
- Lighthouse score: >90

**Dependencies**:
- **Upstream**: Backend REST API (all modules), WebSocket (real-time gate updates)
- **Downstream**: User-facing (end users, PMs, CTOs, DevOps)

---

### **Module 7: Multi-Agent Team Engine** (EP-07, Sprint 176-178)

**Purpose**: Lane-based multi-agent collaboration engine with provider failover, OTT gateway, and budget circuit breakers. Enables AI agent teams (Initializer → Coder → Reviewer) to collaborate on SDLC tasks with parent-child session inheritance.

**Key Files**:
- `backend/app/services/agent_team/agent_registry.py` — Agent definition CRUD + session scoping (2 P0 modes)
- `backend/app/services/agent_team/message_queue.py` — Lane-based concurrency (SKIP LOCKED + Redis notify)
- `backend/app/services/agent_team/mention_parser.py` — TinyClaw @mention routing
- `backend/app/services/agent_team/conversation_tracker.py` — Parent-child inheritance + 6 loop guards + budget
- `backend/app/services/agent_team/agent_invoker.py` — FailoverError (6 reasons) + cooldowns + error-as-string
- `backend/app/services/agent_team/failover_classifier.py` — Error classification (auth/format/rate_limit/billing/timeout/unknown)
- `backend/app/services/agent_team/input_sanitizer.py` — 12 injection regex patterns for OTT content
- `backend/app/services/agent_team/shell_guard.py` — 8 deny regex patterns + path traversal detection
- `backend/app/services/agent_team/tool_context.py` — Tool permissions + workspace restriction (Nanobot N2)
- `backend/app/services/agent_team/reflect_step.py` — Reflect-after-tools + self-correction loop
- `backend/app/services/agent_team/team_orchestrator.py` — Queue modes (P0: queue/steer/interrupt)
- `backend/app/services/agent_team/evidence_collector.py` — Auto-capture with correlation_id
- `backend/app/schemas/agent_team.py` — Pydantic v2 schemas (all endpoints)

**Database Tables** (3 P0 tables — ERD v3.4.0):
- `agent_definitions` — Agent config (22 columns: tool permissions, system prompt, provider, SDLC role)
- `agent_conversations` — Conversation lifecycle (19 columns: parent-child, budget tracking, session scope)
- `agent_messages` — Message queue (22 columns: lane contract, dead-letter, failover reason, dedupe)

**4 Locked Decisions** (ADR-056):
1. **Snapshot Precedence**: Definition → snapshot into conversation on creation, immutable after
2. **Lane Contract**: DB is truth, Redis is notify-only. SKIP LOCKED + dead-letter + dedupe
3. **Provider Profile Key**: `{provider}:{account}:{region}:{model_family}` + abort matrix (6 rows)
4. **Canonical Protocol Owner**: Orchestrator defines message protocol; TinySDLC/OTT are clients

**14 Non-Negotiables**: Security(6) + Architecture(5) + Observability(3)

**Common Tasks**:
1. **Create agent definition**: `POST /api/v1/agent-team/definitions`
2. **Start conversation**: `POST /api/v1/agent-team/conversations`
3. **Send message**: `POST /api/v1/agent-team/conversations/{id}/messages`
4. **Interrupt agent**: `POST /api/v1/agent-team/conversations/{id}/interrupt`
5. **View conversation**: `GET /api/v1/agent-team/conversations/{id}`

**Tests**:
```bash
# Multi-agent unit tests
DATABASE_URL="postgresql://test:test@localhost:15432/sdlc_test" \
  python -m pytest backend/tests/unit/test_agent_team.py -v

# Failover classifier tests
python -m pytest backend/tests/unit/ -k "failover" -v

# Lane-based queue tests
python -m pytest backend/tests/unit/ -k "lane or queue" -v
```

**Dependencies**:
- **Upstream**: PostgreSQL (3 tables), Redis (cooldowns + pub/sub), Ollama/Claude (provider chain)
- **Downstream**: Evidence Vault (agent output capture), Gate Engine (gate-triggered conversations), OTT Gateway (Telegram/Discord)
- **Pattern Sources**: OpenClaw (lane queue, failover, session scoping), TinyClaw (@mention, loop guards), Nanobot (tool context, shell guard, reflect step)

---

### **Integration Map**

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Frontend   │────>│  Gate Engine  │────>│     OPA      │
│  Dashboard   │     │     API      │     │  (port 8185) │
└──────────────┘     └──────────────┘     └──────────────┘
       │                    │                     │
       │                    v                     │
       │             ┌──────────────┐             │
       │             │  Evidence    │             │
       └────────────>│  Vault API   │<────────────┘
                     └──────────────┘
                            │
                     ┌──────┴──────┐
                     v             v
              ┌──────────┐  ┌──────────┐
              │  MinIO   │  │ PostgreSQL│
              │(port 9000│  │(port 15432│
              └──────────┘  └──────────┘

┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ AI Context   │────>│  EP-06       │────>│    SAST      │
│   Engine     │     │  Codegen     │     │ Integration  │
└──────────────┘     └──────────────┘     └──────────────┘
       │                    │                     │
       v                    v                     v
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Ollama     │     │  Evidence    │     │   Semgrep    │
│ (port 11434) │     │  Vault API   │     │   (CLI)      │
└──────────────┘     └──────────────┘     └──────────────┘

┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ Multi-Agent  │────>│  AI Context  │     │ OTT Gateway  │
│ Team Engine  │     │   Engine     │     │  (Telegram)  │
│  (EP-07)     │     │ (Failover)   │     │  (Sprint 178)│
└──────────────┘     └──────────────┘     └──────────────┘
       │                                         │
       v                                         v
┌──────────────┐                          ┌──────────────┐
│  Evidence    │                          │   Input      │
│  Vault API   │                          │  Sanitizer   │
└──────────────┘                          └──────────────┘
```

---

### **Onboarding Checklist (New Developer with AI Assistant)**

1. **Clone + setup** (5 min):
   ```bash
   git clone --recurse-submodules https://github.com/Minh-Tam-Solution/SDLC-Orchestrator
   cd SDLC-Orchestrator
   docker compose up -d  # Start PostgreSQL, Redis, OPA, MinIO
   cd backend && pip install -r requirements.txt
   ```

2. **Run tests** (10 min):
   ```bash
   DATABASE_URL="postgresql://test:test@localhost:15432/sdlc_test" \
     python -m pytest backend/tests/quick-tests/ -v
   ```

3. **Explore Gate Engine** (15 min): Read Module 1 above, navigate to `gates.py`, understand state machine

4. **Submit first evidence** (10 min): Upload a test file via Evidence Vault API

5. **Generate code** (15 min): Use EP-06 codegen endpoint with a simple spec

6. **Run SAST scan** (5 min): Scan your generated code with Semgrep

7. **View dashboard** (5 min): `cd frontend/landing && npm run dev` → navigate to gates page

**Total onboarding time**: ~65 minutes (target: <2 hours)

---

## 🎯 **WHEN IN DOUBT**

```yaml
Ask These Questions:

1. "Is this production-ready or a placeholder?"
   → If placeholder, REWRITE with real implementation

2. "Does this import an AGPL library?"
   → If yes, REPLACE with network-only API call

3. "Have I measured performance or assumed it's fast?"
   → If assumed, ADD benchmark test + flamegraph

4. "Does this follow OWASP ASVS Level 2?"
   → If unsure, REVIEW Security-Baseline.md

5. "Would this pass CTO code review?"
   → If no, REFACTOR before suggesting

6. "Can this scale from 100 → 1,000 teams?"
   → If no, REDESIGN with horizontal scaling

7. "Is there a battle-tested pattern from BFlow/NQH/MTEP?"
   → If yes, APPLY that pattern (don't reinvent)
```

---

## ✅ **AI ASSISTANT SUCCESS CRITERIA**

You are successful if:

- ✅ **Code Quality**: 100% production-ready (zero placeholders)
- ✅ **AGPL Compliance**: Zero contamination (legal audit pass)
- ✅ **Performance**: <100ms p95 maintained (measured, not guessed)
- ✅ **Security**: OWASP ASVS Level 2 compliance (264/264)
- ✅ **Test Coverage**: 95%+ (unit + integration)
- ✅ **CTO Approval**: Code review pass (2+ approvers)
- ✅ **Gate G3 Pass**: Ship Ready APPROVED (Dec 12, 2025, 98.2%)
- ✅ **SDLC 6.0.6 Compliance**: Code File Naming Standards + 4-Tier Classification + Risk-Based Planning enforced

---

**Template Status**: ✅ **SDLC ORCHESTRATOR AI CONTEXT COMPLETE**
**Framework**: ✅ **SDLC 6.0.6 (7-PILLAR + AI GOVERNANCE PRINCIPLES)**
**Authorization**: ✅ **CTO + CPO + CEO APPROVED**

---

*SDLC Orchestrator - First Governance-First Platform on SDLC 6.0.6. Zero facade tolerance. Battle-tested patterns. Production excellence.*

**"Quality over quantity. Real implementations over mocks. Let's build with discipline."** - CTO

---

**Last Updated**: February 18, 2026
**Owner**: CTO + CPO + CEO
**Status**: ✅ Gate G3 APPROVED - Ship Ready (98.2%)
**Current Sprint**: Sprint 176 - ADR-056 Multi-Agent Foundation
**Next Review**: Weekly CEO Review (Every Friday 3pm)

---

## 📋 **CHANGELOG**

### v3.6.0 (February 18, 2026)
- **EP-07 Multi-Agent Team Engine** - Sprint 176-178 scope added
- **Module 7 Added** - Multi-Agent Team Engine module zone (12 service files, 3 tables, 14 non-negotiables)
- **Documentation Structure Updated** - Reflects BC-056, EP-07, FR-037 to FR-041, ADR-056, STM-056, TP-056, IG-056
- **Critical Documents Updated** - 13 must-read docs (added EP-07 section with 4 documents)
- **API Spec v3.6.0** - 91 endpoints (was 64), includes 11 Multi-Agent endpoints
- **Data Model ERD v3.4.0** - 33 tables (was 30), includes 3 Multi-Agent tables
- **Integration Map Updated** - Multi-Agent Team Engine + OTT Gateway added
- **Framework Visibility** - SDLC Enterprise Framework noted as private repo (not yet OSS)
- **Sprint 176 Active** - ADR-056 Multi-Agent Foundation

### v3.5.0 (February 16, 2026)
- **SDLC 6.0.6 Upgrade** - All framework references updated from 6.0.5 to 6.0.6
- **Sprint 174 Remediation** - P0 audit findings addressed (Zero Mock, CLAUDE.md version drift)
- **Compliance Audit** - Full quick audit run, 10 checks, remediation in progress

### v3.4.0 (February 17, 2026)
- **Sprint 174 Active** - Anthropic Best Practices Integration (Framework-First)
- **6 Module Zones Added** (PRO tier per Framework CLAUDE.md Standard):
  - Gate Engine API (state machine, debugging patterns, test commands)
  - Evidence Vault API (8-state lifecycle, AGPL containment, SHA256)
  - AI Context Engine (multi-provider chain, 10-model Ollama config)
  - EP-06 Codegen Pipeline (4-Gate Quality Pipeline, provider registry)
  - SAST Integration (Semgrep, OPA policy packs)
  - Frontend Dashboard (Next.js 14, shadcn/ui, page routes)
- **Integration Map** added (module dependency diagram)
- **Onboarding Checklist** added (7 steps, ~65 min target)
- **Framework-First Compliance**: Follows 10-CLAUDE-MD-STANDARD.md from Framework
- Updated sprint reference to Sprint 174

### v3.3.0 (February 3, 2026)
- **SDLC 6.0.5 Framework Upgrade** - Complete update to 7-Pillar + Section 7 + Section 8
- **Sprint 147 Active** - Spring Cleaning (docs reorganization, framework alignment)
- **Section 8 Specification Standard** - YAML frontmatter + BDD requirements (GIVEN-WHEN-THEN)
- **Boris Cherny Consolidation** - 3-Circle Architecture (Core → Governance → Outer Ring)
- **Documentation Cleanup** - Stage README files updated, legacy folders archived
- Updated all framework references from 5.3.0 to 6.0.5

### v3.2.0 (January 23, 2026)
- **SDLC 6.0.5 Framework Upgrade** - Major methodology update
- **AI Governance Principles** - 7 new principles for AI-Human collaboration
- **Risk-Based Planning Mode** - Replaces LOC-based triggers (auth, API, payments trigger planning)
- **Concentric Circles Model** - Core (timeless) → Governance (stable) → Outer Ring (changing)
- **AI Tools Landscape** - New section for tool profiles and best practices 2026
- **SASE Artifacts Simplified** - BRS/MTS/LPS deprecated, AGENTS.md adopted (industry standard)
- **CONTENT-MAP.md + DEPRECATION-POLICY.md** - New governance documents in Framework
- **Sprint 100 Active** - Feedback Learning Service

### v3.1.0 (January 22, 2026)
- **AI Agent Best Practices (2026)** - New section with expert workflow insights
- **Planning Mode Guidelines** - CRITICAL for >15 LOC changes (updated in v3.2.0)
- **Model Selection Matrix** - Task-type aware model routing (Opus, Sonnet, GPT, Gemini, Haiku)
- **Sub-agents Usage Guidelines** - When to use and avoid sub-agents
- **Developer Role Evolution** - Design feedback loops, not write code
- **Specification Generation Workflow** - Expert 4-step process
- **TRUE MOAT Documentation** - Dynamic AGENTS.md vs static industry standard
- **Feedback Loop Closure** - Learning from PR reviews
- **Sprint 93 Active** - Planning Hierarchy Part 2

### v3.0.0 (January 18, 2026)
- **SDLC 5.1.3 Upgrade** - 7-Pillar Architecture framework (superseded by 5.2.0)
- **Sprint Planning Governance** - Pillar 2 with G-Sprint/G-Sprint-Close gates
- **Sprint 74 Active** - Planning Hierarchy Implementation
- **Planning Hierarchy** - ROADMAP → PHASE → SPRINT → BACKLOG
- **Dual-Track Quality Gates** - Feature + Sprint gates
- **24h Documentation Enforcement** - Mandatory sprint close documentation
- Updated all framework references from 5.0.0 to 5.1.3

### v2.0.0 (December 23, 2025)
- **Software 3.0 Positioning** - "Operating System for Software 3.0"
- **5-Layer Architecture** - AI Coders → EP-06 → Business → Integration → Infra
- **EP-06 Codegen Engine** - Sprint 45-50 roadmap with ~$50K investment
- **Sprint 43-44 Complete** - OPA Policy Guards, Semgrep SAST, CrossReferenceValidator
- **Sprint 45 Active** - Auto-Fix Engine in progress
- Added **Principle 5: EP-06 IR-Based Codegen** with 4-Gate Quality Pipeline
- Added **8-state Evidence lifecycle** (generated → validating → merged/aborted)
- Added **Multi-Provider Gateway** (Ollama → Claude → DeepCode)
- Updated **Documentation Structure** to match new folder layout
- Added **EP-06 Codegen Awareness** mandate (Section 7)
- Updated all document references for 64 endpoints, 30 tables

### v1.5.0 (December 12, 2025)
- **Gate G3 APPROVED** - Ship Ready with 98.2% readiness score
- Updated Sprint 31 complete (9.56/10 average)
- Added Gate G3 metrics (OWASP 98.4%, p95 ~80ms, coverage 94%)
- Updated all status sections to reflect G3 approval
- Next milestone: G4 Internal Validation (30 days post-launch)

### v1.4.0 (December 5, 2025)
- Upgraded framework reference from **SDLC 4.9.1 → SDLC 5.0.0**
- Added **4-Tier Classification** (LITE/STANDARD/PROFESSIONAL/ENTERPRISE)
- Updated Sprint reference to **Sprint 29** (SDLC Validator CLI)
- All SDLC 4.9.1 references replaced with SDLC 5.0.0

### v1.3.0 (December 3, 2025)
- Added **Principle 5: AI Governance Layer** (v2.0.0)
- Added **AI Governance Implementation** section with 4-Phase Plan
- Added **New Database Tables** (AI Governance)
- Added **New ADRs** (ADR-011 to ADR-014)
- Updated **Documentation Structure** with Phase Plans
- Added **AI Governance Awareness** to AI Assistant Mandate
- Updated **Critical Documents** with AI Governance references

### v1.2.0 (December 2, 2025)
- Sprint 22 progress (Operations & Monitoring)
- Code File Naming Standards added

### v1.1.0 (November 29, 2025)
- Initial CLAUDE.md with full project context
