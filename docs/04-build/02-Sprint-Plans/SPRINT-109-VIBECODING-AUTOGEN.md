# Sprint 109: Vibecoding Index + Auto-Generation Complete

**Version**: 1.0.0
**Date**: February 5-11, 2026 (7 days)
**Status**: ✅ **85% COMPLETE** (All Engines Done, Tests Pending)
**Epic**: GOVERNANCE SYSTEM v1.0 - Anti-Vibecoding Implementation
**Framework**: SDLC 6.1.0
**Prerequisites**: Sprint 108 (Governance Foundation)

---

## Executive Summary

**Goal**: Complete 5-signal Vibecoding Index calculation and all 4 auto-generators to enable SOFT enforcement mode.

**Business Driver**: Enable CEO Time Savings through automated routing (Green auto-approve, Yellow to Tech Lead, Orange/Red to CEO).

**Scope**: Full Vibecoding Index (5 signals), 3 remaining auto-generators (Ownership, Context, Attestation), SOFT enforcement mode, first 20 Prometheus metrics.

---

## Sprint Goals

### Primary Goals

1. **Complete Vibecoding Index**: All 5 signal calculations implemented
2. **Complete Auto-Generation**: All 4 generators (Intent, Ownership, Context, Attestation)
3. **SOFT Enforcement**: Block critical paths only
4. **Prometheus Metrics**: First 20 metrics for observability
5. **CEO Calibration API**: Enable CEO feedback for index calibration

### Success Criteria

| Metric | Target | Verification |
|--------|--------|--------------|
| Vibecoding signals | 5/5 signals | Unit tests pass |
| Auto-generators | 4/4 generators | Integration tests pass |
| Latency targets | All met | Performance tests |
| SOFT mode | Deployable | Critical paths blocked |
| Prometheus metrics | 20/45 | Grafana query works |
| CEO calibration API | Functional | API test pass |

### Out of Scope (Sprint 110)

- ❌ FULL enforcement mode
- ❌ Kill switch automation
- ❌ CEO Dashboard UI
- ❌ Tech Dashboard UI
- ❌ Remaining 25 Prometheus metrics

---

## Day-by-Day Plan

### Day 1: Architectural Smell + Abstraction Complexity

**Signal 1: Architectural Smell (25%)**
- [ ] Implement God Class detection (>500 lines, >30 methods)
- [ ] Implement Feature Envy detection
- [ ] Implement Shotgun Surgery detection (>10 files)
- [ ] Implement Parallel Inheritance detection
- [ ] Implement Data Clumps detection

**Signal 2: Abstraction Complexity (15%)**
- [ ] Implement Deep Inheritance detection (>3 levels)
- [ ] Implement Interface Proliferation detection
- [ ] Implement Generic Type Depth detection
- [ ] Implement Factory Pattern Abuse detection
- [ ] Implement Premature Abstraction detection

**Exit Criteria:**
- [ ] Signal 1 returns 0-100 score
- [ ] Signal 2 returns 0-100 score
- [ ] Unit tests pass

---

### Day 2: AI Dependency + Change Surface Area

**Signal 3: AI Dependency Ratio (20%)**
- [ ] Parse AI code markers (comments, session metadata)
- [ ] Calculate AI-generated lines percentage
- [ ] Calculate human modification percentage
- [ ] Implement RED FLAG detection (>80% AI, <10% human)

**Signal 4: Change Surface Area (20%)**
- [ ] Count files changed (factor 30%)
- [ ] Count modules touched (factor 25%)
- [ ] Count API contracts affected (factor 25%)
- [ ] Detect database schema changes (factor 15%)
- [ ] Detect security-sensitive files (factor 5%)

**Exit Criteria:**
- [ ] Signal 3 returns 0-100 score
- [ ] Signal 4 returns 0-100 score
- [ ] RED FLAG triggers correctly

---

### Day 3: Drift Velocity + MAX CRITICALITY

**Signal 5: Drift Velocity (20%)**
- [ ] Track new patterns introduced
- [ ] Detect deprecated pattern usage
- [ ] Check naming consistency
- [ ] Run style violation checks (ruff)
- [ ] Calculate 7-day rolling score

**MAX CRITICALITY OVERRIDE**
- [ ] Load critical_paths.yaml patterns
- [ ] Match submission files against patterns
- [ ] Auto-boost index to 80 if critical path
- [ ] Add override reason to explainability

**Exit Criteria:**
- [ ] Signal 5 returns 0-100 score
- [ ] Critical paths auto-boost to Red
- [ ] Full 5-signal calculation works

---

### Day 4: Ownership + Context Generators

**Ownership Service**
- [ ] `suggest_ownership(file_path, task, repo)` → OwnershipSuggestion
- [ ] Source 1: CODEOWNERS file (confidence 1.0)
- [ ] Source 2: Git blame (confidence 0.8)
- [ ] Source 3: Directory pattern (confidence 0.6)
- [ ] Source 4: Task creator fallback (confidence 0.3)

**Context Service**
- [ ] `attach_context(submission, project)` → ContextDocument
- [ ] ADR search (full-text, relevance scoring)
- [ ] Design doc linkage
- [ ] AGENTS.md freshness check
- [ ] Module annotation validation

**Exit Criteria:**
- [ ] Ownership <2s latency
- [ ] Context <5s latency
- [ ] Fallbacks work

---

### Day 5: Attestation Generator + SOFT Mode

**Attestation Service**
- [ ] `generate_attestation(submission, ai_session)` → AttestationDocument
- [ ] Pre-fill from AI session metadata
- [ ] Calculate minimum review time
- [ ] Validate understanding confirmation
- [ ] Generate attestation form

**SOFT Enforcement Mode**
- [ ] Implement `GOVERNANCE_MODE = "SOFT"`
- [ ] Block only critical paths (security, payment, infra)
- [ ] Log Yellow/Orange/Red violations (don't block)
- [ ] Add bypass reason requirement for blocked paths

**Exit Criteria:**
- [ ] Attestation <3s latency
- [ ] SOFT mode blocks critical paths
- [ ] Non-critical paths logged only

---

### Day 6: Prometheus Metrics (20 metrics)

**Governance Metrics (10)**
- [ ] `governance_submissions_total` (counter)
- [ ] `governance_rejections_total` (counter)
- [ ] `governance_vibecoding_index` (histogram)
- [ ] `governance_routing_total` (counter by routing)
- [ ] `governance_signals_*` (5 histograms)

**Performance Metrics (5)**
- [ ] `api_request_duration_seconds` (histogram)
- [ ] `db_query_duration_seconds` (histogram)
- [ ] `llm_generation_duration_seconds` (histogram)
- [ ] `auto_generation_duration_seconds` (histogram by component)
- [ ] `cache_hit_rate` (gauge)

**Business Metrics (5)**
- [ ] `ceo_time_saved_hours` (gauge)
- [ ] `ceo_pr_review_reduction_percent` (gauge)
- [ ] `developer_friction_minutes` (histogram)
- [ ] `first_pass_rate_percent` (gauge)
- [ ] `auto_generation_usage_rate` (gauge)

**Exit Criteria:**
- [ ] All 20 metrics exposed at `/metrics`
- [ ] Grafana can query metrics
- [ ] No performance impact

---

### Day 7: CEO Calibration API + Integration Testing

**CEO Calibration API**
- [ ] `POST /api/v1/governance/calibration/override`
  - Record CEO agrees/disagrees with index
- [ ] `GET /api/v1/governance/calibration/history`
  - Calibration history for weight adjustment
- [ ] `PUT /api/v1/governance/calibration/weights`
  - Adjust signal weights (CEO + CTO only)

**Integration Testing**
- [ ] Test: Full flow (Submit → Index → Route → Auto-gen)
- [ ] Test: SOFT mode (block critical, log non-critical)
- [ ] Test: CEO calibration flow
- [ ] Test: All 4 auto-generators

**Exit Criteria:**
- [ ] All integration tests pass
- [ ] SOFT mode ready for deployment
- [ ] Calibration API functional

---

## Technical Specifications

### Vibecoding Index Complete Formula

```python
async def calculate_vibecoding_index(submission: Submission) -> VibecodingResult:
    # Calculate all 5 signals in parallel
    signals = await asyncio.gather(
        calculate_architectural_smell(submission),    # Signal 1
        calculate_abstraction_complexity(submission), # Signal 2
        calculate_ai_dependency_ratio(submission),    # Signal 3
        calculate_change_surface_area(submission),    # Signal 4
        calculate_drift_velocity(submission),         # Signal 5
    )

    arch, abstraction, ai_ratio, surface, drift = signals

    # Weighted sum
    index = (
        arch * 0.25 +
        abstraction * 0.15 +
        ai_ratio * 0.20 +
        surface * 0.20 +
        drift * 0.20
    )

    # MAX CRITICALITY OVERRIDE
    index = apply_max_criticality_override(submission, index)

    # Generate explainability
    explainability = generate_explainability(index, signals)

    return VibecodingResult(
        index=index,
        routing=determine_routing(index),
        signals=signals,
        explainability=explainability,
    )
```

### Auto-Generation Complete

| Generator | Input | Output | Latency |
|-----------|-------|--------|---------|
| Intent | Task, PR | IntentDocument | <10s |
| Ownership | File, Task, Repo | OwnershipSuggestion | <2s |
| Context | Submission, Project | ContextDocument | <5s |
| Attestation | Submission, Session | AttestationDocument | <3s |

### SOFT Mode Behavior

```python
SOFT_MODE_RULES = {
    "critical_paths": ["security/**", "payment/**", "auth/**"],
    "behavior": {
        "green": "auto_approve",           # No blocking
        "yellow": "log_only",              # Log, don't block
        "orange": "log_only",              # Log, don't block
        "red": "block_if_critical",        # Block only critical paths
    }
}
```

---

## Success Metrics

| Metric | Sprint 108 End | Sprint 109 End | Target |
|--------|----------------|----------------|--------|
| Vibecoding signals | 0/5 | 5/5 | ✅ |
| Auto-generators | 1/4 | 4/4 | ✅ |
| Governance mode | WARNING | SOFT | ✅ |
| Prometheus metrics | 0/45 | 20/45 | On track |
| CEO calibration | N/A | Functional | ✅ |

---

## Approval

**CTO Review**: ⏳ PENDING
**Tech Lead Review**: ⏳ PENDING
**Sprint Ready**: ⏳ PENDING (after Sprint 108 complete)

---

**Document Status**: ✅ PLANNING COMPLETE
**Next Action**: Sprint 108 completion → Sprint 109 execution
