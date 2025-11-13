# Stage 02: Design & Architecture (HOW?)
## System Architecture + Technical Design

**Version**: 1.0.0
**Date**: November 13, 2025
**Status**: ACTIVE - IN PROGRESS (0% complete)
**Authority**: CTO + Tech Lead + Backend Lead
**Foundation**: SDLC 4.9 Complete Lifecycle (10 Stages)
**Previous Stage**: Stage 01 (Planning & Analysis - WHAT) ✅ COMPLETE

---

## Purpose

Stage 02 answers the fundamental question: **"HOW will we build this?"**

This stage transforms requirements (Stage 01 - WHAT) into technical architecture and design blueprints.

**Critical Success Factor**: We must design a system that is **scalable, secure, and maintainable** BEFORE writing production code.

---

## Folder Structure

```
02-Design-Architecture/
├── README.md (this file)
├── 01-System-Architecture/
│   ├── System-Architecture-Document.md
│   ├── Component-Diagram.md
│   └── Technology-Stack-Justification.md
├── 02-Microservices-Design/
│   ├── Microservices-Architecture.md
│   ├── Service-Boundaries.md
│   └── API-Contracts.md
├── 03-Database-Design/
│   ├── Database-Architecture.md
│   ├── Schema-Optimization.md
│   └── Migration-Strategy.md
├── 04-Security-Design/
│   ├── Security-Architecture.md
│   ├── Threat-Model.md
│   └── OWASP-Compliance.md
├── 05-Performance-Design/
│   ├── Performance-Architecture.md
│   ├── Caching-Strategy.md
│   └── Scalability-Plan.md
├── 06-Deployment-Design/
│   ├── Deployment-Architecture.md
│   ├── CI-CD-Pipeline.md
│   └── Infrastructure-as-Code.md
└── 07-Monitoring-Design/
    ├── Observability-Architecture.md
    ├── Metrics-Design.md
    └── Alerting-Strategy.md
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

### Gate G2: Technical Feasibility ⏳

**Question**: "Have we designed a system that is technically feasible and scalable?"

**Criteria**:
- ⏳ System architecture reviewed by CTO + Tech Lead
- ⏳ Technology stack justified (no silver bullets, proven technologies)
- ⏳ Scalability validated (100 teams → 1,000 teams)
- ⏳ Security validated (OWASP Top 10 mitigated)
- ⏳ Performance validated (DORA metrics achievable)
- ⏳ Deployment validated (Docker → Kubernetes)

**Status**: ⏳ PENDING - Stage 02 just started

**Decision Date**: Week 4 end (December 11, 2025)

**Approvers Required**:
- ✅ CTO (Chief Technology Officer) - REQUIRED
- ✅ Tech Lead - REQUIRED
- ✅ Backend Lead - REQUIRED
- ⚠️ CPO (Chief Product Officer) - RECOMMENDED
- ⚠️ Security Lead - RECOMMENDED

---

## Progress Tracker

### 01-System-Architecture (0% complete)
- ⏳ System-Architecture-Document.md
- ⏳ Component-Diagram.md
- ⏳ Technology-Stack-Justification.md

### 02-Microservices-Design (0% complete)
- ⏳ Microservices-Architecture.md
- ⏳ Service-Boundaries.md
- ⏳ API-Contracts.md

### 03-Database-Design (0% complete)
- ⏳ Database-Architecture.md
- ⏳ Schema-Optimization.md
- ⏳ Migration-Strategy.md

### 04-Security-Design (0% complete)
- ⏳ Security-Architecture.md
- ⏳ Threat-Model.md
- ⏳ OWASP-Compliance.md

### 05-Performance-Design (0% complete)
- ⏳ Performance-Architecture.md
- ⏳ Caching-Strategy.md
- ⏳ Scalability-Plan.md

### 06-Deployment-Design (0% complete)
- ⏳ Deployment-Architecture.md
- ⏳ CI-CD-Pipeline.md
- ⏳ Infrastructure-as-Code.md

### 07-Monitoring-Design (0% complete)
- ⏳ Observability-Architecture.md
- ⏳ Metrics-Design.md
- ⏳ Alerting-Strategy.md

**Overall Progress**: ⏳ 0% (0 of 21 documents complete)

---

## Exit Criteria (Must Complete Before Stage 03)

- [ ] G2: Technical Feasibility validated ⏳ PENDING
- [ ] All 21 architecture documents completed
- [ ] CTO + Tech Lead + Backend Lead approval (3 required)
- [ ] Technology stack finalized (no changes during Stage 03)
- [ ] Security design approved (OWASP Top 10 coverage)
- [ ] Scalability validated (load testing plan documented)

**Stage 02 Status**: ⏳ IN PROGRESS - Just started

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
- **Stage 03 (BUILD)**: Code generation, code review, refactoring
- **Stage 04 (TEST)**: Test case generation, test data, edge cases
- **Stage 05 (DEPLOY)**: Deployment scripts, rollback procedures, runbooks
- **Stage 06 (OPERATE)**: Incident response, RCA, postmortems

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

Once Stage 02 is complete → **[Stage 03: Development & Implementation (BUILD)](../03-Development-Implementation/README.md)**

---

## References

- [Stage 01: Planning & Analysis (WHAT)](../01-Planning-Analysis/README.md) - Requirements foundation
- [SDLC 4.9 Core Methodology](../../SDLC-Enterprise-Framework/README.md) - 10-Stage lifecycle
- [API Specification v1.0](../01-Planning-Analysis/04-API-Design/API-Specification.md) - REST + GraphQL
- [Data Model ERD v1.0](../01-Planning-Analysis/03-Data-Model/Data-Model-ERD.md) - Database schema
- [Security Architecture Best Practices](https://owasp.org/www-project-secure-coding-practices/) - OWASP guide

---

**Last Updated**: November 13, 2025
**Owner**: CTO + Tech Lead
**Status**: ⏳ IN PROGRESS (0% complete)

---

## Document Summary

**Total Documents**: 21 planned
**Total Lines**: 20,000+ target
**Quality Gates**: G2 (Technical Feasibility) - Week 4 end
**Next Gate**: G2 (December 11, 2025)
