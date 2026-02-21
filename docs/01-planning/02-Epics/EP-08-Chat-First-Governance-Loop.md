---
sdlc_version: "6.1.0"
document_type: "Epic"
status: "IN PROGRESS"
sprint: "189-192"
spec_id: "EP-08"
tier: "ALL"
stage: "01 - Planning"
---

# EP-08 — Chat-First Governance Loop

| Field | Value |
|-------|-------|
| **Epic ID** | EP-08 |
| **Title** | Chat-First Governance Loop |
| **Status** | **IN PROGRESS** — Sprint 189 COMPLETE (CTO 9.4/10), Sprint 190 CEO APPROVED |
| **Priority** | **P0** (CEO strategic directive) |
| **Owner** | CTO / Platform Team |
| **Created** | 2026-02-21 |
| **Updated** | 2026-02-21 |
| **SDLC Version** | 6.1.0 |
| **Stage** | 01-planning |
| **Timeline** | Sprint 189–192 (Feb–Mar 2026) |
| **Investment** | ~$24,000 |
| **ADR** | ADR-064 (Chat-First Facade, 4 locked decisions, 13 conditions) |

---

## 1. Epic Summary

Add a thin LLM Function Calling chat interface on top of the existing Enterprise Control Plane, enabling governance workflows (project creation, gate evaluation, evidence submission, approval via Magic Link, audit export) through natural language `@mention` commands in OTT channels (Telegram, Zalo, Teams, Slack). Simultaneously remove ~21K LOC of frozen/unused code to reduce cognitive and maintenance overhead.

**CEO Vision**: A platform that realizes the SDLC Framework, governs large repos (Bflow, NQH-Bot), and frees the CEO from manually playing CEO/CPO/CTO oversight roles.

**CEO Interface Strategy** (Feb 21, 2026): Product is **conversation-first**. Team members interact via OTT or CLI. Web App is for admin/owner only. Enterprise channels (MS Teams, Slack) retained for enterprises that prohibit consumer OTT for work.

**North Star Loop**: `@mention → Gate Actions → Evidence → Approve (Magic Link) → Audit Export`

### Sprint Progress

| Sprint | Scope | Status |
|--------|-------|--------|
| **189** | Chat Command Router + Magic Link + OTT Dedupe | **COMPLETE** (CTO 9.4/10, CONDITIONAL APPROVE) |
| **190** | Aggressive Cleanup (~21K LOC deletion) | **CEO APPROVED** — executing |
| 191 | Unified Command Registry (CLI + OTT shared commands) | PROPOSED |
| 192 | Enterprise Hardening (Teams/Slack parity, SSO integration) | PROPOSED |

---

## 2. Business Value

- **CEO Liberation**: Encodes CEO governance patterns so any PM achieves CEO-level oversight
- **UX Transformation**: 35+ dashboard pages → single chat thread governance loop
- **Cost Efficiency**: $24K / 5 sprints vs $60-90K / 12-18 sprints (Option C rebuild)
- **Codebase Health**: ~21K LOC deleted (33% of frozen backend code)
- **Framework Realization**: SDLC Framework gate/evidence workflow becomes the chat UX, not a hidden feature
- **Time to Value**: <10 min for first governance loop (vs 30+ min with dashboard)

---

## 3. Scope

### 3.1 P0 — Chat Command Router + Magic Link (Sprint 189)

| Deliverable | Description | Sprint |
|------------|-------------|--------|
| chat_command_router.py | Bounded LLM Function Calling with Pydantic validation (~300 LOC) | 189 |
| magic_link_service.py | HMAC-signed single-use tokens, 5-min expiry, async Redis (~150 LOC) | 189 |
| requires_oob_auth | Add field to GateActionsResponse + compute_gate_actions() (~20 LOC) | 189 |
| OTT gateway dedupe | Redis-based event_id deduplication at ingest (~30 LOC) | 189 |
| MAGIC_LINK_SECRET | Add to config.py Settings (~5 LOC) | 189 |
| Wiring | Connect ott_gateway → mention_parser → chat_command_router | 189 |
| Acceptance Tests | 6 tests (happy path, actions contract, evidence, non-happy, bootstrap, bounded LLM) | 189 |

### 3.2 P1 — Aggressive Cleanup (Sprint 190) — CEO APPROVED

| Deliverable | Description | LOC | Sprint |
|------------|-------------|-----|--------|
| Pre-deletion dependency audit | `scripts/sprint190_audit_deps.sh` validates all imports clean | — | 190 (Day 0.5) |
| NIST services deletion | 4 service files + 4 route files | ~8,581 | 190 (Day 1) |
| AI Council + Feedback Learning | 3 service files + 3 route files + learning_aggregation.py collateral | ~4,083 | 190 (Day 2) |
| SOP/Spec/Pilot + V1 routes | 6 service items + 6 route files + dogfooding | ~6,277 | 190 (Day 3) |
| Router cleanup + import hygiene | main.py, models/__init__.py, services/__init__.py | — | 190 (Day 4) |
| Dashboard feature-flag + RBAC | `conversation_first_guard` middleware, 5 admin pages ON, ~29 pages OFF | — | 190 (Day 5) |
| DB tables deprecation | COMMENT ON TABLE (reversible), Alembic `include_object` filter | — | 190 (Day 6) |
| Test cleanup + smoke tests | Delete test files, 3 smoke tests, SASE anti-regression | ~2,000 | 190 (Day 7) |
| CLAUDE.md update + sprint close | Background task cleanup, sprint close doc | — | 190 (Day 8) |

**BLOCKER**: `sase_generation_service.py` CANNOT be deleted — `vcr_service.py` + `crp_service.py` actively import it. Deferred to Sprint 191+.

**Expert Validation**: 9/9 experts APPROVE (11 corrections incorporated, see SPRINT-190 plan)

### 3.3 P2 — Enterprise Hardening (Sprint 191-192)

| Deliverable | Description | Sprint |
|------------|-------------|--------|
| Teams + Slack parity | Enterprise channels as primary (existing normalizers) | 191 |
| SSO + Magic Link integration | Use existing SAML 2.0 for Magic Link authentication | 191 |
| Agent workflow chain | @pm → @architect → @coder → @reviewer → gate | 191 |
| GitHub evidence auto-capture | Webhook → auto-upload CI artifacts as gate evidence | 191 |
| Compliance export | @pm compliance report → audit PDF | 192 |
| Dashboard read-only mode | View status/evidence; write/approve via chat | 192 |
| Break-glass web approve | Feature-flagged admin-only approve button | 192 |

---

## 4. Out of Scope

- OpenClaw rebuild (Option C) — deferred unless Phase 0 PoC fails
- New DB schema for chat (reuses existing tables)
- LangChain or external LLM orchestration framework (T-02: native Ollama only)
- Dashboard redesign (just feature-flag, not rebuild)
- Mobile app (OTT channels serve as mobile interface)

---

## 5. Dependencies

| Dependency | Status | Impact |
|-----------|--------|--------|
| EP-07 Multi-Agent Team Engine (Sprint 176-179) | COMPLETE | Provides agent_team services, OTT gateway, mention_parser |
| ADR-059 Enterprise-First (Sprint 180-188) | COMPLETE | Provides tier enforcement, usage limits, pricing |
| Ollama qwen3:32b Vietnamese tool calling | UNTESTED | Day 1 PoC test — HIGH risk |
| Redis async client (app/utils/redis.py) | PRODUCTION | Used for magic link storage + dedupe |

---

## 6. Acceptance Criteria

### Phase 0 PoC (10 days, GO/NO-GO)

| # | Test | Pass Criteria |
|---|------|---------------|
| 1 | Happy path + OPA decision | Full governance loop <10 min, ≤8 interactions, OPA decision in audit_logs |
| 2 | Actions contract | GET /gates/{id}/actions returns requires_oob_auth. Bot explains "why not". Router NEVER bypasses. |
| 3 | Evidence contract | SHA256 server-side. User MUST select evidence type. Hash mismatch → reject. |
| 4 | Non-happy paths (6 cases) | DRAFT approve → 409; duplicate → idempotent; no permission → 403; hash mismatch → reject; Slack replay → dedupe; concurrent approvals → consistent |
| 5 | Developer setup | bootstrap_dev.sh → admin + sample project → <5 min |
| 6 | Bounded LLM | Invalid tool → clarification; Pydantic fail → retry 2x then error; hallucinated gate_id → rejected |

### Post-Cleanup (Sprint 190)

- `ruff check backend/` → 0 errors
- `python -m pytest backend/tests/` → all green
- Backend LOC: ~120K → ~100K
- Dashboard pages: 35 → 5 (default view)

---

## 7. New Files

| File | LOC | Purpose |
|------|-----|---------|
| `backend/app/services/agent_team/chat_command_router.py` | ~300 | LLM Function Calling router with Pydantic validation |
| `backend/app/services/agent_team/magic_link_service.py` | ~150 | HMAC-signed single-use OOB auth tokens |
| `scripts/bootstrap_dev.sh` | ~80 | One-command dev environment setup |

## 8. Modified Files

| File | Change | LOC |
|------|--------|-----|
| `backend/app/schemas/gate.py` | Add `requires_oob_auth` to GateActionsResponse | ~5 |
| `backend/app/services/gate_service.py` | Add OOB auth logic to compute_gate_actions() | ~15 |
| `backend/app/api/routes/ott_gateway.py` | Add Redis-based webhook dedupe | ~30 |
| `backend/app/core/config.py` | Add MAGIC_LINK_SECRET setting | ~5 |

## 9. Files to Delete (Sprint 190)

| File | LOC | Reason |
|------|-----|--------|
| `backend/app/services/nist_govern_service.py` | 1,653 | Frozen, unused |
| `backend/app/services/nist_map_service.py` | 1,697 | Frozen, unused |
| `backend/app/services/nist_manage_service.py` | 1,964 | Frozen, unused |
| `backend/app/services/nist_measure_service.py` | 1,104 | Frozen, unused |
| `backend/app/services/ai_council_service.py` | 1,895 | Frozen, unused |
| `backend/app/services/feedback_learning_service.py` | 1,588 | Frozen, unused |
| `backend/app/services/sop_generator_service.py` | ~500 | Frozen, unused |
| `backend/app/services/sase_generation_service.py` | ~500 | Frozen, unused |
| `backend/app/services/spec_converter/` | ~800 | Frozen, unused |
| `backend/app/services/pilot_tracking_service.py` | 914 | Frozen, unused |
| `backend/app/api/routes/dogfooding.py` | 1,682 | Frozen, unused |
| Corresponding route + test files | ~4,000 | Matching deletions |
| **Total** | **~18,300** | **28% of backend service code** |

---

## 10. Risk Register

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Ollama Vietnamese tool calling fails | MEDIUM | HIGH | Day 1 test; fallback: Claude Haiku |
| Cleanup breaks hidden dependencies | LOW | HIGH | Feature-flag first, delete after 1 sprint |
| Chat UX slower than dashboard | LOW | MEDIUM | Break-glass web approve (Phase 2) |
| Magic Link token guessing | LOW | CRITICAL | HMAC-SHA256 signing + 5-min TTL + single-use |
