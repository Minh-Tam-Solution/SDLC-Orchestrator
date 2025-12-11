# Stage 02: Design & Architecture (HOW?)
## System Architecture + Technical Design

**Version**: 2.0.0
**Date**: November 29, 2025
**Status**: ✅ COMPLETED - Gate G2 PASSED (CTO 9.4/10, CPO 9.2/10)
**Authority**: CTO + Tech Lead + Backend Lead Approved
**Foundation**: SDLC 4.9.1 Complete Lifecycle (10 Stages)
**Previous Stage**: Stage 01 (Planning & Analysis - WHAT) ✅ COMPLETE
**Next Stage**: Stage 04 (BUILD) - IN PROGRESS

---

## Purpose

Stage 02 answers the fundamental question: **"HOW will we build this?"**

This stage transforms requirements (Stage 01 - WHAT) into technical architecture and design blueprints.

**Critical Success Factor**: We must design a system that is **scalable, secure, and maintainable** BEFORE writing production code.

---

## Folder Structure (SDLC 4.9.1 Compliant)

```
02-Design-Architecture/
├── README.md (this file)
├── 01-System-Architecture/
│   ├── System-Architecture-Document.md ✅
│   ├── Component-Diagram.md ✅
│   └── ADRs/ (Architecture Decision Records) ✅
├── 02-Database-Design/
│   ├── Database-Architecture.md ✅
│   └── Alembic-Migration-Strategy.md ✅
├── 03-API-Design/
│   ├── openapi.yml (139KB, 30+ endpoints) ✅
│   ├── API-DEVELOPER-GUIDE.md ✅
│   ├── CURL-EXAMPLES.md ✅
│   └── TROUBLESHOOTING-GUIDE.md ✅
├── 04-Interface-Design/
│   └── Interface-Design-Document.md ✅
├── 05-Data-Architecture/
│   └── Data-Flow-Architecture.md ✅
├── 06-Security-RBAC/
│   ├── Security-Baseline.md (OWASP ASVS Level 2) ✅
│   └── SOC2-TYPE-I-CONTROLS-MATRIX.md ✅
├── 07-User-Experience/
│   ├── User-Onboarding-Flow-Architecture.md ✅
│   └── GitHub-Integration-Design-Clarification.md ✅
├── 08-DevOps-Architecture/
│   ├── CI-CD-Pipeline.md ✅
│   └── Infrastructure-as-Code.md ✅
├── 09-Performance-Architecture/
│   ├── Performance-Baseline.md ✅
│   └── Caching-Strategy.md ✅
├── 10-Testing-Strategy/
│   └── Testing-Architecture.md ✅
├── 11-UI-UX-Design/
│   └── Wireframes.md ✅
└── 99-Legacy/
    └── (archived planning docs)
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

### 01-System-Architecture (100% complete)
- ✅ System-Architecture-Document.md (568 lines, 4-layer architecture)
- ✅ Component-Diagram.md (bridge-first pattern)
- ✅ ADRs/ (7 Architecture Decision Records)

### 02-Database-Design (100% complete)
- ✅ Database-Architecture.md (24 tables, 6-layer design)
- ✅ Alembic-Migration-Strategy.md

### 03-API-Design (100% complete)
- ✅ openapi.yml (139KB, 30+ endpoints)
- ✅ API-DEVELOPER-GUIDE.md
- ✅ CURL-EXAMPLES.md
- ✅ TROUBLESHOOTING-GUIDE.md

### 04-Interface-Design (100% complete)
- ✅ Interface-Design-Document.md

### 05-Data-Architecture (100% complete)
- ✅ Data-Flow-Architecture.md

### 06-Security-RBAC (100% complete)
- ✅ Security-Baseline.md (OWASP ASVS Level 2, 264/264)
- ✅ SOC2-TYPE-I-CONTROLS-MATRIX.md

### 07-User-Experience (100% complete)
- ✅ User-Onboarding-Flow-Architecture.md (<30 min TTFV)
- ✅ GitHub-Integration-Design-Clarification.md

### 08-DevOps-Architecture (100% complete)
- ✅ CI-CD-Pipeline.md (GitHub Actions)
- ✅ Infrastructure-as-Code.md (Terraform + Kubernetes)

### 09-Performance-Architecture (100% complete)
- ✅ Performance-Baseline.md (<100ms p95 target)
- ✅ Caching-Strategy.md (Redis layer)

### 10-Testing-Strategy (100% complete)
- ✅ Testing-Architecture.md (95%+ coverage target)

### 11-UI-UX-Design (100% complete)
- ✅ Wireframes.md (Dashboard, Gates, Evidence)

**Overall Progress**: ✅ 100% (24 documents complete)

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
- [SDLC 4.9 Core Methodology](../../SDLC-Enterprise-Framework/README.md) - 10-Stage lifecycle
- [API Specification v1.0](../01-Planning-Analysis/04-API-Design/API-Specification.md) - REST + GraphQL
- [Data Model ERD v1.0](../01-Planning-Analysis/03-Data-Model/Data-Model-ERD.md) - Database schema
- [Security Architecture Best Practices](https://owasp.org/www-project-secure-coding-practices/) - OWASP guide

---

**Last Updated**: November 29, 2025
**Owner**: CTO + Tech Lead + Backend Lead
**Status**: ✅ COMPLETED - Gate G2 PASSED

---

## Document Summary

**Total Documents**: 24 (across 11 folders)
**Total Lines**: 50,000+ lines of architecture documentation
**Quality Gates**: G2 (Technical Feasibility) ✅ PASSED (Dec 9, 2025)
**Next Stage**: Stage 04 (BUILD) - IN PROGRESS
**Current Stage**: ✅ Stage 02 COMPLETED

---

## Implementation Highlights (Week 10 of 13)

### Architecture Delivered:

| Component | Status | Key Deliverable |
|-----------|--------|-----------------|
| **System Architecture** | ✅ | 4-layer architecture, bridge-first pattern |
| **Database Design** | ✅ | 24 tables, 6-layer schema, Alembic migrations |
| **API Design** | ✅ | openapi.yml (139KB, 30+ endpoints) |
| **Security** | ✅ | OWASP ASVS Level 2, SOC 2 Type I matrix |
| **Performance** | ✅ | <100ms p95 target, Redis caching strategy |
| **DevOps** | ✅ | CI/CD pipeline, Docker/Kubernetes ready |
| **Testing** | ✅ | 95%+ coverage target, E2E with Playwright |

### ADRs (Architecture Decision Records):

1. **ADR-001**: FastAPI over Django (10x throughput, async-first)
2. **ADR-002**: PostgreSQL over MongoDB (ACID, JSONB flexibility)
3. **ADR-003**: Modular Monolith → Microservices path
4. **ADR-004**: REST + GraphQL hybrid API
5. **ADR-005**: OAuth 2.0 (MVP) + SAML (Enterprise)
6. **ADR-006**: OPA Policy-as-Code (CNCF graduated)
7. **ADR-007**: Ollama AI Integration (95% cost savings)
