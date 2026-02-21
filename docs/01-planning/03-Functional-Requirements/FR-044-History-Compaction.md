---
sdlc_version: "6.1.0"
document_type: "Functional Requirement"
status: "PROPOSED"
sprint: "179"
spec_id: "FR-044"
tier: "PROFESSIONAL"
stage: "01 - Planning"
---

# FR-044: History Compaction (Auto-Summarize)

**Version**: 1.0.0
**Status**: PROPOSED
**Created**: February 2026
**Sprint**: 179
**Framework**: SDLC 6.1.0
**Epic**: EP-07 Multi-Agent Team Engine
**ADR**: ADR-058 (ZeroClaw Pattern B)
**Owner**: Backend Team
**Source**: ZeroClaw `src/agent/loop_.rs` -- threshold 50 msgs -> summarize -> keep 20 recent + 2K-char summary

---

## 1. Overview

### 1.1 Purpose

Auto-summarize conversation history when approaching the message limit instead of hard-stopping at `max_messages=50`. Preserves conversation continuity by compacting older messages into a structured summary while retaining recent messages.

### 1.2 Business Value

- Conversations no longer "die" at 50 messages -- graceful degradation via compaction
- Preserves critical context: user preferences, commitments, decisions, unresolved tasks
- Reduces token consumption by replacing verbose history with concise summary
- No new database migration required (uses existing `metadata_` JSONB column)

---

## 2. Functional Requirements

### 2.1 Compaction Trigger (CTO Amendment)

**GIVEN** a conversation has `total_messages >= max_messages * 0.8`
**WHEN** a new message is about to be added
**THEN** the system SHALL trigger history compaction
**AND** the threshold SHALL be `max_messages * 0.8` (e.g., 40 for max_messages=50)

### 2.2 Compaction Process

**GIVEN** compaction is triggered
**WHEN** `HistoryCompactor.compact()` executes
**THEN** the system SHALL:
1. Retain the last `max_messages * 0.4` messages (e.g., 20 for max_messages=50)
2. Summarize older messages using a separate fast LLM call (`qwen3:8b` per CTO)
3. Store the summary in `agent_conversations.metadata_` JSONB under key `compaction_summary`
4. Store `last_compacted_at` timestamp in `metadata_` JSONB
5. Track `compaction_count` in `metadata_` JSONB
6. NOT delete any messages from `agent_messages` table (audit trail preserved)

### 2.3 Summarizer Prompt

**GIVEN** the system invokes the summarizer LLM
**WHEN** building the summarizer prompt
**THEN** the prompt SHALL instruct: "Preserve: user preferences, commitments, decisions, unresolved tasks, key facts. Omit: filler, repeated chit-chat, verbose tool logs."
**AND** the summary SHALL be limited to 2,000 characters maximum

### 2.4 Context Injection

**GIVEN** a conversation has a `compaction_summary` in `metadata_`
**WHEN** `TeamOrchestrator._build_llm_context()` constructs the message list
**THEN** the summary SHALL be injected as the first context message (role=system)
**AND** recent messages follow the summary

### 2.5 Fallback on Summarizer Failure

**GIVEN** the summarizer LLM call fails (timeout, provider error)
**WHEN** compaction is in progress
**THEN** the system SHALL fall back to deterministic truncation:
  - Keep last `max_messages * 0.4` messages
  - Summary = "[Compaction: {N} older messages truncated due to summarizer failure]"
  - No exception raised (graceful degradation)

### 2.6 No New Migration (CTO Amendment)

**GIVEN** the `agent_conversations` table has an existing `metadata_` JSONB column
**WHEN** compaction data is stored
**THEN** the system SHALL use `metadata_` JSONB keys:
  - `compaction_summary: str` -- the summary text
  - `last_compacted_at: str` -- ISO 8601 timestamp
  - `compaction_count: int` -- number of times compacted
**AND** no new Alembic migration SHALL be created

---

## 3. Test Coverage

| Test ID | Description | Reference |
|---------|-------------|-----------|
| HC-01 | Compaction triggers at 80% threshold | ADR-058 S3 |
| HC-02 | No compaction below 80% threshold | ADR-058 S3 |
| HC-03 | Last 40% messages retained | ADR-058 S3 |
| HC-04 | Summary stored in metadata_ JSONB | ADR-058 S3 |
| HC-05 | Summary limited to 2000 chars | ADR-058 S3 |
| HC-06 | Summarizer failure triggers fallback | ADR-058 S3 |
| HC-07 | Summary injected as first system message | ADR-058 S3 |
| HC-08 | No migration needed (metadata_ JSONB) | ADR-058 S3 |
| HC-09 | Compaction count tracked | ADR-058 S3 |
| HC-10 | Messages not deleted from DB | ADR-058 S3 |

---

## 4. Dependencies

- `HistoryCompactor` class (`history_compactor.py`, new file)
- `TeamOrchestrator._build_llm_context()` (`team_orchestrator.py`, modified)
- `ConversationTracker` (`conversation_tracker.py`, modified -- compaction trigger)
- `AgentInvoker` (`agent_invoker.py`, used for summarizer LLM call)
- `agent_conversations.metadata_` JSONB column (existing, no migration)
- ZeroClaw source: `src/agent/loop_.rs` -- compaction logic
