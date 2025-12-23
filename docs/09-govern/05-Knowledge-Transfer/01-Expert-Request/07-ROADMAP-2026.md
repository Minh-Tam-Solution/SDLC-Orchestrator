# Product Roadmap 2026 - SDLC Orchestrator
## 12-Month Execution Plan

**Version**: 1.0.0
**Date**: December 23, 2025
**Purpose**: External Expert Review - Strategic Planning
**Status**: CTO Approved

---

## 1. Vision for 2026

**End State**: 100 paying teams using SDLC Orchestrator for AI-native governance.

### Key Milestones

| Milestone | Target Date | Success Criteria |
|-----------|-------------|------------------|
| **M1: AI Safety v1** | March 2026 | 6 design partners, ≥70% internal adoption |
| **M2: Evidence Vault GA** | June 2026 | 30 paying teams, audit-ready |
| **M3: Multi-VCS** | September 2026 | GitLab + Bitbucket support |
| **M4: 100 Teams** | December 2026 | 100 teams, $240K ARR |

---

## 2. Q1 2026: AI Safety Foundation

### Sprint 41-43: Policy Guards & Evidence UI ✅ (Complete)

| Deliverable | Status | Lines |
|-------------|--------|-------|
| OPA Integration | ✅ Complete | 3,578 |
| SAST Validator (Semgrep) | ✅ Complete | 4,431 |
| Evidence Timeline UI | ✅ Complete | 4,526 |
| **Total** | ✅ | **15,388** |

### Sprint 44-46: Stalled Project Detection (Feb 2026)

| Deliverable | Description |
|-------------|-------------|
| Stalled Project Algorithm | Detect projects stuck at gates for >7 days |
| Notification Engine | Slack/Email alerts for stalled projects |
| Dashboard Widgets | At-risk project visualization |
| M1 Polish | Bug fixes, performance optimization |

### M1 Milestone (March 2026)

| Criterion | Target |
|-----------|--------|
| Internal AI-Intent Flows | ≥70% adoption |
| AI Safety Layer | Protecting all internal AI PRs |
| Design Partners | ≥6 onboarded and active |
| Actionable Feedback | ≥10 items shipped |

---

## 3. Q2 2026: Evidence Vault GA

### Sprint 47-50: Enterprise Migration Engine (Apr-May 2026)

| Deliverable | Description |
|-------------|-------------|
| .sdlc-config.json | 1KB config replaces 700KB manual docs |
| Version Scanner | Detect SDLC version of any project |
| Auto-Fixer | Automatically fix structure violations |
| Backup Engine | Safe migration with rollback |

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
| Paying Teams | 30 |
| Audit-Ready | Pass mock SOC 2 audit |
| Evidence Integrity | 100% SHA256 verified |
| Search Performance | <200ms p95 |

---

## 4. Q3 2026: Multi-VCS & Scale

### Sprint 53-56: Codegen Engine Tri-Mode (Jul-Aug 2026)

| Mode | Description |
|------|-------------|
| **Mode A: BYO Codex** | Claude/Cursor/Copilot + Governance |
| **Mode B: Native OSS** | qwen2.5-coder:32b (92.7% HumanEval) |
| **Mode C: Hybrid** | Claude → Continue.dev auto-failover |

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
| Paying Teams | 60 |
| Multi-VCS Projects | ≥10 |
| API Latency | <100ms p95 |

---

## 5. Q4 2026: Scale to 100 Teams

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
| Performance Optimization | 100K concurrent users |
| High Availability | Multi-region deployment |
| Disaster Recovery | RTO 4h, RPO 1h |
| Documentation v2 | Complete user guides |

### M4 Milestone (December 2026)

| Criterion | Target |
|-----------|--------|
| Paying Teams | 100 |
| ARR | $240K |
| NPS | ≥8.0/10 |
| Uptime | 99.9% |

---

## 6. Feature Prioritization (MoSCoW)

### Must Have (Q1-Q2 2026)

| Feature | Sprint | Priority |
|---------|--------|----------|
| Policy Guards (OPA) | 41-43 | P0 ✅ |
| SAST Integration | 43 | P0 ✅ |
| Evidence Timeline | 43 | P0 ✅ |
| Stalled Project Detection | 44-45 | P0 |
| Evidence Vault v2 | 51-52 | P0 |

### Should Have (Q2-Q3 2026)

| Feature | Sprint | Priority |
|---------|--------|----------|
| Enterprise Migration | 47-50 | P1 |
| Codegen Engine | 53-56 | P1 |
| GitLab Integration | 57-58 | P1 |
| Bitbucket Integration | 59-60 | P1 |

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
| Jira Native Integration | Focus on GitHub-first |
| Mobile App | Web-first strategy |
| Self-hosted | Cloud-only in Year 1 |
| AI Code Generation | We validate, not generate |

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
| Paying Teams | On track to 100 |
| ARR | On track to $240K |
| Churn Rate | <5% annual |
| NPS | ≥8.0/10 |

---

## 10. Questions for Expert Review

1. **Pacing**: Is the roadmap too aggressive for 8.5 FTE?
2. **Prioritization**: Should Multi-VCS come before Codegen Engine?
3. **Enterprise Features**: When should we add SSO? Earlier?
4. **Revenue Target**: Is 100 teams / $240K ARR realistic for Year 1?
5. **Technical Debt**: When should we pause features for cleanup?

---

**Document Control**

| Field | Value |
|-------|-------|
| Author | PM Team, NQH Holdings |
| Approved By | CTO |
| Status | Ready for External Review |

---

*"Ship the RIGHT things at the RIGHT time."*
