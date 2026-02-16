# GitHub App Setup Guide - SDLC Orchestrator

**Version:** 1.0.0
**Date:** January 19, 2026
**Status:** ACTIVE - Sprint 82 (Pre-Launch Hardening)
**Authority:** DevOps Lead + CTO Approved
**Framework:** SDLC 6.0.6 P4 (Quality Gates)

---

## Overview

This guide covers the complete setup of the SDLC Orchestrator GitHub App for production deployment. The GitHub App enables:

- **Check Runs**: Post gate evaluation results on PRs
- **Context Overlay**: Deliver SDLC stage context via annotations
- **Webhook Events**: Receive PR events for automated evaluation
- **Repository Access**: Read repository contents for analysis

---

## Prerequisites

| Requirement | Description |
|-------------|-------------|
| GitHub Organization | Admin access to organization where app will be installed |
| Production Domain | `api.sdlc.example.com` or your production API domain |
| HashiCorp Vault | Running instance for secrets management |
| Backend Deployed | SDLC Orchestrator backend running |

---

## Part 1: GitHub App Registration

### Step 1: Create GitHub App

1. Navigate to **GitHub Organization Settings** → **Developer settings** → **GitHub Apps**
2. Click **"New GitHub App"**
3. Fill in the following details:

#### Basic Information

| Field | Value |
|-------|-------|
| **GitHub App name** | `SDLC Orchestrator` (or `{org}-sdlc-orchestrator`) |
| **Description** | SDLC Gate Evaluation and Context Overlay for AI-generated code governance |
| **Homepage URL** | `https://your-company.com/sdlc-orchestrator` |

#### Webhook Configuration

| Field | Value |
|-------|-------|
| **Webhook URL** | `https://api.sdlc.example.com/api/v1/webhooks/github` |
| **Webhook secret** | Generate with: `openssl rand -hex 32` (save this!) |
| **Active** | ✅ Checked |

#### Permissions (Repository)

| Permission | Access Level | Purpose |
|------------|--------------|---------|
| **Checks** | Read & Write | Create Check Runs for gate evaluation |
| **Contents** | Read-only | Read files for SAST and context analysis |
| **Metadata** | Read-only | Access repository metadata (required) |
| **Pull requests** | Read-only | Read PR details and labels |

#### Permissions (Organization)

| Permission | Access Level | Purpose |
|------------|--------------|---------|
| **Members** | Read-only | (Optional) Team membership for RBAC |

#### Subscribe to Events

| Event | Purpose |
|-------|---------|
| ✅ **Check run** | Re-request check runs |
| ✅ **Check suite** | Auto-trigger on new check suites |
| ✅ **Pull request** | Trigger on PR open/sync/reopen |
| ✅ **Push** | (Optional) Trigger on push to branches |

#### Where can this GitHub App be installed?

- ✅ **Any account** (if SaaS)
- ✅ **Only on this account** (if self-hosted/enterprise)

### Step 2: Generate Private Key

1. After creation, scroll to **"Private keys"** section
2. Click **"Generate a private key"**
3. Download the `.pem` file (e.g., `sdlc-orchestrator.2026-01-19.private-key.pem`)
4. **IMPORTANT**: This file is shown only once. Store securely!

### Step 3: Note App Details

Record these values for configuration:

| Field | Example | Your Value |
|-------|---------|------------|
| **App ID** | `123456` | __________ |
| **Client ID** | `Iv1.abc123def456` | __________ |
| **Client Secret** | (from OAuth settings) | __________ |
| **Webhook Secret** | (generated in step 1) | __________ |
| **Private Key File** | `sdlc-orchestrator.pem` | __________ |

---

## Part 2: Secrets Storage (HashiCorp Vault)

### Step 1: Store Private Key

```bash
# Convert PEM to base64 for storage
cat sdlc-orchestrator.pem | base64 > private-key-base64.txt

# Store in Vault
vault kv put secret/sdlc-orchestrator/github \
  app_id="123456" \
  client_id="Iv1.abc123def456" \
  client_secret="your-client-secret" \
  webhook_secret="your-webhook-secret" \
  private_key_base64="$(cat private-key-base64.txt)"

# Verify storage
vault kv get secret/sdlc-orchestrator/github
```

### Step 2: Create Vault Policy

```hcl
# sdlc-orchestrator-policy.hcl
path "secret/data/sdlc-orchestrator/github" {
  capabilities = ["read"]
}

path "secret/data/sdlc-orchestrator/evidence" {
  capabilities = ["read"]
}
```

Apply policy:

```bash
vault policy write sdlc-orchestrator sdlc-orchestrator-policy.hcl
```

### Step 3: Create Service Token

```bash
# Create token for backend service
vault token create \
  -policy=sdlc-orchestrator \
  -display-name="sdlc-orchestrator-backend" \
  -ttl=720h \
  -renewable

# Note the token value for backend configuration
```

---

## Part 3: Backend Configuration

### Environment Variables

Add to `.env` or Kubernetes secrets:

```bash
# GitHub App Configuration
GITHUB_APP_ID=123456
GITHUB_APP_CLIENT_ID=Iv1.abc123def456
GITHUB_APP_CLIENT_SECRET=your-client-secret
GITHUB_APP_WEBHOOK_SECRET=your-webhook-secret
GITHUB_APP_PRIVATE_KEY_BASE64=<base64-encoded-pem>

# OR if using Vault
VAULT_ADDR=https://vault.example.com
VAULT_TOKEN=hvs.your-vault-token
GITHUB_APP_VAULT_PATH=secret/data/sdlc-orchestrator/github
```

### Kubernetes Secret (Recommended)

```yaml
# github-app-secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: sdlc-github-app
  namespace: sdlc-orchestrator
type: Opaque
stringData:
  GITHUB_APP_ID: "123456"
  GITHUB_APP_CLIENT_ID: "Iv1.abc123def456"
  GITHUB_APP_CLIENT_SECRET: "your-client-secret"
  GITHUB_APP_WEBHOOK_SECRET: "your-webhook-secret"
  GITHUB_APP_PRIVATE_KEY_BASE64: |
    LS0tLS1CRUdJTi... (base64 encoded PEM)
```

Apply:

```bash
kubectl apply -f github-app-secret.yaml
```

### Backend Deployment Reference

```yaml
# deployment.yaml (snippet)
spec:
  containers:
  - name: backend
    envFrom:
    - secretRef:
        name: sdlc-github-app
```

---

## Part 4: Webhook Verification

### Step 1: Test Webhook Endpoint

```bash
# Verify webhook endpoint is accessible
curl -X POST https://api.sdlc.example.com/api/v1/webhooks/github \
  -H "Content-Type: application/json" \
  -H "X-GitHub-Event: ping" \
  -H "X-Hub-Signature-256: sha256=test" \
  -d '{"zen": "Testing webhook"}'

# Expected: 200 OK or signature validation error
```

### Step 2: Check GitHub App Deliveries

1. Go to GitHub App Settings → **Advanced** → **Recent Deliveries**
2. Verify "ping" event shows green checkmark (200 response)
3. If failed, check:
   - Webhook URL is correct
   - Backend is running
   - Webhook secret matches

### Step 3: Validate Signature Verification

The backend validates webhook signatures using HMAC-SHA256:

```python
# Backend validation (already implemented in github_webhook_service.py)
import hmac
import hashlib

def verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Verify GitHub webhook signature."""
    expected = "sha256=" + hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
```

---

## Part 5: Check Run Configuration

### Per-Project Enforcement Mode

Projects can configure Check Run enforcement mode in their settings:

| Mode | Behavior | GitHub Conclusion |
|------|----------|-------------------|
| `advisory` | Informational only, never blocks | `success` or `neutral` |
| `blocking` | Blocks merge if gates fail | `failure` |
| `strict` | Blocks + requires manual approval | `action_required` |

### Branch Protection (Required for Blocking Mode)

To enforce blocking mode, configure GitHub branch protection:

1. Go to **Repository Settings** → **Branches** → **Branch protection rules**
2. Click **"Add rule"** for `main` branch
3. Configure:

| Setting | Value |
|---------|-------|
| **Require status checks to pass** | ✅ Enabled |
| **Status checks that are required** | Add: `SDLC Gate Evaluation` |
| **Require branches to be up to date** | Optional |

### Bypass Label

PRs with the `sdlc-bypass` label skip enforcement regardless of project mode.

**Creating the label:**

```bash
# Using GitHub CLI
gh label create "sdlc-bypass" \
  --description "Skip SDLC gate enforcement (emergency only)" \
  --color "FBCA04" \
  --repo owner/repo
```

---

## Part 6: Installation on Repositories

### Step 1: Install GitHub App

1. Go to GitHub App page: `https://github.com/apps/sdlc-orchestrator`
2. Click **"Install"**
3. Choose repositories:
   - **All repositories** (for org-wide deployment)
   - **Only select repositories** (for gradual rollout)
4. Click **"Install"**

### Step 2: Verify Installation

```bash
# Check installation via API
curl -H "Authorization: Bearer $GITHUB_TOKEN" \
  https://api.github.com/app/installations

# Or via backend endpoint
curl https://api.sdlc.example.com/api/v1/github/installations \
  -H "Authorization: Bearer $USER_TOKEN"
```

### Step 3: Link Project to Repository

In SDLC Orchestrator:

1. Go to **Project Settings** → **GitHub Integration**
2. Select installation and repository
3. Configure enforcement mode (advisory/blocking/strict)
4. Save

---

## Part 7: Monitoring & Troubleshooting

### Health Check Endpoints

```bash
# Check GitHub App service health
curl https://api.sdlc.example.com/api/v1/health/github-app

# Response:
{
  "status": "healthy",
  "app_id": "123456",
  "installations_count": 5,
  "last_webhook_at": "2026-01-19T10:30:00Z"
}
```

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Webhook signature invalid | Mismatched secret | Verify GITHUB_APP_WEBHOOK_SECRET matches GitHub App settings |
| Check Run not appearing | Missing permissions | Re-check `checks:write` permission |
| "Not Found" on installation | App not installed on repo | Install app on repository |
| Rate limited | Too many API calls | Implement caching, reduce webhook frequency |

### Logs to Check

```bash
# Backend logs
kubectl logs -l app=sdlc-orchestrator -c backend --tail=100

# Filter for GitHub App errors
kubectl logs -l app=sdlc-orchestrator | grep -i "github\|check_run\|webhook"
```

### Metrics to Monitor

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| `github_webhook_latency_p95` | <500ms | >2s |
| `github_check_run_created_total` | Growing | N/A |
| `github_webhook_signature_failures` | 0 | >5/hour |
| `github_api_rate_limit_remaining` | >1000 | <100 |

---

## Part 8: Security Checklist

### Pre-Production

- [ ] Private key stored in Vault (not in code/config files)
- [ ] Webhook secret is unique and random (32+ characters)
- [ ] HTTPS only for webhook URL
- [ ] Minimal permissions (only what's needed)
- [ ] App installed only on intended repositories

### Post-Production

- [ ] Webhook signature validation enabled and tested
- [ ] Rate limiting configured (10 Check Runs/min/repo)
- [ ] Failed webhook retries limited (prevent DDoS)
- [ ] Audit logging enabled for GitHub API calls
- [ ] Private key rotation scheduled (every 90 days)

### Key Rotation Procedure

```bash
# 1. Generate new private key in GitHub App settings
# 2. Store new key in Vault
vault kv patch secret/sdlc-orchestrator/github \
  private_key_base64="$(cat new-private-key.pem | base64)"

# 3. Restart backend to pick up new key
kubectl rollout restart deployment/sdlc-orchestrator

# 4. Verify functionality
curl https://api.sdlc.example.com/api/v1/health/github-app

# 5. Delete old key from GitHub App settings
```

---

## Appendix A: Required API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/webhooks/github` | POST | Receive GitHub webhooks |
| `/api/v1/github/installations` | GET | List app installations |
| `/api/v1/github/repositories` | GET | List accessible repositories |
| `/api/v1/health/github-app` | GET | Health check |

---

## Appendix B: Example Check Run Output

When configured, Check Runs appear on PRs like this:

```
┌──────────────────────────────────────────────────────────────┐
│ SDLC Gate Evaluation                                    ✅ Passed │
├──────────────────────────────────────────────────────────────┤
│ 🛡️ Stage: BUILD | Gate: G3-PASSED                            │
│                                                              │
│ **Enforcement Mode**: BLOCKING                               │
│                                                              │
│ > Blocking mode: Merge will be blocked if gates fail.       │
│                                                              │
│ ## Gate Evaluation                                           │
│ **Result**: ✅ PASSED                                         │
│                                                              │
│ ---                                                          │
│ *Generated by SDLC Orchestrator - Sprint 82*                 │
└──────────────────────────────────────────────────────────────┘
```

---

## References

- [GitHub Apps Documentation](https://docs.github.com/en/apps)
- [GitHub Check Runs API](https://docs.github.com/en/rest/checks/runs)
- [ADR-029: Dynamic Context Overlay](../../02-design/03-ADRs/ADR-029-AGENTS-MD-INTEGRATION.md)
- [Sprint 82 Plan](../../04-build/02-Sprint-Plans/SPRINT-82-HARDENING-EVIDENCE.md)

---

**Document Status:** ✅ APPROVED
**Last Updated:** January 19, 2026
**Owner:** DevOps Lead
**Review:** CTO
