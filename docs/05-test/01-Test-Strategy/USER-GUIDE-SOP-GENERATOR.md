# SOP Generator User Guide

**Version**: 1.0.0
**Status**: Phase 2-Pilot (SE 3.0 Track 1)
**Date**: January 2025
**BRS Reference**: BRS-PILOT-001-NQH-Bot-SOP-Generator.yaml

---

## Table of Contents

1. [Overview](#overview)
2. [Getting Started](#getting-started)
3. [Generating an SOP](#generating-an-sop)
4. [Understanding MRP Evidence](#understanding-mrp-evidence)
5. [VCR Approval Workflow](#vcr-approval-workflow)
6. [SOP History & Management](#sop-history--management)
7. [API Reference](#api-reference)
8. [Troubleshooting](#troubleshooting)

---

## Overview

The SOP Generator is an AI-assisted tool that creates Standard Operating Procedures (SOPs) following the SASE Level 1 workflow:

```
📝 BRS (Requirements) → 🤖 Generate SOP → 📊 MRP (Evidence) → ✅ VCR (Review)
```

### Key Features

- **5 SOP Types**: Deployment, Incident, Change, Backup, Security
- **5 Mandatory Sections**: Purpose, Scope, Procedure, Roles, Quality Criteria
- **AI-Powered**: Uses Ollama (qwen3:32b) for generation
- **MRP Evidence**: Automatic evidence collection with SHA256 integrity
- **VCR Workflow**: Human review and approval process

### Performance Targets

| Metric | Target | Description |
|--------|--------|-------------|
| NFR1 | <30s | SOP generation time (p95) |
| NFR2 | ≥4/5 | Quality rating target |
| NFR3 | <$50/month | AI cost with Ollama |
| NFR4 | ≥95% | Generation success rate |

---

## Getting Started

### Prerequisites

1. **Login**: Access the SDLC Orchestrator dashboard
2. **Project**: Have an active project (optional but recommended)
3. **Permissions**: User role with SOP generation access

### Navigation

1. Click **"SOP Generator"** in the sidebar
2. Or navigate to `/sop-generator` directly

---

## Generating an SOP

### Step 1: Select SOP Type

Choose one of the 5 supported SOP types:

| Type | Icon | Description |
|------|------|-------------|
| Deployment | 🚀 | Application deployment procedures with rollback |
| Incident | 🚨 | P0-P3 incident handling and escalation |
| Change | 📋 | Change request and CAB approval workflow |
| Backup | 💾 | Backup schedules and disaster recovery |
| Security | 🔒 | Access control and vulnerability management |

### Step 2: Describe Your Workflow

Enter a detailed workflow description (minimum 50 characters):

**Good Example**:
```
Deploy the SDLC Orchestrator web application to production Kubernetes
cluster. The deployment should include blue-green strategy, database
migrations, health checks, and automatic rollback on failure. Target
cluster is GKE production with Docker images from gcr.io.
```

**Bad Example**:
```
Deploy the app to production.
```
(Too short, lacks specifics)

### Step 3: Add Context (Optional)

Provide additional context:
- Target environment details
- Compliance requirements
- Team-specific conventions
- External dependencies

### Step 4: Generate

Click **"🤖 Generate SOP"** and wait for AI generation (typically 5-10 seconds).

### Step 5: Review Generated SOP

The generated SOP appears in the preview panel with:
- **Document Control**: ID, version, dates
- **Purpose**: Why this SOP exists
- **Scope**: What's covered and excluded
- **Procedure**: Step-by-step instructions
- **Roles & Responsibilities**: RACI matrix
- **Quality Criteria**: Verification checklist

### Step 6: Download

Click **"⬇️ Download .md"** to save the SOP as a markdown file.

---

## Understanding MRP Evidence

Every generated SOP includes an MRP (Merge-Readiness Pack) evidence record.

### MRP Evidence Card

Located below the generation form, displays:

| Field | Description |
|-------|-------------|
| **MRP ID** | Unique identifier (e.g., MRP-PILOT-20250120...) |
| **SOP ID** | Associated SOP identifier |
| **Generation Time** | How long AI took (NFR1: <30s target) |
| **Completeness** | Percentage of sections present (100% = 5/5) |
| **SHA256 Hash** | Content integrity verification |
| **AI Model** | Model used (e.g., qwen3:32b) |
| **Status** | pending_review, approved, rejected |

### Viewing Full MRP

1. Go to **SOP History** (`/sop-history`)
2. Click **"📊 MRP"** on any SOP row
3. Or navigate to `/sop/{sop_id}/mrp`

### MRP Tab Contents

**Overview Card**:
- MRP ID and BRS reference (BRS-PILOT-001)
- Creation timestamp
- Current status

**Generation Metrics Card**:
- AI provider (Ollama)
- AI model used
- Generation time with NFR1 compliance indicator
- Template used

**Quality Metrics Card**:
- Completeness score with progress bar
- Sections present vs required (5/5)
- FR2 compliance status

**Integrity Card**:
- Full SHA256 hash for content verification
- Used to prove content has not been modified

---

## VCR Approval Workflow

VCR (Version Controlled Resolution) is the human review step in SASE Level 1.

### Submitting a VCR Decision

1. Navigate to SOP detail page (`/sop/{sop_id}`)
2. Click **"✅ VCR Review"** tab
3. Fill in the form:

| Field | Required | Description |
|-------|----------|-------------|
| Reviewer Name | Yes | Your name |
| Decision | Yes | approved / rejected / revision_required |
| Quality Rating | No | 1-5 stars (NFR2: target ≥4) |
| Comments | No | Review feedback |

4. Click **"Submit VCR Decision"**

### VCR Decisions

| Decision | Effect | When to Use |
|----------|--------|-------------|
| **Approved** ✅ | SOP status → approved | SOP is complete and accurate |
| **Rejected** ❌ | SOP status → rejected | SOP is fundamentally flawed |
| **Revision Required** 🔄 | SOP status → revision_required | Minor fixes needed |

### After VCR

- SOP status updates immediately
- VCR record stored with full audit trail
- MRP status updated to match decision

---

## SOP History & Management

### Accessing SOP History

Navigate to **"SOP History"** in sidebar or `/sop-history`.

### Filtering SOPs

**By Type**:
- All Types
- Deployment, Incident, Change, Backup, Security

**By Status**:
- All Status
- Draft, Pending Review, Approved, Rejected, Revision Required

### SOP List Columns

| Column | Description |
|--------|-------------|
| Type | SOP type icon |
| SOP ID | Unique identifier |
| Title | SOP title |
| Status | Current lifecycle status |
| Completeness | MRP completeness score |
| VCR | ✓ if VCR submitted, - if pending |
| Created | Generation timestamp |
| Actions | View, MRP buttons |

### Pagination

- 20 SOPs per page
- Navigate with Previous/Next buttons
- Shows "Showing X to Y of Z SOPs"

---

## API Reference

### Base URL

```
http://localhost:8000/api/v1
```

### Endpoints

#### List SOP Types (FR3)
```http
GET /sop/types
```

Response:
```json
[
  {
    "type": "deployment",
    "name": "Deployment SOP",
    "description": "Application deployment procedures",
    "typical_sections": ["Pre-deployment checklist", "Deployment steps", ...]
  },
  ...
]
```

#### Generate SOP (FR1)
```http
POST /sop/generate
Content-Type: application/json

{
  "sop_type": "deployment",
  "workflow_description": "Deploy the application... (min 50 chars)",
  "additional_context": "Optional context",
  "project_id": "PRJ-001"
}
```

Response (201 Created):
```json
{
  "sop_id": "SOP-DEPLOYMENT-20250120-abc12345",
  "sop_type": "deployment",
  "title": "Application Deployment Procedure",
  "version": "1.0.0",
  "status": "draft",
  "purpose": "...",
  "scope": "...",
  "procedure": "...",
  "roles": "...",
  "quality_criteria": "...",
  "markdown_content": "# SOP: ...",
  "sha256_hash": "abc123...",
  "generation_time_ms": 6500.0,
  "ai_model": "qwen3:32b",
  "mrp_id": "MRP-PILOT-20250120-xyz98765",
  "completeness_score": 100.0
}
```

#### List SOPs (M4)
```http
GET /sop/list?page=1&page_size=20&sop_type=deployment&status=approved
```

#### Get SOP Detail
```http
GET /sop/{sop_id}
```

#### Get MRP Evidence (FR6)
```http
GET /sop/{sop_id}/mrp
```

#### Submit VCR (FR7)
```http
POST /sop/{sop_id}/vcr
Content-Type: application/json

{
  "decision": "approved",
  "reviewer": "Tech Lead",
  "comments": "SOP is complete and follows standards.",
  "quality_rating": 5
}
```

#### Get VCR Decision
```http
GET /sop/{sop_id}/vcr
```

#### Health Check
```http
GET /sop/health
```

---

## Troubleshooting

### Common Issues

#### "Generation timeout"
- **Cause**: Ollama took longer than 30 seconds
- **Solution**: Try again with shorter workflow description
- **Check**: Ollama server availability at `OLLAMA_URL`

#### "Invalid SOP type"
- **Cause**: sop_type not one of 5 valid types
- **Solution**: Use: deployment, incident, change, backup, security

#### "Workflow description too short"
- **Cause**: Description < 50 characters
- **Solution**: Provide more detailed workflow description

#### "SOP not found" (404)
- **Cause**: SOP ID doesn't exist in system
- **Solution**: Check SOP ID, use /sop/list to find valid IDs

#### "Completeness < 100%"
- **Cause**: AI didn't generate all 5 sections
- **Solution**: Regenerate with more specific workflow description

### Health Check

```bash
curl http://localhost:8000/api/v1/sop/health
```

Response should show:
- `status: "healthy"`
- `ollama.status: "healthy"`
- `ollama.model: "qwen3:32b"`

### Contact Support

- **Documentation Issues**: File in docs/ folder
- **Bug Reports**: GitHub Issues
- **Feature Requests**: Talk to PM/PO

---

## Appendix

### SASE Level 1 Artifacts

| Artifact | Purpose | Created By |
|----------|---------|------------|
| BRS | Business requirements specification | PM/PO |
| MRP | Merge-readiness evidence pack | AI + System |
| VCR | Version controlled resolution | Reviewer |

### FR (Functional Requirements) Matrix

| FR | Description | Implementation |
|----|-------------|----------------|
| FR1 | Generate SOP from workflow | POST /sop/generate |
| FR2 | Include 5 mandatory sections | AI prompt structure |
| FR3 | Support 5 SOP types | GET /sop/types |
| FR4 | ISO 9001 compliance | Template structure |
| FR5 | SHA256 evidence | MRP sha256_hash field |
| FR6 | MRP generation | Automatic with SOP |
| FR7 | VCR approval workflow | POST /sop/{id}/vcr |

---

**Last Updated**: January 2025
**Author**: AI Development Partner
**Approved By**: CTO
