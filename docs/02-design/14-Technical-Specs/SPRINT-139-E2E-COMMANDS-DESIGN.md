# Sprint 139: E2E Commands Design Document

**Version**: 1.0
**Date**: February 2, 2026
**Sprint**: 139 (Feb 3-7, 2026)
**Status**: ✅ DESIGN COMPLETE
**Framework**: SDLC 6.0.5 (RFC-SDLC-602)

---

## 1. Current State Analysis

### 1.1 CLI Commands (`sdlcctl e2e`)

**File**: `backend/sdlcctl/sdlcctl/commands/e2e.py` (714 LOC)

| Command | Status | Options | Missing |
|---------|--------|---------|---------|
| `e2e validate` | ✅ Implemented | `--project-path`, `--min-pass-rate`, `--from-stage`, `--to-stage`, `--evidence`, `--format`, `--strict` | `--init` flag |
| `e2e cross-reference` | ✅ Implemented | `--stage-03`, `--stage-05`, `--project-path`, `--format`, `--strict` | `--fix` flag |
| `e2e generate-report` | ✅ Implemented | `--results`, `--output`, `--project-path`, `--api-reference`, `--openapi` | - |

**CLI Gap Analysis**:
- ❌ `--init` flag mentioned in docstring but not implemented
- ❌ `--fix` flag for cross-reference mentioned but not implemented
- ❌ Uses local validation logic instead of OPA policy calls
- ❌ No `auth-setup` command (Phase 1 automation)
- ❌ No `parse-openapi` command (Phase 0)
- ❌ No `run-tests` command (Phase 2 wrapper)

### 1.2 Extension Commands

**File**: `vscode-extension/package.json`

| Declared Commands | E2E Related? |
|-------------------|--------------|
| 36 commands total | ❌ None are E2E |

**Extension Gap Analysis**:
- ❌ No `sdlc.e2eValidate` command
- ❌ No `sdlc.e2eCrossReference` command
- ❌ No `sdlc.e2eInit` command
- ❌ No E2E-related keybindings
- ❌ README declares E2E awareness but no implementation

### 1.3 Evidence Types

**File**: `vscode-extension/src/types/evidence.ts` (CREATED)

| Type | Status |
|------|--------|
| `E2E_TESTING_REPORT` | ✅ Created |
| `API_DOCUMENTATION_REFERENCE` | ✅ Created |
| `SECURITY_TESTING_RESULTS` | ✅ Created |
| `STAGE_CROSS_REFERENCE` | ✅ Created |

---

## 2. Sprint 139 Implementation Design

### 2.1 Extension Commands to Add

#### 2.1.1 `sdlc.e2eValidate`

**Purpose**: Validate E2E testing compliance from IDE

**Implementation**:
```typescript
// vscode-extension/src/commands/e2eValidateCommand.ts

registerCommand('sdlc.e2eValidate', async () => {
    // 1. Get workspace root
    // 2. Find Stage 05 path
    // 3. Load test results
    // 4. Validate compliance
    // 5. Update diagnostics
    // 6. Show summary
})
```

**Options** (via quick pick):
- Minimum pass rate: 80% (default)
- Strict mode: false (default)
- Init mode: false (default)

**Keybinding**: `Cmd+Shift+E` (was for Evidence, repurpose)

#### 2.1.2 `sdlc.e2eCrossReference`

**Purpose**: Validate Stage 03 ↔ Stage 05 cross-references

**Implementation**:
```typescript
// vscode-extension/src/commands/e2eCrossRefCommand.ts

registerCommand('sdlc.e2eCrossReference', async () => {
    // 1. Find Stage 03 and Stage 05 paths
    // 2. Parse OpenAPI from Stage 03
    // 3. Find test files in Stage 05
    // 4. Match endpoints to tests
    // 5. Calculate coverage
    // 6. Show tree view with missing tests
})
```

**Options**:
- Strict mode: Fail if coverage < 80%
- Fix mode: Generate test stubs for uncovered endpoints

#### 2.1.3 `sdlc.e2eInit`

**Purpose**: Initialize E2E testing folder structure

**Implementation**:
```typescript
// Already in e2eValidateCommand.ts

registerCommand('sdlc.e2eInit', async () => {
    // 1. Create Stage 05/03-E2E-Testing/ folders
    // 2. Create template README
    // 3. Create template test script
})
```

### 2.2 Package.json Updates

```json
{
    "commands": [
        {
            "command": "sdlc.e2eValidate",
            "title": "E2E: Validate Testing Compliance",
            "category": "SDLC",
            "icon": "$(beaker)"
        },
        {
            "command": "sdlc.e2eCrossReference",
            "title": "E2E: Validate Cross-References",
            "category": "SDLC",
            "icon": "$(references)"
        },
        {
            "command": "sdlc.e2eInit",
            "title": "E2E: Initialize Testing Structure",
            "category": "SDLC",
            "icon": "$(folder-opened)"
        },
        {
            "command": "sdlc.e2eValidateWithOptions",
            "title": "E2E: Validate with Options",
            "category": "SDLC"
        },
        {
            "command": "sdlc.showE2EResults",
            "title": "E2E: Show Validation Results",
            "category": "SDLC"
        }
    ],
    "keybindings": [
        {
            "command": "sdlc.e2eValidate",
            "key": "ctrl+shift+e",
            "mac": "cmd+shift+e"
        }
    ]
}
```

### 2.3 Backend API (New Endpoint)

**Endpoint**: `POST /api/v1/cross-reference/validate`

**Purpose**: Server-side cross-reference validation with OPA

**Request**:
```json
{
    "project_id": "uuid",
    "stage_03_path": "docs/03-integrate",
    "stage_05_path": "docs/05-deploy"
}
```

**Response**:
```json
{
    "success": true,
    "api_endpoints": [...],
    "test_files": [...],
    "coverage": {
        "total": 58,
        "covered": 45,
        "percentage": 77.6
    },
    "missing_tests": [...],
    "validation_timestamp": "2026-02-02T..."
}
```

---

## 3. File Changes Summary

### 3.1 New Files (Extension)

| File | LOC | Purpose |
|------|-----|---------|
| `src/commands/e2eValidateCommand.ts` | 250 | E2E validate command |
| `src/commands/e2eCrossRefCommand.ts` | 300 | Cross-reference command |
| `src/types/evidence.ts` | 150 | ✅ Created - Evidence types |

### 3.2 Modified Files (Extension)

| File | Changes |
|------|---------|
| `package.json` | Add 5 commands, 1 keybinding |
| `src/extension.ts` | Import and register E2E commands |

### 3.3 New Files (Backend)

| File | LOC | Purpose |
|------|-----|---------|
| `api/v1/endpoints/cross_reference.py` | 200 | Cross-reference API |

---

## 4. Implementation Sequence

### Day 1 (Feb 3)
1. ✅ Evidence types created (`types/evidence.ts`)
2. E2E Validate command (`e2eValidateCommand.ts`)
3. Register in `extension.ts`
4. Add to `package.json`

### Day 2 (Feb 4)
1. Cross-Reference command (`e2eCrossRefCommand.ts`)
2. Tree view provider for cross-ref results
3. Quick fixes for missing tests

### Day 3 (Feb 5)
1. Backend API endpoint (`cross_reference.py`)
2. OPA policy integration
3. Integration tests

### Day 4 (Feb 6)
1. Update Extension README
2. Unit tests for commands
3. Integration tests (Extension → Backend)

### Day 5 (Feb 7)
1. Code review
2. Fix issues
3. Deploy to staging: Extension v1.5.0

---

## 5. Testing Strategy

### 5.1 Unit Tests

```typescript
// src/test/suite/e2eValidateCommand.test.ts

describe('E2E Validate Command', () => {
    it('should detect missing Stage 05 folder')
    it('should load test results from JSON')
    it('should validate pass rate threshold')
    it('should update diagnostics')
})
```

### 5.2 Dogfooding

Run on SDLC-Orchestrator itself:
```bash
# From Extension
Cmd+Shift+E  # Trigger sdlc.e2eValidate

# Expected: Find Stage 05, validate compliance
```

---

## 6. Success Criteria

| Metric | Target | Validation |
|--------|--------|------------|
| E2E commands in Extension | 5/5 | package.json check |
| Feature parity | 15% → 90% | E2E commands work |
| Unit test coverage | 80%+ | npm run test |
| Integration works | Yes | Extension → Backend |

---

## 7. References

- [Sprint 139-141 Plan](../../04-build/02-Sprint-Plans/SPRINT-139-141-SDLC-602-REALITY-CHECK.md)
- [RFC-SDLC-602](../../01-planning/02-RFCs/RFC-SDLC-602-E2E-API-TESTING.md)
- [CLI e2e.py](../../../backend/sdlcctl/sdlcctl/commands/e2e.py)
- [e2e-api-testing Skill](~/.claude/skills/e2e-api-testing/SKILL.md)

---

**Design Status**: ✅ COMPLETE
**Next Step**: Proceed with implementation
**Approved By**: CTO (Sprint 139-141 approval)
