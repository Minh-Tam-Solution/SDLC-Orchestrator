# Complete API Endpoint Reference

**API**: SDLC Orchestrator API
**Version**: 1.4.0
**OpenAPI**: 3.1.0
**Description**: AI-Native SDLC Governance Platform with Quality Gates
**Last Updated**: February 8, 2026 (Sprint 147 - Product Truth Layer)

---

## Table of Contents

- [AGENTS.md](#agents.md) (16 endpoints)
- [AI](#ai) (2 endpoints)
- [AI Council](#ai-council) (10 endpoints)
- [AI Detection](#ai-detection) (12 endpoints)
- [AI Providers](#ai-providers) (10 endpoints)
- [API Keys](#api-keys) (6 endpoints)
- [Admin Panel](#admin-panel) (22 endpoints)
- [Agentic Maturity](#agentic-maturity) (12 endpoints)
- [Analytics](#analytics) (37 endpoints)
- [Analytics v2](#analytics-v2) (8 endpoints)
- [Authentication](#authentication) (26 endpoints)
- [Auto-Generation](#auto-generation) (12 endpoints)
- [CEO Dashboard](#ceo-dashboard) (14 endpoints)
- [CRP - Consultations](#crp---consultations) (14 endpoints)
- [Check Runs](#check-runs) (5 endpoints)
- [Codegen](#codegen) (58 endpoints)
- [Compliance](#compliance) (26 endpoints)
- [Compliance Validation](#compliance-validation) (10 endpoints)
- [Context Authority](#context-authority) (7 endpoints)
- [Context Authority V2](#context-authority-v2) (22 endpoints)
- [Context Overlay](#context-overlay) (2 endpoints)
- [Context Validation](#context-validation) (8 endpoints)
- [Contract Lock](#contract-lock) (14 endpoints)
- [Cross-Reference](#cross-reference) (8 endpoints)
- [Dashboard](#dashboard) (2 endpoints)
- [Dependencies](#dependencies) (10 endpoints)
- [Documentation](#documentation) (4 endpoints)
- [Dogfooding](#dogfooding) (20 endpoints)
- [E2E Testing](#e2e-testing) (10 endpoints)
- [Evidence](#evidence) (3 endpoints)
- [Evidence Manifest](#evidence-manifest) (7 endpoints)
- [Evidence Timeline](#evidence-timeline) (7 endpoints)
- [Feedback](#feedback) (14 endpoints)
- [Feedback Learning](#feedback-learning) (22 endpoints)
- [Feedback Learning (EP-11)](#feedback-learning-(ep-11)) (22 endpoints)
- [Framework Version](#framework-version) (12 endpoints)
- [Gates](#gates) (16 endpoints)
- [Gates Engine](#gates-engine) (16 endpoints)
- [GitHub](#github) (13 endpoints)
- [Governance Metrics](#governance-metrics) (14 endpoints)
- [Governance Mode](#governance-mode) (8 endpoints)
- [Governance Specs](#governance-specs) (5 endpoints)
- [Governance Vibecoding](#governance-vibecoding) (7 endpoints)
- [Grafana Dashboards](#grafana-dashboards) (7 endpoints)
- [MRP - Merge Readiness Protocol](#mrp---merge-readiness-protocol) (18 endpoints)
- [MRP - Policy Enforcement](#mrp---policy-enforcement) (4 endpoints)
- [Notifications](#notifications) (8 endpoints)
- [Organization Invitations](#organization-invitations) (7 endpoints)
- [Organizations](#organizations) (6 endpoints)
- [Override / VCR](#override---vcr) (9 endpoints)
- [Payments](#payments) (5 endpoints)
- [Pilot](#pilot) (13 endpoints)
- [Planning](#planning) (46 endpoints)
- [Planning Hierarchy](#planning-hierarchy) (150 endpoints)
- [Planning Sub-agent](#planning-sub-agent) (16 endpoints)
- [Policies](#policies) (5 endpoints)
- [Policy Packs](#policy-packs) (8 endpoints)
- [Preview](#preview) (6 endpoints)
- [Projects](#projects) (9 endpoints)
- [Resource Allocation](#resource-allocation) (11 endpoints)
- [Retrospective](#retrospective) (9 endpoints)
- [Risk Analysis](#risk-analysis) (8 endpoints)
- [SAST](#sast) (14 endpoints)
- [SDLC Structure](#sdlc-structure) (6 endpoints)
- [SOP Generator](#sop-generator) (16 endpoints)
- [Sprint 77](#sprint-77) (3 endpoints)
- [Sprint 78](#sprint-78) (39 endpoints)
- [Stage Gating](#stage-gating) (7 endpoints)
- [Teams](#teams) (10 endpoints)
- [Telemetry](#telemetry) (3 endpoints)
- [Templates](#templates) (9 endpoints)
- [Tier Management](#tier-management) (5 endpoints)
- [Triage](#triage) (12 endpoints)
- [Uncategorized](#uncategorized) (4 endpoints)
- [Vibecoding Index](#vibecoding-index) (7 endpoints)
- [dashboard](#dashboard) (2 endpoints)
- [dogfooding](#dogfooding) (20 endpoints)
- [github](#github) (13 endpoints)
- [organization-invitations](#organization-invitations) (7 endpoints)
- [organizations](#organizations) (6 endpoints)
- [payments](#payments) (5 endpoints)
- [pilot](#pilot) (13 endpoints)
- [projects](#projects) (9 endpoints)
- [teams](#teams) (10 endpoints)

---

## AGENTS.md

### 🔵 GET `/api/v1/agents-md/context/{project_id}`

**Summary**: Get context overlay


---

### 🔵 GET `/api/v1/agents-md/context/{project_id}`

**Summary**: Get context overlay


---

### 🔵 GET `/api/v1/agents-md/context/{project_id}/history`

**Summary**: Get context overlay history

**Description**: Get context overlay delivery history for a project.

---

### 🔵 GET `/api/v1/agents-md/context/{project_id}/history`

**Summary**: Get context overlay history

**Description**: Get context overlay delivery history for a project.

---

### 🟢 POST `/api/v1/agents-md/generate`

**Summary**: Generate AGENTS.md

**Description**: Generate AGENTS.md from project configuration analysis.

---

### 🟢 POST `/api/v1/agents-md/generate`

**Summary**: Generate AGENTS.md

**Description**: Generate AGENTS.md from project configuration analysis.

---

### 🟢 POST `/api/v1/agents-md/lint`

**Summary**: Lint AGENTS.md


---

### 🟢 POST `/api/v1/agents-md/lint`

**Summary**: Lint AGENTS.md


---

### 🔵 GET `/api/v1/agents-md/repos`

**Summary**: List all repositories with AGENTS.md status

**Description**: Get list of all accessible projects with their AGENTS.md status.

---

### 🔵 GET `/api/v1/agents-md/repos`

**Summary**: List all repositories with AGENTS.md status

**Description**: Get list of all accessible projects with their AGENTS.md status.

---

### 🟢 POST `/api/v1/agents-md/validate`

**Summary**: Validate AGENTS.md

**Description**: Validate AGENTS.md content for secrets, structure, and line limits.

---

### 🟢 POST `/api/v1/agents-md/validate`

**Summary**: Validate AGENTS.md

**Description**: Validate AGENTS.md content for secrets, structure, and line limits.

---

### 🔵 GET `/api/v1/agents-md/{project_id}`

**Summary**: Get latest AGENTS.md


---

### 🔵 GET `/api/v1/agents-md/{project_id}`

**Summary**: Get latest AGENTS.md


---

### 🔵 GET `/api/v1/agents-md/{project_id}/history`

**Summary**: Get AGENTS.md history


---

### 🔵 GET `/api/v1/agents-md/{project_id}/history`

**Summary**: Get AGENTS.md history


---

## AI

### 🔵 GET `/api/v1/planning/sprints/{sprint_id}/analytics`

**Summary**: Get comprehensive sprint analytics

<details>
<summary>View full description</summary>

Get comprehensive analytics for a sprint.

**Sprint 76: AI Sprint Assistant - Full Analytics**

Combines velocity, health, and suggestions into a single response
with an AI-generated summary of sprint status.

Args:
    sprint_id: Sprint UUID

Returns:
    SprintAnalyticsResponse with full analytics

Raises:
    404: Sprint not found

</details>

---

### 🔵 GET `/api/v1/planning/sprints/{sprint_id}/suggestions`

**Summary**: Get AI prioritization suggestions

<details>
<summary>View full description</summary>

Get AI-powered prioritization suggestions for a sprint.

**Sprint 76: AI Sprint Assistant - Recommendations**

Analyzes sprint backlog and generates suggestions:
- start_p0: P0 items not yet started (critical)
- unassigned_priority: Unassigned P0/P1 items
- overloaded: Sprint capacity exceeds velocity
- blocked: Items requiring unblocking
- p2_at_risk: Low-priority items at risk
- underloaded: Capacity opportunity

Args:
    sprint_id: Sprint UUID

Returns:
    SprintSuggestionsResponse with AI suggestions

Raises:
    404: Sprint not found

</details>

---

## AI Council

### 🟢 POST `/api/v1/council/decide`

**Summary**: Request council decision with sprint context

<details>
<summary>View full description</summary>

Sprint 77 Day 1: AI Council Sprint Context Integration

    Request an AI Council decision with full sprint context.
    The council considers sprint health, team availability, velocity,
    and backlog status when making decisions.

    Decision types:
    - code_review: Review code changes
    - architecture: Architecture decisions
    - security: Security review
    - prioritization: Backlog prioritization
    - estimation: Story point estimation
    - blocker: Blocker resolution

</details>

---

### 🟢 POST `/api/v1/council/decide`

**Summary**: Request council decision with sprint context

<details>
<summary>View full description</summary>

Sprint 77 Day 1: AI Council Sprint Context Integration

    Request an AI Council decision with full sprint context.
    The council considers sprint health, team availability, velocity,
    and backlog status when making decisions.

    Decision types:
    - code_review: Review code changes
    - architecture: Architecture decisions
    - security: Security review
    - prioritization: Backlog prioritization
    - estimation: Story point estimation
    - blocker: Blocker resolution

</details>

---

### 🟢 POST `/api/v1/council/deliberate`

**Summary**: Trigger AI Council deliberation

**Description**: Trigger AI Council deliberation for a compliance violation. Uses 3-stage process: parallel queries, peer review, chairman synthesis.

---

### 🟢 POST `/api/v1/council/deliberate`

**Summary**: Trigger AI Council deliberation

**Description**: Trigger AI Council deliberation for a compliance violation. Uses 3-stage process: parallel queries, peer review, chairman synthesis.

---

### 🔵 GET `/api/v1/council/history/{project_id}`

**Summary**: Get project council history


---

### 🔵 GET `/api/v1/council/history/{project_id}`

**Summary**: Get project council history


---

### 🔵 GET `/api/v1/council/stats/{project_id}`

**Summary**: Get project council statistics

**Description**: Get aggregated statistics for council deliberations in a project.

---

### 🔵 GET `/api/v1/council/stats/{project_id}`

**Summary**: Get project council statistics

**Description**: Get aggregated statistics for council deliberations in a project.

---

### 🔵 GET `/api/v1/council/status/{request_id}`

**Summary**: Get deliberation status

**Description**: Get the status and result of a council deliberation request.

---

### 🔵 GET `/api/v1/council/status/{request_id}`

**Summary**: Get deliberation status

**Description**: Get the status and result of a council deliberation request.

---

## AI Detection

### 🟢 POST `/api/v1/ai-detection/analyze`

**Summary**: Analyze Pr

<details>
<summary>View full description</summary>

Analyze a PR for AI-generated content.

This endpoint can be used for:
- Manual testing of the detection service
- Integration with GitHub webhooks
- Debugging detection issues

The result is also logged in shadow mode for production validation.

</details>

---

### 🟢 POST `/api/v1/ai-detection/analyze`

**Summary**: Analyze Pr

<details>
<summary>View full description</summary>

Analyze a PR for AI-generated content.

This endpoint can be used for:
- Manual testing of the detection service
- Integration with GitHub webhooks
- Debugging detection issues

The result is also logged in shadow mode for production validation.

</details>

---

### 🔵 GET `/api/v1/ai-detection/circuit-breakers`

**Summary**: Get Circuit Breakers

<details>
<summary>View full description</summary>

Get circuit breaker status for all external services.

CTO P2: Monitor circuit breaker health for external API calls.

Returns:
    Status of all circuit breakers including:
    - Current state (closed/open/half_open)
    - Failure/success counts
    - Configuration thresholds

</details>

---

### 🔵 GET `/api/v1/ai-detection/circuit-breakers`

**Summary**: Get Circuit Breakers

<details>
<summary>View full description</summary>

Get circuit breaker status for all external services.

CTO P2: Monitor circuit breaker health for external API calls.

Returns:
    Status of all circuit breakers including:
    - Current state (closed/open/half_open)
    - Failure/success counts
    - Configuration thresholds

</details>

---

### 🟢 POST `/api/v1/ai-detection/circuit-breakers/{breaker_name}/reset`

**Summary**: Reset Circuit Breaker

<details>
<summary>View full description</summary>

Reset a circuit breaker to closed state.

Use this endpoint to manually recover a circuit breaker
after fixing the underlying issue.

Args:
    breaker_name: Name of the circuit breaker (github_api, external_ai)

Returns:
    Updated circuit breaker status

</details>

---

### 🟢 POST `/api/v1/ai-detection/circuit-breakers/{breaker_name}/reset`

**Summary**: Reset Circuit Breaker

<details>
<summary>View full description</summary>

Reset a circuit breaker to closed state.

Use this endpoint to manually recover a circuit breaker
after fixing the underlying issue.

Args:
    breaker_name: Name of the circuit breaker (github_api, external_ai)

Returns:
    Updated circuit breaker status

</details>

---

### 🔵 GET `/api/v1/ai-detection/shadow-mode`

**Summary**: Get Shadow Mode

**Description**: Get shadow mode configuration and status.

Shadow mode enables production validation without affecting users.

---

### 🔵 GET `/api/v1/ai-detection/shadow-mode`

**Summary**: Get Shadow Mode

**Description**: Get shadow mode configuration and status.

Shadow mode enables production validation without affecting users.

---

### 🔵 GET `/api/v1/ai-detection/status`

**Summary**: Get Detection Status

**Description**: Get AI detection service status and configuration.

Returns current detection threshold, strategies, weights, and shadow mode status.

---

### 🔵 GET `/api/v1/ai-detection/status`

**Summary**: Get Detection Status

**Description**: Get AI detection service status and configuration.

Returns current detection threshold, strategies, weights, and shadow mode status.

---

### 🔵 GET `/api/v1/ai-detection/tools`

**Summary**: Get Supported Tools

**Description**: Get list of supported AI tools for detection.

Returns all AI coding tools that can be detected by the service.

---

### 🔵 GET `/api/v1/ai-detection/tools`

**Summary**: Get Supported Tools

**Description**: Get list of supported AI tools for detection.

Returns all AI coding tools that can be detected by the service.

---

## AI Providers

### 🔵 GET `/api/v1/admin/ai-providers/config`

**Summary**: Get AI provider configuration

**Description**: Get full AI provider configuration including status and available models

---

### 🔵 GET `/api/v1/admin/ai-providers/config`

**Summary**: Get AI provider configuration

**Description**: Get full AI provider configuration including status and available models

---

### 🟢 POST `/api/v1/admin/ai-providers/ollama/refresh-models`

**Summary**: Refresh Ollama models

**Description**: Fetch fresh list of available models from Ollama server

---

### 🟢 POST `/api/v1/admin/ai-providers/ollama/refresh-models`

**Summary**: Refresh Ollama models

**Description**: Fetch fresh list of available models from Ollama server

---

### 🟠 PATCH `/api/v1/admin/ai-providers/{provider}`

**Summary**: Update provider settings


---

### 🟠 PATCH `/api/v1/admin/ai-providers/{provider}`

**Summary**: Update provider settings


---

### 🔵 GET `/api/v1/admin/ai-providers/{provider}/models`

**Summary**: Get available models for provider

**Description**: Get list of available models for a specific provider

---

### 🔵 GET `/api/v1/admin/ai-providers/{provider}/models`

**Summary**: Get available models for provider

**Description**: Get list of available models for a specific provider

---

### 🟢 POST `/api/v1/admin/ai-providers/{provider}/test`

**Summary**: Test provider connection


---

### 🟢 POST `/api/v1/admin/ai-providers/{provider}/test`

**Summary**: Test provider connection


---

## API Keys

### 🟢 POST `/api/v1/api-keys`

**Summary**: Create Api Key

<details>
<summary>View full description</summary>

Create a new API key for the current user.

**Important**: The API key will only be shown ONCE in the response.
Make sure to copy and save it securely.

Request Body:
    {
        "name": "VS Code Extension",
        "expires_in_days": 90  // Optional, null = never expires
    }

Response (201 Created):
    {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "VS Code Extension",
        "api_key": "sdlc_live_abc123...",  // SAVE THIS!
        "prefix": "sdlc_live_abc...",
        "expires_at": "2026-03-26T00:00:00Z",
        "created_at": "2025-12-26T10:00:00Z"
    }

Usage:
    - Use the `api_key` value in VS Code extension settings
    - Or set as Authorization header: `Bearer <api_key>`

</details>

---

### 🟢 POST `/api/v1/api-keys`

**Summary**: Create Api Key

<details>
<summary>View full description</summary>

Create a new API key for the current user.

**Important**: The API key will only be shown ONCE in the response.
Make sure to copy and save it securely.

Request Body:
    {
        "name": "VS Code Extension",
        "expires_in_days": 90  // Optional, null = never expires
    }

Response (201 Created):
    {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "VS Code Extension",
        "api_key": "sdlc_live_abc123...",  // SAVE THIS!
        "prefix": "sdlc_live_abc...",
        "expires_at": "2026-03-26T00:00:00Z",
        "created_at": "2025-12-26T10:00:00Z"
    }

Usage:
    - Use the `api_key` value in VS Code extension settings
    - Or set as Authorization header: `Bearer <api_key>`

</details>

---

### 🔵 GET `/api/v1/api-keys`

**Summary**: List Api Keys

<details>
<summary>View full description</summary>

List all API keys for the current user.

Response (200 OK):
    [
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "name": "VS Code Extension",
            "prefix": "sdlc_live_abc...",
            "last_used_at": "2025-12-26T10:00:00Z",
            "expires_at": "2026-03-26T00:00:00Z",
            "is_active": true,
            "created_at": "2025-12-26T10:00:00Z"
        }
    ]

Note:
    - The actual API key is NOT returned (only shown on creation)
    - Use the `prefix` to identify which key is which

</details>

---

### 🔵 GET `/api/v1/api-keys`

**Summary**: List Api Keys

<details>
<summary>View full description</summary>

List all API keys for the current user.

Response (200 OK):
    [
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "name": "VS Code Extension",
            "prefix": "sdlc_live_abc...",
            "last_used_at": "2025-12-26T10:00:00Z",
            "expires_at": "2026-03-26T00:00:00Z",
            "is_active": true,
            "created_at": "2025-12-26T10:00:00Z"
        }
    ]

Note:
    - The actual API key is NOT returned (only shown on creation)
    - Use the `prefix` to identify which key is which

</details>

---

### 🔴 DELETE `/api/v1/api-keys/{key_id}`

**Summary**: Revoke Api Key

<details>
<summary>View full description</summary>

Revoke (delete) an API key.

Path Parameters:
    key_id: UUID of the API key to revoke

Response (204 No Content):
    (empty response)

Errors:
    - 404 Not Found: API key not found or doesn't belong to user

</details>

---

### 🔴 DELETE `/api/v1/api-keys/{key_id}`

**Summary**: Revoke Api Key

<details>
<summary>View full description</summary>

Revoke (delete) an API key.

Path Parameters:
    key_id: UUID of the API key to revoke

Response (204 No Content):
    (empty response)

Errors:
    - 404 Not Found: API key not found or doesn't belong to user

</details>

---

## Admin Panel

### 🔵 GET `/api/v1/admin/audit-logs`

**Summary**: List audit logs (paginated)


---

### 🟢 POST `/api/v1/admin/evidence/retention-archive`

**Summary**: Trigger evidence archival (ADR-027)

**Description**: Manually trigger archival of evidence older than retention period

---

### 🟢 POST `/api/v1/admin/evidence/retention-purge`

**Summary**: Trigger evidence purge (ADR-027)

**Description**: Manually trigger permanent deletion of archived evidence beyond grace period

---

### 🔵 GET `/api/v1/admin/evidence/retention-stats`

**Summary**: Get evidence retention statistics (ADR-027)

**Description**: Get current evidence retention stats including active, archived, and due for cleanup

---

### 🔵 GET `/api/v1/admin/settings`

**Summary**: Get all system settings


---

### 🔵 GET `/api/v1/admin/settings/{key}`

**Summary**: Get setting by key


---

### 🟠 PATCH `/api/v1/admin/settings/{key}`

**Summary**: Update setting


---

### 🟢 POST `/api/v1/admin/settings/{key}/rollback`

**Summary**: Rollback setting


---

### 🔵 GET `/api/v1/admin/stats`

**Summary**: Get admin dashboard statistics

**Description**: Get platform statistics including user counts, project counts, and system status.

---

### 🔵 GET `/api/v1/admin/system/health`

**Summary**: Get system health


---

### 🔵 GET `/api/v1/admin/users`

**Summary**: List all users (paginated)

**Description**: Get paginated list of all users with search and filter capabilities.

---

### 🟢 POST `/api/v1/admin/users`

**Summary**: Create new user

**Description**: Create a new user account with email and password (Sprint 40).

---

### 🔴 DELETE `/api/v1/admin/users/bulk`

**Summary**: Bulk delete users (soft delete)

**Description**: Soft delete multiple users at once with full audit trail (Sprint 40 Part 3).

---

### 🟢 POST `/api/v1/admin/users/bulk`

**Summary**: Bulk user action


---

### 🔵 GET `/api/v1/admin/users/{user_id}`

**Summary**: Get user details


---

### 🟠 PATCH `/api/v1/admin/users/{user_id}`

**Summary**: Update user

**Description**: Update user information (name, email, password, is_active, is_superuser) - Sprint 40 Part 2.

---

### 🔴 DELETE `/api/v1/admin/users/{user_id}`

**Summary**: Delete user (soft delete)

**Description**: Soft delete a user account with audit trail (Sprint 40).

---

### 🟢 POST `/api/v1/admin/users/{user_id}/mfa-exempt`

**Summary**: Set MFA exemption (ADR-027)

**Description**: Admin can exempt specific users from MFA requirement

---

### 🔵 GET `/api/v1/admin/users/{user_id}/mfa-status`

**Summary**: Get user MFA status (ADR-027)


---

### 🔴 DELETE `/api/v1/admin/users/{user_id}/permanent`

**Summary**: Permanently delete user (Sprint 105)

**Description**: Permanently delete a soft-deleted user. This action is irreversible.

---

### 🟢 POST `/api/v1/admin/users/{user_id}/restore`

**Summary**: Restore deleted user (Sprint 105)


---

### 🟢 POST `/api/v1/admin/users/{user_id}/unlock`

**Summary**: Unlock user account (ADR-027)

**Description**: Admin can manually unlock accounts locked due to failed login attempts

---

## Agentic Maturity

### 🔵 GET `/api/v1/maturity/health`

**Summary**: Health check


---

### 🔵 GET `/api/v1/maturity/health`

**Summary**: Health check


---

### 🔵 GET `/api/v1/maturity/levels`

**Summary**: Get maturity level definitions


---

### 🔵 GET `/api/v1/maturity/levels`

**Summary**: Get maturity level definitions


---

### 🔵 GET `/api/v1/maturity/org/{org_id}`

**Summary**: Get org-wide maturity report

**Description**: Get maturity report for all projects in an organization.

---

### 🔵 GET `/api/v1/maturity/org/{org_id}`

**Summary**: Get org-wide maturity report

**Description**: Get maturity report for all projects in an organization.

---

### 🔵 GET `/api/v1/maturity/{project_id}`

**Summary**: Get latest maturity assessment

**Description**: Get the most recent maturity assessment for a project.

---

### 🔵 GET `/api/v1/maturity/{project_id}`

**Summary**: Get latest maturity assessment

**Description**: Get the most recent maturity assessment for a project.

---

### 🟢 POST `/api/v1/maturity/{project_id}/assess`

**Summary**: Perform fresh maturity assessment


---

### 🟢 POST `/api/v1/maturity/{project_id}/assess`

**Summary**: Perform fresh maturity assessment


---

### 🔵 GET `/api/v1/maturity/{project_id}/history`

**Summary**: Get assessment history


---

### 🔵 GET `/api/v1/maturity/{project_id}/history`

**Summary**: Get assessment history


---

## Analytics

### 🔵 GET `/api/v1/analytics/circuit-breaker/status`

**Summary**: Get Circuit Breaker Status

<details>
<summary>View full description</summary>

Get Mixpanel circuit breaker status.

Returns current circuit state, failure count, and recovery info.

Circuit States:
- CLOSED: Normal operation (Mixpanel enabled)
- OPEN: Too many failures (Mixpanel disabled, PostgreSQL-only)
- HALF_OPEN: Testing recovery after timeout

CTO Condition #2: Monitor circuit breaker health

</details>

---

### 🔵 GET `/api/v1/analytics/circuit-breaker/status`

**Summary**: Get Circuit Breaker Status

<details>
<summary>View full description</summary>

Get Mixpanel circuit breaker status.

Returns current circuit state, failure count, and recovery info.

Circuit States:
- CLOSED: Normal operation (Mixpanel enabled)
- OPEN: Too many failures (Mixpanel disabled, PostgreSQL-only)
- HALF_OPEN: Testing recovery after timeout

CTO Condition #2: Monitor circuit breaker health

</details>

---

### 🔵 GET `/api/v1/analytics/engagement`

**Summary**: Get Engagement Summary

**Description**: Get engagement summary for dashboard.

Returns today's and this week's metrics.

---

### 🔵 GET `/api/v1/analytics/engagement`

**Summary**: Get Engagement Summary

**Description**: Get engagement summary for dashboard.

Returns today's and this week's metrics.

---

### 🟢 POST `/api/v1/analytics/events`

**Summary**: Track Event

**Description**: Track a usage event.

Generic event tracking for any type of user activity.
For specific events, use dedicated endpoints (page views, features).

---

### 🟢 POST `/api/v1/analytics/events`

**Summary**: Track Event

**Description**: Track a usage event.

Generic event tracking for any type of user activity.
For specific events, use dedicated endpoints (page views, features).

---

### 🟢 POST `/api/v1/analytics/events/feature`

**Summary**: Track Feature Use


---

### 🟢 POST `/api/v1/analytics/events/feature`

**Summary**: Track Feature Use


---

### 🟢 POST `/api/v1/analytics/events/page-view`

**Summary**: Track Page View


---

### 🟢 POST `/api/v1/analytics/events/page-view`

**Summary**: Track Page View


---

### 🔵 GET `/api/v1/analytics/features`

**Summary**: Get Feature Usage

**Description**: Get feature usage statistics.

Returns aggregated feature usage for the last N days.

---

### 🔵 GET `/api/v1/analytics/features`

**Summary**: Get Feature Usage

**Description**: Get feature usage statistics.

Returns aggregated feature usage for the last N days.

---

### 🔵 GET `/api/v1/analytics/my-activity`

**Summary**: Get My Activity

**Description**: Get the current user's recent activity.

Returns events from the last N days (default 7).

---

### 🔵 GET `/api/v1/analytics/my-activity`

**Summary**: Get My Activity

**Description**: Get the current user's recent activity.

Returns events from the last N days (default 7).

---

### 🔵 GET `/api/v1/analytics/pilot-metrics`

**Summary**: Get Pilot Metrics

**Description**: Get pilot program metrics for dashboard.

Returns daily metrics for the last N days.

---

### 🔵 GET `/api/v1/analytics/pilot-metrics`

**Summary**: Get Pilot Metrics

**Description**: Get pilot program metrics for dashboard.

Returns daily metrics for the last N days.

---

### 🟢 POST `/api/v1/analytics/pilot-metrics/calculate`

**Summary**: Calculate Today Metrics

**Description**: Manually trigger pilot metrics calculation for today.

This is typically done by a scheduled job, but can be triggered manually.

---

### 🟢 POST `/api/v1/analytics/pilot-metrics/calculate`

**Summary**: Calculate Today Metrics

**Description**: Manually trigger pilot metrics calculation for today.

This is typically done by a scheduled job, but can be triggered manually.

---

### 🟢 POST `/api/v1/analytics/retention/cleanup`

**Summary**: Run Retention Cleanup

<details>
<summary>View full description</summary>

Manually trigger analytics retention cleanup.

Deletes events older than retention period (default: 90 days).
This is typically run by cron job daily at 2:00 AM UTC.

Requires: Admin role (future enhancement)

CTO Condition #3: Manual cleanup trigger for testing/emergency

</details>

---

### 🟢 POST `/api/v1/analytics/retention/cleanup`

**Summary**: Run Retention Cleanup

<details>
<summary>View full description</summary>

Manually trigger analytics retention cleanup.

Deletes events older than retention period (default: 90 days).
This is typically run by cron job daily at 2:00 AM UTC.

Requires: Admin role (future enhancement)

CTO Condition #3: Manual cleanup trigger for testing/emergency

</details>

---

### 🔵 GET `/api/v1/analytics/retention/stats`

**Summary**: Get Retention Stats

**Description**: Get analytics data retention statistics.

Returns current storage metrics and events older than retention period.

CTO Condition #3: Monitor retention compliance

---

### 🔵 GET `/api/v1/analytics/retention/stats`

**Summary**: Get Retention Stats

**Description**: Get analytics data retention statistics.

Returns current storage metrics and events older than retention period.

CTO Condition #3: Monitor retention compliance

---

### 🔵 GET `/api/v1/analytics/sessions/active`

**Summary**: Get Active Session

**Description**: Get the current active session for the authenticated user.

---

### 🔵 GET `/api/v1/analytics/sessions/active`

**Summary**: Get Active Session

**Description**: Get the current active session for the authenticated user.

---

### 🟢 POST `/api/v1/analytics/sessions/start`

**Summary**: Start Session

**Description**: Start a new user session.

Automatically captures user agent and IP address from request.
Returns session token for subsequent event tracking.

---

### 🟢 POST `/api/v1/analytics/sessions/start`

**Summary**: Start Session

**Description**: Start a new user session.

Automatically captures user agent and IP address from request.
Returns session token for subsequent event tracking.

---

### 🟢 POST `/api/v1/analytics/sessions/{session_id}/end`

**Summary**: End Session

**Description**: End a user session.

Calculates total session duration and marks session as inactive.

---

### 🟢 POST `/api/v1/analytics/sessions/{session_id}/end`

**Summary**: End Session

**Description**: End a user session.

Calculates total session duration and marks session as inactive.

---

### 🔵 GET `/api/v1/analytics/summary`

**Summary**: Get Analytics Summary

<details>
<summary>View full description</summary>

Get comprehensive analytics summary for AGENTS.md.

Sprint 85: Combined metrics endpoint for AGENTS.md analytics dashboard.

Returns:
    Dictionary with overlay, engagement, gates, security, and agents_md metrics.

</details>

---

### 🔵 GET `/api/v1/analytics/summary`

**Summary**: Get Analytics Summary

<details>
<summary>View full description</summary>

Get comprehensive analytics summary for AGENTS.md.

Sprint 85: Combined metrics endpoint for AGENTS.md analytics dashboard.

Returns:
    Dictionary with overlay, engagement, gates, security, and agents_md metrics.

</details>

---

### 🔵 GET `/api/v1/planning/projects/{project_id}/velocity`

**Summary**: Get project velocity metrics

<details>
<summary>View full description</summary>

Get velocity metrics for a project from historical sprint data.

**Sprint 76: AI Sprint Assistant - Velocity Calculation**

Calculates:
- Average velocity (story points per sprint)
- Velocity trend (increasing/decreasing/stable)
- Confidence score based on data availability
- History of recent sprint velocities

Args:
    project_id: Project UUID
    sprint_count: Number of completed sprints to analyze (default: 5)

Returns:
    VelocityMetricsResponse with velocity metrics

Raises:
    404: Project not found or no access

</details>

---

### 🔵 GET `/api/v1/planning/sprints/{sprint_id}/analytics`

**Summary**: Get comprehensive sprint analytics

<details>
<summary>View full description</summary>

Get comprehensive analytics for a sprint.

**Sprint 76: AI Sprint Assistant - Full Analytics**

Combines velocity, health, and suggestions into a single response
with an AI-generated summary of sprint status.

Args:
    sprint_id: Sprint UUID

Returns:
    SprintAnalyticsResponse with full analytics

Raises:
    404: Sprint not found

</details>

---

### 🔵 GET `/api/v1/planning/sprints/{sprint_id}/burndown`

**Summary**: Get sprint burndown chart data

<details>
<summary>View full description</summary>

Get burndown chart data for a sprint.

**Sprint 77: Burndown Charts - Day 2 Implementation**

Generates burndown chart data including:
- Ideal burndown line (linear from total points to 0)
- Actual burndown line (based on completed items)
- Progress metrics (completion rate, days remaining)
- On-track indicator (actual vs ideal comparison)

Performance Budget:
- Query time: <50ms
- Calculation time: <20ms
- Total response: <100ms p95

Args:
    sprint_id: Sprint UUID

Returns:
    BurndownChartResponse with ideal and actual burndown data

Raises:
    404: Sprint not found
    400: Sprint has no start/end dates

</details>

---

### 🔵 GET `/api/v1/planning/sprints/{sprint_id}/forecast`

**Summary**: Get sprint completion forecast

<details>
<summary>View full description</summary>

Get sprint completion forecast with probability and risks.

**Sprint 77: Sprint Forecasting - Day 3 Implementation**

Predicts sprint completion probability based on:
- Current vs required burn rate
- Blocked items penalty (-5% each)
- Incomplete P0 items penalty (-10% each)
- Days remaining urgency factor

Returns:
- Completion probability (0-100%)
- Predicted end date
- On-track indicator
- Identified risks with severity
- AI-generated recommendations

Performance Budget:
- Query time: <50ms
- Calculation time: <30ms
- Total response: <100ms p95

Args:
    sprint_id: Sprint UUID

Returns:
    SprintForecastResponse with probability, risks, and recommendations

Raises:
    404: Sprint not found

*(truncated for brevity)*

</details>

---

### 🔵 GET `/api/v1/planning/sprints/{sprint_id}/health`

**Summary**: Get sprint health indicators

<details>
<summary>View full description</summary>

Get health indicators for a sprint.

**Sprint 76: AI Sprint Assistant - Health Assessment**

Calculates:
- Completion rate (story points done / total)
- Blocked item count
- Risk level (low/medium/high based on progress vs time)
- Days remaining in sprint
- Expected completion based on time elapsed

Args:
    sprint_id: Sprint UUID

Returns:
    SprintHealthResponse with health indicators

Raises:
    404: Sprint not found

</details>

---

### 🔵 GET `/api/v1/planning/sprints/{sprint_id}/retrospective`

**Summary**: Get auto-generated sprint retrospective

<details>
<summary>View full description</summary>

Get auto-generated sprint retrospective.

**Sprint 77: Retrospective Automation - Day 4 Implementation**

Analyzes sprint performance and generates:
- Metrics summary (completion rate, P0 status, blocked items)
- "Went well" insights (positive patterns)
- "Needs improvement" insights (areas for growth)
- Action items (concrete next steps)
- Executive summary

Insight Categories:
- delivery: Completion and delivery performance
- priority: P0/P1 focus and completion
- velocity: Velocity trends (improving/stable/declining)
- planning: Sprint planning accuracy
- scope: Scope changes and creep
- blockers: Blocked items management

Performance Budget:
- Query time: <50ms
- Analysis time: <30ms
- Total response: <100ms p95

Args:
    sprint_id: Sprint UUID

Returns:
    SprintRetrospectiveResponse with metrics, insights, and actions


*(truncated for brevity)*

</details>

---

### 🔵 GET `/api/v1/planning/sprints/{sprint_id}/suggestions`

**Summary**: Get AI prioritization suggestions

<details>
<summary>View full description</summary>

Get AI-powered prioritization suggestions for a sprint.

**Sprint 76: AI Sprint Assistant - Recommendations**

Analyzes sprint backlog and generates suggestions:
- start_p0: P0 items not yet started (critical)
- unassigned_priority: Unassigned P0/P1 items
- overloaded: Sprint capacity exceeds velocity
- blocked: Items requiring unblocking
- p2_at_risk: Low-priority items at risk
- underloaded: Capacity opportunity

Args:
    sprint_id: Sprint UUID

Returns:
    SprintSuggestionsResponse with AI suggestions

Raises:
    404: Sprint not found

</details>

---

## Analytics v2

### 🟢 POST `/api/v1/analytics/v2/events`

**Summary**: Track Event

<details>
<summary>View full description</summary>

Track a single analytics event.

Stores event in both PostgreSQL (audit trail) and Mixpanel (analytics UX).

Request Body:
    {
        "user_id": "550e8400-e29b-41d4-a716-446655440000",
        "event_name": "gate_passed",
        "properties": {
            "gate_id": "G2",
            "project_id": "proj_123",
            "duration_ms": 1250
        }
    }

Response:
    {
        "success": true,
        "event_id": "660e8400-e29b-41d4-a716-446655440000",
        "message": null
    }

Security:
    - User ID is hashed with salt before sending to Mixpanel (GDPR)
    - Original user_id stored in PostgreSQL for audit trail
    - No PII in event properties

Performance:
    - Async event tracking (non-blocking)
    - Circuit breaker prevents cascading failures

*(truncated for brevity)*

</details>

---

### 🟢 POST `/api/v1/analytics/v2/events`

**Summary**: Track Event

<details>
<summary>View full description</summary>

Track a single analytics event.

Stores event in both PostgreSQL (audit trail) and Mixpanel (analytics UX).

Request Body:
    {
        "user_id": "550e8400-e29b-41d4-a716-446655440000",
        "event_name": "gate_passed",
        "properties": {
            "gate_id": "G2",
            "project_id": "proj_123",
            "duration_ms": 1250
        }
    }

Response:
    {
        "success": true,
        "event_id": "660e8400-e29b-41d4-a716-446655440000",
        "message": null
    }

Security:
    - User ID is hashed with salt before sending to Mixpanel (GDPR)
    - Original user_id stored in PostgreSQL for audit trail
    - No PII in event properties

Performance:
    - Async event tracking (non-blocking)
    - Circuit breaker prevents cascading failures

*(truncated for brevity)*

</details>

---

### 🟢 POST `/api/v1/analytics/v2/events/batch`

**Summary**: Track Batch Events

<details>
<summary>View full description</summary>

Track multiple analytics events in batch.

Supports up to 100 events per batch for performance optimization.

Request Body:
    {
        "events": [
            {
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "event_name": "gate_passed",
                "properties": {"gate_id": "G2"}
            },
            {
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "event_name": "evidence_uploaded",
                "properties": {"file_size_kb": 1024}
            }
        ]
    }

Response:
    {
        "success_count": 98,
        "total_count": 100,
        "failed_events": [12, 45]
    }

Performance:
    - Batch processing (100 events in ~200ms vs 10s sequential)
    - Automatic retry on batch failure

*(truncated for brevity)*

</details>

---

### 🟢 POST `/api/v1/analytics/v2/events/batch`

**Summary**: Track Batch Events

<details>
<summary>View full description</summary>

Track multiple analytics events in batch.

Supports up to 100 events per batch for performance optimization.

Request Body:
    {
        "events": [
            {
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "event_name": "gate_passed",
                "properties": {"gate_id": "G2"}
            },
            {
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "event_name": "evidence_uploaded",
                "properties": {"file_size_kb": 1024}
            }
        ]
    }

Response:
    {
        "success_count": 98,
        "total_count": 100,
        "failed_events": [12, 45]
    }

Performance:
    - Batch processing (100 events in ~200ms vs 10s sequential)
    - Automatic retry on batch failure

*(truncated for brevity)*

</details>

---

### 🔵 GET `/api/v1/analytics/v2/metrics/ai-safety`

**Summary**: Get Ai Safety Metrics

<details>
<summary>View full description</summary>

Get AI Safety Layer aggregate metrics for the last N days.

Query Parameters:
    days: Number of days to query (default: 7)

Response:
    {
        "period_days": 7,
        "total_validations": 1234,
        "pass_rate": 0.87,
        "avg_duration_ms": 945.2,
        "top_tools": {
            "claude-code": 450,
            "cursor": 380,
            "copilot": 250,
            "windsurf": 100,
            "continue": 54
        },
        "violations_by_type": {
            "naming_convention": 12,
            "folder_structure": 8,
            "missing_evidence": 5
        }
    }

Metrics Explained:
    - total_validations: Number of PRs validated by AI Safety Layer
    - pass_rate: Percentage of validations that passed (0.0-1.0)
    - avg_duration_ms: Average validation duration in milliseconds
    - top_tools: AI tools usage count (top 5)

*(truncated for brevity)*

</details>

---

### 🔵 GET `/api/v1/analytics/v2/metrics/ai-safety`

**Summary**: Get Ai Safety Metrics

<details>
<summary>View full description</summary>

Get AI Safety Layer aggregate metrics for the last N days.

Query Parameters:
    days: Number of days to query (default: 7)

Response:
    {
        "period_days": 7,
        "total_validations": 1234,
        "pass_rate": 0.87,
        "avg_duration_ms": 945.2,
        "top_tools": {
            "claude-code": 450,
            "cursor": 380,
            "copilot": 250,
            "windsurf": 100,
            "continue": 54
        },
        "violations_by_type": {
            "naming_convention": 12,
            "folder_structure": 8,
            "missing_evidence": 5
        }
    }

Metrics Explained:
    - total_validations: Number of PRs validated by AI Safety Layer
    - pass_rate: Percentage of validations that passed (0.0-1.0)
    - avg_duration_ms: Average validation duration in milliseconds
    - top_tools: AI tools usage count (top 5)

*(truncated for brevity)*

</details>

---

### 🔵 GET `/api/v1/analytics/v2/metrics/dau`

**Summary**: Get Daily Active Users

<details>
<summary>View full description</summary>

Get Daily Active Users (DAU) metrics for the last N days.

Query Parameters:
    days: Number of days to query (default: 30)

Response:
    {
        "start_date": "2026-01-01",
        "end_date": "2026-01-30",
        "daily_counts": {
            "2026-01-06": 45,
            "2026-01-07": 52,
            "2026-01-08": 48
        },
        "total_unique_users": 127,
        "avg_dau": 48.3
    }

Notes:
    - DAU is calculated from user_login events
    - Unique users are counted per day
    - Average DAU is calculated across the period

</details>

---

### 🔵 GET `/api/v1/analytics/v2/metrics/dau`

**Summary**: Get Daily Active Users

<details>
<summary>View full description</summary>

Get Daily Active Users (DAU) metrics for the last N days.

Query Parameters:
    days: Number of days to query (default: 30)

Response:
    {
        "start_date": "2026-01-01",
        "end_date": "2026-01-30",
        "daily_counts": {
            "2026-01-06": 45,
            "2026-01-07": 52,
            "2026-01-08": 48
        },
        "total_unique_users": 127,
        "avg_dau": 48.3
    }

Notes:
    - DAU is calculated from user_login events
    - Unique users are counted per day
    - Average DAU is calculated across the period

</details>

---

## Authentication

### 🟢 POST `/api/v1/auth/forgot-password`

**Summary**: Forgot Password

<details>
<summary>View full description</summary>

Initiate password reset by sending reset link to email.

Request Body:
    {
        "email": "user@example.com"
    }

Response (200 OK - always, for email enumeration protection):
    {
        "message": "If an account with this email exists, you will receive a password reset link.",
        "email": "user@example.com"
    }

Flow:
    1. Look up user by email
    2. If user exists and is active:
       a. Generate secure reset token (64-byte URL-safe)
       b. Store SHA-256 hash in database (1-hour expiry)
       c. Send email with reset link
    3. Always return 200 OK (prevents email enumeration)

Security:
    - Always returns success (prevents email enumeration attacks)
    - Token is SHA-256 hashed before storage
    - Token expires in 1 hour
    - Rate limited: 3 requests/email/hour (recommended)

</details>

---

### 🟢 POST `/api/v1/auth/forgot-password`

**Summary**: Forgot Password

<details>
<summary>View full description</summary>

Initiate password reset by sending reset link to email.

Request Body:
    {
        "email": "user@example.com"
    }

Response (200 OK - always, for email enumeration protection):
    {
        "message": "If an account with this email exists, you will receive a password reset link.",
        "email": "user@example.com"
    }

Flow:
    1. Look up user by email
    2. If user exists and is active:
       a. Generate secure reset token (64-byte URL-safe)
       b. Store SHA-256 hash in database (1-hour expiry)
       c. Send email with reset link
    3. Always return 200 OK (prevents email enumeration)

Security:
    - Always returns success (prevents email enumeration attacks)
    - Token is SHA-256 hashed before storage
    - Token expires in 1 hour
    - Rate limited: 3 requests/email/hour (recommended)

</details>

---

### 🟢 POST `/api/v1/auth/github/device`

**Summary**: Github Device Flow Init

<details>
<summary>View full description</summary>

Initiate GitHub OAuth Device Flow (for CLI/Desktop apps).

This endpoint is designed for applications that cannot easily handle
browser redirects (like CLI tools, VS Code extensions, desktop apps).

Response (200 OK):
    {
        "device_code": "3584d83530557fdd1f46af8289938c8ef79f9dc5",
        "user_code": "WDJB-MJHT",
        "verification_uri": "https://github.com/login/device",
        "expires_in": 900,
        "interval": 5
    }

Errors:
    - 400 Bad Request: GitHub device flow initiation failed
    - 500 Internal Server Error: Service unavailable

Flow:
    1. Extension calls this endpoint to get device_code and user_code
    2. Extension shows user_code and verification_uri to user
    3. User visits https://github.com/login/device and enters user_code
    4. Extension polls POST /auth/github/token with device_code
    5. When user authorizes, token endpoint returns access_token
    6. Extension creates user session with access_token

Usage:
    - VS Code Extension: Show user_code in notification, open browser
    - CLI: Print user_code and verification_uri, poll for token
    - Desktop App: Show dialog with user_code, poll for token

*(truncated for brevity)*

</details>

---

### 🟢 POST `/api/v1/auth/github/device`

**Summary**: Github Device Flow Init

<details>
<summary>View full description</summary>

Initiate GitHub OAuth Device Flow (for CLI/Desktop apps).

This endpoint is designed for applications that cannot easily handle
browser redirects (like CLI tools, VS Code extensions, desktop apps).

Response (200 OK):
    {
        "device_code": "3584d83530557fdd1f46af8289938c8ef79f9dc5",
        "user_code": "WDJB-MJHT",
        "verification_uri": "https://github.com/login/device",
        "expires_in": 900,
        "interval": 5
    }

Errors:
    - 400 Bad Request: GitHub device flow initiation failed
    - 500 Internal Server Error: Service unavailable

Flow:
    1. Extension calls this endpoint to get device_code and user_code
    2. Extension shows user_code and verification_uri to user
    3. User visits https://github.com/login/device and enters user_code
    4. Extension polls POST /auth/github/token with device_code
    5. When user authorizes, token endpoint returns access_token
    6. Extension creates user session with access_token

Usage:
    - VS Code Extension: Show user_code in notification, open browser
    - CLI: Print user_code and verification_uri, poll for token
    - Desktop App: Show dialog with user_code, poll for token

*(truncated for brevity)*

</details>

---

### 🟢 POST `/api/v1/auth/github/token`

**Summary**: Github Device Flow Poll

<details>
<summary>View full description</summary>

Poll for GitHub device authorization completion.

Request Body:
    {
        "device_code": "3584d83530557fdd1f46af8289938c8ef79f9dc5"
    }

Response (200 OK - when authorized):
    {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "token_type": "bearer",
        "expires_in": 28800
    }

Response (400 Bad Request - polling states):
    {
        "detail": "error:authorization_pending"  # User hasn't authorized yet
    }
    {
        "detail": "error:slow_down"  # Polling too fast
    }
    {
        "detail": "error:expired_token"  # Device code expired
    }
    {
        "detail": "error:access_denied"  # User denied authorization
    }

Errors:

*(truncated for brevity)*

</details>

---

### 🟢 POST `/api/v1/auth/github/token`

**Summary**: Github Device Flow Poll

<details>
<summary>View full description</summary>

Poll for GitHub device authorization completion.

Request Body:
    {
        "device_code": "3584d83530557fdd1f46af8289938c8ef79f9dc5"
    }

Response (200 OK - when authorized):
    {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "token_type": "bearer",
        "expires_in": 28800
    }

Response (400 Bad Request - polling states):
    {
        "detail": "error:authorization_pending"  # User hasn't authorized yet
    }
    {
        "detail": "error:slow_down"  # Polling too fast
    }
    {
        "detail": "error:expired_token"  # Device code expired
    }
    {
        "detail": "error:access_denied"  # User denied authorization
    }

Errors:

*(truncated for brevity)*

</details>

---

### 🔵 GET `/api/v1/auth/health`

**Summary**: Auth Health Check

<details>
<summary>View full description</summary>

Authentication service health check.

Response (200 OK):
    {
        "status": "healthy",
        "service": "authentication",
        "version": "1.0.0"
    }

Usage:
    - Kubernetes liveness probe
    - Monitoring/alerting systems
    - CI/CD health validation

</details>

---

### 🔵 GET `/api/v1/auth/health`

**Summary**: Auth Health Check

<details>
<summary>View full description</summary>

Authentication service health check.

Response (200 OK):
    {
        "status": "healthy",
        "service": "authentication",
        "version": "1.0.0"
    }

Usage:
    - Kubernetes liveness probe
    - Monitoring/alerting systems
    - CI/CD health validation

</details>

---

### 🟢 POST `/api/v1/auth/login`

**Summary**: Login

<details>
<summary>View full description</summary>

Login with email and password.

Sprint 63: Sets httpOnly cookies + returns tokens in body (dual mode).

Request Body:
    {
        "email": "nguyen.van.anh@mtc.com.vn",
        "password": "SecurePassword123!"
    }

Response (200 OK):
    Body: {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "token_type": "bearer",
        "expires_in": 3600
    }
    Cookies:
        - sdlc_access_token (httpOnly, 15 min)
        - sdlc_refresh_token (httpOnly, 7 days)

Errors:
    - 401 Unauthorized: Invalid email or password
    - 403 Forbidden: User account is inactive

Flow:
    1. Validate email/password
    2. Generate access token (15 min cookie, 1 hour body for legacy)
    3. Generate refresh token (7 days cookie, 30 days body for legacy)
    4. Store refresh token in database

*(truncated for brevity)*

</details>

---

### 🟢 POST `/api/v1/auth/login`

**Summary**: Login

<details>
<summary>View full description</summary>

Login with email and password.

Sprint 63: Sets httpOnly cookies + returns tokens in body (dual mode).

Request Body:
    {
        "email": "nguyen.van.anh@mtc.com.vn",
        "password": "SecurePassword123!"
    }

Response (200 OK):
    Body: {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "token_type": "bearer",
        "expires_in": 3600
    }
    Cookies:
        - sdlc_access_token (httpOnly, 15 min)
        - sdlc_refresh_token (httpOnly, 7 days)

Errors:
    - 401 Unauthorized: Invalid email or password
    - 403 Forbidden: User account is inactive

Flow:
    1. Validate email/password
    2. Generate access token (15 min cookie, 1 hour body for legacy)
    3. Generate refresh token (7 days cookie, 30 days body for legacy)
    4. Store refresh token in database

*(truncated for brevity)*

</details>

---

### 🟢 POST `/api/v1/auth/logout`

**Summary**: Logout

<details>
<summary>View full description</summary>

Logout and revoke refresh token.

Sprint 63 Dual Mode: Accepts refresh token from cookie OR body.

Request (Option A - Cookie - Sprint 63):
    Cookie: sdlc_refresh_token=eyJ...

Request (Option B - Body - Legacy):
    {
        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    }

Response (204 No Content):
    Clear-Cookie: sdlc_access_token
    Clear-Cookie: sdlc_refresh_token
    (empty body)

Errors:
    - 401 Unauthorized: Invalid access token
    - 404 Not Found: Refresh token not found (only if body provided)

Flow:
    1. Validate access token (current_user dependency)
    2. Get refresh token from cookie OR body
    3. Find and revoke refresh token in database
    4. Clear cookies (Sprint 63)
    5. Return 204 No Content

</details>

---

### 🟢 POST `/api/v1/auth/logout`

**Summary**: Logout

<details>
<summary>View full description</summary>

Logout and revoke refresh token.

Sprint 63 Dual Mode: Accepts refresh token from cookie OR body.

Request (Option A - Cookie - Sprint 63):
    Cookie: sdlc_refresh_token=eyJ...

Request (Option B - Body - Legacy):
    {
        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    }

Response (204 No Content):
    Clear-Cookie: sdlc_access_token
    Clear-Cookie: sdlc_refresh_token
    (empty body)

Errors:
    - 401 Unauthorized: Invalid access token
    - 404 Not Found: Refresh token not found (only if body provided)

Flow:
    1. Validate access token (current_user dependency)
    2. Get refresh token from cookie OR body
    3. Find and revoke refresh token in database
    4. Clear cookies (Sprint 63)
    5. Return 204 No Content

</details>

---

### 🔵 GET `/api/v1/auth/me`

**Summary**: Get Current User Profile

<details>
<summary>View full description</summary>

Get current authenticated user profile.

Headers:
    Authorization: Bearer <access_token>

Response (200 OK):
    {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "email": "nguyen.van.anh@mtc.com.vn",
        "name": "Nguyễn Văn Anh",
        "is_active": true,
        "is_superuser": false,
        "is_platform_admin": false,
        "roles": ["Engineering Manager", "CTO"],
        "oauth_providers": ["github", "google"],
        "created_at": "2025-10-01T08:00:00Z",
        "last_login_at": "2025-11-28T10:30:00Z"
    }

Sprint 88: Platform Admin Privacy Fix
    - is_platform_admin: Platform admins manage system operations but CANNOT access customer data
    - is_superuser: DEPRECATED - legacy field, use is_platform_admin for privacy checks

Errors:
    - 401 Unauthorized: Invalid or expired access token
    - 403 Forbidden: User account is inactive

Flow:
    1. Validate access token (get_current_active_user dependency)
    2. Fetch user roles from database

*(truncated for brevity)*

</details>

---

### 🔵 GET `/api/v1/auth/me`

**Summary**: Get Current User Profile

<details>
<summary>View full description</summary>

Get current authenticated user profile.

Headers:
    Authorization: Bearer <access_token>

Response (200 OK):
    {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "email": "nguyen.van.anh@mtc.com.vn",
        "name": "Nguyễn Văn Anh",
        "is_active": true,
        "is_superuser": false,
        "is_platform_admin": false,
        "roles": ["Engineering Manager", "CTO"],
        "oauth_providers": ["github", "google"],
        "created_at": "2025-10-01T08:00:00Z",
        "last_login_at": "2025-11-28T10:30:00Z"
    }

Sprint 88: Platform Admin Privacy Fix
    - is_platform_admin: Platform admins manage system operations but CANNOT access customer data
    - is_superuser: DEPRECATED - legacy field, use is_platform_admin for privacy checks

Errors:
    - 401 Unauthorized: Invalid or expired access token
    - 403 Forbidden: User account is inactive

Flow:
    1. Validate access token (get_current_active_user dependency)
    2. Fetch user roles from database

*(truncated for brevity)*

</details>

---

### 🔵 GET `/api/v1/auth/oauth/{provider}/authorize`

**Summary**: Oauth Authorize

<details>
<summary>View full description</summary>

Get OAuth authorization URL for the specified provider.

Path Parameters:
    - provider: OAuth provider ('github' or 'google')

Query Parameters:
    - redirect_uri: Optional custom redirect URI (default: OAUTH_REDIRECT_URL)

Response (200 OK):
    {
        "authorization_url": "https://github.com/login/oauth/authorize?...",
        "state": "random-state-string"
    }

Errors:
    - 400 Bad Request: Invalid provider or provider not configured

Flow:
    1. Generate state for CSRF protection
    2. Store state in Redis (10 min TTL)
    3. Build authorization URL
    4. Return URL and state

</details>

---

### 🔵 GET `/api/v1/auth/oauth/{provider}/authorize`

**Summary**: Oauth Authorize

<details>
<summary>View full description</summary>

Get OAuth authorization URL for the specified provider.

Path Parameters:
    - provider: OAuth provider ('github' or 'google')

Query Parameters:
    - redirect_uri: Optional custom redirect URI (default: OAUTH_REDIRECT_URL)

Response (200 OK):
    {
        "authorization_url": "https://github.com/login/oauth/authorize?...",
        "state": "random-state-string"
    }

Errors:
    - 400 Bad Request: Invalid provider or provider not configured

Flow:
    1. Generate state for CSRF protection
    2. Store state in Redis (10 min TTL)
    3. Build authorization URL
    4. Return URL and state

</details>

---

### 🟢 POST `/api/v1/auth/oauth/{provider}/callback`

**Summary**: Oauth Callback

<details>
<summary>View full description</summary>

Handle OAuth callback and exchange code for tokens.

Path Parameters:
    - provider: OAuth provider ('github' or 'google')

Request Body:
    {
        "code": "authorization_code_from_provider",
        "state": "encoded_state_from_authorize"
    }

Response (200 OK):
    {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "token_type": "bearer",
        "expires_in": 3600
    }

Errors:
    - 400 Bad Request: Invalid state or provider
    - 401 Unauthorized: OAuth exchange failed
    - 500 Internal Server Error: User creation failed

Flow:
    1. Validate state parameter
    2. Exchange code for OAuth tokens
    3. Get user info from provider
    4. Find or create user
    5. Link OAuth account

*(truncated for brevity)*

</details>

---

### 🟢 POST `/api/v1/auth/oauth/{provider}/callback`

**Summary**: Oauth Callback

<details>
<summary>View full description</summary>

Handle OAuth callback and exchange code for tokens.

Path Parameters:
    - provider: OAuth provider ('github' or 'google')

Request Body:
    {
        "code": "authorization_code_from_provider",
        "state": "encoded_state_from_authorize"
    }

Response (200 OK):
    {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "token_type": "bearer",
        "expires_in": 3600
    }

Errors:
    - 400 Bad Request: Invalid state or provider
    - 401 Unauthorized: OAuth exchange failed
    - 500 Internal Server Error: User creation failed

Flow:
    1. Validate state parameter
    2. Exchange code for OAuth tokens
    3. Get user info from provider
    4. Find or create user
    5. Link OAuth account

*(truncated for brevity)*

</details>

---

### 🟢 POST `/api/v1/auth/refresh`

**Summary**: Refresh Access Token

<details>
<summary>View full description</summary>

Refresh access token using refresh token.

Sprint 63 Dual Mode: Accepts refresh token from cookie OR body.

Request (Option A - Cookie - Sprint 63 preferred):
    Cookie: sdlc_refresh_token=eyJ...

Request (Option B - Body - Legacy):
    {
        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    }

Response (200 OK):
    Body: {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "token_type": "bearer",
        "expires_in": 3600
    }
    Cookie: sdlc_access_token (new token)

Errors:
    - 401 Unauthorized: Invalid or expired refresh token
    - 401 Unauthorized: Refresh token revoked

Flow:
    1. Get refresh token from cookie OR body (priority: cookie)
    2. Decode and validate refresh token
    3. Check token type is "refresh"
    4. Verify token exists in database (not revoked)

*(truncated for brevity)*

</details>

---

### 🟢 POST `/api/v1/auth/refresh`

**Summary**: Refresh Access Token

<details>
<summary>View full description</summary>

Refresh access token using refresh token.

Sprint 63 Dual Mode: Accepts refresh token from cookie OR body.

Request (Option A - Cookie - Sprint 63 preferred):
    Cookie: sdlc_refresh_token=eyJ...

Request (Option B - Body - Legacy):
    {
        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    }

Response (200 OK):
    Body: {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "token_type": "bearer",
        "expires_in": 3600
    }
    Cookie: sdlc_access_token (new token)

Errors:
    - 401 Unauthorized: Invalid or expired refresh token
    - 401 Unauthorized: Refresh token revoked

Flow:
    1. Get refresh token from cookie OR body (priority: cookie)
    2. Decode and validate refresh token
    3. Check token type is "refresh"
    4. Verify token exists in database (not revoked)

*(truncated for brevity)*

</details>

---

### 🟢 POST `/api/v1/auth/register`

**Summary**: Register

<details>
<summary>View full description</summary>

Register a new user with email and password.

Request Body:
    {
        "email": "user@example.com",
        "password": "SecurePassword123!",
        "full_name": "Nguyễn Văn A"
    }

Response (201 Created):
    {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "email": "user@example.com",
        "name": "Nguyễn Văn A",
        "is_active": true,
        "created_at": "2025-12-27T10:30:00Z",
        "message": "Registration successful. You can now login."
    }

Errors:
    - 400 Bad Request: Email already registered
    - 422 Unprocessable Entity: Invalid email format or password too short

Flow:
    1. Validate email uniqueness
    2. Hash password with bcrypt (cost=12)
    3. Create user record
    4. Return user info with success message

Security:

*(truncated for brevity)*

</details>

---

### 🟢 POST `/api/v1/auth/register`

**Summary**: Register

<details>
<summary>View full description</summary>

Register a new user with email and password.

Request Body:
    {
        "email": "user@example.com",
        "password": "SecurePassword123!",
        "full_name": "Nguyễn Văn A"
    }

Response (201 Created):
    {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "email": "user@example.com",
        "name": "Nguyễn Văn A",
        "is_active": true,
        "created_at": "2025-12-27T10:30:00Z",
        "message": "Registration successful. You can now login."
    }

Errors:
    - 400 Bad Request: Email already registered
    - 422 Unprocessable Entity: Invalid email format or password too short

Flow:
    1. Validate email uniqueness
    2. Hash password with bcrypt (cost=12)
    3. Create user record
    4. Return user info with success message

Security:

*(truncated for brevity)*

</details>

---

### 🟢 POST `/api/v1/auth/reset-password`

**Summary**: Reset Password

<details>
<summary>View full description</summary>

Reset password using valid token.

Request Body:
    {
        "token": "abc123...",
        "new_password": "NewSecurePassword123!"
    }

Response (200 OK):
    {
        "message": "Password has been reset successfully. You can now login with your new password.",
        "email": "user@example.com"
    }

Errors:
    - 400 Bad Request: Invalid, expired, or already used token
    - 422 Unprocessable Entity: Password too short

Flow:
    1. Validate reset token
    2. Check token is not expired or used
    3. Update user password (bcrypt hash)
    4. Mark token as used
    5. Revoke all existing sessions (refresh tokens)
    6. Return success message

Security:
    - Token marked as used immediately after password reset
    - All existing sessions revoked (security best practice)
    - Password hashed with bcrypt (cost=12)

</details>

---

### 🟢 POST `/api/v1/auth/reset-password`

**Summary**: Reset Password

<details>
<summary>View full description</summary>

Reset password using valid token.

Request Body:
    {
        "token": "abc123...",
        "new_password": "NewSecurePassword123!"
    }

Response (200 OK):
    {
        "message": "Password has been reset successfully. You can now login with your new password.",
        "email": "user@example.com"
    }

Errors:
    - 400 Bad Request: Invalid, expired, or already used token
    - 422 Unprocessable Entity: Password too short

Flow:
    1. Validate reset token
    2. Check token is not expired or used
    3. Update user password (bcrypt hash)
    4. Mark token as used
    5. Revoke all existing sessions (refresh tokens)
    6. Return success message

Security:
    - Token marked as used immediately after password reset
    - All existing sessions revoked (security best practice)
    - Password hashed with bcrypt (cost=12)

</details>

---

### 🔵 GET `/api/v1/auth/verify-reset-token`

**Summary**: Verify Reset Token

<details>
<summary>View full description</summary>

Verify password reset token validity.

Query Parameters:
    token: Password reset token from email link

Response (200 OK - valid token):
    {
        "valid": true,
        "email": "user@example.com",
        "expires_at": "2025-12-29T15:00:00Z"
    }

Response (200 OK - invalid/expired token):
    {
        "valid": false,
        "email": null,
        "expires_at": null,
        "error": "Token has expired"
    }

Usage:
    Frontend calls this when user clicks reset link to check if token is valid
    before showing the password reset form.

</details>

---

### 🔵 GET `/api/v1/auth/verify-reset-token`

**Summary**: Verify Reset Token

<details>
<summary>View full description</summary>

Verify password reset token validity.

Query Parameters:
    token: Password reset token from email link

Response (200 OK - valid token):
    {
        "valid": true,
        "email": "user@example.com",
        "expires_at": "2025-12-29T15:00:00Z"
    }

Response (200 OK - invalid/expired token):
    {
        "valid": false,
        "email": null,
        "expires_at": null,
        "error": "Token has expired"
    }

Usage:
    Frontend calls this when user clicks reset link to check if token is valid
    before showing the password reset form.

</details>

---

## Auto-Generation

### 🟢 POST `/api/v1/auto-generate/all`

**Summary**: Generate All Compliance Artifacts

<details>
<summary>View full description</summary>

Generate all applicable compliance artifacts for a PR.

Generates:
- Context attachment (always)
- Intent document (if task provided)
- Ownership suggestions (for changed files)
- Attestation template (if AI session provided)

Combined time saved: ~30 minutes per PR

</details>

---

### 🟢 POST `/api/v1/auto-generate/all`

**Summary**: Generate All Compliance Artifacts

<details>
<summary>View full description</summary>

Generate all applicable compliance artifacts for a PR.

Generates:
- Context attachment (always)
- Intent document (if task provided)
- Ownership suggestions (for changed files)
- Attestation template (if AI session provided)

Combined time saved: ~30 minutes per PR

</details>

---

### 🟢 POST `/api/v1/auto-generate/attestation`

**Summary**: Generate AI Attestation

<details>
<summary>View full description</summary>

Generate attestation template for AI-generated code.

Auto-fills 80%:
- AI provider, model, session ID
- Prompt hash, generated lines, timestamp

Developer confirms 20%:
- Review time (minimum 2 sec/line)
- Modifications made
- Understanding confirmation

Time saved: ~8 minutes per AI session

</details>

---

### 🟢 POST `/api/v1/auto-generate/attestation`

**Summary**: Generate AI Attestation

<details>
<summary>View full description</summary>

Generate attestation template for AI-generated code.

Auto-fills 80%:
- AI provider, model, session ID
- Prompt hash, generated lines, timestamp

Developer confirms 20%:
- Review time (minimum 2 sec/line)
- Modifications made
- Understanding confirmation

Time saved: ~8 minutes per AI session

</details>

---

### 🟢 POST `/api/v1/auto-generate/context`

**Summary**: Attach Context to PR

<details>
<summary>View full description</summary>

Auto-attach ADRs, specs, and design docs to PR description.

Algorithm:
1. Extract modules from changed files
2. Find ADRs mentioning those modules
3. Find specs in related directories
4. Format context section for PR

Time saved: ~5 minutes per PR

</details>

---

### 🟢 POST `/api/v1/auto-generate/context`

**Summary**: Attach Context to PR

<details>
<summary>View full description</summary>

Auto-attach ADRs, specs, and design docs to PR description.

Algorithm:
1. Extract modules from changed files
2. Find ADRs mentioning those modules
3. Find specs in related directories
4. Format context section for PR

Time saved: ~5 minutes per PR

</details>

---

### 🔵 GET `/api/v1/auto-generate/health`

**Summary**: Auto-Generation Health Check

**Description**: Check health of auto-generation service including Ollama status.

---

### 🔵 GET `/api/v1/auto-generate/health`

**Summary**: Auto-Generation Health Check

**Description**: Check health of auto-generation service including Ollama status.

---

### 🟢 POST `/api/v1/auto-generate/intent`

**Summary**: Generate Intent Document

<details>
<summary>View full description</summary>

Generate an intent document from task description.

Uses 3-level fallback:
1. LLM (Ollama qwen3:32b) - Best quality (~10s)
2. Template - Deterministic (~1s)
3. Minimal - Basic structure (~0.5s)

Time saved: ~15 minutes per task

</details>

---

### 🟢 POST `/api/v1/auto-generate/intent`

**Summary**: Generate Intent Document

<details>
<summary>View full description</summary>

Generate an intent document from task description.

Uses 3-level fallback:
1. LLM (Ollama qwen3:32b) - Best quality (~10s)
2. Template - Deterministic (~1s)
3. Minimal - Basic structure (~0.5s)

Time saved: ~15 minutes per task

</details>

---

### 🟢 POST `/api/v1/auto-generate/ownership`

**Summary**: Suggest File Ownership

<details>
<summary>View full description</summary>

Suggest ownership for a file based on multiple sources.

Algorithm (priority order):
1. CODEOWNERS file (confidence: 1.0)
2. Directory patterns (confidence: 0.9)
3. Git blame (confidence: 0.7)
4. Task creator (confidence: 0.5)
5. Extension fallback (confidence: 0.3)

Time saved: ~2 minutes per file

</details>

---

### 🟢 POST `/api/v1/auto-generate/ownership`

**Summary**: Suggest File Ownership

<details>
<summary>View full description</summary>

Suggest ownership for a file based on multiple sources.

Algorithm (priority order):
1. CODEOWNERS file (confidence: 1.0)
2. Directory patterns (confidence: 0.9)
3. Git blame (confidence: 0.7)
4. Task creator (confidence: 0.5)
5. Extension fallback (confidence: 0.3)

Time saved: ~2 minutes per file

</details>

---

## CEO Dashboard

### 🟢 POST `/api/v1/ceo-dashboard/decisions/{submission_id}/override`

**Summary**: Record CEO override for calibration

<details>
<summary>View full description</summary>

Record a CEO override for signal calibration.

    **Override Types:**
    - agrees: CEO confirms the routing was correct
    - disagrees: CEO disagrees with the routing (false positive/negative)

    **Calibration Impact:**
    - Tracks false positive rate
    - Generates weight adjustment recommendations
    - Feeds into weekly calibration session

    **Recommendation:**
    - If disagrees rate >10% → Trigger calibration session
    - If specific signal consistently wrong → Adjust weight

</details>

---

### 🟢 POST `/api/v1/ceo-dashboard/decisions/{submission_id}/resolve`

**Summary**: Resolve pending CEO decision

<details>
<summary>View full description</summary>

Resolve a pending CEO decision.

    **Actions:**
    - Removes from pending queue
    - Updates submission status
    - Records for metrics

    **Decisions:**
    - approved: Approve the PR
    - rejected: Reject the PR

</details>

---

### 🔵 GET `/api/v1/ceo-dashboard/health`

**Summary**: CEO Dashboard health check


---

### 🔵 GET `/api/v1/ceo-dashboard/overrides`

**Summary**: Get CEO overrides this week

<details>
<summary>View full description</summary>

Get CEO override records for calibration.

    **Override types:**
    - agrees: CEO confirms routing was correct
    - disagrees: CEO disagrees (false positive/negative)

    **Used for:**
    - Tracking false positive rate
    - Signal weight calibration
    - Identifying systematic biases

    **Recommendation:** If disagrees rate >10%, schedule calibration session.

</details>

---

### 🔵 GET `/api/v1/ceo-dashboard/pending-decisions`

**Summary**: Get pending CEO decisions queue

<details>
<summary>View full description</summary>

Get queue of pending CEO decisions (Orange and Red PRs).

    **Queue Priority:**
    1. Red PRs (index >80) - CEO must review
    2. Orange PRs (index 61-80) - CEO should review

    **Sorted by:** Vibecoding Index (descending), then waiting time

    Returns top 10 for dashboard. Use pagination for full queue.

</details>

---

### 🔵 GET `/api/v1/ceo-dashboard/routing-breakdown`

**Summary**: Get PR routing breakdown

<details>
<summary>View full description</summary>

Get PR routing breakdown by vibecoding index category.

    **Categories:**
    - **Green (0-30)**: Auto-approve (no CEO time needed)
    - **Yellow (31-60)**: Tech Lead review (no CEO time needed)
    - **Orange (61-80)**: CEO should review (~10 min each)
    - **Red (81-100)**: CEO must review (~30 min each)

    **Target:** Auto-approval rate >85% by Week 8

</details>

---

### 🟢 POST `/api/v1/ceo-dashboard/submissions`

**Summary**: Record governance submission

<details>
<summary>View full description</summary>

Record a governance submission for dashboard metrics.

    Called by governance validation endpoints to feed metrics.

    **Routing Categories:**
    - auto_approve: Green (index 0-30)
    - tech_lead_review: Yellow (index 31-60)
    - ceo_should_review: Orange (index 61-80)
    - ceo_must_review: Red (index 81-100)

</details>

---

### 🔵 GET `/api/v1/ceo-dashboard/summary`

**Summary**: Get complete CEO dashboard summary

<details>
<summary>View full description</summary>

Get complete CEO dashboard summary with all metrics.

    **Includes:**
    - Executive Summary (time saved, routing breakdown, pending count)
    - Weekly Summary (compliance rate, vibecoding avg, false positive rate)
    - Trends (time saved 8 weeks, vibecoding index 7 days)
    - Top Issues (rejection reasons, CEO overrides)
    - System Health (uptime, latency, kill switch status)
    - Pending Decisions queue (Orange/Red PRs)

    **Time Ranges:**
    - today: Today only
    - this_week: Current week (Monday-Sunday)
    - last_7_days: Rolling 7 days
    - last_30_days: Rolling 30 days

    **Target Metrics (per CEO-WORKFLOW-CONTRACT.md):**
    - Time Saved: 40h → 10h by Week 8
    - Auto-Approval Rate: 85% by Week 8
    - Vibecoding Index: <30 average
    - False Positive Rate: <10%

</details>

---

### 🔵 GET `/api/v1/ceo-dashboard/system-health`

**Summary**: Get system health snapshot

<details>
<summary>View full description</summary>

Get system health snapshot for CEO quick glance.

    **Metrics:**
    - uptime_percent: System uptime (SLO: >99%)
    - api_latency_p95_ms: API latency P95 (SLO: <100ms)
    - kill_switch_status: Current mode (OFF/WARNING/SOFT/FULL)
    - overall_status: excellent/good/warning/critical
    - alerts_active: Number of active alerts
    - last_incident: Timestamp of last incident

    **Kill Switch Status:**
    - OFF: No enforcement (dev mode)
    - WARNING: Log violations only
    - SOFT: Block critical, warn others
    - FULL: Block all violations

</details>

---

### 🔵 GET `/api/v1/ceo-dashboard/time-saved`

**Summary**: Get CEO time saved metrics

<details>
<summary>View full description</summary>

Get CEO time saved metrics vs baseline.

    **Calculation:**
    - Baseline: 40 hours/week (manual governance)
    - Actual: (ceo_should_review × 10min) + (ceo_must_review × 30min)
    - Time Saved: Baseline - Actual

    **Targets (per MONITORING-PLAN.md):**
    - Week 2: 30 hours (-25%)
    - Week 4: 20 hours (-50%)
    - Week 8: 10 hours (-75%)

</details>

---

### 🔵 GET `/api/v1/ceo-dashboard/top-rejections`

**Summary**: Get top rejection reasons

<details>
<summary>View full description</summary>

Get top 5 rejection reasons with actionable fixes.

    **Each reason includes:**
    - reason: Rejection reason code
    - count: Number of rejections
    - percentage: Percentage of total rejections
    - trend: Trend direction (up/down/stable)
    - actionable_fix: CLI command or steps to fix

    **Common reasons:**
    - missing_ownership: No @owner annotation
    - missing_intent: No intent statement
    - orphan_code: No linked ADR
    - stage_violation: PR doesn't match current stage

</details>

---

### 🔵 GET `/api/v1/ceo-dashboard/trends/time-saved`

**Summary**: Get time saved trend (8 weeks)

<details>
<summary>View full description</summary>

Get time saved trend data for last 8 weeks.

    **Data points:**
    - week: ISO week number
    - week_start: Week start date
    - time_saved_hours: Hours saved that week
    - baseline_hours: Baseline (40h)
    - target_hours: Target for that week

    Used for CEO Dashboard line chart.

</details>

---

### 🔵 GET `/api/v1/ceo-dashboard/trends/vibecoding-index`

**Summary**: Get vibecoding index trend (7 days)

<details>
<summary>View full description</summary>

Get vibecoding index distribution for last 7 days.

    **Data points:**
    - date: Date string
    - day_name: Day of week
    - average_index: Average vibecoding index
    - count: Number of submissions
    - distribution: Count by index bucket (0-10, 11-20, etc.)

    Used for CEO Dashboard heatmap.

</details>

---

### 🔵 GET `/api/v1/ceo-dashboard/weekly-summary`

**Summary**: Get weekly governance summary

<details>
<summary>View full description</summary>

Get governance summary for current week.

    **Metrics:**
    - Compliance pass rate (first submission success)
    - Vibecoding index average
    - False positive rate (CEO disagrees / total escalations)
    - Developer satisfaction NPS
    - Time saved hours
    - Total submissions and rejections
    - CEO overrides count

    **Health Status:**
    - Excellent: pass_rate ≥70%, index ≤30, false_positive ≤10%
    - Good: pass_rate ≥50%, index ≤60, false_positive ≤15%
    - Warning: pass_rate ≥30% OR index ≤80
    - Critical: Otherwise

</details>

---

## CRP - Consultations

### 🟢 POST `/api/v1/consultations`

**Summary**: Create consultation request

**Description**: Create a new consultation request for high-risk changes.

---

### 🟢 POST `/api/v1/consultations`

**Summary**: Create consultation request

**Description**: Create a new consultation request for high-risk changes.

---

### 🔵 GET `/api/v1/consultations`

**Summary**: List consultations


---

### 🔵 GET `/api/v1/consultations`

**Summary**: List consultations


---

### 🔵 GET `/api/v1/consultations/my-reviews`

**Summary**: Get my pending reviews

**Description**: Get consultations assigned to the current user for review.

---

### 🔵 GET `/api/v1/consultations/my-reviews`

**Summary**: Get my pending reviews

**Description**: Get consultations assigned to the current user for review.

---

### 🔵 GET `/api/v1/consultations/{consultation_id}`

**Summary**: Get consultation


---

### 🔵 GET `/api/v1/consultations/{consultation_id}`

**Summary**: Get consultation


---

### 🟢 POST `/api/v1/consultations/{consultation_id}/assign`

**Summary**: Assign reviewer


---

### 🟢 POST `/api/v1/consultations/{consultation_id}/assign`

**Summary**: Assign reviewer


---

### 🟢 POST `/api/v1/consultations/{consultation_id}/comments`

**Summary**: Add comment


---

### 🟢 POST `/api/v1/consultations/{consultation_id}/comments`

**Summary**: Add comment


---

### 🟢 POST `/api/v1/consultations/{consultation_id}/resolve`

**Summary**: Resolve consultation


---

### 🟢 POST `/api/v1/consultations/{consultation_id}/resolve`

**Summary**: Resolve consultation


---

## Check Runs

### 🔵 GET `/api/v1/check-runs`

**Summary**: List Check Runs

<details>
<summary>View full description</summary>

List GitHub Check Runs with filtering and pagination.

Frontend: /app/check-runs dashboard page
Sprint 86: GitHub Check Run UI (P0 Blocker)

Returns:
    CheckRunsResponse: Paginated list of check runs

</details>

---

### 🔵 GET `/api/v1/check-runs/health/status`

**Summary**: Health Check

**Description**: Check runs API health check.

Returns:
    dict: Health status

---

### 🔵 GET `/api/v1/check-runs/stats`

**Summary**: Get Check Run Stats

<details>
<summary>View full description</summary>

Get GitHub Check Run statistics.

Frontend: /app/check-runs stats cards
Sprint 86: GitHub Check Run UI (P0 Blocker)

Args:
    project_id: Optional project UUID filter
    period_days: Number of days to include in stats

Returns:
    CheckRunStats: Aggregate statistics for check runs

</details>

---

### 🔵 GET `/api/v1/check-runs/{check_run_id}`

**Summary**: Get Check Run

<details>
<summary>View full description</summary>

Get single Check Run detail.

Frontend: /app/check-runs/[id] detail page
Sprint 86: GitHub Check Run UI (P0 Blocker)

Args:
    check_run_id: Check Run UUID

Returns:
    dict: Check run detail with gate results

</details>

---

### 🟢 POST `/api/v1/check-runs/{check_run_id}/rerun`

**Summary**: Rerun Check Run

<details>
<summary>View full description</summary>

Re-run a GitHub Check Run.

Frontend: Re-run button on check runs list
Sprint 86: GitHub Check Run UI (P0 Blocker)

Args:
    check_run_id: Check Run UUID
    force: Force re-run even if already running

Returns:
    dict: New check run result

</details>

---

## Codegen

### 🟢 POST `/api/v1/codegen/estimate`

**Summary**: Estimate Cost

<details>
<summary>View full description</summary>

Estimate generation cost across providers.

Returns cost estimates for all available providers to help
with budget management and provider selection.

Args:
    request: GenerateRequest with app_blueprint

Returns:
    EstimateResponse with per-provider cost estimates

</details>

---

### 🟢 POST `/api/v1/codegen/estimate`

**Summary**: Estimate Cost

<details>
<summary>View full description</summary>

Estimate generation cost across providers.

Returns cost estimates for all available providers to help
with budget management and provider selection.

Args:
    request: GenerateRequest with app_blueprint

Returns:
    EstimateResponse with per-provider cost estimates

</details>

---

### 🟢 POST `/api/v1/codegen/generate`

**Summary**: Generate Code

<details>
<summary>View full description</summary>

Generate code from IR specification.

Takes an app blueprint (IR) and generates production-ready code
using the available AI provider (Ollama by default).

Args:
    request: GenerateRequest with app_blueprint and options

Returns:
    GenerateResponse with generated files and metadata

Raises:
    503: No providers available
    500: Generation failed

</details>

---

### 🟢 POST `/api/v1/codegen/generate`

**Summary**: Generate Code

<details>
<summary>View full description</summary>

Generate code from IR specification.

Takes an app blueprint (IR) and generates production-ready code
using the available AI provider (Ollama by default).

Args:
    request: GenerateRequest with app_blueprint and options

Returns:
    GenerateResponse with generated files and metadata

Raises:
    503: No providers available
    500: Generation failed

</details>

---

### 🟢 POST `/api/v1/codegen/generate/full`

**Summary**: Generate With Quality

<details>
<summary>View full description</summary>

Generate code with full 4-Gate Quality Pipeline.

This endpoint:
1. Creates session in Redis for tracking
2. Generates code using AI provider (Ollama/Claude)
3. Runs 4-Gate Quality Pipeline (Syntax, Security, Context, Tests)
4. Saves completed session to Redis
5. Returns detailed quality report

Sprint 49: EP-06 Full Code Generation with Quality
Sprint 69: Session persistence for history tracking

Args:
    request: GenerateRequest with app_blueprint

Returns:
    GenerateWithQualityResponse with files and quality report

Raises:
    503: No providers available
    500: Generation failed

</details>

---

### 🟢 POST `/api/v1/codegen/generate/full`

**Summary**: Generate With Quality

<details>
<summary>View full description</summary>

Generate code with full 4-Gate Quality Pipeline.

This endpoint:
1. Creates session in Redis for tracking
2. Generates code using AI provider (Ollama/Claude)
3. Runs 4-Gate Quality Pipeline (Syntax, Security, Context, Tests)
4. Saves completed session to Redis
5. Returns detailed quality report

Sprint 49: EP-06 Full Code Generation with Quality
Sprint 69: Session persistence for history tracking

Args:
    request: GenerateRequest with app_blueprint

Returns:
    GenerateWithQualityResponse with files and quality report

Raises:
    503: No providers available
    500: Generation failed

</details>

---

### 🟢 POST `/api/v1/codegen/generate/resume/{session_id}`

**Summary**: Resume Generation

<details>
<summary>View full description</summary>

Resume code generation from last checkpoint.

Sprint 51B: Session Checkpoint Feature

This endpoint resumes a previously interrupted generation session.
It first sends all completed files from the checkpoint, then continues
generating remaining files.

Args:
    session_id: UUID of the session to resume

Returns:
    StreamingResponse with SSE events (text/event-stream)

Raises:
    404: Session not found or expired
    400: Session cannot be resumed (completed or non-recoverable error)
    403: User not authorized for this session

Example events:
    data: {"type": "session_resumed", "session_id": "abc123", "resumed_from_checkpoint": 2, "files_already_completed": 6, "files_remaining": 9, "completed_files": [...]}

    data: {"type": "file_generated", ...}

    data: {"type": "completed", ...}

</details>

---

### 🟢 POST `/api/v1/codegen/generate/resume/{session_id}`

**Summary**: Resume Generation

<details>
<summary>View full description</summary>

Resume code generation from last checkpoint.

Sprint 51B: Session Checkpoint Feature

This endpoint resumes a previously interrupted generation session.
It first sends all completed files from the checkpoint, then continues
generating remaining files.

Args:
    session_id: UUID of the session to resume

Returns:
    StreamingResponse with SSE events (text/event-stream)

Raises:
    404: Session not found or expired
    400: Session cannot be resumed (completed or non-recoverable error)
    403: User not authorized for this session

Example events:
    data: {"type": "session_resumed", "session_id": "abc123", "resumed_from_checkpoint": 2, "files_already_completed": 6, "files_remaining": 9, "completed_files": [...]}

    data: {"type": "file_generated", ...}

    data: {"type": "completed", ...}

</details>

---

### 🟢 POST `/api/v1/codegen/generate/stream`

**Summary**: Generate Stream

<details>
<summary>View full description</summary>

Stream code generation with real-time file events via SSE.

Sprint 51A: Progressive Code Generation Flow

This endpoint streams events as files are generated:
- started: Generation session initiated with provider info
- file_generating: File generation started
- file_generated: File completed with content and syntax check
- quality_started: Quality pipeline initiated
- quality_gate: Individual gate results
- completed: All files generated successfully
- error: Generation failed (includes recovery_id if partial)

Frontend can display files as they appear, providing better UX
than waiting for all files to complete.

Args:
    request: GenerateRequest with app_blueprint

Returns:
    StreamingResponse with SSE events (text/event-stream)

Example events:
    data: {"type": "started", "session_id": "abc123", "model": "qwen2.5-coder:32b", "provider": "ollama"}

    data: {"type": "file_generating", "session_id": "abc123", "path": "app/main.py"}

    data: {"type": "file_generated", "session_id": "abc123", "path": "app/main.py", "content": "...", "lines": 45, "language": "python", "syntax_valid": true}

    data: {"type": "completed", "session_id": "abc123", "total_files": 12, "total_lines": 450, "duration_ms": 30000, "success": true}

</details>

---

### 🟢 POST `/api/v1/codegen/generate/stream`

**Summary**: Generate Stream

<details>
<summary>View full description</summary>

Stream code generation with real-time file events via SSE.

Sprint 51A: Progressive Code Generation Flow

This endpoint streams events as files are generated:
- started: Generation session initiated with provider info
- file_generating: File generation started
- file_generated: File completed with content and syntax check
- quality_started: Quality pipeline initiated
- quality_gate: Individual gate results
- completed: All files generated successfully
- error: Generation failed (includes recovery_id if partial)

Frontend can display files as they appear, providing better UX
than waiting for all files to complete.

Args:
    request: GenerateRequest with app_blueprint

Returns:
    StreamingResponse with SSE events (text/event-stream)

Example events:
    data: {"type": "started", "session_id": "abc123", "model": "qwen2.5-coder:32b", "provider": "ollama"}

    data: {"type": "file_generating", "session_id": "abc123", "path": "app/main.py"}

    data: {"type": "file_generated", "session_id": "abc123", "path": "app/main.py", "content": "...", "lines": 45, "language": "python", "syntax_valid": true}

    data: {"type": "completed", "session_id": "abc123", "total_files": 12, "total_lines": 450, "duration_ms": 30000, "success": true}

</details>

---

### 🟢 POST `/api/v1/codegen/generate/zip`

**Summary**: Generate Zip

<details>
<summary>View full description</summary>

Generate code and return as downloadable ZIP file.

Creates a proper folder structure for immediate use.

Sprint 49: EP-06 ZIP Export

Args:
    request: GenerateRequest with app_blueprint

Returns:
    StreamingResponse with ZIP file

</details>

---

### 🟢 POST `/api/v1/codegen/generate/zip`

**Summary**: Generate Zip

<details>
<summary>View full description</summary>

Generate code and return as downloadable ZIP file.

Creates a proper folder structure for immediate use.

Sprint 49: EP-06 ZIP Export

Args:
    request: GenerateRequest with app_blueprint

Returns:
    StreamingResponse with ZIP file

</details>

---

### 🔵 GET `/api/v1/codegen/health`

**Summary**: Health Check

<details>
<summary>View full description</summary>

Provider health check.

Returns health status for all providers without requiring
authentication (useful for monitoring).

Returns:
    HealthResponse with provider status

</details>

---

### 🔵 GET `/api/v1/codegen/health`

**Summary**: Health Check

<details>
<summary>View full description</summary>

Provider health check.

Returns health status for all providers without requiring
authentication (useful for monitoring).

Returns:
    HealthResponse with provider status

</details>

---

### 🟢 POST `/api/v1/codegen/ir/generate`

**Summary**: Ir Generate

<details>
<summary>View full description</summary>

Generate backend scaffold from AppBlueprint using IR Processor.

This endpoint uses deterministic Jinja2 templates (no AI) for fast,
predictable code generation. Suitable for standard CRUD applications.

Sprint 46: EP-06 IR-Based Backend Scaffold Generation
ADR-023: IR-Based Deterministic Code Generation

Args:
    request: IRGenerateRequest with blueprint specification

Returns:
    IRGenerateResponse with generated files

Raises:
    400: Invalid blueprint
    500: Generation failed

</details>

---

### 🟢 POST `/api/v1/codegen/ir/generate`

**Summary**: Ir Generate

<details>
<summary>View full description</summary>

Generate backend scaffold from AppBlueprint using IR Processor.

This endpoint uses deterministic Jinja2 templates (no AI) for fast,
predictable code generation. Suitable for standard CRUD applications.

Sprint 46: EP-06 IR-Based Backend Scaffold Generation
ADR-023: IR-Based Deterministic Code Generation

Args:
    request: IRGenerateRequest with blueprint specification

Returns:
    IRGenerateResponse with generated files

Raises:
    400: Invalid blueprint
    500: Generation failed

</details>

---

### 🟢 POST `/api/v1/codegen/ir/validate`

**Summary**: Ir Validate

<details>
<summary>View full description</summary>

Validate AppBlueprint without generating code.

Returns validation results and normalized blueprint if valid.

Args:
    request: IRGenerateRequest with blueprint to validate

Returns:
    IRValidateResponse with validation results

</details>

---

### 🟢 POST `/api/v1/codegen/ir/validate`

**Summary**: Ir Validate

<details>
<summary>View full description</summary>

Validate AppBlueprint without generating code.

Returns validation results and normalized blueprint if valid.

Args:
    request: IRGenerateRequest with blueprint to validate

Returns:
    IRValidateResponse with validation results

</details>

---

### 🔵 GET `/api/v1/codegen/onboarding/options/domains`

**Summary**: Get Domain Options

**Description**: Get available domain options (restaurant, hotel, retail).

---

### 🔵 GET `/api/v1/codegen/onboarding/options/domains`

**Summary**: Get Domain Options

**Description**: Get available domain options (restaurant, hotel, retail).

---

### 🔵 GET `/api/v1/codegen/onboarding/options/features/{domain}`

**Summary**: Get Feature Options


---

### 🔵 GET `/api/v1/codegen/onboarding/options/features/{domain}`

**Summary**: Get Feature Options


---

### 🔵 GET `/api/v1/codegen/onboarding/options/scales`

**Summary**: Get Scale Options


---

### 🔵 GET `/api/v1/codegen/onboarding/options/scales`

**Summary**: Get Scale Options


---

### 🟢 POST `/api/v1/codegen/onboarding/start`

**Summary**: Start Onboarding

**Description**: Start new onboarding session for Vietnamese SME founder.

Sprint 47: Vietnamese Domain Templates + Onboarding IR (EP-06)

Returns session ID and initial state for guided wizard.

---

### 🟢 POST `/api/v1/codegen/onboarding/start`

**Summary**: Start Onboarding

**Description**: Start new onboarding session for Vietnamese SME founder.

Sprint 47: Vietnamese Domain Templates + Onboarding IR (EP-06)

Returns session ID and initial state for guided wizard.

---

### 🔵 GET `/api/v1/codegen/onboarding/{session_id}`

**Summary**: Get Onboarding Session


---

### 🔵 GET `/api/v1/codegen/onboarding/{session_id}`

**Summary**: Get Onboarding Session


---

### 🟢 POST `/api/v1/codegen/onboarding/{session_id}/app_name`

**Summary**: Set Onboarding App Name


---

### 🟢 POST `/api/v1/codegen/onboarding/{session_id}/app_name`

**Summary**: Set Onboarding App Name


---

### 🟢 POST `/api/v1/codegen/onboarding/{session_id}/domain`

**Summary**: Set Onboarding Domain


---

### 🟢 POST `/api/v1/codegen/onboarding/{session_id}/domain`

**Summary**: Set Onboarding Domain


---

### 🟢 POST `/api/v1/codegen/onboarding/{session_id}/features`

**Summary**: Set Onboarding Features


---

### 🟢 POST `/api/v1/codegen/onboarding/{session_id}/features`

**Summary**: Set Onboarding Features


---

### 🟢 POST `/api/v1/codegen/onboarding/{session_id}/generate`

**Summary**: Generate Onboarding Blueprint

**Description**: Generate AppBlueprint from completed onboarding session.

Returns valid AppBlueprint IR that can be used with /ir/generate endpoint.

---

### 🟢 POST `/api/v1/codegen/onboarding/{session_id}/generate`

**Summary**: Generate Onboarding Blueprint

**Description**: Generate AppBlueprint from completed onboarding session.

Returns valid AppBlueprint IR that can be used with /ir/generate endpoint.

---

### 🟢 POST `/api/v1/codegen/onboarding/{session_id}/scale`

**Summary**: Set Onboarding Scale


---

### 🟢 POST `/api/v1/codegen/onboarding/{session_id}/scale`

**Summary**: Set Onboarding Scale


---

### 🔵 GET `/api/v1/codegen/providers`

**Summary**: List Providers

<details>
<summary>View full description</summary>

List available codegen providers.

Returns all registered providers with their availability status
and position in the fallback chain.

Returns:
    ProvidersResponse with provider list and fallback chain

</details>

---

### 🔵 GET `/api/v1/codegen/providers`

**Summary**: List Providers

<details>
<summary>View full description</summary>

List available codegen providers.

Returns all registered providers with their availability status
and position in the fallback chain.

Returns:
    ProvidersResponse with provider list and fallback chain

</details>

---

### 🔵 GET `/api/v1/codegen/sessions`

**Summary**: List Sessions

<details>
<summary>View full description</summary>

List all codegen sessions for current user.

Sprint 69: Zero Mock Policy - Real API for session history

Args:
    page: Page number (1-indexed)
    page_size: Items per page (max 100)
    status_filter: Optional status filter (completed, failed, validating)

Returns:
    Paginated list of session summaries

</details>

---

### 🔵 GET `/api/v1/codegen/sessions`

**Summary**: List Sessions

<details>
<summary>View full description</summary>

List all codegen sessions for current user.

Sprint 69: Zero Mock Policy - Real API for session history

Args:
    page: Page number (1-indexed)
    page_size: Items per page (max 100)
    status_filter: Optional status filter (completed, failed, validating)

Returns:
    Paginated list of session summaries

</details>

---

### 🔵 GET `/api/v1/codegen/sessions/active`

**Summary**: List Active Sessions

<details>
<summary>View full description</summary>

List all active (resumable) sessions for current user.

Sprint 51B: List resumable sessions

Returns:
    List of SessionStateResponse for sessions that can be resumed

Sessions with these statuses are considered resumable:
- IN_PROGRESS: Generation was interrupted
- CHECKPOINTED: Has a saved checkpoint
- FAILED: Failed with recoverable error

</details>

---

### 🔵 GET `/api/v1/codegen/sessions/active`

**Summary**: List Active Sessions

<details>
<summary>View full description</summary>

List all active (resumable) sessions for current user.

Sprint 51B: List resumable sessions

Returns:
    List of SessionStateResponse for sessions that can be resumed

Sessions with these statuses are considered resumable:
- IN_PROGRESS: Generation was interrupted
- CHECKPOINTED: Has a saved checkpoint
- FAILED: Failed with recoverable error

</details>

---

### 🔵 GET `/api/v1/codegen/sessions/{session_id}`

**Summary**: Get Session Status

<details>
<summary>View full description</summary>

Get current session status and checkpoint info.

Sprint 51B: Session status endpoint

Args:
    session_id: Session UUID

Returns:
    SessionStateResponse with current progress and checkpoint data

Raises:
    404: Session not found or expired
    403: User not authorized to view this session

</details>

---

### 🔵 GET `/api/v1/codegen/sessions/{session_id}`

**Summary**: Get Session Status

<details>
<summary>View full description</summary>

Get current session status and checkpoint info.

Sprint 51B: Session status endpoint

Args:
    session_id: Session UUID

Returns:
    SessionStateResponse with current progress and checkpoint data

Raises:
    404: Session not found or expired
    403: User not authorized to view this session

</details>

---

### 🔵 GET `/api/v1/codegen/sessions/{session_id}/quality/stream`

**Summary**: Stream Quality Pipeline

<details>
<summary>View full description</summary>

Stream quality pipeline results for a session via SSE.

Sprint 56: Backend Integration for Quality Pipeline

This endpoint streams quality gate events for an existing session:
- quality_started: Quality pipeline initiated
- quality_gate: Individual gate status/result
- quality_issue: Individual issue found
- quality_completed: All gates finished

The frontend QualityPanel component uses this endpoint for real-time
quality status updates.

Args:
    session_id: Session UUID

Returns:
    StreamingResponse with SSE events (text/event-stream)

Example events:
    data: {"type": "quality_started", "session_id": "abc123", "timestamp": "..."}
    data: {"type": "quality_gate", "session_id": "abc123", "gate_name": "Syntax", "status": "running", ...}
    data: {"type": "quality_issue", "session_id": "abc123", "gate_name": "Security", "severity": "high", ...}
    data: {"type": "quality_completed", "session_id": "abc123", "passed": true, ...}

</details>

---

### 🔵 GET `/api/v1/codegen/sessions/{session_id}/quality/stream`

**Summary**: Stream Quality Pipeline

<details>
<summary>View full description</summary>

Stream quality pipeline results for a session via SSE.

Sprint 56: Backend Integration for Quality Pipeline

This endpoint streams quality gate events for an existing session:
- quality_started: Quality pipeline initiated
- quality_gate: Individual gate status/result
- quality_issue: Individual issue found
- quality_completed: All gates finished

The frontend QualityPanel component uses this endpoint for real-time
quality status updates.

Args:
    session_id: Session UUID

Returns:
    StreamingResponse with SSE events (text/event-stream)

Example events:
    data: {"type": "quality_started", "session_id": "abc123", "timestamp": "..."}
    data: {"type": "quality_gate", "session_id": "abc123", "gate_name": "Syntax", "status": "running", ...}
    data: {"type": "quality_issue", "session_id": "abc123", "gate_name": "Security", "severity": "high", ...}
    data: {"type": "quality_completed", "session_id": "abc123", "passed": true, ...}

</details>

---

### 🔵 GET `/api/v1/codegen/templates`

**Summary**: List Templates

<details>
<summary>View full description</summary>

List available codegen templates.

Sprint 69: Zero Mock Policy - Real API for templates

Returns:
    List of available templates

</details>

---

### 🔵 GET `/api/v1/codegen/templates`

**Summary**: List Templates

<details>
<summary>View full description</summary>

List available codegen templates.

Sprint 69: Zero Mock Policy - Real API for templates

Returns:
    List of available templates

</details>

---

### 🔵 GET `/api/v1/codegen/usage/monthly`

**Summary**: Get Monthly Cost

<details>
<summary>View full description</summary>

Get monthly cost summary.

Sprint 48: Cost tracking for budget management.

Args:
    year: Year (e.g., 2025)
    month: Month (1-12)
    project_id: Optional filter by project

Returns:
    Monthly cost summary with budget status

</details>

---

### 🔵 GET `/api/v1/codegen/usage/monthly`

**Summary**: Get Monthly Cost

<details>
<summary>View full description</summary>

Get monthly cost summary.

Sprint 48: Cost tracking for budget management.

Args:
    year: Year (e.g., 2025)
    month: Month (1-12)
    project_id: Optional filter by project

Returns:
    Monthly cost summary with budget status

</details>

---

### 🔵 GET `/api/v1/codegen/usage/provider-health/{provider}`

**Summary**: Get Provider Health History

<details>
<summary>View full description</summary>

Get provider health check history.

Sprint 48: Monitor provider availability and fallback frequency.

Args:
    provider: Provider name (ollama, claude, deepcode)
    hours: Hours of history to fetch (default 24)

Returns:
    Health check history with availability percentage

</details>

---

### 🔵 GET `/api/v1/codegen/usage/provider-health/{provider}`

**Summary**: Get Provider Health History

<details>
<summary>View full description</summary>

Get provider health check history.

Sprint 48: Monitor provider availability and fallback frequency.

Args:
    provider: Provider name (ollama, claude, deepcode)
    hours: Hours of history to fetch (default 24)

Returns:
    Health check history with availability percentage

</details>

---

### 🔵 GET `/api/v1/codegen/usage/report`

**Summary**: Get Cost Report

<details>
<summary>View full description</summary>

Get comprehensive cost report for codegen usage.

Sprint 48: Quality Gates + Ollama Optimization + MVP Hardening

Target: <$50/month infrastructure cost per project (Founder Plan).

Args:
    days: Number of days to include (default 30)
    project_id: Optional filter by project

Returns:
    Cost report with totals, daily breakdown, and projections

</details>

---

### 🔵 GET `/api/v1/codegen/usage/report`

**Summary**: Get Cost Report

<details>
<summary>View full description</summary>

Get comprehensive cost report for codegen usage.

Sprint 48: Quality Gates + Ollama Optimization + MVP Hardening

Target: <$50/month infrastructure cost per project (Founder Plan).

Args:
    days: Number of days to include (default 30)
    project_id: Optional filter by project

Returns:
    Cost report with totals, daily breakdown, and projections

</details>

---

### 🟢 POST `/api/v1/codegen/validate`

**Summary**: Validate Code

<details>
<summary>View full description</summary>

Validate generated code.

Performs AI-powered validation on code to check for errors,
potential issues, and improvement suggestions.

Args:
    request: ValidateRequest with code and context

Returns:
    ValidateResponse with validation results

Raises:
    503: No providers available
    500: Validation failed

</details>

---

### 🟢 POST `/api/v1/codegen/validate`

**Summary**: Validate Code

<details>
<summary>View full description</summary>

Validate generated code.

Performs AI-powered validation on code to check for errors,
potential issues, and improvement suggestions.

Args:
    request: ValidateRequest with code and context

Returns:
    ValidateResponse with validation results

Raises:
    503: No providers available
    500: Validation failed

</details>

---

## Compliance

### 🔵 GET `/api/v1/compliance/ai/budget`

**Summary**: Get AI budget status


---

### 🔵 GET `/api/v1/compliance/ai/budget`

**Summary**: Get AI budget status


---

### 🔵 GET `/api/v1/compliance/ai/models`

**Summary**: List available Ollama models

**Description**: Get list of available models in local Ollama instance.

---

### 🔵 GET `/api/v1/compliance/ai/models`

**Summary**: List available Ollama models

**Description**: Get list of available models in local Ollama instance.

---

### 🔵 GET `/api/v1/compliance/ai/providers`

**Summary**: Get AI providers status


---

### 🔵 GET `/api/v1/compliance/ai/providers`

**Summary**: Get AI providers status


---

### 🟢 POST `/api/v1/compliance/ai/recommendations`

**Summary**: Generate AI recommendation

**Description**: Generate an AI recommendation for a compliance violation using the fallback chain.

---

### 🟢 POST `/api/v1/compliance/ai/recommendations`

**Summary**: Generate AI recommendation

**Description**: Generate an AI recommendation for a compliance violation using the fallback chain.

---

### 🔵 GET `/api/v1/compliance/jobs/{job_id}`

**Summary**: Get scan job status


---

### 🔵 GET `/api/v1/compliance/jobs/{job_id}`

**Summary**: Get scan job status


---

### 🔵 GET `/api/v1/compliance/queue/status`

**Summary**: Get scan queue status

**Description**: Get the current status of the compliance scan queue.

---

### 🔵 GET `/api/v1/compliance/queue/status`

**Summary**: Get scan queue status

**Description**: Get the current status of the compliance scan queue.

---

### 🟢 POST `/api/v1/compliance/scans/{project_id}`

**Summary**: Trigger compliance scan

**Description**: Trigger a compliance scan for a project. Only project owners and admins can trigger scans.

---

### 🟢 POST `/api/v1/compliance/scans/{project_id}`

**Summary**: Trigger compliance scan

**Description**: Trigger a compliance scan for a project. Only project owners and admins can trigger scans.

---

### 🔵 GET `/api/v1/compliance/scans/{project_id}/history`

**Summary**: Get scan history


---

### 🔵 GET `/api/v1/compliance/scans/{project_id}/history`

**Summary**: Get scan history


---

### 🔵 GET `/api/v1/compliance/scans/{project_id}/latest`

**Summary**: Get latest scan result

**Description**: Get the most recent compliance scan result for a project.

---

### 🔵 GET `/api/v1/compliance/scans/{project_id}/latest`

**Summary**: Get latest scan result

**Description**: Get the most recent compliance scan result for a project.

---

### 🟢 POST `/api/v1/compliance/scans/{project_id}/schedule`

**Summary**: Schedule compliance scan

**Description**: Schedule a compliance scan to run in background. Returns immediately with job ID.

---

### 🟢 POST `/api/v1/compliance/scans/{project_id}/schedule`

**Summary**: Schedule compliance scan

**Description**: Schedule a compliance scan to run in background. Returns immediately with job ID.

---

### 🔵 GET `/api/v1/compliance/violations/{project_id}`

**Summary**: Get project violations

**Description**: Get all violations for a project, optionally filtered by resolution status.

---

### 🔵 GET `/api/v1/compliance/violations/{project_id}`

**Summary**: Get project violations

**Description**: Get all violations for a project, optionally filtered by resolution status.

---

### 🟢 POST `/api/v1/compliance/violations/{violation_id}/ai-recommendation`

**Summary**: Generate recommendation for violation

**Description**: Generate and store AI recommendation for a specific violation.

---

### 🟢 POST `/api/v1/compliance/violations/{violation_id}/ai-recommendation`

**Summary**: Generate recommendation for violation

**Description**: Generate and store AI recommendation for a specific violation.

---

### 🟡 PUT `/api/v1/compliance/violations/{violation_id}/resolve`

**Summary**: Resolve violation


---

### 🟡 PUT `/api/v1/compliance/violations/{violation_id}/resolve`

**Summary**: Resolve violation


---

## Compliance Validation

### 🔵 GET `/api/v1/projects/{project_id}/compliance/history`

**Summary**: Get compliance score history

**Description**: Get historical compliance scores for trend analysis.

---

### 🔵 GET `/api/v1/projects/{project_id}/compliance/history`

**Summary**: Get compliance score history

**Description**: Get historical compliance scores for trend analysis.

---

### 🔵 GET `/api/v1/projects/{project_id}/compliance/last-check`

**Summary**: Get last folder collision check


---

### 🔵 GET `/api/v1/projects/{project_id}/compliance/last-check`

**Summary**: Get last folder collision check


---

### 🔵 GET `/api/v1/projects/{project_id}/compliance/score`

**Summary**: Get quick compliance score

**Description**: Get cached compliance score for badges and dashboards. Returns None if never calculated.

---

### 🔵 GET `/api/v1/projects/{project_id}/compliance/score`

**Summary**: Get quick compliance score

**Description**: Get cached compliance score for badges and dashboards. Returns None if never calculated.

---

### 🟢 POST `/api/v1/projects/{project_id}/validate/compliance`

**Summary**: Calculate compliance score

**Description**: Calculate SDLC 6.0.6 compliance score for a project. 10 categories × 10 points = 100 maximum score.

---

### 🟢 POST `/api/v1/projects/{project_id}/validate/compliance`

**Summary**: Calculate compliance score

**Description**: Calculate SDLC 6.0.6 compliance score for a project. 10 categories × 10 points = 100 maximum score.

---

### 🟢 POST `/api/v1/projects/{project_id}/validate/duplicates`

**Summary**: Detect duplicate stage folders

**Description**: Detect stage folder collisions in docs/ directory. Reports duplicates, missing stages, and extra folders.

---

### 🟢 POST `/api/v1/projects/{project_id}/validate/duplicates`

**Summary**: Detect duplicate stage folders

**Description**: Detect stage folder collisions in docs/ directory. Reports duplicates, missing stages, and extra folders.

---

## Context Authority

### 🔵 GET `/api/v1/context-authority/adrs`

**Summary**: List all ADRs

**Description**: Get list of all ADRs in the repository with their status.

---

### 🔵 GET `/api/v1/context-authority/adrs/{adr_id}`

**Summary**: Get specific ADR


---

### 🔵 GET `/api/v1/context-authority/agents-md`

**Summary**: Get AGENTS.md status

**Description**: Get the status and freshness of the AGENTS.md context file.

---

### 🟢 POST `/api/v1/context-authority/check-adr-linkage`

**Summary**: Check ADR linkage for modules


---

### 🟢 POST `/api/v1/context-authority/check-spec`

**Summary**: Check design spec existence

**Description**: Check if a design specification document exists for a task.

---

### 🔵 GET `/api/v1/context-authority/health`

**Summary**: Context authority health check


---

### 🟢 POST `/api/v1/context-authority/validate`

**Summary**: Validate code context linkage

<details>
<summary>View full description</summary>

Validate that code submission has proper context linkage.

    Performs 4 checks:
    1. **ADR Linkage**: Every module must reference at least one ADR
    2. **Design Doc Reference**: New features must have spec files
    3. **AGENTS.md Freshness**: Context file should be updated within 7 days
    4. **Module Annotation Consistency**: @module header must match directory

    **Philosophy**: "Orphan Code = Rejected Code"

    **V1 Scope** (Metadata Only):
    - File existence checks
    - Pattern matching for annotations
    - Simple text search in ADR content

    **NOT in V1 Scope**:
    - Semantic understanding
    - Deep content analysis
    - AI-powered validation

</details>

---

## Context Authority V2

### 🔵 GET `/api/v1/context-authority/v2/health`

**Summary**: Health check


---

### 🔵 GET `/api/v1/context-authority/v2/health`

**Summary**: Health check


---

### 🟢 POST `/api/v1/context-authority/v2/overlay`

**Summary**: Generate dynamic overlay

<details>
<summary>View full description</summary>

Generate dynamic overlay without full validation (SPEC-0011 FR-002).

    **Use Cases**:
    - Preview overlay before submission
    - Generate AGENTS.md context section
    - Real-time overlay updates in IDE

    **Template Selection**:
    1. Gate-based: Triggered by last_passed_gate
    2. Zone-based: Triggered by vibecoding_zone
    3. Stage-based: Triggered by stage constraints

    **Template Variables**:
    - `{date}`: Current date (YYYY-MM-DD)
    - `{index}`: Vibecoding index value
    - `{stage}`: Current SDLC stage
    - `{tier}`: Project tier
    - `{gate}`: Last passed gate
    - `{top_signals}`: Top contributing signals

</details>

---

### 🟢 POST `/api/v1/context-authority/v2/overlay`

**Summary**: Generate dynamic overlay

<details>
<summary>View full description</summary>

Generate dynamic overlay without full validation (SPEC-0011 FR-002).

    **Use Cases**:
    - Preview overlay before submission
    - Generate AGENTS.md context section
    - Real-time overlay updates in IDE

    **Template Selection**:
    1. Gate-based: Triggered by last_passed_gate
    2. Zone-based: Triggered by vibecoding_zone
    3. Stage-based: Triggered by stage constraints

    **Template Variables**:
    - `{date}`: Current date (YYYY-MM-DD)
    - `{index}`: Vibecoding index value
    - `{stage}`: Current SDLC stage
    - `{tier}`: Project tier
    - `{gate}`: Last passed gate
    - `{top_signals}`: Top contributing signals

</details>

---

### 🔵 GET `/api/v1/context-authority/v2/snapshot/{submission_id}`

**Summary**: Get context snapshot


---

### 🔵 GET `/api/v1/context-authority/v2/snapshot/{submission_id}`

**Summary**: Get context snapshot


---

### 🔵 GET `/api/v1/context-authority/v2/snapshots/{project_id}`

**Summary**: List project snapshots


---

### 🔵 GET `/api/v1/context-authority/v2/snapshots/{project_id}`

**Summary**: List project snapshots


---

### 🔵 GET `/api/v1/context-authority/v2/stats`

**Summary**: Get statistics

**Description**: Get Context Authority V2 statistics for a time period.

---

### 🔵 GET `/api/v1/context-authority/v2/stats`

**Summary**: Get statistics

**Description**: Get Context Authority V2 statistics for a time period.

---

### 🔵 GET `/api/v1/context-authority/v2/templates`

**Summary**: List overlay templates

**Description**: List all overlay templates with optional filtering.

---

### 🔵 GET `/api/v1/context-authority/v2/templates`

**Summary**: List overlay templates

**Description**: List all overlay templates with optional filtering.

---

### 🟢 POST `/api/v1/context-authority/v2/templates`

**Summary**: Create overlay template


---

### 🟢 POST `/api/v1/context-authority/v2/templates`

**Summary**: Create overlay template


---

### 🔵 GET `/api/v1/context-authority/v2/templates/{template_id}`

**Summary**: Get template by ID


---

### 🔵 GET `/api/v1/context-authority/v2/templates/{template_id}`

**Summary**: Get template by ID


---

### 🟡 PUT `/api/v1/context-authority/v2/templates/{template_id}`

**Summary**: Update template


---

### 🟡 PUT `/api/v1/context-authority/v2/templates/{template_id}`

**Summary**: Update template


---

### 🔵 GET `/api/v1/context-authority/v2/templates/{template_id}/usage`

**Summary**: Get template usage statistics


---

### 🔵 GET `/api/v1/context-authority/v2/templates/{template_id}/usage`

**Summary**: Get template usage statistics


---

### 🟢 POST `/api/v1/context-authority/v2/validate`

**Summary**: Gate-aware context validation

<details>
<summary>View full description</summary>

Validate code submission with gate-aware rules (SPEC-0011 FR-001).

    **V1 + V2 Combined Validation**:
    1. **V1 Checks**: ADR linkage, design doc, AGENTS.md freshness, module consistency
    2. **V2 Gate Checks**: Stage-aware file blocking (e.g., no code in Stage 02)
    3. **V2 Index Checks**: Vibecoding zone warnings/blocks

    **Stage Rules**:
    - Stage 00 (Discover): Only docs/00-* allowed
    - Stage 01 (Planning): Only docs/01-* allowed
    - Stage 02 (Design): Design docs + schema files allowed
    - Stage 04 (Build): All code allowed
    - Stage 05 (Test): Tests and bug fixes only
    - Stage 06 (Deploy): Infrastructure only

    **Vibecoding Zones**:
    - GREEN (0-30): Auto-approve
    - YELLOW (31-60): Tech Lead review
    - ORANGE (61-80): CEO should review
    - RED (81-100): CEO must review (blocks)

    **Outputs**:
    - `is_valid`: Overall validation result
    - `dynamic_overlay`: Generated context for AGENTS.md
    - `snapshot_id`: Audit trail reference

</details>

---

### 🟢 POST `/api/v1/context-authority/v2/validate`

**Summary**: Gate-aware context validation

<details>
<summary>View full description</summary>

Validate code submission with gate-aware rules (SPEC-0011 FR-001).

    **V1 + V2 Combined Validation**:
    1. **V1 Checks**: ADR linkage, design doc, AGENTS.md freshness, module consistency
    2. **V2 Gate Checks**: Stage-aware file blocking (e.g., no code in Stage 02)
    3. **V2 Index Checks**: Vibecoding zone warnings/blocks

    **Stage Rules**:
    - Stage 00 (Discover): Only docs/00-* allowed
    - Stage 01 (Planning): Only docs/01-* allowed
    - Stage 02 (Design): Design docs + schema files allowed
    - Stage 04 (Build): All code allowed
    - Stage 05 (Test): Tests and bug fixes only
    - Stage 06 (Deploy): Infrastructure only

    **Vibecoding Zones**:
    - GREEN (0-30): Auto-approve
    - YELLOW (31-60): Tech Lead review
    - ORANGE (61-80): CEO should review
    - RED (81-100): CEO must review (blocks)

    **Outputs**:
    - `is_valid`: Overall validation result
    - `dynamic_overlay`: Generated context for AGENTS.md
    - `snapshot_id`: Audit trail reference

</details>

---

## Context Overlay

### 🔵 GET `/api/v1/agents-md/context/{project_id}`

**Summary**: Get context overlay


---

### 🔵 GET `/api/v1/agents-md/context/{project_id}/history`

**Summary**: Get context overlay history

**Description**: Get context overlay delivery history for a project.

---

## Context Validation

### 🔵 GET `/api/v1/context-validation/health`

**Summary**: Health check


---

### 🔵 GET `/api/v1/context-validation/health`

**Summary**: Health check


---

### 🔵 GET `/api/v1/context-validation/limits`

**Summary**: Get context limits configuration

**Description**: Get the current context limits configuration for AGENTS.md validation.

---

### 🔵 GET `/api/v1/context-validation/limits`

**Summary**: Get context limits configuration

**Description**: Get the current context limits configuration for AGENTS.md validation.

---

### 🟢 POST `/api/v1/context-validation/validate`

**Summary**: Validate AGENTS.md context limits

**Description**: Validate that all file contexts in AGENTS.md are within the 60-line limit.

---

### 🟢 POST `/api/v1/context-validation/validate`

**Summary**: Validate AGENTS.md context limits

**Description**: Validate that all file contexts in AGENTS.md are within the 60-line limit.

---

### 🟢 POST `/api/v1/context-validation/validate-github`

**Summary**: Validate AGENTS.md from GitHub repository

**Description**: Fetch and validate AGENTS.md from a GitHub repository.

---

### 🟢 POST `/api/v1/context-validation/validate-github`

**Summary**: Validate AGENTS.md from GitHub repository

**Description**: Fetch and validate AGENTS.md from a GitHub repository.

---

## Contract Lock

### 🟢 POST `/api/v1/onboarding/{session_id}/force-unlock`

**Summary**: Force unlock (admin)

**Description**: Force unlock a specification. Requires admin privileges.

---

### 🟢 POST `/api/v1/onboarding/{session_id}/force-unlock`

**Summary**: Force unlock (admin)

**Description**: Force unlock a specification. Requires admin privileges.

---

### 🟢 POST `/api/v1/onboarding/{session_id}/lock`

**Summary**: Lock specification

<details>
<summary>View full description</summary>

Lock an onboarding session's specification for code generation.

This freezes the AppBlueprint and calculates a SHA256 hash for integrity.
Once locked:
- Specification cannot be modified
- Code generation uses the locked spec
- Hash can be verified at any time

Lock expires after 1 hour if generation is not started (auto-cleanup).

</details>

---

### 🟢 POST `/api/v1/onboarding/{session_id}/lock`

**Summary**: Lock specification

<details>
<summary>View full description</summary>

Lock an onboarding session's specification for code generation.

This freezes the AppBlueprint and calculates a SHA256 hash for integrity.
Once locked:
- Specification cannot be modified
- Code generation uses the locked spec
- Hash can be verified at any time

Lock expires after 1 hour if generation is not started (auto-cleanup).

</details>

---

### 🔵 GET `/api/v1/onboarding/{session_id}/lock-audit`

**Summary**: Get lock audit log

**Description**: Get the audit log of all lock/unlock operations for a session.

---

### 🔵 GET `/api/v1/onboarding/{session_id}/lock-audit`

**Summary**: Get lock audit log

**Description**: Get the audit log of all lock/unlock operations for a session.

---

### 🔵 GET `/api/v1/onboarding/{session_id}/lock-status`

**Summary**: Get lock status

**Description**: Get the current lock status of an onboarding session.

---

### 🔵 GET `/api/v1/onboarding/{session_id}/lock-status`

**Summary**: Get lock status

**Description**: Get the current lock status of an onboarding session.

---

### 🔵 GET `/api/v1/onboarding/{session_id}/status`

**Summary**: Get full session status

**Description**: Get full status of an onboarding session including:
- Lock status
- Generation status
- Blueprint metadata

---

### 🔵 GET `/api/v1/onboarding/{session_id}/status`

**Summary**: Get full session status

**Description**: Get full status of an onboarding session including:
- Lock status
- Generation status
- Blueprint metadata

---

### 🟢 POST `/api/v1/onboarding/{session_id}/unlock`

**Summary**: Unlock specification

<details>
<summary>View full description</summary>

Unlock an onboarding session's specification.

Only the user who locked the spec or an admin can unlock.
Requires a reason for audit trail.

Unlock reasons:
- modification_needed: Need to update the blueprint
- generation_failed: Generation failed, need to retry
- admin_override: Admin unlocking for recovery
- session_expired: Session expired (auto-unlock)

</details>

---

### 🟢 POST `/api/v1/onboarding/{session_id}/unlock`

**Summary**: Unlock specification

<details>
<summary>View full description</summary>

Unlock an onboarding session's specification.

Only the user who locked the spec or an admin can unlock.
Requires a reason for audit trail.

Unlock reasons:
- modification_needed: Need to update the blueprint
- generation_failed: Generation failed, need to retry
- admin_override: Admin unlocking for recovery
- session_expired: Session expired (auto-unlock)

</details>

---

### 🟢 POST `/api/v1/onboarding/{session_id}/verify-hash`

**Summary**: Verify spec hash

**Description**: Verify that the current specification matches an expected hash.

Used internally before code generation to ensure the locked spec
has not been modified. Also useful for audit/compliance.

---

### 🟢 POST `/api/v1/onboarding/{session_id}/verify-hash`

**Summary**: Verify spec hash

**Description**: Verify that the current specification matches an expected hash.

Used internally before code generation to ensure the locked spec
has not been modified. Also useful for audit/compliance.

---

## Cross-Reference

### 🔵 GET `/api/v1/cross-reference/coverage/{project_id}`

**Summary**: Get Coverage

**Description**: Get quick coverage metrics for a project.

Returns only coverage statistics without full validation details.

---

### 🔵 GET `/api/v1/cross-reference/coverage/{project_id}`

**Summary**: Get Coverage

**Description**: Get quick coverage metrics for a project.

Returns only coverage statistics without full validation details.

---

### 🔵 GET `/api/v1/cross-reference/missing-tests/{project_id}`

**Summary**: Get Missing Tests

**Description**: Get list of endpoints missing test coverage.

Returns prioritized list of endpoints that need tests.

---

### 🔵 GET `/api/v1/cross-reference/missing-tests/{project_id}`

**Summary**: Get Missing Tests

**Description**: Get list of endpoints missing test coverage.

Returns prioritized list of endpoints that need tests.

---

### 🔵 GET `/api/v1/cross-reference/ssot-check/{project_id}`

**Summary**: Check Ssot Compliance

**Description**: Check SSOT compliance for OpenAPI specification.

Per RFC-SDLC-602:
- openapi.json should only exist in Stage 03
- No duplicates in Stage 05 or other folders

---

### 🔵 GET `/api/v1/cross-reference/ssot-check/{project_id}`

**Summary**: Check Ssot Compliance

**Description**: Check SSOT compliance for OpenAPI specification.

Per RFC-SDLC-602:
- openapi.json should only exist in Stage 03
- No duplicates in Stage 05 or other folders

---

### 🟢 POST `/api/v1/cross-reference/validate`

**Summary**: Validate Cross Reference

<details>
<summary>View full description</summary>

Validate cross-references between Stage 03 and Stage 05.

RFC-SDLC-602 Phase 5: Cross-Reference Validation

This endpoint:
1. Parses OpenAPI specification from Stage 03
2. Finds test files in Stage 05
3. Matches API endpoints to test coverage
4. Calculates coverage percentage
5. Checks SSOT compliance (no duplicate openapi.json)

Args:
    request: CrossReferenceValidateRequest with project_id and paths

Returns:
    CrossReferenceValidateResponse with validation results

</details>

---

### 🟢 POST `/api/v1/cross-reference/validate`

**Summary**: Validate Cross Reference

<details>
<summary>View full description</summary>

Validate cross-references between Stage 03 and Stage 05.

RFC-SDLC-602 Phase 5: Cross-Reference Validation

This endpoint:
1. Parses OpenAPI specification from Stage 03
2. Finds test files in Stage 05
3. Matches API endpoints to test coverage
4. Calculates coverage percentage
5. Checks SSOT compliance (no duplicate openapi.json)

Args:
    request: CrossReferenceValidateRequest with project_id and paths

Returns:
    CrossReferenceValidateResponse with validation results

</details>

---

## Dashboard

### 🔵 GET `/api/v1/dashboard/recent-gates`

**Summary**: Get Recent Gates

**Description**: Get recent gate activity.

Returns list of recent gates with project info.

---

### 🔵 GET `/api/v1/dashboard/stats`

**Summary**: Get Dashboard Stats

<details>
<summary>View full description</summary>

Get dashboard statistics.

Returns:
    - total_projects: Total number of projects
    - active_gates: Gates with pending status
    - pending_approvals: Gates awaiting approval
    - pass_rate: Percentage of approved gates

</details>

---

## Dependencies

### 🟢 POST `/api/v1/planning/dependencies`

**Summary**: Create sprint dependency

<details>
<summary>View full description</summary>

Create a dependency between two sprints.

**Sprint 78: Cross-Project Sprint Dependencies - Day 2 Implementation**

Dependency types:
- **blocks**: Source sprint is blocked until target completes (critical)
- **requires**: Source requires deliverable from target
- **related**: Sprints are related but not blocking

Validation:
- Both sprints must exist
- No self-reference allowed
- Circular dependencies are prevented

Args:
    data: Dependency creation data

Returns:
    Created SprintDependencyResponse

Raises:
    400: Invalid dependency (circular, self-reference, duplicate)
    404: Sprint not found

</details>

---

### 🟢 POST `/api/v1/planning/dependencies/bulk/resolve`

**Summary**: Bulk resolve dependencies


---

### 🔵 GET `/api/v1/planning/dependencies/check-circular`

**Summary**: Check for circular dependency

**Description**: Check if adding a dependency would create a cycle.

Use this endpoint before creating a dependency to validate.

---

### 🔵 GET `/api/v1/planning/dependencies/{dependency_id}`

**Summary**: Get a sprint dependency


---

### 🟡 PUT `/api/v1/planning/dependencies/{dependency_id}`

**Summary**: Update a sprint dependency

**Description**: Update a dependency's type, description, or status.

---

### 🔴 DELETE `/api/v1/planning/dependencies/{dependency_id}`

**Summary**: Delete a sprint dependency


---

### 🟢 POST `/api/v1/planning/dependencies/{dependency_id}/resolve`

**Summary**: Resolve a sprint dependency


---

### 🔵 GET `/api/v1/planning/projects/{project_id}/dependency-analysis`

**Summary**: Analyze project dependencies

<details>
<summary>View full description</summary>

Analyze dependency structure for a project.

Returns:
- Dependency counts by type and status
- Critical path through dependency chain
- Risk indicators (high-dependency sprints)

</details>

---

### 🔵 GET `/api/v1/planning/projects/{project_id}/dependency-graph`

**Summary**: Get dependency graph for a project

<details>
<summary>View full description</summary>

Get dependency graph for visualization.

**Sprint 78: Cross-Project Sprint Dependencies - Day 2 Implementation**

Returns a graph structure with:
- **nodes**: Sprints with status and blocking info
- **edges**: Dependencies with type and status

Suitable for rendering with visualization libraries like ReactFlow or D3.

</details>

---

### 🔵 GET `/api/v1/planning/sprints/{sprint_id}/dependencies`

**Summary**: List dependencies for a sprint

<details>
<summary>View full description</summary>

List dependencies for a specific sprint.

Direction:
- **incoming**: Dependencies where this sprint is the target
- **outgoing**: Dependencies where this sprint is the source
- **both**: All dependencies involving this sprint

</details>

---

## Documentation

### 🔵 GET `/api/v1/docs/user-support`

**Summary**: List User Support Docs

**Description**: List available user support documentation files.

Returns:
    list[str]: List of available documentation filenames

---

### 🔵 GET `/api/v1/docs/user-support`

**Summary**: List User Support Docs

**Description**: List available user support documentation files.

Returns:
    list[str]: List of available documentation filenames

---

### 🔵 GET `/api/v1/docs/user-support/{filename}`

**Summary**: Get User Support Doc

<details>
<summary>View full description</summary>

Get user support documentation file content.

Args:
    filename: Name of the markdown file to retrieve
    
Returns:
    PlainTextResponse: Markdown content of the documentation file
    
Raises:
    HTTPException: 404 if file not found or not allowed
    HTTPException: 500 if error reading file

</details>

---

### 🔵 GET `/api/v1/docs/user-support/{filename}`

**Summary**: Get User Support Doc

<details>
<summary>View full description</summary>

Get user support documentation file content.

Args:
    filename: Name of the markdown file to retrieve
    
Returns:
    PlainTextResponse: Markdown content of the documentation file
    
Raises:
    HTTPException: 404 if file not found or not allowed
    HTTPException: 500 if error reading file

</details>

---

## Dogfooding

### 🔵 GET `/api/v1/dogfooding/ceo-time/entries`

**Summary**: List Ceo Time Entries

**Description**: List CEO time tracking entries.

Requires CTO or CEO role.

---

### 🟢 POST `/api/v1/dogfooding/ceo-time/record`

**Summary**: Record Ceo Time

**Description**: Record CEO time spent on governance-related activities.

Used to track time savings during Sprint 114 dogfooding.
Requires CTO or CEO role.

---

### 🔵 GET `/api/v1/dogfooding/ceo-time/summary`

**Summary**: Get Ceo Time Summary

**Description**: Get CEO time tracking summary for Sprint 114.

Shows baseline vs actual hours, time saved, and trend data.

---

### 🔵 GET `/api/v1/dogfooding/daily-checks`

**Summary**: Run Daily Checks

**Description**: Run daily checks for Sprint 114 dogfooding.

Day 2: Verify 5+ PRs evaluated, check kill switch dashboard, baseline CEO time
Day 3: Analyze first 10 PRs, tune thresholds, collect developer feedback
Day 4: Review false positives, adjust prompts, prepare metrics report

---

### 🔵 GET `/api/v1/dogfooding/daily-checks/history`

**Summary**: Get Daily Checks History

**Description**: Get history of daily checks for all sprint days.

Returns a summary of checks for each day of Sprint 114.

---

### 🟢 POST `/api/v1/dogfooding/enforce/soft`

**Summary**: Enforce Soft Mode

<details>
<summary>View full description</summary>

Evaluate PR against SOFT mode enforcement rules.

SOFT Mode Rules (Sprint 115):
- RED zone (81-100): BLOCK with CTO override option
- ORANGE zone (61-80): WARN (Tech Lead should review)
- YELLOW zone (31-60): WARN (Spot check recommended)
- GREEN zone (0-30): PASS (Auto-approve)

Exemptions applied:
- dependency_update_exemption: Package files only = reduced friction
- documentation_safe_pattern: docs/ only + low index = auto-approve
- test_only_pattern: tests/ only = warn, never block

This endpoint does not require authentication for GitHub Actions integration.

</details>

---

### 🔵 GET `/api/v1/dogfooding/enforce/soft/log`

**Summary**: Get Soft Enforcement Log

**Description**: Get SOFT mode enforcement log.

Returns paginated list of enforcement decisions for audit and analysis.
Requires authenticated user.

---

### 🟢 POST `/api/v1/dogfooding/enforce/soft/override`

**Summary**: Request Cto Override

**Description**: Request CTO override for blocked PR.

Only available for RED zone PRs. Requires authentication.
CTO/CEO can approve overrides directly.

---

### 🔵 GET `/api/v1/dogfooding/enforce/soft/status`

**Summary**: Get Soft Mode Status

**Description**: Get current SOFT mode configuration and metrics.

Returns configuration details and enforcement statistics.

---

### 🔵 GET `/api/v1/dogfooding/export/json`

**Summary**: Export Json Metrics

**Description**: Export all dogfooding metrics as JSON.

Comprehensive export for reporting and analysis.

---

### 🔵 GET `/api/v1/dogfooding/export/prometheus`

**Summary**: Export Prometheus Metrics

**Description**: Export dogfooding metrics in Prometheus format.

Used by Prometheus scraper for Grafana dashboards.

---

### 🟢 POST `/api/v1/dogfooding/feedback`

**Summary**: Submit Developer Feedback

**Description**: Submit developer feedback for Sprint 114 dogfooding.

Collects satisfaction ratings, NPS scores, and qualitative feedback
to assess developer experience with WARNING mode governance.

---

### 🔵 GET `/api/v1/dogfooding/feedback/list`

**Summary**: List Developer Feedback

**Description**: List all developer feedback submissions.

Requires CTO or admin role for full access.
Regular users only see their own feedback.

---

### 🔵 GET `/api/v1/dogfooding/feedback/summary`

**Summary**: Get Feedback Summary

**Description**: Get aggregated developer feedback summary.

Returns NPS scores, satisfaction distribution, and top pain points
for Sprint 114 dogfooding analysis.

---

### 🔵 GET `/api/v1/dogfooding/go-no-go`

**Summary**: Get Go No Go Decision

**Description**: Get Go/No-Go decision for Sprint 115 (SOFT mode).

Evaluates all criteria and provides recommendation.
Requires CTO or CEO role.

---

### 🔵 GET `/api/v1/dogfooding/metrics`

**Summary**: Get Dogfooding Metrics

**Description**: Get Sprint 114 dogfooding metrics for WARNING mode observation.

Returns aggregated metrics for Go/No-Go decision support.

---

### 🔵 GET `/api/v1/dogfooding/prs`

**Summary**: Get Pr Metrics

**Description**: Get list of PR governance evaluations.

Paginated list of PRs evaluated during dogfooding period.

---

### 🟢 POST `/api/v1/dogfooding/prs/record`

**Summary**: Record Pr Metric

**Description**: Record a PR governance evaluation metric.

Called by GitHub Actions workflow after each PR evaluation.
No authentication required for GitHub Actions webhook.

---

### 🟢 POST `/api/v1/dogfooding/report-false-positive`

**Summary**: Report False Positive

**Description**: Report a false positive governance evaluation.

Used by developers to flag incorrect violations for calibration.

---

### 🔵 GET `/api/v1/dogfooding/status`

**Summary**: Get Dogfooding Status

**Description**: Get current dogfooding status (public endpoint).

Returns basic status information for monitoring.

---

## E2E Testing

### 🟢 POST `/api/v1/e2e/cancel/{execution_id}`

**Summary**: Cancel Execution

<details>
<summary>View full description</summary>

Cancel a running E2E test execution.

Args:
    execution_id: Unique execution identifier
    db: Database session
    current_user: Authenticated user

Returns:
    Cancellation confirmation

Raises:
    HTTPException 404: Execution not found
    HTTPException 400: Execution not cancellable

</details>

---

### 🟢 POST `/api/v1/e2e/cancel/{execution_id}`

**Summary**: Cancel Execution

<details>
<summary>View full description</summary>

Cancel a running E2E test execution.

Args:
    execution_id: Unique execution identifier
    db: Database session
    current_user: Authenticated user

Returns:
    Cancellation confirmation

Raises:
    HTTPException 404: Execution not found
    HTTPException 400: Execution not cancellable

</details>

---

### 🟢 POST `/api/v1/e2e/execute`

**Summary**: Execute E2E Tests

<details>
<summary>View full description</summary>

Execute E2E API tests asynchronously.

Supports Newman (Postman), Pytest, and REST Assured test runners.
Tests run in background and results can be retrieved via GET /results/{id}.

RFC-SDLC-602 Phase 2: Test Execution

Args:
    request: Test execution configuration
    background_tasks: FastAPI background tasks handler
    db: Database session
    current_user: Authenticated user

Returns:
    TestExecutionResult with execution ID for tracking

Raises:
    HTTPException 404: Project not found
    HTTPException 400: Invalid test configuration

</details>

---

### 🟢 POST `/api/v1/e2e/execute`

**Summary**: Execute E2E Tests

<details>
<summary>View full description</summary>

Execute E2E API tests asynchronously.

Supports Newman (Postman), Pytest, and REST Assured test runners.
Tests run in background and results can be retrieved via GET /results/{id}.

RFC-SDLC-602 Phase 2: Test Execution

Args:
    request: Test execution configuration
    background_tasks: FastAPI background tasks handler
    db: Database session
    current_user: Authenticated user

Returns:
    TestExecutionResult with execution ID for tracking

Raises:
    HTTPException 404: Project not found
    HTTPException 400: Invalid test configuration

</details>

---

### 🔵 GET `/api/v1/e2e/history`

**Summary**: Get Execution History

<details>
<summary>View full description</summary>

Get E2E test execution history.

Args:
    project_id: Optional project filter
    limit: Maximum results to return
    db: Database session
    current_user: Authenticated user

Returns:
    List of recent test executions

</details>

---

### 🔵 GET `/api/v1/e2e/history`

**Summary**: Get Execution History

<details>
<summary>View full description</summary>

Get E2E test execution history.

Args:
    project_id: Optional project filter
    limit: Maximum results to return
    db: Database session
    current_user: Authenticated user

Returns:
    List of recent test executions

</details>

---

### 🔵 GET `/api/v1/e2e/results/{execution_id}`

**Summary**: Get Test Results

<details>
<summary>View full description</summary>

Get E2E test execution results.

Returns complete test results including individual test cases,
pass/fail counts, and execution timing.

RFC-SDLC-602 Phase 3: Report Generation

Args:
    execution_id: Unique execution identifier
    db: Database session
    current_user: Authenticated user

Returns:
    TestResults with complete execution data

Raises:
    HTTPException 404: Execution not found
    HTTPException 202: Execution still in progress

</details>

---

### 🔵 GET `/api/v1/e2e/results/{execution_id}`

**Summary**: Get Test Results

<details>
<summary>View full description</summary>

Get E2E test execution results.

Returns complete test results including individual test cases,
pass/fail counts, and execution timing.

RFC-SDLC-602 Phase 3: Report Generation

Args:
    execution_id: Unique execution identifier
    db: Database session
    current_user: Authenticated user

Returns:
    TestResults with complete execution data

Raises:
    HTTPException 404: Execution not found
    HTTPException 202: Execution still in progress

</details>

---

### 🔵 GET `/api/v1/e2e/status/{execution_id}`

**Summary**: Get Execution Status

<details>
<summary>View full description</summary>

Check E2E test execution status.

Provides real-time progress updates for running tests.

Args:
    execution_id: Unique execution identifier
    db: Database session
    current_user: Authenticated user

Returns:
    ExecutionStatusResponse with current progress

Raises:
    HTTPException 404: Execution not found

</details>

---

### 🔵 GET `/api/v1/e2e/status/{execution_id}`

**Summary**: Get Execution Status

<details>
<summary>View full description</summary>

Check E2E test execution status.

Provides real-time progress updates for running tests.

Args:
    execution_id: Unique execution identifier
    db: Database session
    current_user: Authenticated user

Returns:
    ExecutionStatusResponse with current progress

Raises:
    HTTPException 404: Execution not found

</details>

---

## Evidence

### 🔵 GET `/api/v1/projects/{project_id}/evidence/gaps`

**Summary**: Get Evidence Gaps

<details>
<summary>View full description</summary>

Get detailed gap analysis report for a project.

Query Parameters:
    interface: Filter by interface (backend, frontend, extension, cli)

Returns:
    {
        "gaps": {
            "missing_evidence": [...],
            "backend_gaps": [...],
            "frontend_gaps": [...],
            "extension_gaps": [...],
            "cli_gaps": [...],
            "test_gaps": [...]
        },
        "total_gaps": int,
        "recommendations": [...]
    }

</details>

---

### 🔵 GET `/api/v1/projects/{project_id}/evidence/status`

**Summary**: Get Evidence Status

<details>
<summary>View full description</summary>

Get evidence completeness status for a project.

Called by:
- OPA policies during gate evaluation (gates/evidence_completeness.rego)
- Frontend dashboard (evidence status widget)
- CLI tools (sdlcctl evidence check)

Returns:
    {
        "status": "complete" | "partial" | "missing",
        "gaps": {
            "backend": [...],
            "frontend": [...],
            "extension": [...],
            "cli": [...]
        },
        "total_gaps": int,
        "checked_at": "ISO 8601 timestamp",
        "specs_checked": int,
        "specs_complete": int
    }

Raises:
    HTTPException 404: Project not found
    HTTPException 403: User not authorized

</details>

---

### 🟢 POST `/api/v1/projects/{project_id}/evidence/validate`

**Summary**: Trigger Evidence Validation

<details>
<summary>View full description</summary>

Trigger full evidence validation and update validation metadata.

This endpoint:
1. Runs evidence validation
2. Updates validation.last_checked timestamps in evidence files
3. Returns full validation report

Used by:
- Manual validation requests from dashboard
- Scheduled validation jobs
- Pre-deployment validation

Returns:
    {
        "validation_id": UUID,
        "status": "complete" | "partial" | "missing",
        "violations": [...],
        "summary": {...}
    }

</details>

---

## Evidence Manifest

### 🟢 POST `/api/v1/evidence-manifests`

**Summary**: Create evidence manifest

<details>
<summary>View full description</summary>

Create a new evidence manifest with hash chain linking (Sprint 82 P0).

    **Hash Chain Design**:
    - Each manifest's `manifest_hash` = SHA256(content)
    - Each manifest's `previous_manifest_hash` = previous manifest's hash
    - Genesis manifests have `previous_manifest_hash = null`
    - Chain forms linked list: M1 → M2 → M3 → ...

    **Ed25519 Signing**:
    - Manifests are signed with Ed25519 private key
    - Non-repudiation: Only server can sign, anyone can verify
    - Signature stored in `signature` field

    **Request**:
    - `project_id`: Project UUID
    - `artifacts`: List of artifact entries to include

    **Response** (201 Created):
    - Complete manifest with hash, signature, sequence number
    - `is_genesis = true` if first manifest for project

</details>

---

### 🔵 GET `/api/v1/evidence-manifests`

**Summary**: List evidence manifests

<details>
<summary>View full description</summary>

List all evidence manifests for a project, ordered by sequence number.

    **Pagination**:
    - `limit`: Max results (default 100, max 1000)
    - `offset`: Offset for pagination

    **Response**:
    - `total`: Total manifests for project
    - `manifests`: List of manifest objects

</details>

---

### 🔵 GET `/api/v1/evidence-manifests/latest`

**Summary**: Get latest manifest

**Description**: Get the latest (highest sequence number) manifest for a project.

    Returns null if no manifests exist for the project.

---

### 🔵 GET `/api/v1/evidence-manifests/status`

**Summary**: Get chain status

<details>
<summary>View full description</summary>

Get chain status summary for a project.

    **Response includes**:
    - Total manifest count
    - Latest sequence number
    - Latest manifest hash
    - Last verification result (if any)

</details>

---

### 🔵 GET `/api/v1/evidence-manifests/verifications`

**Summary**: Get verification history

<details>
<summary>View full description</summary>

Get verification history for a project.

    Shows all past chain verification runs, including:
    - Verification timestamp
    - Result (valid/invalid)
    - Error details (if invalid)
    - Who/what triggered verification

</details>

---

### 🟢 POST `/api/v1/evidence-manifests/verify`

**Summary**: Verify hash chain

<details>
<summary>View full description</summary>

Verify the integrity of the entire hash chain for a project (Sprint 82 P0).

    **Verification Steps**:
    1. Load all manifests ordered by sequence
    2. Verify each manifest's hash matches content
    3. Verify each manifest's `previous_manifest_hash` matches prior manifest
    4. Verify Ed25519 signatures (if keys available)
    5. Check for sequence gaps

    **Result**:
    - `is_valid = true`: All checks passed
    - `is_valid = false`: Chain integrity broken (tampering detected)

    **Audit**:
    - Each verification is logged to `evidence_manifest_verifications`
    - Results available via GET /evidence-manifests/verifications

</details>

---

### 🔵 GET `/api/v1/evidence-manifests/{manifest_id}`

**Summary**: Get manifest by ID


---

## Evidence Timeline

### 🔵 GET `/api/v1/projects/{project_id}/timeline`

**Summary**: List evidence timeline events

<details>
<summary>View full description</summary>

Get paginated list of AI code events for a project with filters.

    **Query Parameters**:
    - page: Page number (default: 1)
    - limit: Items per page (default: 20, max: 100)
    - date_start: Filter events after this date
    - date_end: Filter events before this date
    - ai_tool: Filter by AI tool (cursor, copilot, claude, etc)
    - validation_status: Filter by validation status
    - search: Search in PR title/number

    **Response**:
    - Paginated list of events
    - Timeline statistics
    - Total count and pagination info

</details>

---

### 🔵 GET `/api/v1/projects/{project_id}/timeline/export`

**Summary**: Export evidence data

<details>
<summary>View full description</summary>

Export evidence timeline data in CSV or JSON format.

    **Query Parameters**:
    - format: Export format (csv or json, default: csv)
    - date_start: Filter events after this date
    - date_end: Filter events before this date
    - include_details: Include validator details (default: false)

    **Response**:
    - File download with evidence data

</details>

---

### 🔵 GET `/api/v1/projects/{project_id}/timeline/stats`

**Summary**: Get timeline statistics

<details>
<summary>View full description</summary>

Get aggregated statistics for the evidence timeline.

    **Response**:
    - Total events count
    - AI-detected events count
    - Pass rate percentage
    - Override rate percentage
    - Breakdown by AI tool
    - Breakdown by validation status

</details>

---

### 🔵 GET `/api/v1/projects/{project_id}/timeline/{event_id}`

**Summary**: Get event detail

<details>
<summary>View full description</summary>

Get detailed information for a specific AI code event.

    **Response**:
    - Full event metadata
    - Individual validator results
    - Detection evidence
    - Override history
    - GitHub integration links

</details>

---

### 🟢 POST `/api/v1/timeline/{event_id}/override/approve`

**Summary**: Approve override

<details>
<summary>View full description</summary>

Approve a pending override request.

    **Access Control**:
    - Requires ADMIN or MANAGER role

    **Request Body**:
    - comment: Optional approval comment

    **Response**:
    - Updated override record with approved status

</details>

---

### 🟢 POST `/api/v1/timeline/{event_id}/override/reject`

**Summary**: Reject override

<details>
<summary>View full description</summary>

Reject a pending override request.

    **Access Control**:
    - Requires ADMIN or MANAGER role

    **Request Body**:
    - reason: Required rejection reason (min 10 chars)

    **Response**:
    - Updated override record with rejected status

</details>

---

### 🟢 POST `/api/v1/timeline/{event_id}/override/request`

**Summary**: Request override

<details>
<summary>View full description</summary>

Request an override for a failed validation event.

    **Request Body**:
    - override_type: Type of override (false_positive, approved_risk, emergency)
    - reason: Detailed justification (min 50 chars)

    **Response** (201 Created):
    - Override record with pending status

    **Notes**:
    - Only available for events with failed validation
    - Requires valid justification
    - Creates audit trail for compliance

</details>

---

## Feedback

### 🟢 POST `/api/v1/feedback`

**Summary**: Create Feedback

**Description**: Submit new feedback.

Anyone with an account can submit feedback about bugs,
feature requests, or general improvements.

---

### 🟢 POST `/api/v1/feedback`

**Summary**: Create Feedback

**Description**: Submit new feedback.

Anyone with an account can submit feedback about bugs,
feature requests, or general improvements.

---

### 🔵 GET `/api/v1/feedback`

**Summary**: List Feedback

**Description**: List all feedback with optional filters.

Supports filtering by type, status, and priority.
Results are paginated.

---

### 🔵 GET `/api/v1/feedback`

**Summary**: List Feedback

**Description**: List all feedback with optional filters.

Supports filtering by type, status, and priority.
Results are paginated.

---

### 🔵 GET `/api/v1/feedback/stats`

**Summary**: Get Feedback Stats

**Description**: Get feedback statistics.

Returns counts by type, status, and priority,
plus average resolution time.

---

### 🔵 GET `/api/v1/feedback/stats`

**Summary**: Get Feedback Stats

**Description**: Get feedback statistics.

Returns counts by type, status, and priority,
plus average resolution time.

---

### 🔵 GET `/api/v1/feedback/{feedback_id}`

**Summary**: Get Feedback


---

### 🔵 GET `/api/v1/feedback/{feedback_id}`

**Summary**: Get Feedback


---

### 🟠 PATCH `/api/v1/feedback/{feedback_id}`

**Summary**: Update Feedback

**Description**: Update feedback status, priority, or resolution.

Only admins or the original submitter can update.

---

### 🟠 PATCH `/api/v1/feedback/{feedback_id}`

**Summary**: Update Feedback

**Description**: Update feedback status, priority, or resolution.

Only admins or the original submitter can update.

---

### 🟢 POST `/api/v1/feedback/{feedback_id}/comments`

**Summary**: Add Comment


---

### 🟢 POST `/api/v1/feedback/{feedback_id}/comments`

**Summary**: Add Comment


---

### 🔵 GET `/api/v1/feedback/{feedback_id}/comments`

**Summary**: List Comments


---

### 🔵 GET `/api/v1/feedback/{feedback_id}/comments`

**Summary**: List Comments


---

## Feedback Learning

### 🟢 POST `/api/v1/learnings/projects/{project_id}/aggregations`

**Summary**: Create aggregation

**Description**: Create and process a learning aggregation for a period.

---

### 🔵 GET `/api/v1/learnings/projects/{project_id}/aggregations`

**Summary**: List aggregations


---

### 🔵 GET `/api/v1/learnings/projects/{project_id}/aggregations/{aggregation_id}`

**Summary**: Get aggregation


---

### 🟢 POST `/api/v1/learnings/projects/{project_id}/aggregations/{aggregation_id}/apply`

**Summary**: Apply aggregation suggestions

**Description**: Apply the suggestions from an aggregation (creates hints, etc.).

---

### 🟢 POST `/api/v1/learnings/projects/{project_id}/aggregations/{aggregation_id}/reject`

**Summary**: Reject aggregation suggestions


---

### 🟢 POST `/api/v1/learnings/projects/{project_id}/generate-hints`

**Summary**: Generate hints from learnings

**Description**: Generate decomposition hints from unapplied learnings (monthly job).

---

### 🟢 POST `/api/v1/learnings/projects/{project_id}/hints`

**Summary**: Create a hint


---

### 🔵 GET `/api/v1/learnings/projects/{project_id}/hints`

**Summary**: List hints


---

### 🔵 GET `/api/v1/learnings/projects/{project_id}/hints/active`

**Summary**: Get active hints for decomposition

**Description**: Get hints relevant for a specific decomposition context.

---

### 🔵 GET `/api/v1/learnings/projects/{project_id}/hints/stats`

**Summary**: Get hint statistics


---

### 🟢 POST `/api/v1/learnings/projects/{project_id}/hints/usage`

**Summary**: Record hint usage


---

### 🟢 POST `/api/v1/learnings/projects/{project_id}/hints/usage/{usage_id}/feedback`

**Summary**: Provide hint usage feedback


---

### 🔵 GET `/api/v1/learnings/projects/{project_id}/hints/{hint_id}`

**Summary**: Get a hint


---

### 🟠 PATCH `/api/v1/learnings/projects/{project_id}/hints/{hint_id}`

**Summary**: Update a hint


---

### 🟢 POST `/api/v1/learnings/projects/{project_id}/hints/{hint_id}/verify`

**Summary**: Verify a hint


---

### 🟢 POST `/api/v1/learnings/projects/{project_id}/learnings`

**Summary**: Create a learning manually

**Description**: Create a PR learning record manually (not from AI extraction).

---

### 🔵 GET `/api/v1/learnings/projects/{project_id}/learnings`

**Summary**: List learnings

**Description**: List PR learnings with optional filtering and pagination.

---

### 🟢 POST `/api/v1/learnings/projects/{project_id}/learnings/bulk-status`

**Summary**: Bulk update learning status


---

### 🟢 POST `/api/v1/learnings/projects/{project_id}/learnings/extract`

**Summary**: Extract learning from PR comment

**Description**: Use AI to extract a learning from a PR review comment.

---

### 🔵 GET `/api/v1/learnings/projects/{project_id}/learnings/stats`

**Summary**: Get learning statistics


---

### 🔵 GET `/api/v1/learnings/projects/{project_id}/learnings/{learning_id}`

**Summary**: Get a learning


---

### 🟠 PATCH `/api/v1/learnings/projects/{project_id}/learnings/{learning_id}`

**Summary**: Update a learning


---

## Feedback Learning (EP-11)

### 🟢 POST `/api/v1/learnings/projects/{project_id}/aggregations`

**Summary**: Create aggregation

**Description**: Create and process a learning aggregation for a period.

---

### 🔵 GET `/api/v1/learnings/projects/{project_id}/aggregations`

**Summary**: List aggregations


---

### 🔵 GET `/api/v1/learnings/projects/{project_id}/aggregations/{aggregation_id}`

**Summary**: Get aggregation


---

### 🟢 POST `/api/v1/learnings/projects/{project_id}/aggregations/{aggregation_id}/apply`

**Summary**: Apply aggregation suggestions

**Description**: Apply the suggestions from an aggregation (creates hints, etc.).

---

### 🟢 POST `/api/v1/learnings/projects/{project_id}/aggregations/{aggregation_id}/reject`

**Summary**: Reject aggregation suggestions


---

### 🟢 POST `/api/v1/learnings/projects/{project_id}/generate-hints`

**Summary**: Generate hints from learnings

**Description**: Generate decomposition hints from unapplied learnings (monthly job).

---

### 🟢 POST `/api/v1/learnings/projects/{project_id}/hints`

**Summary**: Create a hint


---

### 🔵 GET `/api/v1/learnings/projects/{project_id}/hints`

**Summary**: List hints


---

### 🔵 GET `/api/v1/learnings/projects/{project_id}/hints/active`

**Summary**: Get active hints for decomposition

**Description**: Get hints relevant for a specific decomposition context.

---

### 🔵 GET `/api/v1/learnings/projects/{project_id}/hints/stats`

**Summary**: Get hint statistics


---

### 🟢 POST `/api/v1/learnings/projects/{project_id}/hints/usage`

**Summary**: Record hint usage


---

### 🟢 POST `/api/v1/learnings/projects/{project_id}/hints/usage/{usage_id}/feedback`

**Summary**: Provide hint usage feedback


---

### 🔵 GET `/api/v1/learnings/projects/{project_id}/hints/{hint_id}`

**Summary**: Get a hint


---

### 🟠 PATCH `/api/v1/learnings/projects/{project_id}/hints/{hint_id}`

**Summary**: Update a hint


---

### 🟢 POST `/api/v1/learnings/projects/{project_id}/hints/{hint_id}/verify`

**Summary**: Verify a hint


---

### 🟢 POST `/api/v1/learnings/projects/{project_id}/learnings`

**Summary**: Create a learning manually

**Description**: Create a PR learning record manually (not from AI extraction).

---

### 🔵 GET `/api/v1/learnings/projects/{project_id}/learnings`

**Summary**: List learnings

**Description**: List PR learnings with optional filtering and pagination.

---

### 🟢 POST `/api/v1/learnings/projects/{project_id}/learnings/bulk-status`

**Summary**: Bulk update learning status


---

### 🟢 POST `/api/v1/learnings/projects/{project_id}/learnings/extract`

**Summary**: Extract learning from PR comment

**Description**: Use AI to extract a learning from a PR review comment.

---

### 🔵 GET `/api/v1/learnings/projects/{project_id}/learnings/stats`

**Summary**: Get learning statistics


---

### 🔵 GET `/api/v1/learnings/projects/{project_id}/learnings/{learning_id}`

**Summary**: Get a learning


---

### 🟠 PATCH `/api/v1/learnings/projects/{project_id}/learnings/{learning_id}`

**Summary**: Update a learning


---

## Framework Version

### 🔵 GET `/api/v1/framework-version/health`

**Summary**: Health check


---

### 🔵 GET `/api/v1/framework-version/health`

**Summary**: Health check


---

### 🔵 GET `/api/v1/framework-version/{project_id}`

**Summary**: Get current Framework version

**Description**: Get the current (latest) Framework version for a project.

---

### 🔵 GET `/api/v1/framework-version/{project_id}`

**Summary**: Get current Framework version

**Description**: Get the current (latest) Framework version for a project.

---

### 🟢 POST `/api/v1/framework-version/{project_id}`

**Summary**: Record new Framework version

**Description**: Record a new Framework version for a project (e.g., after migration).

---

### 🟢 POST `/api/v1/framework-version/{project_id}`

**Summary**: Record new Framework version

**Description**: Record a new Framework version for a project (e.g., after migration).

---

### 🔵 GET `/api/v1/framework-version/{project_id}/compliance`

**Summary**: Get compliance summary


---

### 🔵 GET `/api/v1/framework-version/{project_id}/compliance`

**Summary**: Get compliance summary


---

### 🔵 GET `/api/v1/framework-version/{project_id}/drift`

**Summary**: Check version drift

**Description**: Check if project is behind the latest Framework version.

---

### 🔵 GET `/api/v1/framework-version/{project_id}/drift`

**Summary**: Check version drift

**Description**: Check if project is behind the latest Framework version.

---

### 🔵 GET `/api/v1/framework-version/{project_id}/history`

**Summary**: Get version history


---

### 🔵 GET `/api/v1/framework-version/{project_id}/history`

**Summary**: Get version history


---

## Gates

### 🟢 POST `/api/v1/gates`

**Summary**: Create Gate

<details>
<summary>View full description</summary>

Create new quality gate.

Request Body:
    {
        "project_id": "550e8400-e29b-41d4-a716-446655440000",
        "gate_name": "G2",
        "gate_type": "SHIP_READY",
        "stage": "SHIP",
        "description": "G2 (Ship Ready) - Production deployment approval",
        "exit_criteria": [
            {"criterion": "Zero P0 bugs", "status": "pending"}
        ]
    }

Response (201 Created):
    {
        "id": "...",
        "project_id": "...",
        "gate_name": "G2",
        "status": "DRAFT",
        ...
    }

Errors:
    - 401 Unauthorized: Invalid token
    - 403 Forbidden: User not project member
    - 404 Not Found: Project not found

Flow:
    1. Validate user is project member

*(truncated for brevity)*

</details>

---

### 🟢 POST `/api/v1/gates`

**Summary**: Create Gate

<details>
<summary>View full description</summary>

Create new quality gate.

Request Body:
    {
        "project_id": "550e8400-e29b-41d4-a716-446655440000",
        "gate_name": "G2",
        "gate_type": "SHIP_READY",
        "stage": "SHIP",
        "description": "G2 (Ship Ready) - Production deployment approval",
        "exit_criteria": [
            {"criterion": "Zero P0 bugs", "status": "pending"}
        ]
    }

Response (201 Created):
    {
        "id": "...",
        "project_id": "...",
        "gate_name": "G2",
        "status": "DRAFT",
        ...
    }

Errors:
    - 401 Unauthorized: Invalid token
    - 403 Forbidden: User not project member
    - 404 Not Found: Project not found

Flow:
    1. Validate user is project member

*(truncated for brevity)*

</details>

---

### 🔵 GET `/api/v1/gates`

**Summary**: List Gates

<details>
<summary>View full description</summary>

List quality gates with pagination and filters.

Query Parameters:
    - project_id: Filter by project UUID
    - stage: Filter by stage (WHY, WHAT, BUILD, TEST, SHIP, etc.)
    - status: Filter by status (DRAFT, PENDING_APPROVAL, APPROVED, REJECTED)
    - page: Page number (default: 1)
    - page_size: Items per page (default: 20, max: 100)

Response (200 OK):
    {
        "items": [
            {"id": "...", "gate_name": "G2", ...}
        ],
        "total": 9,
        "page": 1,
        "page_size": 20,
        "pages": 1
    }

Errors:
    - 401 Unauthorized: Invalid token

Flow:
    1. Build query with filters
    2. Get total count
    3. Apply pagination
    4. Return paginated results

</details>

---

### 🔵 GET `/api/v1/gates`

**Summary**: List Gates

<details>
<summary>View full description</summary>

List quality gates with pagination and filters.

Query Parameters:
    - project_id: Filter by project UUID
    - stage: Filter by stage (WHY, WHAT, BUILD, TEST, SHIP, etc.)
    - status: Filter by status (DRAFT, PENDING_APPROVAL, APPROVED, REJECTED)
    - page: Page number (default: 1)
    - page_size: Items per page (default: 20, max: 100)

Response (200 OK):
    {
        "items": [
            {"id": "...", "gate_name": "G2", ...}
        ],
        "total": 9,
        "page": 1,
        "page_size": 20,
        "pages": 1
    }

Errors:
    - 401 Unauthorized: Invalid token

Flow:
    1. Build query with filters
    2. Get total count
    3. Apply pagination
    4. Return paginated results

</details>

---

### 🔵 GET `/api/v1/gates/{gate_id}`

**Summary**: Get Gate

<details>
<summary>View full description</summary>

Get gate details by ID.

Path Parameters:
    - gate_id: Gate UUID

Response (200 OK):
    {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "gate_name": "G2",
        "status": "APPROVED",
        "approvals": [
            {
                "approved_by_name": "Hoàng Văn Em (CTO)",
                "is_approved": true,
                "approved_at": "2025-11-28T10:30:00Z"
            }
        ],
        ...
    }

Errors:
    - 401 Unauthorized: Invalid token
    - 403 Forbidden: User not project member
    - 404 Not Found: Gate not found

Flow:
    1. Fetch gate by ID
    2. Verify user is project member
    3. Load approvals, evidence count, policy violations
    4. Return gate details

</details>

---

### 🔵 GET `/api/v1/gates/{gate_id}`

**Summary**: Get Gate

<details>
<summary>View full description</summary>

Get gate details by ID.

Path Parameters:
    - gate_id: Gate UUID

Response (200 OK):
    {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "gate_name": "G2",
        "status": "APPROVED",
        "approvals": [
            {
                "approved_by_name": "Hoàng Văn Em (CTO)",
                "is_approved": true,
                "approved_at": "2025-11-28T10:30:00Z"
            }
        ],
        ...
    }

Errors:
    - 401 Unauthorized: Invalid token
    - 403 Forbidden: User not project member
    - 404 Not Found: Gate not found

Flow:
    1. Fetch gate by ID
    2. Verify user is project member
    3. Load approvals, evidence count, policy violations
    4. Return gate details

</details>

---

### 🟡 PUT `/api/v1/gates/{gate_id}`

**Summary**: Update Gate

<details>
<summary>View full description</summary>

Update gate details.

Path Parameters:
    - gate_id: Gate UUID

Request Body:
    {
        "gate_name": "G2 (Updated)",
        "description": "Updated description",
        "exit_criteria": [...]
    }

Response (200 OK):
    {
        "id": "...",
        "gate_name": "G2 (Updated)",
        ...
    }

Errors:
    - 401 Unauthorized: Invalid token
    - 403 Forbidden: User not project member or gate already approved
    - 404 Not Found: Gate not found

Flow:
    1. Fetch gate by ID
    2. Verify user is project member
    3. Verify gate status is DRAFT (cannot update approved gates)
    4. Update gate fields
    5. Return updated gate

</details>

---

### 🟡 PUT `/api/v1/gates/{gate_id}`

**Summary**: Update Gate

<details>
<summary>View full description</summary>

Update gate details.

Path Parameters:
    - gate_id: Gate UUID

Request Body:
    {
        "gate_name": "G2 (Updated)",
        "description": "Updated description",
        "exit_criteria": [...]
    }

Response (200 OK):
    {
        "id": "...",
        "gate_name": "G2 (Updated)",
        ...
    }

Errors:
    - 401 Unauthorized: Invalid token
    - 403 Forbidden: User not project member or gate already approved
    - 404 Not Found: Gate not found

Flow:
    1. Fetch gate by ID
    2. Verify user is project member
    3. Verify gate status is DRAFT (cannot update approved gates)
    4. Update gate fields
    5. Return updated gate

</details>

---

### 🔴 DELETE `/api/v1/gates/{gate_id}`

**Summary**: Delete Gate

<details>
<summary>View full description</summary>

Delete gate (soft delete).

Path Parameters:
    - gate_id: Gate UUID

Response (204 No Content):
    (empty response)

Errors:
    - 401 Unauthorized: Invalid token
    - 403 Forbidden: User not project member or gate already approved
    - 404 Not Found: Gate not found

Flow:
    1. Fetch gate by ID
    2. Verify user is project member
    3. Verify gate status is DRAFT (cannot delete approved gates)
    4. Soft delete gate (set deleted_at timestamp)
    5. Return 204 No Content

</details>

---

### 🔴 DELETE `/api/v1/gates/{gate_id}`

**Summary**: Delete Gate

<details>
<summary>View full description</summary>

Delete gate (soft delete).

Path Parameters:
    - gate_id: Gate UUID

Response (204 No Content):
    (empty response)

Errors:
    - 401 Unauthorized: Invalid token
    - 403 Forbidden: User not project member or gate already approved
    - 404 Not Found: Gate not found

Flow:
    1. Fetch gate by ID
    2. Verify user is project member
    3. Verify gate status is DRAFT (cannot delete approved gates)
    4. Soft delete gate (set deleted_at timestamp)
    5. Return 204 No Content

</details>

---

### 🔵 GET `/api/v1/gates/{gate_id}/approvals`

**Summary**: Get Gate Approvals

<details>
<summary>View full description</summary>

Get gate approval history.

Path Parameters:
    - gate_id: Gate UUID

Response (200 OK):
    [
        {
            "id": "...",
            "approved_by": "...",
            "approved_by_name": "Hoàng Văn Em (CTO)",
            "approved_by_role": "CTO",
            "is_approved": true,
            "comments": "...",
            "approved_at": "2025-11-28T10:30:00Z"
        }
    ]

Errors:
    - 401 Unauthorized: Invalid token
    - 403 Forbidden: User not project member
    - 404 Not Found: Gate not found

Flow:
    1. Fetch gate by ID
    2. Verify user is project member
    3. Fetch approval records with approver details
    4. Return approval list

</details>

---

### 🔵 GET `/api/v1/gates/{gate_id}/approvals`

**Summary**: Get Gate Approvals

<details>
<summary>View full description</summary>

Get gate approval history.

Path Parameters:
    - gate_id: Gate UUID

Response (200 OK):
    [
        {
            "id": "...",
            "approved_by": "...",
            "approved_by_name": "Hoàng Văn Em (CTO)",
            "approved_by_role": "CTO",
            "is_approved": true,
            "comments": "...",
            "approved_at": "2025-11-28T10:30:00Z"
        }
    ]

Errors:
    - 401 Unauthorized: Invalid token
    - 403 Forbidden: User not project member
    - 404 Not Found: Gate not found

Flow:
    1. Fetch gate by ID
    2. Verify user is project member
    3. Fetch approval records with approver details
    4. Return approval list

</details>

---

### 🟢 POST `/api/v1/gates/{gate_id}/approve`

**Summary**: Approve Gate

<details>
<summary>View full description</summary>

Approve or reject gate (CTO, CPO, CEO only).

Path Parameters:
    - gate_id: Gate UUID

Request Body:
    {
        "approved": true,
        "comments": "All exit criteria validated. Approved for production."
    }

Response (200 OK):
    {
        "id": "...",
        "status": "APPROVED",
        "approved_at": "2025-11-28T10:30:00Z",
        ...
    }

Errors:
    - 401 Unauthorized: Invalid token
    - 403 Forbidden: User not CTO/CPO/CEO or gate not pending approval
    - 404 Not Found: Gate not found

Flow:
    1. Fetch gate by ID
    2. Verify user is CTO/CPO/CEO (require_roles dependency)
    3. Verify gate status is PENDING_APPROVAL
    4. Create approval record
    5. If approved: Change status → APPROVED, set approved_at

*(truncated for brevity)*

</details>

---

### 🟢 POST `/api/v1/gates/{gate_id}/approve`

**Summary**: Approve Gate

<details>
<summary>View full description</summary>

Approve or reject gate (CTO, CPO, CEO only).

Path Parameters:
    - gate_id: Gate UUID

Request Body:
    {
        "approved": true,
        "comments": "All exit criteria validated. Approved for production."
    }

Response (200 OK):
    {
        "id": "...",
        "status": "APPROVED",
        "approved_at": "2025-11-28T10:30:00Z",
        ...
    }

Errors:
    - 401 Unauthorized: Invalid token
    - 403 Forbidden: User not CTO/CPO/CEO or gate not pending approval
    - 404 Not Found: Gate not found

Flow:
    1. Fetch gate by ID
    2. Verify user is CTO/CPO/CEO (require_roles dependency)
    3. Verify gate status is PENDING_APPROVAL
    4. Create approval record
    5. If approved: Change status → APPROVED, set approved_at

*(truncated for brevity)*

</details>

---

### 🟢 POST `/api/v1/gates/{gate_id}/submit`

**Summary**: Submit Gate

<details>
<summary>View full description</summary>

Submit gate for approval (CTO/CPO/CEO review).

Path Parameters:
    - gate_id: Gate UUID

Request Body:
    {
        "message": "Submitting G2 for approval. All exit criteria met."
    }

Response (200 OK):
    {
        "id": "...",
        "status": "PENDING_APPROVAL",
        ...
    }

Errors:
    - 401 Unauthorized: Invalid token
    - 403 Forbidden: User not project member or gate already submitted
    - 404 Not Found: Gate not found

Flow:
    1. Fetch gate by ID
    2. Verify user is project member
    3. Verify gate status is DRAFT
    4. Change status: DRAFT → PENDING_APPROVAL
    5. Trigger policy evaluation (OPA) - TODO
    6. Send notifications to CTO/CPO/CEO - TODO
    7. Return updated gate

</details>

---

### 🟢 POST `/api/v1/gates/{gate_id}/submit`

**Summary**: Submit Gate

<details>
<summary>View full description</summary>

Submit gate for approval (CTO/CPO/CEO review).

Path Parameters:
    - gate_id: Gate UUID

Request Body:
    {
        "message": "Submitting G2 for approval. All exit criteria met."
    }

Response (200 OK):
    {
        "id": "...",
        "status": "PENDING_APPROVAL",
        ...
    }

Errors:
    - 401 Unauthorized: Invalid token
    - 403 Forbidden: User not project member or gate already submitted
    - 404 Not Found: Gate not found

Flow:
    1. Fetch gate by ID
    2. Verify user is project member
    3. Verify gate status is DRAFT
    4. Change status: DRAFT → PENDING_APPROVAL
    5. Trigger policy evaluation (OPA) - TODO
    6. Send notifications to CTO/CPO/CEO - TODO
    7. Return updated gate

</details>

---

## Gates Engine

### 🟢 POST `/api/v1/gates-engine/bulk-evaluate`

**Summary**: Evaluate multiple gates

**Description**: Evaluate multiple gates for a project.

    If gate_codes is empty, evaluates all gates in order.
    With stop_on_failure=true, stops at first failed gate.

---

### 🟢 POST `/api/v1/gates-engine/bulk-evaluate`

**Summary**: Evaluate multiple gates

**Description**: Evaluate multiple gates for a project.

    If gate_codes is empty, evaluates all gates in order.
    With stop_on_failure=true, stops at first failed gate.

---

### 🟢 POST `/api/v1/gates-engine/evaluate-by-code`

**Summary**: Evaluate gate by project and code

**Description**: Evaluate a gate by project ID and gate code (G0.1, G0.2, G1...G9).

---

### 🟢 POST `/api/v1/gates-engine/evaluate-by-code`

**Summary**: Evaluate gate by project and code

**Description**: Evaluate a gate by project ID and gate code (G0.1, G0.2, G1...G9).

---

### 🟢 POST `/api/v1/gates-engine/evaluate/{gate_id}`

**Summary**: Evaluate single gate

<details>
<summary>View full description</summary>

Evaluate a gate for readiness to pass.

    **Evaluation Phases:**
    1. Prerequisites: Check prerequisite gates are approved
    2. Exit Criteria: Verify all exit criteria are met
    3. Policy Evaluation: Run OPA policies for gate
    4. Context Check: Validate context using CA V2
    5. Approval Check: Verify required approvals

    **Readiness Score:**
    - Phase completion: 40%
    - Exit criteria: 40%
    - Vibecoding index: 20%

    Returns detailed evaluation result with recommendations.

</details>

---

### 🟢 POST `/api/v1/gates-engine/evaluate/{gate_id}`

**Summary**: Evaluate single gate

<details>
<summary>View full description</summary>

Evaluate a gate for readiness to pass.

    **Evaluation Phases:**
    1. Prerequisites: Check prerequisite gates are approved
    2. Exit Criteria: Verify all exit criteria are met
    3. Policy Evaluation: Run OPA policies for gate
    4. Context Check: Validate context using CA V2
    5. Approval Check: Verify required approvals

    **Readiness Score:**
    - Phase completion: 40%
    - Exit criteria: 40%
    - Vibecoding index: 20%

    Returns detailed evaluation result with recommendations.

</details>

---

### 🔵 GET `/api/v1/gates-engine/health`

**Summary**: Gates engine health check


---

### 🔵 GET `/api/v1/gates-engine/health`

**Summary**: Gates engine health check


---

### 🔵 GET `/api/v1/gates-engine/policies/{gate_code}`

**Summary**: Get policies for gate

**Description**: Get the list of OPA policies configured for a gate.

---

### 🔵 GET `/api/v1/gates-engine/policies/{gate_code}`

**Summary**: Get policies for gate

**Description**: Get the list of OPA policies configured for a gate.

---

### 🔵 GET `/api/v1/gates-engine/prerequisites/{gate_code}`

**Summary**: Check gate prerequisites

**Description**: Check which prerequisite gates must be passed before a target gate.

---

### 🔵 GET `/api/v1/gates-engine/prerequisites/{gate_code}`

**Summary**: Check gate prerequisites

**Description**: Check which prerequisite gates must be passed before a target gate.

---

### 🔵 GET `/api/v1/gates-engine/readiness/{project_id}`

**Summary**: Get project gate readiness


---

### 🔵 GET `/api/v1/gates-engine/readiness/{project_id}`

**Summary**: Get project gate readiness


---

### 🔵 GET `/api/v1/gates-engine/stages`

**Summary**: Get gate-to-stage mapping


---

### 🔵 GET `/api/v1/gates-engine/stages`

**Summary**: Get gate-to-stage mapping


---

## GitHub

### 🔵 GET `/api/v1/github/installations`

**Summary**: List user's GitHub installations

<details>
<summary>View full description</summary>

List all active GitHub App installations for the current user.

    Returns installations where the user installed the GitHub App.
    Each installation provides access to repositories in that user/org.

    **Note**: To get repositories for an installation, use
    GET /github/installations/{installation_id}/repositories

</details>

---

### 🔵 GET `/api/v1/github/installations/{installation_id}/repositories`

**Summary**: List repositories for installation

<details>
<summary>View full description</summary>

List repositories accessible to a GitHub App installation.

    Requires the installation to be owned by the current user.
    Results are paginated (default: 100 per page, max: 100).

    **Note**: This fetches fresh data from GitHub API, not cached.

</details>

---

### 🟢 POST `/api/v1/github/projects/{project_id}/clone`

**Summary**: Clone linked repository

<details>
<summary>View full description</summary>

Clone the linked GitHub repository to local storage.

    Uses shallow clone (--depth=1) by default for faster cloning.
    After clone, use GET /projects/{project_id}/scan for gap analysis.

    **Clone Status Flow**:
    pending → cloning → cloned (or failed)

</details>

---

### 🟢 POST `/api/v1/github/projects/{project_id}/link`

**Summary**: Link GitHub repository to project

<details>
<summary>View full description</summary>

Link a GitHub repository to an SDLC Orchestrator project.

    **Rules**:
    - One project can only be linked to one repository
    - One repository can only be linked to one project
    - User must own the installation

    **After linking**:
    - Use POST /projects/{project_id}/clone to clone the repository
    - Use GET /projects/{project_id}/scan to scan the cloned repository

</details>

---

### 🔵 GET `/api/v1/github/projects/{project_id}/repository`

**Summary**: Get linked repository for project


---

### 🔵 GET `/api/v1/github/projects/{project_id}/scan`

**Summary**: Scan cloned repository

**Description**: Scan the cloned repository structure for gap analysis.

    Returns folder/file structure to determine SDLC compliance.
    Repository must be cloned first (clone_status = 'cloned').

---

### 🔴 DELETE `/api/v1/github/projects/{project_id}/unlink`

**Summary**: Unlink GitHub repository from project

**Description**: Unlink a GitHub repository from a project.

    This does NOT delete the repository from GitHub.
    The local clone is also preserved (can be deleted manually).

---

### 🟢 POST `/api/v1/github/webhooks`

**Summary**: GitHub webhook handler

<details>
<summary>View full description</summary>

Handle GitHub webhook events (Sprint 129.5).

    **Supported Events**:
    - installation: App install/uninstall/suspend/unsuspend
    - push: Code pushed → triggers gap analysis
    - pull_request: PR opened/sync/closed → triggers gate evaluation
    - ping: Webhook configuration test

    **Security**:
    - Webhook signature validation (HMAC-SHA256)
    - X-Hub-Signature-256 header required
    - Idempotency via X-GitHub-Delivery header

    **Processing**:
    - Webhook returns 202 Accepted immediately
    - Actual processing happens in background job
    - Use X-GitHub-Delivery to track status

</details>

---

### 🔵 GET `/api/v1/github/webhooks/dlq`

**Summary**: Get dead letter queue jobs

<details>
<summary>View full description</summary>

Get jobs in the dead letter queue (failed after max retries).

    **Dead Letter Queue (DLQ)**:
    - Contains jobs that failed after 3 retry attempts
    - Jobs can be manually retried via POST /webhooks/dlq/{job_id}/retry
    - Monitor DLQ size for potential issues

    **Access**: Requires admin authentication

</details>

---

### 🟢 POST `/api/v1/github/webhooks/dlq/{job_id}/retry`

**Summary**: Retry a dead letter queue job

<details>
<summary>View full description</summary>

Retry a job from the dead letter queue.

    **Retry Behavior**:
    - Moves job from DLQ back to main queue
    - Resets retry count to 0
    - Job will be processed with next batch

    **Access**: Requires admin authentication

</details>

---

### 🔵 GET `/api/v1/github/webhooks/jobs/{job_id}`

**Summary**: Get webhook job status

<details>
<summary>View full description</summary>

Get status of a specific webhook job.

    **Job Status**:
    - queued: Waiting to be processed
    - processing: Currently being processed
    - completed: Successfully processed
    - retrying: Failed, queued for retry
    - failed: Failed after max retries (in DLQ)

    **Access**: Requires authentication

</details>

---

### 🟢 POST `/api/v1/github/webhooks/process`

**Summary**: Trigger webhook job processing

<details>
<summary>View full description</summary>

Manually trigger processing of queued webhook jobs.

    **Processing Behavior**:
    - Processes up to `max_jobs` queued webhooks
    - Returns processing summary
    - Should be called by scheduler or admin

    **Access**: Requires admin authentication

</details>

---

### 🔵 GET `/api/v1/github/webhooks/stats`

**Summary**: Get webhook job queue statistics

<details>
<summary>View full description</summary>

Get statistics about webhook job queues.

    **Statistics Include**:
    - Queue length (pending jobs)
    - Dead letter queue (DLQ) length
    - Jobs by status (queued, processing, completed, failed)
    - Total jobs tracked

    **Access**: Requires admin authentication

</details>

---

## Governance Metrics

### 🔵 GET `/api/v1/governance-metrics`

**Summary**: Get Prometheus metrics

<details>
<summary>View full description</summary>

Get all governance metrics in Prometheus text exposition format.

    **Metric Categories (45 total):**
    1. Governance System (15 metrics)
    2. Performance (10 metrics)
    3. Business / CEO Dashboard (8 metrics)
    4. Developer Experience (7 metrics)
    5. System Health (5 metrics)

    **Response Format:**
    ```
    # HELP governance_submissions_total Total number of governance submissions
    # TYPE governance_submissions_total counter
    governance_submissions_total{project_id="proj-123",status="passed"} 150
    ```

    Use with Prometheus scrape config:
    ```yaml
    scrape_configs:
      - job_name: 'sdlc-orchestrator'
        static_configs:
          - targets: ['localhost:8000']
        metrics_path: '/api/v1/governance-metrics'
    ```

</details>

---

### 🔵 GET `/api/v1/governance-metrics/definitions`

**Summary**: Get metric definitions

**Description**: Get all metric definitions with descriptions and types.

    Useful for documentation and understanding available metrics.

---

### 🔵 GET `/api/v1/governance-metrics/health`

**Summary**: Metrics service health check


---

### 🔵 GET `/api/v1/governance-metrics/json`

**Summary**: Get metrics in JSON format

<details>
<summary>View full description</summary>

Get all governance metrics in JSON format.

    **Structure:**
    ```json
    {
      "counters": {"metric_name": {"labels": value}},
      "gauges": {"metric_name": {"labels": value}},
      "histograms": {"metric_name": {"labels": {stats}}},
      "timestamp": "2026-01-27T...",
      "total_metrics": 45
    }
    ```

    Useful for:
    - Custom dashboards
    - API integrations
    - Debugging

</details>

---

### 🟢 POST `/api/v1/governance-metrics/record-break-glass`

**Summary**: Record break glass activation

<details>
<summary>View full description</summary>

Record break glass activation.

    **Severities:**
    - P0: Production critical (justified)
    - P1: High priority (justified)
    - abuse: Unjustified use

    **Metrics Updated:**
    - governance_break_glass_total

</details>

---

### 🟢 POST `/api/v1/governance-metrics/record-bypass`

**Summary**: Record governance bypass incident

<details>
<summary>View full description</summary>

Record governance bypass incident.

    **Bypass Types:**
    - pre_commit_skip: Skipped pre-commit hook
    - direct_push: Direct push to protected branch
    - break_glass_abuse: Abuse of break glass

    **Target:** 0 incidents

    **Metrics Updated:**
    - governance_bypass_incidents_total

</details>

---

### 🟢 POST `/api/v1/governance-metrics/record-ceo-override`

**Summary**: Record CEO override

<details>
<summary>View full description</summary>

Record a CEO override for calibration tracking.

    **Override Types:**
    - agrees: CEO confirms the routing was correct
    - disagrees: CEO disagrees (false positive/negative)

    **Metrics Updated:**
    - governance_ceo_overrides_total

</details>

---

### 🟢 POST `/api/v1/governance-metrics/record-developer-friction`

**Summary**: Record developer friction

<details>
<summary>View full description</summary>

Record developer friction (time to pass governance).

    **Target:** <5 minutes (P95)

    **Metrics Updated:**
    - developer_friction_minutes

</details>

---

### 🟢 POST `/api/v1/governance-metrics/record-evidence`

**Summary**: Record evidence upload

**Description**: Record an evidence upload.

    **Metrics Updated:**
    - evidence_vault_uploads_total
    - evidence_vault_size_bytes

---

### 🟢 POST `/api/v1/governance-metrics/record-llm`

**Summary**: Record LLM generation metrics

<details>
<summary>View full description</summary>

Record LLM generation metrics.

    **Metrics Updated:**
    - llm_generation_duration_seconds
    - llm_generation_success_rate
    - llm_fallback_triggered_total (if fallback)

</details>

---

### 🟢 POST `/api/v1/governance-metrics/record-submission`

**Summary**: Record governance submission metrics

<details>
<summary>View full description</summary>

Record a governance submission with all related metrics.

    **Metrics Updated:**
    - governance_submissions_total
    - governance_submissions_duration_seconds
    - governance_vibecoding_index
    - governance_routing_total
    - governance_rejections_total (if rejected)
    - governance_signals_* (if signal_breakdown provided)
    - governance_critical_override_total (if critical override)
    - governance_escalations_total (if Orange/Red)

</details>

---

### 🟢 POST `/api/v1/governance-metrics/set-kill-switch`

**Summary**: Set kill switch status

<details>
<summary>View full description</summary>

Set kill switch status gauge.

    **Statuses:**
    - OFF: No enforcement (0)
    - WARNING: Log only (1)
    - SOFT: Block critical (2)
    - FULL: Block all (3)

    **Metrics Updated:**
    - kill_switch_status

</details>

---

### 🟢 POST `/api/v1/governance-metrics/update-ceo-metrics`

**Summary**: Update CEO dashboard metrics

<details>
<summary>View full description</summary>

Update CEO dashboard metrics.

    **Metrics Updated:**
    - ceo_time_saved_hours
    - ceo_pr_review_reduction_percent
    - governance_without_ceo_percent
    - governance_false_positive_rate

</details>

---

### 🟢 POST `/api/v1/governance-metrics/update-system-health`

**Summary**: Update system health metrics

<details>
<summary>View full description</summary>

Update system health gauges.

    **Metrics Updated:**
    - system_uptime_seconds
    - system_cpu_usage_percent
    - system_memory_usage_percent

</details>

---

## Governance Mode

### 🔵 GET `/api/v1/governance/dogfooding/status`

**Summary**: Get dogfooding status

**Description**: Get status of governance dogfooding on SDLC Orchestrator repo.

---

### 🟢 POST `/api/v1/governance/false-positive`

**Summary**: Report false positive

<details>
<summary>View full description</summary>

Report a false positive (incorrectly blocked submission).

    This data is used to:
    - Track false positive rate
    - Calibrate governance rules
    - Trigger auto-rollback if rate exceeds threshold

</details>

---

### 🔵 GET `/api/v1/governance/health`

**Summary**: Governance service health check


---

### 🟢 POST `/api/v1/governance/kill-switch`

**Summary**: Emergency kill switch

<details>
<summary>View full description</summary>

**EMERGENCY ONLY**: Immediately rollback governance to WARNING mode.

    Use this when:
    - Governance is blocking critical production deployments
    - False positive rate is too high
    - System is causing more harm than good

    **Authorization Required**: CTO or CEO role

    **Actions triggered**:
    1. Mode immediately set to WARNING
    2. All stakeholders notified (CEO, CTO, Tech Lead)
    3. Incident logged for post-mortem
    4. Post-incident review required within 24 hours

</details>

---

### 🔵 GET `/api/v1/governance/metrics`

**Summary**: Get governance metrics

**Description**: Get governance enforcement metrics for monitoring and calibration.

---

### 🔵 GET `/api/v1/governance/mode`

**Summary**: Get current governance mode

<details>
<summary>View full description</summary>

Get the current governance enforcement mode.

    Modes:
    - `off`: No enforcement (development mode)
    - `warning`: Log violations, don't block (observability mode)
    - `soft`: Block critical violations, warn on others
    - `full`: Block all violations (production mode)

</details>

---

### 🟡 PUT `/api/v1/governance/mode`

**Summary**: Set governance mode

<details>
<summary>View full description</summary>

Set the governance enforcement mode.

    **Authorization Required**: Admin or CTO role

    Mode progression:
    - Recommended: `off` → `warning` → `soft` → `full`
    - Rollback: Any mode can rollback to `warning` for safety

    **Warning**: Setting to `full` mode will block all non-compliant PRs.

</details>

---

### 🔵 GET `/api/v1/governance/mode/state`

**Summary**: Get full governance mode state

**Description**: Get full governance mode state including metrics for calibration.

---

## Governance Specs

### 🔵 GET `/api/v1/governance/specs/health`

**Summary**: Specification service health check


---

### 🟢 POST `/api/v1/governance/specs/validate`

**Summary**: Validate YAML Frontmatter

<details>
<summary>View full description</summary>

Validate YAML frontmatter against SPEC-0002 Specification Standard.

    **Mandatory Fields:**
    - authors (list of strings)

    **Recommended Fields:**
    - spec_version, status, tier, stage, owner
    - reviewers, stakeholders
    - created, last_updated
    - related_adrs

    **Validation Rules:**
    - YAML must be valid and parseable
    - Required fields must be present
    - Tier must be one of: LITE, STANDARD, PROFESSIONAL, ENTERPRISE
    - Stage must be valid SDLC stage (00-10)
    - Status must be one of: draft, review, approved, deprecated

</details>

---

### 🔵 GET `/api/v1/governance/specs/{spec_id}`

**Summary**: Get Specification Metadata

<details>
<summary>View full description</summary>

Retrieve specification metadata by ID.

    Returns:
    - Spec metadata (number, title, status, tier, stage)
    - Version history
    - Frontmatter metadata

</details>

---

### 🔵 GET `/api/v1/governance/specs/{spec_id}/acceptance-criteria`

**Summary**: List Acceptance Criteria

<details>
<summary>View full description</summary>

List all acceptance criteria for a specification.

    Criteria include:
    - Criterion ID (e.g., AC-001)
    - Description
    - Verification method (automated, manual, hybrid)
    - Tier applicability
    - Automation status and tool

</details>

---

### 🔵 GET `/api/v1/governance/specs/{spec_id}/requirements`

**Summary**: List Functional Requirements

<details>
<summary>View full description</summary>

List all functional requirements for a specification.

    Requirements include:
    - Requirement ID (e.g., FR-001)
    - Title and description
    - Priority (MUST, SHOULD, MAY, COULD)
    - Tier applicability
    - BDD format (GIVEN-WHEN-THEN)

</details>

---

## Governance Vibecoding

### 🟢 POST `/api/v1/governance/vibecoding/calculate`

**Summary**: Calculate Vibecoding Index (Database-Backed)

<details>
<summary>View full description</summary>

Calculate and store Vibecoding Index for a code submission.

    **5-Signal Formula (SPEC-0001):**
    - **Intent Clarity** (30%): How well documented is the "why"?
    - **Code Ownership** (25%): Is ownership clearly declared?
    - **Context Completeness** (20%): Are ADRs and context linked?
    - **AI Attestation** (15%): Is AI usage attested?
    - **Historical Rejection Rate** (10%): Past rejection history

    **Index Calculation:**
    index = 100 - (intent*0.30 + ownership*0.25 + context*0.20 + ai*0.15 + rejection*0.10)

    **Zone Routing (Progressive):**
    - GREEN (0-20): AUTO_MERGE
    - YELLOW (20-40): HUMAN_REVIEW
    - ORANGE (40-60): SENIOR_REVIEW
    - RED (60-100): BLOCK

    Results are stored in database for historical analysis.

</details>

---

### 🔵 GET `/api/v1/governance/vibecoding/health`

**Summary**: Vibecoding service health check


---

### 🟢 POST `/api/v1/governance/vibecoding/kill-switch/check`

**Summary**: Check Kill Switch Triggers

<details>
<summary>View full description</summary>

Check if any kill switch triggers are active for a project.

    **Kill Switch Triggers (SPEC-0001):**
    1. **Rejection Rate >80%** (30min window) - Governance too strict
    2. **API Latency >500ms** (15min window) - Performance degradation
    3. **Critical CVEs >=5** (immediate) - Security emergency

    If triggered, returns recommended action (WARNING or FULL rollback).

</details>

---

### 🟢 POST `/api/v1/governance/vibecoding/route`

**Summary**: Progressive Routing Decision

<details>
<summary>View full description</summary>

Get routing decision for a given index score.

    **Routing Rules:**
    - GREEN (0-20): AUTO_MERGE - No human review needed
    - YELLOW (20-40): HUMAN_REVIEW - Team lead review
    - ORANGE (40-60): SENIOR_REVIEW - Senior engineer review
    - RED (60-100): BLOCK - Requires remediation

    Returns routing action with SLA and escalation path.

</details>

---

### 🔵 GET `/api/v1/governance/vibecoding/signals/{submission_id}`

**Summary**: Get Signal Breakdown

<details>
<summary>View full description</summary>

Get detailed breakdown of 5 signals for a submission.

    Returns each signal with:
    - Signal type and value
    - Weight in formula
    - Weighted contribution to final score

</details>

---

### 🔵 GET `/api/v1/governance/vibecoding/stats/{project_id}`

**Summary**: Get Zone Statistics

<details>
<summary>View full description</summary>

Get aggregate zone statistics for a project.

    Returns:
    - Zone distribution (count per zone)
    - Zone percentages
    - Average index score
    - Trend analysis (improving/stable/degrading)

</details>

---

### 🔵 GET `/api/v1/governance/vibecoding/{submission_id}`

**Summary**: Get Index History

**Description**: Get historical Vibecoding Index calculations for a submission.

    Returns all index calculations with signals breakdown,
    sorted by calculation time (most recent first).

---

## Grafana Dashboards

### 🔵 GET `/api/v1/grafana-dashboards`

**Summary**: List all Grafana dashboards

**Description**: Get metadata for all available Grafana dashboard configurations.

---

### 🔵 GET `/api/v1/grafana-dashboards/datasource/template`

**Summary**: Get Prometheus datasource template

**Description**: Get Prometheus datasource configuration template for Grafana.

---

### 🔵 GET `/api/v1/grafana-dashboards/export/all`

**Summary**: Export all dashboards

**Description**: Export all dashboard configurations as a single JSON array.

---

### 🟢 POST `/api/v1/grafana-dashboards/provision`

**Summary**: Provision dashboards to Grafana

**Description**: Provision all dashboard configurations to a Grafana instance via API.

---

### 🔵 GET `/api/v1/grafana-dashboards/{dashboard_type}`

**Summary**: Get dashboard configuration

**Description**: Get complete Grafana dashboard configuration in JSON format.

---

### 🔵 GET `/api/v1/grafana-dashboards/{dashboard_type}/json`

**Summary**: Download dashboard JSON

**Description**: Download dashboard configuration as a JSON file for Grafana import.

---

### 🔵 GET `/api/v1/grafana-dashboards/{dashboard_type}/panels`

**Summary**: List dashboard panels

**Description**: Get metadata for all panels in a specific dashboard.

---

## MRP - Merge Readiness Protocol

### 🔵 GET `/api/v1/mrp/health`

**Summary**: Health check


---

### 🔵 GET `/api/v1/mrp/health`

**Summary**: Health check


---

### 🟢 POST `/api/v1/mrp/policies/compare`

**Summary**: Compare two tiers

**Description**: Compare requirements between two tiers for upgrade/downgrade planning.

---

### 🟢 POST `/api/v1/mrp/policies/compare`

**Summary**: Compare two tiers

**Description**: Compare requirements between two tiers for upgrade/downgrade planning.

---

### 🔵 GET `/api/v1/mrp/policies/compliance/{project_id}`

**Summary**: Get tier compliance report


---

### 🔵 GET `/api/v1/mrp/policies/compliance/{project_id}`

**Summary**: Get tier compliance report


---

### 🟢 POST `/api/v1/mrp/policies/enforce`

**Summary**: Enforce policies for PR

<details>
<summary>View full description</summary>

Enforce 4-tier policies for a PR.

    This endpoint:
    1. Gets project's policy tier
    2. Runs MRP 5-point validation
    3. Generates VCR
    4. Determines enforcement action
    5. (Optionally) Updates GitHub check

    **Enforcement Modes**:
    - LITE: Advisory only, never blocks
    - STANDARD: Soft enforcement, warnings only
    - PROFESSIONAL: Hard enforcement, blocks on failure
    - ENTERPRISE: Strictest, zero tolerance

    Performance: <30s (p95)

</details>

---

### 🟢 POST `/api/v1/mrp/policies/enforce`

**Summary**: Enforce policies for PR

<details>
<summary>View full description</summary>

Enforce 4-tier policies for a PR.

    This endpoint:
    1. Gets project's policy tier
    2. Runs MRP 5-point validation
    3. Generates VCR
    4. Determines enforcement action
    5. (Optionally) Updates GitHub check

    **Enforcement Modes**:
    - LITE: Advisory only, never blocks
    - STANDARD: Soft enforcement, warnings only
    - PROFESSIONAL: Hard enforcement, blocks on failure
    - ENTERPRISE: Strictest, zero tolerance

    Performance: <30s (p95)

</details>

---

### 🔵 GET `/api/v1/mrp/policies/tiers`

**Summary**: Get all policy tiers

**Description**: Retrieve all available policy tiers with their requirements.

---

### 🔵 GET `/api/v1/mrp/policies/tiers`

**Summary**: Get all policy tiers

**Description**: Retrieve all available policy tiers with their requirements.

---

### 🟢 POST `/api/v1/mrp/validate`

**Summary**: Validate MRP 5-point structure

<details>
<summary>View full description</summary>

Validate MRP (Merge Readiness Protocol) 5-point evidence structure for a PR.

    The 5 MRP points:
    1. **Test Evidence**: Unit/integration test results and coverage
    2. **Lint Evidence**: ruff/eslint zero errors
    3. **Security Evidence**: bandit/grype vulnerability scan
    4. **Build Evidence**: Docker/package build success
    5. **Conformance Evidence**: Pattern alignment and ADR check

    Validation is performed against the project's policy tier.

    Performance: <30s (p95)

</details>

---

### 🟢 POST `/api/v1/mrp/validate`

**Summary**: Validate MRP 5-point structure

<details>
<summary>View full description</summary>

Validate MRP (Merge Readiness Protocol) 5-point evidence structure for a PR.

    The 5 MRP points:
    1. **Test Evidence**: Unit/integration test results and coverage
    2. **Lint Evidence**: ruff/eslint zero errors
    3. **Security Evidence**: bandit/grype vulnerability scan
    4. **Build Evidence**: Docker/package build success
    5. **Conformance Evidence**: Pattern alignment and ADR check

    Validation is performed against the project's policy tier.

    Performance: <30s (p95)

</details>

---

### 🔵 GET `/api/v1/mrp/validate/{project_id}/{pr_id}`

**Summary**: Get latest MRP validation


---

### 🔵 GET `/api/v1/mrp/validate/{project_id}/{pr_id}`

**Summary**: Get latest MRP validation


---

### 🔵 GET `/api/v1/mrp/vcr/{project_id}/history`

**Summary**: Get VCR history


---

### 🔵 GET `/api/v1/mrp/vcr/{project_id}/history`

**Summary**: Get VCR history


---

### 🔵 GET `/api/v1/mrp/vcr/{project_id}/{pr_id}`

**Summary**: Get latest VCR

**Description**: Retrieve the latest VCR (Verification Completion Report) for a PR.

---

### 🔵 GET `/api/v1/mrp/vcr/{project_id}/{pr_id}`

**Summary**: Get latest VCR

**Description**: Retrieve the latest VCR (Verification Completion Report) for a PR.

---

## MRP - Policy Enforcement

### 🟢 POST `/api/v1/mrp/policies/compare`

**Summary**: Compare two tiers

**Description**: Compare requirements between two tiers for upgrade/downgrade planning.

---

### 🔵 GET `/api/v1/mrp/policies/compliance/{project_id}`

**Summary**: Get tier compliance report


---

### 🟢 POST `/api/v1/mrp/policies/enforce`

**Summary**: Enforce policies for PR

<details>
<summary>View full description</summary>

Enforce 4-tier policies for a PR.

    This endpoint:
    1. Gets project's policy tier
    2. Runs MRP 5-point validation
    3. Generates VCR
    4. Determines enforcement action
    5. (Optionally) Updates GitHub check

    **Enforcement Modes**:
    - LITE: Advisory only, never blocks
    - STANDARD: Soft enforcement, warnings only
    - PROFESSIONAL: Hard enforcement, blocks on failure
    - ENTERPRISE: Strictest, zero tolerance

    Performance: <30s (p95)

</details>

---

### 🔵 GET `/api/v1/mrp/policies/tiers`

**Summary**: Get all policy tiers

**Description**: Retrieve all available policy tiers with their requirements.

---

## Notifications

### 🔵 GET `/api/v1/notifications`

**Summary**: List Notifications

<details>
<summary>View full description</summary>

List user's notifications with pagination and filters.

Args:
    page: Page number (1-indexed)
    page_size: Number of items per page
    unread_only: Only return unread notifications
    notification_type: Filter by notification type
    project_id: Filter by project ID

Returns:
    Paginated list of notifications with metadata

</details>

---

### 🟡 PUT `/api/v1/notifications/read-all`

**Summary**: Mark All Notifications Read

<details>
<summary>View full description</summary>

Mark all unread notifications as read.

Args:
    project_id: Optional project ID to filter

Returns:
    Number of notifications updated

</details>

---

### 🔵 GET `/api/v1/notifications/settings/preferences`

**Summary**: Get Notification Settings

**Description**: Get user's notification preferences.

Returns:
    Current notification settings

---

### 🟡 PUT `/api/v1/notifications/settings/preferences`

**Summary**: Update Notification Settings

<details>
<summary>View full description</summary>

Update user's notification preferences.

Args:
    settings: New notification settings

Returns:
    Updated notification settings

</details>

---

### 🔵 GET `/api/v1/notifications/stats/summary`

**Summary**: Get Notification Stats

**Description**: Get notification statistics for the user.

Returns:
    Notification counts by type and read status

---

### 🔵 GET `/api/v1/notifications/{notification_id}`

**Summary**: Get Notification

<details>
<summary>View full description</summary>

Get a single notification by ID.

Args:
    notification_id: UUID of the notification

Returns:
    Notification details

Raises:
    404: Notification not found

</details>

---

### 🔴 DELETE `/api/v1/notifications/{notification_id}`

**Summary**: Delete Notification

<details>
<summary>View full description</summary>

Delete a notification.

Args:
    notification_id: UUID of the notification

Raises:
    404: Notification not found

</details>

---

### 🟡 PUT `/api/v1/notifications/{notification_id}/read`

**Summary**: Mark Notification Read

<details>
<summary>View full description</summary>

Mark a single notification as read.

Args:
    notification_id: UUID of the notification

Returns:
    Success status

Raises:
    404: Notification not found

</details>

---

## Organization Invitations

### 🔴 DELETE `/api/v1/org-invitations/{invitation_id}`

**Summary**: Cancel organization invitation

<details>
<summary>View full description</summary>

Cancel pending invitation (admin action).

    **Permissions**:
    - Organization owner/admin only

    **Effect**:
    - Status changed to 'cancelled'
    - Invitation token invalidated

</details>

---

### 🟢 POST `/api/v1/org-invitations/{invitation_id}/resend`

**Summary**: Resend organization invitation email

<details>
<summary>View full description</summary>

Resend invitation email with new token.

    **Security**:
    - Generates NEW token (invalidates old token)
    - Rate limiting: Max 3 resends per invitation
    - Cooldown: 5 minutes between resends

    **Permissions**:
    - Organization owner/admin only

</details>

---

### 🔵 GET `/api/v1/org-invitations/{token}`

**Summary**: Get organization invitation details by token

**Description**: Get invitation details for acceptance page (public endpoint).

    **Security**:
    - No authentication required (token is the credential)
    - Constant-time token verification (prevents timing attacks)

---

### 🟢 POST `/api/v1/org-invitations/{token}/accept`

**Summary**: Accept organization invitation

<details>
<summary>View full description</summary>

Accept invitation and create organization membership.

    **Security**:
    - Requires authentication (user must be logged in)
    - Email verification (user email must match invited email)
    - One-time use (status change prevents replay)

</details>

---

### 🟢 POST `/api/v1/org-invitations/{token}/decline`

**Summary**: Decline organization invitation

**Description**: Decline invitation politely (no membership created).

    **Security**:
    - No authentication required (anonymous decline allowed)
    - One-time use (status change prevents replay)

---

### 🟢 POST `/api/v1/organizations/{organization_id}/invitations`

**Summary**: Send organization invitation

<details>
<summary>View full description</summary>

Send invitation to join organization with secure token.

    **Security**:
    - Rate limiting: 50 invitations/hour per organization
    - Email rate limit: 10 invitations/day per email
    - Token hashing: SHA256 (never store raw)
    - Audit trail: IP address, user agent, timestamp

    **Permissions**:
    - Organization owner: Can invite with admin/member role
    - Organization admin: Can invite members only
    - Note: Cannot invite as 'owner' (CTO constraint)

    **Errors**:
    - 403: User not authorized to invite
    - 404: Organization not found
    - 409: Pending invitation already exists
    - 429: Rate limit exceeded

</details>

---

### 🔵 GET `/api/v1/organizations/{organization_id}/invitations`

**Summary**: List organization invitations

<details>
<summary>View full description</summary>

List all invitations for an organization (pending, accepted, declined).

    **Permissions**:
    - Organization owner/admin only

    **Filters** (query params):
    - status: Filter by status (pending, accepted, declined, expired, cancelled)
    - email: Filter by invited email

    **Pagination**:
    - limit: Max results per page (default: 50)
    - offset: Skip N results (default: 0)

</details>

---

## Organizations

### 🟢 POST `/api/v1/organizations`

**Summary**: Create Organization

**Description**: Create a new organization. The creator is automatically assigned to it.

---

### 🔵 GET `/api/v1/organizations`

**Summary**: List Organizations

**Description**: List organizations. Regular users see only their own organization.

---

### 🔵 GET `/api/v1/organizations/{org_id}`

**Summary**: Get Organization


---

### 🟠 PATCH `/api/v1/organizations/{org_id}`

**Summary**: Update Organization

**Description**: Update organization details. User must be a member.

---

### 🟢 POST `/api/v1/organizations/{org_id}/members`

**Summary**: Add Member Directly

**Description**: Add existing user to organization directly (bypass invitation flow).

---

### 🔵 GET `/api/v1/organizations/{org_id}/stats`

**Summary**: Get Organization Statistics


---

## Override / VCR

### 🔵 GET `/api/v1/admin/override-queue`

**Summary**: Get override approval queue

<details>
<summary>View full description</summary>

Get list of pending override requests for admin approval.

    **Access Control**:
    - Requires ADMIN, MANAGER, or SECURITY role

    **Query Parameters**:
    - project_id: Filter by project (optional)
    - limit: Max pending items (default: 50)

    **Response**:
    - pending: List of pending override requests
    - recent_decisions: Recent approvals/rejections for reference
    - total_pending: Total count of pending requests

</details>

---

### 🔵 GET `/api/v1/admin/override-stats`

**Summary**: Get override statistics

<details>
<summary>View full description</summary>

Get override statistics for dashboard.

    **Access Control**:
    - Requires ADMIN, MANAGER, or SECURITY role

    **Query Parameters**:
    - project_id: Filter by project (optional)
    - days: Number of days to include (default: 30)

</details>

---

### 🔵 GET `/api/v1/overrides/event/{event_id}`

**Summary**: Get overrides for event

**Description**: Get all override requests for a specific AI code event.

---

### 🟢 POST `/api/v1/overrides/request`

**Summary**: Create override request

<details>
<summary>View full description</summary>

Create a new override request for a failed validation event.

    **Request Body**:
    - event_id: ID of the AI code event (must be failed/warning)
    - override_type: Type of override (false_positive, approved_risk, emergency)
    - reason: Detailed justification (min 50 chars)

    **Business Rules**:
    - Event must have failed or warning validation status
    - Only one pending override per event allowed
    - Emergency overrides require post-merge review

    **Response** (201 Created):
    - Created override record with PENDING status

</details>

---

### 🔵 GET `/api/v1/overrides/{override_id}`

**Summary**: Get override details

**Description**: Get detailed information about an override request.

---

### 🟢 POST `/api/v1/overrides/{override_id}/approve`

**Summary**: Approve override

<details>
<summary>View full description</summary>

Approve a pending override request.

    **Access Control**:
    - Requires ADMIN, MANAGER, or SECURITY role

    **Side Effects**:
    - Updates AICodeEvent.validation_result to 'overridden'
    - Creates audit log entry

    **Request Body**:
    - comment: Optional approval comment

</details>

---

### 🟢 POST `/api/v1/overrides/{override_id}/cancel`

**Summary**: Cancel override

**Description**: Cancel a pending override request.

    **Access Control**:
    - Requester can cancel their own request
    - Admins can cancel any request

---

### 🟢 POST `/api/v1/overrides/{override_id}/reject`

**Summary**: Reject override

<details>
<summary>View full description</summary>

Reject a pending override request.

    **Access Control**:
    - Requires ADMIN, MANAGER, or SECURITY role

    **Request Body**:
    - reason: Required rejection reason (min 10 chars)

</details>

---

### 🔵 GET `/api/v1/projects/{project_id}/overrides`

**Summary**: Get project overrides


---

## Payments

### 🔵 GET `/api/v1/payments/subscriptions/me`

**Summary**: Get My Subscription

<details>
<summary>View full description</summary>

Get current user's subscription.

Returns:
    SubscriptionResponse with current subscription details

Raises:
    HTTPException 404: No subscription found

</details>

---

### 🟢 POST `/api/v1/payments/vnpay/create`

**Summary**: Create Vnpay Payment

<details>
<summary>View full description</summary>

Create VNPay payment URL for plan upgrade.

Per Plan v2.2 Section 7.1:
- Generates unique transaction reference
- Creates pending payment record
- Returns VNPay URL for redirect

Args:
    request_body: Plan and billing period
    request: FastAPI request (for IP address)
    db: Database session
    current_user: Authenticated user

Returns:
    VNPayCreateResponse with payment URL

Raises:
    HTTPException 400: Invalid plan
    HTTPException 400: Standard plan not self-service in V1

</details>

---

### 🟢 POST `/api/v1/payments/vnpay/ipn`

**Summary**: Vnpay Ipn Handler

<details>
<summary>View full description</summary>

VNPay IPN webhook handler (server-to-server).

Per Plan v2.2 Section 7.3.3:
- This is the SINGLE SOURCE OF TRUTH for payment state
- Idempotent: Same IPN called N times → Same response, 1 state change
- Terminal states (completed/failed) are immutable
- Subscription activation is ATOMIC with payment completion

VNPay Response Codes:
- 00: Success (Confirmed)
- 01: Order not found
- 02: Already updated (idempotent)
- 97: Invalid signature
- 99: Unknown error

Returns:
    VNPay response format: {"RspCode": "XX", "Message": "..."}

</details>

---

### 🔵 GET `/api/v1/payments/vnpay/return`

**Summary**: Vnpay Return Handler

<details>
<summary>View full description</summary>

VNPay return handler (user-facing redirect).

Per Plan v2.2 Section 7.3.2:
- This endpoint is READ-ONLY
- Does NOT change payment status (that's IPN's job)
- Only verifies signature and returns status

VNPay redirects user here after payment.
Frontend should redirect to /checkout/success or /checkout/failed based on response.

Returns:
    Payment status for frontend display

</details>

---

### 🔵 GET `/api/v1/payments/{vnp_txn_ref}`

**Summary**: Get Payment Status

<details>
<summary>View full description</summary>

Get payment status by transaction reference.

Args:
    vnp_txn_ref: VNPay transaction reference
    db: Database session
    current_user: Authenticated user

Returns:
    PaymentStatusResponse with current status

Raises:
    HTTPException 404: Payment not found
    HTTPException 403: Not authorized to view this payment

</details>

---

## Pilot

### 🟢 POST `/api/v1/pilot/feedback`

**Summary**: Submit satisfaction survey

**Description**: Submit satisfaction survey.

Score is 1-10, with 8+ being the target.

---

### 🟢 POST `/api/v1/pilot/metrics/aggregate`

**Summary**: Trigger daily metrics aggregation

**Description**: Trigger daily metrics aggregation.

Defaults to today if no date provided. Admin only.

---

### 🔵 GET `/api/v1/pilot/metrics/summary`

**Summary**: Get pilot program summary

<details>
<summary>View full description</summary>

Get overall pilot program metrics for CEO dashboard.

Includes:
- Participant progress (target: 10)
- TTFV metrics (target: <30 min)
- Quality gate pass rate (target: 95%+)
- Satisfaction scores (target: 8/10)

</details>

---

### 🔵 GET `/api/v1/pilot/metrics/targets`

**Summary**: Get Sprint 49 targets


---

### 🟢 POST `/api/v1/pilot/participants`

**Summary**: Register as pilot participant

**Description**: Register current user as a pilot participant.

Validates domain if provided and creates participant record.

---

### 🔵 GET `/api/v1/pilot/participants`

**Summary**: List pilot participants

**Description**: List pilot participants.

Requires admin role for full access.

---

### 🔵 GET `/api/v1/pilot/participants/me`

**Summary**: Get current user's participant profile


---

### 🔵 GET `/api/v1/pilot/participants/{participant_id}`

**Summary**: Get participant by ID


---

### 🟢 POST `/api/v1/pilot/sessions`

**Summary**: Start pilot session (TTFV timer begins)

**Description**: Start a new pilot session.

This marks the beginning of the TTFV timer.

---

### 🔵 GET `/api/v1/pilot/sessions`

**Summary**: Get my sessions


---

### 🔵 GET `/api/v1/pilot/sessions/{session_id}`

**Summary**: Get session details


---

### 🟢 POST `/api/v1/pilot/sessions/{session_id}/generation`

**Summary**: Record generation results

**Description**: Record code generation results for a session.

If quality_gate_passed is True, TTFV will be calculated.

---

### 🟠 PATCH `/api/v1/pilot/sessions/{session_id}/stage`

**Summary**: Update session stage

**Description**: Update session to a new stage.

Valid stages: started, domain_selected, app_named, features_selected,
scale_selected, blueprint_generated, code_generating, code_generated,
quality_gate_passed, deployed, completed

---

## Planning

### 🟢 POST `/api/v1/planning/action-items/bulk/status`

**Summary**: Bulk update action item status


---

### 🔵 GET `/api/v1/planning/action-items/{item_id}`

**Summary**: Get a single action item


---

### 🟡 PUT `/api/v1/planning/action-items/{item_id}`

**Summary**: Update an action item

<details>
<summary>View full description</summary>

Update an action item.

Status transitions:
- open -> in_progress (when assigned)
- in_progress -> completed (manual)
- Any -> cancelled (manual)

</details>

---

### 🔴 DELETE `/api/v1/planning/action-items/{item_id}`

**Summary**: Delete an action item


---

### 🟢 POST `/api/v1/planning/allocations`

**Summary**: Create resource allocation

<details>
<summary>View full description</summary>

Allocate a team member to a sprint.

**Sprint 78: Resource Allocation Optimization - Day 3 Implementation**

Allocation validation:
- User must exist
- Sprint must exist
- No duplicate allocation (user to same sprint)
- Allocation percentage between 1-100%
- Dates must be within sprint range
- Total allocation across sprints cannot exceed 100%

Args:
    data: Allocation creation data

Returns:
    Created ResourceAllocationResponse

Raises:
    400: Validation error or conflict detected
    404: Sprint or user not found

</details>

---

### 🟢 POST `/api/v1/planning/allocations/check-conflicts`

**Summary**: Check allocation conflicts

<details>
<summary>View full description</summary>

Check if an allocation would create conflicts.

**Sprint 78: Resource Allocation Optimization - Day 3 Implementation**

Use this endpoint before creating/updating an allocation to validate.

Returns:
- Whether conflicts exist
- List of conflicts with details
- Warnings for high utilization

</details>

---

### 🔵 GET `/api/v1/planning/allocations/{allocation_id}`

**Summary**: Get a resource allocation

**Description**: Get a single allocation with user and sprint details.

---

### 🟡 PUT `/api/v1/planning/allocations/{allocation_id}`

**Summary**: Update a resource allocation


---

### 🔴 DELETE `/api/v1/planning/allocations/{allocation_id}`

**Summary**: Delete a resource allocation


---

### 🟢 POST `/api/v1/planning/dependencies`

**Summary**: Create sprint dependency

<details>
<summary>View full description</summary>

Create a dependency between two sprints.

**Sprint 78: Cross-Project Sprint Dependencies - Day 2 Implementation**

Dependency types:
- **blocks**: Source sprint is blocked until target completes (critical)
- **requires**: Source requires deliverable from target
- **related**: Sprints are related but not blocking

Validation:
- Both sprints must exist
- No self-reference allowed
- Circular dependencies are prevented

Args:
    data: Dependency creation data

Returns:
    Created SprintDependencyResponse

Raises:
    400: Invalid dependency (circular, self-reference, duplicate)
    404: Sprint not found

</details>

---

### 🟢 POST `/api/v1/planning/dependencies/bulk/resolve`

**Summary**: Bulk resolve dependencies


---

### 🔵 GET `/api/v1/planning/dependencies/check-circular`

**Summary**: Check for circular dependency

**Description**: Check if adding a dependency would create a cycle.

Use this endpoint before creating a dependency to validate.

---

### 🔵 GET `/api/v1/planning/dependencies/{dependency_id}`

**Summary**: Get a sprint dependency


---

### 🟡 PUT `/api/v1/planning/dependencies/{dependency_id}`

**Summary**: Update a sprint dependency

**Description**: Update a dependency's type, description, or status.

---

### 🔴 DELETE `/api/v1/planning/dependencies/{dependency_id}`

**Summary**: Delete a sprint dependency


---

### 🟢 POST `/api/v1/planning/dependencies/{dependency_id}/resolve`

**Summary**: Resolve a sprint dependency


---

### 🔵 GET `/api/v1/planning/projects/{project_id}/dependency-analysis`

**Summary**: Analyze project dependencies

<details>
<summary>View full description</summary>

Analyze dependency structure for a project.

Returns:
- Dependency counts by type and status
- Critical path through dependency chain
- Risk indicators (high-dependency sprints)

</details>

---

### 🔵 GET `/api/v1/planning/projects/{project_id}/dependency-graph`

**Summary**: Get dependency graph for a project

<details>
<summary>View full description</summary>

Get dependency graph for visualization.

**Sprint 78: Cross-Project Sprint Dependencies - Day 2 Implementation**

Returns a graph structure with:
- **nodes**: Sprints with status and blocking info
- **edges**: Dependencies with type and status

Suitable for rendering with visualization libraries like ReactFlow or D3.

</details>

---

### 🔵 GET `/api/v1/planning/projects/{project_id}/resource-heatmap`

**Summary**: Get resource allocation heatmap

<details>
<summary>View full description</summary>

Get resource allocation heatmap for visualization.

**Sprint 78: Resource Allocation Optimization - Day 3 Implementation**

Returns a heatmap structure with:
- **users**: List of users with allocations
- **sprints**: List of sprints
- **cells**: Allocation data for each user-sprint combination

Suitable for rendering with visualization libraries.

Cell status values:
- **available**: No allocation (0%)
- **partial**: Partial allocation (1-99%)
- **full**: Full allocation (100%)
- **over_allocated**: Over-allocated (>100%)

</details>

---

### 🔵 GET `/api/v1/planning/projects/{project_id}/retrospective-comparison`

**Summary**: Compare retrospectives across sprints

<details>
<summary>View full description</summary>

Compare retrospectives across multiple sprints.

**Sprint 78: Retrospective Enhancement - Day 1 Implementation**

Compares key metrics across selected sprints:
- Completion rates
- P0 completion rates
- Blocked item trends
- Velocity trends
- Action item completion rates

Args:
    project_id: Project UUID
    sprint_ids: Comma-separated sprint UUIDs (2-5 sprints)

Returns:
    Comparison data with metrics for each sprint

</details>

---

### 🔵 GET `/api/v1/planning/projects/{project_id}/template-suggestions`

**Summary**: Get template suggestions for project

<details>
<summary>View full description</summary>

Get template suggestions based on project context.

**Sprint 78: Sprint Template Library - Day 4 Implementation**

Analyzes:
- Recent sprint patterns
- Project characteristics
- Template popularity

Returns top 5 suggestions with match scores.

</details>

---

### 🔵 GET `/api/v1/planning/projects/{project_id}/velocity`

**Summary**: Get project velocity metrics

<details>
<summary>View full description</summary>

Get velocity metrics for a project from historical sprint data.

**Sprint 76: AI Sprint Assistant - Velocity Calculation**

Calculates:
- Average velocity (story points per sprint)
- Velocity trend (increasing/decreasing/stable)
- Confidence score based on data availability
- History of recent sprint velocities

Args:
    project_id: Project UUID
    sprint_count: Number of completed sprints to analyze (default: 5)

Returns:
    VelocityMetricsResponse with velocity metrics

Raises:
    404: Project not found or no access

</details>

---

### 🟢 POST `/api/v1/planning/sprints/{sprint_id}/action-items`

**Summary**: Create action item from retrospective

<details>
<summary>View full description</summary>

Create a new action item from sprint retrospective.

**Sprint 78: Retrospective Enhancement - Day 1 Implementation**

Action items track concrete next steps identified during sprint retrospectives.
Supports:
- Category classification (delivery, priority, velocity, etc.)
- Priority levels (low, medium, high)
- Assignment to team members
- Cross-sprint tracking via due_sprint_id

Args:
    sprint_id: Sprint UUID (source sprint)
    data: Action item data

Returns:
    Created RetroActionItemResponse

Raises:
    404: Sprint not found
    403: No write access to project

</details>

---

### 🔵 GET `/api/v1/planning/sprints/{sprint_id}/action-items`

**Summary**: List action items for a sprint

<details>
<summary>View full description</summary>

List action items for a sprint retrospective.

**Sprint 78: Retrospective Enhancement - Day 1 Implementation**

Supports filtering by:
- status: open, in_progress, completed, cancelled
- category: delivery, priority, velocity, planning, scope, blockers, team, general
- priority: low, medium, high
- assignee_id: User UUID

Args:
    sprint_id: Sprint UUID
    Various filters

Returns:
    Paginated list of action items

</details>

---

### 🟢 POST `/api/v1/planning/sprints/{sprint_id}/action-items/bulk`

**Summary**: Bulk create action items

**Description**: Bulk create action items from retrospective.

Useful for importing action items generated by retrospective automation.

---

### 🔵 GET `/api/v1/planning/sprints/{sprint_id}/action-items/stats`

**Summary**: Get action items statistics

**Description**: Get statistics for action items in a sprint retrospective.

Returns counts by status, category, and priority.

---

### 🔵 GET `/api/v1/planning/sprints/{sprint_id}/allocations`

**Summary**: List allocations for a sprint

**Description**: List all team member allocations for a sprint.

Returns paginated list of allocations with user details.

---

### 🔵 GET `/api/v1/planning/sprints/{sprint_id}/analytics`

**Summary**: Get comprehensive sprint analytics

<details>
<summary>View full description</summary>

Get comprehensive analytics for a sprint.

**Sprint 76: AI Sprint Assistant - Full Analytics**

Combines velocity, health, and suggestions into a single response
with an AI-generated summary of sprint status.

Args:
    sprint_id: Sprint UUID

Returns:
    SprintAnalyticsResponse with full analytics

Raises:
    404: Sprint not found

</details>

---

### 🔵 GET `/api/v1/planning/sprints/{sprint_id}/burndown`

**Summary**: Get sprint burndown chart data

<details>
<summary>View full description</summary>

Get burndown chart data for a sprint.

**Sprint 77: Burndown Charts - Day 2 Implementation**

Generates burndown chart data including:
- Ideal burndown line (linear from total points to 0)
- Actual burndown line (based on completed items)
- Progress metrics (completion rate, days remaining)
- On-track indicator (actual vs ideal comparison)

Performance Budget:
- Query time: <50ms
- Calculation time: <20ms
- Total response: <100ms p95

Args:
    sprint_id: Sprint UUID

Returns:
    BurndownChartResponse with ideal and actual burndown data

Raises:
    404: Sprint not found
    400: Sprint has no start/end dates

</details>

---

### 🔵 GET `/api/v1/planning/sprints/{sprint_id}/capacity`

**Summary**: Get sprint capacity

<details>
<summary>View full description</summary>

Calculate capacity for a sprint.

**Sprint 78: Resource Allocation Optimization - Day 3 Implementation**

Returns:
- Team size (allocated members)
- Total capacity hours
- Allocated hours
- Available hours
- Utilization rate (%)
- Breakdown by role

</details>

---

### 🔵 GET `/api/v1/planning/sprints/{sprint_id}/dependencies`

**Summary**: List dependencies for a sprint

<details>
<summary>View full description</summary>

List dependencies for a specific sprint.

Direction:
- **incoming**: Dependencies where this sprint is the target
- **outgoing**: Dependencies where this sprint is the source
- **both**: All dependencies involving this sprint

</details>

---

### 🔵 GET `/api/v1/planning/sprints/{sprint_id}/forecast`

**Summary**: Get sprint completion forecast

<details>
<summary>View full description</summary>

Get sprint completion forecast with probability and risks.

**Sprint 77: Sprint Forecasting - Day 3 Implementation**

Predicts sprint completion probability based on:
- Current vs required burn rate
- Blocked items penalty (-5% each)
- Incomplete P0 items penalty (-10% each)
- Days remaining urgency factor

Returns:
- Completion probability (0-100%)
- Predicted end date
- On-track indicator
- Identified risks with severity
- AI-generated recommendations

Performance Budget:
- Query time: <50ms
- Calculation time: <30ms
- Total response: <100ms p95

Args:
    sprint_id: Sprint UUID

Returns:
    SprintForecastResponse with probability, risks, and recommendations

Raises:
    404: Sprint not found

*(truncated for brevity)*

</details>

---

### 🔵 GET `/api/v1/planning/sprints/{sprint_id}/health`

**Summary**: Get sprint health indicators

<details>
<summary>View full description</summary>

Get health indicators for a sprint.

**Sprint 76: AI Sprint Assistant - Health Assessment**

Calculates:
- Completion rate (story points done / total)
- Blocked item count
- Risk level (low/medium/high based on progress vs time)
- Days remaining in sprint
- Expected completion based on time elapsed

Args:
    sprint_id: Sprint UUID

Returns:
    SprintHealthResponse with health indicators

Raises:
    404: Sprint not found

</details>

---

### 🔵 GET `/api/v1/planning/sprints/{sprint_id}/retrospective`

**Summary**: Get auto-generated sprint retrospective

<details>
<summary>View full description</summary>

Get auto-generated sprint retrospective.

**Sprint 77: Retrospective Automation - Day 4 Implementation**

Analyzes sprint performance and generates:
- Metrics summary (completion rate, P0 status, blocked items)
- "Went well" insights (positive patterns)
- "Needs improvement" insights (areas for growth)
- Action items (concrete next steps)
- Executive summary

Insight Categories:
- delivery: Completion and delivery performance
- priority: P0/P1 focus and completion
- velocity: Velocity trends (improving/stable/declining)
- planning: Sprint planning accuracy
- scope: Scope changes and creep
- blockers: Blocked items management

Performance Budget:
- Query time: <50ms
- Analysis time: <30ms
- Total response: <100ms p95

Args:
    sprint_id: Sprint UUID

Returns:
    SprintRetrospectiveResponse with metrics, insights, and actions


*(truncated for brevity)*

</details>

---

### 🔵 GET `/api/v1/planning/sprints/{sprint_id}/suggestions`

**Summary**: Get AI prioritization suggestions

<details>
<summary>View full description</summary>

Get AI-powered prioritization suggestions for a sprint.

**Sprint 76: AI Sprint Assistant - Recommendations**

Analyzes sprint backlog and generates suggestions:
- start_p0: P0 items not yet started (critical)
- unassigned_priority: Unassigned P0/P1 items
- overloaded: Sprint capacity exceeds velocity
- blocked: Items requiring unblocking
- p2_at_risk: Low-priority items at risk
- underloaded: Capacity opportunity

Args:
    sprint_id: Sprint UUID

Returns:
    SprintSuggestionsResponse with AI suggestions

Raises:
    404: Sprint not found

</details>

---

### 🔵 GET `/api/v1/planning/teams/{team_id}/capacity`

**Summary**: Get team capacity

<details>
<summary>View full description</summary>

Calculate team capacity for a date range.

**Sprint 78: Resource Allocation Optimization - Day 3 Implementation**

Returns:
- Total capacity hours for team
- Allocated hours
- Available hours
- Utilization rate (%)
- Breakdown by member
- Breakdown by role

</details>

---

### 🟢 POST `/api/v1/planning/templates`

**Summary**: Create sprint template

<details>
<summary>View full description</summary>

Create a new sprint template.

**Sprint 78: Sprint Template Library - Day 4 Implementation**

Template types:
- **standard**: Standard 2-week sprint
- **feature**: Feature-focused sprint
- **bugfix**: Bug-fix focused sprint
- **release**: Release preparation sprint
- **custom**: Custom configuration

Templates can include:
- Default duration and capacity
- Pre-defined backlog structure
- Sprint goal template
- Gate configuration

Args:
    data: Template creation data

Returns:
    Created SprintTemplateResponse

</details>

---

### 🔵 GET `/api/v1/planning/templates`

**Summary**: List sprint templates

<details>
<summary>View full description</summary>

List available sprint templates.

**Sprint 78: Sprint Template Library - Day 4 Implementation**

Filters:
- **team_id**: Team-specific templates
- **template_type**: Filter by type (standard, feature, bugfix, release, custom)
- **include_public**: Include public templates (default: true)

Returns paginated list sorted by:
1. Default templates first
2. Usage count (popularity)

</details>

---

### 🟢 POST `/api/v1/planning/templates/bulk/delete`

**Summary**: Bulk delete templates


---

### 🔵 GET `/api/v1/planning/templates/default`

**Summary**: Get default template

**Description**: Get the default template for a team or organization.

Returns team-specific default if available, otherwise public default.

---

### 🔵 GET `/api/v1/planning/templates/{template_id}`

**Summary**: Get a sprint template


---

### 🟡 PUT `/api/v1/planning/templates/{template_id}`

**Summary**: Update a sprint template


---

### 🔴 DELETE `/api/v1/planning/templates/{template_id}`

**Summary**: Delete a sprint template


---

### 🟢 POST `/api/v1/planning/templates/{template_id}/apply`

**Summary**: Apply template to create sprint

<details>
<summary>View full description</summary>

Create a new sprint from a template.

**Sprint 78: Sprint Template Library - Day 4 Implementation**

Copies from template:
- Duration configuration
- Capacity points
- Gate settings
- Backlog structure (if include_backlog=true)

Can override:
- Sprint name
- Goal
- Team size

Args:
    template_id: Template to apply
    data: Apply template request

Returns:
    ApplyTemplateResponse with created sprint info

Raises:
    400: Validation error
    404: Template or project not found

</details>

---

### 🔵 GET `/api/v1/planning/users/{user_id}/allocations`

**Summary**: List allocations for a user

**Description**: List all sprint allocations for a user.

Optionally filter by date range.

---

### 🔵 GET `/api/v1/planning/users/{user_id}/capacity`

**Summary**: Get user capacity

<details>
<summary>View full description</summary>

Calculate user capacity for a date range.

**Sprint 78: Resource Allocation Optimization - Day 3 Implementation**

Returns:
- Total working days in period
- Allocated days across sprints
- Available days
- Utilization rate (%)
- List of allocations

</details>

---

## Planning Hierarchy

### 🟢 POST `/api/v1/planning/action-items/bulk/status`

**Summary**: Bulk update action item status


---

### 🟢 POST `/api/v1/planning/action-items/bulk/status`

**Summary**: Bulk update action item status


---

### 🔵 GET `/api/v1/planning/action-items/{item_id}`

**Summary**: Get a single action item


---

### 🔵 GET `/api/v1/planning/action-items/{item_id}`

**Summary**: Get a single action item


---

### 🟡 PUT `/api/v1/planning/action-items/{item_id}`

**Summary**: Update an action item

<details>
<summary>View full description</summary>

Update an action item.

Status transitions:
- open -> in_progress (when assigned)
- in_progress -> completed (manual)
- Any -> cancelled (manual)

</details>

---

### 🟡 PUT `/api/v1/planning/action-items/{item_id}`

**Summary**: Update an action item

<details>
<summary>View full description</summary>

Update an action item.

Status transitions:
- open -> in_progress (when assigned)
- in_progress -> completed (manual)
- Any -> cancelled (manual)

</details>

---

### 🔴 DELETE `/api/v1/planning/action-items/{item_id}`

**Summary**: Delete an action item


---

### 🔴 DELETE `/api/v1/planning/action-items/{item_id}`

**Summary**: Delete an action item


---

### 🟢 POST `/api/v1/planning/allocations`

**Summary**: Create resource allocation

<details>
<summary>View full description</summary>

Allocate a team member to a sprint.

**Sprint 78: Resource Allocation Optimization - Day 3 Implementation**

Allocation validation:
- User must exist
- Sprint must exist
- No duplicate allocation (user to same sprint)
- Allocation percentage between 1-100%
- Dates must be within sprint range
- Total allocation across sprints cannot exceed 100%

Args:
    data: Allocation creation data

Returns:
    Created ResourceAllocationResponse

Raises:
    400: Validation error or conflict detected
    404: Sprint or user not found

</details>

---

### 🟢 POST `/api/v1/planning/allocations`

**Summary**: Create resource allocation

<details>
<summary>View full description</summary>

Allocate a team member to a sprint.

**Sprint 78: Resource Allocation Optimization - Day 3 Implementation**

Allocation validation:
- User must exist
- Sprint must exist
- No duplicate allocation (user to same sprint)
- Allocation percentage between 1-100%
- Dates must be within sprint range
- Total allocation across sprints cannot exceed 100%

Args:
    data: Allocation creation data

Returns:
    Created ResourceAllocationResponse

Raises:
    400: Validation error or conflict detected
    404: Sprint or user not found

</details>

---

### 🟢 POST `/api/v1/planning/allocations/check-conflicts`

**Summary**: Check allocation conflicts

<details>
<summary>View full description</summary>

Check if an allocation would create conflicts.

**Sprint 78: Resource Allocation Optimization - Day 3 Implementation**

Use this endpoint before creating/updating an allocation to validate.

Returns:
- Whether conflicts exist
- List of conflicts with details
- Warnings for high utilization

</details>

---

### 🟢 POST `/api/v1/planning/allocations/check-conflicts`

**Summary**: Check allocation conflicts

<details>
<summary>View full description</summary>

Check if an allocation would create conflicts.

**Sprint 78: Resource Allocation Optimization - Day 3 Implementation**

Use this endpoint before creating/updating an allocation to validate.

Returns:
- Whether conflicts exist
- List of conflicts with details
- Warnings for high utilization

</details>

---

### 🔵 GET `/api/v1/planning/allocations/{allocation_id}`

**Summary**: Get a resource allocation

**Description**: Get a single allocation with user and sprint details.

---

### 🔵 GET `/api/v1/planning/allocations/{allocation_id}`

**Summary**: Get a resource allocation

**Description**: Get a single allocation with user and sprint details.

---

### 🟡 PUT `/api/v1/planning/allocations/{allocation_id}`

**Summary**: Update a resource allocation


---

### 🟡 PUT `/api/v1/planning/allocations/{allocation_id}`

**Summary**: Update a resource allocation


---

### 🔴 DELETE `/api/v1/planning/allocations/{allocation_id}`

**Summary**: Delete a resource allocation


---

### 🔴 DELETE `/api/v1/planning/allocations/{allocation_id}`

**Summary**: Delete a resource allocation


---

### 🟢 POST `/api/v1/planning/backlog`

**Summary**: Create Backlog Item

**Description**: Create a new backlog item (story, task, bug, spike).

SDLC 5.1.3 GAP 2 Resolution (Sprint 76):
- If assignee_id is provided, validates that assignee is a team member
- Projects without teams allow any assignee (backward compatibility)

---

### 🟢 POST `/api/v1/planning/backlog`

**Summary**: Create Backlog Item

**Description**: Create a new backlog item (story, task, bug, spike).

SDLC 5.1.3 GAP 2 Resolution (Sprint 76):
- If assignee_id is provided, validates that assignee is a team member
- Projects without teams allow any assignee (backward compatibility)

---

### 🔵 GET `/api/v1/planning/backlog`

**Summary**: List Backlog Items


---

### 🔵 GET `/api/v1/planning/backlog`

**Summary**: List Backlog Items


---

### 🔵 GET `/api/v1/planning/backlog/assignees/{project_id}`

**Summary**: Get Valid Assignees

<details>
<summary>View full description</summary>

Get list of valid assignees for backlog items in a project.

SDLC 5.1.3 GAP 2 Resolution (Sprint 76):
- Returns only team members who can be assigned to backlog items
- Used by frontend to populate assignee dropdown
- If project has no team, returns empty list (allow any assignee)

Returns:
    List of dicts with user info:
    [
        {
            "user_id": UUID,
            "full_name": str,
            "email": str,
            "role": str,
            "member_type": str
        }
    ]

</details>

---

### 🔵 GET `/api/v1/planning/backlog/assignees/{project_id}`

**Summary**: Get Valid Assignees

<details>
<summary>View full description</summary>

Get list of valid assignees for backlog items in a project.

SDLC 5.1.3 GAP 2 Resolution (Sprint 76):
- Returns only team members who can be assigned to backlog items
- Used by frontend to populate assignee dropdown
- If project has no team, returns empty list (allow any assignee)

Returns:
    List of dicts with user info:
    [
        {
            "user_id": UUID,
            "full_name": str,
            "email": str,
            "role": str,
            "member_type": str
        }
    ]

</details>

---

### 🟢 POST `/api/v1/planning/backlog/bulk/move-to-sprint`

**Summary**: Bulk Move To Sprint

**Description**: Bulk move backlog items to a sprint (or back to product backlog).

---

### 🟢 POST `/api/v1/planning/backlog/bulk/move-to-sprint`

**Summary**: Bulk Move To Sprint

**Description**: Bulk move backlog items to a sprint (or back to product backlog).

---

### 🟢 POST `/api/v1/planning/backlog/bulk/update-priority`

**Summary**: Bulk Update Priority


---

### 🟢 POST `/api/v1/planning/backlog/bulk/update-priority`

**Summary**: Bulk Update Priority


---

### 🔵 GET `/api/v1/planning/backlog/{item_id}`

**Summary**: Get Backlog Item


---

### 🔵 GET `/api/v1/planning/backlog/{item_id}`

**Summary**: Get Backlog Item


---

### 🟡 PUT `/api/v1/planning/backlog/{item_id}`

**Summary**: Update Backlog Item

**Description**: Update a backlog item.

SDLC 5.1.3 GAP 2 Resolution (Sprint 76):
- If assignee_id is being updated, validates that new assignee is a team member
- Projects without teams allow any assignee (backward compatibility)

---

### 🟡 PUT `/api/v1/planning/backlog/{item_id}`

**Summary**: Update Backlog Item

**Description**: Update a backlog item.

SDLC 5.1.3 GAP 2 Resolution (Sprint 76):
- If assignee_id is being updated, validates that new assignee is a team member
- Projects without teams allow any assignee (backward compatibility)

---

### 🔴 DELETE `/api/v1/planning/backlog/{item_id}`

**Summary**: Delete Backlog Item


---

### 🔴 DELETE `/api/v1/planning/backlog/{item_id}`

**Summary**: Delete Backlog Item


---

### 🔵 GET `/api/v1/planning/dashboard/{project_id}`

**Summary**: Get Planning Dashboard

<details>
<summary>View full description</summary>

Get planning hierarchy dashboard data for a project.

Returns:
- All roadmaps with phases and sprints
- Active roadmap and current sprint
- Backlog statistics

</details>

---

### 🔵 GET `/api/v1/planning/dashboard/{project_id}`

**Summary**: Get Planning Dashboard

<details>
<summary>View full description</summary>

Get planning hierarchy dashboard data for a project.

Returns:
- All roadmaps with phases and sprints
- Active roadmap and current sprint
- Backlog statistics

</details>

---

### 🟢 POST `/api/v1/planning/dependencies`

**Summary**: Create sprint dependency

<details>
<summary>View full description</summary>

Create a dependency between two sprints.

**Sprint 78: Cross-Project Sprint Dependencies - Day 2 Implementation**

Dependency types:
- **blocks**: Source sprint is blocked until target completes (critical)
- **requires**: Source requires deliverable from target
- **related**: Sprints are related but not blocking

Validation:
- Both sprints must exist
- No self-reference allowed
- Circular dependencies are prevented

Args:
    data: Dependency creation data

Returns:
    Created SprintDependencyResponse

Raises:
    400: Invalid dependency (circular, self-reference, duplicate)
    404: Sprint not found

</details>

---

### 🟢 POST `/api/v1/planning/dependencies`

**Summary**: Create sprint dependency

<details>
<summary>View full description</summary>

Create a dependency between two sprints.

**Sprint 78: Cross-Project Sprint Dependencies - Day 2 Implementation**

Dependency types:
- **blocks**: Source sprint is blocked until target completes (critical)
- **requires**: Source requires deliverable from target
- **related**: Sprints are related but not blocking

Validation:
- Both sprints must exist
- No self-reference allowed
- Circular dependencies are prevented

Args:
    data: Dependency creation data

Returns:
    Created SprintDependencyResponse

Raises:
    400: Invalid dependency (circular, self-reference, duplicate)
    404: Sprint not found

</details>

---

### 🟢 POST `/api/v1/planning/dependencies/bulk/resolve`

**Summary**: Bulk resolve dependencies


---

### 🟢 POST `/api/v1/planning/dependencies/bulk/resolve`

**Summary**: Bulk resolve dependencies


---

### 🔵 GET `/api/v1/planning/dependencies/check-circular`

**Summary**: Check for circular dependency

**Description**: Check if adding a dependency would create a cycle.

Use this endpoint before creating a dependency to validate.

---

### 🔵 GET `/api/v1/planning/dependencies/check-circular`

**Summary**: Check for circular dependency

**Description**: Check if adding a dependency would create a cycle.

Use this endpoint before creating a dependency to validate.

---

### 🔵 GET `/api/v1/planning/dependencies/{dependency_id}`

**Summary**: Get a sprint dependency


---

### 🔵 GET `/api/v1/planning/dependencies/{dependency_id}`

**Summary**: Get a sprint dependency


---

### 🟡 PUT `/api/v1/planning/dependencies/{dependency_id}`

**Summary**: Update a sprint dependency

**Description**: Update a dependency's type, description, or status.

---

### 🟡 PUT `/api/v1/planning/dependencies/{dependency_id}`

**Summary**: Update a sprint dependency

**Description**: Update a dependency's type, description, or status.

---

### 🔴 DELETE `/api/v1/planning/dependencies/{dependency_id}`

**Summary**: Delete a sprint dependency


---

### 🔴 DELETE `/api/v1/planning/dependencies/{dependency_id}`

**Summary**: Delete a sprint dependency


---

### 🟢 POST `/api/v1/planning/dependencies/{dependency_id}/resolve`

**Summary**: Resolve a sprint dependency


---

### 🟢 POST `/api/v1/planning/dependencies/{dependency_id}/resolve`

**Summary**: Resolve a sprint dependency


---

### 🟢 POST `/api/v1/planning/phases`

**Summary**: Create Phase


---

### 🟢 POST `/api/v1/planning/phases`

**Summary**: Create Phase


---

### 🔵 GET `/api/v1/planning/phases`

**Summary**: List Phases


---

### 🔵 GET `/api/v1/planning/phases`

**Summary**: List Phases


---

### 🔵 GET `/api/v1/planning/phases/{phase_id}`

**Summary**: Get Phase


---

### 🔵 GET `/api/v1/planning/phases/{phase_id}`

**Summary**: Get Phase


---

### 🟡 PUT `/api/v1/planning/phases/{phase_id}`

**Summary**: Update Phase


---

### 🟡 PUT `/api/v1/planning/phases/{phase_id}`

**Summary**: Update Phase


---

### 🔴 DELETE `/api/v1/planning/phases/{phase_id}`

**Summary**: Delete Phase


---

### 🔴 DELETE `/api/v1/planning/phases/{phase_id}`

**Summary**: Delete Phase


---

### 🔵 GET `/api/v1/planning/projects/{project_id}/dependency-analysis`

**Summary**: Analyze project dependencies

<details>
<summary>View full description</summary>

Analyze dependency structure for a project.

Returns:
- Dependency counts by type and status
- Critical path through dependency chain
- Risk indicators (high-dependency sprints)

</details>

---

### 🔵 GET `/api/v1/planning/projects/{project_id}/dependency-analysis`

**Summary**: Analyze project dependencies

<details>
<summary>View full description</summary>

Analyze dependency structure for a project.

Returns:
- Dependency counts by type and status
- Critical path through dependency chain
- Risk indicators (high-dependency sprints)

</details>

---

### 🔵 GET `/api/v1/planning/projects/{project_id}/dependency-graph`

**Summary**: Get dependency graph for a project

<details>
<summary>View full description</summary>

Get dependency graph for visualization.

**Sprint 78: Cross-Project Sprint Dependencies - Day 2 Implementation**

Returns a graph structure with:
- **nodes**: Sprints with status and blocking info
- **edges**: Dependencies with type and status

Suitable for rendering with visualization libraries like ReactFlow or D3.

</details>

---

### 🔵 GET `/api/v1/planning/projects/{project_id}/dependency-graph`

**Summary**: Get dependency graph for a project

<details>
<summary>View full description</summary>

Get dependency graph for visualization.

**Sprint 78: Cross-Project Sprint Dependencies - Day 2 Implementation**

Returns a graph structure with:
- **nodes**: Sprints with status and blocking info
- **edges**: Dependencies with type and status

Suitable for rendering with visualization libraries like ReactFlow or D3.

</details>

---

### 🔵 GET `/api/v1/planning/projects/{project_id}/resource-heatmap`

**Summary**: Get resource allocation heatmap

<details>
<summary>View full description</summary>

Get resource allocation heatmap for visualization.

**Sprint 78: Resource Allocation Optimization - Day 3 Implementation**

Returns a heatmap structure with:
- **users**: List of users with allocations
- **sprints**: List of sprints
- **cells**: Allocation data for each user-sprint combination

Suitable for rendering with visualization libraries.

Cell status values:
- **available**: No allocation (0%)
- **partial**: Partial allocation (1-99%)
- **full**: Full allocation (100%)
- **over_allocated**: Over-allocated (>100%)

</details>

---

### 🔵 GET `/api/v1/planning/projects/{project_id}/resource-heatmap`

**Summary**: Get resource allocation heatmap

<details>
<summary>View full description</summary>

Get resource allocation heatmap for visualization.

**Sprint 78: Resource Allocation Optimization - Day 3 Implementation**

Returns a heatmap structure with:
- **users**: List of users with allocations
- **sprints**: List of sprints
- **cells**: Allocation data for each user-sprint combination

Suitable for rendering with visualization libraries.

Cell status values:
- **available**: No allocation (0%)
- **partial**: Partial allocation (1-99%)
- **full**: Full allocation (100%)
- **over_allocated**: Over-allocated (>100%)

</details>

---

### 🔵 GET `/api/v1/planning/projects/{project_id}/retrospective-comparison`

**Summary**: Compare retrospectives across sprints

<details>
<summary>View full description</summary>

Compare retrospectives across multiple sprints.

**Sprint 78: Retrospective Enhancement - Day 1 Implementation**

Compares key metrics across selected sprints:
- Completion rates
- P0 completion rates
- Blocked item trends
- Velocity trends
- Action item completion rates

Args:
    project_id: Project UUID
    sprint_ids: Comma-separated sprint UUIDs (2-5 sprints)

Returns:
    Comparison data with metrics for each sprint

</details>

---

### 🔵 GET `/api/v1/planning/projects/{project_id}/retrospective-comparison`

**Summary**: Compare retrospectives across sprints

<details>
<summary>View full description</summary>

Compare retrospectives across multiple sprints.

**Sprint 78: Retrospective Enhancement - Day 1 Implementation**

Compares key metrics across selected sprints:
- Completion rates
- P0 completion rates
- Blocked item trends
- Velocity trends
- Action item completion rates

Args:
    project_id: Project UUID
    sprint_ids: Comma-separated sprint UUIDs (2-5 sprints)

Returns:
    Comparison data with metrics for each sprint

</details>

---

### 🔵 GET `/api/v1/planning/projects/{project_id}/template-suggestions`

**Summary**: Get template suggestions for project

<details>
<summary>View full description</summary>

Get template suggestions based on project context.

**Sprint 78: Sprint Template Library - Day 4 Implementation**

Analyzes:
- Recent sprint patterns
- Project characteristics
- Template popularity

Returns top 5 suggestions with match scores.

</details>

---

### 🔵 GET `/api/v1/planning/projects/{project_id}/template-suggestions`

**Summary**: Get template suggestions for project

<details>
<summary>View full description</summary>

Get template suggestions based on project context.

**Sprint 78: Sprint Template Library - Day 4 Implementation**

Analyzes:
- Recent sprint patterns
- Project characteristics
- Template popularity

Returns top 5 suggestions with match scores.

</details>

---

### 🔵 GET `/api/v1/planning/projects/{project_id}/velocity`

**Summary**: Get project velocity metrics

<details>
<summary>View full description</summary>

Get velocity metrics for a project from historical sprint data.

**Sprint 76: AI Sprint Assistant - Velocity Calculation**

Calculates:
- Average velocity (story points per sprint)
- Velocity trend (increasing/decreasing/stable)
- Confidence score based on data availability
- History of recent sprint velocities

Args:
    project_id: Project UUID
    sprint_count: Number of completed sprints to analyze (default: 5)

Returns:
    VelocityMetricsResponse with velocity metrics

Raises:
    404: Project not found or no access

</details>

---

### 🔵 GET `/api/v1/planning/projects/{project_id}/velocity`

**Summary**: Get project velocity metrics

<details>
<summary>View full description</summary>

Get velocity metrics for a project from historical sprint data.

**Sprint 76: AI Sprint Assistant - Velocity Calculation**

Calculates:
- Average velocity (story points per sprint)
- Velocity trend (increasing/decreasing/stable)
- Confidence score based on data availability
- History of recent sprint velocities

Args:
    project_id: Project UUID
    sprint_count: Number of completed sprints to analyze (default: 5)

Returns:
    VelocityMetricsResponse with velocity metrics

Raises:
    404: Project not found or no access

</details>

---

### 🟢 POST `/api/v1/planning/roadmaps`

**Summary**: Create Roadmap

**Description**: Create a new roadmap for a project.

Roadmaps represent strategic 12-month planning with quarterly review cadence.

---

### 🟢 POST `/api/v1/planning/roadmaps`

**Summary**: Create Roadmap

**Description**: Create a new roadmap for a project.

Roadmaps represent strategic 12-month planning with quarterly review cadence.

---

### 🔵 GET `/api/v1/planning/roadmaps`

**Summary**: List Roadmaps


---

### 🔵 GET `/api/v1/planning/roadmaps`

**Summary**: List Roadmaps


---

### 🔵 GET `/api/v1/planning/roadmaps/{roadmap_id}`

**Summary**: Get Roadmap


---

### 🔵 GET `/api/v1/planning/roadmaps/{roadmap_id}`

**Summary**: Get Roadmap


---

### 🟡 PUT `/api/v1/planning/roadmaps/{roadmap_id}`

**Summary**: Update Roadmap


---

### 🟡 PUT `/api/v1/planning/roadmaps/{roadmap_id}`

**Summary**: Update Roadmap


---

### 🔴 DELETE `/api/v1/planning/roadmaps/{roadmap_id}`

**Summary**: Delete Roadmap


---

### 🔴 DELETE `/api/v1/planning/roadmaps/{roadmap_id}`

**Summary**: Delete Roadmap


---

### 🟢 POST `/api/v1/planning/sprints`

**Summary**: Create Sprint

**Description**: Create a new sprint.

SDLC 5.1.3 Rule #1: Sprint numbers are immutable after creation.

---

### 🟢 POST `/api/v1/planning/sprints`

**Summary**: Create Sprint

**Description**: Create a new sprint.

SDLC 5.1.3 Rule #1: Sprint numbers are immutable after creation.

---

### 🔵 GET `/api/v1/planning/sprints`

**Summary**: List Sprints


---

### 🔵 GET `/api/v1/planning/sprints`

**Summary**: List Sprints


---

### 🔵 GET `/api/v1/planning/sprints/{sprint_id}`

**Summary**: Get Sprint


---

### 🔵 GET `/api/v1/planning/sprints/{sprint_id}`

**Summary**: Get Sprint


---

### 🟡 PUT `/api/v1/planning/sprints/{sprint_id}`

**Summary**: Update Sprint

**Description**: Update a sprint.

Note: Sprint number cannot be changed (Rule #1: Immutable).

---

### 🟡 PUT `/api/v1/planning/sprints/{sprint_id}`

**Summary**: Update Sprint

**Description**: Update a sprint.

Note: Sprint number cannot be changed (Rule #1: Immutable).

---

### 🔴 DELETE `/api/v1/planning/sprints/{sprint_id}`

**Summary**: Delete Sprint

**Description**: Delete a sprint.

Warning: Deleting a sprint moves all backlog items back to the product backlog.

---

### 🔴 DELETE `/api/v1/planning/sprints/{sprint_id}`

**Summary**: Delete Sprint

**Description**: Delete a sprint.

Warning: Deleting a sprint moves all backlog items back to the product backlog.

---

### 🟢 POST `/api/v1/planning/sprints/{sprint_id}/action-items`

**Summary**: Create action item from retrospective

<details>
<summary>View full description</summary>

Create a new action item from sprint retrospective.

**Sprint 78: Retrospective Enhancement - Day 1 Implementation**

Action items track concrete next steps identified during sprint retrospectives.
Supports:
- Category classification (delivery, priority, velocity, etc.)
- Priority levels (low, medium, high)
- Assignment to team members
- Cross-sprint tracking via due_sprint_id

Args:
    sprint_id: Sprint UUID (source sprint)
    data: Action item data

Returns:
    Created RetroActionItemResponse

Raises:
    404: Sprint not found
    403: No write access to project

</details>

---

### 🟢 POST `/api/v1/planning/sprints/{sprint_id}/action-items`

**Summary**: Create action item from retrospective

<details>
<summary>View full description</summary>

Create a new action item from sprint retrospective.

**Sprint 78: Retrospective Enhancement - Day 1 Implementation**

Action items track concrete next steps identified during sprint retrospectives.
Supports:
- Category classification (delivery, priority, velocity, etc.)
- Priority levels (low, medium, high)
- Assignment to team members
- Cross-sprint tracking via due_sprint_id

Args:
    sprint_id: Sprint UUID (source sprint)
    data: Action item data

Returns:
    Created RetroActionItemResponse

Raises:
    404: Sprint not found
    403: No write access to project

</details>

---

### 🔵 GET `/api/v1/planning/sprints/{sprint_id}/action-items`

**Summary**: List action items for a sprint

<details>
<summary>View full description</summary>

List action items for a sprint retrospective.

**Sprint 78: Retrospective Enhancement - Day 1 Implementation**

Supports filtering by:
- status: open, in_progress, completed, cancelled
- category: delivery, priority, velocity, planning, scope, blockers, team, general
- priority: low, medium, high
- assignee_id: User UUID

Args:
    sprint_id: Sprint UUID
    Various filters

Returns:
    Paginated list of action items

</details>

---

### 🔵 GET `/api/v1/planning/sprints/{sprint_id}/action-items`

**Summary**: List action items for a sprint

<details>
<summary>View full description</summary>

List action items for a sprint retrospective.

**Sprint 78: Retrospective Enhancement - Day 1 Implementation**

Supports filtering by:
- status: open, in_progress, completed, cancelled
- category: delivery, priority, velocity, planning, scope, blockers, team, general
- priority: low, medium, high
- assignee_id: User UUID

Args:
    sprint_id: Sprint UUID
    Various filters

Returns:
    Paginated list of action items

</details>

---

### 🟢 POST `/api/v1/planning/sprints/{sprint_id}/action-items/bulk`

**Summary**: Bulk create action items

**Description**: Bulk create action items from retrospective.

Useful for importing action items generated by retrospective automation.

---

### 🟢 POST `/api/v1/planning/sprints/{sprint_id}/action-items/bulk`

**Summary**: Bulk create action items

**Description**: Bulk create action items from retrospective.

Useful for importing action items generated by retrospective automation.

---

### 🔵 GET `/api/v1/planning/sprints/{sprint_id}/action-items/stats`

**Summary**: Get action items statistics

**Description**: Get statistics for action items in a sprint retrospective.

Returns counts by status, category, and priority.

---

### 🔵 GET `/api/v1/planning/sprints/{sprint_id}/action-items/stats`

**Summary**: Get action items statistics

**Description**: Get statistics for action items in a sprint retrospective.

Returns counts by status, category, and priority.

---

### 🔵 GET `/api/v1/planning/sprints/{sprint_id}/allocations`

**Summary**: List allocations for a sprint

**Description**: List all team member allocations for a sprint.

Returns paginated list of allocations with user details.

---

### 🔵 GET `/api/v1/planning/sprints/{sprint_id}/allocations`

**Summary**: List allocations for a sprint

**Description**: List all team member allocations for a sprint.

Returns paginated list of allocations with user details.

---

### 🔵 GET `/api/v1/planning/sprints/{sprint_id}/analytics`

**Summary**: Get comprehensive sprint analytics

<details>
<summary>View full description</summary>

Get comprehensive analytics for a sprint.

**Sprint 76: AI Sprint Assistant - Full Analytics**

Combines velocity, health, and suggestions into a single response
with an AI-generated summary of sprint status.

Args:
    sprint_id: Sprint UUID

Returns:
    SprintAnalyticsResponse with full analytics

Raises:
    404: Sprint not found

</details>

---

### 🔵 GET `/api/v1/planning/sprints/{sprint_id}/analytics`

**Summary**: Get comprehensive sprint analytics

<details>
<summary>View full description</summary>

Get comprehensive analytics for a sprint.

**Sprint 76: AI Sprint Assistant - Full Analytics**

Combines velocity, health, and suggestions into a single response
with an AI-generated summary of sprint status.

Args:
    sprint_id: Sprint UUID

Returns:
    SprintAnalyticsResponse with full analytics

Raises:
    404: Sprint not found

</details>

---

### 🔵 GET `/api/v1/planning/sprints/{sprint_id}/burndown`

**Summary**: Get sprint burndown chart data

<details>
<summary>View full description</summary>

Get burndown chart data for a sprint.

**Sprint 77: Burndown Charts - Day 2 Implementation**

Generates burndown chart data including:
- Ideal burndown line (linear from total points to 0)
- Actual burndown line (based on completed items)
- Progress metrics (completion rate, days remaining)
- On-track indicator (actual vs ideal comparison)

Performance Budget:
- Query time: <50ms
- Calculation time: <20ms
- Total response: <100ms p95

Args:
    sprint_id: Sprint UUID

Returns:
    BurndownChartResponse with ideal and actual burndown data

Raises:
    404: Sprint not found
    400: Sprint has no start/end dates

</details>

---

### 🔵 GET `/api/v1/planning/sprints/{sprint_id}/burndown`

**Summary**: Get sprint burndown chart data

<details>
<summary>View full description</summary>

Get burndown chart data for a sprint.

**Sprint 77: Burndown Charts - Day 2 Implementation**

Generates burndown chart data including:
- Ideal burndown line (linear from total points to 0)
- Actual burndown line (based on completed items)
- Progress metrics (completion rate, days remaining)
- On-track indicator (actual vs ideal comparison)

Performance Budget:
- Query time: <50ms
- Calculation time: <20ms
- Total response: <100ms p95

Args:
    sprint_id: Sprint UUID

Returns:
    BurndownChartResponse with ideal and actual burndown data

Raises:
    404: Sprint not found
    400: Sprint has no start/end dates

</details>

---

### 🔵 GET `/api/v1/planning/sprints/{sprint_id}/capacity`

**Summary**: Get sprint capacity

<details>
<summary>View full description</summary>

Calculate capacity for a sprint.

**Sprint 78: Resource Allocation Optimization - Day 3 Implementation**

Returns:
- Team size (allocated members)
- Total capacity hours
- Allocated hours
- Available hours
- Utilization rate (%)
- Breakdown by role

</details>

---

### 🔵 GET `/api/v1/planning/sprints/{sprint_id}/capacity`

**Summary**: Get sprint capacity

<details>
<summary>View full description</summary>

Calculate capacity for a sprint.

**Sprint 78: Resource Allocation Optimization - Day 3 Implementation**

Returns:
- Team size (allocated members)
- Total capacity hours
- Allocated hours
- Available hours
- Utilization rate (%)
- Breakdown by role

</details>

---

### 🔵 GET `/api/v1/planning/sprints/{sprint_id}/dependencies`

**Summary**: List dependencies for a sprint

<details>
<summary>View full description</summary>

List dependencies for a specific sprint.

Direction:
- **incoming**: Dependencies where this sprint is the target
- **outgoing**: Dependencies where this sprint is the source
- **both**: All dependencies involving this sprint

</details>

---

### 🔵 GET `/api/v1/planning/sprints/{sprint_id}/dependencies`

**Summary**: List dependencies for a sprint

<details>
<summary>View full description</summary>

List dependencies for a specific sprint.

Direction:
- **incoming**: Dependencies where this sprint is the target
- **outgoing**: Dependencies where this sprint is the source
- **both**: All dependencies involving this sprint

</details>

---

### 🔵 GET `/api/v1/planning/sprints/{sprint_id}/forecast`

**Summary**: Get sprint completion forecast

<details>
<summary>View full description</summary>

Get sprint completion forecast with probability and risks.

**Sprint 77: Sprint Forecasting - Day 3 Implementation**

Predicts sprint completion probability based on:
- Current vs required burn rate
- Blocked items penalty (-5% each)
- Incomplete P0 items penalty (-10% each)
- Days remaining urgency factor

Returns:
- Completion probability (0-100%)
- Predicted end date
- On-track indicator
- Identified risks with severity
- AI-generated recommendations

Performance Budget:
- Query time: <50ms
- Calculation time: <30ms
- Total response: <100ms p95

Args:
    sprint_id: Sprint UUID

Returns:
    SprintForecastResponse with probability, risks, and recommendations

Raises:
    404: Sprint not found

*(truncated for brevity)*

</details>

---

### 🔵 GET `/api/v1/planning/sprints/{sprint_id}/forecast`

**Summary**: Get sprint completion forecast

<details>
<summary>View full description</summary>

Get sprint completion forecast with probability and risks.

**Sprint 77: Sprint Forecasting - Day 3 Implementation**

Predicts sprint completion probability based on:
- Current vs required burn rate
- Blocked items penalty (-5% each)
- Incomplete P0 items penalty (-10% each)
- Days remaining urgency factor

Returns:
- Completion probability (0-100%)
- Predicted end date
- On-track indicator
- Identified risks with severity
- AI-generated recommendations

Performance Budget:
- Query time: <50ms
- Calculation time: <30ms
- Total response: <100ms p95

Args:
    sprint_id: Sprint UUID

Returns:
    SprintForecastResponse with probability, risks, and recommendations

Raises:
    404: Sprint not found

*(truncated for brevity)*

</details>

---

### 🟢 POST `/api/v1/planning/sprints/{sprint_id}/gates`

**Summary**: Create Gate Evaluation

**Description**: Create a gate evaluation for a sprint.

Gate types:
- g_sprint: Sprint Planning Gate (before sprint starts)
- g_sprint_close: Sprint Completion Gate (before sprint closes)

---

### 🟢 POST `/api/v1/planning/sprints/{sprint_id}/gates`

**Summary**: Create Gate Evaluation

**Description**: Create a gate evaluation for a sprint.

Gate types:
- g_sprint: Sprint Planning Gate (before sprint starts)
- g_sprint_close: Sprint Completion Gate (before sprint closes)

---

### 🔵 GET `/api/v1/planning/sprints/{sprint_id}/gates`

**Summary**: List Gate Evaluations


---

### 🔵 GET `/api/v1/planning/sprints/{sprint_id}/gates`

**Summary**: List Gate Evaluations


---

### 🔵 GET `/api/v1/planning/sprints/{sprint_id}/gates/{gate_type}`

**Summary**: Get Gate Evaluation


---

### 🔵 GET `/api/v1/planning/sprints/{sprint_id}/gates/{gate_type}`

**Summary**: Get Gate Evaluation


---

### 🟡 PUT `/api/v1/planning/sprints/{sprint_id}/gates/{gate_type}`

**Summary**: Update Gate Evaluation


---

### 🟡 PUT `/api/v1/planning/sprints/{sprint_id}/gates/{gate_type}`

**Summary**: Update Gate Evaluation


---

### 🟢 POST `/api/v1/planning/sprints/{sprint_id}/gates/{gate_type}/submit`

**Summary**: Submit Gate Evaluation

<details>
<summary>View full description</summary>

Submit gate evaluation for approval.

SDLC 5.1.3 Sprint Planning Governance (Sprint 75):
- Only team owner/admin (SE4H Coach) can approve sprint gates
- AI agents (SE4A) cannot approve gates
- This enforces human oversight for sprint governance

The gate passes only if all checklist items are checked.
This also updates the sprint's gate status.

</details>

---

### 🟢 POST `/api/v1/planning/sprints/{sprint_id}/gates/{gate_type}/submit`

**Summary**: Submit Gate Evaluation

<details>
<summary>View full description</summary>

Submit gate evaluation for approval.

SDLC 5.1.3 Sprint Planning Governance (Sprint 75):
- Only team owner/admin (SE4H Coach) can approve sprint gates
- AI agents (SE4A) cannot approve gates
- This enforces human oversight for sprint governance

The gate passes only if all checklist items are checked.
This also updates the sprint's gate status.

</details>

---

### 🔵 GET `/api/v1/planning/sprints/{sprint_id}/health`

**Summary**: Get sprint health indicators

<details>
<summary>View full description</summary>

Get health indicators for a sprint.

**Sprint 76: AI Sprint Assistant - Health Assessment**

Calculates:
- Completion rate (story points done / total)
- Blocked item count
- Risk level (low/medium/high based on progress vs time)
- Days remaining in sprint
- Expected completion based on time elapsed

Args:
    sprint_id: Sprint UUID

Returns:
    SprintHealthResponse with health indicators

Raises:
    404: Sprint not found

</details>

---

### 🔵 GET `/api/v1/planning/sprints/{sprint_id}/health`

**Summary**: Get sprint health indicators

<details>
<summary>View full description</summary>

Get health indicators for a sprint.

**Sprint 76: AI Sprint Assistant - Health Assessment**

Calculates:
- Completion rate (story points done / total)
- Blocked item count
- Risk level (low/medium/high based on progress vs time)
- Days remaining in sprint
- Expected completion based on time elapsed

Args:
    sprint_id: Sprint UUID

Returns:
    SprintHealthResponse with health indicators

Raises:
    404: Sprint not found

</details>

---

### 🔵 GET `/api/v1/planning/sprints/{sprint_id}/retrospective`

**Summary**: Get auto-generated sprint retrospective

<details>
<summary>View full description</summary>

Get auto-generated sprint retrospective.

**Sprint 77: Retrospective Automation - Day 4 Implementation**

Analyzes sprint performance and generates:
- Metrics summary (completion rate, P0 status, blocked items)
- "Went well" insights (positive patterns)
- "Needs improvement" insights (areas for growth)
- Action items (concrete next steps)
- Executive summary

Insight Categories:
- delivery: Completion and delivery performance
- priority: P0/P1 focus and completion
- velocity: Velocity trends (improving/stable/declining)
- planning: Sprint planning accuracy
- scope: Scope changes and creep
- blockers: Blocked items management

Performance Budget:
- Query time: <50ms
- Analysis time: <30ms
- Total response: <100ms p95

Args:
    sprint_id: Sprint UUID

Returns:
    SprintRetrospectiveResponse with metrics, insights, and actions


*(truncated for brevity)*

</details>

---

### 🔵 GET `/api/v1/planning/sprints/{sprint_id}/retrospective`

**Summary**: Get auto-generated sprint retrospective

<details>
<summary>View full description</summary>

Get auto-generated sprint retrospective.

**Sprint 77: Retrospective Automation - Day 4 Implementation**

Analyzes sprint performance and generates:
- Metrics summary (completion rate, P0 status, blocked items)
- "Went well" insights (positive patterns)
- "Needs improvement" insights (areas for growth)
- Action items (concrete next steps)
- Executive summary

Insight Categories:
- delivery: Completion and delivery performance
- priority: P0/P1 focus and completion
- velocity: Velocity trends (improving/stable/declining)
- planning: Sprint planning accuracy
- scope: Scope changes and creep
- blockers: Blocked items management

Performance Budget:
- Query time: <50ms
- Analysis time: <30ms
- Total response: <100ms p95

Args:
    sprint_id: Sprint UUID

Returns:
    SprintRetrospectiveResponse with metrics, insights, and actions


*(truncated for brevity)*

</details>

---

### 🔵 GET `/api/v1/planning/sprints/{sprint_id}/suggestions`

**Summary**: Get AI prioritization suggestions

<details>
<summary>View full description</summary>

Get AI-powered prioritization suggestions for a sprint.

**Sprint 76: AI Sprint Assistant - Recommendations**

Analyzes sprint backlog and generates suggestions:
- start_p0: P0 items not yet started (critical)
- unassigned_priority: Unassigned P0/P1 items
- overloaded: Sprint capacity exceeds velocity
- blocked: Items requiring unblocking
- p2_at_risk: Low-priority items at risk
- underloaded: Capacity opportunity

Args:
    sprint_id: Sprint UUID

Returns:
    SprintSuggestionsResponse with AI suggestions

Raises:
    404: Sprint not found

</details>

---

### 🔵 GET `/api/v1/planning/sprints/{sprint_id}/suggestions`

**Summary**: Get AI prioritization suggestions

<details>
<summary>View full description</summary>

Get AI-powered prioritization suggestions for a sprint.

**Sprint 76: AI Sprint Assistant - Recommendations**

Analyzes sprint backlog and generates suggestions:
- start_p0: P0 items not yet started (critical)
- unassigned_priority: Unassigned P0/P1 items
- overloaded: Sprint capacity exceeds velocity
- blocked: Items requiring unblocking
- p2_at_risk: Low-priority items at risk
- underloaded: Capacity opportunity

Args:
    sprint_id: Sprint UUID

Returns:
    SprintSuggestionsResponse with AI suggestions

Raises:
    404: Sprint not found

</details>

---

### 🔵 GET `/api/v1/planning/teams/{team_id}/capacity`

**Summary**: Get team capacity

<details>
<summary>View full description</summary>

Calculate team capacity for a date range.

**Sprint 78: Resource Allocation Optimization - Day 3 Implementation**

Returns:
- Total capacity hours for team
- Allocated hours
- Available hours
- Utilization rate (%)
- Breakdown by member
- Breakdown by role

</details>

---

### 🔵 GET `/api/v1/planning/teams/{team_id}/capacity`

**Summary**: Get team capacity

<details>
<summary>View full description</summary>

Calculate team capacity for a date range.

**Sprint 78: Resource Allocation Optimization - Day 3 Implementation**

Returns:
- Total capacity hours for team
- Allocated hours
- Available hours
- Utilization rate (%)
- Breakdown by member
- Breakdown by role

</details>

---

### 🟢 POST `/api/v1/planning/templates`

**Summary**: Create sprint template

<details>
<summary>View full description</summary>

Create a new sprint template.

**Sprint 78: Sprint Template Library - Day 4 Implementation**

Template types:
- **standard**: Standard 2-week sprint
- **feature**: Feature-focused sprint
- **bugfix**: Bug-fix focused sprint
- **release**: Release preparation sprint
- **custom**: Custom configuration

Templates can include:
- Default duration and capacity
- Pre-defined backlog structure
- Sprint goal template
- Gate configuration

Args:
    data: Template creation data

Returns:
    Created SprintTemplateResponse

</details>

---

### 🟢 POST `/api/v1/planning/templates`

**Summary**: Create sprint template

<details>
<summary>View full description</summary>

Create a new sprint template.

**Sprint 78: Sprint Template Library - Day 4 Implementation**

Template types:
- **standard**: Standard 2-week sprint
- **feature**: Feature-focused sprint
- **bugfix**: Bug-fix focused sprint
- **release**: Release preparation sprint
- **custom**: Custom configuration

Templates can include:
- Default duration and capacity
- Pre-defined backlog structure
- Sprint goal template
- Gate configuration

Args:
    data: Template creation data

Returns:
    Created SprintTemplateResponse

</details>

---

### 🔵 GET `/api/v1/planning/templates`

**Summary**: List sprint templates

<details>
<summary>View full description</summary>

List available sprint templates.

**Sprint 78: Sprint Template Library - Day 4 Implementation**

Filters:
- **team_id**: Team-specific templates
- **template_type**: Filter by type (standard, feature, bugfix, release, custom)
- **include_public**: Include public templates (default: true)

Returns paginated list sorted by:
1. Default templates first
2. Usage count (popularity)

</details>

---

### 🔵 GET `/api/v1/planning/templates`

**Summary**: List sprint templates

<details>
<summary>View full description</summary>

List available sprint templates.

**Sprint 78: Sprint Template Library - Day 4 Implementation**

Filters:
- **team_id**: Team-specific templates
- **template_type**: Filter by type (standard, feature, bugfix, release, custom)
- **include_public**: Include public templates (default: true)

Returns paginated list sorted by:
1. Default templates first
2. Usage count (popularity)

</details>

---

### 🟢 POST `/api/v1/planning/templates/bulk/delete`

**Summary**: Bulk delete templates


---

### 🟢 POST `/api/v1/planning/templates/bulk/delete`

**Summary**: Bulk delete templates


---

### 🔵 GET `/api/v1/planning/templates/default`

**Summary**: Get default template

**Description**: Get the default template for a team or organization.

Returns team-specific default if available, otherwise public default.

---

### 🔵 GET `/api/v1/planning/templates/default`

**Summary**: Get default template

**Description**: Get the default template for a team or organization.

Returns team-specific default if available, otherwise public default.

---

### 🔵 GET `/api/v1/planning/templates/{template_id}`

**Summary**: Get a sprint template


---

### 🔵 GET `/api/v1/planning/templates/{template_id}`

**Summary**: Get a sprint template


---

### 🟡 PUT `/api/v1/planning/templates/{template_id}`

**Summary**: Update a sprint template


---

### 🟡 PUT `/api/v1/planning/templates/{template_id}`

**Summary**: Update a sprint template


---

### 🔴 DELETE `/api/v1/planning/templates/{template_id}`

**Summary**: Delete a sprint template


---

### 🔴 DELETE `/api/v1/planning/templates/{template_id}`

**Summary**: Delete a sprint template


---

### 🟢 POST `/api/v1/planning/templates/{template_id}/apply`

**Summary**: Apply template to create sprint

<details>
<summary>View full description</summary>

Create a new sprint from a template.

**Sprint 78: Sprint Template Library - Day 4 Implementation**

Copies from template:
- Duration configuration
- Capacity points
- Gate settings
- Backlog structure (if include_backlog=true)

Can override:
- Sprint name
- Goal
- Team size

Args:
    template_id: Template to apply
    data: Apply template request

Returns:
    ApplyTemplateResponse with created sprint info

Raises:
    400: Validation error
    404: Template or project not found

</details>

---

### 🟢 POST `/api/v1/planning/templates/{template_id}/apply`

**Summary**: Apply template to create sprint

<details>
<summary>View full description</summary>

Create a new sprint from a template.

**Sprint 78: Sprint Template Library - Day 4 Implementation**

Copies from template:
- Duration configuration
- Capacity points
- Gate settings
- Backlog structure (if include_backlog=true)

Can override:
- Sprint name
- Goal
- Team size

Args:
    template_id: Template to apply
    data: Apply template request

Returns:
    ApplyTemplateResponse with created sprint info

Raises:
    400: Validation error
    404: Template or project not found

</details>

---

### 🔵 GET `/api/v1/planning/users/{user_id}/allocations`

**Summary**: List allocations for a user

**Description**: List all sprint allocations for a user.

Optionally filter by date range.

---

### 🔵 GET `/api/v1/planning/users/{user_id}/allocations`

**Summary**: List allocations for a user

**Description**: List all sprint allocations for a user.

Optionally filter by date range.

---

### 🔵 GET `/api/v1/planning/users/{user_id}/capacity`

**Summary**: Get user capacity

<details>
<summary>View full description</summary>

Calculate user capacity for a date range.

**Sprint 78: Resource Allocation Optimization - Day 3 Implementation**

Returns:
- Total working days in period
- Allocated days across sprints
- Available days
- Utilization rate (%)
- List of allocations

</details>

---

### 🔵 GET `/api/v1/planning/users/{user_id}/capacity`

**Summary**: Get user capacity

<details>
<summary>View full description</summary>

Calculate user capacity for a date range.

**Sprint 78: Resource Allocation Optimization - Day 3 Implementation**

Returns:
- Total working days in period
- Allocated days across sprints
- Available days
- Utilization rate (%)
- List of allocations

</details>

---

## Planning Sub-agent

### 🟢 POST `/api/v1/planning/subagent/conformance`

**Summary**: Check PR conformance

<details>
<summary>View full description</summary>

Check PR diff conformance against established patterns.

    This endpoint is designed for **GitHub CI integration**:
    1. Receives PR diff content
    2. Extracts patterns from codebase
    3. Analyzes diff for pattern violations
    4. Returns conformance score (0-100)

    **Score Levels**:
    - EXCELLENT (≥90): Auto-approve eligible
    - GOOD (≥70): Review recommended
    - FAIR (≥50): Review required
    - POOR (<50): Changes required

    Use in GitHub Actions:
    ```yaml
    - name: Check Conformance
      run: |
        curl -X POST .../conformance \
          -d '{"diff_content": "...", "project_path": "."}' \
          | jq '.score >= 70'
    ```

</details>

---

### 🟢 POST `/api/v1/planning/subagent/conformance`

**Summary**: Check PR conformance

<details>
<summary>View full description</summary>

Check PR diff conformance against established patterns.

    This endpoint is designed for **GitHub CI integration**:
    1. Receives PR diff content
    2. Extracts patterns from codebase
    3. Analyzes diff for pattern violations
    4. Returns conformance score (0-100)

    **Score Levels**:
    - EXCELLENT (≥90): Auto-approve eligible
    - GOOD (≥70): Review recommended
    - FAIR (≥50): Review required
    - POOR (<50): Changes required

    Use in GitHub Actions:
    ```yaml
    - name: Check Conformance
      run: |
        curl -X POST .../conformance \
          -d '{"diff_content": "...", "project_path": "."}' \
          | jq '.score >= 70'
    ```

</details>

---

### 🔵 GET `/api/v1/planning/subagent/health`

**Summary**: Health check


---

### 🔵 GET `/api/v1/planning/subagent/health`

**Summary**: Health check


---

### 🟢 POST `/api/v1/planning/subagent/plan`

**Summary**: Start planning session

<details>
<summary>View full description</summary>

Start a new planning session with sub-agent orchestration.

    This endpoint:
    1. Spawns 3-5 explore sub-agents (parallel)
    2. Extracts patterns from codebase, ADRs, tests
    3. Synthesizes implementation plan
    4. Calculates conformance score (0-100)
    5. Returns plan for human approval

    **Planning Mode is MANDATORY for changes >15 LOC** (SDLC 5.2.0)

    Performance: Typical response in <60s (p95)

</details>

---

### 🟢 POST `/api/v1/planning/subagent/plan`

**Summary**: Start planning session

<details>
<summary>View full description</summary>

Start a new planning session with sub-agent orchestration.

    This endpoint:
    1. Spawns 3-5 explore sub-agents (parallel)
    2. Extracts patterns from codebase, ADRs, tests
    3. Synthesizes implementation plan
    4. Calculates conformance score (0-100)
    5. Returns plan for human approval

    **Planning Mode is MANDATORY for changes >15 LOC** (SDLC 5.2.0)

    Performance: Typical response in <60s (p95)

</details>

---

### 🟢 POST `/api/v1/planning/subagent/plan/with-risk`

**Summary**: Start risk-based planning session (Sprint 101)

<details>
<summary>View full description</summary>

Start planning session with integrated risk analysis.

    **This is the recommended entry point for planning** (SDLC 5.2.0).

    This endpoint:
    1. Analyzes diff for 7 mandatory risk factors
    2. Determines planning requirement level
    3. Creates CRP if risk_score >= 70 (high-risk)
    4. Spawns explore sub-agents (parallel)
    5. Extracts patterns from codebase
    6. Generates implementation plan
    7. Returns result with risk analysis and optional CRP

    **Risk-Based Decisions**:
    - NOT_REQUIRED (risk < 20): Returns planning anyway for guidance
    - RECOMMENDED (risk 20-49): Standard planning
    - REQUIRED (risk 50-69): Mandatory planning, more thorough
    - REQUIRES_CRP (risk >= 70): CRP created, awaits human approval

    Performance: Typical response in <60s (p95)

</details>

---

### 🟢 POST `/api/v1/planning/subagent/plan/with-risk`

**Summary**: Start risk-based planning session (Sprint 101)

<details>
<summary>View full description</summary>

Start planning session with integrated risk analysis.

    **This is the recommended entry point for planning** (SDLC 5.2.0).

    This endpoint:
    1. Analyzes diff for 7 mandatory risk factors
    2. Determines planning requirement level
    3. Creates CRP if risk_score >= 70 (high-risk)
    4. Spawns explore sub-agents (parallel)
    5. Extracts patterns from codebase
    6. Generates implementation plan
    7. Returns result with risk analysis and optional CRP

    **Risk-Based Decisions**:
    - NOT_REQUIRED (risk < 20): Returns planning anyway for guidance
    - RECOMMENDED (risk 20-49): Standard planning
    - REQUIRED (risk 50-69): Mandatory planning, more thorough
    - REQUIRES_CRP (risk >= 70): CRP created, awaits human approval

    Performance: Typical response in <60s (p95)

</details>

---

### 🔵 GET `/api/v1/planning/subagent/sessions`

**Summary**: List planning sessions

**Description**: List all active planning sessions for the current user.

---

### 🔵 GET `/api/v1/planning/subagent/sessions`

**Summary**: List planning sessions

**Description**: List all active planning sessions for the current user.

---

### 🟢 POST `/api/v1/planning/subagent/should-plan`

**Summary**: Check if planning is required

<details>
<summary>View full description</summary>

Quick check if planning mode is required based on 7 mandatory risk factors.

    **This replaces the simple ">15 LOC" heuristic** (SDLC 5.2.0).

    Risk factors analyzed:
    - DATA_SCHEMA: Database/schema changes
    - API_CONTRACT: API signature changes
    - AUTH: Authentication/authorization changes
    - CROSS_SERVICE: Cross-service dependencies
    - CONCURRENCY: Threading/async patterns
    - SECURITY: Security-sensitive code
    - PUBLIC_API: Public API changes

    **Planning Decisions**:
    - NOT_REQUIRED (risk < 20): Simple changes, no planning needed
    - RECOMMENDED (risk 20-49): Planning suggested
    - REQUIRED (risk 50-69): Planning mandatory
    - REQUIRES_CRP (risk >= 70): Human oversight required

    Performance: <500ms (p95)

</details>

---

### 🟢 POST `/api/v1/planning/subagent/should-plan`

**Summary**: Check if planning is required

<details>
<summary>View full description</summary>

Quick check if planning mode is required based on 7 mandatory risk factors.

    **This replaces the simple ">15 LOC" heuristic** (SDLC 5.2.0).

    Risk factors analyzed:
    - DATA_SCHEMA: Database/schema changes
    - API_CONTRACT: API signature changes
    - AUTH: Authentication/authorization changes
    - CROSS_SERVICE: Cross-service dependencies
    - CONCURRENCY: Threading/async patterns
    - SECURITY: Security-sensitive code
    - PUBLIC_API: Public API changes

    **Planning Decisions**:
    - NOT_REQUIRED (risk < 20): Simple changes, no planning needed
    - RECOMMENDED (risk 20-49): Planning suggested
    - REQUIRED (risk 50-69): Planning mandatory
    - REQUIRES_CRP (risk >= 70): Human oversight required

    Performance: <500ms (p95)

</details>

---

### 🔵 GET `/api/v1/planning/subagent/{planning_id}`

**Summary**: Get planning result


---

### 🔵 GET `/api/v1/planning/subagent/{planning_id}`

**Summary**: Get planning result


---

### 🟢 POST `/api/v1/planning/subagent/{planning_id}/approve`

**Summary**: Approve or reject plan

<details>
<summary>View full description</summary>

Approve or reject a planning session.

    **Human oversight is required** for plan approval (SDLC 5.2.0).
    AI agents cannot approve plans - only SE4H (human coach) can.

    On approval:
    - Plan status changes to APPROVED
    - Implementation can proceed

    On rejection:
    - Plan status changes to REJECTED
    - Notes explain required changes

</details>

---

### 🟢 POST `/api/v1/planning/subagent/{planning_id}/approve`

**Summary**: Approve or reject plan

<details>
<summary>View full description</summary>

Approve or reject a planning session.

    **Human oversight is required** for plan approval (SDLC 5.2.0).
    AI agents cannot approve plans - only SE4H (human coach) can.

    On approval:
    - Plan status changes to APPROVED
    - Implementation can proceed

    On rejection:
    - Plan status changes to REJECTED
    - Notes explain required changes

</details>

---

## Policies

### 🔵 GET `/api/v1/policies`

**Summary**: List policies

<details>
<summary>View full description</summary>

List policies from policy pack library with filters.

    **Query Parameters**:
    - stage: Filter by SDLC stage (WHY, WHAT, BUILD, etc.)
    - is_active: Filter by active status (default: true)
    - page: Page number (default: 1)
    - page_size: Items per page (default: 20, max: 100)

    **Response** (200 OK):
    - Paginated list of policies
    - Total count and pages

</details>

---

### 🟢 POST `/api/v1/policies/evaluate`

**Summary**: Evaluate policy

<details>
<summary>View full description</summary>

Evaluate a policy against a gate with custom input data.

    **Week 4 Day 4 - REAL OPA Integration** ✅:
    - OPA evaluation via REST API (http://opa:8181)
    - Real Rego policy execution
    - Violation detection and tracking
    - Timeout handling (5s fail-safe)

    **Request Body**:
    - gate_id: Gate UUID
    - policy_id: Policy UUID
    - input_data: JSON input data for policy evaluation

    **Response** (201 Created):
    - Policy evaluation result (pass/fail)
    - List of violations (if failed)
    - Execution metadata (response time, etc.)

</details>

---

### 🔵 GET `/api/v1/policies/evaluations/{gate_id}`

**Summary**: Get policy evaluations for gate

**Description**: Get all policy evaluation results for a specific gate.

    **Response** (200 OK):
    - List of policy evaluations
    - Total evaluations, passed, failed, pass rate

---

### 🔵 GET `/api/v1/policies/{policy_id}`

**Summary**: Get policy details

<details>
<summary>View full description</summary>

Get policy details by ID.

    **Response** (200 OK):
    - Policy metadata with Rego code
    - Policy severity and version

    **Response** (404 Not Found):
    - Policy not found

</details>

---

### 🟡 PUT `/api/v1/policies/{policy_id}`

**Summary**: Update policy

<details>
<summary>View full description</summary>

Update an existing policy.

    **Design Reference**: API-CHANGELOG.md v1.0.0
    - Version history tracking
    - Partial updates supported

    **Request Body** (partial update):
    - policy_name: Updated name (optional)
    - description: Updated description (optional)
    - rego_code: Updated Rego code (optional)
    - severity: INFO | WARNING | ERROR | CRITICAL (optional)
    - is_active: Active status (optional)
    - version: Semantic version e.g. "1.0.1" (optional)

    **Response** (200 OK):
    - Updated policy details

    **Response** (404 Not Found):
    - Policy not found

</details>

---

## Policy Packs

### 🔵 GET `/api/v1/projects/{project_id}/policy-pack`

**Summary**: Get project's policy pack

<details>
<summary>View full description</summary>

Get the policy pack configuration for a project.

    **Response** (200 OK):
    - Policy pack with all rules
    - Validator configuration
    - Architecture rules

    **Response** (404 Not Found):
    - Project has no policy pack configured

</details>

---

### 🟢 POST `/api/v1/projects/{project_id}/policy-pack`

**Summary**: Create or update policy pack

<details>
<summary>View full description</summary>

Create or update the policy pack for a project.

    **Request Body**:
    - name: Pack name
    - description: Pack description
    - version: Semantic version (e.g., "1.0.0")
    - tier: SDLC tier (lite, standard, professional, enterprise)
    - validators: Validator pipeline configuration
    - coverage_threshold: Min test coverage (0-100)
    - forbidden_imports: AGPL imports to block
    - policies: Custom OPA policies

    **Response** (201 Created):
    - Created/updated policy pack

</details>

---

### 🔴 DELETE `/api/v1/projects/{project_id}/policy-pack`

**Summary**: Delete policy pack

<details>
<summary>View full description</summary>

Delete the policy pack for a project.

    **Response** (204 No Content):
    - Policy pack deleted

    **Response** (404 Not Found):
    - Project has no policy pack

</details>

---

### 🟢 POST `/api/v1/projects/{project_id}/policy-pack/evaluate`

**Summary**: Evaluate policies

<details>
<summary>View full description</summary>

Evaluate all enabled policies against provided files.

    **Request Body**:
    - files: List of files with path and content
    - diff: Unified diff (optional)

    **Response** (200 OK):
    - Evaluation results for each policy
    - Pass/fail status
    - Violation details

</details>

---

### 🟢 POST `/api/v1/projects/{project_id}/policy-pack/init`

**Summary**: Initialize default policy pack

<details>
<summary>View full description</summary>

Create a default policy pack with AI safety policies.

    **Query Parameters**:
    - tier: SDLC tier (lite, standard, professional, enterprise)
          Default: standard

    **Default Policies**:
    - no-hardcoded-secrets: Detect secrets in code
    - architecture-boundaries: Enforce 4-layer architecture
    - no-forbidden-imports: Block AGPL imports

    **Response** (201 Created):
    - Created policy pack with default policies

</details>

---

### 🟢 POST `/api/v1/projects/{project_id}/policy-pack/rules`

**Summary**: Add policy rule

<details>
<summary>View full description</summary>

Add a custom policy rule to the project's policy pack.

    **Request Body**:
    - policy_id: Unique identifier (kebab-case)
    - name: Human-readable name
    - description: What the policy checks
    - rego_policy: OPA Rego code
    - severity: critical, high, medium, low, info
    - blocking: If true, violations block merge
    - message_template: Message on failure ({file}, {line} placeholders)
    - tags: Categorization tags

    **Response** (201 Created):
    - Created policy rule

</details>

---

### 🟡 PUT `/api/v1/projects/{project_id}/policy-pack/rules/{policy_id}`

**Summary**: Update policy rule

<details>
<summary>View full description</summary>

Update an existing policy rule.

    **Path Parameters**:
    - project_id: Project UUID
    - policy_id: Policy identifier (e.g., "no-hardcoded-secrets")

    **Request Body** (all fields optional):
    - name: Updated name
    - description: Updated description
    - rego_policy: Updated Rego code
    - severity: Updated severity
    - blocking: Updated blocking status
    - enabled: Enable/disable rule

    **Response** (200 OK):
    - Updated policy rule

</details>

---

### 🔴 DELETE `/api/v1/projects/{project_id}/policy-pack/rules/{policy_id}`

**Summary**: Delete policy rule

<details>
<summary>View full description</summary>

Delete a policy rule from the project's pack.

    **Path Parameters**:
    - project_id: Project UUID
    - policy_id: Policy identifier

    **Response** (204 No Content):
    - Rule deleted

    **Response** (404 Not Found):
    - Rule not found

</details>

---

## Preview

### 🔵 GET `/api/v1/codegen/preview/{token}`

**Summary**: Get Preview

<details>
<summary>View full description</summary>

Get preview content by token.

Sprint 51B: Public endpoint (no auth required)

This endpoint is public so preview links can be shared without login.

Args:
    token: Preview token from URL
    password: Password if preview is protected

Returns:
    PreviewContent with files and metadata

Raises:
    404: Preview not found or expired
    401: Password required or invalid

</details>

---

### 🔵 GET `/api/v1/codegen/preview/{token}`

**Summary**: Get Preview

<details>
<summary>View full description</summary>

Get preview content by token.

Sprint 51B: Public endpoint (no auth required)

This endpoint is public so preview links can be shared without login.

Args:
    token: Preview token from URL
    password: Password if preview is protected

Returns:
    PreviewContent with files and metadata

Raises:
    404: Preview not found or expired
    401: Password required or invalid

</details>

---

### 🔴 DELETE `/api/v1/codegen/preview/{token}`

**Summary**: Delete Preview

<details>
<summary>View full description</summary>

Delete a preview before expiration.

Args:
    token: Preview token to delete

Returns:
    Success message

Raises:
    404: Preview not found
    403: User not authorized

</details>

---

### 🔴 DELETE `/api/v1/codegen/preview/{token}`

**Summary**: Delete Preview

<details>
<summary>View full description</summary>

Delete a preview before expiration.

Args:
    token: Preview token to delete

Returns:
    Success message

Raises:
    404: Preview not found
    403: User not authorized

</details>

---

### 🟢 POST `/api/v1/codegen/sessions/{session_id}/preview`

**Summary**: Create Preview

<details>
<summary>View full description</summary>

Create a shareable preview URL for generated code.

Sprint 51B: QR Mobile Preview Feature

Creates a preview link that can be shared via QR code.
Preview links expire after the specified duration (default 24h).

Args:
    session_id: UUID of the generation session
    request: Preview options (password, expiration)

Returns:
    PreviewResponse with URL and QR code image data

Raises:
    404: Session not found
    403: User not authorized
    400: No files to preview

</details>

---

### 🟢 POST `/api/v1/codegen/sessions/{session_id}/preview`

**Summary**: Create Preview

<details>
<summary>View full description</summary>

Create a shareable preview URL for generated code.

Sprint 51B: QR Mobile Preview Feature

Creates a preview link that can be shared via QR code.
Preview links expire after the specified duration (default 24h).

Args:
    session_id: UUID of the generation session
    request: Preview options (password, expiration)

Returns:
    PreviewResponse with URL and QR code image data

Raises:
    404: Session not found
    403: User not authorized
    400: No files to preview

</details>

---

## Projects

### 🟢 POST `/api/v1/projects`

**Summary**: Create Project

<details>
<summary>View full description</summary>

Create a new project with optional policy pack configuration.

The current user becomes the project owner.

Args:
    data: ProjectCreate schema with name, description, policy_pack, and optional GitHub fields

Returns:
    Created project with ID, slug, and policy pack tier

ADR-027 Phase 2:
    Enforces max_projects_per_user limit from system settings.

</details>

---

### 🔵 GET `/api/v1/projects`

**Summary**: List Projects

<details>
<summary>View full description</summary>

List all projects with gate status summary.

Sprint 23 Day 2 Optimization:
- Changed from N+1 queries to single query with subqueries
- Performance improvement: ~200ms -> ~50ms (75% faster)
- Added Redis caching (60s TTL) for further optimization

</details>

---

### 🟢 POST `/api/v1/projects/init`

**Summary**: Initialize SDLC project

**Description**: Initialize a new SDLC 6.0.6 project. Creates project in database and returns configuration for .sdlc-config.json. Per RFC-001, creates 10-archive/ folder (no 99-Legacy/ in active stages 00-09).

---

### 🔵 GET `/api/v1/projects/{project_id}`

**Summary**: Get Project


---

### 🟡 PUT `/api/v1/projects/{project_id}`

**Summary**: Update Project

**Description**: Update a project.

Only project owners and admins can update projects.

---

### 🔴 DELETE `/api/v1/projects/{project_id}`

**Summary**: Delete Project

**Description**: Delete a project (soft delete).

Only project owners can delete projects.

---

### 🟡 PUT `/api/v1/projects/{project_id}/context`

**Summary**: Update project context (stage, gate, sprint)

<details>
<summary>View full description</summary>

Update the current SDLC context for a project.
    
    **SSOT Principle (Sprint 136)**:
    - Database is the Single Source of Truth
    - Extension/Dashboard READ from this data
    - Admin UI/CLI WRITE via this endpoint
    
    **Valid Stages**: FOUNDATION, PLANNING, DESIGN, INTEGRATE, BUILD, TEST, DEPLOY, OPERATE, GOVERN, ARCHIVE
    **Valid Gates**: G0.1, G0.2, G1, G2, G3, G4, G5, G6, G7, G8, G9

</details>

---

### 🔵 GET `/api/v1/projects/{project_id}/context`

**Summary**: Get project context (stage, gate, sprint)

**Description**: Get the current SDLC context for a project (SSOT read endpoint).

---

### 🟢 POST `/api/v1/projects/{project_id}/migrate-stages`

**Summary**: Migrate project stages to SDLC 6.0.6

**Description**: Migrate project from old stage structure to SDLC 6.0.6. Includes RFC-001 legacy archive migration (99-Legacy/ → 10-archive/{NN}-Legacy/). Moves INTEGRATE from stage 07 to stage 03.

---

## Resource Allocation

### 🟢 POST `/api/v1/planning/allocations`

**Summary**: Create resource allocation

<details>
<summary>View full description</summary>

Allocate a team member to a sprint.

**Sprint 78: Resource Allocation Optimization - Day 3 Implementation**

Allocation validation:
- User must exist
- Sprint must exist
- No duplicate allocation (user to same sprint)
- Allocation percentage between 1-100%
- Dates must be within sprint range
- Total allocation across sprints cannot exceed 100%

Args:
    data: Allocation creation data

Returns:
    Created ResourceAllocationResponse

Raises:
    400: Validation error or conflict detected
    404: Sprint or user not found

</details>

---

### 🟢 POST `/api/v1/planning/allocations/check-conflicts`

**Summary**: Check allocation conflicts

<details>
<summary>View full description</summary>

Check if an allocation would create conflicts.

**Sprint 78: Resource Allocation Optimization - Day 3 Implementation**

Use this endpoint before creating/updating an allocation to validate.

Returns:
- Whether conflicts exist
- List of conflicts with details
- Warnings for high utilization

</details>

---

### 🔵 GET `/api/v1/planning/allocations/{allocation_id}`

**Summary**: Get a resource allocation

**Description**: Get a single allocation with user and sprint details.

---

### 🟡 PUT `/api/v1/planning/allocations/{allocation_id}`

**Summary**: Update a resource allocation


---

### 🔴 DELETE `/api/v1/planning/allocations/{allocation_id}`

**Summary**: Delete a resource allocation


---

### 🔵 GET `/api/v1/planning/projects/{project_id}/resource-heatmap`

**Summary**: Get resource allocation heatmap

<details>
<summary>View full description</summary>

Get resource allocation heatmap for visualization.

**Sprint 78: Resource Allocation Optimization - Day 3 Implementation**

Returns a heatmap structure with:
- **users**: List of users with allocations
- **sprints**: List of sprints
- **cells**: Allocation data for each user-sprint combination

Suitable for rendering with visualization libraries.

Cell status values:
- **available**: No allocation (0%)
- **partial**: Partial allocation (1-99%)
- **full**: Full allocation (100%)
- **over_allocated**: Over-allocated (>100%)

</details>

---

### 🔵 GET `/api/v1/planning/sprints/{sprint_id}/allocations`

**Summary**: List allocations for a sprint

**Description**: List all team member allocations for a sprint.

Returns paginated list of allocations with user details.

---

### 🔵 GET `/api/v1/planning/sprints/{sprint_id}/capacity`

**Summary**: Get sprint capacity

<details>
<summary>View full description</summary>

Calculate capacity for a sprint.

**Sprint 78: Resource Allocation Optimization - Day 3 Implementation**

Returns:
- Team size (allocated members)
- Total capacity hours
- Allocated hours
- Available hours
- Utilization rate (%)
- Breakdown by role

</details>

---

### 🔵 GET `/api/v1/planning/teams/{team_id}/capacity`

**Summary**: Get team capacity

<details>
<summary>View full description</summary>

Calculate team capacity for a date range.

**Sprint 78: Resource Allocation Optimization - Day 3 Implementation**

Returns:
- Total capacity hours for team
- Allocated hours
- Available hours
- Utilization rate (%)
- Breakdown by member
- Breakdown by role

</details>

---

### 🔵 GET `/api/v1/planning/users/{user_id}/allocations`

**Summary**: List allocations for a user

**Description**: List all sprint allocations for a user.

Optionally filter by date range.

---

### 🔵 GET `/api/v1/planning/users/{user_id}/capacity`

**Summary**: Get user capacity

<details>
<summary>View full description</summary>

Calculate user capacity for a date range.

**Sprint 78: Resource Allocation Optimization - Day 3 Implementation**

Returns:
- Total working days in period
- Allocated days across sprints
- Available days
- Utilization rate (%)
- List of allocations

</details>

---

## Retrospective

### 🟢 POST `/api/v1/planning/action-items/bulk/status`

**Summary**: Bulk update action item status


---

### 🔵 GET `/api/v1/planning/action-items/{item_id}`

**Summary**: Get a single action item


---

### 🟡 PUT `/api/v1/planning/action-items/{item_id}`

**Summary**: Update an action item

<details>
<summary>View full description</summary>

Update an action item.

Status transitions:
- open -> in_progress (when assigned)
- in_progress -> completed (manual)
- Any -> cancelled (manual)

</details>

---

### 🔴 DELETE `/api/v1/planning/action-items/{item_id}`

**Summary**: Delete an action item


---

### 🔵 GET `/api/v1/planning/projects/{project_id}/retrospective-comparison`

**Summary**: Compare retrospectives across sprints

<details>
<summary>View full description</summary>

Compare retrospectives across multiple sprints.

**Sprint 78: Retrospective Enhancement - Day 1 Implementation**

Compares key metrics across selected sprints:
- Completion rates
- P0 completion rates
- Blocked item trends
- Velocity trends
- Action item completion rates

Args:
    project_id: Project UUID
    sprint_ids: Comma-separated sprint UUIDs (2-5 sprints)

Returns:
    Comparison data with metrics for each sprint

</details>

---

### 🟢 POST `/api/v1/planning/sprints/{sprint_id}/action-items`

**Summary**: Create action item from retrospective

<details>
<summary>View full description</summary>

Create a new action item from sprint retrospective.

**Sprint 78: Retrospective Enhancement - Day 1 Implementation**

Action items track concrete next steps identified during sprint retrospectives.
Supports:
- Category classification (delivery, priority, velocity, etc.)
- Priority levels (low, medium, high)
- Assignment to team members
- Cross-sprint tracking via due_sprint_id

Args:
    sprint_id: Sprint UUID (source sprint)
    data: Action item data

Returns:
    Created RetroActionItemResponse

Raises:
    404: Sprint not found
    403: No write access to project

</details>

---

### 🔵 GET `/api/v1/planning/sprints/{sprint_id}/action-items`

**Summary**: List action items for a sprint

<details>
<summary>View full description</summary>

List action items for a sprint retrospective.

**Sprint 78: Retrospective Enhancement - Day 1 Implementation**

Supports filtering by:
- status: open, in_progress, completed, cancelled
- category: delivery, priority, velocity, planning, scope, blockers, team, general
- priority: low, medium, high
- assignee_id: User UUID

Args:
    sprint_id: Sprint UUID
    Various filters

Returns:
    Paginated list of action items

</details>

---

### 🟢 POST `/api/v1/planning/sprints/{sprint_id}/action-items/bulk`

**Summary**: Bulk create action items

**Description**: Bulk create action items from retrospective.

Useful for importing action items generated by retrospective automation.

---

### 🔵 GET `/api/v1/planning/sprints/{sprint_id}/action-items/stats`

**Summary**: Get action items statistics

**Description**: Get statistics for action items in a sprint retrospective.

Returns counts by status, category, and priority.

---

## Risk Analysis

### 🟢 POST `/api/v1/risk/analyze`

**Summary**: Analyze diff for risk factors

**Description**: Perform full risk analysis on a git diff. Detects 7 mandatory risk factors and calculates risk score.

---

### 🟢 POST `/api/v1/risk/analyze`

**Summary**: Analyze diff for risk factors

**Description**: Perform full risk analysis on a git diff. Detects 7 mandatory risk factors and calculates risk score.

---

### 🔵 GET `/api/v1/risk/factors`

**Summary**: List 7 mandatory risk factors

**Description**: Get information about the 7 mandatory risk factors from SDLC 5.2.0.

---

### 🔵 GET `/api/v1/risk/factors`

**Summary**: List 7 mandatory risk factors

**Description**: Get information about the 7 mandatory risk factors from SDLC 5.2.0.

---

### 🔵 GET `/api/v1/risk/levels`

**Summary**: Get risk level thresholds


---

### 🔵 GET `/api/v1/risk/levels`

**Summary**: Get risk level thresholds


---

### 🔵 GET `/api/v1/risk/should-plan`

**Summary**: Quick check if planning is needed

**Description**: Lightweight check for planning trigger. Use for CI/CD integration.

---

### 🔵 GET `/api/v1/risk/should-plan`

**Summary**: Quick check if planning is needed

**Description**: Lightweight check for planning trigger. Use for CI/CD integration.

---

## SAST

### 🔵 GET `/api/v1/sast/health`

**Summary**: SAST health check


---

### 🔵 GET `/api/v1/sast/health`

**Summary**: SAST health check


---

### 🔵 GET `/api/v1/sast/projects/{project_id}/analytics`

**Summary**: Get SAST analytics


---

### 🔵 GET `/api/v1/sast/projects/{project_id}/analytics`

**Summary**: Get SAST analytics


---

### 🟢 POST `/api/v1/sast/projects/{project_id}/scan`

**Summary**: Initiate SAST scan

**Description**: Start a static application security testing scan for a project

---

### 🟢 POST `/api/v1/sast/projects/{project_id}/scan`

**Summary**: Initiate SAST scan

**Description**: Start a static application security testing scan for a project

---

### 🔵 GET `/api/v1/sast/projects/{project_id}/scans`

**Summary**: Get scan history


---

### 🔵 GET `/api/v1/sast/projects/{project_id}/scans`

**Summary**: Get scan history


---

### 🔵 GET `/api/v1/sast/projects/{project_id}/scans/{scan_id}`

**Summary**: Get scan details


---

### 🔵 GET `/api/v1/sast/projects/{project_id}/scans/{scan_id}`

**Summary**: Get scan details


---

### 🔵 GET `/api/v1/sast/projects/{project_id}/trend`

**Summary**: Get findings trend


---

### 🔵 GET `/api/v1/sast/projects/{project_id}/trend`

**Summary**: Get findings trend


---

### 🟢 POST `/api/v1/sast/scan-snippet`

**Summary**: Scan code snippet


---

### 🟢 POST `/api/v1/sast/scan-snippet`

**Summary**: Scan code snippet


---

## SDLC Structure

### 🔵 GET `/api/v1/projects/{project_id}/compliance-summary`

**Summary**: Get compliance summary


---

### 🔵 GET `/api/v1/projects/{project_id}/compliance-summary`

**Summary**: Get compliance summary


---

### 🟢 POST `/api/v1/projects/{project_id}/validate-structure`

**Summary**: Validate SDLC 5.0.0 structure

**Description**: Validate project documentation structure against SDLC 5.0.0 standards.

---

### 🟢 POST `/api/v1/projects/{project_id}/validate-structure`

**Summary**: Validate SDLC 5.0.0 structure

**Description**: Validate project documentation structure against SDLC 5.0.0 standards.

---

### 🔵 GET `/api/v1/projects/{project_id}/validation-history`

**Summary**: Get validation history

**Description**: Get SDLC structure validation history for a project.

---

### 🔵 GET `/api/v1/projects/{project_id}/validation-history`

**Summary**: Get validation history

**Description**: Get SDLC structure validation history for a project.

---

## SOP Generator

### 🟢 POST `/api/v1/sop/generate`

**Summary**: Generate SOP from workflow description

<details>
<summary>View full description</summary>

Generate a Standard Operating Procedure (SOP) using AI (FR1).

    This endpoint:
    1. Takes a workflow description and SOP type
    2. Generates complete SOP with 5 mandatory sections (FR2)
    3. Creates MRP evidence automatically (FR6)
    4. Returns SOP ready for VCR approval (FR7)

    Performance: Target <30 seconds generation time (NFR1)

</details>

---

### 🟢 POST `/api/v1/sop/generate`

**Summary**: Generate SOP from workflow description

<details>
<summary>View full description</summary>

Generate a Standard Operating Procedure (SOP) using AI (FR1).

    This endpoint:
    1. Takes a workflow description and SOP type
    2. Generates complete SOP with 5 mandatory sections (FR2)
    3. Creates MRP evidence automatically (FR6)
    4. Returns SOP ready for VCR approval (FR7)

    Performance: Target <30 seconds generation time (NFR1)

</details>

---

### 🔵 GET `/api/v1/sop/health`

**Summary**: SOP Generator health check


---

### 🔵 GET `/api/v1/sop/health`

**Summary**: SOP Generator health check


---

### 🔵 GET `/api/v1/sop/list`

**Summary**: List generated SOPs

**Description**: Get paginated list of generated SOPs for history view (M4)

---

### 🔵 GET `/api/v1/sop/list`

**Summary**: List generated SOPs

**Description**: Get paginated list of generated SOPs for history view (M4)

---

### 🔵 GET `/api/v1/sop/types`

**Summary**: List supported SOP types


---

### 🔵 GET `/api/v1/sop/types`

**Summary**: List supported SOP types


---

### 🔵 GET `/api/v1/sop/{sop_id}`

**Summary**: Get SOP details


---

### 🔵 GET `/api/v1/sop/{sop_id}`

**Summary**: Get SOP details


---

### 🔵 GET `/api/v1/sop/{sop_id}/mrp`

**Summary**: Get MRP evidence for SOP

**Description**: Retrieve Merge-Readiness Pack evidence for a generated SOP (FR6)

---

### 🔵 GET `/api/v1/sop/{sop_id}/mrp`

**Summary**: Get MRP evidence for SOP

**Description**: Retrieve Merge-Readiness Pack evidence for a generated SOP (FR6)

---

### 🟢 POST `/api/v1/sop/{sop_id}/vcr`

**Summary**: Submit VCR decision for SOP

<details>
<summary>View full description</summary>

Submit Version Controlled Resolution (VCR) decision for SOP approval (FR7).

    Decision options:
    - approved: SOP is approved for use
    - rejected: SOP is rejected (needs new generation)
    - revision_required: SOP needs modifications

    Quality rating (1-5) is optional but recommended (NFR2: target ≥4)

</details>

---

### 🟢 POST `/api/v1/sop/{sop_id}/vcr`

**Summary**: Submit VCR decision for SOP

<details>
<summary>View full description</summary>

Submit Version Controlled Resolution (VCR) decision for SOP approval (FR7).

    Decision options:
    - approved: SOP is approved for use
    - rejected: SOP is rejected (needs new generation)
    - revision_required: SOP needs modifications

    Quality rating (1-5) is optional but recommended (NFR2: target ≥4)

</details>

---

### 🔵 GET `/api/v1/sop/{sop_id}/vcr`

**Summary**: Get VCR decision for SOP

**Description**: Retrieve Version Controlled Resolution decision for SOP (FR7)

---

### 🔵 GET `/api/v1/sop/{sop_id}/vcr`

**Summary**: Get VCR decision for SOP

**Description**: Retrieve Version Controlled Resolution decision for SOP (FR7)

---

## Sprint 77

### 🔵 GET `/api/v1/planning/sprints/{sprint_id}/burndown`

**Summary**: Get sprint burndown chart data

<details>
<summary>View full description</summary>

Get burndown chart data for a sprint.

**Sprint 77: Burndown Charts - Day 2 Implementation**

Generates burndown chart data including:
- Ideal burndown line (linear from total points to 0)
- Actual burndown line (based on completed items)
- Progress metrics (completion rate, days remaining)
- On-track indicator (actual vs ideal comparison)

Performance Budget:
- Query time: <50ms
- Calculation time: <20ms
- Total response: <100ms p95

Args:
    sprint_id: Sprint UUID

Returns:
    BurndownChartResponse with ideal and actual burndown data

Raises:
    404: Sprint not found
    400: Sprint has no start/end dates

</details>

---

### 🔵 GET `/api/v1/planning/sprints/{sprint_id}/forecast`

**Summary**: Get sprint completion forecast

<details>
<summary>View full description</summary>

Get sprint completion forecast with probability and risks.

**Sprint 77: Sprint Forecasting - Day 3 Implementation**

Predicts sprint completion probability based on:
- Current vs required burn rate
- Blocked items penalty (-5% each)
- Incomplete P0 items penalty (-10% each)
- Days remaining urgency factor

Returns:
- Completion probability (0-100%)
- Predicted end date
- On-track indicator
- Identified risks with severity
- AI-generated recommendations

Performance Budget:
- Query time: <50ms
- Calculation time: <30ms
- Total response: <100ms p95

Args:
    sprint_id: Sprint UUID

Returns:
    SprintForecastResponse with probability, risks, and recommendations

Raises:
    404: Sprint not found

*(truncated for brevity)*

</details>

---

### 🔵 GET `/api/v1/planning/sprints/{sprint_id}/retrospective`

**Summary**: Get auto-generated sprint retrospective

<details>
<summary>View full description</summary>

Get auto-generated sprint retrospective.

**Sprint 77: Retrospective Automation - Day 4 Implementation**

Analyzes sprint performance and generates:
- Metrics summary (completion rate, P0 status, blocked items)
- "Went well" insights (positive patterns)
- "Needs improvement" insights (areas for growth)
- Action items (concrete next steps)
- Executive summary

Insight Categories:
- delivery: Completion and delivery performance
- priority: P0/P1 focus and completion
- velocity: Velocity trends (improving/stable/declining)
- planning: Sprint planning accuracy
- scope: Scope changes and creep
- blockers: Blocked items management

Performance Budget:
- Query time: <50ms
- Analysis time: <30ms
- Total response: <100ms p95

Args:
    sprint_id: Sprint UUID

Returns:
    SprintRetrospectiveResponse with metrics, insights, and actions


*(truncated for brevity)*

</details>

---

## Sprint 78

### 🟢 POST `/api/v1/planning/action-items/bulk/status`

**Summary**: Bulk update action item status


---

### 🔵 GET `/api/v1/planning/action-items/{item_id}`

**Summary**: Get a single action item


---

### 🟡 PUT `/api/v1/planning/action-items/{item_id}`

**Summary**: Update an action item

<details>
<summary>View full description</summary>

Update an action item.

Status transitions:
- open -> in_progress (when assigned)
- in_progress -> completed (manual)
- Any -> cancelled (manual)

</details>

---

### 🔴 DELETE `/api/v1/planning/action-items/{item_id}`

**Summary**: Delete an action item


---

### 🟢 POST `/api/v1/planning/allocations`

**Summary**: Create resource allocation

<details>
<summary>View full description</summary>

Allocate a team member to a sprint.

**Sprint 78: Resource Allocation Optimization - Day 3 Implementation**

Allocation validation:
- User must exist
- Sprint must exist
- No duplicate allocation (user to same sprint)
- Allocation percentage between 1-100%
- Dates must be within sprint range
- Total allocation across sprints cannot exceed 100%

Args:
    data: Allocation creation data

Returns:
    Created ResourceAllocationResponse

Raises:
    400: Validation error or conflict detected
    404: Sprint or user not found

</details>

---

### 🟢 POST `/api/v1/planning/allocations/check-conflicts`

**Summary**: Check allocation conflicts

<details>
<summary>View full description</summary>

Check if an allocation would create conflicts.

**Sprint 78: Resource Allocation Optimization - Day 3 Implementation**

Use this endpoint before creating/updating an allocation to validate.

Returns:
- Whether conflicts exist
- List of conflicts with details
- Warnings for high utilization

</details>

---

### 🔵 GET `/api/v1/planning/allocations/{allocation_id}`

**Summary**: Get a resource allocation

**Description**: Get a single allocation with user and sprint details.

---

### 🟡 PUT `/api/v1/planning/allocations/{allocation_id}`

**Summary**: Update a resource allocation


---

### 🔴 DELETE `/api/v1/planning/allocations/{allocation_id}`

**Summary**: Delete a resource allocation


---

### 🟢 POST `/api/v1/planning/dependencies`

**Summary**: Create sprint dependency

<details>
<summary>View full description</summary>

Create a dependency between two sprints.

**Sprint 78: Cross-Project Sprint Dependencies - Day 2 Implementation**

Dependency types:
- **blocks**: Source sprint is blocked until target completes (critical)
- **requires**: Source requires deliverable from target
- **related**: Sprints are related but not blocking

Validation:
- Both sprints must exist
- No self-reference allowed
- Circular dependencies are prevented

Args:
    data: Dependency creation data

Returns:
    Created SprintDependencyResponse

Raises:
    400: Invalid dependency (circular, self-reference, duplicate)
    404: Sprint not found

</details>

---

### 🟢 POST `/api/v1/planning/dependencies/bulk/resolve`

**Summary**: Bulk resolve dependencies


---

### 🔵 GET `/api/v1/planning/dependencies/check-circular`

**Summary**: Check for circular dependency

**Description**: Check if adding a dependency would create a cycle.

Use this endpoint before creating a dependency to validate.

---

### 🔵 GET `/api/v1/planning/dependencies/{dependency_id}`

**Summary**: Get a sprint dependency


---

### 🟡 PUT `/api/v1/planning/dependencies/{dependency_id}`

**Summary**: Update a sprint dependency

**Description**: Update a dependency's type, description, or status.

---

### 🔴 DELETE `/api/v1/planning/dependencies/{dependency_id}`

**Summary**: Delete a sprint dependency


---

### 🟢 POST `/api/v1/planning/dependencies/{dependency_id}/resolve`

**Summary**: Resolve a sprint dependency


---

### 🔵 GET `/api/v1/planning/projects/{project_id}/dependency-analysis`

**Summary**: Analyze project dependencies

<details>
<summary>View full description</summary>

Analyze dependency structure for a project.

Returns:
- Dependency counts by type and status
- Critical path through dependency chain
- Risk indicators (high-dependency sprints)

</details>

---

### 🔵 GET `/api/v1/planning/projects/{project_id}/dependency-graph`

**Summary**: Get dependency graph for a project

<details>
<summary>View full description</summary>

Get dependency graph for visualization.

**Sprint 78: Cross-Project Sprint Dependencies - Day 2 Implementation**

Returns a graph structure with:
- **nodes**: Sprints with status and blocking info
- **edges**: Dependencies with type and status

Suitable for rendering with visualization libraries like ReactFlow or D3.

</details>

---

### 🔵 GET `/api/v1/planning/projects/{project_id}/resource-heatmap`

**Summary**: Get resource allocation heatmap

<details>
<summary>View full description</summary>

Get resource allocation heatmap for visualization.

**Sprint 78: Resource Allocation Optimization - Day 3 Implementation**

Returns a heatmap structure with:
- **users**: List of users with allocations
- **sprints**: List of sprints
- **cells**: Allocation data for each user-sprint combination

Suitable for rendering with visualization libraries.

Cell status values:
- **available**: No allocation (0%)
- **partial**: Partial allocation (1-99%)
- **full**: Full allocation (100%)
- **over_allocated**: Over-allocated (>100%)

</details>

---

### 🔵 GET `/api/v1/planning/projects/{project_id}/retrospective-comparison`

**Summary**: Compare retrospectives across sprints

<details>
<summary>View full description</summary>

Compare retrospectives across multiple sprints.

**Sprint 78: Retrospective Enhancement - Day 1 Implementation**

Compares key metrics across selected sprints:
- Completion rates
- P0 completion rates
- Blocked item trends
- Velocity trends
- Action item completion rates

Args:
    project_id: Project UUID
    sprint_ids: Comma-separated sprint UUIDs (2-5 sprints)

Returns:
    Comparison data with metrics for each sprint

</details>

---

### 🔵 GET `/api/v1/planning/projects/{project_id}/template-suggestions`

**Summary**: Get template suggestions for project

<details>
<summary>View full description</summary>

Get template suggestions based on project context.

**Sprint 78: Sprint Template Library - Day 4 Implementation**

Analyzes:
- Recent sprint patterns
- Project characteristics
- Template popularity

Returns top 5 suggestions with match scores.

</details>

---

### 🟢 POST `/api/v1/planning/sprints/{sprint_id}/action-items`

**Summary**: Create action item from retrospective

<details>
<summary>View full description</summary>

Create a new action item from sprint retrospective.

**Sprint 78: Retrospective Enhancement - Day 1 Implementation**

Action items track concrete next steps identified during sprint retrospectives.
Supports:
- Category classification (delivery, priority, velocity, etc.)
- Priority levels (low, medium, high)
- Assignment to team members
- Cross-sprint tracking via due_sprint_id

Args:
    sprint_id: Sprint UUID (source sprint)
    data: Action item data

Returns:
    Created RetroActionItemResponse

Raises:
    404: Sprint not found
    403: No write access to project

</details>

---

### 🔵 GET `/api/v1/planning/sprints/{sprint_id}/action-items`

**Summary**: List action items for a sprint

<details>
<summary>View full description</summary>

List action items for a sprint retrospective.

**Sprint 78: Retrospective Enhancement - Day 1 Implementation**

Supports filtering by:
- status: open, in_progress, completed, cancelled
- category: delivery, priority, velocity, planning, scope, blockers, team, general
- priority: low, medium, high
- assignee_id: User UUID

Args:
    sprint_id: Sprint UUID
    Various filters

Returns:
    Paginated list of action items

</details>

---

### 🟢 POST `/api/v1/planning/sprints/{sprint_id}/action-items/bulk`

**Summary**: Bulk create action items

**Description**: Bulk create action items from retrospective.

Useful for importing action items generated by retrospective automation.

---

### 🔵 GET `/api/v1/planning/sprints/{sprint_id}/action-items/stats`

**Summary**: Get action items statistics

**Description**: Get statistics for action items in a sprint retrospective.

Returns counts by status, category, and priority.

---

### 🔵 GET `/api/v1/planning/sprints/{sprint_id}/allocations`

**Summary**: List allocations for a sprint

**Description**: List all team member allocations for a sprint.

Returns paginated list of allocations with user details.

---

### 🔵 GET `/api/v1/planning/sprints/{sprint_id}/capacity`

**Summary**: Get sprint capacity

<details>
<summary>View full description</summary>

Calculate capacity for a sprint.

**Sprint 78: Resource Allocation Optimization - Day 3 Implementation**

Returns:
- Team size (allocated members)
- Total capacity hours
- Allocated hours
- Available hours
- Utilization rate (%)
- Breakdown by role

</details>

---

### 🔵 GET `/api/v1/planning/sprints/{sprint_id}/dependencies`

**Summary**: List dependencies for a sprint

<details>
<summary>View full description</summary>

List dependencies for a specific sprint.

Direction:
- **incoming**: Dependencies where this sprint is the target
- **outgoing**: Dependencies where this sprint is the source
- **both**: All dependencies involving this sprint

</details>

---

### 🔵 GET `/api/v1/planning/teams/{team_id}/capacity`

**Summary**: Get team capacity

<details>
<summary>View full description</summary>

Calculate team capacity for a date range.

**Sprint 78: Resource Allocation Optimization - Day 3 Implementation**

Returns:
- Total capacity hours for team
- Allocated hours
- Available hours
- Utilization rate (%)
- Breakdown by member
- Breakdown by role

</details>

---

### 🟢 POST `/api/v1/planning/templates`

**Summary**: Create sprint template

<details>
<summary>View full description</summary>

Create a new sprint template.

**Sprint 78: Sprint Template Library - Day 4 Implementation**

Template types:
- **standard**: Standard 2-week sprint
- **feature**: Feature-focused sprint
- **bugfix**: Bug-fix focused sprint
- **release**: Release preparation sprint
- **custom**: Custom configuration

Templates can include:
- Default duration and capacity
- Pre-defined backlog structure
- Sprint goal template
- Gate configuration

Args:
    data: Template creation data

Returns:
    Created SprintTemplateResponse

</details>

---

### 🔵 GET `/api/v1/planning/templates`

**Summary**: List sprint templates

<details>
<summary>View full description</summary>

List available sprint templates.

**Sprint 78: Sprint Template Library - Day 4 Implementation**

Filters:
- **team_id**: Team-specific templates
- **template_type**: Filter by type (standard, feature, bugfix, release, custom)
- **include_public**: Include public templates (default: true)

Returns paginated list sorted by:
1. Default templates first
2. Usage count (popularity)

</details>

---

### 🟢 POST `/api/v1/planning/templates/bulk/delete`

**Summary**: Bulk delete templates


---

### 🔵 GET `/api/v1/planning/templates/default`

**Summary**: Get default template

**Description**: Get the default template for a team or organization.

Returns team-specific default if available, otherwise public default.

---

### 🔵 GET `/api/v1/planning/templates/{template_id}`

**Summary**: Get a sprint template


---

### 🟡 PUT `/api/v1/planning/templates/{template_id}`

**Summary**: Update a sprint template


---

### 🔴 DELETE `/api/v1/planning/templates/{template_id}`

**Summary**: Delete a sprint template


---

### 🟢 POST `/api/v1/planning/templates/{template_id}/apply`

**Summary**: Apply template to create sprint

<details>
<summary>View full description</summary>

Create a new sprint from a template.

**Sprint 78: Sprint Template Library - Day 4 Implementation**

Copies from template:
- Duration configuration
- Capacity points
- Gate settings
- Backlog structure (if include_backlog=true)

Can override:
- Sprint name
- Goal
- Team size

Args:
    template_id: Template to apply
    data: Apply template request

Returns:
    ApplyTemplateResponse with created sprint info

Raises:
    400: Validation error
    404: Template or project not found

</details>

---

### 🔵 GET `/api/v1/planning/users/{user_id}/allocations`

**Summary**: List allocations for a user

**Description**: List all sprint allocations for a user.

Optionally filter by date range.

---

### 🔵 GET `/api/v1/planning/users/{user_id}/capacity`

**Summary**: Get user capacity

<details>
<summary>View full description</summary>

Calculate user capacity for a date range.

**Sprint 78: Resource Allocation Optimization - Day 3 Implementation**

Returns:
- Total working days in period
- Allocated days across sprints
- Available days
- Utilization rate (%)
- List of allocations

</details>

---

## Stage Gating

### 🟢 POST `/api/v1/stage-gating/advance`

**Summary**: Advance to next stage


---

### 🟢 POST `/api/v1/stage-gating/complete`

**Summary**: Mark stage as complete


---

### 🔵 GET `/api/v1/stage-gating/health`

**Summary**: Stage gating health check


---

### 🔵 GET `/api/v1/stage-gating/progress/{project_id}`

**Summary**: Get stage progress


---

### 🔵 GET `/api/v1/stage-gating/rules`

**Summary**: Get all stage rules


---

### 🔵 GET `/api/v1/stage-gating/rules/{stage}`

**Summary**: Get rules for specific stage


---

### 🟢 POST `/api/v1/stage-gating/validate`

**Summary**: Validate PR against stage rules

<details>
<summary>View full description</summary>

Validate a pull request against the current project stage rules.

    This endpoint checks:
    - **File patterns**: Are changed files allowed in current stage?
    - **Prerequisites**: Are all prerequisite stages complete?
    - **PR requirements**: Does PR meet stage requirements (task link, tests, etc)?

    **Stage Progression**:
    - Stage 00 (Foundation): Only docs/00-foundation/** allowed
    - Stage 01 (Planning): Docs allowed, no src/backend/frontend
    - Stage 02 (Design): Schema/specs allowed, no implementation
    - Stage 04 (Build): All code allowed with compliance
    - Stage 05 (Test): Bug fixes and tests only
    - Stage 06 (Deploy): Only deployment configs, code freeze

</details>

---

## Teams

### 🟢 POST `/api/v1/teams`

**Summary**: Create Team

**Description**: Create a new team. The creator becomes the team owner (SE4H Coach).

---

### 🔵 GET `/api/v1/teams`

**Summary**: List Teams


---

### 🔵 GET `/api/v1/teams/{team_id}`

**Summary**: Get Team


---

### 🟠 PATCH `/api/v1/teams/{team_id}`

**Summary**: Update Team


---

### 🔴 DELETE `/api/v1/teams/{team_id}`

**Summary**: Delete Team


---

### 🟢 POST `/api/v1/teams/{team_id}/members`

**Summary**: Add Team Member

**Description**: Add a user to the team. Requires admin or owner role.

---

### 🔵 GET `/api/v1/teams/{team_id}/members`

**Summary**: List Team Members


---

### 🟠 PATCH `/api/v1/teams/{team_id}/members/{user_id}`

**Summary**: Update Member Role


---

### 🔴 DELETE `/api/v1/teams/{team_id}/members/{user_id}`

**Summary**: Remove Team Member

**Description**: Remove a member from the team. Requires admin or owner role.

---

### 🔵 GET `/api/v1/teams/{team_id}/stats`

**Summary**: Get Team Statistics


---

## Telemetry

*Sprint 147 - Product Truth Layer: Measure real product usage to replace narrative-based metrics*

### 🟢 POST `/api/v1/telemetry/events`

**Summary**: Track product event

<details>
<summary>View full description</summary>

Track a product activation or engagement event. Supports 10 core events for activation funnel analysis.

**Sprint 147: Product Truth Layer - Day 2 Implementation**

**Core Events (Tier 1)**:
- `user_signed_up` - User registration completed
- `project_created` - New project created
- `project_connected_github` - GitHub repo connected
- `first_validation_run` - First validation per project
- `first_evidence_uploaded` - First evidence per project
- `first_gate_passed` - First gate approval per project
- `invite_sent` - Team invitation sent
- `invite_accepted` - Team invitation accepted
- `policy_violation_blocked` - OPA deny returned
- `ai_council_used` - AI Council interaction

**Interfaces**: web, cli, extension, api

</details>

**Parameters**:
| Name | In | Required | Type | Description |
|------|-----|----------|------|-------------|
| body | body | ✅ | object | Event data |

**Request Body**:
```json
{
  "event_name": "project_created",
  "properties": {
    "tier": "PROFESSIONAL",
    "template_used": "sdlcctl-init"
  },
  "project_id": "550e8400-e29b-41d4-a716-446655440000",
  "session_id": "cli-20260208120000-12345"
}
```

**Response**: 201 Created
```json
{
  "event_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "tracked_at": "2026-02-08T12:00:00Z"
}
```

---

### 🔵 GET `/api/v1/telemetry/funnels/{funnel_name}`

**Summary**: Get funnel metrics

<details>
<summary>View full description</summary>

Retrieve conversion metrics for activation funnels.

**Sprint 147: Product Truth Layer - Day 4 Implementation**

**Supported Funnels**:
1. `time-to-first-project` - Signup → Project → GitHub connect
2. `time-to-first-evidence` - Project → Validation → Evidence
3. `time-to-first-gate` - Evidence → Approval request → Gate pass

**Cohort Options**: day, week, month

</details>

**Parameters**:
| Name | In | Required | Type | Description |
|------|-----|----------|------|-------------|
| funnel_name | path | ✅ | string | Funnel identifier |
| start_date | query | ❌ | date | Start date (default: 30 days ago) |
| end_date | query | ❌ | date | End date (default: today) |
| cohort_by | query | ❌ | string | Cohort grouping: day, week, month |

**Response**: 200 OK
```json
{
  "funnel_name": "time-to-first-project",
  "period": {
    "start": "2026-01-08",
    "end": "2026-02-08"
  },
  "steps": [
    { "name": "user_signed_up", "count": 127, "percentage": 100 },
    { "name": "project_created", "count": 104, "percentage": 82 },
    { "name": "project_connected_github", "count": 52, "percentage": 41 }
  ],
  "conversion_rates": {
    "signup_to_project": 82,
    "project_to_github": 50
  },
  "median_times": {
    "signup_to_project_minutes": 3.2,
    "project_to_github_minutes": 12.5
  }
}
```

---

### 🔵 GET `/api/v1/telemetry/dashboard`

**Summary**: Get activation dashboard

<details>
<summary>View full description</summary>

Retrieve high-level activation metrics for dashboard display. Includes signups, activation rate, and time-to-value metrics.

**Sprint 147: Product Truth Layer - Day 4 Implementation**

**Metrics Included**:
- Signups (7-day rolling)
- Activation rate (% completing first gate)
- Time-to-first-project (p50)
- Time-to-first-evidence (p50)
- Funnel current vs target

</details>

**Response**: 200 OK
```json
{
  "signups_7d": 127,
  "signups_7d_change": 12,
  "activation_rate": 64,
  "activation_rate_change": 5,
  "time_to_first_project_p50_minutes": 3.2,
  "time_to_first_project_change": -18,
  "time_to_first_evidence_p50_minutes": 12.5,
  "time_to_first_evidence_change": -8,
  "funnels": {
    "time_to_first_project": { "current": 82, "target": 70 },
    "time_to_first_evidence": { "current": 52, "target": 40 },
    "time_to_first_gate": { "current": 25, "target": 25 }
  }
}
```

---

## Templates

### 🔵 GET `/api/v1/planning/projects/{project_id}/template-suggestions`

**Summary**: Get template suggestions for project

<details>
<summary>View full description</summary>

Get template suggestions based on project context.

**Sprint 78: Sprint Template Library - Day 4 Implementation**

Analyzes:
- Recent sprint patterns
- Project characteristics
- Template popularity

Returns top 5 suggestions with match scores.

</details>

---

### 🟢 POST `/api/v1/planning/templates`

**Summary**: Create sprint template

<details>
<summary>View full description</summary>

Create a new sprint template.

**Sprint 78: Sprint Template Library - Day 4 Implementation**

Template types:
- **standard**: Standard 2-week sprint
- **feature**: Feature-focused sprint
- **bugfix**: Bug-fix focused sprint
- **release**: Release preparation sprint
- **custom**: Custom configuration

Templates can include:
- Default duration and capacity
- Pre-defined backlog structure
- Sprint goal template
- Gate configuration

Args:
    data: Template creation data

Returns:
    Created SprintTemplateResponse

</details>

---

### 🔵 GET `/api/v1/planning/templates`

**Summary**: List sprint templates

<details>
<summary>View full description</summary>

List available sprint templates.

**Sprint 78: Sprint Template Library - Day 4 Implementation**

Filters:
- **team_id**: Team-specific templates
- **template_type**: Filter by type (standard, feature, bugfix, release, custom)
- **include_public**: Include public templates (default: true)

Returns paginated list sorted by:
1. Default templates first
2. Usage count (popularity)

</details>

---

### 🟢 POST `/api/v1/planning/templates/bulk/delete`

**Summary**: Bulk delete templates


---

### 🔵 GET `/api/v1/planning/templates/default`

**Summary**: Get default template

**Description**: Get the default template for a team or organization.

Returns team-specific default if available, otherwise public default.

---

### 🔵 GET `/api/v1/planning/templates/{template_id}`

**Summary**: Get a sprint template


---

### 🟡 PUT `/api/v1/planning/templates/{template_id}`

**Summary**: Update a sprint template


---

### 🔴 DELETE `/api/v1/planning/templates/{template_id}`

**Summary**: Delete a sprint template


---

### 🟢 POST `/api/v1/planning/templates/{template_id}/apply`

**Summary**: Apply template to create sprint

<details>
<summary>View full description</summary>

Create a new sprint from a template.

**Sprint 78: Sprint Template Library - Day 4 Implementation**

Copies from template:
- Duration configuration
- Capacity points
- Gate settings
- Backlog structure (if include_backlog=true)

Can override:
- Sprint name
- Goal
- Team size

Args:
    template_id: Template to apply
    data: Apply template request

Returns:
    ApplyTemplateResponse with created sprint info

Raises:
    400: Validation error
    404: Template or project not found

</details>

---

## Tier Management

### 🔵 GET `/api/v1/governance/tiers/`

**Summary**: List All Tiers


---

### 🔵 GET `/api/v1/governance/tiers/health`

**Summary**: Tier management health check


---

### 🔵 GET `/api/v1/governance/tiers/{project_id}`

**Summary**: Get Project Tier

<details>
<summary>View full description</summary>

Get the current tier classification for a project.

    **4-Tier System:**
    - **LITE**: Solo/hobby, minimal governance
    - **STANDARD**: Small teams, standard controls
    - **PROFESSIONAL**: Business-critical, full governance
    - **ENTERPRISE**: Regulated, maximum controls

    Returns tier info with compliance status.

</details>

---

### 🟢 POST `/api/v1/governance/tiers/{project_id}/upgrade`

**Summary**: Request Tier Upgrade

<details>
<summary>View full description</summary>

Request an upgrade to a higher tier.

    **Upgrade Path:**
    LITE → STANDARD → PROFESSIONAL → ENTERPRISE

    The request will be validated against:
    - Current compliance status
    - Target tier requirements
    - Team size and project maturity

    Returns gap analysis and estimated effort.

</details>

---

### 🔵 GET `/api/v1/governance/tiers/{tier}/requirements`

**Summary**: Get Tier Requirements

<details>
<summary>View full description</summary>

Get all requirements for a specific tier.

    Requirements include:
    - Mandatory vs optional classification
    - Validation type (automated, manual, hybrid)
    - Failure action (blocking, warning, info)
    - Category grouping

    Use this to understand what's needed for a tier.

</details>

---

## Triage

### 🟢 POST `/api/v1/triage/analyze`

**Summary**: Analyze For Triage

<details>
<summary>View full description</summary>

Analyze text to suggest triage priority and routing.

This endpoint analyzes the provided text (title, description, etc.)
and returns suggested priority, team assignment, and SLA information.

Does not modify any data - use /triage/{id}/apply to apply decisions.

</details>

---

### 🟢 POST `/api/v1/triage/analyze`

**Summary**: Analyze For Triage

<details>
<summary>View full description</summary>

Analyze text to suggest triage priority and routing.

This endpoint analyzes the provided text (title, description, etc.)
and returns suggested priority, team assignment, and SLA information.

Does not modify any data - use /triage/{id}/apply to apply decisions.

</details>

---

### 🔵 GET `/api/v1/triage/sla-breaches`

**Summary**: Get Sla Breaches

**Description**: Get all feedback items with SLA breaches.

Returns list of items that have breached their SLA.

---

### 🔵 GET `/api/v1/triage/sla-breaches`

**Summary**: Get Sla Breaches

**Description**: Get all feedback items with SLA breaches.

Returns list of items that have breached their SLA.

---

### 🔵 GET `/api/v1/triage/stats`

**Summary**: Get Triage Statistics

**Description**: Get overall triage statistics.

Returns counts by status, priority, and triage rate.
Used for the triage dashboard.

---

### 🔵 GET `/api/v1/triage/stats`

**Summary**: Get Triage Statistics

**Description**: Get overall triage statistics.

Returns counts by status, priority, and triage rate.
Used for the triage dashboard.

---

### 🟢 POST `/api/v1/triage/{feedback_id}/apply`

**Summary**: Apply Triage Decision

**Description**: Apply triage decision to a feedback item.

Sets the priority and updates status to TRIAGED.
Requires triage permissions (any authenticated user for pilot).

---

### 🟢 POST `/api/v1/triage/{feedback_id}/apply`

**Summary**: Apply Triage Decision

**Description**: Apply triage decision to a feedback item.

Sets the priority and updates status to TRIAGED.
Requires triage permissions (any authenticated user for pilot).

---

### 🟢 POST `/api/v1/triage/{feedback_id}/auto-triage`

**Summary**: Auto Triage Feedback

**Description**: Run auto-triage on an existing feedback item.

Returns suggested triage without applying it.
Use /triage/{id}/apply to apply the decision.

---

### 🟢 POST `/api/v1/triage/{feedback_id}/auto-triage`

**Summary**: Auto Triage Feedback

**Description**: Run auto-triage on an existing feedback item.

Returns suggested triage without applying it.
Use /triage/{id}/apply to apply the decision.

---

### 🔵 GET `/api/v1/triage/{feedback_id}/sla`

**Summary**: Get Sla Status

**Description**: Get SLA status for a feedback item.

Returns whether SLAs are being met or breached.

---

### 🔵 GET `/api/v1/triage/{feedback_id}/sla`

**Summary**: Get Sla Status

**Description**: Get SLA status for a feedback item.

Returns whether SLAs are being met or breached.

---

## Uncategorized

### 🔵 GET `/`

**Summary**: Root


---

### 🔵 GET `/health`

**Summary**: Health Check

**Description**: Health check endpoint for load balancers and monitoring

---

### 🔵 GET `/health/ready`

**Summary**: Readiness Check

<details>
<summary>View full description</summary>

Readiness check - verifies all dependencies are available.

Checks:
- PostgreSQL: SELECT 1 query
- Redis: PING command
- OPA: /health endpoint
- MinIO: HEAD bucket
- APScheduler: Running status

Returns:
    200 OK if all dependencies are healthy
    503 Service Unavailable if any dependency is down

</details>

---

### 🔵 GET `/metrics`

**Summary**: Metrics

**Description**: Prometheus metrics endpoint

Returns:
    Prometheus metrics in text format (for Prometheus scraping)

---

## Vibecoding Index

### 🟢 POST `/api/v1/vibecoding/batch`

**Summary**: Batch calculate Vibecoding Index

**Description**: Calculate Vibecoding Index for multiple submissions in batch.

---

### 🟢 POST `/api/v1/vibecoding/calculate`

**Summary**: Calculate Vibecoding Index

<details>
<summary>View full description</summary>

Calculate the Vibecoding Index for a code submission.

    The index is a composite score (0-100) from 5 signals:
    - **Architectural Smell** (25%): God class, feature envy, shotgun surgery
    - **Abstraction Complexity** (15%): Inheritance depth, generics
    - **AI Dependency Ratio** (20%): AI-generated lines / total lines
    - **Change Surface Area** (20%): Files, modules, API contracts affected
    - **Drift Velocity** (20%): Pattern changes over 7 days

    **Routing:**
    - Green (0-30): Auto-approve
    - Yellow (31-60): Tech Lead review
    - Orange (61-80): CEO should review
    - Red (81-100): CEO must review

    **MAX CRITICALITY OVERRIDE:**
    Critical path files (auth, security, payment) automatically boost
    the index to minimum 80 (Red), requiring CEO review.

</details>

---

### 🟢 POST `/api/v1/vibecoding/calibrate`

**Summary**: Submit calibration feedback

<details>
<summary>View full description</summary>

Submit CEO calibration feedback for index tuning.

    This feedback is used to:
    - Adjust signal weights over time
    - Identify false positives/negatives
    - Improve routing accuracy

</details>

---

### 🔵 GET `/api/v1/vibecoding/health`

**Summary**: Signals engine health check

**Description**: Check health of the Vibecoding Index signals engine.

---

### 🔵 GET `/api/v1/vibecoding/stats`

**Summary**: Get index statistics

**Description**: Get aggregate statistics for Vibecoding Index calculations.

---

### 🔵 GET `/api/v1/vibecoding/thresholds`

**Summary**: Get index thresholds

**Description**: Get Vibecoding Index thresholds, routing rules, and signal weights.

---

### 🔵 GET `/api/v1/vibecoding/{submission_id}`

**Summary**: Get cached Vibecoding Index

**Description**: Get previously calculated Vibecoding Index for a submission.

---

## dashboard

### 🔵 GET `/api/v1/dashboard/recent-gates`

**Summary**: Get Recent Gates

**Description**: Get recent gate activity.

Returns list of recent gates with project info.

---

### 🔵 GET `/api/v1/dashboard/stats`

**Summary**: Get Dashboard Stats

<details>
<summary>View full description</summary>

Get dashboard statistics.

Returns:
    - total_projects: Total number of projects
    - active_gates: Gates with pending status
    - pending_approvals: Gates awaiting approval
    - pass_rate: Percentage of approved gates

</details>

---

## dogfooding

### 🔵 GET `/api/v1/dogfooding/ceo-time/entries`

**Summary**: List Ceo Time Entries

**Description**: List CEO time tracking entries.

Requires CTO or CEO role.

---

### 🟢 POST `/api/v1/dogfooding/ceo-time/record`

**Summary**: Record Ceo Time

**Description**: Record CEO time spent on governance-related activities.

Used to track time savings during Sprint 114 dogfooding.
Requires CTO or CEO role.

---

### 🔵 GET `/api/v1/dogfooding/ceo-time/summary`

**Summary**: Get Ceo Time Summary

**Description**: Get CEO time tracking summary for Sprint 114.

Shows baseline vs actual hours, time saved, and trend data.

---

### 🔵 GET `/api/v1/dogfooding/daily-checks`

**Summary**: Run Daily Checks

**Description**: Run daily checks for Sprint 114 dogfooding.

Day 2: Verify 5+ PRs evaluated, check kill switch dashboard, baseline CEO time
Day 3: Analyze first 10 PRs, tune thresholds, collect developer feedback
Day 4: Review false positives, adjust prompts, prepare metrics report

---

### 🔵 GET `/api/v1/dogfooding/daily-checks/history`

**Summary**: Get Daily Checks History

**Description**: Get history of daily checks for all sprint days.

Returns a summary of checks for each day of Sprint 114.

---

### 🟢 POST `/api/v1/dogfooding/enforce/soft`

**Summary**: Enforce Soft Mode

<details>
<summary>View full description</summary>

Evaluate PR against SOFT mode enforcement rules.

SOFT Mode Rules (Sprint 115):
- RED zone (81-100): BLOCK with CTO override option
- ORANGE zone (61-80): WARN (Tech Lead should review)
- YELLOW zone (31-60): WARN (Spot check recommended)
- GREEN zone (0-30): PASS (Auto-approve)

Exemptions applied:
- dependency_update_exemption: Package files only = reduced friction
- documentation_safe_pattern: docs/ only + low index = auto-approve
- test_only_pattern: tests/ only = warn, never block

This endpoint does not require authentication for GitHub Actions integration.

</details>

---

### 🔵 GET `/api/v1/dogfooding/enforce/soft/log`

**Summary**: Get Soft Enforcement Log

**Description**: Get SOFT mode enforcement log.

Returns paginated list of enforcement decisions for audit and analysis.
Requires authenticated user.

---

### 🟢 POST `/api/v1/dogfooding/enforce/soft/override`

**Summary**: Request Cto Override

**Description**: Request CTO override for blocked PR.

Only available for RED zone PRs. Requires authentication.
CTO/CEO can approve overrides directly.

---

### 🔵 GET `/api/v1/dogfooding/enforce/soft/status`

**Summary**: Get Soft Mode Status

**Description**: Get current SOFT mode configuration and metrics.

Returns configuration details and enforcement statistics.

---

### 🔵 GET `/api/v1/dogfooding/export/json`

**Summary**: Export Json Metrics

**Description**: Export all dogfooding metrics as JSON.

Comprehensive export for reporting and analysis.

---

### 🔵 GET `/api/v1/dogfooding/export/prometheus`

**Summary**: Export Prometheus Metrics

**Description**: Export dogfooding metrics in Prometheus format.

Used by Prometheus scraper for Grafana dashboards.

---

### 🟢 POST `/api/v1/dogfooding/feedback`

**Summary**: Submit Developer Feedback

**Description**: Submit developer feedback for Sprint 114 dogfooding.

Collects satisfaction ratings, NPS scores, and qualitative feedback
to assess developer experience with WARNING mode governance.

---

### 🔵 GET `/api/v1/dogfooding/feedback/list`

**Summary**: List Developer Feedback

**Description**: List all developer feedback submissions.

Requires CTO or admin role for full access.
Regular users only see their own feedback.

---

### 🔵 GET `/api/v1/dogfooding/feedback/summary`

**Summary**: Get Feedback Summary

**Description**: Get aggregated developer feedback summary.

Returns NPS scores, satisfaction distribution, and top pain points
for Sprint 114 dogfooding analysis.

---

### 🔵 GET `/api/v1/dogfooding/go-no-go`

**Summary**: Get Go No Go Decision

**Description**: Get Go/No-Go decision for Sprint 115 (SOFT mode).

Evaluates all criteria and provides recommendation.
Requires CTO or CEO role.

---

### 🔵 GET `/api/v1/dogfooding/metrics`

**Summary**: Get Dogfooding Metrics

**Description**: Get Sprint 114 dogfooding metrics for WARNING mode observation.

Returns aggregated metrics for Go/No-Go decision support.

---

### 🔵 GET `/api/v1/dogfooding/prs`

**Summary**: Get Pr Metrics

**Description**: Get list of PR governance evaluations.

Paginated list of PRs evaluated during dogfooding period.

---

### 🟢 POST `/api/v1/dogfooding/prs/record`

**Summary**: Record Pr Metric

**Description**: Record a PR governance evaluation metric.

Called by GitHub Actions workflow after each PR evaluation.
No authentication required for GitHub Actions webhook.

---

### 🟢 POST `/api/v1/dogfooding/report-false-positive`

**Summary**: Report False Positive

**Description**: Report a false positive governance evaluation.

Used by developers to flag incorrect violations for calibration.

---

### 🔵 GET `/api/v1/dogfooding/status`

**Summary**: Get Dogfooding Status

**Description**: Get current dogfooding status (public endpoint).

Returns basic status information for monitoring.

---

## github

### 🔵 GET `/api/v1/github/installations`

**Summary**: List user's GitHub installations

<details>
<summary>View full description</summary>

List all active GitHub App installations for the current user.

    Returns installations where the user installed the GitHub App.
    Each installation provides access to repositories in that user/org.

    **Note**: To get repositories for an installation, use
    GET /github/installations/{installation_id}/repositories

</details>

---

### 🔵 GET `/api/v1/github/installations/{installation_id}/repositories`

**Summary**: List repositories for installation

<details>
<summary>View full description</summary>

List repositories accessible to a GitHub App installation.

    Requires the installation to be owned by the current user.
    Results are paginated (default: 100 per page, max: 100).

    **Note**: This fetches fresh data from GitHub API, not cached.

</details>

---

### 🟢 POST `/api/v1/github/projects/{project_id}/clone`

**Summary**: Clone linked repository

<details>
<summary>View full description</summary>

Clone the linked GitHub repository to local storage.

    Uses shallow clone (--depth=1) by default for faster cloning.
    After clone, use GET /projects/{project_id}/scan for gap analysis.

    **Clone Status Flow**:
    pending → cloning → cloned (or failed)

</details>

---

### 🟢 POST `/api/v1/github/projects/{project_id}/link`

**Summary**: Link GitHub repository to project

<details>
<summary>View full description</summary>

Link a GitHub repository to an SDLC Orchestrator project.

    **Rules**:
    - One project can only be linked to one repository
    - One repository can only be linked to one project
    - User must own the installation

    **After linking**:
    - Use POST /projects/{project_id}/clone to clone the repository
    - Use GET /projects/{project_id}/scan to scan the cloned repository

</details>

---

### 🔵 GET `/api/v1/github/projects/{project_id}/repository`

**Summary**: Get linked repository for project


---

### 🔵 GET `/api/v1/github/projects/{project_id}/scan`

**Summary**: Scan cloned repository

**Description**: Scan the cloned repository structure for gap analysis.

    Returns folder/file structure to determine SDLC compliance.
    Repository must be cloned first (clone_status = 'cloned').

---

### 🔴 DELETE `/api/v1/github/projects/{project_id}/unlink`

**Summary**: Unlink GitHub repository from project

**Description**: Unlink a GitHub repository from a project.

    This does NOT delete the repository from GitHub.
    The local clone is also preserved (can be deleted manually).

---

### 🟢 POST `/api/v1/github/webhooks`

**Summary**: GitHub webhook handler

<details>
<summary>View full description</summary>

Handle GitHub webhook events (Sprint 129.5).

    **Supported Events**:
    - installation: App install/uninstall/suspend/unsuspend
    - push: Code pushed → triggers gap analysis
    - pull_request: PR opened/sync/closed → triggers gate evaluation
    - ping: Webhook configuration test

    **Security**:
    - Webhook signature validation (HMAC-SHA256)
    - X-Hub-Signature-256 header required
    - Idempotency via X-GitHub-Delivery header

    **Processing**:
    - Webhook returns 202 Accepted immediately
    - Actual processing happens in background job
    - Use X-GitHub-Delivery to track status

</details>

---

### 🔵 GET `/api/v1/github/webhooks/dlq`

**Summary**: Get dead letter queue jobs

<details>
<summary>View full description</summary>

Get jobs in the dead letter queue (failed after max retries).

    **Dead Letter Queue (DLQ)**:
    - Contains jobs that failed after 3 retry attempts
    - Jobs can be manually retried via POST /webhooks/dlq/{job_id}/retry
    - Monitor DLQ size for potential issues

    **Access**: Requires admin authentication

</details>

---

### 🟢 POST `/api/v1/github/webhooks/dlq/{job_id}/retry`

**Summary**: Retry a dead letter queue job

<details>
<summary>View full description</summary>

Retry a job from the dead letter queue.

    **Retry Behavior**:
    - Moves job from DLQ back to main queue
    - Resets retry count to 0
    - Job will be processed with next batch

    **Access**: Requires admin authentication

</details>

---

### 🔵 GET `/api/v1/github/webhooks/jobs/{job_id}`

**Summary**: Get webhook job status

<details>
<summary>View full description</summary>

Get status of a specific webhook job.

    **Job Status**:
    - queued: Waiting to be processed
    - processing: Currently being processed
    - completed: Successfully processed
    - retrying: Failed, queued for retry
    - failed: Failed after max retries (in DLQ)

    **Access**: Requires authentication

</details>

---

### 🟢 POST `/api/v1/github/webhooks/process`

**Summary**: Trigger webhook job processing

<details>
<summary>View full description</summary>

Manually trigger processing of queued webhook jobs.

    **Processing Behavior**:
    - Processes up to `max_jobs` queued webhooks
    - Returns processing summary
    - Should be called by scheduler or admin

    **Access**: Requires admin authentication

</details>

---

### 🔵 GET `/api/v1/github/webhooks/stats`

**Summary**: Get webhook job queue statistics

<details>
<summary>View full description</summary>

Get statistics about webhook job queues.

    **Statistics Include**:
    - Queue length (pending jobs)
    - Dead letter queue (DLQ) length
    - Jobs by status (queued, processing, completed, failed)
    - Total jobs tracked

    **Access**: Requires admin authentication

</details>

---

## organization-invitations

### 🔴 DELETE `/api/v1/org-invitations/{invitation_id}`

**Summary**: Cancel organization invitation

<details>
<summary>View full description</summary>

Cancel pending invitation (admin action).

    **Permissions**:
    - Organization owner/admin only

    **Effect**:
    - Status changed to 'cancelled'
    - Invitation token invalidated

</details>

---

### 🟢 POST `/api/v1/org-invitations/{invitation_id}/resend`

**Summary**: Resend organization invitation email

<details>
<summary>View full description</summary>

Resend invitation email with new token.

    **Security**:
    - Generates NEW token (invalidates old token)
    - Rate limiting: Max 3 resends per invitation
    - Cooldown: 5 minutes between resends

    **Permissions**:
    - Organization owner/admin only

</details>

---

### 🔵 GET `/api/v1/org-invitations/{token}`

**Summary**: Get organization invitation details by token

**Description**: Get invitation details for acceptance page (public endpoint).

    **Security**:
    - No authentication required (token is the credential)
    - Constant-time token verification (prevents timing attacks)

---

### 🟢 POST `/api/v1/org-invitations/{token}/accept`

**Summary**: Accept organization invitation

<details>
<summary>View full description</summary>

Accept invitation and create organization membership.

    **Security**:
    - Requires authentication (user must be logged in)
    - Email verification (user email must match invited email)
    - One-time use (status change prevents replay)

</details>

---

### 🟢 POST `/api/v1/org-invitations/{token}/decline`

**Summary**: Decline organization invitation

**Description**: Decline invitation politely (no membership created).

    **Security**:
    - No authentication required (anonymous decline allowed)
    - One-time use (status change prevents replay)

---

### 🟢 POST `/api/v1/organizations/{organization_id}/invitations`

**Summary**: Send organization invitation

<details>
<summary>View full description</summary>

Send invitation to join organization with secure token.

    **Security**:
    - Rate limiting: 50 invitations/hour per organization
    - Email rate limit: 10 invitations/day per email
    - Token hashing: SHA256 (never store raw)
    - Audit trail: IP address, user agent, timestamp

    **Permissions**:
    - Organization owner: Can invite with admin/member role
    - Organization admin: Can invite members only
    - Note: Cannot invite as 'owner' (CTO constraint)

    **Errors**:
    - 403: User not authorized to invite
    - 404: Organization not found
    - 409: Pending invitation already exists
    - 429: Rate limit exceeded

</details>

---

### 🔵 GET `/api/v1/organizations/{organization_id}/invitations`

**Summary**: List organization invitations

<details>
<summary>View full description</summary>

List all invitations for an organization (pending, accepted, declined).

    **Permissions**:
    - Organization owner/admin only

    **Filters** (query params):
    - status: Filter by status (pending, accepted, declined, expired, cancelled)
    - email: Filter by invited email

    **Pagination**:
    - limit: Max results per page (default: 50)
    - offset: Skip N results (default: 0)

</details>

---

## organizations

### 🟢 POST `/api/v1/organizations`

**Summary**: Create Organization

**Description**: Create a new organization. The creator is automatically assigned to it.

---

### 🔵 GET `/api/v1/organizations`

**Summary**: List Organizations

**Description**: List organizations. Regular users see only their own organization.

---

### 🔵 GET `/api/v1/organizations/{org_id}`

**Summary**: Get Organization


---

### 🟠 PATCH `/api/v1/organizations/{org_id}`

**Summary**: Update Organization

**Description**: Update organization details. User must be a member.

---

### 🟢 POST `/api/v1/organizations/{org_id}/members`

**Summary**: Add Member Directly

**Description**: Add existing user to organization directly (bypass invitation flow).

---

### 🔵 GET `/api/v1/organizations/{org_id}/stats`

**Summary**: Get Organization Statistics


---

## payments

### 🔵 GET `/api/v1/payments/subscriptions/me`

**Summary**: Get My Subscription

<details>
<summary>View full description</summary>

Get current user's subscription.

Returns:
    SubscriptionResponse with current subscription details

Raises:
    HTTPException 404: No subscription found

</details>

---

### 🟢 POST `/api/v1/payments/vnpay/create`

**Summary**: Create Vnpay Payment

<details>
<summary>View full description</summary>

Create VNPay payment URL for plan upgrade.

Per Plan v2.2 Section 7.1:
- Generates unique transaction reference
- Creates pending payment record
- Returns VNPay URL for redirect

Args:
    request_body: Plan and billing period
    request: FastAPI request (for IP address)
    db: Database session
    current_user: Authenticated user

Returns:
    VNPayCreateResponse with payment URL

Raises:
    HTTPException 400: Invalid plan
    HTTPException 400: Standard plan not self-service in V1

</details>

---

### 🟢 POST `/api/v1/payments/vnpay/ipn`

**Summary**: Vnpay Ipn Handler

<details>
<summary>View full description</summary>

VNPay IPN webhook handler (server-to-server).

Per Plan v2.2 Section 7.3.3:
- This is the SINGLE SOURCE OF TRUTH for payment state
- Idempotent: Same IPN called N times → Same response, 1 state change
- Terminal states (completed/failed) are immutable
- Subscription activation is ATOMIC with payment completion

VNPay Response Codes:
- 00: Success (Confirmed)
- 01: Order not found
- 02: Already updated (idempotent)
- 97: Invalid signature
- 99: Unknown error

Returns:
    VNPay response format: {"RspCode": "XX", "Message": "..."}

</details>

---

### 🔵 GET `/api/v1/payments/vnpay/return`

**Summary**: Vnpay Return Handler

<details>
<summary>View full description</summary>

VNPay return handler (user-facing redirect).

Per Plan v2.2 Section 7.3.2:
- This endpoint is READ-ONLY
- Does NOT change payment status (that's IPN's job)
- Only verifies signature and returns status

VNPay redirects user here after payment.
Frontend should redirect to /checkout/success or /checkout/failed based on response.

Returns:
    Payment status for frontend display

</details>

---

### 🔵 GET `/api/v1/payments/{vnp_txn_ref}`

**Summary**: Get Payment Status

<details>
<summary>View full description</summary>

Get payment status by transaction reference.

Args:
    vnp_txn_ref: VNPay transaction reference
    db: Database session
    current_user: Authenticated user

Returns:
    PaymentStatusResponse with current status

Raises:
    HTTPException 404: Payment not found
    HTTPException 403: Not authorized to view this payment

</details>

---

## pilot

### 🟢 POST `/api/v1/pilot/feedback`

**Summary**: Submit satisfaction survey

**Description**: Submit satisfaction survey.

Score is 1-10, with 8+ being the target.

---

### 🟢 POST `/api/v1/pilot/metrics/aggregate`

**Summary**: Trigger daily metrics aggregation

**Description**: Trigger daily metrics aggregation.

Defaults to today if no date provided. Admin only.

---

### 🔵 GET `/api/v1/pilot/metrics/summary`

**Summary**: Get pilot program summary

<details>
<summary>View full description</summary>

Get overall pilot program metrics for CEO dashboard.

Includes:
- Participant progress (target: 10)
- TTFV metrics (target: <30 min)
- Quality gate pass rate (target: 95%+)
- Satisfaction scores (target: 8/10)

</details>

---

### 🔵 GET `/api/v1/pilot/metrics/targets`

**Summary**: Get Sprint 49 targets


---

### 🟢 POST `/api/v1/pilot/participants`

**Summary**: Register as pilot participant

**Description**: Register current user as a pilot participant.

Validates domain if provided and creates participant record.

---

### 🔵 GET `/api/v1/pilot/participants`

**Summary**: List pilot participants

**Description**: List pilot participants.

Requires admin role for full access.

---

### 🔵 GET `/api/v1/pilot/participants/me`

**Summary**: Get current user's participant profile


---

### 🔵 GET `/api/v1/pilot/participants/{participant_id}`

**Summary**: Get participant by ID


---

### 🟢 POST `/api/v1/pilot/sessions`

**Summary**: Start pilot session (TTFV timer begins)

**Description**: Start a new pilot session.

This marks the beginning of the TTFV timer.

---

### 🔵 GET `/api/v1/pilot/sessions`

**Summary**: Get my sessions


---

### 🔵 GET `/api/v1/pilot/sessions/{session_id}`

**Summary**: Get session details


---

### 🟢 POST `/api/v1/pilot/sessions/{session_id}/generation`

**Summary**: Record generation results

**Description**: Record code generation results for a session.

If quality_gate_passed is True, TTFV will be calculated.

---

### 🟠 PATCH `/api/v1/pilot/sessions/{session_id}/stage`

**Summary**: Update session stage

**Description**: Update session to a new stage.

Valid stages: started, domain_selected, app_named, features_selected,
scale_selected, blueprint_generated, code_generating, code_generated,
quality_gate_passed, deployed, completed

---

## projects

### 🟢 POST `/api/v1/projects`

**Summary**: Create Project

<details>
<summary>View full description</summary>

Create a new project with optional policy pack configuration.

The current user becomes the project owner.

Args:
    data: ProjectCreate schema with name, description, policy_pack, and optional GitHub fields

Returns:
    Created project with ID, slug, and policy pack tier

ADR-027 Phase 2:
    Enforces max_projects_per_user limit from system settings.

</details>

---

### 🔵 GET `/api/v1/projects`

**Summary**: List Projects

<details>
<summary>View full description</summary>

List all projects with gate status summary.

Sprint 23 Day 2 Optimization:
- Changed from N+1 queries to single query with subqueries
- Performance improvement: ~200ms -> ~50ms (75% faster)
- Added Redis caching (60s TTL) for further optimization

</details>

---

### 🟢 POST `/api/v1/projects/init`

**Summary**: Initialize SDLC project

**Description**: Initialize a new SDLC 6.0.6 project. Creates project in database and returns configuration for .sdlc-config.json. Per RFC-001, creates 10-archive/ folder (no 99-Legacy/ in active stages 00-09).

---

### 🔵 GET `/api/v1/projects/{project_id}`

**Summary**: Get Project


---

### 🟡 PUT `/api/v1/projects/{project_id}`

**Summary**: Update Project

**Description**: Update a project.

Only project owners and admins can update projects.

---

### 🔴 DELETE `/api/v1/projects/{project_id}`

**Summary**: Delete Project

**Description**: Delete a project (soft delete).

Only project owners can delete projects.

---

### 🟡 PUT `/api/v1/projects/{project_id}/context`

**Summary**: Update project context (stage, gate, sprint)

<details>
<summary>View full description</summary>

Update the current SDLC context for a project.
    
    **SSOT Principle (Sprint 136)**:
    - Database is the Single Source of Truth
    - Extension/Dashboard READ from this data
    - Admin UI/CLI WRITE via this endpoint
    
    **Valid Stages**: FOUNDATION, PLANNING, DESIGN, INTEGRATE, BUILD, TEST, DEPLOY, OPERATE, GOVERN, ARCHIVE
    **Valid Gates**: G0.1, G0.2, G1, G2, G3, G4, G5, G6, G7, G8, G9

</details>

---

### 🔵 GET `/api/v1/projects/{project_id}/context`

**Summary**: Get project context (stage, gate, sprint)

**Description**: Get the current SDLC context for a project (SSOT read endpoint).

---

### 🟢 POST `/api/v1/projects/{project_id}/migrate-stages`

**Summary**: Migrate project stages to SDLC 6.0.6

**Description**: Migrate project from old stage structure to SDLC 6.0.6. Includes RFC-001 legacy archive migration (99-Legacy/ → 10-archive/{NN}-Legacy/). Moves INTEGRATE from stage 07 to stage 03.

---

## teams

### 🟢 POST `/api/v1/teams`

**Summary**: Create Team

**Description**: Create a new team. The creator becomes the team owner (SE4H Coach).

---

### 🔵 GET `/api/v1/teams`

**Summary**: List Teams


---

### 🔵 GET `/api/v1/teams/{team_id}`

**Summary**: Get Team


---

### 🟠 PATCH `/api/v1/teams/{team_id}`

**Summary**: Update Team


---

### 🔴 DELETE `/api/v1/teams/{team_id}`

**Summary**: Delete Team


---

### 🟢 POST `/api/v1/teams/{team_id}/members`

**Summary**: Add Team Member

**Description**: Add a user to the team. Requires admin or owner role.

---

### 🔵 GET `/api/v1/teams/{team_id}/members`

**Summary**: List Team Members


---

### 🟠 PATCH `/api/v1/teams/{team_id}/members/{user_id}`

**Summary**: Update Member Role


---

### 🔴 DELETE `/api/v1/teams/{team_id}/members/{user_id}`

**Summary**: Remove Team Member

**Description**: Remove a member from the team. Requires admin or owner role.

---

### 🔵 GET `/api/v1/teams/{team_id}/stats`

**Summary**: Get Team Statistics


---

## Summary Statistics

- **Total Categories**: 83
- **Total Endpoints**: 1135

### Endpoints by Category

- AGENTS.md: 16 endpoints
- AI: 2 endpoints
- AI Council: 10 endpoints
- AI Detection: 12 endpoints
- AI Providers: 10 endpoints
- API Keys: 6 endpoints
- Admin Panel: 22 endpoints
- Agentic Maturity: 12 endpoints
- Analytics: 37 endpoints
- Analytics v2: 8 endpoints
- Authentication: 26 endpoints
- Auto-Generation: 12 endpoints
- CEO Dashboard: 14 endpoints
- CRP - Consultations: 14 endpoints
- Check Runs: 5 endpoints
- Codegen: 58 endpoints
- Compliance: 26 endpoints
- Compliance Validation: 10 endpoints
- Context Authority: 7 endpoints
- Context Authority V2: 22 endpoints
- Context Overlay: 2 endpoints
- Context Validation: 8 endpoints
- Contract Lock: 14 endpoints
- Cross-Reference: 8 endpoints
- Dashboard: 2 endpoints
- Dependencies: 10 endpoints
- Documentation: 4 endpoints
- Dogfooding: 20 endpoints
- E2E Testing: 10 endpoints
- Evidence: 3 endpoints
- Evidence Manifest: 7 endpoints
- Evidence Timeline: 7 endpoints
- Feedback: 14 endpoints
- Feedback Learning: 22 endpoints
- Feedback Learning (EP-11): 22 endpoints
- Framework Version: 12 endpoints
- Gates: 16 endpoints
- Gates Engine: 16 endpoints
- GitHub: 13 endpoints
- Governance Metrics: 14 endpoints
- Governance Mode: 8 endpoints
- Governance Specs: 5 endpoints
- Governance Vibecoding: 7 endpoints
- Grafana Dashboards: 7 endpoints
- MRP - Merge Readiness Protocol: 18 endpoints
- MRP - Policy Enforcement: 4 endpoints
- Notifications: 8 endpoints
- Organization Invitations: 7 endpoints
- Organizations: 6 endpoints
- Override / VCR: 9 endpoints
- Payments: 5 endpoints
- Pilot: 13 endpoints
- Planning: 46 endpoints
- Planning Hierarchy: 150 endpoints
- Planning Sub-agent: 16 endpoints
- Policies: 5 endpoints
- Policy Packs: 8 endpoints
- Preview: 6 endpoints
- Projects: 9 endpoints
- Resource Allocation: 11 endpoints
- Retrospective: 9 endpoints
- Risk Analysis: 8 endpoints
- SAST: 14 endpoints
- SDLC Structure: 6 endpoints
- SOP Generator: 16 endpoints
- Sprint 77: 3 endpoints
- Sprint 78: 39 endpoints
- Stage Gating: 7 endpoints
- Teams: 10 endpoints
- Templates: 9 endpoints
- Tier Management: 5 endpoints
- Triage: 12 endpoints
- Uncategorized: 4 endpoints
- Vibecoding Index: 7 endpoints
- dashboard: 2 endpoints
- dogfooding: 20 endpoints
- github: 13 endpoints
- organization-invitations: 7 endpoints
- organizations: 6 endpoints
- payments: 5 endpoints
- pilot: 13 endpoints
- projects: 9 endpoints
- teams: 10 endpoints

---

**Document Status**: ✅ Auto-Generated from OpenAPI Specification
**Source**: `docs/03-integrate/02-API-Specifications/openapi.json`
**Generated**: Sprint 145+ - MCP Integration Phase 1
**Framework**: SDLC 6.0.6 (Stage 03 Integration)
**Date**: February 3, 2026
