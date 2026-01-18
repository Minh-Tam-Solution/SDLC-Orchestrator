# PHASE-01: AI Council Service
## AI Task Decomposition & Multi-Provider Fallback

**Version**: 1.0.0
**Date**: December 3, 2025
**Status**: PLANNED - Sprint 26
**Duration**: 5 days (Dec 9-13, 2025)
**Owner**: Tech Lead + Backend Team
**Framework**: SDLC 5.1.3.1 Complete Lifecycle

---

## Executive Summary

PHASE-01 implements the **AI Council Service** - the core engine for AI-powered task decomposition. This enables ANY PM to achieve CEO-level quality when breaking down user stories into actionable tasks.

**Key Deliverables**:
1. AI Task Decomposition API (User Story → Sub-Tasks)
2. Multi-Provider Fallback Chain (Ollama → Claude → GPT-4o → Rule-based)
3. Context Builder (Project state → AI context)
4. Decomposition Session Management (Track quality metrics)

**Success Criteria**:
- Decomposition latency <2min end-to-end (p95)
- CEO-quality output for 90%+ of decompositions
- 100% fallback coverage (no failures)

---

## 1. Problem Statement

### Current State (Before PHASE-01)

**Pain Points**:
1. **CEO Bottleneck**: Only CEO can effectively use Claude for task decomposition
2. **Inconsistent Quality**: 10 PMs produce 10 different quality levels
3. **No Context Awareness**: AI doesn't know project state, stage, or constraints
4. **Single Provider Dependency**: If Claude is down, productivity stops

**Evidence**:
- NQH CEO: 1 person → 10 executive-quality documents/day
- NQH PMs: 10 people → 10 inconsistent documents/week
- Gap: 100x productivity difference

### Target State (After PHASE-01)

- ANY PM can produce CEO-quality task decomposition
- Multi-provider fallback ensures 100% availability
- Context-aware AI knows project state, stage, and constraints
- Quality metrics track and improve over time

---

## 2. Technical Architecture

### 2.1 Component Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    AI COUNCIL SERVICE                           │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │ Context Builder │  │ Provider Router │  │ Quality Scorer  │ │
│  │                 │  │                 │  │                 │ │
│  │ - Project state │  │ - Ollama        │  │ - Completeness  │ │
│  │ - Gate status   │  │ - Claude        │  │ - Actionability │ │
│  │ - Evidence      │  │ - GPT-4o        │  │ - Alignment     │ │
│  │ - Stage context │  │ - Rule-based    │  │ - Metrics       │ │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘ │
│           │                    │                    │           │
│           └────────────────────┴────────────────────┘           │
│                                │                                 │
│                    ┌───────────┴───────────┐                    │
│                    │ Decomposition Engine  │                    │
│                    │                       │                    │
│                    │ User Story → Tasks    │                    │
│                    │ CEO-quality output    │                    │
│                    └───────────────────────┘                    │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Multi-Provider Fallback Chain

```yaml
Provider Chain (Priority Order):
  1. Ollama (api.nhatquangholding.com):
     - Latency: <100ms
     - Cost: $50/month
     - Model: llama3.1:70b or similar
     - Use case: Primary provider

  2. Claude (Anthropic):
     - Latency: ~300ms
     - Cost: ~$1000/month at scale
     - Model: claude-sonnet-4-5-20250929
     - Use case: Complex reasoning fallback

  3. GPT-4o (OpenAI):
     - Latency: ~250ms
     - Cost: ~$800/month at scale
     - Model: gpt-4o
     - Use case: Code generation fallback

  4. Rule-based:
     - Latency: <50ms
     - Cost: $0
     - Logic: Pre-defined decomposition rules
     - Use case: Last resort (guaranteed response)

Fallback Triggers:
  - API timeout (>5s)
  - Rate limit (429)
  - Server error (5xx)
  - Quality score <60%
```

### 2.3 Database Schema

```sql
-- Migration 007: Decomposition Sessions

CREATE TABLE decomposition_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES users(id),
  input_type VARCHAR(50) NOT NULL CHECK (input_type IN ('user_story', 'epic', 'feature', 'requirement')),
  input_text TEXT NOT NULL,
  provider_used VARCHAR(50) NOT NULL,
  latency_ms INTEGER NOT NULL,
  quality_score DECIMAL(5,2) CHECK (quality_score >= 0 AND quality_score <= 100),
  context_snapshot JSONB NOT NULL DEFAULT '{}',
  status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
  error_message TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  completed_at TIMESTAMPTZ
);

CREATE TABLE decomposed_tasks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID NOT NULL REFERENCES decomposition_sessions(id) ON DELETE CASCADE,
  task_number INTEGER NOT NULL,
  title VARCHAR(255) NOT NULL,
  description TEXT,
  estimated_hours DECIMAL(5,2),
  complexity VARCHAR(20) CHECK (complexity IN ('trivial', 'simple', 'medium', 'complex', 'unknown')),
  dependencies JSONB DEFAULT '[]',
  acceptance_criteria JSONB DEFAULT '[]',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Indexes
CREATE INDEX idx_sessions_project ON decomposition_sessions(project_id);
CREATE INDEX idx_sessions_user ON decomposition_sessions(user_id);
CREATE INDEX idx_sessions_status ON decomposition_sessions(status);
CREATE INDEX idx_tasks_session ON decomposed_tasks(session_id);
```

---

## 3. API Specification

### 3.1 POST /projects/{id}/decompose

**Purpose**: Start AI task decomposition session

**Request**:
```json
{
  "input_type": "user_story",
  "input_text": "As a PM, I want to see real-time compliance status so that I can track project health",
  "options": {
    "max_tasks": 10,
    "include_estimates": true,
    "include_acceptance_criteria": true
  }
}
```

**Response** (201 Created):
```json
{
  "session_id": "uuid",
  "status": "processing",
  "estimated_completion_ms": 2000,
  "provider": "ollama"
}
```

### 3.2 GET /projects/{id}/decomposition-sessions

**Purpose**: List decomposition sessions for project

**Response** (200 OK):
```json
{
  "sessions": [
    {
      "id": "uuid",
      "input_type": "user_story",
      "input_text": "As a PM...",
      "status": "completed",
      "quality_score": 92.5,
      "task_count": 5,
      "created_at": "2025-12-10T10:00:00Z"
    }
  ],
  "pagination": { "page": 1, "total": 10 }
}
```

### 3.3 GET /decomposition-sessions/{session_id}/tasks

**Purpose**: Get decomposed tasks from session

**Response** (200 OK):
```json
{
  "session": {
    "id": "uuid",
    "status": "completed",
    "quality_score": 92.5,
    "latency_ms": 1850,
    "provider_used": "ollama"
  },
  "tasks": [
    {
      "task_number": 1,
      "title": "Create compliance status API endpoint",
      "description": "Implement GET /api/v1/projects/{id}/compliance-status",
      "estimated_hours": 4.0,
      "complexity": "medium",
      "dependencies": [],
      "acceptance_criteria": [
        "Returns current compliance percentage",
        "Includes violation count by severity",
        "Response time <200ms"
      ]
    }
  ]
}
```

---

## 4. Implementation Plan

### Day 1: Foundation (Dec 9)

**Tasks**:
1. Create database migration (decomposition_sessions, decomposed_tasks)
2. Implement base models (SQLAlchemy)
3. Create API routes skeleton (FastAPI)
4. Set up unit tests structure

**Deliverables**:
- Migration applied
- `/projects/{id}/decompose` returns 201 (stub)
- 80%+ test coverage for models

### Day 2: Ollama Integration (Dec 10)

**Tasks**:
1. Implement Ollama adapter (HTTP client to api.nhatquangholding.com)
2. Create context builder (project state → prompt)
3. Implement task parser (AI response → structured tasks)
4. Integration tests with Ollama

**Deliverables**:
- Ollama provider working
- Context builder tested
- Task parsing validated

### Day 3: Fallback Chain (Dec 11)

**Tasks**:
1. Implement Claude adapter (Anthropic API)
2. Implement GPT-4o adapter (OpenAI API)
3. Implement rule-based fallback
4. Create provider router (fallback logic)

**Deliverables**:
- All 4 providers working
- Fallback chain tested
- 100% coverage guarantee

### Day 4: Quality & Polish (Dec 12)

**Tasks**:
1. Implement quality scorer (task evaluation)
2. Add latency tracking
3. Create frontend decomposition UI (basic)
4. End-to-end testing

**Deliverables**:
- Quality scoring operational
- Metrics collection working
- E2E tests passing

### Day 5: Integration & Validation (Dec 13)

**Tasks**:
1. Integration with existing project views
2. Load testing (100 concurrent sessions)
3. Documentation update
4. CTO review & approval

**Deliverables**:
- Production-ready code
- Load test results
- CTO approval

---

## 5. Success Criteria

### Performance Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Decomposition latency (p95) | <2min | Prometheus histogram |
| Fallback success rate | 100% | Provider router logs |
| Quality score average | >85% | decomposition_sessions.quality_score |
| Session completion rate | >95% | status = 'completed' / total |

### Quality Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Task completeness | 100% | All tasks have title + description |
| Estimate accuracy | ±30% | Compare to actual (post-implementation) |
| Acceptance criteria | >80% tasks | Tasks with AC defined |
| CEO validation | 90%+ approved | Manual review sample |

### Technical Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Unit test coverage | 95%+ | pytest --cov |
| Integration test pass | 100% | CI/CD pipeline |
| Error rate | <1% | Sentry errors / total requests |
| API response time | <200ms | Prometheus (excluding AI call) |

---

## 6. Risk Assessment

### Risk 1: Ollama API Instability

**Probability**: Medium (30%)
**Impact**: High
**Mitigation**: Multi-provider fallback ensures 100% availability
**Contingency**: Promote Claude to primary if Ollama >5% failure rate

### Risk 2: Quality Score <80%

**Probability**: Low (15%)
**Impact**: Medium
**Mitigation**: CEO validation during development, prompt tuning
**Contingency**: Extend Day 4-5 for quality improvement

### Risk 3: Context Builder Performance

**Probability**: Low (10%)
**Impact**: Medium
**Mitigation**: Limit context size, use summary for large projects
**Contingency**: Implement context caching

---

## 7. Dependencies

### External Dependencies

| Dependency | Owner | Status | Risk |
|------------|-------|--------|------|
| Ollama API (api.nhatquangholding.com) | Infra Team | ✅ Available | Low |
| Anthropic API key | DevOps | ✅ Available | Low |
| OpenAI API key | DevOps | ✅ Available | Low |

### Internal Dependencies

| Dependency | Owner | Status | Risk |
|------------|-------|--------|------|
| Projects table | Sprint 15 | ✅ Complete | None |
| Users table | Sprint 12 | ✅ Complete | None |
| Frontend project view | Sprint 20 | ✅ Complete | None |

---

## 8. Team Allocation

| Role | Person | Allocation | Focus |
|------|--------|------------|-------|
| Tech Lead | TBD | 100% | Architecture, review |
| Backend Dev 1 | TBD | 100% | Ollama, Claude adapters |
| Backend Dev 2 | TBD | 100% | Router, quality scorer |
| Frontend Dev | TBD | 50% | Decomposition UI |
| DevOps | TBD | 25% | API keys, monitoring |

---

## 9. Acceptance Criteria (Phase Gate)

### Phase Complete When:

1. ✅ All 3 API endpoints operational
2. ✅ All 4 providers in fallback chain working
3. ✅ Quality score >85% average
4. ✅ Latency <2min (p95)
5. ✅ 95%+ test coverage
6. ✅ CTO approval obtained
7. ✅ 10+ test decomposition sessions validated

### Phase Blocked If:

- ❌ Quality score <60% (requires prompt rewrite)
- ❌ Latency >5min (p95) (architecture issue)
- ❌ Fallback chain failure (requires debugging)

---

## 10. References

- [ADR-011: AI Governance Layer](../../02-design/01-ADRs/ADR-011-AI-Governance-Layer.md)
- [ADR-012: Context-Aware Requirements](../../02-design/01-ADRs/ADR-012-Context-Aware-Requirements.md)
- [Product Roadmap v3.0.0](../../00-Project-Foundation/04-Roadmap/Product-Roadmap.md)
- [Sprint 26 Plan](../02-Sprint-Plans/SPRINT-26-AI-COUNCIL-SERVICE.md)

---

**Document Status**: ✅ APPROVED - Ready for Sprint 26
**Last Updated**: December 3, 2025
**Owner**: Tech Lead + CTO
