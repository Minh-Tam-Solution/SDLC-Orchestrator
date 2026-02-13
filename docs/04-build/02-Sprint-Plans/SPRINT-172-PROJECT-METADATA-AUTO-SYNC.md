# Sprint 172: Project Metadata Auto-Sync

**Sprint Duration**: Feb 10-14, 2026 (5 days)
**Status**: ✅ PARTIAL COMPLETE
**Phase**: Phase 6 - Market Expansion + Infrastructure
**Framework**: SDLC 6.0.3 (7-Pillar + Section 7 Quality Assurance)
**CTO Approval**: ✅ APPROVED (Feb 10, 2026)

---

## 🎯 **Sprint Goal**

Implement **Project Metadata Auto-Sync** to eliminate manual database updates by parsing canonical repository files (`.sdlc-config.json`, `AGENTS.md`, `CLAUDE.md`, `README.md`) on project access.

**Success Criteria**:
- ✅ POST `/projects/{id}/sync` endpoint working
- ✅ Auto-sync on project page load
- ✅ 95%+ test coverage
- ✅ <200ms p95 latency
- ✅ SDLC-Orchestrator metadata always accurate

---

## 📋 **Sprint Backlog**

### **Day 1: Backend Implementation** (2 hours)

#### Task 1.1: ProjectSyncService Core (1 hour)
**Owner**: Backend Team
**Priority**: P0

**Deliverables**:
```python
# backend/app/services/project_sync_service.py

class ProjectSyncService:
    - async def sync_project_metadata()
    - async def _parse_sdlc_config()
    - async def _parse_agents_md()
    - async def _parse_claude_md()
    - async def _parse_readme()
    - async def _get_git_metadata()
```

**Acceptance Criteria**:
- [ ] All 6 methods implemented with real file parsing (no mocks)
- [ ] Handles missing files gracefully (returns empty dict)
- [ ] Parses AGENTS.md lines 20-30 for sprint info
- [ ] Parses CLAUDE.md lines 1-10 for framework version
- [ ] README.md first paragraph extraction (<200 chars)

**Test Coverage**: 95%+

#### Task 1.2: API Endpoint (1 hour)
**Owner**: Backend Team
**Priority**: P0

**Deliverables**:
```python
# backend/app/api/routes/projects.py

@router.post("/{project_id}/sync")
async def sync_project_metadata():
    # 1. Check permissions (project member only)
    # 2. Check 5-min cache (Redis)
    # 3. Call ProjectSyncService
    # 4. Update database
    # 5. Set cache
    # 6. Return updated project
```

**Acceptance Criteria**:
- [ ] POST `/api/v1/projects/{id}/sync` endpoint created
- [ ] Auth middleware (requires project membership)
- [ ] 5-min cache with Redis
- [ ] Updates `projects` table with synced metadata
- [ ] Returns `ProjectResponse` schema
- [ ] Error handling (404, 403, 500)

**Test Coverage**: 90%+

---

### **Day 2: Frontend Integration** (1 hour)

#### Task 2.1: useProjectSync Hook (30 min)
**Owner**: Frontend Team
**Priority**: P0

**Deliverables**:
```typescript
// frontend/src/hooks/useProjectSync.ts

export function useProjectSync(projectId: string) {
  return useMutation({
    mutationFn: () => syncProjectMetadata(projectId),
    onSuccess: (updatedProject) => {
      // Update cache
      // Invalidate queries
    }
  });
}
```

**Acceptance Criteria**:
- [ ] Hook created with TanStack Query mutation
- [ ] Calls `POST /projects/{id}/sync` API
- [ ] Updates project cache on success
- [ ] Invalidates project list queries
- [ ] Error handling with console.error

**Test Coverage**: 80%+

#### Task 2.2: Auto-Sync on Page Load (30 min)
**Owner**: Frontend Team
**Priority**: P0

**Deliverables**:
```typescript
// frontend/src/app/app/projects/[id]/page.tsx

export default function ProjectDetailPage({ params }) {
  const syncMutation = useProjectSync(params.id);

  // Auto-sync on mount
  useEffect(() => {
    syncMutation.mutate();
  }, [params.id]);

  return <ProjectDetails />;
}
```

**Acceptance Criteria**:
- [ ] Project detail page calls `syncMutation.mutate()` on mount
- [ ] Non-blocking (page loads with cached data)
- [ ] UI updates when sync completes
- [ ] Optional: Loading indicator during sync

**Test Coverage**: E2E test

---

### **Day 3: Testing & QA** (1 hour)

#### Task 3.1: Unit Tests (30 min)
**Owner**: Backend Team
**Priority**: P0

**Files**:
```bash
backend/tests/unit/services/test_project_sync_service.py
  - test_parse_sdlc_config_valid()
  - test_parse_sdlc_config_missing()
  - test_parse_agents_md_sprint_171()
  - test_parse_agents_md_no_sprint()
  - test_parse_claude_md_framework_version()
  - test_parse_readme_first_paragraph()
  - test_get_git_metadata()
```

**Acceptance Criteria**:
- [ ] 95%+ coverage for ProjectSyncService
- [ ] All edge cases tested (missing files, invalid JSON, empty content)
- [ ] Fast (<1s total test time)

#### Task 3.2: Integration Tests (30 min)
**Owner**: Backend + Frontend Team
**Priority**: P0

**Files**:
```bash
backend/tests/integration/test_project_sync_api.py
  - test_sync_project_metadata_success()
  - test_sync_project_metadata_cache()
  - test_sync_project_metadata_not_member()
  - test_sync_project_metadata_repo_not_found()

frontend/e2e/project-metadata-sync.spec.ts
  - test('auto-syncs on page load')
  - test('displays synced metadata')
```

**Acceptance Criteria**:
- [ ] 90%+ coverage for API endpoint
- [ ] E2E test passes (Playwright)
- [ ] Performance verified (<200ms p95)

---

### **Day 4: Deployment & Verification** (30 min)

#### Task 4.1: Deploy to Staging (15 min)
**Owner**: DevOps Team
**Priority**: P0

**Steps**:
1. Rebuild backend Docker image
2. Deploy to staging environment
3. Restart backend service
4. Verify health checks pass

**Acceptance Criteria**:
- [ ] Backend deployed to staging
- [ ] POST `/projects/{id}/sync` endpoint accessible
- [ ] Logs show no errors

#### Task 4.2: Smoke Testing (15 min)
**Owner**: QA Team
**Priority**: P0

**Test Cases**:
1. Visit https://sdlc.nhatquangholding.com/app/projects/c0000000-0000-0000-0000-000000000003
2. Check Network tab: POST `/projects/{id}/sync` called
3. Verify metadata updated (SDLC 6.0.3, Sprint 171, G3 Ship Ready)
4. Refresh page: metadata still accurate (cached)
5. Wait 6 minutes: metadata re-synced (cache expired)

**Acceptance Criteria**:
- [ ] All smoke tests pass
- [ ] No 500 errors in logs
- [ ] Performance <200ms (Chrome DevTools)

---

### **Day 5: Documentation & Sprint Close** (1 hour)

#### Task 5.1: Update Documentation (30 min)
**Owner**: Tech Lead
**Priority**: P1

**Files to Update**:
```bash
docs/02-design/14-Technical-Specs/Project-Metadata-Auto-Sync-Design.md ✅
docs/04-build/02-Sprint-Plans/SPRINT-172-PROJECT-METADATA-AUTO-SYNC.md ✅
docs/01-planning/05-API-Design/API-Specification.md (add /sync endpoint)
AGENTS.md (update with Sprint 172 completion)
```

**Acceptance Criteria**:
- [ ] Technical spec complete
- [ ] Sprint plan updated
- [ ] API docs include `/sync` endpoint
- [ ] AGENTS.md reflects Sprint 172 status

#### Task 5.2: Sprint Completion Report (30 min)
**Owner**: Scrum Master
**Priority**: P1

**Deliverable**: `SPRINT-172-COMPLETION-REPORT.md`

**Sections**:
- Sprint goal achievement (100%)
- Velocity (LOC added, tests written)
- Performance metrics (latency, test coverage)
- Known issues / technical debt
- Next sprint preview (Phase 3 features)

**Acceptance Criteria**:
- [ ] Report published to docs/04-build/02-Sprint-Plans/
- [ ] CTO review scheduled
- [ ] Stakeholders notified

---

## 📊 **Sprint Metrics**

### Estimated Effort

```yaml
Feature 1 (Project Metadata Auto-Sync): 3-4 hours
  Day 1 (Backend): 2 hours
  Day 2 (Frontend): 1 hour
  Day 3 (Testing): 1 hour
  Day 4 (Deploy): 0.5 hour
  Day 5 (Docs): 1 hour

Feature 2 (Project-Team-Tier Ownership): 18 hours
  Backend Schema: 2 hours
  Backend Validation: 3 hours
  Backend Endpoint: 3 hours
  Frontend Types/Hook: 2 hours
  Frontend Edit Modal: 3 hours
  Testing: 4 hours
  Documentation: 1 hour

Total Sprint Effort: ~22 hours

Team Allocation:
  - Backend Lead: 10.5 hours (F1: 2.5h + F2: 8h)
  - Frontend Lead: 6 hours (F1: 1h + F2: 5h)
  - QA Engineer: 5 hours (F1: 1h + F2: 4h)
  - DevOps: 0.5 hour
  - Tech Lead: 2 hours (docs)
```

### Code Metrics (Estimated)

```yaml
New Code:
  Backend:
    - project_sync_service.py: ~200 LOC
    - projects.py (endpoint): ~50 LOC
  Frontend:
    - useProjectSync.ts: ~30 LOC
    - page.tsx (integration): ~10 LOC

  Total: ~290 LOC (production code)

Tests:
  - Unit tests: ~150 LOC
  - Integration tests: ~100 LOC
  - E2E tests: ~50 LOC

  Total: ~300 LOC (test code)

Test Coverage: 95%+ (unit + integration)
```

### Performance Targets

```yaml
API Latency (p95):
  - Cache hit: <50ms
  - Cache miss: <200ms

File Parsing Time:
  - .sdlc-config.json: <10ms
  - AGENTS.md: <20ms
  - CLAUDE.md: <20ms
  - README.md: <30ms

Total Pipeline: <130ms (under 200ms target)
```

---

## 🔗 **Related Documents**

### Design Documents (Stage 02)
- ✅ [Technical Specification](../../../02-design/14-Technical-Specs/Project-Metadata-Auto-Sync-Design.md)
- ✅ [ADR-029: AGENTS.md Integration Strategy](../../../02-design/01-ADRs/ADR-029-AGENTS-MD-Integration-Strategy.md)

### Migration (Stage 04)
- ✅ [s172_001_sync_sdlc_orchestrator_metadata.py](../../../backend/alembic/versions/s172_001_sync_sdlc_orchestrator_metadata.py)

### Testing (Stage 05)
- [ ] Unit tests: `backend/tests/unit/services/test_project_sync_service.py`
- [ ] Integration tests: `backend/tests/integration/test_project_sync_api.py`
- [ ] E2E tests: `frontend/e2e/project-metadata-sync.spec.ts`

---

## ⚠️ **Risks & Mitigation**

### Risk 1: Repository Path Not Accessible

**Impact**: HIGH (sync fails for all projects)
**Probability**: MEDIUM

**Mitigation**:
- Validate `repo_path` exists before parsing
- Fallback to default path: `/home/nqh/shared/{project.name}`
- Error handling returns 404 with clear message
- Admin dashboard to configure repo paths

### Risk 2: File Parsing Errors

**Impact**: MEDIUM (partial sync, missing data)
**Probability**: LOW

**Mitigation**:
- Graceful degradation (missing file → empty dict)
- JSON schema validation for .sdlc-config.json
- Regex patterns tested with edge cases
- Logging for debugging (which file/line failed)

### Risk 3: Performance Degradation

**Impact**: MEDIUM (slow page loads)
**Probability**: LOW

**Mitigation**:
- 5-min cache (avoid excessive file I/O)
- Background mutation (non-blocking UI)
- Performance profiling (Chrome DevTools)
- Monitoring alerts (p95 latency >200ms)

---

## ✅ **Definition of Done**

Sprint 172 is **DONE** when:

- [x] **Phase 1** (Quick Fix): SDLC-Orchestrator metadata updated via migration ✅
- [x] **Phase 1.5** (Bug Fixes - Gate Status & Cold Start):
  - [x] Gate status mapping fixed (UPPERCASE DB enum → display string)
  - [x] DynamicContextService.load_context() hydrates from DB on cold start
  - [x] ContextOverlayService queries highest APPROVED gate first
  - [x] TeamsService.create_team() uses selectinload (no lazy-load hang)
  - [x] Documentation: SPEC-0011 v1.1.0, AGENTS-MD Tech Design Section 15
- [x] **Phase 1.6** (VSCode Extension v1.6.3):
  - [x] Auth pre-check in init command (warn if not logged in)
  - [x] syncWithServer returns bool + user-facing error messages
  - [x] Null guards for E2E validate and spec validation results
  - [x] Version bump 1.6.2 → 1.6.3
- [x] **Feature 2 - Design** (Project-Team-Tier Ownership Spec):
  - [x] Project-Ownership-Transfer-Spec.md written (333 lines)
  - [x] Data-Model-ERD.md updated (owner_id, policy_pack_tier, tier constraints)
  - [x] API-Specification.md updated (PUT → PATCH, team/owner/tier fields)
  - [x] Teams-Data-Model-Specification.md Section 9 added
  - [x] Sprint plan expanded with Feature 2 tasks
- [ ] **Phase 2** (Auto-Sync) - Deferred to Sprint 173:
  - [ ] POST `/projects/{id}/sync` endpoint live in staging
  - [ ] Auto-sync on project page load (frontend integration)
  - [ ] 95%+ test coverage (unit + integration + E2E)
- [ ] **Feature 2 - Implementation** - Deferred to Sprint 173:
  - [ ] PATCH `/projects/{id}` supports team_id, owner_id, policy_pack_tier
  - [ ] Cross-org team assignment blocked (400)
  - [ ] PROFESSIONAL+ null team_id blocked (400)
  - [ ] Frontend Edit Project modal working
  - [ ] 13 unit tests + E2E tests passing

**Sign-off Required**:
- CTO (Technical approval)
- QA Lead (Test verification)
- DevOps (Deployment confirmation)

---

## 🏗️ **Feature 2: Project-Team-Tier Ownership Management**

**Priority**: P1
**Effort**: 18h (2.25 days)
**Technical Spec**: [Project-Ownership-Transfer-Spec.md](../../../02-design/14-Technical-Specs/Project-Ownership-Transfer-Spec.md)
**CTO Approval**: ✅ APPROVED (Feb 12, 2026)

### Overview

Enable project team reassignment, ownership transfer, and tier management via `PATCH /projects/{project_id}`. Currently only `name` and `description` are updatable. This feature adds:
- `team_id` reassignment (same org only, tier-dependent)
- `owner_id` transfer (to existing project member)
- `policy_pack_tier` upgrade/downgrade (with validation)

### Task F2.1: Backend - ProjectUpdate Schema (2h)
**Owner**: Backend Team
**Priority**: P0

**File**: `backend/app/schemas/project.py`

Add to `ProjectUpdate`:
- `team_id: Optional[str]` - reassign to different team
- `owner_id: Optional[str]` - transfer ownership
- `policy_pack_tier: Optional[str]` - LITE/STANDARD/PROFESSIONAL/ENTERPRISE

**Acceptance Criteria**:
- [ ] ProjectUpdate schema accepts all 5 fields
- [ ] Pydantic validation for tier enum values
- [ ] Backward compatible (existing name/description updates still work)

### Task F2.2: Backend - Validation Service (3h)
**Owner**: Backend Team
**Priority**: P0

**File**: `backend/app/services/teams_service.py`

New method `validate_project_team_reassignment()`:
- Cross-org check: target team.organization_id must match project's org
- User membership: requesting user must be TeamMember of target team
- Tier enforcement: PROFESSIONAL/ENTERPRISE cannot have null team_id
- Ownership: new owner must be existing ProjectMember

**Acceptance Criteria**:
- [ ] Cross-org assignment returns 400
- [ ] Non-member of target team returns 403
- [ ] PROFESSIONAL null team_id returns 400
- [ ] Invalid owner_id returns 404

### Task F2.3: Backend - Update Endpoint (3h)
**Owner**: Backend Team
**Priority**: P0

**File**: `backend/app/api/routes/projects.py`

Extend `update_project()` handler:
1. Existing auth check (owner/admin of project)
2. If `team_id` provided: call validation service
3. If `owner_id` provided: validate is ProjectMember + only owner can transfer
4. If `policy_pack_tier` changes: validate tier requirements, warn on downgrade
5. Log all changes to `governance_audit_log`
6. Use `selectinload` for response (avoid lazy-load hang)

**Acceptance Criteria**:
- [ ] Team reassignment works (same org)
- [ ] Ownership transfer works (valid member)
- [ ] Tier upgrade validates team_id requirement
- [ ] Tier downgrade returns warning, keeps team_id
- [ ] All changes logged to audit trail
- [ ] No lazy-load hang (selectinload used)

### Task F2.4: Frontend - API Types & Hook (2h)
**Owner**: Frontend Team
**Priority**: P0

**Files**: `frontend/src/lib/api.ts`, `frontend/src/hooks/useProjects.ts`

- Add `ProjectUpdate` interface with optional fields
- Add `updateProject(projectId, data)` API function
- Add `useUpdateProject(projectId)` mutation hook
- Update `ProjectDetail` type: add `team_id`, `team_name`, `policy_pack_tier`
- Cache invalidation on success (project detail + lists)

**Acceptance Criteria**:
- [ ] updateProject API function created
- [ ] useUpdateProject hook with cache invalidation
- [ ] ProjectDetail type includes team_id, team_name
- [ ] TypeScript compilation passes

### Task F2.5: Frontend - Edit Project Modal (3h)
**Owner**: Frontend Team
**Priority**: P0

**File**: `frontend/src/app/app/projects/[id]/page.tsx`

- "Edit Project" button visible to owner/admin only
- Dialog with: name, description, team selector, owner transfer dropdown, tier badge
- Team selector: `useTeams()` dropdown, pre-filled with current team
- Owner transfer: dropdown of project members, current owner selected
- Loading/error states following existing modal patterns

**Acceptance Criteria**:
- [ ] Edit button visible for owner/admin
- [ ] Edit button hidden for viewers/non-members
- [ ] Team selector shows user's teams only
- [ ] Owner transfer dropdown shows project members
- [ ] Success toast after update
- [ ] Error toast for validation failures

### Task F2.6: Testing (4h)
**Owner**: QA Team
**Priority**: P0

**Test Scenarios** (13 unit + integration + E2E):
- [ ] Update name/description → 200
- [ ] Reassign team (same org) → 200
- [ ] Reassign team (cross-org) → 400
- [ ] Transfer ownership (valid member) → 200
- [ ] Transfer ownership (non-member) → 404
- [ ] Transfer by non-owner → 403
- [ ] Unassign team (LITE) → 200
- [ ] Unassign team (PROFESSIONAL) → 400
- [ ] Upgrade LITE → PROFESSIONAL (with team) → 200
- [ ] Upgrade LITE → PROFESSIONAL (no team) → 400
- [ ] Downgrade PROFESSIONAL → LITE → 200 + warning
- [ ] E2E: Edit modal opens and submits
- [ ] E2E: Unauthorized user cannot see edit button

### Task F2.7: Documentation Review (1h)
**Owner**: Tech Lead
**Priority**: P1

- [ ] Verify Data-Model-ERD.md matches implementation
- [ ] Verify API-Specification.md matches implementation
- [ ] Verify Project-Ownership-Transfer-Spec.md is complete
- [ ] Update AGENTS.md with Sprint 172 ownership feature

---

## 📅 **Next Sprint Preview: Sprint 173**

### Phase 3: Production Enhancements

**Features** (Future):
- GitHub API integration (remote repos)
- Webhook triggers (push → auto-sync)
- Background job queue (non-blocking)
- Admin dashboard (sync status monitoring)
- Batch sync for all projects (CLI command)

**Estimated Effort**: 5-7 hours (Sprint 173-174)

---

## 📝 **Sprint Retrospective** (Post-Sprint)

### What Went Well
- Phase 1 completed in 30 min (SQL migration)
- Clear technical spec before implementation
- ADR-029 compliance ensured vendor neutrality

### What Could Be Improved
- Auto-Sync feature (Phase 2) deferred — underestimated dependency on gate status bug fix
- Feature 2 design docs completed but implementation deferred to Sprint 173

### Action Items
- Sprint 173: Implement Phase 2 Auto-Sync (ProjectSyncService + API endpoint)
- Sprint 173: Implement Feature 2 PATCH /projects/{id} (team/owner/tier management)
- Cleanup: Fix 15 pre-existing agents_md_validator test failures (Sprint 80 drift)

---

**Sprint Status**: ✅ PARTIAL COMPLETE (Phase 1 + Bug Fixes + Design)
**Completed**: Feb 13, 2026
**Deferred**: Phase 2 Auto-Sync + Feature 2 Implementation → Sprint 173
**CTO Review**: Sprint close (Feb 14, 2026)
