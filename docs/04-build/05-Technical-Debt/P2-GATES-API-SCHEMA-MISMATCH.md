# P2: Gates API Pydantic Schema Mismatch

**Discovered**: 2025-12-07 (Sprint 33 Day 4 - Smoke Testing)
**Severity**: P2 (Non-blocking, API unusable)
**Component**: Backend API - Gates Router
**Affects**: `GET /api/v1/gates` endpoint

---

## Issue Description

The `/api/v1/gates` endpoint returns 500 Internal Server Error due to Pydantic validation failure when serializing gate records from the database.

### Error Message

```
pydantic_core._pydantic_core.ValidationError: 3 validation errors for GateResponse
exit_criteria.0
  Input should be a valid dictionary [type=dict_type, input_value='Problem statement: Vietn...MEs lack affordable HRM', input_type=str]
exit_criteria.1
  Input should be a valid dictionary [type=dict_type, input_value='User personas: HR Manage...Employee, Payroll Admin', input_type=str]
exit_criteria.2
  Input should be a valid dictionary [type=dict_type, input_value='Market: $500M VN HRM market, 30% CAGR', input_type=str]
```

### HTTP Request

```bash
TOKEN="<valid_jwt_token>"
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8300/api/v1/gates?page=1&page_size=5"

# Response: 500 Internal Server Error
```

---

## Root Cause

**Schema Mismatch** between seed data and Pydantic response model.

### Seed Data Format (backend/alembic/versions/a502ce0d23a7_seed_data_realistic_mtc_nqh_examples.py)

```python
# Gate exit_criteria stored as JSON array of strings
"exit_criteria": json.dumps([
    "Problem statement: Vietnamese SMEs lack affordable HRM",
    "User personas: HR Manager, Department Head, Employee, Payroll Admin",
    "Market: $500M VN HRM market, 30% CAGR"
])
```

### Pydantic Schema (backend/app/schemas/gate.py)

```python
class GateResponse(BaseModel):
    # ...
    exit_criteria: List[Dict[str, Any]]  # Expects array of dicts, not strings!
```

**Mismatch**: Seed data provides `List[str]`, schema expects `List[Dict[str, Any]]`.

---

## Impact

- **Severity**: P2 (Non-blocking)
- **Workaround**: Use direct database queries or create gates via POST endpoint
- **Affected Endpoints**:
  - `GET /api/v1/gates` (list all gates) ❌
  - `GET /api/v1/gates/{gate_id}` (get single gate) ❌ (assumed)
- **Not Affected**:
  - `POST /api/v1/gates` (create gate) ✅
  - Auth endpoints ✅
  - Health/metrics ✅

---

## Fix Options

### Option A: Update Pydantic Schema (Quick Fix - 15 min)

**Pros**: Fastest fix, backward compatible
**Cons**: Allows inconsistent data format

```python
# backend/app/schemas/gate.py
from typing import List, Dict, Any, Union

class GateResponse(BaseModel):
    # ...
    exit_criteria: List[Union[str, Dict[str, Any]]]  # Accept both formats
```

### Option B: Update Seed Data (Correct Fix - 30 min)

**Pros**: Fixes root cause, enforces schema consistency
**Cons**: Requires migration update and re-run

```python
# backend/alembic/versions/a502ce0d23a7_seed_data_realistic_mtc_nqh_examples.py
"exit_criteria": json.dumps([
    {"criterion": "Problem statement", "description": "Vietnamese SMEs lack affordable HRM"},
    {"criterion": "User personas", "description": "HR Manager, Department Head, Employee, Payroll Admin"},
    {"criterion": "Market", "description": "$500M VN HRM market, 30% CAGR"}
])
```

### Option C: Add Data Migration (Robust - 1 hour)

**Pros**: Fixes existing data, supports both old/new formats
**Cons**: Most complex, requires careful testing

```sql
-- New migration: 001_fix_exit_criteria_format.py
UPDATE gates
SET exit_criteria = jsonb_build_array(
  jsonb_build_object('criterion', 'Problem statement', 'description', exit_criteria->0),
  jsonb_build_object('criterion', 'User personas', 'description', exit_criteria->1),
  jsonb_build_object('criterion', 'Market', 'description', exit_criteria->2)
)
WHERE jsonb_typeof(exit_criteria->0) = 'string';
```

---

## Recommendation

**For Sprint 33 Day 4**: **Option A** (Quick Fix)
- Unblocks smoke testing
- Minimal risk
- Allows both string and dict formats

**For Sprint 34**: **Option B + Option C**
- Update seed data to use proper dict format
- Add data migration to fix existing records
- Update schema to enforce dict format only

---

## Workaround (Until Fixed)

### Query Gates via Database

```bash
docker exec sdlc-postgres psql -U sdlc_user -d sdlc_orchestrator -c "
  SELECT id, gate_code, stage, status
  FROM gates
  LIMIT 5;
"
```

### Create New Gate (POST works)

```bash
curl -X POST http://localhost:8300/api/v1/gates \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "<uuid>",
    "gate_code": "G0.1",
    "stage": "WHY",
    "exit_criteria": [
      {"criterion": "Test", "description": "Value"}
    ]
  }'
```

---

## Action Items

- [ ] **Sprint 33 Day 4**: Document issue (this file) ✅
- [ ] **Sprint 34**: Apply Option A quick fix
- [ ] **Sprint 34**: Create data migration (Option C)
- [ ] **Sprint 34**: Update seed data (Option B)
- [ ] **Sprint 34**: Add integration test for schema validation
- [ ] **Sprint 34**: Update API documentation with exit_criteria format

---

## Testing

### Verify Fix (After Applied)

```bash
# Login
TOKEN=$(curl -s -X POST http://localhost:8300/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@sdlc-orchestrator.io","password":"Admin@123"}' | \
  python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

# Test gates list
curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8300/api/v1/gates?page=1&page_size=5" | \
  python3 -m json.tool

# Expected: 200 OK with gates array (no validation error)
```

---

**Status**: Documented
**Assigned**: Backend Team (Sprint 34)
**Priority**: P2
**ETA**: Sprint 34 Day 1 (1 hour fix + 1 hour testing)
