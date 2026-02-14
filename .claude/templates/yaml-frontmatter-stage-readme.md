# Stage README Template (SDLC 6.0.5)

**File naming**: `README.md`
**Location**: `docs/[stage-folder]/README.md`

---

## YAML Frontmatter (Required)

```yaml
---
# Required Fields (9/9)
stage_id: "[XX-stage-name]"  # 00-foundation, 01-planning, 02-design, etc.
title: "Stage [XX]: [Stage Name]"
stage_name: [FOUNDATION|PLANNING|DESIGN|INTEGRATE|BUILD|TEST|DEPLOY|OPERATE|COLLABORATE|GOVERN]
framework_version: 6.0.5
status: ACTIVE  # ACTIVE | PLANNED | DEPRECATED
owner: "[Role]"  # e.g., PM, Architect, Backend Lead
last_updated: YYYY-MM-DD

# Context Management
context_zone: Semi-Static  # Stage structure changes per sprint
update_frequency: Per Sprint  # Updated as stage content evolves

# Stage-Specific Fields
subdirectories:
  - 01-[subdirectory-name]
  - 02-[subdirectory-name]
related_stages:
  - upstream: "[XX-stage-name]"  # e.g., 01-planning
  - downstream: "[XX-stage-name]"  # e.g., 03-integrate
gates:
  - G0.1  # Gates associated with this stage
  - G0.2
deliverables:
  - "[Deliverable 1]"
  - "[Deliverable 2]"
---
```

---

## Stage Overview

### Purpose
[What is the purpose of this stage in the SDLC?]

### Scope
[What activities are performed in this stage?]

### Key Questions Answered
- [Question 1]
- [Question 2]
- [Question 3]

---

## Stage Structure

```
[XX-stage-name]/
├── README.md (this file)
├── 01-[subdirectory-name]/
│   ├── [document-1].md
│   └── [document-2].md
├── 02-[subdirectory-name]/
│   ├── [document-1].md
│   └── [document-2].md
└── 99-Legacy/ (archived content)
```

---

## Subdirectories

### 01-[Subdirectory Name]
**Purpose**: [What goes in this subdirectory?]

**Key Documents**:
- [[Document 1]](01-[subdirectory]/[document-1].md) - [Description]
- [[Document 2]](01-[subdirectory]/[document-2].md) - [Description]

---

### 02-[Subdirectory Name]
**Purpose**: [What goes in this subdirectory?]

**Key Documents**:
- [[Document 1]](02-[subdirectory]/[document-1].md) - [Description]
- [[Document 2]](02-[subdirectory]/[document-2].md) - [Description]

---

## Stage Entry Criteria (BDD Format)

```gherkin
Feature: Enter Stage [XX]
  As a [role]
  I want to start Stage [XX]
  So that [benefit]

  Scenario: Stage entry requirements met
    Given [upstream stage] is complete
    And [prerequisite deliverable] is approved
    When reviewing stage entry criteria
    Then all entry requirements MUST be satisfied:
      - [ ] [Criterion 1]
      - [ ] [Criterion 2]
      - [ ] [Criterion 3]
```

---

## Stage Exit Criteria (BDD Format)

```gherkin
Feature: Exit Stage [XX]
  As a [role]
  I want to complete Stage [XX]
  So that [downstream stage] can begin

  Scenario: Stage completion requirements met
    Given all stage activities are complete
    And all deliverables are approved
    When reviewing stage exit criteria
    Then all exit requirements MUST be satisfied:
      - [ ] [Criterion 1]
      - [ ] [Criterion 2]
      - [ ] [Criterion 3]
      - [ ] Gate [GX] passed
```

---

## Key Deliverables

| Deliverable | Owner | Template | Required For |
|-------------|-------|----------|--------------|
| [Deliverable 1] | [Role] | [Link to template] | [Gate/Stage] |
| [Deliverable 2] | [Role] | [Link to template] | [Gate/Stage] |

---

## Quality Gates

### Gate [GX]: [Gate Name]
**Purpose**: [What does this gate validate?]

**Criteria**:
```gherkin
GIVEN [stage] is complete
WHEN evaluating Gate [GX]
THEN the following MUST be true:
  - [ ] [Criterion 1]
  - [ ] [Criterion 2]
  - [ ] [Criterion 3]
```

**Approval Required**: [CTO | CPO | CEO]

---

## Tier-Specific Guidance

### LITE Tier
**Minimum Requirements**:
- [ ] [Requirement 1]
- [ ] [Requirement 2]

**Optional**:
- [ ] [Optional item 1]

---

### STANDARD Tier
**Requirements**: All LITE +
- [ ] [Additional requirement 1]
- [ ] [Additional requirement 2]

---

### PROFESSIONAL Tier
**Requirements**: All STANDARD +
- [ ] [Additional requirement 1]
- [ ] [Additional requirement 2]

---

### ENTERPRISE Tier
**Requirements**: All PROFESSIONAL +
- [ ] [Additional requirement 1]
- [ ] [Additional requirement 2]
- [ ] [Compliance documentation]

---

## Tools & Templates

**Documentation Templates**:
- [Template 1](.claude/templates/[template-name].md)
- [Template 2](.claude/templates/[template-name].md)

**Validation Tools**:
- `sdlcctl validate` - Check stage compliance
- `sdlcctl generate` - Generate stage documents

**Automation**:
- Pre-commit hooks
- CI/CD validation
- Compliance dashboard

---

## Common Patterns

### Pattern 1: [Name]
**When to use**: [Scenario]
**How to implement**: [Steps]
**Example**: [Link or code snippet]

---

### Pattern 2: [Name]
**When to use**: [Scenario]
**How to implement**: [Steps]
**Example**: [Link or code snippet]

---

## Anti-Patterns (What NOT to Do)

### Anti-Pattern 1: [Name]
**Problem**: [What's wrong with this approach?]
**Why it fails**: [Explanation]
**Better approach**: [Alternative]

---

### Anti-Pattern 2: [Name]
**Problem**: [What's wrong with this approach?]
**Why it fails**: [Explanation]
**Better approach**: [Alternative]

---

## Related Stages

### Upstream: Stage [XX] ([Stage Name])
**Provides**: [What inputs come from upstream stage?]
**Link**: [../XX-stage-name/README.md](../XX-stage-name/README.md)

---

### Downstream: Stage [XX] ([Stage Name])
**Consumes**: [What outputs go to downstream stage?]
**Link**: [../XX-stage-name/README.md](../XX-stage-name/README.md)

---

## References

**SDLC Framework**:
- [SDLC 6.0.5 Overview](../../SDLC-Enterprise-Framework/README.md)
- [Stage Transition Guide](../../SDLC-Enterprise-Framework/02-Process-Guides/)

**Project-Specific**:
- [Project Roadmap](../00-foundation/04-Roadmap/Product-Roadmap.md)
- [Technical Specifications](../02-design/14-Technical-Specs/)

---

## Changelog

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | YYYY-MM-DD | [Name] | Initial stage README |

---

**Stage Status**: ACTIVE
**Last Updated**: YYYY-MM-DD
**Owner**: [Role]
**Next Review**: [Date]
