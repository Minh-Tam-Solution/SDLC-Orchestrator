# ADR-013: 4-Level Planning Hierarchy

**Status**: APPROVED
**Date**: December 3, 2025
**Decision Makers**: CTO, CPO (joint review)
**Stage**: Stage 02 (HOW - Design & Architecture)
**Framework**: SDLC 6.1.0

---

## Context

SDLC Orchestrator cần quản lý planning ở nhiều cấp độ khác nhau để hỗ trợ:

1. **Strategic Planning**: Vision dài hạn (1-3 năm)
2. **Tactical Planning**: Quarterly objectives
3. **Operational Planning**: Weekly sprints
4. **Execution Planning**: Daily tasks

**Current Problem**:
- Không có cấu trúc rõ ràng từ Vision → Task
- Khó trace ngược từ code commit → business value
- PM thiếu framework để communicate planning với stakeholders

---

## Decision

Implement **4-Level Planning Hierarchy**:

```
┌─────────────────────────────────────────────────────────────────┐
│ LEVEL 1: ROADMAP (Vision - 1-3 years)                          │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ LEVEL 2: PHASE (Quarter - 3 months)                         │ │
│ │ ┌─────────────────────────────────────────────────────────┐ │ │
│ │ │ LEVEL 3: SPRINT (Week - 1-2 weeks)                      │ │ │
│ │ │ ┌─────────────────────────────────────────────────────┐ │ │ │
│ │ │ │ LEVEL 4: BACKLOG (Day - Tasks/Issues)               │ │ │ │
│ │ │ └─────────────────────────────────────────────────────┘ │ │ │
│ │ └─────────────────────────────────────────────────────────┘ │ │
│ └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Level Details

```yaml
Level 1 - Roadmap:
  Timeframe: 1-3 years
  Owner: CEO/CPO
  Content:
    - Product vision statement
    - Major milestones
    - Strategic themes
    - Success metrics (OKRs)
  Review Cycle: Quarterly
  Document: PRODUCT-ROADMAP-vX.X.X.md

Level 2 - Phase:
  Timeframe: 1 quarter (3 months)
  Owner: CPO/PM
  Content:
    - Phase objectives
    - Key deliverables
    - Resource allocation
    - Risk assessment
    - SDLC Gates to pass
  Review Cycle: Monthly
  Document: PHASE-XX-{name}.md

Level 3 - Sprint:
  Timeframe: 1-2 weeks
  Owner: Tech Lead/Scrum Master
  Content:
    - Sprint goals
    - User stories
    - Technical tasks
    - Definition of Done
    - Burndown targets
  Review Cycle: Daily standup, Sprint review
  Document: SPRINT-XX-{name}.md

Level 4 - Backlog:
  Timeframe: Daily
  Owner: Individual contributors
  Content:
    - Tasks (from decomposition)
    - Bugs
    - Tech debt items
    - Acceptance criteria
    - Time estimates
  Review Cycle: Daily
  Source: GitHub Issues (synced)
```

---

## Architecture Design

### 1. Data Model

```python
# models/planning.py
from sqlalchemy import Column, String, Integer, Date, JSON, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

class Roadmap(Base):
    """Product roadmap (Level 1)"""
    __tablename__ = "roadmaps"

    id = Column(UUID, primary_key=True, default=uuid4)
    project_id = Column(UUID, ForeignKey("projects.id"), nullable=False)

    # Version
    version = Column(String(20), nullable=False)  # e.g., "3.0.0"
    status = Column(String(20), default="draft")  # draft, active, archived

    # Content
    vision_statement = Column(Text)
    timeframe_start = Column(Date)
    timeframe_end = Column(Date)
    strategic_themes = Column(JSON)  # ["AI Governance", "Enterprise Scale"]
    success_metrics = Column(JSON)  # OKRs

    # Relationships
    phases = relationship("Phase", back_populates="roadmap")

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(UUID, ForeignKey("users.id"))
    approved_at = Column(DateTime)
    approved_by = Column(UUID, ForeignKey("users.id"))


class Phase(Base):
    """Quarterly phase (Level 2)"""
    __tablename__ = "phases"

    id = Column(UUID, primary_key=True, default=uuid4)
    roadmap_id = Column(UUID, ForeignKey("roadmaps.id"), nullable=False)
    project_id = Column(UUID, ForeignKey("projects.id"), nullable=False)

    # Identity
    phase_number = Column(Integer, nullable=False)  # 1, 2, 3, 4
    name = Column(String(100), nullable=False)  # "MVP Launch"
    quarter = Column(String(10))  # "Q1-2026"

    # Timeline
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    status = Column(String(20), default="planned")  # planned, active, completed

    # Content
    objectives = Column(JSON)  # List of phase objectives
    key_deliverables = Column(JSON)  # List of deliverables
    resource_allocation = Column(JSON)  # Team assignments
    risk_assessment = Column(JSON)  # Identified risks

    # SDLC Integration
    target_gates = Column(JSON)  # ["G2", "G3"] gates to pass
    sdlc_stages = Column(JSON)  # Stages covered in this phase

    # Metrics
    planned_velocity = Column(Integer)
    actual_velocity = Column(Integer)

    # Relationships
    roadmap = relationship("Roadmap", back_populates="phases")
    sprints = relationship("Sprint", back_populates="phase")

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)


class Sprint(Base):
    """Sprint/iteration (Level 3)"""
    __tablename__ = "sprints"

    id = Column(UUID, primary_key=True, default=uuid4)
    phase_id = Column(UUID, ForeignKey("phases.id"))
    project_id = Column(UUID, ForeignKey("projects.id"), nullable=False)

    # Identity
    sprint_number = Column(Integer, nullable=False)  # 22, 23, 24...
    name = Column(String(100))  # "Operations & Monitoring"

    # Timeline
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    status = Column(String(20), default="planned")

    # Goals
    sprint_goals = Column(JSON)  # List of sprint goals
    definition_of_done = Column(JSON)

    # Metrics
    planned_points = Column(Integer)
    completed_points = Column(Integer)
    burndown_data = Column(JSON)  # Daily burndown

    # Relationships
    phase = relationship("Phase", back_populates="sprints")
    backlog_items = relationship("BacklogItem", back_populates="sprint")

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)


class BacklogItem(Base):
    """Backlog item/task (Level 4)"""
    __tablename__ = "backlog_items"

    id = Column(UUID, primary_key=True, default=uuid4)
    sprint_id = Column(UUID, ForeignKey("sprints.id"))
    project_id = Column(UUID, ForeignKey("projects.id"), nullable=False)

    # External reference (GitHub sync)
    github_issue_id = Column(Integer)
    github_issue_url = Column(String(500))

    # Identity
    title = Column(String(200), nullable=False)
    description = Column(Text)
    item_type = Column(String(20))  # user_story, task, bug, tech_debt, spike

    # Priority & Status
    priority = Column(String(10))  # P0, P1, P2, P3
    status = Column(String(20), default="backlog")  # backlog, todo, in_progress, review, done
    labels = Column(JSON)

    # Estimates
    story_points = Column(Integer)
    estimated_hours = Column(Integer)
    actual_hours = Column(Integer)

    # Assignment
    assignee_id = Column(UUID, ForeignKey("users.id"))

    # Acceptance criteria
    acceptance_criteria = Column(JSON)

    # Traceability
    user_story_id = Column(UUID, ForeignKey("user_stories.id"))
    decomposition_session_id = Column(UUID, ForeignKey("decomposition_sessions.id"))

    # Relationships
    sprint = relationship("Sprint", back_populates="backlog_items")

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
```

### 2. Planning Service

```python
# services/planning_service.py
from typing import List, Dict, Optional

class PlanningService:
    """Manage 4-level planning hierarchy"""

    def __init__(self, db: Session):
        self.db = db
        self.github_sync = GitHubSyncService()

    async def get_planning_hierarchy(
        self,
        project_id: str,
        include_backlog: bool = True
    ) -> PlanningHierarchy:
        """Get complete planning hierarchy for a project"""

        # Get active roadmap
        roadmap = await self._get_active_roadmap(project_id)
        if not roadmap:
            return PlanningHierarchy(project_id=project_id, roadmap=None)

        # Get phases
        phases = await self._get_phases(roadmap.id)

        # Get sprints for each phase
        for phase in phases:
            phase.sprints = await self._get_sprints(phase.id)

            # Get backlog for each sprint
            if include_backlog:
                for sprint in phase.sprints:
                    sprint.backlog_items = await self._get_backlog_items(sprint.id)

        return PlanningHierarchy(
            project_id=project_id,
            roadmap=roadmap,
            phases=phases,
            current_phase=self._get_current_phase(phases),
            current_sprint=self._get_current_sprint(phases)
        )

    async def get_traceability_chain(
        self,
        backlog_item_id: str
    ) -> TraceabilityChain:
        """
        Get full traceability from backlog item to roadmap vision.

        Returns chain: Backlog → Sprint → Phase → Roadmap → Vision
        """

        item = await self._get_backlog_item(backlog_item_id)
        if not item:
            raise NotFoundError(f"Backlog item {backlog_item_id} not found")

        chain = TraceabilityChain(backlog_item=item)

        # Get sprint
        if item.sprint_id:
            sprint = await self._get_sprint(item.sprint_id)
            chain.sprint = sprint

            # Get phase
            if sprint.phase_id:
                phase = await self._get_phase(sprint.phase_id)
                chain.phase = phase

                # Get roadmap
                if phase.roadmap_id:
                    roadmap = await self._get_roadmap(phase.roadmap_id)
                    chain.roadmap = roadmap
                    chain.vision = roadmap.vision_statement

        # Calculate alignment score
        chain.alignment_score = self._calculate_alignment(chain)

        return chain

    def _calculate_alignment(self, chain: TraceabilityChain) -> float:
        """Calculate how well backlog item aligns with roadmap vision"""

        if not chain.roadmap:
            return 0.0

        score = 0.0

        # Check if item contributes to phase objectives
        if chain.phase and chain.backlog_item.labels:
            phase_themes = chain.phase.objectives or []
            item_labels = chain.backlog_item.labels or []

            # Simple keyword matching
            matching = sum(1 for theme in phase_themes
                         if any(label in theme.lower() for label in item_labels))
            if phase_themes:
                score += (matching / len(phase_themes)) * 0.5

        # Check if sprint goal is met
        if chain.sprint and chain.sprint.sprint_goals:
            score += 0.3  # Assume aligned if in sprint

        # Bonus for having acceptance criteria
        if chain.backlog_item.acceptance_criteria:
            score += 0.2

        return min(score, 1.0)

    async def sync_backlog_from_github(
        self,
        project_id: str,
        sprint_id: str
    ) -> SyncResult:
        """
        Sync backlog items from GitHub Issues.

        Note: Bridge pattern - READ ONLY from GitHub, don't create issues.
        """

        project = await self._get_project(project_id)
        sprint = await self._get_sprint(sprint_id)

        # Get GitHub issues with sprint label
        sprint_label = f"sprint-{sprint.sprint_number}"
        issues = await self.github_sync.get_issues(
            repo=project.github_repo,
            labels=[sprint_label],
            state="all"
        )

        synced = []
        for issue in issues:
            # Check if already exists
            existing = await self._get_backlog_by_github_id(issue.number)

            if existing:
                # Update existing
                await self._update_backlog_from_issue(existing, issue)
                synced.append({"action": "updated", "issue": issue.number})
            else:
                # Create new
                item = await self._create_backlog_from_issue(
                    issue=issue,
                    sprint_id=sprint_id,
                    project_id=project_id
                )
                synced.append({"action": "created", "issue": issue.number})

        return SyncResult(
            synced_count=len(synced),
            items=synced
        )
```

### 3. API Endpoints

```python
# api/routes/planning.py
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/api/v1/planning", tags=["Planning"])

@router.get("/hierarchy")
async def get_planning_hierarchy(
    project_id: str = Query(...),
    include_backlog: bool = Query(True),
    db: Session = Depends(get_db)
) -> PlanningHierarchyResponse:
    """Get complete 4-level planning hierarchy"""

    service = PlanningService(db)
    hierarchy = await service.get_planning_hierarchy(
        project_id=project_id,
        include_backlog=include_backlog
    )

    return hierarchy

@router.get("/traceability/{backlog_item_id}")
async def get_traceability(
    backlog_item_id: str,
    db: Session = Depends(get_db)
) -> TraceabilityResponse:
    """Get traceability chain from backlog to vision"""

    service = PlanningService(db)
    chain = await service.get_traceability_chain(backlog_item_id)

    return TraceabilityResponse(
        chain=chain,
        visualization=generate_traceability_visualization(chain)
    )

@router.post("/sprints/{sprint_id}/sync-github")
async def sync_sprint_from_github(
    sprint_id: str,
    project_id: str = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> SyncResponse:
    """Sync backlog items from GitHub Issues"""

    service = PlanningService(db)
    result = await service.sync_backlog_from_github(
        project_id=project_id,
        sprint_id=sprint_id
    )

    return result

@router.get("/roadmap/export")
async def export_roadmap(
    project_id: str = Query(...),
    format: str = Query("markdown"),  # markdown, json, pdf
    db: Session = Depends(get_db)
) -> ExportResponse:
    """Export roadmap in various formats"""

    service = PlanningService(db)
    hierarchy = await service.get_planning_hierarchy(project_id)

    if format == "markdown":
        content = generate_roadmap_markdown(hierarchy)
        return ExportResponse(
            content=content,
            filename=f"PRODUCT-ROADMAP-v{hierarchy.roadmap.version}.md"
        )
    elif format == "json":
        return ExportResponse(
            content=hierarchy.dict(),
            filename="roadmap.json"
        )
```

---

## Traceability Visualization

```
┌─────────────────────────────────────────────────────────────────┐
│ TRACEABILITY: Backlog Item → Vision                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  📋 Task: "Implement JWT refresh token rotation"                │
│     └─ Sprint 23: Security & Performance                        │
│        └─ Phase 01: MVP Launch (Q4-2025)                        │
│           └─ Roadmap v3.0.0: "Enterprise-Grade Platform"        │
│              └─ Vision: "First Governance-First Platform"       │
│                                                                  │
│  Alignment Score: 92% ████████████░░ (Strong)                   │
│                                                                  │
│  Contributing to:                                               │
│  ✓ Phase Objective: "Security Baseline OWASP ASVS L2"          │
│  ✓ Sprint Goal: "JWT + MFA implementation"                      │
│  ✓ Gate: G3 (Ship Ready)                                        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Consequences

### Positive

1. **Clear Structure**: 4-level hierarchy provides clarity for all stakeholders
2. **Traceability**: Every task traces back to business value
3. **Alignment**: Team understands how daily work contributes to vision
4. **Communication**: PM can present planning at appropriate level for audience

### Negative

1. **Overhead**: Maintaining 4 levels requires discipline
2. **Rigidity**: May feel bureaucratic for small teams
3. **Sync Complexity**: Keeping GitHub and Orchestrator in sync

### Risks

1. **Orphan Tasks**: Tasks not linked to sprint/phase
   - **Mitigation**: Validation rules, dashboard warnings

2. **Stale Planning**: Roadmap not updated with reality
   - **Mitigation**: Quarterly review process, progress tracking

---

## Approval

| Role | Name | Decision | Date | Comment |
|------|------|----------|------|---------|
| **CTO** | [CTO Name] | ✅ APPROVED | Dec 3, 2025 | Essential for governance |
| **CPO** | [CPO Name] | ✅ APPROVED | Dec 3, 2025 | Improves strategic alignment |

---

**Decision**: **APPROVED** - 4-Level Planning Hierarchy

**Priority**: **HIGH** - Core planning framework

**Timeline**: Sprint 29 (AI Governance & Docs)
