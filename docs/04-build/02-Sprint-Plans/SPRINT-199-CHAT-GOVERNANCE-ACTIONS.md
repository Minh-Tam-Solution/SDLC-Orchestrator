# Sprint 199 — Chat Governance Actions + Evidence Upload via OTT

**Sprint Duration**: March 10 – March 21, 2026 (10 working days)
**Sprint Goal**: Wire end-to-end governance actions via OTT chat (gate approve, evidence upload, sprint status) and deliver Sprint 198 deferred items (webhook viewer, config panel, Master Test Plan)
**Status**: PLANNED
**Priority**: P0 (Dogfooding 60% → 75%)
**Framework**: SDLC 6.1.1
**CTO Score (Sprint 198)**: TBD
**Previous Sprint**: [Sprint 198 — OTT Gateway Dashboard + Bidirectional AI](SPRINT-198-OTT-GATEWAY-DASHBOARD.md)

---

## Sprint 199 Goal

Sprint 198 delivers bidirectional AI conversation (Telegram ↔ Ollama) and the Gateway Dashboard. Sprint 199 **wires the governance actions** so users can actually *do things* via chat — approve gates, upload evidence, check sprint status — completing the Chat-First Facade (ADR-064) North Star Loop.

**Dogfooding level**: 60% → 75% — governance actions accessible from OTT chat.

**Three pillars**:
1. **Gate Actions via Chat** — `approve <gate_id>` wired end-to-end with Magic Link OOB auth
2. **Evidence Upload via OTT** — File attachment → Evidence Vault → SHA256 integrity
3. **Sprint 198 Deferred Items** — Webhook viewer, config panel, Master Test Plan escalation

**North Star Loop (ADR-064 §2.3)**:
```
@mention → Gate Actions → Evidence → Approve (Magic Link) → Audit Export
                ↑ Sprint 199 delivers these 3 steps ↑
```

**Conversation-First** (CEO directive Sprint 190): All governance flows through OTT+CLI. Web App = admin-only.

---

## Sprint 199 Backlog

### Track A — Gate Actions via Chat (Day 1-5) — @pm

**Goal**: Wire the `approve_gate`, `gate_status`, and `create_project` commands from `command_registry.py` (registered but not yet wired end-to-end) through the OTT → Agent Team → Service → Response pipeline.

**Architecture**:
```
User: "approve gate 5"
    │
    ├─ ai_response_handler.py → detect governance intent
    │
    ├─ chat_command_router.py → Ollama function calling
    │   └─ tool_call: approve_gate(gate_id=5)
    │
    ├─ gate_service.compute_gate_actions(gate_id=5) → check permissions
    │
    ├─ magic_link_service.py → generate HMAC-SHA256 OOB auth link (5-min TTL)
    │   └─ "Click to confirm: https://sdlc.../approve?token=abc123"
    │
    └─ telegram_responder.send_reply() → formatted gate approval message
```

| ID | Item | Priority | Deliverable |
|----|------|----------|-------------|
| A-01 | Wire `gate_status` command end-to-end | P0 | User sends "gate status 5" → formatted gate info returned via Telegram |
| A-02 | Wire `approve_gate` command with Magic Link | P0 | User sends "approve gate 5" → OOB auth link generated → gate approved on click |
| A-03 | Wire `create_project` command | P1 | User sends "create project X" → project created → confirmation reply |
| A-04 | Governance intent detection in AI handler | P1 | `ai_response_handler.py` detects governance verbs → routes to `chat_command_router` |
| A-05 | Magic Link callback endpoint | P0 | `GET /api/v1/magic-link/verify?token=...` → gate approved + redirect to confirmation |
| A-06 | Response formatter for gate actions | P1 | Vietnamese/English formatted Telegram messages for gate status, approval, rejection |

**Key files**:
- `backend/app/services/agent_team/chat_command_router.py` — Already has 6-tool allowlist, needs wiring to real services
- `backend/app/services/agent_team/magic_link_service.py` — HMAC-SHA256 OOB auth (313 LOC, exists)
- `backend/app/services/agent_team/command_registry.py` — 6 tools registered, handlers declared but not connected

**Acceptance criteria**:
- [ ] `gate_status` returns gate info (type, status, exit criteria, last evaluation)
- [ ] `approve_gate` generates Magic Link with 5-min TTL, gate approved after click
- [ ] `create_project` creates real project in DB, returns project ID + URL
- [ ] All governance actions logged to audit trail with `source="chat"`

---

### Track B — Evidence Upload via OTT (Day 3-6) — @pm

**Goal**: Enable file attachments from Telegram/Zalo to flow into the Evidence Vault with SHA256 integrity verification.

**Architecture**:
```
User sends file attachment on Telegram
    │
    ├─ ott_gateway.py → extract file_id from message.document
    │
    ├─ telegram_responder.py → download file via Bot API getFile
    │
    ├─ evidence_service.upload() → MinIO S3 + SHA256 hash
    │
    └─ Reply: "Evidence uploaded: SHA256=abc123, linked to Gate G2"
```

| ID | Item | Priority | Deliverable |
|----|------|----------|-------------|
| B-01 | Telegram file attachment handler | P0 | Extract `file_id` from `message.document`, download via Bot API |
| B-02 | Wire `submit_evidence` command | P0 | "upload evidence for gate 3" → download attachment → Evidence Vault |
| B-03 | Evidence confirmation reply | P1 | Reply with SHA256 hash, evidence type, linked gate ID |
| B-04 | File size validation | P1 | Max 10MB for OTT uploads (consistent with Evidence API) |
| B-05 | Zalo file attachment support | P2 | Extract file URL from Zalo OA `user_send_file` event |

**New/Modified files**:
- `backend/app/services/agent_bridge/telegram_responder.py` — Add `download_file()` + `send_reply()` methods
- `backend/app/services/agent_bridge/ai_response_handler.py` — Detect file attachments, route to evidence handler
- `backend/app/services/agent_bridge/evidence_upload_handler.py` — NEW (~150 LOC) — OTT → Evidence Vault bridge

**Acceptance criteria**:
- [ ] PDF/image file sent via Telegram → stored in Evidence Vault with SHA256
- [ ] Evidence linked to specified gate (user provides gate_id)
- [ ] Confirmation reply shows SHA256 hash + evidence URL
- [ ] Files > 10MB rejected with Vietnamese error message

---

### Track C — Sprint 198 Deferred Items (Day 4-7) — @pm

| ID | Item | Source | Priority | Deliverable |
|----|------|--------|----------|-------------|
| C-01 | Webhook log viewer component | Sprint 198 A-09 (deferred) | P2 | `WebhookLogViewer.tsx` — recent payloads, status codes, dedup indicator |
| C-02 | Channel config panel | Sprint 198 A-10 (deferred) | P2 | `ChannelConfigPanel.tsx` — view/test channel config (secrets masked) |
| C-03 | Test-webhook endpoint | Sprint 198 A-04 (deferred) | P2 | `POST /api/v1/admin/ott-channels/{channel}/test-webhook` |
| C-04 | Master Test Plan — ESCALATED | CF-03 (3rd deferral) | **P1** | MASTER-TEST-PLAN.md skeleton — **CTO escalation: must deliver or explain** |

**CTO Directive on C-04**: This item has been deferred 3 sprints (196 → 197 → 198 → 199). If @tester unavailable, @pm creates a skeleton Master Test Plan from existing test docs (00-TEST-STRATEGY-2026.md, test reports, pytest output). No 4th deferral allowed.

**Acceptance criteria**:
- [ ] Webhook viewer shows recent webhooks with timestamp, channel, status, dedup flag
- [ ] Config panel shows channel configuration with secrets masked (●●●●)
- [ ] Test-webhook sends synthetic payload, returns health status
- [ ] MASTER-TEST-PLAN.md exists with 7-category index linking to existing docs

---

### Track D — E2E Testing + Sprint Close (Day 8-10) — @pm

| ID | Item | Priority | Deliverable |
|----|------|----------|-------------|
| D-01 | Gate approval via Telegram E2E test | P0 | Create gate → approve via chat → verify gate status APPROVED |
| D-02 | Evidence upload via Telegram E2E test | P0 | Upload file via chat → verify in Evidence Vault with SHA256 |
| D-03 | Magic Link verification E2E test | P1 | Generate link → click → verify gate state transition |
| D-04 | Regression test suite (700+ tests) | P0 | All Sprint 197 + 198 tests passing, 0 regressions |
| D-05 | OWASP verification for Magic Link | P1 | Token expiry (5 min), single-use, HMAC integrity, no replay |
| D-06 | Sprint 199 close documentation | P1 | G-Sprint-Close within 24h |

---

## Architecture: Chat Governance Action Flow

### Gate Approval via OTT (ADR-064 North Star)

```
  Telegram User               SDLC Backend              Magic Link
       │                           │                        │
       │── "approve gate 5" ──────>│                        │
       │                           │── chat_command_router   │
       │                           │── tool: approve_gate(5) │
       │                           │── compute_gate_actions() │
       │                           │── requires_oob_auth?    │
       │                           │   YES → magic_link      │
       │                           │── generate HMAC token ──>│
       │                           │                        │
       │<── "Click to approve:     │                        │
       │     https://sdlc.../      │                        │
       │     verify?token=abc123"  │                        │
       │                           │                        │
       │── [User clicks link] ────────────────────────────>│
       │                           │                        │── verify HMAC
       │                           │                        │── check 5min TTL
       │                           │<── gate_service.approve()│
       │                           │                        │
       │<── "Gate 5 APPROVED ✅    │                        │
       │     by @user via OTT"     │                        │
```

### Evidence Upload via OTT

```
  Telegram User               SDLC Backend              MinIO S3
       │                           │                        │
       │── [Attach PDF] ──────────>│                        │
       │   "evidence for gate 3"   │                        │
       │                           │── extract file_id      │
       │                           │── Bot API getFile()    │
       │                           │── download file bytes  │
       │                           │── SHA256 hash         │
       │                           │── evidence_service     │
       │                           │── upload() ──────────>│
       │                           │                        │── store
       │                           │<── s3://evidence/...  │
       │                           │                        │
       │<── "Evidence uploaded ✅   │                        │
       │     SHA256: abc123...      │                        │
       │     Gate: G2, Type: TEST"  │                        │
```

---

## Files Summary

| File | Action | LOC | Track |
|------|--------|-----|-------|
| `backend/app/services/agent_bridge/evidence_upload_handler.py` | NEW | ~150 | B |
| `backend/app/services/agent_bridge/ai_response_handler.py` | MODIFY | ~80 | A (governance intent detection) |
| `backend/app/services/agent_bridge/telegram_responder.py` | MODIFY | ~60 | B (download_file, send_reply) |
| `backend/app/services/agent_team/chat_command_router.py` | MODIFY | ~100 | A (wire to real services) |
| `backend/app/api/routes/magic_link.py` | NEW | ~80 | A (callback endpoint) |
| `backend/app/api/routes/admin_ott.py` | MODIFY | ~40 | C (test-webhook endpoint) |
| `frontend/src/components/ott-gateway/WebhookLogViewer.tsx` | NEW | ~70 | C |
| `frontend/src/components/ott-gateway/ChannelConfigPanel.tsx` | NEW | ~80 | C |
| `docs/05-test/MASTER-TEST-PLAN.md` | NEW | ~200 | C (skeleton) |
| Tests (unit + integration + E2E) | NEW | ~400 | D |
| **Total** | | **~1,260** | |

---

## Sprint 199 Success Criteria

**Hard criteria (8)**:
- [ ] `gate_status` command returns real gate info via Telegram
- [ ] `approve_gate` generates Magic Link, gate approved after click
- [ ] `create_project` creates real project, confirmation via chat
- [ ] File attachment via Telegram → Evidence Vault with SHA256
- [ ] Magic Link: HMAC integrity, 5-min TTL, single-use
- [ ] All audit logs record `source="chat"` for OTT actions
- [ ] 700+ test suite green, 0 regressions
- [ ] G-Sprint-Close within 24h

**Stretch criteria (3)**:
- [ ] Webhook log viewer live on Gateway Dashboard
- [ ] Channel config panel with test-webhook button
- [ ] MASTER-TEST-PLAN.md with 7-category index

---

## Risk Assessment

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Magic Link security (token replay) | P0 — unauthorized gate approval | Low | Single-use token, 5-min TTL, HMAC-SHA256, audit log |
| File download from Telegram Bot API fails | P1 — evidence upload broken | Medium | Retry 3x with exponential backoff, fallback error message |
| chat_command_router hallucination | P1 — wrong gate_id | Medium | Pydantic v2 validation + user confirmation before mutation |
| Master Test Plan 4th deferral | P2 — CTO escalation | Low | PM creates skeleton if @tester unavailable |

---

## Dependencies

- **Sprint 198 complete**: Bidirectional AI + Gateway Dashboard must be working
- **Magic Link service**: `magic_link_service.py` (313 LOC) exists, needs callback route
- **Command Registry**: 6 tools registered in `command_registry.py`, handlers need wiring
- **Evidence Vault API**: Existing `evidence_service.upload()` reused
- **Telegram Bot API**: `getFile` endpoint for file downloads

---

**Last Updated**: February 23, 2026
**Created By**: PM + AI Development Partner — Sprint 199 Planning
**Framework Version**: SDLC 6.1.1
**Previous State**: Sprint 198 IN PROGRESS
