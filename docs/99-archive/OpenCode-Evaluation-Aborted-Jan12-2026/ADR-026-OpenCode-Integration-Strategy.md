# ADR-026: OpenCode Integration Strategy

- Status: Approved for Level 0 Observation (Jan 12, 2026)
- Owners: CTO (sponsor), Architect (design), Backend Lead (implementation), PM/PO (governance)
- Related: ADR-022 Multi-Provider Codegen, ADR-023 Vibecode CLI, ADR-020 4-Gate Quality Pipeline

## Context

OpenCode (https://github.com/anomalyco/opencode) is an emerging multi-agent code generation system. We will evaluate it as a Layer 5 AI Coder while preserving SDLC Orchestrator's provider-agnostic posture and keeping Vibecode CLI as the deterministic Layer 4 codegen path. OpenCode remains an external executor with a strict safety envelope and an immediate fallback path.

## Decision

Adopt a staged integration plan with explicit budget, timeline, and exit gates. Commit now only to Level 0 Observation in Q1 2026. Advance to later levels only if the prior gate is passed.

## Plan by Level

| Level | Window | Budget | Scope | Exit / Success Criteria |
|-------|--------|--------|-------|-------------------------|
| 0: Observation | Jan 12 - Mar 28, 2026 (12 weeks) | $0 | Repo monitoring, local server-mode runs, 5-task benchmark, latency/correctness sampling | >100 stars; >=2 commits/week; <10 critical issues; 5-task quality >=80% 4-Gate pass; P95 latency <30s |
| 1: Pilot (conditional) | Q2 2026, 2 sprints | $30K | OpenCode Server Mode Adapter; 4-Gate pipeline integration; retry loop (max 3) with feedback; opt-in provider flag | >=80% 4-Gate pass; cost < $20/feature; stable API for 8 weeks |
| 2: Production (conditional) | Q3 2026, 1 sprint | $20K | Multi-tenant routing, rate limiting, monitoring/alerting, runbook + kill-switch | Cost < $50/month; >=80% success rate; zero P0s for 30 days |
| 3: Optimization (optional) | H2 2026 | $40K | Fine-tuning, N-Version Programming, cache/memory tuning | ROI >30% quality uplift vs Claude; latency P95 <25s |

## Level 0: Activities (Committed)

- GitHub monitoring: stars, commit velocity, critical issues, release cadence.
- Local evaluation (no production traffic): 5-sample benchmark
  - Task 1: Simple CRUD API endpoint (FastAPI)
  - Task 2: React component with state
  - Task 3: Multi-file auth flow
  - Task 4: Bug fix with tests
  - Task 5: Performance optimization
- Quality measurement via 4-Gate proxy: Plan, Test, Lint, Security; accept if pass rate >=80%.
- Latency target: P95 <30s per feature; cost tracked as $0 (local runs).

### Level 0 Exit to Proceed

- Stability: >100 stars; >=2 commits/week; <10 critical issues; API unchanged for 3 months.
- Quality: >=80% 4-Gate pass across 5 tasks; correctness >=80% by reviewer spot-check; generated tests run clean.
- Latency: P95 <30s end-to-end for sample tasks on local server mode.
- Strategic: Fits ADR-022 provider-agnostic path; no hard dependency; graceful fallback to Claude/Ollama.

## Level 1: Pilot (Conditional)

- Build OpenCode Server Mode Adapter behind a feature flag; keep Claude/Ollama defaults.
- Integrate 4-Gate Quality Pipeline; enforce retry loop with feedback (max 3 attempts) then fallback.
- Limit to non-critical feature branches; no direct production writes.
- Success: >=80% 4-Gate pass; cost < $20/feature; zero P0 incidents during the pilot window.

## Level 2: Production (Conditional)

- Add multi-tenant support, rate limiting, monitoring dashboards, alerts, and an operator runbook with kill-switch.
- Success: cost < $50/month; >=80% success; zero P0s for 30 days.

## Level 3: Optimization (Optional)

- Fine-tune or add N-Version Programming for critical paths if ROI >30% quality uplift vs Claude.
- Tighten latency (P95 <25s) and reduce retries via cached plans/memory.

## Positioning & Roles

- OpenCode: Layer 5 AI Coder (exploratory, multi-agent). Use for complex or ambiguous features.
- Vibecode CLI (ADR-023): Layer 4 deterministic codegen (IR-based), primary for Vietnamese SME workloads.
- Hybrid Strategy: Keep both. Use OpenCode for exploration; use Vibecode for governed generation. Maintain provider-agnostic orchestration (ADR-022).

## Guardrails

- Pre-integration checklist: stability (stars/velocity/issues), API maturity, licensing, security scan, roadmap fit.
- Kill-switch triggers: quality <60% 4-Gate pass, cost >$30/feature, any P0 incident, or API breaking change.
- Monthly checkpoints: CTO review of metrics (quality, latency, cost, incidents) with stay/go decision.
- Data handling: no production secrets; redact sensitive inputs; store logs in existing observability stack with 30-day retention.
- Access: feature-flagged; limited to pilot namespaces and non-critical branches.

## Risks & Mitigations

- API churn -> Mitigate with adapter isolation and schema version pinning.
- Quality regression -> Enforce 4-Gate + retry/fallback; block merge on failures.
- Cost overrun -> Track cost/feature; kill-switch at $30/feature; prefer local/server mode for pilots.
- Vendor lock-in -> Maintain Claude/Ollama paths; avoid proprietary extensions.

## Timeline Snapshot

- Q1 2026: Level 0 Observation (committed) with April 2026 decision.
- Q2 2026: Level 1 Pilot (conditional on Level 0 success).
- Q3 2026: Level 2 Production hardening (conditional on pilot success).
- H2 2026: Level 3 Optimization (only if ROI threshold met).
