# API Versioning Strategy
## Semantic Versioning + URL-Based Versioning

**Version**: 2.0.0
**Date**: December 21, 2025
**Status**: ACTIVE - EP-04/05/06 EXTENDED
**Authority**: Backend Lead + CTO Review (✅ APPROVED)
**Foundation**: API Specification v3.0.0, NFR v3.0.0, Roadmap v4.1.0
**Stage**: Stage 01 (WHAT - Planning & Analysis)
**Framework**: SDLC 6.1.0 (7-Pillar + Section 7 Quality Assurance + Section 8 Specification Standard)

**Changelog**:
- v2.0.0 (Dec 21, 2025): SDLC 5.1.3 update, EP-04/05/06 API versioning strategy
- v1.0.0 (Nov 13, 2025): Initial versioning strategy

---

## Table of Contents

1. [Versioning Philosophy](#1-versioning-philosophy)
2. [Versioning Scheme](#2-versioning-scheme)
3. [REST API Versioning](#3-rest-api-versioning)
4. [GraphQL API Versioning](#4-graphql-api-versioning)
5. [Breaking vs Non-Breaking Changes](#5-breaking-vs-non-breaking-changes)
6. [Deprecation Policy](#6-deprecation-policy)
7. [Version Lifecycle](#7-version-lifecycle)
8. [Client Migration Strategy](#8-client-migration-strategy)
9. [Backward Compatibility](#9-backward-compatibility)
10. [Version Discovery](#10-version-discovery)

---

## 1. Versioning Philosophy

### 1.1 Core Principles

**Stability First**: API contracts are sacred - breaking changes require major version bump.

**Client-Centric**: Minimize disruption to client integrations (VS Code Ext, CLI, third-party tools).

**Long-Term Support (LTS)**: Each major version supported for 18 months minimum.

**Transparent Communication**: 90-day advance notice for deprecations.

### 1.2 Target Audiences

| Audience | Integration Method | Versioning Impact |
|----------|-------------------|-------------------|
| **VS Code Extension** | REST API + GraphQL | High - requires coordinated releases |
| **CLI (`sdlcctl`)** | REST API only | High - version locking required |
| **Third-Party Tools** | REST API (webhooks) | Medium - gradual migration path |
| **CI/CD Pipelines** | API keys + REST | Critical - zero downtime required |
| **Mobile Apps (Future)** | GraphQL only | Medium - auto-update strategy |

### 1.3 Design Decisions

**Decision 1: URL-Based Versioning (REST)**
- **Why**: Explicit, discoverable, cache-friendly (CDN can route by URL)
- **Example**: `https://api.sdlc-orchestrator.com/v1/projects`
- **Rejected Alternatives**: Header-based versioning (harder to debug, cache, document)

**Decision 2: Schema Versioning (GraphQL)**
- **Why**: GraphQL has built-in deprecation, no need for URL versioning
- **Example**: `@deprecated(reason: "Use newField instead. Removal in v2.0")`
- **Rejected Alternatives**: URL-based (violates GraphQL single-endpoint principle)

**Decision 3: Semantic Versioning (SemVer)**
- **Why**: Industry standard, clear communication of change magnitude
- **Example**: `v1.2.3` (MAJOR.MINOR.PATCH)
- **Rejected Alternatives**: Date-based versioning (less semantic meaning)

---

## 2. Versioning Scheme

### 2.1 Semantic Versioning (SemVer)

**Format**: `vMAJOR.MINOR.PATCH`

| Component | When to Increment | Example Change |
|-----------|-------------------|----------------|
| **MAJOR** | Breaking changes | Removed endpoint, changed response structure |
| **MINOR** | New features (backward-compatible) | New endpoint, new optional field |
| **PATCH** | Bug fixes (backward-compatible) | Fixed error handling, performance improvement |

**Examples**:
- `v1.0.0` → `v1.0.1`: Fixed pagination bug in `/projects` endpoint (PATCH)
- `v1.0.1` → `v1.1.0`: Added `/gates/{id}/comments` endpoint (MINOR)
- `v1.1.0` → `v2.0.0`: Removed `status` field from Project schema (MAJOR)

### 2.2 Version Format

**REST API URL**:
```
https://api.sdlc-orchestrator.com/v{MAJOR}/resource
```

**Example**:
```
https://api.sdlc-orchestrator.com/v1/projects
https://api.sdlc-orchestrator.com/v2/projects
```

**GraphQL Endpoint** (no version in URL):
```
https://api.sdlc-orchestrator.com/graphql
```

**Version Header** (optional for advanced clients):
```http
X-API-Version: 1.2.3
```

### 2.3 Version Numbering Strategy

**MVP (Year 1)**:
- Start at `v1.0.0` (no beta/alpha in production)
- Incremental releases: `v1.1.0`, `v1.2.0`, `v1.3.0`
- First breaking change → `v2.0.0` (expected Q3 2026)

**LTS Releases**:
- Every **6 months** → LTS release (e.g., `v1.0 LTS`, `v2.0 LTS`)
- LTS versions supported for **18 months** after successor release

**Rapid Releases**:
- Patch releases: Every **2 weeks** (bug fixes, security patches)
- Minor releases: Every **1-2 months** (new features, non-breaking)

---

## 3. REST API Versioning

### 3.1 URL-Based Versioning

**Pattern**: `/v{MAJOR}/resource`

**Example Endpoints**:
```http
# Version 1
GET https://api.sdlc-orchestrator.com/v1/projects
POST https://api.sdlc-orchestrator.com/v1/gates/{id}/approve

# Version 2 (hypothetical future)
GET https://api.sdlc-orchestrator.com/v2/projects
POST https://api.sdlc-orchestrator.com/v2/gates/{id}/approve
```

**Why MAJOR version only in URL?**
- MINOR/PATCH changes are backward-compatible
- Clients don't need to change URL for non-breaking updates
- Reduces client maintenance burden

### 3.2 Version Routing (Backend)

**Request Flow**:
```
Client Request → API Gateway → Version Router → v1 Handler OR v2 Handler
```

**Example (Node.js/Express)**:
```javascript
// Version Router
app.use('/v1', v1Router);
app.use('/v2', v2Router);

// v1 Handler
v1Router.get('/projects', async (req, res) => {
  // v1 logic (returns old schema)
  const projects = await ProjectService.listV1(req.user);
  res.json(projects);
});

// v2 Handler
v2Router.get('/projects', async (req, res) => {
  // v2 logic (returns new schema)
  const projects = await ProjectService.listV2(req.user);
  res.json(projects);
});
```

### 3.3 Default Version Handling

**No version in URL → Use latest stable**:
```http
# Client omits version
GET https://api.sdlc-orchestrator.com/projects

# Redirects to (302 Found)
GET https://api.sdlc-orchestrator.com/v1/projects
```

**Response Header**:
```http
HTTP/1.1 302 Found
Location: https://api.sdlc-orchestrator.com/v1/projects
X-API-Version: 1.2.3
```

**Why redirect?**
- Forces clients to be version-aware
- Prevents accidental breaking when v2 becomes default

### 3.4 Version Negotiation (Advanced)

**Custom Header** (for clients needing MINOR/PATCH control):
```http
GET https://api.sdlc-orchestrator.com/v1/projects
X-API-Version: 1.2.3
```

**Backend Logic**:
```javascript
// Parse version header
const requestedVersion = req.headers['x-api-version'] || 'latest';

// Validate version
if (!supportedVersions.includes(requestedVersion)) {
  return res.status(400).json({
    error: 'unsupported_version',
    message: `API version ${requestedVersion} is not supported`,
    supported_versions: supportedVersions
  });
}

// Route to specific handler
const handler = versionHandlers[requestedVersion];
return handler(req, res);
```

---

## 4. GraphQL API Versioning

### 4.1 Schema Evolution (NOT URL Versioning)

**GraphQL Best Practice**: Single endpoint, evolving schema with deprecation.

**Endpoint** (never changes):
```
https://api.sdlc-orchestrator.com/graphql
```

### 4.2 Field Deprecation

**Example Schema Evolution**:
```graphql
# v1.0 Schema
type Project {
  id: ID!
  name: String!
  status: String!  # Old field (to be removed in v2.0)
}

# v1.1 Schema (added new field)
type Project {
  id: ID!
  name: String!
  status: String! @deprecated(reason: "Use state instead. Removal in v2.0 (2026-06-01)")
  state: ProjectState!  # New field (enum-based, more type-safe)
}

enum ProjectState {
  PLANNING
  IN_PROGRESS
  COMPLETED
  ARCHIVED
}
```

**Client Migration Path**:
```graphql
# Old query (still works in v1.x)
query {
  projects {
    id
    name
    status
  }
}

# New query (recommended)
query {
  projects {
    id
    name
    state
  }
}
```

### 4.3 Type Deprecation

**Example**:
```graphql
# v1.0 Schema
type GateApproval {
  id: ID!
  gate_id: String!
  user_id: String!
  approved: Boolean!
}

# v1.1 Schema (deprecated type)
type GateApproval @deprecated(reason: "Use GateApprovalV2. Removal in v2.0") {
  id: ID!
  gate_id: String!
  user_id: String!
  approved: Boolean!
}

type GateApprovalV2 {
  id: ID!
  gate: Gate!  # Relationship instead of ID
  approver: User!  # Relationship instead of ID
  status: ApprovalStatus!  # Enum instead of Boolean
  approved_at: DateTime
  comment: String
}

enum ApprovalStatus {
  PENDING
  APPROVED
  REJECTED
  REVOKED
}
```

### 4.4 Introspection & Schema Discovery

**Clients can query schema**:
```graphql
query {
  __type(name: "Project") {
    fields {
      name
      isDeprecated
      deprecationReason
    }
  }
}
```

**Response**:
```json
{
  "data": {
    "__type": {
      "fields": [
        {
          "name": "id",
          "isDeprecated": false,
          "deprecationReason": null
        },
        {
          "name": "status",
          "isDeprecated": true,
          "deprecationReason": "Use state instead. Removal in v2.0 (2026-06-01)"
        },
        {
          "name": "state",
          "isDeprecated": false,
          "deprecationReason": null
        }
      ]
    }
  }
}
```

---

## 5. Breaking vs Non-Breaking Changes

### 5.1 Breaking Changes (Require MAJOR version bump)

**REST API**:
- ❌ Removed endpoint (e.g., `DELETE /v1/users/{id}` removed)
- ❌ Removed required field from request (e.g., `name` no longer required in `POST /projects`)
- ❌ Removed field from response (e.g., `created_at` removed from Project schema)
- ❌ Changed field type (e.g., `status: String` → `status: Number`)
- ❌ Renamed field (e.g., `user_id` → `owner_id`)
- ❌ Changed authentication method (e.g., JWT → OAuth only)
- ❌ Changed error response structure

**GraphQL API**:
- ❌ Removed type or field (after deprecation period)
- ❌ Changed field type (non-nullable → nullable is OK, reverse is breaking)
- ❌ Removed enum value
- ❌ Changed query/mutation signature (added required argument)

### 5.2 Non-Breaking Changes (MINOR or PATCH version)

**REST API**:
- ✅ Added new endpoint (e.g., `GET /v1/gates/{id}/history`)
- ✅ Added optional field to request (e.g., `description` in `POST /projects`)
- ✅ Added field to response (e.g., `updated_by` in Project schema)
- ✅ Added new query parameter (optional, e.g., `?include_archived=true`)
- ✅ Added new HTTP method to existing resource (e.g., `PATCH /projects/{id}`)
- ✅ Added new error code (e.g., `429 Too Many Requests`)
- ✅ Bug fix (e.g., fixed pagination offset calculation)

**GraphQL API**:
- ✅ Added new type
- ✅ Added new field to existing type
- ✅ Added new query or mutation
- ✅ Deprecated field (with `@deprecated` directive)
- ✅ Made field nullable (non-nullable → nullable)
- ✅ Added optional argument to query/mutation

### 5.3 Examples

**Breaking Change (v1 → v2)**:
```json
// v1 Response
{
  "id": "123",
  "name": "Project Alpha",
  "status": "active"  // String
}

// v2 Response (BREAKING: status removed, state added)
{
  "id": "123",
  "name": "Project Alpha",
  "state": "IN_PROGRESS"  // Enum
}
```

**Non-Breaking Change (v1.0 → v1.1)**:
```json
// v1.0 Response
{
  "id": "123",
  "name": "Project Alpha",
  "status": "active"
}

// v1.1 Response (NON-BREAKING: added field)
{
  "id": "123",
  "name": "Project Alpha",
  "status": "active",
  "created_by": "john@techcorp.com"  // New field
}
```

---

## 6. Deprecation Policy

### 6.1 Deprecation Timeline

**90-Day Advance Notice** (minimum):
- **Day 0**: Announce deprecation (changelog, email, in-app notification)
- **Day 30**: Add deprecation warnings to API responses
- **Day 60**: Send final migration reminder
- **Day 90**: Remove deprecated feature in next MAJOR version

**Example Timeline**:
```
2026-03-01: Announce deprecation of /v1/gates/{id}/approve
2026-04-01: Add X-Deprecation-Warning header to responses
2026-05-01: Send final migration email to all API key holders
2026-06-01: Release v2.0.0 (remove deprecated endpoint)
```

### 6.2 Deprecation Communication Channels

**1. Changelog** (`/docs/CHANGELOG.md`):
```markdown
## [1.5.0] - 2026-03-01

### Deprecated
- `POST /v1/gates/{id}/approve` - Use `POST /v1/gates/{id}/approvals` instead
  - **Removal Date**: 2026-06-01 (v2.0.0)
  - **Migration Guide**: See [API Migration Guide](./docs/migrations/v1-to-v2.md)
```

**2. API Response Headers**:
```http
HTTP/1.1 200 OK
X-Deprecation-Warning: This endpoint is deprecated. Use POST /v1/gates/{id}/approvals instead. Removal: 2026-06-01
Sunset: Sat, 01 Jun 2026 00:00:00 GMT
Link: <https://docs.sdlc-orchestrator.com/migrations/v1-to-v2>; rel="deprecation"
```

**3. Email Notifications**:
- Sent to all API key holders (from `users` table)
- 90 days, 60 days, 30 days, 7 days before removal

**4. In-App Notifications**:
- Banner in VS Code Extension
- Warning in CLI output (`sdlcctl`)

**5. Documentation**:
- Strikethrough in API docs
- "DEPRECATED" badge in OpenAPI spec

### 6.3 Deprecation Exceptions

**Security Vulnerabilities**: Immediate removal (no 90-day grace period)
- Example: JWT algorithm vulnerability discovered → disable immediately
- Mitigation: Provide emergency migration guide + support

**Critical Bugs**: Accelerated deprecation (30-day grace period)
- Example: Endpoint causing data corruption
- Mitigation: Provide temporary workaround until fix deployed

---

## 7. Version Lifecycle

### 7.1 Version Support Windows

| Version Type | Support Duration | Updates Included |
|--------------|------------------|------------------|
| **Current** | Until next MAJOR release | Bug fixes, security patches, new features |
| **Previous MAJOR** | 18 months after successor release | Critical bug fixes, security patches only |
| **End-of-Life (EOL)** | No support | No updates (decommissioned) |

**Example Lifecycle**:
```
v1.0 Released: 2025-11-13
v2.0 Released: 2026-06-01

Timeline:
- 2025-11-13 to 2026-06-01: v1.x is "Current" (full support)
- 2026-06-01 to 2027-12-01: v1.x is "Previous" (security patches only)
- 2027-12-01: v1.x is EOL (decommissioned)
```

### 7.2 Version Status API

**Endpoint**: `GET /version`

**Response**:
```json
{
  "current_version": "1.2.3",
  "latest_stable": "1.2.3",
  "supported_versions": [
    {
      "version": "2.0.0",
      "status": "current",
      "released_at": "2026-06-01T00:00:00Z",
      "eol_at": null
    },
    {
      "version": "1.2.3",
      "status": "previous",
      "released_at": "2025-11-13T00:00:00Z",
      "eol_at": "2027-12-01T00:00:00Z"
    }
  ],
  "deprecated_versions": [
    {
      "version": "1.0.0",
      "status": "eol",
      "released_at": "2025-11-13T00:00:00Z",
      "eol_at": "2026-06-01T00:00:00Z"
    }
  ]
}
```

### 7.3 Decommissioning Process

**30 Days Before EOL**:
- Send final email notification to all users still on old version
- Display blocking modal in VS Code Extension
- CLI shows error message + migration guide

**EOL Day**:
- API returns `410 Gone` for all deprecated version endpoints
- Redirect to migration guide documentation

**Example Response (after EOL)**:
```http
HTTP/1.1 410 Gone
Content-Type: application/json

{
  "error": "version_eol",
  "message": "API v1 reached end-of-life on 2027-12-01. Please upgrade to v2.",
  "migration_guide": "https://docs.sdlc-orchestrator.com/migrations/v1-to-v2",
  "current_version": "2.1.0"
}
```

---

## 8. Client Migration Strategy

### 8.1 VS Code Extension Migration

**Coordinated Release Strategy**:
- VS Code Ext v1.x → REST API v1.x (version parity)
- VS Code Ext v2.x → REST API v2.x (released simultaneously)

**Backward Compatibility Window**:
- VS Code Ext v1.5 supports **both** API v1 and v2 (6-month transition period)
- Users can opt-in to v2 via settings

**Example Settings** (`settings.json`):
```json
{
  "sdlcOrchestrator.apiVersion": "v2",  // Options: "v1", "v2", "auto"
  "sdlcOrchestrator.autoUpgrade": true
}
```

### 8.2 CLI (`sdlcctl`) Migration

**Version Locking** (prevent surprise breakage):
```bash
# Lock to specific version
sdlcctl config set api-version v1

# Auto-detect latest
sdlcctl config set api-version auto

# Check current version
sdlcctl version
# Output: CLI v1.2.3 | API v1.2.3
```

**Upgrade Command**:
```bash
# Upgrade CLI + API version
sdlcctl upgrade --to v2

# Dry run (check breaking changes)
sdlcctl upgrade --to v2 --dry-run
```

### 8.3 Third-Party Integration Migration

**Webhook Version Header**:
```http
POST https://customer-webhook.com/sdlc-events
Content-Type: application/json
X-SDLC-Webhook-Version: 1.0

{
  "event": "gate.approved",
  "data": { ... }
}
```

**Gradual Migration**:
- Third-party tools can register for **both** v1 and v2 webhooks
- Receive duplicate events during transition period
- Deregister v1 webhook after full migration

---

## 9. Backward Compatibility

### 9.1 Compatibility Guarantees

**Within MAJOR version** (e.g., v1.x → v1.y):
- ✅ All existing endpoints continue to work
- ✅ All existing request/response schemas remain valid
- ✅ New features are additive only
- ✅ No behavior changes (except bug fixes)

**Across MAJOR versions** (e.g., v1.x → v2.y):
- ❌ Breaking changes allowed
- ✅ Migration guide provided
- ✅ 18-month support window for v1.x

### 9.2 Version Detection (Client-Side)

**REST API**:
```javascript
// Client detects version from response header
const response = await fetch('https://api.sdlc-orchestrator.com/v1/projects');
const apiVersion = response.headers.get('X-API-Version');  // "1.2.3"

if (semver.lt(apiVersion, '1.2.0')) {
  // Use old field
  console.log(project.status);
} else {
  // Use new field
  console.log(project.state);
}
```

**GraphQL API**:
```javascript
// Client introspects schema to detect deprecated fields
const introspection = await client.query({
  query: gql`
    query {
      __type(name: "Project") {
        fields {
          name
          isDeprecated
        }
      }
    }
  `
});

const statusField = introspection.data.__type.fields.find(f => f.name === 'status');
if (statusField.isDeprecated) {
  // Use new field
  console.log(project.state);
} else {
  // Use old field
  console.log(project.status);
}
```

### 9.3 Polyfill Strategy (Server-Side)

**Example: Backward-compatible response transformation**:
```javascript
// v2 Handler (returns new schema)
v2Router.get('/projects/:id', async (req, res) => {
  const project = await ProjectService.get(req.params.id);

  // New schema (v2)
  res.json({
    id: project.id,
    name: project.name,
    state: project.state  // Enum: PLANNING, IN_PROGRESS, etc.
  });
});

// v1 Handler (polyfills old schema)
v1Router.get('/projects/:id', async (req, res) => {
  const project = await ProjectService.get(req.params.id);

  // Old schema (v1) - polyfill from new data model
  res.json({
    id: project.id,
    name: project.name,
    status: mapStateToStatus(project.state)  // Convert enum → string
  });
});

function mapStateToStatus(state) {
  const mapping = {
    PLANNING: 'planning',
    IN_PROGRESS: 'active',
    COMPLETED: 'completed',
    ARCHIVED: 'archived'
  };
  return mapping[state] || 'unknown';
}
```

---

## 10. Version Discovery

### 10.1 API Version Metadata Endpoint

**Endpoint**: `GET /`

**Response**:
```json
{
  "name": "SDLC Orchestrator API",
  "tagline": "Project governance tool that enforces the SDLC Universal Framework",
  "version": "1.2.3",
  "api_versions": [
    {
      "version": "v1",
      "status": "stable",
      "base_url": "https://api.sdlc-orchestrator.com/v1",
      "documentation": "https://docs.sdlc-orchestrator.com/api/v1",
      "openapi_spec": "https://api.sdlc-orchestrator.com/v1/openapi.json"
    },
    {
      "version": "v2",
      "status": "beta",
      "base_url": "https://api.sdlc-orchestrator.com/v2",
      "documentation": "https://docs.sdlc-orchestrator.com/api/v2",
      "openapi_spec": "https://api.sdlc-orchestrator.com/v2/openapi.json"
    }
  ],
  "supported_features": {
    "rest_api": true,
    "graphql_api": true,
    "webhooks": true,
    "sse": false,
    "grpc": false
  },
  "rate_limits": {
    "free": 100,
    "pro": 1000,
    "enterprise": 10000
  }
}
```

### 10.2 OpenAPI Spec Discovery

**Per-Version OpenAPI Spec**:
```
GET https://api.sdlc-orchestrator.com/v1/openapi.json
GET https://api.sdlc-orchestrator.com/v2/openapi.json
```

**Response** (OpenAPI 3.0):
```json
{
  "openapi": "3.0.3",
  "info": {
    "title": "SDLC Orchestrator API v1",
    "version": "1.2.3",
    "description": "REST API for project governance and SDLC enforcement",
    "x-api-status": "stable",
    "x-eol-date": "2027-12-01"
  },
  "servers": [
    {
      "url": "https://api.sdlc-orchestrator.com/v1"
    }
  ],
  "paths": { ... }
}
```

### 10.3 GraphQL Schema Discovery

**SDL (Schema Definition Language) Endpoint**:
```
GET https://api.sdlc-orchestrator.com/graphql/schema.graphql
```

**Response**:
```graphql
"""
SDLC Orchestrator GraphQL API
Version: 1.2.3
Status: Stable
"""
schema {
  query: Query
  mutation: Mutation
  subscription: Subscription
}

type Query {
  projects(limit: Int = 20, cursor: String): ProjectConnection!
  gates(project_id: ID!): [Gate!]!
}

type Mutation {
  createProject(input: CreateProjectInput!): Project!
  approveGate(gate_id: ID!, comment: String): GateApproval!
}

type Subscription {
  gateStatusChanged(project_id: ID!): Gate!
}
```

---

## Implementation Checklist

### Stage 02 (HOW - Architecture & Design) - Week 3-4
- [ ] Design version routing middleware (Express/Fastify)
- [ ] Implement version detection logic (header parsing, URL parsing)
- [ ] Design GraphQL schema evolution strategy (deprecation, field versioning)
- [ ] Create OpenAPI specs for v1 and v2 (OpenAPI Generator)

### Stage 04 (BUILD - Development| - Week 5-8
- [ ] Implement REST API v1 with URL-based versioning
- [ ] Implement GraphQL API with `@deprecated` directive
- [ ] Build version metadata endpoint (`GET /`)
- [ ] Implement deprecation warning headers
- [ ] Create version migration scripts (database schema, data transformation)

### Stage 05 (TEST - Quality Assurance| - Week 9-10
- [ ] Unit tests: version routing (v1 vs v2 requests)
- [ ] Integration tests: backward compatibility (v1.0 → v1.5)
- [ ] E2E tests: client migration (VS Code Ext v1 → v2)
- [ ] Load tests: version-specific rate limits

### Stage 06 (DEPLOY - Production Go-Live| - Week 11
- [ ] Deploy v1.0.0 to production
- [ ] Configure CDN routing (Cloudflare/AWS CloudFront)
- [ ] Set up version monitoring (Datadog APM)

### Stage 07 (OPERATE - Production Excellence| - Week 12+
- [ ] Monitor version adoption metrics (v1 vs v2 usage)
- [ ] Track deprecated endpoint usage (sunset dashboard)
- [ ] Send deprecation notifications (email, in-app)
- [ ] Decommission EOL versions (automated process)

---

## Success Metrics

### KPI 1: Client Migration Speed
**Target**: 80% of clients migrate to new MAJOR version within 90 days.

**Measurement**:
```sql
-- % of API requests using v2 (after v2.0 release)
SELECT
  api_version,
  COUNT(*) as request_count,
  COUNT(*) * 100.0 / SUM(COUNT(*)) OVER () as percentage
FROM api_request_logs
WHERE created_at >= '2026-06-01'  -- v2.0 release date
GROUP BY api_version;
```

### KPI 2: Zero Breaking Changes in MINOR Releases
**Target**: 0 incidents of breaking changes in v1.x releases.

**Measurement**:
- Automated backward compatibility tests (contract testing)
- Customer support tickets tagged `breaking-change`

### KPI 3: Deprecation Compliance
**Target**: 100% deprecated endpoints removed on schedule (no delays).

**Measurement**:
```sql
-- Track deprecation timeline adherence
SELECT
  deprecated_feature,
  announced_at,
  planned_removal_at,
  actual_removal_at,
  DATEDIFF(day, planned_removal_at, actual_removal_at) as delay_days
FROM deprecation_log
WHERE actual_removal_at IS NOT NULL;
```

### KPI 4: API Version Discoverability
**Target**: 95% of clients use version discovery endpoint (`GET /`) before first API call.

**Measurement**:
```sql
-- % of new clients who call GET / before other endpoints
SELECT
  COUNT(DISTINCT user_id) as clients_using_discovery,
  COUNT(DISTINCT user_id) * 100.0 / (SELECT COUNT(*) FROM users) as percentage
FROM api_request_logs
WHERE endpoint = '/' AND created_at >= user.created_at;
```

---

## Risks & Mitigations

### Risk 1: Client Breakage During Major Version Upgrade
**Impact**: High - clients stop working after v2.0 release
**Probability**: Medium

**Mitigations**:
- 18-month support window for v1.x (generous grace period)
- Automated migration scripts (`sdlcctl upgrade --to v2`)
- Comprehensive migration guide with code examples
- Backward compatibility layer (polyfill v1 responses from v2 data model)

### Risk 2: Version Sprawl (Too Many Supported Versions)
**Impact**: High - engineering team overwhelmed by maintenance burden
**Probability**: Low

**Mitigations**:
- Maximum 2 MAJOR versions supported simultaneously (v1 + v2)
- Strict EOL enforcement (no exceptions for enterprise customers)
- Automated decommissioning process (410 Gone responses after EOL)

### Risk 3: GraphQL Schema Evolution Complexity
**Impact**: Medium - clients confused by field deprecation
**Probability**: Medium

**Mitigations**:
- Clear deprecation messages with removal date
- Introspection endpoint for automated detection
- VS Code Extension auto-updates queries (replace deprecated fields)

---

## References

- [Semantic Versioning 2.0.0](https://semver.org/)
- [REST API Versioning Best Practices](https://restfulapi.net/versioning/)
- [GraphQL Schema Deprecation](https://graphql.org/learn/best-practices/#versioning)
- [Stripe API Versioning](https://stripe.com/docs/api/versioning) - Industry benchmark
- [GitHub API Versioning](https://docs.github.com/en/rest/overview/api-versions) - Calendar versioning example
- [API Specification v1.0](./API-Specification.md) - REST + GraphQL endpoints
- [API Authentication v1.0](./API-Authentication.md) - JWT + OAuth 2.0 + RBAC

---

**Last Updated**: November 13, 2025
**Owner**: Backend Lead + CTO
**Status**: DRAFT (awaiting CTO review)
**Next Review**: Stage 02 (Architecture Design) - Week 3

---

## Document Summary

**Total Sections**: 10
**Total Lines**: 900+
**Quality Gates**: Supports G1 (Requirements Ready), G2 (Technical Feasibility)
**Next Document**: Legal-Review-Report.md (CRITICAL - Go/No-Go decision)
