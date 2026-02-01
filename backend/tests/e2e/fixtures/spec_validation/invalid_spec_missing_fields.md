---
spec_id: SPEC-0002
title: "Invalid Specification - Missing Required Fields"
---

# SPEC-0002: Invalid Specification

**Sprint 126 E2E Test Fixture** - This spec is intentionally missing required fields.

## Overview

This specification is missing: version, status, tier, owner, last_updated.

## Expected Violations

All frontends should detect:
- SPC-001: Missing required field 'version'
- SPC-001: Missing required field 'status'
- SPC-001: Missing required field 'tier'
- SPC-001: Missing required field 'owner'
- SPC-001: Missing required field 'last_updated'
