# ADR-041: Framework 6.0 Governance System Design

**Version**: 1.0.0
**Status**: APPROVED
**Date**: January 28, 2026
**Author**: Backend Lead
**Approvers**: CEO, CTO, CPO
**Framework**: SDLC 6.1.0

---

## Context

### Problem Statement

The SDLC Orchestrator was assessed as "infrastructure without value" because:
1. Does NOT help CEO work faster than manual SDLC Framework usage
2. Does NOT help team work better
3. Has infrastructure but creates NO measurable VALUE

### Expert Review Findings (6 Fatal Gaps)

| Gap | Source | Severity |
|-----|--------|----------|
| GAP 1: Orchestrator ≠ Path of Least Resistance | Expert 1 (Product) | CRITICAL |
| GAP 2: Missing Governance Signals (CEO Intuition) | Expert 1 (Product) | CRITICAL |
| GAP 3: Stage Governance ≠ Daily Work | Expert 1 (Product) | CRITICAL |
| GAP 4: Context Authority Over-Engineered | Expert 2 (Technical) | MAJOR |
| GAP 5: Feedback Not Actionable | Expert 2 (Technical) | MAJOR |
| GAP 6: No Dogfooding | Expert 2 (Technical) | MAJOR |

### Critical Principle

```
"GOVERNANCE MUST BE THE FASTEST WAY"

If Orchestrator adds >5 min friction per PR → PRODUCT FAILS
If CEO time does NOT decrease → PRODUCT FAILS
If developers bypass governance → PRODUCT FAILS

Success = CEO works FASTER + Team works BETTER
```

---

## Decision

Implement a **Quality Assurance System** (Pillar 7 in SDLC 6.1.0) with 6 key components:

### Component 1: Auto-Generation Layer

**Purpose**: Reduce developer friction from 30 min → <5 min per PR

| Generator | Trigger | Output | Time Saved |
|-----------|---------|--------|------------|
| Intent Skeleton | task_created | Intent document | ~15 min |
| Ownership Suggestion | file_modified | @owner annotation | ~2 min |
| Context Attachment | pr_created | ADR/spec links | ~5 min |
| Attestation Template | ai_code_detected | Pre-filled form | ~8 min |

**Technical Design**:
```python
class AutoGenerationService:
    async def generate_intent_skeleton(self, task: Task) -> IntentDocument
    async def suggest_ownership(self, file_path: str, repo: Repository) -> OwnershipSuggestion
    async def auto_attach_context(self, pr: PullRequest) -> PRContextAttachment
    async def pre_fill_attestation(self, ai_session: AISession) -> AttestationForm
```

### Component 2: Governance Signals Engine (Vibecoding Index)

**Purpose**: Capture CEO's "code smell" intuition as non-blocking signals

| Signal | Weight | Description |
|--------|--------|-------------|
| Architectural Smell | 0.25 | God class, feature envy, shotgun surgery |
| Abstraction Complexity | 0.15 | Inheritance depth, interface count |
| AI Dependency Ratio | 0.20 | AI lines / total lines |
| Change Surface Area | 0.20 | Files touched, modules affected |
| Drift Velocity | 0.20 | Pattern changes over 7 days |

**Vibecoding Index Routing**:
```yaml
Green (0-30): Auto-approve (CEO doesn't need to look)
Yellow (31-60): Queue for Tech Lead
Orange (61-80): Queue for CEO (should review)
Red (81-100): Block + CEO immediate attention
```

### Component 3: Stage-Aware PR Gating

**Purpose**: Prevent working ahead of design

| Stage | Allows | Blocks | Message |
|-------|--------|--------|---------|
| 00-Foundation | docs/00-*/** | src/** | "Complete foundation first" |
| 01-Planning | docs/01-*/** | src/** | "Finish requirements first" |
| 02-Design | docs/02-*/**, schema.prisma | backend/app/** | "Approve architecture first" |
| 04-Build | ** | - | All code allowed with compliance |
| 05-Test | tests/**, bug fixes | new features | "Code freeze in effect" |

### Component 4: Context Authority MVP

**Purpose**: Validate code has proper context linkage (metadata only, NOT semantic)

| Check | Rule | Failure Action |
|-------|------|----------------|
| ADR Linkage | Every module references an ADR | ERROR: Orphan code |
| Design Doc Reference | New features have spec file | ERROR: No design |
| AGENTS.md Freshness | Updated within 7 days | WARNING: Stale context |
| Module Annotation | Header matches directory | ERROR: Organization confusion |

### Component 5: Actionable Feedback Templates

**Purpose**: Every error message includes CLI commands to fix

```markdown
❌ GOVERNANCE FAILED: Missing Ownership Declaration

📍 What Failed:
File `backend/app/services/test.py` has no @owner annotation.

🔧 How To Fix:
1. Open the file
2. Add at the top: `# @owner: @backend-lead`
3. Commit: `git add backend/app/services/test.py`

⚡ Quick Fix Command:
$ sdlcctl add-ownership --file backend/app/services/test.py --owner @backend-lead
```

### Component 6: Kill Switch + Break Glass

**Purpose**: Emergency bypass and automatic rollback

**Kill Switch Criteria**:
```yaml
auto_trigger:
  rejection_rate: ">80%"
  latency_p95: ">500ms"
  false_positive_rate: ">20%"
  developer_complaints: ">5/day"
rollback_to: "WARNING"
```

**Break Glass** (Emergency Bypass):
- Authorization: Tech Lead → CTO → CEO
- Audit: All bypass attempts logged
- Auto-revert: 24 hours if not properly approved

---

## Database Schema

### Tables (14 Total)

```sql
-- Core Governance
governance_submissions    -- PR/code submission records
governance_rejections     -- Rejection history with reasons
governance_evidence       -- Evidence attachments
governance_audit_log      -- Immutable audit trail

-- Ownership & Context
governance_ownership      -- File → owner mappings
context_authorities       -- ADR/spec linkage records
context_snapshots         -- Point-in-time context state

-- Contracts & Validation
governance_contracts      -- Quality contract definitions
contract_versions         -- Contract version history
contract_violations       -- Violation records

-- AI & Human Review
ai_attestations           -- AI code attestation records
human_reviews             -- Human review decisions

-- Exceptions & Escalation
governance_exceptions     -- Exception request records
escalation_log            -- Escalation history
```

---

## API Endpoints

### CEO Dashboard (12 endpoints)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| /api/v1/governance/ceo/summary | GET | Dashboard summary |
| /api/v1/governance/ceo/time-saved | GET | Time saved metrics |
| /api/v1/governance/ceo/routing-breakdown | GET | Routing distribution |
| /api/v1/governance/ceo/pending-decisions | GET | Pending decision queue |
| /api/v1/governance/ceo/weekly-summary | GET | Weekly metrics |
| /api/v1/governance/ceo/trends/time-saved | GET | Time saved trend |
| /api/v1/governance/ceo/trends/vibecoding | GET | Index trend |
| /api/v1/governance/ceo/top-rejections | GET | Top rejection reasons |
| /api/v1/governance/ceo/overrides | GET | Override history |
| /api/v1/governance/ceo/system-health | GET | System health status |
| /api/v1/governance/ceo/decisions/{id}/resolve | POST | Resolve decision |
| /api/v1/governance/ceo/decisions/{id}/override | POST | Record override |

### Governance Core (Existing)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| /api/v1/governance/submit | POST | Submit for validation |
| /api/v1/governance/evaluate | POST | Evaluate submission |
| /api/v1/governance/mode | GET/POST | Get/set governance mode |

---

## Success Metrics

### Primary: CEO Time Saved

| Period | Baseline | Target | Measurement |
|--------|----------|--------|-------------|
| Week 2 | 40h/sprint | 30h (-25%) | CEO time tracking |
| Week 4 | 40h/sprint | 20h (-50%) | CEO time tracking |
| Week 8 | 40h/sprint | 10h (-75%) | CEO time tracking |

### Secondary: Developer Experience

| Metric | Target | Measurement |
|--------|--------|-------------|
| Developer friction | <5 min/PR | Time to comply |
| First-pass rate | >70% | PRs pass first try |
| Auto-generation usage | >80% | Artifacts auto-generated |
| NPS | >50 | Developer survey |

### Tertiary: Governance Quality

| Metric | Target | Measurement |
|--------|--------|-------------|
| Vibecoding index avg | <40 | Calculated index |
| Bypass incidents | 0 | Audit log |
| Auto-reject accuracy | >95% | CEO agreement rate |

---

## Rollout Strategy

### Phase 1: Warning Mode (Week 1)
- Enable governance on Orchestrator repo
- Log violations but don't block
- Establish baseline metrics

### Phase 2: Soft Enforcement (Week 2)
- Block critical violations (missing ownership, missing intent, index >80)
- Warn medium violations (stale context, index 61-80)
- Measure friction and adjust

### Phase 3: Full Enforcement (Week 3+)
- All violations block
- Auto-approve green PRs
- Measure CEO time saved

---

## Consequences

### Positive

1. **CEO Time Reduction**: 40h → 10h per sprint (75% savings)
2. **Developer Friction**: <5 min per PR (vs 30 min manual)
3. **Code Quality**: Measurable vibecoding index
4. **Audit Trail**: Complete governance history

### Negative

1. **Learning Curve**: Developers need to learn new workflow
2. **False Positives**: Initial tuning required
3. **Maintenance**: Signals need periodic calibration

### Mitigations

1. **Kill Switch**: Auto-rollback on high rejection rate
2. **Feedback Loop**: Continuous improvement from PR reviews
3. **CEO Calibration**: Monthly review of signal weights

---

## References

- Pre-Phase 0 Documents:
  - CEO-WORKFLOW-CONTRACT.md (Signed Jan 27, 2026)
  - AUTO-GENERATION-FAIL-SAFE-POLICY.md (Signed Jan 27, 2026)
  - VIBECODING-INDEX-EXPLAINABILITY-SPEC.md (Signed Jan 27, 2026)
- Expert Reviews: Product Review (Expert 1), Technical Review (Expert 2)
- Framework: SDLC 6.1.0 Section 7 (Quality Assurance System)

---

## Approval

| Role | Name | Date | Signature |
|------|------|------|-----------|
| CEO | Tai | Jan 27, 2026 | ✅ APPROVED |
| CTO | - | Jan 28, 2026 | ⏳ PENDING |
| CPO | - | Jan 27, 2026 | ✅ APPROVED |

---

## Document Control

| Field | Value |
|-------|-------|
| **Version** | 1.0.0 |
| **Created** | January 28, 2026 |
| **ADR Number** | ADR-041 |
| **Status** | APPROVED |
| **Supersedes** | N/A |
