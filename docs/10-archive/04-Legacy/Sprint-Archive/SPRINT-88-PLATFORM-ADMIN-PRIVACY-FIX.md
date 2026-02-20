# Sprint 88: Platform Admin Privacy Fix (ADR-030)
## Security & Privacy - Remove Customer Data Access from Platform Admins

**Sprint Dates**: February 1-12, 2026 (10 working days)
**Status**: 🔴 CRITICAL - Security & Privacy Issue
**Priority**: P0 - Must fix before soft launch (March 1, 2026)
**Framework**: SDLC 6.1.0
**Related Documents**:
- ADR-030: Platform Admin Role Redesign
- ADMIN-ROLE-REFACTOR-PLAN.md

---

## 🎯 Sprint Goal

**Remove all customer data access from Platform Admins.**

Platform Admin should be a **system operations role** (like AWS admin, GitHub staff), NOT a super user who can access customer projects, gates, evidence, and other sensitive data.

**Success Criteria**:
- ✅ Platform admins CANNOT access `/app/*` routes (redirected to `/admin`)
- ✅ Platform admins get 403 Forbidden on all customer API endpoints
- ✅ Regular customers unaffected (100% backward compatible)
- ✅ 100% E2E test coverage for role separation
- ✅ Zero security regressions

---

## 📊 Sprint Metrics

| Metric | Target | Status |
|--------|--------|--------|
| **Frontend Changes** | 5 files modified | ⏳ Not started |
| **Backend Changes** | 12 files modified + 1 migration | ⏳ Not started |
| **E2E Tests** | 10+ scenarios | ⏳ Not started |
| **API Latency** | <100ms p95 (no degradation) | ⏳ Not measured |
| **Security Score** | 0 privacy violations | ⏳ Not audited |

---

## 🗓️ Daily Plan (10 Days)

### **Day 1 (Feb 1): Quick Security Win - Frontend**

**Owner**: Frontend Lead
**Goal**: Remove "Back to App" link + add basic route guard

#### Tasks:
1. ✅ **Remove "Back to App" Link** (30 min)
   - File: `frontend/src/components/admin/AdminSidebar.tsx`
   - Delete lines 182-191 (Back to App link)
   - Commit: "fix(admin): Remove Back to App link - security fix"

2. ✅ **Add Route Guard to `/app` Layout** (1 hour)
   - File: `frontend/src/app/app/layout.tsx`
   - Add check: If `user.is_platform_admin` → redirect to `/admin`
   - Commit: "feat(security): Block platform admins from /app routes"

3. ✅ **Manual Testing** (30 min)
   - Login as platform admin (taidt@mtsolution.com.vn)
   - Verify: Cannot access `/app/projects`
   - Verify: Redirected to `/admin`

**Deliverable**: Platform admins can no longer access customer UI (partial fix)

---

### **Day 2 (Feb 3): Auto-redirect on Login**

**Owner**: Frontend Lead
**Goal**: Redirect admins to `/admin`, users to `/app` on login

#### Tasks:
1. ✅ **Update Login Flow** (1 hour)
   - File: `frontend/src/app/login/page.tsx`
   - After successful login, check `userProfile.is_platform_admin`
   - If admin → `/admin`, else → `/app`

2. ✅ **Update Header Link** (30 min)
   - File: `frontend/src/components/landing/Header.tsx`
   - Change "Dashboard" link based on `user.is_platform_admin`:
     - Admin: "Admin Panel" → `/admin`
     - User: "Dashboard" → `/app`

3. ✅ **Add TypeScript Types** (30 min)
   - File: `frontend/src/lib/types/user.ts`
   - Add `is_platform_admin: boolean` to UserProfile interface

4. ✅ **Manual Testing** (30 min)
   - Login as platform admin → should go to `/admin`
   - Login as regular user → should go to `/app`
   - Logout and switch between accounts

**Deliverable**: Login flow properly routes users based on role

---

### **Day 3 (Feb 4): Frontend E2E Tests**

**Owner**: QA Lead
**Goal**: 100% frontend role separation coverage

#### Tasks:
1. ✅ **E2E Test: Admin Blocked from Customer Routes** (2 hours)
   - File: `e2e/admin-role-separation.spec.ts`
   - Scenarios:
     - Admin tries `/app/projects` → redirected to `/admin`
     - Admin tries `/app/gates` → redirected to `/admin`
     - Admin tries `/app/evidence` → redirected to `/admin`

2. ✅ **E2E Test: Login Redirect** (1 hour)
   - Admin login → lands on `/admin`
   - User login → lands on `/app`

3. ✅ **E2E Test: Regular User Unaffected** (1 hour)
   - User can access `/app/projects` ✅
   - User cannot access `/admin` ❌ (403)

4. ✅ **Run Full Regression Suite** (1 hour)
   - Verify no existing tests broken
   - All 114 E2E tests still passing

**Deliverable**: 10+ E2E tests for role separation, all passing

---

### **Day 4 (Feb 5): Backend - Database Migration**

**Owner**: Backend Lead
**Goal**: Add `is_platform_admin` field to User model

#### Tasks:
1. ✅ **Create Migration Script** (1 hour)
   - File: `backend/alembic/versions/s88_add_platform_admin_flag.py`
   - Add column: `is_platform_admin BOOLEAN DEFAULT FALSE`
   - Set existing superusers: `UPDATE users SET is_platform_admin=TRUE WHERE is_superuser=TRUE`
   - Set `organization_id=NULL` for platform admins
   - Add constraint: Platform admins cannot have `organization_id`

2. ✅ **Update User Model** (30 min)
   - File: `backend/app/models/user.py`
   - Add field: `is_platform_admin: bool = Column(Boolean, default=False)`

3. ✅ **Run Migration Locally** (15 min)
   - `alembic upgrade head`
   - Verify: `SELECT id, email, is_superuser, is_platform_admin, organization_id FROM users WHERE is_superuser=TRUE`

4. ✅ **Update Seed Data** (30 min)
   - File: `backend/app/db/seed.py`
   - Ensure platform admin seed user has `is_platform_admin=True, organization_id=NULL`

**Deliverable**: Database schema supports platform admin role

---

### **Day 5 (Feb 6): Backend - API Response Updates**

**Owner**: Backend Lead
**Goal**: Include `is_platform_admin` in API responses

#### Tasks:
1. ✅ **Update UserProfile Schema** (30 min)
   - File: `backend/app/api/routes/auth.py`
   - Add `is_platform_admin: bool` to `UserProfile` Pydantic model
   - Return field in `GET /api/v1/auth/me` endpoint

2. ✅ **Update getCurrentUser Response** (30 min)
   - File: `backend/app/api/dependencies.py`
   - Ensure `is_platform_admin` loaded from database

3. ✅ **Test API Response** (30 min)
   - `curl -H "Authorization: Bearer $TOKEN" http://localhost:8300/api/v1/auth/me | jq .is_platform_admin`
   - Should return `true` for platform admins

**Deliverable**: Frontend can read `is_platform_admin` from API

---

### **Day 6 (Feb 7): Backend - Access Control Dependency**

**Owner**: Backend Lead
**Goal**: Create `require_customer_user` dependency

#### Tasks:
1. ✅ **Create New Dependency** (1 hour)
   - File: `backend/app/api/dependencies.py`
   - Function: `require_customer_user(current_user: User) -> User`
   - Logic: If `current_user.is_platform_admin` → 403 Forbidden
   - Error: "Platform admins cannot access customer data"

2. ✅ **Unit Tests** (1 hour)
   - File: `backend/tests/api/test_dependencies.py`
   - Test: Platform admin gets 403
   - Test: Regular user passes through

3. ✅ **Integration Test** (30 min)
   - Test endpoint with `require_customer_user`
   - Verify 403 for admin, 200 for user

**Deliverable**: Backend can block platform admins from customer endpoints

---

### **Day 7-8 (Feb 8-11): Backend - Apply to All Customer Endpoints**

**Owner**: Backend Team (2 devs in parallel)
**Goal**: Apply `require_customer_user` to ALL customer-facing endpoints

#### Tasks (Dev 1):
1. ✅ **Projects Routes** (2 hours)
   - File: `backend/app/api/routes/projects.py`
   - Replace `get_current_user` → `require_customer_user`
   - All endpoints: list, create, get, update, delete

2. ✅ **Gates Routes** (2 hours)
   - File: `backend/app/api/routes/gates.py`
   - All endpoints: list, create, get, update, delete, evaluate

3. ✅ **Evidence Routes** (2 hours)
   - File: `backend/app/api/routes/evidence.py`
   - All endpoints: list, create, get, update, delete, download

#### Tasks (Dev 2):
4. ✅ **Teams Routes** (1.5 hours)
   - File: `backend/app/api/routes/teams.py`
   - All endpoints: list, create, get, update, delete, members

5. ✅ **Organizations Routes** (1.5 hours)
   - File: `backend/app/api/routes/organizations.py`
   - All endpoints: list, create, get, update, delete

6. ✅ **AGENTS.md Routes** (1 hour)
   - File: `backend/app/api/routes/agents.py`
   - All customer endpoints

7. ✅ **Check Runs Routes** (1 hour)
   - File: `backend/app/api/routes/check_runs.py`
   - All customer endpoints

8. ✅ **Dashboard Routes** (1 hour)
   - File: `backend/app/api/routes/dashboard.py`
   - Customer dashboard endpoints

9. ✅ **Analytics Routes** (1 hour)
   - File: `backend/app/api/routes/analytics.py`
   - Customer analytics endpoints (NOT platform analytics)

**Deliverable**: 12+ route files updated, all customer endpoints protected

---

### **Day 9 (Feb 12): Integration & E2E Testing**

**Owner**: QA Team
**Goal**: Comprehensive testing of backend access control

#### Tasks:
1. ✅ **Integration Tests** (3 hours)
   - Test ALL updated endpoints with platform admin token
   - Verify: All return 403 Forbidden
   - Test with regular user token
   - Verify: All return 200 OK (existing behavior)

2. ✅ **E2E API Tests** (2 hours)
   - Automated tests for:
     - `GET /api/v1/projects` as admin → 403
     - `GET /api/v1/gates` as admin → 403
     - `GET /api/v1/evidence` as admin → 403
     - All other customer endpoints

3. ✅ **Performance Benchmarking** (1 hour)
   - Run load tests with `require_customer_user` dependency
   - Verify: <100ms p95 API latency (no degradation)
   - Compare before/after metrics

**Deliverable**: 100% test coverage, all passing, no performance regression

---

### **Day 10 (Feb 13): Documentation & Deployment**

**Owner**: PM + DevOps
**Goal**: Document changes and prepare for production

#### Tasks:
1. ✅ **Update API Documentation** (2 hours)
   - File: `docs/01-planning/05-API-Design/API-Specification.md`
   - Add `is_platform_admin` field to UserProfile schema
   - Document 403 Forbidden behavior for admin on customer endpoints

2. ✅ **Migration Guide** (1 hour)
   - File: `docs/04-build/Migration-Guides/Sprint-88-Platform-Admin-Migration.md`
   - Instructions for existing platform admins
   - What changed, what they can/can't do

3. ✅ **Deployment Checklist** (1 hour)
   - Database migration steps
   - Rollback plan
   - Smoke tests after deployment

4. ✅ **Deploy to Staging** (1 hour)
   - Run migration: `alembic upgrade head`
   - Deploy frontend + backend
   - Smoke test: Admin blocked from `/app`, user works normally

5. ✅ **Security Audit** (1 hour)
   - Manual verification: Platform admin CANNOT access customer data
   - Check all critical routes
   - Generate security report

**Deliverable**: Documentation complete, staging deployed, ready for production

---

## 📋 Detailed Task Breakdown

### Frontend Changes (5 files)

| File | Lines Changed | Task |
|------|---------------|------|
| `frontend/src/components/admin/AdminSidebar.tsx` | -10 | Remove "Back to App" link |
| `frontend/src/app/app/layout.tsx` | +15 | Add route guard (redirect admin to /admin) |
| `frontend/src/app/login/page.tsx` | +10 | Auto-redirect based on role |
| `frontend/src/components/landing/Header.tsx` | +5 | Update "Dashboard" link |
| `frontend/src/lib/types/user.ts` | +1 | Add `is_platform_admin` field |

**Total**: ~41 lines changed

### Backend Changes (13 files)

| File | Lines Changed | Task |
|------|---------------|------|
| `backend/alembic/versions/s88_*.py` | +50 | Migration script |
| `backend/app/models/user.py` | +5 | Add `is_platform_admin` field |
| `backend/app/api/routes/auth.py` | +3 | Update UserProfile schema |
| `backend/app/api/dependencies.py` | +15 | Create `require_customer_user` |
| `backend/app/api/routes/projects.py` | ~20 | Apply dependency |
| `backend/app/api/routes/gates.py` | ~15 | Apply dependency |
| `backend/app/api/routes/evidence.py` | ~15 | Apply dependency |
| `backend/app/api/routes/teams.py` | ~10 | Apply dependency |
| `backend/app/api/routes/organizations.py` | ~10 | Apply dependency |
| `backend/app/api/routes/agents.py` | ~8 | Apply dependency |
| `backend/app/api/routes/check_runs.py` | ~5 | Apply dependency |
| `backend/app/api/routes/dashboard.py` | ~8 | Apply dependency |
| `backend/app/api/routes/analytics.py` | ~5 | Apply dependency |

**Total**: ~169 lines changed

### Test Files (New)

| File | Lines | Purpose |
|------|-------|---------|
| `e2e/admin-role-separation.spec.ts` | ~200 | E2E tests for frontend |
| `backend/tests/api/test_dependencies.py` | ~100 | Unit tests for `require_customer_user` |
| `backend/tests/api/test_admin_access_control.py` | ~300 | Integration tests for all endpoints |

**Total**: ~600 lines new test code

---

## 🚨 Risk Analysis

### High Risk

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Existing platform admins locked out** | 🔴 High | Migration guide + support announcement |
| **Breaking customer workflows** | 🔴 High | 100% backward compatible for customers |
| **Performance degradation** | 🟠 Medium | Benchmark before/after, target <100ms p95 |

### Medium Risk

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Test coverage gaps** | 🟠 Medium | 100+ E2E tests, comprehensive coverage |
| **Documentation outdated** | 🟡 Low | Update all docs on Day 10 |

### Mitigation Strategy

1. **Feature Flag** (optional):
   - `ENABLE_PLATFORM_ADMIN_ISOLATION = true/false`
   - Can disable if critical issues found
   - Default: `true` in production

2. **Rollback Plan**:
   - Database rollback: `alembic downgrade -1` (<2 min)
   - Code rollback: Revert Git commits (<5 min)
   - Total rollback time: <10 minutes

3. **Gradual Rollout**:
   - Day 10: Deploy to staging
   - Day 11: Monitor staging for 24 hours
   - Day 12: Deploy to production (if staging OK)

---

## 🎯 Success Criteria

### Functional Requirements

- [x] Platform admin CANNOT access `/app/*` routes (frontend)
- [x] Platform admin gets 403 on customer API endpoints (backend)
- [x] Regular users unaffected (100% backward compatible)
- [x] Login redirects to correct dashboard based on role
- [x] "Back to App" link removed from admin sidebar

### Non-Functional Requirements

- [x] API latency <100ms p95 (no degradation)
- [x] 100% E2E test coverage for role separation
- [x] Zero security regressions
- [x] Documentation complete and accurate
- [x] Rollback plan tested and ready

### Security Requirements

- [x] 0 platform admins can access customer projects
- [x] 0 platform admins can view customer gates/evidence
- [x] 100% of customer data protected from admin access
- [x] Audit log records all access attempts

---

## 📊 Definition of Done

### Code Quality

- [ ] All code reviewed (2+ approvers)
- [ ] Zero mock implementations
- [ ] 95%+ test coverage (unit + integration)
- [ ] Linting passes (ruff, ESLint, Prettier)
- [ ] Type checking passes (mypy, TypeScript strict)

### Testing

- [ ] 100+ E2E tests passing
- [ ] All integration tests passing
- [ ] Manual smoke tests passing
- [ ] Performance benchmarks meeting targets

### Documentation

- [ ] ADR-030 finalized
- [ ] API docs updated
- [ ] Migration guide complete
- [ ] Deployment checklist ready

### Deployment

- [ ] Staging deployment successful
- [ ] 24-hour monitoring (no errors)
- [ ] Production deployment ready
- [ ] Rollback plan tested

---

## 📅 Sprint Schedule

| Week | Days | Focus |
|------|------|-------|
| **Week 1** | Feb 1-7 | Frontend + Backend foundation |
| **Week 2** | Feb 8-13 | Apply to all endpoints + testing + docs |

### Team Allocation

| Role | Allocation | Tasks |
|------|------------|-------|
| **Frontend Lead** | 3 days | Days 1-3 (UI + routing + tests) |
| **Backend Lead** | 4 days | Days 4-7 (migration + dependency + 3 routes) |
| **Backend Dev** | 2 days | Days 7-8 (remaining 9 routes) |
| **QA Lead** | 2 days | Days 3, 9 (E2E + integration tests) |
| **PM** | 1 day | Day 10 (documentation) |
| **DevOps** | 1 day | Day 10 (deployment + monitoring) |

**Total Effort**: ~50 hours across 6 people

---

## 🔄 Daily Standups

### Questions to Answer:

1. **What did you complete yesterday?**
2. **What will you work on today?**
3. **Any blockers?**
4. **Is the sprint on track?**

### Critical Metrics to Track:

- Files modified (target: 18 files)
- Tests added (target: 100+ tests)
- Tests passing (target: 100%)
- API latency (target: <100ms p95)
- Customer workflows broken (target: 0)

---

## 🚀 Post-Sprint Actions

### Immediate (Feb 14-15)

- [ ] Monitor production for 48 hours
- [ ] Check error logs for 403 Forbidden spikes
- [ ] Verify customer support tickets (should be 0 related to this change)

### Follow-up (Feb 16-28)

- [ ] Customer access grant system (future Sprint 89)
- [ ] Temporary admin access for support tickets
- [ ] Audit log viewer for admin actions

### Long-term (March+)

- [ ] Role-based access control (RBAC) for admins
- [ ] Support staff vs platform admin roles
- [ ] Customer data access request workflow

---

## 📚 References

- **ADR-030**: Platform Admin Role Redesign
- **ADMIN-ROLE-REFACTOR-PLAN.md**: Detailed implementation plan
- **GDPR Article 25**: Privacy by Design
- **SOC 2 CC7.1**: Access Control Requirements
- **AWS IAM Best Practices**: Principle of Least Privilege

---

## ✅ Sprint 88 Approval

- [x] **CTO Approved**: January 21, 2026
- [x] **CEO Approved**: January 21, 2026
- [ ] **Backend Lead Approved**: Pending
- [ ] **Frontend Lead Approved**: Pending
- [ ] **QA Lead Approved**: Pending
- [ ] **PM Approved**: Pending

---

**Sprint Status**: ✅ READY TO START (February 1, 2026)
**Priority**: P0 - Critical Security Fix
**Target Completion**: February 13, 2026 (before soft launch)
**Owner**: CTO + Backend Lead + Frontend Lead
