---
sdlc_version: "6.0.6"
document_type: "ADR"
status: "PROPOSED"
sprint: "176"
spec_id: "ADR-056"
tier: "PROFESSIONAL"
stage: "02 - Design"
---

# ADR-056: Multi-Agent Team Engine — Strategic Upgrade from TinyClaw + OpenClaw + Nanobot

**Status**: PROPOSED (Sprint 176 Day 6, implementation Sprint 176-178)
**Date**: February 2026
**Author**: CTO Nguyen Quoc Huy
**Sprint**: Sprint 176 — Multi-Agent Foundation
**Framework**: SDLC 6.1.0
**Supersedes**: None (new capability)
**References**: ADR-055 (Autonomous Codegen), ADR-022 (Multi-Provider Architecture)
**Review History**: Expert Synthesis v2 FINAL, CTO Review (Feb 17), Nanobot 3-Expert Synthesis

---

## 1. Context

### 1.1 Problem Statement

SDLC Orchestrator's autonomous codegen pipeline (ADR-055) demonstrated a critical gap: **multi-agent collaboration** requires infrastructure that does not exist in the current platform. Specifically:

- **No agent-to-agent messaging** -- ADR-055's Initializer cannot delegate to Coder, Coder cannot hand off to Reviewer
- **No conversation state management** -- Agent sessions are ephemeral with no parent-child relationships
- **No provider failover** -- AI Council is FROZEN (Sprint 173); no lightweight alternative exists
- **No OTT channel integration** -- Vietnamese SME pilot requires Telegram/Zalo notifications
- **No agent safety guardrails** -- No tool permission boundaries, no shell command protection, no delegation depth limits

### 1.2 Pattern Sources

Three production codebases were analyzed for absorbable patterns:

| Codebase | Tech Stack | Scale | Patterns Extracted |
|----------|-----------|-------|-------------------|
| **OpenClaw** | Node.js 22+, TypeScript 5.9, WebSocket | 36 channels, 50+ skills, 900 tests | 7 core + 4 CTO-discovered |
| **TinyClaw** | Node.js, file-based queue, CLI | 6 SDLC roles, @mention routing | 7 patterns |
| **Nanobot** | Python 3.11+, LiteLLM, asyncio | ~3,663 core LOC, 9 channels | 6 patterns (5 P0) |

**CTO Verification**: Every OpenClaw claim verified against source code. 3 factual errors corrected (session scope 2 not 4, queue modes 7 not 5, failover reasons 6 not 5).

### 1.3 CEO Vision

3-product ecosystem:
- **SDLC Framework 6.0.6** (methodology) -- receives pattern templates
- **TinySDLC** (lightweight) -- receives plugin architecture + failover
- **SDLC Orchestrator** (enterprise) -- receives full Multi-Agent Team Engine

### 1.4 Existing System Constraints

| Component | Constraint | Decision |
|-----------|-----------|----------|
| `ai_council_service.py` (1,896 LOC) | FROZEN since Sprint 173 (CPO approval required) | Build lighter `agent_invoker.py` instead |
| `team.py` model | Already has `member_type='ai_agent'` with agentic maturity L0-L3 | Keep `agent_definitions` separate; dual-registration pattern |
| EventBus + WebSocket + Notifications | Three disconnected real-time systems | P0 uses `WebSocketManager.broadcast` directly; P1 bridges all three |

---

## 2. Decision

### 2.1 Option Selected: Option C (Hybrid)

Absorb *patterns* (not code) from all three codebases into Python backend. OTT channels as Node.js sidecar with plugin architecture.

**Rating**: A+ (95% confidence) after 4 review rounds across 3 codebases.

### 2.2 Architecture Overview

```
┌──────────────────────────────────────────────────────────────┐
│  SDLC Orchestrator (Python FastAPI)                          │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  Multi-Agent Team Engine                               │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────────────────┐   │  │
│  │  │ Registry │ │  Queue   │ │ Conversation Tracker │   │  │
│  │  │ (scopes) │ │ (lanes)  │ │ (parent-child+guard) │   │  │
│  │  └──────────┘ └──────────┘ └──────────────────────┘   │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────────────────┐   │  │
│  │  │ Invoker  │ │ Failover │ │  Input Sanitizer     │   │  │
│  │  │(fallback)│ │Classifier│ │ (12 regex patterns)  │   │  │
│  │  └──────────┘ └──────────┘ └──────────────────────┘   │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────────────────┐   │  │
│  │  │  Shell   │ │  Tool    │ │   Reflect Step       │   │  │
│  │  │  Guard   │ │ Context  │ │ (self-correction)    │   │  │
│  │  └──────────┘ └──────────┘ └──────────────────────┘   │  │
│  └────────────────────────────────────────────────────────┘  │
│                           ↕ REST API                         │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  OTT Gateway (Node.js sidecar, plugin architecture)   │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ │  │
│  │  │ Telegram │ │ Discord  │ │ WhatsApp │ │   Zalo   │ │  │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

---

## 3. Four Locked Architectural Decisions

These decisions are **non-negotiable** and locked by expert synthesis v2 + CTO review.

### 3.1 Decision 1: Snapshot Precedence

`agent_definitions` = **defaults/templates**. On conversation creation, snapshot relevant fields into `agent_conversations`. Once snapshotted, the conversation copy is **immutable** -- changing the definition does NOT retroactively affect running conversations.

```
CREATE conversation:
  conversation.max_messages = definition.max_messages  -- snapshot
  conversation.max_budget_cents = definition.max_budget_cents  -- snapshot
  conversation.queue_mode = definition.queue_mode  -- snapshot
  conversation.session_scope = definition.session_scope  -- snapshot
  -- After creation: conversation fields are authoritative, definition is ignored
```

**Rationale**: Running agents must not be affected by config changes. This is the same principle as Kubernetes pod spec immutability.

### 3.2 Decision 2: Lane Contract (Includes Dead-Letter + Deduplication)

**DB is truth. Redis is notify-only.** Dead-letter queue and deduplication are integral parts of the lane contract, not separate non-negotiables.

```
-- Lane processing pseudocode:
LOOP:
  BEGIN TX
    SELECT id, conversation_id, content, processing_lane
    FROM agent_messages
    WHERE processing_status = 'pending'
      AND processing_lane = :lane
      AND (next_retry_at IS NULL OR next_retry_at <= NOW())
    ORDER BY created_at
    FOR UPDATE SKIP LOCKED
    LIMIT 1
  -> msg

  IF msg IS NULL: BREAK

  UPDATE agent_messages SET processing_status = 'processing' WHERE id = msg.id
  COMMIT

  TRY:
    result = invoke_agent(msg)
    UPDATE agent_messages SET processing_status = 'completed', latency_ms = ... WHERE id = msg.id
  CATCH:
    UPDATE agent_messages SET
      processing_status = CASE WHEN failed_count >= 3 THEN 'dead_letter' ELSE 'pending' END,
      failed_count = failed_count + 1,
      last_error = error_message,
      next_retry_at = NOW() + (30 * 2^failed_count) SECONDS  -- 30s, 60s, 120s
    WHERE id = msg.id
```

**Deduplication**: `dedupe_key` column with UNIQUE constraint. `INSERT ... ON CONFLICT (dedupe_key) DO NOTHING`.

**Dead-Letter**: Messages with `failed_count >= 3` get `processing_status = 'dead_letter'`. Admin endpoint to inspect/replay. Exponential backoff: 30s, 60s, 120s.

**Redis notify**: `PUBLISH agent:lane:{lane_name} "new_message"` -- workers `SUBSCRIBE` and wake up. If Redis is down, workers poll DB every 5 seconds (fallback).

### 3.3 Decision 3: Provider Profile Key + Abort Matrix

**Provider Profile Key** format: `{provider}:{account}:{region}:{model_family}`

Examples:
- `ollama:local:vietnam:qwen3-coder`
- `anthropic:team-alpha:us-east-1:claude-sonnet`
- `openai:default:global:gpt-4o`

**Cooldown state** in Redis: `cooldown:{profile_key}` with TTL-based expiry (rate_limit=60s, timeout=120s).

**Abort vs Fallback Matrix** (6 error classes, CTO-verified):

| Error Class | HTTP Code | Action | Rationale |
|-------------|-----------|--------|-----------|
| `auth` | 401/403 | **ABORT** -- rethrow | Credential issue, won't resolve by retrying |
| `billing` | 402 | **ABORT** -- rethrow | Payment issue, needs human intervention |
| `rate_limit` | 429 | **FALLBACK** -- next provider | Transient, other providers likely available |
| `timeout` | 408/network | **FALLBACK** -- next provider | Transient, other providers likely faster |
| `format` | 400 | **RETRY 1x** -- fix prompt | Likely prompt issue, not provider issue |
| `unknown` | other | **ABORT** -- log + rethrow | Unclassifiable, needs human investigation |

**Error-as-String** (Nanobot N3): For RETRY cases, the error message is returned as structured content to the LLM, enabling self-correction. Errors are NOT raised as Python exceptions during retry -- they become part of the conversation context.

### 3.4 Decision 4: Canonical Protocol Owner = Orchestrator

Orchestrator defines the **canonical message protocol**. TinySDLC and OTT Gateway are **clients**.

```
Orchestrator (canonical owner):
  - Defines agent_messages schema (PostgreSQL)
  - Defines WebSocket protocol (JSON Schema validation)
  - Defines REST API contracts (Pydantic schemas)

TinySDLC (client):
  - Sends messages via Orchestrator REST API
  - Receives events via WebSocket or polling

OTT Gateway (client):
  - Translates Telegram/Discord/WhatsApp -> Orchestrator protocol
  - Sends via REST API, receives via WebSocket
```

---

## 4. Enhanced Database Schema (3 P0 Tables)

### 4.1 agent_definitions

```sql
CREATE TABLE agent_definitions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id),
    team_id UUID REFERENCES teams(id),
    agent_name VARCHAR(50) NOT NULL,
    sdlc_role VARCHAR(20) NOT NULL,              -- 12 roles: researcher/pm/pjm/architect/coder/reviewer/tester/devops/ceo/cpo/cto/assistant (see Section 12.5 SASE Classification)
    provider VARCHAR(20) NOT NULL,               -- ollama/anthropic/openai
    model VARCHAR(100) NOT NULL,
    system_prompt TEXT,
    working_directory VARCHAR(500),
    max_tokens INTEGER NOT NULL DEFAULT 4096,
    temperature FLOAT NOT NULL DEFAULT 0.7,
    queue_mode VARCHAR(20) NOT NULL DEFAULT 'queue',      -- P0: queue/steer/interrupt
    session_scope VARCHAR(20) NOT NULL DEFAULT 'per-sender', -- P0: per-sender/global
    max_delegation_depth INTEGER NOT NULL DEFAULT 1,       -- Nanobot: 0=no spawn, 1=one level
    -- Tool permissions (Nanobot N2)
    allowed_tools JSONB NOT NULL DEFAULT '["*"]',          -- ["*"]=all, ["read_file"]=restricted
    denied_tools JSONB NOT NULL DEFAULT '[]',              -- ["spawn_agent","send_message"]
    can_spawn_subagent BOOLEAN NOT NULL DEFAULT false,     -- Explicit spawn permission
    allowed_paths JSONB NOT NULL DEFAULT '[]',             -- ["/project/src/","/project/tests/"]
    -- Reflect step (Nanobot)
    reflect_frequency INTEGER NOT NULL DEFAULT 1,          -- 1=every batch, 3=every 3rd, 0=disabled
    is_active BOOLEAN NOT NULL DEFAULT true,
    config JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    UNIQUE(project_id, agent_name)
);

CREATE INDEX idx_agent_definitions_project ON agent_definitions(project_id);
CREATE INDEX idx_agent_definitions_team ON agent_definitions(team_id);
```

### 4.2 agent_conversations

```sql
CREATE TABLE agent_conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id),
    agent_definition_id UUID NOT NULL REFERENCES agent_definitions(id),
    parent_conversation_id UUID REFERENCES agent_conversations(id),  -- OpenClaw: subagent inheritance
    delegation_depth INTEGER NOT NULL DEFAULT 0,    -- Nanobot: current depth in chain
    initiator_type VARCHAR(20) NOT NULL,            -- user/agent/gate_event/ott_channel
    initiator_id VARCHAR(100) NOT NULL,
    channel VARCHAR(20) NOT NULL,                   -- web/cli/extension/telegram/discord
    session_scope VARCHAR(20) NOT NULL,             -- Snapshot from definition
    status VARCHAR(20) NOT NULL DEFAULT 'active',   -- active/completed/max_reached/paused_by_human/error
    total_messages INTEGER NOT NULL DEFAULT 0,
    max_messages INTEGER NOT NULL DEFAULT 50,       -- TinyClaw: loop prevention
    branch_count INTEGER NOT NULL DEFAULT 0,        -- TinyClaw: branch tracking
    -- Token budget (OpenClaw)
    input_tokens INTEGER NOT NULL DEFAULT 0,
    output_tokens INTEGER NOT NULL DEFAULT 0,
    total_tokens INTEGER NOT NULL DEFAULT 0,
    current_cost_cents INTEGER NOT NULL DEFAULT 0,  -- Budget circuit breaker
    max_budget_cents INTEGER NOT NULL DEFAULT 1000, -- $10 default max
    metadata JSONB NOT NULL DEFAULT '{}',
    started_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    CONSTRAINT chk_delegation_depth CHECK (delegation_depth >= 0)
);

CREATE INDEX idx_agent_conversations_project ON agent_conversations(project_id);
CREATE INDEX idx_agent_conversations_parent ON agent_conversations(parent_conversation_id);
CREATE INDEX idx_agent_conversations_status ON agent_conversations(status);
```

### 4.3 agent_messages

```sql
CREATE TABLE agent_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES agent_conversations(id),
    parent_message_id UUID REFERENCES agent_messages(id),  -- Thread support
    sender_type VARCHAR(20) NOT NULL,               -- user/agent/system
    sender_id VARCHAR(100) NOT NULL,
    recipient_id VARCHAR(100),
    content TEXT NOT NULL,
    mentions JSONB NOT NULL DEFAULT '[]',            -- TinyClaw: [@agent: message] tags
    message_type VARCHAR(20) NOT NULL,               -- request/response/mention/system/interrupt
    queue_mode VARCHAR(20) NOT NULL,                 -- How this message was queued
    processing_status VARCHAR(20) NOT NULL DEFAULT 'pending',  -- pending/processing/completed/failed/dead_letter
    processing_lane VARCHAR(50) NOT NULL,            -- Lane for concurrency control
    dedupe_key VARCHAR(100),                         -- Idempotency (UNIQUE)
    correlation_id UUID NOT NULL DEFAULT gen_random_uuid(),  -- Request tracing
    token_count INTEGER,
    latency_ms INTEGER,
    provider_used VARCHAR(20),
    failover_reason VARCHAR(20),                     -- auth/format/rate_limit/billing/timeout/unknown
    -- Dead-letter (part of Lane Contract)
    failed_count INTEGER NOT NULL DEFAULT 0,
    last_error TEXT,
    next_retry_at TIMESTAMP WITH TIME ZONE,
    evidence_id UUID,                                -- FK to gate_evidence (nullable)
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_dedupe_key UNIQUE (dedupe_key)
);

CREATE INDEX idx_agent_messages_conversation ON agent_messages(conversation_id);
CREATE INDEX idx_agent_messages_lane_status ON agent_messages(processing_lane, processing_status);
CREATE INDEX idx_agent_messages_retry ON agent_messages(next_retry_at) WHERE processing_status = 'pending';
CREATE INDEX idx_agent_messages_dead_letter ON agent_messages(processing_status) WHERE processing_status = 'dead_letter';
```

---

## 5. Pattern Absorption Matrix

### 5.1 OpenClaw Patterns (7 core + 4 CTO-discovered)

| # | Pattern | Source | P0/P1/P2 | Target |
|---|---------|--------|----------|--------|
| 1 | Gateway Control Plane | `src/gateway/server-methods.ts` | P1 | Typed WebSocket protocol upgrade |
| 2 | Plugin-Based Channels | `src/channels/plugins/types.*.ts` | P1 | OTT Gateway ChannelPlugin interface |
| 3 | Lane-Based Concurrency | `src/process/command-queue.ts` | **P0** | `message_queue.py` with SKIP LOCKED |
| 4 | FailoverError Classification | `src/agents/failover-error.ts` | **P0** | `failover_classifier.py` (6 reasons) |
| 5 | Subagent Session Inheritance | `src/commands/agent/session.ts` | **P0** | `parent_conversation_id` FK |
| 6 | Message Queue Modes (7) | `src/config/types.queue.ts` | **P0** (3 of 7) | queue/steer/interrupt |
| 7 | Session Scoping (2) | `src/config/sessions/types.ts` | **P0** | per-sender/global |
| 8 | Security Audit System | `src/security/audit.ts` | P2 | Security finding lifecycle |
| 9 | Prompt Injection Protection | `src/security/external-content.ts` | **P0** | `input_sanitizer.py` (12 regex) |
| 10 | Per-Channel Retry | `src/infra/retry-policy.ts` | P1 | OTT plugin retry policies |
| 11 | DM Pairing Policy | `src/channels/pairing/` | P2 | Unknown sender approval |

### 5.2 TinyClaw Patterns (7)

| # | Pattern | Source | P0/P1/P2 | Target |
|---|---------|--------|----------|--------|
| 1 | File-based message queue | `queue-processor.ts` | **P0** | Atomic ops pattern in `message_queue.py` |
| 2 | @mention routing | `lib/routing.ts` | **P0** | `mention_parser.py` |
| 3 | Conversation state tracking | `queue-processor.ts` | **P0** | `conversation_tracker.py` (50-msg, branches) |
| 4 | Provider abstraction | `lib/invoke.ts` | **P0** | `agent_invoker.py` multi-provider |
| 5 | SDLC role templates | `lib/types.ts` | **P0** | `sdlc_role` enum in `agent_definitions` |
| 6 | Hot-reload config | `settings.json` | P1 | Redis pub/sub invalidation |
| 7 | Team events | `queue-processor.ts` | P1 | WebSocket agent event broadcast |

### 5.3 Nanobot Patterns (6)

| # | Pattern | Source | P0/P1/P2 | Target |
|---|---------|--------|----------|--------|
| N1 | Two-Layer Memory | `nanobot/agent/memory.py` | P1 | `long_term_memory` JSONB + consolidation |
| **N2** | **Subagent Isolation** | `nanobot/agent/subagent.py` | **P0** | `max_delegation_depth`, `allowed_tools`, `denied_tools`, `can_spawn_subagent`, `allowed_paths` |
| **N3** | **Error-as-String** | `nanobot/agent/tools/registry.py` | **P0** | Design principle in `agent_invoker.py` |
| N4 | Heartbeat Wake-Up | `nanobot/heartbeat/service.py` | P1 | `heartbeat_interval_seconds` column |
| N5 | Progressive Skills | `nanobot/agent/skills.py` | P1 | `skills` JSONB column |
| **N6** | **Shell Safety Guards** | `nanobot/agent/tools/shell.py` | **P0** | `shell_guard.py` (8 deny patterns) |

---

## 6. Fourteen Non-Negotiable Conditions

### Security (6)

**#1 Least-Privilege Scopes**: `scopes=[]` = NO permissions. Legacy API keys get `["legacy:full"]`. New service accounts require explicit scope grants.

**#2 External Identity Verified**: `status = "verified"` required before OTT identity can trigger agent delegation. Unverified senders are queued for manual approval.

**#3 2FA-like OTT Approval** (P2): `APPROVE G3 #12345` confirmation message required for gate-level actions from OTT channels.

**#4 External Content Sanitization**: All OTT input wrapped before agent context injection. `input_sanitizer.py` applies 12 injection regex patterns (from OpenClaw `src/security/external-content.ts`). Patterns include:
- System prompt override: `r"(?i)(ignore|forget|disregard)\s+(previous|above|all)\s+(instructions|prompts)"`
- Role injection: `r"(?i)you\s+are\s+(now|a)\s+"`
- Delimiter escape: `r"(```|<\|im_sep\|>|<\|system\|>)"`
- Base64 payload: `r"(?i)base64[:\s]"`

**#5 Shell Command Guard** (Nanobot N6): `shell_guard.py` with 8 deny regex patterns blocks dangerous commands before execution:
- `r"rm\s+(-[rf]+\s+)*/"` -- recursive delete
- `r":\(\)\{.*\|.*&\s*\};"` -- fork bomb
- `r"(shutdown|reboot|halt|poweroff)"` -- system control
- `r"(mkfs|fdisk|dd\s+if=)"` -- disk operations
- `r">\s*/dev/sd"` -- raw disk write
- `r"chmod\s+(-R\s+)?777"` -- unsafe permissions
- `r"curl.*\|\s*(bash|sh)"` -- pipe to shell
- `r"eval\s*\("` -- eval injection

Path traversal detection. Output truncation at 10KB.

**#6 Tool-Level Workspace Restriction** (Nanobot N2): Per-agent tool permissions enforced via `tool_context.py`:
- `allowed_tools JSONB DEFAULT '["*"]'` -- whitelist (`["*"]`=all, `["read_file","write_file"]`=restricted)
- `denied_tools JSONB DEFAULT '[]'` -- blacklist (`["spawn_agent","send_message"]` for subagents)
- `can_spawn_subagent BOOLEAN DEFAULT false` -- explicit spawn permission
- `allowed_paths JSONB DEFAULT '[]'` -- workspace restriction (`["/project/src/"]`)

Enforcement: `tool_context.check_tool_permission(tool_name)` called before every tool invocation. `tool_context.check_path_allowed(file_path)` called before file operations.

### Architecture (5)

**#7 Lane-Based Queue** (includes dead-letter + deduplication): Per-agent lanes with configurable concurrency. PostgreSQL `FOR UPDATE SKIP LOCKED` for lane isolation. Redis pub/sub for notify-only wake-up. Dead-letter at `failed_count >= 3` with exponential backoff (30s, 60s, 120s). `dedupe_key` UNIQUE constraint for idempotency. See Decision 2 for full contract.

**#8 Read-Only Workspace**: Container no-root, read-only mount, patch pipeline. Agents operate in sandboxed environments with `allowed_paths` restriction.

**#9 Loop Guards (6 Limits)**:

| Guard | Default | Enforcement |
|-------|---------|-------------|
| `max_messages` | 50 | Conversation status -> `max_reached` |
| `max_tokens` | 100,000 | Token budget circuit breaker |
| `max_tool_calls` | 20 | Per-message tool invocation limit |
| `timeout_minutes` | 30 | Conversation hard timeout |
| `max_diff_size` | 10,000 lines | Reject oversized code changes |
| `max_retries_per_step` | 3 | Dead-letter after 3 failures |

**#10 Snapshot Precedence**: Definition fields snapshot into conversation on creation. Conversation copy is authoritative after creation. See Decision 1.

**#11 Canonical Protocol Owner**: Orchestrator defines the canonical message protocol. TinySDLC and OTT Gateway are clients. See Decision 4.

### Observability (3)

**#12 Identity Masquerading Audit**: `X-On-Behalf-Of-Identity` header with device logging. Every agent action records which human identity authorized it.

**#13 Token Budget Circuit Breaker**: Redis `INCRBY` for real-time tracking, DB for persistence. `current_cost_cents` vs `max_budget_cents` hard stop. When exceeded, all agents in conversation are paused immediately.

**#14 Human-in-the-Loop Interrupt**: `POST /conversations/{id}/interrupt` endpoint. Sets `status = 'paused_by_human'`. Uses `"interrupt"` queue mode to halt current agent processing.

### 3 Minimum Viable Traces

Every P0 endpoint MUST emit these 3 traces:

1. **Message Lifecycle**: `msg_created -> msg_queued -> msg_processing -> msg_completed/msg_failed/msg_dead_letter` with `correlation_id` linking all events.
2. **Provider Invocation**: `provider_selected -> provider_invoked -> provider_succeeded/provider_failed(reason) -> fallback_selected` with `provider_profile_key` and `latency_ms`.
3. **Budget Consumption**: `budget_checked -> tokens_consumed -> cost_incremented -> budget_exceeded(if)` with `conversation_id` and running totals.

---

## 7. Service Files (12 in `backend/app/services/agent_team/`)

| File | LOC | Source Pattern | Key Responsibility |
|------|-----|---------------|-------------------|
| `agent_registry.py` | ~150 | OpenClaw session scope | Agent CRUD, session scoping (per-sender/global) |
| `message_queue.py` | ~250 | OpenClaw lane queue | Lane-based SKIP LOCKED + Redis notify + dead-letter |
| `mention_parser.py` | ~80 | TinyClaw routing | Parse `[@agent: message]` tags, leader delegation |
| `conversation_tracker.py` | ~200 | TinyClaw + OpenClaw | Parent-child inheritance, 6 loop guards, token budget |
| `agent_invoker.py` | ~250 | OpenClaw failover + Nanobot N3 | Provider chain, error-as-string, cooldowns |
| `team_orchestrator.py` | ~250 | OpenClaw queue modes | P0: queue/steer/interrupt (3 of 7) |
| `evidence_collector.py` | ~120 | Both | Auto-capture with correlation_id |
| `failover_classifier.py` | ~100 | OpenClaw | 6 error reasons + abort matrix routing |
| `input_sanitizer.py` | ~60 | OpenClaw Pattern 9 | 12 injection regex patterns for OTT input |
| `shell_guard.py` | ~80 | Nanobot N6 | 8 deny patterns, path traversal, output truncation |
| `tool_context.py` | ~50 | Nanobot N2 | Tool permission checking, workspace restriction |
| `reflect_step.py` | ~40 | Nanobot | Reflect-after-tools prompt injection, self-correction |

---

## 8. OTT Gateway -- Plugin Architecture

Adopted from OpenClaw's plugin pattern. NOT 4 hardcoded channel adapters.

```typescript
interface ChannelPlugin {
  id: string;                          // "telegram", "discord", etc.
  meta: { name: string; icon: string; };
  capabilities: { threading: boolean; reactions: boolean; edits: boolean; };
  connect(): Promise<void>;
  disconnect(): Promise<void>;
  sendMessage(to: string, content: string, opts?: SendOpts): Promise<void>;
  onMessage(handler: (msg: IncomingMessage) => void): void;
}
```

**Plugin rollout**: Telegram (Sprint 178 MVP, NOTIFY-ONLY), Discord (Sprint 179), WhatsApp (Sprint 180), Zalo (Sprint 181).

---

## 9. P0/P1/P2 Scope

### P0: Core Multi-Agent (Sprint 176-177)

- **Database**: 3 tables (agent_definitions, agent_conversations, agent_messages) with all enhanced columns
- **Services**: 10 files in `agent_team/` (registry, queue, parser, tracker, invoker, classifier, sanitizer, shell_guard, tool_context, reflect_step)
- **Endpoints**: 5 minimal (definitions CRUD, conversations start, messages send/get)
- **Exit Criteria**: ADR-055 Initializer -> Coder -> Reviewer verified as multi-agent with parent-child sessions

### P1: Collaboration + OTT Notify (Sprint 178)

- **Services**: +2 (team_orchestrator, evidence_collector)
- **OTT Gateway**: Plugin scaffold + Telegram plugin (NOTIFY-ONLY)
- **Exit Criteria**: Telegram notifications in Vietnamese SME pilot

### P2: OTT Approval + Expansion (Sprint 179+)

- OTT approval with identity verification
- Discord/WhatsApp/Zalo plugins
- Session scoping for group chats (per-chat, per-channel via key derivation)

---

## 10. Nanobot Addendum -- 5 P0 Micro-Patterns

These patterns add **+170 LOC across 3 new files** without changing the core architecture. Expert consensus: "Nanobot patterns are defensive layers that complement the OpenClaw foundation."

### 10.1 Tool Context Routing (`tool_context.py` ~50 LOC)

```python
class ToolContext(BaseModel):
    """Context injected into every tool invocation for permission checking."""
    channel: str                        # web/cli/extension/telegram
    chat_id: str | None = None          # OTT chat identifier
    thread_id: str | None = None        # Thread within chat
    sender_id: str                      # Human or agent ID
    origin_conversation_id: UUID        # Root conversation for audit trail

    def check_tool_permission(self, tool_name: str, definition: AgentDefinition) -> bool:
        if tool_name in definition.denied_tools:
            return False
        if definition.allowed_tools == ["*"]:
            return True
        return tool_name in definition.allowed_tools

    def check_path_allowed(self, file_path: str, definition: AgentDefinition) -> bool:
        if not definition.allowed_paths:
            return True  # No restriction if empty
        return any(file_path.startswith(p) for p in definition.allowed_paths)
```

### 10.2 Shell Command Guard (`shell_guard.py` ~80 LOC)

```python
DENY_PATTERNS: list[re.Pattern] = [
    re.compile(r"rm\s+(-[rf]+\s+)*/"),
    re.compile(r":\(\)\{.*\|.*&\s*\};"),
    re.compile(r"(shutdown|reboot|halt|poweroff)"),
    re.compile(r"(mkfs|fdisk|dd\s+if=)"),
    re.compile(r">\s*/dev/sd"),
    re.compile(r"chmod\s+(-R\s+)?777"),
    re.compile(r"curl.*\|\s*(bash|sh)"),
    re.compile(r"eval\s*\("),
]

MAX_OUTPUT_SIZE = 10 * 1024  # 10KB

def guard_command(command: str, allowed_paths: list[str]) -> tuple[bool, str]:
    """Returns (allowed, reason). Check deny patterns + path traversal."""
    for pattern in DENY_PATTERNS:
        if pattern.search(command):
            return False, f"Blocked by deny pattern: {pattern.pattern}"
    if ".." in command:
        return False, "Path traversal detected"
    for path in allowed_paths:
        if not any(token.startswith(path) for token in command.split()):
            pass  # Path check is advisory, not blocking for non-file commands
    return True, "OK"

def truncate_output(output: str) -> str:
    """Truncate command output to MAX_OUTPUT_SIZE."""
    if len(output) > MAX_OUTPUT_SIZE:
        return output[:MAX_OUTPUT_SIZE] + f"\n... truncated ({len(output)} bytes total)"
    return output
```

### 10.3 Reflect-After-Tools (`reflect_step.py` ~40 LOC)

```python
REFLECT_PROMPT = (
    "Review the tool results above. Were there any errors or unexpected outcomes? "
    "If so, explain what went wrong and suggest a corrected approach. "
    "If everything looks correct, confirm and proceed."
)

def should_reflect(tool_results: list[dict], batch_index: int, frequency: int) -> bool:
    """Determine if reflection step should be injected."""
    if frequency == 0:
        return False
    if any(r.get("error") for r in tool_results):
        return True  # Always reflect on errors
    return (batch_index % frequency) == 0

def inject_reflection(messages: list[dict], tool_results: list[dict]) -> list[dict]:
    """Append reflection prompt after tool results."""
    summary = "\n".join(
        f"- {r['tool']}: {'ERROR: ' + r['error'] if r.get('error') else 'OK'}"
        for r in tool_results
    )
    messages.append({
        "role": "user",
        "content": f"Tool execution summary:\n{summary}\n\n{REFLECT_PROMPT}"
    })
    return messages
```

### 10.4 Configuration

`reflect_frequency` in `agent_definitions`:
- `1` = reflect after every tool batch (Nanobot default, safest)
- `3` = reflect every 3rd batch (balanced)
- `0` = disabled (fastest, no self-correction overhead)

---

## 11. CTO Corrections Applied (8 from OpenClaw Review)

| # | Issue | Before | After |
|---|-------|--------|-------|
| 1 | Session scope count | 4 explicit types | **2** (per-sender/global); group isolation via key derivation |
| 2 | Queue mode count | 5 modes | **7** modes; P0 implements **3** (queue/steer/interrupt) |
| 3 | FailoverReason count | 5 reasons | **6** reasons (added `unknown` catch-all) |
| 4 | AI Council status | Unfreeze for agent_invoker | **FROZEN** -- build lighter `agent_invoker.py` instead |
| 5 | Team model conflict | Replace ai_agent role | **Dual-registration**: agent_definitions (config) + team_members (membership) |
| 6 | EventBus integration | Bridge all three systems | **Skip P0** -- use WebSocketManager.broadcast directly |
| 7 | Input sanitization | Not in plan | **Added**: `input_sanitizer.py` with 12 regex patterns |
| 8 | Per-channel retry | Not in plan | **Added**: OTT plugins carry own retry policies (P1) |

---

## 12. Sprint Plan

### Sprint 176 (Mar 17-28): ADR-055 + Multi-Agent Foundation
- Days 1-5: Initializer Agent + Gate G1 (ADR-055)
- Day 6: This ADR-056 + DB migration (3 P0 tables)
- Day 7: Service account auth + least-privilege scopes
- Days 8-10: Feature flag + regression

### Sprint 177 (Mar 31 - Apr 11): Multi-Agent Services
- Days 1-4: Coding Agent + G2/G3 (ADR-055)
- Day 5: `message_queue.py` (lane-based) + `failover_classifier.py`
- Day 6: `conversation_tracker.py` + Nanobot trio (`shell_guard.py`, `tool_context.py`, `reflect_step.py`)
- Day 7: `mention_parser.py` + `agent_registry.py` + `input_sanitizer.py`
- Day 8: `agent_invoker.py` (failover + cooldowns + error-as-string)
- Days 9-10: 5 P0 API endpoints + unit tests

### Sprint 178 (Apr 14-25): Multi-Agent Complete + OTT Notify MVP
- Days 1-2: `team_orchestrator.py` + `evidence_collector.py`
- Days 3-5: Human-in-the-Loop interrupt + external identity + G4 policy
- Days 6-7: OTT Gateway scaffold + Telegram plugin (NOTIFY-ONLY)
- Days 8-10: Vietnamese SME Pilot + demo

---

## 12.5 SASE Role Classification (SDLC 6.0.6 Enterprise Tier)

> **Added**: Sprint 176 design review. Expands `sdlc_role` from 8 → 12 values.
> **Authority**: CTO Approved (5 amendments applied).
> **Reference**: SASE Framework (arXiv:2509.06216v2), SDLC 6.0.6 Section 7.

### 12.5.1 Role Progression

The `sdlc_role` field in `agent_definitions` has evolved across sprints:

| Sprint | Count | Roles Added | Trigger |
|--------|-------|-------------|---------|
| 176 (initial) | 6 | pm, architect, coder, reviewer, tester, devops | ADR-056 Phase 1 |
| 176 (P0 fix) | 8 | + researcher, pjm | TinySDLC 6.0.6 compatibility (s176_002 migration) |
| 177 (planned) | 12 | + ceo, cpo, cto, assistant | SASE Enterprise tier (this section, s177_001 migration) |

### 12.5.2 Three-Type Taxonomy

All 12 roles are classified into 3 types. The type is **derivable from the role value** — no extra column needed.

| Type | Roles | SASE Reference | Environment | Authority |
|------|-------|---------------|-------------|-----------|
| **SE4A** | researcher, pm, pjm, architect, coder, reviewer, tester, devops | arXiv:2509.06216v2 | AEE (Agent Execution) | Delegated by SE4H |
| **SE4H** | ceo, cpo, cto | arXiv:2509.06216v2 | ACE (Agent Command) | VCR authority, final approval |
| **Router** | assistant | Orchestrator-specific | Both | No authority, guidance only |

**Derivation logic** (no DB column, computed in application):
```python
SE4H_ROLES = {"ceo", "cpo", "cto"}
ROUTER_ROLES = {"assistant"}
# All other roles → SE4A (default)
```

### 12.5.3 SE4H Role Definition (CTO Amendment #1)

SE4H entries in `agent_definitions` are **AI advisors that SUPPORT human SE4H decision-makers** — they are NOT the humans themselves. Since `agent_definitions` is an agent configuration table, SE4H rows represent AI assistants configured to serve the CEO, CPO, or CTO roles:

- **ceo**: AI advisor for strategic decisions, roadmap synthesis, market analysis
- **cpo**: AI advisor for product decisions, user research summaries, prioritization drafts
- **cto**: AI advisor for architectural decisions, security analysis, technical debt assessment

The actual human CEO/CPO/CTO retains:
- Final decision authority (VCR — Verify, Correct, Ratify)
- Approval of all shipped code
- Accountability for all agent outputs

### 12.5.4 SE4H Behavioral Constraints (CTO Amendment #5)

SE4H agent definitions MUST enforce stricter safety controls than SE4A agents:

| Constraint | SE4H Value | SE4A Default | Rationale |
|-----------|-----------|-------------|-----------|
| `max_delegation_depth` | `0` | `1` | SE4H agents do not delegate to sub-agents |
| `can_spawn_subagent` | `false` | `false` | No autonomous spawning |
| `allowed_tools` | Read-only subset | `["*"]` | Advisory output only — no write operations |
| `queue_mode` | `queue` | `queue` | No interrupt/steer for advisory agents |
| Output format | Analysis/summary/draft | Executable code/actions | SE4H output requires human review before action |

**Enforcement**: Application-layer validation in `agent_registry.py` (Sprint 177). When `sdlc_role ∈ SE4H_ROLES`:
- Reject `max_delegation_depth > 0`
- Reject `can_spawn_subagent = true`
- Warn if `allowed_tools` contains write operations

### 12.5.5 Router Role Definition

The `assistant` role is a **routing agent** that:
- Guides users unfamiliar with SDLC Framework to the correct agent or workflow
- Explains available SDLC stages, gates, and agent capabilities
- Has no decision authority — purely informational/navigational
- Uses a fast, low-cost model (local inference preferred)

### 12.5.6 Model Routing Recommendations (CTO Amendment #4)

Model assignments use **abstract capability tiers** rather than version-pinned strings. Concrete model IDs are configured at deployment time, not hardcoded in schemas.

| Tier | Capability | Example Models (Feb 2026) | Used By |
|------|-----------|--------------------------|---------|
| **Tier 1: Deep Reasoning** | Strategic analysis, architecture review | claude-opus-4, deepseek-r1:32b | ceo, cto, architect, reviewer |
| **Tier 2: Fast Reasoning** | Product analysis, code generation, synthesis | claude-sonnet-4, qwen3:32b, qwen3-coder:30b | cpo, researcher, pm, coder, tester |
| **Tier 3: Fast Execution** | Coordination, routing, simple tasks | qwen3:14b, qwen3:8b | pjm, devops, assistant |

**Implementation**: `ROLE_MODEL_DEFAULTS` mapping lives in `backend/app/services/agent_team/config.py` (Sprint 177), NOT in `schemas/agent_team.py`. Schemas define data shape; model routing is business logic (CTO Amendment #2).

**SE4H model preference**: SE4H roles (ceo, cpo, cto) default to cloud providers (Anthropic) for best reasoning quality. SE4A roles default to local Ollama for cost efficiency ($50/month). This is a **recommendation**, not a constraint — all roles can use any configured provider.

---

## 13. Consequences

### Positive
- ADR-055's Initializer -> Coder -> Reviewer becomes a production-grade multi-agent workflow
- Lane-based queue provides serialization guarantees per agent while allowing cross-agent parallelism
- Provider failover with 6 classified error types prevents AI Council unfreezing complexity
- Nanobot safety patterns (shell guard, tool restrictions) prevent runaway agent behavior
- Plugin-based OTT Gateway scales to 30+ channels without core code changes
- Error-as-string enables LLM self-correction, reducing human intervention

### Negative
- 28 new files increase codebase surface area
- Lane-based queue adds PostgreSQL load (SKIP LOCKED queries)
- Redis dependency for provider cooldowns (mitigated: DB fallback for persistence)
- OTT Gateway as Node.js sidecar introduces polyglot operations

### Neutral
- AI Council remains FROZEN -- future capability but not blocker
- TinySDLC/Framework updates are methodology-only (no code dependency)
- P2 features (OTT approval, group scoping) are well-defined but not committed

---

## 14. Files Summary

### New Files (28)

**Multi-Agent Team Engine (13)**: `backend/app/services/agent_team/` -- `__init__.py`, `agent_registry.py`, `message_queue.py`, `mention_parser.py`, `conversation_tracker.py`, `agent_invoker.py`, `team_orchestrator.py`, `evidence_collector.py`, `failover_classifier.py`, `input_sanitizer.py`, `shell_guard.py`, `tool_context.py`, `reflect_step.py`

**Models/Routes/Schemas (8)**: `agent_definition.py`, `agent_conversation.py`, `agent_state.py`, `integration_event.py`, `external_identity.py`, `schemas/agent_team.py`, `routes/agent_team.py`, `alembic/versions/xxx_agent_team.py`

**OTT Gateway (5)**: `gateway.ts`, `plugin-loader.ts`, `plugins/telegram/adapter.ts`, `orchestrator-client.ts`, `Dockerfile`

**Tests & Docs (2)**: `test_agent_team.py`, this ADR

### Modified Files (5)

`user.py` (APIKey scopes), `dependencies.py` (require_scopes), `api_keys.py` (service accounts), `main.py` (router registration), `models/__init__.py` (model registration)
