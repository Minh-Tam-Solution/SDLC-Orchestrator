---
# Required Fields (9/9) - SDLC 6.0.5 Section 8
sprint_id: SPRINT-123
title: "Compliance Validation Service (P0)"
status: PLANNING
tier: PROFESSIONAL
owner: "Backend Lead"
start_date: 2026-03-03
end_date: 2026-03-14
framework_version: 6.0.5

# Context Management (AGENTS.md 4-Zone Model)
context_zone: Semi-Static
update_frequency: Daily

# Sprint-Specific Fields
team_size: 1
priority: P0
effort_hours: 24
effort_sp: 3
estimated_loc: 1200
stage: 04-build
dependencies:
  - SPRINT-120 (Gates Engine)
  - SPRINT-120 (Context Authority V2)
related_specs:
  - SPEC-0013 (Compliance Validation Service)
predecessor: SPRINT-122
successor: SPRINT-124
goals:
  - "Automate SDLC 6.0.5 compliance scoring (X/100) with category breakdown"
  - "Implement duplicate folder detection to prevent migration collisions"
deliverables:
  - "Compliance Scorer (10 categories, 10 pts each)"
  - "Duplicate Folder Detector"
  - "CLI commands: sdlcctl validate --compliance/--duplicates"
  - "API endpoints: compliance score, duplicate detection"
---

# Sprint 123: Compliance Validation Service (P0)

**Dates**: March 3-14, 2026 (10 working days)
**Status**: 📋 PLANNED
**Total Estimated LOC**: ~1,200
**Estimated Effort**: 24h (16h Compliance Scorer + 8h Duplicate Detection)
**Framework**: SDLC 6.0.5
**Priority**: P0 (First post-feature-freeze sprint)

---

## Executive Summary

Sprint 123 implements P0 Compliance Validation features derived from NQH-Bot and BFlow real-world migration lessons. This sprint delivers automated compliance scoring and duplicate folder detection capabilities.

### Sprint Objective

```
PRIMARY: Automate SDLC 6.0.5 compliance scoring (X/100) with category breakdown
SECONDARY: Implement duplicate folder detection to prevent migration collisions
```

### Background: Lessons Learned

**Source**: PM/PJM Review of NQH-Bot + BFlow SDLC 6.0.5 Migrations (Jan 30, 2026)

| Issue | Impact at NQH-Bot | Prevention |
|-------|-------------------|------------|
| Duplicate stage folders (04/05/06 collision) | Broken links, Gate failure | Automated detection |
| Version reference inconsistency | Outdated AGENTS.md header | Automated validation |
| 23% specs missed 6.0.5 format | Failed Gate G-Phase-3 | YAML frontmatter validator |
| Manual compliance scoring | Subjective, inconsistent | Automated X/100 scoring |

---

## CTO-Approved Roadmap Context

```yaml
Phase 0 (Jan 30 - Feb 28): Feature Freeze
  - BFlow uses scripts manually
  - No Orchestrator automation work
  - Focus on Go-Live (Mar 1)

Phase 1 (Mar 3-21): Sprint 123 - THIS SPRINT
  - P0: Compliance Scorer (16h)
  - P0: Duplicate Detection (8h)
  - Total: 24h = ~2-3 days + testing

Phase 2 (Mar 22+): Future Sprints
  - P1: Version Reference Validator
  - P2: Gate Readiness Dashboard
  - P3: Cross-project Compliance Aggregation
```

---

## Features

### Feature 1: Compliance Scorer (16h)

**Goal**: Automated SDLC 6.0.5 compliance scoring with category breakdown

#### 1.1 Scoring Categories (10 categories, 10 pts each)

| Category | Max Points | Checks |
|----------|------------|--------|
| Documentation Structure | 10 | Stage folders (00-10), no duplicates |
| Specifications Management | 10 | YAML frontmatter, SPEC-XXXX numbering |
| CLAUDE.md & AGENTS.md | 10 | Version headers, required sections |
| SASE Artifacts | 10 | CRP, MRP, VCR templates present |
| Code File Naming | 10 | snake_case (Python), camelCase/PascalCase (TS) |
| Migration Tracking | 10 | Progress percentage, deadline compliance |
| Framework Alignment | 10 | 7-Pillar + Section 7 compliance |
| Team Organization | 10 | SDLC Compliance Hub, roles defined |
| Legacy Archival | 10 | Proper 99-legacy/ or 10-Archive/ usage |
| Governance Documentation | 10 | CEO/CTO approvals, ADRs |

**Total**: 100 points

#### 1.2 API Endpoints

```yaml
POST /api/v1/projects/{id}/validate/compliance:
  description: Run full compliance validation
  request:
    project_id: UUID
    include_categories: Optional[List[str]]
    exclude_categories: Optional[List[str]]
  response:
    overall_score: int (0-100)
    categories:
      - name: str
        score: int (0-10)
        max_score: int
        issues: List[ComplianceIssue]
        passed_checks: List[str]
    summary:
      total_issues: int
      critical_issues: int
      warnings: int
    recommendations: List[str]
    generated_at: datetime

GET /api/v1/projects/{id}/compliance/score:
  description: Get cached compliance score
  response:
    overall_score: int
    last_calculated: datetime
    category_scores: Dict[str, int]
```

#### 1.3 CLI Commands

```bash
# Full compliance check
sdlcctl validate --compliance
# Output: Overall: 87/100 | Documentation: 8.5 | Specs: 9.2 | ...

# Specific category
sdlcctl validate --compliance --category specifications

# JSON output for CI/CD
sdlcctl validate --compliance --format json > compliance-report.json

# Score only (for badges/dashboards)
sdlcctl score
# Output: 87
```

#### 1.4 Implementation Plan

| Day | Task | LOC |
|-----|------|-----|
| Day 1 | Database schema + models | 150 |
| Day 2 | Scoring service + 5 category checkers | 250 |
| Day 3 | 5 remaining category checkers | 200 |
| Day 4 | API endpoints + response schemas | 150 |
| Day 5 | CLI integration | 100 |
| **Total** | | **850** |

---

### Feature 2: Duplicate Folder Detection (8h)

**Goal**: Detect and report stage folder collisions (e.g., 04-Development + 04-Testing)

#### 2.1 Detection Rules

```yaml
Stage Folder Rules:
  00-discover: Exactly 1 folder starting with "00-"
  01-planning: Exactly 1 folder starting with "01-"
  02-design: Exactly 1 folder starting with "02-"
  03-integrate: Exactly 1 folder starting with "03-"
  04-build: Exactly 1 folder starting with "04-"
  05-test: Exactly 1 folder starting with "05-"
  06-deploy: Exactly 1 folder starting with "06-"
  07-operate: Exactly 1 folder starting with "07-"
  08-collaborate: Exactly 1 folder starting with "08-"
  09-govern: Exactly 1 folder starting with "09-"
  10-archive: Exactly 1 folder starting with "10-"

Collision Types:
  SAME_PREFIX: "04-Development" and "04-Testing" (critical)
  NUMBERING_GAP: Missing "03-integrate" folder (warning)
  EXTRA_STAGE: "11-custom" folder (info)
```

#### 2.2 API Endpoints

```yaml
POST /api/v1/projects/{id}/validate/duplicates:
  description: Detect duplicate stage folders
  request:
    project_id: UUID
    docs_path: Optional[str]  # Default: "docs/"
  response:
    valid: bool
    collisions: List[FolderCollision]
      - stage_prefix: str  # "04"
        folders: List[str]  # ["04-Development", "04-Testing"]
        severity: str  # "critical"
        fix_suggestion: str
    gaps: List[str]  # Missing stages
    extras: List[str]  # Extra folders
```

#### 2.3 CLI Commands

```bash
# Check for duplicates
sdlcctl validate --duplicates
# Output:
# ❌ CRITICAL: Stage 04 collision
#    Found: 04-Development-Implementation/, 04-Testing-Quality/
#    Fix: Archive one folder to 10-Archive/

# Auto-fix (with confirmation)
sdlcctl fix --duplicates
# Prompts for which folder to archive
```

#### 2.4 Implementation Plan

| Day | Task | LOC |
|-----|------|-----|
| Day 6 | Detection service + rules | 200 |
| Day 7 | API endpoint + CLI | 150 |
| **Total** | | **350** |

---

## Technical Design

### Database Schema

```sql
-- File: alembic/versions/sprint123_compliance_validation.py

-- Table: compliance_scores
CREATE TABLE compliance_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id),
    overall_score INTEGER NOT NULL,
    category_scores JSONB NOT NULL,
    issues_summary JSONB NOT NULL,
    calculated_at TIMESTAMPTZ DEFAULT NOW(),
    calculated_by UUID REFERENCES users(id),
    validation_version VARCHAR(20) DEFAULT '1.0.0',
    CONSTRAINT valid_score CHECK (overall_score >= 0 AND overall_score <= 100)
);

CREATE INDEX idx_compliance_scores_project ON compliance_scores(project_id);
CREATE INDEX idx_compliance_scores_date ON compliance_scores(calculated_at DESC);

-- Table: compliance_issues
CREATE TABLE compliance_issues (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    score_id UUID NOT NULL REFERENCES compliance_scores(id) ON DELETE CASCADE,
    category VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,  -- 'critical', 'warning', 'info'
    issue_type VARCHAR(100) NOT NULL,
    message TEXT NOT NULL,
    file_path VARCHAR(500),
    fix_suggestion TEXT,
    fix_command VARCHAR(500),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_compliance_issues_score ON compliance_issues(score_id);
CREATE INDEX idx_compliance_issues_severity ON compliance_issues(severity);

-- Table: folder_collision_checks
CREATE TABLE folder_collision_checks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id),
    checked_at TIMESTAMPTZ DEFAULT NOW(),
    valid BOOLEAN NOT NULL,
    collisions JSONB,
    gaps JSONB,
    extras JSONB
);
```

### Service Architecture

```python
# File: backend/app/services/validation/compliance_scorer.py

class ComplianceScorerService:
    """SDLC 6.0.5 Compliance Scoring Engine."""

    CATEGORY_CHECKERS = {
        "documentation_structure": DocumentationStructureChecker,
        "specifications_management": SpecificationsChecker,
        "claude_agents_md": ClaudeAgentsMdChecker,
        "sase_artifacts": SASEArtifactsChecker,
        "code_file_naming": CodeFileNamingChecker,
        "migration_tracking": MigrationTrackingChecker,
        "framework_alignment": FrameworkAlignmentChecker,
        "team_organization": TeamOrganizationChecker,
        "legacy_archival": LegacyArchivalChecker,
        "governance_documentation": GovernanceDocumentationChecker,
    }

    async def calculate_score(
        self,
        project_id: UUID,
        include_categories: Optional[List[str]] = None,
        exclude_categories: Optional[List[str]] = None,
    ) -> ComplianceScoreResult:
        """Calculate compliance score for project."""
        categories_to_check = self._get_categories(include_categories, exclude_categories)

        results = {}
        total_score = 0
        all_issues = []

        for category, checker_class in self.CATEGORY_CHECKERS.items():
            if category not in categories_to_check:
                continue

            checker = checker_class(self.db, self.file_service)
            result = await checker.check(project_id)

            results[category] = result
            total_score += result.score
            all_issues.extend(result.issues)

        return ComplianceScoreResult(
            overall_score=total_score,
            category_results=results,
            issues=all_issues,
            generated_at=datetime.utcnow(),
        )


class DuplicateFolderDetector:
    """Detect stage folder collisions."""

    STAGE_PREFIXES = [
        ("00", "discover"),
        ("01", "planning"),
        ("02", "design"),
        ("03", "integrate"),
        ("04", "build"),
        ("05", "test"),
        ("06", "deploy"),
        ("07", "operate"),
        ("08", "collaborate"),
        ("09", "govern"),
        ("10", "archive"),
    ]

    async def detect(
        self,
        project_id: UUID,
        docs_path: str = "docs/",
    ) -> DuplicateDetectionResult:
        """Detect duplicate stage folders."""
        folders = await self.file_service.list_directories(project_id, docs_path)

        collisions = []
        gaps = []

        for prefix, stage_name in self.STAGE_PREFIXES:
            matching = [f for f in folders if f.startswith(f"{prefix}-")]

            if len(matching) > 1:
                collisions.append(FolderCollision(
                    stage_prefix=prefix,
                    stage_name=stage_name,
                    folders=matching,
                    severity="critical",
                    fix_suggestion=f"Archive duplicates to 10-Archive/duplicate-folders-sprint-XXX/",
                ))
            elif len(matching) == 0 and prefix not in ("10",):  # 10-archive optional
                gaps.append(f"{prefix}-{stage_name}")

        return DuplicateDetectionResult(
            valid=len(collisions) == 0,
            collisions=collisions,
            gaps=gaps,
            extras=[f for f in folders if not any(f.startswith(f"{p[0]}-") for p in self.STAGE_PREFIXES)],
        )
```

---

## Daily Schedule

| Day | Feature | Task | LOC |
|-----|---------|------|-----|
| **1** | Compliance Scorer | DB schema + models | 150 |
| **2** | Compliance Scorer | Service + 5 checkers | 250 |
| **3** | Compliance Scorer | 5 remaining checkers | 200 |
| **4** | Compliance Scorer | API endpoints | 150 |
| **5** | Compliance Scorer | CLI integration | 100 |
| **6** | Duplicate Detection | Detection service | 200 |
| **7** | Duplicate Detection | API + CLI | 150 |
| **8** | Both | Integration tests | 200 |
| **9** | Both | E2E tests + docs | 150 |
| **10** | Both | Bug fixes + polish | 50 |
| **TOTAL** | | | **1,200** |

---

## Success Criteria

### Compliance Scorer

| Metric | Target | Measurement |
|--------|--------|-------------|
| API functional | 100% | All endpoints working |
| Category accuracy | >95% | Manual verification on NQH-Bot |
| Performance | <5s | Full scan on 1000-file project |
| Test coverage | >90% | pytest-cov report |

### Duplicate Detection

| Metric | Target | Measurement |
|--------|--------|-------------|
| Detection accuracy | 100% | All NQH-Bot collisions detected |
| False positives | 0 | No incorrect reports |
| Performance | <1s | Scan docs/ folder |
| CLI usability | 100% | Team feedback |

---

## Integration with Existing Systems

### Gates Engine (Sprint 120)

```yaml
Integration Point: Gate Readiness Check
  - Before G-Phase-0: Check compliance_score >= 80
  - Before G-Phase-1: Check no duplicate folders
  - Evidence: compliance_scores table linked to gate_evidence
```

### Context Authority V2 (Sprint 120)

```yaml
Integration Point: Dynamic Overlay
  - Low compliance score → Add warning to AGENTS.md overlay
  - Duplicate detected → Block certain file modifications
```

### SDLC Orchestrator CLI (sdlcctl)

```yaml
Existing Commands Extended:
  sdlcctl validate:
    --compliance   # NEW: Run compliance scoring
    --duplicates   # NEW: Check folder collisions
    --all          # Existing: Include all validators

  sdlcctl score     # NEW: Quick compliance score output
  sdlcctl fix --duplicates  # NEW: Interactive duplicate resolution
```

---

## Risks and Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Category checker complexity | Medium | Medium | Start with 5 most critical |
| Cross-project file access | Low | High | Use existing FileService |
| Performance on large repos | Medium | Medium | Incremental scanning, caching |
| CLI UX complexity | Low | Low | Follow existing sdlcctl patterns |

---

## Dependencies

### Internal

- [x] Gates Engine (Sprint 120) - ✅ In progress
- [x] Context Authority V2 (Sprint 120) - ✅ In progress
- [x] sdlcctl CLI framework (Sprint 114) - ✅ Complete
- [x] FileService (existing) - ✅ Available

### External

- [x] SDLC 6.0.5 Framework finalized - ✅ Complete (Jan 28, 2026)
- [x] NQH-Bot lessons documented - ✅ Complete (Jan 30, 2026)
- [x] BFlow scripts tested - ✅ Complete (Jan 30, 2026)

---

## Testing Strategy

### Unit Tests

```python
# Test compliance scoring
def test_documentation_structure_checker_detects_missing_stages():
    """Missing stage folder reduces score."""

def test_specifications_checker_validates_yaml_frontmatter():
    """Invalid YAML frontmatter reported as issue."""

def test_duplicate_detector_finds_collisions():
    """04-Development + 04-Testing detected as collision."""
```

### Integration Tests

```python
# Test full workflow
async def test_compliance_score_api_returns_correct_score():
    """API returns accurate compliance score."""

async def test_duplicate_detection_integrates_with_gates():
    """Gate blocked when duplicates detected."""
```

### E2E Tests

```bash
# CLI test scenario
sdlcctl validate --compliance --project nqh-bot
# Expected: Score matches PM/PJM review (96/100)

sdlcctl validate --duplicates --project bflow
# Expected: Reports known duplicates
```

---

## Stakeholder Communication

### Sprint Kickoff

```markdown
## Sprint 123 Kickoff: Compliance Validation

**Date**: March 3, 2026
**Goal**: Automate SDLC 6.0.5 compliance checking

### Why This Sprint Matters
- NQH-Bot migration revealed manual compliance scoring is inconsistent
- BFlow almost had same duplicate folder issue
- Automation prevents human error in future migrations

### Key Deliverables
1. `sdlcctl validate --compliance` → X/100 score
2. `sdlcctl validate --duplicates` → Folder collision detection
3. API endpoints for dashboard integration
```

### Daily Standup Template

```markdown
Sprint 123 Day X Status:

Compliance Scorer:
- Yesterday: [completed tasks]
- Today: [planned tasks]
- Blockers: [if any]

Duplicate Detection:
- Yesterday: [completed tasks]
- Today: [planned tasks]
- Blockers: [if any]

LOC Progress: XXXX / 1,200 (XX%)
```

---

## Document Control

| Field | Value |
|-------|-------|
| **Version** | 1.0.0 |
| **Created** | January 30, 2026 |
| **Author** | PM/PJM Office |
| **Sprint** | 123 |
| **Status** | PLANNED |
| **Predecessor** | Sprint 122 (TBD) |
| **Successor** | Sprint 124 (P1 Features) |
| **Source** | PM/PJM Review of NQH-Bot + BFlow Migrations |
| **CTO Approval** | Pending (via Phase 1 roadmap approval) |

---

## References

- [PM-PJM-REVIEW-SDLC-6.0.5-MIGRATION.md](../../../NQH-Bot-Platform/docs/08-Team-Management/01-SDLC-Compliance/PM-PJM-REVIEW-SDLC-6.0.5-MIGRATION.md)
- [SPRINT-127-GATE-READINESS-CHECKLIST.md](../../../Bflow-Platform/docs/08-Team-Management/02-SDLC-Compliance/SDLC-6.0.5-Preparation/SPRINT-127-GATE-READINESS-CHECKLIST.md)
- [SPEC-0013-Compliance-Validation-Service.md](../../02-design/14-Technical-Specs/SPEC-0013-Compliance-Validation-Service.md)

---

*Sprint 123 - First post-feature-freeze sprint. Automating lessons learned from real-world migrations.*
