# ADR-012: AI Task Decomposition Service

**Status**: APPROVED
**Date**: December 3, 2025
**Decision Makers**: CTO, CPO (joint review)
**Stage**: Stage 02 (HOW - Design & Architecture)
**Framework**: SDLC 4.9.1

---

## Context

**Problem Statement**: CEO có thể phân tích user story và decompose thành tasks hiệu quả. PM/Tech Lead khác mất nhiều thời gian hơn và thường miss edge cases.

**Current State**:
- CEO: 10 phút decompose 1 user story → 8-12 tasks với acceptance criteria
- Average PM: 30-45 phút → 5-8 tasks, thiếu edge cases
- Junior Dev: 60+ phút → incomplete decomposition

**Goal**: AI service decompose user stories với chất lượng tương đương CEO trong <2 phút.

---

## Decision

Implement **AI Task Decomposition Service** với:

1. **Input**: User story + project context + SDLC stage
2. **Output**: Structured task list với estimates, dependencies, acceptance criteria
3. **Quality**: Match CEO's decomposition quality (measured by task completeness score)

### Task Decomposition Flow

```yaml
1. Input Parsing:
   - Extract user story components (As a, I want, So that)
   - Identify domain entities
   - Detect technical requirements

2. Context Enrichment:
   - Load project profile (tech stack, team size, stage)
   - Fetch related existing tasks
   - Include SDLC stage requirements

3. AI Decomposition:
   - Primary: Ollama (qwen2.5:14b) for Vietnamese context
   - Fallback: Claude for complex technical stories
   - Output: JSON structured task list

4. Validation & Enhancement:
   - Check completeness against checklist
   - Add missing edge cases
   - Estimate effort based on team velocity

5. Human Review:
   - Present decomposition to PM/Tech Lead
   - Allow refinement
   - Learn from corrections
```

---

## Architecture Design

### 1. Data Model

```python
# models/task_decomposition.py
from sqlalchemy import Column, String, Integer, JSON, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, ARRAY

class DecomposedTask(Base):
    """AI-generated task from user story decomposition"""
    __tablename__ = "decomposed_tasks"

    id = Column(UUID, primary_key=True, default=uuid4)
    user_story_id = Column(UUID, ForeignKey("user_stories.id"), nullable=False)
    project_id = Column(UUID, ForeignKey("projects.id"), nullable=False)

    # Task details
    title = Column(String(200), nullable=False)
    description = Column(Text)
    task_type = Column(String(50))  # feature, bug, chore, spike
    priority = Column(String(20))  # P0, P1, P2, P3

    # Estimates
    estimated_hours = Column(Integer)
    complexity = Column(String(20))  # trivial, simple, medium, complex, unknown
    confidence_score = Column(Float)  # AI's confidence in estimate

    # Dependencies
    depends_on = Column(ARRAY(UUID))  # Task IDs this depends on
    blocks = Column(ARRAY(UUID))  # Task IDs blocked by this

    # Acceptance criteria
    acceptance_criteria = Column(JSON)
    """
    Example:
    [
        {"id": "AC1", "description": "User can login with email", "testable": true},
        {"id": "AC2", "description": "Error shown for invalid credentials", "testable": true}
    ]
    """

    # Technical details
    affected_components = Column(ARRAY(String))  # ["auth-service", "user-db"]
    suggested_assignee_role = Column(String(50))  # "backend", "frontend", "fullstack"

    # AI metadata
    ai_provider = Column(String(50))  # "ollama", "claude"
    ai_model = Column(String(100))
    decomposition_prompt = Column(Text)
    raw_ai_response = Column(JSON)

    # Review status
    review_status = Column(String(20), default="pending")  # pending, approved, rejected, modified
    reviewed_by = Column(UUID, ForeignKey("users.id"))
    review_notes = Column(Text)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)


class DecompositionSession(Base):
    """Track decomposition sessions for learning"""
    __tablename__ = "decomposition_sessions"

    id = Column(UUID, primary_key=True, default=uuid4)
    user_story_id = Column(UUID, ForeignKey("user_stories.id"))
    project_id = Column(UUID, ForeignKey("projects.id"))

    # Session metrics
    ai_tasks_generated = Column(Integer)
    tasks_approved = Column(Integer)
    tasks_modified = Column(Integer)
    tasks_rejected = Column(Integer)

    # Quality metrics
    completeness_score = Column(Float)  # % of edge cases covered
    accuracy_score = Column(Float)  # Estimate accuracy vs actual

    # Timing
    ai_generation_time_ms = Column(Integer)
    human_review_time_ms = Column(Integer)

    created_at = Column(DateTime, default=datetime.utcnow)
```

### 2. Task Decomposition Service

```python
# services/task_decomposition_service.py
from typing import List, Dict, Optional
import json

class TaskDecompositionService:
    """AI-powered user story decomposition"""

    def __init__(self, ai_gateway: AIGateway, db: Session):
        self.ai = ai_gateway
        self.db = db
        self.context_engine = ContextEngine()

    async def decompose_user_story(
        self,
        user_story: UserStory,
        project_id: str,
        options: DecompositionOptions = None
    ) -> DecompositionResult:
        """Decompose user story into tasks using AI"""

        start_time = time.time()

        # 1. Build context
        context = await self._build_decomposition_context(
            user_story=user_story,
            project_id=project_id
        )

        # 2. Generate decomposition prompt
        prompt = self._build_decomposition_prompt(user_story, context, options)

        # 3. Call AI
        ai_response = await self.ai.complete(
            prompt=prompt,
            context={"stage": "task_decomposition"},
            use_cache=False  # Each decomposition should be fresh
        )

        # 4. Parse AI response
        tasks = self._parse_ai_response(ai_response["response"])

        # 5. Validate and enhance
        tasks = await self._validate_and_enhance(tasks, context)

        # 6. Calculate completeness score
        completeness = self._calculate_completeness(tasks, user_story)

        # 7. Store session
        session = await self._store_session(
            user_story_id=user_story.id,
            project_id=project_id,
            tasks=tasks,
            ai_response=ai_response,
            generation_time_ms=int((time.time() - start_time) * 1000)
        )

        return DecompositionResult(
            session_id=session.id,
            tasks=tasks,
            completeness_score=completeness,
            ai_provider=ai_response["provider"],
            generation_time_ms=session.ai_generation_time_ms
        )

    async def _build_decomposition_context(
        self,
        user_story: UserStory,
        project_id: str
    ) -> Dict:
        """Build rich context for decomposition"""

        project = await self._get_project(project_id)

        return {
            "project": {
                "name": project.name,
                "tech_stack": project.tech_stack,
                "team_size": project.team_size,
                "current_stage": project.current_stage
            },
            "existing_components": await self._get_project_components(project_id),
            "team_velocity": await self._get_team_velocity(project_id),
            "similar_stories": await self._find_similar_stories(user_story, project_id),
            "sdlc_stage_requirements": await self._get_stage_requirements(
                project_id,
                project.current_stage
            )
        }

    def _build_decomposition_prompt(
        self,
        user_story: UserStory,
        context: Dict,
        options: Optional[DecompositionOptions]
    ) -> str:
        """Build AI prompt for decomposition"""

        return f"""
Bạn là AI Assistant giúp PM decompose user story thành tasks.

## User Story
**Title**: {user_story.title}
**Description**: {user_story.description}
**As a**: {user_story.as_a}
**I want**: {user_story.i_want}
**So that**: {user_story.so_that}

## Project Context
- **Tech Stack**: {', '.join(context['project']['tech_stack'])}
- **Team Size**: {context['project']['team_size']} người
- **Current Stage**: {context['project']['current_stage']}
- **Average Velocity**: {context['team_velocity']} story points/sprint

## Existing Components
{json.dumps(context['existing_components'], indent=2)}

## Similar Stories (Reference)
{self._format_similar_stories(context['similar_stories'])}

## Your Task
Decompose user story trên thành danh sách tasks. Mỗi task phải có:

1. **title**: Tiêu đề ngắn gọn (max 100 chars)
2. **description**: Mô tả chi tiết công việc
3. **task_type**: feature | bug | chore | spike
4. **estimated_hours**: Số giờ ước tính (1-40)
5. **complexity**: trivial | simple | medium | complex
6. **acceptance_criteria**: Danh sách tiêu chí nghiệm thu (testable)
7. **affected_components**: Components bị ảnh hưởng
8. **suggested_role**: backend | frontend | fullstack | qa | devops
9. **depends_on**: Index của tasks phụ thuộc (nếu có)

## Quality Checklist
Đảm bảo decomposition bao gồm:
- [ ] Happy path implementation
- [ ] Error handling và edge cases
- [ ] Input validation
- [ ] Unit tests
- [ ] Integration tests (nếu cần)
- [ ] Documentation update (nếu cần)
- [ ] Security considerations (nếu có user data)
- [ ] Performance considerations (nếu có scale concern)

## Output Format
Trả về JSON array với format sau:
```json
[
  {{
    "title": "...",
    "description": "...",
    "task_type": "feature",
    "estimated_hours": 4,
    "complexity": "medium",
    "acceptance_criteria": [
      {{"id": "AC1", "description": "...", "testable": true}}
    ],
    "affected_components": ["auth-service"],
    "suggested_role": "backend",
    "depends_on": []
  }}
]
```

Hãy decompose chi tiết và đầy đủ như một Senior Tech Lead có 10+ năm kinh nghiệm.
"""

    def _parse_ai_response(self, response: str) -> List[Dict]:
        """Parse AI response into structured tasks"""

        # Extract JSON from response
        json_match = re.search(r'\[[\s\S]*\]', response)
        if not json_match:
            raise AIResponseParseError("No JSON array found in response")

        try:
            tasks = json.loads(json_match.group())
        except json.JSONDecodeError as e:
            raise AIResponseParseError(f"Invalid JSON: {e}")

        # Validate required fields
        required_fields = ["title", "task_type", "estimated_hours"]
        for i, task in enumerate(tasks):
            for field in required_fields:
                if field not in task:
                    raise AIResponseParseError(f"Task {i} missing field: {field}")

        return tasks

    async def _validate_and_enhance(
        self,
        tasks: List[Dict],
        context: Dict
    ) -> List[Dict]:
        """Validate and enhance AI-generated tasks"""

        enhanced = []
        for i, task in enumerate(tasks):
            # Add default values
            task.setdefault("priority", "P2")
            task.setdefault("confidence_score", 0.8)

            # Validate estimates against team velocity
            if task["estimated_hours"] > 40:
                task["warnings"] = task.get("warnings", [])
                task["warnings"].append("Task > 40h, consider breaking down further")

            # Check component validity
            valid_components = context.get("existing_components", [])
            for comp in task.get("affected_components", []):
                if comp not in [c["name"] for c in valid_components]:
                    task.setdefault("warnings", [])
                    task["warnings"].append(f"Unknown component: {comp}")

            # Add index for dependency resolution
            task["index"] = i

            enhanced.append(task)

        return enhanced

    def _calculate_completeness(
        self,
        tasks: List[Dict],
        user_story: UserStory
    ) -> float:
        """Calculate decomposition completeness score"""

        checklist = {
            "has_main_feature": False,
            "has_error_handling": False,
            "has_validation": False,
            "has_tests": False,
            "has_documentation": False
        }

        for task in tasks:
            title_lower = task["title"].lower()
            desc_lower = task.get("description", "").lower()
            combined = title_lower + " " + desc_lower

            if any(kw in combined for kw in ["implement", "create", "add", "build"]):
                checklist["has_main_feature"] = True
            if any(kw in combined for kw in ["error", "exception", "handle", "fallback"]):
                checklist["has_error_handling"] = True
            if any(kw in combined for kw in ["validate", "validation", "check"]):
                checklist["has_validation"] = True
            if any(kw in combined for kw in ["test", "unit test", "integration"]):
                checklist["has_tests"] = True
            if any(kw in combined for kw in ["document", "readme", "api doc"]):
                checklist["has_documentation"] = True

        completed = sum(1 for v in checklist.values() if v)
        return completed / len(checklist)
```

### 3. API Endpoints

```python
# api/routes/decomposition.py
from fastapi import APIRouter, Depends, BackgroundTasks

router = APIRouter(prefix="/api/v1/decomposition", tags=["Task Decomposition"])

@router.post("/decompose")
async def decompose_user_story(
    request: DecomposeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> DecompositionResponse:
    """Decompose a user story into tasks using AI"""

    service = TaskDecompositionService(
        ai_gateway=get_ai_gateway(),
        db=db
    )

    result = await service.decompose_user_story(
        user_story=request.user_story,
        project_id=request.project_id,
        options=request.options
    )

    # Store tasks in background
    background_tasks.add_task(
        store_decomposed_tasks,
        session_id=result.session_id,
        tasks=result.tasks,
        db=db
    )

    return result

@router.post("/sessions/{session_id}/approve")
async def approve_decomposition(
    session_id: str,
    request: ApproveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ApprovalResponse:
    """Approve decomposed tasks (with optional modifications)"""

    service = TaskDecompositionService(
        ai_gateway=get_ai_gateway(),
        db=db
    )

    result = await service.approve_session(
        session_id=session_id,
        approved_tasks=request.approved_task_ids,
        modified_tasks=request.modified_tasks,
        rejected_tasks=request.rejected_task_ids,
        reviewer_id=current_user.id,
        review_notes=request.notes
    )

    return result

@router.get("/sessions/{session_id}/export")
async def export_to_github(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ExportResponse:
    """Export approved tasks to GitHub Issues"""

    service = TaskDecompositionService(
        ai_gateway=get_ai_gateway(),
        db=db
    )

    # Get approved tasks
    tasks = await service.get_approved_tasks(session_id)

    # Export to GitHub
    github_issues = await export_tasks_to_github(
        tasks=tasks,
        project_id=request.project_id,
        user=current_user
    )

    return ExportResponse(
        exported_count=len(github_issues),
        github_issues=github_issues
    )
```

---

## Consequences

### Positive

1. **PM Productivity**: 30-45 min → 2 min decomposition time
2. **Consistency**: Same quality regardless of PM experience
3. **Completeness**: AI checklist catches missing edge cases
4. **Learning**: System improves from human feedback

### Negative

1. **AI Dependency**: Risk if AI service unavailable
2. **Over-reliance**: PMs may stop thinking critically
3. **Context Limitations**: AI may miss domain-specific nuances

### Risks

1. **Hallucination**: AI may suggest non-existent components
   - **Mitigation**: Validate against known component list

2. **Estimate Accuracy**: AI estimates may be off
   - **Mitigation**: Calibrate with historical team velocity

---

## Approval

| Role | Name | Decision | Date | Comment |
|------|------|----------|------|---------|
| **CTO** | [CTO Name] | ✅ APPROVED | Dec 3, 2025 | Leverages AI for productivity |
| **CPO** | [CPO Name] | ✅ APPROVED | Dec 3, 2025 | Key PM productivity feature |

---

**Decision**: **APPROVED** - AI Task Decomposition Service

**Priority**: **HIGH** - Core AI Governance feature

**Timeline**: Sprint 29 (AI Governance & Docs)
