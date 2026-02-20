---
sdlc_version: "6.1.0"
document_type: "Epic"
status: "PROPOSED"
sprint: "176-179"
spec_id: "EP-07"
tier: "PROFESSIONAL"
stage: "01 - Planning"
---

# EP-07 — Multi-Agent Team Engine (MATE)

| Field | Value |
|-------|-------|
| **Epic ID** | EP-07 |
| **Title** | Multi-Agent Team Engine |
| **Status** | PROPOSED — Sprint 176 Design |
| **Priority** | **P0** (blocks EP-06 Autonomous Codegen) |
| **Owner** | CTO / Platform Team |
| **Created** | 2026-02-17 |
| **Updated** | 2026-02-19 |
| **SDLC Version** | 6.1.0 |
| **Stage** | 01-planning |
| **Timeline** | Sprint 176–179 (Feb–Apr 2026) |
| **Investment** | ~$14,400 |
| **ADR** | ADR-056 (4 locked decisions, 14 non-negotiables), ADR-058 (ZeroClaw patterns) |

---

## 1. Epic Summary

Build foundational multi-agent infrastructure for SDLC Orchestrator by absorbing production-proven patterns from OpenClaw (36-channel gateway), TinyClaw (file-based queue), Nanobot (tool isolation), and ZeroClaw (Rust agent runtime). Enables agent-to-agent delegation, lane-based message queue, provider failover classification, security guards, and output credential scrubbing.

**Dependency**: EP-06 Autonomous Codegen (ADR-055) requires MATE for Initializer → Coder → Reviewer agent chain.

---

## 2. Business Value

- **Unblocks EP-06**: Autonomous Codegen cannot function without agent delegation infrastructure
- **Enables OTT**: Vietnamese SME market access via Telegram/Zalo integration
- **Security Hardening**: 20 deny patterns (input sanitizer + shell guard) protect agent execution
- **Cost Control**: Per-conversation budget circuit breaker prevents runaway AI spend
- **Provider Resilience**: 6-reason failover classification with automatic fallback chain

---

## 3. Scope

### 3.1 P0 — Core Multi-Agent (Sprint 176-177)

| Deliverable | Description | Sprint |
|------------|-------------|--------|
| 3 DB Tables | agent_definitions, agent_conversations, agent_messages | 177 |
| 12 Service Files | Registry, queue, tracker, invoker, classifier, sanitizer, guard, context, reflect | 177 |
| 5 API Endpoints | Definitions CRUD, conversations start, messages send/get | 177 |
| Pydantic Schemas | Request/response validation with CTO-corrected enums | 176 |
| Security Guards | InputSanitizer (12 patterns) + ShellGuard (8 patterns) + ToolContext | 177 |
| Unit Tests | 73 test cases across 6 modules | 177 |

### 3.2 P1 — Collaboration + OTT Notify (Sprint 178)

| Deliverable | Description | Sprint |
|------------|-------------|--------|
| Team Orchestrator | Queue modes (queue/steer/interrupt) | 178 |
| Evidence Collector | Auto-capture with correlation_id | 178 |
| OTT Gateway Scaffold | Plugin-based architecture (Telegram MVP) | 178 |
| Integration Tests | 14 test cases (lane queue + multi-agent E2E) | 178 |

### 3.3 P1.5 — ZeroClaw Security Hardening (Sprint 179)

| Deliverable | Description | Sprint |
|------------|-------------|--------|
| Output Credential Scrubbing | 6 regex patterns, scrub → hash → store (FR-042) | 179 |
| Environment Variable Scrubbing | 9-var safe allowlist for shell execution (FR-043) | 179 |
| History Compaction | Auto-summarize at 80% capacity, metadata_ JSONB (FR-044) | 179 |
| Query Classification | Pure function model routing: code/reasoning/fast hints | 179 |
| Unit Tests | 34 new test cases across 4 modules | 179 |

### 3.4 P2 — OTT Approval + Expansion (Sprint 180+)

| Deliverable | Description | Sprint |
|------------|-------------|--------|
| OTT Approval Flow | 2FA-like confirmation (APPROVE G3 #12345) | 180 |
| Discord Plugin | Discord channel integration | 180 |
| WhatsApp/Zalo Plugins | Vietnamese market channels | 181-182 |
| Team Visualizer | Agent collaboration dashboard | 181 |

---

## 4. Architecture

### 4.1 Four Locked Decisions (ADR-056)

| # | Decision | Summary |
|---|----------|---------|
| 1 | Snapshot Precedence | Definition fields snapshot into conversation on creation; immutable after |
| 2 | Lane Contract | DB is truth, Redis is notify-only; includes dead-letter + dedupe |
| 3 | Provider Profile Key | `{provider}:{account}:{region}:{model_family}` + abort matrix |
| 4 | Canonical Protocol Owner | Orchestrator defines all message schemas |

### 4.2 Fourteen Non-Negotiables

**Security (6)**: Least-privilege scopes, external identity verified, 2FA OTT approval, input sanitizer (12 patterns), shell guard (8 patterns), tool workspace restriction

**Architecture (5)**: Lane-based queue (includes dead-letter + dedupe), read-only workspace, loop guards (6 limits), snapshot precedence, canonical protocol owner

**Observability (3)**: Identity masquerading audit, token budget circuit breaker, human-in-the-loop interrupt

### 4.3 Pattern Sources

| Pattern | Source | Files |
|---------|--------|-------|
| Lane-based concurrency | OpenClaw `command-queue.ts` | `message_queue.py` |
| FailoverError (6 reasons) | OpenClaw `failover-error.ts` | `failover_classifier.py` |
| @mention routing | TinyClaw `routing.ts` | `mention_parser.py` |
| 50-msg loop prevention | TinyClaw `queue-processor.ts` | `conversation_tracker.py` |
| Shell deny patterns | Nanobot `tools/shell.py` | `shell_guard.py` |
| Tool context isolation | Nanobot `subagent.py` | `tool_context.py` |
| Reflect-after-tools | Nanobot `loop.py` | `reflect_step.py` |
| Credential scrubbing | ZeroClaw `src/agent/loop_.rs` | `output_scrubber.py` |
| Environment scrubbing | ZeroClaw `src/tools/shell.rs` | `shell_guard.py` |
| History compaction | ZeroClaw `src/agent/loop_.rs` | `history_compactor.py` |
| Query classification | ZeroClaw `src/agent/classifier.rs` | `query_classifier.py` |

---

## 5. Database Schema (3 P0 Tables)

### 5.1 agent_definitions

Stores agent templates/defaults. Snapshot Precedence: these values become defaults for new conversations.

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| project_id | UUID FK → projects | |
| team_id | UUID FK → teams | nullable |
| agent_name | VARCHAR(50) | |
| sdlc_role | VARCHAR(20) | 12 roles (3 types): SE4A: researcher/pm/pjm/architect/coder/reviewer/tester/devops, SE4H: ceo/cpo/cto, Router: assistant (ADR-056 §12.5) |
| provider | VARCHAR(20) | |
| model | VARCHAR(100) | |
| system_prompt | TEXT | |
| working_directory | VARCHAR(500) | |
| max_tokens | INTEGER DEFAULT 4096 | |
| temperature | FLOAT DEFAULT 0.7 | |
| queue_mode | VARCHAR(20) DEFAULT 'queue' | P0: queue/steer/interrupt |
| session_scope | VARCHAR(20) DEFAULT 'per-sender' | P0: per-sender/global |
| max_delegation_depth | INTEGER DEFAULT 1 | Nanobot N2 |
| allowed_tools | JSONB DEFAULT '["*"]' | Nanobot N2 |
| denied_tools | JSONB DEFAULT '[]' | Nanobot N2 |
| can_spawn_subagent | BOOLEAN DEFAULT false | Nanobot N2 |
| allowed_paths | JSONB DEFAULT '[]' | Nanobot N2 |
| reflect_frequency | INTEGER DEFAULT 1 | Nanobot N4 |
| is_active | BOOLEAN DEFAULT true | |
| config | JSONB | |
| created_at, updated_at | TIMESTAMP | |

### 5.2 agent_conversations

Stores active conversations with snapshotted fields.

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| project_id | UUID FK → projects | |
| agent_definition_id | UUID FK → agent_definitions | |
| parent_conversation_id | UUID FK → self | nullable, OpenClaw subagent inheritance |
| delegation_depth | INTEGER DEFAULT 0 | Nanobot N2 |
| initiator_type | VARCHAR(20) | user/agent/gate_event/ott_channel |
| initiator_id | VARCHAR(100) | |
| channel | VARCHAR(20) | web/cli/extension/telegram/discord |
| session_scope | VARCHAR(20) | Snapshotted from definition |
| status | VARCHAR(20) | active/completed/max_reached/paused_by_human/error |
| total_messages | INTEGER DEFAULT 0 | |
| max_messages | INTEGER DEFAULT 50 | Snapshotted from definition |
| branch_count | INTEGER DEFAULT 0 | TinyClaw |
| input_tokens | INTEGER DEFAULT 0 | OpenClaw |
| output_tokens | INTEGER DEFAULT 0 | OpenClaw |
| total_tokens | INTEGER DEFAULT 0 | OpenClaw |
| current_cost_cents | INTEGER DEFAULT 0 | Budget circuit breaker |
| max_budget_cents | INTEGER DEFAULT 1000 | Snapshotted from definition |
| metadata | JSONB | |
| started_at, completed_at | TIMESTAMP | |

### 5.3 agent_messages

Stores messages with lane contract + dead-letter fields.

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| conversation_id | UUID FK → agent_conversations | |
| parent_message_id | UUID FK → self | nullable, thread support |
| sender_type | VARCHAR(20) | user/agent/system |
| sender_id | VARCHAR(100) | |
| recipient_id | VARCHAR(100) | |
| content | TEXT | |
| mentions | JSONB | TinyClaw @mention |
| message_type | VARCHAR(20) | request/response/mention/system/interrupt |
| queue_mode | VARCHAR(20) | OpenClaw |
| processing_status | VARCHAR(20) | pending/processing/completed/failed/dead_letter |
| processing_lane | VARCHAR(50) | OpenClaw lane concurrency |
| dedupe_key | VARCHAR(100) UNIQUE | Idempotency |
| correlation_id | UUID | Request tracing |
| token_count | INTEGER | |
| latency_ms | INTEGER | |
| provider_used | VARCHAR(20) | |
| failover_reason | VARCHAR(20) | 6 values |
| failed_count | INTEGER DEFAULT 0 | Dead-letter tracking |
| last_error | TEXT | Dead-letter |
| next_retry_at | TIMESTAMP | Exponential backoff |
| evidence_id | UUID FK → gate_evidence | nullable |
| created_at | TIMESTAMP | |

---

## 6. API Endpoints

### 6.1 P0 Endpoints (Sprint 177)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/agent-team/definitions` | Create agent definition |
| GET | `/api/v1/agent-team/definitions` | List definitions (paginated) |
| PATCH | `/api/v1/agent-team/definitions/{id}` | Update definition |
| POST | `/api/v1/agent-team/conversations` | Start conversation |
| POST | `/api/v1/agent-team/conversations/{id}/messages` | Send message |
| GET | `/api/v1/agent-team/conversations/{id}/messages` | Get messages (paginated) |

### 6.2 P1 Endpoints (Sprint 178)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/agent-team/conversations/{id}` | Get conversation state |
| POST | `/api/v1/agent-team/conversations/{id}/complete` | Complete conversation |
| POST | `/api/v1/agent-team/conversations/{id}/interrupt` | Human interrupt |
| GET | `/api/v1/agent-team/conversations/{id}/events` | SSE event feed |
| POST | `/api/v1/agent-team/evidence/batch` | Batch evidence capture |

---

## 7. Success Criteria

| Criterion | Target | Measurement |
|-----------|--------|-------------|
| Unit test coverage | 95%+ | `--cov-report=term-missing` |
| All unit tests pass | 107/107 | 10 test suites (6 original + 4 ZeroClaw) |
| Integration tests pass | 14/14 | Lane queue + E2E |
| P0 API response time | <100ms p95 | pytest-benchmark |
| Zero P0 security bugs | 0 | STM-056 threat coverage |
| Budget circuit breaker tested | Pass | MA-03 test case |
| Failover chain tested | Pass | MA-04 test case |

---

## 8. Dependencies

| Dependency | Type | Status |
|-----------|------|--------|
| ADR-055 (Autonomous Codegen) | Consumer | Sprint 176-178 |
| AI Council Service | Reference only | FROZEN (Sprint 173) |
| PostgreSQL 15.5 | Infrastructure | Available |
| Redis 7.2 | Infrastructure | Available |
| Alembic migration pipeline | Tool | Available |

---

## 9. Risks

| Risk | Mitigation |
|------|-----------|
| ADR-055 scope conflict with Sprint 176-178 | Update sprint plans to include MATE P0 |
| AI Council unfreezing pressure | MATE replaces Council patterns; Council stays FROZEN |
| OTT security (prompt injection) | InputSanitizer 12 patterns + defense-in-depth wrapping |
| Provider vendor lock-in | Provider profile key enables multi-provider failover |

---

## 10. Related Documents

| Document | Location | Status |
|----------|----------|--------|
| ADR-056 | `docs/02-design/ADR-056-Multi-Agent-Team-Engine.md` | PROPOSED |
| Security Threat Model | `docs/02-design/Multi-Agent-Security-Threat-Model.md` | PROPOSED |
| Test Plan | `docs/02-design/Multi-Agent-Test-Plan.md` | PROPOSED |
| Business Case | `docs/00-foundation/02-Business-Case/Multi-Agent-Team-Engine-Business-Case.md` | PROPOSED |
| Pydantic Schemas | `backend/app/schemas/agent_team.py` | IMPLEMENTED |
| Design Contracts | `backend/app/services/agent_team/` | IMPLEMENTED |
| ADR-058 | `docs/02-design/ADR-058-ZeroClaw-Best-Practice-Adoption.md` | PROPOSED |
| FR-042 | `docs/01-planning/03-Functional-Requirements/FR-042-Output-Credential-Scrubbing.md` | PROPOSED |
| FR-043 | `docs/01-planning/03-Functional-Requirements/FR-043-Environment-Variable-Scrubbing.md` | PROPOSED |
| FR-044 | `docs/01-planning/03-Functional-Requirements/FR-044-History-Compaction.md` | PROPOSED |
| Sprint 179 Plan | `docs/04-build/02-Sprint-Plans/SPRINT-179-ZEROCLAW-HARDENING.md` | PROPOSED |
