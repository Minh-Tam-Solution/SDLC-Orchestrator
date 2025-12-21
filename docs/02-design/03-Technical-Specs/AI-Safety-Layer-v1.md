# AI Safety Layer v1 – Specification

**Version**: 0.1.0 (Draft)  
**Date**: December 5, 2025  
**Authors**: AI Governance Squad (CTO Program)  
**Status**: In Review – Align with EP-02 roadmap deliverables  
**Related Docs**: Product-Roadmap-2026-Software3.0.md, AI Council Service (Sprint 26), Policy Pack Library

---

## 1. Purpose & Scope
- **Purpose**: Protect codebases from uncontrolled AI-generated changes by enforcing architecture, security, and compliance policies before merge.
- **Scope v1**:
  - Git-based workflows (GitHub primary, GitLab alpha).  
  - Pull requests / merge requests labelled as AI-generated (auto or manual).  
  - Back-end services and core libraries (frontend optional, telemetry only).  
  - Integration with SDLC Orchestrator policy packs and Evidence Vault.
- **Out of Scope v1**:
  - Real-time IDE blocking (cursor agent hooks).  
  - Full-stack dependency scanning (deferred to v2).  
  - Automated remediation suggestions (AI Council advisory only).

Success criteria align with EP-02: 100% AI PR coverage, zero untracked overrides, mean time-to-feedback <8 minutes.

---

## 2. Architecture Overview
**Primary Components**
- **Safety Gateway** (new service/module): Receives AI PR events, orchestrates validators, aggregates results.
- **Policy Engine** (OPA-driven): Evaluates policy packs against validator outputs and metadata.
- **Validator Workers**: Execute linting, tests, SAST, architecture checks (containerised tasks triggered by Gateway).
- **Evidence Logger**: Persists structured evidence into Evidence Vault (`ai_code_events`) and audit trail tables.
- **Developer Feedback Integrations**: Git status checks, PR comments, Orchestrator UI timeline views.

**Data Flow**
1. PR labelled as AI-generated (metadata from tools or manual).  
2. CI/CD triggers Safety Gateway via webhook/CLI.  
3. Gateway loads applicable policy packs for repository/project context.  
4. Validators execute in parallel pools; results streamed back to Gateway.  
5. Policy engine evaluates pass/fail, determines required overrides.  
6. Gateway updates PR status (GitHub Checks API) and stores evidence logs.  
7. Orchestrator UI surfaces consolidated timeline and governance decisions.

**System Boundaries**
- Runs within existing CI infrastructure (GitHub Actions runner baseline).  
- Requires secure communication with Orchestrator API for policy and evidence operations.  
- Validator execution isolated in container sandbox; secrets managed via CI secrets store.

---

## 3. Input Side – Prompt Guardrails
Goals: Prevent sensitive data leakage and ensure consistent prompt metadata for downstream auditing.

**Capabilities**
- Secret detection/redaction for prompts sent to external LLMs (pattern-based + allowlist).  
- Prompt size enforcement (token limit) to avoid context overexposure.  
- Metadata capture (ai_tool, ai_model, mode, workspace path) when available.

```yaml
safety:
  prompts:
    redact_secrets: true
    secret_patterns:
      - '(?i)api[_-]?key'
      - '-----BEGIN.*PRIVATE KEY-----'
      - 'AKIA[0-9A-Z]{16}'
    max_context_tokens: 8000
    metadata_required: [ai_tool, ai_mode]
    drop_on_violation: true    # block prompt if secrets detected
```

Prompt guardrails integrate with IDE plugins (future) and PR metadata ingestion (v1 ensures storage for audit even if guardrails executed elsewhere).

---

## 4. Change Detection & Metadata Capture
- **Auto-tag sources**:  
  - Git commit trailers (`Co-authored-by: cursor-ai`), tool-specific commit metadata, custom headers from Cursor/Copilot/Claude integrations.  
  - Diff heuristics (high token count with low comment density) flagged for manual review.
- **Manual override**: Maintainers can apply `ai-generated` label; Orchestrator prompts for rationale if removed.
- **Metadata schema**:

```json
{
  "pr_id": "uuid",
  "repo": "org/service",
  "ai_tool": "cursor",
  "ai_model": "gpt-4.1",
  "prompt_hash": "sha256",
  "generated_at": "2025-12-05T10:42:00Z",
  "initiator": "dev@example.com",
  "lines_added": 324,
  "files_touched": 12,
  "labels": ["ai-generated", "backend-critical"]
}
```

Metadata stored prior to validation to ensure audit trail even if validators fail or are aborted.

---

## 5. Validator Catalogue
| Category | Validator | Description | Target | Tooling / Implementation |
|----------|-----------|-------------|--------|---------------------------|
| Formatting | `lint_check` | Run standard lint/format (e.g., Ruff, Black, ESLint) | All python/node repos | Existing lint scripts wrapped by Gateway |
| Testing | `unit_subset` | Targeted unit tests for impacted modules | Backend critical packs | pytest with test selection via `pytest-testmon` |
| Security | `sast_basic` | Static analysis for top CWEs | Backend + infra repos | Bandit (Python), Semgrep ruleset (critical subset) |
| Architecture | `layer_guard` | Forbid disallowed imports/cross-layer dependencies | Services with layered architecture | Custom AST scanner referencing architecture manifest |
| Coverage | `coverage_gate` | Ensure coverage ≥ threshold defined in policy pack | Critical repos | `coverage.py` diff mode |
| Dependency | `license_scan_light` | Identify forbidden licenses in new dependencies | All repos | `pip-licenses` / `license-checker` |
| Custom | `policy_script` | Hooks for repo-specific scripts (e.g., SQL lint) | Optional | Executed via repository script path |

**Execution Model**
- Validators run inside Docker-in-Docker container with resource limits (CPU 2 cores, memory 4GB).  
- Parallelism: up to 4 validators concurrently per PR to keep end-to-end within 8 minutes p95.  
- Retries: single automatic retry for transient failures; persistent failures reported as `validator_error`.

---

## 6. Policy Engine & Enforcement
- Policies defined in Orchestrator policy packs (OPA/Rego + YAML metadata).
- Gateway requests policy set applying to repository context (team, risk tier, environment).
- Sample policy schema:

```yaml
name: backend-critical
severity: critical
validators:
  lint_check: required
  unit_subset:
    required: true
    rerun_on_override: true
  sast_basic:
    required: true
    min_severity: medium
  coverage_gate:
    required: true
    threshold: 0.80
enforcement:
  block_merge: true
  allow_vcr_override: true
override:
  approvers: ["security-lead", "cto"]
  audit_reason_required: true
```

- **Decision Outcomes**:
  - `pass`: all required validators succeed.  
  - `fail`: at least one required validator fails.  
  - `pending`: validators still running or manual approval required.
- **Override Workflow**:
  - Maintainer initiates VCR (Version-Controlled Resolution) in Orchestrator UI.  
  - Provide rationale + evidence; requires policy-defined approvers.  
  - All overrides logged with diff of failed checks and justification.

---

## 7. Evidence & Audit Logging
- Evidence stored in Evidence Vault with tight coupling to PR and policy context.
- **Collections**:
  - `ai_code_events`: metadata about AI involvement and validator outcomes.  
  - `ai_prompt_records`: hashed prompts with secret redaction status and storage pointer (for on-prem secure vault).  
  - `ai_override_decisions`: VCR records with approver chain.
- **Log Fields**:
  - Policy evaluation summary, timestamps, validator execution metrics.  
  - Links to artifacts (test reports, coverage HTML) stored in MinIO bucket.  
- **Access Controls**:
  - RBAC ensures only compliance/security roles can view prompt details.  
  - S3 bucket encryption + retention policy (default 18 months, configurable).

---

## 8. Integrations & Interfaces
- **GitHub**: Checks API for status updates, PR comment for failure summary, label management automation.
- **GitLab (Alpha)**: Pipeline job template invoking Safety Gateway CLI, uses Merge Request discussions for feedback.
- **CLI**: `sdlcctl safety run --pr <id>` for local dry-run (developer self-service, advisory mode).  
- **Orchestrator UI**: New “AI Safety” tab per PR or gate showing validator timeline, overrides, and evidence.
- **Notifications**: Optional Slack/Teams integration for failed AI checks routed to owning team channel.

---

## 9. Observability & SLOs
- **Metrics**:
  - `safety.validation.duration_ms` (per validator and aggregate).  
  - `safety.validation.status` (pass/fail/error).  
  - `safety.override.count` (per policy pack).  
  - `safety.prompt.redaction_events`.
- **Logs**:
  - Structured JSON logs for validator start/stop, failures, retries.  
  - Prompt redaction alarms when secrets detected.
- **Dashboards** (Grafana/Looker):
  - Validation latency percentiles.  
  - Top failing validators by repo/team.  
  - Override trends (identify policy tuning needs).
- **SLO Targets v1**:
  - p95 validation <8 minutes.  
  - Error rate (<500 responses) <1%.  
  - Override approval latency <24 hours.

Alerts integrate with on-call rotations (PagerDuty) for sustained failures or latency breaches.

---

## 10. Rollout Plan
1. **Week 1-2**: Internal sandbox (two backend services) in monitor-only mode; collect baseline metrics.  
2. **Week 3-4**: Enable blocking mode for internal pilot teams with support playbook.  
3. **Week 5-6**: Expand to all internal AI-labelled PRs; run education sessions (docs, office hours).  
4. **Week 7+**: Rollout to design partners (EP-03) with shared telemetry dashboards and feedback loop.

**Enablement Assets**
- Developer quickstart guide.  
- Policy authoring tutorial (for custom packs).  
- Troubleshooting runbook (validator timeouts, false positives).

---

## 11. Security & Compliance Considerations
- Adhere to secret-handling policies (no prompts stored with raw secrets; hashed references only).  
- Ensure audit logs satisfy SOC2/ISO evidence requirements (immutable storage, timestamping, signature).  
- Support data residency (configurable storage buckets per tenant for future enterprise deployments).  
- Conduct threat modeling session before GA (focus on PR spoofing, validator tampering).  
- Pen-test required before external rollout; coordinate with Security team.

---

## 12. Open Questions & Risks
| Topic | Status | Owner | Notes |
|-------|--------|-------|-------|
| Secret detection coverage | Pending validation | Security | Need benchmark against production repo history |
| GitLab metadata parity | In discovery | Platform | Lack of native AI labels; may require custom hooks |
| Validator resource limits | Pending perf tests | DevInfra | Ensure CI runners can handle increased load |
| Override governance | Requires policy | Compliance | Define escalation for repeat manual overrides |
| Developer UX fatigue | Monitor | DX Guild | Provide simulation mode and targeted messaging |

---

## 13. Change Management
- Updates to specification reviewed weekly during AI Governance sync (CTO/CPO reps present).  
- Major changes (new validator category, enforcement behaviour) require ADR and communication plan.  
- Versioning: tag releases (`v1.0 GA`) when feature gates enabled for all design partners.

---

*End of document.*
