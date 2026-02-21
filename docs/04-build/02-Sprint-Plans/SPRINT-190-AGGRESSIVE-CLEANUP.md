---
sdlc_version: "6.1.0"
document_type: "Sprint Plan"
status: "CEO APPROVED"
sprint: "190"
spec_id: "SPRINT-190"
tier: "ALL"
stage: "04 - Build"
expert_review: "9/9 APPROVE (Expert 8 SDLC/Governance + Expert 9 Enterprise Arch)"
---

# SPRINT-190 — Conversation-First Cleanup (~21K LOC Deletion)

**Status**: CEO APPROVED (Feb 21, 2026) — Expert Panel 9/9 APPROVE
**Sprint Duration**: 8 working days + Day 0.5 pre-sprint audit
**Sprint Goal**: Delete ~21K LOC of frozen/unused code, align interfaces with CEO's Conversation-First directive
**Epic**: EP-08 Chat-First Governance Loop (P1 — Cleanup)
**ADR**: ADR-064 (Option D+)
**Dependencies**: Sprint 189 complete (Chat Governance Loop PoC — CTO APPROVED 9.4/10)
**Budget**: ~$5,120 (64 hrs at $80/hr)

---

## 1. Sprint Goal

Sprint 190 is the aggressive cleanup phase aligned with CEO's **Conversation-First Interface Strategy**:

> "web app chủ yếu dùng cho admin hoặc owner, team member phần lớn thời gian sẽ là conversation-first qua OTT hoặc CLI"

**Interface Strategy (CEO Decided)**:

| Interface | Role | Investment |
|-----------|------|-----------|
| **OTT Gateway** | **PRIMARY** — conversation-first for team members | Active dev |
| **CLI (sdlcctl)** | **PRIMARY** — unified commands with OTT, for devs + AI Codex | Active dev |
| **Web App** | **ADMIN ONLY** — enterprise features that OTT/CLI can't do | Simplify to 5 pages |
| **VSCode Extension** | **FROZEN** | Bug fixes only, defer to Sprint 193+ |

**Enterprise Channels**: MS Teams + Slack retained — enterprise security policies prohibit consumer OTT for work.

**Target**: Delete ~21K LOC of frozen services + feature-flag dashboard to 5 admin pages.

| Track | Priority | Days |
|-------|----------|------|
| Pre-sprint dependency audit | P0 | 0.5 |
| NIST services deletion (4 files, ~6,418 LOC) | P0 | 1 |
| AI Council + Feedback Learning deletion (3 files, ~4,083 LOC) | P0 | 1 |
| SOP/Spec/Pilot + V1 routes deletion (~3,777 LOC) | P0 | 1 |
| Router cleanup + import hygiene | P0 | 1 |
| Dashboard feature-flag + RBAC + React fallback | P1 | 1 |
| DB tables deprecation (COMMENT, NOT DROP) | P1 | 1 |
| Test cleanup + smoke tests + verification | P0 | 1 |
| CLAUDE.md update + background task cleanup + sprint close | -- | 1 |
| **Total** | | **8.5** |

---

## 2. Files to Delete

### Tier 1: Service Files (Day 1-3)

| # | File | LOC | Reason | Day |
|---|------|-----|--------|-----|
| 1 | `backend/app/services/nist_govern_service.py` | 1,653 | Frozen, zero cross-imports | 1 |
| 2 | `backend/app/services/nist_map_service.py` | 1,697 | Frozen, zero cross-imports | 1 |
| 3 | `backend/app/services/nist_manage_service.py` | 1,964 | Frozen, zero cross-imports | 1 |
| 4 | `backend/app/services/nist_measure_service.py` | 1,104 | Frozen, zero cross-imports | 1 |
| 5 | `backend/app/services/ai_council_service.py` | 1,895 | Frozen, sandbox only | 2 |
| 6 | `backend/app/services/feedback_learning_service.py` | 1,588 | Frozen, never in frontend | 2 |
| 7 | `backend/app/jobs/learning_aggregation.py` | ~600 | **Collateral**: imports feedback_learning_service | 2 |
| 8 | `backend/app/services/sop_generator_service.py` | ~500 | Frozen, unused | 3 |
| 9 | `backend/app/services/spec_converter/` (directory, 11 files) | ~800 | Frozen, **verified**: zero imports from vcr/crp | 3 |
| 10 | `backend/app/services/pilot_tracking_service.py` | 914 | Frozen, unused | 3 |
| 11 | `backend/app/services/analytics_service.py` (v1) | 901 | **CEO Amendment**: superseded by analytics_v2 | 3 |
| 12 | `backend/app/services/governance/context_authority.py` (v1) | 662 | **CEO Amendment**: superseded by context_authority_v2 | 3 |

**NOT deleted (blocker)**:
- `sase_generation_service.py` — `vcr_service.py` (line 655) and `crp_service.py` (line 496) actively import it. **Deferred to Sprint 191+** after refactoring those imports.

### Tier 2: Route Files (Day 1-3, co-deleted with services)

| # | File | LOC | main.py Symbol | Day |
|---|------|-----|----------------|-----|
| 13 | `backend/app/api/routes/nist_govern.py` | 783 | `nist_govern.router` | 1 |
| 14 | `backend/app/api/routes/nist_manage.py` | 500 | `nist_manage.router` | 1 |
| 15 | `backend/app/api/routes/nist_map.py` | 406 | `nist_map.router` | 1 |
| 16 | `backend/app/api/routes/nist_measure.py` | 474 | `nist_measure.router` | 1 |
| 17 | `backend/app/api/routes/council.py` | 884 | `council.router` | 2 |
| 18 | `backend/app/api/routes/feedback.py` | ~400 | `feedback.router` | 2 |
| 19 | `backend/app/api/routes/learnings.py` | 795 | `learnings.router` | 2 |
| 20 | `backend/app/api/routes/sop.py` | 701 | `sop.router` | 3 |
| 21 | `backend/app/api/routes/pilot.py` | 630 | `pilot.router` | 3 |
| 22 | `backend/app/api/routes/spec_converter.py` | 550 | `spec_converter.router` | 3 |
| 23 | `backend/app/api/routes/analytics.py` (v1) | 902 | `analytics.router` | 3 |
| 24 | `backend/app/api/routes/context_authority.py` (v1) | 663 | `context_authority.router` | 3 |
| 25 | `backend/app/api/routes/dogfooding.py` | 1,682 | `dogfooding.router` | 3 |

### Tier 3: Supporting Files (Day 4, 7)

| # | File | Action | Day |
|---|------|--------|-----|
| 26 | Corresponding test files for all deleted services | Delete | 7 |
| 27 | Model imports in `models/__init__.py` | Remove unused | 4 |
| 28 | Router imports in `main.py` | Remove by **symbol name** (NOT line numbers) | 4 |
| 29 | Re-exports in `services/__init__.py` | Clean up | 4 |

---

## 3. Daily Schedule

### Day 0.5 (Pre-Sprint): Dependency Audit

**Goal**: Verify all deletion targets are truly safe before any code changes.

**Create `scripts/sprint190_audit_deps.sh`**:

```bash
#!/bin/bash
# Sprint 190 — Pre-deletion dependency audit
set -e

echo "=== 1. Python Import Check ==="
PATTERNS="NistGovern|NistMap|NistManage|NistMeasure|AICouncil|FeedbackLearning|SpecConverter|PilotTracking|SopGenerator"
rg "$PATTERNS" backend/app -g'*.py' --files-with-matches || echo "No unexpected matches"

echo "=== 2. Router Registrations (by symbol) ==="
grep -E "nist_govern|nist_map|nist_manage|nist_measure|council|feedback|learnings|sop|pilot|spec_converter|dogfooding|analytics\.router" backend/app/main.py || echo "None found"

echo "=== 3. Foreign Key Dependencies ==="
echo "Run in PostgreSQL:"
echo "SELECT conrelid::regclass, confrelid::regclass FROM pg_constraint WHERE contype='f' AND confrelid::regclass::text ~ 'nist|council|feedback|spec|pilot|sop';"

echo "=== 4. Background Tasks ==="
rg "nist_|council|feedback_learning|learning_aggregation" backend/app/jobs/ -g'*.py' || echo "No background tasks found"

echo "=== 5. Alembic Migration References ==="
rg "nist_|ai_council|feedback_learning" backend/alembic/versions/ -l || echo "No direct references"

echo "✅ Audit complete."
```

### Day 1: NIST Services + Routes Deletion (~6,418 LOC services + ~2,163 LOC routes)

**Goal**: Delete 4 NIST services and 4 NIST routes

**Steps**:
1. Remove 4 NIST import lines from `main.py` (find by symbol: `nist_govern`, `nist_manage`, `nist_map`, `nist_measure`)
2. Remove 4 `include_router` calls (find by symbol: `nist_govern.router`, `nist_manage.router`, `nist_map.router`, `nist_measure.router`)
3. Delete 4 service files: `nist_govern_service.py`, `nist_manage_service.py`, `nist_map_service.py`, `nist_measure_service.py`
4. Delete 4 route files: `routes/nist_govern.py`, `routes/nist_manage.py`, `routes/nist_map.py`, `routes/nist_measure.py`
5. Remove unused model imports in `models/__init__.py`
6. Run `ruff check backend/` → fix broken imports
7. Run `python -c "from app.main import app"` → verify clean startup

### Day 2: AI Council + Feedback Learning Deletion (~4,083 LOC services + ~2,079 LOC routes)

**Goal**: Delete AI Council + Feedback Learning services, routes, and collateral job

**Steps**:
1. Remove router registrations by symbol: `council.router`, `feedback.router`, `learnings.router`
2. Remove imports from mega-import line in `main.py`: `council`, `feedback`, `learnings`
3. Delete service files: `ai_council_service.py` (1,895 LOC), `feedback_learning_service.py` (1,588 LOC)
4. Delete collateral job: `learning_aggregation.py` (~600 LOC) — imports deleted `feedback_learning_service`
5. Delete route files: `council.py`, `feedback.py`, `learnings.py`
6. Run `ruff check backend/` + `python -c "from app.main import app"`

### Day 3: SOP/Spec/Pilot + V1 Routes + Dogfooding Deletion (~3,777 LOC services + ~4,128 LOC routes)

**Goal**: Delete remaining frozen services + CEO-amended V1 routes

**Steps**:
1. Remove router registrations by symbol: `sop.router`, `pilot.router`, `spec_converter.router`, `analytics.router`, `context_authority.router`, `dogfooding.router`
2. Remove imports from mega-import line: `sop`, `pilot`, `spec_converter`, `analytics`, `context_authority`, `dogfooding`
3. Delete service files:
   - `sop_generator_service.py` (~500 LOC)
   - `pilot_tracking_service.py` (914 LOC)
   - `spec_converter/` directory (~800 LOC, 11 files)
   - `analytics_service.py` v1 (901 LOC) — superseded by `analytics_v2`
   - `governance/context_authority.py` v1 (662 LOC) — superseded by `context_authority_v2`
4. Delete route files: `sop.py`, `pilot.py`, `spec_converter.py`, `analytics.py` (v1), `context_authority.py` (v1), `dogfooding.py`
5. **Verify v2 routes untouched**: `analytics_v2.router` + `context_authority_v2.router` still in `main.py`
6. Run `ruff check backend/` + `python -c "from app.main import app"`

**Add 410 Gone stub router** (`backend/app/api/routes/deprecated_routes.py`):
- Returns HTTP 410 for all deprecated endpoint prefixes
- Message: "This endpoint deprecated in Sprint 190. Use OTT/CLI."
- Register in `main.py` AFTER all other routers (catch-all for 1 sprint)
- **Remove in Sprint 191**

### Day 4: Router Cleanup + Import Hygiene

**Goal**: Zero orphaned imports, ruff clean

**Steps**:
1. Clean up mega-import line in `main.py` — remove all deleted route symbols
2. Clean up `models/__init__.py` — remove model imports for deleted services
3. Clean up `services/__init__.py` — remove re-exports
4. Verify no orphaned imports across codebase: `rg "from app.services.nist" backend/app/`
5. Run `ruff check backend/` → **target 0 errors**
6. Run `python -c "from app.main import app; print(f'Routes: {len(app.routes)}')"` → verify clean startup

### Day 5: Dashboard Feature-Flag + RBAC + React Fallback

**Goal**: Simplify dashboard to 5 admin pages, enforce admin-only via RBAC

**Default ON (5 admin pages)**:
1. **Projects** — admin manages projects
2. **Gates** — admin oversight + approve
3. **Evidence** — admin review + verify
4. **Team** — admin-only: agents + roles + members
5. **Settings** — admin-only: billing + SSO + config + data residency

**Implementation**:
1. Add `FEATURE_FLAG_LEGACY_DASHBOARD` env var (default `false`)
2. Frontend: wrap sidebar navigation items with flag check. Pages remain in codebase but unreachable from nav.
3. **React Router fallback component**: Hidden pages show "Feature moved to Conversation-First interface" with links to Telegram Bot and back to Projects.
4. **RBAC middleware enforcement** (`conversation_first_guard`): For admin-only write paths (teams, settings, billing, SSO), verify `user.role in ["admin", "owner"]` on POST/PUT/PATCH/DELETE. Return 403 with "Use OTT or CLI" message for non-admin users.

### Day 6: DB Tables Deprecation (Reversible Migration)

**Goal**: Mark unused tables deprecated (NOT drop)

**Alembic Migration**: `s190_001_deprecate_unused_tables.py`

```python
DEPRECATED_TABLES = [
    'nist_govern', 'nist_map', 'nist_manage', 'nist_measure',
    'ai_council_sessions', 'feedback_learning',
]

def upgrade():
    for table in DEPRECATED_TABLES:
        op.execute(f"COMMENT ON TABLE {table} IS 'DEPRECATED Sprint 190 — frozen, unused. See ADR-064.'")

def downgrade():
    # REVERSIBLE (Expert 8 correction — not NotImplementedError)
    for table in DEPRECATED_TABLES:
        op.execute(f"COMMENT ON TABLE {table} IS NULL")
```

**Update `alembic/env.py`** — add `include_object` to ignore deprecated tables in autogenerate:

```python
DEPRECATED_TABLES = {'nist_govern', 'nist_map', 'nist_manage', 'nist_measure', 'ai_council_sessions', 'feedback_learning'}

def include_object(object, name, type_, reflected, compare_to):
    if type_ == "table" and name in DEPRECATED_TABLES:
        return False
    return True
```

### Day 7: Test Cleanup + Smoke Tests + Verification

**Goal**: All tests green, 3 new smoke tests pass

**Steps**:
1. Delete test files for all deleted services/routes (~2,000 LOC)
2. **Add 3 smoke integration tests** (`backend/tests/integration/test_sprint190_smoke.py`):
   - Test 1: Application starts + healthcheck passes
   - Test 2: Gate actions endpoint works (`requires_oob_auth` field present)
   - Test 3: OTT channel ingestion works (Telegram webhook)
3. **Add SASE anti-regression test** (`backend/tests/integration/test_sase_dependency.py`):
   - Verify `vcr_service.py` and `crp_service.py` can still import SASE
   - Comment: "DO NOT TOUCH sase_generation_service.py until Sprint 191 refactor"
4. Run `ruff check backend/` → 0 errors
5. Run `python -m pytest backend/tests/` → all green
6. Verify Sprint 189 acceptance tests still pass
7. Run `semgrep --config backend/policy-packs/`
8. Verify LOC count

### Day 8: CLAUDE.md + Background Tasks + Sprint Close

**Goal**: Documentation updated, sprint closed

**Steps**:
1. **Audit background tasks**: Check `backend/app/jobs/` for tasks referencing deleted services. `learning_aggregation.py` already deleted Day 2. Verify `jobs/__init__.py` has no orphaned imports.
2. **Update CLAUDE.md**: Add Interface Strategy section (conversation-first), remove references to deleted services from Module Zones, update file/route counts.
3. Create **SPRINT-190-CLOSE.md** with LOC metrics (before/after).
4. CTO review of deletion scope.
5. Verify git history preserves all deleted code.

---

## 4. Routes to KEEP (actively used)

| Symbol | Tag | Reason |
|--------|-----|--------|
| `analytics_v2.router` | Analytics v2 | Current analytics (supersedes v1) |
| `context_authority_v2.router` | Context Authority V2 | Current context authority (supersedes v1) |
| `agent_team.router` | Multi-Agent Team Engine | EP-07 (Sprint 176) |
| `ott_gateway.router` | OTT Gateway | Sprint 189 — PRIMARY interface |
| `enterprise_sso.router` | Enterprise SSO | SAML 2.0 (Sprint 183) |
| `jira_integration.router` | Jira Integration | PROFESSIONAL+ (Sprint 184) |
| `audit_trail.router` | Audit Trail | ENTERPRISE (Sprint 185) |
| `data_residency.router` | Data Residency | ENTERPRISE (Sprint 186) |
| `gdpr.router` | GDPR | Sprint 186 |
| `compliance_framework.router` | Compliance Framework | ENTERPRISE (Sprint 181) |
| `templates.router` | Templates | CORE public (Sprint 181) |
| `invitations.router` | Invitations | ENTERPRISE (Sprint 181) |
| All core routes | auth, gates, evidence, projects, teams, planning, github, codegen, admin, etc. | Core product |

## 5. Files NOT to Touch

- `backend/app/services/agent_team/` — Sprint 189 deliverables (keep all)
- `backend/app/services/agent_bridge/` — OTT normalizers: Telegram, Zalo, MS Teams, Slack (keep all)
- `backend/app/api/routes/ott_gateway.py` — Sprint 189 (keep)
- `backend/app/services/sase_generation_service.py` — VCR/CRP dependency (keep, deferred to Sprint 191)
- `backend/app/services/sase_sprint_integration.py` — Coupled with SASE (keep, deferred)
- `backend/app/services/governance/context_authority_v2.py` — Active v2 (keep)
- `backend/app/services/analytics_v2_service.py` — Active v2 (keep)
- All enterprise routes: SSO, Jira, Audit Trail, Data Residency, GDPR

---

## 6. Verification Criteria

| # | Criterion | Target | Day |
|---|-----------|--------|-----|
| 1 | `scripts/sprint190_audit_deps.sh` | 0 unexpected refs | 0.5 |
| 2 | `ruff check backend/` | 0 errors | 4 |
| 3 | `python -m pytest backend/tests/` | All green | 7 |
| 4 | `test_sprint190_smoke.py` | 3/3 pass | 7 |
| 5 | Backend LOC reduction | ~21K deleted | 7 |
| 6 | Dashboard default pages | 5 admin pages | 5 |
| 7 | Deprecated routes return 410 | Verified | 3 |
| 8 | Alembic autogenerate | No DROP commands for deprecated tables | 6 |
| 9 | Background tasks | No orphan tasks referencing deleted services | 8 |
| 10 | React Router fallback | Shows "moved to chat" message | 5 |
| 11 | Sprint 189 acceptance tests | Still pass (no regression) | 7 |
| 12 | Enterprise channels (Teams/Slack) | Still functional | 7 |

---

## 7. Risk Register

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Cleanup breaks hidden dependencies | LOW | HIGH | Day 0.5 audit script + `rg` search before each deletion |
| Tests reference deleted services | MEDIUM | MEDIUM | Delete tests same day as services + 3 smoke tests |
| SASE deletion breaks VCR/CRP | BLOCKED | HIGH | **Deferred** to Sprint 191 — anti-regression test locks it |
| Model FK dependencies prevent table comment | LOW | LOW | COMMENT ON TABLE works regardless of FK status |
| Dashboard regression after feature-flag | LOW | MEDIUM | RBAC middleware + React fallback + 5 default pages tested |
| Alembic autogenerate creates DROP | LOW | HIGH | `include_object` filter in env.py |
| Background task crashes on deleted service | MEDIUM | MEDIUM | Day 8 audit of jobs/ directory |

---

## 8. Expert Corrections Applied

| # | Correction | Source | Status |
|---|------------|--------|--------|
| 1 | Dependency audit script before delete | Expert 8 | Day 0.5 |
| 2 | Reversible migration (`COMMENT ON TABLE ... IS NULL` in downgrade) | Expert 8 | Day 6 |
| 3 | Use symbol names, NOT line numbers in main.py | Expert 8 | All days |
| 4 | Alembic `env.py` `include_object` for deprecated tables | Expert 9 | Day 6 |
| 5 | Clean up background tasks in `jobs/` | Expert 9 | Day 8 |
| 6 | 410 Gone stub router (`deprecated_routes.py`) | Expert 8 | Day 3 |
| 7 | RBAC enforcement for admin-only web write | Expert 8 | Day 5 |
| 8 | 3 smoke integration tests | Expert 8 | Day 7 |
| 9 | SASE anti-regression lock (test + "DO NOT TOUCH") | Expert 8 | Day 7 |
| 10 | React Router fallback component | Expert 9 | Day 5 |
| 11 | Command registry limit (10 commands max) for Sprint 191+ | Expert 8 | Deferred |

---

## 9. Definition of Done

- [ ] Dependency audit script run, 0 unexpected refs
- [ ] ~21K LOC of frozen services + routes deleted
- [ ] All router registrations for deleted services removed from `main.py` (by symbol name)
- [ ] `deprecated_routes.py` returns 410 for all deleted endpoints
- [ ] `ruff check backend/` → 0 errors
- [ ] `python -m pytest backend/tests/` → all green
- [ ] 3 smoke integration tests pass
- [ ] SASE anti-regression test in place
- [ ] Dashboard default view = 5 admin pages
- [ ] RBAC middleware enforces admin-only write
- [ ] React Router fallback shows "moved to chat" message
- [ ] DB tables marked DEPRECATED (reversible migration)
- [ ] Alembic `env.py` ignores deprecated tables in autogenerate
- [ ] Background tasks cleaned (no orphan references)
- [ ] Sprint 189 acceptance tests still pass (no regression)
- [ ] Enterprise channels (Teams/Slack) still functional
- [ ] CLAUDE.md updated with conversation-first interface strategy
- [ ] CTO review APPROVED
- [ ] SPRINT-190-CLOSE.md created with LOC metrics
