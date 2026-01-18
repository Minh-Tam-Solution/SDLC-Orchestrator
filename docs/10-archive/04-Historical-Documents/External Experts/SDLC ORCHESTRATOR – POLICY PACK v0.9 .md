# SDLC ORCHESTRATOR – POLICY PACK v0.9 & ARTEFACT TEMPLATES (4.9)

**Date:** 16/11/2025
**Scope:** YAML gate policies cho **Lite / Standard / Enterprise**, Evidence Schema, PR Checks contract, và bộ **templates** để team pilot ngay.

---

## 1) POLICY PACK v0.9 (TIERED COMPLIANCE)

> Dùng với **Gate Engine** (OPA/Conftest). YAML phía dưới là **abstraction** cho PM/QA, được biên dịch sang quy tắc chi tiết.

```yaml
# policy_pack.yaml — SDLC 5.1.3 (v0.9)
version: 0.9
schema: sdlc.gatepolicy/1

# ===== TIERS =====
Tiers:
  Lite:
    id: TIER_LITE
    waiver:
      allowed: true
      max_items: 2
      ttl_days: 21
    thresholds:
      coverage_min: 0.70
      tests_pass_critical: 0.90
      evidence_auto_min: 0.40
      security_profile: OWASP_BASELINE
      sast_required: false
      dast_required: false
      openapi_diff_required: false
  Standard:
    id: TIER_STD
    waiver:
      allowed: true
      max_items: 1
      ttl_days: 14
    thresholds:
      coverage_min: 0.80
      tests_pass_critical: 0.90
      evidence_auto_min: 0.60
      security_profile: OWASP_BASELINE
      sast_required: true
      dast_required: false
      openapi_diff_required: true
  Enterprise:
    id: TIER_ENT
    waiver:
      allowed: true
      max_items: 1
      ttl_days: 7
    thresholds:
      coverage_min: 0.85
      tests_pass_critical: 0.95
      evidence_auto_min: 0.70
      security_profile: OWASP_BASELINE
      sast_required: true
      dast_required: true
      openapi_diff_required: true

# ===== GATES =====
Gates:
  - id: G0_1_PROBLEM_DEFINED
    stage: WHY
    requires:
      problem_statement: present
      success_metrics: present
      interviews_count: ">=5"
      risk_list: present
    approvals: ["ProductLead"]

  - id: G0_2_SOLUTION_DIVERSITY
    stage: WHAT
    requires:
      solution_gallery: { ideas: ">=100", themes: ">=10" }
      concept_shortlist: ">=3"
      scorecards: present
    approvals: ["ProductLead", "CTO"]

  - id: G1_REQUIREMENTS_READY   # optional per product/tier
    stage: WHAT
    optional: true
    requires:
      requirements_doc: present   # MoSCoW/Job stories/AC
      success_metrics: present
      phase_plan: present
      sprint_plan: present
    approvals: ["PM_PO", "TechLead"]

  - id: G2_DESIGN_READY
    stage: HOW
    requires:
      adr_links: present
      openapi_lint: PASS
      db_erd_link: present
      tdd_diagram: present
      security_review: "OWASP_BASELINE"
      perf_budget: present
      operate_preview: present
    approvals: ["TechLead", "SecurityLead"]
    waiver_from_tier: true

  - id: G3_SHIP_READY
    stage: BUILD_TEST
    requires:
      tests_pass_critical: ">={tier.thresholds.tests_pass_critical}"
      coverage: ">={tier.thresholds.coverage_min}"
      perf_budget: PASS
      release_notes: present
      sast: "{ tier.thresholds.sast_required ? 'PASS' : 'N/A' }"
    approvals: ["QALead", "PM"]

  - id: G4_DEPLOY_READINESS
    stage: DEPLOY
    requires:
      openapi_diff: "{ tier.thresholds.openapi_diff_required ? 'NO_BREAKING' : 'N/A' }"
      sbom: present
      attestations: present
      rollback_plan: present
      feature_flags: present
      migration_plan: present
    approvals: ["ReleaseManager", "TechLead", "SecurityLead?opt"]

  - id: G5_OPERATE_READY
    stage: OPERATE
    requires:
      runbook: present
      oncall_configured: true
      alerts_critical_defined: true
      sla_declared: true
    approvals: ["SRE_Lead"]

# ===== PR CHECKS CONTRACT =====
PRChecks:
  enabled: true
  checks:
    - gate/G0.1
    - gate/G0.2
    - gate/G1   # if enabled for product
    - gate/G2
    - gate/G3
    - gate/G4
    - gate/G5
  message_template: "{gate_id}: {status} — see evidence: {evidence_link}"

# ===== RBAC/ANTI-SELF =====
RBAC:
  anti_self_testing: true
  rules:
    - id: R_SELF_APPROVE_BLOCK
      description: "Author of PR cannot approve their own QA/Release gates"
      applies_to: ["G3_SHIP_READY", "G4_DEPLOY_READINESS"]
      action: BLOCK
```

---

## 2) EVIDENCE SCHEMA v0.9 (VAULT)

```json
{
  "stage": "WHY|WHAT|HOW|BUILD_TEST|DEPLOY|OPERATE",
  "gate": "G0.1|G0.2|G1|G2|G3|G4|G5",
  "evidence_type": "doc|report|artifact|attestation|sbom|runbook",
  "file_hash": "sha256:...",
  "owner": "user@company",
  "pr_id": "org/repo#123",
  "run_id": "gh-actions-2025-11-16T08:00:00Z",
  "timestamp": "2025-11-16T08:00:00+07:00",
  "link": "https://.../evidence/..."
}
```

**Nơi lưu:**

* **Orchdocs Git**: BRD/ADR/Runbook/RCA/Plans…
* **Artifacts/S3 (MinIO)**: Allure reports, coverage, SBOM, attestations, perf logs.
* **Bất biến:** hash + timestamp; audit log append-only.

---

## 3) PR CHECKS – CONTRACT (ÁP DỤNG CHUNG)

```
Checks: gate/G0.1, gate/G0.2, gate/G1 (optional), gate/G2, gate/G3, gate/G4, gate/G5
Payload: { gate_id, status, evidence_link, message, updated_at }
Rule: Fail nếu thiếu evidence/approval hoặc vi phạm RBAC/anti-self-testing
```

---

## 4) ARTEFACT TEMPLATES (SẴN DÙNG)

### 4.1 RELEASE_NOTES.md (DEPLOY – G4)

```markdown
# Release Notes — <product> v<version>
Date: <YYYY-MM-DD>
Release Manager: <name>

## 1. Summary
- Key changes:
- User impact:

## 2. Technical Notes
- Migrations:
- Feature flags:
- Backward compatibility:

## 3. Risk & Rollback
- Known risks:
- Rollback plan:

## 4. Validation
- Test coverage: <percent>
- Perf budget: PASS/FAIL (notes)
- OpenAPI-Diff: NO_BREAKING / WAIVER(<id>)

## 5. Links
- PRs: ...
- Evidence Vault: ...
```

### 4.2 RUNBOOK.md (OPERATE – G5)

```markdown
# Runbook — <service>
Owner: <team>
On-call rota: <link>

## 1. Overview
Purpose, SLO, dependencies

## 2. Operational Procedures
- Start/Stop/Deploy
- Backup/Restore
- Config/Secrets

## 3. Monitoring & Alerts
- Dashboards (Grafana): <links>
- Alerts (critical/warning): <rules>

## 4. Incident Handling
- Triage steps
- Escalation path
- Communication template

## 5. Recovery & Verification
- Rollback recipe
- Post-recovery checks
```

### 4.3 RCA_TEMPLATE.md (OPERATE)

```markdown
# RCA — Incident <id>
Date/Time:
Severity:

## 1. Timeline
- t0: detection
- t1: containment
- t2: resolution

## 2. Impact
Users/transactions affected, duration, revenue risk

## 3. Root Cause (5 Whys)
Why1 → Why2 → Why3 → Why4 → Why5

## 4. Contributing Factors
- ...

## 5. Corrective & Preventive Actions (CAPA)
- Immediate fixes
- Long-term prevention (policy/gate/update)

## 6. Evidence Links
- Logs/dashboards/PRs
```

### 4.4 CONCEPT_SCORECARDS.md (WHAT)

```markdown
# Concept Scorecards
Criteria: Feasibility, Impact, Risk, Cost (1–5)

| Concept | Feasibility | Impact | Risk | Cost | Notes |
|---|---|---|---|---|---|
| A | 4 | 5 | 2 | 3 | ... |
| B | 3 | 4 | 3 | 2 | ... |

Shortlist: [A, B, C]
```

### 4.5 PHASE_PLAN.md (WHAT)

```markdown
# Phase Plan — <product>
Duration: 4–12 weeks
Goals & KPI:

| Week | Goals | Gates | KPI |
|---|---|---|---|
| 1 | ... | G0.2 | ... |
| 2 | ... | G1 | ... |
```

### 4.6 SPRINT_PLAN.md (WHAT)

```markdown
# Sprint Plan — Sprint <n>
Length: 2 weeks
Outcome/KPI:

| Story | Acceptance Criteria | Estimate | Owner |
|---|---|---|---|
| ... | ... | ... | ... |
```

### 4.7 SOLUTION_GALLERY.csv (WHAT)

```csv
idea,theme,concept_candidate,notes
"<idea 1>","<theme>","<A/B/C>","..."
"<idea 2>","<theme>","<A/B/C>","..."
```

### 4.8 SECURITY_BASELINE.md (HOW)

```markdown
# Security Baseline — <service>
OWASP ASVS level: BASELINE
Authn/Authz model:
Secrets policy:
Dependency policy (SBOM, updates):
Data classification (PII/PHI/PCI):
Egress control & masking for AI:
```

### 4.9 PERF_BUDGET.md (HOW)

```markdown
# Performance Budget — <service>
Latency p95/p99:
Throughput target:
CPU/RAM/IO caps:
DB size/IO pattern:
Perf test plan (baseline/stress):
```

---

## 5) CI/CD HOOKS (SNIPPETS THAM KHẢO)

### 5.1 OpenAPI-Diff (trước G4)

```bash
oapi-diff old.yml new.yml --fail-on-breaking
```

### 5.2 SBOM & Cosign (G4)

```bash
syft packages:oci://registry/app:RC-123 -o cyclonedx-json > sbom.json
cosign attest --predicate sbom.json --type cyclonedx oci://registry/app:RC-123
```

### 5.3 Allure + Coverage (G3)

```bash
pytest --alluredir=allure-results
coverage xml -o coverage.xml
# upload artifacts to S3/MinIO and register to Evidence Vault
```

---

## 6) VS CODE / CLI USAGE (DEVELOPER-FIRST)

```
VS Code Palette:
- SDLC: Generate BRD / Scorecards / Phase Plan / Sprint Plan / ADR / OpenAPI / ERD / TDD / Security Baseline / Release Notes / Runbook / RCA

CLI (sdlcctl):
- validate-gate --stage WHAT|HOW|BUILD_TEST|DEPLOY|OPERATE
- attach-evidence --doc <file>
- publish-release-notes --from CHANGELOG.md
- deploy-readiness --rc-tag RC-123
```

---

**Ready for Pilot:** Dùng file **policy_pack.yaml**, **evidence schema**, và **templates** trên để bật 2 đội thử nghiệm (1 **Lite**, 1 **Standard**) theo lộ trình 90 ngày đã thống nhất.
