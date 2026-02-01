# CTO Report Template (SDLC 6.0.0)

**File naming**: `CTO-REPORT-YYYY-MM-DD-[kebab-case-title].md`
**Location**: `docs/09-govern/01-CTO-Reports/`

---

## YAML Frontmatter (Required)

```yaml
---
# Required Fields (9/9)
report_id: CTO-REPORT-YYYY-MM-DD-XXX
title: "[Report Title]"
report_type: GAP_ANALYSIS  # GAP_ANALYSIS | STATUS | STRATEGIC | TECHNICAL | GATE_REVIEW
severity: HIGH  # CRITICAL | HIGH | MEDIUM | LOW | INFO
date: YYYY-MM-DD
author: CTO
audience:
  - CEO
  - CPO
  - CTO
status: DRAFT  # DRAFT | REVIEW | APPROVED | ACTIONED
stage: 09-govern
tier: ENTERPRISE

# Context Management
context_zone: Dynamic  # Reports are typically Dynamic (time-sensitive)
update_frequency: One-time  # One-time | Weekly | Monthly | Quarterly

# Optional Fields
related_reports:
  - CTO-REPORT-YYYY-MM-DD-YYY
related_sprints:
  - SPRINT-XXX
decisions_made:
  - "[Decision 1]"
  - "[Decision 2]"
action_items:
  - owner: "[Name]"
    task: "[Description]"
    due_date: YYYY-MM-DD
    status: PENDING  # PENDING | IN_PROGRESS | COMPLETE
tags:
  - gap-analysis
  - strategic
  - gate-review
---
```

---

## CTO Report Structure

### 1. Executive Summary (3-5 sentences)

**TL;DR**: [One-sentence summary]

**Key Findings**:
- Finding 1: [Brief description]
- Finding 2: [Brief description]
- Finding 3: [Brief description]

**Recommendation**: [Primary recommendation]

**Impact**: [Business/technical impact]

---

### 2. Context & Background

**Situation**: [What triggered this report?]

**Scope**: [What areas were assessed?]

**Methodology**: [How was the analysis conducted?]

---

### 3. Findings (BDD Format)

#### Finding 1: [Name]
**Severity**: [CRITICAL | HIGH | MEDIUM | LOW]

```gherkin
GIVEN [observation/data]
WHEN [analysis/evaluation]
THEN [conclusion/impact]
```

**Evidence**:
- [Data point 1]
- [Data point 2]

**Impact**:
- Technical: [Impact description]
- Business: [Impact description]
- Timeline: [Impact description]

---

#### Finding 2: [Name]
**Severity**: [CRITICAL | HIGH | MEDIUM | LOW]

```gherkin
GIVEN [observation/data]
WHEN [analysis/evaluation]
THEN [conclusion/impact]
```

**Evidence**:
- [Data point 1]
- [Data point 2]

**Impact**:
- Technical: [Impact description]
- Business: [Impact description]
- Timeline: [Impact description]

---

### 4. Recommendations

#### Recommendation 1: [Name]
**Priority**: [P0 | P1 | P2]
**Effort**: [X SP | Y days | Z weeks]

**Rationale**: [Why this recommendation?]

**Expected Outcome**:
```gherkin
GIVEN recommendation is implemented
WHEN [completion condition]
THEN [expected benefit/result]
```

**Success Criteria**:
- [ ] [Measurable criterion 1]
- [ ] [Measurable criterion 2]

---

#### Recommendation 2: [Name]
**Priority**: [P0 | P1 | P2]
**Effort**: [X SP | Y days | Z weeks]

**Rationale**: [Why this recommendation?]

**Expected Outcome**:
```gherkin
GIVEN recommendation is implemented
WHEN [completion condition]
THEN [expected benefit/result]
```

**Success Criteria**:
- [ ] [Measurable criterion 1]
- [ ] [Measurable criterion 2]

---

### 5. Action Items

| # | Owner | Task | Priority | Due Date | Status |
|---|-------|------|----------|----------|--------|
| 1 | [Name] | [Description] | P0 | YYYY-MM-DD | PENDING |
| 2 | [Name] | [Description] | P1 | YYYY-MM-DD | PENDING |

---

### 6. Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| [Risk 1] | Low/Med/High | Low/Med/High | [Strategy] |

---

### 7. Timeline & Milestones

```
Week 1 (Date - Date): [Milestone 1]
Week 2 (Date - Date): [Milestone 2]
Week N (Date - Date): [Milestone N]

Target Completion: [Date]
```

---

### 8. Success Metrics

| Metric | Baseline | Target | Timeline |
|--------|----------|--------|----------|
| [Metric 1] | X | Y | Z weeks |
| [Metric 2] | X | Y | Z weeks |

---

### 9. Stakeholder Impact

**CEO**: [Impact and required action]
**CPO**: [Impact and required action]
**CTO**: [Impact and required action]
**Team**: [Impact and required action]

---

### 10. Appendix

#### A. Data & Evidence
- [Supporting data 1]
- [Supporting data 2]

#### B. References
- [Internal doc 1](link)
- [External reference 1](url)

---

### 11. Approval & Sign-off

**CTO Assessment**: [Grade/Score]
**Status**: [APPROVED | PENDING REVIEW | NEEDS REVISION]
**Approval Date**: YYYY-MM-DD

**Approvers**:
- [ ] CEO - [Name] (Date)
- [ ] CPO - [Name] (Date)
- [ ] CTO - [Name] (Date)

---

**Report Status**: DRAFT
**Created**: YYYY-MM-DD
**Author**: CTO
**Next Review**: [Date]
**Follow-up Required**: [Yes/No]
