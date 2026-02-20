# ADR-034: Planning Sub-agent Orchestration
## Preventing Architectural Drift via Pre-Planning Pattern Extraction

**Status**: ✅ APPROVED (CTO Approved - January 23, 2026)
**Date**: January 22, 2026
**Approved**: January 23, 2026
**Decision Makers**: CTO, CPO
**Stage**: Stage 02 (HOW - Design & Architecture)
**Framework**: SDLC 6.1.0
**Sprint**: Sprint 97-100 (January - February 2026)
**Priority**: P1 - KEY DIFFERENTIATOR
**Reference**: Expert Workflow Analysis (Jan 2026)
**Implementation Status**: Sprint 98 COMPLETE, Sprint 99-100 IN PROGRESS

---

## Context

### Problem Statement

When AI agents make changes exceeding 15 lines of code (LOC), **architectural drift** becomes a significant risk:

1. **Pattern Inconsistency**: New code doesn't follow existing codebase patterns
2. **ADR Violation**: Architectural decisions are ignored or contradicted
3. **Convention Drift**: Code style and naming conventions become inconsistent
4. **Test Pattern Mismatch**: Tests don't follow existing test patterns

**Expert Observation (Jan 2026):**

> "Khi không dùng planning mode, codebase dễ bị architectural drift. Planning mode spawns explore sub-agents → extract patterns → build on them. This prevents drift."

### Current State

| Aspect | Current Implementation | Gap |
|--------|----------------------|-----|
| Code Generation | Multi-provider (Ollama → Claude) | ✅ Working |
| Quality Gates | 4-Gate Pipeline (Syntax → Security → Context → Tests) | ✅ Working |
| Pattern Extraction | None before generation | ❌ KEY GAP |
| ADR Awareness | Manual reference only | ❌ No automated check |
| Pre-planning | Not implemented | ❌ KEY GAP |

### Expert Workflow Analysis

```
Expert Workflow (2026):

┌─────────────────────────────────────────────────────────────────┐
│ PLANNING MODE (ALWAYS for >15 LOC changes)                      │
│                                                                 │
│  ┌────────────┐   ┌────────────┐   ┌────────────┐              │
│  │ Explore    │   │ Explore    │   │ Explore    │              │
│  │ Sub-agent  │   │ Sub-agent  │   │ Sub-agent  │              │
│  │ (patterns) │   │ (similar)  │   │ (ADRs)     │              │
│  └─────┬──────┘   └─────┬──────┘   └─────┬──────┘              │
│        │                │                │                      │
│        └────────────────┼────────────────┘                      │
│                         ▼                                       │
│               ┌─────────────────┐                               │
│               │ Planning Agent  │                               │
│               │ "Build on ADRs" │                               │
│               └─────────────────┘                               │
│                         │                                       │
│                         ▼ PREVENTS ARCHITECTURAL DRIFT          │
└─────────────────────────────────────────────────────────────────┘
```

**Key Expert Insight:**

> "Agentic grep (AI-powered code search) > RAG for context retrieval. Direct codebase exploration finds real patterns. RAG can miss context and produce stale results."

---

## Decision

### Implement Planning Mode with Sub-agent Orchestration

We will implement a **planning mode** that spawns sub-agents to extract patterns before code generation:

```
┌─────────────────────────────────────────────────────────────────────┐
│                    PLANNING SUB-AGENT ORCHESTRATION                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  INPUT: Task description + context                                  │
│                                                                     │
│  PHASE 1: PATTERN EXTRACTION (Parallel Sub-agents)                  │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐  │ │
│  │ │ Similar Code    │ │ ADR Patterns    │ │ Test Patterns   │  │ │
│  │ │ Explorer        │ │ Explorer        │ │ Explorer        │  │ │
│  │ │                 │ │                 │ │                 │  │ │
│  │ │ - Find similar  │ │ - Load relevant │ │ - Find test     │  │ │
│  │ │   implementations │ │   ADRs        │ │   patterns      │  │ │
│  │ │ - Extract code  │ │ - Extract       │ │ - Extract       │  │ │
│  │ │   patterns      │ │   constraints   │ │   conventions   │  │ │
│  │ └────────┬────────┘ └────────┬────────┘ └────────┬────────┘  │ │
│  │          │                    │                    │          │ │
│  │          └────────────────────┼────────────────────┘          │ │
│  └───────────────────────────────┼───────────────────────────────┘ │
│                                  ▼                                  │
│  PHASE 2: PATTERN SYNTHESIS                                         │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │ Planning Agent (Synthesize patterns → Implementation plan)    │ │
│  │                                                               │ │
│  │ Output: PlanningContext                                       │ │
│  │   - similar_implementations: [code snippets]                  │ │
│  │   - adr_constraints: [ADR requirements]                       │ │
│  │   - code_patterns: [naming, structure, style]                 │ │
│  │   - test_patterns: [test structure, mocks, assertions]        │ │
│  │   - implementation_plan: [step-by-step approach]              │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                                  │                                  │
│                                  ▼                                  │
│  PHASE 3: HUMAN APPROVAL                                            │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │ Present plan for approval:                                    │ │
│  │   - Show extracted patterns                                   │ │
│  │   - Show ADR constraints that apply                           │ │
│  │   - Show proposed implementation approach                     │ │
│  │   - Request approval before proceeding                        │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                                  │                                  │
│                                  ▼                                  │
│  PHASE 4: CONTEXT-AWARE GENERATION                                  │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │ Code Generator (with PlanningContext injected)                │ │
│  │   - Generate code following extracted patterns                │ │
│  │   - Respect ADR constraints                                   │ │
│  │   - Match test patterns                                       │ │
│  │   - Validate against plan before output                       │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  OUTPUT: Code that follows existing patterns + Evidence             │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### CLI Command: `sdlcctl plan`

```bash
# Plan a task before implementation
sdlcctl plan "Add authentication middleware for API routes"

# Options
sdlcctl plan --task "Add logging to all service methods" \
             --scope backend/app/services \
             --depth thorough  # quick | medium | thorough
             --output plan.md

# Example output:
#
# Planning: Add authentication middleware for API routes
#
# ═══════════════════════════════════════════════════════════
# PHASE 1: Pattern Extraction
# ═══════════════════════════════════════════════════════════
#
# Similar Implementations Found:
#   1. backend/app/middleware/cors_middleware.py (87% similar)
#   2. backend/app/middleware/logging_middleware.py (72% similar)
#   3. backend/app/middleware/rate_limit_middleware.py (65% similar)
#
# ADR Constraints:
#   - ADR-002: JWT tokens with 15min expiry
#   - ADR-002: OAuth 2.0 support required
#   - ADR-007: Multi-provider fallback for AI operations
#
# Code Patterns:
#   - Middleware class with __call__ method
#   - Async/await pattern used
#   - Logger injection via dependency
#   - Exception handling with HTTPException
#
# Test Patterns:
#   - pytest-asyncio for async tests
#   - Mock external dependencies
#   - Test both success and failure paths
#
# ═══════════════════════════════════════════════════════════
# PHASE 2: Implementation Plan
# ═══════════════════════════════════════════════════════════
#
# Proposed Steps:
#   1. Create AuthMiddleware class in middleware/auth_middleware.py
#   2. Implement JWT validation using existing auth_service
#   3. Add OAuth token validation fallback
#   4. Register middleware in app startup
#   5. Create unit tests following existing patterns
#
# Estimated Changes:
#   - New: backend/app/middleware/auth_middleware.py (~80 LOC)
#   - Modified: backend/app/main.py (+5 LOC)
#   - New: backend/tests/middleware/test_auth_middleware.py (~120 LOC)
#
# ═══════════════════════════════════════════════════════════
#
# [A]pprove and proceed | [M]odify plan | [C]ancel
```

### API Endpoints

```yaml
POST /api/v1/projects/{project_id}/plan
  Description: Create implementation plan for a task
  Request:
    task_description: string
    scope: string[]  # Directories/files to consider
    depth: enum [quick, medium, thorough]
  Response:
    plan_id: uuid
    similar_implementations: Implementation[]
    adr_constraints: ADRConstraint[]
    code_patterns: Pattern[]
    test_patterns: Pattern[]
    implementation_plan: Step[]
    estimated_changes: ChangeEstimate[]

GET /api/v1/projects/{project_id}/plans/{plan_id}
  Description: Get plan details
  Response: PlanningContext

POST /api/v1/projects/{project_id}/plans/{plan_id}/approve
  Description: Approve plan for implementation
  Request:
    modifications: string[]  # Optional modifications
  Response:
    approved: boolean
    context_id: uuid  # For injection into generation

DELETE /api/v1/projects/{project_id}/plans/{plan_id}
  Description: Cancel/reject plan
```

### Database Schema

```sql
CREATE TABLE planning_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id),
    task_description TEXT NOT NULL,
    scope JSONB,  -- Array of directories/files
    depth VARCHAR(20) DEFAULT 'medium',
    status VARCHAR(20) DEFAULT 'extracting',  -- extracting, synthesizing, pending_approval, approved, rejected

    -- Extracted patterns
    similar_implementations JSONB,
    adr_constraints JSONB,
    code_patterns JSONB,
    test_patterns JSONB,

    -- Synthesized plan
    implementation_plan JSONB,
    estimated_changes JSONB,

    -- Approval
    approved_by UUID REFERENCES users(id),
    approved_at TIMESTAMP WITH TIME ZONE,
    modifications JSONB,

    -- Audit
    created_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_planning_sessions_project ON planning_sessions(project_id);
CREATE INDEX idx_planning_sessions_status ON planning_sessions(status);
```

### Integration with Existing Systems

```yaml
Evidence Vault Integration:
  - Store planning context as evidence artifact
  - Link to code generation evidence
  - Complete audit trail: plan → approval → generation → validation

Gate Integration:
  - G-Sprint gate can require planning for large changes
  - Planning context injected into AI prompts during G3

Dynamic Context Overlay:
  - PlanningContext becomes part of dynamic overlay
  - Injected into PR comments, CLI output, VS Code panel
```

---

## Consequences

### Positive

1. **Prevent Architectural Drift**: 90% reduction in pattern violations
2. **ADR Compliance**: Automated ADR constraint extraction and validation
3. **Consistent Codebase**: Generated code follows existing patterns
4. **Audit Trail**: Full traceability from plan → code → evidence
5. **Human Oversight**: Approval gate before significant changes
6. **Quality Improvement**: Better first-pass code quality

### Negative

1. **Additional Latency**: ~30-60s for pattern extraction
2. **Complexity**: More infrastructure to maintain
3. **Learning Curve**: Teams need to adopt planning workflow

### Neutral

1. **Optional for Small Changes**: <15 LOC changes can skip planning
2. **Configurable Depth**: Teams choose quick/medium/thorough based on risk

---

## Implementation Plan

### Phase 1: Core Infrastructure (Sprint 94-95)

| Task | Effort | Owner |
|------|--------|-------|
| Create planning_sessions table migration | 2d | Backend |
| Implement PlanningService core | 3d | Backend |
| Similar code explorer sub-agent | 3d | Backend |
| ADR explorer sub-agent | 2d | Backend |
| Test pattern explorer sub-agent | 2d | Backend |

### Phase 2: CLI & API (Sprint 96)

| Task | Effort | Owner |
|------|--------|-------|
| Add `sdlcctl plan` command | 3d | Backend |
| Planning API endpoints | 2d | Backend |
| Integration with codegen service | 2d | Backend |
| Evidence Vault integration | 1d | Backend |

### Phase 3: Integration & Polish (Sprint 97-98)

| Task | Effort | Owner |
|------|--------|-------|
| VS Code Extension integration | 3d | Frontend |
| Dashboard planning view | 2d | Frontend |
| Gate integration (G-Sprint) | 2d | Backend |
| Documentation & examples | 2d | PM |

---

## Alternatives Considered

### Alternative 1: RAG-Based Pattern Retrieval

**Rejected**: Expert insight indicates "agentic grep > RAG" for pattern extraction. RAG can miss context and produce stale results from indexed data.

### Alternative 2: Static Pattern Library

**Rejected**: Patterns evolve with codebase. Static library becomes outdated quickly and doesn't capture project-specific conventions.

### Alternative 3: Post-Generation Validation Only

**Rejected**: Catching pattern violations after generation wastes cycles. Prevention is more efficient than correction.

---

## References

- Expert Workflow Analysis (Jan 2026) - Plan file Section 15
- [ADR-029: AGENTS.md Integration Strategy](ADR-029-AGENTS-MD-Integration-Strategy.md)
- [ADR-022: Multi-Provider Codegen Architecture](ADR-022-Multi-Provider-Codegen-Architecture.md)
- [SDLC-Agentic-Core-Principles.md](../../SDLC-Enterprise-Framework/02-Core-Methodology/SDLC-Agentic-Core-Principles.md)

---

## Approval

| Role | Name | Date | Signature |
|------|------|------|-----------|
| CTO | CTO | January 23, 2026 | ✅ APPROVED |
| CPO | CPO | January 23, 2026 | ✅ APPROVED |
| Backend Lead | Backend Lead | January 23, 2026 | ✅ APPROVED |

---

## Implementation Progress

### Sprint 98 (COMPLETE - January 22-25, 2026)

| Deliverable | Status | File |
|-------------|--------|------|
| PlanningOrchestratorService | ✅ Complete | `backend/app/services/planning_orchestrator_service.py` |
| PatternExtractionService | ✅ Complete | `backend/app/services/pattern_extraction_service.py` |
| ADRScannerService | ✅ Complete | `backend/app/services/adr_scanner_service.py` |
| TestPatternService | ✅ Complete | `backend/app/services/test_pattern_service.py` |
| Planning Schemas | ✅ Complete | `backend/app/schemas/planning_subagent.py` |
| Integration Tests | ✅ Complete | `backend/tests/integration/test_plan_command.py` |

**Design Document**: [Planning-Orchestrator-Service-Design.md](../14-Technical-Specs/Planning-Orchestrator-Service-Design.md)

### Sprint 99 (IN PROGRESS)

| Deliverable | Status |
|-------------|--------|
| ConformanceCheckService | ⏳ Pending |
| Planning Subagent API Routes | ⏳ Pending |
| Plan Approval UI | ⏳ Pending |
| GitHub Check Integration | ⏳ Pending |
| E2E Tests | ⏳ Pending |

**Design Document**: [Conformance-Check-Service-Design.md](../14-Technical-Specs/Conformance-Check-Service-Design.md)

### Sprint 100 (PLANNED)

| Deliverable | Status |
|-------------|--------|
| FeedbackLearningService | ⏳ Planned |
| pr_learnings table | ⏳ Planned |
| decomposition_hints table | ⏳ Planned |
| Feedback Loop Integration | ⏳ Planned |

**Design Document**: [Feedback-Learning-Service-Design.md](../14-Technical-Specs/Feedback-Learning-Service-Design.md)

---

**Document Version**: 1.1.0
**Created**: January 22, 2026
**Last Updated**: January 23, 2026
**Change Log**:
- v1.1.0 (Jan 23, 2026): Updated to APPROVED, added implementation progress
