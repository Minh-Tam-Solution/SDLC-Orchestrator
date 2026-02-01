---
spec_id: BAD-FORMAT
title: "Invalid Specification - Bad Formats"
version: "v1.0"
status: INVALID_STATUS
tier:
  - INVALID_TIER
owner: "Test"
last_updated: "30-01-2026"
---

# Bad Format Specification

**Sprint 126 E2E Test Fixture** - This spec has format violations.

## Expected Violations

All frontends should detect:
- SPC-002: Invalid spec_id format (expected SPEC-XXYY, got BAD-FORMAT)
- SPC-002: Invalid version format (expected X.Y.Z, got v1.0)
- SPC-002: Invalid status value (expected DRAFT/APPROVED/ACTIVE/DEPRECATED)
- SPC-002: Invalid tier value (expected LITE/STANDARD/PROFESSIONAL/ENTERPRISE)
- SPC-002: Invalid date format (expected YYYY-MM-DD, got 30-01-2026)
