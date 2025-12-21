# Sprint 41-43 Executive Summary
## AI Safety Layer v1 - 6-Week Implementation Plan (Q1 2026)

**Document ID**: SPRINT-EXEC-2026-Q1
**Date**: December 20, 2025
**Status**: ✅ **CTO APPROVED**
**Framework**: SDLC 5.1.1 Complete Lifecycle
**Epic Coverage**: EP-01, EP-02, EP-03

---

## 🎯 6-Week Roadmap Overview

| Sprint | Dates | Focus | Team | Deliverables |
|--------|-------|-------|------|--------------|
| **Sprint 41** | Jan 6-17 | Foundation Setup | 6 FTE | Analytics, Schema, Partners |
| **Sprint 42** | Jan 20-31 | Detection & Pipeline | 7 FTE | AI Detection, Validators, Workshop |
| **Sprint 43** | Feb 3-14 | Policy Guards & UI | 7 FTE | OPA Integration, Timeline, VCR |

**Total Duration**: 6 weeks (42 days)
**Total Team**: 6-7 FTE (Backend, Frontend, DevOps, Product, QA)
**Budget**: $25,000 (EP-02 allocation)

---

## 📊 Sprint 41: AI Safety Foundation (Jan 6-17)

### Objectives
1. **Setup Product Analytics** - Mixpanel/Amplitude with 10 key events
2. **Create AI Code Events Schema** - `ai_code_events` table + ADR-019
3. **Design PR Detection** - 3 strategies (metadata, API, manual)
4. **Source Design Partners** - 20 qualified candidates
5. **Create Workshop Deck** - 90-min "AI Safety for Engineering Teams"

### Key Deliverables

| Deliverable | Owner | Status |
|-------------|-------|--------|
| Mixpanel project + API keys | Backend + DevOps | ⏳ Week 1 |
| `ai_code_events` table deployed | Backend Lead + DBA | ⏳ Week 1 |
| AIDetectionService interface | Backend Dev 2 | ⏳ Week 1 |
| 20 partner candidates sourced | Product Team | ⏳ Week 2 |
| Workshop deck v1.0 | Product + Frontend | ⏳ Week 2 |

### Success Metrics

```yaml
Analytics: ≥10 events tracked
Schema: ADR-019 approved by DBA
Detection Design: ≥90% accuracy on test dataset
Partners: 20 qualified (≥60 points on scorecard)
Workshop: v1.0 complete (25+ slides)
```

### Dependencies
- [ ] Mixpanel API keys (block Day 1-2)
- [ ] ADR-019 DBA review (block Day 3-4)
- [x] GitHub App credentials
- [ ] Partner contact list (block Day 6-7)

---

## 🔍 Sprint 42: AI Detection & Validation Pipeline (Jan 20-31)

### Objectives
1. **Implement GitHubAIDetectionService** - Combined detection strategies
2. **Create Validation Pipeline** - Orchestrator for validators
3. **Implement 3 Core Validators** - Lint, Tests, Coverage
4. **Onboard 2-3 Design Partners** - First wave onboarding
5. **Conduct First Workshop** - Live workshop delivery

### Key Deliverables

| Deliverable | Owner | Status |
|-------------|-------|--------|
| GitHubAIDetectionService | Backend Dev 1+2 | ⏳ Week 1 |
| Validation Pipeline orchestrator | Backend Lead | ⏳ Week 1 |
| Lint Validator (ESLint/Ruff) | Backend Dev 3 | ⏳ Week 1 |
| Test Runner Validator | Backend Dev 3 | ⏳ Week 2 |
| Coverage Validator | Backend Dev 3 | ⏳ Week 2 |
| PR Comment integration | Frontend Dev 1 | ⏳ Week 2 |
| 2-3 partners onboarded | Product Team | ⏳ Week 2 |

### Success Metrics

```yaml
Detection Accuracy: ≥85% on 100-PR test dataset
Pipeline Latency: <6 min p95
Validators: 3/5 core validators live
Partners: ≥2 active (Slack channel created)
Workshop: 1 session delivered (attendance tracked)
```

### Technical Highlights

**AI Detection Strategies**:
- Metadata Analysis (~70% accuracy)
- GitHub API Integration (~85% accuracy)
- Manual Tagging (100% accuracy)
- **Combined Weighted**: ≥85% target

**Validation Pipeline**:
- Celery-based task queue
- Parallel validator execution
- Redis for job state
- Webhook-triggered from GitHub

---

## 🛡️ Sprint 43: Policy Guards & Evidence UI (Feb 3-14)

### Objectives
1. **Implement Policy Guards** - OPA-based policy enforcement
2. **Create Evidence Timeline UI** - Audit trail visualization
3. **Add SAST Validator** - Semgrep security scanning
4. **Implement VCR Override Flow** - Approval workflow
5. **Begin "Ý tưởng mới" Flow** - EP-01 kickoff
6. **Onboard Remaining Partners** - Target 6 total

### Key Deliverables

| Deliverable | Owner | Status |
|-------------|-------|--------|
| Policy Guards (OPA) | Backend Lead | ⏳ Week 1 |
| SAST Validator (Semgrep) | Backend Dev 3 | ⏳ Week 1 |
| Evidence Timeline UI | Frontend Dev 1+2 | ⏳ Week 2 |
| VCR Override dialog | Frontend Dev 2 | ⏳ Week 2 |
| "Ý tưởng mới" wizard (v0.1) | Frontend Dev 1 | ⏳ Week 2 |
| 6 total partners active | Product Team | ⏳ Week 2 |

### Success Metrics

```yaml
Policy Guards: 100% blocking on policy fail
Evidence Timeline: Viewable for all AI events
SAST Validator: ≥5 security rules active
VCR Override Rate: <5% of blocked PRs
Partners Active: ≥6 total in CRM
Idea Flow UI: v0.1 prototype demo-ready
```

### Policy Guard Examples

```rego
# No AI-generated code in critical paths
package ai_safety.critical_paths

deny[msg] {
    input.files_changed[_] contains "/auth/"
    input.ai_generated == true
    msg := "AI code not allowed in authentication modules"
}

# Require human review for database migrations
deny[msg] {
    input.files_changed[_] contains "migrations/"
    input.human_review_count < 2
    msg := "Database migrations require ≥2 human reviews"
}
```

---

## 🏆 End-of-Sprint-43 Milestone (M1)

### EP-02 AI Safety Layer v1 - COMPLETE ✅

**Core Capabilities Delivered**:

1. **Detection**
   - ✅ AI PR auto-detection (≥85% accuracy)
   - ✅ Multi-tool support (Cursor, Copilot, Claude, ChatGPT)
   - ✅ Manual tagging fallback

2. **Validation**
   - ✅ 5 validators live (Lint, Tests, Coverage, SAST, Architecture)
   - ✅ Pipeline latency <6 min p95
   - ✅ Parallel execution + result aggregation

3. **Policy Enforcement**
   - ✅ OPA-based Policy Guards
   - ✅ 100% blocking on mandatory policy fails
   - ✅ VCR override workflow

4. **Evidence Trail**
   - ✅ `ai_code_events` table with full audit log
   - ✅ Evidence Timeline UI
   - ✅ PR metadata + validation results

### EP-03 Design Partner Program - ON TRACK 🟢

**Partner Metrics**:
- ✅ 20 candidates sourced
- ✅ ≥6 partners onboarded
- ✅ 2 workshops delivered
- ✅ Bi-weekly feedback loops active

**Key Feedback Collected**:
- Pain points validated
- Feature requests logged
- 2 case studies in progress

---

## 📈 Analytics & KPIs (End of Sprint 43)

### Product Analytics (Mixpanel)

| Event | Weekly Count Target |
|-------|-------------------|
| `ai_pr_detected` | ≥50 |
| `ai_safety_validation` | ≥50 |
| `policy_guard_blocked` | ≥5 |
| `vcr_override_requested` | <3 |
| `idea_submitted` | ≥10 |

### Performance Metrics

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Detection Accuracy | ≥85% | TBD | ⏳ |
| Validation Latency (p95) | <6 min | TBD | ⏳ |
| False Positive Rate | <10% | TBD | ⏳ |
| Partner NPS | ≥8.0 | TBD | ⏳ |

### Team Velocity

| Sprint | Story Points | Completed | Velocity |
|--------|-------------|-----------|----------|
| Sprint 41 | 55 | TBD | TBD |
| Sprint 42 | 70 | TBD | TBD |
| Sprint 43 | 75 | TBD | TBD |

---

## 🚧 Risks & Mitigation

### High-Priority Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **Detection accuracy <85%** | High | Medium | Expand test dataset, tune weights |
| **OPA policy complexity** | High | Medium | Provide policy templates library |
| **Partner churn** | Medium | Medium | High-touch support, rapid iteration |
| **Pipeline timeout (>6min)** | Medium | Low | Optimize validators, add caching |

### Technical Debt

| Debt Item | Severity | Plan |
|-----------|----------|------|
| GitLab support deferred | Low | Scope to Q2 2026 |
| Full-stack validation | Medium | Defer to v2 |
| AI remediation suggestions | Low | Research phase only |

---

## 🎯 Critical Success Factors

### Sprint 41 Blockers (MUST RESOLVE)
1. **Mixpanel API keys** - Request before Jan 6
2. **ADR-019 DBA review** - Schedule for Jan 8-9
3. **Partner contact list** - Prepare during Dec 23-31

### Sprint 42 Blockers (MUST RESOLVE)
1. **GitHub App permissions** - Verify before Jan 20
2. **Celery infrastructure** - Setup during Sprint 41
3. **Test dataset** - Collect 100 PRs during Sprint 41

### Sprint 43 Blockers (MUST RESOLVE)
1. **OPA policy library** - Draft during Sprint 42
2. **Frontend UI components** - Design in Sprint 42
3. **VCR approval workflow** - Define process in Sprint 42

---

## 📅 Key Dates & Milestones

| Date | Milestone | Deliverable |
|------|-----------|-------------|
| **Jan 6** | Sprint 41 Kickoff | Team alignment, dependencies confirmed |
| **Jan 10** | Analytics Live | Mixpanel tracking 10 events |
| **Jan 17** | Sprint 41 Complete | Schema deployed, 20 partners sourced |
| **Jan 20** | Sprint 42 Kickoff | Detection service implementation starts |
| **Jan 24** | First Workshop | Design Partner workshop delivered |
| **Jan 31** | Sprint 42 Complete | 3 validators live, 2 partners onboarded |
| **Feb 3** | Sprint 43 Kickoff | Policy Guards implementation |
| **Feb 7** | OPA Integration | Policy Guards blocking active |
| **Feb 14** | M1 Milestone | AI Safety Layer v1 COMPLETE |

---

## 👥 Team Allocation (6 Weeks)

### Core Team

| Role | Name | Sprint 41 | Sprint 42 | Sprint 43 |
|------|------|-----------|-----------|-----------|
| **Backend Lead** | TBD | 100% | 100% | 100% |
| **Backend Dev 1** | TBD | 100% | 100% | 100% |
| **Backend Dev 2** | TBD | 100% | 100% | 100% |
| **Backend Dev 3** | TBD | - | 100% | 100% |
| **Frontend Dev 1** | TBD | 50% | 100% | 100% |
| **Frontend Dev 2** | TBD | 50% | 100% | 100% |
| **DevOps** | TBD | 50% | 50% | 50% |
| **Product/PM** | TBD | 100% | 100% | 100% |
| **QA** | TBD | 100% | 100% | 100% |

**Total Capacity**: ~40 person-weeks across 6 weeks

---

## 💰 Budget Breakdown

| Category | Sprint 41 | Sprint 42 | Sprint 43 | Total |
|----------|-----------|-----------|-----------|-------|
| Development | $6,000 | $9,000 | $8,000 | $23,000 |
| Infrastructure | $500 | $500 | $500 | $1,500 |
| Tools (Mixpanel, Semgrep) | $0 | $0 | $0 | $0 (Free tier) |
| Partner Program | $300 | $300 | $200 | $800 |
| **Total** | **$6,800** | **$9,800** | **$8,700** | **$25,300** |

*(Fits within $25K EP-02 allocation + $300 contingency)*

---

## ✅ Definition of Done (Sprint-Level)

### Sprint 41 DoD
- [ ] All P0 tasks completed
- [ ] Mixpanel live with 10 events
- [ ] `ai_code_events` table deployed
- [ ] 20 partners sourced (scorecard ≥60)
- [ ] Workshop deck v1.0 complete
- [ ] Retro completed, Sprint 42 backlog refined

### Sprint 42 DoD
- [ ] AI Detection Service live (≥85% accuracy)
- [ ] Validation Pipeline operational
- [ ] 3 validators implemented
- [ ] 2-3 partners onboarded
- [ ] First workshop delivered
- [ ] PR Comment integration working

### Sprint 43 DoD
- [ ] Policy Guards blocking on policy fail
- [ ] Evidence Timeline UI viewable
- [ ] SAST validator live (≥5 rules)
- [ ] VCR override flow implemented
- [ ] 6 total partners active
- [ ] M1 Milestone metrics met

---

## 📞 Escalation Path

| Issue Type | Escalate To | SLA |
|------------|-------------|-----|
| **Technical Blocker** | Backend Lead → CTO | 24h |
| **Product Decision** | Product → CTO | 48h |
| **Partner Issue** | Product → Customer Success | 12h |
| **Infrastructure** | DevOps → CTO | 24h |

---

## 🚀 Post-Sprint-43 Next Steps

### Sprint 44+ (Feb 17 onwards)
1. **EP-01 "Ý tưởng mới" Flow** - Full implementation
2. **EP-01 "Dự án dở dang" Flow** - Repo scan + gap analysis
3. **AI Safety Layer Iteration** - Based on partner feedback
4. **Additional Validators** - Custom rules, dependency scanning
5. **GitLab Support** - Expand beyond GitHub

### M2 Milestone (End of Q1 2026)
- EP-01 + EP-02 complete
- ≥10 Design Partners active
- 2 case studies published
- Product-Market Fit metrics validated

---

**Document Version**: 1.0.0
**Created**: December 20, 2025
**Framework**: SDLC 5.1.1 Complete Lifecycle
**Approval**: CTO Mr. Tai (taidt@mtsolution.com.vn)

---

*This executive summary provides strategic oversight for Sprint 41-43. Detailed task-level plans available in individual sprint documents.*
