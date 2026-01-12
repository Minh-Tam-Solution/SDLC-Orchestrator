# Email to CTO: OpenCode Critical Discovery

**To**: CTO
**From**: PM/PO + Backend Lead
**Subject**: 🚨 OpenCode Level 0 - Critical Discovery Requires Your Review (Before Jan 17 Checkpoint)
**Priority**: HIGH
**Date**: January 12, 2026, 9:45pm

---

## Summary

We've discovered a **critical architecture mismatch** in our OpenCode evaluation that affects the $30K Q2 2026 pilot budget. **Your review is required before Friday's checkpoint (Jan 17 @ 3pm)**.

---

## Critical Finding

**ADR-026 Assumption** (approved Jan 12):
> OpenCode has "Server Mode" with HTTP API endpoints for integration

**Reality** (discovered Jan 12 after cloning repository):
> OpenCode is a **CLI/TUI tool** (like Claude Code, Cursor) with **NO HTTP API**

### Evidence

After Backend Lead cloned `/home/nqh/shared/opencode`, we found:
- ✅ OpenCode is TypeScript/Bun monorepo for CLI application
- ✅ Interactive terminal interface (TUI) only
- ❌ No REST API endpoints (`/api/v1/feature`, `/health`)
- ❌ No Docker server mode
- ❌ Client/server architecture exists ONLY for remote control (mobile → CLI), NOT HTTP API

**Source**: OpenCode README describes it as "AI-powered development tool" (CLI), not API server

---

## Impact Assessment

| Level | Original Plan | Current Status | Impact |
|-------|--------------|----------------|--------|
| **Level 0** (Q1 2026) | Local Docker API testing | CLI-based testing | ✅ Still viable |
| **Level 1** (Q2 2026) | Build HTTP adapter ($30K) | Integration method invalid | ❌ **HIGH** |
| **Strategic** | Layer 5 AI provider | Competitor to Cursor/Claude Code | ⚠️ **CRITICAL** |

---

## 4 Integration Options (Your Decision Required)

### Option A: CLI Wrapper Integration
- **Scope**: Subprocess-based integration (`opencode` CLI spawn)
- **Budget**: $10K-$15K (reduced from $30K)
- **Timeline**: 2-3 weeks (Q2 2026)
- **Pros**: Minimal effort, no OpenCode modification
- **Cons**: No self-healing loop, hard to sandbox, limited control

### Option B: Fork + Custom API Layer
- **Scope**: Fork OpenCode, add HTTP API package
- **Budget**: $50K-$80K (increased from $30K)
- **Timeline**: 8-12 weeks (Q2-Q3 2026)
- **Pros**: Full control, self-healing loop, retry logic
- **Cons**: High maintenance, diverges from upstream

### Option C: Pivot to External Tool (Governance Only) ⭐ **PM/PO RECOMMENDATION**
- **Scope**: Use OpenCode as external AI coder (like Cursor)
- **Budget**: $0 (no integration)
- **Timeline**: N/A
- **Strategy**: SDLC Orchestrator governs OpenCode-generated PRs via 4-Gate pipeline
- **Narrative**: "We govern ALL AI coders" vs "We integrate one specific tool"
- **Resource Allocation**: Reallocate $30K to Vibecode CLI (our differentiator)

### Option D: Abort Evaluation Early
- **Scope**: Stop after Week 1-2
- **Budget**: $0
- **Rationale**: Strategic misalignment (OpenCode competes with us, not complements)

---

## PM/PO Recommendation: **Option C**

### Why Option C?

**1. Strategic Positioning**:
- OpenCode **competes** with Cursor/Claude Code (AI coding assistants)
- SDLC Orchestrator's value = governance **ABOVE** AI coders
- Stronger narrative: "We govern ALL AI coders (including OpenCode)" vs "We integrate OpenCode"

**2. Resource Optimization**:
- $30K Level 1 budget better spent on **Vibecode CLI** (our core differentiator)
- IR-based codegen for Vietnamese SME = higher ROI than CLI wrapper
- Focus on EP-06 enhancements (Sprint 45-50) already in progress

**3. Technical Reality**:
- CLI wrapper = limited value (no self-healing loop, hard to sandbox)
- Fork + API = high maintenance cost ($50K-$80K), upstream divergence
- External tool governance = leverage existing 4-Gate pipeline

**4. Market Implications**:
- OpenCode positioning: Competitor to AI coders, NOT integration partner
- Our differentiation: Governance layer ABOVE AI coders, not alongside them
- Better story for investors/customers: "We govern industry-leading tools"

---

## Required Action

**Before Checkpoint (Jan 17 @ 3pm)**:
1. ✅ Review this email + [OpenCode-Critical-Discovery-Jan12-2026.md](./OpenCode-Critical-Discovery-Jan12-2026.md)
2. ✅ Consider 4 integration options (A, B, C, D)
3. ✅ Decide: Which option to pursue?

**At Checkpoint (Jan 17 @ 3pm)**:
- Backend Lead demos: OpenCode CLI with sample task
- PM/PO presents: 4 options with pros/cons
- CTO decides: A (CLI Wrapper) / B (Fork + API) / C (Governance Only) / D (Abort)

**Outcome**: Clear direction for Week 3-12 activities + Q2 2026 budget allocation

---

## Documents to Review (Priority Order)

1. **[OpenCode-Critical-Discovery-Jan12-2026.md](./OpenCode-Critical-Discovery-Jan12-2026.md)** - 🚨 **READ FIRST** (10 min)
   - Detailed impact assessment
   - 4 options analysis with budget/timeline
   - Strategic considerations

2. **[ADR-026-OpenCode-Integration-Strategy.md](../../02-design/01-ADRs/ADR-026-OpenCode-Integration-Strategy.md)** - Original strategy (5 min)
   - Based on API server assumption (now invalid)

3. **[OpenCode-Setup-Instructions-ACTUAL.md](./OpenCode-Setup-Instructions-ACTUAL.md)** - Revised setup guide (optional)
   - CLI installation steps
   - Integration scenarios comparison

---

## Timeline

| Date | Milestone | Owner | Status |
|------|-----------|-------|--------|
| Jan 12, 2026 | Repository cloned | Backend Lead | ✅ DONE |
| Jan 12, 2026 | Critical discovery documented | PM/PO | ✅ DONE |
| Jan 13-16, 2026 | CTO reviews discovery + options | CTO | ⏳ PENDING |
| Jan 17, 2026 @ 3pm | **Checkpoint meeting** - Decision | CTO + PM/PO + Backend Lead | ⏳ SCHEDULED |
| Jan 20, 2026 | Execute decision (A/B/C/D) | Team | ⏳ PENDING |

---

## Questions?

**Slack**: `#sdlc-orchestrator-dev` or `#product-strategy`
**PM/PO**: Available for 1-on-1 discussion before checkpoint

---

## Bottom Line

**Original Plan**: Integrate OpenCode via HTTP API ($30K, Q2 2026)
**Reality Check**: No HTTP API exists → Need strategic pivot
**Recommended**: Governance-only approach ($0, no integration) + reallocate $30K to Vibecode CLI
**Your Decision**: Required by Jan 17 @ 3pm

---

**Urgency**: HIGH - Affects Q2 2026 roadmap and $30K budget allocation
**Next Steps**: Review documents → Decide on option → Communicate at checkpoint

Thank you for your prompt attention to this matter.

---

**Attachments**:
- [OpenCode-Critical-Discovery-Jan12-2026.md](./OpenCode-Critical-Discovery-Jan12-2026.md) (detailed analysis)
- [ADR-026-OpenCode-Integration-Strategy.md](../../02-design/01-ADRs/ADR-026-OpenCode-Integration-Strategy.md) (original strategy)
- [CURRENT-SPRINT.md](../02-Sprint-Plans/CURRENT-SPRINT.md) (updated with discovery)

---

**Email Status**: 📤 READY TO SEND
**Recommended Recipients**:
- **To**: CTO (primary decision maker)
- **CC**: Architect (technical review), Backend Lead (implementer)
- **FYI**: CPO (strategic context)
