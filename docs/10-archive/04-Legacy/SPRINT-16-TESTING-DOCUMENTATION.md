# Sprint 16: Testing & Documentation
## GitHub Integration Testing + Documentation Completion

**Version**: 1.0.0
**Date**: December 3, 2025
**Status**: 🔄 **IN PROGRESS**
**Authority**: Backend Lead + QA Lead + Frontend Lead
**Foundation**: Sprint 15 Complete (GitHub Foundation + G6 UX)
**Framework**: SDLC 6.1.0

---

## 🎯 Sprint 16 Overview

**Sprint Goal**: Complete testing coverage for GitHub integration and finalize documentation

**Duration**: 5 days (Dec 3-7, 2025)

**Prerequisites**: Sprint 15 complete (GitHub Service, API Routes, Onboarding Wizard)

---

## 📋 Sprint 16 Backlog

### Day 1: Unit Tests for GitHub Service ⏳

**Target File**: `tests/unit/services/test_github_service.py`

**Test Cases**:
1. `test_generate_oauth_url` - OAuth URL generation with state parameter
2. `test_exchange_code_for_token_success` - Code exchange with valid code
3. `test_exchange_code_for_token_failure` - Code exchange with invalid code
4. `test_get_user_repositories` - List user repositories
5. `test_get_repository_details` - Get single repository info
6. `test_get_repository_contents` - Get repository file tree
7. `test_get_repository_languages` - Get language breakdown
8. `test_validate_webhook_signature` - HMAC signature validation
9. `test_store_oauth_token` - Token storage with encryption
10. `test_refresh_oauth_token` - Token refresh flow

**Acceptance Criteria**:
- ✅ 95%+ coverage for `github_service.py`
- ✅ All edge cases covered (rate limits, network errors, invalid tokens)
- ✅ Zero Mock Policy compliant (mock external APIs only)

---

### Day 2: Integration Tests for OAuth Flow ⏳

**Target File**: `tests/integration/test_github_oauth.py`

**Test Cases**:
1. `test_oauth_authorize_redirect` - GET /github/authorize returns redirect URL
2. `test_oauth_callback_success` - POST /github/callback with valid code
3. `test_oauth_callback_invalid_code` - POST /github/callback with invalid code
4. `test_oauth_callback_missing_state` - POST /github/callback without state
5. `test_github_status_connected` - GET /github/status for connected user
6. `test_github_status_not_connected` - GET /github/status for new user
7. `test_github_disconnect` - POST /github/disconnect removes OAuth account
8. `test_repository_list` - GET /github/repositories returns repos
9. `test_repository_details` - GET /github/repositories/{owner}/{repo}
10. `test_repository_sync` - POST /github/sync creates project

**Acceptance Criteria**:
- ✅ All 11 GitHub endpoints tested
- ✅ Real PostgreSQL + Redis in tests (Zero Mock Policy)
- ✅ 90%+ coverage for `github.py` routes

---

### Day 3: Update OpenAPI Spec ⏳

**Target File**: `docs/02-Design-Architecture/openapi.yml`

**New Endpoints to Document**:
```yaml
/github/authorize:
  get:
    summary: Generate GitHub OAuth authorization URL
    responses:
      200: { url: string, state: string }

/github/callback:
  post:
    summary: Handle GitHub OAuth callback
    requestBody: { code: string, state: string }
    responses:
      200: { access_token, refresh_token, user }
      400: Invalid code or state

/github/status:
  get:
    summary: Check GitHub connection status
    responses:
      200: { connected: boolean, username: string }

/github/disconnect:
  post:
    summary: Disconnect GitHub OAuth account
    responses:
      200: { success: true }

/github/repositories:
  get:
    summary: List user's GitHub repositories
    responses:
      200: { repositories: Repository[] }

/github/repositories/{owner}/{repo}:
  get:
    summary: Get repository details
    responses:
      200: Repository

/github/repositories/{owner}/{repo}/contents:
  get:
    summary: Get repository file tree
    responses:
      200: { contents: FileTreeNode[] }

/github/repositories/{owner}/{repo}/languages:
  get:
    summary: Get repository language breakdown
    responses:
      200: { languages: Record<string, number> }

/github/repositories/{owner}/{repo}/analyze:
  post:
    summary: Analyze repository for SDLC configuration
    responses:
      200: { project_type, suggested_policy_pack, stage_mappings }

/github/sync:
  post:
    summary: Sync GitHub repository to SDLC project
    requestBody: { repo_id, repo_full_name }
    responses:
      200: Project

/github/webhook:
  post:
    summary: Handle GitHub webhook events
    responses:
      200: { processed: true }
```

**Acceptance Criteria**:
- ✅ All 11 GitHub endpoints documented
- ✅ Request/response schemas defined
- ✅ Error codes documented (400, 401, 403, 404, 500)
- ✅ Examples provided

---

### Day 4: Background Sync Job ⏳

**Target Files**:
- `backend/app/tasks/github_sync_task.py` (new)
- `backend/app/api/routes/github.py` (update)

**Features**:
1. **Periodic Sync Job** (every 5 minutes):
   - Fetch active projects with GitHub connection
   - Check for new commits, PRs, issues
   - Update project sync_status and synced_at

2. **Webhook Processing** (on event):
   - Handle push events → Update commit count
   - Handle PR events → Collect evidence
   - Handle issue events → Track requirements

3. **Rate Limit Management**:
   - Track remaining API calls
   - Backoff when rate limited
   - Priority queue (active projects first)

**Implementation Options**:
- **Option A**: FastAPI BackgroundTasks (simple, in-process)
- **Option B**: Celery + Redis (scalable, distributed)

**Recommendation**: FastAPI BackgroundTasks for MVP (simpler deployment)

**Acceptance Criteria**:
- ✅ Auto-sync every 5 minutes for active projects
- ✅ Webhook events processed within 30 seconds
- ✅ Rate limit handling (no 429 errors)
- ✅ Sync status updated in database

---

### Day 5: Polish & Documentation ⏳

**Target Files**:
- `docs/03-Development-Implementation/GITHUB-INTEGRATION-GUIDE.md` (new)
- `docs/08-Team-Management/BETA-TEAM-ONBOARDING-GUIDE.md` (update)
- `PROJECT-STATUS.md` (update)

**Documentation Tasks**:

1. **GitHub Integration Guide** (developer-focused):
   - OAuth App setup instructions
   - API endpoint reference
   - Webhook configuration
   - Troubleshooting guide

2. **Beta Team Onboarding Update**:
   - Add GitHub connection steps
   - Update screenshots for onboarding wizard
   - Add FAQ for GitHub integration

3. **Project Status Update**:
   - Mark Sprint 16 complete
   - Update metrics (test coverage, API count)
   - Set next milestone (Sprint 17)

**Acceptance Criteria**:
- ✅ GitHub Integration Guide complete (500+ lines)
- ✅ Beta Team Guide updated with GitHub steps
- ✅ PROJECT-STATUS.md reflects Sprint 16 completion

---

## 📊 Success Metrics

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| Unit Test Coverage (GitHub Service) | 95% | 0% | ⏳ |
| Integration Test Coverage (GitHub Routes) | 90% | 0% | ⏳ |
| OpenAPI Endpoints Documented | 11/11 | 0/11 | ⏳ |
| Background Sync Job | Working | Not Started | ⏳ |
| Documentation Complete | 100% | 70% | ⏳ |

---

## 🔧 Technical Implementation

### Test Framework Setup

```python
# tests/conftest.py additions
@pytest.fixture
def mock_github_api():
    """Mock GitHub API responses for unit tests."""
    with respx.mock:
        respx.get("https://api.github.com/user").mock(return_value=Response(200, json={
            "id": 12345,
            "login": "testuser",
            "avatar_url": "https://avatars.githubusercontent.com/u/12345"
        }))
        yield

@pytest.fixture
def github_oauth_state(db: Session, test_user: User):
    """Create OAuth state for testing."""
    state = secrets.token_urlsafe(32)
    # Store state in Redis with 10 min TTL
    return state
```

### Background Task Pattern

```python
# backend/app/tasks/github_sync_task.py
from fastapi import BackgroundTasks

async def sync_github_project(project_id: UUID, db: Session):
    """Sync a single project's GitHub data."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project or not project.github_repo_id:
        return

    github = GitHubService(db)
    try:
        # Fetch latest repo data
        repo = await github.get_repository(project.github_repo_full_name)

        # Update project
        project.github_sync_status = "synced"
        project.github_synced_at = datetime.utcnow()
        db.commit()
    except GitHubRateLimitError:
        project.github_sync_status = "rate_limited"
        db.commit()
```

---

## 🚨 Risk Assessment

### Low Risk ✅
- Unit test implementation (straightforward mocking)
- OpenAPI documentation (schema generation)

### Medium Risk ⚠️
- OAuth integration tests (requires mock OAuth server)
- Background sync job (timing issues, race conditions)

### Mitigation
- Use `respx` for HTTP mocking in tests
- Add retry logic with exponential backoff
- Implement sync lock to prevent duplicate runs

---

## 📅 Sprint 16 Schedule

| Day | Date | Focus | Owner |
|-----|------|-------|-------|
| Day 1 | Dec 3 | Unit Tests (GitHub Service) | QA Lead |
| Day 2 | Dec 4 | Integration Tests (OAuth) | QA Lead |
| Day 3 | Dec 5 | OpenAPI Spec Update | Backend Lead |
| Day 4 | Dec 6 | Background Sync Job | Backend Lead |
| Day 5 | Dec 7 | Documentation Polish | PM |

---

## ✅ Definition of Done

Sprint 16 is complete when:

1. ✅ Unit tests for GitHub Service: 95%+ coverage
2. ✅ Integration tests for GitHub routes: 90%+ coverage
3. ✅ OpenAPI spec updated with all 11 GitHub endpoints
4. ✅ Background sync job working (5-min interval)
5. ✅ GitHub Integration Guide created
6. ✅ Beta Team Guide updated
7. ✅ All tests passing in CI/CD
8. ✅ Zero Mock Policy compliance verified

---

**Sprint 16 Status**: 🔄 **IN PROGRESS** (Day 1 starting)

**Created By**: PM + Backend Lead + QA Lead
**Date**: December 3, 2025
**Framework**: SDLC 6.1.0

---

*SDLC Orchestrator - First Governance-First Platform on SDLC 6.1.0. Zero Mock Policy enforced.*
