# SDLC Orchestrator - Business Requirements Document (BRD)
## WHY We Need This Solution — Problem Validation, Two-Product Strategy, Enterprise-First

**Version**: 4.0.0
**Date**: February 21, 2026
**Status**: ACTIVE - STAGE 00 FOUNDATION (Chat-First Governance + Enterprise-First)
**Authority**: CEO + CPO Approved
**Foundation**: Market-Sizing v4.0.0, Financial Model v2.0.0, ADR-059, ADR-064
**Stage**: Stage 00 (WHY) — Project Foundation
**Framework**: SDLC 6.1.0 (7-Pillar + AI Governance Principles + 12-Role System)

**Changelog v4.0.0** (Feb 21, 2026) — Chat-First Governance Loop:
- **CHAT-FIRST UX PIVOT**: EP-08 + ADR-064 approved — Chat is the primary interface, Control Plane is truth
- **NEW UX PROBLEM**: 35+ dashboard pages slower than manual AI + SDLC Framework docs; CEO liberation blocked
- **NORTH STAR LOOP**: `@mention → Gate Actions → Evidence → Approve (Magic Link) → Audit Export`
- **SPRINT 189-192**: Chat Governance Loop roadmap (Router, Magic Link, Cleanup, Enterprise Hardening)
- **CODEBASE CLEANUP**: Sprint 190 deletes ~18.3K LOC (28% frontend) — dead pages, unused components
- **OPTION D+**: Chat-First Facade (~500 LOC new) over existing enterprise Control Plane
- **BR6 ADDED**: Platform UX — Chat-First Governance as new business requirement
- **11 CTO CONDITIONS**: T-01..T-09 + A-01..A-04 locked in ADR-064

**Changelog v3.0.0** (Feb 19, 2026) — Enterprise-First Refocus:
- **TWO-PRODUCT STRATEGY**: TinySDLC OSS (community/individual) + Orchestrator (commercial/enterprise)
- **REVISED ICP**: Primary ICP shifts to 15-50 engineers ($299-$499/mo) — was 6-50 at $99-$299
- **NEW TIER MODEL**: LITE free / STD_STARTER $99 / STD_GROWTH $299 / PROFESSIONAL $499 / ENTERPRISE $80/seat / FOUNDER_LEGACY (grandfathered)
- **REVISED YEAR 1 TARGET**: $160K-$350K ARR (45-70 teams) — was $86K-$144K
- **REVISED UNIT ECONOMICS**: LTV:CAC 6.6:1 (was 3:1-7:1), CAC $4,000, LTV $26,400, Gross Margin 78%
- **FOUNDER LEGACY**: FOUNDER Plan grandfathered forever at $399/mo — no new sales after Sprint 181
- **14-DAY TRIAL**: PROFESSIONAL trial auto-activates on LITE signup (no credit card)
- **PROFESSIONAL SERVICES**: New revenue stream, $3K-$10K packages (30% Year 1 mix in Vietnam)
- **CPO BM-01 to BM-10**: All 10 business model decisions incorporated

**Changelog v2.0.0** (Dec 23, 2025) — Software 3.0 Pivot:
- **SOFTWARE 3.0 PIVOT**: Operating System for Software 3.0 positioning
- **EP-06 P0**: IR-Based Codegen (Sprint 45-50) as top priority
- **Founder Plan**: $99/team/month for Vietnam SME
- **Year 1 Target**: 30-50 teams (realistic, founder-led sales)
- **Dual Wedge Strategy**: Vietnam SME (40%) + Global EM (40%) + Enterprise (20%)

**Changelog v1.2.0** (Dec 21, 2025):
- Updated framework to SDLC 5.1.3; added EP-04/05/06 strategic extensions
- Added NQH AI Platform integration; updated competitive moat with AI Safety positioning

---

## 🎯 Document Purpose

This Business Requirements Document (BRD) answers **WHY** we are building SDLC Orchestrator by validating the business problem, opportunity, and two-product ecosystem strategy.

**Stage 00 Focus (WHY)**:
- ✅ Problem validation with evidence
- ✅ Target market & personas (WHO suffers from this problem)
- ✅ Two-product ecosystem model (HOW we address different market segments)
- ✅ Business opportunity & value proposition
- ✅ Revenue model, pricing tiers, unit economics
- ✅ Success criteria & constraints

**Out of Scope** (Stage 01+): Detailed functional requirements, API specs, data models, technical implementation.

---

## 📊 Executive Summary

### The Problem (Validated)

**Engineering teams waste 60-70% of effort building features users don't need.**

**Evidence**:
- **Bflow Platform**: Only 32% feature adoption (68% wasted effort)
- **Pendo 2024 Report**: 70% of features rarely/never used across 10,000+ products
- **User Interviews**: 10+ Engineering Managers confirmed pain point
- **Financial Impact**: $100K team salary = $60-70K/year wasted on wrong features

**Root Causes** (identified through user research):
1. **No validation gates**: Teams skip user validation, build features on assumptions
2. **No evidence trail**: PM says "users want it" but has no proof
3. **Process fatigue**: Too many tools (Jira, Confluence, Slack, Docs), nothing enforced
4. **Audit chaos**: Manual evidence gathering (40-80 hours) for SOC 2/ISO compliance
5. **No AI governance**: AI-generated code (Cursor, Copilot, Claude Code) has no quality gates

### The Two-Product Strategy (CPO, Feb 19, 2026)

**Problem with original single-product approach**:
> "SDLC Orchestrator attempts to serve ALL tiers (LITE → ENTERPRISE) simultaneously, resulting in 38% of features orphaned or ungated, unclear product identity, and inability to articulate a differentiated enterprise value proposition."

**Solution — Two-Product Ecosystem**:

```
┌──────────────────────────┐          ┌──────────────────────────────┐
│       TinySDLC           │          │     SDLC Orchestrator        │
│    (OSS Community)       │          │   (Commercial Enterprise)    │
│                          │          │                              │
│ License: MIT / Apache    │   10%    │ License: Apache-2.0 (prop.)  │
│ Price:   Free forever    │ convert  │ Price: $99-$499/mo + custom  │
│ Deploy:  Local / self    │ ────────>│ Deploy: Cloud-hosted         │
│ Target:  Individual dev  │          │ Target: 15+ dev teams        │
│ OTT:     Telegram/Zalo   │          │ OTT:   Telegram/Teams/Slack  │
│ Agents:  8 SDLC agents   │          │ Agents: 8 + Multi-Agent EP-07│
│ Revenue: $0 direct       │          │ Revenue: SaaS + PS           │
│ Purpose: Community moat  │          │ Purpose: Revenue engine      │
└──────────────────────────┘          └──────────────────────────────┘
         │                                         │
         └─────── SDLC 6.1.0 Framework ───────────┘
                  (shared methodology)
```

**Key clarification** (ADR-059 INV-01 — INVARIANT):
> "TinySDLC ≠ Orchestrator LITE. TinySDLC is a separate product (local, OSS). Orchestrator LITE is a free cloud tier in the commercial product — the entry point to the commercial conversion funnel, not the same as TinySDLC."

### The Opportunity (Enterprise-First)

| Market | TAM | SAM | SOM Year 1 | Strategy |
|--------|-----|-----|------------|----------|
| TinySDLC (OSS community) | 1.2M devs | — | 1,000+ installs | Community moat |
| Orchestrator (commercial) | $1.44B ARR | 420K teams | 45-70 teams | Revenue engine |
| **Total** | — | — | **$160K-$350K ARR** | **Two-product ecosystem** |

**Why Now (Feb 2026)**:
- AI coding tools (Cursor, Claude Code, Copilot) now 73% enterprise adoption
- 67% of teams have NO governance for AI-generated code
- TinySDLC OSS creates community entry point NOW (before competitors)
- SDLC 6.1.0 framework is validated (Sprints 176-179 multi-agent complete)

---

## 👥 Target Market & Personas (Revised v3.0.0)

### Market Segmentation — Enterprise-First

**Primary Market (ICP — Orchestrator commercial)**:
- **Company size**: 50-500 employees
- **Engineering team**: 15-50 engineers
- **Industry**: SaaS, B2B software, cloud-native, fintech, healthcare (compliance-driven)
- **Geography**: Vietnam (Year 1 pilot), English-speaking markets (US, UK, Australia — Year 1-2)
- **Tech stack**: Modern (React, Node.js, Python, Docker, Kubernetes, GitHub)
- **Compliance**: SOC 2, ISO 27001 required or upcoming
- **Tier**: Orchestrator STANDARD Growth ($299) or PROFESSIONAL ($499)

**Secondary Market (Enterprise)**:
- Enterprise (500+ employees, 50-300 engineers) at $499-custom
- Regulated industries (Healthcare/HIPAA, Fintech) — requires SSO (Sprint 182+)

**Community Market (TinySDLC OSS)**:
- Individual developers, teams ≤3 members
- SDLC methodology adopters (local, free, self-hosted)
- Conversion pipeline to Orchestrator LITE

**Excluded from Orchestrator commercial Year 1**:
- Teams <15 engineers: TinySDLC OSS is the right product
- Startups <6 engineers: TinySDLC or free tier only
- Non-English markets (except Vietnam): Year 2+

### Primary Personas (Revised)

#### Persona 1: Engineering Manager — Enterprise-First ICP (60% of ARR)

**Demographics**:
- Role: Engineering Manager, VP Engineering
- Team size: **15-50 engineers** (revised from 6-50)
- Company Stage: **Series B-C** (revised from Series A-C)
- Reports to: CTO or CEO
- Budget authority: $30K-$200K/year
- Decision timeline: 2-4 weeks

**Pain Points** (validated):
1. **Feature waste**: "We built the commenting system. 2% used it. 3 sprints wasted."
2. **AI code governance**: "Engineers use Claude Code/Cursor. No one audits what AI generates."
3. **Compliance overhead**: "SOC 2 = 3 engineers × 2 weeks scrambling for screenshots."
4. **Process overhead**: "8 tools (Jira, Confluence, Slack). Nothing enforced."
5. **Multi-agent coordination**: "We run 3 AI agents. How do I know they don't conflict?"

**Goals**:
- Increase feature adoption from 30% to 70%+
- Govern AI-generated code (audit trail, quality gates)
- Pass SOC 2/ISO audits without manual evidence gathering
- Coordinate AI agent teams (Multi-Agent Engine EP-07)

**Buying Criteria**:
- ROI: Must save 20+ engineering hours/month (>$5K/month value)
- Ease of adoption: <2 weeks to onboard team
- Developer-friendly: Minimal workflow disruption
- Pricing: **$299-$499/month** acceptable (revised from $99-$999)

**Willingness to Pay**: **$299-$499/month** (STANDARD Growth or PROFESSIONAL)

**Quote**:
> "If you can stop my team from wasting 60% of our effort on features users don't want, AND audit my AI-generated code, I'll pay $500/month TODAY."
> — Engineering Manager, 25-person SaaS company, Series B

---

#### Persona 2: CTO — Enterprise Target (30% of ARR)

**Demographics**:
- Role: CTO, VP Engineering (50+ engineers)
- Company size: 100-2,000 employees
- Budget authority: $100K-$500K/year
- Decision timeline: 4-12 weeks (enterprise procurement cycle)

**Pain Points**:
1. **Compliance overhead**: "SOC 2 audit = $50K auditor + 200 hours internal."
2. **AI governance at scale**: "50 engineers use AI coders. Zero visibility on what's generated."
3. **Lack of visibility**: "10 teams, 30 projects. No idea which are on track."
4. **Process inconsistency**: "Each team has own 'process.' No standards."
5. **SSO + compliance**: "We can't use any tool without SAML SSO + NIST alignment."

**Goals**:
- Standardize SDLC across 10+ teams
- Govern AI agent output (EP-07 Multi-Agent Engine)
- Automated evidence for compliance (SOC 2, HIPAA, NIST AI RMF)
- Enterprise SSO (SAML, Azure AD) — Sprint 182 blocker
- Real-time project health visibility

**Buying Criteria**:
- Enterprise features: SSO (SAML/Azure AD), RBAC, white-label
- Compliance: SOC 2 Type II, HIPAA evidence vault, NIST AI RMF
- Scalability: Support 50-300 engineers
- **Pricing**: PROFESSIONAL $499 → ENTERPRISE $80/seat

---

#### Persona 3: Vietnam Founding Customer — PROFESSIONAL Legacy (5 teams)

**Demographics**:
- Role: CTO or Founder-CTO
- Company: Vietnamese tech company, 15-30 engineers
- Commitment: **PROFESSIONAL $399/mo** (grandfathered forever — CPO BM-04)
- Value: Case study, referral source, product feedback partner

**Context**:
- 5 founding customers locked at $399/mo PROFESSIONAL for life (non-negotiable retention)
- Total value: 5 × $399 × 12 = $23,940 ARR
- Strategic value: Vietnamese market proof point, referrals → additional Vietnam enterprise deals

---

### Anti-ICP (Who We DON'T Target via Orchestrator)

**Teams ≤14 Engineers**:
- **Why Not**: TinySDLC OSS is the right product for them (free, local, simple)
- **Exception**: If compliance pain exists (SOC 2 upcoming) → STANDARD Starter $99 acceptable
- **Strategy**: Direct to TinySDLC → they upgrade to Orchestrator when team grows to 15+

**Individual Developers**:
- **Why Not**: TinySDLC territory — don't pay for governance tooling
- **Strategy**: Install TinySDLC → contribute to community → convert when joining/building a team

**Regulated Industries before Sprint 182** (Finance, Healthcare):
- **Why Not**: SSO is required (SAML/Azure AD) — Sprint 182 delivery date
- **Strategy**: PROFESSIONAL trial in Q1 2026; full ENTERPRISE close after SSO GA (Q2 2026)

---

## 💼 Business Requirements (Updated v3.0.0)

### BR1: Problem-Solution Fit

**Requirement**: SDLC Orchestrator must solve the validated problem of 60-70% feature waste AND AI code governance.

**Success Criteria**:
- ✅ Problem validated with 10+ external users
- ✅ Solution addresses root causes (no validation, no evidence, no AI governance)
- ✅ Competitive differentiation clear (SDLC 6.1.0 + Multi-Agent EP-07 + OSS moat)
- ✅ Value proposition quantified (save $60-70K/year per $100K team)

**Status**: ✅ VALIDATED (Stage 00 Gate G0.1)

---

### BR2: Market Opportunity (Revised — Enterprise-First)

**Requirement**: Orchestrator must target the enterprise segment where TinySDLC cannot serve.

**Success Criteria**:
- ✅ Orchestrator TAM >$500M (actual: $1.44B)
- ✅ Orchestrator SAM targeting 420K teams (15+ engineer cloud teams)
- ✅ SOM Year 1 achievable at $160K-$350K ARR (45-70 teams, enterprise-first)
- ✅ ICP revised: Engineering Manager 15-50 engineers at $299-$499 (CPO confirmed)
- ✅ TinySDLC OSS creates 10% conversion funnel to Orchestrator

**Market Trends** (supporting enterprise-first):
- AI-native tools: 73% enterprise adoption (GitHub Copilot, Cursor, Claude Code)
- Compliance: SOC 2 + NIST AI RMF now required (EU AI Act, enterprise procurement)
- Multi-agent governance: New category; EP-07 is first-to-market solution
- OSS community: TinySDLC → enterprise conversion follows HashiCorp playbook

**Status**: ✅ VALIDATED (CPO G0.2 approval, Feb 19, 2026)

---

### BR3: Revenue Model (Updated — CPO BM-01 through BM-10)

**Revenue Streams (CPO Decision BM-01)**:

| Stream | Year 1 % | Description |
|--------|----------|-------------|
| SaaS Subscription | 70% | Recurring tier-based licensing (LITE free → ENTERPRISE custom) |
| Professional Services | 30% | Onboarding, compliance consulting, custom policy packs |
| Integration Marketplace | 0% (Q3 2026+) | Revenue share on certified integrations (Jira, Slack, Azure) |

**Pricing Model (v3.0.0 — 6 billing plans)**:

| Plan Name | SKU | Price/mo (USD) | Price/mo (VND) | Tier | Target |
|-----------|-----|----------------|----------------|------|--------|
| **Free** | `lite_free` | $0 | — | LITE | Individual dev, evaluation, 14-day trial funnel |
| **Starter** | `std_starter` | $99 | ~2.5M VND | STANDARD | Small team 2-5 devs, full gates |
| **Growth** | `std_growth` | $299 | ~7.5M VND | STANDARD | Growing team 5-15 devs, Telegram OTT |
| **Professional** | `professional` | $499 | ~12.5M VND | PROFESSIONAL | 15-30 devs, compliance, multi-agent, all OTT |
| **Enterprise** | `ent_custom` | $80/seat (min $2K) | Custom | ENTERPRISE | 50+ devs, SSO + NIST + SLA |
| **FOUNDER** | `founder_legacy` | $399 | ~10M VND | PROFESSIONAL | **5 founding customers ONLY — legacy, no new sales** |

> **BM-02**: PROFESSIONAL $499 (down from $599) for Vietnam purchasing power (~VND 12.5M/mo confirmed).
> **BM-03**: ENTERPRISE $80/seat, minimum 25-seat floor = $2,000/mo minimum contract.
> **BM-04**: FOUNDER grandfathered at $399/mo for life — retention decision, non-negotiable. No new FOUNDER signups after Sprint 181.
> **BM-05**: 14-day PROFESSIONAL trial auto-activates on every LITE signup (no credit card required). Day 12: nudge. Day 14: auto-downgrade to LITE.

**Tier vs Billing Plan Separation** (ADR-059 INV-02 — INVARIANT):

```
project.tier_level  = feature entitlements (LITE / STANDARD / PROFESSIONAL / ENTERPRISE)
subscription.plan   = billing SKU (lite_free / std_starter / std_growth / professional / ent_custom / founder_legacy)

Invariant mapping (one-way only):
  lite_free       → LITE
  std_starter     → STANDARD
  std_growth      → STANDARD
  professional    → PROFESSIONAL
  ent_custom      → ENTERPRISE
  founder_legacy  → PROFESSIONAL (grandfathered at $399, same features as professional)
```

**Revenue Projections (Revised)**:

| Year | Teams | ARR | Notes |
|------|-------|-----|-------|
| Year 1 | 45-70 | $160K-$350K | Vietnam pilots + early enterprise, founder-led |
| Year 2 | 120-200 | $600K-$1.2M | Enterprise land-and-expand; SSO GA; compliance upsell |
| Year 3 | 300-500 | $1.8M-$3.6M | Multi-region; international enterprise; marketplace revenue |

**Unit Economics (Revised — Enterprise-First)**:

| Metric | Original (BRD v2.0.0) | Revised (BRD v3.0.0) | Delta |
|--------|----------------------|---------------------|-------|
| CAC | $2,650/team (est. $1,500 founder-led) | **$4,000/team** | +51% |
| ARPU/mo | $99-$299 avg ~$150 | **$550 (blended)** | +267% |
| LTV | $10,800 | **$26,400** | +144% |
| **LTV:CAC** | 3:1 to 7:1 | **6.6:1** | Better |
| **Gross Margin** | 72% | **78%** | +6pp (enterprise tier mix) |
| **Break-even** | Month 18 (original) | **Month 16** | -2 months |

**Professional Services Revenue (CPO Approved)**:

| Service | Price | Duration |
|---------|-------|----------|
| Onboarding + SDLC 6.1.0 Implementation | $3,000 | 2 weeks |
| Methodology Training Workshop | $1,500 | 1 day |
| Custom Policy Pack (OPA + Semgrep) | $4,000 | 1 week |
| NIST AI RMF Gap Assessment | $6,000 | 2-3 weeks |
| SOC2 Type II Evidence Vault Setup | $10,000 | 1 month |

**Status**: ✅ VALIDATED (CPO BM-01 through BM-10, Feb 19, 2026)

---

### BR4: Competitive Positioning (Updated — Two-Product Moat)

**Requirement**: Orchestrator must differentiate from existing tools AND establish an OSS community moat.

**Competitive Landscape**:

| Competitor | Category | Our Advantage |
|------------|----------|---------------|
| **Jira** | Project management | SDLC gates + evidence vault (they have none) |
| **Linear** | Issue tracking | Multi-agent engine + compliance automation |
| **GitLab** | DevOps platform | AI governance layer focused on SDLC quality |
| **Backstage** | Developer portal | Turnkey SaaS vs DIY open-source |
| **No competitor** | OSS SDLC governance community | **TinySDLC owns this category** |

**Two-Product Competitive Moat** (ADR-059 D1-D5):
1. **SDLC 6.1.0 framework** — proprietary methodology, 1-2 years to replicate
2. **TinySDLC OSS community** — nobody else owns OSS SDLC governance
3. **Multi-Agent Team Engine EP-07** — first enterprise multi-agent SDLC platform
4. **Community-to-enterprise funnel** — TinySDLC → Orchestrator conversion (HashiCorp playbook)
5. **OTT channels** (Telegram/Zalo Vietnam + Teams/Slack enterprise) — meet teams where they work

**Positioning**:
- Category: "Enterprise Governance Platform for AI-Assisted Software Teams"
- Tagline: "The Operating System for Software 3.0 — where AI teams ship quality, always"
- Differentiation: ONLY platform combining OSS community + enterprise compliance + multi-agent governance

**Status**: ✅ VALIDATED

---

### BR5: Legal & Compliance

**Requirement**: SDLC Orchestrator must comply with all legal requirements.

**Critical Requirements**:
- ✅ OSS license compliance (AGPL v3 containment for MinIO, Grafana) — RESOLVED (Dec 2025)
- ✅ Trademark protection ("SDLC Orchestrator" US filing)
- ✅ Data privacy (GDPR, CCPA compliance)
- 🔴 Enterprise SSO (SAML 2.0, Azure AD) — Sprint 182 (unblocks enterprise sales)
- 🟡 SOC 2 Type II certification — Sprint 185 target
- 🟡 HIPAA compliance — Sprint 183+ (HIPAA evidence vault)
- 🟡 NIST AI RMF alignment — Sprint 184+ (ENTERPRISE tier feature)

**Status**: Ongoing — see Sprint 182-186 roadmap in ADR-059.

---

### BR6: TinySDLC OSS Integration (NEW — v3.0.0)

**Requirement**: TinySDLC OSS must serve as the community entry point and conversion funnel to Orchestrator.

**Success Criteria**:
- 1,000+ TinySDLC GitHub stars by Q2 2026
- 10% conversion: TinySDLC users → Orchestrator LITE signups
- 25% conversion: LITE 14-day trial → STANDARD+ paid
- Clear product handoff messages in TinySDLC README

**TinySDLC Handoff Triggers**:
- Team size grows beyond 3 → "SDLC Orchestrator: cloud collaboration for growing teams"
- Compliance requirements appear → "Evidence Vault: SOC2/HIPAA ready from day 1"
- Enterprise toolchain needed (Jira/Teams/Slack) → "Orchestrator integrates natively"
- Multiple AI agents → "Multi-Agent Team Engine: govern your AI team"

**Status**: ✅ PLANNED (TinySDLC public launch Sprint 180-181)

---

## 🎯 High-Level Requirements

### What Success Looks Like

**Product Success** (North Star Metric):
- **Feature Adoption Rate**: Increase from 30% (industry baseline) to **70%+**
- **AI Code Governance Rate**: 100% of AI-generated code through quality gates

**Supporting Metrics**:

| Metric | Baseline | Year 1 Target | Measurement |
|--------|----------|---------------|-------------|
| **Time to Pass Gates** | 2-3 days (manual) | <1 day (AI-assisted) | Gate completion logs |
| **Developer NPS** | N/A | 8.0/10 | Quarterly survey |
| **Audit Prep Time** | 40-80 hours (manual) | <2 hours (automated) | Customer reports |
| **Engineering Waste** | 60-70% (validated) | <30% | Feature adoption tracking |
| **AI Agent Governance** | 0% (untracked) | 100% (all agent outputs gated) | Multi-Agent EP-07 |
| **TinySDLC → Orch conversion** | N/A | 10% | GitHub → LITE signup funnel |

---

### High-Level Functional Requirements (Updated)

#### Capability 1: Quality Gate Management
- System must enforce SDLC 6.1.0 quality gates (prevent building wrong features)
- Gates must block progress until evidence provided
- Support for custom gates (YAML-based policy packs, OPA Rego)

#### Capability 2: Evidence Vault
- System must automatically collect evidence for every gate
- Evidence must be encrypted, searchable, audit-ready (SOC 2 / HIPAA / NIST AI RMF)
- Support multiple evidence types (screenshots, PDFs, test results, approvals)
- Tier-gated storage: LITE 100MB / STANDARD 50GB / PROFESSIONAL 100GB / ENTERPRISE unlimited

#### Capability 3: AI Assistance (Multi-Provider + Multi-Agent EP-07)
- System must provide AI help for every SDLC stage (00-09)
- AI must be context-aware (knows current stage, project, gate status)
- Multi-provider support (Ollama primary + Claude fallback) for reliability
- **Multi-Agent Team Engine** (EP-07): PROFESSIONAL+ feature — coordinate AI agent teams

#### Capability 4: OTT Gateway (Channel-Based Access)
- Vietnam pilot: Telegram + Zalo (Sprint 181)
- Enterprise: Microsoft Teams + Slack (Sprint 182-183)
- All channels normalized via `agent_bridge/protocol_adapter.py`
- G3/G4 gate approvals via Magic Link (not direct OTT — security requirement ADR-059 INV-06)

#### Capability 5: Dashboard & Visibility
- Engineering Managers must see project health at a glance
- Real-time gate status (passed, failed, in progress)
- CEO Dashboard (PROFESSIONAL+ tier)
- Export reports for stakeholders (PDF, CSV)

#### Capability 6: Enterprise Features (PROFESSIONAL / ENTERPRISE tiers)
- Enterprise SSO: SAML 2.0 + Azure AD (Sprint 182 — BLOCKS enterprise sales)
- Compliance Evidence: SOC2 / HIPAA / NIST AI RMF evidence types (Sprint 183+)
- Tier Management Controls (ENTERPRISE only)
- Custom SLA + dedicated CSM (ENTERPRISE only)

---

### High-Level Non-Functional Requirements

**Performance**:
- Dashboard load: <1 second (p95)
- API response: <100ms (95th percentile)
- Support 100-1,000 concurrent teams (Year 1-2)

**Security**:
- Encryption at rest + in transit (AES-256, TLS 1.3)
- Authentication: OAuth 2.0 + Enterprise SSO (SAML/Azure AD)
- Authorization: RBAC (13 roles) + tier-based access
- Output credential scrubbing: 6 patterns (ADR-058 Pattern A, Sprint 179)

**Scalability**:
- Multi-tenant architecture (tenant isolation)
- Horizontal scaling (Kubernetes auto-scale)
- Evidence Vault: multi-region storage (Sprint 186)

**LITE Tier Resource Policy** (ADR-059 INV-05):
- Projects: 1 / Gates: 4 / Storage: 100MB / Members: 1
- Hibernate: 30 days inactivity → freeze (email warning Day 23)
- Purge: 90 days inactivity → hard delete (email Day 83, final Day 89)
- GDPR: data export available up to purge date

---

## ✅ Success Criteria (Gate Exit Criteria)

### Stage 00 Exit Criteria (G0.1 + G0.2 — PASSED)

**G0.1: Problem Definition Validated** ✅:
- ✅ Problem validated with 10+ external users
- ✅ Two-product strategy addresses root cause (identity crisis resolved)
- ✅ Enterprise-First refocus confirmed by CTO (Feb 19, 2026)
- ✅ Financial impact quantified ($60-70K waste per $100K team)

**G0.2: Solution Diversity Validated** ✅ (CPO Review, Feb 19, 2026):
| Option | Proposal | CPO Verdict |
|--------|----------|-------------|
| A: Enterprise-First | LITE stays, PROFESSIONAL+ gets investment priority | ✅ APPROVED |
| B: Enterprise-Only | Drop LITE + STANDARD entirely | ❌ VETOED (too narrow TAM) |
| C: Bottom-Up Growth | Feature parity all tiers; grow to enterprise | ❌ REJECTED (revenue delayed) |

**Overall Stage 00 Status**: ✅ APPROVED — Enterprise-First Option A

---

### Year 1 Success Criteria (Revised — Enterprise-First)

**Q1 2026 — Vietnam Pilot**:
- 5 Vietnam founding customers onboarded (PROFESSIONAL $399)
- TTFV <30 minutes (median)
- Satisfaction: 8/10 average
- Quality gate pass rate: ≥95%

**Q2 2026 — First Enterprise**:
- SSO GA (Sprint 182 complete)
- First enterprise deal closed (Teams OTT + SSO)
- TinySDLC 1,000 GitHub stars
- ARR: $65K-$120K

**Year 1 Exit (Dec 2026)**:
- **$160K-$350K ARR** (45-70 teams total) ← CPO committed target
- Feature Adoption Rate: 70%+ (North Star achieved)
- NPS: 8.0/10
- LTV:CAC: **>6.6:1** (CPO target BM-07)
- Gross Margin: **>78%** (CPO target)
- Break-even trajectory: Month 16 confirmed
- FOUNDER retention: 5/5 founding customers active

---

## 🗓️ Enterprise Roadmap (Sprint 181-192)

| Sprint | Theme | Key Deliverable |
|--------|-------|------------------|
| Sprint 181 | OTT Foundation | Telegram+Zalo live; 7 orphaned routes activated |
| Sprint 182 | Enterprise SSO Design | ADR-061 + Teams channel — enterprise deals unlocked |
| Sprint 183 | SSO Implementation | SAML GA + SOC2/HIPAA evidence types |
| Sprint 184 | Integrations + Tier Gates | Jira live; all 78 routes tier-gated |
| Sprint 185 | Audit Trail + SOC2 | SOC2 evidence pack generator |
| Sprint 186 | Multi-Region + GDPR | EU data residency (storage-level only) |
| Sprint 187 | G4 + Enterprise Beta | Gate G4 APPROVED; 2-3 beta enterprise |
| Sprint 188 | GA Launch | Pricing enforced; v2.0.0-ga; enterprise sales open |
| **Sprint 189** | **Chat Governance Loop** | **Ollama PoC + Chat Router + Magic Link (EP-08, ADR-064)** |
| **Sprint 190** | **Aggressive Cleanup** | **~18.3K LOC deletion (28% frontend); dead page removal** |
| **Sprint 191-192** | **Enterprise Hardening** | **SOC 2 chat audit; SSO magic link federation; E2E** |

---

## 🚫 Out of Scope (Stage 00)

**Stage 01 (WHAT)** will define:
- Detailed functional requirements (FR1, FR2, FR3...)
- Detailed feature specifications for new epics
- User stories & acceptance criteria

**Stage 02 (HOW)** will define:
- System architecture updates
- Database schema for new features
- API design

**Deferred to Sprint 181+**:
- `protocol_adapter.py` implementation (OTT abstraction — Sprint 181)
- `agent_bridge/` package (Sprint 181)
- ADR-060 Enterprise Channel Abstraction (Sprint 181)
- ADR-061 Enterprise SSO (Sprint 182)
- Enterprise pricing page + marketing materials (Sprint 188, CPO authority)

---

## 🎯 Approval & Next Steps

### Stakeholder Approval (Updated)

**Original Approval** (Nov 7, 2025):
- ✅ CEO (9.5/10) — GO FOR EXECUTION
- ✅ CPO (9.0/10)

**Enterprise-First Refocus Approval** (Feb 19, 2026):
- ✅ CTO — Enterprise-First conditional approval (6 corrections applied in ADR-059)
- ✅ CPO — G0.1 + G0.2 APPROVED; BM-01 through BM-10 DECIDED
- ✅ PM (@pm, SE4A) — BRD v3.0.0 reflecting all CPO decisions

**Chat-First Governance Loop Approval** (Feb 21, 2026):
- ✅ CTO — EP-08 + ADR-064 conditionally approved (11 conditions locked)
- ✅ Expert Panel — Option D+ approved 7/7 (5 expert rounds)
- ✅ PM (@pm, SE4A) — BRD v4.0.0 reflecting Chat-First pivot

**Pending CEO Review** (required before external communication):
- 🔴 Pricing page copy + marketing materials (Sprint 188)
- 🔴 Product Hunt launch timing
- 🟡 TinySDLC public launch announcement (Sprint 180-181)

### Next Steps (Enterprise-First Execution)

**Immediate (Sprint 181)**:
- TinySDLC public launch (GitHub repo + README)
- OTT foundation (Telegram + Zalo normalizers)
- 7 orphaned routes activated
- FOUNDER plan legacy migration (billing enum update)

**Near-term (Sprint 182-183)**:
- Enterprise SSO design + implementation
- Microsoft Teams channel
- SOC2/HIPAA evidence types

**Chat-First Governance (Sprint 189-192)**:
- Chat Router + Magic Link (Sprint 189)
- Aggressive Cleanup — 18.3K LOC deletion (Sprint 190)
- Enterprise Hardening — SOC 2 chat audit, SSO federation (Sprint 191-192)

**Target (Q4 2026)**:
- GA launch (Sprint 188)
- Enterprise sales pipeline open
- 50+ paying teams, ARR $150K+

---

**Document**: SDLC-Orchestrator-Business-Requirements-Document
**Framework**: SDLC 6.1.0 Stage 00 (WHY)
**Component**: Business Case — Problem & Opportunity Validation (Chat-First + Enterprise-First)
**Review**: Weekly with CPO (Tuesday 2 PM)
**CPO Authority**: BM-01 through BM-10 decided (Feb 19, 2026)
**ADR Reference**: ADR-059 (Enterprise-First), ADR-064 (Chat-First Facade)
**Last Updated**: February 21, 2026 by @pm (SE4A)

*"Chat = UX, Control Plane = Truth. Platform not faster than manual AI is a failed platform."* 🎯
