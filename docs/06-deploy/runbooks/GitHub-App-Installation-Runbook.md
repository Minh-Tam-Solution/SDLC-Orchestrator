# GitHub App Installation Runbook

**Version**: 1.0.0
**Sprint**: 129 - GitHub Integration
**Status**: ACTIVE
**Last Updated**: January 31, 2026

---

## Overview

This runbook covers the installation, configuration, and troubleshooting of the SDLC Orchestrator GitHub App for repository integration.

### Prerequisites

- GitHub account with organization owner or admin permissions
- SDLC Orchestrator backend deployed and accessible
- Domain with valid SSL certificate (for webhooks)

---

## 1. Creating the GitHub App

### Step 1: Navigate to GitHub App Settings

1. Go to GitHub.com → Settings → Developer settings → GitHub Apps
2. Click **"New GitHub App"**

### Step 2: Configure Basic Information

```yaml
App name: SDLC Orchestrator
Description: Enterprise SDLC governance and compliance automation
Homepage URL: https://sdlc.nhatquangholding.com
```

### Step 3: Configure Callback URL

```yaml
Callback URL: https://sdlc.nhatquangholding.com/api/v1/auth/github/callback
Setup URL (optional): https://sdlc.nhatquangholding.com/setup/github
Post installation: Redirect to setup URL (checked)
```

### Step 4: Configure Webhook

```yaml
Webhook:
  Active: ✅ Checked
  Webhook URL: https://sdlc.nhatquangholding.com/api/webhooks/github
  Webhook secret: <generate-random-secret>

# Generate secret with:
openssl rand -hex 32
```

### Step 5: Set Repository Permissions

| Permission | Access Level | Purpose |
|------------|--------------|---------|
| **Contents** | Read-only | Clone repository, read files |
| **Metadata** | Read-only | List repositories, get repo info |
| **Pull requests** | Read & write | Comment on PRs with gate results |
| **Issues** | Read-only | Read issue metadata (optional) |
| **Commit statuses** | Read & write | Post gate check status |

### Step 6: Set Organization Permissions

| Permission | Access Level | Purpose |
|------------|--------------|---------|
| **Members** | Read-only | Get organization membership info |

### Step 7: Subscribe to Events

| Event | Purpose |
|-------|---------|
| `push` | Trigger sync on code changes |
| `pull_request` | Trigger gate evaluation |
| `installation` | Track app installs/uninstalls |
| `repository` | Track repo created/deleted |

### Step 8: Configure Where App Can Be Installed

```yaml
Installation:
  ☑ Any account (recommended for SaaS)
  ☐ Only on this account (for internal use)
```

### Step 9: Create the GitHub App

Click **"Create GitHub App"**

### Step 10: Generate Private Key

1. After creation, scroll to "Private keys" section
2. Click **"Generate a private key"**
3. Download the `.pem` file
4. Store securely (do NOT commit to git)

---

## 2. Backend Configuration

### Environment Variables

Add to your `.env` or secrets management:

```bash
# GitHub App Configuration
GITHUB_APP_ID=123456
GITHUB_APP_NAME=sdlc-orchestrator
GITHUB_APP_CLIENT_ID=Iv1.abc123def456
GITHUB_APP_CLIENT_SECRET=xxxxxxxxxxxxx
GITHUB_APP_PRIVATE_KEY_PATH=/etc/secrets/github-app-private-key.pem
GITHUB_WEBHOOK_SECRET=your-webhook-secret

# Alternative: Private key as base64-encoded string
GITHUB_APP_PRIVATE_KEY_BASE64=LS0tLS1CRUdJTi...
```

### Private Key Storage

**Option A: File-based (recommended for production)**
```bash
# Copy private key to secure location
sudo mkdir -p /etc/secrets
sudo cp your-app.2026-01-31.private-key.pem /etc/secrets/github-app-private-key.pem
sudo chmod 600 /etc/secrets/github-app-private-key.pem
sudo chown app-user:app-group /etc/secrets/github-app-private-key.pem
```

**Option B: Environment variable (for containers)**
```bash
# Encode private key as base64
cat your-app.2026-01-31.private-key.pem | base64 -w0 > private-key.b64

# Set in Kubernetes secret
kubectl create secret generic github-app-key \
  --from-file=private-key=/etc/secrets/github-app-private-key.pem
```

### Verify Configuration

```bash
# Test GitHub App authentication
curl -s https://sdlc.example.com/api/v1/github/installations \
  -H "Authorization: Bearer $API_TOKEN" | jq
```

---

## 3. Installing the App on Repositories

### For Organization Owners

1. Navigate to: `https://github.com/apps/sdlc-orchestrator/installations/new`
2. Select your organization
3. Choose repository access:
   - **All repositories**: Full access to current and future repos
   - **Only select repositories**: Choose specific repos (recommended)
4. Review permissions
5. Click **"Install"**

### For Repository Admins

1. Go to: Settings → Integrations → GitHub Apps
2. Click **"Configure"** next to SDLC Orchestrator
3. Select which repositories to enable
4. Click **"Save"**

### Verify Installation

```bash
# Via CLI
SDLC_API_TOKEN=your-token sdlcctl init test-project --github owner/repo --tier lite

# Expected output:
# ✓ GitHub App installed for owner
# ✓ Repository access verified
# ✓ Project created
```

---

## 4. Webhook Configuration

### Verify Webhook Endpoint

```bash
# Test webhook endpoint is accessible
curl -X POST https://sdlc.example.com/api/webhooks/github \
  -H "Content-Type: application/json" \
  -H "X-GitHub-Event: ping" \
  -d '{"zen": "test"}'

# Expected: 200 OK
```

### Webhook Signature Validation

The backend validates webhook signatures using HMAC-SHA256:

```python
import hmac
import hashlib

def verify_webhook_signature(payload_body: bytes, signature: str, secret: str) -> bool:
    """Verify GitHub webhook signature."""
    if not signature.startswith("sha256="):
        return False

    expected = hmac.new(
        secret.encode("utf-8"),
        payload_body,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(f"sha256={expected}", signature)
```

### Webhook Events

| Event | Payload | Action |
|-------|---------|--------|
| `installation.created` | Installation ID | Store in database |
| `installation.deleted` | Installation ID | Remove from database |
| `push` | Commits, refs | Trigger sync + gap analysis |
| `pull_request.opened` | PR details | Trigger gate evaluation |
| `pull_request.synchronize` | Updated commits | Re-run gate evaluation |

---

## 5. Rate Limiting

### GitHub API Limits

| Limit Type | Value | Reset |
|------------|-------|-------|
| Installation token requests | 5,000/hour | Rolling window |
| Search API | 30/minute | Per installation |
| GraphQL | 5,000 points/hour | Per installation |

### Handling Rate Limits

```python
# Response header check
rate_limit_remaining = response.headers.get("X-RateLimit-Remaining")
rate_limit_reset = response.headers.get("X-RateLimit-Reset")

if rate_limit_remaining == "0":
    reset_time = datetime.fromtimestamp(int(rate_limit_reset))
    wait_seconds = (reset_time - datetime.now()).total_seconds()
    logger.warning(f"Rate limited. Waiting {wait_seconds}s")
    time.sleep(wait_seconds)
```

---

## 6. Troubleshooting

### Issue: "App not installed" Error

**Symptoms:**
```
GitHubAppNotInstalledError: SDLC Orchestrator GitHub App is not installed
```

**Resolution:**
1. Verify app is installed: Settings → Integrations → GitHub Apps
2. Check repository is included in app's access list
3. Verify installation is not suspended

### Issue: Webhook Not Received

**Symptoms:**
- Push events not triggering sync
- PR comments not appearing

**Resolution:**
1. Check webhook delivery logs: Settings → Developer settings → GitHub Apps → [Your App] → Advanced
2. Verify webhook URL is accessible from GitHub
3. Check webhook secret matches backend configuration
4. Verify SSL certificate is valid

### Issue: Clone Fails with "Authentication Failed"

**Symptoms:**
```
GitHubCloneError: fatal: Authentication failed for 'https://github.com/...'
```

**Resolution:**
1. Verify installation token is valid
2. Check repository is accessible via installation
3. Verify repository is not archived
4. Check for branch protection rules

### Issue: Rate Limit Exceeded

**Symptoms:**
```
GitHubApiError (429): Rate limit exceeded
```

**Resolution:**
1. Check rate limit headers in responses
2. Implement exponential backoff
3. Cache API responses where possible
4. Consider multiple GitHub App installations

### Issue: Private Key Invalid

**Symptoms:**
```
jwt.exceptions.InvalidKeyError: Could not deserialize key data
```

**Resolution:**
1. Verify private key file format (PEM)
2. Check for extra whitespace or newlines
3. Regenerate private key if corrupted
4. Verify file permissions (should be 600)

---

## 7. Security Checklist

### Pre-Deployment

- [ ] Private key stored securely (not in git)
- [ ] Webhook secret is random and strong (32+ chars)
- [ ] HTTPS enabled for all endpoints
- [ ] Minimal permissions requested

### Post-Deployment

- [ ] Verify webhook signature validation works
- [ ] Test rate limiting behavior
- [ ] Monitor webhook delivery logs
- [ ] Set up alerts for failed authentications

### Ongoing

- [ ] Rotate webhook secret annually
- [ ] Review app permissions quarterly
- [ ] Monitor for suspicious activity
- [ ] Keep private key backup secure

---

## 8. Monitoring

### Key Metrics

| Metric | Alert Threshold | Action |
|--------|-----------------|--------|
| `github_api_errors_total` | >10/hour | Check authentication |
| `github_rate_limit_remaining` | <500 | Reduce API calls |
| `github_webhook_failures` | >5/hour | Check endpoint health |
| `github_clone_duration_seconds` | >300 | Check network/disk |

### Grafana Dashboard

```yaml
Panels:
  - GitHub API Request Rate
  - Rate Limit Remaining
  - Webhook Delivery Success Rate
  - Clone Duration (p95)
  - Installations Count
  - Active Repositories
```

---

## 9. Rollback Procedure

### If GitHub App Needs to Be Disabled

1. **Suspend App (temporary)**
   - Go to: Settings → Developer settings → GitHub Apps → [Your App]
   - Click "Suspend" to pause all installations

2. **Revoke All Installations (permanent)**
   - Go to: Settings → Developer settings → GitHub Apps → [Your App] → Advanced
   - Click "Revoke all user tokens"
   - Contact affected users

3. **Delete App (irreversible)**
   - Go to: Settings → Developer settings → GitHub Apps → [Your App] → Advanced
   - Scroll to bottom and click "Delete this GitHub App"

---

## 10. Contact & Support

- **GitHub Issues**: https://github.com/Minh-Tam-Solution/SDLC-Orchestrator/issues
- **Documentation**: https://docs.sdlc-orchestrator.dev
- **Email**: support@sdlc-orchestrator.dev
- **Slack**: #sdlc-orchestrator-support

---

**Document Status**: P0 Runbook
**Compliance**: SDLC 6.0.0 Stage 06
**Owner**: DevOps Team
