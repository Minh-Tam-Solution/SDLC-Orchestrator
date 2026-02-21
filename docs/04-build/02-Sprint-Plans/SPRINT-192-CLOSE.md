# Sprint 192 Close — Enterprise Hardening + Security Parity

**Sprint**: 192
**Duration**: 8 working days
**Status**: COMPLETE
**Framework**: SDLC 6.1.0
**Preceded by**: Sprint 191 (Unified Command Registry, CTO APPROVED)
**Epic**: EP-08 Enterprise Hardening

---

## Deliverables Summary

| # | Deliverable | Status | LOC |
|---|-------------|--------|-----|
| 1 | Frontend/Backend Mismatch Cleanup (Day 1) | DONE | ~-25,953 (removal) |
| 2 | Zalo SHA256 Signature Verification (Day 2) | DONE | ~80 |
| 3 | Docker Multi-Stage Build (Day 3A) | DONE | ~65 (rewrite) |
| 4 | sdlcctl CI Step in test.yml (Day 3B) | DONE | ~40 |
| 5 | Semgrep SAST CI Step (Day 4) | DONE | ~30 |
| 6 | Compliance Audit PDF Export — Service (Day 5-6) | DONE | ~478 |
| 7 | Compliance Audit PDF Export — Route (Day 5-6) | DONE | ~199 |
| 8 | Break-Glass Emergency Approve (Day 7A) | DONE | ~160 |
| 9 | Dashboard Read-Only Guard Expansion (Day 7B) | DONE | ~10 |
| 10 | Sprint 192 Acceptance Tests (Day 7C) | DONE | ~290 |

**Net code change**: ~+1,352 LOC new, ~-25,953 LOC removed (frontend cleanup)

---

## Verification Criteria

| # | Criterion | Result |
|---|-----------|--------|
| 1 | Zalo SHA256 valid signature → True | PASS — constant-time compare via `hmac.compare_digest` |
| 2 | Zalo SHA256 invalid signature → False | PASS — tampered hash rejected |
| 3 | Zalo SHA256 empty secret → False | PASS — fail-fast guard |
| 4 | Dockerfile has `AS builder` + `AS runtime` stages | PASS — 2-stage multi-stage build |
| 5 | Dockerfile `COPY --from=builder` (no build tools in runtime) | PASS — only `curl` + `libpq5` in runtime |
| 6 | Dockerfile uses `requirements/core.txt` | PASS — Sprint 191 split layout |
| 7 | sdlcctl governance tests in CI | PASS — new `sdlcctl-governance-tests` job in test.yml |
| 8 | Semgrep SAST scan in CI | PASS — new `sast-scan` job in test.yml |
| 9 | ComplianceExportService importable | PASS — reportlab ImportError guard pattern |
| 10 | Compliance export route registered | PASS — `POST /api/v1/compliance/export/{project_id}` |
| 11 | Break-glass feature flag default OFF | PASS — `BREAK_GLASS_WEB_ENABLED=false` |
| 12 | Break-glass route registered in gates router | PASS — `/{gate_id}/break-glass-approve` |
| 13 | Dashboard read-only paths include governance | PASS — gates, evidence, projects added |
| 14 | ConversationFirstGuard blocks non-admin POST | PASS — returns 403 JSON with alternatives |
| 15 | ConversationFirstGuard passes GET always | PASS — read-only access for all users |
| 16 | `ruff check` on all Sprint 192 files | PASS — 0 errors |
| 17 | Acceptance tests | PASS — 25/25 passed |

**Total test results**: 25 passed, 0 skipped, 0 failed (acceptance suite)

---

## Key Decisions

### D-192-01: Zalo uses SHA256 (not HMAC-SHA256)
Zalo OA computes `sha256(app_id + body + timestamp + oa_secret_key)` — a plain hash, not HMAC. We still use `hmac.compare_digest` for constant-time comparison (PA-40 timing oracle prevention). No replay protection available (documented limitation).

### D-192-02: Break-glass is feature-flagged OFF by default
`BREAK_GLASS_WEB_ENABLED=false` in config.py. Requires explicit opt-in via environment variable. Rate limited to 2 per user per week via Redis. Only CEO/CTO/admin/owner roles permitted.

### D-192-03: Dashboard read-only via ADMIN_WRITE_PATHS expansion
Extended `ConversationFirstGuard.ADMIN_WRITE_PATHS` with `/api/v1/gates`, `/api/v1/evidence`, `/api/v1/projects`. Non-admin users get 403 with OTT/CLI alternatives message. GET/HEAD/OPTIONS always pass through.

### D-192-04: Compliance PDF uses reportlab ImportError guard
Following CLAUDE.md §5 Optional Dependency Guard pattern (same as `soc2_pack_service.py`). Service is importable even without reportlab — raises `RuntimeError` with actionable install message at call time.

### D-192-05: Docker multi-stage eliminates build tools from runtime
Stage 1 (builder) has `build-essential`, `pkg-config`, `libpq-dev`. Stage 2 (runtime) has only `curl` + `libpq5`. Python packages compiled in builder and copied via `COPY --from=builder /install /usr/local`. Non-root user enforced (CWE-250).

---

## Files Changed

### New Files
| File | LOC | Purpose |
|------|-----|---------|
| `backend/app/services/compliance_export_service.py` | ~478 | Compliance audit PDF generation service |
| `backend/app/api/routes/compliance_export.py` | ~199 | POST /api/v1/compliance/export/{project_id} |
| `backend/tests/integration/test_sprint192_acceptance.py` | ~290 | Sprint 192 acceptance tests (25 tests) |

### Modified Files
| File | Change |
|------|--------|
| `backend/Dockerfile` | Rewritten as 2-stage multi-stage build |
| `backend/requirements-docker.txt` | Redirect to `requirements/core.txt` |
| `.github/workflows/test.yml` | Added sdlcctl-governance-tests + sast-scan jobs |
| `backend/app/services/agent_bridge/zalo_normalizer.py` | Added `verify_signature()` (SHA256) |
| `backend/app/api/routes/ott_gateway.py` | Wired Zalo signature verification |
| `backend/app/api/routes/gates.py` | Added break-glass approve endpoint |
| `backend/app/core/config.py` | Added `BREAK_GLASS_WEB_ENABLED` flag |
| `backend/app/middleware/conversation_first_guard.py` | Extended ADMIN_WRITE_PATHS (gates, evidence, projects) |
| `backend/app/main.py` | Registered compliance_export router |
| `backend/tests/unit/test_zalo_normalizer.py` | 13 tests for signature verification |

### Deleted Files
| File | Reason |
|------|--------|
| ~25,953 LOC frontend dead imports/components | Track A cleanup (Day 1) |

---

## Sprint 191 Recommendations Addressed

| Recommendation | Outcome |
|----------------|---------|
| sdlcctl governance end-to-end test | DONE — CI job added to test.yml |
| Zalo HMAC signature verification | DONE — SHA256 verification with 13 unit tests |
| Docker image optimization (multi-stage) | DONE — 2-stage build, runtime-only deps |
| SASE service refactor | DEFERRED — not in Sprint 192 scope |

---

## Risks Mitigated

| Risk | Outcome |
|------|---------|
| Zalo SHA256 timing oracle | Mitigated — `hmac.compare_digest` for constant-time comparison |
| Break-glass abuse | Mitigated — feature flag OFF, rate limit (2/week), role restriction, audit logging |
| Dashboard over-restriction | Mitigated — GET/HEAD/OPTIONS always pass; fail-open on missing role |
| Frontend cleanup breaks existing features | Mitigated — no functional code removed, only dead imports |
| reportlab missing in test env | Mitigated — ImportError guard, service importable without reportlab |

---

## Sprint Metrics

| Metric | Value |
|--------|-------|
| Duration | 8 working days |
| Deliverables planned | 10 |
| Deliverables completed | 10 (100%) |
| LOC added | ~1,352 |
| LOC removed | ~25,953 |
| New tests written | 38 (13 Zalo unit + 25 acceptance) |
| P0/P1 bugs | 0 |
| CTO Reviews | 3 (Day 1: 9.3/10, Day 2: 9.4/10, Day 3: 9.2/10) |

---

## Sprint 193 Recommendations

1. **Compliance PDF end-to-end test** — current tests verify import/structure; add DB-backed test with real audit_logs data.
2. **Break-glass monitoring dashboard** — add Grafana panel tracking break-glass usage frequency per user/org.
3. **ConversationFirstGuard role alignment** — middleware uses "admin"/"owner" strings but user model has 13 roles. Consider unifying role vocabulary (CTO P2-2 follow-up).
4. **Docker image size measurement** — build and measure final image size against <600MB target.
5. **Semgrep custom rule expansion** — current AI-security + OWASP base. Add enterprise compliance rules for SOC2/ISO27001.

---

**Sprint 192 Status**: COMPLETE
**Ready for CTO Review**: YES
**GO/NO-GO for Sprint 193**: Recommend GO
