---
spec_id: SPRINT-120-API
title: Sprint 120 API Contracts - Context Authority V2
version: "1.0.0"
status: DRAFT
tier:
  - STANDARD
  - PROFESSIONAL
  - ENTERPRISE
pillar: 7
owner: Backend Team
last_updated: 2026-01-29
related_specs:
  - SPEC-0011
  - SPEC-0001
---

# Sprint 120 API Contracts: Context Authority V2

## 1. Overview

This document defines the API contracts for Context Authority V2 (SPEC-0011) to be implemented in Sprint 120.

### 1.1 Endpoints Summary

| # | Method | Endpoint | Purpose | SLA |
|---|--------|----------|---------|-----|
| 1 | POST | `/api/v1/context/v2/validate` | Gate-aware context validation | <100ms |
| 2 | GET | `/api/v1/context/v2/overlay/{project_id}` | Get dynamic overlay | <50ms |
| 3 | GET | `/api/v1/context/v2/snapshot/{snapshot_id}` | Get context snapshot | <50ms |
| 4 | GET | `/api/v1/context/v2/snapshots/{project_id}` | List project snapshots | <100ms |
| 5 | GET | `/api/v1/context/v2/templates` | List overlay templates | <20ms |
| 6 | POST | `/api/v1/context/v2/templates` | Create overlay template | <50ms |
| 7 | PUT | `/api/v1/context/v2/templates/{template_id}` | Update overlay template | <50ms |

---

## 2. Endpoint Specifications

### 2.1 POST `/api/v1/context/v2/validate`

**Purpose:** Gate-aware context validation combining V1 checks with gate status and vibecoding index.

**Authentication:** Required (Bearer Token)
**Authorization:** `governance:write` scope

#### Request

```json
{
  "project_id": "uuid",
  "submission_id": "uuid",
  "changed_files": ["backend/app/services/new_feature.py", "backend/app/models/user.py"],
  "affected_modules": ["services", "models"],
  "task_id": "TASK-123",
  "is_new_feature": true,
  "repo_path": "/path/to/repo"
}
```

**Request Schema:**

```python
class ContextValidationV2Request(BaseModel):
    project_id: UUID
    submission_id: UUID
    changed_files: List[str] = Field(..., min_items=1, max_items=1000)
    affected_modules: List[str] = Field(default_factory=list)
    task_id: Optional[str] = Field(None, max_length=50)
    is_new_feature: bool = False
    repo_path: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "project_id": "550e8400-e29b-41d4-a716-446655440000",
                "submission_id": "660e8400-e29b-41d4-a716-446655440001",
                "changed_files": ["backend/app/services/auth.py"],
                "affected_modules": ["services.auth"],
                "task_id": "TASK-456",
                "is_new_feature": True
            }
        }
```

#### Response (200 OK)

```json
{
  "valid": false,
  "snapshot_id": "uuid",
  "tier": "PROFESSIONAL",
  "gate_status": {
    "current_stage": "02",
    "last_passed_gate": "G0.2",
    "pending_gates": ["G1", "G2"]
  },
  "vibecoding_index": 65,
  "vibecoding_zone": "ORANGE",
  "v1_result": {
    "valid": true,
    "adr_count": 15,
    "linked_adrs": ["ADR-041", "ADR-042"],
    "spec_found": true,
    "agents_md_fresh": true,
    "module_consistency": true
  },
  "gate_violations": [
    {
      "type": "stage_blocked",
      "severity": "error",
      "message": "File 'backend/app/services/new_feature.py' blocked in Stage 02",
      "file_path": "backend/app/services/new_feature.py",
      "fix": "Complete Stage 02 gates before modifying this file",
      "cli_command": "sdlcctl gate status"
    }
  ],
  "index_warnings": [
    {
      "type": "high_vibecoding_index",
      "severity": "warning",
      "message": "Vibecoding Index 65 in Orange zone (61-80)",
      "fix": "Tech Lead review recommended."
    }
  ],
  "dynamic_overlay": "## 🎯 Current Status...",
  "validated_at": "2026-01-29T18:30:00Z"
}
```

**Response Schema:**

```python
class ContextViolationResponse(BaseModel):
    type: str
    severity: Literal["error", "warning", "info"]
    message: str
    file_path: Optional[str] = None
    module: Optional[str] = None
    fix: Optional[str] = None
    cli_command: Optional[str] = None
    related_adr: Optional[str] = None


class GateStatusResponse(BaseModel):
    current_stage: str
    last_passed_gate: Optional[str] = None
    pending_gates: List[str] = Field(default_factory=list)


class V1ResultResponse(BaseModel):
    valid: bool
    violations: List[ContextViolationResponse] = Field(default_factory=list)
    warnings: List[ContextViolationResponse] = Field(default_factory=list)
    adr_count: int = 0
    linked_adrs: List[str] = Field(default_factory=list)
    spec_found: bool = False
    agents_md_fresh: bool = True
    module_consistency: bool = True


class ContextValidationV2Response(BaseModel):
    valid: bool
    snapshot_id: UUID
    tier: str
    gate_status: GateStatusResponse
    vibecoding_index: int = Field(..., ge=0, le=100)
    vibecoding_zone: Literal["GREEN", "YELLOW", "ORANGE", "RED"]
    v1_result: V1ResultResponse
    gate_violations: List[ContextViolationResponse] = Field(default_factory=list)
    index_warnings: List[ContextViolationResponse] = Field(default_factory=list)
    dynamic_overlay: str
    validated_at: datetime
```

#### Error Responses

| Status | Code | Description |
|--------|------|-------------|
| 400 | `INVALID_REQUEST` | Missing or invalid fields |
| 401 | `UNAUTHORIZED` | Invalid or missing token |
| 403 | `FORBIDDEN` | Insufficient permissions |
| 404 | `PROJECT_NOT_FOUND` | Project does not exist |
| 500 | `INTERNAL_ERROR` | Server error |

---

### 2.2 GET `/api/v1/context/v2/overlay/{project_id}`

**Purpose:** Get current dynamic overlay for a project based on gate status and vibecoding index.

**Authentication:** Required (Bearer Token)
**Authorization:** `governance:read` scope

#### Response (200 OK)

```json
{
  "project_id": "uuid",
  "overlay": "## 🎯 Current Status: Design Approved\n\nGate G0.2 (Solution Diversity) PASSED on 2026-01-29...",
  "gate_status": {
    "current_stage": "04",
    "last_passed_gate": "G2",
    "pending_gates": ["G3"]
  },
  "vibecoding_index": 25,
  "vibecoding_zone": "YELLOW",
  "applied_templates": [
    {
      "id": "uuid",
      "name": "Gate G2 Pass - Build Active",
      "trigger_type": "gate_pass",
      "trigger_value": "G2"
    }
  ],
  "generated_at": "2026-01-29T18:30:00Z"
}
```

**Response Schema:**

```python
class AppliedTemplateInfo(BaseModel):
    id: UUID
    name: str
    trigger_type: str
    trigger_value: str


class DynamicOverlayResponse(BaseModel):
    project_id: UUID
    overlay: str
    gate_status: GateStatusResponse
    vibecoding_index: int
    vibecoding_zone: Literal["GREEN", "YELLOW", "ORANGE", "RED"]
    applied_templates: List[AppliedTemplateInfo] = Field(default_factory=list)
    generated_at: datetime
```

---

### 2.3 GET `/api/v1/context/v2/snapshot/{snapshot_id}`

**Purpose:** Get a specific context snapshot for audit purposes.

**Authentication:** Required (Bearer Token)
**Authorization:** `governance:read` scope

#### Response (200 OK)

```json
{
  "id": "uuid",
  "submission_id": "uuid",
  "project_id": "uuid",
  "gate_status": {
    "current_stage": "02",
    "last_passed_gate": "G0.2",
    "pending_gates": ["G1", "G2"]
  },
  "vibecoding_index": 65,
  "vibecoding_zone": "ORANGE",
  "dynamic_overlay": "## ⚠️ Vibecoding Index: ORANGE (65)...",
  "v1_result": { ... },
  "gate_violations": [ ... ],
  "index_warnings": [ ... ],
  "tier": "PROFESSIONAL",
  "is_valid": false,
  "applied_template_ids": ["uuid1", "uuid2"],
  "snapshot_at": "2026-01-29T18:30:00Z"
}
```

**Response Schema:**

```python
class ContextSnapshotResponse(BaseModel):
    id: UUID
    submission_id: UUID
    project_id: UUID
    gate_status: dict
    vibecoding_index: int
    vibecoding_zone: str
    dynamic_overlay: str
    v1_result: Optional[dict] = None
    gate_violations: Optional[List[dict]] = None
    index_warnings: Optional[List[dict]] = None
    tier: str
    is_valid: bool
    applied_template_ids: Optional[List[UUID]] = None
    snapshot_at: datetime
```

---

### 2.4 GET `/api/v1/context/v2/snapshots/{project_id}`

**Purpose:** List context snapshots for a project with pagination.

**Authentication:** Required (Bearer Token)
**Authorization:** `governance:read` scope

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | int | 50 | Max 100 |
| `offset` | int | 0 | Pagination offset |
| `is_valid` | bool | null | Filter by validity |
| `zone` | string | null | Filter by vibecoding zone |
| `start_date` | datetime | null | Filter by date range |
| `end_date` | datetime | null | Filter by date range |

#### Response (200 OK)

```json
{
  "items": [
    {
      "id": "uuid",
      "submission_id": "uuid",
      "vibecoding_index": 65,
      "vibecoding_zone": "ORANGE",
      "is_valid": false,
      "snapshot_at": "2026-01-29T18:30:00Z"
    }
  ],
  "total": 150,
  "limit": 50,
  "offset": 0
}
```

**Response Schema:**

```python
class ContextSnapshotSummary(BaseModel):
    id: UUID
    submission_id: UUID
    vibecoding_index: int
    vibecoding_zone: str
    is_valid: bool
    snapshot_at: datetime


class ContextSnapshotListResponse(BaseModel):
    items: List[ContextSnapshotSummary]
    total: int
    limit: int
    offset: int
```

---

### 2.5 GET `/api/v1/context/v2/templates`

**Purpose:** List overlay templates with filtering.

**Authentication:** Required (Bearer Token)
**Authorization:** `admin:read` scope

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `trigger_type` | string | null | Filter by trigger type |
| `tier` | string | null | Filter by tier |
| `is_active` | bool | true | Filter by active status |
| `limit` | int | 50 | Max 100 |
| `offset` | int | 0 | Pagination offset |

#### Response (200 OK)

```json
{
  "items": [
    {
      "id": "uuid",
      "name": "Gate G0.2 Pass - Design Approved",
      "trigger_type": "gate_pass",
      "trigger_value": "G0.2",
      "tier": null,
      "priority": 100,
      "is_active": true,
      "overlay_content": "## 🎯 Current Status: Design Approved...",
      "description": "Shown when Gate G0.2 passes",
      "created_at": "2026-01-29T12:00:00Z",
      "updated_at": "2026-01-29T12:00:00Z"
    }
  ],
  "total": 5,
  "limit": 50,
  "offset": 0
}
```

---

### 2.6 POST `/api/v1/context/v2/templates`

**Purpose:** Create a new overlay template.

**Authentication:** Required (Bearer Token)
**Authorization:** `admin:write` scope

#### Request

```json
{
  "name": "Custom Gate G3 Warning",
  "trigger_type": "gate_pass",
  "trigger_value": "G3",
  "tier": "ENTERPRISE",
  "priority": 80,
  "overlay_content": "## ✅ Ship Ready\n\nGate G3 passed on {date}...",
  "description": "Custom template for Enterprise tier G3 pass"
}
```

**Request Schema:**

```python
class CreateContextOverlayTemplateRequest(BaseModel):
    name: str = Field(..., max_length=200)
    trigger_type: Literal["gate_pass", "gate_fail", "index_zone", "stage_constraint"]
    trigger_value: str = Field(..., max_length=100)
    tier: Optional[Literal["LITE", "STANDARD", "PROFESSIONAL", "ENTERPRISE"]] = None
    priority: int = Field(default=0, ge=0, le=100)
    overlay_content: str = Field(..., min_length=10)
    description: Optional[str] = None
    is_active: bool = True

    @field_validator('trigger_value')
    @classmethod
    def validate_trigger_value(cls, v, info):
        trigger_type = info.data.get('trigger_type')
        valid_values = {
            'gate_pass': ['G0.1', 'G0.2', 'G1', 'G2', 'G3', 'G4'],
            'gate_fail': ['G0.1', 'G0.2', 'G1', 'G2', 'G3', 'G4'],
            'index_zone': ['green', 'yellow', 'orange', 'red'],
            'stage_constraint': ['stage_00_only', 'stage_01_only', 'stage_02_code_block', 'stage_05_freeze'],
        }
        if trigger_type and v.lower() not in [x.lower() for x in valid_values.get(trigger_type, [])]:
            raise ValueError(f"Invalid trigger_value '{v}' for trigger_type '{trigger_type}'")
        return v
```

#### Response (201 Created)

```json
{
  "id": "uuid",
  "name": "Custom Gate G3 Warning",
  "trigger_type": "gate_pass",
  "trigger_value": "G3",
  "tier": "ENTERPRISE",
  "priority": 80,
  "is_active": true,
  "overlay_content": "## ✅ Ship Ready...",
  "description": "Custom template for Enterprise tier G3 pass",
  "created_by_id": "uuid",
  "created_at": "2026-01-29T18:30:00Z",
  "updated_at": "2026-01-29T18:30:00Z"
}
```

---

### 2.7 PUT `/api/v1/context/v2/templates/{template_id}`

**Purpose:** Update an existing overlay template.

**Authentication:** Required (Bearer Token)
**Authorization:** `admin:write` scope

#### Request

```json
{
  "name": "Updated Gate G3 Warning",
  "priority": 90,
  "overlay_content": "## ✅ Ship Ready (Updated)\n\n...",
  "is_active": true
}
```

**Request Schema:**

```python
class UpdateContextOverlayTemplateRequest(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    trigger_type: Optional[Literal["gate_pass", "gate_fail", "index_zone", "stage_constraint"]] = None
    trigger_value: Optional[str] = Field(None, max_length=100)
    tier: Optional[Literal["LITE", "STANDARD", "PROFESSIONAL", "ENTERPRISE"]] = None
    priority: Optional[int] = Field(None, ge=0, le=100)
    overlay_content: Optional[str] = Field(None, min_length=10)
    description: Optional[str] = None
    is_active: Optional[bool] = None
```

#### Response (200 OK)

Returns updated template object.

---

## 3. Integration Points

### 3.1 Context Authority V2 → Vibecoding Service

```python
# CA V2 calls VibecodingService to get current index
vibecoding_service = get_vibecoding_service()
index_result = await vibecoding_service.get_recent_index(project_id)

# Returns:
{
    "index": 65,
    "zone": "ORANGE",
    "signal_breakdown": {
        "intent_clarity": 70,
        "code_ownership": 60,
        "context_completeness": 55,
        "ai_attestation": 100,
        "rejection_rate": 10
    },
    "calculated_at": "2026-01-29T18:00:00Z"
}
```

### 3.2 Context Authority V2 → Gate Service

```python
# CA V2 calls GateService to get current gate status
gate_service = get_gate_service()
gate_status = await gate_service.get_project_gate_status(project_id)

# Returns:
{
    "current_stage": "02",
    "last_passed_gate": "G0.2",
    "pending_gates": ["G1", "G2"],
    "blocked_paths": ["backend/app/**", "frontend/src/**"],
    "allowed_paths": ["docs/02-design/**", "openapi/**"]
}
```

### 3.3 Gates Engine → Context Authority V2

```python
# Gates Engine calls CA V2 for context validation before gate evaluation
context_service = get_context_authority_v2()
context_result = await context_service.validate_context_v2(submission)

# If context invalid, gate evaluation may be blocked
if not context_result.valid:
    raise GateEvaluationBlocked(
        "Context validation failed",
        violations=context_result.gate_violations
    )
```

---

## 4. Error Handling

### 4.1 Standard Error Response

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": [
      {
        "field": "changed_files",
        "message": "At least one file must be specified"
      }
    ]
  },
  "request_id": "uuid",
  "timestamp": "2026-01-29T18:30:00Z"
}
```

### 4.2 Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Request validation failed |
| `UNAUTHORIZED` | 401 | Invalid or missing authentication |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `CONFLICT` | 409 | Resource conflict (e.g., duplicate template) |
| `RATE_LIMITED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Internal server error |
| `SERVICE_UNAVAILABLE` | 503 | Dependent service unavailable |

---

## 5. Performance Requirements

| Endpoint | p50 | p95 | p99 | Max |
|----------|-----|-----|-----|-----|
| `POST /validate` | 30ms | 100ms | 200ms | 500ms |
| `GET /overlay/{id}` | 10ms | 50ms | 100ms | 200ms |
| `GET /snapshot/{id}` | 10ms | 50ms | 100ms | 200ms |
| `GET /snapshots/{id}` | 20ms | 100ms | 200ms | 500ms |
| `GET /templates` | 5ms | 20ms | 50ms | 100ms |
| `POST /templates` | 10ms | 50ms | 100ms | 200ms |
| `PUT /templates/{id}` | 10ms | 50ms | 100ms | 200ms |

### 5.1 Caching Strategy

| Endpoint | Cache | TTL | Invalidation |
|----------|-------|-----|--------------|
| `GET /overlay/{id}` | Redis | 30s | On gate change, index change |
| `GET /templates` | Redis | 5min | On template create/update |
| `GET /snapshot/{id}` | None | - | Immutable |

---

## 6. Security Considerations

### 6.1 Authentication

All endpoints require Bearer Token authentication:

```
Authorization: Bearer <jwt_token>
```

### 6.2 Authorization Scopes

| Scope | Endpoints |
|-------|-----------|
| `governance:read` | GET snapshots, overlay |
| `governance:write` | POST validate |
| `admin:read` | GET templates |
| `admin:write` | POST/PUT templates |

### 6.3 Rate Limiting

| Scope | Limit | Window |
|-------|-------|--------|
| `governance:read` | 1000 | 1 minute |
| `governance:write` | 100 | 1 minute |
| `admin:write` | 50 | 1 minute |

---

## 7. Document Control

| Field | Value |
|-------|-------|
| **Version** | 1.0.0 |
| **Created** | January 29, 2026 |
| **Author** | Backend Team |
| **Status** | DRAFT |
| **Sprint** | 120 (Pre-work) |
| **Endpoints** | 7 |

---

## Changelog

### v1.0.0 (January 29, 2026)
- Initial API contracts for Context Authority V2
- 7 endpoints defined
- Request/response schemas
- Integration points documented
- Performance requirements specified
