# Stage 02: Design & Architecture (HOW?)
## System Architecture + Technical Design

**Version**: 3.2.0
**Date**: January 30, 2026
**Status**: ✅ COMPLETED - Gate G2 PASSED (CTO 9.4/10, CPO 9.2/10)
**Authority**: CTO + Tech Lead + Backend Lead Approved
**Foundation**: SDLC 6.1.0 (7-Pillar + Section 7 Quality Assurance + Section 8 Specification Standard)
**Previous Stage**: Stage 01 (Planning & Analysis - WHAT) ✅ COMPLETE
**Next Stage**: Stage 04 (BUILD) - Sprint 122 Stabilization
**Positioning**: Operating System for Software 3.0

**Changelog v3.2.0** (Jan 30, 2026):
- **SDLC 6.1.0 Migration**: Framework upgraded from 5.1.3 → 6.0.5
- **Multi-Frontend Alignment**: Sprint 125-127 (26.5 SP in 1 day)
  - CLI (sdlcctl) parity: 39% → 71% (+32 points)
  - VS Code Extension parity: 67% → 89% (+22 points)
- **CLI Validation Testing Bug Fixes**:
  - Stage folder naming convention: `00-Project-Foundation` → `00-foundation`
  - P0 artifact paths updated for SDLC 6.1.0
  - Pre-commit hooks module created (`sdlcctl.hooks`)
  - Fix command now creates `99-Legacy` folders consistently
  - NLP parser test expectations aligned with actual implementation
  - See: [sdlcctl CHANGELOG v1.2.0](../../backend/sdlcctl/CHANGELOG.md)
- **Design Decision**: All CLI validation rules now enforce SDLC 6.1.0 lowercase naming

**Changelog v3.1.0** (Jan 19, 2026):
- **Sprint 78 Design Artifacts**: 4 new data models + 38 API endpoints documented
  - Sprint Analytics Foundation: RetroActionItem, SprintDependency models
  - Resource Optimization: ResourceAllocation, SprintTemplate models
  - Frontend Components: 4 React components (SprintDependencyGraph with D3.js, ResourceAllocationHeatmap, SprintTemplateSelector, SprintRetroComparison)
- **Personal Teams Design**: Comprehensive design document (1,247 lines)
  - Dual ownership model: User-owned + Organization-owned teams
  - Database schema: owner_id column + XOR constraint
  - API specification: organization_id optional, new response fields
  - Status: Awaiting CTO approval
- **ADR-025 Re-enforced**: Unified frontend architecture restored after 13 sprints drift
  - Governance incident documented: [GOVERNANCE-FAILURE-FRONTEND-DUPLICATION.md](../07-operate/03-Lessons-Learned/GOVERNANCE-FAILURE-FRONTEND-DUPLICATION.md)
  - Corrective actions: Mandatory ADR review in G-Sprint-Open, automated compliance checks
- **Architecture Stabilized**: Single Next.js frontend (port 8310), FastAPI backend (port 8300)

**Changelog v3.0.0** (Dec 23, 2025):
- **SOFTWARE 3.0 PIVOT**: Control Plane for AI Coders positioning
- **EP-06 Technical Specs**: Quality-Gates-Codegen-Specification.md (Sprint 48)
- **EP-06 Sprint 45-50**: IR Processor, Vietnamese Templates, Pilot, Productization
- **Sprint 43 OPA Integration**: Policy Guards Design complete
- **Sprint 44 Scanner Engine**: CrossReferenceValidator, SDLC Structure Scanner
- **14-Technical-Specs folder**: 15 specifications total
- Updated framework reference: SDLC 6.1.0 → SDLC 6.1.0

**Changelog v2.0.0** (Nov 29, 2025):
- Added AI Governance Layer (Section 11)
- Added Admin Panel Design (Sprint 37-40)

---

## Purpose

Stage 02 answers the fundamental question: **"HOW will we build this?"**

This stage transforms requirements (Stage 01 - WHAT) into technical architecture and design blueprints.

**Critical Success Factor**: We must design a system that is **scalable, secure, and maintainable** BEFORE writing production code.

---

## Folder Structure (SDLC 6.1.0 Compliant)

```
02-design/
├── README.md (this file)
├── 01-ADRs/ (Architecture Decision Records - Consolidated)
│   ├── ADR-001 to ADR-022 (22 ADRs total) ✅
│   └── All architecture decisions in one place
├── 02-System-Architecture/
│   ├── System-Architecture-Document.md ✅ (v3.0.0)
│   ├── Component-Architecture.md ✅
│   ├── Technical-Design-Document.md ✅
│   ├── Integration-Architecture.md ✅
│   ├── Event-Driven-Architecture.md ✅
│   └── C4-ARCHITECTURE-DIAGRAMS.md ✅
├── 03-Database-Design/
│   └── Database-Architecture.md ✅ (33 tables)
├── 04-API-Design/
│   ├── API-DEVELOPER-GUIDE.md ✅
│   ├── API-CHANGELOG.md ✅
│   ├── API-Frontend-Validation-Checklist.md ✅
│   ├── CURL-EXAMPLES.md ✅
│   ├── OPENAPI-ENHANCEMENT-SUMMARY.md ✅
│   └── TROUBLESHOOTING-GUIDE.md ✅
├── 05-Interface-Design/
│   └── Interface-Design-Document.md ✅
├── 06-Data-Architecture/
│   └── Data-Flow-Architecture.md ✅
├── 07-Security-Design/
│   ├── Security-Baseline.md (OWASP ASVS Level 2) ✅
│   └── SOC2-TYPE-I-CONTROLS-MATRIX.md ✅
├── 08-User-Experience/
│   ├── User-Onboarding-Flow-Architecture.md ✅
│   └── GitHub-Integration-Design-Clarification.md ✅
├── 09-UI-Design/
│   ├── FRONTEND-DESIGN-SPECIFICATION.md ✅
│   ├── AI-COUNCIL-CHAT-DESIGN.md ✅
│   ├── DESIGN-EVIDENCE-LOG.md ✅
│   └── Support-Page-Design.md ✅
├── 10-Admin-Panel-Design/
│   ├── ADMIN-PANEL-REQUIREMENTS.md ✅
│   ├── ADMIN-PANEL-API-DESIGN.md ✅
│   ├── ADMIN-PANEL-UI-SPECIFICATION.md ✅
│   └── ADMIN-PANEL-SECURITY-REVIEW.md ✅
├── 11-DevOps-Design/
│   ├── Infrastructure-Architecture.md ✅
│   ├── Network-Architecture.md ✅
│   ├── Monitoring-Observability-Architecture.md ✅
│   ├── Operability-Architecture.md ✅
│   └── Disaster-Recovery-Plan.md ✅
├── 12-Performance-Design/
│   ├── Performance-Budget.md ✅
│   └── Scalability-Architecture.md ✅
├── 13-Testing-Strategy/
│   └── Testing-Architecture.md ✅
├── 14-Technical-Specs/ ⭐ EXPANDED (15 specs)
│   ├── AI-Safety-Layer-v1.md ✅
│   ├── AI-Detection-Service-Interface.md ✅
│   ├── Analytics-Events-Taxonomy-v1.md ✅
│   ├── Design-Partner-Scorecard-v1.md ✅
│   ├── Workshop-Deck-AI-Safety-v1.md ✅
│   ├── Policy-Guards-Design.md ✅ (Sprint 43)
│   ├── Validation-Pipeline-Interface.md ✅
│   ├── Validator-Rules-Specification.md ✅
│   ├── Scanner-Architecture-Design.md ✅ (Sprint 44)
│   ├── Codegen-Service-Specification.md ✅ (EP-06)
│   ├── IR-Processor-Specification.md ✅ (Sprint 46)
│   ├── Vietnamese-Domain-Templates-Specification.md ✅ (Sprint 47)
│   ├── Quality-Gates-Codegen-Specification.md ✅ (Sprint 48) ⭐
│   ├── Pilot-Execution-Specification.md ✅ (Sprint 49)
│   └── Productization-Baseline-Specification.md ✅ (Sprint 50)
└── (Legacy content migrated to docs/10-archive/02-Legacy/ per RFC-001)
```

---

## Timeline (10 Days - Week 3-4)

| Days | Phase | Focus | Deliverables |
|------|-------|-------|--------------|
| 1-3 | **System Architecture** | High-level design | System Architecture, Component Diagram, Tech Stack |
| 4-5 | **Microservices Design** | Service boundaries | Microservices Architecture, API Contracts |
| 6-7 | **Security + Performance** | Non-functional design | Security Architecture, Performance Architecture |
| 8-9 | **Deployment + Monitoring** | Operations design | Deployment Architecture, Observability |
| 10 | **Gate G2 Prep** | Review + approval | Gate G2 documentation |

---

## Quality Gates

### Gate G2: Technical Feasibility ✅ PASSED

**Question**: "Have we designed a system that is technically feasible and scalable?"

**Criteria**:
- ✅ System architecture reviewed by CTO + Tech Lead (9.4/10)
- ✅ Technology stack justified (FastAPI, PostgreSQL, Redis, OPA, MinIO)
- ✅ Scalability validated (100 teams → 1,000 teams - modular monolith)
- ✅ Security validated (OWASP ASVS Level 2, 264/264 requirements)
- ✅ Performance validated (<100ms p95 API latency target)
- ✅ Deployment validated (Docker Compose dev, Kubernetes prod)

**Status**: ✅ PASSED - CTO 9.4/10, CPO 9.2/10

**Decision Date**: December 9, 2025 (Week 4)

**Approvers**:
- ✅ CTO (Chief Technology Officer) - APPROVED (9.4/10)
- ✅ Tech Lead - APPROVED
- ✅ Backend Lead - APPROVED
- ✅ CPO (Chief Product Officer) - APPROVED (9.2/10)
- ✅ Security Lead - APPROVED (OWASP ASVS L2 validated)

---

## Progress Tracker

### Latest Updates (Sprint 78 - Jan 2026)

**New Design Artifacts:**
- ✅ **Personal-Teams-Design.md** (1,247 lines) - Dual ownership model design
- ✅ **Sprint 78 Data Models**: 4 new tables (retro_action_items, sprint_dependencies, resource_allocations, sprint_templates)
- ✅ **Sprint 78 API Endpoints**: 38 new endpoints across 4 categories
- ✅ **Sprint 78 Frontend Components**: 4 React components (SprintDependencyGraph with D3.js, ResourceAllocationHeatmap, SprintTemplateSelector, SprintRetroComparison)
- ✅ **ADR-025 Re-enforced**: Unified frontend architecture + governance lessons documented

### 01-ADRs (100% complete - 25 ADRs)
- ✅ ADR-001 to ADR-028 (25 Architecture Decision Records)
- ✅ All decisions consolidated in single folder
- ✅ ADR-020: EP-04 SDLC Structure Enforcement
- ✅ ADR-021: EP-05 Enterprise SDLC Migration
- ✅ ADR-022: EP-06 Multi-Provider Codegen Architecture
- ✅ ADR-025: Frontend Platform Consolidation (Re-enforced Jan 2026)
- ✅ ADR-028: Teams Feature Architecture (Personal + Organization Teams)

### 02-System-Architecture (100% complete)
- ✅ System-Architecture-Document.md (v3.1.0 - 5-layer architecture with Sprint 78 extensions)
- ✅ Component-Architecture.md (bridge-first pattern)
- ✅ Technical-Design-Document.md (v2.0.0)
- ✅ Integration-Architecture.md
- ✅ Event-Driven-Architecture.md
- ✅ C4-ARCHITECTURE-DIAGRAMS.md

### 03-Database-Design (100% complete)
- ✅ Database-Architecture.md (32 tables: 28 core + 4 Sprint 78, 7-layer design including EP-06 Codegen Layer)

### 04-API-Design (100% complete)
- ✅ API-DEVELOPER-GUIDE.md (90+ endpoints: 52 core + 38 Sprint 78)
- ✅ API-CHANGELOG.md (Sprint 78 additions documented)
- ✅ API-Frontend-Validation-Checklist.md
- ✅ CURL-EXAMPLES.md
- ✅ OPENAPI-ENHANCEMENT-SUMMARY.md
- ✅ TROUBLESHOOTING-GUIDE.md

### 05-Interface-Design (100% complete)
- ✅ Interface-Design-Document.md

### 06-Data-Architecture (100% complete)
- ✅ Data-Flow-Architecture.md

### 07-Security-Design (100% complete)
- ✅ Security-Baseline.md (OWASP ASVS Level 2, 264/264)
- ✅ SOC2-TYPE-I-CONTROLS-MATRIX.md

### 08-User-Experience (100% complete)
- ✅ User-Onboarding-Flow-Architecture.md (<30 min TTFV)
- ✅ GitHub-Integration-Design-Clarification.md

### 09-UI-Design (100% complete)
- ✅ FRONTEND-DESIGN-SPECIFICATION.md
- ✅ AI-COUNCIL-CHAT-DESIGN.md
- ✅ DESIGN-EVIDENCE-LOG.md
- ✅ Support-Page-Design.md

### 10-Admin-Panel-Design (100% complete)
- ✅ ADMIN-PANEL-REQUIREMENTS.md (v2.0.0)
- ✅ ADMIN-PANEL-API-DESIGN.md (v2.0.0)
- ✅ ADMIN-PANEL-UI-SPECIFICATION.md (v1.0.0)
- ✅ ADMIN-PANEL-SECURITY-REVIEW.md (v1.0.0)

### 11-DevOps-Design (100% complete)
- ✅ Infrastructure-Architecture.md
- ✅ Network-Architecture.md
- ✅ Monitoring-Observability-Architecture.md
- ✅ Operability-Architecture.md
- ✅ Disaster-Recovery-Plan.md

### 12-Performance-Design (100% complete)
- ✅ Performance-Budget.md (<100ms p95 target)
- ✅ Scalability-Architecture.md

### 13-Testing-Strategy (100% complete)
- ✅ Testing-Architecture.md (95%+ coverage target)

### 14-Technical-Specs (100% complete) ⭐ EXPANDED
- ✅ AI-Safety-Layer-v1.md
- ✅ AI-Detection-Service-Interface.md
- ✅ Analytics-Events-Taxonomy-v1.md
- ✅ Design-Partner-Scorecard-v1.md
- ✅ Workshop-Deck-AI-Safety-v1.md
- ✅ Policy-Guards-Design.md (Sprint 43 - OPA Integration)
- ✅ Validation-Pipeline-Interface.md
- ✅ Validator-Rules-Specification.md
- ✅ Scanner-Architecture-Design.md (Sprint 44 - CrossReferenceValidator)
- ✅ Codegen-Service-Specification.md (EP-06 Codegen)
- ✅ IR-Processor-Specification.md (Sprint 46)
- ✅ Vietnamese-Domain-Templates-Specification.md (Sprint 47)
- ✅ **Quality-Gates-Codegen-Specification.md** (Sprint 48) ⭐ NEW
- ✅ Pilot-Execution-Specification.md (Sprint 49)
- ✅ Productization-Baseline-Specification.md (Sprint 50)

**Overall Progress**: ✅ 100% (75+ documents complete)

---

## Exit Criteria (Must Complete Before Stage 03)

- [x] G2: Technical Feasibility validated ✅ PASSED (CTO 9.4/10)
- [x] All 24 architecture documents completed ✅
- [x] CTO + Tech Lead + Backend Lead approval (3 required) ✅
- [x] Technology stack finalized (FastAPI, PostgreSQL, Redis, OPA, MinIO) ✅
- [x] Security design approved (OWASP ASVS Level 2) ✅
- [x] Scalability validated (modular monolith → microservices path) ✅

**Stage 02 Status**: ✅ COMPLETED - Ready for Stage 04 (BUILD)

---

## Architecture Principles (HOW We Design)

### Principle 1: **Bridge-First Architecture**

**Problem**: We're a governance layer, NOT a replacement for GitHub/Jira/Linear.

**Solution**:
- **Read & Display**: GitHub Issues, Projects, Pull Requests (read-only)
- **Enforce & Validate**: Quality gates, policy checks, evidence requirements
- **Audit & Report**: Evidence vault, compliance dashboards, gate status

**Architecture**:
```
┌─────────────────────────────────────────────────────────┐
│ SDLC Orchestrator (Proprietary - Apache-2.0)           │
│ - Gate Engine, Evidence Vault, Policy Packs            │
└─────────────────┬───────────────────────────────────────┘
                  │ (Bridge Layer - Read/Sync)
                  ↓
┌─────────────────────────────────────────────────────────┐
│ Existing Tools (Customer Infrastructure)               │
│ - GitHub (Issues, Projects, PRs)                       │
│ - CI/CD (GitHub Actions, Argo, Tekton)                │
│ - Monitoring (Grafana, Prometheus)                     │
└─────────────────────────────────────────────────────────┘
```

### Principle 2: **4-Layer Architecture**

**Layer 1: User-Facing** (Proprietary - Apache-2.0)
- React Dashboard
- VS Code Extension
- CLI (`sdlcctl`)

**Layer 2: Business Logic** (Proprietary - Apache-2.0)
- Gate Engine (Policy-as-Code)
- Evidence Vault API
- AI Context Engine (WHY/WHAT/HOW)

**Layer 3: Integration** (Thin Wrapper - Apache-2.0)
- `opa_service.py` → OPA (Apache-2.0)
- `minio_service.py` → MinIO (AGPL, network-only)
- `grafana_service.py` → Grafana (AGPL, iframe-only)

**Layer 4: Infrastructure** (OSS - AGPL/Apache-2.0)
- OPA (policy engine)
- MinIO (evidence storage)
- Grafana (dashboards)
- PostgreSQL (database)
- Redis (cache)

### Principle 3: **Policy-as-Code (OPA)**

**Why OPA?**
- Industry standard (CNCF graduated project)
- Declarative policy language (Rego)
- High performance (compiled policies)
- Extensible (custom functions)

**Example Policy** (`gate-g1-policy.rego`):
```rego
package gates.g1

default allow = false

# Gate G1: Legal + Market Validation
allow {
    input.gate_id == "G1"
    legal_approved
    market_validated
}

legal_approved {
    input.evidence["legal-review-report.md"].status == "approved"
    input.evidence["agpl-containment-strategy.md"].status == "approved"
}

market_validated {
    input.evidence["competitive-landscape.md"].status == "complete"
    input.evidence["market-sizing.md"].status == "complete"
}
```

### Principle 4: **Evidence-First (Vault)**

**Problem**: Most tools track tasks, NOT evidence (test results, coverage, security scans).

**Solution**: Evidence Vault (S3-compatible storage + metadata database)

**Architecture**:
```
Evidence Vault = MinIO (S3 storage) + PostgreSQL (metadata)

Evidence Types:
- Test Results: Allure reports, JUnit XML
- Coverage: Coverage.py, Istanbul
- Security: SAST (Semgrep), DAST (OWASP ZAP)
- Compliance: SOC 2 audit reports, GDPR DPIAs
- Documentation: ADRs, RFCs, Runbooks

Metadata:
- SHA256 hash (integrity)
- Timestamp (audit trail)
- Owner (accountability)
- Gate linkage (traceability)
```

### Principle 5: **AI-Augmented (WHY/WHAT/HOW)**

**Stage-Specific AI Context**:
- **Stage 00 (WHY)**: Empathy maps, problem statements, HMW questions
- **Stage 01 (WHAT)**: User stories, acceptance criteria, API specs
- **Stage 02 (HOW)**: Architecture diagrams, tech stack, security design
- **Stage 04 (BUILD)**: Code generation, code review, refactoring
- **Stage 05 (TEST)**: Test case generation, test data, edge cases
- **Stage 06 (DEPLOY)**: Deployment scripts, rollback procedures, runbooks
- **Stage 07 (OPERATE)**: Incident response, RCA, postmortems

**Example AI Prompt** (Stage 02):
```
You are a Senior Architect designing SDLC Orchestrator (Stage 02 - HOW).

Context:
- Stage 00 (WHY): Problem validated (60-70% feature waste)
- Stage 01 (WHAT): 15 docs, 30,000 lines (requirements, API specs, legal)
- Target: 100 teams (MVP), 1,000 teams (Year 3)
- Tech stack: Python (FastAPI), React, PostgreSQL, Redis, OPA, MinIO

Task: Design the Gate Engine microservice.
- Input: Policy pack (YAML), evidence metadata (JSON), gate ID
- Output: PASS/FAIL decision, missing evidence list, recommendation
- Constraints: <100ms latency (p95), 1,000 req/min throughput

Generate:
1. Component diagram (Gate Engine internals)
2. API contract (OpenAPI spec)
3. Database schema (policy_packs, gate_evaluations tables)
4. Deployment architecture (Docker Compose, Kubernetes)
```

---

## Technology Stack (Finalized in Stage 01)

### Backend
- **Language**: Python 3.11+
- **Framework**: FastAPI (async, high performance)
- **Database**: PostgreSQL 15.5 (ACID, JSONB support)
- **Cache**: Redis 7.2 (session storage, token blacklist)
- **Policy Engine**: OPA 0.58.0 (Apache-2.0)
- **Object Storage**: MinIO (AGPL, S3-compatible)

### Frontend
- **Language**: TypeScript 5.0+
- **Framework**: React 18 (hooks, suspense)
- **State**: Zustand (lightweight, no Redux complexity)
- **UI Library**: shadcn/ui (Tailwind + Radix)
- **API Client**: React Query (caching, optimistic updates)

### DevOps
- **Containerization**: Docker + Docker Compose
- **Orchestration**: Kubernetes (production)
- **CI/CD**: GitHub Actions
- **IaC**: Terraform (AWS/GCP)
- **Monitoring**: Grafana + Prometheus + OnCall

### AI/ML
- **Providers**: Claude (Anthropic), GPT-4o (OpenAI), Gemini (Google)
- **Framework**: LangChain (agent orchestration)
- **Embeddings**: OpenAI Ada-002 (semantic search)
- **Vector DB**: PostgreSQL + pgvector (no separate DB)

---

## Design Decisions (ADRs - Architecture Decision Records)

### ADR-001: FastAPI vs Django vs Flask
**Decision**: FastAPI
**Rationale**:
- Async support (10x throughput vs Django)
- Auto-generated OpenAPI docs (API-first)
- Pydantic validation (type safety)
- Modern Python (3.11+ features)

**Trade-offs**:
- ❌ Smaller ecosystem vs Django
- ✅ Better performance (50ms vs 200ms p95 latency)

### ADR-002: PostgreSQL vs MongoDB
**Decision**: PostgreSQL
**Rationale**:
- ACID compliance (critical for gate approvals)
- JSONB support (flexible schema where needed)
- Full-text search (pgvector for embeddings)
- 20+ years of production battle-testing

**Trade-offs**:
- ❌ Less flexible schema vs MongoDB
- ✅ Better data integrity (no orphaned records)

### ADR-003: Microservices vs Monolith
**Decision**: Modular Monolith → Microservices (future)
**Rationale**:
- MVP: Modular monolith (faster development, simpler ops)
- Year 2: Extract microservices (Gate Engine, Evidence Vault)
- Year 3: Full microservices (if scaling >1,000 teams)

**Trade-offs**:
- ❌ Initial latency (in-process calls faster than network)
- ✅ Simpler debugging (single process, single log stream)

### ADR-004: REST vs GraphQL vs Both
**Decision**: Both (Hybrid)
**Rationale**:
- REST: Simple CRUD (gates, evidence, projects)
- GraphQL: Complex queries (dashboards, reports)
- Clients choose based on use case

**Trade-offs**:
- ❌ Maintain 2 APIs (double documentation)
- ✅ Better DX (developers use what fits their need)

### ADR-005: OAuth 2.0 vs SAML vs Both
**Decision**: OAuth 2.0 (MVP), SAML (Enterprise add-on)
**Rationale**:
- OAuth 2.0: 90%+ startups (GitHub, Google, Microsoft)
- SAML: 100% enterprises (Okta, Azure AD)
- MVP: OAuth only (faster)
- Enterprise: Add SAML (when needed)

**Trade-offs**:
- ❌ No SAML in MVP (blocks some enterprise deals)
- ✅ Faster MVP (OAuth simpler to implement)

---

## Risks & Mitigations (HOW We De-Risk)

### Risk 1: Over-Engineering (Gold-Plating)
**Impact**: High - waste 4-6 weeks on features nobody needs
**Probability**: Medium

**Mitigation**:
- Follow YAGNI (You Ain't Gonna Need It)
- Design for 100 teams (MVP), NOT 1M teams
- Defer optimization until measurements prove need

### Risk 2: Under-Engineering (Technical Debt)
**Impact**: High - 6-12 months rewrite in Year 2
**Probability**: Medium

**Mitigation**:
- Design for 10x scale (100 → 1,000 teams)
- Use industry-standard patterns (no custom protocols)
- Document trade-offs (ADRs) for future context

### Risk 3: Vendor Lock-In (AWS/GCP)
**Impact**: Medium - hard to migrate if pricing changes
**Probability**: Low

**Mitigation**:
- Use open standards (S3 API, Postgres protocol)
- MinIO = self-hosted S3 (portable)
- Kubernetes = cloud-agnostic orchestration

### Risk 4: AGPL Contamination
**Impact**: Critical - forced to open-source proprietary code
**Probability**: Low (if containment strategy followed)

**Mitigation**:
- Network-only access (MinIO, Grafana)
- Pre-commit hooks (block AGPL imports)
- Quarterly audits (CTO sign-off)

---

## Success Metrics (HOW We Measure Design Quality)

### Metric 1: Architecture Review Score
**Target**: 8.5/10+ (CTO approval)
**Measurement**: CTO rates each design document (1-10 scale)

### Metric 2: Security Coverage
**Target**: 100% OWASP Top 10 mitigated
**Measurement**: Threat model maps each OWASP risk → mitigation

### Metric 3: Scalability Validation
**Target**: 1,000 teams supported (10x MVP scale)
**Measurement**: Load testing scenarios documented

### Metric 4: Technology Debt Ratio
**Target**: <10% "known shortcuts" vs total architecture
**Measurement**: ADRs track deferred work (pay down in Stage 07)

---

## Next Stage

Once Stage 02 is complete → **[Stage 04 (BUILD)](../03-Development-Implementation/README.md)**

---

## References

- [Stage 01: Planning & Analysis (WHAT)](../01-Planning-Analysis/README.md) - Requirements foundation
- [SDLC 6.1.0 Core Methodology](../../SDLC-Enterprise-Framework/README.md) - 10-Stage lifecycle
- [API Specification v1.0](../01-Planning-Analysis/04-API-Design/API-Specification.md) - REST + GraphQL
- [Data Model ERD v1.0](../01-Planning-Analysis/03-Data-Model/Data-Model-ERD.md) - Database schema
- [Security Architecture Best Practices](https://owasp.org/www-project-secure-coding-practices/) - OWASP guide

---

**Last Updated**: December 23, 2025
**Owner**: CTO + Tech Lead + Backend Lead
**Status**: ✅ COMPLETED - Gate G2 PASSED
**Positioning**: Operating System for Software 3.0

---

## Document Summary

**Total Documents**: 75+ (across 14 folders)
**Total Lines**: 100,000+ lines of architecture documentation
**Quality Gates**: G2 (Technical Feasibility) ✅ PASSED (Dec 9, 2025)
**Next Stage**: Stage 04 (BUILD) - Sprint 44-50 IN PROGRESS
**Current Stage**: ✅ Stage 02 COMPLETED
**Framework**: SDLC 6.1.0

---

## Strategic Design Updates (Dec 23, 2025)

### Software 3.0 Positioning

> **"Operating System for Software 3.0 - Where AI coders are governed, not feared."**

**5-Layer Architecture** (updated from 4-layer):
```
Layer 5: AI Coders (Claude/Cursor/Copilot/OSS) ← We orchestrate
Layer 4: EP-06 Codegen (IR Processor + Quality Gates) ← NEW ⭐
Layer 3: Business Logic (Gate Engine + Evidence Vault) ← Core
Layer 2: Integration Layer (OPA, MinIO, GitHub Bridge)
Layer 1: Infrastructure (PostgreSQL, Redis, MinIO, Grafana)
```

### EP-06 Technical Specs (Sprint 45-50)

| Sprint | Focus | Spec Document | Status |
|--------|-------|---------------|--------|
| 45 | Multi-Provider Architecture | ADR-022, Tech Spec | ✅ |
| 46 | IR Processor Backend | IR-Processor-Specification.md | ✅ |
| 47 | Vietnamese Domain Templates | Vietnamese-Domain-Templates-Specification.md | ✅ |
| 48 | Quality Gates for Codegen | Quality-Gates-Codegen-Specification.md | ✅ ⭐ |
| 49 | Vietnam SME Pilot | Pilot-Execution-Specification.md | ✅ |
| 50 | Productization + GA | Productization-Baseline-Specification.md | ✅ |

### Sprint 43-44 Implementations

| Sprint | Feature | Key Design |
|--------|---------|------------|
| 43 | OPA Integration + Policy Guards | Policy-Guards-Design.md |
| 43 | SAST Validator (Semgrep) | Validation-Pipeline-Interface.md |
| 43 | Evidence Timeline UI | Component-Architecture.md |
| 43 | Override Queue Management | Data-Flow-Architecture.md |
| 44 | SDLC Structure Scanner | Scanner-Architecture-Design.md |
| 44 | CrossReferenceValidator | Validator-Rules-Specification.md |

---

## Implementation Highlights

### Architecture Delivered:

| Component | Status | Key Deliverable |
|-----------|--------|-----------------|
| **System Architecture** | ✅ | 5-layer architecture (EP-06 Codegen Layer added) |
| **Database Design** | ✅ | 33 tables, 7-layer schema, Alembic migrations |
| **API Design** | ✅ | openapi.yml (139KB, 91+ endpoints) |
| **Security** | ✅ | OWASP ASVS Level 2, SOC 2 Type I matrix |
| **Performance** | ✅ | <100ms p95 target, Redis caching strategy |
| **DevOps** | ✅ | CI/CD pipeline, Docker/Kubernetes ready |
| **Testing** | ✅ | 95%+ coverage target, E2E with Playwright |
| **Admin Panel** | ✅ | Sprint 37-40, Full CRUD, 121 E2E tests |
| **EP-06 Codegen** | ✅ | 4-Gate Quality Pipeline, Validation Loop, Evidence State Machine |

### ADRs (Architecture Decision Records):

**Original ADRs (ADR-001 to ADR-019)**:
1. **ADR-001**: FastAPI over Django (10x throughput, async-first)
2. **ADR-002**: PostgreSQL over MongoDB (ACID, JSONB flexibility)
3. **ADR-003**: Modular Monolith → Microservices path
4. **ADR-004**: REST + GraphQL hybrid API
5. **ADR-005**: OAuth 2.0 (MVP) + SAML (Enterprise)
6. **ADR-006**: OPA Policy-as-Code (CNCF graduated)
7. **ADR-007**: Ollama AI Integration (95% cost savings)
8. **ADR-017**: Admin Panel Architecture (Sprint 37-40)

**New ADRs (ADR-020 to ADR-022)** *(Dec 2025)*:
9. **ADR-020**: EP-04 SDLC Structure Enforcement (Universal AI Codex Validation)
10. **ADR-021**: EP-05 Enterprise SDLC Migration (.sdlc-config.json 700x smaller)
11. **ADR-022**: EP-06 Multi-Provider Codegen Architecture (Ollama → Claude → DeepCode)

---

## Admin Panel Design (Sprint 37-40)

### Overview

The Admin Panel provides platform-level user management for superusers:

| Feature | Folder | Status |
|---------|--------|--------|
| Requirements | 10-Admin-Panel-Design/ADMIN-PANEL-REQUIREMENTS.md | ✅ v2.0.0 |
| API Design | 10-Admin-Panel-Design/ADMIN-PANEL-API-DESIGN.md | ✅ v2.0.0 |
| UI Specification | 10-Admin-Panel-Design/ADMIN-PANEL-UI-SPECIFICATION.md | ✅ v1.0.0 |
| Security Review | 10-Admin-Panel-Design/ADMIN-PANEL-SECURITY-REVIEW.md | ✅ v1.0.0 |

### Implementation Summary

| Sprint | Deliverable | Lines |
|--------|-------------|-------|
| 37 | Backend (11 endpoints) + Frontend (5 pages) | ~2,500 |
| 38 | E2E Tests (109 tests) | ~1,300 |
| 39 | Toast Notifications | ~600 |
| 40 | Full CRUD (Create, Soft Delete) | ~550 |

### User Model Extensions (Sprint 40)

```sql
-- Soft delete support for audit trail
ALTER TABLE users ADD COLUMN deleted_at TIMESTAMP NULL;
ALTER TABLE users ADD COLUMN deleted_by UUID REFERENCES users(id) ON DELETE SET NULL;
CREATE INDEX ix_users_deleted_at ON users(deleted_at);
CREATE INDEX ix_users_active_not_deleted ON users(is_active, deleted_at);
```

### Security Enforcements

- All admin endpoints require `is_superuser=true`
- Cannot delete/deactivate self
- Cannot delete last superuser
- Password minimum 12 characters
- All actions audit logged (SOC 2 compliant)
