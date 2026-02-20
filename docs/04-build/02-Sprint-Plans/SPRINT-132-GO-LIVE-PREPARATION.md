---
sdlc_version: "6.0.6"
document_type: "Sprint Plan"
stage: "04 - BUILD"
sprint: "132"
status: "ACTIVE"
owner: "CTO"
last_updated: "2026-01-31"
context_zone: "Dynamic"
update_frequency: "Daily"
---

# Sprint 132: Go-Live Preparation

**Sprint Duration**: January 31 - February 1, 2026 (1 day critical path)
**Sprint Goal**: Resolve all P0 blockers for production launch
**Framework**: SDLC 6.1.0
**Authority**: CTO APPROVED (Jan 31, 2026, 10:45 AM)

---

## Executive Summary

### Sprint Context

**Pre-condition**: Sprint 131 (Documentation Compliance) completed
**Post-condition**: All P0 blockers resolved, 95%+ confidence for launch
**Critical Path**: 7.5 hours total

### Go-Live Readiness

| Metric | Before Sprint 132 | Target | Status |
|--------|-------------------|--------|--------|
| Launch Confidence | 88.2% | 95%+ | ⏳ |
| Test Collection Errors | 7 | 0 | ⏳ |
| P0 TODOs | 21 (estimated) | 0 | ⏳ |
| sdlcctl CLI | BROKEN | WORKING | ⏳ |
| Extension Auth | ERROR | DEBUGGED | ⏳ |

---

## Sprint Backlog

### Task 1: Fix sdlcctl CLI Import Error
**Priority**: P0 - CRITICAL
**Owner**: DevOps Lead
**Estimate**: 10 minutes
**Status**: IN_PROGRESS

**Given** the sdlcctl CLI is broken with ModuleNotFoundError
**When** we reinstall the package in editable mode
**Then** `sdlcctl --version` should return version 1.2.0 without errors

**Root Cause**:
```
OLD: backend/sdlcctl/cli.py (deleted)
NEW: backend/sdlcctl/sdlcctl/cli.py (current location)
Entry point in pyproject.toml:50 expects old location
```

**Fix Command**:
```bash
cd /home/nqh/shared/SDLC-Orchestrator/backend/sdlcctl
pip install -e .
sdlcctl --version  # Verify
```

**Acceptance Criteria**:
- [ ] `sdlcctl --version` returns `1.2.0`
- [ ] `sdlcctl validate --help` shows help text
- [ ] No ImportError or ModuleNotFoundError

---

### Task 2: Debug Extension Authentication
**Priority**: P0 - HIGH
**Owner**: Frontend Lead
**Estimate**: 15 minutes
**Status**: PENDING

**Given** Extension shows "Error loading context overlay"
**When** we verify authentication token flow
**Then** either auth works OR we document expected behavior for unregistered projects

**Investigation Steps**:
1. Re-login via Extension: `Cmd+Shift+P` → "SDLC: Login"
2. Complete GitHub OAuth flow
3. Check Extension logs: View → Output → "SDLC Orchestrator"
4. Look for: `[INFO] Access token stored successfully`

**Test API**:
```bash
TOKEN="<from-extension-storage>"
curl -H "Authorization: Bearer $TOKEN" \
  https://sdlc.nhatquangholding.com/api/v1/projects
```

**Acceptance Criteria**:
- [ ] Auth token stored after login
- [ ] Context overlay loads without error
- [ ] OR documented as expected for unregistered projects

---

### Task 3: Fix Test Collection Errors
**Priority**: P0 - BLOCKING
**Owner**: Backend Lead + QA Lead
**Estimate**: 2 hours
**Status**: PENDING

**Given** 7 test files fail to collect
**When** we identify and fix import errors
**Then** `pytest --collect-only -q` shows 0 errors and 3,867+ tests

**Affected Files**:
1. `tests/services/test_codegen_service.py`
2. `tests/services/test_gate_service.py`
3. `tests/services/test_policy_service.py`
4. `tests/services/test_project_service.py`
5. `tests/services/test_user_service.py`
6. `tests/unit/test_ai_detection_accuracy.py`
7. `tests/unit/test_github_app_service.py`

**Diagnostic Commands**:
```bash
cd /home/nqh/shared/SDLC-Orchestrator/backend
PYTHONPATH=$PWD:$PYTHONPATH pytest tests/services/test_codegen_service.py --collect-only -vv 2>&1 | tail -50
# Repeat for each file
```

**Common Root Causes**:
- Missing factory functions in service files
- Circular imports between modules
- Missing `__init__.py` exports

**Acceptance Criteria**:
- [ ] 0 test collection errors
- [ ] 3,867+ tests collected
- [ ] All imports resolve correctly

---

### Task 4: TODO Audit & Resolution
**Priority**: P0 - BLOCKING
**Owner**: Tech Lead + Senior Engineers
**Estimate**: 4 hours
**Status**: PENDING

**Given** 21 TODO items exist in production code
**When** we classify and resolve P0 items
**Then** 0 P0 TODOs remain and resolution plan is documented

**Phase 1: Extract TODOs (30 min)**
```bash
cd /home/nqh/shared/SDLC-Orchestrator/backend
grep -rn "TODO" app/ --include="*.py" | grep -v "test_" > todos-audit-raw.txt
wc -l todos-audit-raw.txt
```

**Phase 2: Classify (1 hour)**

| Classification | Criteria | Action |
|----------------|----------|--------|
| **P0** | Security gaps, incomplete validation, blocking errors | FIX TODAY |
| **P1** | Performance, logging, minor improvements | JIRA ticket (Sprint 133) |
| **P2** | Nice-to-have, documentation | Backlog |

**Phase 3: Fix P0 TODOs (2 hours)**
- Create fix branch: `fix/p0-todos-sprint132`
- Fix each P0 item
- Run tests after each fix
- Commit with clear messages

**Phase 4: Document (30 min)**
- Create `docs/go-live/TODO-RESOLUTION-PLAN.md`
- List all TODOs with classification
- Include commit SHAs for P0 fixes
- Include JIRA links for P1 items

**Acceptance Criteria**:
- [ ] 0 P0 TODOs remaining
- [ ] All P1/P2 TODOs have tickets or backlog items
- [ ] `TODO-RESOLUTION-PLAN.md` published

---

## Non-Blocking Items (Sprint 133)

### YAML Frontmatter Migration
**Priority**: P1 - POST-LAUNCH
**Status**: Deferred to Sprint 133

**Current State**: 10/861 files (1.2%) have YAML frontmatter
**Target**: 100% compliance

**Sprint 133 Plan**:
```bash
python scripts/sdlc-validation/batch-add-frontmatter.py \
  --input docs/ --tier PROFESSIONAL --execute
```

### BDD Format Conversion
**Priority**: P2 - POST-LAUNCH
**Status**: Deferred to Sprint 134

**Current State**: 139/861 files (16.1%) use Given/When/Then
**Target**: 100% compliance

---

## Timeline & Checkpoints

| Time | Checkpoint | Owner | Deliverable |
|------|------------|-------|-------------|
| 11:00 AM | Start Sprint 132 | All | Sprint kickoff |
| 11:30 AM | Task 1 Complete | DevOps | sdlcctl CLI working |
| 12:00 PM | Task 2 Complete | Frontend | Extension auth debugged |
| 2:00 PM | Task 3 Complete | Backend | 0 test errors |
| 5:00 PM | **CHECKPOINT #1** | CTO | Progress review |
| 6:00 PM | Task 4 Complete | Tech Lead | TODO audit done |
| 8:00 PM | **CHECKPOINT #2** | CTO | Final validation |
| Feb 1, 9:00 AM | **GO/NO-GO DECISION** | CTO | Launch approval |

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Test errors unfixable | Low | High | Pair programming, escalate to CTO |
| TODOs reveal blocking issues | Medium | High | Prioritize security-related items |
| Extension auth complex | Medium | Medium | Document as expected behavior if timeout |
| Time overrun | Medium | Medium | Cut P2 items, focus on P0 only |

---

## Success Criteria

### Sprint 132 Exit Criteria

**Mandatory (Go-Live Blockers)**:
1. ✅ **0 test collection errors** - `pytest --collect-only -q`
2. ✅ **0 P0 TODOs** - No incomplete implementations in production
3. ✅ **sdlcctl CLI functional** - `--version` returns 1.2.0
4. ✅ **3,867+ tests passing** - Full test suite green
5. ✅ **TODO resolution plan documented** - Published to docs/go-live/

**Nice-to-Have (Can defer)**:
- Extension auth fully debugged (can defer feature)
- YAML frontmatter migration (Sprint 133)
- BDD format conversion (Sprint 134)

---

## Definition of Done

- [ ] All P0 tasks completed
- [ ] 0 test collection errors
- [ ] 0 P0 TODOs
- [ ] sdlcctl CLI working
- [ ] TODO-RESOLUTION-PLAN.md published
- [ ] CTO final approval at 8PM checkpoint
- [ ] Launch confidence ≥ 95%

---

## References

- [Go-Live Plan v4.0](../../../.claude/plans/twinkly-waddling-dewdrop.md)
- [FIX-CONTEXT-OVERLAY-ERROR.md](../../../FIX-CONTEXT-OVERLAY-ERROR.md)
- [Sprint 131 Completion](./SPRINT-131-DOCUMENTATION-COMPLIANCE.md)
- [SDLC 6.1.0 Framework](../../../SDLC-Enterprise-Framework/)

---

**Sprint Owner**: CTO
**Created**: January 31, 2026
**Status**: ✅ APPROVED - EXECUTION STARTED
