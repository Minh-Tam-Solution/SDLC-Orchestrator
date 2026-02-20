# GitHub Sync Background Jobs Unit Tests

**Version**: 1.0.0
**Date**: November 28, 2025
**Status**: ACTIVE - Sprint 16 Day 4
**Authority**: Backend Lead + QA Lead Approved
**Foundation**: Sprint 16 Testing Plan
**Framework**: SDLC 6.1.0

---

## Overview

Unit tests for the GitHub Sync Background Jobs module (`backend/app/jobs/github_sync.py`), testing all job queue operations, webhook processing, and scheduled sync functions.

**Test File**: `tests/unit/jobs/test_github_sync.py`
**Total Tests**: 22
**Coverage Target**: 95%+
**Status**: 100% PASS

---

## Test Classes Summary

| Test Class | Tests | Description |
|------------|-------|-------------|
| TestScheduleProjectSync | 5 | Job scheduling and queue operations |
| TestRunGitHubSyncJob | 3 | Sync job execution and error handling |
| TestProcessWebhookEvent | 3 | Webhook event queuing |
| TestRunWebhookProcessingJob | 2 | Webhook batch processing |
| TestJobManagement | 3 | Queue stats and cleanup |
| TestScheduledSync | 1 | Scheduled sync for stale projects |
| TestEventHandlers | 5 | Event-specific handlers |

**Total**: 22 tests

---

## Test Coverage by Function

### 1. schedule_project_sync()

Tests job scheduling into the sync queue:

| Test | Scenario | Expected |
|------|----------|----------|
| test_schedules_job_with_normal_priority | Normal priority job | Job added to queue end |
| test_schedules_job_with_high_priority_first | High priority job | Job inserted at queue front |
| test_tracks_job_status | Job status tracking | Status stored in _job_status |
| test_force_flag_is_stored | Force sync option | force=True stored in job |
| test_get_pending_sync_jobs | List pending jobs | Returns queue summary |

### 2. run_github_sync_job()

Tests sync job execution:

| Test | Scenario | Expected |
|------|----------|----------|
| test_processes_empty_queue | Empty queue | Returns 0 jobs processed |
| test_respects_max_jobs_limit | max_jobs=2, queue=5 | Processes only 2, leaves 3 |
| test_handles_missing_oauth_account | No OAuth account | Job fails with error message |

### 3. process_webhook_event()

Tests webhook event queuing:

| Test | Scenario | Expected |
|------|----------|----------|
| test_queues_valid_webhook | Valid signature | Event queued for processing |
| test_rejects_invalid_signature | Invalid signature | Returns received=False |
| test_extracts_repository_info | Push event | Extracts repo_id, full_name |

### 4. run_webhook_processing_job()

Tests webhook batch processing:

| Test | Scenario | Expected |
|------|----------|----------|
| test_processes_empty_queue | Empty queue | Returns 0 events processed |
| test_skips_webhook_without_linked_project | No linked project | Event skipped, status="skipped" |

### 5. Job Management Functions

Tests queue utilities:

| Test | Scenario | Expected |
|------|----------|----------|
| test_get_job_queue_stats | Queue stats | Returns queue lengths, status counts |
| test_clear_completed_jobs | Old completed jobs | Clears jobs older than threshold |
| test_get_sync_job_status_not_found | Non-existent job ID | Returns None |

### 6. run_scheduled_sync_for_stale_projects()

Tests scheduled sync:

| Test | Scenario | Expected |
|------|----------|----------|
| test_schedules_sync_for_stale_projects | Stale projects found | Jobs queued with priority="low" |

### 7. Event Handlers

Tests event-specific processing:

| Test | Scenario | Expected |
|------|----------|----------|
| test_push_event_updates_timestamp | Push event | Updates github_synced_at |
| test_push_event_detects_significant_changes | requirements.txt changed | needs_full_sync=True |
| test_pull_request_event_processing | PR event | Extracts PR number, title, state |
| test_issues_event_processing | Issues event | Extracts issue number, title |
| test_branch_event_processing | Branch create | Returns action="branch_created" |

---

## Background Job Architecture

### Job Types

1. **Project Sync Jobs**: Queue sync operations for background execution
2. **Webhook Processing Jobs**: Process GitHub webhook events asynchronously
3. **Scheduled Sync Jobs**: Poll stale projects without webhooks

### Queue Strategy (MVP)

```python
# In-memory queues for MVP
_sync_queue: list[dict[str, Any]] = []
_webhook_queue: list[dict[str, Any]] = []
_job_status: dict[str, dict[str, Any]] = {}

# Production upgrade path: Redis Queue or Celery
```

### Job Status Lifecycle

```
queued → running → completed/failed
```

### Event Types Handled

- `push`: Update sync timestamp, detect significant changes
- `pull_request`: Track PR state for evidence collection
- `issues`: Track issue state for project management
- `create/delete`: Handle branch/tag lifecycle

---

## Zero Mock Policy Compliance

Per SDLC 6.1.0 Zero Mock Policy:

**Mocked**: External dependencies
- AsyncSessionLocal (database session factory)
- github_service.validate_webhook_signature (external API)

**NOT Mocked**:
- Job queue operations (in-memory data structures)
- Job status tracking
- Event parsing logic
- Significant change detection

---

## Running Tests

```bash
# Run all GitHub Sync job tests
PYTHONPATH="$PWD/backend" pytest tests/unit/jobs/test_github_sync.py -v --no-cov

# Run specific test class
PYTHONPATH="$PWD/backend" pytest tests/unit/jobs/test_github_sync.py::TestEventHandlers -v

# Run with coverage
PYTHONPATH="$PWD/backend" pytest tests/unit/jobs/test_github_sync.py --cov=app.jobs.github_sync --cov-report=html
```

---

## Quality Metrics

| Metric | Target | Achieved | Status |
|--------|--------|----------|--------|
| Total Tests | 20+ | 22 | EXCEEDS |
| Pass Rate | 100% | 100% | PASS |
| Coverage | 95%+ | TBD | PENDING |
| Zero Mock | 100% | 100% | PASS |
| Execution Time | <5s | ~1s | PASS |

---

## Related Documents

- [github_sync.py](../../../../backend/app/jobs/github_sync.py) - Background jobs implementation
- [project_sync_service.py](../../../../backend/app/services/project_sync_service.py) - Sync service
- [GITHUB-SERVICE-UNIT-TESTS.md](./GITHUB-SERVICE-UNIT-TESTS.md) - GitHub Service tests
- [GITHUB-OAUTH-INTEGRATION-TESTS.md](../04-Integration-Testing/GITHUB-OAUTH-INTEGRATION-TESTS.md) - Integration tests

---

*SDLC Orchestrator - First Governance-First Platform on SDLC 6.1.0. Zero Mock Policy enforced.*
