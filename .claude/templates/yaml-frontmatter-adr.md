# ADR Template (SDLC 6.0.0)

**File naming**: `ADR-XXX-[kebab-case-title].md`
**Location**: `docs/02-design/01-ADRs/`

---

## YAML Frontmatter (Required)

```yaml
---
# Required Fields (9/9)
adr_id: ADR-XXX
title: "[Decision Title]"
version: 1.0.0
status: DRAFT  # DRAFT | REVIEW | APPROVED | SUPERSEDED | DEPRECATED
date: YYYY-MM-DD
author: "[Name]"
approvers:
  - CEO
  - CTO
  - CPO
stage: 02-design
tier: PROFESSIONAL  # LITE | STANDARD | PROFESSIONAL | ENTERPRISE

# Context Management
context_zone: Static  # Static | Semi-Static | Dynamic | Ephemeral
update_frequency: Quarterly  # Daily | Weekly | Per Sprint | Quarterly

# Optional Fields
supersedes: ADR-YYY  # If replacing previous ADR
superseded_by: null  # Updated when superseded
related_specs:
  - SPEC-XXXX
related_adrs:
  - ADR-YYY
tags:
  - architecture
  - security
  - performance
---
```

---

## ADR Structure (BDD Format)

### 1. Context

**Background**: [Describe the situation requiring a decision]

**Problem Statement**: [What problem are we solving?]

**Stakeholders**:
- Technical: [Team members affected]
- Business: [Business stakeholders]

---

### 2. Decision Criteria (BDD Format)

#### Criterion 1: [Name]
```gherkin
GIVEN [context/constraint]
WHEN evaluating solutions
THEN the solution MUST [requirement]
```

**Weight**: [High | Medium | Low]
**Rationale**: [Why this criterion matters]

#### Criterion 2: [Name]
```gherkin
GIVEN [context/constraint]
WHEN evaluating solutions
THEN the solution MUST [requirement]
```

**Weight**: [High | Medium | Low]
**Rationale**: [Why this criterion matters]

---

### 3. Options Considered

#### Option A: [Name]
**Description**: [Brief description]

**Pros**:
- ✅ [Advantage 1]
- ✅ [Advantage 2]

**Cons**:
- ❌ [Disadvantage 1]
- ❌ [Disadvantage 2]

**Decision Criteria Evaluation**:
```gherkin
GIVEN Criterion 1
WHEN evaluating Option A
THEN it MEETS/FAILS because [reason]
```

#### Option B: [Name]
**Description**: [Brief description]

**Pros**:
- ✅ [Advantage 1]
- ✅ [Advantage 2]

**Cons**:
- ❌ [Disadvantage 1]
- ❌ [Disadvantage 2]

**Decision Criteria Evaluation**:
```gherkin
GIVEN Criterion 1
WHEN evaluating Option B
THEN it MEETS/FAILS because [reason]
```

---

### 4. Decision

**Chosen Option**: **Option [A/B/C]** - [Name]

**Rationale**: [Why this option was chosen]

**Key Factors**:
1. [Factor 1]
2. [Factor 2]
3. [Factor 3]

---

### 5. Acceptance Criteria (BDD Format)

#### AC-1: Architecture Approved
```gherkin
GIVEN the ADR is submitted for review
WHEN CTO/CPO/CEO review the decision
THEN the ADR status MUST change to APPROVED
  AND all reviewers MUST sign off
  AND no critical concerns raised
```

#### AC-2: Implementation Complete
```gherkin
GIVEN the ADR is approved
WHEN the implementation is complete
THEN all acceptance criteria MUST pass validation
  AND system meets performance targets
  AND security requirements satisfied
```

#### AC-3: Documentation Updated
```gherkin
GIVEN the implementation is complete
WHEN reviewing documentation
THEN all related docs MUST be updated
  AND cross-references validated
  AND team trained on new approach
```

---

### 6. Consequences

#### Positive
- ✅ [Positive consequence 1]
- ✅ [Positive consequence 2]

#### Negative
- ⚠️ [Negative consequence 1] - Mitigation: [Strategy]
- ⚠️ [Negative consequence 2] - Mitigation: [Strategy]

#### Neutral
- ℹ️ [Neutral consequence 1]
- ℹ️ [Neutral consequence 2]

---

### 7. Implementation Plan

**Phase 1**: [Name] (X days)
- [ ] Task 1.1
- [ ] Task 1.2

**Phase 2**: [Name] (Y days)
- [ ] Task 2.1
- [ ] Task 2.2

**Success Criteria**:
```gherkin
GIVEN implementation is complete
WHEN system is deployed to production
THEN [measurable outcome]
```

---

### 8. Risks & Mitigation

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| [Risk 1] | Low/Med/High | Low/Med/High | [Strategy] |

---

### 9. References

**Internal**:
- [SPEC-XXXX: Technical Specification](link)
- [ADR-YYY: Related Decision](link)

**External**:
- [External reference 1](url)
- [External reference 2](url)

---

### 10. Changelog

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | YYYY-MM-DD | [Name] | Initial decision |

---

**ADR Status**: DRAFT
**Created**: YYYY-MM-DD
**Author**: [Name]
**Next Review**: [Date]
**Approval Required**: CTO + CPO + CEO
