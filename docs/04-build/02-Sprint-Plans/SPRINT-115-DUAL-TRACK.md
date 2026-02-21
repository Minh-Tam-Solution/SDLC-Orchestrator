# Sprint 115: Dual-Track Execution Plan
## Framework 6.0 Templates + Anti-Vibecoding SOFT Mode

**Version**: 1.0.0
**Dates**: February 10-14, 2026 (5 days)
**Status**: PLANNED (Pending Sprint 114 Completion)
**Framework**: SDLC 6.1.0
**Prerequisites**: Sprint 114 metrics pass Go/No-Go gate

---

## Executive Summary

Sprint 115 continues dual-track execution:
- **Track 1 (40%)**: Framework 6.0 Template Development
- **Track 2 (60%)**: Anti-Vibecoding SOFT Mode Enforcement

Key milestone: First blocking enforcement of governance rules.

---

## Sprint 114 → 115 Gate

```yaml
Go/No-Go Criteria (from Sprint 114):
  ✓ Developer friction < 10 minutes per PR
  ✓ False positive rate < 20%
  ✓ No critical bugs in WARNING mode
  ✓ Team feedback positive (>50% satisfied)

If ALL pass → Proceed to SOFT enforcement
If ANY fail → Extend WARNING mode, defer SOFT to Sprint 116
```

---

## Track 1: Framework 6.0 Template Development (40%)

### Goals
1. Complete DESIGN_DECISIONS.md template
2. Complete SPEC_DELTA.md template
3. Document Context Authority methodology

### Day-by-Day Plan

#### Day 1-2: DESIGN_DECISIONS.md Template

**Purpose**: Capture design decisions that aren't full ADRs

**Template Structure**:
```markdown
# Design Decisions: [Feature/Component Name]

---
decision_id: DD-[NNNN]
status: proposed | accepted | rejected | superseded
created: YYYY-MM-DD
author: [name]
related_adrs: [ADR-XXX, ADR-YYY]
---

## Context
What is the issue that we're seeing that motivates this decision?

## Decision Drivers
* [driver 1, e.g., a force, facing concern, …]
* [driver 2, e.g., a force, facing concern, …]

## Considered Options
1. [option 1]
2. [option 2]
3. [option 3]

## Decision Outcome
Chosen option: "[option X]", because [justification].

### Consequences
* Good: [positive consequences]
* Bad: [negative consequences]

## Validation
How will we know this decision was correct?
* [metric/signal 1]
* [metric/signal 2]
```

**Deliverables**:
- [ ] DESIGN_DECISIONS.md template finalized
- [ ] 2 example design decisions created
- [ ] CTO review and approval

#### Day 3-4: SPEC_DELTA.md Template

**Purpose**: Track changes between specification versions

**Template Structure**:
```markdown
# Spec Delta: [Spec Name] v[X.Y] → v[X.Z]

---
spec_name: [name]
from_version: X.Y
to_version: X.Z
delta_date: YYYY-MM-DD
author: [name]
impact: breaking | non-breaking | patch
---

## Summary of Changes
Brief description of what changed and why.

## Added
- [New requirement/feature 1]
- [New requirement/feature 2]

## Modified
| Original | New | Rationale |
|----------|-----|-----------|
| [old text] | [new text] | [why changed] |

## Removed
- [Removed item 1] - Reason: [...]
- [Removed item 2] - Reason: [...]

## Migration Guide
Steps to update implementations:
1. [Step 1]
2. [Step 2]

## Breaking Changes
⚠️ List any breaking changes that require code updates.

## Backward Compatibility
How to maintain compatibility during transition.
```

**Deliverables**:
- [ ] SPEC_DELTA.md template finalized
- [ ] 1 example spec delta created
- [ ] Integrated with spec validation workflow

#### Day 5: Context Authority Methodology

**Purpose**: Document AGENTS.md patterns for Framework 6.0

**Document Structure**:
```markdown
# Context Authority Methodology

## 1. Overview
How AGENTS.md/CLAUDE.md provides context to AI agents.

## 2. Context Injection Patterns
### 2.1 Static Context (Manual)
- Project-level CLAUDE.md
- Team conventions
- ADR summaries

### 2.2 Dynamic Context (Automated)
- Gate status updates
- Current stage information
- Known issues/blockers

## 3. Context Authority Engine (Orchestrator)
### 3.1 Architecture
How Orchestrator injects dynamic context.

### 3.2 Integration Points
- Pre-commit hooks
- CI/CD pipeline
- IDE extensions

## 4. Best Practices
- Keep context focused
- Update on gate transitions
- Avoid information overload

## 5. Migration from Manual to Automated
Phased approach for existing projects.
```

**Deliverables**:
- [ ] Context Authority Methodology document
- [ ] Integration with Orchestrator documented
- [ ] Patterns extracted from OpenSpec research

---

## Track 2: Orchestrator SOFT Enforcement (60%)

### Goals
1. Enable SOFT enforcement mode
2. Block critical violations (Red PRs)
3. Measure developer friction accurately

### Enforcement Rules

```yaml
SOFT Mode Rules:

  BLOCK (Cannot Merge):
    - missing_ownership: No @owner header
    - missing_intent: No intent document
    - vibecoding_index_red: Index > 80
    - security_scan_fail: Critical vulnerabilities
    - stage_violation: Work in wrong stage

  WARN (Can Merge with Override):
    - stale_agents_md: >7 days since update
    - missing_adr_linkage: No related ADRs
    - vibecoding_index_orange: Index 61-80
    - missing_tests: Coverage below threshold

  AUTO_APPROVE (No Review Needed):
    - vibecoding_index_green: Index < 30
    - all_checks_pass: No violations detected
```

### Day-by-Day Plan

#### Day 1: Enable SOFT Mode

**Tasks**:
```bash
# 1. Update environment configuration
export GOVERNANCE_MODE=SOFT

# 2. Deploy enforcement rules
# backend/app/config/governance_rules.yaml
governance:
  mode: SOFT
  rules:
    block:
      - missing_ownership
      - missing_intent
      - vibecoding_index_red
      - security_scan_fail
    warn:
      - stale_agents_md
      - missing_adr_linkage
      - vibecoding_index_orange

# 3. Update GitHub Actions workflow
- name: Governance Check (SOFT)
  run: |
    result=$(curl -X POST $ORCHESTRATOR_URL/api/v1/governance/evaluate)
    if [[ $(echo $result | jq '.block') == "true" ]]; then
      echo "::error::Governance BLOCKED - Critical violations"
      exit 1
    fi
```

**Exit Criteria**:
- [ ] SOFT mode active
- [ ] First blocked PR observed
- [ ] Override mechanism working

#### Day 2-4: Developer Friction Measurement

**Metrics Collection**:
```yaml
Quantitative Metrics:
  Time to Compliance:
    - Time from PR creation to governance pass
    - Target: < 5 minutes average

  First-Pass Rate:
    - % of PRs that pass on first attempt
    - Target: > 70%

  Block Rate:
    - % of PRs blocked by SOFT mode
    - Target: < 20%

  Override Rate:
    - % of warned PRs that use override
    - Target: < 30%

Qualitative Feedback:
  Daily Survey:
    1. How long did governance compliance take today?
    2. Were any blocks frustrating/incorrect?
    3. Did auto-generation help?
    4. Suggestions for improvement?
```

**Daily Analysis**:
```yaml
Day 2:
  - Review first 5 blocked PRs
  - Identify false positives
  - Adjust thresholds if needed

Day 3:
  - Analyze friction patterns
  - Interview developers with issues
  - Document improvement ideas

Day 4:
  - Address top 3 friction points
  - Test fixes in staging
  - Prepare Go/No-Go report
```

**Exit Criteria**:
- [ ] 20+ PRs evaluated in SOFT mode
- [ ] Developer friction survey completed
- [ ] Friction points documented and addressed

#### Day 5: Go/No-Go Decision for FULL Mode

**Decision Criteria**:
```yaml
GO to FULL Enforcement (Sprint 116) if:
  - First-pass rate > 70%
  - Blocked PRs < 20%
  - Developer satisfaction > 60%
  - No critical bugs discovered
  - CEO time showing improvement trend

STAY in SOFT Mode if:
  - Any metric below threshold
  - Critical issues discovered
  - Team requests more tuning

ROLLBACK to WARNING Mode if:
  - Developer friction > 15 minutes
  - False positive rate > 30%
  - Team morale significantly impacted
```

**Sprint 115 Report Template**:
```yaml
Sprint 115 Metrics Report:

Track 1 (Framework 6.0):
  Templates Completed: [X/3]
  CTO Approval: [Yes/No]
  Ready for Sprint 116: [Yes/No]

Track 2 (Anti-Vibecoding):
  Mode: SOFT
  PRs Evaluated: [N]
  First-Pass Rate: [%]
  Block Rate: [%]
  Developer Friction: [minutes]
  Developer Satisfaction: [%]

Go/No-Go Decision:
  FULL Mode Ready: [Yes/No]
  Rationale: [...]

CPO Conditions Check:
  Track 2 Priority: [Met/Not Met]
  CEO Time Trend: [Improving/Flat/Worse]
  Context Switching: [Manageable/Problematic]
```

---

## Success Metrics

### Track 1 Metrics

| Metric | Target | Actual |
|--------|--------|--------|
| DESIGN_DECISIONS.md template | Complete | TBD |
| SPEC_DELTA.md template | Complete | TBD |
| Context Authority doc | Complete | TBD |
| CTO Approval | Yes | TBD |

### Track 2 Metrics

| Metric | Target | Sprint 114 | Sprint 115 |
|--------|--------|------------|------------|
| First-Pass Rate | >70% | TBD | TBD |
| Block Rate | <20% | N/A | TBD |
| Developer Friction | <5 min | TBD | TBD |
| Developer Satisfaction | >60% | TBD | TBD |
| CEO Time | Improving | Baseline | TBD |

---

## Risk Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Too many blocks | Medium | High | Tune thresholds, allow overrides |
| Developer frustration | Medium | High | Quick response to feedback |
| False positives | Medium | Medium | Review all blocked PRs |
| Template delays | Low | Low | Parallelize with Track 2 |

---

## Team Assignments

### Track 1 (Framework 6.0)
- **Lead**: PM/PJM
- **Template Author**: Tech Writer
- **Reviewer**: CTO

### Track 2 (Orchestrator)
- **Lead**: Backend Lead
- **DevOps**: Deployment + Monitoring
- **Frontend**: Dashboard updates
- **Reviewer**: CTO

---

## Approval

| Role | Status | Date |
|------|--------|------|
| CTO | ⏳ PENDING | - |
| CPO | ⏳ PENDING | - |
| CEO | ⏳ PENDING | - |

*Approval pending Sprint 114 completion and Go/No-Go gate pass.*

---

## Document Control

| Field | Value |
|-------|-------|
| **Version** | 1.0.0 |
| **Created** | January 28, 2026 |
| **Author** | PM/PJM Team |
| **Status** | PLANNED |
| **Sprint** | 115 |
| **Dual-Track** | Yes (Track 1: 40%, Track 2: 60%) |
