# TinySDLC → SDLC Orchestrator: Knowledge Transfer

**Date**: 2026-02-19
**From**: TinySDLC Team (S04 Sprint Close)
**To**: SDLC Orchestrator Team (EP-07 Multi-Agent Team Engine)
**Relevance**: Sprint 179 — ZeroClaw Hardening (PROPOSED)

---

## TL;DR

TinySDLC S04 vừa ship **5 ZeroClaw patterns** (A/B/C/E/F) dưới dạng production-proven TypeScript modules. Đây là **reference implementations** cho Sprint 179. Ngoài ra, community release của TinySDLC sẽ **cắt 3 features** và chuyển toàn bộ sang SDLC Orchestrator — vì Orchestrator sẽ **embed full TinySDLC** (không chỉ patterns).

---

## 1. ZeroClaw Patterns — Reference Implementations từ TinySDLC S04

Sprint 179 plan implement A+C+B+E. TinySDLC S04 đã implement **A+C+B+E+F** — có thể dùng làm reference trực tiếp.

| Pattern | TinySDLC File | LOC | Status | Sprint 179 Alignment |
|---------|--------------|-----|--------|---------------------|
| A: Credential Scrubbing | `src/lib/credential-scrubber.ts` | 73 | ✅ Ship-ready | → EP-07 output scrubbing |
| C: Environment Scrubbing | `src/lib/env-scrubber.ts` | 114 | ✅ Ship-ready | → EP-07 subprocess env |
| B: History Compaction | `src/lib/history-compactor.ts` | 128 | ✅ Ship-ready | → EP-07 conversation mgmt |
| E: Query Classification | `src/lib/query-classifier.ts` | 126 | ✅ Ship-ready | → EP-07 routing layer |
| F: Processing Status | `src/lib/processing-status.ts` | 139 | ✅ Ship-ready | → (bonus, no Sprint 179 item) |

**Reference path**: `/home/nqh/shared/tinysdlc/src/lib/`

### Quan trọng — Các fix đã được áp dụng trong TinySDLC:

**Pattern A (Credential Scrubber)**:
- Regex threshold: `{16,}` (không phải `{20,}`) cho `sk-ant-` và `sk-proj-` — 18-char keys thực tế không match với `{20,}`
- Log prefix: `[CRED-SCRUB]` (không phải `[CREDENTIAL-SCRUB]`)
- 11 patterns: AWS, Anthropic, OpenAI, GitHub, Slack, generic API key, Bearer, password fields, connection strings, PEM, generic sk- fallback

**Pattern C (Environment Scrubber)**:
- `SENSITIVE_EXACT` dùng `Set<string>` (O(1) lookup, không phải `string[]`)
- PRESERVE_LIST bắt buộc phải có `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `CODEX_API_KEY` — thiếu sẽ làm tất cả agent CLI fail auth
- 8 suffix patterns: `_SECRET`, `_TOKEN`, `_PASSWORD`, `_PASS`, `_API_KEY`, `_PRIVATE_KEY`, `_CREDENTIAL`, `_CREDENTIALS`
- CTO fix: Provider auth keys phải trong PRESERVE_LIST (phát hiện khi test thực tế)

**Pattern E (Query Classifier)**:
- Entity list mở rộng: `function|class|module|component|feature|api|endpoint|service|test|script|file|page|app|bot|tool|plugin|widget|form|button|route|handler`
- Allow intermediate words: `(?:\w+\s+){0,3}` — "implement a login page" → `code_request` (không phải `unknown`)
- Confidence boosting: mỗi pattern match thêm +0.05, "what time is it?" = 0.75 (2 patterns) không phải 0.70

**Pattern F (Processing Status)**:
- `elapsedMs` phải tính client-side (`Date.now() - startedAt`), không đọc từ file (stale)
- `formatStatusMessage(status, nowMs?)` nhận optional `nowMs` param
- CTO fix: elapsed computation là critical — file-based elapsed không reliable

---

## 2. Features CUT từ TinySDLC Community → Chuyển sang SDLC Orchestrator

TinySDLC community release sẽ là bản **tối giản** (LITE tier, 1-2 devs). 3 features sau đây không phù hợp với "tiny" positioning — sẽ sống trong SDLC Orchestrator thay thế:

### 2.1 `protocol-adapter.ts` (174 LOC) — ENTERPRISE PROTOCOL TRANSLATION

```typescript
// Hiện tại trong TinySDLC:
export function toCanonical(msg: MessageData, agentId: string): CanonicalAgentMessage { ... }
export function fromCanonical(msg: CanonicalAgentMessage): Partial<MessageData> { ... }
export function responseToCanonical(response: string, agentId: string): CanonicalAgentMessage { ... }
```

**Lý do chuyển**:
- Zero imports trong TinySDLC hiện tại — chưa được dùng ở đâu
- Gated bởi `orchestrator_integration.enabled` (default: false)
- Logic này thuộc về Orchestrator integration layer — Orchestrator là canonical owner
- Blocker: ADR-056 (chưa finalized)

**Action cho Orchestrator**:
- Tích hợp vào `backend/app/services/agent_bridge/` hoặc tương đương
- Orchestrator side cần: nhận `QueueMessage` từ TinySDLC → translate sang internal format
- TinySDLC side: chỉ cần gửi raw `QueueMessage` qua REST API khi `orchestrator_integration.enabled`

**File reference**: `/home/nqh/shared/tinysdlc/src/lib/protocol-adapter.ts`

---

### 2.2 `query-classifier.ts` (126 LOC) — QUERY ANALYTICS / INTELLIGENT ROUTING

```typescript
// Categories: command | question | code_request | file_operation | conversation | unknown
export function classifyQuery(message: string): ClassifyResult { ... }
// ClassifyResult: { category, confidence, signals }
```

**Lý do chuyển**:
- Trong TinySDLC: **informational only** — log category nhưng không có routing decision nào dựa vào
- Trong Orchestrator: có thể thực sự route đến different models (Opus vs Haiku), different agent pools, hoặc cache simple queries
- EP-07 engine có đủ context để act on classification

**Giá trị thực trong Orchestrator**:
- `command` → route to command handler (no LLM needed)
- `question` → route to Haiku (cost saving)
- `code_request` → route to Opus/Sonnet (quality)
- `file_operation` → route to tool-capable agent
- Confidence threshold: skip LLM nếu `command` với confidence 1.0

**File reference**: `/home/nqh/shared/tinysdlc/src/lib/query-classifier.ts`

---

### 2.3 `history-compactor.ts` (128 LOC) — CONVERSATION COMPACTION

```typescript
// Extractive summarization: first paragraph + truncation, no LLM
export function compactHistory(responses: AgentResponse[], config: CompactionConfig): CompactionResult { ... }
export const DEFAULT_COMPACTION_CONFIG: CompactionConfig = {
    compactionThreshold: 10,  // responses before compaction
    preserveRecent: 5,        // always keep last N intact
    maxSummaryLength: 200,    // chars for compacted entry
};
```

**Lý do chuyển**:
- TinySDLC LITE: 200K context window, 50-msg hard cap → vấn đề không xảy ra ở scale này
- Orchestrator PROFESSIONAL/ENTERPRISE: multi-agent chains, cross-sprint context, long-running conversations → cần compaction thực sự
- Orchestrator có thể nâng lên LLM-based summarization (TinySDLC dùng extractive để zero latency/cost)

**Nâng cấp đề xuất trong Orchestrator**:
- Giữ extractive method làm fast path (zero cost)
- Thêm LLM summarization khi `conversation.budget_remaining > threshold` (chất lượng cao hơn)
- Store compacted summaries trong Evidence Vault (audit trail)

**File reference**: `/home/nqh/shared/tinysdlc/src/lib/history-compactor.ts`

---

## 3. SDLC Orchestrator sẽ Embed Full TinySDLC

Quyết định kiến trúc: SDLC Orchestrator **không chỉ port patterns** — sẽ embed toàn bộ TinySDLC như một sub-system. Điều này có nghĩa:

```
SDLC Orchestrator (Enterprise)
├── EP-07: Multi-Agent Team Engine
│   ├── TinySDLC (embedded, full feature set)  ← embed here
│   │   ├── File-based queue (atomic operations)
│   │   ├── Multi-channel (Discord/Telegram/WhatsApp/Zalo)
│   │   ├── [@teammate: message] routing
│   │   ├── 8 SE4A agent templates (SDLC v6.1.0)
│   │   ├── ZeroClaw patterns (A+C+E+F) ← security kept in TinySDLC
│   │   └── Processing status signaling
│   │
│   └── Orchestrator Extensions (add-on to TinySDLC)
│       ├── protocol-adapter (canonical protocol translation)
│       ├── query-classifier → intelligent routing
│       ├── history-compactor → Evidence Vault integration
│       ├── Budget control (max_budget_cents per conversation)
│       ├── Parent-child conversation inheritance
│       └── Multi-team coordination (cross-team messaging)
│
└── Other EPs (Gate Engine, Evidence Vault, IR Codegen...)
```

**TinySDLC community version** = stripped-down subset:
- Keeps: queue, channels, routing, 4 security modules, processing status, agent templates
- Removes: protocol-adapter, query-classifier, history-compactor
- Adds: clear documentation to upgrade path → SDLC Orchestrator

---

## 4. Agent Templates — Cập nhật SDLC v6.1.0

8 SE4A agent templates trong `templates/agents/` vừa được nâng cấp. Đây là pattern cho SDLC Orchestrator's agent AGENTS.md generation:

### 4.1 Cấu trúc 3-Zone (Context Authority Methodology)

```markdown
## Zone 1 (Static): Role definition, constraints, SDLC policies
## Zone 2 (Semi-Dynamic): Setup Activity — agent fills on first run
## Zone 3 (Dynamic): SDLC Context — PJM/system updates at gate transitions

<!-- SDLC-CONTEXT-START -->
Stage: [current stage]
Gate: [current gate status]
Mode: [LITE | STANDARD | PROFESSIONAL | ENTERPRISE] GOVERNANCE
Sprint: [current sprint]
[role-specific fields]
Updated: [YYYY-MM-DD by pjm | auto by orchestrator]
<!-- SDLC-CONTEXT-END -->
```

**Orchestrator enhancement**: Zone 3 có thể được auto-updated bởi Orchestrator khi gate status thay đổi — đây là `Context Authority Methodology` đã được document trong `.sdlc-framework/02-Core-Methodology/SDLC-Context-Authority-Methodology.md`.

### 4.2 Handoff Protocol đã được formalize trong mỗi template

Mỗi role có explicit Handoff Protocol block:

```
researcher → pm (research brief → G0.1)
pm → architect (requirements → feasibility)
pm → pjm (G1 approved → sprint planning)
architect → coder (ADR + contracts → G2)
coder → reviewer ([APPROVED] sprint gate)
reviewer → tester (G3 primary sign-off)
tester → devops (G3 co-sign → deploy auth)
devops → SE4H (G4 production metrics)
```

### 4.3 CTO-Approved (2026-02-19)

- 8/8 templates: SDLC Context zone ✅
- 8/8 templates: Handoff Protocol ✅
- P0 fix applied: `05-Integrate` → `05-Verify` (stage naming)
- 2 P1 items in backlog: PJM coordinator handoff, Reviewer DoD

**Template path**: `/home/nqh/shared/tinysdlc/templates/agents/`

---

## 5. Cross-Stage Documentation Consistency — New Policy

Hai role templates (PM + PJM) đã được thêm **doc consistency enforcement**:

**PM** (`templates/agents/pm/AGENTS.md`):
- Owns doc content across all stages (00→04)
- Runs doc audit at sprint close: code ↔ docs ↔ ADRs
- Stage-by-stage checklist (Stage 00 through 04)
- Communication pattern: self-correct trivial gaps, escalate semantic gaps

**PJM** (`templates/agents/pjm/AGENTS.md`):
- Owns doc *delivery* (PM owns content)
- LITE tier self-correct: counts, log prefixes, confidence values, DoD states
- Cannot self-correct: requirements, ADR decisions, scope semantics
- Always notifies PM after self-correct

**Relevance cho Orchestrator**: Pattern này áp dụng trực tiếp cho Orchestrator's PM/PJM agents khi manage multi-sprint evidence trail.

---

## 6. Action Items cho SDLC Orchestrator Team

| # | Action | Owner | Sprint | Reference |
|---|--------|-------|--------|-----------|
| 1 | Port `credential-scrubber.ts` + `env-scrubber.ts` vào EP-07 (reference implementation từ TinySDLC) | EP-07 team | Sprint 179 | See §1 — critical fixes documented |
| 2 | Port `history-compactor.ts` với LLM upgrade option vào EP-07 | EP-07 team | Sprint 179 | See §2.3 |
| 3 | Port `query-classifier.ts` với actual routing logic vào EP-07 | EP-07 team | Sprint 179 | See §2.2 — add routing decisions |
| 4 | Design `protocol-adapter` integration point (Orchestrator side) | Architecture | Sprint 180 | See §2.1 — blocked on ADR-056 |
| 5 | Plan TinySDLC embed strategy vào EP-07 | CTO | Sprint 180 | See §3 — architecture decision needed |
| 6 | Copy Zone 3 SDLC-CONTEXT pattern vào Orchestrator AGENTS.md generator | PM/PJM | Sprint 180 | See §4.1 |

---

## 7. Files Changed in TinySDLC S04 (Complete List)

**New files** (5 ZeroClaw modules):
- `src/lib/credential-scrubber.ts` (73 LOC)
- `src/lib/env-scrubber.ts` (114 LOC)
- `src/lib/query-classifier.ts` (126 LOC)
- `src/lib/processing-status.ts` (139 LOC)
- `src/lib/history-compactor.ts` (128 LOC)

**Modified files** (integration):
- `src/queue-processor.ts` — integrated A+E+F+B patterns, periodic in-flight compaction
- `src/lib/invoke.ts` — Pattern C (env scrubbing on all spawns)
- `src/lib/types.ts` — 5 new config flags + query_category field

**Template files** (SDLC v6.1.0 upgrade):
- `templates/agents/pm/AGENTS.md` — Cross-Stage Doc Consistency section + Zone 3
- `templates/agents/pjm/AGENTS.md` — Doc delivery enforcement + self-correct rules + Zone 3
- `templates/agents/{researcher,architect,coder,reviewer,tester,devops}/AGENTS.md` — Zone 3 + Handoff Protocol

**Documentation**:
- `docs/01-planning/sprint-plan-zeroclaw-patterns.md` — sprint plan with corrected ACs
- `docs/02-design/adr-zeroclaw-security-patterns.md` — ADR-008 through ADR-012
- `docs/01-planning/requirements.md` — ZeroClaw requirements section

---

**Trạng thái**: TinySDLC S04 CLOSED — CTO Approved 2026-02-19
**Next**: Community release (cắt 3 modules) → SDLC Orchestrator embed (full TinySDLC)
