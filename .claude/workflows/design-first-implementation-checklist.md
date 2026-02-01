# Design-First Implementation Checklist

**Version**: 1.0.0
**Framework**: SDLC 6.0.0
**Principle**: "Kiểm tra và cập nhật tài liệu thiết kế và yêu cầu đặc tả TRƯỚC KHI implement"
**Created**: January 30, 2026
**Owner**: CTO + Architect

---

## 🎯 Core Principle

```
┌─────────────────────────────────────────────────────────────┐
│  DESIGN-FIRST IMPLEMENTATION MANDATE                        │
├─────────────────────────────────────────────────────────────┤
│  1. READ design docs BEFORE writing code                   │
│  2. VERIFY specs are up-to-date                           │
│  3. UPDATE docs if gaps found                              │
│  4. GET approval for design changes                        │
│  5. THEN implement with confidence                         │
│                                                             │
│  "Code without design is just guessing" - CTO              │
└─────────────────────────────────────────────────────────────┘
```

---

## 📋 Pre-Implementation Checklist (MANDATORY)

### Phase 1: Discovery (Before writing ANY code)

#### 1.1 Read Existing Design Documents
**Time**: 30-60 minutes
**Owner**: Developer assigned to task

- [ ] **Read Technical Specification** (if exists)
  - Location: `docs/02-design/14-Technical-Specs/SPEC-XXXX-*.md`
  - Check: YAML frontmatter, BDD requirements, acceptance criteria
  - Verify: `status: CTO_APPROVED` or `status: ACTIVE`

- [ ] **Read Related ADRs** (Architecture Decisions)
  - Location: `docs/02-design/01-ADRs/ADR-XXX-*.md`
  - Identify: Which ADRs impact this feature?
  - Check: `status: APPROVED`, supersedes chain

- [ ] **Read Sprint Plan** (Context)
  - Location: `docs/04-build/02-Sprint-Plans/SPRINT-XXX-*.md`
  - Understand: Sprint goals, acceptance criteria, dependencies

- [ ] **Read API Specification** (if backend work)
  - Location: `docs/01-planning/05-API-Design/API-Specification.md`
  - Verify: Endpoints, request/response formats, error codes

- [ ] **Read Data Model** (if database work)
  - Location: `docs/01-planning/04-Data-Model/Data-Model-ERD.md`
  - Check: Tables, relationships, constraints, migrations

**Exit Criteria**:
```gherkin
GIVEN I am about to implement a feature
WHEN I have read all related design documents
THEN I MUST be able to answer:
  - What problem does this solve? (Context)
  - What are the acceptance criteria? (Definition of Done)
  - What are the architectural constraints? (ADRs)
  - What are the API contracts? (Specification)
  - What are the data requirements? (ERD)
```

---

#### 1.2 Verify Documentation Currency
**Time**: 15-30 minutes
**Owner**: Developer + PM

- [ ] **Check Document Last Updated Date**
  - Frontmatter field: `last_updated: YYYY-MM-DD`
  - If > 30 days old → Flag for review

- [ ] **Verify Status Fields**
  - Technical Spec: `status: CTO_APPROVED` or `ACTIVE`
  - ADR: `status: APPROVED`
  - Sprint Plan: `status: IN_PROGRESS` or `COMPLETE`

- [ ] **Check for Superseded Documents**
  - ADRs: `superseded_by: ADR-YYY`
  - Specs: `supersedes: SPEC-YYYY`
  - If superseded → Read the LATEST version

- [ ] **Validate Cross-References**
  - All links work (no 404s)
  - Related specs/ADRs are current
  - Dependencies are documented

**Red Flags** (STOP and update docs first):
```yaml
❌ Doc marked as DRAFT (not approved)
❌ Last updated > 90 days ago (likely stale)
❌ Status is DEPRECATED or SUPERSEDED
❌ Cross-references are broken
❌ No BDD acceptance criteria
❌ No YAML frontmatter (pre-SDLC 6.0.0 doc)
```

---

#### 1.3 Identify Documentation Gaps
**Time**: 15-30 minutes
**Owner**: Developer + Architect

**Common Gaps Checklist**:

- [ ] **Missing Technical Specification**
  - If no SPEC-XXXX exists for this feature
  - Action: Create SPEC draft using template
  - Get CTO approval before implementing

- [ ] **Incomplete BDD Requirements**
  - Spec has prose, not GIVEN-WHEN-THEN
  - Action: Convert to BDD format
  - Validate with PM/QA

- [ ] **Missing API Contracts**
  - Endpoints not documented in API Specification
  - Action: Add OpenAPI spec
  - Review with Backend Lead

- [ ] **Data Model Mismatch**
  - Tables/fields not in ERD
  - Action: Update ERD + migration script
  - Review with Architect

- [ ] **No Acceptance Criteria**
  - Sprint plan missing measurable DoD
  - Action: Add BDD acceptance criteria
  - Validate with PM

**Gap Documentation Template**:
```markdown
## Documentation Gap Identified

**Date**: YYYY-MM-DD
**Found by**: [Developer Name]
**Feature**: [Feature Name]

**Missing/Outdated**:
- [ ] Technical Spec (SPEC-XXXX)
- [ ] ADR (ADR-XXX)
- [ ] API Specification
- [ ] Data Model (ERD)
- [ ] Acceptance Criteria

**Impact**: [How does this affect implementation?]
**Action**: [What will be updated?]
**Owner**: [Who will update?]
**ETA**: [When will it be ready?]
```

---

### Phase 2: Design Update (If gaps found)

#### 2.1 Update Design Documents
**Time**: 1-4 hours (depending on gaps)
**Owner**: Developer + Architect + PM

**Priority Order** (Update in this sequence):

1. **Technical Specification** (Highest Priority)
   - Use template: `.claude/templates/yaml-frontmatter-technical-spec.md`
   - Include: BDD requirements, API contracts, data model
   - Get CTO approval: `status: CTO_APPROVED`

2. **Architecture Decision Record** (If new pattern)
   - Use template: `.claude/templates/yaml-frontmatter-adr.md`
   - Document: Decision criteria, options, chosen approach
   - Get CTO/CPO/CEO approval: `status: APPROVED`

3. **API Specification** (If new endpoints)
   - Location: `docs/01-planning/05-API-Design/API-Specification.md`
   - Add: Request/response schemas, error codes
   - Validate: OpenAPI 3.0 compliance

4. **Data Model** (If database changes)
   - Location: `docs/01-planning/04-Data-Model/Data-Model-ERD.md`
   - Update: ERD diagram, table definitions
   - Write: Alembic migration script

5. **Sprint Plan** (If scope changed)
   - Update: Acceptance criteria, story points, timeline
   - Flag: Scope change to PM/CTO
   - Revalidate: Team capacity, dependencies

**Documentation Update Checklist**:
- [ ] YAML frontmatter complete (9 required fields)
- [ ] BDD format used (GIVEN-WHEN-THEN)
- [ ] Acceptance criteria measurable
- [ ] Cross-references validated
- [ ] Approval workflow triggered
- [ ] Team notified of changes

---

#### 2.2 Get Design Approval
**Time**: 30 minutes - 2 days (depending on changes)
**Owner**: PM + CTO

**Approval Matrix**:

| Change Type | Approver | Timeline |
|-------------|----------|----------|
| **New Technical Spec** | CTO | 1-2 days |
| **New ADR** | CTO + CPO + CEO | 2-3 days |
| **API Change (breaking)** | CTO + Backend Lead | 1 day |
| **API Change (additive)** | Backend Lead | 4 hours |
| **Data Model Change** | Architect + CTO | 1 day |
| **Scope Change** | PM + CTO | 1-2 days |

**Approval Process**:
1. Create PR with documentation updates
2. Tag approvers in PR (use GitHub @mentions)
3. Wait for approval (DO NOT implement until approved)
4. Update document `status` field after approval
5. Merge documentation PR
6. THEN start implementation

**Fast-Track Approval** (For urgent P0 work):
- Slack CTO with: "URGENT: Need approval for [SPEC/ADR/API]"
- Provide: 1-paragraph summary + link to PR
- Get verbal approval → Document in PR comments
- Formalize approval in retrospective

---

### Phase 3: Implementation (After design approved)

#### 3.1 Code with Confidence
**Owner**: Developer

**Now you can implement because**:
- ✅ Design is documented and approved
- ✅ Requirements are clear (BDD format)
- ✅ Acceptance criteria are measurable
- ✅ API contracts are defined
- ✅ Data model is finalized
- ✅ No surprises during code review

**Implementation Checklist**:
- [ ] Follow approved technical spec exactly
- [ ] Implement BDD scenarios as tests first (TDD)
- [ ] Use approved API contracts (no deviation)
- [ ] Follow approved data model (no schema drift)
- [ ] Reference spec/ADR in code comments
- [ ] Update docs if edge cases discovered

**Zero Mock Policy** (Reminder):
- ❌ NO mocks in production code
- ❌ NO `// TODO: Implement` placeholders
- ❌ NO `return { mock: 'data' }`
- ✅ Real implementations only
- ✅ Integration tests with real services

---

#### 3.2 Validate Against Design
**Time**: 30 minutes before PR
**Owner**: Developer

**Pre-PR Validation**:
- [ ] **Requirements Coverage**
  - All BDD scenarios implemented?
  - All acceptance criteria met?
  - Edge cases handled?

- [ ] **API Contract Compliance**
  - Request/response match spec?
  - Error codes match spec?
  - OpenAPI validation passes?

- [ ] **Data Model Compliance**
  - Tables match ERD?
  - Constraints enforced?
  - Migrations tested?

- [ ] **Performance Budget**
  - API p95 < 100ms?
  - Database queries < 50ms?
  - Frontend render < 100ms?

- [ ] **Security Checklist**
  - OWASP ASVS L2 requirements met?
  - Input validation present?
  - SQL injection prevented?

**If ANY validation fails**:
1. Fix the code (NOT the design)
2. If design is wrong → Update design + get re-approval
3. Never silently deviate from approved design

---

### Phase 4: Documentation Sync (After implementation)

#### 4.1 Update Implementation Notes
**Time**: 15-30 minutes
**Owner**: Developer

**Add to Technical Spec**:
```markdown
## Implementation Notes

**Implemented**: YYYY-MM-DD
**Developer**: [Name]
**Sprint**: SPRINT-XXX
**PR**: #1234

**Deviations from Spec** (if any):
- [Deviation 1] - Reason: [Why?] - Approved by: [CTO/Architect]

**Edge Cases Discovered**:
- [Edge case 1] - Handled by: [Solution]

**Performance Results**:
- API p95 latency: Xms (target: <100ms)
- Test coverage: Y% (target: 95%)
```

---

#### 4.2 Update Cross-References
**Time**: 10 minutes
**Owner**: Developer

- [ ] Link code to spec in PR description
- [ ] Add spec reference in code comments
  ```python
  # Implementation of SPEC-0013 Section 2.3
  # See: docs/02-design/14-Technical-Specs/SPEC-0013-*.md
  ```
- [ ] Update sprint plan with completion status
- [ ] Tag spec/ADR in commit message
  ```bash
  git commit -m "feat: Implement team invitation (SPEC-0013, ADR-043)"
  ```

---

## 🚨 Anti-Patterns (What NOT to Do)

### ❌ Anti-Pattern 1: "Code First, Document Later"
**Problem**: Implement first, then write specs to match code
**Why it fails**: Design decisions not reviewed, rework needed after code review
**Cost**: 2-3x development time (write code, rewrite after design review)
**Better approach**: Design-first (this checklist)

---

### ❌ Anti-Pattern 2: "Design Docs Are Optional"
**Problem**: Skip design docs for "small changes"
**Why it fails**: Small changes accumulate, architecture drift
**Cost**: Technical debt, future refactoring
**Better approach**: Document EVERYTHING, use lightweight templates for small changes

---

### ❌ Anti-Pattern 3: "Outdated Docs Are Fine"
**Problem**: Use old specs without checking currency
**Why it fails**: Implement deprecated approach, waste time
**Cost**: Full reimplementation
**Better approach**: Always check `last_updated` and `status` fields

---

### ❌ Anti-Pattern 4: "I'll Update Docs After PR Merge"
**Problem**: Merge code without updating docs
**Why it fails**: Docs diverge from code, next developer confused
**Cost**: Knowledge loss, onboarding friction
**Better approach**: Docs + code in same PR, both reviewed together

---

## ✅ Success Metrics

**Design-First Compliance** (Measured per PR):
- [ ] Design docs read before implementation (self-reported)
- [ ] Documentation gaps identified and fixed (tracked in PR)
- [ ] CTO approval received before coding (PR comments)
- [ ] Implementation matches approved design (code review)
- [ ] Cross-references updated (PR description + commits)

**Team-Level Metrics** (Measured per sprint):
- **Design-First Adherence**: % of PRs that followed this checklist
  - Target: 100%
  - Measurement: PR review checklist

- **Documentation Currency**: % of docs updated in last 30 days
  - Target: 80%+
  - Measurement: Compliance dashboard

- **Rework Rate**: % of PRs requiring redesign after initial review
  - Target: <5%
  - Measurement: GitHub PR labels

---

## 🎓 Training & Onboarding

**New Developer Onboarding**:
- **Day 1**: Read this checklist
- **Day 2**: Shadow senior dev following this process
- **Day 3**: Practice on sample task (with mentor review)
- **Week 2**: First real task using this checklist

**Checklist Quiz** (100% required):
1. What MUST you read before implementing? (Answer: Technical spec, ADRs, Sprint plan)
2. What status indicates an approved design? (Answer: CTO_APPROVED or APPROVED)
3. What do you do if design doc is outdated? (Answer: Update it and get re-approval)
4. Can you deviate from approved design? (Answer: No, unless you get re-approval)

---

## 📚 References

**Templates**:
- [Technical Spec Template](.claude/templates/yaml-frontmatter-technical-spec.md)
- [ADR Template](.claude/templates/yaml-frontmatter-adr.md)
- [Sprint Plan Template](.claude/templates/yaml-frontmatter-sprint-plan.md)

**SDLC 6.0.0 Framework**:
- [Section 8: Specification Standard](../SDLC-Enterprise-Framework/08-Section-8-Specification-Standard.md)
- [Design-First Principles](../SDLC-Enterprise-Framework/02-Process-Guides/Design-First-Development.md)

**Project Docs**:
- [Technical Specifications](../docs/02-design/14-Technical-Specs/)
- [ADRs](../docs/02-design/01-ADRs/)
- [API Specification](../docs/01-planning/05-API-Design/API-Specification.md)

---

## 🔄 Continuous Improvement

**Retrospective Questions** (Every sprint):
1. Did we follow Design-First checklist?
2. How many PRs required redesign? (Target: <5%)
3. How many docs were outdated? (Target: <20%)
4. What can we improve in this process?

**Quarterly Review**:
- Update checklist based on lessons learned
- Add new anti-patterns discovered
- Refine approval timelines
- Celebrate Design-First wins

---

**Checklist Version**: 1.0.0
**Created**: January 30, 2026
**Author**: CTO + Architect
**Next Review**: April 30, 2026 (Quarterly)
**Status**: ACTIVE

---

**CTO Mandate**: "Kiểm tra và cập nhật tài liệu thiết kế và yêu cầu đặc tả TRƯỚC KHI implement. This is not optional—it's how we build with discipline." ✅
