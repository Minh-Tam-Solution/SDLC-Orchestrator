# SDLC Orchestrator – AI-Native SDLC Governance & Safety Platform

**Version**: 0.1.0 (Draft)  
**Date**: December 5, 2025  
**Status**: In Review – Requires CEO/CPO/CTO Sign-off  
**Owners**: Product Strategy (CPO), AI Program (CTO)  
**Alignment**: Product Vision v2.0.0, SDLC 5.x Framework, AI Governance Extension

---

## 1. Context & Vision

### 1.1 SDLC 5.x & Orchestrator
- **SDLC 5.x** delivers a 10-stage, compliance-aware lifecycle where security, observability, governance, and evidence are enforced by design.
- **SDLC Orchestrator** functions as the **control plane** for SDLC 5.x, managing stages, gates, policy packs, evidence trails, and performance metrics across engineering teams.
- MVP (Sprint 17) has validated the bridge-first integration model with GitHub, delivering 131+ automated tests, 9.9/10 code quality, and production-ready onboarding.

### 1.2 Software 3.0 Direction
- **Software 3.0** treats AI as a first-class actor across ideation, build, test, and operations. Natural-language intent flows through AI systems to generate artefacts that must still comply with enterprise standards.
- Cursor, Copilot, Claude Code, ChatGPT Code, and internal LLM agents increase throughput but also introduce governance gaps (architecture drift, compliance risks, missing evidence).
- Orchestrator must evolve into the **governance and safety layer** that certifies AI-generated artefacts before they reach production environments.

### 1.3 Positioning (v2)
> **Product Category**: AI-Native SDLC Governance & Safety Platform  
> **Tagline**: *“The control plane that keeps Cursor/Copilot compliant with your architecture & standards.”*

**Core Principles**
- AI can produce massive code volume; Orchestrator guarantees that the output is safe, compliant, and aligned with SDLC 5.x.
- Governance remains non-negotiable: automated gates, evidence, and policy enforcement are required before every promotion.
- Differentiation is anchored in the AI Council pattern, policy-as-code library, and SDLC 5.x expertise—competitors lack the same depth of governance DNA.

---

## 2. 2026 Strategic Themes
1. **AI-Intent-First Adoption**  
   - Orchestrator becomes the entry point for new ideas and stalled projects, with AI guiding governance decisions and next best actions.  
   - Success metric: ≥70% of internal PM/EM personas initiate ideas via Orchestrator vs legacy tools.
2. **AI Safety & Governance**  
   - Every AI-generated change is validated through policy guards, validators, and evidence trails before merge.  
   - Success metric: 0 unreviewed AI PRs merged; 100% of AI-labelled PRs have audit logs in Evidence Vault.
3. **Ecosystem & Enterprise**  
   - Launch marketplace for policy packs, expand beyond GitHub, and harden enterprise capabilities (SSO/SAML, RBAC, compliance reporting, self-hosted deployment).  
   - Success metric: ≥5 external policy contributors; ≥3 enterprise pilots using governance bundle by Q4.

---

## 3. 2026 Roadmap Overview

### 3.1 High-Level Phases
| Quarter | Theme | Primary Epics | Outcomes |
|---------|-------|---------------|----------|
| **Q1–Q2** | AI Safety First *(Phase 1+2 consolidated)* | EP-01 Idea & Stalled Project Flow<br>EP-02 AI Safety Layer v1<br>EP-03 Design Partner Program | Pivot positioning, achieve intent-first adoption, validate AI Safety Layer with internal + external partners |
| **Q3** | Ecosystem & Marketplace *(scope focus)* | EP-04 Policy Pack Marketplace (Core)<br>EP-05 Multi-VCS (GitHub + GitLab) | Extend policy reach, abstract repository layer, prepare for community contributions |
| **Q4** | Enterprise Governance Bundle | EP-06 SSO/SAML + Advanced RBAC<br>EP-07 Compliance Reporting Suite<br>EP-08 White-label / Self-hosted options | Unlock enterprise buying criteria, provide audit-ready evidence, enable deployment flexibility |
| **2027+** | Become the Standard | EP-09 Industry Reference Architectures<br>EP-10 Analyst & Market Programs | Reach 10K+ teams, secure Gartner/Forrester coverage, publish industry-specific governance playbooks |

### 3.2 Milestone Map
- **M1 (Mar 2026)**: AI-Intent Flows live for internal teams (≥70% adoption); AI Safety Layer v1 protecting internal AI PRs.
- **M2 (Jun 2026)**: 10 design partners onboarded; ≥10 actionable improvements shipped; ≥2 anonymised case studies drafted.
- **M3 (Sep 2026)**: Marketplace beta with vetted policy packs; GitLab integration GA; usage telemetry instrumentation complete.
- **M4 (Dec 2026)**: Enterprise governance bundle GA; compliance report templates delivered; self-hosted pilot in production.
- **M5 (2027)**: Publish reference architectures for FinTech, HealthTech, GovTech; achieve ≥10K active teams; Gartner Market Guide inclusion.

### 3.3 Cross-Phase Enablers
- Central telemetry & product analytics pipeline (DAU/WAU, AI usage, gate pass rates).
- Policy-as-code SDK and versioning to support marketplace and enterprise extensions.
- Responsible AI framework: audit logging, bias review cadence, policy override governance.
- Scalable Evidence Vault (retention policies, partitioning for 10K+ teams).

---

## 4. Q1–Q2 2026: AI Safety First (Detailed Plan)

### 4.1 Objectives
- Pivot from “project governance tool” to “AI safety & governance layer” in all messaging and product flows.
- Make Orchestrator the default entry point for **new ideas**, **stalled projects**, and **AI-generated pull requests**.
- Run a two-track launch: internal validation (5–8 teams) and external design partners (10 teams) to accelerate feedback and proof.

### 4.2 EP-01 – Idea & Stalled Project Flow with AI Governance Hints
**Problem**  
Ideation and stalled work are scattered across Jira/Linear/Notion with no governance context, leading to 60%+ effort waste and zero visibility into gate readiness.

**Goal**  
Position Orchestrator as the decision cockpit for new ideas and stalled projects, with AI suggesting governance paths, policy packs, and next best actions.

**Scope & Deliverables**
- **New Idea Flow**  
  - Natural-language input (VN/EN) → classification (Epic/Feature/Experiment), risk tiering, effort estimation.  
  - AI recommends SDLC stage path, initial gate set, and applicable policy packs.  
  - Output: Idea Card with Build/Explore/Park recommendation and evidence requirements.
- **Stalled Project Flow**  
  - Repo + CI + evidence ingestion → gate compliance scoring, missing evidence detection, activity/bug trend analysis.  
  - AI surfaces: Kill with justification, Rescue with ordered steps, Park with re-entry criteria.  
  - Integrate with AI Council metadata to highlight past recommendations and outcomes.
- **Persona Outcomes**  
  - EM: Identify wasteful initiatives within 5 minutes.  
  - PM: Generate SDLC-ready backlog skeleton automatically.  
  - CTO: Portfolio dashboard showing governance gaps across initiatives.
- **Metrics**  
  - ≥80% of new ideas receive policy pack suggestions automatically.  
  - Time-to-first-decision <5 minutes per idea.  
  - Stalled project assessment <10 seconds with cached evidence.  
  - ≥70% of internal EM/PM personas use at least one flow weekly after 4 weeks.

**Dependencies**
- AI Council evidence schema (Sprint 26) for reuse.  
- Telemetry instrumentation to measure adoption and funnel.  
- UX updates (Support Page & Frontend Spec alignment) for guided experiences.

### 4.3 EP-02 – AI Safety Layer v1
**Goal**  
Ensure every AI-influenced pull request is validated through standardized safety checks, policy enforcement, and auditable evidence before merge.

**Scope & Deliverables**
- **AI Change Detection**  
  - Auto-tag PRs via metadata from Cursor/Copilot/Claude or manual override; store tool/model data.  
  - Integration hooks for GitHub (v1) and GitLab (paved for Q3).
- **Output Validators**  
  - Lint/format, targeted unit tests, optional SAST, architecture & dependency checks, coverage thresholds tied to policy packs.  
  - Performance target: <6 minutes p95 end-to-end validation pipeline.
- **Policy Guards**  
  - Policy packs define mandatory checks (e.g., `backend-critical` requires SAST, coverage ≥80%, forbids legacy modules).  
  - Failures block gates until Version-Controlled Resolution (VCR) is approved; audit overrides with rationale.
- **Evidence Trail**  
  - Log AI tool/model, prompts (hashed/redacted), validator outcomes, reviewer decisions into Evidence Vault (`ai_code_events`).  
  - Generate timeline view per PR for compliance teams.
- **Metrics**  
  - 100% of AI-tagged PRs processed by Safety Layer.  
  - 0 AI PR merges without passing policies or recorded VCR.  
  - Mean time-to-feedback <8 minutes; override rate <5%.
- **Specification**  
  - Detailed engineering specification maintained at `docs/specs/AI-Safety-Layer-v1.md` (see Section 5).

**Dependencies**
- OPA policy engine enhancements and test harness.  
- Evidence Vault indexing improvements for AI artefacts.  
- Collaboration with Security team on secret redaction and prompt hygiene.

### 4.4 EP-03 – Design Partner Program (10 External Teams)
**Goal**  
Reduce risk of internal-only validation by onboarding external AI-heavy teams for structured feedback, case studies, and proof of value.

**Target Partners**
- Engineering orgs with 10–200 developers, ≥100K LOC, heavy Cursor/Copilot/Claude usage, and explicit pain around AI-induced architecture drift.

**Offer & Support**
- 6–9 month free or symbolic pricing, dedicated Slack/Discord channel, rapid-response playbooks, grandfathered pricing at GA.

**Engagement Flow**
1. Recruit 10 candidates (VN/EU/US).  
2. Deliver 90-minute “AI Safety for Engineering Teams” workshop.  
3. Onboard pilot repos (GitHub initially), enable AI Safety Layer v1, configure policy packs.  
4. Bi-weekly feedback loops (calls + surveys) feeding directly into EP-01/02 backlogs.

**Success Criteria**
- ≥6 partners onboarded and active within 60 days.  
- ≥10 actionable roadmap improvements captured and prioritized.  
- ≥2 case studies (anonymised if required) illustrating defect reduction, gate adherence, or velocity improvements.  
- Partner NPS ≥40 and renewal intent ≥80% before pricing discussions.

---

## 5. AI Safety Layer v1 – Specification Reference
- Authoritative specification lives in `docs/specs/AI-Safety-Layer-v1.md`.  
- Captures architecture, data flows, validator catalogue, policy schemas, integration points, observability, and open risks.  
- Updated alongside EP-02 implementation; treated as source-of-truth for Engineering, Security, and Compliance stakeholders.

---

## 6. Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| Rebrand confusion between “governance tool” vs “AI safety platform” | Misaligned messaging, sales friction | Stage communication plan, validate positioning with design partners, maintain governance-first narrative |
| Telemetry gaps for adoption metrics | Inability to prove value or tune flows | Instrument event pipeline in Q1 (blocking dependency for EP-01/03); define shared KPIs with Data team |
| AI Safety Layer false positives causing developer friction | Reduced adoption, policy bypass culture | Progressive rollout (warning → enforcement), allow policy simulation mode, invest in developer UX and override education |
| Marketplace scope creep in Q3 | Delay enterprise commitments | Limit Q3 scope to curated policy packs + GitLab integration; defer Backstage/IDE plugins to 2027 backlog |
| Compliance features delayed to Q4 | Enterprise deals blocked | Start architecture work in parallel (RBAC/SSO schema, evidence export) during Q2 to reduce crunch |

---

## 7. Next Steps
1. Secure leadership sign-off on roadmap direction and positioning shift.  
2. Kick off telemetry/analytics workstream (Product + Data + Platform) to support EP-01/03 measurement.  
3. Finalise AI Safety Layer v1 specification and technical spike (Security, Backend, DevInfra).  
4. Prepare design partner outreach materials (case study template, workshop deck, onboarding checklist).  
5. Align GTM messaging with Marketing for Q2 “AI Safety First” announcement.

---

*This document will be versioned alongside quarterly reviews. Changes impacting phase sequencing, success metrics, or positioning require dual approval from CPO and CTO.*
