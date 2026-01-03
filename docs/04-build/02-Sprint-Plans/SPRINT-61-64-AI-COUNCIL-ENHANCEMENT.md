# Sprint 61-64: AI Council Enhancement Roadmap
## "Inspired Evolution" - AgentScope Pattern Implementation

**Epic**: AI Council Multi-Agent Enhancement  
**Framework**: SDLC 5.1.2 Universal Framework  
**Duration**: 8 weeks (Q1 2026)  
**Decision Reference**: [ADR-023: AgentScope Pattern Extraction](../../02-design/01-ADRs/ADR-023-AgentScope-Pattern-Extraction.md)

---

## Executive Summary

Enhance `AICouncilService` with advanced agent patterns inspired by AgentScope (Alibaba's 14.6k⭐ framework) **WITHOUT runtime integration**. Extract and implement ReAct loop, long-term memory, and tool orchestration patterns into existing codebase.

### Strategic Rationale

| Factor | Value |
|--------|-------|
| **Cost** | $0 (no new dependencies) |
| **Risk** | LOW (incremental enhancement) |
| **Control** | Full ownership maintained |
| **Learning** | Best practices from Alibaba research |
| **Timeline** | 8 weeks across 4 sprints |

### Decision

✅ **Extract patterns**, ❌ **DO NOT integrate runtime**

---

## Sprint 61: Research Phase
**Duration**: 2 weeks  
**Goal**: Deep-dive AgentScope source + design enhancement schemas

### Objectives

1. **AgentScope Source Analysis**
   - Study ReAct implementation in `agentscope/agents/react_agent.py`
   - Analyze memory architecture in `agentscope/memory/`
   - Review tool orchestration in `agentscope/service/`
   - Extract design patterns to internal wiki

2. **Memory Schema Design**
   - Design agent-specific memory schema (Redis + pgvector)
   - Define context window optimization strategy
   - Plan migration path for existing projects

3. **Pattern Documentation**
   - Create internal pattern library document
   - Document API contracts for new capabilities
   - Write architecture diagrams (Mermaid)

### Deliverables

- [ ] AgentScope pattern extraction report (Markdown)
- [ ] Agent memory schema (PostgreSQL + Redis design)
- [ ] API contract specification (OpenAPI)
- [ ] Architecture diagrams (Mermaid)

### Success Criteria

- Team understands ReAct loop implementation details
- Memory schema reviewed and approved by architect
- Zero code changes (research only)

---

## Sprint 62: ReAct Loop Implementation
**Duration**: 2 weeks  
**Goal**: Add reasoning-action cycle to AICouncilService Stage 1

### Objectives

1. **ReAct Loop Core**
   ```python
   # New method in AICouncilService
   async def react_loop(
       self,
       task: str,
       max_steps: int = 5
   ) -> ReActResult:
       """
       Reasoning and Acting loop for complex tasks
       
       Pattern inspired by AgentScope's ReAct agent
       """
   ```

2. **Reasoning Chain Tracking**
   - Store reasoning steps in Redis
   - Track action outcomes
   - Log decision paths for debugging

3. **Plan Generation**
   - Add `generate_plan()` method
   - Implement step-by-step task decomposition
   - Integrate with existing IR processor

### Files Modified

- `backend/app/services/ai_council_service.py` (add ReAct methods)
- `backend/app/schemas/ai_council.py` (new Pydantic models)
- `backend/app/core/config.py` (add ReAct config)

### Deliverables

- [ ] ReAct loop implementation
- [ ] Unit tests (>80% coverage)
- [ ] Integration tests with Ollama
- [ ] API endpoint `/api/v1/ai/council/react`
- [ ] Documentation update

### Success Criteria

- ReAct loop successfully decomposes complex tasks
- All tests pass
- Latency <5s for 3-step tasks
- Backward compatible with existing AICouncil API

---

## Sprint 63: Long-term Memory Enhancement
**Duration**: 2 weeks  
**Goal**: Upgrade Redis cache to agent-specific semantic memory

### Objectives

1. **Memory Storage Layer**
   ```python
   # New AgentMemory class
   class AgentMemory:
       def __init__(self, redis: Redis, pgvector: PGVector):
           self.redis = redis
           self.vectors = pgvector
       
       async def store(self, agent_id: str, interaction: dict):
           """Store with semantic embedding"""
       
       async def retrieve(self, agent_id: str, query: str, k: int = 5):
           """Semantic retrieval of past interactions"""
   ```

2. **Context Window Optimization**
   - Implement sliding window for token budget
   - Add relevance scoring for memory recall
   - Prune low-value memories

3. **Cross-Session Context**
   - Enable memory persistence across sessions
   - Link project-level context
   - Add user-specific memory isolation

### Database Schema

```sql
-- New table in PostgreSQL
CREATE TABLE agent_memories (
    id UUID PRIMARY KEY,
    agent_id VARCHAR(50) NOT NULL,
    project_id UUID REFERENCES projects(id),
    interaction_type VARCHAR(50),
    content JSONB NOT NULL,
    embedding VECTOR(1536),  -- pgvector
    created_at TIMESTAMP DEFAULT NOW(),
    relevance_score FLOAT DEFAULT 1.0
);

CREATE INDEX ON agent_memories USING ivfflat (embedding vector_cosine_ops);
```

### Deliverables

- [ ] `AgentMemory` service implementation
- [ ] Database migration script
- [ ] Redis → pgvector integration
- [ ] Memory retrieval API
- [ ] Alembic migration file

### Success Criteria

- Semantic retrieval works for past interactions
- Query latency <200ms for k=5 retrieval
- Memory survives session restarts
- Migration runs successfully on staging

---

## Sprint 64: Tool Orchestration
**Duration**: 2 weeks  
**Goal**: Parallel tool execution with interruption support

### Objectives

1. **Parallel Tool Executor**
   ```python
   # New ToolOrchestrator class
   class ToolOrchestrator:
       async def execute_tools(
           self,
           tools: List[Tool],
           context: dict
       ) -> ToolExecutionResult:
           """Execute multiple tools in parallel"""
           tasks = [tool.execute(context) for tool in tools]
           results = await asyncio.gather(*tasks, return_exceptions=True)
           return self._aggregate(results)
   ```

2. **Tool Interruption**
   - Add timeout support per tool
   - Implement graceful cancellation
   - Handle partial results

3. **Result Aggregation**
   - Summarize multi-tool outputs
   - Detect conflicts between tools
   - Prioritize results by confidence

### Integration with EP-06 Codegen

- Connect ToolOrchestrator with CodegenService
- Enable multi-provider parallel codegen
- Add tool result caching

### Deliverables

- [ ] `ToolOrchestrator` service
- [ ] Tool timeout + cancellation logic
- [ ] Result aggregation algorithm
- [ ] Integration with EP-06 codegen
- [ ] Performance benchmarks

### Success Criteria

- 3 tools execute in parallel successfully
- Timeout works (tool stops after 30s)
- Failed tools don't block successful ones
- Aggregation improves codegen quality

---

## Testing Strategy

### Unit Tests

- ReAct loop: 15 test cases
- AgentMemory: 20 test cases
- ToolOrchestrator: 18 test cases
- **Target Coverage**: >80%

### Integration Tests

- End-to-end ReAct workflow with Ollama
- Memory retrieval across sessions
- Multi-tool parallel execution
- Fallback scenarios

### Performance Tests

- ReAct loop latency: <5s for 3-step tasks
- Memory retrieval: <200ms for k=5
- Tool orchestration: 3 parallel tools <10s

---

## Risks & Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Pattern extraction takes longer | Schedule slip | MEDIUM | Limit scope to ReAct + Memory only |
| Memory migration breaks prod | Data loss | LOW | Full backup + staging validation |
| Tool orchestration complexity | Delayed launch | MEDIUM | Defer to Sprint 65 if needed |
| Team learning curve | Low velocity | LOW | Pair programming + code reviews |

---

## Dependencies

### External

- AgentScope source code (read-only reference)
- pgvector extension for PostgreSQL
- OpenAI embedding API (for semantic search)

### Internal

- `AICouncilService` (base implementation)
- `CodegenService` (tool integration)
- `OllamaService` (LLM provider)
- Redis cache layer
- PostgreSQL with pgvector

---

## Success Metrics

| Metric | Baseline | Target | Measurement |
|--------|----------|--------|-------------|
| Task decomposition quality | N/A | >85% correct steps | Manual QA |
| Memory recall accuracy | N/A | >90% relevance | Semantic similarity |
| Tool execution parallelism | 1x sequential | 3x parallel | Latency reduction |
| AICouncil response quality | 7.5/10 | 8.5/10 | User feedback |
| Code coverage | 75% | >80% | pytest-cov |

---

## Rollout Plan

### Phase 1: Internal Testing (Sprint 61-62)

- ReAct loop tested with internal projects only
- Flag: `ENABLE_REACT_LOOP=false` (default off)

### Phase 2: Beta Testing (Sprint 63)

- Memory enhancement rolled out to 10 beta users
- Monitoring for memory leaks and retrieval accuracy

### Phase 3: General Availability (Sprint 64)

- All features enabled for all users
- Documentation published
- Blog post: "How We Enhanced AI Council with Agent Patterns"

---

## Budget

| Item | Cost | Notes |
|------|------|-------|
| Development time | $0 | Internal team |
| OpenAI embeddings | ~$20/mo | For semantic search |
| pgvector storage | $0 | Existing PostgreSQL |
| Testing infrastructure | $0 | Existing staging |
| **Total** | **~$20/mo** | Minimal incremental cost |

**vs. AgentScope Integration**: Saved $0 licensing + 6 weeks effort

---

## Review Gates

### Sprint 61 Exit Criteria

- [ ] Pattern extraction report approved
- [ ] Memory schema design reviewed
- [ ] Team trained on ReAct concepts

### Sprint 62 Exit Criteria

- [ ] ReAct loop passes all tests
- [ ] API documented in Swagger
- [ ] No regression in existing features

### Sprint 63 Exit Criteria

- [ ] Memory migration runs successfully
- [ ] Retrieval latency <200ms
- [ ] 10 beta users testing

### Sprint 64 Exit Criteria

- [ ] Tool orchestration in production
- [ ] All 4 sprints documented
- [ ] Blog post published

---

## Follow-up Actions (Sprint 65+)

1. **Visualization**: Add agent workflow visualization to admin panel
2. **Monitoring**: OpenTelemetry tracing for ReAct loops
3. **Optimization**: Fine-tune memory retrieval algorithms
4. **Enterprise Features**: Multi-tenant memory isolation

---

## References

- [ADR-023: AgentScope Pattern Extraction](../../02-design/01-ADRs/ADR-023-AgentScope-Pattern-Extraction.md)
- [ADR-022: Multi-Provider Codegen Architecture](../../02-design/01-ADRs/ADR-022-Multi-Provider-Codegen-Architecture.md)
- [ADR-007: AI Context Engine](../../02-design/01-ADRs/ADR-007-AI-Context-Engine.md)
- [AgentScope GitHub](https://github.com/agentscope-ai/agentscope)
- [AgentScope Documentation](https://doc.agentscope.io/)

---

## Approval

**CTO Approval**: ✅ December 28, 2025

**Sprint Commitment**:
```
Sprint 61-64 roadmap approved.
Team assigned: 2 backend engineers + 1 architect.
Budget: ~$20/mo incremental.
Review gate: End of Sprint 64.
AgentScope runtime integration remains PROHIBITED.
```

---

**Last Updated**: December 28, 2025  
**Next Review**: End of Sprint 64 (Q1 2026)
