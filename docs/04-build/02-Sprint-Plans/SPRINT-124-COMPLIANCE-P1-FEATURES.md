---
# Required Fields (9/9) - SDLC 6.1.0 Section 8
sprint_id: SPRINT-124
title: "Compliance P1 Features - Version Validator & Auto-Fix"
status: PLANNING
tier: PROFESSIONAL
owner: "Backend Lead + Frontend Lead"
start_date: 2026-03-17
end_date: 2026-03-28
framework_version: 6.0.5

# Context Management (AGENTS.md 4-Zone Model)
context_zone: Semi-Static
update_frequency: Daily

# Sprint-Specific Fields
team_size: 2
priority: P1
effort_hours: 40
effort_sp: 5
estimated_loc: 1800
stage: 04-build
dependencies:
  - SPRINT-123 (Compliance Validation P0)
related_specs:
  - SPEC-0013 (Compliance Validation Service)
predecessor: SPRINT-123
successor: SPRINT-125
goals:
  - "Implement Version Reference Validator for CLAUDE.md/AGENTS.md consistency"
  - "Build Auto-Fix Engine with AI-assisted remediation suggestions"
  - "Integrate compliance scoring into Web Dashboard"
deliverables:
  - "Version Reference Validator (20h)"
  - "Auto-Fix Engine (12h)"
  - "Web Dashboard Integration (8h)"
  - "CLI commands: sdlcctl compliance versions/fix"
  - "API endpoints: version validation, auto-fix, dashboard integration"
---

# Sprint 124: Compliance P1 Features - Version Validator & Auto-Fix

**Dates**: March 17-28, 2026 (10 working days)
**Status**: 📋 PLANNED
**Total Estimated LOC**: ~1,800
**Estimated Effort**: 40h (20h Version Validator + 12h Auto-Fix + 8h Web Dashboard)
**Framework**: SDLC 6.1.0
**Priority**: P1 (Post-P0 Compliance Features)
**Predecessor**: Sprint 123 (Compliance Validation P0) - ✅ A+ Rating

---

## Executive Summary

Sprint 124 builds on Sprint 123's compliance foundation by adding P1 features: version reference validation, auto-fix engine, and web dashboard integration. These features transform compliance checking from passive reporting to active remediation.

### Sprint Objective

```
PRIMARY: Implement Version Reference Validator for CLAUDE.md/AGENTS.md consistency
SECONDARY: Build Auto-Fix Engine with AI-assisted remediation suggestions
TERTIARY: Integrate compliance scoring into Web Dashboard
```

### Sprint 123 Foundation (Required)

```yaml
Sprint 123 Deliverables (Prerequisite):
  ✅ Compliance Scorer (10 categories × 10 pts)
  ✅ Duplicate Folder Detection
  ✅ CLI: sdlcctl compliance score/duplicates/report/categories
  ✅ API: 5 compliance endpoints
  ✅ Database: compliance_checks, folder_collisions tables
  ✅ 21 unit tests (100% pass)
  ✅ CTO Approval: A+ Grade (98/100)
```

---

## CTO-Approved Roadmap Context

```yaml
Phase 0 (Jan 30 - Feb 28): Feature Freeze
  ✅ Complete - Go-Live Mar 1

Phase 1 (Mar 3-14): Sprint 123 - COMPLETE ✅
  ✅ P0: Compliance Scorer (A+ Rating)
  ✅ P0: Duplicate Detection (100% accuracy)

Phase 2 (Mar 17-28): Sprint 124 - THIS SPRINT
  - P1: Version Reference Validator (20h)
  - P1: Auto-Fix Engine (12h)
  - P1: Web Dashboard Integration (8h)

Phase 3 (Mar 31+): Sprint 125+
  - P2: Gate Readiness Dashboard
  - P2: Cross-project Compliance Aggregation
  - P3: Compliance Trends & Analytics
```

---

## Features

### Feature 1: Version Reference Validator (20h)

**Goal**: Validate SDLC version consistency across CLAUDE.md, AGENTS.md, and documentation files

#### 1.1 Version Reference Rules

```yaml
Version Consistency Rules:
  CLAUDE.md:
    - Header must contain "SDLC X.Y.Z" version
    - Version must match project's declared framework version
    - "Migration" suffix should be removed after completion

  AGENTS.md:
    - Version header must match CLAUDE.md
    - Framework reference must be consistent
    - No outdated "5.x → 6.0" migration references

  Documentation Files:
    - Sprint plans reference correct framework version
    - ADRs mention framework version if relevant
    - README.md has updated version badge

Validation Levels:
  ERROR:
    - CLAUDE.md missing version header
    - AGENTS.md version mismatch with CLAUDE.md
    - Migration reference after completion date

  WARNING:
    - Outdated version in older documents (>30 days)
    - Missing version in optional files

  INFO:
    - Version correctly synchronized
    - All references consistent
```

#### 1.2 Detection Patterns

```python
# Version extraction patterns
VERSION_PATTERNS = {
    "header": r"(?:SDLC|Framework)[\s:]*(\d+\.\d+\.\d+)",
    "badge": r"\[.*?(\d+\.\d+\.\d+).*?\]",
    "yaml_frontmatter": r"framework_version:\s*['\"]?(\d+\.\d+\.\d+)",
    "migration": r"(\d+\.\d+\.?\d*).*?[→→>]+.*?(\d+\.\d+\.?\d*)",
}

# Files to check
VERSION_FILES = {
    "required": ["CLAUDE.md", "docs/*/01-SDLC-Compliance/AGENTS.md"],
    "recommended": ["README.md", "docs/02-design/01-ADRs/*.md"],
    "optional": ["docs/04-build/02-Sprint-Plans/*.md"],
}
```

#### 1.3 API Endpoints

```yaml
POST /api/v1/projects/{id}/validate/versions:
  description: Validate version reference consistency
  request:
    project_id: UUID
    expected_version: Optional[str]  # Auto-detect if not provided
  response:
    valid: bool
    detected_version: str
    inconsistencies:
      - file: str
        found_version: str
        expected_version: str
        severity: str  # ERROR | WARNING | INFO
        line_number: int
        context: str
        fix_suggestion: str
    summary:
      files_checked: int
      errors: int
      warnings: int
      consistent: int

GET /api/v1/projects/{id}/compliance/versions:
  description: Get version reference report (cached)
  response:
    primary_version: str  # From CLAUDE.md
    agents_version: str
    docs_versions: Dict[str, str]
    last_checked: datetime
```

#### 1.4 CLI Commands

```bash
# Check version consistency
sdlcctl compliance versions
# Output:
# ✅ Primary Version: SDLC 6.1.0 (from CLAUDE.md)
# ✅ AGENTS.md: SDLC 6.1.0 (consistent)
# ⚠️ WARNING: docs/04-build/02-Sprint-Plans/SPRINT-41.md
#    Found: "SDLC 6.1.0", Expected: "SDLC 6.1.0"
#    Line 15: "Framework: SDLC 6.1.0"
#    Suggestion: Update to "Framework: SDLC 6.1.0"

# Check with expected version
sdlcctl compliance versions --expected 6.0.5

# Fix suggestions only
sdlcctl compliance versions --suggestions-only

# JSON output
sdlcctl compliance versions --format json
```

#### 1.5 Implementation Plan

| Day | Task | LOC | Status |
|-----|------|-----|--------|
| Day 1 | Version parser + extraction patterns | 200 | 📋 |
| Day 2 | VersionReferenceChecker service | 300 | 📋 |
| Day 3 | File scanning + CLAUDE/AGENTS validation | 250 | 📋 |
| Day 4 | API endpoints + response schemas | 150 | 📋 |
| Day 5 | CLI integration + tests | 150 | 📋 |
| **Total** | | **1,050** | |

---

### Feature 2: Auto-Fix Engine (12h)

**Goal**: Provide automated fix suggestions and one-click remediation for compliance issues

#### 2.1 Auto-Fix Categories

```yaml
Category 1: Duplicate Folder Resolution
  Detection: Sprint 123
  Auto-Fix Options:
    - Archive to 10-archive/ (recommended)
    - Merge contents into primary folder
    - Rename with valid prefix
  Implementation:
    - Generate shell commands
    - Create PR with changes
    - Rollback support

Category 2: Version Reference Update
  Detection: Sprint 124 (this feature)
  Auto-Fix Options:
    - Update header with correct version
    - Remove migration suffix
    - Add version badge to README
  Implementation:
    - sed/awk commands for simple updates
    - Template-based for complex changes

Category 3: YAML Frontmatter Migration
  Detection: Sprint 123 (Specifications Checker)
  Auto-Fix Options:
    - Add missing YAML frontmatter
    - Convert SDLC 5.x format to 6.0.5
    - Validate and fix field names
  Implementation:
    - Python script for frontmatter injection
    - Preserve existing content

Category 4: Stage Folder Naming
  Detection: Sprint 123 (Documentation Structure)
  Auto-Fix Options:
    - Rename to standard name (e.g., "04-Development" → "04-build")
    - Create missing stage folders
    - Move misplaced files
  Implementation:
    - Safe rename with git mv
    - Update internal references
```

#### 2.2 Auto-Fix API

```yaml
POST /api/v1/projects/{id}/compliance/fix:
  description: Generate or apply auto-fix for compliance issues
  request:
    project_id: UUID
    issue_id: UUID  # From compliance check result
    fix_type: str  # "suggest" | "preview" | "apply"
    options:
      backup: bool  # Create backup before applying
      dry_run: bool  # Show changes without applying
  response:
    fix_id: UUID
    status: str  # "suggested" | "previewed" | "applied" | "failed"
    changes:
      - file: str
        operation: str  # "update" | "rename" | "create" | "delete" | "move"
        before: Optional[str]
        after: Optional[str]
        line_numbers: Optional[List[int]]
    commands:  # Shell commands for manual execution
      - str
    rollback:  # Rollback information if applied
      backup_path: str
      restore_command: str

POST /api/v1/projects/{id}/compliance/fix/batch:
  description: Apply multiple fixes at once
  request:
    project_id: UUID
    issue_ids: List[UUID]
    options:
      create_pr: bool  # Create GitHub PR with changes
      branch_name: str
      commit_message: str
  response:
    batch_id: UUID
    status: str
    applied: int
    failed: int
    pr_url: Optional[str]
```

#### 2.3 CLI Commands

```bash
# List fixable issues
sdlcctl compliance fix --list
# Output:
# Fixable Issues (5):
#   1. [DUPLICATE] 04-Development + 04-Testing → Archive one
#   2. [VERSION] AGENTS.md header outdated → Update to 6.0.5
#   3. [SPEC] SPEC-0301 missing frontmatter → Add YAML block
#   4. [SPEC] SPEC-0302 missing frontmatter → Add YAML block
#   5. [FOLDER] Missing 03-integrate/ → Create folder

# Preview specific fix
sdlcctl compliance fix --preview 1
# Output:
# Fix Preview: Archive 04-Testing to 10-archive/
# Commands:
#   mkdir -p docs/10-archive/duplicate-sprint124
#   mv docs/04-Testing docs/10-archive/duplicate-sprint124/
#   git add .
#   git commit -m "fix: Archive duplicate 04-Testing folder"
#
# Apply? [y/N]

# Apply fix with backup
sdlcctl compliance fix --apply 1 --backup

# Batch fix all safe issues
sdlcctl compliance fix --apply-all --safe-only

# Create PR with all fixes
sdlcctl compliance fix --apply-all --create-pr
```

#### 2.4 Implementation Plan

| Day | Task | LOC | Status |
|-----|------|-----|--------|
| Day 6 | AutoFixEngine service + fix generators | 200 | 📋 |
| Day 7 | Fix preview + apply logic | 150 | 📋 |
| Day 8 | CLI integration + batch support | 100 | 📋 |
| Day 9 | PR creation integration + tests | 100 | 📋 |
| **Total** | | **550** | |

---

### Feature 3: Web Dashboard Integration (8h)

**Goal**: Integrate compliance scoring into Web Dashboard with visual reports

#### 3.1 Dashboard Components

```yaml
Components:

1. ComplianceScoreCard.tsx:
   - Large circular progress (X/100)
   - Color-coded: Green (≥85), Yellow (70-84), Orange (50-69), Red (<50)
   - Last checked timestamp
   - "Run Check" button

2. ComplianceCategoryBreakdown.tsx:
   - Horizontal bar chart (10 categories)
   - Each bar shows X/10 score
   - Click to expand issues

3. ComplianceIssuesList.tsx:
   - Sortable table: Issue, Category, Severity, Fix Available
   - Filter by severity (Critical, High, Medium, Low)
   - "Fix" button for auto-fixable issues

4. ComplianceHistoryChart.tsx:
   - Line chart showing score over time
   - Annotations for major changes
   - Compare with team average

5. ComplianceQuickActions.tsx:
   - "Run Full Check" button
   - "Fix All Safe Issues" button
   - "Export Report" dropdown (PDF, JSON, CSV)
```

#### 3.2 API Integration

```typescript
// hooks/useComplianceScore.ts
export function useComplianceScore(projectId: string) {
  return useQuery({
    queryKey: ['compliance', 'score', projectId],
    queryFn: () => complianceApi.getScore(projectId),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

// hooks/useComplianceValidation.ts
export function useComplianceValidation(projectId: string) {
  return useMutation({
    mutationFn: () => complianceApi.runValidation(projectId),
    onSuccess: () => {
      queryClient.invalidateQueries(['compliance', 'score', projectId]);
    },
  });
}

// hooks/useComplianceFix.ts
export function useComplianceFix(projectId: string) {
  return useMutation({
    mutationFn: (issueId: string) => complianceApi.applyFix(projectId, issueId),
    onSuccess: () => {
      queryClient.invalidateQueries(['compliance', projectId]);
    },
  });
}
```

#### 3.3 Pages

```yaml
Pages:

1. /projects/{id}/compliance:
   - Main compliance dashboard
   - ComplianceScoreCard (hero)
   - ComplianceCategoryBreakdown
   - ComplianceIssuesList
   - ComplianceHistoryChart

2. /projects/{id}/compliance/issues:
   - Full issues list with pagination
   - Bulk fix selection
   - Export functionality

3. /projects/{id}/compliance/history:
   - Historical compliance scores
   - Trend analysis
   - Comparison with benchmarks
```

#### 3.4 Implementation Plan

| Day | Task | LOC | Status |
|-----|------|-----|--------|
| Day 8 | ComplianceScoreCard + CategoryBreakdown | 150 | 📋 |
| Day 9 | ComplianceIssuesList + QuickActions | 150 | 📋 |
| Day 10 | HistoryChart + API hooks + tests | 100 | 📋 |
| **Total** | | **400** | |

---

## Day-by-Day Implementation Schedule

### Week 1 (Mar 17-21): Version Validator

| Day | Focus | Deliverables | LOC |
|-----|-------|--------------|-----|
| **Day 1** | Version Parser | `version_parser.py`, extraction patterns | 200 |
| **Day 2** | Version Checker | `VersionReferenceChecker` service | 300 |
| **Day 3** | File Scanner | CLAUDE.md + AGENTS.md validation logic | 250 |
| **Day 4** | API Layer | Endpoints + response schemas | 150 |
| **Day 5** | CLI + Tests | `sdlcctl compliance versions` + 10 tests | 150 |

### Week 2 (Mar 24-28): Auto-Fix + Dashboard

| Day | Focus | Deliverables | LOC |
|-----|-------|--------------|-----|
| **Day 6** | Auto-Fix Engine | `AutoFixEngine` service + generators | 200 |
| **Day 7** | Fix Apply | Preview + apply logic | 150 |
| **Day 8** | CLI + Dashboard 1 | CLI batch support + ScoreCard | 150 |
| **Day 9** | Dashboard 2 | IssuesList + QuickActions | 150 |
| **Day 10** | Integration | HistoryChart + E2E tests | 100 |

---

## Technical Specifications

### New Files

```yaml
Backend:
  - backend/app/services/compliance/version_validator.py (300 LOC)
  - backend/app/services/compliance/auto_fix_engine.py (350 LOC)
  - backend/app/api/routes/compliance_validation.py (update: +200 LOC)
  - backend/sdlcctl/commands/compliance.py (update: +150 LOC)

Frontend:
  - frontend/src/components/compliance/ComplianceScoreCard.tsx (100 LOC)
  - frontend/src/components/compliance/ComplianceCategoryBreakdown.tsx (120 LOC)
  - frontend/src/components/compliance/ComplianceIssuesList.tsx (150 LOC)
  - frontend/src/components/compliance/ComplianceHistoryChart.tsx (100 LOC)
  - frontend/src/components/compliance/ComplianceQuickActions.tsx (80 LOC)
  - frontend/src/hooks/useCompliance.ts (50 LOC)
  - frontend/src/pages/projects/[id]/compliance/index.tsx (150 LOC)

Tests:
  - backend/tests/services/test_version_validator.py (200 LOC)
  - backend/tests/services/test_auto_fix_engine.py (200 LOC)
  - frontend/tests/compliance/compliance.spec.ts (150 LOC)
```

### Database Changes

```sql
-- New table: version_checks
CREATE TABLE version_checks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id),
    detected_version VARCHAR(20) NOT NULL,
    is_consistent BOOLEAN NOT NULL,
    inconsistencies JSONB,
    files_checked INTEGER NOT NULL,
    errors INTEGER NOT NULL DEFAULT 0,
    warnings INTEGER NOT NULL DEFAULT 0,
    checked_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    checked_by UUID REFERENCES users(id)
);

-- New table: auto_fixes
CREATE TABLE auto_fixes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id),
    issue_id UUID NOT NULL,
    fix_type VARCHAR(50) NOT NULL,  -- 'duplicate', 'version', 'frontmatter', 'folder'
    status VARCHAR(20) NOT NULL DEFAULT 'suggested',  -- 'suggested', 'previewed', 'applied', 'failed', 'rolled_back'
    changes JSONB NOT NULL,
    commands TEXT[],
    backup_path VARCHAR(500),
    applied_at TIMESTAMP WITH TIME ZONE,
    applied_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for fast lookups
CREATE INDEX idx_version_checks_project ON version_checks(project_id);
CREATE INDEX idx_auto_fixes_project ON auto_fixes(project_id);
CREATE INDEX idx_auto_fixes_status ON auto_fixes(status);
```

---

## Success Criteria

### Technical Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Version detection accuracy | 100% | Manual verification on 10 test projects |
| Auto-fix success rate | ≥95% | Applied fixes / attempted fixes |
| Dashboard load time | <2s | Lighthouse performance audit |
| API latency (p95) | <500ms | APM monitoring |
| Test coverage | ≥90% | pytest-cov / vitest coverage |

### Business Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Manual compliance work reduction | 80% | Time tracking before/after |
| Fix adoption rate | ≥60% | Applied fixes / suggested fixes |
| Dashboard usage | Daily use by 80% of teams | Analytics |

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Version parsing false positives | Medium | Medium | Extensive regex testing, manual override option |
| Auto-fix breaks working code | Low | High | Preview mode required, rollback support, backup creation |
| Dashboard performance on large projects | Medium | Medium | Pagination, lazy loading, caching |
| Git conflicts from auto-fix | Low | Medium | Check for uncommitted changes, create separate branch |

---

## Testing Strategy

### Unit Tests (20 tests)

```python
# Version Validator Tests
def test_version_parser_extracts_semantic_version():
    """Extract version from 'SDLC 6.1.0' format."""

def test_version_parser_handles_migration_format():
    """Extract both versions from '5.3.0 → 6.0.5' format."""

def test_version_checker_detects_mismatch():
    """AGENTS.md version different from CLAUDE.md."""

def test_version_checker_ignores_old_files():
    """Files older than threshold are INFO not ERROR."""

# Auto-Fix Tests
def test_auto_fix_generates_archive_command():
    """Duplicate folder fix generates correct mv command."""

def test_auto_fix_preview_shows_changes():
    """Preview mode shows changes without applying."""

def test_auto_fix_creates_backup():
    """Apply with backup creates .bak file."""

def test_auto_fix_rollback_works():
    """Rollback restores original state."""
```

### Integration Tests (5 tests)

```python
async def test_version_validation_api_full_flow():
    """API validates versions and returns correct response."""

async def test_auto_fix_api_applies_fix():
    """API applies fix and updates database."""

async def test_compliance_dashboard_data():
    """Dashboard API returns all required data."""
```

### E2E Tests (3 scenarios)

```bash
# Scenario 1: Version check flow
1. Navigate to /projects/{id}/compliance
2. Click "Run Check"
3. Verify version inconsistencies displayed
4. Apply version fix
5. Verify score updated

# Scenario 2: Auto-fix flow
1. View compliance issues
2. Select fixable issue
3. Preview fix
4. Apply fix
5. Verify issue resolved

# Scenario 3: Export flow
1. View compliance dashboard
2. Click Export → PDF
3. Verify PDF downloaded with correct data
```

---

## Stakeholder Communication

### Sprint Kickoff

```markdown
## Sprint 124 Kickoff: Compliance P1 Features

**Date**: March 17, 2026
**Goal**: Active compliance remediation (not just reporting)

### Why This Sprint Matters
- Sprint 123 tells teams what's wrong
- Sprint 124 helps teams FIX what's wrong
- Auto-fix reduces manual compliance work by 80%

### Key Deliverables
1. `sdlcctl compliance versions` → Version consistency check
2. `sdlcctl compliance fix` → Auto-fix engine
3. Web Dashboard → Visual compliance reporting

### Dependencies
✅ Sprint 123 complete (A+ rating)
✅ Framework 6.0.5 finalized
✅ NQH-Bot lessons documented
```

### Daily Standup Template

```markdown
Sprint 124 Day X Status:

Version Validator:
- Yesterday: [completed tasks]
- Today: [planned tasks]
- Blockers: [if any]

Auto-Fix Engine:
- Yesterday: [completed tasks]
- Today: [planned tasks]
- Blockers: [if any]

Dashboard:
- Yesterday: [completed tasks]
- Today: [planned tasks]
- Blockers: [if any]

LOC Progress: XXXX / 1,800 (XX%)
```

---

## Document Control

| Field | Value |
|-------|-------|
| **Version** | 1.0.0 |
| **Created** | January 30, 2026 |
| **Author** | PM/PJM Office |
| **Sprint** | 124 |
| **Status** | PLANNED |
| **Predecessor** | Sprint 123 (Compliance Validation P0) - ✅ A+ |
| **Successor** | Sprint 125 (Gate Readiness Dashboard) |
| **Framework** | SDLC 6.1.0 |
| **CTO Approval** | Pending |

---

## References

- [Sprint 123 Plan](./SPRINT-123-COMPLIANCE-VALIDATION.md) - Prerequisite sprint
- [PM-PJM-REVIEW-SDLC-6.0.5-MIGRATION.md](../../../NQH-Bot-Platform/docs/08-Team-Management/01-SDLC-Compliance/PM-PJM-REVIEW-SDLC-6.0.5-MIGRATION.md) - Source lessons
- [SPEC-0013-Compliance-Validation-Service.md](../../02-design/14-Technical-Specs/SPEC-0013-Compliance-Validation-Service.md) - Technical spec
- [SDLC-Implementation-Guide.md](../../../SDLC-Enterprise-Framework/07-Implementation-Guides/SDLC-Implementation-Guide.md) - Framework reference

---

*Sprint 124 - From passive compliance reporting to active remediation. Auto-fix what Sprint 123 detects.*
