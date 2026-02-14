# FR-036: Validate Consistency Command (sdlcctl validate-consistency)

**Version**: 1.0.0
**Status**: APPROVED
**Created**: February 1, 2026
**Sprint**: Sprint 136
**Framework**: SDLC 6.0.5
**Related Spec**: SPEC-0021 Stage Consistency Validation
**Owner**: Backend Team

---

## 1. Overview

### 1.1 Purpose

Implement the `sdlcctl validate-consistency` command that validates consistency between Stage 01 (Planning), Stage 02 (Design), Stage 03 (Integrate), and Stage 04 (Build) artifacts.

### 1.2 Business Value

- **Reduces rework** by catching stage drift before merge
- **Improves quality** by enforcing stage-to-stage consistency
- **Saves time** - 60% reduction in manual review time (per SPEC-0021 metrics)
- **Enables CI/CD integration** for automated blocking on violations

### 1.3 Success Metrics

| Metric | Current | Target | Measurement |
|--------|---------|--------|-------------|
| Stage consistency violations per sprint | Unknown | <10 | Command output |
| Command execution time | N/A | <30 seconds | Timer in output |
| CI/CD integration adoption | 0% | 100% | GitHub Actions usage |

---

## 2. Functional Requirements

### 2.1 Command Signature

```bash
sdlcctl validate-consistency \
  --stage 01 <path_to_stage_01> \
  --stage 02 <path_to_stage_02> \
  --stage 03 <path_to_stage_03> \
  --stage 04 <path_to_stage_04> \
  [--tier TIER] \
  [--format FORMAT] \
  [--output OUTPUT_PATH] \
  [--strict] \
  [--verbose]
```

### 2.2 Required Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `--stage 01` | Path | Path to Stage 01 (Planning) folder | `docs/01-planning/` |
| `--stage 02` | Path | Path to Stage 02 (Design) folder | `docs/02-design/` |
| `--stage 03` | Path | Path to Stage 03 (Integrate) folder | `docs/03-integrate/` |
| `--stage 04` | Path | Path to Stage 04 (Build) folder | `backend/app/` |

### 2.3 Optional Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `--tier` | Enum | Auto-detect | LITE, STANDARD, PROFESSIONAL, ENTERPRISE |
| `--format` | Enum | `text` | Output format: text, json, github, summary |
| `--output` | Path | stdout | Write output to file |
| `--strict` | Flag | False | Exit code 1 if any violations |
| `--verbose` | Flag | False | Show detailed context |
| `--check-checksums` | Path | None | Verify artifact integrity against checksum file |

---

## 3. Validation Rules

### 3.1 Stage 01 ↔ Stage 02 Consistency

| Rule ID | Description | Severity |
|---------|-------------|----------|
| CONS-001 | ADRs must reference Stage 01 requirements | ERROR (PRO+), WARNING (STD) |
| CONS-002 | Design documents must cite specification IDs | WARNING |
| CONS-003 | Architecture decisions must trace to user stories | INFO |

### 3.2 Stage 02 ↔ Stage 03 Consistency

| Rule ID | Description | Severity |
|---------|-------------|----------|
| CONS-004 | API contracts must match architecture design | ERROR (PRO+) |
| CONS-005 | Integration strategy must reference ADRs | WARNING |
| CONS-006 | Third-party dependencies must be documented | WARNING |

### 3.3 Stage 03 ↔ Stage 04 Consistency

| Rule ID | Description | Severity |
|---------|-------------|----------|
| CONS-007 | API endpoints must match Stage 03 contracts | ERROR |
| CONS-008 | Request/response schemas must match OpenAPI | ERROR |
| CONS-009 | New endpoints must be documented in Stage 03 | WARNING |

### 3.4 Stage 01 ↔ Stage 04 Consistency

| Rule ID | Description | Severity |
|---------|-------------|----------|
| CONS-010 | Implementation must satisfy requirements | ERROR (PRO+) |
| CONS-011 | Behavioral changes must update Stage 01 | WARNING |
| CONS-012 | User stories acceptance criteria must be met | INFO |

---

## 4. Output Specifications

### 4.1 Text Output (default)

```
Stage Consistency Validation Report
====================================
Project: SDLC-Orchestrator
Tier: PROFESSIONAL
Framework: SDLC 6.0.5
Timestamp: 2026-02-01T12:00:00Z

Stage Consistency Results:
--------------------------
✅ Stage 01 ←→ Stage 02: CONSISTENT (0 violations)
✅ Stage 02 ←→ Stage 03: CONSISTENT (0 violations)
⚠️  Stage 03 ←→ Stage 04: 3 violations
✅ Stage 01 ←→ Stage 04: CONSISTENT (0 violations)

Violations:
-----------
[ERROR] CONS-007: API endpoint mismatch
  File: backend/app/api/routes/users.py:45
  Expected: GET /users/{id} (from openapi.yaml)
  Actual: GET /api/v1/users/{id}
  Fix: Update OpenAPI spec or rename endpoint

[WARNING] CONS-009: Undocumented endpoint
  File: backend/app/api/routes/health.py:12
  Endpoint: GET /health
  Fix: Add endpoint to docs/03-integrate/01-api-contracts/openapi.yaml

Summary:
--------
Total violations: 3
  Errors: 1
  Warnings: 2
  Info: 0

Overall consistency: 95.2%
Execution time: 2.34s
```

### 4.2 JSON Output

```json
{
  "schema_version": "1.0.0",
  "project": "SDLC-Orchestrator",
  "tier": "PROFESSIONAL",
  "framework_version": "6.0.5",
  "timestamp": "2026-02-01T12:00:00Z",
  "consistency_checks": {
    "stage_01_02": {"status": "CONSISTENT", "violations": 0},
    "stage_02_03": {"status": "CONSISTENT", "violations": 0},
    "stage_03_04": {"status": "INCONSISTENT", "violations": 3},
    "stage_01_04": {"status": "CONSISTENT", "violations": 0}
  },
  "violations": [
    {
      "rule_id": "CONS-007",
      "severity": "ERROR",
      "file_path": "backend/app/api/routes/users.py",
      "line_number": 45,
      "message": "API endpoint mismatch",
      "expected": "GET /users/{id}",
      "actual": "GET /api/v1/users/{id}",
      "fix_suggestion": "Update OpenAPI spec or rename endpoint"
    }
  ],
  "summary": {
    "total_violations": 3,
    "errors": 1,
    "warnings": 2,
    "info": 0,
    "overall_consistency_percent": 95.2,
    "execution_time_seconds": 2.34
  }
}
```

### 4.3 GitHub Actions Output

```
::error file=backend/app/api/routes/users.py,line=45::CONS-007: API endpoint mismatch - Expected: GET /users/{id}, Actual: GET /api/v1/users/{id}
::warning file=backend/app/api/routes/health.py,line=12::CONS-009: Undocumented endpoint - GET /health
```

---

## 5. Tier-Specific Behavior

### 5.1 LITE Tier

- All consistency checks: Optional (warnings only)
- CI/CD blocking: Disabled
- Exit code: Always 0 unless `--strict`

### 5.2 STANDARD Tier

- CONS-001 to CONS-006: WARNING
- CONS-007 to CONS-012: WARNING
- CI/CD blocking: Optional
- Exit code: 0 unless errors

### 5.3 PROFESSIONAL Tier

- CONS-001, CONS-004, CONS-007, CONS-010: ERROR (blocking)
- Other rules: WARNING
- CI/CD blocking: Default enabled
- Exit code: 1 if any ERROR violations

### 5.4 ENTERPRISE Tier

- All rules: ERROR (blocking)
- CI/CD blocking: Mandatory
- Exit code: 1 if any violations
- Audit trail: Required

---

## 6. Error Handling

### 6.1 Input Validation Errors

| Error | Message | Exit Code |
|-------|---------|-----------|
| Stage path not found | `Error: Stage {N} path does not exist: {path}` | 1 |
| Invalid tier | `Error: Invalid tier '{tier}'. Valid: LITE, STANDARD, PROFESSIONAL, ENTERPRISE` | 1 |
| Invalid format | `Error: Invalid format '{format}'. Valid: text, json, github, summary` | 1 |

### 6.2 Runtime Errors

| Error | Message | Exit Code |
|-------|---------|-----------|
| Parse error | `Warning: Could not parse {file}: {error}` | Continue (skip file) |
| Permission denied | `Error: Permission denied reading {path}` | 1 |
| Timeout | `Error: Validation timed out after {timeout}s` | 1 |

---

## 7. Acceptance Criteria

### 7.1 Functional Criteria

- [ ] Command accepts `--stage` parameters for all 4 stages
- [ ] Command validates consistency between all stage pairs
- [ ] Command outputs results in text, json, github, summary formats
- [ ] Command respects tier-specific severity levels
- [ ] Command supports `--strict` flag for CI/CD integration

### 7.2 Performance Criteria

- [ ] Validation completes in <30 seconds for typical project (1000 files)
- [ ] Memory usage stays under 500MB

### 7.3 Quality Criteria

- [ ] Unit test coverage ≥90%
- [ ] Integration test with real project structure
- [ ] Documentation updated (README, CHANGELOG)

---

## 8. Dependencies

### 8.1 Internal Dependencies

- `sdlcctl.validation.engine` - Validation infrastructure
- `sdlcctl.validation.violation` - Violation reporting
- `sdlcctl.validation.tier` - Tier detection and requirements

### 8.2 External Dependencies

- `typer` - CLI framework
- `rich` - Console output formatting
- `pyyaml` - YAML parsing (OpenAPI specs)
- `jsonschema` - JSON schema validation

---

## 9. Related Documents

- [SPEC-0021: Stage Consistency Validation](../../../SDLC-Enterprise-Framework/05-Templates-Tools/01-Specification-Standard/SPEC-0021-Stage-Consistency-Validation.md)
- [ADR-046: Validate Consistency Command Architecture](../../02-design/01-ADRs/ADR-046-Validate-Consistency-Command.md)
- [Sprint 136 Plan](../../04-build/02-Sprint-Plans/SPRINT-136-VALIDATE-CONSISTENCY.md)

---

**Document Status**: APPROVED
**Approval Date**: February 1, 2026
**Approved By**: CTO Office
