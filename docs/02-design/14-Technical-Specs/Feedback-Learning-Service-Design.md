# Feedback Learning Service - Technical Design Document
## Feedback Loop Closure - Learning from Code Reviews

**Epic**: EP-11 Feedback Loop Closure
**Status**: PLANNED
**Reference**: ADR-034-Planning-Subagent-Orchestration
**Depends On**: Planning-Orchestrator-Service, Conformance-Check-Service
**Implementation**: Sprint 100

---

## 1. Executive Summary

This document describes the **Feedback Loop Closure** feature, which closes the learning cycle from code review feedback back to specification refinement. This enables continuous improvement of AI-generated plans based on real-world review outcomes.

### Key Insight (Expert Workflow)

> "No learning from code review feedback" - This was identified as a key gap in SDLC Orchestrator
>
> **Solution**: Close the feedback loop from PR → Spec refinement
> - Extract learnings from PR review comments
> - Categorize by type (pattern_violation, missing_requirement, etc.)
> - Update decomposition hints for future generations

### Business Value

| Metric | Before | After |
|--------|--------|-------|
| Recurring review comments | Many | Significantly reduced |
| AI plan quality | Static | Continuously improving |
| Pattern drift detection | Manual | Automated |
| Developer context | Lost between PRs | Preserved and applied |

---

## 2. Architecture Overview

### 2.1 System Context Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         FEEDBACK LOOP CLOSURE                                │
│                        (Sprint 100 - EP-11)                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────┐                                 ┌─────────────────────────┐│
│  │   GitHub    │                                 │  SDLC Orchestrator      ││
│  │   PR/MR     │                                 │  Dashboard              ││
│  └──────┬──────┘                                 └────────────┬────────────┘│
│         │                                                     │              │
│         │ Webhook: pull_request_review                        │              │
│         │ Webhook: pull_request_review_comment               │              │
│         ▼                                                     │              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                    FEEDBACK EXTRACTION LAYER                            ││
│  │                                                                          ││
│  │  ┌────────────────────────────────────────────────────────────────────┐ ││
│  │  │              FeedbackLearningService                               │ ││
│  │  │        (backend/app/services/feedback_learning_service.py)         │ ││
│  │  │                                                                     │ ││
│  │  │  Methods:                                                           │ ││
│  │  │  • extract_learnings_from_pr(pr_id) → list[PRLearning]            │ ││
│  │  │  • categorize_feedback(comment) → FeedbackType                    │ ││
│  │  │  • update_decomposition_hints(project_id)                          │ ││
│  │  │  • generate_claude_md_update(learnings) → str                      │ ││
│  │  │  • get_learning_stats(project_id) → LearningStats                  │ ││
│  │  └────────────────────────────────────────────────────────────────────┘ ││
│  │                              │                                          ││
│  │                              ▼                                          ││
│  │  ┌────────────────────────────────────────────────────────────────────┐ ││
│  │  │              AI Analysis Pipeline                                   │ ││
│  │  │                                                                     │ ││
│  │  │  1. Parse review comments                                           │ ││
│  │  │  2. Use AI to extract semantic meaning                             │ ││
│  │  │  3. Categorize by feedback type                                     │ ││
│  │  │  4. Link to original spec section (if traceable)                   │ ││
│  │  │  5. Extract corrective pattern                                      │ ││
│  │  └────────────────────────────────────────────────────────────────────┘ ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                              │                                               │
│                              ▼                                               │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                     LEARNING STORAGE LAYER                              ││
│  │                                                                          ││
│  │  ┌────────────────────────────────────────────────────────────────────┐ ││
│  │  │                     pr_learnings Table                             │ ││
│  │  │                                                                     │ ││
│  │  │  id: UUID (PK)                                                     │ ││
│  │  │  project_id: UUID (FK → projects)                                  │ ││
│  │  │  pr_id: str                                                        │ ││
│  │  │  pr_url: str                                                       │ ││
│  │  │  feedback_type: enum                                               │ ││
│  │  │  original_spec_section: text (nullable)                            │ ││
│  │  │  corrected_approach: text                                          │ ││
│  │  │  pattern_extracted: text                                           │ ││
│  │  │  reviewer_id: str                                                  │ ││
│  │  │  created_at: timestamp                                             │ ││
│  │  │  applied_to_hints: bool                                            │ ││
│  │  │  applied_at: timestamp (nullable)                                  │ ││
│  │  └────────────────────────────────────────────────────────────────────┘ ││
│  │                                                                          ││
│  │  ┌────────────────────────────────────────────────────────────────────┐ ││
│  │  │               decomposition_hints Table                            │ ││
│  │  │                                                                     │ ││
│  │  │  id: UUID (PK)                                                     │ ││
│  │  │  project_id: UUID (FK → projects)                                  │ ││
│  │  │  hint_type: enum (pattern, antipattern, convention)                │ ││
│  │  │  content: text                                                     │ ││
│  │  │  source_learnings: UUID[] (FK → pr_learnings)                      │ ││
│  │  │  confidence: float (0-1)                                           │ ││
│  │  │  created_at: timestamp                                             │ ││
│  │  │  updated_at: timestamp                                             │ ││
│  │  └────────────────────────────────────────────────────────────────────┘ ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                              │                                               │
│                              ▼                                               │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                    IMPROVEMENT APPLICATION LAYER                        ││
│  │                                                                          ││
│  │  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐      ││
│  │  │ Monthly Job:     │  │ Quarterly Job:   │  │ On-Demand:       │      ││
│  │  │ Update           │  │ Update           │  │ Export           │      ││
│  │  │ Decomposition    │  │ CLAUDE.md        │  │ Learning         │      ││
│  │  │ Hints            │  │ Patterns         │  │ Report           │      ││
│  │  └──────────────────┘  └──────────────────┘  └──────────────────┘      ││
│  │           │                     │                     │                  ││
│  │           ▼                     ▼                     ▼                  ││
│  │  ┌────────────────────────────────────────────────────────────────────┐ ││
│  │  │                   Improved AI Planning                             │ ││
│  │  │                                                                     │ ││
│  │  │  • PlanningOrchestratorService reads decomposition_hints          │ ││
│  │  │  • AI plans incorporate learned patterns                           │ ││
│  │  │  • Avoids previously-flagged antipatterns                          │ ││
│  │  │  • CLAUDE.md reflects accumulated wisdom                           │ ││
│  │  └────────────────────────────────────────────────────────────────────┘ ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Data Flow

```
GitHub PR Merged with Review Comments
           │
           ▼
┌─────────────────────────────────────┐
│  GitHub Webhook                      │
│  Event: pull_request (closed+merged) │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  WebhookHandler                      │
│  Route: POST /webhooks/github        │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────────┐
│                   FeedbackLearningService                        │
│                                                                  │
│  Step 1: Fetch PR Review Comments (GitHub API)                  │
│          │                                                       │
│          ▼                                                       │
│  Step 2: Filter Actionable Comments                             │
│          • Skip "LGTM", "looks good", etc.                      │
│          • Keep substantive feedback                            │
│          │                                                       │
│          ▼                                                       │
│  Step 3: AI Analysis (per comment)                              │
│          • Extract semantic meaning                              │
│          • Categorize feedback type                             │
│          • Identify pattern/antipattern                          │
│          │                                                       │
│          ▼                                                       │
│  Step 4: Store in pr_learnings Table                            │
│          │                                                       │
│          ▼                                                       │
│  Step 5: Check if Monthly Aggregation Due                       │
│          │                                                       │
│          └─── If due ──▶ update_decomposition_hints()           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Database Schema

### 3.1 pr_learnings Table

```sql
CREATE TABLE pr_learnings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,

    -- PR Identification
    pr_id VARCHAR(50) NOT NULL,
    pr_url VARCHAR(500) NOT NULL,
    pr_title VARCHAR(500),
    pr_number INTEGER,

    -- Feedback Classification
    feedback_type VARCHAR(50) NOT NULL,  -- enum
    severity VARCHAR(20) DEFAULT 'medium',  -- low, medium, high

    -- Learning Content
    original_comment TEXT NOT NULL,
    original_spec_section TEXT,  -- nullable, for traceability
    corrected_approach TEXT NOT NULL,
    pattern_extracted TEXT,  -- reusable pattern for future

    -- Metadata
    reviewer_id VARCHAR(100),
    reviewer_name VARCHAR(200),
    file_path VARCHAR(500),
    line_number INTEGER,

    -- Application Status
    applied_to_hints BOOLEAN DEFAULT FALSE,
    applied_at TIMESTAMP WITH TIME ZONE,

    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Indexes
    INDEX idx_pr_learnings_project_id (project_id),
    INDEX idx_pr_learnings_feedback_type (feedback_type),
    INDEX idx_pr_learnings_created_at (created_at),
    INDEX idx_pr_learnings_applied (applied_to_hints)
);

-- Feedback Types Enum
CREATE TYPE feedback_type_enum AS ENUM (
    'pattern_violation',      -- Violated established pattern
    'missing_requirement',    -- Missed a requirement
    'edge_case',              -- Unhandled edge case
    'performance',            -- Performance issue
    'security',               -- Security concern
    'code_style',             -- Style/convention issue
    'architecture',           -- Architectural concern
    'testing',                -- Missing/inadequate tests
    'documentation',          -- Documentation issue
    'other'                   -- Uncategorized
);
```

### 3.2 decomposition_hints Table

```sql
CREATE TABLE decomposition_hints (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,

    -- Hint Classification
    hint_type VARCHAR(30) NOT NULL,  -- pattern, antipattern, convention
    category VARCHAR(50) NOT NULL,   -- same as PatternCategory enum

    -- Content
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    example_code TEXT,

    -- Provenance
    source_learnings UUID[] DEFAULT '{}',  -- FK → pr_learnings
    source_count INTEGER DEFAULT 1,

    -- Quality
    confidence FLOAT DEFAULT 0.5 CHECK (confidence >= 0 AND confidence <= 1),
    times_applied INTEGER DEFAULT 0,
    times_helpful INTEGER DEFAULT 0,  -- positive feedback count

    -- Lifecycle
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,  -- optional auto-expiry

    -- Indexes
    INDEX idx_decomposition_hints_project_id (project_id),
    INDEX idx_decomposition_hints_category (category),
    INDEX idx_decomposition_hints_active (is_active),
    UNIQUE (project_id, title)
);

-- Hint Types
CREATE TYPE hint_type_enum AS ENUM (
    'pattern',       -- Good pattern to follow
    'antipattern',   -- Pattern to avoid
    'convention'     -- Naming/style convention
);
```

### 3.3 learning_aggregations Table (For Analytics)

```sql
CREATE TABLE learning_aggregations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,

    -- Aggregation Period
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    period_type VARCHAR(20) NOT NULL,  -- weekly, monthly, quarterly

    -- Statistics
    total_learnings INTEGER DEFAULT 0,
    by_feedback_type JSONB DEFAULT '{}',
    by_severity JSONB DEFAULT '{}',

    -- Trends
    top_patterns JSONB DEFAULT '[]',
    top_antipatterns JSONB DEFAULT '[]',
    improvement_score FLOAT,  -- calculated metric

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE (project_id, period_start, period_type)
);
```

---

## 4. Core Services

### 4.1 FeedbackLearningService

**File**: `backend/app/services/feedback_learning_service.py`

```python
class FeedbackLearningService:
    """
    Extracts learnings from PR review comments and updates decomposition hints.

    This service closes the feedback loop from code review → improved AI planning.

    Workflow:
    1. On PR merge: extract_learnings_from_pr()
    2. Monthly: update_decomposition_hints()
    3. Quarterly: generate_claude_md_update()
    4. On-demand: get_learning_stats(), export_report()
    """

    async def extract_learnings_from_pr(
        self,
        project_id: UUID,
        pr_id: str,
        pr_url: str,
    ) -> list[PRLearning]:
        """
        Extract learnings from a merged PR's review comments.

        Steps:
        1. Fetch review comments from GitHub API
        2. Filter actionable comments
        3. Use AI to analyze each comment
        4. Categorize and extract patterns
        5. Store in pr_learnings table

        Args:
            project_id: Project UUID
            pr_id: GitHub PR ID
            pr_url: Full PR URL

        Returns:
            List of extracted PRLearning objects
        """
        pass

    def categorize_feedback(
        self,
        comment: str,
        file_path: str,
        diff_context: str,
    ) -> FeedbackCategory:
        """
        Categorize a review comment using AI.

        Categories:
        - pattern_violation: Violated established pattern
        - missing_requirement: Missed a requirement
        - edge_case: Unhandled edge case
        - performance: Performance concern
        - security: Security issue
        - code_style: Style/convention issue
        - architecture: Architectural concern
        - testing: Missing/inadequate tests
        - documentation: Documentation issue

        Args:
            comment: Review comment text
            file_path: File being reviewed
            diff_context: Surrounding diff context

        Returns:
            FeedbackCategory enum
        """
        pass

    async def update_decomposition_hints(
        self,
        project_id: UUID,
        since: datetime | None = None,
    ) -> int:
        """
        Aggregate learnings and update decomposition hints.

        Run monthly to:
        1. Aggregate learnings since last run
        2. Identify recurring patterns
        3. Calculate confidence scores
        4. Create/update decomposition_hints

        Args:
            project_id: Project UUID
            since: Only process learnings since this date

        Returns:
            Number of hints created/updated
        """
        pass

    async def generate_claude_md_update(
        self,
        project_id: UUID,
        learnings: list[PRLearning],
    ) -> str:
        """
        Generate CLAUDE.md update suggestions based on learnings.

        Quarterly task to:
        1. Analyze accumulated learnings
        2. Identify significant patterns
        3. Generate markdown sections

        Args:
            project_id: Project UUID
            learnings: Learnings to analyze

        Returns:
            Markdown content for CLAUDE.md update
        """
        pass

    async def get_learning_stats(
        self,
        project_id: UUID,
        period: str = "monthly",
    ) -> LearningStats:
        """
        Get learning statistics for a project.

        Args:
            project_id: Project UUID
            period: Aggregation period (weekly, monthly, quarterly)

        Returns:
            LearningStats with counts, trends, top patterns
        """
        pass
```

### 4.2 AI Analysis Prompts

```python
FEEDBACK_CATEGORIZATION_PROMPT = """
Analyze this code review comment and categorize it.

Review Comment:
{comment}

File: {file_path}
Diff Context:
{diff_context}

Categorize as one of:
- pattern_violation: The code violated an established pattern
- missing_requirement: A requirement was missed
- edge_case: An edge case was not handled
- performance: Performance concern
- security: Security issue
- code_style: Style/convention issue
- architecture: Architectural concern
- testing: Missing or inadequate tests
- documentation: Documentation issue
- other: None of the above

Respond with JSON:
{{
  "category": "<category>",
  "severity": "<low|medium|high>",
  "pattern_extracted": "<reusable pattern or null>",
  "corrected_approach": "<how to fix this>"
}}
"""

CLAUDE_MD_UPDATE_PROMPT = """
Based on these accumulated learnings from code reviews, generate
suggestions for updating the project's CLAUDE.md file.

Learnings Summary:
{learnings_summary}

Top Recurring Issues:
{top_issues}

Generate markdown sections that could be added to CLAUDE.md to help
AI coding assistants avoid these issues in the future.

Focus on:
1. Patterns to follow
2. Antipatterns to avoid
3. Project-specific conventions

Output format: markdown
"""
```

---

## 5. API Endpoints

### 5.1 Learning Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/projects/{id}/learnings/extract` | Trigger learning extraction for a PR |
| GET | `/api/v1/projects/{id}/learnings` | List learnings for a project |
| GET | `/api/v1/projects/{id}/learnings/stats` | Get learning statistics |
| GET | `/api/v1/projects/{id}/learnings/{learning_id}` | Get specific learning |
| DELETE | `/api/v1/projects/{id}/learnings/{learning_id}` | Delete a learning |

### 5.2 Hint Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/projects/{id}/hints` | List decomposition hints |
| GET | `/api/v1/projects/{id}/hints/{hint_id}` | Get specific hint |
| PUT | `/api/v1/projects/{id}/hints/{hint_id}` | Update hint |
| DELETE | `/api/v1/projects/{id}/hints/{hint_id}` | Delete hint |
| POST | `/api/v1/projects/{id}/hints/regenerate` | Trigger hint regeneration |

### 5.3 Reports

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/projects/{id}/learnings/report` | Generate learning report |
| GET | `/api/v1/projects/{id}/learnings/claude-md-suggestions` | Get CLAUDE.md suggestions |

### 5.4 Webhook Handler

```python
@router.post("/webhooks/github")
async def handle_github_webhook(
    request: Request,
    x_github_event: str = Header(...),
    x_hub_signature_256: str = Header(...),
):
    """
    Handle GitHub webhook events.

    Supported events:
    - pull_request (action: closed, merged: true)
    - pull_request_review (action: submitted)
    - pull_request_review_comment (action: created)
    """
    if x_github_event == "pull_request":
        payload = await request.json()
        if payload.get("action") == "closed" and payload.get("merged"):
            # Trigger learning extraction
            await feedback_service.extract_learnings_from_pr(
                project_id=get_project_id_from_repo(payload["repository"]),
                pr_id=str(payload["pull_request"]["id"]),
                pr_url=payload["pull_request"]["html_url"],
            )
```

---

## 6. Pydantic Schemas

```python
# === Input Schemas ===

class ExtractLearningRequest(BaseModel):
    pr_url: str
    force: bool = False  # Re-extract even if already processed

class HintUpdateRequest(BaseModel):
    title: str | None = None
    content: str | None = None
    is_active: bool | None = None
    confidence: float | None = Field(None, ge=0, le=1)

# === Output Schemas ===

class FeedbackType(str, Enum):
    PATTERN_VIOLATION = "pattern_violation"
    MISSING_REQUIREMENT = "missing_requirement"
    EDGE_CASE = "edge_case"
    PERFORMANCE = "performance"
    SECURITY = "security"
    CODE_STYLE = "code_style"
    ARCHITECTURE = "architecture"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    OTHER = "other"

class PRLearning(BaseModel):
    id: UUID
    project_id: UUID
    pr_id: str
    pr_url: str
    pr_title: str | None
    feedback_type: FeedbackType
    severity: str  # low, medium, high
    original_comment: str
    original_spec_section: str | None
    corrected_approach: str
    pattern_extracted: str | None
    reviewer_name: str | None
    file_path: str | None
    line_number: int | None
    applied_to_hints: bool
    created_at: datetime

class DecompositionHint(BaseModel):
    id: UUID
    project_id: UUID
    hint_type: str  # pattern, antipattern, convention
    category: str
    title: str
    content: str
    example_code: str | None
    confidence: float
    source_count: int
    times_applied: int
    times_helpful: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

class LearningStats(BaseModel):
    project_id: UUID
    period: str
    period_start: date
    period_end: date
    total_learnings: int
    by_feedback_type: dict[str, int]
    by_severity: dict[str, int]
    top_patterns: list[str]
    top_antipatterns: list[str]
    improvement_score: float | None  # 0-100

class ClaudeMdSuggestion(BaseModel):
    section_title: str
    content: str
    based_on_learnings: int
    confidence: float
```

---

## 7. UI Components

### 7.1 Learnings Dashboard

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Project: SDLC Orchestrator                              [Export Report]    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  Learning Stats (Last 30 Days)                                         │ │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐      │ │
│  │  │ Total       │ │ Patterns    │ │ Antipatterns│ │ Improvement │      │ │
│  │  │ Learnings   │ │ Extracted   │ │ Identified  │ │ Score       │      │ │
│  │  │             │ │             │ │             │ │             │      │ │
│  │  │    47       │ │    12       │ │    8        │ │   78%       │      │ │
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘      │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  Feedback Distribution                                                  │ │
│  │  ┌───────────────────────────────────────────────────────────────────┐ │ │
│  │  │ pattern_violation    ████████████████████░░░░░░░░░  42%           │ │ │
│  │  │ code_style           ████████░░░░░░░░░░░░░░░░░░░░░░  21%           │ │ │
│  │  │ testing              ██████░░░░░░░░░░░░░░░░░░░░░░░░  15%           │ │ │
│  │  │ edge_case            █████░░░░░░░░░░░░░░░░░░░░░░░░░  11%           │ │ │
│  │  │ other                ████░░░░░░░░░░░░░░░░░░░░░░░░░░  11%           │ │ │
│  │  └───────────────────────────────────────────────────────────────────┘ │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  Recent Learnings                                      [View All →]    │ │
│  │  ┌───────────────────────────────────────────────────────────────────┐ │ │
│  │  │ 🔴 HIGH | pattern_violation                           2 hours ago │ │ │
│  │  │    PR #123: "Add OAuth2 authentication"                           │ │ │
│  │  │    "Missing CSRF protection in OAuth callback"                    │ │ │
│  │  │    Pattern: Always include CSRF token validation                  │ │ │
│  │  ├───────────────────────────────────────────────────────────────────┤ │ │
│  │  │ 🟡 MED  | code_style                                 1 day ago    │ │ │
│  │  │    PR #121: "Refactor user service"                               │ │ │
│  │  │    "Use async context manager for DB sessions"                    │ │ │
│  │  │    Convention: async with get_session() as db:                    │ │ │
│  │  ├───────────────────────────────────────────────────────────────────┤ │ │
│  │  │ 🟢 LOW  | documentation                              2 days ago   │ │ │
│  │  │    PR #120: "Add caching layer"                                   │ │ │
│  │  │    "Add docstring explaining cache invalidation"                  │ │ │
│  │  │    Convention: Document all public methods                        │ │ │
│  │  └───────────────────────────────────────────────────────────────────┘ │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 7.2 Decomposition Hints Manager

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Decomposition Hints                                 [+ Add Hint] [Refresh] │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Filter: [All Types ▼] [All Categories ▼] [Active Only ☑]                  │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  ✅ PATTERN | security                            Confidence: 92%       │ │
│  │     CSRF Token Validation                                               │ │
│  │     ────────────────────────────────────────────────────────────────── │ │
│  │     Always validate CSRF token in OAuth callbacks and form submissions. │ │
│  │     Example:                                                            │ │
│  │     ```python                                                           │ │
│  │     @router.post("/oauth/callback")                                     │ │
│  │     async def callback(csrf_token: str = Form(...)):                   │ │
│  │         validate_csrf_token(csrf_token)                                 │ │
│  │     ```                                                                 │ │
│  │     Source: 5 learnings | Applied: 12 times | Helpful: 10              │ │
│  │                                                      [Edit] [Disable]   │ │
│  ├────────────────────────────────────────────────────────────────────────┤ │
│  │  ❌ ANTIPATTERN | database                        Confidence: 85%       │ │
│  │     Raw SQL in Business Logic                                           │ │
│  │     ────────────────────────────────────────────────────────────────── │ │
│  │     Avoid raw SQL queries in service layer. Use ORM methods or         │ │
│  │     repository pattern.                                                 │ │
│  │     Source: 3 learnings | Applied: 8 times | Helpful: 7                │ │
│  │                                                      [Edit] [Disable]   │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 8. Background Jobs

### 8.1 Monthly Hint Aggregation

```python
# Celery task or APScheduler job
@celery.task
def monthly_hint_aggregation():
    """
    Run monthly to aggregate learnings into hints.

    Schedule: First day of each month, 2:00 AM UTC
    """
    projects = get_all_active_projects()

    for project in projects:
        try:
            feedback_service.update_decomposition_hints(
                project_id=project.id,
                since=datetime.utcnow() - timedelta(days=30)
            )
        except Exception as e:
            logger.error(f"Hint aggregation failed for {project.id}: {e}")
```

### 8.2 Quarterly CLAUDE.md Suggestions

```python
@celery.task
def quarterly_claude_md_suggestions():
    """
    Run quarterly to generate CLAUDE.md update suggestions.

    Schedule: First day of Q1, Q2, Q3, Q4 at 3:00 AM UTC
    """
    projects = get_all_active_projects()

    for project in projects:
        try:
            learnings = get_learnings_since(
                project.id,
                datetime.utcnow() - timedelta(days=90)
            )

            if len(learnings) >= 10:  # Minimum threshold
                suggestions = feedback_service.generate_claude_md_update(
                    project_id=project.id,
                    learnings=learnings
                )

                # Notify project admins
                notify_admins(project.id, "CLAUDE.md Update Suggestions Ready")

        except Exception as e:
            logger.error(f"CLAUDE.md generation failed for {project.id}: {e}")
```

---

## 9. Integration with Planning Orchestrator

### 9.1 Hint Injection into Planning

```python
# In PlanningOrchestratorService

async def plan(self, request: PlanningRequest) -> PlanningResult:
    # ... existing code ...

    # NEW: Load decomposition hints
    hints = await self._load_decomposition_hints(request.project_id)

    # Inject hints into plan generation
    plan = await self._generate_plan(
        task=request.task,
        patterns=patterns,
        adr_scan=adr_scan,
        hints=hints,  # NEW: Pass hints
    )

    # Track hint usage
    await self._track_hint_applications(plan, hints)

    return result

async def _load_decomposition_hints(
    self,
    project_id: UUID,
) -> list[DecompositionHint]:
    """Load active decomposition hints for a project."""
    return await db.query(DecompositionHint).filter(
        DecompositionHint.project_id == project_id,
        DecompositionHint.is_active == True,
        DecompositionHint.confidence >= 0.5,
    ).order_by(
        DecompositionHint.confidence.desc()
    ).limit(20).all()
```

### 9.2 Hint-Aware Plan Generation

```python
async def _generate_plan(
    self,
    task: str,
    patterns: PatternSummary,
    adr_scan: ADRScanResult | None,
    hints: list[DecompositionHint],  # NEW
) -> ImplementationPlan:
    # Include hints in plan generation prompt
    pattern_hints = [h for h in hints if h.hint_type == "pattern"]
    antipattern_hints = [h for h in hints if h.hint_type == "antipattern"]
    convention_hints = [h for h in hints if h.hint_type == "convention"]

    # Incorporate into plan steps
    plan = generate_base_plan(task, patterns)

    # Add pattern recommendations
    for hint in pattern_hints:
        if is_relevant_to_task(hint, task):
            plan.patterns_to_follow.append(hint.title)

    # Add antipattern warnings
    for hint in antipattern_hints:
        if is_relevant_to_task(hint, task):
            plan.risks.append(f"Avoid: {hint.title}")

    return plan
```

---

## 10. Performance Targets

| Metric | Target | Notes |
|--------|--------|-------|
| Learning extraction (per PR) | <30s | Includes GitHub API calls |
| Hint aggregation (per project) | <60s | Monthly batch job |
| CLAUDE.md generation | <2min | Quarterly, AI-intensive |
| Hint lookup (planning) | <100ms | Indexed query |
| Dashboard stats | <500ms | Cached aggregations |

---

## 11. Files to Create

| File | Purpose | Est. Lines |
|------|---------|------------|
| `backend/app/services/feedback_learning_service.py` | Core service | ~500 |
| `backend/app/schemas/feedback_learning.py` | Pydantic models | ~200 |
| `backend/app/api/routes/learnings.py` | API endpoints | ~300 |
| `backend/app/models/pr_learning.py` | SQLAlchemy model | ~60 |
| `backend/app/models/decomposition_hint.py` | SQLAlchemy model | ~50 |
| `backend/alembic/versions/xxx_add_feedback_tables.py` | Migration | ~100 |
| `backend/app/jobs/feedback_jobs.py` | Background jobs | ~150 |
| `frontend/src/hooks/useLearnings.ts` | React hooks | ~150 |
| `frontend/src/components/learnings/` | UI components | ~500 |
| `backend/tests/services/test_feedback_learning.py` | Tests | ~400 |

**Total**: ~2,410 lines

---

## 12. Sprint 100 Deliverables

| Deliverable | Priority | Status |
|-------------|----------|--------|
| FeedbackLearningService | P0 | PLANNED |
| pr_learnings table migration | P0 | PLANNED |
| decomposition_hints table migration | P0 | PLANNED |
| Learning extraction API | P0 | PLANNED |
| Hint management API | P1 | PLANNED |
| GitHub webhook handler | P1 | PLANNED |
| Learnings Dashboard UI | P1 | PLANNED |
| Hints Manager UI | P2 | PLANNED |
| Monthly aggregation job | P2 | PLANNED |
| Integration with PlanningOrchestrator | P1 | PLANNED |
| Unit tests | P1 | PLANNED |
| Integration tests | P2 | PLANNED |

---

## 13. Success Criteria

| Metric | Target | Measurement |
|--------|--------|-------------|
| PR learnings extracted | >80% accuracy | AI categorization accuracy |
| Hint generation | >70% relevance | Manual review sample |
| Planning improvement | Measurable | A/B test plan quality |
| Developer adoption | >50% | Teams actively reviewing hints |
| Reduced review comments | -20% | Compare before/after |

---

## 14. Dependencies

### Internal

- Sprint 98-99 complete (PlanningOrchestratorService)
- GitHub OAuth integration (existing)
- AI service (Ollama/Claude integration)

### External

- GitHub API (PR comments, reviews)
- Background job scheduler (Celery or APScheduler)

---

## Appendix A: AI Prompt Examples

### Feedback Categorization

```
Input Comment:
"The error handling here doesn't account for network timeouts.
Should wrap in try/except and handle ConnectionError."

AI Output:
{
  "category": "edge_case",
  "severity": "medium",
  "pattern_extracted": "Always handle network-related exceptions (ConnectionError, TimeoutError) in external API calls",
  "corrected_approach": "Add try/except block to catch ConnectionError and TimeoutError with appropriate retry logic"
}
```

### CLAUDE.md Suggestion

```
## Network Error Handling (Auto-generated from 7 learnings)

When making external API calls, always handle network-related exceptions:

```python
try:
    response = await client.get(url, timeout=30)
except (ConnectionError, TimeoutError) as e:
    logger.error(f"Network error: {e}")
    raise ServiceUnavailableError("External service unavailable")
```

This pattern was extracted from code reviews identifying missing error handling
in OAuth callbacks, payment webhooks, and third-party API integrations.
```

---

**Document Version**: 1.0.0
**Last Updated**: January 23, 2026
**Author**: Backend Team
**Reviewer**: CTO
**Status**: PLANNED
