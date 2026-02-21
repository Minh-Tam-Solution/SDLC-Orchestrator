# Stage 10: Archive (Centralized Legacy Archive)

**Version**: 6.0.5
**Stage**: 10 - Archive
**Question Answered**: What is the historical record?
**Status**: REFERENCE ONLY
**Framework**: SDLC 6.1.0

---

## Purpose

This folder is the **single centralized archive** for all legacy and historical documents, organized by stage-aligned subdirectories per RFC-001 (SDLC 6.1.0 MANDATORY standard).

Benefits:
- Historical reference and audit compliance
- Learning from past decisions
- Legal requirements
- **Zero `99-Legacy/` in active stages (00-09)** — eliminates AI context pollution

---

## AI-NEVER-READ Directive

```yaml
# This entire folder should be treated as Legacy/Archive
# AI assistants should NOT read content from this folder
# unless specifically requested by the user

directive: AI-NEVER-READ
reason: Contains outdated, superseded, or historical content
exception: User explicitly requests historical information
```

---

## Folder Structure

```
10-archive/
├── README.md                                # This file (AI-NEVER-READ directive)
│
├── 00-Legacy/                               # Foundation archives (from 00-foundation)
├── 01-Legacy/                               # Planning archives (from 01-planning)
├── 02-Legacy/                               # Design archives (from 02-design)
├── 03-Legacy/                               # Integration archives (from 03-integrate)
├── 04-Legacy/                               # Build archives (from 04-build)
├── 05-Legacy/                               # Test archives (from 05-test)
├── 07-Legacy/                               # Operations archives (from 07-operate)
├── 08-Legacy/                               # Collaboration archives (from 08-collaborate)
├── 09-Legacy/                               # Governance archives (from 09-govern)
│
├── 04-Historical-Documents/                 # Pre-existing historical documents
├── OpenCode-Evaluation-Aborted-Jan12-2026/  # Archived evaluation
├── Root-Cleanup-Feb-2026/                   # Root cleanup records
└── Temp-Debug-Docs/                         # Temporary debug documentation
```

---

## Archive Pattern (RFC-001)

**MANDATORY (SDLC 6.1.0)**: All legacy content lives in `10-archive/{NN}-Legacy/` where `{NN}` is the stage number.

```
Stage 00 legacy → 10-archive/00-Legacy/
Stage 01 legacy → 10-archive/01-Legacy/
Stage 02 legacy → 10-archive/02-Legacy/
...
Stage 09 legacy → 10-archive/09-Legacy/
```

### Rules

| # | Rule | Level |
|---|------|-------|
| R-001 | Zero `99-Legacy/` folders in active stages (00-09) | MANDATORY |
| R-002 | All legacy content in `10-archive/{NN}-Legacy/` | MANDATORY |
| R-003 | `README.md` with `AI-NEVER-READ` directive in archive root | MANDATORY |
| R-004 | Preserve original directory structure inside `{NN}-Legacy/` | MANDATORY |
| R-005 | Use `cp -r` + verify + `rm -rf` for migration (never `mv`) | RECOMMENDED |
| R-006 | Add migration timestamp to archived README files | RECOMMENDED |

---

## Archive Policy

### 1. Move, Don't Delete

```yaml
Rule: Never delete project documentation
Instead: Move to 10-archive/{NN}-Legacy/ (stage-aligned)
Reason: Historical reference, audit trail, learning
```

### 2. Date Prefix Retention

```yaml
Format: YYYY-MM-DD-{description}.md
Example: 2025-11-15-Sprint-20-Report.md
Rule: Retain original date prefix when archiving
```

### 3. No Active References

```yaml
Rule: Active documents should NOT link to archived content
Exception: Historical reference with clear "ARCHIVED" label
```

### 4. Periodic Review

```yaml
Cadence: Quarterly
Review: Archive contents for cleanup or permanent retention
Decision: Keep for audit / Delete if no value
```

---

## Migration Evidence

Migrated from `99-Legacy/` per-stage to centralized `10-archive/{NN}-Legacy/` on February 13, 2026.

| Source | Destination | Files |
|--------|-------------|-------|
| `00-foundation/99-Legacy/` | `10-archive/00-Legacy/` | 12 |
| `01-planning/99-Legacy/` | `10-archive/01-Legacy/` | 1 |
| `02-design/99-Legacy/` | `10-archive/02-Legacy/` | 4 |
| `03-integrate/99-Legacy/` | `10-archive/03-Legacy/` | 1 |
| `04-build/99-Legacy/` | `10-archive/04-Legacy/` | 123 |
| `05-test/99-Legacy/` | `10-archive/05-Legacy/` | 1 |
| `07-operate/99-Legacy/` | `10-archive/07-Legacy/` | 1 |
| `08-collaborate/99-Legacy/` | `10-archive/08-Legacy/` | 1 |
| `09-govern/99-Legacy/` | `10-archive/09-Legacy/` | 86 |
| **Total** | | **230** |

---

## Tier Requirements (SDLC 6.1.0)

| Tier | Archive Requirements |
|------|---------------------|
| LITE | Not required |
| STANDARD | Basic archival policy |
| PROFESSIONAL | Structured archive, quarterly review |
| ENTERPRISE | Full audit trail, retention policy, compliance docs |

---

## AI Assistant Guidance

**CRITICAL**: This folder is marked **AI-NEVER-READ**

```yaml
DO NOT:
  - Read content from this folder for active development
  - Use archived patterns or code as reference
  - Link to archived content in new documents

DO:
  - Acknowledge folder exists as historical archive
  - Redirect to current equivalents when asked about archived topics
  - Only read if user explicitly requests historical information
```

---

## Related Documents

| Document | Purpose |
|----------|---------|
| RFC-001 (Framework) | Legacy Document Organization Standard |
| SDLC-Legacy-Document-Organization.md (Framework) | RFC-001 rules and migration guide |
| migrate-legacy-to-archive.sh (Framework) | Automated migration script |

---

**Document Status**: P0 Entry Point (AI-NEVER-READ Directive)
**Compliance**: SDLC 6.1.0 (RFC-001 MANDATORY)
**Last Updated**: February 13, 2026
**Owner**: PM + CTO
