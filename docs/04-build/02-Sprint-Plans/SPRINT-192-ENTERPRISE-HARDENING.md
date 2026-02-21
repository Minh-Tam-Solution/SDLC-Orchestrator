---
sdlc_version: "6.1.1"
document_type: "Sprint Plan"
status: "APPROVED"
sprint: "192"
spec_id: "SPRINT-192"
tier: "ALL"
stage: "04 - Build"
cto_review: "8.2/10 APPROVED WITH CORRECTIONS"
reviewer_audit: "Frontend/Backend Mismatch Report (2026-02-21)"
---

# Sprint 192 — Enterprise Hardening + Security Parity

**Status**: APPROVED (CTO 8.2/10 + Reviewer Frontend Audit incorporated)
**Duration**: 8 working days
**Goal**: Close EP-08 P2 gaps + fix Sprint 190-191 frontend/backend mismatches + harden security parity across all OTT channels
**Epic**: EP-08 Chat-First Governance Loop (P2 — Enterprise Hardening)
**ADR**: ADR-064 (Option D+, 4 locked decisions)
**Preceded by**: Sprint 191 (Unified Command Registry, CTO 8.9/10)
**Budget**: ~$5,120 (64 hrs @ $80/hr)

---

## Context

- Sprint 189 delivered Chat-First Governance Loop PoC (CTO 9.4/10)
- Sprint 190 deleted ~21K LOC backend (CEO APPROVED, 9/9 Expert Panel)
- Sprint 191 delivered Unified Command Registry + requirements split (CTO 8.9/10)
- **Reviewer audit (2026-02-21)**: Found ~2,500 LOC dead frontend code across 48 files referencing deleted backend endpoints — including 1 P0 user-facing breakage
- Sprint 191 close identified 4 recommendations — this sprint addresses 3 of 4 (SASE refactor deferred)

### Two Tracks

| Track | Priority | Scope | Days |
|-------|----------|-------|------|
| **A: Frontend Cleanup** | P0-P2 | Fix Sprint 190-191 frontend/backend mismatches (~2,500 LOC dead code) | Day 1 |
| **B: Security + Compliance** | P0-P2 | Zalo HMAC, Docker, CI hardening, compliance export, break-glass, read-only guard | Days 2-7 |

---

## Deliverables

| # | Deliverable | Description | LOC Delta | Day | Priority |
|---|-------------|-------------|-----------|-----|----------|
| 1 | /pilot page fix | Replace broken public form with `ConversationFirstFallback` | ~-200 | 1 | P0 |
| 2 | api.ts dead export cleanup | Remove ~80 dead function exports calling deleted endpoints | ~-600 | 1 | P1 |
| 3 | Dead hook files deletion | Delete `useCouncil.ts`, `useLearnings.ts`, `useSpecConverter.ts`, `usePilotSignup.ts` | ~-1,098 | 1 | P2 |
| 4 | NIST tab disable | Add `disabled: true` to NIST AI RMF tab in compliance layout | ~3 | 1 | P2 |
| 5 | Stale frontend test cleanup | Delete/archive 13+ test files for deleted features | ~-800 | 1 | P2 |
| 6 | SOP detail pages fallback | Verify backend or add `ConversationFirstFallback` | ~-150 | 1 | P2 |
| 7 | Orphaned i18n keys removal | Remove `sopGenerator`, `specConverter`, `pilot` keys from en.json/vi.json | ~-30 | 1 | P3 |
| 8 | Zalo HMAC-SHA256 verification | `verify_hmac()` in `zalo_normalizer.py`, wire into `ott_gateway.py` | ~60 | 2 | P0 |
| 9 | Docker multi-stage build | 2-stage Dockerfile: builder + runtime (core.txt only) | ~30 | 3 | P0 |
| 10 | sdlcctl CI step | New job in `test.yml`: install sdlcctl, run governance parity tests | ~40 | 3 | P0 |
| 11 | Semgrep SAST CI step | New job in `test.yml`: Semgrep with policy-packs, SARIF upload | ~25 | 4 | P0 |
| 12 | Compliance audit PDF export | New service + route: `POST /api/v1/compliance/export/{project_id}` → PDF | ~250 | 5-6 | P1 |
| 13 | Break-glass web approve | Feature-flagged `POST /gates/{id}/break-glass-approve`, admin-only | ~120 | 7 | P1 |
| 14 | Dashboard read-only enforcement | Extend `ConversationFirstGuard` ADMIN_WRITE_PATHS | ~10 | 7 | P2 |
| 15 | Acceptance tests + sprint close | 10 acceptance tests + SPRINT-192-CLOSE.md | ~200 | 7-8 | P0 |

**Net LOC delta**: ~-2,140 (deleted ~2,878 dead frontend LOC, added ~738 new backend LOC)

---

## CTO Corrections Applied

| # | Finding | Severity | Resolution |
|---|---------|----------|------------|
| P0-1 | `receive_webhook()` missing `x_zalo_oa_signature` header parameter | P0 | Added to Day 2: explicit `Header(default=None)` in function signature |
| P1-2 | Config pattern inconsistency — existing OTT secrets use `os.getenv()` in ott_gateway.py, not Settings | P1 | **Option A adopted**: `_ZALO_APP_SECRET = os.getenv("ZALO_APP_SECRET", "")` module-level in `ott_gateway.py`. No config.py change for Zalo. |
| P2-1 | `tier_gate.py` compliance prefix already covers `/api/v1/compliance/export` | P2 | Removed from modified files — verify prefix match covers it |
| P2-2 | Break-glass role strings — confirm "admin"/"owner" exist in RBAC | P2 | Verify in `models/user.py` before Day 7 implementation |
| P2-3 | Docker image size test #4 not a pytest test | P2 | Replaced with Dockerfile structure assertion (contains `AS builder` + `COPY --from=builder`) |
| P3-1 | Zalo HMAC header name — confirm exact header from Zalo OA docs | P3 | Day 2 starts with Zalo OA API doc verification. Risk register updated. |
| P3-2 | Semgrep CI cache-dependency-path stale | P3 | Use `requirements/core.txt` for cache key in Semgrep job |

---

## Daily Schedule

### Day 1: Frontend/Backend Mismatch Cleanup (Track A — All P0-P3 Frontend)

**Goal**: Eliminate ~2,500 LOC dead frontend code referencing Sprint 190-191 deleted backend endpoints. Fix P0 user-facing /pilot breakage first.

**Source**: Reviewer Frontend/Backend Mismatch Report (2026-02-21)

#### P0 Fix: /pilot page (15 min)

| File | Change |
|------|--------|
| `frontend/src/app/pilot/page.tsx` | Replace entire page content with `ConversationFirstFallback` component (same pattern as `sop-generator/page.tsx`, `learnings/page.tsx`) |

**Why P0**: Public-facing page. Users fill form → submit → 404 error. Backend `POST /api/v1/pilot/participants` deleted Sprint 190 Day 3.

#### P1 Fix: api.ts dead exports (30-45 min)

| File | Change |
|------|--------|
| `frontend/src/lib/api.ts` | Remove ~80 dead function exports in these groups: `/council/*` (4 functions), `/learnings/*` (20+ functions), `/sop/*` (10 functions), `/spec-converter/*` (4 functions), `/nist/*` (44 functions), `/pilot/*` (1 function), `/dogfooding/*` (7 functions) |

**Why P1**: Runtime 404 errors if any component calls these. Bundle bloat. Confuses developers.

#### P2 Fixes (30 min total)

| # | File(s) | Change | LOC |
|---|---------|--------|-----|
| P2-1 | `frontend/src/hooks/useCouncil.ts` | **Delete** — orphaned, no page uses it | -136 |
| P2-1 | `frontend/src/hooks/useLearnings.ts` | **Delete** — page shows ConversationFirstFallback | -519 |
| P2-1 | `frontend/src/hooks/useSpecConverter.ts` | **Delete** — page shows ConversationFirstFallback | -254 |
| P2-1 | `frontend/src/hooks/usePilotSignup.ts` | **Delete** — pilot page being replaced with fallback | -189 |
| P2-2 | `frontend/src/app/app/compliance/layout.tsx` | Add `disabled: true` to NIST AI RMF tab (match EU AI Act / ISO 42001 pattern) | ~3 |
| P2-3 | `frontend/__tests__/app/compliance/nist*` (4 files) | **Delete** — test deleted NIST backend endpoints | ~-300 |
| P2-3 | `frontend/__tests__/components/spec-converter/*` (7 files) | **Delete** — test deleted spec converter | ~-400 |
| P2-3 | `frontend/__tests__/**/sprint171-pilot-landing.spec.ts` | **Delete** — 10 test scenarios mock deleted endpoint | ~-100 |
| P2-4 | `frontend/src/app/app/sop/[id]/page.tsx` + 4 tab components | Verify backend SOP read-only endpoints. If deleted → replace with `ConversationFirstFallback` | ~-150 |

#### P3 Fix: Orphaned i18n keys (5 min)

| File | Keys to Remove |
|------|----------------|
| `frontend/src/messages/en.json` | `"sopGenerator"`, `"specConverter"`, `"pilot"` sections |
| `frontend/src/messages/vi.json` | `"sopGenerator"`, `"specConverter"`, `"pilot"` sections |

**Day 1 Verification**:
- `npm run build` → 0 errors (no broken imports from deleted files)
- Navigate to `/pilot` → shows ConversationFirstFallback (NOT broken form)
- Navigate to `/compliance` → NIST tab shows disabled state
- `grep -r "useCouncil\|useLearnings\|useSpecConverter\|usePilotSignup" frontend/src/` → 0 hits (no orphaned imports)
- Bundle size comparison: before/after (expect ~15-20% reduction in api.ts chunk)

---

### Day 2: Zalo HMAC-SHA256 Verification (Track B — P0 Security Gap)

**Goal**: Close the only OTT channel without webhook signature verification.

**Evidence**: Teams has `verify_hmac()` (teams_normalizer.py:50-77), Slack has `verify_signature()` with replay protection (slack_normalizer.py:75-134), Telegram has shared-secret token (ott_gateway.py:83-100). Zalo has NONE.

**CTO P0-1 applied**: Explicit `x_zalo_oa_signature` header parameter in `receive_webhook()` function signature.
**CTO P1-2 applied**: `_ZALO_APP_SECRET = os.getenv(...)` in ott_gateway.py (matches existing Slack/Telegram pattern).

| File | Change | LOC |
|------|--------|-----|
| `backend/app/services/agent_bridge/zalo_normalizer.py` | Add `verify_hmac(request_body: bytes, mac_header: str, app_secret: str) -> bool`. HMAC-SHA256 with `hmac.compare_digest()` (constant-time). No replay protection (Zalo API lacks timestamp header — documented limitation). | ~35 |
| `backend/app/api/routes/ott_gateway.py` | 1) Add `_ZALO_APP_SECRET = os.getenv("ZALO_APP_SECRET", "")` (line ~51, after `_SLACK_SIGNING_SECRET`). 2) Add `_verify_zalo_signature()` helper (mirrors `_verify_slack_signature` pattern). 3) Add `x_zalo_oa_signature: str | None = Header(default=None)` to `receive_webhook()` params. 4) Add `elif channel == "zalo":` verification block after Slack block (after line 203). | ~25 |

**Day 2 Verification**:
- `ruff check backend/app/services/agent_bridge/zalo_normalizer.py` → 0 errors
- Unit test: `verify_hmac(body, valid_mac, secret)` → True
- Unit test: `verify_hmac(body, "tampered", secret)` → False
- Unit test: `verify_hmac(body, mac, "")` → False
- Integration: `OTT_HMAC_ENABLED=true` + wrong Zalo signature → HTTP 403

---

### Day 3: Docker Multi-Stage Build + sdlcctl CI (P0 — Infra)

**Part A: Docker Multi-Stage Build**

| File | Change | LOC |
|------|--------|-----|
| `backend/Dockerfile` | 2-stage rewrite. Stage 1 `builder`: python:3.11-slim, build-essential, libpq-dev, `pip install --prefix=/install -r requirements/core.txt`, semgrep. Stage 2 `runtime`: python:3.11-slim, `COPY --from=builder /install /usr/local`, curl + libpq5 only, non-root user, EXPOSE 8300, healthcheck. | ~30 |
| `backend/requirements-docker.txt` | Redirect to `-r requirements/core.txt` (backward compat per Sprint 191 D-191-04 pattern) | ~3 |

**Rationale**: `enterprise.txt` includes torch (~2.7GB), transformers, chromadb, Google Cloud SDKs. `core.txt` has ~116 lines of production deps. Target: <600MB (vs ~2GB+ current).

**Part B: sdlcctl Governance CI Step**

| File | Change | LOC |
|------|--------|-----|
| `.github/workflows/test.yml` | New `sdlcctl-governance-tests` job: checkout → Python 3.11 → `pip install -r requirements/core.txt` → `pip install -e sdlcctl/` → `pytest tests/unit/test_command_registry.py -v` | ~40 |

**Resolves**: Sprint 191 skip at `test_command_registry.py:115` — sdlcctl now installed in CI.

**Day 3 Verification**:
- `docker build -t sdlc-192-test backend/` → succeeds
- Docker image size: `docker images sdlc-192-test` → <600MB
- sdlcctl governance tests: 15/15 pass, 0 skipped

---

### Day 4: Semgrep SAST CI Step (P0 — Security Gate)

| File | Change | LOC |
|------|--------|-----|
| `.github/workflows/test.yml` | New `sast-scan` job: install Semgrep → scan `backend/app/` with `policy-packs/semgrep/ai-security.yml` + `owasp-python.yml` → `--severity ERROR` (block on ERROR only) → SARIF output → upload to GitHub Security tab. Cache key: `requirements/core.txt` (CTO P3-2). | ~25 |

**Context**: Semgrep rules exist at `backend/policy-packs/semgrep/` (25.8KB) but are not in CI pipeline.

**Day 4 Verification**:
- `semgrep --config backend/policy-packs/semgrep/ --severity ERROR backend/app/` → 0 ERROR findings
- SARIF file generated and parseable

---

### Day 5-6: Compliance Audit PDF Export (P1 — EP-08 P2)

**Goal**: Enable `@pm compliance report` → audit PDF generation.

**Pattern source**: `backend/app/services/compliance/soc2_pack_service.py` (reportlab ImportError guard, PDF generation, dataclass result).

**New Files**:

| File | LOC | Purpose |
|------|-----|---------|
| `backend/app/services/compliance_export_service.py` | ~180 | `ComplianceExportService.generate_audit_pdf(project_id, from_date, to_date)` → `ComplianceExportResult(pdf_bytes, total_events, summary)`. Module-level `try/except ImportError` for reportlab (CLAUDE.md §5 Optional Dependency Guard). Collects from: `audit_logs`, `gate_approvals`, `gate_evidence`, `projects`. PDF structure: cover page + gate timeline + evidence summary + audit detail table. SHA256 hash in footer (tamper-evidence). |
| `backend/app/api/routes/compliance_export.py` | ~70 | `POST /api/v1/compliance/export/{project_id}` → `Response(media_type="application/pdf")`. Request: `ComplianceExportRequest(from_date, to_date, format="pdf")`. Requires auth + project membership. Logs `action="compliance_export"` to audit_logs. |

**Modified Files**:

| File | Change | LOC |
|------|--------|-----|
| `backend/app/main.py` | Register `compliance_export.router` | ~3 |

**Note**: CTO P2-1 confirmed `tier_gate.py` parent prefix `/api/v1/compliance` already covers `/api/v1/compliance/export`. No tier_gate.py change needed.

**Day 5-6 Verification**:
- `POST /api/v1/compliance/export/1` with valid JWT → PDF bytes >0
- PDF opens in viewer, contains gate timeline + evidence summary
- `audit_logs` has `action="compliance_export"` entry
- Without reportlab installed → module loads → `generate_audit_pdf()` raises `RuntimeError` with install instructions

---

### Day 7: Break-Glass + Dashboard Read-Only + Acceptance Tests (P1-P2 + P0)

**Part A: Break-Glass Web Approve (P1)**

| File | Change | LOC |
|------|--------|-----|
| `backend/app/api/routes/gates.py` | New `POST /{gate_id}/break-glass-approve`. Feature flag `BREAK_GLASS_WEB_ENABLED` (default `false` → 404 when off). Requires admin/owner role (CTO P2-2: verify exact role strings in `models/user.py`). Required fields: `reason` (min 50 chars), `incident_ticket`, `severity` (P0/P1). State: SUBMITTED → APPROVED. Audit: `action="break_glass_approve"`, `source="break_glass_web"`. Rate limit: Redis `break_glass:{user_id}` count/week, reject >2. | ~80 |
| `backend/app/core/config.py` | Add `BREAK_GLASS_WEB_ENABLED: bool = False` | ~2 |

**Part B: Dashboard Read-Only Enforcement (P2)**

| File | Change | LOC |
|------|--------|-----|
| `backend/app/middleware/conversation_first_guard.py` | Extend `ADMIN_WRITE_PATHS` with `/api/v1/gates`, `/api/v1/evidence`, `/api/v1/projects`. Non-admin POST/PUT/PATCH/DELETE → 403 "Use OTT or CLI". GET (read) still open to all. Admin/owner pass-through. | ~10 |

**Part C: Acceptance Tests (P0)**

**New File**: `backend/tests/integration/test_sprint192_acceptance.py` (~200 LOC)

| # | Test | Pass Criteria |
|---|------|---------------|
| 1 | Zalo HMAC valid signature | `verify_hmac(body, valid_mac, secret)` → True |
| 2 | Zalo HMAC invalid signature | `verify_hmac(body, "tampered", secret)` → False |
| 3 | Zalo HMAC empty secret | `verify_hmac(body, mac, "")` → False |
| 4 | Dockerfile multi-stage structure | File contains `AS builder` and `COPY --from=builder` (CTO P2-3) |
| 5 | sdlcctl governance importable | `from sdlcctl.commands.governance import app` succeeds |
| 6 | Compliance export PDF | `generate_audit_pdf()` returns bytes >0 |
| 7 | Break-glass feature flag OFF | POST → 404 |
| 8 | Break-glass feature flag ON + admin | POST → 200, audit logged |
| 9 | Dashboard read-only guard | Non-admin POST /gates → 403 |
| 10 | Frontend build clean | `npm run build` → 0 errors (no dead imports) |

**Day 7 Verification**:
- 10/10 acceptance tests pass
- Sprint 191 regression: all pass
- `ruff check backend/` → 0 errors on all Sprint 192 files

---

### Day 8: Sprint Close + CTO Review

1. Create `docs/04-build/02-Sprint-Plans/SPRINT-192-CLOSE.md`
2. Update `CLAUDE.md` — Sprint 192 changelog, current sprint ref
3. Update EP-08 status → P2 COMPLETE
4. CTO review focus areas:
   - Zalo HMAC implementation (security review)
   - Break-glass approve endpoint (security + audit review)
   - Dashboard read-only guard expansion (scope review)
   - Docker multi-stage build (DevOps review)
   - Frontend cleanup completeness (no dead imports remaining)
5. Full test suite: `python -m pytest backend/tests/ -v`
6. Frontend build: `cd frontend && npm run build`
7. Semgrep scan: `semgrep --config backend/policy-packs/semgrep/ backend/app/`
8. Docker build: `docker build -t sdlc-192 backend/`

---

## New Files

| File | LOC | Purpose |
|------|-----|---------|
| `backend/app/services/compliance_export_service.py` | ~180 | Compliance audit PDF generation (reportlab, ImportError guarded) |
| `backend/app/api/routes/compliance_export.py` | ~70 | REST endpoint for compliance PDF export |
| `backend/tests/integration/test_sprint192_acceptance.py` | ~200 | Sprint 192 acceptance tests (10 tests) |

## Modified Files

| File | Change | LOC |
|------|--------|-----|
| `frontend/src/app/pilot/page.tsx` | Replace with `ConversationFirstFallback` | ~-180 |
| `frontend/src/lib/api.ts` | Remove ~80 dead function exports | ~-600 |
| `frontend/src/app/app/compliance/layout.tsx` | Disable NIST tab | ~3 |
| `frontend/src/messages/en.json` | Remove orphaned i18n keys | ~-10 |
| `frontend/src/messages/vi.json` | Remove orphaned i18n keys | ~-10 |
| `backend/app/services/agent_bridge/zalo_normalizer.py` | Add `verify_hmac()` | ~35 |
| `backend/app/api/routes/ott_gateway.py` | `_ZALO_APP_SECRET` + verification + header param | ~25 |
| `backend/Dockerfile` | Multi-stage build rewrite | ~30 |
| `backend/requirements-docker.txt` | Redirect to `requirements/core.txt` | ~3 |
| `.github/workflows/test.yml` | Add sdlcctl CI + Semgrep SAST jobs | ~65 |
| `backend/app/api/routes/gates.py` | Add `break-glass-approve` endpoint | ~80 |
| `backend/app/core/config.py` | Add `BREAK_GLASS_WEB_ENABLED: bool = False` | ~2 |
| `backend/app/middleware/conversation_first_guard.py` | Extend `ADMIN_WRITE_PATHS` | ~10 |
| `backend/app/main.py` | Register `compliance_export.router` | ~3 |

## Deleted Files

| File | LOC | Reason |
|------|-----|--------|
| `frontend/src/hooks/useCouncil.ts` | 136 | Orphaned — AI Council deleted Sprint 190 |
| `frontend/src/hooks/useLearnings.ts` | 519 | Unreachable — page shows ConversationFirstFallback |
| `frontend/src/hooks/useSpecConverter.ts` | 254 | Unreachable — page shows ConversationFirstFallback |
| `frontend/src/hooks/usePilotSignup.ts` | 189 | Orphaned — pilot backend deleted Sprint 190 |
| `frontend/src/components/pilot/PilotSignupForm.tsx` | ~100 | Dead — pilot form submits to deleted endpoint |
| `frontend/src/components/pilot/PilotBenefits.tsx` | ~80 | Dead — pilot page replaced with fallback |
| `frontend/src/components/pilot/PilotFAQ.tsx` | ~60 | Dead — pilot page replaced with fallback |
| `frontend/src/components/pilot/index.ts` | ~10 | Dead — re-exports deleted components |
| `frontend/__tests__/**/nist*` (4 files) | ~300 | Test deleted NIST backend endpoints |
| `frontend/__tests__/**/spec-converter*` (7 files) | ~400 | Test deleted spec converter |
| `frontend/__tests__/**/sprint171-pilot-landing.spec.ts` | ~100 | Tests mock deleted pilot endpoint |
| `frontend/src/app/app/sop/[id]/**` (if backend deleted) | ~150 | SOP detail pages calling deleted endpoints |

---

## Risk Register

| Risk | Prob | Impact | Mitigation | Day |
|------|------|--------|------------|-----|
| Zalo OA webhook lacks HMAC header in actual API | MEDIUM | HIGH | Day 2 starts with Zalo OA API doc verification. If no HMAC header, document limitation + implement IP allowlist alternative. | 2 |
| api.ts dead export removal breaks active components | LOW | HIGH | `grep -r` for each removed function before deletion. `npm run build` after each batch to catch import errors. | 1 |
| Docker multi-stage build breaks enterprise deployment | LOW | HIGH | Keep original as `Dockerfile.full` for enterprise tier. Test both builds. | 3 |
| sdlcctl editable install fails in CI (pkg structure) | LOW | MEDIUM | Verify `pip install -e sdlcctl/` locally before CI change. | 3 |
| Semgrep false positives block CI | MEDIUM | LOW | `--severity ERROR` only (not warnings). `--exclude` for known patterns. | 4 |
| reportlab missing in test env for compliance export | LOW | LOW | ImportError guard (`soc2_pack_service.py` pattern). Tests mock reportlab. | 5 |
| Break-glass approve opens security hole | LOW | CRITICAL | Feature flag OFF default. Admin role + incident ticket + rate limit. Full audit trail. | 7 |
| SOP detail pages have preserved read-only backend | MEDIUM | LOW | Verify backend first. If endpoints exist, keep pages. If deleted, replace with fallback. | 1 |

---

## Verification Criteria

| # | Criterion | Target | Day |
|---|-----------|--------|-----|
| 1 | `/pilot` page shows fallback (NOT broken form) | ConversationFirstFallback renders | 1 |
| 2 | `npm run build` → 0 errors after dead code removal | Clean build | 1 |
| 3 | No dead hook imports in frontend codebase | `grep` returns 0 hits | 1 |
| 4 | Zalo HMAC unit tests | 3/3 pass (valid, invalid, empty) | 2 |
| 5 | Zalo webhook wrong sig + HMAC enabled | HTTP 403 | 2 |
| 6 | Docker image size (multi-stage) | <600MB (vs ~2GB+ current) | 3 |
| 7 | sdlcctl governance tests in CI | 15/15 pass, 0 skipped | 3 |
| 8 | Semgrep CI scan | 0 ERROR-level findings | 4 |
| 9 | Compliance PDF export | Returns valid PDF >0 bytes | 6 |
| 10 | Break-glass flag OFF | POST → 404 | 7 |
| 11 | Break-glass flag ON + admin | POST → 200, audit logged | 7 |
| 12 | Break-glass rate limit | 3rd/week → 429 | 7 |
| 13 | Dashboard guard non-admin POST /gates | HTTP 403 | 7 |
| 14 | Sprint 192 acceptance tests | 10/10 pass | 7 |
| 15 | Sprint 191 regression | All pass | 8 |
| 16 | `ruff check backend/` | 0 errors | 8 |
| 17 | CTO review | APPROVED | 8 |

---

## Definition of Done

- [ ] /pilot page replaced with ConversationFirstFallback (P0 user-facing fix)
- [ ] api.ts dead exports removed (~80 functions, ~600 LOC)
- [ ] 4 dead hook files deleted (~1,098 LOC)
- [ ] NIST tab disabled in compliance layout
- [ ] 13+ stale frontend test files deleted
- [ ] Orphaned i18n keys removed from en.json/vi.json
- [ ] `npm run build` → 0 errors after cleanup
- [ ] Zalo HMAC verification implemented and wired into OTT gateway
- [ ] Docker multi-stage build reduces image to <600MB
- [ ] sdlcctl governance tests run in CI (0 skipped)
- [ ] Semgrep SAST scan runs in CI (0 ERROR findings)
- [ ] Compliance audit PDF export endpoint functional (ENTERPRISE tier)
- [ ] Break-glass web approve endpoint functional (feature-flagged OFF default)
- [ ] Dashboard read-only guard extended to gate/evidence/project mutations
- [ ] 10/10 acceptance tests pass
- [ ] Sprint 191 acceptance tests still pass (no regression)
- [ ] SPRINT-192-CLOSE.md created
- [ ] CLAUDE.md updated (Sprint 192 changelog)
- [ ] EP-08 P2 status updated
- [ ] CTO review APPROVED

---

## Scope (WA-3 Compliance)

### In-Scope

**Track A (Frontend Cleanup)**:
- /pilot page ConversationFirstFallback replacement
- api.ts dead export removal (~80 functions)
- Dead hook file deletion (4 files, ~1,098 LOC)
- NIST tab disable in compliance layout
- Stale frontend test file deletion (13+ files)
- SOP detail page verification and fallback (if needed)
- Orphaned i18n key removal

**Track B (Security + Compliance)**:
- Zalo HMAC-SHA256 webhook signature verification
- Docker multi-stage build using `requirements/core.txt`
- sdlcctl governance tests in CI (no longer skipped)
- Semgrep SAST CI step with SARIF upload
- Compliance audit PDF export (`POST /api/v1/compliance/export/{project_id}`)
- Break-glass web approve (feature-flagged, admin-only, rate-limited)
- Dashboard read-only enforcement for gate/evidence/project mutations

### Out-of-Scope
- Zalo replay protection (Zalo API lacks timestamp header)
- Enterprise-specific Dockerfile variant (separate concern)
- Frontend UI for break-glass button (backend-only this sprint)
- Frontend UI for read-only dashboard indicators (middleware enforcement only)
- SASE service refactor (Sprint 191 rec #4 — independent, not EP-08)
- New chat commands beyond existing 5 (registry capped at 10, D-191-01)
- Frontend pilot component refactor (delete, not refactor)

### Deferred to Sprint 193+
- Frontend break-glass UI component (red button per break_glass.yaml)
- Frontend read-only visual indicators (greyed-out action buttons)
- SASE service refactor/split
- Zalo IP allowlist as secondary defense
- Enterprise Dockerfile variant (`Dockerfile.enterprise` with `enterprise.txt`)

---

## Handoff to @dev Team

**Execution order**: Day 1 (Track A frontend) → Days 2-7 (Track B backend) → Day 8 (close)

**Day 1 can be parallelized**:
- Developer A: api.ts cleanup + hook deletion + i18n keys
- Developer B: /pilot page fix + NIST tab + SOP verification + test cleanup

**Days 2-7 are sequential** — each day builds on the previous.

**Critical path**: Day 2 (Zalo HMAC) blocks Day 7 (acceptance tests). Day 5-6 (compliance export) blocks Day 7 (acceptance test #6).

---

**Sprint 192 Status**: APPROVED — Ready for @dev team execution
**GO/NO-GO**: GO
