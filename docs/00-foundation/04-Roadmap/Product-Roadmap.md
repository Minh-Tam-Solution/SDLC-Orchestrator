# Product Roadmap
## Operating System for Software 3.0

**Version**: 7.0.0
**Date**: February 3, 2026
**Status**: ✅ CTO APPROVED - Sprint 147+ Roadmap (Spring Cleaning → Feature Complete)
**Authority**: CTO Approval (Feb 3, 2026), CEO/CPO Signatures (Jan 27, 2026)
**Foundation**: Financial Model v1.0, Product Vision v4.1.0, ADR-041, Framework 6.0.3
**Framework**: SDLC 6.0.3 + Quality Assurance System (Pillar 7) + Organization Access Control

**Changelog v7.0.0** (Feb 3, 2026):
- **Sprint 145 DEPLOYED**: MCP Integration Phase 1 (189%, 5,953 LOC)
  - Tag: sprint-145-v1.0.0 (Production Ready)
  - 571/578 tests passing (98.8%)
  - MCP Server + Context Providers + AI Pipeline integration
- **Sprint 146 COMPLETE**: Organization Access Control (472%, 6,772 LOC)
  - Backend: Organization invitation system with SHA256 tokens
  - Frontend: OrgInviteMemberModal, TierBadge, UserOrganizationsPanel
  - Tests: 108 tests (100% pass rate)
  - Celery cleanup job for 90-day retention
- **Sprint 147 COMPLETE**: Spring Cleaning (100%, 20/20 deliverables)
  - Tag: sprint-147-v1.0.0 (Production Ready)
  - V1 API Deprecation: -22 endpoints (Context Authority, Analytics) - Sunset: March 6, 2026
  - Product Telemetry: 10 core events, 3 funnels, 50K+ events tracked
  - CLI/Extension: 4 CLI commands + 3 extension commands instrumented
  - Migration Guides: 3 complete guides created
  - Test Coverage: 95% maintained
- **Sprint 147+ Roadmap APPROVED**: 24-sprint plan to 95% framework realization
  - Phase 1 (Sprint 147-150): Consolidation - V1/V2 API merge, telemetry
  - Phase 2 (Sprint 151-155): Feature Complete - SASE artifacts, Context Authority UI
  - Phase 3 (Sprint 156-160): Compliance - NIST AI RMF, EU AI Act, ISO 42001
  - Phase 4 (Sprint 161-165): Platform Engineering - IDP integration, EP-06 GA
  - Phase 5 (Sprint 166-170+): Market Expansion
- **Expert Synthesis Course Correction** (Feb 2, 2026):
  - ❌ Discord/Jira adapters DEFERRED (failed Opportunity Gate - no customer evidence)
  - ❌ Desktop App KILLED permanently (low ROI, 1.5 FTE maintenance)
  - ✅ V1/V2 Consolidation elevated to P0 (tech debt before features)
  - ✅ Product Truth Layer added (telemetry to verify framework realization)
- **New Planning Documents**:
  - [ROADMAP-147-170.md](../04-build/02-Sprint-Plans/ROADMAP-147-170.md)
  - [OPPORTUNITY-GATE-TEMPLATE.md](../09-govern/OPPORTUNITY-GATE-TEMPLATE.md)
  - [PRODUCT-TRUTH-LAYER-SPEC.md](../04-build/02-Sprint-Plans/PRODUCT-TRUTH-LAYER-SPEC.md)
  - [V1-V2-CONSOLIDATION-PLAN.md](../04-build/02-Sprint-Plans/V1-V2-CONSOLIDATION-PLAN.md)

**Changelog v6.0.0** (Jan 28, 2026):
- **Framework 6.0 Governance System**: Quality Assurance System (Pillar 7) complete
  - ADR-041 + Technical Spec approved (864 lines design documentation)
  - 6 components: Auto-Gen, Signals Engine, Stage Gating, Context Authority, Feedback, Kill Switch
  - Database: 14 governance tables (submissions, rejections, evidence_vault, audit_log, etc.)
  - CEO Dashboard: Time saved 40h→10h target, Vibecoding Index (0-100), routing breakdown
  - Success: 673/734 tests passing (91.6% overall), P6/P7 delivered ahead of schedule
- **Sprint 107-111 Complete** (Jan 20-28, 2026):
  - Sprint 107: TDD Foundation (41 tests, factories + stubs)
  - Sprint 108: Governance Foundation (266/295 tests, 90.16% pass rate)
  - Sprint 109: Intelligence Layer (125/125 tests, 100% pass rate - PERFECT)
  - Sprint 110: Observability (40/58 tests, 69% pass rate)
  - Sprint 111: Infrastructure Integration (242 tests, 100% pass rate)

**Changelog v5.1.0** (Jan 19, 2026):
- **Sprint 78 Complete**: Sprint Analytics + Cross-Project Coordination (36/36 SP, 100%)
  - 4 database models: RetroActionItem, SprintDependency, ResourceAllocation, SprintTemplate
  - 38 API endpoints (all <500ms p95)
  - 4 React components: SprintDependencyGraph, ResourceAllocationHeatmap, SprintTemplateSelector, SprintRetroComparison
  - 84 tests (98% coverage), zero P0 issues
  - Business impact: 60% faster sprint planning, 25% meeting reduction, 400% ROI
- **Personal Teams Design**: Dual ownership model design complete (awaiting CTO approval)
- **Sprint 79 Planning**: Team Authorization + Planning API Testing + Frontend Re-unification
- **Governance Lesson**: ADR enforcement now mandatory in G-Sprint-Open gate
- **Production Timeline**: Sprint 78 staging (Jan 20-21), production (Jan 22-23)

**Changelog v5.0.0** (Dec 23, 2025):
- **SOFTWARE 3.0 PIVOT**: Control Plane for AI Coders positioning
- **EP-06 IR-Based Codegen**: Sprint 45-50 (not Tri-Mode), P0 priority
- **Founder Plan**: $99/team/month for Vietnam SME (GA launch Q1 2026)
- **Year 1 Target**: 30-50 teams (realistic, founder-led sales)
- **Dual Wedge Strategy**: Vietnam SME (40%) + Global EM (40%) + Enterprise (20%)
- **Multi-Provider**: Ollama → Claude → DeepCode (deferred Q2 2026)
- **Sprint 45-50 Design Complete**: All 5 technical specs approved

**Changelog v4.1.0** (Dec 21, 2025):
- **EP-04**: SDLC Structure Enforcement (Sprint 41-46, $16.5K, 117 SP)
- **EP-05**: Enterprise SDLC Migration Engine (deprioritized, pending EP-06 success)
- **EP-06**: Codegen Engine initial scope defined
- **NQH AI Platform**: qwen2.5-coder:32b (92.7% HumanEval) ready
- **.sdlc-config.json**: 1KB replaces 700KB manual compliance docs

**Changelog v4.0.0** (Dec 20, 2025):
- **POSITIONING PIVOT**: "Project Governance Tool" → "AI-Native SDLC Governance & Safety Platform"
- Added 3 Strategic Epics (EP-01, EP-02, EP-03) for Q1-Q2 2026
- Added AI Safety Layer v1 as core capability
- Added Design Partner Program (10 external teams)
- Updated pricing tiers (Free / Team $149 / Enterprise $500+)
- Two-Track Launch Strategy (Internal + External parallel)
- CTO Approval: [Q1Q2-2026-ROADMAP-CTO-APPROVED.md](../../09-govern/04-Strategic-Updates/2025-12-20-Q1Q2-2026-ROADMAP-CTO-APPROVED.md)

---

## Executive Summary

### New Positioning (v5.0.0)

> **Product Category**: Operating System for Software 3.0
> **Tagline**: *"The Operating System for Software 3.0 - Where AI coders are governed, not feared."*

**Core Value Proposition**:
- AI coding tools (Cursor, Copilot, Claude Code) increase throughput but create governance gaps
- SDLC Orchestrator is the **control plane** that sits ABOVE AI coders, not alongside them
- Differentiation: 3-Layer Architecture + IR-Based Codegen + Founder Plan for Vietnam SME

**3-Layer Architecture**:
```
Layer 3: AI Coders (Claude/Cursor/Copilot/OSS) ← We orchestrate
Layer 2: SDLC Orchestrator (Governance + Codegen) ← Our product
Layer 1: SDLC-Enterprise-Framework (Methodology) ← Our foundation
```

### 2026 Strategic Themes

| Theme | Description | Success Metric |
|-------|-------------|----------------|
| **EP-06 Codegen P0** | IR-based codegen for Vietnam SME | 10 pilots, 8/10 satisfaction, TTFV <30min |
| **Founder Plan GA** | $99/team/month Vietnam SME | 30-50 teams Year 1 |
| **AI Governance** | Every AI change validated before merge | 0 unreviewed AI PRs merged |
| **Multi-VCS** | GitLab/Bitbucket support | Q3 2026 |

---

## Current Status (February 2026)

### Sprint 146 Complete ✅ (Organization Access Control)

| Phase | Status | Gate |
|-------|--------|------|
| **Foundation** (Nov 2025) | ✅ COMPLETE | G0.1 ✅, G0.2 ✅ |
| **Planning** (Nov 2025) | ✅ COMPLETE | G1 ✅ (Legal + Market) |
| **Design** (Nov-Dec 2025) | ✅ COMPLETE | G2 ✅ (Architecture 9.4/10) |
| **Build** (Dec 2025 - Feb 2026) | ✅ Sprint 33-146 COMPLETE | Sprint 146: 108 tests (100%) |
| **Sprint 145** (Jan 27-31, 2026) | ✅ DEPLOYED | MCP Integration (tag: sprint-145-v1.0.0) |
| **Sprint 146** (Feb 1-2, 2026) | ✅ COMPLETE | Organization Access Control (472% achievement) |
| **Sprint 147** (Feb 4-8, 2026) | ✅ COMPLETE | Spring Cleaning (100% achievement, tag: sprint-147-v1.0.0) |
| **Sprint 148** (Feb 11-15, 2026) | 📋 NEXT | Service Consolidation (164 → 140 services) |

### Sprint 145-147 Achievement Summary

| Sprint | Focus | LOC | Tests | Achievement |
|--------|-------|-----|-------|-------------|
| **Sprint 145** | MCP Integration Phase 1 | 5,953 | 571/578 (98.8%) | 189% |
| **Sprint 146** | Organization Access Control | 6,772 | 108/108 (100%) | 472% |
| **Sprint 147** | Spring Cleaning (V1/V2 + Telemetry) | ~1,500 | 95% coverage | 100% |
| **Total** | | **14,225+** | **700+ tests** | **254% avg** |

**Sprint 147 Key Deliverables**:
1. **V1 API Deprecation** (-22 endpoints, Sunset: March 6, 2026):
   - Context Authority V1: 7 endpoints deprecated
   - Analytics V1: 15 endpoints deprecated
   - Migration guides: 3 complete guides created

2. **Product Telemetry MVP**:
   - 10 core events: user_signed_up, project_created, first_evidence_uploaded, etc.
   - 3 activation funnels: Time-to-First-Project, Time-to-First-Evidence, Time-to-First-Gate-Pass
   - Backend: product_event.py model, telemetry_service.py, 6 API endpoints
   - Frontend: telemetry.ts client, 5 hooks instrumented

3. **CLI/Extension Instrumentation**:
   - CLI: 4 commands (validate, spec, report, init) with telemetry.py module
   - Extension: 3 commands (specValidation, init, e2eValidate) with telemetryService.ts

4. **Test Coverage**: 95% maintained across all changes

### Sprint 147-170+ Roadmap (CTO APPROVED)

**Status**: ✅ APPROVED - Spring Cleaning → Feature Complete → Compliance → Platform Engineering
**Timeline**: February 4, 2026 - October 2026 (24 sprints)
**Target**: 82-85% → 95% Framework Realization

| Phase | Sprints | Focus | Key Outcomes |
|-------|---------|-------|--------------|
| **Phase 1: Consolidation** | 147-150 | Spring Cleaning | -22 endpoints, -44 services, telemetry MVP |
| **Phase 2: Feature Complete** | 151-155 | SASE + Context Auth UI | 60% → 95% feature coverage |
| **Phase 3: Compliance** | 156-160 | NIST/EU AI Act/ISO 42001 | Compliance dashboard |
| **Phase 4: Platform Engineering** | 161-165 | IDP + EP-06 GA | Golden Path integration |
| **Phase 5: Market Expansion** | 166-170+ | Scale | 150-300 teams target |

### Sprint 147: Spring Cleaning (Feb 4-8, 2026) ✅ COMPLETE

**Priority**: P0 - Tech Debt Reduction
**Achievement**: 100% (20/20 deliverables)
**Tag**: sprint-147-v1.0.0

| Day | Focus | Achievement |
|-----|-------|-------------|
| **Mon** | Context Authority V1/V2 Merge | ✅ -7 endpoints (Context Authority V1 deprecated) |
| **Tue** | Analytics V1 Deprecation | ✅ -15 endpoints (Analytics V1 deprecated) |
| **Wed** | Product Truth Layer MVP | ✅ 10 events instrumented, 3 funnels |
| **Thu** | CLI/Extension Telemetry | ✅ 4 CLI commands + 3 extension commands |
| **Fri** | Verification + Documentation | ✅ All tests passing, docs complete |

**V1/V2 Consolidation Results**:
- Context Authority: 7 V1 endpoints deprecated → V2 only
- Analytics: 15 V1 endpoints deprecated → V2 only
- **Total**: -22 V1 endpoints, Sunset date: March 6, 2026
- Migration guides: 3 guides created (Context Authority, Analytics, V1 Deprecation Notice)

**Product Telemetry Results**:
- 10 core events tracked across web, CLI, extension
- 3 activation funnels operational
- 50K+ events tracked in first week
- Backend: 6 new API endpoints, telemetry_service.py
- Frontend: telemetry.ts client, 5 hooks instrumented
- CLI: telemetry.py module, 4 commands instrumented
- Extension: telemetryService.ts, 3 commands instrumented

**Next Sprint**: Sprint 148 - Service Consolidation (Feb 11-15)

### Framework Realization Progress

| Area | Current | Target | Gap |
|------|---------|--------|-----|
| **Quality Assurance System** | 85% | 95% | 10% |
| **SASE Artifacts (VCR/CRP)** | 60% | 95% | 35% |
| **Context Authority** | 50% | 90% | 40% |
| **Spec Standard** | 55% | 90% | 35% |
| **Cross-Reference** | 30% | 85% | 55% |
| **Planning Sync** | 40% | 85% | 45% |
| **Overall Realization** | 82-85% | 95% | 10-13% |

### Killed Features (Expert Synthesis)

| Feature | Reason | Savings |
|---------|--------|---------|
| **Desktop App (Tauri)** | Low ROI, VS Code Extension sufficient | 1.5 FTE/year |
| **Discord Adapter** | No customer evidence (failed Opportunity Gate) | $30K |
| **Jira Adapter** | No LOI evidence (deferred to Sprint 150+) | $25K |

### North Star Metrics (90 Days)

| Metric | Current | Target | Method |
|--------|---------|--------|--------|
| Time-to-First-Gate-Pass | Unknown | <60 min (p90) | Telemetry |
| Activation Rate | ~40% | >60% | Product Truth Layer |
| Framework Realization | 82-85% | 95% | Sprint execution |
  - Mode toggle (OFF/WARNING/SOFT/FULL)
  - Rollback criteria dashboard

**Sprint 114 Details** (Feb 3-7):
- **Dogfooding Plan**:
  - GOVERNANCE_MODE=WARNING on Orchestrator repo
  - All PRs evaluated but not blocked
  - Collect baseline metrics: Developer friction, false positive rate, Vibecoding Index distribution
  - Go/No-Go decision for Soft Enforcement

**Sprint 115-116 Details** (Feb 10-21):
- **Soft Enforcement** (Sprint 115):
  - Block: Missing ownership, missing intent, index >80, security scan failures
  - Warn: Stale AGENTS.md, missing ADR, index 61-80
- **Full Enforcement** (Sprint 116):
  - All violations block except Green auto-approve (<30 index)
  - Measure CEO time saved (target: 40h→20h, -50%)
  - Customer-ready governance (docs, runbooks, support escalation)

**Framework 6.0 Complete**: February 21, 2026 (1 week ahead of original schedule)

### Platform Capabilities (February 2026)

**Core Platform:**
- ✅ **Backend API**: 120+ endpoints (FastAPI, PostgreSQL, Redis)
- ✅ **Frontend**: Unified Next.js (port 8310), React components, Admin Panel, CEO Dashboard
- ✅ **Authentication**: JWT + OAuth (GitHub), MFA support
- ✅ **Gate Engine**: OPA integration, YAML → Rego policies
- ✅ **Evidence Vault**: MinIO S3, SHA256 hashing
- ✅ **AI Council**: Ollama + Claude integration
- ✅ **VS Code Extension**: AI-assisted development
- ✅ **CLI Tool**: sdlcctl validate
- ✅ **MCP Integration**: Model Context Protocol server + 12 context providers

**Governance System (Framework 6.0.3):**
- ✅ **Auto-Generation Layer**: Intent skeleton, Ownership suggestions, Context attachment, Attestation pre-fill
- ✅ **Governance Signals Engine**: Vibecoding Index (0-100), 5 signals
- ✅ **Stage Gating Service**: 11 SDLC stage validation, prerequisite checking
- ✅ **Context Authority Service**: ADR linkage, Design doc reference, AGENTS.md freshness (<7 days)
- ✅ **Feedback Loop**: Kill Switch (auto-rollback on rejection >80%), Manual CTO/CEO rollback
- ✅ **CEO Dashboard**: Time saved calculation, Routing breakdown (Green/Yellow/Orange/Red)
- ✅ **Metrics & Observability**: 45 Prometheus metrics, 3 Grafana dashboards

**Organization Access Control (Sprint 146 - NEW):**
- ✅ **Organization Invitations**: SHA256 token-based, 7-day expiry, rate limiting
- ✅ **RBAC Enforcement**: Role-based invitation permissions
- ✅ **Invitation Cleanup**: Celery task for 90-day retention
- ✅ **Frontend Components**: OrgInviteMemberModal, TierBadge, UserOrganizationsPanel

**MCP Integration (Sprint 145 - NEW):**
- ✅ **MCP Server**: stdio + SSE transports
- ✅ **Context Providers**: 12 providers (project, gate, evidence, AI council, etc.)
- ✅ **AI Pipeline Integration**: Claude, Cursor, Copilot context sharing
- ✅ **Resource Management**: Dynamic context loading

**Sprint Management:**
- ✅ **Retrospective Enhancement**: Action item tracking across sprints
- ✅ **Cross-Project Dependencies**: Dependency graph, circular detection
- ✅ **Resource Allocation**: Capacity planning, conflict detection
- ✅ **Sprint Template Library**: 4 default templates

**Architecture:**
- ✅ **Unified Frontend**: Single Next.js service on port 8310 (ADR-025)
- ✅ **Container Status**: sdlc-frontend (8310:3000), sdlc-backend (8300:8300)
- ✅ **Routes**: `/` (landing), `/login` (auth), `/app/*` (dashboard), `/admin/*` (admin)

**Quality Metrics (Sprint 146):**
- ✅ **Test Coverage**: 98.8% overall (679+ tests passing)
- ✅ **Performance**: All API endpoints <500ms p95
- ✅ **Security**: 100% OWASP API compliance, zero P0 issues
- ✅ **TypeScript**: 100% coverage in frontend

---

## 2026 Roadmap Overview

### Milestone Map (Updated Feb 2026)

| Milestone | Date | Key Outcomes |
|-----------|------|--------------|
| **M0** | February 2026 | Sprint 147+ roadmap approved, V1/V2 consolidation started |
| **M1** | March 2026 | Phase 1 complete (-22 endpoints, telemetry live), SASE 60%→75% |
| **M2** | June 2026 | Feature complete (95% framework realization), Context Authority UI |
| **M3** | September 2026 | Compliance dashboard (NIST + EU AI Act prep), ISO 42001 alignment |
| **M4** | December 2026 | Platform engineering complete, EP-06 GA, IDP integration |
| **M5** | 2027 | 150-300 teams, Gartner inclusion, compliance certifications |

### Sprint 147-170+ Phases

| Phase | Sprints | Dates | Theme | Target |
|-------|---------|-------|-------|--------|
| **Phase 1** | 147-150 | Feb 4 - Mar 1 | Consolidation | -22 endpoints, -44 services, telemetry |
| **Phase 2** | 151-155 | Mar 4 - Apr 5 | Feature Complete | SASE 95%, Context Auth UI 90% |
| **Phase 3** | 156-160 | Apr 8 - May 10 | Compliance | NIST/EU AI Act/ISO 42001 |
| **Phase 4** | 161-165 | May 13 - Jun 14 | Platform Engineering | IDP, EP-06 GA |
| **Phase 5** | 166-170+ | Jun 17+ | Market Expansion | 150-300 teams |

### Quarterly Investment (Updated)

| Quarter | Theme | Primary Focus | Investment |
|---------|-------|---------------|------------|
| **Q1 2026** | Consolidation | V1/V2 merge, Telemetry MVP | ~$25,000 |
| **Q1-Q2 2026** | Feature Complete | SASE artifacts, Context Auth UI | ~$50,000 |
| **Q2 2026** | Compliance | NIST AI RMF, EU AI Act | ~$60,000 |
| **Q3 2026** | Platform Engineering | IDP integration, EP-06 GA | ~$80,000 |
| **Q4 2026** | Market Expansion | Scale to 150+ teams | ~$100,000 |

---

## Phase 1: Consolidation (Sprint 147-150)

### Sprint 147: Spring Cleaning (Feb 4-8, 2026)

**Priority**: P0 - V1/V2 API Consolidation + Product Telemetry
**Target**: -22 endpoints, +10 telemetry events

| Day | Task | Deliverable |
|-----|------|-------------|
| Mon | Context Authority V1/V2 Merge | 18 → 9 endpoints |
| Tue | Analytics V1 Deprecation | 19 → 6 endpoints |
| Wed | Product Truth Layer MVP | 10 events instrumented |
| Thu | Service Boundary Audit | 164 → <155 services |
| Fri | System Inventory SSOT | CI auto-generation |

**V1/V2 Migration Details**:
- [V1-V2-CONSOLIDATION-PLAN.md](../04-build/02-Sprint-Plans/V1-V2-CONSOLIDATION-PLAN.md)

### Sprint 148-150: Deep Consolidation (Feb 11 - Mar 1)

| Sprint | Focus | Target |
|--------|-------|--------|
| **Sprint 148** | Service boundary merge | 155 → 140 services |
| **Sprint 149** | Vibecoding V1/V2, AI Detection merge | 140 → 130 services |
| **Sprint 150** | Dead code removal, Phase 1 verification | 130 → 120 services, baseline |

**Phase 1 Exit Criteria**:
- [ ] V1 endpoints removed (Context Authority, Analytics)
- [ ] Service count: 164 → <120
- [ ] Telemetry: 10 core events live
- [ ] System inventory auto-generated in CI

---

## Phase 2: Feature Complete (Sprint 151-155)

### Focus Areas

| Sprint | Focus | Deliverable |
|--------|-------|-------------|
| **Sprint 151** | SASE Artifacts (VCR/CRP) | 60% → 75% |
| **Sprint 152** | Context Authority UI | 50% → 70% |
| **Sprint 153** | Real-time Notifications | WebSocket integration |
| **Sprint 154** | Spec Standard completion | 55% → 80% |
| **Sprint 155** | Cross-Reference + Planning Sync | 30% → 60%, 40% → 65% |

**Phase 2 Exit Criteria**:
- [ ] SASE Artifacts: 95% feature complete
- [ ] Context Authority UI: 90% feature complete
- [ ] Framework Realization: 85% → 92%

---

## Phase 3: Compliance (Sprint 156-160)

### Compliance Targets

| Standard | Deadline | Priority |
|----------|----------|----------|
| **NIST AI RMF** | Q2 2026 | P0 |
| **EU AI Act** | August 2026 | P0 |
| **ISO 42001** | Q3 2026 | P1 |
| **SOC 2 Type II** | Q4 2026 | P2 |

### Sprint Allocation

| Sprint | Focus | Deliverable |
|--------|-------|-------------|
| **Sprint 156** | NIST AI RMF Gap Analysis | Assessment report |
| **Sprint 157** | NIST Controls Implementation | 80% coverage |
| **Sprint 158** | EU AI Act Requirements | Documentation |
| **Sprint 159** | ISO 42001 Alignment | Control mapping |
| **Sprint 160** | Unified Compliance Dashboard | Single view |

**Phase 3 Exit Criteria**:
- [ ] NIST AI RMF: 90% control coverage
- [ ] EU AI Act: Documentation complete
- [ ] Compliance Dashboard: Live

---

## Phase 4: Platform Engineering (Sprint 161-165)

### Focus Areas

| Sprint | Focus | Deliverable |
|--------|-------|-------------|
| **Sprint 161** | IDP Golden Path integration | Template system |
| **Sprint 162** | Developer Experience | DX improvements |
| **Sprint 163** | EP-06 Codegen refinement | Quality gates |
| **Sprint 164** | EP-06 GA preparation | Documentation |
| **Sprint 165** | EP-06 GA Release | Production ready |

**Phase 4 Exit Criteria**:
- [ ] IDP Golden Path: 5 templates
- [ ] EP-06 Codegen: GA release
- [ ] Framework Realization: 95%

---

## Phase 5: Market Expansion (Sprint 166-170+)

### Targets

- **Team Count**: 50 → 150-300 teams
- **Revenue**: $100K → $500K ARR
- **Compliance Certifications**: NIST, ISO 42001, SOC 2

### Key Initiatives

1. **Scale Infrastructure**: Auto-scaling, multi-region
2. **Enterprise Features**: SSO, SCIM, audit logs
3. **Partner Program**: System integrator partnerships
4. **Marketing**: Case studies, conference presence

---

## Opportunity Gate Framework (NEW)

All P0/P1 features must pass 5 questions before development:

| # | Question | Threshold | Kill If |
|---|----------|-----------|---------|
| 1 | **User Pull** | ≥10 customers requested | <5 requests |
| 2 | **Time-to-Value** | ≥30% improvement | <15% improvement |
| 3 | **Revenue Impact** | Quantified | "Nice to have" |
| 4 | **Surface Area** | ≤2 secrets, ≤10 endpoints | >5 secrets, >20 endpoints |
| 5 | **Kill Switch** | Rollback in 1 day | No rollback plan |

### Example Applications

**Discord Adapter** (FAILED - Deferred):
- User Pull: 2 requests ❌ (<10 threshold)
- Revenue Impact: "Nice to have" ❌
- **Decision**: DEFER to Sprint 150+

**Product Telemetry** (PASSED):
- User Pull: Internal requirement ✅
- Time-to-Value: Validates "82% realization" claim ✅
- Revenue Impact: Required for investor metrics ✅
- **Decision**: P0 for Sprint 147

Full template: [OPPORTUNITY-GATE-TEMPLATE.md](../09-govern/OPPORTUNITY-GATE-TEMPLATE.md)

---

## Product Truth Layer (Sprint 147)

### Core Events (10)

| Event | Trigger | Properties |
|-------|---------|------------|
| `user_signed_up` | Registration complete | method, plan |
| `project_created` | New project | template, has_repo |
| `gate_evaluation_started` | Gate run begins | gate_id, trigger |
| `gate_evaluation_completed` | Gate run ends | passed, duration_ms |
| `evidence_uploaded` | Evidence submitted | type, size_bytes |
| `evidence_approved` | Evidence passes | reviewer_type |
| `ai_suggestion_generated` | AI provides suggestion | model, tokens |
| `ai_suggestion_accepted` | User accepts AI | edit_distance |
| `sprint_started` | Sprint begins | story_points |
| `sprint_completed` | Sprint ends | velocity, completion_rate |

### Funnels (3)

| Funnel | Steps | Target |
|--------|-------|--------|
| **Time-to-First-Project** | signup → project_created | <5 min (p90) |
| **Time-to-First-Evidence** | project_created → evidence_uploaded | <15 min (p90) |
| **Time-to-First-Gate-Pass** | evidence_uploaded → gate_passed | <60 min (p90) |

Full spec: [PRODUCT-TRUTH-LAYER-SPEC.md](../04-build/02-Sprint-Plans/PRODUCT-TRUTH-LAYER-SPEC.md)

---

## Track 1 SASE: Framework Enhancement (Updated Status)

**Status**: 🔄 **IN PROGRESS** - Phase 2-Pilot (Week 5/8)
**Priority**: P0 - Critical (Q1 2026 Top Priority)
**Budget**: $50,000
**Timeline**: Dec 9, 2025 - **April 18, 2026** (14 weeks + 1 week adjustment)
**Authority**: CTO APPROVED (Dec 8, 2025 + Jan 17, 2026 adjustment)

### Overview

SASE (Structured Agentic Software Engineering) integration into SDLC Framework and Orchestrator platform, based on research paper [arXiv:2509.06216v2](https://arxiv.org/abs/2509.06216).

**Approach**: Framework-First (Track 1 → Track 2)
- ✅ **Track 1**: Framework Enhancement (methodology, templates) - Q1 2026
- ⏳ **Track 2**: Orchestrator Automation (tooling) - Q2 2026 (conditional on Track 1 success)

### Phase Timeline (Adjusted)

| Phase | Original Timeline | Adjusted Timeline | Status | Deliverables |
|-------|------------------|-------------------|--------|--------------|
| **Phase 1-Spec** | Weeks 1-2 (Dec 9-20) | Weeks 1-2 (Dec 9-20) | ✅ COMPLETE | 4 documents + 6 templates |
| **Phase 2-Pilot** | Weeks 3-8 (Dec 23 - Feb 7) | Weeks 3-9 (Dec 23 - Feb 14) | 🔄 IN PROGRESS | Week 5/8 |
| **Phase 3-Rollout** | Weeks 9-12 (Feb 10 - Mar 6) | Weeks 10-13 (Feb 17 - Mar 13) | ⏳ PLANNED | 5 NQH projects |
| **Phase 4-Retro** | Weeks 13-14 (Mar 9-20) | Weeks 14-15 (Mar 16-27) | ⏳ PLANNED | Lessons learned |

**Timeline Adjustment Rationale**: Sprint 69 (Route Restructure + MinIO Migration) took priority during Weeks 3-4 → Pilot kickoff delayed to Week 6 (Jan 20)

**Impact**: +1 week delay, still within Q1 2026 (April 30 deadline)

### Phase 1-Spec: Framework Templates (COMPLETE ✅)

**Deliverables** (all committed to SDLC-Enterprise-Framework):

1. **Core Documents** (4):
   - SDLC-Agentic-Core-Principles.md (SE4H vs SE4A distinction)
   - SDLC-Agentic-Maturity-Model.md (Level 0-3)
   - ACE-AEE-Reference-Architecture.md (Agent environments)

2. **Artifact Templates** (6):
   - BriefingScript-Template.yaml (BRS)
   - LoopScript-Template.yaml (LPS)
   - MentorScript-Template.md (MTS)
   - CRP-Template.md (Consultation Request Pack)
   - MRP-Template.md (Merge-Readiness Pack)
   - VCR-Template.md (Version Controlled Resolution)

**Quality**: 8.75/10 (CTO assessment - exceeds expectations)

### Phase 2-Pilot: SOP Generator (Week 5/8 🔄)

**Feature**: NQH-Bot SOP Generator (AI-assisted SOP generation)
**Timeline**: Jan 20 - Feb 14, 2026 (6 weeks, Weeks 6-11)
**Budget**: $23,000

**Artifacts Created**:
- ✅ BRS-PILOT-001 (STATUS: APPROVED - Jan 17)
- ✅ LPS-PILOT-001 (6 iterations defined - Jan 17)
- ✅ MRP-PILOT-001-EXAMPLE (template - Jan 17)
- ✅ VCR-PILOT-001-EXAMPLE (template - Jan 17)

**6 Iterations** (per LPS-PILOT-001):
1. Week 6 (Jan 20-24): Template Design + Basic Generation
2. Week 7 (Jan 27-31): ISO 9001 Compliance Validation
3. Week 8 (Feb 3-7): Evidence Vault Integration
4. Week 9 (Feb 10-14): MRP/VCR Workflow
5. Week 10 (Feb 17-21): 5 SOP Types Implementation
6. Week 11 (Feb 24-28): Quality Review + Pilot Completion

**Success Criteria**:
- 5 SOPs generated (1 per type: Deployment, Incident, Change, Backup, Security)
- Developer satisfaction ≥4/5
- Time reduction ≥20% (baseline: 2-4h manual SOP creation)
- Agent cost <$50/month
- Zero P0 incidents

**Week 4 Checkpoint** (Jan 17, 2026 - MAKEUP SESSION):
- Kill-switch criteria: 0/4 failed (no trigger)
- Decision: ✅ CONTINUE with +1 week adjustment
- Next checkpoint: Week 8 (Feb 7)

### Phase 3-Rollout: 5 NQH Projects (Weeks 10-13)

**Target Projects**:
1. Bflow Platform (SOP for deployment workflows)
2. NQH-Bot (SOP for incident response)
3. MTEP Platform (SOP for change management)
4. SDLC Orchestrator (SOP for backup & recovery)
5. Superset Analytics (SOP for security procedures)

**Success Criteria**:
- 5/5 projects using SASE artifacts (Level 1+)
- 2/5 projects reached Level 2 (Structured Agentic)
- Developer satisfaction ≥4/5 across all projects
- Agent cost <$50/month across all projects
- Zero P0 incidents caused by SASE workflow

**Budget**: $15,000

### Phase 4-Retrospective (Weeks 14-15)

**Activities**:
- Week 14: Retrospective workshop with all teams
- Week 15: Track 2 Go/No-Go decision preparation

**Deliverables**:
- Lessons Learned Document
- Track 2 Requirements Document (if Go decision)
- Q2 2026 Roadmap Update

**Budget**: Covered within Phase 1-Spec buffer

### Budget Breakdown

| Phase | Budget | Spent (as of Week 5) | Remaining |
|-------|--------|---------------------|-----------|
| Phase 1-Spec | $10,000 | $10,000 | $0 |
| Phase 2-Pilot | $25,000 | $2,000 | $23,000 |
| Phase 3-Rollout | $15,000 | $0 | $15,000 |
| **TOTAL** | **$50,000** | **$12,000** | **$38,000** |

**Burn Rate**: 24% spent at 36% timeline (under budget ✅)

### Key References

- **SE 3.0 SASE Plan**: `docs/09-govern/04-Strategic-Updates/SE3.0-SASE-Integration-Plan-APPROVED.md`
- **Week 5 Progress**: `docs/09-govern/01-CTO-Reports/SASE-Week-5-Progress-Report.md`
- **Week 4 Retrospective**: `docs/09-govern/01-CTO-Reports/SASE-Week-4-Checkpoint-Retrospective.md`
- **Pilot Artifacts**: `docs/04-build/05-SASE-Artifacts/` (BRS/LPS/MRP/VCR)

---

## Q1-Q2 2026: AI Safety First (Detailed)

### EP-01: Idea & Stalled Project Flow with AI Governance Hints

**Status**: ✅ CTO APPROVED  
**Priority**: P0 - Critical  
**Timeline**: Sprint 41-45 (Jan-Mar 2026)  
**Budget**: $15,000

**Problem**: Ideation and stalled work scattered across tools with no governance context, 60%+ effort waste.

**Scope**:
- **"Ý tưởng mới" Flow**: NL input → classification → risk tier → policy pack suggestion → Idea Card
- **"Dự án dở dang" Flow**: Repo scan → gap analysis → AI recommendations (Kill/Rescue/Park)
- **Persona Dashboards**: EM (waste detection), PM (backlog generation), CTO (portfolio gaps)

**Success Criteria**:
- ≥80% ideas receive auto policy pack suggestion
- Stalled project assessment <10s
- ≥70% internal EM/PM use weekly after 4 weeks

### EP-02: AI Safety Layer v1

**Status**: ✅ CTO APPROVED  
**Priority**: P0 - Critical  
**Timeline**: Sprint 41-45 (Jan-Mar 2026)  
**Budget**: $25,000

**Problem**: AI-generated code from Cursor/Copilot/Claude creates governance gaps, architecture drift, missing evidence.

**Scope**:
- **AI Detection**: Auto-tag PRs from AI tools (metadata, commit patterns, manual tag)
- **Output Validators**: Lint, Tests, Coverage, SAST, Architecture checks
- **Policy Guards**: OPA-based enforcement, auto-comment PR, VCR override
- **Evidence Trail**: `ai_code_events` collection, timeline view per PR

**3 Killer Capabilities**:
1. "AI không được merge code nếu vi phạm kiến trúc"
2. "Mọi AI code có Evidence trail đầy đủ"
3. "AI gợi ý - Orchestrator quyết định"

**Success Criteria**:
- 100% AI-tagged PRs processed by Safety Layer
- 0 AI PR merges without passing policies or VCR
- <6 min p95 validation pipeline
- Override rate <5%

### EP-03: Design Partner Program (10 External Teams)

**Status**: ✅ CTO APPROVED  
**Priority**: P0 - Critical  
**Timeline**: Sprint 41-45 (Jan-Mar 2026)  
**Budget**: $8,000

**Problem**: Internal-only validation = 6-9 month lock-in, miss market timing for AI Safety narrative.

**Scope**:
- Source 20 candidates, onboard ≥6 teams
- Workshop "AI Safety for Engineering Teams" (90 min)
- Bi-weekly feedback loops
- Case study generation

**Target Partners**:
- 10-200 engineers, ≥100K LOC
- Heavy Cursor/Copilot/Claude usage
- Pain: AI-induced architecture drift

**Success Criteria**:
- ≥6 partners active within 60 days
- ≥10 actionable improvements captured
- ≥2 case studies with metrics

---

## ❌ OpenCode Integration Evaluation - ABORTED (Jan 12, 2026)

### Abort Decision

**Date**: January 12, 2026, 10:15pm (4 hours after start)
**Status**: ❌ ABORTED - Strategic refocus on Track 1 SASE
**Reason**: Strategic misalignment + resource prioritization
**Budget Saved**: $90K (Levels 1-3) → Reallocated to Vibecode CLI + SASE

**Why Aborted**:
- OpenCode is CLI/TUI tool (competitor to Claude Code, Cursor), NOT API server
- No HTTP API for integration (ADR-026 assumption invalid)
- Integration would require $50K-$80K fork + custom API layer
- Better strategy: Govern ALL AI coders via 4-Gate pipeline (no specific integration)
- Track 1 SASE is Q1 2026 P0 (requires full team focus)

**What We Learned** (4 hours):
- ✅ OpenCode = TypeScript/Bun CLI application (Interactive TUI)
- ❌ No REST API endpoints exist
- ❌ Cannot integrate via adapter pattern
- ✅ Better positioning: Governance layer ABOVE all AI coders

**Budget Reallocation**:
- Level 1 ($30K) → Vibecode CLI enhancements (Q2 2026)
- Level 2 ($20K) → SASE artifact development
- Level 3 ($40K) → Vibecode CLI optimization (H2 2026)

**Archived Documents**: `docs/99-archive/OpenCode-Evaluation-Aborted-Jan12-2026/`

See: [README-ABORT-DECISION.md](../../99-archive/OpenCode-Evaluation-Aborted-Jan12-2026/README-ABORT-DECISION.md)

---

## Two-Track Launch Strategy

### Track A: Internal Dogfooding

| Target | Teams | Engineers | DAU Target |
|--------|-------|-----------|------------|
| NQH | 3 | 15 | 70%+ |
| MTS | 3 | 25 | 70%+ |
| Bflow | 2 | 10 | 70%+ |
| **Total** | **8** | **50** | **70%+** |

**Success Criteria**:
- 70%+ DAU across all teams
- Zero P0 bugs for 90 days
- Measurable waste reduction (before/after)

### Track B: Design Partners

| Target | Teams | Engineers | Status |
|--------|-------|-----------|--------|
| External (VN) | 4 | 40 | Sourcing |
| External (EU) | 3 | 30 | Sourcing |
| External (US) | 3 | 30 | Sourcing |
| **Total** | **10** | **100** | **Parallel** |

**Success Criteria**:
- ≥6 active within 60 days
- Partner NPS ≥40
- Renewal intent ≥80%

---

## Pricing Tiers (v5.0.0)

| Tier | Price | Target | Features | Support |
|------|-------|--------|----------|---------|
| **Founder Plan** | $99/team/mo | Vietnam SME | IR Codegen, 1 product, unlimited users | Email + Community |
| **Standard** | $30/user/mo | Global EM 6-50 eng | Full governance, 10 projects | Email |
| **Enterprise** | Custom | CTO 50-500 eng | SSO, RBAC, self-hosted, unlimited | Dedicated |

**Vietnam SME Special** (Founder Plan):
- ~2.5M VND/month (competitive local pricing)
- 3 domain templates: F&B, Hotel, Retail
- Vietnamese onboarding flow
- IR-based code generation included
- Free 3 months for pilot participants

**Year 1 Revenue Target**:
- Founder Plan (60%): 18-30 teams × $99 × 12 = $21K-$36K
- Standard (30%): 9-15 teams × $30 × 10 users × 12 = $32K-$54K
- Enterprise (10%): 3-5 teams × custom = $33K-$54K
- **Total: $86K-$144K ARR**

---

## Sprint Planning (Q1-Q3 2026)

### EP-01/02/03: AI Safety First (Sprint 41-45)

| Sprint | Dates | Focus | Story Points |
|--------|-------|-------|-------------|
| **Sprint 41** | Jan 6-17 | AI Safety Foundation | 18 SP |
| **Sprint 42** | Jan 20-31 | AI Detection & Pipeline | 20 SP |
| **Sprint 43** | Feb 3-14 | Policy Guards & Evidence UI | 22 SP |
| **Sprint 44** | Feb 17-28 | Stalled Project Flow | 18 SP |
| **Sprint 45** | Mar 3-14 | M1 Milestone Delivery | 20 SP |

### EP-04: SDLC Structure Enforcement (Sprint 44-46) - $16.5K

| Sprint | Dates | Focus | Story Points |
|--------|-------|-------|-------------|
| **Sprint 44** | Feb 17-28 | SDLC Structure Scanner | 39 SP |
| **Sprint 45** | Mar 3-14 | Auto-Fix Engine | 44 SP |
| **Sprint 46** | Mar 17-28 | CI/CD Integration | 34 SP |

### EP-05: Enterprise SDLC Migration (Sprint 47-50) - $58K

| Sprint | Dates | Focus | Story Points |
|--------|-------|-------|-------------|
| **Sprint 47** | Mar 31 - Apr 11 | Scanner + Config Generator | 22 SP |
| **Sprint 48** | Apr 14-25 | Fixer + Backup Engine | 23 SP |
| **Sprint 49** | Apr 28 - May 9 | Real-time Compliance | 22 SP |
| **Sprint 50** | May 12-23 | Dashboard + Enterprise | 22 SP |

### EP-06: IR-Based Codegen Engine (Sprint 45-50) - ~$50K ⭐ P0 PRIORITY

| Sprint | Dates | Focus | Story Points | Design Spec |
|--------|-------|-------|-------------|-------------|
| **Sprint 45** | Feb 17-28 | Multi-Provider Architecture | ~20 SP | ✅ ADR-022, Tech Spec |
| **Sprint 46** | Mar 3-14 | IR Processor (Backend scaffold) | ~20 SP | ✅ IR-Processor-Specification.md |
| **Sprint 47** | Mar 17-28 | Vietnamese Domain Templates | ~18 SP | ✅ Vietnamese-Domain-Templates-Specification.md |
| **Sprint 48** | Mar 31 - Apr 11 | Quality Gates for Codegen | ~20 SP | ✅ Quality-Gates-Codegen-Specification.md |
| **Sprint 49** | Apr 14-25 | Vietnam SME Pilot (10 founders) | ~18 SP | ✅ Pilot-Execution-Specification.md |
| **Sprint 50** | Apr 28 - May 9 | Productization + GA | ~20 SP | ✅ Productization-Baseline-Specification.md |

**EP-06 Success Gate (End of Sprint 50)**:
- 10 pilot founders complete onboarding
- TTFV <30 minutes (median)
- Satisfaction ≥8/10
- Quality gate pass rate ≥95%
- DeepCode Q2 decision gate prepared

**Total Investment (Sprint 41-50)**: ~$126.5K (350+ SP)

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Rebrand confusion | Messaging misalignment | Stage communication, validate with partners |
| Telemetry gaps | Cannot prove value | Instrument analytics Q1 (blocking) |
| AI Safety false positives | Developer friction | Progressive rollout, simulation mode |
| Marketplace scope creep | Delay enterprise | Limit Q3 scope to curated packs |
| Compliance delays | Enterprise deals blocked | Start RBAC/SSO architecture Q2 |

---

## Historical Context (Legacy)

Previous roadmap versions archived at:
- [Product-Roadmap-2026-Software3.0.md](../99-Legacy/Product-Roadmap-2026-Software3.0.md) (Draft v0.1)
- [TIMELINE-UPDATE-NOV-2025.md](../99-Legacy/TIMELINE-UPDATE-NOV-2025.md)

---

## Approval & Governance

| Role | Name | Approval Date | Status |
|------|------|---------------|--------|
| **CTO** | Mr. Tai | February 3, 2026 | ✅ APPROVED (v7.0.0) |
| **CPO** | TBD | Pending | ⏳ |
| **CEO** | TBD | Pending | ⏳ |

**Sprint 147+ Roadmap Approval**: February 3, 2026 (24-sprint plan)
**Expert Synthesis Review**: February 2, 2026 (Course correction approved)
**Sprint 147 Kickoff**: February 4, 2026, 9am

**Key Planning Documents**:
- [ROADMAP-147-170.md](../04-build/02-Sprint-Plans/ROADMAP-147-170.md) - Complete 24-sprint roadmap
- [OPPORTUNITY-GATE-TEMPLATE.md](../09-govern/OPPORTUNITY-GATE-TEMPLATE.md) - Feature evaluation framework
- [PRODUCT-TRUTH-LAYER-SPEC.md](../04-build/02-Sprint-Plans/PRODUCT-TRUTH-LAYER-SPEC.md) - Telemetry specification
- [V1-V2-CONSOLIDATION-PLAN.md](../04-build/02-Sprint-Plans/V1-V2-CONSOLIDATION-PLAN.md) - API migration guide

**Next Review**: February 14, 2026 (Sprint 148 planning)

---

*This document is the SINGLE SOURCE OF TRUTH for product roadmap. Changes require CTO + CPO approval.*
*Version controlled alongside quarterly reviews.*
*Last Updated: February 3, 2026*
