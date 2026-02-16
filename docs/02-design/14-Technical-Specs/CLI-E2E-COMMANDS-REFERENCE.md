# CLI E2E Commands Reference

**Version**: 1.5.0
**Sprint**: 140 - CLI Orchestration Upgrade
**Framework**: SDLC 6.0.6 (RFC-SDLC-602)
**Status**: Production Ready

---

## Overview

The `sdlcctl e2e` command group provides E2E API testing capabilities following the RFC-SDLC-602 6-Phase workflow:

| Phase | Command | Purpose |
|-------|---------|---------|
| Phase 0 | - | Check documentation (automatic) |
| Phase 1 | `e2e auth-setup` | Setup authentication |
| Phase 2 | Backend API | Execute tests via API |
| Phase 3 | `e2e generate-report` | Generate test reports |
| Phase 4 | - | Update docs (automatic) |
| Phase 5 | `e2e cross-reference` | Validate cross-references |

---

## Command: `sdlcctl e2e validate`

Validate E2E API test artifacts against SDLC 6.0.5 requirements.

### Synopsis

```bash
sdlcctl e2e validate [OPTIONS]
```

### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--project-path`, `-p` | PATH | `.` | Project root path |
| `--init` | FLAG | `false` | Initialize E2E folder structure |
| `--use-opa/--no-opa` | FLAG | `true` | Use OPA for policy evaluation |
| `--format`, `-f` | ENUM | `text` | Output format: text, json, summary |
| `--strict`, `-s` | FLAG | `false` | Exit with error code 1 if validation fails |

### Examples

```bash
# Basic validation
sdlcctl e2e validate

# Initialize E2E structure with templates
sdlcctl e2e validate --init

# Validate with OPA policies
sdlcctl e2e validate --use-opa

# Skip OPA, use local validation
sdlcctl e2e validate --no-opa

# JSON output for CI/CD
sdlcctl e2e validate --format json --strict
```

### Initialization (`--init`)

Creates the following structure:

```
docs/05-Testing-Quality/03-E2E-Testing/
├── README.md                    # E2E testing guidelines
├── collections/
│   └── api-tests.postman.json   # Postman collection template
├── tests/
│   └── test_api_endpoints.py    # pytest test template
└── reports/
    └── .gitkeep                 # Report output directory
```

### Exit Codes

| Code | Condition |
|------|-----------|
| 0 | Validation passed |
| 1 | Validation failed (with `--strict`) |

---

## Command: `sdlcctl e2e cross-reference`

Validate Stage 03 ↔ Stage 05 cross-references and SSOT compliance.

### Synopsis

```bash
sdlcctl e2e cross-reference [OPTIONS]
```

### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--project-path`, `-p` | PATH | `.` | Project root path |
| `--stage-03` | PATH | Auto | Path to Stage 03 folder |
| `--stage-05` | PATH | Auto | Path to Stage 05 folder |
| `--use-opa/--no-opa` | FLAG | `true` | Use OPA for policy evaluation |
| `--fix` | FLAG | `false` | Auto-fix SSOT violations |
| `--format`, `-f` | ENUM | `text` | Output format: text, json, summary |
| `--strict`, `-s` | FLAG | `false` | Exit with error code 1 if validation fails |

### Examples

```bash
# Validate cross-references
sdlcctl e2e cross-reference

# Validate specific stage paths
sdlcctl e2e cross-reference \
    --stage-03 docs/03-Integration-APIs \
    --stage-05 docs/05-Testing-Quality

# Auto-fix SSOT violations
sdlcctl e2e cross-reference --fix

# Skip OPA validation
sdlcctl e2e cross-reference --no-opa

# CI/CD mode
sdlcctl e2e cross-reference --strict --format json
```

### Validation Checks

1. **Stage 03 → Stage 05 Links**
   - API documentation references E2E test reports
   - OpenAPI spec linked to test collections

2. **Stage 05 → Stage 03 Links**
   - E2E reports reference API documentation
   - Test results link to OpenAPI spec

3. **SSOT Compliance**
   - Single source of truth for `openapi.json`
   - Canonical location: `docs/03-Integration-APIs/02-API-Specifications/openapi.json`
   - No duplicate files (symlinks allowed)

### Auto-Fix (`--fix`)

When SSOT violations are detected:

1. Creates backup: `openapi.json` → `openapi.json.bak`
2. Replaces duplicate with symlink to canonical location
3. Reports fixed files

**Example output:**
```
[yellow]Attempting to fix SSOT violations...[/yellow]
[green]✓ Fixed 2 SSOT violations[/green]
  • docs/05-Testing-Quality/api/openapi.json → symlink
  • frontend/api/openapi.json → symlink
```

### OPA Policy

When `--use-opa` is enabled, evaluates:

```
sdlc.e2e_testing.stage_cross_reference
```

**Input:**
```json
{
  "project_path": "/path/to/project",
  "stage_03_path": "/path/to/docs/03-Integration-APIs",
  "stage_05_path": "/path/to/docs/05-Testing-Quality"
}
```

**Fallback:** If OPA unavailable, uses local validation logic.

---

## Command: `sdlcctl e2e auth-setup`

Automate authentication configuration for E2E API testing.

### Synopsis

```bash
sdlcctl e2e auth-setup [OPTIONS]
```

### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--project-path`, `-p` | PATH | `.` | Project root path |
| `--auth-type` | ENUM | Interactive | oauth2, apikey, basic, bearer |
| `--client-id` | STRING | Interactive | OAuth2 client ID |
| `--client-secret` | STRING | Interactive | OAuth2 client secret |
| `--token-url` | URL | Interactive | OAuth2 token endpoint |
| `--api-key` | STRING | Interactive | API key value |
| `--username` | STRING | Interactive | Basic auth username |
| `--password` | STRING | Interactive | Basic auth password |
| `--bearer-token` | STRING | Interactive | Bearer token value |
| `--output`, `-o` | PATH | `.env.test` | Output file for credentials |
| `--interactive/--no-interactive` | FLAG | `true` | Interactive mode |

### Examples

```bash
# Interactive setup (prompts for auth type and credentials)
sdlcctl e2e auth-setup

# OAuth2 setup (non-interactive)
sdlcctl e2e auth-setup \
    --auth-type oauth2 \
    --client-id "my-client-id" \
    --client-secret "my-secret" \
    --token-url "https://auth.example.com/oauth/token" \
    --no-interactive

# API Key setup
sdlcctl e2e auth-setup \
    --auth-type apikey \
    --api-key "my-api-key-12345" \
    --output .env.test

# Basic Auth setup
sdlcctl e2e auth-setup \
    --auth-type basic \
    --username "test-user" \
    --password "test-pass" \
    --no-interactive

# Bearer token setup
sdlcctl e2e auth-setup \
    --auth-type bearer \
    --bearer-token "eyJhbGciOiJIUzI1NiIs..."
```

### Auth Types

| Type | Required Options | Output Variables |
|------|------------------|------------------|
| `oauth2` | client-id, client-secret, token-url | `OAUTH_CLIENT_ID`, `OAUTH_CLIENT_SECRET`, `OAUTH_TOKEN_URL` |
| `apikey` | api-key | `API_KEY` |
| `basic` | username, password | `BASIC_AUTH_USER`, `BASIC_AUTH_PASS` |
| `bearer` | bearer-token | `BEARER_TOKEN` |

### Output Files

**`.env.test`** (credentials, gitignored):
```bash
# E2E API Testing Credentials
# Generated by sdlcctl e2e auth-setup
# DO NOT COMMIT THIS FILE

AUTH_TYPE=oauth2
OAUTH_CLIENT_ID=my-client-id
OAUTH_CLIENT_SECRET=my-secret
OAUTH_TOKEN_URL=https://auth.example.com/oauth/token
```

**`.env.test.example`** (template for team):
```bash
# E2E API Testing Credentials Template
# Copy to .env.test and fill in values

AUTH_TYPE=oauth2
OAUTH_CLIENT_ID=<your-client-id>
OAUTH_CLIENT_SECRET=<your-client-secret>
OAUTH_TOKEN_URL=<your-token-url>
```

---

## Command: `sdlcctl e2e generate-report`

Generate E2E API test report from test results.

### Synopsis

```bash
sdlcctl e2e generate-report [OPTIONS]
```

### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--results`, `-r` | PATH | Required | Path to test results JSON file |
| `--output`, `-o` | PATH | Auto | Output directory for report |
| `--project-path`, `-p` | PATH | `.` | Project root path |
| `--api-reference` | PATH | None | Path to API reference document |
| `--openapi` | PATH | None | Path to OpenAPI spec (SSOT link) |

### Examples

```bash
# Generate report from pytest results
sdlcctl e2e generate-report \
    --results test-results.json

# Generate with custom output directory
sdlcctl e2e generate-report \
    --results test-results.json \
    --output docs/05-Testing-Quality/03-E2E-Testing/reports/

# Generate with cross-references
sdlcctl e2e generate-report \
    --results test-results.json \
    --api-reference docs/03-Integration-APIs/API-Reference.md \
    --openapi docs/03-Integration-APIs/02-API-Specifications/openapi.json
```

### Input Format

**test-results.json:**
```json
{
  "summary": {
    "total": 50,
    "passed": 47,
    "failed": 2,
    "skipped": 1,
    "duration_seconds": 45.2
  },
  "tests": [
    {
      "name": "test_get_users",
      "endpoint": "GET /api/v1/users",
      "status": "passed",
      "duration_ms": 120
    },
    {
      "name": "test_create_user_invalid",
      "endpoint": "POST /api/v1/users",
      "status": "failed",
      "error": "Expected 400, got 500"
    }
  ]
}
```

### Output Format

**E2E-Test-Report-2026-02-13.md:**
```markdown
# E2E API Test Report

**Date**: 2026-02-13
**Pass Rate**: 94% (47/50)
**Duration**: 45.2s

## Summary

| Metric | Value |
|--------|-------|
| Total Tests | 50 |
| Passed | 47 |
| Failed | 2 |
| Skipped | 1 |

## Failed Tests

### test_create_user_invalid
- **Endpoint**: POST /api/v1/users
- **Error**: Expected 400, got 500

## Cross-References

- [API Reference](../03-Integration-APIs/API-Reference.md)
- [OpenAPI Spec](../03-Integration-APIs/02-API-Specifications/openapi.json)
```

---

## Backend API Integration

The CLI integrates with the SDLC Orchestrator backend for test execution.

### Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/e2e/execute` | POST | Queue test execution |
| `/api/v1/e2e/results/{id}` | GET | Get test results |
| `/api/v1/e2e/status/{id}` | GET | Check execution status |
| `/api/v1/e2e/cancel/{id}` | POST | Cancel running tests |
| `/api/v1/e2e/history` | GET | Get execution history |

### Environment Variables

```bash
# SDLC Orchestrator API
export SDLC_API_URL=https://sdlc.example.com/api/v1
export SDLC_API_TOKEN=your-api-token

# OPA Server (optional)
export OPA_URL=http://localhost:8181
export OPA_TIMEOUT=10.0

# Redis (for execution store)
export REDIS_URL=redis://localhost:6379
```

---

## OPA Policy Reference

### E2E Testing Compliance

**Policy Path**: `sdlc.e2e_testing.e2e_testing_compliance`

**Input:**
```json
{
  "project_path": "/path/to/project",
  "min_pass_rate": 80,
  "evidence": [
    {"artifact_type": "E2E_TESTING_REPORT", "metadata": {"pass_rate": 95}},
    {"artifact_type": "API_DOCUMENTATION_REFERENCE"}
  ]
}
```

**Output:**
```json
{
  "allow": true,
  "violations": [],
  "warnings": [],
  "details": {
    "has_e2e_report": true,
    "has_api_documentation": true,
    "e2e_pass_rate": 95
  }
}
```

### Cross-Reference Validation

**Policy Path**: `sdlc.e2e_testing.stage_cross_reference`

**Input:**
```json
{
  "project_path": "/path/to/project",
  "stage_03_path": "/path/to/docs/03-Integration-APIs",
  "stage_05_path": "/path/to/docs/05-Testing-Quality"
}
```

**Output:**
```json
{
  "allow": true,
  "violations": [],
  "details": {
    "has_stage_03_links": true,
    "has_stage_05_links": true,
    "ssot_compliance": true,
    "duplicate_openapi_locations": []
  }
}
```

---

## Fallback Behavior

When OPA is unavailable, the CLI uses local validation:

1. **E2E Compliance Fallback**
   - Checks for E2E test report existence
   - Checks for API documentation reference
   - Validates pass rate against minimum threshold

2. **Cross-Reference Fallback**
   - Verifies Stage 03 and Stage 05 folders exist
   - Scans for duplicate `openapi.json` files
   - Validates symlinks point to canonical location

**Fallback Indicator:**
```
[yellow]OPA unavailable, using local validation[/yellow]
```

---

## CI/CD Integration

### GitHub Actions

```yaml
name: E2E Validation

on: [push, pull_request]

jobs:
  e2e-validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install sdlcctl
        run: pip install sdlcctl

      - name: Validate E2E Structure
        run: sdlcctl e2e validate --strict

      - name: Validate Cross-References
        run: sdlcctl e2e cross-reference --strict --format json

      - name: Generate Report
        if: always()
        run: |
          if [ -f test-results.json ]; then
            sdlcctl e2e generate-report --results test-results.json
          fi
```

### GitLab CI

```yaml
e2e-validation:
  stage: test
  image: python:3.11
  script:
    - pip install sdlcctl
    - sdlcctl e2e validate --strict
    - sdlcctl e2e cross-reference --strict
```

---

## Troubleshooting

### Common Issues

**1. "OPA unavailable"**
```bash
# Check OPA server status
curl http://localhost:8181/health

# Use local validation
sdlcctl e2e cross-reference --no-opa
```

**2. "SSOT violation detected"**
```bash
# Auto-fix duplicates
sdlcctl e2e cross-reference --fix

# Or manually create symlink
ln -sf ../03-Integration-APIs/02-API-Specifications/openapi.json duplicate/openapi.json
```

**3. "Redis connection failed"**
```bash
# Check Redis status
redis-cli ping

# Backend falls back to in-memory storage
# Test results may not persist across restarts
```

**4. "Auth setup failed"**
```bash
# Check OAuth token URL is accessible
curl -X POST https://auth.example.com/oauth/token

# Use interactive mode for debugging
sdlcctl e2e auth-setup --interactive
```

---

## References

- [RFC-SDLC-602: E2E API Testing Enhancement](../../01-planning/02-RFCs/RFC-SDLC-602-E2E-API-TESTING.md)
- [Sprint 140 Progress](../../04-build/02-Sprint-Plans/SPRINT-140-PROGRESS.md)
- [OPA Client Library](../../../backend/sdlcctl/sdlcctl/lib/opa_client.py)
- [E2E Testing Endpoint](../../../backend/app/api/v1/endpoints/e2e_testing.py)

---

**Document Status**: Production Ready
**Last Updated**: February 13, 2026
**Author**: Engineering Team
**Reviewed By**: CTO (Sprint 140 Day 4)
