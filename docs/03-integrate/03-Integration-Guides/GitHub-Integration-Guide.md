# GitHub Integration Guide

**Version**: 1.0.0
**Sprint**: 129 - GitHub Project Onboarding
**Status**: ACTIVE
**Last Updated**: January 31, 2026

---

## Overview

This guide covers integrating GitHub repositories with SDLC Orchestrator for automated compliance tracking, gap analysis, and governance features.

### Prerequisites

- SDLC Orchestrator account with team membership
- GitHub account with repository access
- Repository owner or admin permissions (for GitHub App installation)

---

## Integration Methods

SDLC Orchestrator supports three integration methods:

| Method | Best For | Authentication |
|--------|----------|----------------|
| **VS Code Extension** | Daily development workflow | OAuth + GitHub App |
| **CLI (`sdlcctl`)** | CI/CD pipelines, automation | API Token + GitHub App |
| **Web Dashboard** | Project management, reporting | OAuth + GitHub App |

---

## 1. VS Code Extension Integration

### Step 1: Install the Extension

```bash
# From VS Code Marketplace
ext install sdlc-orchestrator.sdlc-orchestrator

# Or from VSIX file
code --install-extension sdlc-orchestrator-1.2.3.vsix
```

### Step 2: Connect GitHub Repository

1. Open Command Palette (`Cmd+Shift+P` / `Ctrl+Shift+P`)
2. Run **"SDLC: Connect GitHub Repository"**
3. Select your GitHub account/organization
4. Choose the repository to connect
5. Wait for clone and gap analysis to complete

### Available Commands

| Command | Description |
|---------|-------------|
| `SDLC: Connect GitHub Repository` | Link a repository to current project |
| `SDLC: Disconnect GitHub` | Unlink the connected repository |
| `SDLC: Sync GitHub` | Trigger manual sync/clone |
| `SDLC: Scan GitHub Repository` | Run structure scan on repository |

### Status Bar

The extension shows GitHub connection status in the status bar:
- `$(github) owner/repo` - Connected and synced
- `$(github) Not Connected` - No repository linked (click to connect)

---

## 2. CLI Integration (`sdlcctl`)

### Installation

```bash
# Install via pip
pip install sdlcctl

# Or from source
cd backend/sdlcctl && pip install -e .
```

### Initialize with GitHub Repository

```bash
# Basic usage (owner/repo format)
sdlcctl init my-project --github owner/repo --tier professional

# With HTTPS URL
sdlcctl init my-project --github https://github.com/owner/repo

# With SSH URL
sdlcctl init my-project --github git@github.com:owner/repo.git

# Skip cloning (link only)
sdlcctl init my-project --github owner/repo --no-clone

# Non-interactive mode
sdlcctl init my-project --github owner/repo --tier standard --no-interactive
```

### Supported Repository Formats

The `--github` flag accepts three formats:

```bash
# 1. Simple format (recommended)
--github owner/repo

# 2. HTTPS URL
--github https://github.com/owner/repo
--github https://github.com/owner/repo.git

# 3. SSH URL
--github git@github.com:owner/repo.git
```

### Environment Variables

```bash
# API endpoint (default: http://localhost:8000/api/v1)
export SDLC_API_URL=https://sdlc.example.com/api/v1

# Authentication token
export SDLC_API_TOKEN=your-api-token
```

---

## 3. GitHub App Installation

### Why GitHub App?

SDLC Orchestrator uses a GitHub App for:
- **Fine-grained permissions** - Only request what's needed
- **Installation-based access** - Per-organization control
- **Webhook events** - Real-time sync on push/PR
- **Audit trail** - Track all access through GitHub

### Installation Steps

1. **Navigate to GitHub App page**:
   ```
   https://github.com/apps/sdlc-orchestrator/installations/new
   ```

2. **Select account** (personal or organization)

3. **Choose repositories**:
   - "All repositories" - Full access to current and future repos
   - "Only select repositories" - Choose specific repos (recommended)

4. **Review permissions**:
   - Repository contents: Read-only
   - Metadata: Read-only
   - Pull requests: Read & write (for comments)

5. **Click "Install"**

### Verify Installation

```bash
# Via CLI
sdlcctl init test-project --github owner/repo --tier lite

# Check for "GitHub App installed" message
```

---

## 4. API Endpoints

### List Installations

```bash
GET /api/v1/github/installations
Authorization: Bearer <token>

Response:
{
  "installations": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "installation_id": 12345678,
      "account_type": "Organization",
      "account_login": "acme-corp",
      "status": "active",
      "installed_at": "2026-01-30T10:00:00Z"
    }
  ]
}
```

### List Repositories

```bash
GET /api/v1/github/installations/{installation_id}/repositories
Authorization: Bearer <token>

Response:
{
  "total_count": 5,
  "repositories": [
    {
      "id": 987654321,
      "name": "sdlc-orchestrator",
      "full_name": "acme-corp/sdlc-orchestrator",
      "owner": "acme-corp",
      "private": false,
      "html_url": "https://github.com/acme-corp/sdlc-orchestrator",
      "default_branch": "main"
    }
  ]
}
```

### Link Repository to Project

```bash
POST /api/v1/github/projects/{project_id}/link
Authorization: Bearer <token>
Content-Type: application/json

{
  "installation_id": "550e8400-e29b-41d4-a716-446655440000",
  "owner": "acme-corp",
  "repo": "sdlc-orchestrator"
}

Response:
{
  "id": "repo-uuid",
  "github_repo_id": 987654321,
  "clone_status": "pending"
}
```

### Trigger Clone

```bash
POST /api/v1/github/projects/{project_id}/clone
Authorization: Bearer <token>
Content-Type: application/json

{
  "shallow": true
}

Response:
{
  "status": "cloning",
  "message": "Clone started in background"
}
```

### Scan Repository

```bash
GET /api/v1/github/projects/{project_id}/scan
Authorization: Bearer <token>

Response:
{
  "folders": ["docs", "src", "tests"],
  "files": ["README.md", "package.json"],
  "total_folders": 15,
  "total_files": 42,
  "sdlc_config_found": true,
  "docs_folder_exists": true
}
```

---

## 5. Webhooks (Optional)

### Supported Events

| Event | Trigger | Action |
|-------|---------|--------|
| `push` | Code pushed to any branch | Sync repository, re-run gap analysis |
| `pull_request` | PR opened/updated | Trigger gate evaluation |
| `installation` | App installed/uninstalled | Update installation status |

### Webhook Configuration

Webhooks are automatically configured when installing the GitHub App. The webhook URL is:

```
https://sdlc.example.com/api/webhooks/github
```

### Webhook Secret

The webhook secret is configured in your backend environment:

```bash
GITHUB_WEBHOOK_SECRET=your-webhook-secret
```

---

## 6. Error Handling

### Common Errors

| Error Code | Description | Resolution |
|------------|-------------|------------|
| `GITHUB_AUTH_FAILED` | Authentication failed | Re-authorize GitHub App |
| `GITHUB_RATE_LIMIT` | API rate limit exceeded | Wait 1 hour (5000 req/hour) |
| `GITHUB_REPO_ACCESS_DENIED` | No access to repository | Install GitHub App on repo |
| `GITHUB_REPO_NOT_FOUND` | Repository not found | Check repo URL and visibility |
| `GITHUB_APP_NOT_INSTALLED` | App not installed | Install GitHub App |
| `GITHUB_CLONE_FAILED` | Clone operation failed | Check permissions, retry |

### Rate Limiting

GitHub API allows 5000 requests per hour per installation. SDLC Orchestrator tracks rate limits and:

1. Shows remaining quota in error messages
2. Automatically retries after rate limit reset
3. Uses exponential backoff for transient failures

### Retry Behavior

```
Attempt 1: Immediate
Attempt 2: 1 second delay
Attempt 3: 2 seconds delay (with jitter)
Attempt 4: 4 seconds delay (with jitter)
...
Max retries: 5
```

---

## 7. Security Considerations

### Permissions Model

SDLC Orchestrator requests minimal permissions:

| Permission | Level | Purpose |
|------------|-------|---------|
| Contents | Read | Clone repository, read files |
| Metadata | Read | List repositories, get repo info |
| Pull requests | Read/Write | Comment on PRs with gate results |

### Token Security

- **Installation tokens** expire after 1 hour
- **Tokens are auto-refreshed** 5 minutes before expiry
- **No user tokens stored** - OAuth is session-only
- **Audit logs** track all GitHub API calls

### AGPL Compliance

SDLC Orchestrator uses network-only access to GitHub API (no SDK imports), ensuring legal compliance with our Apache-2.0 license.

---

## 8. Troubleshooting

### "GitHub App not installed"

1. Visit https://github.com/apps/sdlc-orchestrator/installations/new
2. Install the app on your account/organization
3. Grant access to the specific repository
4. Retry the connection

### "Repository not found"

1. Verify the repository URL is correct
2. Check if the repository is private
3. Ensure GitHub App has access to the repository
4. Check if repository was renamed or transferred

### "Clone failed"

1. Check network connectivity to github.com
2. Verify repository permissions
3. Check disk space on server
4. Try shallow clone (`--shallow=true`)
5. Check for large files (>100MB) that may timeout

### "Rate limit exceeded"

1. Wait for rate limit reset (shown in error message)
2. Check if other applications share the same installation
3. Consider using webhook events instead of polling
4. Contact support if rate limit is consistently exceeded

### Debug Mode

Enable debug logging for detailed information:

```bash
# CLI
SDLC_DEBUG=1 sdlcctl init --github owner/repo

# Extension (VS Code settings)
"sdlc.debug": true
```

---

## 9. Best Practices

### Repository Setup

1. **Use `.sdlc-config.json`** in repository root for project settings
2. **Keep `docs/` folder** at root level for gap analysis
3. **Use consistent branch naming** (main, develop, feature/*)
4. **Enable branch protection** for main branch

### CI/CD Integration

```yaml
# .github/workflows/sdlc-validate.yml
name: SDLC Validation
on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: sdlc-orchestrator/action@v1
        with:
          api-url: ${{ secrets.SDLC_API_URL }}
          api-token: ${{ secrets.SDLC_API_TOKEN }}
          tier: professional
```

### Multi-Repository Projects

For projects spanning multiple repositories:

1. Create a "parent" project in SDLC Orchestrator
2. Link each repository as a sub-project
3. Use cross-reference validation for shared specifications
4. Configure webhook events for all repositories

---

## 10. Reference

### Related Documents

- [ADR-044: GitHub Integration Strategy](../../02-design/01-ADRs/ADR-044-GitHub-Integration-Strategy.md)
- [Sprint 129 Plan](../../04-build/02-Sprint-Plans/SPRINT-129-GITHUB-INTEGRATION.md)
- [API Specification](../../01-planning/05-API-Design/API-Specification.md)

### Support

- **GitHub Issues**: https://github.com/Minh-Tam-Solution/SDLC-Orchestrator/issues
- **Documentation**: https://docs.sdlc-orchestrator.dev
- **Email**: support@sdlc-orchestrator.dev

---

**Document Status**: P0 Integration Guide
**Compliance**: SDLC 6.1.0 Stage 03 (RFC-001)
**Owner**: Backend Team
