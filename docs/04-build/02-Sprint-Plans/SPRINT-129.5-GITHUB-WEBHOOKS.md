# Sprint 129.5: GitHub Webhooks (P1.5 - Post-Launch)

**Sprint Duration**: Mar 1-3, 2026 (3 days)
**Sprint Goal**: Auto-trigger gap analysis and gate evaluation via webhooks
**Story Points**: 3 SP
**Team**: Backend (1 FTE)
**Priority**: P1.5 (Post-launch enhancement, NOT blocking March 1)

---

## Executive Summary

Sprint 129.5 implements **GitHub Webhooks**, enabling automatic gap analysis and gate evaluation when code changes. This sprint was **deferred from Sprint 129** to reduce scope risk and ensure March 1 soft launch success.

**Strategic Context**:
- **Problem**: Users must manually trigger gap analysis after pushing code
- **Solution**: Webhooks auto-trigger analysis on `push` and `pull_request` events
- **Impact**: Reduces manual work, enables continuous compliance monitoring

**Rationale for Deferral** (from Sprint 129):
- Sprint 129 was overloaded (10 days of work)
- Webhooks are "nice-to-have" for launch (manual trigger works)
- User can manually refresh gap analysis via Extension command
- Deferred to post-launch to reduce risk

**Success Criteria**:
- ✅ Webhook receives `push` events (99% delivery rate)
- ✅ Webhook receives `pull_request` events (99% delivery rate)
- ✅ Gap analysis triggered within 30s of push
- ✅ PR status checks posted to GitHub

---

## Sprint Backlog

### Day 1: Webhook Handler + Job Queue (1.5 SP)

**Tasks**:
- [ ] **WEBHOOK-001**: Implement webhook endpoint
  - Route: `POST /api/webhooks/github`
  - Signature validation: HMAC-SHA256 (X-Hub-Signature-256 header)
  - Event parsing: X-GitHub-Event header (push, pull_request, installation)
  - Idempotency: X-GitHub-Delivery header (prevent duplicate processing)
- [ ] **WEBHOOK-002**: Implement webhook handler logic
  - Parse event payload (JSON)
  - Validate installation_id (check DB for linked project)
  - Enqueue background job (Redis queue)
  - Return 202 Accepted immediately (no sync processing)
- [ ] **WEBHOOK-003**: Implement idempotency check
  - Store delivery_id in Redis (TTL: 24 hours)
  - If delivery_id exists, return 200 OK (already processed)
  - Prevent duplicate job enqueuing
- [ ] **JOB-002**: Create background job `process_github_webhook_job`
  - Celery task (async)
  - Parse event type (push, pull_request, installation)
  - Fetch project by installation_id
  - Trigger appropriate action (gap analysis, gate evaluation)
  - Update project metadata (last_synced_at)
- [ ] **TEST-009**: Write 8 unit tests
  - Signature validation (valid HMAC)
  - Signature validation (invalid HMAC → 401)
  - Idempotency check (duplicate delivery_id → 200)
  - Push event parsing (extract repo, branch, commit)
  - Pull request event parsing (extract PR number, action)
  - Installation event (create/delete installation)
  - Unknown event (log and ignore)
  - Job enqueuing (Redis queue)

**Acceptance Criteria**:
- Webhook endpoint responds in <50ms (sync only validates + enqueues)
- Signature validation prevents unauthorized requests
- Idempotency prevents duplicate processing
- All 8 unit tests passing

---

### Day 2: Event Handlers (1 SP)

**Tasks**:
- [ ] **EVENT-001**: Implement `push` event handler
  - Trigger: Code pushed to branch
  - Action: Run gap analysis on new code
  - Output: Update gap report in DB
  - Notification: Send Slack message if compliance score drops
- [ ] **EVENT-002**: Implement `pull_request` event handler
  - Trigger: PR opened, synchronized (new commits), reopened
  - Action: Run gate evaluation (G0-G3 checks)
  - Output: Post PR status check to GitHub
  - Comment: Add compliance report to PR (if violations found)
- [ ] **EVENT-003**: Implement `installation` event handler
  - Trigger: GitHub App installed/uninstalled
  - Action (installed): Create installation record in DB
  - Action (uninstalled): Soft-delete installation, unlink projects
  - Notification: Send email to user (welcome/goodbye)
- [ ] **GITHUB-004**: Implement PR status check posting
  - GitHub API: POST /repos/{owner}/{repo}/statuses/{sha}
  - Status: success (green), failure (red), pending (yellow)
  - Description: "SDLC compliance: {score}% ({violations} violations)"
  - Target URL: Link to compliance report in SDLC Orchestrator dashboard
- [ ] **GITHUB-005**: Implement PR comment posting
  - GitHub API: POST /repos/{owner}/{repo}/issues/{pr_number}/comments
  - Comment body: Markdown table of violations
  - Only post if violations found (don't spam on success)
  - Use collapsed section for long reports (<details> tag)
- [ ] **TEST-010**: Write 10 unit tests
  - Push event: Gap analysis triggered
  - Push event: Slack notification sent (if score drops)
  - PR event: Gate evaluation triggered
  - PR event: Status check posted to GitHub
  - PR event: Comment posted (if violations)
  - PR event: No comment (if no violations)
  - Installation created: DB record created
  - Installation deleted: Projects unlinked
  - PR status check format (success, failure, pending)
  - PR comment format (Markdown table)

**Acceptance Criteria**:
- Gap analysis runs within 30s of push
- PR status checks appear on GitHub
- PR comments show violations clearly
- All 10 unit tests passing

---

### Day 3: Error Handling + Documentation (0.5 SP)

**Tasks**:
- [ ] **ERROR-007**: Handle webhook delivery failures
  - GitHub retries failed webhooks (exponential backoff)
  - Log failed deliveries (Sentry)
  - Manual retry endpoint: `POST /webhooks/retry/{delivery_id}`
  - Alert if failure rate >5% (Datadog)
- [ ] **ERROR-008**: Handle job processing failures
  - Retry failed jobs (max 3 retries, exponential backoff)
  - Dead letter queue (DLQ) for permanently failed jobs
  - Alert on DLQ size >10 (Slack notification)
- [ ] **ERROR-009**: Handle rate limit errors
  - GitHub API rate limit: 5000 requests/hour
  - If rate limited: Enqueue job for retry (after reset time)
  - Show warning in dashboard: "GitHub rate limit reached. Retry at {reset_time}"
- [ ] **DOC-008**: Write webhook setup guide
  - How to configure webhook URL (GitHub App settings)
  - How to test webhooks (ngrok for local dev)
  - How to verify signature (HMAC-SHA256)
  - How to troubleshoot failures (check logs)
- [ ] **DOC-009**: Write webhook event documentation
  - List of supported events (push, pull_request, installation)
  - Event payload examples (JSON)
  - Expected actions for each event
  - Retry behavior and failure handling
- [ ] **TEST-011**: Write 5 E2E tests
  - Push event → Gap analysis → Report updated
  - PR opened → Gate evaluation → Status check posted
  - PR synchronized → Re-evaluate → Status updated
  - Installation created → DB record created
  - Webhook signature invalid → 401 Unauthorized

**Acceptance Criteria**:
- Webhook failures are logged and alerted
- Failed jobs retry automatically
- Webhook guide published to docs
- All 5 E2E tests passing

---

## Technical Architecture

### Webhook Handler Flow

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│ GitHub   │     │ Backend  │     │  Redis   │     │ Celery   │
└────┬─────┘     └────┬─────┘     └────┬─────┘     └────┬─────┘
     │                │                │                │
     │ POST /webhooks/github           │                │
     │───────────────>│                │                │
     │                │                │                │
     │                │ Validate signature (HMAC-SHA256)│
     │                │                │                │
     │                │ Check idempotency (delivery_id) │
     │                │───────────────>│                │
     │                │                │                │
     │                │ EXISTS?        │                │
     │                │<───────────────│                │
     │                │                │                │
     │                │ If EXISTS: Return 200 OK        │
     │                │                │                │
     │                │ If NOT EXISTS: Store delivery_id│
     │                │───────────────>│                │
     │                │                │                │
     │                │ Enqueue job    │                │
     │                │───────────────>│                │
     │                │                │                │
     │ 202 Accepted   │                │                │
     │<───────────────│                │                │
     │                │                │                │
     │                │                │ Pick up job    │
     │                │                │───────────────>│
     │                │                │                │
     │                │                │ Process event  │
     │                │                │ (async)        │
     │                │                │                │
     │                │                │ Trigger gap    │
     │                │                │ analysis       │
     │                │                │                │
     │                │                │ Update DB      │
     │                │                │                │
     │                │<───────────────────────────────-│
     │                │ Job complete   │                │
     │                │                │                │
```

### PR Status Check Example

**GitHub API Call**:
```python
import requests

def post_pr_status_check(repo_full_name: str, commit_sha: str, status: str, description: str):
    """Post status check to GitHub PR"""
    token = github_app_service.get_installation_token(installation_id)

    payload = {
        "state": status,  # success, failure, pending
        "target_url": f"https://sdlc.nhatquangholding.com/projects/{project_id}/reports",
        "description": description,  # "SDLC compliance: 85% (3 violations)"
        "context": "SDLC Orchestrator / Compliance"
    }

    response = requests.post(
        f"https://api.github.com/repos/{repo_full_name}/statuses/{commit_sha}",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json"
        },
        json=payload
    )

    response.raise_for_status()
```

**GitHub UI Result**:
```
✅ SDLC Orchestrator / Compliance — SDLC compliance: 100% (0 violations)
❌ SDLC Orchestrator / Compliance — SDLC compliance: 70% (5 violations)
⏳ SDLC Orchestrator / Compliance — Running compliance check...
```

### PR Comment Example

**Markdown Template**:
```markdown
## 🔍 SDLC Compliance Report

**Compliance Score**: 70% (5 violations found)

<details>
<summary>❌ G1 Violations (2)</summary>

| Severity | Gate | Rule | File | Line |
|----------|------|------|------|------|
| HIGH | G1 | Missing required P0 artifact | docs/01-planning/Business-Case.md | - |
| MEDIUM | G1 | Incomplete stakeholder signoff | docs/01-planning/README.md | 45 |

</details>

<details>
<summary>⚠️ G2 Violations (3)</summary>

| Severity | Gate | Rule | File | Line |
|----------|------|------|------|------|
| HIGH | G2 | Architecture diagram missing | docs/02-design/System-Architecture.md | - |
| MEDIUM | G2 | API spec incomplete | docs/02-design/API-Design.md | 120 |
| LOW | G2 | ADR formatting inconsistent | docs/02-design/ADRs/ADR-001.md | 10 |

</details>

---

**View full report**: [SDLC Orchestrator Dashboard](https://sdlc.nhatquangholding.com/projects/abc123/reports/latest)
```

---

## Webhook Events

| Event | Trigger | Action | Output |
|-------|---------|--------|--------|
| `push` | Code pushed to branch | Run gap analysis | Update gap report, Slack notification |
| `pull_request` (opened) | PR created | Run gate evaluation | Post status check, PR comment (if violations) |
| `pull_request` (synchronized) | New commits pushed | Re-run gate evaluation | Update status check, update comment |
| `pull_request` (reopened) | PR reopened | Re-run gate evaluation | Post status check |
| `installation` (created) | App installed | Create DB record | Send welcome email |
| `installation` (deleted) | App uninstalled | Unlink projects | Send goodbye email |

---

## Performance Requirements

| Metric | Target | Measurement | Rationale |
|--------|--------|-------------|-----------|
| Webhook Response | <50ms (p95) | Backend timer | GitHub expects fast 2xx response |
| Job Processing | <30s (p95) | Celery timer | User expects results quickly |
| PR Status Check | <5s (p95) | GitHub API latency | Show check before user sees PR |
| Gap Analysis | <10s (typical repo) | Extension timer | Local filesystem scan |
| Webhook Delivery | >99% | GitHub webhooks dashboard | Industry standard |

---

## Security Considerations

### Webhook Signature Verification

**HMAC-SHA256 Validation**:
```python
import hmac
import hashlib

def verify_webhook_signature(payload: bytes, signature_header: str, secret: str) -> bool:
    """Verify GitHub webhook signature"""
    # Extract signature from header (format: "sha256=<hex>")
    if not signature_header.startswith("sha256="):
        return False

    signature = signature_header[7:]  # Remove "sha256=" prefix

    # Compute expected signature
    expected_signature = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()

    # Constant-time comparison (prevent timing attacks)
    return hmac.compare_digest(signature, expected_signature)
```

### Idempotency Protection

**Redis-based Idempotency**:
```python
from redis import Redis

def check_webhook_idempotency(redis: Redis, delivery_id: str) -> bool:
    """Check if webhook has already been processed"""
    key = f"webhook:delivery:{delivery_id}"

    # Try to set key (atomic operation)
    if redis.set(key, "processed", ex=86400, nx=True):
        # Key didn't exist, first time processing
        return True
    else:
        # Key already exists, duplicate delivery
        return False
```

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Webhook delivery failure | Medium | Medium | GitHub retries automatically (exponential backoff) |
| Job processing failure | Medium | High | Retry with exponential backoff (max 3), DLQ for permanent failures |
| Rate limit exceeded | Low | Medium | Queue jobs for retry after reset time |
| Large repo slow scan | Medium | Medium | Async processing, show "Processing..." status |
| Webhook spam attack | Low | High | Signature validation, rate limiting |
| GitHub API downtime | Low | High | Fallback to manual trigger, alert on failures |

---

## Definition of Done

- [ ] All 3 user stories completed
- [ ] 23 tests passing (8 + 10 + 5)
- [ ] Code coverage >95%
- [ ] Security scan passing (Semgrep)
- [ ] Performance requirements met (<30s processing)
- [ ] Webhook signature validation tested
- [ ] PR status checks working on test repo
- [ ] Documentation published
- [ ] Demo to stakeholders completed
- [ ] CTO approval received

---

## Sprint Retrospective Template

**What went well**:
- [ ] Webhook handler (fast, reliable)
- [ ] Idempotency (no duplicate processing)
- [ ] PR status checks (good UX)

**What could be improved**:
- [ ] Error handling (more resilient retry logic)
- [ ] Job processing (optimize gap analysis speed)
- [ ] Documentation (more examples)

**Deferred to Sprint 130**:
- [ ] Webhook dashboard (show delivery stats)
- [ ] Webhook replay (manually re-process events)
- [ ] Advanced PR checks (block merge if violations)

**Action items**:
- [ ] Monitor webhook delivery rate
- [ ] Track job processing time
- [ ] Gather user feedback on PR comments

---

**Sprint Owner**: Backend Lead
**Product Owner**: CTO
**Stakeholders**: DevOps Team, Extension Team

**Status**: 🟡 READY FOR KICKOFF (Mar 1, 2026) - POST-LAUNCH
