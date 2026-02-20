# ADR-023: AgentScope Pattern Extraction Strategy
## Multi-Agent Enhancement via Inspired Evolution (Not Runtime Integration)

**Status**: ✅ APPROVED
**Date**: December 28, 2025
**Decision Makers**: CTO
**Stage**: Stage 02 (HOW - Design & Architecture)
**Framework**: SDLC 6.1.0
**Sprints**: Sprint 65-68 (Q1/Q2 2026) *(rescheduled due to Sprint 61-64 frontend platform consolidation)*

---

## Context

### Research Objective

Evaluate [AgentScope](https://github.com/agentscope-ai/agentscope) (Alibaba's Agent-Oriented Programming framework, 14.6k ⭐) for potential integration into SDLC Orchestrator's AI architecture.

### AgentScope Overview

| Attribute | Value |
|-----------|-------|
| Organization | Alibaba Group (Tongyi Lab) |
| Stars | 14.6k ⭐ |
| License | Apache 2.0 |
| Language | Python 3.10+ |
| Philosophy | Developer-centric agent framework |
| Latest Version | v1.0.10 (Dec 2025) |

### SDLC Orchestrator's Existing AI Architecture

**Production-Ready Multi-Agent System:**

| Component | Purpose | Status | LOC |
|-----------|---------|--------|-----|
| `AICouncilService` | 3-stage multi-agent deliberation | ✅ Production | 1,550+ |
| `CodegenService` | Provider registry + fallback | ✅ Production | 614 |
| `OllamaService` | Local LLM via HTTP REST | ✅ Production | 874 |
| `AIRecommendationService` | Fallback chain orchestration | ✅ Production | - |
| IR Processor | Spec → Intermediate Representation | ✅ Production | - |
| Quality Pipeline | 4-gate validation | ✅ Sprint 48 | - |

**Key Finding**: `AICouncilService` already implements multi-agent deliberation functionally equivalent to AgentScope's `MsgHub`!

```
┌─────────────────────────────────────────────────────────────┐
│         AICOUNCILSERVICE (3-STAGE DELIBERATION)             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  STAGE 1: PARALLEL QUERIES                                  │
│  → Equivalent to AgentScope's parallel agent execution      │
│                                                             │
│  STAGE 2: PEER REVIEW                                       │
│  → Equivalent to AgentScope's agent collaboration           │
│                                                             │
│  STAGE 3: SYNTHESIS                                         │
│  → Equivalent to AgentScope's aggregation agent             │
│                                                             │
│  THIS IS FUNCTIONALLY EQUIVALENT TO AGENTSCOPE'S MsgHub!    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Decision

### ⚠️ VERDICT: 🔴 DO NOT INTEGRATE - EXTRACT PATTERNS ONLY

**Alignment Score**: 50/100 (adjusted from initial 70/100)

### Reasons NOT to Integrate Runtime

1. **Redundancy**: `AICouncilService` (1,550+ LOC) already implements equivalent multi-agent architecture
2. **Cost Already Optimized**: Provider chain (Ollama $50/mo → Claude $1000/mo → GPT-4 $800/mo) saves $11,400/year (95% reduction). AgentScope cannot improve this.
3. **License Risk**: Unclear AGPL contamination risk from Alibaba SDK dependencies
4. **Training Overhead**: 6-8 weeks effort + team training not justified for minimal benefit
5. **Control**: Full ownership of existing codebase vs. external framework dependency
6. **Integration Complexity**: 6-8 weeks full replacement effort for marginal gain

### Gap Analysis

| Feature | AgentScope | SDLC Orchestrator | Gap Status |
|---------|-----------|-------------------|-----------|
| Multi-agent messaging | ✅ MsgHub | ✅ AICouncilService | 🟢 CLOSED |
| Provider abstraction | ✅ Model-agnostic | ✅ ProviderRegistry | 🟢 CLOSED |
| Async execution | ✅ Native | ✅ asyncio/FastAPI | 🟢 CLOSED |
| Fallback chain | ⚠️ Manual | ✅ Automatic | 🟢 **Team leads** |
| Cost tracking | ❌ None | ✅ Budget management | 🟢 **Team leads** |
| Quality gates | ❌ None | ✅ 4-stage pipeline | 🟢 **Team leads** |
| **ReAct planning** | ✅ Built-in | ❌ Not implemented | 🔴 **OPEN** |
| **Long-term memory** | ✅ ReMe | ⚠️ Redis cache only | 🔴 **OPEN** |
| **Tool orchestration** | ✅ Agentic tools | ⚠️ Manual integration | 🔴 **OPEN** |
| Visualization | ✅ AgentScope Studio | ⚠️ Grafana dashboards | 🟡 PARTIAL |

**Recommendation**: Close OPEN gaps via **"Inspired Evolution"** (self-implementation), NOT via AgentScope runtime integration.

---

## Approved Actions

### ✅ PERMITTED

1. **Study AgentScope source code** for architectural patterns
2. **Extract ReAct, Memory, Tool patterns** for learning
3. **Implement patterns in AICouncilService** (Sprint 61-64)
4. **Quarterly review** of AgentScope development

### ❌ PROHIBITED

1. Add `agentscope` as pip dependency
2. Replace `AICouncilService` with AgentScope agents
3. Market product as "powered by AgentScope"
4. Introduce new external runtime dependencies

---

## Implementation Roadmap: "Inspired Evolution"

### Sprint 61: Research Phase (2 weeks)

- Deep-dive AgentScope source code
- Extract ReAct implementation pattern
- Design memory enhancement schema  
- Document patterns for team

### Sprint 62: ReAct Enhancement (2 weeks)

- Add ReAct loop to `AICouncilService` Stage 1
- Implement reasoning chain tracking
- Add plan generation capability
- Unit tests for ReAct logic

### Sprint 63: Memory Enhancement (2 weeks)

- Design agent memory schema
- Implement memory retrieval (Redis + pgvector)
- Add context window optimization
- Migration for existing projects

### Sprint 64: Tool Orchestration (2 weeks)

- Add parallel tool executor
- Implement tool interruption
- Add tool result aggregation
- Integration with EP-06 codegen

**Total Effort**: 8 weeks across 4 sprints  
**Risk**: LOW (incremental, no external dependencies)

---

## Patterns to Extract

### 1. ReAct Loop Pattern

```python
# Inspired by AgentScope's ReAct implementation
# To be added to AICouncilService Stage 1

async def react_loop(self, task: str) -> str:
    """
    Reasoning and Acting loop for complex tasks
    """
    thoughts = []
    actions = []
    
    for step in range(max_steps):
        # Reasoning step
        thought = await self._reason(task, thoughts, actions)
        thoughts.append(thought)
        
        # Action step
        action = await self._act(thought)
        actions.append(action)
        
        # Observation
        observation = await self._observe(action)
        
        if self._is_complete(observation):
            break
    
    return self._synthesize(thoughts, actions)
```

### 2. Long-term Memory Pattern

```python
# Inspired by AgentScope's ReMe (Retrieval-enhanced Memory)

class AgentMemory:
    """
    Long-term memory with semantic retrieval
    """
    def __init__(self, redis_client, vector_store):
        self.redis = redis_client
        self.vectors = vector_store  # pgvector
    
    async def store(self, agent_id: str, context: dict):
        """Store agent interaction with embedding"""
        embedding = await self._embed(context)
        await self.vectors.store(agent_id, embedding, context)
        await self.redis.lpush(f"agent:{agent_id}:history", context)
    
    async def retrieve(self, agent_id: str, query: str, k: int = 5):
        """Semantic retrieval of relevant past interactions"""
        query_embedding = await self._embed(query)
        similar = await self.vectors.search(agent_id, query_embedding, k)
        return similar
```

### 3. Tool Orchestration Pattern

```python
# Inspired by AgentScope's ServiceToolkit

class ToolOrchestrator:
    """
    Parallel tool execution with interruption support
    """
    async def execute_tools(self, tools: List[Tool], context: dict):
        """Execute multiple tools in parallel"""
        tasks = [tool.execute(context) for tool in tools]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Aggregate results
        successful = [r for r in results if not isinstance(r, Exception)]
        failed = [r for r in results if isinstance(r, Exception)]
        
        return {
            "successful": successful,
            "failed": failed,
            "summary": self._summarize(successful)
        }
```

---

## Consequences

### Positive

- ✅ **Maintain full control** of AI architecture
- ✅ **No new dependencies** or license risks
- ✅ **Learn from industry best practices** (Alibaba research)
- ✅ **Incremental enhancement** with low risk
- ✅ **Team skills development** in agent patterns

### Negative

- ⚠️ **DIY maintenance burden** (vs. framework updates)
- ⚠️ **4 sprints of development** (8 weeks)
- ⚠️ **No AgentScope Studio** visualization (use Grafana instead)

### Risks

| Risk | Mitigation |
|------|-----------|
| Pattern extraction takes longer than expected | Limit scope to ReAct + Memory only; defer Tool orchestration |
| Custom implementation has bugs | Comprehensive unit tests; gradual rollout |
| AgentScope adds killer feature | Quarterly review process (Q2 2026) |

---

## Review Gate

**Q2 2026 Reassessment**: Revisit AgentScope integration if:

- Custom ReAct/Memory implementation proves insufficient
- Enterprise customer explicitly requests AgentScope
- AGPL assessment completed and deemed safe
- AgentScope adds critical enterprise features

---

## References

### Existing Architecture

- [backend/app/services/ai_council_service.py](../../backend/app/services/ai_council_service.py) - 1,550 lines
- [backend/app/services/codegen/codegen_service.py](../../backend/app/services/codegen/codegen_service.py) - 614 lines
- [backend/app/services/ollama_service.py](../../backend/app/services/ollama_service.py) - 874 lines
- [ADR-007: AI Context Engine](./ADR-007-AI-Context-Engine.md)
- [ADR-022: Multi-Provider Codegen Architecture](./ADR-022-Multi-Provider-Codegen-Architecture.md)

### AgentScope Resources

- **GitHub**: https://github.com/agentscope-ai/agentscope
- **Docs**: https://doc.agentscope.io/
- **License**: Apache 2.0
- **Paper**: "AgentScope: A Developer-Centric Multi-Agent Platform" (Alibaba, 2024)

---

## Document Control

| Field | Value |
|-------|-------|
| Version | 1.0 |
| Status | ✅ APPROVED |
| Decision | Extract patterns only, NO runtime integration |
| Risk Level | LOW (pattern extraction) |
| Next Review | Q2 2026 |
| Related ADRs | ADR-007, ADR-022 |

---

## Approval

**CTO Approval**: ✅ December 28, 2025

**Signature**:
```
Approved for "Inspired Evolution" strategy.
Patterns to be extracted and implemented in Sprint 61-64.
AgentScope runtime integration explicitly REJECTED.
Review gate: Q2 2026.
```
