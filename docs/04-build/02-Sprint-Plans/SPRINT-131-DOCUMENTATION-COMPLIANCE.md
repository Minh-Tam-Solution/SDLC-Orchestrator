# Sprint 131: Documentation Compliance Sprint

**Sprint ID**: SPRINT-131
**Duration**: March 17-28, 2026 (2 weeks)
**Theme**: Documentation Debt Remediation (Post-Launch Stabilization)
**Priority**: P1 (Technical Debt)
**Team**: Full Team (Backend Lead coordinates)
**Framework**: SDLC 6.0.5

---

## 1. Executive Summary

### Context
- **March 1, 2026**: SDLC Orchestrator soft launch at **82/100 compliance** ✅
- **Sprint 128-130**: Onboarding Flow Implementation (Feb 3 - Mar 14)
- **Current Documentation Coverage**: 5.1% (43/843 files with YAML frontmatter)
- **Target**: 70%+ coverage by March 28 (Sprint 131 completion)

### Compliance Gap Analysis
| Category | Current | Target | Gap |
|----------|---------|--------|-----|
| YAML Frontmatter Coverage | 5.1% | 70% | +64.9% |
| BDD Format Usage | 7% | 40% | +33% |
| Overall Compliance Score | 82/100 | 88/100 | +6 points |

### Sprint Goal
**Backfill 200+ high-traffic process documents** with SDLC 6.0.5 compliant metadata to achieve 70%+ documentation coverage.

---

## 2. Sprint Objectives

### Primary Objectives (P0)
1. **Add YAML Frontmatter to 200+ High-Traffic Files** (70% coverage)
   - Sprint plans (Sprint 100+)
   - Active ADRs (ADR-030+)
   - Stage README files (all 10 stages)
   - CTO/CPO reports (2026 reports)

2. **Convert Top 20 ADRs to BDD Format** (40% ADR coverage)
   - ADR-030 to ADR-050
   - Focus on architectural decisions with acceptance criteria

3. **Create Automated Validation Tools** (CI/CD integration)
   - Pre-commit hook for YAML frontmatter
   - GitHub Actions workflow for BDD format check
   - Compliance dashboard automation

### Secondary Objectives (P1)
4. **Archive Legacy Directories** (Tech debt cleanup)
   - Move obsolete docs to `docs/10-archive/{NN}-Legacy/` per RFC-001
   - Update cross-references
   - Create migration guide

5. **Create Documentation Templates** (Future-proofing)
   - YAML frontmatter template
   - BDD acceptance criteria template
   - Sprint plan template (6.0.5 compliant)

---

## 3. Detailed Task Breakdown

### Track 1: YAML Frontmatter Backfill (8 days, 32 SP)

#### Task 1.1: Sprint Plans Metadata (Sprint 100-130)
**Owner**: PM/PJM Office
**Effort**: 3 days (12 SP)
**Files**: ~30 sprint plans

**Template**:
```yaml
---
sprint_id: SPRINT-131
title: "Documentation Compliance Sprint"
status: IN_PROGRESS
tier: STANDARD
owner: Backend Lead
start_date: 2026-03-17
end_date: 2026-03-28
framework_version: 6.0.5
context_zone: Semi-Static
update_frequency: Daily
team:
  - Backend Lead
  - PM/PJM Office
  - Frontend Lead
dependencies:
  - SPRINT-130 (Onboarding Flow Complete)
related_specs:
  - SPEC-0002 (Specification Standard)
---
```

**Acceptance Criteria**:
- [ ] All Sprint 100+ plans have YAML frontmatter
- [ ] sprint_id, title, status, owner, dates populated
- [ ] Validated by `sdlcctl validate` CLI
- [ ] CI/CD pipeline passes

#### Task 1.2: ADR Metadata (ADR-001 to ADR-050)
**Owner**: Architect
**Effort**: 2 days (8 SP)
**Files**: ~50 ADRs

**Template**:
```yaml
---
adr_id: ADR-041
title: "Framework 6.0 Governance System Design"
version: 1.0.0
status: APPROVED
date: 2026-01-28
author: Backend Lead
approvers:
  - CEO
  - CTO
  - CPO
stage: 02-design
tier: PROFESSIONAL
context_zone: Static
update_frequency: Quarterly
related_specs:
  - SPEC-0001 (Anti-Vibecoding)
  - SPEC-0002 (Specification Standard)
supersedes: ADR-040
---
```

**Acceptance Criteria**:
- [ ] All ADR-001 to ADR-050 have frontmatter
- [ ] adr_id, status, approvers populated
- [ ] Supersedes chain validated
- [ ] No broken cross-references

#### Task 1.3: Stage README Files (10 stages)
**Owner**: Backend Lead
**Effort**: 1 day (4 SP)
**Files**: 10 README.md files

**Template**:
```yaml
---
stage_id: "04-build"
title: "Stage 04: Development & Implementation"
stage_name: BUILD
framework_version: 6.0.5
status: ACTIVE
owner: Backend Lead
last_updated: 2026-03-17
context_zone: Semi-Static
update_frequency: Per Sprint
subdirectories:
  - 01-Coding-Standards
  - 02-Sprint-Plans
  - 03-Code-Reviews
related_stages:
  - 02-design (upstream)
  - 05-test (downstream)
---
```

**Acceptance Criteria**:
- [ ] All 10 stage READMEs have frontmatter
- [ ] stage_id, subdirectories documented
- [ ] Related stages cross-referenced
- [ ] Validation passes

#### Task 1.4: CTO/CPO Reports (2026 reports)
**Owner**: PM/PJM Office
**Effort**: 1 day (4 SP)
**Files**: ~60 executive reports

**Template**:
```yaml
---
report_id: CTO-REPORT-2026-01-30-001
title: "Multi-Frontend Alignment Gap"
report_type: GAP_ANALYSIS
severity: HIGH
date: 2026-01-30
author: CTO
audience:
  - CEO
  - CPO
  - CTO
status: APPROVED
stage: 09-govern
tier: ENTERPRISE
context_zone: Dynamic
update_frequency: One-time
related_reports:
  - CTO-REPORT-2026-01-15-GATE-G3
decisions_made:
  - Option A+ Enhanced (40 SP investment)
action_items:
  - Sprint 125-127 execution
  - Version alignment complete
---
```

**Acceptance Criteria**:
- [ ] All 2026 reports have frontmatter
- [ ] report_id, severity, decisions_made populated
- [ ] Action items tracked
- [ ] Executive dashboard updated

#### Task 1.5: Test Strategy & Runbooks
**Owner**: QA Lead
**Effort**: 1 day (4 SP)
**Files**: ~50 test/deployment docs

**Template**:
```yaml
---
doc_id: TEST-STRATEGY-E2E-2026
title: "End-to-End Testing Strategy"
doc_type: TEST_STRATEGY
stage: 05-test
tier: PROFESSIONAL
owner: QA Lead
last_updated: 2026-03-17
status: ACTIVE
framework_version: 6.0.5
context_zone: Semi-Static
update_frequency: Per Sprint
tools:
  - Playwright
  - pytest
  - Docker Compose
coverage_target: 80%
related_docs:
  - TEST-STRATEGY-UNIT-2026
  - TEST-STRATEGY-INTEGRATION-2026
---
```

**Acceptance Criteria**:
- [ ] Test strategies have frontmatter
- [ ] Runbooks have structured metadata
- [ ] Tools and coverage targets documented
- [ ] Validation passes

---

### Track 2: BDD Format Conversion (5 days, 20 SP)

#### Task 2.1: Convert ADR-030 to ADR-050 to BDD Format
**Owner**: Architect + Backend Lead
**Effort**: 3 days (12 SP)
**Files**: 20 ADRs

**BDD Template for ADRs**:
```markdown
## Decision Criteria (BDD Format)

### Criterion 1: Performance Requirements
GIVEN the system handles 1000+ concurrent users
WHEN evaluating architecture options
THEN the solution MUST support <100ms p95 API latency

### Criterion 2: Scalability
GIVEN the platform targets 10K+ projects
WHEN choosing database architecture
THEN the solution MUST support horizontal scaling

## Acceptance Criteria

### AC-1: Architecture Approved
GIVEN the ADR is submitted for review
WHEN CTO/CPO/CEO review the decision
THEN the ADR status MUST change to APPROVED

### AC-2: Implementation Complete
GIVEN the ADR is approved
WHEN the implementation is complete
THEN all acceptance criteria MUST pass validation
```

**Target ADRs** (High Priority):
1. ADR-041: Framework 6.0 Governance System Design
2. ADR-042: SDLC 6.0.5 Migration Strategy
3. ADR-043: Context Authority V2 Design
4. ADR-044: Compliance Validation Service
5. ADR-045: Multi-Frontend Alignment Strategy
6. ADR-046 to ADR-050: TBD based on recent decisions

**Acceptance Criteria**:
- [ ] 20 ADRs converted to BDD format
- [ ] Decision criteria use GIVEN-WHEN-THEN
- [ ] Acceptance criteria testable
- [ ] BDD validator passes (70%+ score)

#### Task 2.2: Convert Sprint Plans to BDD Acceptance Criteria
**Owner**: PM/PJM Office
**Effort**: 2 days (8 SP)
**Files**: 10 recent sprint plans (Sprint 120-130)

**BDD Template for Sprint Plans**:
```markdown
## Sprint Goals (BDD Format)

### Goal 1: Team Invitation System
GIVEN a project owner wants to invite team members
WHEN they use the invitation feature
THEN invitations MUST be sent via email with accept/decline links

### Goal 2: GitHub Integration
GIVEN a developer wants to connect their GitHub repo
WHEN they run `sdlcctl init --github=owner/repo`
THEN the repo MUST be linked and structure validated

## Acceptance Criteria

### Sprint 128 Success Criteria
GIVEN Sprint 128 is complete
WHEN reviewing deliverables
THEN the following MUST be true:
  - [ ] 5 invitation API endpoints deployed
  - [ ] Email service integration working
  - [ ] Frontend invitation UI complete
  - [ ] 90%+ test coverage achieved
  - [ ] CTO demo successful
```

**Acceptance Criteria**:
- [ ] 10 sprint plans have BDD goals
- [ ] Acceptance criteria measurable
- [ ] Testable success criteria defined
- [ ] Retrospective references BDD criteria

---

### Track 3: Automation & Tooling (3 days, 12 SP)

#### Task 3.1: Pre-commit Hook for YAML Frontmatter
**Owner**: DevOps + Backend Lead
**Effort**: 1 day (4 SP)

**Implementation**:
```python
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: yaml-frontmatter-check
        name: Check YAML Frontmatter
        entry: python scripts/sdlc-validation/frontmatter-checker.py
        language: python
        files: \.md$
        exclude: ^(99-legacy|10-Archive)/
```

**Validation Rules**:
- Block commits without frontmatter for new specs
- Warn for missing frontmatter in existing docs
- Auto-suggest template based on file path

**Acceptance Criteria**:
- [ ] Pre-commit hook installed in repo
- [ ] Blocks SPEC-*.md without frontmatter
- [ ] Warns for other .md files
- [ ] Provides helpful error messages
- [ ] CI/CD enforces hook

#### Task 3.2: GitHub Actions Workflow for BDD Format Check
**Owner**: DevOps
**Effort**: 1 day (4 SP)

**Implementation**:
```yaml
# .github/workflows/bdd-format-check.yml
name: BDD Format Validation
on: [pull_request]
jobs:
  bdd-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run BDD Validator
        run: |
          python scripts/sdlc-validation/bdd-format-validator.py docs/ --score
      - name: Comment PR with Score
        uses: actions/github-script@v7
        with:
          script: |
            const score = process.env.BDD_SCORE;
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              body: `BDD Format Score: ${score}/100`
            })
```

**Acceptance Criteria**:
- [ ] GitHub Actions workflow created
- [ ] BDD score calculated on PR
- [ ] Score commented on PR automatically
- [ ] Fails if score < 50% for new specs

#### Task 3.3: Compliance Dashboard Automation
**Owner**: Backend Lead
**Effort**: 1 day (4 SP)

**Implementation**:
- Automated daily compliance scan
- Generates HTML report
- Tracks drift over time
- Alerts if compliance drops >5%

**Dashboard Metrics**:
```yaml
metrics:
  - yaml_frontmatter_coverage: 70%
  - bdd_format_usage: 40%
  - zero_mock_violations: 0
  - agpl_containment: 100%
  - overall_compliance: 88/100

drift_detection:
  - baseline: Sprint 130 (82/100)
  - current: Sprint 131 (88/100)
  - change: +6 points (GREEN)
  - alert_threshold: -5 points
```

**Acceptance Criteria**:
- [ ] Daily automated scan running
- [ ] HTML report generated
- [ ] Drift tracking functional
- [ ] Alerts configured for Slack

---

### Track 4: Legacy Migration (2 days, 8 SP)

#### Task 4.1: Archive Legacy Directories to 10-archive
**Owner**: PM/PJM Office + Backend Lead
**Effort**: 1 day (4 SP)

**Migration Strategy** (per RFC-001):
1. Identify obsolete docs (pre-SDLC 5.0, 2024-2025)
2. Move to `docs/10-archive/{NN}-Legacy/`
3. Update cross-references with [ARCHIVED] tag
4. Create migration guide

**Directories to Archive**:
- `docs/01-planning/99-Session-Logs/` → Already moved ✅
- `docs/02-design/99-Legacy/` → Migrated to `docs/10-archive/02-Legacy/` ✅
- `docs/04-build/99-Old-Sprints/` (Sprint 1-50) → Migrated to `docs/10-archive/04-Legacy/` ✅
- `frontend/99-legacy/`

**Acceptance Criteria**:
- [ ] All legacy directories archived to docs/10-archive/
- [ ] Cross-references updated
- [ ] Migration guide created
- [ ] No broken links

#### Task 4.2: Create Migration Guide
**Owner**: Backend Lead
**Effort**: 1 day (4 SP)

**Guide Structure**:
```markdown
# Legacy Document Migration Guide

## What to Migrate
- Docs referenced in last 90 days
- ADRs marked as ACTIVE/APPROVED
- Sprint plans (Sprint 100+)
- Technical specs (all SPEC-*.md)

## What to Archive
- Docs untouched >6 months
- Pre-SDLC 5.0 content
- Obsolete sprint plans (Sprint 1-50)
- Superseded ADRs

## Migration Process
1. Check git log for last access date
2. Add YAML frontmatter if migrating
3. Update cross-references
4. Validate with `sdlcctl validate`
5. Archive old version to 10-Archive/
```

**Acceptance Criteria**:
- [ ] Migration guide published
- [ ] Decision tree for migrate vs archive
- [ ] Automated script for bulk migration
- [ ] Training session for team

---

### Track 5: Documentation Templates (1 day, 4 SP)

#### Task 5.1: Create Reusable Templates
**Owner**: PM/PJM Office
**Effort**: 1 day (4 SP)

**Templates to Create**:

1. **Sprint Plan Template**:
```yaml
---
sprint_id: SPRINT-XXX
title: "[Theme Name]"
status: PLANNING
tier: [LITE|STANDARD|PROFESSIONAL|ENTERPRISE]
owner: [Team Lead]
start_date: YYYY-MM-DD
end_date: YYYY-MM-DD
framework_version: 6.0.5
context_zone: Semi-Static
update_frequency: Daily
team: []
dependencies: []
related_specs: []
---

## Sprint Goals (BDD Format)
GIVEN [context]
WHEN [action]
THEN [expected outcome]

## Acceptance Criteria
- [ ] [Measurable criteria]
```

2. **ADR Template**:
```yaml
---
adr_id: ADR-XXX
title: "[Decision Title]"
version: 1.0.0
status: DRAFT
date: YYYY-MM-DD
author: [Name]
approvers: []
stage: 02-design
tier: PROFESSIONAL
context_zone: Static
supersedes: null
---

## Context
[Background and problem statement]

## Decision Criteria (BDD Format)
### Criterion 1: [Name]
GIVEN [context]
WHEN [evaluation]
THEN [requirement]

## Acceptance Criteria
### AC-1: [Name]
GIVEN [precondition]
WHEN [action]
THEN [expected result]
```

3. **CTO Report Template**:
```yaml
---
report_id: CTO-REPORT-YYYY-MM-DD-XXX
title: "[Report Title]"
report_type: [GAP_ANALYSIS|STATUS|STRATEGIC]
severity: [HIGH|MEDIUM|LOW]
date: YYYY-MM-DD
author: CTO
audience: [CEO, CPO, CTO]
status: DRAFT
stage: 09-govern
tier: ENTERPRISE
context_zone: Dynamic
---

## Executive Summary
[3-5 sentence summary]

## Findings (BDD Format)
GIVEN [observation]
WHEN [analysis]
THEN [recommendation]

## Action Items
- [ ] [Actionable task with owner]
```

**Acceptance Criteria**:
- [ ] 5+ templates created
- [ ] Published to `.claude/templates/`
- [ ] Documentation written
- [ ] Team training conducted

---

## 4. Success Metrics

### Primary KPIs (Sprint 131)
| Metric | Baseline | Target | Measurement |
|--------|----------|--------|-------------|
| YAML Frontmatter Coverage | 5.1% | 70% | Automated scan |
| BDD Format Usage | 7% | 40% | BDD validator |
| Overall Compliance Score | 82/100 | 88/100 | Compliance dashboard |
| Archived Legacy Files | 0 | 200+ | Manual count |
| Automated Validation | 0% | 100% | Pre-commit + CI/CD |

### Secondary KPIs
- **Developer Friction**: <5 min per PR (measured by time to fix validation failures)
- **Template Usage**: 100% of new docs use templates (tracked in PRs)
- **Broken Links**: 0 (validated by link checker)
- **Documentation Debt**: Tracked in backlog, no new debt added

---

## 5. Risk Management

### High-Risk Items
| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Team capacity during feature freeze | Medium | High | Frontend continues onboarding polish; backend focuses on docs |
| Breaking existing workflows | Low | High | Pre-commit hook warns but doesn't block; 1-week grace period |
| BDD conversion quality | Medium | Medium | Pair programming for first 5 ADRs; peer review mandatory |

### Dependencies
- **Upstream**: Sprint 130 completion (Onboarding Flow)
- **Downstream**: Sprint 132+ (new features rely on compliant docs)
- **External**: None

---

## 6. Timeline

### Week 1 (March 17-21)
**Day 1-2 (Mon-Tue)**:
- Track 1.1: Sprint plans metadata (PM/PJM Office)
- Track 2.1: ADR BDD conversion start (Architect)
- Track 3.1: Pre-commit hook (DevOps)

**Day 3-4 (Wed-Thu)**:
- Track 1.2: ADR metadata (Architect)
- Track 2.1: ADR BDD conversion (ongoing)
- Track 3.2: GitHub Actions workflow (DevOps)

**Day 5 (Fri)**:
- Track 1.3: Stage READMEs (Backend Lead)
- Track 2.2: Sprint plans BDD (PM/PJM Office)
- Track 3.3: Compliance dashboard (Backend Lead)
- **Mid-sprint review**: Check 50% progress

### Week 2 (March 24-28)
**Day 6-7 (Mon-Tue)**:
- Track 1.4: CTO/CPO reports (PM/PJM Office)
- Track 2.2: Sprint plans BDD (ongoing)
- Track 4.1: Archive 99-legacy (Backend Lead)

**Day 8-9 (Wed-Thu)**:
- Track 1.5: Test strategy & runbooks (QA Lead)
- Track 4.2: Migration guide (Backend Lead)
- Track 5.1: Documentation templates (PM/PJM Office)

**Day 10 (Fri)**:
- Final validation pass
- Compliance dashboard review
- Sprint 131 retrospective
- **Sprint close**: Publish compliance report

---

## 7. Definition of Done

### Sprint-Level DoD
- [ ] 200+ files have YAML frontmatter (70% coverage)
- [ ] 20 ADRs converted to BDD format (40% ADR coverage)
- [ ] Pre-commit hook active and enforced
- [ ] GitHub Actions workflow running on all PRs
- [ ] Compliance dashboard shows 88/100 score
- [ ] All 99-legacy directories archived
- [ ] 5+ documentation templates published
- [ ] Team training session conducted
- [ ] Sprint retrospective completed
- [ ] CTO approval for Sprint 132 start

### File-Level DoD (for each document updated)
- [ ] YAML frontmatter with 9 required fields
- [ ] BDD format if applicable (specs, ADRs, sprint plans)
- [ ] Cross-references validated (no broken links)
- [ ] Validated by `sdlcctl validate` CLI
- [ ] Peer review approved
- [ ] CI/CD pipeline passes
- [ ] Committed to main branch

---

## 8. Team Allocation

| Role | Allocation | Tasks |
|------|-----------|-------|
| **Backend Lead** | 80% (8 days) | Stage READMEs, compliance dashboard, migration guide |
| **PM/PJM Office** | 100% (10 days) | Sprint plans, CTO reports, templates |
| **Architect** | 60% (6 days) | ADR metadata + BDD conversion |
| **DevOps** | 40% (4 days) | Pre-commit hook, GitHub Actions, automation |
| **QA Lead** | 20% (2 days) | Test strategy documentation |
| **Frontend Lead** | 10% (1 day) | Review frontend impact, template testing |

**Total Effort**: 76 SP (2 developers * 2 weeks = 80 SP capacity) ✅

---

## 9. Deliverables

### Code Deliverables
1. `.pre-commit-config.yaml` - YAML frontmatter validator hook
2. `.github/workflows/bdd-format-check.yml` - BDD format CI/CD check
3. `scripts/sdlc-validation/compliance_dashboard.py` - Automated compliance scanner
4. `scripts/sdlc-validation/migration-helper.py` - Bulk migration tool

### Documentation Deliverables
1. 200+ files with YAML frontmatter
2. 20 ADRs with BDD format
3. 10 stage READMEs updated
4. 60 CTO/CPO reports with metadata
5. 5+ reusable templates
6. Migration guide
7. Sprint 131 retrospective

### Reports
1. Compliance Dashboard (HTML) - Daily
2. Sprint 131 Final Compliance Report - March 28
3. Documentation Debt Backlog - Tracked in Jira

---

## 10. Post-Sprint Actions

### Sprint 132+ (April 2026)
- **Maintain 88/100+ compliance** via automation
- **Zero new documentation debt** policy
- **Quarterly compliance audits** (June, Sept, Dec)
- **Archive policy enforcement** (auto-archive docs >6 months untouched)

### Q2 2026 Goals
- 90%+ YAML frontmatter coverage
- 70%+ BDD format usage
- 95/100 overall compliance score
- Full SDLC 6.0.5 alignment

---

## 11. References

### Related Documents
- [SPEC-0002: Specification Standard](../../02-design/14-Technical-Specs/SPEC-0002-Specification-Standard.md)
- [ADR-041: Framework 6.0 Governance System](../../02-design/01-ADRs/ADR-041-Framework-6.0-Governance-System.md)
- [SDLC 6.0.5 Compliance Assessment Report](../../09-govern/05-Operations/SDLC-60-Compliance-Assessment-2026-01-30.md)
- [Sprint 130: Onboarding Flow Complete](SPRINT-130-ONBOARDING-FLOW.md)

### External References
- [SDLC 6.0.5 Framework](../../SDLC-Enterprise-Framework/README.md)
- [BDD Format Examples](../../SDLC-Enterprise-Framework/03-Templates-Tools/BDD-Examples.md)
- [YAML Frontmatter Specification](../../SDLC-Enterprise-Framework/08-Section-8-Specification-Standard.md)

---

**Sprint Plan Status**: DRAFT (Pending CTO Approval)
**Created**: January 30, 2026
**Author**: Backend Lead + PM/PJM Office
**Next Review**: March 14, 2026 (Sprint 130 close)
**Approval Required**: CTO + CPO

---

## Changelog

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-01-30 | Backend Lead | Initial draft based on compliance assessment |
| 1.1.0 | 2026-01-30 | PM/PJM Office | Added CTO recommendation (Sprint 128-130 correction) |
