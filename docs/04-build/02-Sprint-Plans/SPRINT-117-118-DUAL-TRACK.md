# Sprint 117-118: Dual-Track Execution Plan
## Framework 6.0 Development + Orchestrator Stability

**Version**: 1.0.0
**Dates**: February 24 - March 7, 2026 (10 days / 2 weeks)
**Status**: PLANNED (Pending Sprint 116 Completion)
**Framework**: SDLC 6.1.0
**Prerequisites**: Sprint 116 FULL mode stable, Week 8 Gate passed

---

## Executive Summary

Sprint 117-118 is a **2-week development sprint** focused on:
- **Track 1 (60%)**: Framework 6.0 Spec Migration (20 specs)
- **Track 2 (40%)**: Orchestrator Stability + Context Authority Engine

Key outcomes:
- 20 specifications migrated to Framework 6.0 format
- Section 7 (Quality Assurance) fully updated
- Anti-Vibecoding FULL mode stable (3 weeks live)
- Context Authority Engine MVP (if resources allow)

---

## Sprint 116 → 117 Gate

```yaml
Go/No-Go Criteria (from Sprint 116):
  ✓ FULL mode live and stable (no critical issues)
  ✓ CEO time ≤ 15h/week (75% reduction path)
  ✓ First-pass rate > 70%
  ✓ Kill switch not triggered
  ✓ Week 8 Gate decision made (OpenSpec ADOPT/EXTEND/DEFER)

If ALL pass → Proceed to Framework 6.0 Development
If Track 2 issues → Increase Track 2 allocation to 60%
```

---

## Track 1: Framework 6.0 Development (60%)

### Goals
1. Migrate 20 prioritized specs to new format
2. Update Section 7 (Quality Assurance System)
3. Update CONTENT-MAP.md navigation
4. Quality review and testing

### Week 1 (Feb 24-28): Priority 1 Specs Migration

#### Day 1-2: Core Specs Migration (5 specs)

**Priority 1 Specs**:
```yaml
Core Specifications:
  1. Security-Baseline.md
     - Add YAML frontmatter (tier, stage, owner)
     - Standardize acceptance criteria (BDD format)
     - Link to related ADRs

  2. API-Specification.md
     - Add spec_version metadata
     - Standardize endpoint documentation
     - Add OpenAPI alignment notes

  3. Data-Model-ERD.md
     - Add tier-specific requirements
     - Document entity relationships
     - Add migration notes for schema changes

  4. Authentication-Flow.md
     - Add security tier classification
     - Document OAuth/JWT requirements per tier
     - Add sequence diagrams

  5. Evidence-Vault-Design.md
     - Add 8-state lifecycle documentation
     - Document S3 API requirements
     - Add AGPL containment notes
```

**Migration Template**:
```markdown
# [Spec Name]

---
spec_version: "1.0"
spec_id: SPEC-[NNNN]
status: draft | approved | implemented
tier: LITE | STANDARD | PROFESSIONAL | ENTERPRISE
stage: 00-10
owner: [team/person]
created: YYYY-MM-DD
last_updated: YYYY-MM-DD
related_adrs: [ADR-XXX, ADR-YYY]
---

## 1. Overview
[Brief description]

## 2. Requirements
### 2.1 Functional Requirements (BDD)
- GIVEN [context] WHEN [action] THEN [outcome]

### 2.2 Non-Functional Requirements
- Performance: [metrics]
- Security: [OWASP level]
- Scalability: [targets]

## 3. Design Decisions
[References to ADRs]

## 4. Spec Delta
[Changes from previous version]

## 5. Acceptance Criteria
[Testable criteria]

## 6. Dependencies
[Related specs/systems]
```

**Exit Criteria**:
- [ ] 5 core specs migrated
- [ ] All specs pass validation
- [ ] CTO review completed

#### Day 3-5: Active Development Specs (5 specs)

**Priority 2 Specs**:
```yaml
Active Development Specifications:
  6. Governance-System-Implementation-Spec.md
     - Document Vibecoding Index calculation
     - Add routing logic (Green/Yellow/Orange/Red)
     - Document kill switch criteria

  7. Quality-Gates-Codegen-Specification.md
     - Document 4-Gate pipeline
     - Add validation loop requirements
     - Document max_retries behavior

  8. Policy-Guards-Design.md
     - Document OPA integration
     - Add policy pack structure
     - Document override workflow

  9. Vibecoding-Index-Calculation.md
     - Document 5 weighted signals
     - Add threshold configuration
     - Document calibration process

  10. Kill-Switch-Criteria.md
     - Document trigger conditions
     - Add rollback procedures
     - Document notification flow
```

**Exit Criteria**:
- [ ] 5 active development specs migrated
- [ ] Integration with Orchestrator validated
- [ ] Tech Lead review completed

### Week 2 (Mar 3-7): Supporting Specs + Section 7

#### Day 1-3: Supporting Specs Migration (10 specs)

**Priority 3 Specs** (selected based on usage analytics):
```yaml
Supporting Specifications:
  11. AI-Context-Engine-Design.md
  12. Multi-Provider-Fallback.md
  13. SAST-Integration-Semgrep.md
  14. Override-Queue-Design.md
  15. Audit-Trail-Requirements.md
  16. RBAC-Implementation.md
  17. Dashboard-UI-Specification.md
  18. GitHub-Integration.md
  19. CI-CD-Pipeline-Design.md
  20. Performance-Budget.md
```

**Migration Checklist Per Spec**:
```yaml
Per-Spec Migration Checklist:
  [ ] Add YAML frontmatter
  [ ] Convert requirements to BDD format
  [ ] Add tier-specific requirements
  [ ] Link to related ADRs
  [ ] Update acceptance criteria
  [ ] Validate with sdlcctl (if available)
  [ ] CTO/Tech Lead review
```

**Exit Criteria**:
- [ ] All 20 specs migrated
- [ ] 80%+ spec format compliance
- [ ] No broken references

#### Day 4-5: Section 7 + CONTENT-MAP Updates

**Section 7 (Quality Assurance System) Updates**:
```yaml
Section 7 Structure:
  7.1 Anti-Vibecoding System
      - Vibecoding Index (0-100)
      - 5 weighted signals
      - Progressive routing

  7.2 Quality Gate Integration
      - 4-Gate pipeline (Syntax → Security → Context → Tests)
      - Gate evaluation timing
      - Override workflow

  7.3 Auto-Generation Layer
      - Intent generation
      - Ownership extraction
      - Context injection
      - Attestation workflow

  7.4 Kill Switch Criteria
      - Trigger conditions
      - Rollback procedures
      - Recovery process

  7.5 Developer Experience Metrics
      - First-pass rate targets
      - Friction measurement
      - Satisfaction tracking
```

**CONTENT-MAP.md Updates**:
```yaml
Navigation Updates:
  - Add Framework 6.0 section
  - Link to new templates
  - Add migration status indicators
  - Update cross-references
```

**Exit Criteria**:
- [ ] Section 7 complete
- [ ] CONTENT-MAP.md updated
- [ ] All links validated

---

## Track 2: Orchestrator Stability (40%)

### Goals
1. FULL mode stability monitoring
2. Bug fixes and threshold tuning
3. Context Authority Engine development (conditional)

### Week 1: Stability + Bug Fixes

#### Day 1-2: FULL Mode Monitoring

**Monitoring Checklist**:
```yaml
Daily Monitoring:
  Dashboard Checks:
    - Rejection rate: Target <20%
    - False positive rate: Target <5%
    - API latency p95: Target <100ms
    - Kill switch status: INACTIVE

  Alert Review:
    - Review all governance alerts
    - Investigate false positives
    - Document edge cases

  Developer Feedback:
    - Check Slack/Teams channels
    - Review override requests
    - Track friction points
```

**Exit Criteria**:
- [ ] No critical issues
- [ ] Kill switch not triggered
- [ ] Daily reports generated

#### Day 3-5: Bug Fixes + Threshold Tuning

**Bug Fix Priority**:
```yaml
Bug Triage Rules:
  P0 (Same day):
    - Kill switch triggered
    - False positive >10% (blocks work)
    - Security vulnerability

  P1 (Within 2 days):
    - Incorrect routing (Green → Red)
    - Override queue stuck
    - Dashboard performance issues

  P2 (This sprint):
    - UI/UX improvements
    - Documentation gaps
    - Non-critical edge cases
```

**Threshold Tuning**:
```yaml
Tuning Parameters:
  Vibecoding Index:
    - Review signal weights
    - Adjust thresholds if needed
    - Document rationale for changes

  Routing Logic:
    - Review Green/Yellow boundary (30)
    - Review Yellow/Orange boundary (60)
    - Review Orange/Red boundary (80)

  Kill Switch:
    - Review rejection rate threshold (80%)
    - Review latency threshold (500ms)
    - Adjust if too sensitive/lenient
```

**Exit Criteria**:
- [ ] All P0/P1 bugs fixed
- [ ] Thresholds documented
- [ ] No regression introduced

### Week 2: Context Authority Engine (Conditional)

**Prerequisites**:
```yaml
Start Context Authority if:
  - FULL mode stable (7+ days)
  - No P0/P1 bugs in queue
  - Team capacity available

Defer if:
  - Stability issues persist
  - Bug backlog growing
  - Framework migration needs support
```

#### Context Authority Engine MVP

**If Started**:
```yaml
Context Authority Engine V1:

  Purpose:
    - Dynamic AGENTS.md updates based on gate status
    - Context injection for AI coding agents
    - Stage-aware guidance

  MVP Scope:
    - Gate status → AGENTS.md update
    - Basic context templates
    - Manual trigger (API endpoint)

  API Endpoint:
    POST /api/v1/projects/{id}/context/refresh

  Response:
    - Updated AGENTS.md content
    - Context injection payload
    - Last refresh timestamp

  Templates:
    - G0.2 Pass: "Design approved. Architecture in /docs/arch.md."
    - G1 Pass: "Stage: Build. Unit tests required."
    - G2 Pass: "Integration tests mandatory. No new features."
    - G3 Pass: "STRICT MODE. Only bug fixes allowed."
```

**Deliverables (if started)**:
- [ ] Context Authority API endpoint
- [ ] Basic context templates
- [ ] Integration with gate evaluation
- [ ] Documentation

---

## Success Metrics

### Track 1 Metrics (Framework 6.0)

| Metric | Target | Actual |
|--------|--------|--------|
| Specs migrated | 20/20 | TBD |
| Format compliance | >80% | TBD |
| Section 7 complete | Yes | TBD |
| CONTENT-MAP updated | Yes | TBD |
| CTO approval | Yes | TBD |

### Track 2 Metrics (Orchestrator)

| Metric | Target | Actual |
|--------|--------|--------|
| FULL mode uptime | >99% | TBD |
| P0 bugs | 0 | TBD |
| P1 bugs fixed | 100% | TBD |
| Kill switch triggers | 0 | TBD |
| CEO time | <15h/week | TBD |
| Context Authority MVP | Conditional | TBD |

---

## Risk Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Spec migration delays | Medium | Medium | Parallelize migration, prioritize core specs |
| FULL mode instability | Low | High | Quick rollback to SOFT, dedicated bug fix team |
| Context Authority scope creep | Medium | Low | Strict MVP definition, defer non-essential features |
| Team fatigue (2-week sprint) | Medium | Medium | Clear daily goals, celebrate milestones |

---

## Team Assignments

### Track 1 (Framework 6.0)
- **Lead**: PM/PJM
- **Spec Migration**: Tech Writer + 1 Backend Dev
- **Section 7 Author**: PM + CTO review
- **Quality Reviewer**: CTO

### Track 2 (Orchestrator)
- **Lead**: Backend Lead
- **Monitoring**: DevOps
- **Bug Fixes**: 1-2 Backend Devs
- **Context Authority**: Senior Backend Dev (if capacity)

---

## Daily Standup Focus

```yaml
Week 1:
  Mon: Sprint kickoff, migration plan review
  Tue: Core specs progress, monitoring setup
  Wed: Core specs complete, bug triage
  Thu: Active specs progress, threshold review
  Fri: Week 1 checkpoint, plan Week 2

Week 2:
  Mon: Supporting specs kickoff, Context Authority decision
  Tue: Specs 11-15 progress, stability check
  Wed: Specs 16-20 progress, bug fixes
  Thu: Section 7 + CONTENT-MAP, final testing
  Fri: Sprint completion, Sprint 119 prep
```

---

## Approval

| Role | Status | Date |
|------|--------|------|
| CTO | ⏳ PENDING | - |
| CPO | ⏳ PENDING | - |
| CEO | ⏳ PENDING | - |

*Approval pending Sprint 116 completion and Week 8 Gate pass.*

---

## Document Control

| Field | Value |
|-------|-------|
| **Version** | 1.0.0 |
| **Created** | January 28, 2026 |
| **Author** | PM/PJM Team |
| **Status** | PLANNED |
| **Sprint** | 117-118 (combined) |
| **Duration** | 10 days (2 weeks) |
| **Dual-Track** | Yes (Track 1: 60%, Track 2: 40%) |
