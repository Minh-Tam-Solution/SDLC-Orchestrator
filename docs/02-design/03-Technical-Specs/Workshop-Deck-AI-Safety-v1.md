# Workshop: "AI Safety for Engineering Teams"
## 90-Minute Workshop Deck Structure & Content Outline

**Document ID**: TECH-SPEC-2026-005
**Version**: 1.0.0
**Status**: ✅ DESIGN APPROVED
**Created**: December 20, 2025
**Sprint**: Sprint 41 - AI Safety Foundation (Week 2)
**Framework**: SDLC 5.1.1 Complete Lifecycle
**Owner**: Product Team + CTO

---

## 📋 Table of Contents

1. [Executive Summary](#executive-summary)
2. [Workshop Overview](#workshop-overview)
3. [Learning Objectives](#learning-objectives)
4. [Deck Structure (25 Slides)](#deck-structure-25-slides)
5. [Slide-by-Slide Content](#slide-by-slide-content)
6. [Facilitator Guide](#facilitator-guide)
7. [Interactive Activities](#interactive-activities)
8. [Post-Workshop Materials](#post-workshop-materials)
9. [Appendix](#appendix)

---

## 1. Executive Summary

### 1.1 Purpose

This document defines the structure and content for the **"AI Safety for Engineering Teams"** workshop, a 90-minute interactive session designed to educate Design Partners on AI code governance best practices and introduce SDLC Orchestrator's AI Safety Layer capabilities.

### 1.2 Target Audience

**Primary**: Engineering Leaders (CTOs, VP Eng, Engineering Managers)
**Secondary**: Senior Engineers, Tech Leads, DevOps/SRE Teams

**Audience Profile**:
- Using AI coding tools (Cursor, Copilot, Claude Code) with ≥30% of team
- Experiencing or concerned about AI code quality issues
- Responsible for architecture, compliance, or code quality standards
- Decision makers for tooling adoption

### 1.3 Success Criteria

```yaml
Sprint 42 (First Workshop - Jan 24, 2026):
  ✅ Attendance: ≥4 Design Partners
  ✅ Engagement: ≥80% participation in interactive activities
  ✅ Satisfaction: ≥4.5/5 post-workshop survey
  ✅ Conversion: ≥2 partners request immediate onboarding

Sprint 43 (Second Workshop - Feb 7, 2026):
  ✅ Attendance: ≥6 Design Partners
  ✅ Testimonials: ≥2 LinkedIn posts from attendees
  ✅ Referrals: ≥1 new lead generated from attendees
```

---

## 2. Workshop Overview

### 2.1 Workshop Details

**Title**: "AI Safety for Engineering Teams: How to Govern AI-Generated Code Without Killing Velocity"

**Duration**: 90 minutes
- Presentation: 50 minutes
- Interactive activities: 25 minutes
- Q&A: 15 minutes

**Format**: Hybrid (Zoom + In-Person option for Vietnam-based partners)

**Delivery Schedule**:
- **Workshop 1**: Sprint 42, Week 1 (Jan 24, 2026) - 2:00 PM GMT+7
- **Workshop 2**: Sprint 43, Week 1 (Feb 7, 2026) - 2:00 PM GMT+7
- **On-Demand**: Recorded version available post-workshop

### 2.2 Workshop Positioning

**Problem Statement**:
"Your team adopted Cursor, Copilot, or Claude Code to move faster. But now you're worried: Is AI code safe? Does it follow our architecture? Can we prove compliance?"

**Promise**:
"In 90 minutes, you'll learn a proven framework to govern AI code without slowing down your team—plus see how SDLC Orchestrator automates this framework."

**Not a Sales Pitch**:
- 70% education (framework, best practices, industry trends)
- 20% demonstration (SDLC Orchestrator live demo)
- 10% call-to-action (Design Partner invitation)

### 2.3 Desired Outcomes

**For Attendees**:
1. **Awareness**: Understand AI code governance risks (security, architecture drift, compliance)
2. **Knowledge**: Learn 4-layer AI Safety framework (Detection → Validation → Policy → Evidence)
3. **Confidence**: Feel equipped to implement AI governance in their teams
4. **Interest**: Want to explore SDLC Orchestrator for their organization

**For SDLC Orchestrator**:
1. **Pipeline**: ≥3 qualified leads from each workshop
2. **Credibility**: Establish thought leadership in AI Safety space
3. **Feedback**: Gather insights on pain points, feature priorities
4. **Community**: Build engaged community of AI governance practitioners

---

## 3. Learning Objectives

### 3.1 By the End of This Workshop, Attendees Will Be Able To:

**LO1: Identify AI Code Risks**
- List ≥5 common AI-generated code issues (security, architecture, quality)
- Explain why "just code review" is insufficient for AI code governance

**LO2: Apply 4-Layer AI Safety Framework**
- Describe the 4 layers: Detection, Validation, Policy Enforcement, Evidence Trail
- Map each layer to specific tools/practices (e.g., OPA for policies, SAST for validation)

**LO3: Design AI Governance Policies**
- Write 3 example OPA policies for their codebase (e.g., "No AI in auth modules")
- Understand policy classification (Mandatory vs Recommended vs Optional)

**LO4: Evaluate AI Safety Tools**
- Assess SDLC Orchestrator against 5 criteria (accuracy, latency, coverage, compliance, UX)
- Decide if Design Partner program is a fit for their team

---

## 4. Deck Structure (25 Slides)

### 4.1 Slide Overview

| # | Section | Slide Count | Duration |
|---|---------|-------------|----------|
| **Part 1: The Problem** | Opening, Pain Points, Real Incidents | 5 slides | 12 min |
| **Part 2: The Framework** | 4-Layer AI Safety Framework | 8 slides | 25 min |
| **Part 3: The Solution** | SDLC Orchestrator Demo | 6 slides | 20 min |
| **Part 4: Interactive** | Poll, Q&A, Case Study Workshop | 4 slides | 25 min |
| **Part 5: Close** | Recap, CTA, Resources | 2 slides | 8 min |
| **TOTAL** | | **25 slides** | **90 min** |

---

## 5. Slide-by-Slide Content

### PART 1: THE PROBLEM (Slides 1-5, 12 minutes)

---

#### Slide 1: Title Slide

**Visual**: Bold title on clean background, SDLC Orchestrator logo

**Text**:
```
AI Safety for Engineering Teams
How to Govern AI-Generated Code Without Killing Velocity

Speaker: [CTO Name / Product Lead]
Company: SDLC Orchestrator
Date: [Workshop Date]
Duration: 90 minutes
```

**Speaker Notes**:
- Welcome attendees, introduce yourself (30 sec)
- Set expectations: "This is 70% education, 20% demo, 10% pitch. You'll leave with a framework you can apply even if you never use our tool."
- Housekeeping: Cameras on encouraged, questions in chat, poll coming soon

---

#### Slide 2: Poll - "How AI-Native Is Your Team?"

**Visual**: Interactive poll (Zoom or Slido)

**Poll Question**: "What % of your engineering team uses AI coding tools (Cursor, Copilot, Claude Code, ChatGPT)?"

**Options**:
- A) 0-10% (Just experimenting)
- B) 10-30% (Early adopters)
- C) 30-60% (Majority using)
- D) 60%+ (AI-native team)

**Speaker Notes**:
- Launch poll, give 30 seconds to respond
- Share results: "Great, I see [X%] of you have teams that are 30%+ AI-native. This workshop is perfect for you."
- Transition: "Let's talk about why AI code governance matters..."

---

#### Slide 3: The AI Coding Revolution

**Visual**: Timeline graphic showing AI tool adoption curve

**Text**:
```
2021: GitHub Copilot launches → 1M users in 6 months
2023: Cursor, Claude Code, ChatGPT Code Interpreter → 10M+ developers
2025: 60% of professional developers use AI coding tools (Stack Overflow Survey)

The question isn't "Should we use AI?"
The question is "How do we use AI SAFELY?"
```

**Statistics** (in smaller text):
- 40% faster coding (GitHub Copilot study)
- 55% higher job satisfaction (happier devs)
- BUT: 3x higher defect rate if ungoverned (Google Research, 2024)

**Speaker Notes**:
- "Raise your hand if your team's velocity increased after adopting AI tools." [Pause for hands]
- "Now keep your hand up if you've also seen an AI-generated bug reach production." [Some hands drop]
- "This is the paradox: AI makes us faster, but introduces new risks."

---

#### Slide 4: The Dark Side of AI Code (Real Incidents)

**Visual**: 3-column layout with incident cards

**Incident 1: Security Vulnerability**
```
🔴 CRITICAL
Company: [Anonymized Fintech Startup]
Issue: AI-generated code hardcoded API key in commit
Impact: $50K penalty (PCI-DSS violation), 2 weeks incident response
Root Cause: No secret scanning, dev copy-pasted AI suggestion
```

**Incident 2: Architecture Drift**
```
🟠 HIGH
Company: [Anonymized E-commerce Platform]
Issue: AI rewrote auth module using deprecated library
Impact: 3 days rollback, $20K lost revenue (checkout broken)
Root Cause: AI trained on old StackOverflow answers, no architecture validation
```

**Incident 3: Compliance Failure**
```
🟡 MEDIUM
Company: [Anonymized Healthcare SaaS]
Issue: No audit trail for AI-generated HIPAA-critical code
Impact: SOC 2 audit finding, 6 months to remediate
Root Cause: No evidence tracking, can't prove code review rigor
```

**Speaker Notes**:
- "These aren't hypothetical. These happened to real teams in 2024-2025."
- "The common thread? Speed without safety. Fast code that breaks things."
- "Let's talk about what went wrong, and how to prevent this..."

---

#### Slide 5: The Cost of Ungoverned AI Code

**Visual**: Bar chart comparing costs

**Chart**:
```
Average cost per AI code incident:
- Security breach: $50K - $500K (IBM Cost of Data Breach Report)
- Architecture rework: $10K - $100K (developer time + lost revenue)
- Compliance penalty: $5K - $1M (SOC 2, HIPAA, PCI-DSS)

vs.

Cost of AI Safety tooling: $300 - $1000/month
ROI: 50x - 1000x (prevent 1 incident → tool pays for itself for 5 years)
```

**Speaker Notes**:
- "Here's the business case for AI governance in one slide."
- "A single security breach from AI code costs $50K on average. Our tool costs $500/month."
- "That's 100 months of protection for the cost of one incident."
- Transition: "So how do we prevent these incidents? Let me show you a framework..."

---

### PART 2: THE FRAMEWORK (Slides 6-13, 25 minutes)

---

#### Slide 6: The 4-Layer AI Safety Framework

**Visual**: Pyramid diagram with 4 layers

```
┌─────────────────────────────────────────────┐
│  LAYER 4: EVIDENCE TRAIL                   │  ← Compliance, Audit, Traceability
├─────────────────────────────────────────────┤
│  LAYER 3: POLICY ENFORCEMENT               │  ← Block risky AI code
├─────────────────────────────────────────────┤
│  LAYER 2: VALIDATION PIPELINE              │  ← Lint, Test, Coverage, Security
├─────────────────────────────────────────────┤
│  LAYER 1: AI CODE DETECTION                │  ← Identify which PRs used AI
└─────────────────────────────────────────────┘
```

**Speaker Notes**:
- "This is the framework we'll walk through. 4 layers, each builds on the previous."
- "Layer 1: You can't govern what you can't see. First, detect AI code."
- "Layer 2: Validate it. Does it pass tests? Is it secure?"
- "Layer 3: Enforce policies. Does it follow our architecture?"
- "Layer 4: Leave an audit trail. Can we prove compliance?"

---

#### Slide 7: Layer 1 - AI Code Detection

**Visual**: 3 detection methods with accuracy badges

**Text**:
```
Challenge: How do you know which PRs used AI tools?

3 Detection Strategies:

1️⃣ Metadata Analysis (~70% accuracy)
   - PR title: "feat: add login via Copilot"
   - Commit messages: "Generated by Cursor"
   - Comment patterns: AI tools leave signatures

2️⃣ GitHub API (~85% accuracy)
   - GitHub Copilot metadata in PR
   - Committer email: cursor@*.com
   - Labels: ai-generated, copilot

3️⃣ Manual Tagging (100% accuracy)
   - Developer adds label: "AI-assisted"
   - Enforced via PR template

✅ Best Practice: Combine all 3 → 85%+ accuracy
```

**Speaker Notes**:
- "You might think 'just ask developers to tag PRs.' But humans forget. We need automated detection."
- "Metadata analysis: Look for keywords in PR titles, commits. Works ~70% of the time."
- "GitHub API: Some tools (like Copilot) expose metadata. More reliable, ~85%."
- "Manual: Always provide fallback for devs to self-report."
- "Combine all 3 → 85%+ accuracy. Good enough for production."

---

#### Slide 8: Layer 2 - Validation Pipeline

**Visual**: Flowchart showing validation steps

**Text**:
```
Once AI code is detected → Run automated validation:

┌─────────────┐
│  AI PR      │
│  Detected   │
└──────┬──────┘
       │
       ├─→ Linter (ESLint, Ruff, Prettier)
       │     ✅ Pass / ❌ Fail
       │
       ├─→ Test Runner (pytest, jest)
       │     ✅ 100% pass / ❌ 2 failures
       │
       ├─→ Coverage Check (≥80% target)
       │     ✅ 85% / ❌ 72%
       │
       ├─→ Security Scan (Semgrep, Snyk)
       │     ✅ 0 critical / ❌ 3 high vulns
       │
       └─→ Architecture Check (OPA policies)
             ✅ Compliant / ❌ Violates policy #42

Performance Budget: <6 minutes p95 (parallel execution)
```

**Speaker Notes**:
- "This is standard CI/CD, but applied specifically to AI PRs."
- "Why separate pipeline? Because AI code has different risk profile. You want extra scrutiny."
- "Run these in parallel. With Celery or GitHub Actions, this takes <6 minutes."
- "If ANY validator fails → block merge. No exceptions (unless VCR override, we'll get to that)."

---

#### Slide 9: Layer 3 - Policy Enforcement (OPA)

**Visual**: Code snippet showing OPA policy

**Text**:
```
Challenge: How do you encode "AI can't touch auth modules" as code?

Answer: Policy-as-Code (Open Policy Agent - OPA)

Example Policy (Rego language):

package ai_safety.critical_paths

# No AI-generated code in authentication modules
deny[msg] {
    input.files_changed[_] contains "/auth/"
    input.ai_generated == true
    msg := "❌ AI code not allowed in authentication modules"
}

# Require ≥2 human reviews for database migrations
deny[msg] {
    input.files_changed[_] contains "migrations/"
    input.human_review_count < 2
    msg := "❌ Database migrations require ≥2 human reviews"
}
```

**Speaker Notes**:
- "This is where the magic happens. You encode your team's rules as policies."
- "Example: 'No AI in auth modules.' In Rego (OPA language), that's 5 lines."
- "OPA evaluates this policy for every AI PR. If it fails → PR is blocked."
- "You can have 100+ policies. SDLC Orchestrator comes with 110 starter policies."

---

#### Slide 10: Policy Guard in Action (Demo Screenshot)

**Visual**: Screenshot of GitHub PR with Policy Guard comment

**Screenshot**:
```
GitHub PR #42: "Implement user login via Cursor"

🤖 SDLC Orchestrator Policy Guard
❌ PR BLOCKED - Policy Violations Found

┌─────────────────────────────────────────────────┐
│  ❌ MANDATORY POLICY FAILED                     │
│  Policy: no_ai_in_auth_modules                  │
│  Reason: AI code not allowed in authentication  │
│  Files: backend/app/api/routes/auth.py          │
│                                                  │
│  📖 Learn more: docs/policies/critical-paths.md │
│  🔓 VCR Override: Request approval from CTO     │
└─────────────────────────────────────────────────┘

✅ All other checks passed:
  ✅ Linter: Passed
  ✅ Tests: 42/42 passed
  ✅ Coverage: 87% (target: 80%)
  ✅ Security: 0 vulnerabilities
```

**Speaker Notes**:
- "This is what your developers see when a policy fails."
- "Clear message: WHY it failed, WHICH files, HOW to fix (link to docs)."
- "VCR Override: Sometimes you need to break the rules. CTO can approve exceptions."
- "But by default? Blocked. AI can't merge until policy passes."

---

#### Slide 11: Layer 4 - Evidence Trail

**Visual**: Timeline UI showing evidence history

**Text**:
```
Challenge: "Prove that all AI code was reviewed and validated."

Solution: Immutable Evidence Vault

What We Store:
  ✅ PR metadata (author, timestamp, AI tool used)
  ✅ Detection results (confidence score, method)
  ✅ Validation results (lint, tests, coverage, SAST)
  ✅ Policy evaluation (pass/fail, which policies)
  ✅ Code review comments (human reviewers)
  ✅ VCR overrides (who approved, why)

Storage: MinIO S3 + PostgreSQL (SHA256 integrity checks)
Retention: 2 years active, 5 years archive (compliance-ready)
Access: Audit UI, CSV export, API (for SOC 2/HIPAA audits)
```

**Speaker Notes**:
- "If you're in Fintech, Healthcare, or any regulated industry, this is gold."
- "Auditor asks: 'Prove this AI-generated code was reviewed.' You pull up the evidence timeline."
- "Every step logged: Detection → Validation → Policy → Approval. Immutable."
- "This is what separates SDLC Orchestrator from 'just use GitHub Actions.' We're compliance-first."

---

#### Slide 12: Framework Summary (The Whole Picture)

**Visual**: Diagram showing all 4 layers integrated

**Text**:
```
AI PR Workflow with 4-Layer Safety:

Developer creates PR (using Cursor/Copilot)
        ↓
Layer 1: AI Detection Service
   → "This PR used Cursor (87% confidence)"
        ↓
Layer 2: Validation Pipeline
   → Lint ✅, Tests ✅, Coverage ✅, SAST ✅
        ↓
Layer 3: Policy Guard (OPA)
   → Evaluate 110 policies
   → ❌ BLOCKED: "AI not allowed in /auth/"
        ↓
Layer 4: Evidence Vault
   → Store: PR + Detection + Validation + Policy results
   → Generate audit report
        ↓
Developer fixes issue OR requests VCR override
   → CTO approves → PR merges
```

**Speaker Notes**:
- "This is the end-to-end flow. From PR creation to merge (or block)."
- "Each layer is independent. You can implement Layer 1-2 without Layer 3-4."
- "But together? That's where you get comprehensive AI Safety."

---

#### Slide 13: Interactive Activity - "Write Your First Policy"

**Visual**: Editable text box (Google Doc or Miro board link)

**Activity**:
```
🛠️ Hands-On: Write an AI Safety Policy for Your Team

Scenario: Your team uses Cursor heavily. You're concerned about:
  1. AI code in payment processing modules
  2. AI-generated database migrations
  3. AI code without test coverage

Task (5 minutes):
  - Pick 1 scenario
  - Write a policy in plain English (we'll translate to OPA later)
  - Share in chat or Google Doc

Example Policy:
  "No AI-generated code is allowed in /payments/ directory without CTO approval."

Bonus:
  - What's the enforcement action? (Block merge / Require review / Warning only)
  - Who can override? (CTO / Tech Lead / No overrides)
```

**Speaker Notes**:
- "Let's make this practical. Open the Google Doc link in chat."
- "Take 5 minutes. Write 1 policy for your team. Doesn't have to be perfect."
- [After 5 min] "Great, I see some excellent policies. Let's review 2-3..."
- [Read 2-3 policies from chat/doc, give feedback]
- "See how easy this is? That's the power of Policy-as-Code."

---

### PART 3: THE SOLUTION (Slides 14-19, 20 minutes)

---

#### Slide 14: Introducing SDLC Orchestrator

**Visual**: Product logo + tagline

**Text**:
```
SDLC Orchestrator
The Control Plane for AI-Generated Code

Tagline: "The platform that keeps Cursor/Copilot/Claude Code compliant
         with your architecture and standards."

What We Do:
  ✅ Automatically detect AI PRs (85%+ accuracy)
  ✅ Validate against your quality standards (lint, tests, security)
  ✅ Enforce architecture policies (OPA-based Policy Guards)
  ✅ Maintain audit trail (compliance-ready Evidence Vault)

What We Don't Do:
  ❌ Replace GitHub/GitLab (we integrate, not replace)
  ❌ Replace CI/CD (we orchestrate, not re-implement)
  ❌ Block all AI code (we govern, not ban)
```

**Speaker Notes**:
- "That framework I just showed? SDLC Orchestrator automates all 4 layers."
- "We're a bridge-layer tool. We sit between your AI tools and your repo."
- "Think of us as 'Policy-as-Code for AI tools.'"

---

#### Slide 15: Product Demo - Part 1 (Dashboard)

**Visual**: Screenshot of SDLC Orchestrator dashboard

**Screenshot**:
```
Dashboard: "AI Safety Overview"

┌──────────────────────────────────────────────────────────┐
│  📊 Last 7 Days                                          │
├──────────────────────────────────────────────────────────┤
│  AI PRs Detected: 42                                     │
│  Policy Guards Triggered: 38 (90%)                       │
│  Policy Blocked: 3 (7%)                                  │
│  VCR Overrides: 1 (2%)                                   │
│  Validation Pass Rate: 88%                               │
├──────────────────────────────────────────────────────────┤
│  🔥 Top Policy Violations (Last 30 Days)                 │
│  1. no_ai_in_auth_modules: 5 blocks                      │
│  2. require_80_percent_coverage: 3 blocks                │
│  3. no_hardcoded_secrets: 2 blocks                       │
├──────────────────────────────────────────────────────────┤
│  🏆 Most Active AI Tools                                 │
│  1. Cursor: 22 PRs (52%)                                 │
│  2. Copilot: 15 PRs (36%)                                │
│  3. Claude Code: 5 PRs (12%)                             │
└──────────────────────────────────────────────────────────┘
```

**Speaker Notes**:
- "This is what your CTO sees. Real-time AI Safety dashboard."
- "Notice: 42 AI PRs detected, only 3 blocked. We're not killing velocity."
- "Top violations? AI trying to touch auth modules. That's our policy working."

---

#### Slide 16: Product Demo - Part 2 (Evidence Timeline)

**Visual**: Screenshot of Evidence Timeline UI

**Screenshot**:
```
PR #42: "Implement user login via Cursor"

Evidence Timeline:

🕐 2026-01-24 10:30 - PR Created
   Author: john_doe
   Branch: feature/auth-login

🕐 10:32 - AI Detection (87% confidence)
   Tool: Cursor
   Model: GPT-4
   Method: Combined (metadata + GitHub API)

🕐 10:35 - Validation Started
   Validators: Lint, Tests, Coverage, SAST

🕐 10:38 - Validation Complete
   ✅ Lint: Passed
   ✅ Tests: 42/42 passed
   ✅ Coverage: 87%
   ✅ SAST: 0 vulnerabilities

🕐 10:40 - Policy Evaluation
   Evaluated: 110 policies
   ❌ FAILED: no_ai_in_auth_modules

🕐 11:15 - VCR Override Requested
   Requester: john_doe
   Reason: "Auth refactor approved in design doc"

🕐 11:45 - VCR Override Approved
   Approver: CTO (Jane Smith)
   Comment: "Approved per ADR-042"

🕐 11:50 - PR Merged
   SHA: a1b2c3d4
```

**Speaker Notes**:
- "This is the compliance magic. Every step logged, immutable."
- "Auditor asks 'Was this PR reviewed?' You show this timeline."
- "Notice the VCR override. Developer made the case, CTO approved. All documented."

---

#### Slide 17: Product Demo - Part 3 (Policy Editor)

**Visual**: Screenshot of Policy Editor UI

**Screenshot**:
```
Policy Editor: "Create New Policy"

┌────────────────────────────────────────────────────────┐
│  Policy Name: no_ai_in_payments_module                │
├────────────────────────────────────────────────────────┤
│  Classification: ● MANDATORY  ○ RECOMMENDED  ○ OPTIONAL│
├────────────────────────────────────────────────────────┤
│  Scope: All Projects  ▼                                │
├────────────────────────────────────────────────────────┤
│  Condition (Rego):                                     │
│  ┌────────────────────────────────────────────────┐  │
│  │ package ai_safety.payments                      │  │
│  │                                                 │  │
│  │ deny[msg] {                                     │  │
│  │     input.files_changed[_] contains "/payments/"│  │
│  │     input.ai_generated == true                  │  │
│  │     msg := "AI code not allowed in /payments/"  │  │
│  │ }                                               │  │
│  └────────────────────────────────────────────────┘  │
├────────────────────────────────────────────────────────┤
│  VCR Override Allowed: ✅ Yes (Requires CTO approval)  │
├────────────────────────────────────────────────────────┤
│  [Test Policy]  [Save Draft]  [Publish Policy]        │
└────────────────────────────────────────────────────────┘
```

**Speaker Notes**:
- "You don't need to be an OPA expert. Our UI guides you."
- "Pick a template (we have 110 starter policies), customize, publish."
- "Test it first on historical PRs. See what would've been blocked."

---

#### Slide 18: Why SDLC Orchestrator vs DIY

**Visual**: Comparison table

**Text**:
```
"Can't I just build this with GitHub Actions + OPA?"

| Feature | DIY (GH Actions + OPA) | SDLC Orchestrator |
|---------|------------------------|-------------------|
| Setup Time | 2-4 weeks (eng effort) | <30 min (wizard) |
| AI Detection | Manual (write custom scripts) | Automated (3 strategies) |
| Policy Library | 0 (write from scratch) | 110 starter policies |
| Evidence Vault | DIY (S3 + DB schema) | Built-in (compliance-ready) |
| VCR Override Flow | Custom UI | Built-in approval workflow |
| Support | StackOverflow | Dedicated Slack + CSM |
| Maintenance | You own it | We maintain it |
| Cost | Engineer time ($10K+) | $500/month |

✅ Use DIY if: You have 2 weeks + 2 engineers to build custom solution
✅ Use SDLC Orchestrator if: You want to ship this week, not next month
```

**Speaker Notes**:
- "Fair question. You CAN build this yourself. BFlow did (took 6 weeks)."
- "But time-to-value matters. With us? 30 minutes to first policy enforcement."
- "Plus: We maintain it. When OPA updates, GitHub API changes, we handle it."

---

#### Slide 19: Pricing & Plans

**Visual**: 3-column pricing table

**Text**:
```
| Tier | Free | Team | Enterprise |
|------|------|------|------------|
| **Price** | $0 | $149/mo | Custom |
| **Projects** | 1 | 5 | Unlimited |
| **Policies** | 5 rules | 50+ rules | Custom |
| **AI Safety** | 2 devs max | Full v1 | Full + Self-hosted |
| **Support** | Community | Email | Dedicated CSM |
| **Evidence Vault** | 30 days | 2 years | Unlimited |

✨ Design Partner Offer (Limited - 6 Spots):
  - 6-9 months FREE (Team tier, $900+ value)
  - Dedicated Slack support (<2h response time)
  - Grandfathered pricing (lock in $149/mo when GA)
  - Co-marketing opportunity (case study, logo)
```

**Speaker Notes**:
- "Free tier: Perfect for solo devs, indie hackers. Try it risk-free."
- "Team tier: Most startups, scale-ups. $149/mo = cost of 1 incident prevented."
- "Enterprise: For regulated industries (Fintech, Healthcare), self-hosted option."
- Transition: "Now, I promised this isn't a sales pitch. Let me show you the Design Partner offer..."

---

### PART 4: INTERACTIVE (Slides 20-23, 25 minutes)

---

#### Slide 20: Case Study Workshop - "Diagnose This Incident"

**Visual**: Incident report card

**Activity**:
```
🔍 Group Activity: Root Cause Analysis (10 minutes)

Incident Report:
  Company: [Anonymized Fintech]
  Date: Nov 12, 2024
  Severity: P0 (Critical)

  Incident:
    - Developer used Copilot to generate payment processing code
    - AI code hardcoded Stripe API key in source file
    - Key committed to GitHub repo (public)
    - Key discovered by external security researcher
    - $50K security audit + $10K Stripe key rotation

  Developer Quote: "I didn't notice. I just copy-pasted the Copilot suggestion."

Discussion Questions (Breakout rooms - 5 min):
  1. Which of the 4 layers would have prevented this?
  2. What policy would you write?
  3. How would you train developers to avoid this?

Report Back (5 min):
  - Each group shares 1 key insight
```

**Speaker Notes**:
- "Let's make this real. Break into groups of 3-4 (Zoom breakout rooms)."
- "Read the incident, discuss 3 questions. 5 minutes."
- [After 5 min] "Welcome back. Group 1, what layer would've prevented this?"
- [Facilitate discussion, highlight good insights]
- "Correct answer: Layer 2 (SAST would've caught hardcoded secret) + Layer 3 (Policy: no secrets in code)."

---

#### Slide 21: Poll - "Will You Implement AI Safety?"

**Visual**: Poll question with 5 options

**Poll**:
```
After today's workshop, what's your next step?

A) Implement DIY AI Safety (GH Actions + OPA)
B) Evaluate SDLC Orchestrator (request demo)
C) Join Design Partner Program (if qualified)
D) Not ready yet (will revisit in 6 months)
E) Not interested (AI Safety not a priority)
```

**Speaker Notes**:
- "Quick poll before we wrap up. What's YOUR next step?"
- [Give 30 sec to respond]
- "Interesting! I see [X%] want to evaluate us, [Y%] will DIY. Both great choices."
- "For those who picked C (Design Partner), stay on the line after. I have a special invite."

---

#### Slide 22: Q&A - Common Questions

**Visual**: FAQ accordion (expand on click)

**Text**:
```
❓ Frequently Asked Questions:

Q: "Will this slow down my team?"
A: No. Validation runs in parallel (<6 min p95). Policy evaluation is <100ms.
   Only blocks if MANDATORY policy fails (you control which policies).

Q: "What if AI detection is wrong (false positive)?"
A: Manual override available. Developer can tag PR as "not AI" if mislabeled.

Q: "Does this work with GitLab / Bitbucket?"
A: GitHub-first in Q1 2026. GitLab support coming Q2 2026.

Q: "Can I customize policies for different teams?"
A: Yes. Policies can be project-scoped or team-scoped.

Q: "What if I use Claude Code / ChatGPT (not Copilot)?"
A: We detect all major tools: Cursor, Copilot, Claude Code, ChatGPT.
   Detection method: metadata + manual tagging.

Q: "How do you handle secret scanning?"
A: Layer 2 includes Semgrep (open-source SAST). Detects 100+ secret patterns.

Q: "Is this GDPR / SOC 2 compliant?"
A: Yes. Evidence Vault is audit-ready. EU data residency available (Enterprise).
```

**Speaker Notes**:
- "Let's open the floor for questions. Type in chat or unmute."
- [Answer 3-5 questions live, refer to FAQ for others]
- "Great questions. I'll share this FAQ deck after the call."

---

#### Slide 23: Live Q&A (Open Discussion)

**Visual**: "Q&A" text on simple background

**Speaker Notes**:
- "Any other questions? Now's the time."
- [Answer questions for 10-15 minutes]
- [If no questions] "No questions? That means I explained it well... or you're all too polite!" [Laugh]

---

### PART 5: CLOSE (Slides 24-25, 8 minutes)

---

#### Slide 24: Recap - Key Takeaways

**Visual**: Numbered list with icons

**Text**:
```
🎯 What You Learned Today:

1️⃣ The Problem: AI code is 3x riskier if ungoverned (security, architecture, compliance)

2️⃣ The Framework: 4-Layer AI Safety
   - Detection → Validation → Policy → Evidence

3️⃣ The Solution: SDLC Orchestrator automates all 4 layers
   - 85%+ AI detection accuracy
   - <6 min validation pipeline
   - 110 starter policies
   - Compliance-ready evidence vault

4️⃣ The Action: 3 ways to get started
   - DIY (GitHub Actions + OPA)
   - Try Free Tier (1 project, 5 policies)
   - Join Design Partner Program (6 spots, free for 6-9 months)
```

**Speaker Notes**:
- "Let's recap. You now understand the 4-layer framework."
- "You can implement this yourself (DIY) or use our platform."
- "Either way, you're better equipped to govern AI code than 99% of teams."

---

#### Slide 25: Call-to-Action - Design Partner Invitation

**Visual**: CTA button + contact info

**Text**:
```
🚀 Design Partner Program - 6 Spots Available

What You Get:
  ✅ 6-9 months FREE access (Team tier, $900+ value)
  ✅ Dedicated Slack support (<2h response time)
  ✅ Influence product roadmap (bi-weekly feedback calls)
  ✅ Grandfathered pricing when we GA launch
  ✅ Case study co-marketing (optional)

What We Need:
  ✅ 30-min bi-weekly calls (6 weeks)
  ✅ Share metrics (DORA, coverage, incidents)
  ✅ Patience with beta product (we'll fix bugs fast!)

Qualification:
  ✅ 10-50 engineers
  ✅ Using Cursor/Copilot/Claude Code (≥30% of team)
  ✅ Active development (≥5 PRs/week)
  ✅ CTO/VP Eng/Eng Manager willing to participate

Apply: [Typeform Link] or Email: partners@sdlcorchestrator.com
Deadline: Feb 1, 2026 (rolling basis)

Questions? Stay on the call. I'll open a breakout room for Design Partner Q&A.
```

**Speaker Notes**:
- "For those interested in Design Partner program, here's the deal."
- "6 spots available. First-come, first-served (but we do qualify)."
- "Apply via Typeform [show link in chat]. Takes 5 minutes."
- "Questions about the program? Stay on. I'll open a breakout room in 2 minutes."
- "For everyone else: Thank you for attending! Slides + recording will be emailed tomorrow."
- "Let's stay in touch. Connect with me on LinkedIn [show QR code]."

---

## 6. Facilitator Guide

### 6.1 Pre-Workshop Checklist (1 Week Before)

**Logistics**:
- [ ] Zoom meeting created (90 min duration, breakout rooms enabled)
- [ ] Calendar invites sent (include Zoom link, agenda, prep materials)
- [ ] Reminder emails scheduled (7 days before, 1 day before, 1 hour before)
- [ ] Slide deck finalized (Google Slides or PowerPoint)
- [ ] Demo environment prepared (staging instance, test data loaded)

**Interactive Tools**:
- [ ] Poll tool configured (Zoom Polls or Slido)
- [ ] Google Doc created for "Write Your First Policy" activity (editing permissions enabled)
- [ ] Miro board prepared for case study workshop (optional)
- [ ] Typeform created for Design Partner applications

**Team Roles**:
- [ ] Primary facilitator assigned (CTO or Product Lead)
- [ ] Co-facilitator assigned (handle chat, breakout rooms, tech issues)
- [ ] Notetaker assigned (capture questions, feedback, attendance)

### 6.2 Day-Of Checklist (1 Hour Before)

**Technical Setup**:
- [ ] Test Zoom audio/video (backup headset ready)
- [ ] Test screen sharing (slides + demo environment)
- [ ] Test polls (launch dry run)
- [ ] Test breakout rooms (pre-assign groups if >20 attendees)
- [ ] Open tabs: Slides, Demo, Google Doc, Typeform, LinkedIn
- [ ] Start recording (for on-demand version)

**Materials**:
- [ ] Slide deck open (presenter mode)
- [ ] Speaker notes visible (second monitor or printed)
- [ ] Backup slides (PDF export, in case Google Slides crashes)
- [ ] Water bottle nearby (you'll be talking for 90 minutes!)

### 6.3 Facilitation Tips

**Engagement Strategies**:
1. **Start with Poll** (Slide 2): Gets attendees active early, breaks ice
2. **Use Names**: "Great question, Sarah. Let me answer that..."
3. **Pause for Questions**: After each major section (Part 1, 2, 3), ask "Questions so far?"
4. **Encourage Chat**: "Don't wait for Q&A. Type questions in chat anytime."
5. **Acknowledge Contributors**: "Excellent policy, Ahmed. I love the specificity."

**Time Management**:
- **Part 1 (12 min)**: STRICTLY enforce. Problem awareness sets context, but don't linger.
- **Part 2 (25 min)**: This is the meat. Budget 6 min per layer + 1 min buffer.
- **Part 3 (20 min)**: Demo can run long. Set timer. Skip slides if needed.
- **Part 4 (25 min)**: Interactive is most valuable. Don't skip if running late—skip demo slides instead.
- **Part 5 (8 min)**: Recap fast. Spend time on CTA if attendees engaged.

**Handling Questions**:
- **Easy Questions**: Answer live (30 sec max)
- **Complex Questions**: "Great question. Let's take that offline. Email me."
- **Off-Topic Questions**: "Interesting, but outside scope. Let's chat after."
- **Repeated Questions**: "We covered this in Slide X. Check the recording."

### 6.4 Troubleshooting

**Issue: Low Attendance (<4 people)**
- **Action**: Still run workshop. Smaller group = more interactive, better feedback.
- **Bonus**: Can skip breakout rooms, do group discussion instead.

**Issue: Technical Failure (Zoom crash, demo breaks)**
- **Backup Plan**: Have PDF slides ready. If demo breaks, show screenshots instead of live demo.

**Issue: Dominant Participant (monopolizes Q&A)**
- **Action**: "Thanks, John. Let's hear from others. Anyone else have questions?"

**Issue: Silent Audience (no questions, no chat)**
- **Action**: Call on people. "Sarah, you work in Fintech. What resonates with you?"

---

## 7. Interactive Activities

### 7.1 Activity 1: "Write Your First Policy" (Slide 13)

**Objective**: Hands-on practice writing AI Safety policies in plain English

**Format**: Individual → Group Share

**Materials**:
- Google Doc (shared link in chat)
- Slide with example policy template

**Instructions** (5 minutes):
1. Facilitator: "Open the Google Doc link in chat."
2. Facilitator: "Pick 1 scenario: AI in payments, AI migrations, or AI without tests."
3. Facilitator: "Write 1 policy in plain English. 2-3 sentences."
4. Participants: Write policies in Google Doc
5. Facilitator: "Time's up! Let's review 2-3 policies together."

**Debrief** (3 minutes):
- Facilitator reads 2-3 standout policies from Google Doc
- Provides feedback: "Great specificity. Here's how this translates to OPA..."
- Encourages participants: "See? You just wrote your first AI Safety policy. That's all it takes."

**Expected Outcomes**:
- ≥50% of participants write at least 1 policy
- Participants understand policies are simple (not complex code)
- Participants feel confident they can implement this in their teams

---

### 7.2 Activity 2: "Diagnose This Incident" (Slide 20)

**Objective**: Apply 4-layer framework to real-world incident

**Format**: Breakout Rooms (3-4 people per room)

**Materials**:
- Incident report card (on slide)
- Discussion questions (on slide)

**Instructions** (10 minutes):
1. Facilitator: "I'm creating breakout rooms. 3-4 people per room."
2. Facilitator: "Read the incident. Discuss 3 questions. 5 minutes."
3. Participants: Breakout room discussions (5 min)
4. Facilitator: "Welcome back! Group 1, what layer would've prevented this?"
5. Groups: Share 1 key insight each (5 min)

**Debrief** (5 minutes):
- Facilitator synthesizes insights: "Most of you said Layer 2 (SAST) + Layer 3 (Policy). Correct!"
- Facilitator highlights training point: "Also, developer education. Teach devs to review AI suggestions, not blindly copy-paste."
- Facilitator transitions: "This is why AI Safety isn't just tooling. It's culture + tooling."

**Expected Outcomes**:
- Participants practice incident analysis
- Participants see how 4-layer framework prevents real incidents
- Participants recognize need for developer training (not just tools)

---

## 8. Post-Workshop Materials

### 8.1 Follow-Up Email (Sent Within 24 Hours)

**Subject**: "Thanks for attending 'AI Safety for Engineering Teams' + Resources"

**Body**:
```
Hi [First Name],

Thanks for attending yesterday's workshop on AI Safety! Here's what I promised to send:

📊 Workshop Materials:
  - Slides (PDF): [Link]
  - Recording (Zoom): [Link]
  - Google Doc ("Write Your First Policy"): [Link]

📚 Resources:
  - 4-Layer AI Safety Framework (blog post): [Link]
  - 110 Starter Policies (GitHub repo): [Link]
  - OPA Tutorial (for beginners): [Link]
  - Case Study: Acme FinTech (AI Safety ROI): [Link]

🚀 Next Steps:
  1. DIY Route: Fork our OPA policies repo, customize for your team
  2. Try Free Tier: Sign up at [app.sdlcorchestrator.com/signup]
  3. Join Design Partner Program: Apply at [Typeform link] (6 spots, deadline Feb 1)

Questions? Reply to this email or book a 15-min call: [Calendly link]

Best,
[Your Name]
[Title]
SDLC Orchestrator

P.S. We're running Workshop #2 on Feb 7, 2026. Know someone who'd benefit? Forward this invite: [Link]
```

---

### 8.2 Design Partner Application (Typeform)

**Form Fields**:

1. **Company Name** (Text)
2. **Your Name** (Text)
3. **Your Role** (Dropdown: CTO / VP Eng / Eng Manager / Tech Lead / Other)
4. **Email** (Email)
5. **Team Size** (Number: How many engineers?)
6. **AI Tool Usage** (Dropdown: 0-10% / 10-30% / 30-60% / 60%+)
7. **Primary AI Tool** (Multiple choice: Cursor / Copilot / Claude Code / ChatGPT / Other)
8. **Industry** (Dropdown: Fintech / Healthcare / SaaS / E-commerce / Other)
9. **Tech Stack** (Text: e.g., Python + TypeScript + React)
10. **Pain Point** (Long text: Describe your biggest AI code quality challenge)
11. **Commitment** (Checkbox: I can commit to 30-min bi-weekly calls for 6 weeks)
12. **Metrics** (Checkbox: I can share before/after metrics - DORA, coverage, incidents)
13. **Case Study** (Dropdown: Yes, I'm open to case study / Maybe / No)
14. **How did you hear about us?** (Dropdown: Workshop / LinkedIn / Referral / Other)

**Qualification Logic** (Backend):
- If Team Size < 10 OR AI Tool Usage < 30% → Waitlist
- If Role != CTO/VP Eng/Eng Manager → Ask for intro to decision maker
- If Commitment = Unchecked → Polite decline
- Otherwise → Schedule screening call

---

### 8.3 Post-Workshop Survey (Google Form)

**Survey Questions** (1-5 scale):

1. **Overall Satisfaction**: How valuable was this workshop? (1 = Not valuable, 5 = Extremely valuable)
2. **Content Quality**: The content was relevant to my role. (1 = Disagree, 5 = Agree)
3. **Facilitator**: The facilitator was engaging and knowledgeable. (1 = Disagree, 5 = Agree)
4. **Pace**: The workshop pace was appropriate. (1 = Too slow, 3 = Just right, 5 = Too fast)
5. **Interactive Activities**: The hands-on activities were useful. (1 = Disagree, 5 = Agree)
6. **Likelihood to Recommend**: Would you recommend this workshop to a colleague? (1 = No, 5 = Definitely)

**Open-Ended**:
7. What was the most valuable part of the workshop?
8. What could be improved for next time?
9. Any topics you'd like to see covered in future workshops?

**Success Threshold**: Avg score ≥4.5/5 on Q1 (Overall Satisfaction)

---

## 9. Appendix

### 9.1 Slide Deck Template (Download)

**File**: `Workshop-AI-Safety-Engineering-Teams-v1.0.pptx`

**Contents**:
- 25 slides (as outlined in Section 5)
- Brand colors: SDLC Orchestrator color palette
- Fonts: Inter (headings), Source Sans Pro (body)
- Image assets: Icons (Flaticon), diagrams (Excalidraw), screenshots (Staging)

**Export Formats**:
- PowerPoint (.pptx): For offline presenting
- Google Slides: For collaborative editing
- PDF: For email distribution

**Download**: [Link to Google Drive or GitHub repo]

---

### 9.2 Speaker Notes (Full Script)

**Purpose**: Backup script for facilitators (especially non-CTO presenters)

**Format**: Slide-by-slide script (verbatim)

**Example** (Slide 3):
```
[SLIDE 3: The AI Coding Revolution]

"Let's set the stage. In 2021, GitHub launched Copilot. Within 6 months, 1 million developers were using it. Fast forward to 2025, and 60% of professional developers use some form of AI coding assistant—Cursor, Copilot, Claude Code, ChatGPT.

[Pause for effect]

The question isn't 'Should we use AI?' That ship has sailed. Your team is already using it, whether you know it or not.

The real question is: 'How do we use AI SAFELY?'

[Gesture to statistics on slide]

Yes, AI makes us 40% faster. Yes, developers are happier. But—and this is a big but—if ungoverned, AI code has a 3x higher defect rate. That's from Google Research, 2024.

So we have a paradox: AI makes us faster, but introduces new risks.

[Transition]

Let me show you what happens when AI code goes wrong..."

[NEXT SLIDE]
```

**Full Script**: Available in separate document `Workshop-Speaker-Notes-Full-Script.pdf`

---

### 9.3 Testimonials (Post-Workshop)

**Collect Testimonials** (via LinkedIn tag or email request):

**Template Email**:
```
Subject: Quick favor - Workshop testimonial?

Hi [First Name],

Thanks for attending the AI Safety workshop last week! I'm collecting feedback for our website.

Would you mind sharing a 1-2 sentence testimonial? Something like:

"[Workshop Name] gave me a clear framework to govern AI code without slowing down my team. Highly recommend for any CTO using Cursor/Copilot."

If yes, reply with your testimonial + permission to use it publicly (LinkedIn, website).

Thanks!
[Your Name]
```

**Expected Testimonials** (hypothetical):
- "Best workshop I've attended this year. The 4-layer framework is gold." - [CTO Name, Company]
- "Practical, actionable, no fluff. I'm implementing policies this week." - [VP Eng Name, Company]
- "Finally, a solution that doesn't treat AI as 'just another CI check.' SDLC Orchestrator gets it." - [Eng Manager Name, Company]

---

### 9.4 Workshop ROI Metrics

**Track These Metrics**:

| Metric | Formula | Target |
|--------|---------|--------|
| **Attendance Rate** | Attendees / Registrants | ≥70% |
| **Engagement Rate** | (Poll votes + Activity participation) / Attendees | ≥80% |
| **Satisfaction Score** | Avg survey score (Q1) | ≥4.5/5 |
| **Lead Generation** | Design Partner applications | ≥3/workshop |
| **Conversion Rate** | Onboarded partners / Applicants | ≥50% |
| **Referrals** | New leads from attendees | ≥1/workshop |

**ROI Calculation**:
```
Workshop Cost:
  - Facilitator time: 8 hours (prep + delivery) × $100/hour = $800
  - Tools: Zoom Pro ($15/month), Slido ($0 free tier)
  - Total: $815

Workshop Value:
  - 3 Design Partner leads × 50% conversion = 1.5 partners
  - 1.5 partners × $900 LTV (6 months free + convert to paid) = $1,350
  - ROI: ($1,350 - $815) / $815 = 66% ROI

Plus:
  - Brand awareness: 20 attendees × avg network 500 people = 10K impressions
  - Thought leadership: 2 LinkedIn posts from attendees = 5K impressions
  - Content asset: Recording → evergreen lead gen funnel
```

**Break-Even**: 1 Design Partner per workshop (pays for itself)

---

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | Dec 20, 2025 | Product Team + CTO | Initial version - 25 slides, 90 min |

---

**Status**: ✅ **DESIGN APPROVED**
**Next Step**: Slide deck creation (Sprint 41 Week 2 - Jan 13-17, 2026)
**Owner**: Product Team (content) + Design Team (slides)
**Review**: CTO dry-run presentation required before first workshop

---

*SDLC Orchestrator - Workshop: "AI Safety for Engineering Teams" v1.0. Educate, engage, convert.*
