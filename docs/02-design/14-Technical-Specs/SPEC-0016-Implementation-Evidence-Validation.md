# SPEC-0016: Implementation Evidence Validation

**Version**: 1.0.0
**Date**: February 1, 2026
**Status**: IMPLEMENTED
**Sprint**: Sprint 132 - Go-Live Preparation
**Author**: Backend Team
**Approver**: CTO

---

## Problem Statement

### Context Drift Discovery

During Sprint 132 go-live audit, SDLC Orchestrator itself exhibited **context drift**:

```
Sprint 125-129: Multi-Frontend Alignment
├── Backend APIs: 100% complete ✓
│   ├── Team Invitations (540 LOC, 7 endpoints)
│   └── GitHub Integration (978 LOC, 8 endpoints)
├── Web Frontend: 0% complete ✗
│   ├── Team Invitation UI: Missing
│   └── GitHub Integration UI: Missing
└── VSCode Extension: Partial
    ├── Auto-detect project: 100% complete ✓
    └── GitHub commands: Missing source code
```

**Root Cause**: No automated validation that implementation matches approved design (SPEC/ADR).

### The Irony

SDLC Orchestrator was built to **prevent context drift** in other projects, yet suffered from it:
- Detailed planning (ADR-043, ADR-044, Sprint Plans)
- Backend implementation complete
- Frontend implementation forgotten
- No automation caught this before launch

### Existing Evidence Vault Limitations

SDLC Orchestrator has Evidence Vault since Sprint 10:
- **Evidence Upload**: ✓ Works (MinIO S3 storage)
- **Evidence Retrieval**: ✓ Works (SHA256 integrity)
- **Evidence Lifecycle**: ✓ Works (8 states)
- **Validation**: ✗ **MISSING** (no spec-to-code checking)
- **Gate Integration**: ✗ **MISSING** (no blocking mechanism)
- **Enforcement**: ✗ **MISSING** (gates pass without evidence)

**Quote from User**: "ngay từ ban đầu SDLC Orchestrator đã có Evidence Vault, nhưng chúng ta thiếu cơ chế kiểm tra, kiểm soát, cũng như ràng buộc các gates" (from the beginning SDLC Orchestrator had Evidence Vault, but we lack checking mechanisms, control, and gate constraints)

---

## Solution: Evidence-Based Validation

### Core Concept

For each SPEC or ADR, require an **evidence file** proving implementation across all interfaces:

```
docs/02-design/14-Technical-Specs/
├── SPEC-0013-Compliance-Validation-Service.md
├── SPEC-0013-evidence.json  ⭐ NEW - Proof of implementation
├── ADR-043-Team-Invitation-System-Architecture.md
└── ADR-043-evidence.json  ⭐ NEW - Proof of implementation
```

Evidence file structure:

```json
{
  "spec_id": "SPEC-0013",
  "spec_title": "Compliance Validation Service",
  "spec_type": "feature",
  "implementation_date": "2026-01-15",
  "sprint": "Sprint 123",
  "interfaces": {
    "backend": {
      "api_routes": ["backend/app/api/routes/compliance_validation.py"],
      "services": ["backend/app/services/validation/compliance_validator.py"],
      "models": ["backend/app/models/compliance_validation.py"],
      "schemas": ["backend/app/schemas/compliance.py"],
      "tests": ["backend/tests/services/test_compliance_validation.py"],
      "migrations": ["backend/alembic/versions/s123_001_compliance_validation.py"]
    },
    "frontend": {
      "components": ["frontend/src/components/compliance/ValidationPanel.tsx"],
      "pages": ["frontend/src/app/compliance/page.tsx"],
      "hooks": ["frontend/src/hooks/useCompliance.ts"],
      "api_client": ["frontend/src/lib/api.ts"],
      "tests": ["frontend/src/components/compliance/ValidationPanel.test.tsx"]
    },
    "extension": {
      "commands": ["vscode-extension/src/commands/validateComplianceCommand.ts"],
      "services": ["vscode-extension/src/services/complianceService.ts"],
      "views": ["vscode-extension/src/views/compliancePanel.ts"],
      "package_json": ["vscode-extension/package.json"],
      "tests": ["vscode-extension/src/test/suite/compliance.test.ts"]
    },
    "cli": {
      "commands": ["backend/sdlcctl/sdlcctl/commands/compliance.py"],
      "services": ["backend/sdlcctl/sdlcctl/services/compliance_service.py"],
      "tests": ["backend/sdlcctl/tests/test_compliance.py"]
    }
  },
  "documentation": {
    "user_guide": ["docs/05-test/user-guide/compliance-validation.md"],
    "api_docs": ["docs/01-planning/05-API-Design/Compliance-API-Spec.md"],
    "runbooks": ["docs/06-deploy/runbooks/compliance-troubleshooting.md"]
  },
  "validation": {
    "last_checked": "2026-02-01T10:30:00Z",
    "checker_version": "1.0.0",
    "status": "complete",
    "missing_files": [],
    "warnings": []
  }
}
```

---

## Implementation

### 1. JSON Schema (`spec-evidence-schema.json`)

**Location**: `backend/sdlcctl/sdlcctl/schemas/spec-evidence-schema.json`

**Purpose**: Define structure for evidence files

**Features**:
- Required fields: `spec_id`, `spec_title`, `spec_type`, `implementation_date`, `interfaces`
- Validation patterns: File paths must match conventions (e.g., `^backend/app/api/routes/.*\\.py$`)
- Mandatory tests: Backend tests are REQUIRED
- Flexible interfaces: Frontend/Extension/CLI optional (if SPEC doesn't require them)

### 2. Evidence Validator (`evidence_validator.py`)

**Location**: `backend/sdlcctl/sdlcctl/validation/validators/evidence_validator.py`

**Core Validation Functions**:

```python
class EvidenceValidator(BaseValidator):
    def validate(self) -> List[Violation]:
        """Main validation entry point"""

    def _validate_evidence_file(self, evidence_file: Path) -> List[Violation]:
        """Validate single evidence file"""

    def _validate_schema(self, evidence_data: dict) -> List[Violation]:
        """Validate against JSON schema"""

    def _validate_file_existence(self, evidence_data: dict) -> List[Violation]:
        """Check all referenced files exist on disk"""

    def _validate_test_coverage(self, evidence_data: dict) -> List[Violation]:
        """Check test coverage requirements"""

    def _check_missing_evidence(self) -> List[Violation]:
        """Find SPECs/ADRs without evidence files"""
```

**Violation Rules**:
- `EVIDENCE-001`: No evidence files found in project
- `EVIDENCE-002`: Invalid JSON syntax
- `EVIDENCE-003`: Failed to validate file
- `EVIDENCE-004`: Evidence schema not loaded
- `EVIDENCE-005`: Schema validation failed
- `EVIDENCE-006`: Backend file not found
- `EVIDENCE-007`: Frontend file not found
- `EVIDENCE-008`: Extension file not found
- `EVIDENCE-009`: CLI file not found
- `EVIDENCE-010`: Backend tests missing (ERROR)
- `EVIDENCE-011`: Frontend tests missing (WARNING)
- `EVIDENCE-012`: Extension tests missing (WARNING)
- `EVIDENCE-013`: CLI tests missing (WARNING)
- `EVIDENCE-014`: Missing evidence file for SPEC/ADR

### 3. CLI Commands (`evidence.py`)

**Location**: `backend/sdlcctl/sdlcctl/commands/evidence.py`

**Commands**:

#### `sdlcctl evidence validate`

Validate all evidence files in project:

```bash
# Basic validation
sdlcctl evidence validate

# Fail on errors (for CI/CD)
sdlcctl evidence validate --fail-on-error

# Output JSON report
sdlcctl evidence validate --output gaps.json
```

**Output**:
```
SDLC Evidence Validator
Project: /home/nqh/shared/SDLC-Orchestrator

Validation Summary
─────────────────────────────────
Metric               Value
─────────────────────────────────
Total Violations      15
Errors                 3
Warnings              12
─────────────────────────────────

Violations
─────────────────────────────────────────────────────────────
Severity   Rule             File                             Message
─────────────────────────────────────────────────────────────
ERROR      EVIDENCE-007     ADR-043-evidence.json            Frontend components file not found
ERROR      EVIDENCE-007     ADR-044-evidence.json            Frontend pages file not found
WARNING    EVIDENCE-014     SPEC-0013.md                     Missing evidence file
...
```

#### `sdlcctl evidence create`

Create evidence file template:

```bash
sdlcctl evidence create SPEC-0013 --title "Compliance Validation Service"
sdlcctl evidence create ADR-043 --title "Team Invitation System" --sprint "Sprint 128"
```

**Output**: Creates JSON template with empty arrays for population.

#### `sdlcctl evidence check`

Check spec-to-code alignment and generate gap report:

```bash
sdlcctl evidence check
sdlcctl evidence check --output gaps.md
```

**Output**: Markdown report categorizing gaps:
- Missing evidence files
- Backend gaps
- Frontend gaps
- Extension gaps
- CLI gaps
- Test coverage gaps

---

## Integration with Evidence Vault & Gates

### Current State (Before SPEC-0016)

```
┌─────────────────────┐
│  Evidence Vault     │
│  ├── upload()       │ ✓ Works
│  ├── retrieve()     │ ✓ Works
│  ├── lifecycle()    │ ✓ Works
│  └── validate()?    │ ✗ Missing
└─────────────────────┘
         ↓ (weak link)
┌─────────────────────┐
│  Gate Engine        │
│  ├── evaluate()     │ ✓ Works (OPA)
│  ├── block_merge()  │ ✓ Works
│  └── require_evidence()? │ ✗ Missing (gates pass without evidence!)
└─────────────────────┘
```

**Problem**: Gates can pass even when implementation incomplete.

### Enhanced State (After SPEC-0016)

```
┌─────────────────────┐
│  Evidence Vault     │
│  ├── upload()       │ ✓ Works
│  ├── retrieve()     │ ✓ Works
│  ├── lifecycle()    │ ✓ Works
│  └── validate()     │ ⭐ NEW (SPEC-0016)
└─────────────────────┘
         ↓ (strong link)
┌─────────────────────┐
│ Evidence Validator  │ ⭐ NEW (SPEC-0016)
│  ├── schema check   │
│  ├── file existence │
│  ├── test coverage  │
│  └── gap analysis   │
└─────────────────────┘
         ↓ (enforcement)
┌─────────────────────┐
│  Gate Engine        │
│  ├── evaluate()     │ ✓ Works (OPA)
│  ├── block_merge()  │ ✓ Works
│  └── require_evidence() │ ⭐ ENHANCED (OPA policy)
└─────────────────────┘
```

### OPA Policy Enhancement (Sprint 133)

**New Policy**: `evidence_completeness.rego`

```rego
package gates.evidence

# Gate G3 (Ship Ready) requires 100% evidence
deny[msg] {
    input.gate_code == "G3"
    missing_evidence := evidence_validator.check_gaps(input.project_id)
    count(missing_evidence.frontend_gaps) > 0
    msg := sprintf("G3 BLOCKED: %d frontend components missing", [count(missing_evidence.frontend_gaps)])
}

# Gate G4 (Internal Validation) requires tests
deny[msg] {
    input.gate_code == "G4"
    missing_tests := evidence_validator.check_test_coverage(input.project_id)
    missing_tests.backend_tests_missing == true
    msg := "G4 BLOCKED: Backend tests required"
}

# Allow gates if evidence complete
allow {
    evidence_validator.status(input.project_id) == "complete"
}
```

**Implementation Steps** (Sprint 133):
1. Add `evidence_validator` API endpoint: `GET /api/v1/projects/{id}/evidence/status`
2. OPA policy calls this endpoint during gate evaluation
3. Gate evaluation FAILS if evidence incomplete
4. Frontend shows specific missing files in gate status

---

## Workflow Integration

### Developer Workflow (Enhanced)

```
1. SPEC/ADR Approved
   ↓
2. Create evidence template:
   sdlcctl evidence create SPEC-00XX --title "Feature Name"
   ↓
3. Implement backend
   → Update evidence.json with file paths
   ↓
4. Implement frontend
   → Update evidence.json with file paths
   ↓
5. Validate evidence:
   sdlcctl evidence validate --fail-on-error
   ↓
6. Fix gaps (if any)
   ↓
7. Commit evidence.json with implementation
   ↓
8. Pre-commit hook validates evidence ⭐ NEW
   ↓
9. CI/CD validates evidence ⭐ NEW
   ↓
10. Gate evaluation checks evidence ⭐ NEW (Sprint 133)
```

### Pre-commit Hook Integration

**File**: `.pre-commit-config.yaml` (to be added)

```yaml
repos:
  - repo: local
    hooks:
      - id: evidence-validation
        name: SDLC Evidence Validation
        entry: sdlcctl evidence validate --fail-on-error
        language: system
        pass_filenames: false
        files: '.*-evidence\.json$'
```

### CI/CD Integration

**File**: `.github/workflows/evidence-check.yml` (to be added)

```yaml
name: Evidence Validation

on:
  pull_request:
    paths:
      - 'docs/**/*-evidence.json'
      - 'backend/**/*.py'
      - 'frontend/**/*.tsx'
      - 'vscode-extension/**/*.ts'

jobs:
  validate-evidence:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Install sdlcctl
        run: pip install -e backend/sdlcctl

      - name: Validate Evidence
        run: sdlcctl evidence validate --fail-on-error --output gaps.json

      - name: Upload Gap Report
        if: failure()
        uses: actions/upload-artifact@v3
        with:
          name: evidence-gaps
          path: gaps.json
```

---

## Success Metrics

### Adoption Metrics (Sprint 132-133)

| Metric | Target | Measurement |
|--------|--------|-------------|
| Evidence files created | 15+ | Count `*-evidence.json` files |
| Validation coverage | 100% | All SPECs/ADRs have evidence |
| CI/CD integration | 100% | Pre-commit + GitHub Actions enabled |
| Gate blocking accuracy | 95%+ | Gates correctly block incomplete evidence |

### Quality Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| False positives | <5% | Valid implementations flagged as missing |
| False negatives | 0% | Missing implementations not detected |
| Validation speed | <10s | Time to validate 1000+ files |

### Context Drift Prevention

**Before SPEC-0016**:
- Sprint 128-129 Backend 100% → Frontend 0% (undetected)

**After SPEC-0016**:
- Evidence validation catches gaps before merge
- Pre-commit hook prevents incomplete commits
- Gates block promotion without evidence

**Expected Reduction**: Context drift incidents from 1-2 per sprint → 0 per quarter

---

## Implementation Status

### Sprint 132 (February 1, 2026) - COMPLETED

✅ **JSON Schema** (`spec-evidence-schema.json`)
- 350 lines of validation rules
- Supports 4 interfaces (backend, frontend, extension, CLI)
- Mandatory test coverage for backend

✅ **Evidence Validator** (`evidence_validator.py`)
- 450 lines of validation logic
- 14 violation rules
- Automatic metadata updates

✅ **CLI Commands** (`evidence.py`)
- 400 lines of CLI implementation
- 3 commands: `validate`, `create`, `check`
- Rich terminal output (tables, colors)

✅ **CLI Integration** (`cli.py`)
- Registered `evidence` sub-app
- Available globally as `sdlcctl evidence`

### Sprint 133 (Planned) - Evidence Vault + Gates Integration

⏳ **OPA Policy** (`evidence_completeness.rego`)
- Gate G3/G4 evidence requirements
- API endpoint for evidence status

⏳ **Pre-commit Hook**
- Block commits with invalid evidence
- Auto-fix validation metadata

⏳ **CI/CD Workflow**
- GitHub Actions evidence check
- PR comments with gap report

⏳ **Dogfooding**
- Create evidence for all 15 existing SPECs
- Catch Sprint 128-129 frontend gaps
- Validate before go-live

---

## Risks & Mitigations

### Risk 1: Developer Friction

**Risk**: Developers may resist creating evidence files (extra work)

**Mitigation**:
- Auto-generate evidence templates (`sdlcctl evidence create`)
- Pre-populate from existing code (scan imports/exports)
- Make evidence creation part of SPEC approval workflow

### Risk 2: Schema Rigidity

**Risk**: JSON schema too strict, rejects valid implementations

**Mitigation**:
- Allow flexible interfaces (frontend optional if SPEC doesn't require UI)
- Support custom file patterns via `notes` field
- Version schema (1.0.0 → 2.0.0 as needs evolve)

### Risk 3: Validation Performance

**Risk**: Validation slow for large projects (1000+ files)

**Mitigation**:
- Cache validation results (only re-validate changed evidence)
- Parallel file existence checks
- Incremental validation (only validate modified evidence)

### Risk 4: False Positives

**Risk**: Validator flags correct implementations as missing

**Mitigation**:
- Comprehensive pattern matching (support multiple file patterns)
- Manual override via `validation.warnings` field
- Continuous improvement based on feedback

---

## Related Documents

- **ADR-043**: Team Invitation System Architecture (evidence: missing frontend)
- **ADR-044**: GitHub Integration Strategy (evidence: missing frontend)
- **SPEC-0013**: Compliance Validation Service (evidence: complete)
- **SPEC-0014**: CLI Extension SDLC 6.0.0 Upgrade (evidence: partial)
- **CURRENT-SPRINT.md**: Sprint 132 Go-Live Preparation

---

## Appendix A: Evidence File Template

```json
{
  "spec_id": "SPEC-00XX",
  "spec_title": "Feature Name",
  "spec_type": "feature",
  "implementation_date": "2026-02-01",
  "sprint": "Sprint XXX",
  "interfaces": {
    "backend": {
      "api_routes": [],
      "services": [],
      "models": [],
      "schemas": [],
      "tests": [],
      "migrations": []
    },
    "frontend": {
      "components": [],
      "pages": [],
      "hooks": [],
      "api_client": [],
      "tests": []
    },
    "extension": {
      "commands": [],
      "services": [],
      "views": [],
      "package_json": [],
      "tests": []
    },
    "cli": {
      "commands": [],
      "services": [],
      "tests": []
    }
  },
  "documentation": {
    "user_guide": [],
    "api_docs": [],
    "runbooks": []
  },
  "validation": {
    "last_checked": "2026-02-01T00:00:00Z",
    "checker_version": "1.0.0",
    "status": "missing",
    "missing_files": [],
    "warnings": ["Template created - populate with actual implementation files"]
  },
  "notes": "TODO: Fill in actual implementation file paths"
}
```

---

**Status**: IMPLEMENTED (Sprint 132)
**Next Steps**: Sprint 133 - OPA integration, pre-commit hook, dogfooding
**Owner**: Backend Team
**Approver**: CTO
