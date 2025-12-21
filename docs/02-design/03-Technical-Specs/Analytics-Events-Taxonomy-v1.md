# Analytics Events Taxonomy v1.0
## Product Analytics Implementation for SDLC Orchestrator

**Document ID**: TECH-SPEC-2026-003
**Version**: 1.0.0
**Status**: ✅ DESIGN APPROVED
**Created**: December 20, 2025
**Sprint**: Sprint 41 - AI Safety Foundation (Week 1)
**Framework**: SDLC 5.1.1 Complete Lifecycle
**Owner**: Product Team + Backend Team

---

## 📋 Table of Contents

1. [Executive Summary](#executive-summary)
2. [Business Context](#business-context)
3. [Analytics Platform Selection](#analytics-platform-selection)
4. [Event Taxonomy Overview](#event-taxonomy-overview)
5. [10 Core Events Specification](#10-core-events-specification)
6. [Event Properties Schema](#event-properties-schema)
7. [Implementation Architecture](#implementation-architecture)
8. [Privacy & Compliance](#privacy--compliance)
9. [Testing & Validation](#testing--validation)
10. [Success Metrics](#success-metrics)
11. [Appendix](#appendix)

---

## 1. Executive Summary

### 1.1 Purpose

This document defines the **Analytics Events Taxonomy v1.0** for SDLC Orchestrator, implementing comprehensive product analytics to track user behavior, AI Safety Layer adoption, and Design Partner engagement during Sprint 41-43 (Q1 2026).

### 1.2 Scope

**In Scope (Sprint 41)**:
- ✅ 10 Core Events (Authentication, Projects, AI Safety, Policy)
- ✅ Mixpanel/Amplitude integration architecture
- ✅ Event properties schema (user, session, project context)
- ✅ Privacy-compliant implementation (GDPR, CCPA)
- ✅ Backend service + frontend hooks

**Out of Scope (Defer to Sprint 42+)**:
- ❌ Advanced funnels (multi-step conversion tracking)
- ❌ Cohort analysis (behavioral segmentation)
- ❌ A/B testing framework
- ❌ Custom dashboards (beyond platform defaults)

### 1.3 Success Criteria

```yaml
Sprint 41 (Week 2) Targets:
  ✅ AnalyticsService deployed (backend)
  ✅ 10 events instrumented (backend + frontend)
  ✅ Mixpanel project created + API key configured
  ✅ 100+ events tracked in 48 hours (smoke test)
  ✅ Event validation: 100% schema compliance

Sprint 42-43 Targets:
  ✅ Weekly event volume: ≥500 (6 Design Partners active)
  ✅ ai_pr_detected: ≥50/week
  ✅ ai_safety_validation: ≥50/week
  ✅ idea_submitted: ≥10/week
```

---

## 2. Business Context

### 2.1 Strategic Alignment

**Q1-Q2 2026 Roadmap** (CTO Approved Dec 20, 2025):
- **EP-02: AI Safety Layer v1** - Track AI PR detection accuracy, validation pipeline performance
- **EP-03: Design Partner Program** - Monitor partner engagement, workshop attendance, feedback loops
- **EP-01: Idea Flow** - Measure "Ý tưởng mới" flow adoption

**Key Questions Analytics Must Answer**:
1. Are Design Partners actively using AI Safety features? (EP-03)
2. What is the AI PR detection accuracy in production? (EP-02)
3. How often do policy guards block AI code? (EP-02)
4. What is the VCR override rate? (EP-02)
5. Are teams submitting ideas through the new flow? (EP-01)

### 2.2 Analytics Maturity Level

**Current State (Pre-Sprint 41)**: Level 0 - No Analytics
- ❌ No event tracking
- ❌ No user behavior insights
- ❌ No product usage metrics
- ✅ Only server logs (unstructured)

**Target State (Post-Sprint 41)**: Level 2 - Event Tracking + Properties
- ✅ 10 core events instrumented
- ✅ Rich event properties (user, session, project context)
- ✅ Real-time dashboards (Mixpanel/Amplitude)
- ✅ Weekly metrics reporting

**Future State (Q2 2026)**: Level 3 - Funnels + Cohorts
- Advanced conversion funnels
- Behavioral cohorts
- Predictive analytics (churn risk)

---

## 3. Analytics Platform Selection

### 3.1 Platform Comparison

| Criteria | Mixpanel | Amplitude | Custom (Grafana + Prometheus) |
|----------|----------|-----------|-------------------------------|
| **Event Tracking** | ✅ Excellent | ✅ Excellent | ⚠️ Manual implementation |
| **User Journeys** | ✅ Flows | ✅ Pathfinder | ❌ Not built-in |
| **Real-time Dashboards** | ✅ Yes | ✅ Yes | ✅ Yes (Grafana) |
| **Retention Analysis** | ✅ Built-in | ✅ Built-in | ❌ Custom queries |
| **Free Tier** | ✅ 100K events/mo | ✅ 10M events/mo | ✅ Self-hosted (free) |
| **GDPR Compliance** | ✅ EU data residency | ✅ EU data residency | ✅ Full control |
| **Integration Effort** | ⚡ Low (SDK) | ⚡ Low (SDK) | 🔨 High (custom) |
| **Cost (Year 1)** | $0 (free tier) | $0 (free tier) | $0 (self-hosted) |

### 3.2 Decision: Mixpanel (Primary) + Amplitude (Fallback)

**Rationale**:
1. **Free Tier Adequate**: 100K events/month covers 6 Design Partners (estimated 10K events/month)
2. **Fast Implementation**: SDK reduces Sprint 41 implementation time by ~5 days
3. **Product Analytics Focus**: Built-in funnels, retention, and cohort analysis
4. **GDPR Compliant**: EU data residency option available
5. **Dual Strategy**: Use both platforms during pilot to evaluate which fits better

**Implementation Plan**:
- **Week 1 (Jan 6-10)**: Mixpanel integration (primary)
- **Week 1 (Jan 6-10)**: Amplitude integration (secondary, parallel)
- **Week 2 (Jan 13-17)**: Evaluate data quality, choose primary platform
- **Sprint 42+**: Consolidate to single platform based on evaluation

---

## 4. Event Taxonomy Overview

### 4.1 Event Naming Convention

**Format**: `{domain}_{action}_{object?}`

**Rules**:
1. **Lowercase + Underscores**: `user_login` (NOT `UserLogin`, `user-login`)
2. **Verb + Noun**: `project_created` (action + object)
3. **Past Tense**: `ai_pr_detected` (NOT `ai_pr_detect`)
4. **Domain Prefix**: `ai_`, `policy_`, `idea_` for namespacing
5. **Max Length**: 50 characters

**Examples**:
- ✅ `user_login` (domain: user, action: login)
- ✅ `ai_pr_detected` (domain: ai, action: detected, object: pr)
- ✅ `policy_guard_blocked` (domain: policy, action: blocked, object: guard)
- ❌ `UserLoginEvent` (wrong casing)
- ❌ `ai-pr-detected` (wrong separator)

### 4.2 Event Categories (4 Domains)

```yaml
1. Authentication & Session (user_*)
   Events: user_login, user_logout
   Purpose: Track user engagement, session duration

2. Core Product (project_*, gate_*)
   Events: project_created, project_viewed
   Purpose: Track core SDLC Orchestrator usage

3. AI Safety Layer (ai_*, policy_*)
   Events: ai_pr_detected, ai_safety_validation, policy_pack_applied, policy_guard_blocked
   Purpose: Track EP-02 AI Safety adoption

4. Idea Flow (idea_*, stalled_*)
   Events: idea_submitted, stalled_project_analyzed
   Purpose: Track EP-01 Idea Flow adoption
```

### 4.3 Property Naming Convention

**Format**: `{category}_{property_name}`

**Categories**:
- `user_*`: User properties (user_id, user_email, user_role)
- `session_*`: Session properties (session_id, session_duration)
- `project_*`: Project properties (project_id, project_name)
- `event_*`: Event metadata (event_timestamp, event_source)

**Rules**:
1. **Snake_case**: `project_id` (NOT `projectId`, `ProjectID`)
2. **Descriptive**: `ai_detection_confidence` (NOT `ai_conf`)
3. **Consistent Types**: `user_id` always UUID string, `event_timestamp` always ISO8601
4. **No PII in Names**: `user_email` (hashed) NOT `john_doe_email`

---

## 5. 10 Core Events Specification

### 5.1 Authentication & Session Events

#### Event 1: `user_login`

**Description**: Fired when a user successfully authenticates (JWT, OAuth, or MFA).

**When Triggered**:
- POST `/api/v1/auth/login` returns 200 OK
- POST `/api/v1/auth/oauth/callback` returns 200 OK
- POST `/api/v1/auth/mfa/verify` returns 200 OK

**Required Properties**:
```typescript
{
  // User Context
  user_id: string              // UUID of authenticated user
  user_email_hash: string      // SHA256 hash (GDPR compliance)
  user_role: string            // "owner" | "admin" | "pm" | "dev" | "qa"
  user_is_superuser: boolean   // true if superuser

  // Session Context
  session_id: string           // UUID of session
  auth_method: string          // "jwt" | "oauth_google" | "oauth_github" | "mfa"

  // Device Context
  device_type: string          // "web" | "mobile" | "desktop" (future)
  browser: string              // "Chrome 120" | "Firefox 115" | "Safari 17"
  os: string                   // "Windows 11" | "macOS 14" | "Ubuntu 22.04"

  // Event Metadata
  event_timestamp: string      // ISO8601 UTC timestamp
  event_source: string         // "frontend" | "backend" | "cli"
}
```

**Optional Properties**:
```typescript
{
  oauth_provider?: string      // "google" | "github" | "microsoft" (if auth_method=oauth_*)
  mfa_method?: string          // "totp" | "sms" | "email" (if auth_method=mfa)
  referrer?: string            // URL that led to login page
}
```

**Example Payload**:
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_email_hash": "a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3",
  "user_role": "admin",
  "user_is_superuser": false,
  "session_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "auth_method": "oauth_google",
  "device_type": "web",
  "browser": "Chrome 120",
  "os": "macOS 14",
  "event_timestamp": "2026-01-10T10:30:45.123Z",
  "event_source": "frontend",
  "oauth_provider": "google"
}
```

**Backend Implementation Location**: `backend/app/api/routes/auth.py:login()`, `backend/app/api/routes/auth.py:oauth_callback()`

**Frontend Implementation Location**: `frontend/web/src/api/auth.ts:useLogin()`, `frontend/web/src/api/auth.ts:useOAuthCallback()`

---

#### Event 2: `user_logout`

**Description**: Fired when a user explicitly logs out or session expires.

**When Triggered**:
- POST `/api/v1/auth/logout` called
- Session timeout (15 min inactivity)
- User clicks "Logout" button

**Required Properties**:
```typescript
{
  // User Context
  user_id: string
  session_id: string
  session_duration_seconds: number  // Time from login to logout

  // Logout Context
  logout_reason: string            // "manual" | "timeout" | "forced"

  // Event Metadata
  event_timestamp: string
  event_source: string
}
```

**Example Payload**:
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "session_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "session_duration_seconds": 3600,
  "logout_reason": "manual",
  "event_timestamp": "2026-01-10T11:30:45.123Z",
  "event_source": "frontend"
}
```

---

### 5.2 Core Product Events

#### Event 3: `project_created`

**Description**: Fired when a new project is created in SDLC Orchestrator.

**When Triggered**:
- POST `/api/v1/projects` returns 201 Created
- User completes "Create Project" wizard

**Required Properties**:
```typescript
{
  // User Context
  user_id: string
  user_role: string

  // Project Context
  project_id: string               // UUID of new project
  project_name: string             // Project name (first 100 chars)
  project_type: string             // "idea" | "stalled" | "standard"
  project_tier: string             // "LITE" | "STANDARD" | "PROFESSIONAL" | "ENTERPRISE"

  // Configuration Context
  policy_pack_applied: boolean     // true if policy pack auto-applied
  policy_pack_name?: string        // Name of policy pack (if applied)
  github_connected: boolean        // true if GitHub repo linked

  // Event Metadata
  event_timestamp: string
  event_source: string
}
```

**Example Payload**:
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_role": "pm",
  "project_id": "a1b2c3d4-e5f6-4a5b-8c7d-9e0f1a2b3c4d",
  "project_name": "Mobile App Redesign",
  "project_type": "idea",
  "project_tier": "PROFESSIONAL",
  "policy_pack_applied": true,
  "policy_pack_name": "Startup SDLC (Lean)",
  "github_connected": false,
  "event_timestamp": "2026-01-10T14:22:13.456Z",
  "event_source": "frontend"
}
```

---

#### Event 4: `project_viewed`

**Description**: Fired when a user views a project dashboard or details page.

**When Triggered**:
- GET `/api/v1/projects/{id}` called
- User navigates to project detail page

**Required Properties**:
```typescript
{
  // User Context
  user_id: string
  user_role: string

  // Project Context
  project_id: string
  project_name: string
  project_type: string
  project_tier: string

  // View Context
  view_source: string              // "dashboard_list" | "search" | "direct_link"
  time_on_page_seconds?: number    // Duration if tracked (on page exit)

  // Event Metadata
  event_timestamp: string
  event_source: string
}
```

**Example Payload**:
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_role": "dev",
  "project_id": "a1b2c3d4-e5f6-4a5b-8c7d-9e0f1a2b3c4d",
  "project_name": "Mobile App Redesign",
  "project_type": "idea",
  "project_tier": "PROFESSIONAL",
  "view_source": "dashboard_list",
  "event_timestamp": "2026-01-10T14:25:30.789Z",
  "event_source": "frontend"
}
```

---

### 5.3 AI Safety Layer Events (EP-02)

#### Event 5: `ai_pr_detected`

**Description**: Fired when a PR is detected as AI-generated by the AI Detection Service.

**When Triggered**:
- GitHubAIDetectionService returns `is_ai_generated=true`
- GitHub webhook triggers PR analysis

**Required Properties**:
```typescript
{
  // User Context
  user_id: string                  // PR author (if SDLC user)

  // Project Context
  project_id: string
  project_name: string

  // PR Context
  pr_number: string                // GitHub PR number
  pr_title: string                 // PR title (first 200 chars)
  pr_author: string                // GitHub username

  // AI Detection Context
  ai_tool_detected: string         // "cursor" | "copilot" | "claude" | "chatgpt" | "unknown"
  ai_model_detected?: string       // "gpt-4" | "claude-3.5-sonnet" | null
  detection_confidence: number     // 0.0 - 1.0 (e.g., 0.87)
  detection_method: string         // "metadata" | "github_api" | "manual" | "combined"
  detection_strategies_used: string[]  // ["metadata", "github_api"]

  // Event Metadata
  event_timestamp: string
  event_source: string             // "backend" (always backend for this event)
}
```

**Example Payload**:
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "project_id": "a1b2c3d4-e5f6-4a5b-8c7d-9e0f1a2b3c4d",
  "project_name": "Mobile App Redesign",
  "pr_number": "42",
  "pr_title": "Implement user authentication with OAuth",
  "pr_author": "john_doe_github",
  "ai_tool_detected": "cursor",
  "ai_model_detected": "gpt-4",
  "detection_confidence": 0.87,
  "detection_method": "combined",
  "detection_strategies_used": ["metadata", "github_api"],
  "event_timestamp": "2026-01-10T15:10:22.345Z",
  "event_source": "backend"
}
```

**Backend Implementation Location**: `backend/app/services/ai_detection_service.py:detect_ai_code()`

---

#### Event 6: `ai_safety_validation`

**Description**: Fired when AI-generated code completes validation pipeline (lint, tests, coverage, SAST).

**When Triggered**:
- ValidationPipeline completes all validators
- POST `/api/v1/ai-safety/validate` returns results

**Required Properties**:
```typescript
{
  // User Context
  user_id: string

  // Project Context
  project_id: string
  project_name: string

  // PR Context
  pr_number: string
  pr_title: string

  // Validation Results
  validation_status: string        // "passed" | "failed" | "partial"
  validators_run: string[]         // ["lint", "tests", "coverage", "sast"]
  validators_passed: string[]      // ["lint", "tests"]
  validators_failed: string[]      // ["coverage", "sast"]
  validation_duration_seconds: number  // Pipeline execution time

  // Detailed Results
  lint_result?: string             // "pass" | "fail" | "not_run"
  tests_result?: string
  coverage_result?: string
  coverage_percentage?: number     // 0-100 (if coverage run)
  sast_result?: string
  sast_issues_found?: number       // Count of security issues

  // Event Metadata
  event_timestamp: string
  event_source: string
}
```

**Example Payload**:
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "project_id": "a1b2c3d4-e5f6-4a5b-8c7d-9e0f1a2b3c4d",
  "project_name": "Mobile App Redesign",
  "pr_number": "42",
  "pr_title": "Implement user authentication with OAuth",
  "validation_status": "partial",
  "validators_run": ["lint", "tests", "coverage", "sast"],
  "validators_passed": ["lint", "tests"],
  "validators_failed": ["coverage", "sast"],
  "validation_duration_seconds": 245,
  "lint_result": "pass",
  "tests_result": "pass",
  "coverage_result": "fail",
  "coverage_percentage": 72,
  "sast_result": "fail",
  "sast_issues_found": 3,
  "event_timestamp": "2026-01-10T15:14:27.890Z",
  "event_source": "backend"
}
```

**Backend Implementation Location**: `backend/app/services/validation_pipeline.py:run_validation()`

---

#### Event 7: `policy_pack_applied`

**Description**: Fired when a policy pack is applied to a project (manual or AI-recommended).

**When Triggered**:
- POST `/api/v1/projects/{id}/apply-policy-pack` called
- User accepts AI-recommended policy pack during project creation

**Required Properties**:
```typescript
{
  // User Context
  user_id: string
  user_role: string

  // Project Context
  project_id: string
  project_name: string
  project_tier: string

  // Policy Pack Context
  policy_pack_name: string         // "Startup SDLC (Lean)" | "Enterprise SDLC (Strict)"
  policy_pack_source: string       // "ai_recommended" | "manual_selection" | "default"
  policies_count: number           // Number of policies in pack
  mandatory_policies_count: number // Number of MANDATORY policies

  // Event Metadata
  event_timestamp: string
  event_source: string
}
```

**Example Payload**:
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_role": "pm",
  "project_id": "a1b2c3d4-e5f6-4a5b-8c7d-9e0f1a2b3c4d",
  "project_name": "Mobile App Redesign",
  "project_tier": "PROFESSIONAL",
  "policy_pack_name": "Startup SDLC (Lean)",
  "policy_pack_source": "ai_recommended",
  "policies_count": 25,
  "mandatory_policies_count": 8,
  "event_timestamp": "2026-01-10T14:22:18.123Z",
  "event_source": "frontend"
}
```

---

#### Event 8: `policy_guard_blocked`

**Description**: Fired when OPA Policy Guard blocks AI-generated code from merging due to policy violation.

**When Triggered**:
- OPA policy evaluation returns `deny` decision
- PR merge blocked by Policy Guard

**Required Properties**:
```typescript
{
  // User Context
  user_id: string

  // Project Context
  project_id: string
  project_name: string

  // PR Context
  pr_number: string
  pr_title: string

  // Policy Context
  policy_name: string              // "no_ai_in_auth_modules"
  policy_rule: string              // OPA rule that failed
  policy_severity: string          // "critical" | "high" | "medium" | "low"
  policy_message: string           // "AI code not allowed in authentication modules"

  // Block Context
  blocking_reason: string          // "mandatory_policy_fail" | "validation_fail"
  files_affected: string[]         // Files that triggered policy
  vcr_override_available: boolean  // true if VCR override allowed

  // Event Metadata
  event_timestamp: string
  event_source: string
}
```

**Example Payload**:
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "project_id": "a1b2c3d4-e5f6-4a5b-8c7d-9e0f1a2b3c4d",
  "project_name": "Mobile App Redesign",
  "pr_number": "42",
  "pr_title": "Implement user authentication with OAuth",
  "policy_name": "no_ai_in_auth_modules",
  "policy_rule": "ai_safety.critical_paths.deny",
  "policy_severity": "critical",
  "policy_message": "AI code not allowed in authentication modules",
  "blocking_reason": "mandatory_policy_fail",
  "files_affected": ["backend/app/api/routes/auth.py", "backend/app/services/auth_service.py"],
  "vcr_override_available": true,
  "event_timestamp": "2026-01-10T15:18:45.678Z",
  "event_source": "backend"
}
```

**Backend Implementation Location**: `backend/app/services/policy_guard_service.py:evaluate_policy()`

---

### 5.4 Idea Flow Events (EP-01)

#### Event 9: `idea_submitted`

**Description**: Fired when a user submits a new idea through the "Ý tưởng mới" flow.

**When Triggered**:
- POST `/api/v1/ideas` returns 201 Created
- User completes "Submit Idea" wizard

**Required Properties**:
```typescript
{
  // User Context
  user_id: string
  user_role: string

  // Idea Context
  idea_id: string                  // UUID of new idea
  idea_title: string               // First 200 chars
  idea_category: string            // "feature" | "product" | "improvement" | "other"

  // AI Classification Context
  ai_classified: boolean           // true if AI classified idea
  ai_suggested_risk: string        // "low" | "medium" | "high" | null
  ai_suggested_policy_pack?: string  // Policy pack recommended by AI
  ai_classification_confidence?: number  // 0.0 - 1.0

  // User Actions
  user_accepted_ai_suggestions: boolean  // true if user accepted AI recommendations
  user_modified_ai_suggestions: boolean  // true if user manually changed AI suggestions

  // Event Metadata
  event_timestamp: string
  event_source: string
}
```

**Example Payload**:
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_role": "pm",
  "idea_id": "b2c3d4e5-f6a7-5b6c-9d8e-0f1a2b3c4d5e",
  "idea_title": "Add dark mode to mobile app",
  "idea_category": "feature",
  "ai_classified": true,
  "ai_suggested_risk": "low",
  "ai_suggested_policy_pack": "Startup SDLC (Lean)",
  "ai_classification_confidence": 0.92,
  "user_accepted_ai_suggestions": true,
  "user_modified_ai_suggestions": false,
  "event_timestamp": "2026-01-10T16:30:12.345Z",
  "event_source": "frontend"
}
```

**Frontend Implementation Location**: `frontend/web/src/components/ideas/IdeaSubmissionWizard.tsx`

---

#### Event 10: `stalled_project_analyzed`

**Description**: Fired when a user analyzes a stalled project through the "Dự án dở dang" flow.

**When Triggered**:
- POST `/api/v1/projects/{id}/analyze-stalled` completes
- User runs gap analysis on repository

**Required Properties**:
```typescript
{
  // User Context
  user_id: string
  user_role: string

  // Project Context
  project_id: string
  project_name: string
  project_type: string             // "stalled" (always for this event)

  // Repository Context
  repo_url: string                 // GitHub repo URL
  repo_language: string            // "python" | "typescript" | "java" | "go" | etc
  repo_file_count: number          // Files scanned

  // Gap Analysis Results
  gaps_found_count: number         // Total gaps detected
  gaps_critical_count: number      // Critical gaps
  gaps_high_count: number          // High priority gaps
  gaps_medium_count: number        // Medium priority gaps

  // AI Recommendations
  ai_recommended_actions: string[]  // ["add_tests", "fix_security", "document_api"]
  ai_estimated_effort_hours?: number  // AI estimate to fix all gaps

  // Analysis Performance
  analysis_duration_seconds: number  // Time to complete scan

  // Event Metadata
  event_timestamp: string
  event_source: string
}
```

**Example Payload**:
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_role": "pm",
  "project_id": "c3d4e5f6-a7b8-6c7d-0e9f-1a2b3c4d5e6f",
  "project_name": "Legacy E-commerce Platform",
  "project_type": "stalled",
  "repo_url": "https://github.com/acme-corp/legacy-ecommerce",
  "repo_language": "python",
  "repo_file_count": 342,
  "gaps_found_count": 18,
  "gaps_critical_count": 3,
  "gaps_high_count": 7,
  "gaps_medium_count": 8,
  "ai_recommended_actions": ["add_tests", "fix_security_vulnerabilities", "update_dependencies", "document_api"],
  "ai_estimated_effort_hours": 120,
  "analysis_duration_seconds": 45,
  "event_timestamp": "2026-01-10T17:15:33.567Z",
  "event_source": "backend"
}
```

**Backend Implementation Location**: `backend/app/services/stalled_project_service.py:analyze_gaps()`

---

## 6. Event Properties Schema

### 6.1 Common Properties (All Events)

**Required in Every Event**:
```typescript
{
  event_timestamp: string          // ISO8601 UTC (e.g., "2026-01-10T10:30:45.123Z")
  event_source: string             // "frontend" | "backend" | "cli"
  event_name: string               // Event name (e.g., "user_login")
  event_version: string            // "1.0" (for schema versioning)
}
```

**User Context** (if user authenticated):
```typescript
{
  user_id: string                  // UUID
  user_email_hash?: string         // SHA256 hash (GDPR compliance)
  user_role?: string               // "owner" | "admin" | "pm" | "dev" | "qa"
  user_is_superuser?: boolean      // true | false
}
```

**Session Context** (if session exists):
```typescript
{
  session_id: string               // UUID of session
  session_duration_seconds?: number  // Duration since login
}
```

**Device Context** (frontend events only):
```typescript
{
  device_type: string              // "web" | "mobile" | "desktop"
  browser?: string                 // User agent (e.g., "Chrome 120")
  os?: string                      // Operating system (e.g., "macOS 14")
  screen_resolution?: string       // "1920x1080" | "2560x1440"
  viewport_size?: string           // "1200x800" (browser window size)
}
```

### 6.2 Project Context Properties

**When Event Involves a Project**:
```typescript
{
  project_id: string               // UUID
  project_name: string             // Project name (first 100 chars)
  project_type: string             // "idea" | "stalled" | "standard"
  project_tier: string             // "LITE" | "STANDARD" | "PROFESSIONAL" | "ENTERPRISE"
  project_created_at?: string      // ISO8601 timestamp
  project_owner_id?: string        // UUID of project owner
}
```

### 6.3 AI Context Properties

**When Event Involves AI Detection or Recommendations**:
```typescript
{
  ai_tool_detected?: string        // "cursor" | "copilot" | "claude" | "chatgpt" | "unknown"
  ai_model_detected?: string       // "gpt-4" | "claude-3.5-sonnet" | "gemini-pro"
  ai_classified?: boolean          // true if AI classified
  ai_classification_confidence?: number  // 0.0 - 1.0
  ai_suggested_risk?: string       // "low" | "medium" | "high"
  ai_suggested_policy_pack?: string  // Policy pack name
}
```

### 6.4 GitHub/Repository Context

**When Event Involves GitHub Integration**:
```typescript
{
  pr_number?: string               // GitHub PR number
  pr_title?: string                // PR title (first 200 chars)
  pr_author?: string               // GitHub username
  pr_url?: string                  // Full GitHub PR URL
  repo_url?: string                // Repository URL
  repo_language?: string           // Primary language
  repo_file_count?: number         // Files in repo
}
```

---

## 7. Implementation Architecture

### 7.1 Backend Service Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ API Endpoints (FastAPI)                                    │
│ - POST /api/v1/auth/login → track("user_login")           │
│ - POST /api/v1/projects → track("project_created")        │
│ - POST /api/v1/ai-safety/validate → track("ai_safety_...")│
└──────────────────┬──────────────────────────────────────────┘
                   │
┌──────────────────┴──────────────────────────────────────────┐
│ AnalyticsService (backend/app/services/analytics.py)       │
│                                                             │
│ async def track_event(                                     │
│     event_name: str,                                       │
│     properties: Dict[str, Any],                            │
│     user_id: Optional[UUID] = None,                        │
│ ) -> bool:                                                 │
│     # 1. Enrich with common properties                     │
│     # 2. Hash PII (user_email → SHA256)                    │
│     # 3. Send to Mixpanel + Amplitude in parallel          │
│     # 4. Handle failures gracefully (no blocking)          │
└──────────────────┬──────────────────────────────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
┌───────▼─────────┐  ┌───────▼─────────┐
│ MixpanelClient  │  │ AmplitudeClient │
│ (HTTP API)      │  │ (HTTP API)      │
└─────────────────┘  └─────────────────┘
```

### 7.2 AnalyticsService Implementation

**File**: `backend/app/services/analytics_service.py`

```python
"""
Analytics Service for SDLC Orchestrator
Tracks user behavior, AI Safety adoption, and Design Partner engagement.

Sprint 41 - AI Safety Foundation (Week 1)
"""

import hashlib
import logging
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)


class AnalyticsService:
    """
    Centralized analytics service for tracking events to Mixpanel/Amplitude.

    Features:
    - Dual platform support (Mixpanel + Amplitude)
    - Automatic PII hashing (GDPR compliance)
    - Common property enrichment
    - Graceful error handling (no blocking)
    - Async batch processing
    """

    def __init__(self):
        self.mixpanel_token = settings.MIXPANEL_TOKEN
        self.amplitude_api_key = settings.AMPLITUDE_API_KEY
        self.enabled = settings.ANALYTICS_ENABLED  # Feature flag

        # HTTP client for async requests
        self.http_client = httpx.AsyncClient(timeout=5.0)

    async def track_event(
        self,
        event_name: str,
        properties: Dict[str, Any],
        user_id: Optional[UUID] = None,
    ) -> bool:
        """
        Track an analytics event to Mixpanel and Amplitude.

        Args:
            event_name: Event name (e.g., "user_login")
            properties: Event properties dict
            user_id: Optional user UUID (will be stringified)

        Returns:
            True if event sent successfully to at least one platform

        Example:
            await analytics.track_event(
                event_name="user_login",
                properties={
                    "auth_method": "oauth_google",
                    "device_type": "web",
                },
                user_id=UUID("550e8400-e29b-41d4-a716-446655440000"),
            )
        """
        if not self.enabled:
            logger.debug(f"Analytics disabled, skipping event: {event_name}")
            return False

        try:
            # 1. Enrich with common properties
            enriched = self._enrich_properties(properties, user_id)

            # 2. Hash PII fields
            enriched = self._hash_pii(enriched)

            # 3. Add event metadata
            enriched["event_name"] = event_name
            enriched["event_version"] = "1.0"
            enriched["event_timestamp"] = datetime.utcnow().isoformat() + "Z"

            # 4. Send to platforms (parallel, non-blocking)
            results = await asyncio.gather(
                self._send_to_mixpanel(event_name, enriched, user_id),
                self._send_to_amplitude(event_name, enriched, user_id),
                return_exceptions=True,  # Don't fail if one platform errors
            )

            # Success if at least one platform succeeded
            success = any(r is True for r in results if not isinstance(r, Exception))

            if not success:
                logger.warning(f"Failed to send event {event_name} to all platforms")

            return success

        except Exception as e:
            # NEVER block application flow due to analytics errors
            logger.error(f"Analytics error for {event_name}: {str(e)}", exc_info=True)
            return False

    def _enrich_properties(
        self, properties: Dict[str, Any], user_id: Optional[UUID]
    ) -> Dict[str, Any]:
        """
        Add common properties to all events.

        Adds:
        - user_id (if provided)
        - environment (dev, staging, prod)
        - app_version
        """
        enriched = properties.copy()

        if user_id:
            enriched["user_id"] = str(user_id)

        enriched["environment"] = settings.ENVIRONMENT  # "dev" | "staging" | "prod"
        enriched["app_version"] = settings.APP_VERSION  # "1.0.0"

        return enriched

    def _hash_pii(self, properties: Dict[str, Any]) -> Dict[str, Any]:
        """
        Hash PII fields for GDPR compliance.

        Hashes:
        - user_email → user_email_hash (SHA256)
        - Any field ending with _email → {field}_hash
        """
        hashed = properties.copy()

        for key, value in properties.items():
            if key.endswith("_email") and isinstance(value, str):
                # Hash email to SHA256
                hash_key = key.replace("_email", "_email_hash")
                hashed[hash_key] = hashlib.sha256(value.encode()).hexdigest()

                # Remove original email
                del hashed[key]

        return hashed

    async def _send_to_mixpanel(
        self, event_name: str, properties: Dict[str, Any], user_id: Optional[UUID]
    ) -> bool:
        """Send event to Mixpanel via HTTP API."""
        try:
            payload = {
                "event": event_name,
                "properties": {
                    "token": self.mixpanel_token,
                    "distinct_id": str(user_id) if user_id else "anonymous",
                    **properties,
                },
            }

            response = await self.http_client.post(
                "https://api.mixpanel.com/track",
                json=payload,
            )

            response.raise_for_status()
            logger.debug(f"Sent {event_name} to Mixpanel")
            return True

        except Exception as e:
            logger.warning(f"Mixpanel error for {event_name}: {str(e)}")
            return False

    async def _send_to_amplitude(
        self, event_name: str, properties: Dict[str, Any], user_id: Optional[UUID]
    ) -> bool:
        """Send event to Amplitude via HTTP API."""
        try:
            payload = {
                "api_key": self.amplitude_api_key,
                "events": [
                    {
                        "user_id": str(user_id) if user_id else "anonymous",
                        "event_type": event_name,
                        "event_properties": properties,
                        "time": int(datetime.utcnow().timestamp() * 1000),  # Milliseconds
                    }
                ],
            }

            response = await self.http_client.post(
                "https://api2.amplitude.com/2/httpapi",
                json=payload,
            )

            response.raise_for_status()
            logger.debug(f"Sent {event_name} to Amplitude")
            return True

        except Exception as e:
            logger.warning(f"Amplitude error for {event_name}: {str(e)}")
            return False

    async def close(self):
        """Close HTTP client on shutdown."""
        await self.http_client.aclose()


# Singleton instance
analytics_service = AnalyticsService()
```

### 7.3 Frontend Hook Implementation

**File**: `frontend/web/src/hooks/useAnalytics.ts`

```typescript
/**
 * Analytics hook for tracking events from React components.
 *
 * Sprint 41 - AI Safety Foundation (Week 1)
 */

import { useCallback } from 'react'
import { apiClient } from '@/api/client'
import { useAuth } from '@/contexts/AuthContext'

interface TrackEventParams {
  eventName: string
  properties?: Record<string, any>
}

export function useAnalytics() {
  const { user } = useAuth()

  /**
   * Track an analytics event.
   *
   * Automatically enriches with:
   * - User ID (if authenticated)
   * - Device context (browser, OS, screen size)
   * - Event source ("frontend")
   *
   * Example:
   *   const { trackEvent } = useAnalytics()
   *   trackEvent({
   *     eventName: 'project_created',
   *     properties: {
   *       project_id: project.id,
   *       project_name: project.name,
   *       project_tier: 'PROFESSIONAL',
   *     },
   *   })
   */
  const trackEvent = useCallback(
    async ({ eventName, properties = {} }: TrackEventParams) => {
      try {
        // Enrich with device context
        const enrichedProperties = {
          ...properties,
          event_source: 'frontend',
          device_type: 'web',
          browser: navigator.userAgent,
          screen_resolution: `${window.screen.width}x${window.screen.height}`,
          viewport_size: `${window.innerWidth}x${window.innerHeight}`,
        }

        // Send to backend (which forwards to Mixpanel/Amplitude)
        await apiClient.post('/analytics/track', {
          event_name: eventName,
          properties: enrichedProperties,
          user_id: user?.id || null,
        })
      } catch (error) {
        // Never block user flow due to analytics errors
        console.warn(`Analytics error for ${eventName}:`, error)
      }
    },
    [user]
  )

  return { trackEvent }
}
```

### 7.4 Configuration (Environment Variables)

**File**: `backend/app/core/config.py`

```python
class Settings(BaseSettings):
    # ... existing settings ...

    # Analytics Configuration (Sprint 41)
    ANALYTICS_ENABLED: bool = Field(True, env="ANALYTICS_ENABLED")
    MIXPANEL_TOKEN: str = Field("", env="MIXPANEL_TOKEN")
    AMPLITUDE_API_KEY: str = Field("", env="AMPLITUDE_API_KEY")

    # Privacy Configuration
    ANALYTICS_HASH_PII: bool = Field(True, env="ANALYTICS_HASH_PII")  # Always hash emails
```

**File**: `.env.example`

```bash
# Analytics Configuration (Sprint 41)
ANALYTICS_ENABLED=true
MIXPANEL_TOKEN=your_mixpanel_project_token_here
AMPLITUDE_API_KEY=your_amplitude_api_key_here
ANALYTICS_HASH_PII=true
```

---

## 8. Privacy & Compliance

### 8.1 GDPR Compliance

**Data Minimization**:
- ✅ Only collect properties necessary for analytics
- ✅ No sensitive data (passwords, API keys, tokens)
- ✅ Hash all email addresses (SHA256)
- ✅ No IP address collection (Mixpanel/Amplitude configurable)

**User Consent**:
- ✅ Analytics opt-out available in user settings
- ✅ Cookie banner with analytics consent checkbox
- ✅ Granular consent (essential vs analytics cookies)

**Data Retention**:
- ✅ Mixpanel: 2 years (configurable)
- ✅ Amplitude: 2 years (configurable)
- ✅ User can request data deletion (GDPR Article 17)

**Data Portability**:
- ✅ Export user's analytics data (GDPR Article 20)
- ✅ API endpoint: GET `/api/v1/users/me/analytics-export`

### 8.2 PII Hashing Strategy

**Email Hashing**:
```python
# Original email
user_email = "john.doe@acme.com"

# SHA256 hash (one-way, irreversible)
user_email_hash = "a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3"

# Stored in analytics
properties = {
    "user_email_hash": user_email_hash,  # ✅ GDPR-compliant
    # "user_email": user_email,  # ❌ NOT stored
}
```

**Why Hash?**:
- GDPR Article 6: Legitimate interest (analytics) requires minimizing PII
- Hashing is one-way (cannot reverse to original email)
- Still allows user-level analysis (same hash = same user)

**What We Hash**:
- ✅ All email addresses (user_email → user_email_hash)
- ✅ Any field ending in `_email`
- ❌ User IDs (UUID, not PII)
- ❌ Project names (not PII, needed for context)

### 8.3 Analytics Opt-Out

**User Settings UI**:
```typescript
// frontend/web/src/components/settings/AnalyticsSettings.tsx

<Form>
  <Checkbox
    id="analytics_enabled"
    checked={analyticsEnabled}
    onChange={handleToggle}
  />
  <Label htmlFor="analytics_enabled">
    Enable product analytics
  </Label>
  <HelpText>
    Help us improve SDLC Orchestrator by sharing anonymous usage data.
    No personally identifiable information (PII) is collected.
    You can opt out anytime.
  </HelpText>
</Form>
```

**Backend Enforcement**:
```python
# backend/app/services/analytics_service.py

async def track_event(self, event_name: str, properties: Dict, user_id: Optional[UUID]):
    # Check user's analytics preference
    if user_id:
        user = await db.query(User).filter(User.id == user_id).first()
        if not user.analytics_enabled:
            logger.debug(f"User {user_id} opted out of analytics")
            return False  # Don't track

    # Proceed with tracking...
```

### 8.4 Data Deletion (GDPR Article 17)

**User Requests Data Deletion**:
1. User submits request: POST `/api/v1/users/me/delete-analytics-data`
2. Backend calls Mixpanel/Amplitude deletion APIs
3. Mixpanel: `https://api.mixpanel.com/engage#profile-delete`
4. Amplitude: `https://amplitude.com/api/2/deletions/users`
5. Confirmation email sent to user

**Implementation**:
```python
# backend/app/api/routes/users.py

@router.post("/me/delete-analytics-data")
async def delete_analytics_data(
    current_user: User = Depends(get_current_user),
):
    """
    Delete user's analytics data from Mixpanel and Amplitude.
    GDPR Article 17 (Right to Erasure).
    """
    # Call Mixpanel deletion API
    await analytics_service.delete_user_data(current_user.id)

    # Mark user's analytics as deleted
    current_user.analytics_deleted_at = datetime.utcnow()
    await db.commit()

    return {"message": "Analytics data deletion initiated"}
```

---

## 9. Testing & Validation

### 9.1 Event Schema Validation

**Unit Tests** (`backend/tests/services/test_analytics_service.py`):

```python
import pytest
from app.services.analytics_service import AnalyticsService


@pytest.mark.asyncio
async def test_track_user_login_event():
    """Test user_login event has correct schema."""
    analytics = AnalyticsService()

    # Mock HTTP client to capture payload
    with patch.object(analytics.http_client, "post") as mock_post:
        mock_post.return_value = Mock(status_code=200)

        await analytics.track_event(
            event_name="user_login",
            properties={
                "auth_method": "oauth_google",
                "device_type": "web",
                "browser": "Chrome 120",
            },
            user_id=UUID("550e8400-e29b-41d4-a716-446655440000"),
        )

        # Assert Mixpanel payload
        call_args = mock_post.call_args_list[0]  # First call (Mixpanel)
        payload = call_args[1]["json"]

        assert payload["event"] == "user_login"
        assert payload["properties"]["auth_method"] == "oauth_google"
        assert payload["properties"]["user_id"] == "550e8400-e29b-41d4-a716-446655440000"
        assert "event_timestamp" in payload["properties"]


@pytest.mark.asyncio
async def test_pii_hashing():
    """Test email addresses are hashed."""
    analytics = AnalyticsService()

    properties = {
        "user_email": "john.doe@acme.com",
        "team_email": "team@acme.com",
    }

    hashed = analytics._hash_pii(properties)

    # Original emails removed
    assert "user_email" not in hashed
    assert "team_email" not in hashed

    # Hashed versions present
    assert "user_email_hash" in hashed
    assert "team_email_hash" in hashed
    assert len(hashed["user_email_hash"]) == 64  # SHA256 = 64 hex chars
```

### 9.2 Integration Tests

**E2E Test** (`backend/tests/integration/test_analytics_flow.py`):

```python
@pytest.mark.asyncio
async def test_full_analytics_flow(client: AsyncClient, test_user: User):
    """Test full analytics flow: login → create project → track events."""

    # 1. Login (should track user_login)
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "testuser", "password": "password123"},
    )
    assert response.status_code == 200

    # 2. Create project (should track project_created)
    response = await client.post(
        "/api/v1/projects",
        json={
            "name": "Test Project",
            "type": "idea",
            "tier": "PROFESSIONAL",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201

    # 3. Verify events sent to analytics platform
    # (Mock Mixpanel/Amplitude HTTP calls)
    # Assert 2 events tracked: user_login, project_created
```

### 9.3 Production Smoke Test

**Sprint 41 Week 2 Checklist**:
- [ ] Deploy to production with analytics enabled
- [ ] Trigger each of 10 events manually (via UI or API)
- [ ] Verify events appear in Mixpanel dashboard within 5 minutes
- [ ] Verify events appear in Amplitude dashboard within 5 minutes
- [ ] Check event properties match schema (no missing fields)
- [ ] Verify PII hashing (no plaintext emails in Mixpanel)
- [ ] Test analytics opt-out (user setting works)

**Acceptance Criteria**:
- ✅ 100+ events tracked within 48 hours of deployment
- ✅ 10/10 core events validated in Mixpanel
- ✅ 0 schema validation errors
- ✅ 0 PII leaks (manual audit)

---

## 10. Success Metrics

### 10.1 Sprint 41 Week 2 Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Events Tracked** | ≥100 in 48h | Mixpanel dashboard |
| **Schema Compliance** | 100% | Automated validation |
| **PII Leaks** | 0 | Manual audit |
| **Event Delivery Rate** | ≥95% | Success rate in logs |
| **Analytics Latency** | <5min p95 | Event → Dashboard delay |

### 10.2 Sprint 42-43 Targets (Design Partners Active)

| Event | Weekly Volume | Purpose |
|-------|---------------|---------|
| `user_login` | ≥100 | Partner engagement |
| `project_created` | ≥20 | Adoption rate |
| `project_viewed` | ≥200 | Activity level |
| `ai_pr_detected` | ≥50 | AI Safety Layer usage |
| `ai_safety_validation` | ≥50 | Validation pipeline usage |
| `policy_pack_applied` | ≥15 | Policy adoption |
| `policy_guard_blocked` | ≥5 | Policy enforcement |
| `idea_submitted` | ≥10 | EP-01 Idea Flow usage |
| `stalled_project_analyzed` | ≥5 | EP-01 Stalled Flow usage |
| `user_logout` | ≥80 | Session completion |

### 10.3 Key Analytics Dashboards

**Dashboard 1: Design Partner Engagement** (Mixpanel)
- Daily Active Users (DAU)
- Weekly Active Users (WAU)
- Retention curve (Day 1, Day 7, Day 30)
- Top 10 most active partners

**Dashboard 2: AI Safety Adoption** (Mixpanel)
- AI PRs detected per week
- AI PR detection accuracy (confidence distribution)
- Validation pipeline pass/fail rate
- Policy Guard block rate
- VCR override rate

**Dashboard 3: Idea Flow Adoption** (Amplitude)
- Ideas submitted per week
- AI classification acceptance rate
- Stalled projects analyzed per week
- Gap analysis completion rate

---

## 11. Appendix

### 11.1 Event Tracking Checklist (Implementation)

**Backend Events** (8/10):
- [ ] `user_login` - POST `/api/v1/auth/login`
- [ ] `user_logout` - POST `/api/v1/auth/logout`
- [ ] `project_created` - POST `/api/v1/projects`
- [ ] `ai_pr_detected` - GitHubAIDetectionService
- [ ] `ai_safety_validation` - ValidationPipeline
- [ ] `policy_guard_blocked` - PolicyGuardService
- [ ] `idea_submitted` - POST `/api/v1/ideas`
- [ ] `stalled_project_analyzed` - POST `/api/v1/projects/{id}/analyze-stalled`

**Frontend Events** (2/10):
- [ ] `project_viewed` - ProjectDetailPage mount
- [ ] `policy_pack_applied` - PolicyPackSelector component

### 11.2 Example Mixpanel Dashboard Queries

**Query 1: AI PR Detection Accuracy**
```javascript
// Mixpanel Insights query
function main() {
  return Events({
    from_date: '2026-01-10',
    to_date: '2026-01-17',
    event_selectors: [{event: 'ai_pr_detected'}],
  })
  .groupBy(['detection_method'], mixpanel.reducer.avg('detection_confidence'))
  .orderBy('value', 'descending')
}

// Expected output:
// detection_method      avg_confidence
// combined              0.87
// github_api            0.85
// metadata              0.70
// manual                1.00
```

**Query 2: Policy Guard Block Rate**
```javascript
// Mixpanel Funnels query
function main() {
  return Funnels({
    from_date: '2026-01-10',
    to_date: '2026-01-17',
    steps: [
      {event: 'ai_pr_detected'},
      {event: 'ai_safety_validation'},
      {event: 'policy_guard_blocked'},
    ],
  })
}

// Expected output:
// Step 1: ai_pr_detected         100 PRs (100%)
// Step 2: ai_safety_validation   100 PRs (100%)
// Step 3: policy_guard_blocked     5 PRs (5%)
// → Block rate = 5%
```

### 11.3 Amplitude Cohort Definitions

**Cohort 1: Active Design Partners**
- Definition: Users who triggered ≥10 events in past 7 days
- Purpose: Identify highly engaged partners for case studies

**Cohort 2: AI Safety Adopters**
- Definition: Users who triggered `ai_pr_detected` ≥5 times in past 7 days
- Purpose: Track AI Safety Layer adoption

**Cohort 3: Idea Flow Users**
- Definition: Users who triggered `idea_submitted` ≥1 time in past 30 days
- Purpose: Track EP-01 adoption

### 11.4 Privacy Audit Checklist

**Pre-Production Checklist**:
- [ ] All email fields hashed (search codebase for `user_email:`)
- [ ] No passwords in analytics properties
- [ ] No API keys/tokens in analytics properties
- [ ] Cookie banner deployed with analytics consent
- [ ] User settings page has "Disable Analytics" toggle
- [ ] Data deletion API endpoint tested
- [ ] Mixpanel IP anonymization enabled
- [ ] Amplitude IP anonymization enabled

**Monthly Audit**:
- [ ] Manual review of 100 random Mixpanel events (no PII)
- [ ] Manual review of 100 random Amplitude events (no PII)
- [ ] Verify data retention policies (2 years max)
- [ ] Review user opt-out rate (<5% threshold)

### 11.5 Cost Estimation (Year 1)

**Mixpanel Free Tier**:
- Limit: 100,000 events/month
- Estimated usage (6 Design Partners): ~10,000 events/month
- **Cost**: $0/month ✅

**Amplitude Free Tier**:
- Limit: 10,000,000 events/month
- Estimated usage: ~10,000 events/month
- **Cost**: $0/month ✅

**Upgrade Path (if needed)**:
- Mixpanel Growth Plan: $25/month (1M events)
- Amplitude Starter Plan: $49/month (unlimited events)
- **Decision Point**: If events >80K/month, upgrade Mixpanel

**Total Year 1 Cost**: $0 (both platforms stay on free tier)

---

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | Dec 20, 2025 | Product Team + Backend Team | Initial version - 10 core events |

---

**Status**: ✅ **DESIGN APPROVED**
**Next Step**: Implementation (Sprint 41 Week 1 - Jan 6-10, 2026)
**Owner**: Backend Lead (AnalyticsService) + Frontend Lead (useAnalytics hook)
**Review**: CTO approval required before implementation kickoff

---

*SDLC Orchestrator - Analytics Events Taxonomy v1.0. Privacy-first, GDPR-compliant, actionable insights.*
