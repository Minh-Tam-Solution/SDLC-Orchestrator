# E2E API Testing Complete Guide

**Version**: 1.0.0
**Sprint**: 141 - Full Workflow Integration
**Framework**: SDLC 6.0.6
**RFC**: RFC-SDLC-602 E2E API Testing Enhancement
**Status**: GA (General Availability)

---

## Executive Summary

This guide provides comprehensive documentation for the RFC-SDLC-602 6-Phase E2E API Testing Workflow. It covers all CLI commands, VS Code Extension features, and best practices for implementing E2E API testing in SDLC 6.0.5 compliant projects.

### Key Features

- **6-Phase Workflow**: Structured approach from documentation check to cross-reference validation
- **CLI Tools**: `sdlcctl e2e` commands for all phases
- **VS Code Integration**: Commands, keybindings, and SSOT enforcement
- **OPA Policy Integration**: Automated compliance checking
- **Zero Mock Policy**: Real test execution and validation

---

## Table of Contents

1. [Overview](#1-overview)
2. [Phase 0: Check Documentation](#2-phase-0-check-documentation)
3. [Phase 1: Setup & Authentication](#3-phase-1-setup--authentication)
4. [Phase 2: Execute Tests](#4-phase-2-execute-tests)
5. [Phase 3: Generate Report](#5-phase-3-generate-report)
6. [Phase 4: Update Stage 03](#6-phase-4-update-stage-03)
7. [Phase 5: Cross-Reference Validation](#7-phase-5-cross-reference-validation)
8. [VS Code Extension](#8-vs-code-extension)
9. [SSOT Enforcement](#9-ssot-enforcement)
10. [Best Practices](#10-best-practices)
11. [Troubleshooting](#11-troubleshooting)

---

## 1. Overview

### RFC-SDLC-602 6-Phase Workflow

```
┌─────────────────────────────────────────────────────────────────────┐
│                    E2E API Testing Workflow                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   Phase 0          Phase 1          Phase 2          Phase 3        │
│   ────────         ────────         ────────         ────────        │
│   Check Docs  →    Setup Auth  →    Execute    →    Generate        │
│   (OpenAPI)        (Credentials)    (Tests)         (Report)        │
│                                                                      │
│                         ↓                                            │
│                                                                      │
│                 Phase 4          Phase 5                             │
│                 ────────         ────────                            │
│                 Update     ←     Cross-Ref                           │
│                 Stage 03         Validation                          │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Prerequisites

- **sdlcctl CLI**: v1.5.0 or later
- **VS Code Extension**: v1.6.0 or later
- **Python**: 3.11+ (for CLI and pytest)
- **Node.js**: 18+ (for Newman runner)

### Installation

```bash
# Install sdlcctl CLI
pip install sdlcctl

# Verify installation
sdlcctl --version
# Output: sdlcctl v1.5.0 (SDLC 6.0.5)

# Install VS Code Extension
code --install-extension sdlc-orchestrator-1.6.0.vsix
```

---

## 2. Phase 0: Check Documentation

**Goal**: Validate that OpenAPI specification exists and is valid.

### CLI Command: `parse-openapi`

```bash
# Basic usage
sdlcctl e2e parse-openapi docs/03-Integration-APIs/02-API-Specifications/openapi.json

# With output file
sdlcctl e2e parse-openapi openapi.json --output endpoints.json

# Generate test scaffolds
sdlcctl e2e parse-openapi openapi.json --generate-tests --test-output tests/e2e/

# Filter by tag
sdlcctl e2e parse-openapi openapi.json --tag users

# Filter by method
sdlcctl e2e parse-openapi openapi.json --method GET

# JSON output
sdlcctl e2e parse-openapi openapi.json --format json
```

### Example Output

```
╭─────────────────────────────────────────────────────────────────────╮
│                         OpenAPI Parser                               │
│                                                                      │
│ File: docs/03-Integration-APIs/02-API-Specifications/openapi.json   │
╰─────────────────────────────────────────────────────────────────────╯

API: SDLC Orchestrator v1.0.0
OpenAPI Version: 3.0.3
Total Endpoints: 64
Servers: https://sdlc.nhatquangholding.com

┏━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━┓
┃ Method   ┃ Path                          ┃ Tags       ┃ Auth       ┃ Summary            ┃
┡━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━┩
│ GET      │ /health                       │ health     │ -          │ Health check       │
│ GET      │ /api/v1/projects              │ projects   │ bearer     │ List projects      │
│ POST     │ /api/v1/projects              │ projects   │ bearer     │ Create project     │
│ GET      │ /api/v1/gates/{id}/evaluate   │ gates      │ bearer     │ Evaluate gate      │
│ ...      │ ...                           │ ...        │ ...        │ ...                │
└──────────┴───────────────────────────────┴────────────┴────────────┴────────────────────┘

Endpoints by Tag:
  • health: 2 endpoints
  • projects: 8 endpoints
  • gates: 12 endpoints
  • evidence: 15 endpoints
  • users: 10 endpoints
```

### Generated Test Scaffolds

When using `--generate-tests`, the following files are created:

```
docs/05-Testing-Quality/03-E2E-Testing/
├── collections/
│   └── sdlc_orchestrator-e2e-collection.json  # Newman collection
├── tests/
│   └── test_sdlc_orchestrator_api.py          # pytest test file
└── .env.e2e.template                          # Environment template
```

---

## 3. Phase 1: Setup & Authentication

**Goal**: Configure authentication credentials for E2E testing.

### CLI Command: `auth-setup`

```bash
# OAuth2 authentication
sdlcctl e2e auth-setup --type oauth2

# API Key authentication
sdlcctl e2e auth-setup --type api_key --output .env.test

# Bearer token authentication
sdlcctl e2e auth-setup --type bearer

# Basic authentication
sdlcctl e2e auth-setup --type basic

# Non-interactive mode (use environment variables)
sdlcctl e2e auth-setup --type bearer --non-interactive
```

### Authentication Types

| Type | Required Inputs | Environment Variables |
|------|-----------------|----------------------|
| `oauth2` | Client ID, Secret, Token URL | `E2E_CLIENT_ID`, `E2E_CLIENT_SECRET`, `E2E_TOKEN_URL` |
| `api_key` | API Key, Header Name | `E2E_API_KEY`, `E2E_API_KEY_HEADER` |
| `bearer` | Bearer Token | `E2E_BEARER_TOKEN` |
| `basic` | Username, Password | `E2E_USERNAME`, `E2E_PASSWORD` |

### Example `.env.test` Output

```bash
# E2E API Testing Credentials
# Generated by: sdlcctl e2e auth-setup --type bearer
# Date: 2026-02-17T10:30:00
# RFC-SDLC-602 Phase 1: Setup & Authentication

E2E_AUTH_TYPE=bearer
E2E_BEARER_TOKEN=sdlc_live_abc123xyz...
```

### Security Note

Always add credential files to `.gitignore`:

```gitignore
# E2E Testing Credentials
.env.test
.env.e2e
*.postman_environment.json
```

---

## 4. Phase 2: Execute Tests

**Goal**: Run E2E API tests using supported test runners.

### CLI Command: `run-tests`

```bash
# pytest runner (default)
sdlcctl e2e run-tests --runner pytest --tests tests/e2e/

# Newman runner
sdlcctl e2e run-tests --runner newman --collection api-tests.json

# With environment file
sdlcctl e2e run-tests --runner pytest --environment .env.test --verbose

# Save results to file
sdlcctl e2e run-tests --runner pytest --report-output results.json

# Parallel execution (pytest)
sdlcctl e2e run-tests --runner pytest --parallel

# Custom timeout
sdlcctl e2e run-tests --runner newman --collection tests.json --timeout 600
```

### Supported Runners

| Runner | Use Case | Requirements |
|--------|----------|--------------|
| `pytest` | Python-based API tests | pytest, pytest-json-report |
| `newman` | Postman collection tests | newman (npm) |
| `rest-assured` | Java-based tests | Maven/Gradle (future) |

### Example Output

```
╭─────────────────────────────────────────────────────────────────────╮
│                      E2E Test Execution                              │
│                                                                      │
│ Runner: pytest                                                       │
╰─────────────────────────────────────────────────────────────────────╯

╭─────────────────────────────────────────────────────────────────────╮
│ PASS | Pass Rate: 95.0%                                             │
╰─────────────────────────────────────────────────────────────────────╯

┏━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┓
┃ Metric           ┃ Value         ┃
┡━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━┩
│ Total Tests      │ 40            │
│ Passed           │ 38            │
│ Failed           │ 2             │
│ Skipped          │ 0             │
│ Duration         │ 12.34s        │
└──────────────────┴───────────────┘

Failed Tests:
  • test_api_endpoints.py::TestProjectsAPI::test_create_project_validation
  • test_api_endpoints.py::TestGatesAPI::test_evaluate_gate_timeout
```

---

## 5. Phase 3: Generate Report

**Goal**: Generate E2E API test report for Stage 05 documentation.

### CLI Command: `generate-report`

```bash
# Basic usage
sdlcctl e2e generate-report --results test_results.json

# Custom output directory
sdlcctl e2e generate-report --results results.json --output docs/05-Testing-Quality/03-E2E-Testing/reports/

# With API reference cross-link
sdlcctl e2e generate-report --results results.json --api-reference docs/03-Integration-APIs/02-API-Specifications/COMPLETE-API-ENDPOINT-REFERENCE.md

# With OpenAPI spec link
sdlcctl e2e generate-report --results results.json --openapi docs/03-Integration-APIs/02-API-Specifications/openapi.json
```

### Generated Report Structure

```markdown
# E2E API Test Report

**Project**: SDLC Orchestrator
**Date**: 2026-02-17 14:30:00
**Framework**: SDLC 6.0.6
**Stage**: 05-Testing-Quality

---

## Summary

| Metric | Value |
|--------|-------|
| Total Tests | 40 |
| Passed | 38 |
| Failed | 2 |
| Skipped | 0 |
| **Pass Rate** | **95.0%** |

### Status: ✅ PASS (Threshold: 80%)

---

## Cross-Reference

### Stage 03 - Integration & APIs
- **API Documentation**: ../../../03-Integration-APIs/02-API-Specifications/COMPLETE-API-ENDPOINT-REFERENCE.md
- **OpenAPI Spec**: ../../../03-Integration-APIs/02-API-Specifications/openapi.json (SSOT)

### SSOT Note
The `openapi.json` file is maintained in Stage 03 (Integration & APIs).
Stage 05 references this file via relative path - **do not duplicate**.
```

---

## 6. Phase 4: Update Stage 03

**Goal**: Update Stage 03 API documentation with test results.

### Automatic Updates

When E2E tests pass, the following may need updates in Stage 03:

1. **API Reference**: Add test coverage badges
2. **OpenAPI Spec**: Update with discovered issues
3. **Change Log**: Document API changes found during testing

### Manual Process

```bash
# 1. Review test results
cat docs/05-Testing-Quality/03-E2E-Testing/reports/E2E-API-REPORT-2026-02-17.md

# 2. Update API reference with test status
# Edit: docs/03-Integration-APIs/02-API-Specifications/COMPLETE-API-ENDPOINT-REFERENCE.md

# 3. Run cross-reference validation
sdlcctl e2e cross-reference
```

---

## 7. Phase 5: Cross-Reference Validation

**Goal**: Validate bidirectional links between Stage 03 and Stage 05.

### CLI Command: `cross-reference`

```bash
# Basic validation
sdlcctl e2e cross-reference

# Custom stage paths
sdlcctl e2e cross-reference \
    --stage-03 docs/03-Integration-APIs \
    --stage-05 docs/05-Testing-Quality

# With auto-fix for SSOT violations
sdlcctl e2e cross-reference --fix

# Using OPA for policy evaluation
sdlcctl e2e cross-reference --use-opa

# JSON output
sdlcctl e2e cross-reference --format json

# Strict mode (exit code 1 on failure)
sdlcctl e2e cross-reference --strict
```

### Validation Checks

| Check | Description |
|-------|-------------|
| Stage 03 → Stage 05 Links | API Reference links to E2E test reports |
| Stage 05 → Stage 03 Links | E2E reports link to API documentation |
| SSOT Compliance | No duplicate `openapi.json` files |

### Example Output

```
╭─────────────────────────────────────────────────────────────────────╮
│                              PASS                                    │
│          Cross-Reference Validation (Stage 03 ↔ Stage 05)           │
╰─────────────────────────────────────────────────────────────────────╯

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┓
┃ Check                                     ┃ Status     ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━┩
│ Stage 03 → Stage 05 Links                 │ ✅          │
│ Stage 05 → Stage 03 Links                 │ ✅          │
│ SSOT Compliance (no duplicate openapi.json)│ ✅         │
└───────────────────────────────────────────┴────────────┘
```

### SSOT Violation Fix

```bash
# Auto-fix creates symlinks for duplicates
sdlcctl e2e cross-reference --fix

# Output:
# Attempting to fix SSOT violations...
# ✓ Fixed 2 SSOT violations
#   • docs/05-Testing-Quality/03-E2E-Testing/openapi.json → ../../03-Integration-APIs/02-API-Specifications/openapi.json
#   • backend/tests/fixtures/openapi.json → ../../../docs/03-Integration-APIs/02-API-Specifications/openapi.json
```

---

## 8. VS Code Extension

### E2E Testing Commands

| Command | Keybinding | Description |
|---------|------------|-------------|
| `SDLC: E2E Validate Testing Compliance` | `Cmd+Shift+E` | Validate E2E compliance |
| `SDLC: E2E Validate Cross-References` | - | Check Stage 03 ↔ 05 links |
| `SDLC: E2E Initialize Testing Structure` | - | Create E2E folder structure |
| `SDLC: Check SSOT Compliance` | - | Detect duplicate openapi.json |
| `SDLC: Fix SSOT Violations` | - | Auto-fix with symlinks |

### Command Palette

1. Press `Cmd+Shift+P` (macOS) or `Ctrl+Shift+P` (Windows/Linux)
2. Type "SDLC E2E" to filter E2E commands
3. Select the desired command

### Diagnostics Integration

SSOT violations appear in the VS Code **Problems** panel:

```
PROBLEMS
─────────────────────────────────────────
docs/05-Testing-Quality/03-E2E-Testing/openapi.json
  ⚠ DUPLICATE_OPENAPI: Duplicate openapi.json found. SSOT location: docs/03-Integration-APIs/02-API-Specifications/openapi.json
```

---

## 9. SSOT Enforcement

### Single Source of Truth Principle

The `openapi.json` file MUST exist only in one canonical location:

```
docs/03-Integration-APIs/02-API-Specifications/openapi.json  ← SSOT (canonical)
```

Other locations should use **symlinks** to reference the canonical file:

```bash
# Example symlink structure
docs/05-Testing-Quality/03-E2E-Testing/openapi.json → ../../03-Integration-APIs/02-API-Specifications/openapi.json
```

### SSOT Validator Features

1. **Detection**: Find all `openapi.json` files in the project
2. **Compliance Check**: Verify only one canonical file exists
3. **Auto-Fix**: Replace duplicates with symlinks
4. **Backup**: Create `.backup` files before modification
5. **Watch Mode**: Monitor for new duplicates

### CLI Validation

```bash
# Validate SSOT compliance
sdlcctl e2e cross-reference

# Auto-fix violations
sdlcctl e2e cross-reference --fix
```

### VS Code Validation

```
Command Palette → SDLC: Check SSOT Compliance
Command Palette → SDLC: Fix SSOT Violations
```

---

## 10. Best Practices

### 1. Project Structure

```
project-root/
├── docs/
│   ├── 03-Integration-APIs/
│   │   └── 02-API-Specifications/
│   │       ├── openapi.json          ← SSOT (canonical)
│   │       └── COMPLETE-API-ENDPOINT-REFERENCE.md
│   └── 05-Testing-Quality/
│       └── 03-E2E-Testing/
│           ├── README.md
│           ├── tests/
│           │   └── test_api_endpoints.py
│           ├── collections/
│           │   └── api-tests.json
│           ├── reports/
│           │   └── E2E-API-REPORT-YYYY-MM-DD.md
│           └── evidence/
│               └── test-results.json
├── .env.test                          ← Git-ignored credentials
└── .gitignore
```

### 2. Test Naming Conventions

```python
# Good: Descriptive, follows pattern
def test_create_project_returns_201_with_valid_input():
    ...

def test_get_project_by_id_returns_404_when_not_found():
    ...

# Bad: Vague, no context
def test_project():
    ...

def test_api():
    ...
```

### 3. Environment Management

```bash
# Development
E2E_BASE_URL=http://localhost:8000
E2E_AUTH_TYPE=bearer
E2E_BEARER_TOKEN=dev_token

# Staging
E2E_BASE_URL=https://staging.sdlc.example.com
E2E_AUTH_TYPE=oauth2
E2E_TOKEN_URL=https://auth.example.com/oauth/token

# Production (read-only tests only!)
E2E_BASE_URL=https://sdlc.nhatquangholding.com
E2E_AUTH_TYPE=bearer
E2E_BEARER_TOKEN=readonly_token
```

### 4. CI/CD Integration

```yaml
# GitHub Actions example
name: E2E API Tests

on:
  push:
    branches: [main]
  pull_request:

jobs:
  e2e-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install sdlcctl
        run: pip install sdlcctl

      - name: Phase 0: Parse OpenAPI
        run: sdlcctl e2e parse-openapi docs/03-Integration-APIs/02-API-Specifications/openapi.json

      - name: Phase 1: Setup Auth
        run: sdlcctl e2e auth-setup --type bearer --non-interactive
        env:
          E2E_BEARER_TOKEN: ${{ secrets.E2E_BEARER_TOKEN }}

      - name: Phase 2: Run Tests
        run: sdlcctl e2e run-tests --runner pytest --tests tests/e2e/ --report-output results.json

      - name: Phase 3: Generate Report
        run: sdlcctl e2e generate-report --results results.json

      - name: Phase 5: Validate Cross-References
        run: sdlcctl e2e cross-reference --strict
```

---

## 11. Troubleshooting

### Common Issues

#### Issue: "OPA unavailable" warning

**Cause**: OPA server not running or unreachable.

**Solution**: The CLI uses local fallback validation automatically. To use OPA:

```bash
# Start OPA server
docker run -d -p 8181:8181 openpolicyagent/opa run --server

# Verify OPA is running
curl http://localhost:8181/health
```

#### Issue: "Newman not found"

**Cause**: Newman CLI not installed.

**Solution**:

```bash
npm install -g newman
```

#### Issue: "SSOT violation detected"

**Cause**: Duplicate `openapi.json` files in the project.

**Solution**:

```bash
# Auto-fix with symlinks
sdlcctl e2e cross-reference --fix
```

#### Issue: "E2E_BEARER_TOKEN not set"

**Cause**: Missing credentials for non-interactive mode.

**Solution**:

```bash
export E2E_BEARER_TOKEN="your_token_here"
sdlcctl e2e auth-setup --type bearer --non-interactive
```

#### Issue: "pytest-json-report not found"

**Cause**: Missing pytest plugin for JSON reports.

**Solution**:

```bash
pip install pytest-json-report
```

---

## References

- [RFC-SDLC-602: E2E API Testing Enhancement](../../01-planning/02-RFCs/RFC-SDLC-602-E2E-API-TESTING.md)
- [CLI E2E Commands Reference](./CLI-E2E-COMMANDS-REFERENCE.md)
- [Sprint 139 Release Notes](../../09-govern/01-CTO-Reports/SPRINT-139-RELEASE-NOTES.md)
- [Sprint 140 Release Notes](../../09-govern/01-CTO-Reports/SPRINT-140-RELEASE-NOTES.md)
- [VS Code Extension CHANGELOG](../../../vscode-extension/CHANGELOG.md)

---

**Document Status**: GA (General Availability)
**Last Updated**: February 17, 2026
**Author**: Engineering Team
**Reviewed By**: CTO
