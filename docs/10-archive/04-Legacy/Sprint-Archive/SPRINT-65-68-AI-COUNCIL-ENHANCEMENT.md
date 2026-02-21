# Sprint 65-68: AI Council Enhancement Roadmap
## "Inspired Evolution" - AgentScope Pattern Implementation

**Epic**: AI Council Multi-Agent Enhancement  
**Framework**: SDLC 6.1.0
**Duration**: 8 weeks (Q1/Q2 2026)  
**Decision Reference**: [ADR-023: AgentScope Pattern Extraction](../../02-design/01-ADRs/ADR-023-AgentScope-Pattern-Extraction.md)

---

## Executive Summary

Enhance `AICouncilService` with advanced agent patterns inspired by AgentScope (Alibaba's framework) **WITHOUT runtime integration**. Extract and implement ReAct loop, long-term memory, and tool orchestration patterns into existing codebase.

### Decision

✅ **Extract patterns**, ❌ **DO NOT integrate runtime**

---

## Sprint 65: Research Phase
**Duration**: 2 weeks  
**Goal**: Deep-dive AgentScope source + design enhancement schemas

### Deliverables
- [ ] AgentScope pattern extraction report (Markdown)
- [ ] Agent memory schema (PostgreSQL + Redis design)
- [ ] API contract specification (OpenAPI)
- [ ] Architecture diagrams (Mermaid)

---

## Sprint 66: ReAct Loop Implementation
**Duration**: 2 weeks  
**Goal**: Add reasoning-action cycle to AICouncilService Stage 1

### Files Modified
- `backend/app/services/ai_council_service.py`
- `backend/app/schemas/ai_council.py`
- `backend/app/core/config.py`

### Deliverables
- [ ] ReAct loop implementation
- [ ] Unit tests (>80% coverage)
- [ ] Integration tests with Ollama
- [ ] API endpoint `/api/v1/ai/council/react`

---

## Sprint 67: Long-term Memory Enhancement
**Duration**: 2 weeks  
**Goal**: Upgrade Redis cache to agent-specific semantic memory

### Deliverables
- [ ] `AgentMemory` service implementation
- [ ] Database migration script
- [ ] Redis → pgvector integration
- [ ] Memory retrieval API

---

## Sprint 68: Tool Orchestration
**Duration**: 2 weeks  
**Goal**: Parallel tool execution with interruption support

### Deliverables
- [ ] `ToolOrchestrator` service
- [ ] Tool timeout + cancellation logic
- [ ] Result aggregation algorithm
- [ ] Integration with EP-06 codegen

---

## Notes

This roadmap was originally planned as Sprint 61–64, but was **rescheduled** because Sprint 61–64 is now allocated to **frontend platform consolidation (Next.js)** per ADR-025.

## References

- [ADR-023: AgentScope Pattern Extraction](../../02-design/01-ADRs/ADR-023-AgentScope-Pattern-Extraction.md)
- [ADR-022: Multi-Provider Codegen Architecture](../../02-design/01-ADRs/ADR-022-Multi-Provider-Codegen-Architecture.md)
