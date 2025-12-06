# GitHub OAuth Integration Tests

**Version**: 1.0.0
**Date**: November 28, 2025
**Status**: ACTIVE - Sprint 16 Day 2
**Authority**: Backend Lead + QA Lead Approved
**Foundation**: Sprint 16 Testing Plan
**Framework**: SDLC 4.9 Complete Lifecycle

---

## Overview

Integration tests for GitHub OAuth API endpoints, testing the complete OAuth flow from authorization to token exchange, repository listing, and webhook handling.

**Test File**: `tests/integration/test_github_oauth.py`
**Total Tests**: 25+
**Coverage Target**: 90%+
**Status**: IN PROGRESS

---

## Endpoints Covered

| Endpoint | Method | Tests | Description |
|----------|--------|-------|-------------|
| /api/v1/github/authorize | GET | 3 | OAuth authorization URL |
| /api/v1/github/callback | POST | 4 | OAuth code exchange |
| /api/v1/github/status | GET | 2 | Connection status |
| /api/v1/github/disconnect | POST | 2 | Disconnect GitHub |
| /api/v1/github/repositories | GET | 3 | List repositories |
| /api/v1/github/repositories/{owner}/{repo} | GET | 2 | Repository details |
| /api/v1/github/repositories/{owner}/{repo}/contents | GET | 2 | Repository contents |
| /api/v1/github/repositories/{owner}/{repo}/languages | GET | 1 | Language breakdown |
| /api/v1/github/sync | POST | 2 | Sync repo to project |
| /api/v1/github/webhook | POST | 4 | Webhook handling |

**Total Endpoints**: 10
**Total Tests**: 25+

---

## Test Classes Summary

### 1. TestGitHubAuthorize

Tests OAuth authorization URL generation:

| Test | Scenario | Expected |
|------|----------|----------|
| test_authorize_returns_oauth_url | Get auth URL | 200, returns URL + state |
| test_authorize_with_custom_redirect_uri | Custom redirect | URL includes redirect_uri |
| test_authorize_without_auth_returns_401 | No auth header | 401 Unauthorized |

### 2. TestGitHubCallback

Tests OAuth code exchange:

| Test | Scenario | Expected |
|------|----------|----------|
| test_callback_success_new_user | Valid code | 200, JWT tokens returned |
| test_callback_invalid_code | Invalid code | 400/401 error |
| test_callback_missing_code | No code param | 422 validation error |
| test_callback_missing_state | No state param | 422 validation error |

### 3. TestGitHubStatus

Tests connection status:

| Test | Scenario | Expected |
|------|----------|----------|
| test_status_not_connected | User without GitHub | 200, connected=false |
| test_status_without_auth_returns_401 | No auth | 401 Unauthorized |

### 4. TestGitHubDisconnect

Tests GitHub disconnection:

| Test | Scenario | Expected |
|------|----------|----------|
| test_disconnect_without_connection | No GitHub connected | 200/404 |
| test_disconnect_without_auth_returns_401 | No auth | 401 Unauthorized |

### 5. TestGitHubRepositories

Tests repository listing:

| Test | Scenario | Expected |
|------|----------|----------|
| test_list_repositories_success | Connected user | 200, list of repos |
| test_list_repositories_without_auth | No auth | 401 Unauthorized |
| test_list_repositories_with_pagination | page=1, per_page=10 | 200, paginated results |

### 6. TestGitHubRepositoryDetails

Tests repository details:

| Test | Scenario | Expected |
|------|----------|----------|
| test_get_repository_details | Valid owner/repo | 200, repo details |
| test_get_repository_without_auth | No auth | 401 Unauthorized |

### 7. TestGitHubRepositoryContents

Tests repository file listing:

| Test | Scenario | Expected |
|------|----------|----------|
| test_get_repository_contents | Root path | 200, file list |
| test_get_repository_contents_with_path | path=src | 200, subdirectory contents |

### 8. TestGitHubRepositoryLanguages

Tests language breakdown:

| Test | Scenario | Expected |
|------|----------|----------|
| test_get_repository_languages | Valid repo | 200, language percentages |

### 9. TestGitHubSync

Tests repository sync:

| Test | Scenario | Expected |
|------|----------|----------|
| test_sync_repository_to_project | Valid repo | 200/201, project created |
| test_sync_without_auth_returns_401 | No auth | 401 Unauthorized |

### 10. TestGitHubWebhook

Tests webhook handling:

| Test | Scenario | Expected |
|------|----------|----------|
| test_webhook_push_event | Push event | 200, event processed |
| test_webhook_pull_request_event | PR event | 200, event processed |
| test_webhook_missing_signature | No X-Hub-Signature | 400/401 error |
| test_webhook_invalid_signature | Invalid HMAC | 401/403 error |

### 11. TestGitHubRateLimit

Tests rate limit handling:

| Test | Scenario | Expected |
|------|----------|----------|
| test_rate_limit_info | Get rate limit | 200, limit info |

### 12. TestGitHubErrorHandling

Tests API error handling:

| Test | Scenario | Expected |
|------|----------|----------|
| test_github_api_error_handling | GitHub API down | 500/503 error |
| test_github_rate_limit_error_handling | Rate limit exceeded | 429 error |

---

## Test Fixtures

```python
@pytest.fixture
def mock_github_token_response():
    """Mock successful GitHub token exchange response."""
    return {
        "access_token": "gho_mock_access_token_12345",
        "token_type": "bearer",
        "scope": "repo,read:user,user:email",
    }

@pytest.fixture
def mock_github_user_response():
    """Mock GitHub user info response."""
    return {
        "id": 12345678,
        "login": "testuser",
        "name": "Test User",
        "email": "testuser@example.com",
    }

@pytest.fixture
def mock_github_repositories():
    """Mock GitHub repositories list response."""
    return [
        {
            "id": 1001,
            "name": "sdlc-project",
            "full_name": "testuser/sdlc-project",
            "language": "Python",
        },
    ]
```

---

## Zero Mock Policy Compliance

Per SDLC 4.9 Zero Mock Policy:

**Mocked**: External GitHub API calls only
- `github_service.exchange_code_for_token()`
- `github_service.validate_access_token()`
- `github_service.list_repositories()`
- `github_service.get_repository()`
- `github_service.get_repository_contents()`
- `github_service.get_repository_languages()`

**NOT Mocked**:
- Real PostgreSQL database (test database)
- Real FastAPI application
- Real HTTP client (httpx.AsyncClient)
- Real JWT token generation
- Real request/response handling

---

## Running Tests

```bash
# Run all GitHub OAuth integration tests
PYTHONPATH="$PWD/backend" pytest tests/integration/test_github_oauth.py -v

# Run specific test class
PYTHONPATH="$PWD/backend" pytest tests/integration/test_github_oauth.py::TestGitHubCallback -v

# Run with coverage
PYTHONPATH="$PWD/backend" pytest tests/integration/test_github_oauth.py --cov=app.api.routes.github --cov-report=html

# Run marked tests only
PYTHONPATH="$PWD/backend" pytest -m "github" -v
```

---

## Test Requirements

### Prerequisites

1. **PostgreSQL Test Database**: Running on localhost:5432
2. **Test User**: Created via `test_user` fixture
3. **Auth Headers**: Generated via `auth_headers` fixture

### Environment Variables

```bash
TEST_DATABASE_URL=postgresql+asyncpg://sdlc_user:changeme_secure_password@localhost:5432/sdlc_orchestrator_test
GITHUB_CLIENT_ID=test_client_id
GITHUB_CLIENT_SECRET=test_client_secret
GITHUB_WEBHOOK_SECRET=test_webhook_secret
```

---

## Quality Metrics

| Metric | Target | Achieved | Status |
|--------|--------|----------|--------|
| Total Tests | 20+ | 25+ | EXCEEDS |
| Pass Rate | 100% | TBD | PENDING |
| Endpoint Coverage | 100% | 100% | PASS |
| Zero Mock | 100% | 100% | PASS |

---

## Related Documents

- [GITHUB-SERVICE-UNIT-TESTS.md](../03-Unit-Testing/GITHUB-SERVICE-UNIT-TESTS.md)
- [SPRINT-16-TESTING-DOCUMENTATION.md](../../../08-Team-Management/04-Sprint-Management/SPRINT-16-TESTING-DOCUMENTATION.md)
- [github.py](../../../../backend/app/api/routes/github.py)

---

*SDLC Orchestrator - First Governance-First Platform on SDLC 4.9. Zero Mock Policy enforced.*
