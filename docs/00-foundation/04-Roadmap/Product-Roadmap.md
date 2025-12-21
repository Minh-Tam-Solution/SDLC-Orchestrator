# Product Roadmap
## AI-Native SDLC Governance & Safety Platform

**Version**: 4.1.0
**Date**: December 21, 2025
**Status**: ✅ CTO APPROVED - Q1-Q2 2026 AI Safety First + EP-04/05/06
**Authority**: CTO Approval (Dec 21, 2025), Board Decision December 2024
**Foundation**: Financial Model v1.0, Product Vision v3.1.0
**Framework**: SDLC 5.1.1 + SASE Level 2

**Changelog v4.1.0** (Dec 21, 2025):
- **EP-04**: SDLC Structure Enforcement (Sprint 41-46, $16.5K, 117 SP)
- **EP-05**: Enterprise SDLC Migration Engine (Sprint 47-50, $58K, 89 SP)
- **EP-06**: Codegen Engine Tri-Mode (Sprint 51-55, ~$50K, 99 SP)
- **Mode C Hybrid Fallback**: Claude → Continue.dev auto-failover
- **Model Roles Strategy**: IT Admin 10-model structure integrated
- **NQH AI Platform**: qwen2.5-coder:32b (92.7% HumanEval) ready
- **.sdlc-config.json**: 1KB replaces 700KB manual compliance docs
- **Total Investment**: $74.5K+ committed (305+ SP)
- **Revenue Projection**: +$34.5K ARR Year 1 from new epics

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

### New Positioning (v4.0.0)

> **Product Category**: AI-Native SDLC Governance & Safety Platform  
> **Tagline**: *"The control plane that keeps Claude Code/Cursor/Copilot compliant with your architecture & standards."*

**Core Value Proposition**:
- AI coding tools (Cursor, Copilot, Claude Code) increase throughput but create governance gaps
- SDLC Orchestrator is the **governance and safety layer** that certifies AI-generated code before production
- Differentiation: AI Council pattern + Policy-as-Code + Evidence Vault + SDLC 5.x expertise

### 2026 Strategic Themes

| Theme | Description | Success Metric |
|-------|-------------|----------------|
| **AI-Intent-First Adoption** | Orchestrator = entry point for ideas & projects | ≥70% internal PM/EM use weekly |
| **AI Safety & Governance** | Every AI change validated before merge | 0 unreviewed AI PRs merged |
| **Ecosystem & Enterprise** | Marketplace + SSO + Self-hosted | ≥5 external policy contributors |

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
| **Q1-Q2 2026** | AI Safety First | EP-01, EP-02, EP-03 | $60,000 |
| **Q1-Q2 2026** | Structure & Migration | EP-04, EP-05 | $74,500 |
| **Q2-Q3 2026** | Codegen Engine | EP-06 | ~$50,000 |
| **Q3 2026** | Ecosystem & Marketplace | EP-07, EP-08 | $80,000 |
| **Q4 2026** | Enterprise Governance | EP-09, EP-10 | $100,000 |
| **2027** | Become the Standard | EP-11+ | TBD |

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

## Pricing Tiers (v4.0.0)

| Tier | Price | Projects | Policies | AI Safety | Support |
|------|-------|----------|----------|-----------|---------|
| **Free** | $0 | 1 | 5 rules | 2 devs max | Community |
| **Team** | $149/mo | 10 | Unlimited | Full validators | Email |
| **Enterprise** | $500+/mo | Unlimited | Custom | SSO + RBAC | Dedicated |

**Design Partner Offer**:
- 6-9 months free or symbolic pricing
- Grandfathered pricing at GA
- Dedicated support channel

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

### EP-06: Codegen Engine Tri-Mode (Sprint 51-55) - ~$50K

| Sprint | Dates | Focus | Story Points |
|--------|-------|-------|-------------|
| **Sprint 51** | May 26 - Jun 6 | IR v0 Schemas + Codegen API | ~20 SP |
| **Sprint 52** | Jun 9-20 | Mode B: qwen2.5-coder:32b | ~20 SP |
| **Sprint 53** | Jun 23 - Jul 4 | Mode A: BYO Integration | ~20 SP |
| **Sprint 54** | Jul 7-18 | Mode C: Hybrid Fallback | ~20 SP |
| **Sprint 55** | Jul 21 - Aug 1 | Non-Tech Journey + Polish | ~19 SP |

**Total Investment (Sprint 41-55)**: $184.5K (459+ SP)

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
| **CTO** | Mr. Tai | December 21, 2025 | ✅ APPROVED (v4.1.0) |
| **CPO** | TBD | Pending | ⏳ |
| **CEO** | TBD | Pending | ⏳ |

**Session Log**: [SESSION-2025-12-21-CTO-Strategic-Planning.md](../../01-planning/99-Session-Logs/SESSION-2025-12-21-CTO-Strategic-Planning.md)
**Next Review**: December 27, 2025 (CTO Review Meeting, 3pm)
**Sprint 41 Kickoff**: January 6, 2026, 9am

---

*This document is the SINGLE SOURCE OF TRUTH for product roadmap. Changes require CTO + CPO approval.*
*Version controlled alongside quarterly reviews.*
