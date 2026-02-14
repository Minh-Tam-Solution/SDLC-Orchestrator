# Sprint Plan Template (SDLC 6.0.5)

**File naming**: `SPRINT-XXX-[kebab-case-title].md`
**Location**: `docs/04-build/02-Sprint-Plans/`

---

## YAML Frontmatter (Required)

```yaml
---
# Required Fields (9/9)
sprint_id: SPRINT-XXX
title: "[Sprint Theme Name]"
status: PLANNING  # PLANNING | IN_PROGRESS | COMPLETE | CANCELLED
tier: STANDARD  # LITE | STANDARD | PROFESSIONAL | ENTERPRISE
owner: "[Team Lead Name]"
start_date: YYYY-MM-DD
end_date: YYYY-MM-DD
framework_version: 6.0.5

# Context Management (AGENTS.md 4-Zone Model)
context_zone: Semi-Static  # Static | Semi-Static | Dynamic | Ephemeral
update_frequency: Daily  # Daily | Weekly | Per Sprint | Quarterly

# Optional Fields
team:
  - Backend Lead
  - Frontend Lead
  - QA Lead
dependencies:
  - SPRINT-YYY (Prerequisite sprint)
related_specs:
  - SPEC-XXXX (Related technical spec)
related_adrs:
  - ADR-XXX (Related architecture decision)
epic: EP-XX  # If part of an epic
priority: P0  # P0 (Critical) | P1 (High) | P2 (Medium)
story_points: 15  # Total effort
---
```

---

## Sprint Structure (BDD Format)

### 1. Sprint Goals (BDD Format)

**Goal 1: [Feature Name]**
```gherkin
GIVEN [context/precondition]
WHEN [action/trigger]
THEN [expected outcome]
```

**Goal 2: [Feature Name]**
```gherkin
GIVEN [context/precondition]
WHEN [action/trigger]
THEN [expected outcome]
```

---

### 2. Acceptance Criteria

#### Sprint Success Criteria
```gherkin
GIVEN Sprint XXX is complete
WHEN reviewing deliverables
THEN the following MUST be true:
  - [ ] [Measurable criterion 1]
  - [ ] [Measurable criterion 2]
  - [ ] [Measurable criterion 3]
  - [ ] Test coverage ≥ 90%
  - [ ] API p95 latency < 100ms
  - [ ] Zero P0 bugs
```

---

### 3. Task Breakdown

#### Track 1: [Backend/Frontend/etc]
**Owner**: [Name]
**Effort**: X days (Y SP)

**Tasks**:
- [ ] Task 1.1: [Description] (X SP)
- [ ] Task 1.2: [Description] (Y SP)

**Acceptance Criteria**:
```gherkin
GIVEN [precondition]
WHEN [action]
THEN [expected result]
```

---

### 4. Success Metrics

| Metric | Baseline | Target | Measurement |
|--------|----------|--------|-------------|
| API Latency (p95) | Xms | <100ms | pytest-benchmark |
| Test Coverage | X% | 90%+ | pytest-cov |
| Bug Count | X | 0 P0/P1 | Jira |

---

### 5. Risk Management

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| [Risk description] | Low/Med/High | Low/Med/High | [Mitigation strategy] |

---

### 6. Timeline

**Week 1 (Date - Date)**:
- Day 1-2: [Tasks]
- Day 3-4: [Tasks]
- Day 5: Mid-sprint review

**Week 2 (Date - Date)**:
- Day 6-7: [Tasks]
- Day 8-9: [Tasks]
- Day 10: Sprint close + retrospective

---

### 7. Definition of Done

**Sprint-Level DoD**:
- [ ] All acceptance criteria met
- [ ] Test coverage ≥ 90%
- [ ] API performance budget met
- [ ] Security scan passed
- [ ] Documentation updated
- [ ] Sprint retrospective completed
- [ ] CTO/CPO approval for next sprint

---

### 8. Deliverables

**Code**:
- [ ] [Component 1] - [Description]
- [ ] [Component 2] - [Description]

**Documentation**:
- [ ] [Doc 1] - [Description]
- [ ] [Doc 2] - [Description]

**Reports**:
- [ ] Sprint retrospective
- [ ] Metrics dashboard

---

### 9. References

- [SPEC-XXXX: Technical Specification](link)
- [ADR-XXX: Architecture Decision](link)
- [Previous Sprint: SPRINT-YYY](link)

---

**Sprint Status**: DRAFT
**Created**: YYYY-MM-DD
**Author**: [Name]
**Next Review**: [Date]
**Approval Required**: CTO + CPO
