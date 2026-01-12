# OpenCode Critical Discovery - January 12, 2026

**Status**: 🚨 URGENT - CTO Review Required
**Date**: January 12, 2026
**Discoverer**: Backend Lead + PM/PO
**Impact**: ADR-026 Level 1 Pilot ($30K) feasibility affected

---

## 🚨 Critical Finding

### ADR-026 Assumption vs Reality

| Aspect | ADR-026 Assumption | Actual Reality | Impact |
|--------|-------------------|----------------|--------|
| **Architecture** | HTTP API server with "Server Mode" | CLI/TUI tool (like Claude Code) | ❌ HIGH |
| **Integration** | REST endpoints (`/api/v1/feature`, `/health`) | Interactive terminal interface only | ❌ HIGH |
| **Retry Loop** | Auto-fix failing tests (max 3 retries) | Manual approval in TUI | ❌ MEDIUM |
| **Deployment** | Docker container (port 8080) | CLI binary (`opencode` command) | ❌ HIGH |
| **Use Case** | API integration for Layer 5 | External AI coder (competitor) | ⚠️ STRATEGIC |

### Source of Assumption

**ADR-026 Context** (Line 9):
> "OpenCode remains an external executor with a strict safety envelope and an immediate fallback path."

**Expert Analysis Referenced**:
> "OpenCode Server Mode: HTTP API for external tool integration with self-healing loop"

**Reality Check**:
- OpenCode README describes it as "AI-powered development tool" (CLI)
- Repository structure: TypeScript/Bun monorepo for CLI application
- No HTTP server code found in `/home/nqh/shared/opencode/packages/`
- Client/server architecture exists for remote control (mobile app → CLI), NOT HTTP API

---

## 📊 Impact Assessment

### Level 0: Observation Phase (Q1 2026) - ✅ STILL VIABLE

**Original Plan**: Local Docker evaluation, 5-sample benchmark
**Revised Plan**: CLI-based evaluation, 5-sample benchmark
**Status**: ✅ Can proceed with CLI testing
**Budget**: $0 (no change)

### Level 1: Pilot Integration (Q2 2026) - ⚠️ REQUIRES REVISION

**Original Plan**: Build OpenCode Server Mode Adapter ($30K, 2 sprints)
**Reality**: No HTTP API exists to integrate with
**Options**:
1. **CLI Wrapper** - Spawn `opencode` subprocess, capture filesystem output
   - Effort: 2-4 weeks
   - Budget: ~$10K-$15K
   - Limitations: No retry loop, hard to sandbox

2. **Fork + Custom API** - Add HTTP layer to OpenCode codebase
   - Effort: 8-12 weeks
   - Budget: ~$50K-$80K
   - Maintenance: High (diverges from upstream)

3. **External Tool** - Treat OpenCode as Layer 5 AI coder (no integration)
   - Effort: 0 weeks
   - Budget: $0
   - Use case: SDLC Orchestrator reviews OpenCode-generated PRs

---

## 🔄 Recommended Actions

### Immediate (Week 1-2) - Continue as Planned

- [x] ✅ Repository cloned (`/home/nqh/shared/opencode`)
- [ ] ⏳ Install OpenCode CLI (`brew install anomalyco/tap/opencode`)
- [ ] ⏳ Run 5-sample benchmark manually (interactive CLI prompts)
- [ ] ⏳ Document CLI architecture and extensibility
- [ ] ⏳ Complete Week 1-2 report with revised findings

### Checkpoint (Friday Jan 17 @ 3pm) - CTO Decision

**Agenda**:
1. Present discovery: OpenCode is CLI tool, not API server
2. Demo: OpenCode CLI with sample task (FastAPI CRUD)
3. Discuss: 3 integration options (CLI Wrapper / Fork + API / External Tool)
4. Decide: Proceed with Level 1 pilot (modified) OR pivot strategy

**Decision Options**:

**Option A: Continue with CLI Wrapper** (Modified Level 1)
- Scope: Subprocess-based integration
- Budget: $10K-$15K (reduced from $30K)
- Timeline: Q2 2026 (2-3 weeks)
- Risk: Limited control, no self-healing loop

**Option B: Fork + Custom API** (Expanded Level 1)
- Scope: Fork OpenCode, add HTTP API layer
- Budget: $50K-$80K (increased from $30K)
- Timeline: Q2-Q3 2026 (8-12 weeks)
- Risk: Maintenance burden, upstream divergence

**Option C: Pivot to External Tool** (No Level 1 Pilot)
- Scope: Use OpenCode as competitor (like Cursor/Claude Code)
- Budget: $0 (no integration)
- Timeline: N/A
- Strategy: Focus $30K budget on EP-06 Vibecode CLI enhancements

**Option D: Abort OpenCode Evaluation** (Exit Level 0 Early)
- Scope: Stop evaluation after Week 1-2
- Budget: $0 (no further investment)
- Timeline: Q1 2026 (Week 2 exit)
- Rationale: Strategic misalignment (OpenCode competes with us, not complements)

---

## 📋 Strategic Considerations

### OpenCode Positioning

**Original ADR-026 Positioning**:
- OpenCode: Layer 5 AI Coder (exploratory, multi-agent)
- Vibecode CLI: Layer 4 deterministic codegen (IR-based)
- Hybrid Strategy: Use both

**Reality Check**:
- OpenCode IS a competitor to Claude Code/Cursor (AI coding assistants)
- OpenCode COMPETES with SDLC Orchestrator's AI governance narrative
- Vibecode CLI remains our core differentiator (IR-based, Vietnamese SME focus)

### Market Implications

| Factor | Original Assumption | Actual Insight | Strategic Impact |
|--------|-------------------|----------------|------------------|
| **Differentiation** | OpenCode complements us | OpenCode competes with us | ⚠️ HIGH |
| **Integration Value** | Expand AI provider ecosystem | Limited value (CLI tool, not API) | ❌ MEDIUM |
| **Resource Allocation** | $30K for OpenCode pilot | Better spent on Vibecode CLI? | ✅ HIGH |
| **Go-to-Market** | "We integrate best AI tools" | "We govern AI coders" (including OpenCode) | ✅ HIGH |

---

## 📊 Revised ADR-026 Level 0 Exit Criteria

**Original Exit Criteria** (April 2026):
- Stability: >100 stars, >=2 commits/week, <10 critical issues ✅
- Quality: >=80% 4-Gate pass rate across 5 tasks ✅
- Latency: P95 <30s for sample tasks ⚠️ (CLI interactive, not batch)
- Strategic fit: Compatible with ADR-022 provider-agnostic architecture ❌ (NOT API)

**Revised Exit Criteria** (April 2026):
- CLI Quality: >=80% 4-Gate pass rate across 5 tasks ✅
- Code Generation: Produces production-ready code ✅
- Integration Feasibility: CLI wrapper viable? ⚠️ (to be assessed)
- **Strategic Fit**: Does OpenCode integration add value vs focusing on Vibecode CLI? 🔍

---

## 🎯 Recommendation

### PM/PO Recommendation: **Option C - Pivot to External Tool**

**Rationale**:

1. **Strategic Misalignment**:
   - OpenCode competes with AI coding assistants (Cursor, Claude Code)
   - SDLC Orchestrator's value = governance ABOVE AI coders, not integrating one specific tool
   - Better positioning: "We govern ALL AI coders (including OpenCode)" vs "We integrate OpenCode"

2. **Resource Optimization**:
   - $30K Level 1 budget better spent on Vibecode CLI (our differentiator)
   - IR-based codegen for Vietnamese SME = higher ROI than OpenCode CLI wrapper
   - Focus on EP-06 enhancements (Sprint 45-50) already in progress

3. **Market Narrative**:
   - Stronger story: "SDLC Orchestrator governs OpenCode/Cursor/Claude Code via 4-Gate pipeline"
   - Weaker story: "SDLC Orchestrator integrates with OpenCode via subprocess wrapper"

4. **Technical Reality**:
   - CLI wrapper integration = limited value (no self-healing loop, hard to sandbox)
   - Fork + API layer = high maintenance cost, diverges from upstream
   - External tool governance = leverage existing 4-Gate pipeline

### Alternative: **Option A - CLI Wrapper** (If Integration Still Desired)

**Conditions**:
- Reduce budget to $10K-$15K (realistic for CLI wrapper)
- Accept limitations (no self-healing loop, manual approval)
- Scope to 2-3 weeks pilot (not 2 sprints)
- Position as "proof of concept" not production integration

---

## 📅 Timeline

| Date | Milestone | Owner | Status |
|------|-----------|-------|--------|
| Jan 12, 2026 | Repository cloned | Backend Lead | ✅ DONE |
| Jan 12, 2026 | Critical discovery documented | PM/PO | ✅ DONE |
| Jan 13-15, 2026 | Install + test OpenCode CLI | Backend Lead | ⏳ IN PROGRESS |
| Jan 16, 2026 | Document architecture + findings | Backend Lead | ⏳ PENDING |
| Jan 17, 2026 @ 3pm | **CTO Checkpoint** - GO/PIVOT/ABORT decision | CTO + PM/PO + Backend Lead | ⏳ SCHEDULED |
| Jan 20, 2026 | Execute decision (continue/pivot/abort) | Team | ⏳ PENDING |

---

## 📞 Next Steps

**For Backend Lead** (Jan 13-17):
1. Install OpenCode CLI (`brew install anomalyco/tap/opencode`)
2. Run 5-sample benchmark (interactive prompts)
3. Document findings in Week 1-2 report
4. Prepare demo for CTO checkpoint

**For PM/PO** (Jan 12-17):
1. ✅ Document critical discovery (this file)
2. Share with CTO + Architect before checkpoint
3. Prepare 3 options presentation (A, B, C, D)
4. Recommend strategic pivot (Option C)

**For CTO** (Review by Jan 16):
1. Review this critical discovery document
2. Review ADR-026 integration assumptions
3. Consider strategic implications (compete vs complement)
4. Prepare decision for Jan 17 checkpoint

---

## 📂 Related Documentation

- [ADR-026-OpenCode-Integration-Strategy.md](../../02-design/01-ADRs/ADR-026-OpenCode-Integration-Strategy.md) - Original strategy
- [ISSUE-OpenCode-Level0-Week1-2.md](./ISSUE-OpenCode-Level0-Week1-2.md) - Week 1-2 tasks
- [OpenCode-Setup-Instructions-ACTUAL.md](./OpenCode-Setup-Instructions-ACTUAL.md) - Revised setup guide
- OpenCode Repository: `/home/nqh/shared/opencode`
- OpenCode Official Docs: https://opencode.ai/docs

---

**Status**: 🚨 CTO REVIEW REQUIRED
**Urgency**: HIGH - Affects Q2 2026 roadmap ($30K budget decision)
**Next Checkpoint**: Friday, January 17, 2026 @ 3pm

---

**Last Updated**: January 12, 2026, 9:30pm
**Document Owner**: PM/PO + Backend Lead
