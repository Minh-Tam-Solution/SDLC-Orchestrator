# Sprint 97-100: Expert Workflow Enhancements

**Planning Date:** January 22, 2026  
**CTO Approval:** ✅ Approved (Jan 22, 2026)  
**Framework:** SDLC 5.1.3 (7-Pillar Architecture)  
**Source:** Expert AI Coding Workflow Analysis (2026)  
**Status:** 📋 PLANNED (Post Go/No-Go)

---

## Executive Summary

Based on comprehensive analysis of expert AI coding workflow (Jan 22, 2026), identified key enhancements to improve SDLC Orchestrator's agentic capabilities. Current alignment: **92%** with expert workflow. These 4 sprints close the remaining **8% gap** to achieve 100% alignment.

### Alignment Status

| Metric | Before | After Sprint 100 |
|--------|--------|------------------|
| Expert Workflow Alignment | 92% | 100% |
| Planning Sub-agent Support | ❌ | ✅ |
| Feedback Loop Closure | ❌ | ✅ |
| Agentic Grep (vs RAG) | ❌ | ✅ |
| Conformance Check | ❌ | ✅ |

### Enhancement Priority (CTO Approved)

| Enhancement | Priority | Sprint | Status |
|-------------|----------|--------|--------|
| **EP-10:** Planning Sub-agent Orchestration | P1 | 97-99 | 📋 APPROVED |
| **EP-11:** Feedback Loop Closure | P1 | 100 | 📋 APPROVED |
| EP-09: Spec Generation from Recording | P2 | Q3 2026 | ⏸️ DEFERRED |
| EP-12: Intelligent Model Routing | P3 | Q4 2026 | ⏸️ DEFERRED |

---

## Background: Expert AI Coding Workflow (2026)

### Key Insights from Expert

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                    EXPERT AI CODING WORKFLOW (2026)                         │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  PHASE 1: SPECIFICATION GENERATION                                          │
│  - Screen recording of similar app → Gemini 3 Pro → PRD draft              │
│  - Claude Code "interview mode" (ask_user_question) for refinement          │
│  - ChatGPT + web search for library discovery                               │
│                                                                              │
│  PHASE 2: PLANNING MODE (CRITICAL for >15 LOC changes)                      │
│  - Spawn explore sub-agents → extract patterns → build on them             │
│  - Key insight: "Agentic grep > RAG for context retrieval"                 │
│  - PREVENTS ARCHITECTURAL DRIFT                                             │
│                                                                              │
│  PHASE 3: IMPLEMENTATION                                                     │
│  - Model Selection Matrix (task-type aware)                                 │
│  - Opus 4.5 (70%): Large features, multi-file refactor                     │
│  - Sonnet 4.5: Small fixes, UI tweaks, code review                         │
│  - GPT 5.2: Architecture decisions, debugging (when stuck)                  │
│  - Gemini 3 Pro: Design, creativity, large context                         │
│  - Haiku 4.5: Quick answers, explanations, micro-edits                     │
│                                                                              │
│  PHASE 4: REVIEW & LEARNING                                                  │
│  - Review by "diff shape" not line-by-line                                 │
│  - Update claude.md with learnings                                          │
│  - Fork session for learning without polluting main context                 │
│                                                                              │
│  KEY INSIGHT: Developer role = Design feedback loops, NOT write code        │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### What SDLC Orchestrator Already Has (92% Aligned)

| Expert Practice | SDLC Implementation | Evidence |
|-----------------|---------------------|----------|
| Multi-Provider Fallback | Ollama → Claude → GPT-4o (10 models!) | ADR-007, Model Strategy v3.0 |
| Dynamic Context Engine | Gate-aware context overlay (TRUE MOAT) | Sprint 81, useContextOverlay.ts |
| AGENTS.md Generator | `sdlcctl agents init` CLI | agents.py (931 lines) |
| AGENTS.md Validator | `sdlcctl agents validate` CLI | agents.py |
| Planning Hierarchy | Roadmap → Phase → Sprint → Backlog | ADR-013, Sprint 74-77 |
| Task Decomposition | AI Task Decomposition Service | ADR-012 |
| Evidence Collection | Evidence Vault with SHA256 | minio_service.py |
| SE4H/SE4A Framework | Agent Coach / Agent Executor | SDLC-Agentic-Core-Principles.md |

### What's Missing (8% Gap)

| Expert Practice | Gap | Priority |
|-----------------|-----|----------|
| Pre-planning sub-agent exploration | No pattern extraction before implementation | P1 - HIGH |
| Agentic grep (vs RAG) | No AI-powered codebase search | P1 - HIGH |
| Feedback loop closure | No learning from PR comments → spec | P1 - HIGH |
| Conformance check | No drift prevention gate | P2 - MEDIUM |

---

## Sprint 97: ADR-034 + Planning Architecture (Mar 1-7, 2026)

**Duration:** 5 days  
**Priority:** P1 - Expert Workflow Core  
**Story Points:** 21 SP  
**Prerequisite:** Framework-First compliance (ADR-034 in SDLC-Enterprise-Framework)

### 97.1 Objectives

Create framework documentation and design architecture for Planning Sub-agent Orchestration. This sprint focuses on **design and documentation** before implementation.

### 97.2 Features

| Feature | Priority | SP | Owner | Status |
|---------|----------|----|----|--------|
| ADR-034: Planning Sub-agent Orchestration | P1 | 5 | CTO | 📋 |
| `sdlcctl plan` Command Design | P1 | 8 | Backend Lead | 📋 |
| AI Council Service Refactor Evaluation | P1 | 5 | Backend Lead | 📋 |
| CLAUDE.md Update (AI Best Practices 2026) | P1 | 3 | PM | 📋 |

### 97.3 Deliverables

#### ADR-034: Planning Sub-agent Orchestration

**Location:** `SDLC-Enterprise-Framework/02-Core-Methodology/03-ADRs/ADR-034-Planning-Subagent-Orchestration.md`

```markdown
# ADR-034: Planning Sub-agent Orchestration

## Status
APPROVED (January 22, 2026)

## Context
Expert AI workflow analysis (Jan 2026) identified that pre-planning
pattern extraction via sub-agents prevents architectural drift.

Key insight from expert: "Agentic grep > RAG for context retrieval"

Current SDLC Orchestrator has:
- ✅ AI Task Decomposition Service (ADR-012)
- ✅ Multi-Provider AI (ADR-007)
- ❌ Pre-planning pattern extraction
- ❌ Conformance check gate

## Decision
1. Add `sdlcctl plan <task>` command
2. Spawn explore sub-agents (3-5 parallel) for:
   - Similar implementations in codebase (agentic grep)
   - Related ADRs and patterns
   - Existing test patterns
3. Synthesize findings into implementation plan
4. Human approval gate before execution
5. Optional: GitHub Check for conformance

## Consequences

### Positive
- Prevents architectural drift (>15 LOC changes)
- Builds on established patterns
- Maintains codebase consistency
- Closes 8% gap with expert workflow

### Negative
- Additional step before implementation
- Requires sub-agent infrastructure
- May slow down small changes (mitigation: skip for <15 LOC)

## Implementation
- Sprint 97: Architecture + ADR
- Sprint 98: Core implementation
- Sprint 99: UI + GitHub integration
```

#### CLAUDE.md Update

**Section to add:** AI Agent Best Practices (2026)

```yaml
## AI Agent Best Practices (2026)

### Planning Mode (CRITICAL for >15 LOC changes)
- ALWAYS use planning mode for changes >15 LOC
- Planning spawns explore sub-agents → extract patterns
- Agentic grep > RAG for context retrieval
- Human approves plan before execution

### Model Selection Matrix
| Task Type | Primary | Fallback | Reasoning |
|-----------|---------|----------|-----------|
| Large Feature (>50 LOC) | Opus 4.5 | GPT 5.2 | Best at multi-file refactor |
| Small Fix (<15 LOC) | Sonnet 4.5 | Haiku 4.5 | Fast, accurate for tweaks |
| Architecture Decision | GPT 5.2 | Claude Opus | Strong reasoning, debugging |
| UI/Design | Gemini 3 Pro | Claude Opus | Creative, visual context |
| Quick Explanation | Haiku 4.5 | Sonnet 4.5 | Fastest response |
| Stuck/Debugging | GPT 5.2 | Switch model | "Switch model when stuck" |

### Sub-agents Usage
- ✅ Use for: Research, thinking, pattern exploration (isolated context)
- ❌ Avoid: Parallel editing in same project (coordination issues)
- Fork sessions to learn without polluting main session

### Developer Role Evolution
- Design feedback loops, NOT write code
- Monitor agent, identify patterns, update context files
- Make high-level architecture decisions AI can't
- Update tools/skills/MCP servers configuration
```

#### `sdlcctl plan` Command Architecture

**File:** `backend/sdlcctl/commands/plan.py`

```python
"""
Planning mode with sub-agent orchestration.

Usage:
    sdlcctl plan "Add user authentication with OAuth2"
    sdlcctl plan "Refactor payment service" --depth 5
    sdlcctl plan --check --diff <diff_url>  # CI/CD mode
"""

import typer
from pathlib import Path
from typing import Optional

app = typer.Typer(help="Planning mode with sub-agent orchestration")

@app.command()
def plan(
    task: str = typer.Argument(..., help="Task description"),
    project_path: Path = typer.Option(".", "--path", "-p", help="Project root"),
    depth: int = typer.Option(3, "--depth", "-d", help="Search depth for patterns"),
    auto_approve: bool = typer.Option(False, "--auto", "-a", help="Skip approval gate"),
    output: str = typer.Option("terminal", "--output", "-o", help="Output format: terminal, json, markdown"),
):
    """
    Execute planning mode with sub-agent orchestration.
    
    Steps:
    1. Spawn explore sub-agents (parallel)
    2. Extract patterns from codebase (agentic grep)
    3. Extract patterns from ADRs
    4. Identify test patterns
    5. Synthesize implementation plan
    6. Human approval gate (unless --auto)
    
    Example:
        sdlcctl plan "Add user authentication with OAuth2"
        sdlcctl plan "Refactor payment service" --depth 5
    """
    pass  # Implementation in Sprint 98

@app.command()
def check(
    diff_url: str = typer.Argument(..., help="GitHub PR diff URL"),
    project_path: Path = typer.Option(".", "--path", "-p", help="Project root"),
    fail_threshold: int = typer.Option(70, "--threshold", "-t", help="Conformance score threshold"),
):
    """
    Check PR conformance against established patterns.
    For CI/CD integration (GitHub Actions).
    
    Example:
        sdlcctl plan check https://github.com/org/repo/pull/123.diff
    """
    pass  # Implementation in Sprint 99
```

### 97.4 Success Criteria

- [ ] ADR-034 created in SDLC-Enterprise-Framework
- [ ] ADR-034 CTO approved
- [ ] CLAUDE.md updated with AI Best Practices 2026
- [ ] `sdlcctl plan` command architecture documented
- [ ] AI Council refactor decision made (refactor vs new service)
- [ ] Sprint 98-99 backlog refined

---

## Sprint 98: Planning Sub-agent Implementation Part 1 (Mar 8-14, 2026)

**Duration:** 5 days  
**Priority:** P1 - Expert Workflow Core  
**Story Points:** 26 SP  
**Depends On:** Sprint 97 (ADR-034)

### 98.1 Objectives

Implement core planning sub-agent service with pattern extraction using agentic grep approach.

### 98.2 Features

| Feature | Priority | SP | Owner | Status |
|---------|----------|----|----|--------|
| PlanningOrchestratorService | P1 | 8 | Backend | 📋 |
| Pattern Extraction (Agentic Grep) | P1 | 8 | Backend | 📋 |
| ADR Pattern Scanner | P1 | 5 | Backend | 📋 |
| Test Pattern Scanner | P1 | 5 | Backend | 📋 |

### 98.3 Files to Create

```
backend/app/services/planning_orchestrator_service.py    # Main orchestrator
backend/app/services/pattern_extraction_service.py       # Agentic grep
backend/app/services/adr_scanner_service.py              # ADR pattern extraction
backend/app/services/test_pattern_service.py             # Test pattern extraction
backend/app/schemas/planning.py                          # Pydantic schemas
backend/sdlcctl/commands/plan.py                         # CLI implementation
tests/unit/services/test_planning_orchestrator.py        # Unit tests
tests/integration/test_plan_command.py                   # Integration tests
```

### 98.4 Core Implementation

#### PlanningOrchestratorService

```python
# backend/app/services/planning_orchestrator_service.py

from typing import List
from pathlib import Path
import asyncio

from app.services.pattern_extraction_service import PatternExtractionService
from app.services.adr_scanner_service import ADRScannerService
from app.services.test_pattern_service import TestPatternService
from app.schemas.planning import (
    PlanningResult, ExploreResult, PatternSummary, ImplementationPlan
)

class PlanningOrchestratorService:
    """
    Orchestrates planning sub-agents for pre-implementation analysis.
    
    Key insight from expert: "Agentic grep > RAG for context retrieval"
    
    This service:
    1. Spawns explore sub-agents (parallel)
    2. Extracts patterns from codebase, ADRs, tests
    3. Synthesizes implementation plan
    4. Returns for human approval
    """
    
    def __init__(
        self,
        pattern_service: PatternExtractionService,
        adr_service: ADRScannerService,
        test_service: TestPatternService,
    ):
        self.pattern_service = pattern_service
        self.adr_service = adr_service
        self.test_service = test_service
    
    async def plan(
        self, 
        task: str, 
        project_path: Path,
        depth: int = 3,
    ) -> PlanningResult:
        """
        Execute planning mode with sub-agent orchestration.
        
        Args:
            task: Task description (e.g., "Add OAuth2 authentication")
            project_path: Path to project root
            depth: Search depth for pattern extraction
            
        Returns:
            PlanningResult with patterns, plan, and conformance score
        """
        # Step 1: Spawn explore sub-agents (parallel)
        explore_results = await self._spawn_explore_agents(task, project_path, depth)
        
        # Step 2: Extract and synthesize patterns
        patterns = await self._extract_patterns(explore_results)
        
        # Step 3: Generate implementation plan
        plan = await self._generate_plan(task, patterns)
        
        # Step 4: Calculate conformance score
        conformance_score = self._calculate_conformance(plan, patterns)
        
        return PlanningResult(
            task=task,
            patterns=patterns,
            plan=plan,
            conformance_score=conformance_score,
            requires_approval=True,
        )
    
    async def _spawn_explore_agents(
        self, 
        task: str, 
        project_path: Path,
        depth: int,
    ) -> List[ExploreResult]:
        """
        Spawn 3-5 explore sub-agents with isolated contexts.
        Each agent searches for different aspects.
        """
        agents = [
            self.pattern_service.search_similar_implementations(task, project_path, depth),
            self.adr_service.find_related_adrs(task, project_path),
            self.test_service.find_test_patterns(task, project_path),
        ]
        
        # Run in parallel (key efficiency gain)
        results = await asyncio.gather(*agents, return_exceptions=True)
        
        return [r for r in results if not isinstance(r, Exception)]
    
    async def _extract_patterns(
        self, 
        results: List[ExploreResult],
    ) -> PatternSummary:
        """
        Synthesize exploration results into pattern summary.
        """
        # Combine patterns from all explore agents
        # Deduplicate and rank by relevance
        pass
    
    async def _generate_plan(
        self, 
        task: str,
        patterns: PatternSummary,
    ) -> ImplementationPlan:
        """
        Generate implementation plan building on existing patterns.
        Uses AI to synthesize plan that follows established conventions.
        """
        pass
    
    def _calculate_conformance(
        self, 
        plan: ImplementationPlan,
        patterns: PatternSummary,
    ) -> int:
        """
        Calculate conformance score (0-100).
        Higher score = better alignment with existing patterns.
        """
        pass
```

#### Pattern Extraction Service (Agentic Grep)

```python
# backend/app/services/pattern_extraction_service.py

class PatternExtractionService:
    """
    Pattern extraction using agentic grep approach.
    
    Key insight: "Agentic grep > RAG for context retrieval"
    
    Instead of RAG (embedding similarity), we:
    1. Use AI to understand the task semantically
    2. Generate targeted grep patterns
    3. Search codebase with multiple patterns
    4. Filter and rank results by relevance
    """
    
    async def search_similar_implementations(
        self,
        task: str,
        project_path: Path,
        depth: int = 3,
    ) -> ExploreResult:
        """
        Search for similar implementations in codebase.
        
        Steps:
        1. AI extracts key concepts from task
        2. Generate grep patterns for each concept
        3. Execute grep searches (parallel)
        4. Filter results by relevance
        5. Extract patterns from top results
        """
        # Step 1: Extract key concepts
        concepts = await self._extract_concepts(task)
        
        # Step 2: Generate grep patterns
        grep_patterns = await self._generate_grep_patterns(concepts)
        
        # Step 3: Execute searches
        search_results = await self._execute_searches(grep_patterns, project_path)
        
        # Step 4: Filter and rank
        relevant_files = self._filter_results(search_results, task)
        
        # Step 5: Extract patterns
        patterns = await self._extract_patterns_from_files(relevant_files)
        
        return ExploreResult(
            agent_type="similar_implementations",
            patterns=patterns,
            files_searched=len(search_results),
            files_relevant=len(relevant_files),
        )
```

### 98.5 Success Criteria

- [ ] PlanningOrchestratorService implemented
- [ ] Pattern extraction working (agentic grep)
- [ ] ADR scanner finding relevant patterns
- [ ] Test pattern scanner working
- [ ] Unit tests: 80% coverage
- [ ] Integration test: `sdlcctl plan` basic flow
- [ ] Performance: <30s for typical task

---

## Sprint 99: Planning Sub-agent Implementation Part 2 (Mar 15-21, 2026)

**Duration:** 5 days  
**Priority:** P1 - Expert Workflow Core  
**Story Points:** 24 SP  
**Depends On:** Sprint 98

### 99.1 Objectives

Complete planning sub-agent with conformance checking, approval UI, and GitHub integration.

### 99.2 Features

| Feature | Priority | SP | Owner | Status |
|---------|----------|----|----|--------|
| ConformanceCheckService | P1 | 8 | Backend | 📋 |
| Plan Approval UI | P1 | 8 | Frontend | 📋 |
| GitHub Check Integration | P2 | 5 | DevOps | 📋 |
| E2E Tests | P1 | 3 | QA | 📋 |

### 99.3 Files to Create

```
backend/app/services/conformance_check_service.py        # Conformance check
backend/app/api/routes/planning.py                       # API endpoints
frontend/src/app/app/planning/plan-review/page.tsx       # Plan approval UI
frontend/src/hooks/usePlanningReview.ts                  # React hooks
.github/workflows/pattern-conformance.yml                # GitHub Action
tests/e2e/planning-subagent.spec.ts                      # E2E tests
```

### 99.4 Core Implementation

#### ConformanceCheckService

```python
# backend/app/services/conformance_check_service.py

class ConformanceCheckService:
    """
    Compare proposed changes against established patterns.
    Prevents architectural drift.
    """
    
    async def check(
        self, 
        proposed_diff: str, 
        patterns: PatternSummary,
    ) -> ConformanceResult:
        """
        Check conformance of proposed changes.
        
        Returns:
            - conformance_score: 0-100 (higher = better alignment)
            - deviations: list of pattern violations
            - recommendations: list of suggested changes
            - requires_adr: bool (if new pattern introduced)
        """
        pass
    
    async def check_pr(
        self,
        pr_diff_url: str,
        project_path: Path,
    ) -> ConformanceResult:
        """
        Check PR conformance for CI/CD integration.
        Used by GitHub Action.
        """
        pass
```

#### Plan Approval UI

```typescript
// frontend/src/app/app/planning/plan-review/page.tsx

export default function PlanReviewPage() {
  // Features:
  // - Display extracted patterns (grouped by type)
  // - Show implementation plan (steps, files, estimates)
  // - Conformance score visualization (gauge chart)
  // - Pattern deviation warnings
  // - Approve/Reject/Request Changes buttons
  // - ADR creation trigger (if new pattern)
  // - Comments/notes for approver
}
```

#### GitHub Check Integration

```yaml
# .github/workflows/pattern-conformance.yml

name: Pattern Conformance Check
on: [pull_request]

jobs:
  conformance:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install sdlcctl
        run: pip install sdlcctl
      
      - name: Run Conformance Check
        id: conformance
        run: |
          result=$(sdlcctl plan check ${{ github.event.pull_request.diff_url }} --output json)
          echo "score=$(echo $result | jq -r '.conformance_score')" >> $GITHUB_OUTPUT
          echo "deviations=$(echo $result | jq -r '.deviations | length')" >> $GITHUB_OUTPUT
      
      - name: Post Results
        uses: actions/github-script@v7
        with:
          script: |
            const score = ${{ steps.conformance.outputs.score }};
            const deviations = ${{ steps.conformance.outputs.deviations }};
            
            const emoji = score >= 80 ? '✅' : score >= 60 ? '⚠️' : '❌';
            const body = `## Pattern Conformance Check ${emoji}
            
            **Score:** ${score}/100
            **Deviations:** ${deviations}
            
            ${score < 70 ? '⚠️ Consider reviewing patterns before merging.' : ''}`;
            
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: body
            });
```

### 99.5 Success Criteria

- [ ] ConformanceCheckService working
- [ ] Plan approval UI functional
- [ ] GitHub Check integration (optional but recommended)
- [ ] E2E tests: 5 scenarios
  - [ ] Plan generation flow
  - [ ] Pattern extraction accuracy
  - [ ] Conformance scoring
  - [ ] Approval workflow
  - [ ] GitHub Check integration
- [ ] Documentation complete
- [ ] `sdlcctl plan` command fully functional

---

## Sprint 100: Feedback Loop Closure - EP-11 (Mar 22-28, 2026)

**Duration:** 5 days  
**Priority:** P1 - Expert Workflow Core  
**Story Points:** 21 SP  
**Depends On:** None (independent of EP-10)

### 100.1 Objectives

Close the feedback loop from PR review comments → specification refinement. Learn from code review to improve future decompositions.

### 100.2 Features

| Feature | Priority | SP | Owner | Status |
|---------|----------|----|----|--------|
| `pr_learnings` Table Migration | P1 | 3 | Backend | 📋 |
| FeedbackLearningService | P1 | 8 | Backend | 📋 |
| PR Comment Analyzer | P1 | 5 | Backend | 📋 |
| Monthly Aggregation Job | P2 | 3 | Backend | 📋 |
| CLAUDE.md Auto-Update (Quarterly) | P2 | 2 | Backend | 📋 |

### 100.3 Files to Create

```
backend/alembic/versions/xxx_add_pr_learnings.py         # Migration
backend/app/models/pr_learning.py                        # SQLAlchemy model
backend/app/services/feedback_learning_service.py        # Core service
backend/app/services/pr_comment_analyzer_service.py      # Comment analysis
backend/app/jobs/monthly_learning_aggregation.py         # Scheduled job
backend/app/jobs/quarterly_claudemd_update.py            # Scheduled job
tests/unit/services/test_feedback_learning.py            # Unit tests
```

### 100.4 Core Implementation

#### Database Migration

```python
# backend/alembic/versions/xxx_add_pr_learnings.py

def upgrade():
    op.create_table(
        'pr_learnings',
        sa.Column('id', UUID, primary_key=True, default=uuid.uuid4),
        sa.Column('project_id', UUID, sa.ForeignKey('projects.id'), nullable=False),
        sa.Column('pr_id', sa.String(100), nullable=False),
        sa.Column('pr_url', sa.String(500), nullable=False),
        sa.Column('pr_title', sa.String(500)),
        sa.Column('feedback_type', sa.Enum(
            'pattern_violation',
            'missing_requirement', 
            'edge_case',
            'performance',
            'security',
            'naming_convention',
            'documentation',
            'test_coverage',
            name='feedback_type_enum'
        ), nullable=False),
        sa.Column('original_spec_section', sa.Text),
        sa.Column('reviewer_comment', sa.Text, nullable=False),
        sa.Column('corrected_approach', sa.Text),
        sa.Column('pattern_extracted', sa.Text),
        sa.Column('applied_to_decomposition', sa.Boolean, default=False),
        sa.Column('applied_to_claudemd', sa.Boolean, default=False),
        sa.Column('severity', sa.Enum('low', 'medium', 'high', 'critical', name='severity_enum')),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, onupdate=sa.func.now()),
    )
    
    op.create_index('ix_pr_learnings_project_id', 'pr_learnings', ['project_id'])
    op.create_index('ix_pr_learnings_feedback_type', 'pr_learnings', ['feedback_type'])
    op.create_index('ix_pr_learnings_created_at', 'pr_learnings', ['created_at'])


def downgrade():
    op.drop_table('pr_learnings')
```

#### FeedbackLearningService

```python
# backend/app/services/feedback_learning_service.py

class FeedbackLearningService:
    """
    Extracts learnings from PR reviews to improve future decompositions.
    
    Closes the feedback loop:
    PR Review → Extract Learnings → Update Decomposition Hints → Better Specs
    
    Expert insight: "Design feedback loops, NOT write code"
    """
    
    async def extract_learnings_from_pr(
        self, 
        pr_id: str,
        repo_url: str,
    ) -> List[PRLearning]:
        """
        Analyze PR review comments for learnings.
        
        Extracts:
        - Pattern violations (architecture drift)
        - Missing requirements (scope gaps)
        - Edge cases discovered (better test coverage)
        - Performance issues (optimization opportunities)
        - Security concerns (vulnerability patterns)
        - Naming convention issues (consistency)
        - Documentation gaps
        - Test coverage issues
        """
        # 1. Fetch PR review comments
        comments = await self._fetch_pr_comments(pr_id, repo_url)
        
        # 2. Classify each comment
        classified = await self._classify_comments(comments)
        
        # 3. Extract patterns from significant comments
        learnings = await self._extract_patterns(classified)
        
        # 4. Store learnings
        await self._store_learnings(learnings)
        
        return learnings
    
    async def update_decomposition_hints(
        self, 
        project_id: str,
    ) -> DecompositionHintUpdate:
        """
        Monthly job: Aggregate learnings → Improve decomposition templates.
        
        Analyzes patterns in learnings to:
        - Add new decomposition hints
        - Update existing patterns
        - Remove outdated guidance
        """
        # 1. Get learnings from last 30 days
        learnings = await self._get_recent_learnings(project_id, days=30)
        
        # 2. Aggregate by feedback type
        aggregated = self._aggregate_learnings(learnings)
        
        # 3. Generate decomposition hints
        hints = await self._generate_hints(aggregated)
        
        # 4. Update decomposition service
        await self._update_decomposition_service(hints)
        
        return DecompositionHintUpdate(
            hints_added=len(hints.new),
            hints_updated=len(hints.updated),
            hints_removed=len(hints.removed),
        )
    
    async def generate_claude_md_update(
        self, 
        learnings: List[PRLearning],
    ) -> str:
        """
        Quarterly: Synthesize learnings into CLAUDE.md sections.
        Returns suggested additions for human review.
        
        Does NOT auto-update CLAUDE.md - human approval required.
        """
        # 1. Group learnings by category
        grouped = self._group_by_category(learnings)
        
        # 2. Identify patterns (recurring issues)
        patterns = self._identify_recurring_patterns(grouped)
        
        # 3. Generate CLAUDE.md sections
        sections = await self._generate_sections(patterns)
        
        # 4. Format as markdown
        return self._format_as_markdown(sections)
```

### 100.5 Success Criteria

- [ ] `pr_learnings` table created and migrated
- [ ] FeedbackLearningService implemented
- [ ] PR comment analysis working
- [ ] Monthly aggregation job scheduled (cron)
- [ ] Quarterly CLAUDE.md update suggestion working
- [ ] Unit tests: 80% coverage
- [ ] Integration test: Full feedback loop
- [ ] Documentation complete

---

## Summary

### Sprint Timeline

```
Sprint  Dates           Focus                           SP    Status
════════════════════════════════════════════════════════════════════════════════
97      Mar 1-7         ADR-034 + Plan Architecture     21    📋 PLANNED
98      Mar 8-14        Planning Sub-agents Part 1      26    📋 PLANNED
99      Mar 15-21       Planning Sub-agents Part 2      24    📋 PLANNED
100     Mar 22-28       Feedback Loop (EP-11)           21    📋 PLANNED
────────────────────────────────────────────────────────────────────────────────
Total:                  4 sprints (4 weeks)             92    📋 CTO APPROVED
```

### Total Story Points

| Sprint | SP | Cumulative |
|--------|-----|------------|
| 97 | 21 | 21 |
| 98 | 26 | 47 |
| 99 | 24 | 71 |
| 100 | 21 | 92 |

### Key Deliverables

| Enhancement | Deliverable | Sprint |
|-------------|-------------|--------|
| **EP-10** | ADR-034: Planning Sub-agent Orchestration | 97 |
| **EP-10** | `sdlcctl plan` command | 97-99 |
| **EP-10** | PlanningOrchestratorService | 98 |
| **EP-10** | Pattern Extraction (Agentic Grep) | 98 |
| **EP-10** | ConformanceCheckService | 99 |
| **EP-10** | Plan Approval UI | 99 |
| **EP-10** | GitHub Check Integration | 99 |
| **EP-11** | `pr_learnings` table | 100 |
| **EP-11** | FeedbackLearningService | 100 |
| **EP-11** | Monthly Aggregation Job | 100 |
| **EP-11** | CLAUDE.md Update Suggestions | 100 |

### Alignment Improvement

| Metric | Before | After |
|--------|--------|-------|
| Expert Workflow Alignment | 92% | 100% |
| Planning Sub-agent Support | ❌ | ✅ |
| Agentic Grep (vs RAG) | ❌ | ✅ |
| Conformance Check | ❌ | ✅ |
| Feedback Loop Closure | ❌ | ✅ |

---

## Deferred Enhancements (CTO Decision)

### EP-09: Spec Generation from Recording (Q3 2026)

**Reason for deferral:** Nice-to-have, not core workflow. Requires Gemini multimodal integration which adds complexity.

**Scope:**
- Screen recording → Gemini 3 Pro → PRD draft
- Claude Code "interview mode" for refinement
- ChatGPT + web search for library discovery

### EP-12: Intelligent Model Routing (Q4 2026)

**Reason for deferral:** Current Model Strategy v3.0 is sufficient. 10-model configuration already exceeds expert's 5 models.

**Scope:**
- Task-type aware model selection
- Automatic fallback on timeout/error
- Cost optimization by task type
- Performance tracking per model per task type

---

## Approval & Sign-off

### Document Approvals

- [x] **CTO**: Sprint scope, timeline, architecture (Jan 22, 2026)
- [ ] **CPO**: Feature prioritization alignment
- [ ] **Backend Lead**: Implementation approach
- [ ] **Frontend Lead**: UI implementation
- [ ] **QA Lead**: Testing strategy

---

**Document Version:** 1.0.0  
**Created:** January 22, 2026  
**Author:** PM + CTO  
**Next Review:** Sprint 97 Kickoff (Mar 1, 2026)
