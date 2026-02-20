---
sdlc_version: "6.1.0"
document_type: "Functional Requirement"
status: "PROPOSED"
sprint: "176"
spec_id: "FR-037"
tier: "PROFESSIONAL"
stage: "01 - Planning"
---

# FR-037: Multi-Agent Conversation Management

**Version**: 1.0.0
**Status**: PROPOSED
**Created**: February 2026
**Sprint**: 176-177
**Framework**: SDLC 6.1.0
**Epic**: EP-07 Multi-Agent Team Engine
**ADR**: ADR-056 (Decision 1: Snapshot Precedence)
**Owner**: Backend Team

---

## 1. Overview

### 1.1 Purpose

Implement multi-agent conversation lifecycle management with parent-child session inheritance, snapshot precedence, and 6 loop guards. Agents communicate through typed messages within conversations that enforce budget and message limits.

### 1.2 Business Value

- Enables agent-to-agent delegation (Initializer → Coder → Reviewer)
- Prevents runaway agent costs via per-conversation budget circuit breaker
- Prevents infinite loops via 6 configurable loop guards
- Supports parent-child sessions for delegation depth tracking

### 1.3 Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Conversation create latency | <50ms p95 | pytest-benchmark |
| Loop guard enforcement | 100% | 13 unit tests (CL-01 to CL-13) |
| Budget circuit breaker | 100% | CL-07 + MA-03 tests |
| Snapshot immutability | 100% | MA-02 test |

---

## 2. Functional Requirements

### 2.1 Conversation Creation

**GIVEN** a valid agent definition exists
**WHEN** a user or agent creates a conversation via `POST /api/v1/agent-team/conversations`
**THEN** the system SHALL:
1. Snapshot `max_messages`, `max_budget_cents`, `queue_mode`, `session_scope` from the agent definition into the conversation
2. Set `delegation_depth = parent.delegation_depth + 1` if `parent_conversation_id` is provided, else `0`
3. Set `status = 'active'`
4. Return the conversation with all snapshotted fields

### 2.2 Snapshot Precedence (Decision 1)

**GIVEN** a conversation has been created with snapshotted fields
**WHEN** the agent definition is subsequently modified
**THEN** the conversation's snapshotted fields SHALL NOT change (immutable after creation)

### 2.3 Loop Guards (Non-Negotiable #9)

**GIVEN** an active conversation
**WHEN** any of the following limits are reached:
- `total_messages >= max_messages` (default 50)
- `total_tokens >= 100,000`
- `tool_call_count >= 20` per message
- `timeout_minutes >= 30`
- `diff_lines >= 10,000`
- `failed_count >= 3` per step (dead-letter)

**THEN** the system SHALL:
1. Transition conversation status to `max_reached`
2. Halt all agent processing for this conversation
3. Log the specific limit violation

### 2.4 Budget Circuit Breaker (Non-Negotiable #13)

**GIVEN** an active conversation
**WHEN** `current_cost_cents >= max_budget_cents`
**THEN** the system SHALL:
1. Pause ALL agents in this conversation (including child conversations)
2. Transition status to `max_reached`
3. Budget check has HIGHEST priority (checked before other limits)

### 2.5 Delegation Depth (Non-Negotiable #6)

**GIVEN** an agent with `max_delegation_depth = N`
**WHEN** a spawn request is made from a conversation with `delegation_depth >= N`
**THEN** the system SHALL reject the spawn with `LimitViolation.MAX_DELEGATION_DEPTH`

### 2.6 Conversation Completion

**GIVEN** an active conversation
**WHEN** all agent tasks are complete OR a human interrupts
**THEN** the system SHALL:
1. Set `status = 'completed'` or `'paused_by_human'`
2. Set `completed_at = NOW()`
3. Total tokens and cost are final

---

## 3. Non-Functional Requirements

| Requirement | Target |
|------------|--------|
| Conversation table row size | <2KB average |
| Max concurrent conversations per project | 100 |
| Max conversation duration | 30 minutes (configurable) |
| Audit trail | All status transitions logged |

---

## 4. Test Coverage

| Test ID | Description | Non-Negotiable |
|---------|-------------|---------------|
| CL-01 to CL-09 | Loop guard tests | #9 |
| CL-10 to CL-13 | Delegation depth tests | #6 |
| MA-01 | Parent-child session | — |
| MA-02 | Snapshot precedence | Decision 1 |
| MA-03 | Budget circuit breaker | #13 |

---

## 5. Dependencies

- `agent_definitions` table (agent templates)
- `agent_conversations` table (conversation state)
- `ConversationLimits` class (`conversation_limits.py`)
- Redis for budget tracking (INCRBY)
