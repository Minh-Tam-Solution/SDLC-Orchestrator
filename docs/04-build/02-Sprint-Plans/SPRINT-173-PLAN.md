# Sprint 173: "Sharpen, Don't Amputate" — Complete the Governance Loop + Framework Cleanup

**Sprint Duration**: Feb 17 - Mar 7, 2026 (14 working days)
**Status**: PLANNED
**Phase**: Phase 4 - BUILD (Governance Loop Completion)
**Framework**: SDLC 6.0.5 (7-Pillar + Section 7 Quality Assurance)
**CTO Approval**: Approved v4 FINAL (Feb 15, 2026) — All reviewers unanimous
**ADR**: ADR-053-Governance-Loop-State-Machine.md
**Contract**: CONTRACT-GOVERNANCE-LOOP.md

---

## Sprint Goal

**Complete the governance loop** across all 3 client interfaces (Web, CLI, Extension) so that gate evaluation, evidence submission, approval, and rejection work identically everywhere. Simplify overengineered modules via Strangler Fig pattern. Freeze non-core code. Clean up SDLC Enterprise Framework docs.

**CTO Directive**: "The product doesn't need to be smaller. It needs to be COMPLETE."

**Success Criteria**:
- All 3 clients (Web, CLI, Extension) can perform full gate lifecycle: evaluate → submit → approve/reject
- `compute_gate_actions()` is the SSOT for all permission checks (no client-side permission logic)
- Evidence contract enforced: server-side SHA256 re-verification + `criteria_snapshot_id` binding
- Redis-based idempotency on all mutation endpoints
- Context Authority V1 absorbed into V2 (golden tests verified)
- Governance Mode Enforcer consolidated (Strategy pattern)
- Non-core modules frozen with CI enforcement
- Framework docs cleaned up (Code Review consolidated, AI-GOVERNANCE expanded)

---

## Scope

### In Scope

| Phase | Deliverable | Track |
|-------|-------------|-------|
| Pre-Phase | Gate state machine, `compute_gate_actions()`, DB migration, idempotency middleware, evidence contract | A (Engineers) |
| Phase 1.1 | CLI gate commands (7 commands in `gate.py`) | A |
| Phase 1.2 | CLI evidence submit command | A |
| Phase 1.3 | Extension gate approval + evidence submission commands | A |
| Phase 2.1 | Context Authority V1→V2 merge (Strangler Fig) | A |
| Phase 2.2 | Governance Mode Enforcer consolidation (Strategy pattern) | A |
| Phase 3 | Freeze non-core modules (headers + CI enforcement) | A |
| Phase 4 | Delete HIGH confidence dead code (~838 LOC) | A |
| Phase 5.0 | Framework SPEC moratorium | B (Tech Lead) |
| Phase 5.1 | Framework AI-Tools freeze | B |
| Phase 5.2 | Code Review doc consolidation (3 guides → 1 SSOT) | B |
| Phase 5.3 | AI-GOVERNANCE expansion (Decision Matrix + Metrics) | B |
| Phase 5.4 | Stale version ref updates (5.x → 6.0.5) | B |
| Phase 5.5 | .gitattributes for archive exclusion | B |

### Out of Scope (Deferred to Sprint 174)

| Item | Reason |
|------|--------|
| Phase 2.3: Codegen template consolidation | CTO Mod 3 — prevent sprint overload |
| Phase 2.4: Dashboard consolidation | CTO Mod 3 — needs folder grouping design first |
| Dogfooding pages deletion (~1,600 LOC) | MEDIUM confidence — needs verification checklist |
| Template merge leftovers (~400 LOC) | Depends on Phase 2.3 completion |
| Training Materials expansion (08-Training-Materials) | P3 — Post-launch (Sprint 175+) |

---

## Execution Model — Dual Track

**Track A** (Backend/Extension Engineers): Phase Pre-Phase through Phase 4. 100% code. No Framework .md files.
**Track B** (Tech Lead/PM/Architect): Phase 5. Framework docs cleanup. Runs in parallel.

Benefit: No context switching. Developers stay in flow state.

---

## Sprint Backlog

### Day 1: Pre-Phase — Contract + Pre-Flight + State Machine

**Owner**: Backend Lead
**Priority**: P0 (blocking for all subsequent work)

#### Task 0.1: Pre-Flight Verification (1 hour)

Verify before coding:
- [ ] Gate model `status` field supports new states (EVALUATED, EVALUATED_STALE, SUBMITTED) — if not, migration needed
- [ ] Evidence model has fields for `sha256_server`, `criteria_snapshot_id`, `source` — if not, migration needed
- [ ] Redis connection verified (port 6395, `REDIS_PASSWORD` in .env, pool size sufficient)
- [ ] Auth scopes `governance:write` and `governance:approve` exist in JWT token generation

**Outcome**: Pre-flight report. If DB migration needed, add 0.5 day to Day 1.

#### Task 0.2: Alembic Migration (1-2 hours)

```
File: backend/alembic/versions/XXX_sprint_173_gate_state_machine.py
```

- Rename `PENDING_APPROVAL` → `SUBMITTED` in gates table
- Remove `IN_PROGRESS` (→ `EVALUATED`)
- Add `evaluated_at`, `exit_criteria_version` columns to gates
- Rename `sha256_hash` → `sha256_client` in gate_evidence
- Add `sha256_server`, `criteria_snapshot_id`, `source` columns to gate_evidence
- Add indexes

**Acceptance Criteria**:
- [ ] Migration runs without errors on dev database
- [ ] Rollback migration works
- [ ] Existing gate data preserved (status values remapped)

#### Task 0.3: `compute_gate_actions()` + State Machine Guards (2 hours)

```
File: backend/app/services/gate_service.py
```

- Implement `compute_gate_actions(gate, user)` function
- Refactor `approve_gate()` and `reject_gate()` to delegate to `compute_gate_actions()`
- Add transition guard validation

**Acceptance Criteria**:
- [ ] `compute_gate_actions()` returns correct actions for all 6 states
- [ ] Invalid transitions return 409 Conflict
- [ ] Unit tests for all state transitions

#### Task 0.4: New API Endpoints (2 hours)

```
File: backend/app/api/routes/gates.py
```

- Add `GET /gates/{id}/actions` endpoint
- Add `POST /gates/{id}/reject` endpoint (separate from approve — CTO Mod 1)
- Add `POST /gates/{id}/evaluate` endpoint
- Update `POST /gates/{id}/submit` to enforce `missing_evidence = []`
- All endpoints use `compute_gate_actions()` for permission checks

**Acceptance Criteria**:
- [ ] `/actions` returns correct JSON schema per contract
- [ ] `/reject` separate from `/approve`
- [ ] `/submit` blocked when evidence missing (422)
- [ ] All endpoints return proper error codes (403, 409, 422)

#### Task 0.5: Idempotency Middleware (1 hour)

```
File: backend/app/middleware/idempotency.py
```

- Redis-based idempotency middleware
- Key: `idempotency:{user_id}:{endpoint}:{gate_id}:{idempotency_key}`
- TTL: 86400 seconds (24 hours)
- Stores and replays full response body
- Graceful degradation if Redis unavailable

**Acceptance Criteria**:
- [ ] Duplicate requests return stored response
- [ ] Different users with same key execute independently
- [ ] Redis timeout doesn't block request (graceful degradation)

#### Task 0.6: Evidence Contract Enforcement (1 hour)

```
File: backend/app/api/routes/evidence.py
```

- Server-side SHA256 re-computation on upload
- Compare `sha256_client` vs `sha256_server` — reject on mismatch
- Handle `source=other` (no `sha256_client`) — log warning
- Store `criteria_snapshot_id` binding
- If gate status is `EVALUATED` → set to `EVALUATED_STALE`

**Acceptance Criteria**:
- [ ] Hash mismatch returns 400
- [ ] Untrusted source logs warning but proceeds
- [ ] Evidence upload while EVALUATED → EVALUATED_STALE
- [ ] `criteria_snapshot_id` stored and indexed

---

### Day 1 (Track B): Framework Freeze PR

**Owner**: Tech Lead
**Priority**: P0

- Add SPEC moratorium notice to `05-Templates-Tools/01-Specification-Standard/README.md`
- Add AI-Tools freeze notice to `05-Templates-Tools/02-AI-Tools/README.md`
- Create `.gitattributes` for archive exclusion
- Create PR: `sprint-173-framework-cleanup` branch → main

**Acceptance Criteria**:
- [ ] Moratorium notice merged to prevent new SPECs during sprint
- [ ] AI-Tools freeze notice merged
- [ ] `.gitattributes` excludes 10-Archive/ from diffs

---

### Day 1 Checkpoint (CTO Requirement)

After Day 1, Engineering reports:
- [ ] Model fields verified (or migration created and applied)
- [ ] Redis connection confirmed
- [ ] State machine guards implemented
- [ ] `compute_gate_actions()` function working
- [ ] Framework freeze PR merged

**GO / NO-GO** for Phase 1 based on Day 1 checkpoint.

---

### Day 2-3: Phase 1.1 — CLI Gate Commands

**Owner**: Backend Team
**Priority**: P0

```
Create: backend/sdlcctl/sdlcctl/commands/gate.py
Edit: backend/sdlcctl/sdlcctl/cli.py (register gate sub-app)
```

7 commands using Typer sub-app pattern:

| Command | Endpoint | Notes |
|---------|----------|-------|
| `sdlcctl gate list` | `GET /gates?project_id=X` | Rich table |
| `sdlcctl gate show <id>` | `GET /gates/{id}` | Details + criteria |
| `sdlcctl gate evaluate <id>` | `POST /evaluate` | Evaluate criteria |
| `sdlcctl gate submit <id>` | `POST /submit` | Submit for approval |
| `sdlcctl gate approve <id> -c "..."` | `POST /approve` | Prompt if no comment |
| `sdlcctl gate reject <id> -c "..."` | `POST /reject` | `click.edit()` for long comments |
| `sdlcctl gate status` | `GET /gates` | Compact status table |

**Acceptance Criteria**:
- [ ] All 7 commands implemented with Rich Console output
- [ ] Pre-action check via `/actions` endpoint on all mutations
- [ ] `X-Idempotency-Key` header on all mutations
- [ ] 403 handling with clear scope message
- [ ] `httpx` timeout 120s for evidence, 30s for others
- [ ] `click.edit()` opens `$EDITOR` for reject without `-c`

---

### Day 4: Phase 1.2 — CLI Evidence Submit

**Owner**: Backend Team
**Priority**: P0

```
Edit: backend/sdlcctl/sdlcctl/commands/evidence.py (add submit command)
```

Command: `sdlcctl evidence submit --gate <id> --type <type> --file <path> [--file <path2>]`

Evidence types: `test-results`, `api-docs`, `design-doc`, `security-scan`, `code-review`, `manual`

**Acceptance Criteria**:
- [ ] Client-side SHA256 computed before upload
- [ ] Multipart upload with metadata (hash, size, mime, source=`cli`)
- [ ] `X-Idempotency-Key` header
- [ ] `httpx` timeout 120s
- [ ] Multiple `--file` flags supported
- [ ] Progress indicator for large files

---

### Day 5-7: Phase 1.3 — Extension Gate Actions + Evidence

**Owner**: Extension Team
**Priority**: P0

```
Create: vscode-extension/src/commands/gateApprovalCommand.ts
Create: vscode-extension/src/commands/evidenceSubmissionCommand.ts
Edit: vscode-extension/src/services/apiClient.ts (4 new methods)
Edit: vscode-extension/src/extension.ts (register commands)
Edit: vscode-extension/package.json (commands + context menus)
```

4 new apiClient methods:
- `getGateActions(gateId)` — `GET /gates/{id}/actions`
- `approveGate(gateId, comment)` — `POST /gates/{id}/approve`
- `rejectGate(gateId, comment)` — `POST /gates/{id}/reject`
- `submitEvidence(gateId, type, files)` — `POST /gates/{id}/evidence`

3 new commands in `package.json`:
- `sdlc.approveGate` (thumbsup icon)
- `sdlc.rejectGate` (thumbsdown icon)
- `sdlc.submitEvidence` (upload icon)

**Acceptance Criteria**:
- [ ] All commands call `getGateActions()` before executing
- [ ] Optimistic UI: spinner icon immediately, confirm on API response
- [ ] Exponential backoff polling if `processing=true`: 500ms → 1s → 2s → 5s
- [ ] SHA256 computation via Node.js `crypto.createHash('sha256')`
- [ ] File picker supports multi-file selection
- [ ] Progress indicator with `vscode.window.withProgress()`
- [ ] 403 handling with "Re-login" prompt
- [ ] Context menus on gate items in sidebar

---

### Day 2-7 (Track B): Framework Cleanup

**Owner**: Tech Lead / PM / Architect
**Priority**: P1

#### Day 2-3: Phase 5.2 — Code Review Consolidation (4-6 hours)

Consolidate 3 Implementation Guides into 1 SSOT:
- Create: `SDLC-Enterprise-Framework/07-Implementation-Guides/SDLC-Code-Review-Guide.md`
- Archive: 3 old guides → `10-Archive/02-Legacy/`
- Update: `CONTENT-MAP.md`

Sections: Tier Selection, Review Checklists, SDLC 6.0.5 Integration, Platform-Specific Guides

#### Day 4: Phase 5.3 — AI-GOVERNANCE Expansion (4 hours)

- Create: `03-AI-GOVERNANCE/08-Governance-Decision-Matrix.md` (requirement → principle → enforcement)
- Create: `03-AI-GOVERNANCE/09-Governance-Metrics.md` (vibecoding index, gate pass rate, evidence coverage)
- Update: `03-AI-GOVERNANCE/README.md` with section overview

#### Day 5-7: Phase 5.4 — Version Reference Updates (2-3 hours)

Update ~30 files with stale pre-6.0 version references:
- `Version: 5.x.x` in headers → `Version: 6.0.5`
- `SDLC 5.x.x` in titles → `SDLC 6.0.5`
- `NEW in 5.x.x` markers → `Added in 5.x.x, current as of 6.0.5`
- Preserve historical narrative in case studies (CTO Mod 8)

---

### Day 8-10: Phase 2.1 — Context Authority V1→V2 Merge

**Owner**: Backend Lead
**Priority**: P1

**Strangler Fig Pattern** (SDLC Expert mandatory safety rail):

#### Day 8: Golden Snapshot Tests

```
Create: backend/tests/unit/services/governance/test_ca_golden_snapshots.py
```

5 golden test scenarios:
1. ADR linkage validation
2. AGENTS.md freshness check
3. Module annotation consistency
4. Design doc reference check
5. Mixed violations scenario

**Stable ordering rule**: Sort violations by `(code, path, message)`, strip timestamps before assert. Use real production data (anonymized) as input.

#### Day 9: Deprecate V1 + Redirect Routes

- Add deprecation warning to `context_authority.py` (V1)
- Change route service calls from V1 → V2 in `routes/context_authority.py`
- Verify golden tests still pass

#### Day 10: Verify & Delete

- Run full test suite including golden tests
- If 100% pass: delete V1 file
- Absorb `gates_ca_integration.py` into `gates_engine.py`
- Keep old import path as facade in `__init__.py` (1 sprint deprecation period)

**Files**:
- Create: `test_ca_golden_snapshots.py`
- Deprecate: `context_authority.py` (V1)
- Edit: `routes/context_authority.py` (redirect)
- Edit: `context_authority_v2.py` (absorb V1 methods)
- Delete: `context_authority.py`, `gates_ca_integration.py`

**LOC saved**: ~500

---

### Day 11-12: Phase 2.2 — Governance Mode Enforcer Consolidation

**Owner**: Backend Team
**Priority**: P1

#### Day 11: Unit Test Matrix + Strategy

```
Create: backend/tests/unit/services/governance/test_enforcement_matrix.py
Create: backend/app/services/governance/enforcement_strategy.py
```

Decision matrix test:
```python
DECISION_MATRIX = [
    (25, "SOFT", "AUTO_APPROVED"),
    (25, "FULL", "AUTO_APPROVED"),
    (45, "SOFT", "APPROVED"),
    (45, "FULL", "NEED_TECH_LEAD_APPROVAL"),
    (70, "SOFT", "WARNED"),
    (70, "FULL", "NEED_CEO_APPROVAL"),
    (90, "SOFT", "BLOCKED"),
    (90, "FULL", "BLOCKED_NEED_CTO_CEO"),
]
```

Strategy pattern:
- `EnforcementStrategy` (ABC): pure decision engine, no side effects
- `SoftEnforcement`: advisory, blocks CRITICAL only
- `FullEnforcement`: strict, zone-based approval + workflow effects

#### Day 12: Integrate & Delete

- `mode_service.py` delegates to appropriate strategy
- Delete `soft_mode_enforcer.py` and `full_mode_enforcer.py`
- Verify test matrix passes

**LOC saved**: ~700

---

### Day 13: Phase 3 (Freeze) + Phase 4 (Delete)

**Owner**: Backend Lead
**Priority**: P1

#### Phase 3: Freeze Non-Core Modules (2 hours)

Add freeze header to each frozen module:
```python
"""
STATUS: FROZEN (Sprint 173, Feb 2026)
TIER: Enterprise
REASON: Non-core for current phase. Working code preserved.
REACTIVATION: CPO approval required.
DO NOT: Delete, refactor, or add features without CTO approval.
"""
```

Modules to freeze: NIST Compliance (4 services), AI Council Service, Feedback Learning, SOP Generator, Agentic Maturity, SASE Generation, App Builder, Spec Converter, Codegen EP-06 (46 files).

CI enforcement in `.github/workflows/ci.yml`:
- Use merge-base diff (`$base_ref...$sha`) for frozen path detection
- Bypass via GitHub `CTO-OVERRIDE` label

#### Phase 4: Delete HIGH Confidence Dead Code (1 hour)

| Item | LOC | Confidence |
|------|-----|------------|
| `vietnamese_sme_demo.py` | 638 | HIGH |
| Empty NIST frontend pages (4) | ~200 | HIGH |
| `admin.py.backup-*` | ? | HIGH |

**Total**: ~838 LOC deleted

---

### Day 14: Integration Test + Review

**Owner**: Full Team
**Priority**: P0

- 3-client parity test (same gate lifecycle via Web, CLI, Extension)
- Golden snapshot tests pass
- Enforcement decision matrix passes
- Full test suite: `cd backend && python -m pytest tests/ -v`
- Extension tests: `cd vscode-extension && npm run test`
- Framework verification:
  - `grep -r "SDLC 5\." --include="*.md" -l | grep -v "10-Archive/"` → 0 results
  - Moratorium + freeze notices present
  - Code Review consolidated

---

## Sprint Metrics

| Metric | Target |
|--------|--------|
| Test coverage | 95%+ |
| API p95 latency | <100ms |
| State machine transitions | 100% tested |
| Golden test scenarios | 5+ |
| Enforcement matrix | 8+ scenarios |
| Client parity | 100% (3/3 clients) |
| LOC removed (Phase 2+4) | ~2,038 |
| Modules frozen | 9 |

---

## Risk Register

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| DB migration breaks existing gates | HIGH | LOW | Alembic handles data migration explicitly; test on dev first |
| Redis unavailable for idempotency | MEDIUM | LOW | Graceful degradation: skip check, log warning |
| State rename breaks client code | MEDIUM | MEDIUM | Search all codebases for `PENDING_APPROVAL` before migration |
| Golden tests fail on V1→V2 merge | HIGH | MEDIUM | Use real production data; fix discrepancies before delete |
| Extension SHA256 slow on large files | LOW | LOW | Stream-based hashing; 100MB limit |
| CTO-OVERRIDE label misuse | MEDIUM | LOW | Label requires CTO manually adding it to PR |

---

## Dependencies

| Dependency | Owner | Status |
|------------|-------|--------|
| Redis (port 6395) | DevOps | Verify in Pre-Flight |
| Gate model migration | Backend | Day 1 |
| Evidence model migration | Backend | Day 1 |
| Auth scope separation | Backend | Day 1 |
| Framework submodule | Tech Lead | Day 1 (freeze PR) |

---

## Review History

| Version | Date | Reviewer | Verdict |
|---------|------|----------|---------|
| v1 | Feb 12 | CTO | Partially Approved — rejected 80% deletion |
| v2 | Feb 13 | Architect v1 | Approved w/ 3 fixes |
| v2 | Feb 13 | SDLC Expert v1 | Approved w/ 6 safety rails |
| v3 | Feb 14 | Architect v2 | Approved — Grade A (Dual Track) |
| v3 | Feb 14 | SDLC Expert v2 | Approved w/ 6 P0 fixes |
| v3 | Feb 14 | CTO | Approved w/ 8 mandatory modifications |
| **v4 FINAL** | **Feb 15** | **All** | **Unanimous approval for execution** |

---

## Definition of Done

- [ ] All 3 clients perform full gate lifecycle (evaluate → submit → approve/reject)
- [ ] `compute_gate_actions()` is sole permission authority (no client-side logic)
- [ ] Evidence contract enforced (server SHA256 + criteria_snapshot_id)
- [ ] Idempotency on all mutations (Redis TTL 24h)
- [ ] Context Authority V1 deleted, V2 is SSOT (golden tests passing)
- [ ] Enforcement consolidated (Strategy pattern, matrix tests passing)
- [ ] 9 modules frozen with CI enforcement
- [ ] ~838 LOC dead code deleted
- [ ] Framework SPEC moratorium + AI-Tools freeze active
- [ ] Code Review docs consolidated (1 SSOT guide)
- [ ] AI-GOVERNANCE expanded (Decision Matrix + Metrics)
- [ ] Version refs updated (5.x → 6.0.5 where appropriate)
- [ ] Full test suite passing
- [ ] CTO Day 1 checkpoint passed

---

*Sprint 173 — "Sharpen, Don't Amputate". Complete the governance loop. Simplify, don't delete. Framework first, code second.*
