# AI Council Manual Test Guide

**Version**: 1.0.0
**Date**: December 16, 2025
**Status**: ACTIVE - Manual Testing Guide
**Authority**: QA Lead + Frontend Lead
**Framework**: SDLC 5.1.1 Complete Lifecycle

---

## 1. Overview

This guide provides step-by-step manual testing procedures for the **AI Council** feature in SDLC Orchestrator. AI Council is a multi-LLM deliberation system that provides high-quality compliance recommendations.

### 1.1 AI Council Features

| Feature | Description | Mode | Expected Latency |
|---------|-------------|------|------------------|
| Single Mode | Fast recommendations (Ollama only) | `single` | <3s (p95) |
| Council Mode | 3-stage deliberation (3+ LLMs) | `council` | <8s (p95) |
| Auto Mode | Severity-based routing | `auto` | Variable |

### 1.2 3-Stage Council Process

```
Stage 1: Parallel Queries
├─ Ollama → Independent recommendation
├─ Claude → Independent recommendation
└─ GPT-4o → Independent recommendation

Stage 2: Peer Review
├─ Each LLM ranks others' responses (anonymized)
└─ Consensus scoring

Stage 3: Chairman Synthesis
└─ Chairman LLM combines best elements → Final recommendation
```

---

## 2. Prerequisites

### 2.1 System Requirements

✅ **Backend**: Running on http://localhost:8300
✅ **Frontend**: Running on http://localhost:8310
✅ **Database**: PostgreSQL with seed data loaded
✅ **AI Providers**:
- Ollama (api.nqh.vn) - Primary
- Claude API key configured (fallback)
- GPT-4o API key configured (fallback)

### 2.2 Test Accounts

| Role | Email | Password | Purpose |
|------|-------|----------|---------|
| Admin | admin@sdlc-orchestrator.io | Admin@123 | Full access |
| CTO | dvhiep@nqh.com.vn | Admin@123 | Technical approvals |
| CPO | dunglt@mtsolution.com.vn | Admin@123 | Product decisions |

---

## 3. Test Scenarios

### TC-AI-001: Access AI Council Chat (Single Mode)

**Objective**: Verify AI Council chat UI is accessible from Compliance Page

**Steps**:
1. Open browser → http://localhost:8310
2. Login with `admin@sdlc-orchestrator.io` / `Admin@123`
3. Navigate to **Compliance** page (sidebar menu)
4. Scroll to **Violations by Category** chart
5. Look for **AI Council Chat** button (bottom-right corner)
6. Click the **Bot icon** button

**Expected Result**:
- ✅ Sheet slides out from right side
- ✅ Welcome message displayed:
  ```
  Welcome! I'm your AI Compliance Assistant. I can help you with:
  • Fixing compliance violations
  • Understanding gate requirements
  • Generating evidence templates
  • Answering SDLC 5.1.1 questions

  How can I help you today?
  ```
- ✅ Text input field visible
- ✅ Send button enabled
- ✅ Council Mode toggle OFF (default = Single Mode)

**Screenshot**: `TC-AI-001-chat-open.png`

---

### TC-AI-002: Send Question in Single Mode

**Objective**: Test AI Council Single Mode response (<3s target)

**Steps**:
1. Open AI Council Chat (from TC-AI-001)
2. Ensure **Council Mode** toggle is **OFF** (Single Mode)
3. Type question in input field:
   ```
   How do I fix a missing evidence violation for Gate G1?
   ```
4. Click **Send** button (or press Enter)
5. Observe loading indicator
6. Wait for response

**Expected Result**:
- ✅ User message appears immediately
- ✅ Loading indicator (3 dots or spinner) shown
- ✅ Response received within **<3 seconds**
- ✅ AI response includes:
  - Specific steps to fix violation
  - Evidence type recommendations
  - Clear, actionable guidance
- ✅ Response formatted with markdown (bullets, code blocks)
- ✅ **Provider used**: Ollama (shown in metadata badge)
- ✅ **Confidence score**: >70%

**Sample Response**:
```markdown
To fix a missing evidence violation for Gate G1, follow these steps:

1. **Identify Required Evidence**: G1 (Market Validation) typically requires:
   - Legal review documents (COMPLIANCE type)
   - Market research reports (DOCUMENTATION type)
   - Beta tester agreements (COMPLIANCE type)

2. **Upload Evidence**:
   - Navigate to Gates → G1 → Evidence tab
   - Click "Upload Evidence"
   - Select file (PDF, DOCX, TXT)
   - Choose evidence type: COMPLIANCE
   - Add description: "Legal AGPL containment review - Q4 2025"

3. **Verify Integrity**:
   - System automatically generates SHA256 hash
   - Check integrity status = "valid"

4. **Re-trigger Gate Evaluation**:
   - Click "Re-evaluate Gate" button
   - Policy engine will re-scan evidence
   - Violation should auto-resolve if evidence is sufficient

**Provider**: Ollama (llama3.1:70b)
**Confidence**: 85%
**Response Time**: 1.2s
```

**Screenshot**: `TC-AI-002-single-mode-response.png`

---

### TC-AI-003: Switch to Council Mode

**Objective**: Test AI Council 3-stage deliberation (<8s target)

**Steps**:
1. In AI Council Chat, toggle **Council Mode** to **ON**
2. Observe toggle state (blue = ON)
3. Type question:
   ```
   What is the best way to implement RBAC for gate approvals?
   ```
4. Click **Send**
5. Observe loading indicator with stage progress (if implemented)
6. Wait for response (max 10s timeout)

**Expected Result**:
- ✅ Toggle switches to ON (blue background)
- ✅ Loading message: "Council is deliberating..." (with stages)
- ✅ Response received within **<8 seconds**
- ✅ **Council Deliberation Metadata** shown:
  ```yaml
  Mode: council
  Providers Used: ollama, claude, gpt4
  Stage 1: 3 independent responses (2.1s)
  Stage 2: Peer review + ranking (1.5s)
  Stage 3: Chairman synthesis (3.2s)
  Total Duration: 6.8s
  Consensus Score: 92%
  ```
- ✅ Response quality higher than Single Mode:
  - More detailed analysis
  - Multiple perspectives considered
  - Confidence score >85%
  - Clear rationale for recommendation

**Sample Response**:
```markdown
After deliberating with multiple AI experts, here's the recommended RBAC implementation:

**Consensus Recommendation** (92% agreement):

1. **4-Tier Role Hierarchy**:
   ```
   CEO/CPO/CTO → Can approve any gate
   Tech Lead → Can approve BUILD/VERIFY gates
   PM/Developer → Can submit gates
   QA/Viewer → Read-only access
   ```

2. **Row-Level Security (PostgreSQL RLS)**:
   - Enforce project membership at database level
   - Automatic filtering: Users only see their team's gates
   - Performance: <10ms overhead (indexed on user_id)

3. **API-Level Authorization**:
   ```python
   @require_role(["CEO", "CPO", "CTO"])
   async def approve_gate(gate_id: UUID, user: User):
       if gate.status != "PENDING_APPROVAL":
           raise ForbiddenError("Gate not pending approval")
   ```

**Why this approach?** (Council deliberation summary):
- Ollama: Emphasized simplicity and performance
- Claude: Highlighted security best practices (OWASP ASVS L2)
- GPT-4o: Suggested PostgreSQL RLS for scalability

**Final synthesis**: Combine database-level RLS (can't be bypassed) with API-level role checks (better error messages).

**Council Metadata**:
- Providers: ollama, claude, gpt4
- Total Duration: 6.8s
- Consensus Score: 92%
- Chairman: Claude Sonnet 4.5
```

**Screenshot**: `TC-AI-003-council-mode-response.png`

---

### TC-AI-004: Multi-Turn Conversation

**Objective**: Verify context is maintained across multiple messages

**Steps**:
1. In AI Council Chat (Single or Council Mode)
2. Send first question:
   ```
   What are the stages in SDLC 5.1.1?
   ```
3. Wait for response
4. Send follow-up question (without repeating context):
   ```
   Which stage requires legal review?
   ```
5. Verify AI understands context from previous message

**Expected Result**:
- ✅ First response lists all 10 SDLC stages (00-WHY to 09-GOVERN)
- ✅ Second response correctly identifies:
  - **Stage 01 (WHAT)** - Legal review at G1 gate
  - References previous answer about SDLC stages
  - No need to re-explain SDLC framework

**Screenshot**: `TC-AI-004-multi-turn.png`

---

### TC-AI-005: Clear Chat History

**Objective**: Test chat reset functionality

**Steps**:
1. In AI Council Chat with existing conversation
2. Click **Trash** icon (top-right of chat sheet)
3. Confirm clear action (if dialog appears)
4. Observe chat state

**Expected Result**:
- ✅ All messages cleared except Welcome message
- ✅ Chat resets to initial state
- ✅ Input field cleared
- ✅ Context not carried over to new conversation

---

### TC-AI-006: Error Handling - Timeout

**Objective**: Verify graceful handling of AI provider timeout

**Steps**:
1. Disconnect internet or block AI provider APIs (simulate)
2. Send question in Council Mode (8s timeout)
3. Wait for timeout

**Expected Result**:
- ✅ Loading indicator shows for 8-10s
- ✅ Error message displayed:
  ```
  ⚠️ Council deliberation timed out.
  Please try again in Single Mode for faster response.
  ```
- ✅ **Fallback suggestion**: "Try Single Mode" button
- ✅ Chat remains functional (can send new messages)

---

### TC-AI-007: Violation-Specific Recommendation

**Objective**: Test context-aware recommendations for specific violations

**Steps**:
1. Navigate to **Compliance Page**
2. Find a violation in "Recent Violations" table
3. Click **"Ask AI"** button on violation row
4. AI Council Chat opens with **pre-filled context**:
   - Violation ID
   - Violation message
   - Severity level
   - Project context
5. Send question or use suggested prompts

**Expected Result**:
- ✅ Chat opens with violation context pre-loaded
- ✅ Suggested prompts shown:
  - "How do I fix this violation?"
  - "What evidence is needed?"
  - "Explain this policy requirement"
- ✅ AI response specific to that violation
- ✅ Includes project-aware recommendations
- ✅ Cites relevant SDLC 5.1.1 policies

---

## 4. Performance Benchmarks

### 4.1 Latency Targets

| Mode | Target (p95) | Max Timeout | Fallback |
|------|--------------|-------------|----------|
| Single | <3s | 5s | Rule-based |
| Council | <8s | 10s | Single Mode |
| Auto (CRITICAL) | <8s | 10s | Single Mode |
| Auto (LOW) | <3s | 5s | Rule-based |

### 4.2 Quality Metrics

| Metric | Single Mode | Council Mode |
|--------|-------------|--------------|
| Confidence Score | >70% | >85% |
| Actionability | Good | Excellent |
| Context Awareness | Basic | Advanced |
| Consensus | N/A | >80% |

---

## 5. Known Limitations (v1.0.0)

⚠️ **Current Limitations**:

1. **No Persistent Chat History**: Chat resets on page reload
2. **No Async Processing**: Long deliberations block UI (no background job queue)
3. **Limited Context Window**: Only last 5 messages considered
4. **No Code Execution**: Cannot run validation scripts
5. **English Only**: Multilingual support not yet implemented

**Roadmap** (v2.0.0 - Q1 2026):
- Persistent chat history (stored in database)
- Async deliberations with WebSocket updates
- Extended context window (last 20 messages)
- Python code execution sandbox
- Vietnamese language support

---

## 6. Troubleshooting

### Issue: Chat doesn't open

**Solution**:
- Check browser console for JavaScript errors (F12)
- Verify frontend build: `docker logs sdlc-frontend`
- Hard refresh: Ctrl+Shift+R

### Issue: No response from AI

**Solution**:
- Check backend logs: `docker logs sdlc-backend | grep -i council`
- Verify AI providers configured in `.env`:
  ```bash
  OLLAMA_API_URL=http://api.nqh.vn
  ANTHROPIC_API_KEY=sk-ant-xxx
  OPENAI_API_KEY=sk-xxx
  ```
- Test fallback chain: Council → Single → Rule-based

### Issue: Response too slow (>10s)

**Solution**:
- Use Single Mode instead of Council Mode
- Check network latency to AI providers
- Monitor backend metrics: `http://localhost:8300/api/v1/health`

---

## 7. Test Completion Checklist

- [ ] TC-AI-001: Access AI Council Chat
- [ ] TC-AI-002: Single Mode response (<3s)
- [ ] TC-AI-003: Council Mode response (<8s)
- [ ] TC-AI-004: Multi-turn conversation
- [ ] TC-AI-005: Clear chat history
- [ ] TC-AI-006: Error handling (timeout)
- [ ] TC-AI-007: Violation-specific recommendation

**Test Status**: ✅ PASS / ⚠️ PARTIAL / ❌ FAIL

**Tester**: _________________
**Date**: _________________
**Signature**: _________________

---

**Next Steps**:
1. Execute all test scenarios via browser
2. Take screenshots for evidence
3. Document any bugs in GitHub Issues
4. Update test report with actual results

**Reference Documents**:
- `docs/04-build/04-Phase-Plans/PHASE-01-AI-COUNCIL-SERVICE.md`
- `docs/02-design/03-API-Design/openapi.yml` (lines 3300-3500)
- `backend/app/api/routes/council.py`
- `frontend/web/src/components/council/AICouncilChat.tsx`
