# Design Stage Restructure Plan
## SDLC 6.1.0 Compliance - Stage 02 (DESIGN)

**Date**: December 21, 2025
**Status**: PROPOSED
**Owner**: CTO

---

## Current Structure Issues

### Problem 1: Duplicate Numbering
```
03-ADRs/              ❌ Conflict
03-API-Design/        ❌ Conflict
03-Technical-Specs/   ❌ Conflict
```

### Problem 2: Fragmented ADRs
```
01-System-Architecture/Architecture-Decisions/  → ADR-001 to ADR-015
03-ADRs/                                        → ADR-015, 016, 017 (duplicate 015!)
01-ADRs/                                        → ADR-019
```

### Problem 3: Inconsistent Naming
- Some folders use singular (System-Architecture, Database-Design)
- Some use plural (ADRs)
- Some mix concepts (Admin-Panel, DevOps-Architecture)

---

## Proposed Structure (SDLC 6.1.0 / RFC-001 Compliant)

```
docs/02-design/
├── 01-ADRs/                          # All Architecture Decision Records
│   ├── ADR-001-Database-Choice.md
│   ├── ADR-002-Authentication-Model.md
│   ├── ADR-003-API-Strategy.md
│   ├── ADR-004-Microservices-Architecture.md
│   ├── ADR-005-Caching-Strategy.md
│   ├── ADR-006-CICD-Pipeline.md
│   ├── ADR-007-AI-Context-Engine.md
│   ├── ADR-011-Context-Aware-Requirements.md
│   ├── ADR-012-AI-Task-Decomposition.md
│   ├── ADR-013-Planning-Hierarchy.md
│   ├── ADR-014-SDLC-Structure-Validator.md
│   ├── ADR-015-AI-Council-Testing.md          # From 01-System-Architecture
│   ├── ADR-016-SDLC-5.0.0-Stage-Restructure.md # From 03-ADRs (rename)
│   ├── ADR-017-Admin-Panel-Architecture.md     # From 03-ADRs
│   └── ADR-019-AI-Code-Events-Schema.md        # Already here
│
├── 02-System-Architecture/           # Rename from 01-System-Architecture
│   ├── System-Architecture-Document.md
│   ├── Technical-Design-Document.md
│   ├── Component-Architecture.md
│   ├── Integration-Architecture.md
│   ├── Event-Driven-Architecture.md
│   └── C4-ARCHITECTURE-DIAGRAMS.md
│
├── 03-Database-Design/               # Rename from 02-Database-Design
│   └── Database-Architecture.md
│
├── 04-API-Design/                    # Rename from 03-API-Design
│   ├── API-DEVELOPER-GUIDE.md
│   ├── API-CHANGELOG.md
│   ├── API-Frontend-Validation-Checklist.md
│   ├── CURL-EXAMPLES.md
│   ├── OPENAPI-ENHANCEMENT-SUMMARY.md
│   └── TROUBLESHOOTING-GUIDE.md
│
├── 05-Interface-Design/              # Rename from 04-Interface-Design
│   └── Interface-Design-Document.md
│
├── 06-Data-Architecture/             # Rename from 05-Data-Architecture
│   └── Data-Flow-Architecture.md
│
├── 07-Security-Design/               # Rename from 06-Security-RBAC
│   ├── Security-Baseline.md
│   └── SOC2-TYPE-I-CONTROLS-MATRIX.md
│
├── 08-User-Experience/               # Rename from 07-User-Experience
│   ├── User-Onboarding-Flow-Architecture.md
│   └── GitHub-Integration-Design-Clarification.md
│
├── 09-UI-Design/                     # Rename from 11-UI-UX-Design
│   ├── FRONTEND-DESIGN-SPECIFICATION.md
│   ├── AI-COUNCIL-CHAT-DESIGN.md
│   ├── DESIGN-EVIDENCE-LOG.md
│   └── Support-Page-Design.md
│
├── 10-Admin-Panel-Design/            # Rename from 08-Admin-Panel
│   ├── ADMIN-PANEL-REQUIREMENTS.md
│   ├── ADMIN-PANEL-API-DESIGN.md
│   ├── ADMIN-PANEL-UI-SPECIFICATION.md
│   └── ADMIN-PANEL-SECURITY-REVIEW.md
│
├── 11-DevOps-Design/                 # Rename from 08-DevOps-Architecture
│   ├── Infrastructure-Architecture.md
│   ├── Network-Architecture.md
│   ├── Monitoring-Observability-Architecture.md
│   ├── Operability-Architecture.md
│   └── Disaster-Recovery-Plan.md
│
├── 12-Performance-Design/            # Rename from 09-Performance-Architecture
│   ├── Performance-Budget.md
│   └── Scalability-Architecture.md
│
├── 13-Testing-Strategy/              # Rename from 10-Testing-Strategy
│   └── Testing-Architecture.md
│
├── 14-Technical-Specs/               # Rename from 03-Technical-Specs
│   ├── AI-Safety-Layer-v1.md
│   ├── AI-Detection-Service-Interface.md
│   ├── Analytics-Events-Taxonomy-v1.md
│   ├── Design-Partner-Scorecard-v1.md
│   └── Workshop-Deck-AI-Safety-v1.md
│
└── README.md

# NOTE: Per RFC-001 (SDLC 6.1.0 MANDATORY), legacy content is centralized in:
#   docs/10-archive/02-Legacy/
# Active stages (00-09) NO LONGER contain 99-Legacy/ folders.
# See: SDLC-Enterprise-Framework/02-Core-Methodology/Documentation-Standards/SDLC-Legacy-Document-Organization-Standard.md
```

---

## Migration Steps

### Step 1: Consolidate ADRs (Highest Priority)
```bash
# Move ADR-001 to ADR-015 from 01-System-Architecture/Architecture-Decisions/
mv docs/02-design/01-System-Architecture/Architecture-Decisions/ADR-*.md \
   docs/02-design/01-ADRs/

# Move ADR-016, 017 from 03-ADRs/ (skip ADR-015 duplicate)
mv docs/02-design/03-ADRs/ADR-016-SDLC-5.0.0-STAGE-RESTRUCTURE.md \
   docs/02-design/01-ADRs/
mv docs/02-design/03-ADRs/ADR-017-ADMIN-PANEL-ARCHITECTURE.md \
   docs/02-design/01-ADRs/

# Move duplicate ADR-015 to Legacy
mv docs/02-design/03-ADRs/ADR-015-SDLC-5.1.0-STAGE-RESTRUCTURING.md \
   docs/02-design/99-Legacy/

# Remove empty 03-ADRs folder
rmdir docs/02-design/03-ADRs/
```

### Step 2: Rename Folders (Sequential)
```bash
# Rename in reverse order to avoid conflicts
mv docs/02-design/11-UI-UX-Design              docs/02-design/09-UI-Design
mv docs/02-design/10-Testing-Strategy          docs/02-design/13-Testing-Strategy
mv docs/02-design/09-Performance-Architecture  docs/02-design/12-Performance-Design
mv docs/02-design/08-DevOps-Architecture       docs/02-design/11-DevOps-Design
mv docs/02-design/08-Admin-Panel               docs/02-design/10-Admin-Panel-Design
mv docs/02-design/07-User-Experience           docs/02-design/08-User-Experience
mv docs/02-design/06-Security-RBAC             docs/02-design/07-Security-Design
mv docs/02-design/05-Data-Architecture         docs/02-design/06-Data-Architecture
mv docs/02-design/04-Interface-Design          docs/02-design/05-Interface-Design
mv docs/02-design/03-Technical-Specs           docs/02-design/14-Technical-Specs
mv docs/02-design/03-API-Design                docs/02-design/04-API-Design
mv docs/02-design/02-Database-Design           docs/02-design/03-Database-Design
mv docs/02-design/01-System-Architecture       docs/02-design/02-System-Architecture
```

### Step 3: Update Cross-References
Files with internal links to update:
- All ADRs referencing other ADRs
- System-Architecture-Document.md → references ADRs, API docs
- Technical-Design-Document.md → references ADRs, database docs
- API-DEVELOPER-GUIDE.md → references ADRs, security docs
- README.md → references all subdirectories

Example replacements:
```markdown
# Old
[ADR-001](01-System-Architecture/Architecture-Decisions/ADR-001-Database-Choice.md)

# New
[ADR-001](01-ADRs/ADR-001-Database-Choice.md)
```

```markdown
# Old
[Security Baseline](06-Security-RBAC/Security-Baseline.md)

# New
[Security Baseline](07-Security-Design/Security-Baseline.md)
```

---

## Validation Checklist

After migration:
- [ ] All ADRs (001-019) in `01-ADRs/` folder
- [ ] No duplicate folder numbers (01-14, 99)
- [ ] All cross-references updated (no broken links)
- [ ] Git history preserved (use `git mv` not `mv`)
- [ ] README.md reflects new structure

---

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Broken cross-references | High | Automated find/replace + manual review |
| Git merge conflicts | Medium | Do migration in single atomic commit |
| Lost ADR history | Low | Use `git mv` to preserve history |
| Team confusion | Medium | Update README.md + announce in Slack |

---

## Rollback Plan

If issues occur:
```bash
git revert <commit-hash>
```

All changes in single commit → single revert restores old structure.

---

**Approval Required**: CTO
**Estimated Time**: 45 minutes
**Execution Window**: Before Sprint 41 kickoff (Jan 6, 2026)
