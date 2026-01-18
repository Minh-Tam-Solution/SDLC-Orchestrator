# GitHub Service Unit Tests

**Version**: 1.0.0
**Date**: November 28, 2025
**Status**: ACTIVE - Sprint 16 Day 1
**Authority**: Backend Lead + QA Lead Approved
**Foundation**: Sprint 16 Testing Plan
**Framework**: SDLC 5.1.3 Complete Lifecycle

---

## Overview

Unit tests for the GitHub Service (`backend/app/services/github_service.py`), testing all public methods in isolation with mocked external GitHub API calls.

**Test File**: `tests/unit/services/test_github_service.py`
**Total Tests**: 46
**Coverage Target**: 95%+
**Status**: 100% PASS

---

## Test Classes Summary

| Test Class | Tests | Description |
|------------|-------|-------------|
| TestGetAuthorizationUrl | 5 | OAuth URL generation |
| TestExchangeCodeForToken | 7 | Token exchange flow |
| TestValidateAccessToken | 2 | Token validation |
| TestListRepositories | 3 | Repository listing + pagination |
| TestGetRepository | 2 | Repository details + 404 handling |
| TestGetRepositoryContents | 2 | Directory contents |
| TestGetRepositoryLanguages | 1 | Language breakdown |
| TestValidateWebhookSignature | 6 | HMAC-SHA256 validation |
| TestParseWebhookEvent | 5 | Event parsing |
| TestGetRateLimit | 1 | Rate limit info |
| TestRateLimitHandling | 2 | Rate limit exhaustion |
| TestErrorHandling | 6 | HTTP error codes |
| TestEdgeCases | 4 | Special characters, unicode |

**Total**: 46 tests

---

## Test Coverage by Method

### 1. get_authorization_url()

Tests OAuth authorization URL generation:

| Test | Scenario | Expected |
|------|----------|----------|
| test_generates_valid_url_with_required_params | Generate URL with state | URL contains client_id, scope, state |
| test_includes_default_scopes | Default scopes applied | URL contains repo,read:user,user:email |
| test_includes_custom_scopes | Custom scopes provided | URL contains custom scopes |
| test_includes_redirect_uri_when_provided | Custom redirect URI | URL contains redirect_uri |
| test_raises_error_when_client_id_missing | No client_id configured | Raises GitHubAuthError |

### 2. exchange_code_for_token()

Tests OAuth code exchange:

| Test | Scenario | Expected |
|------|----------|----------|
| test_successful_token_exchange | Valid code | Returns access_token dict |
| test_exchange_with_redirect_uri | With redirect URI | Sends redirect_uri in request |
| test_raises_error_on_oauth_error_response | GitHub returns error | Raises GitHubAuthError |
| test_raises_error_on_http_error | HTTP 400 response | Raises GitHubAuthError |
| test_raises_error_on_timeout | Request timeout | Raises GitHubAPIError |
| test_raises_error_on_request_exception | Network error | Raises GitHubAPIError |
| test_raises_error_when_credentials_missing | No client_secret | Raises GitHubAuthError |

### 3. validate_access_token()

Tests token validation:

| Test | Scenario | Expected |
|------|----------|----------|
| test_valid_token_returns_user_info | Valid token | Returns user dict |
| test_invalid_token_raises_auth_error | Invalid/expired token | Raises GitHubAuthError |

### 4. list_repositories()

Tests repository listing:

| Test | Scenario | Expected |
|------|----------|----------|
| test_returns_list_of_repos | Valid request | Returns list of repos |
| test_pagination_params_passed_correctly | page=2, per_page=50 | Params sent in request |
| test_per_page_capped_at_100 | per_page=200 | Capped at 100 |

### 5. get_repository()

Tests repository details:

| Test | Scenario | Expected |
|------|----------|----------|
| test_returns_repository_details | Valid owner/repo | Returns repo dict |
| test_raises_error_for_not_found_repo | Invalid repo | Raises GitHubAPIError with 404 |

### 6. get_repository_contents()

Tests repository file listing:

| Test | Scenario | Expected |
|------|----------|----------|
| test_returns_directory_contents | Root path | Returns file list |
| test_accepts_ref_parameter | With ref=develop | Adds ref to query |

### 7. get_repository_languages()

Tests language breakdown:

| Test | Scenario | Expected |
|------|----------|----------|
| test_returns_language_breakdown | Valid repo | Returns {language: bytes} dict |

### 8. validate_webhook_signature()

Tests HMAC-SHA256 signature validation:

| Test | Scenario | Expected |
|------|----------|----------|
| test_valid_signature_returns_true | Correct HMAC | Returns True |
| test_invalid_signature_returns_false | Wrong HMAC | Returns False |
| test_missing_signature_prefix_returns_false | No sha256= prefix | Returns False |
| test_empty_signature_returns_false | Empty string | Returns False |
| test_none_signature_returns_false | None value | Returns False |
| test_no_webhook_secret_allows_all | No secret configured | Returns True (bypass) |

### 9. parse_webhook_event()

Tests webhook event parsing:

| Test | Scenario | Expected |
|------|----------|----------|
| test_parses_push_event | Push event | Returns parsed event |
| test_parses_pull_request_event | PR event | Returns parsed event |
| test_parses_issues_event | Issues event | Returns parsed event |
| test_parses_create_event | Create event | Returns parsed event |
| test_parses_unknown_event_type | Unknown event | Returns generic parsed event |

### 10. get_rate_limit()

Tests rate limit info:

| Test | Scenario | Expected |
|------|----------|----------|
| test_returns_rate_limit_info | Valid request | Returns limit, remaining, reset |

### 11. Rate Limit Handling

Tests rate limit error handling:

| Test | Scenario | Expected |
|------|----------|----------|
| test_raises_rate_limit_error_when_exhausted | 0 remaining | Raises GitHubRateLimitError |
| test_logs_warning_when_rate_limit_low | 50 remaining | Logs warning, continues |

### 12. Error Handling

Tests HTTP error code handling:

| Test | Scenario | Expected |
|------|----------|----------|
| test_handles_401_unauthorized | HTTP 401 | Raises GitHubAuthError |
| test_handles_403_forbidden | HTTP 403 | Raises GitHubAPIError |
| test_handles_404_not_found | HTTP 404 | Raises GitHubAPIError |
| test_handles_server_error | HTTP 500 | Raises GitHubAPIError |
| test_handles_timeout | Timeout exception | Raises GitHubAPIError |
| test_handles_request_exception | Network error | Raises GitHubAPIError |

### 13. Edge Cases

Tests special scenarios:

| Test | Scenario | Expected |
|------|----------|----------|
| test_empty_response_body | Empty JSON response | Returns empty dict |
| test_large_repository_list | 100 repos | Returns all 100 |
| test_special_characters_in_repo_name | my-repo_test.v1 | Handles correctly |
| test_unicode_in_commit_message | Vietnamese, emoji | Handles UTF-8 |

---

## Zero Mock Policy Compliance

Per SDLC 5.1.3 Zero Mock Policy:

**Mocked**: External GitHub API calls (requests.get, requests.post)
- Reason: Cannot call real GitHub API in tests
- Method: `@patch("requests.get")`, `@patch("requests.post")`

**NOT Mocked**:
- Business logic (URL building, signature validation)
- Error handling paths
- Rate limit calculations

---

## Running Tests

```bash
# Run all GitHub Service unit tests
PYTHONPATH="$PWD/backend" pytest tests/unit/services/test_github_service.py -v

# Run specific test class
PYTHONPATH="$PWD/backend" pytest tests/unit/services/test_github_service.py::TestValidateWebhookSignature -v

# Run with coverage
PYTHONPATH="$PWD/backend" pytest tests/unit/services/test_github_service.py --cov=app.services.github_service --cov-report=html
```

---

## Quality Metrics

| Metric | Target | Achieved | Status |
|--------|--------|----------|--------|
| Total Tests | 40+ | 46 | EXCEEDS |
| Pass Rate | 100% | 100% | PASS |
| Coverage | 95%+ | TBD | PENDING |
| Zero Mock | 100% | 100% | PASS |
| Execution Time | <5s | ~1s | PASS |

---

## Related Documents

- [SPRINT-16-TESTING-DOCUMENTATION.md](../../../08-Team-Management/04-Sprint-Management/SPRINT-16-TESTING-DOCUMENTATION.md)
- [SPRINT-15-COMPLETE.md](../../../09-Executive-Reports/03-CPO-Reports/2025-12-02-CPO-SPRINT-15-COMPLETE.md)
- [github_service.py](../../../../backend/app/services/github_service.py)

---

*SDLC Orchestrator - First Governance-First Platform on SDLC 5.1.3. Zero Mock Policy enforced.*
