# Sprint 174: Anthropic Best Practices Integration

**Sprint Duration**: February 17-28, 2026 (10 working days)  
**Sprint Goal**: Implement Tier 1 Anthropic patterns (Prompt Caching + MCP Positioning)  
**Framework**: SDLC 6.1.0
**Status**: PLANNED

---

## Context

Research into Anthropic team's internal usage of Claude Code reveals 7 strategic patterns. Sprint 174 focuses on **Tier 1** (highest ROI):

1. **Prompt Caching** → $14,850/year cost savings
2. **MCP Positioning** → Marketing clarity (not a competitor, but orchestrator)

**Reference**: [ADR-054](../../02-design/ADR-054-Anthropic-Claude-Code-Best-Practices.md)

---

## Sprint Objectives

### P0: Prompt Caching Service (Days 1-7)
**Goal**: Reduce codegen costs by 8x via Anthropic's prompt caching API.

**Current State**:
- Every EP-06 codegen request re-sends SDLC Framework (960KB)
- Cost: $0.012 per request × 1000 requests/day = $12/day
- No caching across sessions

**Target State**:
- Framework context cached for 24 hours
- Cost: $0.0015 per request (90% cache hit rate)
- Savings: $10.50/day = $3,832/year (first year) → $14,850/year (full adoption)

**Acceptance Criteria**:
- [ ] Cache hit rate: >85% (measured via Prometheus metrics)
- [ ] Cost per codegen request: <$0.002
- [ ] Latency reduction: -200ms on cached requests
- [ ] Auto-refresh on framework updates (webhook trigger)

### P0: MCP Positioning Document (Days 8-10)
**Goal**: Clarify market position — we **orchestrate** AI coders, not compete with them.

**Deliverables**:
- [ ] "SDLC-as-MCP-Control-Plane.md" (technical doc)
- [ ] Updated homepage copy (landing page)
- [ ] Sales deck slides (3-5 slides on MCP architecture)
- [ ] Blog post draft: "Why We Don't Compete with Claude Code"

**Target Audience**:
- Investors (understand our moat)
- Customers (why buy SDLC + Claude Code, not just Claude Code?)
- Partners (Claude/Cursor/Copilot are complementary, not threats)

---

## Stories & Tasks

### Story 1: Prompt Caching Infrastructure (5 days)

**Day 1-2: Design + Framework Selection**
- [ ] Research Anthropic's `cache_control` API (see docs)
- [ ] Design cache strategy:
  - What to cache? (Framework docs, ADRs, templates)
  - When to invalidate? (framework updates, new templates)
  - How to measure? (cache hit rate, cost metrics)
- [ ] Select cache breakpoints (SDLC sections with high reuse)

**Day 3-4: Implementation**
```python
# backend/app/services/context_cache_service.py
class SDLCContextCache:
    """
    Anthropic prompt caching for SDLC Framework.
    
    Architecture:
    1. Load framework docs (960KB total)
    2. Mark cache breakpoints (Anthropic syntax)
    3. Store in Redis (fast retrieval)
    4. Auto-refresh on updates (webhook)
    
    Cost model:
    - Write to cache: $15/million tokens (once per 24h)
    - Read from cache: $1.50/million tokens (10x cheaper)
    """
    
    CACHED_SECTIONS = [
        "SDLC-Enterprise-Framework/02-Core-Methodology/README.md",
        "docs/02-design/ADR-*.md",
        "backend/app/services/codegen/templates/*.j2",
    ]
    
    async def get_cached_prompt(self) -> CachedPrompt:
        """Returns prompt with cache_control markers."""
        pass
    
    async def invalidate_on_update(self, changed_files: list[str]):
        """Webhook handler for framework updates."""
        pass
```

**Day 5: Integration + Testing**
- [ ] Integrate with CodegenService
- [ ] Add Prometheus metrics (cache hit rate, cost per request)
- [ ] Load test (1000 codegen requests, verify 85%+ cache hit)

### Story 2: Cost Monitoring Dashboard (2 days)

**Day 6-7: Grafana Dashboard**
- [ ] Create "Codegen Cost Analytics" dashboard
  - Panel 1: Cost per request (before/after caching)
  - Panel 2: Cache hit rate over time
  - Panel 3: Estimated monthly savings
  - Panel 4: Top cached contexts (what's most reused?)
- [ ] Alert: If cache hit rate <70%, notify #eng-alerts
- [ ] Weekly report: Email CTO/CEO with cost savings summary

### Story 3: MCP Positioning Document (3 days)

**Day 8: Technical Document**
```markdown
# SDLC Orchestrator as MCP Control Plane

## Architecture

```
┌─────────────────────────────────────┐
│   SDLC Orchestrator (Control Plane) │
│                                     │
│  ┌─────────────────────────────┐   │
│  │  MCP Provider Interface     │   │
│  │  ├─ Claude Code (Anthropic) │   │
│  │  ├─ Cursor (OpenAI)         │   │
│  │  ├─ Copilot (GitHub)        │   │
│  │  └─ Ollama (Local)          │   │
│  └─────────────────────────────┘   │
│                                     │
│  ┌─────────────────────────────┐   │
│  │  Governance Services (MCP)  │   │
│  │  ├─ Evidence Vault (S3)     │   │
│  │  ├─ OPA Policy Engine       │   │
│  │  ├─ Quality Gates (4-layer) │   │
│  │  └─ GitHub Integration      │   │
│  └─────────────────────────────┘   │
└─────────────────────────────────────┘
```

## Value Proposition

**We are NOT**:
- "Claude Code competitor"
- "AI coder wrapper"
- "Cursor alternative"

**We ARE**:
- **Control plane** that governs ALL AI coders
- **MCP orchestration layer** (multi-provider)
- **Evidence-based governance** (Quality Gates + Vault)

## Customer Stories

"We use Claude Code for implementation, SDLC Orchestrator for governance."
— Enterprise customer (Fortune 500)

"SDLC doesn't replace Cursor — it makes Cursor safe for production."
— Startup CTO
```

**Day 9: Marketing Materials**
- [ ] Update homepage hero section (MCP diagram)
- [ ] Sales deck: Add "Architecture" slide (MCP visual)
- [ ] Write blog post: "SDLC + Claude Code: Better Together"
  - Explain MCP philosophy
  - Show customer workflow: Code in Claude → Govern in SDLC
  - Position as **complementary**, not competitive

**Day 10: Internal Alignment**
- [ ] All-hands presentation: "Our MCP Strategy"
- [ ] Update pitch deck (investor version)
- [ ] Train sales team: New positioning talking points

---

## Success Metrics

| Metric | Baseline | Target (End of Sprint) | Measurement |
|--------|----------|------------------------|-------------|
| **Cost per Codegen** | $0.012 | <$0.002 | Prometheus `/metrics` |
| **Cache Hit Rate** | 0% (no cache) | >85% | Redis analytics |
| **Monthly Cost Savings** | $0 | $320 | Cost dashboard |
| **Sales Messaging Clarity** | ? | Survey score >8/10 | Internal survey |

---

## Risks & Mitigations

### Risk 1: Cache invalidation bugs
**Impact**: Stale framework context → bad codegen output  
**Probability**: Medium  
**Mitigation**: 
- Cache TTL = 24h (auto-refresh)
- Webhook on framework commits (instant invalidation)
- Manual override: `sdlcctl cache clear --force`

### Risk 2: Anthropic API changes
**Impact**: Prompt caching syntax breaks  
**Probability**: Low  
**Mitigation**:
- Use stable API version (pinned in code)
- Monitor Anthropic changelog (RSS feed)
- Fallback: Disable caching if API errors (graceful degradation)

### Risk 3: MCP positioning confuses customers
**Impact**: "Wait, I still need Claude Code?"  
**Probability**: Medium  
**Mitigation**:
- Clear messaging: "SDLC + Claude = Better Together"
- Demo video showing workflow (code in Claude, govern in SDLC)
- Sales enablement training (Day 10)

---

## Dependencies

- **External**: Anthropic API access (prompt caching feature enabled)
- **Internal**: Redis cluster (for cache storage)
- **Team**: Marketing designer (MCP diagram for sales deck)

---

## Team Allocation

- **Backend Engineer (7 days)**: Prompt caching implementation
- **DevOps Engineer (2 days)**: Grafana dashboard + metrics
- **Marketing Lead (3 days)**: MCP positioning docs + blog post
- **CTO (1 day)**: Review + approve messaging

---

## Definition of Done

- [ ] Prompt caching service deployed to production
- [ ] Cache hit rate >85% (measured over 1000 requests)
- [ ] Cost savings visible in Grafana (<$0.002 per request)
- [ ] MCP positioning doc published (docs site + blog)
- [ ] Sales team trained (can explain MCP strategy)
- [ ] All-hands presentation completed (team alignment)

---

## Next Steps (Sprint 175+)

**Sprint 175**: Framework Migration Toolkit (`sdlcctl migrate framework`)  
**Sprint 176**: Progressive Stage Unlock (beginner mode)  
**Sprint 177**: AI Approval Assistant (CTO tool)

See [ADR-054](../../02-design/ADR-054-Anthropic-Claude-Code-Best-Practices.md) for full roadmap.

---

**Related Documents**:
- ADR-054: Anthropic Claude Code Best Practices
- ADR-053: Governance Loop Architecture (Sprint 173)
- CURRENT-SPRINT.md (update with Sprint 174 kickoff)

**Approvals**:
- [ ] CTO (Technical feasibility)
- [ ] CEO (Budget + marketing strategy)
- [ ] Engineering Team (Capacity confirmed)

---

*Sprint 174 Plan — SDLC Orchestrator Team*  
*February 16, 2026*
