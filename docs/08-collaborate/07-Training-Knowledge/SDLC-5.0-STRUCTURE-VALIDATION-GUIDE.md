# SDLC 6.1.0 Structure Validation - User Guide

**Version**: 1.0.0
**Status**: ACTIVE - STAGE 03 (BUILD)
**Date**: December 6, 2025
**Sprint**: 30 - CI/CD & Web Integration (Day 5)
**Authority**: Frontend Lead + CTO Approved

---

## Overview

The SDLC 6.1.0 Structure Validation feature ensures your project documentation follows the complete SDLC lifecycle framework. It validates folder structure, P0 artifacts, and provides actionable fix suggestions.

### Key Features

- **4-Tier Classification**: Lite, Standard, Professional, Enterprise
- **11 SDLC Stages**: Complete lifecycle from Project Foundation to Archive
- **P0 Artifact Tracking**: Critical documents that must exist
- **Compliance Score**: 0-100 score based on coverage
- **Interactive Dashboard**: Real-time validation with visual feedback
- **History Tracking**: Trend analysis and compliance history

---

## 4-Tier Classification

SDLC 6.1.0 supports four tiers based on project size and requirements:

| Tier | Icon | Required Stages | Description |
|------|------|-----------------|-------------|
| **Lite** | 🌱 | 5 | Minimal structure for small projects |
| **Standard** | ⚡ | 8 | Standard structure for mid-size projects |
| **Professional** | 🏆 | 10 | Full structure for enterprise projects |
| **Enterprise** | 👑 | 11 | Complete lifecycle with Archive stage |

### Tier Selection Guidelines

- **Lite**: Personal projects, MVPs, prototypes
- **Standard**: Team projects, internal tools, mid-size applications
- **Professional**: Production systems, client projects, enterprise apps
- **Enterprise**: Regulated industries, compliance-required, audit-heavy projects

---

## 11 SDLC Stages

Each stage represents a phase of the software development lifecycle:

| Stage | Name | Folder | Key Artifacts |
|-------|------|--------|---------------|
| **00** | Project Foundation | `00-Project-Foundation` | Product Vision, Problem Statement |
| **01** | Planning & Analysis | `01-Planning-Analysis` | FRD, User Stories, Data Model |
| **02** | Design & Architecture | `02-Design-Architecture` | System Architecture, API Design, ADRs |
| **03** | Development & Implementation | `03-Development-Implementation` | Sprint Plans, Setup Guides |
| **04** | Testing & QA | `04-Testing-QA` | Test Plan, Test Cases |
| **05** | Deployment & Release | `05-Deployment-Release` | Deployment Guide, Release Notes |
| **06** | Operations & Support | `06-Operations-Support` | Runbook, Incident Response |
| **07** | Maintenance & Evolution | `07-Maintenance-Evolution` | Change Management, Tech Debt |
| **08** | Training & Knowledge | `08-Training-Knowledge` | User Guides, Training Materials |
| **09** | Executive Reports | `09-Executive-Reports` | CTO/CPO Reports, Gate Reviews |
| **10** | Archive | `10-Archive` | Historical Documents (Enterprise only) |

---

## P0 Artifacts

P0 (Priority 0) artifacts are critical documents that must exist for each stage. Missing P0 artifacts result in **error** severity issues.

### P0 Artifacts by Stage

| Stage | Required P0 Artifacts |
|-------|----------------------|
| **00** | `Product-Vision.md`, `Problem-Statement.md` |
| **01** | `Functional-Requirements-Document.md` |
| **02** | `System-Architecture-Document.md`, `openapi.yml` |
| **03** | `Sprint-Plans/`, `Setup-Guides/` |
| **04** | `Test-Plan.md` |
| **05** | `Deployment-Guide.md` |
| **06** | `Runbook.md` |
| **07-10** | No mandatory P0 artifacts |

---

## Using the Dashboard

### Accessing the Dashboard

1. Navigate to your project
2. Click on "SDLC Validation" in the sidebar
3. Or navigate directly to `/projects/{project_id}/sdlc-validation`

### Dashboard Components

#### Compliance Score Circle

The circular progress indicator shows your overall compliance score:

- **Green (90-100)**: Excellent - Fully compliant
- **Yellow (70-89)**: Good - Minor issues
- **Orange (50-69)**: Fair - Needs attention
- **Red (0-49)**: Poor - Critical issues

#### Tier Badge

Shows your current or target SDLC tier with the corresponding icon and required stages.

#### Stage Progress Grid

Visual representation of all 11 stages:
- **Green checkmark**: Stage folder exists
- **Red X**: Stage folder missing
- **Gray**: Optional for current tier

Hover over each stage to see details like file count and README status.

#### Validation History Chart

Interactive chart showing compliance score trend over time:
- Reference lines at 70% (Good) and 90% (Excellent)
- Tooltip with detailed information on hover
- Click data points for full validation details

#### Issue List

Filtered list of validation issues with three tabs:
- **All**: All issues
- **Errors**: Critical issues (P0 missing, required stages missing)
- **Warnings**: Non-critical issues (optional stages missing, naming conventions)

Each issue includes:
- Severity icon (❌ Error, ⚠️ Warning, ℹ️ Info)
- Issue description
- File/folder path
- Fix suggestion (collapsible)

### Running Validation

1. **Select Target Tier** (optional):
   - Auto-detect: System determines best tier
   - Or manually select: Lite, Standard, Professional, Enterprise

2. **Select Mode**:
   - Normal: Standard validation
   - Strict: Fails on warnings

3. **Click "Validate Now"**:
   - System scans your docs folder
   - Results appear in real-time
   - History is automatically saved

---

## API Usage

### Validate Structure

```bash
curl -X POST "http://localhost:8000/api/v1/projects/{project_id}/validate-structure" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "tier": "professional",
    "docs_root": "docs",
    "strict_mode": false,
    "include_p0": true
  }'
```

### Get Validation History

```bash
curl -X GET "http://localhost:8000/api/v1/projects/{project_id}/validation-history?limit=10" \
  -H "Authorization: Bearer <token>"
```

### Get Compliance Summary

```bash
curl -X GET "http://localhost:8000/api/v1/projects/{project_id}/compliance-summary" \
  -H "Authorization: Bearer <token>"
```

---

## CLI Usage (sdlcctl)

### Validate Structure

```bash
sdlcctl validate --tier professional --strict
```

### Initialize Structure

```bash
sdlcctl init --tier standard
```

### Fix Issues

```bash
sdlcctl fix --auto
```

### Generate Report

```bash
sdlcctl report --format html --output compliance-report.html
```

---

## CI/CD Integration

### GitHub Actions

Add to `.github/workflows/sdlc-validate.yml`:

```yaml
name: SDLC Structure Validation

on:
  push:
    branches: [main, develop]
    paths:
      - 'docs/**'
  pull_request:
    paths:
      - 'docs/**'

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Validate SDLC Structure
        uses: nqh/sdlc-validator-action@v1
        with:
          tier: professional
          strict: false
          fail-on-warning: false

      - name: Upload Report
        uses: actions/upload-artifact@v4
        with:
          name: sdlc-compliance-report
          path: sdlc-report.json
```

### Pre-commit Hook

Add to `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: local
    hooks:
      - id: sdlc-validate
        name: SDLC Structure Validation
        entry: sdlcctl validate --tier standard
        language: system
        pass_filenames: false
        files: ^docs/
```

---

## Troubleshooting

### Common Issues

#### "Missing P0 artifact" Error

**Problem**: Required P0 artifact not found.

**Solution**:
1. Check the issue path for the expected location
2. Create the missing file with the correct name
3. Re-run validation

**Example**:
```bash
# Issue: Missing P0 artifact: Test-Plan.md
# Path: docs/04-Testing-QA

# Solution:
mkdir -p docs/04-Testing-QA
touch docs/04-Testing-QA/Test-Plan.md
```

#### "Stage folder not found" Warning

**Problem**: Expected stage folder doesn't exist.

**Solution**:
1. Create the folder with the correct naming format
2. Add at least a README.md

**Example**:
```bash
# Issue: Stage 07 not found
# Solution:
mkdir -p docs/07-Maintenance-Evolution
echo "# Maintenance & Evolution" > docs/07-Maintenance-Evolution/README.md
```

#### "Invalid folder naming" Warning

**Problem**: Folder name doesn't match SDLC 6.1.0 convention.

**Solution**:
1. Rename folder to match `XX-Stage-Name` format
2. Use kebab-case for multi-word names

**Example**:
```bash
# Wrong: docs/01-planning_analysis
# Correct: docs/01-Planning-Analysis

mv docs/01-planning_analysis docs/01-Planning-Analysis
```

### Getting Help

- **Documentation**: Check this guide and API docs
- **GitHub Issues**: Report bugs at [SDLC Orchestrator Issues](https://github.com/nqh/sdlc-orchestrator/issues)
- **Slack**: Join #sdlc-support channel

---

## Best Practices

### 1. Start with Lite Tier

For new projects, start with Lite tier and progressively add stages as needed.

### 2. Keep P0 Artifacts Updated

P0 artifacts are your foundation. Keep them updated and accurate.

### 3. Use Auto-detect for Initial Assessment

Let the system auto-detect your tier to understand current state before setting targets.

### 4. Review Trends Regularly

Check the validation history chart weekly to track improvement.

### 5. Fix Errors Before Warnings

Focus on error-severity issues first (P0 artifacts, required stages).

### 6. Integrate with CI/CD

Add SDLC validation to your CI/CD pipeline to catch issues early.

---

## Compliance Scoring

### Score Calculation

```
Score = (Stage Coverage * 0.6) + (P0 Coverage * 0.4)

Where:
- Stage Coverage = (Stages Found / Stages Required) * 100
- P0 Coverage = (P0 Found / P0 Required) * 100
```

### Score Interpretation

| Score Range | Label | Status |
|-------------|-------|--------|
| 90-100 | Excellent | Fully compliant |
| 70-89 | Good | Minor issues |
| 50-69 | Fair | Needs attention |
| 0-49 | Poor | Critical issues |

### Compliance Status

- **Compliant**: Score >= 70 AND no error-severity issues
- **Non-Compliant**: Score < 70 OR has error-severity issues

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-12-06 | Initial release with Sprint 30 |

---

**Questions?** Contact the SDLC Orchestrator team at support@sdlc-orchestrator.com
