# SDLC Orchestrator - Business Requirements Document (BRD)
## WHY We Need This Solution - Problem Validation & Business Case

**Version**: 2.0.0
**Date**: December 23, 2025
**Status**: ACTIVE - STAGE 00 FOUNDATION (Software 3.0 Pivot)
**Authority**: CEO + CPO Approved
**Foundation**: Product Vision 4.0.0
**Stage**: Stage 00 (WHY) - Project Foundation
**Framework**: SDLC 5.1.1 Complete Lifecycle (10 Stages)

**Changelog v2.0.0** (Dec 23, 2025):
- **SOFTWARE 3.0 PIVOT**: Operating System for Software 3.0 positioning
- **EP-06 P0**: IR-Based Codegen (Sprint 45-50) as top priority
- **Founder Plan**: $99/team/month for Vietnam SME
- **Year 1 Target**: 30-50 teams (realistic, founder-led sales)
- **Dual Wedge Strategy**: Vietnam SME (40%) + Global EM (40%) + Enterprise (20%)
- **3-Layer Architecture**: Framework → Orchestrator → AI Coders

**Changelog v1.2.0** (Dec 21, 2025):
- Updated framework to SDLC 5.1.1 (from 4.9)
- Added EP-04/05/06 strategic extensions
- Added NQH AI Platform integration (qwen2.5-coder:32b)
- Added .sdlc-config.json innovation
- Updated competitive moat with AI Safety positioning

---

## 🎯 Document Purpose

This Business Requirements Document (BRD) answers **WHY** we are building SDLC Orchestrator by validating the business problem and opportunity.

**Stage 00 Focus (WHY)**:
- ✅ Problem validation with evidence
- ✅ Target market & personas (WHO suffers from this problem)
- ✅ Business opportunity & value proposition
- ✅ High-level requirements (what success looks like)
- ✅ Success criteria & constraints

**Stage 01 Focus (WHAT)** - Will be detailed later:
- ❌ Detailed functional requirements (FR1, FR2, FR3...)
- ❌ Detailed feature specifications
- ❌ Technical acceptance criteria
- ❌ Non-functional requirements (NFR1, NFR2...)

**Out of Scope**: Technical implementation (see Stage 02 - HOW)

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
5. **No AI assistance**: Manual PRD writing, test planning takes 2-3 days

### The Opportunity

**Market Size (Dual Wedge Strategy)**:

**Segment 1: Vietnam SME (40% of Year 1)**
- **TAM**: 800,000+ Vietnam SMEs
- **SAM**: 100,000 SMEs (F&B, Hotel, Retail seeking digitalization)
- **SOM Year 1**: 18-30 teams × $99/month × 12 = **$21K-$36K ARR**

**Segment 2: Global EM (40% of Year 1)**
- **TAM**: 3.4 million engineering teams globally
- **SAM**: 840,000 teams (English-speaking, cloud-native)
- **SOM Year 1**: 9-15 teams × $30/user × 10 users × 12 = **$32K-$54K ARR**

**Segment 3: Enterprise (20% of Year 1)**
- **SOM Year 1**: 3-5 teams × custom = **$33K-$54K ARR**

**Total Year 1 ARR: $86K-$144K** (realistic, founder-led sales)

**Why Now**:
- AI-native tools becoming standard (Copilot, Cursor, Claude Code)
- Compliance requirements increasing (SOC 2, ISO 27001 now table stakes)
- Vietnam SME digitalization government push (8% → 30% target by 2030)
- **SDLC 5.1.1 framework** validated (Bflow Platform proof of concept)

### What is SDLC 5.1.1? (Framework Foundation)

**SDLC 5.1.1** is a complete 10-stage software development lifecycle framework that guides teams from problem discovery to production operations.

**Evolution**: SDLC 4.8 → SDLC 5.1.3 → SDLC 5.1.3 → **SDLC 5.1.1** (December 2025)
- **SDLC 4.8**: 4 stages (WHY, WHAT, HOW, BUILD) - Foundation validated
- **SDLC 5.1.3**: 10 stages - Complete lifecycle including TEST, DEPLOY, OPERATE
- **SDLC 5.1.3**: Added AI Safety, SASE integration
- **SDLC 5.1.1**: Current - AI-Native Governance + Codegen Engine (Dec 2025)

**10 Stages**:
1. **Stage 00 (WHY - Foundation)**: Problem validation, business case, design thinking
2. **Stage 01 (WHAT - Planning)**: Requirements, user stories, solution design
3. **Stage 02 (HOW - Architecture)**: System design, database schema, API specs
4. **Stage 04 (BUILD - Development|**: Implementation, code review, CI/CD
5. **Stage 05 (TEST - Quality Assurance|**: Unit tests, integration tests, UAT
6. **Stage 06 (DEPLOY) - Go-Live)**: Blue-green deployment, rollback strategy, production readiness
7. **Stage 07 (OPERATE - Production Excellence|**: Monitoring, incident response, SRE practices
8. **Stage 03 (INTEGRATE - Systems Integration|**: API contracts, third-party integrations, data flows
9. **Stage 08 (COLLABORATE - Team Coordination)**: Documentation, knowledge sharing, team velocity
10. **Stage 09 (GOVERN - Strategic Oversight)**: Compliance, governance, strategic alignment

**Gate System**: 11 quality gates (G0.1, G0.2, G1-G9) with multi-approval workflow (CEO, CTO, CPO, CIO, CFO)

**Competitive Advantage**: SDLC Orchestrator is the FIRST platform built on SDLC 5.1.3 from day one, with perfect 1:1 alignment (10 stages → 10 /docs folders).

### The Solution (High-Level)

**SDLC Orchestrator**: The ONLY platform that ensures teams build the RIGHT things RIGHT by integrating SDLC 5.1.3 quality gates into developer workflows.

**Core Value Propositions**:
1. **Prevent Feature Waste**: Quality gates stop teams from building unwanted features
2. **Evidence-Based Decisions**: Every gate requires verifiable evidence
3. **AI-Powered Assistance**: Stage-aware AI helps teams pass gates faster
4. **Compliance Ready**: Automatic evidence vault for audits

**Competitive Moat**:
- **SDLC 5.1.1 methodology** (proprietary framework, 1-2 years to replicate, complete 10-stage lifecycle)
- 100+ pre-built policy packs (Lite, Standard, Enterprise)
- AI stage-aware prompts (unique differentiator, context-aware across 10 stages)
- Hybrid architecture (OSS infrastructure + custom IP)
- **Perfect /docs alignment**: ONLY platform with 10 stages → 10 folders (00-09)
- **AI Safety Layer**: Governance for Claude Code/Cursor/Copilot (EP-02)
- **SDLC Structure Enforcement**: Universal AI Codex validation (EP-04)
- **Enterprise Migration Engine**: .sdlc-config.json (1KB replaces 700KB) (EP-05)
- **Codegen Engine Tri-Mode**: BYO + Native OSS + Hybrid Fallback (EP-06)

---

## 👥 Target Market & Personas

### Market Segmentation

**Primary Market** (ICP - Ideal Customer Profile):
- **Company size**: 20-500 employees
- **Engineering team**: 6-50 engineers
- **Industry**: SaaS, B2B software, cloud-native
- **Geography**: English-speaking markets (US, UK, Australia, Canada)
- **Tech stack**: Modern (React, Node.js, Python, Docker, Kubernetes)
- **Compliance**: SOC 2, ISO 27001 required or upcoming

**Secondary Market** (Future expansion):
- Enterprise (500+ employees, 50-500 engineers)
- Regulated industries (Healthcare/HIPAA, Fintech/PCI-DSS)
- Non-English markets (Vietnamese, Japanese, German)

### Primary Personas

#### Persona 1: Engineering Manager (Primary Buyer - 60% of deals)

**Demographics**:
- Role: Engineering Manager, VP Engineering
- Team size: 6-50 engineers
- Reports to: CTO or CEO
- Budget authority: $10K-$100K/year
- Decision timeline: 2-4 weeks

**Pain Points** (validated with 10+ interviews):
1. **Feature waste**: "We built commenting system. 2% used it. 3 sprints wasted."
2. **No evidence**: "PM says users want it. No data. We waste 2 sprints."
3. **Audit chaos**: "SOC 2 = 3 engineers × 2 weeks scrambling for screenshots."
4. **Process overhead**: "8 tools (Jira, Confluence, Slack). Nothing enforced."
5. **Team morale**: "Engineers frustrated building features users ignore."

**Goals**:
- Increase feature adoption from 30% to 70%+
- Reduce wasted engineering effort by 50%+
- Pass SOC 2/ISO audits without manual evidence gathering
- Improve team morale (build features users LOVE)

**Buying Criteria**:
- ROI: Must save 20+ engineering hours/month (>$5K/month value)
- Ease of adoption: <2 weeks to onboard team
- Developer-friendly: Minimal workflow disruption
- Pricing: $99-$999/month acceptable

**Quote**:
> "If you can stop my team from wasting 60% of our effort on features users don't want, I'll pay $500/month TODAY."
> — Engineering Manager, 25-person SaaS company

---

#### Persona 2: CTO (Enterprise Buyer - 30% of deals)

**Demographics**:
- Role: CTO, VP Engineering (50+ engineers)
- Company size: 100-2,000 employees
- Budget authority: $100K-$500K/year
- Decision timeline: 4-12 weeks (requires board approval)

**Pain Points**:
1. **Compliance overhead**: "SOC 2 audit = $50K auditor + 200 hours internal."
2. **Lack of visibility**: "10 teams, 30 projects. No idea which on track."
3. **Process inconsistency**: "Each team has own 'process.' No standards."
4. **Evidence gaps**: "Auditor asks 'How validate requirements?' No answer."

**Goals**:
- Standardize SDLC across 10+ teams
- Automated evidence for compliance (SOC 2, ISO 27001)
- Real-time project health visibility
- Reduce audit prep from 200 hours to <20 hours

**Buying Criteria**:
- Enterprise features: SSO, RBAC, white-label, API access
- Compliance: SOC 2 Type 2, ISO 27001, GDPR-ready
- Scalability: Support 50-500 engineers
- Vendor stability: 3+ year roadmap

**Quote**:
> "We spend $150K/year on compliance. If you cut that in half AND improve SDLC quality, you're a no-brainer."
> — CTO, 200-person enterprise SaaS

---

#### Persona 3: Product Manager (Influencer - 10% direct buyer)

**Demographics**:
- Role: Product Manager, Product Owner
- Team size: 1-3 PMs managing 6-20 engineers
- Budget authority: Limited (influences EM/CTO)
- Decision timeline: 1-2 weeks (if self-funded)

**Pain Points**:
1. **No validation proof**: "Engineers ask 'Did you validate?' No proof."
2. **Feature bloat**: "Roadmap has 50 features. Which 10 to build?"
3. **Stakeholder pressure**: "CEO wants Feature X. Users want Y. No data."
4. **Post-launch regret**: "Shipped it. 5% adoption. Wasted 3 months."

**Goals**:
- Force discipline: No feature without user validation
- Data-driven prioritization
- Stakeholder communication (show WHY not building Feature X)
- Career growth: Ship features users LOVE (70%+ adoption)

**Buying Criteria**:
- Easy to use: PM can create gates without engineer help
- AI assistance: Generate interview scripts, PRD templates
- Integrations: Jira, Linear, GitHub, Figma
- Low price: <$299/month (PM can expense)

**Quote**:
> "I WANT gates. They protect me from building features that'll fail. Career insurance."
> — Senior PM, 50-person B2B SaaS

---

## 💼 Business Requirements (High-Level)

### BR1: Problem-Solution Fit

**Requirement**: SDLC Orchestrator must solve the validated problem of 60-70% feature waste.

**Success Criteria**:
- ✅ Problem validated with 3+ external users (actual: 10+ users)
- ✅ Solution addresses root causes (no validation, no evidence, process fatigue)
- ✅ Competitive differentiation clear (SDLC 4.8 moat vs Jira/Linear/GitLab)
- ✅ Value proposition quantified (save $60-70K/year per $100K team)

**Evidence**:
- 10+ user interview transcripts
- Pendo 2024 report (70% features unused)
- Bflow Platform data (32% adoption = 68% waste)
- Competitive analysis (Jira, Linear, GitLab, Backstage)

**Status**: ✅ VALIDATED (Stage 00 Gate G0.1)

---

### BR2: Market Opportunity

**Requirement**: SDLC Orchestrator must target a large, growing market.

**Success Criteria**:
- ✅ TAM >$500M (actual: $816M)
- ✅ SAM >$100M (actual: $201M)
- ✅ SOM Year 1 achievable (actual: $240K ARR with 100 teams)
- ✅ ICP validated (Engineering Manager, CTO, PM personas)
- ✅ Pricing validated (8/10 prospects: "$99-$999 reasonable")

**Market Trends** (supporting opportunity):
- AI-native tools: 300% growth 2023-2024 (GitHub Copilot, Cursor, v0)
- Compliance: SOC 2 now required by 80% of enterprise buyers (Vanta 2024)
- Remote work: 70% teams hybrid/remote (need process enforcement)
- Feature waste: Industry problem (Pendo: 70% features unused)

**Status**: ✅ VALIDATED

---

### BR3: Revenue Model

**Requirement**: SDLC Orchestrator must generate sustainable revenue.

**Pricing Model (v2.0.0 - Dual Wedge)**:

| Tier | Price | Target Customer | Expected Mix |
|------|-------|-----------------|--------------|
| **Founder Plan** | $99/team/mo | Vietnam SME (F&B, Hotel, Retail) | 60% (18-30 teams) |
| **Standard** | $30/user/mo | Global EM (6-50 engineers) | 30% (9-15 teams) |
| **Enterprise** | Custom | CTO (50-500 engineers) | 10% (3-5 teams) |

**Revenue Projections (Realistic)**:
- Year 1 ARR: **$86K-$144K** (30-50 teams, founder-led sales)
- Year 2 ARR: $432K-$864K (150-300 teams, sales team hired)
- Year 3 ARR: $1.4M-$2.9M (500-1,000 teams)

**Unit Economics**:
- Founder Plan LTV: $2,376/team (24 months × $99)
- Standard Plan LTV: $10,800/team (36 months × 10 users × $30)
- CAC (Year 1): ~$1,500/team (founder-led, low-cost channels)
- LTV:CAC ratio: 3:1 to 7:1 (healthy: >3:1)
- Gross margin: 80%+ (SaaS + codegen, minimal variable cost)

**Status**: ✅ VALIDATED (see Financial Model 2.0.0)

---

### BR4: Competitive Positioning

**Requirement**: SDLC Orchestrator must differentiate from existing tools.

**Competitive Landscape**:

| Competitor | Category | Our Advantage |
|------------|----------|---------------|
| **Jira** | Project management | SDLC 4.8 gates (they have none) |
| **Linear** | Issue tracking | Evidence vault (they have none) |
| **GitLab** | DevOps platform | AI-native (focused on SDLC quality) |
| **Backstage** | Developer portal | Turnkey SaaS (vs DIY open-source) |

**Competitive Moat** (1-2 years to replicate):
1. **3-Layer Architecture**: Framework → Orchestrator → AI Coders (unique positioning)
2. **SDLC 5.1.1 Framework**: Proprietary methodology, 5+ years development
3. **IR-Based Codegen**: Domain-specific code generation for Vietnam SME
4. **Policy Packs**: 100+ pre-built gates (Lite, Standard, Enterprise)
5. **AI Stage-Aware Prompts**: 50+ prompts aligned to SDLC stages
6. **Evidence Vault**: Automated compliance (SOC 2, ISO 27001)

**Positioning**:
- Category: "Operating System for Software 3.0" (new category we define)
- Tagline: "The Operating System for Software 3.0 - Where AI coders are governed, not feared"
- Differentiation: Control plane for AI coders + IR-based codegen for SME

**Status**: ✅ VALIDATED

---

### BR5: Legal & Compliance

**Requirement**: SDLC Orchestrator must comply with all legal requirements.

**Critical Requirements**:
- 🔴 OSS license compliance (AGPL v3 for MinIO, Grafana)
- 🔴 Trademark protection ("SDLC Orchestrator" US filing)
- 🟡 Data privacy (GDPR, CCPA compliance)
- 🟡 Security (SOC 2 Type 2 certification - Year 1 goal)

**Legal Review** (Week 2 - CRITICAL):
- OSS license audit: $25,000 (AGPL contamination risk)
- IP protection: $30,000 (trademark, trade secrets)
- Terms of Service: $10,000 (SaaS terms, privacy policy, DPA)
- Vendor contracts: $10,000 (AI providers, OSS vendors)

**Status**: 🔴 PENDING (Week 2 deadline - Go/No-Go decision)

---

## 🎯 High-Level Requirements

### What Success Looks Like

**Product Success** (North Star Metric):
- **Feature Adoption Rate**: Increase from 30% (industry baseline) to **70%+**
- Measurement: Track feature usage 90 days post-launch

**Supporting Metrics**:

| Metric | Baseline | Year 1 Target | Measurement Method |
|--------|----------|---------------|-------------------|
| **Time to Pass Gates** | 2-3 days (manual) | <1 day (AI-assisted) | Gate completion logs |
| **Developer NPS** | N/A | 8.0/10 | Quarterly survey |
| **Audit Prep Time** | 40-80 hours (manual) | <2 hours (automated) | Customer reports |
| **Engineering Waste** | 60-70% (validated) | <30% | Feature adoption tracking |

---

### High-Level Functional Requirements

**Note**: Detailed functional requirements will be specified in Stage 01 (WHAT). This section defines high-level capabilities only.

#### Capability 1: Quality Gate Management
- System must enforce SDLC 4.8 quality gates (prevent building wrong features)
- Gates must block progress until evidence provided
- Support for custom gates (YAML-based policy packs)

#### Capability 2: Evidence Vault
- System must automatically collect evidence for every gate
- Evidence must be encrypted, searchable, audit-ready
- Support multiple evidence types (screenshots, PDFs, test results, approvals)

#### Capability 3: AI Assistance
- System must provide AI help for every SDLC stage (00-06)
- AI must be context-aware (knows current stage, project, gate status)
- Multi-provider support (Claude, GPT-4o, Gemini) for reliability

#### Capability 4: Dashboard & Visibility
- Engineering Managers must see project health at a glance
- Real-time gate status (passed, failed, in progress)
- Export reports for stakeholders (PDF, CSV)

#### Capability 5: Developer Workflow Integration
- Developers interact with gates in existing tools (GitHub, VS Code)
- GitHub PR checks (gate status displayed in PR)
- GitHub Actions integration (auto-run gates on PR)

---

### High-Level Non-Functional Requirements

**Performance**:
- Dashboard load: <2 seconds
- API response: <100ms (95th percentile)
- Support 100-1,000 concurrent teams (Year 1-2)

**Security**:
- Encryption at rest + in transit (AES-256, TLS 1.3)
- Authentication: OAuth 2.0 (GitHub, Google, SSO)
- Authorization: RBAC (Admin, Manager, Developer, Viewer)

**Scalability**:
- Multi-tenant architecture (tenant isolation)
- Horizontal scaling (Kubernetes auto-scale)
- Rate limiting (1,000 req/min per tenant)

**Usability**:
- Developer onboarding: <2 weeks
- Quick start guide: <30 minutes
- Documentation: Searchable, versioned

---

## ✅ Success Criteria (Gate Exit Criteria)

### Stage 00 Exit Criteria (G0.1 + G0.2)

**G0.1: Problem Definition Validated**:
- ✅ Problem validated with 3+ external users (actual: 10+)
- ✅ Evidence collected (user interviews, Pendo report, Bflow data)
- ✅ Root causes identified (5 root causes documented)
- ✅ Financial impact quantified ($60-70K waste per $100K team)

**G0.2: Solution Diversity Validated**:
- ✅ 3+ solution options evaluated (Pure proprietary, Pure OSS, Hybrid)
- ✅ Decision matrix created (9 criteria scored)
- ✅ Option selected with justification (Option C - Hybrid: 9/10)
- ✅ Stakeholder approval (CEO 9.5/10, CTO 8.5/10, CPO 9.0/10)

**Overall Stage 00 Success**:
- ✅ Business case approved by CEO (9.5/10 confidence)
- ✅ Budget approved ($552.85K for 90 days)
- ✅ Team committed (8.5 FTE)
- ✅ Legal review planned (Week 2 - CRITICAL)
- ✅ GO FOR EXECUTION directive received

**Status**: 🟡 IN PROGRESS (awaiting legal review Week 2)

---

### Year 1 Success Criteria (Realistic)

**EP-06 Pilot (Sprint 49 - Q1 2026)**:
- 10 Vietnam SME founders onboarded
- TTFV <30 minutes (median)
- Satisfaction: 8/10 average
- Quality gate pass rate: ≥95%

**Founder Plan GA (Sprint 50 - Q2 2026)**:
- 18-30 Founder Plan teams
- Productization complete (docs, observability, support)
- DeepCode Q2 decision gate prepared

**Year 1 Exit (Dec 2026)**:
- **$86K-$144K ARR** (30-50 teams total)
- Feature Adoption Rate: 70%+ (North Star achieved)
- NPS: 8.0/10 (Vietnam SME focus)
- LTV:CAC: >3:1
- Vietnam SME satisfaction: ≥8/10

---

## 🚫 Out of Scope (Stage 00)

**Not Defined in Stage 00** (deferred to later stages):

**Stage 01 (WHAT)** will define:
- Detailed functional requirements (FR1, FR2, FR3...)
- Detailed feature specifications
- User stories & acceptance criteria
- API specifications
- Data models

**Stage 02 (HOW)** will define:
- System architecture
- Database schema
- API design
- Security architecture
- Deployment architecture

**Stage 04 (BUILD)** will create:
- Working code
- Unit tests
- Integration tests
- Documentation

---

## 🎯 Approval & Next Steps

### Stakeholder Approval

**Approved By**:
- ✅ CEO (9.5/10) - November 7, 2025
- ✅ CPO (9.0/10) - November 7, 2025
- ✅ PM (You) - November 13, 2025

**Conditions for GO**:
- 🔴 Legal review MUST complete by Week 2 (CRITICAL PATH)
- 🟡 GTM plan finalization by Week 6
- 🟡 Competitive defense strategy by Week 8

### Next Steps (Stage 00 Completion)

**Remaining Stage 00 Documents**:
- ✅ Product Vision (completed)
- ✅ Financial Model (completed)
- ✅ Stakeholder Alignment (completed)
- ✅ Business Requirements Document (this document)
- 🔵 Design Thinking documents (6 docs - in progress)
- 🔵 Product Roadmap (1 doc - pending)
- 🔵 Market Analysis (3 docs - pending)

**Timeline**:
- Week 1 (Nov 13-19): Complete Stage 00 documentation
- Week 2 (Nov 20-27): Legal review (CRITICAL - Go/No-Go)
- Week 3 (Nov 28-Dec 4): Begin Stage 01 (WHAT) - Planning & Analysis

---

**Document**: SDLC-Orchestrator-Business-Requirements-Document
**Framework**: SDLC 5.1.1 Stage 00 (WHY)
**Component**: Business Case - Problem & Opportunity Validation
**Review**: Weekly with CPO (Tuesday 2 PM)
**Last Updated**: December 23, 2025

**Strategic Priority (Software 3.0)**:
- EP-06 IR-Based Codegen: Sprint 45-50 (P0)
- Founder Plan: $99/team/month (Vietnam SME)
- Year 1 Target: 30-50 teams, $86K-$144K ARR

*"Define the RIGHT problem to build the RIGHT solution"* 🎯
