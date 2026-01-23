# Planning Orchestrator Service - Technical Design Document
## Core Infrastructure for Planning Sub-agent Orchestration

**Epic**: EP-10 Planning Mode with Sub-agent Orchestration
**Status**: COMPLETE
**Reference**: ADR-034-Planning-Subagent-Orchestration
**Implementation**: Sprint 98 (January 22-25, 2026)

---

## 1. Executive Summary

This document describes the core planning sub-agent infrastructure for SDLC Orchestrator. This includes:

1. **PlanningOrchestratorService** - Main orchestrator for planning sub-agents
2. **PatternExtractionService** - Agentic grep for pattern discovery
3. **ADRScannerService** - ADR pattern extraction
4. **TestPatternService** - Test pattern discovery
5. **Planning Schemas** - Pydantic models for planning feature

### Key Insight (Expert Workflow)

> "Agentic grep > RAG for context retrieval"
> - Direct codebase exploration finds REAL patterns
> - RAG can miss context and produce stale results
> - MANDATORY for changes >15 LOC

---

## 2. Architecture Overview

### 2.1 Component Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PLANNING ORCHESTRATOR                                │
│                    (Sprint 98 - Core Infrastructure)                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                 PlanningOrchestratorService                           │   │
│  │  (backend/app/services/planning_orchestrator_service.py)             │   │
│  │                                                                       │   │
│  │  Responsibilities:                                                    │   │
│  │  • Coordinate sub-agent execution (parallel)                         │   │
│  │  • Synthesize patterns from multiple sources                         │   │
│  │  • Generate implementation plans                                      │   │
│  │  • Calculate conformance scores                                       │   │
│  │  • Manage planning session lifecycle                                  │   │
│  │                                                                       │   │
│  │  Key Methods:                                                         │   │
│  │  • plan(request) → PlanningResult                                    │   │
│  │  • approve_plan(planning_id, approved, notes) → PlanningResult       │   │
│  │  • get_session(planning_id) → PlanningResult                         │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                              │                                               │
│                              │ Spawns parallel sub-agents                    │
│                              ▼                                               │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                    EXPLORE SUB-AGENTS (Parallel Execution)              ││
│  │                                                                          ││
│  │  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐      ││
│  │  │ Pattern          │  │ ADR Scanner      │  │ Test Pattern     │      ││
│  │  │ Extraction       │  │ Service          │  │ Service          │      ││
│  │  │ Service          │  │                  │  │                  │      ││
│  │  │                  │  │                  │  │                  │      ││
│  │  │ • Agentic grep   │  │ • Scan ADRs      │  │ • Find test      │      ││
│  │  │ • Code patterns  │  │ • Extract rules  │  │   patterns       │      ││
│  │  │ • Conventions    │  │ • Conventions    │  │ • Coverage       │      ││
│  │  └──────────────────┘  └──────────────────┘  └──────────────────┘      ││
│  │          │                     │                     │                  ││
│  │          └─────────────────────┼─────────────────────┘                  ││
│  │                                ▼                                         ││
│  │                      [ExploreResult[]]                                   ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                   │                                          │
│                                   ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                         SYNTHESIS LAYER                                  ││
│  │                                                                          ││
│  │  ┌────────────────────────┐    ┌────────────────────────────────────┐   ││
│  │  │ Pattern Synthesizer    │    │ Plan Generator                     │   ││
│  │  │                        │    │                                    │   ││
│  │  │ • Deduplicate          │    │ • Generate steps                   │   ││
│  │  │ • Rank by relevance    │───▶│ • Estimate effort                  │   ││
│  │  │ • Detect conventions   │    │ • Identify risks                   │   ││
│  │  │                        │    │ • Calculate conformance            │   ││
│  │  └────────────────────────┘    └────────────────────────────────────┘   ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                   │                                          │
│                                   ▼                                          │
│                          [PlanningResult]                                    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Data Flow

```
User Request                                                   PlanningResult
    │                                                               ▲
    ▼                                                               │
┌─────────────────┐                                                 │
│ PlanningRequest │                                                 │
│ • task          │                                                 │
│ • project_path  │                                                 │
│ • depth         │                                                 │
│ • include_tests │                                                 │
│ • include_adrs  │                                                 │
│ • auto_approve  │                                                 │
└────────┬────────┘                                                 │
         │                                                          │
         ▼                                                          │
┌─────────────────────────────────────────────────────────────────┐│
│                      PLANNING WORKFLOW                           ││
│                                                                  ││
│  Step 1: EXPLORING ───────────────────────────────────────────┐ ││
│          │                                                     │ ││
│          ▼                                                     │ ││
│  ┌─────────────────────────────────────────────────────────┐  │ ││
│  │ asyncio.gather(                                          │  │ ││
│  │   pattern_service.search_similar_implementations(),      │  │ ││
│  │   adr_service.find_related_adrs(),                       │  │ ││
│  │   test_service.find_test_patterns()                      │  │ ││
│  │ )                                                        │  │ ││
│  └─────────────────────────────────────────────────────────┘  │ ││
│                              │                                 │ ││
│                              ▼                                 │ ││
│  Step 2: SYNTHESIZING ────────────────────────────────────────┤ ││
│          │                                                     │ ││
│          ▼                                                     │ ││
│  ┌─────────────────────────────────────────────────────────┐  │ ││
│  │ _synthesize_patterns(explore_results)                    │  │ ││
│  │ • Deduplicate patterns by name                           │  │ ││
│  │ • Sort by confidence + occurrences                       │  │ ││
│  │ • Calculate category counts                              │  │ ││
│  │ • Detect coding conventions                              │  │ ││
│  └─────────────────────────────────────────────────────────┘  │ ││
│                              │                                 │ ││
│                              ▼                                 │ ││
│  Step 3: GENERATING ──────────────────────────────────────────┤ ││
│          │                                                     │ ││
│          ▼                                                     │ ││
│  ┌─────────────────────────────────────────────────────────┐  │ ││
│  │ _generate_plan(task, patterns, adr_scan)                 │  │ ││
│  │ • Generate implementation steps                          │  │ ││
│  │ • Calculate LOC/hours estimates                          │  │ ││
│  │ • Identify files to create/modify                        │  │ ││
│  │ • Reference relevant ADRs                                │  │ ││
│  │ • Identify risks                                         │  │ ││
│  └─────────────────────────────────────────────────────────┘  │ ││
│                              │                                 │ ││
│                              ▼                                 │ ││
│  Step 4: CONFORMANCE ─────────────────────────────────────────┘ ││
│          │                                                       ││
│          ▼                                                       ││
│  ┌─────────────────────────────────────────────────────────┐    ││
│  │ _calculate_conformance(plan, patterns)                   │    ││
│  │ • Pattern coverage (40 pts)                              │    ││
│  │ • ADR alignment (20 pts)                                 │    ││
│  │ • New patterns check (20 pts)                            │    ││
│  │ • Risk assessment (20 pts)                               │    ││
│  │ • Level: EXCELLENT/GOOD/FAIR/POOR                        │    ││
│  └─────────────────────────────────────────────────────────┘    ││
│                              │                                   ││
│                              ▼                                   ││
│                    AWAITING_APPROVAL                             ││
└──────────────────────────────┼───────────────────────────────────┘│
                               │                                    │
                               └────────────────────────────────────┘
```

---

## 3. Core Services Implementation

### 3.1 PlanningOrchestratorService

**File**: `backend/app/services/planning_orchestrator_service.py`
**Lines**: 829

#### Key Methods

| Method | Description | Input | Output |
|--------|-------------|-------|--------|
| `plan()` | Execute planning mode with sub-agents | `PlanningRequest` | `PlanningResult` |
| `approve_plan()` | Approve or reject a planning session | `planning_id, approved, notes` | `PlanningResult` |
| `get_session()` | Get an active planning session | `planning_id` | `PlanningResult` |
| `list_sessions()` | List all active planning sessions | - | `list[PlanningResult]` |

#### Planning Workflow States

```
EXPLORING → SYNTHESIZING → GENERATING → AWAITING_APPROVAL
                                              │
                            ┌─────────────────┼─────────────────┐
                            ▼                 ▼                 ▼
                        APPROVED          REJECTED          FAILED
```

#### Conformance Scoring Algorithm

```python
# Scoring criteria (100 points total)
Pattern Coverage:    40 points
ADR Alignment:       20 points
New Patterns Check:  20 points
Risk Assessment:     20 points

# Conformance Levels
EXCELLENT: score >= 90
GOOD:      score >= 70
FAIR:      score >= 50
POOR:      score < 50
```

### 3.2 PatternExtractionService

**File**: `backend/app/services/pattern_extraction_service.py`
**Lines**: 571

#### Agentic Grep Algorithm

```
1. Extract key concepts from task description
   └─ Remove stop words
   └─ Prioritize technical terms
   └─ Limit to top 10 concepts

2. Generate targeted grep patterns
   └─ Function definitions (def, async def)
   └─ Class definitions
   └─ Variable assignments
   └─ Import statements
   └─ Docstrings/comments

3. Find relevant files
   └─ Match file patterns (*.py, *.ts, *.tsx)
   └─ Exclude node_modules, __pycache__, .git, etc.
   └─ Limit to 500 files

4. Execute searches
   └─ Compile regex patterns
   └─ Search each file
   └─ Collect matches (line_number, content)

5. Extract patterns from results
   └─ Categorize by pattern type
   └─ Calculate confidence scores
   └─ Sort by relevance
   └─ Return top 50 patterns
```

#### Pattern Categories

| Category | Detection Patterns |
|----------|-------------------|
| `CODE_STYLE` | Function/class definitions, naming conventions |
| `ERROR_HANDLING` | try/except blocks, raise statements |
| `API_DESIGN` | FastAPI/Flask routes, CRUD methods |
| `TESTING` | Test functions, pytest decorators, assertions |
| `DATABASE` | SQLAlchemy queries, ORM operations |
| `SECURITY` | Auth operations, crypto functions |

### 3.3 ADRScannerService

**File**: `backend/app/services/adr_scanner_service.py`

#### Responsibilities

- Scan ADR directory for markdown files
- Parse ADR structure (Status, Context, Decision, Consequences)
- Extract patterns and conventions from ADRs
- Match ADRs to task keywords

### 3.4 TestPatternService

**File**: `backend/app/services/test_pattern_service.py`

#### Responsibilities

- Find test files in project
- Extract test patterns (fixtures, mocks, assertions)
- Detect coverage conventions
- Identify test structure patterns

---

## 4. Pydantic Schemas

**File**: `backend/app/schemas/planning_subagent.py`
**Lines**: 655

### 4.1 Request/Response Schemas

```python
# Input
class PlanningRequest(BaseModel):
    task: str                          # Task description
    project_path: str = "."            # Project root path
    depth: int = 3                     # Search depth (1-5)
    include_tests: bool = True         # Include test patterns
    include_adrs: bool = True          # Include ADR analysis
    auto_approve: bool = False         # Auto-approve (skip review)

# Output
class PlanningResult(BaseModel):
    id: UUID                           # Session ID
    task: str                          # Original task
    status: PlanningStatus             # Current status
    patterns: PatternSummary           # Extracted patterns
    plan: ImplementationPlan           # Generated plan
    conformance: ConformanceResult     # Conformance score
    execution_time_ms: int             # Total execution time
    requires_approval: bool            # Needs human approval
```

### 4.2 Pattern Schemas

```python
class PatternCategory(str, Enum):
    ARCHITECTURE = "architecture"
    CODE_STYLE = "code_style"
    ERROR_HANDLING = "error_handling"
    TESTING = "testing"
    SECURITY = "security"
    API_DESIGN = "api_design"
    DATABASE = "database"

class ExtractedPattern(BaseModel):
    id: str                            # Pattern ID (pat_xxx)
    category: PatternCategory          # Pattern type
    name: str                          # Pattern name
    description: str                   # Human-readable description
    source_file: str                   # Where pattern was found
    source_line: int                   # Line number
    code_snippet: str                  # Example code
    confidence: float                  # Relevance score (0-1)
    occurrences: int                   # Times found in codebase
```

### 4.3 Plan Schemas

```python
class ImplementationStep(BaseModel):
    order: int                         # Step order
    title: str                         # Step title
    description: str                   # Detailed description
    files_to_create: list[str]         # New files needed
    files_to_modify: list[str]         # Existing files to change
    patterns_to_follow: list[str]      # Patterns to apply
    estimated_loc: int                 # Lines of code estimate
    estimated_hours: float             # Time estimate
    dependencies: list[int]            # Dependent step orders
    tests_required: list[str]          # Tests to write

class ImplementationPlan(BaseModel):
    id: UUID                           # Plan ID
    task: str                          # Original task
    summary: str                       # Plan summary
    steps: list[ImplementationStep]    # Implementation steps
    total_estimated_loc: int           # Total LOC
    total_estimated_hours: float       # Total hours
    files_to_create: list[str]         # All new files
    files_to_modify: list[str]         # All files to modify
    patterns_applied: list[str]        # Patterns being used
    adrs_referenced: list[str]         # Related ADRs
    new_patterns_introduced: list[str] # New patterns (may need ADR)
    risks: list[str]                   # Identified risks
```

### 4.4 Conformance Schemas

```python
class ConformanceLevel(str, Enum):
    EXCELLENT = "excellent"  # >= 90
    GOOD = "good"            # >= 70
    FAIR = "fair"            # >= 50
    POOR = "poor"            # < 50

class ConformanceResult(BaseModel):
    score: int                              # 0-100 score
    level: ConformanceLevel                 # Grade
    deviations: list[ConformanceDeviation]  # Pattern violations
    recommendations: list[str]              # Improvement suggestions
    requires_adr: bool                      # Needs new ADR
    new_patterns_detected: list[str]        # New patterns found
```

---

## 5. Performance Targets

| Metric | Target | Implementation |
|--------|--------|----------------|
| Pattern extraction (p95) | <30s | Parallel file search, compiled regex |
| Plan generation (p95) | <10s | Cached patterns, efficient synthesis |
| Total planning (p95) | <60s | Async sub-agents, early termination |
| File search | <15s | Limited to 500 files, exclusion filters |
| Concept extraction | <2s | In-memory tokenization, stop words filter |

---

## 6. Files Created/Modified

### New Files (Sprint 98)

| File | Lines | Purpose |
|------|-------|---------|
| `backend/app/services/planning_orchestrator_service.py` | 829 | Main orchestrator |
| `backend/app/services/pattern_extraction_service.py` | 571 | Agentic grep |
| `backend/app/services/adr_scanner_service.py` | ~300 | ADR scanning |
| `backend/app/services/test_pattern_service.py` | ~250 | Test pattern discovery |
| `backend/app/schemas/planning_subagent.py` | 655 | Pydantic models |

### Modified Files

| File | Changes |
|------|---------|
| `backend/app/__init__.py` | Export new services |
| `backend/app/services/__init__.py` | Export new services |

---

## 7. Testing Strategy

### 7.1 Unit Tests

```python
# test_planning_orchestrator_service.py
- test_plan_creates_session
- test_plan_extracts_patterns
- test_plan_generates_steps
- test_plan_calculates_conformance
- test_approve_plan_updates_status
- test_reject_plan_stores_reason

# test_pattern_extraction_service.py
- test_extract_concepts_filters_stop_words
- test_generate_grep_patterns_depth
- test_find_relevant_files_excludes_pycache
- test_execute_searches_matches_patterns
- test_extract_patterns_categorizes_correctly

# test_adr_scanner_service.py
- test_find_related_adrs
- test_extract_adr_conventions

# test_test_pattern_service.py
- test_find_test_patterns
- test_detect_coverage_conventions
```

### 7.2 Integration Tests

```python
# test_plan_command.py (CLI integration)
- test_plan_command_help
- test_plan_command_with_task
- test_plan_command_outputs_patterns
- test_plan_command_json_output
- test_plan_command_markdown_output
```

---

## 8. Dependencies

### Internal Dependencies

- `app.schemas.planning_subagent` - Pydantic models
- `app.services.ai_service` - AI provider (future enhancement)

### External Dependencies

- `asyncio` - Parallel sub-agent execution
- `pathlib` - File system operations
- `re` - Regex pattern matching
- `fnmatch` - File pattern matching
- `uuid` - Session ID generation

---

## 9. Security Considerations

1. **Path Traversal Prevention**: Validate project_path is within allowed directories
2. **File Access Control**: Only read files, never write during exploration
3. **Resource Limits**: Max 500 files, 50 patterns to prevent DoS
4. **Sensitive Data**: Exclude .env, credentials.json from search

---

## 10. Sprint 98 Deliverables Status

| Deliverable | Status | Notes |
|-------------|--------|-------|
| PlanningOrchestratorService | ✅ COMPLETE | 829 lines, full implementation |
| PatternExtractionService | ✅ COMPLETE | 571 lines, agentic grep |
| ADRScannerService | ✅ COMPLETE | ADR pattern extraction |
| TestPatternService | ✅ COMPLETE | Test pattern discovery |
| Planning Schemas | ✅ COMPLETE | 655 lines, all Pydantic models |
| Unit Tests | ✅ COMPLETE | See test_planning_orchestrator_service.py |
| Integration Tests | ✅ COMPLETE | See test_plan_command.py |

---

## 11. Next Sprint (Sprint 99)

Sprint 99 will build on Sprint 98 foundation:

1. **ConformanceCheckService** - Compare PR diffs against patterns
2. **Planning Subagent API Routes** - REST API endpoints
3. **Plan Approval UI** - React components for review
4. **GitHub Check Integration** - CI/CD gate
5. **E2E Tests** - Full workflow testing

---

## Appendix A: Code Examples

### Example: Planning Request

```python
from app.services.planning_orchestrator_service import PlanningOrchestratorService
from app.schemas.planning_subagent import PlanningRequest

orchestrator = PlanningOrchestratorService()

request = PlanningRequest(
    task="Add OAuth2 authentication with Google provider",
    project_path="/path/to/project",
    depth=3,
    include_tests=True,
    include_adrs=True,
    auto_approve=False,
)

result = await orchestrator.plan(request)
print(f"Patterns found: {result.patterns.total_patterns_found}")
print(f"Conformance: {result.conformance.score}% ({result.conformance.level})")
print(f"Steps: {len(result.plan.steps)}")
```

### Example: Pattern Extraction Output

```json
{
  "patterns": [
    {
      "id": "pat_a1b2c3d4",
      "category": "code_style",
      "name": "AuthService",
      "description": "Pattern found 5 times in codebase",
      "source_file": "backend/app/services/auth_service.py",
      "source_line": 15,
      "code_snippet": "class AuthService:",
      "confidence": 0.85,
      "occurrences": 5
    }
  ],
  "total_files_scanned": 127,
  "total_patterns_found": 23
}
```

---

**Document Version**: 1.0.0
**Last Updated**: January 23, 2026
**Author**: Backend Team
**Reviewer**: CTO
