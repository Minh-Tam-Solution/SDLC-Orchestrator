# ADR-040: App Builder Integration - Strategic Necessity

**Status**: APPROVED
**Date**: January 27, 2026
**Sprint**: Sprint 106
**Deciders**: CTO (Tai), CEO, Product Team
**Related**: ADR-039 (Technical Implementation), ADR-022 (Multi-Provider Codegen)

---

## Context

### Market Reality (January 2026)

All major AI development tools now provide instant app scaffolding as a **table stakes feature**:

| Tool | Price | Has Scaffolding | Has Governance | Market Share |
|------|-------|-----------------|----------------|--------------|
| **Cursor AI** | $20/mo | ✅ | ⚠️ (Self-claimed) | 40% |
| **Bolt.new** | Free | ✅ | ❌ | 25% |
| **Windsurf** | Free | ✅ | ❌ | 15% |
| **v0.dev** | Free | ✅ | ❌ | 10% |
| **SDLC Orchestrator** (current) | $99/mo | ❌ | ✅ | <1% |
| **SDLC Orchestrator** (with App Builder) | $99/mo | ✅ | ✅ | **Target: 5-10%** |

### Business Problem

**Customer Expectation**: One tool for complete workflow (init → code → review → deploy)

**Current State**: SDLC Orchestrator provides governance (50% of workflow)

**Customer Question**: *"Why pay $99/month for governance-only when Cursor $20/month has scaffolding + governance?"*

**Current Answer**: ❌ "Our governance is better quality" → Weak positioning

**Needed Answer**: ✅ "We provide complete workflow with enterprise-grade governance" → Strong positioning

### Business Impact Analysis

```yaml
WITHOUT App Builder:
  Conversion: 15-20%
  Churn: 30%
  ARPU: $99
  Annual Revenue (100 trials/mo): $14,964

  Customer sees: "Governance-only tool"
  Customer thinks: "Need Cursor ($20) + SDLC ($99)"
  Customer does: Abandons → Uses Cursor alone

WITH App Builder:
  Conversion: 25-35%
  Churn: 15-20%
  ARPU: $99-149
  Annual Revenue (100 trials/mo): $30,288

  Customer sees: "Complete AI dev platform"
  Customer thinks: "1 tool for full workflow"
  Customer does: Converts → Stays long-term

Revenue Impact: +$15,324/year (+102% increase)
```

### Strategic Clarification

**Question**: Does this contradict Jan 19 decision to "Pause EP-06" and pursue Wrapper Strategy?

**Answer**: NO. **Two different market segments, two different solutions:**

| Decision | Date | Target Segment | Strategy | Status |
|----------|------|----------------|----------|--------|
| **Wrapper Strategy** | Jan 19 | Enterprise (large teams, existing codebases) | Govern external AI coders | ✅ Active (Q2 2026) |
| **App Builder** | Jan 27 | SME (small teams, new projects) | Provide scaffolding + governance | ✅ Active (Sprint 106) |

**Enterprise Track**: Governance wrapper for Cursor/Copilot ($500-2000/month)
**SME Track**: Complete solution with scaffolding ($99-299/month)

---

## Problem Statement

**Core Problem**: Without app scaffolding capability, SDLC Orchestrator appears "incomplete" compared to competitors, resulting in:

1. **Low conversion**: 15-20% (missing 30-50% due to partial workflow)
2. **High churn**: 30% (users switch to Cursor for "complete" solution)
3. **Weak pricing justification**: $99/month for 50% workflow is hard sell
4. **Competitive disadvantage**: All competitors have instant scaffolding

**Root Cause**: Positioning as "governance specialist" instead of "complete AI dev platform"

---

## Decision

**Add app scaffolding as HYGIENE FEATURE, not strategic expansion.**

### Implementation Approach

1. **4 Deterministic Templates** (Sprint 106):
   - Next.js Fullstack (Next.js + Prisma + NextAuth)
   - Next.js SaaS (Next.js + Stripe + Subscriptions)
   - FastAPI (Python + SQLAlchemy + JWT)
   - React Native (Expo + Zustand + Navigation)

2. **Quality Gates Enforced**:
   - Gate 1 (Syntax): MANDATORY - Code must compile
   - Gate 2 (Security): MANDATORY - No OWASP Top 10 violations
   - Gate 3 (Context): OPTIONAL - Import consistency (may fail for scaffolds)
   - Gate 4 (Tests): OPTIONAL - Scaffolds may not have tests

3. **Evidence Vault Integration**: Full audit trail with SHA256 integrity hashing

4. **CRP for High-Risk Projects**: Architect approval when risk >= 50

5. **Fallback Chain**: app-builder → ollama → claude (when confidence < 0.75)

### Positioning

- **NOT**: "We're building code generator" ❌
- **YES**: "We're providing complete dev workflow with governance" ✅

### Cost Structure

- **Planning Phase**: LLM tokens for risk analysis (~$0.02)
- **Execution Phase**: Deterministic scaffolding ($0.00)
- **Total**: Transparent two-phase breakdown to avoid misleading "$0" claim

---

## Alternatives Considered

### Alternative 1: Wrapper-Only Strategy (Do Nothing)

**Approach**: Focus exclusively on Wrapper Strategy for Enterprise, no SME scaffolding.

**Pros**:
- ✅ Clear strategic focus (governance-only)
- ✅ No maintenance burden (13 templates)
- ✅ No scope creep into code generation

**Cons**:
- ❌ **Loses SME market entirely** (50% of addressable market)
- ❌ Appears "incomplete" vs competitors (all have scaffolding)
- ❌ Low conversion (15-20%) persists
- ❌ High churn (30%) persists
- ❌ Weak pricing justification ($99 for partial workflow)

**Risk**: Market consolidation. If competitors add governance (Cursor already claims it), we have NO differentiator.

**Decision**: ❌ **REJECTED** - Business necessity trumps strategic purity.

---

### Alternative 2: Partner with Bolt.new / v0.dev

**Approach**: Integration partnership instead of building in-house.

**Pros**:
- ✅ Fast time-to-market (2 weeks integration vs 2 months build)
- ✅ No maintenance burden (partner handles templates)
- ✅ Leverage partner's brand (Bolt.new has 25% market share)

**Cons**:
- ❌ **Revenue sharing** (70/30 split = -30% margin)
- ❌ **No control over quality gates** (partner may not support our 4-Gate pipeline)
- ❌ **Evidence Vault integration complexity** (partner may not expose artifacts)
- ❌ **Dependency risk** (partner pivot = feature loss)
- ❌ **Competitive positioning** ("We use Bolt.new too" vs "We have our own")

**Risk**: Partner becomes competitor. Bolt.new adds governance → direct competitor with our revenue share.

**Decision**: ❌ **REJECTED** - Loss of control over quality + revenue share too high.

---

### Alternative 3: Build In-House with Full Orchestration (Original Plan)

**Approach**: Implement full hybrid approach (Option C) in Sprint 106 with:
- Planning Sub-Agent for template recommendation
- CRP workflow for all template selections
- AI-powered customization after scaffold

**Pros**:
- ✅ Full governance integration (CRP, Evidence Vault, quality gates)
- ✅ Best user experience (guided template selection)
- ✅ Architect approval for all generations

**Cons**:
- ❌ **10-day implementation** (vs 4-day MVP)
- ❌ **Higher complexity** (planning + provider + coordinator)
- ❌ **Delayed market entry** (Feb 6 vs Jan 31)
- ❌ **Capacity constraint** (8.5 FTE team already at Sprint 105 capacity)

**Risk**: Over-engineering. Customers want instant scaffolding, not approval workflows for templates.

**Decision**: ⚠️ **PARTIALLY ACCEPTED** - Build incrementally:
- **Sprint 106 (MVP)**: Deterministic scaffolder only (4 days)
- **Sprint 107 (Full)**: Add planning orchestration (3 days)

---

### Alternative 4: Buy OpenCode / Use Ollama Directly (Minimal)

**Approach**: Expose Ollama codegen directly without templates, let AI generate from scratch.

**Pros**:
- ✅ Fastest implementation (2 days)
- ✅ No template maintenance
- ✅ Maximum flexibility (any tech stack)

**Cons**:
- ❌ **Inconsistent quality** (AI hallucinations, non-standard patterns)
- ❌ **High latency** (30-60s generation time)
- ❌ **High cost** ($0.50-1.00 per generation vs $0.00 for templates)
- ❌ **No competitive differentiation** (everyone has Ollama access)
- ❌ **Fails Gate 1-2 often** (syntax errors, security issues)

**Risk**: Quality degradation. SDLC Orchestrator's moat is quality gates - if we feed low-quality input, gates fail frequently → bad UX.

**Decision**: ❌ **REJECTED** - Conflicts with quality-first positioning.

---

## Selected Alternative: Build In-House (Incremental)

**Sprint 106 (MVP)**: Deterministic scaffolder (4 templates, 4 days)
**Sprint 107 (Full)**: Planning orchestration (CRP, sub-agent, 3 days)

**Reasoning**:
1. **Speed**: 4-day MVP vs 10-day full build
2. **Control**: Own quality + evidence + governance integration
3. **Zero cost**: Deterministic scaffolding ($0 per generation)
4. **Incremental**: Ship value early, add orchestration later
5. **Risk mitigation**: MVP validates demand before full investment

---

## Rationale

### Why NOW (January 2026)?

1. **Market moved faster**: Cursor, Windsurf gained massive traction (Q4 2025)
2. **Customer feedback**: "Need complete solution, not governance-only"
3. **Competitive parity**: Without scaffolding, we look incomplete
4. **Business necessity**: +102% revenue impact justifies 4-day investment

### Why In-House (vs Partnership)?

| Factor | In-House | Partnership | Winner |
|--------|----------|-------------|--------|
| **Quality Control** | 100% control | Depends on partner | 🏆 In-House |
| **Revenue** | 100% retained | 70% after split | 🏆 In-House |
| **Evidence Vault** | Native integration | Complex API | 🏆 In-House |
| **Time to Market** | 4 days (MVP) | 2 weeks (integration) | 🏆 In-House |
| **Maintenance** | 4 templates initially | Partner handles | ⚖️ Tie |
| **Risk** | Maintenance burden | Dependency risk | ⚖️ Tie |

**Decision**: In-house wins on control + revenue, acceptable maintenance tradeoff.

### Why Deterministic Templates (vs AI Generation)?

| Factor | Templates | AI Generation | Winner |
|--------|-----------|---------------|--------|
| **Quality** | Predictable, passes gates | Inconsistent, fails often | 🏆 Templates |
| **Cost** | $0.00 | $0.50-1.00 | 🏆 Templates |
| **Speed** | <1s | 30-60s | 🏆 Templates |
| **Flexibility** | 4 stacks | Unlimited stacks | AI Generation |
| **Maintenance** | Template updates | Prompt tuning | ⚖️ Tie |

**Decision**: Templates win on quality + cost + speed. Flexibility tradeoff acceptable (expand templates later).

---

## Consequences

### Positive

✅ **Competitive parity**: Match Cursor, Bolt.new, Windsurf on scaffolding
✅ **Justify pricing**: $99/month for 100% workflow (vs 50%)
✅ **Higher conversion**: 25-35% (vs 15-20%)
✅ **Lower churn**: 15-20% (vs 30%)
✅ **Complete workflow**: init → code → review → deploy
✅ **Revenue impact**: +$15,324/year (+102% increase)

### Negative

⚠️ **Maintenance burden**: 4 templates to keep updated
⚠️ **Template versioning**: Next.js 14 vs 15 complexity
⚠️ **Quality gate tuning**: Balance strictness vs usability
⚠️ **Scope creep risk**: Users may expect 13 templates immediately

### Neutral

⚪ **Two-track strategy**: SME (app-builder) + Enterprise (wrapper)
⚪ **Incremental delivery**: MVP now, full orchestration later

---

## Risk Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **Template drift** | High | Medium | Automated dependency scanning, 6-month review cycle |
| **Gate 2 (Security) false positives** | Medium | High | Multi-tool validation (bandit + npm audit + semgrep) |
| **User expects AI customization** | Medium | Low | Clear messaging: "Scaffold → Customize → Govern" |
| **Maintenance burden (13 templates)** | High | Medium | Usage-based retention, deprecate <5 uses/6mo |
| **Conflict with EP-06 Vietnamese** | Low | Medium | Intent router with confidence thresholds |

---

## Success Metrics (Business-Focused)

| Metric | Baseline (No App Builder) | Target (With App Builder) | Timeframe |
|--------|---------------------------|---------------------------|-----------|
| **Trial Conversion** | 15-20% | **25-35%** | 3 months |
| **Churn Rate** | 30% | **15-20%** | 6 months |
| **ARPU** | $99 | **$99-149** | 6 months |
| **Competitive Win Rate** | 30% vs Cursor | **50-60%** | 6 months |
| **Time to First Value** | 45 min (manual setup) | **<5 min** (scaffold) | Immediate |
| **Customer Satisfaction** | 7.2/10 | **8.5/10** | 3 months |

**Revenue Impact Calculation**:
```
Scenario 1 (No App Builder):
  100 trials/month × 18% conversion × $99/month × 70% retention = $1,247/month
  Annual: $14,964

Scenario 2 (With App Builder):
  100 trials/month × 30% conversion × $99/month × 85% retention = $2,524/month
  Annual: $30,288

Lift: +$15,324/year (+102% revenue increase)
```

---

## Implementation Plan

### Sprint 106 (4 days)

| Day | Phase | Deliverable |
|-----|-------|-------------|
| **Day 0** | Prerequisites | ADR-040, Intent Router design, test scenarios |
| **Day 1-2** | Template Development | 4 templates with smoke tests |
| **Day 3** | Provider Integration | app_builder_provider.py + registry |
| **Day 4** | Testing & Documentation | E2E test + ADR-039 + Sprint plan |

### Sprint 107 (3 days) - Deferred

- Planning Sub-Agent integration
- CRP workflow for template selection
- Coordinator glue (planning → execution)

---

## Approval

**Status**: ✅ **APPROVED**

**Approval Conditions** (All Met):

1. ✅ Two-track strategy confirmed (Enterprise + SME)
2. ✅ 4 templates maximum scope for Sprint 106
3. ✅ ADR-040 completed with Alternatives section

**Signatures**:
- **CTO (Tai)**: ✅ APPROVED - January 27, 2026 23:50
- **CEO**: ⏳ Pending review (expected approval Jan 28)
- **Product**: ✅ APPROVED - January 27, 2026

**Next Checkpoint**: Sprint 106 Day 5 Review (Feb 1, 2026)

---

## References

- [ADR-039: App Builder Technical Implementation](./ADR-039-App-Builder-Deterministic-Scaffolder.md)
- [ADR-022: Multi-Provider Codegen Architecture](../01-ADRs/ADR-022-Multi-Provider-Codegen-Architecture.md)
- [Sprint 105 Design](../../../04-build/02-Sprint-Plans/SPRINT-105-DESIGN.md)
- [App Builder Skill](./.claude/skills/app-builder/SKILL.md)
- [Planning Mode Review](/home/dttai/.claude/plans/twinkly-waddling-dewdrop.md)

---

## Document Control

| Field | Value |
|-------|-------|
| **Version** | 1.0.0 |
| **Date** | January 27, 2026 |
| **Author** | Architecture Team + CTO |
| **Status** | APPROVED |
| **CTO Approval** | ✅ Jan 27, 2026 23:50 |
| **CEO Approval** | ⏳ Pending (expected Jan 28) |
| **Next Review** | Sprint 106 Day 5 (Feb 1, 2026) |
