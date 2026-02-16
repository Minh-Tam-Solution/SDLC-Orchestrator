# Stage 01: Planning (WHAT?)
## Functional Requirements & System Specifications

**Stage**: 01 - PLANNING
**Question**: What are we building?
**Version**: 4.2.0
**Date**: January 30, 2026
**Status**: ✅ COMPLETED - Gate G1 PASSED
**Authority**: PM + CTO + CPO Approved
**Framework**: SDLC 6.0.6 (7-Pillar + Section 7 Quality Assurance + Section 8 Specification Standard)
**Positioning**: Operating System for Software 3.0

**Changelog v4.2.1** (Jan 30, 2026):
- **CLI Test Bug Fixes**: Sprint 127 continuation - validation testing revealed SDLC 6.0.5 migration gaps
  - **Stage Folder Naming**: Updated from legacy format to SDLC 6.0.5 convention
    - `00-Project-Foundation` → `00-foundation` (lowercase, hyphenated)
    - `01-Planning-Analysis` → `01-planning`
    - Full migration across CLI codebase (tier.py, p0.py, scanner.py)
  - **Pre-commit Hooks Module**: New `sdlcctl.hooks` package for CI/CD integration
    - `run_validation()` with docs_root, tier, strict parameters
  - **Fix Command Enhancement**: Creates `99-Legacy` folder in all stage folders
  - **Test Coverage**: 264 passed, 7 skipped (environment-specific)
  - See: [sdlcctl CHANGELOG v1.2.0](../../backend/sdlcctl/CHANGELOG.md)

**Changelog v4.2.0** (Jan 30, 2026):
- **Multi-Frontend Alignment**: Sprint 125-127 completed (26.5 SP in 1 day)
  - 3 delivery surfaces defined: Web Dashboard, CLI (sdlcctl), VS Code Extension
  - Frontend Alignment Matrix created (docs/01-planning/01-Requirements/Frontend-Alignment-Matrix.md)
  - CLI parity: 39% → 71% (+32 points)
  - Extension parity: 67% → 89% (+22 points)
- **SDLC 6.0.5 Framework**: All surfaces aligned to latest framework version
  - YAML frontmatter validation (SPEC-0002 compliant)
  - BDD requirements validation (GIVEN-WHEN-THEN)
  - Tier-specific sections validation (LITE/STANDARD/PROFESSIONAL/ENTERPRISE)
- **ADR-045**: Multi-Frontend Alignment Strategy documented
- **Framework Update Trigger**: GitHub Actions automation for version alignment
- **Monthly Checkpoint**: Process established for ongoing alignment

**Changelog v4.1.0** (Jan 19, 2026):
- **Sprint 78 Complete**: Sprint Analytics + Cross-Project Coordination (36/36 SP, 100%)
  - 4 new database models: RetroActionItem, SprintDependency, ResourceAllocation, SprintTemplate
  - 38 API endpoints (retrospectives, dependencies, resource allocation, templates)
  - Data model extended to 32 tables (28 core + 4 Sprint 78)
  - API specification: 52 → 90+ endpoints
- **Personal Teams Feature**: Design complete (awaiting CTO approval)
  - Dual ownership model: User-owned + Organization-owned teams
  - Schema changes: owner_id column, XOR constraint
  - API changes: organization_id optional, new response fields
- **Architecture Documentation**: ADR-025 re-enforced (unified frontend)
- **Governance Enhancements**: Mandatory ADR review in G-Sprint-Open gate

**Changelog v4.0.0** (Dec 23, 2025):
- **SOFTWARE 3.0 PIVOT**: Control Plane for AI Coders positioning
- **EP-06 IR-Based Codegen**: Sprint 45-50 (P0 priority), ~$50K investment
- **Founder Plan**: $99/team/month for Vietnam SME (~2.5M VND)
- **Dual Wedge Strategy**: Vietnam SME (40%) + Global EM (40%) + Enterprise (20%)
- **Year 1 Target**: 30-50 teams, $86K-$144K ARR (realistic, founder-led sales)
- **Sprint 45-50 Design Complete**: All 5 technical specs CTO-approved
- **Multi-Provider**: Ollama → Claude → DeepCode (DeepCode deferred Q2 2026)
- **Vietnamese Domain Templates**: F&B, Hotel, Retail with Vietnamese questionnaire

**Changelog v3.1.0** (Dec 23, 2025):
- **EP-04**: SDLC Structure Enforcement - Universal AI Codex Validation
- **EP-05**: Enterprise SDLC Migration Engine - Automated Pro/Enterprise Migration
- **EP-06**: Codegen Engine Tri-Mode - BYO + Native OSS + Hybrid Fallback
- **EP-06 Quality Gates (Stage 01 refresh)**: FR41-FR45 + NFR29-NFR35 + P8 traceability + codegen data/API additions
- **Model Roles**: IT Admin 10-model strategy integrated
- **NQH AI Platform**: qwen3-coder:30b (256K context) configured
- **.sdlc-config.json**: Revolutionary 1KB replacement for 700KB manual docs

---

## Purpose

Stage 01 answers the fundamental question: **"WHAT are we building?"**

This stage transforms validated problems (Stage 00) into detailed requirements:
- **Functional Requirements** (FR1-FR20+) - WHAT features to build
- **Non-Functional Requirements** (NFR1-NFR15+) - WHAT quality attributes
- **User Stories** (Epics → Stories → Tasks) - WHAT users can do
- **Data Model** (ERD, Schema) - WHAT data to store
- **API Specifications** (OpenAPI 3.0) - WHAT endpoints to expose

**Critical Success Factor**: We must define WHAT to build with enough detail that engineers can estimate effort and architects can design solutions.

---

## EP-06 (v3.1.0) Key Planning Additions

Stage 01 documents were updated to support Sprint 48 implementation of Codegen Quality Gates:

- **FR additions (FR41–FR45)**: IR-based codegen, 4-gate pipeline, validation loop (`max_retries=3`), evidence state machine (8 states), integration points.
- **NFR additions (NFR29–NFR35)**: latency budgets, state transition time (<100ms), 7 Prometheus metrics, escalation SLA (24h), CTX checks performance.
- **Data model**: 6 EP-06 tables added (ir_modules, codegen_generations, codegen_attempts, codegen_escalations, codegen_evidence, vcr_requests).
- **API spec**: +12 endpoints for codegen generation/status/attempts/escalations/evidence/VCR/metrics (total 52 → 64).

---

## Folder Structure (SDLC 5.1.0 Compliant)

```
01-planning/
├── README.md                               # This file
├── 01-Requirements/
│   ├── Functional-Requirements-Document.md # FR1-FR5 detailed specs
│   ├── Non-Functional-Requirements.md      # NFR1-NFR15+ quality attributes
│   ├── Requirements-Traceability-Matrix.md # FR → Design → Test mapping
│   └── FR-21-USER-AI-API-KEY-MANAGEMENT.md # Additional FRs
├── 02-Epics/
│   ├── EP-04-SDLC-Structure-Enforcement.md   # Universal AI Codex Validation ($16.5K, 117 SP)
│   ├── EP-05-ENTERPRISE-SDLC-MIGRATION.md    # Automated Migration (Deprioritized)
│   └── EP-06-IR-Based-Codegen-Engine.md      # IR-Based Codegen (~$50K, Sprint 45-50) ⭐ P0
├── 03-User-Stories/
│   ├── User-Stories-Epics.md               # Epic breakdown
│   ├── Acceptance-Criteria.md              # Definition of Done
│   └── Story-Mapping.md                    # Story map visualization
├── 04-Data-Model/
│   ├── Data-Model-v0.1.md                  # Initial data model
│   ├── Data-Model-ERD.md                   # Entity-Relationship Diagram
│   ├── Database-Schema.md                  # PostgreSQL schema
│   └── Data-Dictionary.md                  # Field definitions
├── 05-API-Design/
│   ├── API-Specification.md                # OpenAPI 3.0
│   ├── API-Authentication.md               # JWT + OAuth
│   └── API-Versioning-Strategy.md          # v1/v2 strategy
├── 06-Legal-Compliance/
│   ├── AGPL-Containment-Strategy.md        # OSS legal strategy
│   ├── AGPL-Containment-Legal-Brief.md     # Legal opinion
│   ├── Legal-Review-Report.md              # External counsel report
│   └── License-Audit-Report.md             # License scan results
└── STAGE-01-PROGRESS-REPORT.md             # Progress tracking
# Note: Legacy content migrated to docs/10-archive/01-Legacy/ per RFC-001
```

---

## Timeline (Week 2 - 2 Weeks)

| Days | Phase | Focus | Deliverables |
|------|-------|-------|--------------|
| 1-3 | **Legal Review** | AGPL containment validation | Legal Report, Go/No-Go Decision |
| 4-7 | **Requirements** | Functional + Non-Functional | FRD, NFR, RTM |
| 8-10 | **User Stories** | Epic → Story → Task breakdown | User Stories, Acceptance Criteria |
| 11-12 | **Data Model** | Database schema design | ERD, Schema, Data Dictionary |
| 13-14 | **API Specs** | REST endpoints, GraphQL schema | OpenAPI 3.0, Authentication |

---

## Quality Gates

### Gate G1: Planning & Analysis ✅

**Question**: "Have we defined WHAT to build with sufficient detail?"

**Criteria**:
- [x] Legal review PASSED (AGPL containment approved)
- [x] Internal-first strategy approved (5-8 MTS/NQH teams for Phase 1)
- [x] FRD updated (includes EP-06 FR41-FR45)
- [x] NFR updated (includes EP-06 NFR29-NFR35)
- [x] Data model reviewed (includes EP-06 codegen tables)
- [x] API specs complete (includes EP-06 codegen endpoints)
- [x] User stories estimated (story points, velocity calculated)

**Status**: ✅ PASSED

---

## Progress Tracker

### 01-Requirements (100% complete)
- ✅ Functional-Requirements-Document.md (v3.1.0, includes FR41-FR45)
- ✅ Non-Functional-Requirements.md (v3.1.0, includes NFR29-NFR35)
- ✅ Requirements-Traceability-Matrix.md (v2.1.0, includes P8 + FR41-FR45 + NFR29-NFR35)

### 02-Epics (Updated Dec 2025) ✅ COMPLETE
- ✅ EP-04-SDLC-Structure-Enforcement.md (Universal AI Codex Validation, Sprint 44-46, $16.5K)
- ⏸️ EP-05-ENTERPRISE-SDLC-MIGRATION.md (Deprioritized - pending EP-06 success)
- ✅ EP-06-IR-Based-Codegen-Engine.md (IR-Based Codegen, Sprint 45-50, ~$50K) ⭐ **P0 PRIORITY**

**Strategic Epics Summary (Dec 23, 2025 - Software 3.0 Pivot)**:

| Epic | Investment | Timeline | Priority | Key Innovation |
|------|------------|----------|----------|----------------|
| EP-04 | $16,500 | Sprint 44-46 | P1 | AI Codex Structure Protection |
| EP-05 | Deprioritized | Pending EP-06 | P2 | `.sdlc-config.json` (700x smaller) |
| EP-06 | ~$50,000 | Sprint 45-50 | **P0** ⭐ | IR-Based Codegen for Vietnam SME |

**EP-06 Sprint 45-50 Design Specs (CTO Approved)**:

| Sprint | Focus | Spec Document |
|--------|-------|---------------|
| 45 | Multi-Provider Architecture | ADR-022, Tech Spec |
| 46 | IR Processor Backend | IR-Processor-Specification.md |
| 47 | Vietnamese Domain Templates | Vietnamese-Domain-Templates-Specification.md |
| 48 | Quality Gates for Codegen | Quality-Gates-Codegen-Specification.md |
| 49 | Vietnam SME Pilot | Pilot-Execution-Specification.md |
| 50 | Productization + GA | Productization-Baseline-Specification.md |

### 03-User-Stories (100% complete)
- ✅ User-Stories-Epics.md
- ✅ Acceptance-Criteria.md
- ✅ Story-Mapping.md

### 04-Data-Model (100% complete)
- ✅ Data-Model-v0.1.md (baseline)
- ✅ Data-Model-ERD.md (v3.1.0, 30 tables incl. EP-06 codegen)
- ✅ Database-Schema.md
- ✅ Data-Dictionary.md

### 05-API-Design (100% complete)
- ✅ API-Specification.md (v3.1.0, 64 endpoints incl. +12 EP-06 codegen)
- ✅ API-Authentication.md (JWT + OAuth)
- ✅ API-Versioning-Strategy.md

### 06-Legal-Compliance (100% complete)
- ✅ AGPL-Containment-Strategy.md (42KB)
- ✅ AGPL-Containment-Legal-Brief.md
- ✅ Legal-Review-Report.md (37KB)
- ✅ License-Audit-Report.md

**Overall Progress**: 100% (20 of 20 documents complete)

---

## Exit Criteria (Stage 01 COMPLETED)

- [x] G1: Planning & Analysis validated ✅
- [x] Legal review PASSED (AGPL containment approved) ✅
- [x] All 20 required documents completed ✅
- [x] CTO review (data model 9.8/10, API specs approved) ✅
- [x] Backend Lead review (API specs, schema migrations planned) ✅
- [x] QA Lead review (test strategy defined based on requirements) ✅
- [x] Internal-first strategy (NQH Portfolio - 4 projects, 26 gates seed data) ✅

---

## Key Deliverables (WHAT We're Defining)

### 1. Functional Requirements (FR1-FR20+)

**FR1: Quality Gate Management**
- Gate Engine evaluates SDLC 4.8 policies
- Gate status (BLOCKED, PENDING, PASSED) visible in dashboard
- Gate checks run on git push (VS Code Extension)
- Policy packs configurable (YAML)

**FR2: Evidence Vault**
- Auto-collect evidence from Slack, GitHub, Figma
- Evidence encrypted (AES-256)
- Evidence searchable (full-text search)
- Evidence audit trail (who accessed when)

**FR3: AI Context Engine**
- Stage-aware AI (knows Stage 00-06)
- Multi-provider (Claude, GPT-4o, Gemini fallback)
- AI generates PRD from user interviews
- AI reviews designs for SDLC compliance

**FR4: Real-Time Dashboard**
- Gate status overview (all projects, all gates)
- Feature Adoption Rate tracking (30% → 70%+ target)
- Evidence completeness meter (per gate)
- Grafana iframe embedding (metrics)

**FR5: Policy Pack Library**
- 100+ SDLC 4.8 policy packs (Rego)
- Policy editor (VS Code-like, syntax highlighting)
- Policy testing framework (unit tests for policies)
- Policy versioning (Git-based)

*(FR6-FR20 to be detailed in FRD)*

---

### 2. Non-Functional Requirements (NFR1-NFR15+)

**NFR1: Performance**
- Gate check: <500ms (p95)
- Evidence upload: <2s for 10MB file
- Dashboard load: <1s (p95)
- API response: <200ms (p95)

**NFR2: Scalability**
- 100 teams Year 1 (100 concurrent users)
- 1,000 teams Year 3 (1,000 concurrent users)
- 10GB evidence storage per team
- 10K+ policy evaluations/sec (OPA benchmark)

**NFR3: Security**
- AES-256 encryption (at-rest + in-transit)
- RBAC (EM, CTO, PM roles)
- Audit logging (all actions logged)
- SOC 2 Type I compliant (Week 12)

**NFR4: Availability**
- 99.9% uptime SLA (8.76 hours downtime/year)
- Multi-AZ deployment (AWS us-east-1)
- Auto-scaling (1-10 instances)
- Disaster recovery: <1 hour RTO, <5 min RPO

**NFR5: Usability**
- Time to First Value: <1 hour (from signup to first gate check)
- Onboarding: <30 min (video + dashboard tour)
- SUS score: >70 (System Usability Scale)
- Mobile-responsive (dashboard accessible on mobile)

*(NFR6-NFR15 to be detailed in NFR)*

---

### 3. Data Model (Key Entities)

**Core Entities** (15+ tables):
1. **projects** - Project metadata (name, owner, created_at)
2. **gates** - Gate definitions (stage, criteria, status)
3. **evidence** - Evidence records (type, file_path, uploaded_by)
4. **policies** - Policy pack definitions (rego_code, version)
5. **users** - User accounts (email, role, team_id)
6. **teams** - Team/organization data (name, subscription_tier)
7. **features** - Feature tracking (name, adoption_rate, status)
8. **ai_contexts** - AI conversation history (prompt, response, stage)
9. **audit_logs** - Audit trail (action, user_id, timestamp)
10. **integrations** - External integrations (GitHub, Slack, Figma)

*(Full ERD with relationships in Data-Model-ERD.md)*

---

### 4. API Endpoints (30+ endpoints)

**Gate Management API**:
- `POST /api/v1/gates/evaluate` - Evaluate gate with policy
- `GET /api/v1/gates/{gate_id}/status` - Get gate status
- `PUT /api/v1/gates/{gate_id}/override` - Manual override (CTO only)

**Evidence Vault API**:
- `POST /api/v1/evidence/upload` - Upload evidence file
- `GET /api/v1/evidence/{evidence_id}` - Retrieve evidence
- `POST /api/v1/evidence/search` - Full-text search

**AI Context API**:
- `POST /api/v1/ai/generate-prd` - Generate PRD from interviews
- `POST /api/v1/ai/review-design` - Review design for SDLC compliance
- `GET /api/v1/ai/contexts/{project_id}` - Get AI conversation history

**Dashboard API**:
- `GET /api/v1/dashboard/overview` - Gate status, Feature Adoption Rate
- `GET /api/v1/dashboard/metrics` - Time-series metrics (Grafana data)

*(Full OpenAPI 3.0 spec in API-Specification.md)*

---

## Critical Path: Legal Review (Week 2)

### CRITICAL Go/No-Go Decision

**Timeline**: Week 2 (Jan 20-24)
**Blocker**: AGPL containment strategy must be approved by external legal counsel

**Legal Review Scope**:
1. **MinIO (AGPL v3)**: Can we use MinIO S3 API (HTTP calls) without triggering AGPL?
2. **Grafana (AGPL v3)**: Can we embed Grafana dashboards (iframe) without triggering AGPL?
3. **Commercial SaaS**: Can we offer paid SaaS that uses AGPL components (MinIO, Grafana)?

**Expected Outcome**: ✅ APPROVED (with containment strategy)

**Contingency Plans** (if Legal says NO):
- **Plan A**: Replace MinIO with SeaweedFS (Apache-2.0) - 2 weeks delay
- **Plan B**: Replace Grafana with Apache Superset (Apache-2.0) - 2 weeks delay
- **Plan C**: Pivot to pure OSS (no proprietary SaaS) - business model change

**Budget**: $75K allocated for legal review (external counsel)

---

## Relationship to Stage 00 (WHY → WHAT)

### How Stage 01 Builds on Stage 00

| Stage 00 (WHY) | Stage 01 (WHAT) |
|----------------|----------------|
| **Problem**: 60-70% feature waste | **Solution**: Gate Engine blocks un-validated features |
| **Persona**: Engineering Manager (60% of market) | **User Story**: "As EM, I want gate checks so that team doesn't build un-validated features" |
| **Pain**: No evidence trail (9/10 pain level) | **Feature**: Evidence Vault auto-collects proof from Slack/GitHub |
| **Goal**: Feature Adoption Rate 30% → 70%+ | **Metric**: Feature Adoption Rate tracking in dashboard |
| **Journey**: 43 hours manual work → 16 hours | **AI**: AI Context Engine generates PRD (14 hours saved) |

**Principle**: Every functional requirement (FR) must trace back to validated problem (Stage 00).

---

## Next Stages Preview (SDLC 5.1 Complete Lifecycle)

**Stage 02: Design & Architecture (HOW)** - Week 3-4
- System Architecture Diagram (4-layer architecture)
- Database Schema (PostgreSQL tables, indexes, migrations)
- API Design (REST endpoints, GraphQL schema)
- UI/UX Wireframes (Dashboard, VS Code Extension)
- Security Architecture (RBAC, encryption, audit logging)
- **Gate G2**: CTO + Security Lead approval

**Stage 03-09: Integration to Governance** - Week 5-12
- **Stage 03** (INTEGRATE): API contracts, integration tests ≥90%, event-driven
- **Stage 04** (BUILD): FastAPI backend, React frontend, VS Code extension
- **Stage 05** (TEST): 80%+ coverage, UAT ≥8.5/10, zero P0 bugs
- **Stage 06** (DEPLOY): Blue-green deployment, rollback <5min, 24/7 war room
- **Stage 07** (OPERATE): 99.9%+ uptime, P0 response <15min, monitoring ≥95%
- **Stage 08** (COLLABORATE): Documentation ≥90%, velocity stable ±20%
- **Stage 09** (GOVERN): Zero violations, budget ±10%, ROI tracking (target: 827:1)

---

## References

- [Stage 00: Foundation](../00-foundation/README.md) - WHY we're building
- [Product Roadmap](../00-foundation/04-Roadmap/Product-Roadmap.md) - 90-day timeline
- [SDLC 5.1 Core Methodology](../../SDLC-Enterprise-Framework/02-Core-Methodology/)

---

**Last Updated**: December 23, 2025
**Owner**: PM + Backend Lead + Legal Counsel + CTO
**Status**: ✅ COMPLETED

---

## Document Summary

**Total Documents**: 20+ (delivered)
**Total Lines**: 250,000+ lines across all documents
**Quality Gates**: G1 (Planning & Analysis) - ✅ PASSED
**Next Stage**: Stage 02 (Design & Architecture) - ✅ PASSED
**Current Stage**: Stage 04 (BUILD) - Sprint 44-50 EP-06
**Positioning**: Operating System for Software 3.0

**Strategic Updates (Dec 23, 2025 - Software 3.0 Pivot)**:
- **EP-06 IR-Based Codegen**: P0 priority, Sprint 45-50, ~$50K investment
- **Founder Plan**: $99/team/month for Vietnam SME (~2.5M VND)
- **Year 1 Target**: 30-50 teams, $86K-$144K ARR (realistic)
- **Sprint 45-50 Design Complete**: All 5 technical specs CTO-approved
- **Multi-Provider**: Ollama → Claude → DeepCode (DeepCode Q2 2026 decision gate)
- **Vietnamese Domain Templates**: F&B, Hotel, Retail with Vietnamese questionnaire

---

## Implementation Status

| Document | Size | Status |
|----------|------|--------|
| Data-Model-v0.1.md | 45KB | ✅ IMPLEMENTED (24 tables, Alembic) |
| Data-Model-ERD.md | 32KB | ✅ CURRENT (6-layer diagram) |
| FRD | 61KB | ✅ APPROVED (FR1-FR5) |
| Legal Compliance | 106KB | ✅ PASSED (AGPL containment) |

**Database Implementation**:
- 24 tables across 6 layers (Auth, Project, Gate, Policy, AI, System)
- Seed data: 12 users, 4 projects, 26 gates, 46 evidence files
- NQH Portfolio demo data (internal-first validation)

---

## Admin Panel & User Management (Sprint 37-40)

### Platform Admin Features (Dec 2025)

The Admin Panel was implemented in Sprint 37-40 to provide platform-level user management:

| Feature | Sprint | Status |
|---------|--------|--------|
| Admin Dashboard | 37 | ✅ Implemented |
| User List (paginated) | 37 | ✅ Implemented |
| User Activate/Deactivate | 37 | ✅ Implemented |
| User Superuser Toggle | 37 | ✅ Implemented |
| Audit Logs (SOC 2) | 37 | ✅ Implemented |
| System Settings (versioned) | 37 | ✅ Implemented |
| System Health Dashboard | 37 | ✅ Implemented |
| E2E Test Suite (121 tests) | 38 | ✅ Implemented |
| Toast Notifications | 39 | ✅ Implemented |
| Create User (POST) | 40 | ✅ Implemented |
| Soft Delete (DELETE) | 40 | ✅ Implemented |

### User Model Extensions

```sql
-- Sprint 40: Soft delete support
ALTER TABLE users ADD COLUMN deleted_at TIMESTAMP NULL;
ALTER TABLE users ADD COLUMN deleted_by UUID REFERENCES users(id);
CREATE INDEX ix_users_active_not_deleted ON users(is_active, deleted_at);
```

### API Endpoints (Admin Panel)

```
GET  /api/v1/admin/stats           - Dashboard statistics
GET  /api/v1/admin/users           - List users (paginated)
POST /api/v1/admin/users           - Create new user (Sprint 40)
GET  /api/v1/admin/users/{id}      - Get user details
PATCH /api/v1/admin/users/{id}     - Update user
DELETE /api/v1/admin/users/{id}    - Soft delete user (Sprint 40)
POST /api/v1/admin/users/bulk      - Bulk actions
GET  /api/v1/admin/audit-logs      - Audit logs (SOC 2)
GET  /api/v1/admin/settings        - System settings
PATCH /api/v1/admin/settings/{key} - Update setting
POST /api/v1/admin/settings/{key}/rollback - Rollback setting
GET  /api/v1/admin/system/health   - System health
```

**Security Enforced**:
- All endpoints require `is_superuser=true`
- Cannot delete/demote self
- Cannot delete last superuser
- Password minimum 12 characters
- All actions audit logged
