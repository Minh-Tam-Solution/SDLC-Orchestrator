# Technical Specification: sdlcctl plan Command
## Planning Sub-agent Orchestration Architecture

**Version**: 1.0.0
**Date**: January 22, 2026
**Status**: DRAFT - Pending CTO Review
**Sprint**: Sprint 95-98
**Reference**: ADR-034-Planning-Subagent-Orchestration
**Author**: Backend Team

---

## 1. Overview

### 1.1 Purpose

The `sdlcctl plan` command implements **Planning Sub-agent Orchestration** (ADR-034) to prevent architectural drift by extracting patterns before code generation.

### 1.2 Problem Statement

When AI agents make changes exceeding 15 lines of code (LOC), architectural drift becomes a significant risk:
- Pattern inconsistency with existing codebase
- ADR violations
- Convention drift
- Test pattern mismatch

### 1.3 Solution

Implement a planning command that:
1. Spawns parallel sub-agents to extract patterns
2. Synthesizes patterns into implementation plan
3. Presents plan for human approval
4. Injects planning context into code generation

---

## 2. Command Interface

### 2.1 Basic Usage

```bash
# Basic plan command
sdlcctl plan "Add authentication middleware for API routes"

# With scope restriction
sdlcctl plan "Add logging to services" --scope backend/app/services

# With depth control
sdlcctl plan "Refactor user module" --depth thorough

# Output to file
sdlcctl plan "Add caching layer" --output plan.md

# Interactive mode (default)
sdlcctl plan "Add pagination to list endpoints" --interactive

# Non-interactive (CI/CD)
sdlcctl plan "Fix security vulnerability" --no-interactive --auto-approve
```

### 2.2 Command Options

```python
@app.command(name="plan")
def plan_command(
    task: str = typer.Argument(
        ...,
        help="Task description (what to implement)"
    ),
    scope: Optional[List[str]] = typer.Option(
        None,
        "--scope", "-s",
        help="Directories/files to consider (can specify multiple)"
    ),
    depth: str = typer.Option(
        "medium",
        "--depth", "-d",
        help="Analysis depth: quick (10s) | medium (30s) | thorough (60s)"
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output", "-o",
        help="Output plan to file instead of console"
    ),
    interactive: bool = typer.Option(
        True,
        "--interactive/--no-interactive",
        help="Interactive approval mode"
    ),
    auto_approve: bool = typer.Option(
        False,
        "--auto-approve",
        help="Skip approval (for CI/CD)"
    ),
    project_id: Optional[str] = typer.Option(
        None,
        "--project", "-p",
        help="Project ID for API integration"
    ),
    format: str = typer.Option(
        "rich",
        "--format", "-f",
        help="Output format: rich | json | markdown"
    ),
) -> None:
    """
    Plan implementation before coding.

    Extracts patterns from codebase, reviews ADRs, and creates
    an implementation plan for human approval.

    Recommended for changes >15 LOC to prevent architectural drift.

    Examples:
        sdlcctl plan "Add user authentication"
        sdlcctl plan "Refactor database layer" --depth thorough
        sdlcctl plan "Add caching" -s backend/app/services --output plan.md
    """
```

### 2.3 Output Format

```
═══════════════════════════════════════════════════════════════════════════════
                         SDLC PLANNING MODE
                    Task: Add authentication middleware
═══════════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────────┐
│ PHASE 1: Pattern Extraction                                          [✓]   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ Similar Implementations Found (3):                                          │
│ ┌─────────────────────────────────────────────────────────────────────────┐│
│ │ 1. backend/app/middleware/cors_middleware.py                    87%     ││
│ │    - BaseMiddleware pattern                                             ││
│ │    - Async __call__ method                                              ││
│ │    - Logger dependency injection                                        ││
│ │                                                                         ││
│ │ 2. backend/app/middleware/logging_middleware.py                 72%     ││
│ │    - Request/response logging pattern                                   ││
│ │    - Structured logging with context                                    ││
│ │                                                                         ││
│ │ 3. backend/app/middleware/rate_limit_middleware.py              65%     ││
│ │    - Rate limiting with Redis backend                                   ││
│ │    - Configurable limits per endpoint                                   ││
│ └─────────────────────────────────────────────────────────────────────────┘│
│                                                                             │
│ ADR Constraints (2):                                                        │
│ ┌─────────────────────────────────────────────────────────────────────────┐│
│ │ ADR-002: Authentication Model                                           ││
│ │   • JWT tokens with 15min expiry, refresh token rotation                ││
│ │   • OAuth 2.0 support (GitHub, Google, Microsoft)                       ││
│ │   • MFA support required for admin roles                                ││
│ │                                                                         ││
│ │ ADR-007: AI Context Engine                                              ││
│ │   • Multi-provider fallback (Ollama → Claude → GPT)                     ││
│ │   • Async operations required                                           ││
│ └─────────────────────────────────────────────────────────────────────────┘│
│                                                                             │
│ Code Patterns Extracted:                                                    │
│   • Middleware: BaseMiddleware class with async __call__                   │
│   • Naming: snake_case, max 50 chars                                        │
│   • Error handling: HTTPException with status codes                         │
│   • Logging: structlog with request context                                 │
│   • Dependencies: Inject via Depends()                                      │
│                                                                             │
│ Test Patterns Extracted:                                                    │
│   • Framework: pytest + pytest-asyncio                                      │
│   • Mocking: unittest.mock for external services                           │
│   • Coverage: 95%+ required                                                 │
│   • Naming: test_<function>_<scenario>                                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ PHASE 2: Implementation Plan                                         [✓]   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ Proposed Steps:                                                             │
│                                                                             │
│   1. Create AuthMiddleware class                                            │
│      File: backend/app/middleware/auth_middleware.py                        │
│      Pattern: Follow cors_middleware.py structure                           │
│      Estimated: ~80 LOC                                                     │
│                                                                             │
│   2. Implement JWT validation                                               │
│      Using: existing auth_service.verify_token()                            │
│      Constraint: ADR-002 (15min expiry)                                     │
│                                                                             │
│   3. Add OAuth token validation                                             │
│      Fallback: JWT → OAuth → 401 Unauthorized                               │
│      Constraint: ADR-002 (GitHub, Google, Microsoft)                        │
│                                                                             │
│   4. Register in app startup                                                │
│      File: backend/app/main.py                                              │
│      Change: +5 LOC (app.add_middleware)                                    │
│                                                                             │
│   5. Create unit tests                                                      │
│      File: backend/tests/middleware/test_auth_middleware.py                 │
│      Pattern: Follow test_cors_middleware.py                                │
│      Estimated: ~120 LOC                                                    │
│                                                                             │
│ Total Estimated Changes:                                                    │
│   • New files: 2 (~200 LOC)                                                 │
│   • Modified files: 1 (~5 LOC)                                              │
│   • Tests: 1 file (~120 LOC)                                                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ PHASE 3: Approval                                                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   [A] Approve and proceed                                                   │
│   [M] Modify plan                                                           │
│   [S] Save plan to file                                                     │
│   [C] Cancel                                                                │
│                                                                             │
│   Choice:                                                                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Architecture

### 3.1 Component Diagram

```
┌───────────────────────────────────────────────────────────────────────────────┐
│                           sdlcctl plan Command                                │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                        PlanCommand (CLI Layer)                          │ │
│  │                                                                         │ │
│  │  - Parse arguments                                                      │ │
│  │  - Initialize services                                                  │ │
│  │  - Orchestrate workflow                                                 │ │
│  │  - Handle user interaction                                              │ │
│  └────────────────────────────────────┬────────────────────────────────────┘ │
│                                       │                                       │
│  ┌────────────────────────────────────┼────────────────────────────────────┐ │
│  │                        PlanningService (Core)                           │ │
│  │                                    │                                     │ │
│  │  ┌─────────────────────────────────┼─────────────────────────────────┐  │ │
│  │  │                    Pattern Extraction Layer                        │  │ │
│  │  │                                                                    │  │ │
│  │  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │  │ │
│  │  │  │SimilarCode   │  │ADRExplorer   │  │TestPattern   │            │  │ │
│  │  │  │Explorer      │  │              │  │Explorer      │            │  │ │
│  │  │  │              │  │              │  │              │            │  │ │
│  │  │  │- Agentic grep│  │- Load ADRs   │  │- Find tests  │            │  │ │
│  │  │  │- Extract     │  │- Extract     │  │- Extract     │            │  │ │
│  │  │  │  patterns    │  │  constraints │  │  patterns    │            │  │ │
│  │  │  └──────────────┘  └──────────────┘  └──────────────┘            │  │ │
│  │  │                                                                    │  │ │
│  │  └────────────────────────────────────────────────────────────────────┘  │ │
│  │                                                                           │ │
│  │  ┌────────────────────────────────────────────────────────────────────┐  │ │
│  │  │                    Plan Synthesis Layer                            │  │ │
│  │  │                                                                    │  │ │
│  │  │  ┌──────────────────────────────────────────────────────────────┐ │  │ │
│  │  │  │               PlanSynthesizer                                 │ │  │ │
│  │  │  │                                                               │ │  │ │
│  │  │  │  - Combine extracted patterns                                 │ │  │ │
│  │  │  │  - Generate implementation steps                              │ │  │ │
│  │  │  │  - Estimate changes                                           │ │  │ │
│  │  │  │  - Validate against constraints                               │ │  │ │
│  │  │  └──────────────────────────────────────────────────────────────┘ │  │ │
│  │  │                                                                    │  │ │
│  │  └────────────────────────────────────────────────────────────────────┘  │ │
│  │                                                                           │ │
│  │  ┌────────────────────────────────────────────────────────────────────┐  │ │
│  │  │                    Integration Layer                               │  │ │
│  │  │                                                                    │  │ │
│  │  │  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐  │  │ │
│  │  │  │Evidence    │  │Dynamic     │  │AI Provider │  │Database    │  │  │ │
│  │  │  │Vault       │  │Context     │  │(Ollama)    │  │(Postgres)  │  │  │ │
│  │  │  │            │  │Engine      │  │            │  │            │  │  │ │
│  │  │  │Store plan  │  │Inject ctx  │  │Pattern     │  │Store       │  │  │ │
│  │  │  │as evidence │  │to overlay  │  │extraction  │  │sessions    │  │  │ │
│  │  │  └────────────┘  └────────────┘  └────────────┘  └────────────┘  │  │ │
│  │  │                                                                    │  │ │
│  │  └────────────────────────────────────────────────────────────────────┘  │ │
│  │                                                                           │ │
│  └───────────────────────────────────────────────────────────────────────────┘ │
│                                                                               │
└───────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            Planning Data Flow                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. USER INPUT                                                              │
│     ↓                                                                       │
│     task_description: "Add authentication middleware"                       │
│     scope: ["backend/app/middleware", "backend/app/services/auth"]          │
│     depth: "thorough"                                                       │
│                                                                             │
│  2. PARALLEL EXTRACTION (Sub-agents)                                        │
│     ┌────────────────────────────────────────────────────────────────────┐ │
│     │                                                                    │ │
│     │   SimilarCodeExplorer ─────┐                                       │ │
│     │   (agentic grep)           │                                       │ │
│     │                            │                                       │ │
│     │   ADRExplorer ─────────────┼──→ PatternCollection                  │ │
│     │   (constraint extraction)  │                                       │ │
│     │                            │                                       │ │
│     │   TestPatternExplorer ─────┘                                       │ │
│     │   (test convention extraction)                                     │ │
│     │                                                                    │ │
│     └────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  3. SYNTHESIS                                                               │
│     ↓                                                                       │
│     PatternCollection + ADRConstraints + TestPatterns                       │
│           ↓                                                                 │
│     PlanSynthesizer.synthesize()                                            │
│           ↓                                                                 │
│     PlanningContext {                                                       │
│         similar_implementations: [...],                                     │
│         adr_constraints: [...],                                             │
│         code_patterns: {...},                                               │
│         test_patterns: {...},                                               │
│         implementation_plan: [...],                                         │
│         estimated_changes: {...}                                            │
│     }                                                                       │
│                                                                             │
│  4. APPROVAL                                                                │
│     ↓                                                                       │
│     User reviews plan → [Approve | Modify | Cancel]                         │
│                                                                             │
│  5. STORAGE & INJECTION                                                     │
│     ↓                                                                       │
│     Approved plan → Evidence Vault (artifact)                               │
│     Approved plan → Dynamic Context Engine (overlay)                        │
│     Approved plan → .sdlc-context.json (local cache)                        │
│                                                                             │
│  6. CODE GENERATION (with context)                                          │
│     ↓                                                                       │
│     PlanningContext injected into AI prompt                                 │
│     Generated code follows extracted patterns                               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Core Components

### 4.1 PlanningService

```python
# backend/app/services/planning_service.py

from typing import List, Optional
from uuid import UUID
import asyncio

from app.models.planning import PlanningSession, PlanningContext
from app.services.similar_code_explorer import SimilarCodeExplorer
from app.services.adr_explorer import ADRExplorer
from app.services.test_pattern_explorer import TestPatternExplorer
from app.services.plan_synthesizer import PlanSynthesizer


class PlanningService:
    """
    Core planning service that orchestrates pattern extraction
    and plan synthesis.

    Reference: ADR-034-Planning-Subagent-Orchestration
    """

    def __init__(
        self,
        similar_code_explorer: SimilarCodeExplorer,
        adr_explorer: ADRExplorer,
        test_pattern_explorer: TestPatternExplorer,
        plan_synthesizer: PlanSynthesizer,
        db: AsyncSession,
    ):
        self.similar_code_explorer = similar_code_explorer
        self.adr_explorer = adr_explorer
        self.test_pattern_explorer = test_pattern_explorer
        self.plan_synthesizer = plan_synthesizer
        self.db = db

    async def create_plan(
        self,
        task_description: str,
        project_path: str,
        scope: Optional[List[str]] = None,
        depth: str = "medium",
        user_id: Optional[UUID] = None,
    ) -> PlanningContext:
        """
        Create implementation plan for a task.

        Args:
            task_description: What to implement
            project_path: Path to project root
            scope: Directories/files to consider
            depth: Analysis depth (quick|medium|thorough)
            user_id: User creating the plan

        Returns:
            PlanningContext with extracted patterns and plan
        """
        # Create session
        session = PlanningSession(
            task_description=task_description,
            scope=scope,
            depth=depth,
            status="extracting",
            created_by=user_id,
        )
        self.db.add(session)
        await self.db.flush()

        try:
            # Phase 1: Parallel pattern extraction
            similar_impl, adr_constraints, test_patterns = await asyncio.gather(
                self.similar_code_explorer.find_similar(
                    task_description, project_path, scope, depth
                ),
                self.adr_explorer.extract_constraints(
                    task_description, project_path
                ),
                self.test_pattern_explorer.extract_patterns(
                    task_description, project_path, scope
                ),
            )

            # Update session with extraction results
            session.similar_implementations = similar_impl
            session.adr_constraints = adr_constraints
            session.test_patterns = test_patterns
            session.status = "synthesizing"
            await self.db.flush()

            # Phase 2: Synthesize plan
            context = await self.plan_synthesizer.synthesize(
                task_description=task_description,
                similar_implementations=similar_impl,
                adr_constraints=adr_constraints,
                test_patterns=test_patterns,
            )

            # Update session with plan
            session.implementation_plan = context.implementation_plan
            session.estimated_changes = context.estimated_changes
            session.code_patterns = context.code_patterns
            session.status = "pending_approval"
            await self.db.commit()

            return context

        except Exception as e:
            session.status = "failed"
            session.error_message = str(e)
            await self.db.commit()
            raise

    async def approve_plan(
        self,
        session_id: UUID,
        user_id: UUID,
        modifications: Optional[List[str]] = None,
    ) -> PlanningContext:
        """Approve plan for implementation."""
        session = await self.db.get(PlanningSession, session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        session.approved_by = user_id
        session.approved_at = datetime.utcnow()
        session.modifications = modifications
        session.status = "approved"
        await self.db.commit()

        return PlanningContext.from_session(session)

    async def reject_plan(self, session_id: UUID, reason: str) -> None:
        """Reject plan."""
        session = await self.db.get(PlanningSession, session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        session.status = "rejected"
        session.rejection_reason = reason
        await self.db.commit()
```

### 4.2 SimilarCodeExplorer

```python
# backend/app/services/similar_code_explorer.py

from typing import List, Optional
import asyncio
from pathlib import Path

from app.services.ai_service import AIService


class SimilarCodeExplorer:
    """
    Find similar implementations in codebase using agentic grep.

    Key insight: "Agentic grep > RAG" - direct code search finds
    real patterns, RAG can miss context.
    """

    def __init__(self, ai_service: AIService):
        self.ai_service = ai_service

    async def find_similar(
        self,
        task_description: str,
        project_path: str,
        scope: Optional[List[str]] = None,
        depth: str = "medium",
    ) -> List[dict]:
        """
        Find similar implementations using AI-powered search.

        Args:
            task_description: What to implement
            project_path: Path to project root
            scope: Limit search to specific directories
            depth: quick (top 3), medium (top 5), thorough (top 10)

        Returns:
            List of similar implementations with patterns
        """
        # Determine search targets
        search_paths = self._resolve_scope(project_path, scope)

        # Determine result limit based on depth
        limits = {"quick": 3, "medium": 5, "thorough": 10}
        limit = limits.get(depth, 5)

        # Use AI to find similar code
        prompt = f"""
        Find code implementations similar to this task:
        "{task_description}"

        Search in these paths:
        {search_paths}

        For each similar implementation, extract:
        1. File path
        2. Similarity score (0-100%)
        3. Key patterns used:
           - Class/function structure
           - Dependencies
           - Error handling approach
           - Logging patterns

        Return top {limit} most similar implementations.
        Format as JSON array.
        """

        response = await self.ai_service.generate(
            prompt=prompt,
            model="qwen3-coder:30b",  # Best for code analysis
            temperature=0.1,  # Low for consistency
        )

        return self._parse_response(response)

    def _resolve_scope(
        self,
        project_path: str,
        scope: Optional[List[str]]
    ) -> List[str]:
        """Resolve scope to actual paths."""
        base = Path(project_path)

        if not scope:
            # Default scope: source directories
            return [
                str(base / "backend/app"),
                str(base / "frontend/src"),
            ]

        return [str(base / s) for s in scope]

    def _parse_response(self, response: str) -> List[dict]:
        """Parse AI response into structured data."""
        import json

        try:
            # Extract JSON from response
            start = response.find('[')
            end = response.rfind(']') + 1
            if start >= 0 and end > start:
                return json.loads(response[start:end])
        except json.JSONDecodeError:
            pass

        return []
```

### 4.3 ADRExplorer

```python
# backend/app/services/adr_explorer.py

from typing import List
from pathlib import Path

from app.services.ai_service import AIService


class ADRExplorer:
    """
    Extract ADR constraints relevant to a task.
    """

    ADR_PATHS = [
        "docs/02-design/01-ADRs",
        "docs/02-design/03-ADRs",  # Legacy path
    ]

    def __init__(self, ai_service: AIService):
        self.ai_service = ai_service

    async def extract_constraints(
        self,
        task_description: str,
        project_path: str,
    ) -> List[dict]:
        """
        Extract ADR constraints relevant to task.

        Returns:
            List of ADR constraints with requirements
        """
        # Find ADR files
        adr_files = self._find_adr_files(project_path)

        if not adr_files:
            return []

        # Load ADR contents
        adr_contents = self._load_adrs(adr_files)

        # Use AI to extract relevant constraints
        prompt = f"""
        Given this task:
        "{task_description}"

        Review these ADRs and extract constraints that apply:

        {adr_contents}

        For each relevant ADR, extract:
        1. ADR number and title
        2. Specific constraints/requirements that apply to this task
        3. Why this constraint is relevant

        Only include ADRs that directly impact implementation.
        Format as JSON array.
        """

        response = await self.ai_service.generate(
            prompt=prompt,
            model="qwen3:32b",  # Good for analysis
            temperature=0.1,
        )

        return self._parse_response(response)

    def _find_adr_files(self, project_path: str) -> List[Path]:
        """Find all ADR files in project."""
        base = Path(project_path)
        adr_files = []

        for adr_path in self.ADR_PATHS:
            full_path = base / adr_path
            if full_path.exists():
                adr_files.extend(full_path.glob("ADR-*.md"))

        return adr_files

    def _load_adrs(self, adr_files: List[Path]) -> str:
        """Load ADR contents (limited to avoid context overflow)."""
        contents = []
        max_per_adr = 500  # Characters

        for f in adr_files[:20]:  # Max 20 ADRs
            try:
                text = f.read_text()
                # Extract key sections
                summary = self._extract_summary(text, max_per_adr)
                contents.append(f"## {f.name}\n{summary}")
            except Exception:
                continue

        return "\n\n".join(contents)

    def _extract_summary(self, text: str, max_chars: int) -> str:
        """Extract key sections from ADR."""
        # Focus on Decision and Consequences sections
        lines = text.split('\n')
        result = []
        in_section = False

        for line in lines:
            if line.startswith('## Decision') or line.startswith('## Consequences'):
                in_section = True
            elif line.startswith('## ') and in_section:
                in_section = False

            if in_section:
                result.append(line)
                if len('\n'.join(result)) > max_chars:
                    break

        return '\n'.join(result)[:max_chars]

    def _parse_response(self, response: str) -> List[dict]:
        """Parse AI response."""
        import json

        try:
            start = response.find('[')
            end = response.rfind(']') + 1
            if start >= 0 and end > start:
                return json.loads(response[start:end])
        except json.JSONDecodeError:
            pass

        return []
```

### 4.4 PlanSynthesizer

```python
# backend/app/services/plan_synthesizer.py

from typing import List, Optional
from dataclasses import dataclass


@dataclass
class PlanningContext:
    """Context for code generation with planning data."""
    similar_implementations: List[dict]
    adr_constraints: List[dict]
    code_patterns: dict
    test_patterns: dict
    implementation_plan: List[dict]
    estimated_changes: dict


class PlanSynthesizer:
    """
    Synthesize extracted patterns into implementation plan.
    """

    def __init__(self, ai_service):
        self.ai_service = ai_service

    async def synthesize(
        self,
        task_description: str,
        similar_implementations: List[dict],
        adr_constraints: List[dict],
        test_patterns: List[dict],
    ) -> PlanningContext:
        """
        Synthesize patterns into implementation plan.
        """
        # Extract code patterns from similar implementations
        code_patterns = self._extract_code_patterns(similar_implementations)

        # Extract test patterns
        test_pattern_summary = self._summarize_test_patterns(test_patterns)

        # Generate implementation plan
        implementation_plan = await self._generate_plan(
            task_description,
            similar_implementations,
            adr_constraints,
            code_patterns,
        )

        # Estimate changes
        estimated_changes = self._estimate_changes(implementation_plan)

        return PlanningContext(
            similar_implementations=similar_implementations,
            adr_constraints=adr_constraints,
            code_patterns=code_patterns,
            test_patterns=test_pattern_summary,
            implementation_plan=implementation_plan,
            estimated_changes=estimated_changes,
        )

    def _extract_code_patterns(
        self,
        similar_implementations: List[dict]
    ) -> dict:
        """Extract common patterns from similar implementations."""
        patterns = {
            "structure": [],
            "naming": [],
            "dependencies": [],
            "error_handling": [],
            "logging": [],
        }

        for impl in similar_implementations:
            if "patterns" in impl:
                for key in patterns:
                    if key in impl["patterns"]:
                        patterns[key].append(impl["patterns"][key])

        # Deduplicate and summarize
        return {k: list(set(v)) for k, v in patterns.items()}

    def _summarize_test_patterns(
        self,
        test_patterns: List[dict]
    ) -> dict:
        """Summarize test patterns."""
        return {
            "framework": "pytest + pytest-asyncio",
            "mocking": "unittest.mock",
            "coverage_target": "95%",
            "naming": "test_<function>_<scenario>",
        }

    async def _generate_plan(
        self,
        task_description: str,
        similar_implementations: List[dict],
        adr_constraints: List[dict],
        code_patterns: dict,
    ) -> List[dict]:
        """Generate step-by-step implementation plan."""
        prompt = f"""
        Create implementation plan for:
        "{task_description}"

        Similar implementations to follow:
        {similar_implementations[:3]}

        ADR constraints to respect:
        {adr_constraints}

        Code patterns to follow:
        {code_patterns}

        Generate step-by-step plan with:
        1. Step number and description
        2. File to create/modify
        3. Pattern to follow (from similar implementations)
        4. Constraints that apply (from ADRs)
        5. Estimated lines of code

        Format as JSON array.
        """

        response = await self.ai_service.generate(
            prompt=prompt,
            model="qwen3:32b",
            temperature=0.2,
        )

        return self._parse_plan(response)

    def _parse_plan(self, response: str) -> List[dict]:
        """Parse plan from AI response."""
        import json

        try:
            start = response.find('[')
            end = response.rfind(']') + 1
            if start >= 0 and end > start:
                return json.loads(response[start:end])
        except json.JSONDecodeError:
            pass

        return []

    def _estimate_changes(self, plan: List[dict]) -> dict:
        """Estimate total changes from plan."""
        new_files = []
        modified_files = []
        total_loc = 0

        for step in plan:
            file_path = step.get("file", "")
            loc = step.get("estimated_loc", 0)
            total_loc += loc

            if step.get("action") == "create":
                new_files.append(file_path)
            else:
                modified_files.append(file_path)

        return {
            "new_files": list(set(new_files)),
            "modified_files": list(set(modified_files)),
            "total_loc": total_loc,
        }
```

---

## 5. Database Schema

### 5.1 Planning Sessions Table

```sql
-- Migration: s96_create_planning_sessions.py

CREATE TABLE planning_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id),

    -- Input
    task_description TEXT NOT NULL,
    scope JSONB,  -- ["backend/app/services", "backend/app/middleware"]
    depth VARCHAR(20) DEFAULT 'medium' CHECK (depth IN ('quick', 'medium', 'thorough')),

    -- Status
    status VARCHAR(30) DEFAULT 'extracting' CHECK (status IN (
        'extracting', 'synthesizing', 'pending_approval',
        'approved', 'rejected', 'failed'
    )),
    error_message TEXT,
    rejection_reason TEXT,

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
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Constraints
    CONSTRAINT valid_approval CHECK (
        (status = 'approved' AND approved_by IS NOT NULL AND approved_at IS NOT NULL)
        OR status != 'approved'
    )
);

-- Indexes
CREATE INDEX idx_planning_sessions_project ON planning_sessions(project_id);
CREATE INDEX idx_planning_sessions_status ON planning_sessions(status);
CREATE INDEX idx_planning_sessions_created ON planning_sessions(created_at DESC);
CREATE INDEX idx_planning_sessions_created_by ON planning_sessions(created_by);

-- Comments
COMMENT ON TABLE planning_sessions IS 'Planning sub-agent orchestration sessions (ADR-034)';
COMMENT ON COLUMN planning_sessions.depth IS 'Analysis depth: quick (10s), medium (30s), thorough (60s)';
```

---

## 6. CLI Implementation

### 6.1 Command File

```python
# backend/sdlcctl/commands/plan.py

"""
=========================================================================
SDLC 6.1.0 Planning Mode Command
SDLC Orchestrator - Sprint 96

Version: 1.0.0
Date: January 22, 2026
Status: DRAFT
Authority: Backend Team + CTO Approved
Reference: ADR-034-Planning-Subagent-Orchestration

Purpose:
- Extract patterns before code generation
- Prevent architectural drift
- Create human-approved implementation plans

Commands:
    sdlcctl plan "task description"
=========================================================================
"""

import asyncio
from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt
from rich.table import Table

console = Console()


def plan_command(
    task: str = typer.Argument(..., help="Task description"),
    scope: Optional[List[str]] = typer.Option(None, "--scope", "-s"),
    depth: str = typer.Option("medium", "--depth", "-d"),
    output: Optional[Path] = typer.Option(None, "--output", "-o"),
    interactive: bool = typer.Option(True, "--interactive/--no-interactive"),
    auto_approve: bool = typer.Option(False, "--auto-approve"),
    project_id: Optional[str] = typer.Option(None, "--project", "-p"),
    format: str = typer.Option("rich", "--format", "-f"),
) -> None:
    """
    Plan implementation before coding.

    Extracts patterns from codebase, reviews ADRs, and creates
    an implementation plan for human approval.

    Recommended for changes >15 LOC to prevent architectural drift.
    """
    asyncio.run(_run_plan(
        task=task,
        scope=scope,
        depth=depth,
        output=output,
        interactive=interactive,
        auto_approve=auto_approve,
        project_id=project_id,
        format=format,
    ))


async def _run_plan(
    task: str,
    scope: Optional[List[str]],
    depth: str,
    output: Optional[Path],
    interactive: bool,
    auto_approve: bool,
    project_id: Optional[str],
    format: str,
) -> None:
    """Run planning workflow."""
    from app.services.planning_service import PlanningService

    # Display header
    console.print(Panel(
        f"[bold]Planning Mode[/bold]\n\n"
        f"Task: {task}\n"
        f"Depth: {depth}\n"
        f"Scope: {scope or 'All source directories'}",
        title="SDLC Planning",
        border_style="blue",
    ))

    # Phase 1: Pattern extraction
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        extract_task = progress.add_task("Extracting patterns...", total=None)

        # Initialize service (simplified for CLI)
        service = PlanningService.create_for_cli()

        # Create plan
        project_path = str(Path.cwd())
        context = await service.create_plan(
            task_description=task,
            project_path=project_path,
            scope=scope,
            depth=depth,
        )

        progress.update(extract_task, completed=True)

    # Display results
    _display_similar_implementations(context.similar_implementations)
    _display_adr_constraints(context.adr_constraints)
    _display_code_patterns(context.code_patterns)
    _display_implementation_plan(context.implementation_plan)
    _display_estimated_changes(context.estimated_changes)

    # Output to file if requested
    if output:
        _save_plan(context, output, format)
        console.print(f"\n[green]Plan saved to {output}[/green]")
        return

    # Approval workflow
    if not interactive or auto_approve:
        console.print("\n[yellow]Auto-approved (non-interactive mode)[/yellow]")
        return

    # Interactive approval
    choice = Prompt.ask(
        "\n[bold]What would you like to do?[/bold]",
        choices=["a", "m", "s", "c"],
        default="a",
    )

    if choice == "a":
        console.print("[green]Plan approved. Ready for implementation.[/green]")
        _inject_context(context)
    elif choice == "m":
        console.print("[yellow]Modification not yet implemented.[/yellow]")
    elif choice == "s":
        save_path = Prompt.ask("Save to file", default="plan.md")
        _save_plan(context, Path(save_path), "markdown")
        console.print(f"[green]Saved to {save_path}[/green]")
    else:
        console.print("[red]Plan cancelled.[/red]")


def _display_similar_implementations(implementations: List[dict]) -> None:
    """Display similar implementations."""
    console.print("\n[bold]Similar Implementations Found:[/bold]")

    table = Table(show_header=True)
    table.add_column("#", width=3)
    table.add_column("File", style="cyan")
    table.add_column("Similarity", justify="right")
    table.add_column("Key Patterns")

    for i, impl in enumerate(implementations[:5], 1):
        patterns = impl.get("patterns", {})
        pattern_str = ", ".join(patterns.keys())[:50]
        table.add_row(
            str(i),
            impl.get("file", "Unknown"),
            f"{impl.get('similarity', 0)}%",
            pattern_str,
        )

    console.print(table)


def _display_adr_constraints(constraints: List[dict]) -> None:
    """Display ADR constraints."""
    if not constraints:
        return

    console.print("\n[bold]ADR Constraints:[/bold]")

    for c in constraints[:5]:
        console.print(f"  [cyan]{c.get('adr', 'Unknown')}[/cyan]")
        for req in c.get("requirements", [])[:3]:
            console.print(f"    • {req}")


def _display_code_patterns(patterns: dict) -> None:
    """Display extracted code patterns."""
    console.print("\n[bold]Code Patterns Extracted:[/bold]")

    for category, items in patterns.items():
        if items:
            console.print(f"  [cyan]{category}:[/cyan] {', '.join(items[:3])}")


def _display_implementation_plan(plan: List[dict]) -> None:
    """Display implementation plan."""
    console.print("\n[bold]Implementation Plan:[/bold]")

    for i, step in enumerate(plan, 1):
        console.print(f"\n  [cyan]{i}. {step.get('description', 'Step')}[/cyan]")
        console.print(f"     File: {step.get('file', 'N/A')}")
        console.print(f"     Estimated: ~{step.get('estimated_loc', 0)} LOC")


def _display_estimated_changes(changes: dict) -> None:
    """Display estimated changes."""
    console.print("\n[bold]Estimated Changes:[/bold]")
    console.print(f"  New files: {len(changes.get('new_files', []))}")
    console.print(f"  Modified files: {len(changes.get('modified_files', []))}")
    console.print(f"  Total LOC: ~{changes.get('total_loc', 0)}")


def _save_plan(context, output: Path, format: str) -> None:
    """Save plan to file."""
    import json

    if format == "json":
        with open(output, "w") as f:
            json.dump(context.__dict__, f, indent=2)
    else:
        # Markdown format
        with open(output, "w") as f:
            f.write(f"# Implementation Plan\n\n")
            f.write(f"## Task\n{context.implementation_plan}\n\n")
            # ... more sections


def _inject_context(context) -> None:
    """Inject planning context for code generation."""
    import json

    # Save to local context file (gitignored)
    context_file = Path(".sdlc-context.json")
    with open(context_file, "w") as f:
        json.dump({
            "planning_context": context.__dict__,
            "created_at": datetime.utcnow().isoformat(),
        }, f, indent=2, default=str)

    console.print(f"\n[dim]Context saved to {context_file} (gitignored)[/dim]")
```

---

## 7. Integration Points

### 7.1 Evidence Vault Integration

```python
# Store planning session as evidence artifact
async def store_plan_evidence(
    session: PlanningSession,
    evidence_vault: EvidenceVaultService,
) -> str:
    """Store approved plan as evidence."""
    artifact = {
        "type": "planning_session",
        "session_id": str(session.id),
        "task": session.task_description,
        "plan": session.implementation_plan,
        "approved_by": str(session.approved_by),
        "approved_at": session.approved_at.isoformat(),
    }

    return await evidence_vault.store_artifact(
        content=json.dumps(artifact),
        artifact_type="planning_session",
        metadata={
            "session_id": str(session.id),
            "task_hash": hashlib.sha256(session.task_description.encode()).hexdigest(),
        },
    )
```

### 7.2 Dynamic Context Integration

```python
# Inject planning context into dynamic overlay
async def inject_planning_context(
    session: PlanningSession,
    context_engine: DynamicContextEngine,
) -> None:
    """Inject planning context into dynamic overlay."""
    overlay = {
        "planning_active": True,
        "task": session.task_description,
        "constraints": session.adr_constraints,
        "patterns_to_follow": session.code_patterns,
        "implementation_steps": session.implementation_plan,
    }

    await context_engine.update_overlay(
        project_id=session.project_id,
        overlay_type="planning",
        content=overlay,
    )
```

---

## 8. Testing Strategy

### 8.1 Unit Tests

```python
# backend/tests/services/test_planning_service.py

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.services.planning_service import PlanningService


@pytest.fixture
def planning_service():
    return PlanningService(
        similar_code_explorer=AsyncMock(),
        adr_explorer=AsyncMock(),
        test_pattern_explorer=AsyncMock(),
        plan_synthesizer=AsyncMock(),
        db=AsyncMock(),
    )


class TestPlanningService:
    @pytest.mark.asyncio
    async def test_create_plan_extracts_patterns(self, planning_service):
        """Test that create_plan extracts patterns from all explorers."""
        # Arrange
        planning_service.similar_code_explorer.find_similar.return_value = [
            {"file": "middleware/cors.py", "similarity": 85}
        ]
        planning_service.adr_explorer.extract_constraints.return_value = [
            {"adr": "ADR-002", "requirements": ["JWT 15min"]}
        ]

        # Act
        context = await planning_service.create_plan(
            task_description="Add auth middleware",
            project_path="/project",
        )

        # Assert
        assert len(context.similar_implementations) == 1
        assert len(context.adr_constraints) == 1
        planning_service.similar_code_explorer.find_similar.assert_called_once()
        planning_service.adr_explorer.extract_constraints.assert_called_once()


class TestSimilarCodeExplorer:
    @pytest.mark.asyncio
    async def test_find_similar_respects_scope(self):
        """Test that find_similar respects scope parameter."""
        # ...


class TestADRExplorer:
    @pytest.mark.asyncio
    async def test_extract_constraints_finds_relevant_adrs(self):
        """Test that extract_constraints finds relevant ADRs."""
        # ...
```

### 8.2 Integration Tests

```python
# backend/tests/integration/test_plan_command.py

import pytest
from typer.testing import CliRunner

from sdlcctl.cli import app


runner = CliRunner()


class TestPlanCommand:
    def test_plan_command_shows_similar_implementations(self):
        """Test plan command displays similar implementations."""
        result = runner.invoke(app, ["plan", "Add caching layer"])
        assert result.exit_code == 0
        assert "Similar Implementations" in result.output

    def test_plan_command_respects_depth(self):
        """Test plan command respects depth option."""
        result = runner.invoke(app, [
            "plan", "Add logging",
            "--depth", "thorough"
        ])
        assert result.exit_code == 0
```

---

## 9. Timeline

| Sprint | Deliverables | Effort |
|--------|--------------|--------|
| **95** | Architecture design (this doc), Database schema | 1 week |
| **96** | Core services (PlanningService, Explorers) | 2 weeks |
| **97** | CLI implementation, Basic tests | 1 week |
| **98** | Integration (Evidence, Context), Polish | 1 week |

---

## 10. Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Pattern extraction time | <30s (medium depth) | CLI timing |
| ADR coverage | >90% relevant ADRs found | Manual review |
| Plan approval rate | >80% first-pass | Analytics |
| Architectural drift reduction | 90% reduction | Code review feedback |

---

## 11. Open Questions

1. **AI Council Refactor**: Should PlanningService reuse AI Council infrastructure?
2. **Caching**: Should extracted patterns be cached per project?
3. **Multi-file planning**: How to handle plans spanning multiple related tasks?

---

**Document Status**: DRAFT
**Next Step**: CTO Review → Sprint 95 Backlog
