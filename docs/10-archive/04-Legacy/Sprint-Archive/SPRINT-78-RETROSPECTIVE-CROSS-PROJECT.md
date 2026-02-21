# Sprint 78: Sprint Retrospective Automation & Cross-Project Coordination

**Sprint ID:** S78
**Status:** 🆕 PLANNED
**Duration:** 5 days (February 10-14, 2026)
**Goal:** Complete Sprint Analytics Foundation + Cross-Project Sprint Dependencies
**Story Points:** 36 SP
**Framework Reference:** SDLC 6.1.0 P2 (Sprint Planning Governance)
**Prerequisite:** Sprint 77 ✅ (AI Council Sprint Integration)

---

## 🎯 Sprint 78 Objectives

### Primary Goals (P0)

1. **Sprint Retrospective Automation** - Auto-generate retrospective insights from sprint data
2. **Cross-Project Sprint Dependencies** - Track and visualize dependencies between projects
3. **Resource Allocation Optimization** - Team capacity planning across sprints

### Secondary Goals (P1)

4. **Sprint Template Library** - Reusable sprint configurations
5. **Sprint Health Monitoring** - Real-time alerts for at-risk sprints
6. **Performance Optimization** - Query caching for analytics

---

## ✅ Sprint 77 Handoff

### Expected Completion (Sprint 77)

| Feature | Status | Tests |
|---------|--------|-------|
| AI Council sprint integration | ✅ Expected | 10 |
| Burndown charts | ✅ Expected | 8 |
| Sprint forecasting | ✅ Expected | 8 |
| Retrospective foundation | ✅ Expected | 6 |

### Sprint 78 Build-Upon

Sprint 78 completes the **Sprint Analytics Suite** started in Sprint 77:
- Sprint 77: Burndown, Forecast, Retro Foundation
- Sprint 78: Cross-Project, Templates, Health Monitoring

---

## 📋 Sprint 78 Backlog

### Day 1: Retrospective Enhancement (8 SP)

| Task | Owner | Est | Priority | Status |
|------|-------|-----|----------|--------|
| Enhanced retro metrics calculation | Backend | 2h | P0 | ⏳ |
| Action item tracking system | Backend | 3h | P0 | ⏳ |
| Retrospective comparison (sprint-over-sprint) | Backend | 2h | P1 | ⏳ |
| Integration tests (8 tests) | Backend | 2h | P0 | ⏳ |

**Implementation:**

```python
# backend/app/services/retrospective_service.py (Enhanced)
class RetrospectiveService:
    """Enhanced retrospective with action item tracking."""
    
    async def create_action_items(
        self,
        sprint_id: UUID,
        insights: List[RetroInsight],
    ) -> List[RetroActionItem]:
        """
        Create trackable action items from retrospective insights.
        
        Action items can be:
        - Assigned to team members
        - Tracked across sprints
        - Marked as complete/incomplete
        - Referenced in future retros
        """
        action_items = []
        
        for insight in insights:
            if insight.category == "needs_improvement":
                # Generate action item
                action = RetroActionItem(
                    sprint_id=sprint_id,
                    title=f"Address: {insight.title}",
                    description=insight.description,
                    category=insight.category,
                    priority=self._calculate_priority(insight),
                    status="open",
                    created_at=datetime.utcnow(),
                )
                action_items.append(action)
        
        return action_items
    
    async def compare_retrospectives(
        self,
        sprint_id: UUID,
        previous_sprint_id: Optional[UUID] = None,
    ) -> RetroComparison:
        """
        Compare current sprint retrospective with previous sprint.
        
        Shows:
        - Metrics improvement/decline
        - Action items from previous sprint
        - Recurring issues
        """
        current = await self.generate_retrospective(sprint_id)
        
        if not previous_sprint_id:
            # Get previous sprint automatically
            sprint = await self.sprint_repo.get(sprint_id)
            previous = await self.sprint_repo.get_previous(
                project_id=sprint.project_id,
                sprint_number=sprint.number - 1,
            )
            previous_sprint_id = previous.id if previous else None
        
        if previous_sprint_id:
            previous_retro = await self.generate_retrospective(previous_sprint_id)
            
            return RetroComparison(
                current=current,
                previous=previous_retro,
                metrics_delta=self._calculate_metrics_delta(current, previous_retro),
                action_items_completed=await self._get_completed_actions(previous_sprint_id),
                recurring_issues=self._identify_recurring_issues(current, previous_retro),
            )
        
        return RetroComparison(current=current, previous=None)

class RetroActionItem(BaseModel):
    """Trackable action item from retrospective."""
    id: UUID
    sprint_id: UUID
    title: str
    description: str
    category: str
    priority: str  # low, medium, high
    status: str  # open, in_progress, completed, cancelled
    assignee_id: Optional[UUID] = None
    due_sprint_id: Optional[UUID] = None  # Target sprint for completion
    created_at: datetime
    completed_at: Optional[datetime] = None
```

### Day 2: Cross-Project Sprint Dependencies (8 SP)

| Task | Owner | Est | Priority | Status |
|------|-------|-----|----------|--------|
| Create `SprintDependency` model | Backend | 2h | P0 | ⏳ |
| Dependency CRUD API | Backend | 3h | P0 | ⏳ |
| Dependency graph visualization data | Backend | 2h | P0 | ⏳ |
| Integration tests (8 tests) | Backend | 2h | P0 | ⏳ |

**Implementation:**

```python
# backend/app/models/sprint_dependency.py
class SprintDependency(Base):
    """
    Sprint-to-sprint dependencies across projects.
    
    Use cases:
    - Project A sprint depends on Project B feature
    - Shared resource allocation
    - Cross-team collaboration tracking
    """
    __tablename__ = "sprint_dependencies"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_sprint_id = Column(UUID(as_uuid=True), ForeignKey("sprints.id"), nullable=False)
    target_sprint_id = Column(UUID(as_uuid=True), ForeignKey("sprints.id"), nullable=False)
    
    dependency_type = Column(String, nullable=False)  # blocks, requires, related
    description = Column(Text)
    
    status = Column(String, default="pending")  # pending, active, resolved, cancelled
    
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    
    # Relationships
    source_sprint = relationship("Sprint", foreign_keys=[source_sprint_id])
    target_sprint = relationship("Sprint", foreign_keys=[target_sprint_id])
    created_by = relationship("User")

# backend/app/services/sprint_dependency_service.py
class SprintDependencyService:
    """Manage cross-project sprint dependencies."""
    
    async def create_dependency(
        self,
        source_sprint_id: UUID,
        target_sprint_id: UUID,
        dependency_type: str,
        description: str,
        user_id: UUID,
    ) -> SprintDependency:
        """
        Create dependency between sprints.
        
        Validation:
        - No circular dependencies
        - Both sprints exist and accessible
        - User has permission
        """
        # Validate no circular dependency
        if await self._has_circular_dependency(source_sprint_id, target_sprint_id):
            raise ValueError("Circular dependency detected")
        
        dependency = SprintDependency(
            source_sprint_id=source_sprint_id,
            target_sprint_id=target_sprint_id,
            dependency_type=dependency_type,
            description=description,
            created_by_id=user_id,
            status="active" if dependency_type == "blocks" else "pending",
        )
        
        self.db.add(dependency)
        await self.db.commit()
        
        return dependency
    
    async def get_dependency_graph(
        self,
        project_id: UUID,
    ) -> DependencyGraph:
        """
        Get dependency graph for all sprints in a project.
        
        Returns graph data suitable for visualization:
        - Nodes: Sprints
        - Edges: Dependencies
        - Metadata: Status, type, blocking info
        """
        sprints = await self.sprint_repo.get_by_project(project_id)
        dependencies = await self.dependency_repo.get_by_sprints(
            [s.id for s in sprints]
        )
        
        nodes = [
            DependencyNode(
                id=str(sprint.id),
                label=f"Sprint {sprint.number}",
                status=sprint.status,
                project_id=str(sprint.project_id),
            )
            for sprint in sprints
        ]
        
        edges = [
            DependencyEdge(
                source=str(dep.source_sprint_id),
                target=str(dep.target_sprint_id),
                type=dep.dependency_type,
                status=dep.status,
            )
            for dep in dependencies
        ]
        
        return DependencyGraph(nodes=nodes, edges=edges)
    
    async def _has_circular_dependency(
        self,
        source_id: UUID,
        target_id: UUID,
    ) -> bool:
        """Check if adding dependency would create cycle."""
        # BFS to detect cycle
        visited = set()
        queue = [target_id]
        
        while queue:
            current = queue.pop(0)
            if current == source_id:
                return True
            
            if current in visited:
                continue
            
            visited.add(current)
            
            # Get dependencies where current is target
            deps = await self.dependency_repo.get_by_target(current)
            queue.extend([d.source_sprint_id for d in deps])
        
        return False
```

### Day 3: Resource Allocation Optimization (8 SP)

| Task | Owner | Est | Priority | Status |
|------|-------|-----|----------|--------|
| Create `ResourceAllocation` model | Backend | 2h | P0 | ⏳ |
| Team capacity calculation | Backend | 3h | P0 | ⏳ |
| Allocation conflict detection | Backend | 2h | P1 | ⏳ |
| Integration tests (6 tests) | Backend | 2h | P0 | ⏳ |

**Implementation:**

```python
# backend/app/models/resource_allocation.py
class ResourceAllocation(Base):
    """
    Team member allocation across sprints.
    
    Tracks:
    - Who is allocated to which sprint
    - Allocation percentage (0-100%)
    - Capacity vs. load
    """
    __tablename__ = "resource_allocations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sprint_id = Column(UUID(as_uuid=True), ForeignKey("sprints.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    allocation_percentage = Column(Integer, default=100)  # 0-100%
    role = Column(String)  # developer, qa, designer, pm
    
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    sprint = relationship("Sprint")
    user = relationship("User")

# backend/app/services/resource_allocation_service.py
class ResourceAllocationService:
    """Optimize resource allocation across sprints."""
    
    async def calculate_team_capacity(
        self,
        team_id: UUID,
        start_date: date,
        end_date: date,
    ) -> TeamCapacity:
        """
        Calculate team capacity for date range.
        
        Considers:
        - Team member count
        - Working days (exclude weekends, holidays)
        - Existing allocations to other sprints
        """
        members = await self.team_repo.get_members(team_id)
        working_days = self._count_working_days(start_date, end_date)
        
        total_capacity = 0
        allocated_capacity = 0
        
        for member in members:
            # Each member has N working days
            member_capacity = working_days * 8  # 8 hours per day
            total_capacity += member_capacity
            
            # Get existing allocations
            allocations = await self.allocation_repo.get_by_user_and_dates(
                user_id=member.user_id,
                start_date=start_date,
                end_date=end_date,
            )
            
            allocated = sum(
                a.allocation_percentage / 100 * member_capacity
                for a in allocations
            )
            allocated_capacity += allocated
        
        return TeamCapacity(
            team_id=team_id,
            total_hours=total_capacity,
            allocated_hours=allocated_capacity,
            available_hours=total_capacity - allocated_capacity,
            utilization_rate=allocated_capacity / total_capacity if total_capacity > 0 else 0,
        )
    
    async def detect_conflicts(
        self,
        user_id: UUID,
        sprint_id: UUID,
        allocation_percentage: int,
    ) -> List[AllocationConflict]:
        """
        Detect if user allocation exceeds 100% for any time period.
        """
        sprint = await self.sprint_repo.get(sprint_id)
        
        # Get existing allocations for user in same time period
        existing = await self.allocation_repo.get_by_user_and_dates(
            user_id=user_id,
            start_date=sprint.start_date,
            end_date=sprint.end_date,
        )
        
        conflicts = []
        
        for alloc in existing:
            total_allocation = allocation_percentage + alloc.allocation_percentage
            
            if total_allocation > 100:
                conflicts.append(AllocationConflict(
                    user_id=user_id,
                    conflicting_sprint_id=alloc.sprint_id,
                    total_percentage=total_allocation,
                    message=f"User over-allocated: {total_allocation}%",
                ))
        
        return conflicts
```

### Day 4: Sprint Template Library (6 SP)

| Task | Owner | Est | Priority | Status |
|------|-------|-----|----------|--------|
| Create `SprintTemplate` model | Backend | 2h | P1 | ⏳ |
| Template CRUD API | Backend | 2h | P1 | ⏳ |
| Apply template to new sprint | Backend | 2h | P1 | ⏳ |
| Integration tests (4 tests) | Backend | 1h | P0 | ⏳ |

**Implementation:**

```python
# backend/app/models/sprint_template.py
class SprintTemplate(Base):
    """
    Reusable sprint configuration template.
    
    Use cases:
    - 2-week standard sprint template
    - Feature sprint template
    - Bug-fix sprint template
    - Release sprint template
    """
    __tablename__ = "sprint_templates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    description = Column(Text)
    
    # Template configuration
    duration_days = Column(Integer, default=10)  # 2 weeks
    default_story_points = Column(Integer, default=40)
    
    # Default backlog structure
    backlog_structure = Column(JSON)  # List of default item types
    
    # Default gate configuration
    gates_enabled = Column(Boolean, default=True)
    
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=True)
    is_public = Column(Boolean, default=False)
    
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

# backend/app/services/sprint_template_service.py
class SprintTemplateService:
    """Manage sprint templates."""
    
    async def apply_template(
        self,
        template_id: UUID,
        project_id: UUID,
        start_date: date,
    ) -> Sprint:
        """
        Create new sprint from template.
        
        Copies:
        - Duration configuration
        - Default backlog structure
        - Gate settings
        """
        template = await self.template_repo.get(template_id)
        
        # Create sprint
        sprint = await self.sprint_service.create_sprint(
            project_id=project_id,
            phase_id=None,  # User selects phase
            start_date=start_date,
            end_date=start_date + timedelta(days=template.duration_days),
            goal=template.name,
        )
        
        # Create default backlog items from template
        if template.backlog_structure:
            for item_template in template.backlog_structure:
                await self.backlog_service.create_item(
                    sprint_id=sprint.id,
                    title=item_template["title"],
                    type=item_template["type"],
                    priority=item_template["priority"],
                    story_points=item_template.get("story_points"),
                )
        
        return sprint
```

### Day 5: Frontend Components & Completion (6 SP)

| Task | Owner | Est | Priority | Status |
|------|-------|-----|----------|--------|
| Retrospective comparison UI | Frontend | 2h | P0 | ⏳ |
| Dependency graph visualization | Frontend | 2h | P0 | ⏳ |
| Resource allocation heatmap | Frontend | 2h | P1 | ⏳ |
| Sprint template selector | Frontend | 1h | P1 | ⏳ |
| Sprint 78 completion docs | PM | 1h | P0 | ⏳ |

**Frontend Components:**

```typescript
// frontend/web/src/components/sprints/RetrospectiveComparison.tsx
interface RetrospectiveComparisonProps {
  sprintId: string;
}

export function RetrospectiveComparison({ sprintId }: RetrospectiveComparisonProps) {
  const { data: comparison } = useRetrospectiveComparison(sprintId);
  
  if (!comparison || !comparison.previous) {
    return <p>No previous sprint for comparison</p>;
  }
  
  return (
    <div className="grid grid-cols-2 gap-4">
      <Card>
        <CardHeader>
          <CardTitle>Previous Sprint {comparison.previous.sprint_number}</CardTitle>
        </CardHeader>
        <CardContent>
          <MetricsDisplay metrics={comparison.previous.metrics} />
        </CardContent>
      </Card>
      
      <Card>
        <CardHeader>
          <CardTitle>Current Sprint {comparison.current.sprint_number}</CardTitle>
        </CardHeader>
        <CardContent>
          <MetricsDisplay metrics={comparison.current.metrics} />
          
          {comparison.metrics_delta && (
            <Alert className="mt-4">
              <TrendingUp className="h-4 w-4" />
              <AlertTitle>Performance Trend</AlertTitle>
              <AlertDescription>
                Completion rate: {comparison.metrics_delta.completion_rate > 0 ? "↑" : "↓"} 
                {Math.abs(comparison.metrics_delta.completion_rate * 100).toFixed(1)}%
              </AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>
      
      <Card className="col-span-2">
        <CardHeader>
          <CardTitle>Action Items from Previous Sprint</CardTitle>
        </CardHeader>
        <CardContent>
          <ActionItemsTracker items={comparison.action_items_completed} />
        </CardContent>
      </Card>
    </div>
  );
}

// frontend/web/src/components/sprints/DependencyGraph.tsx
import ReactFlow from 'reactflow';

export function DependencyGraph({ projectId }: { projectId: string }) {
  const { data: graph } = useDependencyGraph(projectId);
  
  if (!graph) return <Skeleton className="h-96" />;
  
  const nodes = graph.nodes.map(node => ({
    id: node.id,
    data: { label: node.label, status: node.status },
    position: { x: 0, y: 0 }, // Layout calculated by reactflow
    type: 'sprintNode',
  }));
  
  const edges = graph.edges.map(edge => ({
    id: `${edge.source}-${edge.target}`,
    source: edge.source,
    target: edge.target,
    label: edge.type,
    type: edge.type === 'blocks' ? 'blocking' : 'default',
  }));
  
  return (
    <div className="h-96">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        fitView
      />
    </div>
  );
}

// frontend/web/src/components/sprints/ResourceAllocationHeatmap.tsx
export function ResourceAllocationHeatmap({ teamId }: { teamId: string }) {
  const { data: allocation } = useTeamAllocation(teamId);
  
  return (
    <Card>
      <CardHeader>
        <CardTitle>Team Capacity</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <span>Total Capacity</span>
            <span className="font-bold">{allocation.total_hours}h</span>
          </div>
          <div className="flex items-center justify-between">
            <span>Allocated</span>
            <span className="font-bold">{allocation.allocated_hours}h</span>
          </div>
          <div className="flex items-center justify-between">
            <span>Available</span>
            <span className="font-bold text-green-600">{allocation.available_hours}h</span>
          </div>
          
          <Progress value={allocation.utilization_rate * 100} />
          
          {allocation.utilization_rate > 0.9 && (
            <Alert variant="warning">
              <AlertTriangle className="h-4 w-4" />
              <AlertTitle>High Utilization</AlertTitle>
              <AlertDescription>
                Team is at {(allocation.utilization_rate * 100).toFixed(0)}% capacity
              </AlertDescription>
            </Alert>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
```

---

## 🔗 API Endpoints

```yaml
# Sprint 78 New Endpoints

# Retrospective Enhancements
POST /planning/sprints/{sprint_id}/retrospective/action-items:
  summary: Create action items from retrospective
  tags: [Planning, Retrospective]

GET /planning/sprints/{sprint_id}/retrospective/comparison:
  summary: Compare with previous sprint retrospective
  tags: [Planning, Analytics]

# Sprint Dependencies
POST /planning/sprints/dependencies:
  summary: Create dependency between sprints
  tags: [Planning, Dependencies]

GET /planning/projects/{project_id}/dependency-graph:
  summary: Get dependency graph for project
  tags: [Planning, Visualization]

# Resource Allocation
POST /planning/sprints/{sprint_id}/allocations:
  summary: Allocate team member to sprint
  tags: [Planning, Resources]

GET /planning/teams/{team_id}/capacity:
  summary: Get team capacity for date range
  tags: [Planning, Resources]

# Sprint Templates
POST /planning/templates:
  summary: Create sprint template
  tags: [Planning, Templates]

POST /planning/templates/{template_id}/apply:
  summary: Apply template to create new sprint
  tags: [Planning, Templates]
```

---

## 🔒 Definition of Done

### Code Complete

- [ ] Retrospective action item tracking
- [ ] Sprint-to-sprint dependency management
- [ ] Resource allocation optimization
- [ ] Sprint template library
- [ ] Frontend components (comparison, graph, heatmap)

### Tests

- [ ] `pytest backend/tests/integration/test_retrospective_*.py` passes
- [ ] Retrospective tests (8 tests)
- [ ] Dependency tests (8 tests)
- [ ] Allocation tests (6 tests)
- [ ] Template tests (4 tests)
- [ ] Total: 26+ new tests

### Documentation

- [ ] OpenAPI spec updated with new endpoints
- [ ] Cross-project coordination guide
- [ ] Sprint 78 completion report

### Review

- [ ] Code review approved by Tech Lead
- [ ] PR merged to main
- [ ] Staging deployment verified

---

## 📊 Metrics & Success Criteria

| Metric | Target | Notes |
|--------|--------|-------|
| Integration Tests | 26+ | Retrospective + Dependencies + Allocation |
| API Response Time | <200ms p95 | Dependency graph queries |
| Test Coverage | 90%+ | Sprint coordination module |
| Dependency Detection | <1s | Circular dependency check |

---

## 📝 SDLC 6.1.0 Compliance

| Pillar | Sprint 78 Implementation |
|--------|--------------------------|
| P2 (Sprint Planning) | Cross-project coordination, retrospective tracking |
| P6 (Documentation Permanence) | Action item tracking, retrospective comparison |
| P4 (Quality Gates) | Retrospective insights for process improvement |

---

## 🚀 Handoff to Sprint 79

### Expected Completion (Sprint 78)

- ✅ Sprint retrospective automation complete
- ✅ Cross-project dependencies tracked
- ✅ Resource allocation optimization
- ✅ Sprint template library

### Sprint 79 Focus (EP-01: Idea & Stalled Project Flow)

- ⏳ "Ý tưởng mới" NL input flow
- ⏳ "Dự án dở dang" repo scan
- ⏳ Persona dashboards (EM/PM/CTO)

---

**SDLC 6.1.0 | Sprint 78 | Stage 04 (BUILD)**

*G-Sprint Approval Required Before Sprint Start*
