# Sprint 101: Risk-Based Planning Trigger + CRP Implementation

**Version**: 1.0.0  
**Date**: January 23, 2026  
**Status**: DESIGN APPROVED - Ready for Implementation  
**Epic**: GAP-001, GAP-002 (SDLC 6.1.0 Compliance)

---

## Executive Summary

**Goal**: Replace >15 LOC heuristic with Risk-Based Planning Trigger (7 mandatory risk factors) and implement Consultation Request Protocol (CRP) UI for human oversight workflow.

**Timeline**: 5 days (Jan 27 - Jan 31, 2026)  
**Story Points**: 18 SP  
**Owner**: Backend Lead + Frontend Lead

**Key Deliverables**:
1. Risk-Based Planning Trigger Engine (backend)
2. CRP UI for consultation requests (frontend)
3. Integration with existing PlanningOrchestratorService (Sprint 98)
4. 25+ tests

---

## Background

### Current State (Sprint 98-100 Complete)

**Existing Services**:
- ✅ `PlanningOrchestratorService` (828 lines) - Orchestrates sub-agents
- ✅ `PatternExtractionService` (570 lines) - Extracts patterns
- ✅ `ADRScannerService` (536 lines) - Scans ADRs
- ✅ `TestPatternService` (561 lines) - Analyzes test patterns
- ✅ `ConformanceCheckService` (705 lines) - Checks conformance
- ✅ `FeedbackLearningService` (1,581 lines) - Learns from PRs

**Gap Identified**:
- ❌ Still using `>15 LOC` heuristic for planning trigger
- ❌ No UI for CRP (Consultation Request Protocol)
- ❌ No risk factor analysis before planning

### Framework 5.2.0 Requirements

**From**: `03-AI-GOVERNANCE/03-Planning-Mode-Principle.md`

```yaml
Risk-Based Planning Trigger (7 Mandatory Risk Factors):
  1. Data schema changes (migrations, models)
  2. API contracts (endpoints, breaking changes)
  3. Authentication / Authorization
  4. Cross-service boundaries (microservices)
  5. Concurrency / race conditions
  6. Security-sensitive code (payment, PII)
  7. Public API interfaces

LOC Heuristic (Recommended, not mandatory):
  - >50 LOC: Highly recommended
  - >15 LOC: Consider planning
  - <15 LOC + zero risk factors: No planning needed
```

**CRP (Consultation Request Protocol)**:
- Human oversight for high-risk changes
- AI proposes change → CRP → Human reviews → Approve/Reject
- Tracks consultation history

---

## Architecture

### Component Overview

```
┌────────────────────────────────────────────────────────────────┐
│              SPRINT 101: RISK-BASED PLANNING                   │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  Developer Commits Changes                                     │
│         ↓                                                      │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ RiskAnalysisService (NEW)                                │ │
│  │ - analyze_diff() → Risk factors detected                 │ │
│  │ - calculate_risk_score() → 0-100 score                   │ │
│  │ - should_require_planning() → Boolean decision           │ │
│  └──────────────────────────────────────────────────────────┘ │
│         ↓                                                      │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ IF risk_score > 50 OR risk_factors > 0                   │ │
│  └──────────────────────────────────────────────────────────┘ │
│         ↓                                                      │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ PlanningOrchestratorService (Sprint 98 - REUSE)          │ │
│  │ - Orchestrate sub-agents                                 │ │
│  │ - Generate implementation plan                           │ │
│  └──────────────────────────────────────────────────────────┘ │
│         ↓                                                      │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ IF high_risk (score > 70)                                │ │
│  └──────────────────────────────────────────────────────────┘ │
│         ↓                                                      │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ CRPService (NEW)                                         │ │
│  │ - create_consultation_request()                          │ │
│  │ - assign_reviewer(role, expertise)                       │ │
│  │ - track_resolution()                                     │ │
│  └──────────────────────────────────────────────────────────┘ │
│         ↓                                                      │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ CRP Dashboard (NEW - Frontend)                           │ │
│  │ - Pending consultations list                             │ │
│  │ - Risk analysis display                                  │ │
│  │ - Approve/Reject workflow                                │ │
│  │ - Comments/feedback thread                               │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

## Detailed Tasks

### Backend (12 SP - 3.5 days)

#### Task 1.1: RiskAnalysisService (5 SP - 1.5 days)

**File**: `backend/app/services/risk_analysis_service.py` (~600 lines)

**Key Methods**:
```python
class RiskAnalysisService:
    async def analyze_diff(self, diff: str, context: dict) -> RiskAnalysis:
        """
        Analyze git diff for 7 mandatory risk factors.
        
        Returns:
            RiskAnalysis with detected factors, score, recommendations
        """
        risk_factors = []
        
        # 1. Data schema changes
        if self._contains_migration(diff):
            risk_factors.append(RiskFactor.DATA_SCHEMA)
        
        # 2. API contracts
        if self._contains_api_changes(diff):
            risk_factors.append(RiskFactor.API_CONTRACT)
        
        # 3. Auth changes
        if self._contains_auth_changes(diff):
            risk_factors.append(RiskFactor.AUTH)
        
        # 4. Cross-service
        if self._contains_cross_service(diff):
            risk_factors.append(RiskFactor.CROSS_SERVICE)
        
        # 5. Concurrency
        if self._contains_concurrency(diff):
            risk_factors.append(RiskFactor.CONCURRENCY)
        
        # 6. Security-sensitive
        if self._contains_security(diff):
            risk_factors.append(RiskFactor.SECURITY)
        
        # 7. Public API
        if self._contains_public_api(diff):
            risk_factors.append(RiskFactor.PUBLIC_API)
        
        score = self._calculate_risk_score(risk_factors, diff)
        
        return RiskAnalysis(
            risk_factors=risk_factors,
            risk_score=score,
            loc_changed=self._count_loc(diff),
            should_plan=score > 50 or len(risk_factors) > 0,
            recommendations=self._generate_recommendations(risk_factors)
        )
    
    def _contains_migration(self, diff: str) -> bool:
        """Check for alembic migrations, model changes."""
        patterns = [
            r"alembic/versions/.*\.py",
            r"models/.*\.py.*class.*\(Base\)",
            r"CREATE TABLE|ALTER TABLE|DROP TABLE"
        ]
        return any(re.search(p, diff) for p in patterns)
    
    def _contains_api_changes(self, diff: str) -> bool:
        """Check for API route changes."""
        patterns = [
            r"@router\.(get|post|put|delete|patch)",
            r"@app\.route",
            r"FastAPI\(",
            r"Request|Response"
        ]
        return any(re.search(p, diff) for p in patterns)
    
    # ... similar for other risk factors
    
    def _calculate_risk_score(self, factors: list, diff: str) -> int:
        """
        Calculate 0-100 risk score.
        
        Formula:
            base_score = len(factors) * 20  # Each factor = 20 points
            loc_multiplier = min(loc / 50, 1.5)  # Up to 1.5x for large changes
            final_score = min(base_score * loc_multiplier, 100)
        """
        base = len(factors) * 20
        loc = self._count_loc(diff)
        multiplier = min(loc / 50, 1.5)
        return min(int(base * multiplier), 100)
```

**Tests**: 15 tests
- Test each risk factor detection
- Test risk score calculation
- Test LOC counting
- Test edge cases (empty diff, no risks)

---

#### Task 1.2: CRPService (4 SP - 1 day)

**File**: `backend/app/services/crp_service.py` (~400 lines)

**Database Schema**:
```sql
CREATE TABLE consultation_requests (
    id UUID PRIMARY KEY,
    project_id UUID NOT NULL REFERENCES projects(id),
    pr_id VARCHAR,
    requester_id UUID NOT NULL REFERENCES users(id),
    risk_analysis JSONB NOT NULL,  -- RiskAnalysis object
    status VARCHAR NOT NULL,  -- pending, approved, rejected, cancelled
    assigned_reviewer_id UUID REFERENCES users(id),
    resolution_notes TEXT,
    created_at TIMESTAMP NOT NULL,
    resolved_at TIMESTAMP,
    CONSTRAINT valid_status CHECK (status IN ('pending', 'approved', 'rejected', 'cancelled'))
);

CREATE TABLE consultation_comments (
    id UUID PRIMARY KEY,
    consultation_id UUID NOT NULL REFERENCES consultation_requests(id),
    user_id UUID NOT NULL REFERENCES users(id),
    comment TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL
);

CREATE INDEX idx_consultations_status ON consultation_requests(status);
CREATE INDEX idx_consultations_project ON consultation_requests(project_id);
CREATE INDEX idx_consultations_reviewer ON consultation_requests(assigned_reviewer_id);
```

**Key Methods**:
```python
class CRPService:
    async def create_consultation(
        self,
        project_id: UUID,
        pr_id: str,
        risk_analysis: RiskAnalysis,
        requester_id: UUID
    ) -> ConsultationRequest:
        """Create new consultation request."""
        
    async def assign_reviewer(
        self,
        consultation_id: UUID,
        reviewer_id: UUID
    ) -> ConsultationRequest:
        """Assign expert reviewer based on risk factors."""
        
    async def resolve_consultation(
        self,
        consultation_id: UUID,
        status: str,  # approved | rejected
        notes: str,
        reviewer_id: UUID
    ) -> ConsultationRequest:
        """Resolve consultation with decision."""
        
    async def add_comment(
        self,
        consultation_id: UUID,
        user_id: UUID,
        comment: str
    ) -> ConsultationComment:
        """Add comment to consultation thread."""
        
    async def get_pending_consultations(
        self,
        reviewer_id: UUID | None = None,
        project_id: UUID | None = None
    ) -> list[ConsultationRequest]:
        """Get pending consultations (optionally filtered)."""
```

**Tests**: 10 tests
- Create consultation
- Assign reviewer
- Resolve (approve/reject)
- Add comments
- Query filtering

---

#### Task 1.3: API Routes (2 SP - 0.5 day)

**File**: `backend/app/api/routes/consultations.py` (~350 lines)

**Endpoints**:
```python
# Risk Analysis
POST /api/v1/risk/analyze
  Body: { diff: string, context?: dict }
  Response: RiskAnalysis

# Consultation Requests
POST /api/v1/consultations
  Body: { project_id, pr_id, risk_analysis }
  Response: ConsultationRequest

GET /api/v1/consultations
  Query: ?status=pending&project_id=&reviewer_id=
  Response: { consultations: ConsultationRequest[] }

GET /api/v1/consultations/{id}
  Response: ConsultationRequest (with comments)

POST /api/v1/consultations/{id}/assign
  Body: { reviewer_id }
  Response: ConsultationRequest

POST /api/v1/consultations/{id}/resolve
  Body: { status: "approved"|"rejected", notes }
  Response: ConsultationRequest

POST /api/v1/consultations/{id}/comments
  Body: { comment }
  Response: ConsultationComment

# Integration with Planning
GET /api/v1/planning/should-plan
  Query: ?diff=&project_id=
  Response: { should_plan: boolean, risk_analysis: RiskAnalysis }
```

**Tests**: Built into service tests

---

#### Task 1.4: Integration with PlanningOrchestratorService (1 SP - 0.5 day)

**File**: `backend/app/services/planning_orchestrator_service.py` (modify existing)

**Changes**:
```python
class PlanningOrchestratorService:
    def __init__(self, ..., risk_service: RiskAnalysisService, crp_service: CRPService):
        self.risk_service = risk_service
        self.crp_service = crp_service
    
    async def create_planning_session(
        self,
        project_id: UUID,
        task_description: str,
        diff: str | None = None  # NEW
    ):
        """
        Create planning session with risk analysis.
        
        NEW: If diff provided, analyze risk first.
        If high-risk, create CRP before planning.
        """
        if diff:
            risk_analysis = await self.risk_service.analyze_diff(diff, context)
            
            if risk_analysis.should_plan:
                # Risk detected - planning required
                pass
            else:
                # No risk - skip planning
                return {"message": "No planning required", "risk_analysis": risk_analysis}
            
            if risk_analysis.risk_score > 70:
                # High risk - create CRP
                consultation = await self.crp_service.create_consultation(
                    project_id=project_id,
                    pr_id=...,
                    risk_analysis=risk_analysis,
                    requester_id=...
                )
                return {"consultation_required": True, "consultation_id": consultation.id}
        
        # Continue with existing planning flow
        ...
```

---

### Frontend (6 SP - 1.5 days)

#### Task 2.1: CRP Dashboard Page (3 SP - 1 day)

**File**: `frontend/src/app/app/consultations/page.tsx` (~500 lines)

**Features**:
- List pending consultations (tabs: Pending, Approved, Rejected, All)
- Filter by project, reviewer, risk factors
- Risk analysis summary cards
- Quick actions (Assign, View Details)
- Real-time updates (useQuery polling)

**Components**:
```tsx
// Main dashboard
export default function ConsultationsPage() {
  const [status, setStatus] = useState<'pending' | 'approved' | 'rejected' | 'all'>('pending')
  const { data, isLoading } = useConsultations({ status })
  
  return (
    <div>
      <ConsultationTabs status={status} onChangeStatus={setStatus} />
      <ConsultationFilters />
      <ConsultationList consultations={data?.consultations} />
    </div>
  )
}

// Consultation card
function ConsultationCard({ consultation }) {
  return (
    <Card>
      <RiskBadge score={consultation.risk_analysis.risk_score} />
      <RiskFactorsList factors={consultation.risk_analysis.risk_factors} />
      <ConsultationMeta consultation={consultation} />
      <QuickActions consultation={consultation} />
    </Card>
  )
}
```

---

#### Task 2.2: Consultation Detail Page (2 SP - 0.5 day)

**File**: `frontend/src/app/app/consultations/[id]/page.tsx` (~400 lines)

**Features**:
- Risk analysis detail display
- Diff viewer (code changes)
- Comments thread
- Approve/Reject workflow
- Reviewer assignment
- Audit trail

**Components**:
```tsx
export default function ConsultationDetailPage({ params }) {
  const { data: consultation } = useConsultation(params.id)
  const resolveMutation = useResolveConsultation()
  
  return (
    <div>
      <ConsultationHeader consultation={consultation} />
      <RiskAnalysisSection analysis={consultation.risk_analysis} />
      <DiffViewer diff={consultation.diff} />
      <CommentsThread consultationId={params.id} />
      <ResolveActions 
        onApprove={(notes) => resolveMutation.mutate({ id: params.id, status: 'approved', notes })}
        onReject={(notes) => resolveMutation.mutate({ id: params.id, status: 'rejected', notes })}
      />
    </div>
  )
}
```

---

#### Task 2.3: React Query Hooks (1 SP - 0.5 day)

**File**: `frontend/src/hooks/useConsultations.ts` (~300 lines)

**Hooks**:
```typescript
// List consultations
export function useConsultations(filters?: ConsultationFilters) {
  return useQuery({
    queryKey: ['consultations', filters],
    queryFn: () => api.consultations.list(filters)
  })
}

// Single consultation
export function useConsultation(id: string) {
  return useQuery({
    queryKey: ['consultations', id],
    queryFn: () => api.consultations.get(id),
    refetchInterval: 5000  // Real-time updates
  })
}

// Create consultation
export function useCreateConsultation() {
  return useMutation({
    mutationFn: api.consultations.create,
    onSuccess: () => queryClient.invalidateQueries(['consultations'])
  })
}

// Assign reviewer
export function useAssignReviewer() {
  return useMutation({
    mutationFn: ({ id, reviewerId }) => api.consultations.assign(id, reviewerId),
    onSuccess: () => queryClient.invalidateQueries(['consultations'])
  })
}

// Resolve consultation
export function useResolveConsultation() {
  return useMutation({
    mutationFn: ({ id, status, notes }) => api.consultations.resolve(id, status, notes),
    onSuccess: () => queryClient.invalidateQueries(['consultations'])
  })
}

// Add comment
export function useAddConsultationComment() {
  return useMutation({
    mutationFn: ({ consultationId, comment }) => 
      api.consultations.addComment(consultationId, comment),
    onSuccess: () => queryClient.invalidateQueries(['consultations'])
  })
}

// Risk analysis
export function useRiskAnalysis() {
  return useMutation({
    mutationFn: ({ diff, context }) => api.risk.analyze(diff, context)
  })
}
```

---

## Success Metrics

| Metric | Target | Verification |
|--------|--------|--------------|
| Risk factor detection accuracy | >90% | Manual testing with 20 sample diffs |
| Risk score precision | ±10% | Compare with expert human assessment |
| CRP creation latency | <2s | API response time |
| Dashboard load time | <1s | Frontend performance |
| Test coverage | >90% | pytest coverage report |
| False positives (unnecessary planning) | <15% | Monitor first 100 changes |
| False negatives (missed risks) | <5% | Security audit |

---

## Testing Strategy

### Unit Tests (15 tests - backend)

**RiskAnalysisService**:
- Test each risk factor detection (7 tests)
- Test risk score calculation (3 tests)
- Test LOC counting (2 tests)
- Test edge cases (3 tests)

**CRPService**:
- Test CRUD operations (5 tests)
- Test workflow (approve/reject) (3 tests)
- Test filtering/querying (2 tests)

### Integration Tests (5 tests)

- Risk analysis → Planning trigger
- High-risk → CRP creation
- CRP resolution → Planning resume
- GitHub webhook → Risk analysis
- End-to-end workflow

### E2E Tests (5 tests - frontend)

- Create consultation request
- Assign reviewer
- Add comments
- Approve consultation
- Reject consultation

---

## Migration Plan

### Database Migration

**File**: `backend/alembic/versions/s101_001_crp_tables.py`

```python
def upgrade():
    # Create consultation_requests table
    op.create_table(...)
    
    # Create consultation_comments table
    op.create_table(...)
    
    # Create indexes
    op.create_index(...)

def downgrade():
    op.drop_table('consultation_comments')
    op.drop_table('consultation_requests')
```

### Backwards Compatibility

- ✅ Existing PlanningOrchestratorService still works without risk analysis
- ✅ Old `>15 LOC` heuristic available as fallback
- ✅ CRP optional (can be disabled via feature flag)

---

## Documentation Updates

### Framework Updates

**File**: `SDLC-Enterprise-Framework/03-AI-GOVERNANCE/03-Planning-Mode-Principle.md`

- Update with implementation details
- Add risk analysis examples
- Document CRP workflow

### Orchestrator Updates

**Files**:
- `PROJECT-STATUS.md` - Add Sprint 101 completion
- `CLAUDE.md` - Update with risk-based planning guidance
- `docs/02-design/03-ADRs/ADR-035-Risk-Based-Planning.md` - Create new ADR

---

## Timeline

| Day | Tasks | Owner | Hours |
|-----|-------|-------|-------|
| **Day 1** | RiskAnalysisService implementation | Backend | 8h |
| **Day 2** | RiskAnalysisService tests + CRPService start | Backend | 8h |
| **Day 3** | CRPService completion + API routes | Backend | 8h |
| **Day 4** | Frontend: CRP Dashboard + Detail page | Frontend | 8h |
| **Day 5** | Integration tests + E2E tests + Documentation | Full Team | 8h |

**Total Effort**: 40 hours (18 SP = 2.2 hours/SP)

---

## Risk & Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| False positives too high (>20%) | Medium | High | Add confidence scoring, allow user override |
| Performance issues (large diffs) | Low | Medium | Implement diff chunking, async processing |
| Complex regex patterns fail | Medium | Medium | Comprehensive test suite, fallback to AI analysis |
| CRP workflow too slow | Low | High | Real-time updates, notifications, auto-assignment |

---

## Dependencies

- ✅ Sprint 98: PlanningOrchestratorService (complete)
- ✅ Sprint 99: ConformanceCheckService (complete)
- ✅ Framework 5.2.0: Planning Mode Principle (complete)

---

## Approval

**Status**: ✅ APPROVED FOR IMPLEMENTATION

```
┌─────────────────────────────────────────────────────────────────┐
│                    ✅ SPRINT 101 APPROVED                       │
│                                                                 │
│  Sprint: 101 - Risk-Based Planning + CRP                       │
│  Date: January 23, 2026                                        │
│  Story Points: 18 SP                                           │
│  Timeline: 5 days (Jan 27 - Jan 31)                           │
│                                                                 │
│  "Critical gap closure for SDLC 6.1.0 compliance.              │
│   Approved for immediate execution post-Sprint 100."           │
│                                                                 │
│  — CTO, SDLC Orchestrator                                      │
└─────────────────────────────────────────────────────────────────┘
```
