# SDLC Structure Scanner - Validator Rules Specification

**Document Type**: Technical Specification
**Sprint**: 44 - SDLC Structure Scanner Engine
**Epic**: EP-04: SDLC Structure Enforcement
**Version**: 1.0.0
**Date**: December 22, 2025
**Status**: APPROVED
**Framework**: SDLC 6.1.0

---

## 1. Overview

This document specifies all validation rules enforced by the SDLC Structure Scanner. Each rule has:

- **Rule ID**: Unique identifier (e.g., STAGE-001)
- **Severity**: ERROR, WARNING, or INFO
- **Description**: What the rule checks
- **Examples**: Violation and correct examples
- **Auto-fix**: Whether the scanner can automatically fix it
- **Fix Template**: Suggested fix format

---

## 2. Rule Categories

| Category | Prefix | Rules | Purpose |
|----------|--------|-------|---------|
| Stage Folder | STAGE | 5 | SDLC stage validation |
| Numbering | NUM | 3 | Subfolder numbering |
| Naming | NAME | 2 | File/folder naming |
| Header | HDR | 2 | Document metadata |
| Reference | REF | 2 | Link validation |
| Scanner | SCANNER | 1 | Internal errors |

**Total**: 15 rules

---

## 3. Stage Folder Rules (STAGE-xxx)

### STAGE-001: Invalid Stage Folder Naming

| Property | Value |
|----------|-------|
| **Rule ID** | STAGE-001 |
| **Severity** | ERROR |
| **Auto-fixable** | Yes |
| **Category** | Stage Folder |

**Description**: Stage folders must follow the pattern `XX-name` where XX is a two-digit number (00-09).

**Violation Examples**:
```
docs/
├── foundation/           ❌ Missing number prefix
├── 1-planning/           ❌ Single digit (should be 01)
├── 00_design/            ❌ Underscore instead of hyphen
├── Stage-01-Planning/    ❌ Extra prefix
```

**Correct Examples**:
```
docs/
├── 00-foundation/        ✅
├── 01-planning/          ✅
├── 02-design/            ✅
```

**Fix Template**:
```
Rename '{folder}' to '{XX}-{name}'
```

---

### STAGE-002: Unknown Stage Number

| Property | Value |
|----------|-------|
| **Rule ID** | STAGE-002 |
| **Severity** | ERROR |
| **Auto-fixable** | No |
| **Category** | Stage Folder |

**Description**: Stage numbers must be 00-09. Numbers 10+ are reserved (10-archive is special).

**Violation Examples**:
```
docs/
├── 11-extra-stage/       ❌ Invalid (>09)
├── 15-custom/            ❌ Invalid (>09)
├── 00-foundation/        ✅
```

**Correct Examples**:
```
docs/
├── 00-foundation/        ✅ Stage 00
├── 01-planning/          ✅ Stage 01
├── ...
├── 09-govern/            ✅ Stage 09 (last stage)
├── 10-archive/           ✅ Special (not a stage)
```

**Why Not Auto-fixable**: Unknown stages require human decision on where content belongs.

---

### STAGE-003: Stage Name Mismatch

| Property | Value |
|----------|-------|
| **Rule ID** | STAGE-003 |
| **Severity** | WARNING |
| **Auto-fixable** | Yes |
| **Category** | Stage Folder |

**Description**: Stage folders should use the canonical SDLC 6.1.0 names.

**SDLC 6.1.0 Canonical Names**:
| Stage | Canonical Name |
|-------|---------------|
| 00 | foundation |
| 01 | planning |
| 02 | design |
| 03 | integration |
| 04 | build |
| 05 | test |
| 06 | deploy |
| 07 | operate |
| 08 | collaborate |
| 09 | govern |

**Violation Examples**:
```
docs/
├── 00-Project-Foundation/    ❌ Should be 00-foundation
├── 01-Planning-Analysis/     ❌ Should be 01-planning
├── 02-Design-Architecture/   ❌ Should be 02-design
├── 03-Development/           ❌ Should be 03-integration
```

**Fix Template**:
```
Rename '{current}' to '{stage_num}-{canonical_name}'
```

---

### STAGE-004: Duplicate Stage Number

| Property | Value |
|----------|-------|
| **Rule ID** | STAGE-004 |
| **Severity** | ERROR |
| **Auto-fixable** | Yes (with rename) |
| **Category** | Stage Folder |

**Description**: Each stage number (00-09) must appear exactly once.

**Violation Examples**:
```
docs/
├── 01-planning/          ✅ First 01
├── 01-requirements/      ❌ DUPLICATE 01
├── 02-design/            ✅ First 02
├── 02-architecture/      ❌ DUPLICATE 02
```

**Correct Examples**:
```
docs/
├── 01-planning/          ✅
│   ├── 01-requirements/  ✅ (subfolder, not stage)
│   └── 02-analysis/      ✅ (subfolder, not stage)
├── 02-design/            ✅
```

**Fix Template**:
```
Merge or rename: {folder1} vs {folder2}
Option 1: Merge contents into {folder1}
Option 2: Rename {folder2} to {XX}-{new_name}
```

---

### STAGE-005: Missing Required Stage

| Property | Value |
|----------|-------|
| **Rule ID** | STAGE-005 |
| **Severity** | WARNING |
| **Auto-fixable** | Yes |
| **Category** | Stage Folder |

**Description**: All 10 SDLC stages (00-09) should exist.

**Violation Examples**:
```
docs/
├── 00-foundation/        ✅
├── 01-planning/          ✅
├── 02-design/            ✅
├── 04-build/             ❌ Missing 03-integration
├── 05-test/              ✅
```

**Fix Template**:
```bash
mkdir -p docs/{stage_num}-{stage_name}
echo "# {Stage Name}" > docs/{stage_num}-{stage_name}/README.md
```

**Tier Exceptions**:
| Tier | Required Stages |
|------|----------------|
| LITE | 00, 01, 02, 03 |
| STANDARD | 00, 01, 02, 03, 04, 05 |
| PROFESSIONAL | 00-09 (all) |
| ENTERPRISE | 00-09 + 10-archive |

---

## 4. Numbering Rules (NUM-xxx)

### NUM-001: Duplicate Subfolder Number

| Property | Value |
|----------|-------|
| **Rule ID** | NUM-001 |
| **Severity** | ERROR |
| **Auto-fixable** | Yes |
| **Category** | Numbering |

**Description**: Within each stage, subfolder numbers must be unique.

**Violation Examples**:
```
docs/02-design/
├── 01-ADRs/              ✅ First 01
├── 01-System-Architecture/  ❌ DUPLICATE 01
├── 02-Database-Design/   ✅ First 02
├── 03-ADRs/              ❌ DUPLICATE (ADRs already at 01)
├── 03-API-Design/        ❌ DUPLICATE 03
```

**Correct Examples**:
```
docs/02-design/
├── 01-ADRs/              ✅
├── 02-System-Architecture/  ✅
├── 03-Database-Design/   ✅
├── 04-API-Design/        ✅
```

**Fix Template**:
```
Renumber subfolders sequentially:
  {old_num}-{name} → {new_num}-{name}
```

---

### NUM-002: Non-Sequential Numbering

| Property | Value |
|----------|-------|
| **Rule ID** | NUM-002 |
| **Severity** | INFO |
| **Auto-fixable** | Yes |
| **Category** | Numbering |

**Description**: Subfolder numbers should be sequential without gaps.

**Violation Examples**:
```
docs/02-design/
├── 01-ADRs/              ✅
├── 03-Database-Design/   ⚠️ Gap (missing 02)
├── 05-API-Design/        ⚠️ Gap (missing 04)
```

**Correct Examples**:
```
docs/02-design/
├── 01-ADRs/              ✅
├── 02-Database-Design/   ✅
├── 03-API-Design/        ✅
```

**Note**: This is INFO severity because gaps don't break functionality, just readability.

---

### NUM-003: Invalid Subfolder Number Format

| Property | Value |
|----------|-------|
| **Rule ID** | NUM-003 |
| **Severity** | WARNING |
| **Auto-fixable** | Yes |
| **Category** | Numbering |

**Description**: Subfolder numbers should be two-digit (01, 02, not 1, 2).

**Violation Examples**:
```
docs/02-design/
├── 1-ADRs/               ❌ Single digit
├── 002-Database/         ❌ Three digits
├── A-API-Design/         ❌ Letter prefix
```

**Correct Examples**:
```
docs/02-design/
├── 01-ADRs/              ✅
├── 02-Database/          ✅
├── 03-API-Design/        ✅
```

---

## 5. Naming Rules (NAME-xxx)

### NAME-001: Non-Standard Folder Name

| Property | Value |
|----------|-------|
| **Rule ID** | NAME-001 |
| **Severity** | WARNING |
| **Auto-fixable** | Yes |
| **Category** | Naming |

**Description**: Folder names should use kebab-case (lowercase with hyphens).

**Violation Examples**:
```
docs/02-design/
├── 01-ADRs/              ❌ UPPERCASE (should be 01-adrs)
├── 02_Database_Design/   ❌ Underscores (should be hyphens)
├── 03-apiDesign/         ❌ camelCase
├── 04-API Design/        ❌ Spaces
```

**Correct Examples**:
```
docs/02-design/
├── 01-adrs/              ✅
├── 02-database-design/   ✅
├── 03-api-design/        ✅
```

**Naming Convention**:
```
{NN}-{lowercase-kebab-case-name}
```

---

### NAME-002: Non-Standard File Name

| Property | Value |
|----------|-------|
| **Rule ID** | NAME-002 |
| **Severity** | INFO |
| **Auto-fixable** | No |
| **Category** | Naming |

**Description**: Markdown files should use UPPER-KEBAB-CASE.md.

**Violation Examples**:
```
docs/02-design/01-adrs/
├── adr-001.md            ❌ lowercase
├── ADR001.md             ❌ No hyphens
├── adr_001.md            ❌ Underscores
├── My ADR.md             ❌ Spaces
```

**Correct Examples**:
```
docs/02-design/01-adrs/
├── ADR-001-TITLE.md      ✅
├── SPRINT-43-PLAN.md     ✅
├── API-SPECIFICATION.md  ✅
├── README.md             ✅ (exception)
```

**Exceptions**:
- `README.md` - Standard convention
- `CHANGELOG.md` - Standard convention
- `LICENSE.md` - Standard convention

---

## 6. Header Rules (HDR-xxx)

### HDR-001: Missing Document Header Table

| Property | Value |
|----------|-------|
| **Rule ID** | HDR-001 |
| **Severity** | WARNING |
| **Auto-fixable** | Yes |
| **Category** | Header |

**Description**: SDLC documents should have a metadata header table.

**Violation Examples**:
```markdown
# My Document

This document describes...
```

**Correct Examples**:
```markdown
# My Document

| Field | Value |
|-------|-------|
| **Version** | 1.0.0 |
| **Date** | December 22, 2025 |
| **Stage** | 02-design |
| **Status** | APPROVED |

---

This document describes...
```

**Fix Template**:
```markdown
| Field | Value |
|-------|-------|
| **Version** | 1.0.0 |
| **Date** | {current_date} |
| **Stage** | {detected_stage} |
| **Status** | DRAFT |
```

---

### HDR-002: Missing Required Header Field

| Property | Value |
|----------|-------|
| **Rule ID** | HDR-002 |
| **Severity** | WARNING |
| **Auto-fixable** | Yes |
| **Category** | Header |

**Description**: Header tables must include required fields.

**Required Fields**:
| Field | Required | Description |
|-------|----------|-------------|
| Version | Yes | Semantic version (1.0.0) |
| Date | Yes | Document date |
| Stage | Yes | SDLC stage (02-design) |
| Status | Yes | DRAFT, APPROVED, DEPRECATED |
| Author | No | Document author |
| Owner | No | Responsible team |

**Violation Examples**:
```markdown
| Field | Value |
|-------|-------|
| **Version** | 1.0.0 |
| **Date** | December 22, 2025 |
```
❌ Missing Stage and Status

**Correct Examples**:
```markdown
| Field | Value |
|-------|-------|
| **Version** | 1.0.0 |
| **Date** | December 22, 2025 |
| **Stage** | 02-design |
| **Status** | APPROVED |
```

---

## 7. Reference Rules (REF-xxx)

### REF-001: Broken Internal Link

| Property | Value |
|----------|-------|
| **Rule ID** | REF-001 |
| **Severity** | ERROR |
| **Auto-fixable** | No |
| **Category** | Reference |

**Description**: Internal markdown links must point to existing files.

**Violation Examples**:
```markdown
See [Sprint Plan](./SPRINT-44-PLAN.md)  ❌ File doesn't exist
Reference: [ADR-001](../01-adrs/ADR-001.md)  ❌ Wrong path
```

**Correct Examples**:
```markdown
See [Sprint Plan](../../04-build/02-Sprint-Plans/SPRINT-44.md)  ✅
Reference: [ADR-001](../../02-design/01-adrs/ADR-001.md)  ✅
```

---

### REF-002: Inconsistent Link Format

| Property | Value |
|----------|-------|
| **Rule ID** | REF-002 |
| **Severity** | INFO |
| **Auto-fixable** | Yes |
| **Category** | Reference |

**Description**: Internal links should use relative paths from docs root.

**Violation Examples**:
```markdown
[Link](/home/user/project/docs/02-design/file.md)  ❌ Absolute path
[Link](C:\Users\docs\file.md)  ❌ Windows absolute path
```

**Correct Examples**:
```markdown
[Link](../../02-design/file.md)  ✅ Relative path
[Link](./subdir/file.md)  ✅ Relative path
```

---

## 8. Scanner Rules (SCANNER-xxx)

### SCANNER-ERROR: Internal Scanner Error

| Property | Value |
|----------|-------|
| **Rule ID** | SCANNER-ERROR |
| **Severity** | ERROR |
| **Auto-fixable** | No |
| **Category** | Scanner |

**Description**: Internal error during scanning (validator exception).

**Causes**:
- Permission denied on file/folder
- Validator logic error
- Memory/resource exhaustion

**Output**:
```
SCANNER-ERROR: Validator 'header-metadata' failed: UnicodeDecodeError
```

---

## 9. Rule Configuration

### 9.1 Disable Rules

```json
{
  "scanner": {
    "disabled_rules": ["NUM-002", "NAME-002"]
  }
}
```

### 9.2 Override Severity

```json
{
  "scanner": {
    "rule_overrides": {
      "STAGE-005": { "severity": "INFO" },
      "NAME-001": { "severity": "ERROR" }
    }
  }
}
```

### 9.3 Disable Validators

```json
{
  "scanner": {
    "disabled_validators": ["header-metadata"]
  }
}
```

---

## 10. Rule Summary Table

| Rule ID | Severity | Auto-Fix | Category | Description |
|---------|----------|----------|----------|-------------|
| STAGE-001 | ERROR | ✅ | Stage | Invalid stage folder naming |
| STAGE-002 | ERROR | ❌ | Stage | Unknown stage number |
| STAGE-003 | WARNING | ✅ | Stage | Stage name mismatch |
| STAGE-004 | ERROR | ✅ | Stage | Duplicate stage number |
| STAGE-005 | WARNING | ✅ | Stage | Missing required stage |
| NUM-001 | ERROR | ✅ | Numbering | Duplicate subfolder number |
| NUM-002 | INFO | ✅ | Numbering | Non-sequential numbering |
| NUM-003 | WARNING | ✅ | Numbering | Invalid number format |
| NAME-001 | WARNING | ✅ | Naming | Non-standard folder name |
| NAME-002 | INFO | ❌ | Naming | Non-standard file name |
| HDR-001 | WARNING | ✅ | Header | Missing header table |
| HDR-002 | WARNING | ✅ | Header | Missing required field |
| REF-001 | ERROR | ❌ | Reference | Broken internal link |
| REF-002 | INFO | ✅ | Reference | Inconsistent link format |
| SCANNER-ERROR | ERROR | ❌ | Scanner | Internal error |

---

## 11. Exit Codes

| Code | Meaning | When |
|------|---------|------|
| 0 | Success | No errors (warnings allowed) |
| 1 | Failure | Any ERROR severity violations |
| 2 | Failure | Any violations with `--fail-on-warning` |

---

## 12. Output Formats

### 12.1 Table Format (default)

```
┌──────────┬───────────┬─────────────────────────────────────┬────────────────────────────────┬─────────┐
│ Severity │ Rule      │ Path                                │ Message                        │ Fixable │
├──────────┼───────────┼─────────────────────────────────────┼────────────────────────────────┼─────────┤
│ ERROR    │ STAGE-001 │ docs/foundation/                    │ Invalid stage folder naming    │ ✅      │
│ ERROR    │ NUM-001   │ docs/02-design/01-ADRs/             │ Duplicate numbering '01'       │ ✅      │
│ WARNING  │ STAGE-003 │ docs/00-Project-Foundation/         │ Stage name mismatch            │ ✅      │
│ INFO     │ NUM-002   │ docs/02-design/                     │ Non-sequential numbering       │ ✅      │
└──────────┴───────────┴─────────────────────────────────────┴────────────────────────────────┴─────────┘

Summary: 2 errors, 1 warning, 1 info
```

### 12.2 JSON Format

```json
{
  "violations": [
    {
      "rule_id": "STAGE-001",
      "severity": "ERROR",
      "path": "docs/foundation/",
      "message": "Invalid stage folder naming",
      "fix_suggestion": "Rename to: 00-foundation",
      "auto_fixable": true
    }
  ],
  "summary": {
    "errors": 2,
    "warnings": 1,
    "info": 1,
    "total": 4
  },
  "scan_duration_ms": 1234,
  "files_scanned": 150,
  "folders_scanned": 25
}
```

### 12.3 GitHub Annotations

```
::error file=docs/foundation/::Invalid stage folder naming: foundation
::error file=docs/02-design/01-ADRs/::Duplicate numbering '01' in 02-design
::warning file=docs/00-Project-Foundation/::Stage name mismatch: expected 'foundation'
```

---

## 13. Approvals

| Role | Name | Date | Status |
|------|------|------|--------|
| Tech Lead | [Pending] | Dec 22, 2025 | ⏳ |
| CTO | [Pending] | Dec 22, 2025 | ⏳ |

---

**Document Version**: 1.0.0
**Last Updated**: December 22, 2025
**Owner**: Backend Team
