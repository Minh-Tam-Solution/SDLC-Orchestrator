# EP-04: SDLC Structure Enforcement (Universal AI Codex)

**Status:** APPROVED  
**Created:** December 21, 2025  
**Updated:** December 21, 2025  
**Owner:** Platform Team  
**Priority:** P1 (follows EP-02)  
**Budget:** $8,000 (internal tooling, 47 SP)

---

## Executive Summary

Automate SDLC folder structure validation and auto-fixing to eliminate manual restructuring effort. **Tool-agnostic design** supports all AI coding assistants (Cursor, Copilot, ChatGPT, Claude Code, etc.) without per-tool integration.

**Key Insight:** We validate the OUTPUT, not the tool. This makes the system future-proof for any new AI coding assistant.

### Supported AI Coding Tools (Auto-Detected)

| Tool | Vendor | Detection Method |
|------|--------|------------------|
| Claude Code | Anthropic | Output validation |
| Cursor | Anysphere | Output validation |
| GitHub Copilot | Microsoft | Output validation |
| ChatGPT Code Interpreter | OpenAI | Output validation |
| Amazon CodeWhisperer | AWS | Output validation |
| Tabnine | Codota | Output validation |
| Codeium | Exafunction | Output validation |
| Replit Ghostwriter | Replit | Output validation |
| *Future AI tools* | *Any* | Output validation ✅ |

### Real-World Origin

Stage 02 restructure on Dec 21, 2025 took 45 minutes manually; this feature reduces to 30 seconds.

---

## Problem Statement

### Current State
- Manual restructuring takes 45+ minutes per occurrence
- Human error rate 5-10% (missed cross-references, typos)
- No standardized process documentation
- AI-generated code creates structure violations undetected until review

### Evidence (Dec 21, 2025 Incident)
```
DETECTED VIOLATIONS:
- docs/02-design/01-ADRs/           ✅
- docs/02-design/01-System-Architecture/  ❌ CONFLICT (duplicate 01)
- docs/02-design/03-ADRs/           ❌ CONFLICT (duplicate 03)  
- docs/02-design/03-API-Design/     ❌ CONFLICT (duplicate 03)
- docs/02-design/03-Technical-Specs/ ❌ CONFLICT (duplicate 03)
- docs/02-design/08-Admin-Panel/    ❌ CONFLICT (duplicate 08)
- docs/02-design/08-DevOps-Architecture/ ❌ CONFLICT (duplicate 08)

FIX EFFORT:
- 78 files migrated
- 30+ cross-references updated
- 3 git commits
- 45 minutes elapsed time
```

---

## Solution

### `sdlcctl validate --auto-fix`

Automated detection and remediation of SDLC structure violations:

```bash
# Scan only (no fix)
sdlcctl validate
# Output:
# ❌ docs/02-design: 3 violations (duplicate numbering)
# ❌ docs/02-design: 1 violation (fragmented ADRs)
# Run 'sdlcctl validate --auto-fix' to fix automatically

# Auto-fix with preview
sdlcctl validate --auto-fix --dry-run

# Execute auto-fix
sdlcctl validate --auto-fix
# ✓ Renamed 15 folders
# ✓ Consolidated 15 ADRs
# ✓ Updated 30 cross-references
# ✓ Created commit d616cd1
```

---

## Detection Rules

### Rule 1: `stage-folder-sequential-numbering`

```yaml
rule: stage-folder-sequential-numbering
pattern: docs/{stage}/**/
validation:
  - Each child folder must start with XX- (01-99)
  - No duplicate numbers within same parent
  - Must be sequential (01, 02, 03... not 01, 03, 05)
  - 99-Legacy/ exempt from sequence

auto_fix_strategy:
  1. Scan current structure
  2. Group by parent folder
  3. Detect conflicts (duplicates, gaps)
  4. Generate rename plan (reverse order to avoid collisions)
  5. Update cross-references (AST-based for code, regex for markdown)
  6. Validate links (no 404s)
  7. Create git commit with detailed message
```

### Rule 2: `adr-consolidation`

```yaml
rule: adr-consolidation
pattern: "**/ADR-*.md" or "**/Architecture-Decisions/"
validation:
  - All ADRs must be in {stage}/01-ADRs/
  - No ADRs scattered across multiple folders
  - ADR numbers must be unique (no duplicates)

auto_fix_strategy:
  1. Find all ADR files recursively
  2. Check for number conflicts (e.g., two ADR-015)
  3. Move to {stage}/01-ADRs/
  4. Archive duplicates to 99-Legacy/
  5. Update all references
```

### Rule 3: `naming-convention`

```yaml
rule: naming-convention
pattern: docs/{stage}/**/
validation:
  - Folder names must use PascalCase-Hyphenated (e.g., "System-Architecture")
  - No underscores in folder names
  - Consistent suffixes (-Design, -Specs, -Architecture)

auto_fix_strategy:
  1. Detect naming violations
  2. Generate rename suggestions
  3. Apply standardized naming
  4. Update references
```

---

## Sprint Breakdown

### Sprint 44: Enhanced Detection (Feb 17-28, 2026)

**Goal:** Implement comprehensive violation detection

**User Stories:**
| ID | Story | Points |
|----|-------|--------|
| EP04-001 | As a developer, I can run `sdlcctl validate` to see all structure violations | 5 |
| EP04-002 | As a developer, I see severity levels (error, warning, info) for violations | 3 |
| EP04-003 | As a developer, I see auto-fix availability indicator per violation | 2 |
| EP04-004 | As a CI/CD, I can fail builds on error-level violations | 3 |

**Technical Tasks:**
- [ ] Implement `FolderStructureValidator` class
- [ ] Add `sequential-numbering` detection rule
- [ ] Add `adr-consolidation` detection rule
- [ ] Add `naming-convention` detection rule
- [ ] Create violation severity classification
- [ ] Add JSON output format for CI/CD integration

**Deliverables:**
- `backend/app/services/sdlc_validator.py`
- `backend/sdlcctl/commands/validate.py`
- Unit tests with 90%+ coverage

---

### Sprint 45: Auto-Fix Engine (Mar 3-14, 2026)

**Goal:** Implement automated remediation engine

**User Stories:**
| ID | Story | Points |
|----|-------|--------|
| EP04-005 | As a developer, I can preview fixes with `--dry-run` flag | 5 |
| EP04-006 | As a developer, I can execute fixes with `--auto-fix` flag | 8 |
| EP04-007 | As a developer, cross-references are updated automatically | 5 |
| EP04-008 | As a developer, a RESTRUCTURE-PLAN.md is generated documenting changes | 3 |

**Technical Tasks:**
- [ ] Implement `AutoFixEngine` class
- [ ] Implement `RenamePlanner` with collision avoidance
- [ ] Implement `CrossReferenceUpdater` (markdown + code)
- [ ] Implement `LinkValidator` (detect broken links)
- [ ] Generate RESTRUCTURE-PLAN.md automatically
- [ ] Create atomic git commits with detailed messages

**Deliverables:**
- `backend/app/services/auto_fix_engine.py`
- `backend/app/services/cross_reference_updater.py`
- Integration tests with real file operations

---

### Sprint 46: CLI + CI/CD Integration (Mar 17-28, 2026)

**Goal:** Production-ready CLI and CI/CD integration

**User Stories:**
| ID | Story | Points |
|----|-------|--------|
| EP04-009 | As a developer, I can use `sdlcctl validate` in pre-commit hooks | 3 |
| EP04-010 | As a CI/CD, structure violations block PR merge | 5 |
| EP04-011 | As a developer, I can request auto-fix via PR comment `/sdlc fix` | 3 |
| EP04-012 | As a CTO, I see structure compliance dashboard | 2 |

**Technical Tasks:**
- [ ] Create GitHub Action for structure validation
- [ ] Add pre-commit hook integration
- [ ] Implement `/sdlc fix` PR comment trigger
- [ ] Add compliance metrics to dashboard
- [ ] Documentation and user guides

**Deliverables:**
- `.github/actions/sdlc-validate/action.yml`
- `.pre-commit-hooks.yaml` template
- GitHub App webhook handler for PR comments
- User documentation

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Time to restructure | < 1 min | Timer from command to commit |
| Cross-reference accuracy | 100% | Zero broken links post-fix |
| Detection coverage | 95%+ | Known violation types detected |
| CI/CD integration | 100% projects | All repos have GitHub Action |

---

## Dependencies

| Dependency | Status | Notes |
|------------|--------|-------|
| EP-02 AI Safety Layer | In Progress (Sprint 41-43) | Provides Policy Guard framework |
| ADR-014 SDLC Structure Validator | ✅ Approved | Design foundation |
| sdlcctl CLI framework | ✅ Exists | `backend/sdlcctl/` |

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Cross-reference updates miss edge cases | Medium | High | Comprehensive test suite, dry-run mode |
| Git history issues with renames | Low | Medium | Use `git mv`, preserve history |
| Performance on large repos | Low | Low | Incremental scanning, caching |

---

## Integration with AI Safety Layer

```
AI-Generated Code → PR Created
        ↓
   AI Detection (EP-02)
        ↓
   Policy Guard Check
        ↓
   ┌─────────────────────────────────────┐
   │ SDLC Structure Validation (EP-04)   │
   │ - sequential-numbering              │
   │ - adr-consolidation                 │
   │ - naming-convention                 │
   └─────────────────────────────────────┘
        ↓
   Violation Detected?
        ↓
   YES → Block PR + Suggest Auto-Fix
   NO  → Continue to next policy check
```

**Value:** AI-generated folder structures are validated before merge, preventing structure violations from entering codebase.

---

## Real-World Scenarios

### Scenario 1: Cursor Creates Wrong Structure

```bash
# Developer uses Cursor prompt:
"Create a new design document for user authentication flow"

# Cursor generates (WRONG):
docs/02-design/15-Auth-Flow/User-Auth-Design.md
                ↑↑
                Gap! (no 14-)

# SDLC Orchestrator detects in real-time:
🤖 AI Code Event Detected
Tool: Cursor
Action: File creation
Files: docs/02-design/15-Auth-Flow/

⚠️ SDLC Structure Violation
Rule: stage-folder-sequential-numbering
Issue: Gap in numbering (14 missing)
Suggestion: Rename 15-Auth-Flow → 14-Auth-Flow

Auto-fix? [y/N]: y
✓ Renamed to 14-Auth-Flow
✓ Structure now compliant ✅
```

### Scenario 2: GitHub Copilot Duplicate ADR

```bash
# Developer accepts Copilot suggestion:
# "Create ADR for database migration strategy"

# Copilot generates (WRONG):
docs/02-design/03-Database-Design/ADR-020-Migration.md
                                    ↑↑↑
                                    Should be in 01-ADRs/

# SDLC Orchestrator PR check:
GitHub PR #789: "feat: Add database migration ADR"

🤖 SDLC Orchestrator Policy Guard
❌ PR BLOCKED - ADR Location Violation

Violation: adr-consolidation
- ADR-020 must be in docs/02-design/01-ADRs/
- Not in docs/02-design/03-Database-Design/

Auto-fix: Move to correct location?
□ Yes, auto-move and update references
□ No, I'll fix manually
□ Request VCR override (requires CTO approval)
```

### Scenario 3: ChatGPT Creates Duplicate Number

```bash
# Developer copy-pastes ChatGPT response:
"Here's the folder structure for your API documentation"

# ChatGPT suggests (WRONG):
docs/02-design/04-API-Documentation/
               ↑↑
               Conflicts with existing 04-API-Design/

# Pre-commit hook catches:
$ git commit -m "Add API docs"

⚠️ Pre-commit: SDLC Structure Validation
Detected violation: Duplicate folder number
- Existing: docs/02-design/04-API-Design/
- New:      docs/02-design/04-API-Documentation/

Auto-fix suggestions:
1. Rename 04-API-Documentation → 15-API-Documentation
2. Merge into existing 04-API-Design/
3. Override (--no-verify flag, not recommended)

Choose option [1-3]: 1
✓ Renamed to 15-API-Documentation
✓ Commit proceeding...
```

---

## Multi-Checkpoint Integration

### Checkpoint 1: Pre-Commit Hook (Sprint 44)

```bash
# .git/hooks/pre-commit (auto-installed by sdlcctl)

#!/bin/bash
# SDLC Structure Validator - Pre-Commit Hook
# Validates structure regardless of AI tool used

echo "🔍 SDLC Structure Validation..."

# Get staged files
STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM)

# Check for structure violations
VIOLATIONS=$(sdlcctl validate --staged-only --format=json)

if [ -n "$VIOLATIONS" ]; then
  echo "⚠️ SDLC Structure Violations Detected:"
  echo "$VIOLATIONS" | jq -r '.[] | "  - \(.rule): \(.message)"'
  
  echo ""
  echo "Auto-fix available. Run:"
  echo "  sdlcctl validate --auto-fix"
  echo ""
  echo "Or override (not recommended):"
  echo "  git commit --no-verify"
  
  exit 1
fi

echo "✅ SDLC Structure: COMPLIANT"
exit 0
```

### Checkpoint 2: GitHub Action (Sprint 45)

```yaml
# .github/workflows/sdlc-validation.yml

name: SDLC Structure Validation

on:
  pull_request:
    paths:
      - 'docs/**'

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup SDLC CLI
        run: pip install sdlcctl
      
      - name: Validate SDLC Structure
        id: validate
        run: sdlcctl validate --format=github-action
        continue-on-error: true
      
      - name: Post PR Comment (if violations)
        if: steps.validate.outcome == 'failure'
        uses: actions/github-script@v6
        with:
          script: |
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: `🤖 **SDLC Orchestrator Structure Validation**
              
              ❌ **PR BLOCKED** - SDLC 5.1.1 violations detected
              
              **Auto-fix available:**
              \`\`\`bash
              sdlcctl validate --auto-fix
              git add . && git commit -m "fix: SDLC structure compliance"
              git push
              \`\`\`
              
              Or request **VCR Override** (requires CTO approval)`
            })
      
      - name: Block PR if violations
        if: steps.validate.outcome == 'failure'
        run: exit 1
```

### Checkpoint 3: VS Code Extension (Sprint 46)

```typescript
// Real-time validation for ANY AI tool output

export class StructureValidator {
  async onFileCreate(uri: vscode.Uri): Promise<void> {
    const violations = await this.validatePath(uri.fsPath)
    
    if (violations.length > 0) {
      const action = await vscode.window.showWarningMessage(
        `⚠️ SDLC Structure Violation:\n${violations.map(v => v.message).join('\n')}`,
        'Auto-fix',
        'Ignore',
        'Learn More'
      )
      
      if (action === 'Auto-fix') {
        await this.autoFix(violations)
        vscode.window.showInformationMessage('✅ Structure fixed!')
      }
    }
  }
}
```

---

## Tool-Agnostic Design Benefits

| Traditional (Tool-Specific) | SDLC Orchestrator (Tool-Agnostic) |
|----------------------------|-----------------------------------|
| ❌ Cursor integration → breaks when Cursor updates | ✅ Validates OUTPUT, not tool |
| ❌ Copilot plugin → doesn't work with ChatGPT | ✅ Works with any AI assistant |
| ❌ New AI tool → requires new integration | ✅ Zero per-tool integration |
| ❌ 8 tools × N updates = maintenance chaos | ✅ One codebase → all tools covered |

**Annual Impact (per team):**
- Without SDLC Orchestrator: 2 hours/week cleanup × 52 = **104 hours/year**
- With SDLC Orchestrator: 30 seconds/violation × auto-fix = **~2 hours/year**
- **Savings: 102 hours/year per team**

---

## Approval

| Role | Name | Date | Status |
|------|------|------|--------|
| CTO | [CTO] | Dec 21, 2025 | ✅ APPROVED |
| Tech Lead | TBD | - | Pending |
| PM | TBD | - | Pending |

---

## References

- [ADR-014: SDLC Structure Validator](../../../02-design/01-ADRs/ADR-014-SDLC-Structure-Validator.md)
- [EP-02: AI Safety Layer](EP-02-AI-Safety-Layer.md)
- [SDLC 5.1.1 Framework](../../../../SDLC-Enterprise-Framework/02-Core-Methodology/)
