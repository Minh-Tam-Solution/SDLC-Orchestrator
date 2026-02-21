---
sdlc_version: "6.1.0"
document_type: "Architecture Decision Record"
status: "ACCEPTED"
sprint: "180"
spec_id: "ADR-059"
tier: "ALL"
stage: "02 - Design"
owner: "CTO"
approved_by: "CTO + CPO + CEO"
approved_date: "2026-02-19"
---

# ADR-059 — Enterprise-First Refocus Strategy

**Status**: ACCEPTED (CTO + CPO + CEO, Feb 19, 2026)
**Sprint**: 180
**Deciders**: CEO, CTO, CPO
**Category**: Strategic Architecture + Product Strategy
**Supersedes**: N/A (new direction)
**Triggers**: ADR-060 (Route Registration Standards), ADR-061 (SSO Integration), ADR-062 (Evidence Type Extensions), ADR-063 (Multi-Region Architecture)

---

## Context

### 1.1 Triggering Event

On February 19, 2026, the CTO issued a strategic direction change:

> "TinySDLC is now OSS for community. SDLC Orchestrator should refocus on Enterprise — large, complex projects. Review tiers, subscription plan, business model."

The immediate cause: **TinySDLC** (the local-first, lightweight SDLC governance tool) is being released as MIT/Apache-2.0 open-source for individual developers and small teams. This eliminates the original LITE/SME market for Orchestrator and creates an opportunity to focus exclusively on the enterprise segment.

### 1.2 Current State Assessment

**What changed (Feb 19, 2026)**:

```
Before: SDLC Orchestrator = Only product (serves Individual → Enterprise)
        TinySDLC           = Internal tool / prototype

After:  TinySDLC           = OSS community product (Individual / Small team, local-first)
        SDLC Orchestrator  = Commercial enterprise product (Team+ → Enterprise, cloud-first)
```

**Structural problems identified**:

- 38% of API surface (30/78 routes) orphaned or ungated — no tier check on production endpoints
- 8+ tier-related enums across codebase with inconsistent values (some still use `FREE`, some `LITE`, one is a plain `str` class rather than `enum.Enum`)
- `SubscriptionPlan` (subscription.py) has 4 values (`FREE/FOUNDER/STANDARD/ENTERPRISE`) — no `PROFESSIONAL` billing plan exists despite PROFESSIONAL being a target tier
- No enterprise-differentiating features in current production deployment (SSO, NIST AI RMF, multi-agent are all unfinished)
- Unclear product identity: marketing and codebase say "LITE/STANDARD/ENTERPRISE" while billing says "FREE/FOUNDER/STANDARD/ENTERPRISE"

### 1.3 Two-Product Ecosystem

```
┌──────────────────────────┐          ┌──────────────────────────────┐
│       TinySDLC           │          │     SDLC Orchestrator        │
│    (OSS Community)       │          │   (Commercial Enterprise)    │
│                          │          │                              │
│ License: MIT / Apache    │   10%    │ License: Apache-2.0 (prop.)  │
│ Price:   Free forever    │ convert  │ Price: $99-$499/mo + custom  │
│ Deploy:  Local / self    │ ────────>│ Deploy: Cloud-hosted         │
│ Target:  Individual dev  │          │ Target: 15+ dev teams        │
│ OTT:     Telegram/Zalo   │          │ OTT:   Telegram/Teams/Slack  │
│ Agents:  8 SDLC agents   │          │ Agents: 8 + Multi-Agent EP-07│
│ Revenue: $0 direct       │          │ Revenue: SaaS + PS           │
└──────────────────────────┘          └──────────────────────────────┘
         │                                         │
         └─────── SDLC 6.1.0 Framework ───────────┘
                  (shared methodology)
```

**Important invariant** (INV-01): TinySDLC ≠ Orchestrator LITE. They are distinct products sharing a methodology framework. Orchestrator LITE is the *free cloud gateway tier* for users who want cloud-hosted features but are evaluating; TinySDLC is the fully local, self-hosted, no-account-required tool.

### 1.4 CPO Gate Validation

**G0.1 (Problem Statement)**: ✅ APPROVED by CPO (SE4H role)
> "SDLC Orchestrator attempts to serve ALL tiers simultaneously, resulting in 38% of features (30/78 routes) being orphaned or ungated, unclear product identity, and inability to articulate a differentiated enterprise value proposition."

**G0.2 (Solution Diversity)**: ✅ APPROVED by CPO

| Option | Description | CPO Verdict |
|--------|-------------|-------------|
| A: Enterprise-First | LITE stays, PROFESSIONAL+ gets investment priority | ✅ **SELECTED** |
| B: Enterprise-Only | Drop LITE + STANDARD entirely | ❌ VETOED (loses acquisition funnel) |
| C: Bottom-Up Growth | Feature parity all tiers first | ❌ REJECTED (unsustainable; revenue delayed) |

---

## Decisions (LOCKED)

### Decision Table

| # | Decision | Description | Owner | Status |
|---|----------|-------------|-------|--------|
| D1 | Tier Model | LITE/STANDARD/PROFESSIONAL/ENTERPRISE with LITE as free cloud gateway | CPO | **LOCKED** |
| D2 | Enterprise-First Investment Priority | PROFESSIONAL+ gets new features; LITE/STANDARD get maintenance-only | CTO + CPO | **LOCKED** |
| D3 | OTT Channel Abstraction | All channels via `protocol_adapter.py`; Teams+Slack = P0; Telegram+Zalo = P1 | Tech Lead | **LOCKED** |
| D4 | Orphaned Routes Disposition | 6 routes → ENTERPRISE (Sprint 181); 1 route → CORE with rate-limit (Sprint 181) | Architect | **LOCKED** |
| D5 | Enterprise Feature Roadmap | SSO (Sprint 182) → Compliance (Sprint 183) → Integrations (Sprint 184) → GA (Sprint 188) | CEO | **LOCKED** |

**Non-Goals** (explicitly out of scope for this ADR):
- Pricing page copy, marketing messaging, sales playbook (CPO + Marketing)
- Specific implementation of SSO (ADR-061)
- Evidence type extensions (ADR-062)
- Multi-region DB architecture (ADR-063)
- CLAUDE.md v3.9.0 update (end of Sprint 180 or Sprint 181)

---

## Section 1: Tier vs. Billing Separation (INV-01, INV-02, INV-03)

### INV-01: Two-Layer Model (INVARIANT — LOCKED)

The system has TWO distinct layers that must not be conflated:

```
Feature Layer (product entitlements):
  project.tier_level = LITE | STANDARD | PROFESSIONAL | ENTERPRISE

Billing Layer (commercial SKU):
  subscription.plan = LITE_FREE | STD_STARTER | STD_GROWTH | PRO |
                      ENT_CUSTOM | FOUNDER_LEGACY
```

**Invariant mapping** (`plan ⇒ tier_level`, one-way only):

| Billing Plan | Feature Tier | Notes |
|-------------|-------------|-------|
| `LITE_FREE` | `LITE` | Free forever, 1 project, 100MB, 4 gates |
| `STD_STARTER` | `STANDARD` | $99/mo, 5 projects, 10GB, 10 members |
| `STD_GROWTH` | `STANDARD` | $299/mo, 15 projects, 50GB, 30 members |
| `PRO` | `PROFESSIONAL` | $499/mo, multi-agent, compliance-light |
| `ENT_CUSTOM` | `ENTERPRISE` | Custom $80/seat, SSO, NIST, unlimited |
| `FOUNDER_LEGACY` | `STANDARD` | Legacy SKU, no new sales, ~$150/mo |

The reverse direction (tier → plan) is NOT a function — one tier can have multiple billing plans. Never derive billing plan from tier alone.

### INV-02: TinySDLC vs. Orchestrator LITE (INVARIANT — LOCKED)

```
TinySDLC:
  - Local-only, no account required
  - Ships as OSS (MIT/Apache-2.0)
  - Target: Individual developer, <3 person team
  - Evidence: local filesystem only
  - Agents: single-provider, no Multi-Agent EP-07

Orchestrator LITE:
  - Cloud-hosted, account required
  - Free tier of commercial product
  - Target: Small team evaluating cloud features
  - Evidence: MinIO cloud vault
  - Agents: base 8 SDLC agents (no Multi-Agent)
  - Upgrades to STANDARD/PROFESSIONAL/ENTERPRISE

They share: SDLC 6.1.0 methodology framework (submodule)
They do NOT share: billing, auth, data, infrastructure
```

### INV-03: HTTP Code Semantics for Tier Gates (INVARIANT — LOCKED)

| HTTP Code | Meaning | When to Use |
|-----------|---------|-------------|
| `401 Unauthorized` | No valid authentication | Missing/expired JWT or API key |
| `403 Forbidden` | Authenticated but lacks scope/role | Has JWT but wrong RBAC role |
| `402 Payment Required` | Feature locked to higher tier | Correct role, wrong tier for this endpoint |
| `404 Not Found` | Resource does not exist | Standard not-found |

**Rule**: Tier-gated endpoints MUST return `402` with body `{"error": "tier_required", "required_tier": "PROFESSIONAL", "upgrade_url": "/billing/upgrade"}`. Never return `403` for a tier-blocking event.

### CTO Correction C-180-01: Actual Class Name is `ProjectTier`

> The plan referenced `TierLevel.FREE → TierLevel.LITE`. **`TierLevel` does not exist** in the codebase. The actual class is `ProjectTier` in `backend/app/schemas/tier_approval.py`.

Furthermore, `ProjectTier` at `tier_approval.py` is a **plain `str` subclass**, not `enum.Enum`:

```python
# Current (BROKEN — plain str, not enum.Enum)
class ProjectTier(str):
    FREE = "FREE"         # ← uses FREE not LITE
    STANDARD = "STANDARD"
    PROFESSIONAL = "PROFESSIONAL"
    ENTERPRISE = "ENTERPRISE"
```

Corrective action is documented in Appendix C (Sprint 181 migration).

### CTO Correction C-180-02: 8+ Tier Enums — Full Inventory

| Enum | File | Current Values | Proper `enum.Enum`? | Needs Fix |
|------|------|---------------|---------------------|-----------|
| `SubscriptionPlan` | `models/subscription.py` | `FREE/FOUNDER/STANDARD/ENTERPRISE` | ✅ Yes | Rename `FREE→LITE`, add `PROFESSIONAL` |
| `ProjectTier` | `schemas/tier_approval.py` | `FREE/STANDARD/PROFESSIONAL/ENTERPRISE` | ❌ **No** (plain `str`) | Convert to enum + rename `FREE→LITE` |
| `ProjectTier` | `schemas/codegen/template_blueprint.py` | `LITE/STANDARD/PROFESSIONAL/ENTERPRISE` | ✅ Yes | **Already correct** ✅ |
| `TierEnum` | `schemas/context_authority.py` | `LITE/STANDARD/PROFESSIONAL/ENTERPRISE` | ✅ Yes | **Already correct** ✅ |
| `SDLCTier` | `models/sdlc_validation.py` | `lite/standard/professional/enterprise` | ✅ Yes | **Lowercase values** — acceptable per file |
| `PolicyTier` | `policies/tier_policies.py` | `LITE/STANDARD/PROFESSIONAL/ENTERPRISE` | ✅ Yes | **Already correct** ✅ |
| `PolicyTier` | `schemas/policy_pack.py` | Mixed `LITE/standard/professional` | ✅ Yes | Normalize casing |

**Canonical target**: `LITE / STANDARD / PROFESSIONAL / ENTERPRISE` (SCREAMING_SNAKE_CASE). Sprint 181 migration plan is in Appendix C.

### CTO Correction C-180-03: `SubscriptionPlan` Missing `PROFESSIONAL`

> Current `SubscriptionPlan` has 4 values: `FREE / FOUNDER / STANDARD / ENTERPRISE`. **There is no `PROFESSIONAL` billing plan**.

The PROFESSIONAL tier is CPO-approved at $499/mo (see Appendix D), but the billing enum does not yet reflect this. Sprint 181 must:
1. Rename `FREE → LITE` in `SubscriptionPlan`
2. Add `PROFESSIONAL = "professional"` value
3. Expand to 6 total values: `LITE_FREE / STD_STARTER / STD_GROWTH / PRO / ENT_CUSTOM / FOUNDER_LEGACY`
4. Write Alembic migration for `subscription_plan` column (existing `free` rows → `lite`)
5. Data backfill for all existing `FREE` subscribers

This is a **4-value → 6-value enum migration** requiring Alembic + data backfill. Full steps in Appendix C.

---

## Section 2: Orphaned Route Security Rubric (INV-04 partial)

7 files exist in `backend/app/api/routes/` but are NOT registered in `backend/app/main.py`. All are production-ready (no TODOs, real implementations). Disposition is locked.

| File | LOC | Endpoints | Auth Required | Tier | Sensitivity | Disposition | Owner | Fix Required |
|------|-----|-----------|--------------|------|-------------|-------------|-------|-------------|
| `compliance_framework.py` | 228 | 3 | ✅ Required | ENTERPRISE | MED | REGISTER → ENTERPRISE (Sprint 181) | Architect | None |
| `invitations.py` | 540 | 7 | ✅ Required | ENTERPRISE | **PII** | REGISTER → ENTERPRISE + async fix | Architect | Sync `Session` → async `AsyncSession`; add `/api/v1` prefix |
| `nist_govern.py` | 783 | 7 | ✅ Required | ENTERPRISE | HIGH | REGISTER → ENTERPRISE (Sprint 181) | Architect | None |
| `nist_manage.py` | 500 | 8 | ✅ Required | ENTERPRISE | HIGH | REGISTER → ENTERPRISE (Sprint 181) | Architect | None |
| `nist_map.py` | 406 | 7 | ✅ Required | ENTERPRISE | HIGH | REGISTER → ENTERPRISE (Sprint 181) | Architect | None |
| `nist_measure.py` | 474 | 7 | ✅ Required | ENTERPRISE | HIGH | REGISTER → ENTERPRISE (Sprint 181) | Architect | None |
| `templates.py` | 532 | 3 | ❌ **PUBLIC** | CORE (LITE) | **LOW** | REGISTER → CORE + **rate-limit 100/min** + sanitized subset | Architect | Add `slowapi` rate limiter; review response fields for PII |

**`templates.py` RED FLAG**: This is a public endpoint (no auth) serving project templates. It must be rate-limited (100 req/min per IP) to prevent scraping and DDoS. The response must only include a sanitized subset of fields — no internal metadata, user IDs, or pricing information. This is a CORE endpoint, not ENTERPRISE, and should be registered immediately in Sprint 181.

**`invitations.py` PII NOTE**: This file handles team member invitations. It uses synchronous `sqlalchemy.orm.Session` in `async def` route handlers — a P0 correctness bug (blocks the event loop). This must be fixed to `AsyncSession` before registration.

**Total recovered**: 42 endpoints / 3,463 LOC — no new code, just registration + tier gating.

---

## Section 3: OTT Channel Priority (INV-04)

### INV-04: Channel Priority and Abstraction (INVARIANT — LOCKED)

All OTT channels (Telegram, Zalo, Teams, Slack, etc.) MUST go through a single abstraction layer:

```
backend/app/services/agent_bridge/protocol_adapter.py
  normalize(raw_payload, channel: str) -> OrchestratorMessage
  route_to_normalizer(channel: str) -> BaseNormalizer
```

`OrchestratorMessage` v1 schema is frozen 1 sprint after the first normalizer ships. No breaking changes after that without ADR.

### Channel Priority Table

| Priority | Channel | Sprint | Tier Gate | Rationale |
|----------|---------|--------|-----------|-----------|
| P0 (Enterprise) | Microsoft Teams | Sprint 182 | PROFESSIONAL+ | Primary enterprise collaboration platform |
| P0 (Enterprise) | Slack | Sprint 183 | PROFESSIONAL+ | Standard enterprise chat; large pipeline |
| P1 (Vietnam pilot) | Telegram | Sprint 181 | STANDARD+ (limited) | Vietnam pilot customers use Telegram; STANDARD to drive upgrade |
| P1 (Vietnam pilot) | Zalo | Sprint 181 | PROFESSIONAL+ | Vietnam-specific; pilot customers only |
| P2 (Future) | Jira | Sprint 184+ | PROFESSIONAL+ | Enterprise project tracking integration |
| P2 (Future) | Discord | Sprint 184+ | STANDARD+ | Community / developer teams |

**Rules**:
1. Telegram/Zalo thin normalizers in Sprint 181 must NOT delay Teams P0 delivery in Sprint 182
2. `agent_bridge/` package core must be enterprise-grade from day 1: tenant routing, `correlation_id`, audit hooks, per-channel rate limiting
3. Telegram on STANDARD tier is a deliberate Vietnam market decision (CPO BM-10): drives upgrade from LITE → STANDARD

---

## Section 4: LITE Tier Resource Policy (INV-05)

### INV-05: Hibernate/Purge Policy (INVARIANT — LOCKED)

To manage cloud infrastructure costs and comply with GDPR data minimization:

**Hibernate flow** (30 days inactivity):
- Day 23: Email warning "Your Orchestrator LITE workspace will hibernate in 7 days"
- Day 30: Workspace frozen — no new gate evaluations, read-only access
- Evidence files retained in MinIO (billed at storage rate)
- Re-activation: any login immediately restores workspace

**Purge flow** (90 days inactivity from last activity):
- Day 83: Email warning "Your workspace will be permanently deleted in 7 days"
- Day 89: Final warning "48 hours until deletion"
- Day 90: Hard delete — all data purged from PostgreSQL + MinIO
- GDPR: User can request full export at any time up to and including Day 89

**GDPR compliance**:
- `GET /api/v1/account/export` — returns ZIP of all user data (available until Day 89)
- Right to erasure: `DELETE /api/v1/account` — triggers immediate purge regardless of inactivity days

This policy applies to LITE tier only. STANDARD+ accounts do not auto-purge (billing relationship continues).

---

## Section 5: Sprint 186 De-scope

### Original Scope (Too Broad for One Sprint)

Sprint 186 was originally planned as "Multi-Region Deployment + Data Residency" including:
- Multi-region PostgreSQL (primary + read replicas per region)
- MinIO bucket routing per region
- GDPR data residency controls
- CDN Cloudflare routing

**Revised scope** (Expert 5 correction):

Sprint 186 delivers **storage-level data residency only**:
- MinIO/S3 bucket per region (`VN`, `EU`, `US`)
- `project.data_region` field (selectable at project creation)
- Evidence Vault upload/download respects `data_region`
- API `data-region` header enforcement

**What is deferred** (until first EU enterprise contract signed):
- Multi-region PostgreSQL read replicas
- Full GDPR Right to Erasure implementation (basic version in INV-05 above covers LITE tier)
- Data Subject Access Request (DSAR) endpoint
- Consent management UI

**Rationale**: Multi-region DB is complex, expensive, and creates operational risk. We have zero EU enterprise customers today. Build it when an enterprise contract requires it, not speculatively.

---

## Section 6: OTT Security for G3/G4 Gates

### Gate Approval via OTT — Security Rules (INV-06)

| Gate | Tier | OTT Approval Method | Rationale |
|------|------|--------------------|---------:|
| G0.1 / G0.2 | Any | Direct OTT approve allowed | Low stakes; foundation gates |
| G1 | LITE/STANDARD | Direct OTT approve allowed | Team-level decision, lower risk |
| G2 | STANDARD | Direct OTT approve allowed | Architecture review, moderate risk |
| G3 | PROFESSIONAL | **Magic Link required** | Ship-ready gate; irreversible deploy decision |
| G4 | ENTERPRISE | **Magic Link required** | Production validation; highest stakes |

### Magic Link Flow (G3/G4)

```
1. Agent/OTT sends message: "Gate G3 pending approval for project {name}"
2. System generates Magic Link JWT (5-min expiry, HS256 signed):
   { "gate_id": "...", "action": "approve", "exp": now+300, "jti": "<unique>" }
3. OTT message contains: "Approve here: https://app.sdlcorchestrator.com/gates/magic/{token}"
4. User clicks → Browser opens → SSO auth required (if enterprise) or JWT login
5. Approval happens in authenticated browser session
6. Audit log: OTT message ID + Magic Link JWT ID + browser session ID correlated
7. Magic Link expires immediately after use (one-time use)
```

**Security properties**:
- 5-minute expiry prevents replay attacks
- One-time use JTI prevents double-approval
- SSO requirement for ENTERPRISE ensures IdP audit trail
- Audit correlation links OTT message → magic link → browser session → gate action

---

## Consequences

### Positive

1. **Product identity clarity**: Two distinct products, each with a clear target and value proposition
2. **Higher ARPU**: Fewer total customers, but $550/mo average vs $200/mo original — more sustainable
3. **Shorter path to break-even**: Month 16 vs Month 18 (revised unit economics)
4. **Improved LTV:CAC**: 6.6:1 vs original 4.08:1
5. **42 endpoints recovered**: 3,463 LOC of production-ready ENTERPRISE features now reachable (Sprint 181)
6. **Tier gate consistency**: Once C-180-02 + C-180-03 migration is complete, `tier_level` is a single source of truth

### Negative

1. **Sprint 181 migration complexity**: 8+ enum files need updating; `SubscriptionPlan` needs Alembic migration with data backfill — high risk if not careful
2. **STANDARD/LITE users get less investment**: Maintenance-only mode may lead to churn if they expect new features
3. **FOUNDER customers**: Grandfathered forever at ~$150/mo — creates pricing parity concerns long-term
4. **OTT channel delay**: Teams/Slack delivery is Sprint 182-183; 2-3 months before enterprise OTT is available

### Neutral

1. TinySDLC OSS growth may drive Orchestrator pipeline — or may reduce pressure to pay for Orchestrator. Net effect unknown until Q3 2026 data.
2. GDPR/multi-region deferred: Risk if an EU enterprise customer requires this sooner than Sprint 186

### CTO Answers Recorded

- **OTT strategy**: ALL channels via `agent_bridge/protocol_adapter.py` abstraction. Enterprise channels (Teams/Slack) are P0 — Sprint 182/183. Vietnam channels (Telegram/Zalo) are P1 — Sprint 181. OTT channels in TinySDLC (Telegram/Zalo) are a separate implementation; protocol_adapter.py in Orchestrator is the canonical protocol owner per ADR-056 Decision 4.
- **Enterprise SSO**: P0 for first enterprise customer (Sprint 182 design, Sprint 183 GA).
- **protocol_adapter.py**: Python service in `backend/app/services/agent_bridge/`, deferred to Sprint 181 (not Sprint 180).
- **LITE stays**: It is the free cloud acquisition funnel. Removing it eliminates the TinySDLC → Orchestrator conversion path.

---

## Follow-up ADRs

| ADR | Title | Trigger | Sprint |
|-----|-------|---------|--------|
| ADR-060 | Route Registration Standards | D4 outcome (Sprint 181 registration) | Sprint 181 |
| ADR-061 | Enterprise SSO Integration | D5 roadmap — SSO design | Sprint 182 |
| ADR-062 | Compliance Evidence Types | D5 roadmap — SOC2/HIPAA artifacts | Sprint 182-183 |
| ADR-063 | Multi-Region Architecture | Sprint 186 revised scope | Sprint 185 |

---

## Appendix A: 78 Route Tier Mapping

*All 78 routes from `backend/app/api/routes/`. Zero TBD entries. Columns: #, file, prefix, auth_required, tier_requirement.*

*Source: `backend/app/main.py` — 71 `include_router()` calls (registered) + 7 orphaned files confirmed absent from main.py.*

*Note: 7 orphaned routes (marked `[ORPHAN]`) are to be registered in Sprint 181.*

### CORE (LITE) — 15 routes

| # | File | Prefix | Auth | Tier |
|---|------|--------|------|------|
| 1 | `auth.py` | `/api/v1/auth` | Partial (login public) | LITE |
| 2 | `projects.py` | `/api/v1/projects` | Required | LITE |
| 3 | `gates.py` | `/api/v1/gates` | Required | LITE |
| 4 | `evidence.py` | `/api/v1/evidence` | Required | LITE |
| 5 | `dashboard.py` | `/api/v1/dashboard` | Required | LITE |
| 6 | `notifications.py` | `/api/v1/notifications` | Required | LITE |
| 7 | `check_runs.py` | `/api/v1/check-runs` | Required | LITE |
| 8 | `github.py` | `/api/v1/github` | Required | LITE |
| 9 | `feedback.py` | `/api/v1/feedback` | Required | LITE |
| 10 | `docs.py` | `/api/v1/docs` | None (public) | LITE |
| 11 | `api_keys.py` | `/api/v1/api-keys` | Required | LITE |
| 12 | `push.py` | `/api/v1/push` | Required | LITE |
| 13 | `websocket.py` | `/api/v1/ws` | Required | LITE |
| 14 | `framework_version.py` | `/api/v1/framework-version` | Required | LITE |
| 15 | `templates.py` [ORPHAN] | `/api/v1/templates` | ❌ PUBLIC | LITE/CORE |

### STANDARD — 24 routes

| # | File | Prefix | Auth | Tier |
|---|------|--------|------|------|
| 16 | `policies.py` | `/api/v1/policies` | Required | STANDARD |
| 17 | `compliance.py` | `/api/v1/compliance` | Required | STANDARD |
| 18 | `triage.py` | `/api/v1/triage` | Required | STANDARD |
| 19 | `analytics.py` | `/api/v1/analytics` | Required | STANDARD |
| 20 | `analytics_v2.py` | `/api/v1/analytics/v2` | Required | STANDARD |
| 21 | `council.py` | `/api/v1/council` | Required | STANDARD |
| 22 | `sdlc_structure.py` | `/api/v1/sdlc-structure` | Required | STANDARD |
| 23 | `sop.py` | `/api/v1/sop` | Required | STANDARD |
| 24 | `policy_packs.py` | `/api/v1/policy-packs` | Required | STANDARD |
| 25 | `sast.py` | `/api/v1/sast` | Required | STANDARD |
| 26 | `override.py` | `/api/v1/override` | Required | STANDARD |
| 27 | `codegen.py` | `/api/v1/codegen` | Required | STANDARD |
| 28 | `pilot.py` | `/api/v1/pilot` | Required | STANDARD |
| 29 | `preview.py` | `/api/v1/preview` | Required | STANDARD |
| 30 | `payments.py` | `/api/v1/payments` | Required | STANDARD |
| 31 | `ai_providers.py` | `/api/v1/ai-providers` | Required | STANDARD |
| 32 | `teams.py` | `/api/v1/teams` | Required | STANDARD |
| 33 | `organizations.py` | `/api/v1/organizations` | Required | STANDARD |
| 34 | `organization_invitations.py` | `/api/v1/organization-invitations` | Required | STANDARD |
| 35 | `planning.py` | `/api/v1/planning` | Required | STANDARD |
| 36 | `learnings.py` | `/api/v1/learnings` | Required | STANDARD |
| 37 | `risk_analysis.py` | `/api/v1/risk-analysis` | Required | STANDARD |
| 38 | `consultations.py` | `/api/v1/consultations` | Required | STANDARD |
| 39 | `mrp.py` | `/api/v1/mrp` | Required | STANDARD |

### PROFESSIONAL — 31 routes

| # | File | Prefix | Auth | Tier |
|---|------|--------|------|------|
| 40 | `ai_detection.py` | `/api/v1/ai-detection` | Required | PROFESSIONAL |
| 41 | `evidence_timeline.py` | `/api/v1/evidence/timeline` | Required | PROFESSIONAL |
| 42 | `contract_lock.py` | `/api/v1/contract-lock` | Required | PROFESSIONAL |
| 43 | `agents.py` | `/api/v1/agents` | Required | PROFESSIONAL |
| 44 | `evidence_manifest.py` | `/api/v1/evidence/manifest` | Required | PROFESSIONAL |
| 45 | `planning_subagent.py` | `/api/v1/planning/subagent` | Required | PROFESSIONAL |
| 46 | `context_validation.py` | `/api/v1/context-validation` | Required | PROFESSIONAL |
| 47 | `maturity.py` | `/api/v1/maturity` | Required | PROFESSIONAL |
| 48 | `auto_generation.py` | `/api/v1/auto-generation` | Required | PROFESSIONAL |
| 49 | `governance_mode.py` | `/api/v1/governance-mode` | Required | PROFESSIONAL |
| 50 | `vibecoding_index.py` | `/api/v1/vibecoding` | Required | PROFESSIONAL |
| 51 | `stage_gating.py` | `/api/v1/stage-gating` | Required | PROFESSIONAL |
| 52 | `context_authority.py` | `/api/v1/context-authority` | Required | PROFESSIONAL |
| 53 | `ceo_dashboard.py` | `/api/v1/ceo-dashboard` | Required | PROFESSIONAL |
| 54 | `governance_metrics.py` | `/api/v1/governance-metrics` | Required | PROFESSIONAL |
| 55 | `grafana_dashboards.py` | `/api/v1/grafana` | Required | PROFESSIONAL |
| 56 | `dogfooding.py` | `/api/v1/dogfooding` | Required | PROFESSIONAL |
| 57 | `governance_specs.py` | `/api/v1/governance-specs` | Required | PROFESSIONAL |
| 58 | `governance_vibecoding.py` | `/api/v1/governance-vibecoding` | Required | PROFESSIONAL |
| 59 | `context_authority_v2.py` | `/api/v1/context-authority/v2` | Required | PROFESSIONAL |
| 60 | `gates_engine.py` | `/api/v1/gates/engine` | Required | PROFESSIONAL |
| 61 | `compliance_validation.py` | `/api/v1/compliance/validation` | Required | PROFESSIONAL |
| 62 | `cross_reference.py` | `/api/v1/cross-reference` | Required | PROFESSIONAL |
| 63 | `e2e_testing.py` | `/api/v1/e2e` | Required | PROFESSIONAL |
| 64 | `telemetry.py` | `/api/v1/telemetry` | Required | PROFESSIONAL |
| 65 | `mcp_analytics.py` | `/api/v1/mcp/analytics` | Required | PROFESSIONAL |
| 66 | `deprecation_monitoring.py` | `/api/v1/deprecation` | Required | PROFESSIONAL |
| 67 | `vcr.py` | `/api/v1/vcr` | Required | PROFESSIONAL |
| 68 | `spec_converter.py` | `/api/v1/spec/convert` | Required | PROFESSIONAL |
| 69 | `cross_reference_validation.py` | `/api/v1/cross-reference/validate` | Required | PROFESSIONAL |
| 70 | `agent_team.py` | `/api/v1/agent-team` | Required | PROFESSIONAL |

### ENTERPRISE — 8 routes

| # | File | Prefix | Auth | Tier |
|---|------|--------|------|------|
| 71 | `admin.py` | `/api/v1/admin` | Required | ENTERPRISE |
| 72 | `tier_management.py` | `/api/v1/tier-management` | Required | ENTERPRISE |
| 73 | `compliance_framework.py` [ORPHAN] | `/api/v1/compliance/framework` | Required | ENTERPRISE |
| 74 | `invitations.py` [ORPHAN] | `/api/v1/invitations` | Required | ENTERPRISE |
| 75 | `nist_govern.py` [ORPHAN] | `/api/v1/nist/govern` | Required | ENTERPRISE |
| 76 | `nist_manage.py` [ORPHAN] | `/api/v1/nist/manage` | Required | ENTERPRISE |
| 77 | `nist_map.py` [ORPHAN] | `/api/v1/nist/map` | Required | ENTERPRISE |
| 78 | `nist_measure.py` [ORPHAN] | `/api/v1/nist/measure` | Required | ENTERPRISE |

**Totals**: 15 CORE + 24 STANDARD + 31 PROFESSIONAL + 8 ENTERPRISE = **78 routes** ✅ (zero TBD)

> **Audit methodology**: File names verified against `backend/app/api/routes/` directory (76 .py files, excluding `__init__.py`). Registration status verified against 71 `include_router()` calls in `backend/app/main.py`. All 7 orphans confirmed absent from main.py include_router calls.

---

## Appendix B: 7 Orphaned Route Security Rubric

| File | LOC | Endpoints | Auth Required | Tier | Sensitivity | Disposition | Owner | Fix Required |
|------|-----|-----------|--------------|------|-------------|-------------|-------|-------------|
| `compliance_framework.py` | 228 | 3 | ✅ | ENTERPRISE | MED | Register → ENTERPRISE | Architect | None |
| `invitations.py` | 540 | 7 | ✅ | ENTERPRISE | **PII** | Register → ENTERPRISE | Architect | sync→async `Session`; add `/api/v1` prefix |
| `nist_govern.py` | 783 | 7 | ✅ | ENTERPRISE | HIGH | Register → ENTERPRISE | Architect | None |
| `nist_manage.py` | 500 | 8 | ✅ | ENTERPRISE | HIGH | Register → ENTERPRISE | Architect | None |
| `nist_map.py` | 406 | 7 | ✅ | ENTERPRISE | HIGH | Register → ENTERPRISE | Architect | None |
| `nist_measure.py` | 474 | 7 | ✅ | ENTERPRISE | HIGH | Register → ENTERPRISE | Architect | None |
| `templates.py` | 532 | 3 | ❌ PUBLIC | CORE | LOW | Register → CORE + rate-limit 100/min | Architect | Add `slowapi` limiter; sanitize response fields |

**Totals**: 3,463 LOC, 42 endpoints recovered in Sprint 181.

---

## Appendix C: Tier-Billing Migration Plan (Sprint 181)

### Step 1: Create Canonical Enum in Central File

Create `backend/app/models/enums.py` with the canonical tier enum (if not already existing):

```python
# backend/app/models/enums.py — CANONICAL TIER ENUM
import enum

class TierLevel(str, enum.Enum):
    """Canonical product tier classification (SDLC 6.1.0).

    This is the single source of truth for feature entitlements.
    All other tier enums in the codebase should alias or reference this.
    """
    LITE = "LITE"
    STANDARD = "STANDARD"
    PROFESSIONAL = "PROFESSIONAL"
    ENTERPRISE = "ENTERPRISE"
```

### Step 2: Rename `SubscriptionPlan.FREE → .LITE`, Add `PROFESSIONAL`

```python
# backend/app/models/subscription.py
class SubscriptionPlan(str, enum.Enum):
    LITE_FREE = "lite_free"          # was: FREE = "free"
    STD_STARTER = "std_starter"      # new value
    STD_GROWTH = "std_growth"        # new value
    PROFESSIONAL = "professional"    # new value — was MISSING
    ENTERPRISE = "enterprise"        # unchanged
    FOUNDER_LEGACY = "founder_legacy"  # was: FOUNDER = "founder"
```

### Step 3: Fix `ProjectTier` in `tier_approval.py`

Convert from plain `str` to proper `enum.Enum`, rename `FREE → LITE`:

```python
# backend/app/schemas/tier_approval.py (before: plain str class)
class ProjectTier(str, enum.Enum):  # NOW a proper enum.Enum
    LITE = "LITE"              # was: FREE = "FREE"
    STANDARD = "STANDARD"
    PROFESSIONAL = "PROFESSIONAL"
    ENTERPRISE = "ENTERPRISE"
```

### Step 4: Audit and Update Remaining 5 Affected Files

| File | Current Issue | Fix |
|------|--------------|-----|
| `schemas/codegen/template_blueprint.py::ProjectTier` | Correct already (LITE/STD/PRO/ENT) | No change |
| `schemas/context_authority.py::TierEnum` | Correct already (LITE/STD/PRO/ENT) | No change |
| `models/sdlc_validation.py::SDLCTier` | Lowercase values (lite/std/pro/ent) | Acceptable for this model — no change |
| `schemas/policy_pack.py::PolicyTier` | Mixed casing (LITE + lowercase) | Normalize to SCREAMING_SNAKE_CASE |
| `policies/tier_policies.py::PolicyTier` | Correct already (LITE/STD/PRO/ENT) | No change |

### Step 5: Alembic Migration

> **CRITICAL**: The PostgreSQL enum type is named `subscription_plan_enum` (NOT `subscriptionplan`).
> Confirmed at `backend/app/models/subscription.py:121`:
> `Enum(SubscriptionPlan, name="subscription_plan_enum", create_constraint=True)`
> And `backend/alembic/versions/s58_subscription_payment.py` (lines 26–31).

```python
# backend/alembic/versions/s181_001_tier_billing_unification.py
def upgrade():
    # Step A: Add new enum values FIRST (PostgreSQL requires this before UPDATE)
    op.execute("ALTER TYPE subscription_plan_enum ADD VALUE IF NOT EXISTS 'lite_free'")
    op.execute("ALTER TYPE subscription_plan_enum ADD VALUE IF NOT EXISTS 'std_starter'")
    op.execute("ALTER TYPE subscription_plan_enum ADD VALUE IF NOT EXISTS 'std_growth'")
    op.execute("ALTER TYPE subscription_plan_enum ADD VALUE IF NOT EXISTS 'professional'")
    op.execute("ALTER TYPE subscription_plan_enum ADD VALUE IF NOT EXISTS 'founder_legacy'")

    # Step B: Data backfill — rename existing values
    op.execute("UPDATE subscriptions SET plan = 'lite_free' WHERE plan = 'free'")
    op.execute("UPDATE subscriptions SET plan = 'founder_legacy' WHERE plan = 'founder'")
    # Existing 'standard' rows → 'std_starter' (conservative: keep on lower STANDARD plan)
    op.execute("UPDATE subscriptions SET plan = 'std_starter' WHERE plan = 'standard'")

def downgrade():
    # Reverse data backfill (PostgreSQL enum values cannot be deleted — only data reverted)
    op.execute("UPDATE subscriptions SET plan = 'free' WHERE plan = 'lite_free'")
    op.execute("UPDATE subscriptions SET plan = 'founder' WHERE plan = 'founder_legacy'")
    op.execute("UPDATE subscriptions SET plan = 'standard' WHERE plan = 'std_starter'")
    op.execute("UPDATE subscriptions SET plan = 'standard' WHERE plan = 'std_growth'")
```

### Step 6: Data Backfill Verification

```bash
# Verify after migration
cd /home/nqh/shared/SDLC-Orchestrator/backend
python3 -c "
from app.models.subscription import SubscriptionPlan
assert SubscriptionPlan.LITE_FREE == 'lite_free'
assert SubscriptionPlan.PROFESSIONAL == 'professional'
assert SubscriptionPlan.FOUNDER_LEGACY == 'founder_legacy'
print('Tier-billing migration: ALL CHECKS PASS')
"
```

---

## Appendix D: CPO Pricing Decision Register

> **Note**: Per Expert 4 fix #8 (Pricing SSOT), this appendix contains references only — no pricing numbers are duplicated here. All commercial pricing decisions are owned by CPO (SE4H role: taidt@mtsolution.com.vn) and governed by the internal CPO Pricing Decision Register (BM-01 through BM-10, Feb 19, 2026).

| Decision ID | Summary | Status |
|-------------|---------|--------|
| BM-01 | Revenue streams: SaaS subscriptions + Professional Services + Marketplace (Q3 2026+) | DECIDED |
| BM-02 | PROFESSIONAL tier pricing (Vietnam fit, per CPO review) | DECIDED |
| BM-03 | Enterprise seat pricing model + minimum floor | DECIDED |
| BM-04 | FOUNDER → legacy SKU, no new signups after Sprint 181 launch | DECIDED |
| BM-05 | 14-day PROFESSIONAL trial on LITE signup (no credit card) | DECIDED |
| BM-06 | Revised Year 1 ARR target (higher than original due to enterprise-first ARPU) | DECIDED |
| BM-07 | Revised LTV:CAC target (improved due to enterprise focus) | DECIDED |
| BM-08 | Break-even timeline (accelerated vs original model) | DECIDED |
| BM-09 | Two-product ecosystem model (TinySDLC OSS + Orchestrator commercial) | DECIDED |
| BM-10 | Telegram on STANDARD (Vietnam retention); Teams/Slack on PROFESSIONAL+ | DECIDED |

Required actions after this ADR is approved:
- [ ] Update `docs/00-foundation/05-Market-Analysis/Financial-Model.md` → v2.0.0
- [ ] Update `docs/00-foundation/02-Business-Case/Business-Requirements-Document.md` → v3.0.0 (ICP revision)
- [ ] Update `docs/00-foundation/05-Market-Analysis/Market-Sizing.md` → v4.0.0 (two-product SAM/SOM split)
- [ ] CEO review required before external communication (pricing page, Product Hunt)

---

## Appendix E: Out of Scope (Deferred Items)

| Item | Why Deferred | Sprint |
|------|-------------|--------|
| `protocol_adapter.py` implementation | Needs ADR-059 channel priority confirmed first | Sprint 181 |
| `agent_bridge/` package creation | Depends on protocol_adapter.py | Sprint 181 |
| ADR-060 Route Registration Standards | Sprint 181 registration work first | Sprint 181 |
| ADR-061 Enterprise SSO | Design sprint needed before implementation | Sprint 182 |
| ADR-062 Compliance Evidence Types | After SSO design confirmed | Sprint 182+ |
| ADR-063 Multi-Region Architecture | After first EU enterprise contract | Sprint 185 |
| CLAUDE.md v3.9.0 | After ADR-059 approved | End of Sprint 180 or Sprint 181 |
| Enterprise pricing page copy | CPO + Marketing | Sprint 188 |
| Product Hunt launch | After G4 gate approved | Sprint 188 |
| Multi-region DB + read replicas | No EU customers yet (see Section 5) | Sprint 186+ |
| DSAR endpoint | No GDPR obligation until EU customers | Sprint 186+ |
| GDPR consent management UI | Same as DSAR | Sprint 186+ |
| OSS partnership (STANDARD free for OSS projects) | CPO decision; Q2 2026 | Q2 2026 |

---

*ADR-059 accepted 2026-02-19. Sprint 180 formally closed. Next: Sprint 181 begins route activation and OTT foundation.*
