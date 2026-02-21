# ADR-003: API Strategy (REST + GraphQL Hybrid)

**Status**: ✅ ACCEPTED
**Date**: November 13, 2025
**Deciders**: CTO, Backend Lead, Frontend Lead
**Stage**: Stage 02 (HOW - Design & Architecture)
**Framework**: SDLC 6.1.0

---

## Context

SDLC Orchestrator serves multiple client types:
- **React Dashboard** - Complex queries (dashboards, reports, analytics)
- **VS Code Extension** - Simple CRUD (gates, evidence, projects)
- **CLI (`sdlcctl`)** - Batch operations, scripting
- **CI/CD integrations** - Webhooks, automated checks
- **Third-party tools** - API integrations (Jira, Linear, Slack)

**Requirements**:
- Simple queries must be fast (<50ms p95)
- Complex queries must be flexible (avoid over-fetching)
- Real-time updates needed (gate status changes, approvals)
- API must be versioned (backward compatibility)
- Developer experience matters (auto-generated clients, docs)

**Alternatives Considered**:
1. **REST only** - Simple, widely understood
2. **GraphQL only** - Flexible, modern
3. **REST + GraphQL hybrid** - Best of both worlds
4. **gRPC** - High performance, but complex for web clients

---

## Decision

**We choose a REST + GraphQL hybrid approach:**
- **REST API** for simple CRUD operations (gates, evidence, projects)
- **GraphQL API** for complex queries (dashboards, reports, analytics)
- **Both APIs** share the same authentication, authorization, and business logic

---

## Rationale

### Why REST for Simple CRUD?

**1. Simplicity (Easier for CLI/CI/CD)**
```bash
# REST: Simple GET request (curl, Postman, CLI)
$ curl https://api.sdlc-orchestrator.com/api/v1/projects \
  -H "Authorization: Bearer <token>"

# Response: JSON array
[
  {"id": "proj_123", "name": "SDLC Orchestrator", "status": "active"},
  {"id": "proj_456", "name": "Mobile App", "status": "planning"}
]
```

**Benefits**:
- ✅ **No learning curve**: Every developer knows REST
- ✅ **Easy debugging**: Use curl, Postman, browser DevTools
- ✅ **Cacheable**: Standard HTTP caching (ETag, Cache-Control)

**2. HTTP Semantics (Clear Intent)**
```http
GET    /api/v1/projects          # List projects
POST   /api/v1/projects          # Create project
GET    /api/v1/projects/:id      # Get project
PATCH  /api/v1/projects/:id      # Update project
DELETE /api/v1/projects/:id      # Delete project

GET    /api/v1/gates/:id         # Get gate
POST   /api/v1/gates/:id/approve # Approve gate
```

**Benefits**:
- ✅ **Self-documenting**: HTTP verbs indicate operation (GET = read, POST = create)
- ✅ **RESTful conventions**: Predictable URL patterns
- ✅ **OpenAPI spec**: Auto-generated docs (Swagger, Redoc)

**3. Example: Gate Approval (REST)**
```python
# FastAPI endpoint (REST)
@app.post("/api/v1/gates/{gate_id}/approve")
async def approve_gate(
    gate_id: str,
    comment: str = Body(...),
    user: User = Depends(get_current_user)
):
    """
    Approve a gate.

    - **gate_id**: Gate ID (G0.1, G0.2, G1, ..., G9)
    - **comment**: Approval comment (optional)
    """
    # Check if user has permission
    if not user.can_approve_gate(gate_id):
        raise HTTPException(403, "Forbidden: You cannot approve this gate")

    # Create approval record
    approval = await gate_service.create_approval(
        gate_id=gate_id,
        user_id=user.id,
        comment=comment
    )

    # Check if gate passed (2+ approvals)
    gate_status = await gate_service.check_gate_status(gate_id)

    return {
        "approval": approval,
        "gate_status": gate_status
    }
```

**Response**:
```json
{
  "approval": {
    "id": "appr_789",
    "gate_id": "G1",
    "user_id": "user_123",
    "comment": "AGPL containment strategy looks good",
    "created_at": "2025-11-13T10:30:00Z"
  },
  "gate_status": {
    "gate_id": "G1",
    "status": "PASS",
    "approvals_count": 2,
    "required_approvals": 2
  }
}
```

---

### Why GraphQL for Complex Queries?

**1. Avoid Over-Fetching (Dashboard Performance)**

**Problem with REST**:
```bash
# Dashboard needs: Project + Gates + Evidence + Team
# REST requires 4 requests:
GET /api/v1/projects/proj_123
GET /api/v1/projects/proj_123/gates
GET /api/v1/projects/proj_123/evidence
GET /api/v1/projects/proj_123/team
# Total: 4 requests, 200ms latency (4 × 50ms)
```

**Solution with GraphQL**:
```graphql
# Single request (all data in one query)
query ProjectDashboard($projectId: ID!) {
  project(id: $projectId) {
    id
    name
    status

    # Nested: Gates with approvals
    gates {
      id
      name
      status
      approvals {
        user {
          name
          avatar
        }
        comment
        createdAt
      }
    }

    # Nested: Evidence
    evidence {
      id
      title
      type
      uploadedBy {
        name
      }
      uploadedAt
    }

    # Nested: Team
    team {
      members {
        name
        role
        avatar
      }
    }
  }
}
```

**Response**:
```json
{
  "data": {
    "project": {
      "id": "proj_123",
      "name": "SDLC Orchestrator",
      "status": "active",
      "gates": [
        {
          "id": "G1",
          "name": "Legal + Market Validation",
          "status": "PASS",
          "approvals": [
            {
              "user": {"name": "John Doe", "avatar": "https://..."},
              "comment": "Approved",
              "createdAt": "2025-11-13T10:30:00Z"
            }
          ]
        }
      ],
      "evidence": [...],
      "team": {...}
    }
  }
}
```

**Benefits**:
- ✅ **1 request instead of 4**: 50ms latency (vs 200ms REST)
- ✅ **No over-fetching**: Client requests exactly what it needs
- ✅ **No under-fetching**: No need for additional requests

**2. Flexible Queries (Client-Controlled)**
```graphql
# Frontend 1: Minimal data (list view)
query ProjectsList {
  projects {
    id
    name
    status
  }
}

# Frontend 2: Detailed data (detail view)
query ProjectDetail($id: ID!) {
  project(id: $id) {
    id
    name
    status
    description
    gates { ... }
    evidence { ... }
    team { ... }
  }
}
```

**Benefits**:
- ✅ **Client decides**: No need for `/projects/simple` vs `/projects/detailed` endpoints
- ✅ **Fewer API changes**: Add fields without breaking existing queries

**3. Real-Time Updates (Subscriptions)**
```graphql
# GraphQL Subscription (WebSocket)
subscription GateStatusChanged($projectId: ID!) {
  gateStatusChanged(projectId: $projectId) {
    gateId
    status
    approvals {
      user {
        name
      }
      createdAt
    }
  }
}
```

**Use Case**:
- Dashboard shows gate status in real-time
- When someone approves gate → All viewers see update instantly
- No polling (REST requires polling every 5-10 seconds)

**Benefits**:
- ✅ **Real-time**: WebSocket push (not polling)
- ✅ **Efficient**: Server pushes only changed data
- ✅ **Better UX**: Instant updates (no refresh button)

---

### Why Hybrid (REST + GraphQL)?

**Decision Matrix**:

| Use Case | Best API | Rationale |
|----------|----------|-----------|
| **List projects** | REST | Simple, cacheable, no nested data |
| **Get project detail** | GraphQL | Complex, nested data (gates, evidence, team) |
| **Create project** | REST | Simple POST, no nested query |
| **Approve gate** | REST | Simple action, no nested query |
| **Dashboard (DORA metrics)** | GraphQL | Complex aggregation, multiple resources |
| **Real-time gate updates** | GraphQL Subscription | WebSocket push |
| **CLI batch operations** | REST | Simple scripting, no GraphQL client needed |

**Example: CLI uses REST, Dashboard uses GraphQL**
```bash
# CLI: REST (simple, scriptable)
$ sdlcctl gates approve G1 --comment "Approved"
# Internally: POST /api/v1/gates/G1/approve

# Dashboard: GraphQL (complex, nested)
const { data } = useQuery(gql`
  query ProjectDashboard($projectId: ID!) {
    project(id: $projectId) {
      gates { ... }
      evidence { ... }
    }
  }
`)
```

---

### Why NOT REST-only?

**Problems with REST-only**:
1. ❌ **Over-fetching**: GET /projects returns all fields (slow for mobile)
2. ❌ **Under-fetching**: Need 4 requests for dashboard (200ms latency)
3. ❌ **No real-time**: Requires polling (inefficient, delayed updates)
4. ❌ **Version sprawl**: `/v1/projects`, `/v1/projects/simple`, `/v1/projects/detailed`

**Example Problem (Over-fetching)**:
```json
// Mobile app only needs: id, name, status
// But REST returns everything (100KB response):
{
  "id": "proj_123",
  "name": "SDLC Orchestrator",
  "status": "active",
  "description": "Very long description...",  // Not needed
  "gates": [...],  // Not needed
  "evidence": [...],  // Not needed
  "team": {...}  // Not needed
}
```

---

### Why NOT GraphQL-only?

**Problems with GraphQL-only**:
1. ❌ **Steep learning curve**: CLI/CI/CD users struggle with GraphQL syntax
2. ❌ **Caching complexity**: GraphQL queries not cacheable by HTTP layer
3. ❌ **File uploads**: GraphQL file upload is awkward (multipart/form-data)
4. ❌ **Debugging**: Harder than REST (all requests POST to /graphql)

**Example Problem (CLI complexity)**:
```bash
# REST: Simple curl (everyone knows this)
$ curl -X POST https://api.sdlc-orchestrator.com/api/v1/gates/G1/approve

# GraphQL: Complex syntax (many users don't know GraphQL)
$ curl -X POST https://api.sdlc-orchestrator.com/graphql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "mutation ApproveGate($gateId: ID!) { approveGate(gateId: $gateId) { status } }",
    "variables": {"gateId": "G1"}
  }'
```

---

### Why NOT gRPC?

**Problems with gRPC**:
1. ❌ **No browser support**: Requires gRPC-Web proxy (extra complexity)
2. ❌ **Binary protocol**: Hard to debug (not human-readable)
3. ❌ **Tooling**: No curl, Postman support (requires grpcurl)
4. ❌ **Learning curve**: Protobuf syntax, code generation

**When gRPC makes sense**:
- ✅ Microservices internal communication (high throughput, low latency)
- ✅ Mobile apps (efficient binary protocol)
- ❌ **NOT for SDLC Orchestrator**: We need browser support + human-readable API

---

## Implementation Design

### 1. Shared Business Logic

**Architecture**:
```
┌─────────────────────────────────────────────────────┐
│ REST API            GraphQL API                     │
│ (FastAPI)           (Strawberry GraphQL)            │
└────────┬──────────────────────┬─────────────────────┘
         │                      │
         ↓                      ↓
┌─────────────────────────────────────────────────────┐
│ Business Logic Layer (Shared Services)              │
│ - GateService, EvidenceService, ProjectService      │
└─────────────────────────────────────────────────────┘
```

**Example Service**:
```python
# app/services/gate_service.py (shared by REST + GraphQL)
class GateService:
    async def approve_gate(self, gate_id: str, user_id: str, comment: str):
        """Approve gate (used by both REST and GraphQL)."""
        # Business logic (authorization, validation, DB operations)
        if not await self.can_approve(user_id, gate_id):
            raise PermissionError("User cannot approve this gate")

        approval = await db.gate_approvals.create({
            "gate_id": gate_id,
            "user_id": user_id,
            "comment": comment,
            "created_at": datetime.utcnow()
        })

        # Check if gate passed
        gate_status = await self.check_gate_status(gate_id)

        return approval, gate_status
```

**REST endpoint**:
```python
@app.post("/api/v1/gates/{gate_id}/approve")
async def approve_gate_rest(gate_id: str, comment: str, user: User):
    approval, gate_status = await gate_service.approve_gate(gate_id, user.id, comment)
    return {"approval": approval, "gate_status": gate_status}
```

**GraphQL mutation**:
```python
@strawberry.type
class Mutation:
    @strawberry.mutation
    async def approve_gate(self, gate_id: str, comment: str, info: Info) -> GateApproval:
        user = info.context["user"]
        approval, gate_status = await gate_service.approve_gate(gate_id, user.id, comment)
        return approval
```

**Benefits**:
- ✅ **No code duplication**: Business logic written once
- ✅ **Consistent behavior**: REST and GraphQL return same data
- ✅ **Easier testing**: Test service, not endpoints

---

### 2. API Versioning Strategy

**REST Versioning** (URL-based):
```
/api/v1/projects  → Version 1 (current)
/api/v2/projects  → Version 2 (future breaking changes)
```

**GraphQL Versioning** (schema evolution):
```graphql
# v1.0 schema
type Project {
  id: ID!
  status: String!  # Old field
}

# v1.1 schema (backward-compatible)
type Project {
  id: ID!
  status: String! @deprecated(reason: "Use state instead. Removal in v2.0")
  state: ProjectState!  # New field (enum)
}
```

**Benefits**:
- ✅ **REST**: Clear versioning (URL indicates breaking changes)
- ✅ **GraphQL**: Gradual deprecation (clients migrate at own pace)

---

### 3. Rate Limiting (Per Client Type)

```yaml
Rate Limits:
  Free Tier:
    REST: 100 requests/hour
    GraphQL: 100 queries/hour (complexity limit: 1000)

  Pro Tier:
    REST: 1,000 requests/hour
    GraphQL: 1,000 queries/hour (complexity limit: 5000)

  Enterprise:
    REST: 10,000 requests/hour
    GraphQL: 10,000 queries/hour (complexity limit: 10000)
```

**GraphQL Query Complexity**:
```graphql
# Simple query (complexity: 10)
query { projects { id name } }

# Complex query (complexity: 100)
query {
  projects {
    gates {
      approvals {
        user {
          team {
            members { ... }
          }
        }
      }
    }
  }
}
```

**Why complexity matters**:
- Prevents malicious queries (deep nesting, large lists)
- Example: `projects { gates { evidence { ... } } }` could fetch 1M records

---

## Consequences

### Positive

**1. Developer Experience**
- ✅ **CLI/CI/CD**: Use REST (simple curl commands)
- ✅ **Dashboard**: Use GraphQL (flexible queries, real-time updates)
- ✅ **Mobile**: Use GraphQL (minimal data transfer)

**2. Performance**
- ✅ **REST**: Simple queries fast (<50ms p95)
- ✅ **GraphQL**: Complex queries efficient (1 request vs 4)
- ✅ **Subscriptions**: Real-time updates (no polling)

**3. Flexibility**
- ✅ **REST**: Add new endpoints without breaking existing clients
- ✅ **GraphQL**: Add new fields without versioning

### Negative

**1. Operational Complexity**
- ❌ **Two APIs**: More code, more testing, more documentation
- **Mitigation**: Shared business logic layer (no duplication)

**2. Learning Curve**
- ❌ **Team needs to learn GraphQL**: Not all developers know it
- **Mitigation**: Training, documentation, code examples

**3. Caching Complexity**
- ❌ **GraphQL queries not cacheable by HTTP layer**: Requires custom caching (Redis, Apollo Client cache)
- **Mitigation**: REST for cacheable endpoints (GET /projects)

---

## References

- [API Specification v1.0](../../../01-Planning-Analysis/04-API-Design/API-Specification.md) - Complete REST + GraphQL spec
- [API Versioning Strategy v1.0](../../../01-Planning-Analysis/04-API-Design/API-Versioning-Strategy.md)
- [GraphQL Best Practices](https://graphql.org/learn/best-practices/)
- [REST API Design Best Practices](https://restfulapi.net/)

---

## Approval

| Role | Name | Approval | Date |
|------|------|----------|------|
| **CTO** | [CTO Name] | ✅ APPROVED | Nov 13, 2025 |
| **Backend Lead** | [Backend Lead Name] | ✅ APPROVED | Nov 13, 2025 |
| **Frontend Lead** | [Frontend Lead Name] | ✅ APPROVED | Nov 13, 2025 |

---

**Last Updated**: November 13, 2025
**Status**: ✅ ACCEPTED - Binding decision
**Next Review**: Phase 1 (Implementation, Week 5-8)
