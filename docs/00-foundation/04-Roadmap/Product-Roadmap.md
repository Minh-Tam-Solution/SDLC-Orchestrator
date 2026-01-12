# Product Roadmap
## Operating System for Software 3.0

**Version**: 5.0.0
**Date**: December 23, 2025
**Status**: ✅ CTO APPROVED - Software 3.0 Pivot + EP-06 P0
**Authority**: CTO Approval (Dec 23, 2025), Board Decision December 2024
**Foundation**: Financial Model v1.0, Product Vision v4.0.0
**Framework**: SDLC 5.1.1 + SASE Level 2

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

## Current Status (December 2025)

### Sprint 40 Complete ✅

| Phase | Status | Gate |
|-------|--------|------|
| **Foundation** (Nov 2025) | ✅ COMPLETE | G0.1 ✅, G0.2 ✅ |
| **Planning** (Nov 2025) | ✅ COMPLETE | G1 ✅ (Legal + Market) |
| **Design** (Nov-Dec 2025) | ✅ COMPLETE | G2 ✅ (Architecture 9.4/10) |
| **Build** (Dec 2025) | ✅ Sprint 33-40 COMPLETE | Beta Pilot Live |
| **Beta Pilot** (Dec 2025) | ✅ 5 teams, 38 users | Production Stable |

### Platform Capabilities (Delivered)

- ✅ **Backend API**: 35+ endpoints (FastAPI, PostgreSQL, Redis)
- ✅ **Frontend**: React Dashboard, shadcn/ui, Admin Panel
- ✅ **Authentication**: JWT + OAuth (GitHub), MFA support
- ✅ **Gate Engine**: OPA integration, YAML → Rego policies
- ✅ **Evidence Vault**: MinIO S3, SHA256 hashing
- ✅ **AI Council**: Ollama + Claude integration
- ✅ **VS Code Extension**: AI-assisted development
- ✅ **CLI Tool**: sdlcctl validate

---

## 2026 Roadmap Overview

### Milestone Map

| Milestone | Date | Key Outcomes |
|-----------|------|--------------|
| **M1** | March 2026 | AI-Intent Flows live (≥70% adoption), AI Safety Layer v1 protecting AI PRs |
| **M2** | June 2026 | 10 Design Partners active, ≥10 improvements shipped, ≥2 case studies |
| **M3** | September 2026 | Marketplace beta, GitLab integration GA, telemetry complete |
| **M4** | December 2026 | Enterprise bundle GA, compliance reports, self-hosted pilot |
| **M5** | 2027 | 10K+ teams, Gartner inclusion, industry reference architectures |

### Quarterly Phases

| Quarter | Theme | Primary Epics | Investment |
|---------|-------|---------------|------------|
| **Q1 2026** | **EP-06 Codegen P0** | Sprint 45-50 (IR Codegen + Pilot) | ~$50,000 |
| **Q1 2026** | **Track 1 SASE** | SDLC 5.1.0 Framework Enhancement | $0 (internal) |
| **Q1-Q2 2026** | AI Safety | EP-01, EP-02, EP-03 | $60,000 |
| **Q2 2026** | Structure Enforcement | EP-04 (Sprint 41-46) | $16,500 |
| **Q2 2026** | **Vibecode CLI** | IR-based codegen enhancements | $30,000 (reallocated) |
| **Q3 2026** | Multi-VCS + Marketplace | EP-07, EP-08 | $80,000 |
| **Q4 2026** | Enterprise Governance | EP-09, EP-10 | $100,000 |
| **2027** | Scale to 150-300 teams | EP-11+ | TBD |

**Note**:
- EP-05 (Enterprise Migration) deprioritized until EP-06 success validated.
- OpenCode evaluation ABORTED (Jan 12, 2026) - $90K budget reallocated to Vibecode CLI.

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
| **CTO** | Mr. Tai | December 23, 2025 | ✅ APPROVED (v5.0.0) |
| **CPO** | TBD | Pending | ⏳ |
| **CEO** | TBD | Pending | ⏳ |

**EP-06 Design Approval**: December 23, 2025 (Sprint 45-50 specs committed)
**Session Log**: [SESSION-2025-12-23-Stage00-Foundation-Update.md](../../01-planning/99-Session-Logs/SESSION-2025-12-23-Stage00-Foundation-Update.md)
**Next Review**: December 27, 2025 (CTO Review Meeting, 3pm)
**Sprint 45 Kickoff**: February 17, 2026, 9am

---

*This document is the SINGLE SOURCE OF TRUTH for product roadmap. Changes require CTO + CPO approval.*
*Version controlled alongside quarterly reviews.*
