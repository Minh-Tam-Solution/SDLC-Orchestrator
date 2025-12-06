# GitHub Webhook Load Testing

**Version**: 1.0.0
**Date**: November 28, 2025
**Status**: ACTIVE - Sprint 17
**Authority**: QA Lead + Backend Lead Approved
**Foundation**: Sprint 16 GitHub Integration
**Framework**: SDLC 4.9 Complete Lifecycle

---

## Overview

Load testing suite for GitHub webhook endpoint to validate throughput capacity and latency under high load.

**Test File**: `tests/load/github_webhook_load.py`
**Framework**: Locust (Python)
**Target**: 500+ webhooks/second sustained throughput

---

## Test Scenarios

### Traffic Distribution (Real GitHub Patterns)

| Event Type | Weight | Description |
|------------|--------|-------------|
| Push | 60% | Commits to branches |
| Pull Request | 25% | PR opened/closed/sync |
| Issues | 10% | Issue lifecycle |
| Branch | 5% | Branch create/delete |

### User Types

| User Type | Weight | Behavior |
|-----------|--------|----------|
| GitHubWebhookUser | 90% | Normal webhook traffic |
| WebhookBurstUser | 10% | CI/CD burst patterns |

---

## Performance Targets

| Metric | Target | Critical |
|--------|--------|----------|
| p50 Latency | <100ms | - |
| p95 Latency | <500ms | ⭐ Yes |
| p99 Latency | <1000ms | - |
| Error Rate | <0.1% | ⭐ Yes |
| Throughput | >500 req/s | ⭐ Yes |

---

## Test Configuration

```yaml
Default Configuration:
  users: 1000
  spawn_rate: 100 users/second
  run_time: 10 minutes
  host: http://localhost:8000

High Load Configuration:
  users: 5000
  spawn_rate: 500 users/second
  run_time: 30 minutes
```

---

## Running Tests

### Web UI Mode (Interactive)

```bash
# Start load test with web UI
locust -f tests/load/github_webhook_load.py --host http://localhost:8000

# Open browser: http://localhost:8089
# Configure users, spawn rate, and start test
```

### Headless Mode (CI/CD)

```bash
# Run 10-minute load test
locust -f tests/load/github_webhook_load.py \
  --host http://localhost:8000 \
  --users 1000 \
  --spawn-rate 100 \
  --run-time 10m \
  --headless \
  --csv=reports/webhook_load \
  --html=reports/webhook_load_report.html
```

### Quick Smoke Test

```bash
# 1-minute smoke test with 100 users
locust -f tests/load/github_webhook_load.py \
  --host http://localhost:8000 \
  --users 100 \
  --spawn-rate 50 \
  --run-time 1m \
  --headless
```

---

## Webhook Payload Structure

### Push Event

```json
{
  "ref": "refs/heads/main",
  "before": "abc123...",
  "after": "def456...",
  "repository": {
    "id": 123456789,
    "full_name": "owner/repo",
    "default_branch": "main"
  },
  "pusher": {"name": "developer", "email": "dev@example.com"},
  "sender": {"login": "developer", "id": 1001},
  "commits": [
    {"id": "...", "message": "feat: ...", "author": {...}}
  ]
}
```

### Pull Request Event

```json
{
  "action": "opened",
  "number": 42,
  "pull_request": {
    "id": 100001,
    "number": 42,
    "state": "open",
    "title": "Feature: Add new endpoint",
    "user": {"login": "developer", "id": 1001},
    "head": {"ref": "feature-branch", "sha": "..."},
    "base": {"ref": "main", "sha": "..."}
  },
  "repository": {...},
  "sender": {...}
}
```

---

## Signature Validation

All webhooks include proper HMAC-SHA256 signature:

```python
def generate_webhook_signature(payload: str, secret: str) -> str:
    signature = hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return f"sha256={signature}"
```

Headers included:
- `X-GitHub-Event`: Event type
- `X-GitHub-Delivery`: UUID delivery ID
- `X-Hub-Signature-256`: HMAC-SHA256 signature

---

## Expected Results

### Normal Load (1000 users)

| Metric | Expected |
|--------|----------|
| Throughput | 500-2000 req/s |
| p50 Latency | 20-50ms |
| p95 Latency | 100-300ms |
| Error Rate | <0.1% |

### High Load (5000 users)

| Metric | Expected |
|--------|----------|
| Throughput | 1000-5000 req/s |
| p50 Latency | 50-100ms |
| p95 Latency | 200-500ms |
| Error Rate | <0.5% |

---

## Bottleneck Analysis

| Component | Risk | Mitigation |
|-----------|------|------------|
| Signature Verification | Low | HMAC is CPU-bound, fast |
| Job Queue | Medium | In-memory queue (MVP) |
| Database Writes | Medium | Batch writes, async |
| Background Processing | High | Redis Queue (production) |

---

## Integration with CI/CD

```yaml
# .github/workflows/load-test.yml
load-test:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4

    - name: Start services
      run: docker-compose up -d

    - name: Wait for healthy
      run: sleep 30

    - name: Run load test
      run: |
        pip install locust
        locust -f tests/load/github_webhook_load.py \
          --host http://localhost:8000 \
          --users 500 \
          --spawn-rate 50 \
          --run-time 5m \
          --headless \
          --csv=load_test

    - name: Upload results
      uses: actions/upload-artifact@v4
      with:
        name: load-test-results
        path: load_test*.csv
```

---

## Related Documents

- [locustfile.py](../../../tests/load/locustfile.py) - Main API load tests
- [github_webhook_load.py](../../../tests/load/github_webhook_load.py) - Webhook load tests
- [GITHUB-SERVICE-UNIT-TESTS.md](../03-Unit-Testing/GITHUB-SERVICE-UNIT-TESTS.md) - Unit tests
- [GITHUB-OAUTH-INTEGRATION-TESTS.md](../04-Integration-Testing/GITHUB-OAUTH-INTEGRATION-TESTS.md) - Integration tests

---

*SDLC Orchestrator - First Governance-First Platform on SDLC 4.9. Zero Mock Policy enforced.*
