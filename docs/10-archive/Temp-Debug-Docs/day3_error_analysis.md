# Week 6 Day 3 - Test Error Analysis
**Date**: November 21, 2025
**Analysis Time**: 13:15 PST
**Total Tests**: 104

## Summary

| Status | Count | Percentage |
|--------|-------|------------|
| PASSING | 13 | 12.5% |
| SKIPPED | 8 | 7.7% |
| FAILING | 6 | 5.8% |
| ERRORS | 77 | 74.0% |

## Error Categories

### Category 1: `username` Field Error (18 tests) - QUICK FIX
**Root Cause**: Test files use `username` field, but User model only has `email` and `name`

**Affected Files**:
- `test_all_endpoints.py` (18 tests)

**Error Message**:
```
TypeError: 'username' is an invalid keyword argument for User
```

**Fix**: Replace `username` with `email` in fixture definitions

**Priority**: HIGH (Quick win - 1 hour)
**Impact**: +18 tests passing

---

### Category 2: Missing `access_token` Fixture (4 tests) - QUICK FIX
**Root Cause**: Tests expect `access_token` fixture, but we use `auth_headers`

**Affected Files**:
- `test_api_endpoints_simple.py` (4 tests)

**Error Message**:
```
fixture 'access_token' not found
```

**Fix**: Either create `access_token` fixture OR change tests to use `auth_headers`

**Priority**: HIGH (Quick win - 30 min)
**Impact**: +4 tests passing

---

### Category 3: SQLAlchemy Transaction Issues (Test Data Isolation) - MEDIUM FIX
**Root Cause**: Tests not properly cleaning up between runs, causing:
- "duplicate key value violates unique constraint"
- "Can't operate on closed transaction"

**Affected Files**:
- `test_auth_integration.py` (2 tests)

**Error Messages**:
```
sqlalchemy.exc.InvalidRequestError: Can't operate on closed transaction
asyncpg.exceptions.UniqueViolationError: duplicate key value violates unique constraint "ix_users_email"
```

**Fix**: Review conftest.py database rollback logic

**Priority**: MEDIUM (2 hours)
**Impact**: +2-5 tests passing

---

### Category 4: Gates API Tests (All Require Fixtures) - FIXTURE DEPENDENCY
**Root Cause**: All gates tests ERROR because they depend on `test_user` fixture that has `username` issue

**Affected Files**:
- `test_gates_integration.py` (18 tests)

**Fix**: Once Category 1 is fixed, these should work

**Priority**: BLOCKED by Category 1
**Impact**: +18 tests (after Category 1 fix)

---

### Category 5: Evidence API Tests (Require test_gate + auth) - FIXTURE DEPENDENCY
**Root Cause**: All evidence tests ERROR because they depend on auth fixtures

**Affected Files**:
- `test_evidence_integration.py` (12 tests)

**Fix**: Once Category 1 is fixed, these should work

**Priority**: BLOCKED by Category 1
**Impact**: +12 tests (after Category 1 fix)

---

### Category 6: Policies API Tests (Require auth) - FIXTURE DEPENDENCY
**Root Cause**: All policy tests ERROR because they depend on auth fixtures

**Affected Files**:
- `test_policies_integration.py` (16 tests)

**Fix**: Once Category 1 is fixed, these should work

**Priority**: BLOCKED by Category 1
**Impact**: +16 tests (after Category 1 fix)

---

### Category 7: Endpoint Not Found (3 tests) - ASSERTION FIX
**Root Cause**: Tests calling endpoints with wrong paths

**Affected Tests**:
- `test_all_endpoints.py::test_health_check` (expects `/health` not `/api/v1/health`)
- `test_all_endpoints.py::test_version` (endpoint doesn't exist)

**Error Message**:
```
HTTP/1.1 404 Not Found
```

**Fix**: Update endpoint paths or add skip markers

**Priority**: LOW (30 min)
**Impact**: +2 tests passing

---

### Category 8: Assertion Failures (6 tests) - ASSERTION FIX
**Root Cause**: Tests pass but assertions expect wrong values

**Affected Tests**:
- `test_all_endpoints.py::test_register` (404 - endpoint not implemented)
- `test_auth_integration.py::test_login_inactive_user` (wrong error message)
- `test_auth_integration.py::test_get_current_user_no_token` (expects 401, gets 403)
- `test_auth_integration.py::test_logout_no_token` (expects 401, gets 403)

**Fix**: Update assertions to match actual API behavior

**Priority**: MEDIUM (1 hour)
**Impact**: +6 tests passing

---

## Execution Plan (Day 3)

### Phase 1: Quick Wins (2 hours) - TARGET: +22 TESTS
1. **Fix Category 1** (username → email) - 1 hour → +18 tests
2. **Fix Category 2** (access_token fixture) - 30 min → +4 tests

### Phase 2: Cascading Fixes (1 hour) - TARGET: +46 TESTS
3. **Re-run tests** after Phase 1 - 10 min
4. **Verify Categories 4,5,6** auto-fixed → +46 tests

### Phase 3: Assertion Fixes (2 hours) - TARGET: +8 TESTS
5. **Fix Category 8** (assertion errors) - 1 hour → +6 tests
6. **Fix Category 7** (endpoint paths) - 30 min → +2 tests
7. **Fix Category 3** (transaction issues) - 30 min → +2-5 tests

### Expected Day 3 Results:
- **Tests Passing**: 13 → 85+ (85/104 = 82%)
- **Coverage**: 63% → 78-82%
- **Time**: 5 hours (fits in 1 day)

