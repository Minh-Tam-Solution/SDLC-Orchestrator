# Design Partner Scorecard v1.0
## Partner Selection & Qualification Criteria for EP-03

**Document ID**: TECH-SPEC-2026-004
**Version**: 1.0.0
**Status**: ✅ DESIGN APPROVED
**Created**: December 20, 2025
**Sprint**: Sprint 41 - AI Safety Foundation (Week 2)
**Framework**: SDLC 5.1.1 Complete Lifecycle
**Owner**: Product Team + Customer Success

---

## 📋 Table of Contents

1. [Executive Summary](#executive-summary)
2. [Business Context](#business-context)
3. [Partner Profile Definition](#partner-profile-definition)
4. [Scorecard Criteria](#scorecard-criteria)
5. [Scoring Model](#scoring-model)
6. [Qualification Process](#qualification-process)
7. [Partner Benefits & Commitments](#partner-benefits--commitments)
8. [Success Metrics](#success-metrics)
9. [Appendix](#appendix)

---

## 1. Executive Summary

### 1.1 Purpose

This document defines the **Design Partner Scorecard v1.0** for SDLC Orchestrator's EP-03 (Design Partner Program), providing a systematic framework to source, evaluate, and qualify 20 partner candidates with a target of onboarding ≥6 active partners during Sprint 41-43 (Q1 2026).

### 1.2 Strategic Alignment

**Q1-Q2 2026 Roadmap** (CTO Approved Dec 20, 2025):
- **EP-03: Design Partner Program** - Target 6 external teams by Sprint 43 (Feb 14, 2026)
- **Goal**: Validate AI Safety Layer v1 with real-world users, collect actionable feedback, generate 2 case studies
- **Budget**: $8,000 (workshops, onboarding materials, support)

### 1.3 Success Criteria

```yaml
Sprint 41 (Jan 6-17):
  ✅ 20 partner candidates sourced
  ✅ All candidates scored (≥60 points minimum)
  ✅ Partner outreach list prioritized

Sprint 42 (Jan 20-31):
  ✅ 2-3 partners onboarded
  ✅ First workshop delivered
  ✅ Bi-weekly feedback loop established

Sprint 43 (Feb 3-14):
  ✅ 6 total partners active
  ✅ ≥10 actionable feedback items collected
  ✅ 2 case studies in progress
```

---

## 2. Business Context

### 2.1 Why Design Partners?

**Rationale**:
1. **Validate Product-Market Fit**: Real-world usage before GA launch
2. **Gather Authentic Feedback**: Pain points, feature gaps, UX issues
3. **Build Case Studies**: Metrics-driven success stories for marketing
4. **Establish Advocates**: Early adopters become evangelists
5. **Reduce Risk**: Identify blockers before scaling to 100+ teams

**Lessons from MTEP & BFlow**:
- **MTEP**: Launched with 3 design partners → 65% drop-off → learned onboarding critical
- **BFlow**: 10 design partners → 2 became first paying customers ($50K ARR)
- **Key Insight**: Quality > Quantity. 6 engaged partners > 20 inactive.

### 2.2 Ideal Partner Profile (Hypothesis)

**Firmographic**:
- Team size: 10-50 engineers (not too small, not enterprise complexity)
- Industry: SaaS, Fintech, Healthcare, E-commerce (high governance needs)
- Stage: Series A - Series C (post-PMF, pre-IPO)
- Tech stack: Python/TypeScript/Java/Go (matches SDLC Orchestrator target)

**Behavioral**:
- **Heavy AI Tool Usage**: Cursor, Copilot, Claude Code (≥50% of team)
- **Governance Pain**: Struggling with AI code quality, architecture drift
- **Engaged Leadership**: CTO/VP Eng/Eng Manager willing to invest time
- **Data-Driven**: Tracks DORA metrics, code quality metrics

**Psychographic**:
- **Innovators**: Early adopters, willing to try new tools
- **Pragmatists**: Care about ROI, not just novelty
- **Collaborators**: Willing to give feedback, attend workshops
- **Champions**: Can influence others (peer network, conferences)

---

## 3. Partner Profile Definition

### 3.1 Must-Have Criteria (Disqualifiers)

**If ANY of these are NO, candidate is disqualified**:

1. **AI Tool Adoption**: Using Cursor, Copilot, Claude Code, or ChatGPT for code generation
   - **Why**: Can't validate AI Safety Layer without AI-generated code
   - **Verification**: Ask "What % of your team uses AI coding tools?" (answer must be >30%)

2. **Codebase Size**: ≥10,000 lines of code (LOC)
   - **Why**: Too small = no governance complexity
   - **Verification**: GitHub repo stats or manual estimate

3. **Active Development**: ≥5 PRs per week
   - **Why**: Need ongoing activity to test AI Safety features
   - **Verification**: GitHub Insights or Jira velocity

4. **Decision Maker Access**: CTO, VP Eng, or Eng Manager willing to participate
   - **Why**: Need authority to implement tool, not just IC interest
   - **Verification**: Email domain (@company.com), LinkedIn title

5. **English/Vietnamese Communication**: Can communicate in English or Vietnamese
   - **Why**: Support team fluency, documentation language
   - **Verification**: Email/call screening

### 3.2 Nice-to-Have Criteria (Scored)

**These criteria are scored 0-100 points** (see Scoring Model section):

1. **AI Governance Pain** (0-20 points)
   - Has experienced AI code quality issues (bugs, architecture drift)
   - Actively seeking solution (not just curious)

2. **Team Size & Structure** (0-15 points)
   - 10-50 engineers ideal (10 pts)
   - Dedicated QA/DevOps (5 pts)

3. **Industry & Use Case** (0-15 points)
   - Regulated industry (Fintech, Healthcare, Government) = high governance needs
   - B2B SaaS = good case study material

4. **Technical Fit** (0-15 points)
   - Tech stack matches SDLC Orchestrator (Python, TypeScript, React)
   - Already using similar tools (OPA, Argo, Linear)

5. **Engagement Commitment** (0-20 points)
   - Willing to attend bi-weekly feedback calls (10 pts)
   - Can provide metrics (DORA, quality) before/after (10 pts)

6. **Network & Influence** (0-10 points)
   - Speaks at conferences, writes blog posts
   - Large LinkedIn/Twitter following (>1K)

7. **Geographic Location** (0-5 points)
   - Vietnam, Singapore, US West Coast (timezone overlap)
   - Enables live workshops, faster support

**Total Possible Score**: 100 points
**Minimum Passing Score**: 60 points

---

## 4. Scorecard Criteria

### 4.1 Detailed Scoring Rubric

#### Criterion 1: AI Governance Pain (0-20 points)

**Question**: "What AI code quality challenges are you currently facing?"

| Score | Description | Indicators |
|-------|-------------|------------|
| **20** | **Acute Pain** | Experiencing production incidents from AI code (bugs, security issues), actively budgeted for solution |
| **15** | **Moderate Pain** | Frequent AI code review rework, architecture drift complaints, seeking solution |
| **10** | **Mild Pain** | Occasional issues, aware of risks, open to preventive tools |
| **5** | **Latent Pain** | No incidents yet, but concerned about future risks |
| **0** | **No Pain** | Not concerned, or not using AI tools enough to have issues |

**Verification**:
- Ask: "Can you share an example of an AI-generated code issue in the past 3 months?"
- Red flag: Vague answers like "we're just curious" (score 0)
- Green flag: Specific incident (e.g., "AI added hardcoded credentials, went to prod") (score 20)

---

#### Criterion 2: Team Size & Structure (0-15 points)

**Question**: "How many engineers on your team, and what's the structure?"

| Score | Description | Indicators |
|-------|-------------|------------|
| **15** | **Ideal Structure** | 20-50 engineers, dedicated QA team, DevOps/SRE team, PM/PO |
| **12** | **Good Structure** | 10-20 engineers, some QA, some DevOps, PM |
| **8** | **Acceptable** | 5-10 engineers, no dedicated QA/DevOps (engineers wear hats) |
| **4** | **Small Team** | 2-5 engineers, solo founders |
| **0** | **Too Small** | 1 engineer (can't validate team collaboration features) |

**Verification**:
- LinkedIn company page (employee count)
- Ask org chart or team composition

**Bonus Points**:
- +3 points: Has dedicated QA team (validates AI Safety validation pipeline)
- +2 points: Has DevOps/SRE team (validates deployment automation)

---

#### Criterion 3: Industry & Use Case (0-15 points)

**Question**: "What industry are you in, and what does your product do?"

| Score | Description | Industries | Why High Value |
|-------|-------------|------------|----------------|
| **15** | **High Governance** | Fintech, Healthcare, Government, Defense | Regulatory compliance (HIPAA, SOC 2, ISO 27001) requires strong SDLC governance |
| **12** | **Medium Governance** | E-commerce, SaaS, EdTech, Logistics | Quality-sensitive, customer-facing, moderate compliance needs |
| **8** | **Low Governance** | Internal tools, B2B utilities, Marketing tech | Less regulatory pressure, but still care about quality |
| **4** | **Consumer Apps** | Social, Gaming, Media | Fast iteration, less governance culture |
| **0** | **Not Applicable** | Non-software (consulting, services) | Can't validate SDLC tool |

**High-Value Industries for Case Studies**:
1. **Fintech**: "How Acme FinTech ensured AI code complied with PCI-DSS using SDLC Orchestrator"
2. **Healthcare**: "Reducing AI code risks in HIPAA-compliant telehealth platform"
3. **Government**: "AI Safety for critical infrastructure management systems"

---

#### Criterion 4: Technical Fit (0-15 points)

**Question**: "What's your tech stack (languages, frameworks, tools)?"

| Score | Description | Tech Stack |
|-------|-------------|------------|
| **15** | **Perfect Fit** | Python + TypeScript + React, uses OPA/Argo/MinIO, GitHub |
| **12** | **Good Fit** | Python or TypeScript, uses some OSS governance tools, GitHub |
| **8** | **Acceptable Fit** | Java/Go/Ruby, GitHub, willing to try new tools |
| **4** | **Partial Fit** | .NET/PHP, GitLab (requires GitLab support, deferred to Q2) |
| **0** | **No Fit** | Legacy languages (COBOL, VB6), SVN version control |

**Bonus Points**:
- +3 points: Already uses OPA (Open Policy Agent) for policies
- +2 points: Already uses MinIO or S3 for storage
- +2 points: Already uses Grafana or Prometheus for monitoring
- +2 points: Uses Linear, Jira, or Asana (integrates with SDLC Orchestrator)

**Red Flags** (disqualify):
- No version control (SVN, manual deployments)
- Exclusively GitLab (SDLC Orchestrator GitHub-first in Q1, GitLab deferred to Q2)

---

#### Criterion 5: Engagement Commitment (0-20 points)

**Question**: "Can you commit to bi-weekly feedback calls and sharing metrics?"

| Score | Description | Commitment Level |
|-------|-------------|------------------|
| **20** | **Full Engagement** | Bi-weekly calls + metrics (DORA, coverage, bugs) + case study interview + workshop attendance |
| **15** | **High Engagement** | Bi-weekly calls + some metrics + case study interview |
| **10** | **Moderate Engagement** | Monthly calls + async feedback (Slack, email) |
| **5** | **Low Engagement** | Async feedback only, no calls |
| **0** | **No Engagement** | "Just let us try it, we'll reach out if we have issues" |

**Verification**:
- Ask: "Can you commit to 30-min bi-weekly calls for 6 weeks (Sprint 41-43)?"
- Ask: "Can you share DORA metrics (deploy frequency, lead time, MTTR, change fail rate) before/after pilot?"
- Ask: "Would you be willing to be featured in a case study if the pilot is successful?"

**Red Flags**:
- "We're too busy for regular calls" → Likely to churn
- "We don't track metrics" → Hard to prove ROI

---

#### Criterion 6: Network & Influence (0-10 points)

**Question**: "Do you speak at conferences, write technical blog posts, or have a strong social media presence?"

| Score | Description | Indicators |
|-------|-------------|------------|
| **10** | **High Influence** | Conference speaker (≥2 talks/year), technical blog (≥1K followers), Twitter/LinkedIn influencer (≥5K followers) |
| **7** | **Moderate Influence** | Occasional speaker, company blog author, LinkedIn active (≥1K connections) |
| **4** | **Low Influence** | Attends conferences, shares content, small network (<500) |
| **0** | **No Influence** | No public presence |

**Why This Matters**:
- **Marketing Amplification**: Influencers share case studies → organic reach
- **Credibility**: "As seen at [Conference Name]" → trust signal
- **Referrals**: Influencers refer peers → pipeline growth

**Verification**:
- LinkedIn profile (connections, posts, activity)
- Google search: "[Name] conference talk" or "[Company] blog"
- Twitter/X follower count

**Bonus Points**:
- +5 points: Has spoken at major conference (GopherCon, PyCon, React Summit, KubeCon)
- +3 points: Company has active engineering blog (≥1 post/month)

---

#### Criterion 7: Geographic Location (0-5 points)

**Question**: "Where is your engineering team located?"

| Score | Location | Timezone Overlap (GMT+7 Hanoi) |
|-------|----------|--------------------------------|
| **5** | Vietnam, Thailand, Singapore, Malaysia | Perfect overlap (same timezone) |
| **4** | Hong Kong, Philippines, Indonesia, Australia | ±1-2 hour overlap |
| **3** | India, Middle East, Europe | ±3-5 hour overlap (workable) |
| **2** | US West Coast (PST) | +15 hours (challenging but doable) |
| **1** | US East Coast (EST) | +12 hours (minimal overlap) |
| **0** | South America, Africa | Minimal/no overlap |

**Why This Matters**:
- **Live Workshops**: Easier to schedule 90-min workshop if timezones align
- **Support Speed**: Faster Slack responses, live debugging sessions
- **Relationship Building**: Video calls easier when both parties awake

**Note**: Not a disqualifier, but preferred. US partners acceptable if highly qualified.

---

## 5. Scoring Model

### 5.1 Weighted Scorecard

**Total Score = Σ (Criterion Score × Weight)**

| # | Criterion | Max Points | Weight | Weighted Max |
|---|-----------|------------|--------|--------------|
| 1 | AI Governance Pain | 20 | 1.0x | 20 |
| 2 | Team Size & Structure | 15 | 1.0x | 15 |
| 3 | Industry & Use Case | 15 | 1.0x | 15 |
| 4 | Technical Fit | 15 | 1.0x | 15 |
| 5 | Engagement Commitment | 20 | 1.5x | 30 |
| 6 | Network & Influence | 10 | 0.5x | 5 |
| 7 | Geographic Location | 5 | 0.5x | 2.5 |
| **TOTAL** | | **100** | | **102.5** |

**Rationale for Weights**:
- **Engagement Commitment (1.5x)**: Most predictive of success. Engaged partners = actionable feedback.
- **Network & Influence (0.5x)**: Nice-to-have, not critical. A quiet partner who gives great feedback > loud partner who ghosts.
- **Geographic Location (0.5x)**: Convenience, not requirement.

### 5.2 Qualification Tiers

| Tier | Score Range | Priority | Action |
|------|-------------|----------|--------|
| **Tier 1: High Priority** | 80-100 | P0 | Immediate outreach, CTO call, expedite onboarding |
| **Tier 2: Medium Priority** | 60-79 | P1 | Standard outreach, PM call, onboard if Tier 1 insufficient |
| **Tier 3: Low Priority** | 40-59 | P2 | Waitlist, defer to Sprint 44+ |
| **Tier 4: Disqualified** | 0-39 | - | Politely decline, keep in CRM for future |

**Sprint 41 Target**: Source 20 candidates, aim for ≥10 Tier 1 + ≥6 Tier 2.

### 5.3 Example Scoring

**Candidate A: Acme FinTech (Tier 1 - Score 87)**

| Criterion | Score | Rationale |
|-----------|-------|-----------|
| AI Governance Pain | 20/20 | Production incident: AI code exposed API keys, $10K security audit |
| Team Size & Structure | 15/15 | 30 engineers, dedicated QA (5), DevOps (3), PM team |
| Industry & Use Case | 15/15 | Fintech, PCI-DSS compliance required |
| Technical Fit | 15/15 | Python + TypeScript, GitHub, already uses OPA (+3 bonus) |
| Engagement Commitment | 20/20 × 1.5 = 30 | Committed to bi-weekly calls, will share DORA metrics, case study OK |
| Network & Influence | 7/10 × 0.5 = 3.5 | CTO spoke at local conference, LinkedIn 2K connections |
| Geographic Location | 5/5 × 0.5 = 2.5 | Vietnam (perfect overlap) |
| **TOTAL** | **87** | **Tier 1 - High Priority** |

**Action**: Immediate outreach, schedule CTO call within 48 hours, fast-track onboarding.

---

**Candidate B: BetaStartup (Tier 2 - Score 68)**

| Criterion | Score | Rationale |
|-----------|-------|-----------|
| AI Governance Pain | 15/20 | Moderate pain: frequent code review rework, no incidents |
| Team Size & Structure | 8/15 | 8 engineers, no dedicated QA (devs do QA) |
| Industry & Use Case | 12/15 | B2B SaaS, medium governance needs |
| Technical Fit | 12/15 | TypeScript + React, GitHub, no OPA experience |
| Engagement Commitment | 15/20 × 1.5 = 22.5 | Committed to bi-weekly calls, no metrics sharing |
| Network & Influence | 0/10 × 0.5 = 0 | No public presence |
| Geographic Location | 3/5 × 0.5 = 1.5 | India (+5 hour overlap, workable) |
| **TOTAL** | **68** | **Tier 2 - Medium Priority** |

**Action**: Standard outreach, PM call, onboard if Tier 1 slots filled.

---

**Candidate C: GammaGaming (Tier 3 - Score 52)**

| Criterion | Score | Rationale |
|-----------|-------|-----------|
| AI Governance Pain | 5/20 | Latent pain, no issues yet |
| Team Size & Structure | 4/15 | 3 engineers, solo founders |
| Industry & Use Case | 4/15 | Mobile gaming, low governance culture |
| Technical Fit | 8/15 | React Native, GitHub |
| Engagement Commitment | 10/20 × 1.5 = 15 | Monthly calls only, no metrics |
| Network & Influence | 4/10 × 0.5 = 2 | Small LinkedIn network |
| Geographic Location | 5/5 × 0.5 = 2.5 | Vietnam (perfect overlap) |
| **TOTAL** | **52** | **Tier 3 - Waitlist** |

**Action**: Defer to Sprint 44+, keep in CRM for future when product matures.

---

## 6. Qualification Process

### 6.1 Sourcing Channels (20 Candidates)

**Channel 1: Existing Network (Target: 8 candidates)**
- NQH internal teams (BFlow, MTEP, Nhat Quang Digital)
- MTS portfolio companies (5-10 companies)
- Personal network: CTO, CPO, CEO connections

**Channel 2: LinkedIn Outreach (Target: 6 candidates)**
- Search: "CTO" OR "VP Engineering" + "Cursor" OR "Copilot" OR "AI coding"
- Vietnam, Singapore, US West Coast
- InMail campaign (personalized, not spam)

**Channel 3: Community & Events (Target: 4 candidates)**
- Vietnam Tech Meetups (VNTechies, GDG, PyConVN)
- Singapore Tech Conferences (DevSecCon, AWS Summit)
- Online communities (r/devops, r/programming, Dev.to)

**Channel 4: Referrals (Target: 2 candidates)**
- Ask existing partners: "Who else do you know struggling with AI code quality?"
- Referral incentive: 1 month free upgrade if referral becomes partner

### 6.2 Outreach Email Template

**Subject**: [First Name], interested in beta-testing AI code governance for [Company]?

**Body**:
```
Hi [First Name],

I noticed [Company] is using [AI Tool - Cursor/Copilot] based on [specific signal - GitHub commits, blog post, LinkedIn post].

We're launching SDLC Orchestrator, an AI Safety Layer that ensures AI-generated code complies with your architecture and quality standards. Think "Policy-as-Code for AI tools."

**3 killer capabilities**:
1. AI code can't merge if it violates your architecture policies
2. Full evidence trail for every AI-generated PR (compliance-ready)
3. Automatic validation (lint, tests, coverage, security) before merge

We're looking for 6 Design Partners (Series A-C SaaS/Fintech teams) to pilot the platform in Q1 2026.

**What's in it for you**:
- 6-9 months free access ($500+/month value)
- Dedicated Slack support (response time <2 hours)
- Grandfathered pricing when we GA launch

**What we need**:
- 30-min bi-weekly feedback calls (6 weeks)
- Share before/after metrics (deploy frequency, code quality)
- Optional: Case study if pilot is successful

Interested? Let's schedule a 15-min intro call: [Calendly link]

Best,
[Your Name]
[Title]
SDLC Orchestrator
[Website] | [LinkedIn]

P.S. We're backed by [Investor/CTO approval], battle-tested by [NQH/MTS] teams (200K LOC managed).
```

**Follow-up Sequence**:
- Day 0: Initial email
- Day 3: Follow-up if no response ("Just checking if you saw this...")
- Day 7: Final follow-up ("Last call - pilot spots filling up fast")
- Day 10: Move to "Not Interested" list

### 6.3 Screening Call Agenda (15 minutes)

**Objective**: Score candidate on 7 criteria, qualify or disqualify.

**Minute 0-2: Intro**
- "Thanks for taking the time. I'm [Name], building SDLC Orchestrator - an AI Safety Layer for dev teams."
- "Goal today: See if there's a fit for our Design Partner program. Sound good?"

**Minute 2-5: Discovery (Score Criteria 1-3)**
- "Tell me about your team. How many engineers? What's your tech stack?"
  → Score: Team Size, Technical Fit
- "What % of your team uses AI coding tools like Cursor, Copilot, Claude?"
  → Verify: Must-Have Criterion 1
- "Have you experienced any AI code quality issues? Can you share an example?"
  → Score: AI Governance Pain

**Minute 5-8: Qualifying Questions (Score Criteria 4-7)**
- "What industry are you in? Any compliance requirements (HIPAA, SOC 2, PCI-DSS)?"
  → Score: Industry & Use Case
- "If we move forward, can you commit to 30-min bi-weekly calls for 6 weeks?"
  → Score: Engagement Commitment
- "Can you share metrics like deploy frequency, test coverage before/after the pilot?"
  → Score: Engagement Commitment (bonus)
- "Where is your engineering team located?"
  → Score: Geographic Location

**Minute 8-12: Pitch (If score ≥60)**
- "Based on what you've shared, I think there's a strong fit. Let me explain what we're building..."
- [Demo 3 killer capabilities: Policy Guards, Evidence Trail, Validation Pipeline]
- "This is perfect for teams like yours in [Industry] with [Pain Point]."

**Minute 12-14: Next Steps**
- "Here's what the Design Partner program includes: [Benefits]"
- "And here's what we'd need from you: [Commitments]"
- "Does this sound like a good fit?"

**Minute 14-15: Close**
- If YES: "Great! I'll send a calendar invite for onboarding kickoff. You'll meet [Backend Lead] who'll walk you through setup."
- If NO: "No problem. I'll keep you posted when we GA launch. Can I stay in touch via [LinkedIn/email]?"

**Post-Call**:
- Score candidate in CRM (Airtable or Notion)
- Send follow-up email with next steps (if qualified)
- Update pipeline dashboard

---

## 7. Partner Benefits & Commitments

### 7.1 What Partners Get (Benefits)

**Benefit 1: Free Access (6-9 months)**
- Value: $500-1000/month (Team tier pricing)
- Duration: Sprint 41 (Jan 6) → GA launch (target: Jun 30, 2026)
- No credit card required

**Benefit 2: Dedicated Support**
- Slack channel: #design-partner-[company-name]
- Response time: <2 hours during business hours (GMT+7)
- Direct access to Backend Lead, Frontend Lead, CTO

**Benefit 3: Influence Product Roadmap**
- Bi-weekly feedback calls → features prioritized
- Vote on roadmap (Productboard or Linear)
- Early access to new features (beta releases)

**Benefit 4: Grandfathered Pricing**
- Lock in design partner pricing when GA launches
- Example: If GA launch = $500/mo, partner pays $300/mo (40% discount)
- Lifetime guarantee (as long as subscribed)

**Benefit 5: Marketing Co-Benefits**
- Case study feature (optional): "[Company] reduced AI code incidents by 60% with SDLC Orchestrator"
- Co-marketing: Joint blog post, conference talk, webinar
- Logo on website: "Trusted by [Partner Logos]"

**Benefit 6: Exclusive Workshops**
- 90-min workshop: "AI Safety for Engineering Teams" (Sprint 42)
- Q&A sessions with CTO on AI governance best practices
- Access to workshop materials (slides, templates)

### 7.2 What Partners Commit (Responsibilities)

**Commitment 1: Active Usage**
- Integrate SDLC Orchestrator into daily workflow
- Target: ≥10 AI PRs analyzed during pilot (Sprint 41-43)
- Minimum: ≥5 PRs (otherwise, not enough data to validate)

**Commitment 2: Bi-Weekly Feedback Calls**
- Duration: 30 minutes
- Frequency: Every 2 weeks (total 3 calls during Sprint 41-43)
- Attendance: CTO, VP Eng, or Eng Manager (decision maker)
- Agenda: What's working, what's not, feature requests, bugs

**Commitment 3: Metrics Sharing**
- Before pilot: Baseline metrics (DORA, coverage, incident rate)
- After pilot: Post-pilot metrics (compare before/after)
- Examples:
  - Deploy frequency: 5/week → 8/week (+60%)
  - Change fail rate: 15% → 8% (-47%)
  - Test coverage: 65% → 82% (+17pp)

**Commitment 4: Case Study Participation (Optional)**
- If pilot successful, participate in case study interview (60 min)
- Approve draft before publication
- Share on company's social media (LinkedIn, Twitter)

**Commitment 5: Bug Reporting & Documentation**
- Report bugs in Slack or GitHub Issues (response within 24h)
- Share screenshots, logs, reproduction steps
- Patience with beta product (expected rough edges)

**Commitment 6: NDA & Confidentiality**
- Sign NDA (mutual non-disclosure)
- Don't share pre-GA product screenshots publicly
- Don't share pricing, roadmap, or internal docs

---

## 8. Success Metrics

### 8.1 Sprint 41 Metrics (Sourcing Phase)

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Candidates Sourced** | 20 | CRM count |
| **Tier 1 Candidates** | ≥10 | Score ≥80 |
| **Tier 2 Candidates** | ≥6 | Score 60-79 |
| **Qualification Rate** | ≥50% | (Tier 1 + Tier 2) / Total |
| **Response Rate** | ≥30% | Replied / Outreach emails |
| **Screening Calls Completed** | ≥15 | Calendar events |

### 8.2 Sprint 42-43 Metrics (Onboarding & Engagement)

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Partners Onboarded** | ≥6 | Signed NDA, integrated tool |
| **Active Partners** | ≥5 | ≥5 PRs analyzed during pilot |
| **Feedback Items Collected** | ≥10 | Linear issues tagged "partner-feedback" |
| **Workshop Attendance** | ≥4 partners | Zoom attendance log |
| **Churn Rate** | <20% | (Churned / Onboarded) × 100 |
| **Case Studies In Progress** | ≥2 | Interviews scheduled |

### 8.3 Post-Sprint 43 Metrics (Outcomes)

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Partner NPS** | ≥8.0 | NPS survey (0-10 scale) |
| **Feature Requests Implemented** | ≥5 | From partner feedback → shipped |
| **Case Studies Published** | ≥2 | Blog post, PDF, video |
| **Conversion to Paid** | ≥3 partners | When GA launch (Jun 2026) |
| **Referrals Generated** | ≥2 new leads | "How did you hear about us?" |

---

## 9. Appendix

### 9.1 Scorecard Template (Airtable/Notion)

**Table: Design Partner Candidates**

| Field | Type | Description |
|-------|------|-------------|
| Company Name | Text | Candidate company |
| Contact Name | Text | CTO/VP Eng/Eng Manager |
| Email | Email | Contact email |
| LinkedIn | URL | LinkedIn profile |
| Source | Select | Existing Network / LinkedIn / Community / Referral |
| Team Size | Number | Number of engineers |
| Industry | Select | Fintech / Healthcare / SaaS / E-commerce / Other |
| Tech Stack | Text | Python, TypeScript, etc |
| AI Tool Usage | Text | Cursor, Copilot, Claude, ChatGPT |
| **Score: AI Governance Pain** | Number (0-20) | From screening call |
| **Score: Team Size** | Number (0-15) | From screening call |
| **Score: Industry** | Number (0-15) | From screening call |
| **Score: Technical Fit** | Number (0-15) | From screening call |
| **Score: Engagement** | Number (0-30) | From screening call (weighted) |
| **Score: Influence** | Number (0-5) | From screening call (weighted) |
| **Score: Location** | Number (0-2.5) | From screening call (weighted) |
| **Total Score** | Formula | SUM(Scores) |
| **Tier** | Formula | IF(Score≥80, "Tier 1", IF(Score≥60, "Tier 2", "Tier 3")) |
| Status | Select | Sourced / Contacted / Screened / Qualified / Onboarded / Churned |
| Notes | Long Text | Screening call notes, feedback |

### 9.2 Outreach Tracking Dashboard

**Metrics to Track**:
- Outreach emails sent: 50 (to get 20 responses at 40% response rate)
- Screening calls scheduled: 20
- Screening calls completed: 18 (90% show-up rate)
- Qualified candidates (≥60 points): 12 (67% qualification rate)
- Onboarded partners: 6 (50% conversion from qualified)

**Funnel**:
```
50 Outreach Emails
  ↓ (40% response rate)
20 Responses
  ↓ (90% show-up rate)
18 Screening Calls
  ↓ (67% qualification rate)
12 Qualified Candidates
  ↓ (50% onboarding rate)
6 Onboarded Partners
```

### 9.3 Partner Onboarding Checklist

**Pre-Onboarding** (Week before Sprint 42):
- [ ] NDA signed (both parties)
- [ ] Slack channel created: #design-partner-[company]
- [ ] Calendar invites sent: Bi-weekly feedback calls (3 calls)
- [ ] Access credentials sent: Dashboard login, API key
- [ ] Onboarding doc shared: Setup guide, FAQs

**Week 1 (Sprint 42 - Jan 20-24)**:
- [ ] Kickoff call (60 min): Product walkthrough, setup assistance
- [ ] GitHub integration completed (connect repo)
- [ ] First policy pack applied (AI-recommended or manual)
- [ ] First AI PR analyzed (validation pipeline triggered)
- [ ] Support check-in (Day 3): "Any blockers?")

**Week 2 (Sprint 42 - Jan 27-31)**:
- [ ] First feedback call (30 min): What's working, what's not
- [ ] Bug reports addressed (P0 within 24h, P1 within 48h)
- [ ] Workshop attendance (90 min): "AI Safety for Engineering Teams"

**Week 3-4 (Sprint 43 - Feb 3-14)**:
- [ ] Second feedback call (30 min): Feature requests, UX issues
- [ ] Metrics collection: Before/after DORA metrics
- [ ] Third feedback call (30 min): Wrap-up, case study discussion

**Post-Pilot**:
- [ ] NPS survey sent (0-10 scale)
- [ ] Case study interview scheduled (if partner agrees)
- [ ] Transition plan: Extend pilot or convert to paid (when GA)

### 9.4 Red Flags (Disqualify Immediately)

**Red Flag 1: No AI Tool Usage**
- "We're planning to adopt AI tools in the future."
- **Action**: Politely decline, revisit in 6 months.

**Red Flag 2: Solo Founder / 1-Person Team**
- Can't validate team collaboration features.
- **Action**: Waitlist for MVP v2 (individual plan).

**Red Flag 3: No Decision Maker**
- Contact is IC (Individual Contributor), not CTO/VP Eng/Manager.
- **Action**: Ask for intro to decision maker, otherwise decline.

**Red Flag 4: "Just Curious" / No Pain**
- Scored 0-5 on AI Governance Pain.
- **Action**: Keep in CRM for future, focus on pain-driven partners first.

**Red Flag 5: Can't Commit to Calls**
- "We're too busy for regular calls, just async feedback."
- **Action**: Decline, explain bi-weekly calls are core requirement.

**Red Flag 6: Competitor**
- Building competing SDLC governance tool.
- **Action**: Politely decline, NDA risk too high.

### 9.5 Partner Success Stories (Hypothetical Examples)

**Case Study 1: Acme FinTech (Tier 1 Partner)**

**Before SDLC Orchestrator**:
- 30% of AI-generated PRs required rework (failed code review)
- 1 production incident per month from AI code (avg cost: $5K/incident)
- No audit trail for compliance (PCI-DSS audit finding)

**After SDLC Orchestrator (6 weeks)**:
- AI PR rework rate: 30% → 8% (-73%)
- Production incidents: 1/month → 0/month (-100%)
- Compliance: Full evidence trail, passed PCI-DSS audit
- ROI: Saved $30K/year in incident costs + audit penalties

**Quote**: "SDLC Orchestrator gave us confidence to embrace AI tools without sacrificing quality. Our CTO sleeps better knowing every AI PR is validated against our architecture policies." - [CTO Name], Acme FinTech

---

**Case Study 2: BetaStartup SaaS (Tier 2 Partner)**

**Before SDLC Orchestrator**:
- No standardized code review process for AI PRs
- Test coverage: 65% (inconsistent across AI vs human code)
- Deploy frequency: 5/week (slow due to manual review bottleneck)

**After SDLC Orchestrator (6 weeks)**:
- Automated validation pipeline: 100% of AI PRs validated
- Test coverage: 65% → 82% (+17pp) [Policy Guard enforces 80% min]
- Deploy frequency: 5/week → 8/week (+60%) [Faster reviews, fewer reworks]

**Quote**: "As a lean startup, we can't afford dedicated QA. SDLC Orchestrator acts as our AI code quality gate, letting us move fast without breaking things." - [Eng Manager Name], BetaStartup

---

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | Dec 20, 2025 | Product Team | Initial version - 7-criteria scorecard |

---

**Status**: ✅ **DESIGN APPROVED**
**Next Step**: Sourcing (Sprint 41 Week 2 - Jan 13-17, 2026)
**Owner**: Product Team (sourcing) + Customer Success (onboarding)
**Review**: CTO approval required before outreach begins

---

*SDLC Orchestrator - Design Partner Scorecard v1.0. Quality over quantity. Engaged partners over vanity metrics.*
