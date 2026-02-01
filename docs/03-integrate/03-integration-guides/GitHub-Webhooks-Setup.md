# GitHub Webhooks Setup Guide

**Version**: 1.0.0
**Sprint**: 129.5 - GitHub Webhooks
**Date**: January 2026
**Status**: ACTIVE

---

## Overview

This guide explains how to configure and troubleshoot GitHub webhooks for SDLC Orchestrator. Webhooks enable automatic compliance checking when code is pushed or PRs are created.

### What Webhooks Enable

| Event | Trigger | Action |
|-------|---------|--------|
| `push` | Code pushed to any branch | Gap analysis on default branch |
| `pull_request` | PR opened/synchronized | Gate evaluation + PR status check |
| `installation` | App installed/uninstalled | Track installation in database |

---

## Prerequisites

1. **GitHub App Created** - SDLC Orchestrator GitHub App configured
2. **Webhook Secret** - Shared secret for HMAC-SHA256 signature validation
3. **Backend Running** - SDLC Orchestrator backend accessible

---

## Configuration

### Step 1: Configure Webhook URL

In your GitHub App settings (GitHub.com → Settings → Developer settings → GitHub Apps):

```
Webhook URL: https://your-domain.com/api/v1/github/webhooks
```

**For Local Development** (using ngrok):
```bash
# Start ngrok tunnel
ngrok http 8000

# Use ngrok URL in GitHub App settings
Webhook URL: https://abc123.ngrok.io/api/v1/github/webhooks
```

### Step 2: Set Webhook Secret

Generate a secure random secret:
```bash
# Generate 32-character secret
openssl rand -hex 16

# Example output: 8a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d
```

Configure in GitHub App settings:
```
Webhook secret: 8a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d
```

Configure in backend environment:
```bash
# .env file
GITHUB_APP_WEBHOOK_SECRET=8a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d
```

### Step 3: Subscribe to Events

In GitHub App settings, enable these events:

**Required Events**:
- [x] Push
- [x] Pull requests
- [x] Installation

**Optional Events** (for future features):
- [ ] Issues
- [ ] Create/Delete (branch events)
- [ ] Check runs

### Step 4: Verify Configuration

Test webhook by clicking "Redeliver" in GitHub App → Advanced → Recent Deliveries:

**Expected Response**:
```json
{
  "status": "accepted",
  "event": "ping",
  "delivery_id": "abc123...",
  "message": "Webhook configured successfully"
}
```

---

## Webhook Processing Flow

```
┌──────────────────────────────────────────────────────────────────┐
│                     WEBHOOK PROCESSING FLOW                       │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  GitHub                Backend                  Redis     Celery │
│    │                     │                       │          │    │
│    │ POST /webhooks      │                       │          │    │
│    │────────────────────>│                       │          │    │
│    │                     │                       │          │    │
│    │                     │ 1. Validate signature │          │    │
│    │                     │    (HMAC-SHA256)      │          │    │
│    │                     │                       │          │    │
│    │                     │ 2. Check idempotency  │          │    │
│    │                     │───────────────────────>│          │    │
│    │                     │                       │          │    │
│    │                     │ 3. Enqueue job        │          │    │
│    │                     │───────────────────────>│          │    │
│    │                     │                       │          │    │
│    │  202 Accepted       │                       │          │    │
│    │<────────────────────│                       │          │    │
│    │                     │                       │          │    │
│    │                     │                       │ 4. Process│    │
│    │                     │                       │──────────>│    │
│    │                     │                       │          │    │
│    │                     │                       │ 5. Post  │    │
│    │                     │<─────────────────────────────────│    │
│    │                     │    status check       │          │    │
│    │<────────────────────│                       │          │    │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## Signature Verification

GitHub signs webhook payloads with HMAC-SHA256. The backend validates signatures to prevent spoofing.

### How It Works

1. GitHub computes: `sha256=HMAC(payload, secret)`
2. GitHub sends signature in `X-Hub-Signature-256` header
3. Backend computes same HMAC and compares
4. Timing-safe comparison prevents timing attacks

### Manual Verification (for debugging)

```python
import hmac
import hashlib

def verify_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Verify GitHub webhook signature."""
    if not signature.startswith("sha256="):
        return False

    expected_sig = "sha256=" + hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(signature, expected_sig)
```

### Example with cURL

```bash
# Compute signature manually
PAYLOAD='{"action":"opened"}'
SECRET="your-webhook-secret"
SIGNATURE=$(echo -n "$PAYLOAD" | openssl dgst -sha256 -hmac "$SECRET" | cut -d' ' -f2)

# Send webhook request
curl -X POST https://your-domain.com/api/v1/github/webhooks \
  -H "Content-Type: application/json" \
  -H "X-GitHub-Event: pull_request" \
  -H "X-Hub-Signature-256: sha256=$SIGNATURE" \
  -H "X-GitHub-Delivery: test-$(date +%s)" \
  -d "$PAYLOAD"
```

---

## Troubleshooting

### Error: 401 Unauthorized - "signature_missing"

**Cause**: X-Hub-Signature-256 header not sent

**Solution**:
1. Ensure webhook secret is configured in GitHub App settings
2. Check that signature header is being forwarded (reverse proxy issue)

### Error: 401 Unauthorized - "signature_invalid"

**Cause**: Signature doesn't match

**Solutions**:
1. Verify GITHUB_APP_WEBHOOK_SECRET matches GitHub App webhook secret
2. Check for encoding issues (UTF-8 payload)
3. Ensure payload isn't modified by middleware

### Error: 500 Internal Server Error - "webhook_not_configured"

**Cause**: GITHUB_APP_WEBHOOK_SECRET environment variable not set

**Solution**:
```bash
export GITHUB_APP_WEBHOOK_SECRET="your-secret"
# or add to .env file
```

### Error: 200 OK with "status": "duplicate"

**Cause**: Same X-GitHub-Delivery already processed (idempotency check)

**This is expected behavior** - GitHub may retry webhooks, and we prevent duplicate processing.

### Webhook Not Received

**Check GitHub Delivery Logs**:
1. Go to GitHub App → Advanced → Recent Deliveries
2. Check for failed deliveries (red X)
3. View request/response details

**Common Causes**:
- Backend not accessible from internet
- Firewall blocking GitHub IPs
- SSL certificate issues
- Incorrect webhook URL

**GitHub IP Ranges** (for firewall allowlist):
- https://api.github.com/meta → "hooks" field

### Job Stuck in Queue

**Check Queue Status**:
```bash
curl -H "Authorization: Bearer $TOKEN" \
  https://your-domain.com/api/v1/github/webhooks/stats
```

**Manual Processing**:
```bash
curl -X POST -H "Authorization: Bearer $TOKEN" \
  https://your-domain.com/api/v1/github/webhooks/process
```

### Job Failed - In Dead Letter Queue

**View DLQ**:
```bash
curl -H "Authorization: Bearer $TOKEN" \
  https://your-domain.com/api/v1/github/webhooks/dlq
```

**Retry Failed Job**:
```bash
curl -X POST -H "Authorization: Bearer $TOKEN" \
  https://your-domain.com/api/v1/github/webhooks/dlq/{job_id}/retry
```

---

## Monitoring

### Key Metrics to Monitor

| Metric | Alert Threshold | Description |
|--------|-----------------|-------------|
| `webhook_delivery_rate` | <99% | Webhook delivery success rate |
| `webhook_processing_time_p95` | >30s | 95th percentile processing time |
| `webhook_dlq_size` | >10 | Jobs in dead letter queue |
| `webhook_signature_failures` | >5/min | Potential attack or misconfiguration |

### Logging

Webhook events are logged at INFO level:
```
INFO - Enqueued webhook job webhook_abc123 (event: push)
INFO - Processing webhook job webhook_abc123
INFO - Webhook job webhook_abc123 completed successfully
```

Errors are logged at ERROR level:
```
ERROR - Webhook job webhook_abc123 failed: Connection timeout
ERROR - Webhook signature invalid (delivery: abc123)
```

---

## Event Payload Examples

### Push Event

```json
{
  "ref": "refs/heads/main",
  "after": "abc123def456789...",
  "repository": {
    "id": 12345,
    "full_name": "owner/repo",
    "default_branch": "main"
  },
  "pusher": {
    "name": "user"
  },
  "commits": [
    {
      "id": "abc123",
      "message": "Fix bug in auth",
      "author": {"name": "User"}
    }
  ],
  "installation": {
    "id": 99999
  }
}
```

### Pull Request Event

```json
{
  "action": "opened",
  "number": 42,
  "pull_request": {
    "number": 42,
    "title": "Add new feature",
    "state": "open",
    "draft": false,
    "head": {
      "sha": "abc123...",
      "ref": "feature/new-feature"
    },
    "base": {
      "ref": "main"
    }
  },
  "repository": {
    "id": 12345,
    "full_name": "owner/repo"
  },
  "installation": {
    "id": 99999
  }
}
```

### Installation Event

```json
{
  "action": "created",
  "installation": {
    "id": 99999,
    "account": {
      "login": "org-name",
      "type": "Organization"
    }
  },
  "sender": {
    "login": "admin-user"
  }
}
```

---

## Security Best Practices

1. **Rotate Webhook Secret Regularly** - Every 90 days
2. **Monitor for Signature Failures** - Could indicate attack
3. **Use HTTPS Only** - Never accept webhooks over HTTP
4. **Validate Installation ID** - Ensure webhook is from known installation
5. **Rate Limit Processing** - Prevent DoS via webhook flooding

---

## Related Documentation

- [ADR-044: GitHub Integration Strategy](../../02-design/01-ADRs/ADR-044-GitHub-Integration-Strategy.md)
- [Sprint 129.5 Plan](../../04-build/02-Sprint-Plans/SPRINT-129.5-GITHUB-WEBHOOKS.md)
- [GitHub App API Reference](https://docs.github.com/en/apps)
- [Webhook Best Practices](https://docs.github.com/en/webhooks/using-webhooks/best-practices-for-using-webhooks)
