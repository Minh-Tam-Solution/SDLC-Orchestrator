---
sdlc_version: "6.1.1"
document_type: "Sprint Plan"
status: "DRAFT — Pending CTO Approval"
sprint: "222"
tier: "PROFESSIONAL"
stage: "04 - Build"
---

# Sprint 222 — OTT @mention → EP-07 Agent Direct Routing

**Sprint Duration**: March 2026
**Sprint Goal**: Wire `@agent_name` syntax in OTT channels (Telegram, Zalo) directly into the
EP-07 TeamOrchestrator pipeline so users can invoke named agents by @mention instead of only
through keyword-based intent detection.
**Status**: DRAFT — Pending CTO Approval
**Priority**: P0 — Design Gap Fix (not a new feature)
**Framework**: SDLC 6.1.1
**ADRs**: ADR-056 (Multi-Agent Team Engine), ADR-060 (Channel-agnostic OrchestratorMessage)
**Previous Sprint**: [Sprint 221 — Group Consensus](SPRINT-221-CONSENSUS.md)
**Parallelism**: No parallel dependencies. Can start immediately after S221.
**Raised by**: @pm + @architect post-S221 design review (2026-03-05)

---

## Root Cause Analysis

### The Bug

Typing `@pjm báo cáo hiện trạng dự án` in Telegram returns:

> "I cannot directly notify the project manager. Please use the /status command..."

Instead of routing to the actual EP-07 PM agent.

### Trace to Design Decision

**1. S215-219 scope doc explicitly deferred Interface Parity:**

```yaml
# scope-sprint-215-219-mtclaw-adoption.md — Out of Scope
| Interface parity (CLI/Web/Extension/OTT) | After foundation stabilized | S220+ |
```

S220 (Memory/Feedback) and S221 (Consensus) shipped without picking this up.

**2. S219 plan had a misleading statement:**

```
# SPRINT-219-ROUTER-TSVECTOR.md line 39:
"@mention routing already works"
```

This referred to **agent-to-agent** @mention INSIDE TeamOrchestrator conversations
(mention_parser.py → delegation chain). It was NOT about OTT user → EP-07 agent routing.
The ambiguity was not caught during S219 CTO review.

**3. FR-046 used @mention as illustrative example, not spec:**

```
# FR-046-Chat-Command-Router.md
"Enables governance loop via chat: @pm create project → @reviewer approve G2"
```

The `@pm` here was an example. Actual requirements only specified 5 tool names.
No FR ever stated: "OTT user typing @name routes to AgentDefinition by that name."

### Why This Is P0

The OTT channel is declared PRIMARY interface (CEO Sprint 190 directive). The EP-07 TeamOrchestrator
pipeline (`ott_team_bridge.py`) was built in Sprint 200 and works end-to-end. The @mention routing
branch is the **last missing wire** between the OTT surface and the agent engine.

---

## What Already Works (DO NOT BREAK)

| Component | File | Status |
|-----------|------|--------|
| OTT webhook intake | `ott_gateway.py` | ✅ S181 |
| Telegram bidirectional | `telegram_responder.py` | ✅ S198 |
| Multi-agent intent detection | `ott_team_bridge.is_multi_agent_intent()` | ✅ S200 |
| OTT → TeamOrchestrator pipeline | `ott_team_bridge.handle_agent_team_request()` | ✅ S200 |
| Multi-turn conversation (Redis) | `ott_team_bridge._get_or_create_active_conversation()` | ✅ S200 |
| Agent-to-agent @mention (internal) | `mention_parser.py` | ✅ S177 |
| Delegation guard | `delegation_service.py` | ✅ S216 |

Sprint 222 adds ONE new branch in `_telegram_dispatch()` and ONE new function in
`ott_team_bridge.py`. All existing paths are preserved.

---

## Sprint Summary

| Track | Scope | Est. LOC | Impact |
|-------|-------|----------|--------|
| A | `ott_team_bridge.py`: add `handle_mention_request()` + `_find_agent_by_name_or_role()` | ~90 new | Core routing: @name/role → EP-07 agent |
| B | `ott_gateway.py`: add @mention branch to `_telegram_dispatch()` + `_zalo_dispatch()` | ~30 modify | Wire OTT → Track A |
| C | Tests: mention routing, agent not found, delegation guard, Zalo parity | ~100 new | Regression safety |
| **Total** | | **~220 LOC** | **OTT @mention fully wired to EP-07** |

---

## Track A — `ott_team_bridge.py` — handle_mention_request()

### A1: New helper `_find_agent_by_name_or_role()`

**File**: `backend/app/services/agent_bridge/ott_team_bridge.py`

Add after `_find_entry_agent()`:

```python
async def _find_agent_by_name_or_role(
    db: AsyncSession,
    project_id: UUID,
    name: str,
) -> AgentDefinition | None:
    """
    Find an active agent definition by agent_name OR sdlc_role.

    Precedence: exact agent_name match first, then role match.
    This allows both @coder-alpha (name) and @coder (role) to resolve.

    Args:
        db: Async DB session.
        project_id: Scope lookup to this project.
        name: The raw mention name (lowercased, no leading @).

    Returns:
        AgentDefinition if found and active, None otherwise.
    """
    # 1. Try exact agent_name match
    result = await db.execute(
        select(AgentDefinition).where(
            and_(
                AgentDefinition.project_id == project_id,
                AgentDefinition.agent_name == name,
                AgentDefinition.is_active.is_(True),
            )
        ).limit(1)
    )
    definition = result.scalar_one_or_none()
    if definition:
        return definition

    # 2. Try sdlc_role match (e.g. @coder → sdlc_role="coder")
    result = await db.execute(
        select(AgentDefinition).where(
            and_(
                AgentDefinition.project_id == project_id,
                AgentDefinition.sdlc_role == name,
                AgentDefinition.is_active.is_(True),
            )
        ).limit(1)
    )
    return result.scalar_one_or_none()
```

### A2: New function `handle_mention_request()`

Add after `handle_agent_team_request()`:

```python
async def handle_mention_request(
    chat_id: str | int,
    text: str,
    bot_token: str,
    sender_id: str,
    channel: str = "telegram",
) -> bool:
    """
    Route an OTT @mention to the named EP-07 agent (Sprint 222).

    Called when OTT message contains an @name pattern BEFORE the
    multi-agent intent detection. Allows users to invoke agents
    directly: "@pjm báo cáo hiện trạng" → PM AgentDefinition.

    Routing precedence (checked by caller in ott_gateway.py):
        /command        → telegram_responder (static)
        @mention        → THIS FUNCTION (direct EP-07 agent)
        multi-agent kw  → handle_agent_team_request (preset-based)
        free text       → ai_response_handler (generic Ollama)

    Args:
        chat_id:   OTT chat/user ID.
        text:      Full message text (may contain @mention + message).
        bot_token: Telegram bot token (empty for Zalo).
        sender_id: OTT user's ID.
        channel:   "telegram" or "zalo".

    Returns:
        True  — mention was resolved and agent pipeline ran (or error
                message was sent explaining why it failed).
        False — no @mention found; caller should try next branch.
    """
    from app.services.agent_team.mention_parser import MentionParser

    mentions = MentionParser.extract_mentions(text)
    if not mentions:
        return False

    project_id = await _resolve_project_id(chat_id)
    if not project_id:
        await _ott_send_progress(
            channel, bot_token, chat_id,
            "⚠️ No project configured for this chat.\n"
            "Chưa có dự án. Gửi UUID dự án hoặc liên hệ admin.",
        )
        return True  # handled — error sent, do not fall through to generic AI

    # Use first mention as the target agent (subsequent mentions are
    # handled by the agent itself via internal @mention delegation chain).
    target_name = mentions[0].name.lower()

    from app.db.session import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        definition = await _find_agent_by_name_or_role(db, project_id, target_name)

        if not definition:
            await _ott_send_progress(
                channel, bot_token, chat_id,
                f"⚠️ Agent @{target_name} không tồn tại hoặc không active "
                f"trong project này.\n\n"
                f"Dùng Web Dashboard hoặc API để xem danh sách agent đang active.",
            )
            return True  # handled — error sent

        # Acknowledge routing to the user
        await _ott_send_progress(
            channel, bot_token, chat_id,
            f"🔀 Routing → @{definition.agent_name} "
            f"({definition.sdlc_role})...",
        )

        logger.info(
            "ott_team_bridge: @mention routing chat_id=%s "
            "mention=%s → agent=%s role=%s",
            chat_id,
            target_name,
            definition.agent_name,
            definition.sdlc_role,
        )

        try:
            return await _process_agent_request(
                db=db,
                project_id=project_id,
                chat_id=chat_id,
                text=text,
                bot_token=bot_token,
                sender_id=sender_id,
                preset_name=_DEFAULT_PRESET,
                channel=channel,
                definition_override=definition,
            )
        except Exception as exc:
            logger.error(
                "ott_team_bridge: @mention pipeline error "
                "chat_id=%s agent=%s error=%s",
                chat_id,
                definition.agent_name,
                str(exc),
                exc_info=True,
            )
            await _ott_send_progress(
                channel, bot_token, chat_id,
                f"❌ Agent @{definition.agent_name} pipeline error.\n"
                f"{str(exc)[:200]}",
            )
            return True  # handled — error sent
```

### A3: Modify `_process_agent_request()` to accept `definition_override`

Add optional parameter to the existing function signature:

```python
async def _process_agent_request(
    db: AsyncSession,
    project_id: UUID,
    chat_id: str | int,
    text: str,
    bot_token: str,
    sender_id: str,
    preset_name: str,
    channel: str = "telegram",
    definition_override: AgentDefinition | None = None,  # NEW — Sprint 222
) -> bool:
```

Inside `_process_agent_request()`, replace the Step 1 block:

```python
# Step 1: Find entry-point agent
# Sprint 222: definition_override takes precedence over preset-based lookup.
# Used by handle_mention_request() for direct @name routing.
if definition_override is not None:
    definition = definition_override
else:
    definition = await _find_entry_agent(db, project_id, preset_name)
    if not definition:
        await _ott_send_progress(...)
        return False
```

**No other changes to `_process_agent_request()`.**

---

## Track B — `ott_gateway.py` — Wire @mention branch

### B1: Telegram dispatch — add @mention branch

**File**: `backend/app/api/routes/ott_gateway.py`

Modify `_telegram_dispatch()`:

```python
async def _telegram_dispatch() -> None:
    """Route Telegram message: commands → responder, @mention → EP-07, free text → AI."""
    # 1. Command check — /start, /help, /status etc. (existing, unchanged)
    handled = await handle_telegram_auto_reply(raw_body)
    if handled:
        return

    # 2. @mention → direct EP-07 agent routing (Sprint 222)
    #    Checked BEFORE multi-agent intent so explicit @name always wins.
    if "@" in msg.content:
        from app.services.agent_bridge.ott_team_bridge import handle_mention_request
        routed = await handle_mention_request(
            chat_id=raw_body.get("message", {}).get("chat", {}).get("id", ""),
            text=msg.content,
            bot_token=_TELEGRAM_BOT_TOKEN,
            sender_id=msg.sender_id,
            channel="telegram",
        )
        if routed:
            return

    # 3. Multi-agent intent detection — "generate code", "analyze my..." (existing)
    if is_multi_agent_intent(msg.content):
        await handle_agent_team_request(
            chat_id=raw_body.get("message", {}).get("chat", {}).get("id", ""),
            text=msg.content,
            bot_token=_TELEGRAM_BOT_TOKEN,
            sender_id=msg.sender_id,
            channel="telegram",
        )
        return

    # 4. Generic AI fallback — Ollama qwen3:14b (existing, unchanged)
    await handle_ai_response(raw_body, _TELEGRAM_BOT_TOKEN)
```

### B2: Zalo dispatch — same @mention branch

**File**: `backend/app/api/routes/ott_gateway.py`

Same pattern applied to `_zalo_dispatch()` for channel parity:

```python
async def _zalo_dispatch() -> None:
    # 1. Command check (existing)
    handled = await handle_zalo_auto_reply(raw_body)
    if handled:
        return

    # 2. @mention → EP-07 (Sprint 222)
    if "@" in msg.content:
        from app.services.agent_bridge.ott_team_bridge import handle_mention_request
        routed = await handle_mention_request(
            chat_id=_zalo_sender_id,
            text=msg.content,
            bot_token="",
            sender_id=_zalo_sender_id,
            channel="zalo",
        )
        if routed:
            return

    # 3. Generic AI fallback (existing)
    await handle_ai_response(raw_body, "", channel="zalo")
```

---

## Track C — Tests

### C1: New test file

**File**: `backend/tests/unit/test_sprint222_ott_mention.py`

**10 test groups:**

```
S1: extract_mentions() — detect @name in OTT messages (3 tests)
    - @pjm in free text extracted correctly
    - Multiple @mentions: first is used as primary target
    - No @ in message → returns empty list → handle_mention_request returns False

S2: _find_agent_by_name_or_role() — agent resolution (3 tests)
    - Exact agent_name match found
    - Fallback to sdlc_role match when name not found
    - Neither name nor role → returns None

S3: handle_mention_request() — happy path (2 tests)
    - @pjm → PM agent found → _process_agent_request called with definition_override
    - @architect → architect agent found → pipeline routed correctly

S4: handle_mention_request() — error paths (3 tests)
    - Agent not found → error message sent, returns True (handled)
    - No project configured → error message sent, returns True (handled)
    - No @mention in text → returns False (not handled)

S5: ott_gateway dispatch — routing precedence (4 tests)
    - /command → telegram_responder (unchanged)
    - @mention → handle_mention_request called, handle_ai_response NOT called
    - Multi-agent keyword (no @) → handle_agent_team_request called
    - Plain text (no @ no keyword) → handle_ai_response called

S6: Zalo channel parity (2 tests)
    - @mention in Zalo message → handle_mention_request with channel="zalo"
    - No regression on existing Zalo flow

S7: definition_override in _process_agent_request (2 tests)
    - definition_override=agent → skips _find_entry_agent, uses override directly
    - definition_override=None → falls back to preset-based lookup (existing behavior)

S8: Delegation guard integration (2 tests)
    - @mention to agent without delegation link from caller → guard blocks, error sent
    - @mention to agent WITH delegation link → allowed, pipeline proceeds

S9: Concurrent @mention (1 test)
    - Two @mentions in same message → first mention used, second handled by agent internally

S10: Alembic chain (1 test)
    - s221_001 is present (no new migration in S222 — code-only sprint)
```

**Mocking strategy**: Same as S218-S221 pattern — `_mock_db()`, `AsyncMock`, `MagicMock` for
external dependencies. No real DB or Redis required for unit tests.

---

## Definition of Done

| # | Criterion | Verification |
|---|-----------|-------------|
| 1 | `@pjm báo cáo hiện trạng dự án` in Telegram routes to PM agent | Manual test + S5 unit tests |
| 2 | `@architect review auth flow` routes to Architect agent | Manual test |
| 3 | `@unknownagent do X` sends clear error message, does NOT fall to generic AI | S4 unit tests |
| 4 | Existing `/command` flow unchanged | S5 unit tests |
| 5 | Existing multi-agent intent flow unchanged | S5 unit tests |
| 6 | Existing generic AI fallback unchanged | S5 unit tests |
| 7 | Zalo channel has same @mention routing | S6 unit tests |
| 8 | Delegation guard enforced for @mention (unauthorized agent blocked) | S8 unit tests |
| 9 | All 23 new tests pass | `pytest test_sprint222_ott_mention.py` |
| 10 | Full S216-S222 regression: 290/290 pass (267 existing + 23 new) | `pytest test_sprint21*.py test_sprint222*.py` |
| 11 | No new Pydantic deprecation warnings introduced | pytest -W error::DeprecationWarning |
| 12 | `_process_agent_request()` backward-compatible (`definition_override=None` default) | Existing tests still pass |

---

## Files Changed

| File | Change Type | Est. LOC |
|------|-------------|----------|
| `backend/app/services/agent_bridge/ott_team_bridge.py` | MODIFY | +90 |
| `backend/app/api/routes/ott_gateway.py` | MODIFY | +30 |
| `backend/tests/unit/test_sprint222_ott_mention.py` | NEW | ~100 |
| **Total** | | **~220 LOC** |

**No new DB tables. No Alembic migration. Code-only sprint.**

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| `@email` addresses detected as @mention | Medium | Low | MentionParser already excludes email patterns (`@word` not `@word@`) |
| `_process_agent_request()` signature change breaks callers | Low | Medium | `definition_override=None` default — fully backward-compatible |
| Delegation guard blocks all @mentions | Low | High | S8 tests validate allowed/blocked paths |
| OTT_DEFAULT_PROJECT_ID not set in prod | Medium | Low | Clear error message sent to user, returns True (handled) |
| Performance: extra DB query per message with `@` | Low | Low | Query is indexed on `project_id + agent_name` |

---

## Out of Scope (Deferred)

| Item | Deferred To |
|------|-------------|
| Teams/Slack channel @mention parity | S223+ (after Telegram/Zalo validated) |
| Multiple simultaneous @mentions (parallel agent dispatch) | S224+ (requires parallel lane management) |
| `@mention` history / audit log in conversation | S224+ |
| UI in Web Dashboard to test @mention routing | S225+ |
| @mention auto-complete in Telegram (BotFather setcommands) | S225+ |

---

## CTO Review Checklist

- [ ] **ADR-056 LD#2 compliance**: Lane Contract — `handle_mention_request()` uses existing
  `enqueue()` via `_process_agent_request()`. DB is truth, Redis is notify-only. ✅ No new lane.
- [ ] **ADR-058 security**: Input sanitization runs BEFORE this code (in `protocol_adapter.py`
  during normalization). @mention branch receives already-sanitized `msg.content`. ✅ No bypass.
- [ ] **Snapshot precedence (ADR-056 LD#1)**: `definition_override` passed into
  `_process_agent_request()` triggers normal `tracker.create()` with snapshot at conversation
  creation. ✅ Immutability preserved.
- [ ] **Backward compatibility**: `definition_override=None` default. All 267 existing tests
  continue passing without change.
- [ ] **Delegation guard**: `@mention` to agent the caller has no delegation link to is blocked
  by existing `delegation_service.check_spawn_authorization()` inside TeamOrchestrator. ✅

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 0.1.0 | 2026-03-05 | @pm | Initial draft — design gap root cause + sprint plan |

---

*Sprint 222 — Zero facade tolerance. The OTT primary interface must have full parity with CLI.*
*@pjm in Telegram must call the PM agent. That's the contract.*
