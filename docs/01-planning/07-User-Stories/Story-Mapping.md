# Story Mapping
## User Journey Visualization (Stage 00-09)

**Version**: 2.1.0
**Date**: February 20, 2026
**Status**: ACTIVE - Enterprise-First Alignment
**Authority**: PM + UX Lead Review (✅ APPROVED)
**Foundation**: User Stories v2.1.0, Acceptance Criteria v2.1.0, Roadmap v5.0.0
**Stage**: Stage 01 (WHAT - Planning & Analysis)
**Framework**: SDLC 6.1.0 (7-Pillar + Section 7 Quality Assurance + Section 8 Specification Standard)

**Changelog**:
- v2.1.0 (Feb 20, 2026): Enterprise-First alignment — SDLC 5.1.3→6.1.0, SDLC 4.8→6.1.0
- v2.0.0 (Dec 21, 2025): SDLC 5.1.3 update, EP-04/05/06 user journeys added
- v1.0.0 (Jan 13, 2025): Initial story mapping (7 journeys, 50+ stories)

---

## Document Purpose

This document visualizes **user journeys across SDLC 6.1.0 stages (Stage 00-09)** using story mapping.

**Key Sections**:
- Journey 1: EM Validates Feature Idea (Stage 00)
- Journey 2: EM Defines Requirements (Stage 01)
- Journey 3: CTO Reviews Architecture (Stage 02)
- Journey 4: Dev Lead Implements Feature (Stage 03)
- Journey 5: QA Lead Tests Feature (Stage 04)
- Journey 6: DevOps Lead Deploys Feature (Stage 05)
- Journey 7: CIO Monitors Production (Stage 06)

---

## Story Mapping Framework

**Format**: Horizontal flow (left-to-right, time-based)

```
┌─────────────────────────────────────────────────────────────────┐
│ USER JOURNEY: EM Validates Feature Idea (Stage 00 - WHY)       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  BACKBONE (Epic-Level Activities):                             │
│  ┌────────┐   ┌────────┐   ┌────────┐   ┌────────┐          │
│  │ Upload │ → │ AI Gen │ → │ Eval   │ → │ View   │          │
│  │Evidence│   │  PRD   │   │ Gates  │   │ Status │          │
│  └────────┘   └────────┘   └────────┘   └────────┘          │
│      │            │            │            │                  │
│      ▼            ▼            ▼            ▼                  │
│  ┌────────┐   ┌────────┐   ┌────────┐   ┌────────┐          │
│  │ US2.1  │   │ US4.1  │   │ US1.2  │   │ US1.1  │          │
│  │ Upload │   │ AI PRD │   │ Eval   │   │ View   │          │
│  │ 5 PDFs │   │ 14h→20m│   │ G0.1   │   │ Gate   │          │
│  └────────┘   └────────┘   └────────┘   └────────┘          │
│      │            │            │            │                  │
│      ▼            ▼            ▼            ▼                  │
│  ┌────────┐   ┌────────┐   ┌────────┐   ┌────────┐          │
│  │ US2.2  │   │ US4.2  │   │ US1.3  │   │ US1.4  │          │
│  │ Auto   │   │ AI Rev │   │Request │   │ Depend │          │
│  │ Slack  │   │ Design │   │Override│   │ Chain  │          │
│  └────────┘   └────────┘   └────────┘   └────────┘          │
│                                                                 │
│  TIME SAVINGS: 43 hours → 16 hours (37% reduction)            │
└─────────────────────────────────────────────────────────────────┘
```

---

## Journey 1: EM Validates Feature Idea (Stage 00 - WHY)

### Backbone (Epic-Level Activities)

1. **Conduct User Research** (Epic 2: Evidence Vault)
2. **Generate PRD** (Epic 4: AI Context Engine)
3. **Evaluate Gates G0.1, G0.2** (Epic 1: Gate Management)
4. **View Progress** (Epic 5: Dashboard)

### Detailed User Stories (Walking Skeleton - MVP)

**Step 1: Upload User Interview Transcripts**
- **US2.1**: Upload 5 PDF transcripts (2MB each)
- **Time**: 10 minutes (baseline: 30 minutes manual export from Zoom)
- **Success**: 5 evidence records created in Evidence Vault

**Step 2: AI Generates PRD from Interviews**
- **US4.1**: AI analyzes transcripts, extracts pain points, generates PRD (3,000 words)
- **Time**: 20 minutes (baseline: 14 hours manual PRD writing)
- **Success**: PRD ready for review

**Step 3: Evaluate Gate G0.1 (Problem Definition)**
- **US1.2**: EM clicks "Evaluate G0.1"
- **Policies Checked**:
  - `policy-user-interviews`: Requires 3+ interviews (✅ 5 interviews)
  - `policy-problem-statement`: Validated problem statement (✅ AI-generated PRD)
  - `policy-pain-level`: Pain level ≥7/10 (✅ 10/10 from interviews)
- **Time**: 30 seconds (baseline: 8 hours manual checklist)
- **Result**: G0.1 PASSED

**Step 4: Request Approval from CPO**
- **US1.5**: EM requests CPO approval (multi-approval workflow)
- **Time**: 5 minutes (baseline: 2 hours Slack back-and-forth)
- **Success**: CPO approves, G0.1 fully approved

**Step 5: View Next Gate (G0.2 - Market Validation)**
- **US1.4**: EM views gate dependency chain (G0.1 → G0.2 → G1)
- **Time**: 1 minute
- **Success**: EM sees G0.2 criteria (internal-first strategy, market sizing complete)

### Alternative Paths

**Path A: G0.1 BLOCKED (Insufficient Evidence)**
- EM uploads only 2 interviews (policy requires 3+)
- Gate evaluation → BLOCKED
- EM receives actionable feedback: "Upload 1 more user interview to meet policy requirements."
- EM uploads 3rd interview → Re-evaluate → G0.1 PASSED

**Path B: G0.1 Override (Emergency)**
- G0.1 BLOCKED (legal review delayed)
- EM requests override from CTO
- CTO approves override (expires in 7 days)
- G0.1 PASSED (OVERRIDE)

### Time Savings Breakdown

| Task | Baseline (Manual) | AI-Assisted | Savings |
|------|------------------|-------------|---------|
| Upload interviews | 30 min | 10 min | 20 min |
| Write PRD | 14 hours | 20 min | 13h 40min |
| Evaluate gate | 8 hours | 30 sec | 7h 59min |
| Request approval | 2 hours | 5 min | 1h 55min |
| **TOTAL** | **24h 30min** | **35 min** | **23h 55min (98% reduction)** |

---

## Journey 2: EM Defines Requirements (Stage 01 - WHAT)

### Backbone

1. **Define Functional Requirements** (Epic 1: Gate Management)
2. **Define Non-Functional Requirements** (Epic 1: Gate Management)
3. **Create User Stories** (Epic 2: Evidence Vault)
4. **Design Data Model** (Epic 3: Policy Packs)
5. **Define API Specs** (Epic 4: AI Context Engine)
6. **Evaluate Gate G1** (Epic 1: Gate Management)

### Detailed User Stories

**Step 1: AI Generates FRD from PRD**
- **US4.1**: AI converts PRD → 25 Functional Requirements (FR1-FR25)
- **Time**: 30 minutes (baseline: 8 hours manual FRD writing)
- **Success**: FRD ready for CTO review

**Step 2: Define NFRs (Performance, Security, Scalability)**
- **Manual**: EM + CTO collaborate on NFRs (17 NFRs: NFR1-NFR17)
- **Time**: 4 hours (baseline: 6 hours)
- **Success**: NFRs documented (99.9% uptime, <200ms API, AES-256 encryption)

**Step 3: Create User Stories (10 Epics, 50+ Stories)**
- **US3.1**: EM creates user stories from FRs (Epic 1-7)
- **Time**: 6 hours (baseline: 10 hours)
- **Success**: 50 user stories with acceptance criteria

**Step 4: Design Data Model (16 Tables)**
- **Manual**: Backend Lead designs ERD (users, teams, projects, gates, evidence, etc.)
- **Time**: 8 hours (baseline: 12 hours)
- **Success**: ERD reviewed by CTO (no N+1 queries)

**Step 5: Define API Specs (OpenAPI 3.0)**
- **Manual**: Backend Lead writes OpenAPI spec (30+ endpoints)
- **Time**: 10 hours (baseline: 16 hours)
- **Success**: API spec reviewed by Frontend Lead

**Step 6: Evaluate Gate G1 (Requirements)**
- **US1.2**: EM clicks "Evaluate G1"
- **Policies Checked**:
  - `policy-frd-completeness`: 25 FRs defined (✅)
  - `policy-nfr-completeness`: 17 NFRs defined (✅)
  - `policy-data-model-review`: CTO approved ERD (✅)
  - `policy-api-specs`: 30 endpoints documented (✅)
  - `policy-legal-review`: AGPL containment approved (✅)
- **Time**: 1 minute
- **Result**: G1 PASSED

**Step 7: Multi-Approval Workflow (CTO + CPO)**
- **US1.5**: System creates 2 approval requests (CTO, CPO)
- **CTO approves**: "Architecture looks good, no N+1 queries."
- **CPO approves**: "Requirements align with user pain points."
- **Time**: 30 minutes (baseline: 2 days email back-and-forth)
- **Result**: G1 fully approved, stage transition → Stage 02 (Architecture)

### Time Savings Breakdown

| Task | Baseline | AI-Assisted | Savings |
|------|----------|-------------|---------|
| AI FRD generation | 8h | 30min | 7h 30min |
| NFRs | 6h | 4h | 2h |
| User stories | 10h | 6h | 4h |
| Data model | 12h | 8h | 4h |
| API specs | 16h | 10h | 6h |
| Evaluate G1 | 4h | 1min | 3h 59min |
| Multi-approval | 2 days | 30min | ~15h |
| **TOTAL** | **58h** | **29h** | **29h (50% reduction)** |

---

## Journey 3: CTO Reviews Architecture (Stage 02 - HOW)

### Backbone

1. **Design System Architecture** (4-layer architecture)
2. **Design Database Schema** (PostgreSQL migrations)
3. **Design API Endpoints** (REST + GraphQL)
4. **Review Security Architecture** (RBAC, encryption, audit logs)
5. **Evaluate Gate G2** (Architecture)

### Detailed User Stories

**Step 1: Backend Lead Designs System Architecture**
- **Manual**: 4-layer architecture diagram (User-Facing, Business Logic, Integration, Infrastructure)
- **Time**: 12 hours (baseline: 20 hours)
- **Success**: Architecture diagram reviewed by CTO

**Step 2: Backend Lead Designs Database Schema**
- **Manual**: PostgreSQL schema (16 tables, indexes, migrations)
- **Time**: 16 hours (baseline: 24 hours)
- **Success**: Schema reviewed by CTO (no N+1 queries)

**Step 3: Backend Lead Designs API Endpoints**
- **Manual**: REST endpoints (30+), GraphQL schema
- **Time**: 20 hours (baseline: 32 hours)
- **Success**: API design reviewed by Frontend Lead

**Step 4: Security Lead Reviews Architecture**
- **Manual**: RBAC (13 roles), AES-256 encryption, audit logging
- **Time**: 8 hours (baseline: 12 hours)
- **Success**: Security architecture approved by CTO

**Step 5: Evaluate Gate G2 (Architecture)**
- **US1.2**: Backend Lead clicks "Evaluate G2"
- **Policies Checked**:
  - `policy-architecture-diagram`: 4-layer architecture defined (✅)
  - `policy-database-schema`: 16 tables, indexes, migrations (✅)
  - `policy-api-design`: 30+ endpoints documented (✅)
  - `policy-security-review`: Security Lead approved (✅)
- **Result**: G2 PASSED

**Step 6: Multi-Approval Workflow (CTO + Security Lead)**
- **CTO approves**: "Architecture scalable, no single point of failure."
- **Security Lead approves**: "RBAC correctly implemented, AES-256 encryption."
- **Result**: G2 fully approved, stage transition → Stage 03 (Build)

---

## Journey 4-7: Implementation, Testing, Deployment, Operations (Stages 03-06)

*Detailed story mapping for Stages 03-06 to be completed in Stage 02 (Design & Architecture).*

**Summary**:
- **Stage 03 (Build)**: Dev Lead implements features (FR1-FR25)
- **Stage 04 (Test)**: QA Lead runs unit/integration/load tests
- **Stage 05 (Deploy)**: DevOps Lead deploys to production (multi-AZ, auto-scaling)
- **Stage 06 (Operate)**: CIO monitors production (99.9% uptime, RTO <1hr)

---

## Story Mapping Summary

**Total Journeys Mapped**: 7 (Stage 00-06)
**Total User Stories**: 50+ (across 7 epics)
**Time Savings** (Stage 00 + Stage 01):
- **Baseline**: 82.5 hours
- **AI-Assisted**: 30 hours
- **Savings**: 52.5 hours (64% reduction)

**Key Insights**:
- **Biggest Time Savings**: AI PRD generation (14h → 20min = 98% reduction)
- **Biggest Adoption Risk**: Evidence Vault (25% adoption in Stage 00)
- **Highest Complexity**: Multi-approval workflow (G0.2, G1, G2, G5, G9)

---

## Next Steps

1. **UX Lead Review** (validate user journeys)
2. **Wireframe Creation** (Dashboard, VS Code Extension UI)
3. **Internal Beta Testing** (5-8 MTS/NQH teams, Week 11+)

---

## References

- [User Stories & Epics](./User-Stories-Epics.md) (v2.0.0)
- [Acceptance Criteria](./Acceptance-Criteria.md) (v2.0.0)
- [Functional Requirements Document](../01-Requirements/Functional-Requirements-Document.md) (v3.0.0)
- [EP-04 SDLC Structure Enforcement](../02-Epics/EP-04-SDLC-Structure-Enforcement.md)
- [EP-05 Enterprise Migration](../02-Epics/EP-05-ENTERPRISE-SDLC-MIGRATION.md)
- [EP-06 Codegen Engine](../02-Epics/EP-06-Codegen-Engine-Dual-Mode.md)

---

**Document**: SDLC-Orchestrator-Story-Mapping
**Framework**: SDLC 6.1.0 Stage 01 (WHAT) - Planning & Analysis
**Component**: User Journey Visualization
**Review**: Sprint planning sessions with PM + UX Lead
**Last Updated**: February 20, 2026

*"Story mapping bridges the gap between requirements and user experience."* 🗺️
