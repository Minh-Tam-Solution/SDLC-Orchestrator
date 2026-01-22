# Product Roadmap 2026 - SDLC Orchestrator
## 12-Month Execution Plan

**Version**: 1.1.0
**Date**: January 18, 2026
**Purpose**: External Expert Review - Strategic Planning
**Status**: CTO Approved (Updated for SDLC 5.1.3)

---

## 1. Vision for 2026

**End State**: 30-50 paying teams using SDLC Orchestrator as the **Operating System for Software 3.0** - the control plane that orchestrates all AI coders under governance, evidence, and policy-as-code.

### Key Milestones

| Milestone | Target Date | Success Criteria |
|-----------|-------------|------------------|
| **M1: AI Safety v1** | March 2026 | 6 design partners, ≥70% internal adoption |
| **M2: EP-06 Codegen GA** | June 2026 | IR-based codegen for Vietnam SME, 15-25 paying teams |
| **M3: Multi-VCS** | September 2026 | GitLab + Bitbucket support |
| **M4: 30-50 Teams** | December 2026 | 30-50 teams, $86K-$144K ARR |

---

## 2. Q1 2026: AI Safety Foundation & Sprint Governance

### Sprint 41-73: Core Platform ✅ (Complete)

| Sprint Range | Focus | Status |
|--------------|-------|--------|
| Sprint 41-43 | Policy Guards & Evidence UI | ✅ Complete |
| Sprint 44-60 | AI Governance & Codegen | ✅ Complete |
| Sprint 61-73 | Auto-Fix Engine & SAST | ✅ Complete |

### Sprint 74-77: Sprint Planning Governance ✅ (Complete) (NEW)

| Deliverable | Status | Description |
|-------------|--------|-------------|
| G-Sprint Gate | ✅ Complete | Sprint planning validation gate |
| G-Sprint-Close Gate | ✅ Complete | Sprint completion with 24h docs enforcement |
| Planning Hierarchy API | ✅ Complete | Roadmap → Phase → Sprint → Backlog |
| Planning Dashboard | ✅ Complete | Full hierarchy visualization |
| Burndown Charts | ✅ Complete | Sprint progress tracking |
| Sprint Forecasting | ✅ Complete | AI-powered sprint predictions |
| Retrospective Automation | ✅ Complete | Automated retro suggestions |

### Sprint 78-79: Team Management ✅ (Current - Jan 2026)

| Deliverable | Status | Description |
|-------------|--------|-------------|
| Personal Teams | ✅ Complete | Individual developer workspace |
| Organization Teams | ✅ Complete | Shared company workspace |
| Team Switching | ✅ Complete | Context switching between teams |
| Role-Based Access | ✅ Complete | Owner/Admin/Member/Viewer roles |
| Landing Page Update | ✅ Complete | SDLC 5.1.3 messaging |

**Current Sprint**: Sprint 79 (January 2026)

### M1 Milestone (March 2026)

| Criterion | Target |
|-----------|--------|
| Internal AI-Intent Flows | ≥70% adoption |
| AI Safety Layer | Protecting all internal AI PRs |
| Design Partners | ≥6 onboarded and active |
| Actionable Feedback | ≥10 items shipped |

---

## 3. Q2 2026: Evidence Vault GA

### Sprint 47-50: EP-06 Codegen Engine (Apr-May 2026)

| Deliverable | Description |
|-------------|-------------|
| **IR-Based Codegen** | Intermediate Representation for Vietnamese SME templates |
| **Dual Mode Support** | Mode A: BYO (Cursor/Copilot) + Mode B: Native OSS (qwen2.5-coder) |
| **Vietnam SME Templates** | Pre-built templates for common Vietnamese business apps |
| **BYOK LLM Integration** | Bring Your Own Key for API cost optimization |

### Sprint 51-52: Evidence Vault v2 (May-Jun 2026)

| Deliverable | Description |
|-------------|-------------|
| Bulk Export | Auditor-ready ZIP with manifest |
| Retention Policies | Configurable 1-7 year retention |
| Search v2 | Full-text search across all evidence |
| Compliance Reports | SOC 2, ISO 27001 templates |

### M2 Milestone (June 2026)

| Criterion | Target |
|-----------|--------|
| Paying Teams | 15-25 |
| EP-06 Codegen | GA for Vietnam SME |
| Evidence Vault v2 | Audit-ready with compliance reports |
| Vietnam SME Adoption | 5-10 teams using IR-based codegen |

---

## 4. Q3 2026: Multi-VCS & Scale

### Sprint 53-56: Codegen Engine v2 (Jul-Aug 2026)

| Deliverable | Description |
|-------------|-------------|
| **Tri-Mode Enhancement** | Advanced fallback: Cursor → Native OSS → Rule-based |
| **Cross-Reference Validator** | Multi-file code consistency validation |
| **Control Plane Dashboard** | Unified view of all AI coders in organization |
| **Enterprise BYO Features** | Custom LLM endpoint configuration |

### Sprint 57-60: Multi-VCS Support (Aug-Sep 2026)

| Deliverable | Description |
|-------------|-------------|
| GitLab Integration | OAuth, webhook, MR validation |
| Bitbucket Integration | OAuth, webhook, PR validation |
| VCS Abstraction Layer | Unified interface for all VCS |
| Migration Tool | GitHub → GitLab project migration |

### M3 Milestone (September 2026)

| Criterion | Target |
|-----------|--------|
| VCS Support | GitHub + GitLab + Bitbucket |
| Paying Teams | 25-40 |
| Control Plane | Orchestrating 3+ AI coders per team |
| API Latency | <100ms p95 |

---

## 5. Q4 2026: Scale to 30-50 Teams

### Sprint 61-64: Enterprise Features (Oct-Nov 2026)

| Deliverable | Description |
|-------------|-------------|
| SSO (SAML/OIDC) | Enterprise authentication |
| Advanced RBAC | Custom roles, fine-grained permissions |
| Audit Log Export | SIEM integration ready |
| Custom Policies | User-defined OPA policies |

### Sprint 65-68: Scale & Polish (Nov-Dec 2026)

| Deliverable | Description |
|-------------|-------------|
| Performance Optimization | 100K concurrent users (designed for, 10K tested) |
| High Availability | Multi-region deployment |
| Disaster Recovery | RTO 4h, RPO 1h |
| Documentation v2 | Complete user guides |

### M4 Milestone (December 2026)

| Criterion | Target |
|-----------|--------|
| Paying Teams | 30-50 |
| ARR | $86K-$144K |
| NPS | ≥8.0/10 |
| Uptime | 99.9% |
| Vietnam SME | 10-15 teams on Founder Plan |
| Control Plane | Orchestrating 5+ AI coders per enterprise team |

---

## 6. Feature Prioritization (MoSCoW)

### Must Have (Q1-Q2 2026)

| Feature | Sprint | Priority |
|---------|--------|----------|
| Policy Guards (OPA) | 41-43 | P0 ✅ |
| SAST Integration | 43 | P0 ✅ |
| Evidence Timeline | 43 | P0 ✅ |
| Stalled Project Detection | 44-46 | P0 |
| **EP-06 Codegen Engine** | **47-50** | **P0** |
| Evidence Vault v2 | 51-52 | P0 |

### Should Have (Q3 2026)

| Feature | Sprint | Priority |
|---------|--------|----------|
| Codegen Engine v2 | 53-56 | P1 |
| GitLab Integration | 57-58 | P1 |
| Bitbucket Integration | 59-60 | P1 |
| Control Plane Dashboard | 55-56 | P1 |

### Could Have (Q4 2026)

| Feature | Sprint | Priority |
|---------|--------|----------|
| SSO (SAML/OIDC) | 61-62 | P2 |
| Custom Policies UI | 63-64 | P2 |
| SIEM Integration | 65-66 | P2 |
| Mobile App | Future | P3 |

### Won't Have (2026)

| Feature | Reason |
|---------|--------|
| Jira Native Integration | Focus on GitHub-first, complement not compete |
| Mobile App | Web-first strategy, responsive dashboard sufficient |
| Self-hosted On-Premise | Cloud-only in Year 1, enterprise on-prem in Year 2 |

**Note**: EP-06 Codegen Engine is now a **Must Have** for Q2 2026, providing IR-based codegen for Vietnam SME while also serving as the governance control plane for BYO AI coders (Cursor, Copilot, Claude Code).

---

## 7. Risk Register

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Slow customer acquisition | Medium | High | Double down on content marketing |
| GitHub API changes | Low | High | Abstract VCS layer early |
| Team burnout | Medium | High | Monitor velocity, enforce breaks |
| Competition launches | Medium | Medium | Move faster, deeper integration |
| AI provider reliability | Low | Medium | Multi-provider fallback |

---

## 8. Resource Allocation

### Team (8.5 FTE)

| Role | FTE | Focus |
|------|-----|-------|
| Backend Engineers | 3 | Core platform |
| Frontend Engineers | 2 | Dashboard, VS Code ext |
| DevOps/SRE | 1 | Infrastructure, scaling |
| PM | 1 | Roadmap, customers |
| Design | 0.5 | UI/UX |
| QA | 1 | Testing, quality |

### Budget (Annual)

| Category | Budget |
|----------|--------|
| Engineering Salaries | $400,000 |
| Product & Design | $120,000 |
| Infrastructure | $36,000 |
| Marketing | $80,000 |
| Tools & Services | $20,000 |
| **Total** | **$656,000** |

---

## 9. Success Metrics

### Leading Indicators (Track Weekly)

| Metric | Target |
|--------|--------|
| Weekly Active Users | Growing 10%+ WoW |
| Trial Signups | 10+ per week |
| Feature Completion | On schedule |
| Sprint Velocity | Stable or improving |

### Lagging Indicators (Track Monthly)

| Metric | Target |
|--------|--------|
| Paying Teams | On track to 30-50 |
| ARR | On track to $86K-$144K |
| Churn Rate | <5% annual |
| NPS | ≥8.0/10 |
| Vietnam SME Adoption | 10-15 teams on Founder Plan |
| Control Plane Usage | 3+ AI coders orchestrated per team |

---

## 10. Expert Feedback Applied

| Original Question | Expert Feedback | Resolution |
|-------------------|-----------------|------------|
| Is roadmap too aggressive? | Yes, 100 teams unrealistic for 8.5 FTE | Reduced to 30-50 teams |
| Should Multi-VCS come before Codegen? | No, Codegen is wedge for Vietnam SME | EP-06 moved to Q2 Must Have |
| When should we add SSO? | Q4 is appropriate | Kept as-is |
| Is 100 teams / $240K ARR realistic? | No, too aggressive | Revised to 30-50 teams / $86K-$144K |
| Codegen contradiction | "Won't Have" conflicted with CEO approval | Removed contradiction, added EP-06 |

---

**Document Control**

| Field | Value |
|-------|-------|
| Author | PM Team, Nhat Quang Holding |
| Approved By | CTO + CEO |
| Status | Updated for SDLC 5.1.3 (Jan 18, 2026) |
| Version | 1.2.0 |

---

*"Operating System for Software 3.0 - We orchestrate, not compete."*
