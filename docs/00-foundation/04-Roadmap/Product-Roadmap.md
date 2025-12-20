# Product Roadmap
## AI-Native SDLC Governance & Safety Platform

**Version**: 4.0.0
**Date**: December 20, 2025
**Status**: ✅ CTO APPROVED - Q1-Q2 2026 AI Safety First
**Authority**: CTO Approval (Dec 20, 2025), Board Decision December 2024
**Foundation**: Financial Model v1.0, Product Vision v3.0.0
**Framework**: SDLC 5.1.1 + SASE Level 2

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
| **Q3 2026** | Ecosystem & Marketplace | EP-04, EP-05 | $80,000 |
| **Q4 2026** | Enterprise Governance | EP-06, EP-07, EP-08 | $100,000 |
| **2027** | Become the Standard | EP-09, EP-10 | TBD |

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

## Sprint Planning (Q1 2026)

| Sprint | Dates | Focus | Status |
|--------|-------|-------|--------|
| **Sprint 41** | Jan 6-17 | AI Safety Foundation | [PLANNED](../../../04-build/02-Sprint-Plans/SPRINT-41-AI-SAFETY-FOUNDATION.md) |
| **Sprint 42** | Jan 20-31 | AI Detection & Pipeline | [PLANNED](../../../04-build/02-Sprint-Plans/SPRINT-42-AI-DETECTION-PIPELINE.md) |
| **Sprint 43** | Feb 3-14 | Policy Guards & Evidence UI | [PLANNED](../../../04-build/02-Sprint-Plans/SPRINT-43-POLICY-GUARDS-EVIDENCE-UI.md) |
| **Sprint 44** | Feb 17-28 | Stalled Project Flow | Planning |
| **Sprint 45** | Mar 3-14 | M1 Milestone Delivery | Planning |

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
| **CTO** | Mr. Tai | December 20, 2025 | ✅ APPROVED |
| **CPO** | TBD | Pending | ⏳ |
| **CEO** | TBD | Pending | ⏳ |

**Next Review**: January 15, 2026 (Sprint 41 Mid-Point)

---

*This document is the SINGLE SOURCE OF TRUTH for product roadmap. Changes require CTO + CPO approval.*
*Version controlled alongside quarterly reviews.*
