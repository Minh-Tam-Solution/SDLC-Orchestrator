# Governance Auto-Generation User Guide

**Version**: 1.0.0
**Date**: January 28, 2026
**Framework**: SDLC 6.1.0
**ADR Reference**: ADR-041

---

## Overview

The Auto-Generation Layer reduces developer friction from **30 minutes to <5 minutes per PR** by automatically generating compliance artifacts. This guide covers the four auto-generation components available in the Governance Dashboard.

### Components

| Component | Purpose | Time Saved |
|-----------|---------|------------|
| **Intent Generator** | Generate intent skeleton from task description | ~15 min |
| **Ownership Suggestions** | Suggest file owners via git blame + CODEOWNERS | ~2 min |
| **Context Attachments** | Auto-attach ADRs, specs to PR | ~5 min |
| **Attestation Form** | Pre-fill AI attestation with session metadata | ~8 min |

---

## Quick Start

1. Navigate to **Governance Dashboard** (`/app/governance`)
2. Select your task from the task selector
3. Click **Generate Intent** to create intent skeleton
4. Review **Ownership Suggestions** and accept/reject
5. Verify **Context Attachments** are relevant
6. Complete **Attestation Form** (if AI-generated code)
7. Submit PR with all compliance artifacts attached

**Total time:** ~3-5 minutes (vs 30+ minutes manually)

---

## 1. Intent Generator

### Purpose
Generate a structured intent document from your task description using LLM (with template fallback).

### How to Use

1. Enter your **Task Title** (e.g., "Add user authentication")
2. Enter your **Task Description** (detailed explanation of what and why)
3. Optionally add **Acceptance Criteria** (bullet points)
4. Click **Generate Intent**

### Generated Output

The intent document includes:

```markdown
## Why This Change?
[Auto-generated business reason]

## What Problem Does It Solve?
[Auto-generated problem statement]

## Alternatives Considered
- [Alternative 1]
- [Alternative 2]
- [Reason for chosen approach]
```

### Badges

| Badge | Meaning |
|-------|---------|
| **AI Generated** (green) | LLM successfully generated content |
| **Template** (yellow) | Fallback template used (LLM timeout/error) |
| **Manual** (gray) | Developer wrote content manually |

### Tips

- Provide detailed task descriptions for better LLM output
- Review and edit generated content before saving
- Use the **Copy** button to paste into PR description

---

## 2. Ownership Suggestions

### Purpose
Automatically suggest file owners based on:
1. **CODEOWNERS** file (highest confidence)
2. **Git blame** (most recent committer)
3. **Directory patterns** (e.g., `backend/` → Backend Team)
4. **Task creator** (fallback)

### How to Use

1. File list auto-populates from your PR diff
2. Review suggested owners for each file
3. Click **Accept** to assign owner (adds `@owner` header)
4. Click **Reject** to skip (manual assignment later)
5. Use **Accept All** for batch processing

### Confidence Scores

| Score | Meaning |
|-------|---------|
| **90-100%** | CODEOWNERS match (highly reliable) |
| **70-89%** | Git blame match (recent activity) |
| **50-69%** | Directory pattern match |
| **<50%** | Fallback suggestion (review carefully) |

### Manual Override

Click the owner name to manually enter a different owner (e.g., `@john.doe`).

---

## 3. Context Attachments

### Purpose
Auto-attach relevant ADRs, specs, and design documents to your PR based on changed files.

### How It Works

1. System analyzes your PR diff (changed files)
2. Searches for ADRs mentioning affected modules
3. Searches for specs in same/related directories
4. Links relevant documents in PR description

### Context Types

| Type | Icon | Example |
|------|------|---------|
| **ADR** | Document | ADR-041-Stage-Dependencies.md |
| **Spec** | File | TASK-123-spec.md |
| **Design Doc** | Blueprint | system-architecture.md |
| **Intent** | Target | TASK-123-intent.md |
| **AGENTS.md** | Robot | AGENTS.md (project context) |

### Manual Additions

Click **Add Context** to manually attach additional documents not auto-discovered.

### Relevance Scoring

Documents are ranked by relevance (0-100%). High-relevance documents appear first.

---

## 4. Attestation Form

### Purpose
Pre-fill AI attestation form with session metadata when your code includes AI-generated content.

### Auto-Filled Fields

| Field | Source |
|-------|--------|
| **AI Provider** | Session metadata (Ollama, Claude, etc.) |
| **Model Version** | API response (e.g., qwen3:32b) |
| **Prompt Hash** | SHA256 of prompt used |
| **Generated Lines** | Count from session log |
| **AI Dependency Ratio** | `ai_lines / total_lines` |

### Human Confirmation Required

You must confirm:

1. **Review Time** - Minimum 2 seconds per AI-generated line
2. **Modifications Made** - Describe any changes you made
3. **Understanding Confirmed** - Check that you understand the code

### Review Timer

A timer tracks your review time. Minimum required = `generated_lines * 2 seconds`.

- **Green**: Meets minimum review time
- **Red**: Below minimum (cannot submit until met)

### Submission

Click **Submit Attestation** after:
- All auto-filled fields verified
- Human confirmation checkboxes checked
- Review time met

---

## Troubleshooting

### Intent Generation Fails

**Problem**: "LLM timeout" or "Generation failed"

**Solution**:
- System automatically falls back to template
- Template provides structure, you fill in details
- If template also fails, use manual entry

### Ownership Suggestions Empty

**Problem**: No suggestions for some files

**Solution**:
- Check if CODEOWNERS file exists in repo
- Verify git history exists for those files
- Use manual override to assign owner

### Context Attachments Missing

**Problem**: Relevant ADRs not attached

**Solution**:
- Ensure ADRs use consistent naming (`ADR-XXX-*.md`)
- Add module tags to ADR frontmatter
- Use **Add Context** for manual attachment

### Attestation Timer Not Starting

**Problem**: Review timer shows 0:00

**Solution**:
- Ensure form is in focus (click on form area)
- Timer starts when form loads
- Refresh page if timer stuck

---

## Best Practices

1. **Write detailed task descriptions** - Better input = better LLM output
2. **Review before accepting** - AI suggestions are helpful but not perfect
3. **Use batch operations** - Accept All for large file sets
4. **Keep context relevant** - Remove unrelated auto-attachments
5. **Take time to review** - Don't rush attestation just to pass timer

---

## Time Savings Summary

| Manual Process | Auto-Generated | Savings |
|----------------|----------------|---------|
| Write intent (15 min) | Generate + edit (2 min) | **87%** |
| Assign ownership (5 min) | Accept suggestions (30 sec) | **90%** |
| Find & link ADRs (8 min) | Auto-attach (0 sec) | **100%** |
| Fill attestation (10 min) | Confirm pre-fill (2 min) | **80%** |
| **Total: 38 min** | **Total: 4.5 min** | **88%** |

---

## Related Documentation

- [Kill Switch Admin Guide](./Governance-Kill-Switch-Admin-Guide.md)
- [ADR-041: Stage Dependencies](../../02-design/03-ADRs/ADR-041-Stage-Dependencies.md)
- [SDLC 6.1.0 Quality Assurance System](../../../SDLC-Enterprise-Framework/02-Core-Methodology/SDLC-Quality-Assurance-System.md)

---

*SDLC Orchestrator - Governance that accelerates, not hinders.*
