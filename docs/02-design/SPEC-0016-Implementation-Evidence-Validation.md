# SPEC-0016: Implementation Evidence Validation

**Status**: 🟡 PROPOSED  
**Created**: February 1, 2026  
**Owner**: CTO  
**Priority**: P0 - Critical Meta-Problem  

---

## 🎯 Executive Summary

**Problem**: SDLC Orchestrator is experiencing the exact context drift problem it was built to prevent. Specs are approved and backend is implemented perfectly, but frontend UI components are completely missing. No automation detected this drift.

**Solution**: Implement automated spec-to-code validation that requires evidence files proving each spec component is implemented across all surfaces (Backend, Web, CLI, Extension).

**Impact**: Prevent future spec-code drift, restore trust in our own processes, enable "eat your own dog food" dogfooding.

---

## 📊 Problem Statement

### Current Situation (Meta-Problem)

```
SDLC Orchestrator Mission: Prevent AI coder context drift
                    ↓
          Reality: SDLC Orchestrator HAS context drift
                    ↓
         "The doctor must take their own medicine" - FAILED ❌
```

### Evidence of Drift

| Component | Spec | Backend | Web UI | CLI | Extension |
|-----------|------|---------|--------|-----|-----------|
| Team Invitations (ADR-043, SPEC-0012) | ✅ Approved | ✅ 100% | ❌ 0% | N/A | N/A |
| GitHub Integration (ADR-044, SPEC-0010) | ✅ Approved | ✅ 100% | ❌ 0% | ✅ Done | ❌ Missing |
| Auto-Detect Project | N/A | N/A | N/A | N/A | ✅ Done |

**Root Cause Analysis**:
1. ✅ Planning Phase: Specs detailed, ADRs approved → **Good**
2. ✅ Backend Execution: Code quality high, 100% spec match → **Good**
3. ❌ Frontend Execution: UI components never built → **Bad**
4. ❌ Detection: No automation caught the drift → **Critical Gap**

### Launch Impact

- **Original Plan**: Soft Launch Feb 1, 2026
- **Current Status**: **Launch SUSPENDED** - P0 blockers discovered
- **Delay**: 2-3 days (20-30 hours effort)
- **Confidence**: Dropped from 90% → 60%

### User's Critical Observation

> "chính SDLC Orchestrator lại bị drift context, khi chúng ta muốn làm 1 automation tool kiểm soát việc này"
> 
> "plan rất kỹ, nhưng khi thực thì lại không bám sát được plan"

**This is the most important lesson of the entire project.**

---

## 🎯 Solution Design

### 1. Evidence-Based Validation

For each `SPEC-00XX.md`, require a companion `SPEC-00XX-evidence.json`:

```json
{
  "spec_id": "SPEC-0012",
  "title": "Team Invitation System",
  "status": "implemented",
  "last_validated": "2026-02-01T09:00:00Z",
  "evidence": {
    "backend": {
      "api_routes": [
        "POST /api/v1/teams/{team_id}/invitations",
        "GET /api/v1/teams/{team_id}/invitations",
        "POST /api/v1/teams/invitations/{id}/accept",
        "DELETE /api/v1/teams/invitations/{id}"
      ],
      "services": ["app/services/invitation_service.py"],
      "models": ["app/models/invitation.py"],
      "tests": ["tests/unit/test_invitation_service.py"],
      "coverage": 95.0,
      "status": "complete"
    },
    "frontend": {
      "components": [
        "src/components/teams/InvitationForm.tsx",
        "src/components/teams/InvitationList.tsx"
      ],
      "pages": ["src/app/teams/[id]/invitations/page.tsx"],
      "hooks": ["src/hooks/useInvitations.ts"],
      "tests": ["e2e/invitations.spec.ts"],
      "status": "missing"  // ← This would have caught the problem!
    },
    "cli": {
      "commands": [],
      "status": "not_applicable"
    },
    "extension": {
      "commands": [],
      "status": "not_applicable"
    }
  },
  "validation": {
    "all_surfaces_complete": false,  // ← Blocker!
    "blocking_surfaces": ["frontend"],
    "can_launch": false
  }
}
```

### 2. Validation Rules

#### Rule 1: Spec Must Have Evidence File

```yaml
rule: "spec-has-evidence"
severity: error
check: |
  For each docs/02-design/SPEC-*.md:
    - Evidence file exists: SPEC-*-evidence.json
    - Evidence file is valid JSON
    - Evidence file has all required fields
```

#### Rule 2: All Planned Surfaces Must Be Implemented

```yaml
rule: "all-surfaces-implemented"
severity: error
check: |
  For each surface in spec.evidence:
    IF status != "not_applicable":
      - status == "complete"
      - files[] all exist
      - tests exist and pass
```

#### Rule 3: Sprint Close Gate

```yaml
gate: "G-Sprint-Close"
criteria:
  - all_specs_have_evidence: true
  - all_surfaces_complete: true
  - no_blocking_gaps: true
  - validation.can_launch: true
```

### 3. Automation Points

#### A. Pre-Commit Hook

```bash
#!/bin/bash
# .git/hooks/pre-commit

echo "🔍 Validating spec-code alignment..."

# Check if any SPEC-*.md changed
SPECS_CHANGED=$(git diff --cached --name-only | grep "SPEC-.*\.md")

if [ ! -z "$SPECS_CHANGED" ]; then
  # Validate evidence files exist
  sdlcctl validate --check-evidence-files
  
  if [ $? -ne 0 ]; then
    echo "❌ Spec-code alignment check FAILED"
    echo "Run: sdlcctl validate --check-evidence-files --fix"
    exit 1
  fi
fi

echo "✅ Spec-code alignment check PASSED"
```

#### B. GitHub Action (CI/CD)

```yaml
name: Spec-Code Alignment Check
on: [push, pull_request]

jobs:
  validate-evidence:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Install SDLC CLI
        run: pip install sdlcctl
      
      - name: Validate Implementation Evidence
        run: |
          sdlcctl validate --check-implementation-gaps \
            --output gaps.json \
            --fail-on-missing
      
      - name: Comment PR with Gaps
        if: failure()
        uses: actions/github-script@v6
        with:
          script: |
            const fs = require('fs');
            const gaps = JSON.parse(fs.readFileSync('gaps.json'));
            await github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: `## ❌ Spec-Code Alignment Failed\n\n${gaps.summary}`
            });
```

#### C. Weekly Alignment Check (Cron)

```bash
# .github/workflows/weekly-alignment-check.yml
name: Weekly Spec Alignment Audit
on:
  schedule:
    - cron: '0 9 * * MON'  # Every Monday 9am

jobs:
  audit-alignment:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Run Full Alignment Check
        run: sdlcctl align check --output gaps.md
      
      - name: Create GitHub Issue if Gaps Found
        if: failure()
        run: |
          gh issue create \
            --title "⚠️ Spec-Code Drift Detected - Week $(date +%U)" \
            --body-file gaps.md \
            --label "context-drift,P0" \
            --assignee "@CTO"
```

### 4. CLI Commands

#### `sdlcctl validate --check-evidence-files`

Validates all SPEC-*.md have evidence files:

```bash
$ sdlcctl validate --check-evidence-files

🔍 Checking spec-evidence alignment...

✅ SPEC-0010: Evidence file exists and valid
❌ SPEC-0012: Evidence file missing
❌ SPEC-0015: Evidence exists but frontend.status = "missing"

Summary:
  Total Specs: 16
  With Evidence: 14
  Missing Evidence: 2
  Blocking Gaps: 1 (SPEC-0012 frontend)
  
❌ VALIDATION FAILED - 1 blocking gap found
```

#### `sdlcctl validate --check-implementation-gaps`

Validates code files exist for each evidence claim:

```bash
$ sdlcctl validate --check-implementation-gaps

🔍 Checking implementation gaps...

SPEC-0012: Team Invitation System
  Backend:
    ✅ POST /api/v1/teams/{team_id}/invitations (found)
    ✅ app/services/invitation_service.py (exists)
    ✅ tests/unit/test_invitation_service.py (passing)
  Frontend:
    ❌ src/components/teams/InvitationForm.tsx (NOT FOUND)
    ❌ src/app/teams/[id]/invitations/page.tsx (NOT FOUND)
    ❌ e2e/invitations.spec.ts (NOT FOUND)

❌ VALIDATION FAILED - 3 files missing
```

#### `sdlcctl align check`

Full alignment check with drift analysis:

```bash
$ sdlcctl align check --output gaps.md

🔍 Running full spec-code alignment check...

Checking SPEC-0010: GitHub Integration...
  Backend: ✅ Complete (100%)
  Frontend: ❌ Missing (0%)
  Drift Score: 50%

Checking SPEC-0012: Team Invitations...
  Backend: ✅ Complete (100%)
  Frontend: ❌ Missing (0%)
  Drift Score: 50%

Overall Alignment: 75% (12/16 specs complete)
Context Drift Score: 25% (4 specs with surface gaps)

❌ CRITICAL DRIFT DETECTED
```

---

## 🔧 Implementation Plan

### Phase 1: Create Evidence Files (Day 1 - Feb 1)

**Owner**: Tech Lead  
**Time**: 4 hours

**Tasks**:
1. Create `SPEC-00XX-evidence.json` template
2. Generate evidence files for all 16 existing specs
3. Mark frontend status as "missing" for SPEC-0010, SPEC-0012

**Deliverable**: 16 evidence files in `docs/02-design/evidence/`

---

### Phase 2: Build Validator Tool (Day 1-2 - Feb 1-2)

**Owner**: Backend Lead  
**Time**: 8 hours

**Tasks**:
1. Create `sdlcctl validate --check-evidence-files` command
2. Create `sdlcctl validate --check-implementation-gaps` command
3. Create `sdlcctl align check` command
4. Add JSON schema validation for evidence files
5. Write unit tests (coverage >90%)

**Deliverable**: Working CLI commands with tests

---

### Phase 3: Setup Automation (Day 2 - Feb 2)

**Owner**: DevOps Lead  
**Time**: 4 hours

**Tasks**:
1. Create pre-commit hook (`.git/hooks/pre-commit`)
2. Create GitHub Action (`.github/workflows/spec-alignment-check.yml`)
3. Create weekly cron (`.github/workflows/weekly-alignment-audit.yml`)
4. Enable for SDLC-Orchestrator repo

**Deliverable**: Automated checks running in CI/CD

---

### Phase 4: Fix P0 Gaps (Day 2-3 - Feb 2-3)

**Owner**: Frontend Lead  
**Time**: 12-16 hours

**Tasks**:
1. Build Team Invitation UI (6-8 hours)
   - InvitationForm.tsx
   - InvitationList.tsx
   - Teams invitations page
   - useInvitations hook
   - E2E tests
   
2. Build GitHub Integration UI (6-8 hours)
   - GitHubConnectButton.tsx
   - GitHubRepoList.tsx
   - GitHub settings page
   - useGitHub hook
   - E2E tests

**Deliverable**: Frontend components with >80% test coverage

---

### Phase 5: Dogfooding (Day 3 - Feb 3)

**Owner**: CTO  
**Time**: 2 hours

**Tasks**:
1. Register SDLC-Orchestrator in its own system
2. Enable Context Overlay for this project
3. Run full validation: `sdlcctl align check`
4. Verify all gaps fixed
5. Update evidence files to "complete"

**Deliverable**: Clean alignment check (0% drift)

---

## 📏 Success Criteria

### Launch Readiness

```yaml
criteria:
  - all_specs_have_evidence: true
  - all_evidence_files_valid: true
  - backend_complete: 100%
  - frontend_complete: 100%
  - cli_complete: 100%
  - extension_complete: 100%
  - context_drift_score: <5%
  - can_launch: true
```

### Validation Gates

#### Gate 1: Evidence Files Exist

```bash
$ sdlcctl validate --check-evidence-files
✅ All 16 specs have evidence files
```

#### Gate 2: No Implementation Gaps

```bash
$ sdlcctl validate --check-implementation-gaps
✅ All claimed files exist and pass tests
```

#### Gate 3: Zero Context Drift

```bash
$ sdlcctl align check
✅ Alignment: 100% (16/16 specs complete)
✅ Context Drift: 0%
✅ READY FOR LAUNCH
```

---

## 🎯 Long-Term Vision

### Prevent Future Drift

1. **Continuous Validation**: Pre-commit hooks catch drift immediately
2. **CI/CD Enforcement**: PRs blocked if evidence missing
3. **Weekly Audits**: Automated Monday checks create GitHub issues
4. **Dogfooding**: SDLC Orchestrator uses itself for quality control

### Expand to All Projects

Once validated on SDLC Orchestrator:
1. Package as default policy in SDLC Framework
2. Enable for all Nhat Quang Holding projects
3. Offer as premium feature to customers
4. Market as "Spec-Code Alignment as a Service"

---

## 📚 Related Documents

- **ADR-043**: Team Collaboration Features (backend ✅, frontend ❌)
- **ADR-044**: GitHub Integration Strategy (backend ✅, frontend ❌)
- **SPEC-0010**: GitHub Integration Implementation (drift detected)
- **SPEC-0012**: Team Invitation System (drift detected)
- **Sprint 132**: Go-Live Preparation (blocked by this spec)

---

## 🔍 Lessons Learned

### What Went Right

1. ✅ **Planning**: Specs were detailed and approved
2. ✅ **Backend Execution**: 100% match to specs, high quality
3. ✅ **Detection**: Planning agent caught the drift before launch

### What Went Wrong

1. ❌ **No Automation**: Manual oversight failed to catch drift
2. ❌ **Frontend Oversight**: UI components never built despite specs
3. ❌ **Validation Gap**: No tools to verify spec-code alignment

### Key Insight

> **"The doctor must take their own medicine"**
> 
> We built a tool to prevent context drift in AI-assisted development.
> We didn't use it on ourselves.
> We experienced the exact problem we're solving.
> 
> **This is the validation we needed.** ✅

---

## ✅ Approval & Sign-Off

**Created By**: CTO  
**Date**: February 1, 2026, 9:00 AM  
**Status**: 🟡 PROPOSED - Awaiting approval  
**Priority**: P0 - Blocking launch

**Approvers**:
- [ ] CEO - Strategic approval
- [ ] CPO - Product alignment approval
- [ ] Tech Lead - Technical feasibility approval
- [ ] DevOps Lead - Automation feasibility approval

**Implementation Start**: February 1, 2026 (immediately)  
**Target Completion**: February 3, 2026 (before new launch date)

---

**Note**: This spec is being created in response to a critical meta-problem discovered on launch day. It represents the most important lesson of the entire SDLC Orchestrator project: we must use our own tools to prevent the problems we're solving for others.
