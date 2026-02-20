# SDLC Orchestrator - HMW Questions
## How Might We Questions (Design Thinking: DEFINE → IDEATE)

**Version**: 2.0.0
**Date**: February 19, 2026
**Status**: ACTIVE - 47 QUESTIONS GENERATED
**Authority**: CPO + PM + Design Lead Approved
**Foundation**: POV Statement 2.0.0, Problem Statement 3.0.0
**Stage**: Stage 00 (WHY) - Design Thinking DEFINE → IDEATE Transition
**Framework**: SDLC 6.1.0 (7-Pillar + AI Governance)

**Changelog v2.0.0** (February 19, 2026) — Enterprise-First Alignment:
- **FRAMEWORK**: SDLC 5.1.3 → 6.1.0 (7-Pillar + AI Governance)
- **STRATEGY**: Dual Wedge → Enterprise-First (ADR-059)
- **PRICING**: 6-tier model (LITE → ENTERPRISE, ADR-059)
- Year 1: 45-70 teams / $160K-$350K ARR

**Changelog v1.1.0** (Dec 21, 2025):
- Updated framework to SDLC 5.1.3
- Updated foundation references
- Added EP-04/05/06 solution context

---

## 🎯 Document Purpose

**HMW Questions** (How Might We) reframe problems as opportunities for solutions. They bridge the DEFINE phase (problem understanding) and IDEATE phase (solution generation).

**Format**: "How might we [verb] [object] [constraint/context]?"

**Goals**:
- Generate 20-50 HMW questions (actual: 47)
- Cover all user personas (EM, CTO, PM)
- Address all root causes (5 identified)
- Prioritize top 10 for IDEATE phase

---

## 📊 HMW Question Categories

We generated 47 HMW questions across 6 categories:

| Category | # Questions | Focus Area |
|----------|-------------|------------|
| **Validation** | 12 | How to enforce user validation before building |
| **Evidence** | 10 | How to collect/organize evidence automatically |
| **Compliance** | 8 | How to make audits effortless |
| **AI Assistance** | 9 | How to automate manual work (PRD, test plans) |
| **Visibility** | 5 | How to give EMs/CTOs real-time project health |
| **Process** | 3 | How to reduce tool overhead |

---

## 🎯 Category 1: Validation (12 HMW Questions)

**Root Cause**: No validation gates → 60-70% feature waste

**POV**: Engineering Managers need to prevent building unwanted features

---

### HMW-V1: Core Validation
**How might we** help Engineering Managers validate features with 3+ users before sprint planning?

**Why important**: Gate G0.1 requires 3+ user validations
**Constraints**: <2 hours time investment (vs 80 hours wasted sprint)
**Ideas**: AI interview script, user recruitment service, validation checklist

---

### HMW-V2: Make Validation Easy
**How might we** make user validation so easy that PMs do it for every feature?

**Why important**: Survey shows only 15% validate currently
**Constraints**: Must be easier than skipping validation
**Ideas**: 1-click interview scheduler, AI question generator, automated transcription

---

### HMW-V3: Prove Validation
**How might we** help PMs prove they validated features (not just claim it)?

**Why important**: Engineers don't trust PM claims without evidence
**Constraints**: Evidence must be searchable, audit-ready
**Ideas**: Evidence vault, auto-save interviews, shareable validation reports

---

### HMW-V4: Prevent Un-Validated Features
**How might we** block engineering from starting sprints on un-validated features?

**Why important**: Enforcement is critical (process without enforcement fails)
**Constraints**: Must not frustrate developers
**Ideas**: GitHub PR check (gate status), Jira integration (block ticket), dashboard alert

---

### HMW-V5: Quantify Validation Quality
**How might we** help EMs measure validation quality (not just "yes/no did it")?

**Why important**: 1 softball interview ≠ 3 rigorous interviews
**Constraints**: Simple scoring (1-10 scale)
**Ideas**: AI validation score, peer review, EM approval required

---

### HMW-V6: Scale Validation Across Teams
**How might we** help CTOs ensure all 10 teams validate features consistently?

**Why important**: CTO needs standardization at scale
**Constraints**: Works for 50-500 engineers
**Ideas**: Org-wide dashboard, team benchmarking, validation leaderboard

---

### HMW-V7: Learn from Past Mistakes
**How might we** show EMs which un-validated features failed (learn from history)?

**Why important**: "Those who don't learn history are doomed to repeat it"
**Constraints**: Non-blaming (learning, not punishment)
**Ideas**: Post-mortem dashboard, feature adoption tracking, pattern recognition

---

### HMW-V8: Validate Earlier
**How might we** help PMs validate features BEFORE detailed design (not after)?

**Why important**: Validating after design = sunk cost bias
**Constraints**: Gate G0.1 before Gate G1 (PRD)
**Ideas**: Problem validation phase, design thinking workshop, prototype testing

---

### HMW-V9: Validation Templates
**How might we** give PMs proven validation templates (not starting from scratch)?

**Why important**: 80% of interviews ask similar questions
**Constraints**: Customizable for different feature types
**Ideas**: Question library, AI interview script, industry best practices

---

### HMW-V10: Remote Validation
**How might we** make remote user validation as effective as in-person?

**Why important**: 70% teams hybrid/remote
**Constraints**: Zoom fatigue, timezone differences
**Ideas**: Async video interviews, loom recordings, survey+follow-up

---

### HMW-V11: Incentivize Users
**How might we** motivate users to participate in validation interviews?

**Why important**: Low response rates (20-30%)
**Constraints**: Budget ($50-100/interview)
**Ideas**: Gift cards, early access, feature voting, community recognition

---

### HMW-V12: Validation for B2B
**How might we** help B2B teams validate when users are busy executives?

**Why important**: ICP is Engineering Managers (busy, low availability)
**Constraints**: 15-30 min max interview time
**Ideas**: Async surveys, office hours, user advisory board

---

## 📂 Category 2: Evidence (10 HMW Questions)

**Root Cause**: No evidence trail → can't prove validation, audit chaos

**POV**: PMs need to prove validation, CTOs need audit-ready evidence

---

### HMW-E1: Auto-Collect Evidence
**How might we** automatically collect evidence without PM manual work?

**Why important**: Manual evidence collection fails (only 8% do it)
**Constraints**: Zero extra PM effort
**Ideas**: Browser extension (auto-screenshot), email integration, API uploads

---

### HMW-E2: Organize Evidence
**How might we** organize evidence so it's searchable and audit-ready?

**Why important**: Evidence in 8 tools = can't find when needed
**Constraints**: Folder structure (by gate, by project, by date)
**Ideas**: Evidence vault (MinIO S3), tags/metadata, full-text search

---

### HMW-E3: Evidence Types
**How might we** support all evidence types (screenshots, PDFs, videos, emails)?

**Why important**: Different gates need different evidence
**Constraints**: 10MB file size limit (performance)
**Ideas**: Multi-format storage, thumbnail previews, video transcription

---

### HMW-E4: Evidence Completeness
**How might we** help EMs know if evidence is complete (before audit)?

**Why important**: Auditor says "insufficient evidence" → scramble for 2 weeks
**Constraints**: Real-time completeness score
**Ideas**: Gate checklist, completeness percentage, missing evidence alerts

---

### HMW-E5: Share Evidence
**How might we** help PMs share evidence with engineers, stakeholders, auditors?

**Why important**: Evidence locked in PM's laptop ≠ shareable
**Constraints**: Permission controls (RBAC)
**Ideas**: Shareable links, PDF export, embeddable dashboard

---

### HMW-E6: Evidence Versioning
**How might we** track evidence changes over time (version control)?

**Why important**: PRD v1 → v2 → v3 (need to see evolution)
**Constraints**: Git-like versioning
**Ideas**: Evidence history, diff view, rollback capability

---

### HMW-E7: Evidence Retention
**How might we** ensure evidence is retained for 2+ years (compliance requirement)?

**Why important**: SOC 2 requires 2-year evidence retention
**Constraints**: Storage cost (<$100/month for 100 teams)
**Ideas**: MinIO lifecycle policies, S3 glacier, compression

---

### HMW-E8: Evidence Security
**How might we** ensure evidence is encrypted and access-controlled?

**Why important**: Evidence contains sensitive data (user interviews, emails)
**Constraints**: GDPR, CCPA compliance
**Ideas**: AES-256 encryption, IAM policies, audit logs

---

### HMW-E9: Evidence Templates
**How might we** give PMs evidence templates for common gates?

**Why important**: "What evidence does Gate G0.1 need?" → template shows
**Constraints**: Customizable per policy pack
**Ideas**: Template library, auto-fill forms, example evidence

---

### HMW-E10: Evidence Audit Trail
**How might we** show auditors WHO uploaded evidence WHEN?

**Why important**: Auditor asks "When was this validated?" → timestamp proves
**Constraints**: Immutable audit log
**Ideas**: Blockchain-like log, signed uploads, tamper-proof timestamps

---

## 🔒 Category 3: Compliance (8 HMW Questions)

**Root Cause**: Audit chaos → $150K/year cost, 200 hours manual work

**POV**: CTOs need automated compliance evidence

---

### HMW-C1: Audit Prep Time
**How might we** reduce SOC 2 audit prep from 40-80 hours → <2 hours?

**Why important**: $50K lost productivity per audit
**Constraints**: 1-click export
**Ideas**: Audit dashboard, PDF report generator, evidence vault

---

### HMW-C2: Compliance Dashboard
**How might we** give CTOs real-time compliance score (before auditor arrives)?

**Why important**: Proactive (fix gaps before audit), not reactive
**Constraints**: Live dashboard (updated real-time)
**Ideas**: Compliance percentage, missing evidence alerts, gate pass rate

---

### HMW-C3: Multi-Framework
**How might we** support multiple compliance frameworks (SOC 2, ISO 27001, HIPAA)?

**Why important**: Enterprise needs 2-3 frameworks
**Constraints**: Policy packs map to frameworks
**Ideas**: Framework templates, cross-walk mapping, multi-cert dashboard

---

### HMW-C4: Continuous Compliance
**How might we** make compliance continuous (not annual scramble)?

**Why important**: Evidence collected during development > scrambling before audit
**Constraints**: Zero extra PM effort
**Ideas**: Auto-collect evidence, real-time dashboard, gate enforcement

---

### HMW-C5: Auditor Collaboration
**How might we** make it easy for auditors to review evidence?

**Why important**: Happy auditor = faster audit, lower cost
**Constraints**: Read-only access, audit trail
**Ideas**: Guest login, shareable dashboard, PDF export

---

### HMW-C6: Compliance Benchmarking
**How might we** help CTOs compare compliance maturity vs peers?

**Why important**: Board asks "How do we compare to competitors?"
**Constraints**: Anonymous benchmarking data
**Ideas**: Industry averages, percentile ranking, best practices

---

### HMW-C7: Compliance Cost
**How might we** reduce compliance cost from $150K → <$50K/year?

**Why important**: $100K savings = 2x our product price
**Constraints**: Internal hours (200 → 20), external auditor cost (fixed)
**Ideas**: Self-service evidence, faster audits, multi-year certs

---

### HMW-C8: Compliance as Moat
**How might we** turn compliance burden into competitive advantage?

**Why important**: "We're SOC 2 certified" = trust signal, win enterprise deals
**Constraints**: Certified faster than competitors
**Ideas**: Fast-track cert (3 months), badge for website, sales enablement

---

## 🤖 Category 4: AI Assistance (9 HMW Questions)

**Root Cause**: Manual work → 14-28 hours/sprint on docs

**POV**: PMs/EMs need AI to automate PRD, test plans, release notes

---

### HMW-A1: PRD Generation
**How might we** generate 80% complete PRD from 5 user interview transcripts?

**Why important**: PRD writing takes 8-16 hours manually
**Constraints**: <2 hours PM review time
**Ideas**: Claude Sonnet 4.5, template-based generation, auto-fill sections

---

### HMW-A2: Interview Analysis
**How might we** help PMs synthesize 5 user interviews into insights?

**Why important**: Manual synthesis takes 4-8 hours
**Constraints**: Identify patterns, contradictions, quotes
**Ideas**: AI clustering, sentiment analysis, quote extraction

---

### HMW-A3: Test Plan Generation
**How might we** generate test plans from requirements?

**Why important**: Test planning takes 4-8 hours manually
**Constraints**: Cover all requirements, edge cases
**Ideas**: GPT-4o for test case generation, risk-based prioritization

---

### HMW-A4: Release Notes
**How might we** generate release notes from commit history?

**Why important**: Release notes take 2-4 hours manually
**Constraints**: User-facing language (not technical jargon)
**Ideas**: Git log analysis, AI rewriting, categorization

---

### HMW-A5: Stage-Aware AI
**How might we** provide AI assistance specific to each SDLC stage (00-06)?

**Why important**: Generic AI (ChatGPT) ≠ SDLC-specific prompts
**Constraints**: 50+ pre-built prompts
**Ideas**: Prompt library, context-aware (knows current gate), multi-provider

---

### HMW-A6: AI Context
**How might we** give AI context (project, gate, evidence) for better output?

**Why important**: "Generate PRD" (no context) < "Generate PRD for Project X, Gate G1, based on 5 interviews"
**Constraints**: Auto-load context (PM doesn't manual copy-paste)
**Ideas**: Evidence vault integration, project metadata, gate-aware prompts

---

### HMW-A7: AI Review
**How might we** use AI to review PRDs for completeness before PM submits?

**Why important**: Catch missing sections, success metrics undefined
**Constraints**: Checklist-based validation
**Ideas**: AI reviewer, completeness score, improvement suggestions

---

### HMW-A8: Multi-Provider AI
**How might we** use 3 AI providers (Claude, GPT-4o, Gemini) for cost optimization?

**Why important**: Claude best quality but expensive, Gemini 20x cheaper for bulk
**Constraints**: Intelligent routing (complex → Claude, simple → Gemini)
**Ideas**: Provider scoring, fallback logic, cost tracking

---

### HMW-A9: AI Cost Control
**How might we** prevent AI costs from spiraling (pass-through pricing)?

**Why important**: Customer pays AI cost, we add 20% markup
**Constraints**: Transparent pricing, usage caps
**Ideas**: Cost dashboard, usage alerts, tier-based limits

---

## 📊 Category 5: Visibility (5 HMW Questions)

**Root Cause**: Lack of visibility → CTOs don't know project status

**POV**: CTOs need real-time dashboard for 10+ teams, 30+ projects

---

### HMW-VIS1: Real-Time Dashboard
**How might we** give CTOs real-time project health (not 2-day manual consolidation)?

**Why important**: Board asks "What's at risk?" → CTO needs instant answer
**Constraints**: WebSocket push, <2 sec load time
**Ideas**: Live dashboard, at-risk alerts, gate pass rate

---

### HMW-VIS2: At-Risk Detection
**How might we** automatically detect at-risk projects (before they blow up)?

**Why important**: Proactive intervention > reactive firefighting
**Constraints**: Alert when 2+ critical gates fail
**Ideas**: Risk scoring, Slack/email alerts, escalation workflows

---

### HMW-VIS3: Team Benchmarking
**How might we** help CTOs compare team performance (gate pass rate, velocity)?

**Why important**: Identify best practices, scale what works
**Constraints**: Non-blaming (learning, not punishment)
**Ideas**: Team leaderboard, best practice sharing, peer learning

---

### HMW-VIS4: Board Reporting
**How might we** help CTOs present to board with live dashboard?

**Why important**: "Here's our real-time SDLC health" impresses board
**Constraints**: Executive-friendly (not technical jargon)
**Ideas**: Executive view, metrics explanation, export to PowerPoint

---

### HMW-VIS5: Historical Trends
**How might we** show CTOs trends over time (improving or declining)?

**Why important**: "We've improved gate pass rate 50% → 90% in 6 months"
**Constraints**: 12-month historical data
**Ideas**: Time-series charts, YoY comparison, goal tracking

---

## 🔧 Category 6: Process (3 HMW Questions)

**Root Cause**: Process fatigue → 6-10 tools, 20-30% time on overhead

**POV**: Developers need single source of truth, not 8 tools

---

### HMW-P1: Tool Consolidation
**How might we** reduce tool count from 8 → 1 (orchestration, not replacement)?

**Why important**: Context switching kills productivity
**Constraints**: Integrate with Jira, GitHub, Slack (not replace)
**Ideas**: Single dashboard, API integrations, unified search

---

### HMW-P2: Developer Experience
**How might we** make gate enforcement helpful (not frustrating) for developers?

**Why important**: Developers will hate gates if too much friction
**Constraints**: <5 min to pass typical gate
**Ideas**: GitHub PR checks, auto-run gates, clear error messages

---

### HMW-P3: Onboarding
**How might we** onboard new teams in <2 weeks (not 2 months)?

**Why important**: Fast time-to-value = higher adoption
**Constraints**: Quick start guide (<30 min), interactive tutorial
**Ideas**: Wizard setup, sample project, video walkthrough

---

## 🏆 Top 10 Prioritized HMW Questions

Based on:
- **Impact**: How much does solving this reduce feature waste?
- **Evidence**: How validated is the problem (user interviews)?
- **Feasibility**: Can we build this in 90 days?

### Priority Tier 1 (Must-Have for MVP)

1. **HMW-V1**: Help EMs validate features with 3+ users before sprint planning
   - Impact: 10/10 (core problem)
   - Evidence: 10/10 (all 10 EMs validated)
   - Feasibility: 8/10 (interview script generator)

2. **HMW-E1**: Automatically collect evidence without PM manual work
   - Impact: 9/10 (enables audit + trust)
   - Evidence: 9/10 (only 8% do this manually)
   - Feasibility: 7/10 (evidence vault integration)

3. **HMW-V4**: Block engineering from starting un-validated features
   - Impact: 10/10 (enforcement critical)
   - Evidence: 10/10 (process without enforcement fails)
   - Feasibility: 9/10 (GitHub PR check)

4. **HMW-A1**: Generate 80% complete PRD from interview transcripts
   - Impact: 8/10 (save 8-16 hours)
   - Evidence: 10/10 (all PMs want this)
   - Feasibility: 9/10 (Claude Sonnet 4.5 excellent at this)

5. **HMW-C1**: Reduce audit prep from 40-80 hours → <2 hours
   - Impact: 9/10 ($50K savings)
   - Evidence: 9/10 (9/10 companies pursuing SOC 2)
   - Feasibility: 8/10 (evidence vault + PDF export)

### Priority Tier 2 (Nice-to-Have for MVP, Must-Have Year 1)

6. **HMW-VIS1**: Give CTOs real-time dashboard for 10+ teams
   - Impact: 8/10 (CTO visibility)
   - Evidence: 8/10 (2/2 CTOs want this)
   - Feasibility: 7/10 (WebSocket complexity)

7. **HMW-V2**: Make user validation so easy PMs do it for every feature
   - Impact: 9/10 (increase validation rate 15% → 100%)
   - Evidence: 9/10 (survey validated)
   - Feasibility: 6/10 (user recruitment service complex)

8. **HMW-A5**: Provide stage-aware AI prompts (00-06)
   - Impact: 7/10 (differentiation)
   - Evidence: 7/10 (unique to SDLC Orchestrator)
   - Feasibility: 8/10 (50+ prompts to write)

9. **HMW-E2**: Organize evidence for searchability
   - Impact: 8/10 (find evidence in <30 sec)
   - Evidence: 8/10 (audit chaos validated)
   - Feasibility: 7/10 (metadata, tagging, search)

10. **HMW-P2**: Make gates helpful not frustrating for developers
    - Impact: 9/10 (adoption critical)
    - Evidence: 8/10 (developer resistance validated)
    - Feasibility: 8/10 (UX design, clear messaging)

---

## ✅ Next Steps (DEFINE → IDEATE)

**Completed** (DEFINE phase):
- ✅ User Personas (3 personas: EM, CTO, PM)
- ✅ Problem Statement (60-70% feature waste validated)
- ✅ POV Statement (EM needs to prevent waste)
- ✅ HMW Questions (47 questions generated, top 10 prioritized)

**Next** (IDEATE phase):
- 🔵 Generate 3+ solution options for top 10 HMW questions
- 🔵 Evaluate solutions (decision matrix: impact, cost, feasibility)
- 🔵 Select best solution for Gate G0.2 (Solution Diversity)
- 🔵 Create Empathy Maps (understand EM emotions)
- 🔵 Map User Journey (Idea → Production)

**Timeline**:
- Week 1: DEFINE phase complete (HMW questions done)
- Week 2: IDEATE phase (3 solution options for Gate G0.2)
- Week 3-4: PROTOTYPE phase (begin design)

---

**Document**: SDLC-Orchestrator-HMW-Questions
**Framework**: SDLC 6.1.0 Stage 00 (WHY) - Design Thinking DEFINE → IDEATE
**Component**: Problem Reframing (47 HMW Questions, Top 10 Prioritized)
**Review**: Monthly (generate new HMW questions as we learn)
**Last Updated**: February 19, 2026

*"Reframe problems as opportunities for solutions"* 💡
