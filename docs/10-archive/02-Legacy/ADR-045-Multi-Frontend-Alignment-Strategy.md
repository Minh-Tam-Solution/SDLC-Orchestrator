# ADR-045: Multi-Frontend Alignment Strategy
## Governance Framework for Web, CLI, and VS Code Extension

**Status**: APPROVED
**Date**: January 30, 2026
**Decision Makers**: CTO, PM, Backend Lead, Frontend Lead
**Stage**: Stage 02 (HOW - Design & Architecture)
**Framework**: SDLC 6.1.0
**Sprint**: Sprint 127 (Jan 30 - Feb 7, 2026)
**Priority**: P0 - Prevents framework version drift across delivery surfaces

---

## Context

### Problem Statement

During Sprint 124 work on CLI/Extension updates, a **critical planning gap** was discovered:

```
SDLC Orchestrator = Implementation of SDLC Framework
                    ↓
        BUT the project itself was NOT following the framework properly:
        - Design docs not updated when requirements change
        - Multiple frontends (Web, CLI, Extension) not kept in sync
        - Framework version mismatch (5.0.0 vs 6.0.5)
        - No alignment matrix tracking feature parity
```

### Business Impact

| Metric | Before Alignment | After Alignment |
|--------|------------------|-----------------|
| CLI SDLC Version | 5.0.0 | 6.0.5 |
| Extension SDLC Version | 5.x | 6.0.5 |
| CLI Feature Parity | 39% | 71% |
| Extension Feature Parity | 67% | 89% |
| Launch Confidence | 86% | 99.9% |

### Root Cause Analysis

**"Nhà bác sĩ phải tự uống thuốc" (Doctor must take own medicine)**

SDLC Orchestrator implements SDLC Framework, so it MUST:
1. Follow all SDLC 6.1.0 documentation standards
2. Keep Stage 00-03 (Foundation → Planning → Design → Integrate) docs updated
3. Maintain feature parity matrix for all delivery surfaces
4. Update ALL frontends when Framework version changes

### Affected Stages

| Stage | Name | Gap Found |
|-------|------|-----------|
| 00-FOUNDATION | Strategic Discovery | Missing multi-frontend scope in vision |
| 01-PLANNING | Requirements Planning | FRD doesn't cover CLI/Extension parity |
| 02-DESIGN | Technical Design | No unified architecture for 3 frontends |
| 03-INTEGRATE | API Contracts | API contracts not validated against all consumers |

---

## Decision

We will establish a **Multi-Frontend Alignment Framework** consisting of:

### 1. Frontend Alignment Matrix (Living Document)

Location: `docs/01-planning/01-Requirements/Frontend-Alignment-Matrix.md`

**Purpose**: Track feature parity across all delivery surfaces

**Structure**:
```markdown
| Feature | Web | CLI | Extension | Gap Owner | Target Sprint |
|---------|-----|-----|-----------|-----------|---------------|
| Spec Validation | ✅ | ✅ | ✅ | ✅ Aligned | - |
| Tier Classification | ✅ | ✅ | ✅ | ✅ Aligned | - |
| Context Authority | ✅ | ❌ | ❌ | All | Sprint 128 |
```

**Update Triggers**:
- New feature added to any frontend
- Framework version changes
- API endpoint added/modified
- Sprint planning (review gaps)
- Monthly alignment checkpoint

### 2. Framework Update Trigger Automation

When SDLC-Enterprise-Framework submodule version changes:

```yaml
# .github/workflows/framework-alignment.yml
name: Framework Version Alignment Check

on:
  push:
    paths:
      - 'SDLC-Enterprise-Framework/**'

jobs:
  check-alignment:
    runs-on: ubuntu-latest
    steps:
      - name: Detect Framework Version Change
        run: |
          NEW_VERSION=$(cat SDLC-Enterprise-Framework/VERSION)
          echo "Framework version: $NEW_VERSION"

      - name: Create Alignment Issues
        uses: actions/github-script@v7
        with:
          script: |
            const surfaces = ['Web Dashboard', 'CLI (sdlcctl)', 'VS Code Extension'];
            for (const surface of surfaces) {
              await github.rest.issues.create({
                owner: context.repo.owner,
                repo: context.repo.repo,
                title: `[Framework Alignment] Update ${surface} to SDLC ${newVersion}`,
                body: `Framework version changed. Update ${surface} to align.`,
                labels: ['framework-alignment', 'p0']
              });
            }
```

### 3. Monthly Alignment Checkpoint

**Schedule**: First Monday of each month
**Owner**: PM
**Attendees**: Backend Lead, Frontend Lead, Architect

**Agenda**:
1. Review Frontend Alignment Matrix (15 min)
2. Identify new gaps from recent sprints (15 min)
3. Prioritize alignment work for next sprint (15 min)
4. Update documentation if needed (15 min)

**Output**: Meeting notes + updated Frontend-Alignment-Matrix.md

### 4. Validation Pipeline

All three frontends MUST pass the same validation rules:

```
┌─────────────────────────────────────────────────────────────┐
│           SDLC 6.1.0 Spec Validation Pipeline               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐       │
│  │ Web Backend │   │ CLI         │   │ Extension   │       │
│  │ (Python)    │   │ (Python)    │   │ (TypeScript)│       │
│  └──────┬──────┘   └──────┬──────┘   └──────┬──────┘       │
│         │                 │                 │               │
│         ▼                 ▼                 ▼               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │          Shared Validation Rules                    │   │
│  │  - SPC-001: Missing required field                  │   │
│  │  - SPC-002: Invalid field format                    │   │
│  │  - SPC-003: Missing BDD requirements                │   │
│  │  - SPC-004: Missing YAML frontmatter                │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │          E2E Parity Tests                           │   │
│  │  - Same spec → Same errors across all surfaces     │   │
│  │  - Error codes match (SPC-XXX)                      │   │
│  │  - Performance <500ms on all surfaces               │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Consequences

### Positive

1. **Guaranteed Parity**: All users get consistent validation regardless of interface
2. **Faster Updates**: Framework changes propagate to all surfaces systematically
3. **Better Testing**: E2E parity tests catch drift early
4. **Clear Ownership**: Gap Owner column in matrix assigns responsibility
5. **Predictable Planning**: Monthly checkpoints ensure alignment stays on radar

### Negative

1. **Additional Process**: Monthly checkpoint adds 1 hour/month overhead
2. **CI Complexity**: Framework alignment workflow adds build time
3. **Documentation Burden**: Matrix must be updated with every feature

### Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Matrix becomes stale | Automated reminder in sprint planning checklist |
| Alignment issues ignored | P0 label ensures visibility; blocks merge |
| Performance drift | E2E tests include latency assertions |

---

## Implementation

### Phase 1: Foundation (Sprint 125) ✅ COMPLETE

- [x] Create Frontend Alignment Matrix v1.0.0
- [x] Update CLI to SDLC 6.1.0 (35 files)
- [x] Update Extension to SDLC 6.1.0 (5 files)
- [x] Implement SpecFrontmatterValidator in CLI
- [x] Publish CLI v1.2.0 to PyPI
- [x] Publish Extension v1.2.0 to VS Code Marketplace

### Phase 2: Feature Parity (Sprint 126) ✅ COMPLETE

- [x] Implement JSON Schema validation in CLI
- [x] Implement BDD requirements validator
- [x] Implement `sdlcctl spec convert` command
- [x] Implement `sdlcctl spec init` command
- [x] Add spec validation to Extension
- [x] Create E2E parity tests (25 tests)

### Phase 3: Process Establishment (Sprint 127) 🔄 IN PROGRESS

- [x] Create ADR-045 Multi-Frontend Strategy (this document)
- [ ] Implement Framework Update Trigger automation
- [ ] Document Monthly Alignment Checkpoint process
- [ ] Update Stage 00-03 documentation
- [ ] Create Lessons Learned documentation

---

## Appendix A: Error Code Registry

All frontends MUST use these error codes for spec validation:

| Code | Severity | Description | Trigger |
|------|----------|-------------|---------|
| SPC-001 | Critical | Missing required field | spec_id, title, version, status, tier, owner, last_updated |
| SPC-002 | High | Invalid field format | spec_id not SPEC-XXYY, version not X.Y.Z, etc. |
| SPC-003 | Medium | Missing BDD requirements | PROFESSIONAL/ENTERPRISE tier without GIVEN-WHEN-THEN |
| SPC-004 | Critical | Missing YAML frontmatter | No `---` block at document start |
| SPC-005 | Medium | Missing tier-specific sections | Required sections per SPEC-0002 |
| SPC-006 | Low | Cross-reference broken | Referenced SPEC/ADR not found |

## Appendix B: Feature Parity Targets

| Category | Web Target | CLI Target | Extension Target |
|----------|------------|------------|------------------|
| Core Governance | 100% | 75% | 90% |
| Spec Validation | 100% | 100% | 100% |
| AI Features | 100% | 0% (by design) | 100% |
| Admin Features | 100% | 0% (by design) | 0% (by design) |

**Note**: CLI and Extension intentionally do NOT implement all features. Admin features are Web-only. AI features may be Extension-only for IDE integration.

## Appendix C: Related Documents

- [Frontend-Alignment-Matrix.md](../../01-planning/01-Requirements/Frontend-Alignment-Matrix.md)
- [SPRINT-125-127-MULTI-FRONTEND-ALIGNMENT.md](../../04-build/02-Sprint-Plans/SPRINT-125-127-MULTI-FRONTEND-ALIGNMENT.md)
- [SPEC-0002-Specification-Standard.md](../../02-design/14-Technical-Specs/SPEC-0002-Specification-Standard.md)

---

**Document Status**: APPROVED
**Review Cycle**: Quarterly
**Next Review**: April 30, 2026
