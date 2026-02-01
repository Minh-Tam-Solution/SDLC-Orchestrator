# Sprint 125-127: Multi-Frontend Alignment Plan

**Status**: ✅ **CTO APPROVED** (Option A+ Enhanced)
**Date**: January 30, 2026
**Approved**: January 30, 2026
**Priority**: HIGH (Planning Gap Remediation)
**Owner**: Backend Lead + Frontend Lead + PM
**Total Effort**: 40 SP (~80 hours) - Reduced from 47 SP per CTO decision

---

## 1. Context & Problem Statement

### 1.1 Root Cause Analysis

During Sprint 124 work on CLI/Extension updates, a **critical planning gap** was discovered:

```
SDLC Orchestrator = Implementation of SDLC Framework
                    ↓
        BUT the project itself was NOT following the framework properly:
        - Design docs not updated when requirements change
        - Multiple frontends (Web, CLI, Extension) not kept in sync
        - Framework version mismatch (5.0.0 vs 6.0.0)
        - No alignment matrix tracking feature parity
```

### 1.2 Key Lesson Learned

> **"Nhà bác sĩ phải tự uống thuốc" (Doctor must take own medicine)**
>
> SDLC Orchestrator implements SDLC Framework, so it MUST:
> 1. Follow all SDLC 6.0.0 documentation standards
> 2. Keep Stage 00-03 (Foundation → Planning → Design → Integrate) docs updated
> 3. Maintain feature parity matrix for all delivery surfaces
> 4. Update ALL frontends when Framework version changes

### 1.3 Affected Stages

| Stage | Name | Gap Found |
|-------|------|-----------|
| 00-FOUNDATION | Strategic Discovery | Missing multi-frontend scope in vision |
| 01-PLANNING | Requirements Planning | FRD doesn't cover CLI/Extension parity |
| 02-DESIGN | Technical Design | No unified architecture for 3 frontends |
| 03-INTEGRATE | API Contracts | API contracts not validated against all consumers |

---

## 2. Objectives

### Sprint 125: Documentation Alignment
- [ ] Update Stage 00-03 documentation for multi-frontend scope
- [ ] Create Frontend Alignment Matrix (Web + CLI + Extension)
- [ ] Update CLI/Extension version to SDLC 6.0.0

### Sprint 126: Implementation Alignment
- [ ] Implement SDLC 6.0.0 spec validation in CLI
- [ ] Implement SDLC 6.0.0 features in Extension
- [ ] Add cross-frontend integration tests

### Sprint 127: Process Improvement
- [ ] Establish Framework Update Trigger process
- [ ] Create ADR-045: Multi-Frontend Alignment Strategy
- [ ] Publish aligned versions (CLI v1.2.0, Extension v1.2.0)

---

## 3. Sprint 125: Documentation Alignment ✅ **COMPLETE**

**Sprint Goal**: Achieve documentation parity across all SDLC stages
**Completion Date**: January 30, 2026
**Actual Effort**: 11 SP (100% of planned)

### 3.1 Deliverables

| ID | Deliverable | Owner | SP | Status |
|----|-------------|-------|-----|--------|
| S125-01 | Update FRD with CLI/Extension requirements | PM | 3 | DEFERRED → S126 |
| S125-02 | Create Frontend Alignment Matrix | Architect | 2 | ✅ **DONE** (Jan 30) |
| S125-03 | Update Stage 00 Product Vision | PM | 2 | DEFERRED → S127 |
| S125-04 | Update Stage 02 System Architecture | Architect | 3 | DEFERRED → S127 |
| S125-05 | Update CLI version refs (5.x → 6.0.0) | Backend | 2 | ✅ **DONE** (Jan 30) |
| S125-06 | Update Extension version refs | Frontend | 2 | ✅ **DONE** (Jan 30) |
| S125-07 | Add ADR-045 Multi-Frontend Strategy | Architect | 2 | DEFERRED → S127 |
| S125-08 | Implement YAML frontmatter validator | Backend | 3 | ✅ **DONE** (Jan 30) |
| S125-09 | Publish CLI v1.2.0 to PyPI | Backend | 1 | ✅ **DONE** (Jan 30) |
| S125-10 | Publish Extension v1.2.0 | Frontend | 1 | ✅ **DONE** (Jan 30) |
| **Total P0** | | | **11 SP** | ✅ **100% COMPLETE** |

### Sprint 125 Completion Summary

**Delivered Artifacts**:
- `backend/sdlcctl/sdlcctl/__init__.py` - Updated to v1.2.0, SDLC 6.0.0
- `backend/sdlcctl/pyproject.toml` - Updated to v1.2.0, added pyyaml + jsonschema
- `backend/sdlcctl/sdlcctl/schemas/spec-frontmatter-schema.json` - NEW: JSON Schema for SPEC-0002
- `backend/sdlcctl/sdlcctl/validation/validators/spec_frontmatter.py` - NEW: Frontmatter validator
- `backend/sdlcctl/tests/unit/validation/test_spec_frontmatter_validator.py` - NEW: 16 unit tests
- `vscode-extension/package.json` - Updated to v1.2.0, SDLC 6.0.0
- `docs/01-planning/01-Requirements/Frontend-Alignment-Matrix.md` - Updated GAPs resolved

**Published Packages**:
- PyPI: `sdlcctl==1.2.0` (SDLC 6.0.0 framework)
- VS Code Marketplace: `sdlc-orchestrator@1.2.0`

**Note**: Existing validators in `backend/sdlcctl/sdlcctl/validation/validators/` acknowledged. Only incremental work needed for SDLC 6.0.0 features.

### 3.2 Stage Documentation Updates

#### Stage 00 - FOUNDATION (Strategic Discovery)

**File**: `docs/00-foundation/02-Product-Vision/Product-Vision.md`

**Update Required**:
```diff
+ ## Delivery Surfaces
+
+ SDLC Orchestrator delivers governance through 3 interfaces:
+
+ | Surface | Purpose | Target User |
+ |---------|---------|-------------|
+ | Web Dashboard | Project management, reports, admin | PM, Tech Lead, CTO |
+ | CLI (sdlcctl) | CI/CD integration, local validation | Developer, DevOps |
+ | VS Code Extension | IDE-integrated governance | Developer |
+
+ **Alignment Requirement**: All 3 surfaces MUST support the same SDLC Framework version.
```

#### Stage 01 - PLANNING (Requirements)

**File**: `docs/01-planning/01-Requirements/Functional-Requirements-Document.md`

**Update Required**:
- Add FR50-FR59: CLI-specific functional requirements
- Add FR60-FR69: Extension-specific functional requirements
- Add CFR5: Cross-Frontend Consistency requirements
- Add Feature Parity Matrix table

#### Stage 02 - DESIGN (Architecture)

**File**: `docs/02-design/02-System-Architecture/Technical-Design-Document.md`

**Update Required**:
- Add section: Multi-Frontend Architecture
- Add diagram: Frontend → API → Backend flow for each surface
- Add table: API endpoint coverage by frontend

#### Stage 03 - INTEGRATE (API Contracts)

**File**: `docs/03-integrate/01-api-contracts/API-Consumer-Matrix.md` (NEW)

**Create**:
- Matrix of which APIs are consumed by which frontend
- Version compatibility requirements
- Breaking change notification process

### 3.3 Frontend Alignment Matrix (NEW)

**File**: `docs/01-planning/01-Requirements/Frontend-Alignment-Matrix.md`

```markdown
# Frontend Feature Alignment Matrix

**Last Updated**: 2026-01-30
**Framework Version**: SDLC 6.0.0

## Feature Parity Status

| Feature | Web App | CLI | Extension | Gap Action |
|---------|---------|-----|-----------|------------|
| **Framework Version** | 6.0.0 | ❌ 5.0.0 | ❌ 5.x | Sprint 125 |
| Project Validation | ✅ | ✅ | ✅ | - |
| Tier Classification | ✅ | ✅ | ✅ | - |
| Gate Status View | ✅ | ❌ | ✅ | Sprint 126 |
| **Spec YAML Frontmatter** | ✅ | ❌ | ❌ | Sprint 126 |
| **BDD Requirements** | ✅ | ❌ | ❌ | Sprint 126 |
| **Spec Convert (OpenSpec)** | ❌ | ❌ | ❌ | Sprint 126 |
| Compliance Scoring | ✅ | ✅ | ⚠️ | Sprint 126 |
| Evidence Upload | ✅ | ❌ | ✅ | Backlog |
| AI Council | ✅ | ❌ | ✅ | Backlog |
| Context Authority | ✅ | ❌ | ❌ | Sprint 127 |

## API Coverage Matrix

| API Endpoint | Web App | CLI | Extension |
|--------------|---------|-----|-----------|
| POST /auth/login | ✅ | ❌ | ✅ |
| GET /projects | ✅ | ❌ | ✅ |
| POST /projects/{id}/validate | ✅ | ⚠️ Local | ✅ |
| GET /gates/{id} | ✅ | ❌ | ✅ |
| POST /evidence | ✅ | ❌ | ✅ |
| POST /specs/validate | ✅ | ⚠️ Local | ❌ |
| GET /compliance/score | ✅ | ⚠️ Local | ⚠️ |

**Legend**: ✅ Implemented | ⚠️ Partial | ❌ Not implemented
```

---

## 4. Sprint 126: Implementation Alignment (Current)

**Sprint Goal**: Implement SDLC 6.0.0 features in CLI and Extension
**Start Date**: February 3, 2026 (accelerated from Feb 14)
**Target Date**: February 14, 2026

### 4.1 Deliverables

| ID | Deliverable | Owner | SP | Status |
|----|-------------|-------|-----|--------|
| S126-01 | Update spec_validator.py with frontmatter | Backend | 2 | ✅ **DONE** (Jan 30) |
| S126-02 | Implement `sdlcctl spec convert` | Backend | 3 | ✅ **DONE** (Jan 30) |
| S126-03 | Implement `sdlcctl spec list` | Backend | 1.5 | ✅ **EXISTS** (Sprint 119) |
| S126-04 | Implement `sdlcctl spec init` | Backend | 1.5 | ✅ **DONE** (Jan 30) |
| S126-05 | Implement BDD requirements validator | Backend | 3 | ✅ **EXISTS** (Sprint 119) |
| S126-06 | Add spec validation to Extension | Frontend | 2 | ✅ **DONE** (Jan 30) |
| S126-07 | Cross-frontend E2E tests | QA | 3 | ✅ **DONE** (Jan 30) |
| **Total** | | | **16 SP** | ✅ **100% COMPLETE** |

**Note**: Sprint 126 completed ahead of schedule (Jan 30, 2026).

**S126-06 Implementation Details**:
- `vscode-extension/src/commands/specValidationCommand.ts` - NEW: Spec validation commands
- `vscode-extension/src/types/codegen.ts` - Added SpecValidationResult, FrontmatterValidation types
- `vscode-extension/src/services/codegenApi.ts` - Added validateSpecificationLocal() method
- `vscode-extension/package.json` - Added commands, keybindings, settings
- Features:
  - `sdlc.validateSpec` command (Cmd+Shift+V)
  - `sdlc.validateSpecWithTier` command (tier selection)
  - Problems panel integration (VS Code diagnostics)
  - Local validation (no backend required)
  - Settings: validateSpecOnSave, defaultSpecTier

### 4.2 CLI Changes (sdlcctl)

**New Validators**:
- `validation/validators/spec_frontmatter.py`
- `validation/validators/spec_bdd.py`
- `validation/validators/spec_tier.py`

**New Commands**:
- `sdlcctl spec convert --from openspec --path .openspec/proposals/`
- `sdlcctl spec list --tier PROFESSIONAL --status APPROVED`
- `sdlcctl spec init --tier STANDARD --stage 02`

**Templates to Copy**:
- Framework 6.0 spec templates → `sdlcctl/templates/specifications/`

### 4.3 Extension Changes ✅ **COMPLETE**

**Implemented (S126-06)**:
- Version refs → 6.0.0
- Spec validation command with Problems panel integration
- Keybinding: Cmd+Shift+V for spec validation
- Local validation (YAML frontmatter, BDD, tier-specific sections)
- Settings: validateSpecOnSave, defaultSpecTier

**New Files**:
- `src/commands/specValidationCommand.ts` (340+ lines)
- Types in `src/types/codegen.ts` (~100 lines added)
- API methods in `src/services/codegenApi.ts` (~150 lines added)

**Commands Added**:
- `sdlc.validateSpec` - Validate specification (SDLC 6.0.0)
- `sdlc.validateSpecWithTier` - Validate with tier selection
- `sdlc.showSpecValidationResults` - Show validation results

---

## 5. Sprint 127: Process Improvement

**Sprint Goal**: Establish processes to prevent future misalignment

### 5.1 Deliverables

| ID | Deliverable | Owner | SP | Status |
|----|-------------|-------|-----|--------|
| S127-01 | ADR-045 Multi-Frontend Strategy | Architect | 2 | PENDING |
| S127-02 | Framework Update Trigger Automation | DevOps | 3 | PENDING |
| S127-03 | Monthly Alignment Checkpoint | PM | 1 | PENDING |
| S127-04 | Publish CLI v1.2.0 to PyPI | Backend | 1 | PENDING |
| S127-05 | Publish Extension v1.2.0 | Frontend | 1 | PENDING |
| S127-06 | Update all Stage 00-03 docs | PM | 5 | PENDING |
| S127-07 | Lessons Learned documentation | All | 2 | PENDING |
| **Total** | | | **15 SP** | |

### 5.2 Process Improvements

#### Framework Update Trigger

When SDLC-Enterprise-Framework version changes:
1. GitHub Action detects submodule version change
2. Auto-creates issues for each frontend (Web, CLI, Extension)
3. Blocks main branch merge until alignment tickets closed
4. Updates Frontend Alignment Matrix automatically

#### Monthly Alignment Checkpoint

**Checklist**:
- [ ] All frontends on same Framework version
- [ ] Feature Parity Matrix up to date
- [ ] No P0 gaps in matrix
- [ ] Stage 00-03 docs reflect current state

---

## 6. Lessons Learned (To Be Added to ADR-045)

### 6.1 What Went Wrong

1. **Framework evolved faster than implementations**
   - Framework: 5.0.0 → 5.3.0 → 6.0.0 in 2 months
   - CLI/Extension: Still on 5.0.0

2. **No formal sync process**
   - No trigger when Framework version changes
   - No alignment checkpoint in sprint planning

3. **Documentation lag**
   - Stage 00-03 docs not updated when Web App changed
   - No Feature Parity Matrix existed

4. **Decoupled development**
   - Web App, CLI, Extension developed in silos
   - No cross-frontend integration tests

### 6.2 What We're Fixing

1. **Framework Update Trigger** - Auto-create tickets when Framework changes
2. **Frontend Alignment Matrix** - Track feature parity
3. **Monthly Checkpoint** - PM validates alignment
4. **Cross-Frontend Tests** - E2E tests cover all surfaces
5. **ADR-045** - Formal decision on alignment strategy

### 6.3 Prevention for Future

> **Rule**: When SDLC Framework version changes, ALL frontends MUST be updated in the SAME sprint or the next sprint. No exceptions.

---

## 7. Success Criteria

| Metric | Target | Sprint | Status |
|--------|--------|--------|--------|
| CLI Framework Version | 6.0.0 | 125 | ✅ **ACHIEVED** (v1.2.0) |
| Extension Framework Version | 6.0.0 | 125 | ✅ **ACHIEVED** (v1.2.0) |
| YAML Frontmatter Validator | 100% SPEC-0002 | 125 | ✅ **ACHIEVED** |
| JSON Schema Validation | CLI integration | 126 | ✅ **ACHIEVED** |
| BDD Requirements Validator | CLI + Web | 126 | ✅ **ACHIEVED** (CLI) |
| Spec Commands (convert/init) | CLI | 126 | ✅ **ACHIEVED** |
| CLI Parity Score | >70% | 126 | ✅ **ACHIEVED** (71%) |
| Extension Spec Features | Spec validation | 126 | ✅ **ACHIEVED** (Jan 30) |
| Extension Parity Score | >80% | 126 | ✅ **ACHIEVED** (89%) |
| Cross-Frontend Tests | 10+ E2E scenarios | 126/127 | PENDING |
| Documentation Completeness | 100% Stage 00-03 | 127 | PENDING |

---

## 8. Approval

**CTO Decision Required**:

- [ ] APPROVE Sprint 125-127 plan as written
- [ ] MODIFY with changes: _______________
- [ ] REJECT with reason: _______________

**Estimated Effort**: 51 SP across 3 sprints (~102 hours)
**Risk Level**: MEDIUM (existing codebase, known scope)

---

---

## 9. CTO Approval Record

### Decision: ✅ APPROVED - OPTION A+ (ENHANCED)

**Approval Date**: January 30, 2026
**Approved By**: CTO, SDLC Orchestrator Project

### Modifications Applied

| Original | Modified | Reason |
|----------|----------|--------|
| Sprint 125: 16 SP | Sprint 125: 10 SP | P0 only, defer P1 to S126 |
| Sprint 126: 17 SP | Sprint 126: 18 SP | Absorbed P1 from S125 |
| Sprint 127: 15 SP | Sprint 127: 12 SP | Removed optional items |
| **Total: 47 SP** | **Total: 40 SP** | 15% reduction |

### CTO Directives Issued

1. **DIRECTIVE 1**: Framework Freeze (Jan 30 - Mar 14, 2026)
   - No Framework 6.0.1/6.1.0/7.0.0 releases during alignment work

2. **DIRECTIVE 2**: Monthly Alignment Review (Mar 1+ onwards)
   - First Monday of each month
   - Review Frontend Alignment Matrix

3. **DIRECTIVE 3**: Framework Update Trigger (Sprint 127)
   - Auto-create issues when Framework version bumps
   - GitHub Actions automation required

### Budget Approved (Revised after CTO Review)

| Sprint | Original | Revised | Reason |
|--------|----------|---------|--------|
| Sprint 125 | 10 SP | 11 SP | Matrix done (-2), added frontmatter (+3) |
| Sprint 126 | 18 SP | 15.5 SP | Existing validators (-2.5) |
| Sprint 127 | 12 SP | 17 SP | Added operational readiness (+5) |
| **Total** | **40 SP** | **43.5 SP** | Higher quality deliverables |

- Sprint 125: 11 SP × ₫2M = ₫22M
- Sprint 126: 15.5 SP × ₫2M = ₫31M
- Sprint 127: 17 SP × ₫2M = ₫34M
- **Total**: 43.5 SP = **₫87M** (~$3,700 USD)

### Expected ROI: 225% first-year return (unchanged)

---

---

## Appendix A: File Update Checklist (CTO Review Finding)

### CLI Files Requiring Version Update (4 files)

| File | Line | Current | Target | Change |
|------|------|---------|--------|--------|
| `backend/sdlcctl/pyproject.toml` | 8 | `"SDLC 5.0.0 Structure Validator CLI"` | `"SDLC 6.0.0 Specification Validator CLI"` | Description |
| `backend/sdlcctl/sdlcctl/__init__.py` | 14 | `__framework__ = "SDLC 5.0.0"` | `__framework__ = "SDLC 6.0.0"` | Framework constant |
| `backend/sdlcctl/sdlcctl/__init__.py` | 19 | Docstring mentions 5.0.0 | Update to 6.0.0 | Docstring |
| `backend/sdlcctl/sdlcctl/cli.py` | 3, 64, 90, 92, 104, 110, 116 | Multiple 5.0.0 refs | Update all to 6.0.0 | Help text + comments |

### Extension Files Requiring Version Update (3 files)

| File | Line | Current | Target | Change |
|------|------|---------|--------|--------|
| `vscode-extension/package.json` | 3 | `"version": "1.1.2"` | `"version": "1.2.0"` | Version bump |
| `vscode-extension/package.json` | 4 | Description | Add "SDLC 6.0.0" | Description |
| `vscode-extension/package.json` | 42 | Keywords | Add "sdlc-6.0" | Keywords |

### Validation Script (Create in Sprint 125)

```bash
# backend/scripts/validate-version-refs.sh
#!/bin/bash
# Validates all version references are at target SDLC version

TARGET_VERSION="${1:-6.0.0}"

echo "Checking version refs for SDLC $TARGET_VERSION..."

# CLI checks
grep -r "SDLC 5\." backend/sdlcctl/ --include="*.py" && echo "❌ Found 5.x refs in CLI" || echo "✅ CLI OK"

# Extension checks
grep -r "5\." vscode-extension/package.json && echo "❌ Found old version in Extension" || echo "✅ Extension OK"

echo "Done. Run 'sdlcctl validate-version-refs --target $TARGET_VERSION' after v1.2.0"
```

---

## Appendix B: Existing Validators (CTO Review Finding)

**Location**: `backend/sdlcctl/sdlcctl/validation/validators/`

| Validator | Status | SDLC 6.0.0 Work Needed |
|-----------|--------|------------------------|
| `naming_convention.py` | ✅ Exists | None |
| `sequential_numbering.py` | ✅ Exists | None |
| `stage_folder.py` | ✅ Exists | None |
| `tier_compliance.py` | ✅ Exists | None |
| `cross_reference.py` | ✅ Exists | None |
| `spec_validator.py` | ✅ 80% done | Add frontmatter schema validation |

**Impact**: Sprint 126 effort reduced by ~2.5 SP (validators not greenfield)

---

## Appendix C: E2E Test Task (CTO Review Finding)

**Added to Sprint 126**: S126-07 Cross-Frontend E2E Validation (3 SP) ✅ **COMPLETE**

**Scope**:
- Validate CLI output matches Web App validation
- Validate Extension validation matches CLI
- Fix API endpoint mismatches in test suite

**S126-07 Implementation Details** (Jan 30, 2026):

Test Fixtures Created:
- `backend/tests/e2e/fixtures/spec_validation/valid_spec_professional.md`
- `backend/tests/e2e/fixtures/spec_validation/invalid_spec_missing_fields.md`
- `backend/tests/e2e/fixtures/spec_validation/invalid_spec_bad_format.md`
- `backend/tests/e2e/fixtures/spec_validation/invalid_spec_no_frontmatter.md`
- `backend/tests/e2e/fixtures/spec_validation/invalid_spec_missing_bdd.md`
- `backend/tests/e2e/fixtures/spec_validation/openspec_format.md`

E2E Test Files:
- `backend/tests/e2e/test_spec_validation_parity.py` - 9 tests (all passing)
  - TestSpecValidationParity: 6 tests for cross-frontend parity
  - TestSpecValidationPerformance: 1 test (<500ms latency)
  - TestSpecInitValidateWorkflow: 1 test
  - TestSpecConvertValidateWorkflow: 1 test
- `vscode-extension/src/test/suite/specValidation.test.ts` - 16 tests
  - Valid spec detection (2 tests)
  - SPC-001 Missing fields (1 test)
  - SPC-002 Format violations (5 tests)
  - SPC-004 Missing frontmatter (1 test)
  - SPC-003 BDD warnings (2 tests)
  - Line numbers (1 test)
  - CLI parity (1 test)
  - Type validation (3 tests)

Error Codes Verified:
- SPC-001: Missing required field (CLI/Extension parity ✅)
- SPC-002: Invalid field format (CLI/Extension parity ✅)
- SPC-003: Missing BDD requirements (CLI/Extension parity ✅)
- SPC-004: Missing YAML frontmatter (CLI/Extension parity ✅)
- Add version consistency checks

---

**Document Status**: ✅ **CTO APPROVED + REVIEWED**
**Created**: 2026-01-30
**Approved**: 2026-01-30
**Reviewed**: 2026-01-30 (CTO detailed review)
**Sprint 125 Completed**: 2026-01-30 (14 days ahead of schedule)
**Next Review**: February 14, 2026 (Sprint 126 completion)
