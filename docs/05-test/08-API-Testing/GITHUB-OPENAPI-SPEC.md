# GitHub API OpenAPI Specification

**Version**: 1.0.0
**Date**: November 28, 2025
**Status**: ACTIVE - Sprint 16 Day 3
**Authority**: Backend Lead + API Architect Approved
**Foundation**: Sprint 15 GitHub Foundation, Sprint 16 Testing Plan
**Framework**: SDLC 6.1.0

---

## Overview

This document describes the GitHub integration API endpoints documented in the OpenAPI specification at `docs/02-Design-Architecture/04-API-Specifications/openapi.yml`.

**OpenAPI Version**: 3.0.3
**Total GitHub Endpoints**: 11
**Total GitHub Schemas**: 14
**Status**: 100% SYNCHRONIZED with Pydantic schemas

---

## Endpoints Summary

| Endpoint | Method | Line # | Description |
|----------|--------|--------|-------------|
| `/github/authorize` | GET | 2572 | Get GitHub OAuth authorization URL |
| `/github/callback` | POST | 2614 | Handle GitHub OAuth callback |
| `/github/status` | GET | 2659 | Get GitHub connection status |
| `/github/disconnect` | DELETE | 2685 | Disconnect GitHub account |
| `/github/repositories` | GET | 2709 | List user's GitHub repositories |
| `/github/repositories/{owner}/{repo}` | GET | 2753 | Get repository details |
| `/github/repositories/{owner}/{repo}/contents` | GET | 2793 | Get repository contents |
| `/github/repositories/{owner}/{repo}/languages` | GET | 2849 | Get repository language breakdown |
| `/github/repositories/{owner}/{repo}/analyze` | GET | 2890 | Analyze repository structure |
| `/github/sync` | POST | 2955 | Sync GitHub repository to project |
| `/github/webhook` | POST | 3000 | Handle GitHub webhook events |

---

## Schemas Summary

| Schema | Line # | Description |
|--------|--------|-------------|
| GitHubOAuthURLResponse | 3686 | OAuth authorization URL response |
| GitHubOAuthCallbackRequest | 3700 | OAuth callback request body |
| GitHubOAuthCallbackResponse | 3713 | OAuth callback response with tokens |
| GitHubConnectionStatus | 3759 | User's GitHub connection status |
| GitHubRepositoryOwner | 3793 | Repository owner information |
| GitHubRepository | 3818 | Repository details |
| GitHubRepositoryListResponse | 3906 | Paginated repository list |
| GitHubRepositoryContents | 3930 | Repository file/directory item |
| GitHubRepositoryLanguages | 3963 | Repository language breakdown |
| GitHubSyncRequest | 3982 | Repository sync request body |
| GitHubSyncResponse | 4005 | Repository sync response |
| GitHubWebhookEvent | 4042 | Normalized webhook event |
| GitHubWebhookResponse | 4074 | Webhook processing response |
| GitHubRateLimitInfo | 4097 | GitHub API rate limit info |

---

## Endpoint Details

### 1. GET /github/authorize

**Purpose**: Generate GitHub OAuth authorization URL for user login/connection.

**Security**: Bearer JWT required

**Query Parameters**:
- `redirect_uri` (optional): Custom redirect URI after OAuth

**Response**: `GitHubOAuthURLResponse`
```json
{
  "authorization_url": "https://github.com/login/oauth/authorize?client_id=abc123&scope=read:user%20user:email%20repo&state=xyz789",
  "state": "xyz789"
}
```

**cURL Example**:
```bash
curl -X GET "http://localhost:8000/api/v1/github/authorize" \
  -H "Authorization: Bearer {token}"
```

---

### 2. POST /github/callback

**Purpose**: Exchange OAuth authorization code for tokens and create/link user.

**Security**: None (public endpoint)

**Request Body**: `GitHubOAuthCallbackRequest`
```json
{
  "code": "abc123def456",
  "state": "xyz789"
}
```

**Response**: `GitHubOAuthCallbackResponse`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "github_connected": true,
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "developer@example.com",
  "name": "Developer Name",
  "avatar_url": "https://avatars.githubusercontent.com/u/12345"
}
```

**cURL Example**:
```bash
curl -X POST http://localhost:8000/api/v1/github/callback \
  -H "Content-Type: application/json" \
  -d '{"code": "abc123def456", "state": "xyz789"}'
```

---

### 3. GET /github/status

**Purpose**: Check if current user has GitHub connected.

**Security**: Bearer JWT required

**Response**: `GitHubConnectionStatus`
```json
{
  "connected": true,
  "github_username": "developer",
  "github_avatar": "https://avatars.githubusercontent.com/u/12345",
  "scopes": ["read:user", "user:email", "repo"],
  "connected_at": "2025-01-01T00:00:00Z",
  "rate_limit": {
    "limit": 5000,
    "remaining": 4999,
    "reset": "2025-01-01T01:00:00Z",
    "used": 1
  }
}
```

**cURL Example**:
```bash
curl -X GET http://localhost:8000/api/v1/github/status \
  -H "Authorization: Bearer {token}"
```

---

### 4. DELETE /github/disconnect

**Purpose**: Disconnect GitHub OAuth account from current user.

**Security**: Bearer JWT required

**Response**: 204 No Content

**cURL Example**:
```bash
curl -X DELETE http://localhost:8000/api/v1/github/disconnect \
  -H "Authorization: Bearer {token}"
```

---

### 5. GET /github/repositories

**Purpose**: List all repositories accessible to authenticated user.

**Security**: Bearer JWT required

**Query Parameters**:
- `page` (optional, default: 1): Page number
- `per_page` (optional, default: 30, max: 100): Items per page

**Response**: `GitHubRepositoryListResponse`
```json
{
  "repositories": [
    {
      "id": 123456789,
      "name": "my-project",
      "full_name": "developer/my-project",
      "description": "A sample project",
      "html_url": "https://github.com/developer/my-project",
      "default_branch": "main",
      "language": "Python",
      "private": false,
      "owner": {
        "login": "developer",
        "id": 12345,
        "type": "User"
      }
    }
  ],
  "total": 25,
  "page": 1,
  "per_page": 30
}
```

**cURL Example**:
```bash
curl -X GET "http://localhost:8000/api/v1/github/repositories?page=1&per_page=30" \
  -H "Authorization: Bearer {token}"
```

---

### 6. GET /github/repositories/{owner}/{repo}

**Purpose**: Get detailed information about a specific repository.

**Security**: Bearer JWT required

**Path Parameters**:
- `owner`: Repository owner (username or organization)
- `repo`: Repository name

**Response**: `GitHubRepository`

**cURL Example**:
```bash
curl -X GET "http://localhost:8000/api/v1/github/repositories/developer/my-project" \
  -H "Authorization: Bearer {token}"
```

---

### 7. GET /github/repositories/{owner}/{repo}/contents

**Purpose**: Get file and directory listing for a repository path.

**Security**: Bearer JWT required

**Path Parameters**:
- `owner`: Repository owner
- `repo`: Repository name

**Query Parameters**:
- `path` (optional, default: ""): Path within repository
- `ref` (optional): Branch/tag/commit SHA

**Response**: Array of `GitHubRepositoryContents`
```json
[
  {
    "name": "main.py",
    "path": "src/main.py",
    "type": "file",
    "size": 1024,
    "sha": "abc123def456",
    "download_url": "https://raw.githubusercontent.com/developer/my-project/main/src/main.py"
  }
]
```

**cURL Example**:
```bash
curl -X GET "http://localhost:8000/api/v1/github/repositories/developer/my-project/contents?path=src" \
  -H "Authorization: Bearer {token}"
```

---

### 8. GET /github/repositories/{owner}/{repo}/languages

**Purpose**: Get language breakdown for a repository.

**Security**: Bearer JWT required

**Response**: `GitHubRepositoryLanguages`
```json
{
  "languages": {
    "Python": 50000,
    "TypeScript": 30000,
    "JavaScript": 10000
  },
  "primary_language": "Python"
}
```

**cURL Example**:
```bash
curl -X GET "http://localhost:8000/api/v1/github/repositories/developer/my-project/languages" \
  -H "Authorization: Bearer {token}"
```

---

### 9. GET /github/repositories/{owner}/{repo}/analyze

**Purpose**: Analyze repository structure, detect project type, recommend policy pack.

**Security**: Bearer JWT required

**Response**:
```json
{
  "project_type": "FastAPI",
  "languages": {
    "Python": 50000,
    "TypeScript": 30000
  },
  "recommended_policy_pack": "standard",
  "stage_mappings": [
    {"folder": "docs/", "stage": "planning"},
    {"folder": "src/", "stage": "development"}
  ]
}
```

**cURL Example**:
```bash
curl -X GET "http://localhost:8000/api/v1/github/repositories/developer/my-project/analyze" \
  -H "Authorization: Bearer {token}"
```

---

### 10. POST /github/sync

**Purpose**: Create SDLC Orchestrator project from GitHub repository.

**Security**: Bearer JWT required

**Request Body**: `GitHubSyncRequest`
```json
{
  "github_repo_id": 123456789,
  "github_repo_full_name": "developer/my-project",
  "project_name": "My Project",
  "auto_setup": true
}
```

**Response**: `GitHubSyncResponse`
```json
{
  "project_id": "550e8400-e29b-41d4-a716-446655440000",
  "project_name": "My Project",
  "project_slug": "my-project",
  "github_repo_id": 123456789,
  "github_repo_full_name": "developer/my-project",
  "sync_status": "synced",
  "synced_at": "2025-01-01T00:00:00Z"
}
```

**cURL Example**:
```bash
curl -X POST http://localhost:8000/api/v1/github/sync \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "github_repo_id": 123456789,
    "github_repo_full_name": "developer/my-project",
    "project_name": "My Project",
    "auto_setup": true
  }'
```

---

### 11. POST /github/webhook

**Purpose**: Process GitHub webhook events (push, pull_request, issues, etc.).

**Security**: HMAC-SHA256 signature validation (X-Hub-Signature-256 header)

**Headers**:
- `X-GitHub-Event`: Event type (push, pull_request, etc.)
- `X-Hub-Signature-256`: HMAC SHA-256 signature

**Request Body**: GitHub webhook payload (varies by event type)

**Response**: `GitHubWebhookResponse`
```json
{
  "received": true,
  "event_type": "push",
  "repository": "developer/my-project",
  "message": "Push event processed: 3 commits to main"
}
```

**cURL Example**:
```bash
curl -X POST http://localhost:8000/api/v1/github/webhook \
  -H "Content-Type: application/json" \
  -H "X-GitHub-Event: push" \
  -H "X-Hub-Signature-256: sha256=..." \
  -d '{...webhook payload...}'
```

---

## Schema Synchronization

All OpenAPI schemas are synchronized with Pydantic models in `backend/app/schemas/github.py`:

| Pydantic Model | OpenAPI Schema | Sync Status |
|----------------|----------------|-------------|
| GitHubOAuthURLResponse | GitHubOAuthURLResponse | ✅ SYNC |
| GitHubOAuthCallbackRequest | GitHubOAuthCallbackRequest | ✅ SYNC |
| GitHubOAuthCallbackResponse | GitHubOAuthCallbackResponse | ✅ SYNC |
| GitHubConnectionStatus | GitHubConnectionStatus | ✅ SYNC |
| GitHubRepositoryOwner | GitHubRepositoryOwner | ✅ SYNC |
| GitHubRepository | GitHubRepository | ✅ SYNC |
| GitHubRepositoryListResponse | GitHubRepositoryListResponse | ✅ SYNC |
| GitHubRepositoryContents | GitHubRepositoryContents | ✅ SYNC |
| GitHubRepositoryLanguages | GitHubRepositoryLanguages | ✅ SYNC |
| GitHubSyncRequest | GitHubSyncRequest | ✅ SYNC |
| GitHubSyncResponse | GitHubSyncResponse | ✅ SYNC |
| GitHubWebhookEvent | GitHubWebhookEvent | ✅ SYNC |
| GitHubWebhookResponse | GitHubWebhookResponse | ✅ SYNC |
| GitHubRateLimitInfo | GitHubRateLimitInfo | ✅ SYNC |

---

## Contract Testing

The OpenAPI spec serves as the source of truth for API contracts:

1. **FastAPI Auto-Generation**: Routes generate OpenAPI from Pydantic models
2. **Integration Tests**: Validate response schemas against OpenAPI
3. **Frontend TypeScript**: Generate types from OpenAPI spec
4. **Bruno Collections**: Import OpenAPI for manual testing

---

## Related Documents

- [openapi.yml](../../../02-Design-Architecture/04-API-Specifications/openapi.yml) - Full OpenAPI specification
- [github.py](../../../../backend/app/schemas/github.py) - Pydantic schemas
- [GITHUB-SERVICE-UNIT-TESTS.md](../03-Unit-Testing/GITHUB-SERVICE-UNIT-TESTS.md) - Unit test documentation
- [GITHUB-OAUTH-INTEGRATION-TESTS.md](../04-Integration-Testing/GITHUB-OAUTH-INTEGRATION-TESTS.md) - Integration test documentation

---

*SDLC Orchestrator - First Governance-First Platform on SDLC 6.1.0. Zero Mock Policy enforced.*
