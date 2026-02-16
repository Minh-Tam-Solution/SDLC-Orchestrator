---
sdlc_version: "6.0.6"
document_type: "ADR"
status: "PROPOSED"
sprint: "174"
spec_id: "ADR-055"
tier: "PROFESSIONAL"
stage: "02 - Design"
---

# ADR-055: Autonomous Codegen with 4-Gate Validation

**Status**: PROPOSED (Sprint 174 documentation, implementation Sprint 175-177)
**Date**: February 2026
**Author**: CTO Nguyen Quoc Huy
**Sprint**: Sprint 174 — Anthropic Patterns Integration
**Framework**: SDLC 6.0.6 (7-Pillar + Section 7 Quality Assurance)
**Supersedes**: None (new capability)
**References**: ADR-022 (Multi-Provider Codegen Architecture), ADR-054 (Anthropic Claude Code Best Practices)

---

## 1. Context

### 1.1 Problem Statement

Autonomous coding agents (Devin, SWE-Agent, AutoGPT) demonstrate impressive code generation capability but suffer from **60-80% feature waste** because they operate without a governance layer. Generated code is merged without:

- **Specification review** -- Features diverge from business intent within 2-3 autonomous iterations
- **Security validation** -- AI agents introduce CWE Top 25 vulnerabilities at 3-5x the rate of human developers
- **Architectural alignment** -- Technical debt accumulates across sessions with no ADR enforcement
- **Evidence traceability** -- No audit trail for SOC 2, GDPR, or HIPAA compliance requirements

### 1.2 Anthropic's Reference Implementation

Anthropic's `claude-quickstarts/autonomous-coding` repository provides a **two-agent pattern** for autonomous code generation:

| Component | Description |
|-----------|-------------|
| **Initializer Agent** | Reads `app_spec.txt`, generates `feature_list.json` with 50-200 test cases, sets up git repo |
| **Coding Agent** | Iterates through `feature_list.json`, implements one feature per session, commits to git |
| **Persistence** | `feature_list.json` (state) + `git` (code), survives session boundaries |
| **Verification** | Bash-based: `pytest`, `ruff`, basic subprocess allowlist |

**Strengths**: Clean separation of concerns, JSON-based state persistence, git-native workflow.

**Gaps identified**:
1. No quality gates between features (all features auto-continue)
2. Security validation is a bash allowlist, not semantic policy evaluation
3. No evidence collection or audit trail per feature
4. No escalation path when a feature repeatedly fails validation
5. No cost optimization (every call sends full context, no prompt caching)

### 1.3 SDLC Orchestrator Position

SDLC Orchestrator sits at **Layer 3-4** of the Software 3.0 stack -- above infrastructure, below AI coders. We already have:

- **OPA Policy Engine** (110 policies, REST API integration)
- **Evidence Vault** (MinIO S3, SHA256 integrity, 8-state lifecycle)
- **4-Gate Quality Pipeline** (Syntax, Security, Context, Tests -- from EP-06)
- **Multi-Provider Gateway** (Ollama, Claude, DeepCode fallback chain)
- **Governance Loop State Machine** (ADR-053, 6-state gate lifecycle)

The opportunity: enhance Anthropic's two-agent pattern with our existing governance infrastructure to create the first **governed autonomous codegen** system.

---

## 2. Decision

Adopt Anthropic's two-agent pattern (Initializer + Coding Agent) enhanced with the SDLC 6.0.5 4-Gate Quality Pipeline, OPA-based policy evaluation, and Evidence State Machine tracking per feature.

### 2.1 Two-Agent Pattern with JSON Persistence

Preserve Anthropic's core architecture with modifications for governance integration:

```
                    ┌──────────────────────────────────┐
                    │     Initializer Agent (Once)      │
                    │                                    │
                    │  1. Read app_spec.txt              │
                    │  2. Generate feature_list.json     │
                    │  3. Initialize git repository      │
                    │  4. Create evidence_manifest.json  │  ← NEW
                    │  5. Register OPA policy context    │  ← NEW
                    └──────────────┬───────────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────────┐
                    │     Coding Agent (Per Feature)    │
                    │                                    │
                    │  1. Read feature_list.json         │
                    │  2. Find next unimplemented item   │
                    │  3. Implement feature              │
                    │  4. Run 4-Gate Validation     ← NEW│
                    │  5. Update feature_list.json       │
                    │  6. Commit to git                  │
                    │  7. Upload evidence to Vault  ← NEW│
                    │  8. Continue or escalate      ← NEW│
                    └──────────────────────────────────┘
```

**State files** (JSON, committed to git):

| File | Purpose | Anthropic Original | SDLC Enhancement |
|------|---------|-------------------|------------------|
| `feature_list.json` | Feature tracking with pass/fail status | Yes | Add `gate_status`, `evidence_ids`, `retry_count` fields |
| `evidence_manifest.json` | Per-feature evidence chain | No | New: links features to Evidence Vault artifacts |
| `.sdlc-policy-context.json` | OPA policy bindings for this project | No | New: project tier, required gates, policy pack |

### 2.2 4-Gate Quality Pipeline (Per Feature)

Each feature generated by the Coding Agent passes through 4 gates before being marked as complete. Gates execute sequentially; failure at any gate triggers retry or escalation.

```
Feature Implementation
        │
        ▼
   ┌─────────┐   FAIL    ┌─────────────┐
   │  G1:    │──────────→│  Retry with  │
   │  Spec   │           │  LLM feedback│
   │  Review │           └──────┬──────┘
   └────┬────┘                  │
        │ PASS                  │ (max 3)
        ▼                       │
   ┌─────────┐                  │
   │  G2:    │──────────────────┘
   │  SAST   │   FAIL
   │  Scan   │
   └────┬────┘
        │ PASS
        ▼
   ┌─────────┐
   │  G3:    │   FAIL
   │  Test   │──────────────────┐
   │  Suite  │                  │
   └────┬────┘                  │
        │ PASS                  │
        ▼                       │
   ┌─────────┐                  │
   │  G4:    │                  │
   │  Human  │ (>500 LOC only)  │
   │  Review │                  │
   └────┬────┘                  │
        │ PASS                  │
        ▼                       ▼
   ┌─────────┐           ┌──────────┐
   │APPROVED │           │ESCALATED │
   │(commit) │           │(to human)│
   └─────────┘           └──────────┘
```

**Gate specifications**:

| Gate | Name | Validation | Latency Target | Tools |
|------|------|-----------|----------------|-------|
| G1 | Spec Review | Feature implementation matches `feature_list.json` spec; no scope creep; imports align with ADRs | <10s | LLM semantic comparison (cached context) |
| G2 | SAST Scan | Zero critical/high vulnerabilities; AGPL containment check; CWE Top 25 coverage | <15s | Semgrep (subprocess), OPA policy evaluation |
| G3 | Test Suite | All existing tests pass; new feature has >80% branch coverage; no regressions | <60s | pytest (Dockerized), coverage.py |
| G4 | Human Review | Required for features >500 LOC; optional for <500 LOC; CTO override available | Async | Notification via Web UI, CLI, or Extension |

### 2.3 OPA-Based Policy Evaluation

Replace Anthropic's bash subprocess allowlist with semantic OPA policies:

```rego
# policy-packs/rego/autonomous-codegen/feature_gate.rego
package sdlc.autonomous.feature_gate

import rego.v1

# G1: Spec alignment check
spec_aligned if {
    input.feature.files_changed <= input.feature.spec.max_files
    input.feature.imports_added == input.feature.spec.expected_imports
    not scope_creep_detected
}

scope_creep_detected if {
    extra_files := input.feature.files_changed - input.feature.spec.expected_files
    extra_files > 2
}

# G2: Security gate
security_passed if {
    input.sast.critical_count == 0
    input.sast.high_count == 0
    not agpl_contamination
}

agpl_contamination if {
    some dep in input.dependencies
    dep.license in {"AGPL-3.0", "AGPL-3.0-only", "AGPL-3.0-or-later"}
}

# G3: Test gate
tests_passed if {
    input.tests.all_passed == true
    input.tests.branch_coverage >= 0.80
    input.tests.regression_count == 0
}

# G4: Human review trigger
human_review_required if {
    input.feature.lines_of_code > 500
}

human_review_required if {
    input.feature.touches_auth == true
}

human_review_required if {
    input.feature.touches_payments == true
}

# Final verdict
feature_approved if {
    spec_aligned
    security_passed
    tests_passed
    not human_review_required
}

feature_needs_review if {
    spec_aligned
    security_passed
    tests_passed
    human_review_required
}
```

**Advantages over bash allowlist**:
- **Semantic**: Policies evaluate meaning (scope creep, AGPL contamination), not just command safety
- **Composable**: Policy packs per project tier (LITE skips G4, ENTERPRISE requires all 4)
- **Auditable**: Every evaluation stored in Evidence Vault with full decision trace
- **Updateable**: Policies updated without modifying agent code

### 2.4 Evidence State Machine (Per Feature)

Each feature tracks its own evidence lifecycle through the 8-state machine (aligned with ADR-053 governance loop):

```
generated → validating → [retrying] → evidence_locked → awaiting_vcr → merged
                ↓                           ↑
            escalated ──────────────────────┘
                ↓
            aborted
```

| State | Description | Trigger |
|-------|-------------|---------|
| `generated` | Coding Agent produced implementation | Feature code committed to git |
| `validating` | 4-Gate Pipeline evaluating | G1-G4 gates running sequentially |
| `retrying` | Gate failed, LLM regenerating with feedback | Retry count < max_retries (3) |
| `escalated` | Max retries exhausted, awaiting human | retry_count >= 3 OR G4 triggered |
| `evidence_locked` | All gates passed, evidence immutable | G1-G4 all PASS (or G4 human APPROVED) |
| `awaiting_vcr` | Validation Completion Report pending | Evidence locked, VCR not yet generated |
| `merged` | Feature merged to main branch | VCR approved, PR merged |
| `aborted` | Feature abandoned | Human decision or timeout (configurable) |

**Evidence artifacts per feature**:

| Artifact | Gate | Storage | Retention |
|----------|------|---------|-----------|
| `spec_review_result.json` | G1 | Evidence Vault (MinIO) | 90 days |
| `sast_report.json` | G2 | Evidence Vault (MinIO) | 90 days |
| `test_results.json` | G3 | Evidence Vault (MinIO) | 90 days |
| `human_review_decision.json` | G4 | Evidence Vault (MinIO) | 365 days |
| `feature_diff.patch` | All | Git + Evidence Vault | Permanent |
| `llm_conversation_log.json` | All | Evidence Vault (MinIO) | 90 days |

### 2.5 Retry Logic with Automatic Escalation

```python
MAX_RETRIES = 3  # Configurable per project tier

async def validate_feature(
    feature: Feature,
    coding_agent: CodingAgent,
    retry_count: int = 0
) -> FeatureResult:
    """
    Validation loop with deterministic feedback and escalation.

    Args:
        feature: Feature specification from feature_list.json
        coding_agent: Active coding agent session
        retry_count: Current retry attempt (0-indexed)

    Returns:
        FeatureResult with status and evidence chain

    Raises:
        EscalationRequired: When max_retries exceeded
    """
    # Run 4-Gate Pipeline
    g1_result = await run_spec_review(feature)
    if not g1_result.passed:
        if retry_count >= MAX_RETRIES:
            return await escalate_to_human(feature, "G1", g1_result)
        return await retry_with_feedback(
            feature, coding_agent, g1_result, retry_count + 1
        )

    g2_result = await run_sast_scan(feature)
    if not g2_result.passed:
        if retry_count >= MAX_RETRIES:
            return await escalate_to_human(feature, "G2", g2_result)
        return await retry_with_feedback(
            feature, coding_agent, g2_result, retry_count + 1
        )

    g3_result = await run_test_suite(feature)
    if not g3_result.passed:
        if retry_count >= MAX_RETRIES:
            return await escalate_to_human(feature, "G3", g3_result)
        return await retry_with_feedback(
            feature, coding_agent, g3_result, retry_count + 1
        )

    # G4: Human review (conditional)
    if await requires_human_review(feature):
        return FeatureResult(
            status="escalated",
            gate="G4",
            evidence=collect_evidence(g1_result, g2_result, g3_result),
            message="Feature requires human review (>500 LOC or security-sensitive)"
        )

    # All gates passed
    return FeatureResult(
        status="evidence_locked",
        evidence=collect_evidence(g1_result, g2_result, g3_result),
        retry_count=retry_count
    )
```

**Deterministic feedback**: When a gate fails, the retry prompt includes structured failure data (not just "try again"):

```json
{
  "gate": "G2",
  "gate_name": "SAST Scan",
  "failures": [
    {
      "rule": "python.django.security.injection.sql-injection",
      "severity": "critical",
      "file": "backend/app/services/user_service.py",
      "line": 42,
      "message": "User input concatenated into SQL query",
      "fix_hint": "Use parameterized query: db.execute(text(:param), {param: value})"
    }
  ],
  "retry_count": 1,
  "max_retries": 3,
  "instruction": "Fix the identified vulnerabilities. Do not introduce new files. Re-run tests after fix."
}
```

### 2.6 Prompt Caching for Cost Optimization

Leverage Anthropic's prompt caching (from ADR-054) to reduce per-feature codegen cost:

```python
# backend/app/services/context_cache_service.py

class AutonomousCodegenCache:
    """
    Cache layers for autonomous codegen sessions:

    L1 (Redis): Feature list, project config, recent gate results
    L2 (Anthropic Cache): SDLC Framework, ADRs, policy packs, templates

    Cost impact per feature:
    - Without caching: ~$0.012 (960KB context re-sent)
    - With caching: ~$0.0015 (cache hit on stable context)
    - Savings: 8x cost reduction
    - At 100 features/day: $36/day saved ($13,140/year)
    """

    STABLE_CONTEXT = [
        # Cached at L2 (Anthropic), refreshed every 24h
        "SDLC-Enterprise-Framework/02-Core-Methodology/",
        "SDLC-Enterprise-Framework/03-AI-GOVERNANCE/",
        "docs/02-design/01-ADRs/",
        "backend/policy-packs/rego/",
    ]

    SESSION_CONTEXT = [
        # Cached at L1 (Redis), refreshed per feature
        "feature_list.json",
        "evidence_manifest.json",
        ".sdlc-policy-context.json",
    ]
```

---

## 3. Framework Reference

This ADR implements the methodology defined in the SDLC Enterprise Framework:

| Framework Document | Path | Purpose |
|-------------------|------|---------|
| Autonomous Codegen Patterns | `SDLC-Enterprise-Framework/03-AI-GOVERNANCE/11-AUTONOMOUS-CODEGEN-PATTERNS.md` | Two-agent pattern with Quality Gates methodology |
| CLAUDE.md Standard | `SDLC-Enterprise-Framework/03-AI-GOVERNANCE/10-CLAUDE-MD-STANDARD.md` | 3-tier CLAUDE.md for agent context |
| MRP Template | `SDLC-Enterprise-Framework/02-Core-Methodology/SDLC-MRP-Template.md` | Merge-Readiness Package structure |

**Framework-First Compliance**: The methodology was defined in the Framework (Sprint 174 Days 1-3) before this Orchestrator ADR was authored (Sprint 174 Day 5+). See `SPRINT-174-FRAMEWORK-FIRST-ANALYSIS.md`.

---

## 4. Related ADRs

| ADR | Relationship | Description |
|-----|-------------|-------------|
| ADR-022 | Foundation | Multi-Provider Codegen Architecture -- defines the Ollama/Claude/DeepCode fallback chain used by the Coding Agent |
| ADR-053 | Integration | Governance Loop State Machine -- the 6-state gate lifecycle that this ADR extends to per-feature evidence tracking |
| ADR-054 | Parent | Anthropic Claude Code Best Practices -- the strategic integration ADR from which this specific pattern is extracted |

---

## 5. Consequences

### 5.1 Positive

- **Feature waste reduced from 60% to <30%**: Every autonomous feature passes 4 quality gates before merge, catching scope creep (G1), vulnerabilities (G2), regressions (G3), and architectural drift (G4)
- **Security vulnerability rate <2%**: Semgrep SAST + OPA AGPL containment on every feature eliminates the 3-5x vulnerability rate of ungoverned AI agents
- **Full audit trail**: Every feature has a complete evidence chain (spec review, SAST report, test results, human decision) stored in the Evidence Vault with SHA256 integrity
- **8x cost reduction**: Prompt caching reduces per-feature cost from $0.012 to $0.0015, saving approximately $13,140/year at projected usage
- **Deterministic retry feedback**: Failed features receive structured error data (not vague "try again"), improving fix success rate from approximately 40% to approximately 85% on first retry
- **Progressive trust**: Small features (<500 LOC) auto-approve through G1-G3; large or security-sensitive features require human review (G4)

### 5.2 Negative

- **Added latency per feature**: 4-gate validation adds 30-90 seconds per feature (G1: 10s, G2: 15s, G3: 60s). For a 100-feature project, this is approximately 1.5 additional hours
- **OPA infrastructure required**: Autonomous codegen requires a running OPA instance with the `autonomous-codegen` policy pack loaded. Teams without OPA cannot use this feature
- **Retry overhead**: Features that fail gates consume additional LLM tokens on retry. At max_retries=3, worst case is 4x the token cost of a single feature
- **Evidence storage growth**: Each feature generates 4-6 evidence artifacts (approximately 50KB each). A 200-feature project produces approximately 60MB of evidence data in MinIO

### 5.3 Neutral

- **Human review still required for >500 LOC changes**: G4 is explicitly human-in-the-loop for large features. This is by design (SDLC 6.0.5 AI Governance Principle: "Human accountability for architectural decisions"), not a limitation
- **Policy pack maintenance**: OPA policies for autonomous codegen require updates when new vulnerability patterns emerge or framework versions change. This follows the same maintenance cadence as existing policy packs
- **Git-based persistence unchanged**: We preserve Anthropic's git-based state persistence (feature_list.json committed to repo). This is a pragmatic decision -- git is universally available and provides built-in history

---

## 6. Alternatives Considered

### 6.1 No Governance (Anthropic Pattern As-Is)

**Rejected**: The bash allowlist approach in `claude-quickstarts/autonomous-coding` prevents destructive commands but does not validate code quality. A `rm -rf /` is blocked, but an SQL injection vulnerability passes silently. Our pilot with BFlow showed 60% feature waste with ungoverned agents.

### 6.2 Post-Hoc Validation Only

**Rejected**: Validating all features after the full batch completes (instead of per-feature) means rework cascades. If feature 15 introduces a breaking change, features 16-50 may all need regeneration. Per-feature gating catches issues early.

### 6.3 Single-Agent Pattern

**Rejected**: Combining initialization and coding into one agent creates context overflow for large projects (>50 features). Anthropic's two-agent split is correct -- the Initializer runs once with full project context, the Coding Agent operates with narrow per-feature context.

### 6.4 Custom State Machine (Not 8-State)

**Rejected**: Creating a separate state machine for autonomous codegen would fragment the governance model. Reusing the existing 8-state Evidence State Machine (ADR-053) provides consistency across manual and autonomous workflows.

---

## 7. Implementation Plan

### Sprint 175: Initializer Agent (March 3-14, 2026)

| Deliverable | Effort | Owner |
|-------------|--------|-------|
| `feature_list.json` schema with gate_status, evidence_ids, retry_count fields | 1 day | Backend |
| `evidence_manifest.json` schema and Evidence Vault integration | 1 day | Backend |
| `.sdlc-policy-context.json` generator (reads project tier, policy pack) | 0.5 day | Backend |
| Initializer Agent service (`autonomous_initializer_service.py`) | 2 days | Backend |
| OPA policy pack: `autonomous-codegen/feature_gate.rego` | 1 day | Backend |
| Unit tests (95%+ coverage) | 1.5 days | Backend |
| Integration test with Evidence Vault + OPA | 1 day | Backend |

**Sprint 175 Exit Criteria**: Initializer Agent generates valid `feature_list.json` + `evidence_manifest.json` from `app_spec.txt` input, with OPA policy context bound.

### Sprint 176: Coding Agent Loop (March 17-28, 2026)

| Deliverable | Effort | Owner |
|-------------|--------|-------|
| Coding Agent service (`autonomous_coding_service.py`) | 3 days | Backend |
| 4-Gate validation pipeline (G1-G4 sequential execution) | 2 days | Backend |
| Retry logic with deterministic feedback (max_retries=3) | 1 day | Backend |
| Escalation path (human notification via Web/CLI/Extension) | 1 day | Backend |
| Prompt caching integration (`context_cache_service.py`) | 1 day | Backend |
| Unit + integration tests (95%+ coverage) | 2 days | Backend |

**Sprint 176 Exit Criteria**: Coding Agent iterates through `feature_list.json`, implements features with 4-gate validation, retries on failure (max 3), escalates to human when exhausted. Evidence stored in Vault per feature.

### Sprint 177: E2E Pilot (March 31 - April 11, 2026)

| Deliverable | Effort | Owner |
|-------------|--------|-------|
| E2E test: Initializer + Coding Agent full cycle (10-feature project) | 2 days | QA |
| Performance benchmarking (latency per gate, total project time) | 1 day | Backend |
| Evidence audit trail verification (SHA256 integrity check) | 1 day | Backend |
| Dashboard integration (feature progress visualization) | 2 days | Frontend |
| CLI integration (`sdlcctl codegen autonomous --spec app_spec.txt`) | 1 day | Backend |
| Documentation: runbook, architecture diagram, API reference | 1 day | Docs |
| Internal pilot: SDLC Orchestrator self-dogfooding (20-feature test) | 2 days | Team |

**Sprint 177 Exit Criteria**: Full autonomous codegen cycle completed on a real project. Feature waste rate measured. Evidence trail verified. Dashboard shows feature-by-feature gate results.

---

## 8. Rollout Plan

| Phase | Target | Timeline | Success Criteria |
|-------|--------|----------|-----------------|
| **Internal Pilot** | SDLC Orchestrator (self-dogfooding) | Sprint 177 | Feature waste <30%, all evidence captured, zero P0 bugs |
| **BFlow Pilot** | BFlow Platform (200K users) | Sprint 178-179 | 5 features generated autonomously, CTO sign-off |
| **Vietnamese SME Pilot** | 5 founding customers | Sprint 180+ | Time-to-feature <1 hour (vs 1 day manual), customer satisfaction >4/5 |
| **GA Release** | All SDLC Orchestrator customers | Q3 2026 | Documentation complete, policy packs published, pricing finalized |

---

## 9. Success Metrics

| Metric | Before (Ungoverned) | Target (With 4-Gate) | Measurement |
|--------|---------------------|---------------------|-------------|
| Feature waste rate | 60-80% | <30% | Features rejected at G1-G4 / total features |
| Security vulnerability rate | 8-12% of features | <2% | G2 SAST findings per feature |
| Test regression rate | 15-20% | <5% | G3 regression count per feature |
| Cost per feature (LLM) | $0.012 | $0.0015 | Anthropic billing / features generated |
| Time per feature (autonomous) | 5-10 min | 6-12 min (with gates) | Wall clock from start to evidence_locked |
| Evidence completeness | 0% | 100% | Features with full evidence chain / total features |
| Human escalation rate | N/A | <15% | Features requiring G4 / total features |

---

## 10. Approval

- [ ] **CTO Review**: Pending (Sprint 174)
- [ ] **Enterprise Architect Review**: Pending
- [ ] **SDLC Expert Review**: Pending
- [ ] **Security Lead Review**: Pending (OPA policy pack validation)
- [ ] **CEO Budget Approval**: Pending (Sprint 175-177 resource allocation)

---

**References**:
- Anthropic: `anthropics/claude-quickstarts/autonomous-coding/` (two-agent pattern)
- Framework: `SDLC-Enterprise-Framework/03-AI-GOVERNANCE/11-AUTONOMOUS-CODEGEN-PATTERNS.md`
- ADR-022: Multi-Provider Codegen Architecture (EP-06 IR-based codegen)
- ADR-053: Governance Loop State Machine (6-state gate lifecycle)
- ADR-054: Anthropic Claude Code Best Practices (strategic integration)
- SDLC 6.0.5: 7-Pillar Architecture + Section 7 Quality Assurance System

---

*ADR-055 -- Autonomous Codegen with 4-Gate Validation. Enhances Anthropic's two-agent pattern with SDLC 6.0.5 governance: OPA policies, Evidence State Machine, deterministic retry feedback, and prompt caching. Feature waste 60% to 30%. Security vulnerability rate <2%. Full audit trail.*
